#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Emerald Tablet decoded as a Harmonic Nexus specification document.

The Tabula Smaragdina is treated here as compressed technical documentation
for the Aureon Harmonic Nexus Core, transliterated from hermetic symbolism
into computational parameters.  Every verse maps to a concrete constant,
scaling law, or pipeline stage already present in the codebase.

This module is research-grade.  It does not claim historical authenticity
for the hermetic-to-engineering mapping — it claims **structural
isomorphism** between the Tablet's relational logic and the L(t) pipeline.

Usage:
    python -m aureon.decoders.emerald_spec [--json] [--stage N] [--verse KEY]
"""

import sys
import os

if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io

        def _is_utf8_wrapper(stream):
            return (
                isinstance(stream, io.TextIOWrapper)
                and hasattr(stream, 'encoding')
                and stream.encoding
                and stream.encoding.lower().replace('-', '') == 'utf8'
            )

        if hasattr(sys.stdout, 'buffer') and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer,
                encoding='utf-8',
                errors='replace',
                line_buffering=True,
            )
    except Exception:
        pass

import argparse
import json
import math
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional, Sequence, Tuple

# ════════════════════════════════════════════════════════════════════════════
# SACRED CONSTANTS (mirrors aureon_seer.py — kept local to avoid bootstrap)
# ════════════════════════════════════════════════════════════════════════════

PHI = (1 + math.sqrt(5)) / 2            # 1.618033988749895
SCHUMANN_FUNDAMENTAL = 7.83             # Hz — Earth's heartbeat
LOVE_FREQUENCY = 528.0                  # Hz — DNA repair / MI solfeggio
RF_CARRIER_ISM = 13.56e6               # Hz — ISM-band RF carrier
PRIME_SENTINEL_HZ = 2.111991           # Gary's frequency (DOB 02.11.1991)

# HAARP → EPOS scaling constants
HAARP_POWER_W = 3.6e6                  # 3.6 MW effective radiated power
HAARP_VOLUME_M3 = 1.13e15             # F-region interaction volume (km³ → m³)
EPOS_CHAMBER_DIAMETER_M = 0.30        # 30 cm spherical chamber
EPOS_CHAMBER_VOLUME_M3 = (4 / 3) * math.pi * (EPOS_CHAMBER_DIAMETER_M / 2) ** 3
EPOS_CHAMBER_AREA_M2 = math.pi * (EPOS_CHAMBER_DIAMETER_M / 2) ** 2
EPOS_RF_POWER_W = 50.0                # Typical RF drive
EPOS_PRESSURE_MBAR = 0.1              # Argon fill
PASCHEN_OPTIMAL_PD = 2.25             # Torr·cm for min breakdown (~400 V)
PASCHEN_BREAKDOWN_V = 400.0

# Derived ratios
HAARP_POWER_DENSITY = HAARP_POWER_W / HAARP_VOLUME_M3          # W/m³
EPOS_POWER_DENSITY = EPOS_RF_POWER_W / EPOS_CHAMBER_VOLUME_M3 # W/m³
VOLUMETRIC_CONCENTRATION_FACTOR = round(EPOS_POWER_DENSITY / HAARP_POWER_DENSITY)
IONOSPHERIC_FLUX_W_M2 = 0.03          # W/m² at F-region
POWER_COUPLING_METHOD1 = IONOSPHERIC_FLUX_W_M2 * EPOS_CHAMBER_AREA_M2

# L(t) threshold — the "Philosopher's Stone"
PHILOSOPHERS_STONE_THRESHOLD = 2.8     # 99 % null-hypothesis rejection
GOLDEN_SCORE_THRESHOLD = PHI * PHILOSOPHERS_STONE_THRESHOLD  # ≈ 4.53

WIKIPEDIA_API_BASE = 'https://en.wikipedia.org/api/rest_v1/page/summary/'
WIKIPEDIA_SEARCH_API = 'https://en.wikipedia.org/w/api.php'
WIKIPEDIA_USER_AGENT = (
    'AureonDecoder/1.0 '
    '(https://github.com/RA-CONSULTING/aureon-trading; research@aureon.ai)'
)

WIKIPEDIA_TOPIC_ALIASES: Dict[str, str] = {
    'emerald tablet': 'Emerald Tablet',
    'tabula smaragdina': 'Emerald Tablet',
    'smaragdine table': 'Emerald Tablet',
    'hermes trismegistus': 'Hermes Trismegistus',
    'anubis': 'Anubis',
    'maat': 'Maat',
    "ma'at": 'Maat',
    'thoth': 'Thoth',
    'osiris': 'Osiris',
    'ra': 'Ra',
    'book of the dead': 'Book of the Dead',
    'weighing of the heart': 'Book of the Dead',
    'spell 125': 'Book of the Dead',
    'spell_125': 'Book of the Dead',
    'hermetica': 'Hermetica',
    # ── Mogollon ──
    'mogollon': 'Mogollon culture',
    'mogollon culture': 'Mogollon culture',
    'mimbres': 'Mimbres culture',
    'petroglyph': 'Petroglyph',
    'petroglyphs': 'Petroglyph',
    'spiral glyph': 'Petroglyph',
    'light language': 'Petroglyph',
    'sipapu': 'Sipapu',
    'ancestral puebloans': 'Ancestral Puebloans',
    # ── Maya ──
    'maya': 'Maya civilization',
    'mayan': 'Maya civilization',
    'maya calendar': 'Maya calendar',
    'long count': 'Maya calendar',
    'tzolkin': 'Tzolkin',
    'haab': 'Maya calendar',
    'baktun': 'Maya calendar',
    'venus cycle': 'Venus (planet)',
    'dresden codex': 'Dresden Codex',
    # ── Celtic ──
    'celt': 'Celtic mythology',
    'celtic': 'Celtic mythology',
    'ogham': 'Ogham',
    'druids': 'Druids',
    'druidry': 'Druids',
    'triskelion': 'Triskelion',
    'triquetra': 'Triquetra',
    'standing stones': 'Standing stone',
    'stonehenge': 'Stonehenge',
    'celtic tree calendar': 'Celtic tree calendar',
}

# ════════════════════════════════════════════════════════════════════════════
# TABLET VERSES
# ════════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class TabletVerse:
    """One line of the Emerald Tablet mapped to its computational meaning."""

    key: str
    latin_fragment: str
    hermetic_text: str
    technical_translation: str
    aureon_implementation: str
    parameters: Dict[str, object] = field(default_factory=dict)
    pipeline_stage: Optional[int] = None


_VERSE_CATALOG: Tuple[TabletVerse, ...] = (
    TabletVerse(
        key='verum',
        latin_fragment='Verum, sine mendacio, certum et verissimum',
        hermetic_text='Tis true without lying, certain & most true',
        technical_translation=(
            'Tier 1 Evidence Standard — Boolean verification without '
            'epistemic uncertainty'
        ),
        aureon_implementation='L(t) > 2.8 (99 % confidence null rejection); Tier 1 data only',
        parameters={
            'threshold': PHILOSOPHERS_STONE_THRESHOLD,
            'confidence_pct': 99,
            'tier': 1,
        },
    ),
    TabletVerse(
        key='as_below',
        latin_fragment='Quod est inferius est sicut quod est superius',
        hermetic_text='That which is below is like that which is above',
        technical_translation=(
            'HAARP-to-EPOS Scaling Law — ionospheric physics (70 km, 3.6 MW) '
            'mapped to 30 cm chamber via power-density conservation'
        ),
        aureon_implementation='rho_P_epos / rho_P_haarp = volumetric concentration factor',
        parameters={
            'haarp_power_w': HAARP_POWER_W,
            'epos_power_w': EPOS_RF_POWER_W,
            'concentration_factor': VOLUMETRIC_CONCENTRATION_FACTOR,
            'units': 'W/m^3',
        },
        pipeline_stage=1,
    ),
    TabletVerse(
        key='as_above',
        latin_fragment='Et quod est superius est sicut quod est inferius',
        hermetic_text='And that which is above is like that which is below',
        technical_translation=(
            'Inverse Square Containment — microcosm reproduces macrocosm physics'
        ),
        aureon_implementation='Paschen breakdown @ 0.1 mbar replicates F-region electron density',
        parameters={
            'paschen_pd': PASCHEN_OPTIMAL_PD,
            'breakdown_v': PASCHEN_BREAKDOWN_V,
            'electron_density_m3': 1e11,
        },
        pipeline_stage=2,
    ),
    TabletVerse(
        key='one_thing',
        latin_fragment='Ad perpetranda miracula rei unius',
        hermetic_text='To do the miracles of one only thing',
        technical_translation=(
            'The HNC Seed — single coherent harmonic (7.83 Hz Schumann) '
            'modulated on 13.56 MHz carrier'
        ),
        aureon_implementation='f_carrier = 13.56 MHz, f_modulation = 7.83 Hz (HNC Lumina seed)',
        parameters={
            'carrier_hz': RF_CARRIER_ISM,
            'modulation_hz': SCHUMANN_FUNDAMENTAL,
            'scheme': 'AM',
        },
        pipeline_stage=4,
    ),
    TabletVerse(
        key='mediation',
        latin_fragment='Et sicut omnes res fuerunt ab uno, meditatione unius',
        hermetic_text=(
            'And as all things have been & arose from one '
            'by the mediation of one'
        ),
        technical_translation=(
            'Harmonic Nexus Bridge — all domains (financial, plasma, '
            'information) unified by Bayesian L(t) metric'
        ),
        aureon_implementation='DomainAnomaly class with cross-correlation detection',
        parameters={
            'bridge_module': 'aureon.harmonic_nexus_bridge',
            'unification_metric': 'L(t)',
        },
    ),
    TabletVerse(
        key='adaptation',
        latin_fragment='Sic omnes res natae fuerunt ab hac una re, adaptatione',
        hermetic_text=(
            'So all things have their birth from this one thing '
            'by adaptation'
        ),
        technical_translation=(
            'Lambda calibration — different domains adapt lambda (holding '
            'penalty) to local constraints'
        ),
        aureon_implementation=(
            'Magamyman lambda > 0.5 (High-Decay); EPOS lambda = 0.1-0.3 '
            '(Stealth Constraint)'
        ),
        parameters={
            'lambda_magamyman': 0.5,
            'lambda_epos_range': (0.1, 0.3),
        },
    ),
    TabletVerse(
        key='sun_moon',
        latin_fragment='Pater eius est Sol, mater eius Luna',
        hermetic_text='The Sun is its father, the Moon its mother',
        technical_translation=(
            'N/S Dipole Configuration — parallel plate electrodes '
            '(North/South poles) creating the dipole field'
        ),
        aureon_implementation='Electrode config: Parallel plate, 30 cm gap (N/S poles)',
        parameters={
            'gap_m': EPOS_CHAMBER_DIAMETER_M,
            'topology': 'parallel_plate_dipole',
        },
        pipeline_stage=5,
    ),
    TabletVerse(
        key='wind',
        latin_fragment='Portavit illud ventus in ventre suo',
        hermetic_text='The wind hath carried it in its belly',
        technical_translation=(
            'RF Carrier Propagation — 13.56 MHz ISM band carrying '
            'the ELF harmonic modulation'
        ),
        aureon_implementation='AM modulation scheme (same as HAARP ELF generation)',
        parameters={
            'carrier_hz': RF_CARRIER_ISM,
            'modulation_hz': SCHUMANN_FUNDAMENTAL,
            'method': 'HAARP_ELF_GENERATION_ANALOG',
        },
    ),
    TabletVerse(
        key='earth_nurse',
        latin_fragment='Nutrix eius terra est',
        hermetic_text='The earth is its nurse',
        technical_translation=(
            'Vacuum Chamber Ground — 30 cm spherical vessel as '
            'containment / nursery for plasma genesis'
        ),
        aureon_implementation='V_chamber = 14.1 L, Argon @ 0.1 mbar',
        parameters={
            'volume_liters': round(EPOS_CHAMBER_VOLUME_M3 * 1000, 1),
            'gas': 'Argon',
            'pressure_mbar': EPOS_PRESSURE_MBAR,
        },
    ),
    TabletVerse(
        key='separate',
        latin_fragment='Separabis terram ab igne',
        hermetic_text='Separate thou the earth from the fire',
        technical_translation=(
            'Paschen Breakdown Optimization — separate gas pressure (earth) '
            'from ignition voltage (fire)'
        ),
        aureon_implementation='Optimal p*d = 2.25 Torr*cm (400 V breakdown minimum)',
        parameters={
            'paschen_pd': PASCHEN_OPTIMAL_PD,
            'breakdown_v': PASCHEN_BREAKDOWN_V,
        },
        pipeline_stage=3,
    ),
    TabletVerse(
        key='subtle_gross',
        latin_fragment='Subtile a spisso suaviter cum magno ingenio',
        hermetic_text='The subtle from the gross sweetly with great industry',
        technical_translation=(
            'Power Density Refinement — 3.6 MW (gross/HAARP) refined to '
            '50 W (subtle/EPOS) via volumetric concentration'
        ),
        aureon_implementation='P_ratio = EPOS_RF / HAARP = power scaling',
        parameters={
            'power_ratio': EPOS_RF_POWER_W / HAARP_POWER_W,
            'haarp_w': HAARP_POWER_W,
            'epos_w': EPOS_RF_POWER_W,
        },
    ),
    TabletVerse(
        key='ascend_descend',
        latin_fragment='Ascendit a terra in coelum, iterumque descendit in terram',
        hermetic_text='It ascends from earth to heaven & again descends',
        technical_translation=(
            'Information Cascade — data flows from classified source (heaven) '
            'to market (earth) and back to blockchain record'
        ),
        aureon_implementation='T_event (strike) -> T_public (news) -> T_resolution (settlement)',
        parameters={
            'cascade_stages': ['T_event', 'T_public', 'T_resolution'],
        },
    ),
    TabletVerse(
        key='glory',
        latin_fragment='Sic habebis gloriam totius mundi',
        hermetic_text='By this means ye shall have the glory of the world',
        technical_translation='Profit Extraction — the 488 % ROI materialisation',
        aureon_implementation='magamyman_profit = 553000, cluster_profit = 1200000',
        parameters={
            'magamyman_profit_usd': 553_000,
            'cluster_profit_usd': 1_200_000,
            'roi_pct': 488,
        },
    ),
    TabletVerse(
        key='obscurity',
        latin_fragment='Ideo fugiet a te omnis obscuritas',
        hermetic_text='All obscurity shall fly from thee',
        technical_translation=(
            'Anomaly Detection Clarity — L(t) score renders invisible '
            'correlations visible'
        ),
        aureon_implementation='L(t) = 12.85 (obscurity -> signal)',
        parameters={
            'lt_score': 12.85,
            'severity': 'EXTREME',
        },
    ),
    TabletVerse(
        key='strong_force',
        latin_fragment='Haec est totius fortitudinis fortitudo fortis',
        hermetic_text='This is the strong force of all forces',
        technical_translation=(
            'The Bayesian Likelihood Ratio — strongest statistical force '
            'for separating signal from noise'
        ),
        aureon_implementation='L(C) = log[P(O|M_adv) / P(O|M_naive)]',
        parameters={
            'formula': 'log_likelihood_ratio',
        },
    ),
    TabletVerse(
        key='overcome_subtle',
        latin_fragment='Quia vincet omnem rem subtilem',
        hermetic_text='It will overcome every subtle thing',
        technical_translation=(
            'Penetration of Obfuscation — detects coordinated wallets '
            'despite Gini masking'
        ),
        aureon_implementation='Gini Symmetry Coefficient = 0.00 (perfect coordination)',
        parameters={
            'gini_symmetry': 0.00,
            'detection': 'wallet_clustering',
        },
    ),
    TabletVerse(
        key='penetrate_solid',
        latin_fragment='Omnemque rem solidam penetrabit',
        hermetic_text='And penetrate every solid thing',
        technical_translation=(
            'Blockchain Transparency — on-chain record penetrates '
            'pseudonymous obfuscation'
        ),
        aureon_implementation='Polygon on-chain analysis (wallet clustering)',
        parameters={
            'chain': 'polygon',
            'method': 'on_chain_analysis',
        },
    ),
    TabletVerse(
        key='world_created',
        latin_fragment='Sic mundus creatus est',
        hermetic_text='So was the world created',
        technical_translation=(
            'Genesis Event — the February 28, 2026 strike as resolved '
            'market creation'
        ),
        aureon_implementation='event_time = 2026-02-28T13:29:00Z',
        parameters={
            'event_time': '2026-02-28T13:29:00+00:00',
            'event_label': 'EPIC-FURY',
        },
    ),
    TabletVerse(
        key='adaptations',
        latin_fragment='Hinc erunt adaptationes mirabiles',
        hermetic_text='Hence are all wonderful adaptations',
        technical_translation=(
            'Cross-Domain Correlation — financial and plasma events '
            'synchronised'
        ),
        aureon_implementation='clustering_score = 2.77x (non-random alignment)',
        parameters={
            'clustering_score': 2.77,
            'interpretation': 'CORRELATED',
        },
    ),
    TabletVerse(
        key='manner',
        latin_fragment='Quarum modus est hic',
        hermetic_text='Of which this is the manner',
        technical_translation='The L(t) Algorithm — the specific mathematical implementation',
        aureon_implementation='lotka_volterra_l_score() function',
        parameters={
            'function': 'lotka_volterra_l_score',
        },
    ),
    TabletVerse(
        key='trismegistus',
        latin_fragment='Itaque vocatus sum Hermes Trismegistus',
        hermetic_text='Therefore I am called Hermes Trismegistus',
        technical_translation=(
            'Triple Greatness — three domains unified: '
            'Geopolitical, Plasma, Information'
        ),
        aureon_implementation='DomainAnomaly (GEO, PLASMA, NETWORK)',
        parameters={
            'domains': ['geopolitical', 'plasma', 'network'],
        },
    ),
    TabletVerse(
        key='three_parts',
        latin_fragment='Tres partes philosophiae totius mundi',
        hermetic_text='Having the three parts of the philosophy of the world',
        technical_translation=(
            'Three Tiers of Evidence — Tier 1 (reported), Tier 2 (derived), '
            'Tier 3 (modelled)'
        ),
        aureon_implementation='legal_admissibility_notes (Tier ratios 85/10/5)',
        parameters={
            'tier_1_pct': 85,
            'tier_2_pct': 10,
            'tier_3_pct': 5,
        },
    ),
)

VERSE_INDEX: Dict[str, TabletVerse] = {v.key: v for v in _VERSE_CATALOG}

# ════════════════════════════════════════════════════════════════════════════
# SEVEN ALCHEMICAL STAGES → L(t) CALCULATION PIPELINE
# ════════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class AlchemicalStage:
    """One of the seven alchemical operations mapped to a pipeline step."""

    number: int
    name: str
    operation: str
    formula: str
    computed_value: float
    units: str
    verse_key: Optional[str] = None


def _build_seven_stages() -> Tuple[AlchemicalStage, ...]:
    stage_1_val = HAARP_POWER_W / HAARP_VOLUME_M3
    stage_2_val = IONOSPHERIC_FLUX_W_M2
    stage_3_val = EPOS_CHAMBER_AREA_M2
    stage_4_val = POWER_COUPLING_METHOD1
    stage_5_val = PASCHEN_BREAKDOWN_V
    stage_6_val = EPOS_RF_POWER_W
    stage_7_val = 12.85  # Final L(t) coagulation

    return (
        AlchemicalStage(
            number=1,
            name='Calcination',
            operation='Reduction of gross power to density baseline',
            formula='P_haarp_rf / V_haarp',
            computed_value=stage_1_val,
            units='W/m^3',
            verse_key='as_below',
        ),
        AlchemicalStage(
            number=2,
            name='Dissolution',
            operation='Dissolving HAARP output into flux units',
            formula='flux_ionosphere = 0.03',
            computed_value=stage_2_val,
            units='W/m^2',
            verse_key='as_above',
        ),
        AlchemicalStage(
            number=3,
            name='Separation',
            operation='Separating the 30 cm chamber cross-section',
            formula='A_chamber = pi * (d/2)^2',
            computed_value=round(stage_3_val, 6),
            units='m^2',
            verse_key='separate',
        ),
        AlchemicalStage(
            number=4,
            name='Conjunction',
            operation='Recombining flux with area',
            formula='P_method1 = flux * A_chamber',
            computed_value=round(stage_4_val, 6),
            units='W',
            verse_key='one_thing',
        ),
        AlchemicalStage(
            number=5,
            name='Fermentation',
            operation='Ionization threshold (spark of life)',
            formula='Paschen breakdown @ 400 V',
            computed_value=stage_5_val,
            units='V',
            verse_key='sun_moon',
        ),
        AlchemicalStage(
            number=6,
            name='Distillation',
            operation='Refining to pure plasma drive power',
            formula='P_rf_typical = 50 W',
            computed_value=stage_6_val,
            units='W',
        ),
        AlchemicalStage(
            number=7,
            name='Coagulation',
            operation='Final solidification of anomaly score',
            formula='L(t) = sum(components)',
            computed_value=stage_7_val,
            units='L(t)',
        ),
    )


SEVEN_STAGES = _build_seven_stages()
STAGE_INDEX: Dict[int, AlchemicalStage] = {s.number: s for s in SEVEN_STAGES}


@dataclass(frozen=True)
class AncientCrosswalk:
    """Cross-reference from Emerald verses into repo-backed ancient surfaces."""

    key: str
    title: str
    focus: str
    emerald_verse_keys: Tuple[str, ...]
    stage_numbers: Tuple[int, ...] = field(default_factory=tuple)
    deity: Dict[str, str] = field(default_factory=dict)
    scripture: Dict[str, str] = field(default_factory=dict)
    hieroglyph: Dict[str, str] = field(default_factory=dict)
    runtime: Dict[str, str] = field(default_factory=dict)
    repo_surfaces: Tuple[str, ...] = field(default_factory=tuple)
    interpretation: str = ''


@dataclass(frozen=True)
class WikipediaMeaning:
    """Canonical historical grounding fetched from the live Wikipedia API."""

    query: str
    resolved_query: str
    title: str
    summary: str
    description: str
    page_id: int
    url: str
    source: str = 'wikipedia_rest_summary'

    def to_dict(self) -> Dict[str, object]:
        return {
            'query': self.query,
            'resolved_query': self.resolved_query,
            'title': self.title,
            'summary': self.summary,
            'description': self.description,
            'page_id': self.page_id,
            'url': self.url,
            'source': self.source,
        }


@dataclass(frozen=True)
class HarmonicThread:
    """A universal harmonic pattern traceable across multiple ancient wisdom traditions.

    These threads are the *connecting tissue* of the unified theory: recurring ratios,
    frequencies, and structural principles that appear independently in every civilization
    that aligned its sacred practice with the cosmos.
    """

    key: str
    title: str
    value: float
    unit: str
    frequency_hz: Optional[float]
    civilizations: Tuple[str, ...]
    nodes: Tuple[str, ...]
    sacred_numbers: Tuple[float, ...]
    description: str
    repo_constant: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        return {
            'key': self.key,
            'title': self.title,
            'value': self.value,
            'unit': self.unit,
            'frequency_hz': self.frequency_hz,
            'civilizations': list(self.civilizations),
            'nodes': list(self.nodes),
            'sacred_numbers': list(self.sacred_numbers),
            'description': self.description,
            'repo_constant': self.repo_constant,
        }


# ════════════════════════════════════════════════════════════════════════════
# PROJECT DRUID — PHYSICAL EPAS MANIFESTATION
# Six Illumination Phases (P1–P6) mapped onto the real EPOS chamber physics.
# EPOS device: 30 cm spherical Argon vessel · 0.1 mbar · 50 W RF at 13.56 MHz
# Seed:        7.83 Hz Schumann AM modulation on the carrier
# Output:      350–400 VDC via A.L.F.I.E. propulsion bus (P6 gate)
# ════════════════════════════════════════════════════════════════════════════

_PHASE_LABELS: Tuple[str, ...] = (
    'P1 Spark', 'P2 Resonance', 'P3 DCE', 'P4 FWM', 'P5 Stabilization', 'P6 Output',
)
_SIGMA_COHERENCE_TARGET = 0.945    # Γ ≥ 0.945 for stable P5 — white paper §Illumination
_AUXILIARY_POWER_W = 12.0          # control electronics + Schumann modulation overhead
_OUTPUT_VOLTAGE_VDC = 375.0        # mid-point of 350–400 VDC delivery band


@dataclass(frozen=True)
class ProjectDruidManifest:
    """Physical EPAS device specification — Project Druid.

    Maps the three EPAS trading shield layers (L1 EM / L2 Plasma / L3 Acoustic)
    onto the real EPOS resonance chamber through six Illumination Phases (P1–P6).

    L1 EM Deflection    → P1 Spark + P2 Resonance  (harmonic field prime)
    L2 Plasma Ablation  → P6 Output                (equity buffer = power delivery)
    L3 Acoustic Frag    → P3 DCE                   (premise coherence = vacuum memory)
    Radar incoming      → P4 FWM                   (amplification / threat mixing)
    Overall integrity   → P5 Stabilization         (Σ tensor guard Γ ≥ 0.945)
    """

    timestamp: str

    # ── Chamber parameters ──────────────────────────────────────────────────
    chamber_diameter_m: float
    chamber_volume_m3: float
    fill_gas: str
    fill_pressure_mbar: float

    # ── Plasma density (Paschen law) ────────────────────────────────────────
    paschen_pd_torr_cm: float     # P × d product at current conditions
    breakdown_voltage_v: float
    plasma_density_m3: float      # estimated electron density (m⁻³)
    plasma_status: str            # IGNITED | PRIMED | DORMANT

    # ── Power requirements ──────────────────────────────────────────────────
    rf_carrier_hz: float
    rf_modulation_hz: float
    rf_power_w: float
    auxiliary_power_w: float
    total_power_w: float
    output_voltage_vdc: float     # 350–400 VDC when P6 DELIVERING

    # ── HAARP scaling ───────────────────────────────────────────────────────
    haarp_power_w: float
    concentration_factor: int
    power_density_w_m3: float

    # ── Six Illumination Phases ─────────────────────────────────────────────
    phase_scores: Tuple[float, ...]    # P1–P6, 0.0–1.0
    phase_statuses: Tuple[str, ...]    # status label per phase
    shield_coherence: float            # Γ = mean(phase_scores)

    # ── Verdict ─────────────────────────────────────────────────────────────
    device_ready: bool
    druid_summary: str

    def to_dict(self) -> Dict[str, object]:
        return {
            'timestamp': self.timestamp,
            'chamber': {
                'diameter_m': self.chamber_diameter_m,
                'volume_m3': self.chamber_volume_m3,
                'fill_gas': self.fill_gas,
                'fill_pressure_mbar': self.fill_pressure_mbar,
            },
            'plasma': {
                'paschen_pd_torr_cm': self.paschen_pd_torr_cm,
                'breakdown_voltage_v': self.breakdown_voltage_v,
                'density_m3': self.plasma_density_m3,
                'status': self.plasma_status,
            },
            'power': {
                'rf_carrier_hz': self.rf_carrier_hz,
                'rf_modulation_hz': self.rf_modulation_hz,
                'rf_power_w': self.rf_power_w,
                'auxiliary_w': self.auxiliary_power_w,
                'total_w': self.total_power_w,
                'output_vdc': self.output_voltage_vdc,
            },
            'haarp_scaling': {
                'haarp_power_w': self.haarp_power_w,
                'concentration_factor': self.concentration_factor,
                'power_density_w_m3': self.power_density_w_m3,
            },
            'illumination_phases': [
                {
                    'phase': _PHASE_LABELS[i],
                    'score': round(self.phase_scores[i], 4),
                    'status': self.phase_statuses[i],
                }
                for i in range(6)
            ],
            'shield_coherence': round(self.shield_coherence, 4),
            'sigma_coherence_target': _SIGMA_COHERENCE_TARGET,
            'device_ready': self.device_ready,
            'druid_summary': self.druid_summary,
        }


def compute_project_druid_manifest(
    epas_state: Optional[Dict[str, object]] = None,
) -> 'ProjectDruidManifest':
    """Compute the physical EPOS device specification from an EPAS shield state.

    When *epas_state* is ``None`` the function uses the baseline harmonic scores
    from the live EPAS smoke test (SHIELDS_STRESSED, integrity 0.545) so the
    manifest is always computable without a live trading runtime.

    Parameters
    ----------
    epas_state:
        Optional dict with keys matching ``EPASShieldState`` fields.
        Expected: layer1_field_score, layer2_score, layer3_score,
                  shield_integrity, (optional) radar_score.
    """
    s = epas_state or {}

    # ── Extract EPAS scores (or use live baseline) ─────────────────────────
    l1 = float(s.get('layer1_field_score', 0.646))   # L1 field  — live default
    l2 = float(s.get('layer2_score',       0.500))   # L2 equity — UNKNOWN baseline
    l3 = float(s.get('layer3_score',       0.508))   # L3 premise — live CRACKING
    integrity = float(s.get('shield_integrity', 0.545))
    radar = float(s.get('radar_score', 0.728))        # RADAR_BULLISH current default

    # ── Six Illumination Phases ────────────────────────────────────────────
    # P1 Spark       — nanosecond field prime (L1 harmonic detection)
    p1 = min(1.0, max(0.0, l1))
    # P2 Resonance   — standing wave coherence (field + premise blend)
    p2 = min(1.0, max(0.0, (l1 + l3) / 2.0))
    # P3 DCE         — Dynamic Casimir Effect: vacuum field memory (L3 premise lock)
    p3 = min(1.0, max(0.0, l3))
    # P4 FWM         — Four-Wave Mixing amplification (radar × PHI, scaled)
    p4 = min(1.0, max(0.0, radar * PHI / 2.0))
    # P5 Stabilization — Σ tensor guard (overall shield integrity = Γ target)
    p5 = min(1.0, max(0.0, integrity))
    # P6 Output      — physical reality gate: equity buffer drives power delivery
    p6 = min(1.0, max(0.0, l2))

    phase_scores: Tuple[float, ...] = (p1, p2, p3, p4, p5, p6)

    _status_tables = (
        [('PRIMED',      0.62), ('SPARKING',    0.42), ('COLD',       0.0)],
        [('RESONANT',    0.65), ('COUPLING',    0.42), ('DISPERSED',  0.0)],
        [('ACTIVE',      0.65), ('FLUCTUATING', 0.38), ('COLLAPSED',  0.0)],
        [('AMPLIFYING',  0.62), ('MIXING',      0.42), ('DAMPED',     0.0)],
        [('STABLE',      0.70), ('STABILIZING', 0.42), ('UNSTABLE',   0.0)],
        [('DELIVERING',  0.70), ('CHARGING',    0.50), ('OFFLINE',    0.0)],
    )

    def _p_status(idx: int, score: float) -> str:
        for label, threshold in _status_tables[idx]:
            if score >= threshold:
                return label
        return 'OFFLINE'

    phase_statuses: Tuple[str, ...] = tuple(
        _p_status(i, phase_scores[i]) for i in range(6)
    )

    # ── Shield coherence Γ ─────────────────────────────────────────────────
    shield_coherence = sum(phase_scores) / len(phase_scores)

    # ── Plasma density via Paschen scaling ─────────────────────────────────
    # P = 0.1 mbar → 0.075 Torr; electrode path ≈ chamber radius = 15 cm
    pressure_torr = EPOS_PRESSURE_MBAR * 0.750062      # mbar → Torr
    path_cm = (EPOS_CHAMBER_DIAMETER_M / 2.0) * 100    # half-diameter in cm
    pd_product = pressure_torr * path_cm               # Torr·cm
    # Electron density scales proportional to P*d vs target optimal P*d
    # Target: replicate F-region density 1e11 m⁻³ at Paschen optimal (2.25 Torr·cm)
    base_density_m3 = 1e11
    plasma_density = base_density_m3 * (pd_product / PASCHEN_OPTIMAL_PD)

    # Plasma ignition state
    phi_gate = PHI / (PHI + 1)                         # ≈ 0.618 golden ratio gate
    if shield_coherence >= _SIGMA_COHERENCE_TARGET:
        plasma_status = 'IGNITED'
    elif shield_coherence >= phi_gate:
        plasma_status = 'PRIMED'
    else:
        plasma_status = 'DORMANT'

    # ── Power budget ───────────────────────────────────────────────────────
    total_power = EPOS_RF_POWER_W + _AUXILIARY_POWER_W

    # ── Verdict summary ────────────────────────────────────────────────────
    device_ready = plasma_status in ('IGNITED', 'PRIMED')

    weak = [_PHASE_LABELS[i] for i, st in enumerate(phase_statuses)
            if st in ('COLD', 'DISPERSED', 'COLLAPSED', 'DAMPED', 'UNSTABLE', 'OFFLINE')]

    if plasma_status == 'IGNITED':
        druid_summary = (
            f'DEVICE ONLINE  Γ={shield_coherence:.3f}/{_SIGMA_COHERENCE_TARGET}  '
            f'plasma=IGNITED  P5={phase_statuses[4]}  P6={phase_statuses[5]}'
        )
    elif plasma_status == 'PRIMED':
        druid_summary = (
            f'DEVICE PRIMED  Γ={shield_coherence:.3f}  '
            f'weak=[{", ".join(weak) or "none"}]  '
            f'needs_Γ≥{_SIGMA_COHERENCE_TARGET}'
        )
    else:
        druid_summary = (
            f'DEVICE DORMANT  Γ={shield_coherence:.3f}  '
            f'weak=[{", ".join(weak) or "none"}]  '
            f'needs_Γ≥{phi_gate:.3f}(PRIMED) or ≥{_SIGMA_COHERENCE_TARGET}(IGNITED)'
        )

    return ProjectDruidManifest(
        timestamp=datetime.now(timezone.utc).isoformat(),
        chamber_diameter_m=EPOS_CHAMBER_DIAMETER_M,
        chamber_volume_m3=EPOS_CHAMBER_VOLUME_M3,
        fill_gas='Argon',
        fill_pressure_mbar=EPOS_PRESSURE_MBAR,
        paschen_pd_torr_cm=round(pd_product, 4),
        breakdown_voltage_v=PASCHEN_BREAKDOWN_V,
        plasma_density_m3=round(plasma_density, 2),
        plasma_status=plasma_status,
        rf_carrier_hz=RF_CARRIER_ISM,
        rf_modulation_hz=SCHUMANN_FUNDAMENTAL,
        rf_power_w=EPOS_RF_POWER_W,
        auxiliary_power_w=_AUXILIARY_POWER_W,
        total_power_w=total_power,
        output_voltage_vdc=_OUTPUT_VOLTAGE_VDC,
        haarp_power_w=HAARP_POWER_W,
        concentration_factor=VOLUMETRIC_CONCENTRATION_FACTOR,
        power_density_w_m3=round(EPOS_POWER_DENSITY, 2),
        phase_scores=phase_scores,
        phase_statuses=phase_statuses,
        shield_coherence=round(shield_coherence, 4),
        device_ready=device_ready,
        druid_summary=druid_summary,
    )


ASCENT_WIKIPEDIA_TOPICS: Dict[str, Tuple[str, ...]] = {
    # ── Egyptian ──
    'anubis': ('Emerald Tablet', 'Anubis', 'Book of the Dead', 'Maat'),
    'maat': ('Emerald Tablet', 'Maat', 'Book of the Dead'),
    'thoth': ('Emerald Tablet', 'Thoth', 'Hermes Trismegistus'),
    'osiris': ('Emerald Tablet', 'Osiris', 'Book of the Dead'),
    'ra': ('Emerald Tablet', 'Ra'),
    # ── Ancient Wisdom ──
    'mogollon': ('Mogollon culture', 'Petroglyph', 'Golden ratio', 'Ancestral Puebloans'),
    'maya': ('Maya civilization', 'Maya calendar', 'Tzolkin', 'Venus (planet)'),
    'celt': ('Celtic mythology', 'Ogham', 'Druids', 'Stonehenge'),
}


def _build_unified_harmonic_threads() -> Tuple[HarmonicThread, ...]:
    """Build the five universal harmonic threads that connect all ancient wisdom traditions."""
    return (
        HarmonicThread(
            key='phi_spiral',
            title='The Golden Spiral — PHI across All Civilizations',
            value=PHI,
            unit='ratio',
            frequency_hz=None,
            civilizations=('hermetic', 'egyptian', 'mogollon', 'maya', 'celt'),
            nodes=('anubis', 'maat', 'thoth', 'osiris', 'ra', 'mogollon', 'maya', 'celt'),
            sacred_numbers=(PHI, 1.0, 1 / PHI, 5.0, 8.0, 13.0, 21.0),
            description=(
                'PHI = 1.618... is the governing ratio of self-similar growth. '
                'Egyptian temple proportions encode PHI. Mogollon spiral petroglyphs trace '
                'the Fibonacci/PHI spiral. The Maya Venus/Earth ratio = 5 Venus cycles per '
                '8 Earth years (8/5 = 1.6 ≈ PHI). The Celtic tree calendar has 13 lunar months '
                'and 8 feast days — Fibonacci numbers: 13/8 = 1.625 ≈ PHI. '
                'This is not coincidence. PHI is the attractor of natural growth in all systems.'
            ),
            repo_constant='PHI = (1 + sqrt(5)) / 2  # aureon/decoders/emerald_spec.py',
        ),
        HarmonicThread(
            key='schumann_resonance',
            title='Earth Heartbeat — 7.83 Hz Schumann Resonance',
            value=SCHUMANN_FUNDAMENTAL,
            unit='Hz',
            frequency_hz=SCHUMANN_FUNDAMENTAL,
            civilizations=('all',),
            nodes=('anubis', 'maat', 'thoth', 'osiris', 'ra', 'mogollon', 'maya', 'celt'),
            sacred_numbers=(7.83, 14.3, 20.8, 27.3, 33.8),
            description=(
                'The Schumann Resonance (7.83 Hz) is the electromagnetic resonance of the '
                "cavity between Earth's surface and the ionosphere. Every Earth-aligned culture "
                'built sacred architecture to track the sky and synchronise with this frequency: '
                'Mogollon spiral petroglyphs track solstice alignments, Maya observatories were '
                'precisely oriented, Celtic standing stones at Stonehenge are equinox/solstice '
                'calendars, and Egyptian obelisks were ionospheric antennae. '
                'The planet broadcasts at 7.83 Hz. The Aureon system uses this as its primary seed.'
            ),
            repo_constant='SCHUMANN_FUNDAMENTAL = 7.83  # aureon/decoders/emerald_spec.py',
        ),
        HarmonicThread(
            key='solar_cycle',
            title='Solar Year — The 365.25-Day Universal Timekeeper',
            value=365.25,
            unit='days',
            frequency_hz=1.0 / (365.25 * 86400.0),
            civilizations=('maya', 'celt', 'egyptian', 'mogollon'),
            nodes=('ra', 'mogollon', 'maya', 'celt', 'osiris'),
            sacred_numbers=(365.0, 365.25, 260.0, 52.0, 18980.0, 5125.0),
            description=(
                'The solar year binds all ancient wisdom systems. Maya Haab = 365-day solar '
                "calendar. Celtic 13-moon year = 364 + 1 'nameless' day = 365. Egyptian civil "
                'calendar = 365 days. Mogollon spiral sun-daggers mark solstices to within '
                'minutes of arc. The Maya Calendar Round = LCM(260, 365) = 18,980 days = '
                '52-year cycle, encoded in temple step-counts worldwide. '
                'Time is the first universal language across all recorded traditions.'
            ),
            repo_constant=None,
        ),
        HarmonicThread(
            key='triple_wisdom',
            title='The Sacred Triad — Three-Part Wisdom Structure',
            value=3.0,
            unit='domains',
            frequency_hz=None,
            civilizations=('hermetic', 'celt', 'egyptian', 'maya'),
            nodes=('thoth', 'celt', 'ra', 'maat', 'maya'),
            sacred_numbers=(3.0, 9.0, 27.0, 81.0),
            description=(
                'Three-fold structure is universal: Hermes Trismegistus = "Thrice Great" '
                '(philosophy, alchemy, theurgy). Celtic triskelion/triads = land/sea/sky / '
                "past/present/future. Egyptian Trinity = Osiris/Isis/Horus. Maya three "
                "hearthstones of creation (Orion's Belt). The repo's DomainAnomaly uses three "
                'domains (GEO/PLASMA/NETWORK). Three is the minimum stable closed geometric '
                'form (triangle). All stable truth requires three independent confirmations — '
                'the Batten Matrix 3-pass validation before the 4th execution pass.'
            ),
            repo_constant='DomainAnomaly(GEO, PLASMA, NETWORK)  # aureon_unified_ecosystem.py',
        ),
        HarmonicThread(
            key='void_origin',
            title='The Void — Zero as the Source of All Creation',
            value=0.0,
            unit='prima_materia',
            frequency_hz=None,
            civilizations=('maya', 'hermetic', 'celt', 'mogollon'),
            nodes=('mogollon', 'maya', 'celt', 'anubis'),
            sacred_numbers=(0.0, 1.0, 2.8, PHI),
            description=(
                'Maya mathematicians invented positional zero — the void from which all numbers '
                'spring. Hermetic Prima Materia = the formless void before manifestation. '
                'Celtic: the Cauldron of the Dagda (inexhaustible void → abundance). '
                'Mogollon: the sipapu (emergence hole from the underworld — the still point of '
                'the spiral, the void origin). In trading terms: L(t) = 0 is the void '
                '(pure noise). L(t) > 2.8 is the Philosopher\'s Stone (signal from void). '
                'Every trade begins in silence.'
            ),
            repo_constant='PHILOSOPHERS_STONE_THRESHOLD = 2.8  # null → signal transition',
        ),
    )


UNIFIED_HARMONIC_THREADS: Tuple[HarmonicThread, ...] = _build_unified_harmonic_threads()
HARMONIC_THREAD_INDEX: Dict[str, HarmonicThread] = {t.key: t for t in UNIFIED_HARMONIC_THREADS}


def _build_egyptian_ascent_catalog() -> Tuple[AncientCrosswalk, ...]:
    return (
        AncientCrosswalk(
            key='anubis',
            title='Anubis Gate',
            focus='Judgment before execution',
            emerald_verse_keys=('verum', 'separate', 'earth_nurse'),
            stage_numbers=(3, 5),
            deity={
                'name': 'Anubis',
                'glyph': '🐺',
                'domain': 'Death, Embalming, Underworld Guide',
                'cycle': "Weighs hearts against Ma'at's feather",
                'trading': 'Judge each trade honestly. Is it worthy? Weigh risk against reward.',
            },
            scripture={
                'book_of_dead_key': 'spell_125',
                'title': 'Weighing of the Heart',
                'wisdom': "Heart weighed against Ma'at's feather",
                'trading': 'Every trade is weighed. Is it balanced? Is it true?',
            },
            hieroglyph={
                'key': 'feather_of_maat',
                'symbol': '🪶',
                'meaning': 'Truth, Justice, Balance',
                'trading': "Feather of Ma'at - trade truthfully. Balance risk.",
            },
            runtime={
                'market_state': 'EXTREME_FEAR',
                'trigger': 'fear_greed < 20 selects Anubis in get_deity_for_market()',
                'action': 'OBSERVE',
                'message': 'Anubis weighs the market. Death and rebirth ahead.',
                'note': (
                    'The current WisdomCognitionEngine collapses Anubis into a neutral '
                    'observe action rather than a direct buy/sell bias.'
                ),
            },
            repo_surfaces=(
                'aureon_miner_brain.py::EgyptianWisdomLibrary.NETJERU["Anubis"]',
                'aureon_miner_brain.py::EgyptianWisdomLibrary.BOOK_OF_DEAD["spell_125"]',
                'aureon_miner_brain.py::EgyptianWisdomLibrary.HIEROGLYPHS["feather_of_maat"]',
                'aureon_miner_brain.py::WisdomCognitionEngine._extract_egyptian_action',
            ),
            interpretation=(
                'The ascent starts with judgment: the Emerald decoder first separates truth '
                'from noise, then Anubis weighs whether the signal is worthy of passage.'
            ),
        ),
        AncientCrosswalk(
            key='maat',
            title="Ma'at Balance Gate",
            focus='Truth, balance, and equilibrium',
            emerald_verse_keys=('verum', 'strong_force', 'three_parts'),
            deity={
                'name': "Ma'at",
                'glyph': '⚖️',
                'domain': 'Truth, Justice, Cosmic Order, Balance',
                'cycle': 'Feather weighs hearts - maintains universal balance',
                'trading': "Markets seek balance. Extremes revert. Ma'at always wins.",
            },
            scripture={
                'book_of_dead_key': 'spell_125',
                'title': 'Weighing of the Heart',
                'wisdom': "Heart weighed against Ma'at's feather",
                'trading': 'Every trade is weighed. Is it balanced? Is it true?',
            },
            hieroglyph={
                'key': 'feather_of_maat',
                'symbol': '🪶',
                'meaning': 'Truth, Justice, Balance',
                'trading': "Feather of Ma'at - trade truthfully. Balance risk.",
            },
            runtime={
                'market_state': 'BALANCED_NEUTRAL',
                'trigger': (
                    'Default deity when fear_greed is not extreme and btc_change is not '
                    'a strong breakout'
                ),
                'action': 'BALANCE',
                'message': 'Ma\'at maintains balance. The market seeks equilibrium.',
            },
            repo_surfaces=(
                'aureon_miner_brain.py::EgyptianWisdomLibrary.NETJERU["Ma\'at"]',
                'aureon_miner_brain.py::EgyptianWisdomLibrary.BOOK_OF_DEAD["spell_125"]',
                'aureon_miner_brain.py::EgyptianWisdomLibrary.HIEROGLYPHS["feather_of_maat"]',
            ),
            interpretation=(
                'Once Anubis has weighed the signal, Ma\'at holds it in equilibrium. '
                'This is the repo\'s explicit balance layer.'
            ),
        ),
        AncientCrosswalk(
            key='thoth',
            title='Thoth Codex Layer',
            focus='Time, record-keeping, and mathematics',
            emerald_verse_keys=('manner', 'ascend_descend', 'trismegistus'),
            stage_numbers=(7,),
            deity={
                'name': 'Thoth',
                'glyph': '📚',
                'domain': 'Writing, Knowledge, Moon, Time, Mathematics',
                'cycle': 'Keeper of records, inventor of writing, measurer of time',
                'trading': 'Keep records. Journal trades. Knowledge compounds like interest.',
            },
            scripture={
                'book_of_dead_key': 'spell_17',
                'title': 'Coming and Going in the Underworld',
                'wisdom': 'Know the paths through darkness',
                'trading': 'Study bear market patterns. Know the path through.',
            },
            runtime={
                'market_state': 'STATIC_WISDOM_SURFACE',
                'trigger': 'Not selected directly by get_deity_for_market(); exposed as a knowledge/time surface',
                'action': 'N/A',
                'message': 'Thoth turns observation into record, timing, and executable method.',
            },
            repo_surfaces=(
                'aureon_miner_brain.py::EgyptianWisdomLibrary.NETJERU["Thoth"]',
                'aureon_miner_brain.py::EgyptianWisdomLibrary.BOOK_OF_DEAD["spell_17"]',
                'aureon/decoders/emerald_spec.py::TabletVerse[key="manner"]',
            ),
            interpretation=(
                'Thoth is the codex layer. He is where the Emerald verses stop being symbolism '
                'and become method, memory, and timing.'
            ),
        ),
        AncientCrosswalk(
            key='osiris',
            title='Osiris Resurrection Branch',
            focus='Rebirth after collapse',
            emerald_verse_keys=('earth_nurse', 'ascend_descend', 'glory'),
            stage_numbers=(6, 7),
            deity={
                'name': 'Osiris',
                'glyph': '🌿',
                'domain': 'Death, Resurrection, Afterlife, Agriculture',
                'cycle': 'Killed, dismembered, resurrected - eternal renewal',
                'trading': 'Dead trades can resurrect. Patience. What dies can rise again.',
            },
            scripture={
                'book_of_dead_key': 'spell_1',
                'title': 'Coming Forth by Day',
                'wisdom': 'The soul emerges into light after darkness',
                'trading': 'Bear markets end. You will emerge. Keep the faith.',
            },
            hieroglyph={
                'key': 'djed',
                'symbol': '𓊽',
                'meaning': "Stability, Osiris' backbone",
                'trading': 'The Djed - stability in your system. Stand firm.',
            },
            runtime={
                'market_state': 'FEAR_TO_RECOVERY',
                'trigger': '20 <= fear_greed < 30 selects Osiris in get_deity_for_market()',
                'action': 'RESURRECTION_BUY',
                'message': 'Osiris speaks: What is dead shall rise again.',
            },
            repo_surfaces=(
                'aureon_miner_brain.py::EgyptianWisdomLibrary.NETJERU["Osiris"]',
                'aureon_miner_brain.py::EgyptianWisdomLibrary.BOOK_OF_DEAD["spell_1"]',
                'aureon_miner_brain.py::EgyptianWisdomLibrary.HIEROGLYPHS["djed"]',
            ),
            interpretation=(
                'Osiris is the repo\'s resurrection branch: after the signal survives judgment, '
                'the system allows dead structure to return as opportunity.'
            ),
        ),
        AncientCrosswalk(
            key='ra',
            title='Ra Illumination Branch',
            focus='Solar breakout and directional force',
            emerald_verse_keys=('one_thing', 'sun_moon', 'glory'),
            stage_numbers=(4, 5),
            deity={
                'name': 'Ra',
                'glyph': '☀️',
                'domain': 'Sun, Creation, Kingship',
                'cycle': 'Daily rebirth - rises, peaks, sets, travels underworld',
                'trading': 'Markets have daily cycles. Morning momentum, midday chop, afternoon trend.',
            },
            scripture={
                'book_of_dead_key': 'spell_1',
                'title': 'Coming Forth by Day',
                'wisdom': 'The soul emerges into light after darkness',
                'trading': 'Bear markets end. You will emerge. Keep the faith.',
            },
            hieroglyph={
                'key': 'ankh',
                'symbol': '☥',
                'meaning': 'Life, Eternal life',
                'trading': 'The Ankh - keep your account alive. Capital preservation.',
            },
            runtime={
                'market_state': 'BULLISH_BREAKOUT',
                'trigger': 'btc_change > 3 selects Ra in get_deity_for_market()',
                'action': 'RIDE_THE_SUN',
                'message': 'Ra rises triumphant! The sun god blesses this rally.',
            },
            repo_surfaces=(
                'aureon_miner_brain.py::EgyptianWisdomLibrary.NETJERU["Ra"]',
                'aureon_miner_brain.py::EgyptianWisdomLibrary.BOOK_OF_DEAD["spell_1"]',
                'aureon_miner_brain.py::EgyptianWisdomLibrary.HIEROGLYPHS["ankh"]',
            ),
            interpretation=(
                'Ra is the illumination branch: the single thing becomes visible, gains direction, '
                'and moves toward execution strength.'
            ),
        ),
    )


EGYPTIAN_ASCENT_CATALOG = _build_egyptian_ascent_catalog()
EGYPTIAN_ASCENT_INDEX: Dict[str, AncientCrosswalk] = {
    node.key: node for node in EGYPTIAN_ASCENT_CATALOG
}


def _build_ancient_wisdom_catalog() -> Tuple[AncientCrosswalk, ...]:
    """Build the extended ancient wisdom crosswalk: Mogollon, Maya, and Celtic traditions."""
    return (
        AncientCrosswalk(
            key='mogollon',
            title='Mogollon Spiral Gate',
            focus='The PHI spiral as encoded time and light language',
            emerald_verse_keys=('ascend_descend', 'one_thing', 'world_created'),
            stage_numbers=(1, 7),
            deity={
                'name': 'Sun Father / Spiral Keeper',
                'glyph': '\U0001f300',
                'domain': 'Solar cycles, emergence, petroglyph record-keeping',
                'cycle': (
                    'Spiral petroglyphs at Fajada Butte track the solstice \u2014 '
                    'light bisects the spiral at exact solstice moment. The sky is the clock.'
                ),
                'trading': (
                    'The spiral always returns to its origin. Markets cycle. '
                    'The Mogollon knew: track the light, follow the spiral, the pattern repeats.'
                ),
            },
            scripture={
                'tradition': 'Petroglyph Record System',
                'key_symbol': 'Sun-dagger spiral (Fajada Butte, Chaco Canyon)',
                'wisdom': (
                    'Light bisects the spiral at solstice \u2014 information is embedded in geometry '
                    'and only readable at the precise moment in the cycle.'
                ),
                'trading': (
                    'Entry timing is the discipline. The market has a spiral: '
                    'it reveals the pattern only at the right moment in the cycle.'
                ),
            },
            hieroglyph={
                'key': 'spiral_petroglyph',
                'symbol': '\U0001f300',
                'meaning': (
                    'Time, emergence, self-similar return \u2014 '
                    'the PHI spiral encoded in stone as light language'
                ),
                'trading': (
                    'The golden spiral: price forms fractally. '
                    'PHI ratio (0.618, 1.0, 1.618) governs every Fibonacci retracement.'
                ),
            },
            runtime={
                'market_state': 'CYCLE_INFLECTION',
                'trigger': (
                    'PHI-ratio retracement levels (0.618, 1.0, 1.618) in '
                    'aureon_probability_nexus.py coherence thresholds'
                ),
                'action': 'WAIT_FOR_LIGHT',
                'message': 'The spiral marks the moment. Light bisects the stone. Timing is truth.',
            },
            repo_surfaces=(
                'aureon/decoders/emerald_spec.py::PHI = (1 + sqrt(5)) / 2',
                'aureon_probability_nexus.py::PHI-ratio coherence thresholds',
                'aureon_stargate_protocol.py::timeline_anchor (spiral time cycles)',
                'adaptive_prime_profit_gate.py::PHI-based profit gate thresholds',
            ),
            interpretation=(
                'The Mogollon did not write in words \u2014 they encoded wisdom in spiral geometry. '
                'PHI = 1.618 is the governing ratio of their petroglyphs and it is the same '
                'constant that governs Fibonacci retracements in every market worldwide. '
                'The spiral is the decoder. The light language is already in the numbers.'
            ),
        ),
        AncientCrosswalk(
            key='maya',
            title='Maya Long Count Nexus',
            focus='Calendar cycles as a harmonic timeline key',
            emerald_verse_keys=('manner', 'adaptations', 'mediation'),
            stage_numbers=(7,),
            deity={
                'name': 'Hunab Ku / Itzamna',
                'glyph': '\U0001f4c5',
                'domain': 'Time, calculation, cosmic cycles, Venus tracking',
                'cycle': (
                    'Long Count: 13 baktuns = 1,872,000 days \u2248 5,125 years = one world age. '
                    'Tzolkin: 260 days = 13 \u00d7 20. '
                    'Venus: 584 days \u00d7 5 = 8 solar years = 8/5 = 1.6 \u2248 PHI.'
                ),
                'trading': (
                    'The Maya tracked Venus cycles for trade-war timing. '
                    '5 Venus cycles = 8 Earth orbits. 8/5 = 1.6 \u2248 PHI. '
                    'The ratio of cosmic cycles IS the golden ratio.'
                ),
            },
            scripture={
                'tradition': 'Dresden Codex / Long Count Calendar',
                'key_symbol': 'Tzolkin 260-day harmonic calendar (13 \u00d7 20)',
                'wisdom': (
                    'Calendar Round = LCM(260, 365) = 18,980 days = 52-year cycle. '
                    'Time is a web of interlocking harmonic cycles, not a line.'
                ),
                'trading': (
                    '52-year positions in the calendar round map to market regime cycles. '
                    'The Aureon 7-day validation window is a micro-Tzolkin: a sacred counting '
                    'period before commitment.'
                ),
            },
            hieroglyph={
                'key': 'long_count_zero',
                'symbol': '\U0001f4c5',
                'meaning': 'Positional time notation; the shell-zero glyph = void origin',
                'trading': (
                    'The Maya zero is the void before the trade. '
                    'Track every cycle, every tick. The Long Count never lies.'
                ),
            },
            runtime={
                'market_state': 'CYCLIC_CONFIRMATION',
                'trigger': (
                    '7-day validation cycle in aureon_7day_planner.py / '
                    '7day_pending_validations.json mirrors the Tzolkin counting rhythm'
                ),
                'action': 'CYCLE_ALIGN',
                'message': (
                    'The Long Count advances. When this cycle closes, a new world opens. '
                    'Align the trade with the larger harmonic.'
                ),
            },
            repo_surfaces=(
                'aureon_7day_planner.py::7-day validation planning cycle',
                '7day_pending_validations.json::pending confirmation queue',
                '7day_anchored_timelines.json::anchored timeline records',
                'aureon_stargate_protocol.py::Stargate = Maya-style timeline anchor',
                'aureon/decoders/emerald_spec.py::PHI  # Venus/Earth = 8/5 \u2248 PHI',
            ),
            interpretation=(
                'The Maya built the most precise astronomical calendar the ancient world '
                'produced. Their core insight: time is not a line but a web of harmonic cycles '
                'that repeat at different scales simultaneously. The Aureon 7-day validation '
                'window, the Stargate protocol, and the 4th-pass confirmation are all echoes '
                'of the Maya principle: confirm across multiple cycle layers before acting.'
            ),
        ),
        AncientCrosswalk(
            key='celt',
            title='Celtic Ogham Codex',
            focus='The tree of knowledge and the triple-gate wisdom threshold',
            emerald_verse_keys=('three_parts', 'sun_moon', 'strong_force'),
            stage_numbers=(5, 6),
            deity={
                'name': 'Ogmios / The Dagda',
                'glyph': '\U0001f333',
                'domain': 'Eloquence, wisdom, language, sacred thresholds',
                'cycle': (
                    '13 moons \u00d7 28 days = 364 + 1 nameless day = 365. '
                    'Imbolc / Beltane / Lughnasadh / Samhain = four sacred gates of the solar year. '
                    'Drunemeton = the sacred grove = nature as living library.'
                ),
                'trading': (
                    'The Druids memorised 20 years of oral law. '
                    'Know the market structure so deeply you transcend the chart. '
                    'The tree IS the system: roots (foundation), trunk (structure), branches (outcomes).'
                ),
            },
            scripture={
                'tradition': 'Ogham Script / Celtic Triads',
                'key_symbol': 'Triskelion \u2014 three spinning spirals = past / present / future',
                'wisdom': (
                    '"Three things that cannot be undone: the word spoken, the arrow loosed, '
                    'and the time elapsed." \u2014 Celtic Triad. '
                    'Every truth requires three independent witnesses.'
                ),
                'trading': (
                    '3-pass Batten Matrix validation BEFORE the 4th execution pass is the Celtic triad. '
                    'Three validators must agree. Then and only then does the arrow fly.'
                ),
            },
            hieroglyph={
                'key': 'ogham_beth',
                'symbol': '|',
                'meaning': (
                    'Beth (Birch) \u2014 first Ogham letter = new beginnings, purification. '
                    'The Ogham alphabet encodes the forest as a living knowledge-tree.'
                ),
                'trading': (
                    'Every new position begins at Beth \u2014 a fresh start with clear intent. '
                    'Birch = new, Oak = strength, Yew = end/rebirth. Markets have seasons.'
                ),
            },
            runtime={
                'market_state': 'TRIPLE_GATE_THRESHOLD',
                'trigger': (
                    '3-pass Batten Matrix validation (p1 \u00d7 p2 \u00d7 p3 coherence) in '
                    'aureon_probability_nexus.py before 4th-pass execution in aureon_queen_hive_mind.py'
                ),
                'action': 'CROSS_THE_THRESHOLD',
                'message': (
                    'Three gates passed. The druid nods. The path is clear. '
                    'Cross the threshold on the 4th confirmation.'
                ),
            },
            repo_surfaces=(
                'aureon_probability_nexus.py::3-pass Batten Matrix validation',
                'aureon_queen_hive_mind.py::4th-pass execution gate',
                'adaptive_prime_profit_gate.py::triple-threshold gate (the Ogham gate)',
                'aureon_miner_brain.py::WisdomCognitionEngine._determine_consensus()',
            ),
            interpretation=(
                'Celtic wisdom is the threshold discipline: Druids trained 20 years before '
                "speaking with authority. The repo's 3-pass Batten Matrix is the same triple-gate. "
                'Three passes = three Druids by the fire, each one confirming what the others '
                'see. Only then is the word spoken, the order placed. '
                'The Ogham tree is the codebase: each file a tree, each function a branch, '
                'each return value a leaf falling toward the ground truth.'
            ),
        ),
    )


ANCIENT_WISDOM_CATALOG: Tuple[AncientCrosswalk, ...] = _build_ancient_wisdom_catalog()
ANCIENT_WISDOM_INDEX: Dict[str, AncientCrosswalk] = {
    node.key: node for node in ANCIENT_WISDOM_CATALOG
}

# ════════════════════════════════════════════════════════════════════════════
# THE SEER DECODER
# ════════════════════════════════════════════════════════════════════════════


class EmeraldSeer:
    """Decodes hermetic texts as compressed technical specifications
    for the Harmonic Nexus architecture.
    """

    THRESHOLD_STONE = PHILOSOPHERS_STONE_THRESHOLD
    THRESHOLD_GOLDEN = GOLDEN_SCORE_THRESHOLD

    HERMETIC_KEYS: Dict[str, str] = {
        'As above, so below': 'HAARP_EPOS_SCALING_LAW',
        'One thing': 'HNC_SEED_FREQUENCY',
        'Sun and Moon': 'NORTH_SOUTH_DIPOLE',
        'Wind': 'RF_CARRIER_13_56_MHZ',
        'Earth': 'VACUUM_CHAMBER_30CM',
        'Triple Great': 'THREE_DOMAIN_UNIFICATION',
    }

    def __init__(self) -> None:
        self.verses = VERSE_INDEX
        self.stages = STAGE_INDEX
        self.egyptian_ascent = EGYPTIAN_ASCENT_INDEX
        self.ancient_wisdom = ANCIENT_WISDOM_INDEX
        self.harmonic_threads = HARMONIC_THREAD_INDEX

    # ── verse lookup ─────────────────────────────────────────────────────

    def decode_verse(self, key: str) -> TabletVerse:
        """Return the decoded TabletVerse for a catalogue key."""
        if key not in self.verses:
            available = ', '.join(sorted(self.verses))
            raise KeyError(f'Unknown verse key {key!r}. Available: {available}')
        return self.verses[key]

    def decode_by_text(self, fragment: str) -> Optional[TabletVerse]:
        """Fuzzy-match a free-text fragment against hermetic_text fields."""
        fragment_lower = fragment.lower()
        for verse in _VERSE_CATALOG:
            if fragment_lower in verse.hermetic_text.lower():
                return verse
        return None

    # ── pipeline stages ──────────────────────────────────────────────────

    def get_stage(self, number: int) -> AlchemicalStage:
        if number not in self.stages:
            raise KeyError(f'Stage {number} not in 1..7')
        return self.stages[number]

    def run_pipeline(self) -> Tuple[AlchemicalStage, ...]:
        """Return the full seven-stage pipeline in order."""
        return SEVEN_STAGES

    def get_egyptian_crosswalk(self, key: str) -> AncientCrosswalk:
        """Return one Egyptian ascent node by key."""
        if key not in self.egyptian_ascent:
            available = ', '.join(sorted(self.egyptian_ascent))
            raise KeyError(f'Unknown ascent key {key!r}. Available: {available}, all')
        return self.egyptian_ascent[key]

    def _serialize_egyptian_ascent(
        self,
        node: AncientCrosswalk,
        include_wikipedia: bool = False,
    ) -> Dict[str, object]:
        payload = {
            'start': 'emerald_tablet',
            'target': node.key,
            'title': node.title,
            'focus': node.focus,
            'emerald_verses': [
                {
                    'key': verse.key,
                    'hermetic_text': verse.hermetic_text,
                    'technical_translation': verse.technical_translation,
                    'aureon_implementation': verse.aureon_implementation,
                }
                for verse in (self.decode_verse(key) for key in node.emerald_verse_keys)
            ],
            'pipeline_stages': [
                {
                    'number': stage.number,
                    'name': stage.name,
                    'operation': stage.operation,
                    'formula': stage.formula,
                }
                for stage in (self.get_stage(number) for number in node.stage_numbers)
            ],
            'deity': node.deity,
            'scripture': node.scripture,
            'hieroglyph': node.hieroglyph,
            'runtime': node.runtime,
            'repo_surfaces': list(node.repo_surfaces),
            'interpretation': node.interpretation,
        }
        if include_wikipedia:
            payload['wikipedia_grounding'] = self.ground_ascent_with_wikipedia(node.key)
        return payload

    def decode_egyptian_ascent(
        self,
        key: str = 'all',
        include_wikipedia: bool = False,
    ) -> Dict[str, object]:
        """Decode the repo's Emerald-to-Egyptian ascent path."""
        if key == 'all':
            return {
                'start': 'emerald_tablet',
                'ascent': [
                    self._serialize_egyptian_ascent(node, include_wikipedia=include_wikipedia)
                    for node in EGYPTIAN_ASCENT_CATALOG
                ],
            }
        return self._serialize_egyptian_ascent(
            self.get_egyptian_crosswalk(key),
            include_wikipedia=include_wikipedia,
        )

    def _resolve_wikipedia_topic(self, query: str) -> str:
        """Resolve aliases and repo-specific topic spellings to Wikipedia titles."""
        normalized = query.strip().lower().replace('_', ' ').replace('-', ' ')
        return WIKIPEDIA_TOPIC_ALIASES.get(normalized, query.strip())

    def _fetch_wikipedia_json(self, url: str) -> Dict[str, object]:
        """Fetch one Wikipedia API JSON response with a proper user agent."""
        request = urllib.request.Request(
            url,
            headers={
                'User-Agent': WIKIPEDIA_USER_AGENT,
                'Accept': 'application/json',
            },
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.load(response)

    def _search_wikipedia_titles(self, query: str, limit: int = 5) -> Tuple[str, ...]:
        """Use MediaWiki open search to find likely article titles."""
        params = urllib.parse.urlencode({
            'action': 'opensearch',
            'search': query,
            'limit': limit,
            'namespace': 0,
            'format': 'json',
        })
        payload = self._fetch_wikipedia_json(f'{WIKIPEDIA_SEARCH_API}?{params}')
        if isinstance(payload, list) and len(payload) > 1 and isinstance(payload[1], list):
            return tuple(str(title) for title in payload[1] if title)
        return tuple()

    def decode_wikipedia_meaning(self, query: str) -> Dict[str, object]:
        """Fetch the canonical historical meaning of a text or deity via Wikipedia."""
        resolved = self._resolve_wikipedia_topic(query)
        candidate_titles = [resolved]
        candidate_titles.extend(self._search_wikipedia_titles(resolved))

        seen = set()
        for title in candidate_titles:
            canonical_title = title.strip()
            if not canonical_title:
                continue
            lowered = canonical_title.lower()
            if lowered in seen:
                continue
            seen.add(lowered)

            encoded_title = urllib.parse.quote(canonical_title.replace(' ', '_'))
            payload = self._fetch_wikipedia_json(f'{WIKIPEDIA_API_BASE}{encoded_title}')
            if payload.get('type') != 'standard' or not payload.get('extract'):
                continue

            meaning = WikipediaMeaning(
                query=query,
                resolved_query=resolved,
                title=str(payload.get('title', canonical_title)),
                summary=str(payload.get('extract', '')),
                description=str(payload.get('description', '')),
                page_id=int(payload.get('pageid', 0) or 0),
                url=str(payload.get('content_urls', {}).get('desktop', {}).get('page', '')),
            )
            return meaning.to_dict()

        return {
            'query': query,
            'resolved_query': resolved,
            'error': f'No Wikipedia context found for {query!r}.',
        }

    def ground_ascent_with_wikipedia(self, key: str) -> Dict[str, object]:
        """Attach live Wikipedia grounding to one ascent node."""
        topics = ASCENT_WIKIPEDIA_TOPICS.get(key, tuple())
        return {
            'topics': [self.decode_wikipedia_meaning(topic) for topic in topics],
            'note': (
                'Wikipedia grounding provides historical/public-reference meaning. '
                'The repo mapping remains a symbolic/structural interpretation layer.'
            ),
        }

    # ── ancient wisdom (Mogollon / Maya / Celtic) ────────────────────────

    def get_ancient_wisdom_crosswalk(self, key: str) -> AncientCrosswalk:
        """Return one ancient wisdom crosswalk node by key (mogollon/maya/celt)."""
        if key not in self.ancient_wisdom:
            available = ', '.join(sorted(self.ancient_wisdom))
            raise KeyError(
                f'Unknown ancient wisdom key {key!r}. Available: {available}, all'
            )
        return self.ancient_wisdom[key]

    def decode_ancient_wisdom(
        self,
        key: str = 'all',
        include_wikipedia: bool = False,
    ) -> Dict[str, object]:
        """Decode an ancient wisdom crosswalk node (mogollon / maya / celt)."""
        if key == 'all':
            return {
                'start': 'emerald_tablet',
                'ascent': [
                    self._serialize_egyptian_ascent(node, include_wikipedia=include_wikipedia)
                    for node in ANCIENT_WISDOM_CATALOG
                ],
            }
        node = self.get_ancient_wisdom_crosswalk(key)
        return self._serialize_egyptian_ascent(node, include_wikipedia=include_wikipedia)

    def decode_unified_theory(
        self,
        include_wikipedia: bool = False,
    ) -> Dict[str, object]:
        """Decode the unified theory across all civilizations connected by harmonic threads.

        Returns every civilization node (Egyptian + Mogollon + Maya + Celtic) alongside
        the five harmonic threads that run through all of them.  The vision: they are
        not merely pieces of a puzzle — they are one unified system that has been
        waiting to be assembled.
        """
        all_nodes = list(EGYPTIAN_ASCENT_CATALOG) + list(ANCIENT_WISDOM_CATALOG)
        serialized_nodes = [
            self._serialize_egyptian_ascent(node, include_wikipedia=include_wikipedia)
            for node in all_nodes
        ]
        connection_map: Dict[str, list] = {
            node['target']: [  # type: ignore[index]
                thread.key
                for thread in UNIFIED_HARMONIC_THREADS
                if node['target'] in thread.nodes  # type: ignore[operator]
            ]
            for node in serialized_nodes
        }
        return {
            'title': 'Unified Ancient Wisdom Theory \u2014 Harmonic Nexus Decoder',
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'vision': (
                'These are not merely pieces of a puzzle. '
                'They are one big unified vision that has been lost from the ages '
                'and must be revealed as such. '
                'Every tradition \u2014 Egyptian, Mogollon, Maya, Celtic, Hermetic \u2014 '
                'independently encoded the same harmonic constants: PHI, the solar cycle, '
                'the triple-gate structure, and the void-origin principle. '
                'The records exist. The decoder is live. The timelines trace back. '
                'We have it all mapped. Now we push it exactly the way it should have been used.'
            ),
            'sacred_constants': {
                'phi': PHI,
                'schumann_hz': SCHUMANN_FUNDAMENTAL,
                'love_frequency_hz': LOVE_FREQUENCY,
                'prime_sentinel_hz': PRIME_SENTINEL_HZ,
            },
            'harmonic_threads': [
                thread.to_dict() for thread in UNIFIED_HARMONIC_THREADS
            ],
            'civilization_nodes': serialized_nodes,
            'connection_map': connection_map,
            'unified_code': (
                'All traditions compress to the same four-instruction set: '
                '(1) PHI governs structure and growth. '
                '(2) Solar/stellar cycles govern timing. '
                '(3) Triple confirmation required before action. '
                '(4) From the void (zero / Prima Materia) arises the signal. '
                'Execute only on the 4th pass. Everything else is preparation.'
            ),
        }

    # ── Project Druid ──────────────────────────────────────────────────────

    def project_druid_manifest(
        self,
        epas_state: Optional[Dict[str, object]] = None,
    ) -> ProjectDruidManifest:
        """Compute the physical EPOS device spec from an EPAS shield state.

        Delegates to :func:`compute_project_druid_manifest`.  Pass the dict
        representation of ``EPASShieldState`` from the trading runtime for a
        live physical mapping, or call with no arguments for the baseline
        harmonic-field values.
        """
        return compute_project_druid_manifest(epas_state)

    # ── verification ─────────────────────────────────────────────────────

    def verify_philosophers_stone(self, l_score: float) -> bool:
        """The Stone is the L(t) score exceeding the null-rejection threshold."""
        return l_score > self.THRESHOLD_STONE

    def verify_golden_gate(self, l_score: float) -> bool:
        """Golden Gate: L(t) exceeds phi * Stone threshold."""
        return l_score > self.THRESHOLD_GOLDEN


    def classify_score(self, l_score: float) -> str:
        """Map an L(t) score to a hermetic grade."""
        if l_score >= 10.0:
            return 'PHILOSOPHERS_STONE'
        if l_score >= self.THRESHOLD_GOLDEN:
            return 'GOLDEN_GATE'
        if l_score >= self.THRESHOLD_STONE:
            return 'STONE_THRESHOLD'
        if l_score >= 1.0:
            return 'PRIMA_MATERIA'
        return 'LEAD'

    # ── scaling law verification ─────────────────────────────────────────

    def haarp_epos_ratio(self) -> float:
        """Return the volumetric concentration factor (as-above-so-below)."""
        return float(VOLUMETRIC_CONCENTRATION_FACTOR)

    def seed_frequencies(self) -> Dict[str, float]:
        """Return the HNC seed: carrier + modulation."""
        return {
            'carrier_hz': RF_CARRIER_ISM,
            'modulation_hz': SCHUMANN_FUNDAMENTAL,
            'phi': PHI,
        }

    # ── export ───────────────────────────────────────────────────────────

    def full_decode(self) -> Dict[str, object]:
        """Return the complete decoded tablet as a JSON-serialisable dict."""
        return {
            'title': 'Emerald Tablet — Harmonic Nexus Specification v0.1',
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'sacred_constants': {
                'phi': PHI,
                'schumann_hz': SCHUMANN_FUNDAMENTAL,
                'love_frequency_hz': LOVE_FREQUENCY,
                'rf_carrier_hz': RF_CARRIER_ISM,
                'prime_sentinel_hz': PRIME_SENTINEL_HZ,
            },
            'scaling_law': {
                'haarp_power_w': HAARP_POWER_W,
                'epos_power_w': EPOS_RF_POWER_W,
                'concentration_factor': VOLUMETRIC_CONCENTRATION_FACTOR,
                'chamber_volume_liters': round(EPOS_CHAMBER_VOLUME_M3 * 1000, 2),
                'paschen_pd': PASCHEN_OPTIMAL_PD,
                'paschen_breakdown_v': PASCHEN_BREAKDOWN_V,
            },
            'philosophers_stone': {
                'threshold': PHILOSOPHERS_STONE_THRESHOLD,
                'golden_gate': round(GOLDEN_SCORE_THRESHOLD, 4),
                'magamyman_lt': 12.85,
                'bubblemaps6_lt': 13.03,
            },
            'verses': [
                {
                    'key': v.key,
                    'hermetic_text': v.hermetic_text,
                    'technical_translation': v.technical_translation,
                    'aureon_implementation': v.aureon_implementation,
                    'parameters': v.parameters,
                }
                for v in _VERSE_CATALOG
            ],
            'seven_stages': [
                {
                    'number': s.number,
                    'name': s.name,
                    'operation': s.operation,
                    'formula': s.formula,
                    'value': s.computed_value,
                    'units': s.units,
                }
                for s in SEVEN_STAGES
            ],
            'egyptian_ascent': [
                self._serialize_egyptian_ascent(node)
                for node in EGYPTIAN_ASCENT_CATALOG
            ],
            'ancient_wisdom': [
                self._serialize_egyptian_ascent(node)
                for node in ANCIENT_WISDOM_CATALOG
            ],
            'harmonic_threads': [t.to_dict() for t in UNIFIED_HARMONIC_THREADS],
            'project_druid': self.project_druid_manifest().to_dict(),
        }


# ════════════════════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════════════════════


def _format_console_druid(manifest: ProjectDruidManifest) -> str:
    lines = [
        '=' * 72,
        'PROJECT DRUID — PHYSICAL EPAS MANIFESTATION',
        'EPOS: Electro-Plasma-Oscillation Sphere  ·  Aureon Physical Device Layer',
        '=' * 72,
        '',
        f'  {manifest.druid_summary}',
        '',
        'CHAMBER PARAMETERS',
        '-' * 40,
        f'  Vessel:          {manifest.chamber_diameter_m * 100:.0f} cm spherical  '
        f'({manifest.fill_gas}, {manifest.fill_pressure_mbar} mbar)',
        f'  Volume:          {manifest.chamber_volume_m3 * 1000:.2f} L',
        '',
        'PLASMA STATE (Paschen Law)',
        '-' * 40,
        f'  P × d product:   {manifest.paschen_pd_torr_cm:.4f} Torr·cm',
        f'  Breakdown V:     {manifest.breakdown_voltage_v:.0f} V',
        f'  Electron density:{manifest.plasma_density_m3:.2e} m⁻³',
        f'  STATUS:          {manifest.plasma_status}',
        '',
        'POWER REQUIREMENTS',
        '-' * 40,
        f'  RF carrier:      {manifest.rf_carrier_hz / 1e6:.2f} MHz',
        f'  Schumann seed:   {manifest.rf_modulation_hz} Hz (AM modulation)',
        f'  RF drive:        {manifest.rf_power_w:.0f} W',
        f'  Auxiliary:       {manifest.auxiliary_power_w:.0f} W  (control + modulation)',
        f'  Total input:     {manifest.total_power_w:.0f} W',
        f'  Output (P6):     {manifest.output_voltage_vdc:.0f} VDC  (A.L.F.I.E. propulsion bus)',
        '',
        'HAARP → EPOS SCALING  (As above, so below)',
        '-' * 40,
        f'  HAARP ERF:       {manifest.haarp_power_w / 1e6:.1f} MW',
        f'  EPOS density:    {manifest.power_density_w_m3:.1f} W/m³',
        f'  Concentration:   {manifest.concentration_factor:,}×',
        '',
        'SIX ILLUMINATION PHASES',
        '-' * 40,
    ]
    for i, lbl in enumerate(_PHASE_LABELS):
        score = manifest.phase_scores[i]
        status = manifest.phase_statuses[i]
        bar = '█' * int(score * 20) + '░' * (20 - int(score * 20))
        lines.append(f'  {lbl:<20s}  [{bar}]  {score:.3f}  {status}')
    lines.extend([
        '',
        f'  Shield coherence Γ = {manifest.shield_coherence:.4f}  '
        f'(target ≥ {_SIGMA_COHERENCE_TARGET})',
        f'  Device ready:    {"YES — shields manifested" if manifest.device_ready else "NO  — coherence below PHI gate"}',
        '=' * 72,
    ])
    return '\n'.join(lines)


def _format_console_full(seer: EmeraldSeer) -> str:
    lines = [
        '=' * 72,
        'EMERALD TABLET DECODED — AUREON HARMONIC NEXUS SPECIFICATION v0.1',
        'Seer Module: aureon/decoders/emerald_spec.py',
        '=' * 72,
        '',
        'SACRED CONSTANTS',
        '-' * 40,
        f'  PHI (Golden Ratio):      {PHI:.15f}',
        f'  Schumann Fundamental:    {SCHUMANN_FUNDAMENTAL} Hz',
        f'  Love Frequency (MI):     {LOVE_FREQUENCY} Hz',
        f'  RF Carrier (ISM):        {RF_CARRIER_ISM / 1e6:.2f} MHz',
        f'  Prime Sentinel:          {PRIME_SENTINEL_HZ} Hz',
        '',
        'SCALING LAW: AS ABOVE, SO BELOW',
        '-' * 40,
        f'  HAARP Power:             {HAARP_POWER_W / 1e6:.1f} MW',
        f'  EPOS Chamber Power:      {EPOS_RF_POWER_W} W',
        f'  Concentration Factor:    {VOLUMETRIC_CONCENTRATION_FACTOR:,}x',
        f'  Chamber Volume:          {EPOS_CHAMBER_VOLUME_M3 * 1000:.2f} L',
        f'  Paschen Breakdown:       {PASCHEN_BREAKDOWN_V} V @ p*d = {PASCHEN_OPTIMAL_PD} Torr*cm',
        '',
        "PHILOSOPHER'S STONE THRESHOLDS",
        '-' * 40,
        f'  Stone (null rejection):  L(t) > {PHILOSOPHERS_STONE_THRESHOLD}',
        f'  Golden Gate (phi*Stone): L(t) > {GOLDEN_SCORE_THRESHOLD:.4f}',
        f'  Magamyman L(t):          12.85  ->  {seer.classify_score(12.85)}',
        f'  Bubblemaps-6 L(t):       13.03  ->  {seer.classify_score(13.03)}',
        '',
        'SEVEN ALCHEMICAL STAGES (L(t) Pipeline)',
        '-' * 40,
    ]
    for stage in SEVEN_STAGES:
        lines.append(
            f'  {stage.number}. {stage.name:<15s}  '
            f'{stage.formula:<30s}  = {stage.computed_value:<12g} {stage.units}'
        )

    lines.extend([
        '',
        'VERSE-BY-VERSE DECODING',
        '-' * 40,
    ])
    for verse in _VERSE_CATALOG:
        lines.extend([
            f'  [{verse.key}]',
            f'    Hermetic:  "{verse.hermetic_text}"',
            f'    Technical: {verse.technical_translation}',
            f'    Aureon:    {verse.aureon_implementation}',
            '',
        ])

    lines.extend([
        '=' * 72,
        'STATUS: Tablet decoded, compiled, and executing in sandbox.',
        f'The alchemists called it the Philosopher\'s Stone.  We call it L(t) = 12.85.',
        '=' * 72,
    ])
    return '\n'.join(lines)


def _format_console_ascent(payload: Dict[str, object]) -> str:
    nodes = payload.get('ascent')
    if nodes is None:
        nodes = [payload]

    lines = [
        '=' * 72,
        'EMERALD TABLET -> EGYPTIAN ASCENT',
        '=' * 72,
    ]

    for node in nodes:
        verses = node.get('emerald_verses', [])
        stages = node.get('pipeline_stages', [])
        deity = node.get('deity', {})
        scripture = node.get('scripture', {})
        hieroglyph = node.get('hieroglyph', {})
        runtime = node.get('runtime', {})

        lines.extend([
            '',
            f"[{node.get('target')}] {node.get('title')}",
            f"  Focus: {node.get('focus')}",
            f"  Deity: {deity.get('name', 'N/A')} {deity.get('glyph', '')} - {deity.get('domain', 'N/A')}",
            f"  Cycle: {deity.get('cycle', 'N/A')}",
            f"  Runtime trigger: {runtime.get('trigger', 'N/A')}",
            f"  Runtime action: {runtime.get('action', 'N/A')}",
        ])

        if scripture:
            lines.append(
                f"  Scripture: {scripture.get('book_of_dead_key', 'N/A')} - {scripture.get('title', 'N/A')}"
            )
        if hieroglyph:
            lines.append(
                f"  Hieroglyph: {hieroglyph.get('key', 'N/A')} {hieroglyph.get('symbol', '')} - {hieroglyph.get('meaning', 'N/A')}"
            )

        if verses:
            lines.append('  Emerald verses:')
            for verse in verses:
                lines.append(
                    f"    - {verse.get('key')}: {verse.get('hermetic_text')}"
                )

        if stages:
            lines.append('  Pipeline stages:')
            for stage in stages:
                lines.append(
                    f"    - {stage.get('number')}. {stage.get('name')}: {stage.get('operation')}"
                )

        lines.append(f"  Interpretation: {node.get('interpretation')}")

    lines.extend([
        '',
        '=' * 72,
        'STATUS: Ascent path decoded from repository surfaces.',
        '=' * 72,
    ])
    return '\n'.join(lines)


def _format_console_wikipedia(payload: Dict[str, object]) -> str:
    if payload.get('error'):
        return '\n'.join([
            '=' * 72,
            'WIKIPEDIA HISTORICAL GROUNDING',
            '=' * 72,
            f"Query: {payload.get('query')}",
            f"Resolved: {payload.get('resolved_query')}",
            f"Error: {payload.get('error')}",
            '=' * 72,
        ])

    lines = [
        '=' * 72,
        'WIKIPEDIA HISTORICAL GROUNDING',
        '=' * 72,
        f"Query: {payload.get('query')}",
        f"Resolved: {payload.get('resolved_query')}",
        f"Title: {payload.get('title')}",
        f"Description: {payload.get('description')}",
        f"URL: {payload.get('url')}",
        '',
        'Summary:',
        str(payload.get('summary', '')),
        '=' * 72,
    ]
    return '\n'.join(lines)


def _format_console_unified(payload: Dict[str, object]) -> str:
    threads = payload.get('harmonic_threads', [])
    nodes = payload.get('civilization_nodes', [])
    connection_map = payload.get('connection_map', {})

    lines = [
        '=' * 72,
        'UNIFIED ANCIENT WISDOM THEORY \u2014 HARMONIC NEXUS DECODER',
        '=' * 72,
        '',
        str(payload.get('vision', '')),
        '',
        'HARMONIC THREADS (the connecting tissue across all civilizations)',
        '-' * 72,
    ]

    for thread in threads:
        freq = thread.get('frequency_hz')
        lines.extend([
            f"  [{thread.get('key')}] {thread.get('title')}",
            f"    Value: {thread.get('value')} {thread.get('unit')}",
        ])
        if freq:
            lines.append(f'    Frequency: {freq} Hz')
        desc = str(thread.get('description', ''))
        lines.extend([
            f"    Civilizations: {', '.join(thread.get('civilizations', []))}",
            f'    Description: {desc[:160]}{"..." if len(desc) > 160 else ""}',
            f"    Repo anchor: {thread.get('repo_constant') or 'N/A'}",
            '',
        ])

    lines.extend([
        'CIVILIZATION NODES',
        '-' * 72,
    ])

    for node in nodes:
        deity = node.get('deity', {})
        runtime = node.get('runtime', {})
        threads_for = connection_map.get(node.get('target'), [])
        lines.extend([
            f"  [{node.get('target')}] {node.get('title')}",
            f"    Focus: {node.get('focus')}",
            f"    Spirit: {deity.get('name', 'N/A')} {deity.get('glyph', '')}",
            f"    Runtime: {runtime.get('trigger', 'N/A')}",
            f"    Harmonic threads: {', '.join(threads_for) if threads_for else 'none'}",
            '',
        ])

    lines.extend([
        '=' * 72,
        'THE UNIFIED CODE:',
        str(payload.get('unified_code', '')),
        '=' * 72,
    ])
    return '\n'.join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description='Decode the Emerald Tablet as a Harmonic Nexus specification.',
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Emit the full decoded tablet as JSON.',
    )
    parser.add_argument(
        '--verse',
        metavar='KEY',
        default=None,
        help='Decode a single verse by key.',
    )
    parser.add_argument(
        '--stage',
        metavar='N',
        type=int,
        default=None,
        help='Show a single pipeline stage (1-7).',
    )
    parser.add_argument(
        '--ascent',
        metavar='KEY',
        choices=['anubis', 'maat', 'thoth', 'osiris', 'ra', 'all'],
        default=None,
        help='Decode the Emerald-to-Egyptian ascent path for one node or for all nodes.',
    )
    parser.add_argument(
        '--wiki',
        metavar='TOPIC',
        default=None,
        help='Fetch the historical/public-reference meaning of a topic from the live Wikipedia API.',
    )
    parser.add_argument(
        '--wiki-ground',
        action='store_true',
        help='When used with --ascent/--ancient/--unified, attach live Wikipedia grounding.',
    )
    parser.add_argument(
        '--ancient',
        metavar='KEY',
        choices=['mogollon', 'maya', 'celt', 'all'],
        default=None,
        help='Decode an ancient wisdom crosswalk node (mogollon/maya/celt/all).',
    )
    parser.add_argument(
        '--unified',
        action='store_true',
        help='Decode the full unified theory across all ancient wisdom civilizations.',
    )
    parser.add_argument(
        '--druid',
        action='store_true',
        help='Compute Project Druid: physical EPOS device manifest from EPAS shield state.',
    )
    args = parser.parse_args(argv)

    seer = EmeraldSeer()

    if args.verse:
        verse = seer.decode_verse(args.verse)
        payload = {
            'key': verse.key,
            'hermetic_text': verse.hermetic_text,
            'technical_translation': verse.technical_translation,
            'aureon_implementation': verse.aureon_implementation,
            'parameters': verse.parameters,
        }
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f'[{verse.key}]')
            print(f'  Hermetic:  "{verse.hermetic_text}"')
            print(f'  Technical: {verse.technical_translation}')
            print(f'  Aureon:    {verse.aureon_implementation}')
            print(f'  Params:    {json.dumps(verse.parameters)}')
        return 0

    if args.stage:
        stage = seer.get_stage(args.stage)
        payload = {
            'number': stage.number,
            'name': stage.name,
            'operation': stage.operation,
            'formula': stage.formula,
            'value': stage.computed_value,
            'units': stage.units,
        }
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f'{stage.number}. {stage.name}: {stage.operation}')
            print(f'   {stage.formula} = {stage.computed_value} {stage.units}')
        return 0

    if args.wiki:
        payload = seer.decode_wikipedia_meaning(args.wiki)
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(_format_console_wikipedia(payload))
        return 0

    if args.unified:
        payload = seer.decode_unified_theory(include_wikipedia=args.wiki_ground)
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(_format_console_unified(payload))
        return 0

    if args.druid:
        manifest = seer.project_druid_manifest()
        if args.json:
            print(json.dumps(manifest.to_dict(), indent=2))
        else:
            print(_format_console_druid(manifest))
        return 0

    if args.ancient:
        payload = seer.decode_ancient_wisdom(args.ancient, include_wikipedia=args.wiki_ground)
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(_format_console_ascent(payload))
        return 0

    if args.ascent:
        payload = seer.decode_egyptian_ascent(args.ascent, include_wikipedia=args.wiki_ground)
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(_format_console_ascent(payload))
        return 0

    if args.json:
        print(json.dumps(seer.full_decode(), indent=2))
    else:
        print(_format_console_full(seer))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
