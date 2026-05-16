import json
from pathlib import Path

from aureon.autonomous import aureon_ollama_cognitive_bridge as bridge


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _seed_cognitive_sources(root: Path) -> None:
    _write(root / "state/aureon_hnc_cognitive_proof.json", {"status": "passing"})
    _write(
        root / "docs/audits/aureon_harmonic_affect_state.json",
        {"schema_version": "test", "status": "harmonic_affect_state_ready", "summary": {}},
    )
    _write(
        root / "docs/audits/aureon_cognitive_trade_evidence.json",
        {"schema_version": "test", "status": "cognitive_trade_evidence_ready", "summary": {}},
    )
    _write(root / "state/aureon_expression_profile.json", {"status": "present"})
    _write(root / "state/aureon_voice_last_run.json", {"status": "present"})
    _write(
        root / "frontend/public/aureon_agent_creative_process_guardian.json",
        {
            "schema_version": "test",
            "status": "agent_creative_process_guardian_ready",
            "summary": {
                "hnc_auris_ready": True,
                "metacognitive_ready": True,
                "who_what_where_when_how_act_ready": True,
            },
        },
    )


def test_ollama_cognitive_bridge_ready_writes_evidence(tmp_path, monkeypatch):
    _seed_cognitive_sources(tmp_path)
    monkeypatch.setenv("AUREON_LLM_MODEL", "qwen2.5:0.5b")
    monkeypatch.setenv("AUREON_LLM_API_KEY", "SECRET_SHOULD_NOT_LEAK")
    monkeypatch.setattr(
        bridge,
        "_ollama_snapshot",
        lambda: {
            "reachable": True,
            "base_url": "http://localhost:11434",
            "chat_model": "qwen2.5:0.5b",
            "models": ["qwen2.5:0.5b"],
            "running": ["qwen2.5:0.5b"],
            "version": "test",
        },
    )

    report = bridge.build_and_write_ollama_cognitive_bridge(root=tmp_path)

    assert report["ok"] is True
    assert report["status"] == "ollama_cognitive_bridge_ready"
    assert report["summary"]["ollama_reachable"] is True
    assert report["summary"]["hnc_auris_ready"] is True
    assert report["model_resolution"]["resolved_model"] == "qwen2.5:0.5b"
    assert report["who_what_where_when_how_act"]["who"]["language_worker"] == "Ollama Language Worker"
    assert (tmp_path / "frontend/public/aureon_ollama_cognitive_bridge.json").exists()
    assert "SECRET_SHOULD_NOT_LEAK" not in json.dumps(report)


def test_ollama_cognitive_bridge_blocks_when_ollama_offline(tmp_path, monkeypatch):
    _seed_cognitive_sources(tmp_path)
    monkeypatch.setattr(
        bridge,
        "_ollama_snapshot",
        lambda: {
            "reachable": False,
            "base_url": "http://localhost:11434",
            "chat_model": "llama3",
            "models": [],
            "running": [],
        },
    )

    report = bridge.build_and_write_ollama_cognitive_bridge(root=tmp_path)

    assert report["ok"] is False
    assert report["status"] == "ollama_cognitive_bridge_waiting_for_ollama"
    assert report["summary"]["blocking_check_count"] >= 1
    assert any(action["id"] == "start_ollama" for action in report["next_actions"])
