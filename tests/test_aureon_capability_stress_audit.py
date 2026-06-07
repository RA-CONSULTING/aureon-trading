from __future__ import annotations

import json
from pathlib import Path

from aureon.autonomous.aureon_capability_stress_audit import build_and_write_capability_stress_audit


def _fake_expression_context(*args, **kwargs):
    return {
        "schema_features": ["aureon_code_expression_context_v1"],
        "ok": True,
        "voice_summary": "Aureon stress audit recorded safe code evidence.",
        "runtime_summary": "stress audit state translated",
        "redaction_applied": False,
    }


def _seed_admin_proofs(root: Path) -> Path:
    proof = root / "proof"
    proof.mkdir(parents=True, exist_ok=True)
    payloads = {
        "20260606T000001_admin_cognitive_cycle.json": {"schema_version": "aureon-admin-cognitive-cycle-v1", "status": {"passed": True}},
        "20260606T000002_logistics_office_self_audit.json": {"schema_version": "aureon-logistics-office-self-audit-v1", "status": {"passed": True}},
        "20260606T000003_workweek_dispatch_tick.json": {"schema_version": "aureon-workweek-dispatch-tick-v1", "status": {"state": "specialist_work_dispatched"}},
        "20260606T000004_stock_migration_queue_worker_result.json": {"schema_version": "azyra-stock-migration-queue-worker-result-v1", "ok": True},
    }
    for name, payload in payloads.items():
        (proof / name).write_text(json.dumps(payload), encoding="utf-8")
    return proof


def test_capability_stress_audit_proves_barcode_and_catches_fake_pass_gate(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "aureon.autonomous.aureon_safe_code_control.build_code_expression_context",
        _fake_expression_context,
    )
    cases = [
        {
            "id": "barcode_label_tool",
            "family": "adaptive_skill",
            "prompt": "Build a local barcode label generator tool for the warehouse team, with run instructions and proof.",
            "expected_handover": True,
            "required_kind": "barcode_label_generator",
            "required_checks": ["domain_specific_barcode_logic", "printable_label_preview"],
        },
        {
            "id": "generic_unknown_tool_gate",
            "family": "adaptive_skill",
            "prompt": "Build a local quantum spline inventory generator tool with run instructions and proof.",
            "expected_handover": False,
            "required_kind": "adaptive_skill_capsule",
            "required_checks": ["domain_specific_worker_present"],
        },
    ]

    report = build_and_write_capability_stress_audit(root=tmp_path, cases=cases)
    public = json.loads((tmp_path / "frontend" / "public" / "aureon_capability_stress_audit.json").read_text(encoding="utf-8"))

    assert report["ok"] is True
    assert report["summary"]["case_count"] == 2
    assert report["summary"]["passed_count"] == 2
    assert report["summary"]["fake_pass_count"] == 0
    assert report["capability_scope"]["proven_now"] == ["barcode_label_tool"]
    assert report["capability_scope"]["correctly_blocked"] == ["generic_unknown_tool_gate"]
    assert public["schema_version"] == "aureon-capability-stress-audit-v1"


def test_capability_stress_audit_proves_human_admin_workflow_matrix(tmp_path: Path) -> None:
    proof_dir = _seed_admin_proofs(tmp_path)
    cases = [
        {
            "id": "human_admin_workflow_matrix",
            "family": "admin_workflow",
            "prompt": "Stress test Aureon against a high-level logistics admin workweek.",
            "expected_handover": True,
            "required_kind": "admin_capability_matrix",
            "required_checks": [
                "generic_admin_baseline_present",
                "sfg_admin_overlay_present",
                "admin_jobs_have_routes",
                "controlled_record_update_gated",
                "live_mutation_gates_present",
                "work_orders_present",
                "output_artifacts_exist",
            ],
            "proof_dirs": [str(proof_dir)],
        }
    ]

    report = build_and_write_capability_stress_audit(root=tmp_path, cases=cases)
    case = report["cases"][0]

    assert report["ok"] is True
    assert report["capability_scope"]["proven_now"] == ["human_admin_workflow_matrix"]
    assert case["artifact_kind"] == "admin_capability_matrix"
    assert case["actual_handover"] is True
    assert case["admin_matrix_summary"]["generic_admin_row_count"] >= 8
    assert case["admin_matrix_summary"]["sfg_admin_row_count"] >= 28
    assert case["live_execution"]["allowed_now"] is False
