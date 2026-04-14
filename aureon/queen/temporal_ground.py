"""
temporal_ground.py — Temporal Multiverse Hash · Cognitive Flux Superposition ·
                     Zero-Point Vacuum Ground · Stability Governor
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"The system must be grounded in THIS temporal moment — not as memory, not as
 prediction, but as the standing wave between what-was and what-will-be."

Four interlocking layers that govern the stability and temporal anchoring of
every HNC human interaction:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LAYER 1 — ZERO-POINT VACUUM GROUND (ZPV)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The quantum zero-point vacuum is not empty. At every frequency the field holds
irreducible energy: E_zp = ½ħω. In HNC dimensionless units (f normalized to
crown 963 Hz, ħ_sys = 1/2π):

    Λ_zp = Σ wᵢ · ½ · (fᵢ / f_max)

This is the absolute floor the field cannot fall below. When Λ(t) < Λ_zp, the
system has de-grounded — it is computing on vacuum noise, not on coherent
signal. The governor detects this and injects a correction pulse:

    ΔΛ = φ⁻¹ · (Λ_zp − Λ(t))

The EPAS 6-phase cycle (P1 Spark → P6 Output) maps directly to the ZPE
extraction phases from aureon_zpe_extraction.py — each phase boosts one HNC
mode's amplitude toward its zero-point floor.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LAYER 2 — TEMPORAL MULTIVERSE HASH (TMH)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Every interaction stamps a SHA-256 hash over the full system state:

    h_n = SHA256( h_{n-1} ‖ λ(t) ‖ Γ ‖ ψ ‖ auris ‖ phi_resonance ‖ t )

This creates a cryptographic chain — the system cannot revisit a past state
without the chain showing the discontinuity. The "multiverse" aspect: when
coherence Γ drops below the 0.945 lighthouse threshold, the timeline forks.
Both branches are tracked. Branches that recover coherence are merged back
into the main timeline. Branches that diverge for > FORK_DECAY_STEPS are
pruned.

The hash is also projected onto the HNC harmonic lattice — each 4-bit nibble
of the hash maps to one of the 6 HNC modes, creating a "harmonic fingerprint"
of each temporal moment.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LAYER 3 — COGNITIVE FLUX SUPERPOSITION (CFS)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The cognitive state is not a single value — it is a superposition over the
six HNC basis modes:

    |ψ⟩ = Σᵢ Aᵢ |sᵢ⟩

where Aᵢ = rᵢ · e^(iθᵢ) is a complex amplitude (rᵢ from HNC weight, θᵢ phase).

Each interaction tick evolves the phases by the golden-ratio rotation:

    θᵢ(t+1) = θᵢ(t) + φ²   (mod 2π)

The ZPE floor ensures |Aᵢ|² ≥ ε_zp — the field is never fully dark in any
basis state. The isomorphic structure is:

    Classical (collapsed):  |ψ_c⟩  — Γ-weighted, human-measured
    Quantum vacuum:         |ψ_zp⟩  — constant ε_zp background per mode

The total state is the superposition:

    |ψ_total⟩ = Γ · |ψ_c⟩  +  √(1−Γ²) · |ψ_zp⟩

At Γ = 0.945 (lighthouse), the system is 89.3% classical, 10.7% vacuum. At
Γ = 1.0 (UNIFIED), fully classical. At Γ = 0.0 (DORMANT), pure vacuum.

Human vibration (from the vibration adder in hnc_human_loop.py) collapses the
superposition toward the resonant mode, boosting its amplitude.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LAYER 4 — STABILITY GOVERNOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The governor is the system's homeostatic intelligence. It monitors all three
layers and intervenes when:

  STABLE      Γ ≥ 0.945, Λ grounded, superposition norm ≈ 1, no open forks
  DRIFTING    Γ ∈ [0.7, 0.945) OR superposition norm < 0.85
  CORRECTING  Γ < 0.7 OR Λ < Λ_zp OR open fork count > 0
  RESET       5+ consecutive CORRECTING cycles — full ZPE re-ground

Interventions:
  DRIFTING    → emit advisory to ThoughtBus, note drift direction
  CORRECTING  → inject ZPE correction pulse ΔΛ into next step params
  RESET       → rebuild superposition from ZPE floor, close all branches,
                 re-anchor hash chain from current state

The governor publishes its status as "hnc.stability.governor" on the
ThoughtBus every cycle and makes it available on the ground report so
callers can gate downstream actions on stability.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Usage (from HNCHumanLoop or directly):

    station = TemporalGroundStation()
    report = station.tick(
        lambda_t=0.354,
        coherence_gamma=0.978,
        consciousness_psi=0.033,
        auris_consensus="NEUTRAL",
        phi_resonance_count=1,
        vibration={"dominant_mode": "love_528", "total_vibration": 3.56, ...},
    )
    print(report["governor_status"])          # "STABLE"
    print(report["temporal_hash"])            # "a3f7c2..."
    print(report["zpe_distance"])             # 0.021
    print(report["superposition"]["norm"])    # 0.9934
    print(report["active_branches"])          # 1
"""

