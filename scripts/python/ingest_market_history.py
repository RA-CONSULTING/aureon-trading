#!/usr/bin/env python3
"""
Ingest market history into Aureon's single-file global history database.

This is a pragmatic "master dataset" builder:
- Your private account history is handled by sync_global_history_db.py
- This script adds *public* market history (OHLCV bars, optionally trades)

Important reality check:
Downloading "every single trade ever recorded" across all global markets is
not feasible with typical API plans (data volume, cost, rate limits, licenses).
This script is built to scale up safely by:
- explicit symbol selection
- explicit time bounds
- resumable watermarks stored in SQLite
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
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


# Make this script runnable from any working directory by ensuring repo imports work.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv(_REPO_ROOT / ".env")
except Exception:
    pass


def _json_dumps_safe(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=True, separators=(",", ":"), default=str)
    except Exception:
        try:
            return json.dumps({"_unserializable": True, "repr": repr(obj)}, ensure_ascii=True, separators=(",", ":"))
        except Exception:
            return "{}"


def _parse_dt(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _dt_to_iso_z(dt: datetime) -> str:
    # CoinAPI is strict: it rejects fractional seconds for time_start/time_end.
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _dt_from_ms(ts_ms: int) -> datetime:
    return datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)


def _period_to_seconds(period_id: str) -> int:
    p = str(period_id or "").strip().upper()
    for suffix, mult in (("SEC", 1), ("MIN", 60), ("HRS", 3600), ("DAY", 86400)):
        if p.endswith(suffix):
            num = p[: -len(suffix)]
            try:
                return int(num) * mult
            except Exception:
                return 60
    return 60


def _default_chunk(period_seconds: int) -> timedelta:
    # Try to keep requests in a reasonable size window.
    if period_seconds <= 60:
        # 1m bars: cap at ~3 days
        return timedelta(days=3)
    if period_seconds <= 300:
        # 5m bars: cap at ~14 days
        return timedelta(days=14)
    if period_seconds <= 3600:
        # hourly: cap at ~180 days
        return timedelta(days=180)
    # daily+: cap at ~5 years
    return timedelta(days=365 * 5)


def _extract_venue_from_coinapi_symbol_id(symbol_id: str) -> str:
    sid = str(symbol_id or "")
    if "_" not in sid:
        return ""
    return sid.split("_", 1)[0].upper()


def _symbol_from_coinapi_symbol_id(symbol_id: str) -> str:
    parts = str(symbol_id or "").split("_")
    if len(parts) >= 4:
        base = parts[2].upper()
        quote = parts[3].upper()
        return f"{base}{quote}"
    return str(symbol_id or "").upper()


def _dedupe_preserve_order(items: Iterable[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for it in items:
        if not it:
            continue
        if it in seen:
            continue
        seen.add(it)
        out.append(it)
    return out


def _parse_csv(value: str) -> List[str]:
    return [v.strip() for v in str(value or "").split(",") if v.strip()]


def _insert_market_bars(conn: sqlite3.Connection, rows: Sequence[Tuple[Any, ...]]) -> Tuple[int, int]:
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


def _insert_market_trades(conn: sqlite3.Connection, rows: Sequence[Tuple[Any, ...]]) -> Tuple[int, int]:
    if not rows:
        return (0, 0)
    stmt = """
        INSERT OR IGNORE INTO market_trades(
            provider, venue, symbol_id, symbol, trade_id,
            side, size, price, ts_ms,
            ingested_at_ms,
            raw_json
        )
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    before = conn.total_changes
    conn.executemany(stmt, rows)
    inserted = conn.total_changes - before
    skipped = len(rows) - inserted
    return inserted, skipped


