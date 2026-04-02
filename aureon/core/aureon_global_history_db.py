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


SCHEMA_VERSION = 5


def connect(db_path: str | None = None, *, check_same_thread: bool = True) -> sqlite3.Connection:
    paths = resolve_paths(db_path)
    conn = sqlite3.connect(str(paths.db_path), check_same_thread=check_same_thread)
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

    # Macro economic indicators (FRED, World Bank, central bank rates, etc).
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS macro_indicators (
            provider TEXT NOT NULL,
            series_id TEXT NOT NULL,
            series_name TEXT,
            category TEXT,
            region TEXT,
            frequency TEXT,
            units TEXT,
            observation_date_ms INTEGER NOT NULL,
            value REAL,
            ingested_at_ms INTEGER,
            raw_json TEXT,
            PRIMARY KEY (provider, series_id, observation_date_ms)
        );
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_macro_series_time ON macro_indicators(series_id, observation_date_ms);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_macro_provider_time ON macro_indicators(provider, observation_date_ms);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_macro_category ON macro_indicators(category);")

    # Market sentiment snapshots (Fear & Greed, news sentiment, social, on-chain).
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sentiment (
            source TEXT NOT NULL,
            sentiment_id TEXT NOT NULL,
            sentiment_type TEXT,
            symbol TEXT,
            value REAL,
            label TEXT,
            ts_ms INTEGER NOT NULL,
            ingested_at_ms INTEGER,
            raw_json TEXT,
            PRIMARY KEY (source, sentiment_id)
        );
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sentiment_type_time ON sentiment(sentiment_type, ts_ms);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sentiment_symbol_time ON sentiment(symbol, ts_ms);")

    # On-chain metrics (whale movements, exchange flows, network stats).
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS onchain_metrics (
            provider TEXT NOT NULL,
            metric_id TEXT NOT NULL,
            metric_name TEXT,
            asset TEXT,
            value REAL,
            ts_ms INTEGER NOT NULL,
            ingested_at_ms INTEGER,
            raw_json TEXT,
            PRIMARY KEY (provider, metric_id)
        );
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_onchain_metric_time ON onchain_metrics(metric_name, ts_ms);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_onchain_asset_time ON onchain_metrics(asset, ts_ms);")

    # Geopolitical / economic calendar events (FOMC, NFP, earnings, elections, etc).
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS calendar_events (
            source TEXT NOT NULL,
            event_id TEXT NOT NULL,
            event_type TEXT,
            title TEXT,
            country TEXT,
            currency TEXT,
            impact TEXT,
            actual TEXT,
            forecast TEXT,
            previous TEXT,
            event_ts_ms INTEGER,
            ingested_at_ms INTEGER,
            raw_json TEXT,
            PRIMARY KEY (source, event_id)
        );
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_calendar_type_time ON calendar_events(event_type, event_ts_ms);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_calendar_country_time ON calendar_events(country, event_ts_ms);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_calendar_impact ON calendar_events(impact, event_ts_ms);")

    # Queen memories — crystallized experiences, lessons learned, wisdom truths.
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS queen_memories (
            memory_id TEXT PRIMARY KEY,
            memory_type TEXT NOT NULL,
            category TEXT,
            title TEXT,
            description TEXT,
            symbol TEXT,
            outcome TEXT,
            outcome_value REAL,
            importance REAL,
            confidence REAL,
            lesson TEXT,
            ts_ms INTEGER,
            ingested_at_ms INTEGER,
            raw_json TEXT
        );
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_qmem_type_time ON queen_memories(memory_type, ts_ms);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_qmem_symbol ON queen_memories(symbol, ts_ms);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_qmem_category ON queen_memories(category, ts_ms);")

    # Queen insights — deep intelligence, market awareness, neural predictions.
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS queen_insights (
            insight_id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            insight_type TEXT,
            symbol TEXT,
            title TEXT,
            conclusion TEXT,
            confidence REAL,
            severity REAL,
            ts_ms INTEGER,
            ingested_at_ms INTEGER,
            raw_json TEXT
        );
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_qins_source_time ON queen_insights(source, ts_ms);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_qins_type ON queen_insights(insight_type, ts_ms);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_qins_symbol ON queen_insights(symbol, ts_ms);")

    # Queen thoughts — continuous thought stream from thought bus.
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS queen_thoughts (
            thought_id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            topic TEXT,
            symbol TEXT,
            thought_text TEXT,
            confidence REAL,
            ts_ms INTEGER,
            ingested_at_ms INTEGER,
            raw_json TEXT
        );
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_qthought_source_time ON queen_thoughts(source, ts_ms);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_qthought_topic ON queen_thoughts(topic, ts_ms);")

    # Queen trading knowledge — concepts, strategies, tactics, lessons.
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS queen_knowledge (
            knowledge_id TEXT PRIMARY KEY,
            knowledge_type TEXT NOT NULL,
            topic TEXT,
            summary TEXT,
            source TEXT,
            confidence REAL,
            success_rate REAL,
            times_applied INTEGER,
            ts_ms INTEGER,
            ingested_at_ms INTEGER,
            raw_json TEXT
        );
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_qknow_type ON queen_knowledge(knowledge_type, ts_ms);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_qknow_topic ON queen_knowledge(topic);")

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


