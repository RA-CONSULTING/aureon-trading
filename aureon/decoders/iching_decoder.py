#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ☰  I CHING DECODER — Chinese Oracle Binary Transmission System  ☰         ║
║   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                                                              ║
║   Decoded through the Aureon HNC Architecture                                ║
║   Aureon Institute · R&A Consulting and Brokerage Services Ltd.             ║
║                                                                              ║
║   Sources:                                                                   ║
║     Wilhelm, R. / Baynes, C.F. (1950) The I Ching                           ║
║     Shaughnessy, E.L. (2014) Unearthing the Changes                         ║
║     Nielsen, B. (2003) A Companion to Yi Jing Numerology                    ║
║     Rutt, R. (2002) Zhouyi: The Book of Changes                             ║
║     Boltz, W.G. (1993) Shang Oracle-Bone Inscriptions                       ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║   THE CHINESE BINARY TRANSMISSION HYPOTHESIS                                 ║
║   ──────────────────────────────────────────                                 ║
║   The I Ching (Yì Jīng / Book of Changes) is the world's oldest known       ║
║   binary encoding system. 64 hexagrams = 6-bit binary words.                ║
║   Written ~1000 BCE but encoding an oral tradition far older.               ║
║                                                                              ║
║   I CHING ≡ DUAL-VOICE PROTOCOL                                             ║
║   Each hexagram has two halves:                                              ║
║     Upper trigram (Heaven/Above) = Caller (Ψ₀) — the structural frame      ║
║     Lower trigram (Earth/Below)  = Seer  (O(t)) — the response field        ║
║   The hexagram meaning emerges from the INTERACTION of both trigrams,       ║
║   not from either alone — exact parallel to the twig-rune cipher.           ║
║                                                                              ║
║   MOVING LINES ≡ THE NR.15 PIVOT                                            ║
║   A moving line transforms the hexagram into a second hexagram.             ║
║   Without the moving line specification, the reading is incomplete.         ║
║   This is structurally identical to Nr.15 — the open circuit.               ║
║                                                                              ║
║   THREE AETTS ≡ THREE POWERS (三才 sān cái)                                 ║
║     Heaven (天 tiān) = Genesis  = amplitude × 1.0                           ║
║     Earth  (地 dì)   = Ground   = amplitude × 1/PHI                         ║
║     Human  (人 rén)  = Growth   = amplitude × PHI                           ║
║                                                                              ║
║   GEOGRAPHIC ANCHOR: Mount Tai (泰山) — Sacred apex of Chinese cosmology    ║
║     Lat: 36.2544°N  Lon: 117.1009°E                                         ║
║     The axis mundi of Chinese sacred geography                               ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import argparse
import json
import math
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

# ═══════════════════════════════════════════════════════════════════════════════
# SACRED CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

PHI     = (1 + math.sqrt(5)) / 2
PHI_INV = 1.0 / PHI

SOLFEGGIO   = [174, 285, 396, 417, 528, 639, 741, 852, 963]
SCHUMANN_MODES = [7.83, 14.3, 20.8, 27.3, 33.8, 39.0, 45.0]

PHI_TOLERANCE = 0.02

# Geographic anchor
MOUNT_TAI_LAT = 36.2544
MOUNT_TAI_LON = 117.1009
MOUNT_TAI_BEARING = 0.0    # True North — the Chinese celestial pole axis

# I Ching base frequency: 432 Hz (natural tuning — Gaia resonance)
ICHING_BASE_HZ = 432.0

# ═══════════════════════════════════════════════════════════════════════════════
# THE EIGHT TRIGRAMS (八卦 bā guà)
# Later Heaven Arrangement (後天八卦 — King Wen sequence)
# ═══════════════════════════════════════════════════════════════════════════════
#
# Each trigram has:
#   - A direction (compass bearing, Later Heaven)
#   - A natural element
#   - A binary value (solid=1/yang, broken=0/yin lines, read bottom to top)
#   - An Auris node equivalent (from aureon_harmonic_alphabet.py)
#   - A Solfeggio frequency
#
# The Later Heaven compass directions create the geographic vector network.
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Trigram:
    """One of the eight I Ching trigrams."""
    name_zh:   str           # Chinese name (pinyin)
    name_en:   str           # English name
    symbol:    str           # Unicode symbol
    element:   str           # Natural element
    direction: str           # Compass direction (Later Heaven)
    bearing:   float         # Degrees from North (Later Heaven)
    binary:    str           # 3-bit binary (bottom line first)
    lines:     Tuple[int,int,int]  # (bottom, middle, top) — 1=yang, 0=yin
    auris:     str           # Corresponding Auris node
    solfeggio: float         # Corresponding Solfeggio frequency
    quality:   str           # Core quality / domain