def _coinapi_discover_symbol_ids(
    client: Any,
    base: str,
    quote: str,
    exchange_allowlist: Optional[set[str]],
    max_symbols: int,
) -> List[str]:
    base_u = str(base or "").upper()
    quote_u = str(quote or "").upper()
    symbol_filter = f"*_{base_u}_{quote_u}"

    symbol_ids: List[str] = []
    try:
        quotes = client.get_quotes_current(symbol_filter) or []
        for q in quotes:
            if isinstance(q, dict):
                sid = str(q.get("symbol_id") or "")
                if sid:
                    symbol_ids.append(sid)
    except Exception:
        quotes = []

    # Fallback: heavy call, but more reliable if quote-filter returns nothing.
    if not symbol_ids:
        try:
            symbols = client.get_symbols() or []
            for s in symbols:
                if not isinstance(s, dict):
                    continue
                if str(s.get("asset_id_base") or "").upper() != base_u:
                    continue
                if str(s.get("asset_id_quote") or "").upper() != quote_u:
                    continue
                sid = str(s.get("symbol_id") or "")
                if sid:
                    symbol_ids.append(sid)
        except Exception:
            pass

    symbol_ids = _dedupe_preserve_order(symbol_ids)
    if exchange_allowlist:
        symbol_ids = [sid for sid in symbol_ids if _extract_venue_from_coinapi_symbol_id(sid) in exchange_allowlist]

    # Prefer SPOT markets first.
    symbol_ids.sort(key=lambda sid: (0 if "_SPOT_" in sid.upper() else 1, sid))
    return symbol_ids[: max(1, int(max_symbols or 1))]


def _coinapi_index_symbols(conn: sqlite3.Connection, client: Any, limit: int = 0) -> int:
    """Cache CoinAPI symbol registry into the DB (symbols table)."""
    from aureon.core import aureon_global_history_db as ghdb  # type: ignore

    symbols = client.get_symbols() or []
    if not isinstance(symbols, list):
        print("[coinapi] symbols endpoint returned non-list")
        return 0

    total = len(symbols)
    if limit and limit > 0:
        total = min(total, int(limit))

    inserted = 0
    for i, s in enumerate(symbols[:total], start=1):
        if not isinstance(s, dict):
            continue

        symbol_id = str(s.get("symbol_id") or "")
        if not symbol_id:
            continue

        venue = str(s.get("exchange_id") or "") or _extract_venue_from_coinapi_symbol_id(symbol_id)
        symbol_type = str(s.get("symbol_type") or "")
        base = str(s.get("asset_id_base") or "")
        quote = str(s.get("asset_id_quote") or "")
        canonical_symbol = f"{base}{quote}".upper() if base and quote else _symbol_from_coinapi_symbol_id(symbol_id)

        data_start_raw = (
            s.get("data_start")
            or s.get("data_trade_start")
            or s.get("data_quote_start")
            or s.get("data_orderbook_start")
        )
        data_end_raw = (
            s.get("data_end")
            or s.get("data_trade_end")
            or s.get("data_quote_end")
            or s.get("data_orderbook_end")
        )

        data_start_ms: Optional[int] = None
        if data_start_raw:
            try:
                data_start_ms = int(_parse_dt(str(data_start_raw)).timestamp() * 1000)
            except Exception:
                data_start_ms = None

        data_end_ms: Optional[int] = None
        if data_end_raw:
            try:
                data_end_ms = int(_parse_dt(str(data_end_raw)).timestamp() * 1000)
            except Exception:
                data_end_ms = None

        ghdb.upsert_symbol(
            conn,
            {
                "provider": "coinapi",
                "symbol_id": symbol_id,
                "venue": venue,
                "symbol": canonical_symbol,
                "symbol_type": symbol_type,
                "asset_id_base": base.upper(),
                "asset_id_quote": quote.upper(),
                "data_start_ms": data_start_ms,
                "data_end_ms": data_end_ms,
                "raw_json": _json_dumps_safe(s),
            },
        )
        inserted += 1
        if inserted % 5000 == 0:
            conn.commit()
            print(f"[coinapi] indexed {inserted}/{total} symbols...")

    conn.commit()
    print(f"[coinapi] indexed symbols: {inserted}")
    return inserted