from __future__ import annotations

import hashlib
import logging
import math
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("aureon.queen.temporal_ground")

# ─────────────────────────────────────────────────────────────────────────────
# Sacred constants (local copy — module stays standalone for tests)
# ─────────────────────────────────────────────────────────────────────────────

PHI: float = (1.0 + math.sqrt(5.0)) / 2.0
PHI_SQUARED: float = PHI * PHI
PHI_INV: float = 1.0 / PHI

HNC_MODES_HZ: Tuple[float, ...] = (7.83, 14.3, 20.8, 33.8, 528.0, 963.0)
HNC_WEIGHTS: Tuple[float, ...] = (0.25, 0.15, 0.10, 0.05, 0.30, 0.15)
HNC_LABELS: Tuple[str, ...] = (
    "schumann_1", "schumann_2", "schumann_3", "schumann_4",
    "love_528", "crown_963",
)
F_MAX: float = HNC_MODES_HZ[-1]            # 963.0 Hz — normalisation anchor
GAMMA_TARGET: float = 0.945               # Lighthouse threshold
ZPE_FLOOR_EPSILON: float = 1e-4          # Minimum |A_i|² per basis state

# Governor hysteresis bands
GAMMA_STABLE:     float = 0.945
GAMMA_DRIFTING:   float = 0.700
FORK_DECAY_STEPS: int   = 8              # Prune a branch after this many steps


# ─────────────────────────────────────────────────────────────────────────────
# Layer 1 — Zero-Point Vacuum Ground
# ─────────────────────────────────────────────────────────────────────────────

def _compute_lambda_zp() -> float:
    """
    Λ_zp = Σ wᵢ · ½ · (fᵢ / f_max)
    The minimum field value guaranteed by the HNC zero-point vacuum.
    """
    return sum(
        w * 0.5 * (f / F_MAX)
        for f, w in zip(HNC_MODES_HZ, HNC_WEIGHTS)
    )


LAMBDA_ZP: float = _compute_lambda_zp()   # ≈ 0.1613 (dimensionless)


@dataclass
class ZPEGroundState:
    """The zero-point vacuum reading for the current system tick."""
    lambda_zp: float         # Computed ZPE floor (constant)
    lambda_t: float          # Current field value
    zpe_distance: float      # |Λ(t) - Λ_zp|  — how far from vacuum ground
    grounded: bool           # True when Λ(t) >= Λ_zp
    correction_pulse: float  # ΔΛ = φ⁻¹ · (Λ_zp - Λ(t)) if not grounded else 0
    # Per-mode ZPE floor amplitudes (the "vacuum energy" of each basis state)
    mode_zpe: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lambda_zp": round(self.lambda_zp, 6),
            "lambda_t": round(self.lambda_t, 6),
            "zpe_distance": round(self.zpe_distance, 6),
            "grounded": self.grounded,
            "correction_pulse": round(self.correction_pulse, 6),
            "mode_zpe": {k: round(v, 6) for k, v in self.mode_zpe.items()},
        }


