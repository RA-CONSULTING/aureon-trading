#!/usr/bin/env python3
"""
Tests for PersonaVacuum — the quantum-collapse layer over the ten personas.

  - subscribes to dj.track.drop / queen.source_law.cognition / persona.observe
  - softmax distribution matches manual computation
  - deterministic collapse under a seeded RNG
  - 10k-sample empirical distribution sits within 3σ of softmax probabilities
  - publishes persona.collapse + persona.thought after observe()
  - calls vault.ingest(topic=..., payload=...) when vault exposes it
  - no exception if vault has no ingest method
"""

from __future__ import annotations

import math
import os
import random
import sys
from typing import Any, Callable, Dict, List

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from aureon.vault.voice.aureon_personas import (  # noqa: E402
    AUREON_PERSONA_REGISTRY,
    build_aureon_personas,
)
from aureon.vault.voice.persona_vacuum import PersonaVacuum, _softmax  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
# Test doubles
# ─────────────────────────────────────────────────────────────────────────────


class _StubThought:
    def __init__(self, topic: str, payload: Dict[str, Any]):
        self.topic = topic
        self.payload = payload
        self.source = "test"


class _StubBus:
    def __init__(self):
        self.published: List[_StubThought] = []
        self._subs: Dict[str, List[Callable]] = {}

    def publish(self, thought):
        # PersonaVacuum publishes via Thought(...) — accept either the real
        # Thought class or our stub; both have .topic/.payload.
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
            text = "stub response"
            model = "stub"
            usage = {"total_tokens": 5}

        return _R()


class _StubVault:
    def __init__(self):
        self.love_amplitude = 0.5
        self.gratitude_score = 0.5
        self.last_casimir_force = 0.0
        self.last_lambda_t = 0.1
        self.dominant_chakra = "heart"
        self.dominant_frequency_hz = 528.0
        self.rally_active = False
        self.cortex_snapshot = {"delta": 0.1, "theta": 0.2, "alpha": 0.2, "beta": 0.2, "gamma": 0.3}
        self.ingested: List[Dict[str, Any]] = []

    def fingerprint(self) -> str:
        return "stubfp"

    def __len__(self) -> int:
        return 7

    def ingest(self, topic: str, payload: Any):
        self.ingested.append({"topic": topic, "payload": payload})
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _make_vacuum(rng_seed: int = 42, temperature: float = 1.0) -> tuple:
    bus = _StubBus()
    personas = build_aureon_personas(adapter=_StubAdapter())
    vacuum = PersonaVacuum(
        personas=personas,
        thought_bus=bus,
        rng=random.Random(rng_seed),
        temperature=temperature,
    )
    vacuum.start()
    return vacuum, bus, personas


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────


def test_subscribes_to_three_topics():
    vacuum, bus, _ = _make_vacuum()
    assert "dj.track.drop" in bus._subs
    assert "queen.source_law.cognition" in bus._subs
    assert "persona.observe" in bus._subs


def test_drop_and_cognition_update_internal_state():
    vacuum, bus, _ = _make_vacuum()
    bus.publish(_StubThought("dj.track.drop", {"energy": 0.9, "bpm": 128.0}))
    bus.publish(_StubThought("queen.source_law.cognition", {
        "coherence_gamma": 0.95, "consciousness_psi": 0.8, "consciousness_level": "DAWNING",
        "node_readings": {"tiger": 0.9},
    }))
    state = vacuum._build_state(_StubVault())
    assert state["dj_drop"]["energy"] == 0.9
    assert state["dj_drop"]["bpm"] == 128.0
    assert state["coherence_gamma"] == 0.95
    assert state["consciousness_psi"] == 0.8
    assert state["consciousness_level"] == "DAWNING"
    assert state["node_readings"]["tiger"] == 0.9


def test_softmax_distribution_matches_manual_computation():
    scores = [0.5, 1.0, 1.5, 2.0, 0.0, 0.1, 0.2, 0.3, 0.4, 0.6]
    probs = _softmax(scores, temperature=1.0)
    assert math.isclose(sum(probs), 1.0, abs_tol=1e-9)
    # manual
    m = max(scores)
    exps = [math.exp(s - m) for s in scores]
    z = sum(exps)
    manual = [e / z for e in exps]
    for p, q in zip(probs, manual):
        assert math.isclose(p, q, abs_tol=1e-9)


def test_collapse_is_deterministic_under_seeded_rng():
    state_cfg = {
        "dj.track.drop": {"energy": 0.0, "bpm": 0.0},
        "queen.source_law.cognition": {
            "coherence_gamma": 0.96,
            "consciousness_psi": 0.2,
            "consciousness_level": "",
            "node_readings": {"tiger": 0.9},
        },
    }

    def run_once(seed: int) -> str:
        vacuum, bus, _ = _make_vacuum(rng_seed=seed)
        for topic, payload in state_cfg.items():
            bus.publish(_StubThought(topic, payload))
        vacuum.observe(_StubVault())
        return vacuum.last_winner

    w1 = run_once(42)
    w2 = run_once(42)
    assert w1 == w2
    # Engineer is the peak for this configuration
    assert w1 == "engineer"


