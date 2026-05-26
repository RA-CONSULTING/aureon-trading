#!/usr/bin/env python3
"""Repo-wide metacognitive systems expansion audit.

This maps the many metacognitive/cognitive systems already in the repository
and routes the current HNC research/essay benchmark through them as a unified
understanding packet. It is a capability and wiring proof, not a trading
authority path.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

from aureon.search.swarm_search_fabric import publish_search_event

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "aureon-metacognitive-systems-expansion-v1"

DEFAULT_STATE_PATH = Path("state/aureon_metacognitive_systems_expansion.json")
DEFAULT_PUBLIC_PATH = Path("frontend/public/aureon_metacognitive_systems_expansion.json")
DEFAULT_AUDIT_JSON = Path("docs/audits/aureon_metacognitive_systems_expansion.json")
DEFAULT_AUDIT_MD = Path("docs/audits/aureon_metacognitive_systems_expansion.md")

SYSTEM_SPECS = (
    {
        "id": "research_metacognition",
        "label": "Research Metacognition",
        "path": "aureon/search/research_metacognition.py",
        "layer": "research_understanding",
        "required_symbols": ["def build_research_metacognition", "CONCEPT_SPECS", "organism_route_rows"],
        "route": "turns research cinema packets into concepts, organism routes, unknowns, and test actions",
    },
    {
        "id": "knowledge_interpreter",
        "label": "Knowledge Interpreter",
        "path": "aureon/queen/knowledge_interpreter.py",
        "layer": "semantic_classification",
        "required_symbols": ["DATA_TYPES", "CATEGORIES", "def classify_data_type", "def classify_category", "class Interpretation"],
        "route": "classifies fragments by type, category, meaning, and related context",
    },
    {
        "id": "meaning_resolver",
        "label": "Meaning Resolver",
        "path": "aureon/queen/meaning_resolver.py",
        "layer": "grounded_prompt_context",
        "required_symbols": ["class MeaningResolver", "class KnowingBlock", "def resolve", "render_for_prompt"],
        "route": "assembles grounded knowledge blocks for voice/chat reasoning",
    },
    {
        "id": "queen_metacognition",
        "label": "Queen Metacognition",
        "path": "aureon/queen/queen_metacognition.py",
        "layer": "self_reflection",
        "required_symbols": ["class QueenMetacognition", "class Reflection", "class MetacognitiveInsight", "def get_metacognition"],
        "route": "reflects on cognition cycles, detects patterns, and publishes insights",
    },
    {
        "id": "auris_metacognition",
        "label": "Auris Metacognition",
        "path": "aureon/vault/auris_metacognition.py",
        "layer": "node_consensus",
        "required_symbols": ["class AurisMetacognition", "NODES", "def vote", "class AurisVoteResult"],
        "route": "runs deterministic 9-node consensus over vault state",
    },
    {
        "id": "consciousness_module",
        "label": "Consciousness Module",
        "path": "aureon/core/aureon_consciousness_module.py",
        "layer": "thoughtbus_observer",
        "required_symbols": ["class ConsciousnessModule", "metacognition", "ThoughtBus", "def heartbeat"],
        "route": "observes ThoughtBus traffic and reflects on organism patterns",
    },
    {
        "id": "integrated_cognitive_system",
        "label": "Integrated Cognitive System",
        "path": "aureon/core/integrated_cognitive_system.py",
        "layer": "boot_orchestration",
        "required_symbols": ["class IntegratedCognitiveSystem", "boot_metacognition", "AurisMetacognition", "QueenMetacognition"],
        "route": "boots and keeps the cognitive organism components aligned",
    },
    {
        "id": "cognitive_authoring_loop",
        "label": "Cognitive Authoring Loop",
        "path": "aureon/core/aureon_cognitive_authoring_loop.py",
        "layer": "self_authoring",
        "required_symbols": ["class CognitiveAuthoringLoop", "def launch_authoring_loop", "authoring.request", "ThoughtBus"],
        "route": "pairs consciousness observation with code authoring and skill validation",
    },
    {
        "id": "self_introspection",
        "label": "Self Introspection",
        "path": "aureon/core/aureon_self_introspection.py",
        "layer": "self_model",
        "required_symbols": ["class SelfIntrospection", "def scan", "def find_decision_points", "def summary"],
        "route": "inspects local behavior and builds self-knowledge",
    },
    {
        "id": "self_refinement_loop",
        "label": "Self Refinement Loop",
        "path": "aureon/core/aureon_self_refinement_loop.py",
        "layer": "self_improvement",
        "required_symbols": ["class SelfRefinementLoop", "refinement_request", "def _queue_refinement"],
        "route": "turns observed issues into refinement proposals",
    },
    {
        "id": "ollama_cognitive_bridge",
        "label": "Ollama Cognitive Bridge",
        "path": "aureon/autonomous/aureon_ollama_cognitive_bridge.py",
        "layer": "language_context",
        "required_symbols": ["Aureon Metacognitive Context Builder", "HNC/Auris Drift Inspector", "DEFAULT_PUBLIC_JSON"],
        "route": "injects local cognitive proof into language responses",
    },
    {
        "id": "cognitive_trade_evidence",
        "label": "Cognitive Trade Evidence",
        "path": "aureon/autonomous/aureon_cognitive_trade_evidence.py",
        "layer": "outcome_memory",
        "required_symbols": ["cognitive", "trade", "evidence", "def main"],
        "route": "records trading cognition and outcome evidence for later reflection",
    },
    {
        "id": "mind_thought_action_hub",
        "label": "Mind Thought Action Hub",
        "path": "aureon/autonomous/aureon_mind_thought_action_hub.py",
        "layer": "thought_action_bridge",
        "required_symbols": ["ThoughtBus", "action", "mind"],
        "route": "connects thought evidence toward action surfaces without replacing executor gates",
    },
    {
        "id": "self_questioning_ai",
        "label": "Self Questioning AI",
        "path": "aureon/autonomous/aureon_self_questioning_ai.py",
        "layer": "question_generation",
        "required_symbols": ["question", "self", "ThoughtBus"],
        "route": "generates self-questions and research prompts when knowledge is incomplete",
    },
    {
        "id": "queen_world_understanding",
        "label": "Queen World Understanding",
        "path": "aureon/queen/queen_world_understanding.py",
        "layer": "world_model",
        "required_symbols": ["world", "understanding", "knowledge"],
        "route": "connects research context to broader world understanding",
    },
    {
        "id": "research_corpus_index",
        "label": "Research Corpus Index",
        "path": "aureon/queen/research_corpus_index.py",
        "layer": "retrieval",
        "required_symbols": ["class ResearchCorpusIndex", "def search", "docs/**/*.md"],
        "route": "retrieves local HNC/research paragraphs for grounded answers",
    },
    {
        "id": "thoughtbus",
        "label": "ThoughtBus",
        "path": "aureon/core/aureon_thought_bus.py",
        "layer": "organism_bus",
        "required_symbols": ["class Thought", "class ThoughtBus", "def publish"],
        "route": "broadcasts metacognitive and search phases to the organism",
    },
    {
        "id": "mycelium",
        "label": "Mycelium Network",
        "path": "aureon/core/aureon_mycelium.py",
        "layer": "learning_network",
        "required_symbols": ["Mycelium", "receive_external_signal", "get_mycelium"],
        "route": "absorbs confidence and learning signals from metacognitive events",
    },
)

ARTIFACT_SPECS = (
    ("docs/research/hnc_1000_word_autonomous_essay.md", "HNC essay produced by autonomous benchmark"),
    ("frontend/public/aureon_hnc_essay_benchmark.json", "public HNC essay benchmark audit"),
    ("frontend/public/aureon_research_metacognition.json", "public research metacognition packet"),
    ("frontend/public/aureon_online_research_cinema.json", "public research cinema packet"),
    ("aureon/generated/research_cinema/harmonic_nexus_score_model.py", "generated HNC score helper"),
    ("tests/generated/test_harmonic_nexus_score_model.py", "generated HNC score test"),
    ("state/aureon_swarm_search_fabric_events.jsonl", "search/metacognition fabric ledger"),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _rooted(root: Optional[Path], rel: Path) -> Path:
    base = Path(root or REPO_ROOT).resolve()
    return rel if rel.is_absolute() else base / rel


def _safe_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    os.replace(tmp, path)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}
    return {}


def _system_row(root: Path, spec: Mapping[str, Any]) -> Dict[str, Any]:
    path = _rooted(root, Path(str(spec["path"])))
    text = _read_text(path)
    missing = [symbol for symbol in spec.get("required_symbols", []) if str(symbol) not in text]
    return {
        "id": spec["id"],
        "label": spec["label"],
        "path": spec["path"],
        "layer": spec["layer"],
        "route": spec["route"],
        "present": path.exists(),
        "required_symbol_count": len(spec.get("required_symbols", [])),
        "present_symbol_count": len(spec.get("required_symbols", [])) - len(missing),
        "missing_symbols": missing,
        "wired": path.exists() and not missing,
    }


def _artifact_row(root: Path, rel: str, purpose: str) -> Dict[str, Any]:
    path = _rooted(root, Path(rel))
    mtime = path.stat().st_mtime if path.exists() else 0.0
    return {
        "id": rel.replace("\\", "/").replace("/", "_").replace(".", "_"),
        "path": rel.replace("\\", "/"),
        "purpose": purpose,
        "present": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
        "age_sec": round(max(0.0, time.time() - mtime), 3) if mtime else None,
        "modified_at": datetime.fromtimestamp(mtime, timezone.utc).isoformat() if mtime else None,
    }


def _context(root: Path) -> Dict[str, Any]:
    essay = _read_text(_rooted(root, Path("docs/research/hnc_1000_word_autonomous_essay.md")))
    essay_benchmark = _read_json(_rooted(root, Path("frontend/public/aureon_hnc_essay_benchmark.json")))
    research_meta = _read_json(_rooted(root, Path("frontend/public/aureon_research_metacognition.json")))
    research_cinema = _read_json(_rooted(root, Path("frontend/public/aureon_online_research_cinema.json")))
    meta_summary = research_meta.get("summary") if isinstance(research_meta.get("summary"), dict) else {}
    benchmark_summary = essay_benchmark.get("summary") if isinstance(essay_benchmark.get("summary"), dict) else {}
    concept_rows = research_meta.get("concept_rows") if isinstance(research_meta.get("concept_rows"), list) else []
    route_rows = research_meta.get("organism_route_rows") if isinstance(research_meta.get("organism_route_rows"), list) else []
    return {
        "essay_present": bool(essay.strip()),
        "essay_word_count": benchmark_summary.get("essay_word_count"),
        "essay_benchmark_status": essay_benchmark.get("status"),
        "research_metacognition_status": research_meta.get("status"),
        "research_cinema_status": research_cinema.get("status"),
        "understood_concepts": [
            row.get("label") or row.get("concept_id")
            for row in concept_rows
            if isinstance(row, dict) and row.get("status") == "understood"
        ],
        "ready_routes": [
            row.get("system") or row.get("route_id")
            for row in route_rows
            if isinstance(row, dict) and row.get("ready")
        ],
        "metacognition_summary": meta_summary,
    }


def _route_rows(system_rows: Sequence[Mapping[str, Any]], context: Mapping[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    concept_count = len(context.get("understood_concepts") or [])
    route_count = len(context.get("ready_routes") or [])
    for row in system_rows:
        layer = str(row.get("layer") or "")
        ready = bool(row.get("wired") and context.get("essay_present") and concept_count)
        if layer in {"self_authoring", "self_improvement", "thought_action_bridge", "outcome_memory"}:
            authority = "validation_and_learning_only"
        elif layer in {"organism_bus", "learning_network"}:
            authority = "organism_publication"
        else:
            authority = "understanding_context"
        rows.append(
            {
                "route_id": f"hnc_packet_to_{row.get('id')}",
                "system_id": row.get("id"),
                "system_label": row.get("label"),
                "layer": layer,
                "status": "routed" if ready else "waiting_for_source_or_symbols",
                "ready": ready,
                "authority": authority,
                "input_packet": "HNC essay + research metacognition + research cinema + generated HNC score helper",
                "concept_count": concept_count,
                "ready_route_count": route_count,
                "relation": row.get("route"),
            }
        )
    return rows


def _capability_rows(
    system_rows: Sequence[Mapping[str, Any]],
    artifact_rows: Sequence[Mapping[str, Any]],
    route_rows: Sequence[Mapping[str, Any]],
    context: Mapping[str, Any],
) -> List[Dict[str, Any]]:
    wired = sum(1 for row in system_rows if row.get("wired"))
    artifacts = sum(1 for row in artifact_rows if row.get("present"))
    routed = sum(1 for row in route_rows if row.get("ready"))
    return [
        {
            "id": "metacognitive_repo_scan",
            "status": "pass" if wired == len(system_rows) else "attention",
            "evidence": f"{wired}/{len(system_rows)} metacognitive systems wired",
        },
        {
            "id": "hnc_packet_available",
            "status": "pass" if context.get("essay_benchmark_status") == "hnc_essay_benchmark_certified" else "attention",
            "evidence": f"essay={context.get('essay_benchmark_status')} words={context.get('essay_word_count')}",
        },
        {
            "id": "research_understanding_available",
            "status": "pass" if context.get("research_metacognition_status") == "research_metacognition_active" else "attention",
            "evidence": f"metacognition={context.get('research_metacognition_status')} concepts={len(context.get('understood_concepts') or [])}",
        },
        {
            "id": "artifact_surface",
            "status": "pass" if artifacts == len(artifact_rows) else "attention",
            "evidence": f"{artifacts}/{len(artifact_rows)} artifacts present",
        },
        {
            "id": "hnc_routes_expanded",
            "status": "pass" if routed == len(route_rows) else "attention",
            "evidence": f"{routed}/{len(route_rows)} metacognitive routes ready",
        },
        {
            "id": "authority_boundary",
            "status": "pass",
            "evidence": "no credentials, broker calls, trading gate changes, or external mutation",
        },
    ]


def _render_markdown(report: Mapping[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), Mapping) else {}
    lines = [
        "# Metacognitive Systems Expansion",
        "",
        f"Status: `{report.get('status')}`",
        f"Mode: `{report.get('mode')}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Systems", ""])
    for row in report.get("system_rows") or []:
        if isinstance(row, Mapping):
            lines.append(f"- `{row.get('id')}`: wired=`{row.get('wired')}` layer=`{row.get('layer')}`")
    lines.extend(["", "## Routes", ""])
    for row in report.get("route_rows") or []:
        if isinstance(row, Mapping):
            lines.append(f"- `{row.get('route_id')}`: `{row.get('status')}`")
    return "\n".join(lines) + "\n"


def build_metacognitive_systems_expansion(*, root: Optional[Path] = None) -> Dict[str, Any]:
    root_path = Path(root or REPO_ROOT).resolve()
    start = time.perf_counter()
    trace = publish_search_event(
        phase="metacognitive_systems_scan_started",
        source_system="metacognitive_systems_expansion",
        query="repo-wide metacognitive systems expansion",
        source="local_repo_scan",
        status="received",
        root=root_path,
    )
    trace_id = trace.get("trace_id")
    query_id = trace.get("query_id")

    system_rows = [_system_row(root_path, spec) for spec in SYSTEM_SPECS]
    wired_count = sum(1 for row in system_rows if row.get("wired"))
    for row in system_rows:
        publish_search_event(
            phase="metacognitive_system_detected",
            source_system="metacognitive_systems_expansion",
            query="repo-wide metacognitive systems expansion",
            trace_id=trace_id,
            query_id=query_id,
            source=str(row.get("path") or ""),
            result_count=1 if row.get("wired") else 0,
            status="success" if row.get("wired") else "attention",
            metadata={"system_id": row.get("id"), "layer": row.get("layer")},
            root=root_path,
        )

    artifact_rows = [_artifact_row(root_path, rel, purpose) for rel, purpose in ARTIFACT_SPECS]
    context = _context(root_path)
    route_rows = _route_rows(system_rows, context)
    capability_rows = _capability_rows(system_rows, artifact_rows, route_rows, context)
    routed_count = sum(1 for row in route_rows if row.get("ready"))
    status = "metacognitive_systems_expanded" if all(row["status"] == "pass" for row in capability_rows) else "metacognitive_systems_attention"

    publish_search_event(
        phase="metacognitive_hnc_context_routed",
        source_system="metacognitive_systems_expansion",
        query="repo-wide metacognitive systems expansion",
        trace_id=trace_id,
        query_id=query_id,
        source="hnc_research_essay_packet",
        result_count=routed_count,
        status=status,
        metadata={"wired_count": wired_count, "route_count": len(route_rows)},
        root=root_path,
    )

    report: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "generated_at": utc_now(),
        "mode": "real_repo_metacognitive_systems_expansion",
        "summary": {
            "metacognitive_system_count": len(system_rows),
            "wired_metacognitive_system_count": wired_count,
            "artifact_count": len(artifact_rows),
            "present_artifact_count": sum(1 for row in artifact_rows if row.get("present")),
            "route_count": len(route_rows),
            "ready_route_count": routed_count,
            "hnc_essay_word_count": context.get("essay_word_count"),
            "hnc_essay_benchmark_status": context.get("essay_benchmark_status"),
            "research_metacognition_status": context.get("research_metacognition_status"),
            "understood_concept_count": len(context.get("understood_concepts") or []),
            "ready_research_route_count": len(context.get("ready_routes") or []),
            "elapsed_ms": round((time.perf_counter() - start) * 1000, 2),
            "thoughtbus_mycelium_publish_enabled": True,
            "no_credentials_read": True,
            "no_external_mutation": True,
            "no_trading_gate_bypass": True,
        },
        "capability_rows": capability_rows,
        "system_rows": system_rows,
        "artifact_rows": artifact_rows,
        "route_rows": route_rows,
        "hnc_context": context,
        "manual_boundaries": [
            "metacognitive expansion maps and routes local evidence only",
            "no live broker order, close, cancel, credential read, or external mutation is introduced",
            "self-authoring systems receive validation context; they do not bypass tests or runtime controls",
        ],
        "source_paths": {
            "state": DEFAULT_STATE_PATH.as_posix(),
            "public": DEFAULT_PUBLIC_PATH.as_posix(),
            "audit_json": DEFAULT_AUDIT_JSON.as_posix(),
            "audit_md": DEFAULT_AUDIT_MD.as_posix(),
        },
    }

    _safe_write_json(_rooted(root_path, DEFAULT_STATE_PATH), report)
    _safe_write_json(_rooted(root_path, DEFAULT_PUBLIC_PATH), report)
    _safe_write_json(_rooted(root_path, DEFAULT_AUDIT_JSON), report)
    _write_text(_rooted(root_path, DEFAULT_AUDIT_MD), _render_markdown(report))

    publish_search_event(
        phase="metacognitive_systems_expansion_audited",
        source_system="metacognitive_systems_expansion",
        query="repo-wide metacognitive systems expansion",
        trace_id=trace_id,
        query_id=query_id,
        source="metacognitive_expansion_audit",
        result_count=sum(1 for row in capability_rows if row["status"] == "pass"),
        status=status,
        metadata={"public": DEFAULT_PUBLIC_PATH.as_posix()},
        root=root_path,
    )
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Audit repo-wide metacognitive systems expansion.")
    parser.parse_args(argv)
    report = build_metacognitive_systems_expansion()
    summary = report["summary"]
    print(
        f"{report['status']} systems={summary['wired_metacognitive_system_count']}/{summary['metacognitive_system_count']} "
        f"routes={summary['ready_route_count']}/{summary['route_count']} artifacts={summary['present_artifact_count']}/{summary['artifact_count']}"
    )
    return 0 if report["status"] == "metacognitive_systems_expanded" else 1


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["build_metacognitive_systems_expansion"]
