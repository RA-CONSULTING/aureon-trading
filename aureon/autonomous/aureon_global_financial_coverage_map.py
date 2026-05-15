"""Global financial coverage map for Aureon.

This report shows how much of the financial ecosystem Aureon can see right
now: live exchange feeds, historical waveform memory, symbols, macro context,
events, sentiment, on-chain context, forecasts, and account trade memory.
"""

from __future__ import annotations

import argparse
import json
import math
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Sequence

from aureon.autonomous.aureon_data_ocean import evaluate_data_ocean_sources


SCHEMA_VERSION = "aureon-global-financial-coverage-map-v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_STATUS_PATH = Path("state/unified_runtime_status.json")
STREAM_CACHE_PATH = Path("ws_cache/ws_prices.json")
EXCHANGE_CHECKLIST_PATH = Path("docs/audits/aureon_exchange_monitoring_checklist.json")
WAVEFORM_RECORDER_PATH = Path("state/aureon_live_waveform_recorder.json")
HISTORY_DB_PATH = Path("state/aureon_global_history.sqlite")
DEFAULT_OUTPUT_JSON = REPO_ROOT / "docs/audits/aureon_global_financial_coverage_map.json"
DEFAULT_OUTPUT_MD = REPO_ROOT / "docs/audits/aureon_global_financial_coverage_map.md"
DEFAULT_PUBLIC_JSON = REPO_ROOT / "frontend/public/aureon_global_financial_coverage_map.json"


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
        return value.strip().lower() in {"1", "true", "yes", "on", "fresh", "ready", "active"}
    return bool(value)


def _connect_existing(db_path: Path) -> Optional[sqlite3.Connection]:
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
        row = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
        return bool(row)
    except Exception:
        return False


def _scalar(conn: sqlite3.Connection, sql: str, params: Sequence[Any] = ()) -> Any:
    try:
        row = conn.execute(sql, tuple(params)).fetchone()
        if row is None:
            return None
        return row[0]
    except Exception:
        return None


def _group_counts(conn: sqlite3.Connection, sql: str, params: Sequence[Any] = (), limit: int = 12) -> list[dict[str, Any]]:
    try:
        rows = conn.execute(sql, tuple(params)).fetchmany(limit)
        return [{"name": str(row[0] or "unknown"), "count": _as_int(row[1], 0)} for row in rows]
    except Exception:
        return []


def _ms_to_iso(value: Any) -> Optional[str]:
    number = _as_float(value, 0.0)
    if number <= 0:
        return None
    try:
        return datetime.fromtimestamp(number / 1000.0, timezone.utc).isoformat()
    except Exception:
        return None


def _history_table_summary(conn: sqlite3.Connection, table: str, time_column: str, symbol_column: str = "symbol") -> dict[str, Any]:
    if not _table_exists(conn, table):
        return {"table": table, "present": False, "row_count": 0, "symbol_count": 0}
    row_count = _as_int(_scalar(conn, f"SELECT COUNT(*) FROM {table}"), 0)
    symbol_count = _as_int(
        _scalar(conn, f"SELECT COUNT(DISTINCT COALESCE(NULLIF({symbol_column}, ''), 'unknown')) FROM {table}"),
        0,
    )
    min_ts = _scalar(conn, f"SELECT MIN({time_column}) FROM {table}")
    max_ts = _scalar(conn, f"SELECT MAX({time_column}) FROM {table}")
    recent_since = int((time.time() - 24 * 60 * 60) * 1000)
    recent_count = _as_int(_scalar(conn, f"SELECT COUNT(*) FROM {table} WHERE {time_column} >= ?", (recent_since,)), 0)
    return {
        "table": table,
        "present": True,
        "row_count": row_count,
        "symbol_count": symbol_count,
        "first_at": _ms_to_iso(min_ts),
        "last_at": _ms_to_iso(max_ts),
        "recent_24h_count": recent_count,
    }


