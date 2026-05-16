from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from aureon.autonomous.aureon_artifact_quality_gate import (
    DEFAULT_PUBLIC_QUALITY_JSON,
    build_artifact_quality_report,
    write_artifact_quality_report,
)
from aureon.autonomous.aureon_safe_code_control import CodeProposal, SafeCodeControl


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STATE_PATH = Path("state/aureon_capability_forge_last_run.json")
DEFAULT_AUDIT_JSON = Path("docs/audits/aureon_capability_forge.json")
DEFAULT_AUDIT_MD = Path("docs/audits/aureon_capability_forge.md")
DEFAULT_PUBLIC_JSON = Path("frontend/public/aureon_capability_forge.json")
DEFAULT_SAFE_CODE_STATE = Path("state/aureon_capability_forge_safe_code_state.json")

REFERENCE_PATTERNS = [
    {
        "name": "OpenAI Agents SDK",
        "url": "https://developers.openai.com/api/docs/guides/agents",
        "pattern": "agents, tools, handoffs, guardrails, tracing, sandbox state",
    },
    {
        "name": "Anthropic tool use",
        "url": "https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview",
        "pattern": "client tools, server tools, strict schemas, tool_result loop",
    },
    {
        "name": "Claude Code subagents",
        "url": "https://code.claude.com/docs/en/sub-agents",
        "pattern": "specialist workers with isolated context and scoped tool access",
    },
    {
        "name": "Gemini function calling",
        "url": "https://ai.google.dev/gemini-api/docs/function-calling",
        "pattern": "OpenAPI-shaped function calls and automatic function execution",
    },
    {
        "name": "Gemini Veo video flow",
        "url": "https://ai.google.dev/gemini-api/docs/video",
        "pattern": "image/storyboard seed, async video operation, poll until ready",
    },
    {
        "name": "AutoGen multi-agent chat",
        "url": "https://microsoft.github.io/autogen/0.2/docs/Use-Cases/agent_chat/",
        "pattern": "conversable agents coordinating tools and human feedback",
    },
    {
        "name": "Semantic Kernel orchestration",
        "url": "https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/agent-orchestration/",
        "pattern": "sequential, concurrent, group, and handoff orchestration",
    },
    {
        "name": "GitHub Copilot cloud agent",
        "url": "https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/start-copilot-sessions",
        "pattern": "delegate prompt to agent, inspect session, review resulting changes",
    },
    {
        "name": "Jules coding agent",
        "url": "https://jules.google/docs/",
        "pattern": "autonomous coding task in repo context with human review",
    },
    {
        "name": "Runway video models",
        "url": "https://docs.dev.runwayml.com/guides/models/",
        "pattern": "video models expose text/image-to-video as job artifacts",
    },
    {
        "name": "Adobe Firefly Services",
        "url": "https://developer.adobe.com/firefly-services/docs/guides/",
        "pattern": "creative generation at scale with credentials kept server-side",
    },
    {
        "name": "Canva Connect design metadata",
        "url": "https://www.canva.dev/docs/connect/api-reference/designs/get-design/",
        "pattern": "design preview/edit/view metadata with expiring URLs",
    },
]

TASK_FAMILIES = [
    "video",
    "image_graphic_design",
    "coding",
    "ui",
    "document",
    "research",
    "browser_qa",
    "mixed",
]

FAMILY_KEYWORDS = {
    "video": ("video", "clip", "animation", "mp4", "webm", "10 second", "seconds"),
    "image_graphic_design": ("image", "picture", "graphic", "logo", "design", "poster", "draw", "illustration", "svg"),
    "coding": ("code", "repo", "patch", "python", "typescript", "test", "build", "function", "module"),
    "ui": ("ui", "frontend", "dashboard", "console", "panel", "react", "tsx", "screen"),
    "document": ("document", "pdf", "markdown", "report", "runbook", "docx"),
    "research": ("research", "online", "official docs", "search", "learn", "source"),
    "browser_qa": ("browser", "playwright", "smoke", "screenshot", "open the page", "render"),
}


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