def _coinapi_split_symbol_id(symbol_id: str) -> Tuple[str, str, str]:
    parts = str(symbol_id or "").split("_")
    venue = parts[0].upper() if len(parts) >= 1 and parts[0] else ""
    base = parts[2].upper() if len(parts) >= 4 and parts[2] else ""
    quote = parts[3].upper() if len(parts) >= 4 and parts[3] else ""
    return venue, base, quote


def _ingest_coinapi_symbol_id(
    conn: sqlite3.Connection,
    client: Any,
    start_dt: datetime,
    end_dt: datetime,
    symbol_id: str,
    venue: str,
    symbol: str,
    period_id_u: str,
    chunk: timedelta,
    include_trades: bool,
    no_resume: bool,
) -> None:
    # local import to keep the script standalone if core isn't installed
    from aureon.core import aureon_global_history_db as ghdb  # type: ignore

    wm_key = f"bars:coinapi:{symbol_id}:{period_id_u}"
    wm = None if no_resume else ghdb.get_watermark_ms(conn, wm_key)
    cur_start = start_dt
    if wm is not None:
        cur_start = max(cur_start, _dt_from_ms(int(wm) + 1))

    total_inserted = 0
    total_skipped = 0
    loops = 0

    while cur_start < end_dt:
        loops += 1
        cur_end = min(cur_start + chunk, end_dt)

        bars = client.get_ohlcv_history(
            symbol_id=symbol_id,
            period=period_id_u,
            time_start=_dt_to_iso_z(cur_start),
            time_end=_dt_to_iso_z(cur_end),
            limit=10000,
        )
        status = getattr(client, "last_status_code", None)
        if status != 200:
            err = str(getattr(client, "last_error_text", "") or "")
            if status == 429:
                time.sleep(2.0)
                continue
            print(f"[coinapi] HTTP {status} for {symbol_id}: {err[:200]}")
            break

        ingested_at_ms = int(time.time() * 1000)
        rows: List[Tuple[Any, ...]] = []
        max_end_ms: Optional[int] = None
        for b in bars or []:
            if not isinstance(b, dict):
                continue
            ts_start = str(b.get("time_period_start") or "")
            if not ts_start:
                continue
            try:
                ts_start_ms = int(_parse_dt(ts_start).timestamp() * 1000)
            except Exception:
                continue

            ts_end_ms: Optional[int] = None
            ts_end = str(b.get("time_period_end") or "")
            if ts_end:
                try:
                    ts_end_ms = int(_parse_dt(ts_end).timestamp() * 1000)
                except Exception:
                    ts_end_ms = None

            if ts_end_ms is not None:
                max_end_ms = ts_end_ms if max_end_ms is None else max(max_end_ms, ts_end_ms)
            else:
                max_end_ms = ts_start_ms if max_end_ms is None else max(max_end_ms, ts_start_ms)

            rows.append(
                (
                    "coinapi",
                    venue,
                    symbol_id,
                    symbol,
                    period_id_u,
                    ts_start_ms,
                    ts_end_ms,
                    float(b.get("price_open", 0) or 0),
                    float(b.get("price_high", 0) or 0),
                    float(b.get("price_low", 0) or 0),
                    float(b.get("price_close", 0) or 0),
                    float(b.get("volume_traded", 0) or 0),
                    int(b.get("trades_count", 0) or 0),
                    ingested_at_ms,
                    _json_dumps_safe(b),
                )
            )

        ins, skip = _insert_market_bars(conn, rows)
        total_inserted += ins
        total_skipped += skip

        # Advance start
        if max_end_ms is not None:
            ghdb.set_watermark_ms(conn, wm_key, int(max_end_ms))
            conn.commit()
            cur_start = _dt_from_ms(int(max_end_ms) + 1)
        else:
            # No data returned for this window; advance.
            ghdb.set_watermark_ms(conn, wm_key, int(cur_end.timestamp() * 1000))
            conn.commit()
            cur_start = cur_end

        # Gentle pacing on free plans.
        time.sleep(0.11)

        # Avoid infinite loops if time parsing fails.
        if loops > 200000:
            print(f"[coinapi] aborting {symbol_id}: too many loops")
            break

    print(f"[coinapi] bars {symbol_id} {period_id_u}: inserted={total_inserted} skipped={total_skipped}")

    if not include_trades:
        return

    trade_wm_key = f"trades:coinapi:{symbol_id}"
    trade_wm = None if no_resume else ghdb.get_watermark_ms(conn, trade_wm_key)
    trade_start = start_dt
    if trade_wm is not None:
        trade_start = max(trade_start, _dt_from_ms(int(trade_wm) + 1))

    # Trades are much heavier; use shorter windows.
    trade_chunk = timedelta(minutes=15)
    trades_inserted = 0
    trades_skipped = 0
    loops = 0

    while trade_start < end_dt:
        loops += 1
        trade_end = min(trade_start + trade_chunk, end_dt)
        trades = client.get_trades_history(
            symbol_id=symbol_id,
            time_start=_dt_to_iso_z(trade_start),
            time_end=_dt_to_iso_z(trade_end),
            limit=10000,
        )
        status = getattr(client, "last_status_code", None)
        if status != 200:
            err = str(getattr(client, "last_error_text", "") or "")
            if status == 429:
                time.sleep(2.0)
                continue
            print(f"[coinapi] HTTP {status} for trades {symbol_id}: {err[:200]}")
            break

        ingested_at_ms = int(time.time() * 1000)
        t_rows: List[Tuple[Any, ...]] = []
        max_ts_ms: Optional[int] = None
        for t in trades or []:
            if not isinstance(t, dict):
                continue
            trade_id = str(t.get("uuid") or t.get("trade_id") or t.get("id") or "")
            if not trade_id:
                continue

            ts_raw = str(t.get("time_exchange") or t.get("time_coinapi") or "")
            ts_ms: Optional[int] = None
            if ts_raw:
                try:
                    ts_ms = int(_parse_dt(ts_raw).timestamp() * 1000)
                except Exception:
                    ts_ms = None

            if ts_ms is not None:
                max_ts_ms = ts_ms if max_ts_ms is None else max(max_ts_ms, ts_ms)

            t_rows.append(
                (
                    "coinapi",
                    venue,
                    symbol_id,
                    symbol,
                    trade_id,
                    str(t.get("taker_side") or t.get("side") or "").upper(),
                    float(t.get("size", 0) or 0),
                    float(t.get("price", 0) or 0),
                    ts_ms,
                    ingested_at_ms,
                    _json_dumps_safe(t),
                )
            )

        ins, skip = _insert_market_trades(conn, t_rows)
        trades_inserted += ins
        trades_skipped += skip

        if max_ts_ms is not None:
            ghdb.set_watermark_ms(conn, trade_wm_key, int(max_ts_ms))
            conn.commit()
            trade_start = _dt_from_ms(int(max_ts_ms) + 1)
        else:
            ghdb.set_watermark_ms(conn, trade_wm_key, int(trade_end.timestamp() * 1000))
            conn.commit()
            trade_start = trade_end

        time.sleep(0.11)
        if loops > 200000:
            print(f"[coinapi] aborting trades {symbol_id}: too many loops")
            break

    print(f"[coinapi] trades {symbol_id}: inserted={trades_inserted} skipped={trades_skipped}")