def test_empirical_distribution_within_3_sigma():
    vacuum, bus, personas = _make_vacuum(rng_seed=7)
    # neutral state — every persona gets its baseline
    state = {
        "love_amplitude": 0.5, "gratitude_score": 0.5, "dominant_chakra": "solar",
        "dominant_frequency_hz": 300.0, "rally_active": False, "vault_size": 50,
        "cortex": {"delta": 0.2, "theta": 0.2, "alpha": 0.2, "beta": 0.2, "gamma": 0.2},
        "consciousness_psi": 0.3, "coherence_gamma": 0.3, "consciousness_level": "",
        "confidence": 0.3, "node_readings": {"tiger": 0.3, "falcon": 0.3, "dolphin": 0.3, "panda": 0.3},
        "dj_drop": {},
        "last_lambda_t": 0.0,
    }
    raw = [personas[n].compute_affinity(state) for n in personas]
    expected = dict(zip(personas.keys(), _softmax(raw, temperature=1.0)))

    # Seed cognition + drop so _build_state sees the same neutral frame
    bus.publish(_StubThought("queen.source_law.cognition", {
        "coherence_gamma": 0.3, "consciousness_psi": 0.3, "consciousness_level": "",
        "confidence": 0.3,
        "node_readings": {"tiger": 0.3, "falcon": 0.3, "dolphin": 0.3, "panda": 0.3},
    }))

    class _NeutralVault(_StubVault):
        def __init__(self):
            super().__init__()
            self.love_amplitude = 0.5
            self.gratitude_score = 0.5
            self.last_lambda_t = 0.0
            self.dominant_chakra = "solar"
            self.dominant_frequency_hz = 300.0
            self.rally_active = False
            self.cortex_snapshot = state["cortex"]

        def __len__(self):
            return 50

    vault = _NeutralVault()
    n = 10_000
    counts = {name: 0 for name in personas}
    for _ in range(n):
        vacuum.observe(vault)
        counts[vacuum.last_winner] += 1

    for name, p in expected.items():
        observed = counts[name] / n
        sigma = math.sqrt(max(p * (1 - p), 1e-12) / n)
        # 3σ tolerance, with a floor so tiny-p buckets still have room
        tol = max(3 * sigma, 0.005)
        assert abs(observed - p) < tol, (
            f"{name}: observed {observed:.4f} vs expected {p:.4f} (tol {tol:.4f})"
        )


def test_observe_publishes_collapse_and_thought():
    vacuum, bus, _ = _make_vacuum()
    bus.publish(_StubThought("queen.source_law.cognition", {
        "coherence_gamma": 0.96, "node_readings": {"tiger": 0.9},
    }))
    before = len(bus.published)
    vacuum.observe(_StubVault())
    after_topics = [t.topic for t in bus.published[before:]]
    assert "persona.collapse" in after_topics
    assert "persona.thought" in after_topics


def test_observe_calls_vault_ingest_when_available():
    vacuum, bus, _ = _make_vacuum()
    vault = _StubVault()
    vacuum.observe(vault)
    assert vault.ingested, "vault.ingest was not called"
    assert vault.ingested[-1]["topic"] == "persona.thought"
    assert isinstance(vault.ingested[-1]["payload"], dict)


def test_observe_tolerates_vault_without_ingest():
    vacuum, bus, _ = _make_vacuum()

    class _NoIngest:
        love_amplitude = 0.5
        gratitude_score = 0.5
        last_casimir_force = 0.0
        last_lambda_t = 0.0
        dominant_chakra = "heart"
        dominant_frequency_hz = 528.0
        rally_active = False
        cortex_snapshot = {"gamma": 0.5}

        def fingerprint(self):
            return ""

    # must not raise
    vacuum.observe(_NoIngest())


def test_observe_handles_none_vault():
    vacuum, bus, _ = _make_vacuum()
    # With no vault, speak() still runs via stub adapter — should not raise.
    stmt = vacuum.observe(None)
    # stmt may be a VoiceStatement (stub adapter returns text) or None if
    # prompt composition emitted no lines on the empty slice — either way
    # the collapse itself must have been recorded.
    assert vacuum.collapse_count >= 1


def test_persona_observe_trigger_calls_observe():
    vacuum, bus, _ = _make_vacuum()
    bus.publish(_StubThought("persona.observe", {}))
    assert vacuum.collapse_count >= 1


def test_temperature_env_var_is_respected(monkeypatch=None):
    os.environ["AUREON_PERSONA_TEMPERATURE"] = "0.25"
    try:
        personas = build_aureon_personas(adapter=_StubAdapter())
        vacuum = PersonaVacuum(
            personas=personas,
            thought_bus=_StubBus(),
            rng=random.Random(0),
        )
        assert abs(vacuum.temperature - 0.25) < 1e-9
    finally:
        os.environ.pop("AUREON_PERSONA_TEMPERATURE", None)


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
