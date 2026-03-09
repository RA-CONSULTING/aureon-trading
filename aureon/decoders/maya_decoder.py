#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   𝄋  MAYA DECODER — Long Count + Venus Cycle Transmission  𝄋               ║
║   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                                                              ║
║   Decoded through the Aureon HNC Architecture                                ║
║   Aureon Institute · R&A Consulting and Brokerage Services Ltd.             ║
║                                                                              ║
║   Sources:                                                                   ║
║     Coe, M.D. (2012) Breaking the Maya Code                                 ║
║     Schele, L. & Freidel, D. (1990) A Forest of Kings                      ║
║     Lounsbury, F. (1978) "Maya Numeration, Computation, and Calendrical    ║
║       Astronomy" in Dictionary of Scientific Biography                       ║
║     Kelley, D.H. (1976) Deciphering the Maya Script                        ║
║     Milbrath, S. (1999) Star Gods of the Maya                              ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║   THE MAYA TRANSMISSION HYPOTHESIS                                           ║
║   ──────────────────────────────────                                         ║
║   The Maya Long Count calendar is not just a time-keeping system — it is   ║
║   a multi-layered frequency archive. The 5 Long Count cycles (kin/uinal/   ║
║   tun/katun/baktun) are 5 nested frequency bands. The 260-day Tzolkin is   ║
║   a 13×20 matrix — a binary transmission table equivalent to the I Ching.  ║
║                                                                              ║
║   VENUS CYCLE ≡ DUAL-VOICE PROTOCOL                                         ║
║   Venus makes 5 synodic cycles (584 days each) in 8 Earth years = 2920     ║
║   days. This 5:8 ratio is a PHI approximation (5/8 = 0.625, near 0.618).   ║
║   Venus as Morning Star = Caller (Ψ₀); Evening Star = Seer (O(t)).         ║
║   The Dresden Codex Venus tables are a 104-year cycle of these transitions. ║
║                                                                              ║
║   20 DAY SIGNS ≡ DUAL-VOICE CIPHER                                          ║
║   The 20 Tzolkin day signs × 13 numbers = 260 unique combinations.         ║
║   Day sign = structural frame (Caller), day number = response field (Seer). ║
║   260 = 13 × 20 = complete transmission matrix.                             ║
║                                                                              ║
║   GEOGRAPHIC ANCHOR: Chichen Itza, Yucatan, Mexico                          ║
║     Lat: 20.6843°N  Lon: -88.5678°W                                         ║
║     El Castillo (Kukulcan pyramid): equinox serpent shadow at 17° from N   ║
║     Observatory (El Caracol): aligned to Venus rising/setting               ║
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

SOLFEGGIO      = [174, 285, 396, 417, 528, 639, 741, 852, 963]
SCHUMANN_MODES = [7.83, 14.3, 20.8, 27.3, 33.8, 39.0, 45.0]

PHI_TOLERANCE = 0.02

# Maya anchor frequency: 417 Hz — RE solfeggio / transformation / Venus
MAYA_BASE_HZ = 417.0

# Chichen Itza geographic anchor
CHICHEN_LAT     = 20.6843
CHICHEN_LON     = -88.5678
CHICHEN_BEARING = 17.0    # El Castillo equinox sunrise axis

# Calendar constants
TZOLKIN_DAYS  = 260   # Sacred calendar (13 × 20)
HAAB_DAYS     = 365   # Solar calendar (18 × 20 + 5)
VENUS_SYNODIC = 584   # Venus synodic period in Earth days
LONG_COUNT_BASE_YEAR = 3114  # BCE — Maya creation date (4 Ahau 8 Cumku)

N_LONG_COUNT_CYCLES = 5
N_TZOLKIN_DAYSIGNS  = 20
N_TZOLKIN_NUMBERS   = 13
N_HAAB_MONTHS       = 18
N_WAYEB_DAYS        = 5     # The 5 nameless days — open circuit equivalent


# ═══════════════════════════════════════════════════════════════════════════════
# 20 TZOLKIN DAY SIGNS (Caller / structural frame)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class DaySign:
    number:      int    # 1-20 in Tzolkin sequence
    name:        str    # Yucatec name
    glyph:       str    # Transliteration
    element:     str    # Earth / Air / Fire / Water
    direction:   str    # Cardinal / intercardinal
    solfeggio_hz: float # Frequency correspondence
    amplitude:   float  # PHI-mode (groups of 5 × 4 = 20)
    mode:        str    # GENESIS / GROWTH / RETURN / KEYS
    decoded:     bool
    notes:       str = ""


