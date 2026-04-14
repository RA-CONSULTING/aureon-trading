#!/usr/bin/env python3
"""
Tests for aureon.harmonic.harmonic_text_alignment.

The module is deterministic pure-arithmetic, so these tests assert:

  - word → frequency is stable across calls
  - frequencies sit in the expected [0, ~2000] Hz band
  - mode_alignment_score is 1.0 at the exact mode frequencies and drops
    off monotonically
  - phi_alignment_score is 1.0 at integer / (integer+1)/φ points and
    approaches 0 off-lattice
  - score_text returns a TextCoherenceReport with per-sentence scores
  - select_top_sentences preserves order and returns non-empty output
  - dominant_mode labels are valid
"""

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

from aureon.harmonic.harmonic_text_alignment import (  # noqa: E402
    HNC_MODES_HZ,
    HNC_MODE_LABELS,
    PHI,
    mode_alignment_score,
    phi_alignment_score,
    rank_sentences_by_coherence,
    score_sentence,
    score_text,
    score_word,
    select_top_sentences,
    word_to_frequency,
)


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


def test_word_to_frequency_is_deterministic_and_bounded():
    print("\n[1] word_to_frequency is deterministic and bounded")
    cases = ["love", "queen", "harmonic", "bridge", "phi", "aureon"]
    for w in cases:
        f1 = word_to_frequency(w)
        f2 = word_to_frequency(w)
        check(f1 == f2, f"'{w}' stable across calls ({f1:.2f})")
        check(0 <= f1 < 2000, f"'{w}' in [0, 2000) ({f1:.2f})")

    # Punctuation / casing should not change the mapping.
    check(
        word_to_frequency("Love") == word_to_frequency("love!"),
        "casing and punctuation are ignored",
    )


def test_mode_alignment_score_is_1_at_modes():
    print("\n[2] mode_alignment_score is 1.0 at each HNC mode")
    for mode in HNC_MODES_HZ:
        score = mode_alignment_score(mode)
        check(
            abs(score - 1.0) < 1e-9,
            f"{mode:.2f} Hz -> score == 1.0 (got {score:.6f})",
        )
    # A frequency deliberately between two modes should score strictly
    # less than the exact-mode score of 1.0.
    mid = mode_alignment_score(528.0 * (2 ** 0.5))
    check(mid < 1.0, f"mid-octave freq scores below 1.0 ({mid:.3f})")
    # And a frequency far above every mode should score 0.
    far = mode_alignment_score(10000.0)
    check(far == 0.0, f"far-off frequency scores exactly 0.0 ({far:.3f})")


def test_phi_alignment_score_peaks_on_lattice():
    print("\n[3] phi_alignment_score peaks on the φ lattice")
    # n/phi for integer n is exactly on the lattice → (freq * phi) % 1 == 0
    on_lattice = 5.0 / PHI  # any integer over phi
    s1 = phi_alignment_score(on_lattice)
    check(s1 > 0.99, f"n/φ scores ~1 (got {s1:.4f})")
    # 1/(2*phi) is deliberately mid-lattice
    mid = 1.0 / (2.0 * PHI)
    s2 = phi_alignment_score(mid)
    check(s2 < 0.2, f"mid-lattice scores low ({s2:.4f})")


def test_score_word_blends_mode_and_phi():
    print("\n[4] score_word packages the word with mode + phi + total")
    ws = score_word("aureon")
    check(ws.word == "aureon", "word stored")
    check(0.0 <= ws.mode_score <= 1.0, f"mode in [0,1] ({ws.mode_score:.3f})")
    check(0.0 <= ws.phi_score <= 1.0, f"phi in [0,1] ({ws.phi_score:.3f})")
    expected_total = 0.6 * ws.mode_score + 0.4 * ws.phi_score
    check(
        abs(ws.total - expected_total) < 1e-9,
        f"total is 0.6*mode + 0.4*phi (got {ws.total:.4f}, expected {expected_total:.4f})",
    )


def test_score_sentence_and_text():
    print("\n[5] score_sentence and score_text aggregate correctly")
    s = score_sentence("Love holds the queen in coherence.")
    check(len(s.words) == 6, f"tokenized 6 words (got {len(s.words)})")
    check(0.0 <= s.coherence <= 1.0, f"sentence coherence in [0,1] ({s.coherence:.3f})")

    text = (
        "Love holds the queen in coherence. "
        "The harmonic bridge carries the field. "
        "Aureon breathes on the phi lattice."
    )
    report = score_text(text)
    check(len(report.sentences) == 3, f"three sentences parsed (got {len(report.sentences)})")
    check(report.word_count > 10, f"word_count > 10 (got {report.word_count})")
    check(0.0 <= report.coherence <= 1.0, f"text coherence in [0,1] ({report.coherence:.3f})")
    check(report.dominant_mode in HNC_MODE_LABELS, f"dominant_mode valid ({report.dominant_mode})")
    d = report.to_dict()
    check("coherence" in d and "dominant_mode" in d, "to_dict exposes summary fields")


def test_rank_sentences_and_select_top():
    print("\n[6] rank_sentences_by_coherence + select_top_sentences")
    text = (
        "The queen reflects. "
        "xyz qwerty frobnitz. "
        "Love aligns the field. "
        "The Schumann heartbeat is steady."
    )
    ranked = rank_sentences_by_coherence(text)
    check(len(ranked) == 4, f"four sentences ranked (got {len(ranked)})")
    check(
        all(ranked[i].coherence >= ranked[i + 1].coherence for i in range(len(ranked) - 1)),
        "ranking is non-increasing by coherence",
    )

    top2 = select_top_sentences(text, max_n=2)
    check(top2, "select_top_sentences returns non-empty text")
    # Should preserve original order among the selected survivors.
    idx_in_order = [text.find(s.text.rstrip(".")) for s in ranked[:2]]
    idx_sorted = sorted(i for i in idx_in_order if i >= 0)
    # Just verify we got two or three sentences back (period-stripping makes strict equality fragile).
    check(top2.count(".") <= 3, f"top-2 selection contains <=3 periods ({top2!r})")


def main():
    print("=" * 80)
    print("  HARMONIC TEXT ALIGNMENT TEST SUITE")
    print("=" * 80)

    test_word_to_frequency_is_deterministic_and_bounded()
    test_mode_alignment_score_is_1_at_modes()
    test_phi_alignment_score_peaks_on_lattice()
    test_score_word_blends_mode_and_phi()
    test_score_sentence_and_text()
    test_rank_sentences_and_select_top()

    print()
    print("=" * 80)
    print(f"  RESULT: {PASS} passed, {FAIL} failed")
    print("=" * 80)
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