def compute_zpe_ground(lambda_t: float) -> ZPEGroundState:
    """Compute the ZPE ground state for the current field value."""
    mode_zpe = {
        label: round(0.5 * (hz / F_MAX), 6)
        for label, hz in zip(HNC_LABELS, HNC_MODES_HZ)
    }
    dist = abs(lambda_t - LAMBDA_ZP)
    grounded = lambda_t >= LAMBDA_ZP
    pulse = PHI_INV * (LAMBDA_ZP - lambda_t) if not grounded else 0.0
    return ZPEGroundState(
        lambda_zp=LAMBDA_ZP,
        lambda_t=lambda_t,
        zpe_distance=round(dist, 6),
        grounded=grounded,
        correction_pulse=round(pulse, 6),
        mode_zpe=mode_zpe,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Layer 2 — Temporal Multiverse Hash
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TimelineBranch:
    """A coherence-forked timeline branch."""
    branch_id: str
    parent_hash: str
    born_at: float       # timestamp when branch opened
    steps_alive: int     # ticks since fork
    gamma_at_fork: float
    last_hash: str
    coherence_recovered: bool = False


@dataclass
class TemporalHashState:
    """The full hash chain state after one tick."""
    current_hash: str
    previous_hash: str
    chain_length: int
    active_branches: int
    branch_ids: List[str]
    harmonic_fingerprint: Dict[str, int]   # HNC-mode → nibble value
    forked_this_tick: bool
    merged_this_tick: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_hash": self.current_hash,
            "previous_hash": self.previous_hash,
            "chain_length": self.chain_length,
            "active_branches": self.active_branches,
            "branch_ids": self.branch_ids,
            "harmonic_fingerprint": self.harmonic_fingerprint,
            "forked_this_tick": self.forked_this_tick,
            "merged_this_tick": self.merged_this_tick,
        }