def _history_db_summary(root: Path) -> dict[str, Any]:
    db_path = root / HISTORY_DB_PATH
    conn = _connect_existing(db_path)
    if conn is None:
        return {
            "present": False,
            "db_path": str(HISTORY_DB_PATH).replace("\\", "/"),
            "missing": ["history_database_missing"],
            "tables": {},
        }
    try:
        tables = {
            "market_bars": _history_table_summary(conn, "market_bars", "time_start_ms"),
            "market_trades": _history_table_summary(conn, "market_trades", "ts_ms"),
            "account_trades": _history_table_summary(conn, "account_trades", "ts_ms"),
            "events": _history_table_summary(conn, "events", "event_ts_ms"),
            "calendar_events": _history_table_summary(conn, "calendar_events", "event_ts_ms", "currency"),
            "forecasts": _history_table_summary(conn, "forecasts", "as_of_ts_ms"),
            "macro_indicators": _history_table_summary(conn, "macro_indicators", "observation_date_ms", "series_id"),
            "sentiment": _history_table_summary(conn, "sentiment", "ts_ms"),
            "onchain_metrics": _history_table_summary(conn, "onchain_metrics", "ts_ms", "asset"),
            "symbols": {
                "table": "symbols",
                "present": _table_exists(conn, "symbols"),
                "row_count": _as_int(_scalar(conn, "SELECT COUNT(*) FROM symbols") if _table_exists(conn, "symbols") else 0, 0),
                "symbol_count": _as_int(
                    _scalar(conn, "SELECT COUNT(DISTINCT COALESCE(NULLIF(symbol, ''), symbol_id)) FROM symbols")
                    if _table_exists(conn, "symbols")
                    else 0,
                    0,
                ),
            },
        }
        providers = _group_counts(
            conn,
            "SELECT COALESCE(provider, 'unknown') AS provider, COUNT(*) FROM market_bars GROUP BY provider ORDER BY COUNT(*) DESC",
        ) if _table_exists(conn, "market_bars") else []
        venues = _group_counts(
            conn,
            "SELECT COALESCE(venue, 'unknown') AS venue, COUNT(*) FROM market_bars GROUP BY venue ORDER BY COUNT(*) DESC",
        ) if _table_exists(conn, "market_bars") else []
        periods = _group_counts(
            conn,
            "SELECT COALESCE(period_id, 'unknown') AS period_id, COUNT(*) FROM market_bars GROUP BY period_id ORDER BY COUNT(*) DESC",
        ) if _table_exists(conn, "market_bars") else []
        return {
            "present": True,
            "db_path": str(HISTORY_DB_PATH).replace("\\", "/"),
            "size_bytes": db_path.stat().st_size if db_path.exists() else 0,
            "tables": tables,
            "market_bar_providers": providers,
            "market_bar_venues": venues,
            "market_bar_periods": periods,
            "missing": [],
        }
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _stream_summary(stream_cache: dict[str, Any]) -> dict[str, Any]:
    ticker_cache = stream_cache.get("ticker_cache") if isinstance(stream_cache.get("ticker_cache"), dict) else {}
    source_health = stream_cache.get("source_health") if isinstance(stream_cache.get("source_health"), dict) else {}
    exchange_counts: dict[str, int] = {}
    quote_counts: dict[str, int] = {}
    for entry in ticker_cache.values():
        if not isinstance(entry, dict):
            continue
        exchange = str(entry.get("exchange") or "unknown").lower()
        quote = str(entry.get("quote") or "unknown").upper()
        exchange_counts[exchange] = exchange_counts.get(exchange, 0) + 1
        quote_counts[quote] = quote_counts.get(quote, 0) + 1
    return {
        "present": bool(stream_cache),
        "source": stream_cache.get("source", ""),
        "generated_at": stream_cache.get("generated_at"),
        "source_count": _as_int(stream_cache.get("source_count"), len(source_health)),
        "active_source_count": _as_int(stream_cache.get("active_source_count"), sum(1 for item in source_health.values() if isinstance(item, dict) and _as_bool(item.get("active")))),
        "ticker_count": len(ticker_cache),
        "exchange_counts": [{"name": key, "count": value} for key, value in sorted(exchange_counts.items())],
        "quote_counts": [{"name": key, "count": value} for key, value in sorted(quote_counts.items(), key=lambda item: item[1], reverse=True)[:12]],
        "source_health": source_health,
    }