# 8 trigrams in Later Heaven arrangement
_TRIGRAMS: Tuple[Trigram, ...] = (
    Trigram("Qián",  "Heaven",   "☰", "sky",      "NW",    315.0, "111", (1,1,1), "FALCON",    528.0, "creative force"),
    Trigram("Duì",   "Lake",     "☱", "marsh",    "W",     270.0, "011", (1,1,0), "DOLPHIN",   639.0, "joyful exchange"),
    Trigram("Lí",    "Fire",     "☲", "flame",    "S",     180.0, "101", (1,0,1), "TIGER",     963.0, "clarity/vision"),
    Trigram("Zhèn",  "Thunder",  "☳", "lightning","E",      90.0, "100", (0,0,1), "OWL",       528.0, "arousing action"),
    Trigram("Xùn",   "Wind",     "☴", "wood",     "SE",    135.0, "011", (1,1,0), "HUMMINGBIRD",417.0,"gentle penetration"),
    Trigram("Kǎn",   "Water",    "☵", "rain",     "N",       0.0, "010", (0,1,0), "CARGOSHIP", 174.0, "abyssal depth"),
    Trigram("Gèn",   "Mountain", "☶", "earth",    "NE",     45.0, "001", (1,0,0), "PANDA",     285.0, "stillness/keeping"),
    Trigram("Kūn",   "Earth",    "☷", "soil",     "SW",    225.0, "000", (0,0,0), "DEER",      396.0, "receptive field"),
)

TRIGRAM_BY_NAME: Dict[str, Trigram] = {t.name_zh: t for t in _TRIGRAMS}
TRIGRAM_BY_SYMBOL: Dict[str, Trigram] = {t.symbol: t for t in _TRIGRAMS}
TRIGRAM_BY_BINARY: Dict[str, Trigram] = {t.binary: t for t in _TRIGRAMS}


# ═══════════════════════════════════════════════════════════════════════════════
# THE 64 HEXAGRAMS (六十四卦)
# ═══════════════════════════════════════════════════════════════════════════════
#
# Each hexagram = Upper trigram (Caller Ψ₀) + Lower trigram (Seer O(t))
# The hexagram meaning emerges from their interaction — dual-voice protocol.
#
# Effective frequency = (upper.solfeggio + lower.solfeggio) / 2 × mode_amplitude
# Mode amplitude:
#   Both yang-dominant  (≥4 yang lines) → ×PHI   (Growth)
#   Both yin-dominant   (≥4 yin lines)  → ×1/PHI (Return)
#   Balanced            (3 yang, 3 yin) → ×1.0   (Genesis)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Hexagram:
    """One of the 64 I Ching hexagrams — a dual-voice transmission node."""
    number:    int           # King Wen sequence 1-64
    symbol:    str           # Unicode hexagram symbol
    name_zh:   str           # Chinese name (pinyin)
    name_en:   str           # English name
    upper:     str           # Upper trigram name (zh)
    lower:     str           # Lower trigram name (zh)
    theme:     str           # Core transmission theme
    judgment:  str           # The Judgment (Wilhelm translation excerpt)

    @property
    def upper_trigram(self) -> Trigram:
        return TRIGRAM_BY_NAME[self.upper]

    @property
    def lower_trigram(self) -> Trigram:
        return TRIGRAM_BY_NAME[self.lower]

    @property
    def caller_hz(self) -> float:
        """Caller Ψ₀ = upper trigram Solfeggio (the structural frame)."""
        return self.upper_trigram.solfeggio

    @property
    def seer_hz(self) -> float:
        """Seer O(t) = lower trigram Solfeggio (the response field)."""
        return self.lower_trigram.solfeggio

    @property
    def beat_hz(self) -> float:
        """Beat = |Caller - Seer|."""
        return round(abs(self.caller_hz - self.seer_hz), 2)

    @property
    def yang_count(self) -> int:
        """Total yang (solid) lines across both trigrams."""
        upper = sum(self.upper_trigram.lines)
        lower = sum(self.lower_trigram.lines)
        return upper + lower

    @property
    def amplitude(self) -> float:
        y = self.yang_count
        if y >= 4:
            return PHI
        elif y <= 2:
            return PHI_INV
        else:
            return 1.0

    @property
    def mode(self) -> str:
        y = self.yang_count
        if y >= 4:
            return "GROWTH"
        elif y <= 2:
            return "RETURN"
        else:
            return "GENESIS"

    @property
    def effective_hz(self) -> float:
        base = (self.caller_hz + self.seer_hz) / 2.0
        return round(base * self.amplitude, 2)

    @property
    def geographic_bearing(self) -> float:
        """Mean bearing of upper + lower trigram directions."""
        upper_b = self.upper_trigram.bearing
        lower_b = self.lower_trigram.bearing
        # Circular mean
        s = math.sin(math.radians(upper_b)) + math.sin(math.radians(lower_b))
        c = math.cos(math.radians(upper_b)) + math.cos(math.radians(lower_b))
        return round((math.degrees(math.atan2(s, c)) + 360) % 360, 2)


