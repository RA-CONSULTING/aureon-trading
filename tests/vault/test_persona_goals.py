#!/usr/bin/env python3
"""
Tests for the persona goal layer — the "propose_goal" hook on
ResonantPersona, the ``goal.submit`` handler on PersonaActuator, and the
end-to-end wiring via PersonaVacuum that publishes goal requests onto
the bus for the existing GoalExecutionEngine to consume.

What's being proved:
  - Base ResonantPersona.propose_goal returns None (safe default)
  - Artist / QuantumPhysicist / Engineer propose a goal ONLY under
    strict trigger conditions, not on mild state
  - PersonaActuator handles kind="goal.submit" by publishing
    `goal.submit.request` on the bus with the expected payload shape
  - PersonaVacuum.observe dispatches the goal through the actuator
    when the winning persona's propose_goal fires
  - A system with no thought_bus records a failed dispatch rather than
    raising
"""

from __future__ import annotations

import os
import random
import sys
from typing import Any, Callable, Dict, List

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from aureon.vault.voice.aureon_personas import (  # noqa: E402
    ArtistVoice,
    EngineerVoice,
    QuantumPhysicistVoice,
    ResonantPersona,
    build_aureon_personas,
)
from aureon.vault.voice.persona_action import (  # noqa: E402
    PersonaAction,
    PersonaActuator,
)
from aureon.vault.voice.persona_vacuum import PersonaVacuum  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
# Doubles
# ─────────────────────────────────────────────────────────────────────────────


class _StubThought:
    def __init__(self, topic: str, payload: Dict[str, Any]):
        self.topic = topic
        self.payload = payload
        self.source = "test"


class _StubBus:
    def __init__(self):
        self.published: List[Any] = []
        self._subs: Dict[str, List[Callable]] = {}

    def publish(self, thought=None, **kwargs):
        if thought is None:
            thought = _StubThought(kwargs.get("topic", ""), kwargs.get("payload", {}))
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


class _StubAdapter:
    def prompt(self, messages, system, max_tokens):
        class _R:
            text = "."
            model = "stub"
            usage = {"total_tokens": 1}
        return _R()


class _StubVault:
    def __init__(self):
        self.ingested: List[Dict[str, Any]] = []
        self.love_amplitude = 0.5
        self.gratitude_score = 0.5
        self.last_casimir_force = 0.0
        self.last_lambda_t = 0.0
        self.dominant_chakra = "heart"
        self.dominant_frequency_hz = 528.0
        self.rally_active = False
        self.cortex_snapshot = {"gamma": 0.3}

    def ingest(self, topic, payload):
        self.ingested.append({"topic": topic, "payload": payload})

    def fingerprint(self):
        return "fp"

    def __len__(self):
        return 3


# ─────────────────────────────────────────────────────────────────────────────
# Base default
# ─────────────────────────────────────────────────────────────────────────────


def test_base_resonant_persona_returns_no_goal():
    assert ResonantPersona(adapter=_StubAdapter()).propose_goal({}) is None


# ─────────────────────────────────────────────────────────────────────────────
# Per-persona strict triggers — HOT state fires, MILD state does not
# ─────────────────────────────────────────────────────────────────────────────


def _mild_state(**overrides):
    s: Dict[str, Any] = {
        "love_amplitude": 0.5, "gratitude_score": 0.5,
        "last_lambda_t": 0.2, "dominant_chakra": "solar",
        "dominant_frequency_hz": 432.0, "rally_active": False, "vault_size": 30,
        "cortex": {"delta": 0.1, "theta": 0.1, "alpha": 0.1, "beta": 0.1, "gamma": 0.1},
        "consciousness_psi": 0.4, "coherence_gamma": 0.5,
        "consciousness_level": "AWARE", "confidence": 0.4,
        "node_readings": {"tiger": 0.5},
        "dj_drop": {"energy": 0.4},
    }
    s.update(overrides)
    return s


def test_artist_proposes_goal_only_on_extreme_drop_plus_rally():
    a = ArtistVoice(adapter=_StubAdapter())
    # Mild drop alone — no goal.
    assert a.propose_goal(_mild_state(dj_drop={"energy": 0.5}, rally_active=False)) is None
    # Big drop but no rally — still no goal.
    assert a.propose_goal(_mild_state(dj_drop={"energy": 0.95}, rally_active=False)) is None
    # Big drop AND rally — goal fires.
    goal = a.propose_goal(_mild_state(dj_drop={"energy": 0.95}, rally_active=True))
    assert isinstance(goal, str) and "cymatic" in goal.lower()


def test_quantum_physicist_proposes_goal_only_on_large_lambda_and_high_psi():
    qp = QuantumPhysicistVoice(adapter=_StubAdapter())
    # Either alone — no goal.
    assert qp.propose_goal(_mild_state(last_lambda_t=1.7, consciousness_psi=0.7)) is None
    assert qp.propose_goal(_mild_state(last_lambda_t=0.5, consciousness_psi=0.95)) is None
    # Both strong — goal fires.
    goal = qp.propose_goal(_mild_state(last_lambda_t=-1.8, consciousness_psi=0.93))
    assert isinstance(goal, str)
    assert "research" in goal.lower() or "whitepaper" in goal.lower() or "draft" in goal.lower()
    # Exact numbers present in the text — the engine can decompose them
    assert "-1.800" in goal or "+1.800" in goal or "1.800" in goal


