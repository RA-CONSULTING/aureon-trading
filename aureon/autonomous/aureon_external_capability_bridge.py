"""Aureon bridges for Codex-adjacent document, image, and automation skills."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Sequence

try:
    from aureon.queen.queen_code_architect import QueenCodeArchitect
except Exception:  # pragma: no cover
    QueenCodeArchitect = None  # type: ignore[assignment]


SCHEMA_VERSION = "aureon-external-capability-bridge-v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STATE_PATH = Path("state/aureon_external_capability_bridge_last_run.json")
DEFAULT_AUDIT_JSON = Path("docs/audits/aureon_external_capability_bridge.json")
DEFAULT_AUDIT_MD = Path("docs/audits/aureon_external_capability_bridge.md")
DEFAULT_PUBLIC_JSON = Path("frontend/public/aureon_external_capability_bridge.json")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_root() -> Path:
    cwd = Path.cwd().resolve()
    if (cwd / "aureon").exists() or (cwd / "frontend").exists() or (cwd / "README.md").exists():
        return cwd
    return REPO_ROOT


def _rooted(root: Path, path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else root / candidate


def _write_text(root: Path, rel_path: Path, content: str) -> dict[str, Any]:
    rel = str(rel_path).replace("\\", "/")
    if QueenCodeArchitect is not None:
        queen = QueenCodeArchitect(repo_path=str(root))
        ok = queen.write_file(rel, content, backup=True)
        return {"path": rel, "ok": bool(ok), "writer": "QueenCodeArchitect"}
    target = _rooted(root, rel_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return {"path": rel, "ok": True, "writer": "direct_fallback"}


def _write_json(root: Path, rel_path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    return _write_text(root, rel_path, json.dumps(payload, indent=2, sort_keys=True, default=str))


def _bridge_rows(root: Path) -> list[dict[str, Any]]:
    return [
        {
            "id": "documents_and_pdfs",
            "title": "Documents and PDFs",
            "status": "ready_for_aureon_contract",
            "aureon_surface": "aureon.autonomous.aureon_external_capability_bridge.documents",
            "operator_goal": "Create or revise human-readable documents and PDF-ready reports.",
            "contract": {
                "request_fields": ["goal", "audience", "format", "source_paths", "output_dir", "verification_required"],
                "outputs": ["markdown_report", "optional_pdf_artifact", "render_or_readback_evidence"],
                "verification": ["source files exist", "artifact written", "report is readable", "private values redacted"],
            },
            "current_repo_support": [
                "aureon/core/goal_execution_engine.py",
                "aureon/vault/voice",
                "docs/audits",
            ],
            "public_boundary": "No official filing/submission/payment is performed by this bridge.",
        },
        {
            "id": "image_generation",
            "title": "Image generation",
            "status": "ready_for_prompt_contract",
            "aureon_surface": "aureon.autonomous.aureon_external_capability_bridge.images",
            "operator_goal": "Create a structured image/asset request and register produced visuals as presentation assets.",
            "contract": {
                "request_fields": ["goal", "style", "subject", "reference_paths", "output_path", "evidence_use"],
                "outputs": ["image_prompt_contract", "asset_registry_entry", "redaction_status"],
                "verification": ["prompt has subject/style/use", "asset is not treated as hidden evidence", "source references preserved"],
            },
            "current_repo_support": [
                "frontend/public",
                "docs/audits",
                "aureon/vault/voice",
            ],
            "public_boundary": "Generated visuals explain or present state; they do not prove runtime facts.",
        },
        {
            "id": "automations",
            "title": "Automations",
            "status": "ready_for_schedule_handoff",
            "aureon_surface": "aureon.autonomous.aureon_external_capability_bridge.automations",
            "operator_goal": "Record reminder, monitor, heartbeat, or recurring-work intent as a self-contained handoff.",
            "contract": {
                "request_fields": ["name", "task_prompt", "schedule_text", "destination", "workspace_paths", "status"],
                "outputs": ["automation_handoff_contract", "operator_review_status"],
                "verification": ["prompt is self-contained", "schedule is described", "no raw credential values", "requires operator/app scheduler to activate"],
            },
            "current_repo_support": [
                "state",
                "docs/audits",
                "aureon/autonomous/aureon_local_task_queue.py",
            ],
            "public_boundary": "This bridge records the automation contract; the Codex app scheduler creates live recurring jobs.",
        },
    ]


def build_external_capability_bridge(*, root: Optional[Path] = None, goal: str = "") -> dict[str, Any]:
    root = Path(root or _default_root()).resolve()
    rows = _bridge_rows(root)
    ready = len([row for row in rows if str(row.get("status", "")).startswith("ready")])
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now(),
        "goal": goal,
        "summary": {
            "bridge_count": len(rows),
            "ready_count": ready,
            "coverage_percent": round((ready / max(len(rows), 1)) * 100, 2),
        },
        "who": {
            "executor": "Aureon external capability bridge",
            "authoring_system": "QueenCodeArchitect" if QueenCodeArchitect is not None else "direct_fallback",
        },
        "what": {
            "bridges": rows,
            "purpose": "Bridge Codex document, image, and automation capabilities into Aureon request contracts.",
        },
        "where": {
            "state": str(_rooted(root, DEFAULT_STATE_PATH)),
            "audit_json": str(_rooted(root, DEFAULT_AUDIT_JSON)),
            "audit_md": str(_rooted(root, DEFAULT_AUDIT_MD)),
            "public_json": str(_rooted(root, DEFAULT_PUBLIC_JSON)),
        },
        "when": {"built_at": utc_now()},
        "how": {
            "validation_logic": [
                "define typed request fields",
                "define expected outputs",
                "define verification checks",
                "declare public safety boundary",
            ],
            "used_by": [
                "EVERYTHING_CODEX_CAN_DO.md ingestion",
                "director capability bridge",
                "coding organism prompt lane",
            ],
        },
        "act": {
            "status": "ready",
            "next_step": "Run codex capability ingestion again; documents/images/automations should map to this bridge.",
        },
    }


def _make_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary", {})
    lines = [
        "# Aureon External Capability Bridge",
        "",
        f"- Generated: {report.get('generated_at')}",
        f"- Bridges: {summary.get('bridge_count', 0)}",
        f"- Ready: {summary.get('ready_count', 0)}",
        "",
        "## Bridges",
        "",
    ]
    for row in report.get("what", {}).get("bridges", []):
        lines.append(f"- **{row.get('title')}**: {row.get('status')} - {row.get('operator_goal')}")
    return "\n".join(lines) + "\n"


def build_and_write_external_capability_bridge(*, root: Optional[Path] = None, goal: str = "") -> dict[str, Any]:
    root = Path(root or _default_root()).resolve()
    report = build_external_capability_bridge(root=root, goal=goal)
    writes = [
        _write_json(root, DEFAULT_STATE_PATH, report),
        _write_json(root, DEFAULT_AUDIT_JSON, report),
        _write_json(root, DEFAULT_PUBLIC_JSON, report),
        _write_text(root, DEFAULT_AUDIT_MD, _make_markdown(report)),
    ]
    report["write_info"] = {
        "writer": writes[0].get("writer"),
        "writes": writes,
        "all_ok": all(item.get("ok") for item in writes),
    }
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Publish Aureon external capability bridges.")
    parser.add_argument("--goal", default="")
    args = parser.parse_args(argv)
    result = build_and_write_external_capability_bridge(goal=args.goal)
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0 if result.get("write_info", {}).get("all_ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())