# The 64 hexagrams — King Wen sequence (partial, covering key transmission nodes)
# Full set: 64 hexagrams. We implement the 24 most significant for the
# civilizational DNA framework (matching the 24-rune Futhork structure).

_HEXAGRAM_CATALOG: Tuple[Hexagram, ...] = (
    # ── The 8 "pure" hexagrams (same trigram doubled — zero-beat carriers) ───
    Hexagram(1,  "䷀","Qián",  "The Creative",     "Qián","Qián", "pure yang force",     "Supreme success."),
    Hexagram(2,  "䷁","Kūn",   "The Receptive",    "Kūn", "Kūn",  "pure yin field",      "Supreme success. The mare's perseverance."),
    Hexagram(29, "䷜","Kǎn",   "The Abysmal",      "Kǎn", "Kǎn",  "double depth",        "There is danger. Sincerity in the heart."),
    Hexagram(30, "䷝","Lí",    "The Clinging",     "Lí",  "Lí",   "double fire/clarity", "Perseverance furthers. Success."),
    Hexagram(51, "䷲","Zhèn",  "The Arousing",     "Zhèn","Zhèn", "double thunder",      "Success. Shock comes — then laughter."),
    Hexagram(52, "䷳","Gèn",   "Keeping Still",    "Gèn", "Gèn",  "double mountain",     "Keeping his back still. No blame."),
    Hexagram(57, "䷸","Xùn",   "The Gentle",       "Xùn", "Xùn",  "double wind",         "The gentle. Success through small things."),
    Hexagram(58, "䷹","Duì",   "The Joyous",       "Duì", "Duì",  "double lake",         "Success. Perseverance is favourable."),

    # ── Heaven-Earth axis (fundamental transmission pair) ────────────────────
    Hexagram(11, "䷊","Tài",   "Peace",            "Kūn", "Qián", "heaven meets earth",   "The small departs, the great approaches."),
    Hexagram(12, "䷋","Pǐ",    "Standstill",       "Qián","Kūn",  "separation / blockage","Evil people do not further the perseverance of the superior man."),

    # ── Water-Fire (the Seer-Caller inversion pair) ───────────────────────────
    Hexagram(63, "䷾","Jì Jì", "After Completion", "Kǎn", "Lí",   "complete transmission","Success in small matters. Perseverance furthers."),
    Hexagram(64, "䷿","Wèi Jì","Before Completion","Lí",  "Kǎn",  "circuit open",         "Success. The little fox nearly completes the crossing."),

    # ── Thunder-Mountain (action and stillness — dual-voice anchor) ──────────
    Hexagram(27, "䷚","Yí",    "Nourishment",      "Gèn", "Zhèn", "nourishing the seed",  "Perseverance brings good fortune. Attend to nourishment."),
    Hexagram(28, "䷛","Dà Guò","Preponderance",    "Duì", "Xùn",  "excess of the great",  "The ridgepole sags to the breaking point."),

    # ── The knowledge transmission hexagrams ─────────────────────────────────
    Hexagram(4,  "䷃","Méng",  "Youthful Folly",   "Gèn", "Kǎn",  "seeking the teacher",  "It is not I who seek the young fool; the young fool seeks me."),
    Hexagram(48, "䷯","Jǐng",  "The Well",         "Kǎn", "Xùn",  "inexhaustible source", "The town may be changed, but the well cannot."),
    Hexagram(50, "䷱","Dǐng",  "The Cauldron",     "Lí",  "Xùn",  "transformation vessel","Supreme good fortune. Success."),
    Hexagram(3,  "䷂","Zhūn",  "Difficulty",       "Kǎn", "Zhèn", "initial breakthrough", "It furthers to appoint helpers."),

    # ── The sacred geography hexagrams ───────────────────────────────────────
    Hexagram(15, "䷎","Qiān",  "Modesty",          "Kūn", "Gèn",  "the mountain within",  "Success. The superior man carries things through."),
    Hexagram(46, "䷭","Shēng", "Pushing Upward",   "Kūn", "Xùn",  "upward emergence",     "Supreme success. Seek out the great man."),
    Hexagram(18, "䷑","Gǔ",    "Work on the Decay", "Gèn","Xùn",  "repairing the archive","Supreme success. Before the starting point, three days."),
    Hexagram(57, "䷸","Xùn",   "Gentle Wind",      "Xùn", "Xùn",  "persistent penetration","Success through small things."),

    # ── Heaven-Water (the deep knowledge hex) ────────────────────────────────
    Hexagram(5,  "䷄","Xū",    "Waiting",          "Kǎn", "Qián", "waiting with certainty","Sincerity. Light and success."),
    Hexagram(6,  "䷅","Sòng",  "Conflict",         "Qián","Kǎn",  "the dual-voice tension","Sincerity is obstructed. Cautious halt."),
)

