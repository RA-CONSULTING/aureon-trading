"""Aureon planetary financial data ocean registry and governor.

The data ocean is a low-priority evidence layer. It names every repo-backed
financial data source, proves what is configured and usable, and tells the
separate supervisor what to refresh next without touching live order logic.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Sequence


SCHEMA_VERSION = "aureon-data-ocean-status-v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = Path("state/aureon_data_ocean_status.json")
PUBLIC_PATH = Path("frontend/public/aureon_data_ocean_status.json")
RUNTIME_STATUS_PATH = Path("state/unified_runtime_status.json")
STREAM_CACHE_PATH = Path("ws_cache/ws_prices.json")
EXCHANGE_CHECKLIST_PATH = Path("docs/audits/aureon_exchange_monitoring_checklist.json")
HISTORY_DB_PATH = Path("state/aureon_global_history.sqlite")
INGEST_ATTEMPTS_PATH = Path("state/aureon_data_ocean_ingest_attempts.json")


@dataclass(frozen=True)
class DataOceanSource:
    source_id: str
    title: str
    category: str
    asset_classes: tuple[str, ...]
    kind: str
    evidence_table: str = ""
    evidence_provider: str = ""
    evidence_source: str = ""
    live_exchange: str = ""
    credential_env: tuple[str, ...] = ()
    optional: bool = False
    cadence_sec: int = 300
    priority: int = 50
    max_calls_per_hour: int = 60
    command: tuple[str, ...] = ()
    next_action: str = ""


SOURCE_REGISTRY: tuple[DataOceanSource, ...] = (
    DataOceanSource(
        "binance_live",
        "Binance live crypto universe",
        "live_exchange",
        ("crypto", "spot", "quotes"),
        "live_exchange",
        live_exchange="binance",
        credential_env=("BINANCE_API_KEY", "BINANCE_API_SECRET"),
        cadence_sec=5,
        priority=95,
        max_calls_per_hour=720,
        command=("python", "-m", "aureon.data_feeds.ws_market_data_feeder", "--binance"),
        next_action="Keep Binance live cache fresh and feed high-volume crypto candidates.",
    ),
    DataOceanSource(
        "kraken_live",
        "Kraken spot and margin live crypto",
        "live_exchange",
        ("crypto", "spot", "margin", "quotes", "balances"),
        "live_exchange",
        live_exchange="kraken",
        credential_env=("KRAKEN_API_KEY", "KRAKEN_API_SECRET"),
        cadence_sec=10,
        priority=94,
        max_calls_per_hour=360,
        command=("python", "-m", "aureon.data_feeds.ws_market_data_feeder", "--kraken"),
        next_action="Activate Kraken live cache, fee context, collateral context, and order-book probes.",
    ),
    DataOceanSource(
        "alpaca_live",
        "Alpaca equities, ETFs, and crypto snapshots",
        "live_exchange",
        ("stocks", "etfs", "crypto", "quotes"),
        "live_exchange",
        live_exchange="alpaca",
        credential_env=("ALPACA_API_KEY", "ALPACA_API_SECRET"),
        cadence_sec=15,
        priority=88,
        max_calls_per_hour=240,
        command=("python", "-m", "aureon.data_feeds.ws_market_data_feeder", "--alpaca"),
        next_action="Enable fresh stock/ETF snapshots and market-hours state.",
    ),
    DataOceanSource(
        "capital_live",
        "Capital.com CFD, FX, index, and equity snapshots",
        "live_exchange",
        ("cfds", "forex", "indices", "stocks", "positions"),
        "live_exchange",
        live_exchange="capital",
        credential_env=("CAPITAL_API_KEY", "CAPITAL_IDENTIFIER", "CAPITAL_PASSWORD"),
        cadence_sec=20,
        priority=87,
        max_calls_per_hour=180,
        command=("python", "-m", "aureon.data_feeds.ws_market_data_feeder", "--capital"),
        next_action="Enable fresh Capital market snapshots and profitable-position close telemetry.",
    ),
    DataOceanSource(
        "yfinance_history",
        "Yahoo Finance broad historical OHLCV",
        "history",
        ("stocks", "etfs", "indices", "forex", "commodities", "crypto"),
        "table_provider",
        evidence_table="market_bars",
        evidence_provider="yfinance",
        cadence_sec=86400,
        priority=70,
        max_calls_per_hour=30,
        command=("python", "scripts/python/ingest_yfinance.py", "--all", "--days", "1825"),
        next_action="Backfill broad daily history for world indices, equities, ETFs, FX, commodities, and crypto.",
    ),
    DataOceanSource(
        "coinapi_history",
        "CoinAPI crypto market history",
        "history",
        ("crypto", "bars", "trades", "symbols"),
        "table_provider",
        evidence_table="market_bars",
        evidence_provider="coinapi",
        credential_env=("COINAPI_KEY", "COINAPI_API_KEY"),
        cadence_sec=21600,
        priority=78,
        max_calls_per_hour=100,
        command=("python", "scripts/python/ingest_market_history.py", "--coinapi"),
        next_action="Use licensed CoinAPI capacity for wide daily and recent minute crypto waveforms.",
    ),
    DataOceanSource(
        "coinbase_history",
        "Coinbase public crypto history",
        "history",
        ("crypto", "bars"),
        "table_provider",
        evidence_table="market_bars",
        evidence_provider="coinbase",
        cadence_sec=21600,
        priority=62,
        max_calls_per_hour=40,
        command=("python", "scripts/python/ingest_existing_feeds.py", "--feeds", "coinbase"),
        next_action="Use Coinbase public candles as crypto cross-check history.",
    ),
    DataOceanSource(
        "coingecko_snapshot",
        "CoinGecko crypto reference snapshots",
        "context",
        ("crypto", "reference_prices"),
        "table_provider",
        evidence_table="market_bars",
        evidence_provider="coingecko",
        cadence_sec=600,
        priority=64,
        max_calls_per_hour=60,
        command=("python", "scripts/python/ingest_existing_feeds.py", "--feeds", "coingecko"),
        next_action="Keep CoinGecko reference prices as non-execution cross-checks.",
    ),
    DataOceanSource(
        "fred_macro",
        "FRED macro indicators",
        "macro",
        ("rates", "inflation", "growth", "employment", "macro"),
        "table_provider",
        evidence_table="macro_indicators",
        evidence_provider="fred",
        credential_env=("FRED_API_KEY",),
        cadence_sec=86400,
        priority=58,
        max_calls_per_hour=120,
        command=("python", "scripts/python/ingest_fred.py", "--category", "all"),
        next_action="Configure FRED_API_KEY and refresh rates, CPI, GDP, and employment context.",
    ),
    DataOceanSource(
        "fmp_calendar",
        "FMP economic, earnings, IPO, and dividend calendar",
        "events",
        ("calendar", "earnings", "macro_events", "corporate_actions"),
        "table_source",
        evidence_table="calendar_events",
        evidence_source="fmp",
        credential_env=("FMP_API_KEY",),
        cadence_sec=21600,
        priority=56,
        max_calls_per_hour=60,
        command=("python", "scripts/python/ingest_economic_calendar.py", "--sources", "all"),
        next_action="Configure FMP_API_KEY for economic and corporate calendar coverage.",
    ),
    DataOceanSource(
        "world_news",
        "World News market and geopolitical sentiment",
        "sentiment",
        ("news", "sentiment", "geopolitical"),
        "table_source",
        evidence_table="sentiment",
        evidence_source="news_feed",
        credential_env=("WORLD_NEWS_API_KEY",),
        cadence_sec=1800,
        priority=55,
        max_calls_per_hour=30,
        command=("python", "scripts/python/ingest_existing_feeds.py", "--feeds", "news"),
        next_action="Configure WORLD_NEWS_API_KEY for fresh news sentiment and geopolitical context.",
    ),
    DataOceanSource(
        "glassnode_onchain",
        "Glassnode on-chain crypto metrics",
        "onchain",
        ("crypto", "onchain"),
        "table_provider",
        evidence_table="onchain_metrics",
        evidence_provider="glassnode",
        credential_env=("GLASSNODE_API_KEY",),
        cadence_sec=3600,
        priority=50,
        max_calls_per_hour=30,
        command=("python", "scripts/python/ingest_existing_feeds.py", "--feeds", "glassnode"),
        next_action="Configure GLASSNODE_API_KEY for on-chain confirmation signals.",
    ),
    DataOceanSource(
        "macro_snapshot",
        "Global financial feed macro snapshot",
        "context",
        ("macro", "risk_regime", "commodities", "forex"),
        "table_source",
        evidence_table="sentiment",
        evidence_source="global_financial_feed",
        cadence_sec=1800,
        priority=52,
        max_calls_per_hour=20,
        command=("python", "scripts/python/ingest_existing_feeds.py", "--feeds", "macro,macro_intel"),
        next_action="Refresh macro snapshot for risk regime, DXY, VIX, yields, oil, and gold context.",
    ),
    DataOceanSource(
        "account_trades",
        "Private account trade history",
        "account_memory",
        ("account_trades", "positions", "fills"),
        "table",
        evidence_table="account_trades",
        credential_env=(
            "KRAKEN_API_KEY",
            "KRAKEN_API_SECRET",
            "BINANCE_API_KEY",
            "BINANCE_API_SECRET",
            "ALPACA_API_KEY",
            "CAPITAL_API_KEY",
        ),
        cadence_sec=3600,
        priority=82,
        max_calls_per_hour=40,
        command=("python", "scripts/python/sync_global_history_db.py"),
        next_action="Keep private account trade history synced for cost basis, execution learning, and risk memory.",
    ),
    DataOceanSource(
        "queen_knowledge",
        "Queen knowledge, memories, insights, thoughts, and strategies",
        "internal",
        ("knowledge", "forecasts", "reasoning", "memory"),
        "queen_tables",
        cadence_sec=21600,
        priority=45,
        max_calls_per_hour=10,
        command=("python", "scripts/python/ingest_queen_knowledge.py", "--sources", "all"),
        next_action="Refresh internal memory and strategy knowledge into the global history database.",
    ),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path, default: Any) -> Any:
    try:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")


def _read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        if not path.exists():
            return values
        for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            if line.lower().startswith("export "):
                line = line[7:].strip()
            key, value = line.split("=", 1)
            key = key.strip()
            if not key:
                continue
            value = value.strip().strip('"').strip("'")
            values[key] = value
    except Exception:
        return values
    return values


def _merged_env(root: Path) -> dict[str, str]:
    env = dict(os.environ)
    for env_path in (root / ".env", root / ".env.local"):
        for key, value in _read_env_file(env_path).items():
            if value and not env.get(key):
                env[key] = value
    return env


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
        if math.isfinite(number):
            return number
    except Exception:
        pass
    return default


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(_as_float(value, default))
    except Exception:
        return default


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on", "ready", "fresh", "active", "configured"}
    return bool(value)


def _connect_existing(root: Path) -> Optional[sqlite3.Connection]:
    db_path = root / HISTORY_DB_PATH
    if not db_path.exists():
        return None
    try:
        conn = sqlite3.connect(str(db_path), timeout=5)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception:
        return None


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    try:
        return bool(conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone())
    except Exception:
        return False


def _count_table(conn: sqlite3.Connection, table: str) -> int:
    if not _table_exists(conn, table):
        return 0
    try:
        return _as_int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0], 0)
    except Exception:
        return 0


def _count_table_provider(conn: sqlite3.Connection, table: str, provider: str) -> int:
    if not _table_exists(conn, table):
        return 0
    try:
        return _as_int(
            conn.execute(
                f"SELECT COUNT(*) FROM {table} WHERE LOWER(COALESCE(provider, '')) = LOWER(?)",
                (provider,),
            ).fetchone()[0],
            0,
        )
    except Exception:
        return 0


def _count_table_source(conn: sqlite3.Connection, table: str, source: str) -> int:
    if not _table_exists(conn, table):
        return 0
    column = "source"
    try:
        columns = [row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
        if column not in columns:
            return 0
        return _as_int(
            conn.execute(
                f"SELECT COUNT(*) FROM {table} WHERE LOWER(COALESCE(source, '')) = LOWER(?) OR LOWER(COALESCE(source, '')) LIKE LOWER(?)",
                (source, f"%{source}%"),
            ).fetchone()[0],
            0,
        )
    except Exception:
        return 0


def _max_time_for_source(conn: sqlite3.Connection, source: DataOceanSource) -> Optional[int]:
    time_column_by_table = {
        "market_bars": "time_start_ms",
        "market_trades": "ts_ms",
        "account_trades": "ts_ms",
        "events": "event_ts_ms",
        "calendar_events": "event_ts_ms",
        "forecasts": "as_of_ts_ms",
        "macro_indicators": "observation_date_ms",
        "sentiment": "ts_ms",
        "onchain_metrics": "ts_ms",
    }
    if source.kind == "queen_tables":
        values: list[int] = []
        for table in ("queen_memories", "queen_insights", "queen_thoughts", "queen_knowledge", "forecasts"):
            if _table_exists(conn, table):
                try:
                    value = conn.execute(f"SELECT MAX(ts_ms) FROM {table}").fetchone()[0]
                    if value:
                        values.append(int(value))
                except Exception:
                    pass
        return max(values) if values else None
    table = source.evidence_table
    time_column = time_column_by_table.get(table)
    if not table or not time_column or not _table_exists(conn, table):
        return None
    where = ""
    params: tuple[Any, ...] = ()
    if source.kind == "table_provider" and source.evidence_provider:
        where = " WHERE LOWER(COALESCE(provider, '')) = LOWER(?)"
        params = (source.evidence_provider,)
    elif source.kind == "table_source" and source.evidence_source:
        where = " WHERE LOWER(COALESCE(source, '')) = LOWER(?) OR LOWER(COALESCE(source, '')) LIKE LOWER(?)"
        params = (source.evidence_source, f"%{source.evidence_source}%")
    try:
        return conn.execute(f"SELECT MAX({time_column}) FROM {table}{where}", params).fetchone()[0]
    except Exception:
        return None


def _ms_to_iso(value: Any) -> Optional[str]:
    number = _as_float(value, 0.0)
    if number <= 0:
        return None
    try:
        return datetime.fromtimestamp(number / 1000.0, timezone.utc).isoformat()
    except Exception:
        return None


def _credential_state(source: DataOceanSource, env: dict[str, str]) -> tuple[str, list[str]]:
    if not source.credential_env:
        return "not_required", []
    configured = [name for name in source.credential_env if env.get(name)]
    if configured:
        return "configured", []
    if source.optional:
        return "optional_missing", list(source.credential_env)
    return "missing", list(source.credential_env)


def _live_source_row(source: DataOceanSource, stream_cache: dict[str, Any], exchange_checklist: dict[str, Any]) -> dict[str, Any]:
    health = {}
    stream_health = stream_cache.get("source_health")
    if isinstance(stream_health, dict) and isinstance(stream_health.get(source.live_exchange), dict):
        health.update(stream_health[source.live_exchange])
    exchange_rows = exchange_checklist.get("rows") if isinstance(exchange_checklist.get("rows"), list) else []
    exchange_row = next(
        (row for row in exchange_rows if isinstance(row, dict) and row.get("exchange") == source.live_exchange),
        {},
    )
    active = _as_bool(health.get("active")) or _as_bool(exchange_row.get("cache_active"))
    fresh = _as_bool(health.get("fresh")) or _as_bool(exchange_row.get("cache_fresh"))
    ticker_count = max(_as_int(health.get("ticker_count"), 0), _as_int(exchange_row.get("ticker_count"), 0))
    return {
        "active": active,
        "fresh": fresh,
        "row_count": ticker_count,
        "last_success_at": health.get("generated_at") or health.get("timestamp") or exchange_row.get("last_timestamp"),
        "last_error": health.get("reason") or "",
        "evidence_path": f"{STREAM_CACHE_PATH.as_posix()}#source_health.{source.live_exchange}",
    }


def _history_source_row(source: DataOceanSource, conn: Optional[sqlite3.Connection]) -> dict[str, Any]:
    if conn is None:
        return {
            "active": False,
            "fresh": False,
            "row_count": 0,
            "last_success_at": None,
            "last_error": "history_database_missing",
            "evidence_path": HISTORY_DB_PATH.as_posix(),
        }
    if source.kind == "table_provider":
        row_count = _count_table_provider(conn, source.evidence_table, source.evidence_provider)
    elif source.kind == "table_source":
        row_count = _count_table_source(conn, source.evidence_table, source.evidence_source)
    elif source.kind == "table":
        row_count = _count_table(conn, source.evidence_table)
    elif source.kind == "queen_tables":
        row_count = sum(_count_table(conn, table) for table in ("queen_memories", "queen_insights", "queen_thoughts", "queen_knowledge", "forecasts"))
    else:
        row_count = 0
    last_ts = _max_time_for_source(conn, source)
    return {
        "active": row_count > 0,
        "fresh": row_count > 0,
        "row_count": row_count,
        "last_success_at": _ms_to_iso(last_ts),
        "last_error": "",
        "evidence_path": f"{HISTORY_DB_PATH.as_posix()}#{source.evidence_table or source.kind}",
    }


def evaluate_data_ocean_sources(
    *,
    root: Optional[Path] = None,
    runtime: Optional[dict[str, Any]] = None,
    stream_cache: Optional[dict[str, Any]] = None,
    exchange_checklist: Optional[dict[str, Any]] = None,
    env: Optional[dict[str, str]] = None,
    ingest_attempts: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    root = (root or REPO_ROOT).resolve()
    runtime = runtime if isinstance(runtime, dict) else _read_json(root / RUNTIME_STATUS_PATH, {})
    stream_cache = stream_cache if isinstance(stream_cache, dict) else _read_json(root / STREAM_CACHE_PATH, {})
    exchange_checklist = exchange_checklist if isinstance(exchange_checklist, dict) else _read_json(root / EXCHANGE_CHECKLIST_PATH, {})
    ingest_attempts = ingest_attempts if isinstance(ingest_attempts, dict) else _read_json(root / INGEST_ATTEMPTS_PATH, {})
    env = env if env is not None else _merged_env(root)
    runtime_stale = _as_bool(runtime.get("stale")) if isinstance(runtime, dict) else False
    conn = _connect_existing(root)
    rows: list[dict[str, Any]] = []
    try:
        for source in SOURCE_REGISTRY:
            credential_state, missing_credentials = _credential_state(source, env)
            if source.kind == "live_exchange":
                evidence = _live_source_row(source, stream_cache if isinstance(stream_cache, dict) else {}, exchange_checklist if isinstance(exchange_checklist, dict) else {})
            else:
                evidence = _history_source_row(source, conn)
            attempt = ingest_attempts.get(source.source_id) if isinstance(ingest_attempts, dict) else None
            attempt = attempt if isinstance(attempt, dict) else {}
            attempt_status = str(attempt.get("status") or "")
            evidence_error = str(evidence.get("last_error") or "")
            rate_limited_now = any(
                token in evidence_error.lower()
                for token in ("rate_limited", "rate limited", "too-many.requests", "429", "provider_backoff")
            )
            provider_unavailable = bool(
                (
                    attempt_status
                    in {
                        "provider_unavailable",
                        "provider_unavailable_or_no_data",
                        "rate_limited",
                        "unlicensed",
                        "out_of_scope",
                    }
                    or rate_limited_now
                )
                and _as_int(evidence.get("row_count"), 0) <= 0
            )
            configured_reachable = credential_state in {"configured", "not_required"}
            if provider_unavailable:
                configured_reachable = False
            active = bool(evidence["active"])
            source_fresh = bool(evidence["fresh"])
            usable = bool(configured_reachable and active and evidence["row_count"] > 0 and source_fresh)
            usable_for_decision = bool(usable and not (source.kind == "live_exchange" and runtime_stale))
            if credential_state == "missing":
                governor_action = "credential_required"
                reason = "required_credentials_missing"
            elif provider_unavailable:
                governor_action = "rate_limit_backoff" if rate_limited_now else "provider_unavailable"
                reason = evidence_error if rate_limited_now else str(attempt.get("reason") or attempt_status)
            elif usable:
                governor_action = "maintain" if usable_for_decision else "mapped_runtime_stale_decision_hold"
                reason = ""
            elif configured_reachable:
                governor_action = "run_refresh"
                reason = evidence.get("last_error") or "no_usable_rows_or_fresh_cache"
            else:
                governor_action = "explained_not_configured"
                reason = credential_state
            rows.append(
                {
                    "source_id": source.source_id,
                    "title": source.title,
                    "category": source.category,
                    "asset_classes": list(source.asset_classes),
                    "credential_state": credential_state,
                    "missing_credentials": missing_credentials,
                    "configured_reachable": configured_reachable,
                    "availability_state": attempt_status or ("rate_limited" if rate_limited_now else ("provider_unavailable" if provider_unavailable else "unknown")),
                    "active": active,
                    "fresh": source_fresh,
                    "usable_for_mapping": usable,
                    "usable_for_decision": usable_for_decision,
                    "decision_blocker": "runtime_stale" if usable and source.kind == "live_exchange" and runtime_stale else "",
                    "row_count": _as_int(evidence["row_count"], 0),
                    "last_success_at": evidence.get("last_success_at"),
                    "last_error": evidence.get("last_error") or "",
                    "last_attempt": attempt,
                    "rate_budget": {
                        "cadence_sec": source.cadence_sec,
                        "priority": source.priority,
                        "max_calls_per_hour": source.max_calls_per_hour,
                        "mode": "budgeted_adaptive",
                    },
                    "governor_action": governor_action,
                    "reason": reason,
                    "command": list(source.command),
                    "evidence_path": evidence.get("evidence_path"),
                    "next_action": source.next_action,
                }
            )
    finally:
        if conn is not None:
            conn.close()
    total = len(rows)
    configured = [row for row in rows if row["configured_reachable"]]
    usable = [row for row in configured if row["usable_for_mapping"]]
    accounted = [
        row
        for row in rows
        if row["usable_for_mapping"] or row["reason"] or row["credential_state"] in {"missing", "optional_missing"}
    ]
    coverage_percent = round((len(usable) / len(configured) * 100.0), 2) if configured else 0.0
    accounted_percent = round((len(accounted) / total * 100.0), 2) if total else 0.0
    mapping_complete = bool(configured and len(usable) == len(configured))
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now(),
        "coverage_profile": "LicensedReachable",
        "governor_mode": "budgeted_adaptive",
        "mapping_complete": mapping_complete,
        "summary": {
            "source_count": total,
            "configured_reachable_count": len(configured),
            "usable_source_count": len(usable),
            "decision_usable_source_count": sum(1 for row in rows if row.get("usable_for_decision")),
            "fresh_source_count": sum(1 for row in rows if row["fresh"]),
            "credential_missing_count": sum(1 for row in rows if row["credential_state"] == "missing"),
            "coverage_percent": coverage_percent,
            "accounted_percent": accounted_percent,
            "runtime_stale": runtime_stale,
            "top_gaps": [
                {"source_id": row["source_id"], "reason": row["reason"], "next_action": row["next_action"]}
                for row in rows
                if not row["usable_for_mapping"]
            ][:12],
        },
        "sources": rows,
    }


def build_data_ocean_status(
    root: Optional[Path] = None,
    *,
    coverage_profile: str = "LicensedReachable",
    adaptive: bool = True,
    dry_run: bool = False,
) -> dict[str, Any]:
    root = (root or REPO_ROOT).resolve()
    status = evaluate_data_ocean_sources(root=root)
    status.update(
        {
            "status": "data_ocean_complete" if status["mapping_complete"] else "data_ocean_ready_with_gaps",
            "repo_root": str(root),
            "coverage_profile": coverage_profile,
            "adaptive": bool(adaptive),
            "dry_run": bool(dry_run),
            "contract": {
                "definition_of_100_percent": "Every configured/reachable registered source is usable, or every unavailable source is explicitly classified.",
                "execution_priority": "live execution and positions first, live ticks second, history/backfill third",
                "no_execution_change": "The data ocean refreshes evidence only and never bypasses trading runtime gates.",
            },
        }
    )
    return status


def write_data_ocean_status(
    report: dict[str, Any],
    output_json: Path = REPO_ROOT / STATE_PATH,
    public_json: Path = REPO_ROOT / PUBLIC_PATH,
) -> tuple[Path, Path]:
    _write_json(output_json, report)
    _write_json(public_json, report)
    return output_json, public_json


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Aureon's planetary data-ocean status.")
    parser.add_argument("--repo-root", default="", help="Repo root; defaults to current Aureon repo.")
    parser.add_argument("--coverage-profile", default="LicensedReachable", choices=["LicensedReachable", "FreeOpenOnly", "InstitutionalMax"])
    parser.add_argument("--adaptive", action="store_true", help="Use budgeted adaptive source governor.")
    parser.add_argument("--dry-run", action="store_true", help="Do not ingest; only report planned source state.")
    parser.add_argument("--json", default=str(REPO_ROOT / STATE_PATH), help="State JSON path.")
    parser.add_argument("--public-json", default=str(REPO_ROOT / PUBLIC_PATH), help="Frontend public JSON path.")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    root = Path(args.repo_root).resolve() if args.repo_root else REPO_ROOT
    report = build_data_ocean_status(
        root,
        coverage_profile=args.coverage_profile,
        adaptive=bool(args.adaptive),
        dry_run=bool(args.dry_run),
    )
    output_json, public_json = write_data_ocean_status(report, Path(args.json), Path(args.public_json))
    print(
        json.dumps(
            {
                "json": str(output_json),
                "public_json": str(public_json),
                "summary": report["summary"],
                "status": report["status"],
            },
            indent=2,
            sort_keys=True,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