def ingest_coinapi_all_symbols(
    conn: sqlite3.Connection,
    start_dt: datetime,
    end_dt: datetime,
    period_id: str,
    exchange_allowlist: Optional[set[str]],
    symbol_type_filter: str,
    base_assets: List[str],
    quote_assets: List[str],
    symbol_limit: int,
    include_trades: bool,
    no_resume: bool,
) -> None:
    """Ingest CoinAPI bars/trades for every symbol_id in the CoinAPI registry."""
    try:
        from aureon.exchanges.coinapi_anomaly_detector import CoinAPIClient  # type: ignore
    except Exception:
        from coinapi_anomaly_detector import CoinAPIClient  # type: ignore

    api_key = os.getenv("COINAPI_KEY", "") or os.getenv("COINAPI_API_KEY", "")
    if not api_key:
        print("[coinapi] COINAPI_KEY missing, skipping.")
        return

    client = CoinAPIClient(api_key)
    period_id_u = str(period_id or "1MIN").upper()
    period_seconds = _period_to_seconds(period_id_u)
    chunk = _default_chunk(period_seconds)

    # Ensure we have the registry locally.
    try:
        count_row = conn.execute(
            "SELECT COUNT(1) AS n FROM symbols WHERE provider = 'coinapi';"
        ).fetchone()
        n = int(count_row["n"]) if count_row and "n" in count_row.keys() else int(count_row[0] if count_row else 0)
    except Exception:
        n = 0

    if n <= 0:
        print("[coinapi] symbols table empty; indexing CoinAPI registry first (this is a big call).")
        _coinapi_index_symbols(conn, client, limit=0)

    rows = conn.execute(
        "SELECT symbol_id, venue, symbol, symbol_type, asset_id_base, asset_id_quote "
        "FROM symbols WHERE provider = 'coinapi';"
    ).fetchall()

    st_filter = str(symbol_type_filter or "").strip().upper()
    base_set = {b.strip().upper() for b in base_assets if b.strip()}
    quote_set = {q.strip().upper() for q in quote_assets if q.strip()}

    universe: List[Tuple[str, str, str]] = []
    for r in rows or []:
        sid = str(r["symbol_id"] or "")
        if not sid:
            continue
        venue = str(r["venue"] or "") or _extract_venue_from_coinapi_symbol_id(sid)
        symbol = str(r["symbol"] or "") or _symbol_from_coinapi_symbol_id(sid)
        sym_type = str(r["symbol_type"] or "").strip().upper()
        base = str(r["asset_id_base"] or "").strip().upper()
        quote = str(r["asset_id_quote"] or "").strip().upper()
        if not base or not quote:
            _, base2, quote2 = _coinapi_split_symbol_id(sid)
            base = base or base2
            quote = quote or quote2

        if exchange_allowlist and venue.upper() not in exchange_allowlist:
            continue
        if st_filter and sym_type and sym_type != st_filter:
            continue
        if st_filter and not sym_type:
            # If we asked for a type but the registry row doesn't have one, skip.
            continue
        if base_set and base not in base_set:
            continue
        if quote_set and quote not in quote_set:
            continue

        universe.append((sid, venue.upper(), symbol.upper()))

    # Stable order and optional limit.
    universe.sort(key=lambda t: (t[1], t[0]))
    if symbol_limit and symbol_limit > 0:
        universe = universe[: int(symbol_limit)]

    print(f"[coinapi] ingest universe size: {len(universe)}")
    for sid, venue, symbol in universe:
        _ingest_coinapi_symbol_id(
            conn=conn,
            client=client,
            start_dt=start_dt,
            end_dt=end_dt,
            symbol_id=sid,
            venue=venue,
            symbol=symbol,
            period_id_u=period_id_u,
            chunk=chunk,
            include_trades=include_trades,
            no_resume=no_resume,
        )


