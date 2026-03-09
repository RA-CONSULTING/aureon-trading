#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ☀  AZTEC DECODER — Tonalpohualli + Solar Calendar Transmission  ☀         ║
║   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                                                              ║
║   Decoded through the Aureon HNC Architecture                                ║
║   Aureon Institute · R&A Consulting and Brokerage Services Ltd.             ║
║                                                                              ║
║   Sources:                                                                   ║
║     Townsend, R.F. (2000) The Aztecs                                        ║
║     Berdan, F.F. (2014) Aztec Archaeology and Ethnohistory                  ║
║     Caso, A. (1971) "Calendrical Systems of Central Mexico" in HMAI v.10   ║
║     Heyden, D. (1975) "An Interpretation of the Cave underneath the         ║
║       Pyramid of the Sun in Teotihuacan" — American Antiquity                ║
║     Aveni, A.F. (1980) Skywatchers of Ancient Mexico                       ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║   THE AZTEC TRANSMISSION HYPOTHESIS                                          ║
║   ──────────────────────────────────                                         ║
║   Teotihuacan (built ~100 BCE, occupied ~500 CE) is the archetypal          ║
║   Mesoamerican transmission site. The Street of the Dead (15.5° W of N)    ║
║   was deliberately misaligned from cardinal north to point toward the       ║
║   Pleiades setting — a star whose 52-year cycle governed all Aztec time.   ║
║                                                                              ║
║   TONALPOHUALLI ≡ DUAL-VOICE CIPHER                                         ║
║   The 260-day sacred calendar (Tonalpohualli) is:                           ║
║     20 day signs (trecena frame) = Caller (Ψ₀) — structural pattern        ║
║     13 day numbers               = Seer (O(t)) — the response field        ║
║   Neither the sign alone nor the number alone determines the day's meaning. ║
║   Only the combination of both — exact dual-voice protocol.                 ║
║                                                                              ║
║   18-MONTH SOLAR CALENDAR (XIUHPOHUALLI) + 5 NEMONTEMI                     ║
║   18 months × 20 days = 360 days + 5 Nemontemi (unlucky days) = 365.       ║
║   The 5 Nemontemi are the open circuit — the unnamed/dangerous days.        ║
║   Structurally identical to Nr.15 (Maeshowe) and the 8-day Venus gap.      ║
║                                                                              ║
║   GEOGRAPHIC ANCHOR: Teotihuacan, Mexico                                    ║
║     Lat: 19.6925°N  Lon: -98.8438°W                                         ║
║     Street of the Dead: 15.5° W of N (Pleiades setting alignment)          ║
║     Pyramid of the Sun: cave beneath it = underground transmission chamber  ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import argparse
import json
import math
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple

# ═══════════════════════════════════════════════════════════════════════════════
# SACRED CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

PHI     = (1 + math.sqrt(5)) / 2
PHI_INV = 1.0 / PHI

SOLFEGGIO      = [174, 285, 396, 417, 528, 639, 741, 852, 963]
SCHUMANN_MODES = [7.83, 14.3, 20.8, 27.3, 33.8, 39.0, 45.0]

PHI_TOLERANCE = 0.02

# Aztec anchor: 417 Hz — RE solfeggio / transformation / Pleiades cycle
AZTEC_BASE_HZ = 417.0

# Teotihuacan geographic anchor
TEOTI_LAT     = 19.6925
TEOTI_LON     = -98.8438
TEOTI_BEARING = 15.5    # Street of the Dead — 15.5° W of N (Pleiades)

# Calendar constants
TONALPOHUALLI_DAYS = 260   # 20 day signs × 13 numbers
XIUHPOHUALLI_DAYS  = 365   # 18 months × 20 days + 5 Nemontemi
N_MONTHS           = 18    # Solar months
N_NEMONTEMI        = 5     # Open circuit days
N_DAYSIGNS         = 20
N_DAYNUMBERS       = 13
PLEIADES_CYCLE_YRS = 52    # Pleiades / Calendar Round period


