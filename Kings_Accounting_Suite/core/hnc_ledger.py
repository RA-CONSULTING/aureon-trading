#!/usr/bin/env python3
"""
HNC ACCOUNTANT — UK Double-Entry Ledger
========================================
Built on the Kings Ledger foundation, expanded for full UK GAAP compliance.

FRS 102 Section 1A compliant Chart of Accounts.
Supports: Sole Trader, LTD Company, Partnership, LLP.
Tax year: April 6 → April 5 (configurable).

ACCOUNT STRUCTURE:
  1xxx  Assets (Debit-normal)
  2xxx  Liabilities (Credit-normal)
  3xxx  Equity (Credit-normal)
  4xxx  Revenue (Credit-normal)
  5xxx  Cost of Sales (Debit-normal)
  6xxx  Overheads (Debit-normal)
  7xxx  Administrative (Debit-normal)
  8xxx  Tax (Debit-normal)

Aureon Creator | April 2026
"Every penny accounted for."
"""

import json
import time
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict
from pathlib import Path
from enum import Enum
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# ENTITY TYPES
# ═══════════════════════════════════════════════════════════════════════════

class EntityType(Enum):
    SOLE_TRADER = "sole_trader"       # SA100 + SA108
    LTD_COMPANY = "ltd_company"       # CT600
    PARTNERSHIP = "partnership"       # SA800
    LLP = "llp"                       # SA800 + CT600


# ═══════════════════════════════════════════════════════════════════════════
# UK CHART OF ACCOUNTS (FRS 102)
# ═══════════════════════════════════════════════════════════════════════════

class UKAccount(Enum):
    """Full UK GAAP Chart of Accounts."""

    # ─── ASSETS (1xxx) ───
    CASH_BANK = "1000"
    CURRENT_ACCOUNT = "1010"
    SAVINGS_ACCOUNT = "1020"
    PETTY_CASH = "1030"
    TRADE_DEBTORS = "1100"
    STOCK_INVENTORY = "1200"
    PREPAYMENTS = "1300"
    FIXED_TANGIBLE = "1400"
    PLANT_MACHINERY = "1410"
    MOTOR_VEHICLES = "1420"
    OFFICE_EQUIPMENT = "1430"
    COMPUTER_EQUIPMENT = "1440"
    FIXTURES_FITTINGS = "1450"
    FIXED_INTANGIBLE = "1500"
    INVESTMENTS = "1600"
    CRYPTO_HOLDINGS = "1610"
    VAT_INPUT = "1700"
    DEPRECIATION_ACCUMULATED = "1800"

    # ─── LIABILITIES (2xxx) ───
    TRADE_CREDITORS = "2000"
    VAT_OUTPUT = "2100"
    PAYE_NI_PAYABLE = "2200"
    CORPORATION_TAX_PAYABLE = "2300"
    LOANS_OVERDRAFTS = "2400"
    DIRECTORS_LOAN = "2500"
    ACCRUALS = "2600"
    DEFERRED_INCOME = "2700"

    # ─── EQUITY (3xxx) ───
    SHARE_CAPITAL = "3000"
    RETAINED_EARNINGS = "3100"
    DIVIDENDS_PAID = "3200"
    DRAWINGS = "3300"
    CURRENT_YEAR_PNL = "3400"

    # ─── REVENUE (4xxx) ───
    SALES_TURNOVER = "4000"
    TRADING_GAINS = "4100"
    INTEREST_INCOME = "4200"
    RENTAL_INCOME = "4300"
    OTHER_INCOME = "4400"
    STAKING_YIELD = "4500"

    # ─── COST OF SALES (5xxx) ───
    PURCHASES = "5000"
    TRADING_LOSSES = "5100"
    DIRECT_LABOUR = "5200"
    SUBCONTRACTOR_COSTS = "5300"

    # ─── OVERHEADS (6xxx) ───
    RENT_RATES = "6000"
    LIGHT_HEAT_POWER = "6100"
    TELEPHONE_INTERNET = "6200"
    POSTAGE_STATIONERY = "6300"
    MOTOR_EXPENSES = "6400"
    TRAVEL_SUBSISTENCE = "6500"
    ADVERTISING_MARKETING = "6600"
    INSURANCE = "6700"
    PROFESSIONAL_FEES = "6800"
    BANK_CHARGES = "6900"
    EXCHANGE_FEES = "6910"
    WITHDRAWAL_FEES = "6920"

    # ─── ADMINISTRATIVE (7xxx) ───
    WAGES_SALARIES = "7000"
    EMPLOYER_NI = "7100"
    PENSION_CONTRIBUTIONS = "7200"
    STAFF_TRAINING = "7300"
    DEPRECIATION = "7400"
    BAD_DEBTS = "7500"
    REPAIRS_MAINTENANCE = "7600"
    SUBSCRIPTIONS = "7700"
    SUNDRY_EXPENSES = "7800"

    # ─── TAX (8xxx) ───
    CORPORATION_TAX = "8000"
    CAPITAL_GAINS_TAX = "8100"
    INCOME_TAX = "8200"


# Which account categories increase with debit vs credit
DEBIT_NORMAL = {"1", "5", "6", "7", "8"}    # Assets, CoS, Overheads, Admin, Tax
CREDIT_NORMAL = {"2", "3", "4"}              # Liabilities, Equity, Revenue

