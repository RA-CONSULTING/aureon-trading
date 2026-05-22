from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

from aureon.autonomous.aureon_live_trade_signal_fabric_stress_audit import (
    build_live_trade_signal_fabric_stress_audit,
)


NOW = datetime(2026, 5, 21, 16, 0, 0, tzinfo=timezone.utc)


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def _fabric_state(thoughtbus: bool = True, mycelium: bool = True) -> Dict[str, Any]:
    return {
        "status": "trade_flow_active",
        "summary": {
            "thoughtbus_receiving": thoughtbus,
            "mycelium_receiving": mycelium,
            "active_trace_count": 1,
            "complete_trace_count": 0,
            "broken_trace_count": 0,
        },
        "thoughtbus_proof": {"receiving": thoughtbus},
        "mycelium_proof": {"receiving": mycelium},
        "phase_counts": {},
        "events": [],
    }


def _lifecycle_state(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "status": "order_lifecycle_ready",
        "active_lifecycle_count": len(rows),
        "completed_lifecycle_count": 0,
        "continuity_blockers": [],
        "active_lifecycles": rows,
        "lifecycles": rows,
    }


def _event(
    phase: str,
    *,
    ts_offset: int,
    trace_id: str = "trace-1",
    lifecycle_id: str = "life-1",
    candidate_id: str = "cand-1",
    intent_id: str = "intent-1",
    route_key: str = "capital:cfd:GOLD:BUY",
    venue: str = "capital",
    symbol: str = "GOLD",
    side: str = "BUY",
    rate_ok: bool = True,
    deal_reference: str = "DR-1",
    deal_id: str = "D-1",
    verification_source: str = "capital_broker_event_stream",
    net_pnl: float | None = None,
) -> Dict[str, Any]:
    generated_at = NOW.replace(second=ts_offset).isoformat()
    row: Dict[str, Any] = {
        "generated_at": generated_at,
        "phase": phase,
        "trace_id": trace_id,
        "lifecycle_id": lifecycle_id,
        "candidate_id": candidate_id,
        "intent_id": intent_id,
        "route_key": route_key,
        "venue": venue,
        "symbol": symbol,
        "side": side,
        "rate_limit_family": "capital_rest",
        "rate_remaining": 9,
        "api_budget_source": "unit_governor",
        "missing_rate_budget_fields": [],
        "missing_api_budget_tags": [],
        "rate_budget_certified": rate_ok,
        "verification_source": verification_source,
        "thoughtbus_publish_ok": True,
        "mycelium_ingest_ok": True,
    }
    if phase in {"order_submitted", "broker_acknowledged"}:
        row["deal_reference"] = deal_reference
    if phase in {"broker_acknowledged", "position_open", "close_requested", "close_acknowledged", "position_closed", "outcome_recorded"}:
        row["deal_id"] = deal_id
    if phase == "position_closed":
        row["position_absence_verified"] = True
    if phase == "outcome_recorded":
        row["net_pnl"] = 0.05 if net_pnl is None else net_pnl
    if not rate_ok:
        row["rate_budget_certified"] = False
        row["missing_rate_budget_fields"] = ["rate_limit_family"]
    return row