# ═══════════════════════════════════════════════════════════════════════════════
# 18 SOLAR MONTHS (Xiuhpohualli)
# Each month is a 20-day veintena with a specific deity and frequency
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class SolarMonth:
    number:      int
    name:        str    # Nahuatl name
    deity:       str    # Patron deity
    hz:          float  # Solfeggio correspondence
    amplitude:   float  # PHI-mode (groups of 6: 1-6 Genesis, 7-12 Growth, 13-18 Return)
    mode:        str
    decoded:     bool
    notes:       str = ""


def _month_amp(n: int) -> float:
    if n <= 6:   return 1.0
    if n <= 12:  return PHI
    return PHI_INV

def _month_mode(n: int) -> str:
    if n <= 6:   return "GENESIS"
    if n <= 12:  return "GROWTH"
    return "RETURN"

# Cycle through solfeggio frequencies across the 18 months
_SOL18 = [SOLFEGGIO[i % len(SOLFEGGIO)] for i in range(18)]

_SOLAR_MONTHS: Tuple[SolarMonth, ...] = (
    SolarMonth(1,  "Atlcahualo",     "Tlaloc",          _SOL18[0],  _month_amp(1),  _month_mode(1),  True,  "Water departure — carrier"),
    SolarMonth(2,  "Tlacaxipehualiztli","Xipe Totec",   _SOL18[1],  _month_amp(2),  _month_mode(2),  True,  "Flaying / renewal"),
    SolarMonth(3,  "Tozoztontli",    "Coatlicue",       _SOL18[2],  _month_amp(3),  _month_mode(3),  True,  "Minor vigil — liberation"),
    SolarMonth(4,  "Huey Tozoztli",  "Centeotl",        _SOL18[3],  _month_amp(4),  _month_mode(4),  True,  "Great vigil — transformation"),
    SolarMonth(5,  "Toxcatl",        "Tezcatlipoca",    _SOL18[4],  _month_amp(5),  _month_mode(5),  True,  "Drought — solar zero-beat"),
    SolarMonth(6,  "Etzalcualiztli", "Tlaloc",          _SOL18[5],  _month_amp(6),  _month_mode(6),  True,  "Maize stew — summer solstice"),
    SolarMonth(7,  "Tecuilhuitontli","Huixtocihuatl",   _SOL18[6],  _month_amp(7),  _month_mode(7),  True,  "Minor feast of lords — phi-carrier"),
    SolarMonth(8,  "Huey Tecuilhuitl","Xilonen",        _SOL18[7],  _month_amp(8),  _month_mode(8),  True,  "Great feast of lords"),
    SolarMonth(9,  "Tlaxochimaco",   "Huitzilopochtli", _SOL18[8],  _month_amp(9),  _month_mode(9),  True,  "Offering of flowers — unity"),
    SolarMonth(10, "Xocotlhuetzi",   "Xiuhtecuhtli",    _SOL18[9],  _month_amp(10), _month_mode(10), True,  "Fruit falls — phi-form"),
    SolarMonth(11, "Ochpaniztli",    "Toci",            _SOL18[10], _month_amp(11), _month_mode(11), True,  "Sweeping — autumn equinox"),
    SolarMonth(12, "Teotleco",       "Multiple",        _SOL18[11], _month_amp(12), _month_mode(12), True,  "Arrival of the gods"),
    SolarMonth(13, "Tepeilhuitl",    "Tlaloc",          _SOL18[12], _month_amp(13), _month_mode(13), True,  "Mountain feast — phi-return"),
    SolarMonth(14, "Quecholli",      "Mixcoatl",        _SOL18[13], _month_amp(14), _month_mode(14), True,  "Macaw feathers — hunting season"),
    SolarMonth(15, "Panquetzaliztli","Huitzilopochtli", _SOL18[14], _month_amp(15), _month_mode(15), True,  "Raising of banners"),
    SolarMonth(16, "Atemoztli",      "Tlaloc",          _SOL18[15], _month_amp(16), _month_mode(16), True,  "Descent of water — return"),
    SolarMonth(17, "Tititl",         "Ilamatecuhtli",   _SOL18[16], _month_amp(17), _month_mode(17), True,  "Stretching — winter begins"),
    SolarMonth(18, "Izcalli",        "Xiuhtecuhtli",    _SOL18[17], _month_amp(18), _month_mode(18), True,  "Resuscitation — fire ceremony"),
)