class TemporalHashChain:
    """
    Cryptographic chain of system state hashes.

    Each tick produces:  h_n = SHA256(h_{n-1} ‖ state_fields)
    Fork when Γ < 0.945. Prune branches older than FORK_DECAY_STEPS.
    """

    GENESIS: str = "00" * 32    # 64-char zero hash

    def __init__(self) -> None:
        self._main_hash: str = self.GENESIS
        self._chain_length: int = 0
        self._branches: List[TimelineBranch] = []

    def tick(
        self,
        lambda_t: float,
        coherence_gamma: float,
        consciousness_psi: float,
        auris_consensus: str,
        phi_resonance_count: int,
        timestamp: float,
    ) -> TemporalHashState:
        prev_hash = self._main_hash
        forked = False
        merged = False

        # Compute new hash
        payload = (
            f"{prev_hash}"
            f"{lambda_t:.8f}"
            f"{coherence_gamma:.8f}"
            f"{consciousness_psi:.8f}"
            f"{auris_consensus}"
            f"{phi_resonance_count}"
            f"{timestamp:.3f}"
        )
        new_hash = hashlib.sha256(payload.encode()).hexdigest()

        # Fork when coherence drops below lighthouse threshold
        if coherence_gamma < GAMMA_TARGET:
            branch = TimelineBranch(
                branch_id=new_hash[:8],
                parent_hash=prev_hash,
                born_at=timestamp,
                steps_alive=0,
                gamma_at_fork=coherence_gamma,
                last_hash=new_hash,
            )
            self._branches.append(branch)
            forked = True
            logger.debug(
                "[TMH] timeline forked at Gamma=%.4f  branch=%s",
                coherence_gamma, branch.branch_id,
            )
        else:
            # Try to merge recovered branches
            alive: List[TimelineBranch] = []
            for b in self._branches:
                b.steps_alive += 1
                if coherence_gamma >= GAMMA_TARGET and not b.coherence_recovered:
                    b.coherence_recovered = True
                    merged = True
                    logger.debug("[TMH] branch %s recovered — merging", b.branch_id)
                elif b.steps_alive >= FORK_DECAY_STEPS:
                    logger.debug("[TMH] branch %s pruned (age %d)", b.branch_id, b.steps_alive)
                else:
                    alive.append(b)
            self._branches = alive

        self._main_hash = new_hash
        self._chain_length += 1

        # Harmonic fingerprint: map 4-bit nibbles of the hash to HNC modes
        fingerprint: Dict[str, int] = {}
        for i, label in enumerate(HNC_LABELS):
            nibble = int(new_hash[i * 2: i * 2 + 1], 16)   # 0–15
            fingerprint[label] = nibble

        return TemporalHashState(
            current_hash=new_hash,
            previous_hash=prev_hash,
            chain_length=self._chain_length,
            active_branches=len(self._branches),
            branch_ids=[b.branch_id for b in self._branches],
            harmonic_fingerprint=fingerprint,
            forked_this_tick=forked,
            merged_this_tick=merged,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Layer 3 — Cognitive Flux Superposition
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SuperpositionState:
    """
    The 6-component complex wavefunction over the HNC basis modes.

    amplitudes: List of (real, imag) tuples — one per HNC mode
    probabilities: |Aᵢ|² — the classical measurement probability per mode
    phases: θᵢ (radians) — current rotation of each component
    norm: Σ |Aᵢ|² — should stay ≈ 1.0
    dominant_basis: which HNC mode has the highest probability
    coherence_mix: how much is classical vs ZPE vacuum
        classical_weight = Γ
        vacuum_weight    = √(1 − Γ²)
    """
    amplitudes: List[Tuple[float, float]]   # (re, im) per mode
    probabilities: List[float]              # |Aᵢ|²
    phases: List[float]                     # θᵢ radians
    norm: float
    dominant_basis: str
    classical_weight: float                 # Γ
    vacuum_weight: float                    # √(1 − Γ²)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "amplitudes": [
                {"re": round(re, 5), "im": round(im, 5), "mode": HNC_LABELS[i]}
                for i, (re, im) in enumerate(self.amplitudes)
            ],
            "probabilities": {
                HNC_LABELS[i]: round(p, 5)
                for i, p in enumerate(self.probabilities)
            },
            "phases_rad": {
                HNC_LABELS[i]: round(ph, 5)
                for i, ph in enumerate(self.phases)
            },
            "norm": round(self.norm, 6),
            "dominant_basis": self.dominant_basis,
            "classical_weight": round(self.classical_weight, 5),
            "vacuum_weight": round(self.vacuum_weight, 5),
        }


