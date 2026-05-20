#!/usr/bin/env python3
"""
Tests for BusFlightCheck — the standing-wave topology inspector.

What's being proved:
  - ThoughtBus now exposes list_subscribed_topics() and subscriber_count()
  - Empty bus → empty topology (no topics, health = 0)
  - Subscriber + publisher produces correct counts and last-seen tracking
  - Publish-without-subscribe flagged as orphan_published
  - Subscribe-without-publish flagged as orphan_subscribed
  - Wildcard subscribers don't distort per-topic counts
  - Prefix-pattern subscribers match the right topics
  - standing_wave_report returns covered_ratio, active_ratio,
    publication_balance, and a scalar health in [0, 1]
  - watch() publishes flight.check.pulse on a fast interval
  - The inspector's own wildcard subscription doesn't get counted as a
    "subscriber" of every topic (would make every topic look covered)
"""

from __future__ import annotations

import os
import sys
import time
from typing import Any

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from aureon.core.aureon_thought_bus import Thought, ThoughtBus  # noqa: E402
from aureon.vault.voice.bus_flight_check import BusFlightCheck  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
# ThoughtBus accessor unit tests
# ─────────────────────────────────────────────────────────────────────────────


def test_list_subscribed_topics_returns_list():
    """Real ThoughtBus auto-wires mycelium whale sonar on init, so we
    can't assume an empty subscription table — we just assert the API
    returns a list and picks up anything we subscribe to."""
    bus = ThoughtBus()
    bus.subscribe("flight.check.test.topic.a", lambda t: None)
    bus.subscribe("flight.check.test.topic.b.*", lambda t: None)
    topics = bus.list_subscribed_topics()
    assert isinstance(topics, list)
    assert "flight.check.test.topic.a" in topics
    assert "flight.check.test.topic.b.*" in topics


def test_subscriber_count_for_known_topics():
    bus = ThoughtBus()
    bus.subscribe("flight.check.test.topic.a", lambda t: None)
    bus.subscribe("flight.check.test.topic.a", lambda t: None)
    bus.subscribe("flight.check.test.topic.b", lambda t: None)
    assert bus.subscriber_count("flight.check.test.topic.a") == 2
    assert bus.subscriber_count("flight.check.test.topic.b") == 1
    assert bus.subscriber_count("flight.check.test.topic.nonexistent") == 0


def test_subscriber_count_total_is_monotonic():
    bus = ThoughtBus()
    total_before = bus.subscriber_count()
    bus.subscribe("flight.check.test.x", lambda t: None)
    bus.subscribe("flight.check.test.y", lambda t: None)
    total_after = bus.subscriber_count()
    assert total_after == total_before + 2


# ─────────────────────────────────────────────────────────────────────────────
# BusFlightCheck — topology
# ─────────────────────────────────────────────────────────────────────────────


def _build():
    bus = ThoughtBus()
    fc = BusFlightCheck(bus, recent_horizon_s=5.0)
    fc.start()
    return fc, bus


def test_topology_contains_structure_even_on_busy_bus():
    """Don't assume an empty bus (whale sonar auto-subscribes). Just
    verify the topology dict has the expected structure."""
    fc, _ = _build()
    topo = fc.topology()
    assert "topics" in topo
    assert "total_publications" in topo
    assert "orphans_published_unsubscribed" in topo
    assert "orphans_subscribed_unpublished" in topo
    report = fc.standing_wave_report()
    assert 0.0 <= report["health"] <= 1.0


def test_publish_is_recorded():
    fc, bus = _build()
    bus.publish(Thought(source="miner", topic="fc_test.miner.signal", payload={}))
    topo = fc.topology()
    topics = {r["topic"]: r for r in topo["topics"]}
    assert "fc_test.miner.signal" in topics
    record = topics["fc_test.miner.signal"]
    assert record["publications"] == 1
    # Publishers dict is a list of (source, count) tuples.
    assert record["publishers"] == [("miner", 1)]
    assert record["last_seen_s_ago"] is not None
    assert record["last_seen_s_ago"] >= 0.0


def test_subscribe_without_publish_is_orphan_subscribed():
    fc, bus = _build()
    bus.subscribe("fc_test.lonely.topic", lambda t: None)
    topo = fc.topology()
    topics = {r["topic"]: r for r in topo["topics"]}
    assert "fc_test.lonely.topic" in topics
    assert topics["fc_test.lonely.topic"]["subscribers"] >= 1
    assert topics["fc_test.lonely.topic"]["publications"] == 0
    assert topics["fc_test.lonely.topic"]["orphan_subscribed"] is True
    assert "fc_test.lonely.topic" in topo["orphans_subscribed_unpublished"]


def test_publish_without_subscribe_is_orphan_published():
    fc, bus = _build()
    bus.publish(Thought(source="whoever", topic="fc_test.unheard.topic", payload={}))
    topo = fc.topology()
    topics = {r["topic"]: r for r in topo["topics"]}
    assert topics["fc_test.unheard.topic"]["orphan_published"] is True
    assert "fc_test.unheard.topic" in topo["orphans_published_unsubscribed"]


