#!/usr/bin/env python3
"""
Ingest global financial historical data from Yahoo Finance (yfinance) into
Aureon's single-file global history database.

Uses the free yfinance library (no API key needed) to download OHLCV bars for:
  - US Stocks, Global Indices, Forex, Commodities, Crypto, ETFs

Data is stored in the ``market_bars`` table with provider="yfinance", venue="yahoo".
Watermarks are used for resumable ingestion (same pattern as CoinAPI / Alpaca ingest).

Usage examples:
    python scripts/python/ingest_yfinance.py --all --days 1825
    python scripts/python/ingest_yfinance.py --category stocks --interval 1d
    python scripts/python/ingest_yfinance.py --stocks AAPL,MSFT --start 2023-01-01
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# Repo-root / sys.path setup (same as ingest_market_history.py)
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv(_REPO_ROOT / ".env")
except Exception:
    pass

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PROVIDER = "yfinance"
VENUE = "yahoo"

# Default symbol universes
DEFAULT_STOCKS = "AAPL,MSFT,GOOGL,AMZN,NVDA,META,TSLA,JPM,V,JNJ,WMT,PG,UNH,HD,BAC"
DEFAULT_INDICES = "^GSPC,^DJI,^IXIC,^FTSE,^N225,^HSI,^GDAXI,^FCHI,^STOXX50E,^BVSP,^AXJO,^KS11,^TWII,^NSEI"
DEFAULT_FOREX = "EURUSD=X,GBPUSD=X,USDJPY=X,USDCHF=X,AUDUSD=X,USDCAD=X,NZDUSD=X,EURGBP=X,EURJPY=X,GBPJPY=X,USDCNY=X,USDINR=X,USDBRL=X,USDMXN=X,USDZAR=X"
DEFAULT_COMMODITIES = "GC=F,SI=F,CL=F,NG=F,HG=F,PL=F,PA=F,ZW=F,ZC=F,ZS=F,KC=F,CC=F,CT=F,LBS=F"
DEFAULT_CRYPTO = "BTC-USD,ETH-USD,XRP-USD,SOL-USD,ADA-USD,DOGE-USD,DOT-USD,AVAX-USD,LINK-USD,MATIC-USD"
DEFAULT_ETFS = "SPY,QQQ,IWM,EEM,TLT,GLD,USO,VXX,XLF,XLE,XLK,XLV,ARKK"

# Map yfinance interval strings to CoinAPI-style period_id for consistent storage.
_INTERVAL_TO_PERIOD_ID = {
    "1m": "1MIN",
    "2m": "2MIN",
    "5m": "5MIN",
    "15m": "15MIN",
    "30m": "30MIN",
    "60m": "60MIN",
    "90m": "90MIN",
    "1h": "60MIN",
    "1d": "1DAY",
    "5d": "5DAY",
    "1wk": "7DAY",
    "1mo": "30DAY",
    "3mo": "90DAY",
}

# Batch size for yfinance.download() calls (number of tickers per batch).
_BATCH_SIZE = 20

# Sleep between batches to be polite to Yahoo servers.
_BATCH_SLEEP = 1.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _parse_csv(value: str) -> List[str]:
    return [v.strip() for v in str(value or "").split(",") if v.strip()]


def _json_dumps_safe(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=True, separators=(",", ":"), default=str)
    except Exception:
        return "{}"


def _dt_from_ms(ts_ms: int) -> datetime:
    return datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)


def _insert_market_bars(conn: sqlite3.Connection, rows: Sequence[Tuple[Any, ...]]) -> Tuple[int, int]:
    """Insert bar rows with INSERT OR IGNORE. Returns (inserted, skipped)."""
    if not rows:
        return (0, 0)
    stmt = """
        INSERT OR IGNORE INTO market_bars(
            provider, venue, symbol_id, symbol, period_id,
            time_start_ms, time_end_ms,
            open, high, low, close, volume, trades_count,
            ingested_at_ms,
            raw_json
        )
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    before = conn.total_changes
    conn.executemany(stmt, rows)
    inserted = conn.total_changes - before
    skipped = len(rows) - inserted
    return inserted, skipped


def _period_id_for_interval(interval: str) -> str:
    return _INTERVAL_TO_PERIOD_ID.get(interval, interval.upper())


def _period_seconds(period_id: str) -> int:
    """Rough seconds for a period id, used to compute time_end_ms."""
    p = period_id.upper()
    for suffix, mult in (("MIN", 60), ("HRS", 3600), ("DAY", 86400)):
        if p.endswith(suffix):
            try:
                return int(p[: -len(suffix)]) * mult
            except Exception:
                return 86400
    return 86400


