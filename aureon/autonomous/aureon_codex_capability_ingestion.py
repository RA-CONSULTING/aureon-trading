"""Ingest the public Codex capability document into Aureon's own bridge plan."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Sequence

try:
    from aureon.autonomous.aureon_director_capability_bridge import (
        CODEX_CLASS_CAPABILITIES,
        build_and_write_director_capability_bridge,
    )
except Exception:  # pragma: no cover
    CODEX_CLASS_CAPABILITIES = []  # type: ignore[assignment]
    build_and_write_director_capability_bridge = None  # type: ignore[assignment]

try:
    from aureon.queen.queen_code_architect import QueenCodeArchitect
except Exception:  # pragma: no cover
    QueenCodeArchitect = None  # type: ignore[assignment]

try:
    from aureon.autonomous.aureon_external_capability_bridge import build_and_write_external_capability_bridge
except Exception:  # pragma: no cover
    build_and_write_external_capability_bridge = None  # type: ignore[assignment]


SCHEMA_VERSION = "aureon-codex-capability-ingestion-v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_MD = Path("EVERYTHING_CODEX_CAN_DO.md")
DEFAULT_STATE_PATH = Path("state/aureon_codex_capability_ingestion_last_run.json")
DEFAULT_AUDIT_JSON = Path("docs/audits/aureon_codex_capability_ingestion_report.json")
DEFAULT_AUDIT_MD = Path("docs/audits/aureon_codex_capability_ingestion_report.md")
DEFAULT_PUBLIC_JSON = Path("frontend/public/aureon_codex_capability_ingestion_report.json")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _rooted(root: Path, path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else root / candidate


def _default_root() -> Path:
    cwd = Path.cwd().resolve()
    if (cwd / "aureon").exists() or (cwd / "frontend").exists() or (cwd / "EVERYTHING_CODEX_CAN_DO.md").exists():
        return cwd
    return REPO_ROOT


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


def _parse_markdown_capabilities(markdown: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    in_table = False
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("| Codex capability |"):
            in_table = True
            continue
        if in_table and stripped.startswith("| ---"):
            continue
        if in_table and stripped.startswith("|"):
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            if len(cells) >= 3:
                title = cells[0].strip()
                if title:
                    rows.append(
                        {
                            "title": title,
                            "codex_can": cells[1].strip(),
                            "aureon_bridge_requirement": cells[2].strip(),
                        }
                    )
            continue
        if in_table and stripped and not stripped.startswith("|"):
            break
    return rows


def _slug(text: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return value or "capability"


def _match_existing_capability(row: dict[str, Any]) -> dict[str, Any]:
    haystack = f"{row.get('title', '')} {row.get('codex_can', '')} {row.get('aureon_bridge_requirement', '')}".lower()
    best: Optional[dict[str, Any]] = None
    best_score = 0
    for candidate in CODEX_CLASS_CAPABILITIES:
        words = set(re.findall(r"[a-z0-9]+", f"{candidate.get('id', '')} {candidate.get('title', '')} {candidate.get('codex_can', '')}".lower()))
        score = sum(1 for word in words if len(word) > 3 and word in haystack)
        if score > best_score:
            best = candidate
            best_score = score
    return {
        "matched": bool(best and best_score >= 2),
        "match_score": best_score,
        "existing_capability_id": best.get("id") if best else "",
        "existing_capability_title": best.get("title") if best else "",
        "aureon_surfaces": best.get("aureon_surfaces", []) if best else [],
        "bridge_prompt": best.get("bridge_prompt") if best else row.get("aureon_bridge_requirement", ""),
    }


def build_codex_capability_ingestion(
    source_md: str | Path = DEFAULT_SOURCE_MD,
    *,
    root: Optional[Path] = None,
    goal: str = "",
) -> dict[str, Any]:
    root = Path(root or _default_root()).resolve()
    source_path = _rooted(root, source_md)
    markdown = source_path.read_text(encoding="utf-8")
    parsed = _parse_markdown_capabilities(markdown)

    bridged_rows: list[dict[str, Any]] = []
    work_orders: list[dict[str, Any]] = []
    for index, row in enumerate(parsed, start=1):
        match = _match_existing_capability(row)
        missing_surfaces = [
            surface for surface in match.get("aureon_surfaces", [])
            if not _rooted(root, surface).exists()
        ]
        status = "ready" if match["matched"] and not missing_surfaces else "bridge_required"
        item = {
            "id": _slug(row["title"]),
            "sequence": index,
            **row,
            **match,
            "missing_surfaces": missing_surfaces,
            "status": status,
        }
        bridged_rows.append(item)
        if status != "ready":
            work_orders.append(
                {
                    "id": f"codex_capability_bridge_{index:03d}_{item['id']}",
                    "title": f"Bridge {row['title']}",
                    "status": "queued_for_aureon_coding_organism",
                    "source_capability": row["title"],
                    "exact_aureon_prompt": (
                        "Aureon must read EVERYTHING_CODEX_CAN_DO.md, implement the bridge for "
                        f"{row['title']}, write or update the smallest required repo files, run focused tests, "
                        "and publish validation evidence."
                    ),
                    "required_tests": [
                        "pytest tests/test_codex_capability_ingestion.py -q",
                        "pytest tests/test_director_capability_bridge.py -q",
                    ],
                }
            )

    external_bridge_report = None
    if build_and_write_external_capability_bridge is not None:
        external_bridge_report = build_and_write_external_capability_bridge(
            root=root,
            goal=goal or "Aureon bridge Codex document image and automation capabilities",
        )

    director_report = None
    if build_and_write_director_capability_bridge is not None:
        director_report = build_and_write_director_capability_bridge(
            goal or "Aureon ingest Everything Codex Can Do and bridge gaps",
            root=root,
        )

    ready_count = len([row for row in bridged_rows if row["status"] == "ready"])
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now(),
        "source_document": str(source_path),
        "goal": goal,
        "summary": {
            "capability_rows_read": len(parsed),
            "ready_count": ready_count,
            "bridge_required_count": len(work_orders),
            "coverage_percent": round((ready_count / max(len(parsed), 1)) * 100, 2),
            "director_bridge_ran": bool(director_report),
            "external_bridge_ran": bool(external_bridge_report),
        },
        "who": {
            "operator": "Codex director mode",
            "executor": "Aureon coding organism",
            "authoring_system": "QueenCodeArchitect" if QueenCodeArchitect is not None else "direct_fallback",
        },
        "what": {
            "source": "EVERYTHING_CODEX_CAN_DO.md",
            "task": "ingest Codex capability map and bridge Aureon gaps",
            "capabilities": bridged_rows,
        },
        "where": {
            "state": str(_rooted(root, DEFAULT_STATE_PATH)),
            "audit_json": str(_rooted(root, DEFAULT_AUDIT_JSON)),
            "audit_md": str(_rooted(root, DEFAULT_AUDIT_MD)),
            "public_json": str(_rooted(root, DEFAULT_PUBLIC_JSON)),
        },
        "when": {"ingested_at": utc_now()},
        "how": {
            "steps": [
                "read Markdown source document",
                "parse capability table",
                "match rows to Aureon director capability surfaces",
                "run director capability bridge",
                "run external document/image/automation bridge",
                "publish state/docs/frontend evidence",
                "queue exact bridge work orders for missing/partial items",
            ],
            "director_summary": (director_report or {}).get("summary", {}),
            "external_bridge_summary": (external_bridge_report or {}).get("summary", {}),
        },
        "act": {
            "status": "completed_with_bridge_work_orders" if work_orders else "completed_all_ready",
            "work_orders": work_orders,
            "validation": {
                "source_document_exists": source_path.exists(),
                "capability_rows_read": len(parsed),
                "public_report_ready": True,
                "director_bridge_ran": bool(director_report),
                "external_bridge_ran": bool(external_bridge_report),
            },
        },
        "completion_report": {
            "did_read_source_document": True,
            "did_marriage_map": True,
            "did_generate_bridge_work_orders": True,
            "did_run_director_bridge": bool(director_report),
            "did_run_external_bridge": bool(external_bridge_report),
            "self_validation_result": "passing" if parsed and bool(director_report) and bool(external_bridge_report) else "attention",
            "remaining_work": [order["title"] for order in work_orders],
        },
    }
    return report


def _make_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary", {})
    lines = [
        "# Aureon Codex Capability Ingestion Report",
        "",
        f"- Generated: {report.get('generated_at')}",
        f"- Source: `{report.get('source_document')}`",
        f"- Capabilities read: {summary.get('capability_rows_read', 0)}",
        f"- Ready: {summary.get('ready_count', 0)}",
        f"- Bridge required: {summary.get('bridge_required_count', 0)}",
        f"- Coverage: {summary.get('coverage_percent', 0)}%",
        "",
        "## Completion Report",
        "",
    ]
    completion = report.get("completion_report", {})
    for key, value in completion.items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Bridge Work Orders", ""])
    for order in report.get("act", {}).get("work_orders", []):
        lines.append(f"- **{order.get('title')}**: {order.get('exact_aureon_prompt')}")
    if not report.get("act", {}).get("work_orders"):
        lines.append("- No missing bridge work orders.")
    return "\n".join(lines) + "\n"


def build_and_write_codex_capability_ingestion(
    source_md: str | Path = DEFAULT_SOURCE_MD,
    *,
    root: Optional[Path] = None,
    goal: str = "",
) -> dict[str, Any]:
    root = Path(root or _default_root()).resolve()
    report = build_codex_capability_ingestion(source_md, root=root, goal=goal)
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
    parser = argparse.ArgumentParser(description="Ingest EVERYTHING_CODEX_CAN_DO.md into Aureon's bridge plan.")
    parser.add_argument("--source-md", default=str(DEFAULT_SOURCE_MD))
    parser.add_argument("--goal", default="")
    args = parser.parse_args(argv)
    result = build_and_write_codex_capability_ingestion(args.source_md, goal=args.goal)
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0 if result.get("completion_report", {}).get("self_validation_result") == "passing" else 1


if __name__ == "__main__":
    raise SystemExit(main())