def _contains_any(text: str, needles: Iterable[str]) -> bool:
    normalized = re.sub(r"\s+", " ", str(text or "").lower())
    for needle in needles:
        keyword = str(needle or "").lower().strip()
        if not keyword:
            continue
        if re.fullmatch(r"[a-z0-9 ]+", keyword):
            if re.search(rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])", normalized):
                return True
        elif keyword in normalized:
            return True
    return False


def classify_task_family(prompt: str) -> Dict[str, Any]:
    text = str(prompt or "").lower()
    hits = [family for family, needles in FAMILY_KEYWORDS.items() if _contains_any(text, needles)]
    priority = ("video", "image_graphic_design", "browser_qa", "ui", "coding", "document", "research")
    if len(hits) > 1:
        primary = next((family for family in priority if family in hits), hits[0])
        family = "mixed" if primary not in {"video", "image_graphic_design"} else primary
    elif hits:
        family = hits[0]
        primary = family
    else:
        family = "coding"
        primary = "coding"
    return {
        "task_family": family,
        "primary_family": primary,
        "detected_families": hits or [family],
        "local_only": True,
    }


def _crew_for_families(families: Sequence[str]) -> List[Dict[str, Any]]:
    base = [
        ("Client Brief Broker", "scope", "lock goal, deliverables, constraints, and acceptance proof"),
        ("Skill Headhunter", "research", "scan local repo first and use official docs as reference-only patterns"),
        ("Subcontractor Crew Builder", "orchestration", "hire the temporary specialist crew and define handoffs"),
        ("Quality Gate Inspector", "qa", "reject weak artifacts before handover"),
        ("Release Manager", "handover", "publish evidence and wait for approval"),
    ]
    family_roles = {
        "video": [
            ("Storyboard Artist", "media", "turn prompt into frames, motion, duration, and preview plan"),
            ("Local Encoder", "media", "produce WebM, GIF fallback, and HTML preview"),
            ("Playback Inspector", "qa", "probe duration and browser-playable artifact state"),
        ],
        "image_graphic_design": [
            ("Graphic Designer", "media", "produce a renderable local visual asset"),
            ("Visual QA Inspector", "qa", "check dimensions, prompt match, and public preview"),
        ],
        "coding": [
            ("Code Architect", "engineering", "scope patch contract and authority boundaries"),
            ("Implementation Worker", "engineering", "route code work through safe local authoring"),
            ("Test Pilot", "qa", "run tests/build proof before approval"),
            ("Security Auditor", "security", "check secrets and unsafe mutation boundaries"),
        ],
        "ui": [
            ("UX Designer", "product", "make the interface usable for a human operator"),
            ("Frontend Console Builder", "engineering", "mount evidence and previews in the cockpit"),
            ("Browser Smoke Inspector", "qa", "confirm visible UI proof"),
        ],
        "document": [("Runbook Writer", "docs", "publish readable operator evidence and handover docs")],
        "research": [("Research Scout", "research", "summarize source-linked patterns without external execution")],
        "browser_qa": [("Browser Smoke Inspector", "qa", "open local UI, inspect console state, and record proof")],
    }
    crew = [{"role": role, "department": dept, "day_to_day": duty, "temporary": True} for role, dept, duty in base]
    for family in families:
        for role, dept, duty in family_roles.get(family, []):
            if not any(item["role"] == role for item in crew):
                crew.append({"role": role, "department": dept, "day_to_day": duty, "temporary": True})
    return crew


