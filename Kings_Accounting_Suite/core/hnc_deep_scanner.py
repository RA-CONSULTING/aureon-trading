"""
HNC DEEP SCANNER — hnc_deep_scanner.py
========================================
Adapted from Aureon's aureon_deep_money_flow_analyzer.py (741 lines).

In Aureon, the Deep Money Flow Analyzer traces money through the
financial system — who moved it, where it went, why, and what
the downstream effects were. It follows every penny through time.

For the HNC Accountant, we flip it:
    - Instead of tracking WHERE money went (institutions/offshore),
      we track WHERE money CAME FROM (contractor → us) and WHERE
      WE SPENT IT (expenses → deductions → tax savings)
    - Instead of finding manipulation, we find MISSED DEDUCTIONS
    - Instead of tracing bot activity, we trace HMRC patterns
    - Instead of planetary damage, we calculate FISCAL DAMAGE to
      the taxpayer from missed reliefs

AUREON DEEP MONEY FLOW        →  HNC DEEP SCANNER
──────────────────────────────────────────────────────
Money Flow Events              →  Expense Flow Events
Perpetrator Network            →  Payee Network Intelligence
Extraction Methods             →  Deduction Methods
Flow Direction                 →  Tax Flow Direction
Planetary Effects              →  Taxpayer Fiscal Effects
Bot Correlations               →  HMRC Pattern Correlations
Historical Evidence Vault      →  Historical Expense Intelligence

The Deep Scanner answers: "For every pound that left your account,
did we extract the maximum tax benefit? If not, what did we miss?"

Every legitimate expense is a weapon. Every missed deduction is
money voluntarily given to the government.

Aureon Creator / Aureon Research — April 2026
"""

from __future__ import annotations
import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from datetime import date, datetime
from collections import defaultdict
from enum import Enum

logger = logging.getLogger("hnc_deep_scanner")


# ═══════════════════════════════════════════════════════════════════
# SCAN CATEGORIES
# ═══════════════════════════════════════════════════════════════════

class ScanResult(Enum):
    """Result of scanning a transaction"""
    FULLY_CLAIMED = "FULLY_CLAIMED"       # Maximum benefit already extracted
    UNDER_CLAIMED = "UNDER_CLAIMED"       # Partial benefit — more available
    MISSED = "MISSED"                     # Not claimed at all
    MISCLASSIFIED = "MISCLASSIFIED"       # Wrong category — losing benefit
    OVERCLAIMED = "OVERCLAIMED"           # Risk: claimed too aggressively
    NOT_DEDUCTIBLE = "NOT_DEDUCTIBLE"     # Genuinely personal / not allowable


class ExpenseCategory(Enum):
    """SA103 expense categories"""
    COST_OF_SALES = "cost_of_sales"       # Box 10
    CONSTRUCTION = "construction"          # Box 11
    OTHER_DIRECT = "other_direct"          # Box 12
    PREMISES = "premises"                  # Box 14
    ADMIN = "admin"                        # Box 15
    ADVERTISING = "advertising"            # Box 16
    BAD_DEBTS = "bad_debts"               # Box 17
    INTEREST = "interest"                  # Box 18
    OTHER_FINANCE = "other_finance"        # Box 19
    DEPRECIATION = "depreciation"          # Box 20 (disallowable, add back)
    OTHER_EXPENSES = "other_expenses"      # Box 21
    MOTOR = "motor"                        # Box 13 (auto via simplified)
    CAPITAL = "capital"                    # Capital allowances
    PRIVATE = "private"                    # Not deductible


# ═══════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════

@dataclass
class ExpenseScan:
    """Result of scanning a single expense transaction"""
    date: str
    description: str
    amount: float
    payee: str
    current_category: str
    scan_result: ScanResult
    optimal_category: str
    tax_benefit_current: float      # Tax saved with current classification
    tax_benefit_optimal: float      # Tax saved with optimal classification
    missed_saving: float            # Difference
    reasoning: str
    legal_basis: str
    action: str
    evidence_needed: List[str] = field(default_factory=list)


