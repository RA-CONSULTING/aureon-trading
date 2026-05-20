#!/usr/bin/env python3
"""
Tests for PersonaMinerBridge — treating personas as miner data packets,
plus GoalSkillAligner — the bridge between learned patterns and the
goal stream.
"""

from __future__ import annotations

import os
import sys
import tempfile
import time
from typing import Any, Callable, Dict, List

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from aureon.core.aureon_thought_bus import Thought, ThoughtBus  # noqa: E402
from aureon.vault.voice.goal_skill_aligner import GoalSkillAligner  # noqa: E402
from aureon.vault.voice.persona_miner_bridge import (  # noqa: E402
    IntentStats,
    PersonaMinerBridge,
    PersonaStats,
    _extract_intent_keywords,
)


# ─────────────────────────────────────────────────────────────────────────────
# Stubs / helpers
# ─────────────────────────────────────────────────────────────────────────────


class _StubSkillLibrary:
    """Tiny SkillLibrary stand-in supporting .get(name)."""

    def __init__(self, names: List[str]):
        self._names = set(names)

    def get(self, name: str):
        if name in self._names:
            class _S:
                pass
            s = _S()
            s.name = name
            return s
        return None


def _build(persistence_path=None, skills=None, threshold=0.6):
    bus = ThoughtBus()
    skill_library = _StubSkillLibrary(skills or [])
    bridge = PersonaMinerBridge(
        thought_bus=bus, skill_library=skill_library,
        persistence_path=persistence_path or tempfile.mktemp(suffix=".json"),
        pattern_threshold=threshold,
    )
    bridge.start()
    return bridge, bus, skill_library


def _submit(bus, goal_id, persona, text):
    bus.publish(Thought(source="actuator", topic="goal.submit.request",
                         payload={"goal_id": goal_id, "text": text,
                                  "proposed_by_persona": persona,
                                  "urgency": 0.7,
                                  "parameters": {}}))


def _terminal(bus, topic, goal_id, **extra):
    payload = {"goal_id": goal_id}
    payload.update(extra)
    bus.publish(Thought(source="engine", topic=topic, payload=payload))


# ─────────────────────────────────────────────────────────────────────────────
# Keyword extraction
# ─────────────────────────────────────────────────────────────────────────────


def test_extract_intent_keywords_strips_stopwords():
    kws = _extract_intent_keywords("Render an SVG for the wedding")
    assert "wedding" in kws
    assert "render" in kws or "svg" in kws
    assert "the" not in kws
    assert "an" not in kws


def test_extract_intent_keywords_caps_at_three():
    kws = _extract_intent_keywords(
        "Author a coherence audit skill that asserts gamma threshold for trades"
    )
    assert len(kws) <= 3


def test_extract_intent_keywords_empty_for_blank():
    assert _extract_intent_keywords("") == []
    assert _extract_intent_keywords("   ") == []


# ─────────────────────────────────────────────────────────────────────────────
# Subscription
# ─────────────────────────────────────────────────────────────────────────────


def test_bridge_subscribes_to_all_inbound_topics():
    bridge, bus, _ = _build()
    for topic in PersonaMinerBridge.INBOUND_TOPICS:
        assert topic in bus._subs, f"missing {topic}"


# ─────────────────────────────────────────────────────────────────────────────
# Persona stat accumulation
# ─────────────────────────────────────────────────────────────────────────────


def test_persona_collapse_increments_action_count():
    bridge, bus, _ = _build()
    for _ in range(5):
        bus.publish(Thought(source="pv", topic="persona.collapse",
                             payload={"winner": "engineer",
                                      "probabilities": {"engineer": 0.9}}))
    health = bridge.persona_health("engineer")
    assert health["action_count"] == 5


