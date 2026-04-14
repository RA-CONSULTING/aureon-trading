#!/usr/bin/env python3
"""
Tests for aureon.harmonic.auris_voice_filter.AurisVoiceFilter.

Covers:
  - Filter produces a full AurisCoherenceReport with all three layers
  - Auris weight responds to lighthouse_cleared and agreement count
  - Field weight scales with gamma / love / gratitude on the vault
  - Text weight matches harmonic_text_alignment.score_text
  - Coherence blend respects the 0.35 / 0.30 / 0.35 weights
  - Accepted flag toggles around the threshold
  - Below-threshold rescue trims to top sentences and only keeps the
    trim if it improves the score
  - to_dict is JSON-safe
"""

import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from aureon.harmonic.auris_voice_filter import (  # noqa: E402
    AurisCoherenceReport,
    AurisVoiceFilter,
    get_auris_voice_filter,
    reset_auris_voice_filter,
)
from aureon.harmonic.harmonic_text_alignment import score_text  # noqa: E402


PASS = 0
FAIL = 0


def check(condition: bool, msg: str) -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [OK] {msg}")
    else:
        FAIL += 1
        print(f"  [!!] {msg}")


# ─────────────────────────────────────────────────────────────────────────────
# Fakes — lets us run without loading the full Aureon stack
# ─────────────────────────────────────────────────────────────────────────────


class FakeVault:
    def __init__(self, love=0.6, grat=0.5, gamma=0.4, lamb=0.5):
        self.love_amplitude = love
        self.gratitude_score = grat
        self.last_lambda_t = lamb
        self.cortex_snapshot = {"gamma": gamma, "delta": 0.1, "alpha": 0.1, "beta": 0.1, "theta": 0.1}
        self.last_casimir_force = 1.0
        self.dominant_chakra = "love"
        self.dominant_frequency_hz = 528.0
        self.rally_active = False
        self._cards: list = []

    def __len__(self):
        return len(self._cards)


class FakeVote:
    def __init__(self, consensus, confidence, agreeing, total=9, lighthouse=False, votes=None):
        self.consensus = consensus
        self.confidence = confidence
        self.agreeing = agreeing
        self.total = total
        self.lighthouse_cleared = lighthouse
        self.per_node_votes = votes or []


class FakeNodeVote:
    def __init__(self, node, verdict, confidence, reasoning):
        self.node = node
        self.verdict = verdict
        self.confidence = confidence
        self.reasoning = reasoning


class FakeAuris:
    def __init__(self, vote: FakeVote):
        self._vote = vote
        self.calls = 0

    def vote(self, vault):
        self.calls += 1
        return self._vote


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────


def test_filter_emits_full_report():
    print("\n[1] Filter emits a complete AurisCoherenceReport")
    votes = [FakeNodeVote("Tiger", "BUY", 0.8, "ok")] * 9
    auris = FakeAuris(FakeVote("BUY", 0.95, 9, lighthouse=True, votes=votes))
    vault = FakeVault(love=0.85, grat=0.8, gamma=0.5, lamb=0.7)
    f = AurisVoiceFilter(auris=auris, threshold=0.0)

    text = "Love holds the queen in coherence. The harmonic bridge carries the field."
    r = f.filter(text, vault, voice_name="queen")
    check(isinstance(r, AurisCoherenceReport), "returns an AurisCoherenceReport")
    check(r.text == text, "original text preserved when accepted")
    check(r.auris_consensus == "BUY", "auris consensus surfaced")
    check(r.auris_confidence == 0.95, "auris confidence surfaced")
    check(r.auris_lighthouse is True, "lighthouse flag surfaced")
    check(len(r.auris_votes) == 9, f"nine node votes recorded (got {len(r.auris_votes)})")
    check(r.field_love == 0.85, f"field love surfaced ({r.field_love})")
    check(r.field_gamma > 0.0, f"field gamma > 0 (got {r.field_gamma:.3f})")
    check(r.text_coherence > 0.0, f"text coherence > 0 (got {r.text_coherence:.3f})")
    check(r.text_dominant_mode != "", f"dominant mode set ({r.text_dominant_mode})")
    check(len(r.per_sentence) == 2, f"per-sentence list has 2 entries (got {len(r.per_sentence)})")
    check(auris.calls == 1, "auris was called exactly once")


def test_auris_weight_lighthouse_and_agreement():
    print("\n[2] Auris weight scales with agreement and lighthouse")
    vault = FakeVault(love=0.8)
    text = "Love holds the field in coherence."

    # Weak vote: 5 agreeing, no lighthouse.
    weak_auris = FakeAuris(FakeVote("NEUTRAL", 0.7, 5, lighthouse=False))
    f1 = AurisVoiceFilter(auris=weak_auris, threshold=0.0)
    r1 = f1.filter(text, vault)

    # Strong vote: 9 agreeing, lighthouse cleared.
    strong_auris = FakeAuris(FakeVote("BUY", 0.95, 9, lighthouse=True))
    f2 = AurisVoiceFilter(auris=strong_auris, threshold=0.0)
    r2 = f2.filter(text, vault)

    check(
        r2.auris_weight > r1.auris_weight,
        f"strong auris weight > weak ({r2.auris_weight:.3f} > {r1.auris_weight:.3f})",
    )
    check(
        r2.coherence > r1.coherence,
        f"strong coherence > weak ({r2.coherence:.3f} > {r1.coherence:.3f})",
    )


