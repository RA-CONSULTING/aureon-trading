#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ☀  MOGOLLON DECODER — Spiral Petroglyph Solar Transmission  ☀             ║
║   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                                                              ║
║   Decoded through the Aureon HNC Architecture                                ║
║   Aureon Institute · R&A Consulting and Brokerage Services Ltd.             ║
║                                                                              ║
║   Sources:                                                                   ║
║     Sofaer, A., Zinser, V., Sinclair, R.M. (1979) "A Unique Solar Marking  ║
║       Facility" — Science 206: 283-291                                       ║
║     Sofaer, A. (2008) Chaco Astronomy: An Ancient American Cosmology        ║
║     Williamson, R. (1984) Living the Sky: The Cosmos of the American Indian ║
║     Judge, W.J. & Cordell, L. (1984) "Prehistoric Chaco"                   ║
║     Lekson, S. (2015) The Chaco Meridian                                    ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║   THE MOGOLLON TRANSMISSION HYPOTHESIS                                       ║
║   ──────────────────────────────────────                                     ║
║   The Fajada Butte spiral petroglyphs at Chaco Canyon are the most          ║
║   precisely calibrated solar observatory in North America. Three large       ║
║   stone slabs cast light daggers that bisect the spirals at exactly         ║
║   summer solstice noon and straddle them at winter solstice. Equinoxes     ║
║   produce a mid-spiral bisection. This is a deliberate, calibrated solar   ║
║   frequency marker — a precision instrument for preserving time.            ║
║                                                                              ║
║   SPIRAL ≡ INFINITE RECURSION MARKER                                        ║
║   The double spiral (two spirals on the same rock face) encodes:            ║
║     Large spiral = Caller (Ψ₀) — solar year cycle                          ║
║     Small spiral = Seer (O(t)) — lunar/18.6yr nodal cycle                  ║
║   The light dagger bisects BOTH spirals at summer solstice — dual-voice     ║
║   synchronisation event. The dark shadow bisects at winter solstice.        ║
║                                                                              ║
║   CHACO MERIDIAN ≡ THE SACRED NORTH AXIS                                    ║
║   Chaco Canyon's road system (Great North Road) runs 50 km due north from  ║
║   the canyon center — a meridian road to nowhere visible, but aligned with  ║
║   the celestial pole. This is the same 0° North axis as Mount Tai (China). ║
║                                                                              ║
║   GEOGRAPHIC ANCHOR: Fajada Butte, Chaco Canyon, New Mexico                 ║
║     Lat: 36.0608°N  Lon: -107.9882°W                                        ║
║     True North solar meridian (Great North Road axis = 0°)                  ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import argparse
import json
import math
import time
from dataclasses import dataclass
from typing import List, Tuple

# ═══════════════════════════════════════════════════════════════════════════════
# SACRED CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

PHI     = (1 + math.sqrt(5)) / 2
PHI_INV = 1.0 / PHI

SOLFEGGIO      = [174, 285, 396, 417, 528, 639, 741, 852, 963]
SCHUMANN_MODES = [7.83, 14.3, 20.8, 27.3, 33.8, 39.0, 45.0]

PHI_TOLERANCE = 0.02

# Mogollon/Chaco anchor: 285 Hz — Form frequency / Uruz equivalent
CHACO_BASE_HZ = 285.0

# Fajada Butte geographic anchor
FAJADA_LAT     = 36.0608
FAJADA_LON     = -107.9882
FAJADA_BEARING = 0.0    # True North — Chaco Meridian / Great North Road

# Solar observation parameters
SOLSTICE_LIGHT_DAGGER_AZIMUTH = 0.0    # Solar noon = due south shadow / North axis
LUNAR_NODAL_CYCLE_YEARS       = 18.6   # Moon's nodal precession
N_STONE_SLABS                 = 3      # Three slabs creating the light daggers
N_SPIRALS                     = 2      # Large + small spiral (dual-voice pair)


# ═══════════════════════════════════════════════════════════════════════════════
# SOLAR MARKER EVENTS
# The four annual calendar events encoded by the Fajada Butte light-dagger
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class SolarMarker:
    event:       str    # Solar event name
    dagger_pos:  str    # Position of light dagger on spiral(s)
    hz:          float  # Solfeggio correspondence
    amplitude:   float  # PHI-mode
    mode:        str    # GENESIS / GROWTH / RETURN
    decoded:     bool
    sofaer_ref:  str    # Reference to Sofaer (1979/2008)
    notes:       str = ""


