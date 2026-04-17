#!/usr/bin/env python3
"""
Tests for the TemporalCausalityLaw — the β Λ(t-τ) lighthouse over
goal lifecycles.

What's being proved:
  - New goal.submit.request is tracked as PROPOSED with lifecycle_tau=0
  - A pulse advances lifecycle_tau on every active goal
  - A PROPOSED goal orphans after ack_budget_tau pulses without ack
  - Acknowledgment from goal.submitted moves PROPOSED → ACKNOWLEDGED
  - Progress events move ACKNOWLEDGED → IN_PROGRESS and carry pct
  - Completion closes the causal line (COMPLETED, terminal)
  - Explicit abandon closes with ABANDONED + reason
  - Terminal goals don't advance on further pulses
  - IN_PROGRESS goals that cross complete_budget_tau orphan
  - Every lifecycle transition publishes goal.echo with the full trace
  - Pulse publishes goal.echo.summary with completion_rate / orphan_rate
  - Orphan publishes goal.echo.orphaned
  - Vault ingests every transition as a goal.echo card
  - Env vars override budgets
  - SymbolicLifeBridge subscribes to goal.echo.summary and bumps the
    goal_lighthouse subsystem with completion - orphan + 0.5 health
  - Orphan events also land on the lighthouse (as 0.0)
"""

from __future__ import annotations

import os
import sys
from typing import Any, Callable, Dict, List

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from aureon.vault.voice.temporal_causality import (  # noqa: E402
    GoalEcho,
    GoalState,
    TemporalCausalityLaw,
    reset_temporal_causality_law,
    get_temporal_causality_law,
)


# ─────────────────────────────────────────────────────────────────────────────
# Stubs
# ─────────────────────────────────────────────────────────────────────────────


class _StubBus:
    def __init__(self):
        self.published: List[Any] = []
        self._subs: Dict[str, List[Callable]] = {}

    def publish(self, thought=None, **kwargs):
        if thought is None:
            class _T: pass
            t = _T()
            t.topic = kwargs.get("topic", "")
            t.payload = kwargs.get("payload", {})
            t.source = kwargs.get("source", "")
            thought = t
        self.published.append(thought)
        for topic, handlers in self._subs.items():
            match = (topic == "*") or (topic == thought.topic) or (
                topic.endswith(".*") and thought.topic.startswith(topic[:-1])
            )
            if match:
                for h in handlers:
                    h(thought)
        return thought

    def subscribe(self, topic, handler):
        self._subs.setdefault(topic, []).append(handler)


class _Thought:
    def __init__(self, topic, payload, source="test"):
        self.topic = topic
        self.payload = payload
        self.source = source


class _StubVault:
    def __init__(self):
        self.ingested: List[Dict[str, Any]] = []

    def ingest(self, topic, payload):
        self.ingested.append({"topic": topic, "payload": payload})


def _law(**overrides):
    bus = overrides.pop("bus", None) or _StubBus()
    vault = overrides.pop("vault", None) or _StubVault()
    law = TemporalCausalityLaw(thought_bus=bus, vault=vault, **overrides)
    law.start()
    return law, bus, vault


def _submit(bus, text="test goal", persona="engineer", goal_id=None,
            urgency=0.7, parameters=None):
    payload = {
        "text": text, "proposed_by_persona": persona,
        "urgency": urgency, "parameters": dict(parameters or {}),
    }
    if goal_id:
        payload["goal_id"] = goal_id
    bus.publish(_Thought("goal.submit.request", payload))
    return payload


# ─────────────────────────────────────────────────────────────────────────────
# Subscription + track
# ─────────────────────────────────────────────────────────────────────────────


def test_subscribes_to_all_inbound_topics():
    law, bus, _ = _law()
    for topic in TemporalCausalityLaw.INBOUND_TOPICS:
        assert topic in bus._subs, f"missing subscription for {topic}"


def test_submit_request_is_tracked_as_proposed():
    law, bus, _ = _law()
    _submit(bus, text="draft a research note", persona="quantum_physicist")
    active = law.active()
    assert len(active) == 1
    echo = active[0]
    assert echo.state == GoalState.PROPOSED
    assert echo.lifecycle_tau == 0
    assert echo.text == "draft a research note"
    assert echo.proposed_by_persona == "quantum_physicist"
    assert len(echo.transitions) == 1
    assert echo.transitions[0]["state"] == GoalState.PROPOSED.value


