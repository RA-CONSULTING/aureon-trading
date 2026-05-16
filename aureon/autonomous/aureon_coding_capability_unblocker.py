from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from aureon.autonomous.aureon_capability_forge import REPO_ROOT, classify_task_family


DEFAULT_STATE_PATH = Path("state/aureon_coding_capability_unblocker_last_run.json")
DEFAULT_AUDIT_JSON = Path("docs/audits/aureon_coding_capability_unblocker.json")
DEFAULT_AUDIT_MD = Path("docs/audits/aureon_coding_capability_unblocker.md")
DEFAULT_PUBLIC_JSON = Path("frontend/public/aureon_coding_capability_unblocker.json")

CODING_BRIDGE_EVIDENCE_PATHS = [
    Path("state/aureon_coding_organism_last_run.json"),
    Path("docs/audits/aureon_coding_organism_bridge.json"),
    Path("frontend/public/aureon_coding_organism_bridge.json"),
]

STATE_INPUTS = [
    Path("state/aureon_coding_organism_last_run.json"),
    Path("state/aureon_capability_forge_last_run.json"),
    Path("state/aureon_capability_stress_audit_last_run.json"),
    Path("state/aureon_complex_build_stress_audit_last_run.json"),
    Path("state/aureon_agent_creative_process_guardian_last_run.json"),
    Path("frontend/public/aureon_coding_agent_skill_base.json"),
]

MANUAL_AUTHORITY_PATTERNS = {
    "live_trading": ("live trade", "order mutation", "exchange mutation", "live trading", "order_intent"),
    "credential_boundary": ("credential reveal", "api key", "secret", "password", "private key"),
    "payment_boundary": ("payment", "top-up", "card charge", "bank transfer"),
    "official_filing_boundary": ("official filing", "hmrc", "companies house", "tax filing"),
    "destructive_os_boundary": ("delete the repo", "wipe", "format disk", "destructive os"),
}

AUTONOMOUS_CODING_PATTERNS = {
    "agentcore_unavailable": ("agentcore not available", "agentcore_required"),
    "missing_domain_worker": ("missing_domain_specific_worker", "domain_specific_worker_present", "generic adaptive capsule"),
    "test_failure": ("pytest", "tests need attention", "test failed", "build failed"),
    "browser_proof_missing": ("browser proof", "preview missing", "playback", "render proof"),
    "dependency_missing": ("module not found", "package not found", "dependency", "importerror"),
    "source_gap": ("open source", "github", "documentation", "research", "official docs"),
}

CODING_GATE_BLUEPRINTS = [
    {
        "id": "scope_defaulting_gate",
        "title": "Scope Defaulting Gate",
        "purpose": "Turn incomplete client prompts into assumed safe defaults instead of stopping the coding lane.",
        "authority": "autonomous_with_recorded_assumptions",
    },
    {
        "id": "local_forge_gate",
        "title": "Local Capability Forge Gate",
        "purpose": "Build app/tool/media/UI artifacts locally when AgentCore-style tools are unavailable.",
        "authority": "autonomous_apply_generated_artifacts",
    },
    {
        "id": "safe_code_authoring_gate",
        "title": "Safe Code Authoring Gate",
        "purpose": "Apply repo code only through scoped local proposal/apply routes and keep diff evidence.",
        "authority": "autonomous_safe_repo_apply",
    },
    {
        "id": "adaptive_skill_acquisition_gate",
        "title": "Adaptive Skill Acquisition Gate",
        "purpose": "When a domain worker is missing, research the pattern and create a new local worker with tests.",
        "authority": "autonomous_skill_build",
    },
    {
        "id": "dependency_install_gate",
        "title": "Project Dependency Gate",
        "purpose": "Install or validate dependencies inside the repo environment only, then test the result.",
        "authority": "autonomous_project_local_install",
    },
    {
        "id": "open_source_research_gate",
        "title": "Open Source Research Gate",
        "purpose": "Search GitHub, docs, and package sources as read-only reference material before implementing Aureon's own code.",
        "authority": "read_only_external_research",
    },
    {
        "id": "test_and_run_gate",
        "title": "Test And Run Gate",
        "purpose": "Run focused pytest, frontend builds, Playwright smoke checks, and generated artifact probes.",
        "authority": "autonomous_local_validation",
    },
    {
        "id": "quality_handover_gate",
        "title": "No Half-Baked Handover Gate",
        "purpose": "Hide or hold weak outputs until quality reports, previews, tests, and snags pass.",
        "authority": "autonomous_quality_hold",
    },
    {
        "id": "manual_authority_boundary_gate",
        "title": "Manual Authority Boundary Gate",
        "purpose": "Keep live trading, payments, official filing, credential reveal, and destructive OS actions out of coding autonomy.",
        "authority": "manual_only_boundary",
    },
]

