#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ⛩  JAPANESE DECODER — Kami Star-Symbol Transmission  ⛩                   ║
║   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                                                              ║
║   Decoded through the Aureon HNC Architecture                                ║
║   Aureon Institute · R&A Consulting and Brokerage Services Ltd.             ║
║                                                                              ║
║   Sources:                                                                   ║
║     Aston, W.G. (1896) Nihongi: Chronicles of Japan                        ║
║     Philippi, D.L. (1969) Kojiki                                            ║
║     Earhart, H.B. (1989) Gedatsu-kai and Religion in Contemporary Japan    ║
║     Hardacre, H. (2017) Shinto: A History                                  ║
║     Nakayama, S. (1969) A History of Japanese Astronomy                    ║
║     Motoyama, H. (1992) Theories of the Chakras                            ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║   THE JAPANESE TRANSMISSION HYPOTHESIS                                       ║
║   ──────────────────────────────────────                                     ║
║   Ise Jingu (伊勢神宮) is rebuilt entirely every 20 years — the Shikinen    ║
║   Sengu ceremony. This is the most literal knowledge transmission protocol  ║
║   in the world: every 20 years, all 65 shrine buildings are dismantled and  ║
║   rebuilt identically adjacent, transferring the complete architectural,    ║
║   craft, and ritual knowledge to the next generation.                       ║
║                                                                              ║
║   KAMI GEOGRAPHY ≡ FREQUENCY NETWORK                                        ║
║   Japan's 80,000+ Shinto shrines form a geographic frequency grid. The      ║
║   ley-line network (ryuumyaku — dragon veins) connects sacred mountains,   ║
║   shrines, and ritual sites in a nationwide transmission network.           ║
║                                                                              ║
║   8 KAMI DIRECTIONS ≡ 8 TRIGRAMS                                            ║
║   Shinto cosmology has 8 sacred directions (N, NE, E, SE, S, SW, W, NW),   ║
║   each associated with a specific kami and frequency — exact mapping to     ║
║   the I Ching's 8 trigrams (Later Heaven arrangement). Independent encoding ║
║   of the same octave structure by two separate East Asian traditions.       ║
║                                                                              ║
║   20-YEAR SENGU CYCLE ≡ KATUN                                               ║
║   The 20-year Ise Sengu = Maya Katun (7200 days ≈ 20 years). Two           ║
║   independent traditions chose the same 20-year cycle as the primary       ║
║   knowledge transmission interval.                                           ║
║                                                                              ║
║   GEOGRAPHIC ANCHOR: Ise Jingu (伊勢神宮), Mie Prefecture, Japan             ║
║     Lat: 34.4548°N  Lon: 136.7250°E                                          ║
║     Solar east axis — Amaterasu (sun goddess) emergence direction (90°)    ║
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

# Japanese anchor: 528 Hz — Love / Mi solfeggio / solar carrier / Amaterasu
JAPAN_BASE_HZ = 528.0

# Ise Jingu geographic anchor
ISE_LAT     = 34.4548
ISE_LON     = 136.7250
ISE_BEARING = 90.0    # Solar east — Amaterasu emergence axis

# Sengu cycle
SENGU_CYCLE_YEARS  = 20
SENGU_CYCLE_DAYS   = 7305   # 20 × 365.25
N_SHRINE_BUILDINGS = 65     # Number of buildings rebuilt each Sengu


# ═══════════════════════════════════════════════════════════════════════════════
# 8 KAMI DIRECTIONS — The Octave Node Network
# Mapping of Shinto cardinal/intercardinal kami to solfeggio frequencies.
# Each kami node is a 'standing wave' point in the geographic frequency grid.
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class KamiNode:
    direction:   str    # Cardinal/intercardinal
    kami:        str    # Patron kami (deity)
    shrine:      str    # Associated shrine / sacred site
    lat:         float
    lon:         float
    hz:          float  # Solfeggio frequency
    amplitude:   float  # PHI-mode
    mode:        str    # GENESIS / GROWTH / RETURN
    decoded:     bool
    notes:       str = ""