def _ds_amp(n: int) -> float:
    """Groups of 5 day signs: 1-5 Genesis, 6-10 Growth, 11-15 Return, 16-20 Keys."""
    group = (n - 1) // 5 + 1
    return {1: 1.0, 2: PHI, 3: PHI_INV, 4: 1.0}.get(group, 1.0)

def _ds_mode(n: int) -> str:
    group = (n - 1) // 5 + 1
    return {1: "GENESIS", 2: "GROWTH", 3: "RETURN", 4: "KEYS"}.get(group, "GENESIS")


_DAY_SIGNS: Tuple[DaySign, ...] = (
    DaySign(1,  "Imix",    "Imix",    "Water", "East",  174.0*_ds_amp(1),  _ds_amp(1),  _ds_mode(1),  True,  "Primordial waters — carrier"),
    DaySign(2,  "Ik'",     "Ik",      "Air",   "North", 285.0*_ds_amp(2),  _ds_amp(2),  _ds_mode(2),  True,  "Wind / breath / spirit"),
    DaySign(3,  "Ak'bal",  "Akbal",   "Earth", "West",  396.0*_ds_amp(3),  _ds_amp(3),  _ds_mode(3),  True,  "Darkness / night / corn"),
    DaySign(4,  "K'an",    "Kan",     "Fire",  "South", 417.0*_ds_amp(4),  _ds_amp(4),  _ds_mode(4),  True,  "Corn / seed / transformation"),
    DaySign(5,  "Chikchan","Chicchan","Water", "East",  528.0*_ds_amp(5),  _ds_amp(5),  _ds_mode(5),  True,  "Serpent / Venus / solar"),
    DaySign(6,  "Kimi",    "Cimi",    "Air",   "North", 174.0*_ds_amp(6),  _ds_amp(6),  _ds_mode(6),  True,  "Death / transformation — phi-carrier"),
    DaySign(7,  "Manik'",  "Manik",   "Earth", "West",  285.0*_ds_amp(7),  _ds_amp(7),  _ds_mode(7),  True,  "Deer / hand / sacrifice"),
    DaySign(8,  "Lamat",   "Lamat",   "Fire",  "South", 396.0*_ds_amp(8),  _ds_amp(8),  _ds_mode(8),  True,  "Venus Star / rabbit / seed"),
    DaySign(9,  "Muluk",   "Muluc",   "Water", "East",  417.0*_ds_amp(9),  _ds_amp(9),  _ds_mode(9),  True,  "Water / moon / offering"),
    DaySign(10, "Ok",      "Oc",      "Air",   "North", 528.0*_ds_amp(10), _ds_amp(10), _ds_mode(10), True,  "Dog / authority — solar zero-beat"),
    DaySign(11, "Chuwen",  "Chuen",   "Earth", "West",  174.0*_ds_amp(11), _ds_amp(11), _ds_mode(11), True,  "Monkey / thread / artisan"),
    DaySign(12, "Eb",      "Eb",      "Fire",  "South", 285.0*_ds_amp(12), _ds_amp(12), _ds_mode(12), True,  "Road / path / rain"),
    DaySign(13, "Ben",     "Ben",     "Water", "East",  396.0*_ds_amp(13), _ds_amp(13), _ds_mode(13), True,  "Reed / corn stalk / growth"),
    DaySign(14, "Ix",      "Ix",      "Air",   "North", 417.0*_ds_amp(14), _ds_amp(14), _ds_mode(14), True,  "Jaguar / shaman / earth magic"),
    DaySign(15, "Men",     "Men",     "Earth", "West",  528.0*_ds_amp(15), _ds_amp(15), _ds_mode(15), True,  "Eagle / moon / higher mind"),
    DaySign(16, "Kib",     "Cib",     "Fire",  "South", 174.0*_ds_amp(16), _ds_amp(16), _ds_mode(16), True,  "Vulture / wisdom / karmic"),
    DaySign(17, "Kaban",   "Caban",   "Water", "East",  285.0*_ds_amp(17), _ds_amp(17), _ds_mode(17), True,  "Earth / movement / earthquake"),
    DaySign(18, "Etz'nab", "Etznab",  "Air",   "North", 396.0*_ds_amp(18), _ds_amp(18), _ds_mode(18), True,  "Flint / mirror / truth"),
    DaySign(19, "Kawak",   "Cauac",   "Earth", "West",  417.0*_ds_amp(19), _ds_amp(19), _ds_mode(19), True,  "Storm / rain / thunder"),
    DaySign(20, "Ajaw",    "Ahau",    "Fire",  "South", 528.0*_ds_amp(20), _ds_amp(20), _ds_mode(20), True,  "Sun Lord — the complete cycle"),
)


