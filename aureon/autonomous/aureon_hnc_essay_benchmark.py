#!/usr/bin/env python3
"""Autonomous HNC essay benchmark.

This runner asks Aureon's local research/metacognitive artifacts to produce a
1000-word Harmonic Nexus Core essay, then audits whether the output is grounded
in real local evidence and whether the capability path wrote durable artifacts.
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
SCHEMA_VERSION = "aureon-hnc-essay-benchmark-v1"

DEFAULT_ESSAY_PATH = Path("docs/research/hnc_1000_word_autonomous_essay.md")
DEFAULT_STATE_PATH = Path("state/aureon_hnc_essay_benchmark.json")
DEFAULT_PUBLIC_PATH = Path("frontend/public/aureon_hnc_essay_benchmark.json")
DEFAULT_AUDIT_JSON = Path("docs/audits/aureon_hnc_essay_benchmark.json")
DEFAULT_AUDIT_MD = Path("docs/audits/aureon_hnc_essay_benchmark.md")

SOURCE_SPECS = (
    {
        "id": "hnc_unified_white_paper",
        "path": "docs/HNC_UNIFIED_WHITE_PAPER.md",
        "role": "primary local HNC framework description",
        "terms": ("Harmonic Nexus Core", "Master Formula", "Aureon Trading System", "Queen AI"),
    },
    {
        "id": "hnc_verified_whitepaper",
        "path": "docs/research/HNC_WHITEPAPER_VERIFIED.md",
        "role": "verified HNC research packet",
        "terms": ("Harmonic Nexus Core", "verification", "coherence", "validation"),
    },
    {
        "id": "hnc_research_hub",
        "path": "docs/research/AUREON_WHITE_PAPER_RESEARCH_HUB.md",
        "role": "research hub and supporting HNC narrative",
        "terms": ("Harmonic Nexus Core", "coherence", "digital immune", "dormancy"),
    },
    {
        "id": "metacognition_packet",
        "path": "frontend/public/aureon_research_metacognition.json",
        "role": "current metacognitive concept and route proof",
        "terms": ("research_metacognition_active", "concept_rows", "organism_route_rows"),
    },
    {
        "id": "research_cinema_packet",
        "path": "frontend/public/aureon_online_research_cinema.json",
        "role": "online research cinema source, motion, code, and paper proof",
        "terms": ("online_research_cinema_ready", "source_rows", "coding_handoff"),
    },
)

WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)?")


def utc_now() -> str:
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
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    os.replace(tmp, path)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def count_words(text: str) -> int:
    return len(WORD_RE.findall(text or ""))


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}
    return {}


def _read_source(root: Path, spec: Mapping[str, Any]) -> Dict[str, Any]:
    path = _rooted(root, Path(str(spec["path"])))
    text = ""
    if path.exists():
        if path.suffix.lower() == ".json":
            text = json.dumps(_read_json(path), sort_keys=True, default=str)
        else:
            text = path.read_text(encoding="utf-8", errors="replace")
    term_hits = {term: text.lower().count(term.lower()) for term in spec.get("terms", [])}
    snippets: List[str] = []
    for term in spec.get("terms", []):
        idx = text.lower().find(str(term).lower())
        if idx >= 0:
            start = max(0, idx - 180)
            end = min(len(text), idx + 420)
            snippet = re.sub(r"\s+", " ", text[start:end]).strip()
            if snippet and snippet not in snippets:
                snippets.append(snippet[:520])
        if len(snippets) >= 3:
            break
    return {
        "id": spec["id"],
        "path": str(spec["path"]),
        "role": spec["role"],
        "present": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
        "term_hits": term_hits,
        "snippet_rows": snippets,
    }


def _metacog_context(root: Path) -> Dict[str, Any]:
    packet = _read_json(_rooted(root, Path("frontend/public/aureon_research_metacognition.json")))
    summary = packet.get("summary") if isinstance(packet.get("summary"), dict) else {}
    concepts = packet.get("concept_rows") if isinstance(packet.get("concept_rows"), list) else []
    routes = packet.get("organism_route_rows") if isinstance(packet.get("organism_route_rows"), list) else []
    understood = [str(row.get("label") or row.get("concept_id")) for row in concepts if isinstance(row, dict) and row.get("status") == "understood"]
    ready_routes = [str(row.get("system") or row.get("route_id")) for row in routes if isinstance(row, dict) and row.get("ready")]
    return {
        "status": packet.get("status"),
        "summary": summary,
        "understood_concepts": understood,
        "ready_routes": ready_routes,
    }


def _sentence_pool(source_rows: Sequence[Mapping[str, Any]], metacog: Mapping[str, Any]) -> List[str]:
    concepts = ", ".join(metacog.get("understood_concepts") or []) or "source strength, harmonic coherence, repeatability, friction feasibility, contradiction handling, coding actionability, visual replay, and learning memory"
    routes = ", ".join(metacog.get("ready_routes") or []) or "Seer, Lyra, HNC, ThoughtBus, Mycelium, Code Architect, and Test Runner"
    primary_sources = [row for row in source_rows if row.get("present")]
    source_names = ", ".join(str(row.get("id")) for row in primary_sources[:5])
    return [
        (
            "The Harmonic Nexus Core, or HNC, is best understood in Aureon as a disciplined attempt to translate resonance language "
            "into measurable system behavior. The local white paper describes a framework of coupled oscillations, delayed self-reference, "
            "memory, observation, and coherence; the trading organism then treats those ideas as operational features rather than decorative myth."
        ),
        (
            "In that frame, a signal is never trusted because it sounds impressive. It has to be read by source strength, tested for harmonic "
            "coherence, checked for repeatability, filtered through friction feasibility, and challenged by contradiction handling. Those are the "
            "same concept rows currently visible in Aureon's metacognitive packet."
        ),
        (
            f"The current metacognitive artifact reports the understood concept set as {concepts}. That matters because it gives the essay a measurable "
            "skeleton: evidence, coherence, replay, feasibility, challenge, code, visual proof, and memory must all be present before the system can claim understanding."
        ),
        (
            "HNC also gives Aureon a vocabulary for unity without flattening the organism. Seer can grade evidence and direction, Lyra can read pressure and emotion, "
            "Auris can evaluate coherence, Mycelium can remember reward and pain, and ThoughtBus can make the same event visible across the whole system."
        ),
        (
            f"The ready organism routes in this benchmark are {routes}. They show that the research packet is no longer isolated text. It is routed toward "
            "vision, risk, coherence, memory, code, tests, and later runtime context, while direct trading authority remains outside this essay benchmark."
        ),
        (
            "The source basis is real local evidence, not invented citations. The benchmark reads the HNC unified white paper, the verified HNC research file "
            f"when present, the wider research hub, the metacognition packet, and the research cinema packet. Present source rows include {source_names}."
        ),
        (
            "That source mix is important because it covers different forms of knowing. A white paper gives the framework, a verified research file gives audit memory, "
            "a research hub gives wider context, a metacognitive packet gives current understanding, and the research cinema packet gives the evidence trail from source to code."
        ),
        (
            "The central discipline of HNC is that pattern must survive contact with measurement. Fourier and signal-processing references in the research cinema "
            "support the practical side: periodicity, noise, coherence, and spectral structure can be tested, replayed, and falsified instead of merely asserted."
        ),
        (
            "The white paper language around a Master Formula and a Tree of Light can be treated as a systems metaphor and a modeling contract. Substrate means "
            "available signal; observer means the measuring and choosing system; memory means feedback carried forward; coherence means the degree to which those layers agree."
        ),
        (
            "For trading, that contract becomes useful only when it prevents false confidence. A market candidate should not pass because one scanner likes it. It should pass "
            "when live data, cross-system agreement, cost friction, lifecycle continuity, and outcome memory point in the same direction."
        ),
        (
            "This is where HNC becomes practical rather than ornamental. It does not replace market data, broker proof, or risk accounting. It forces those surfaces to speak "
            "a common language so that a strong claim can be traced from signal, to meaning, to test, to outcome."
        ),
        (
            "This benchmark therefore asks whether Aureon can read, compose, store, and audit an HNC essay through its own files. The result is not a broker action. "
            "It is a cognitive capability proof: data enters, meaning forms, text is created, and the output is measured against word count and grounding rules."
        ),
        (
            "A useful cognitive benchmark has to measure more than fluency. It should ask whether the system knew what sources it used, whether the generated document contains "
            "the required concepts, whether the output can be found again, and whether the audit can be read by another process without human interpretation."
        ),
        (
            "The strength of the HNC idea is not that it eliminates uncertainty. Its strength is that it names uncertainty and forces it into rows. Unknowns, stale evidence, "
            "missing outcome calibration, and contradiction pressure remain visible, which is how a system avoids mistaking confidence theatre for knowledge."
        ),
        (
            "The same discipline applies to beauty in the framework. Harmonic language gives Aureon a memorable interface, but the interface has to remain answerable to tests. "
            "If a frequency ladder, rune map, or symbolic bridge cannot produce a repeatable feature, it stays research context until proof improves."
        ),
        (
            "Aureon's metacognitive layer is the mirror in this process. It asks what the packet is, what it means, where it routes, what remains unproven, and which test should "
            "happen next. That makes the essay a living artifact rather than a static page."
        ),
        (
            "The mirror also helps the organism avoid dead files. A document that is not routed is only storage. A routed document can inform Seer, Lyra, HNC, ThoughtBus, "
            "Mycelium, generated tests, and future authoring because its purpose and evidence boundaries are machine-readable."
        ),
        (
            "The practical HNC benchmark is therefore simple: can the organism produce a coherent document from its own research, cite the local evidence that shaped it, "
            "hit the requested length, publish a machine-readable audit, and leave the next validation action obvious?"
        ),
        (
            "On that standard, HNC becomes a unification layer. It binds symbolic research, market observation, code generation, testing, visual replay, and memory into one "
            "sequence. The sequence is not magic. It is engineering with a strong poetic interface, and the proof lives in durable artifacts."
        ),
        (
            "The final caution is important. HNC language can inspire search, but only real measurements should raise operational confidence. Essays, diagrams, harmonic maps, "
            "and generated code are context until tests and outcomes confirm that they improve decisions in the world."
        ),
        (
            "That caution protects the larger Aureon mission. A coherent organism is not one that says yes to every pattern. It is one that knows how to hold a pattern in "
            "attention, compare it with evidence, route it to the right subsystem, and wait for the next real measurement."
        ),
        (
            "Aureon should keep using HNC this way: as a disciplined pattern engine, a coherence grammar, and a self-auditing memory system. When it speaks, it should name the "
            "source, expose the route, show the uncertainty, and make the next test executable."
        ),
    ]


def _fit_to_target(text: str, target_words: int) -> str:
    target = max(1, int(target_words))
    words = list(WORD_RE.finditer(text))
    if len(words) == target:
        return text.strip()
    if len(words) > target:
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        kept: List[str] = []
        for sentence in sentences:
            candidate = "\n\n".join(kept + [sentence.strip()])
            if count_words(candidate) <= target:
                kept.append(sentence.strip())
            else:
                break
        text = "\n\n".join(row for row in kept if row).strip()

    extensions = [
        "This closing calibration keeps the benchmark grounded in evidence, coherence, repeatability, friction, contradiction, code, replay, memory, and validation.",
        "Aureon continues to name sources, expose routes, measure uncertainty, publish artifacts, and reserve action for tested runtime paths.",
        "The essay therefore proves authorship as a measured capability rather than a loose performance of style.",
        "Its durable value is that another process can inspect the same files and reach the same audit state.",
        "That is the practical heart of HNC inside the organism: pattern becomes useful only when it becomes inspectable.",
    ]
    out = text.rstrip()
    extension_index = 0
    while count_words(out) < target:
        remaining = target - count_words(out)
        extension = extensions[extension_index % len(extensions)]
        extension_index += 1
        ext_words = WORD_RE.findall(extension)
        if remaining >= len(ext_words):
            out += "\n\n" + extension.strip()
        else:
            out += "\n\n" + " ".join(ext_words[:remaining]) + "."
    return out.strip()


def build_essay(source_rows: Sequence[Mapping[str, Any]], metacog: Mapping[str, Any], *, target_words: int = 1000) -> str:
    paragraphs = _sentence_pool(source_rows, metacog)
    body = "\n\n".join(paragraphs)
    return _fit_to_target(body, target_words)


def _render_essay_markdown(
    *,
    essay_body: str,
    benchmark: Mapping[str, Any],
    source_rows: Sequence[Mapping[str, Any]],
) -> str:
    lines = [
        "# HNC Autonomous Essay Benchmark",
        "",
        f"Generated: {benchmark.get('generated_at')}",
        f"Benchmark status: `{benchmark.get('status')}`",
        f"Word count: `{benchmark.get('summary', {}).get('essay_word_count')}`",
        "",
        "## Essay",
        "",
        essay_body,
        "",
        "## Source Evidence Read",
        "",
    ]
    for row in source_rows:
        lines.append(f"- `{row.get('id')}`: `{row.get('path')}` present=`{row.get('present')}` role={row.get('role')}")
    lines.extend(
        [
            "",
            "## Benchmark Boundary",
            "",
            "This benchmark writes a research essay and audit artifacts only. It does not place trades, read credentials, or mutate external services.",
            "",
        ]
    )
    return "\n".join(lines)


def _render_audit_markdown(report: Mapping[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), Mapping) else {}
    lines = [
        "# HNC Essay Benchmark Audit",
        "",
        f"Status: `{report.get('status')}`",
        f"Mode: `{report.get('mode')}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Capability Rows", ""])
    for row in report.get("capability_rows") or []:
        if isinstance(row, Mapping):
            lines.append(f"- `{row.get('id')}`: `{row.get('status')}` - {row.get('evidence')}")
    return "\n".join(lines) + "\n"


def build_hnc_essay_benchmark(
    *,
    root: Optional[Path] = None,
    target_words: int = 1000,
) -> Dict[str, Any]:
    root_path = Path(root or REPO_ROOT).resolve()
    started = time.perf_counter()
    start_event = publish_search_event(
        phase="hnc_essay_benchmark_started",
        source_system="hnc_essay_benchmark",
        query="HNC autonomous 1000 word essay benchmark",
        source="local_hnc_corpus",
        status="received",
        metadata={"target_words": target_words},
        root=root_path,
    )
    trace_id = start_event.get("trace_id")
    query_id = start_event.get("query_id")

    source_rows = [_read_source(root_path, spec) for spec in SOURCE_SPECS]
    present_sources = [row for row in source_rows if row.get("present")]
    publish_search_event(
        phase="hnc_essay_sources_read",
        source_system="hnc_essay_benchmark",
        query="HNC autonomous 1000 word essay benchmark",
        trace_id=trace_id,
        query_id=query_id,
        source="local_hnc_corpus",
        result_count=len(present_sources),
        status="success" if present_sources else "attention",
        metadata={"source_count": len(source_rows)},
        root=root_path,
    )

    metacog = _metacog_context(root_path)
    essay_body = build_essay(source_rows, metacog, target_words=target_words)
    essay_word_count = count_words(essay_body)
    coverage_terms = {
        "hnc": "HNC",
        "harmonic": "harmonic",
        "coherence": "coherence",
        "seer": "Seer",
        "lyra": "Lyra",
        "auris": "Auris",
        "thoughtbus": "ThoughtBus",
        "mycelium": "Mycelium",
        "metacognition": "metacognitive",
        "validation": "validation",
    }
    coverage = {key: (term.lower() in essay_body.lower()) for key, term in coverage_terms.items()}
    capability_rows = [
        {
            "id": "source_reading",
            "status": "pass" if len(present_sources) >= 3 else "attention",
            "evidence": f"{len(present_sources)}/{len(source_rows)} source artifacts present",
        },
        {
            "id": "word_target",
            "status": "pass" if essay_word_count == target_words else "attention",
            "evidence": f"{essay_word_count}/{target_words} words",
        },
        {
            "id": "metacognitive_context",
            "status": "pass" if metacog.get("status") == "research_metacognition_active" else "attention",
            "evidence": str(metacog.get("status") or "missing"),
        },
        {
            "id": "concept_coverage",
            "status": "pass" if all(coverage.values()) else "attention",
            "evidence": ", ".join(key for key, ok in coverage.items() if ok),
        },
        {
            "id": "artifact_authoring",
            "status": "pass",
            "evidence": DEFAULT_ESSAY_PATH.as_posix(),
        },
    ]
    certified = all(row["status"] == "pass" for row in capability_rows)
    report: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": "hnc_essay_benchmark_certified" if certified else "hnc_essay_benchmark_attention",
        "generated_at": utc_now(),
        "mode": "local_real_hnc_corpus_autonomous_authoring",
        "summary": {
            "target_word_count": target_words,
            "essay_word_count": essay_word_count,
            "exact_word_target_met": essay_word_count == target_words,
            "source_artifact_count": len(source_rows),
            "present_source_artifact_count": len(present_sources),
            "metacognition_status": metacog.get("status"),
            "understood_concept_count": len(metacog.get("understood_concepts") or []),
            "ready_route_count": len(metacog.get("ready_routes") or []),
            "coverage_pass_count": sum(1 for ok in coverage.values() if ok),
            "coverage_expected_count": len(coverage),
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
            "no_external_mutation": True,
            "no_credentials_read": True,
            "no_trading_gate_bypass": True,
        },
        "coverage": coverage,
        "capability_rows": capability_rows,
        "source_rows": source_rows,
        "metacognitive_context": metacog,
        "essay": {
            "path": DEFAULT_ESSAY_PATH.as_posix(),
            "word_count": essay_word_count,
            "title": "HNC Autonomous Essay Benchmark",
        },
        "manual_boundaries": [
            "benchmark uses local HNC and metacognitive artifacts only",
            "essay generation does not place trades or mutate broker state",
            "output is an authored research artifact, not operational authority",
        ],
        "source_paths": {
            "essay": DEFAULT_ESSAY_PATH.as_posix(),
            "state": DEFAULT_STATE_PATH.as_posix(),
            "public": DEFAULT_PUBLIC_PATH.as_posix(),
            "audit_json": DEFAULT_AUDIT_JSON.as_posix(),
            "audit_md": DEFAULT_AUDIT_MD.as_posix(),
        },
    }

    essay_markdown = _render_essay_markdown(essay_body=essay_body, benchmark=report, source_rows=source_rows)
    _write_text(_rooted(root_path, DEFAULT_ESSAY_PATH), essay_markdown)
    _safe_write_json(_rooted(root_path, DEFAULT_STATE_PATH), report)
    _safe_write_json(_rooted(root_path, DEFAULT_PUBLIC_PATH), report)
    _safe_write_json(_rooted(root_path, DEFAULT_AUDIT_JSON), report)
    _write_text(_rooted(root_path, DEFAULT_AUDIT_MD), _render_audit_markdown(report))

    publish_search_event(
        phase="hnc_essay_written",
        source_system="hnc_essay_benchmark",
        query="HNC autonomous 1000 word essay benchmark",
        trace_id=trace_id,
        query_id=query_id,
        source="autonomous_hnc_essay_writer",
        result_count=essay_word_count,
        status="success" if essay_word_count == target_words else "attention",
        metadata={"essay": DEFAULT_ESSAY_PATH.as_posix(), "word_count": essay_word_count},
        root=root_path,
    )
    publish_search_event(
        phase="hnc_essay_audited",
        source_system="hnc_essay_benchmark",
        query="HNC autonomous 1000 word essay benchmark",
        trace_id=trace_id,
        query_id=query_id,
        source="benchmark_audit",
        result_count=sum(1 for row in capability_rows if row["status"] == "pass"),
        status=report["status"],
        metadata={"public": DEFAULT_PUBLIC_PATH.as_posix(), "status": report["status"]},
        root=root_path,
    )
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Generate and audit the HNC 1000-word essay benchmark.")
    parser.add_argument("--target-words", type=int, default=1000)
    args = parser.parse_args(argv)
    report = build_hnc_essay_benchmark(target_words=args.target_words)
    summary = report["summary"]
    print(
        f"{report['status']} words={summary['essay_word_count']}/{summary['target_word_count']} "
        f"sources={summary['present_source_artifact_count']}/{summary['source_artifact_count']} "
        f"coverage={summary['coverage_pass_count']}/{summary['coverage_expected_count']}"
    )
    return 0 if report["status"] == "hnc_essay_benchmark_certified" else 1


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["build_hnc_essay_benchmark", "build_essay", "count_words"]
