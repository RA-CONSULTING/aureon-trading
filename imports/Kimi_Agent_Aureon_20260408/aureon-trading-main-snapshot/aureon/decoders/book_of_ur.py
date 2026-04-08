#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   𒀭  BOOK OF UR — Sumerian Knowledge Archive Decoder  𒀭                    ║
║   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                                                              ║
║   Decoded through the Aureon HNC Architecture                                ║
║   Aureon Institute · R&A Consulting and Brokerage Services Ltd.             ║
║                                                                              ║
║   Sources:                                                                   ║
║     Kramer, S.N. (1963) The Sumerians                                       ║
║     Black, J. et al. (2004) The Literature of Ancient Sumer                 ║
║     Wolkstein & Kramer (1983) Inanna: Queen of Heaven and Earth             ║
║     Leick, G. (2002) Mesopotamia: The Invention of the City                 ║
║     Electronic Text Corpus of Sumerian Literature (ETCSL)                   ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║   THE SUMERIAN TRANSMISSION HYPOTHESIS                                       ║
║   ──────────────────────────────────────                                     ║
║   The city of Ur was not merely a city — it was a distributed knowledge     ║
║   archive. The Sumerian "me" (divine laws/knowledge sets) were physically    ║
║   encoded in temple storehouses and transferred between cities as objects.  ║
║   This is a literal knowledge transmission protocol, not metaphor.          ║
║                                                                              ║
║   CUNEIFORM ≡ TWIG-RUNE CIPHER                                              ║
║   Cuneiform signs are constructed from three wedge types:                   ║
║     Horizontal wedge (→) : aett-class   (1-7 strokes)                       ║
║     Vertical wedge   (↓) : position    (1-7 strokes)                        ║
║     Diagonal wedge   (↘) : mode        (modifier)                           ║
║   Neither channel alone identifies the sign — both must be read together.   ║
║                                                                              ║
║   INANNA'S SEVEN GATES ≡ SEVEN SOLFEGGIO STAGES                            ║
║   At each of 7 underworld gates, Inanna removes one piece of knowledge      ║
║   (garment/ornament). The descent = stripping the signal to its carrier.   ║
║   The ascent = re-encoding the full knowledge set. This is a 7-stage        ║
║   protocol mapping exactly to the 7 Solfeggio frequencies.                  ║
║                                                                              ║
║   GEOGRAPHIC ANCHOR: City of Ur                                              ║
║     Lat: 30.9626°N  Lon: 46.1031°E                                          ║
║     Ziggurat orientation: ~25° from true north (toward Pleiades rise)       ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import argparse
import json
import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# ═══════════════════════════════════════════════════════════════════════════════
# SACRED CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

PHI     = (1 + math.sqrt(5)) / 2          # 1.618033988749895
PHI_INV = 1.0 / PHI                       # 0.618033988749895

# Solfeggio frequencies (the seven stages of Inanna's descent)
SOLFEGGIO = [174, 285, 396, 417, 528, 639, 741, 852, 963]

# Schumann resonances
SCHUMANN_MODES = [7.83, 14.3, 20.8, 27.3, 33.8, 39.0, 45.0]

# Sumerian sexagesimal base frequency: 60 Hz (base-60 number system)
SEXAGESIMAL_BASE_HZ = 60.0

# Sumerian 7-note diatonic scale (reconstructed from cuneiform tablets,
# ref: Kilmer, A.D. 1974, "The Cult Song with Music from Ancient Ugarit")
# Ratios: 1 : 9/8 : 81/64 : 4/3 : 3/2 : 27/16 : 243/128
SUMERIAN_SCALE_RATIOS = [1.0, 1.125, 1.266, 1.333, 1.5, 1.688, 1.898]
SUMERIAN_BASE_NOTE_HZ = 396.0             # Ni (foundation tone) = UT/396 Hz solfeggio

