"""
HNC AURIS THRONE — hnc_auris_throne.py
========================================
Adapted from Aureon's dr_auris_throne.py (462 lines).

In Aureon, Dr. Auris Throne is the Planetary Harmonic Intelligence
Engine. It ingests live NOAA/NASA/Schumann data, processes it through
the HNC Master Formula Λ(t), and publishes advisories:
    TRADE / OBSERVE / PROTECT / SLEEP

The Throne doesn't trade. It sets the CONDITIONS for trading.
It's the strategic layer that tells the Queen when the environment
is favourable or hostile.

For the HNC Accountant, Dr. Auris Throne becomes the
TAX ENVIRONMENT INTELLIGENCE ENGINE:

AUREON DR. AURIS THRONE      →  HNC TAX THRONE
──────────────────────────────────────────────────
Cosmic State (space weather)  →  Fiscal State (tax environment)
Schumann Resonance            →  Budget Resonance (policy changes)
NOAA Data                     →  HMRC Published Data
Solar Flux                    →  Inflation Rate (fiscal pressure)
Geomagnetic Index             →  Enforcement Intensity Index
Advisory: TRADE               →  Advisory: OPTIMISE (conditions favour action)
Advisory: OBSERVE              →  Advisory: HOLD (wait for clarity)
Advisory: PROTECT              →  Advisory: DEFEND (enquiry risk elevated)
Advisory: SLEEP                →  Advisory: DEFER (no action needed)
HNC Master Formula Λ(t)       →  Tax Pressure Formula Λ(t)

The Tax Throne monitors the ENVIRONMENT in which tax decisions are made:
    - How aggressive is HMRC right now?
    - What's inflation doing to thresholds?
    - Are there upcoming policy changes?
    - What's the enforcement budget trend?
    - Is this a good time to file, claim, or defer?

It publishes a continuous ADVISORY that all other systems consume.

Sources (all open source / publicly published):
    - HMRC Annual Reports and Accounts (published)
    - ONS Consumer Price Index (monthly)
    - HMRC Compliance Check Statistics (annual)
    - Bank of England base rate (published)
    - OBR Economic & Fiscal Outlook (biannual)
    - HMRC internal manuals (published online)
    - Gov.uk legislation.gov.uk (all UK law)

Aureon Creator / Aureon Research — April 2026
"""

from __future__ import annotations
import logging
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import date, datetime
from enum import Enum

logger = logging.getLogger("hnc_auris_throne")

PHI = (1 + math.sqrt(5)) / 2  # 1.618 — The Golden Ratio
SCHUMANN_BASE = 7.83           # Hz — Earth's heartbeat


# ═══════════════════════════════════════════════════════════════════
# FISCAL STATES — The Tax Environment
# ═══════════════════════════════════════════════════════════════════

class FiscalState(Enum):
    """The current state of the tax environment"""
    BENIGN = "BENIGN"           # Low enforcement, stable policy
    SHIFTING = "SHIFTING"       # Policy changes in progress
    HOSTILE = "HOSTILE"         # High enforcement, aggressive HMRC
    CRISIS = "CRISIS"           # Emergency measures, unusual rules


class ThroneAdvisory(Enum):
    """What the Throne advises all systems to do"""
    OPTIMISE = "OPTIMISE"       # Environment favours aggressive planning
    HOLD = "HOLD"               # Wait for clarity before major moves
    DEFEND = "DEFEND"           # Strengthen documentation, reduce risk
    DEFER = "DEFER"             # No action needed, maintain position


# ═══════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════