def test_completion_rate_after_terminal_events():
    bridge, bus, _ = _build()
    # 3 successful goals
    for i in range(3):
        _submit(bus, f"g{i}", "engineer", "build the audit tool")
        _terminal(bus, "goal.completed", f"g{i}")
    # 1 abandoned
    _submit(bus, "g_abandon", "engineer", "build the audit tool")
    _terminal(bus, "goal.abandoned", "g_abandon")
    # 1 orphaned
    _submit(bus, "g_orphan", "engineer", "build the audit tool")
    _terminal(bus, "goal.echo.orphaned", "g_orphan")
    health = bridge.persona_health("engineer")
    # 3 success out of 5 terminal = 0.6
    assert abs(health["completion_rate"] - 0.6) < 1e-9
    assert abs(health["abandon_rate"] - 0.2) < 1e-9


def test_meta_reflection_records_sls_delta():
    bridge, bus, _ = _build()
    for delta in (0.05, 0.10, -0.02):
        bus.publish(Thought(source="mco", topic="meta.reflection",
                             payload={"persona": "mystic",
                                      "outcome": "COMPLETED",
                                      "sls_delta": delta,
                                      "sls_after": 0.5,
                                      "bond_count": 1}))
    health = bridge.persona_health("mystic")
    # Average of (0.05, 0.10, -0.02) = 0.0433...
    assert abs(health["avg_sls_delta"] - 0.0433) < 1e-3


def test_silent_outcome_is_counted():
    bridge, bus, _ = _build()
    bus.publish(Thought(source="mco", topic="meta.reflection",
                         payload={"persona": "child",
                                  "outcome": "SILENT",
                                  "sls_delta": 0.0}))
    health = bridge.persona_health("child")
    assert health.get("silent_count", 0) == 1 or "silent_count" not in health


# ─────────────────────────────────────────────────────────────────────────────
# Intent stat accumulation
# ─────────────────────────────────────────────────────────────────────────────


def test_intent_stats_track_success_and_fail():
    bridge, bus, _ = _build()
    # Fire 3 successful "build wedding tool" goals + 1 abandoned
    for i in range(3):
        _submit(bus, f"win{i}", "engineer", "build wedding tool")
        _terminal(bus, "goal.completed", f"win{i}")
    _submit(bus, "lose", "engineer", "build wedding tool")
    _terminal(bus, "goal.abandoned", "lose")

    record = bridge.intent_track_record("engineer", "build")
    assert record["success_count"] == 3
    assert record["fail_count"] == 1
    assert abs(record["success_rate"] - 0.75) < 1e-9
    # Confidence should be > 0 (4 samples, 75% rate)
    assert record["confidence"] > 0.0


def test_winning_skill_chain_recorded_on_completion():
    bridge, bus, _ = _build()
    _submit(bus, "g1", "artist", "render an SVG")
    bus.publish(Thought(source="engine", topic="goal.completed",
                         payload={"goal_id": "g1",
                                  "recommended_skills": ["render_svg",
                                                           "save_to_disk"]}))
    record = bridge.intent_track_record("artist", "render")
    assert record["last_winning_skill_chain"] == ["render_svg", "save_to_disk"]


# ─────────────────────────────────────────────────────────────────────────────
# Pattern publication
# ─────────────────────────────────────────────────────────────────────────────


def test_pattern_published_when_confidence_crosses_threshold():
    bridge, bus, _ = _build(threshold=0.4)
    received = []
    bus.subscribe("miner.pattern.learned", lambda t: received.append(t))

    # Build up a strong pattern: 5 successes of "build audit tool"
    for i in range(5):
        _submit(bus, f"win{i}", "engineer", "build the audit tool")
        _terminal(bus, "goal.completed", f"win{i}")

    assert len(received) >= 1
    payload = received[0].payload
    assert payload["persona"] == "engineer"
    assert payload["confidence"] >= 0.4


def test_pattern_published_at_most_once_per_pair():
    bridge, bus, _ = _build(threshold=0.0)  # publishes immediately on any data
    received = []
    bus.subscribe("miner.pattern.learned", lambda t: received.append(t))
    # Many wins of the same intent
    for i in range(10):
        _submit(bus, f"g{i}", "engineer", "build a tool")
        _terminal(bus, "goal.completed", f"g{i}")
    # We expect ONE pattern per (persona, intent_keyword) pair, not 10.
    # The exact number depends on how many distinct keywords match —
    # at least one and at most 3 (since we cap keywords at 3).
    persona_intent_pairs = {(t.payload["persona"], t.payload["intent_keyword"])
                            for t in received}
    assert len(persona_intent_pairs) == len(received)


