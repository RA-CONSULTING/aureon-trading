#!/usr/bin/env python3
"""
Tests for the persona action layer — PersonaAction, PersonaActuator,
and the per-persona propose_action() overrides.

Covers:
  - PersonaAction dataclass round-trip via to_dict
  - Actuator dispatch in dry_run — action recorded, handlers never called
  - Each of the four default handlers fires under the real path
  - Unknown action.kind recorded with an error, never raises
  - Thread-safe history, maxlen respected
  - Per-persona propose_action trigger matrix — cold state → None,
    hot state → expected (kind, topic)
  - PersonaVacuum integration — collapse triggers actuator dispatch,
    last_action_execution reflects reality
"""

from __future__ import annotations

import os
import random
import sys
import tempfile
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from aureon.vault.aureon_vault import AureonVault  # noqa: E402
from aureon.vault.voice.aureon_personas import (  # noqa: E402
    AUREON_PERSONA_REGISTRY,
    ArtistVoice,
    ChildVoice,
    ElderVoice,
    EngineerVoice,
    LeftVoice,
    MysticVoice,
    PainterVoice,
    PhilosopherVoice,
    QuantumPhysicistVoice,
    ResonantPersona,
    RightVoice,
)
from aureon.vault.voice.persona_action import (  # noqa: E402
    ActionExecution,
    PersonaAction,
    PersonaActuator,
)
from aureon.vault.voice.persona_vacuum import PersonaVacuum  # noqa: E402


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
        self.published: List[Any] = []
        self._subs: Dict[str, List[Callable]] = {}

    def publish(self, thought=None, **kwargs):
        # Accept either a Thought-like object (from persona_action's lazy
        # import) or topic/payload kwargs (fallback path).
        if thought is None:
            topic = kwargs.get("topic", "")
            payload = kwargs.get("payload", {})
            thought = _StubThought(topic, payload)
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
            text = "ok"
            model = "stub"
            usage = {"total_tokens": 1}

        return _R()


class _StubVault:
    """Minimal AureonVault-shaped double for the actuator + vacuum."""

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

    def ingest(self, topic: str, payload: Any):
        self.ingested.append({"topic": topic, "payload": payload})

    def fingerprint(self) -> str:
        return "fp"

    def __len__(self) -> int:
        return 3


# ─────────────────────────────────────────────────────────────────────────────
# PersonaAction dataclass
# ─────────────────────────────────────────────────────────────────────────────


def test_persona_action_to_dict_round_trips():
    a = PersonaAction(
        kind="bus.publish",
        topic="t",
        payload={"k": 1},
        target="anywhere",
        reason="why",
        urgency=0.75,
    )
    d = a.to_dict()
    assert d == {
        "kind": "bus.publish",
        "topic": "t",
        "payload": {"k": 1},
        "target": "anywhere",
        "reason": "why",
        "urgency": 0.75,
    }


def test_persona_action_defaults_are_safe():
    a = PersonaAction(kind="x")
    assert a.topic == ""
    assert a.payload == {}
    assert a.target == ""
    assert a.urgency == 0.5


# ─────────────────────────────────────────────────────────────────────────────
# Actuator — dispatch, dry_run, history, unknown kinds
# ─────────────────────────────────────────────────────────────────────────────


def test_dispatch_returns_none_when_action_is_none():
    a = PersonaActuator(thought_bus=_StubBus(), vault=_StubVault())
    assert a.dispatch("x", None) is None


def test_dispatch_dry_run_records_but_does_not_fire_handlers():
    bus = _StubBus()
    vault = _StubVault()
    a = PersonaActuator(thought_bus=bus, vault=vault, dry_run=True)
    action = PersonaAction(kind="bus.publish", topic="dry.topic", payload={"k": 1})
    rec = a.dispatch("mystic", action)
    assert rec is not None
    assert rec.ok is True
    assert rec.dry_run is True
    assert rec.result == {"note": "dry_run — handler not invoked"}
    # Nothing published, nothing ingested
    assert bus.published == []
    assert vault.ingested == []


def test_dispatch_bus_publish_handler_emits_on_bus():
    bus = _StubBus()
    a = PersonaActuator(thought_bus=bus)
    action = PersonaAction(
        kind="bus.publish", topic="persona.intent.rally",
        payload={"energy": 0.9}, reason="hot drop", urgency=0.9,
    )
    rec = a.dispatch("artist", action)
    assert rec is not None and rec.ok is True
    assert len(bus.published) == 1
    assert bus.published[0].topic == "persona.intent.rally"
    assert bus.published[0].payload["energy"] == 0.9
    assert bus.published[0].payload["reason"] == "hot drop"
    assert bus.published[0].payload["urgency"] == 0.9


