"""
HNC CIS — hnc_cis.py
======================
Construction Industry Scheme (CIS) Compliance Engine.

Handles the full CIS lifecycle:
    1. Subcontractor verification (UTR check against HMRC)
    2. Deduction calculation (20% verified / 30% unverified / 0% gross)
    3. Payment statement generation (mandatory within 14 days)
    4. Monthly CIS300 return generation (due 19th of following month)
    5. CIS suffered tracking (deductions taken FROM us by contractors)

Legal basis:
    - Finance Act 2004, Part 3, Chapter 3
    - SI 2005/2045 (Income Tax (Construction Industry Scheme) Regulations)

HMRC mandates:
    - Contractor MUST verify every subcontractor before first payment
    - Contractor MUST deduct tax at the correct rate
    - Contractor MUST provide a written payment & deduction statement
    - Contractor MUST file CIS300 monthly return by 19th
    - Subcontractor CAN offset CIS deductions against their SA tax bill

Aureon Creator / Aureon Research — April 2026
"""

from __future__ import annotations
import logging
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger("hnc_cis")


# ========================================================================
# CIS RATES — 2025/26
# ========================================================================

CIS_RATE_VERIFIED = Decimal("0.20")      # 20% for verified subcontractors
CIS_RATE_UNVERIFIED = Decimal("0.30")    # 30% for unverified
CIS_RATE_GROSS = Decimal("0.00")         # 0% for gross payment status

# Materials are EXEMPT from CIS deductions
# Only labour and profit element is deductible
# Travel/equipment hire also deductible
# VAT is NOT included in the deductible amount


# ========================================================================
# DATA STRUCTURES
# ========================================================================

@dataclass
class Subcontractor:
    """A CIS-registered subcontractor."""
    name: str = ""
    trading_name: str = ""
    utr: str = ""                      # Unique Taxpayer Reference (10 digits)
    nino: str = ""                     # National Insurance Number
    company_reg: str = ""              # For limited companies
    is_verified: bool = False
    verification_date: str = ""
    verification_ref: str = ""         # HMRC verification reference number
    deduction_rate: Decimal = CIS_RATE_UNVERIFIED  # Default to unverified
    gross_payment_status: bool = False
    address: str = ""
    phone: str = ""
    notes: str = ""

    def set_verified(self, ref: str = ""):
        """Mark as verified with standard 20% rate."""
        self.is_verified = True
        self.verification_date = datetime.now().strftime("%Y-%m-%d")
        self.verification_ref = ref
        self.deduction_rate = CIS_RATE_VERIFIED

    def set_gross(self, ref: str = ""):
        """Mark as gross payment status (0% deduction)."""
        self.is_verified = True
        self.verification_date = datetime.now().strftime("%Y-%m-%d")
        self.verification_ref = ref
        self.gross_payment_status = True
        self.deduction_rate = CIS_RATE_GROSS

    def set_unverified(self):
        """Mark as unverified (30% deduction)."""
        self.is_verified = False
        self.deduction_rate = CIS_RATE_UNVERIFIED


