#!/usr/bin/env python3
"""
Tests for HashResonanceIndex — hash256 as bond, not identity.

What's being proved:
  - bond_strength() follows the saturating log-scale (1=0, monotonic
    from 2 upward, < 1.0)
  - _normalise_payload strips instance keys and rounds numerics
  - Same-semantic events bond regardless of timestamp/content_id
  - Different-semantic events do NOT bond
  - Rebuilding from an existing vault populates the index
  - vault.card.added on the bus triggers indexing in real time
  - Threshold crossings publish standing.wave.bond; only once per
    threshold per fingerprint
  - Bond counts match the number of resonating cards
  - strongest_bonds ranks by count
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
from aureon.vault.aureon_vault import AureonVault, VaultContent  # noqa: E402
from aureon.vault.voice.hash_resonance_index import (  # noqa: E402
    BondRecord,
    HashResonanceIndex,
    _bonding_fingerprint,
    _normalise_payload,
    bond_strength,
)


# ─────────────────────────────────────────────────────────────────────────────
# bond_strength monotonicity
# ─────────────────────────────────────────────────────────────────────────────


def test_bond_strength_for_single_card_is_zero():
    assert bond_strength(1) == 0.0


def test_bond_strength_is_monotonic_and_bounded():
    prev = -1.0
    for n in (2, 3, 5, 8, 13, 21, 55, 144):
        s = bond_strength(n)
        assert 0.0 < s < 1.0
        assert s > prev
        prev = s


def test_bond_strength_for_zero_and_negative_is_zero():
    assert bond_strength(0) == 0.0
    assert bond_strength(-5) == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Normalisation
# ─────────────────────────────────────────────────────────────────────────────


def test_normalise_strips_instance_keys():
    original = {
        "title": "thing",
        "timestamp": 1776400000.5,
        "content_id": "abc",
        "trace_id": "xyz",
        "reflection_id": "rid",
        "payload_value": 42,
    }
    cleaned = _normalise_payload(original)
    assert "timestamp" not in cleaned
    assert "content_id" not in cleaned
    assert "trace_id" not in cleaned
    assert "reflection_id" not in cleaned
    assert cleaned["title"] == "thing"
    assert cleaned["payload_value"] == 42


def test_normalise_rounds_floats():
    assert _normalise_payload({"x": 1.2345678}) == {"x": 1.235}


def test_normalise_handles_nested_structures():
    result = _normalise_payload({
        "outer": {"nested": {"deep": 1.23456, "timestamp": 999}},
        "list": [2.5005, {"ts": 0}, "hi"],
    })
    # 1.23456 → 1.235 under Python's round (bankers)
    assert result["outer"]["nested"]["deep"] == round(1.23456, 3)
    assert "timestamp" not in result["outer"]["nested"]
    # 2.5005 → round to 3dp is 2.501 on most platforms (banker's / IEEE)
    assert result["list"][0] == round(2.5005, 3)
    # list[1] was {"ts": 0} — ts stripped, dict empty
    assert result["list"][1] == {}


# ─────────────────────────────────────────────────────────────────────────────
# _bonding_fingerprint
# ─────────────────────────────────────────────────────────────────────────────


def test_same_semantic_events_produce_same_fingerprint():
    """Two recordings of the same event — different timestamps and sub-3dp
    numeric noise — must produce the same bonding fingerprint."""
    fp1 = _bonding_fingerprint(
        persona="engineer", intent_phrase="author a coherence-audit skill",
        payload={"coherence_gamma": 0.96, "tiger": 0.92, "timestamp": 1.0},
        source_topic="goal.submit.request", category="goal_request",
    )
    fp2 = _bonding_fingerprint(
        persona="engineer", intent_phrase="author a coherence-audit skill",
        # Sub-3dp jitter (values still round to the same 3dp result) +
        # different instance timestamp.
        payload={"coherence_gamma": 0.96002, "tiger": 0.92001, "timestamp": 99.0},
        source_topic="goal.submit.request", category="goal_request",
    )
    assert fp1 == fp2, "timestamp + sub-rounding differences must not break the bond"


def test_differences_at_3dp_produce_different_fingerprints():
    """Values that round to DIFFERENT 3dp results must not bond — otherwise
    the bonding hash would be a too-coarse match."""
    fp1 = _bonding_fingerprint(
        persona="engineer", intent_phrase="X",
        payload={"v": 0.960}, source_topic="t", category="c",
    )
    fp2 = _bonding_fingerprint(
        persona="engineer", intent_phrase="X",
        payload={"v": 0.961}, source_topic="t", category="c",
    )
    assert fp1 != fp2


def test_different_personas_produce_different_fingerprints():
    base = dict(intent_phrase="do a thing", payload={"n": 1},
                source_topic="t", category="c")
    fp_a = _bonding_fingerprint(persona="engineer", **base)
    fp_b = _bonding_fingerprint(persona="mystic", **base)
    assert fp_a != fp_b


def test_missing_persona_falls_back_to_category():
    fp = _bonding_fingerprint(
        persona="", intent_phrase="", payload={"n": 1},
        source_topic="t.a", category="cat.a",
    )
    assert isinstance(fp, str)
    assert len(fp) == 32


# ─────────────────────────────────────────────────────────────────────────────
# Index behaviour
# ─────────────────────────────────────────────────────────────────────────────


def _build():
    bus = ThoughtBus()
    vault = AureonVault()
    vault._thought_bus = bus
    index = HashResonanceIndex(vault=vault, thought_bus=bus)
    index.start()
    return bus, vault, index


def test_same_event_bonds():
    bus, vault, index = _build()
    for i in range(5):
        vault.ingest(
            topic="goal.submit.request",
            payload={
                "text": "author a coherence-audit skill",
                "proposed_by_persona": "engineer",
                "urgency": 0.9,
                "timestamp": time.time() + i,  # deliberately varies
            },
        )
    summary = index.summary()
    # Five cards; all should bond to one fingerprint.
    assert summary["total_cards"] == 5
    assert summary["unique_fingerprints"] == 1
    assert summary["max_bond_count"] == 5
    assert summary["max_bond_strength"] == round(bond_strength(5), 4)


def test_different_events_do_not_bond():
    bus, vault, index = _build()
    vault.ingest("goal.submit.request", {
        "text": "author a coherence-audit skill",
        "proposed_by_persona": "engineer",
    })
    vault.ingest("goal.submit.request", {
        "text": "render cymatic SVG for wedding",
        "proposed_by_persona": "artist",
    })
    summary = index.summary()
    assert summary["unique_fingerprints"] == 2
    assert summary["max_bond_count"] == 1


def test_threshold_crossings_publish_exactly_once():
    bus, vault, index = _build()
    index.thresholds = [2, 4]
    received: List[Thought] = []
    bus.subscribe("standing.wave.bond", lambda t: received.append(t))

    for i in range(5):
        vault.ingest("t.topic", {
            "text": "do X", "proposed_by_persona": "engineer", "i_var": i,
        })
    # Normalisation keeps the i_var key — DIFFERENT VALUES bond separately.
    # Use a truly identical payload so all five bond:
    received.clear()
    for _ in range(5):
        vault.ingest("t.topic", {
            "text": "do Y", "proposed_by_persona": "engineer",
        })
    # With thresholds [2, 4], we should get 2 bond events (crossing 2 then 4).
    topics = [t.payload["threshold_crossed"] for t in received]
    assert sorted(topics) == [2, 4]
    # No double-publishing
    assert len(received) == 2


def test_rebuild_from_vault_populates_index():
    bus, vault, _ = _build()
    # Mute the live index and instead build one after the fact
    vault.ingest("a.topic", {"text": "x", "proposed_by_persona": "engineer"})
    vault.ingest("a.topic", {"text": "x", "proposed_by_persona": "engineer"})
    vault.ingest("b.topic", {"text": "y", "proposed_by_persona": "mystic"})

    fresh = HashResonanceIndex(vault=vault, thought_bus=None)
    n = fresh.rebuild_from_vault()
    assert n == 3
    summary = fresh.summary()
    assert summary["total_cards"] == 3
    assert summary["unique_fingerprints"] == 2
    assert summary["max_bond_count"] == 2


def test_resonating_returns_sibling_cards():
    bus, vault, index = _build()
    ids: List[str] = []
    for _ in range(3):
        c = vault.ingest("goal.submit.request", {
            "text": "same text", "proposed_by_persona": "engineer",
        })
        ids.append(c.content_id)
    siblings = index.resonating(ids[0])
    assert len(siblings) == 3
    assert {c.content_id for c in siblings} == set(ids)


def test_strongest_bonds_ranks_by_count():
    bus, vault, index = _build()
    for _ in range(3):
        vault.ingest("t.a", {"text": "A", "proposed_by_persona": "p"})
    for _ in range(5):
        vault.ingest("t.b", {"text": "B", "proposed_by_persona": "p"})
    top = index.strongest_bonds(n=2)
    assert len(top) == 2
    assert top[0]["count"] == 5
    assert top[1]["count"] == 3


def test_bond_strength_lookup_by_content_id():
    bus, vault, index = _build()
    c = vault.ingest("t.one", {"text": "lone", "proposed_by_persona": "p"})
    assert index.bond_count(index.fingerprint_for_content(c.content_id)) == 1
    assert index.bond_strength(index.fingerprint_for_content(c.content_id)) == 0.0

    for _ in range(2):
        vault.ingest("t.one", {"text": "lone", "proposed_by_persona": "p"})
    fp = index.fingerprint_for_content(c.content_id)
    assert index.bond_count(fp) == 3
    assert index.bond_strength(fp) > 0.2


def test_index_lookup_for_unknown_content_returns_none():
    bus, vault, index = _build()
    assert index.fingerprint_for_content("nonexistent") is None
    assert index.bond_for_content("nonexistent") is None
    assert index.resonating("nonexistent") == []


def test_index_is_idempotent_on_duplicate_bus_events():
    """If somehow vault.card.added fires twice for the same content_id,
    the count should not double."""
    bus, vault, index = _build()
    c = vault.ingest("t.x", {"text": "one", "proposed_by_persona": "p"})
    # Manually republish the same card.added — this should be a no-op.
    bus.publish(Thought(source="aureon_vault", topic="vault.card.added",
                        payload={"content_id": c.content_id,
                                 "harmonic_hash": c.harmonic_hash,
                                 "source_topic": "t.x", "category": "generic"}))
    assert index.bond_count(index.fingerprint_for_content(c.content_id)) == 1


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
