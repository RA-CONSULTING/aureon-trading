#!/usr/bin/env python3
"""
Single-file global history database for Aureon.

This is intentionally SQLite (one file) rather than a single giant JSON blob:
- can grow large without loading into RAM
- supports indexes/queries for "memory" lookups
- safe to append incrementally

The DB is meant to store *your* account history (via API keys) and optionally
market history you are licensed to ingest.
"""

from __future__ import annotations

import os
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class GlobalHistoryPaths:
    repo_root: Path
    state_dir: Path
    db_path: Path


def resolve_paths(db_path: str | None = None) -> GlobalHistoryPaths:
    repo_root = Path(__file__).resolve().parents[2]
    state_dir = repo_root / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    configured = db_path or os.getenv("AUREON_GLOBAL_HISTORY_DB", "") or ""
    path = Path(configured) if configured else (state_dir / "aureon_global_history.sqlite")
    if not path.is_absolute():
        path = (repo_root / path).resolve()
    return GlobalHistoryPaths(repo_root=repo_root, state_dir=state_dir, db_path=path)


SCHEMA_VERSION = 3


def connect(db_path: str | None = None) -> sqlite3.Connection:
    paths = resolve_paths(db_path)
    conn = sqlite3.connect(str(paths.db_path))
    conn.row_factory = sqlite3.Row

    # Keep this resilient for long-running ingestion jobs.
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA temp_store=MEMORY;")
    conn.execute("PRAGMA foreign_keys=ON;")

    _ensure_schema(conn)
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS account_trades (
            venue TEXT NOT NULL,
            trade_id TEXT NOT NULL,
            symbol TEXT,
            side TEXT,
            qty REAL,
            price REAL,
            cost REAL,
            fee REAL,
            fee_asset TEXT,
            ts_ms INTEGER,
            ingested_at_ms INTEGER,
            raw_json TEXT,
            PRIMARY KEY (venue, trade_id)
        );
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_account_trades_symbol_time ON account_trades(symbol, ts_ms);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_account_trades_venue_time ON account_trades(venue, ts_ms);")

    # Public market history (bars). Provider is the datasource (coinapi/alpaca/...),
    # venue is the exchange/market (e.g. BINANCE for CoinAPI symbol_ids).
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS market_bars (
            provider TEXT NOT NULL,
            venue TEXT,
            symbol_id TEXT NOT NULL,
            symbol TEXT,
            period_id TEXT NOT NULL,
            time_start_ms INTEGER NOT NULL,
            time_end_ms INTEGER,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL,
            trades_count INTEGER,
            ingested_at_ms INTEGER,
            raw_json TEXT,
            PRIMARY KEY (provider, symbol_id, period_id, time_start_ms)
        );
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_market_bars_symbol_time ON market_bars(symbol, time_start_ms);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_market_bars_provider_time ON market_bars(provider, time_start_ms);")

    # Public market history (tick trades). This can get huge; ingest is optional.
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS market_trades (
            provider TEXT NOT NULL,
            venue TEXT,
            symbol_id TEXT NOT NULL,
            symbol TEXT,
            trade_id TEXT NOT NULL,
            side TEXT,
            size REAL,
            price REAL,
            ts_ms INTEGER,
            ingested_at_ms INTEGER,
            raw_json TEXT,
            PRIMARY KEY (provider, symbol_id, trade_id)
        );
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_market_trades_symbol_time ON market_trades(symbol, ts_ms);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_market_trades_provider_time ON market_trades(provider, ts_ms);")

    # Symbol metadata registry for providers (e.g. CoinAPI symbol_id -> base/quote).
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS symbols (
            provider TEXT NOT NULL,
            symbol_id TEXT NOT NULL,
            venue TEXT,
            symbol TEXT,
            symbol_type TEXT,
            asset_id_base TEXT,
            asset_id_quote TEXT,
            data_start_ms INTEGER,
            data_end_ms INTEGER,
            ingested_at_ms INTEGER,
            raw_json TEXT,
            PRIMARY KEY (provider, symbol_id)
        );
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_symbols_symbol ON symbols(symbol);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_symbols_provider_venue ON symbols(provider, venue);")

    # Future + scheduled events (earnings, macro releases, corporate actions, etc).
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            source TEXT NOT NULL,
            event_id TEXT NOT NULL,
            event_type TEXT,
            symbol TEXT,
            venue TEXT,
            event_ts_ms INTEGER,
            ingested_at_ms INTEGER,
            raw_json TEXT,
            PRIMARY KEY (source, event_id)
        );
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_symbol_time ON events(symbol, event_ts_ms);")

    # Forecasts / "future claims" (time-travelable: what was predicted, when, for when).
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS forecasts (
            model TEXT NOT NULL,
            forecast_id TEXT NOT NULL,
            symbol TEXT,
            venue TEXT,
            as_of_ts_ms INTEGER,
            target_ts_ms INTEGER,
            ingested_at_ms INTEGER,
            raw_json TEXT,
            PRIMARY KEY (model, forecast_id)
        );
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_forecasts_symbol_asof ON forecasts(symbol, as_of_ts_ms);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_forecasts_symbol_target ON forecasts(symbol, target_ts_ms);")

    # Backfill/upgrade older DBs that were created before we added ingested_at_ms columns.
    _ensure_column(conn, "account_trades", "ingested_at_ms", "INTEGER")
    _ensure_column(conn, "market_bars", "ingested_at_ms", "INTEGER")
    _ensure_column(conn, "market_trades", "ingested_at_ms", "INTEGER")

    existing = _get_meta_int(conn, "schema_version")
    if existing is None or existing < SCHEMA_VERSION:
        _set_meta(conn, "schema_version", str(SCHEMA_VERSION))
    conn.commit()


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, decl: str) -> None:
    try:
        cols = {str(r[1]) for r in conn.execute(f"PRAGMA table_info({table});").fetchall()}
    except Exception:
        cols = set()
    if column in cols:
        return
    try:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {decl};")
    except Exception:
        # If the table doesn't exist yet or alter fails, schema will be recreated on next run.
        pass

