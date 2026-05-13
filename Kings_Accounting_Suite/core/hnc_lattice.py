"""
HNC LATTICE — hnc_lattice.py
==============================
Adapted from Aureon's aureon_lattice.py (1,042 lines).

In Aureon, the Lattice is the multi-dimensional decision grid.
Every trading signal passes through the Lattice, which weighs
multiple strategies simultaneously and finds the OPTIMAL combination.
Not just the best single strategy — the best MIX of strategies.

For the HNC Accountant, the Lattice does the same for tax:
    - Every expense, deduction, and relief is a "signal"
    - The Lattice weighs them ALL simultaneously
    - It finds combinations that compound (pension + mileage + home office)
    - It detects conflicts (can't claim simplified AND actual vehicle costs)
    - It scores the total position and finds the GLOBAL OPTIMUM

AUREON LATTICE               →  HNC TAX LATTICE
──────────────────────────────────────────────────
Signal Grid                  →  Deduction Grid
Multi-Strategy Weighting     →  Multi-Relief Weighting
Conflict Detection           →  Mutual Exclusion Detection
Compound Edge                →  Compound Tax Benefit
Optimal Combination          →  Optimal Tax Position
Lattice Score                →  Net Tax Efficiency Score
Phi Harmonics                →  Tax Band Harmonics

The Lattice answers: "Given ALL available reliefs and deductions,
what is the mathematically optimal combination?"

A normal accountant applies reliefs one at a time.
The Lattice optimises them ALL simultaneously.

Aureon Creator / Aureon Research — April 2026
"""

from __future__ import annotations
import logging
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum
from itertools import combinations

logger = logging.getLogger("hnc_lattice")

PHI = (1 + math.sqrt(5)) / 2  # 1.618


# ═══════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════

class NodeType(Enum):
    """Types of lattice nodes"""
    DEDUCTION = "DEDUCTION"        # Reduces taxable profit
    ALLOWANCE = "ALLOWANCE"        # Reduces tax liability directly
    CREDIT = "CREDIT"              # Offset against liability (CIS)
    TIMING = "TIMING"              # When to claim
    STRUCTURAL = "STRUCTURAL"      # How to structure


@dataclass
class LatticeNode:
    """A single node in the optimisation lattice"""
    name: str
    node_type: NodeType
    annual_value: float            # £ value of deduction/credit
    tax_saving: float              # £ tax saved
    confidence: float              # 0-1 how certain we are
    legal_basis: str
    auto_apply: bool
    conflicts_with: Set[str] = field(default_factory=set)
    requires: Set[str] = field(default_factory=set)
    compounds_with: Set[str] = field(default_factory=set)
    notes: str = ""


@dataclass
class LatticeEdge:
    """Connection between two nodes"""
    from_node: str
    to_node: str
    relationship: str              # "conflicts", "compounds", "requires"
    impact: float                  # How the connection affects value


@dataclass
class LatticePosition:
    """A complete tax position evaluated by the lattice"""
    active_nodes: List[str]        # Which strategies are active
    total_deductions: float
    total_tax_saving: float
    total_credits: float
    net_liability: float
    efficiency_score: float        # 0-1
    conflicts_detected: List[str]
    compound_bonuses: List[str]
    feasible: bool                 # No mutual exclusions violated


@dataclass
class LatticeOptimum:
    """The global optimum found by the lattice"""
    best_position: LatticePosition
    positions_evaluated: int
    naive_liability: float
    optimised_liability: float
    total_saving: float
    saving_percentage: float
    active_strategies: List[LatticeNode]
    inactive_strategies: List[LatticeNode]
    compound_effects: List[str]
    report: str


# ═══════════════════════════════════════════════════════════════════
# MUTUAL EXCLUSION RULES
# ═══════════════════════════════════════════════════════════════════

MUTUAL_EXCLUSIONS = {
    # Can't claim simplified mileage AND actual vehicle costs
    ("simplified_mileage", "actual_vehicle_costs"),
    # Can't claim simplified home AND actual home
    ("simplified_home", "actual_home_costs"),
    # Can't claim flat rate scheme AND standard VAT
    ("flat_rate_vat", "standard_vat"),
    # Can't claim trading allowance AND business expenses
    ("trading_allowance", "full_expenses"),
}

