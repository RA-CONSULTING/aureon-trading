import json
from pathlib import Path

from aureon.autonomous.aureon_cognitive_trade_evidence import (
    build_cognitive_trade_state,
    reward_from_trade,
    write_cognitive_trade_state,
)


def _write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_profitable_fresh_trade_becomes_reinforcement_signal(monkeypatch):
    monkeypatch.setenv("AUREON_COGNITIVE_REWARD_PNL_SCALE_GBP", "5")
    reward = reward_from_trade(
        {
            "symbol": "BTCUSD",
            "net_pnl": 4.0,
            "gross_pnl": 4.2,
            "total_fees": 0.1,
            "hold_seconds": 30,
        },
        {
            "trading_ready": True,
            "data_ready": True,
            "stale": False,
            "runtime_watchdog": {"tick_stale": False},
        },
    )

    assert reward["outcome"] == "win"
    assert reward["operational_affect_label"] == "gratitude_reinforcement"
    assert reward["learning_reward"] >= 0.65
    assert "not a sentience" in reward["affect_note"]
    assert "without_raising_risk_limits" in reward["next_action"]


def test_stale_runtime_turns_trade_evidence_into_recovery_mode(tmp_path):
    _write_json(
        tmp_path / "state" / "unified_runtime_status.json",
        {
            "trading_ready": True,
            "data_ready": True,
            "stale": True,
            "stale_reason": "tick_in_progress_stalled",
            "combined": {"open_positions": 2},
            "runtime_watchdog": {"tick_stale": True, "tick_stale_reason": "tick_in_progress_stalled"},
        },
    )
    evidence_path = tmp_path / "state" / "cognitive_trade_evidence.jsonl"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(
        json.dumps(
            {
                "schema_version": "aureon-cognitive-trade-evidence-v1",
                "type": "trade_cognitive_reward",
                "event_time": "2026-05-12T10:00:00+00:00",
                "source": "test",
                "trade": {"symbol": "BTCUSD"},
                "reward": {
                    "net_pnl": 1.25,
                    "learning_reward": 0.8,
                    "outcome": "win",
                    "operational_affect_label": "gratitude_reinforcement",
                    "next_action": "increase_weight_for_verified_profitable_signal_without_raising_risk_limits",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    state = build_cognitive_trade_state(tmp_path)

    assert state["summary"]["evidence_count"] == 1
    assert state["summary"]["wins"] == 1
    assert state["summary"]["runtime_stale"] is True
    assert state["summary"]["open_positions"] == 2
    assert state["summary"]["action_mode"] == "learn_and_recover"
    assert state["runtime_watchdog"]["tick_stale_reason"] == "tick_in_progress_stalled"
    assert state["contract"]["loop"][-1] == "repeat"


def test_cognitive_trade_state_writes_audit_and_public_json(tmp_path):
    state = build_cognitive_trade_state(tmp_path)
    audit_path, public_path = write_cognitive_trade_state(
        state,
        tmp_path / "docs" / "audits" / "aureon_cognitive_trade_evidence.json",
        tmp_path / "frontend" / "public" / "aureon_cognitive_trade_evidence.json",
    )

    assert audit_path.exists()
    assert public_path.exists()
    payload = json.loads(public_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "aureon-cognitive-trade-evidence-v1"
    assert payload["summary"]["action_mode"] == "observe_and_refine"
