#!/usr/bin/env python3
"""
Build Aureon's single-file "global memory" dataset.

This orchestrates the existing ingest scripts into one command and keeps the
output in a single SQLite file (default: state/aureon_global_history.sqlite).

Reality check:
- "Every trade ever recorded globally" is not feasible with typical API plans
  (cost, rate limits, licensing, data volume).
- What we *can* do is build a data pyramid (long-horizon low-res for breadth +
  high-res recent history for the symbols you actually trade) and keep it
  resumable via SQLite watermarks.

Profiles:
  - standard: mirrors scripts/runners/ingest_all_global_history.cmd
  - max:      broader + deeper (CoinAPI registry + daily for wide universe +
              recent minute bars for majors + optional ticks)
  - unsafe-all: attempts the absolute largest CoinAPI universe (can take days,
                huge disk, may incur plan costs)
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple


_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPTS_DIR = _REPO_ROOT / "scripts" / "python"


def _script(name: str) -> Path:
    p = _SCRIPTS_DIR / name
    if not p.exists():
        raise FileNotFoundError(f"Missing script: {p}")
    return p


def _fmt_cmd(cmd: List[str]) -> str:
    # Windows-friendly quoting for display only.
    out: List[str] = []
    for part in cmd:
        if not part:
            out.append('""')
            continue
        if any(ch in part for ch in (" ", "\t", '"')):
            out.append('"' + part.replace('"', '\\"') + '"')
        else:
            out.append(part)
    return " ".join(out)


def _run_step(
    step_name: str,
    argv: List[str],
    *,
    dry_run: bool,
) -> int:
    cmd = [sys.executable] + argv
    print()
    print("=" * 80)
    print(step_name)
    print("=" * 80)
    print(_fmt_cmd(cmd))

    if dry_run:
        return 0

    start = time.time()
    try:
        res = subprocess.run(cmd, cwd=str(_REPO_ROOT))
    except KeyboardInterrupt:
        raise
    except Exception as exc:
        print(f"[ERROR] {step_name}: {exc}")
        return 1
    finally:
        elapsed = time.time() - start
        print(f"[time] {step_name}: {elapsed:.1f}s")

    if res.returncode != 0:
        print(f"[WARN] {step_name} exited non-zero: {res.returncode}")
    return int(res.returncode or 0)


def _print_db_stats(db_path: Path) -> None:
    try:
        conn = sqlite3.connect(str(db_path))
        try:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;"
            ).fetchall()
            print()
            print("=" * 80)
            print("DB STATS")
            print("=" * 80)
            for (name,) in rows:
                try:
                    n = int(conn.execute(f"SELECT COUNT(1) FROM {name};").fetchone()[0])
                except Exception:
                    n = -1
                print(f"  {name:25s} {n:>12,d}" if n >= 0 else f"  {name:25s} (count failed)")
        finally:
            conn.close()
    except Exception as exc:
        print(f"[WARN] Failed to print DB stats: {exc}")


def _add_db_arg(args: argparse.Namespace, cmd: List[str]) -> List[str]:
    if args.db:
        return cmd + ["--db", args.db]
    return cmd


def _maybe_add_no_resume(args: argparse.Namespace, cmd: List[str]) -> List[str]:
    if args.no_resume:
        return cmd + ["--no-resume"]
    return cmd


def _account_sync_cmd(args: argparse.Namespace) -> List[str]:
    return _add_db_arg(
        args,
        [
            str(_script("sync_global_history_db.py")),
            "--max-kraken",
            str(int(args.account_sync_max_kraken)),
            "--binance-limit",
            str(int(args.account_sync_binance_limit)),
            "--alpaca-limit",
            str(int(args.account_sync_alpaca_limit)),
        ],
    )


def _standard_plan(args: argparse.Namespace) -> List[Tuple[str, List[str]]]:
    # Mirrors scripts/runners/ingest_all_global_history.cmd (but with controlled args).
    plan: List[Tuple[str, List[str]]] = []

    if not args.skip_account_sync:
        plan.append(
            (
                "[1/7] Sync account trades (Kraken, Binance, Alpaca, Capital; budgeted)",
                _account_sync_cmd(args),
            )
        )
    plan.append(
        (
            "[2/7] yfinance broad ingest (5y daily, all categories)",
            _maybe_add_no_resume(
                args,
                _add_db_arg(args, [str(_script("ingest_yfinance.py")), "--all", "--days", "1825"]),
            ),
        )
    )
    plan.append(
        (
            "[3/7] FRED macro indicators",
            _maybe_add_no_resume(
                args,
                _add_db_arg(args, [str(_script("ingest_fred.py")), "--category", "all"]),
            ),
        )
    )
    plan.append(
        (
            "[4/7] Existing feeds (CoinGecko, news, Glassnode, Coinbase, macro)",
            _add_db_arg(args, [str(_script("ingest_existing_feeds.py")), "--feeds", "all"]),
        )
    )
    plan.append(
        (
            "[5/7] CoinAPI crypto market history (core majors, 1y)",
            _maybe_add_no_resume(
                args,
                _add_db_arg(
                    args,
                    [
                        str(_script("ingest_market_history.py")),
                        "--coinapi",
                        "--coinapi-pairs",
                        "BTC/USD,ETH/USD,XRP/USD,SOL/USD",
                        "--coinapi-period",
                        "1MIN",
                        "--days",
                        "365",
                    ],
                ),
            ),
        )
    )
    plan.append(
        (
            "[6/7] Economic calendar + events",
            _add_db_arg(
                args,
                [
                    str(_script("ingest_economic_calendar.py")),
                    "--sources",
                    "all",
                    "--seed-events",
                    "true",
                ],
            ),
        )
    )
    plan.append(
        (
            "[7/7] Queen knowledge ingest (memories/insights/thoughts/strategies)",
            _add_db_arg(
                args,
                [
                    str(_script("ingest_queen_knowledge.py")),
                    "--sources",
                    "all",
                ],
            ),
        )
    )
    return plan


def _max_plan(args: argparse.Namespace) -> List[Tuple[str, List[str]]]:
    """
    A "data pyramid":
    - wide: daily bars for broad CoinAPI SPOT universe (quote-filtered by default)
    - deep: minute bars for majors (recent window)
    - optional: trade ticks for a few majors (very heavy)
    """
    plan: List[Tuple[str, List[str]]] = []

    if not args.skip_account_sync:
        plan.append(
            (
                "[1/8] Sync account trades (Kraken, Binance, Alpaca, Capital; budgeted)",
                _account_sync_cmd(args),
            )
        )

    plan.append(
        (
            "[2/8] yfinance broad ingest (10y daily, all categories)",
            _maybe_add_no_resume(
                args,
                _add_db_arg(args, [str(_script("ingest_yfinance.py")), "--all", "--days", "3650"]),
            ),
        )
    )

    plan.append(
        (
            "[3/8] FRED macro indicators",
            _maybe_add_no_resume(args, _add_db_arg(args, [str(_script("ingest_fred.py")), "--category", "all"])),
        )
    )

    plan.append(
        (
            "[4/8] Existing feeds (CoinGecko, news, Glassnode, Coinbase, macro)",
            _add_db_arg(args, [str(_script("ingest_existing_feeds.py")), "--feeds", "all"]),
        )
    )

    # CoinAPI wide daily ingest
    coinapi_quotes = args.coinapi_quote_assets.strip()
    coinapi_daily_cmd = [
        str(_script("ingest_market_history.py")),
        "--coinapi-index",
        "--coinapi-all-symbols",
        "--coinapi-period",
        "1DAY",
        "--coinapi-symbol-type",
        (args.coinapi_symbol_type or "").strip(),
        "--days",
        str(int(args.coinapi_daily_days)),
    ]
    if coinapi_quotes:
        coinapi_daily_cmd += ["--coinapi-quote-assets", coinapi_quotes]
    if args.coinapi_symbol_limit and int(args.coinapi_symbol_limit) > 0:
        coinapi_daily_cmd += ["--coinapi-symbol-limit", str(int(args.coinapi_symbol_limit))]
    coinapi_daily_cmd = _maybe_add_no_resume(args, _add_db_arg(args, coinapi_daily_cmd))

    plan.append(("[5/8] CoinAPI: index + wide daily bars (resumable)", coinapi_daily_cmd))

    # CoinAPI deep (minute) for majors (recent)
    majors_pairs = "BTC/USD,ETH/USD,SOL/USD,XRP/USD,BNB/USD,DOGE/USD"
    coinapi_minute_cmd = [
        str(_script("ingest_market_history.py")),
        "--coinapi",
        "--coinapi-pairs",
        majors_pairs,
        "--coinapi-period",
        "1MIN",
        "--coinapi-exchanges",
        "BINANCE,COINBASE,KRAKEN",
        "--coinapi-max-symbols",
        "10",
        "--days",
        str(int(args.coinapi_minute_days)),
    ]
    if args.include_trades:
        coinapi_minute_cmd += ["--coinapi-trades"]
    coinapi_minute_cmd = _maybe_add_no_resume(args, _add_db_arg(args, coinapi_minute_cmd))
    plan.append(("[6/8] CoinAPI: deep minute bars for majors (recent)", coinapi_minute_cmd))

    # Alpaca minute bars for key equities/ETFs (recent)
    alpaca_stocks = "SPY,QQQ,DIA,IWM,AAPL,MSFT,NVDA,TSLA,AMZN,GOOGL,META,GLD,TLT"
    alpaca_cmd = [
        str(_script("ingest_market_history.py")),
        "--alpaca",
        "--alpaca-stocks",
        alpaca_stocks,
        "--alpaca-timeframe",
        "1Min",
        "--alpaca-feed",
        "iex",
        "--days",
        str(int(args.alpaca_minute_days)),
    ]
    alpaca_cmd = _maybe_add_no_resume(args, _add_db_arg(args, alpaca_cmd))
    plan.append(("[7/8] Alpaca: minute bars for core equities/ETFs (recent)", alpaca_cmd))

    plan.append(
        (
            "[8/8] Economic calendar + Queen knowledge",
            # Run both scripts sequentially via the orchestrator; we keep this as a
            # "meta-step" so the user sees one header in logs.
            ["__AUREON_META_STEP__"],
        )
    )

    return plan


def _unsafe_all_plan(args: argparse.Namespace) -> List[Tuple[str, List[str]]]:
    plan = _max_plan(args)

    # Replace the wide CoinAPI daily step with an unfiltered ingest attempt.
    widened: List[Tuple[str, List[str]]] = []
    for name, cmd in plan:
        if name.startswith("[5/8] CoinAPI: index + wide daily bars"):
            cmd2 = [
                str(_script("ingest_market_history.py")),
                "--coinapi-index",
                "--coinapi-all-symbols",
                "--coinapi-period",
                "1DAY",
                "--days",
                str(int(args.coinapi_daily_days)),
            ]
            if args.coinapi_symbol_limit and int(args.coinapi_symbol_limit) > 0:
                cmd2 += ["--coinapi-symbol-limit", str(int(args.coinapi_symbol_limit))]
            cmd2 = _maybe_add_no_resume(args, _add_db_arg(args, cmd2))
            widened.append(("[5/8] CoinAPI: UNSAFE all-symbols daily ingest (no filters)", cmd2))
        else:
            widened.append((name, cmd))
    return widened


def main() -> int:
    ap = argparse.ArgumentParser(description="Build Aureon's single-file global memory dataset.")
    ap.add_argument("--profile", default="standard", choices=["standard", "max", "unsafe-all"])
    ap.add_argument("--db", default="", help="SQLite DB path override (default: state/aureon_global_history.sqlite)")
    ap.add_argument("--no-resume", action="store_true", help="Ignore watermarks and re-ingest from scratch where supported")
    ap.add_argument("--dry-run", action="store_true", help="Print the planned commands without executing")

    # Max/unsafe profile tuning knobs (kept simple; defaults are sane).
    ap.add_argument("--coinapi-symbol-type", default="SPOT", help="CoinAPI symbol_type filter for wide ingest (max profile)")
    ap.add_argument(
        "--coinapi-quote-assets",
        default="USD,USDT,USDC,EUR,GBP",
        help="CSV quote-asset filter for wide CoinAPI ingest (blank=all; max profile)",
    )
    ap.add_argument("--coinapi-symbol-limit", type=int, default=0, help="Cap CoinAPI all-symbols universe (0=all)")
    ap.add_argument("--coinapi-daily-days", type=int, default=3650, help="Days of daily CoinAPI history for wide ingest")
    ap.add_argument("--coinapi-minute-days", type=int, default=180, help="Days of minute CoinAPI history for majors")
    ap.add_argument("--alpaca-minute-days", type=int, default=30, help="Days of Alpaca minute bars for equities/ETFs")
    ap.add_argument("--include-trades", action="store_true", help="Also ingest heavy trade ticks in deep CoinAPI step")
    ap.add_argument("--skip-account-sync", action="store_true", help="Skip private exchange account-history endpoints")
    ap.add_argument("--account-sync-max-kraken", type=int, default=50, help="Max Kraken private trades per cycle")
    ap.add_argument("--account-sync-binance-limit", type=int, default=200, help="Binance private trades per symbol per cycle")
    ap.add_argument("--account-sync-alpaca-limit", type=int, default=200, help="Alpaca closed orders per cycle")

    args = ap.parse_args()

    if args.profile == "standard":
        plan = _standard_plan(args)
    elif args.profile == "max":
        plan = _max_plan(args)
    else:
        plan = _unsafe_all_plan(args)

    print("AUREON GLOBAL MEMORY INGEST")
    print(f"Repo: {_REPO_ROOT}")
    print(f"Profile: {args.profile}")
    if args.db:
        print(f"DB: {args.db}")
    else:
        print("DB: (default) state/aureon_global_history.sqlite")
    print(f"Resume: {'off' if args.no_resume else 'on'}")
    print(f"Dry-run: {'yes' if args.dry_run else 'no'}")

    failures: List[Tuple[str, int]] = []

    for step_name, cmd in plan:
        if cmd == ["__AUREON_META_STEP__"]:
            # Keep calendar + queen as separate actual runs so failures are reported properly.
            rc1 = _run_step(
                "[calendar] Economic calendar + events",
                _add_db_arg(
                    args,
                    [
                        str(_script("ingest_economic_calendar.py")),
                        "--sources",
                        "all",
                        "--seed-events",
                        "true",
                    ],
                ),
                dry_run=bool(args.dry_run),
            )
            if rc1 != 0:
                failures.append(("[calendar] Economic calendar + events", rc1))

            rc2 = _run_step(
                "[queen] Queen knowledge ingest",
                _add_db_arg(args, [str(_script("ingest_queen_knowledge.py")), "--sources", "all"]),
                dry_run=bool(args.dry_run),
            )
            if rc2 != 0:
                failures.append(("[queen] Queen knowledge ingest", rc2))
            continue

        rc = _run_step(step_name, cmd, dry_run=bool(args.dry_run))
        if rc != 0:
            failures.append((step_name, rc))

    # Print DB stats (best-effort).
    try:
        from aureon.core import aureon_global_history_db as ghdb  # type: ignore

        paths = ghdb.resolve_paths(args.db or None)
        _print_db_stats(paths.db_path)
    except Exception:
        # Fallback: if imports fail for some reason, try to resolve common default.
        default = Path(args.db) if args.db else (_REPO_ROOT / "state" / "aureon_global_history.sqlite")
        if default.exists():
            _print_db_stats(default)

    if failures:
        print()
        print("=" * 80)
        print("INGEST COMPLETED WITH ERRORS")
        print("=" * 80)
        for name, rc in failures:
            print(f"- {name}: exit {rc}")
        return 1

    print()
    print("=" * 80)
    print("INGEST COMPLETE")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