# ═══════════════════════════════════════════════════════════════════════════════
# LONG COUNT CYCLES (5 nested frequency bands)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class LongCountCycle:
    level:       int    # 1=kin, 2=uinal, 3=tun, 4=katun, 5=baktun
    name:        str    # Maya name
    days:        int    # Days in this unit
    hz:          float  # Solfeggio correspondence
    amplitude:   float  # PHI-mode
    mode:        str
    decoded:     bool
    notes:       str = ""


_LONG_COUNT: Tuple[LongCountCycle, ...] = (
    LongCountCycle(1, "Kin    (1 day)",        1,       174.0,        1.0,      "GENESIS", True,
                   "Single day — base carrier. Foundation."),
    LongCountCycle(2, "Uinal  (20 days)",      20,      285.0,        1.0,      "GENESIS", True,
                   "20-day month — form frequency."),
    LongCountCycle(3, "Tun    (360 days)",      360,     396.0*PHI,    PHI,      "GROWTH",  True,
                   "Approximate solar year — liberation phi."),
    LongCountCycle(4, "Katun  (7200 days)",     7200,    528.0*PHI,    PHI,      "GROWTH",  True,
                   "~20 years — solar carrier phi. Major historical cycle."),
    LongCountCycle(5, "Baktun (144000 days)",   144000,  963.0*PHI_INV,PHI_INV,  "RETURN",  True,
                   "~394 years — 13 baktun = the Great Cycle (2012 completion)."),
)


# ═══════════════════════════════════════════════════════════════════════════════
# VENUS TABLE RECORDS (from the Dresden Codex)
# The Venus cycle is the 'pivot' — the key that connects all other cycles.
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class VenusRecord:
    phase:     str    # Morning Star / Evening Star / Inferior / Superior conjunction
    days:      int    # Days in this phase
    hz:        float  # Frequency correspondence
    caller:    bool   # True = Caller (Ψ₀ / Morning Star), False = Seer (Evening Star)
    decoded:   bool
    notes:     str = ""


_VENUS_TABLE: Tuple[VenusRecord, ...] = (
    VenusRecord("Morning Star (Caller Ψ₀)",      236, 528.0, True,  True,
                "Venus rises before Sun — Caller. Quetzalcoatl / Kukulcan."),
    VenusRecord("Superior conjunction",            90,  963.0, True,  True,
                "Venus behind Sun — maximum distance. Highest solfeggio."),
    VenusRecord("Evening Star (Seer O(t))",       250, 417.0, False, True,
                "Venus follows Sun — Seer. Xolotl / underworld guide."),
    VenusRecord("Inferior conjunction (pivot)",     8,  174.0, False, False,
                "OPEN CIRCUIT — Venus hidden. 8 days of invisibility = Nr.15 pivot."),
)


# ═══════════════════════════════════════════════════════════════════════════════
# LATTICE AND DECODER
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class MayaLattice:
    """Decoded state of the Maya Long Count transmission lattice."""
    timestamp:            float
    n_day_signs:          int
    n_day_signs_decoded:  int
    n_long_count:         int
    n_long_count_decoded: int
    n_venus:              int
    n_venus_decoded:      int
    completeness:         float
    phi_score:            float
    schumann_proximity:   float
    gamma:                float
    field_status:         str
    mean_hz:              float
    anchor_hz:            float
    venus_ratio:          float    # 5:8 Venus:Earth ratio vs PHI_INV
    notes:                str = ""


