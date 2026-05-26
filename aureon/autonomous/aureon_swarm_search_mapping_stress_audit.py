#!/usr/bin/env python3
"""Map and stress-audit Aureon's swarm search/browser/data-capture systems.

This is not a trading blocker gate. It proves which search producers are wired,
which capture artifacts are real, and whether current search events reach the
shared fabric, ThoughtBus, and Mycelium.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "aureon-swarm-search-mapping-stress-audit-v1"

FABRIC_PUBLIC_PATH = Path("frontend/public/aureon_swarm_search_fabric.json")
FABRIC_LEDGER_PATH = Path("state/aureon_swarm_search_fabric_events.jsonl")
KEYWORD_PUBLIC_PATH = Path("frontend/public/aureon_swarm_keyword_search_latest.json")
ONLINE_RESEARCH_PUBLIC_PATH = Path("frontend/public/aureon_online_research_cinema.json")
RESEARCH_METACOG_PUBLIC_PATH = Path("frontend/public/aureon_research_metacognition.json")
DEFAULT_STATE_PATH = Path("state/aureon_swarm_search_mapping_stress_audit.json")
DEFAULT_AUDIT_JSON = Path("docs/audits/aureon_swarm_search_mapping_stress_audit.json")
DEFAULT_AUDIT_MD = Path("docs/audits/aureon_swarm_search_mapping_stress_audit.md")
DEFAULT_PUBLIC_JSON = Path("frontend/public/aureon_swarm_search_mapping_stress_audit.json")

EXPECTED_PHASES = (
    "query_received",
    "source_selected",
    "result_captured",
    "page_fetch_requested",
    "page_fetched",
    "browser_opened",
    "screen_captured",
    "keyword_scan_requested",
    "keyword_file_read",
    "keyword_match_captured",
    "keyword_scan_completed",
    "online_research_goal_received",
    "online_source_discovered",
    "online_source_fetched",
    "online_source_summarized",
    "research_frame_rendered",
    "research_motion_compiled",
    "research_paper_drafted",
    "coding_brief_created",
    "coding_file_written",
    "coding_handoff_ready",
    "metacognition_ingested",
    "metacognition_concepts_extracted",
    "metacognition_routes_mapped",
    "metacognition_understanding_published",
    "knowledge_search_requested",
    "knowledge_search_completed",
)

SYSTEM_SPECS = (
    {
        "id": "agent_core_search_browser",
        "label": "Agent Core web search/browser/capture",
        "path": "aureon/autonomous/aureon_agent_core.py",
        "required_symbols": [
            "def web_search",
            "def web_fetch",
            "def open_url",
            "def screenshot",
            "def keyword_search_files",
            "def online_research_cinema",
            "def search_knowledge",
            "publish_search_event",
        ],
        "role": "operator query intake, web results, page fetch, browser launch, screenshot, local keyword/text search, local knowledge search",
    },
    {
        "id": "local_keyword_search",
        "label": "Local keyword reader",
        "path": "aureon/search/local_keyword_search.py",
        "required_symbols": [
            "def run_keyword_search",
            "TEXT_EXTENSIONS",
            "SENSITIVE_NAME_PARTS",
            "aureon_swarm_keyword_search_latest.json",
        ],
        "role": "reads real repo/test/doc text and returns keyword snippets with path and line evidence",
    },
    {
        "id": "online_research_cinema",
        "label": "Online research cinema",
        "path": "aureon/search/online_research_cinema.py",
        "required_symbols": [
            "def build_online_research_cinema",
            "def discover_sources",
            "def render_frame",
            "def compile_gif",
            "def make_paper",
            "def write_generated_code_artifacts",
            "aureon_online_research_cinema.json",
        ],
        "role": "fetches online source evidence, renders motion replay frames, drafts cited paper packets, and writes coding handoff files",
    },
    {
        "id": "research_metacognition",
        "label": "Research metacognition",
        "path": "aureon/search/research_metacognition.py",
        "required_symbols": [
            "def build_research_metacognition",
            "CONCEPT_SPECS",
            "metacognition_ingested",
            "metacognition_understanding_published",
            "aureon_research_metacognition.json",
        ],
        "role": "turns online research packets into structured concepts, organism routes, unknowns, and validation actions for Seer/Lyra/HNC/ThoughtBus/Mycelium",
    },
    {
        "id": "queen_online_researcher",
        "label": "Queen online researcher",
        "path": "aureon/queen/queen_online_researcher.py",
        "required_symbols": [
            "research_trading_strategies",
            "_research_market_patterns",
            "_research_binance_patterns",
            "_research_kraken_patterns",
            "_save_research_history",
        ],
        "role": "async market/API research and persisted findings",
    },
    {
        "id": "queen_research_engine",
        "label": "Queen research engine",
        "path": "aureon/utils/aureon_queen_research_engine.py",
        "required_symbols": [
            "class QueenResearchEngine",
            "def queue_research",
            "self.thought_bus.publish",
            "ResearchFinding",
        ],
        "role": "goal-triggered research queue and ThoughtBus publication",
    },
    {
        "id": "queen_research_neuron",
        "label": "Queen research neuron",
        "path": "aureon/utils/aureon_queen_research_neuron.py",
        "required_symbols": [
            "class WikipediaResearcher",
            "class RSSFeedScanner",
            "def _publish_thought",
            "async def comprehensive_research",
        ],
        "role": "Wikipedia, RSS, entity, sentiment, and market context research",
    },
    {
        "id": "self_research_loop",
        "label": "Self research loop",
        "path": "aureon/queen/self_research_loop.py",
        "required_symbols": [
            "class SelfResearchLoop",
            "world_data_ingester.answer_question",
            "ingest_to_vault",
            "stash_pockets",
            "thought_bus.publish",
        ],
        "role": "turns unanswered internal questions into ingested external evidence",
    },
    {
        "id": "research_corpus_index",
        "label": "Research corpus index",
        "path": "aureon/queen/research_corpus_index.py",
        "required_symbols": [
            "class ResearchCorpusIndex",
            "def search",
            "state/research_index.json",
            "No semantic embeddings",
        ],
        "role": "local docs and research source retrieval",
    },
    {
        "id": "frontend_queen_hive_browser",
        "label": "Frontend Queen Hive browser",
        "path": "frontend/src/core/queenHiveBrowser.ts",
        "required_symbols": [
            "export class QueenHiveBrowser",
            "registerWithHiveMind",
            "temporalLadder.broadcast",
        ],
        "role": "browser-side hive state and visible search/swarm surface context",
    },
    {
        "id": "search_fabric",
        "label": "Swarm search fabric",
        "path": "aureon/search/swarm_search_fabric.py",
        "required_symbols": [
            "def publish_search_event",
            "ThoughtBus",
            "get_mycelium",
            "aureon_swarm_search_fabric_events.jsonl",
        ],
        "role": "canonical event envelope for browser mapping and data capture",
    },
)


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


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _read_json(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default
    return default


def _write_json(path: Path, payload: Mapping[str, Any]) -> Dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, sort_keys=True, default=str)
    path.write_text(text, encoding="utf-8")
    return {"path": str(path), "bytes": len(text.encode("utf-8"))}


def _write_text(path: Path, text: str) -> Dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return {"path": str(path), "bytes": len(text.encode("utf-8"))}


def _tail_jsonl(path: Path, limit: int = 120, max_bytes: int = 768_000) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    try:
        with path.open("rb") as handle:
            handle.seek(0, os.SEEK_END)
            size = handle.tell()
            handle.seek(max(0, size - max_bytes))
            if size > max_bytes:
                handle.readline()
            text = handle.read().decode("utf-8", errors="replace")
        for line in text.splitlines():
            try:
                value = json.loads(line)
                if isinstance(value, dict):
                    rows.append(value)
            except Exception:
                continue
    except Exception:
        return []
    return rows[-limit:]


def _source_row(root: Path, spec: Mapping[str, Any]) -> Dict[str, Any]:
    path = _rooted(root, Path(str(spec["path"])))
    text = _read_text(path)
    missing = [symbol for symbol in spec["required_symbols"] if symbol not in text]
    return {
        "id": spec["id"],
        "label": spec["label"],
        "path": spec["path"],
        "present": path.exists(),
        "role": spec["role"],
        "required_symbol_count": len(spec["required_symbols"]),
        "present_symbol_count": len(spec["required_symbols"]) - len(missing),
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
        "modified_at": datetime.fromtimestamp(mtime, timezone.utc).isoformat() if mtime else None,
        "age_sec": round(max(0.0, time.time() - mtime), 3) if mtime else None,
    }


def _event_rows(root: Path) -> List[Dict[str, Any]]:
    return _tail_jsonl(_rooted(root, FABRIC_LEDGER_PATH), limit=120)


def _phase_rows(events: List[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    phases_seen = {str(row.get("phase") or "") for row in events}
    rows: List[Dict[str, Any]] = []
    for phase in EXPECTED_PHASES:
        seen_rows = [row for row in events if row.get("phase") == phase]
        latest = seen_rows[-1] if seen_rows else {}
        rows.append(
            {
                "phase": phase,
                "seen": phase in phases_seen,
                "event_count": len(seen_rows),
                "latest_source_system": latest.get("source_system"),
                "latest_trace_id": latest.get("trace_id"),
                "next_producer": _phase_owner(phase),
            }
        )
    return rows


def _phase_owner(phase: str) -> str:
    if phase.startswith("metacognition_"):
        return "research_metacognition"
    if phase in {
        "query_received",
        "source_selected",
        "result_captured",
        "page_fetch_requested",
        "page_fetched",
        "browser_opened",
        "screen_captured",
        "keyword_scan_requested",
        "keyword_file_read",
        "keyword_match_captured",
        "keyword_scan_completed",
        "online_research_goal_received",
        "online_source_discovered",
        "online_source_fetched",
        "online_source_summarized",
        "research_frame_rendered",
        "research_motion_compiled",
        "research_paper_drafted",
        "coding_brief_created",
        "coding_file_written",
        "coding_handoff_ready",
        "metacognition_ingested",
        "metacognition_concepts_extracted",
        "metacognition_routes_mapped",
        "metacognition_understanding_published",
        "knowledge_search_requested",
        "knowledge_search_completed",
    }:
        return "aureon_agent_core"
    return "search producer"


def _browser_mapping_rows(root: Path) -> List[Dict[str, Any]]:
    return [
        {
            "surface": "default browser launcher",
            "path": "aureon/autonomous/aureon_agent_core.py",
            "evidence": "webbrowser.open and search fabric browser_opened event",
            "present": "webbrowser.open" in _read_text(_rooted(root, Path("aureon/autonomous/aureon_agent_core.py"))),
        },
        {
            "surface": "screen capture",
            "path": "aureon/autonomous/aureon_agent_core.py",
            "evidence": "pyautogui screenshot and search fabric screen_captured event",
            "present": "pyautogui.screenshot" in _read_text(_rooted(root, Path("aureon/autonomous/aureon_agent_core.py"))),
        },
        {
            "surface": "browser hive UI",
            "path": "frontend/src/core/queenHiveBrowser.ts",
            "evidence": "QueenHiveBrowser broadcasts hive state to temporal ladder",
            "present": _rooted(root, Path("frontend/src/core/queenHiveBrowser.ts")).exists(),
        },
        {
            "surface": "UI browser QA artifact",
            "path": "frontend/public/aureon_complex_build_artifacts/ui_browser_qa_99b733350342.json",
            "evidence": "local browser verification capture artifact",
            "present": _rooted(root, Path("frontend/public/aureon_complex_build_artifacts/ui_browser_qa_99b733350342.json")).exists(),
        },
    ]


def _data_capture_rows(root: Path) -> List[Dict[str, Any]]:
    artifacts = [
        ("state/research_index.json", "local markdown/PDF research index cache"),
        ("state/research_readiness_index.json", "research readiness index cache"),
        ("state/self_questioning_thoughts.jsonl", "self-questioning ThoughtBus stream"),
        ("logs/aureon_thoughts.jsonl", "organism ThoughtBus stream"),
        ("thoughts.jsonl", "root ThoughtBus stream"),
        ("frontend/public/aureon_swarm_search_fabric.json", "current search fabric public snapshot"),
        ("state/aureon_swarm_search_fabric_events.jsonl", "append-only search fabric event ledger"),
        ("state/aureon_swarm_keyword_search_latest.json", "latest real local keyword scan"),
        ("frontend/public/aureon_swarm_keyword_search_latest.json", "public keyword scan evidence"),
        ("state/aureon_online_research_cinema_latest.json", "latest online research cinema packet"),
        ("frontend/public/aureon_online_research_cinema.json", "public online research cinema evidence"),
        ("state/aureon_research_metacognition_latest.json", "latest metacognitive understanding packet"),
        ("frontend/public/aureon_research_metacognition.json", "public metacognitive understanding evidence"),
        ("docs/audits/aureon_research_metacognition.json", "metacognitive understanding audit packet"),
        ("frontend/public/aureon_complex_build_artifacts/ui_browser_qa_99b733350342.json", "browser QA data capture artifact"),
    ]
    return [_artifact_row(root, rel, purpose) for rel, purpose in artifacts]


def _next_actions(source_rows: List[Mapping[str, Any]], phase_rows: List[Mapping[str, Any]], events: List[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    actions: List[Dict[str, Any]] = []
    if not events:
        actions.append(
            {
                "area": "search_fabric",
                "state": "waiting_for_first_real_search_event",
                "next_action": "perform one real web_search/web_fetch/open_url/screenshot/search_knowledge action so the fabric has live evidence",
                "authority": "no_trading_gate_bypass",
            }
        )
    for row in source_rows:
        if not row.get("wired"):
            actions.append(
                {
                    "area": row.get("id"),
                    "state": "source_wiring_attention",
                    "next_action": f"restore missing symbols: {', '.join(row.get('missing_symbols') or [])}",
                    "authority": "code_wiring_only",
                }
            )
    for row in phase_rows:
        if not row.get("seen"):
            actions.append(
                {
                    "area": row.get("phase"),
                    "state": "waiting_for_live_capture_event",
                    "next_action": f"run producer {row.get('next_producer')} through the real search/capture path",
                    "authority": "search_capture_learning_only",
                }
            )
    return actions[:24]


def build_report(*, root: Optional[Path] = None) -> Dict[str, Any]:
    root = (root or REPO_ROOT).resolve()
    source_rows = [_source_row(root, spec) for spec in SYSTEM_SPECS]
    data_capture_rows = _data_capture_rows(root)
    browser_mapping_rows = _browser_mapping_rows(root)
    events = _event_rows(root)
    phase_rows = _phase_rows(events)
    public_fabric = _read_json(_rooted(root, FABRIC_PUBLIC_PATH), {})
    summary_fabric = public_fabric.get("summary", {}) if isinstance(public_fabric, dict) else {}
    keyword_public = _read_json(_rooted(root, KEYWORD_PUBLIC_PATH), {})
    keyword_summary = keyword_public.get("summary", {}) if isinstance(keyword_public, dict) else {}
    keyword_results = keyword_public.get("results", []) if isinstance(keyword_public, dict) else []
    online_public = _read_json(_rooted(root, ONLINE_RESEARCH_PUBLIC_PATH), {})
    online_summary = online_public.get("summary", {}) if isinstance(online_public, dict) else {}
    online_sources = online_public.get("source_rows", []) if isinstance(online_public, dict) else []
    coding_handoff = online_public.get("coding_handoff", {}) if isinstance(online_public, dict) else {}
    coding_files = coding_handoff.get("generated_files", []) if isinstance(coding_handoff, dict) else []
    metacog_public = _read_json(_rooted(root, RESEARCH_METACOG_PUBLIC_PATH), {})
    metacog_summary = metacog_public.get("summary", {}) if isinstance(metacog_public, dict) else {}
    metacog_concepts = metacog_public.get("concept_rows", []) if isinstance(metacog_public, dict) else []
    metacog_routes = metacog_public.get("organism_route_rows", []) if isinstance(metacog_public, dict) else []
    metacog_unknowns = metacog_public.get("unknown_rows", []) if isinstance(metacog_public, dict) else []
    metacog_actions = metacog_public.get("test_action_rows", []) if isinstance(metacog_public, dict) else []

    wired_count = sum(1 for row in source_rows if row.get("wired"))
    capture_count = sum(1 for row in data_capture_rows if row.get("present"))
    phase_seen_count = sum(1 for row in phase_rows if row.get("seen"))
    thoughtbus_receiving = bool(summary_fabric.get("thoughtbus_receiving")) or any(row.get("thoughtbus_receipt") for row in events)
    mycelium_receiving = bool(summary_fabric.get("mycelium_receiving")) or any(row.get("mycelium_receipt") for row in events)
    source_ready = wired_count == len(source_rows)
    fabric_active = bool(events)
    status = "swarm_search_fabric_active" if source_ready and fabric_active else "swarm_search_fabric_wired_waiting_for_live_search"
    if not source_ready:
        status = "swarm_search_mapping_attention"

    next_actions = _next_actions(source_rows, phase_rows, events)
    report: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "generated_at": utc_now(),
        "mode": "real_repo_evidence_no_synthetic_capture",
        "summary": {
            "source_system_count": len(source_rows),
            "wired_source_system_count": wired_count,
            "browser_mapping_count": len(browser_mapping_rows),
            "browser_mapping_present_count": sum(1 for row in browser_mapping_rows if row.get("present")),
            "data_capture_artifact_count": len(data_capture_rows),
            "data_capture_artifact_present_count": capture_count,
            "fabric_event_count": len(events),
            "keyword_search_active": bool(keyword_results) or bool(keyword_summary.get("scanned_file_count")),
            "latest_keyword_query": keyword_public.get("keyword") if isinstance(keyword_public, dict) else None,
            "keyword_scanned_file_count": keyword_summary.get("scanned_file_count"),
            "keyword_match_file_count": keyword_summary.get("matched_file_count"),
            "keyword_match_count": keyword_summary.get("match_count"),
            "online_research_cinema_active": bool(online_summary.get("paper_created")),
            "online_research_topic": online_public.get("topic") if isinstance(online_public, dict) else None,
            "online_research_source_count": online_summary.get("fetched_source_count"),
            "online_research_frame_count": online_summary.get("frame_count"),
            "online_research_motion_ready": online_summary.get("motion_html_created"),
            "online_research_paper_created": online_summary.get("paper_created"),
            "research_coding_artifacts_created": online_summary.get("coding_artifacts_created"),
            "research_generated_file_count": online_summary.get("generated_file_count"),
            "research_metacognition_active": metacog_public.get("status") == "research_metacognition_active",
            "metacognitive_concept_count": metacog_summary.get("concept_count"),
            "metacognitive_understood_concept_count": metacog_summary.get("understood_concept_count"),
            "metacognitive_route_count": metacog_summary.get("organism_route_count"),
            "metacognitive_ready_route_count": metacog_summary.get("ready_route_count"),
            "metacognitive_unknown_count": metacog_summary.get("unknown_count"),
            "metacognitive_test_action_count": metacog_summary.get("test_action_count"),
            "metacognitive_understanding_published": bool(metacog_public.get("understanding_hash")) if isinstance(metacog_public, dict) else False,
            "phase_seen_count": phase_seen_count,
            "phase_expected_count": len(EXPECTED_PHASES),
            "thoughtbus_receiving": thoughtbus_receiving,
            "mycelium_receiving": mycelium_receiving,
            "live_search_capture_active": fabric_active,
            "no_synthetic_capture": True,
            "no_new_trading_gate": True,
            "no_external_mutation": True,
        },
        "source_system_rows": source_rows,
        "browser_mapping_rows": browser_mapping_rows,
        "data_capture_rows": data_capture_rows,
        "keyword_search_rows": keyword_results[:20] if isinstance(keyword_results, list) else [],
        "online_research_rows": online_sources[:12] if isinstance(online_sources, list) else [],
        "online_research_motion_picture": online_public.get("motion_picture", {}) if isinstance(online_public, dict) else {},
        "online_research_paper": online_public.get("paper", {}) if isinstance(online_public, dict) else {},
        "research_coding_handoff": coding_handoff,
        "research_generated_file_rows": coding_files[:20] if isinstance(coding_files, list) else [],
        "research_metacognition": metacog_public if isinstance(metacog_public, dict) else {},
        "research_metacognition_concept_rows": metacog_concepts[:20] if isinstance(metacog_concepts, list) else [],
        "research_metacognition_route_rows": metacog_routes[:20] if isinstance(metacog_routes, list) else [],
        "research_metacognition_unknown_rows": metacog_unknowns[:20] if isinstance(metacog_unknowns, list) else [],
        "research_metacognition_test_action_rows": metacog_actions[:20] if isinstance(metacog_actions, list) else [],
        "phase_rows": phase_rows,
        "recent_search_events": events[-30:],
        "next_actions": next_actions,
        "manual_boundaries": [
            "search fabric publishes organism/search evidence only",
            "page bodies are not copied into public artifacts",
            "credentials and API keys are never read or stored by this bridge",
            "Mycelium may learn from search coherence, but it cannot place orders",
            "ThoughtBus receives search phases without bypassing trading runtime gates",
        ],
        "source_paths": {
            "state": DEFAULT_STATE_PATH.as_posix(),
            "audit_json": DEFAULT_AUDIT_JSON.as_posix(),
            "audit_md": DEFAULT_AUDIT_MD.as_posix(),
            "public_json": DEFAULT_PUBLIC_JSON.as_posix(),
            "fabric_public": FABRIC_PUBLIC_PATH.as_posix(),
            "fabric_ledger": FABRIC_LEDGER_PATH.as_posix(),
            "research_metacognition": RESEARCH_METACOG_PUBLIC_PATH.as_posix(),
        },
    }
    return report


def render_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# Swarm Search Mapping Stress Audit",
        "",
        f"Status: `{report.get('status')}`",
        f"Mode: `{report.get('mode')}`",
        "",
        "This maps Aureon's search, browser mapping, and data-capture systems into one fabric.",
        "It is real-repo evidence only and does not add trading gates or broker authority.",
        "",
        "## Summary",
    ]
    for key, value in dict(report.get("summary") or {}).items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Source Systems"])
    for row in report.get("source_system_rows", []):
        state = "wired" if row.get("wired") else "attention"
        lines.append(f"- {row.get('label')}: `{state}` -> `{row.get('path')}`")
    lines.extend(["", "## Next Actions"])
    for row in report.get("next_actions", []):
        lines.append(f"- `{row.get('area')}`: {row.get('next_action')}")
    lines.append("")
    return "\n".join(lines)


def build_and_write_report(*, root: Optional[Path] = None) -> Dict[str, Any]:
    root = (root or REPO_ROOT).resolve()
    report = build_report(root=root)
    writes = [
        _write_json(_rooted(root, DEFAULT_STATE_PATH), report),
        _write_json(_rooted(root, DEFAULT_AUDIT_JSON), report),
        _write_text(_rooted(root, DEFAULT_AUDIT_MD), render_markdown(report)),
        _write_json(_rooted(root, DEFAULT_PUBLIC_JSON), report),
    ]
    report["write_info"] = {"evidence_writes": writes}
    for rel in (DEFAULT_STATE_PATH, DEFAULT_AUDIT_JSON, DEFAULT_PUBLIC_JSON):
        _write_json(_rooted(root, rel), report)
    return report


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish swarm search mapping stress audit evidence.")
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    report = build_and_write_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        summary = report["summary"]
        print(
            f"{report['status']} sources={summary['wired_source_system_count']}/{summary['source_system_count']} "
            f"events={summary['fabric_event_count']} phases={summary['phase_seen_count']}/{summary['phase_expected_count']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
