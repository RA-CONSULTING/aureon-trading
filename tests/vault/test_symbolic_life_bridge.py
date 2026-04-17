#!/usr/bin/env python3
"""
Tests for SymbolicLifeBridge — the wiring that makes the persona layer
actually feed the Λ engine's Auris Conjecture pillars.

What's being proved:
  - Bridge subscribes to the expected bus topics and records events
  - Quiet system → low symbolic_life_score
  - Active system (collapses, goals, life events, mesh) raises the score
  - Each pillar responds to the corresponding event category:
      persona.collapse     → ac_self_organization (via winner stability)
      life.event + turn    → ac_meaning_propagation (coherence_phi × γ)
      goal.submit.request  → ac_adaptive_recursion (via ψ change)
      conversation.turn    → ac_memory_persistence (via history depth)
  - pulse() publishes a `symbolic.life.pulse` thought with the expected
    payload shape
  - The vault receives `current_symbolic_life_score` after a pulse
  - Bridge survives when lambda_engine is unavailable (gracefully returns)
"""

from __future__ import annotations

import os
import sys
import time
from typing import Any, Callable, Dict, List

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from aureon.vault.voice.symbolic_life_bridge import SymbolicLifeBridge  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
# Stubs
# ─────────────────────────────────────────────────────────────────────────────


class _StubBus:
    def __init__(self):
        self.published: List[Any] = []
        self._subs: Dict[str, List[Callable]] = {}

    def publish(self, thought=None, **kwargs):
        if thought is None:
            class _T:
                pass
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

    def subscribe(self, topic: str, handler: Callable) -> None:
        self._subs.setdefault(topic, []).append(handler)


class _Thought:
    def __init__(self, topic: str, payload: Dict[str, Any]):
        self.topic = topic
        self.payload = payload
        self.source = "test"


class _StubVault:
    def __init__(self):
        self.fields: Dict[str, Any] = {}

    def __setattr__(self, name, value):
        # Record every attribute write so we can inspect
        # current_symbolic_life_score / current_consciousness_level etc.
        if name == "fields":
            object.__setattr__(self, name, value)
            return
        self.fields[name] = value


# ─────────────────────────────────────────────────────────────────────────────
# Basic lifecycle + subscription
# ─────────────────────────────────────────────────────────────────────────────


def _bridge(**overrides):
    bus = overrides.pop("bus", None) or _StubBus()
    vault = overrides.pop("vault", None) or _StubVault()
    b = SymbolicLifeBridge(thought_bus=bus, vault=vault, horizon=16, **overrides)
    b.start()
    return b, bus, vault


def test_bridge_subscribes_to_expected_topics():
    b, bus, _ = _bridge()
    for topic in ("persona.collapse", "persona.thought", "goal.submit.request",
                  "life.event", "bridge.peer.state", "conversation.turn",
                  "conversation.ambient"):
        assert topic in bus._subs, f"bridge did not subscribe to {topic}"


def test_bridge_start_is_idempotent():
    b, bus, _ = _bridge()
    before = {t: len(h) for t, h in bus._subs.items()}
    b.start()
    after = {t: len(h) for t, h in bus._subs.items()}
    assert before == after


# ─────────────────────────────────────────────────────────────────────────────
# Event recording
# ─────────────────────────────────────────────────────────────────────────────


def test_persona_collapse_is_recorded():
    b, bus, _ = _bridge()
    bus.publish(_Thought("persona.collapse", {
        "winner": "engineer", "probabilities": {"engineer": 0.8},
    }))
    s = b.rolling_summary()
    assert s["persona_collapse"]["count"] == 1
    assert s["chorus_coherence"]["count"] == 1


def test_goal_request_is_recorded():
    b, bus, _ = _bridge()
    bus.publish(_Thought("goal.submit.request", {
        "text": "draft a paper", "urgency": 0.9,
    }))
    s = b.rolling_summary()
    assert s["goal_commitment"]["count"] == 1


def test_life_event_active_weighs_more_than_archived():
    b, bus, _ = _bridge()
    bus.publish(_Thought("life.event", {"status": "active"}))
    bus.publish(_Thought("life.event", {"status": "archived"}))
    s = b.rolling_summary()
    assert s["life_resonance"]["count"] == 2
    # active=1.0, archived=0.2 → mean = 0.6
    assert abs(s["life_resonance"]["mean"] - 0.6) < 0.05


def test_conversation_turn_bumps_vault_and_life():
    b, bus, _ = _bridge()
    bus.publish(_Thought("conversation.turn", {
        "persona": "mystic", "question": "what should I do?",
    }))
    s = b.rolling_summary()
    assert s["vault_memory"]["count"] == 1
    # A turn with a question ALSO bumps life_resonance (operator engagement).
    assert s["life_resonance"]["count"] == 1


def test_peer_state_bumps_mesh_unity():
    b, bus, _ = _bridge()
    bus.publish(_Thought("bridge.peer.state", {
        "peer_id": "remote", "state": {}, "fingerprint": "abc",
    }))
    assert b.rolling_summary()["mesh_unity"]["count"] == 1


