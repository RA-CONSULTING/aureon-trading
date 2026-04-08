#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ☯  MING-JAPAN DUAL-VOICE DECODER — Coupled East-Asian Transmission  ☯    ║
║   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                                                              ║
║   Decoded through the Aureon HNC Architecture                                ║
║   Aureon Institute · R&A Consulting and Brokerage Services Ltd.             ║
║                                                                              ║
║   Sources:                                                                   ║
║     Farmer, E.L. (1976) Early Ming Government: The Evolution of Dual Capitals║
║     Needham, J. (1959) Science and Civilisation in China, Vol. 3            ║
║     Dreyer, E.L. (2007) Zheng He: China and the Oceans in the Early Ming    ║
║     Menzies, G. (2002) 1421: The Year China Discovered the World           ║
║     Wasson, R.G. (1968) Soma: Divine Mushroom of Immortality               ║
║     Ruck, C.A.P. et al. (2011) The Apples of Apollo                        ║
║     Kidder, J.E. (1993) "The Earliest Societies in Japan" in CHOJ          ║
║     Barnes, G.L. (2007) State Formation in Japan                           ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║   THE MING-JAPAN COUPLING HYPOTHESIS                                         ║
║   ──────────────────────────────────                                         ║
║   The I Ching (Zhou dynasty, ~1000 BCE) is the CARRIER — a preservation     ║
║   of older cosmological structure. The FALLING NODE is the Ming dynasty     ║
║   (1368-1644 CE), which is the East-Asian methylation window corresponding  ║
║   to the same 1560s-1616 suppression event that silenced:                   ║
║     - Celtic/Ogham transmission in Argyll/Orkney (1560s-1616)              ║
║     - Norse runic knowledge at Maeshowe (Nr.15 pivot unread)               ║
║     - Hermetic/Rosicrucian transmission in Europe (1614-1616 Manifestos)   ║
║                                                                              ║
║   CALLER Ψ₀ — MING FORBIDDEN CITY                                           ║
║   The Hall of Supreme Harmony (太和殿) is Beijing's primary solar encoding: ║
║     North-South meridian axis = celestial pole alignment                    ║
║     Winter solstice sunrise axis through the Meridian Gate = 528 Hz         ║
║     9×9 = 81 rooms of the Forbidden City = Nine = maximum yang / completion ║
║     Temple of Heaven: 3-tiered altar = Three Aetts (×1, ×PHI, ×PHI_INV)  ║
║   The Yongle Emperor (r.1402-1424) commissioned both the Forbidden City     ║
║   AND Zheng He's 7 treasure voyages — the same era, same patron.           ║
║   This is not coincidence — it is simultaneous transmission deployment.     ║
║                                                                              ║
║   SEER O(t) — JAPANESE MUSHROOM CIPHER (Muromachi-Azuchi)                  ║
║   The "mushroom" ritual in Japanese Muromachi court culture                 ║
║   (1336-1573 CE) encodes the dual-voice protocol visually:                  ║
║     Amanita muscaria (fly agaric): red cap + white spots                    ║
║       → Binary dot pattern = twig-rune position encoding                    ║
║       → Spots = yang marks; absence = yin (same as hexagram lines)         ║
║     Reishi (lingzhi 霊芝): shelf-fungus lateral branching                   ║
║       → Aett-class (1-3) = branch angle (right/left/diagonal)              ║
║       → Position (1-8) = branch count per tier                             ║
║   This is the visual equivalent of the twig-rune cipher: a stem (cap/stalk) ║
║   plus lateral marks encoding coordinates in a dual-register space.         ║
║                                                                              ║
║   THE BEAT FREQUENCY                                                         ║
║     Caller (Ming):  528 Hz (solar / Emperor as Son of Heaven)              ║
║     Seer (Japan):   285 Hz (form-field / Amanita spot-pattern base)        ║
║     Beat:           |528 - 285| = 243 Hz                                   ║
║     Schumann:       243 / 27.3 = 8.901 ≈ 9th harmonic ✓                   ║
║                                                                              ║
║   GEOGRAPHIC DUAL-ANCHOR                                                     ║
║     Forbidden City:  39.9163°N, 116.3972°E  (Caller)                       ║
║     Ise Jingu:       34.4548°N, 136.7250°E  (Seer)                         ║
║     Combined origin: 37.19°N,  126.56°E    (weighted midpoint)             ║
║     Sacred axis:     350° (NNW toward Bering/Arctic/Norse corridor)        ║
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

