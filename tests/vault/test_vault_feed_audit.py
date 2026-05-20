#!/usr/bin/env python3
"""
Tests for VaultFeedAudit — verifies the audit surfaces which bus topics
are publishing but not reaching the vault, and emits a correct
subscription patch.

What's being proved:
  - DEFAULT_SUBSCRIPTIONS was widened to include persona chain topics
    (stage 6.2 class-level patch)
  - AureonVault.ingest() publishes vault.card.added on the bus
  - coverage_report(): per-topic {publications, vault_cards, covered,
    severity}
  - dead-branch severity classification (high = many pubs, 0 cards)
  - subscription_patch() returns only topics NOT already matched by
    prefix patterns in DEFAULT_SUBSCRIPTIONS
  - apply_patch() widens DEFAULT_SUBSCRIPTIONS; with rewire=True also
    subscribes the vault handler to the new topics
"""

from __future__ import annotations

import os
import sys
import time
from typing import Any, Dict, List

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from aureon.core.aureon_thought_bus import Thought, ThoughtBus  # noqa: E402
from aureon.vault.aureon_vault import AureonVault  # noqa: E402
from aureon.vault.voice.bus_flight_check import BusFlightCheck  # noqa: E402
from aureon.vault.voice.vault_feed_audit import VaultFeedAudit  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
# DEFAULT_SUBSCRIPTIONS patch proof
# ─────────────────────────────────────────────────────────────────────────────


def test_persona_chain_topics_are_in_default_subscriptions():
    required = {
        "persona.collapse", "persona.thought", "goal.submit.request",
        "goal.submitted", "goal.progress", "goal.completed",
        "goal.abandoned", "goal.echo", "goal.echo.summary",
        "goal.echo.orphaned", "queen.conscience.verdict",
        "symbolic.life.pulse", "life.event", "conversation.turn",
        "conversation.ambient", "meta.reflection",
        "flight.check.pulse", "standing.wave.bond",
    }
    current = set(AureonVault.DEFAULT_SUBSCRIPTIONS)
    missing = required - current
    assert not missing, f"topics still missing from DEFAULT_SUBSCRIPTIONS: {missing}"


def test_topic_to_category_maps_persona_topics():
    v = AureonVault()
    assert v._topic_to_category("persona.collapse") == "persona_collapse"
    assert v._topic_to_category("persona.thought") == "persona_thought"
    assert v._topic_to_category("persona.intent.rally") == "persona_intent"
    assert v._topic_to_category("persona.painter.composition") == "persona_artefact"
    assert v._topic_to_category("goal.echo") == "goal_echo"
    assert v._topic_to_category("goal.echo.summary") == "goal_summary"
    assert v._topic_to_category("goal.echo.orphaned") == "goal_orphaned"
    assert v._topic_to_category("goal.submit.request") == "goal_request"
    assert v._topic_to_category("goal.submitted") == "goal_submitted"
    assert v._topic_to_category("goal.progress") == "goal_progress"
    assert v._topic_to_category("goal.completed") == "goal_completed"
    assert v._topic_to_category("goal.abandoned") == "goal_abandoned"
    assert v._topic_to_category("queen.conscience.verdict") == "conscience_verdict"
    assert v._topic_to_category("symbolic.life.pulse") == "sls_pulse"
    assert v._topic_to_category("life.event") == "life_event"
    assert v._topic_to_category("conversation.turn") == "conversation"
    assert v._topic_to_category("meta.reflection") == "meta_reflection"
    assert v._topic_to_category("standing.wave.bond") == "wave_bond"


# ─────────────────────────────────────────────────────────────────────────────
# vault.card.added publication from ingest()
# ─────────────────────────────────────────────────────────────────────────────


def test_ingest_publishes_vault_card_added():
    bus = ThoughtBus()
    v = AureonVault()
    v._thought_bus = bus
    received: List[Thought] = []
    bus.subscribe("vault.card.added", lambda t: received.append(t))

    v.ingest(topic="persona.collapse", payload={"winner": "engineer"})
    assert len(received) == 1
    payload = received[0].payload
    assert payload["source_topic"] == "persona.collapse"
    assert payload["category"] == "persona_collapse"
    assert payload["content_id"]
    assert payload["harmonic_hash"]


def test_ingest_does_not_publish_for_vault_card_added_itself():
    """Belt-and-braces: if somebody ever ingests a vault.card.added topic
    directly, we don't recurse."""
    bus = ThoughtBus()
    v = AureonVault()
    v._thought_bus = bus
    received: List[Thought] = []
    bus.subscribe("vault.card.added", lambda t: received.append(t))

    v.ingest(topic="vault.card.added", payload={"content_id": "x"})
    # The card itself landed but no re-publication happened.
    assert len(received) == 0


# ─────────────────────────────────────────────────────────────────────────────
# Coverage report
# ─────────────────────────────────────────────────────────────────────────────


def _build_stack():
    bus = ThoughtBus()
    vault = AureonVault()
    vault._thought_bus = bus
    fc = BusFlightCheck(bus, recent_horizon_s=10.0)
    fc.start()
    audit = VaultFeedAudit(vault, fc)
    return bus, vault, fc, audit


def test_covered_topic_reports_low_severity():
    bus, vault, fc, audit = _build_stack()
    # Real wiring: the vault listens to persona.collapse now
    bus.subscribe("persona.collapse", vault._on_thought)
    bus.publish(Thought(source="pv", topic="persona.collapse", payload={"w": "engineer"}))
    report = audit.coverage_report()
    row = next(r for r in report["topics"] if r["topic"] == "persona.collapse")
    assert row["publications"] == 1
    assert row["vault_cards"] == 1
    assert row["covered"] is True
    assert row["severity"] == "low"


