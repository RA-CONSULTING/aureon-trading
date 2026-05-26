import json
from pathlib import Path

from aureon.autonomous import aureon_metacognitive_systems_expansion as expansion


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _fixture_root(tmp_path: Path) -> Path:
    for spec in expansion.SYSTEM_SPECS:
        source = "\n".join(str(symbol) for symbol in spec["required_symbols"])
        _write(tmp_path / spec["path"], source)

    _write(
        tmp_path / "docs/research/hnc_1000_word_autonomous_essay.md",
        "# Harmonic Nexus Core\n\n## Essay\n\n" + ("coherence " * 1000),
    )
    _write(
        tmp_path / "frontend/public/aureon_hnc_essay_benchmark.json",
        json.dumps(
            {
                "status": "hnc_essay_benchmark_certified",
                "summary": {"essay_word_count": 1000},
            }
        ),
    )
    _write(
        tmp_path / "frontend/public/aureon_research_metacognition.json",
        json.dumps(
            {
                "status": "research_metacognition_active",
                "summary": {"understood_concept_count": 8, "ready_route_count": 7},
                "concept_rows": [
                    {"concept_id": f"concept_{idx}", "label": f"Concept {idx}", "status": "understood"}
                    for idx in range(8)
                ],
                "organism_route_rows": [
                    {"route_id": f"route_{idx}", "system": f"System {idx}", "ready": True}
                    for idx in range(7)
                ],
            }
        ),
    )
    _write(
        tmp_path / "frontend/public/aureon_online_research_cinema.json",
        json.dumps({"status": "online_research_cinema_ready", "summary": {"source_count": 5}}),
    )
    _write(tmp_path / "aureon/generated/research_cinema/harmonic_nexus_score_model.py", "def score(): return 1\n")
    _write(tmp_path / "tests/generated/test_harmonic_nexus_score_model.py", "def test_score(): assert True\n")
    _write(tmp_path / "state/aureon_swarm_search_fabric_events.jsonl", "{}\n")
    return tmp_path


def test_metacognitive_systems_expansion_routes_all_present_systems(tmp_path, monkeypatch):
    monkeypatch.setattr(
        expansion,
        "publish_search_event",
        lambda **kwargs: {"trace_id": "trace_fixture", "query_id": "query_fixture"},
    )
    root = _fixture_root(tmp_path)

    report = expansion.build_metacognitive_systems_expansion(root=root)

    assert report["status"] == "metacognitive_systems_expanded"
    assert report["summary"]["wired_metacognitive_system_count"] == len(expansion.SYSTEM_SPECS)
    assert report["summary"]["ready_route_count"] == len(expansion.SYSTEM_SPECS)
    assert report["summary"]["present_artifact_count"] == len(expansion.ARTIFACT_SPECS)
    assert report["summary"]["hnc_essay_word_count"] == 1000
    assert report["summary"]["no_external_mutation"] is True
    assert (root / "frontend/public/aureon_metacognitive_systems_expansion.json").exists()
    assert all(row["wired"] for row in report["system_rows"])
    assert all(row["ready"] for row in report["route_rows"])


def test_metacognitive_systems_expansion_reports_missing_symbols(tmp_path, monkeypatch):
    monkeypatch.setattr(
        expansion,
        "publish_search_event",
        lambda **kwargs: {"trace_id": "trace_fixture", "query_id": "query_fixture"},
    )
    root = _fixture_root(tmp_path)
    _write(root / "aureon/core/aureon_self_introspection.py", "class SelfIntrospection\n")

    report = expansion.build_metacognitive_systems_expansion(root=root)
    row = next(item for item in report["system_rows"] if item["id"] == "self_introspection")

    assert report["status"] == "metacognitive_systems_attention"
    assert row["wired"] is False
    assert "def scan" in row["missing_symbols"]
    assert report["summary"]["ready_route_count"] == len(expansion.SYSTEM_SPECS) - 1
