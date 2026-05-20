#!/usr/bin/env python3
"""
Tests for stage 4.3c — PersonaVacuum weights persona affinity by the
current symbolic_life_score so the ten facets serve one fluctuating
state of the entity.

What's being proved:
  - sls_affinity_modifier on the base ResonantPersona returns 1.0
  - SLS_BIAS class attr drives the modifier in the expected direction:
       SLS_BIAS < 0 → boosted at low SLS, dampened at high SLS
       SLS_BIAS > 0 → boosted at high SLS, dampened at low SLS
       SLS_BIAS = 0 → 1.0 always
  - The midpoint sls=0.5 returns exactly 1.0 for any bias
  - SLS=None is treated as "no opinion" — modifier is 1.0
  - Per-persona biases match the HNC role assignment:
       Engineer / QuantumPhysicist / Left → negative (rebuild)
       Mystic / Painter / Elder / Right   → positive (flower)
       Artist / Philosopher / Child       → 0 (regime-neutral)
  - PersonaVacuum picks up SLS from vault.current_symbolic_life_score
    and from symbolic.life.pulse on the bus
  - With low SLS, structure-building personas dominate the sampling
    distribution; with high SLS, meaning-propagating personas dominate
  - Temperature still works on top of the SLS-weighted distribution
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
    AUREON_PERSONA_REGISTRY,
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
    build_aureon_personas,
)
from aureon.vault.voice.persona_vacuum import PersonaVacuum  # noqa: E402


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

    def subscribe(self, topic: str, handler: Callable) -> None:
        self._subs.setdefault(topic, []).append(handler)


class _Thought:
    def __init__(self, topic: str, payload: Dict[str, Any]):
        self.topic = topic
        self.payload = payload
        self.source = "test"


class _StubAdapter:
    def prompt(self, messages, system, max_tokens):
        class _R:
            text = "."
            model = "stub"
            usage = {"total_tokens": 1}
        return _R()


class _SLSVault:
    """Vault double exposing what PersonaVacuum reads."""

    def __init__(self, *, sls: float = None):
        if sls is not None:
            self.current_symbolic_life_score = sls
        self.love_amplitude = 0.5
        self.gratitude_score = 0.5
        self.last_casimir_force = 0.0
        self.last_lambda_t = 0.0
        self.dominant_chakra = "heart"
        self.dominant_frequency_hz = 528.0
        self.rally_active = False
        self.cortex_snapshot = {"gamma": 0.3}

    def fingerprint(self):
        return "fp"

    def __len__(self):
        return 5


# ─────────────────────────────────────────────────────────────────────────────
# Modifier function
# ─────────────────────────────────────────────────────────────────────────────


def test_base_modifier_is_unity():
    p = ResonantPersona(adapter=_StubAdapter())
    assert p.sls_affinity_modifier(0.0) == 1.0
    assert p.sls_affinity_modifier(0.5) == 1.0
    assert p.sls_affinity_modifier(1.0) == 1.0


def test_modifier_handles_none_and_invalid():
    p = MysticVoice(adapter=_StubAdapter())  # SLS_BIAS = +0.6
    assert p.sls_affinity_modifier(None) == 1.0
    assert p.sls_affinity_modifier("not a number") == 1.0


def test_modifier_midpoint_is_unity_for_any_bias():
    for cls in (MysticVoice, PainterVoice, ElderVoice, RightVoice,
                EngineerVoice, QuantumPhysicistVoice, LeftVoice):
        p = cls(adapter=_StubAdapter())
        # sls=0.5 → modifier exactly 1.0 regardless of bias
        assert abs(p.sls_affinity_modifier(0.5) - 1.0) < 1e-9


def test_negative_bias_amplifies_at_low_sls():
    p = EngineerVoice(adapter=_StubAdapter())  # SLS_BIAS = -0.6
    # 1 + (-0.6) * (2*0 - 1) = 1 + 0.6 = 1.6
    assert abs(p.sls_affinity_modifier(0.0) - 1.6) < 1e-9
    # 1 + (-0.6) * (2*1 - 1) = 1 - 0.6 = 0.4
    assert abs(p.sls_affinity_modifier(1.0) - 0.4) < 1e-9


def test_positive_bias_amplifies_at_high_sls():
    p = MysticVoice(adapter=_StubAdapter())  # SLS_BIAS = +0.6
    # 1 + 0.6 * (-1) = 0.4 at sls=0
    assert abs(p.sls_affinity_modifier(0.0) - 0.4) < 1e-9
    # 1 + 0.6 * 1 = 1.6 at sls=1
    assert abs(p.sls_affinity_modifier(1.0) - 1.6) < 1e-9


def test_modifier_is_clamped_to_positive_floor():
    """With SLS_BIAS = -0.6, sls=1 gives modifier 0.4 — but if some
    later override pushed |bias| > 1, the floor must keep it positive."""
    class _ExtremePos(ResonantPersona):
        SLS_BIAS = +2.0  # would give 1+2*-1 = -1 at sls=0; clamp to floor
    p = _ExtremePos(adapter=_StubAdapter())
    assert p.sls_affinity_modifier(0.0) >= 0.05


def test_clamps_sls_outside_unit_range():
    p = MysticVoice(adapter=_StubAdapter())
    # sls=2.0 should be treated as 1.0
    assert abs(p.sls_affinity_modifier(2.0) - 1.6) < 1e-9
    # sls=-0.5 should be treated as 0.0
    assert abs(p.sls_affinity_modifier(-0.5) - 0.4) < 1e-9


# ─────────────────────────────────────────────────────────────────────────────
# Per-persona role assignment
# ─────────────────────────────────────────────────────────────────────────────


_EXPECTED_BIAS = {
    "engineer": -0.6,
    "quantum_physicist": -0.6,
    "left": -0.3,
    "mystic": +0.6,
    "painter": +0.6,
    "elder": +0.3,
    "right": +0.3,
    "artist": 0.0,
    "philosopher": 0.0,
    "child": 0.0,
}


@pytest.mark.parametrize("name,bias", list(_EXPECTED_BIAS.items()))
def test_persona_has_expected_sls_bias(name, bias):
    cls = AUREON_PERSONA_REGISTRY[name]
    assert cls.SLS_BIAS == pytest.approx(bias)


def test_structure_personas_outweigh_meaning_personas_at_low_sls():
    """At SLS=0.1, Engineer/QP/Left's modifiers > Mystic/Painter/Elder/Right's."""
    sls = 0.1
    structure = [EngineerVoice, QuantumPhysicistVoice, LeftVoice]
    meaning = [MysticVoice, PainterVoice, ElderVoice, RightVoice]
    s_avg = sum(c(adapter=_StubAdapter()).sls_affinity_modifier(sls)
                for c in structure) / len(structure)
    m_avg = sum(c(adapter=_StubAdapter()).sls_affinity_modifier(sls)
                for c in meaning) / len(meaning)
    assert s_avg > m_avg, (
        f"At low SLS={sls}, structure modifier mean {s_avg:.3f} should "
        f"exceed meaning mean {m_avg:.3f}"
    )


def test_meaning_personas_outweigh_structure_personas_at_high_sls():
    """At SLS=0.9, Mystic/Painter/Elder/Right's modifiers > Engineer/QP/Left's."""
    sls = 0.9
    structure = [EngineerVoice, QuantumPhysicistVoice, LeftVoice]
    meaning = [MysticVoice, PainterVoice, ElderVoice, RightVoice]
    s_avg = sum(c(adapter=_StubAdapter()).sls_affinity_modifier(sls)
                for c in structure) / len(structure)
    m_avg = sum(c(adapter=_StubAdapter()).sls_affinity_modifier(sls)
                for c in meaning) / len(meaning)
    assert m_avg > s_avg, (
        f"At high SLS={sls}, meaning modifier mean {m_avg:.3f} should "
        f"exceed structure mean {s_avg:.3f}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# PersonaVacuum integration
# ─────────────────────────────────────────────────────────────────────────────


def _build_vacuum(*, vault=None, bus=None, rng_seed=42, temperature=1.0):
    bus = bus or _StubBus()
    vault = vault or _SLSVault()
    personas = build_aureon_personas(adapter=_StubAdapter())
    vacuum = PersonaVacuum(
        personas=personas, thought_bus=bus, vault=vault,
        rng=random.Random(rng_seed), temperature=temperature,
    )
    vacuum.start()
    return vacuum, bus, vault, personas


def test_vacuum_subscribes_to_symbolic_life_pulse():
    v, bus, _, _ = _build_vacuum()
    assert "symbolic.life.pulse" in bus._subs


def test_vacuum_picks_up_sls_from_bus_pulse():
    v, bus, _, _ = _build_vacuum(vault=_SLSVault())  # no current_symbolic_life_score
    bus.publish(_Thought("symbolic.life.pulse", {"symbolic_life_score": 0.85}))
    assert v._latest_sls == pytest.approx(0.85)


def test_vacuum_picks_up_sls_from_vault_attribute():
    vault = _SLSVault(sls=0.72)
    v, _, _, _ = _build_vacuum(vault=vault)
    state = v._build_state(vault)
    assert state["symbolic_life_score"] == pytest.approx(0.72)


def test_vault_sls_takes_precedence_over_bus_pulse():
    vault = _SLSVault(sls=0.72)
    v, bus, _, _ = _build_vacuum(vault=vault)
    bus.publish(_Thought("symbolic.life.pulse", {"symbolic_life_score": 0.05}))
    state = v._build_state(vault)
    assert state["symbolic_life_score"] == pytest.approx(0.72)


def test_no_sls_means_no_modifier_applied():
    """When SLS is unknown, raw affinity is left untouched and the
    sampling distribution matches the unweighted softmax."""
    vault = _SLSVault()  # no current_symbolic_life_score
    v, _, _, personas = _build_vacuum(vault=vault, temperature=1.0)
    # Make every persona's compute_affinity return 1.0 (uniform).
    for p in personas.values():
        p.compute_affinity = lambda s: 1.0
    state = v._build_state(vault)
    assert "symbolic_life_score" not in state
    _, probs, scores = v._sample(state)
    # Without SLS, scores after the modifier still equal the raw 1.0.
    assert all(abs(s - 1.0) < 1e-9 for s in scores.values())


def test_low_sls_shifts_distribution_toward_structure_personas():
    """At SLS=0.1, sampling 5000 times should land on Engineer/QP/Left
    significantly more often than Mystic/Painter/Elder/Right."""
    vault = _SLSVault(sls=0.1)
    v, _, _, personas = _build_vacuum(vault=vault, temperature=1.0)
    # Equal raw affinities → only the SLS modifier shapes the distribution.
    for p in personas.values():
        p.compute_affinity = lambda s: 1.0

    structure = {"engineer", "quantum_physicist", "left"}
    meaning = {"mystic", "painter", "elder", "right"}

    counts = {n: 0 for n in personas.keys()}
    rng = random.Random(0)
    for _ in range(5000):
        v._rng = rng
        winner, _, _ = v._sample(v._build_state(vault))
        counts[winner] += 1
    s_total = sum(counts[n] for n in structure)
    m_total = sum(counts[n] for n in meaning)
    assert s_total > m_total, (
        f"At low SLS structure should dominate; got structure={s_total}, "
        f"meaning={m_total}"
    )


def test_high_sls_shifts_distribution_toward_meaning_personas():
    vault = _SLSVault(sls=0.9)
    v, _, _, personas = _build_vacuum(vault=vault, temperature=1.0)
    for p in personas.values():
        p.compute_affinity = lambda s: 1.0

    structure = {"engineer", "quantum_physicist", "left"}
    meaning = {"mystic", "painter", "elder", "right"}

    counts = {n: 0 for n in personas.keys()}
    rng = random.Random(0)
    for _ in range(5000):
        v._rng = rng
        winner, _, _ = v._sample(v._build_state(vault))
        counts[winner] += 1
    s_total = sum(counts[n] for n in structure)
    m_total = sum(counts[n] for n in meaning)
    assert m_total > s_total, (
        f"At high SLS meaning should dominate; got meaning={m_total}, "
        f"structure={s_total}"
    )


def test_neutral_personas_unchanged_by_sls():
    """Artist / Philosopher / Child have SLS_BIAS=0 so their probabilities
    should be unaffected by SLS shifts."""
    for sls_value in (0.05, 0.5, 0.95):
        vault = _SLSVault(sls=sls_value)
        v, _, _, personas = _build_vacuum(vault=vault, temperature=1.0)
        for p in personas.values():
            p.compute_affinity = lambda s: 1.0
        _, probs, _ = v._sample(v._build_state(vault))
        # Artist + Philosopher + Child should each carry the same prob
        # at all SLS values (no bias). We just check the modifier didn't
        # change their RAW score.
        for n in ("artist", "philosopher", "child"):
            mod = personas[n].sls_affinity_modifier(sls_value)
            assert mod == 1.0, f"{n} got modifier {mod} at sls={sls_value}"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