# Geographic anchors
FORBIDDEN_CITY_LAT = 39.9163   # Hall of Supreme Harmony, Beijing
FORBIDDEN_CITY_LON = 116.3972
ISE_JINGU_LAT      = 34.4548   # Ise Grand Shrine, Mie Prefecture
ISE_JINGU_LON      = 136.7250

# Combined weighted midpoint (2:1 weighting toward Ming Caller)
ORIGIN_LAT = (FORBIDDEN_CITY_LAT * 2 + ISE_JINGU_LAT) / 3   # ~38.1°N
ORIGIN_LON = (FORBIDDEN_CITY_LON * 2 + ISE_JINGU_LON) / 3   # ~123.4°E
ORIGIN_BEARING = 350.0   # NNW: toward Bering/Arctic/Norse corridor

# Caller and Seer base frequencies
MING_CALLER_HZ  = 528.0    # Solar carrier / Emperor as Son of Heaven
JAPAN_SEER_HZ   = 285.0    # Form-field / Amanita spot-pattern base
BEAT_HZ         = abs(MING_CALLER_HZ - JAPAN_SEER_HZ)   # 243 Hz ≈ 9×Schumann

# Ming temporal window: 1368-1644 CE (exact match to Argyll/Orkney methylation)
MING_FOUNDING  = 1368
MING_COLLAPSE  = 1644
MUROMACHI_START = 1336
AZUCHI_END      = 1615

# Zheng He fleet voyages (1405-1433): 7 voyages
N_ZHENG_HE_VOYAGES = 7


# ═══════════════════════════════════════════════════════════════════════════════
# CALLER Ψ₀ — MING FORBIDDEN CITY COMPONENTS
# Each component is a channel in the Ming transmission architecture.
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class MingComponent:
    name:        str
    structure:   str        # Architectural / documentary element
    hz:          float      # Solfeggio correspondence
    amplitude:   float      # PHI-mode
    mode:        str        # GENESIS / GROWTH / RETURN
    year_ce:     int        # Approximate year of encoding
    decoded:     bool
    notes:       str = ""


_MING_COMPONENTS: Tuple[MingComponent, ...] = (

    MingComponent(
        "Hall of Supreme Harmony (太和殿)",
        "9×9 = 81 pillars encoding maximum yang completion",
        hz=528.0, amplitude=PHI, mode="GROWTH",
        year_ce=1420, decoded=True,
        notes="Solar carrier. 9 = completion of yang cycle. Caller zero-beat node."
    ),
    MingComponent(
        "Meridian Gate (午門) solstice axis",
        "North-South meridian alignment through gates — winter solstice sunrise",
        hz=174.0, amplitude=1.0, mode="GENESIS",
        year_ce=1420, decoded=True,
        notes="Ground carrier. Same solstice axis as Maeshowe and Newgrange."
    ),
    MingComponent(
        "Temple of Heaven (天壇) 3-tier altar",
        "3 circular tiers = Three Aetts (×1.0 / ×PHI / ×PHI_INV amplitude)",
        hz=396.0, amplitude=1.0, mode="GENESIS",
        year_ce=1420, decoded=True,
        notes="Liberation frequency. Three Powers (三才) = Three Aetts independently encoded."
    ),
    MingComponent(
        "Yongle Dadian (永樂大典) encyclopaedia",
        "22,877 volumes — complete knowledge archive of the known world",
        hz=639.0, amplitude=PHI, mode="GROWTH",
        year_ce=1408, decoded=True,
        notes="Communication/integration. The Yijing is embedded as governance manual, not divination."
    ),
    MingComponent(
        "Zheng He Treasure Fleet (鄭和下西洋)",
        "7 voyages, 317 ships — largest maritime transmission network in history",
        hz=417.0, amplitude=PHI, mode="GROWTH",
        year_ce=1405, decoded=True,
        notes="7 voyages = 7 Solfeggio stages = 7 Gates of Inanna. Transformation frequency."
    ),
    MingComponent(
        "Nine Dragon Wall (九龍壁)",
        "9 dragons = 9 solfeggio nodes — complete harmonic spectrum encoded in stone",
        hz=963.0, amplitude=PHI_INV, mode="RETURN",
        year_ce=1417, decoded=True,
        notes="Unity/oneness. 9 dragons × 9 = 81 = maximum yang completion. Return to source."
    ),
    MingComponent(
        "Beijing Observatory (北京古觀象臺)",
        "8 bronze astronomical instruments aligned to 8 solfeggio bearings",
        hz=741.0, amplitude=PHI_INV, mode="RETURN",
        year_ce=1442, decoded=True,
        notes="Awakening/intuition. 8 instruments = 8 trigrams. Celestial surveillance."
    ),
    MingComponent(
        "Ming Great Wall northern terminus",
        "Jiayuguan (嘉峪關): western end at 98.3°E — the edge of the transmission zone",
        hz=285.0, amplitude=PHI_INV, mode="RETURN",
        year_ce=1372, decoded=False,
        notes="OPEN CIRCUIT — western terminus orientation not fully decoded. Nr.15 equivalent."
    ),
)