def _get_meta_int(conn: sqlite3.Connection, key: str) -> Optional[int]:
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    if not row:
        return None
    try:
        return int(str(row["value"]))
    except Exception:
        return None


def _set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO meta(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )


def get_meta_int(conn: sqlite3.Connection, key: str) -> Optional[int]:
    """Public meta getter for integer values."""
    return _get_meta_int(conn, key)


def set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    """Public meta setter (does not commit)."""
    _set_meta(conn, key, value)


def get_watermark_ms(conn: sqlite3.Connection, name: str) -> Optional[int]:
    """Retrieve a stored watermark in milliseconds."""
    return _get_meta_int(conn, f"wm:{name}")


def set_watermark_ms(conn: sqlite3.Connection, name: str, ts_ms: int) -> None:
    """Set a watermark in milliseconds (does not commit)."""
    _set_meta(conn, f"wm:{name}", str(int(ts_ms)))


def get_last_trade_ts_ms(conn: sqlite3.Connection, venue: str) -> Optional[int]:
    row = conn.execute(
        "SELECT MAX(ts_ms) AS ts_ms FROM account_trades WHERE venue = ?",
        (venue,),
    ).fetchone()
    if not row:
        return None
    ts = row["ts_ms"]
    return int(ts) if ts is not None else None


def insert_account_trade(conn: sqlite3.Connection, trade: Dict[str, Any]) -> bool:
    """
    Insert a normalized account trade dict.

    Returns True if inserted, False if ignored (duplicate).
    """
    ingested_at_ms = trade.get("ingested_at_ms")
    if ingested_at_ms is None:
        ingested_at_ms = int(time.time() * 1000)

    cur = conn.execute(
        """
        INSERT OR IGNORE INTO account_trades(
            venue, trade_id, symbol, side, qty, price, cost, fee, fee_asset, ts_ms, ingested_at_ms, raw_json
        )
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            trade.get("venue"),
            trade.get("trade_id"),
            trade.get("symbol"),
            trade.get("side"),
            trade.get("qty"),
            trade.get("price"),
            trade.get("cost"),
            trade.get("fee"),
            trade.get("fee_asset"),
            trade.get("ts_ms"),
            ingested_at_ms,
            trade.get("raw_json"),
        ),
    )
    return bool(cur.rowcount and cur.rowcount > 0)


def insert_market_bar(conn: sqlite3.Connection, bar: Dict[str, Any]) -> bool:
    """
    Insert a normalized market OHLCV bar dict.

    Returns True if inserted, False if ignored (duplicate).
    """
    ingested_at_ms = bar.get("ingested_at_ms")
    if ingested_at_ms is None:
        ingested_at_ms = int(time.time() * 1000)

    cur = conn.execute(
        """
        INSERT OR IGNORE INTO market_bars(
            provider, venue, symbol_id, symbol, period_id,
            time_start_ms, time_end_ms,
            open, high, low, close, volume, trades_count,
            ingested_at_ms,
            raw_json
        )
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            bar.get("provider"),
            bar.get("venue"),
            bar.get("symbol_id"),
            bar.get("symbol"),
            bar.get("period_id"),
            bar.get("time_start_ms"),
            bar.get("time_end_ms"),
            bar.get("open"),
            bar.get("high"),
            bar.get("low"),
            bar.get("close"),
            bar.get("volume"),
            bar.get("trades_count"),
            ingested_at_ms,
            bar.get("raw_json"),
        ),
    )
    return bool(cur.rowcount and cur.rowcount > 0)


