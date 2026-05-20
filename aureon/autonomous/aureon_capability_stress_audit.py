from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from aureon.autonomous.aureon_capability_forge import (
    DEFAULT_ADAPTIVE_SKILL_DIR,
    REPO_ROOT,
    _is_barcode_label_prompt,
    build_and_write_capability_forge,
)


DEFAULT_STATE_PATH = Path("state/aureon_capability_stress_audit_last_run.json")
DEFAULT_AUDIT_JSON = Path("docs/audits/aureon_capability_stress_audit.json")
DEFAULT_AUDIT_MD = Path("docs/audits/aureon_capability_stress_audit.md")
DEFAULT_PUBLIC_JSON = Path("frontend/public/aureon_capability_stress_audit.json")
CODING_BRIDGE_EVIDENCE_PATHS = [
    Path("state/aureon_coding_organism_last_run.json"),
    Path("docs/audits/aureon_coding_organism_bridge.json"),
    Path("frontend/public/aureon_coding_organism_bridge.json"),
]

DEFAULT_STRESS_CASES: List[Dict[str, Any]] = [
    {
        "id": "barcode_label_tool",
        "family": "adaptive_skill",
        "prompt": "Build a local barcode label generator tool for the warehouse team, with run instructions and proof.",
        "expected_handover": True,
        "required_kind": "barcode_label_generator",
        "required_checks": ["domain_specific_barcode_logic", "printable_label_preview"],
        "why": "proves unknown-tool requests can recruit a domain-specific local worker instead of a generic shell",
    },
    {
        "id": "interactive_game",
        "family": "interactive_app",
        "prompt": "Make me a game where a man walks up to a glowing door and tell the end user how to play from the keyboard.",
        "expected_handover": True,
        "required_kind": "html_game",
        "required_checks": ["html_artifact_exists", "keyboard_controls_visible"],
        "why": "proves local playable UI/game generation with visible controls",
    },
    {
        "id": "short_video_preview",
        "family": "media",
        "prompt": "Make a 1 second video of a dog running across the screen and show a browser-playable preview.",
        "expected_handover": True,
        "required_kinds": ["video", "animated_gif", "webm_video"],
        "required_checks": ["artifact_file_exists", "preview_page_present"],
        "why": "proves media handover requires playable browser preview, not only a file path",
    },
    {
        "id": "generic_unknown_tool_gate",
        "family": "adaptive_skill",
        "prompt": "Build a local quantum spline inventory generator tool with run instructions and proof.",
        "expected_handover": False,
        "required_kind": "adaptive_skill_capsule",
        "required_checks": ["domain_specific_worker_present"],
        "why": "proves Aureon does not fake-pass a finished tool when no domain worker exists yet",
    },
]


def _default_root() -> Path:
    return Path.cwd().resolve() if (Path.cwd() / "aureon").exists() else REPO_ROOT


def _rooted(root: Path, rel_path: Path) -> Path:
    return rel_path if rel_path.is_absolute() else root / rel_path


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_text(path: Path, content: str) -> Dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return {"path": str(path), "ok": path.exists(), "bytes": path.stat().st_size if path.exists() else 0}


def _write_json(path: Path, payload: Dict[str, Any]) -> Dict[str, Any]:
    return _write_text(path, json.dumps(payload, indent=2, sort_keys=True, default=str))


def _artifact_exists(value: Any) -> bool:
    path = Path(str(value or ""))
    return bool(value) and path.exists()