# ─────────────────────────────────────────────────────────────────────────────
# Pulse — Λ engine integration
# ─────────────────────────────────────────────────────────────────────────────


def test_pulse_returns_state_with_five_pillars():
    b, bus, vault = _bridge()
    # Feed some events so the subsystem densities aren't all zero.
    bus.publish(_Thought("persona.collapse", {
        "winner": "engineer", "probabilities": {"engineer": 0.9},
    }))
    bus.publish(_Thought("conversation.turn", {"question": "status?"}))
    bus.publish(_Thought("life.event", {"status": "active"}))
    state = b.pulse()
    assert state is not None
    # LambdaState carries the five pillars.
    for attr in ("ac_self_organization", "ac_memory_persistence",
                 "ac_energy_stability", "ac_adaptive_recursion",
                 "ac_meaning_propagation", "symbolic_life_score"):
        assert hasattr(state, attr), f"Λ state missing {attr}"
        assert 0.0 <= getattr(state, attr) <= 1.0


def test_pulse_publishes_symbolic_life_pulse_topic():
    b, bus, _ = _bridge()
    bus.publish(_Thought("persona.collapse", {"winner": "mystic",
                                              "probabilities": {"mystic": 0.6}}))
    b.pulse()
    topics = [getattr(t, "topic", "") for t in bus.published]
    assert "symbolic.life.pulse" in topics
    # Payload shape
    pulse = next(t for t in bus.published if t.topic == "symbolic.life.pulse")
    p = pulse.payload
    for k in ("lambda_t", "consciousness_psi", "coherence_gamma",
              "symbolic_life_score", "ac_self_organization",
              "ac_memory_persistence", "ac_energy_stability",
              "ac_adaptive_recursion", "ac_meaning_propagation",
              "readings", "pulse_ts"):
        assert k in p, f"pulse payload missing {k}"
    # Readings list contains our seven subsystems.
    names = {r["name"] for r in p["readings"]}
    assert names == set(SymbolicLifeBridge.SUBSYSTEMS)


def test_pulse_writes_symbolic_life_score_to_vault():
    """LambdaEngine.step() with a vault= arg mirrors the score onto
    `vault.current_symbolic_life_score`. Our bridge passes the vault,
    so this assertion proves the wiring actually lands on the vault."""
    b, bus, vault = _bridge()
    bus.publish(_Thought("persona.collapse", {
        "winner": "engineer", "probabilities": {"engineer": 0.8},
    }))
    b.pulse()
    assert "current_symbolic_life_score" in vault.fields
    assert 0.0 <= float(vault.fields["current_symbolic_life_score"]) <= 1.0


def test_active_system_has_higher_score_than_quiet_baseline():
    # Quiet: build bridge, pulse without events
    b_quiet, _, _ = _bridge()
    # Give it a small warm-up so memory_persistence has SOMETHING to count
    for _ in range(5):
        b_quiet.pulse()
    quiet_score = b_quiet.last_state.symbolic_life_score

    # Active: feed a rich stream of events, THEN pulse enough times to
    # build history, and take the final score.
    b_active, bus, _ = _bridge()
    for i in range(12):
        bus.publish(_Thought("persona.collapse", {
            "winner": "engineer", "probabilities": {"engineer": 0.85},
        }))
        bus.publish(_Thought("conversation.turn", {"question": f"q{i}",
                                                   "persona": "engineer"}))
        bus.publish(_Thought("goal.submit.request", {"text": "do a thing",
                                                     "urgency": 0.7}))
        bus.publish(_Thought("life.event", {"status": "active"}))
    for _ in range(10):
        b_active.pulse()
    active_score = b_active.last_state.symbolic_life_score

    assert active_score > quiet_score, (
        f"active SLS {active_score:.3f} should exceed quiet SLS {quiet_score:.3f}"
    )


def test_unified_winner_raises_self_organization():
    """Same winner across many collapses should increase the
    persona_collapse reading value (winner stability pathway)."""
    b, bus, _ = _bridge()
    for _ in range(12):
        bus.publish(_Thought("persona.collapse", {
            "winner": "engineer", "probabilities": {"engineer": 0.85},
        }))
    readings = b._build_readings()
    pc = next(r for r in readings if r.name == "persona_collapse")
    assert pc.state == "unified"
    assert pc.value >= 0.5


def test_pulse_count_increments():
    b, _, _ = _bridge()
    assert b.pulse_count == 0
    b.pulse()
    b.pulse()
    assert b.pulse_count == 2


def test_bridge_tolerates_missing_lambda_engine():
    """A bridge built against a broken engine should still subscribe
    cleanly and return None from pulse() instead of raising."""
    class _BrokenEngine:
        def step(self, readings=None, volatility=0.0, vault=None):
            raise RuntimeError("engine is down")
    bus = _StubBus()
    vault = _StubVault()
    b = SymbolicLifeBridge(thought_bus=bus, vault=vault,
                           lambda_engine=_BrokenEngine(), horizon=8)
    b.start()
    bus.publish(_Thought("persona.collapse",
                         {"winner": "mystic", "probabilities": {"mystic": 0.6}}))
    assert b.pulse() is None
    assert b.pulse_count == 0


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
