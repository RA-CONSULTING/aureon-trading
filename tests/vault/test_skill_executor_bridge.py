#!/usr/bin/env python3
"""
Tests for SkillExecutorBridge — proof the system actually builds things.

What's being proved:
  - subscribes to goal.submit.request.aligned (NOT the raw topic)
  - default executor writes a real markdown artefact under output_root
  - vault receives a skill.execution.output card per artefact
  - skill.execution.started / completed / goal.completed publish in order
  - multi-skill chain executes every skill in order; all succeed → one
    goal.completed with artefacts list
  - any skill failure → skill.execution.failed + goal.abandoned, chain
    aborts (subsequent skills don't run)
  - conscience VETO blocks execution before any skill runs
  - GoalClaims coordinates with GoalDispatchBridge:
      • skill_executor.claim succeeds first → GDB skips
      • no recommended_skills → no claim → GDB proceeds
  - empty recommended_skills list → goal.abandoned with reason
  - custom executor is honored (code_architect_adapter path)
"""

from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable, Dict, List

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from aureon.core.aureon_thought_bus import Thought, ThoughtBus  # noqa: E402
from aureon.vault.aureon_vault import AureonVault  # noqa: E402
from aureon.vault.voice._goal_claims import GoalClaims  # noqa: E402
from aureon.vault.voice.goal_dispatch_bridge import GoalDispatchBridge  # noqa: E402
from aureon.vault.voice.skill_executor_bridge import (  # noqa: E402
    SkillExecutorBridge,
    code_architect_adapter,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _fresh_claims():
    GoalClaims.clear()


def _build(executor=None, conscience=None, output_root=None):
    _fresh_claims()
    bus = ThoughtBus()
    vault = AureonVault()
    vault._thought_bus = bus
    tmp = output_root or tempfile.mkdtemp(prefix="aureon_skill_out_")
    bridge = SkillExecutorBridge(
        thought_bus=bus, vault=vault, executor=executor,
        conscience=conscience, output_root=tmp,
        run_in_thread=False,
    )
    bridge.start()
    return bridge, bus, vault, Path(tmp)


def _aligned_request(bus, goal_id, persona, text, skills):
    bus.publish(Thought(source="aligner",
                         topic="goal.submit.request.aligned",
                         payload={
                             "goal_id": goal_id, "text": text,
                             "proposed_by_persona": persona,
                             "aligned": True,
                             "recommended_skills": list(skills),
                         }))


# ─────────────────────────────────────────────────────────────────────────────
# Subscription
# ─────────────────────────────────────────────────────────────────────────────


def test_subscribes_to_aligned_topic():
    bridge, bus, _, _ = _build()
    assert "goal.submit.request.aligned" in bus._subs


def test_only_subscribes_to_aligned_not_raw():
    bridge, bus, _, _ = _build()
    # We DO NOT subscribe to goal.submit.request — that's GDB's territory.
    assert "goal.submit.request" not in bus._subs or all(
        h.__func__ != bridge._on_aligned_request.__func__
        for h in bus._subs.get("goal.submit.request", [])
        if hasattr(h, "__func__")
    )


# ─────────────────────────────────────────────────────────────────────────────
# Default file executor actually writes
# ─────────────────────────────────────────────────────────────────────────────


def test_default_executor_writes_artefact_to_disk():
    bridge, bus, vault, out = _build()
    _aligned_request(bus, "g1", "engineer", "build the audit skill",
                     ["validate_gate"])
    files = list(out.glob("*.md"))
    assert len(files) == 1
    content = files[0].read_text(encoding="utf-8")
    assert "validate_gate" in content
    assert "build the audit skill" in content  # intent_text in artefact
    assert "engineer" in content


def test_multi_skill_chain_produces_multiple_artefacts():
    bridge, bus, vault, out = _build()
    _aligned_request(bus, "g1", "engineer", "build X",
                     ["skill_a", "skill_b", "skill_c"])
    files = sorted(out.glob("*.md"))
    assert len(files) == 3
    names = [f.name for f in files]
    assert any("skill_a" in n for n in names)
    assert any("skill_b" in n for n in names)
    assert any("skill_c" in n for n in names)


def test_vault_receives_skill_output_card_per_artefact():
    bridge, bus, vault, out = _build()
    _aligned_request(bus, "g1", "mystic", "compose blessing",
                     ["compose_blessing"])
    cards = [c for c in vault._contents.values()
             if c.source_topic == "skill.execution.output"]
    assert len(cards) == 1
    payload = cards[0].payload
    assert payload["skill_name"] == "compose_blessing"
    assert payload["persona"] == "mystic"
    assert payload["artefact_path"].endswith(".md")


# ─────────────────────────────────────────────────────────────────────────────
# Event sequence
# ─────────────────────────────────────────────────────────────────────────────


def test_published_event_sequence():
    bridge, bus, vault, out = _build()
    events = []
    for topic in ("skill.execution.started", "skill.execution.completed",
                  "goal.completed", "goal.abandoned",
                  "skill.execution.failed"):
        bus.subscribe(topic, lambda t: events.append(t.topic))
    _aligned_request(bus, "g1", "engineer", "build X", ["s1", "s2"])
    # 2 started, 2 completed, 1 goal.completed, 0 failures/abandons
    assert events.count("skill.execution.started") == 2
    assert events.count("skill.execution.completed") == 2
    assert events.count("goal.completed") == 1
    assert "goal.abandoned" not in events
    assert "skill.execution.failed" not in events


def test_goal_completed_carries_artefacts():
    bridge, bus, vault, out = _build()
    completions = []
    bus.subscribe("goal.completed", lambda t: completions.append(t))
    _aligned_request(bus, "g1", "engineer", "build X", ["a", "b"])
    assert len(completions) == 1
    p = completions[0].payload
    assert p["goal_id"] == "g1"
    assert len(p["artefacts"]) == 2
    assert p["source"] == "skill_executor_bridge"
    assert "built 2 artefact(s)" in p["result_summary"]


# ─────────────────────────────────────────────────────────────────────────────
# Failure paths
# ─────────────────────────────────────────────────────────────────────────────


def test_failing_skill_aborts_chain():
    calls: List[str] = []

    def failing_executor(skill_name, params):
        calls.append(skill_name)
        if skill_name == "bad":
            return {"ok": False, "artefacts": [], "result": None,
                    "error": "simulated failure"}
        return {"ok": True, "artefacts": [f"/tmp/{skill_name}.md"],
                "result": None, "error": ""}

    bridge, bus, vault, _ = _build(executor=failing_executor)
    abandoned = []
    failed = []
    bus.subscribe("goal.abandoned", lambda t: abandoned.append(t))
    bus.subscribe("skill.execution.failed", lambda t: failed.append(t))
    _aligned_request(bus, "g1", "engineer", "build X",
                     ["good1", "bad", "good2"])
    # good1 runs, bad fails, good2 should NEVER run
    assert calls == ["good1", "bad"]
    assert len(failed) == 1
    assert len(abandoned) == 1
    assert "simulated failure" in abandoned[0].payload["reason"]


def test_no_recommended_skills_is_abandoned():
    bridge, bus, vault, _ = _build()
    abandoned = []
    bus.subscribe("goal.abandoned", lambda t: abandoned.append(t))
    _aligned_request(bus, "g1", "engineer", "build X", [])
    assert len(abandoned) == 1
    assert "no recommended_skills" in abandoned[0].payload["reason"]


# ─────────────────────────────────────────────────────────────────────────────
# Dry-run
# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
# Conscience gating
# ─────────────────────────────────────────────────────────────────────────────


class _VetoConscience:
    class _V: pass
    class _W:
        def __init__(self):
            self.verdict = _VetoConscience._V()
            self.verdict.name = "VETO"
            self.message = "Substrate coherence too low"
            self.why_it_matters = ""
    def ask_why(self, action, context=None):
        return _VetoConscience._W()


class _ApproveConscience:
    class _V: pass
    class _W:
        def __init__(self):
            self.verdict = _ApproveConscience._V()
            self.verdict.name = "APPROVED"
            self.message = "ok"
            self.why_it_matters = ""
    def ask_why(self, action, context=None):
        return _ApproveConscience._W()


def test_conscience_veto_blocks_execution():
    bridge, bus, vault, out = _build(conscience=_VetoConscience())
    abandoned = []
    bus.subscribe("goal.abandoned", lambda t: abandoned.append(t))
    _aligned_request(bus, "g1", "engineer", "build X", ["s1"])
    # Nothing written
    assert list(out.glob("*")) == []
    # Abandoned fired with substrate reason
    assert len(abandoned) == 1
    assert "Substrate coherence" in abandoned[0].payload["reason"]


def test_conscience_approve_allows_execution():
    bridge, bus, vault, out = _build(conscience=_ApproveConscience())
    completions = []
    bus.subscribe("goal.completed", lambda t: completions.append(t))
    _aligned_request(bus, "g1", "engineer", "build X", ["s1"])
    assert len(completions) == 1
    assert len(list(out.glob("*.md"))) == 1


# ─────────────────────────────────────────────────────────────────────────────
# GoalClaims coordination with GoalDispatchBridge
# ─────────────────────────────────────────────────────────────────────────────


def test_skill_executor_claims_goal_id():
    _fresh_claims()
    bridge, bus, _, _ = _build()
    _aligned_request(bus, "claim-test", "engineer", "x", ["s"])
    # After dispatch, the goal_id remains claimed so GDB will skip.
    assert GoalClaims.is_claimed("claim-test")
    assert GoalClaims.who("claim-test") == "skill_executor"


def test_goal_dispatch_bridge_skips_claimed_goal():
    """Full two-bridge dance: the aligned request claims the goal;
    GoalDispatchBridge — even if it receives the raw request after —
    skips the claim and doesn't call the engine."""
    _fresh_claims()
    bus = ThoughtBus()
    vault = AureonVault(); vault._thought_bus = bus

    # Build skill executor first (so it claims first)
    skill = SkillExecutorBridge(
        thought_bus=bus, vault=vault,
        output_root=tempfile.mkdtemp(prefix="aureon_skill_"),
        run_in_thread=False,
    )
    skill.start()

    # Track engine calls
    engine_calls = []
    class _StubEngine:
        def submit_goal(self, text):
            engine_calls.append(text)
            return {"goal_id": "x", "text": text}

    class _Verdict:
        name = "APPROVED"

    class _Whisper:
        def __init__(self):
            self.verdict = _Verdict()
            self.message = "ok"
            self.why_it_matters = ""

    class _ApproveConscience2:
        def ask_why(self, action, context=None):
            return _Whisper()

    gdb = GoalDispatchBridge(
        thought_bus=bus,
        conscience=_ApproveConscience2(),
        goal_engine=_StubEngine(),
        
    )
    gdb._run_in_thread = False
    gdb.start()

    # Step 1: skill executor claims via aligned request
    _aligned_request(bus, "coord-1", "engineer", "build audit", ["s"])
    assert GoalClaims.is_claimed("coord-1")

    # Step 2: GDB receives the RAW request for the same goal_id → skips
    bus.publish(Thought(source="persona_actuator",
                         topic="goal.submit.request",
                         payload={"goal_id": "coord-1",
                                  "text": "build audit",
                                  "proposed_by_persona": "engineer"}))
    assert engine_calls == [], \
        "GDB should have skipped the claimed goal but called the engine"


def test_gdb_runs_normally_for_unclaimed_goal():
    """A goal that never went through the aligner (no learned pattern)
    has no claim — GDB dispatches to the engine as before."""
    _fresh_claims()
    bus = ThoughtBus()
    vault = AureonVault(); vault._thought_bus = bus

    engine_calls = []
    class _StubEngine:
        def submit_goal(self, text):
            engine_calls.append(text)
            return {"goal_id": "x", "text": text}

    class _Verdict:
        name = "APPROVED"

    class _Whisper:
        def __init__(self):
            self.verdict = _Verdict()
            self.message = "ok"
            self.why_it_matters = ""

    class _ApproveConscience2:
        def ask_why(self, action, context=None):
            return _Whisper()

    gdb = GoalDispatchBridge(
        thought_bus=bus,
        conscience=_ApproveConscience2(),
        goal_engine=_StubEngine(),
        
    )
    gdb._run_in_thread = False
    gdb.start()

    bus.publish(Thought(source="persona_actuator",
                         topic="goal.submit.request",
                         payload={"goal_id": "noclaim-1",
                                  "text": "do a thing",
                                  "proposed_by_persona": "engineer"}))
    assert engine_calls == ["do a thing"]


# ─────────────────────────────────────────────────────────────────────────────
# Custom executor
# ─────────────────────────────────────────────────────────────────────────────


def test_custom_executor_is_honored():
    captured: List[Dict[str, Any]] = []

    def my_executor(skill_name, params):
        captured.append({"skill": skill_name, "params": dict(params)})
        return {"ok": True, "artefacts": [f"/tmp/fake/{skill_name}.out"],
                "result": {"done": True}, "error": ""}

    bridge, bus, vault, _ = _build(executor=my_executor)
    _aligned_request(bus, "g1", "mystic", "compose",
                     ["chant", "invocation"])
    assert len(captured) == 2
    assert captured[0]["skill"] == "chant"
    assert captured[0]["params"]["intent_text"] == "compose"
    assert captured[0]["params"]["persona"] == "mystic"


def test_code_architect_adapter_wraps_real_API_shape():
    """The adapter must coerce CodeArchitect.execute_skill's result into
    our {ok, artefacts, result, error} contract even when field names
    differ (success vs ok, outputs vs artefacts)."""

    class _FakeResult:
        def __init__(self):
            self.success = True
            self.outputs = ["/tmp/real_skill.out"]
            self.payload = {"data": 1}
            self.error = ""

    class _FakeCodeArchitect:
        def execute_skill(self, skill_name, params=None):
            return _FakeResult()

    adapted = code_architect_adapter(_FakeCodeArchitect())
    out = adapted("some_skill", {"p": 1})
    assert out["ok"] is True
    assert out["artefacts"] == ["/tmp/real_skill.out"]
    assert out["result"] == {"data": 1}


def test_code_architect_adapter_handles_exception():
    class _Broken:
        def execute_skill(self, skill_name, params=None):
            raise RuntimeError("lib crash")

    adapted = code_architect_adapter(_Broken())
    out = adapted("s", {})
    assert out["ok"] is False
    assert "lib crash" in out["error"]


# ─────────────────────────────────────────────────────────────────────────────
# Stats + history
# ─────────────────────────────────────────────────────────────────────────────


def test_stats_track_execution_counts():
    bridge, bus, vault, out = _build()
    _aligned_request(bus, "g1", "engineer", "build X", ["a", "b"])
    s = bridge.stats()
    assert s["claimed"] == 1
    assert s["executed"] == 2
    assert s["failed"] == 0


def test_history_records_artefacts():
    bridge, bus, vault, out = _build()
    _aligned_request(bus, "g1", "engineer", "build X", ["a"])
    h = bridge.history()
    assert len(h) == 1
    record = h[0]
    assert record["skill_name"] == "a"
    assert record["ok"] is True
    assert len(record["artefacts"]) == 1


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