@dataclass
class FiscalEnvironment:
    """Complete snapshot of the tax environment"""
    # Inflation & thresholds
    cpi_annual: float = 3.2           # ONS CPI annual rate
    rpi_annual: float = 4.1           # RPI (used for some tax calcs)
    pa_frozen_until: int = 2028       # Personal Allowance freeze end
    fiscal_drag_annual: float = 500   # £ per year dragged into higher bands

    # HMRC posture
    hmrc_budget_bn: float = 5.2       # HMRC annual budget (£bn)
    compliance_yield_bn: float = 41.8 # Total compliance revenue (£bn)
    enquiry_rate_pct: float = 1.5     # % of SA returns opened for enquiry
    nudge_letters_sent: int = 150_000 # Annual nudge letters
    connect_data_sources: int = 60    # Number of data feeds into Connect

    # Interest rates
    boe_base_rate: float = 4.50       # Bank of England base rate
    hmrc_late_payment_rate: float = 7.00  # HMRC interest on late payment
    hmrc_repayment_rate: float = 3.50     # HMRC interest on overpayment

    # Policy outlook
    upcoming_changes: List[str] = field(default_factory=list)
    election_proximity: int = 3       # Years to next general election

    # Enforcement focus areas
    enforcement_targets: List[str] = field(default_factory=list)


@dataclass
class ThroneState:
    """The Throne's current assessment"""
    fiscal_state: FiscalState
    advisory: ThroneAdvisory
    pressure_score: float              # 0-1 (Λ(t) adapted)
    confidence: float                  # 0-1
    environment: FiscalEnvironment
    reasoning: List[str]
    gate_open: bool                    # Is it safe to take action?
    optimal_actions: List[str]
    warnings: List[str]
    timestamp: str


# ═══════════════════════════════════════════════════════════════════
# FISCAL INTELLIGENCE — 2025/26 Open Source Data
# ═══════════════════════════════════════════════════════════════════

FISCAL_DATA_2025_26 = FiscalEnvironment(
    cpi_annual=3.2,
    rpi_annual=4.1,
    pa_frozen_until=2028,
    fiscal_drag_annual=500,
    hmrc_budget_bn=5.2,
    compliance_yield_bn=41.8,
    enquiry_rate_pct=1.5,
    nudge_letters_sent=150_000,
    connect_data_sources=60,
    boe_base_rate=4.50,
    hmrc_late_payment_rate=7.00,
    hmrc_repayment_rate=3.50,
    upcoming_changes=[
        "MTD for Income Tax — April 2026 (over £50k)",
        "MTD for Income Tax — April 2027 (over £30k)",
        "Personal Allowance freeze continues until 2028",
        "Corporation Tax remains 25% (small profits rate 19%)",
        "National Living Wage increase to £12.21/hr (April 2025)",
        "Employer NI 15% from April 2025 (threshold £5k)",
    ],
    election_proximity=3,
    enforcement_targets=[
        "Construction CIS subcontractors — compliance checks",
        "Cryptoasset disposals — nudge letter campaign",
        "Online sellers — marketplace data sharing (eBay, Amazon, Etsy)",
        "Cash businesses — unexplained wealth monitoring",
        "Offshore income — AEOI/CRS automatic exchange",
        "Umbrella companies — disguised remuneration",
    ],
)


# ═══════════════════════════════════════════════════════════════════
# THE THRONE ENGINE — Tax Pressure Formula Λ(t)
# ═══════════════════════════════════════════════════════════════════

