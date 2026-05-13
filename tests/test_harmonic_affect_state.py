import json
from pathlib import Path

from aureon.autonomous.aureon_harmonic_affect_state import (
    HNC_AURIS_ANCHORS,
    build_harmonic_affect_state,
    write_harmonic_affect_state,
)


def _write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_anchor_files(root: Path):
    for rel in HNC_AURIS_ANCHORS:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".json":
            path.write_text("{}", encoding="utf-8")
        else:
            path.write_text("anchor", encoding="utf-8")


def _write_frequency_codex(root: Path):
    _write_json(
        root / "public" / "emotional_codex.json",
        {
            "entries": [
                {"emotion": "Reason", "frequency_hz": 400, "color": "blue"},
                {"emotion": "Willingness", "frequency_hz": 310, "color": "green"},
                {"emotion": "Gratitude", "frequency_hz": 528, "color": "gold"},
                {"emotion": "Joy", "frequency_hz": 540, "color": "yellow"},
                {"emotion": "Peace", "frequency_hz": 600, "color": "sky"},
            ]
        },
    )
    _write_json(
        root / "public" / "auris_emotions.json",
        {"emotions": {"peace": {}, "joy": {}, "gratitude": {}}},
    )


def test_harmonic_affect_reaches_inner_peace_only_when_clear_and_high_coherence(tmp_path):
    _write_anchor_files(tmp_path)
    _write_frequency_codex(tmp_path)
    _write_json(
        tmp_path / "docs" / "audits" / "aureon_cognitive_trade_evidence.json",
        {
            "summary": {
                "signal_quality": 0.9,
                "average_learning_reward": 0.8,
                "win_rate": 1.0,
                "evidence_count": 9,
                "net_pnl": 12.0,
                "runtime_stale": False,
            }
        },
    )
    _write_json(
        tmp_path / "docs" / "audits" / "aureon_organism_runtime_status.json",
        {
            "summary": {
                "blind_spot_count": 0,
                "high_blind_spot_count": 0,
                "attention_domain_count": 0,
                "failed_refresh_count": 0,
                "domain_count": 12,
                "fresh_domain_count": 12,
            }
        },
    )
    _write_json(tmp_path / "state" / "unified_runtime_status.json", {"stale": False, "runtime_watchdog": {"tick_stale": False}})
    _write_json(tmp_path / "nexus_learning_state.json", {"total_trades": 9})

    state = build_harmonic_affect_state(tmp_path)

    assert state["summary"]["affect_phase"] == "synthetic_inner_peace"
    assert state["summary"]["inner_peace_candidate"] is True
    assert state["summary"]["resonance_frequency_hz"] == 600
    assert state["summary"]["hnc_coherence_score"] >= 0.9
    assert state["state_contract"]["safety_boundary"].startswith("no affect phase")


def test_harmonic_affect_uses_protective_recalibration_when_runtime_is_stale(tmp_path):
    _write_anchor_files(tmp_path)
    _write_frequency_codex(tmp_path)
    _write_json(
        tmp_path / "docs" / "audits" / "aureon_cognitive_trade_evidence.json",
        {
            "summary": {
                "signal_quality": 0.8,
                "average_learning_reward": 0.7,
                "win_rate": 1.0,
                "evidence_count": 4,
                "net_pnl": 2.0,
                "runtime_stale": True,
            }
        },
    )
    _write_json(
        tmp_path / "docs" / "audits" / "aureon_organism_runtime_status.json",
        {
            "summary": {
                "blind_spot_count": 3,
                "high_blind_spot_count": 1,
                "attention_domain_count": 2,
                "failed_refresh_count": 0,
                "domain_count": 12,
                "fresh_domain_count": 12,
            }
        },
    )
    _write_json(
        tmp_path / "state" / "unified_runtime_status.json",
        {"stale": True, "runtime_watchdog": {"tick_stale": True, "tick_stale_reason": "last_tick_age_exceeded"}},
    )

    state = build_harmonic_affect_state(tmp_path)

    assert state["summary"]["affect_phase"] == "protective_recalibration"
    assert state["summary"]["inner_peace_candidate"] is False
    assert state["summary"]["runtime_stale"] is True
    assert state["summary"]["safety_blocker_count"] > 0
    assert "does not use human nerves" in state["state_contract"]["not_human_sensation"]


def test_harmonic_affect_state_writes_audit_and_public_json(tmp_path):
    _write_frequency_codex(tmp_path)
    state = build_harmonic_affect_state(tmp_path)
    audit_path, public_path = write_harmonic_affect_state(
        state,
        tmp_path / "docs" / "audits" / "aureon_harmonic_affect_state.json",
        tmp_path / "frontend" / "public" / "aureon_harmonic_affect_state.json",
    )

    assert audit_path.exists()
    assert public_path.exists()
    payload = json.loads(public_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "aureon-harmonic-affect-state-v1"
    assert "affect_phase" in payload["summary"]