def test_fabric_stress_certifies_complete_capital_chain(tmp_path: Path) -> None:
    events = [
        _event("signal_generated", ts_offset=1),
        _event("counter_intel_passed", ts_offset=2),
        _event("candidate_ready", ts_offset=3),
        _event("intent_published", ts_offset=4),
        _event("executor_accepted", ts_offset=5),
        _event("order_submitted", ts_offset=6),
        _event("broker_acknowledged", ts_offset=7),
        _event("position_open", ts_offset=8),
        _event("close_requested", ts_offset=9),
        _event("close_acknowledged", ts_offset=10),
        _event("position_closed", ts_offset=11),
        _event("outcome_recorded", ts_offset=12),
    ]
    _write_jsonl(tmp_path / "state/aureon_live_trade_signal_fabric_events.jsonl", events)
    _write_json(tmp_path / "state/aureon_live_trade_signal_fabric_latest.json", _fabric_state())
    _write_json(
        tmp_path / "state/unified_order_lifecycle_latest.json",
        _lifecycle_state(
            [
                {
                    "lifecycle_id": "life-1",
                    "route_key": "capital:cfd:GOLD:BUY",
                    "current_status": "outcome_recorded",
                    "last_event": {"event_type": "outcome_recorded", "status": "outcome_recorded"},
                }
            ]
        ),
    )
    _write_json(tmp_path / "state/unified_runtime_status.json", {"stale": False, "runtime_clearances": []})

    report = build_live_trade_signal_fabric_stress_audit(root=tmp_path, now=NOW)

    assert report["status"] == "live_trade_signal_fabric_stress_certified"
    assert report["summary"]["complete_capital_chain_count"] == 1
    assert report["summary"]["burn_down_ready"] is True
    assert report["summary"]["api_budget_gap_count"] == 0
    assert report["summary"]["broker_gap_count"] == 0
    assert report["summary"]["speed_complete_to_position_count"] == 1
    assert report["summary"]["speed_positive_gain_count"] == 1
    assert report["summary"]["speed_a_to_b_fastest_ms"] == 7000.0
    assert report["summary"]["speed_a_to_gain_fastest_ms"] == 11000.0
    assert report["a_to_b_gain_speed_proof"]["latest_state"] == "gain_speed_certified"


def test_fabric_stress_speed_proof_waits_for_gain_outcome(tmp_path: Path) -> None:
    events = [
        _event("signal_generated", ts_offset=1, trace_id="trace-speed", lifecycle_id="life-speed"),
        _event("counter_intel_passed", ts_offset=2, trace_id="trace-speed", lifecycle_id="life-speed"),
        _event("candidate_ready", ts_offset=3, trace_id="trace-speed", lifecycle_id="life-speed"),
        _event("intent_published", ts_offset=4, trace_id="trace-speed", lifecycle_id="life-speed"),
        _event("executor_accepted", ts_offset=5, trace_id="trace-speed", lifecycle_id="life-speed"),
    ]
    _write_jsonl(tmp_path / "state/aureon_live_trade_signal_fabric_events.jsonl", events)
    _write_json(tmp_path / "state/aureon_live_trade_signal_fabric_latest.json", _fabric_state())
    _write_json(tmp_path / "state/unified_order_lifecycle_latest.json", _lifecycle_state([]))
    _write_json(tmp_path / "state/unified_runtime_status.json", {"stale": False, "runtime_clearances": []})

    report = build_live_trade_signal_fabric_stress_audit(root=tmp_path, now=NOW)

    assert report["summary"]["speed_complete_to_position_count"] == 0
    assert report["summary"]["speed_positive_gain_count"] == 0
    assert report["speed_missing_phase_rows"][0]["missing_speed_phases"] == ["position_open", "outcome_recorded"]
    assert report["a_to_b_gain_speed_proof"]["latest_state"] == "speed_waiting_for_position_open"


def test_fabric_stress_marks_recovered_trace_without_faking_upstream(tmp_path: Path) -> None:
    events = [
        _event("broker_acknowledged", ts_offset=1, trace_id="trace-r", lifecycle_id="life-r"),
        _event("position_open", ts_offset=2, trace_id="trace-r", lifecycle_id="life-r"),
    ]
    _write_jsonl(tmp_path / "state/aureon_live_trade_signal_fabric_events.jsonl", events)
    _write_json(tmp_path / "state/aureon_live_trade_signal_fabric_latest.json", _fabric_state())
    _write_json(
        tmp_path / "state/unified_order_lifecycle_latest.json",
        _lifecycle_state(
            [
                {
                    "lifecycle_id": "life-r",
                    "route_key": "capital:cfd:US100:BUY",
                    "current_status": "position_open",
                    "missing_links": ["candidate_ready", "intent_published", "executor_accepted", "order_submitted"],
                    "last_event": {
                        "event_type": "position_recovered",
                        "status": "position_open",
                        "reason": "broker_position_reconciled_on_startup",
                    },
                }
            ]
        ),
    )
    _write_json(tmp_path / "state/unified_runtime_status.json", {"stale": False, "runtime_clearances": []})

    report = build_live_trade_signal_fabric_stress_audit(root=tmp_path, now=NOW)

    assert report["status"] == "recovered_broker_truth_attention"
    assert report["summary"]["recovered_trace_count"] == 1
    assert report["recovered_trace_rows"][0]["recovered_upstream_context_missing"] is True