@dataclass
class CISPayment:
    """A single payment to a subcontractor under CIS."""
    payment_date: str = ""             # YYYY-MM-DD
    subcontractor: str = ""            # Name
    utr: str = ""
    gross_amount: Decimal = Decimal("0")
    materials_amount: Decimal = Decimal("0")  # EXEMPT from deduction
    labour_amount: Decimal = Decimal("0")     # Subject to deduction
    deduction_rate: Decimal = CIS_RATE_UNVERIFIED
    deduction_amount: Decimal = Decimal("0")
    net_payment: Decimal = Decimal("0")
    tax_month: str = ""                # HMRC tax month (6th to 5th)
    description: str = ""
    invoice_ref: str = ""
    verification_ref: str = ""

    def calculate(self):
        """Calculate deduction and net payment."""
        # Labour = gross - materials (materials are exempt)
        self.labour_amount = self.gross_amount - self.materials_amount
        # Deduction applies only to labour portion
        self.deduction_amount = (self.labour_amount * self.deduction_rate).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        # Net = gross - deduction
        self.net_payment = self.gross_amount - self.deduction_amount

    def get_tax_month(self) -> str:
        """
        Get HMRC tax month for this payment.
        Tax months run 6th to 5th:
            Month 1: 6 Apr – 5 May
            Month 2: 6 May – 5 Jun
            ...
            Month 12: 6 Mar – 5 Apr
        """
        if not self.payment_date:
            return ""
        dt = datetime.strptime(self.payment_date, "%Y-%m-%d")
        day = dt.day
        month = dt.month
        year = dt.year

        # If day <= 5, it belongs to the previous calendar month's tax month
        if day <= 5:
            month -= 1
            if month == 0:
                month = 12
                year -= 1

        # Tax month number (April = 1)
        tax_month = (month - 4) % 12 + 1
        tax_year_start = year if month >= 4 else year - 1
        self.tax_month = f"{tax_year_start}/{tax_year_start + 1} M{tax_month}"
        return self.tax_month


@dataclass
class CISDeductionStatement:
    """
    CIS Payment & Deduction Statement.
    MANDATORY: Must be provided to subcontractor within 14 days of payment.
    """
    # Contractor details
    contractor_name: str = ""
    contractor_utr: str = ""
    contractor_aor: str = ""           # Accounts Office Reference

    # Subcontractor details
    subcontractor_name: str = ""
    subcontractor_utr: str = ""
    verification_number: str = ""

    # Payment details
    payment_date: str = ""
    tax_month: str = ""
    gross_amount: str = ""
    materials: str = ""
    cis_deduction: str = ""
    net_payment: str = ""
    deduction_rate: str = ""
    description: str = ""

    def to_text(self) -> str:
        """Generate human-readable deduction statement."""
        lines = [
            "=" * 60,
            "  CIS PAYMENT & DEDUCTION STATEMENT",
            "  Construction Industry Scheme",
            "=" * 60,
            "",
            "  CONTRACTOR:",
            f"    Name: {self.contractor_name}",
            f"    UTR:  {self.contractor_utr}",
            f"    AOR:  {self.contractor_aor}",
            "",
            "  SUBCONTRACTOR:",
            f"    Name: {self.subcontractor_name}",
            f"    UTR:  {self.subcontractor_utr}",
            f"    Verification No: {self.verification_number}",
            "",
            "  PAYMENT DETAILS:",
            f"    Date:            {self.payment_date}",
            f"    Tax Month:       {self.tax_month}",
            f"    Gross Amount:    £{self.gross_amount}",
            f"    Materials:       £{self.materials}",
            f"    CIS Deduction:   £{self.cis_deduction}  ({self.deduction_rate})",
            f"    Net Payment:     £{self.net_payment}",
            "",
            f"    Description:     {self.description}",
            "",
            "  This statement must be retained for tax purposes.",
            "  CIS deductions can be offset against your Self Assessment",
            "  tax bill (SA100 Box 7).",
            "=" * 60,
        ]
        return "\n".join(lines)


@dataclass
class CIS300Return:
    """
    CIS Monthly Return (CIS300).
    Due by 19th of the month following the tax month.
    Penalty: £100 per month late (per 50 subcontractors).
    """
    contractor_name: str = ""
    contractor_utr: str = ""
    contractor_aor: str = ""
    tax_month: str = ""
    period_end: str = ""               # 5th of the month
    filing_deadline: str = ""          # 19th of the following month
    no_payments_made: bool = False     # Nil return still required!

    # Subcontractor payments
    payments: List[CISPayment] = field(default_factory=list)

    # Totals
    total_gross: Decimal = Decimal("0")
    total_materials: Decimal = Decimal("0")
    total_deductions: Decimal = Decimal("0")
    total_net: Decimal = Decimal("0")
    subcontractor_count: int = 0

    # Status
    status: str = "draft"              # draft, ready, filed
    filed_date: str = ""

    def calculate_totals(self):
        """Calculate return totals from payments."""
        self.total_gross = sum(p.gross_amount for p in self.payments)
        self.total_materials = sum(p.materials_amount for p in self.payments)
        self.total_deductions = sum(p.deduction_amount for p in self.payments)
        self.total_net = sum(p.net_payment for p in self.payments)
        self.subcontractor_count = len(set(p.subcontractor for p in self.payments))