@dataclass
class PayeeIntel:
    """Intelligence on a specific payee"""
    name: str
    total_paid: float
    transaction_count: int
    likely_category: str
    confidence: float
    is_related_party: bool
    is_capital: bool
    optimal_treatment: str
    notes: str


@dataclass
class InvisibleExpense:
    """An expense that EXISTS but wasn't explicitly paid for — still deductible"""
    name: str
    annual_amount: float
    tax_saving: float
    legal_basis: str
    description: str
    auto_claim: bool
    evidence_needed: List[str]


@dataclass
class DeepScanVerdict:
    """Complete deep scan output"""
    total_transactions_scanned: int
    total_expenses_scanned: float
    fully_claimed: int
    under_claimed: int
    missed: int
    misclassified: int
    overclaimed: int
    total_missed_savings: float
    total_invisible_expenses: float
    invisible_tax_saving: float
    payee_network: List[PayeeIntel]
    problem_transactions: List[ExpenseScan]
    invisible_expenses: List[InvisibleExpense]
    scan_report: str


# ═══════════════════════════════════════════════════════════════════
# PAYEE INTELLIGENCE DATABASE
# ═══════════════════════════════════════════════════════════════════

KNOWN_PAYEES = {
    # Construction suppliers
    "travis perkins": {"category": "cost_of_sales", "type": "supplier", "capital": False},
    "jewson": {"category": "cost_of_sales", "type": "supplier", "capital": False},
    "screwfix": {"category": "cost_of_sales", "type": "supplier", "capital": False},
    "toolstation": {"category": "cost_of_sales", "type": "supplier", "capital": False},
    "wickes": {"category": "cost_of_sales", "type": "supplier", "capital": False},
    "b&q": {"category": "cost_of_sales", "type": "supplier", "capital": False},
    "selco": {"category": "cost_of_sales", "type": "supplier", "capital": False},
    "buildbase": {"category": "cost_of_sales", "type": "supplier", "capital": False},

    # Vehicle / fuel
    "bp": {"category": "motor", "type": "fuel", "capital": False},
    "shell": {"category": "motor", "type": "fuel", "capital": False},
    "texaco": {"category": "motor", "type": "fuel", "capital": False},
    "esso": {"category": "motor", "type": "fuel", "capital": False},
    "jet": {"category": "motor", "type": "fuel", "capital": False},
    "applegreen": {"category": "motor", "type": "fuel", "capital": False},
    "maxol": {"category": "motor", "type": "fuel", "capital": False},
    "halfords": {"category": "motor", "type": "repairs_or_capital", "capital": False},

    # Insurance
    "aviva": {"category": "admin", "type": "insurance", "capital": False},
    "axa": {"category": "admin", "type": "insurance", "capital": False},
    "direct line": {"category": "admin", "type": "insurance", "capital": False},
    "zurich": {"category": "admin", "type": "insurance", "capital": False},

    # Professional
    "citb": {"category": "other_expenses", "type": "training", "capital": False},
    "cscs": {"category": "other_expenses", "type": "training", "capital": False},
    "hmrc": {"category": "not_deductible", "type": "tax_payment", "capital": False},

    # Vehicle purchases — CAPITAL
    "close brothers": {"category": "capital", "type": "vehicle_finance", "capital": True},
    "black horse": {"category": "capital", "type": "vehicle_finance", "capital": True},

    # Telecoms
    "ee": {"category": "admin", "type": "phone", "capital": False},
    "vodafone": {"category": "admin", "type": "phone", "capital": False},
    "three": {"category": "admin", "type": "phone", "capital": False},
    "bt": {"category": "admin", "type": "broadband", "capital": False},
    "sky": {"category": "admin", "type": "broadband", "capital": False},
    "virgin media": {"category": "admin", "type": "broadband", "capital": False},

    # Food trade
    "booker": {"category": "cost_of_sales", "type": "food_wholesale", "capital": False},
    "musgrave": {"category": "cost_of_sales", "type": "food_wholesale", "capital": False},
    "brakes": {"category": "cost_of_sales", "type": "food_wholesale", "capital": False},
    "henderson": {"category": "cost_of_sales", "type": "food_wholesale", "capital": False},

    # Personal — NOT deductible
    "netflix": {"category": "private", "type": "entertainment", "capital": False},
    "spotify": {"category": "private", "type": "entertainment", "capital": False},
    "amazon prime": {"category": "private", "type": "entertainment", "capital": False},
    "sky sports": {"category": "private", "type": "entertainment", "capital": False},
}