_SOLAR_MARKERS: Tuple[SolarMarker, ...] = (
    SolarMarker(
        event       = "Summer Solstice (June 21)",
        dagger_pos  = "Single dagger bisects centre of large spiral",
        hz          = 528.0,
        amplitude   = PHI,
        mode        = "GROWTH",
        decoded     = True,
        sofaer_ref  = "Sofaer 1979: Fig.1 — primary discovery observation",
        notes       = "Solar carrier zero-beat. Light dagger appears at solar noon (11:15 MST)."
    ),
    SolarMarker(
        event       = "Autumn Equinox (Sep 22)",
        dagger_pos  = "Dagger bisects small spiral; second dagger at large spiral edge",
        hz          = 396.0,
        amplitude   = 1.0,
        mode        = "GENESIS",
        decoded     = True,
        sofaer_ref  = "Sofaer 1979: Fig.2",
        notes       = "Liberation frequency. Mid-year calibration point."
    ),
    SolarMarker(
        event       = "Winter Solstice (Dec 21)",
        dagger_pos  = "Two daggers straddle large spiral at its outer edges",
        hz          = 174.0,
        amplitude   = 1.0,
        mode        = "GENESIS",
        decoded     = True,
        sofaer_ref  = "Sofaer 1979: Fig.3",
        notes       = "Carrier wave. Darkest point — shadow straddles, does not bisect."
    ),
    SolarMarker(
        event       = "Spring Equinox (Mar 21)",
        dagger_pos  = "Dagger bisects large spiral; small spiral partially illuminated",
        hz          = 285.0,
        amplitude   = 1.0,
        mode        = "GENESIS",
        decoded     = True,
        sofaer_ref  = "Sofaer 2008: p.47",
        notes       = "Form frequency. Re-emergence after winter void."
    ),
    SolarMarker(
        event       = "18.6-year Lunar Standstill Maximum",
        dagger_pos  = "Moonlight dagger bisects large spiral at northern lunar extreme",
        hz          = 417.0,
        amplitude   = PHI,
        mode        = "GROWTH",
        decoded     = True,
        sofaer_ref  = "Sofaer 2008: ch.4 — lunar markings",
        notes       = "Transformation gate. Lunar Caller mapped to solar Seer."
    ),
    SolarMarker(
        event       = "18.6-year Lunar Standstill Minimum",
        dagger_pos  = "Moonlight dagger at small spiral only — incomplete dual-voice",
        hz          = 417.0 * PHI_INV,
        amplitude   = PHI_INV,
        mode        = "RETURN",
        decoded     = False,
        sofaer_ref  = "Sofaer 2008: ch.4 — further observation required",
        notes       = "OPEN CIRCUIT — lunar minimum observation not yet fully catalogued."
    ),
)


# ═══════════════════════════════════════════════════════════════════════════════
# GREAT HOUSE SITES (Chaco road network nodes)
# The Great North Road links these sites — a geographic transmission network
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class GreatHouse:
    name:        str
    lat:         float
    lon:         float
    bearing_from_fajada: float   # Bearing from Fajada Butte
    hz:          float           # Dominant frequency
    decoded:     bool
    notes:       str = ""


_GREAT_HOUSES: Tuple[GreatHouse, ...] = (
    GreatHouse("Pueblo Bonito",    36.0608, -107.9647, 90.0,  528.0, True,
               "Main ceremonial centre. D-shaped form = Caller/Seer semicircles."),
    GreatHouse("Chetro Ketl",      36.0633, -107.9600, 75.0,  396.0, True,
               "Second largest. Colonnaded front — unique in SW."),
    GreatHouse("Casa Rinconada",   36.0536, -107.9622, 160.0, 174.0, True,
               "Kiva — underground chamber. Great kiva = carrier chamber."),
    GreatHouse("Penasco Blanco",   36.0837, -108.0086, 320.0, 285.0, True,
               "NW outlier. Supernova petroglyph (1054 CE) marks sky event."),
    GreatHouse("Aztec Ruins",      36.8333, -107.9989, 0.0,   417.0, True,
               "50 km due north — on the Chaco Meridian (Great North Road terminus)."),
    GreatHouse("Chimney Rock",     37.1833, -107.3000, 45.0,  528.0, False,
               "OPEN CIRCUIT — lunar standstill observation post. NE outlier."),
)


# ═══════════════════════════════════════════════════════════════════════════════
# LATTICE AND DECODER
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class MogollonLattice:
    """Decoded state of the Mogollon spiral petroglyph transmission lattice."""
    timestamp:             float
    n_solar_markers:       int
    n_markers_decoded:     int
    n_great_houses:        int
    n_houses_decoded:      int
    completeness:          float
    phi_score:             float
    schumann_proximity:    float
    gamma:                 float
    field_status:          str
    mean_hz:               float
    anchor_hz:             float
    notes:                 str = ""