def _check_lookup(quality: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    checks = quality.get("checks") if isinstance(quality.get("checks"), list) else []
    return {str(item.get("id")): item for item in checks if isinstance(item, dict)}


def _required_kind_ok(manifest: Dict[str, Any], case: Dict[str, Any]) -> bool:
    kind = str(manifest.get("kind") or "")
    if case.get("required_kind"):
        return kind == str(case["required_kind"])
    required_kinds = case.get("required_kinds")
    if isinstance(required_kinds, list) and required_kinds:
        return kind in {str(item) for item in required_kinds}
    return bool(kind)


def _run_case(case: Dict[str, Any], root: Path) -> Dict[str, Any]:
    report = build_and_write_capability_forge(str(case.get("prompt") or ""), root=root)
    quality = report.get("artifact_quality_report") if isinstance(report.get("artifact_quality_report"), dict) else {}
    manifest = report.get("artifact_manifest") if isinstance(report.get("artifact_manifest"), dict) else {}
    checks = _check_lookup(quality)
    required_checks = [str(item) for item in case.get("required_checks", [])]
    expected_handover = bool(case.get("expected_handover"))
    required_checks_ok = (
        all(checks.get(check_id, {}).get("ok") is True for check_id in required_checks)
        if expected_handover
        else all(check_id in checks for check_id in required_checks)
    )
    kind_ok = _required_kind_ok(manifest, case)
    asset_exists = _artifact_exists(manifest.get("asset_path")) if manifest.get("asset_path") else True
    preview_exists = _artifact_exists(manifest.get("preview_path")) if manifest.get("preview_path") else bool(manifest.get("preview_url") or manifest.get("public_url"))
    actual_handover = bool(report.get("handover_ready"))
    fake_pass = bool(
        actual_handover
        and manifest.get("kind") == "adaptive_skill_capsule"
        and _is_barcode_label_prompt(case.get("prompt", ""))
    )
    ok = actual_handover == expected_handover and kind_ok and required_checks_ok and asset_exists and preview_exists and not fake_pass
    blocking_snags = quality.get("snags") if isinstance(quality.get("snags"), list) else []
    return {
        "id": case.get("id"),
        "family": case.get("family"),
        "prompt": case.get("prompt"),
        "why": case.get("why"),
        "ok": ok,
        "expected_handover": expected_handover,
        "actual_handover": actual_handover,
        "status": report.get("status"),
        "task_family": report.get("task_family"),
        "artifact_kind": manifest.get("kind"),
        "artifact_url": manifest.get("public_url") or manifest.get("preview_url"),
        "quality_score": quality.get("score"),
        "quality_status": quality.get("status"),
        "blocking_snag_count": len(blocking_snags),
        "required_kind_ok": kind_ok,
        "required_checks_ok": required_checks_ok,
        "asset_exists": asset_exists,
        "preview_exists": preview_exists,
        "fake_pass_detected": fake_pass,
        "checks": [
            {
                "id": check_id,
                "ok": bool(checks.get(check_id, {}).get("ok")),
                "label": checks.get(check_id, {}).get("label"),
            }
            for check_id in required_checks
        ],
        "handover_gate": {
            "state": "visible" if actual_handover else "held",
            "reason": "quality passed" if actual_handover else "quality gate or expected blocker held handover",
        },
        "report_job_id": report.get("job_id"),
    }


def _legacy_capsule_findings(root: Path) -> List[Dict[str, Any]]:
    base = _rooted(root, DEFAULT_ADAPTIVE_SKILL_DIR)
    if not base.exists():
        return []
    findings: List[Dict[str, Any]] = []
    for metadata_path in base.glob("*/skill.json"):
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        prompt = str(metadata.get("prompt") or "")
        if not _is_barcode_label_prompt(prompt):
            continue
        tool_path = Path(str(metadata.get("tool_path") or metadata_path.with_name("tool.py")))
        tool_text = tool_path.read_text(encoding="utf-8") if tool_path.exists() else ""
        if metadata.get("kind") == "adaptive_skill_capsule" and "CODE39_PATTERNS" not in tool_text:
            findings.append(
                {
                    "id": "legacy_generic_barcode_capsule",
                    "severity": "high",
                    "title": "Old barcode tool artifact was a generic adaptive capsule",
                    "metadata_path": str(metadata_path),
                    "tool_path": str(tool_path),
                    "prompt": prompt[:240],
                    "fix_status": "new barcode_label_generator_skill now replaces this path on rerun",
                }
            )
    return findings


def _make_markdown(report: Dict[str, Any]) -> str:
    summary = report.get("summary", {})
    lines = [
        "# Aureon Capability Stress Audit",
        "",
        f"- status: {report.get('status')}",
        f"- cases: {summary.get('case_count')}",
        f"- passed: {summary.get('passed_count')}",
        f"- expected blocked: {summary.get('expected_blocked_count')}",
        f"- fake passes: {summary.get('fake_pass_count')}",
        f"- legacy findings: {summary.get('legacy_finding_count')}",
        "",
        "## Cases",
    ]
    for case in report.get("cases", []):
        lines.append(
            f"- {case.get('id')}: ok={case.get('ok')} handover={case.get('actual_handover')} "
            f"kind={case.get('artifact_kind')} score={case.get('quality_score')} url={case.get('artifact_url')}"
        )
    findings = report.get("legacy_findings", [])
    if findings:
        lines.extend(["", "## Findings"])
        for finding in findings:
            lines.append(f"- {finding.get('severity')}: {finding.get('title')} ({finding.get('metadata_path')})")
    return "\n".join(lines) + "\n"


def _attach_to_coding_bridge_evidence(root: Path, report: Dict[str, Any]) -> List[Dict[str, Any]]:
    writes: List[Dict[str, Any]] = []
    compact_report = dict(report)
    compact_report.pop("write_info", None)
    for rel_path in CODING_BRIDGE_EVIDENCE_PATHS:
        path = _rooted(root, rel_path)
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        payload["capability_stress_audit"] = compact_report
        summary = payload.setdefault("summary", {})
        if isinstance(summary, dict):
            summary["capability_stress_audit_status"] = compact_report.get("status")
            summary["capability_stress_fake_pass_count"] = (compact_report.get("summary") or {}).get("fake_pass_count", 0)
            summary["capability_stress_case_count"] = (compact_report.get("summary") or {}).get("case_count", 0)
        writes.append(_write_json(path, payload))
    return writes


def build_and_write_capability_stress_audit(
    *,
    root: Optional[Path] = None,
    cases: Optional[Sequence[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    root = Path(root or _default_root()).resolve()
    case_list = list(cases or DEFAULT_STRESS_CASES)
    results = [_run_case(case, root) for case in case_list]
    legacy_findings = _legacy_capsule_findings(root)
    passed_count = sum(1 for item in results if item.get("ok"))
    fake_pass_count = sum(1 for item in results if item.get("fake_pass_detected"))
    unexpected_failures = [item for item in results if not item.get("ok")]
    expected_blocked_count = sum(1 for item in results if item.get("expected_handover") is False and item.get("actual_handover") is False)
    status = "capability_stress_audit_passed"
    if fake_pass_count:
        status = "capability_stress_audit_fake_pass_detected"
    elif unexpected_failures:
        status = "capability_stress_audit_needs_attention"
    elif legacy_findings:
        status = "capability_stress_audit_passed_with_legacy_findings"

    report: Dict[str, Any] = {
        "schema_version": "aureon-capability-stress-audit-v1",
        "status": status,
        "ok": fake_pass_count == 0 and not unexpected_failures,
        "generated_at": _utc_now(),
        "audit_contract": {
            "goal": "Stress Aureon across task families and catch fake passes before client handover.",
            "quality_rule": "Expected blockers are acceptable; hidden half-finished handovers are not.",
            "authority_boundaries": ["local-only", "no live trading", "no payment", "no filing", "no credential reveal"],
        },
        "cases": results,
        "legacy_findings": legacy_findings,
        "capability_scope": {
            "proven_now": [item["id"] for item in results if item.get("ok") and item.get("actual_handover")],
            "correctly_blocked": [item["id"] for item in results if item.get("ok") and not item.get("actual_handover")],
            "needs_repair": [item["id"] for item in unexpected_failures],
            "legacy_artifacts_to_ignore_or_regenerate": [item.get("metadata_path") for item in legacy_findings],
        },
        "fixes_applied": [
            "barcode label prompts now recruit barcode_label_generator_skill instead of universal_adaptive_skill_forge",
            "generic finished-tool prompts now hold handover when no domain-specific worker exists",
            "stress audit publishes case-by-case capability scope for the cockpit",
        ],
        "summary": {
            "case_count": len(results),
            "passed_count": passed_count,
            "unexpected_failure_count": len(unexpected_failures),
            "expected_blocked_count": expected_blocked_count,
            "fake_pass_count": fake_pass_count,
            "legacy_finding_count": len(legacy_findings),
            "handover_ready_case_count": sum(1 for item in results if item.get("actual_handover")),
            "correctly_held_case_count": sum(1 for item in results if item.get("ok") and not item.get("actual_handover")),
        },
        "output_files": [
            DEFAULT_STATE_PATH.as_posix(),
            DEFAULT_AUDIT_JSON.as_posix(),
            DEFAULT_AUDIT_MD.as_posix(),
            DEFAULT_PUBLIC_JSON.as_posix(),
        ],
    }
    writes = [
        _write_json(_rooted(root, DEFAULT_STATE_PATH), report),
        _write_json(_rooted(root, DEFAULT_AUDIT_JSON), report),
        _write_text(_rooted(root, DEFAULT_AUDIT_MD), _make_markdown(report)),
        _write_json(_rooted(root, DEFAULT_PUBLIC_JSON), report),
    ]
    bridge_writes = _attach_to_coding_bridge_evidence(root, report)
    report["write_info"] = {"evidence_writes": writes, "coding_bridge_evidence_writes": bridge_writes}
    for rel in (DEFAULT_STATE_PATH, DEFAULT_AUDIT_JSON, DEFAULT_PUBLIC_JSON):
        _write_json(_rooted(root, rel), report)
    _write_text(_rooted(root, DEFAULT_AUDIT_MD), _make_markdown(report))
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run Aureon's local capability stress audit.")
    parser.add_argument("--root", default="", help="Repository root. Defaults to current Aureon repo.")
    parser.add_argument("--json", action="store_true", help="Print the full JSON report.")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve() if args.root else None
    report = build_and_write_capability_stress_audit(root=root)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        summary = report.get("summary", {})
        print(
            f"{report.get('status')}: {summary.get('passed_count')}/{summary.get('case_count')} cases ok; "
            f"fake_passes={summary.get('fake_pass_count')} legacy_findings={summary.get('legacy_finding_count')}"
        )
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