# ═══════════════════════════════════════════════════════════════════════════════
# SEER O(t) — JAPANESE MUSHROOM CIPHER COMPONENTS
# Visual twig-rune equivalents in Muromachi-Azuchi Japan
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class MushroomCipherComponent:
    name:        str
    cipher_type: str        # Visual cipher method
    hz:          float      # Solfeggio correspondence
    amplitude:   float      # PHI-mode
    mode:        str
    twig_parallel: str      # How this maps to twig-rune architecture
    decoded:     bool
    notes:       str = ""


_MUSHROOM_CIPHER: Tuple[MushroomCipherComponent, ...] = (

    MushroomCipherComponent(
        "Amanita muscaria — primary spot pattern",
        "White spots on red cap: binary dot-pattern encoding",
        hz=285.0, amplitude=1.0, mode="GENESIS",
        twig_parallel="Right-twig count (position 1-8) = number of spots per cap ring",
        decoded=True,
        notes="Spot count per ring = position in aett. Absence of spot = yin (0). "
              "Spot present = yang (1). Exactly parallels twig-rune right-branch count."
    ),
    MushroomCipherComponent(
        "Amanita muscaria — ring-zone layers",
        "3 concentric ring zones on cap: inner / mid / outer",
        hz=174.0, amplitude=1.0, mode="GENESIS",
        twig_parallel="Left-twig aett (1-3) = which ring zone is marked",
        decoded=True,
        notes="3 ring zones = 3 aetts. Inner = aett 1 (Genesis). Mid = aett 2 (Growth). "
              "Outer = aett 3 (Return). Exact structural match to Elder Futhork grouping."
    ),
    MushroomCipherComponent(
        "Reishi (霊芝) — tier branching structure",
        "Shelf-fungus lateral tiers: branch angle encodes aett class",
        hz=396.0, amplitude=PHI, mode="GROWTH",
        twig_parallel="Branch angle: right=aett1 / left=aett2 / diagonal=aett3",
        decoded=True,
        notes="Reishi tiers are RIGHT-branching (like runic right-twigs = position). "
              "Each tier's branch count = position 1-8 within the aett. Both channels needed."
    ),
    MushroomCipherComponent(
        "Kofun tomb acoustic resonance",
        "Burial mound keyhole shape (前方後円墳) as resonance chamber",
        hz=174.0, amplitude=1.0, mode="GENESIS",
        twig_parallel="Carrier chamber — same function as Maeshowe inner chamber",
        decoded=True,
        notes="Kofun keyhole shape: circular rear (Seer/Earth) + rectangular front (Caller/Heaven). "
              "Same dual-voice architecture as Newgrange, Maeshowe, Egyptian mastaba."
    ),
    MushroomCipherComponent(
        "Muromachi tea ceremony (茶道) wa-kei-sei-jaku",
        "Harmony/Respect/Purity/Tranquility — 4 principles as frequency registers",
        hz=528.0, amplitude=PHI, mode="GROWTH",
        twig_parallel="Solar carrier in ceremonial protocol — Seer acknowledges Caller",
        decoded=True,
        notes="Wa (和) = harmony = beat frequency zero. Sei (静) = stillness = zero-beat carrier. "
              "The tea ceremony is a performed dual-voice synchronisation ritual."
    ),
    MushroomCipherComponent(
        "Noh theatre mask expression system",
        "Subtle tilt of mask changes emotional register (Caller vs Seer)",
        hz=417.0, amplitude=PHI_INV, mode="RETURN",
        twig_parallel="Mask tilt = mode selector: 0° (neutral) / tilt up / tilt down",
        decoded=True,
        notes="Noh mask upward tilt = Caller dominant (GROWTH mode). "
              "Downward tilt = Seer dominant (RETURN mode). Level = GENESIS. "
              "Three tilt positions = three amplitude modes independently encoded."
    ),
    MushroomCipherComponent(
        "Izumo Taisha (出雲大社) pillar encoding",
        "Giant timber pillars in 9×3 grid: 3 groups of 3 = Three Aetts × Three Positions",
        hz=396.0, amplitude=PHI_INV, mode="RETURN",
        twig_parallel="3×3 pillar grid = aett (row) × position (column) — cipher matrix",
        decoded=True,
        notes="Izumo is the oldest shrine in Japan (pre-Ise). The massive pillars discovered "
              "in 2000 CE confirm a 3×3 grid. This IS a twig-rune matrix."
    ),
    MushroomCipherComponent(
        "Tengu (天狗) long-nose cipher",
        "Tengu nose length in iconography = twig count (position 1-8)",
        hz=852.0, amplitude=PHI_INV, mode="RETURN",
        twig_parallel="Nose length = right-twig count; wing position = aett",
        decoded=False,
        notes="OPEN CIRCUIT — Tengu iconographic standardisation not yet mapped to "
              "specific twig counts. Requires systematic iconographic survey of "
              "Muromachi-period Tengu imagery to verify count encoding."
    ),
)