# Geographic anchor: City of Ur, Mesopotamia
UR_LAT =  30.9626                         # degrees North
UR_LON =  46.1031                         # degrees East
UR_ZIGGURAT_BEARING = 25.0               # degrees from true North (Pleiades alignment)

# ═══════════════════════════════════════════════════════════════════════════════
# THE SEVEN "ME" GATES — INANNA'S DESCENT PROTOCOL
# (Wolkstein & Kramer 1983; ETCSL t.1.4.1)
# ═══════════════════════════════════════════════════════════════════════════════
#
# Inanna passes through 7 gates of the underworld.
# At each gate she surrenders one piece of her power (me):
#   Gate 7 → Crown of the plain (authority)        → 174 Hz Persistence
#   Gate 6 → Lapis lazuli measuring rod (order)    → 285 Hz Form
#   Gate 5 → Gold ring (cycle/return)              → 396 Hz Liberation
#   Gate 4 → Breastplate (protection)              → 417 Hz Undoing
#   Gate 3 → Golden hip-girdle (desire/gravity)    → 528 Hz Love/DNA
#   Gate 2 → Lapis lazuli necklace (voice/word)    → 639 Hz Connection
#   Gate 1 → Pala-garment (sovereignty/totality)   → 741 Hz Intuition
#
# STRIPPED TO CARRIER: at the throne of Ereshkigal — pure 0-Hz state
# REASSEMBLY:          the 7 me are restored in reverse = re-encoding
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class InannaGate:
    """One of the seven gates of the underworld descent protocol."""
    gate:        int          # 7 (outermost) → 1 (innermost)
    me_item:     str          # The knowledge item surrendered
    me_function: str          # What knowledge domain it governs
    solfeggio:   float        # Corresponding Solfeggio frequency (Hz)
    cuneiform:   str          # Cuneiform sign / syllable
    sumerian:    str          # Sumerian term


INANNA_GATES: Tuple[InannaGate, ...] = (
    InannaGate(7, "Shugurra crown",         "authority / pattern",   174.0, "𒂗", "shugurra"),
    InannaGate(6, "Lapis measuring rod",    "order / form",          285.0, "𒆳", "gidda"),
    InannaGate(5, "Gold ring",              "cycle / time",          396.0, "𒄖", "dubur"),
    InannaGate(4, "Breastplate",            "protection / shield",   417.0, "𒁾", "kur"),
    InannaGate(3, "Gold hip-girdle",        "love / gravity",        528.0, "𒅗", "sag"),
    InannaGate(2, "Lapis necklace",         "voice / word / logos",  639.0, "𒄑", "gis"),
    InannaGate(1, "Pala-garment",           "sovereignty / totality",741.0, "𒀭", "dingir"),
)

GATE_BY_NUMBER: Dict[int, InannaGate] = {g.gate: g for g in INANNA_GATES}


# ═══════════════════════════════════════════════════════════════════════════════
# THE SUMERIAN "ME" — Divine Knowledge Sets
# (Kramer 1963; ETCSL — "Inanna and Enki: The Transfer of the Arts of
#  Civilization from Eridu to Erech")
# ═══════════════════════════════════════════════════════════════════════════════
#
# The me are 94 defined knowledge domains held by Enki at Eridu.
# Inanna transfers them to Uruk — a literal knowledge transmission event.
# We map the primary 24 me (matching the 24-rune Futhork) to the
# Aureon harmonic architecture.
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class SumerianMe:
    """One divine knowledge set (me) from the Sumerian archive."""
    id:          str          # Short identifier
    sumerian:    str          # Sumerian name
    english:     str          # English translation
    domain:      str          # Knowledge domain
    gate:        int          # Associated Inanna gate (1-7)
    position:    int          # Position within gate (1-3+)
    solfeggio:   float        # Gate Solfeggio frequency
    amplitude:   float        # PHI modulation (like aett system)

    @property
    def effective_hz(self) -> float:
        return round(self.solfeggio * self.amplitude, 2)