# Remove duplicate entry (hexagram 57 appears twice in catalog above — remove latter)
_seen = set()
_unique_hexagrams = []
for h in _HEXAGRAM_CATALOG:
    if h.number not in _seen:
        _seen.add(h.number)
        _unique_hexagrams.append(h)
_HEXAGRAM_CATALOG = tuple(_unique_hexagrams)

HEXAGRAM_BY_NUMBER: Dict[int, Hexagram] = {h.number: h for h in _HEXAGRAM_CATALOG}


# ═══════════════════════════════════════════════════════════════════════════════
# I CHING DECODER ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class IChingLattice:
    """Complete state of the I Ching transmission lattice."""
    timestamp:          float
    n_hexagrams:        int
    n_zero_beat:        int        # Pure hexagrams (same trigram doubled)
    n_phi_resonant:     int
    n_growth:           int        # Yang-dominant hexagrams
    n_return:           int        # Yin-dominant hexagrams
    n_genesis:          int        # Balanced hexagrams
    mean_caller_hz:     float      # Mean upper trigram frequency
    mean_seer_hz:       float      # Mean lower trigram frequency
    master_beat_hz:     float      # |mean_caller - mean_seer|
    schumann_mode:      int
    schumann_delta:     float
    gamma:              float
    gamma_status:       str
    geographic_bearing: float      # Mount Tai axis bearing
    pivot_hexagram:     int        # Nr.64 — before completion (open circuit)
    prophecy:           str