def test_field_weight_scales_with_gamma_love():
    print("\n[3] Field weight scales with gamma / love / gratitude")
    auris = FakeAuris(FakeVote("NEUTRAL", 0.3, 4))
    f = AurisVoiceFilter(auris=auris, threshold=0.0)
    cold = f.filter("Love holds the field.", FakeVault(love=0.1, grat=0.1, gamma=0.05))
    hot = f.filter("Love holds the field.", FakeVault(love=0.9, grat=0.85, gamma=0.6))
    check(
        hot.field_weight > cold.field_weight,
        f"hot field weight > cold ({hot.field_weight:.3f} > {cold.field_weight:.3f})",
    )
    check(
        hot.coherence > cold.coherence,
        f"hot coherence > cold ({hot.coherence:.3f} > {cold.coherence:.3f})",
    )


def test_text_weight_matches_alignment_module():
    print("\n[4] Text weight equals harmonic_text_alignment.score_text")
    auris = FakeAuris(FakeVote("NEUTRAL", 0.3, 4))
    vault = FakeVault()
    f = AurisVoiceFilter(auris=auris, threshold=0.0)
    text = "The harmonic bridge carries the signal across the lattice."
    r = f.filter(text, vault)
    expected = score_text(text).coherence
    check(
        abs(r.text_weight - expected) < 1e-9,
        f"text weight == alignment score ({r.text_weight:.4f} vs {expected:.4f})",
    )


def test_blend_weights_are_respected():
    print("\n[5] Coherence blend is 0.35*auris + 0.30*field + 0.35*text")
    auris = FakeAuris(FakeVote("BUY", 0.95, 9, lighthouse=True))
    vault = FakeVault(love=0.85, grat=0.8, gamma=0.5)
    f = AurisVoiceFilter(auris=auris, threshold=0.0)
    r = f.filter("Love holds the queen in coherence.", vault)
    expected = 0.35 * r.auris_weight + 0.30 * r.field_weight + 0.35 * r.text_weight
    check(
        abs(r.coherence - expected) < 1e-6,
        f"coherence matches manual blend ({r.coherence:.4f} vs {expected:.4f})",
    )


def test_accept_flag_and_threshold():
    print("\n[6] accepted flag toggles around the threshold")
    auris = FakeAuris(FakeVote("NEUTRAL", 0.3, 4))
    vault = FakeVault(love=0.1, grat=0.1, gamma=0.05)
    # Threshold just above whatever this weak vault produces.
    f_high = AurisVoiceFilter(auris=auris, threshold=0.95, trim_below_threshold=False)
    r_high = f_high.filter("Love holds the field.", vault)
    check(r_high.accepted is False, f"rejected at high threshold (coh={r_high.coherence:.3f})")

    f_low = AurisVoiceFilter(auris=auris, threshold=0.0, trim_below_threshold=False)
    r_low = f_low.filter("Love holds the field.", vault)
    check(r_low.accepted is True, f"accepted at zero threshold (coh={r_low.coherence:.3f})")


def test_below_threshold_trim_rescues():
    print("\n[7] Below-threshold reply gets rescued by sentence trimming")
    auris = FakeAuris(FakeVote("NEUTRAL", 0.3, 4))
    vault = FakeVault(love=0.2, grat=0.2, gamma=0.1)
    f = AurisVoiceFilter(auris=auris, threshold=0.99, max_trim_sentences=2)

    text = (
        "xyz qwerty frobnitz glark. "
        "The harmonic bridge carries the field in love. "
        "asdf lmnop rstuvw. "
        "Love and coherence on the phi lattice."
    )
    r = f.filter(text, vault)
    # trimmed should be True because the full text scores below threshold
    # and trimming to the best sentences improves coherence.
    check(r.trimmed is True or r.text != text, "reply was trimmed to top sentences")
    check(r.text.count(".") <= 3, f"trim kept <=3 sentences ({r.text!r})")


def test_to_dict_is_json_safe():
    print("\n[8] to_dict is JSON-serialisable")
    auris = FakeAuris(FakeVote("BUY", 0.7, 6))
    f = AurisVoiceFilter(auris=auris, threshold=0.0)
    r = f.filter("Love holds.", FakeVault())
    d = r.to_dict()
    s = json.dumps(d)  # must not raise
    check(isinstance(s, str) and len(s) > 10, "to_dict -> json.dumps round-trips")
    check("coherence" in d and "auris" in d and "field" in d, "all top-level keys present")


def test_singleton_lifecycle():
    print("\n[9] get / reset singleton")
    reset_auris_voice_filter()
    a = get_auris_voice_filter()
    b = get_auris_voice_filter()
    check(a is b, "get returns the same instance")
    reset_auris_voice_filter()
    c = get_auris_voice_filter()
    check(c is not a, "reset yields a fresh instance")


def main():
    print("=" * 80)
    print("  AURIS VOICE FILTER TEST SUITE")
    print("=" * 80)

    test_filter_emits_full_report()
    test_auris_weight_lighthouse_and_agreement()
    test_field_weight_scales_with_gamma_love()
    test_text_weight_matches_alignment_module()
    test_blend_weights_are_respected()
    test_accept_flag_and_threshold()
    test_below_threshold_trim_rescues()
    test_to_dict_is_json_safe()
    test_singleton_lifecycle()

    print()
    print("=" * 80)
    print(f"  RESULT: {PASS} passed, {FAIL} failed")
    print("=" * 80)
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