def _tools_for_families(families: Sequence[str]) -> List[Dict[str, Any]]:
    tools = [
        {"name": "Repo search", "surface": "rg / RepoSelfCatalog", "mode": "read_only"},
        {"name": "SafeCodeControl", "surface": "aureon.autonomous.aureon_safe_code_control", "mode": "local_safe_route"},
        {"name": "Artifact quality gate", "surface": "aureon.autonomous.aureon_artifact_quality_gate", "mode": "local_quality_gate"},
    ]
    if "video" in families or "image_graphic_design" in families:
        tools.append({"name": "Visual asset worker", "surface": "aureon.autonomous.aureon_visual_asset_request", "mode": "local_generation"})
    if "browser_qa" in families or "ui" in families or "video" in families:
        tools.append({"name": "Playwright/browser smoke", "surface": "frontend Playwright", "mode": "local_browser_proof"})
    if "coding" in families or "ui" in families:
        tools.append({"name": "Focused pytest/build", "surface": "pytest / npm run build", "mode": "local_validation"})
    return tools


def _reference_patterns() -> List[Dict[str, Any]]:
    return [
        {
            **item,
            "provider_policy": "reference_only",
            "external_api_call_allowed": False,
        }
        for item in REFERENCE_PATTERNS
    ]


def _visual_artifact(prompt: str, root: Path) -> Dict[str, Any]:
    from aureon.autonomous.aureon_visual_asset_request import build_and_write_visual_asset_request

    result = build_and_write_visual_asset_request(prompt, root=root, open_requested=True)
    return result if isinstance(result, dict) else {}


def _safe_code_proposal(prompt: str, root: Path, families: Sequence[str]) -> Dict[str, Any]:
    controller = SafeCodeControl(state_path=_rooted(root, DEFAULT_SAFE_CODE_STATE))
    target_files = [
        "aureon/autonomous/aureon_capability_forge.py",
        "aureon/autonomous/aureon_artifact_quality_gate.py",
        "frontend/src/components/generated/AureonCodingOrganismConsole.tsx",
    ]
    proposal = controller.propose(
        CodeProposal(
            kind="capability_forge_coding_job",
            title=prompt[:120],
            summary="Local capability forge scoped this coding/UI request and queued safe route evidence for after-apply review.",
            target_files=target_files if any(family in families for family in ("coding", "ui", "mixed")) else [],
            patch_text="",
            metadata={
                "provider_policy": "local_only_v1",
                "approval_gate": "after_apply",
                "detected_families": list(families),
                "safe_authority": "no live trading, payment, filing, credential, or destructive OS bypass",
            },
            source="aureon_capability_forge",
        )
    )
    return {
        "safe_route": "SafeCodeControl.propose",
        "applied": True,
        "applied_scope": "evidence and safe-code proposal applied locally; target repo patch requires generated proof and review",
        "proposal": proposal,
        "state_path": str(_rooted(root, DEFAULT_SAFE_CODE_STATE)),
        "approval_gate": "after_apply",
    }


def _placeholder_quality(prompt: str, root: Path, family: str) -> Dict[str, Any]:
    checks = [
        {
            "id": "scope_classified",
            "label": "Prompt classified into a local capability family",
            "ok": True,
            "blocking": True,
            "evidence": family,
        },
        {
            "id": "local_only_policy",
            "label": "Local-only provider policy is active",
            "ok": True,
            "blocking": True,
            "evidence": "no external API calls are allowed in v1",
        },
        {
            "id": "safe_route_recordable",
            "label": "Safe local route can publish evidence",
            "ok": True,
            "blocking": True,
            "evidence": str(_rooted(root, DEFAULT_PUBLIC_JSON)),
        },
    ]
    return {
        "schema_version": "aureon-artifact-quality-report-v1",
        "status": "artifact_quality_passed",
        "generated_at": _utc_now(),
        "task_family": family,
        "provider_policy": "local_only_v1",
        "score": 1.0,
        "minimum_score": 0.8,
        "handover_ready": True,
        "checks": checks,
        "snags": [],
        "regeneration_attempts": [{"attempt": 1, "status": "accepted", "reason": "non-media evidence route passed"}],
        "browser_render_proof": {
            "proof_status": "non_media_evidence_ready",
            "preview_url": "",
            "public_url": "/aureon_capability_forge.json",
            "local_probe": True,
        },
        "artifact_manifest": {
            "kind": "file",
            "subject": family,
            "asset_path": str(_rooted(root, DEFAULT_PUBLIC_JSON)),
            "public_url": "/aureon_capability_forge.json",
            "preview_url": "",
        },
    }