class MayaDecoder:
    """
    Decodes the Maya Long Count + Venus Cycle transmission archive.

    Gamma = phi_score × 0.50 + completeness × 0.30 + schumann_proximity × 0.20

    The 8-day inferior conjunction of Venus is the open circuit — the pivot
    equivalent to Nr.15 in Maeshowe. When Venus is hidden (inferior conjunction),
    the dual-voice channel is broken: neither Morning Star (Caller) nor Evening
    Star (Seer) is visible. The transmission resumes on re-emergence.

    The Dresden Codex preserves 104 years of Venus tables — the most accurate
    pre-telescopic astronomical record known. This level of precision implies
    a preserved knowledge-transmission intent, not mere observation.
    """

    GAMMA_DEAD_FIELD = 0.35
    GAMMA_LIGHTHOUSE = 0.945

    def __init__(self):
        self._day_signs   = list(_DAY_SIGNS)
        self._long_count  = list(_LONG_COUNT)
        self._venus_table = list(_VENUS_TABLE)

    def _phi_resonant(self, hz1: float, hz2: float) -> bool:
        if hz1 <= 0 or hz2 <= 0:
            return False
        r = hz1 / hz2 if hz1 > hz2 else hz2 / hz1
        return (abs(r - PHI) < PHI_TOLERANCE or
                abs(r - PHI_INV) < PHI_TOLERANCE or
                abs(r - 1.0) < 0.01)

    def read(self) -> MayaLattice:
        dec_signs = [d for d in self._day_signs   if d.decoded]
        dec_lc    = [l for l in self._long_count  if l.decoded]
        dec_venus = [v for v in self._venus_table if v.decoded]

        n_signs  = len(self._day_signs)
        n_lc     = len(self._long_count)
        n_venus  = len(self._venus_table)
        nd_signs = len(dec_signs)
        nd_lc    = len(dec_lc)
        nd_venus = len(dec_venus)

        completeness = (nd_signs / n_signs * 0.50 +
                        nd_lc    / n_lc    * 0.30 +
                        nd_venus / n_venus * 0.20)

        # Phi-resonance: each decoded day sign against MAYA_BASE_HZ (417)
        phi_hits = sum(
            1 for d in dec_signs
            if self._phi_resonant(d.solfeggio_hz, MAYA_BASE_HZ)
        )
        phi_score = phi_hits / max(nd_signs, 1)

        mean_hz = (
            sum(d.solfeggio_hz for d in dec_signs) / nd_signs
            if nd_signs > 0 else MAYA_BASE_HZ
        )

        nearest_multiple = max(1, round(mean_hz / SCHUMANN_MODES[3]))
        harmonic_hz = SCHUMANN_MODES[3] * nearest_multiple
        schumann_proximity = 1.0 - min(
            abs(mean_hz - harmonic_hz) / harmonic_hz, 1.0
        )

        # Venus 5:8 ratio vs PHI_INV = 0.618 (5/8 = 0.625)
        venus_ratio = 5 / 8  # 0.625 ≈ PHI_INV (0.618)

        gamma = (
            phi_score          * 0.50 +
            completeness       * 0.30 +
            schumann_proximity * 0.20
        )
        gamma = round(min(max(gamma, 0.0), 1.0), 4)

        field_status = (
            "LIGHTHOUSE"  if gamma >= self.GAMMA_LIGHTHOUSE else
            "ACTIVE_FIELD" if gamma >= self.GAMMA_DEAD_FIELD else
            "DEAD_FIELD"
        )

        return MayaLattice(
            timestamp             = time.time(),
            n_day_signs           = n_signs,
            n_day_signs_decoded   = nd_signs,
            n_long_count          = n_lc,
            n_long_count_decoded  = nd_lc,
            n_venus               = n_venus,
            n_venus_decoded       = nd_venus,
            completeness          = round(completeness, 4),
            phi_score             = round(phi_score, 4),
            schumann_proximity    = round(schumann_proximity, 4),
            gamma                 = gamma,
            field_status          = field_status,
            mean_hz               = round(mean_hz, 2),
            anchor_hz             = MAYA_BASE_HZ,
            venus_ratio           = venus_ratio,
            notes                 = (
                "Venus inferior conjunction (8 days hidden) is the open circuit — "
                "the pivot equivalent to Nr.15. Dresden Codex table B-G decoded; "
                "inferior conjunction timing data requires cross-reference with "
                "El Caracol (observatory) alignment records."
            ),
        )

    def get_oracle_score(self) -> float:
        return self.read().gamma

    def get_geographic_vector(self) -> Tuple[float, float, float]:
        return CHICHEN_LAT, CHICHEN_LON, CHICHEN_BEARING


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def _cli():
    parser = argparse.ArgumentParser(
        prog="maya_decoder",
        description="Maya Long Count + Venus Cycle Decoder",
    )
    parser.add_argument("--signs",  action="store_true", help="List 20 Tzolkin day signs")
    parser.add_argument("--longcount", action="store_true", help="List Long Count cycles")
    parser.add_argument("--venus",  action="store_true", help="List Venus table records")
    parser.add_argument("--oracle-score", action="store_true", help="Print oracle score only")
    parser.add_argument("--json",   action="store_true", help="Output as JSON")
    args = parser.parse_args()

    decoder = MayaDecoder()
    lattice = decoder.read()

    if args.oracle_score:
        print(f"{lattice.gamma:.4f}")
        return

    if args.signs:
        print(f"\n{'#':<4} {'Name':<12} {'Element':<8} {'Hz':<10} {'Mode':<8} {'OK'}")
        print("-" * 55)
        for d in decoder._day_signs:
            print(f"{d.number:<4} {d.name[:11]:<12} {d.element:<8} {d.solfeggio_hz:<10.1f} "
                  f"{d.mode:<8} {'YES' if d.decoded else 'NO'}")
        return

    if args.longcount:
        print(f"\n{'L':<3} {'Name':<28} {'Days':<10} {'Hz':<10} {'Mode':<8} {'OK'}")
        print("-" * 70)
        for l in decoder._long_count:
            print(f"{l.level:<3} {l.name[:27]:<28} {l.days:<10} {l.hz:<10.1f} "
                  f"{l.mode:<8} {'YES' if l.decoded else 'NO'}")
        return

    if args.venus:
        print(f"\n{'Phase':<35} {'Days':<6} {'Hz':<8} {'Voice':<15} {'OK'}")
        print("-" * 75)
        for v in decoder._venus_table:
            voice = "Caller (Ψ₀)" if v.caller else "Seer  (O(t))"
            print(f"{v.phase[:34]:<35} {v.days:<6} {v.hz:<8.0f} {voice:<15} "
                  f"{'YES' if v.decoded else 'OPEN'}")
        return

    if args.json:
        out = {
            "timestamp":          lattice.timestamp,
            "n_day_signs_decoded": lattice.n_day_signs_decoded,
            "n_long_count_decoded": lattice.n_long_count_decoded,
            "completeness":       lattice.completeness,
            "phi_score":          lattice.phi_score,
            "schumann_proximity": lattice.schumann_proximity,
            "gamma":              lattice.gamma,
            "field_status":       lattice.field_status,
            "mean_hz":            lattice.mean_hz,
            "venus_ratio":        lattice.venus_ratio,
            "origin":             {"lat": CHICHEN_LAT, "lon": CHICHEN_LON,
                                   "bearing": CHICHEN_BEARING},
            "notes":              lattice.notes,
        }
        print(json.dumps(out, indent=2))
        return

    print("\n╔══════════════════════════════════════════════════════╗")
    print("║   MAYA DECODER — Long Count + Venus Cycle Report    ║")
    print("╚══════════════════════════════════════════════════════╝\n")
    print(f"  Day signs decoded: {lattice.n_day_signs_decoded}/{lattice.n_day_signs}")
    print(f"  Long Count cycles: {lattice.n_long_count_decoded}/{lattice.n_long_count}")
    print(f"  Venus phases     : {lattice.n_venus_decoded}/{lattice.n_venus}")
    print(f"  Completeness     : {lattice.completeness:.3f}")
    print(f"  Phi score        : {lattice.phi_score:.3f}")
    print(f"  Schumann prox.   : {lattice.schumann_proximity:.3f}")
    print(f"  Gamma (Γ)        : {lattice.gamma:.4f}  [{lattice.field_status}]")
    print(f"  Mean Hz          : {lattice.mean_hz:.1f} Hz")
    print(f"  Venus 5:8 ratio  : {lattice.venus_ratio:.4f} (PHI_INV={PHI_INV:.4f})")
    print(f"\n  Geographic vector: {CHICHEN_LAT}°N, {CHICHEN_LON}°E, bearing {CHICHEN_BEARING}°")
    print(f"\n  Note: {lattice.notes}\n")


if __name__ == "__main__":
    _cli()