class HNCAurisThrone:
    """
    Tax Environment Intelligence Engine.

    Adapted from Dr. Auris Throne: replaces cosmic/planetary data
    with fiscal/economic data. Same architecture — continuous
    environment monitoring → advisory for all downstream systems.

    The original Throne uses Schumann resonance, solar flux,
    and geomagnetic indices. We use inflation rates, HMRC budgets,
    and enforcement statistics. The maths is the same.

    Λ(t) = Σ(signal_i × weight_i) / Σ(weight_i)
    """

    def __init__(self, environment: FiscalEnvironment = None):
        self.env = environment or FISCAL_DATA_2025_26
        self._state: Optional[ThroneState] = None

    def _compute_inflation_pressure(self) -> Tuple[float, str]:
        """
        Inflation pressure on tax thresholds.
        Frozen thresholds + rising prices = stealth tax increase.

        Adapted from Schumann resonance monitoring.
        """
        # CPI above 2% target = fiscal drag accelerating
        cpi_excess = max(0, self.env.cpi_annual - 2.0)
        years_frozen = max(0, self.env.pa_frozen_until - 2025)

        # Pressure = inflation excess × years remaining of freeze
        # Normalised to 0-1 using tanh (same as Auris softclip)
        raw_pressure = cpi_excess * years_frozen / 10
        pressure = math.tanh(raw_pressure)

        reasoning = (
            f"CPI {self.env.cpi_annual}% (target 2%). "
            f"PA frozen until {self.env.pa_frozen_until} ({years_frozen} years). "
            f"Fiscal drag ~£{self.env.fiscal_drag_annual:,.0f}/year. "
            f"Pressure: {pressure:.2f}"
        )
        return pressure, reasoning

    def _compute_enforcement_pressure(self) -> Tuple[float, str]:
        """
        HMRC enforcement intensity.
        Higher budget + more enquiries = more hostile environment.

        Adapted from geomagnetic index monitoring.
        """
        # Enquiry rate: 1-2% is normal, >2% is aggressive
        enquiry_signal = min(1.0, self.env.enquiry_rate_pct / 3.0)

        # Nudge letters: 100k is baseline, 200k+ is aggressive
        nudge_signal = min(1.0, self.env.nudge_letters_sent / 200_000)

        # Connect data sources: 40 is baseline, 80+ is deep surveillance
        connect_signal = min(1.0, self.env.connect_data_sources / 80)

        # Weighted average (same as Auris node weighting)
        weights = [0.4, 0.3, 0.3]
        signals = [enquiry_signal, nudge_signal, connect_signal]
        pressure = sum(s * w for s, w in zip(signals, weights))

        reasoning = (
            f"Enquiry rate {self.env.enquiry_rate_pct}% (signal: {enquiry_signal:.2f}). "
            f"Nudge letters {self.env.nudge_letters_sent:,} (signal: {nudge_signal:.2f}). "
            f"Connect sources {self.env.connect_data_sources} (signal: {connect_signal:.2f}). "
            f"Enforcement pressure: {pressure:.2f}"
        )
        return pressure, reasoning

    def _compute_interest_rate_pressure(self) -> Tuple[float, str]:
        """
        Interest rate environment.
        High rates = cost of late payment is steep, incentive to file early.

        Adapted from solar flux monitoring.
        """
        # Late payment rate: 5% is mild, 8%+ is punitive
        late_signal = min(1.0, self.env.hmrc_late_payment_rate / 10.0)

        # Repayment rate differential
        differential = self.env.hmrc_late_payment_rate - self.env.hmrc_repayment_rate
        diff_signal = min(1.0, differential / 5.0)

        pressure = (late_signal * 0.6 + diff_signal * 0.4)

        reasoning = (
            f"HMRC late rate {self.env.hmrc_late_payment_rate}%, "
            f"repayment rate {self.env.hmrc_repayment_rate}%. "
            f"Differential: {differential:.1f}pp. Pressure: {pressure:.2f}"
        )
        return pressure, reasoning

    def _compute_policy_pressure(self) -> Tuple[float, str]:
        """
        Policy change pressure.
        More changes = more complexity = more risk of error.

        Adapted from Kp index monitoring.
        """
        num_changes = len(self.env.upcoming_changes)
        num_targets = len(self.env.enforcement_targets)

        # Policy complexity: 3 changes is normal, 6+ is volatile
        change_signal = min(1.0, num_changes / 8)

        # Election proximity: closer to election = more populist tax moves
        election_signal = max(0, 1.0 - self.env.election_proximity / 5)

        pressure = change_signal * 0.7 + election_signal * 0.3

        reasoning = (
            f"{num_changes} upcoming policy changes. "
            f"{num_targets} enforcement targets. "
            f"Election in ~{self.env.election_proximity} years. "
            f"Policy pressure: {pressure:.2f}"
        )
        return pressure, reasoning

    def _compute_lambda(self) -> Tuple[float, List[str]]:
        """
        The Tax Pressure Formula Λ(t).
        Adapted from Auris HNC Master Formula.

        Λ(t) = Σ(signal_i × weight_i) / Σ(weight_i)

        Where signals are: inflation, enforcement, interest rates, policy
        """
        inflation_p, inflation_r = self._compute_inflation_pressure()
        enforcement_p, enforcement_r = self._compute_enforcement_pressure()
        interest_p, interest_r = self._compute_interest_rate_pressure()
        policy_p, policy_r = self._compute_policy_pressure()

        # Phi-weighted combination (golden ratio weighting — Auris signature)
        weights = {
            "enforcement": PHI,          # Most important
            "inflation": 1.0,
            "policy": 1 / PHI,           # Less urgent but strategic
            "interest": 1 / (PHI * PHI), # Background pressure
        }
        signals = {
            "enforcement": enforcement_p,
            "inflation": inflation_p,
            "policy": policy_p,
            "interest": interest_p,
        }

        total_weight = sum(weights.values())
        lambda_t = sum(signals[k] * weights[k] for k in weights) / total_weight

        reasoning = [inflation_r, enforcement_r, interest_r, policy_r]
        return lambda_t, reasoning

    def _determine_advisory(self, lambda_t: float) -> Tuple[FiscalState, ThroneAdvisory]:
        """
        Map Λ(t) to advisory.
        Same thresholds as Auris: TRADE/OBSERVE/PROTECT/SLEEP
        mapped to OPTIMISE/HOLD/DEFEND/DEFER.
        """
        if lambda_t < 0.30:
            return FiscalState.BENIGN, ThroneAdvisory.OPTIMISE
        elif lambda_t < 0.50:
            return FiscalState.SHIFTING, ThroneAdvisory.HOLD
        elif lambda_t < 0.70:
            return FiscalState.HOSTILE, ThroneAdvisory.DEFEND
        else:
            return FiscalState.CRISIS, ThroneAdvisory.DEFER

    def _generate_optimal_actions(self, state: FiscalState, advisory: ThroneAdvisory) -> List[str]:
        """What should we DO given the current environment?"""
        actions = []

        if advisory == ThroneAdvisory.OPTIMISE:
            actions = [
                "Conditions favour aggressive optimisation — deploy all weapons",
                "File early for faster CIS refund processing",
                "Consider voluntary disclosures while HMRC is not in enforcement mode",
                "Good time for pension contributions — rates may change",
                "Claim all invisible expenses — low scrutiny environment",
            ]
        elif advisory == ThroneAdvisory.HOLD:
            actions = [
                "Policy changes in progress — wait for clarity before major moves",
                "Continue routine filing and record-keeping",
                "Monitor upcoming Budget for threshold changes",
                "Prepare documentation for current claims in case of review",
            ]
        elif advisory == ThroneAdvisory.DEFEND:
            actions = [
                "Strengthen evidence base for all current claims",
                "Run Consciousness self-audit to check for weak spots",
                "Ensure all CIS certificates are reconciled and filed",
                "Reduce any borderline claims that lack strong evidence",
                "Ensure bank reconciliation is complete and bulletproof",
            ]
        elif advisory == ThroneAdvisory.DEFER:
            actions = [
                "Do not file anything non-essential right now",
                "Preserve cash reserves — uncertain environment",
                "Wait for emergency measures to stabilise",
                "Keep all records but defer strategic decisions",
            ]

        return actions

    def _generate_warnings(self, env: FiscalEnvironment) -> List[str]:
        """Active warnings based on current fiscal data."""
        warnings = []

        if env.hmrc_late_payment_rate > 6.0:
            warnings.append(
                f"HMRC late payment interest is {env.hmrc_late_payment_rate}% — "
                f"pay on time or face steep charges"
            )

        if env.enquiry_rate_pct > 2.0:
            warnings.append(
                f"Enquiry rate elevated at {env.enquiry_rate_pct}% — "
                f"higher than normal risk of compliance check"
            )

        if env.cpi_annual > 4.0:
            warnings.append(
                f"Inflation at {env.cpi_annual}% — fiscal drag accelerating. "
                f"Maximise deductions to counter threshold erosion"
            )

        for target in env.enforcement_targets:
            if "construction" in target.lower() or "cis" in target.lower():
                warnings.append(
                    f"HMRC actively targeting construction sector: {target}"
                )

        return warnings

    def assess(self) -> ThroneState:
        """
        Full Throne assessment.
        Computes Λ(t) and produces advisory for all systems.
        """
        lambda_t, reasoning = self._compute_lambda()
        state, advisory = self._determine_advisory(lambda_t)
        actions = self._generate_optimal_actions(state, advisory)
        warnings = self._generate_warnings(self.env)

        # Gate open = safe to take aggressive action
        gate_open = advisory in (ThroneAdvisory.OPTIMISE, ThroneAdvisory.HOLD)

        self._state = ThroneState(
            fiscal_state=state,
            advisory=advisory,
            pressure_score=round(lambda_t, 4),
            confidence=0.85,  # Based on quality of published data
            environment=self.env,
            reasoning=reasoning,
            gate_open=gate_open,
            optimal_actions=actions,
            warnings=warnings,
            timestamp=datetime.now().isoformat(),
        )

        return self._state

    def get_state(self) -> Optional[ThroneState]:
        """Get current state (assess first if needed)."""
        if self._state is None:
            self.assess()
        return self._state

    def is_gate_open(self) -> bool:
        """Is it safe to optimise aggressively?"""
        state = self.get_state()
        return state.gate_open if state else False

    def get_advisory(self) -> str:
        """Get the current advisory as a string."""
        state = self.get_state()
        return state.advisory.value if state else "UNKNOWN"

    def get_pressure_score(self) -> float:
        """Get Λ(t) — the tax pressure formula value."""
        state = self.get_state()
        return state.pressure_score if state else 0.5


