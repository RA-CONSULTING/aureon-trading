#!/usr/bin/env python3
"""
Sync a single-file SQLite history DB from all configured exchange accounts.

This uses your API keys (private endpoints) to pull *your* account activity
and store it in one append-only database file that Aureon can query as memory.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make this script runnable from any working directory by ensuring repo imports work.
_REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (
    _REPO_ROOT,
    _REPO_ROOT / "aureon" / "core",
    _REPO_ROOT / "aureon" / "exchanges",
    _REPO_ROOT / "aureon" / "data_feeds",
    _REPO_ROOT / "aureon" / "monitors",
):
    _sp = str(_p)
    if _sp not in sys.path:
        sys.path.insert(0, _sp)

try:
    from aureon_baton_link import link_system as _baton_link

    _baton_link(__name__)
except Exception:
    pass

import argparse
import json
import os
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

from aureon.core.aureon_global_history_db import connect, insert_account_trade, get_last_trade_ts_ms, resolve_paths


def _load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        return
    try:
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
    except Exception:
        return


def _parse_since(value: str) -> int:
    """
    Returns epoch milliseconds.
    Accepts:
    - unix seconds/ms (int string)
    - ISO date/time
    """
    value = (value or "").strip()
    if not value:
        return 0
    if value.isdigit():
        num = int(value)
        # Heuristic: treat > 10^12 as ms, else seconds.
        return num if num > 1_000_000_000_000 else (num * 1000)
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)
    except Exception:
        raise ValueError(f"Unsupported --since value: {value!r}")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_dumps_safe(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=True, sort_keys=True)
    except Exception:
        try:
            return json.dumps(str(obj), ensure_ascii=True)
        except Exception:
            return "{}"


@dataclass(frozen=True)
class SyncResult:
    venue: str
    fetched: int
    inserted: int
    skipped: int
    error: str = ""


def _normalize_kraken_trade(trade: Dict[str, Any]) -> Dict[str, Any]:
    base = str(trade.get("base", "") or "").upper()
    quote = str(trade.get("quote", "") or "").upper()
    pair = str(trade.get("pair", "") or "").upper()
    symbol = f"{base}{quote}" if base and quote else pair
    ts_ms = int(float(trade.get("time", 0) or 0.0) * 1000)
    trade_id = str(trade.get("id") or "")
    return {
        "venue": "kraken",
        "trade_id": trade_id,
        "symbol": symbol,
        "side": str(trade.get("type", "") or "").upper(),
        "qty": float(trade.get("vol", 0) or 0),
        "price": float(trade.get("price", 0) or 0),
        "cost": float(trade.get("cost", 0) or 0),
        "fee": float(trade.get("fee", 0) or 0),
        "fee_asset": quote or "",
        "ts_ms": ts_ms if ts_ms > 0 else None,
        "raw_json": _json_dumps_safe(trade),
    }


def _normalize_binance_trade(symbol: str, trade: Dict[str, Any]) -> Dict[str, Any]:
    sym = str(symbol or trade.get("symbol", "") or "").upper()
    trade_id = str(trade.get("id") or trade.get("tradeId") or "")
    if sym and trade_id:
        trade_id = f"{sym}:{trade_id}"
    side = "BUY" if bool(trade.get("isBuyer", False)) else "SELL"
    qty = float(trade.get("qty", 0) or 0)
    price = float(trade.get("price", 0) or 0)
    quote_qty = float(trade.get("quoteQty", 0) or 0) if "quoteQty" in trade else (qty * price)
    ts_ms = int(trade.get("time", 0) or 0)
    return {
        "venue": "binance",
        "trade_id": trade_id,
        "symbol": sym,
        "side": side,
        "qty": qty,
        "price": price,
        "cost": quote_qty,
        "fee": float(trade.get("commission", 0) or 0),
        "fee_asset": str(trade.get("commissionAsset", "") or ""),
        "ts_ms": ts_ms if ts_ms > 0 else None,
        "raw_json": _json_dumps_safe(trade),
    }


def _normalize_alpaca_order(order: Dict[str, Any], fee_usd: float) -> Optional[Dict[str, Any]]:
    if str(order.get("status", "") or "").lower() != "filled":
        return None
    order_id = str(order.get("id") or "")
    symbol = str(order.get("symbol", "") or "").upper()
    side = str(order.get("side", "") or "").upper()
    qty = float(order.get("filled_qty", 0) or 0)
    price = float(order.get("filled_avg_price", 0) or 0)
    if qty <= 0 or price <= 0 or not order_id:
        return None
    ts_raw = order.get("filled_at") or order.get("updated_at") or order.get("submitted_at") or ""
    ts_ms: Optional[int] = None
    if ts_raw:
        try:
            dt = datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            ts_ms = int(dt.timestamp() * 1000)
        except Exception:
            ts_ms = None
    return {
        "venue": "alpaca",
        "trade_id": order_id,
        "symbol": symbol,
        "side": side,
        "qty": qty,
        "price": price,
        "cost": qty * price,
        "fee": float(fee_usd or 0.0),
        "fee_asset": "USD",
        "ts_ms": ts_ms,
        "raw_json": _json_dumps_safe(order),
    }


def _normalize_capital_activity(activity: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    epic = str(activity.get("epic", "") or activity.get("details", {}).get("epic", "") or "").upper()
    details = activity.get("details", {}) if isinstance(activity.get("details"), dict) else {}
    direction = str(details.get("direction", "") or activity.get("direction", "") or "").upper()
    size = float(details.get("size", 0) or activity.get("size", 0) or 0)
    level = float(details.get("level", 0) or activity.get("level", 0) or 0)
    if not epic or size <= 0 or level <= 0 or not direction:
        return None

    # Capital provides different identifiers depending on activity type.
    base_id = (
        str(details.get("dealId") or activity.get("dealId") or "")
        or str(details.get("dealReference") or activity.get("dealReference") or "")
        or str(activity.get("id") or "")
    )
    if not base_id:
        base_id = f"{epic}:{abs(hash(_json_dumps_safe(activity))) & 0xFFFFFFFFFFFF:x}"

    ts_ms: Optional[int] = None
    ts_raw = activity.get("dateUTC") or activity.get("date") or activity.get("timestamp") or ""
    if ts_raw:
        try:
            dt = datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            ts_ms = int(dt.timestamp() * 1000)
        except Exception:
            ts_ms = None

    activity_type = str(activity.get("type") or "").upper()
    status = str(activity.get("status") or "").upper()
    ts_key = str(ts_raw or "")
    trade_id = f"{base_id}:{activity_type or 'ACT'}:{status or 'NA'}:{ts_key}"

    return {
        "venue": "capital",
        "trade_id": trade_id,
        "symbol": epic,
        "side": direction,
        "qty": size,
        "price": level,
        "cost": size * level,
        "fee": 0.0,
        "fee_asset": "",
        "ts_ms": ts_ms,
        "raw_json": _json_dumps_safe(activity),
    }


def _sync_kraken(conn: sqlite3.Connection, since_ms: int, max_records: int) -> SyncResult:
    os.environ.setdefault("KRAKEN_DRY_RUN", "false")
    try:
        from aureon.exchanges.kraken_client import KrakenClient
    except Exception as e:
        return SyncResult("kraken", 0, 0, 0, error=str(e))

    try:
        client = KrakenClient()
    except Exception as e:
        return SyncResult("kraken", 0, 0, 0, error=str(e))

    if client.dry_run or not getattr(client, "api_key", "") or not getattr(client, "api_secret", ""):
        return SyncResult("kraken", 0, 0, 0, error="keys_missing_or_dry_run")

    since_sec = int(since_ms / 1000) if since_ms else None
    trades = client.get_trades_history(since=since_sec, max_records=max_records)
    inserted = 0
    skipped = 0
    for t in trades:
        norm = _normalize_kraken_trade(t)
        if not norm.get("trade_id"):
            skipped += 1
            continue
        if insert_account_trade(conn, norm):
            inserted += 1
        else:
            skipped += 1
    conn.commit()
    return SyncResult("kraken", fetched=len(trades), inserted=inserted, skipped=skipped)


def _sync_binance(conn: sqlite3.Connection, since_ms: int, limit_per_symbol: int) -> SyncResult:
    os.environ.setdefault("BINANCE_DRY_RUN", "false")
    try:
        from aureon.exchanges.binance_client import BinanceClient
    except Exception as e:
        return SyncResult("binance", 0, 0, 0, error=str(e))

    try:
        client = BinanceClient()
    except Exception as e:
        return SyncResult("binance", 0, 0, 0, error=str(e))

    # Reuse helper that figures out relevant symbols from balances.
    try:
        trades_by_symbol = client.get_all_my_trades(symbols=None, limit_per_symbol=limit_per_symbol)
    except Exception as e:
        return SyncResult("binance", 0, 0, 0, error=str(e))

    inserted = 0
    skipped = 0
    fetched = 0
    for sym, trades in (trades_by_symbol or {}).items():
        for t in trades or []:
            fetched += 1
            norm = _normalize_binance_trade(sym, t)
            if since_ms and norm.get("ts_ms") and int(norm["ts_ms"]) < since_ms:
                skipped += 1
                continue
            if not norm.get("trade_id"):
                skipped += 1
                continue
            if insert_account_trade(conn, norm):
                inserted += 1
            else:
                skipped += 1
    conn.commit()
    return SyncResult("binance", fetched=fetched, inserted=inserted, skipped=skipped)


def _sync_alpaca(conn: sqlite3.Connection, since_ms: int, limit: int) -> SyncResult:
    os.environ.setdefault("ALPACA_DRY_RUN", "false")
    try:
        from aureon.exchanges.alpaca_client import AlpacaClient
    except Exception as e:
        return SyncResult("alpaca", 0, 0, 0, error=str(e))

    try:
        client = AlpacaClient()
    except Exception as e:
        return SyncResult("alpaca", 0, 0, 0, error=str(e))

    try:
        orders = client.get_all_orders(status="closed", limit=min(500, int(limit or 500)))
    except Exception as e:
        return SyncResult("alpaca", 0, 0, 0, error=str(e))

    inserted = 0
    skipped = 0
    fetched = 0
    for order in orders or []:
        try:
            fee_usd = float(client.compute_order_fees_in_quote(order, primary_quote="USD") or 0.0)
        except Exception:
            fee_usd = 0.0
        norm = _normalize_alpaca_order(order, fee_usd=fee_usd)
        fetched += 1
        if not norm:
            skipped += 1
            continue
        if since_ms and norm.get("ts_ms") and int(norm["ts_ms"]) < since_ms:
            skipped += 1
            continue
        if insert_account_trade(conn, norm):
            inserted += 1
        else:
            skipped += 1
    conn.commit()
    return SyncResult("alpaca", fetched=fetched, inserted=inserted, skipped=skipped)


def _sync_capital(conn: sqlite3.Connection, since_ms: int) -> SyncResult:
    os.environ.setdefault("CAPITAL_HTTP_TIMEOUT_SECS", os.getenv("CAPITAL_HTTP_TIMEOUT_SECS", "25"))
    try:
        from aureon.exchanges.capital_client import CapitalClient
    except Exception as e:
        return SyncResult("capital", 0, 0, 0, error=str(e))

    try:
        client = CapitalClient()
    except Exception as e:
        return SyncResult("capital", 0, 0, 0, error=str(e))

    if not getattr(client, "enabled", False):
        return SyncResult("capital", 0, 0, 0, error=str(getattr(client, "init_error", "") or "client_disabled"))

    from_date: Optional[str] = None
    if since_ms:
        try:
            # Capital `/history/activity` expects `YYYY-MM-DDTHH:MM:SS` (no timezone suffix).
            from_date = datetime.fromtimestamp(since_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        except Exception:
            from_date = None

    try:
        activities = client.get_order_history(from_date=from_date)
    except Exception as e:
        return SyncResult("capital", 0, 0, 0, error=str(e))

    inserted = 0
    skipped = 0
    fetched = 0
    for activity in activities or []:
        fetched += 1
        norm = _normalize_capital_activity(activity)
        if not norm:
            skipped += 1
            continue
        if since_ms and norm.get("ts_ms") and int(norm["ts_ms"]) < since_ms:
            skipped += 1
            continue
        if insert_account_trade(conn, norm):
            inserted += 1
        else:
            skipped += 1
    conn.commit()
    return SyncResult("capital", fetched=fetched, inserted=inserted, skipped=skipped)


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync Aureon global history SQLite DB from exchange accounts")
    parser.add_argument("--db", default="", help="SQLite DB path (default: state/aureon_global_history.sqlite)")
    parser.add_argument("--venues", default="kraken,binance,alpaca,capital", help="Comma-separated venues to sync")
    parser.add_argument("--since", default="", help="Only keep trades on/after this time (ISO or unix seconds/ms)")
    parser.add_argument("--binance-limit", type=int, default=1000, help="Binance trades per symbol (max 1000)")
    parser.add_argument("--alpaca-limit", type=int, default=500, help="Alpaca closed orders to fetch (max 500)")
    parser.add_argument("--max-kraken", type=int, default=5000, help="Max Kraken trades to request (paged)")
    args = parser.parse_args()

    paths = resolve_paths(args.db or None)
    _load_env_file(paths.repo_root / ".env")

    conn = connect(str(paths.db_path))

    venues = [v.strip().lower() for v in str(args.venues or "").split(",") if v.strip()]
    since_ms = _parse_since(args.since) if args.since else 0

    results: List[SyncResult] = []
    for venue in venues:
        effective_since = since_ms
        if not effective_since:
            last = get_last_trade_ts_ms(conn, venue)
            # Back up a bit to make sync idempotent around boundary trades.
            effective_since = max(0, int(last or 0) - 6 * 60 * 60 * 1000)

        if venue == "kraken":
            results.append(_sync_kraken(conn, effective_since, max_records=int(args.max_kraken)))
        elif venue == "binance":
            results.append(_sync_binance(conn, effective_since, limit_per_symbol=min(1000, int(args.binance_limit))))
        elif venue == "alpaca":
            results.append(_sync_alpaca(conn, effective_since, limit=int(args.alpaca_limit)))
        elif venue == "capital":
            results.append(_sync_capital(conn, effective_since))
        else:
            results.append(SyncResult(venue, 0, 0, 0, error="unknown_venue"))

    print("")
    print("AUREON GLOBAL HISTORY SYNC")
    print(f"DB: {paths.db_path}")
    print(f"UTC: {_utc_now_iso()}")
    print("")
    for r in results:
        status = "OK" if not r.error else f"SKIP ({r.error})"
        print(f"- {r.venue:7s} {status:24s} fetched={r.fetched:6d} inserted={r.inserted:6d} skipped={r.skipped:6d}")

    print("")
    print("Next: query via sqlite (example)")
    print(f"  sqlite3 \"{paths.db_path}\" \"select venue, symbol, count(*) from account_trades group by 1,2 order by 3 desc limit 15;\"")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