def test_fabric_stress_flags_external_live_route_leak(tmp_path: Path) -> None:
    events = [
        _event("signal_generated", ts_offset=1, trace_id="trace-x", lifecycle_id="life-x", venue="alpaca", symbol="SPY"),
        _event("candidate_ready", ts_offset=2, trace_id="trace-x", lifecycle_id="life-x", venue="alpaca", symbol="SPY"),
        _event("intent_published", ts_offset=3, trace_id="trace-x", lifecycle_id="life-x", venue="alpaca", symbol="SPY"),
        _event("executor_accepted", ts_offset=4, trace_id="trace-x", lifecycle_id="life-x", venue="alpaca", symbol="SPY"),
        _event("order_submitted", ts_offset=5, trace_id="trace-x", lifecycle_id="life-x", venue="alpaca", symbol="SPY"),
    ]
    _write_jsonl(tmp_path / "state/aureon_live_trade_signal_fabric_events.jsonl", events)
    _write_json(tmp_path / "state/aureon_live_trade_signal_fabric_latest.json", _fabric_state())
    _write_json(tmp_path / "state/unified_order_lifecycle_latest.json", _lifecycle_state([]))
    _write_json(tmp_path / "state/unified_runtime_status.json", {"stale": False, "runtime_clearances": []})

    report = build_live_trade_signal_fabric_stress_audit(root=tmp_path, now=NOW)

    assert report["status"] == "external_live_route_leak"
    assert report["summary"]["external_live_route_leak_count"] >= 1
    assert "external_live_route_leak" in report["blockers"]


def test_fabric_stress_reports_rate_budget_gaps(tmp_path: Path) -> None:
    events = [
        _event("signal_generated", ts_offset=1, trace_id="trace-g", lifecycle_id="life-g"),
        _event("counter_intel_passed", ts_offset=2, trace_id="trace-g", lifecycle_id="life-g"),
        _event("candidate_ready", ts_offset=3, trace_id="trace-g", lifecycle_id="life-g"),
        _event("intent_published", ts_offset=4, trace_id="trace-g", lifecycle_id="life-g"),
        _event("executor_accepted", ts_offset=5, trace_id="trace-g", lifecycle_id="life-g"),
        _event("order_submitted", ts_offset=6, trace_id="trace-g", lifecycle_id="life-g", rate_ok=False),
    ]
    _write_jsonl(tmp_path / "state/aureon_live_trade_signal_fabric_events.jsonl", events)
    _write_json(tmp_path / "state/aureon_live_trade_signal_fabric_latest.json", _fabric_state())
    _write_json(tmp_path / "state/unified_order_lifecycle_latest.json", _lifecycle_state([]))
    _write_json(tmp_path / "state/unified_runtime_status.json", {"stale": False, "runtime_clearances": []})

    report = build_live_trade_signal_fabric_stress_audit(root=tmp_path, now=NOW)

    assert report["summary"]["api_budget_gap_count"] >= 1
    assert any(row.get("phase") == "order_submitted" for row in report["api_budget_gap_rows"])
    assert "rate_budget_missing" in report["blockers"]