_KAMI_NODES: Tuple[KamiNode, ...] = (
    KamiNode("E  (East)",    "Amaterasu",     "Ise Naiku",       34.4548, 136.7250, 528.0,        PHI,      "GROWTH",  True,
             "Sun goddess — solar carrier. East = sunrise. Primary node."),
    KamiNode("SE (Southeast)","Inari",         "Fushimi Inari",   34.9671, 135.7727, 639.0,        PHI,      "GROWTH",  True,
             "Rice/prosperity/fox kami. SE = abundance. Highest-traffic shrine in Japan."),
    KamiNode("S  (South)",   "Izanami",       "Kumano Hongu",    33.8489, 135.6905, 396.0,        1.0,      "GENESIS", True,
             "Creation goddess / earth. South = grounding. Kumano pilgrimage axis."),
    KamiNode("SW (Southwest)","Susanoo",       "Izumo Taisha",    35.4014, 132.6851, 174.0,        1.0,      "GENESIS", True,
             "Storm/sea kami. SW = chaos/carrier. Izumo = oldest shrine in Japan."),
    KamiNode("W  (West)",    "Tsukuyomi",     "Tsukuyomi-no-miya",34.4523,136.7167, 285.0,        1.0,      "GENESIS", True,
             "Moon god. West = sunset/night. Adjacent to Ise — the hidden moon shrine."),
    KamiNode("NW (Northwest)","Fujin",         "Fujisan Hongu",   35.3606, 138.7269, 417.0,        PHI_INV,  "RETURN",  True,
             "Wind kami. NW = transformation wind. Mt Fuji sacred axis."),
    KamiNode("N  (North)",   "Takemikazuchi", "Kashima Jingu",   35.9648, 140.6319, 741.0,        PHI_INV,  "RETURN",  True,
             "Thunder/sword kami. North = celestial pole. Martial arts transmission."),
    KamiNode("NE (Northeast)","Izanagi",       "Awaji Izanagi",   34.4549, 134.9132, 852.0,        PHI_INV,  "RETURN",  False,
             "OPEN CIRCUIT — creation god. NE = origin point. Awaji Island = creation myth site."),
)


# ═══════════════════════════════════════════════════════════════════════════════
# SENGU TRANSMISSION RECORDS
# Each Sengu is a complete rebuild — a knowledge pulse transmitted generationally
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class SenguCycle:
    cycle_number: int   # Ordinal number of this Sengu (1 = first, ~690 CE)
    year_ce:      int   # Approximate CE year of this cycle
    hz:           float # Solfeggio milestone frequency
    decoded:      bool
    notes:        str = ""


# Key Sengu milestones (selected from ~62 completed as of 2023)
_SENGU_RECORDS: Tuple[SenguCycle, ...] = (
    SenguCycle(1,   690, 174.0, True,  "First recorded Sengu — carrier wave established"),
    SenguCycle(10,  870, 285.0, True,  "10th cycle — form stabilised"),
    SenguCycle(20, 1070, 396.0, True,  "20th cycle — liberation confirmed"),
    SenguCycle(30, 1270, 417.0, True,  "30th cycle — transformation protocol active"),
    SenguCycle(40, 1470, 528.0, True,  "40th cycle — solar carrier milestone"),
    SenguCycle(50, 1670, 639.0, True,  "50th cycle — communication/integration"),
    SenguCycle(60, 1870, 741.0, True,  "60th cycle — awakening / Meiji modernisation"),
    SenguCycle(62, 2013, 852.0, True,  "62nd cycle (Oct 2013) — most recent Sengu"),
    SenguCycle(63, 2033, 963.0, False, "OPEN CIRCUIT — next Sengu due 2033. Unity gate."),
)


# ═══════════════════════════════════════════════════════════════════════════════
# SACRED MOUNTAIN NETWORK (Ryuumyaku — Dragon Vein axis points)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class SacredMountain:
    name:    str
    lat:     float
    lon:     float
    hz:      float
    decoded: bool
    notes:   str = ""