# Compounds: strategies that work better together
COMPOUND_RULES = {
    # Pension reduces income → may drop tax band → NI also lower
    ("pension_relief", "basic_rate_retention"): 1.15,  # 15% bonus
    # CIS credit + low liability = refund
    ("cis_credit", "expense_maximisation"): 1.10,
    # Home office + phone = admin deduction block
    ("home_office", "phone_broadband"): 1.05,
    # Mileage + training = work-related travel block
    ("simplified_mileage", "training_cpd"): 1.05,
}


# ═══════════════════════════════════════════════════════════════════
# THE LATTICE ENGINE
# ═══════════════════════════════════════════════════════════════════

class HNCLattice:
    """
    Multi-Strategy Tax Optimisation Lattice.

    Adapted from Aureon Lattice: replaces trading signal grid
    with tax deduction grid. Same simultaneous optimisation,
    same conflict detection, same compound edge identification.
    """

    def __init__(
        self,
        gross_income: float = 51_000,
        net_profit: float = 25_000,
        cis_deducted: float = 10_200,
    ):
        self.gross_income = gross_income
        self.net_profit = net_profit
        self.cis_deducted = cis_deducted
        self.nodes: Dict[str, LatticeNode] = {}
        self.edges: List[LatticeEdge] = []

        self._build_default_lattice()

    def _build_default_lattice(self):
        """Build the default lattice nodes for a construction subcontractor."""

        pa = 12_570
        basic_band = 37_700
        basic_rate = 0.20
        higher_rate = 0.40
        ni_rate = 0.06

        taxable = max(0, self.net_profit - pa)
        in_higher = taxable > basic_band

        marginal_rate = higher_rate if in_higher else basic_rate
        effective_rate = marginal_rate + ni_rate

        # ── CIS Credit ──
        self.nodes["cis_credit"] = LatticeNode(
            name="CIS Tax Credit",
            node_type=NodeType.CREDIT,
            annual_value=self.cis_deducted,
            tax_saving=self.cis_deducted,
            confidence=1.0,
            legal_basis="Finance Act 2004 s.62",
            auto_apply=True,
            notes="Tax already paid at source. Pound-for-pound offset."
        )

        # ── Pension Relief ──
        if in_higher:
            optimal_pension = taxable - basic_band
            pension_saving = optimal_pension * (higher_rate - basic_rate) + optimal_pension * ni_rate
        else:
            optimal_pension = min(5_000, taxable)
            pension_saving = optimal_pension * effective_rate

        self.nodes["pension_relief"] = LatticeNode(
            name="Pension Contribution",
            node_type=NodeType.DEDUCTION,
            annual_value=optimal_pension,
            tax_saving=pension_saving,
            confidence=0.95,
            legal_basis="Finance Act 2004 Part 4",
            auto_apply=False,
            compounds_with={"basic_rate_retention"},
            notes=f"Contribute £{optimal_pension:,.0f} to SIPP."
        )

        # ── Marriage Allowance ──
        ma_value = 1_260
        ma_saving = ma_value * basic_rate  # £252
        self.nodes["marriage_allowance"] = LatticeNode(
            name="Marriage Allowance",
            node_type=NodeType.ALLOWANCE,
            annual_value=ma_value,
            tax_saving=ma_saving,
            confidence=0.90,
            legal_basis="ITA 2007 s.55B",
            auto_apply=False,
            notes="Transfer £1,260 from spouse. Backdate 4 years."
        )

        # ── Simplified Mileage ──
        miles = 8_000
        mileage_value = min(miles, 10_000) * 0.45 + max(0, miles - 10_000) * 0.25
        mileage_saving = mileage_value * marginal_rate
        self.nodes["simplified_mileage"] = LatticeNode(
            name="Simplified Mileage (45p/25p)",
            node_type=NodeType.DEDUCTION,
            annual_value=mileage_value,
            tax_saving=mileage_saving,
            confidence=0.85,
            legal_basis="ITTOIA 2005 s.94D",
            auto_apply=False,
            conflicts_with={"actual_vehicle_costs"},
            compounds_with={"training_cpd"},
            notes="Need mileage log."
        )

        # ── Actual Vehicle Costs ──
        actual_vehicle = 3_500  # Estimate: fuel + insurance + repairs
        actual_saving = actual_vehicle * marginal_rate
        self.nodes["actual_vehicle_costs"] = LatticeNode(
            name="Actual Vehicle Costs",
            node_type=NodeType.DEDUCTION,
            annual_value=actual_vehicle,
            tax_saving=actual_saving,
            confidence=0.80,
            legal_basis="ITTOIA 2005 s.34",
            auto_apply=False,
            conflicts_with={"simplified_mileage"},
            notes="Need all receipts. Compare with mileage."
        )

        # ── Home Office (Simplified) ──
        home_simplified = 312  # £6/week
        self.nodes["simplified_home"] = LatticeNode(
            name="Home Office (Flat Rate)",
            node_type=NodeType.DEDUCTION,
            annual_value=home_simplified,
            tax_saving=home_simplified * marginal_rate,
            confidence=1.0,
            legal_basis="ITTOIA 2005 s.94G",
            auto_apply=True,
            conflicts_with={"actual_home_costs"},
            compounds_with={"phone_broadband"},
        )

        # ── Home Office (Actual) ──
        home_actual = 960  # £80/month
        self.nodes["actual_home_costs"] = LatticeNode(
            name="Home Office (Actual Costs)",
            node_type=NodeType.DEDUCTION,
            annual_value=home_actual,
            tax_saving=home_actual * marginal_rate,
            confidence=0.75,
            legal_basis="ITTOIA 2005 s.34",
            auto_apply=False,
            conflicts_with={"simplified_home"},
            compounds_with={"phone_broadband"},
            notes="Needs utility bills, floor plan."
        )

        # ── Phone & Broadband ──
        phone_value = 360
        self.nodes["phone_broadband"] = LatticeNode(
            name="Phone & Broadband",
            node_type=NodeType.DEDUCTION,
            annual_value=phone_value,
            tax_saving=phone_value * marginal_rate,
            confidence=0.90,
            legal_basis="ITTOIA 2005 s.34",
            auto_apply=True,
            compounds_with={"simplified_home", "actual_home_costs"},
        )

        # ── PPE ──
        ppe_value = 250
        self.nodes["ppe_clothing"] = LatticeNode(
            name="PPE & Protective Clothing",
            node_type=NodeType.DEDUCTION,
            annual_value=ppe_value,
            tax_saving=ppe_value * marginal_rate,
            confidence=0.95,
            legal_basis="BIM37900",
            auto_apply=True,
        )

        # ── Training ──
        training_value = 500
        self.nodes["training_cpd"] = LatticeNode(
            name="Training & CPD",
            node_type=NodeType.DEDUCTION,
            annual_value=training_value,
            tax_saving=training_value * marginal_rate,
            confidence=0.90,
            legal_basis="BIM35660",
            auto_apply=True,
            compounds_with={"simplified_mileage"},
        )

        # ── Professional Subs ──
        subs_value = 200
        self.nodes["professional_subs"] = LatticeNode(
            name="Professional Subscriptions",
            node_type=NodeType.DEDUCTION,
            annual_value=subs_value,
            tax_saving=subs_value * marginal_rate,
            confidence=0.95,
            legal_basis="ITA 2007 s.344",
            auto_apply=True,
        )

        # ── Bank Charges ──
        bank_value = 120
        self.nodes["bank_charges"] = LatticeNode(
            name="Bank Charges",
            node_type=NodeType.DEDUCTION,
            annual_value=bank_value,
            tax_saving=bank_value * marginal_rate,
            confidence=0.95,
            legal_basis="BIM45800",
            auto_apply=True,
        )

        # ── Accountancy ──
        acct_value = 500
        self.nodes["accountancy_fees"] = LatticeNode(
            name="Accountancy Fees",
            node_type=NodeType.DEDUCTION,
            annual_value=acct_value,
            tax_saving=acct_value * marginal_rate,
            confidence=0.95,
            legal_basis="BIM42501",
            auto_apply=True,
        )

        # ── Small Tools ──
        tools_value = 300
        self.nodes["small_tools"] = LatticeNode(
            name="Small Tools & Equipment",
            node_type=NodeType.DEDUCTION,
            annual_value=tools_value,
            tax_saving=tools_value * marginal_rate,
            confidence=0.90,
            legal_basis="BIM46400",
            auto_apply=True,
        )

        # ── Loss Relief ──
        self.nodes["loss_relief"] = LatticeNode(
            name="Sideways Loss Relief",
            node_type=NodeType.DEDUCTION,
            annual_value=0,  # Depends on actual food trade losses
            tax_saving=0,
            confidence=0.70,
            legal_basis="ITA 2007 s.64",
            auto_apply=True,
            notes="If Food Venture makes a loss, offset against construction."
        )

        # ── Basic Rate Retention (virtual node) ──
        self.nodes["basic_rate_retention"] = LatticeNode(
            name="Basic Rate Band Retention",
            node_type=NodeType.STRUCTURAL,
            annual_value=0,
            tax_saving=0,
            confidence=0.80,
            legal_basis="N/A — structural optimisation",
            auto_apply=False,
            compounds_with={"pension_relief"},
            notes="Keep taxable income below £50,270."
        )

        # Build edges from node relationships
        self._build_edges()

    def _build_edges(self):
        """Build lattice edges from node conflict/compound relationships."""
        self.edges = []
        for name, node in self.nodes.items():
            for conflict in node.conflicts_with:
                if conflict in self.nodes:
                    self.edges.append(LatticeEdge(
                        from_node=name,
                        to_node=conflict,
                        relationship="conflicts",
                        impact=-1.0,
                    ))
            for compound in node.compounds_with:
                if compound in self.nodes:
                    # Find compound bonus
                    key1 = (name, compound)
                    key2 = (compound, name)
                    bonus = COMPOUND_RULES.get(key1, COMPOUND_RULES.get(key2, 1.05))
                    self.edges.append(LatticeEdge(
                        from_node=name,
                        to_node=compound,
                        relationship="compounds",
                        impact=bonus,
                    ))

    def _check_conflicts(self, active: Set[str]) -> List[str]:
        """Check for mutual exclusion violations."""
        conflicts = []
        for a, b in MUTUAL_EXCLUSIONS:
            if a in active and b in active:
                conflicts.append(f"Cannot use both '{a}' and '{b}'")
        return conflicts

    def _calculate_compounds(self, active: Set[str]) -> Tuple[float, List[str]]:
        """Calculate compound bonuses for active strategies."""
        total_bonus = 0
        descriptions = []
        for (a, b), multiplier in COMPOUND_RULES.items():
            if a in active and b in active:
                node_a = self.nodes.get(a)
                node_b = self.nodes.get(b)
                if node_a and node_b:
                    combined = node_a.tax_saving + node_b.tax_saving
                    bonus = combined * (multiplier - 1)
                    total_bonus += bonus
                    descriptions.append(
                        f"{node_a.name} + {node_b.name}: "
                        f"£{bonus:,.0f} compound bonus ({multiplier:.0%})"
                    )
        return total_bonus, descriptions

    def _calc_tax(self, profit: float) -> float:
        """Calculate tax + NI on profit."""
        pa = 12_570
        basic_band = 37_700
        taxable = max(0, profit - pa)
        if taxable <= basic_band:
            tax = taxable * 0.20
        else:
            tax = basic_band * 0.20 + (taxable - basic_band) * 0.40
        ni = max(0, profit - pa) * 0.06
        if profit >= pa:
            ni += 3.45 * 52  # Class 2
        return tax + ni

    def evaluate_position(self, active_names: Set[str]) -> LatticePosition:
        """Evaluate a specific combination of active strategies."""
        conflicts = self._check_conflicts(active_names)
        feasible = len(conflicts) == 0

        active_nodes = [self.nodes[n] for n in active_names if n in self.nodes]

        total_deductions = sum(
            n.annual_value for n in active_nodes
            if n.node_type == NodeType.DEDUCTION
        )
        total_credits = sum(
            n.annual_value for n in active_nodes
            if n.node_type == NodeType.CREDIT
        )
        total_saving = sum(n.tax_saving for n in active_nodes)

        # Compound bonuses
        compound_bonus, compound_desc = self._calculate_compounds(active_names)
        total_saving += compound_bonus

        # Net liability
        reduced_profit = max(0, self.net_profit - total_deductions)
        raw_liability = self._calc_tax(reduced_profit)
        net_liability = max(0, raw_liability - total_credits)

        # Efficiency score: what proportion of the naive tax did we eliminate?
        naive = self._calc_tax(self.net_profit)
        efficiency = 1 - (net_liability / naive) if naive > 0 else 0

        return LatticePosition(
            active_nodes=list(active_names),
            total_deductions=round(total_deductions, 2),
            total_tax_saving=round(total_saving, 2),
            total_credits=round(total_credits, 2),
            net_liability=round(net_liability, 2),
            efficiency_score=round(min(1.0, efficiency), 3),
            conflicts_detected=conflicts,
            compound_bonuses=compound_desc,
            feasible=feasible,
        )

    def find_optimum(self) -> LatticeOptimum:
        """
        Find the global optimum across all valid strategy combinations.

        This is the Lattice's core function. It evaluates every feasible
        combination and returns the one with the lowest net liability.
        """
        all_names = set(self.nodes.keys())
        best_position = None
        positions_evaluated = 0

        # For small lattices, evaluate all combinations
        # For large ones, use greedy + pruning
        if len(all_names) <= 20:
            # Evaluate all valid combinations
            for r in range(len(all_names) + 1):
                for combo in combinations(all_names, r):
                    combo_set = set(combo)
                    position = self.evaluate_position(combo_set)
                    positions_evaluated += 1
                    if position.feasible:
                        if best_position is None:
                            best_position = position
                        elif position.net_liability < best_position.net_liability:
                            best_position = position
                        elif (position.net_liability == best_position.net_liability
                              and position.total_tax_saving > best_position.total_tax_saving):
                            # Same net liability but more total saving = better defence position
                            best_position = position
        else:
            # Greedy: start with all, remove conflicts
            active = set(all_names)
            conflicts = self._check_conflicts(active)
            while conflicts:
                # Remove the lower-value node from each conflict
                for conflict_desc in conflicts:
                    for a, b in MUTUAL_EXCLUSIONS:
                        if a in active and b in active:
                            node_a = self.nodes.get(a)
                            node_b = self.nodes.get(b)
                            if node_a and node_b:
                                if node_a.tax_saving >= node_b.tax_saving:
                                    active.discard(b)
                                else:
                                    active.discard(a)
                conflicts = self._check_conflicts(active)
            best_position = self.evaluate_position(active)
            positions_evaluated = 1

        if best_position is None:
            best_position = self.evaluate_position(set())

        naive_liability = self._calc_tax(self.net_profit)
        total_saving = naive_liability - best_position.net_liability

        # Active vs inactive
        active_nodes = [self.nodes[n] for n in best_position.active_nodes if n in self.nodes]
        inactive_names = all_names - set(best_position.active_nodes)
        inactive_nodes = [self.nodes[n] for n in inactive_names if n in self.nodes]

        # Report
        report = (
            f"LATTICE OPTIMISATION COMPLETE\n"
            f"Evaluated {positions_evaluated:,} combinations\n"
            f"Naive liability:     £{naive_liability:,.2f}\n"
            f"Optimised liability: £{best_position.net_liability:,.2f}\n"
            f"Total saving:        £{total_saving:,.2f} ({(total_saving/naive_liability*100) if naive_liability > 0 else 0:.1f}%)\n"
            f"Efficiency score:    {best_position.efficiency_score:.1%}\n"
            f"Active strategies:   {len(active_nodes)}\n"
            f"Compounds detected:  {len(best_position.compound_bonuses)}"
        )

        return LatticeOptimum(
            best_position=best_position,
            positions_evaluated=positions_evaluated,
            naive_liability=round(naive_liability, 2),
            optimised_liability=round(best_position.net_liability, 2),
            total_saving=round(total_saving, 2),
            saving_percentage=round(total_saving / naive_liability * 100, 1) if naive_liability > 0 else 0,
            active_strategies=active_nodes,
            inactive_strategies=inactive_nodes,
            compound_effects=best_position.compound_bonuses,
            report=report,
        )


