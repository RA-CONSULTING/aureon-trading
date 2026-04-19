"""
Walking-skeleton tests for the seven-phase cognition pipeline.

The M0 assertions are architectural, not behavioural: the pipeline must
thread one ``trace_id`` through Boot → Comprehend → Vault → External →
Complexity → Multiverse → Coherence Collapse → Complete, publishing a
thought per phase on the supplied bus.
"""

from __future__ import annotations

from typing import List

import pytest

from aureon.cognition import CognitionPipeline, run_goal
from aureon.core.aureon_thought_bus import Thought, ThoughtBus


PHASE_TOPICS = [
    "cognition.phase.boot",
    "cognition.phase.comprehend",
    "cognition.phase.vault_check",
    "cognition.phase.external_fallback",
    "cognition.phase.complexity_gate",
    "cognition.phase.multiverse",
    "cognition.phase.coherence_collapse",
]

COMPLETE_TOPIC = "cognition.complete"


@pytest.fixture()
def bus(tmp_path) -> ThoughtBus:
    return ThoughtBus(persist_path=str(tmp_path / "thoughts.jsonl"))


@pytest.fixture()
def captured(bus: ThoughtBus) -> List[Thought]:
    recorded: List[Thought] = []
    bus.subscribe("cognition.*", lambda t: recorded.append(t))
    return recorded


def test_echo_flow_publishes_seven_phases(bus: ThoughtBus, captured: List[Thought]) -> None:
    pipeline = CognitionPipeline(bus=bus)
    env = pipeline.run("echo hello world")

    topics = [t.topic for t in captured]
    assert topics == PHASE_TOPICS + [COMPLETE_TOPIC]

    trace_ids = {t.trace_id for t in captured}
    assert trace_ids == {env.trace_id}

    assert env.intent is not None and env.intent.primary_verb == "echo"
    assert env.vault_hit is not None and env.vault_hit.hit is False
    assert env.complexity is not None and env.complexity.n_branches == 1
    assert len(env.branches) == 1
    assert env.collapsed is not None
    assert env.collapsed.winning_branch_id == env.branches[0].branch_id
    assert env.collapsed.text == "echo hello world"


def test_parent_ids_chain_phases(bus: ThoughtBus, captured: List[Thought]) -> None:
    CognitionPipeline(bus=bus).run("ping")

    # First thought has no parent; every subsequent thought's parent_id
    # is the previous thought's id.
    assert captured[0].parent_id is None
    for prev, curr in zip(captured, captured[1:]):
        assert curr.parent_id == prev.id


def test_complete_envelope_contains_all_phase_ids(bus: ThoughtBus, captured: List[Thought]) -> None:
    env = CognitionPipeline(bus=bus).run("check balance")

    expected_keys = {"boot", "comprehend", "vault_check", "external_fallback", "complexity_gate", "multiverse", "coherence_collapse", "complete"}
    assert expected_keys.issubset(env.phase_thought_ids.keys())
    for key in expected_keys:
        assert env.phase_thought_ids[key], f"missing thought id for phase {key}"


def test_run_goal_convenience(bus: ThoughtBus, captured: List[Thought]) -> None:
    env = run_goal("list positions", bus=bus)
    assert env.trace_id
    assert env.intent is not None
    assert len(captured) == len(PHASE_TOPICS) + 1


def test_empty_prompt_routes_to_unknown(bus: ThoughtBus, captured: List[Thought]) -> None:
    env = CognitionPipeline(bus=bus).run("")
    assert env.intent is not None
    assert env.intent.primary_verb == "unknown"
    # Pipeline still completes all seven phases even on empty input.
    assert len([t for t in captured if t.topic.startswith("cognition.phase.")]) == 7
