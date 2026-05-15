import json
from pathlib import Path

from aureon.autonomous.aureon_exchange_data_capability_matrix import (
    SCHEMA_VERSION,
    build_exchange_data_capability_matrix,
    write_exchange_data_capability_matrix,
)


def _write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_exchange_data_capability_matrix_maps_data_modes_and_budgets(tmp_path):
    _write_json(
        tmp_path / "state" / "unified_runtime_status.json",
        {
            "stale": False,
            "booting": False,
            "trading_ready": True,
            "data_ready": True,
            "exchanges": {
                "binance_ready": True,
                "kraken_ready": True,
                "alpaca_ready": True,
                "capital_ready": True,
            },
            "combined": {
                "capital_equity_gbp": 100.0,
                "kraken_equity": 50.0,
                "positions_by_exchange": {"capital": 1},
            },
            "exchange_action_plan": {
                "venues": {
                    "binance_spot": {"ready": True},
                    "kraken_spot": {"ready": True},
                    "kraken_margin": {"ready": True},
                    "capital_cfd": {"ready": True},
                    "alpaca_equities": {"ready": True},
                }
            },
        },
    )
    _write_json(
        tmp_path / "ws_cache" / "ws_prices.json",
        {
            "source": "multi_exchange_stream_cache",
            "source_health": {
                "binance": {"active": True, "fresh": True, "ticker_count": 10},
                "kraken": {"active": True, "fresh": True, "ticker_count": 4},
                "alpaca": {"active": True, "fresh": True, "ticker_count": 3},
                "capital": {"active": True, "fresh": True, "ticker_count": 2},
            },
            "ticker_cache": {
                "binance:BTCUSDT": {"exchange": "binance"},
                "kraken:XBTUSD": {"exchange": "kraken"},
                "alpaca:AAPL": {"exchange": "alpaca"},
                "capital:US500": {"exchange": "capital"},
            },
        },
    )
    _write_json(
        tmp_path / "state" / "aureon_live_waveform_recorder.json",
        {
            "inserted_bar_count": 4,
            "usable_for_waveform_memory": True,
            "source_health": {
                "binance": {"active": True, "fresh": True},
                "kraken": {"active": True, "fresh": True},
                "alpaca": {"active": True, "fresh": True},
                "capital": {"active": True, "fresh": True},
            },
        },
    )

    report = build_exchange_data_capability_matrix(tmp_path)
    rows = {row["exchange"]: row for row in report["rows"]}

    assert report["schema_version"] == SCHEMA_VERSION
    assert report["summary"]["exchange_count"] == 4
    assert report["summary"]["official_rate_limit_profile_count"] == 4
    assert "crypto_margin" in rows["kraken"]["trading_modes"]
    assert rows["kraken"]["official_rate_limit"]["official_limits"]["private_history_counter_increment"] == 4
    assert rows["capital"]["optimization_policy"]["cash_or_position_active"] is True
    assert rows["binance"]["optimization_policy"]["data_boost_eligible"] is True
    assert any(channel["name"] == "live_ticks" and channel["status"] == "fresh" for channel in rows["binance"]["data_channels"])


def test_exchange_data_capability_matrix_degrades_when_runtime_stale(tmp_path):
    _write_json(
        tmp_path / "state" / "unified_runtime_status.json",
        {
            "stale": True,
            "stale_reason": "tick_in_progress_stalled",
            "exchanges": {"binance_ready": True},
            "runtime_watchdog": {"tick_stale": True, "tick_stale_reason": "tick_in_progress_stalled"},
        },
    )
    _write_json(
        tmp_path / "ws_cache" / "ws_prices.json",
        {"source_health": {"binance": {"active": True, "fresh": True, "ticker_count": 1}}},
    )

    report = build_exchange_data_capability_matrix(tmp_path)
    rows = {row["exchange"]: row for row in report["rows"]}

    assert report["status"] == "exchange_data_capability_matrix_connected_guarded_runtime_stale"
    assert rows["binance"]["current_state"]["connected"] is True
    assert rows["binance"]["current_state"]["decision_fed"] is False
    assert "runtime_stale" in rows["binance"]["gaps"]


def test_write_exchange_data_capability_matrix_outputs_json_md_and_public_json(tmp_path):
    report = build_exchange_data_capability_matrix(tmp_path)
    output_json, output_md, public_json = write_exchange_data_capability_matrix(
        report,
        tmp_path / "docs" / "audits" / "aureon_exchange_data_capability_matrix.json",
        tmp_path / "docs" / "audits" / "aureon_exchange_data_capability_matrix.md",
        tmp_path / "frontend" / "public" / "aureon_exchange_data_capability_matrix.json",
    )

    assert output_json.exists()
    assert output_md.exists()
    assert public_json.exists()
    assert "Aureon Exchange Data Capability Matrix" in output_md.read_text(encoding="utf-8")