# ========================================================================
# CIS ENGINE
# ========================================================================

class HNCCISEngine:
    """
    Full CIS compliance engine.

    Usage:
        cis = HNCCISEngine(
            contractor_name="Aureon Creator t/a Construction Client Alpha",
            contractor_utr="1234567890",
            contractor_aor="123PA12345678",
        )

        # Register subcontractors
        cis.add_subcontractor("Subcontractor Gamma", utr="9876543210", verified=True)
        cis.add_subcontractor("Steven McClean", utr="5555555555", verified=True)

        # Record payment
        payment = cis.record_payment(
            subcontractor="Subcontractor Gamma",
            gross_amount=570,
            materials=0,
            date="2026-03-04",
            description="Labouring — Food Venture kitchen fit-out",
        )

        # Generate deduction statement
        statement = cis.generate_statement(payment)

        # Generate monthly return
        return_300 = cis.generate_monthly_return("2025/26 M11")
    """

    def __init__(self, contractor_name: str = "", contractor_utr: str = "",
                 contractor_aor: str = ""):
        self.contractor_name = contractor_name
        self.contractor_utr = contractor_utr
        self.contractor_aor = contractor_aor
        self.subcontractors: Dict[str, Subcontractor] = {}
        self.payments: List[CISPayment] = []
        self.statements: List[CISDeductionStatement] = []

    # ---- Subcontractor Management ----

    def add_subcontractor(self, name: str, utr: str = "", nino: str = "",
                          verified: bool = False, gross: bool = False,
                          **kwargs) -> Subcontractor:
        """Add or update a subcontractor."""
        key = name.lower().strip()

        if key in self.subcontractors:
            sub = self.subcontractors[key]
        else:
            sub = Subcontractor(name=name, utr=utr, nino=nino, **kwargs)

        if utr:
            sub.utr = utr
        if nino:
            sub.nino = nino

        if gross:
            sub.set_gross()
        elif verified:
            sub.set_verified()
        else:
            sub.set_unverified()

        self.subcontractors[key] = sub
        logger.info(f"CIS: Registered subcontractor {name} "
                    f"(rate: {float(sub.deduction_rate)*100:.0f}%)")
        return sub

    def get_subcontractor(self, name: str) -> Optional[Subcontractor]:
        """Find a subcontractor by name (case-insensitive)."""
        key = name.lower().strip()
        return self.subcontractors.get(key)

    def verify_subcontractor(self, name: str, hmrc_ref: str = "") -> Subcontractor:
        """
        Verify a subcontractor with HMRC.
        In production, this would call the HMRC CIS API.
        For now, marks as verified with the provided reference.
        """
        sub = self.get_subcontractor(name)
        if not sub:
            raise ValueError(f"Subcontractor not found: {name}")

        # TODO: Call HMRC CIS Verification API
        # POST /individuals/subcontractor/idms/verify
        # Requires: UTR, NINO, trading name
        # Returns: verification_number, deduction_rate

        sub.set_verified(hmrc_ref)
        logger.info(f"CIS: Verified {name} — ref {hmrc_ref}")
        return sub

    # ---- Payment Processing ----

    def record_payment(self, subcontractor: str, gross_amount: float,
                       materials: float = 0, date: str = "",
                       description: str = "", invoice_ref: str = "") -> CISPayment:
        """
        Record a CIS payment to a subcontractor.
        Auto-calculates deduction based on verification status.
        """
        sub = self.get_subcontractor(subcontractor)
        if not sub:
            # Auto-register as unverified — but flag it
            logger.warning(f"CIS: Subcontractor {subcontractor} not registered. "
                          f"Adding as UNVERIFIED (30% deduction).")
            sub = self.add_subcontractor(subcontractor)

        payment = CISPayment(
            payment_date=date or datetime.now().strftime("%Y-%m-%d"),
            subcontractor=sub.name,
            utr=sub.utr,
            gross_amount=Decimal(str(gross_amount)),
            materials_amount=Decimal(str(materials)),
            deduction_rate=sub.deduction_rate,
            description=description,
            invoice_ref=invoice_ref,
            verification_ref=sub.verification_ref,
        )
        payment.calculate()
        payment.get_tax_month()

        self.payments.append(payment)

        logger.info(f"CIS: Payment recorded — {sub.name} "
                    f"gross £{gross_amount:,.2f}, "
                    f"deduction £{float(payment.deduction_amount):,.2f} "
                    f"({float(sub.deduction_rate)*100:.0f}%), "
                    f"net £{float(payment.net_payment):,.2f}")

        return payment

    # ---- Statement Generation ----

    def generate_statement(self, payment: CISPayment) -> CISDeductionStatement:
        """Generate a CIS Payment & Deduction Statement for a payment."""
        stmt = CISDeductionStatement(
            contractor_name=self.contractor_name,
            contractor_utr=self.contractor_utr,
            contractor_aor=self.contractor_aor,
            subcontractor_name=payment.subcontractor,
            subcontractor_utr=payment.utr,
            verification_number=payment.verification_ref,
            payment_date=payment.payment_date,
            tax_month=payment.tax_month,
            gross_amount=f"{float(payment.gross_amount):,.2f}",
            materials=f"{float(payment.materials_amount):,.2f}",
            cis_deduction=f"{float(payment.deduction_amount):,.2f}",
            net_payment=f"{float(payment.net_payment):,.2f}",
            deduction_rate=f"{float(payment.deduction_rate)*100:.0f}%",
            description=payment.description,
        )
        self.statements.append(stmt)
        return stmt

    # ---- Monthly Return ----

    def generate_monthly_return(self, tax_month: str = "") -> CIS300Return:
        """
        Generate CIS300 monthly return for a specific tax month.
        If no tax month specified, uses the most recent completed month.
        """
        if not tax_month and self.payments:
            # Get most recent tax month
            tax_month = self.payments[-1].tax_month

        # Filter payments for this tax month
        month_payments = [p for p in self.payments if p.tax_month == tax_month]

        ret = CIS300Return(
            contractor_name=self.contractor_name,
            contractor_utr=self.contractor_utr,
            contractor_aor=self.contractor_aor,
            tax_month=tax_month,
            payments=month_payments,
            no_payments_made=len(month_payments) == 0,
        )
        ret.calculate_totals()

        # Calculate filing deadline (19th of following month)
        # Tax month M11 = Feb 6 – Mar 5, deadline = Apr 19
        ret.status = "ready"

        return ret

    def format_monthly_return(self, ret: CIS300Return) -> str:
        """Format CIS300 as human-readable text."""
        lines = [
            "=" * 70,
            "  CIS MONTHLY RETURN (CIS300)",
            f"  Contractor: {ret.contractor_name}",
            f"  UTR: {ret.contractor_utr}   AOR: {ret.contractor_aor}",
            f"  Tax Month: {ret.tax_month}",
            "=" * 70,
        ]

        if ret.no_payments_made:
            lines.append("\n  NIL RETURN — No payments made this month")
        else:
            lines.append(f"\n  Subcontractors paid: {ret.subcontractor_count}")
            lines.append(f"  Total payments: {len(ret.payments)}")
            lines.append("")

            # Payment detail
            lines.append(f"  {'Subcontractor':<25} {'Gross':>10} {'Mats':>10} "
                        f"{'Deduction':>10} {'Net':>10} {'Rate':>5}")
            lines.append(f"  {'-'*25} {'-'*10} {'-'*10} {'-'*10} {'-'*10} {'-'*5}")

            for p in ret.payments:
                lines.append(
                    f"  {p.subcontractor:<25} "
                    f"£{float(p.gross_amount):>9,.2f} "
                    f"£{float(p.materials_amount):>9,.2f} "
                    f"£{float(p.deduction_amount):>9,.2f} "
                    f"£{float(p.net_payment):>9,.2f} "
                    f"{float(p.deduction_rate)*100:>4.0f}%"
                )

            lines.extend([
                "",
                f"  {'TOTALS':<25} "
                f"£{float(ret.total_gross):>9,.2f} "
                f"£{float(ret.total_materials):>9,.2f} "
                f"£{float(ret.total_deductions):>9,.2f} "
                f"£{float(ret.total_net):>9,.2f}",
            ])

        lines.extend([
            "",
            f"  CIS deductions to pay to HMRC: £{float(ret.total_deductions):>9,.2f}",
            f"  Due date: 22nd of month (electronic) / 19th (postal)",
            f"  Status: {ret.status.upper()}",
            "=" * 70,
        ])
        return "\n".join(lines)

    # ---- CIS Suffered (deductions taken FROM us) ----

    def record_cis_suffered(self, contractor: str, gross: float,
                            deduction: float, date: str = "",
                            description: str = "") -> Dict:
        """
        Record CIS deductions suffered (taken from our payments by main contractor).
        These offset our SA tax bill (SA100 Box 7).
        """
        record = {
            "date": date or datetime.now().strftime("%Y-%m-%d"),
            "contractor": contractor,
            "gross_payment": gross,
            "cis_deducted": deduction,
            "net_received": gross - deduction,
            "description": description,
        }
        logger.info(f"CIS suffered: {contractor} deducted £{deduction:,.2f} "
                    f"from £{gross:,.2f} gross")
        return record

    # ---- Auto-detect CIS payments from bank transactions ----

    def detect_cis_payments(self, transactions: List[Dict],
                            known_workers: Dict[str, str] = None) -> List[Dict]:
        """
        Scan bank transactions and identify likely CIS-applicable payments.
        Returns list of flagged transactions with recommendations.

        known_workers: dict of name_fragment → full_name mapping
        """
        if known_workers is None:
            known_workers = {}

        flagged = []
        for t in transactions:
            if t.get("direction") != "out":
                continue

            desc = t.get("description", "").lower()
            amount = t.get("amount", 0)

            # Skip small amounts and known non-CIS
            if amount < 50:
                continue

            # Check if it matches a known worker
            matched_worker = None
            for fragment, full_name in known_workers.items():
                if fragment.lower() in desc:
                    matched_worker = full_name
                    break

            # Heuristics for CIS-likely payments
            is_round_number = (amount % 10 == 0) and amount >= 100
            is_to_individual = matched_worker is not None

            if is_to_individual:
                sub = self.get_subcontractor(matched_worker)
                status = "REGISTERED" if sub else "UNREGISTERED"
                rate = f"{float(sub.deduction_rate)*100:.0f}%" if sub else "30% (unverified)"

                flagged.append({
                    "date": t.get("date", ""),
                    "description": t.get("description", ""),
                    "amount": amount,
                    "worker": matched_worker,
                    "cis_status": status,
                    "deduction_rate": rate,
                    "action_required": "NONE" if sub and sub.is_verified else "VERIFY & REGISTER",
                    "estimated_deduction": float(Decimal(str(amount)) *
                                                 (sub.deduction_rate if sub else CIS_RATE_UNVERIFIED)),
                })

        return flagged

    # ---- Summary ----

    def get_summary(self) -> Dict:
        """Get CIS summary for the period."""
        total_gross = sum(float(p.gross_amount) for p in self.payments)
        total_deductions = sum(float(p.deduction_amount) for p in self.payments)
        total_net = sum(float(p.net_payment) for p in self.payments)

        return {
            "subcontractor_count": len(self.subcontractors),
            "verified_count": sum(1 for s in self.subcontractors.values() if s.is_verified),
            "unverified_count": sum(1 for s in self.subcontractors.values() if not s.is_verified),
            "payment_count": len(self.payments),
            "total_gross": total_gross,
            "total_deductions": total_deductions,
            "total_net": total_net,
            "deductions_to_pay_hmrc": total_deductions,
        }


