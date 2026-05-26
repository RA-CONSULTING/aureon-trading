"""Metacognitive understanding layer for research cinema packets.

The online research cinema can fetch sources, write a paper, render a motion
replay, and generate code. This module turns that packet into structured
understanding the organism can route through Seer, Lyra, HNC, ThoughtBus,
Mycelium, tests, and code authoring.

It does not add trading authority. It publishes what was understood, what is
still unknown, and what validation should happen next.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from aureon.search.swarm_search_fabric import publish_search_event

try:
    from aureon.queen.knowledge_interpreter import (
        classify_category,
        classify_data_type,
        extract_meaning,
    )
except Exception:  # pragma: no cover - keep the search pipeline fail-soft
    classify_category = None  # type: ignore[assignment]
    classify_data_type = None  # type: ignore[assignment]
    extract_meaning = None  # type: ignore[assignment]


REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = Path("state/aureon_research_metacognition_latest.json")
PUBLIC_PATH = Path("frontend/public/aureon_research_metacognition.json")
DOCS_JSON_PATH = Path("docs/audits/aureon_research_metacognition.json")
DOCS_MD_PATH = Path("docs/audits/aureon_research_metacognition.md")

SCHEMA_VERSION = "aureon-research-metacognition-v1"

CONCEPT_SPECS = (
    {
        "id": "source_strength",
        "label": "Source strength",
        "terms": ("source", "evidence", "hash", "status", "fetched", "timestamp", "summary"),
        "route": "Seer evidence grading",
    },
    {
        "id": "harmonic_coherence",
        "label": "Harmonic coherence",
        "terms": ("harmonic", "coherence", "phi", "frequency", "resonance", "nexus", "hnc"),
        "route": "HNC/Auris coherence feature",
    },
    {
        "id": "repeatability",
        "label": "Repeatability",
        "terms": ("repeat", "test", "replay", "benchmark", "pytest", "validation", "outcome"),
        "route": "test and replay validation",
    },
    {
        "id": "friction_feasibility",
        "label": "Friction feasibility",
        "terms": ("friction", "signal-to-noise", "noise", "spread", "slippage", "feasibility", "cost"),
        "route": "Lyra risk and market friction",
    },
    {
        "id": "contradiction_handling",
        "label": "Contradiction handling",
        "terms": ("contradiction", "counter", "veto", "risk", "unknown", "limitation", "blocked"),
        "route": "counter-intelligence and veto pressure",
    },
    {
        "id": "coding_actionability",
        "label": "Coding actionability",
        "terms": ("code", "function", "class", "pytest", "import", "generated", "handoff"),
        "route": "Code Architect and test runner",
    },
    {
        "id": "visual_replay_context",
        "label": "Visual replay context",
        "terms": ("frame", "motion", "replay", "cinema", "screenshot", "visual"),
        "route": "browser mapping and research replay",
    },
    {
        "id": "learning_memory",
        "label": "Learning memory",
        "terms": ("learning", "memory", "mycelium", "thoughtbus", "outcome", "reward", "penalty"),
        "route": "ThoughtBus/Mycelium memory",
    },
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _rooted(root: Optional[Path], rel: Path) -> Path:
    base = Path(root or REPO_ROOT).resolve()
    return rel if rel.is_absolute() else base / rel


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except Exception:
        return str(path)


def _safe_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    os.replace(tmp_path, path)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _hash(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8", errors="replace")).hexdigest()


def _slug(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (text or "research").lower()).strip("-")
    return slug[:80] or "research"


def _read_text(root: Path, rel_or_abs: Optional[str]) -> str:
    if not rel_or_abs:
        return ""
    path = Path(rel_or_abs)
    if not path.is_absolute():
        path = root / path
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _iter_text_parts(
    *,
    topic: str,
    source_rows: Sequence[Mapping[str, Any]],
    paper_text: str,
    coding_manifest: Mapping[str, Any],
) -> Iterable[str]:
    yield topic
    yield paper_text
    for row in source_rows:
        yield str(row.get("title") or "")
        yield str(row.get("summary") or "")
        yield str(row.get("excerpt") or "")
        yield str(row.get("url") or "")
    for row in coding_manifest.get("generated_files") or []:
        if isinstance(row, Mapping):
            yield str(row.get("path") or "")
            yield str(row.get("authoring_path") or "")
    yield str(coding_manifest.get("module_import") or "")
    yield str(coding_manifest.get("test_command") or "")


def _count_terms(text: str, terms: Sequence[str]) -> int:
    lower = text.lower()
    return sum(lower.count(term.lower()) for term in terms)


def _interpret(text: str, tags: Sequence[str]) -> Dict[str, Any]:
    if classify_data_type and classify_category and extract_meaning:
        try:
            return {
                "data_type": str(classify_data_type(text)),
                "category": str(classify_category(text, list(tags))),
                "meaning": str(extract_meaning(text, max_words=24)),
                "interpreter": "knowledge_interpreter",
            }
        except Exception:
            pass
    words = text.split()
    return {
        "data_type": "fact",
        "category": "knowledge",
        "meaning": " ".join(words[:24]),
        "interpreter": "deterministic_fallback",
    }


def _concept_rows(
    *,
    topic: str,
    source_rows: Sequence[Mapping[str, Any]],
    paper_text: str,
    coding_manifest: Mapping[str, Any],
) -> List[Dict[str, Any]]:
    text = "\n".join(
        _iter_text_parts(
            topic=topic,
            source_rows=source_rows,
            paper_text=paper_text,
            coding_manifest=coding_manifest,
        )
    )
    rows: List[Dict[str, Any]] = []
    for spec in CONCEPT_SPECS:
        count = _count_terms(text, spec["terms"])
        evidence_samples: List[str] = []
        for part in _iter_text_parts(
            topic=topic,
            source_rows=source_rows,
            paper_text=paper_text,
            coding_manifest=coding_manifest,
        ):
            lower = part.lower()
            if any(term.lower() in lower for term in spec["terms"]):
                cleaned = re.sub(r"\s+", " ", part).strip()
                if cleaned:
                    evidence_samples.append(cleaned[:220])
            if len(evidence_samples) >= 3:
                break
        interpretation = _interpret(" ".join(evidence_samples) or text[:600], [str(spec["id"])])
        rows.append(
            {
                "concept_id": spec["id"],
                "label": spec["label"],
                "status": "understood" if count else "waiting_for_evidence",
                "evidence_count": count,
                "route": spec["route"],
                "meaning": interpretation.get("meaning"),
                "data_type": interpretation.get("data_type"),
                "category": interpretation.get("category"),
                "interpreter": interpretation.get("interpreter"),
                "evidence_samples": evidence_samples,
            }
        )
    return rows


def _route_rows(concept_rows: Sequence[Mapping[str, Any]], coding_manifest: Mapping[str, Any]) -> List[Dict[str, Any]]:
    concepts = {str(row.get("concept_id")) for row in concept_rows if row.get("status") == "understood"}
    module_import = str(coding_manifest.get("module_import") or "")
    test_command = str(coding_manifest.get("test_command") or "")
    return [
        {
            "route_id": "seer_feature_packet",
            "system": "Seer",
            "relation": "reads source strength, freshness, contradiction, and confidence context",
            "input_concepts": ["source_strength", "contradiction_handling"],
            "ready": {"source_strength", "contradiction_handling"}.issubset(concepts),
            "authority": "feature_context_only",
        },
        {
            "route_id": "lyra_emotion_risk_packet",
            "system": "Lyra",
            "relation": "reads friction, feasibility, urgency, and risk pressure from research context",
            "input_concepts": ["friction_feasibility", "contradiction_handling"],
            "ready": {"friction_feasibility", "contradiction_handling"}.issubset(concepts),
            "authority": "risk_context_only",
        },
        {
            "route_id": "hnc_harmonic_packet",
            "system": "HNC/Auris",
            "relation": "maps harmonic coherence and repeatability into explainable HNC score features",
            "input_concepts": ["harmonic_coherence", "repeatability"],
            "ready": {"harmonic_coherence", "repeatability"}.issubset(concepts),
            "authority": "coherence_feature_only",
        },
        {
            "route_id": "thoughtbus_packet",
            "system": "ThoughtBus",
            "relation": "publishes research understanding phases for whole-organism visibility",
            "input_concepts": list(sorted(concepts)),
            "ready": bool(concepts),
            "authority": "organism_event_publication",
        },
        {
            "route_id": "mycelium_learning_packet",
            "system": "Mycelium",
            "relation": "receives learning memory, route confidence, and validation pressure",
            "input_concepts": ["learning_memory", "repeatability", "contradiction_handling"],
            "ready": bool({"learning_memory", "repeatability"} & concepts),
            "authority": "learning_signal_only",
        },
        {
            "route_id": "code_architect_packet",
            "system": "Code Architect",
            "relation": "tracks generated helper code and handoff files as authored research artifacts",
            "input_concepts": ["coding_actionability"],
            "ready": bool(module_import),
            "authority": "code_artifact_authoring",
            "module_import": module_import,
        },
        {
            "route_id": "test_runner_packet",
            "system": "Test Runner",
            "relation": "validates the generated model before it influences confidence",
            "input_concepts": ["repeatability", "coding_actionability"],
            "ready": bool(test_command),
            "authority": "validation_only",
            "test_command": test_command,
        },
        {
            "route_id": "runtime_action_packet",
            "system": "Runtime action layer",
            "relation": "may consume calibrated features later, but this packet cannot place orders",
            "input_concepts": ["source_strength", "harmonic_coherence", "friction_feasibility"],
            "ready": False,
            "authority": "no_trading_gate_bypass",
        },
    ]


def _unknown_rows(concept_rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for row in concept_rows:
        if row.get("status") != "understood":
            rows.append(
                {
                    "unknown_id": f"{row.get('concept_id')}_evidence_missing",
                    "area": row.get("label"),
                    "state": "waiting_for_real_evidence",
                    "next_action": f"add real source/test rows for {row.get('label')}",
                }
            )
    rows.extend(
        [
            {
                "unknown_id": "outcome_calibration_missing",
                "area": "outcome calibration",
                "state": "requires_real_outcome_history",
                "next_action": "compare score changes against real outcome evidence before raising confidence",
            },
            {
                "unknown_id": "full_source_context_not_stored",
                "area": "source context",
                "state": "bounded_snippets_only",
                "next_action": "re-fetch original URLs when deeper review is needed instead of storing public page bodies",
            },
        ]
    )
    return rows


def _test_action_rows(coding_manifest: Mapping[str, Any]) -> List[Dict[str, Any]]:
    test_command = str(coding_manifest.get("test_command") or "")
    module_import = str(coding_manifest.get("module_import") or "")
    return [
        {
            "action_id": "run_generated_tests",
            "state": "ready" if test_command else "waiting_for_generated_test",
            "command": test_command,
            "purpose": "prove the generated score helper is deterministic and bounded",
        },
        {
            "action_id": "route_explainable_features",
            "state": "ready" if module_import else "waiting_for_generated_module",
            "module_import": module_import,
            "purpose": "make Seer/Lyra/HNC consume the score as explainable context only",
        },
        {
            "action_id": "calibrate_against_outcomes",
            "state": "waiting_for_real_outcomes",
            "purpose": "measure whether the score improves future decisions before promotion",
        },
    ]


def _render_markdown(packet: Mapping[str, Any]) -> str:
    summary = packet.get("summary") if isinstance(packet.get("summary"), Mapping) else {}
    lines = [
        "# Aureon Research Metacognition",
        "",
        f"Status: `{packet.get('status')}`",
        f"Topic: `{packet.get('topic')}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Concepts", ""])
    for row in packet.get("concept_rows") or []:
        if not isinstance(row, Mapping):
            continue
        lines.append(f"- **{row.get('label')}**: {row.get('status')} - {row.get('meaning')}")
    lines.extend(["", "## Organism Routes", ""])
    for row in packet.get("organism_route_rows") or []:
        if not isinstance(row, Mapping):
            continue
        lines.append(f"- **{row.get('system')}**: {row.get('relation')} (`ready={row.get('ready')}`)")
    return "\n".join(lines) + "\n"


def build_research_metacognition(
    *,
    topic: str,
    query: Optional[str] = None,
    source_rows: Optional[Sequence[Mapping[str, Any]]] = None,
    paper_path: Optional[str] = None,
    paper_text: Optional[str] = None,
    motion_picture: Optional[Mapping[str, Any]] = None,
    coding_manifest: Optional[Mapping[str, Any]] = None,
    trace_id: Optional[str] = None,
    query_id: Optional[str] = None,
    root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Create and publish a metacognitive understanding packet."""

    root_path = Path(root or REPO_ROOT).resolve()
    rows = list(source_rows or [])
    coding = dict(coding_manifest or {})
    motion = dict(motion_picture or {})
    paper_body = paper_text if paper_text is not None else _read_text(root_path, paper_path)
    query_text = query or topic

    publish_search_event(
        phase="metacognition_ingested",
        source_system="research_metacognition",
        query=query_text,
        trace_id=trace_id,
        query_id=query_id,
        source="online_research_cinema_packet",
        result_count=len(rows),
        status="success" if rows or paper_body else "attention",
        metadata={"topic": topic, "paper_path": paper_path},
        root=root_path,
    )

    concepts = _concept_rows(
        topic=topic,
        source_rows=rows,
        paper_text=paper_body,
        coding_manifest=coding,
    )
    understood_count = sum(1 for row in concepts if row.get("status") == "understood")
    publish_search_event(
        phase="metacognition_concepts_extracted",
        source_system="research_metacognition",
        query=query_text,
        trace_id=trace_id,
        query_id=query_id,
        source="knowledge_interpreter",
        result_count=understood_count,
        status="success" if understood_count else "attention",
        metadata={"concept_count": len(concepts)},
        root=root_path,
    )

    routes = _route_rows(concepts, coding)
    ready_routes = sum(1 for row in routes if row.get("ready"))
    publish_search_event(
        phase="metacognition_routes_mapped",
        source_system="research_metacognition",
        query=query_text,
        trace_id=trace_id,
        query_id=query_id,
        source="organism_route_mapper",
        result_count=ready_routes,
        status="success" if ready_routes else "attention",
        metadata={"route_count": len(routes)},
        root=root_path,
    )

    unknowns = _unknown_rows(concepts)
    test_actions = _test_action_rows(coding)
    packet_hash = _hash(json.dumps({"topic": topic, "concepts": concepts, "routes": routes}, sort_keys=True, default=str))
    slug = _slug(topic)
    topic_state_path = Path("state/research_metacognition") / slug / "metacognition.json"

    packet: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": "research_metacognition_active" if understood_count and ready_routes else "research_metacognition_attention",
        "generated_at": _utc_now(),
        "mode": "real_research_understanding_packet",
        "topic": topic,
        "query": query_text,
        "understanding_hash": packet_hash,
        "understanding_summary": (
            f"Aureon understands {topic} as a source-linked research packet with "
            f"{understood_count}/{len(concepts)} concept rows and {ready_routes}/{len(routes)} organism routes ready. "
            "It is routed as evidence, learning, code, and validation context, not as direct trading authority."
        ),
        "summary": {
            "source_count": len(rows),
            "concept_count": len(concepts),
            "understood_concept_count": understood_count,
            "organism_route_count": len(routes),
            "ready_route_count": ready_routes,
            "unknown_count": len(unknowns),
            "test_action_count": len(test_actions),
            "paper_present": bool(paper_body),
            "motion_present": bool(motion.get("public_html") or motion.get("html_path")),
            "coding_artifacts_present": bool(coding.get("generated_files")),
            "knowledge_interpreter_used": any(row.get("interpreter") == "knowledge_interpreter" for row in concepts),
            "thoughtbus_mycelium_publish_enabled": True,
            "no_trading_gate_bypass": True,
            "no_external_mutation": True,
        },
        "concept_rows": concepts,
        "organism_route_rows": routes,
        "unknown_rows": unknowns,
        "test_action_rows": test_actions,
        "motion_picture": motion,
        "coding_handoff": coding,
        "integration_proof": {
            "source_packet": "online_research_cinema",
            "metacognition_module": "aureon.search.research_metacognition",
            "deterministic_interpreter": "aureon.queen.knowledge_interpreter",
            "fabric_publisher": "aureon.search.swarm_search_fabric.publish_search_event",
            "thoughtbus_topic_family": "search.fabric.metacognition_*",
            "mycelium_signal_source": "swarm_search_fabric",
        },
        "manual_boundaries": [
            "metacognition classifies and routes research context only",
            "missing evidence remains visible as unknown rows",
            "generated code must pass tests before it influences confidence",
            "this packet cannot place trades, read credentials, or mutate external services",
        ],
        "source_paths": {
            "state": STATE_PATH.as_posix(),
            "topic_state": topic_state_path.as_posix(),
            "public": PUBLIC_PATH.as_posix(),
            "docs_json": DOCS_JSON_PATH.as_posix(),
            "docs_md": DOCS_MD_PATH.as_posix(),
            "paper": paper_path or "",
        },
    }

    for rel in (STATE_PATH, PUBLIC_PATH, DOCS_JSON_PATH, topic_state_path):
        _safe_write_json(_rooted(root_path, rel), packet)
    _write_text(_rooted(root_path, DOCS_MD_PATH), _render_markdown(packet))

    publish_search_event(
        phase="metacognition_understanding_published",
        source_system="research_metacognition",
        query=query_text,
        trace_id=trace_id,
        query_id=query_id,
        source="research_metacognition_packet",
        result_count=understood_count,
        status=packet["status"],
        metadata={
            "public": PUBLIC_PATH.as_posix(),
            "concept_count": len(concepts),
            "ready_route_count": ready_routes,
            "understanding_hash": packet_hash[:18],
        },
        root=root_path,
    )
    return packet


__all__ = ["build_research_metacognition"]