# 24 primary me — mapped to the same 3-tier amplitude structure as Futhork
# Tier 1 (Foundation): amplitude × 1.0   — the permanent me
# Tier 2 (Active):     amplitude × PHI   — the transmitted me
# Tier 3 (Latent):     amplitude × 1/PHI — the hidden me

_ME_CATALOG: Tuple[SumerianMe, ...] = (
    # ── Tier 1 Foundation me (×1.0) ─────────────────────────────────────────
    SumerianMe("ENSHIP",   "nam-en",    "Lordship",             "governance",     7, 1, 174.0, 1.0),
    SumerianMe("GODSHIP",  "nam-dingir","Godship",              "divine order",   7, 2, 174.0, 1.0),
    SumerianMe("CROWN",    "aga",       "The exalted crown",    "authority",      7, 3, 174.0, 1.0),
    SumerianMe("THRONE",   "gišgu.za",  "The throne of kingship","sovereignty",   6, 1, 285.0, 1.0),
    SumerianMe("SHEPHERD", "nam-sipa",  "The shepherd staff",   "leadership",     6, 2, 285.0, 1.0),
    SumerianMe("KINGSHIP", "nam-lugal", "Kingship",             "rule",           6, 3, 285.0, 1.0),
    SumerianMe("SCRIBES",  "dub-sar",   "Scribal art",          "transmission",   5, 1, 396.0, 1.0),
    SumerianMe("MUSIC",    "tigi",      "The tigi instrument",  "frequency",      5, 2, 396.0, 1.0),
    # ── Tier 2 Active me (×PHI) ─────────────────────────────────────────────
    SumerianMe("DESCENT",  "kur-ra",    "Descent to underworld","hidden knowledge",4,1, 417.0, PHI),
    SumerianMe("ASCENT",   "e-a",       "Ascent from underworld","restored knowing",4,2,417.0, PHI),
    SumerianMe("TRUTH",    "mé-nam",    "True speech",          "accuracy",       4, 3, 417.0, PHI),
    SumerianMe("WEAPONS",  "tukul",     "Weapons / protection", "defence",        3, 1, 528.0, PHI),
    SumerianMe("FLOOD",    "a-ma-ru",   "The flood",            "reset / renewal",3, 2, 528.0, PHI),
    SumerianMe("CRAFT",    "tibira",    "Metalwork / craft",    "precision",      3, 3, 528.0, PHI),
    SumerianMe("MUSIC2",   "ala",       "The ala drum",         "resonance",      2, 1, 639.0, PHI),
    SumerianMe("VOICE",    "inim",      "The word / logos",     "encoding",       2, 2, 639.0, PHI),
    # ── Tier 3 Latent me (×1/PHI) ───────────────────────────────────────────
    SumerianMe("TEMPLE",   "é",         "The temple / house",   "sacred space",   1, 1, 741.0, PHI_INV),
    SumerianMe("WISDOM",   "nam-zu",    "Wisdom / knowledge",   "understanding",  1, 2, 741.0, PHI_INV),
    SumerianMe("TABLET",   "dub",       "The tablet of destinies","record",       1, 3, 741.0, PHI_INV),
    SumerianMe("FLOOD2",   "amaru2",    "Second flood / memory","archive",        7, 4, 174.0, PHI_INV),
    SumerianMe("STARMAP",  "mul",       "Star / celestial map", "navigation",     6, 4, 285.0, PHI_INV),
    SumerianMe("MEASURE",  "ninda",     "The measuring reed",   "calibration",    5, 4, 396.0, PHI_INV),
    SumerianMe("UNDERWD",  "kur",       "The underworld itself","deep archive",   4, 4, 417.0, PHI_INV),
    SumerianMe("GIRLHOOD", "nam-kig",   "Girlhood / potential", "latent seed",    3, 4, 528.0, PHI_INV),
)