# Patterns that suggest capital expenditure
CAPITAL_PATTERNS = [
    (r"(?i)vehicle|van|truck|car|transit", "Vehicle purchase — AIA or WDA"),
    (r"(?i)machinery|excavator|digger|mixer", "Plant/machinery — AIA"),
    (r"(?i)computer|laptop|ipad|tablet", "Computer equipment — AIA"),
    (r"(?i)trailer|scaffold", "Equipment — AIA"),
]

# Patterns that suggest personal use
PERSONAL_PATTERNS = [
    (r"(?i)tesco|asda|sainsbury|lidl|aldi", "Supermarket — personal unless food trade stock"),
    (r"(?i)primark|next clothing|h&m", "Clothing — personal unless PPE"),
    (r"(?i)holiday|hotel|airbnb", "Accommodation — personal unless work travel"),
    (r"(?i)restaurant|eating out|just eat|deliveroo", "Dining — personal unless client entertainment"),
]


# ═══════════════════════════════════════════════════════════════════
# INVISIBLE EXPENSES — Things You CAN Claim But Probably Aren't
# ═══════════════════════════════════════════════════════════════════

def get_invisible_expenses(
    has_home_office: bool = True,
    has_vehicle: bool = True,
    is_construction: bool = True,
    annual_mileage: int = 8_000,
) -> List[InvisibleExpense]:
    """
    Expenses that don't appear in bank statements but ARE deductible.
    Most people miss these. That's free money left on the table.
    """
    invisibles = []

    if has_home_office:
        invisibles.append(InvisibleExpense(
            name="Use of Home as Office",
            annual_amount=312,  # £6/week flat rate
            tax_saving=312 * 0.20,
            legal_basis="ITTOIA 2005 s.94G — simplified expenses",
            description=(
                "HMRC flat rate: £6/week for working from home. "
                "No receipts needed. No questions asked. £312/year."
            ),
            auto_claim=True,
            evidence_needed=[],
        ))
        # If actual costs are higher
        invisibles.append(InvisibleExpense(
            name="Use of Home (Actual Costs Alternative)",
            annual_amount=960,  # £80/month typical
            tax_saving=960 * 0.20,
            legal_basis="ITTOIA 2005 s.34 — proportional actual costs",
            description=(
                "Proportional share of rent/mortgage interest, utilities, council tax. "
                "Typically £60-120/month. Higher than flat rate but needs evidence."
            ),
            auto_claim=False,
            evidence_needed=["Utility bills", "Rent/mortgage statement", "Council tax bill", "Floor plan"],
        ))

    if has_vehicle and annual_mileage > 0:
        first_10k = min(annual_mileage, 10_000) * 0.45
        over_10k = max(0, annual_mileage - 10_000) * 0.25
        mileage_value = first_10k + over_10k
        invisibles.append(InvisibleExpense(
            name="Business Mileage Allowance",
            annual_amount=mileage_value,
            tax_saving=mileage_value * 0.20,
            legal_basis="ITTOIA 2005 s.94D — approved mileage rates",
            description=(
                f"{annual_mileage:,} miles @ HMRC approved rates. "
                f"Deduction: £{mileage_value:,.0f}. Covers fuel, insurance, depreciation."
            ),
            auto_claim=False,
            evidence_needed=["Mileage log (date, from, to, miles, purpose)"],
        ))

    if is_construction:
        invisibles.append(InvisibleExpense(
            name="PPE & Protective Clothing",
            annual_amount=250,
            tax_saving=250 * 0.20,
            legal_basis="ITTOIA 2005 s.34, BIM37900",
            description="Steel toe boots, hi-vis, hard hat, safety glasses. Essential for construction.",
            auto_claim=True,
            evidence_needed=["Receipts (or reasonable estimate if receipts lost)"],
        ))
        invisibles.append(InvisibleExpense(
            name="Small Tools & Equipment",
            annual_amount=300,
            tax_saving=300 * 0.20,
            legal_basis="ITTOIA 2005 s.34, BIM46400",
            description="Drill bits, saw blades, measuring tapes, hand tools under £100 each.",
            auto_claim=True,
            evidence_needed=["Receipts where available"],
        ))
        invisibles.append(InvisibleExpense(
            name="CSCS Card / Training Renewal",
            annual_amount=200,
            tax_saving=200 * 0.20,
            legal_basis="ITTOIA 2005 s.34, BIM35660",
            description="CSCS card, CITB courses, first aid training, SMSTS renewal.",
            auto_claim=True,
            evidence_needed=["Course certificates", "Payment confirmations"],
        ))

    # Universal invisible expenses
    invisibles.append(InvisibleExpense(
        name="Phone & Broadband (Business Proportion)",
        annual_amount=360,  # 60% of £600
        tax_saving=360 * 0.20,
        legal_basis="ITTOIA 2005 s.34",
        description="60% business use of phone (£50/month) = £360 deduction.",
        auto_claim=True,
        evidence_needed=["Phone bill", "Reasonable business use estimate"],
    ))
    invisibles.append(InvisibleExpense(
        name="Accountancy / Bookkeeping Fees",
        annual_amount=500,
        tax_saving=500 * 0.20,
        legal_basis="ITTOIA 2005 s.34, BIM42501",
        description="Cost of preparing accounts and tax return. Fully deductible.",
        auto_claim=True,
        evidence_needed=["Accountant's invoice"],
    ))
    invisibles.append(InvisibleExpense(
        name="Bank Charges & Interest",
        annual_amount=120,
        tax_saving=120 * 0.20,
        legal_basis="ITTOIA 2005 s.34, BIM45800",
        description="Business bank charges, overdraft interest, card fees.",
        auto_claim=True,
        evidence_needed=["Bank statements"],
    ))

    return invisibles