def insert_market_trade(conn: sqlite3.Connection, trade: Dict[str, Any]) -> bool:
    """
    Insert a normalized market tick trade dict.

    Returns True if inserted, False if ignored (duplicate).
    """
    ingested_at_ms = trade.get("ingested_at_ms")
    if ingested_at_ms is None:
        ingested_at_ms = int(time.time() * 1000)

    cur = conn.execute(
        """
        INSERT OR IGNORE INTO market_trades(
            provider, venue, symbol_id, symbol, trade_id,
            side, size, price, ts_ms,
            ingested_at_ms,
            raw_json
        )
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            trade.get("provider"),
            trade.get("venue"),
            trade.get("symbol_id"),
            trade.get("symbol"),
            trade.get("trade_id"),
            trade.get("side"),
            trade.get("size"),
            trade.get("price"),
            trade.get("ts_ms"),
            ingested_at_ms,
            trade.get("raw_json"),
        ),
    )
    return bool(cur.rowcount and cur.rowcount > 0)


def upsert_symbol(conn: sqlite3.Connection, sym: Dict[str, Any]) -> None:
    """Upsert provider symbol metadata into the symbols registry."""
    ingested_at_ms = sym.get("ingested_at_ms")
    if ingested_at_ms is None:
        ingested_at_ms = int(time.time() * 1000)

    conn.execute(
        """
        INSERT INTO symbols(
            provider, symbol_id, venue, symbol, symbol_type,
            asset_id_base, asset_id_quote,
            data_start_ms, data_end_ms,
            ingested_at_ms, raw_json
        )
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(provider, symbol_id) DO UPDATE SET
            venue=excluded.venue,
            symbol=excluded.symbol,
            symbol_type=excluded.symbol_type,
            asset_id_base=excluded.asset_id_base,
            asset_id_quote=excluded.asset_id_quote,
            data_start_ms=excluded.data_start_ms,
            data_end_ms=excluded.data_end_ms,
            ingested_at_ms=excluded.ingested_at_ms,
            raw_json=excluded.raw_json
        """,
        (
            sym.get("provider"),
            sym.get("symbol_id"),
            sym.get("venue"),
            sym.get("symbol"),
            sym.get("symbol_type"),
            sym.get("asset_id_base"),
            sym.get("asset_id_quote"),
            sym.get("data_start_ms"),
            sym.get("data_end_ms"),
            ingested_at_ms,
            sym.get("raw_json"),
        ),
    )


def insert_event(conn: sqlite3.Connection, event: Dict[str, Any]) -> bool:
    """Insert a future/past event (scheduled or observed)."""
    ingested_at_ms = event.get("ingested_at_ms")
    if ingested_at_ms is None:
        ingested_at_ms = int(time.time() * 1000)

    cur = conn.execute(
        """
        INSERT OR IGNORE INTO events(
            source, event_id, event_type, symbol, venue, event_ts_ms, ingested_at_ms, raw_json
        )
        VALUES(?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event.get("source"),
            event.get("event_id"),
            event.get("event_type"),
            event.get("symbol"),
            event.get("venue"),
            event.get("event_ts_ms"),
            ingested_at_ms,
            event.get("raw_json"),
        ),
    )
    return bool(cur.rowcount and cur.rowcount > 0)


def insert_forecast(conn: sqlite3.Connection, forecast: Dict[str, Any]) -> bool:
    """Insert a forecast (a future-claim) with bitemporal timestamps."""
    ingested_at_ms = forecast.get("ingested_at_ms")
    if ingested_at_ms is None:
        ingested_at_ms = int(time.time() * 1000)

    cur = conn.execute(
        """
        INSERT OR IGNORE INTO forecasts(
            model, forecast_id, symbol, venue, as_of_ts_ms, target_ts_ms, ingested_at_ms, raw_json
        )
        VALUES(?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            forecast.get("model"),
            forecast.get("forecast_id"),
            forecast.get("symbol"),
            forecast.get("venue"),
            forecast.get("as_of_ts_ms"),
            forecast.get("target_ts_ms"),
            ingested_at_ms,
            forecast.get("raw_json"),
        ),
    )
    return bool(cur.rowcount and cur.rowcount > 0)
