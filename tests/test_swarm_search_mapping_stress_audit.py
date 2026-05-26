import json
from pathlib import Path

from aureon.autonomous.aureon_swarm_search_mapping_stress_audit import (
    EXPECTED_PHASES,
    SYSTEM_SPECS,
    build_report,
)
from aureon.search.swarm_search_fabric import build_search_event, publish_search_event
from aureon.search.local_keyword_search import run_keyword_search
from aureon.search import online_research_cinema as cinema
from aureon.search.research_metacognition import build_research_metacognition


def _write(path: Path, text: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _fixture_root(tmp_path: Path) -> Path:
    for spec in SYSTEM_SPECS:
        text = "\n".join(str(symbol) for symbol in spec["required_symbols"])
        _write(tmp_path / str(spec["path"]), text)
    for rel in [
        "state/research_index.json",
        "state/research_readiness_index.json",
        "state/self_questioning_thoughts.jsonl",
        "logs/aureon_thoughts.jsonl",
        "thoughts.jsonl",
        "frontend/public/aureon_complex_build_artifacts/ui_browser_qa_99b733350342.json",
    ]:
        _write(tmp_path / rel, "{}\n")
    return tmp_path


def test_search_event_envelope_has_required_identity_and_boundaries():
    event = build_search_event(
        phase="result_captured",
        source_system="test_search_worker",
        query="capital gold broker docs",
        url="https://example.com/doc",
        result_count=3,
        status="success",
    )

    assert event["event_id"].startswith("search-event-")
    assert event["trace_id"].startswith("search-trace-")
    assert event["query_id"].startswith("query-")
    assert event["capture_id"].startswith("capture-")
    assert event["credential_boundary"] == "no_credentials_read"
    assert event["mutation_scope"] == "no_external_mutation"
    assert event["no_trading_gate_bypass"] is True
    assert event["rate_budget"]["api_budget_source"] == "producer_local_metadata"


def test_audit_reports_wired_waiting_without_fabric_events(tmp_path):
    root = _fixture_root(tmp_path)
    report = build_report(root=root)

    assert report["status"] == "swarm_search_fabric_wired_waiting_for_live_search"
    assert report["summary"]["wired_source_system_count"] == report["summary"]["source_system_count"]
    assert report["summary"]["fabric_event_count"] == 0
    assert report["summary"]["no_new_trading_gate"] is True
    assert any(row["state"] == "waiting_for_first_real_search_event" for row in report["next_actions"])


def test_audit_reports_active_when_real_fabric_events_exist(tmp_path):
    root = _fixture_root(tmp_path)
    trace_id = None
    query_id = None
    for phase in EXPECTED_PHASES:
        event = publish_search_event(
            phase=phase,
            source_system="test_search_worker",
            query="aureon search fabric",
            trace_id=trace_id,
            query_id=query_id,
            result_count=1,
            status="success",
            root=root,
        )
        trace_id = event["trace_id"]
        query_id = event["query_id"]

    report = build_report(root=root)

    assert report["status"] == "swarm_search_fabric_active"
    assert report["summary"]["fabric_event_count"] == len(EXPECTED_PHASES)
    assert report["summary"]["phase_seen_count"] == len(EXPECTED_PHASES)
    assert all(row["seen"] for row in report["phase_rows"])


def test_audit_surfaces_source_symbol_attention(tmp_path):
    root = _fixture_root(tmp_path)
    agent_core = root / "aureon/autonomous/aureon_agent_core.py"
    agent_core.write_text("def web_search\n", encoding="utf-8")

    report = build_report(root=root)
    agent_row = next(row for row in report["source_system_rows"] if row["id"] == "agent_core_search_browser")

    assert report["status"] == "swarm_search_mapping_attention"
    assert agent_row["wired"] is False
    assert "publish_search_event" in agent_row["missing_symbols"]


def test_local_keyword_search_reads_real_test_text_and_surfaces_audit_proof(tmp_path):
    root = _fixture_root(tmp_path)
    test_file = root / "tests/test_keyword_reader.py"
    _write(
        test_file,
        "def test_signal_fabric_keyword_reader():\n"
        "    assert 'signal fabric' == 'signal fabric'\n",
    )

    result = run_keyword_search(
        keyword="signal fabric",
        scope="tests",
        max_results=5,
        repo_root=root,
    )
    report = build_report(root=root)

    assert result["status"] == "keyword_search_completed"
    assert result["summary"]["match_count"] >= 1
    assert result["results"][0]["path"] == "tests/test_keyword_reader.py"
    assert report["summary"]["keyword_search_active"] is True
    assert report["summary"]["latest_keyword_query"] == "signal fabric"
    assert report["keyword_search_rows"]


def test_online_research_cinema_builds_paper_motion_and_audit_proof(tmp_path, monkeypatch):
    root = _fixture_root(tmp_path)

    def fake_fetch(url: str, topic: str) -> dict:
        return {
            "url": url,
            "success": True,
            "status_code": 200,
            "content_type": "text/html",
            "title": "Harmonic validation source",
            "text_hash": "abc123",
            "text_chars": 2048,
            "summary": f"{topic} uses harmonic evidence, source strength, and repeatable validation.",
            "excerpt": "harmonic evidence source strength repeatable validation",
            "round_trip_ms": 12.5,
            "fetched_at": "2026-05-23T00:00:00+00:00",
        }

    monkeypatch.setattr(cinema, "fetch_source", fake_fetch)
    manifest = cinema.build_online_research_cinema(
        topic="Harmonic Nexus Score",
        urls=["https://example.com/hnc-score"],
        max_sources=1,
        root=root,
    )
    report = build_report(root=root)

    assert manifest["status"] == "online_research_cinema_ready"
    assert manifest["summary"]["paper_created"] is True
    assert manifest["summary"]["motion_html_created"] is True
    assert manifest["summary"]["coding_artifacts_created"] is True
    assert manifest["summary"]["metacognition_active"] is True
    assert manifest["summary"]["understanding_published"] is True
    assert manifest["coding_handoff"]["generated_files"]
    assert manifest["metacognition"]["concept_rows"]
    assert report["summary"]["online_research_cinema_active"] is True
    assert report["summary"]["online_research_topic"] == "Harmonic Nexus Score"
    assert report["summary"]["research_coding_artifacts_created"] is True
    assert report["summary"]["research_metacognition_active"] is True
    assert report["summary"]["metacognitive_understanding_published"] is True
    assert report["research_generated_file_rows"]
    assert report["research_metacognition_concept_rows"]
    assert report["research_metacognition_route_rows"]
    assert report["online_research_rows"]
    assert any(row["phase"] == "research_paper_drafted" and row["seen"] for row in report["phase_rows"])
    assert any(row["phase"] == "coding_handoff_ready" and row["seen"] for row in report["phase_rows"])
    assert any(row["phase"] == "metacognition_understanding_published" and row["seen"] for row in report["phase_rows"])


def test_research_metacognition_routes_research_into_organism(tmp_path):
    root = _fixture_root(tmp_path)
    paper_path = root / "docs/research/harmonic_packet.md"
    _write(
        paper_path,
        "Harmonic coherence uses source evidence, repeatable pytest validation, "
        "friction feasibility, contradiction handling, and ThoughtBus Mycelium learning.",
    )
    packet = build_research_metacognition(
        topic="Harmonic Nexus Score",
        source_rows=[
            {
                "title": "Validation source",
                "url": "https://example.com/validation",
                "success": True,
                "summary": "source evidence hash fetched repeatable validation harmonic coherence",
                "excerpt": "signal-to-noise contradiction risk code pytest",
            }
        ],
        paper_path="docs/research/harmonic_packet.md",
        motion_picture={"public_html": "/online_research_cinema/harmonic/motion.html"},
        coding_manifest={
            "module_import": "aureon.generated.research_cinema.harmonic_nexus_score_model",
            "test_command": "python -m pytest tests/generated/test_harmonic_nexus_score_model.py -q",
            "generated_files": [{"path": "aureon/generated/research_cinema/harmonic_nexus_score_model.py", "ok": True}],
        },
        root=root,
    )
    report = build_report(root=root)

    assert packet["status"] == "research_metacognition_active"
    assert packet["summary"]["understood_concept_count"] >= 6
    assert any(row["system"] == "Seer" and row["ready"] for row in packet["organism_route_rows"])
    assert any(row["system"] == "Mycelium" for row in packet["organism_route_rows"])
    assert report["summary"]["research_metacognition_active"] is True
    assert report["research_metacognition_unknown_rows"]
    assert any(row["phase"] == "metacognition_routes_mapped" and row["seen"] for row in report["phase_rows"])