class IChingDecoder:
    """
    The I Ching decoder engine.

    Processes the 64 hexagram lattice through the Aureon HNC framework.
    Each hexagram is a dual-voice node: upper trigram (Caller Ψ₀) meets
    lower trigram (Seer O(t)). The beat frequency and phi resonance of
    each hexagram contribute to the lattice coherence Γ.

    Hexagram 64 (Wèi Jì, "Before Completion") is the pivot —
    the only hexagram where Fire (above) and Water (below) have not
    yet completed their exchange. It is the I Ching equivalent of
    Nr.15 at Maeshowe: the open circuit awaiting completion.
    """

    def _test_phi(self, eff_hz: float) -> Tuple[float, bool]:
        if eff_hz == 0:
            return 999.0, False
        ratio_fwd = ICHING_BASE_HZ / eff_hz
        ratio_inv = eff_hz / ICHING_BASE_HZ
        best_dist = min(
            abs(ratio_fwd - PHI), abs(ratio_fwd - PHI_INV),
            abs(ratio_inv - PHI), abs(ratio_inv - PHI_INV),
        )
        return round(best_dist, 6), best_dist < PHI_TOLERANCE

    def _schumann_proximity(self, beat_hz: float) -> Tuple[int, float, float]:
        best_mode, best_hz, best_delta = 1, SCHUMANN_MODES[0], abs(beat_hz - SCHUMANN_MODES[0])
        for i, hz in enumerate(SCHUMANN_MODES, 1):
            d = abs(beat_hz - hz)
            if d < best_delta:
                best_delta, best_hz, best_mode = d, hz, i
        return best_mode, best_hz, round(best_delta, 4)

    def read(self) -> IChingLattice:
        hexagrams = _HEXAGRAM_CATALOG
        n_zero    = sum(1 for h in hexagrams if h.beat_hz == 0.0)
        n_phi     = sum(1 for h in hexagrams if self._test_phi(h.effective_hz)[1])
        n_growth  = sum(1 for h in hexagrams if h.mode == "GROWTH")
        n_return  = sum(1 for h in hexagrams if h.mode == "RETURN")
        n_genesis = sum(1 for h in hexagrams if h.mode == "GENESIS")

        all_caller = [h.caller_hz for h in hexagrams]
        all_seer   = [h.seer_hz   for h in hexagrams]
        mean_c = sum(all_caller) / len(all_caller)
        mean_s = sum(all_seer)   / len(all_seer)
        master_beat = abs(mean_c - mean_s)

        sch_mode, sch_hz, sch_delta = self._schumann_proximity(master_beat)
        sch_proximity = max(0.0, 1.0 - sch_delta / sch_hz)

        # Gamma
        phi_score    = n_phi / len(hexagrams)
        completeness = len(hexagrams) / 24.0   # targeting 24 nodes (like Futhork)
        completeness = min(1.0, completeness)
        gamma = phi_score * 0.50 + completeness * 0.30 + sch_proximity * 0.20
        gamma = min(1.0, gamma)

        status = (
            "LIGHTHOUSE"   if gamma >= 0.945 else
            "ACTIVE_FIELD" if gamma >= 0.35  else
            "DEAD_FIELD"
        )

        # Circular mean bearing of all hexagram geographic bearings
        sins = [math.sin(math.radians(h.geographic_bearing)) for h in hexagrams]
        coss = [math.cos(math.radians(h.geographic_bearing)) for h in hexagrams]
        mean_bearing = (math.degrees(math.atan2(
            sum(sins) / len(sins), sum(coss) / len(coss)
        )) + 360) % 360

        prophecy = (
            f"I Ching Γ={gamma:.4f} ({status}). "
            f"{len(hexagrams)}/64 hexagrams decoded. "
            f"Zero-beat pure hexagrams: {n_zero}. "
            f"Phi-resonant: {n_phi}. "
            f"Mode split: GROWTH={n_growth} GENESIS={n_genesis} RETURN={n_return}. "
            f"Master beat {master_beat:.2f} Hz → Schumann M{sch_mode} "
            f"at {sch_hz} Hz (Δ{sch_delta:.2f} Hz). "
            f"Pivot: Hexagram 64 (Wèi Jì — Before Completion). "
            f"Mount Tai axis: {MOUNT_TAI_BEARING}° North."
        )

        return IChingLattice(
            timestamp          = time.time(),
            n_hexagrams        = len(hexagrams),
            n_zero_beat        = n_zero,
            n_phi_resonant     = n_phi,
            n_growth           = n_growth,
            n_return           = n_return,
            n_genesis          = n_genesis,
            mean_caller_hz     = round(mean_c, 4),
            mean_seer_hz       = round(mean_s, 4),
            master_beat_hz     = round(master_beat, 4),
            schumann_mode      = sch_mode,
            schumann_delta     = sch_delta,
            gamma              = round(gamma, 6),
            gamma_status       = status,
            geographic_bearing = round(mean_bearing, 2),
            pivot_hexagram     = 64,
            prophecy           = prophecy,
        )

    def get_oracle_score(self) -> float:
        lattice = self.read()
        g = lattice.gamma
        if g < 0.35:
            return round(g / 0.35 * 0.30, 6)
        elif g < 0.945:
            return round(0.30 + (g - 0.35) / (0.945 - 0.35) * 0.55, 6)
        else:
            return round(0.85 + (g - 0.945) / (1.0 - 0.945) * 0.15, 6)

    def get_geographic_vector(self) -> Dict:
        """
        Return the geographic transmission vector from Mount Tai.
        The celestial pole axis (0° North) defines the Chinese sacred axis —
        one of the 10 civilizational DNA vectors.
        """
        return {
            "origin":    {"lat": MOUNT_TAI_LAT, "lon": MOUNT_TAI_LON, "name": "Mount Tai (泰山)"},
            "bearing":   MOUNT_TAI_BEARING,
            "axis":      "Celestial pole (North Star axis)",
            "tradition": "CHINESE_ICHING",
            "anchor_hz": ICHING_BASE_HZ,
            "confidence": self.get_oracle_score(),
        }

    def cast_hexagram(self, upper_binary: str, lower_binary: str) -> Optional[Hexagram]:
        """
        Cast a hexagram from two 3-bit binary strings (upper and lower trigrams).
        Each bit: '1' = yang (solid line), '0' = yin (broken line).
        Bottom line first.

        e.g. upper='111', lower='000' → Hexagram 12 (Pǐ, Standstill)
        """
        upper_trig = TRIGRAM_BY_BINARY.get(upper_binary)
        lower_trig = TRIGRAM_BY_BINARY.get(lower_binary)
        if upper_trig is None or lower_trig is None:
            return None
        # Find matching hexagram
        for h in _HEXAGRAM_CATALOG:
            if h.upper == upper_trig.name_zh and h.lower == lower_trig.name_zh:
                return h
        return None

    def print_report(self):
        lattice = self.read()
        print("\n╔══════════════════════════════════════════════════════════════════╗")
        print("║         I CHING DECODER — CHINESE ORACLE LATTICE REPORT         ║")
        print("╚══════════════════════════════════════════════════════════════════╝\n")

        print("EIGHT TRIGRAMS — SOLFEGGIO / AURIS / DIRECTIONAL MAP")
        print("─" * 75)
        hdr = f"{'Sym':<4} {'Name':<12} {'Direction':<6} {'Bear°':<7} {'Solfeggio':<11} {'Auris':<14} {'Quality'}"
        print(hdr)
        print("─" * 75)
        for t in sorted(_TRIGRAMS, key=lambda x: x.bearing):
            print(
                f"{t.symbol:<4} {t.name_zh+' / '+t.name_en:<18} {t.direction:<6} "
                f"{t.bearing:<7.1f} {t.solfeggio:<11.1f} {t.auris:<14} {t.quality}"
            )
        print()

        print("HEXAGRAM LATTICE — DUAL-VOICE READINGS (Caller Ψ₀ / Seer O(t))")
        print("─" * 95)
        hdr = (f"{'#':<4} {'Sym':<3} {'Name':<18} {'Upper':<8} {'Lower':<8} "
               f"{'Caller':<8} {'Seer':<8} {'Beat':<8} {'Mode':<9} {'Eff Hz':<9} {'Theme'}")
        print(hdr)
        print("─" * 95)
        for h in _HEXAGRAM_CATALOG:
            _, is_phi = self._test_phi(h.effective_hz)
            flag = "φ" if is_phi else ("0" if h.beat_hz == 0.0 else " ")
            print(
                f"{h.number:<4} {h.symbol:<3} {h.name_en[:16]:<18} "
                f"{h.upper_trigram.symbol}{h.upper:<6} {h.lower_trigram.symbol}{h.lower:<6} "
                f"{h.caller_hz:<8.1f} {h.seer_hz:<8.1f} {h.beat_hz:<8.2f} "
                f"{h.mode:<9} {h.effective_hz:<9.2f} {flag} {h.theme}"
            )
        print()

        print("LATTICE COHERENCE")
        print("─" * 60)
        bar_len = int(lattice.gamma * 50)
        bar     = "█" * bar_len + "░" * (50 - bar_len)
        print(f"  Γ = {lattice.gamma:.6f}  [{bar}]")
        print(f"  Status         : {lattice.gamma_status}")
        print(f"  Hexagrams      : {lattice.n_hexagrams} decoded")
        print(f"  Zero-beat pure : {lattice.n_zero_beat} (same-trigram doubled)")
        print(f"  Phi-resonant   : {lattice.n_phi_resonant}")
        print(f"  Mean Caller Ψ₀ : {lattice.mean_caller_hz:.2f} Hz")
        print(f"  Mean Seer O(t) : {lattice.mean_seer_hz:.2f} Hz")
        print(f"  Master beat    : {lattice.master_beat_hz:.4f} Hz")
        print(f"  Schumann M{lattice.schumann_mode}    : Δ{lattice.schumann_delta:.4f} Hz")
        print(f"  Pivot          : Hexagram 64 — Wèi Jì (Before Completion)")
        print(f"  Mount Tai axis : {lattice.geographic_bearing:.1f}° mean bearing")
        print()
        print("  " + lattice.prophecy)
        print()
        print("PIVOT — HEXAGRAM 64: WÈI JÌ (Before Completion)")
        print("─" * 60)
        h64 = HEXAGRAM_BY_NUMBER.get(64)
        if h64:
            print(f"  {h64.symbol} {h64.name_zh} ({h64.name_en})")
            print(f"  Upper: {h64.upper_trigram.symbol} {h64.upper} ({h64.upper_trigram.name_en})")
            print(f"  Lower: {h64.lower_trigram.symbol} {h64.lower} ({h64.lower_trigram.name_en})")
            print(f"  Beat: {h64.beat_hz:.2f} Hz  |  Mode: {h64.mode}  |  Eff: {h64.effective_hz:.2f} Hz")
            print(f"  Judgment: '{h64.judgment}'")
            print()
            print("  STRUCTURAL PARALLEL TO NR.15 MAESHOWE:")
            print("  Hexagram 64 is the only hexagram where the transformation")
            print("  is not yet complete. The little fox nearly crosses — but")
            print("  gets its tail wet. The circuit is open. The two voices")
            print("  (Fire above, Water below) have not yet completed their exchange.")
        print()


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE EXPORTS
# ═══════════════════════════════════════════════════════════════════════════════