def ingest_coinapi(
    conn: sqlite3.Connection,
    start_dt: datetime,
    end_dt: datetime,
    pairs: List[str],
    period_id: str,
    exchange_allowlist: Optional[set[str]],
    max_symbols_per_pair: int,
    include_trades: bool,
    no_resume: bool,
) -> None:
    try:
        from aureon.exchanges.coinapi_anomaly_detector import CoinAPIClient  # type: ignore
    except Exception:
        from coinapi_anomaly_detector import CoinAPIClient  # type: ignore

    api_key = os.getenv("COINAPI_KEY", "") or os.getenv("COINAPI_API_KEY", "")
    if not api_key:
        print("[coinapi] COINAPI_KEY missing, skipping.")
        return

    client = CoinAPIClient(api_key)
    period_id_u = str(period_id or "1MIN").upper()
    period_seconds = _period_to_seconds(period_id_u)
    chunk = _default_chunk(period_seconds)

    for pair in pairs:
        if "/" not in pair:
            print(f"[coinapi] skipping invalid pair (expected BASE/QUOTE): {pair}")
            continue
        base, quote = pair.split("/", 1)
        base = base.strip().upper()
        quote = quote.strip().upper()
        if not base or not quote:
            continue

        symbol_ids = _coinapi_discover_symbol_ids(
            client=client,
            base=base,
            quote=quote,
            exchange_allowlist=exchange_allowlist,
            max_symbols=max_symbols_per_pair,
        )
        if not symbol_ids:
            print(f"[coinapi] no symbol_ids found for {base}/{quote}")
            continue

        print(f"[coinapi] {base}/{quote}: {len(symbol_ids)} symbol_ids")

        for symbol_id in symbol_ids:
            venue = _extract_venue_from_coinapi_symbol_id(symbol_id)
            symbol = _symbol_from_coinapi_symbol_id(symbol_id)
            _ingest_coinapi_symbol_id(
                conn=conn,
                client=client,
                start_dt=start_dt,
                end_dt=end_dt,
                symbol_id=symbol_id,
                venue=venue,
                symbol=symbol,
                period_id_u=period_id_u,
                chunk=chunk,
                include_trades=include_trades,
                no_resume=no_resume,
            )