def test_dead_branch_high_severity():
    bus, vault, fc, audit = _build_stack()
    # Publish lots but don't subscribe vault; audit should flag HIGH.
    for i in range(7):
        bus.publish(Thought(source="x", topic="fc_test.ignored.topic",
                            payload={"i": i}))
    report = audit.coverage_report()
    row = next(r for r in report["topics"] if r["topic"] == "fc_test.ignored.topic")
    assert row["publications"] == 7
    assert row["vault_cards"] == 0
    assert row["covered"] is False
    assert row["severity"] == "high"
    assert "fc_test.ignored.topic" in report["high_severity_dead_branches"]


def test_low_publication_dead_branch_is_medium():
    bus, vault, fc, audit = _build_stack()
    bus.publish(Thought(source="x", topic="fc_test.lonely", payload={}))
    report = audit.coverage_report()
    row = next(r for r in report["topics"] if r["topic"] == "fc_test.lonely")
    assert row["severity"] == "medium"
    assert "fc_test.lonely" in report["medium_severity_dead_branches"]


def test_coverage_pct_calculation():
    bus, vault, fc, audit = _build_stack()
    bus.subscribe("fc_test.kept", vault._on_thought)
    bus.publish(Thought(source="x", topic="fc_test.kept", payload={}))
    bus.publish(Thought(source="x", topic="fc_test.lost", payload={}))
    report = audit.coverage_report()
    # Among the two fc_test topics, one is covered. Real coverage_pct
    # depends on all bus topics (mycelium sonar etc.), so we just
    # verify the two rows appear correctly.
    topics = {r["topic"]: r for r in report["topics"]}
    assert topics["fc_test.kept"]["covered"] is True
    assert topics["fc_test.lost"]["covered"] is False


# ─────────────────────────────────────────────────────────────────────────────
# Subscription patch
# ─────────────────────────────────────────────────────────────────────────────


def test_subscription_patch_lists_missing_topics():
    bus, vault, fc, audit = _build_stack()
    # Strip the vault's subscriptions down to bare minimum so the patch
    # has something to find.
    vault.DEFAULT_SUBSCRIPTIONS = ["queen.cortex.state"]
    bus.publish(Thought(source="x", topic="totally.new.topic", payload={}))
    bus.publish(Thought(source="x", topic="queen.cortex.state", payload={}))
    patch = audit.subscription_patch()
    assert "totally.new.topic" in patch["missing_topics"]
    assert "queen.cortex.state" in patch["already_covered_topics"]


def test_subscription_patch_respects_prefix_patterns():
    bus, vault, fc, audit = _build_stack()
    vault.DEFAULT_SUBSCRIPTIONS = ["foo.*"]
    bus.publish(Thought(source="x", topic="foo.bar", payload={}))
    bus.publish(Thought(source="x", topic="foo.baz.qux", payload={}))
    bus.publish(Thought(source="x", topic="other.thing", payload={}))
    patch = audit.subscription_patch()
    assert "foo.bar" in patch["already_covered_topics"]
    assert "foo.baz.qux" in patch["already_covered_topics"]
    assert "other.thing" in patch["missing_topics"]
    assert "foo.bar" not in patch["missing_topics"]


def test_subscription_patch_ignores_zero_publication_topics():
    bus, vault, fc, audit = _build_stack()
    vault.DEFAULT_SUBSCRIPTIONS = []
    # A subscribed-but-silent line should NOT appear in missing_topics
    # because we only care about live signal.
    bus.subscribe("silent.line", lambda t: None)
    patch = audit.subscription_patch()
    assert "silent.line" not in patch["missing_topics"]


# ─────────────────────────────────────────────────────────────────────────────
# apply_patch
# ─────────────────────────────────────────────────────────────────────────────


def test_apply_patch_widens_default_subscriptions():
    bus, vault, fc, audit = _build_stack()
    vault.DEFAULT_SUBSCRIPTIONS = ["queen.cortex.state"]
    bus.publish(Thought(source="x", topic="missing.a", payload={}))
    bus.publish(Thought(source="x", topic="missing.b", payload={}))
    result = audit.apply_patch(rewire=False)
    assert result["ok"] is True
    assert set(result["added"]) == {"missing.a", "missing.b"}
    assert "missing.a" in vault.DEFAULT_SUBSCRIPTIONS
    assert "missing.b" in vault.DEFAULT_SUBSCRIPTIONS
    # No rewire asked — no live subscribe
    assert result["rewired"] == []


def test_apply_patch_rewires_bus_when_requested():
    bus, vault, fc, audit = _build_stack()
    vault.DEFAULT_SUBSCRIPTIONS = []
    bus.publish(Thought(source="x", topic="late.join.topic", payload={}))
    result = audit.apply_patch(rewire=True)
    assert "late.join.topic" in result["rewired"]
    # Now publishing to the topic should land on the vault.
    before = len(vault)
    bus.publish(Thought(source="x", topic="late.join.topic", payload={"n": 1}))
    after = len(vault)
    assert after == before + 1


def test_apply_patch_noop_when_nothing_missing():
    bus, vault, fc, audit = _build_stack()
    # No traffic → nothing to patch.
    result = audit.apply_patch()
    assert result["ok"] is True
    assert result["added"] == []


def test_last_report_cached():
    bus, vault, fc, audit = _build_stack()
    bus.publish(Thought(source="x", topic="cached.topic", payload={}))
    assert audit.last_report() == {}
    audit.coverage_report()
    cached = audit.last_report()
    assert cached["total_topics"] > 0
    assert any(r["topic"] == "cached.topic" for r in cached["topics"])


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