# ---------------------------------------------------------------------------
# Core ingestion logic
# ---------------------------------------------------------------------------
def _ingest_symbols(
    conn: sqlite3.Connection,
    symbols: List[str],
    category: str,
    start_dt: datetime,
    end_dt: datetime,
    interval: str,
    no_resume: bool,
) -> None:
    """Download and store OHLCV bars for *symbols* using yfinance."""
    try:
        import yfinance as yf
    except ImportError:
        print("[yfinance] ERROR: yfinance is not installed. Run: pip install yfinance")
        return

    from aureon.core import aureon_global_history_db as ghdb  # type: ignore

    period_id = _period_id_for_interval(interval)
    p_secs = _period_seconds(period_id)
    ingested_at_ms = int(time.time() * 1000)

    # Filter symbols that already have a watermark past end_dt (unless --no-resume).
    work: List[str] = []
    for sym in symbols:
        if no_resume:
            work.append(sym)
            continue
        wm_key = f"bars:{PROVIDER}:{sym}:{period_id}"
        wm = ghdb.get_watermark_ms(conn, wm_key)
        if wm is not None and wm >= int(end_dt.timestamp() * 1000):
            continue
        work.append(sym)

    if not work:
        print(f"[yfinance] {category}: all {len(symbols)} symbols already up to date")
        return

    print(f"[yfinance] {category}: ingesting {len(work)} symbols ({interval} bars)")

    total_inserted = 0
    total_skipped = 0

    # Process in batches.
    for batch_start in range(0, len(work), _BATCH_SIZE):
        batch = work[batch_start : batch_start + _BATCH_SIZE]

        # Determine effective start per symbol (use watermarks).
        # We use the earliest effective start for the batch download, then filter per-symbol.
        earliest_start = start_dt
        sym_starts: Dict[str, datetime] = {}
        for sym in batch:
            wm_key = f"bars:{PROVIDER}:{sym}:{period_id}"
            wm = None if no_resume else ghdb.get_watermark_ms(conn, wm_key)
            if wm is not None:
                sym_start = max(start_dt, _dt_from_ms(int(wm) + 1))
            else:
                sym_start = start_dt
            sym_starts[sym] = sym_start
            if sym_start < earliest_start:
                earliest_start = sym_start

        try:
            df = yf.download(
                tickers=batch,
                start=earliest_start.strftime("%Y-%m-%d"),
                end=end_dt.strftime("%Y-%m-%d"),
                interval=interval,
                auto_adjust=True,
                progress=False,
                threads=True,
                group_by="ticker",
            )
        except Exception as exc:
            print(f"[yfinance] download error for batch {batch[:3]}...: {exc}")
            time.sleep(_BATCH_SLEEP)
            continue

        if df is None or df.empty:
            time.sleep(_BATCH_SLEEP)
            continue

        # When a single ticker is requested, yfinance returns flat columns
        # (Open, High, ...) instead of MultiIndex (TICKER, Open, ...).
        is_single = len(batch) == 1

        for sym in batch:
            try:
                if is_single:
                    sym_df = df
                else:
                    # Multi-ticker download has MultiIndex columns: (ticker, field)
                    if sym not in df.columns.get_level_values(0):
                        continue
                    sym_df = df[sym]

                if sym_df.empty:
                    continue

                sym_df = sym_df.dropna(subset=["Open", "High", "Low", "Close"])
                if sym_df.empty:
                    continue

            except Exception:
                continue

            # Build rows.
            rows: List[Tuple[Any, ...]] = []
            max_ts_ms: Optional[int] = None
            sym_start = sym_starts.get(sym, start_dt)

            for idx, row in sym_df.iterrows():
                # idx is a Timestamp (pandas)
                try:
                    ts = idx.to_pydatetime()
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                    ts_start_ms = int(ts.timestamp() * 1000)
                except Exception:
                    continue

                # Skip rows before this symbol's effective start.
                if ts_start_ms < int(sym_start.timestamp() * 1000):
                    continue

                ts_end_ms = ts_start_ms + (p_secs * 1000)

                o = float(row.get("Open", 0) or 0)
                h = float(row.get("High", 0) or 0)
                l_ = float(row.get("Low", 0) or 0)
                c = float(row.get("Close", 0) or 0)
                v = float(row.get("Volume", 0) or 0)

                if max_ts_ms is None or ts_end_ms > max_ts_ms:
                    max_ts_ms = ts_end_ms

                raw = {
                    "t": ts.isoformat(),
                    "o": o,
                    "h": h,
                    "l": l_,
                    "c": c,
                    "v": v,
                }

                rows.append((
                    PROVIDER,
                    VENUE,
                    sym,        # symbol_id
                    sym,        # symbol
                    period_id,
                    ts_start_ms,
                    ts_end_ms,
                    o, h, l_, c, v,
                    0,          # trades_count (not available from yfinance)
                    ingested_at_ms,
                    _json_dumps_safe(raw),
                ))

            ins, skip = _insert_market_bars(conn, rows)
            total_inserted += ins
            total_skipped += skip

            # Update watermark.
            if max_ts_ms is not None:
                wm_key = f"bars:{PROVIDER}:{sym}:{period_id}"
                ghdb.set_watermark_ms(conn, wm_key, int(max_ts_ms))

        conn.commit()

        if batch_start + _BATCH_SIZE < len(work):
            time.sleep(_BATCH_SLEEP)

    print(
        f"[yfinance] {category}: done — inserted={total_inserted} "
        f"skipped={total_skipped}"
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Ingest Yahoo Finance OHLCV data into Aureon global history DB.",
    )
    p.add_argument("--db", default=None, help="SQLite DB path override")
    p.add_argument("--no-resume", action="store_true", help="Ignore watermarks, re-download everything")
    p.add_argument("--start", default=None, help="ISO start date (e.g. 2020-01-01)")
    p.add_argument("--end", default=None, help="ISO end date (e.g. 2025-12-31)")
    p.add_argument("--days", type=int, default=1825, help="Default lookback in days (default: 1825 = ~5 years)")
    p.add_argument("--interval", default="1d", help="yfinance interval: 1d, 1h, 5m, etc (default: 1d)")

    p.add_argument("--stocks", default=None, help="CSV of stock symbols")
    p.add_argument("--indices", default=None, help="CSV of index symbols")
    p.add_argument("--forex", default=None, help="CSV of forex symbols")
    p.add_argument("--commodities", default=None, help="CSV of commodity symbols")
    p.add_argument("--crypto", default=None, help="CSV of crypto symbols")
    p.add_argument("--etfs", default=None, help="CSV of ETF symbols")

    p.add_argument("--all", action="store_true", help="Ingest all default universes")
    p.add_argument(
        "--category",
        default=None,
        help="Ingest specific category: stocks,indices,forex,commodities,crypto,etfs",
    )
    return p


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    # Time range ----------------------------------------------------------------
    now = datetime.now(tz=timezone.utc)
    if args.end:
        end_dt = datetime.fromisoformat(args.end)
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=timezone.utc)
    else:
        end_dt = now

    if args.start:
        start_dt = datetime.fromisoformat(args.start)
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=timezone.utc)
    else:
        start_dt = end_dt - timedelta(days=args.days)

    print(f"[yfinance] time range: {start_dt.date()} -> {end_dt.date()}")
    print(f"[yfinance] interval: {args.interval}")

    # DB connection --------------------------------------------------------------
    from aureon.core import aureon_global_history_db as ghdb  # type: ignore

    conn = ghdb.connect(args.db)
    print(f"[yfinance] database: {ghdb.resolve_paths(args.db).db_path}")

    # Build work plan ------------------------------------------------------------
    categories_requested = _parse_csv(args.category) if args.category else []
    categories_requested = [c.lower().strip() for c in categories_requested]

    plan: List[Tuple[str, List[str]]] = []

    def _should_run(cat: str, cli_symbols: Optional[str], default_symbols: str) -> None:
        if cli_symbols is not None:
            plan.append((cat, _parse_csv(cli_symbols)))
        elif args.all or cat in categories_requested:
            plan.append((cat, _parse_csv(default_symbols)))

    _should_run("stocks", args.stocks, DEFAULT_STOCKS)
    _should_run("indices", args.indices, DEFAULT_INDICES)
    _should_run("forex", args.forex, DEFAULT_FOREX)
    _should_run("commodities", args.commodities, DEFAULT_COMMODITIES)
    _should_run("crypto", args.crypto, DEFAULT_CRYPTO)
    _should_run("etfs", args.etfs, DEFAULT_ETFS)

    if not plan:
        print("[yfinance] nothing to do. Use --all, --category, or --stocks/--indices/... flags.")
        conn.close()
        return

    # Execute --------------------------------------------------------------------
    for category, symbols in plan:
        _ingest_symbols(
            conn=conn,
            symbols=symbols,
            category=category,
            start_dt=start_dt,
            end_dt=end_dt,
            interval=args.interval,
            no_resume=args.no_resume,
        )

    conn.close()
    print("[yfinance] all done.")


if __name__ == "__main__":
    main()