def ingest_alpaca_stocks(
    conn: sqlite3.Connection,
    start_dt: datetime,
    end_dt: datetime,
    symbols: List[str],
    timeframe: str,
    feed: str,
    no_resume: bool,
) -> None:
    import requests

    api_key = os.getenv("ALPACA_API_KEY", "") or os.getenv("APCA_API_KEY_ID", "")
    api_secret = os.getenv("ALPACA_SECRET_KEY", "") or os.getenv("ALPACA_API_SECRET") or os.getenv("APCA_API_SECRET_KEY", "")
    if not api_key or not api_secret:
        print("[alpaca] ALPACA_API_KEY/ALPACA_SECRET_KEY missing, skipping.")
        return

    data_url = "https://data.alpaca.markets"
    headers = {"APCA-API-KEY-ID": api_key, "APCA-API-SECRET-KEY": api_secret}

    # local import to keep the script standalone if core isn't installed
    from aureon.core import aureon_global_history_db as ghdb  # type: ignore

    tf = str(timeframe or "1Min")
    # Normalize to the CoinAPI-ish "1MIN" style for consistent keys.
    period_id = tf.replace("Hour", "HRS").replace("Min", "MIN").replace("Day", "DAY").upper()
    period_seconds = _period_to_seconds(period_id)

    for sym in symbols:
        sym_u = str(sym or "").strip().upper()
        if not sym_u:
            continue

        wm_key = f"bars:alpaca:{sym_u}:{period_id}"
        wm = None if no_resume else ghdb.get_watermark_ms(conn, wm_key)
        cur_start = start_dt
        if wm is not None:
            cur_start = max(cur_start, _dt_from_ms(int(wm) + 1))

        inserted_total = 0
        skipped_total = 0
        page_token: Optional[str] = None

        while cur_start < end_dt:
            params: Dict[str, Any] = {
                "timeframe": tf,
                "start": _dt_to_iso_z(cur_start),
                "end": _dt_to_iso_z(end_dt),
                "limit": 10000,
                "adjustment": "raw",
                "feed": str(feed or "iex").lower(),
                "sort": "asc",
            }
            if page_token:
                params["page_token"] = page_token

            try:
                resp = requests.get(
                    f"{data_url}/v2/stocks/{sym_u}/bars",
                    headers=headers,
                    params=params,
                    timeout=15,
                )
            except Exception as exc:
                print(f"[alpaca] request error {sym_u}: {exc}")
                break

            if resp.status_code != 200:
                print(f"[alpaca] {sym_u} HTTP {resp.status_code}: {resp.text[:200]}")
                break

            payload = resp.json() or {}
            bars = payload.get("bars") or []
            page_token = payload.get("next_page_token") or None

            ingested_at_ms = int(time.time() * 1000)
            rows: List[Tuple[Any, ...]] = []
            max_ts_ms: Optional[int] = None
            for b in bars:
                if not isinstance(b, dict):
                    continue
                ts_raw = str(b.get("t") or "")
                if not ts_raw:
                    continue
                try:
                    ts_ms = int(_parse_dt(ts_raw).timestamp() * 1000)
                except Exception:
                    continue

                max_ts_ms = ts_ms if max_ts_ms is None else max(max_ts_ms, ts_ms)
                time_end_ms = ts_ms + int(period_seconds * 1000)

                rows.append(
                    (
                        "alpaca",
                        "alpaca",
                        sym_u,
                        sym_u,
                        period_id,
                        ts_ms,
                        time_end_ms,
                        float(b.get("o", 0) or 0),
                        float(b.get("h", 0) or 0),
                        float(b.get("l", 0) or 0),
                        float(b.get("c", 0) or 0),
                        float(b.get("v", 0) or 0),
                        int(b.get("n", 0) or 0),
                        ingested_at_ms,
                        _json_dumps_safe(b),
                    )
                )

            ins, skip = _insert_market_bars(conn, rows)
            inserted_total += ins
            skipped_total += skip

            if max_ts_ms is not None:
                ghdb.set_watermark_ms(conn, wm_key, int(max_ts_ms))
                conn.commit()
                cur_start = _dt_from_ms(int(max_ts_ms) + 1)

            # No more pages or no data: we're caught up to end_dt.
            if not page_token or not bars:
                break

            time.sleep(0.11)

        print(f"[alpaca] bars {sym_u} {period_id}: inserted={inserted_total} skipped={skipped_total}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="", help="Override SQLite path (default: state/aureon_global_history.sqlite)")
    parser.add_argument("--no-resume", action="store_true", help="Ignore stored watermarks and re-ingest from --start")

    parser.add_argument("--start", default="", help="ISO start datetime (default: now - --days)")
    parser.add_argument("--end", default="", help="ISO end datetime (default: now)")
    parser.add_argument("--days", type=int, default=7, help="If --start not set, use now - DAYS (default: 7)")

    parser.add_argument("--coinapi", action="store_true", help="Ingest CoinAPI crypto market history")
    parser.add_argument("--coinapi-index", action="store_true", help="Cache CoinAPI symbol registry into the DB")
    parser.add_argument("--coinapi-index-limit", type=int, default=0, help="Limit CoinAPI symbols indexed (0=all)")
    parser.add_argument("--coinapi-all-symbols", action="store_true", help="Ingest CoinAPI history for all symbol_ids in the registry")
    parser.add_argument("--coinapi-pairs", default="BTC/USD,ETH/USD", help="Comma pairs BASE/QUOTE")
    parser.add_argument("--coinapi-period", default="1MIN", help="CoinAPI period_id (e.g. 1MIN, 5MIN, 1HRS, 1DAY)")
    parser.add_argument("--coinapi-exchanges", default="", help="Comma allowlist of exchange_ids (e.g. BINANCE,COINBASE)")
    parser.add_argument("--coinapi-symbol-type", default="", help="Filter by symbol_type in all-symbols mode (blank=all)")
    parser.add_argument("--coinapi-base-assets", default="", help="CSV base-asset filter for all-symbols mode (e.g. BTC,ETH)")
    parser.add_argument("--coinapi-quote-assets", default="", help="CSV quote-asset filter for all-symbols mode (e.g. USD,USDT,USDC)")
    parser.add_argument("--coinapi-symbol-limit", type=int, default=0, help="Limit symbol_ids ingested in all-symbols mode (0=all)")
    parser.add_argument("--coinapi-max-symbols", type=int, default=6, help="Max symbol_ids per pair (pair mode)")
    parser.add_argument("--coinapi-trades", action="store_true", help="Also ingest CoinAPI trade ticks (heavy)")

    parser.add_argument("--alpaca", action="store_true", help="Ingest Alpaca stock market history")
    parser.add_argument("--alpaca-stocks", default="AAPL,MSFT,TSLA", help="Comma stock symbols")
    parser.add_argument("--alpaca-timeframe", default="1Min", help="Alpaca timeframe (e.g. 1Min, 5Min, 1Hour, 1Day)")
    parser.add_argument("--alpaca-feed", default="iex", help="Alpaca data feed (iex or sip)")

    args = parser.parse_args()

    now = datetime.now(tz=timezone.utc)
    end_dt = _parse_dt(args.end) if args.end else now
    if args.start:
        start_dt = _parse_dt(args.start)
    else:
        start_dt = end_dt - timedelta(days=max(1, int(args.days or 1)))

    if start_dt >= end_dt:
        print("start must be < end")
        return 2

    from aureon.core import aureon_global_history_db as ghdb  # type: ignore

    conn = ghdb.connect(args.db or None)
    try:
        allowlist = {s.strip().upper() for s in _parse_csv(args.coinapi_exchanges)} or None

        if args.coinapi_index:
            try:
                from aureon.exchanges.coinapi_anomaly_detector import CoinAPIClient  # type: ignore
            except Exception:
                from coinapi_anomaly_detector import CoinAPIClient  # type: ignore

            api_key = os.getenv("COINAPI_KEY", "") or os.getenv("COINAPI_API_KEY", "")
            if not api_key:
                print("[coinapi] COINAPI_KEY missing, cannot index.")
            else:
                client = CoinAPIClient(api_key)
                _coinapi_index_symbols(conn, client, limit=int(args.coinapi_index_limit or 0))

        if args.coinapi_all_symbols:
            ingest_coinapi_all_symbols(
                conn=conn,
                start_dt=start_dt,
                end_dt=end_dt,
                period_id=args.coinapi_period,
                exchange_allowlist=allowlist,
                symbol_type_filter=str(args.coinapi_symbol_type or ""),
                base_assets=_parse_csv(args.coinapi_base_assets),
                quote_assets=_parse_csv(args.coinapi_quote_assets),
                symbol_limit=int(args.coinapi_symbol_limit or 0),
                include_trades=bool(args.coinapi_trades),
                no_resume=bool(args.no_resume),
            )
        elif args.coinapi:
            pairs = _parse_csv(args.coinapi_pairs)
            ingest_coinapi(
                conn=conn,
                start_dt=start_dt,
                end_dt=end_dt,
                pairs=pairs,
                period_id=args.coinapi_period,
                exchange_allowlist=allowlist,
                max_symbols_per_pair=int(args.coinapi_max_symbols or 1),
                include_trades=bool(args.coinapi_trades),
                no_resume=bool(args.no_resume),
            )

        if args.alpaca:
            ingest_alpaca_stocks(
                conn=conn,
                start_dt=start_dt,
                end_dt=end_dt,
                symbols=_parse_csv(args.alpaca_stocks),
                timeframe=args.alpaca_timeframe,
                feed=args.alpaca_feed,
                no_resume=bool(args.no_resume),
            )
    finally:
        try:
            conn.close()
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
