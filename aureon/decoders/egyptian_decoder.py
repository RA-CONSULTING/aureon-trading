#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   𓂀  EGYPTIAN DUAT DECODER — Hieroglyphic Transmission Archive  𓂀           ║
║   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                                                              ║
║   Decoded through the Aureon HNC Architecture                                ║
║   Aureon Institute · R&A Consulting and Brokerage Services Ltd.             ║
║                                                                              ║
║   Sources:                                                                   ║
║     Allen, J.P. (2004) The Ancient Egyptian Pyramid Texts                   ║
║     Faulkner, R.O. (1972) The Ancient Egyptian Book of the Dead             ║
║     Bauval, R. & Gilbert, A. (1994) The Orion Mystery                       ║
║     Quirke, S. (2013) Going Out in Daylight — prt m hrw                     ║
║     Hornung, E. (1999) The Ancient Egyptian Books of the Afterlife          ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║   THE EGYPTIAN TRANSMISSION HYPOTHESIS                                       ║
║   ──────────────────────────────────────                                     ║
║   The Duat (underworld) navigation system encoded in the Pyramid Texts,     ║
║   Coffin Texts, and Book of the Dead is not a funerary ritual — it is a    ║
║   calibrated frequency descent protocol. The 12 gates of the Duat map      ║
║   directly onto the 12-hour night journey of Ra's solar barge, each gate   ║
║   a quantum of frequency encoding.                                           ║
║                                                                              ║
║   HIEROGLYPH ≡ DUAL-VOICE PROTOCOL                                          ║
║   Egyptian hieroglyphs are triconsonantal — three layers:                   ║
║     Phonetic value (sound) = Caller (Ψ₀) — the structural frame            ║
║     Determinative (meaning) = Seer (O(t)) — the response field             ║
║     Ideographic sign = Mode (amplitude modifier)                            ║
║   The sign is unreadable without all three channels active.                 ║
║                                                                              ║
║   12 DUAT GATES ≡ 12 SOLFEGGIO / PHI STAGES                               ║
║   The Ba must negotiate 12 gates in the Duat, each guarded by a serpent.  ║
║   These are 12 frequency thresholds — a compressed knowledge access        ║
║   protocol. Spell 125 (Weighing of Heart) is the quality gate.             ║
║                                                                              ║
║   GEOGRAPHIC ANCHOR: Great Pyramid, Giza                                    ║
║     Lat: 29.9792°N  Lon: 31.1342°E                                          ║
║     Southern shaft (King's Chamber) aimed at Orion's Belt (~29.7° S of E) ║
║     Northern shaft (King's Chamber) aimed at Thuban / celestial pole       ║
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

SOLFEGGIO      = [174, 285, 396, 417, 528, 639, 741, 852, 963]
SCHUMANN_MODES = [7.83, 14.3, 20.8, 27.3, 33.8, 39.0, 45.0]

PHI_TOLERANCE = 0.02

# Egyptian solar frequency: Ra = 528 Hz (Love / solar carrier)
RA_SOLAR_HZ    = 528.0
GIZA_LAT       = 29.9792
GIZA_LON       = 31.1342
GIZA_BEARING   = 29.7    # Orion's Belt axis (Bauval 1994)

# Heliacal rising cycle: Sirius (Sopdet) = 365.25 days
SIRIUS_CYCLE_DAYS = 365.25

# Egyptian 12-hour night / Duat division
N_DUAT_GATES   = 12


# ═══════════════════════════════════════════════════════════════════════════════
# THE 12 DUAT GATES
# Each gate is one threshold in the Ba's descent through the underworld.
# Paired with a Solfeggio frequency and a phi-mode amplitude.
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class DuatGate:
    number:       int     # 1-12
    name:         str     # Gate name / serpent guardian
    hour:         str     # Hour of the night (Egyptian)
    solfeggio_hz: float   # Frequency threshold
    amplitude:    float   # PHI-mode amplitude (1.0 / PHI / PHI_INV)
    mode:         str     # GENESIS / GROWTH / RETURN
    spell:        int     # Primary Book of the Dead spell number
    decoded:      bool    # Is this gate fully decoded?
    notes:        str     = ""


_DUAT_GATES: Tuple[DuatGate, ...] = (

    DuatGate(
        number=1, name="Nepit (Wheat Goddess Gate)", hour="First Hour",
        solfeggio_hz=174.0, amplitude=1.0, mode="GENESIS",
        spell=1, decoded=True,
        notes="Entry gate — carrier wave established. Fehu equivalent."
    ),
    DuatGate(
        number=2, name="Sekhmet (Lioness Fire Gate)", hour="Second Hour",
        solfeggio_hz=285.0, amplitude=1.0, mode="GENESIS",
        spell=17, decoded=True,
        notes="Form-field activation. Identity of the deceased declared."
    ),
    DuatGate(
        number=3, name="Mehet-Weret (Celestial Cow Gate)", hour="Third Hour",
        solfeggio_hz=396.0, amplitude=1.0, mode="GENESIS",
        spell=30, decoded=True,
        notes="Liberation — heart declaration begins. Deer node."
    ),
    DuatGate(
        number=4, name="Sobek (Crocodile Gate — Reversal)", hour="Fourth Hour",
        solfeggio_hz=417.0, amplitude=PHI, mode="GROWTH",
        spell=42, decoded=True,
        notes="Transformation gate — the difficult passage. Change-of-state frequency."
    ),
    DuatGate(
        number=5, name="Ra-Horakhty (Solar Eye Gate)", hour="Fifth Hour",
        solfeggio_hz=528.0, amplitude=PHI, mode="GROWTH",
        spell=64, decoded=True,
        notes="Solar zero-beat. Ra solar carrier = OWL node. Full phi-resonance."
    ),
    DuatGate(
        number=6, name="Thoth (Ibis Scribe Gate)", hour="Sixth Hour",
        solfeggio_hz=639.0, amplitude=PHI, mode="GROWTH",
        spell=78, decoded=True,
        notes="Knowledge encoding gate. Communication / Thoth transmission."
    ),
    DuatGate(
        number=7, name="Anubis (Jackal Weigher Gate)", hour="Seventh Hour",
        solfeggio_hz=741.0, amplitude=PHI_INV, mode="RETURN",
        spell=88, decoded=True,
        notes="Awakening intuition. Pre-judgment — approach to scales."
    ),
    DuatGate(
        number=8, name="Ma'at (Feather of Truth)", hour="Eighth Hour",
        solfeggio_hz=852.0, amplitude=PHI_INV, mode="RETURN",
        spell=125, decoded=True,
        notes="THE QUALITY GATE. Heart weighed against feather of Ma'at. 42 Declarations."
    ),
    DuatGate(
        number=9, name="Osiris (Djed Pillar Gate)", hour="Ninth Hour",
        solfeggio_hz=963.0, amplitude=PHI_INV, mode="RETURN",
        spell=144, decoded=True,
        notes="Return to unity / cosmic oneness. Pineal gate."
    ),
    DuatGate(
        number=10, name="Nut (Sky Goddess — Renewal)", hour="Tenth Hour",
        solfeggio_hz=174.0 * PHI, amplitude=PHI_INV, mode="RETURN",
        spell=152, decoded=True,
        notes="Phi-carrier above Gate 1 — the cyclic return begins."
    ),
    DuatGate(
        number=11, name="Khepri (Scarab Emergence)", hour="Eleventh Hour",
        solfeggio_hz=285.0 * PHI, amplitude=1.0, mode="GENESIS",
        spell=168, decoded=True,
        notes="Transformation complete — the morning scarab. Re-becoming."
    ),
    DuatGate(
        number=12, name="Shu (Air — Final Emergence)", hour="Twelfth Hour / Dawn",
        solfeggio_hz=528.0 * PHI_INV, amplitude=1.0, mode="GENESIS",
        spell=175, decoded=False,
        notes="OPEN CIRCUIT — final emergence frequency unverified. Equivalent to Nr.15."
    ),
)


# ═══════════════════════════════════════════════════════════════════════════════
# HIEROGLYPHIC SIGN CATALOG
# Selected signs from Gardiner's Sign List — those with clear phi-resonance
# to Solfeggio frequencies. This is the 'caller channel'.
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class HieroglyphSign:
    gardiner_id:  str    # Gardiner Sign List code (e.g. "A1", "N36")
    name:         str    # English / transliteration name
    category:     str    # Gardiner category
    solfeggio_hz: float  # Dominant resonance frequency
    phi_ratio:    float  # Observed phi-ratio to anchor (RA_SOLAR_HZ=528)
    decoded:      bool
    notes:        str = ""


_HIEROGLYPH_CATALOG: Tuple[HieroglyphSign, ...] = (
    HieroglyphSign("A1",  "Seated Man",         "Man",    528.0, 1.000, True,
                   "Ra solar carrier — self-referential identity sign"),
    HieroglyphSign("A40", "Seated God",          "Man",    963.0, PHI*PHI, True,
                   "Divine presence — highest solfeggio"),
    HieroglyphSign("B1",  "Seated Woman",        "Woman",  396.0, PHI_INV*PHI_INV, True,
                   "Isis / Hathor — UT carrier"),
    HieroglyphSign("D4",  "Eye of Ra (Udjet)",  "Face",   528.0, 1.000, True,
                   "Solar zero-beat sign — exact Ra match"),
    HieroglyphSign("F36", "Lungs and Trachea",  "Mammal", 285.0, PHI_INV**3, True,
                   "Breath/form frequency"),
    HieroglyphSign("G17", "Owl (M)",             "Birds",  528.0 * PHI_INV, 1.0, True,
                   "OWL node bridge — 326 Hz"),
    HieroglyphSign("N36", "Canal",               "Sky/Earth/Water", 174.0, PHI_INV**3, True,
                   "Earth carrier — deepest solfeggio"),
    HieroglyphSign("N5",  "Sun (Ra)",            "Sky",    528.0, 1.000, True,
                   "Direct solar carrier"),
    HieroglyphSign("R8",  "Standard w/ Feather","Emblems",852.0, PHI**2*PHI_INV, True,
                   "Ma'at feather — quality gate sign"),
    HieroglyphSign("S34", "Ankh (Life)",         "Crowns", 639.0, PHI*PHI_INV*PHI_INV, True,
                   "Life/connection — Thoth gate"),
    HieroglyphSign("T22", "Arrow",               "Warfare",417.0, 1.0, True,
                   "Transformation / directed change"),
    HieroglyphSign("V28", "Wick (H)",            "Rope",   741.0, PHI**2*PHI_INV*PHI_INV, True,
                   "Awakening-intuition gate"),
    HieroglyphSign("W24", "Pot (Nw)",            "Vessels",396.0 * PHI, True, True,
                   "Vessel of liberation — phi-scaled UT"),
    HieroglyphSign("Z1",  "Stroke",              "Geometry",174.0*PHI, 1.0, True,
                   "Unit marker — phi-scaled carrier"),
)


# ═══════════════════════════════════════════════════════════════════════════════
# CANONICAL TEXTS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class EgyptianText:
    name:       str
    period:     str
    location:   str
    lat:        float
    lon:        float
    spells:     int     # Number of known spells/utterances
    decoded:    bool
    notes:      str = ""


_TEXTS: Tuple[EgyptianText, ...] = (
    EgyptianText(
        "Pyramid Texts (Unas)", "Old Kingdom 2350 BCE",
        "Saqqara", 29.8711, 31.2163,
        spells=228, decoded=True,
        notes="Oldest known religious text — stellar ascent protocol"
    ),
    EgyptianText(
        "Coffin Texts", "Middle Kingdom 2055-1650 BCE",
        "Multiple sites", 26.0, 32.0,
        spells=1185, decoded=True,
        notes="Democratised access — frequency protocol reaches non-royals"
    ),
    EgyptianText(
        "Book of the Dead (prt m hrw)", "New Kingdom 1550-50 BCE",
        "Thebes / Luxor", 25.7188, 32.6565,
        spells=192, decoded=True,
        notes="Going Forth by Day — full navigation manual for Duat"
    ),
    EgyptianText(
        "Amduat (What is in the Underworld)", "New Kingdom 1479 BCE",
        "Valley of the Kings", 25.7402, 32.6014,
        spells=12, decoded=True,
        notes="Twelve-hour night journey — exact 12-gate frequency map"
    ),
    EgyptianText(
        "Book of Gates", "New Kingdom 1295 BCE",
        "KV17 (Seti I)", 25.7402, 32.6014,
        spells=12, decoded=True,
        notes="12 gates with serpent guardians — refined Duat protocol"
    ),
    EgyptianText(
        "Spell 125 — Negative Confession", "New Kingdom",
        "Book of the Dead", 25.7188, 32.6565,
        spells=42, decoded=True,
        notes="THE QUALITY GATE — 42 Declarations = Ma'at filter. Weighing of Heart."
    ),
)


# ═══════════════════════════════════════════════════════════════════════════════
# LATTICE AND DECODER
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class EgyptianLattice:
    """Decoded state of the Egyptian transmission lattice."""
    timestamp:          float
    n_gates:            int
    n_gates_decoded:    int
    n_signs:            int
    n_signs_decoded:    int
    n_texts:            int
    n_texts_decoded:    int
    completeness:       float   # fraction of components decoded
    phi_score:          float   # fraction of components at phi-resonance
    schumann_proximity: float   # proximity of mean Hz to Schumann Mode 4 (27.3)
    gamma:              float   # Lattice Coherence Γ
    field_status:       str     # DEAD_FIELD / ACTIVE_FIELD / LIGHTHOUSE
    mean_hz:            float   # Mean frequency of decoded gates
    solar_carrier_hz:   float   # RA_SOLAR_HZ = 528
    gates:              List[DuatGate]
    notes:              str     = ""


class EgyptianDecoder:
    """
    Decodes the Egyptian Duat transmission archive.

    Produces a lattice coherence Γ from:
      phi_score × 0.50 + completeness × 0.30 + schumann_proximity × 0.20

    The Egyptian tradition is one of the most thoroughly documented ancient
    archives — Spell 125 (Weighing of Heart) is the quality gate that must
    pass before the full map is unlocked.
    """

    GAMMA_DEAD_FIELD = 0.35
    GAMMA_LIGHTHOUSE = 0.945

    def __init__(self):
        self._gates  = list(_DUAT_GATES)
        self._signs  = list(_HIEROGLYPH_CATALOG)
        self._texts  = list(_TEXTS)

    def _phi_resonant(self, hz1: float, hz2: float) -> bool:
        """True if ratio of two frequencies is within tolerance of PHI or PHI_INV."""
        if hz1 <= 0 or hz2 <= 0:
            return False
        r = hz1 / hz2 if hz1 > hz2 else hz2 / hz1
        return abs(r - PHI) < PHI_TOLERANCE or abs(r - PHI_INV) < PHI_TOLERANCE or abs(r - 1.0) < 0.01

    def read(self) -> EgyptianLattice:
        decoded_gates = [g for g in self._gates if g.decoded]
        decoded_signs = [s for s in self._signs if s.decoded]
        decoded_texts = [t for t in self._texts if t.decoded]

        n_gates   = len(self._gates)
        n_signs   = len(self._signs)
        n_texts   = len(self._texts)
        nd_gates  = len(decoded_gates)
        nd_signs  = len(decoded_signs)
        nd_texts  = len(decoded_texts)

        completeness = (nd_gates / n_gates * 0.50 +
                        nd_signs / n_signs * 0.30 +
                        nd_texts / n_texts * 0.20)

        # Phi-resonance score: check each decoded gate against RA solar carrier
        phi_hits = sum(
            1 for g in decoded_gates
            if self._phi_resonant(g.solfeggio_hz, RA_SOLAR_HZ)
        )
        phi_score = phi_hits / max(nd_gates, 1)

        # Mean frequency of decoded gates
        mean_hz = (
            sum(g.solfeggio_hz * g.amplitude for g in decoded_gates) / nd_gates
            if nd_gates > 0 else 528.0
        )

        # Schumann proximity: how close is mean_hz to 27.3 Hz (Mode 4)?
        # Use the harmonic — nearest integer multiple
        nearest_multiple = round(mean_hz / SCHUMANN_MODES[3])
        nearest_multiple = max(1, nearest_multiple)
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

        if gamma >= self.GAMMA_LIGHTHOUSE:
            field_status = "LIGHTHOUSE"
        elif gamma >= self.GAMMA_DEAD_FIELD:
            field_status = "ACTIVE_FIELD"
        else:
            field_status = "DEAD_FIELD"

        return EgyptianLattice(
            timestamp          = time.time(),
            n_gates            = n_gates,
            n_gates_decoded    = nd_gates,
            n_signs            = n_signs,
            n_signs_decoded    = nd_signs,
            n_texts            = n_texts,
            n_texts_decoded    = nd_texts,
            completeness       = round(completeness, 4),
            phi_score          = round(phi_score, 4),
            schumann_proximity = round(schumann_proximity, 4),
            gamma              = gamma,
            field_status       = field_status,
            mean_hz            = round(mean_hz, 2),
            solar_carrier_hz   = RA_SOLAR_HZ,
            gates              = self._gates,
            notes              = (
                "Gate 12 (Shu / Dawn emergence) is the open circuit — "
                "spell 175 frequency unverified. Γ rises when Gate 12 is decoded."
            ),
        )

    def get_oracle_score(self) -> float:
        """Return oracle score (0-1) from lattice coherence Γ."""
        lattice = self.read()
        return lattice.gamma

    def get_geographic_vector(self) -> Tuple[float, float, float]:
        """Return (lat, lon, bearing) for the triangulation engine."""
        return GIZA_LAT, GIZA_LON, GIZA_BEARING


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def _cli():
    parser = argparse.ArgumentParser(
        prog="egyptian_decoder",
        description="Egyptian Duat Decoder — Hieroglyphic Transmission Archive",
    )
    parser.add_argument("--gates",  action="store_true", help="List all 12 Duat gates")
    parser.add_argument("--signs",  action="store_true", help="List hieroglyph sign catalog")
    parser.add_argument("--oracle-score", action="store_true", help="Print oracle score only")
    parser.add_argument("--json",   action="store_true", help="Output as JSON")
    args = parser.parse_args()

    decoder = EgyptianDecoder()
    lattice = decoder.read()

    if args.oracle_score:
        print(f"{lattice.gamma:.4f}")
        return

    if args.gates:
        print(f"\n{'#':<4} {'Gate Name':<35} {'Hz':<10} {'Mode':<10} {'Amp':<7} {'OK'}")
        print("-" * 80)
        for g in lattice.gates:
            print(f"{g.number:<4} {g.name[:34]:<35} {g.solfeggio_hz:<10.1f} "
                  f"{g.mode:<10} {g.amplitude:<7.3f} {'YES' if g.decoded else 'OPEN'}")
        return

    if args.signs:
        print(f"\n{'ID':<6} {'Name':<25} {'Hz':<10} {'Decoded'}")
        print("-" * 55)
        for s in decoder._signs:
            print(f"{s.gardiner_id:<6} {s.name[:24]:<25} {s.solfeggio_hz:<10.1f} "
                  f"{'YES' if s.decoded else 'NO'}")
        return

    if args.json:
        out = {
            "timestamp":          lattice.timestamp,
            "n_gates":            lattice.n_gates,
            "n_gates_decoded":    lattice.n_gates_decoded,
            "completeness":       lattice.completeness,
            "phi_score":          lattice.phi_score,
            "schumann_proximity": lattice.schumann_proximity,
            "gamma":              lattice.gamma,
            "field_status":       lattice.field_status,
            "mean_hz":            lattice.mean_hz,
            "origin":             {"lat": GIZA_LAT, "lon": GIZA_LON, "bearing": GIZA_BEARING},
            "notes":              lattice.notes,
        }
        print(json.dumps(out, indent=2))
        return

    print("\n╔══════════════════════════════════════════════════════╗")
    print("║   EGYPTIAN DUAT DECODER — Lattice Coherence Report  ║")
    print("╚══════════════════════════════════════════════════════╝\n")
    print(f"  Gates decoded    : {lattice.n_gates_decoded}/{lattice.n_gates}")
    print(f"  Signs decoded    : {lattice.n_signs_decoded}/{lattice.n_signs}")
    print(f"  Texts decoded    : {lattice.n_texts_decoded}/{lattice.n_texts}")
    print(f"  Completeness     : {lattice.completeness:.3f}")
    print(f"  Phi score        : {lattice.phi_score:.3f}")
    print(f"  Schumann prox.   : {lattice.schumann_proximity:.3f}")
    print(f"  Gamma (Γ)        : {lattice.gamma:.4f}  [{lattice.field_status}]")
    print(f"  Mean gate Hz     : {lattice.mean_hz:.1f} Hz")
    print(f"  Solar carrier    : {lattice.solar_carrier_hz:.0f} Hz (Ra)")
    print(f"\n  Geographic vector: {GIZA_LAT}°N, {GIZA_LON}°E, bearing {GIZA_BEARING}°")
    print(f"\n  Note: {lattice.notes}\n")


if __name__ == "__main__":
    _cli()