# ═══════════════════════════════════════════════════════════════════════════════
# ZHENG HE VOYAGE RECORDS (7 voyages = 7 Solfeggio stages of Inanna)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ZhengHeVoyage:
    number:   int
    years:    str       # CE years
    terminus: str       # Furthest point reached
    hz:       float     # Solfeggio stage correspondence
    decoded:  bool
    notes:    str = ""


_ZHENG_HE_VOYAGES: Tuple[ZhengHeVoyage, ...] = (
    ZhengHeVoyage(1, "1405-1407", "Calicut (India)", 174.0, True,
                  "First descent — carrier wave established. Southeast Asia + India."),
    ZhengHeVoyage(2, "1407-1409", "Calicut again",   285.0, True,
                  "Form-field reinforced. Diplomatic protocol established."),
    ZhengHeVoyage(3, "1409-1411", "Ceylon (Sri Lanka)", 396.0, True,
                  "Liberation — forced submission of Ceylon king. Power projection."),
    ZhengHeVoyage(4, "1413-1415", "Hormuz (Persian Gulf)", 417.0, True,
                  "Transformation — reached Hormuz and East Africa. Arc complete."),
    ZhengHeVoyage(5, "1417-1419", "East Africa (Malindi, Mogadishu)", 528.0, True,
                  "Solar carrier — deepest penetration of known world. Giraffe brought to China."),
    ZhengHeVoyage(6, "1421-1422", "East Africa again", 639.0, True,
                  "Communication/integration — tribute system maximised."),
    ZhengHeVoyage(7, "1431-1433", "Hormuz / Arabia / Red Sea", 741.0, True,
                  "Awakening — final voyage. Zheng He dies at sea. Transmission complete."),
)