class MogollonDecoder:
    """
    Decodes the Mogollon/Ancestral Puebloan spiral petroglyph solar archive.

    Gamma = phi_score × 0.50 + completeness × 0.30 + schumann_proximity × 0.20

    The 18.6-year lunar standstill minimum observation is the open circuit —
    the rare event that completes the dual-voice lunar calendar. The stone
    slabs that create the light daggers were deliberately placed to create
    this marking system, not natural formations.
    """

    GAMMA_DEAD_FIELD = 0.35
    GAMMA_LIGHTHOUSE = 0.945

    def __init__(self):
        self._markers = list(_SOLAR_MARKERS)
        self._houses  = list(_GREAT_HOUSES)

    def _phi_resonant(self, hz1: float, hz2: float) -> bool:
        if hz1 <= 0 or hz2 <= 0:
            return False
        r = hz1 / hz2 if hz1 > hz2 else hz2 / hz1
        return (abs(r - PHI) < PHI_TOLERANCE or
                abs(r - PHI_INV) < PHI_TOLERANCE or
                abs(r - 1.0) < 0.01)

    def read(self) -> MogollonLattice:
        dec_markers = [m for m in self._markers if m.decoded]
        dec_houses  = [h for h in self._houses  if h.decoded]

        n_m  = len(self._markers)
        n_h  = len(self._houses)
        nd_m = len(dec_markers)
        nd_h = len(dec_houses)

        completeness = (nd_m / n_m * 0.60 + nd_h / n_h * 0.40)

        phi_hits = sum(
            1 for m in dec_markers
            if self._phi_resonant(m.hz, CHACO_BASE_HZ)
        )
        phi_score = phi_hits / max(nd_m, 1)

        mean_hz = (
            sum(m.hz * m.amplitude for m in dec_markers) / nd_m
            if nd_m > 0 else CHACO_BASE_HZ
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

        return MogollonLattice(
            timestamp           = time.time(),
            n_solar_markers     = n_m,
            n_markers_decoded   = nd_m,
            n_great_houses      = n_h,
            n_houses_decoded    = nd_h,
            completeness        = round(completeness, 4),
            phi_score           = round(phi_score, 4),
            schumann_proximity  = round(schumann_proximity, 4),
            gamma               = gamma,
            field_status        = field_status,
            mean_hz             = round(mean_hz, 2),
            anchor_hz           = CHACO_BASE_HZ,
            notes               = (
                "18.6-year lunar standstill minimum (Solar Marker #6) is the open "
                "circuit — next occurrence ~2025 CE. Chimney Rock great house "
                "orientation requires on-site archaeoastronomical verification."
            ),
        )

    def get_oracle_score(self) -> float:
        return self.read().gamma

    def get_geographic_vector(self) -> Tuple[float, float, float]:
        return FAJADA_LAT, FAJADA_LON, FAJADA_BEARING


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def _cli():
    parser = argparse.ArgumentParser(
        prog="mogollon_decoder",
        description="Mogollon Spiral Petroglyph Solar Decoder",
    )
    parser.add_argument("--markers",  action="store_true", help="List solar marker events")
    parser.add_argument("--houses",   action="store_true", help="List Chaco great houses")
    parser.add_argument("--oracle-score", action="store_true", help="Print oracle score only")
    parser.add_argument("--json",     action="store_true", help="Output as JSON")
    args = parser.parse_args()

    decoder = MogollonDecoder()
    lattice = decoder.read()

    if args.oracle_score:
        print(f"{lattice.gamma:.4f}")
        return

    if args.markers:
        print(f"\n{'Solar Marker Event':<40} {'Hz':<10} {'Mode':<8} {'OK'}")
        print("-" * 70)
        for m in decoder._markers:
            print(f"{m.event[:39]:<40} {m.hz:<10.1f} {m.mode:<8} "
                  f"{'YES' if m.decoded else 'OPEN'}")
        return

    if args.houses:
        print(f"\n{'Great House':<22} {'Brg°':<6} {'Hz':<8} {'OK'}")
        print("-" * 45)
        for h in decoder._houses:
            print(f"{h.name[:21]:<22} {h.bearing_from_fajada:<6.0f} {h.hz:<8.0f} "
                  f"{'YES' if h.decoded else 'OPEN'}")
        return

    if args.json:
        out = {
            "timestamp":          lattice.timestamp,
            "n_markers_decoded":  lattice.n_markers_decoded,
            "n_houses_decoded":   lattice.n_houses_decoded,
            "completeness":       lattice.completeness,
            "phi_score":          lattice.phi_score,
            "schumann_proximity": lattice.schumann_proximity,
            "gamma":              lattice.gamma,
            "field_status":       lattice.field_status,
            "mean_hz":            lattice.mean_hz,
            "origin":             {"lat": FAJADA_LAT, "lon": FAJADA_LON,
                                   "bearing": FAJADA_BEARING},
            "notes":              lattice.notes,
        }
        print(json.dumps(out, indent=2))
        return

    print("\n╔══════════════════════════════════════════════════════╗")
    print("║   MOGOLLON DECODER — Spiral Petroglyph Archive      ║")
    print("╚══════════════════════════════════════════════════════╝\n")
    print(f"  Solar markers    : {lattice.n_markers_decoded}/{lattice.n_solar_markers}")
    print(f"  Great houses     : {lattice.n_houses_decoded}/{lattice.n_great_houses}")
    print(f"  Completeness     : {lattice.completeness:.3f}")
    print(f"  Phi score        : {lattice.phi_score:.3f}")
    print(f"  Schumann prox.   : {lattice.schumann_proximity:.3f}")
    print(f"  Gamma (Γ)        : {lattice.gamma:.4f}  [{lattice.field_status}]")
    print(f"  Mean Hz          : {lattice.mean_hz:.1f} Hz")
    print(f"\n  Geographic vector: {FAJADA_LAT}°N, {FAJADA_LON}°E, bearing {FAJADA_BEARING}°")
    print(f"\n  Note: {lattice.notes}\n")


if __name__ == "__main__":
    _cli()