def _exchange_summary(exchange_checklist: dict[str, Any]) -> dict[str, Any]:
    rows = exchange_checklist.get("rows") if isinstance(exchange_checklist.get("rows"), list) else []
    return {
        "present": bool(rows),
        "status": exchange_checklist.get("status", "missing"),
        "summary": exchange_checklist.get("summary") if isinstance(exchange_checklist.get("summary"), dict) else {},
        "exchanges": [
            {
                "exchange": row.get("exchange"),
                "connected": row.get("connected"),
                "cache_fresh": row.get("cache_fresh"),
                "ticker_count": row.get("ticker_count"),
                "feeds_decision_logic": row.get("feeds_decision_logic"),
                "missing": row.get("missing", [])[:5] if isinstance(row.get("missing"), list) else [],
            }
            for row in rows
            if isinstance(row, dict)
        ],
    }


def _augment_stream_with_durable_exchange_evidence(
    stream: dict[str, Any],
    *,
    exchange: dict[str, Any],
    recorder: dict[str, Any],
) -> dict[str, Any]:
    augmented = dict(stream)
    source_health = dict(augmented.get("source_health") or {})
    recorder_health = recorder.get("source_health") if isinstance(recorder.get("source_health"), dict) else {}
    for key, health in recorder_health.items():
        if not isinstance(health, dict):
            continue
        current = source_health.get(key)
        if not isinstance(current, dict) or (_as_bool(health.get("active")) and not _as_bool(current.get("active"))):
            source_health[str(key)] = dict(health)

    exchange_counts = {str(item.get("name")): _as_int(item.get("count"), 0) for item in augmented.get("exchange_counts", []) if isinstance(item, dict)}
    exchange_rows = exchange.get("exchanges") if isinstance(exchange.get("exchanges"), list) else []
    for row in exchange_rows:
        if not isinstance(row, dict):
            continue
        exchange_name = str(row.get("exchange") or "").lower()
        if not exchange_name:
            continue
        exchange_counts[exchange_name] = max(exchange_counts.get(exchange_name, 0), _as_int(row.get("ticker_count"), 0))
        if exchange_name not in source_health and _as_bool(row.get("cache_fresh")):
            source_health[exchange_name] = {
                "source": "exchange_monitoring_checklist",
                "active": True,
                "fresh": True,
                "ticker_count": _as_int(row.get("ticker_count"), 0),
                "generated_at": row.get("last_timestamp"),
                "reason": "",
            }

    active_source_count = sum(1 for item in source_health.values() if isinstance(item, dict) and _as_bool(item.get("active")))
    ticker_count = max(
        _as_int(augmented.get("ticker_count"), 0),
        sum(exchange_counts.values()),
        _as_int(recorder.get("cache_ticker_count"), 0) if isinstance(recorder, dict) else 0,
    )
    augmented["source_health"] = source_health
    augmented["source_count"] = max(_as_int(augmented.get("source_count"), 0), len(source_health))
    augmented["active_source_count"] = max(_as_int(augmented.get("active_source_count"), 0), active_source_count)
    augmented["ticker_count"] = ticker_count
    augmented["exchange_counts"] = [{"name": key, "count": value} for key, value in sorted(exchange_counts.items())]
    return augmented


