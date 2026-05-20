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