SOURCE_DISCOVERY_ROUTES = [
    {
        "id": "local_repo_first",
        "name": "Local repo and vault search",
        "mode": "read_only",
        "allowed_inputs": ["repo files", "docs/audits", "docs/research", "frontend/public evidence"],
        "allowed_outputs": ["source packets", "implementation hints", "gap list"],
    },
    {
        "id": "github_open_source_reference",
        "name": "GitHub and open-source reference scan",
        "mode": "read_only_reference",
        "allowed_inputs": ["public repos", "README", "docs", "examples", "package metadata", "license files"],
        "allowed_outputs": ["source-linked research packets", "license notes", "design patterns"],
        "blocked_outputs": ["raw credential capture", "large copied code dumps", "unreviewed vendored code", "license-unknown import"],
    },
    {
        "id": "official_docs_reference",
        "name": "Official documentation reference scan",
        "mode": "read_only_reference",
        "allowed_inputs": ["official docs", "API references", "framework guides"],
        "allowed_outputs": ["implementation constraints", "version notes", "test expectations"],
    },
    {
        "id": "local_adaptation_build",
        "name": "Aureon local adaptation build",
        "mode": "autonomous_local_apply",
        "allowed_inputs": ["source packets", "local repo patterns", "client prompt"],
        "allowed_outputs": ["new local worker", "scoped patch", "tests", "quality report"],
        "blocked_outputs": ["unattributed copied source", "unsafe mutation", "secret material"],
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


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _flatten_strings(value: Any, *, limit: int = 420) -> Iterable[str]:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key) in {
                "coding_capability_unblocker",
                "detected_blockers",
                "autonomous_work_orders",
                "autonomous_gates",
                "source_discovery_routes",
                "source_packets",
                "write_info",
            }:
                continue
            if isinstance(key, str):
                yield key[:limit]
            yield from _flatten_strings(item, limit=limit)
    elif isinstance(value, list):
        for item in value:
            yield from _flatten_strings(item, limit=limit)
    elif isinstance(value, str):
        text = re.sub(r"\s+", " ", value).strip()
        if text:
            yield text[:limit]


def _contains_any(text: str, needles: Iterable[str]) -> bool:
    lower = str(text or "").lower()
    return any(str(needle).lower() in lower for needle in needles)


def _load_state_inputs(root: Path) -> Dict[str, Dict[str, Any]]:
    states: Dict[str, Dict[str, Any]] = {}
    for rel_path in STATE_INPUTS:
        payload = _read_json(_rooted(root, rel_path))
        if payload:
            states[rel_path.as_posix()] = payload
    return states


def _state_signal(states: Dict[str, Dict[str, Any]], *keys: str) -> Any:
    for payload in states.values():
        cursor: Any = payload
        for key in keys:
            if not isinstance(cursor, dict):
                cursor = None
                break
            cursor = cursor.get(key)
        if cursor not in (None, "", [], {}):
            return cursor
    return None


def _build_gate_status(root: Path, states: Dict[str, Dict[str, Any]], prompt: str) -> List[Dict[str, Any]]:
    root_checks = {
        "capability_forge": (root / "aureon" / "autonomous" / "aureon_capability_forge.py").exists(),
        "safe_code_control": (root / "aureon" / "autonomous" / "aureon_safe_code_control.py").exists(),
        "complex_stress": (root / "aureon" / "autonomous" / "aureon_complex_build_stress_audit.py").exists(),
        "playwright_spec": (root / "frontend" / "tests" / "capability-forge.spec.ts").exists(),
        "frontend_package": (root / "frontend" / "package.json").exists(),
        "pytest_tests": (root / "tests").exists(),
    }
    stress_ok = bool(_state_signal(states, "ok"))
    complex_status = str(_state_signal(states, "status") or "")
    gates: List[Dict[str, Any]] = []
    for blueprint in CODING_GATE_BLUEPRINTS:
        gate_id = blueprint["id"]
        status = "ready"
        gate_open = True
        evidence = "configured"
        next_action = "Use this gate when the coding route reaches it."

        if gate_id == "local_forge_gate":
            gate_open = root_checks["capability_forge"]
            evidence = "capability forge module present" if gate_open else "capability forge module missing"
            next_action = "Route build/app/media requests through aureon_capability_forge before declaring blocked."
        elif gate_id == "safe_code_authoring_gate":
            gate_open = root_checks["safe_code_control"]
            evidence = "SafeCodeControl present" if gate_open else "SafeCodeControl missing"
            next_action = "Create proposals and apply only scoped repo patches through safe local routes."
        elif gate_id == "adaptive_skill_acquisition_gate":
            gate_open = root_checks["capability_forge"]
            evidence = "adaptive skill generator present" if gate_open else "adaptive skill generator missing"
            next_action = "When a skill is missing, create a domain worker, run tests, and publish a quality report."
        elif gate_id == "dependency_install_gate":
            gate_open = root_checks["frontend_package"] or root_checks["pytest_tests"]
            evidence = "repo-local dependency surfaces detected" if gate_open else "no repo-local dependency surface detected"
            next_action = "Use project-local venv/npm only; record installs and rerun verification."
        elif gate_id == "open_source_research_gate":
            evidence = "GitHub/open-source routes are read-only reference routes"
            next_action = "Search sources, capture source packets, review license/security, then build Aureon's own implementation."
        elif gate_id == "test_and_run_gate":
            gate_open = root_checks["pytest_tests"] or root_checks["playwright_spec"]
            evidence = "pytest or Playwright surfaces present" if gate_open else "no validation surface detected"
            next_action = "Run focused tests/build/smoke after each generated artifact or repo patch."
        elif gate_id == "quality_handover_gate":
            gate_open = root_checks["complex_stress"] and ("certified" in complex_status or stress_ok)
            evidence = complex_status or "complex stress certification not run yet"
            next_action = "Run complex stress certification and hold handover until fake passes are zero."
        elif gate_id == "manual_authority_boundary_gate":
            gate_open = True
            evidence = "manual-only boundaries remain active"
            next_action = "Never convert trading, payment, filing, credential, or destructive OS authority into coding autonomy."
        elif gate_id == "scope_defaulting_gate":
            task = classify_task_family(prompt or "coding task")
            evidence = f"task family {task.get('task_family')}; assumptions allowed when non-destructive"
            next_action = "If the prompt is incomplete, choose safe defaults and write assumptions into evidence."

        if not gate_open:
            status = "needs_repair"
        if gate_id == "manual_authority_boundary_gate":
            status = "manual_hold_ready"
        gates.append(
            {
                **blueprint,
                "status": status,
                "open": gate_open,
                "evidence": evidence,
                "next_action": next_action,
            }
        )
    return gates


def _classify_blocker(text: str) -> Dict[str, Any]:
    lower = text.lower()
    for boundary, needles in MANUAL_AUTHORITY_PATTERNS.items():
        if _contains_any(lower, needles):
            return {
                "kind": boundary,
                "classification": "manual_authority_hold",
                "gate": "manual_authority_boundary_gate",
                "coding_blocker": False,
                "autonomous_resolution": "blocked_manual_boundary",
            }
    for kind, needles in AUTONOMOUS_CODING_PATTERNS.items():
        if _contains_any(lower, needles):
            gate = {
                "agentcore_unavailable": "local_forge_gate",
                "missing_domain_worker": "adaptive_skill_acquisition_gate",
                "test_failure": "test_and_run_gate",
                "browser_proof_missing": "test_and_run_gate",
                "dependency_missing": "dependency_install_gate",
                "source_gap": "open_source_research_gate",
            }.get(kind, "safe_code_authoring_gate")
            return {
                "kind": kind,
                "classification": "autonomous_coding_gate",
                "gate": gate,
                "coding_blocker": True,
                "autonomous_resolution": "repair_or_reroute_through_gate",
            }
    return {
        "kind": "unknown_attention",
        "classification": "attention_review",
        "gate": "safe_code_authoring_gate",
        "coding_blocker": True,
        "autonomous_resolution": "convert_to_explicit_work_order",
    }


def _extract_blockers(states: Dict[str, Dict[str, Any]], prompt: str) -> List[Dict[str, Any]]:
    candidates: List[str] = []
    for payload in states.values():
        for text in _flatten_strings(payload):
            lower = text.lower()
            if any(token in lower for token in ("blocked", "failed", "missing", "not available", "attention", "snag", "fake pass")):
                candidates.append(text)
    if prompt:
        candidates.append(prompt)

    seen = set()
    blockers: List[Dict[str, Any]] = []
    for text in candidates:
        key = text[:220].lower()
        if key in seen:
            continue
        seen.add(key)
        classified = _classify_blocker(text)
        lower = text.lower()
        if classified["classification"] == "manual_authority_hold" and (
            lower.startswith("review generated") or lower.startswith("check generated")
        ):
            continue
        if classified["classification"] == "attention_review":
            if any(
                positive in lower
                for positive in (
                    "no blocking snags",
                    "no blocking",
                    "exists, preview",
                    "works, and no",
                    "unblocked_with_autonomous_gates",
                    "ready_for_client",
                )
            ):
                continue
            padded = f" {lower} "
            coding_terms = (
                "agentcore",
                "code",
                "coding",
                "write_file",
                "create_dir",
                "read_file",
                "list_dir",
                "tool",
                "skill",
                "dependency",
                "test",
                "build",
                "browser",
                "preview",
                "capability",
                " repo ",
                "repository",
            )
            if not any(term in padded for term in coding_terms):
                continue
        blockers.append(
            {
                "id": f"blocker_{len(blockers) + 1}",
                "source_text": text[:360],
                **classified,
            }
        )
        if len(blockers) >= 36:
            break
    return blockers


def _research_packet_index(root: Path, prompt: str) -> List[Dict[str, Any]]:
    needles = [item for item in re.findall(r"[a-zA-Z][a-zA-Z0-9_+-]{3,}", prompt.lower())[:10]]
    search_roots = [root / "docs" / "research", root / "docs", root / "aureon"]
    packets: List[Dict[str, Any]] = []
    for search_root in search_roots:
        if not search_root.exists():
            continue
        for path in list(search_root.rglob("*.md"))[:400] + list(search_root.rglob("*.json"))[:400]:
            if len(packets) >= 12:
                return packets
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            lower = text.lower()
            score = sum(1 for needle in needles if needle in lower)
            if score <= 0 and "gary leckey" not in lower and "aureon" not in lower:
                continue
            packets.append(
                {
                    "source_path": str(path.relative_to(root) if path.is_relative_to(root) else path),
                    "topic_tags": sorted(set(["local_research"] + [needle for needle in needles if needle in lower]))[:8],
                    "confidence": min(0.95, 0.45 + score * 0.08 + (0.15 if "gary leckey" in lower else 0)),
                    "prompt_use_guidance": "Use as a compact local source packet; do not stuff the whole file into the prompt.",
                    "summary": re.sub(r"\s+", " ", text.strip())[:260],
                }
            )
    return packets


def _autonomous_work_orders(gates: List[Dict[str, Any]], blockers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    work_orders: List[Dict[str, Any]] = []
    for blocker in blockers:
        if blocker.get("classification") == "manual_authority_hold":
            continue
        work_orders.append(
            {
                "id": f"unblock_{blocker.get('kind')}_{len(work_orders) + 1}",
                "source_blocker": blocker.get("id"),
                "gate": blocker.get("gate"),
                "priority": "P80" if blocker.get("kind") in {"agentcore_unavailable", "missing_domain_worker"} else "P60",
                "action": "research_build_test_publish",
                "authority": next((gate.get("authority") for gate in gates if gate.get("id") == blocker.get("gate")), "autonomous_safe_route"),
                "acceptance": "Aureon produces a source-linked implementation, local tests/build/browser proof, quality report, and zero fake passes.",
            }
        )
    if not work_orders:
        work_orders.append(
            {
                "id": "unblock_next_unknown_skill",
                "gate": "adaptive_skill_acquisition_gate",
                "priority": "P70",
                "action": "standby_for_next_missing_skill",
                "authority": "autonomous_skill_build",
                "acceptance": "Next missing coding skill becomes a generated local worker with tests instead of a hard stop.",
            }
        )
    return work_orders


def _make_markdown(report: Dict[str, Any]) -> str:
    summary = report.get("summary", {})
    lines = [
        "# Aureon Coding Capability Unblocker",
        "",
        f"- status: {report.get('status')}",
        f"- gates: {summary.get('ready_gate_count')}/{summary.get('gate_count')} ready",
        f"- converted coding blockers: {summary.get('converted_coding_blocker_count')}",
        f"- manual authority holds: {summary.get('manual_authority_hold_count')}",
        f"- work orders: {summary.get('work_order_count')}",
        "",
        "## Gates",
    ]
    for gate in report.get("autonomous_gates", []):
        lines.append(f"- {gate.get('id')}: {gate.get('status')} - {gate.get('next_action')}")
    lines.extend(["", "## Work Orders"])
    for work_order in report.get("autonomous_work_orders", []):
        lines.append(f"- {work_order.get('id')}: {work_order.get('priority')} via {work_order.get('gate')}")
    return "\n".join(lines) + "\n"


def _attach_to_coding_bridge_evidence(root: Path, report: Dict[str, Any]) -> List[Dict[str, Any]]:
    writes: List[Dict[str, Any]] = []
    compact = dict(report)
    compact.pop("write_info", None)
    for rel_path in CODING_BRIDGE_EVIDENCE_PATHS:
        path = _rooted(root, rel_path)
        if not path.exists():
            continue
        payload = _read_json(path)
        if not payload:
            continue
        payload["coding_capability_unblocker"] = compact
        summary = payload.setdefault("summary", {})
        if isinstance(summary, dict):
            report_summary = compact.get("summary") or {}
            summary["coding_capability_unblocker_status"] = compact.get("status")
            summary["coding_capability_ready_gate_count"] = report_summary.get("ready_gate_count", 0)
            summary["coding_capability_blockers_converted"] = report_summary.get("converted_coding_blocker_count", 0)
        writes.append(_write_json(path, payload))
    return writes


def build_and_write_coding_capability_unblocker(
    prompt: str = "",
    *,
    root: Optional[Path] = None,
    attach_to_bridge: bool = True,
) -> Dict[str, Any]:
    root = Path(root or _default_root()).resolve()
    states = _load_state_inputs(root)
    gates = _build_gate_status(root, states, prompt)
    blockers = _extract_blockers(states, prompt)
    source_packets = _research_packet_index(root, prompt)
    work_orders = _autonomous_work_orders(gates, blockers)

    converted = [item for item in blockers if item.get("classification") == "autonomous_coding_gate"]
    manual_holds = [item for item in blockers if item.get("classification") == "manual_authority_hold"]
    gate_failures = [gate for gate in gates if gate.get("status") == "needs_repair"]
    status = "coding_capabilities_unblocked_with_autonomous_gates"
    if gate_failures:
        status = "coding_capabilities_need_gate_repairs"
    report: Dict[str, Any] = {
        "schema_version": "aureon-coding-capability-unblocker-v1",
        "status": status,
        "ok": not gate_failures,
        "generated_at": _utc_now(),
        "prompt": prompt,
        "task_family": classify_task_family(prompt or "advanced coding project"),
        "principle": "Missing coding skills, tools, dependencies, and proof become autonomous gates; unsafe authority remains manual.",
        "provider_policy": "local_first_with_read_only_external_research",
        "autonomous_gates": gates,
        "detected_blockers": blockers,
        "source_discovery_routes": SOURCE_DISCOVERY_ROUTES,
        "source_packets": source_packets,
        "autonomous_work_orders": work_orders,
        "safety_boundaries": [
            "no live trading mutation",
            "no payment mutation",
            "no official filing mutation",
            "no credential reveal",
            "no destructive OS action",
            "no unreviewed license-unknown code import",
        ],
        "runtime_contract": {
            "on_missing_skill": "search local repo, build source packet, read GitHub/open-source references, implement a local worker, test, then publish quality evidence",
            "on_agentcore_missing": "reroute to local capability forge and safe code authoring gate",
            "on_dependency_missing": "install only into repo-local venv/node_modules where safe, then rerun validation",
            "on_external_code_found": "analyze patterns and license; do not paste large/raw third-party code into Aureon without review",
            "on_manual_boundary": "hold and explain the human-only gate",
        },
        "summary": {
            "gate_count": len(gates),
            "ready_gate_count": sum(1 for gate in gates if gate.get("open")),
            "gate_repair_count": len(gate_failures),
            "detected_blocker_count": len(blockers),
            "converted_coding_blocker_count": len(converted),
            "manual_authority_hold_count": len(manual_holds),
            "source_packet_count": len(source_packets),
            "work_order_count": len(work_orders),
            "external_research_routes_ready": len([route for route in SOURCE_DISCOVERY_ROUTES if "reference" in route.get("mode", "")]),
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
    bridge_writes = _attach_to_coding_bridge_evidence(root, report) if attach_to_bridge else []
    report["write_info"] = {"evidence_writes": writes, "coding_bridge_evidence_writes": bridge_writes}
    for rel_path in (DEFAULT_STATE_PATH, DEFAULT_AUDIT_JSON, DEFAULT_PUBLIC_JSON):
        _write_json(_rooted(root, rel_path), report)
    _write_text(_rooted(root, DEFAULT_AUDIT_MD), _make_markdown(report))
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Publish Aureon's coding capability unblocker gates.")
    parser.add_argument("--prompt", default="", help="Optional coding/client prompt to classify.")
    parser.add_argument("--root", default="", help="Repository root. Defaults to current Aureon repo.")
    parser.add_argument("--json", action="store_true", help="Print the JSON report.")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve() if args.root else None
    report = build_and_write_coding_capability_unblocker(args.prompt, root=root)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        summary = report.get("summary", {})
        print(
            f"{report.get('status')}: gates={summary.get('ready_gate_count')}/{summary.get('gate_count')} "
            f"converted={summary.get('converted_coding_blocker_count')} manual_holds={summary.get('manual_authority_hold_count')}"
        )
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
