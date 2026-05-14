import json
from pathlib import Path

from aureon.autonomous.aureon_trading_intelligence_checklist import (
    SCHEMA_VERSION,
    build_trading_intelligence_checklist,
    write_trading_intelligence_checklist,
)


def _write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _runtime_payload(*, stale: bool = False) -> dict:
    stale_reason = "tick_in_progress_stalled" if stale else ""
    return {
        "trading_ready": True,
        "data_ready": True,
        "stale": stale,
        "stale_reason": stale_reason,
        "dashboard_generated_at": "2026-05-14T13:00:00",
        "combined": {"open_positions": 1},
        "runtime_watchdog": {
            "heartbeat_alive": True,
            "tick_stale": stale,
            "tick_stale_reason": stale_reason,
            "heartbeat_at": "2026-05-14T13:00:01",
        },
        "api_governor": {"policy": "execution_and_positions_first_quotes_cached_and_budgeted"},
        "exchange_action_plan": {
            "generated_at": "2026-05-14T13:00:02",
            "mode": "runtime_gated_order_intent",
            "venue_count": 2,
            "ready_venue_count": 2,
            "runtime_clearances": [],
            "selection_process": {"mode": "profit_velocity_ranked_live_shadow_selection"},
            "model_coverage": {"available_model_count": 4},
            "venues": {
                "kraken_spot": {
                    "ready": True,
                    "top_candidates": [
                        {
                            "symbol": "BTCUSD",
                            "side": "BUY",
                            "confidence": 0.8,
                            "profit_velocity_score": 0.7,
                            "model_signal": {"direction": "BUY", "confidence": 0.78},
                        }
                    ],
                }
            },
            "intelligence_mesh": {
                "generated_at": "2026-05-14T13:00:02",
                "capability_count": 4,
                "present_count": 4,
                "active_this_cycle_count": 4,
                "direct_live_count": 3,
                "active_direct_live_count": 3,
                "selection_mesh_score": 1.0,
                "capabilities": [
                    {
                        "name": "LiveExchangeFeeds",
                        "facet": "live_market_data",
                        "wire": "direct_live_signal",
                        "path": "aureon/data_feeds/unified_market_cache.py",
                        "present": True,
                        "active_this_cycle": True,
                    },
                    {
                        "name": "HNCMasterProtocol",
                        "facet": "hnc_harmonic",
                        "wire": "hnc_proof",
                        "path": "aureon/strategies/hnc_master_protocol.py",
                        "present": True,
                        "active_this_cycle": True,
                    },
                    {
                        "name": "PhantomSignalFilter",
                        "facet": "noise_filter",
                        "wire": "mesh_context",
                        "path": "aureon/scanners/aureon_phantom_signal_filter.py",
                        "present": True,
                        "active_this_cycle": True,
                    },
                    {
                        "name": "MicroMomentumGoal",
                        "facet": "fast_profit_eta",
                        "wire": "profit_context",
                        "path": "aureon/conversion/aureon_micro_momentum_goal.py",
                        "present": True,
                        "active_this_cycle": True,
                    },
                ],
            },
        },
        "shadow_trading": {
            "generated_at": "2026-05-14T13:00:03",
            "enabled": True,
            "shadow_opened_count": 2,
            "active_shadow_count": 2,
        },
        "hnc_cognitive_proof": {
            "generated_at": "2026-05-14T13:00:04",
            "status": "passing",
            "passed": True,
            "passed_count": 8,
            "step_count": 8,
            "auris_nodes": {"evaluated": True, "node_count": 9, "coherence": 0.75},
        },
    }


def _by_name(report: dict, name: str) -> dict:
    return next(row for row in report["rows"] if row["system"] == name)


def test_fresh_runtime_marks_intelligence_as_fresh_usable_and_decision_fed(tmp_path):
    _write_json(tmp_path / "state" / "unified_runtime_status.json", _runtime_payload(stale=False))

    report = build_trading_intelligence_checklist(tmp_path)

    assert report["schema_version"] == SCHEMA_VERSION
    assert report["summary"]["runtime_fresh"] is True
    assert report["summary"]["fresh_usable_count"] > 0
    assert _by_name(report, "LiveExchangeFeeds")["usable_for_decision"] is True
    assert _by_name(report, "HNCMasterProtocol")["downstream_stage"] == "hnc_proof"
    assert _by_name(report, "AurisNodes")["downstream_stage"] == "auris_state"
    assert _by_name(report, "PhantomSignalFilter")["category"] == "counter_intelligence_validation"
    assert _by_name(report, "ProfitVelocityRanker")["fed_to_decision_logic"] is True


def test_stale_runtime_keeps_wiring_but_blocks_fresh_usable_decision(tmp_path):
    _write_json(tmp_path / "state" / "unified_runtime_status.json", _runtime_payload(stale=True))

    report = build_trading_intelligence_checklist(tmp_path)
    live = _by_name(report, "LiveExchangeFeeds")

    assert report["summary"]["runtime_stale"] is True
    assert report["summary"]["stale_reason"] == "tick_in_progress_stalled"
    assert live["fed_to_decision_logic"] is True
    assert live["fresh"] is False
    assert live["usable_for_decision"] is False
    assert "tick_in_progress_stalled" in live["blocker"]


def test_missing_runtime_degrades_without_claiming_success(tmp_path):
    report = build_trading_intelligence_checklist(tmp_path)

    assert report["status"] == "runtime_data_not_ready"
    assert report["summary"]["data_ready"] is False
    assert report["summary"]["fresh_usable_count"] == 0
    assert report["summary"]["top_blockers"]


def test_checklist_writes_json_markdown_and_public_json(tmp_path):
    _write_json(tmp_path / "state" / "unified_runtime_status.json", _runtime_payload(stale=False))
    report = build_trading_intelligence_checklist(tmp_path)

    audit_json, audit_md, public_json = write_trading_intelligence_checklist(
        report,
        tmp_path / "docs" / "audits" / "aureon_trading_intelligence_checklist.json",
        tmp_path / "docs" / "audits" / "aureon_trading_intelligence_checklist.md",
        tmp_path / "frontend" / "public" / "aureon_trading_intelligence_checklist.json",
    )

    assert audit_json.exists()
    assert audit_md.exists()
    assert public_json.exists()
    assert json.loads(public_json.read_text(encoding="utf-8"))["schema_version"] == SCHEMA_VERSION
    assert "Aureon Trading Intelligence Checklist" in audit_md.read_text(encoding="utf-8")