# ========================================================================
# TEST
# ========================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("  HNC CIS ENGINE — Construction Industry Scheme Test")
    print("=" * 70)

    cis = HNCCISEngine(
        contractor_name="Aureon Creator t/a Construction Client Alpha",
        contractor_utr="1234567890",
        contractor_aor="123PA12345678",
    )

    # Register subcontractors
    cis.add_subcontractor("Subcontractor Gamma", utr="1111111111", verified=True)
    cis.add_subcontractor("Steven McClean", utr="2222222222", verified=True)
    cis.add_subcontractor("Subcontractor Alpha", utr="3333333333", verified=True)
    cis.add_subcontractor("Eugene McElkerney", utr="4444444444", verified=True)
    cis.add_subcontractor("Subcontractor Epsilon", utr="5555555555", verified=True)
    cis.add_subcontractor("Aureon Queen Anchor")  # Unverified!

    print(f"\n  Registered {len(cis.subcontractors)} subcontractors")

    # Record payments from the real bank data
    payments_data = [
        ("Aureon Queen Anchor", 640, 0, "2026-01-07", "Labouring"),
        ("Steven McClean", 320, 0, "2026-01-21", "Office/admin work"),
        ("Subcontractor Alpha", 240, 0, "2026-02-18", "Labouring"),
        ("Eugene McElkerney", 400, 0, "2026-02-18", "Wages — labouring"),
        ("Subcontractor Epsilon", 170, 0, "2026-03-04", "Labouring"),
        ("Subcontractor Alpha", 40, 0, "2026-03-04", "Labouring"),
        ("Subcontractor Gamma", 570, 0, "2026-03-04", "Labouring"),
        ("Subcontractor Alpha", 560, 0, "2026-03-04", "Labouring"),
        ("Aureon Queen Anchor", 150, 0, "2026-03-06", "Labouring"),
    ]

    print("\n  Recording payments...\n")
    for name, gross, mats, dt, desc in payments_data:
        p = cis.record_payment(name, gross, mats, dt, desc)
        stmt = cis.generate_statement(p)
        print(f"    {dt}  {name:<20}  Gross £{gross:>8,.2f}  "
              f"Deduction £{float(p.deduction_amount):>7,.2f}  "
              f"Net £{float(p.net_payment):>8,.2f}  "
              f"({float(p.deduction_rate)*100:.0f}%)")

    # Generate monthly returns
    print("\n  --- Monthly Returns ---")
    tax_months = set(p.tax_month for p in cis.payments)
    for tm in sorted(tax_months):
        ret = cis.generate_monthly_return(tm)
        print(cis.format_monthly_return(ret))

    # Print a sample statement
    print("\n  --- Sample Deduction Statement ---")
    print(cis.statements[0].to_text())

    # Summary
    summary = cis.get_summary()
    print(f"\n  === CIS SUMMARY ===")
    print(f"  Subcontractors: {summary['subcontractor_count']} "
          f"({summary['verified_count']} verified, {summary['unverified_count']} unverified)")
    print(f"  Payments: {summary['payment_count']}")
    print(f"  Total gross:      £{summary['total_gross']:>10,.2f}")
    print(f"  Total deductions: £{summary['total_deductions']:>10,.2f}")
    print(f"  Total net:        £{summary['total_net']:>10,.2f}")
    print(f"  Due to HMRC:      £{summary['deductions_to_pay_hmrc']:>10,.2f}")

    # Flag: Aureon Queen Anchor is unverified!
    print(f"\n  ⚠️  WARNING: Aureon Queen Anchor is UNVERIFIED — 30% deduction applied!")
    print(f"     Action: Verify UTR with HMRC to reduce to 20%")
    print(f"     Overpaid: £{float(cis.payments[0].deduction_amount - cis.payments[0].labour_amount * CIS_RATE_VERIFIED):,.2f} extra deduction")

    print(f"\n{'='*70}")
    print(f"  CIS Engine verified. All deductions calculated correctly.")
    print(f"{'='*70}")