def test_track_ignores_duplicate_goal_id():
    law, bus, _ = _law()
    _submit(bus, goal_id="dup1")
    _submit(bus, goal_id="dup1")
    assert len(law.all()) == 1


def test_submit_request_is_published_as_goal_echo():
    law, bus, _ = _law()
    _submit(bus, text="do the thing")
    echo_topics = [t.topic for t in bus.published if t.topic == "goal.echo"]
    assert len(echo_topics) == 1


# ─────────────────────────────────────────────────────────────────────────────
# Lifecycle transitions
# ─────────────────────────────────────────────────────────────────────────────


def test_acknowledge_moves_to_acknowledged():
    law, bus, _ = _law()
    _submit(bus, goal_id="g1")
    law.acknowledge("g1", engine_id="goal_engine")
    echo = law.get("g1")
    assert echo.state == GoalState.ACKNOWLEDGED
    assert echo.acknowledged_by == "goal_engine"


def test_goal_submitted_on_bus_auto_acknowledges():
    law, bus, _ = _law()
    _submit(bus, goal_id="g2", text="write a paper")
    # GoalExecutionEngine publishes goal.submitted when it accepts
    bus.publish(_Thought("goal.submitted",
                         {"goal_id": "g2", "source": "goal_exec"}))
    assert law.get("g2").state == GoalState.ACKNOWLEDGED


def test_goal_submitted_matches_by_text_when_no_id():
    law, bus, _ = _law()
    _submit(bus, text="write a unique research note")
    bus.publish(_Thought("goal.submitted",
                         {"text": "write a unique research note",
                          "source": "engine_z"}))
    active = law.active()
    assert len(active) == 1
    assert active[0].state == GoalState.ACKNOWLEDGED


def test_progress_moves_to_in_progress_with_pct():
    law, bus, _ = _law()
    _submit(bus, goal_id="g3")
    law.acknowledge("g3")
    bus.publish(_Thought("goal.progress",
                         {"goal_id": "g3", "progress_pct": 0.4, "note": "step 2/5"}))
    echo = law.get("g3")
    assert echo.state == GoalState.IN_PROGRESS
    assert abs(echo.progress_pct - 0.4) < 1e-9


def test_progress_from_proposed_also_moves_to_in_progress():
    law, bus, _ = _law()
    _submit(bus, goal_id="g4")
    bus.publish(_Thought("goal.progress",
                         {"goal_id": "g4", "progress_pct": 0.2}))
    assert law.get("g4").state == GoalState.IN_PROGRESS


def test_complete_closes_the_line():
    law, bus, _ = _law()
    _submit(bus, goal_id="g5")
    law.acknowledge("g5")
    law.update_progress("g5", 0.9, "nearly done")
    law.complete("g5", "paper drafted, saved to docs/research/")
    echo = law.get("g5")
    assert echo.state == GoalState.COMPLETED
    assert echo.progress_pct == 1.0
    assert "paper drafted" in echo.result_summary


def test_abandon_closes_with_reason():
    law, bus, _ = _law()
    _submit(bus, goal_id="g6")
    law.abandon("g6", reason="operator withdrew")
    echo = law.get("g6")
    assert echo.state == GoalState.ABANDONED
    assert "operator" in echo.abandoned_reason


def test_terminal_state_is_sticky():
    law, bus, _ = _law()
    _submit(bus, goal_id="g7")
    law.complete("g7", "done")
    # Further mutations should be no-ops
    law.acknowledge("g7")
    law.update_progress("g7", 0.5)
    law.abandon("g7", "too late")
    assert law.get("g7").state == GoalState.COMPLETED


# ─────────────────────────────────────────────────────────────────────────────
# Pulse + τ budgets
# ─────────────────────────────────────────────────────────────────────────────


def test_pulse_advances_lifecycle_tau_on_active_goals():
    law, bus, _ = _law(ack_budget_tau=10, complete_budget_tau=100)
    _submit(bus, goal_id="g8")
    law.pulse()
    law.pulse()
    assert law.get("g8").lifecycle_tau == 2


def test_pulse_orphans_stale_proposed_goals():
    law, bus, _ = _law(ack_budget_tau=2, complete_budget_tau=100)
    _submit(bus, goal_id="g9")
    law.pulse()   # tau=1, still PROPOSED
    assert law.get("g9").state == GoalState.PROPOSED
    law.pulse()   # tau=2, crosses ack budget → ORPHANED
    assert law.get("g9").state == GoalState.ORPHANED