def test_fabric_stress_real_only_flags_synthetic_markers(tmp_path: Path) -> None:
    events = [
        _event("signal_generated", ts_offset=1, trace_id="trace-s", lifecycle_id="life-s"),
        {
            **_event("candidate_ready", ts_offset=2, trace_id="trace-s", lifecycle_id="life-s"),
            "source_system": "unit_test",
            "proof_mode": "mock_broker",
        },
    ]
    _write_jsonl(tmp_path / "state/aureon_live_trade_signal_fabric_events.jsonl", events)
    _write_json(tmp_path / "state/aureon_live_trade_signal_fabric_latest.json", _fabric_state())
    _write_json(tmp_path / "state/unified_order_lifecycle_latest.json", _lifecycle_state([]))
    _write_json(tmp_path / "state/unified_runtime_status.json", {"stale": False, "runtime_clearances": []})

    report = build_live_trade_signal_fabric_stress_audit(root=tmp_path, now=NOW, real_only=True)

    assert report["status"] == "synthetic_evidence_present"
    assert report["summary"]["real_evidence_only_mode"] is True
    assert report["summary"]["synthetic_trace_count"] >= 1
    assert "synthetic_evidence_present" in report["blockers"]


def test_fabric_stress_real_only_flags_missing_real_evidence_proof(tmp_path: Path) -> None:
    events = [
        _event("signal_generated", ts_offset=1, trace_id="trace-rm", lifecycle_id="life-rm"),
        _event("candidate_ready", ts_offset=2, trace_id="trace-rm", lifecycle_id="life-rm"),
    ]
    _write_jsonl(tmp_path / "state/aureon_live_trade_signal_fabric_events.jsonl", events)
    _write_json(tmp_path / "state/aureon_live_trade_signal_fabric_latest.json", _fabric_state())
    _write_json(tmp_path / "state/unified_order_lifecycle_latest.json", _lifecycle_state([]))
    _write_json(tmp_path / "state/unified_runtime_status.json", {"stale": False, "runtime_clearances": []})

    report = build_live_trade_signal_fabric_stress_audit(root=tmp_path, now=NOW, real_only=True)

    assert report["status"] == "real_evidence_missing"
    assert report["summary"]["real_evidence_only_mode"] is True
    assert report["summary"]["real_evidence_gap_count"] >= 1
    assert "real_evidence_missing" in report["blockers"]


def test_fabric_stress_real_only_certifies_with_live_proof_fields(tmp_path: Path) -> None:
    events = [
        _event("signal_generated", ts_offset=1),
        _event("counter_intel_passed", ts_offset=2),
        _event("candidate_ready", ts_offset=3),
        _event("intent_published", ts_offset=4),
        _event("executor_accepted", ts_offset=5),
        _event("order_submitted", ts_offset=6),
        _event("broker_acknowledged", ts_offset=7),
        _event("position_open", ts_offset=8),
        _event("close_requested", ts_offset=9),
        _event("close_acknowledged", ts_offset=10),
        _event("position_closed", ts_offset=11),
        _event("outcome_recorded", ts_offset=12),
    ]
    for row in events:
        phase = str(row.get("phase") or "")
        if phase in {"signal_generated", "counter_intel_passed", "candidate_ready", "intent_published", "executor_accepted"}:
            row["source_system"] = "unified_market_trader"
        elif phase in {"order_submitted", "broker_acknowledged", "position_open", "close_requested", "close_acknowledged", "position_closed"}:
            row["source_system"] = "capital_cfd_trader"
        else:
            row["source_system"] = "aureon_cognitive_trade_evidence"
        row["proof_mode"] = "live_runtime"

    _write_jsonl(tmp_path / "state/aureon_live_trade_signal_fabric_events.jsonl", events)
    _write_json(tmp_path / "state/aureon_live_trade_signal_fabric_latest.json", _fabric_state())
    _write_json(
        tmp_path / "state/unified_order_lifecycle_latest.json",
        _lifecycle_state(
            [
                {
                    "lifecycle_id": "life-1",
                    "route_key": "capital:cfd:GOLD:BUY",
                    "current_status": "outcome_recorded",
                    "last_event": {"event_type": "outcome_recorded", "status": "outcome_recorded"},
                }
            ]
        ),
    )
    _write_json(tmp_path / "state/unified_runtime_status.json", {"stale": False, "runtime_clearances": []})

    report = build_live_trade_signal_fabric_stress_audit(root=tmp_path, now=NOW, real_only=True)

    assert report["status"] == "live_trade_signal_fabric_stress_certified"
    assert report["summary"]["real_evidence_gap_count"] == 0
    assert report["summary"]["synthetic_trace_count"] == 0
