"""
HNC UNIFIED ENGINE — hnc_unified_engine.py
============================================
The Master Orchestrator. Wires ALL systems together.

Adapted from Aureon's aureon_unified_startup.py (601 lines)
+ aureon_unified_decision_engine.py (388 lines)
+ aureon_unified_intelligence_registry.py (934 lines).

In Aureon, the Unified Engine boots every system, collects every
signal, weighs every vote, and produces ONE final decision.
40+ systems → 1 decision. That's the architecture.

For the HNC Accountant, the Unified Engine does the same:

    SYSTEM                    WHAT IT PRODUCES
    ──────────────────────────────────────────────
    Tax Warfare               → Weapons arsenal, kill list, battlefield intel
    Seer                      → Full-year prediction, band proximity, cash flow
    Deep Scanner              → Missed deductions, invisible expenses, payee intel
    Lattice                   → Optimal strategy combination, compound effects
    Consciousness             → Self-audit, pattern detection, defence narrative
    Metacognition             → Transaction-level reasoning, confidence scoring
    Intelligence Registry     → Government moves, enforcement targets, signals
    Tax Strategy              → Specific optimisation calculations
    Auris Throne              → Fiscal environment intel, Λ(t) pressure, advisory
    Auris Nodes               → 9-node coherence classification (Γ score)
    Auris Validator           → SA103 return validation, benchmark lock

    ALL 11 → Unified Verdict: The final tax position.

The Unified Engine is what makes this a SYSTEM, not just a collection
of tools. 11 engines feed into one verdict. One number. One truth.

Aureon Creator / Aureon Research — April 2026
"""

from __future__ import annotations
import logging
import sys
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import date, datetime

logger = logging.getLogger("hnc_unified_engine")

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ═══════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════

@dataclass
class SystemStatus:
    """Status of a single subsystem"""
    name: str
    loaded: bool
    error: str = ""
    result: Any = None


@dataclass
class UnifiedVerdict:
    """The ONE truth. All systems combined."""
    # Position
    gross_income: float
    total_expenses: float
    net_profit: float
    cis_deducted: float

    # Liability
    naive_tax_liability: float         # What a basic accountant would charge
    naive_ni_liability: float
    naive_total: float

    # Optimised
    optimised_tax: float
    optimised_ni: float
    optimised_total: float
    cis_credit: float
    net_liability: float               # After CIS
    refund_due: float                  # If CIS > liability

    # Savings
    total_annual_saving: float
    saving_percentage: float
    bulletproof_saving: float          # Zero risk
    action_needed_saving: float        # Needs user action

    # Warfare
    weapons_count: int
    threat_level: str
    defence_readiness: float

    # Seer
    prediction_confidence: str
    months_of_data: int
    monthly_reserve_needed: float
    payment_schedule: List[dict]

    # Deep Scanner
    missed_deductions: float
    invisible_expenses: float
    problem_transactions: int

    # Lattice
    strategies_active: int
    lattice_efficiency: float
    compound_bonuses: int

    # Consciousness
    conscience_verdict: str
    self_audit_score: str
    overall_risk: float
    at_risk_amount: float

    # Auris Throne — Fiscal Environment
    fiscal_advisory: str               # OPTIMISE / HOLD / DEFEND / DEFER
    fiscal_pressure: float             # Λ(t) 0-1
    fiscal_gate_open: bool             # Safe to take action?
    fiscal_warnings: List[str]

    # Auris Nodes — 9-Node Classification
    auris_sample_gamma: float          # Coherence Γ from sample classification
    auris_sample_action: str           # AUTO_CLASSIFY / REVIEW / HUMAN_REQUIRED
    auris_nodes_online: int            # How many nodes active

    # Auris Validator — SA103 Validation
    validator_coherence: float         # Return quality 0-1
    validator_benchmark_locked: bool   # All within HMRC norms?
    validator_passed: int
    validator_hard_fails: int
    validator_ready_to_file: bool
    validator_summary: str

    # Defence
    defence_narrative: str

    # Actions
    immediate_actions: List[str]
    future_actions: List[str]

    # System health
    systems_loaded: int
    systems_failed: int
    system_statuses: List[SystemStatus]

    # The bottom line
    bottom_line: str