# Human-readable account category names
ACCOUNT_CATEGORIES = {
    "1": "Assets",
    "2": "Liabilities",
    "3": "Equity",
    "4": "Revenue",
    "5": "Cost of Sales",
    "6": "Overheads",
    "7": "Administrative Expenses",
    "8": "Tax",
}

# VAT rates
class VATRate(Enum):
    STANDARD = Decimal("0.20")
    REDUCED = Decimal("0.05")
    ZERO = Decimal("0.00")
    EXEMPT = Decimal("-1")       # Exempt (no VAT at all)
    OUTSIDE_SCOPE = Decimal("-2")  # Not a VATable supply


# ═══════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class JournalLine:
    """A single line in a journal entry."""
    account_code: str
    account_name: str
    debit: float = 0.0
    credit: float = 0.0
    asset: str = ""
    entity: str = ""          # Supplier/customer name
    reference: str = ""       # Invoice number, receipt ref
    vat_rate: str = ""        # VATRate name if applicable
    vat_amount: float = 0.0   # VAT component
    memo: str = ""
    cost_centre: str = ""     # For departmental tracking


@dataclass
class JournalEntry:
    """A complete balanced journal entry."""
    id: str
    timestamp: float
    date: str
    description: str
    lines: List[JournalLine] = field(default_factory=list)
    reference: str = ""
    source: str = ""          # "manual", "bank_feed", "invoice", "auto"
    category: str = ""        # Expense/revenue category for reporting
    is_posted: bool = True
    tax_year: str = ""        # e.g. "2025/26"
    vat_period: str = ""      # e.g. "2026-Q1"

    @property
    def total_debits(self) -> float:
        return sum(line.debit for line in self.lines)

    @property
    def total_credits(self) -> float:
        return sum(line.credit for line in self.lines)

    @property
    def is_balanced(self) -> bool:
        return abs(self.total_debits - self.total_credits) < 0.005

    @property
    def hash(self) -> str:
        """Tamper-evident hash for audit trail."""
        content = f"{self.id}:{self.timestamp}:{self.total_debits}:{self.total_credits}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ═══════════════════════════════════════════════════════════════════════════
# TAX YEAR UTILITIES
# ═══════════════════════════════════════════════════════════════════════════

def get_uk_tax_year(dt: datetime = None) -> str:
    """Return UK tax year string e.g. '2025/26' for a given date."""
    if dt is None:
        dt = datetime.now()
    if dt.month < 4 or (dt.month == 4 and dt.day < 6):
        start_year = dt.year - 1
    else:
        start_year = dt.year
    return f"{start_year}/{str(start_year + 1)[-2:]}"


def get_tax_year_bounds(tax_year: str = None) -> Tuple[datetime, datetime]:
    """Return (start, end) datetimes for a UK tax year."""
    if tax_year is None:
        tax_year = get_uk_tax_year()
    start_year = int(tax_year.split("/")[0])
    start = datetime(start_year, 4, 6, 0, 0, 0)
    end = datetime(start_year + 1, 4, 5, 23, 59, 59)
    return start, end


def get_vat_quarter(dt: datetime = None) -> str:
    """Return VAT quarter string e.g. '2026-Q1'."""
    if dt is None:
        dt = datetime.now()
    quarter = (dt.month - 1) // 3 + 1
    return f"{dt.year}-Q{quarter}"


# ═══════════════════════════════════════════════════════════════════════════
# THE HNC LEDGER
# ═══════════════════════════════════════════════════════════════════════════