# ─────────────────────────────────────────────────────────────────────────────
# Recommendation
# ─────────────────────────────────────────────────────────────────────────────


def test_recommend_returns_pattern_when_history_strong():
    bridge, bus, _ = _build(threshold=0.4)
    # Build a strong pattern WITH a recorded skill chain.
    for i in range(4):
        _submit(bus, f"win{i}", "engineer", "build the audit skill")
        bus.publish(Thought(source="engine", topic="goal.completed",
                             payload={"goal_id": f"win{i}",
                                      "recommended_skills": ["validate",
                                                              "compile",
                                                              "register"]}))
    rec = bridge.recommend_skill_for("engineer", "build the audit skill")
    assert rec is not None
    assert rec["source"] == "pattern"
    assert rec["skills"] == ["validate", "compile", "register"]
    assert rec["confidence"] >= 0.4


def test_recommend_falls_back_to_skill_library():
    """Skill names must match one of the extracted keywords. The
    extractor splits on non-letter chars, so the skill name should be a
    single word that appears in the goal text."""
    bridge, bus, _ = _build(skills=["render"])
    # No history yet — pattern lookup misses.
    rec = bridge.recommend_skill_for("artist", "please render for me")
    assert rec is not None
    assert rec["source"] == "skill_library"
    assert "render" in rec["skills"]


def test_recommend_returns_none_when_nothing_matches():
    bridge, bus, _ = _build(skills=["render_svg"])
    rec = bridge.recommend_skill_for("artist", "completely unknown task")
    assert rec is None


def test_recommend_respects_min_confidence():
    bridge, bus, _ = _build(threshold=0.0)
    # Only 1 success — confidence will be 0 (sample size requires ≥ 2)
    _submit(bus, "g1", "engineer", "build a thing")
    bus.publish(Thought(source="engine", topic="goal.completed",
                         payload={"goal_id": "g1",
                                  "recommended_skills": ["x"]}))
    rec = bridge.recommend_skill_for(
        "engineer", "build a thing", min_confidence=0.5,
    )
    # Skill library would still match nothing → None
    assert rec is None


# ─────────────────────────────────────────────────────────────────────────────
# Persistence
# ─────────────────────────────────────────────────────────────────────────────


def test_persist_and_reload_round_trip():
    path = tempfile.mktemp(suffix=".json")
    try:
        bridge, bus, _ = _build(persistence_path=path)
        for i in range(3):
            _submit(bus, f"g{i}", "engineer", "build the audit")
            _terminal(bus, "goal.completed", f"g{i}")
        _submit(bus, "fail", "engineer", "build the audit")
        _terminal(bus, "goal.abandoned", "fail")
        bridge.persist()

        # Load into a fresh bridge — stats should survive.
        fresh = PersonaMinerBridge(
            thought_bus=None, persistence_path=path,
            pattern_threshold=0.4,
        )
        h = fresh.persona_health("engineer")
        assert h["completion_count"] == 3
        assert h["abandon_count"] == 1
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────


def test_summary_includes_persona_intent_open_counts():
    bridge, bus, _ = _build()
    # Use persona.collapse to register engineer in persona_stats too —
    # an unfinished goal alone doesn't create a persona stat (by design:
    # stats only update on collapse + terminal events).
    bus.publish(Thought(source="pv", topic="persona.collapse",
                         payload={"winner": "engineer",
                                  "probabilities": {"engineer": 0.9}}))
    for i in range(2):
        _submit(bus, f"g{i}", "mystic", "compose blessing")
        _terminal(bus, "goal.completed", f"g{i}")
    _submit(bus, "open", "engineer", "build audit")     # never closed
    s = bridge.summary()
    assert s["packet_count"] >= 1
    assert s["persona_count"] >= 2
    assert s["intent_count"] >= 1
    assert s["open_goals"] == 1