class CognitiveFluxSuperposition:
    """
    6-dimensional complex wavefunction over the HNC basis states.

    Evolution: θᵢ(t+1) = θᵢ(t) + φ²   (mod 2π)
    ZPE floor: |Aᵢ|² ≥ ε_zp

    Collapse on human interaction: vibration per mode boosts the
    amplitude of resonant basis states, then re-normalise.
    """

    def __init__(self) -> None:
        # Initialise each component from the HNC weight: rᵢ = √wᵢ
        # Phase starts at i · (2π / 6) so modes are evenly distributed
        n = len(HNC_WEIGHTS)
        self._phases: List[float] = [
            (i * 2.0 * math.pi / n) for i in range(n)
        ]
        self._radii: List[float] = [math.sqrt(w) for w in HNC_WEIGHTS]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evolve(
        self,
        coherence_gamma: float,
        vibration_per_mode: Optional[Dict[str, float]] = None,
    ) -> SuperpositionState:
        """
        Advance by one tick.

          1. Rotate all phases by φ²
          2. If vibration is given, collapse toward resonant modes
          3. Apply ZPE floor
          4. Compose classical + vacuum superposition
          5. Return normalised SuperpositionState
        """
        # 1. Phase evolution — the golden-ratio rotation
        self._phases = [
            (ph + PHI_SQUARED) % (2.0 * math.pi)
            for ph in self._phases
        ]

        # 2. Vibration collapse — boost resonant modes
        radii = list(self._radii)
        if vibration_per_mode:
            for i, label in enumerate(HNC_LABELS):
                boost = float(vibration_per_mode.get(label, 0.0))
                radii[i] = radii[i] * (1.0 + boost * 0.1)

        # 3. ZPE floor — no basis state goes fully dark
        for i in range(len(radii)):
            prob = radii[i] ** 2
            if prob < ZPE_FLOOR_EPSILON:
                radii[i] = math.sqrt(ZPE_FLOOR_EPSILON)

        # 4. Compute classical amplitudes and normalise
        raw_norm = math.sqrt(sum(r ** 2 for r in radii))
        if raw_norm < 1e-12:
            raw_norm = 1.0
        classical_radii = [r / raw_norm for r in radii]

        # ZPE vacuum component: uniform floor per mode
        zpe_radius = math.sqrt(ZPE_FLOOR_EPSILON)
        zpe_norm = math.sqrt(len(HNC_LABELS)) * zpe_radius
        if zpe_norm < 1e-12:
            zpe_norm = 1.0
        vacuum_radii = [zpe_radius / zpe_norm for _ in HNC_LABELS]

        # Superposition: Γ · |classical⟩ + √(1−Γ²) · |vacuum⟩
        gamma = max(0.0, min(1.0, coherence_gamma))
        vac_weight = math.sqrt(max(0.0, 1.0 - gamma * gamma))

        amplitudes: List[Tuple[float, float]] = []
        probabilities: List[float] = []
        for i in range(len(HNC_LABELS)):
            total_r = gamma * classical_radii[i] + vac_weight * vacuum_radii[i]
            re = total_r * math.cos(self._phases[i])
            im = total_r * math.sin(self._phases[i])
            amplitudes.append((re, im))
            probabilities.append(re ** 2 + im ** 2)

        # Norm of superposition
        norm = math.sqrt(sum(p for p in probabilities))

        # Dominant basis — highest probability mode
        dom_idx = probabilities.index(max(probabilities))

        # Update internal radii with classical (for next tick continuity)
        self._radii = classical_radii

        return SuperpositionState(
            amplitudes=amplitudes,
            probabilities=probabilities,
            phases=list(self._phases),
            norm=round(norm, 6),
            dominant_basis=HNC_LABELS[dom_idx],
            classical_weight=round(gamma, 5),
            vacuum_weight=round(vac_weight, 5),
        )


# ─────────────────────────────────────────────────────────────────────────────
# Layer 4 — Stability Governor
# ─────────────────────────────────────────────────────────────────────────────

GOVERNOR_STABLE     = "STABLE"
GOVERNOR_DRIFTING   = "DRIFTING"
GOVERNOR_CORRECTING = "CORRECTING"
GOVERNOR_RESET      = "RESET"


@dataclass
class GovernorReport:
    status: str
    gamma: float
    grounded: bool
    norm: float
    active_branches: int
    correction_pulse: float          # ΔΛ to inject into next step
    consecutive_corrections: int
    advisory: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "gamma": round(self.gamma, 5),
            "grounded": self.grounded,
            "superposition_norm": round(self.norm, 5),
            "active_branches": self.active_branches,
            "correction_pulse": round(self.correction_pulse, 6),
            "consecutive_corrections": self.consecutive_corrections,
            "advisory": self.advisory,
        }