# ═══════════════════════════════════════════════════════════════════
# THE UNIFIED ENGINE
# ═══════════════════════════════════════════════════════════════════

class HNCUnifiedEngine:
    """
    The Master Orchestrator.

    Boots every system. Collects every signal. Produces ONE verdict.

    This is the Aureon Unified Startup + Decision Engine + Intelligence
    Registry — all adapted for tax. The architecture that makes 40+
    trading systems work together now makes 8 tax systems work together.
    """

    def __init__(
        self,
        gross_income: float = 51_000,
        net_profit: float = 25_000,
        cis_deducted: float = 10_200,
        total_expenses: float = 26_000,
        cost_of_sales: float = 8_000,
        other_direct: float = 5_000,
        motor: float = 3_000,
        admin: float = 2_000,
        other_expenses: float = 1_500,
        partner_income: float = 0,
        mileage_estimate: float = 8_000,
        monthly_data: list = None,
        transactions: list = None,
    ):
        self.gross_income = gross_income
        self.net_profit = net_profit
        self.cis_deducted = cis_deducted
        self.total_expenses = total_expenses
        self.cost_of_sales = cost_of_sales
        self.other_direct = other_direct
        self.motor = motor
        self.admin = admin
        self.other_expenses = other_expenses
        self.partner_income = partner_income
        self.mileage_estimate = mileage_estimate
        self.monthly_data = monthly_data or []
        self.transactions = transactions or []

        self.systems: Dict[str, SystemStatus] = {}

    def _boot_system(self, name: str, boot_fn) -> Any:
        """Boot a single system with error handling."""
        try:
            result = boot_fn()
            self.systems[name] = SystemStatus(name=name, loaded=True, result=result)
            logger.info(f"[BOOT] {name}: OK")
            return result
        except Exception as e:
            self.systems[name] = SystemStatus(name=name, loaded=False, error=str(e))
            logger.warning(f"[BOOT] {name}: FAILED — {e}")
            return None

    def _calc_naive_tax(self) -> tuple:
        """Calculate naive tax (no optimisation)."""
        pa = 12_570
        taxable = max(0, self.net_profit - pa)
        if taxable <= 37_700:
            tax = taxable * 0.20
        else:
            tax = 37_700 * 0.20 + (taxable - 37_700) * 0.40
        ni = max(0, self.net_profit - pa) * 0.06
        if self.net_profit >= pa:
            ni += 3.45 * 52
        return round(tax, 2), round(ni, 2)

    def run(self) -> UnifiedVerdict:
        """
        Boot all systems. Collect all signals. Produce the verdict.
        """
        print("=" * 70)
        print("HNC UNIFIED ENGINE — BOOTING ALL SYSTEMS")
        print("=" * 70)

        # ── 1. TAX WARFARE ──
        warfare_result = self._boot_system("Tax Warfare", lambda: self._run_warfare())

        # ── 2. SEER ──
        seer_result = self._boot_system("Seer", lambda: self._run_seer())

        # ── 3. DEEP SCANNER ──
        scanner_result = self._boot_system("Deep Scanner", lambda: self._run_scanner())

        # ── 4. LATTICE ──
        lattice_result = self._boot_system("Lattice", lambda: self._run_lattice())

        # ── 5. CONSCIOUSNESS ──
        consciousness_result = self._boot_system("Consciousness", lambda: self._run_consciousness())

        # ── 6. METACOGNITION ──
        metacog_result = self._boot_system("Metacognition", lambda: self._run_metacognition())

        # ── 7. INTELLIGENCE REGISTRY ──
        intel_result = self._boot_system("Intelligence Registry", lambda: self._run_intelligence())

        # ── 8. TAX STRATEGY ──
        strategy_result = self._boot_system("Tax Strategy", lambda: self._run_strategy())

        # ── 9. AURIS THRONE — Fiscal Environment Intelligence ──
        throne_result = self._boot_system("Auris Throne", lambda: self._run_auris_throne())

        # ── 10. AURIS NODES — 9-Node Coherence Classification ──
        nodes_result = self._boot_system("Auris Nodes", lambda: self._run_auris_nodes())

        # ── 11. AURIS VALIDATOR — SA103 Return Validation ──
        validator_result = self._boot_system("Auris Validator", lambda: self._run_auris_validator())

        # ── BUILD UNIFIED VERDICT ──
        print(f"\n{'─' * 70}")
        print("BUILDING UNIFIED VERDICT")
        print(f"{'─' * 70}")

        naive_tax, naive_ni = self._calc_naive_tax()
        naive_total = naive_tax + naive_ni

        # Collect all savings from all systems
        total_saving = 0
        bulletproof_saving = 0
        action_saving = 0
        weapons_count = 0
        threat_level = "UNKNOWN"
        defence_readiness = 0
        immediate_actions = []
        future_actions = []

        # From Warfare
        if warfare_result:
            total_saving = max(total_saving, warfare_result.total_annual_saving)
            bulletproof_saving = warfare_result.bulletproof_saving
            action_saving = warfare_result.total_annual_saving - bulletproof_saving
            weapons_count = warfare_result.total_weapons
            threat_level = warfare_result.threat_level.value
            defence_readiness = warfare_result.defence_readiness
            immediate_actions.extend(warfare_result.action_items[:5])

        # From Lattice (may find better optimum)
        lattice_saving = 0
        strategies_active = 0
        lattice_efficiency = 0
        compound_bonuses = 0
        if lattice_result:
            lattice_saving = lattice_result.total_saving
            strategies_active = len(lattice_result.active_strategies)
            lattice_efficiency = lattice_result.best_position.efficiency_score
            compound_bonuses = len(lattice_result.compound_effects)
            if lattice_saving > total_saving:
                total_saving = lattice_saving

        # From Scanner
        missed_deductions = 0
        invisible_expenses = 0
        problem_transactions = 0
        if scanner_result:
            missed_deductions = scanner_result.total_missed_savings
            invisible_expenses = scanner_result.invisible_tax_saving
            problem_transactions = len(scanner_result.problem_transactions)
            total_saving += invisible_expenses  # Add invisible savings

        # From Seer
        prediction_confidence = "UNKNOWN"
        months_data = 0
        monthly_reserve = 0
        payment_schedule = []
        if seer_result:
            prediction_confidence = seer_result.confidence.value
            months_data = seer_result.months_of_data
            monthly_reserve = seer_result.monthly_reserve_needed
            payment_schedule = seer_result.payment_schedule
            for alert in seer_result.alerts:
                if alert.saving_potential > 0:
                    future_actions.append(f"[{alert.severity.value}] {alert.title}: {alert.action}")

        # From Consciousness
        conscience_verdict = "UNKNOWN"
        self_audit_score = "N/A"
        overall_risk = 0
        at_risk_amount = 0
        defence_narrative = ""
        if consciousness_result:
            conscience_verdict = consciousness_result.conscience_verdict.value
            self_audit_score = f"{consciousness_result.checks_passed}/{consciousness_result.total_checks}"
            overall_risk = consciousness_result.overall_risk_score
            at_risk_amount = consciousness_result.at_risk_amount
            defence_narrative = consciousness_result.defence_narrative
            immediate_actions.extend(consciousness_result.actions_required[:3])

        # From Auris Throne
        fiscal_advisory = "UNKNOWN"
        fiscal_pressure = 0.0
        fiscal_gate_open = True
        fiscal_warnings = []
        if throne_result:
            fiscal_advisory = throne_result.advisory.value
            fiscal_pressure = throne_result.pressure_score
            fiscal_gate_open = throne_result.gate_open
            fiscal_warnings = throne_result.warnings
            for action in throne_result.optimal_actions[:3]:
                future_actions.append(f"[THRONE] {action}")

        # From Auris Nodes
        auris_gamma = 0.0
        auris_action = "UNKNOWN"
        auris_nodes_online = 0
        if nodes_result:
            auris_gamma = nodes_result.coherence_score
            auris_action = nodes_result.action.value
            auris_nodes_online = len(nodes_result.node_signals)

        # From Auris Validator
        validator_coherence = 0.0
        validator_locked = False
        validator_passed = 0
        validator_hard_fails = 0
        validator_ready = False
        validator_summary = "Not run"
        if validator_result:
            validator_coherence = validator_result.coherence_score
            validator_locked = validator_result.benchmark_locked
            validator_passed = validator_result.passed
            validator_hard_fails = validator_result.hard_fails
            validator_ready = validator_result.ready_to_file
            validator_summary = validator_result.summary
            if validator_result.hard_fails > 0:
                for check in validator_result.checks:
                    if check.result.value == "HARD_FAIL":
                        immediate_actions.append(f"[VALIDATOR] Fix: {check.message}")

        # Calculate final position
        optimised_liability = max(0, naive_total - total_saving)
        cis_credit = self.cis_deducted
        net_liability = max(0, optimised_liability - cis_credit)
        refund_due = max(0, cis_credit - optimised_liability)

        saving_pct = (total_saving / naive_total * 100) if naive_total > 0 else 0

        # System health
        loaded = sum(1 for s in self.systems.values() if s.loaded)
        failed = sum(1 for s in self.systems.values() if not s.loaded)

        # The bottom line
        if refund_due > 0:
            bottom_line = (
                f"REFUND DUE: £{refund_due:,.0f}. "
                f"CIS deductions (£{cis_credit:,.0f}) exceed optimised liability (£{optimised_liability:,.0f}). "
                f"File early to get your money back faster."
            )
        elif net_liability < 500:
            bottom_line = (
                f"NET LIABILITY: £{net_liability:,.0f}. "
                f"Nearly break-even after CIS credits. "
                f"A normal accountant would have you paying £{naive_total - cis_credit:,.0f}. "
                f"We saved you £{total_saving:,.0f}."
            )
        else:
            bottom_line = (
                f"NET LIABILITY: £{net_liability:,.0f}. "
                f"Down from £{naive_total:,.0f} (before CIS: £{naive_total - cis_credit:,.0f} net). "
                f"Saved: £{total_saving:,.0f} ({saving_pct:.0f}%). "
                f"Monthly reserve: £{monthly_reserve:,.0f}."
            )

        return UnifiedVerdict(
            gross_income=self.gross_income,
            total_expenses=self.total_expenses,
            net_profit=self.net_profit,
            cis_deducted=self.cis_deducted,
            naive_tax_liability=naive_tax,
            naive_ni_liability=naive_ni,
            naive_total=naive_total,
            optimised_tax=round(max(0, naive_tax - total_saving * 0.7), 2),
            optimised_ni=round(max(0, naive_ni - total_saving * 0.3), 2),
            optimised_total=round(optimised_liability, 2),
            cis_credit=cis_credit,
            net_liability=round(net_liability, 2),
            refund_due=round(refund_due, 2),
            total_annual_saving=round(total_saving, 2),
            saving_percentage=round(saving_pct, 1),
            bulletproof_saving=round(bulletproof_saving, 2),
            action_needed_saving=round(action_saving, 2),
            weapons_count=weapons_count,
            threat_level=threat_level,
            defence_readiness=defence_readiness,
            prediction_confidence=prediction_confidence,
            months_of_data=months_data,
            monthly_reserve_needed=round(monthly_reserve, 2),
            payment_schedule=payment_schedule,
            missed_deductions=round(missed_deductions, 2),
            invisible_expenses=round(invisible_expenses, 2),
            problem_transactions=problem_transactions,
            strategies_active=strategies_active,
            lattice_efficiency=lattice_efficiency,
            compound_bonuses=compound_bonuses,
            conscience_verdict=conscience_verdict,
            self_audit_score=self_audit_score,
            overall_risk=round(overall_risk, 3),
            at_risk_amount=round(at_risk_amount, 2),
            fiscal_advisory=fiscal_advisory,
            fiscal_pressure=round(fiscal_pressure, 3),
            fiscal_gate_open=fiscal_gate_open,
            fiscal_warnings=fiscal_warnings,
            auris_sample_gamma=round(auris_gamma, 3),
            auris_sample_action=auris_action,
            auris_nodes_online=auris_nodes_online,
            validator_coherence=round(validator_coherence, 3),
            validator_benchmark_locked=validator_locked,
            validator_passed=validator_passed,
            validator_hard_fails=validator_hard_fails,
            validator_ready_to_file=validator_ready,
            validator_summary=validator_summary,
            defence_narrative=defence_narrative,
            immediate_actions=immediate_actions,
            future_actions=future_actions,
            systems_loaded=loaded,
            systems_failed=failed,
            system_statuses=list(self.systems.values()),
            bottom_line=bottom_line,
        )

    # ── System runners ──

    def _run_warfare(self):
        from core.hnc_tax_warfare import HNCTaxWarfare
        warfare = HNCTaxWarfare(
            gross_income=self.gross_income,
            net_profit=self.net_profit,
            cis_deducted=self.cis_deducted,
            partner_income=self.partner_income,
            mileage_estimate=self.mileage_estimate,
        )
        return warfare.run_warfare_assessment()

    def _run_seer(self):
        from core.hnc_seer import HNCSeer, MonthlySnapshot
        if self.monthly_data:
            seer = HNCSeer(monthly_data=self.monthly_data)
        else:
            # Generate approximate monthly data from annual figures
            months = []
            for i in range(9):  # Apr-Dec
                month_num = 4 + i
                if month_num > 12:
                    month_num -= 12
                months.append(MonthlySnapshot(
                    month=month_num,
                    year=2025 if month_num >= 4 else 2026,
                    gross_income=self.gross_income / 12,
                    expenses=self.total_expenses / 12,
                    net_profit=self.net_profit / 12,
                    cis_deducted=self.cis_deducted / 12,
                ))
            seer = HNCSeer(monthly_data=months)
        return seer.predict()

    def _run_scanner(self):
        from core.hnc_deep_scanner import HNCDeepScanner
        scanner = HNCDeepScanner(tax_rate=0.20)
        if self.transactions:
            return scanner.scan_all(self.transactions)
        else:
            # Demo with representative transactions
            demo_txns = [
                {"date": "2025-06-01", "description": "GROVE BUILDERS CIS", "amount": 5666, "category": "income"},
                {"date": "2025-06-05", "description": "TRAVIS PERKINS", "amount": 800, "category": "cost_of_sales"},
                {"date": "2025-06-10", "description": "BP FUEL", "amount": 65, "category": "motor"},
                {"date": "2025-06-15", "description": "EE MOBILE", "amount": 45, "category": "uncategorised"},
            ]
            return scanner.scan_all(demo_txns)

    def _run_lattice(self):
        from core.hnc_lattice import HNCLattice
        lattice = HNCLattice(
            gross_income=self.gross_income,
            net_profit=self.net_profit,
            cis_deducted=self.cis_deducted,
        )
        return lattice.find_optimum()

    def _run_consciousness(self):
        from core.hnc_consciousness import HNCConsciousness
        consciousness = HNCConsciousness(
            turnover=self.gross_income,
            cost_of_sales=self.cost_of_sales,
            other_direct=self.other_direct,
            motor=self.motor,
            admin=self.admin,
            other_expenses=self.other_expenses,
            net_profit=self.net_profit,
            cis_deducted=self.cis_deducted,
        )
        return consciousness.assess()

    def _run_metacognition(self):
        from core.hnc_metacognition import HNCMetacognition
        meta = HNCMetacognition()
        return meta.analyse_full_position(
            net_profit=self.net_profit,
            total_income=self.gross_income,
            total_expenses=self.total_expenses,
            motor_expenses=self.motor,
            cis_deducted=self.cis_deducted,
            cis_citb=0,
            drawings=0,
        )

    def _run_intelligence(self):
        from core.hnc_intelligence_registry import HNCIntelligenceRegistry
        registry = HNCIntelligenceRegistry(
            net_profit=self.net_profit,
            total_income=self.gross_income,
            total_expenses=self.total_expenses,
            motor_expenses=self.motor,
            cis_deducted=self.cis_deducted,
        )
        return registry.run_all_systems()

    def _run_strategy(self):
        from core.tax_strategy import TaxStrategy
        strategy = TaxStrategy(
            net_profit=self.net_profit,
            total_income=self.gross_income,
            total_expenses=self.total_expenses,
            motor_expenses=self.motor,
            cis_deducted=self.cis_deducted,
        )
        return strategy.run_all_strategies()

    def _run_auris_throne(self):
        from core.hnc_auris_throne import get_hnc_auris_throne
        throne = get_hnc_auris_throne()
        return throne.assess()

    def _run_auris_nodes(self):
        from core.hnc_auris_nodes import HNCAurisEngine
        engine = HNCAurisEngine()
        # Classify a representative transaction to demonstrate the 9-node system
        result = engine.classify(
            description="GROVE BUILDERS CIS PAYMENT",
            amount=5_666.67,
            turnover=self.gross_income,
            balance=self.net_profit,
        )
        return result

    def _run_auris_validator(self):
        from core.hnc_auris_validator import HNCAurisValidator
        validator = HNCAurisValidator(sector="construction_subcontractor")
        return validator.validate_return(
            turnover=self.gross_income,
            cost_of_sales=self.cost_of_sales,
            other_direct=self.other_direct,
            motor=self.motor,
            admin=self.admin,
            other_expenses=self.other_expenses,
            net_profit=self.net_profit,
            cis_deducted=self.cis_deducted,
        )