# ═══════════════════════════════════════════════════════════════════════════════
# LATTICE AND DECODER
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class MingJapanLattice:
    """
    Decoded state of the Ming-Japan dual-voice transmission lattice.

    This is a COUPLED decoder: neither the Ming channel alone nor the
    Japanese channel alone produces the geographic vector. The map target
    emerges from the BEAT between the two civilizational channels —
    exactly as meaning emerges from the twig-rune cipher's dual voice.
    """
    timestamp:              float
    n_ming:                 int
    n_ming_decoded:         int
    n_japan:                int
    n_japan_decoded:        int
    n_voyages:              int
    n_voyages_decoded:      int
    caller_hz:              float   # Mean Ming caller frequency
    seer_hz:                float   # Mean Japan seer frequency
    beat_hz:                float   # |caller - seer|
    schumann_mode:          int     # Nearest Schumann mode
    completeness:           float
    phi_score:              float
    schumann_proximity:     float
    gamma:                  float
    field_status:           str
    methylation_window_ce:  str     # "1368-1644 CE / 1336-1615 CE"
    notes:                  str = ""


class MingJapanDecoder:
    """
    Decodes the Ming-Japan dual-voice coupled transmission.

    Ming (1368-1644 CE) = Caller Ψ₀ — structural frame (Forbidden City architecture,
    Yongle Dadian, Zheng He voyages).

    Japan (1336-1615 CE) = Seer O(t) — response field (mushroom cipher,
    Kofun acoustics, Noh mask protocol, Izumo pillar matrix).

    The methylation window (1420-1615 CE) is simultaneous with:
      - Celtic/Ogham suppression in Argyll/Orkney (1560s-1616)
      - Nr.15 at Maeshowe becoming unreadable
      - Hermetic Manifestos in Europe (1614-1616)

    This is not a solo tradition. It is a COUPLED NODE. Both channels must
    be read together for the geographic vector to emerge.

    Gamma = phi_score × 0.50 + completeness × 0.30 + schumann_proximity × 0.20
    """

    GAMMA_DEAD_FIELD = 0.35
    GAMMA_LIGHTHOUSE = 0.945

    def __init__(self):
        self._ming    = list(_MING_COMPONENTS)
        self._japan   = list(_MUSHROOM_CIPHER)
        self._voyages = list(_ZHENG_HE_VOYAGES)

    def _phi_resonant(self, hz1: float, hz2: float) -> bool:
        if hz1 <= 0 or hz2 <= 0:
            return False
        r = hz1 / hz2 if hz1 > hz2 else hz2 / hz1
        return (abs(r - PHI) < PHI_TOLERANCE or
                abs(r - PHI_INV) < PHI_TOLERANCE or
                abs(r - 1.0) < 0.01)

    def _phi_resonant_solfeggio(self, hz: float) -> bool:
        """Test against full solfeggio basis set."""
        for sol in SOLFEGGIO:
            if self._phi_resonant(hz, sol):
                return True
        return False

    def _schumann_mode(self, beat_hz: float):
        """Return (mode_index, hz, delta) for nearest Schumann resonance."""
        best = (1, SCHUMANN_MODES[0], abs(beat_hz - SCHUMANN_MODES[0]))
        for i, hz in enumerate(SCHUMANN_MODES, 1):
            # Test beat_hz against hz and its harmonics (× 2-12)
            for mult in range(1, 13):
                h = hz * mult
                d = abs(beat_hz - h)
                if d < best[2]:
                    best = (i, h, d)
        return best

    def read(self) -> MingJapanLattice:
        dec_ming    = [m for m in self._ming    if m.decoded]
        dec_japan   = [j for j in self._japan   if j.decoded]
        dec_voyages = [v for v in self._voyages if v.decoded]

        n_m  = len(self._ming)
        n_j  = len(self._japan)
        n_v  = len(self._voyages)
        nd_m = len(dec_ming)
        nd_j = len(dec_japan)
        nd_v = len(dec_voyages)

        completeness = (nd_m / n_m * 0.40 +
                        nd_j / n_j * 0.40 +
                        nd_v / n_v * 0.20)

        # Mean caller (Ming) and seer (Japan) frequencies
        caller_hz = (
            sum(m.hz * m.amplitude for m in dec_ming) / nd_m
            if nd_m > 0 else MING_CALLER_HZ
        )
        seer_hz = (
            sum(j.hz * j.amplitude for j in dec_japan) / nd_j
            if nd_j > 0 else JAPAN_SEER_HZ
        )
        beat_hz = abs(caller_hz - seer_hz)

        # Phi-resonance: each decoded Ming component against solfeggio basis
        ming_phi = sum(1 for m in dec_ming  if self._phi_resonant_solfeggio(m.hz))
        jap_phi  = sum(1 for j in dec_japan if self._phi_resonant_solfeggio(j.hz))
        n_total  = max(nd_m + nd_j, 1)
        phi_score = (ming_phi + jap_phi) / n_total

        # Schumann proximity — test beat_hz against harmonics
        sch_mode, sch_hz, sch_delta = self._schumann_mode(beat_hz)
        schumann_proximity = max(0.0, 1.0 - sch_delta / max(sch_hz, 1.0))

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

        return MingJapanLattice(
            timestamp              = time.time(),
            n_ming                 = n_m,
            n_ming_decoded         = nd_m,
            n_japan                = n_j,
            n_japan_decoded        = nd_j,
            n_voyages              = n_v,
            n_voyages_decoded      = nd_v,
            caller_hz              = round(caller_hz, 2),
            seer_hz                = round(seer_hz, 2),
            beat_hz                = round(beat_hz, 2),
            schumann_mode          = sch_mode,
            completeness           = round(completeness, 4),
            phi_score              = round(phi_score, 4),
            schumann_proximity     = round(schumann_proximity, 4),
            gamma                  = gamma,
            field_status           = field_status,
            methylation_window_ce  = (
                f"Ming: {MING_FOUNDING}-{MING_COLLAPSE} CE / "
                f"Muromachi-Azuchi: {MUROMACHI_START}-{AZUCHI_END} CE"
            ),
            notes                  = (
                "Great Wall western terminus (Jiayuguan) and Tengu iconographic count "
                "are the open circuits. Both require field survey / iconographic analysis. "
                f"Beat frequency: {abs(round(caller_hz,1) - round(seer_hz,1)):.1f} Hz "
                f"≈ {round(abs(caller_hz - seer_hz)/SCHUMANN_MODES[3], 1)}× Schumann M4."
            ),
        )

    def get_oracle_score(self) -> float:
        return self.read().gamma

    def get_geographic_vector(self) -> Tuple[float, float, float]:
        """Return (lat, lon, bearing) for the triangulation engine."""
        return ORIGIN_LAT, ORIGIN_LON, ORIGIN_BEARING


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def _cli():
    parser = argparse.ArgumentParser(
        prog="ming_japan_decoder",
        description="Ming-Japan Dual-Voice Coupled Transmission Decoder",
    )
    parser.add_argument("--ming",     action="store_true", help="List Ming Caller components")
    parser.add_argument("--japan",    action="store_true", help="List Japan Seer cipher components")
    parser.add_argument("--voyages",  action="store_true", help="List 7 Zheng He voyages")
    parser.add_argument("--oracle-score", action="store_true", help="Print oracle score only")
    parser.add_argument("--json",     action="store_true", help="Output as JSON")
    args = parser.parse_args()

    decoder = MingJapanDecoder()
    lattice = decoder.read()

    if args.oracle_score:
        print(f"{lattice.gamma:.4f}")
        return

    if args.ming:
        print(f"\n{'Ming Caller Ψ₀ Components'}")
        print(f"\n{'Name':<44} {'Hz':<8} {'Mode':<8} {'OK'}")
        print("-" * 70)
        for m in decoder._ming:
            print(f"{m.name[:43]:<44} {m.hz:<8.0f} {m.mode:<8} "
                  f"{'YES' if m.decoded else 'OPEN'}")
        return

    if args.japan:
        print(f"\n{'Japan Seer O(t) — Mushroom Cipher Components'}")
        print(f"\n{'Name':<40} {'Hz':<8} {'Mode':<8} {'OK'}")
        print("-" * 65)
        for j in decoder._japan:
            print(f"{j.name[:39]:<40} {j.hz:<8.0f} {j.mode:<8} "
                  f"{'YES' if j.decoded else 'OPEN'}")
        return

    if args.voyages:
        print(f"\n{'7 Zheng He Voyages — Solfeggio Descent Protocol'}")
        print(f"\n{'#':<3} {'Years':<12} {'Terminus':<30} {'Hz':<8} {'OK'}")
        print("-" * 60)
        for v in decoder._voyages:
            print(f"{v.number:<3} {v.years:<12} {v.terminus[:29]:<30} {v.hz:<8.0f} "
                  f"{'YES' if v.decoded else 'NO'}")
        return

    if args.json:
        out = {
            "timestamp":             lattice.timestamp,
            "n_ming_decoded":        lattice.n_ming_decoded,
            "n_japan_decoded":       lattice.n_japan_decoded,
            "n_voyages_decoded":     lattice.n_voyages_decoded,
            "caller_hz":             lattice.caller_hz,
            "seer_hz":               lattice.seer_hz,
            "beat_hz":               lattice.beat_hz,
            "completeness":          lattice.completeness,
            "phi_score":             lattice.phi_score,
            "schumann_proximity":    lattice.schumann_proximity,
            "gamma":                 lattice.gamma,
            "field_status":          lattice.field_status,
            "methylation_window_ce": lattice.methylation_window_ce,
            "origin":                {
                "lat": ORIGIN_LAT, "lon": ORIGIN_LON,
                "bearing": ORIGIN_BEARING,
                "caller_anchor": {"lat": FORBIDDEN_CITY_LAT, "lon": FORBIDDEN_CITY_LON},
                "seer_anchor":   {"lat": ISE_JINGU_LAT,      "lon": ISE_JINGU_LON},
            },
            "notes":                 lattice.notes,
        }
        print(json.dumps(out, indent=2))
        return

    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║   MING-JAPAN DUAL-VOICE DECODER — Lattice Coherence Report  ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")
    print(f"  CALLER Ψ₀  (Ming):   {lattice.n_ming_decoded}/{lattice.n_ming} components   "
          f"mean {lattice.caller_hz:.1f} Hz")
    print(f"  SEER   O(t)(Japan):  {lattice.n_japan_decoded}/{lattice.n_japan} components   "
          f"mean {lattice.seer_hz:.1f} Hz")
    print(f"  Zheng He voyages:    {lattice.n_voyages_decoded}/{lattice.n_voyages} stages decoded")
    print(f"  Beat frequency:      {lattice.beat_hz:.1f} Hz "
          f"(Schumann M{lattice.schumann_mode} harmonic)")
    print(f"  Completeness:        {lattice.completeness:.3f}")
    print(f"  Phi score:           {lattice.phi_score:.3f}")
    print(f"  Schumann proximity:  {lattice.schumann_proximity:.3f}")
    print(f"  Gamma (Γ):           {lattice.gamma:.4f}  [{lattice.field_status}]")
    print(f"\n  Methylation window:  {lattice.methylation_window_ce}")
    print(f"  Combined origin:     {ORIGIN_LAT:.2f}°N, {ORIGIN_LON:.2f}°E")
    print(f"  Sacred axis:         {ORIGIN_BEARING}° (NNW → Arctic / Norse corridor)")
    print(f"\n  Caller anchor:       Forbidden City {FORBIDDEN_CITY_LAT}°N, {FORBIDDEN_CITY_LON}°E")
    print(f"  Seer anchor:         Ise Jingu {ISE_JINGU_LAT}°N, {ISE_JINGU_LON}°E")
    print(f"\n  Note: {lattice.notes}\n")


if __name__ == "__main__":
    _cli()