# ═══════════════════════════════════════════════════════════════════
# SINGLETON — Same pattern as Aureon
# ═══════════════════════════════════════════════════════════════════

_throne_instance: Optional[HNCAurisThrone] = None

def get_hnc_auris_throne() -> HNCAurisThrone:
    """Get or create the singleton Throne instance."""
    global _throne_instance
    if _throne_instance is None:
        _throne_instance = HNCAurisThrone()
    return _throne_instance


# ═══════════════════════════════════════════════════════════════════
# DEMO / TEST
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("HNC AURIS THRONE — TAX ENVIRONMENT INTELLIGENCE")
    print("Adapted from Dr. Auris Throne (462 lines)")
    print("=" * 70)

    throne = HNCAurisThrone()
    state = throne.assess()

    print(f"\n  Fiscal State:    {state.fiscal_state.value}")
    print(f"  Advisory:        {state.advisory.value}")
    print(f"  Pressure Λ(t):   {state.pressure_score:.4f}")
    print(f"  Confidence:      {state.confidence:.0%}")
    print(f"  Gate Open:       {state.gate_open}")

    print(f"\n{'─' * 70}")
    print("PRESSURE ANALYSIS")
    print(f"{'─' * 70}")
    for r in state.reasoning:
        print(f"  {r}")

    print(f"\n{'─' * 70}")
    print("OPTIMAL ACTIONS")
    print(f"{'─' * 70}")
    for a in state.optimal_actions:
        print(f"  → {a}")

    if state.warnings:
        print(f"\n{'─' * 70}")
        print("ACTIVE WARNINGS")
        print(f"{'─' * 70}")
        for w in state.warnings:
            print(f"  ⚠ {w}")

    print(f"\n{'─' * 70}")
    print("UPCOMING POLICY CHANGES")
    print(f"{'─' * 70}")
    for change in state.environment.upcoming_changes:
        print(f"  {change}")

    print(f"\n{'─' * 70}")
    print("ENFORCEMENT TARGETS")
    print(f"{'─' * 70}")
    for target in state.environment.enforcement_targets:
        print(f"  {target}")
