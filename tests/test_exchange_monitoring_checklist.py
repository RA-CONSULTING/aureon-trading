import json
from pathlib import Path

from aureon.autonomous.aureon_exchange_monitoring_checklist import (
    SCHEMA_VERSION,
    build_exchange_monitoring_checklist,
    write_exchange_monitoring_checklist,
)


def _write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _runtime_payload(*, stale: bool = False) -> dict:
    return {
        "stale": stale,
        "stale_reason": "tick_in_progress_stalled" if stale else "",
        "exchanges": {
            "binance_ready": True,
            "kraken_ready": True,
            "alpaca_ready": True,
            "capital_ready": True,
        },
        "runtime_watchdog": {"tick_stale": stale, "tick_stale_reason": "tick_in_progress_stalled" if stale else ""},
        "combined": {"capital_equity_gbp": 266.22, "kraken_equity": 123.45},
        "live_stream_cache": {
            "fresh": not stale,
            "usable_for_decision": not stale,
            "exchange_source_health": {
                "binance": {"active": True, "fresh": not stale, "ticker_count": 2, "generated_at": 1778834777.0},
                "kraken": {"active": True, "fresh": not stale, "ticker_count": 1, "generated_at": 1778834778.0},
            },
        },
        "exchange_action_plan": {
            "venues": {
                "binance_spot": {"ready": True},
                "kraken_spot": {"ready": True},
                "kraken_margin": {"ready": True},
                "capital_cfd": {"ready": True},
            }
        },
    }


def _stream_cache_payload() -> dict:
    return {
        "source": "multi_exchange_stream_cache",
        "generated_at": 1778834779.0,
        "source_health": {
            "binance": {"active": True, "fresh": True, "ticker_count": 2, "generated_at": 1778834777.0},
            "kraken": {"active": True, "fresh": True, "ticker_count": 1, "generated_at": 1778834778.0},
            "alpaca": {"active": False, "fresh": False, "ticker_count": 0, "reason": "missing_credentials"},
        },
        "ticker_cache": {
            "binance:BTCUSDT": {"exchange": "binance", "price": 100.0},
            "binance:ETHUSDT": {"exchange": "binance", "price": 10.0},
            "kraken:XBTUSD": {"exchange": "kraken", "price": 100.0},
        },
    }


def test_exchange_monitoring_checklist_marks_monitored_and_missing_sources(tmp_path):
    _write_json(tmp_path / "state" / "unified_runtime_status.json", _runtime_payload(stale=False))
    _write_json(tmp_path / "ws_cache" / "ws_prices.json", _stream_cache_payload())
    _write_json(
        tmp_path / "state" / "aureon_live_waveform_recorder.json",
        {
            "inserted_bar_count": 3,
            "usable_for_waveform_memory": True,
            "source_health": {
                "binance": {"active": True, "fresh": True},
                "kraken": {"active": True, "fresh": True},
            },
        },
    )

    report = build_exchange_monitoring_checklist(tmp_path)
    rows = {row["exchange"]: row for row in report["rows"]}

    assert report["schema_version"] == SCHEMA_VERSION
    assert report["summary"]["connected_exchange_count"] == 4
    assert report["summary"]["fresh_exchange_count"] == 2
    assert rows["binance"]["cache_fresh"] is True
    assert rows["binance"]["feeds_decision_logic"] is True
    assert rows["binance"]["ticker_count"] == 2
    assert "fresh_tickers" in rows["binance"]["monitored_now"]
    assert rows["kraken"]["action_plan_venue_count"] == 2
    assert rows["kraken"]["waveform_history_active"] is True
    assert rows["alpaca"]["cache_active"] is False
    assert "missing_credentials" in rows["alpaca"]["missing"]
    assert "no_live_cache_source_health" in rows["capital"]["missing"]


def test_stale_runtime_keeps_connected_but_blocks_decision_use(tmp_path):
    _write_json(tmp_path / "state" / "unified_runtime_status.json", _runtime_payload(stale=True))
    _write_json(tmp_path / "ws_cache" / "ws_prices.json", _stream_cache_payload())

    report = build_exchange_monitoring_checklist(tmp_path)
    rows = {row["exchange"]: row for row in report["rows"]}

    assert report["status"] == "exchange_monitoring_connected_guarded_runtime_stale"
    assert report["summary"]["runtime_stale"] is True
    assert rows["binance"]["connected"] is True
    assert rows["binance"]["feeds_decision_logic"] is False
    assert "runtime_stale_blocks_fresh_live_decision_use" in rows["binance"]["missing"]


def test_exchange_monitoring_uses_waveform_recorder_source_health_as_backup(tmp_path):
    runtime = _runtime_payload(stale=False)
    runtime["exchange_action_plan"]["venues"]["capital_cfd"] = {"ready": True}
    _write_json(tmp_path / "state" / "unified_runtime_status.json", runtime)
    _write_json(
        tmp_path / "ws_cache" / "ws_prices.json",
        {
            "source": "multi_exchange_stream_cache",
            "source_health": {},
            "ticker_cache": {"capital:AAPLUSD": {"exchange": "capital", "price": 100.0}},
        },
    )
    _write_json(
        tmp_path / "state" / "aureon_live_waveform_recorder.json",
        {
            "inserted_bar_count": 1,
            "usable_for_waveform_memory": True,
            "source_health": {"capital": {"active": True, "fresh": True, "ticker_count": 1, "generated_at": 1778834779.0}},
        },
    )

    report = build_exchange_monitoring_checklist(tmp_path)
    rows = {row["exchange"]: row for row in report["rows"]}

    assert rows["capital"]["cache_present"] is True
    assert rows["capital"]["cache_fresh"] is True
    assert rows["capital"]["ticker_count"] == 1
    assert "no_live_cache_source_health" not in rows["capital"]["missing"]


def test_write_exchange_monitoring_checklist_outputs_json_md_and_public_json(tmp_path):
    report = build_exchange_monitoring_checklist(tmp_path)
    output_json, output_md, public_json = write_exchange_monitoring_checklist(
        report,
        tmp_path / "docs" / "audits" / "aureon_exchange_monitoring_checklist.json",
        tmp_path / "docs" / "audits" / "aureon_exchange_monitoring_checklist.md",
        tmp_path / "frontend" / "public" / "aureon_exchange_monitoring_checklist.json",
    )

    assert output_json.exists()
    assert output_md.exists()
    assert public_json.exists()
    assert "Aureon Exchange Monitoring Checklist" in output_md.read_text(encoding="utf-8")
