"""
CIS RECONCILIATION ENGINE — cis_reconciliation.py
====================================================
Reconciles bank statement NET payments against GROSS invoices.

The bank only shows NET amounts (after CIS 20% + CITB 0.7% deductions).
This module:
    1. Holds the complete invoice schedule from Construction Client Alpha
    2. Grosses up bank income to true GROSS figures
    3. Tracks CIS deductions as reclaimable tax credits
    4. Tracks CITB levy as allowable business expense
    5. Identifies outstanding/unpaid invoices
    6. Cross-references SubContractor Monthly Statements

CIS Deduction Formula:
    Invoice Gross = stated gross amount
    CITB Levy = 0.7% of Gross
    Gross less CITB = Gross - CITB
    CIS Deduction = 20% of (Gross less CITB)
    NET paid to bank = Gross - CITB - CIS

    Reverse: Given NET, Gross = NET / (1 - 0.007) / (1 - 0.20) ≈ NET / 0.7944
    More precisely: NET = Gross * (1 - 0.007) * (1 - 0.20)
                    NET = Gross * 0.993 * 0.80
                    NET = Gross * 0.7944
                    Gross = NET / 0.7944

Legal basis:
    - Finance Act 2004, Part 3, Chapter 3 — CIS scheme
    - Income Tax (Construction Industry Scheme) Regulations 2005
    - CIS deductions are tax already paid — reclaimable via SA return
    - CITB Levy: Industrial Training Act 1982 — allowable business expense

Aureon Creator / Aureon Research — April 2026
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import logging

logger = logging.getLogger("cis_reconciliation")


@dataclass
class CISInvoice:
    """Single invoice to Construction Client Alpha."""
    invoice_number: str
    invoice_date: date
    service_period: str          # e.g. "Month to 5/10/25"
    period_end: date             # The 5th of month end date
    gross: float                 # Total invoice gross
    citb_levy: float             # 0.7% of gross
    gross_less_citb: float       # Gross - CITB
    cis_deduction: float         # 20% of gross_less_citb
    net_payable: float           # What hits the bank
    paid: bool = True            # Has Grove paid this?
    payment_date: Optional[date] = None
    notes: str = ""


@dataclass
class CISStatement:
    """SubContractor Monthly Statement from Construction Client Alpha (official CIS record)."""
    month_ending: date
    gross_excl_citb: float       # "Gross amount paid (Excl VAT and CITB levy)"
    materials: float = 0.0
    amount_liable: float = 0.0
    cis_deducted: float = 0.0
    amount_payable: float = 0.0
    contractor_ref: str = "916/XZ54703"
    subcontractor_utr: str = "5851128031"
    subcontractor_crn: str = "NI696693"


# ========================================================================
# COMPLETE INVOICE SCHEDULE — Extracted from all uploaded documents
# ========================================================================

INVOICES: List[CISInvoice] = [
    # Back-dated batch (all invoiced 08 October 2025 for owed periods)
    CISInvoice(
        invoice_number="INV-10",
        invoice_date=date(2025, 10, 8),
        service_period="Month to 5 June 2025",
        period_end=date(2025, 6, 5),
        gross=1120.00,
        citb_levy=7.84,
        gross_less_citb=1112.16,
        cis_deduction=222.43,
        net_payable=889.73,
        notes="Back-dated invoice for month to 5/6/25"
    ),
    CISInvoice(
        invoice_number="INV-11",
        invoice_date=date(2025, 10, 8),
        service_period="Month to 5 July 2025",
        period_end=date(2025, 7, 5),
        gross=3815.00,
        citb_levy=26.71,
        gross_less_citb=3788.29,
        cis_deduction=757.66,
        net_payable=3030.64,
        notes="Back-dated invoice for month to 5/7/25"
    ),
    CISInvoice(
        invoice_number="INV-12",
        invoice_date=date(2025, 10, 8),
        service_period="Month to 5 August 2025",
        period_end=date(2025, 8, 5),
        gross=5740.00,
        citb_levy=40.18,
        gross_less_citb=5699.82,
        cis_deduction=1139.96,
        net_payable=4559.86,
        notes="Back-dated invoice for month to 5/8/25"
    ),
    CISInvoice(
        invoice_number="INV-09",
        invoice_date=date(2025, 10, 8),
        service_period="Month to 5 September 2025",
        period_end=date(2025, 9, 5),
        gross=3815.00,
        citb_levy=26.71,
        gross_less_citb=3788.29,
        cis_deduction=757.66,
        net_payable=3030.64,
        notes="Labour Services for Site Works — May 6th-9th 2025. CIS statement confirms month ending 05/09/2025."
    ),
    CISInvoice(
        invoice_number="INV-08",
        invoice_date=date(2025, 10, 8),
        service_period="Month to 5 October 2025",
        period_end=date(2025, 10, 5),
        gross=6255.90,
        citb_levy=44.10,
        gross_less_citb=6211.80,
        cis_deduction=1251.18,
        net_payable=5004.72,
        notes="Labour Services — March 6 / 5/10. CIS statement confirms Gross excl CITB = £6,255.90"
    ),
    # November 2025 — new format invoice
    CISInvoice(
        invoice_number="INV-12B",
        invoice_date=date(2025, 11, 10),
        service_period="Month to 5 November 2025",
        period_end=date(2025, 11, 5),
        gross=11340.00,
        citb_levy=79.38,
        gross_less_citb=11260.62,
        cis_deduction=2252.12,
        net_payable=9008.50,
        notes="Covers 3 labour periods: £3,920 + £3,780 + £3,640. New format invoice dated 10 Nov 2025."
    ),
    # January 2026
    CISInvoice(
        invoice_number="INV-13",
        invoice_date=date(2026, 1, 20),
        service_period="Month to 5 January 2026",
        period_end=date(2026, 1, 5),
        gross=2100.00,
        citb_levy=14.70,
        gross_less_citb=2085.30,
        cis_deduction=417.06,
        net_payable=1668.24,
        notes="New format invoice from Jan 2026"
    ),
    # February 2026
    CISInvoice(
        invoice_number="INV-15",
        invoice_date=date(2026, 2, 20),
        service_period="Month to 5 February 2026",
        period_end=date(2026, 2, 5),
        gross=8330.00,
        citb_levy=58.31,
        gross_less_citb=8271.69,
        cis_deduction=1654.34,
        net_payable=6617.35,
        notes="CIS statement confirms: Gross excl CITB £8,271.69, CIS £1,654.33"
    ),
    # March 2026
    CISInvoice(
        invoice_number="INV-14",
        invoice_date=date(2026, 3, 20),
        service_period="Month to 5 March 2026",
        period_end=date(2026, 3, 5),
        gross=8916.00,
        citb_levy=62.41,
        gross_less_citb=8853.59,
        cis_deduction=1770.72,
        net_payable=7082.87,
        notes="CIS statement confirms: Gross excl CITB £8,853.58, CIS £1,770.72"
    ),
]


# ========================================================================
# CIS MONTHLY STATEMENTS — Official Construction Client Alpha records
# ========================================================================

CIS_STATEMENTS: List[CISStatement] = [
    CISStatement(
        month_ending=date(2025, 6, 5),
        gross_excl_citb=1112.16,
        amount_liable=1112.16,
        cis_deducted=222.43,
        amount_payable=889.73,
    ),
    CISStatement(
        month_ending=date(2025, 8, 5),
        gross_excl_citb=5699.82,
        amount_liable=5699.82,
        cis_deducted=1139.97,
        amount_payable=4559.85,
    ),
    CISStatement(
        month_ending=date(2025, 9, 5),
        gross_excl_citb=3788.29,
        amount_liable=3788.29,
        cis_deducted=757.66,
        amount_payable=3030.63,
    ),
    CISStatement(
        month_ending=date(2025, 10, 5),
        gross_excl_citb=6255.90,
        amount_liable=6255.90,
        cis_deducted=1251.18,
        amount_payable=5004.72,
    ),
    CISStatement(
        month_ending=date(2026, 2, 5),
        gross_excl_citb=8271.69,
        amount_liable=8271.69,
        cis_deducted=1654.33,
        amount_payable=6617.36,
    ),
    CISStatement(
        month_ending=date(2026, 3, 5),
        gross_excl_citb=8853.58,
        amount_liable=8853.58,
        cis_deducted=1770.72,
        amount_payable=7082.86,
    ),
]


# ========================================================================
# OUTSTANDING / MISSING INVOICES (from handwritten notes)
# ========================================================================
# Handwritten note: "G Leckey owed 4 invoices: to 5/6, to 5/8, to 5/9, to 5/10"
# These were subsequently invoiced on 08 Oct 2025 (INV-08 through INV-12)
# Additional note: "Also need invoice to 5/10/25 + 5/11/25" — now covered
# Missing period: Month to 5/12/25 (December 2025) — no invoice found
# Missing period: Month to 5/7/25 — covered by INV-11

KNOWN_GAPS = [
    {"period": "Month to 5 December 2025", "period_end": date(2025, 12, 5),
     "status": "NO INVOICE FOUND", "notes": "Gap between Nov 2025 and Jan 2026 — check if work was done"},
]


class CISReconciliation:
    """
    CIS Reconciliation Engine.

    Reconciles bank NET payments against invoice GROSS amounts.
    Tracks CIS deductions as reclaimable tax credits.
    """

    def __init__(self):
        self.invoices = list(INVOICES)
        self.statements = list(CIS_STATEMENTS)
        self.gaps = list(KNOWN_GAPS)

    def get_invoices_by_tax_year(self, year_start: int = 2025) -> List[CISInvoice]:
        """Get invoices for a UK tax year (6 Apr year_start to 5 Apr year_start+1)."""
        ty_start = date(year_start, 4, 6)
        ty_end = date(year_start + 1, 4, 5)
        return [inv for inv in self.invoices
                if ty_start <= inv.period_end <= ty_end]

    def get_tax_year_totals(self, year_start: int = 2025) -> Dict:
        """Get CIS totals for a tax year."""
        invs = self.get_invoices_by_tax_year(year_start)
        return {
            "tax_year": f"{year_start}/{year_start + 1 - 2000}",
            "invoice_count": len(invs),
            "total_gross": sum(i.gross for i in invs),
            "total_citb": sum(i.citb_levy for i in invs),
            "total_cis_deducted": sum(i.cis_deduction for i in invs),
            "total_net_received": sum(i.net_payable for i in invs),
            "cis_tax_credit": sum(i.cis_deduction for i in invs),
            "citb_allowable_expense": sum(i.citb_levy for i in invs),
        }

    def gross_up_bank_amount(self, net_amount: float) -> Dict:
        """
        Given a NET bank payment from Construction Client Alpha, calculate the GROSS.
        Uses the CIS formula: NET = Gross * 0.993 * 0.80
        """
        gross = net_amount / (0.993 * 0.80)
        citb = gross * 0.007
        gross_less_citb = gross - citb
        cis = gross_less_citb * 0.20
        return {
            "net_banked": net_amount,
            "estimated_gross": round(gross, 2),
            "estimated_citb": round(citb, 2),
            "estimated_cis": round(cis, 2),
            "estimated_gross_less_citb": round(gross_less_citb, 2),
        }

    def match_bank_to_invoice(self, net_amount: float, tolerance: float = 2.0) -> Optional[CISInvoice]:
        """Try to match a bank NET amount to a known invoice."""
        for inv in self.invoices:
            if abs(inv.net_payable - net_amount) <= tolerance:
                return inv
        return None

    def get_full_schedule(self) -> List[Dict]:
        """Get the complete CIS schedule as a list of dicts for reporting."""
        schedule = []
        for inv in sorted(self.invoices, key=lambda x: x.period_end):
            # Try to find matching CIS statement
            matching_stmt = None
            for stmt in self.statements:
                if stmt.month_ending == inv.period_end:
                    matching_stmt = stmt
                    break

            schedule.append({
                "invoice": inv.invoice_number,
                "date": inv.invoice_date.isoformat(),
                "period": inv.service_period,
                "period_end": inv.period_end.isoformat(),
                "gross": inv.gross,
                "citb": inv.citb_levy,
                "gross_less_citb": inv.gross_less_citb,
                "cis_20pct": inv.cis_deduction,
                "net": inv.net_payable,
                "has_cis_statement": matching_stmt is not None,
                "statement_matches": (
                    matching_stmt is not None and
                    abs(matching_stmt.cis_deducted - inv.cis_deduction) < 2.0
                ),
                "tax_year": self._get_tax_year(inv.period_end),
                "notes": inv.notes,
            })
        return schedule

    def get_reconciliation_summary(self) -> Dict:
        """Get a full reconciliation summary across all tax years."""
        ty_2024 = self.get_tax_year_totals(2024)
        ty_2025 = self.get_tax_year_totals(2025)

        return {
            "company": "Aureon Consulting Entity and Brokerage Services Ltd",
            "crn": "NI696693",
            "vat": "469976605",
            "utr": "5851128031",
            "contractor": "Construction Client Alpha Ltd",
            "contractor_ref": "916/XZ54703",
            "cis_rate": "20% (verified subcontractor)",
            "citb_rate": "0.7%",
            "tax_years": {
                "2024/25": ty_2024,
                "2025/26": ty_2025,
            },
            "total_invoices": len(self.invoices),
            "total_statements": len(self.statements),
            "statements_matched": sum(
                1 for inv in self.invoices
                if any(abs(s.month_ending - inv.period_end).days == 0
                       for s in self.statements)
            ),
            "known_gaps": self.gaps,
            "vat_reverse_charge": True,
        }

    @staticmethod
    def _get_tax_year(d: date) -> str:
        """Determine UK tax year for a date."""
        if d.month > 4 or (d.month == 4 and d.day >= 6):
            return f"{d.year}/{d.year + 1 - 2000}"
        else:
            return f"{d.year - 1}/{d.year - 2000}"


# Quick verification
if __name__ == "__main__":
    cis = CISReconciliation()

    print("=" * 70)
    print("CIS RECONCILIATION — Aureon Consulting Entity / Construction Client Alpha")
    print("=" * 70)

    for entry in cis.get_full_schedule():
        print(f"\n{entry['invoice']:8s} | {entry['period']:30s} | "
              f"Gross £{entry['gross']:>10,.2f} | CIS £{entry['cis_20pct']:>8,.2f} | "
              f"Net £{entry['net']:>10,.2f} | "
              f"{'✓ STMT' if entry['has_cis_statement'] else '  ---'} | "
              f"TY {entry['tax_year']}")

    print("\n" + "=" * 70)
    summary = cis.get_reconciliation_summary()
    for ty_key, ty_data in summary["tax_years"].items():
        if ty_data["invoice_count"] > 0:
            print(f"\nTax Year {ty_key}:")
            print(f"  Invoices:       {ty_data['invoice_count']}")
            print(f"  Total GROSS:    £{ty_data['total_gross']:>10,.2f}")
            print(f"  Total CITB:     £{ty_data['total_citb']:>10,.2f}")
            print(f"  Total CIS:      £{ty_data['total_cis_deducted']:>10,.2f}")
            print(f"  Total NET:      £{ty_data['total_net_received']:>10,.2f}")
            print(f"  CIS Tax Credit: £{ty_data['cis_tax_credit']:>10,.2f}")

    if summary["known_gaps"]:
        print(f"\n⚠ KNOWN GAPS:")
        for gap in summary["known_gaps"]:
            print(f"  - {gap['period']}: {gap['status']}")