ME_BY_ID: Dict[str, SumerianMe] = {m.id: m for m in _ME_CATALOG}


# ═══════════════════════════════════════════════════════════════════════════════
# KEY SUMERIAN TEXTS — The Transmission Archive
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class SumerianText:
    """A key Sumerian text node in the knowledge lattice."""
    id:           str
    title:        str
    etcsl_ref:    str          # ETCSL catalogue reference
    location:     str          # Primary clay tablet find site
    theme:        str          # Core transmission theme
    primary_me:   Tuple[str, ...]  # Primary me IDs encoded
    gate_sequence: Tuple[int, ...] # Gate numbers activated (1-7)
    lat:          float        # Find-site latitude
    lon:          float        # Find-site longitude
    bearing_to_ur: Optional[float] = None  # Calculated bearing to Ur


_TEXT_ARCHIVE: Tuple[SumerianText, ...] = (
    SumerianText(
        id           = "INANNA_DESCENT",
        title        = "Inanna's Descent to the Underworld",
        etcsl_ref    = "t.1.4.1",
        location     = "Nippur",
        theme        = "7-gate stripping and restoration of knowledge — complete protocol",
        primary_me   = ("DESCENT", "ASCENT", "CROWN", "VOICE", "WISDOM"),
        gate_sequence = (7, 6, 5, 4, 3, 2, 1),
        lat          = 32.1228,
        lon          = 45.2291,
    ),
    SumerianText(
        id           = "INANNA_ENKI",
        title        = "Inanna and Enki: Transfer of the Me",
        etcsl_ref    = "t.1.3.1",
        location     = "Eridu / Uruk",
        theme        = "Physical transport of 94 me from Eridu to Uruk — transmission event",
        primary_me   = ("SCRIBES", "MUSIC", "TRUTH", "CRAFT", "TABLET"),
        gate_sequence = (6, 5, 3, 2),
        lat          = 31.8060,
        lon          = 45.6360,
    ),
    SumerianText(
        id           = "GILGAMESH",
        title        = "Epic of Gilgamesh",
        etcsl_ref    = "t.3.3.1 / SB Gilgamesh",
        location     = "Ur / Nineveh",
        theme        = "Search for immortality = search for the lost knowledge of the flood",
        primary_me   = ("FLOOD", "FLOOD2", "WISDOM", "TEMPLE", "UNDERWD"),
        gate_sequence = (3, 7, 1),
        lat          = 36.3590,
        lon          = 43.1550,   # Nineveh (Ashurbanipal library)
    ),
    SumerianText(
        id           = "ENUMA_ELISH",
        title        = "Enuma Elish — The Babylonian Creation Epic",
        etcsl_ref    = "BBR 1-20",
        location     = "Babylon",
        theme        = "Creation as frequency emergence: from Apsu (silence) to form",
        primary_me   = ("GODSHIP", "KINGSHIP", "WEAPONS", "STARMAP", "MEASURE"),
        gate_sequence = (7, 5, 6),
        lat          = 32.5427,
        lon          = 44.4211,
    ),
    SumerianText(
        id           = "URNAMMU_LAW",
        title        = "Law Code of Ur-Nammu",
        etcsl_ref    = "t.2.4.1.1",
        location     = "Ur",
        theme        = "First known law code — encoding of societal me into permanent form",
        primary_me   = ("ENSHIP", "THRONE", "SHEPHERD", "TRUTH", "MEASURE"),
        gate_sequence = (7, 6, 4),
        lat          = UR_LAT,
        lon          = UR_LON,
    ),
    SumerianText(
        id           = "TABLET_DESTINIES",
        title        = "Tablet of Destinies (Me-tablet)",
        etcsl_ref    = "Anzu myth / Enuma Elish",
        location     = "Nippur / Eridu",
        theme        = "The master record of all me — the Emerald Tablet equivalent",
        primary_me   = ("TABLET", "GODSHIP", "WISDOM", "VOICE", "STARMAP"),
        gate_sequence = (1, 7, 2, 6),
        lat          = 31.8060,
        lon          = 45.6360,   # Eridu
    ),
    SumerianText(
        id           = "HYMN_INANNA",
        title        = "Hymn to Inanna (Exaltation of Inanna)",
        etcsl_ref    = "t.4.07.2",
        location     = "Ur / Nippur",
        theme        = "Inanna as the living carrier wave — all me flow through her",
        primary_me   = ("CROWN", "VOICE", "MUSIC", "GIRLHOOD", "CRAFT"),
        gate_sequence = (7, 2, 5, 3),
        lat          = UR_LAT,
        lon          = UR_LON,
    ),
)