def test_dispatch_vault_ingest_handler():
    vault = _StubVault()
    a = PersonaActuator(vault=vault)
    action = PersonaAction(kind="vault.ingest", topic="persona.painter.card", payload={"note": "x"})
    rec = a.dispatch("painter", action)
    assert rec is not None and rec.ok is True
    assert vault.ingested == [{"topic": "persona.painter.card", "payload": {"note": "x"}}]


def test_dispatch_file_append_handler(tmp_path: Path):
    a = PersonaActuator(file_root=str(tmp_path))
    action = PersonaAction(
        kind="file.append", target="trails/elder.jsonl",
        payload={"recurrence": True}, reason="theta up", urgency=0.6,
    )
    rec = a.dispatch("elder", action)
    assert rec is not None and rec.ok is True
    path = tmp_path / "trails" / "elder.jsonl"
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "recurrence" in content
    assert "theta up" in content
    # Second append lands on a new line
    a.dispatch("elder", action)
    lines = path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2


def test_dispatch_skill_request_publishes_author_topic():
    bus = _StubBus()
    a = PersonaActuator(thought_bus=bus)
    action = PersonaAction(
        kind="skill.request",
        topic="coherence_audit_skill",
        payload={"params": [1, 2]},
        reason="Engineer saw clean gate",
    )
    rec = a.dispatch("engineer", action, state={"persona": "engineer"})
    assert rec is not None and rec.ok is True
    assert bus.published[-1].topic == "skill.author.request"
    assert bus.published[-1].payload["brief"] == "coherence_audit_skill"
    assert bus.published[-1].payload["requested_by_persona"] == "engineer"


def test_dispatch_unknown_kind_records_error_no_raise():
    a = PersonaActuator(thought_bus=_StubBus())
    action = PersonaAction(kind="not.a.real.kind", topic="x")
    rec = a.dispatch("p", action)
    assert rec is not None
    assert rec.ok is False
    assert "no handler registered" in rec.error


def test_dispatch_handler_exception_is_captured():
    a = PersonaActuator(thought_bus=_StubBus())

    def bad(action, state):
        raise RuntimeError("boom")

    a.register("bad", bad)
    rec = a.dispatch("p", PersonaAction(kind="bad"))
    assert rec is not None
    assert rec.ok is False
    assert "boom" in rec.error


def test_history_respects_maxlen():
    a = PersonaActuator(thought_bus=_StubBus(), history_size=5)
    for i in range(20):
        a.dispatch("p", PersonaAction(kind="bus.publish", topic=f"t.{i}"))
    hist = a.history(n=100)
    assert len(hist) == 5
    # Only the last 5 survive
    topics = [h["action"]["topic"] for h in hist]
    assert topics == [f"t.{i}" for i in range(15, 20)]


