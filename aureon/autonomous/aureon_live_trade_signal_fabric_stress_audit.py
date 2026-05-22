"""Stress burn-down audit for the live trade signal fabric.

This audit is evidence-only. It does not place, close, or mutate broker orders.
It classifies chain gaps, producer gaps, broker-proof gaps, and rate-budget gaps
so producers can repair the A-to-B trade flow with explicit next actions.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from aureon.trading.live_trade_signal_fabric import PHASE_SEQUENCE


SCHEMA_VERSION = "aureon-live-trade-signal-fabric-stress-audit-v1"
REPO_ROOT = Path(__file__).resolve().parents[2]

FABRIC_STATE_PATH = Path("state/aureon_live_trade_signal_fabric_latest.json")
FABRIC_PUBLIC_PATH = Path("frontend/public/aureon_live_trade_signal_fabric.json")
FABRIC_EVENTS_PATH = Path("state/aureon_live_trade_signal_fabric_events.jsonl")
LIFECYCLE_STATE_PATH = Path("state/unified_order_lifecycle_latest.json")
RUNTIME_STATUS_PATH = Path("state/unified_runtime_status.json")

DEFAULT_STATE_PATH = Path("state/aureon_live_trade_signal_fabric_stress_audit_last_run.json")
DEFAULT_AUDIT_JSON = Path("docs/audits/aureon_live_trade_signal_fabric_stress_audit.json")
DEFAULT_AUDIT_MD = Path("docs/audits/aureon_live_trade_signal_fabric_stress_audit.md")
DEFAULT_PUBLIC_JSON = Path("frontend/public/aureon_live_trade_signal_fabric_stress_audit.json")

CORE_CHAIN_PHASES = [
    "signal_generated",
    "counter_intel_passed",
    "candidate_ready",
    "intent_published",
    "executor_accepted",
    "order_submitted",
    "broker_acknowledged",
    "position_open",
    "close_requested",
    "close_acknowledged",
    "position_closed",
    "outcome_recorded",
]

BROKER_SENSITIVE_PHASES = {
    "order_submitted",
    "broker_acknowledged",
    "position_open",
    "close_requested",
    "close_acknowledged",
    "position_closed",
    "outcome_recorded",
}

EXTERNAL_MUTATION_PHASES = {
    "executor_accepted",
    "order_submitted",
    "broker_acknowledged",
    "position_open",
    "close_requested",
    "close_acknowledged",
    "position_closed",
    "outcome_recorded",
}

MANUAL_BOUNDARIES = [
    "stress audit is read-only evidence",
    "no direct broker order submission",
    "no direct close request",
    "no direct cancel request",
    "no credential read or reveal",
    "live broker mutation remains under existing executor/runtime/risk gates",
]

SYNTHETIC_MARKER_TOKENS = {
    "mock",
    "mock_broker",
    "sandbox",
    "sandbox_paper",
    "synthetic",
    "fixture",
    "unit_test",
    "unit-test",
    "dry_run",
    "dry-run",
    "simulated",
    "demo_mode",
}

REAL_ONLY_ALLOWED_PROOF_MODE_EXACT = {
    "live",
    "live_runtime",
    "live_broker",
    "live_observed",
    "production_live",
    "runtime_live",
    "broker_stream",
    "broker_rest",
    "capital_live",
}

REAL_ONLY_ALLOWED_PROOF_MODE_PREFIX = (
    "live_",
    "runtime_",
    "broker_",
    "production_",
)

REAL_ONLY_ALLOWED_VERIFICATION_PREFIX = (
    "capital_",
    "alpaca_",
    "binance_",
    "kraken_",
    "broker_",
    "runtime_",
    "exchange_",
    "terminal_",
    "unified_",
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _default_root() -> Path:
    cwd = Path.cwd().resolve()
    return cwd if (cwd / "aureon").exists() and (cwd / "frontend").exists() else REPO_ROOT


def _rooted(root: Path, rel: Path) -> Path:
    return rel if rel.is_absolute() else root / rel


def _read_json(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default
    return default


def _tail_jsonl(path: Path, limit: int = 5000) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                text = line.strip()
                if not text:
                    continue
                try:
                    row = json.loads(text)
                    if isinstance(row, dict):
                        rows.append(row)
                except Exception:
                    continue
    except Exception:
        return []
    return rows[-limit:]


def _write_text(path: Path, content: str) -> Dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return {"path": str(path), "bytes": len(content.encode("utf-8"))}


def _write_json(path: Path, payload: Dict[str, Any]) -> Dict[str, Any]:
    return _write_text(path, json.dumps(payload, indent=2, sort_keys=True, default=str))


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
        return number if math.isfinite(number) else default
    except Exception:
        return default


def _as_optional_float(value: Any) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except Exception:
        return None


def _percentile(values: Sequence[float], percentile: float) -> Optional[float]:
    clean = sorted(value for value in values if math.isfinite(value))
    if not clean:
        return None
    if len(clean) == 1:
        return round(clean[0], 3)
    rank = (len(clean) - 1) * max(0.0, min(100.0, percentile)) / 100.0
    lower = int(math.floor(rank))
    upper = int(math.ceil(rank))
    if lower == upper:
        return round(clean[lower], 3)
    weight = rank - lower
    return round(clean[lower] * (1.0 - weight) + clean[upper] * weight, 3)


def _parse_ts(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.timestamp()
    except Exception:
        return 0.0


def _runtime_writer_scope(runtime_status: Dict[str, Any]) -> Dict[str, Any]:
    writer = runtime_status.get("runtime_writer") if isinstance(runtime_status.get("runtime_writer"), dict) else {}
    instance_id = str(writer.get("instance_id") or "")
    pid_raw = writer.get("pid")
    heartbeat_at = str(writer.get("heartbeat_at") or "")
    started_at_ts = 0.0
    if instance_id and ":" in instance_id:
        try:
            started_at_ts = float(instance_id.split(":", 1)[1])
        except Exception:
            started_at_ts = 0.0
    if started_at_ts <= 0:
        started_at_ts = _parse_ts(runtime_status.get("last_tick_completed_at"))
    started_at = datetime.fromtimestamp(started_at_ts, tz=timezone.utc).isoformat() if started_at_ts > 0 else ""
    return {
        "instance_id": instance_id,
        "pid": int(pid_raw) if isinstance(pid_raw, (int, float)) else 0,
        "started_at": started_at,
        "started_at_ts": started_at_ts,
        "heartbeat_at": heartbeat_at,
    }


def _rows_in_session(rows: Sequence[Dict[str, Any]], session_scope: Dict[str, Any]) -> List[Dict[str, Any]]:
    started_at_ts = float(session_scope.get("started_at_ts") or 0.0)
    if started_at_ts <= 0:
        return list(rows)
    return [row for row in rows if _parse_ts(row.get("generated_at")) >= started_at_ts]


def _trace_groups(events: Iterable[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in events:
        if not isinstance(row, dict):
            continue
        trace_id = str(row.get("trace_id") or row.get("lifecycle_id") or row.get("event_id") or "")
        if not trace_id:
            continue
        grouped[trace_id].append(row)
    for rows in grouped.values():
        rows.sort(key=lambda event: _parse_ts(event.get("generated_at")))
    return grouped


def _lifecycle_rows(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for source in (
        state.get("active_lifecycles") if isinstance(state.get("active_lifecycles"), list) else [],
        state.get("lifecycles") if isinstance(state.get("lifecycles"), list) else [],
    ):
        for row in source:
            if not isinstance(row, dict):
                continue
            key = str(row.get("lifecycle_id") or "")
            if key and key in seen:
                continue
            if key:
                seen.add(key)
            rows.append(row)
    return rows


def _lifecycle_map(state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    mapping: Dict[str, Dict[str, Any]] = {}
    for row in _lifecycle_rows(state):
        lifecycle_id = str(row.get("lifecycle_id") or "")
        if lifecycle_id and lifecycle_id not in mapping:
            mapping[lifecycle_id] = row
    return mapping


def _is_capital_venue(value: Any) -> bool:
    text = str(value or "").lower()
    return text in {"capital", "capital.com", "capital_cfd"}


def _missing_chain_phases(phases: Sequence[str]) -> List[str]:
    highest = max((CORE_CHAIN_PHASES.index(phase) for phase in phases if phase in CORE_CHAIN_PHASES), default=-1)
    if highest < 0:
        return []
    required = CORE_CHAIN_PHASES[: highest + 1]
    return [phase for phase in required if phase not in phases]


def _required_ids_for_phase(phase: str) -> List[str]:
    required = ["trace_id"]
    if phase in {"candidate_ready", "intent_published", "executor_accepted"} | BROKER_SENSITIVE_PHASES:
        required.extend(["lifecycle_id", "candidate_id", "route_key"])
    if phase in {"intent_published", "executor_accepted"} | BROKER_SENSITIVE_PHASES:
        required.append("intent_id")
    if phase in BROKER_SENSITIVE_PHASES:
        required.extend(["venue", "symbol", "side"])
    return list(dict.fromkeys(required))


def _id_gaps_for_event(event: Dict[str, Any]) -> List[str]:
    phase = str(event.get("phase") or "")
    required = _required_ids_for_phase(phase)
    return [field for field in required if not str(event.get(field) or "").strip()]


def _rate_gap_for_event(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    phase = str(event.get("phase") or "")
    missing_fields = [str(item) for item in (event.get("missing_rate_budget_fields") or []) if str(item)]
    missing_tags = [str(item) for item in (event.get("missing_api_budget_tags") or []) if str(item)]
    certified = bool(event.get("rate_budget_certified"))
    if missing_fields or missing_tags or (phase in BROKER_SENSITIVE_PHASES and not certified):
        return {
            "trace_id": str(event.get("trace_id") or ""),
            "lifecycle_id": str(event.get("lifecycle_id") or ""),
            "phase": phase,
            "venue": str(event.get("venue") or ""),
            "rate_limit_family": str(event.get("rate_limit_family") or ""),
            "rate_remaining": event.get("rate_remaining"),
            "api_budget_source": str(event.get("api_budget_source") or ""),
            "missing_rate_budget_fields": missing_fields,
            "missing_api_budget_tags": missing_tags,
            "rate_budget_certified": certified,
        }
    return None


def _broker_gap_for_event(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    phase = str(event.get("phase") or "")
    if phase not in BROKER_SENSITIVE_PHASES:
        return None
    venue = str(event.get("venue") or "").lower()
    missing: List[str] = []
    deal_ref = str(event.get("deal_reference") or "")
    deal_id = str(event.get("deal_id") or "")
    broker_order_id = str(event.get("broker_order_id") or "")
    verification_source = str(event.get("verification_source") or "")
    client_order_id = str(event.get("client_order_id") or "")
    if _is_capital_venue(venue):
        if phase == "order_submitted" and not (deal_ref or client_order_id):
            missing.append("deal_reference_or_client_order_id")
        if phase in {"broker_acknowledged", "position_open", "close_requested", "close_acknowledged", "position_closed"} and not (deal_id or broker_order_id):
            missing.append("deal_id_or_broker_order_id")
        if phase in {"position_closed", "outcome_recorded"} and not verification_source:
            missing.append("verification_source")
        if phase == "position_closed" and event.get("position_absence_verified") not in (True, "true", "True"):
            missing.append("position_absence_verified")
        if phase == "outcome_recorded" and event.get("net_pnl") in (None, ""):
            missing.append("net_pnl")
    else:
        if phase in {"order_submitted", "broker_acknowledged", "position_open"} and not (client_order_id or broker_order_id):
            missing.append("client_or_broker_order_id")
        if phase in {"position_closed", "outcome_recorded"} and not verification_source:
            missing.append("verification_source")
    if missing:
        return {
            "trace_id": str(event.get("trace_id") or ""),
            "lifecycle_id": str(event.get("lifecycle_id") or ""),
            "phase": phase,
            "venue": str(event.get("venue") or ""),
            "route_key": str(event.get("route_key") or ""),
            "missing_fields": missing,
        }
    return None


def _phase_to_producer(phase: str) -> str:
    if phase in {"signal_generated", "counter_intel_passed", "counter_intel_blocked", "candidate_ready", "intent_published", "executor_accepted", "data_ready"}:
        return "unified_market_trader"
    if phase in {"order_submitted", "broker_acknowledged", "position_open", "close_requested", "close_acknowledged", "position_closed", "close_failed"}:
        return "capital_cfd_trader"
    if phase == "outcome_recorded":
        return "aureon_cognitive_trade_evidence"
    return "unknown_producer"


def _next_repair_action(phase: str, gap_type: str) -> str:
    if gap_type == "missing_phase":
        return f"Emit `{phase}` from `{_phase_to_producer(phase)}` with stable ids and route key."
    if gap_type == "missing_ids":
        return f"Attach stable ids on `{phase}` from `{_phase_to_producer(phase)}`."
    if gap_type == "rate_budget":
        return f"Attach rate-budget proof on `{phase}` from `{_phase_to_producer(phase)}`."
    if gap_type == "broker_proof":
        return f"Attach broker verification fields on `{phase}` from `{_phase_to_producer(phase)}`."
    return "Publish the next required phase with full evidence."


def _synthetic_markers_for_event(event: Dict[str, Any]) -> List[str]:
    markers: List[str] = []
    for field in (
        "proof_mode",
        "proof_tier",
        "authority_mode",
        "source_system",
        "source",
        "verification_source",
        "api_budget_source",
    ):
        value = str(event.get(field) or "").strip().lower()
        if not value:
            continue
        for token in SYNTHETIC_MARKER_TOKENS:
            if token in value:
                markers.append(f"{field}:{token}")
    if str(event.get("event_ref") or "").strip().lower().startswith("fixture"):
        markers.append("event_ref:fixture")
    if str(event.get("trace_id") or "").strip().lower().startswith("fixture"):
        markers.append("trace_id:fixture")
    return list(dict.fromkeys(markers))


def _proof_mode_is_real(value: Any) -> bool:
    mode = str(value or "").strip().lower()
    if not mode:
        return False
    if mode in REAL_ONLY_ALLOWED_PROOF_MODE_EXACT:
        return True
    if mode.startswith(REAL_ONLY_ALLOWED_PROOF_MODE_PREFIX):
        return True
    return False


def _verification_source_is_real(value: Any) -> bool:
    source = str(value or "").strip().lower()
    if not source:
        return False
    if any(token in source for token in SYNTHETIC_MARKER_TOKENS):
        return False
    return source.startswith(REAL_ONLY_ALLOWED_VERIFICATION_PREFIX)


def _real_evidence_gap_for_event(event: Dict[str, Any], *, real_only: bool) -> Optional[Dict[str, Any]]:
    if not real_only:
        return None
    phase = str(event.get("phase") or "")
    if not phase:
        return None
    missing: List[str] = []
    if not str(event.get("source_system") or "").strip():
        missing.append("source_system")
    if not str(event.get("generated_at") or "").strip():
        missing.append("generated_at")
    if not _proof_mode_is_real(event.get("proof_mode")):
        missing.append("proof_mode_live_runtime")
    if phase in BROKER_SENSITIVE_PHASES:
        verification_source = event.get("verification_source")
        if not _verification_source_is_real(verification_source):
            missing.append("verification_source_real")
    if missing:
        return {
            "trace_id": str(event.get("trace_id") or ""),
            "lifecycle_id": str(event.get("lifecycle_id") or ""),
            "phase": phase,
            "producer": _phase_to_producer(phase),
            "venue": str(event.get("venue") or ""),
            "route_key": str(event.get("route_key") or ""),
            "missing_real_evidence": missing,
            "next_repair_action": f"Attach real-evidence proof fields on `{phase}` from `{_phase_to_producer(phase)}`.",
        }
    return None


def _is_recovered_trace(
    trace_rows: Sequence[Dict[str, Any]],
    lifecycle_row: Optional[Dict[str, Any]],
    missing_phases: Sequence[str],
) -> bool:
    if lifecycle_row:
        last_event = lifecycle_row.get("last_event") if isinstance(lifecycle_row.get("last_event"), dict) else {}
        if str(last_event.get("event_type") or "") == "position_recovered":
            return True
        if str(last_event.get("reason") or "") == "broker_position_reconciled_on_startup":
            return True
    for row in trace_rows:
        if str(row.get("event_type") or "") == "position_recovered":
            return True
        if str(row.get("reason") or "") == "broker_position_reconciled_on_startup":
            return True
    return bool(missing_phases) and any(
        str(row.get("phase") or "") in {"broker_acknowledged", "position_open", "close_requested", "close_acknowledged", "position_closed"}
        for row in trace_rows
    )


def _classify_trace(
    trace_id: str,
    trace_rows: Sequence[Dict[str, Any]],
    lifecycle_row: Optional[Dict[str, Any]],
    *,
    real_only: bool = False,
) -> Dict[str, Any]:
    phases = [str(row.get("phase") or "") for row in trace_rows]
    highest_phase_index = max((CORE_CHAIN_PHASES.index(phase) for phase in phases if phase in CORE_CHAIN_PHASES), default=-1)
    highest_chain_phase = CORE_CHAIN_PHASES[highest_phase_index] if highest_phase_index >= 0 else ""
    latest = trace_rows[-1] if trace_rows else {}
    missing_phases = _missing_chain_phases(phases)
    id_gap_rows: List[Dict[str, Any]] = []
    rate_gap_rows: List[Dict[str, Any]] = []
    broker_gap_rows: List[Dict[str, Any]] = []
    real_evidence_gap_rows: List[Dict[str, Any]] = []
    synthetic_markers: List[str] = []
    external_live_route = False
    for row in trace_rows:
        phase = str(row.get("phase") or "")
        synthetic_markers.extend(_synthetic_markers_for_event(row))
        id_missing = _id_gaps_for_event(row)
        if id_missing:
            id_gap_rows.append(
                {
                    "trace_id": trace_id,
                    "phase": phase,
                    "producer": _phase_to_producer(phase),
                    "missing_ids": id_missing,
                    "next_repair_action": _next_repair_action(phase, "missing_ids"),
                }
            )
        rate_gap = _rate_gap_for_event(row)
        if rate_gap:
            rate_gap["producer"] = _phase_to_producer(phase)
            rate_gap["next_repair_action"] = _next_repair_action(phase, "rate_budget")
            rate_gap_rows.append(rate_gap)
        broker_gap = _broker_gap_for_event(row)
        if broker_gap:
            broker_gap["producer"] = _phase_to_producer(phase)
            broker_gap["next_repair_action"] = _next_repair_action(phase, "broker_proof")
            broker_gap_rows.append(broker_gap)
        real_gap = _real_evidence_gap_for_event(row, real_only=real_only)
        if real_gap:
            real_evidence_gap_rows.append(real_gap)
        if not _is_capital_venue(row.get("venue")) and phase in EXTERNAL_MUTATION_PHASES:
            external_live_route = True

    classification = "complete_chain"
    if missing_phases or id_gap_rows or rate_gap_rows or broker_gap_rows or real_evidence_gap_rows:
        classification = "broken_chain"
    recovered = _is_recovered_trace(trace_rows, lifecycle_row, missing_phases)
    if recovered and classification != "complete_chain":
        classification = "recovered_downstream_context"
    if rate_gap_rows and not missing_phases and not id_gap_rows and not broker_gap_rows:
        classification = "rate_budget_missing"
    if broker_gap_rows and not missing_phases:
        classification = "broker_proof_missing"
    if real_evidence_gap_rows and not missing_phases and not id_gap_rows and not rate_gap_rows and not broker_gap_rows:
        classification = "real_evidence_missing"
    if external_live_route:
        classification = "external_shadow_only"
    synthetic_markers = list(dict.fromkeys(synthetic_markers))
    has_synthetic_markers = bool(synthetic_markers)
    if has_synthetic_markers and classification == "complete_chain":
        classification = "synthetic_trace_detected"

    stable_id_gaps = sorted(
        {
            str(field)
            for row in id_gap_rows
            for field in (row.get("missing_ids") or [])
            if str(field)
        }
    )
    rate_budget_missing_phases = sorted({str(row.get("phase") or "") for row in rate_gap_rows if str(row.get("phase") or "")})
    broker_requirement_gaps = sorted(
        {
            str(field)
            for row in broker_gap_rows
            for field in (row.get("missing_fields") or [])
            if str(field)
        }
    )
    next_required_phase = ""
    latest_phase = str(latest.get("phase") or "")
    if missing_phases:
        next_required_phase = str(missing_phases[0] or "")
    elif highest_chain_phase:
        idx = CORE_CHAIN_PHASES.index(highest_chain_phase) + 1
        if idx < len(CORE_CHAIN_PHASES):
            next_required_phase = CORE_CHAIN_PHASES[idx]
    next_producer_to_fix = _phase_to_producer(next_required_phase) if next_required_phase else ""
    next_repair_action = ""
    if id_gap_rows:
        next_repair_action = str(id_gap_rows[0].get("next_repair_action") or "")
    elif rate_gap_rows:
        next_repair_action = str(rate_gap_rows[0].get("next_repair_action") or "")
    elif broker_gap_rows:
        next_repair_action = str(broker_gap_rows[0].get("next_repair_action") or "")
    elif real_evidence_gap_rows:
        next_repair_action = str(real_evidence_gap_rows[0].get("next_repair_action") or "")
    elif next_required_phase:
        next_repair_action = _next_repair_action(next_required_phase, "missing_phase")
    blocked_before_broker_mutation = (
        bool(next_required_phase)
        and (
            next_required_phase in {"signal_generated", "counter_intel_passed", "candidate_ready", "intent_published", "executor_accepted"}
            or latest_phase in {"signal_generated", "counter_intel_passed", "candidate_ready", "intent_published", "executor_accepted", "data_ready"}
        )
    )

    return {
        "trace_id": trace_id,
        "lifecycle_id": str(latest.get("lifecycle_id") or ""),
        "route_key": str(latest.get("route_key") or ""),
        "venue": str(latest.get("venue") or ""),
        "symbol": str(latest.get("symbol") or ""),
        "side": str(latest.get("side") or ""),
        "latest_phase": str(latest.get("phase") or ""),
        "highest_chain_phase": highest_chain_phase,
        "generated_at": str(latest.get("generated_at") or ""),
        "classification": classification,
        "missing_phases": missing_phases,
        "id_gap_count": len(id_gap_rows),
        "rate_gap_count": len(rate_gap_rows),
        "broker_gap_count": len(broker_gap_rows),
        "real_evidence_gap_count": len(real_evidence_gap_rows),
        "external_live_route": external_live_route,
        "synthetic_markers": synthetic_markers,
        "has_synthetic_markers": has_synthetic_markers,
        "recovered_downstream_context": recovered,
        "publisher_gap_rows": id_gap_rows,
        "api_budget_gap_rows": rate_gap_rows,
        "broker_requirement_gap_rows": broker_gap_rows,
        "real_evidence_gap_rows": real_evidence_gap_rows,
        "missing_required_phases": list(missing_phases),
        "stable_id_gaps": stable_id_gaps,
        "rate_budget_missing_phases": rate_budget_missing_phases,
        "broker_requirement_gaps": broker_requirement_gaps,
        "next_required_phase": next_required_phase,
        "next_producer_to_fix": next_producer_to_fix,
        "next_repair_action": next_repair_action,
        "blocked_before_broker_mutation": blocked_before_broker_mutation,
        "publisher_owner": str(latest.get("publisher_owner") or ""),
        "dedupe_applied": bool(latest.get("dedupe_applied")),
    }


def _executor_gate_respected(runtime_status: Dict[str, Any], traces: Sequence[Dict[str, Any]]) -> bool:
    runtime_clearances = [str(item) for item in (runtime_status.get("runtime_clearances") or []) if str(item)]
    gates_blocked = any(
        blocker in runtime_clearances
        for blocker in (
            "unified_order_executor_disabled",
            "live_trading_not_enabled",
            "real_orders_disabled",
            "exchange_mutations_disabled",
            "real_orders_not_allowed_by_runtime",
        )
    )
    if not gates_blocked:
        return True
    forbidden = {
        "order_submitted",
        "broker_acknowledged",
        "position_open",
        "close_requested",
        "close_acknowledged",
        "position_closed",
        "outcome_recorded",
    }
    for trace in traces:
        if str(trace.get("venue") or "").lower() == "capital" and str(trace.get("latest_phase") or "") in forbidden:
            return False
    return True


def _phase_event_map(trace_rows: Sequence[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    mapped: Dict[str, Dict[str, Any]] = {}
    for row in sorted(trace_rows, key=lambda event: _parse_ts(event.get("generated_at"))):
        phase = str(row.get("phase") or "")
        if phase and phase not in mapped and _parse_ts(row.get("generated_at")) > 0:
            mapped[phase] = row
    return mapped


def _event_field(trace_rows: Sequence[Dict[str, Any]], field: str, default: Any = "") -> Any:
    for row in reversed(trace_rows):
        value = row.get(field)
        if value not in (None, ""):
            return value
    return default


def _event_pnl(trace_rows: Sequence[Dict[str, Any]]) -> Optional[float]:
    for row in reversed(trace_rows):
        for field in (
            "net_pnl",
            "realized_pnl",
            "realized_profit",
            "profit_loss",
            "profit",
            "pnl",
            "net_profit",
            "net_pl",
            "final_pnl",
        ):
            value = _as_optional_float(row.get(field))
            if value is not None:
                return value
    return None


def _latency_ms(start_ts: float, end_ts: float) -> Optional[float]:
    if start_ts <= 0 or end_ts <= 0 or end_ts < start_ts:
        return None
    return round((end_ts - start_ts) * 1000.0, 3)


def _speed_state_for_row(
    *,
    has_signal: bool,
    has_position_open: bool,
    has_outcome: bool,
    pnl: Optional[float],
    recovered_context: bool,
) -> str:
    if recovered_context and not has_signal:
        return "recovered_context_only"
    if has_signal and has_outcome and pnl is not None and pnl > 0:
        return "gain_speed_certified"
    if has_signal and has_outcome and pnl is not None:
        return "outcome_speed_certified_no_positive_gain"
    if has_signal and has_position_open:
        return "trade_open_speed_certified_waiting_for_gain"
    if has_signal:
        return "speed_waiting_for_position_open"
    return "speed_waiting_for_signal"


def _build_speed_rows(
    grouped: Dict[str, List[Dict[str, Any]]],
    classified_by_trace: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for trace_id, trace_events in grouped.items():
        if not trace_events:
            continue
        phase_events = _phase_event_map(trace_events)
        phase_ts = {phase: _parse_ts(row.get("generated_at")) for phase, row in phase_events.items()}
        latest = trace_events[-1]
        classification = classified_by_trace.get(trace_id, {})
        first_ts = min((_parse_ts(row.get("generated_at")) for row in trace_events if _parse_ts(row.get("generated_at")) > 0), default=0.0)
        latest_ts = _parse_ts(latest.get("generated_at"))
        signal_ts = phase_ts.get("signal_generated", 0.0)
        candidate_ts = phase_ts.get("candidate_ready", 0.0)
        intent_ts = phase_ts.get("intent_published", 0.0)
        executor_ts = phase_ts.get("executor_accepted", 0.0)
        order_ts = phase_ts.get("order_submitted", 0.0)
        broker_ack_ts = phase_ts.get("broker_acknowledged", 0.0)
        position_open_ts = phase_ts.get("position_open", 0.0)
        close_requested_ts = phase_ts.get("close_requested", 0.0)
        close_ack_ts = phase_ts.get("close_acknowledged", 0.0)
        position_closed_ts = phase_ts.get("position_closed", 0.0)
        outcome_ts = phase_ts.get("outcome_recorded", 0.0)
        pnl = _event_pnl(trace_events)
        phase_latency_ms: Dict[str, float] = {}
        for left, right in zip(CORE_CHAIN_PHASES, CORE_CHAIN_PHASES[1:]):
            latency = _latency_ms(phase_ts.get(left, 0.0), phase_ts.get(right, 0.0))
            if latency is not None:
                phase_latency_ms[f"{left}_to_{right}"] = latency
        missing_speed_phases: List[str] = []
        if signal_ts <= 0:
            missing_speed_phases.append("signal_generated")
        if position_open_ts <= 0:
            missing_speed_phases.append("position_open")
        if outcome_ts <= 0:
            missing_speed_phases.append("outcome_recorded")
        if outcome_ts > 0 and pnl is None:
            missing_speed_phases.append("net_pnl")
        if outcome_ts > 0 and pnl is not None and pnl <= 0:
            missing_speed_phases.append("positive_net_pnl")
        recovered_context = bool(classification.get("recovered_downstream_context"))
        speed_state = _speed_state_for_row(
            has_signal=signal_ts > 0,
            has_position_open=position_open_ts > 0,
            has_outcome=outcome_ts > 0,
            pnl=pnl,
            recovered_context=recovered_context,
        )
        row = {
            "trace_id": trace_id,
            "lifecycle_id": str(_event_field(trace_events, "lifecycle_id")),
            "candidate_id": str(_event_field(trace_events, "candidate_id")),
            "intent_id": str(_event_field(trace_events, "intent_id")),
            "route_key": str(_event_field(trace_events, "route_key")),
            "venue": str(_event_field(trace_events, "venue")),
            "symbol": str(_event_field(trace_events, "symbol")),
            "side": str(_event_field(trace_events, "side")),
            "latest_phase": str(latest.get("phase") or ""),
            "classification": str(classification.get("classification") or ""),
            "speed_state": speed_state,
            "phase_count": len({str(row.get("phase") or "") for row in trace_events if str(row.get("phase") or "")}),
            "event_count": len(trace_events),
            "first_event_at": datetime.fromtimestamp(first_ts, tz=timezone.utc).isoformat() if first_ts > 0 else "",
            "latest_event_at": str(latest.get("generated_at") or ""),
            "signal_at": str(phase_events.get("signal_generated", {}).get("generated_at") or ""),
            "candidate_at": str(phase_events.get("candidate_ready", {}).get("generated_at") or ""),
            "intent_at": str(phase_events.get("intent_published", {}).get("generated_at") or ""),
            "executor_at": str(phase_events.get("executor_accepted", {}).get("generated_at") or ""),
            "order_at": str(phase_events.get("order_submitted", {}).get("generated_at") or ""),
            "broker_ack_at": str(phase_events.get("broker_acknowledged", {}).get("generated_at") or ""),
            "position_open_at": str(phase_events.get("position_open", {}).get("generated_at") or ""),
            "close_requested_at": str(phase_events.get("close_requested", {}).get("generated_at") or ""),
            "close_acknowledged_at": str(phase_events.get("close_acknowledged", {}).get("generated_at") or ""),
            "position_closed_at": str(phase_events.get("position_closed", {}).get("generated_at") or ""),
            "outcome_recorded_at": str(phase_events.get("outcome_recorded", {}).get("generated_at") or ""),
            "signal_to_candidate_ms": _latency_ms(signal_ts, candidate_ts),
            "candidate_to_intent_ms": _latency_ms(candidate_ts, intent_ts),
            "intent_to_executor_ms": _latency_ms(intent_ts, executor_ts),
            "executor_to_order_ms": _latency_ms(executor_ts, order_ts),
            "order_to_broker_ack_ms": _latency_ms(order_ts, broker_ack_ts),
            "broker_ack_to_position_open_ms": _latency_ms(broker_ack_ts, position_open_ts),
            "position_open_to_close_requested_ms": _latency_ms(position_open_ts, close_requested_ts),
            "close_requested_to_close_ack_ms": _latency_ms(close_requested_ts, close_ack_ts),
            "close_ack_to_position_closed_ms": _latency_ms(close_ack_ts, position_closed_ts),
            "position_closed_to_outcome_ms": _latency_ms(position_closed_ts, outcome_ts),
            "a_to_b_ms": _latency_ms(signal_ts, position_open_ts),
            "a_to_latest_ms": _latency_ms(signal_ts, latest_ts),
            "a_to_gain_ms": _latency_ms(signal_ts, outcome_ts) if pnl is not None and pnl > 0 else None,
            "round_trip_to_outcome_ms": _latency_ms(signal_ts, outcome_ts),
            "first_event_to_latest_ms": _latency_ms(first_ts, latest_ts),
            "net_pnl": pnl,
            "gain_recorded": bool(outcome_ts > 0 and pnl is not None),
            "positive_gain_recorded": bool(outcome_ts > 0 and pnl is not None and pnl > 0),
            "complete_to_position": bool(signal_ts > 0 and position_open_ts > 0),
            "complete_to_outcome": bool(signal_ts > 0 and outcome_ts > 0),
            "missing_speed_phases": list(dict.fromkeys(missing_speed_phases)),
            "recovered_context": recovered_context,
            "phase_latency_ms": phase_latency_ms,
            "rate_budget_certified_events": sum(1 for event in trace_events if bool(event.get("rate_budget_certified"))),
            "broker_sensitive_events": sum(1 for event in trace_events if str(event.get("phase") or "") in BROKER_SENSITIVE_PHASES),
        }
        rows.append(row)
    rows.sort(
        key=lambda row: (
            0 if row.get("positive_gain_recorded") else 1,
            0 if row.get("complete_to_position") else 1,
            0 if row.get("signal_at") else 1,
            _as_float(row.get("a_to_gain_ms"), _as_float(row.get("a_to_b_ms"), 10**12)),
            -_parse_ts(row.get("latest_event_at")),
        )
    )
    return rows


def _attach_repeat_cycle_rows(speed_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped_by_route: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in speed_rows:
        route = str(row.get("route_key") or row.get("trace_id") or "")
        if route:
            grouped_by_route[route].append(row)
    repeat_rows: List[Dict[str, Any]] = []
    for route, rows in grouped_by_route.items():
        ordered = sorted(rows, key=lambda row: _parse_ts(row.get("signal_at") or row.get("first_event_at")))
        for index, row in enumerate(ordered):
            outcome_ts = _parse_ts(row.get("outcome_recorded_at"))
            if outcome_ts <= 0:
                continue
            next_signal_row: Optional[Dict[str, Any]] = None
            for candidate in ordered[index + 1:]:
                candidate_signal_ts = _parse_ts(candidate.get("signal_at"))
                if candidate_signal_ts > outcome_ts:
                    next_signal_row = candidate
                    break
            if not next_signal_row:
                continue
            repeat_ms = _latency_ms(outcome_ts, _parse_ts(next_signal_row.get("signal_at")))
            row["next_cycle_signal_after_outcome_ms"] = repeat_ms
            row["next_cycle_trace_id"] = str(next_signal_row.get("trace_id") or "")
            repeat_rows.append(
                {
                    "route_key": route,
                    "from_trace_id": row.get("trace_id"),
                    "to_trace_id": next_signal_row.get("trace_id"),
                    "outcome_recorded_at": row.get("outcome_recorded_at"),
                    "next_signal_at": next_signal_row.get("signal_at"),
                    "next_cycle_signal_after_outcome_ms": repeat_ms,
                }
            )
    return repeat_rows


def _speed_latency_rows(speed_rows: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    pair_values: Dict[str, List[float]] = defaultdict(list)
    for row in speed_rows:
        latency_map = row.get("phase_latency_ms") if isinstance(row.get("phase_latency_ms"), dict) else {}
        for key, value in latency_map.items():
            number = _as_optional_float(value)
            if number is not None:
                pair_values[str(key)].append(number)
    rows: List[Dict[str, Any]] = []
    for pair, values in pair_values.items():
        if not values:
            continue
        rows.append(
            {
                "phase_pair": pair,
                "sample_count": len(values),
                "fastest_ms": round(min(values), 3),
                "p50_ms": _percentile(values, 50),
                "p95_ms": _percentile(values, 95),
                "slowest_ms": round(max(values), 3),
            }
        )
    rows.sort(key=lambda row: _as_float(row.get("p95_ms"), 0.0), reverse=True)
    return rows


def _speed_missing_rows(speed_rows: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for row in speed_rows:
        missing = [str(item) for item in (row.get("missing_speed_phases") or []) if str(item)]
        if not missing:
            continue
        rows.append(
            {
                "trace_id": row.get("trace_id"),
                "lifecycle_id": row.get("lifecycle_id"),
                "route_key": row.get("route_key"),
                "symbol": row.get("symbol"),
                "latest_phase": row.get("latest_phase"),
                "speed_state": row.get("speed_state"),
                "missing_speed_phases": missing,
                "next_required_phase": missing[0],
            }
        )
    return rows


def _speed_numbers(speed_rows: Sequence[Dict[str, Any]], field: str) -> List[float]:
    values: List[float] = []
    for row in speed_rows:
        value = _as_optional_float(row.get(field))
        if value is not None:
            values.append(value)
    return values


def _speed_summary(speed_rows: Sequence[Dict[str, Any]], repeat_rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    a_to_b_values = _speed_numbers([row for row in speed_rows if row.get("complete_to_position")], "a_to_b_ms")
    a_to_gain_values = _speed_numbers([row for row in speed_rows if row.get("positive_gain_recorded")], "a_to_gain_ms")
    outcome_values = _speed_numbers([row for row in speed_rows if row.get("complete_to_outcome")], "round_trip_to_outcome_ms")
    repeat_values = _speed_numbers(repeat_rows, "next_cycle_signal_after_outcome_ms")
    positive_gain_count = sum(1 for row in speed_rows if bool(row.get("positive_gain_recorded")))
    outcome_count = sum(1 for row in speed_rows if bool(row.get("complete_to_outcome")))
    open_count = sum(1 for row in speed_rows if bool(row.get("complete_to_position")))
    best_state_row = next(
        (row for row in speed_rows if bool(row.get("positive_gain_recorded"))),
        next(
            (row for row in speed_rows if bool(row.get("complete_to_position"))),
            next((row for row in speed_rows if str(row.get("signal_at") or "")), speed_rows[0] if speed_rows else {}),
        ),
    )
    latest_state = str(best_state_row.get("speed_state") or "speed_waiting_for_signal") if speed_rows else "speed_waiting_for_signal"
    if positive_gain_count:
        answer = (
            f"Fastest observed A-to-gain is {_percentile(a_to_gain_values, 0)} ms; "
            f"fastest A-to-open is {_percentile(a_to_b_values, 0)} ms."
        )
    elif open_count:
        answer = (
            f"Fastest observed A-to-open is {_percentile(a_to_b_values, 0)} ms; "
            "positive P/L outcome timing has not appeared in this scope yet."
        )
    elif speed_rows:
        answer = "Signals are visible, but this scope has not reached position_open yet."
    else:
        answer = "No signal fabric timing rows are present in this scope yet."
    return {
        "speed_trace_count": len(speed_rows),
        "speed_complete_to_position_count": open_count,
        "speed_outcome_recorded_count": outcome_count,
        "speed_positive_gain_count": positive_gain_count,
        "speed_a_to_b_fastest_ms": _percentile(a_to_b_values, 0),
        "speed_a_to_b_p50_ms": _percentile(a_to_b_values, 50),
        "speed_a_to_b_p95_ms": _percentile(a_to_b_values, 95),
        "speed_a_to_gain_fastest_ms": _percentile(a_to_gain_values, 0),
        "speed_a_to_gain_p50_ms": _percentile(a_to_gain_values, 50),
        "speed_a_to_gain_p95_ms": _percentile(a_to_gain_values, 95),
        "speed_round_trip_to_outcome_fastest_ms": _percentile(outcome_values, 0),
        "speed_round_trip_to_outcome_p50_ms": _percentile(outcome_values, 50),
        "speed_round_trip_to_outcome_p95_ms": _percentile(outcome_values, 95),
        "speed_repeat_cycle_fastest_ms": _percentile(repeat_values, 0),
        "speed_repeat_cycle_p50_ms": _percentile(repeat_values, 50),
        "speed_repeat_cycle_p95_ms": _percentile(repeat_values, 95),
        "speed_latest_state": latest_state,
        "speed_current_answer": answer,
    }


def _status_from_counts(
    *,
    has_events: bool,
    broken_count: int,
    non_recovered_broken_count: int,
    recovered_count: int,
    external_leaks: int,
    synthetic_traces: int,
    real_only: bool,
    rate_gaps: int,
    broker_gaps: int,
    real_evidence_gaps: int,
) -> str:
    if not has_events:
        return "trade_flow_waiting_for_signal"
    if real_only and synthetic_traces > 0:
        return "synthetic_evidence_present"
    if real_only and real_evidence_gaps > 0:
        return "real_evidence_missing"
    if external_leaks > 0:
        return "external_live_route_leak"
    if non_recovered_broken_count > 0:
        return "live_trade_signal_fabric_stress_broken"
    if recovered_count > 0:
        return "recovered_broker_truth_attention"
    if broken_count > 0:
        return "live_trade_signal_fabric_stress_broken"
    return "live_trade_signal_fabric_stress_certified"


def build_live_trade_signal_fabric_stress_audit(
    *,
    root: Optional[Path] = None,
    now: Optional[datetime] = None,
    real_only: bool = False,
) -> Dict[str, Any]:
    root_path = Path(root or _default_root()).resolve()
    now_dt = now or utc_now()
    fabric_public = _read_json(_rooted(root_path, FABRIC_PUBLIC_PATH), {})
    fabric_state = _read_json(_rooted(root_path, FABRIC_STATE_PATH), {})
    lifecycle_state = _read_json(_rooted(root_path, LIFECYCLE_STATE_PATH), {})
    runtime_status = _read_json(_rooted(root_path, RUNTIME_STATUS_PATH), {})
    runtime_scope = _runtime_writer_scope(runtime_status if isinstance(runtime_status, dict) else {})
    rows = _tail_jsonl(_rooted(root_path, FABRIC_EVENTS_PATH), limit=5000)
    if not rows:
        source = fabric_state if isinstance(fabric_state, dict) and fabric_state else fabric_public
        rows = source.get("events") if isinstance(source.get("events"), list) else []
    rows = [row for row in rows if isinstance(row, dict)]
    session_rows = _rows_in_session(rows, runtime_scope)

    grouped = _trace_groups(rows)
    grouped_session = _trace_groups(session_rows)
    lifecycle_by_id = _lifecycle_map(lifecycle_state if isinstance(lifecycle_state, dict) else {})
    trace_rows: List[Dict[str, Any]] = []
    for trace_id, events in grouped.items():
        latest = events[-1] if events else {}
        lifecycle_id = str(latest.get("lifecycle_id") or "")
        trace_rows.append(_classify_trace(trace_id, events, lifecycle_by_id.get(lifecycle_id), real_only=real_only))
    trace_rows.sort(key=lambda row: str(row.get("generated_at") or ""), reverse=True)
    trace_rows_session: List[Dict[str, Any]] = []
    for trace_id, events in grouped_session.items():
        latest = events[-1] if events else {}
        lifecycle_id = str(latest.get("lifecycle_id") or "")
        trace_rows_session.append(_classify_trace(trace_id, events, lifecycle_by_id.get(lifecycle_id), real_only=real_only))
    trace_rows_session.sort(key=lambda row: str(row.get("generated_at") or ""), reverse=True)
    classified_by_trace = {str(row.get("trace_id") or ""): row for row in trace_rows if str(row.get("trace_id") or "")}
    classified_by_trace_session = {
        str(row.get("trace_id") or ""): row for row in trace_rows_session if str(row.get("trace_id") or "")
    }
    speed_trace_rows = _build_speed_rows(grouped, classified_by_trace)
    speed_repeat_cycle_rows = _attach_repeat_cycle_rows(speed_trace_rows)
    speed_trace_rows_session = _build_speed_rows(grouped_session, classified_by_trace_session)
    speed_repeat_cycle_rows_session = _attach_repeat_cycle_rows(speed_trace_rows_session)
    speed_scope_rows = speed_trace_rows_session if speed_trace_rows_session else speed_trace_rows
    speed_scope_repeat_rows = speed_repeat_cycle_rows_session if speed_trace_rows_session else speed_repeat_cycle_rows
    speed_latency_rows = _speed_latency_rows(speed_scope_rows)
    speed_missing_phase_rows = _speed_missing_rows(speed_scope_rows)
    speed_summary = _speed_summary(speed_scope_rows, speed_scope_repeat_rows)

    burn_down_rows: List[Dict[str, Any]] = []
    publisher_gap_rows: List[Dict[str, Any]] = []
    api_budget_gap_rows: List[Dict[str, Any]] = []
    broker_requirement_gap_rows: List[Dict[str, Any]] = []
    real_evidence_gap_rows: List[Dict[str, Any]] = []
    recovered_trace_rows: List[Dict[str, Any]] = []
    synthetic_trace_rows: List[Dict[str, Any]] = []
    external_confirmation_rows: List[Dict[str, Any]] = []
    complete_capital_chain_count = 0
    for trace in trace_rows:
        classification = str(trace.get("classification") or "")
        if classification == "complete_chain" and _is_capital_venue(trace.get("venue")):
            complete_capital_chain_count += 1
        if classification in {
            "broken_chain",
            "recovered_downstream_context",
            "rate_budget_missing",
            "broker_proof_missing",
            "real_evidence_missing",
            "external_shadow_only",
            "synthetic_trace_detected",
        }:
            burn_down_rows.append(
                {
                    "trace_id": trace.get("trace_id"),
                    "lifecycle_id": trace.get("lifecycle_id"),
                    "route_key": trace.get("route_key"),
                    "venue": trace.get("venue"),
                    "symbol": trace.get("symbol"),
                    "latest_phase": trace.get("latest_phase"),
                    "classification": classification,
                    "missing_phases": trace.get("missing_phases"),
                    "missing_required_phases": trace.get("missing_required_phases") or trace.get("missing_phases") or [],
                    "missing_phase_count": len(trace.get("missing_required_phases") or trace.get("missing_phases") or []),
                    "id_gap_count": trace.get("id_gap_count"),
                    "rate_gap_count": trace.get("rate_gap_count"),
                    "broker_gap_count": trace.get("broker_gap_count"),
                    "real_evidence_gap_count": trace.get("real_evidence_gap_count"),
                    "external_live_route": bool(trace.get("external_live_route")),
                    "synthetic_markers": trace.get("synthetic_markers") or [],
                    "stable_id_gaps": trace.get("stable_id_gaps") or [],
                    "rate_budget_missing_phases": trace.get("rate_budget_missing_phases") or [],
                    "broker_requirement_gaps": trace.get("broker_requirement_gaps") or [],
                    "next_required_phase": trace.get("next_required_phase") or "",
                    "next_producer_to_fix": trace.get("next_producer_to_fix") or "",
                    "next_repair_action": trace.get("next_repair_action") or "",
                    "blocked_before_broker_mutation": bool(trace.get("blocked_before_broker_mutation")),
                    "publisher_owner": trace.get("publisher_owner") or "",
                    "dedupe_applied": bool(trace.get("dedupe_applied")),
                }
            )
        if trace.get("recovered_downstream_context"):
            recovered_trace_rows.append(
                {
                    "trace_id": trace.get("trace_id"),
                    "lifecycle_id": trace.get("lifecycle_id"),
                    "route_key": trace.get("route_key"),
                    "latest_phase": trace.get("latest_phase"),
                    "recovered_broker_truth_certified": bool(
                        str(trace.get("latest_phase") or "") in {"broker_acknowledged", "position_open", "close_requested", "close_acknowledged", "position_closed", "outcome_recorded"}
                        and _is_capital_venue(trace.get("venue"))
                    ),
                    "recovered_upstream_context_missing": bool(trace.get("missing_phases")),
                    "missing_phases": trace.get("missing_phases"),
                }
            )
        publisher_gap_rows.extend(trace.get("publisher_gap_rows") or [])
        api_budget_gap_rows.extend(trace.get("api_budget_gap_rows") or [])
        broker_requirement_gap_rows.extend(trace.get("broker_requirement_gap_rows") or [])
        real_evidence_gap_rows.extend(trace.get("real_evidence_gap_rows") or [])
        if trace.get("external_live_route"):
            external_confirmation_rows.append(
                {
                    "trace_id": trace.get("trace_id"),
                    "route_key": trace.get("route_key"),
                    "venue": trace.get("venue"),
                    "latest_phase": trace.get("latest_phase"),
                    "classification": "external_live_route_leak",
                }
            )
        if bool(trace.get("has_synthetic_markers")):
            synthetic_trace_rows.append(
                {
                    "trace_id": trace.get("trace_id"),
                    "lifecycle_id": trace.get("lifecycle_id"),
                    "route_key": trace.get("route_key"),
                    "latest_phase": trace.get("latest_phase"),
                    "synthetic_markers": trace.get("synthetic_markers") or [],
                }
            )
    session_broken_trace_count = sum(1 for row in trace_rows_session if str(row.get("classification") or "") != "complete_chain")
    session_api_budget_gap_count = sum(int(row.get("rate_gap_count") or 0) for row in trace_rows_session)
    session_complete_capital_chain_count = sum(
        1 for row in trace_rows_session
        if str(row.get("classification") or "") == "complete_chain" and _is_capital_venue(row.get("venue"))
    )
    session_external_leaks = sum(1 for row in trace_rows_session if bool(row.get("external_live_route")))
    session_scope = {
        "instance_id": runtime_scope.get("instance_id") or "",
        "pid": runtime_scope.get("pid") or 0,
        "started_at": runtime_scope.get("started_at") or "",
        "heartbeat_at": runtime_scope.get("heartbeat_at") or "",
        "event_count": len(session_rows),
        "trace_count": len(trace_rows_session),
    }

    publisher_gap_count = len(publisher_gap_rows) + sum(len(row.get("missing_phases") or []) for row in burn_down_rows)
    api_budget_gap_count = len(api_budget_gap_rows)
    broker_gap_count = len(broker_requirement_gap_rows)
    real_evidence_gap_count = len(real_evidence_gap_rows)
    real_evidence_gap_phase_counts = Counter(str(row.get("phase") or "") for row in real_evidence_gap_rows if str(row.get("phase") or ""))
    real_evidence_gap_producer_counts = Counter(str(row.get("producer") or "") for row in real_evidence_gap_rows if str(row.get("producer") or ""))
    real_evidence_gap_field_counts = Counter(
        str(field)
        for row in real_evidence_gap_rows
        for field in (row.get("missing_real_evidence") or [])
        if str(field)
    )
    recovered_trace_count = len(recovered_trace_rows)
    synthetic_trace_count = len(synthetic_trace_rows)
    synthetic_event_count = sum(1 for row in rows if _synthetic_markers_for_event(row))
    dedupe_applied_count = sum(1 for row in rows if bool(row.get("dedupe_applied")))
    broken_trace_count = sum(1 for row in trace_rows if str(row.get("classification") or "") != "complete_chain")
    non_recovered_broken_count = sum(
        1
        for row in trace_rows
        if str(row.get("classification") or "") != "complete_chain" and not bool(row.get("recovered_downstream_context"))
    )
    external_live_route_leak_count = len(external_confirmation_rows)
    has_events = bool(rows)
    status = _status_from_counts(
        has_events=has_events,
        broken_count=broken_trace_count,
        non_recovered_broken_count=non_recovered_broken_count,
        recovered_count=recovered_trace_count,
        external_leaks=external_live_route_leak_count,
        synthetic_traces=synthetic_trace_count,
        real_only=real_only,
        rate_gaps=api_budget_gap_count,
        broker_gaps=broker_gap_count,
        real_evidence_gaps=real_evidence_gap_count,
    )

    fabric_source = fabric_state if isinstance(fabric_state, dict) and fabric_state else fabric_public
    fabric_summary = fabric_source.get("summary") if isinstance(fabric_source.get("summary"), dict) else {}
    thoughtbus_receiving = bool(fabric_summary.get("thoughtbus_receiving"))
    mycelium_receiving = bool(fabric_summary.get("mycelium_receiving"))
    executor_gate_respected = _executor_gate_respected(
        runtime_status if isinstance(runtime_status, dict) else {},
        trace_rows,
    )
    blockers: List[str] = []
    if not thoughtbus_receiving:
        blockers.append("thoughtbus_not_receiving")
    if not mycelium_receiving:
        blockers.append("mycelium_not_receiving")
    if external_live_route_leak_count > 0:
        blockers.append("external_live_route_leak")
    if broken_trace_count > 0:
        blockers.append("broken_chain")
    if api_budget_gap_count > 0:
        blockers.append("rate_budget_missing")
    if broker_gap_count > 0:
        blockers.append("broker_proof_missing")
    if real_evidence_gap_count > 0:
        blockers.append("real_evidence_missing")
    if recovered_trace_count > 0:
        blockers.append("recovered_upstream_context_missing")
    if synthetic_trace_count > 0:
        blockers.append("synthetic_evidence_present")
    if not executor_gate_respected:
        blockers.append("executor_gate_not_respected")
    if real_only and bool(runtime_status.get("stale")):
        blockers.append("runtime_stale")
    blockers = list(dict.fromkeys(blockers))

    owner_counts = Counter(str(row.get("publisher_owner") or "") for row in rows if str(row.get("publisher_owner") or ""))
    top_publisher_owner = owner_counts.most_common(1)[0][0] if owner_counts else ""

    next_repair_actions: List[str] = []
    for row in publisher_gap_rows[:40]:
        next_repair_actions.append(str(row.get("next_repair_action") or ""))
    for row in api_budget_gap_rows[:40]:
        next_repair_actions.append(str(row.get("next_repair_action") or ""))
    for row in broker_requirement_gap_rows[:40]:
        next_repair_actions.append(str(row.get("next_repair_action") or ""))
    for row in real_evidence_gap_rows[:40]:
        next_repair_actions.append(str(row.get("next_repair_action") or ""))
    next_repair_actions = list(dict.fromkeys(item for item in next_repair_actions if item))

    chain_certification_state = (
        "capital_a_to_b_certified"
        if complete_capital_chain_count > 0 and not blockers and (not real_only or synthetic_trace_count == 0)
        else "real_data_attention"
        if real_only and (synthetic_trace_count > 0 or real_evidence_gap_count > 0)
        else "recovered_broker_truth_attention"
        if recovered_trace_count > 0
        else "live_trade_signal_fabric_stress_broken"
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": now_dt.isoformat(),
        "status": status,
        "ok": status == "live_trade_signal_fabric_stress_certified",
        "mode": "active_trade_flow_stress_burn_down_real_only" if real_only else "active_trade_flow_stress_burn_down",
        "summary": {
            "burn_down_ready": status == "live_trade_signal_fabric_stress_certified",
            "event_count": len(rows),
            "active_trace_count": int(fabric_summary.get("active_trace_count") or len(trace_rows)),
            "complete_trace_count": int(fabric_summary.get("complete_trace_count") or 0),
            "broken_trace_count": broken_trace_count,
            "recovered_trace_count": recovered_trace_count,
            "publisher_gap_count": publisher_gap_count,
            "api_budget_gap_count": api_budget_gap_count,
            "broker_gap_count": broker_gap_count,
            "real_evidence_gap_count": real_evidence_gap_count,
            "real_evidence_gap_top_phase": (real_evidence_gap_phase_counts.most_common(1)[0][0] if real_evidence_gap_phase_counts else ""),
            "real_evidence_gap_top_producer": (real_evidence_gap_producer_counts.most_common(1)[0][0] if real_evidence_gap_producer_counts else ""),
            "real_evidence_gap_top_field": (real_evidence_gap_field_counts.most_common(1)[0][0] if real_evidence_gap_field_counts else ""),
            "complete_capital_chain_count": complete_capital_chain_count,
            "external_live_route_leak_count": external_live_route_leak_count,
            "real_evidence_only_mode": bool(real_only),
            "synthetic_trace_count": synthetic_trace_count,
            "synthetic_event_count": synthetic_event_count,
            "dedupe_applied_count": dedupe_applied_count,
            "dedupe_applied": dedupe_applied_count > 0,
            "publisher_owner": top_publisher_owner,
            "thoughtbus_receiving": thoughtbus_receiving,
            "mycelium_receiving": mycelium_receiving,
            "executor_gate_respected": executor_gate_respected,
            "no_direct_broker_mutation": True,
            "capital_a_to_b_ready": complete_capital_chain_count > 0 and not blockers,
            "session_broken_trace_count": session_broken_trace_count,
            "session_api_budget_gap_count": session_api_budget_gap_count,
            "session_complete_capital_chain_count": session_complete_capital_chain_count,
            "session_external_live_route_leak_count": session_external_leaks,
            "session_scope": session_scope,
            "speed_scope": "current_runtime_session" if speed_trace_rows_session else "tail_ledger",
            "speed_real_data_only_mode": bool(real_only),
            "speed_trace_count": speed_summary["speed_trace_count"],
            "speed_session_trace_count": len(speed_trace_rows_session),
            "speed_complete_to_position_count": speed_summary["speed_complete_to_position_count"],
            "speed_session_complete_to_position_count": sum(1 for row in speed_trace_rows_session if bool(row.get("complete_to_position"))),
            "speed_outcome_recorded_count": speed_summary["speed_outcome_recorded_count"],
            "speed_session_outcome_recorded_count": sum(1 for row in speed_trace_rows_session if bool(row.get("complete_to_outcome"))),
            "speed_positive_gain_count": speed_summary["speed_positive_gain_count"],
            "speed_session_positive_gain_count": sum(1 for row in speed_trace_rows_session if bool(row.get("positive_gain_recorded"))),
            "speed_a_to_b_fastest_ms": speed_summary["speed_a_to_b_fastest_ms"],
            "speed_a_to_b_p50_ms": speed_summary["speed_a_to_b_p50_ms"],
            "speed_a_to_b_p95_ms": speed_summary["speed_a_to_b_p95_ms"],
            "speed_a_to_gain_fastest_ms": speed_summary["speed_a_to_gain_fastest_ms"],
            "speed_a_to_gain_p50_ms": speed_summary["speed_a_to_gain_p50_ms"],
            "speed_a_to_gain_p95_ms": speed_summary["speed_a_to_gain_p95_ms"],
            "speed_round_trip_to_outcome_fastest_ms": speed_summary["speed_round_trip_to_outcome_fastest_ms"],
            "speed_round_trip_to_outcome_p50_ms": speed_summary["speed_round_trip_to_outcome_p50_ms"],
            "speed_round_trip_to_outcome_p95_ms": speed_summary["speed_round_trip_to_outcome_p95_ms"],
            "speed_repeat_cycle_fastest_ms": speed_summary["speed_repeat_cycle_fastest_ms"],
            "speed_repeat_cycle_p50_ms": speed_summary["speed_repeat_cycle_p50_ms"],
            "speed_repeat_cycle_p95_ms": speed_summary["speed_repeat_cycle_p95_ms"],
            "speed_latest_state": speed_summary["speed_latest_state"],
            "speed_current_answer": speed_summary["speed_current_answer"],
        },
        "chain_certification_state": chain_certification_state,
        "capital_a_to_b_ready": complete_capital_chain_count > 0 and not blockers,
        "thoughtbus_proof": fabric_source.get("thoughtbus_proof") if isinstance(fabric_source.get("thoughtbus_proof"), dict) else {},
        "mycelium_proof": fabric_source.get("mycelium_proof") if isinstance(fabric_source.get("mycelium_proof"), dict) else {},
        "active_traces": trace_rows[:50],
        "phase_counts": fabric_source.get("phase_counts") if isinstance(fabric_source.get("phase_counts"), dict) else {},
        "broken_chains": burn_down_rows[:80],
        "burn_down_rows": burn_down_rows[:120],
        "trace_certification_rows": trace_rows[:120],
        "recovered_trace_rows": recovered_trace_rows[:80],
        "synthetic_trace_rows": synthetic_trace_rows[:120],
        "publisher_gap_rows": publisher_gap_rows[:200],
        "producer_repair_rows": publisher_gap_rows[:200],
        "api_budget_gap_rows": api_budget_gap_rows[:240],
        "rate_budget_certification_rows": api_budget_gap_rows[:240],
        "broker_requirement_gap_rows": broker_requirement_gap_rows[:200],
        "real_evidence_gap_rows": real_evidence_gap_rows[:240],
        "real_evidence_gap_phase_counts": [{"phase": key, "count": count} for key, count in real_evidence_gap_phase_counts.most_common(20)],
        "real_evidence_gap_producer_counts": [{"producer": key, "count": count} for key, count in real_evidence_gap_producer_counts.most_common(20)],
        "real_evidence_gap_field_counts": [{"field": key, "count": count} for key, count in real_evidence_gap_field_counts.most_common(20)],
        "recovered_broker_truth_rows": recovered_trace_rows[:80],
        "external_confirmation_rows": external_confirmation_rows[:120],
        "next_repair_actions": next_repair_actions[:80],
        "latest_live_trade_trace": trace_rows[0] if trace_rows else {},
        "session_scope": session_scope,
        "session_trace_rows": trace_rows_session[:80],
        "session_broken_trace_count": session_broken_trace_count,
        "session_api_budget_gap_count": session_api_budget_gap_count,
        "a_to_b_gain_speed_proof": {
            "scope": "current_runtime_session" if speed_trace_rows_session else "tail_ledger",
            "real_data_only": bool(real_only),
            "answer": speed_summary["speed_current_answer"],
            "latest_state": speed_summary["speed_latest_state"],
            "a_to_b_fastest_ms": speed_summary["speed_a_to_b_fastest_ms"],
            "a_to_b_p50_ms": speed_summary["speed_a_to_b_p50_ms"],
            "a_to_b_p95_ms": speed_summary["speed_a_to_b_p95_ms"],
            "a_to_gain_fastest_ms": speed_summary["speed_a_to_gain_fastest_ms"],
            "a_to_gain_p50_ms": speed_summary["speed_a_to_gain_p50_ms"],
            "a_to_gain_p95_ms": speed_summary["speed_a_to_gain_p95_ms"],
            "repeat_cycle_fastest_ms": speed_summary["speed_repeat_cycle_fastest_ms"],
            "repeat_cycle_p50_ms": speed_summary["speed_repeat_cycle_p50_ms"],
            "repeat_cycle_p95_ms": speed_summary["speed_repeat_cycle_p95_ms"],
            "complete_to_position_count": speed_summary["speed_complete_to_position_count"],
            "positive_gain_count": speed_summary["speed_positive_gain_count"],
            "missing_phase_count": len(speed_missing_phase_rows),
        },
        "speed_trace_rows": speed_scope_rows[:120],
        "speed_session_trace_rows": speed_trace_rows_session[:120],
        "speed_latency_rows": speed_latency_rows[:80],
        "speed_missing_phase_rows": speed_missing_phase_rows[:120],
        "speed_repeat_cycle_rows": speed_scope_repeat_rows[:80],
        "runtime_gate_proof": {
            "runtime_stale": bool(runtime_status.get("stale")) if isinstance(runtime_status, dict) else False,
            "runtime_stale_reason": str(runtime_status.get("stale_reason") or "") if isinstance(runtime_status, dict) else "",
            "runtime_clearances": [
                str(item) for item in (runtime_status.get("runtime_clearances") or [])
                if str(item)
            ] if isinstance(runtime_status, dict) else [],
            "executor_gate_respected": executor_gate_respected,
        },
        "blockers": blockers,
        "manual_boundaries": MANUAL_BOUNDARIES,
        "source_paths": {
            "fabric_state": FABRIC_STATE_PATH.as_posix(),
            "fabric_public": FABRIC_PUBLIC_PATH.as_posix(),
            "fabric_events": FABRIC_EVENTS_PATH.as_posix(),
            "lifecycle_state": LIFECYCLE_STATE_PATH.as_posix(),
            "runtime_status": RUNTIME_STATUS_PATH.as_posix(),
        },
        "output_files": [
            DEFAULT_STATE_PATH.as_posix(),
            DEFAULT_AUDIT_JSON.as_posix(),
            DEFAULT_AUDIT_MD.as_posix(),
            DEFAULT_PUBLIC_JSON.as_posix(),
        ],
    }
    producer_wiring_rows: List[Dict[str, Any]] = []
    producer_counter = Counter(str(row.get("phase") or "") for row in session_rows)
    producer_gap_by_phase: Dict[str, Dict[str, int]] = defaultdict(lambda: {"id": 0, "rate": 0, "broker": 0, "real": 0})
    for row in publisher_gap_rows:
        phase = str(row.get("phase") or "")
        if phase:
            producer_gap_by_phase[phase]["id"] += 1
    for row in api_budget_gap_rows:
        phase = str(row.get("phase") or "")
        if phase:
            producer_gap_by_phase[phase]["rate"] += 1
    for row in broker_requirement_gap_rows:
        phase = str(row.get("phase") or "")
        if phase:
            producer_gap_by_phase[phase]["broker"] += 1
    for row in real_evidence_gap_rows:
        phase = str(row.get("phase") or "")
        if phase:
            producer_gap_by_phase[phase]["real"] += 1
    for phase in CORE_CHAIN_PHASES:
        count = int(producer_counter.get(phase, 0))
        gap = producer_gap_by_phase.get(phase, {"id": 0, "rate": 0, "broker": 0, "real": 0})
        if count == 0:
            state = "producer_silent"
        elif gap["id"] > 0:
            state = "producer_id_gap"
        elif gap["rate"] > 0:
            state = "producer_rate_missing"
        elif gap["broker"] > 0:
            state = "producer_broker_gap"
        elif gap["real"] > 0:
            state = "producer_real_evidence_gap"
        else:
            state = "producer_wired"
        producer_wiring_rows.append(
            {
                "phase": phase,
                "producer": _phase_to_producer(phase),
                "state": state,
                "event_count": count,
                "id_gap_count": gap["id"],
                "rate_gap_count": gap["rate"],
                "broker_gap_count": gap["broker"],
                "real_evidence_gap_count": gap["real"],
            }
        )
    now_ts = now_dt.timestamp()
    heartbeat_by_producer: Dict[str, Dict[str, Any]] = {}
    for row in session_rows:
        producer = str(row.get("source_system") or _phase_to_producer(str(row.get("phase") or "")) or "unknown")
        event_ts = _parse_ts(row.get("generated_at"))
        payload = heartbeat_by_producer.setdefault(
            producer,
            {"producer": producer, "event_count": 0, "last_event_at": "", "seconds_since_last_event": 0.0},
        )
        payload["event_count"] = int(payload.get("event_count", 0) or 0) + 1
        if event_ts > _parse_ts(payload.get("last_event_at")):
            payload["last_event_at"] = str(row.get("generated_at") or "")
            payload["seconds_since_last_event"] = round(max(0.0, now_ts - event_ts), 3) if event_ts > 0 else 0.0
    publisher_heartbeat_rows = sorted(
        heartbeat_by_producer.values(),
        key=lambda item: float(item.get("seconds_since_last_event") or 0.0),
    )
    next_live_trace_requirements: List[Dict[str, Any]] = []
    for row in burn_down_rows[:20]:
        next_live_trace_requirements.append(
            {
                "trace_id": row.get("trace_id"),
                "lifecycle_id": row.get("lifecycle_id"),
                "route_key": row.get("route_key"),
                "symbol": row.get("symbol"),
                "latest_phase": row.get("latest_phase"),
                "next_required_phase": row.get("next_required_phase"),
                "next_producer_to_fix": row.get("next_producer_to_fix"),
                "next_repair_action": row.get("next_repair_action"),
                "blocked_before_broker_mutation": bool(row.get("blocked_before_broker_mutation")),
                "classification": row.get("classification"),
            }
        )
    fresh_capital_trace_candidate = next(
        (row for row in trace_rows_session if _is_capital_venue(row.get("venue"))),
        {},
    )
    producer_wired_count = sum(1 for row in producer_wiring_rows if str(row.get("state") or "") in {"producer_wired", "complete_a_to_b"})
    producer_silent_count = sum(1 for row in producer_wiring_rows if str(row.get("state") or "") == "producer_silent")
    producer_rate_missing_count = sum(1 for row in producer_wiring_rows if str(row.get("state") or "") == "producer_rate_missing")
    producer_burndown_state = "producer_burndown_ready" if producer_wired_count >= len(CORE_CHAIN_PHASES) and status == "live_trade_signal_fabric_stress_certified" else "producer_burndown_attention"
    report["producer_wiring_rows"] = producer_wiring_rows
    report["publisher_heartbeat_rows"] = publisher_heartbeat_rows[:50]
    report["next_live_trace_requirements"] = next_live_trace_requirements
    report["fresh_capital_trace_candidate"] = fresh_capital_trace_candidate
    report["producer_burndown_state"] = producer_burndown_state
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    if isinstance(summary, dict):
        summary["producer_wiring_row_count"] = len(producer_wiring_rows)
        summary["publisher_heartbeat_row_count"] = len(publisher_heartbeat_rows)
        summary["producer_wired_count"] = producer_wired_count
        summary["producer_silent_count"] = producer_silent_count
        summary["producer_rate_missing_count"] = producer_rate_missing_count
        summary["producer_burndown_state"] = producer_burndown_state
        summary["producer_repair_row_count"] = len(publisher_gap_rows)
        summary["recovered_broker_truth_count"] = len(recovered_trace_rows)
        summary["trace_count"] = len(trace_rows)
        summary["certified_trace_count"] = max(0, len(trace_rows) - broken_trace_count)
        summary["missing_required_phase_count"] = sum(len(row.get("missing_required_phases") or []) for row in burn_down_rows)
        summary["stable_id_gap_count"] = sum(len(row.get("stable_id_gaps") or []) for row in burn_down_rows)
        summary["rate_budget_missing_count"] = api_budget_gap_count
        summary["broker_requirement_gap_count"] = broker_gap_count
        summary["stale_trace_count"] = 0
        summary["bus_delivery_count"] = sum(int(row.get("bus_delivery_count") or 0) for row in rows)
        summary["mycelium_delivery_count"] = sum(int(row.get("mycelium_delivery_count") or 0) for row in rows)
        summary["rate_budget_certified_count"] = sum(1 for row in rows if bool(row.get("rate_budget_certified")))
        summary["rate_budget_uncertified_count"] = sum(1 for row in rows if not bool(row.get("rate_budget_certified")))
        report["summary"] = summary
    return report


def _make_markdown(report: Dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    lines = [
        "# Aureon Live Trade Signal Fabric Stress Audit",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Chain state: `{report.get('chain_certification_state')}`",
        f"- Event count: `{summary.get('event_count')}`",
        f"- Traces: active `{summary.get('active_trace_count')}` broken `{summary.get('broken_trace_count')}` complete `{summary.get('complete_trace_count')}`",
        f"- Recovered traces: `{summary.get('recovered_trace_count')}`",
        f"- Real-evidence-only mode: `{summary.get('real_evidence_only_mode')}` synthetic traces `{summary.get('synthetic_trace_count')}` events `{summary.get('synthetic_event_count')}`",
        f"- Producer gaps: `{summary.get('publisher_gap_count')}`",
        f"- API budget gaps: `{summary.get('api_budget_gap_count')}`",
        f"- Broker proof gaps: `{summary.get('broker_gap_count')}`",
        f"- Real-evidence gaps: `{summary.get('real_evidence_gap_count')}`",
        f"- Real-evidence top phase/producer/field: `{summary.get('real_evidence_gap_top_phase')}` / `{summary.get('real_evidence_gap_top_producer')}` / `{summary.get('real_evidence_gap_top_field')}`",
        f"- Capital complete A-to-B traces: `{summary.get('complete_capital_chain_count')}`",
        f"- External live-route leaks: `{summary.get('external_live_route_leak_count')}`",
        f"- ThoughtBus receiving: `{summary.get('thoughtbus_receiving')}`",
        f"- Mycelium receiving: `{summary.get('mycelium_receiving')}`",
        f"- Executor gate respected: `{summary.get('executor_gate_respected')}`",
        f"- A-to-B speed scope: `{summary.get('speed_scope')}` answer `{summary.get('speed_current_answer')}`",
        f"- A-to-open fastest/p50/p95 ms: `{summary.get('speed_a_to_b_fastest_ms')}` / `{summary.get('speed_a_to_b_p50_ms')}` / `{summary.get('speed_a_to_b_p95_ms')}`",
        f"- A-to-gain fastest/p50/p95 ms: `{summary.get('speed_a_to_gain_fastest_ms')}` / `{summary.get('speed_a_to_gain_p50_ms')}` / `{summary.get('speed_a_to_gain_p95_ms')}`",
        "",
        "## Top Burn-Down Rows",
    ]
    burn_rows = report.get("burn_down_rows") if isinstance(report.get("burn_down_rows"), list) else []
    if burn_rows:
        for row in burn_rows[:12]:
            lines.append(
                f"- `{row.get('trace_id')}` `{row.get('classification')}` phase `{row.get('latest_phase')}` "
                f"missing `{row.get('missing_phase_count')}` id_gaps `{row.get('id_gap_count')}` "
                f"rate_gaps `{row.get('rate_gap_count')}` broker_gaps `{row.get('broker_gap_count')}` "
                f"real_gaps `{row.get('real_evidence_gap_count')}`"
            )
    else:
        lines.append("- None.")
    lines.extend(["", "## Blockers"])
    blockers = report.get("blockers") if isinstance(report.get("blockers"), list) else []
    lines.extend(f"- `{blocker}`" for blocker in blockers) if blockers else lines.append("- None.")
    return "\n".join(lines) + "\n"


def build_and_write_live_trade_signal_fabric_stress_audit(
    *,
    root: Optional[Path] = None,
    real_only: bool = False,
) -> Dict[str, Any]:
    root_path = Path(root or _default_root()).resolve()
    report = build_live_trade_signal_fabric_stress_audit(root=root_path, real_only=real_only)
    writes = [
        _write_json(_rooted(root_path, DEFAULT_STATE_PATH), report),
        _write_json(_rooted(root_path, DEFAULT_AUDIT_JSON), report),
        _write_text(_rooted(root_path, DEFAULT_AUDIT_MD), _make_markdown(report)),
        _write_json(_rooted(root_path, DEFAULT_PUBLIC_JSON), report),
    ]
    report["write_info"] = {"evidence_writes": writes}
    for rel in (DEFAULT_STATE_PATH, DEFAULT_AUDIT_JSON, DEFAULT_PUBLIC_JSON):
        _write_json(_rooted(root_path, rel), report)
    _write_text(_rooted(root_path, DEFAULT_AUDIT_MD), _make_markdown(report))
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build live trade signal fabric stress burn-down evidence.")
    parser.add_argument("--repo-root", default="", help="Repository root; defaults to cwd/repo.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    parser.add_argument("--real-only", action="store_true", help="Fail attention when synthetic/mock/fixture evidence is detected.")
    args = parser.parse_args(argv)
    root = Path(args.repo_root).resolve() if args.repo_root else None
    report = build_and_write_live_trade_signal_fabric_stress_audit(root=root, real_only=bool(args.real_only))
    print(json.dumps(report, indent=2, sort_keys=True, default=str) if args.json else _make_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