TEXT_BY_ID: Dict[str, SumerianText] = {t.id: t for t in _TEXT_ARCHIVE}


# ═══════════════════════════════════════════════════════════════════════════════
# PHI RESONANCE AND FREQUENCY ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

PHI_TOLERANCE = 0.02


def test_phi_resonance_me(me: SumerianMe, ref_hz: float = SUMERIAN_BASE_NOTE_HZ
                          ) -> Tuple[float, str, float, bool]:
    """
    Test phi resonance between a me's effective frequency and the Sumerian
    base note (396 Hz = ni = UT Solfeggio = foundation tone of Ur).

    Returns: (ratio, target, distance, is_resonant)
    """
    if me.effective_hz == 0:
        return 0.0, "NONE", 999.0, False

    ratio_fwd = ref_hz / me.effective_hz
    ratio_inv = me.effective_hz / ref_hz

    best_ratio, best_target, best_dist = None, "NONE", 999.0
    for ratio in [ratio_fwd, ratio_inv]:
        for target, val in [("PHI", PHI), ("PHI_INV", PHI_INV)]:
            d = abs(ratio - val)
            if d < best_dist:
                best_dist, best_ratio, best_target = d, ratio, target

    return round(best_ratio, 6), best_target, round(best_dist, 6), best_dist < PHI_TOLERANCE


# ═══════════════════════════════════════════════════════════════════════════════
# SUMERIAN DECODER ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class SumerianLattice:
    """Complete state of the Sumerian knowledge lattice."""
    timestamp:          float
    n_me_total:         int
    n_me_decoded:       int
    n_gates_active:     int
    n_phi_resonant:     int
    gate_frequencies:   Dict[int, float]   # gate → Solfeggio Hz
    mean_me_hz:         float
    master_beat_hz:     float
    schumann_mode:      int
    schumann_delta:     float
    gamma:              float              # Lattice coherence
    gamma_status:       str
    geographic_bearing: float              # Ziggurat → sacred axis bearing
    prophecy:           str