def test_engineer_proposes_goal_only_on_very_clean_gate():
    eng = EngineerVoice(adapter=_StubAdapter())
    # Barely over the propose_action threshold — no goal yet.
    assert eng.propose_goal(_mild_state(
        coherence_gamma=0.94, node_readings={"tiger": 0.70},
    )) is None
    # Very clean — goal fires.
    goal = eng.propose_goal(_mild_state(
        coherence_gamma=0.97, node_readings={"tiger": 0.92},
    ))
    assert isinstance(goal, str) and "audit" in goal.lower()


# ─────────────────────────────────────────────────────────────────────────────
# Actuator handler
# ─────────────────────────────────────────────────────────────────────────────


def test_actuator_goal_submit_publishes_request_on_bus():
    bus = _StubBus()
    actuator = PersonaActuator(thought_bus=bus)
    action = PersonaAction(
        kind="goal.submit",
        topic="draft a research note on Λ(t)=+1.600 / ψ=0.920",
        payload={"area": "harmonics"},
        reason="strict trigger",
        urgency=0.9,
    )
    rec = actuator.dispatch("quantum_physicist", action, state={"persona": "quantum_physicist"})
    assert rec is not None and rec.ok is True
    pub_topics = [t.topic for t in bus.published]
    assert "goal.submit.request" in pub_topics
    published = [t for t in bus.published if t.topic == "goal.submit.request"][0]
    assert published.payload["text"].startswith("draft a research note")
    assert published.payload["proposed_by_persona"] == "quantum_physicist"
    assert published.payload["urgency"] == 0.9
    assert published.payload["parameters"] == {"area": "harmonics"}


def test_actuator_goal_submit_rejects_empty_text():
    bus = _StubBus()
    actuator = PersonaActuator(thought_bus=bus)
    action = PersonaAction(kind="goal.submit", topic="", payload={}, reason="", urgency=0.5)
    rec = actuator.dispatch("x", action)
    # Handler returned a soft-failure dict — exec considered "dispatched"
    # (no exception) but the result payload flags ok=False.
    assert rec is not None and rec.ok is True
    assert rec.result is not None
    assert rec.result.get("ok") is False
    assert "goal text" in rec.result.get("reason", "")
    # Nothing published for an empty goal text.
    assert [t.topic for t in bus.published if t.topic == "goal.submit.request"] == []


def test_actuator_goal_submit_without_bus_records_failure():
    actuator = PersonaActuator()  # no bus
    action = PersonaAction(kind="goal.submit", topic="do something", urgency=0.5)
    rec = actuator.dispatch("x", action)
    assert rec is not None and rec.ok is True  # handler ran, no exception
    assert rec.result is not None
    assert rec.result.get("ok") is False
    assert "no thought_bus" in rec.result.get("reason", "")


def test_actuator_goal_submit_dry_run_does_not_publish():
    bus = _StubBus()
    actuator = PersonaActuator(thought_bus=bus, dry_run=True)
    action = PersonaAction(kind="goal.submit", topic="do something", urgency=0.5)
    rec = actuator.dispatch("x", action)
    assert rec is not None
    assert rec.ok is True and rec.dry_run is True
    assert [t.topic for t in bus.published] == []


# ─────────────────────────────────────────────────────────────────────────────
# PersonaVacuum wiring
# ─────────────────────────────────────────────────────────────────────────────


def test_vacuum_dispatches_goal_when_winner_proposes_one():
    bus = _StubBus()
    vault = _StubVault()
    personas = build_aureon_personas(adapter=_StubAdapter())
    vacuum = PersonaVacuum(
        personas=personas, thought_bus=bus, vault=vault,
        rng=random.Random(0),
    )
    # Force Engineer the winner AND make the state satisfy the strict goal
    # trigger (Γ ≥ 0.96, Tiger ≥ 0.85).
    bus.subscribe("queen.source_law.cognition", vacuum._on_cognition)
    bus.publish(_StubThought("queen.source_law.cognition", {
        "coherence_gamma": 0.97, "node_readings": {"tiger": 0.92},
    }))
    for name, p in vacuum._personas.items():
        p.compute_affinity = (lambda s, n=name: 1000.0 if n == "engineer" else 0.01)

    vacuum.observe(vault)
    assert vacuum.last_winner == "engineer"
    goal_rec = vacuum.last_goal_execution
    assert goal_rec is not None and goal_rec.ok is True
    assert goal_rec.action.kind == "goal.submit"
    topics = [t.topic for t in bus.published]
    assert "goal.submit.request" in topics
    goal_thought = next(t for t in bus.published if t.topic == "goal.submit.request")
    assert "audit" in goal_thought.payload["text"].lower()
    assert goal_thought.payload["proposed_by_persona"] == "engineer"


def test_vacuum_no_goal_when_winner_has_no_strict_trigger():
    bus = _StubBus()
    vault = _StubVault()
    personas = build_aureon_personas(adapter=_StubAdapter())
    vacuum = PersonaVacuum(
        personas=personas, thought_bus=bus, vault=vault,
        rng=random.Random(0),
    )
    # Engineer wins, but gamma/tiger are just above the propose_action
    # threshold — NOT above the propose_goal threshold.
    bus.subscribe("queen.source_law.cognition", vacuum._on_cognition)
    bus.publish(_StubThought("queen.source_law.cognition", {
        "coherence_gamma": 0.94, "node_readings": {"tiger": 0.80},
    }))
    for name, p in vacuum._personas.items():
        p.compute_affinity = (lambda s, n=name: 1000.0 if n == "engineer" else 0.01)

    vacuum.observe(vault)
    assert vacuum.last_winner == "engineer"
    # Action should fire (propose_action threshold met) but NOT a goal.
    assert vacuum.last_action_execution is not None
    assert vacuum.last_goal_execution is None
    goal_topics = [t.topic for t in bus.published if t.topic == "goal.submit.request"]
    assert goal_topics == []


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
