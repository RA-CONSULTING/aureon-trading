#!/usr/bin/env python3
"""
Tests for AffinityChorus and the unified-collapse path in PersonaVacuum.

What's being proved:
  - AffinityChorus sums contributions and prunes stale entries
  - publish() round-trips through the local table
  - PersonaVacuum with a chorus publishes its own scores + consumes others
  - Two vacuums sharing a bus + chorus + fingerprint-seed ALWAYS collapse
    to the same winner, across many seeds
  - Without the chorus, the same two vacuums may collapse to different
    winners (i.e. the chorus is actually doing work)
"""

from __future__ import annotations

import os
import random
import sys
import time
from typing import Any, Callable, Dict, List

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from aureon.vault.aureon_vault import AureonVault, VaultContent  # noqa: E402
from aureon.vault.voice.affinity_chorus import (  # noqa: E402
    AffinityChorus,
    AffinityContribution,
    make_vault_seed_fn,
    vault_fingerprint_seed,
)
from aureon.vault.voice.aureon_personas import build_aureon_personas  # noqa: E402
from aureon.vault.voice.persona_vacuum import PersonaVacuum  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
# Doubles
# ─────────────────────────────────────────────────────────────────────────────


class _StubBus:
    def __init__(self):
        self.published: List[Any] = []
        self._subs: Dict[str, List[Callable]] = {}

    def publish(self, thought=None, **kwargs):
        if thought is None:
            class _T:
                pass
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


class _StubAdapter:
    def prompt(self, messages, system, max_tokens):
        class _R:
            text = "."
            model = "stub"
            usage = {"total_tokens": 1}
        return _R()


def _neutral_state_vault() -> AureonVault:
    v = AureonVault()
    v.love_amplitude = 0.5
    v.gratitude_score = 0.5
    v.dominant_chakra = "solar"
    v.dominant_frequency_hz = 432.0
    v.cortex_snapshot = {"delta": 0.2, "theta": 0.2, "alpha": 0.2, "beta": 0.2, "gamma": 0.2}
    # A known card so the fingerprint is non-empty and stable.
    v.add(VaultContent.build(category="seed", source_topic="seed.init", payload={"x": 1}))
    return v


# ─────────────────────────────────────────────────────────────────────────────
# AffinityChorus basics
# ─────────────────────────────────────────────────────────────────────────────


def test_chorus_add_and_merge_averages_contributions():
    """Averaging makes the merged map count-invariant so two nodes see the
    same vector regardless of how many peers have reported so far."""
    chorus = AffinityChorus()
    chorus.add("alpha", {"painter": 1.0, "engineer": 2.0})
    chorus.add("beta",  {"painter": 0.5, "engineer": 3.0, "mystic": 1.0})
    merged = chorus.merged()
    # sums over 2 peers / 2
    assert merged["painter"] == pytest.approx(0.75)
    assert merged["engineer"] == pytest.approx(2.5)
    # mystic only contributed by one peer but the divisor is still peer count
    assert merged["mystic"] == pytest.approx(0.5)


def test_chorus_merge_with_self_scores_does_not_double_count_own_peer_id():
    chorus = AffinityChorus()
    chorus.add("me",   {"engineer": 10.0})
    chorus.add("peer", {"engineer":  1.0})
    merged = chorus.merged(self_scores={"engineer": 10.0}, self_peer_id="me")
    # "me" loop entry skipped; averaged over {peer loop, self_scores} = 2 contributions
    # (10 + 1) / 2 = 5.5
    assert merged["engineer"] == pytest.approx(5.5)


def test_chorus_replaces_existing_peer_id():
    chorus = AffinityChorus()
    chorus.add("alpha", {"mystic": 5.0})
    chorus.add("alpha", {"mystic": 1.0})  # overwrite, not add
    assert chorus.merged()["mystic"] == pytest.approx(1.0)


def test_chorus_prunes_stale_entries():
    chorus = AffinityChorus(ttl_s=0.05)
    chorus.add("old", {"engineer": 9.0}, ts=time.time() - 1.0)
    chorus.add("new", {"engineer": 2.0})
    merged = chorus.merged()
    assert merged["engineer"] == pytest.approx(2.0)
    assert chorus.peer_count() == 1