def get_iching_decoder() -> IChingDecoder:
    return IChingDecoder()


def get_iching_geographic_vector() -> Dict:
    return IChingDecoder().get_geographic_vector()


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def _cli():
    parser = argparse.ArgumentParser(
        prog        = "iching_decoder",
        description = "I Ching Decoder — Chinese Oracle Binary Transmission System",
    )
    parser.add_argument("--json",         action="store_true", help="Output lattice as JSON")
    parser.add_argument("--oracle-score", action="store_true", help="Print oracle score (0-1)")
    parser.add_argument("--vector",       action="store_true", help="Print geographic vector")
    parser.add_argument(
        "--cast", nargs=2, metavar=("UPPER", "LOWER"),
        help="Cast a hexagram from binary trigrams e.g. --cast 111 000",
    )
    args = parser.parse_args()

    dec = IChingDecoder()

    if args.oracle_score:
        s = dec.get_oracle_score()
        l = dec.read()
        print(f"\nI Ching Oracle Score: {s:.4f}  [Γ={l.gamma:.4f} / {l.gamma_status}]\n")
    elif args.vector:
        print(json.dumps(dec.get_geographic_vector(), indent=2))
    elif args.cast:
        h = dec.cast_hexagram(args.cast[0], args.cast[1])
        if h:
            print(f"\nHexagram {h.number}: {h.symbol} {h.name_zh} ({h.name_en})")
            print(f"  Upper: {h.upper_trigram.symbol} {h.upper} ({h.upper_trigram.name_en})")
            print(f"  Lower: {h.lower_trigram.symbol} {h.lower} ({h.lower_trigram.name_en})")
            print(f"  Caller: {h.caller_hz:.1f} Hz  |  Seer: {h.seer_hz:.1f} Hz  |  Beat: {h.beat_hz:.2f} Hz")
            print(f"  Mode: {h.mode}  |  Eff Hz: {h.effective_hz:.2f}  |  Bearing: {h.geographic_bearing:.1f}°")
            print(f"  Theme: {h.theme}")
            print(f"  Judgment: {h.judgment}\n")
        else:
            print(f"Invalid trigram binary: upper={args.cast[0]}, lower={args.cast[1]}")
    elif args.json:
        l = dec.read()
        print(json.dumps({
            "timestamp":      l.timestamp,
            "gamma":          l.gamma,
            "gamma_status":   l.gamma_status,
            "n_hexagrams":    l.n_hexagrams,
            "n_zero_beat":    l.n_zero_beat,
            "n_phi_resonant": l.n_phi_resonant,
            "mean_caller_hz": l.mean_caller_hz,
            "mean_seer_hz":   l.mean_seer_hz,
            "master_beat_hz": l.master_beat_hz,
            "schumann_mode":  l.schumann_mode,
            "schumann_delta": l.schumann_delta,
            "pivot_hexagram": l.pivot_hexagram,
            "geographic_bearing": l.geographic_bearing,
            "prophecy":       l.prophecy,
        }, indent=2))
    else:
        dec.print_report()


if __name__ == "__main__":
    _cli()