def insert_macro_indicator(conn: sqlite3.Connection, ind: Dict[str, Any]) -> bool:
    """Insert a macro economic indicator observation."""
    ingested_at_ms = ind.get("ingested_at_ms")
    if ingested_at_ms is None:
        ingested_at_ms = int(time.time() * 1000)

    cur = conn.execute(
        """
        INSERT OR IGNORE INTO macro_indicators(
            provider, series_id, series_name, category, region, frequency, units,
            observation_date_ms, value, ingested_at_ms, raw_json
        )
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ind.get("provider"),
            ind.get("series_id"),
            ind.get("series_name"),
            ind.get("category"),
            ind.get("region"),
            ind.get("frequency"),
            ind.get("units"),
            ind.get("observation_date_ms"),
            ind.get("value"),
            ingested_at_ms,
            ind.get("raw_json"),
        ),
    )
    return bool(cur.rowcount and cur.rowcount > 0)


def insert_sentiment(conn: sqlite3.Connection, sent: Dict[str, Any]) -> bool:
    """Insert a sentiment snapshot."""
    ingested_at_ms = sent.get("ingested_at_ms")
    if ingested_at_ms is None:
        ingested_at_ms = int(time.time() * 1000)

    cur = conn.execute(
        """
        INSERT OR IGNORE INTO sentiment(
            source, sentiment_id, sentiment_type, symbol, value, label, ts_ms,
            ingested_at_ms, raw_json
        )
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            sent.get("source"),
            sent.get("sentiment_id"),
            sent.get("sentiment_type"),
            sent.get("symbol"),
            sent.get("value"),
            sent.get("label"),
            sent.get("ts_ms"),
            ingested_at_ms,
            sent.get("raw_json"),
        ),
    )
    return bool(cur.rowcount and cur.rowcount > 0)


def insert_onchain_metric(conn: sqlite3.Connection, metric: Dict[str, Any]) -> bool:
    """Insert an on-chain metric observation."""
    ingested_at_ms = metric.get("ingested_at_ms")
    if ingested_at_ms is None:
        ingested_at_ms = int(time.time() * 1000)

    cur = conn.execute(
        """
        INSERT OR IGNORE INTO onchain_metrics(
            provider, metric_id, metric_name, asset, value, ts_ms,
            ingested_at_ms, raw_json
        )
        VALUES(?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            metric.get("provider"),
            metric.get("metric_id"),
            metric.get("metric_name"),
            metric.get("asset"),
            metric.get("value"),
            metric.get("ts_ms"),
            ingested_at_ms,
            metric.get("raw_json"),
        ),
    )
    return bool(cur.rowcount and cur.rowcount > 0)


def insert_calendar_event(conn: sqlite3.Connection, evt: Dict[str, Any]) -> bool:
    """Insert an economic calendar / geopolitical event."""
    ingested_at_ms = evt.get("ingested_at_ms")
    if ingested_at_ms is None:
        ingested_at_ms = int(time.time() * 1000)

    cur = conn.execute(
        """
        INSERT OR IGNORE INTO calendar_events(
            source, event_id, event_type, title, country, currency, impact,
            actual, forecast, previous, event_ts_ms, ingested_at_ms, raw_json
        )
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            evt.get("source"),
            evt.get("event_id"),
            evt.get("event_type"),
            evt.get("title"),
            evt.get("country"),
            evt.get("currency"),
            evt.get("impact"),
            evt.get("actual"),
            evt.get("forecast"),
            evt.get("previous"),
            evt.get("event_ts_ms"),
            ingested_at_ms,
            evt.get("raw_json"),
        ),
    )
    return bool(cur.rowcount and cur.rowcount > 0)