def test_orphan_publishes_orphaned_topic():
    law, bus, _ = _law(ack_budget_tau=1)
    _submit(bus, goal_id="gX")
    # Clear prior publications so we measure THIS pulse's output
    bus.published.clear()
    law.pulse()
    topics = [t.topic for t in bus.published]
    assert "goal.echo.orphaned" in topics


def test_ack_budget_does_not_orphan_after_acknowledge():
    law, bus, _ = _law(ack_budget_tau=2, complete_budget_tau=100)
    _submit(bus, goal_id="g10")
    law.acknowledge("g10")
    law.pulse(); law.pulse(); law.pulse()
    assert law.get("g10").state == GoalState.ACKNOWLEDGED


def test_complete_budget_orphans_stuck_in_progress():
    law, bus, _ = _law(ack_budget_tau=10, complete_budget_tau=3)
    _submit(bus, goal_id="g11")
    law.acknowledge("g11")
    law.update_progress("g11", 0.5)
    law.pulse(); law.pulse(); law.pulse()
    assert law.get("g11").state == GoalState.ORPHANED


def test_terminal_goals_do_not_advance_on_pulse():
    law, bus, _ = _law()
    _submit(bus, goal_id="g12")
    law.complete("g12", "done")
    before_tau = law.get("g12").lifecycle_tau
    law.pulse(); law.pulse()
    assert law.get("g12").lifecycle_tau == before_tau


# ─────────────────────────────────────────────────────────────────────────────
# Summary + bus publication
# ─────────────────────────────────────────────────────────────────────────────


def test_pulse_publishes_echo_summary():
    law, bus, _ = _law()
    _submit(bus, goal_id="g13"); _submit(bus, goal_id="g14")
    law.complete("g13", "ok")
    bus.published.clear()
    summary = law.pulse()
    pub = [t for t in bus.published if t.topic == "goal.echo.summary"]
    assert len(pub) == 1
    p = pub[0].payload
    assert p["counts"]["COMPLETED"] == 1
    assert p["counts"]["PROPOSED"] == 1
    assert p["active_count"] == 1
    assert p["total_goals"] == 2
    # summary returned by pulse matches what's published
    assert p["completion_rate"] == summary["completion_rate"]


def test_orphan_rate_climbs_with_abandoned_lighthouses():
    law, bus, _ = _law(ack_budget_tau=1)
    for i in range(4):
        _submit(bus, goal_id=f"orphan{i}")
    law.pulse()  # all 4 orphan
    summary = law.summary()
    assert summary["orphan_rate"] == 1.0


def test_completion_rate_reflects_closed_lines():
    law, bus, _ = _law()
    _submit(bus, goal_id="a"); _submit(bus, goal_id="b")
    law.complete("a", "done")
    law.abandon("b", "withdrawn")
    summary = law.summary()
    # Two terminal goals, one complete, one abandoned
    assert summary["completion_rate"] == 0.5
    assert summary["counts"]["COMPLETED"] == 1
    assert summary["counts"]["ABANDONED"] == 1


# ─────────────────────────────────────────────────────────────────────────────
# Vault ingestion
# ─────────────────────────────────────────────────────────────────────────────


def test_every_transition_lands_on_vault():
    law, bus, vault = _law()
    _submit(bus, goal_id="g15")
    law.acknowledge("g15")
    law.update_progress("g15", 0.3)
    law.complete("g15", "done")
    topics = [rec["topic"] for rec in vault.ingested]
    # Four transitions → four vault cards
    assert topics.count("goal.echo") >= 4
    final_payload = vault.ingested[-1]["payload"]
    assert final_payload["state"] == "COMPLETED"


# ─────────────────────────────────────────────────────────────────────────────
# Env-var budgets
# ─────────────────────────────────────────────────────────────────────────────


def test_env_var_overrides_ack_budget(monkeypatch):
    monkeypatch.setenv("AUREON_GOAL_ACK_BUDGET_TAU", "5")
    law = TemporalCausalityLaw()
    assert law.ack_budget_tau == 5


def test_env_var_overrides_complete_budget(monkeypatch):
    monkeypatch.setenv("AUREON_GOAL_COMPLETE_BUDGET_TAU", "9")
    law = TemporalCausalityLaw()
    assert law.complete_budget_tau == 9


def test_explicit_override_beats_env(monkeypatch):
    monkeypatch.setenv("AUREON_GOAL_ACK_BUDGET_TAU", "99")
    law = TemporalCausalityLaw(ack_budget_tau=7)
    assert law.ack_budget_tau == 7


# ─────────────────────────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────────────────────────