def test_chorus_publish_round_trips_through_bus():
    bus = _StubBus()
    chorus = AffinityChorus(thought_bus=bus)
    chorus.start()
    chorus.publish("alpha", {"engineer": 1.5})
    # The published message was captured locally AND re-entered via the
    # subscription — the local entry should still only count once.
    assert chorus.merged()["engineer"] == pytest.approx(1.5)
    # And the bus saw exactly one publication.
    pub_topics = [t.topic for t in bus.published if t.topic == AffinityChorus.TOPIC]
    assert len(pub_topics) == 1


def test_chorus_ignores_malformed_payloads():
    bus = _StubBus()
    chorus = AffinityChorus(thought_bus=bus)
    chorus.start()
    # Missing peer_id
    bus.publish(topic=AffinityChorus.TOPIC, payload={"scores": {"engineer": 1.0}})
    # Missing scores
    bus.publish(topic=AffinityChorus.TOPIC, payload={"peer_id": "x"})
    # Non-numeric scores
    bus.publish(topic=AffinityChorus.TOPIC, payload={"peer_id": "y", "scores": {"engineer": "nope"}})
    assert chorus.peer_count() == 0


# ─────────────────────────────────────────────────────────────────────────────
# Deterministic-seed helpers
# ─────────────────────────────────────────────────────────────────────────────


def test_vault_fingerprint_seed_is_stable():
    v = _neutral_state_vault()
    s1 = vault_fingerprint_seed(v)
    s2 = vault_fingerprint_seed(v)
    assert s1 == s2
    assert isinstance(s1, int)


def test_vault_fingerprint_seed_changes_with_state():
    v1 = _neutral_state_vault()
    v2 = _neutral_state_vault()
    v2.add(VaultContent.build(category="new", source_topic="new.topic", payload={"x": 99}))
    assert vault_fingerprint_seed(v1) != vault_fingerprint_seed(v2)


# ─────────────────────────────────────────────────────────────────────────────
# PersonaVacuum integration — the actual unity test
# ─────────────────────────────────────────────────────────────────────────────


def _vacuum(bus: _StubBus, vault: AureonVault, chorus: AffinityChorus,
            peer_id: str, *, seed_fn=None) -> PersonaVacuum:
    """Build a vacuum wired to the shared bus + chorus.

    When seed_fn is None the vacuum derives its seed from the merged
    affinity map — two vacuums that see the same merged map agree on
    the winner without any operator-supplied seed.
    """
    personas = build_aureon_personas(adapter=_StubAdapter())
    return PersonaVacuum(
        personas=personas,
        thought_bus=bus,
        vault=vault,
        chorus=chorus,
        peer_id=peer_id,
        seed_fn=seed_fn,
        temperature=0.5,
    )


def test_two_vacuums_with_shared_chorus_agree_under_quorum():
    """The core unity test. With a quorum step — every vacuum publishes
    its per-persona affinity BEFORE anyone samples — two vacuums must
    pick the same persona every tick. This is the "many thoughts, one
    unified speech" contract.
    """
    bus = _StubBus()
    chorus = AffinityChorus(thought_bus=bus)
    chorus.start()

    # Two independent vaults seeded from the same state (simulating
    # post-gossip convergence — mesh sync has caught both up).
    vault_a = _neutral_state_vault()
    vault_b = _neutral_state_vault()

    va = _vacuum(bus, vault_a, chorus, peer_id="node-a")
    vb = _vacuum(bus, vault_b, chorus, peer_id="node-b")

    for tick in range(25):
        # Phase 1 — every vacuum contributes its local thought
        va.contribute_affinity(vault_a)
        vb.contribute_affinity(vault_b)

        # Phase 2 — each vacuum samples. Both see the full merged map.
        state_a = va._build_state(vault_a)
        state_b = vb._build_state(vault_b)
        winner_a, _, _ = va._sample(state_a)
        winner_b, _, _ = vb._sample(state_b)
        assert winner_a == winner_b, (
            f"tick {tick}: winners diverged — {winner_a} vs {winner_b}"
        )