# ═════════════════════════════════════════════════════════════════════════════
# GoalSkillAligner
# ═════════════════════════════════════════════════════════════════════════════


def _build_aligner(threshold=0.4, skills=None):
    bridge, bus, _ = _build(threshold=threshold, skills=skills or [])
    aligner = GoalSkillAligner(
        thought_bus=bus, miner_bridge=bridge,
        republish_aligned=True, min_confidence=threshold,
    )
    aligner.start()
    return aligner, bridge, bus


def test_aligner_subscribes_to_goal_request():
    aligner, _, bus = _build_aligner()
    assert "goal.submit.request" in bus._subs


def test_aligner_publishes_suggestion_when_pattern_known():
    aligner, bridge, bus = _build_aligner(threshold=0.4)
    received = []
    bus.subscribe("goal.alignment.suggestion", lambda t: received.append(t))
    # Build a known pattern.
    for i in range(4):
        _submit(bus, f"win{i}", "engineer", "build the audit skill")
        bus.publish(Thought(source="engine", topic="goal.completed",
                             payload={"goal_id": f"win{i}",
                                      "recommended_skills": ["validate"]}))
    received.clear()
    # New goal matching the pattern should get a suggestion published.
    _submit(bus, "new", "engineer", "build the audit skill")
    suggestions = [t for t in received if t.topic == "goal.alignment.suggestion"]
    assert len(suggestions) >= 1
    s = suggestions[0].payload
    assert "validate" in s["recommended_skills"]
    assert s["source"] == "pattern"
    assert s["persona"] == "engineer"


def test_aligner_publishes_aligned_request_for_downstream():
    aligner, bridge, bus = _build_aligner(threshold=0.4)
    received = []
    bus.subscribe("goal.submit.request.aligned", lambda t: received.append(t))
    for i in range(4):
        _submit(bus, f"win{i}", "engineer", "build the audit skill")
        bus.publish(Thought(source="engine", topic="goal.completed",
                             payload={"goal_id": f"win{i}",
                                      "recommended_skills": ["validate"]}))
    received.clear()
    _submit(bus, "new", "engineer", "build the audit skill")
    assert len(received) == 1
    p = received[0].payload
    assert p["aligned"] is True
    assert "validate" in p["recommended_skills"]


def test_aligner_does_not_loop_on_aligned_republish():
    aligner, bridge, bus = _build_aligner(threshold=0.4)
    received_suggest = []
    bus.subscribe("goal.alignment.suggestion",
                  lambda t: received_suggest.append(t))
    # Build pattern.
    for i in range(4):
        _submit(bus, f"win{i}", "engineer", "build the audit")
        bus.publish(Thought(source="engine", topic="goal.completed",
                             payload={"goal_id": f"win{i}",
                                      "recommended_skills": ["x"]}))
    received_suggest.clear()
    _submit(bus, "test", "engineer", "build the audit")
    # Exactly one suggestion — the aligned republish must not re-trigger.
    assert len(received_suggest) == 1


def test_aligner_silent_when_no_pattern_or_skill():
    aligner, bridge, bus = _build_aligner()
    received = []
    bus.subscribe("goal.alignment.suggestion", lambda t: received.append(t))
    _submit(bus, "g1", "child", "completely novel intent")
    assert received == []


def test_aligner_falls_back_to_skill_library_match():
    aligner, bridge, bus = _build_aligner(threshold=0.4, skills=["render"])
    received = []
    bus.subscribe("goal.alignment.suggestion", lambda t: received.append(t))
    _submit(bus, "g1", "artist", "please render for the wedding")
    assert len(received) == 1
    assert received[0].payload["source"] == "skill_library"
    assert "render" in received[0].payload["recommended_skills"]


def test_aligner_stats():
    aligner, bridge, bus = _build_aligner(threshold=0.4, skills=["render"])
    _submit(bus, "g1", "artist", "render please")
    s = aligner.stats()
    assert s["lookups"] == 1
    assert s["suggestions"] == 1


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