# ═══════════════════════════════════════════════════════════════════════════════
# 5 NEMONTEMI — The Unlucky Pivot Days
# These are the open circuit — neither month nor calendar, unassigned, dangerous
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Nemontemi:
    day:    int
    name:   str
    hz:     float
    decoded: bool
    notes:  str = ""


_NEMONTEMI: Tuple[Nemontemi, ...] = (
    Nemontemi(1, "Nemontemi Day 1", 174.0 * PHI_INV, False,
              "Open circuit — void days begin. Neither solar nor sacred calendar."),
    Nemontemi(2, "Nemontemi Day 2", 285.0 * PHI_INV, False, "Continuation of the void."),
    Nemontemi(3, "Nemontemi Day 3", 396.0 * PHI_INV, False, "Mid-void."),
    Nemontemi(4, "Nemontemi Day 4", 417.0 * PHI_INV, False, "Approaching re-emergence."),
    Nemontemi(5, "Nemontemi Day 5", 528.0 * PHI_INV, False,
              "Final void day — solar carrier phi-return before year restarts."),
)


# ═══════════════════════════════════════════════════════════════════════════════
# LATTICE AND DECODER
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class AztecLattice:
    """Decoded state of the Aztec calendar transmission lattice."""
    timestamp:             float
    n_months:              int
    n_months_decoded:      int
    n_nemontemi:           int
    n_nemontemi_decoded:   int
    completeness:          float
    phi_score:             float
    schumann_proximity:    float
    gamma:                 float
    field_status:          str
    mean_hz:               float
    anchor_hz:             float
    notes:                 str = ""