class SumerianDecoder:
    """
    The Book of Ur decoder engine.

    Processes the Sumerian me catalog and text archive through the
    Aureon HNC framework, calculating:
      - 7-gate Solfeggio frequency map
      - Me effective frequencies (× PHI tiers)
      - Phi resonance against the Sumerian base note (396 Hz)
      - Master beat frequency → Schumann proximity
      - Lattice coherence Γ
      - Geographic bearing from Ur along sacred axis
    """

    GATE_CALLER_HZ = SUMERIAN_BASE_NOTE_HZ   # The base note = the caller

    def _schumann_proximity(self, beat_hz: float) -> Tuple[int, float, float]:
        best_mode, best_hz, best_delta = 1, SCHUMANN_MODES[0], abs(beat_hz - SCHUMANN_MODES[0])
        for i, hz in enumerate(SCHUMANN_MODES, 1):
            d = abs(beat_hz - hz)
            if d < best_delta:
                best_delta, best_hz, best_mode = d, hz, i
        return best_mode, best_hz, round(best_delta, 4)

    def read(self) -> SumerianLattice:
        # Gate frequency map (7 Inanna gates = 7 Solfeggio stages)
        gate_freqs = {g.gate: g.solfeggio for g in INANNA_GATES}

        # Analyse all 24 me
        decoded_me = [m for m in _ME_CATALOG]
        phi_resonant = 0
        effective_freqs = []

        for me in decoded_me:
            _, _, dist, is_res = test_phi_resonance_me(me)
            if is_res:
                phi_resonant += 1
            effective_freqs.append(me.effective_hz)

        mean_me_hz  = sum(effective_freqs) / len(effective_freqs) if effective_freqs else 0.0
        master_beat = abs(self.GATE_CALLER_HZ - mean_me_hz)

        sch_mode, sch_hz, sch_delta = self._schumann_proximity(master_beat)
        sch_proximity = max(0.0, 1.0 - sch_delta / sch_hz)

        # Gamma: phi_score + completeness + schumann
        phi_score    = phi_resonant / len(decoded_me) if decoded_me else 0.0
        completeness = len(_TEXT_ARCHIVE) / 7.0        # 7 canonical texts = full set
        completeness = min(1.0, completeness)
        gamma        = phi_score * 0.50 + completeness * 0.30 + sch_proximity * 0.20
        gamma        = min(1.0, gamma)

        if gamma >= 0.945:
            status = "LIGHTHOUSE"
        elif gamma >= 0.35:
            status = "ACTIVE_FIELD"
        else:
            status = "DEAD_FIELD"

        prophecy = (
            f"Book of Ur Γ={gamma:.4f} ({status}). "
            f"{len(decoded_me)}/24 me decoded. "
            f"7/7 Inanna gates active (174-741 Hz). "
            f"Master beat {master_beat:.2f} Hz → Schumann M{sch_mode} "
            f"at {sch_hz} Hz (Δ{sch_delta:.2f} Hz). "
            f"Phi-resonant me: {phi_resonant}/{len(decoded_me)}. "
            f"Ur ziggurat bearing: {UR_ZIGGURAT_BEARING}° (Pleiades axis)."
        )

        return SumerianLattice(
            timestamp          = time.time(),
            n_me_total         = len(_ME_CATALOG),
            n_me_decoded       = len(decoded_me),
            n_gates_active     = 7,
            n_phi_resonant     = phi_resonant,
            gate_frequencies   = gate_freqs,
            mean_me_hz         = round(mean_me_hz, 4),
            master_beat_hz     = round(master_beat, 4),
            schumann_mode      = sch_mode,
            schumann_delta     = sch_delta,
            gamma              = round(gamma, 6),
            gamma_status       = status,
            geographic_bearing = UR_ZIGGURAT_BEARING,
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
        Return the geographic transmission vector from Ur.
        The Ur ziggurat bearing (25° from North toward Pleiades) defines
        the Sumerian sacred axis — one of the 10 civilizational DNA vectors.
        """
        return {
            "origin":    {"lat": UR_LAT, "lon": UR_LON, "name": "City of Ur"},
            "bearing":   UR_ZIGGURAT_BEARING,
            "axis":      "Pleiades rise alignment",
            "tradition": "SUMERIAN",
            "anchor_hz": SUMERIAN_BASE_NOTE_HZ,
            "confidence": self.get_oracle_score(),
        }

    def print_report(self):
        lattice = self.read()
        print("\n╔══════════════════════════════════════════════════════════════════╗")
        print("║         BOOK OF UR — SUMERIAN KNOWLEDGE LATTICE REPORT          ║")
        print("╚══════════════════════════════════════════════════════════════════╝\n")

        print("INANNA'S SEVEN GATES — SOLFEGGIO FREQUENCY MAP")
        print("─" * 60)
        for g in sorted(INANNA_GATES, key=lambda x: x.gate, reverse=True):
            print(
                f"  Gate {g.gate}  {g.cuneiform}  {g.solfeggio:>6.1f} Hz  "
                f"{g.me_item:<30} — {g.me_function}"
            )
        print()

        print("24 PRIMARY ME — EFFECTIVE FREQUENCIES (× PHI TIERS)")
        print("─" * 70)
        hdr = f"{'Me ID':<12} {'Sumerian':<14} {'Gate':<5} {'Solf Hz':<9} {'×':<10} {'Eff Hz':<9} {'Domain'}"
        print(hdr)
        print("─" * 70)
        for me in _ME_CATALOG:
            amp_s = "1.000" if me.amplitude == 1.0 else (
                "φ=1.618" if me.amplitude > 1.5 else "1/φ=0.618"
            )
            print(
                f"{me.id:<12} {me.sumerian:<14} {me.gate:<5} "
                f"{me.solfeggio:<9.1f} {amp_s:<10} {me.effective_hz:<9.2f} {me.domain}"
            )
        print()

        print("TEXT ARCHIVE — TRANSMISSION NODES")
        print("─" * 60)
        for t in _TEXT_ARCHIVE:
            print(f"  {t.id:<20} [{t.etcsl_ref}]  {t.lat:.2f}°N {t.lon:.2f}°E")
            print(f"    {t.title}")
            print(f"    Gates: {t.gate_sequence}  Me: {t.primary_me[:3]}")
        print()

        print("LATTICE COHERENCE")
        print("─" * 60)
        bar_len = int(lattice.gamma * 50)
        bar     = "█" * bar_len + "░" * (50 - bar_len)
        print(f"  Γ = {lattice.gamma:.6f}  [{bar}]")
        print(f"  Status    : {lattice.gamma_status}")
        print(f"  Master beat: {lattice.master_beat_hz:.4f} Hz")
        print(f"  Schumann M{lattice.schumann_mode}: Δ{lattice.schumann_delta:.4f} Hz")
        print(f"  Ur bearing : {lattice.geographic_bearing}° (Pleiades axis)")
        print()
        print("  " + lattice.prophecy)
        print()


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE EXPORTS
# ═══════════════════════════════════════════════════════════════════════════════

def get_sumerian_decoder() -> SumerianDecoder:
    return SumerianDecoder()


def get_sumerian_geographic_vector() -> Dict:
    return SumerianDecoder().get_geographic_vector()


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def _cli():
    parser = argparse.ArgumentParser(
        prog        = "book_of_ur",
        description = "Book of Ur — Sumerian Knowledge Archive Decoder",
    )
    parser.add_argument("--json",         action="store_true", help="Output lattice as JSON")
    parser.add_argument("--oracle-score", action="store_true", help="Print oracle score (0-1)")
    parser.add_argument("--vector",       action="store_true", help="Print geographic vector")
    args = parser.parse_args()

    dec = SumerianDecoder()

    if args.oracle_score:
        s = dec.get_oracle_score()
        l = dec.read()
        print(f"\nBook of Ur Oracle Score: {s:.4f}  [Γ={l.gamma:.4f} / {l.gamma_status}]\n")
    elif args.vector:
        v = dec.get_geographic_vector()
        print(json.dumps(v, indent=2))
    elif args.json:
        l = dec.read()
        print(json.dumps({
            "timestamp":      l.timestamp,
            "gamma":          l.gamma,
            "gamma_status":   l.gamma_status,
            "n_me_total":     l.n_me_total,
            "n_me_decoded":   l.n_me_decoded,
            "n_gates_active": l.n_gates_active,
            "n_phi_resonant": l.n_phi_resonant,
            "mean_me_hz":     l.mean_me_hz,
            "master_beat_hz": l.master_beat_hz,
            "schumann_mode":  l.schumann_mode,
            "schumann_delta": l.schumann_delta,
            "geographic_bearing": l.geographic_bearing,
            "prophecy":       l.prophecy,
        }, indent=2))
    else:
        dec.print_report()


if __name__ == "__main__":
    _cli()