def _coverage_rows(
    *,
    runtime: dict[str, Any],
    stream: dict[str, Any],
    exchange: dict[str, Any],
    history: dict[str, Any],
) -> list[dict[str, Any]]:
    tables = history.get("tables") if isinstance(history.get("tables"), dict) else {}
    exchange_summary = exchange.get("summary") if isinstance(exchange.get("summary"), dict) else {}
    runtime_stale = _as_bool(runtime.get("stale"))
    rows = [
        {
            "domain": "crypto_live_market",
            "coverage": "Binance/Kraken crypto ticks and spot/margin context",
            "live_count": _as_int(stream.get("ticker_count"), 0),
            "history_count": _as_int(tables.get("market_bars", {}).get("row_count"), 0) if isinstance(tables.get("market_bars"), dict) else 0,
            "fresh": _as_int(exchange_summary.get("fresh_exchange_count"), 0) > 0 and not runtime_stale,
            "usable": _as_int(exchange_summary.get("decision_fed_exchange_count"), 0) > 0 and not runtime_stale,
            "missing": ["kraken_live_cache"] if _as_int(exchange_summary.get("fresh_exchange_count"), 0) < 2 else [],
            "next_action": "Keep Binance streaming; activate Kraken live cache, spot/margin fee context, and order-book probes.",
        },
        {
            "domain": "equity_and_etf_live_market",
            "coverage": "Alpaca stock/ETF/crypto market snapshots",
            "live_count": sum(item.get("count", 0) for item in stream.get("exchange_counts", []) if item.get("name") == "alpaca"),
            "history_count": _as_int(tables.get("symbols", {}).get("row_count"), 0) if isinstance(tables.get("symbols"), dict) else 0,
            "fresh": any(row.get("exchange") == "alpaca" and row.get("cache_fresh") for row in exchange.get("exchanges", [])),
            "usable": any(row.get("exchange") == "alpaca" and row.get("feeds_decision_logic") for row in exchange.get("exchanges", [])),
            "missing": ["alpaca_fresh_live_cache", "market_hours_state"] if not any(row.get("exchange") == "alpaca" and row.get("cache_fresh") for row in exchange.get("exchanges", [])) else [],
            "next_action": "Use Alpaca snapshots/stream entitlements to add fresh equity and ETF ticks.",
        },
        {
            "domain": "cfd_fx_indices_equities",
            "coverage": "Capital.com CFD positions, equity, and market snapshots",
            "live_count": sum(item.get("count", 0) for item in stream.get("exchange_counts", []) if item.get("name") == "capital"),
            "history_count": _as_int(tables.get("account_trades", {}).get("row_count"), 0) if isinstance(tables.get("account_trades"), dict) else 0,
            "fresh": any(row.get("exchange") == "capital" and row.get("cache_fresh") for row in exchange.get("exchanges", [])),
            "usable": any(row.get("exchange") == "capital" and row.get("feeds_decision_logic") for row in exchange.get("exchanges", [])),
            "missing": ["capital_fresh_market_snapshot", "position_close_speed_probe"] if not any(row.get("exchange") == "capital" and row.get("cache_fresh") for row in exchange.get("exchanges", [])) else [],
            "next_action": "Add Capital market snapshot refresh and fast profitable-position close telemetry.",
        },
        {
            "domain": "historical_waveform_memory",
            "coverage": "1h to 1y market bar memory for multi-horizon waveform models",
            "live_count": _as_int(stream.get("ticker_count"), 0),
            "history_count": _as_int(tables.get("market_bars", {}).get("row_count"), 0) if isinstance(tables.get("market_bars"), dict) else 0,
            "fresh": _as_int(tables.get("market_bars", {}).get("recent_24h_count"), 0) > 0 if isinstance(tables.get("market_bars"), dict) else False,
            "usable": _as_int(tables.get("market_bars", {}).get("symbol_count"), 0) > 0 if isinstance(tables.get("market_bars"), dict) else False,
            "missing": ["live_waveform_recorder_not_current"] if _as_int(tables.get("market_bars", {}).get("recent_24h_count"), 0) <= 0 else [],
            "next_action": "Keep live cache writing bars into global history so models build from 1h through 1y.",
        },
        {
            "domain": "macro_events_context",
            "coverage": "Macro indicators, calendar events, earnings/geopolitical events",
            "live_count": _as_int(tables.get("calendar_events", {}).get("recent_24h_count"), 0) if isinstance(tables.get("calendar_events"), dict) else 0,
            "history_count": _as_int(tables.get("macro_indicators", {}).get("row_count"), 0) + _as_int(tables.get("events", {}).get("row_count"), 0) if isinstance(tables.get("macro_indicators"), dict) and isinstance(tables.get("events"), dict) else 0,
            "fresh": _as_int(tables.get("calendar_events", {}).get("recent_24h_count"), 0) > 0 if isinstance(tables.get("calendar_events"), dict) else False,
            "usable": _as_int(tables.get("macro_indicators", {}).get("row_count"), 0) > 0 if isinstance(tables.get("macro_indicators"), dict) else False,
            "missing": ["fresh_economic_calendar"] if _as_int(tables.get("calendar_events", {}).get("recent_24h_count"), 0) <= 0 else [],
            "next_action": "Refresh owned/licensed macro calendar and event feeds for context-aware trade selection.",
        },
        {
            "domain": "sentiment_onchain_forecast_context",
            "coverage": "Sentiment, on-chain observations, and forecast memory",
            "live_count": _as_int(tables.get("sentiment", {}).get("recent_24h_count"), 0) + _as_int(tables.get("onchain_metrics", {}).get("recent_24h_count"), 0) if isinstance(tables.get("sentiment"), dict) and isinstance(tables.get("onchain_metrics"), dict) else 0,
            "history_count": _as_int(tables.get("sentiment", {}).get("row_count"), 0) + _as_int(tables.get("onchain_metrics", {}).get("row_count"), 0) + _as_int(tables.get("forecasts", {}).get("row_count"), 0) if isinstance(tables.get("sentiment"), dict) and isinstance(tables.get("onchain_metrics"), dict) and isinstance(tables.get("forecasts"), dict) else 0,
            "fresh": _as_int(tables.get("sentiment", {}).get("recent_24h_count"), 0) > 0 if isinstance(tables.get("sentiment"), dict) else False,
            "usable": _as_int(tables.get("forecasts", {}).get("row_count"), 0) > 0 if isinstance(tables.get("forecasts"), dict) else False,
            "missing": ["fresh_sentiment_or_onchain_context"] if _as_int(tables.get("sentiment", {}).get("recent_24h_count"), 0) <= 0 else [],
            "next_action": "Feed sentiment, on-chain, and forecast claims into the decision memory with timestamps.",
        },
    ]
    return rows