def test_unity_survives_many_ticks_when_state_evolves_in_lockstep():
    """State evolves between ticks; as long as both vacuums see the same
    state at each tick, the unity guarantee holds."""
    bus = _StubBus()
    chorus = AffinityChorus(thought_bus=bus)
    chorus.start()

    vault_a = _neutral_state_vault()
    vault_b = _neutral_state_vault()

    va = _vacuum(bus, vault_a, chorus, peer_id="node-a")
    vb = _vacuum(bus, vault_b, chorus, peer_id="node-b")

    for tick in range(30):
        # Mutate both vaults IDENTICALLY to simulate mesh-sync.
        for v in (vault_a, vault_b):
            v.love_amplitude = 0.3 + (tick % 7) * 0.1
            v.cortex_snapshot = {"gamma": 0.1 + (tick % 5) * 0.1,
                                 "delta": 0.1, "theta": 0.1,
                                 "alpha": 0.1, "beta": 0.1}

        va.contribute_affinity(vault_a)
        vb.contribute_affinity(vault_b)

        state_a = va._build_state(vault_a)
        state_b = vb._build_state(vault_b)
        winner_a, _, _ = va._sample(state_a)
        winner_b, _, _ = vb._sample(state_b)
        assert winner_a == winner_b, f"tick {tick}: {winner_a} vs {winner_b}"


def test_without_chorus_two_vacuums_can_diverge():
    """Sanity check — the chorus is doing the work, not some other coincidence."""
    bus = _StubBus()
    vault = _neutral_state_vault()

    personas_a = build_aureon_personas(adapter=_StubAdapter())
    personas_b = build_aureon_personas(adapter=_StubAdapter())
    va = PersonaVacuum(personas=personas_a, thought_bus=bus, vault=vault,
                       rng=random.Random(1), temperature=1.0)
    vb = PersonaVacuum(personas=personas_b, thought_bus=bus, vault=vault,
                       rng=random.Random(2), temperature=1.0)

    divergence = 0
    for _ in range(50):
        va.observe(vault)
        vb.observe(vault)
        if va.last_winner != vb.last_winner:
            divergence += 1
    assert divergence > 0, (
        "without chorus + seed_fn, two independent vacuums should disagree "
        "at least sometimes; if they never do, the test is insensitive"
    )


def test_vacuum_publishes_own_affinity_to_chorus():
    bus = _StubBus()
    chorus = AffinityChorus(thought_bus=bus)
    chorus.start()
    vault = _neutral_state_vault()
    va = _vacuum(bus, vault, chorus, peer_id="node-a")
    va.observe(vault)
    # Chorus should now have node-a's contribution recorded.
    pids = [c["peer_id"] for c in chorus.contributions()]
    assert "node-a" in pids


def test_chorus_merged_reflects_peer_contributions():
    """Peer contributions shift the merged map toward their values —
    with mean semantics, merged == (local + remote) / 2."""
    bus = _StubBus()
    chorus = AffinityChorus(thought_bus=bus)
    chorus.start()
    # Pre-seed a peer's contribution before the local vacuum runs.
    remote_scores = {n: 1.0 for n in [
        "painter", "artist", "quantum_physicist", "philosopher", "child",
        "elder", "mystic", "engineer", "left", "right",
    ]}
    chorus.add("remote-peer", remote_scores)
    vault = _neutral_state_vault()
    va = _vacuum(bus, vault, chorus, peer_id="node-a")

    state = va._build_state(vault)
    local = {n: p.compute_affinity(state) for n, p in va._personas.items()}
    merged = chorus.merged(self_scores=local, self_peer_id="node-a")
    # With two contributions (remote-peer loop entry + self_scores), the
    # merged map is the arithmetic mean.
    for name, local_value in local.items():
        expected = (local_value + 1.0) / 2.0
        assert abs(merged[name] - expected) < 1e-9, (
            f"{name}: merged {merged[name]} != expected mean {expected}"
        )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