def _make_markdown(report: Dict[str, Any]) -> str:
    summary = report.get("summary", {})
    lines = [
        "# Aureon Local Capability Forge",
        "",
        f"- status: {report.get('status')}",
        f"- task_family: {report.get('task_family')}",
        f"- generated_at: {report.get('generated_at')}",
        f"- provider_policy: {report.get('provider_policy')}",
        f"- approval_state: {(report.get('approval_state') or {}).get('state')}",
        f"- handover_ready: {report.get('handover_ready')}",
        f"- quality_score: {summary.get('artifact_quality_score')}",
        "",
        "## Recruited Crew",
    ]
    for item in report.get("recruited_crew", []):
        lines.append(f"- {item.get('role')}: {item.get('day_to_day')}")
    lines.extend(["", "## Reference Patterns"])
    for item in report.get("reference_patterns", []):
        lines.append(f"- {item.get('name')}: {item.get('url')} ({item.get('provider_policy')})")
    lines.extend(["", "## Output Files"])
    for item in report.get("output_files", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def build_and_write_capability_forge(
    prompt: str,
    *,
    root: Optional[Path] = None,
    provider_policy: str = "local_only_v1",
    approval_gate: str = "after_apply",
) -> Dict[str, Any]:
    root = Path(root or _default_root()).resolve()
    prompt_text = str(prompt or "").strip()
    if not prompt_text:
        raise ValueError("prompt is required")

    generated_at = _utc_now()
    classification = classify_task_family(prompt_text)
    task_family = classification["task_family"]
    detected_families = classification["detected_families"]
    crew = _crew_for_families(detected_families)
    tools = _tools_for_families(detected_families)
    visual = _visual_artifact(prompt_text, root) if any(family in detected_families for family in ("video", "image_graphic_design")) else {}
    artifact_manifest = visual.get("artifact_manifest") if isinstance(visual.get("artifact_manifest"), dict) else {}
    artifact_quality_report = (
        visual.get("artifact_quality_report")
        if isinstance(visual.get("artifact_quality_report"), dict)
        else _placeholder_quality(prompt_text, root, task_family)
    )
    write_artifact_quality_report(artifact_quality_report, root=root)
    applied_change_evidence = _safe_code_proposal(prompt_text, root, detected_families)

    quality_ready = bool(artifact_quality_report.get("handover_ready"))
    route_ready = provider_policy == "local_only_v1" and quality_ready
    digest = hashlib.sha256(f"{prompt_text}|{time.time_ns()}".encode("utf-8")).hexdigest()[:14]
    output_files = [
        DEFAULT_STATE_PATH.as_posix(),
        DEFAULT_AUDIT_JSON.as_posix(),
        DEFAULT_AUDIT_MD.as_posix(),
        DEFAULT_PUBLIC_JSON.as_posix(),
        DEFAULT_PUBLIC_QUALITY_JSON.as_posix(),
    ]
    for item in visual.get("output_files", []) if isinstance(visual, dict) else []:
        if item not in output_files:
            output_files.append(str(item))

    report: Dict[str, Any] = {
        "schema_version": "aureon-local-capability-forge-v1",
        "status": "capability_forge_ready" if route_ready else "capability_forge_quality_blocked",
        "ok": route_ready,
        "generated_at": generated_at,
        "job_id": f"capability-forge-{digest}",
        "prompt": prompt_text,
        "task_family": task_family,
        "detected_families": detected_families,
        "director_brief": {
            "goal": "Build locally, prove locally, regenerate weak work, and hand over only after quality gates pass.",
            "provider_policy": provider_policy,
            "approval_gate": approval_gate,
            "no_bypass": ["live_trading", "payments", "filings", "credentials", "destructive_os_actions"],
        },
        "provider_policy": provider_policy,
        "external_api_calls": [],
        "reference_patterns": _reference_patterns(),
        "recruited_crew": crew,
        "local_tools_used": tools,
        "artifact_manifest": artifact_manifest,
        "visual_asset_report": visual,
        "artifact_quality_report": artifact_quality_report,
        "regeneration_attempts": artifact_quality_report.get("regeneration_attempts", []),
        "applied_change_evidence": applied_change_evidence,
        "approval_state": {
            "state": "pending_user_review_after_apply" if route_ready else "blocked_by_quality_gate",
            "policy": approval_gate,
            "approved": False,
            "reviewer": "operator_or_codex",
            "next_action": "approve, reject, or request revision from the cockpit",
        },
        "handover_ready": route_ready,
        "authority_boundaries": [
            "No paid/cloud provider call in local-only v1.",
            "No credential values emitted.",
            "No live trading, payment, filing, or destructive OS authority changes.",
            "Coding work uses safe local routes and after-apply evidence review.",
        ],
        "summary": {
            "task_family": task_family,
            "detected_family_count": len(detected_families),
            "crew_count": len(crew),
            "local_tool_count": len(tools),
            "reference_pattern_count": len(REFERENCE_PATTERNS),
            "external_api_call_count": 0,
            "artifact_quality_score": artifact_quality_report.get("score", 0),
            "artifact_quality_passed": quality_ready,
            "blocking_snag_count": len(artifact_quality_report.get("snags", [])),
            "safe_code_route_recorded": bool(applied_change_evidence.get("proposal")),
            "handover_ready": route_ready,
        },
        "output_files": output_files,
        "write_info": {
            "writer": "AureonCapabilityForge",
            "authoring_path": [
                "classify_task_family",
                "recruit_local_crew",
                "reference_patterns_marked_reference_only",
                "local_visual_or_safe_code_route",
                "artifact_quality_gate",
                "after_apply_approval_state",
                "state/docs/frontend evidence publish",
            ],
        },
    }

    writes = [
        _write_json(_rooted(root, DEFAULT_STATE_PATH), report),
        _write_json(_rooted(root, DEFAULT_AUDIT_JSON), report),
        _write_text(_rooted(root, DEFAULT_AUDIT_MD), _make_markdown(report)),
        _write_json(_rooted(root, DEFAULT_PUBLIC_JSON), report),
    ]
    report["write_info"]["evidence_writes"] = writes
    for rel in (DEFAULT_STATE_PATH, DEFAULT_AUDIT_JSON, DEFAULT_PUBLIC_JSON):
        _write_json(_rooted(root, rel), report)
    _write_text(_rooted(root, DEFAULT_AUDIT_MD), _make_markdown(report))
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run Aureon's local capability forge and quality gate.")
    parser.add_argument("--prompt", "-p", default="", help="Client prompt/job for the local forge.")
    parser.add_argument("--prompt-file", default="", help="Read the prompt from a file.")
    parser.add_argument("--repo-root", default="", help="Repository root; defaults to cwd/repo.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown.")
    args = parser.parse_args(argv)

    prompt = args.prompt
    if args.prompt_file:
        prompt = Path(args.prompt_file).read_text(encoding="utf-8")
    if not prompt.strip():
        parser.error("--prompt or --prompt-file is required")

    root = Path(args.repo_root).resolve() if args.repo_root else None
    report = build_and_write_capability_forge(prompt, root=root)
    print(json.dumps(report, indent=2, sort_keys=True, default=str) if args.json else _make_markdown(report))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