def _summary(
    rows: list[dict[str, Any]],
    history: dict[str, Any],
    stream: dict[str, Any],
    exchange: dict[str, Any],
    data_ocean: dict[str, Any],
) -> dict[str, Any]:
    covered = [row for row in rows if row.get("usable")]
    fresh = [row for row in rows if row.get("fresh")]
    total_history = 0
    tables = history.get("tables") if isinstance(history.get("tables"), dict) else {}
    for table in tables.values():
        if isinstance(table, dict):
            total_history += _as_int(table.get("row_count"), 0)
    missing: list[dict[str, str]] = []
    for row in rows:
        for item in row.get("missing", [])[:4]:
            missing.append({"domain": row["domain"], "missing": str(item)})
    status = "global_financial_map_ready_with_gaps"
    if not stream.get("ticker_count"):
        status = "global_financial_map_missing_live_ticks"
    if not history.get("present"):
        status = "global_financial_map_missing_history_db"
    ocean_summary = data_ocean.get("summary") if isinstance(data_ocean.get("summary"), dict) else {}
    mapping_complete = bool(data_ocean.get("mapping_complete"))
    if mapping_complete and status == "global_financial_map_ready_with_gaps":
        status = "global_financial_map_complete_for_configured_registry"
    return {
        "domain_count": len(rows),
        "usable_domain_count": len(covered),
        "fresh_domain_count": len(fresh),
        "source_count": _as_int(ocean_summary.get("source_count"), 0),
        "configured_reachable_source_count": _as_int(ocean_summary.get("configured_reachable_count"), 0),
        "usable_source_count": _as_int(ocean_summary.get("usable_source_count"), 0),
        "fresh_source_count": _as_int(ocean_summary.get("fresh_source_count"), 0),
        "credential_missing_source_count": _as_int(ocean_summary.get("credential_missing_count"), 0),
        "coverage_percent": _as_float(ocean_summary.get("coverage_percent"), 0.0),
        "accounted_percent": _as_float(ocean_summary.get("accounted_percent"), 0.0),
        "mapping_complete": mapping_complete,
        "live_ticker_count": _as_int(stream.get("ticker_count"), 0),
        "active_live_source_count": _as_int(stream.get("active_source_count"), 0),
        "fresh_exchange_count": _as_int((exchange.get("summary") or {}).get("fresh_exchange_count"), 0) if isinstance(exchange.get("summary"), dict) else 0,
        "decision_fed_exchange_count": _as_int((exchange.get("summary") or {}).get("decision_fed_exchange_count"), 0) if isinstance(exchange.get("summary"), dict) else 0,
        "history_db_present": bool(history.get("present")),
        "history_db_size_bytes": _as_int(history.get("size_bytes"), 0),
        "total_history_rows": total_history,
        "top_missing": missing[:12],
        "status": status,
    }