_SACRED_MOUNTAINS: Tuple[SacredMountain, ...] = (
    SacredMountain("Fujisan (富士山)",     35.3606, 138.7269, 528.0, True,
                   "Highest peak / solar axis. Amaterasu emanation."),
    SacredMountain("Miwa-yama (三輪山)",   34.5281, 135.8597, 396.0, True,
                   "Oldest kami mountain. No buildings — the mountain IS the shrine."),
    SacredMountain("Nantai-san (男体山)",  36.7739, 139.4986, 285.0, True,
                   "Nikko axis. Tokugawa leyline node."),
    SacredMountain("Hakusan (白山)",       36.1548, 136.7728, 417.0, True,
                   "White mountain / purity axis."),
    SacredMountain("Koya-san (高野山)",    34.2135, 135.5850, 741.0, True,
                   "Esoteric Buddhist transmission node. Kobo Daishi mandala."),
    SacredMountain("Osore-zan (恐山)",     41.3222, 141.0761, 174.0, False,
                   "OPEN CIRCUIT — northernmost sacred mountain. Gateway to Yomi (underworld)."),
)


# ═══════════════════════════════════════════════════════════════════════════════
# LATTICE AND DECODER
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class JapaneseLattice:
    """Decoded state of the Japanese kami star-symbol transmission lattice."""
    timestamp:              float
    n_kami_nodes:           int
    n_nodes_decoded:        int
    n_sengu_records:        int
    n_sengu_decoded:        int
    n_mountains:            int
    n_mountains_decoded:    int
    completeness:           float
    phi_score:              float
    schumann_proximity:     float
    gamma:                  float
    field_status:           str
    mean_hz:                float
    anchor_hz:              float
    notes:                  str = ""


