import json
import time
from pathlib import Path

from aureon.autonomous.aureon_global_financial_coverage_map import (
    SCHEMA_VERSION,
    build_global_financial_coverage_map,
    write_global_financial_coverage_map,
)
from aureon.core.aureon_global_history_db import (
    connect,
    insert_calendar_event,
    insert_macro_indicator,
    insert_market_bar,
    insert_onchain_metric,
    insert_sentiment,
)


def _write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _seed_history(root: Path):
    db_path = root / "state" / "aureon_global_history.sqlite"
    conn = connect(str(db_path))
    now_ms = int(time.time() * 1000)
    try:
        insert_market_bar(
            conn,
            {
                "provider": "unit",
                "venue": "BINANCE",
                "symbol_id": "BTCUSDT",
                "symbol": "BTCUSD",
                "period_id": "1MIN",
                "time_start_ms": now_ms - 60_000,
                "time_end_ms": now_ms,
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.5,
                "volume": 10_000.0,
                "raw_json": "{}",
            },
        )
        insert_macro_indicator(
            conn,
            {
                "provider": "unit_macro",
                "series_id": "GDP",
                "series_name": "GDP",
                "category": "growth",
                "region": "US",
                "frequency": "monthly",
                "units": "index",
                "observation_date_ms": now_ms - 3_600_000,
                "value": 1.0,
                "raw_json": "{}",
            },
        )
        insert_calendar_event(
            conn,
            {
                "source": "unit_calendar",
                "event_id": "event-1",
                "event_type": "macro",
                "title": "Rate decision",
                "country": "US",
                "currency": "USD",
                "impact": "high",
                "event_ts_ms": now_ms - 1_000,
                "raw_json": "{}",
            },
        )
        insert_sentiment(
            conn,
            {
                "source": "unit_sentiment",
                "sentiment_id": "sent-1",
                "sentiment_type": "market",
                "symbol": "BTCUSD",
                "value": 0.7,
                "label": "positive",
                "ts_ms": now_ms - 1_000,
                "raw_json": "{}",
            },
        )
        insert_onchain_metric(
            conn,
            {
                "provider": "unit_onchain",
                "metric_id": "metric-1",
                "metric_name": "active_addresses",
                "asset": "BTC",
                "value": 1.0,
                "ts_ms": now_ms - 1_000,
                "raw_json": "{}",
            },
        )
        conn.commit()
    finally:
        conn.close()


def test_global_financial_coverage_map_reads_live_history_and_context(tmp_path):
    _write_json(tmp_path / "state" / "unified_runtime_status.json", {"stale": False})
    _write_json(
        tmp_path / "ws_cache" / "ws_prices.json",
        {
            "source": "multi_exchange_stream_cache",
            "source_count": 2,
            "active_source_count": 2,
            "ticker_cache": {
                "binance:BTCUSDT": {"exchange": "binance", "quote": "USDT"},
                "kraken:XBTUSD": {"exchange": "kraken", "quote": "USD"},
            },
            "source_health": {
                "binance": {"active": True, "fresh": True},
                "kraken": {"active": True, "fresh": True},
            },
        },
    )
    _write_json(
        tmp_path / "docs" / "audits" / "aureon_exchange_monitoring_checklist.json",
        {
            "status": "exchange_monitoring_ready",
            "summary": {"fresh_exchange_count": 2, "decision_fed_exchange_count": 1},
            "rows": [
                {"exchange": "binance", "cache_fresh": True, "ticker_count": 1, "feeds_decision_logic": True},
                {"exchange": "kraken", "cache_fresh": True, "ticker_count": 1, "feeds_decision_logic": False},
            ],
        },
    )
    _seed_history(tmp_path)

    report = build_global_financial_coverage_map(tmp_path)
    rows = {row["domain"]: row for row in report["rows"]}

    assert report["schema_version"] == SCHEMA_VERSION
    assert report["summary"]["live_ticker_count"] == 2
    assert report["summary"]["history_db_present"] is True
    assert report["summary"]["total_history_rows"] > 0
    assert rows["crypto_live_market"]["live_count"] == 2
    assert rows["historical_waveform_memory"]["usable"] is True
    assert rows["macro_events_context"]["usable"] is True
    assert rows["sentiment_onchain_forecast_context"]["fresh"] is True
    assert report["summary"]["source_count"] > 0
    assert report["summary"]["accounted_percent"] >= report["summary"]["coverage_percent"]
    assert any(source["source_id"] == "yfinance_history" for source in report["source_registry"])


def test_missing_history_and_live_ticks_are_reported(tmp_path):
    report = build_global_financial_coverage_map(tmp_path)

    assert report["summary"]["history_db_present"] is False
    assert report["summary"]["live_ticker_count"] == 0
    assert report["status"] == "global_financial_map_missing_history_db"
    assert report["summary"]["top_missing"]


def test_global_financial_coverage_map_uses_exchange_checklist_when_fast_cache_write_is_partial(tmp_path):
    _write_json(tmp_path / "state" / "unified_runtime_status.json", {"stale": False})
    _write_json(
        tmp_path / "ws_cache" / "ws_prices.json",
        {
            "source": "multi_exchange_stream_cache",
            "source_count": 1,
            "active_source_count": 1,
            "ticker_cache": {"binance:BTCUSDT": {"exchange": "binance", "quote": "USDT"}},
            "source_health": {"binance": {"active": True, "fresh": True, "ticker_count": 1}},
        },
    )
    _write_json(
        tmp_path / "docs" / "audits" / "aureon_exchange_monitoring_checklist.json",
        {
            "summary": {"fresh_exchange_count": 4, "decision_fed_exchange_count": 0, "total_tickers_monitored": 4},
            "rows": [
                {"exchange": "binance", "cache_fresh": True, "ticker_count": 1, "feeds_decision_logic": False},
                {"exchange": "kraken", "cache_fresh": True, "ticker_count": 1, "feeds_decision_logic": False},
                {"exchange": "alpaca", "cache_fresh": True, "ticker_count": 1, "feeds_decision_logic": False},
                {"exchange": "capital", "cache_fresh": True, "ticker_count": 1, "feeds_decision_logic": False},
            ],
        },
    )
    _write_json(
        tmp_path / "state" / "aureon_live_waveform_recorder.json",
        {
            "cache_ticker_count": 4,
            "usable_for_waveform_memory": True,
            "source_health": {
                "kraken": {"active": True, "fresh": True, "ticker_count": 1},
                "alpaca": {"active": True, "fresh": True, "ticker_count": 1},
                "capital": {"active": True, "fresh": True, "ticker_count": 1},
            },
        },
    )
    _seed_history(tmp_path)

    report = build_global_financial_coverage_map(tmp_path)

    assert report["summary"]["active_live_source_count"] == 4
    assert report["summary"]["live_ticker_count"] == 4
    assert {item["name"] for item in report["live_stream"]["exchange_counts"]} >= {"binance", "kraken", "alpaca", "capital"}


def test_write_global_financial_coverage_map_outputs_files(tmp_path):
    report = build_global_financial_coverage_map(tmp_path)
    output_json, output_md, public_json = write_global_financial_coverage_map(
        report,
        tmp_path / "docs" / "audits" / "aureon_global_financial_coverage_map.json",
        tmp_path / "docs" / "audits" / "aureon_global_financial_coverage_map.md",
        tmp_path / "frontend" / "public" / "aureon_global_financial_coverage_map.json",
    )

    assert output_json.exists()
    assert output_md.exists()
    assert public_json.exists()
    assert "Aureon Global Financial Coverage Map" in output_md.read_text(encoding="utf-8")