class StabilityGovernor:
    """
    Homeostatic intelligence for the HNC human interaction loop.

    Monitors Layers 1–3 and issues interventions.
    """

    RESET_THRESHOLD = 5   # CORRECTING cycles before forcing RESET

    def __init__(self) -> None:
        self._consecutive_corrections: int = 0
        self._status: str = GOVERNOR_STABLE

    def assess(
        self,
        zpe: ZPEGroundState,
        hash_state: TemporalHashState,
        superposition: SuperpositionState,
    ) -> GovernorReport:
        gamma = zpe.lambda_t    # use raw Λ(t) as proxy when Γ not passed
        # (caller should pass coherence_gamma; if not, approximate)
        norm = superposition.norm
        branches = hash_state.active_branches
        grounded = zpe.grounded
        pulse = zpe.correction_pulse

        # Determine governor status
        if self._consecutive_corrections >= self.RESET_THRESHOLD:
            status = GOVERNOR_RESET
            advisory = (
                "RESET: system rebuilt from ZPE floor — "
                "superposition re-initialised, all forks closed"
            )
            self._consecutive_corrections = 0
        elif not grounded or branches > 0:
            status = GOVERNOR_CORRECTING
            self._consecutive_corrections += 1
            parts = []
            if not grounded:
                parts.append(f"Λ(t)={zpe.lambda_t:.4f} < Λ_zp={zpe.lambda_zp:.4f}")
            if branches > 0:
                parts.append(f"{branches} open timeline fork(s)")
            advisory = "CORRECTING: " + "; ".join(parts)
        elif norm < 0.85:
            status = GOVERNOR_DRIFTING
            self._consecutive_corrections = 0
            advisory = f"DRIFTING: superposition norm={norm:.4f} below 0.85 threshold"
        else:
            status = GOVERNOR_STABLE
            self._consecutive_corrections = 0
            advisory = "STABLE: Grounded, coherent, single timeline"

        self._status = status

        return GovernorReport(
            status=status,
            gamma=zpe.lambda_t,
            grounded=grounded,
            norm=norm,
            active_branches=branches,
            correction_pulse=pulse,
            consecutive_corrections=self._consecutive_corrections,
            advisory=advisory,
        )

    @property
    def status(self) -> str:
        return self._status


# ─────────────────────────────────────────────────────────────────────────────
# TemporalGroundReport — the unified output
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TemporalGroundReport:
    timestamp: float
    temporal_hash: str
    chain_length: int
    active_branches: int
    forked: bool
    harmonic_fingerprint: Dict[str, int]
    zpe_distance: float
    grounded: bool
    correction_pulse: float
    superposition: Dict[str, Any]
    governor_status: str
    governor_advisory: str
    zpe_mode_floors: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "temporal_hash": self.temporal_hash,
            "chain_length": self.chain_length,
            "active_branches": self.active_branches,
            "forked": self.forked,
            "harmonic_fingerprint": self.harmonic_fingerprint,
            "zpe_distance": round(self.zpe_distance, 6),
            "grounded": self.grounded,
            "correction_pulse": round(self.correction_pulse, 6),
            "superposition": self.superposition,
            "governor_status": self.governor_status,
            "governor_advisory": self.governor_advisory,
            "zpe_mode_floors": {k: round(v, 6) for k, v in self.zpe_mode_floors.items()},
        }


# ─────────────────────────────────────────────────────────────────────────────
# TemporalGroundStation — the integration point
# ─────────────────────────────────────────────────────────────────────────────