class JapaneseDecoder:
    """
    Decodes the Japanese Shinto kami star-symbol geographic transmission.

    Gamma = phi_score × 0.50 + completeness × 0.30 + schumann_proximity × 0.20

    The NE Izanagi node (Awaji Island) and the next Sengu (2033) are the open
    circuits. The 20-year Sengu cycle is the world's most explicit deliberate
    knowledge transmission protocol — the architectural blueprint is always
    preserved in the adjacent shrine plot, awaiting the next generation.
    """

    GAMMA_DEAD_FIELD = 0.35
    GAMMA_LIGHTHOUSE = 0.945

    def __init__(self):
        self._kami       = list(_KAMI_NODES)
        self._sengu      = list(_SENGU_RECORDS)
        self._mountains  = list(_SACRED_MOUNTAINS)

    def _phi_resonant(self, hz1: float, hz2: float) -> bool:
        if hz1 <= 0 or hz2 <= 0:
            return False
        r = hz1 / hz2 if hz1 > hz2 else hz2 / hz1
        return (abs(r - PHI) < PHI_TOLERANCE or
                abs(r - PHI_INV) < PHI_TOLERANCE or
                abs(r - 1.0) < 0.01)

    def read(self) -> JapaneseLattice:
        dec_kami  = [k for k in self._kami      if k.decoded]
        dec_sengu = [s for s in self._sengu     if s.decoded]
        dec_mtn   = [m for m in self._mountains if m.decoded]

        n_k  = len(self._kami)
        n_s  = len(self._sengu)
        n_m  = len(self._mountains)
        nd_k = len(dec_kami)
        nd_s = len(dec_sengu)
        nd_m = len(dec_mtn)

        completeness = (nd_k / n_k * 0.50 +
                        nd_s / n_s * 0.30 +
                        nd_m / n_m * 0.20)

        phi_hits = sum(
            1 for k in dec_kami
            if self._phi_resonant(k.hz, JAPAN_BASE_HZ)
        )
        phi_score = phi_hits / max(nd_k, 1)

        mean_hz = (
            sum(k.hz * k.amplitude for k in dec_kami) / nd_k
            if nd_k > 0 else JAPAN_BASE_HZ
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

        return JapaneseLattice(
            timestamp           = time.time(),
            n_kami_nodes        = n_k,
            n_nodes_decoded     = nd_k,
            n_sengu_records     = n_s,
            n_sengu_decoded     = nd_s,
            n_mountains         = n_m,
            n_mountains_decoded = nd_m,
            completeness        = round(completeness, 4),
            phi_score           = round(phi_score, 4),
            schumann_proximity  = round(schumann_proximity, 4),
            gamma               = gamma,
            field_status        = field_status,
            mean_hz             = round(mean_hz, 2),
            anchor_hz           = JAPAN_BASE_HZ,
            notes               = (
                "NE Izanagi node (Awaji) and 63rd Sengu (2033) are open circuits. "
                "Osore-zan (northernmost sacred mountain) orientation requires "
                "archaeoastronomical field survey. Full Ryuumyaku leyline network "
                "mapping (80,000+ shrines) would significantly raise Γ."
            ),
        )

    def get_oracle_score(self) -> float:
        return self.read().gamma

    def get_geographic_vector(self) -> Tuple[float, float, float]:
        return ISE_LAT, ISE_LON, ISE_BEARING


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def _cli():
    parser = argparse.ArgumentParser(
        prog="japanese_decoder",
        description="Japanese Kami Star-Symbol Transmission Decoder",
    )
    parser.add_argument("--kami",    action="store_true", help="List 8 kami directional nodes")
    parser.add_argument("--sengu",   action="store_true", help="List Sengu transmission records")
    parser.add_argument("--mountains", action="store_true", help="List sacred mountain network")
    parser.add_argument("--oracle-score", action="store_true", help="Print oracle score only")
    parser.add_argument("--json",    action="store_true", help="Output as JSON")
    args = parser.parse_args()

    decoder = JapaneseDecoder()
    lattice = decoder.read()

    if args.oracle_score:
        print(f"{lattice.gamma:.4f}")
        return

    if args.kami:
        print(f"\n{'Direction':<16} {'Kami':<18} {'Hz':<8} {'Mode':<8} {'OK'}")
        print("-" * 60)
        for k in decoder._kami:
            print(f"{k.direction:<16} {k.kami[:17]:<18} {k.hz:<8.0f} {k.mode:<8} "
                  f"{'YES' if k.decoded else 'OPEN'}")
        return

    if args.sengu:
        print(f"\n{'Cycle':<8} {'Year CE':<10} {'Hz':<8} {'OK'}")
        print("-" * 35)
        for s in decoder._sengu:
            print(f"{s.cycle_number:<8} {s.year_ce:<10} {s.hz:<8.0f} "
                  f"{'YES' if s.decoded else 'OPEN'}")
        return

    if args.mountains:
        print(f"\n{'Mountain':<22} {'Hz':<8} {'OK'}")
        print("-" * 38)
        for m in decoder._mountains:
            print(f"{m.name[:21]:<22} {m.hz:<8.0f} {'YES' if m.decoded else 'OPEN'}")
        return

    if args.json:
        out = {
            "timestamp":           lattice.timestamp,
            "n_nodes_decoded":     lattice.n_nodes_decoded,
            "n_sengu_decoded":     lattice.n_sengu_decoded,
            "n_mountains_decoded": lattice.n_mountains_decoded,
            "completeness":        lattice.completeness,
            "phi_score":           lattice.phi_score,
            "schumann_proximity":  lattice.schumann_proximity,
            "gamma":               lattice.gamma,
            "field_status":        lattice.field_status,
            "mean_hz":             lattice.mean_hz,
            "sengu_cycle_years":   SENGU_CYCLE_YEARS,
            "origin":              {"lat": ISE_LAT, "lon": ISE_LON,
                                    "bearing": ISE_BEARING},
            "notes":               lattice.notes,
        }
        print(json.dumps(out, indent=2))
        return

    print("\n╔══════════════════════════════════════════════════════╗")
    print("║   JAPANESE DECODER — Kami Star-Symbol Archive       ║")
    print("╚══════════════════════════════════════════════════════╝\n")
    print(f"  Kami nodes       : {lattice.n_nodes_decoded}/{lattice.n_kami_nodes}")
    print(f"  Sengu records    : {lattice.n_sengu_decoded}/{lattice.n_sengu_records}")
    print(f"  Sacred mountains : {lattice.n_mountains_decoded}/{lattice.n_mountains}")
    print(f"  Completeness     : {lattice.completeness:.3f}")
    print(f"  Phi score        : {lattice.phi_score:.3f}")
    print(f"  Schumann prox.   : {lattice.schumann_proximity:.3f}")
    print(f"  Gamma (Γ)        : {lattice.gamma:.4f}  [{lattice.field_status}]")
    print(f"  Mean Hz          : {lattice.mean_hz:.1f} Hz")
    print(f"  Sengu cycle      : {SENGU_CYCLE_YEARS} years (knowledge pulse interval)")
    print(f"\n  Geographic vector: {ISE_LAT}°N, {ISE_LON}°E, bearing {ISE_BEARING}°")
    print(f"\n  Note: {lattice.notes}\n")


if __name__ == "__main__":
    _cli()