def build_global_financial_coverage_map(root: Optional[Path] = None) -> dict[str, Any]:
    root = (root or REPO_ROOT).resolve()
    runtime = _read_json(root / RUNTIME_STATUS_PATH, {})
    stream_cache = _read_json(root / STREAM_CACHE_PATH, {})
    exchange_checklist = _read_json(root / EXCHANGE_CHECKLIST_PATH, {})
    recorder = _read_json(root / WAVEFORM_RECORDER_PATH, {})
    if not isinstance(runtime, dict):
        runtime = {}
    if not isinstance(stream_cache, dict):
        stream_cache = {}
    if not isinstance(exchange_checklist, dict):
        exchange_checklist = {}
    exchange = _exchange_summary(exchange_checklist)
    stream = _augment_stream_with_durable_exchange_evidence(
        _stream_summary(stream_cache),
        exchange=exchange,
        recorder=recorder if isinstance(recorder, dict) else {},
    )
    history = _history_db_summary(root)
    data_ocean = evaluate_data_ocean_sources(
        root=root,
        runtime=runtime,
        stream_cache=stream_cache,
        exchange_checklist=exchange_checklist,
    )
    rows = _coverage_rows(runtime=runtime, stream=stream, exchange=exchange, history=history)
    summary = _summary(rows, history, stream, exchange, data_ocean)
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now(),
        "status": summary["status"],
        "repo_root": str(root),
        "summary": summary,
        "contract": {
            "purpose": "Map current live and historical coverage of the planetary financial ecosystem.",
            "source_of_truth": "runtime status, live stream cache, exchange monitoring checklist, and global history database.",
            "no_execution_change": "This map does not place trades, change credentials, or bypass runtime checks.",
        },
        "live_stream": stream,
        "exchange_monitoring": exchange,
        "data_ocean": data_ocean,
        "source_registry": data_ocean.get("sources", []),
        "history": history,
        "rows": rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    rows = report.get("rows") if isinstance(report.get("rows"), list) else []
    lines = [
        "# Aureon Global Financial Coverage Map",
        "",
        f"- Generated: {report.get('generated_at', '')}",
        f"- Status: {report.get('status', '')}",
        f"- Usable domains: {summary.get('usable_domain_count', 0)}/{summary.get('domain_count', 0)}",
        f"- Fresh domains: {summary.get('fresh_domain_count', 0)}/{summary.get('domain_count', 0)}",
        f"- Source coverage: {summary.get('coverage_percent', 0)}%",
        f"- Usable sources: {summary.get('usable_source_count', 0)}/{summary.get('configured_reachable_source_count', 0)} configured/reachable",
        f"- Accounted sources: {summary.get('accounted_percent', 0)}%",
        f"- Live tickers: {summary.get('live_ticker_count', 0)}",
        f"- Active live sources: {summary.get('active_live_source_count', 0)}",
        f"- Fresh exchanges: {summary.get('fresh_exchange_count', 0)}",
        f"- Decision-fed exchanges: {summary.get('decision_fed_exchange_count', 0)}",
        f"- History rows: {summary.get('total_history_rows', 0)}",
        f"- History DB bytes: {summary.get('history_db_size_bytes', 0)}",
        "",
        "| Domain | Fresh | Usable | Live Count | History Count | Missing | Next Action |",
        "| --- | --- | --- | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {domain} | {fresh} | {usable} | {live} | {history} | {missing} | {next_action} |".format(
                domain=str(row.get("domain", "")),
                fresh=row.get("fresh", False),
                usable=row.get("usable", False),
                live=row.get("live_count", 0),
                history=row.get("history_count", 0),
                missing=", ".join(str(item) for item in row.get("missing", [])[:4]).replace("|", "/"),
                next_action=str(row.get("next_action", "")).replace("|", "/"),
            )
        )
    sources = report.get("source_registry") if isinstance(report.get("source_registry"), list) else []
    lines.extend(
        [
            "",
            "## Source Registry",
            "",
            "| Source | Category | Credentials | Usable | Rows | Governor | Reason |",
            "| --- | --- | --- | --- | ---: | --- | --- |",
        ]
    )
    for source in sources:
        lines.append(
            "| {source} | {category} | {credential} | {usable} | {rows} | {action} | {reason} |".format(
                source=str(source.get("source_id", "")),
                category=str(source.get("category", "")),
                credential=str(source.get("credential_state", "")),
                usable=source.get("usable_for_mapping", False),
                rows=source.get("row_count", 0),
                action=str(source.get("governor_action", "")),
                reason=str(source.get("reason", "")).replace("|", "/"),
            )
        )
    lines.extend(["", "This is an evidence map only. It does not execute trades or bypass live safety checks."])
    return "\n".join(lines) + "\n"