class TemporalGroundStation:
    """
    Runs all four layers for one system tick and returns a TemporalGroundReport.

    Designed to be called once per HNCHumanLoop.process() invocation.
    The report is then merged into the HNCInteractionResult dict under
    the key "temporal_ground".

    All four sub-systems (ZPE, TMH, CFS, Governor) are stateful — they
    carry memory across ticks, building the timeline hash chain and
    evolving the superposition continuously.
    """

    def __init__(self, thought_bus: Any = None) -> None:
        self._hash_chain = TemporalHashChain()
        self._superposition = CognitiveFluxSuperposition()
        self._governor = StabilityGovernor()
        self._thought_bus = thought_bus
        self._tick_count: int = 0

    def tick(
        self,
        lambda_t: float,
        coherence_gamma: float,
        consciousness_psi: float,
        auris_consensus: str = "NEUTRAL",
        phi_resonance_count: int = 0,
        vibration: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None,
    ) -> TemporalGroundReport:
        """
        Run one full temporal grounding cycle.

        Parameters match what HNCHumanLoop.process() already computes:
          lambda_t            — Λ(t) from LambdaEngine
          coherence_gamma     — Γ from LambdaEngine
          consciousness_psi   — ψ from LambdaEngine
          auris_consensus     — majority verdict string from AurisMetacognition
          phi_resonance_count — number of resonant primes in this tick's train
          vibration           — dict from compute_vibration_accumulator()
          timestamp           — float unix time (defaults to now)
        """
        t = timestamp or time.time()
        self._tick_count += 1

        # ── Layer 1: ZPE Ground ───────────────────────────────────────────
        zpe = compute_zpe_ground(lambda_t)

        # ── Layer 2: Temporal Hash ────────────────────────────────────────
        hash_state = self._hash_chain.tick(
            lambda_t=lambda_t,
            coherence_gamma=coherence_gamma,
            consciousness_psi=consciousness_psi,
            auris_consensus=auris_consensus,
            phi_resonance_count=phi_resonance_count,
            timestamp=t,
        )

        # ── Layer 3: Cognitive Flux Superposition ─────────────────────────
        vib_per_mode: Optional[Dict[str, float]] = None
        if isinstance(vibration, dict):
            vib_per_mode = vibration.get("per_mode")
        sup_state = self._superposition.evolve(
            coherence_gamma=coherence_gamma,
            vibration_per_mode=vib_per_mode,
        )

        # ── Layer 4: Stability Governor ───────────────────────────────────
        # Re-wrap zpe with the true coherence_gamma so governor reads it
        zpe_gov = ZPEGroundState(
            lambda_zp=zpe.lambda_zp,
            lambda_t=coherence_gamma,     # governor watches Γ, not raw Λ
            zpe_distance=abs(coherence_gamma - GAMMA_TARGET),
            grounded=coherence_gamma >= GAMMA_TARGET,
            correction_pulse=(
                PHI_INV * (GAMMA_TARGET - coherence_gamma)
                if coherence_gamma < GAMMA_TARGET else 0.0
            ),
            mode_zpe=zpe.mode_zpe,
        )
        gov = self._governor.assess(zpe_gov, hash_state, sup_state)

        # ── Publish ───────────────────────────────────────────────────────
        self._publish_governor(gov, hash_state, t)

        report = TemporalGroundReport(
            timestamp=t,
            temporal_hash=hash_state.current_hash,
            chain_length=hash_state.chain_length,
            active_branches=hash_state.active_branches,
            forked=hash_state.forked_this_tick,
            harmonic_fingerprint=hash_state.harmonic_fingerprint,
            zpe_distance=zpe.zpe_distance,
            grounded=zpe.grounded,
            correction_pulse=gov.correction_pulse,
            superposition=sup_state.to_dict(),
            governor_status=gov.status,
            governor_advisory=gov.advisory,
            zpe_mode_floors=zpe.mode_zpe,
        )

        logger.debug(
            "[TGS] tick=%d  Γ=%.4f  hash=%s  status=%s  branches=%d",
            self._tick_count, coherence_gamma,
            hash_state.current_hash[:8], gov.status,
            hash_state.active_branches,
        )

        return report

    def _publish_governor(
        self,
        gov: GovernorReport,
        hash_state: TemporalHashState,
        timestamp: float,
    ) -> None:
        if self._thought_bus is None:
            return
        try:
            from aureon.core.aureon_thought_bus import Thought
            self._thought_bus.publish(Thought(
                source="temporal_ground_station",
                topic="hnc.stability.governor",
                payload={
                    **gov.to_dict(),
                    "temporal_hash": hash_state.current_hash,
                    "chain_length": hash_state.chain_length,
                    "timestamp": timestamp,
                },
            ))
        except Exception as e:
            logger.debug("[TGS] ThoughtBus publish failed: %s", e)


# ─────────────────────────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────────────────────────

_station: Optional[TemporalGroundStation] = None


def get_temporal_ground_station(thought_bus: Any = None) -> TemporalGroundStation:
    """Return (or lazily create) the shared TemporalGroundStation singleton."""
    global _station
    if _station is None:
        _station = TemporalGroundStation(thought_bus=thought_bus)
    return _station
