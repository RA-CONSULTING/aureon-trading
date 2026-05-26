import json
from pathlib import Path

from aureon.autonomous.aureon_hnc_essay_benchmark import (
    build_hnc_essay_benchmark,
    count_words,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _fixture_root(tmp_path: Path) -> Path:
    _write(
        tmp_path / "docs/HNC_UNIFIED_WHITE_PAPER.md",
        (
            "The Harmonic Nexus Core defines the Master Formula, harmonic coherence, "
            "Aureon Trading System, Queen AI, Seer, Lyra, Auris, ThoughtBus, Mycelium, "
            "validation, source strength, repeatability, friction feasibility, and contradiction handling. "
        )
        * 8,
    )
    _write(
        tmp_path / "docs/research/HNC_WHITEPAPER_VERIFIED.md",
        (
            "HNC verification requires coherence checks, validation rows, falsification, "
            "source evidence, and repeatable tests. "
        )
        * 8,
    )
    _write(
        tmp_path / "docs/research/AUREON_WHITE_PAPER_RESEARCH_HUB.md",
        (
            "The research hub links Harmonic Nexus Core evidence to digital immune systems, "
            "dormancy, metacognition, and outcome calibration. "
        )
        * 8,
    )
    metacognition = {
        "status": "research_metacognition_active",
        "summary": {"understood_concept_count": 8, "ready_route_count": 7},
        "concept_rows": [
            {"label": "Source strength", "status": "understood"},
            {"label": "Harmonic coherence", "status": "understood"},
            {"label": "Repeatability", "status": "understood"},
            {"label": "Friction feasibility", "status": "understood"},
            {"label": "Contradiction handling", "status": "understood"},
            {"label": "Coding actionability", "status": "understood"},
            {"label": "Visual replay context", "status": "understood"},
            {"label": "Learning memory", "status": "understood"},
        ],
        "organism_route_rows": [
            {"system": "Seer", "ready": True},
            {"system": "Lyra", "ready": True},
            {"system": "HNC/Auris", "ready": True},
            {"system": "ThoughtBus", "ready": True},
            {"system": "Mycelium", "ready": True},
            {"system": "Code Architect", "ready": True},
            {"system": "Test Runner", "ready": True},
        ],
    }
    research_cinema = {
        "status": "online_research_cinema_ready",
        "summary": {"paper_created": True, "coding_artifacts_created": True},
        "source_rows": [{"title": "fixture", "success": True}],
        "coding_handoff": {"generated_files": [{"path": "fixture.py", "ok": True}]},
    }
    _write(tmp_path / "frontend/public/aureon_research_metacognition.json", json.dumps(metacognition))
    _write(tmp_path / "frontend/public/aureon_online_research_cinema.json", json.dumps(research_cinema))
    return tmp_path


def test_hnc_essay_benchmark_generates_exact_1000_word_essay_and_audit(tmp_path):
    root = _fixture_root(tmp_path)
    report = build_hnc_essay_benchmark(root=root, target_words=1000)
    essay_path = root / "docs/research/hnc_1000_word_autonomous_essay.md"
    public_path = root / "frontend/public/aureon_hnc_essay_benchmark.json"

    essay_text = essay_path.read_text(encoding="utf-8")
    essay_body = essay_text.split("## Essay", 1)[1].split("## Source Evidence Read", 1)[0]

    assert report["status"] == "hnc_essay_benchmark_certified"
    assert report["summary"]["essay_word_count"] == 1000
    assert report["summary"]["exact_word_target_met"] is True
    assert report["summary"]["present_source_artifact_count"] >= 4
    assert count_words(essay_body) == 1000
    assert public_path.exists()
    assert json.loads(public_path.read_text(encoding="utf-8"))["status"] == "hnc_essay_benchmark_certified"
    assert all(row["status"] == "pass" for row in report["capability_rows"])
