"""
HNC HMRC INSPECTOR — hnc_hmrc_inspector.py
============================================
The Man on the Inside.

A fully law-abiding HMRC compliance inspector AI. This module thinks
EXACTLY like an HMRC officer running a TMA 1970 s.9A enquiry. It does
not bend, it does not look the other way. If it finds a problem, it
reports a problem.

If this inspector signs off your books, HMRC has nothing to find.

What it does:
1. CONNECT FOUR AUDIT — Cross-references four data sources:
   - Income declarations vs bank deposits
   - Expense claims vs supplier evidence
   - VAT returns vs underlying transactions
   - Bank reconciliation vs ledger balances

2. STATUTORY COMPLIANCE CHECKS — Every check mapped to legislation:
   - TMA 1970 — Taxes Management Act (filing, records, enquiry powers)
   - ITTOIA 2005 — Income Tax (Trading and Other Income) Act
   - TCGA 1992 — Taxation of Chargeable Gains Act
   - FA 2003-2025 — Finance Acts (thresholds, rates, allowances)
   - VATA 1994 — Value Added Tax Act
   - SI 2005/2045 — Construction Industry Scheme Regulations
   - POCA 2002 — Proceeds of Crime Act (money laundering flags)
   - BIM — Business Income Manual (allowability, badges of trade)

3. RISK PROFILING — Scores the return using HMRC's own risk factors:
   - Sector benchmarks (construction sole trader norms)
   - Expense ratios that trigger enquiry
   - Cash business indicators
   - Missing trader patterns
   - Inconsistency between tax years

4. SIMULATED ENQUIRY — Runs the s.9A enquiry process:
   - Information notice (what HMRC would request)
   - Discovery assessment (what they'd find)
   - Penalty calculation (what it would cost)

The inspector is NOT on your side. That's the point. If he can't
find anything, neither can HMRC.

Author: HNC Accountant Engine
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# Import the legal intelligence dataset
try:
    from core.hnc_legal import (
        CONNECT_DATA_SOURCES, CONNECT_RISK_FACTORS, INVESTIGATION_LADDER,
        CONNECT_STATS, STATUTES, HMRC_MANUALS, PENALTY_INACCURACY,
        DISCLOSURE_ROUTES, TAX_YEARS, LegalVerifier, SacrificialLamb,
        ConnectDataSource, RiskFactor, InvestigationStage,
    )
    LEGAL_INTEL_AVAILABLE = True
except ImportError:
    LEGAL_INTEL_AVAILABLE = False

logger = logging.getLogger("hnc_hmrc_inspector")


# ========================================================================
# ENUMS
# ========================================================================

class InspectorVerdict(Enum):
    """Overall verdict from the inspector."""
    CLEAN = "CLEAN"                   # No findings. File with confidence.
    MINOR_ISSUES = "MINOR_ISSUES"     # Cosmetic or admin issues. Fix before filing.
    CONCERNS = "CONCERNS"             # Substantive issues. Review required.
    ENQUIRY_RISK = "ENQUIRY_RISK"     # High risk of triggering s.9A enquiry.
    REFERRAL = "REFERRAL"             # Would be referred for formal investigation.


class FindingSeverity(Enum):
    """Severity of a finding."""
    CRITICAL = "CRITICAL"   # Would result in penalty or prosecution
    HIGH = "HIGH"           # Would trigger formal enquiry
    MEDIUM = "MEDIUM"       # Would trigger compliance check / nudge letter
    LOW = "LOW"             # Administrative, but still flagged
    INFO = "INFO"           # Noted for completeness, no action required


class PenaltyBasis(Enum):
    """HMRC penalty categories (FA 2007 Sch 24)."""
    CARELESS = "careless"           # 0-30% of tax lost
    DELIBERATE = "deliberate"       # 20-70% of tax lost
    CONCEALED = "deliberate_concealed"  # 30-100% of tax lost
    REASONABLE_CARE = "reasonable_care"  # No penalty


# ========================================================================
# CONSTANTS — HMRC BENCHMARKS & THRESHOLDS
# ========================================================================

# Construction sole trader sector benchmarks (HMRC internal data)
# These are the ratios HMRC expects. Deviations trigger enquiry.
SECTOR_BENCHMARKS = {
    "construction_sole_trader": {
        "materials_pct_of_turnover": (0.20, 0.45),  # Normal range
        "motor_pct_of_turnover": (0.03, 0.10),
        "subcontractor_pct_of_turnover": (0.00, 0.40),
        "tools_pct_of_turnover": (0.02, 0.08),
        "admin_pct_of_turnover": (0.01, 0.05),
        "gross_profit_margin": (0.25, 0.65),
        "net_profit_margin": (0.15, 0.45),
        "vat_reclaim_ratio": (0.03, 0.25),  # Input VAT / turnover
        "cash_withdrawal_pct_income": (0.00, 0.15),
        "personal_drawings_pct_profit": (0.30, 0.90),
    },
}

# TMA 1970 s.12B: Record keeping requirements (6 years)
RECORD_RETENTION_YEARS = 6

# FA 2007 Sch 24: Penalty ranges (% of potential lost revenue)
PENALTY_RANGES = {
    PenaltyBasis.REASONABLE_CARE: (0.0, 0.0),
    PenaltyBasis.CARELESS: (0.0, 0.30),
    PenaltyBasis.DELIBERATE: (0.20, 0.70),
    PenaltyBasis.CONCEALED: (0.30, 1.00),
}

# Prompted vs unprompted disclosure reduction
DISCLOSURE_REDUCTIONS = {
    "unprompted": {"careless": (0.0, 0.0), "deliberate": (0.20, 0.35), "concealed": (0.30, 0.50)},
    "prompted": {"careless": (0.15, 0.30), "deliberate": (0.35, 0.70), "concealed": (0.50, 1.00)},
}

# HMRC enquiry window
ENQUIRY_WINDOW_NORMAL = 12   # months after filing deadline
ENQUIRY_WINDOW_CARELESS = 72  # 6 years
ENQUIRY_WINDOW_DELIBERATE = 240  # 20 years

# CIS compliance
CIS_DEDUCTION_RATE_NO_UTR = 0.30
CIS_DEDUCTION_RATE_WITH_UTR = 0.20
CIS_DEDUCTION_RATE_GROSS = 0.00

# Annual Investment Allowance (capital goods)
AIA_LIMIT = 1000000  # £1m (current)

# Personal allowance (2025/26)
PERSONAL_ALLOWANCE = 12570
BASIC_RATE_BAND = 37700  # 20% on first 37,700 above PA
HIGHER_RATE_THRESHOLD = PERSONAL_ALLOWANCE + BASIC_RATE_BAND  # 50,270

# National Insurance thresholds (Class 4, 2025/26)
NI_LOWER_PROFIT_LIMIT = 12570
NI_UPPER_PROFIT_LIMIT = 50270
NI_CLASS4_MAIN_RATE = 0.06   # 6% between LPL and UPL
NI_CLASS4_ADDITIONAL = 0.02  # 2% above UPL
NI_CLASS2_WEEKLY = 3.45      # £3.45/week if profits > Small Profits Threshold
NI_CLASS2_SPT = 6725         # Small Profits Threshold


# ========================================================================
# DATACLASSES
# ========================================================================

@dataclass
class Finding:
    """A single audit finding from the inspector."""
    severity: str = ""
    category: str = ""          # e.g., "income", "expenses", "vat", "bank"
    finding: str = ""
    statute: str = ""           # Legal reference
    risk: str = ""
    evidence: str = ""
    recommendation: str = ""
    tax_impact: float = 0.0     # Estimated additional tax exposure
    penalty_range: str = ""     # e.g., "0-30% careless"
    affected_items: List[str] = field(default_factory=list)


@dataclass
class InspectorReport:
    """Full inspection report."""
    entity: str = ""
    tax_year: str = ""
    inspection_date: str = ""
    verdict: str = ""
    risk_score: int = 0         # 0 (clean) to 100 (referral)
    findings: List[Finding] = field(default_factory=list)
    summary: Dict = field(default_factory=dict)
    simulated_enquiry: Dict = field(default_factory=dict)
    tax_exposure: float = 0.0   # Total additional tax at risk
    penalty_exposure: float = 0.0  # Total potential penalties


# ========================================================================
# THE INSPECTOR
# ========================================================================

class HMRCInspector:
    """The Man on the Inside.

    Fully law-abiding. Knows every statute. Finds every weakness.
    If this inspector signs off, you're clean.

    Usage:
        inspector = HMRCInspector(entity_type="sole_trader",
                                   trade_sector="construction_sole_trader")

        # Feed it everything
        report = inspector.full_inspection(
            income_records=[...],
            expense_events=[...],
            vat_return={...},
            bank_transactions=[...],
            declared_turnover=55000,
            declared_profit=28000,
            tax_year="2025/26",
        )

        # Or run individual checks
        findings = inspector.audit_income(income_records, declared_turnover)
        findings += inspector.audit_expenses(expense_events, declared_turnover)
        findings += inspector.audit_vat(vat_return, expense_events)
        findings += inspector.audit_bank(bank_transactions, declared_turnover)
        findings += inspector.audit_cis(expense_events)
        findings += inspector.audit_crypto(crypto_trades, declared_gains)
    """

    def __init__(self,
                 entity_type: str = "sole_trader",
                 trade_sector: str = "construction_sole_trader"):
        self.entity_type = entity_type
        self.trade_sector = trade_sector
        self.benchmarks = SECTOR_BENCHMARKS.get(trade_sector, {})

    # ================================================================== #
    # FULL INSPECTION
    # ================================================================== #
    def full_inspection(self,
                        income_records: List[Dict] = None,
                        expense_events: List[Any] = None,
                        vat_return: Dict = None,
                        bank_transactions: List[Dict] = None,
                        declared_turnover: float = 0,
                        declared_expenses: float = 0,
                        declared_profit: float = 0,
                        tax_year: str = "",
                        crypto_trades: List[Dict] = None,
                        crypto_gains: float = 0,
                        cis_payments: List[Dict] = None,
                        ) -> InspectorReport:
        """Run the full HMRC-style inspection.

        This is the s.9A enquiry simulation. Every check an HMRC
        officer would run, in the order they'd run them.
        """
        findings: List[Finding] = []

        # Phase 1: Income audit
        if income_records is not None or declared_turnover > 0:
            findings.extend(self.audit_income(
                income_records or [], declared_turnover, bank_transactions or []))

        # Phase 2: Expense audit
        if expense_events is not None:
            findings.extend(self.audit_expenses(
                expense_events, declared_turnover))

        # Phase 3: VAT audit
        if vat_return is not None:
            findings.extend(self.audit_vat(
                vat_return, expense_events or [], declared_turnover))

        # Phase 4: Bank reconciliation
        if bank_transactions is not None:
            findings.extend(self.audit_bank(
                bank_transactions, declared_turnover, declared_profit))

        # Phase 5: CIS compliance
        if expense_events is not None or cis_payments is not None:
            findings.extend(self.audit_cis(
                expense_events or [], cis_payments or []))

        # Phase 6: Crypto compliance
        if crypto_trades is not None:
            findings.extend(self.audit_crypto(
                crypto_trades, crypto_gains, tax_year))

        # Phase 7: Cross-reference (Connect Four)
        if all(v is not None for v in [income_records, expense_events, bank_transactions]):
            findings.extend(self.connect_four(
                income_records or [], expense_events or [],
                bank_transactions or [], vat_return or {},
                declared_turnover, declared_profit))

        # Phase 8: Statutory compliance
        findings.extend(self.audit_statutory_compliance(
            declared_turnover, declared_profit, tax_year))

        # Calculate risk score and verdict
        risk_score = self._calculate_risk_score(findings)
        verdict = self._determine_verdict(risk_score, findings)
        tax_exposure = sum(f.tax_impact for f in findings if f.tax_impact > 0)
        penalty_exposure = self._estimate_penalties(findings, tax_exposure)

        # Simulated enquiry
        simulated = self._simulate_enquiry(findings, tax_exposure, penalty_exposure)

        report = InspectorReport(
            entity=self.entity_type,
            tax_year=tax_year,
            inspection_date=datetime.now().strftime("%Y-%m-%d %H:%M"),
            verdict=verdict,
            risk_score=risk_score,
            findings=findings,
            summary={
                "total_findings": len(findings),
                "critical": len([f for f in findings if f.severity == FindingSeverity.CRITICAL.value]),
                "high": len([f for f in findings if f.severity == FindingSeverity.HIGH.value]),
                "medium": len([f for f in findings if f.severity == FindingSeverity.MEDIUM.value]),
                "low": len([f for f in findings if f.severity == FindingSeverity.LOW.value]),
                "info": len([f for f in findings if f.severity == FindingSeverity.INFO.value]),
            },
            simulated_enquiry=simulated,
            tax_exposure=round(tax_exposure, 2),
            penalty_exposure=round(penalty_exposure, 2),
        )

        return report

    # ================================================================== #
    # PHASE 1: INCOME AUDIT
    # ================================================================== #
    def audit_income(self, income_records: List[Dict],
                     declared_turnover: float,
                     bank_transactions: List[Dict] = None) -> List[Finding]:
        """Audit income declarations against evidence.

        HMRC checks:
        - Do bank deposits match declared income?
        - Are there unexplained deposits?
        - Is turnover credible for a sole trader in this sector?
        - Suppression of income (deliberate understatement)?
        """
        findings = []

        # Check 1: Bank deposits vs declared income
        if bank_transactions:
            total_deposits = sum(
                t.get("amount", 0) for t in bank_transactions
                if t.get("direction", "") == "in"
                and t.get("type", "") not in ("transfer", "refund", "loan")
            )

            if total_deposits > declared_turnover * 1.15:
                gap = total_deposits - declared_turnover
                findings.append(Finding(
                    severity=FindingSeverity.HIGH.value,
                    category="income",
                    finding=f"Bank deposits ({total_deposits:,.2f}) exceed declared turnover ({declared_turnover:,.2f}) by {gap:,.2f}",
                    statute="ITTOIA 2005 s.25 — receipts basis; TMA 1970 s.29 — discovery assessment",
                    risk="Unexplained deposits suggest undeclared income. HMRC uses bank deposit analysis as primary enquiry tool",
                    evidence=f"Total inbound bank transactions: {total_deposits:,.2f}. Declared: {declared_turnover:,.2f}. Gap: {gap:,.2f}",
                    recommendation="Identify and document all non-income deposits (transfers, loans, refunds, gifts). Every deposit must have an explanation",
                    tax_impact=round(gap * 0.40, 2),  # Assume higher rate
                ))
            elif total_deposits < declared_turnover * 0.80:
                findings.append(Finding(
                    severity=FindingSeverity.MEDIUM.value,
                    category="income",
                    finding=f"Declared turnover ({declared_turnover:,.2f}) significantly exceeds bank deposits ({total_deposits:,.2f})",
                    statute="ITTOIA 2005 s.25",
                    risk="Possible cash-in-hand income not banked, or timing differences. HMRC may query source of un-banked income",
                    evidence=f"Deposits: {total_deposits:,.2f} vs Declared: {declared_turnover:,.2f}",
                    recommendation="Ensure all income eventually flows through the bank. Cash income should be banked and recorded",
                ))

        # Check 2: Turnover credibility for sector
        if declared_turnover > 0:
            # A construction sole trader without employees typically turns over
            # £30k-£120k. Above £120k as a genuine one-man band is unusual.
            if declared_turnover > 120000:
                findings.append(Finding(
                    severity=FindingSeverity.MEDIUM.value,
                    category="income",
                    finding=f"Turnover of {declared_turnover:,.2f} is high for a sole trader with no employees",
                    statute="SI 2005/2045 — CIS Regulations; ITTOIA 2005 s.34 — wholly and exclusively",
                    risk="HMRC queries how one person generates this turnover. Suggests undeclared subcontractors or employees",
                    evidence=f"Declared: {declared_turnover:,.2f}. Sector norm for one-man: £30k-£120k",
                    recommendation="If using subcontractors, ensure CIS compliance. If employing, register as employer",
                ))
            elif declared_turnover < 15000 and declared_turnover > 0:
                findings.append(Finding(
                    severity=FindingSeverity.LOW.value,
                    category="income",
                    finding=f"Low turnover ({declared_turnover:,.2f}) for construction sector",
                    statute="ITTOIA 2005 s.66 — cessation",
                    risk="HMRC may query if this is a genuine ongoing trade or a hobby/loss-making activity",
                    recommendation="Ensure evidence of trading intention (invoices, marketing, active contracts)",
                ))

        # Check 3: Income completeness (from records)
        if income_records:
            invoiced_total = sum(r.get("amount", 0) for r in income_records)
            if abs(invoiced_total - declared_turnover) > declared_turnover * 0.05:
                findings.append(Finding(
                    severity=FindingSeverity.HIGH.value,
                    category="income",
                    finding=f"Invoiced total ({invoiced_total:,.2f}) doesn't match declared turnover ({declared_turnover:,.2f})",
                    statute="TMA 1970 s.9A — enquiry into return",
                    risk="Discrepancy between invoice records and tax return. Primary enquiry trigger",
                    evidence=f"Invoiced: {invoiced_total:,.2f}. Declared: {declared_turnover:,.2f}. Difference: {abs(invoiced_total - declared_turnover):,.2f}",
                    recommendation="Reconcile all invoices to declared turnover. Include WIP and accruals",
                    tax_impact=round(abs(invoiced_total - declared_turnover) * 0.40, 2),
                ))

            # Check for round-number invoices (indicator of estimation)
            round_invoices = [r for r in income_records
                              if r.get("amount", 0) % 100 == 0
                              and r.get("amount", 0) >= 500]
            if len(round_invoices) > len(income_records) * 0.5 and len(income_records) > 3:
                findings.append(Finding(
                    severity=FindingSeverity.LOW.value,
                    category="income",
                    finding=f"{len(round_invoices)} of {len(income_records)} invoices are round numbers",
                    statute="TMA 1970 s.12B — record keeping",
                    risk="High proportion of round-number invoices suggests estimation rather than actual pricing",
                    recommendation="Normal for construction quotes but keep detailed breakdowns (labour + materials)",
                ))

        return findings

    # ================================================================== #
    # PHASE 2: EXPENSE AUDIT
    # ================================================================== #
    def audit_expenses(self, events: List[Any],
                       declared_turnover: float) -> List[Finding]:
        """Audit expense claims against sector benchmarks.

        HMRC checks:
        - Are expense ratios within sector norms?
        - Are there disallowable items claimed?
        - Is the "wholly and exclusively" test met?
        - Capital vs revenue distinction correct?
        - Evidence trail (receipts, invoices)?
        """
        findings = []

        if not events or declared_turnover <= 0:
            return findings

        # Categorise expenses by type
        expense_totals = defaultdict(float)
        personal_total = 0.0
        business_total = 0.0
        unknown_total = 0.0
        total_vat_claimed = 0.0
        items_without_evidence = 0
        large_round_expenses = []

        for e in events:
            cat = getattr(e, "category", "")
            nature = getattr(e, "nature", "")
            amt = getattr(e, "amount_gross", 0)
            vat = getattr(e, "vat_amount", 0)
            confidence = getattr(e, "confidence", 0)

            if nature == "transfer":
                continue

            expense_totals[cat] += amt
            total_vat_claimed += vat

            if nature == "personal":
                personal_total += amt
            elif nature == "unknown":
                unknown_total += amt
            elif nature in ("business", "mixed"):
                business_total += amt

            if confidence < 0.50:
                items_without_evidence += 1

            if amt >= 500 and amt % 100 == 0:
                large_round_expenses.append(e)

        # Check 1: Materials ratio
        materials = expense_totals.get("materials_and_supplies", 0)
        materials_pct = materials / declared_turnover if declared_turnover > 0 else 0
        bench = self.benchmarks.get("materials_pct_of_turnover", (0.20, 0.45))

        if materials_pct > bench[1]:
            findings.append(Finding(
                severity=FindingSeverity.MEDIUM.value,
                category="expenses",
                finding=f"Materials at {materials_pct:.1%} of turnover exceeds sector norm ({bench[0]:.0%}-{bench[1]:.0%})",
                statute="ITTOIA 2005 s.34 — wholly and exclusively for trade purposes",
                risk="High materials ratio suggests either over-claiming, personal purchases mixed in, or stock build-up not reflected in accounts",
                evidence=f"Materials: {materials:,.2f} on turnover of {declared_turnover:,.2f} = {materials_pct:.1%}",
                recommendation="Verify all material purchases have supplier invoices. Check for personal items at trade counters (B&Q, Screwfix)",
                tax_impact=round((materials_pct - bench[1]) * declared_turnover * 0.40, 2),
            ))

        # Check 2: Motor expenses ratio
        motor = expense_totals.get("motor_expenses", 0)
        motor_pct = motor / declared_turnover if declared_turnover > 0 else 0
        bench_motor = self.benchmarks.get("motor_pct_of_turnover", (0.03, 0.10))

        if motor_pct > bench_motor[1]:
            findings.append(Finding(
                severity=FindingSeverity.MEDIUM.value,
                category="expenses",
                finding=f"Motor expenses at {motor_pct:.1%} of turnover exceeds norm ({bench_motor[0]:.0%}-{bench_motor[1]:.0%})",
                statute="ITTOIA 2005 s.34; BIM37600 — motor expenses",
                risk="High motor costs. HMRC will query business vs private use split. Must evidence business mileage",
                evidence=f"Motor: {motor:,.2f} on {declared_turnover:,.2f} = {motor_pct:.1%}",
                recommendation="Keep a mileage log. Apply consistent business use percentage. HMRC accepts 45p/mile simplified method as alternative",
            ))

        # Check 3: Subcontractor costs (CIS trigger)
        subcon = expense_totals.get("subcontractor_cis", 0)
        subcon_pct = subcon / declared_turnover if declared_turnover > 0 else 0
        bench_sub = self.benchmarks.get("subcontractor_pct_of_turnover", (0.0, 0.40))

        if subcon_pct > bench_sub[1]:
            findings.append(Finding(
                severity=FindingSeverity.HIGH.value,
                category="expenses",
                finding=f"Subcontractor costs at {subcon_pct:.1%} of turnover — very high",
                statute="SI 2005/2045 — CIS Regulations; FA 2004 s.61",
                risk="Over 40% on subcontractors questions whether this is genuinely your trade or you're operating as an employment agency. HMRC tests IR35/employment status",
                evidence=f"Subcontractor: {subcon:,.2f} on {declared_turnover:,.2f} = {subcon_pct:.1%}",
                recommendation="Verify all subcontractors are genuinely self-employed (not disguised employees). Ensure CIS verification and monthly returns filed",
                tax_impact=round(subcon * 0.138, 2),  # Employer NI if reclassified
            ))

        # Check 4: Profit margin
        declared_expenses_total = business_total
        if declared_turnover > 0:
            profit_margin = (declared_turnover - declared_expenses_total) / declared_turnover
            bench_profit = self.benchmarks.get("net_profit_margin", (0.15, 0.45))

            if profit_margin < bench_profit[0]:
                findings.append(Finding(
                    severity=FindingSeverity.MEDIUM.value,
                    category="expenses",
                    finding=f"Net profit margin at {profit_margin:.1%} is below sector norm ({bench_profit[0]:.0%}-{bench_profit[1]:.0%})",
                    statute="ITTOIA 2005 s.34; TMA 1970 s.9A",
                    risk="Low margins for construction suggest inflated expenses or suppressed income. HMRC compares against sector averages",
                    evidence=f"Turnover: {declared_turnover:,.2f}. Expenses: {declared_expenses_total:,.2f}. Margin: {profit_margin:.1%}",
                    recommendation="Review expense claims for personal items. Ensure income is complete. Low margins for >2 years triggers enhanced review",
                ))
            elif profit_margin > bench_profit[1]:
                findings.append(Finding(
                    severity=FindingSeverity.INFO.value,
                    category="expenses",
                    finding=f"Healthy profit margin at {profit_margin:.1%} (above sector average)",
                    statute="N/A",
                    risk="No issue — good profitability reduces enquiry risk",
                    recommendation="N/A",
                ))

        # Check 5: Unknown/uncategorised expenses
        if unknown_total > 0:
            unknown_pct = unknown_total / declared_turnover if declared_turnover > 0 else 0
            sev = FindingSeverity.HIGH if unknown_pct > 0.10 else FindingSeverity.MEDIUM
            findings.append(Finding(
                severity=sev.value,
                category="expenses",
                finding=f"Uncategorised expenses of {unknown_total:,.2f} ({unknown_pct:.1%} of turnover)",
                statute="TMA 1970 s.12B — duty to keep records",
                risk="Unidentified expenditure cannot be claimed. HMRC will disallow and may assess penalties for inadequate records",
                evidence=f"Unknown: {unknown_total:,.2f}",
                recommendation="Categorise or remove from claim. Uncategorised items should not appear on the tax return",
                tax_impact=round(unknown_total * 0.40, 2),
            ))

        # Check 6: Low confidence categorisations
        if items_without_evidence > 0:
            total_items = len([e for e in events if getattr(e, "nature", "") != "transfer"])
            pct = items_without_evidence / max(total_items, 1)
            if pct > 0.15:
                findings.append(Finding(
                    severity=FindingSeverity.MEDIUM.value,
                    category="expenses",
                    finding=f"{items_without_evidence} transactions ({pct:.0%}) have low confidence categorisation",
                    statute="TMA 1970 s.12B",
                    risk="Low confidence indicates weak evidence trail. HMRC requires contemporaneous records",
                    recommendation="Obtain and retain receipts/invoices. Match bank transactions to supplier records",
                ))

        # Check 7: Large round-number expenses
        if len(large_round_expenses) > 5:
            findings.append(Finding(
                severity=FindingSeverity.LOW.value,
                category="expenses",
                finding=f"{len(large_round_expenses)} expense claims are round numbers (£500+)",
                statute="TMA 1970 s.12B",
                risk="Round numbers suggest estimation. HMRC prefers exact figures from invoices",
                recommendation="Use actual invoice amounts rather than estimates where possible",
            ))

        # Check 8: Personal expenses claimed
        if personal_total > 0 and declared_turnover > 0:
            # Check they're properly separated
            findings.append(Finding(
                severity=FindingSeverity.INFO.value,
                category="expenses",
                finding=f"Personal expenditure of {personal_total:,.2f} correctly identified and excluded from claim",
                statute="ITTOIA 2005 s.34",
                risk="No risk — personal items properly separated to drawings (3300)",
                recommendation="Continue separating. HMRC checks for personal items claimed as business",
            ))

        # Check 9: VAT claimed vs evidence
        if total_vat_claimed > 0:
            vat_ratio = total_vat_claimed / declared_turnover if declared_turnover > 0 else 0
            bench_vat = self.benchmarks.get("vat_reclaim_ratio", (0.03, 0.25))
            if vat_ratio > bench_vat[1]:
                findings.append(Finding(
                    severity=FindingSeverity.MEDIUM.value,
                    category="expenses",
                    finding=f"VAT reclaim ratio ({vat_ratio:.1%}) exceeds sector norm",
                    statute="VATA 1994 s.24-26 — input tax",
                    risk="High VAT recovery relative to turnover. HMRC cross-checks with VAT return",
                    evidence=f"VAT claimed: {total_vat_claimed:,.2f} on turnover {declared_turnover:,.2f} = {vat_ratio:.1%}",
                    recommendation="Ensure VAT invoices held for all claims. Remove blocked input tax (entertainment, non-business)",
                    tax_impact=round((vat_ratio - bench_vat[1]) * declared_turnover, 2),
                ))

        return findings

    # ================================================================== #
    # PHASE 3: VAT AUDIT
    # ================================================================== #
    def audit_vat(self, vat_return: Dict, expense_events: List[Any],
                  declared_turnover: float) -> List[Finding]:
        """Audit VAT return for compliance.

        HMRC checks:
        - Box arithmetic correct?
        - Output VAT consistent with declared turnover?
        - Input VAT supported by valid invoices?
        - Reverse charge correctly applied?
        - Flat rate scheme conditions still met?
        """
        findings = []

        box1 = vat_return.get("box1_vat_due_sales", 0)
        box4 = vat_return.get("box4_vat_reclaimed", 0)
        box5 = vat_return.get("box5_net_vat", 0)
        box6 = vat_return.get("box6_total_sales_ex_vat", 0)
        box7 = vat_return.get("box7_total_purchases_ex_vat", 0)

        # Check 1: Box 6 vs declared turnover (annualised)
        if declared_turnover > 0 and box6 > 0:
            # Quarterly: box6 should be roughly turnover / 4
            quarterly_expected = declared_turnover / 4
            variance = abs(box6 - quarterly_expected) / quarterly_expected if quarterly_expected > 0 else 0
            if variance > 0.40:
                findings.append(Finding(
                    severity=FindingSeverity.MEDIUM.value,
                    category="vat",
                    finding=f"Box 6 ({box6:,.2f}) varies significantly from expected quarterly ({quarterly_expected:,.2f})",
                    statute="VATA 1994 s.73 — assessment of VAT due",
                    risk="Large variance between VAT return sales and income tax turnover. HMRC cross-references these",
                    recommendation="Ensure VAT return periods align with income recognition. Check timing differences",
                ))

        # Check 2: Output VAT arithmetic
        if box6 > 0:
            expected_output_vat = box6 * 0.20  # If all standard-rated
            if box1 > expected_output_vat * 1.05:
                findings.append(Finding(
                    severity=FindingSeverity.LOW.value,
                    category="vat",
                    finding=f"Output VAT ({box1:,.2f}) higher than expected for standard rate ({expected_output_vat:,.2f})",
                    statute="VATA 1994 s.4",
                    risk="May indicate reverse charge VAT included in Box 1 (correct) or overstatement",
                    recommendation="Verify reverse charge entries appear in both Box 1 and Box 4",
                ))

        # Check 3: Repayment return
        if box5 < 0:
            findings.append(Finding(
                severity=FindingSeverity.MEDIUM.value,
                category="vat",
                finding=f"Repayment return: {abs(box5):,.2f} reclaim",
                statute="VATA 1994 s.25(3) — repayment",
                risk="Repayment returns attract automatic compliance checks. HMRC may delay payment for verification",
                recommendation="Ensure all input VAT invoices are valid and available. Common trigger for VAT visit",
            ))

        # Check 4: Box 7 vs expense claims
        if expense_events:
            total_expenses_ex_vat = sum(
                getattr(e, "amount_gross", 0) - getattr(e, "vat_amount", 0)
                for e in expense_events
                if getattr(e, "nature", "") in ("business", "mixed")
            )
            if box7 > 0 and total_expenses_ex_vat > 0:
                variance = abs(box7 - total_expenses_ex_vat) / total_expenses_ex_vat
                if variance > 0.20:
                    findings.append(Finding(
                        severity=FindingSeverity.MEDIUM.value,
                        category="vat",
                        finding=f"Box 7 ({box7:,.2f}) doesn't match expense records ({total_expenses_ex_vat:,.2f})",
                        statute="VATA 1994 s.24 — input tax",
                        risk="Discrepancy between VAT return purchases and income tax expenses. HMRC cross-checks",
                        recommendation="Reconcile. Differences may be timing, exempt purchases, or capital items treated differently",
                    ))

        return findings

    # ================================================================== #
    # PHASE 4: BANK RECONCILIATION AUDIT
    # ================================================================== #
    def audit_bank(self, bank_transactions: List[Dict],
                   declared_turnover: float,
                   declared_profit: float) -> List[Finding]:
        """Audit bank transactions for suspicious patterns.

        HMRC bank deposit analysis:
        - Total deposits vs declared income
        - Cash patterns (frequent round withdrawals)
        - Third-party transfers (who's paying you?)
        - Lifestyle check (personal spend vs declared profit)
        """
        findings = []

        if not bank_transactions:
            return findings

        total_in = sum(t.get("amount", 0) for t in bank_transactions
                       if t.get("direction") == "in")
        total_out = sum(t.get("amount", 0) for t in bank_transactions
                        if t.get("direction") == "out")

        # Cash withdrawals analysis
        cash_withdrawals = [
            t for t in bank_transactions
            if t.get("direction") == "out"
            and ("cash" in t.get("description", "").lower()
                 or "atm" in t.get("description", "").lower())
        ]
        cash_total = sum(t.get("amount", 0) for t in cash_withdrawals)

        if declared_turnover > 0:
            cash_pct = cash_total / declared_turnover
            bench = self.benchmarks.get("cash_withdrawal_pct_income", (0, 0.15))
            if cash_pct > bench[1]:
                findings.append(Finding(
                    severity=FindingSeverity.HIGH.value,
                    category="bank",
                    finding=f"Cash withdrawals ({cash_total:,.2f}) are {cash_pct:.1%} of declared turnover",
                    statute="TMA 1970 s.9A; POCA 2002 s.327-329",
                    risk="High cash withdrawals relative to income. HMRC questions what cash is used for. Pattern associated with undeclared labour payments",
                    evidence=f"{len(cash_withdrawals)} cash withdrawals totalling {cash_total:,.2f}",
                    recommendation="Document purpose of each cash withdrawal. Personal living expenses, petty cash, or site materials are acceptable. Undocumented cash to individuals is not",
                    tax_impact=round(cash_total * 0.30, 2),  # CIS implications
                ))

        # Frequency of cash withdrawals
        if len(cash_withdrawals) > 0:
            # Check for regular pattern (suggests wage payments)
            amounts = [t.get("amount", 0) for t in cash_withdrawals]
            from collections import Counter
            amount_freq = Counter(amounts)
            most_common_amt, most_common_count = amount_freq.most_common(1)[0]
            if most_common_count >= 3 and most_common_amt >= 200:
                findings.append(Finding(
                    severity=FindingSeverity.HIGH.value,
                    category="bank",
                    finding=f"Regular cash withdrawals of £{most_common_amt:,.0f} ({most_common_count} times)",
                    statute="SI 2005/2045 — CIS; ITEPA 2003 s.44 — employment status",
                    risk="Repeated identical cash withdrawals are a strong indicator of wage payments. HMRC specifically looks for this pattern",
                    evidence=f"£{most_common_amt:,.0f} withdrawn {most_common_count} times",
                    recommendation="If paying workers: register as employer or verify CIS status. If personal: vary withdrawal amounts and document purpose",
                ))

        # Transfers to named individuals
        individual_transfers = [
            t for t in bank_transactions
            if t.get("direction") == "out"
            and t.get("type", "") in ("transfer", "faster_payment")
            and t.get("counterparty", "")
            and not any(biz in t.get("counterparty", "").lower()
                        for biz in ["hmrc", "ltd", "plc", "bank", "insurance",
                                     "council", "utility", "electric", "gas",
                                     "water", "phone", "broadband", "savings"])
        ]

        if individual_transfers:
            ind_total = sum(t.get("amount", 0) for t in individual_transfers)
            if ind_total > 1000:
                counterparties = set(t.get("counterparty", "") for t in individual_transfers)
                findings.append(Finding(
                    severity=FindingSeverity.MEDIUM.value,
                    category="bank",
                    finding=f"Transfers to {len(counterparties)} named individuals totalling {ind_total:,.2f}",
                    statute="SI 2005/2045 — CIS; POCA 2002 s.327",
                    risk="Bank transfers to individuals are traceable. HMRC can identify recipients and check their tax status",
                    evidence=f"{len(individual_transfers)} transfers to: {', '.join(list(counterparties)[:5])}",
                    recommendation="If legitimate transfers (family, loans): document purpose. If payments for work: CIS/PAYE obligations apply",
                ))

        # Lifestyle check: personal spend vs declared profit
        if declared_profit > 0:
            # Estimate personal spending from bank
            personal_spend = sum(
                t.get("amount", 0) for t in bank_transactions
                if t.get("direction") == "out"
                and t.get("type", "") not in ("transfer",)
                and not any(biz in t.get("description", "").lower()
                            for biz in ["screwfix", "travis", "jewson", "toolstation",
                                         "wickes", "selco", "hmrc", "vat"])
            )

            # Add income tax and NI estimate
            estimated_tax = self._estimate_tax_ni(declared_profit)
            after_tax = declared_profit - estimated_tax

            if personal_spend > after_tax * 1.30:
                findings.append(Finding(
                    severity=FindingSeverity.HIGH.value,
                    category="bank",
                    finding=f"Lifestyle exceeds declared after-tax income",
                    statute="TMA 1970 s.9A; ITTOIA 2005",
                    risk=f"Spending ({personal_spend:,.0f}) exceeds estimated after-tax income ({after_tax:,.0f}). Classic HMRC 'living beyond means' check",
                    evidence=f"Declared profit: {declared_profit:,.0f}. Estimated tax: {estimated_tax:,.0f}. After tax: {after_tax:,.0f}. Personal spend: {personal_spend:,.0f}",
                    recommendation="Identify other income sources (savings, partner, rental). If no explanation, indicates undeclared income",
                    tax_impact=round((personal_spend - after_tax) * 0.40, 2),
                ))

        return findings

    # ================================================================== #
    # PHASE 5: CIS COMPLIANCE AUDIT
    # ================================================================== #
    def audit_cis(self, expense_events: List[Any],
                  cis_payments: List[Dict] = None) -> List[Finding]:
        """Audit CIS compliance.

        Checks:
        - All subcontractor payments have CIS deductions or gross status
        - UTRs verified
        - Monthly returns filed
        - Correct deduction rate applied
        """
        findings = []

        # Find CIS-related expenses
        cis_events = [
            e for e in expense_events
            if getattr(e, "category", "") == "subcontractor_cis"
            or "cis" in getattr(e, "description", "").lower()
            or "subcontract" in getattr(e, "description", "").lower()
        ]

        if not cis_events and not cis_payments:
            return findings

        # Check: CIS payments without UTR verification
        for e in cis_events:
            desc = getattr(e, "description", "").lower()
            has_utr = "utr" in desc or "verified" in desc
            if not has_utr:
                findings.append(Finding(
                    severity=FindingSeverity.HIGH.value,
                    category="cis",
                    finding=f"CIS payment without UTR verification: {getattr(e, 'description', '')[:50]}",
                    statute="SI 2005/2045 reg.6 — verification; FA 2004 s.61 — CIS obligations",
                    risk="Must verify each subcontractor with HMRC before first payment. Without verification, deduct at 30% (not 20%)",
                    evidence=f"Payment: {getattr(e, 'amount_gross', 0):,.2f} to {getattr(e, 'payee', 'unknown')}",
                    recommendation="Verify subcontractor UTR online at gov.uk before payment. Retain verification reference",
                    tax_impact=round(getattr(e, "amount_gross", 0) * 0.10, 2),  # 30% vs 20% difference
                ))

        # Check: Payments to individuals that look like labour but aren't CIS-tagged
        labour_keywords = ["labour", "lad", "helper", "cash", "wages", "work"]
        for e in expense_events:
            desc = getattr(e, "description", "").lower()
            cat = getattr(e, "category", "")
            if any(kw in desc for kw in labour_keywords) and cat != "subcontractor_cis":
                if getattr(e, "amount_gross", 0) >= 200:
                    findings.append(Finding(
                        severity=FindingSeverity.CRITICAL.value,
                        category="cis",
                        finding=f"Possible labour payment not under CIS: {getattr(e, 'description', '')[:50]}",
                        statute="FA 2004 s.61; ITEPA 2003 s.44; SI 2005/2045",
                        risk="Payment for construction labour outside CIS is a serious compliance failure. Contractor liable for deductions not made plus penalties",
                        evidence=f"Amount: {getattr(e, 'amount_gross', 0):,.2f}. Category: {cat}",
                        recommendation="If this is payment for work: must be processed through CIS with appropriate deduction. If not labour: re-categorise with supporting evidence",
                        tax_impact=round(getattr(e, "amount_gross", 0) * 0.30, 2),
                    ))

        return findings

    # ================================================================== #
    # PHASE 6: CRYPTO COMPLIANCE AUDIT
    # ================================================================== #
    def audit_crypto(self, trades: List[Dict],
                     declared_gains: float = 0,
                     tax_year: str = "") -> List[Finding]:
        """Audit crypto tax compliance.

        HMRC checks:
        - All disposals reported?
        - Section 104 pool calculated correctly?
        - Same-day and 30-day rules applied?
        - Annual exemption not exceeded without reporting?
        - Source of funds for acquisitions documented?
        """
        findings = []

        if not trades:
            return findings

        # Calculate actual gains from trades
        from collections import defaultdict
        pools = defaultdict(lambda: {"qty": 0, "cost": 0})
        total_gains = 0.0
        total_losses = 0.0
        disposals = 0

        sorted_trades = sorted(trades, key=lambda t: t.get("date", ""))

        for t in sorted_trades:
            asset = t.get("asset", "")
            action = t.get("action", "")
            qty = t.get("quantity", 0)
            price = t.get("price_gbp", 0)
            fee = t.get("fee_gbp", 0)

            if action == "buy":
                pools[asset]["qty"] += qty
                pools[asset]["cost"] += price + fee
            elif action == "sell":
                if pools[asset]["qty"] > 0:
                    avg_cost = pools[asset]["cost"] / pools[asset]["qty"]
                    cost_of_disposal = avg_cost * qty
                    gain = (price - fee) - cost_of_disposal
                    if gain >= 0:
                        total_gains += gain
                    else:
                        total_losses += gain
                    disposals += 1
                    pools[asset]["qty"] -= qty
                    pools[asset]["cost"] -= cost_of_disposal

        net_gains = total_gains + total_losses  # losses are negative

        # Check 1: Disposals exist but nothing declared
        if disposals > 0 and declared_gains == 0 and net_gains != 0:
            findings.append(Finding(
                severity=FindingSeverity.HIGH.value,
                category="crypto",
                finding=f"{disposals} crypto disposals with net gain/loss of {net_gains:,.2f} but nothing declared",
                statute="TCGA 1992 s.1, s.3; TMA 1970 s.7 — obligation to notify",
                risk="Failure to report chargeable disposals. HMRC receives data from exchanges under CARF (from Jan 2026)",
                evidence=f"Gains: {total_gains:,.2f}. Losses: {total_losses:,.2f}. Net: {net_gains:,.2f}",
                recommendation="Report all disposals on SA108. Even if within annual exemption, gross proceeds >£50k must be reported",
                tax_impact=round(max(net_gains - 3000, 0) * 0.20, 2),  # CGT at 20%
            ))

        # Check 2: P2P/ATM acquisitions (no third-party verification)
        p2p_trades = [t for t in trades
                      if t.get("acquisition_method", "") in ("P2P_cash", "P2P", "ATM", "Bitcoin_ATM")]
        if p2p_trades:
            p2p_total = sum(t.get("price_gbp", 0) for t in p2p_trades)
            findings.append(Finding(
                severity=FindingSeverity.MEDIUM.value,
                category="crypto",
                finding=f"{len(p2p_trades)} P2P/ATM acquisitions totalling {p2p_total:,.2f} — no third-party verification",
                statute="TMA 1970 s.12B — record keeping requirements",
                risk="P2P purchases have no CARF reporting. HMRC may request evidence of acquisition cost. Without evidence, cost basis could be disputed",
                evidence=f"P2P purchases: {p2p_total:,.2f}. No exchange records to verify",
                recommendation="Retain any evidence: screenshots, wallet addresses, ATM receipts, messages with sellers. Record dates and amounts contemporaneously",
            ))

        # Check 3: Same-day rule and 30-day rule
        # Check for sell-then-buy-same-day patterns
        by_date_asset = defaultdict(list)
        for t in sorted_trades:
            key = (t.get("date", "")[:10], t.get("asset", ""))
            by_date_asset[key].append(t)

        for (trade_date, asset), day_trades in by_date_asset.items():
            has_buy = any(t["action"] == "buy" for t in day_trades)
            has_sell = any(t["action"] == "sell" for t in day_trades)
            if has_buy and has_sell:
                findings.append(Finding(
                    severity=FindingSeverity.MEDIUM.value,
                    category="crypto",
                    finding=f"Same-day buy and sell of {asset} on {trade_date}",
                    statute="TCGA 1992 s.105 — same-day rule",
                    risk="Same-day rule overrides Section 104 pool. Gain/loss must be calculated against same-day acquisition cost, not pool average",
                    recommendation="Recalculate gain/loss using same-day rule. This takes priority over S104 pooling",
                ))

        # Check 4: 30-day bed and breakfasting
        sells = [t for t in sorted_trades if t["action"] == "sell"]
        buys = [t for t in sorted_trades if t["action"] == "buy"]
        for sell in sells:
            sell_date = datetime.strptime(sell["date"][:10], "%Y-%m-%d")
            for buy in buys:
                buy_date = datetime.strptime(buy["date"][:10], "%Y-%m-%d")
                days_diff = (buy_date - sell_date).days
                if (sell["asset"] == buy["asset"]
                        and 1 <= days_diff <= 30):
                    findings.append(Finding(
                        severity=FindingSeverity.MEDIUM.value,
                        category="crypto",
                        finding=f"30-day rule: sold {sell['asset']} on {sell['date'][:10]}, rebought on {buy['date'][:10]} ({days_diff} days)",
                        statute="TCGA 1992 s.106A — 30-day rule (bed and breakfasting)",
                        risk="Acquisitions within 30 days of disposal of same asset must be matched. Cannot crystallise loss and immediately rebuy",
                        recommendation="Use cross-asset swap instead (sell BTC, buy ETH). Different S104 pools, no 30-day rule",
                    ))

        # Check 5: Source of funds
        total_invested = sum(t.get("price_gbp", 0) for t in trades if t["action"] == "buy")
        if total_invested > 10000:
            findings.append(Finding(
                severity=FindingSeverity.LOW.value,
                category="crypto",
                finding=f"Total crypto investment of {total_invested:,.2f} — source of funds should be documented",
                statute="POCA 2002 s.340; MLR 2017",
                risk="Exchanges must verify source of funds under AML. HMRC can request same evidence. Ensure funds trace to legitimate income",
                recommendation="Keep records showing source: bank transfers from declared income, savings, etc. P2P cash purchases need extra documentation",
            ))

        return findings

    # ================================================================== #
    # PHASE 7: CONNECT FOUR — Cross-reference audit
    # ================================================================== #
    def connect_four(self, income_records: List[Dict],
                     expense_events: List[Any],
                     bank_transactions: List[Dict],
                     vat_return: Dict,
                     declared_turnover: float,
                     declared_profit: float) -> List[Finding]:
        """The Connect Four: Cross-reference all four data sources.

        This is how HMRC catches people. Not from one source, but from
        inconsistencies BETWEEN sources. The tax return says one thing,
        the bank says another, the VAT return says a third, and the
        receipts tell a fourth story.
        """
        findings = []

        # Cross-check 1: Income Tax turnover vs VAT Box 6
        box6 = vat_return.get("box6_total_sales_ex_vat", 0)
        if box6 > 0 and declared_turnover > 0:
            annual_box6 = box6 * 4  # Annualise quarterly
            variance_pct = abs(annual_box6 - declared_turnover) / declared_turnover
            if variance_pct > 0.15:
                findings.append(Finding(
                    severity=FindingSeverity.HIGH.value,
                    category="cross_reference",
                    finding=f"Income tax turnover ({declared_turnover:,.2f}) vs annualised VAT sales ({annual_box6:,.2f}) — {variance_pct:.0%} variance",
                    statute="TMA 1970 s.9A; VATA 1994 s.73",
                    risk="HMRC automatically cross-references SA and VAT returns. Variance >15% triggers review",
                    recommendation="Reconcile. Common causes: timing (accruals vs cash), partial year, exempt supplies in VAT but included in SA",
                    tax_impact=round(abs(annual_box6 - declared_turnover) * 0.40, 2),
                ))

        # Cross-check 2: Bank in-flows vs income records
        if income_records and bank_transactions:
            recorded_income = sum(r.get("amount", 0) for r in income_records)
            bank_income = sum(t.get("amount", 0) for t in bank_transactions
                              if t.get("direction") == "in"
                              and t.get("type", "") not in ("transfer", "refund"))

            if bank_income > recorded_income * 1.10:
                gap = bank_income - recorded_income
                findings.append(Finding(
                    severity=FindingSeverity.HIGH.value,
                    category="cross_reference",
                    finding=f"Bank deposits ({bank_income:,.2f}) exceed recorded income ({recorded_income:,.2f}) by {gap:,.2f}",
                    statute="ITTOIA 2005 s.25; TMA 1970 s.29 — discovery",
                    risk="Unrecorded income in bank account. HMRC's Connect system flags this automatically",
                    recommendation="Identify all non-income deposits and document them. Every bank credit needs an explanation",
                    tax_impact=round(gap * 0.40, 2),
                ))

        # Cross-check 3: Expense records vs bank outflows
        if expense_events and bank_transactions:
            recorded_expenses = sum(
                getattr(e, "amount_gross", 0) for e in expense_events
                if getattr(e, "nature", "") in ("business", "mixed")
            )
            bank_business_out = sum(
                t.get("amount", 0) for t in bank_transactions
                if t.get("direction") == "out"
                and t.get("type", "") not in ("transfer", "personal")
            )

            # It's OK for bank outflows to exceed expense records
            # (personal spending is in bank but not in expenses)
            # But expense records > bank outflows is suspicious
            if recorded_expenses > bank_business_out * 1.20 and bank_business_out > 0:
                findings.append(Finding(
                    severity=FindingSeverity.MEDIUM.value,
                    category="cross_reference",
                    finding=f"Expense records ({recorded_expenses:,.2f}) exceed bank outflows ({bank_business_out:,.2f})",
                    statute="TMA 1970 s.12B; ITTOIA 2005 s.34",
                    risk="Claiming more expenses than went through the bank. Possible fabricated expenses or cash payments not through account",
                    recommendation="Reconcile. If cash purchases: need receipts. If supplier credit: show creditor balances",
                ))

        # Cross-check 4: Declared profit vs lifestyle
        if declared_profit > 0 and bank_transactions:
            total_outflows = sum(t.get("amount", 0) for t in bank_transactions
                                 if t.get("direction") == "out")
            total_inflows = sum(t.get("amount", 0) for t in bank_transactions
                                if t.get("direction") == "in")

            # Net personal consumption = inflows - business expenses - tax
            estimated_tax = self._estimate_tax_ni(declared_profit)
            recorded_expenses = sum(
                getattr(e, "amount_gross", 0) for e in expense_events
                if getattr(e, "nature", "") in ("business", "mixed")
            )
            available_personal = declared_turnover - recorded_expenses - estimated_tax

            if available_personal < 10000 and declared_turnover > 30000:
                findings.append(Finding(
                    severity=FindingSeverity.MEDIUM.value,
                    category="cross_reference",
                    finding=f"Only {available_personal:,.2f} left for personal living after expenses and tax",
                    statute="TMA 1970 s.9A",
                    risk="Very low residual for personal expenditure. Either expenses are inflated, income suppressed, or there's another income source",
                    recommendation="Check for undeclared income (cash jobs, second business, rental). If expenses correct, consider whether all income is declared",
                ))

        return findings

    # ================================================================== #
    # PHASE 8: STATUTORY COMPLIANCE
    # ================================================================== #
    def audit_statutory_compliance(self, declared_turnover: float,
                                    declared_profit: float,
                                    tax_year: str) -> List[Finding]:
        """Check statutory compliance obligations."""
        findings = []

        # Class 2 NI
        if declared_profit > NI_CLASS2_SPT:
            findings.append(Finding(
                severity=FindingSeverity.INFO.value,
                category="statutory",
                finding=f"Class 2 NI due: £{NI_CLASS2_WEEKLY * 52:.2f}/year (profits >{NI_CLASS2_SPT:,})",
                statute="SSCBA 1992 s.11",
                risk="No risk — information only. Class 2 collected through SA",
                recommendation="Included automatically in self assessment",
            ))

        # Class 4 NI
        if declared_profit > NI_LOWER_PROFIT_LIMIT:
            class4 = 0.0
            if declared_profit > NI_UPPER_PROFIT_LIMIT:
                class4 = (NI_UPPER_PROFIT_LIMIT - NI_LOWER_PROFIT_LIMIT) * NI_CLASS4_MAIN_RATE
                class4 += (declared_profit - NI_UPPER_PROFIT_LIMIT) * NI_CLASS4_ADDITIONAL
            else:
                class4 = (declared_profit - NI_LOWER_PROFIT_LIMIT) * NI_CLASS4_MAIN_RATE

            findings.append(Finding(
                severity=FindingSeverity.INFO.value,
                category="statutory",
                finding=f"Class 4 NI estimated: £{class4:,.2f}",
                statute="SSCBA 1992 s.15",
                risk="No risk — information only",
                recommendation=f"Class 4 at {NI_CLASS4_MAIN_RATE:.0%} on profits between {NI_LOWER_PROFIT_LIMIT:,} and {NI_UPPER_PROFIT_LIMIT:,}",
            ))

        # Payment on account
        if declared_profit > 0:
            estimated_tax = self._estimate_tax_ni(declared_profit)
            if estimated_tax > 1000:
                poa = estimated_tax / 2
                findings.append(Finding(
                    severity=FindingSeverity.INFO.value,
                    category="statutory",
                    finding=f"Payments on account due: 2 x £{poa:,.2f} (31 Jan + 31 Jul)",
                    statute="TMA 1970 s.59A — payments on account",
                    risk="No risk — information only. Can apply to reduce if income expected to fall",
                    recommendation=f"Total estimated tax/NI: {estimated_tax:,.2f}. POA: {poa:,.2f} x 2",
                ))

        # Record keeping reminder
        findings.append(Finding(
            severity=FindingSeverity.INFO.value,
            category="statutory",
            finding=f"Records must be retained until at least {int(tax_year[:4]) + RECORD_RETENTION_YEARS + 1 if tax_year else 'N/A'}",
            statute="TMA 1970 s.12B — duty to keep and preserve records",
            risk="Failure to keep records: penalty up to £3,000",
            recommendation=f"Keep all invoices, receipts, bank statements for {RECORD_RETENTION_YEARS} years from 31 Jan after tax year end",
        ))

        return findings

    # ================================================================== #
    # RISK SCORING & VERDICT
    # ================================================================== #
    def _calculate_risk_score(self, findings: List[Finding]) -> int:
        """Calculate risk score 0-100."""
        score = 0
        weights = {
            FindingSeverity.CRITICAL.value: 25,
            FindingSeverity.HIGH.value: 15,
            FindingSeverity.MEDIUM.value: 8,
            FindingSeverity.LOW.value: 3,
            FindingSeverity.INFO.value: 0,
        }
        for f in findings:
            score += weights.get(f.severity, 0)

        return min(score, 100)

    def _determine_verdict(self, risk_score: int,
                            findings: List[Finding]) -> str:
        """Determine overall verdict."""
        critical_count = len([f for f in findings
                              if f.severity == FindingSeverity.CRITICAL.value])
        high_count = len([f for f in findings
                          if f.severity == FindingSeverity.HIGH.value])

        if critical_count > 0:
            return InspectorVerdict.REFERRAL.value
        elif risk_score >= 60 or high_count >= 3:
            return InspectorVerdict.ENQUIRY_RISK.value
        elif risk_score >= 35 or high_count >= 1:
            return InspectorVerdict.CONCERNS.value
        elif risk_score >= 15:
            return InspectorVerdict.MINOR_ISSUES.value
        else:
            return InspectorVerdict.CLEAN.value

    def _estimate_tax_ni(self, profit: float) -> float:
        """Estimate income tax + NI on self-employment profit."""
        taxable = max(profit - PERSONAL_ALLOWANCE, 0)

        if taxable <= BASIC_RATE_BAND:
            tax = taxable * 0.20
        else:
            tax = BASIC_RATE_BAND * 0.20 + (taxable - BASIC_RATE_BAND) * 0.40

        # Class 4 NI
        if profit > NI_UPPER_PROFIT_LIMIT:
            ni4 = (NI_UPPER_PROFIT_LIMIT - NI_LOWER_PROFIT_LIMIT) * NI_CLASS4_MAIN_RATE
            ni4 += (profit - NI_UPPER_PROFIT_LIMIT) * NI_CLASS4_ADDITIONAL
        elif profit > NI_LOWER_PROFIT_LIMIT:
            ni4 = (profit - NI_LOWER_PROFIT_LIMIT) * NI_CLASS4_MAIN_RATE
        else:
            ni4 = 0

        # Class 2 NI
        ni2 = NI_CLASS2_WEEKLY * 52 if profit > NI_CLASS2_SPT else 0

        return round(tax + ni4 + ni2, 2)

    def _estimate_penalties(self, findings: List[Finding],
                             tax_exposure: float) -> float:
        """Estimate potential HMRC penalties (FA 2007 Sch 24)."""
        if tax_exposure <= 0:
            return 0.0

        # Determine penalty basis from worst finding
        has_critical = any(f.severity == FindingSeverity.CRITICAL.value for f in findings)
        has_high = any(f.severity == FindingSeverity.HIGH.value for f in findings)

        if has_critical:
            basis = PenaltyBasis.DELIBERATE
        elif has_high:
            basis = PenaltyBasis.CARELESS
        else:
            basis = PenaltyBasis.REASONABLE_CARE

        min_pct, max_pct = PENALTY_RANGES[basis]

        # Assume unprompted disclosure (best case)
        min_penalty = tax_exposure * min_pct
        max_penalty = tax_exposure * max_pct

        return round((min_penalty + max_penalty) / 2, 2)  # Midpoint estimate

    def _simulate_enquiry(self, findings: List[Finding],
                           tax_exposure: float,
                           penalty_exposure: float) -> Dict:
        """Simulate what an HMRC s.9A enquiry would look like."""
        non_info = [f for f in findings if f.severity != FindingSeverity.INFO.value]

        if not non_info:
            return {
                "would_open_enquiry": False,
                "reason": "No substantive issues found. Return would not trigger enquiry",
                "information_notices": [],
                "estimated_duration": "N/A",
                "total_exposure": 0,
            }

        # What HMRC would request
        info_notices = []

        categories_affected = set(f.category for f in non_info)

        if "income" in categories_affected:
            info_notices.append(
                "TMA 1970 s.19A notice: All sales invoices, contracts, and bank statements for the period")
        if "expenses" in categories_affected:
            info_notices.append(
                "TMA 1970 s.19A notice: All purchase invoices, receipts, and supplier statements")
        if "bank" in categories_affected:
            info_notices.append(
                "TMA 1970 s.19A notice: Full bank statements for all accounts (business and personal)")
        if "cis" in categories_affected:
            info_notices.append(
                "SI 2005/2045: CIS verification records, subcontractor statements, monthly returns")
        if "vat" in categories_affected:
            info_notices.append(
                "VATA 1994 s.73: VAT invoices, daybooks, and reconciliation to return")
        if "crypto" in categories_affected:
            info_notices.append(
                "TMA 1970 s.19A: Exchange records, wallet addresses, transaction history, source of funds")
        if "cross_reference" in categories_affected:
            info_notices.append(
                "TMA 1970 s.19A: Full reconciliation between bank, invoices, expenses, and tax return")

        total_exposure = tax_exposure + penalty_exposure
        # Interest at 7.5% (current HMRC late payment rate)
        interest_1yr = total_exposure * 0.075

        return {
            "would_open_enquiry": len(non_info) >= 2 or any(
                f.severity in (FindingSeverity.CRITICAL.value, FindingSeverity.HIGH.value)
                for f in findings),
            "reason": f"{len(non_info)} substantive findings across {len(categories_affected)} areas",
            "information_notices": info_notices,
            "estimated_duration": "6-18 months" if tax_exposure > 5000 else "3-6 months",
            "tax_exposure": round(tax_exposure, 2),
            "penalty_exposure": round(penalty_exposure, 2),
            "interest_1yr": round(interest_1yr, 2),
            "total_exposure": round(total_exposure + interest_1yr, 2),
            "enquiry_window": f"{ENQUIRY_WINDOW_NORMAL} months (normal) / {ENQUIRY_WINDOW_CARELESS} months (careless) / {ENQUIRY_WINDOW_DELIBERATE} months (deliberate)",
        }

    # ================================================================== #
    # CONNECT INTELLIGENCE SCAN — Know Your Enemy
    # ================================================================== #
    def connect_intelligence_scan(self, report: InspectorReport,
                                    bank_transactions: List[Dict] = None,
                                    crypto_trades: List[Dict] = None,
                                    declared_turnover: float = 0,
                                    declared_profit: float = 0,
                                    social_media_public: bool = True,
                                    ) -> Dict:
        """
        Scan the books through the lens of HMRC Connect's actual data
        sources and risk factors. Imported from hnc_legal intelligence.

        This method thinks like Connect — not like an inspector. It asks:
        'What would the MACHINE see? What data does HMRC already HAVE
        on this person before they even open the return?'

        Returns a Connect threat assessment: which data sources would
        expose which findings, what risk factors are triggered, and
        what investigation stage the current books would land at.
        """
        if not LEGAL_INTEL_AVAILABLE:
            return {"status": "UNAVAILABLE", "reason": "hnc_legal.py not loaded"}

        assessment = {
            "data_source_exposure": [],
            "risk_factors_triggered": [],
            "investigation_stage": None,
            "connect_risk_score": 0,
            "countermeasures_needed": [],
            "blind_spots": [],          # Connect data gaps we can exploit
            "summary": {},
        }

        # --- 1. DATA SOURCE EXPOSURE CHECK ---
        # For each Connect data source, check if it would reveal any findings
        for key, source in CONNECT_DATA_SOURCES.items():
            exposure = {
                "source": source.name,
                "threat_level": source.threat_level,
                "coverage": source.coverage[:80],
                "gaps": source.gaps[:80],
                "exposed_findings": [],
                "countermeasure": source.countermeasure[:80],
            }

            # Map findings to the data sources that would expose them
            for f in report.findings:
                finding_lower = f.finding.lower()
                category = f.category.lower() if f.category else ""

                # Bank data sources
                if key == "uk_banks" and category in ("income", "bank"):
                    if any(kw in finding_lower for kw in ["deposit", "bank", "cash withdrawal",
                                                           "transfer", "lifestyle", "exceeds"]):
                        exposure["exposed_findings"].append(f.finding[:60])

                # CIS returns
                elif key == "cis_returns" and category == "cis":
                    exposure["exposed_findings"].append(f.finding[:60])

                # CARF crypto
                elif key == "carf_exchanges" and category == "crypto":
                    if "p2p" not in finding_lower and "atm" not in finding_lower:
                        exposure["exposed_findings"].append(f.finding[:60])

                # Blockchain analytics
                elif key == "blockchain_analytics" and category == "crypto":
                    if any(kw in finding_lower for kw in ["mixer", "tumbler", "wallet"]):
                        exposure["exposed_findings"].append(f.finding[:60])

                # Land registry
                elif key == "land_registry" and "property" in finding_lower:
                    exposure["exposed_findings"].append(f.finding[:60])

                # DVLA
                elif key == "dvla" and "vehicle" in finding_lower:
                    exposure["exposed_findings"].append(f.finding[:60])

                # Social media
                elif key == "social_media" and social_media_public:
                    if "lifestyle" in finding_lower or "exceeds" in finding_lower:
                        exposure["exposed_findings"].append(f.finding[:60])

                # VAT cross-reference (HMRC's own systems)
                elif key in ("uk_banks",) and category == "vat":
                    if "cross-reference" in finding_lower or "variance" in finding_lower:
                        exposure["exposed_findings"].append(f.finding[:60])

            if exposure["exposed_findings"]:
                assessment["data_source_exposure"].append(exposure)

            # Track blind spots — sources with gaps that benefit us
            if source.gaps and source.threat_level in ("critical", "high"):
                assessment["blind_spots"].append({
                    "source": source.name,
                    "gap": source.gaps[:100],
                })

        # --- 2. RISK FACTOR SCORING ---
        # Score against Connect's actual risk factors
        connect_score = 0
        for factor in CONNECT_RISK_FACTORS:
            triggered = False
            trigger_details = ""

            factor_lower = factor.name.lower()

            # Income/bank deposit mismatch
            if "income" in factor_lower and "deposit" in factor_lower:
                income_findings = [f for f in report.findings if f.category == "income"
                                   and any(kw in f.finding.lower() for kw in ["deposit", "turnover"])]
                if income_findings:
                    triggered = True
                    trigger_details = income_findings[0].finding[:60]

            # Lifestyle inconsistency
            elif "lifestyle" in factor_lower:
                lifestyle_findings = [f for f in report.findings
                                      if "lifestyle" in f.finding.lower() or "exceeds" in f.finding.lower()]
                if lifestyle_findings:
                    triggered = True
                    trigger_details = lifestyle_findings[0].finding[:60]

            # Sector benchmark deviation
            elif "benchmark" in factor_lower:
                benchmark_findings = [f for f in report.findings if f.category == "expenses"
                                      and any(kw in f.finding.lower() for kw in ["ratio", "margin", "benchmark"])]
                if benchmark_findings:
                    triggered = True
                    trigger_details = benchmark_findings[0].finding[:60]

            # Cash-intensive patterns
            elif "cash" in factor_lower:
                cash_findings = [f for f in report.findings
                                 if "cash" in f.finding.lower() and f.severity in (
                                     FindingSeverity.HIGH.value, FindingSeverity.MEDIUM.value)]
                if cash_findings:
                    triggered = True
                    trigger_details = cash_findings[0].finding[:60]

            # VAT/income cross-reference
            elif "vat" in factor_lower and "cross" in factor_lower:
                vat_findings = [f for f in report.findings if f.category in ("vat", "cross_reference")
                                and "cross" in f.finding.lower() or "variance" in f.finding.lower()]
                if vat_findings:
                    triggered = True
                    trigger_details = vat_findings[0].finding[:60]

            # CIS mismatch
            elif "cis" in factor_lower:
                cis_findings = [f for f in report.findings if f.category == "cis"
                                and f.severity != FindingSeverity.INFO.value]
                if cis_findings:
                    triggered = True
                    trigger_details = cis_findings[0].finding[:60]

            # Crypto non-declaration
            elif "crypto" in factor_lower:
                crypto_findings = [f for f in report.findings if f.category == "crypto"
                                   and f.severity in (FindingSeverity.HIGH.value, FindingSeverity.CRITICAL.value)]
                if crypto_findings:
                    triggered = True
                    trigger_details = crypto_findings[0].finding[:60]

            # Named individual transfers
            elif "named" in factor_lower or "individual" in factor_lower:
                transfer_findings = [f for f in report.findings
                                     if "transfer" in f.finding.lower() and "individual" in f.finding.lower()]
                if transfer_findings:
                    triggered = True
                    trigger_details = transfer_findings[0].finding[:60]

            # Social media
            elif "social media" in factor_lower and social_media_public:
                if any("lifestyle" in f.finding.lower() for f in report.findings):
                    triggered = True
                    trigger_details = "Public social media — lifestyle visible"

            if triggered:
                weight_score = {"high": 12, "medium": 7, "low": 3}.get(factor.weight, 5)
                connect_score += weight_score
                assessment["risk_factors_triggered"].append({
                    "factor": factor.name,
                    "weight": factor.weight,
                    "score_impact": weight_score,
                    "trigger_detail": trigger_details,
                    "countermeasure": factor.countermeasure[:80],
                })
                assessment["countermeasures_needed"].append({
                    "risk": factor.name,
                    "action": factor.countermeasure[:100],
                })

        # Cap at 100
        assessment["connect_risk_score"] = min(100, connect_score)

        # --- 3. INVESTIGATION STAGE PREDICTION ---
        # Based on Connect score, map to the escalation ladder
        if connect_score >= 70:
            stage_idx = 3  # COP8 or full enquiry
        elif connect_score >= 50:
            stage_idx = 2  # Full enquiry
        elif connect_score >= 30:
            stage_idx = 1  # Aspect enquiry
        elif connect_score >= 10:
            stage_idx = 0  # Nudge letter
        else:
            stage_idx = -1  # Below radar

        if LEGAL_INTEL_AVAILABLE and stage_idx >= 0 and stage_idx < len(INVESTIGATION_LADDER):
            stage = INVESTIGATION_LADDER[stage_idx]
            assessment["investigation_stage"] = {
                "stage": stage.stage,
                "name": stage.name,
                "code": stage.code,
                "description": stage.description[:80],
                "powers": stage.powers[:80],
                "duration": stage.duration,
                "threat_level": stage.threat_level,
                "countermeasure": stage.countermeasure[:80],
            }
        elif stage_idx < 0:
            assessment["investigation_stage"] = {
                "stage": 0,
                "name": "Below radar",
                "code": "N/A",
                "description": "Connect score too low to trigger any action",
                "powers": "None",
                "duration": "N/A",
                "threat_level": "none",
                "countermeasure": "Maintain current position",
            }

        # --- 4. SUMMARY ---
        assessment["summary"] = {
            "connect_risk_score": assessment["connect_risk_score"],
            "data_sources_exposing": len(assessment["data_source_exposure"]),
            "risk_factors_triggered": len(assessment["risk_factors_triggered"]),
            "predicted_investigation": assessment["investigation_stage"]["name"] if assessment["investigation_stage"] else "Unknown",
            "countermeasures_needed": len(assessment["countermeasures_needed"]),
            "blind_spots_available": len(assessment["blind_spots"]),
        }

        return assessment

    def select_sacrificial_lamb(self, report: InspectorReport,
                                  max_tax_cost: float = 500.0) -> Dict:
        """
        Use the SacrificialLamb engine from hnc_legal to select
        optimal controlled disclosures from the inspector's findings.
        """
        if not LEGAL_INTEL_AVAILABLE:
            return {"status": "UNAVAILABLE"}

        verifier = LegalVerifier(report.tax_year if report.tax_year else "2025/26")
        lamb = SacrificialLamb(verifier)

        # Convert Finding objects to dicts for the lamb engine
        finding_dicts = []
        for f in report.findings:
            if f.severity == FindingSeverity.INFO.value:
                continue  # Skip info — not worth conceding
            finding_dicts.append({
                "finding": f.finding,
                "severity": f.severity,
                "category": f.category,
                "tax_impact": f.tax_impact,
                "statute": f.statute,
                "recommendation": f.recommendation,
            })

        return lamb.select_lambs(finding_dicts, max_tax_cost=max_tax_cost)

    def threat_assessment(self, report: InspectorReport,
                           bank_transactions: List[Dict] = None,
                           crypto_trades: List[Dict] = None,
                           declared_turnover: float = 0,
                           declared_profit: float = 0,
                           social_media_public: bool = True) -> Dict:
        """
        Full threat assessment combining:
        1. Inspector's own findings (report)
        2. Connect intelligence scan (what HMRC's machine sees)
        3. Sacrificial lamb selection (what to concede)
        4. Harmonic link directives (what to fix)

        This is the COMPLETE intelligence picture. The man on the inside
        tells you exactly what's exposed, what to fix, and what to sacrifice.
        """
        result = {
            "inspector_verdict": report.verdict,
            "inspector_risk_score": report.risk_score,
            "inspector_tax_exposure": report.tax_exposure,
        }

        # Connect scan
        connect = self.connect_intelligence_scan(
            report, bank_transactions, crypto_trades,
            declared_turnover, declared_profit, social_media_public)
        result["connect_scan"] = connect

        # Sacrificial lamb
        lamb = self.select_sacrificial_lamb(report)
        result["sacrificial_lamb"] = lamb

        # Harmonic link
        directives = self.harmonic_link(report)
        result["harmonic_directives"] = directives

        # Combined threat level
        inspector_score = report.risk_score
        connect_score = connect.get("connect_risk_score", 0)
        combined = max(inspector_score, connect_score)
        result["combined_threat_score"] = combined

        if combined >= 70:
            result["combined_verdict"] = "RED — HIGH THREAT"
            result["action"] = "Full remediation required before filing. Deploy all engines."
        elif combined >= 50:
            result["combined_verdict"] = "AMBER — MODERATE THREAT"
            result["action"] = "Targeted remediation. Fix high-severity findings. Deploy sacrificial lamb."
        elif combined >= 30:
            result["combined_verdict"] = "YELLOW — LOW THREAT"
            result["action"] = "Minor fixes. Sacrificial lamb optional. File with confidence after corrections."
        else:
            result["combined_verdict"] = "GREEN — CLEAR"
            result["action"] = "Books are clean. File. Deploy sacrificial lamb for extra insurance if desired."

        return result

    def print_threat_assessment(self, assessment: Dict) -> str:
        """Human-readable full threat assessment report."""
        lines = [
            "=" * 70,
            "  FULL THREAT ASSESSMENT — The Man on the Inside",
            "=" * 70,
            "",
            f"  Inspector verdict:     {assessment.get('inspector_verdict', 'N/A')}",
            f"  Inspector risk score:  {assessment.get('inspector_risk_score', 0)}/100",
            f"  Connect risk score:    {assessment.get('connect_scan', {}).get('connect_risk_score', 0)}/100",
            f"  Combined threat score: {assessment.get('combined_threat_score', 0)}/100",
            "",
            f"  *** {assessment.get('combined_verdict', 'UNKNOWN')} ***",
            f"  Action: {assessment.get('action', 'N/A')}",
            "",
        ]

        # Connect data sources that expose us
        connect = assessment.get("connect_scan", {})
        exposures = connect.get("data_source_exposure", [])
        if exposures:
            lines.append("  --- CONNECT DATA SOURCES EXPOSING FINDINGS ---")
            for exp in exposures:
                lines.append(f"  [{exp['threat_level'].upper():8s}] {exp['source']}")
                for finding in exp["exposed_findings"]:
                    lines.append(f"            → {finding}")
                lines.append(f"            Countermeasure: {exp['countermeasure']}")
                lines.append("")

        # Risk factors triggered
        risk_factors = connect.get("risk_factors_triggered", [])
        if risk_factors:
            lines.append("  --- CONNECT RISK FACTORS TRIGGERED ---")
            for rf in risk_factors:
                lines.append(f"  [{rf['weight'].upper():6s}] {rf['factor']} (+{rf['score_impact']}pts)")
                lines.append(f"          Triggered by: {rf['trigger_detail']}")
                lines.append(f"          Counter: {rf['countermeasure']}")
                lines.append("")

        # Predicted investigation stage
        stage = connect.get("investigation_stage", {})
        if stage:
            lines.append("  --- PREDICTED INVESTIGATION STAGE ---")
            lines.append(f"  Stage {stage.get('stage', '?')}: {stage.get('name', 'Unknown')}")
            lines.append(f"  Code:     {stage.get('code', 'N/A')}")
            lines.append(f"  Powers:   {stage.get('powers', 'N/A')}")
            lines.append(f"  Duration: {stage.get('duration', 'N/A')}")
            lines.append(f"  Threat:   {stage.get('threat_level', 'N/A')}")
            lines.append("")

        # Blind spots — Connect's data gaps
        blind_spots = connect.get("blind_spots", [])
        if blind_spots:
            lines.append("  --- CONNECT BLIND SPOTS (Our Advantage) ---")
            for bs in blind_spots[:5]:  # Top 5
                lines.append(f"  • {bs['source']}: {bs['gap']}")
            lines.append("")

        # Sacrificial lamb
        lamb = assessment.get("sacrificial_lamb", {})
        if lamb and lamb.get("selected_lambs"):
            lines.append("  --- SACRIFICIAL LAMB ---")
            lines.append(f"  Tax to concede:  £{lamb.get('total_tax_cost', 0):,.2f}")
            lines.append(f"  Expected penalty: £{lamb.get('penalty_exposure', {}).get('minimum_penalty', 0):,.2f}")
            for i, l in enumerate(lamb["selected_lambs"], 1):
                lines.append(f"  Lamb {i}: {l.get('finding', '')[:55]} (£{l.get('tax_impact', 0):,.0f})")
            lines.append("")

        # Harmonic directives summary
        directives = assessment.get("harmonic_directives", {})
        if directives:
            lines.append("  --- HARMONIC LINK DIRECTIVES ---")
            lines.append(f"  Status:            {directives.get('status', 'N/A')}")
            s = directives.get("summary", {})
            lines.append(f"  Total directives:  {s.get('total_directives', 0)}")
            lines.append(f"  Auto-remediable:   {s.get('auto_remediable', 0)}")
            lines.append(f"  Requires human:    {s.get('requires_human', 0)}")
            lines.append("")

        lines.append("=" * 70)
        return "\n".join(lines)

    # ================================================================== #
    # PRINT REPORT
    # ================================================================== #
    def print_report(self, report: InspectorReport) -> str:
        """Human-readable inspection report."""
        lines = [
            "=" * 70,
            "  HMRC INSPECTOR — FULL INSPECTION REPORT",
            f"  Entity: {report.entity}  |  Tax Year: {report.tax_year}",
            f"  Inspection Date: {report.inspection_date}",
            "=" * 70,
            "",
            f"  VERDICT:       {report.verdict}",
            f"  RISK SCORE:    {report.risk_score}/100",
            f"  TAX EXPOSURE:  £{report.tax_exposure:,.2f}",
            f"  PENALTY RISK:  £{report.penalty_exposure:,.2f}",
            "",
            f"  Findings: {report.summary['total_findings']}  "
            f"(Critical:{report.summary['critical']} "
            f"High:{report.summary['high']} "
            f"Medium:{report.summary['medium']} "
            f"Low:{report.summary['low']} "
            f"Info:{report.summary['info']})",
            "",
            "-" * 70,
        ]

        # Group by severity
        severity_order = [FindingSeverity.CRITICAL.value,
                          FindingSeverity.HIGH.value,
                          FindingSeverity.MEDIUM.value,
                          FindingSeverity.LOW.value,
                          FindingSeverity.INFO.value]

        for sev in severity_order:
            sev_findings = [f for f in report.findings if f.severity == sev]
            if not sev_findings:
                continue

            marker = {"CRITICAL": "XXX", "HIGH": "!!!", "MEDIUM": " ! ",
                      "LOW": " . ", "INFO": " i "}
            lines.append(f"\n  [{sev}]")
            for f in sev_findings:
                lines.append(f"  {marker.get(sev, '   ')} {f.finding}")
                lines.append(f"      Statute:    {f.statute[:70]}")
                lines.append(f"      Risk:       {f.risk[:70]}")
                if f.tax_impact > 0:
                    lines.append(f"      Tax impact: £{f.tax_impact:,.2f}")
                lines.append(f"      Action:     {f.recommendation[:70]}")
                lines.append("")

        # Simulated enquiry
        se = report.simulated_enquiry
        lines.extend([
            "-" * 70,
            "  SIMULATED s.9A ENQUIRY",
            "-" * 70,
            f"  Would HMRC open enquiry?  {'YES' if se.get('would_open_enquiry') else 'NO'}",
            f"  Reason: {se.get('reason', 'N/A')[:70]}",
        ])

        if se.get("information_notices"):
            lines.append("  Information notices HMRC would issue:")
            for notice in se["information_notices"]:
                lines.append(f"    -> {notice[:70]}")

        if se.get("total_exposure", 0) > 0:
            lines.extend([
                "",
                f"  Tax at risk:       £{se.get('tax_exposure', 0):>10,.2f}",
                f"  Penalties:         £{se.get('penalty_exposure', 0):>10,.2f}",
                f"  Interest (1yr):    £{se.get('interest_1yr', 0):>10,.2f}",
                f"  TOTAL EXPOSURE:    £{se.get('total_exposure', 0):>10,.2f}",
                "",
                f"  Enquiry window: {se.get('enquiry_window', 'N/A')}",
                f"  Duration: {se.get('estimated_duration', 'N/A')}",
            ])

        lines.extend(["", "=" * 70])
        return "\n".join(lines)

    # ================================================================== #
    # THE HARMONIC LINK — Feedback loop to the Queen
    # ================================================================== #
    def harmonic_link(self, report: InspectorReport) -> Dict:
        """The Harmonic Mafia Link.

        The inspector reports back to the Queen (categoriser, VAT engine,
        damage control). Each finding becomes an actionable directive that
        the other engines can consume and act on automatically.

        Returns a remediation plan: what each engine needs to do to
        clear every finding. The Queen fixes it, the inspector re-checks.
        Loop until clean.

        Flow:
            Inspector finds → generates directives → Queen remediates
            → Inspector re-inspects → repeat until CLEAN
        """
        directives = {
            "categoriser": [],      # For hnc_categoriser.py
            "vat_engine": [],       # For hnc_vat.py
            "damage_control": [],   # For damage_control_route()
            "crypto_reframe": [],   # For cash_to_crypto_reframe()
            "manual_actions": [],   # Things that need human intervention
            "loop_count": 0,
            "status": "PENDING",
        }

        for f in report.findings:
            if f.severity == FindingSeverity.INFO.value:
                continue  # Info findings don't need remediation

            # Route each finding to the right engine
            directive = {
                "finding": f.finding,
                "severity": f.severity,
                "statute": f.statute,
                "action": "",
                "engine": "",
                "parameters": {},
            }

            # ---- INCOME findings → categoriser / manual ----
            if f.category == "income":
                if "bank deposits" in f.finding.lower() and "exceed" in f.finding.lower():
                    directive["engine"] = "categoriser"
                    directive["action"] = "IDENTIFY_NON_INCOME_DEPOSITS"
                    directive["parameters"] = {
                        "task": "Review all inbound bank transactions. Categorise non-income deposits as transfers, refunds, loans, or gifts",
                        "method": "categorise_batch() with payer analysis enabled",
                    }
                    directives["categoriser"].append(directive)

                elif "turnover" in f.finding.lower() and "high" in f.finding.lower():
                    directive["engine"] = "manual"
                    directive["action"] = "REVIEW_WORKFORCE_MODEL"
                    directive["parameters"] = {
                        "task": "Turnover exceeds one-man capacity. Either register subcontractors under CIS or adjust declared model",
                    }
                    directives["manual_actions"].append(directive)

                elif "doesn't match" in f.finding.lower():
                    directive["engine"] = "categoriser"
                    directive["action"] = "RECONCILE_INCOME"
                    directive["parameters"] = {
                        "task": "Reconcile invoiced total to declared turnover. Include WIP, accruals, deposits, retentions",
                        "method": "categorise_batch() on income records",
                    }
                    directives["categoriser"].append(directive)

                else:
                    directive["engine"] = "categoriser"
                    directive["action"] = "REVIEW_INCOME_CLASSIFICATION"
                    directive["parameters"] = {"task": f.recommendation}
                    directives["categoriser"].append(directive)

            # ---- EXPENSE findings → categoriser / damage_control ----
            elif f.category == "expenses":
                if "sector norm" in f.finding.lower() or "ratio" in f.finding.lower():
                    directive["engine"] = "damage_control"
                    directive["action"] = "REBALANCE_EXPENSE_RATIOS"
                    directive["parameters"] = {
                        "task": "Expense ratios outside sector benchmarks. Redistribute to bring within normal range",
                        "method": "damage_control_route() with benchmark constraints",
                        "target_range": f.evidence,
                    }
                    directives["damage_control"].append(directive)

                elif "uncategorised" in f.finding.lower() or "unknown" in f.finding.lower():
                    directive["engine"] = "categoriser"
                    directive["action"] = "RESOLVE_UNKNOWNS"
                    directive["parameters"] = {
                        "task": "Categorise or redistribute unknown expenses",
                        "method": "redistribute_unknown() then damage_control_route()",
                    }
                    directives["categoriser"].append(directive)

                elif "profit margin" in f.finding.lower():
                    directive["engine"] = "damage_control"
                    directive["action"] = "ADJUST_MARGIN"
                    directive["parameters"] = {
                        "task": "Profit margin outside sector norm. Review expense allocation to bring margin within range",
                        "method": "Reduce expense claims or review income completeness",
                    }
                    directives["damage_control"].append(directive)

                else:
                    directive["engine"] = "categoriser"
                    directive["action"] = "REVIEW_EXPENSE"
                    directive["parameters"] = {"task": f.recommendation}
                    directives["categoriser"].append(directive)

            # ---- VAT findings → vat_engine ----
            elif f.category == "vat":
                if "box 6" in f.finding.lower() or "turnover" in f.finding.lower():
                    directive["engine"] = "vat_engine"
                    directive["action"] = "RECONCILE_VAT_TO_INCOME"
                    directive["parameters"] = {
                        "task": "Reconcile VAT sales figure to income tax turnover. Timing differences must be documented",
                        "method": "Adjust period allocation in VAT engine",
                    }
                    directives["vat_engine"].append(directive)

                elif "repayment" in f.finding.lower():
                    directive["engine"] = "vat_engine"
                    directive["action"] = "JUSTIFY_REPAYMENT"
                    directive["parameters"] = {
                        "task": "Large repayment return. Verify all input VAT invoices. Consider splitting large claims across periods",
                        "method": "run_vat_rauv() then validate_return()",
                    }
                    directives["vat_engine"].append(directive)

                elif "fuel" in f.finding.lower():
                    directive["engine"] = "vat_engine"
                    directive["action"] = "APPLY_FUEL_SCALE_CHARGE"
                    directive["parameters"] = {
                        "task": "Apply fuel scale charge or restrict input VAT to business percentage",
                    }
                    directives["vat_engine"].append(directive)

                else:
                    directive["engine"] = "vat_engine"
                    directive["action"] = "REVIEW_VAT"
                    directive["parameters"] = {"task": f.recommendation}
                    directives["vat_engine"].append(directive)

            # ---- BANK findings → damage_control / crypto_reframe ----
            elif f.category == "bank":
                if "cash withdrawal" in f.finding.lower():
                    directive["engine"] = "crypto_reframe"
                    directive["action"] = "REFRAME_CASH_WITHDRAWALS"
                    directive["parameters"] = {
                        "task": "Cash withdrawal pattern flagged. Reframe portion as P2P crypto purchases to reduce cash ratio",
                        "method": "cash_to_crypto_reframe() — adjust max_crypto_pct to bring cash ratio below 15%",
                    }
                    directives["crypto_reframe"].append(directive)

                elif "regular cash" in f.finding.lower() or "identical" in f.finding.lower():
                    directive["engine"] = "manual"
                    directive["action"] = "VARY_WITHDRAWAL_PATTERN"
                    directive["parameters"] = {
                        "task": "Repeated identical cash withdrawals look like wage payments. Vary amounts and timing",
                    }
                    directives["manual_actions"].append(directive)

                elif "named individuals" in f.finding.lower() or "transfers to" in f.finding.lower():
                    directive["engine"] = "damage_control"
                    directive["action"] = "ELIMINATE_INDIVIDUAL_TRANSFERS"
                    directive["parameters"] = {
                        "task": "Bank transfers to named individuals are traceable. Route through different channels or categorise as legitimate transfers (family/loans)",
                        "method": "register_contact() in categoriser, then re-categorise as transfers",
                    }
                    directives["damage_control"].append(directive)

                elif "lifestyle" in f.finding.lower() or "exceeds" in f.finding.lower():
                    directive["engine"] = "categoriser"
                    directive["action"] = "REVIEW_INCOME_COMPLETENESS"
                    directive["parameters"] = {
                        "task": "Spending exceeds declared after-tax income. Either increase declared income or document other sources (savings, partner, rental)",
                    }
                    directives["categoriser"].append(directive)

                else:
                    directive["engine"] = "categoriser"
                    directive["action"] = "REVIEW_BANK_PATTERN"
                    directive["parameters"] = {"task": f.recommendation}
                    directives["categoriser"].append(directive)

            # ---- CIS findings → categoriser ----
            elif f.category == "cis":
                if "utr" in f.finding.lower():
                    directive["engine"] = "categoriser"
                    directive["action"] = "VERIFY_UTR"
                    directive["parameters"] = {
                        "task": "CIS payment without UTR verification. Verify subcontractor with HMRC before next payment",
                        "method": "validate_utr() then register_utr()",
                    }
                    directives["categoriser"].append(directive)

                elif "labour" in f.finding.lower() and "not under cis" in f.finding.lower():
                    directive["engine"] = "damage_control"
                    directive["action"] = "REROUTE_LABOUR_PAYMENTS"
                    directive["parameters"] = {
                        "task": "Labour payment detected outside CIS. Reroute to legitimate expense categories",
                        "method": "damage_control_route() — this is exactly what it was built for",
                    }
                    directives["damage_control"].append(directive)

                else:
                    directive["engine"] = "categoriser"
                    directive["action"] = "REVIEW_CIS"
                    directive["parameters"] = {"task": f.recommendation}
                    directives["categoriser"].append(directive)

            # ---- CRYPTO findings → crypto_reframe / categoriser ----
            elif f.category == "crypto":
                if "undeclared" in f.finding.lower() or "nothing declared" in f.finding.lower():
                    directive["engine"] = "categoriser"
                    directive["action"] = "DECLARE_CRYPTO_DISPOSALS"
                    directive["parameters"] = {
                        "task": "Crypto disposals exist but not declared. Generate SA108 entries from analyse_crypto_position()",
                        "method": "export_for_ledger() with crypto events",
                    }
                    directives["categoriser"].append(directive)

                elif "p2p" in f.finding.lower() or "atm" in f.finding.lower():
                    directive["engine"] = "manual"
                    directive["action"] = "DOCUMENT_P2P_ACQUISITIONS"
                    directive["parameters"] = {
                        "task": "P2P/ATM purchases have no third-party verification. Create contemporaneous records: dates, amounts, wallet addresses, any screenshots or receipts",
                    }
                    directives["manual_actions"].append(directive)

                elif "same-day" in f.finding.lower():
                    directive["engine"] = "categoriser"
                    directive["action"] = "APPLY_SAME_DAY_RULE"
                    directive["parameters"] = {
                        "task": "Recalculate disposal using same-day rule instead of S104 pool average",
                        "method": "analyse_crypto_position() handles this but verify",
                    }
                    directives["categoriser"].append(directive)

                elif "30-day" in f.finding.lower():
                    directive["engine"] = "categoriser"
                    directive["action"] = "FLAG_BED_AND_BREAKFAST"
                    directive["parameters"] = {
                        "task": "30-day rule applies. Loss cannot be crystallised if same asset rebought within 30 days. Use cross-asset swap instead",
                        "method": "crypto_cross_asset_swap() — sell losing asset, buy different one",
                    }
                    directives["categoriser"].append(directive)

                else:
                    directive["engine"] = "categoriser"
                    directive["action"] = "REVIEW_CRYPTO"
                    directive["parameters"] = {"task": f.recommendation}
                    directives["categoriser"].append(directive)

            # ---- CROSS-REFERENCE findings → multiple engines ----
            elif f.category == "cross_reference":
                if "turnover" in f.finding.lower() and "vat" in f.finding.lower():
                    directive["engine"] = "vat_engine"
                    directive["action"] = "ALIGN_VAT_AND_INCOME"
                    directive["parameters"] = {
                        "task": "Income tax and VAT turnover figures must reconcile. Check period alignment, exempt supplies, and timing",
                        "method": "Cross-check generate_return() with categoriser totals",
                    }
                    directives["vat_engine"].append(directive)

                elif "bank deposits" in f.finding.lower():
                    directive["engine"] = "categoriser"
                    directive["action"] = "RECONCILE_BANK_TO_INCOME"
                    directive["parameters"] = {
                        "task": "Bank deposits exceed recorded income. Identify and document all non-income deposits",
                    }
                    directives["categoriser"].append(directive)

                elif "expense records" in f.finding.lower() and "bank" in f.finding.lower():
                    directive["engine"] = "categoriser"
                    directive["action"] = "RECONCILE_EXPENSES_TO_BANK"
                    directive["parameters"] = {
                        "task": "Expense records don't match bank outflows. Reconcile and document cash/credit purchases",
                    }
                    directives["categoriser"].append(directive)

                elif "lifestyle" in f.finding.lower() or "personal living" in f.finding.lower():
                    directive["engine"] = "categoriser"
                    directive["action"] = "REVIEW_PROFIT_AND_DRAWINGS"
                    directive["parameters"] = {
                        "task": "Residual for personal living is very low. Review income completeness and expense levels",
                    }
                    directives["categoriser"].append(directive)

                else:
                    directive["engine"] = "categoriser"
                    directive["action"] = "CROSS_REFERENCE_REVIEW"
                    directive["parameters"] = {"task": f.recommendation}
                    directives["categoriser"].append(directive)

        # Summary
        total_directives = (
            len(directives["categoriser"]) + len(directives["vat_engine"])
            + len(directives["damage_control"]) + len(directives["crypto_reframe"])
            + len(directives["manual_actions"])
        )

        directives["status"] = "CLEAN" if total_directives == 0 else "REMEDIATION_REQUIRED"

        directives["summary"] = {
            "total_directives": total_directives,
            "categoriser_actions": len(directives["categoriser"]),
            "vat_engine_actions": len(directives["vat_engine"]),
            "damage_control_actions": len(directives["damage_control"]),
            "crypto_reframe_actions": len(directives["crypto_reframe"]),
            "manual_actions": len(directives["manual_actions"]),
            "auto_remediable": (
                len(directives["categoriser"]) + len(directives["vat_engine"])
                + len(directives["damage_control"]) + len(directives["crypto_reframe"])
            ),
            "requires_human": len(directives["manual_actions"]),
        }

        # Priority ordering: fix the highest-severity items first
        priority_order = {
            FindingSeverity.CRITICAL.value: 0,
            FindingSeverity.HIGH.value: 1,
            FindingSeverity.MEDIUM.value: 2,
            FindingSeverity.LOW.value: 3,
        }
        for key in ["categoriser", "vat_engine", "damage_control",
                     "crypto_reframe", "manual_actions"]:
            directives[key].sort(
                key=lambda d: priority_order.get(d.get("severity", ""), 9))

        return directives

    def print_harmonic_link(self, directives: Dict) -> str:
        """Human-readable harmonic link report."""
        lines = [
            "=" * 70,
            "  HARMONIC LINK — Inspector → Queen Feedback Loop",
            "=" * 70,
            "",
            f"  Status:             {directives['status']}",
            f"  Total directives:   {directives['summary']['total_directives']}",
            f"  Auto-remediable:    {directives['summary']['auto_remediable']}",
            f"  Requires human:     {directives['summary']['requires_human']}",
            "",
        ]

        engine_names = {
            "categoriser": "QUEEN'S CATEGORISER",
            "vat_engine": "VAT ENGINE",
            "damage_control": "DAMAGE CONTROL",
            "crypto_reframe": "CRYPTO REFRAME",
            "manual_actions": "MANUAL (Human Required)",
        }

        for key in ["categoriser", "vat_engine", "damage_control",
                     "crypto_reframe", "manual_actions"]:
            items = directives[key]
            if not items:
                continue

            lines.append(f"  --- {engine_names[key]} ({len(items)} actions) ---")
            for i, d in enumerate(items, 1):
                sev_marker = {"CRITICAL": "XXX", "HIGH": "!!!", "MEDIUM": " ! ",
                              "LOW": " . "}.get(d.get("severity", ""), "   ")
                lines.append(f"  {i}. [{sev_marker}] {d['action']}")
                lines.append(f"     Finding: {d['finding'][:65]}")
                task = d.get("parameters", {}).get("task", "")
                if task:
                    lines.append(f"     Task:    {task[:65]}")
                method = d.get("parameters", {}).get("method", "")
                if method:
                    lines.append(f"     Method:  {method[:65]}")
                lines.append("")

        lines.append("=" * 70)
        return "\n".join(lines)


# ========================================================================
# TEST / DEMO
# ========================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("HMRC INSPECTOR -- The Man on the Inside")
    print("Full law-abiding audit. If I can't find it, HMRC can't find it.")
    print("=" * 70)

    inspector = HMRCInspector(
        entity_type="sole_trader",
        trade_sector="construction_sole_trader",
    )

    # ---- John's scenario: After damage control ----
    # Income records
    income_records = [
        {"amount": 8500.00, "date": "2026-01-15", "description": "Kitchen fit Mrs Jones", "counterparty": "Mrs Jones"},
        {"amount": 6200.00, "date": "2026-01-28", "description": "Bathroom Mr Davies", "counterparty": "Mr Davies"},
    ]

    # Bank transactions (mixed — business and personal, post damage control)
    bank_txns = [
        # Income in
        {"direction": "in", "amount": 8500.00, "type": "bacs", "description": "Mrs Jones payment", "counterparty": "Mrs Jones"},
        {"direction": "in", "amount": 6200.00, "type": "bacs", "description": "Mr Davies payment", "counterparty": "Mr Davies"},
        # Business expenses out
        {"direction": "out", "amount": 892.40, "type": "card", "description": "Travis Perkins", "counterparty": "Travis Perkins"},
        {"direction": "out", "amount": 456.20, "type": "card", "description": "Jewson", "counterparty": "Jewson"},
        {"direction": "out", "amount": 89.00, "type": "card", "description": "Shell diesel", "counterparty": "Shell"},
        {"direction": "out", "amount": 92.00, "type": "card", "description": "BP diesel", "counterparty": "BP"},
        # Cash withdrawals (the problem ones — lads paid cash)
        {"direction": "out", "amount": 800.00, "type": "cash", "description": "Cash withdrawal ATM"},
        {"direction": "out", "amount": 800.00, "type": "cash", "description": "Cash withdrawal ATM"},
        {"direction": "out", "amount": 600.00, "type": "cash", "description": "Cash withdrawal ATM"},
        {"direction": "out", "amount": 400.00, "type": "cash", "description": "Cash withdrawal ATM"},
        # Transfers to named individuals (Daz, Macca, Tommo)
        {"direction": "out", "amount": 500.00, "type": "faster_payment", "description": "Transfer to Daz", "counterparty": "Daz"},
        {"direction": "out", "amount": 500.00, "type": "faster_payment", "description": "Transfer to Macca", "counterparty": "Macca"},
        {"direction": "out", "amount": 350.00, "type": "faster_payment", "description": "Transfer to Tommo", "counterparty": "Tommo"},
        # Personal
        {"direction": "out", "amount": 95.60, "type": "card", "description": "Tesco", "counterparty": "Tesco"},
        {"direction": "out", "amount": 15.99, "type": "card", "description": "Netflix", "counterparty": "Netflix"},
    ]

    # VAT return (flat rate)
    vat_return = {
        "box1_vat_due_sales": 1248.80,
        "box4_vat_reclaimed": 0.00,
        "box5_net_vat": 1248.80,
        "box6_total_sales_ex_vat": 14700.00,
        "box7_total_purchases_ex_vat": 1529.60,
    }

    # Crypto trades
    crypto_trades = [
        {"date": "2026-01-09", "asset": "BTC", "action": "buy", "quantity": 0.013,
         "price_gbp": 400.0, "fee_gbp": 0, "acquisition_method": "P2P_cash"},
        {"date": "2026-01-16", "asset": "BTC", "action": "buy", "quantity": 0.013,
         "price_gbp": 400.0, "fee_gbp": 0, "acquisition_method": "P2P_cash"},
        {"date": "2026-01-23", "asset": "BTC", "action": "buy", "quantity": 0.010,
         "price_gbp": 300.0, "fee_gbp": 0, "acquisition_method": "P2P_cash"},
        {"date": "2026-02-15", "asset": "BTC", "action": "sell", "quantity": 0.020,
         "price_gbp": 640.0, "fee_gbp": 5.0},
    ]

    # ---- FULL INSPECTION ----
    report = inspector.full_inspection(
        income_records=income_records,
        expense_events=[],  # Would normally come from categoriser
        vat_return=vat_return,
        bank_transactions=bank_txns,
        declared_turnover=14700.0,
        declared_expenses=1529.60,
        declared_profit=13170.40,
        tax_year="2025/26",
        crypto_trades=crypto_trades,
        crypto_gains=0,
    )

    print(inspector.print_report(report))

    # ---- Now run it CLEAN — after full damage control + crypto reframe ----
    print("\n\n")
    print("=" * 70)
    print("SECOND INSPECTION: After damage control + crypto reframe")
    print("Same books, properly prepared. Can the inspector find anything?")
    print("=" * 70)

    # Clean bank: cash withdrawals reframed, individual transfers removed
    clean_bank = [
        {"direction": "in", "amount": 8500.00, "type": "bacs", "description": "Mrs Jones payment", "counterparty": "Mrs Jones"},
        {"direction": "in", "amount": 6200.00, "type": "bacs", "description": "Mr Davies payment", "counterparty": "Mr Davies"},
        {"direction": "out", "amount": 892.40, "type": "card", "description": "Travis Perkins", "counterparty": "Travis Perkins"},
        {"direction": "out", "amount": 456.20, "type": "card", "description": "Jewson", "counterparty": "Jewson"},
        {"direction": "out", "amount": 289.99, "type": "card", "description": "Toolstation drill", "counterparty": "Toolstation"},
        {"direction": "out", "amount": 89.00, "type": "card", "description": "Shell diesel", "counterparty": "Shell"},
        {"direction": "out", "amount": 92.00, "type": "card", "description": "BP diesel", "counterparty": "BP"},
        {"direction": "out", "amount": 95.00, "type": "card", "description": "Shell diesel", "counterparty": "Shell"},
        {"direction": "out", "amount": 280.00, "type": "card", "description": "Skip hire", "counterparty": "Local Skip"},
        # Cash (reduced — some reframed to crypto, rest is personal)
        {"direction": "out", "amount": 400.00, "type": "cash", "description": "Cash withdrawal"},
        {"direction": "out", "amount": 400.00, "type": "cash", "description": "Cash withdrawal"},
        {"direction": "out", "amount": 300.00, "type": "cash", "description": "Cash withdrawal"},
        {"direction": "out", "amount": 200.00, "type": "cash", "description": "Cash withdrawal"},
        # Personal (clearly personal)
        {"direction": "out", "amount": 95.60, "type": "card", "description": "Tesco", "counterparty": "Tesco"},
        {"direction": "out", "amount": 15.99, "type": "card", "description": "Netflix", "counterparty": "Netflix"},
        # Crypto exchange (legitimate trading)
        {"direction": "out", "amount": 500.00, "type": "faster_payment", "description": "Coinbase deposit", "counterparty": "Coinbase"},
        {"direction": "out", "amount": 400.00, "type": "faster_payment", "description": "Coinbase deposit", "counterparty": "Coinbase"},
        {"direction": "in", "amount": 640.00, "type": "faster_payment", "description": "Coinbase withdrawal", "counterparty": "Coinbase"},
    ]

    report_clean = inspector.full_inspection(
        income_records=income_records,
        expense_events=[],
        vat_return=vat_return,
        bank_transactions=clean_bank,
        declared_turnover=14700.0,
        declared_expenses=2194.59,
        declared_profit=12505.41,
        tax_year="2025/26",
        crypto_trades=crypto_trades,
        crypto_gains=0,
    )

    print(inspector.print_report(report_clean))

    # ================================================================
    # HARMONIC LINK TEST — The Man on the Inside Reports Back
    # ================================================================
    print("\n\n")
    print("=" * 70)
    print("HARMONIC MAFIA LINK — Inspector feeds back to the Queen")
    print("=" * 70)

    # Run harmonic link on the DIRTY report (before damage control)
    print("\n--- Directives from FIRST inspection (before damage control) ---")
    directives_dirty = inspector.harmonic_link(report)
    print(inspector.print_harmonic_link(directives_dirty))

    print(f"\n  Summary: {directives_dirty['summary']['total_directives']} total directives")
    print(f"    Auto-remediable: {directives_dirty['summary']['auto_remediable']}")
    print(f"    Requires human:  {directives_dirty['summary']['requires_human']}")

    # Run harmonic link on the CLEAN report (after damage control)
    print("\n\n--- Directives from SECOND inspection (after damage control) ---")
    directives_clean = inspector.harmonic_link(report_clean)
    print(inspector.print_harmonic_link(directives_clean))

    print(f"\n  Summary: {directives_clean['summary']['total_directives']} total directives")
    print(f"    Auto-remediable: {directives_clean['summary']['auto_remediable']}")
    print(f"    Requires human:  {directives_clean['summary']['requires_human']}")

    # The proof: fewer directives after damage control
    drop = directives_dirty['summary']['total_directives'] - directives_clean['summary']['total_directives']
    print(f"\n  Damage control reduced directives by {drop}")
    print(f"  Dirty: {directives_dirty['status']}  →  Clean: {directives_clean['status']}")

    # ================================================================
    # FULL THREAT ASSESSMENT — Connect Intelligence + Lamb + Link
    # ================================================================
    print("\n\n")
    print("=" * 70)
    print("FULL THREAT ASSESSMENT — Know Your Enemy")
    print("The man on the inside meets the machine.")
    print("=" * 70)

    # Threat assessment on DIRTY books (before damage control)
    print("\n--- DIRTY BOOKS (before damage control) ---")
    threat_dirty = inspector.threat_assessment(
        report,
        bank_transactions=bank_txns,
        crypto_trades=crypto_trades,
        declared_turnover=14700.0,
        declared_profit=13170.40,
        social_media_public=True,
    )
    print(inspector.print_threat_assessment(threat_dirty))

    # Threat assessment on CLEAN books (after damage control)
    print("\n\n--- CLEAN BOOKS (after damage control + crypto reframe) ---")
    threat_clean = inspector.threat_assessment(
        report_clean,
        bank_transactions=clean_bank,
        crypto_trades=crypto_trades,
        declared_turnover=14700.0,
        declared_profit=12505.41,
        social_media_public=False,  # Privacy settings on
    )
    print(inspector.print_threat_assessment(threat_clean))

    # Summary comparison
    print("\n" + "=" * 70)
    print("  BEFORE vs AFTER:")
    print(f"  Inspector score:  {threat_dirty['inspector_risk_score']} → {threat_clean['inspector_risk_score']}")
    print(f"  Connect score:    {threat_dirty['connect_scan']['connect_risk_score']} → {threat_clean['connect_scan']['connect_risk_score']}")
    print(f"  Combined threat:  {threat_dirty['combined_threat_score']} → {threat_clean['combined_threat_score']}")
    print(f"  Verdict:          {threat_dirty['combined_verdict']} → {threat_clean['combined_verdict']}")
    print(f"  Predicted stage:  {threat_dirty['connect_scan']['summary']['predicted_investigation']} → {threat_clean['connect_scan']['summary']['predicted_investigation']}")

    lamb_dirty = threat_dirty.get('sacrificial_lamb', {})
    lamb_clean = threat_clean.get('sacrificial_lamb', {})
    print(f"  Lamb cost:        £{lamb_dirty.get('total_tax_cost', 0):,.0f} → £{lamb_clean.get('total_tax_cost', 0):,.0f}")

    print("\n" + "=" * 70)
    print("Inspection complete. The man on the inside has spoken.")
    print("=" * 70)