def insert_queen_memory(conn: sqlite3.Connection, mem: Dict[str, Any]) -> bool:
    """Insert a queen memory (experience, wisdom, lesson)."""
    ingested_at_ms = mem.get("ingested_at_ms")
    if ingested_at_ms is None:
        ingested_at_ms = int(time.time() * 1000)

    cur = conn.execute(
        """
        INSERT OR IGNORE INTO queen_memories(
            memory_id, memory_type, category, title, description, symbol,
            outcome, outcome_value, importance, confidence, lesson, ts_ms,
            ingested_at_ms, raw_json
        )
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            mem.get("memory_id"),
            mem.get("memory_type"),
            mem.get("category"),
            mem.get("title"),
            mem.get("description"),
            mem.get("symbol"),
            mem.get("outcome"),
            mem.get("outcome_value"),
            mem.get("importance"),
            mem.get("confidence"),
            mem.get("lesson"),
            mem.get("ts_ms"),
            ingested_at_ms,
            mem.get("raw_json"),
        ),
    )
    return bool(cur.rowcount and cur.rowcount > 0)


def insert_queen_insight(conn: sqlite3.Connection, ins: Dict[str, Any]) -> bool:
    """Insert a queen insight (deep intelligence, market awareness, prediction)."""
    ingested_at_ms = ins.get("ingested_at_ms")
    if ingested_at_ms is None:
        ingested_at_ms = int(time.time() * 1000)

    cur = conn.execute(
        """
        INSERT OR IGNORE INTO queen_insights(
            insight_id, source, insight_type, symbol, title, conclusion,
            confidence, severity, ts_ms, ingested_at_ms, raw_json
        )
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ins.get("insight_id"),
            ins.get("source"),
            ins.get("insight_type"),
            ins.get("symbol"),
            ins.get("title"),
            ins.get("conclusion"),
            ins.get("confidence"),
            ins.get("severity"),
            ins.get("ts_ms"),
            ingested_at_ms,
            ins.get("raw_json"),
        ),
    )
    return bool(cur.rowcount and cur.rowcount > 0)


def insert_queen_thought(conn: sqlite3.Connection, thought: Dict[str, Any]) -> bool:
    """Insert a queen thought from the thought bus."""
    ingested_at_ms = thought.get("ingested_at_ms")
    if ingested_at_ms is None:
        ingested_at_ms = int(time.time() * 1000)

    cur = conn.execute(
        """
        INSERT OR IGNORE INTO queen_thoughts(
            thought_id, source, topic, symbol, thought_text, confidence,
            ts_ms, ingested_at_ms, raw_json
        )
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            thought.get("thought_id"),
            thought.get("source"),
            thought.get("topic"),
            thought.get("symbol"),
            thought.get("thought_text"),
            thought.get("confidence"),
            thought.get("ts_ms"),
            ingested_at_ms,
            thought.get("raw_json"),
        ),
    )
    return bool(cur.rowcount and cur.rowcount > 0)


def insert_queen_knowledge(conn: sqlite3.Connection, know: Dict[str, Any]) -> bool:
    """Insert a queen knowledge entry (concept, strategy, tactic, lesson)."""
    ingested_at_ms = know.get("ingested_at_ms")
    if ingested_at_ms is None:
        ingested_at_ms = int(time.time() * 1000)

    cur = conn.execute(
        """
        INSERT OR IGNORE INTO queen_knowledge(
            knowledge_id, knowledge_type, topic, summary, source,
            confidence, success_rate, times_applied, ts_ms,
            ingested_at_ms, raw_json
        )
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            know.get("knowledge_id"),
            know.get("knowledge_type"),
            know.get("topic"),
            know.get("summary"),
            know.get("source"),
            know.get("confidence"),
            know.get("success_rate"),
            know.get("times_applied"),
            know.get("ts_ms"),
            ingested_at_ms,
            know.get("raw_json"),
        ),
    )
    return bool(cur.rowcount and cur.rowcount > 0)