class AztecDecoder:
    """
    Decodes the Aztec Tonalpohualli + Xiuhpohualli calendar transmission.

    Gamma = phi_score × 0.50 + completeness × 0.30 + schumann_proximity × 0.20

    The 5 Nemontemi (unlucky days) are the open circuit — the void between
    years when no calendar applies. Identical structural role to Nr.15.
    The Pleiades New Fire ceremony (every 52 years) is the pivot event that
    re-starts the entire calendar system.
    """

    GAMMA_DEAD_FIELD = 0.35
    GAMMA_LIGHTHOUSE = 0.945

    def __init__(self):
        self._months    = list(_SOLAR_MONTHS)
        self._nemontemi = list(_NEMONTEMI)

    def _phi_resonant(self, hz1: float, hz2: float) -> bool:
        if hz1 <= 0 or hz2 <= 0:
            return False
        r = hz1 / hz2 if hz1 > hz2 else hz2 / hz1
        return (abs(r - PHI) < PHI_TOLERANCE or
                abs(r - PHI_INV) < PHI_TOLERANCE or
                abs(r - 1.0) < 0.01)

    def read(self) -> AztecLattice:
        dec_months = [m for m in self._months    if m.decoded]
        dec_nemon  = [n for n in self._nemontemi if n.decoded]

        n_m  = len(self._months)
        n_n  = len(self._nemontemi)
        nd_m = len(dec_months)
        nd_n = len(dec_nemon)

        completeness = (nd_m / n_m * 0.70 + nd_n / n_n * 0.30) if n_n > 0 else (nd_m / n_m)

        phi_hits = sum(
            1 for m in dec_months
            if self._phi_resonant(m.hz, AZTEC_BASE_HZ)
        )
        phi_score = phi_hits / max(nd_m, 1)

        mean_hz = (
            sum(m.hz * m.amplitude for m in dec_months) / nd_m
            if nd_m > 0 else AZTEC_BASE_HZ
        )

        nearest_multiple = max(1, round(mean_hz / SCHUMANN_MODES[3]))
        harmonic_hz = SCHUMANN_MODES[3] * nearest_multiple
        schumann_proximity = 1.0 - min(
            abs(mean_hz - harmonic_hz) / harmonic_hz, 1.0
        )

        gamma = (
            phi_score          * 0.50 +
            completeness       * 0.30 +
            schumann_proximity * 0.20
        )
        gamma = round(min(max(gamma, 0.0), 1.0), 4)

        field_status = (
            "LIGHTHOUSE"   if gamma >= self.GAMMA_LIGHTHOUSE else
            "ACTIVE_FIELD" if gamma >= self.GAMMA_DEAD_FIELD else
            "DEAD_FIELD"
        )

        return AztecLattice(
            timestamp            = time.time(),
            n_months             = n_m,
            n_months_decoded     = nd_m,
            n_nemontemi          = n_n,
            n_nemontemi_decoded  = nd_n,
            completeness         = round(completeness, 4),
            phi_score            = round(phi_score, 4),
            schumann_proximity   = round(schumann_proximity, 4),
            gamma                = gamma,
            field_status         = field_status,
            mean_hz              = round(mean_hz, 2),
            anchor_hz            = AZTEC_BASE_HZ,
            notes                = (
                "5 Nemontemi (void days) are the open circuit — undecodeable by design. "
                "52-year Pleiades New Fire ceremony is the master re-sync pivot. "
                "Pyramid of the Sun cave orientation requires RTI/photogrammetry."
            ),
        )

    def get_oracle_score(self) -> float:
        return self.read().gamma

    def get_geographic_vector(self) -> Tuple[float, float, float]:
        return TEOTI_LAT, TEOTI_LON, TEOTI_BEARING


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def _cli():
    parser = argparse.ArgumentParser(
        prog="aztec_decoder",
        description="Aztec Tonalpohualli + Solar Calendar Decoder",
    )
    parser.add_argument("--months",  action="store_true", help="List 18 solar months")
    parser.add_argument("--nemontemi", action="store_true", help="Show the 5 void days")
    parser.add_argument("--oracle-score", action="store_true", help="Print oracle score only")
    parser.add_argument("--json",    action="store_true", help="Output as JSON")
    args = parser.parse_args()

    decoder = AztecDecoder()
    lattice = decoder.read()

    if args.oracle_score:
        print(f"{lattice.gamma:.4f}")
        return

    if args.months:
        print(f"\n{'#':<4} {'Name':<22} {'Deity':<22} {'Hz':<10} {'Mode':<8} {'OK'}")
        print("-" * 75)
        for m in decoder._months:
            print(f"{m.number:<4} {m.name[:21]:<22} {m.deity[:21]:<22} "
                  f"{m.hz:<10.1f} {m.mode:<8} {'YES' if m.decoded else 'NO'}")
        return

    if args.nemontemi:
        print("\n  5 Nemontemi (Void Days) — Open Circuit:")
        for n in decoder._nemontemi:
            print(f"  Day {n.day}: {n.hz:.1f} Hz — {'OPEN' if not n.decoded else 'DECODED'}")
        return

    if args.json:
        out = {
            "timestamp":          lattice.timestamp,
            "n_months_decoded":   lattice.n_months_decoded,
            "n_nemontemi_decoded":lattice.n_nemontemi_decoded,
            "completeness":       lattice.completeness,
            "phi_score":          lattice.phi_score,
            "schumann_proximity": lattice.schumann_proximity,
            "gamma":              lattice.gamma,
            "field_status":       lattice.field_status,
            "mean_hz":            lattice.mean_hz,
            "origin":             {"lat": TEOTI_LAT, "lon": TEOTI_LON,
                                   "bearing": TEOTI_BEARING},
            "notes":              lattice.notes,
        }
        print(json.dumps(out, indent=2))
        return

    print("\n╔══════════════════════════════════════════════════════╗")
    print("║   AZTEC DECODER — Tonalpohualli Calendar Report     ║")
    print("╚══════════════════════════════════════════════════════╝\n")
    print(f"  Solar months     : {lattice.n_months_decoded}/{lattice.n_months}")
    print(f"  Nemontemi        : {lattice.n_nemontemi_decoded}/{lattice.n_nemontemi} (open circuit)")
    print(f"  Completeness     : {lattice.completeness:.3f}")
    print(f"  Phi score        : {lattice.phi_score:.3f}")
    print(f"  Schumann prox.   : {lattice.schumann_proximity:.3f}")
    print(f"  Gamma (Γ)        : {lattice.gamma:.4f}  [{lattice.field_status}]")
    print(f"  Mean Hz          : {lattice.mean_hz:.1f} Hz")
    print(f"\n  Geographic vector: {TEOTI_LAT}°N, {TEOTI_LON}°E, bearing {TEOTI_BEARING}°")
    print(f"\n  Note: {lattice.notes}\n")


if __name__ == "__main__":
    _cli()