# ═══════════════════════════════════════════════════════════════════
# THE DEEP SCANNER ENGINE
# ═══════════════════════════════════════════════════════════════════

class HNCDeepScanner:
    """
    Deep Expense Scanner.

    Adapted from Aureon Deep Money Flow Analyzer.
    Scans every transaction, identifies missed deductions,
    misclassifications, and invisible expenses.

    The philosophy: Every pound of legitimate expense reduces tax.
    Missing a £100 expense costs you £20-40 in unnecessary tax.
    Over a career, that's tens of thousands given away for nothing.
    """

    def __init__(self, tax_rate: float = 0.20):
        self.tax_rate = tax_rate  # Marginal rate for savings calc

    def _match_payee(self, description: str) -> Optional[dict]:
        """Match a transaction description to known payee intelligence."""
        desc_lower = description.lower()
        for payee, intel in KNOWN_PAYEES.items():
            if payee in desc_lower:
                return {"name": payee, **intel}
        return None

    def _check_capital(self, description: str, amount: float) -> Optional[str]:
        """Check if a transaction looks like capital expenditure."""
        for pattern, note in CAPITAL_PATTERNS:
            if re.search(pattern, description):
                return note
        if amount >= 1_000:
            return "High value — check if capital expenditure (AIA eligible)"
        return None

    def _check_personal(self, description: str) -> Optional[str]:
        """Check if a transaction looks personal."""
        for pattern, note in PERSONAL_PATTERNS:
            if re.search(pattern, description):
                return note
        return None

    def scan_transaction(
        self,
        date_str: str,
        description: str,
        amount: float,
        current_category: str = "uncategorised",
    ) -> ExpenseScan:
        """Scan a single transaction for optimal tax treatment."""

        payee = self._match_payee(description)
        capital_check = self._check_capital(description, amount)
        personal_check = self._check_personal(description)

        # Determine scan result
        if personal_check and not payee:
            return ExpenseScan(
                date=date_str,
                description=description,
                amount=amount,
                payee=description[:40],
                current_category=current_category,
                scan_result=ScanResult.NOT_DEDUCTIBLE,
                optimal_category="private",
                tax_benefit_current=0,
                tax_benefit_optimal=0,
                missed_saving=0,
                reasoning=personal_check,
                legal_basis="ITTOIA 2005 s.34 — not wholly and exclusively for trade",
                action="Remove from business expenses if currently claimed.",
            )

        # Only flag capital if: (a) payee is known-capital, OR
        # (b) payee is unknown AND description/amount matches capital patterns
        is_known_revenue = payee and not payee.get("capital", False)
        if capital_check and not is_known_revenue and current_category not in ("capital", "depreciation"):
            aia_saving = amount * self.tax_rate
            current_saving = amount * self.tax_rate if current_category not in ("private", "not_deductible") else 0
            # Capital allowances give 100% AIA vs revenue deduction — same in year 1 but different treatment
            return ExpenseScan(
                date=date_str,
                description=description,
                amount=amount,
                payee=payee["name"] if payee else description[:40],
                current_category=current_category,
                scan_result=ScanResult.MISCLASSIFIED,
                optimal_category="capital",
                tax_benefit_current=current_saving,
                tax_benefit_optimal=aia_saving,
                missed_saving=max(0, aia_saving - current_saving),
                reasoning=f"Capital expenditure detected: {capital_check}. Should be AIA, not revenue.",
                legal_basis="CAA 2001 s.38A — Annual Investment Allowance",
                action="Reclassify as capital expenditure. Claim AIA for 100% first-year deduction.",
                evidence_needed=["Purchase invoice", "Proof of business use"],
            )

        if payee:
            optimal_cat = payee["category"]
            if optimal_cat == "not_deductible":
                return ExpenseScan(
                    date=date_str,
                    description=description,
                    amount=amount,
                    payee=payee["name"],
                    current_category=current_category,
                    scan_result=ScanResult.NOT_DEDUCTIBLE,
                    optimal_category="not_deductible",
                    tax_benefit_current=0,
                    tax_benefit_optimal=0,
                    missed_saving=0,
                    reasoning=f"{payee['name']} is a {payee['type']} — not deductible.",
                    legal_basis="N/A — not a business expense",
                    action="Ensure not claimed as business expense.",
                )

            current_saving = amount * self.tax_rate if current_category not in ("private", "not_deductible", "uncategorised") else 0
            optimal_saving = amount * self.tax_rate

            if current_category == optimal_cat:
                result = ScanResult.FULLY_CLAIMED
                missed = 0
            elif current_category in ("private", "not_deductible", "uncategorised"):
                result = ScanResult.MISSED
                missed = optimal_saving
            else:
                result = ScanResult.UNDER_CLAIMED if current_saving < optimal_saving else ScanResult.FULLY_CLAIMED
                missed = max(0, optimal_saving - current_saving)

            return ExpenseScan(
                date=date_str,
                description=description,
                amount=amount,
                payee=payee["name"],
                current_category=current_category,
                scan_result=result,
                optimal_category=optimal_cat,
                tax_benefit_current=current_saving,
                tax_benefit_optimal=optimal_saving,
                missed_saving=missed,
                reasoning=f"Payee: {payee['name']} ({payee['type']}). Optimal: {optimal_cat}.",
                legal_basis="ITTOIA 2005 s.34",
                action=f"Classify as {optimal_cat}" if missed > 0 else "Correctly classified.",
            )

        # Unknown payee — default scan
        current_saving = amount * self.tax_rate if current_category not in ("private", "not_deductible", "uncategorised") else 0
        return ExpenseScan(
            date=date_str,
            description=description,
            amount=amount,
            payee=description[:40],
            current_category=current_category,
            scan_result=ScanResult.FULLY_CLAIMED if current_saving > 0 else ScanResult.MISSED,
            optimal_category=current_category if current_saving > 0 else "review_needed",
            tax_benefit_current=current_saving,
            tax_benefit_optimal=amount * self.tax_rate,
            missed_saving=max(0, amount * self.tax_rate - current_saving),
            reasoning="Unknown payee — manual review recommended.",
            legal_basis="ITTOIA 2005 s.34",
            action="Review and classify" if current_saving == 0 else "OK",
        )

    def scan_all(
        self,
        transactions: List[dict],
        is_construction: bool = True,
        has_vehicle: bool = True,
        annual_mileage: int = 8_000,
    ) -> DeepScanVerdict:
        """
        Deep scan ALL transactions.

        Each transaction dict should have: date, description, amount, category
        """
        scans = []
        for txn in transactions:
            scan = self.scan_transaction(
                date_str=txn.get("date", ""),
                description=txn.get("description", ""),
                amount=abs(txn.get("amount", 0)),
                current_category=txn.get("category", "uncategorised"),
            )
            scans.append(scan)

        # Counts
        fully_claimed = sum(1 for s in scans if s.scan_result == ScanResult.FULLY_CLAIMED)
        under_claimed = sum(1 for s in scans if s.scan_result == ScanResult.UNDER_CLAIMED)
        missed = sum(1 for s in scans if s.scan_result == ScanResult.MISSED)
        misclassified = sum(1 for s in scans if s.scan_result == ScanResult.MISCLASSIFIED)
        overclaimed = sum(1 for s in scans if s.scan_result == ScanResult.OVERCLAIMED)

        total_missed = sum(s.missed_saving for s in scans)
        total_expenses = sum(s.amount for s in scans)

        # Build payee network
        payee_data: Dict[str, dict] = defaultdict(lambda: {"total": 0, "count": 0, "cats": []})
        for s in scans:
            p = payee_data[s.payee]
            p["total"] += s.amount
            p["count"] += 1
            if s.optimal_category not in p["cats"]:
                p["cats"].append(s.optimal_category)

        payee_network = []
        for name, data in sorted(payee_data.items(), key=lambda x: -x[1]["total"]):
            if data["count"] >= 1:
                matched = self._match_payee(name)
                payee_network.append(PayeeIntel(
                    name=name,
                    total_paid=data["total"],
                    transaction_count=data["count"],
                    likely_category=data["cats"][0] if data["cats"] else "unknown",
                    confidence=0.9 if matched else 0.5,
                    is_related_party=matched.get("type", "") in ("personal", "family") if matched else False,
                    is_capital=matched.get("capital", False) if matched else False,
                    optimal_treatment=data["cats"][0] if data["cats"] else "review",
                    notes=f"{data['count']} transactions, £{data['total']:,.0f} total",
                ))

        # Invisible expenses
        invisibles = get_invisible_expenses(
            has_home_office=True,
            has_vehicle=has_vehicle,
            is_construction=is_construction,
            annual_mileage=annual_mileage,
        )
        total_invisible = sum(i.annual_amount for i in invisibles)
        invisible_saving = sum(i.tax_saving for i in invisibles)

        # Problem transactions (missed, misclassified, under-claimed)
        problems = [s for s in scans if s.scan_result in (ScanResult.MISSED, ScanResult.MISCLASSIFIED, ScanResult.UNDER_CLAIMED)]

        # Build report
        report = (
            f"DEEP SCAN COMPLETE\n"
            f"Scanned {len(scans)} transactions (£{total_expenses:,.0f} total expenses)\n"
            f"Fully claimed: {fully_claimed} | Under-claimed: {under_claimed} | "
            f"Missed: {missed} | Misclassified: {misclassified} | Overclaimed: {overclaimed}\n"
            f"Missed savings from transactions: £{total_missed:,.0f}\n"
            f"Invisible expenses available: £{total_invisible:,.0f} (saving: £{invisible_saving:,.0f})\n"
            f"TOTAL RECOVERABLE: £{total_missed + invisible_saving:,.0f}"
        )

        return DeepScanVerdict(
            total_transactions_scanned=len(scans),
            total_expenses_scanned=total_expenses,
            fully_claimed=fully_claimed,
            under_claimed=under_claimed,
            missed=missed,
            misclassified=misclassified,
            overclaimed=overclaimed,
            total_missed_savings=total_missed,
            total_invisible_expenses=total_invisible,
            invisible_tax_saving=invisible_saving,
            payee_network=payee_network,
            problem_transactions=problems,
            invisible_expenses=invisibles,
            scan_report=report,
        )