def write_global_financial_coverage_map(
    report: dict[str, Any],
    output_json: Path = DEFAULT_OUTPUT_JSON,
    output_md: Path = DEFAULT_OUTPUT_MD,
    public_json: Path = DEFAULT_PUBLIC_JSON,
) -> tuple[Path, Path, Path]:
    _write_json(output_json, report)
    _write_json(public_json, report)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(render_markdown(report), encoding="utf-8")
    return output_json, output_md, public_json


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Aureon's global financial coverage map.")
    parser.add_argument("--repo-root", default="", help="Repo root; defaults to current Aureon repo.")
    parser.add_argument("--json", default=str(DEFAULT_OUTPUT_JSON), help="Audit JSON path.")
    parser.add_argument("--md", default=str(DEFAULT_OUTPUT_MD), help="Audit Markdown path.")
    parser.add_argument("--public-json", default=str(DEFAULT_PUBLIC_JSON), help="Frontend public JSON path.")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    root = Path(args.repo_root).resolve() if args.repo_root else REPO_ROOT
    report = build_global_financial_coverage_map(root)
    output_json, output_md, public_json = write_global_financial_coverage_map(
        report,
        Path(args.json),
        Path(args.md),
        Path(args.public_json),
    )
    print(
        json.dumps(
            {
                "json": str(output_json),
                "md": str(output_md),
                "public_json": str(public_json),
                "summary": report["summary"],
            },
            indent=2,
            sort_keys=True,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