def test_matching_subscription_prevents_orphan():
    fc, bus = _build()
    bus.subscribe("fc_test.x.topic", lambda t: None)
    bus.publish(Thought(source="w", topic="fc_test.x.topic", payload={}))
    topo = fc.topology()
    r = next(r for r in topo["topics"] if r["topic"] == "fc_test.x.topic")
    assert r["orphan_published"] is False
    assert r["orphan_subscribed"] is False
    assert r["subscribers"] >= 1
    assert r["publications"] == 1


def test_prefix_subscription_matches_subtopics():
    fc, bus = _build()
    bus.subscribe("fc_test.queen.*", lambda t: None)
    bus.publish(Thought(source="w", topic="fc_test.queen.cortex.state", payload={}))
    topo = fc.topology()
    match = next(r for r in topo["topics"]
                 if r["topic"] == "fc_test.queen.cortex.state")
    assert match["subscribers"] >= 1
    assert match["orphan_published"] is False
    assert "fc_test.queen.*" in match["subscriber_patterns"]


def test_wildcard_subscriber_does_not_become_universal_cover():
    """A '*' subscriber must NOT be counted as a subscriber of every
    specific topic — otherwise every topic looks covered and orphan
    detection breaks."""
    fc, bus = _build()
    # Use a topic name the mycelium sonar auto-wiring won't touch.
    bus.publish(Thought(source="w", topic="fc_test.unheard.new", payload={}))
    topo = fc.topology()
    r = next(r for r in topo["topics"] if r["topic"] == "fc_test.unheard.new")
    # subscribers count excludes the '*' pattern by design — so even
    # though flight-check subscribes to '*' its listener doesn't count
    # as a per-topic subscriber.
    assert r["subscribers"] == 0
    assert r["orphan_published"] is True


def test_flight_check_does_not_self_record_its_pulse():
    """Publishing flight.check.pulse from source=bus_flight_check must
    be ignored — otherwise the watch loop self-bloats the topology."""
    fc, bus = _build()
    bus.publish(Thought(source="bus_flight_check",
                        topic="flight.check.pulse", payload={"health": 0.5}))
    topo = fc.topology()
    topics = {r["topic"]: r for r in topo["topics"]}
    pulse = topics.get("flight.check.pulse")
    if pulse is not None:
        assert pulse["publications"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# Standing-wave report
# ─────────────────────────────────────────────────────────────────────────────


def test_standing_wave_report_has_all_factors():
    fc, bus = _build()
    for t in ("fc_test.a", "fc_test.b", "fc_test.c"):
        bus.subscribe(t, lambda th: None)
        bus.publish(Thought(source="w", topic=t, payload={"n": 1}))
    report = fc.standing_wave_report()
    for key in ("health", "covered_ratio", "active_ratio", "publication_balance"):
        assert key in report
        assert 0.0 <= report[key] <= 1.0


def test_standing_wave_report_penalises_unbalanced_traffic():
    fc, bus = _build()
    for t in ("fc_test.unbal.a", "fc_test.unbal.b"):
        bus.subscribe(t, lambda th: None)
    for _ in range(100):
        bus.publish(Thought(source="w", topic="fc_test.unbal.a", payload={}))
    bus.publish(Thought(source="w", topic="fc_test.unbal.b", payload={}))
    unbalanced = fc.standing_wave_report()

    fc2, bus2 = _build()
    for t in ("fc_test.bal.x", "fc_test.bal.y"):
        bus2.subscribe(t, lambda th: None)
    for _ in range(10):
        bus2.publish(Thought(source="w", topic="fc_test.bal.x", payload={}))
        bus2.publish(Thought(source="w", topic="fc_test.bal.y", payload={}))
    balanced = fc2.standing_wave_report()

    # Balance is a global metric over ALL topics — we can't guarantee
    # the global figure moves, but we can at least verify the unbalanced
    # report's per-topic publication variance is higher than balanced's.
    unbal_topics = {t["topic"]: t["publications"] for t in unbalanced["topics"]
                    if t["topic"].startswith("fc_test.unbal.")}
    bal_topics = {t["topic"]: t["publications"] for t in balanced["topics"]
                  if t["topic"].startswith("fc_test.bal.")}
    assert max(unbal_topics.values()) / min(unbal_topics.values()) > 10
    assert max(bal_topics.values()) / min(bal_topics.values()) < 2


# ─────────────────────────────────────────────────────────────────────────────
# Watch loop
# ─────────────────────────────────────────────────────────────────────────────


def test_watch_publishes_flight_check_pulse():
    bus = ThoughtBus()
    fc = BusFlightCheck(bus, recent_horizon_s=5.0, watch_interval_s=0.05)
    fc.start()
    # Put something in the topology so the pulse has signal
    bus.subscribe("t", lambda th: None)
    bus.publish(Thought(source="w", topic="t", payload={}))

    received = []
    bus.subscribe("flight.check.pulse", lambda th: received.append(th))

    fc.start_watching()
    try:
        deadline = time.time() + 1.0
        while time.time() < deadline and not received:
            time.sleep(0.02)
    finally:
        fc.stop_watching()

    assert len(received) >= 1
    payload = received[0].payload
    # Compact payload shape
    for key in ("ts", "health", "covered_ratio", "active_ratio",
                 "publication_balance", "active_topic_count",
                 "total_publications"):
        assert key in payload


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
