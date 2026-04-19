#!/usr/bin/env python3
"""
Tests for MetaCognitionObserver — α tanh(g Λ_Δt(t)) made observable.

What's being proved:
  - WATCHED_TOPICS subscribed once on start()
  - persona.collapse opens a window; downstream events accumulate;
    window closes after window_s
  - Decision classification:
      goal.submit.request inside window → decision="goal.submit"
      only persona.thought              → decision="speech"
      neither                            → decision="silence"
  - Outcome classification:
      goal.completed inside window → COMPLETED
      goal.abandoned                → ABANDONED
      goal.echo.orphaned            → ORPHANED
      none of the above             → SILENT
      VETO verdict + no completion  → ABANDONED
  - SLS delta computed from before/after symbolic.life.pulse readings
  - Bond count + strength pulled from HashResonanceIndex when attached
  - Reflection cards published on meta.reflection
  - Vault ingests meta.reflection cards
  - QueenMetacognition.ingest_external_reflection is called when wired
  - Narrative includes persona, decision, outcome, SLS delta, bond
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

from aureon.core.aureon_thought_bus import Thought, ThoughtBus  # noqa: E402
from aureon.vault.aureon_vault import AureonVault  # noqa: E402
from aureon.vault.voice.hash_resonance_index import HashResonanceIndex  # noqa: E402
from aureon.vault.voice.meta_cognition_observer import (  # noqa: E402
    MetaCognitionObserver,
    ReflectionCard,
)


# ─────────────────────────────────────────────────────────────────────────────
# Stubs / helpers
# ─────────────────────────────────────────────────────────────────────────────


def _build(**overrides):
    bus = overrides.pop("bus", None) or ThoughtBus()
    vault = overrides.pop("vault", None) or AureonVault()
    vault._thought_bus = bus
    obs = MetaCognitionObserver(thought_bus=bus, vault=vault, **overrides)
    obs.start()
    return obs, bus, vault


def _collapse(bus, persona="engineer", winning_p=0.9):
    bus.publish(Thought(source="pv", topic="persona.collapse",
                         payload={"winner": persona,
                                  "probabilities": {persona: winning_p}}))


# ─────────────────────────────────────────────────────────────────────────────
# Subscription + window mechanics
# ─────────────────────────────────────────────────────────────────────────────


def test_observer_subscribes_to_all_watched_topics():
    obs, bus, _ = _build(window_s=0.2)
    for topic in MetaCognitionObserver.WATCHED_TOPICS:
        assert topic in bus._subs, f"missing subscription for {topic}"


def test_collapse_opens_window():
    obs, bus, _ = _build(window_s=0.5)
    _collapse(bus)
    assert obs.open_window_count == 1


def test_window_closes_after_duration():
    obs, bus, _ = _build(window_s=0.05)
    _collapse(bus)
    time.sleep(0.15)
    obs.close_expired()
    assert obs.open_window_count == 0
    assert len(obs.closed_cards) == 1


def test_multiple_collapses_open_multiple_windows():
    obs, bus, _ = _build(window_s=0.5)
    for _ in range(3):
        _collapse(bus)
    assert obs.open_window_count == 3


# ─────────────────────────────────────────────────────────────────────────────
# Decision classification
# ─────────────────────────────────────────────────────────────────────────────


def test_decision_silence_when_no_downstream():
    obs, bus, _ = _build(window_s=0.05)
    _collapse(bus)
    time.sleep(0.1)
    obs.close_expired()
    card = obs.closed_cards[-1]
    assert card.decision == "silence"
    assert card.outcome == "SILENT"


def test_decision_speech_with_only_persona_thought():
    obs, bus, _ = _build(window_s=0.05)
    _collapse(bus)
    bus.publish(Thought(source="pv", topic="persona.thought",
                         payload={"voice": "engineer", "text": "."}))
    time.sleep(0.1)
    obs.close_expired()
    card = obs.closed_cards[-1]
    assert card.decision == "speech"


def test_decision_goal_submit_when_request_appears():
    obs, bus, _ = _build(window_s=0.05)
    _collapse(bus)
    bus.publish(Thought(source="pa", topic="goal.submit.request",
                         payload={"goal_id": "g1", "text": "do X"}))
    time.sleep(0.1)
    obs.close_expired()
    card = obs.closed_cards[-1]
    assert card.decision == "goal.submit"
    assert card.action_topic == "goal.submit.request"


# ─────────────────────────────────────────────────────────────────────────────
# Outcome classification
# ─────────────────────────────────────────────────────────────────────────────


def test_outcome_completed():
    obs, bus, _ = _build(window_s=0.05)
    _collapse(bus)
    bus.publish(Thought(source="pa", topic="goal.submit.request",
                         payload={"goal_id": "g1", "text": "X"}))
    bus.publish(Thought(source="e", topic="goal.completed",
                         payload={"goal_id": "g1"}))
    time.sleep(0.1)
    obs.close_expired()
    assert obs.closed_cards[-1].outcome == "COMPLETED"


def test_outcome_abandoned():
    obs, bus, _ = _build(window_s=0.05)
    _collapse(bus)
    bus.publish(Thought(source="pa", topic="goal.submit.request",
                         payload={"goal_id": "g1", "text": "X"}))
    bus.publish(Thought(source="e", topic="goal.abandoned",
                         payload={"goal_id": "g1", "reason": "stopped"}))
    time.sleep(0.1)
    obs.close_expired()
    assert obs.closed_cards[-1].outcome == "ABANDONED"


def test_outcome_orphaned():
    obs, bus, _ = _build(window_s=0.05)
    _collapse(bus)
    bus.publish(Thought(source="pa", topic="goal.submit.request",
                         payload={"goal_id": "g1", "text": "X"}))
    bus.publish(Thought(source="law", topic="goal.echo.orphaned",
                         payload={"goal_id": "g1"}))
    time.sleep(0.1)
    obs.close_expired()
    assert obs.closed_cards[-1].outcome == "ORPHANED"


def test_completed_beats_abandoned():
    """If both arrive in the window, COMPLETED wins."""
    obs, bus, _ = _build(window_s=0.05)
    _collapse(bus)
    bus.publish(Thought(source="pa", topic="goal.submit.request",
                         payload={"goal_id": "g1", "text": "X"}))
    bus.publish(Thought(source="e", topic="goal.completed",
                         payload={"goal_id": "g1"}))
    bus.publish(Thought(source="e", topic="goal.abandoned",
                         payload={"goal_id": "g1"}))
    time.sleep(0.1)
    obs.close_expired()
    assert obs.closed_cards[-1].outcome == "COMPLETED"


def test_veto_with_no_completion_marks_abandoned():
    obs, bus, _ = _build(window_s=0.05)
    _collapse(bus)
    bus.publish(Thought(source="pa", topic="goal.submit.request",
                         payload={"goal_id": "g1", "text": "X"}))
    bus.publish(Thought(source="qc", topic="queen.conscience.verdict",
                         payload={"action": "X", "verdict": "ConscienceVerdict.VETO"}))
    time.sleep(0.1)
    obs.close_expired()
    assert obs.closed_cards[-1].outcome == "ABANDONED"


# ─────────────────────────────────────────────────────────────────────────────
# SLS delta
# ─────────────────────────────────────────────────────────────────────────────


def test_sls_delta_computed_from_before_and_after():
    obs, bus, _ = _build(window_s=0.05)
    bus.publish(Thought(source="slb", topic="symbolic.life.pulse",
                         payload={"symbolic_life_score": 0.40}))
    _collapse(bus)
    bus.publish(Thought(source="slb", topic="symbolic.life.pulse",
                         payload={"symbolic_life_score": 0.55}))
    time.sleep(0.1)
    obs.close_expired()
    card = obs.closed_cards[-1]
    assert card.sls_before == 0.40
    assert card.sls_after == 0.55
    assert abs(card.sls_delta - 0.15) < 1e-9


def test_sls_unknown_when_no_pulse_seen():
    obs, bus, _ = _build(window_s=0.05)
    _collapse(bus)
    time.sleep(0.1)
    obs.close_expired()
    card = obs.closed_cards[-1]
    assert card.sls_before is None
    assert card.sls_after is None
    assert card.sls_delta == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Bond integration
# ─────────────────────────────────────────────────────────────────────────────


def test_bond_count_pulled_from_hash_resonance_index():
    bus = ThoughtBus()
    vault = AureonVault()
    vault._thought_bus = bus
    hri = HashResonanceIndex(vault=vault, thought_bus=bus, thresholds=[2])
    hri.start()
    obs = MetaCognitionObserver(thought_bus=bus, vault=vault,
                                hash_resonance_index=hri, window_s=0.05)
    obs.start()
    # Three identical-semantic goals
    for _ in range(3):
        c = vault.ingest("goal.submit.request",
                         {"goal_id": f"g{time.time()}",
                          "text": "shared goal", "proposed_by_persona": "engineer"})
    # Now collapse + observer sees the latest goal in window
    _collapse(bus)
    bus.publish(Thought(source="pa", topic="goal.submit.request",
                         payload={"goal_id": "fresh",
                                  "text": "shared goal",
                                  "proposed_by_persona": "engineer"}))
    # Vault must have a card for the bus event so HRI can resolve fp
    vault.ingest("goal.submit.request",
                 {"goal_id": "fresh", "text": "shared goal",
                  "proposed_by_persona": "engineer"})
    time.sleep(0.1)
    obs.close_expired()
    card = obs.closed_cards[-1]
    assert card.bond_count >= 3
    assert card.bond_strength > 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Publication + vault ingest
# ─────────────────────────────────────────────────────────────────────────────


def test_meta_reflection_published_on_bus():
    obs, bus, _ = _build(window_s=0.05)
    received: List[Thought] = []
    bus.subscribe("meta.reflection", lambda t: received.append(t))
    _collapse(bus)
    time.sleep(0.1)
    obs.close_expired()
    assert len(received) == 1
    payload = received[0].payload
    for key in ("reflection_id", "collapse_ts", "closed_ts", "persona",
                "decision", "outcome", "window_s", "lambda_delta_t",
                "reasoning"):
        assert key in payload


def test_vault_receives_meta_reflection_card():
    obs, bus, vault = _build(window_s=0.05)
    _collapse(bus)
    time.sleep(0.1)
    obs.close_expired()
    cards = [c for c in vault._contents.values()
             if c.source_topic == "meta.reflection"]
    assert len(cards) == 1
    assert cards[0].category == "meta_reflection"


# ─────────────────────────────────────────────────────────────────────────────
# QueenMetacognition feed
# ─────────────────────────────────────────────────────────────────────────────


class _SpyQueenMetacog:
    def __init__(self):
        self.calls: List[Dict[str, Any]] = []

    def ingest_external_reflection(self, card: Dict[str, Any]):
        self.calls.append(card)


def test_feeds_queen_metacognition_when_attached():
    bus = ThoughtBus()
    vault = AureonVault()
    vault._thought_bus = bus
    spy = _SpyQueenMetacog()
    obs = MetaCognitionObserver(thought_bus=bus, vault=vault,
                                queen_metacognition=spy, window_s=0.05)
    obs.start()
    _collapse(bus)
    time.sleep(0.1)
    obs.close_expired()
    assert len(spy.calls) == 1
    assert "persona" in spy.calls[0]
    assert "outcome" in spy.calls[0]


def test_no_queen_metacognition_does_not_break():
    obs, bus, _ = _build(window_s=0.05)
    _collapse(bus)
    time.sleep(0.1)
    obs.close_expired()
    # No exception means we're good.
    assert len(obs.closed_cards) == 1


# ─────────────────────────────────────────────────────────────────────────────
# Narrative
# ─────────────────────────────────────────────────────────────────────────────


def test_narrative_mentions_persona_decision_outcome():
    obs, bus, _ = _build(window_s=0.05)
    bus.publish(Thought(source="slb", topic="symbolic.life.pulse",
                         payload={"symbolic_life_score": 0.5}))
    _collapse(bus, persona="mystic")
    bus.publish(Thought(source="pa", topic="goal.submit.request",
                         payload={"goal_id": "g1", "text": "X"}))
    bus.publish(Thought(source="e", topic="goal.completed",
                         payload={"goal_id": "g1"}))
    bus.publish(Thought(source="slb", topic="symbolic.life.pulse",
                         payload={"symbolic_life_score": 0.6}))
    time.sleep(0.1)
    obs.close_expired()
    text = obs.closed_cards[-1].reasoning
    assert "mystic" in text
    assert "goal.submit" in text
    assert "COMPLETED" in text
    assert "0.500" in text  # SLS before
    assert "0.600" in text  # SLS after


# ─────────────────────────────────────────────────────────────────────────────
# Real QueenMetacognition.ingest_external_reflection extension
# ─────────────────────────────────────────────────────────────────────────────


def test_queen_metacognition_has_ingest_external_reflection():
    """Stage 6.5 added the entry point. Sanity check: the method exists
    and doesn't raise on a minimal card."""
    try:
        from aureon.queen.queen_metacognition import QueenMetacognition
    except Exception:
        pytest.skip("queen_metacognition not importable in this env")
    qmc = QueenMetacognition()
    assert hasattr(qmc, "ingest_external_reflection")
    qmc.ingest_external_reflection({
        "persona": "engineer",
        "decision": "goal.submit",
        "outcome": "COMPLETED",
        "sls_after": 0.6,
        "sls_delta": 0.05,
        "bond_count": 1,
        "reasoning": "test",
        "closed_ts": time.time(),
    })


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