# ═══════════════════════════════════════════════════════════════════
# DEMO / TEST
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("HNC LATTICE — MULTI-STRATEGY TAX OPTIMISATION")
    print("Adapted from Aureon Lattice (1,042 lines)")
    print("=" * 70)

    lattice = HNCLattice(
        gross_income=51_000,
        net_profit=25_000,
        cis_deducted=10_200,
    )

    optimum = lattice.find_optimum()

    print(f"\n{optimum.report}")

    print(f"\n{'─' * 70}")
    print("ACTIVE STRATEGIES")
    print(f"{'─' * 70}")
    for node in sorted(optimum.active_strategies, key=lambda n: -n.tax_saving):
        auto = "AUTO" if node.auto_apply else "ACTION"
        print(f"  [{auto}] {node.name:35s}  Deduction: £{node.annual_value:>7,.0f}  Saving: £{node.tax_saving:>7,.0f}")

    if optimum.inactive_strategies:
        print(f"\n{'─' * 70}")
        print("EXCLUDED STRATEGIES (conflicts or zero value)")
        print(f"{'─' * 70}")
        for node in optimum.inactive_strategies:
            reason = "CONFLICT" if node.conflicts_with else "ZERO VALUE"
            print(f"  [{reason:12s}] {node.name:35s}  Would save: £{node.tax_saving:>7,.0f}")

    if optimum.compound_effects:
        print(f"\n{'─' * 70}")
        print("COMPOUND EFFECTS")
        print(f"{'─' * 70}")
        for effect in optimum.compound_effects:
            print(f"  {effect}")
