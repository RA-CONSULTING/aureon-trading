import json
import time
from pathlib import Path

from aureon.autonomous.aureon_data_ocean import (
    SOURCE_REGISTRY,
    build_data_ocean_status,
    evaluate_data_ocean_sources,
    write_data_ocean_status,
)
from aureon.core.aureon_global_history_db import connect, insert_market_bar


def _write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _seed_yfinance_history(root: Path):
    db_path = root / "state" / "aureon_global_history.sqlite"
    conn = connect(str(db_path))
    now_ms = int(time.time() * 1000)
    try:
        insert_market_bar(
            conn,
            {
                "provider": "yfinance",
                "venue": "yahoo",
                "symbol_id": "SPY",
                "symbol": "SPY",
                "period_id": "1DAY",
                "time_start_ms": now_ms - 60_000,
                "time_end_ms": now_ms,
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.5,
                "volume": 1000.0,
                "raw_json": "{}",
            },
        )
        conn.commit()
    finally:
        conn.close()


def test_data_ocean_registry_has_expected_source_families():
    source_ids = {source.source_id for source in SOURCE_REGISTRY}

    assert "binance_live" in source_ids
    assert "kraken_live" in source_ids
    assert "alpaca_live" in source_ids
    assert "capital_live" in source_ids
    assert "yfinance_history" in source_ids
    assert "fred_macro" in source_ids
    assert "world_news" in source_ids
    assert "queen_knowledge" in source_ids


def test_data_ocean_marks_live_and_history_sources_usable_without_leaking_secret_values(tmp_path):
    _write_json(tmp_path / "state" / "unified_runtime_status.json", {"stale": False})
    _write_json(
        tmp_path / "ws_cache" / "ws_prices.json",
        {
            "source_health": {
                "binance": {"active": True, "fresh": True, "ticker_count": 10, "generated_at": time.time()}
            }
        },
    )
    _write_json(
        tmp_path / "docs" / "audits" / "aureon_exchange_monitoring_checklist.json",
        {"rows": [{"exchange": "binance", "cache_fresh": True, "ticker_count": 10}]},
    )
    _seed_yfinance_history(tmp_path)

    report = evaluate_data_ocean_sources(
        root=tmp_path,
        env={"BINANCE_API_KEY": "secret-key-value", "BINANCE_API_SECRET": "secret-secret-value"},
    )
    rows = {row["source_id"]: row for row in report["sources"]}
    serialized = json.dumps(report)

    assert rows["binance_live"]["credential_state"] == "configured"
    assert rows["binance_live"]["usable_for_mapping"] is True
    assert rows["yfinance_history"]["credential_state"] == "not_required"
    assert rows["yfinance_history"]["usable_for_mapping"] is True
    assert "secret-key-value" not in serialized
    assert "secret-secret-value" not in serialized


def test_data_ocean_reads_dotenv_configuration_without_serializing_values(tmp_path):
    _write_json(tmp_path / "state" / "unified_runtime_status.json", {"stale": False})
    _write_json(
        tmp_path / "ws_cache" / "ws_prices.json",
        {"source_health": {"kraken": {"active": True, "fresh": True, "ticker_count": 4}}},
    )
    (tmp_path / ".env").write_text(
        "KRAKEN_API_KEY=dotenv-key-value\nKRAKEN_API_SECRET=dotenv-secret-value\n",
        encoding="utf-8",
    )

    report = evaluate_data_ocean_sources(root=tmp_path)
    rows = {row["source_id"]: row for row in report["sources"]}
    serialized = json.dumps(report)

    assert rows["kraken_live"]["credential_state"] == "configured"
    assert rows["kraken_live"]["usable_for_mapping"] is True
    assert "dotenv-key-value" not in serialized
    assert "dotenv-secret-value" not in serialized


def test_data_ocean_explains_missing_credentials_and_runtime_stale(tmp_path):
    _write_json(tmp_path / "state" / "unified_runtime_status.json", {"stale": True})
    _write_json(
        tmp_path / "ws_cache" / "ws_prices.json",
        {"source_health": {"kraken": {"active": True, "fresh": True, "ticker_count": 5}}},
    )

    report = evaluate_data_ocean_sources(root=tmp_path, env={})
    rows = {row["source_id"]: row for row in report["sources"]}

    assert rows["kraken_live"]["credential_state"] == "missing"
    assert rows["kraken_live"]["governor_action"] == "credential_required"
    assert rows["fred_macro"]["reason"] == "required_credentials_missing"
    assert report["summary"]["credential_missing_count"] > 0


def test_data_ocean_treats_provider_unavailable_attempt_as_accounted_not_reachable(tmp_path):
    _write_json(tmp_path / "state" / "aureon_data_ocean_ingest_attempts.json", {
        "yfinance_history": {
            "status": "provider_unavailable_or_no_data",
            "reason": "provider_returned_no_usable_rows",
            "inserted": 0,
        }
    })

    report = evaluate_data_ocean_sources(root=tmp_path, env={})
    rows = {row["source_id"]: row for row in report["sources"]}

    assert rows["yfinance_history"]["configured_reachable"] is False
    assert rows["yfinance_history"]["governor_action"] == "provider_unavailable"
    assert rows["yfinance_history"]["reason"] == "provider_returned_no_usable_rows"


def test_data_ocean_treats_live_rate_limit_as_accounted_not_reachable(tmp_path):
    _write_json(tmp_path / "state" / "unified_runtime_status.json", {"stale": False})
    _write_json(
        tmp_path / "ws_cache" / "ws_prices.json",
        {
            "source_health": {
                "capital": {
                    "active": False,
                    "fresh": False,
                    "ticker_count": 0,
                    "reason": "rate_limited",
                }
            }
        },
    )

    report = evaluate_data_ocean_sources(root=tmp_path, env={"CAPITAL_API_KEY": "k", "CAPITAL_IDENTIFIER": "i", "CAPITAL_PASSWORD": "p"})
    rows = {row["source_id"]: row for row in report["sources"]}

    assert rows["capital_live"]["configured_reachable"] is False
    assert rows["capital_live"]["availability_state"] == "rate_limited"
    assert rows["capital_live"]["governor_action"] == "rate_limit_backoff"
    assert rows["capital_live"]["reason"] == "rate_limited"


def test_write_data_ocean_status_outputs_state_and_public_json(tmp_path):
    report = build_data_ocean_status(tmp_path, dry_run=True)
    output_json, public_json = write_data_ocean_status(
        report,
        tmp_path / "state" / "aureon_data_ocean_status.json",
        tmp_path / "frontend" / "public" / "aureon_data_ocean_status.json",
    )

    assert output_json.exists()
    assert public_json.exists()
