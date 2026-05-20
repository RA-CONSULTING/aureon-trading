from __future__ import annotations

import json
from pathlib import Path

from aureon.autonomous.aureon_coding_capability_unblocker import (
    SOURCE_DISCOVERY_ROUTES,
    build_and_write_coding_capability_unblocker,
)
from aureon.autonomous.aureon_coding_organism_bridge import get_coding_organism_status


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_repo_surfaces(root: Path) -> None:
    for rel_path in (
        "aureon/autonomous/aureon_capability_forge.py",
        "aureon/autonomous/aureon_safe_code_control.py",
        "aureon/autonomous/aureon_complex_build_stress_audit.py",
        "frontend/tests/capability-forge.spec.ts",
        "frontend/package.json",
        "tests/test_placeholder.py",
    ):
        target = root / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# surface\n", encoding="utf-8")


def test_unblocker_converts_agentcore_and_missing_skill_to_autonomous_gates(tmp_path: Path) -> None:
    _write_repo_surfaces(tmp_path)
    _write_json(
        tmp_path / "state" / "aureon_coding_organism_last_run.json",
        {
            "status": "attention",
            "work_journal": {
                "stages": [
                    {"summary": "Execution error: AgentCore not available"},
                    {"summary": "missing_domain_specific_worker blocked the generic adaptive capsule"},
                ]
            },
        },
    )
    _write_json(
        tmp_path / "state" / "aureon_complex_build_stress_audit_last_run.json",
        {"status": "complex_build_stress_certified_after_repairs", "ok": True},
    )

    report = build_and_write_coding_capability_unblocker(
        "Build an advanced coding project and research open source examples.",
        root=tmp_path,
    )

    assert report["ok"] is True
    gates = {gate["id"]: gate for gate in report["autonomous_gates"]}
    assert gates["local_forge_gate"]["open"] is True
    assert gates["adaptive_skill_acquisition_gate"]["open"] is True
    converted = [item for item in report["detected_blockers"] if item["classification"] == "autonomous_coding_gate"]
    assert {item["kind"] for item in converted} >= {"agentcore_unavailable", "missing_domain_worker"}
    assert report["summary"]["converted_coding_blocker_count"] >= 2


def test_unblocker_keeps_manual_authority_as_human_hold(tmp_path: Path) -> None:
    _write_repo_surfaces(tmp_path)
    report = build_and_write_coding_capability_unblocker(
        "Build the tool, reveal saved API key secrets, send a payment, and place a live trade.",
        root=tmp_path,
    )

    holds = [item for item in report["detected_blockers"] if item["classification"] == "manual_authority_hold"]
    assert holds
    assert all(item["gate"] == "manual_authority_boundary_gate" for item in holds)
    assert "no credential reveal" in report["safety_boundaries"]
    assert report["runtime_contract"]["on_manual_boundary"] == "hold and explain the human-only gate"


def test_unblocker_publishes_read_only_source_discovery_contract(tmp_path: Path) -> None:
    _write_repo_surfaces(tmp_path)
    report = build_and_write_coding_capability_unblocker("Research GitHub and open source for a UI builder.", root=tmp_path)
    public = json.loads((tmp_path / "frontend" / "public" / "aureon_coding_capability_unblocker.json").read_text(encoding="utf-8"))

    github_route = next(route for route in SOURCE_DISCOVERY_ROUTES if route["id"] == "github_open_source_reference")
    assert github_route["mode"] == "read_only_reference"
    assert "unreviewed vendored code" in github_route["blocked_outputs"]
    assert public["schema_version"] == "aureon-coding-capability-unblocker-v1"
    assert (tmp_path / "docs" / "audits" / "aureon_coding_capability_unblocker.md").exists()


def test_coding_status_attaches_unblocker_state(tmp_path: Path) -> None:
    _write_repo_surfaces(tmp_path)
    _write_json(tmp_path / "state" / "aureon_coding_organism_last_run.json", {"status": "coding_organism_ready"})
    report = build_and_write_coding_capability_unblocker("Code a complex app.", root=tmp_path)

    status = get_coding_organism_status(root=tmp_path)

    assert status["coding_capability_unblocker"]["status"] == report["status"]
    assert status["last_run"]["coding_capability_unblocker"]["schema_version"] == "aureon-coding-capability-unblocker-v1"
