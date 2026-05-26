"""Active search/browser/data-capture fabric.

The search fabric mirrors the trading fabric idea for research systems:
every query, browser open, page fetch, screenshot, and knowledge search can
emit a small normalized event that ThoughtBus and Mycelium can see. It stores
metadata and hashes, not page bodies or credentials.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
LEDGER_PATH = Path("state/aureon_swarm_search_fabric_events.jsonl")
STATE_PATH = Path("state/aureon_swarm_search_fabric_latest.json")
PUBLIC_PATH = Path("frontend/public/aureon_swarm_search_fabric.json")

SCHEMA_VERSION = "aureon-swarm-search-fabric-v1"
AUTHORITY_MODE = "search_capture_learning_only"


def _rooted(root: Optional[Path], rel: Path) -> Path:
    base = Path(root or REPO_ROOT).resolve()
    return rel if rel.is_absolute() else base / rel


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_id(prefix: str, *parts: Any) -> str:
    raw = "|".join(str(part) for part in parts if part is not None)
    digest = hashlib.sha256(raw.encode("utf-8", errors="replace")).hexdigest()[:18]
    return f"{prefix}-{digest}"


def _safe_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    os.replace(tmp_path, path)


def _append_jsonl(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True, default=str) + "\n")


def _tail_jsonl(path: Path, limit: int = 80, max_bytes: int = 512_000) -> list[Dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[Dict[str, Any]] = []
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


def build_search_event(
    *,
    phase: str,
    source_system: str,
    query: Optional[str] = None,
    url: Optional[str] = None,
    trace_id: Optional[str] = None,
    query_id: Optional[str] = None,
    capture_id: Optional[str] = None,
    result_count: Optional[int] = None,
    status: str = "observed",
    source: Optional[str] = None,
    data_capture_mode: str = "metadata_hash_only",
    browser_mapping: Optional[str] = None,
    error: Optional[str] = None,
    metadata: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a normalized event envelope for search and capture producers."""

    timestamp = _utc_now()
    normalized_query = (query or "").strip()
    normalized_url = (url or "").strip()
    trace = trace_id or _hash_id("search-trace", source_system, normalized_query, normalized_url, int(time.time() // 60))
    qid = query_id or _hash_id("query", normalized_query or normalized_url or source_system)
    cid = capture_id or _hash_id("capture", trace, phase, normalized_url, result_count, status)
    event_id = _hash_id("search-event", trace, phase, cid, timestamp)

    event: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "event_id": event_id,
        "trace_id": trace,
        "query_id": qid,
        "capture_id": cid,
        "phase": phase,
        "source_system": source_system,
        "authority_mode": AUTHORITY_MODE,
        "timestamp": timestamp,
        "query": normalized_query,
        "query_hash": _hash_id("query-hash", normalized_query) if normalized_query else "",
        "url": normalized_url,
        "url_hash": _hash_id("url-hash", normalized_url) if normalized_url else "",
        "source": source or "unknown",
        "status": status,
        "result_count": int(result_count or 0),
        "data_capture_mode": data_capture_mode,
        "browser_mapping": browser_mapping or "repo_browser_search_capture",
        "credential_boundary": "no_credentials_read",
        "mutation_scope": "no_external_mutation",
        "no_trading_gate_bypass": True,
        "rate_budget": {
            "rate_limit_family": "search_capture_local_budget",
            "rate_remaining": None,
            "api_budget_source": "producer_local_metadata",
            "retry_after": None,
        },
        "metadata": dict(metadata or {}),
    }
    if error:
        event["error"] = str(error)[:500]
    return event


def _publish_to_thoughtbus(event: Mapping[str, Any]) -> bool:
    try:
        from aureon.core.aureon_thought_bus import Thought, get_thought_bus

        bus = get_thought_bus()
        bus.publish(
            Thought(
                source=str(event.get("source_system") or "swarm_search_fabric"),
                topic=f"search.fabric.{event.get('phase')}",
                trace_id=str(event.get("trace_id") or ""),
                payload=dict(event),
                meta={"fabric": "swarm_search"},
            )
        )
        return True
    except Exception:
        return False


def _publish_to_mycelium(event: Mapping[str, Any]) -> bool:
    try:
        from aureon.core.aureon_mycelium import get_mycelium

        mycelium = get_mycelium()
        status = str(event.get("status") or "")
        confidence = 0.75 if status in {"ok", "success", "observed"} else 0.35
        signal = 0.2 if str(event.get("phase") or "").endswith(("captured", "completed", "fetched")) else 0.05
        mycelium.receive_external_signal("swarm_search_fabric", signal=signal, confidence=confidence)
        return True
    except Exception:
        return False


def publish_search_event(
    *,
    phase: str,
    source_system: str,
    query: Optional[str] = None,
    url: Optional[str] = None,
    trace_id: Optional[str] = None,
    query_id: Optional[str] = None,
    capture_id: Optional[str] = None,
    result_count: Optional[int] = None,
    status: str = "observed",
    source: Optional[str] = None,
    data_capture_mode: str = "metadata_hash_only",
    browser_mapping: Optional[str] = None,
    error: Optional[str] = None,
    metadata: Optional[Mapping[str, Any]] = None,
    root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Publish an event to ledger, latest/public snapshot, ThoughtBus, and Mycelium."""

    event = build_search_event(
        phase=phase,
        source_system=source_system,
        query=query,
        url=url,
        trace_id=trace_id,
        query_id=query_id,
        capture_id=capture_id,
        result_count=result_count,
        status=status,
        source=source,
        data_capture_mode=data_capture_mode,
        browser_mapping=browser_mapping,
        error=error,
        metadata=metadata,
    )
    ledger_path = _rooted(root, LEDGER_PATH)
    state_path = _rooted(root, STATE_PATH)
    public_path = _rooted(root, PUBLIC_PATH)
    _append_jsonl(ledger_path, event)

    recent_events = _tail_jsonl(ledger_path, limit=80)
    phases: Dict[str, int] = {}
    traces = set()
    for row in recent_events:
        phases[str(row.get("phase") or "unknown")] = phases.get(str(row.get("phase") or "unknown"), 0) + 1
        if row.get("trace_id"):
            traces.add(str(row.get("trace_id")))

    thoughtbus_receipt = _publish_to_thoughtbus(event)
    mycelium_receipt = _publish_to_mycelium(event)
    event["thoughtbus_receipt"] = thoughtbus_receipt
    event["mycelium_receipt"] = mycelium_receipt

    snapshot = {
        "schema_version": SCHEMA_VERSION,
        "status": "swarm_search_fabric_active",
        "generated_at": _utc_now(),
        "mode": AUTHORITY_MODE,
        "summary": {
            "recent_event_count": len(recent_events),
            "active_trace_count": len(traces),
            "phase_count": len(phases),
            "thoughtbus_receiving": thoughtbus_receipt,
            "mycelium_receiving": mycelium_receipt,
            "latest_phase": event.get("phase"),
            "latest_source_system": event.get("source_system"),
            "no_trading_gate_bypass": True,
            "no_external_mutation": True,
        },
        "phase_counts": phases,
        "latest_event": event,
        "recent_events": recent_events[-30:],
        "source_paths": {
            "ledger": LEDGER_PATH.as_posix(),
            "state": STATE_PATH.as_posix(),
            "public": PUBLIC_PATH.as_posix(),
        },
    }
    _safe_write_json(state_path, snapshot)
    _safe_write_json(public_path, snapshot)
    return event