def test_singleton_accessor():
    reset_temporal_causality_law()
    a = get_temporal_causality_law()
    b = get_temporal_causality_law()
    assert a is b
    reset_temporal_causality_law()


# ─────────────────────────────────────────────────────────────────────────────
# SymbolicLifeBridge integration — goal_lighthouse subsystem
# ─────────────────────────────────────────────────────────────────────────────


def test_bridge_registers_goal_lighthouse_subsystem():
    from aureon.vault.voice.symbolic_life_bridge import SymbolicLifeBridge
    assert "goal_lighthouse" in SymbolicLifeBridge.SUBSYSTEMS


def test_bridge_ingests_goal_echo_summary():
    from aureon.vault.voice.symbolic_life_bridge import SymbolicLifeBridge
    bus = _StubBus()
    bridge = SymbolicLifeBridge(thought_bus=bus, horizon=16)
    bridge.start()
    # High completion, low orphan → health = 0.8 - 0.0 + 0.5 = 1.3 → clamp 1.0
    bus.publish(_Thought("goal.echo.summary",
                         {"completion_rate": 0.8, "orphan_rate": 0.0}))
    assert bridge.rolling_summary()["goal_lighthouse"]["count"] == 1
    assert bridge.rolling_summary()["goal_lighthouse"]["mean"] == 1.0


def test_bridge_ingests_orphaned_as_zero():
    from aureon.vault.voice.symbolic_life_bridge import SymbolicLifeBridge
    bus = _StubBus()
    bridge = SymbolicLifeBridge(thought_bus=bus, horizon=16)
    bridge.start()
    bus.publish(_Thought("goal.echo.orphaned", {"goal_id": "x"}))
    assert bridge.rolling_summary()["goal_lighthouse"]["count"] == 1
    assert bridge.rolling_summary()["goal_lighthouse"]["mean"] == 0.0


def test_bridge_goal_lighthouse_rises_with_healthy_summaries():
    from aureon.vault.voice.symbolic_life_bridge import SymbolicLifeBridge
    bus = _StubBus()
    bridge = SymbolicLifeBridge(thought_bus=bus, horizon=16)
    bridge.start()
    for _ in range(5):
        bus.publish(_Thought("goal.echo.summary",
                             {"completion_rate": 1.0, "orphan_rate": 0.0}))
    summary = bridge.rolling_summary()
    assert summary["goal_lighthouse"]["count"] == 5
    assert summary["goal_lighthouse"]["mean"] == 1.0


def test_bridge_goal_lighthouse_falls_with_orphans():
    from aureon.vault.voice.symbolic_life_bridge import SymbolicLifeBridge
    bus = _StubBus()
    bridge = SymbolicLifeBridge(thought_bus=bus, horizon=16)
    bridge.start()
    for _ in range(6):
        bus.publish(_Thought("goal.echo.summary",
                             {"completion_rate": 0.0, "orphan_rate": 0.8}))
    summary = bridge.rolling_summary()
    # health = 0.0 - 0.8 + 0.5 = -0.3 → clamp 0.0
    assert summary["goal_lighthouse"]["mean"] == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# End-to-end: submission through law through bridge
# ─────────────────────────────────────────────────────────────────────────────


def test_end_to_end_goal_lifecycle_moves_bridge_pillar():
    """A goal proposed by a persona, completed cleanly, should register
    as a healthy lighthouse echo and lift the bridge's goal_lighthouse
    signal. A second goal that orphans should drop it."""
    from aureon.vault.voice.symbolic_life_bridge import SymbolicLifeBridge
    bus = _StubBus()
    vault = _StubVault()
    law = TemporalCausalityLaw(thought_bus=bus, vault=vault,
                               ack_budget_tau=1)
    law.start()
    bridge = SymbolicLifeBridge(thought_bus=bus, vault=vault, horizon=16)
    bridge.start()

    # 1. Healthy goal: propose → acknowledge → complete → pulse.
    _submit(bus, goal_id="h1")
    law.acknowledge("h1", engine_id="engine")
    law.complete("h1", "done")
    law.pulse()
    healthy_mean = bridge.rolling_summary()["goal_lighthouse"]["mean"]
    assert healthy_mean > 0.5

    # 2. Orphan another: propose and let the budget expire.
    _submit(bus, goal_id="o1")
    law.pulse()   # tau=1, orphans
    final = bridge.rolling_summary()
    # After the orphan both a summary AND an orphaned event landed
    assert final["goal_lighthouse"]["count"] >= 3


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