class HNCLedger:
    """
    UK-compliant double-entry ledger.

    Every transaction creates balanced journal entries (debits = credits).
    Full audit trail with tamper-evident hashing.
    Supports VAT tracking, multi-entity, and UK tax year boundaries.

    Usage:
        ledger = HNCLedger(entity_type=EntityType.LTD_COMPANY)

        # Record a sale with VAT
        ledger.record_sale_invoice("ACME Ltd", 1000.00, vat_rate=VATRate.STANDARD,
                                   invoice_ref="INV-001")

        # Record a purchase
        ledger.record_purchase("Office Supplies", 50.00, vat_rate=VATRate.STANDARD,
                               account=UKAccount.POSTAGE_STATIONERY)

        # Get trial balance
        print(ledger.trial_balance())
    """

    def __init__(self, entity_type: EntityType = EntityType.SOLE_TRADER,
                 data_dir: str = ".", company_name: str = ""):
        self.entity_type = entity_type
        self.company_name = company_name
        self.data_dir = Path(data_dir)
        self.journal: List[JournalEntry] = []
        self.account_balances: Dict[str, float] = defaultdict(float)
        self._entry_counter = 0
        self._load()

    def _next_id(self) -> str:
        self._entry_counter += 1
        return f"HNC-{int(time.time())}-{self._entry_counter:06d}"

    # ─────────────────────────────────────────────────────────
    # Core Posting
    # ─────────────────────────────────────────────────────────

    def _post_entry(self, entry: JournalEntry) -> bool:
        """Validate and post a journal entry. Returns True if posted."""
        if not entry.is_balanced:
            diff = abs(entry.total_debits - entry.total_credits)
            logger.error(
                f"UNBALANCED ENTRY {entry.id} (off by {diff:.4f}): "
                f"DR={entry.total_debits:.4f} CR={entry.total_credits:.4f} "
                f"'{entry.description}'"
            )
            for i, line in enumerate(entry.lines):
                logger.error(f"  L{i}: {line.account_name} DR={line.debit:.4f} CR={line.credit:.4f}")
            return False

        # Assign tax year and VAT period
        dt = datetime.fromtimestamp(entry.timestamp)
        if not entry.tax_year:
            entry.tax_year = get_uk_tax_year(dt)
        if not entry.vat_period:
            entry.vat_period = get_vat_quarter(dt)

        # Update account balances
        for line in entry.lines:
            code = line.account_code
            is_debit_normal = code[0] in DEBIT_NORMAL
            if is_debit_normal:
                self.account_balances[code] += line.debit - line.credit
            else:
                self.account_balances[code] += line.credit - line.debit

        self.journal.append(entry)
        self._append_audit(entry)
        return True

    def _append_audit(self, entry: JournalEntry):
        """Append to JSONL audit trail."""
        try:
            audit_path = self.data_dir / "hnc_audit.jsonl"
            record = {
                "id": entry.id,
                "hash": entry.hash,
                "ts": entry.timestamp,
                "date": entry.date,
                "desc": entry.description,
                "dr": entry.total_debits,
                "cr": entry.total_credits,
                "source": entry.source,
                "tax_year": entry.tax_year,
                "vat_period": entry.vat_period,
            }
            with open(audit_path, "a") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            logger.error(f"Audit write error: {e}")

    # ─────────────────────────────────────────────────────────
    # Transaction Recording — Sales
    # ─────────────────────────────────────────────────────────

    def record_sale_invoice(self, customer: str, net_amount: float,
                            vat_rate: VATRate = VATRate.STANDARD,
                            invoice_ref: str = "",
                            revenue_account: UKAccount = UKAccount.SALES_TURNOVER,
                            description: str = "",
                            timestamp: float = None) -> JournalEntry:
        """
        Record a sales invoice.
        DR  Trade Debtors         net + VAT (gross)
          CR  Sales/Revenue       net
          CR  VAT Output          VAT amount
        """
        ts = timestamp or time.time()
        dt = datetime.fromtimestamp(ts)

        vat_amount = 0.0
        if vat_rate not in (VATRate.EXEMPT, VATRate.OUTSIDE_SCOPE):
            vat_amount = round(net_amount * float(vat_rate.value), 2)
        gross = net_amount + vat_amount

        lines = [
            JournalLine(
                account_code=UKAccount.TRADE_DEBTORS.value,
                account_name="Trade Debtors",
                debit=gross,
                entity=customer,
                reference=invoice_ref,
            ),
            JournalLine(
                account_code=revenue_account.value,
                account_name=self._account_name(revenue_account.value),
                credit=net_amount,
                entity=customer,
                reference=invoice_ref,
            ),
        ]

        if vat_amount > 0:
            lines.append(JournalLine(
                account_code=UKAccount.VAT_OUTPUT.value,
                account_name="VAT Output",
                credit=vat_amount,
                vat_rate=vat_rate.name,
                vat_amount=vat_amount,
                reference=invoice_ref,
            ))

        desc = description or f"Sales invoice to {customer}"
        entry = JournalEntry(
            id=self._next_id(),
            timestamp=ts,
            date=dt.strftime("%Y-%m-%d %H:%M:%S"),
            description=desc,
            lines=lines,
            reference=invoice_ref,
            source="invoice",
            category="sales",
        )
        self._post_entry(entry)
        self._save()
        return entry

    def record_payment_received(self, customer: str, amount: float,
                                 invoice_ref: str = "",
                                 bank_account: UKAccount = UKAccount.CURRENT_ACCOUNT,
                                 timestamp: float = None) -> JournalEntry:
        """
        Record payment received from customer.
        DR  Bank                amount
          CR  Trade Debtors     amount
        """
        ts = timestamp or time.time()
        dt = datetime.fromtimestamp(ts)

        entry = JournalEntry(
            id=self._next_id(),
            timestamp=ts,
            date=dt.strftime("%Y-%m-%d %H:%M:%S"),
            description=f"Payment received from {customer}",
            lines=[
                JournalLine(
                    account_code=bank_account.value,
                    account_name=self._account_name(bank_account.value),
                    debit=amount,
                    entity=customer,
                    reference=invoice_ref,
                ),
                JournalLine(
                    account_code=UKAccount.TRADE_DEBTORS.value,
                    account_name="Trade Debtors",
                    credit=amount,
                    entity=customer,
                    reference=invoice_ref,
                ),
            ],
            reference=invoice_ref,
            source="bank_feed",
            category="payment_received",
        )
        self._post_entry(entry)
        self._save()
        return entry

    # ─────────────────────────────────────────────────────────
    # Transaction Recording — Purchases & Expenses
    # ─────────────────────────────────────────────────────────

    def record_purchase(self, supplier: str, net_amount: float,
                        vat_rate: VATRate = VATRate.STANDARD,
                        expense_account: UKAccount = UKAccount.PURCHASES,
                        invoice_ref: str = "",
                        description: str = "",
                        cost_centre: str = "",
                        timestamp: float = None) -> JournalEntry:
        """
        Record a purchase/expense with VAT.
        DR  Expense Account     net
        DR  VAT Input           VAT amount (reclaimable)
          CR  Trade Creditors   gross
        """
        ts = timestamp or time.time()
        dt = datetime.fromtimestamp(ts)

        vat_amount = 0.0
        if vat_rate not in (VATRate.EXEMPT, VATRate.OUTSIDE_SCOPE):
            vat_amount = round(net_amount * float(vat_rate.value), 2)
        gross = net_amount + vat_amount

        lines = [
            JournalLine(
                account_code=expense_account.value,
                account_name=self._account_name(expense_account.value),
                debit=net_amount,
                entity=supplier,
                reference=invoice_ref,
                cost_centre=cost_centre,
                memo=description,
            ),
            JournalLine(
                account_code=UKAccount.TRADE_CREDITORS.value,
                account_name="Trade Creditors",
                credit=gross,
                entity=supplier,
                reference=invoice_ref,
            ),
        ]

        if vat_amount > 0:
            lines.insert(1, JournalLine(
                account_code=UKAccount.VAT_INPUT.value,
                account_name="VAT Input (Reclaimable)",
                debit=vat_amount,
                vat_rate=vat_rate.name,
                vat_amount=vat_amount,
                reference=invoice_ref,
            ))

        desc = description or f"Purchase from {supplier}"
        entry = JournalEntry(
            id=self._next_id(),
            timestamp=ts,
            date=dt.strftime("%Y-%m-%d %H:%M:%S"),
            description=desc,
            lines=lines,
            reference=invoice_ref,
            source="invoice",
            category="purchase",
        )
        self._post_entry(entry)
        self._save()
        return entry

    def record_payment_made(self, supplier: str, amount: float,
                            invoice_ref: str = "",
                            bank_account: UKAccount = UKAccount.CURRENT_ACCOUNT,
                            timestamp: float = None) -> JournalEntry:
        """
        Record payment to supplier.
        DR  Trade Creditors     amount
          CR  Bank              amount
        """
        ts = timestamp or time.time()
        dt = datetime.fromtimestamp(ts)

        entry = JournalEntry(
            id=self._next_id(),
            timestamp=ts,
            date=dt.strftime("%Y-%m-%d %H:%M:%S"),
            description=f"Payment to {supplier}",
            lines=[
                JournalLine(
                    account_code=UKAccount.TRADE_CREDITORS.value,
                    account_name="Trade Creditors",
                    debit=amount,
                    entity=supplier,
                    reference=invoice_ref,
                ),
                JournalLine(
                    account_code=bank_account.value,
                    account_name=self._account_name(bank_account.value),
                    credit=amount,
                    entity=supplier,
                    reference=invoice_ref,
                ),
            ],
            reference=invoice_ref,
            source="bank_feed",
            category="payment_made",
        )
        self._post_entry(entry)
        self._save()
        return entry

    # ─────────────────────────────────────────────────────────
    # Transaction Recording — Crypto (Section 104 compatible)
    # ─────────────────────────────────────────────────────────

    def record_crypto_buy(self, exchange: str, asset: str, quantity: float,
                          price: float, fee: float = 0.0,
                          order_id: str = "",
                          timestamp: float = None) -> JournalEntry:
        """
        Record crypto acquisition.
        DR  Crypto Holdings     cost (quantity * price)
        DR  Exchange Fees       fee
          CR  Bank/Cash         total outflow
        """
        ts = timestamp or time.time()
        dt = datetime.fromtimestamp(ts)
        total_cost = quantity * price
        total_outflow = total_cost + fee

        lines = [
            JournalLine(
                account_code=UKAccount.CRYPTO_HOLDINGS.value,
                account_name="Crypto Holdings",
                debit=total_cost,
                asset=asset,
                entity=exchange,
                memo=f"Buy {quantity:.8f} {asset} @ {price:.2f}",
            ),
            JournalLine(
                account_code=UKAccount.CURRENT_ACCOUNT.value,
                account_name="Current Account",
                credit=total_outflow,
                entity=exchange,
            ),
        ]

        if fee > 0:
            lines.insert(1, JournalLine(
                account_code=UKAccount.EXCHANGE_FEES.value,
                account_name="Exchange Fees",
                debit=fee,
                entity=exchange,
                memo=f"Fee on buy {asset}",
            ))

        entry = JournalEntry(
            id=self._next_id(),
            timestamp=ts,
            date=dt.strftime("%Y-%m-%d %H:%M:%S"),
            description=f"Buy {quantity:.8f} {asset} @ {price:.2f} on {exchange}",
            lines=lines,
            reference=order_id,
            source="exchange",
            category="crypto_acquisition",
        )
        self._post_entry(entry)
        self._save()
        return entry

    def record_crypto_sell(self, exchange: str, asset: str, quantity: float,
                           price: float, cost_basis: float, fee: float = 0.0,
                           order_id: str = "",
                           timestamp: float = None) -> JournalEntry:
        """
        Record crypto disposal with realised gain/loss.
        Cost basis comes from Section 104 pool (calculated externally).
        DR  Bank/Cash           net proceeds
        DR  Exchange Fees       fee
          CR  Crypto Holdings   cost_basis
          CR  Trading Gains     gross_gain (or DR Trading Losses)
        """
        ts = timestamp or time.time()
        dt = datetime.fromtimestamp(ts)
        proceeds = quantity * price
        net_proceeds = proceeds - fee
        gross_pnl = proceeds - cost_basis

        lines = [
            JournalLine(
                account_code=UKAccount.CURRENT_ACCOUNT.value,
                account_name="Current Account",
                debit=net_proceeds,
                entity=exchange,
            ),
            JournalLine(
                account_code=UKAccount.CRYPTO_HOLDINGS.value,
                account_name="Crypto Holdings",
                credit=cost_basis,
                asset=asset,
                entity=exchange,
                memo=f"Sell {quantity:.8f} {asset} @ {price:.2f}",
            ),
        ]

        if fee > 0:
            lines.append(JournalLine(
                account_code=UKAccount.EXCHANGE_FEES.value,
                account_name="Exchange Fees",
                debit=fee,
                entity=exchange,
            ))

        if gross_pnl >= 0:
            lines.append(JournalLine(
                account_code=UKAccount.TRADING_GAINS.value,
                account_name="Trading Gains",
                credit=gross_pnl,
                asset=asset,
                memo=f"Realised gain on {asset}",
            ))
        else:
            lines.append(JournalLine(
                account_code=UKAccount.TRADING_LOSSES.value,
                account_name="Trading Losses",
                debit=abs(gross_pnl),
                asset=asset,
                memo=f"Realised loss on {asset}",
            ))

        entry = JournalEntry(
            id=self._next_id(),
            timestamp=ts,
            date=dt.strftime("%Y-%m-%d %H:%M:%S"),
            description=f"Sell {quantity:.8f} {asset} @ {price:.2f} (gain: {gross_pnl:+.2f})",
            lines=lines,
            reference=order_id,
            source="exchange",
            category="crypto_disposal",
        )
        self._post_entry(entry)
        self._save()
        return entry

    # ─────────────────────────────────────────────────────────
    # Transaction Recording — Payroll (Sole Trader / LTD)
    # ─────────────────────────────────────────────────────────

    def record_salary(self, employee: str, gross: float, paye: float,
                      employee_ni: float, employer_ni: float,
                      pension_employee: float = 0.0,
                      pension_employer: float = 0.0,
                      net_pay: float = None,
                      timestamp: float = None) -> JournalEntry:
        """
        Record a salary payment.
        DR  Wages & Salaries      gross
        DR  Employer NI           employer_ni
        DR  Pension (employer)    pension_employer
          CR  Bank                net_pay
          CR  PAYE/NI Payable     paye + employee_ni + employer_ni
          CR  Pension Payable     pension_employee + pension_employer
        """
        ts = timestamp or time.time()
        dt = datetime.fromtimestamp(ts)

        if net_pay is None:
            net_pay = gross - paye - employee_ni - pension_employee

        lines = [
            JournalLine(
                account_code=UKAccount.WAGES_SALARIES.value,
                account_name="Wages & Salaries",
                debit=gross,
                entity=employee,
            ),
            JournalLine(
                account_code=UKAccount.EMPLOYER_NI.value,
                account_name="Employer NI",
                debit=employer_ni,
                entity=employee,
            ),
            JournalLine(
                account_code=UKAccount.CURRENT_ACCOUNT.value,
                account_name="Current Account",
                credit=net_pay,
                entity=employee,
                memo="Net salary payment",
            ),
            JournalLine(
                account_code=UKAccount.PAYE_NI_PAYABLE.value,
                account_name="PAYE/NI Payable",
                credit=paye + employee_ni + employer_ni,
                memo="Due to HMRC",
            ),
        ]

        if pension_employee > 0 or pension_employer > 0:
            lines.insert(2, JournalLine(
                account_code=UKAccount.PENSION_CONTRIBUTIONS.value,
                account_name="Pension Contributions (Employer)",
                debit=pension_employer,
                entity=employee,
            ))
            lines.append(JournalLine(
                account_code=UKAccount.ACCRUALS.value,
                account_name="Pension Payable",
                credit=pension_employee + pension_employer,
                memo="Pension contributions due",
            ))

        entry = JournalEntry(
            id=self._next_id(),
            timestamp=ts,
            date=dt.strftime("%Y-%m-%d %H:%M:%S"),
            description=f"Salary: {employee} (gross {gross:.2f}, net {net_pay:.2f})",
            lines=lines,
            source="payroll",
            category="wages",
        )
        self._post_entry(entry)
        self._save()
        return entry

    # ─────────────────────────────────────────────────────────
    # Transaction Recording — Drawings / Dividends
    # ─────────────────────────────────────────────────────────

    def record_drawings(self, amount: float, description: str = "",
                        timestamp: float = None) -> JournalEntry:
        """Sole trader drawings. DR Drawings, CR Bank."""
        ts = timestamp or time.time()
        dt = datetime.fromtimestamp(ts)
        entry = JournalEntry(
            id=self._next_id(),
            timestamp=ts,
            date=dt.strftime("%Y-%m-%d %H:%M:%S"),
            description=description or f"Drawings {amount:.2f}",
            lines=[
                JournalLine(
                    account_code=UKAccount.DRAWINGS.value,
                    account_name="Drawings",
                    debit=amount,
                ),
                JournalLine(
                    account_code=UKAccount.CURRENT_ACCOUNT.value,
                    account_name="Current Account",
                    credit=amount,
                ),
            ],
            source="manual",
            category="drawings",
        )
        self._post_entry(entry)
        self._save()
        return entry

    def record_dividend(self, amount: float, shareholder: str = "",
                        timestamp: float = None) -> JournalEntry:
        """LTD company dividend. DR Dividends Paid, CR Bank."""
        ts = timestamp or time.time()
        dt = datetime.fromtimestamp(ts)
        entry = JournalEntry(
            id=self._next_id(),
            timestamp=ts,
            date=dt.strftime("%Y-%m-%d %H:%M:%S"),
            description=f"Dividend to {shareholder}: {amount:.2f}",
            lines=[
                JournalLine(
                    account_code=UKAccount.DIVIDENDS_PAID.value,
                    account_name="Dividends Paid",
                    debit=amount,
                    entity=shareholder,
                ),
                JournalLine(
                    account_code=UKAccount.CURRENT_ACCOUNT.value,
                    account_name="Current Account",
                    credit=amount,
                    entity=shareholder,
                ),
            ],
            source="manual",
            category="dividend",
        )
        self._post_entry(entry)
        self._save()
        return entry

    # ─────────────────────────────────────────────────────────
    # General Journal Entry
    # ─────────────────────────────────────────────────────────

    def record_journal(self, description: str,
                       lines: List[JournalLine],
                       reference: str = "",
                       source: str = "manual",
                       category: str = "",
                       timestamp: float = None) -> JournalEntry:
        """Record a general journal entry with arbitrary lines."""
        ts = timestamp or time.time()
        dt = datetime.fromtimestamp(ts)
        entry = JournalEntry(
            id=self._next_id(),
            timestamp=ts,
            date=dt.strftime("%Y-%m-%d %H:%M:%S"),
            description=description,
            lines=lines,
            reference=reference,
            source=source,
            category=category,
        )
        if self._post_entry(entry):
            self._save()
            return entry
        return None

    # ─────────────────────────────────────────────────────────
    # Financial Statements
    # ─────────────────────────────────────────────────────────

    def trial_balance(self) -> Dict[str, Any]:
        """Generate trial balance — total debits must equal total credits."""
        accounts = {}
        total_dr = 0.0
        total_cr = 0.0

        for code, balance in sorted(self.account_balances.items()):
            if abs(balance) < 0.005:
                continue
            is_debit_normal = code[0] in DEBIT_NORMAL
            if is_debit_normal:
                dr = balance if balance > 0 else 0.0
                cr = abs(balance) if balance < 0 else 0.0
            else:
                cr = balance if balance > 0 else 0.0
                dr = abs(balance) if balance < 0 else 0.0

            name = self._account_name(code)
            accounts[code] = {"name": name, "debit": dr, "credit": cr}
            total_dr += dr
            total_cr += cr

        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "entity": self.company_name,
            "entity_type": self.entity_type.value,
            "accounts": accounts,
            "total_debit": total_dr,
            "total_credit": total_cr,
            "is_balanced": abs(total_dr - total_cr) < 0.01,
            "difference": total_dr - total_cr,
        }

    def profit_and_loss(self, tax_year: str = None) -> Dict[str, Any]:
        """
        Generate UK-format P&L (Income Statement).
        Revenue - Cost of Sales = Gross Profit
        Gross Profit - Overheads - Admin = Net Profit Before Tax
        """
        entries = self.journal
        if tax_year:
            start, end = get_tax_year_bounds(tax_year)
            entries = [e for e in entries
                       if start.timestamp() <= e.timestamp <= end.timestamp()]

        revenue = defaultdict(float)
        cost_of_sales = defaultdict(float)
        overheads = defaultdict(float)
        admin = defaultdict(float)
        tax_charges = defaultdict(float)

        for entry in entries:
            for line in entry.lines:
                code = line.account_code
                name = self._account_name(code)
                net = line.credit - line.debit  # Revenue increases with credit

                if code.startswith("4"):
                    revenue[name] += net
                elif code.startswith("5"):
                    cost_of_sales[name] += line.debit - line.credit
                elif code.startswith("6"):
                    overheads[name] += line.debit - line.credit
                elif code.startswith("7"):
                    admin[name] += line.debit - line.credit
                elif code.startswith("8"):
                    tax_charges[name] += line.debit - line.credit

        total_revenue = sum(revenue.values())
        total_cos = sum(cost_of_sales.values())
        gross_profit = total_revenue - total_cos
        total_overheads = sum(overheads.values())
        total_admin = sum(admin.values())
        net_before_tax = gross_profit - total_overheads - total_admin
        total_tax = sum(tax_charges.values())
        net_after_tax = net_before_tax - total_tax

        return {
            "period": tax_year or get_uk_tax_year(),
            "entity": self.company_name,
            "revenue": dict(revenue),
            "total_revenue": total_revenue,
            "cost_of_sales": dict(cost_of_sales),
            "total_cost_of_sales": total_cos,
            "gross_profit": gross_profit,
            "overheads": dict(overheads),
            "total_overheads": total_overheads,
            "administrative": dict(admin),
            "total_administrative": total_admin,
            "net_profit_before_tax": net_before_tax,
            "tax": dict(tax_charges),
            "total_tax": total_tax,
            "net_profit_after_tax": net_after_tax,
        }

    def balance_sheet(self) -> Dict[str, Any]:
        """Generate UK-format balance sheet."""
        fixed_assets = {}
        current_assets = {}
        current_liabilities = {}
        long_term_liabilities = {}
        equity = {}

        for code, balance in self.account_balances.items():
            if abs(balance) < 0.005:
                continue
            name = self._account_name(code)

            if code.startswith("14") or code.startswith("15"):
                fixed_assets[name] = balance
            elif code.startswith("18"):
                fixed_assets[f"{name} (contra)"] = -balance
            elif code.startswith("1"):
                current_assets[name] = balance
            elif code.startswith("24") or code.startswith("25"):
                long_term_liabilities[name] = balance
            elif code.startswith("2"):
                current_liabilities[name] = balance
            elif code.startswith("3"):
                equity[name] = balance

        # Roll P&L into equity
        revenue = sum(v for k, v in self.account_balances.items() if k.startswith("4"))
        expenses = sum(v for k, v in self.account_balances.items()
                       if k[0] in ("5", "6", "7", "8"))
        net_income = revenue - expenses

        total_fixed = sum(fixed_assets.values())
        total_current_assets = sum(current_assets.values())
        total_assets = total_fixed + total_current_assets
        total_current_liab = sum(current_liabilities.values())
        total_long_liab = sum(long_term_liabilities.values())
        total_liabilities = total_current_liab + total_long_liab
        total_equity = sum(equity.values()) + net_income

        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "entity": self.company_name,
            "fixed_assets": fixed_assets,
            "total_fixed_assets": total_fixed,
            "current_assets": current_assets,
            "total_current_assets": total_current_assets,
            "total_assets": total_assets,
            "current_liabilities": current_liabilities,
            "total_current_liabilities": total_current_liab,
            "long_term_liabilities": long_term_liabilities,
            "total_long_term_liabilities": total_long_liab,
            "net_current_assets": total_current_assets - total_current_liab,
            "total_liabilities": total_liabilities,
            "equity": equity,
            "net_income_current_period": net_income,
            "total_equity": total_equity,
            "balanced": abs(total_assets - total_liabilities - total_equity) < 0.01,
        }

    def vat_return(self, period: str = None) -> Dict[str, Any]:
        """
        Generate MTD-format VAT return for a quarter.
        Returns the 9 VAT boxes required by HMRC.
        """
        if period is None:
            period = get_vat_quarter()

        entries = [e for e in self.journal if e.vat_period == period]

        box1 = 0.0  # VAT due on sales
        box4 = 0.0  # VAT reclaimed on purchases
        box6 = 0.0  # Total sales ex VAT
        box7 = 0.0  # Total purchases ex VAT

        for entry in entries:
            for line in entry.lines:
                if line.account_code == UKAccount.VAT_OUTPUT.value:
                    box1 += line.credit - line.debit
                elif line.account_code == UKAccount.VAT_INPUT.value:
                    box4 += line.debit - line.credit

                # Sales revenue (net of VAT)
                if line.account_code.startswith("4") and line.credit > 0:
                    box6 += line.credit

                # Purchases (net of VAT)
                if line.account_code[0] in ("5", "6", "7") and line.debit > 0:
                    if line.vat_rate != VATRate.OUTSIDE_SCOPE.name:
                        box7 += line.debit

        box2 = 0.0   # EU acquisitions (post-Brexit: rare)
        box3 = box1 + box2
        box5 = box3 - box4  # Net VAT to pay (or reclaim if negative)
        box8 = 0.0   # EU supplies
        box9 = 0.0   # EU acquisitions

        return {
            "period": period,
            "entity": self.company_name,
            "box1_vat_due_sales": round(box1, 2),
            "box2_vat_due_acquisitions": round(box2, 2),
            "box3_total_vat_due": round(box3, 2),
            "box4_vat_reclaimed": round(box4, 2),
            "box5_net_vat": round(box5, 2),
            "box6_total_sales_ex_vat": round(box6, 2),
            "box7_total_purchases_ex_vat": round(box7, 2),
            "box8_total_eu_supplies": round(box8, 2),
            "box9_total_eu_acquisitions": round(box9, 2),
            "status": "PAY" if box5 > 0 else "RECLAIM",
        }

    # ─────────────────────────────────────────────────────────
    # Report Generation
    # ─────────────────────────────────────────────────────────

    def print_trial_balance(self) -> str:
        """Human-readable trial balance."""
        tb = self.trial_balance()
        lines = [
            "=" * 70,
            f"  TRIAL BALANCE — {tb['entity'] or 'HNC Accountant'}",
            f"  Date: {tb['date']}  |  Entity: {tb['entity_type']}",
            "=" * 70,
            f"  {'Account':<35s} {'Debit':>15s} {'Credit':>15s}",
            "  " + "-" * 66,
        ]

        current_category = ""
        for code, acct in tb["accounts"].items():
            cat = ACCOUNT_CATEGORIES.get(code[0], "Other")
            if cat != current_category:
                current_category = cat
                lines.append(f"\n  [{cat}]")

            dr = f"{acct['debit']:,.2f}" if acct["debit"] > 0 else ""
            cr = f"{acct['credit']:,.2f}" if acct["credit"] > 0 else ""
            lines.append(f"  {acct['name']:<35s} {dr:>15s} {cr:>15s}")

        lines.extend([
            "  " + "-" * 66,
            f"  {'TOTALS':<35s} {tb['total_debit']:>15,.2f} {tb['total_credit']:>15,.2f}",
            "=" * 70,
            f"  Balanced: {'YES ✓' if tb['is_balanced'] else 'NO ✗ INVESTIGATE'}",
            "=" * 70,
        ])
        return "\n".join(lines)

    # ─────────────────────────────────────────────────────────
    # Utilities
    # ─────────────────────────────────────────────────────────

    def _account_name(self, code: str) -> str:
        """Get human-readable account name from code."""
        for ac in UKAccount:
            if ac.value == code:
                return ac.name.replace("_", " ").title()
        return f"Account {code}"

    def get_account_history(self, account_code: str,
                            limit: int = 100) -> List[Dict[str, Any]]:
        """Get transaction history for a specific account."""
        history = []
        for entry in reversed(self.journal):
            for line in entry.lines:
                if line.account_code == account_code:
                    history.append({
                        "date": entry.date,
                        "description": entry.description,
                        "debit": line.debit,
                        "credit": line.credit,
                        "entity": line.entity,
                        "reference": entry.reference,
                        "memo": line.memo,
                        "category": entry.category,
                    })
                    if len(history) >= limit:
                        return history
        return history

    def get_entity_balance(self, entity_name: str) -> Dict[str, float]:
        """Get outstanding balance for a supplier or customer."""
        balance = 0.0
        for entry in self.journal:
            for line in entry.lines:
                if line.entity == entity_name:
                    balance += line.debit - line.credit
        return {"entity": entity_name, "balance": balance}

    # ─────────────────────────────────────────────────────────
    # Persistence
    # ─────────────────────────────────────────────────────────

    def _save(self):
        """Save ledger to disk. No entry cap — all entries preserved."""
        try:
            data = {
                "saved_at": datetime.now().isoformat(),
                "entity_type": self.entity_type.value,
                "company_name": self.company_name,
                "entry_counter": self._entry_counter,
                "account_balances": dict(self.account_balances),
                "journal_entries": [
                    {
                        "id": e.id,
                        "timestamp": e.timestamp,
                        "date": e.date,
                        "description": e.description,
                        "reference": e.reference,
                        "source": e.source,
                        "category": e.category,
                        "tax_year": e.tax_year,
                        "vat_period": e.vat_period,
                        "lines": [
                            {
                                "account_code": l.account_code,
                                "account_name": l.account_name,
                                "debit": l.debit,
                                "credit": l.credit,
                                "asset": l.asset,
                                "entity": l.entity,
                                "reference": l.reference,
                                "vat_rate": l.vat_rate,
                                "vat_amount": l.vat_amount,
                                "memo": l.memo,
                                "cost_centre": l.cost_centre,
                            }
                            for l in e.lines
                        ],
                    }
                    for e in self.journal
                ],
            }
            ledger_path = self.data_dir / "hnc_ledger.json"
            ledger_path.write_text(json.dumps(data, indent=2, default=str))
        except Exception as e:
            logger.error(f"HNC Ledger save error: {e}")

    def _load(self):
        """Load ledger from disk."""
        ledger_path = self.data_dir / "hnc_ledger.json"
        if not ledger_path.exists():
            return

        try:
            data = json.loads(ledger_path.read_text())
            self._entry_counter = data.get("entry_counter", 0)
            self.account_balances = defaultdict(float, data.get("account_balances", {}))
            self.company_name = data.get("company_name", self.company_name)

            entity_str = data.get("entity_type", "sole_trader")
            for et in EntityType:
                if et.value == entity_str:
                    self.entity_type = et
                    break

            for je_data in data.get("journal_entries", []):
                lines = [
                    JournalLine(
                        account_code=l["account_code"],
                        account_name=l.get("account_name", ""),
                        debit=l.get("debit", 0.0),
                        credit=l.get("credit", 0.0),
                        asset=l.get("asset", ""),
                        entity=l.get("entity", ""),
                        reference=l.get("reference", ""),
                        vat_rate=l.get("vat_rate", ""),
                        vat_amount=l.get("vat_amount", 0.0),
                        memo=l.get("memo", ""),
                        cost_centre=l.get("cost_centre", ""),
                    )
                    for l in je_data.get("lines", [])
                ]
                entry = JournalEntry(
                    id=je_data["id"],
                    timestamp=je_data["timestamp"],
                    date=je_data["date"],
                    description=je_data["description"],
                    reference=je_data.get("reference", ""),
                    source=je_data.get("source", ""),
                    category=je_data.get("category", ""),
                    tax_year=je_data.get("tax_year", ""),
                    vat_period=je_data.get("vat_period", ""),
                    lines=lines,
                )
                self.journal.append(entry)

            logger.info(
                f"HNC Ledger loaded: {len(self.journal)} entries, "
                f"{len(self.account_balances)} accounts"
            )
        except Exception as e:
            logger.error(f"HNC Ledger load error: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════════════════

_hnc_ledger: Optional[HNCLedger] = None


def get_hnc_ledger(**kwargs) -> HNCLedger:
    """Get the singleton HNCLedger instance."""
    global _hnc_ledger
    if _hnc_ledger is None:
        _hnc_ledger = HNCLedger(**kwargs)
    return _hnc_ledger