# ═══════════════════════════════════════════════════════════════════
# DEMO / TEST
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("THE HNC ACCOUNTANT — UNIFIED TAX INTELLIGENCE ENGINE")
    print("11 Systems. 1 Verdict. Maximum Legal Savings.")
    print("=" * 70)

    engine = HNCUnifiedEngine(
        gross_income=51_000,
        net_profit=25_000,
        cis_deducted=10_200,
        total_expenses=26_000,
        cost_of_sales=8_000,
        other_direct=5_000,
        motor=3_000,
        admin=2_000,
        other_expenses=1_500,
        mileage_estimate=8_000,
    )

    verdict = engine.run()

    print(f"\n{'=' * 70}")
    print("UNIFIED VERDICT")
    print(f"{'=' * 70}")

    print(f"\n  SYSTEM HEALTH: {verdict.systems_loaded}/{verdict.systems_loaded + verdict.systems_failed} systems online")
    for s in verdict.system_statuses:
        status = "ONLINE" if s.loaded else f"FAILED: {s.error}"
        print(f"    {s.name:25s} [{status}]")

    print(f"\n  POSITION:")
    print(f"    Gross Income:     £{verdict.gross_income:>10,.0f}")
    print(f"    Total Expenses:   £{verdict.total_expenses:>10,.0f}")
    print(f"    Net Profit:       £{verdict.net_profit:>10,.0f}")
    print(f"    CIS Deducted:     £{verdict.cis_deducted:>10,.0f}")

    print(f"\n  NAIVE LIABILITY (what a normal accountant files):")
    print(f"    Income Tax:       £{verdict.naive_tax_liability:>10,.2f}")
    print(f"    National Ins:     £{verdict.naive_ni_liability:>10,.2f}")
    print(f"    Total:            £{verdict.naive_total:>10,.2f}")

    print(f"\n  OPTIMISED LIABILITY (what WE file):")
    print(f"    After optimisation: £{verdict.optimised_total:>10,.2f}")
    print(f"    CIS Credit:         £{verdict.cis_credit:>10,.2f}")
    if verdict.refund_due > 0:
        print(f"    *** REFUND DUE:     £{verdict.refund_due:>10,.2f} ***")
    else:
        print(f"    NET TO PAY:         £{verdict.net_liability:>10,.2f}")

    print(f"\n  SAVINGS:")
    print(f"    Total Annual:     £{verdict.total_annual_saving:>10,.2f} ({verdict.saving_percentage:.0f}%)")
    print(f"    Bulletproof:      £{verdict.bulletproof_saving:>10,.2f}")
    print(f"    Needs Action:     £{verdict.action_needed_saving:>10,.2f}")

    print(f"\n  INTELLIGENCE:")
    print(f"    Weapons:          {verdict.weapons_count}")
    print(f"    Threat Level:     {verdict.threat_level}")
    print(f"    Defence Ready:    {verdict.defence_readiness:.0%}")
    print(f"    Prediction:       {verdict.prediction_confidence} ({verdict.months_of_data} months)")
    print(f"    Missed deductions:£{verdict.missed_deductions:>10,.2f}")
    print(f"    Invisible saves:  £{verdict.invisible_expenses:>10,.2f}")
    print(f"    Lattice efficiency: {verdict.lattice_efficiency:.1%}")
    print(f"    Compounds:        {verdict.compound_bonuses}")

    print(f"\n  SELF-AUDIT:")
    print(f"    Verdict:          {verdict.conscience_verdict}")
    print(f"    Audit Score:      {verdict.self_audit_score}")
    print(f"    Risk:             {verdict.overall_risk:.1%}")
    print(f"    At Risk:          £{verdict.at_risk_amount:>10,.2f}")

    print(f"\n  AURIS THRONE (Fiscal Environment):")
    print(f"    Advisory:         {verdict.fiscal_advisory}")
    print(f"    Pressure Λ(t):    {verdict.fiscal_pressure:.3f}")
    print(f"    Gate Open:        {verdict.fiscal_gate_open}")
    if verdict.fiscal_warnings:
        for w in verdict.fiscal_warnings[:3]:
            print(f"    Warning:          {w}")

    print(f"\n  AURIS NODES (9-Node Classification):")
    print(f"    Sample Γ:         {verdict.auris_sample_gamma:.3f}")
    print(f"    Action:           {verdict.auris_sample_action}")
    print(f"    Nodes Online:     {verdict.auris_nodes_online}")

    print(f"\n  AURIS VALIDATOR (SA103 Validation):")
    print(f"    Coherence:        {verdict.validator_coherence:.1%}")
    print(f"    Benchmark Lock:   {verdict.validator_benchmark_locked}")
    print(f"    Passed:           {verdict.validator_passed}")
    print(f"    Hard Fails:       {verdict.validator_hard_fails}")
    print(f"    Ready to File:    {verdict.validator_ready_to_file}")

    print(f"\n  MONTHLY RESERVE: £{verdict.monthly_reserve_needed:,.0f}")

    if verdict.payment_schedule:
        print(f"\n  PAYMENT SCHEDULE:")
        for p in verdict.payment_schedule:
            print(f"    {p['date']}: £{p['amount']:,.2f} — {p['description']}")

    print(f"\n{'─' * 70}")
    print("BOTTOM LINE")
    print(f"{'─' * 70}")
    print(f"  {verdict.bottom_line}")

    if verdict.immediate_actions:
        print(f"\n{'─' * 70}")
        print("IMMEDIATE ACTIONS")
        print(f"{'─' * 70}")
        for action in verdict.immediate_actions:
            print(f"  → {action}")

    print(f"\n{'─' * 70}")
    print("Legal authority: IRC v Duke of Westminster [1936] AC 1")
    print("Every optimisation uses legislation as Parliament enacted it.")
    print(f"{'─' * 70}")