# ═══════════════════════════════════════════════════════════════════
# DEMO / TEST
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("HNC DEEP SCANNER — EXPENSE MINING ENGINE")
    print("Adapted from Aureon Deep Money Flow Analyzer")
    print("=" * 70)

    # Sample transactions
    test_transactions = [
        {"date": "2025-04-15", "description": "TRAVIS PERKINS BELFAST", "amount": 847.50, "category": "cost_of_sales"},
        {"date": "2025-04-20", "description": "BP FUEL STATION", "amount": 65.00, "category": "motor"},
        {"date": "2025-05-01", "description": "CLOSE BROTHERS FINANCE", "amount": 450.00, "category": "other_direct"},
        {"date": "2025-05-10", "description": "JAMES LOGAN GROUNDWORKS", "amount": 4500.00, "category": "other_direct"},
        {"date": "2025-05-15", "description": "TESCO GROCERY", "amount": 85.00, "category": "cost_of_sales"},
        {"date": "2025-06-01", "description": "HMRC PAYMENT", "amount": 500.00, "category": "admin"},
        {"date": "2025-06-05", "description": "EE MOBILE", "amount": 45.00, "category": "uncategorised"},
        {"date": "2025-06-10", "description": "CITB TRAINING", "amount": 350.00, "category": "other_expenses"},
        {"date": "2025-06-15", "description": "SCREWFIX DIRECT", "amount": 125.00, "category": "cost_of_sales"},
        {"date": "2025-07-01", "description": "NETFLIX SUBSCRIPTION", "amount": 15.99, "category": "admin"},
    ]

    scanner = HNCDeepScanner(tax_rate=0.20)
    verdict = scanner.scan_all(test_transactions)

    print(f"\n{verdict.scan_report}")

    if verdict.problem_transactions:
        print(f"\n{'─' * 70}")
        print("PROBLEM TRANSACTIONS")
        print(f"{'─' * 70}")
        for p in verdict.problem_transactions:
            status_badge = {
                ScanResult.MISSED: "MISSED",
                ScanResult.MISCLASSIFIED: "WRONG",
                ScanResult.UNDER_CLAIMED: "UNDER",
            }.get(p.scan_result, "?")
            print(f"\n  [{status_badge}] {p.date} — {p.description} — £{p.amount:,.2f}")
            print(f"    Current: {p.current_category} → Optimal: {p.optimal_category}")
            print(f"    Missed saving: £{p.missed_saving:,.2f}")
            print(f"    Reason: {p.reasoning}")
            print(f"    Action: {p.action}")

    print(f"\n{'─' * 70}")
    print("INVISIBLE EXPENSES — Claim These!")
    print(f"{'─' * 70}")
    for inv in verdict.invisible_expenses:
        auto = "AUTO" if inv.auto_claim else "NEED EVIDENCE"
        print(f"  [{auto}] {inv.name}: £{inv.annual_amount:,.0f}/year → saves £{inv.tax_saving:,.0f}")
        print(f"    {inv.description}")

    print(f"\n{'─' * 70}")
    print("PAYEE NETWORK")
    print(f"{'─' * 70}")
    for p in verdict.payee_network[:10]:
        print(f"  {p.name:30s}  £{p.total_paid:>8,.0f}  ({p.transaction_count} txns)  → {p.likely_category}")