def test_actuator_is_thread_safe_under_concurrent_dispatch():
    a = PersonaActuator(thought_bus=_StubBus(), history_size=1000)
    errors: List[Exception] = []
    err_lock = threading.Lock()

    def worker(tid: int) -> None:
        try:
            for i in range(200):
                a.dispatch(f"p{tid}", PersonaAction(kind="bus.publish", topic=f"t.{tid}.{i}"))
        except Exception as e:
            with err_lock:
                errors.append(e)

    threads = [threading.Thread(target=worker, args=(i,), daemon=True) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []
    assert len(a.history(n=10_000)) == 800


# ─────────────────────────────────────────────────────────────────────────────
# Per-persona trigger matrix
# ─────────────────────────────────────────────────────────────────────────────


def _hot_state_for(name: str) -> Dict[str, Any]:
    base: Dict[str, Any] = {
        "love_amplitude": 0.5, "gratitude_score": 0.5, "last_casimir_force": 0.0,
        "last_lambda_t": 0.0, "dominant_chakra": "solar", "dominant_frequency_hz": 300.0,
        "rally_active": False, "vault_size": 50,
        "cortex": {"delta": 0.1, "theta": 0.1, "alpha": 0.1, "beta": 0.1, "gamma": 0.1},
        "consciousness_psi": 0.2, "coherence_gamma": 0.2, "consciousness_level": "",
        "confidence": 0.2, "node_readings": {}, "dj_drop": {},
    }
    if name == "painter":
        base.update({"dominant_chakra": "heart", "love_amplitude": 0.9})
    elif name == "artist":
        base.update({"dj_drop": {"energy": 0.9, "bpm": 128.0}, "rally_active": True})
    elif name == "quantum_physicist":
        base.update({"last_lambda_t": 1.5, "consciousness_psi": 0.9})
    elif name == "philosopher":
        base.update({"consciousness_level": "DAWNING"})
    elif name == "child":
        base.update({"vault_size": 3, "cortex": {**base["cortex"], "delta": 0.85}})
    elif name == "elder":
        base.update({"consciousness_psi": 0.9,
                     "cortex": {**base["cortex"], "theta": 0.85}})
    elif name == "mystic":
        base.update({"love_amplitude": 0.95, "dominant_frequency_hz": 528.0})
    elif name == "engineer":
        base.update({"coherence_gamma": 0.95, "node_readings": {"tiger": 0.9}})
    elif name == "left":
        base.update({"node_readings": {"falcon": 0.95}, "confidence": 0.9})
    elif name == "right":
        base.update({"node_readings": {"dolphin": 0.9, "panda": 0.9}})
    return base


_EXPECTED: Dict[str, Dict[str, str]] = {
    "painter":          {"kind": "vault.ingest",  "topic": "persona.painter.composition"},
    "artist":           {"kind": "bus.publish",   "topic": "persona.intent.rally"},
    "quantum_physicist":{"kind": "bus.publish",   "topic": "auris.throne.alert"},
    "philosopher":      {"kind": "bus.publish",   "topic": "queen.request_cognition"},
    "child":            {"kind": "vault.ingest",  "topic": "persona.child.curiosity"},
    "elder":            {"kind": "vault.ingest",  "topic": "persona.elder.recurrence"},
    "mystic":           {"kind": "bus.publish",   "topic": "love.stream.528hz"},
    "engineer":         {"kind": "bus.publish",   "topic": "queen.request_cognition"},
    "left":             {"kind": "bus.publish",   "topic": "persona.intent.velocity_alert"},
    "right":            {"kind": "vault.ingest",  "topic": "persona.right.field"},
}


@pytest.mark.parametrize("name", list(_EXPECTED.keys()))
def test_each_persona_fires_expected_action_on_hot_state(name: str):
    cls = AUREON_PERSONA_REGISTRY[name]
    persona = cls(adapter=_StubAdapter())
    state = _hot_state_for(name)
    action = persona.propose_action(state)
    assert action is not None, f"{name} returned None on hot state"
    assert action.kind == _EXPECTED[name]["kind"]
    assert action.topic == _EXPECTED[name]["topic"]
    assert 0.0 <= action.urgency <= 1.0


@pytest.mark.parametrize("name", list(_EXPECTED.keys()))
def test_each_persona_returns_none_on_cold_state(name: str):
    cls = AUREON_PERSONA_REGISTRY[name]
    persona = cls(adapter=_StubAdapter())
    # Cold base state — nothing elevated.
    cold = {
        "love_amplitude": 0.1, "gratitude_score": 0.1, "last_lambda_t": 0.0,
        "dominant_chakra": "root", "dominant_frequency_hz": 100.0, "rally_active": False,
        "vault_size": 100, "cortex": {"delta": 0.05, "theta": 0.05, "alpha": 0.05, "beta": 0.05, "gamma": 0.05},
        "consciousness_psi": 0.05, "coherence_gamma": 0.05, "consciousness_level": "DORMANT",
        "confidence": 0.05, "node_readings": {"tiger": 0.1, "falcon": 0.1, "dolphin": 0.1, "panda": 0.1},
        "dj_drop": {},
    }
    assert persona.propose_action(cold) is None


def test_base_resonant_persona_returns_none():
    # The base class default must be None so custom subclasses stay safe.
    assert ResonantPersona.propose_action(ResonantPersona(adapter=_StubAdapter()), {}) is None


# ─────────────────────────────────────────────────────────────────────────────
# PersonaVacuum ↔ Actuator integration
# ─────────────────────────────────────────────────────────────────────────────


def test_vacuum_dispatches_action_after_collapse():
    bus = _StubBus()
    vault = _StubVault()
    from aureon.vault.voice.aureon_personas import build_aureon_personas
    vacuum = PersonaVacuum(
        personas=build_aureon_personas(adapter=_StubAdapter()),
        thought_bus=bus,
        rng=random.Random(0),
        vault=vault,
    )
    # Seed cognition so Engineer's state lights up.
    bus.publish(_StubThought("queen.source_law.cognition", {
        "coherence_gamma": 0.96, "node_readings": {"tiger": 0.9},
    }))
    bus.subscribe("queen.source_law.cognition", vacuum._on_cognition)
    bus.publish(_StubThought("queen.source_law.cognition", {
        "coherence_gamma": 0.96, "node_readings": {"tiger": 0.9},
    }))
    # Force the winner by handing a rigged RNG that picks the first persona
    # whose affinity we've already biased. Easier: stub compute_affinity so
    # Engineer dominates.
    for name, p in vacuum._personas.items():
        p.compute_affinity = (lambda s, n=name: 1000.0 if n == "engineer" else 0.01)
    stmt = vacuum.observe(vault)
    assert vacuum.last_winner == "engineer"
    exec_rec = vacuum.last_action_execution
    assert exec_rec is not None
    assert exec_rec.ok is True
    assert exec_rec.action.kind == "bus.publish"
    assert exec_rec.action.topic == "queen.request_cognition"
    # The bus saw the actuator publish
    topics = [t.topic for t in bus.published]
    assert "queen.request_cognition" in topics


def test_vacuum_dry_run_mode_does_not_fire_handlers():
    bus = _StubBus()
    vault = _StubVault()
    from aureon.vault.voice.aureon_personas import build_aureon_personas
    vacuum = PersonaVacuum(
        personas=build_aureon_personas(adapter=_StubAdapter()),
        thought_bus=bus,
        rng=random.Random(0),
        vault=vault,
        actuator_dry_run=True,
    )
    bus.publish(_StubThought("queen.source_law.cognition", {
        "coherence_gamma": 0.96, "node_readings": {"tiger": 0.9},
    }))
    bus.subscribe("queen.source_law.cognition", vacuum._on_cognition)
    bus.publish(_StubThought("queen.source_law.cognition", {
        "coherence_gamma": 0.96, "node_readings": {"tiger": 0.9},
    }))
    for name, p in vacuum._personas.items():
        p.compute_affinity = (lambda s, n=name: 1000.0 if n == "engineer" else 0.01)
    # Count only actuator-generated publishes (exclude the cognition seeds
    # we did above).
    before = len([t for t in bus.published if t.topic == "queen.request_cognition"])
    vacuum.observe(vault)
    after = len([t for t in bus.published if t.topic == "queen.request_cognition"])
    assert after == before  # dry_run blocked the publish
    rec = vacuum.last_action_execution
    assert rec is not None and rec.dry_run is True and rec.ok is True


def test_vacuum_no_action_when_persona_is_silent():
    bus = _StubBus()
    vault = _StubVault()
    from aureon.vault.voice.aureon_personas import build_aureon_personas
    vacuum = PersonaVacuum(
        personas=build_aureon_personas(adapter=_StubAdapter()),
        thought_bus=bus,
        rng=random.Random(1),
        vault=vault,
    )
    # No hot cognition; winner's propose_action should return None.
    for name, p in vacuum._personas.items():
        # Force Child winner — Child needs small vault + not-rally to fire.
        p.compute_affinity = (lambda s, n=name: 1000.0 if n == "child" else 0.01)

    # Build a cold Child state: big vault, no high delta.
    class _BigVault(_StubVault):
        def __len__(self):
            return 500
    big = _BigVault()
    big.cortex_snapshot = {"delta": 0.05}
    vacuum.observe(big)
    assert vacuum.last_winner == "child"
    # Child requires size < 20 OR delta > 0.6 — neither is true, so no action.
    assert vacuum.last_action_execution is None


def test_vacuum_actuator_end_to_end_against_real_vault():
    """One full collapse should land a VaultContent card in a real AureonVault
    via the actuator's vault.ingest handler."""
    bus = _StubBus()
    vault = AureonVault()
    from aureon.vault.voice.aureon_personas import build_aureon_personas
    vacuum = PersonaVacuum(
        personas=build_aureon_personas(adapter=_StubAdapter()),
        thought_bus=bus,
        rng=random.Random(7),
        vault=vault,
    )
    # Force Painter with a heart-chakra hot state
    for name, p in vacuum._personas.items():
        p.compute_affinity = (lambda s, n=name: 1000.0 if n == "painter" else 0.01)

    class _PainterVault(AureonVault):
        pass
    pv = _PainterVault()
    pv.love_amplitude = 0.9
    pv.dominant_chakra = "heart"
    pv.cortex_snapshot = {"gamma": 0.5}
    cards_before = len(pv)
    vacuum.observe(pv)
    assert vacuum.last_winner == "painter"
    # Two cards land: the statement feedback (persona.thought) and the
    # actuator's vault.ingest for the Painter's composition.
    assert len(pv) == cards_before + 2
    topics = [c.source_topic for c in pv._contents.values()]
    assert "persona.thought" in topics
    assert "persona.painter.composition" in topics


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
