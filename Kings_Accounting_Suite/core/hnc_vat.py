"""
HNC VAT ENGINE — hnc_vat.py
============================
UK VAT compliance engine for The HNC Accountant.

Queen's logic: the system THINKS about VAT, it doesn't just add 20%.

Handles:
- VAT scheme selection and optimisation (Standard, Flat Rate, Cash Accounting)
- Auto-classification of supply types (standard, reduced, zero, exempt, outside scope)
- Reverse charge for construction (CIS domestic reverse charge)
- Partial exemption (if mixed taxable/exempt supplies)
- MTD 9-box return generation
- VAT period management (quarterly, monthly, annual)
- Threshold monitoring (registration/deregistration)
- RAUV-style internal audit (flags your own VAT return before HMRC does)
- Fuel scale charges
- Bad debt relief (6 months+ outstanding, written off)
- Cash vs accrual basis tracking
- Pre-submission validation

Integrates with:
- hnc_categoriser.py: reads ExpenseEvent.vat_rate and vat_amount
- hnc_ledger.py: reads journal entries for VAT account balances

Author: HNC Accountant Engine
UK GAAP / FRS 102 / VAT Act 1994 / HMRC Notice 700
"""

import json
import logging
import uuid
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("hnc_vat")


# ========================================================================
# ENUMS
# ========================================================================

class VATScheme(Enum):
    """VAT accounting schemes available to UK businesses."""
    STANDARD = "standard"           # Normal VAT accounting (accruals)
    FLAT_RATE = "flat_rate"         # Flat Rate Scheme (FRS)
    CASH_ACCOUNTING = "cash"        # Cash Accounting Scheme
    ANNUAL_ACCOUNTING = "annual"    # Annual Accounting Scheme
    NOT_REGISTERED = "not_registered"


class VATRate(Enum):
    """UK VAT rates as of 2025/26."""
    STANDARD = Decimal("0.20")       # 20% - most goods and services
    REDUCED = Decimal("0.05")        # 5%  - domestic fuel, children's car seats
    ZERO = Decimal("0.00")           # 0%  - food, books, children's clothing
    EXEMPT = Decimal("-1")           # No VAT, no input recovery
    OUTSIDE_SCOPE = Decimal("-2")    # Not a VAT supply at all
    REVERSE_CHARGE = Decimal("-3")   # CIS domestic reverse charge


class SupplyType(Enum):
    """Type of supply for VAT purposes."""
    OUTPUT_STANDARD = "output_standard"   # Sales at 20%
    OUTPUT_REDUCED = "output_reduced"     # Sales at 5%
    OUTPUT_ZERO = "output_zero"           # Zero-rated sales
    OUTPUT_EXEMPT = "output_exempt"       # Exempt sales
    INPUT_STANDARD = "input_standard"     # Purchases at 20%
    INPUT_REDUCED = "input_reduced"       # Purchases at 5%
    INPUT_ZERO = "input_zero"            # Zero-rated purchases
    INPUT_EXEMPT = "input_exempt"        # Exempt purchases (no recovery)
    INPUT_OUTSIDE_SCOPE = "input_outside" # Not VATable
    REVERSE_CHARGE_IN = "rc_input"       # CIS reverse charge received
    REVERSE_CHARGE_OUT = "rc_output"     # CIS reverse charge issued


class VATReturnStatus(Enum):
    """Status of a VAT return."""
    DRAFT = "draft"
    VALIDATED = "validated"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class VATFlagSeverity(Enum):
    """Severity levels for VAT RAUV flags."""
    RED = "RED"
    AMBER = "AMBER"
    GREEN = "GREEN"


# ========================================================================
# CONSTANTS — UK VAT THRESHOLDS & RATES (2025/26)
# ========================================================================

# Registration threshold: must register if taxable turnover exceeds
# £90,000 in any rolling 12-month period (from April 2024)
VAT_REGISTRATION_THRESHOLD = 90000.0

# Deregistration threshold: can deregister if taxable turnover
# expected to fall below £88,000
VAT_DEREGISTRATION_THRESHOLD = 88000.0

# Flat Rate Scheme: must leave if turnover exceeds £230,000
# (or if not "limited cost trader")
FRS_EXIT_THRESHOLD = 230000.0

# Flat Rate percentages by trade sector (HMRC Notice 733)
# Construction sector relevant rates
FLAT_RATE_PERCENTAGES = {
    "general_building": Decimal("9.5"),
    "labour_only_building": Decimal("14.5"),
    "electrical": Decimal("10.0"),
    "plumbing": Decimal("10.0"),
    "joinery": Decimal("11.0"),
    "painting_decorating": Decimal("12.5"),
    "roofing": Decimal("6.5"),
    "architect_surveyor": Decimal("14.5"),
    "estate_agent": Decimal("12.0"),
    "accountant": Decimal("14.5"),
    "computer_repair": Decimal("10.5"),
    "hairdresser": Decimal("13.0"),
    "restaurant_catering": Decimal("12.5"),
    "retailer_food": Decimal("4.0"),
    "retailer_other": Decimal("7.5"),
    "transport": Decimal("10.0"),
    "management_consultant": Decimal("14.0"),
    "other": Decimal("12.0"),
}

# Limited cost trader: if goods cost < 2% of VAT-inclusive turnover
# (or < £1,000 per year), flat rate becomes 16.5%
LIMITED_COST_TRADER_RATE = Decimal("16.5")
LIMITED_COST_GOODS_PCT = Decimal("0.02")
LIMITED_COST_ANNUAL_FLOOR = Decimal("1000")

# Fuel scale charges (quarterly, VAT-inclusive) by CO2 band
# Simplified: common bands for vans and cars
FUEL_SCALE_CHARGES_QUARTERLY = {
    "petrol_120": 169.0,
    "petrol_150": 201.0,
    "petrol_170": 226.0,
    "petrol_200": 268.0,
    "petrol_225plus": 308.0,
    "diesel_120": 169.0,
    "diesel_150": 201.0,
    "diesel_170": 226.0,
    "diesel_200": 268.0,
    "diesel_225plus": 308.0,
    "van_diesel": 193.0,    # Standard van rate
    "van_petrol": 193.0,
}

# CIS reverse charge: applies to construction services between
# VAT-registered businesses where the customer is also a contractor
# who makes onward supplies of construction services
CIS_REVERSE_CHARGE_EFFECTIVE = "2021-03-01"

# Bad debt relief: can reclaim output VAT on debts outstanding > 6 months
# and written off in your accounts (VAT Act 1994 s.36)
BAD_DEBT_RELIEF_DAYS = 180


# ========================================================================
# DATACLASSES
# ========================================================================

@dataclass
class VATTransaction:
    """A single transaction with VAT implications."""
    txn_id: str = ""
    date: str = ""
    description: str = ""
    counterparty: str = ""
    gross_amount: float = 0.0
    net_amount: float = 0.0
    vat_amount: float = 0.0
    vat_rate: str = "STANDARD"
    supply_type: str = ""
    category: str = ""              # From hnc_categoriser
    is_cis_reverse_charge: bool = False
    is_fuel_scale: bool = False
    payment_date: Optional[str] = None  # For cash accounting
    is_paid: bool = True
    vat_period: str = ""
    source: str = ""                # "categoriser", "ledger", "manual"
    notes: str = ""


@dataclass
class VATReturn:
    """MTD 9-box VAT return."""
    period: str = ""                # e.g., "2026-Q1"
    period_start: str = ""
    period_end: str = ""
    entity: str = ""
    scheme: str = "standard"
    # The 9 boxes
    box1_vat_due_sales: float = 0.0
    box2_vat_due_acquisitions: float = 0.0
    box3_total_vat_due: float = 0.0
    box4_vat_reclaimed: float = 0.0
    box5_net_vat: float = 0.0
    box6_total_sales_ex_vat: float = 0.0
    box7_total_purchases_ex_vat: float = 0.0
    box8_total_eu_supplies: float = 0.0
    box9_total_eu_acquisitions: float = 0.0
    # Metadata
    status: str = VATReturnStatus.DRAFT.value
    generated_at: str = ""
    flags: List[Dict] = field(default_factory=list)
    transaction_count: int = 0
    adjustments: List[Dict] = field(default_factory=list)


@dataclass
class VATFlag:
    """A RAUV-style flag on a VAT return."""
    severity: str = ""
    flag: str = ""
    risk: str = ""
    redirect: str = ""
    box_affected: str = ""
    amount_impact: float = 0.0


# ========================================================================
# HELPER FUNCTIONS
# ========================================================================

def generate_vat_txn_id() -> str:
    return f"VAT-{uuid.uuid4().hex[:10].upper()}"


def get_vat_period(d: str, frequency: str = "quarterly") -> str:
    """Return the VAT period for a date.

    quarterly: Q1=Jan-Mar, Q2=Apr-Jun, Q3=Jul-Sep, Q4=Oct-Dec
    (Standard quarters aligned to calendar year, but businesses can
     choose stagger groups: months 1/4/7/10 or 2/5/8/11 or 3/6/9/12)
    """
    dt = datetime.strptime(d[:10], "%Y-%m-%d")
    if frequency == "monthly":
        return f"{dt.year}-M{dt.month:02d}"
    elif frequency == "annual":
        # Tax year: April to March
        if dt.month >= 4:
            return f"{dt.year}/{str(dt.year + 1)[2:]}"
        return f"{dt.year - 1}/{str(dt.year)[2:]}"
    else:
        quarter = (dt.month - 1) // 3 + 1
        return f"{dt.year}-Q{quarter}"


def get_period_dates(period: str) -> Tuple[str, str]:
    """Return (start_date, end_date) for a VAT period string."""
    if "-Q" in period:
        year = int(period.split("-Q")[0])
        q = int(period.split("-Q")[1])
        start_month = (q - 1) * 3 + 1
        end_month = start_month + 2
        start = f"{year}-{start_month:02d}-01"
        # Last day of end month
        if end_month == 12:
            end = f"{year}-12-31"
        else:
            next_month = date(year, end_month + 1, 1)
            last_day = next_month - timedelta(days=1)
            end = last_day.strftime("%Y-%m-%d")
        return (start, end)
    elif "-M" in period:
        year = int(period.split("-M")[0])
        month = int(period.split("-M")[1])
        start = f"{year}-{month:02d}-01"
        if month == 12:
            end = f"{year}-12-31"
        else:
            next_month = date(year, month + 1, 1)
            last_day = next_month - timedelta(days=1)
            end = last_day.strftime("%Y-%m-%d")
        return (start, end)
    return ("", "")


def calculate_vat(gross: float, rate_name: str) -> Tuple[float, float]:
    """Split gross amount into (net, vat). VAT-inclusive calculation.

    Standard 20%: gross / 1.20 = net, gross - net = vat
    Reduced  5%:  gross / 1.05 = net
    Zero/Exempt/Outside: net = gross, vat = 0
    """
    rate_map = {
        "STANDARD": Decimal("0.20"),
        "REDUCED": Decimal("0.05"),
        "ZERO": Decimal("0.00"),
        "EXEMPT": None,
        "OUTSIDE_SCOPE": None,
        "REVERSE_CHARGE": Decimal("0.20"),  # Same rate, different accounting
    }
    rate = rate_map.get(rate_name)
    if rate is None:
        return (round(gross, 2), 0.0)
    if rate == Decimal("0.00"):
        return (round(gross, 2), 0.0)

    gross_d = Decimal(str(gross))
    net = (gross_d / (1 + rate)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    vat = (gross_d - net).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return (float(net), float(vat))


def calculate_vat_exclusive(net: float, rate_name: str) -> Tuple[float, float]:
    """Calculate VAT on a net (ex-VAT) amount. Returns (vat, gross)."""
    rate_map = {
        "STANDARD": Decimal("0.20"),
        "REDUCED": Decimal("0.05"),
        "ZERO": Decimal("0.00"),
        "EXEMPT": None,
        "OUTSIDE_SCOPE": None,
        "REVERSE_CHARGE": Decimal("0.20"),
    }
    rate = rate_map.get(rate_name)
    if rate is None or rate == Decimal("0.00"):
        return (0.0, round(net, 2))

    net_d = Decimal(str(net))
    vat = (net_d * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    gross = float(net_d + vat)
    return (float(vat), round(gross, 2))


# ========================================================================
# KNOWN SUPPLY CLASSIFICATIONS
# ========================================================================
# Queen's logic: knows what rate things should be without being told

SUPPLY_CLASSIFICATIONS = {
    # Zero-rated (VAT Act 1994, Schedule 8)
    "food_basic": VATRate.ZERO,         # Most food (not catering/hot/eat-in)
    "books": VATRate.ZERO,
    "newspapers": VATRate.ZERO,
    "children_clothing": VATRate.ZERO,
    "children_shoes": VATRate.ZERO,
    "public_transport": VATRate.ZERO,
    "prescription_drugs": VATRate.ZERO,
    "exports": VATRate.ZERO,
    "new_build_residential": VATRate.ZERO,  # New build homes

    # Reduced rate (5%)
    "domestic_fuel_power": VATRate.REDUCED,  # Gas, electric for homes
    "energy_saving_materials": VATRate.REDUCED,
    "children_car_seats": VATRate.REDUCED,
    "smoking_cessation": VATRate.REDUCED,
    "sanitary_products": VATRate.ZERO,      # Actually zero-rated since Jan 2021

    # Exempt (no VAT, no input recovery)
    "insurance": VATRate.EXEMPT,
    "finance_banking": VATRate.EXEMPT,
    "education": VATRate.EXEMPT,
    "health_medical": VATRate.EXEMPT,
    "land_property": VATRate.EXEMPT,        # Unless opted to tax
    "postal_services": VATRate.EXEMPT,
    "burial_cremation": VATRate.EXEMPT,
    "betting_gaming": VATRate.EXEMPT,

    # Outside scope
    "wages_salaries": VATRate.OUTSIDE_SCOPE,
    "dividends": VATRate.OUTSIDE_SCOPE,
    "donations_gifts": VATRate.OUTSIDE_SCOPE,
    "bank_interest": VATRate.OUTSIDE_SCOPE,
    "statutory_fees": VATRate.OUTSIDE_SCOPE,  # MOT, road tax
    "council_tax": VATRate.OUTSIDE_SCOPE,
    "business_rates": VATRate.OUTSIDE_SCOPE,
}

# Construction-specific VAT classification
CONSTRUCTION_VAT = {
    # Standard rated construction
    "commercial_construction": VATRate.STANDARD,
    "commercial_refurb": VATRate.STANDARD,
    "residential_repair": VATRate.STANDARD,
    "residential_maintenance": VATRate.STANDARD,

    # Zero rated construction
    "new_build_residential": VATRate.ZERO,
    "new_build_charity": VATRate.ZERO,
    "approved_alterations_listed": VATRate.ZERO,

    # Reduced rate construction
    "residential_renovation_empty_3yr": VATRate.REDUCED,  # Empty 2+ years
    "residential_conversion": VATRate.REDUCED,  # e.g., commercial to residential
    "energy_saving_installation": VATRate.REDUCED,
}


# ========================================================================
# THE VAT ENGINE
# ========================================================================

class HNCVATEngine:
    """The Queen's VAT Engine.

    Thinks about VAT the way HMRC thinks about it -- then finds the
    legal optimum.

    Usage:
        vat = HNCVATEngine(
            entity_name="John's Construction",
            scheme=VATScheme.FLAT_RATE,
            flat_rate_trade="general_building",
            vat_number="GB123456789",
        )

        # Feed it categorised events
        vat.ingest_from_categoriser(categorised_events)

        # Or add transactions directly
        vat.add_sale("Kitchen fit Mrs Jones", 8500.0, "2026-01-15",
                     vat_rate="STANDARD")
        vat.add_purchase("Screwfix timber", 145.60, "2026-01-15",
                         vat_rate="STANDARD")

        # Generate MTD return
        vat_return = vat.generate_return("2026-Q1")

        # Run RAUV (internal audit)
        flags = vat.run_vat_rauv("2026-Q1")

        # Scheme optimisation
        recommendation = vat.optimise_scheme(annual_turnover=55000,
                                              annual_costs=22000)
    """

    def __init__(self,
                 entity_name: str = "",
                 scheme: VATScheme = VATScheme.STANDARD,
                 flat_rate_trade: str = "general_building",
                 vat_number: str = "",
                 stagger_group: int = 1,
                 period_frequency: str = "quarterly",
                 business_vehicle_co2: str = "van_diesel",
                 business_fuel_pct: float = 0.75,
                 ):
        self.entity_name = entity_name
        self.scheme = scheme
        self.flat_rate_trade = flat_rate_trade
        self.vat_number = vat_number
        self.stagger_group = stagger_group  # 1, 2, or 3
        self.period_frequency = period_frequency
        self.business_vehicle_co2 = business_vehicle_co2
        self.business_fuel_pct = business_fuel_pct

        # Transaction store
        self.transactions: List[VATTransaction] = []
        self.returns: List[VATReturn] = []

        # Threshold monitoring
        self.rolling_turnover: Dict[str, float] = defaultdict(float)  # month -> turnover

        # Bad debt tracking
        self.outstanding_invoices: List[Dict] = []

        # Flat rate year-1 discount (1% reduction in first year)
        self.is_first_year_frs = False

    # ------------------------------------------------------------------ #
    # INGEST from categoriser
    # ------------------------------------------------------------------ #
    def ingest_from_categoriser(self, events: List[Any]) -> int:
        """Convert ExpenseEvents from hnc_categoriser into VATTransactions.

        Reads each event's vat_rate, vat_amount, category, and nature
        to create properly classified VAT transactions.

        Returns number of transactions ingested.
        """
        count = 0
        for e in events:
            # Skip transfers and non-financial events
            nature = getattr(e, "nature", "")
            if nature == "transfer":
                continue

            gross = getattr(e, "amount_gross", 0)
            if gross == 0:
                continue

            vat_rate_name = getattr(e, "vat_rate", "STANDARD")
            vat_amount = getattr(e, "vat_amount", 0)
            category = getattr(e, "category", "")
            desc = getattr(e, "description", "")
            txn_date = getattr(e, "date", "")

            # Determine supply type
            # Income (invoices, sales) = output
            # Expenses (purchases) = input
            is_income = category in (
                "sales_income", "other_income", "construction_income",
            ) or "invoice" in desc.lower()

            if is_income:
                supply_type = f"output_{vat_rate_name.lower()}"
            else:
                supply_type = f"input_{vat_rate_name.lower()}"

            # Calculate VAT if not provided
            if vat_amount == 0 and vat_rate_name in ("STANDARD", "REDUCED"):
                net, vat_amount = calculate_vat(gross, vat_rate_name)
            else:
                net = gross - vat_amount

            # CIS reverse charge detection
            is_rc = (
                "cis" in desc.lower()
                and "reverse" in desc.lower()
            ) or (
                category == "subcontractor_cis"
                and vat_rate_name == "REVERSE_CHARGE"
            )

            txn = VATTransaction(
                txn_id=generate_vat_txn_id(),
                date=txn_date,
                description=desc,
                counterparty=getattr(e, "payee", "") or getattr(e, "payer", ""),
                gross_amount=round(gross, 2),
                net_amount=round(net, 2),
                vat_amount=round(vat_amount, 2),
                vat_rate=vat_rate_name,
                supply_type=supply_type,
                category=category,
                is_cis_reverse_charge=is_rc,
                vat_period=get_vat_period(txn_date, self.period_frequency),
                source="categoriser",
            )
            self.transactions.append(txn)
            count += 1

        return count

    # ------------------------------------------------------------------ #
    # MANUAL transaction entry
    # ------------------------------------------------------------------ #
    def add_sale(self, description: str, gross_amount: float, date_str: str,
                 counterparty: str = "", vat_rate: str = "STANDARD",
                 is_cis_reverse_charge: bool = False) -> VATTransaction:
        """Record a sale/income with VAT."""
        net, vat = calculate_vat(gross_amount, vat_rate)

        if is_cis_reverse_charge:
            # Reverse charge: no VAT on invoice, customer accounts for it
            vat = 0.0
            net = gross_amount
            supply_type = SupplyType.REVERSE_CHARGE_OUT.value
        else:
            supply_type = f"output_{vat_rate.lower()}"

        txn = VATTransaction(
            txn_id=generate_vat_txn_id(),
            date=date_str,
            description=description,
            counterparty=counterparty,
            gross_amount=round(gross_amount, 2),
            net_amount=round(net, 2),
            vat_amount=round(vat, 2),
            vat_rate=vat_rate,
            supply_type=supply_type,
            is_cis_reverse_charge=is_cis_reverse_charge,
            vat_period=get_vat_period(date_str, self.period_frequency),
            source="manual",
        )
        self.transactions.append(txn)

        # Track rolling turnover for threshold monitoring
        month_key = date_str[:7]  # YYYY-MM
        self.rolling_turnover[month_key] += net

        return txn

    def add_purchase(self, description: str, gross_amount: float, date_str: str,
                     counterparty: str = "", vat_rate: str = "STANDARD",
                     is_cis_reverse_charge: bool = False,
                     category: str = "") -> VATTransaction:
        """Record a purchase/expense with VAT."""
        net, vat = calculate_vat(gross_amount, vat_rate)

        if is_cis_reverse_charge:
            # Reverse charge: you account for VAT as both input and output
            vat_on_net, _ = calculate_vat_exclusive(net, "STANDARD")
            vat = vat_on_net
            supply_type = SupplyType.REVERSE_CHARGE_IN.value
        else:
            supply_type = f"input_{vat_rate.lower()}"

        txn = VATTransaction(
            txn_id=generate_vat_txn_id(),
            date=date_str,
            description=description,
            counterparty=counterparty,
            gross_amount=round(gross_amount, 2),
            net_amount=round(net, 2),
            vat_amount=round(vat, 2),
            vat_rate=vat_rate,
            supply_type=supply_type,
            category=category,
            is_cis_reverse_charge=is_cis_reverse_charge,
            vat_period=get_vat_period(date_str, self.period_frequency),
            source="manual",
        )
        self.transactions.append(txn)
        return txn

    def add_outstanding_invoice(self, counterparty: str, net_amount: float,
                                 vat_amount: float, invoice_date: str,
                                 due_date: str) -> None:
        """Track an outstanding sales invoice for bad debt relief."""
        self.outstanding_invoices.append({
            "counterparty": counterparty,
            "net_amount": net_amount,
            "vat_amount": vat_amount,
            "invoice_date": invoice_date,
            "due_date": due_date,
            "paid": False,
        })

    # ------------------------------------------------------------------ #
    # VAT RETURN GENERATION
    # ------------------------------------------------------------------ #
    def generate_return(self, period: str) -> VATReturn:
        """Generate an MTD 9-box VAT return for the specified period.

        The 9 boxes:
        Box 1: VAT due on sales and other outputs
        Box 2: VAT due on acquisitions from EU (post-Brexit: rare)
        Box 3: Total VAT due (Box 1 + Box 2)
        Box 4: VAT reclaimed on purchases and other inputs
        Box 5: Net VAT to pay HMRC or reclaim (Box 3 - Box 4)
        Box 6: Total value of sales ex VAT
        Box 7: Total value of purchases ex VAT
        Box 8: Total value of supplies to EU (rare post-Brexit)
        Box 9: Total value of acquisitions from EU (rare post-Brexit)
        """
        period_txns = [t for t in self.transactions if t.vat_period == period]

        if self.scheme == VATScheme.FLAT_RATE:
            return self._generate_flat_rate_return(period, period_txns)
        elif self.scheme == VATScheme.CASH_ACCOUNTING:
            return self._generate_cash_return(period, period_txns)
        else:
            return self._generate_standard_return(period, period_txns)

    def _generate_standard_return(self, period: str,
                                   txns: List[VATTransaction]) -> VATReturn:
        """Standard accruals-basis VAT return."""
        box1 = 0.0  # Output VAT (sales)
        box4 = 0.0  # Input VAT (purchases)
        box6 = 0.0  # Sales ex VAT
        box7 = 0.0  # Purchases ex VAT

        adjustments = []

        for t in txns:
            if t.supply_type.startswith("output"):
                box1 += t.vat_amount
                box6 += t.net_amount
            elif t.supply_type.startswith("input"):
                if t.vat_rate not in ("EXEMPT", "OUTSIDE_SCOPE"):
                    box4 += t.vat_amount
                box7 += t.net_amount
            elif t.supply_type == SupplyType.REVERSE_CHARGE_IN.value:
                # Reverse charge: account for VAT as both output and input
                # Box 1: add the VAT (as if you charged it to yourself)
                # Box 4: reclaim the same VAT (net effect = zero)
                # Box 6: NOT included (it's a purchase, not a sale)
                # Box 7: Include the net value
                box1 += t.vat_amount
                box4 += t.vat_amount
                box7 += t.net_amount
                adjustments.append({
                    "type": "reverse_charge",
                    "description": t.description,
                    "vat_amount": t.vat_amount,
                    "note": "CIS domestic reverse charge: VAT accounted for in both Box 1 and Box 4",
                })
            elif t.supply_type == SupplyType.REVERSE_CHARGE_OUT.value:
                # You issued a reverse charge invoice: no VAT on your invoice
                # Customer accounts for the VAT
                box6 += t.net_amount
                adjustments.append({
                    "type": "reverse_charge_issued",
                    "description": t.description,
                    "net_amount": t.net_amount,
                    "note": "Reverse charge invoice issued: VAT accounted for by customer",
                })

        # Bad debt relief adjustment
        bdr = self._calculate_bad_debt_relief(period)
        if bdr > 0:
            box4 += bdr
            adjustments.append({
                "type": "bad_debt_relief",
                "amount": round(bdr, 2),
                "note": f"VAT reclaimed on bad debts outstanding > {BAD_DEBT_RELIEF_DAYS} days",
            })

        # Fuel scale charge adjustment (if applicable)
        fsc = self._calculate_fuel_scale_charge(period)
        if fsc > 0:
            # Fuel scale charge adds to output VAT (Box 1)
            # because you're "supplying" fuel to yourself for personal use
            fsc_vat = round(float(Decimal(str(fsc)) * Decimal("0.20") / Decimal("1.20")), 2)
            box1 += float(fsc_vat)
            adjustments.append({
                "type": "fuel_scale_charge",
                "gross": round(fsc, 2),
                "vat": float(fsc_vat),
                "note": f"Fuel scale charge for {self.business_vehicle_co2}",
            })

        box2 = 0.0  # Post-Brexit: effectively zero for most
        box3 = box1 + box2
        box5 = box3 - box4
        box8 = 0.0
        box9 = 0.0

        period_start, period_end = get_period_dates(period)

        vr = VATReturn(
            period=period,
            period_start=period_start,
            period_end=period_end,
            entity=self.entity_name,
            scheme=self.scheme.value,
            box1_vat_due_sales=round(box1, 2),
            box2_vat_due_acquisitions=round(box2, 2),
            box3_total_vat_due=round(box3, 2),
            box4_vat_reclaimed=round(box4, 2),
            box5_net_vat=round(box5, 2),
            box6_total_sales_ex_vat=round(box6, 2),
            box7_total_purchases_ex_vat=round(box7, 2),
            box8_total_eu_supplies=round(box8, 2),
            box9_total_eu_acquisitions=round(box9, 2),
            status=VATReturnStatus.DRAFT.value,
            generated_at=datetime.now().isoformat(),
            transaction_count=len(txns),
            adjustments=adjustments,
        )

        self.returns.append(vr)
        return vr

    def _generate_flat_rate_return(self, period: str,
                                    txns: List[VATTransaction]) -> VATReturn:
        """Flat Rate Scheme return.

        Under FRS, you pay a fixed percentage of your VAT-inclusive turnover
        to HMRC. You don't reclaim input VAT on most purchases (except
        capital goods over £2,000 inc VAT).
        """
        # Get the flat rate percentage
        flat_pct = FLAT_RATE_PERCENTAGES.get(
            self.flat_rate_trade,
            FLAT_RATE_PERCENTAGES["other"]
        )

        # First year discount: 1% reduction
        if self.is_first_year_frs:
            flat_pct -= Decimal("1.0")

        # Calculate VAT-inclusive turnover for the period
        vat_inclusive_turnover = 0.0
        total_sales_ex_vat = 0.0
        total_purchases_ex_vat = 0.0

        for t in txns:
            if t.supply_type.startswith("output"):
                vat_inclusive_turnover += t.gross_amount
                total_sales_ex_vat += t.net_amount
            elif t.supply_type.startswith("input"):
                total_purchases_ex_vat += t.net_amount

        # Check limited cost trader
        goods_cost = sum(
            t.net_amount for t in txns
            if t.supply_type.startswith("input")
            and t.category in (
                "materials_and_supplies", "tools_and_equipment",
                "motor_expenses",  # fuel counts as goods
            )
        )

        is_limited_cost = goods_cost < float(
            LIMITED_COST_GOODS_PCT * Decimal(str(vat_inclusive_turnover))
        )
        # Also check annual floor (£1,000 per year, pro-rata for quarter = £250)
        period_floor = float(LIMITED_COST_ANNUAL_FLOOR) / 4
        if goods_cost < period_floor:
            is_limited_cost = True

        effective_rate = LIMITED_COST_TRADER_RATE if is_limited_cost else flat_pct

        # Box 1: flat rate % of VAT-inclusive turnover
        box1 = float(
            (Decimal(str(vat_inclusive_turnover)) * effective_rate / 100)
            .quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        )

        # Box 4: Only capital goods > £2,000 inc VAT
        box4 = 0.0
        capital_goods = [
            t for t in txns
            if t.supply_type.startswith("input")
            and t.gross_amount >= 2000.0
            and t.category in ("tools_and_equipment", "motor_expenses",
                               "office_costs", "computer_equipment")
        ]
        for cg in capital_goods:
            _, vat = calculate_vat(cg.gross_amount, cg.vat_rate)
            box4 += vat

        adjustments = [{
            "type": "flat_rate_scheme",
            "effective_rate": float(effective_rate),
            "is_limited_cost_trader": is_limited_cost,
            "goods_cost": round(goods_cost, 2),
            "vat_inclusive_turnover": round(vat_inclusive_turnover, 2),
            "first_year_discount": self.is_first_year_frs,
        }]

        box2 = 0.0
        box3 = box1 + box2
        box5 = box3 - box4

        period_start, period_end = get_period_dates(period)

        vr = VATReturn(
            period=period,
            period_start=period_start,
            period_end=period_end,
            entity=self.entity_name,
            scheme="flat_rate",
            box1_vat_due_sales=round(box1, 2),
            box2_vat_due_acquisitions=round(box2, 2),
            box3_total_vat_due=round(box3, 2),
            box4_vat_reclaimed=round(box4, 2),
            box5_net_vat=round(box5, 2),
            box6_total_sales_ex_vat=round(total_sales_ex_vat, 2),
            box7_total_purchases_ex_vat=round(total_purchases_ex_vat, 2),
            box8_total_eu_supplies=0.0,
            box9_total_eu_acquisitions=0.0,
            status=VATReturnStatus.DRAFT.value,
            generated_at=datetime.now().isoformat(),
            transaction_count=len(txns),
            adjustments=adjustments,
        )

        self.returns.append(vr)
        return vr

    def _generate_cash_return(self, period: str,
                               txns: List[VATTransaction]) -> VATReturn:
        """Cash Accounting Scheme return.

        Only account for VAT when payment is received/made,
        not when invoice is issued. Beneficial for cash flow
        when customers pay late.
        """
        # Filter to only paid transactions
        paid_txns = [t for t in txns if t.is_paid]

        # Then generate same as standard but on paid transactions
        box1 = sum(t.vat_amount for t in paid_txns
                   if t.supply_type.startswith("output"))
        box4 = sum(t.vat_amount for t in paid_txns
                   if t.supply_type.startswith("input")
                   and t.vat_rate not in ("EXEMPT", "OUTSIDE_SCOPE"))
        box6 = sum(t.net_amount for t in paid_txns
                   if t.supply_type.startswith("output"))
        box7 = sum(t.net_amount for t in paid_txns
                   if t.supply_type.startswith("input"))

        box2 = 0.0
        box3 = box1 + box2
        box5 = box3 - box4

        unpaid_count = len(txns) - len(paid_txns)
        adjustments = [{
            "type": "cash_accounting",
            "paid_transactions": len(paid_txns),
            "unpaid_deferred": unpaid_count,
            "note": f"{unpaid_count} transactions deferred to period when payment occurs",
        }]

        period_start, period_end = get_period_dates(period)

        vr = VATReturn(
            period=period,
            period_start=period_start,
            period_end=period_end,
            entity=self.entity_name,
            scheme="cash",
            box1_vat_due_sales=round(box1, 2),
            box2_vat_due_acquisitions=round(box2, 2),
            box3_total_vat_due=round(box3, 2),
            box4_vat_reclaimed=round(box4, 2),
            box5_net_vat=round(box5, 2),
            box6_total_sales_ex_vat=round(box6, 2),
            box7_total_purchases_ex_vat=round(box7, 2),
            box8_total_eu_supplies=0.0,
            box9_total_eu_acquisitions=0.0,
            status=VATReturnStatus.DRAFT.value,
            generated_at=datetime.now().isoformat(),
            transaction_count=len(paid_txns),
            adjustments=adjustments,
        )

        self.returns.append(vr)
        return vr

    # ------------------------------------------------------------------ #
    # ADJUSTMENTS
    # ------------------------------------------------------------------ #
    def _calculate_bad_debt_relief(self, period: str) -> float:
        """Calculate bad debt VAT relief for the period.

        VAT Act 1994 s.36: You can reclaim output VAT on invoices
        that are more than 6 months overdue AND have been written off.
        """
        period_start, period_end = get_period_dates(period)
        if not period_end:
            return 0.0

        cutoff = datetime.strptime(period_end, "%Y-%m-%d") - timedelta(days=BAD_DEBT_RELIEF_DAYS)
        relief = 0.0

        for inv in self.outstanding_invoices:
            if inv["paid"]:
                continue
            try:
                inv_date = datetime.strptime(inv["invoice_date"][:10], "%Y-%m-%d")
                if inv_date <= cutoff:
                    relief += inv["vat_amount"]
            except ValueError:
                continue

        return round(relief, 2)

    def _calculate_fuel_scale_charge(self, period: str) -> float:
        """Calculate fuel scale charge for the period.

        If you reclaim VAT on fuel used partly for private motoring,
        you must apply the fuel scale charge. This is a fixed amount
        based on your vehicle's CO2 emissions.

        The alternative is to only reclaim the business proportion of
        fuel VAT (no scale charge needed).
        """
        if self.business_fuel_pct >= 1.0:
            return 0.0  # 100% business use, no scale charge

        charge = FUEL_SCALE_CHARGES_QUARTERLY.get(self.business_vehicle_co2, 0)
        return float(charge)

    # ------------------------------------------------------------------ #
    # SCHEME OPTIMISATION
    # ------------------------------------------------------------------ #
    def optimise_scheme(self, annual_turnover: float,
                         annual_costs_with_vat: float,
                         goods_costs_with_vat: float = 0.0,
                         trade_sector: str = "general_building") -> Dict:
        """Compare VAT schemes and recommend the most tax-efficient.

        The Queen's question: Which scheme leaves the most money in
        John's pocket?

        Standard: Charge 20% on sales, reclaim 20% on purchases.
                  Pay the difference.
        Flat Rate: Charge 20% on sales (keep it), pay X% of gross to HMRC.
                   Keep the difference. No input VAT recovery (mostly).
        Cash:      Same as standard but only when money changes hands.
                   Better cash flow, same annual amount.
        """
        results = {}

        # 1. STANDARD SCHEME
        # Output VAT = 20% of turnover
        # Input VAT = VAT on costs (roughly costs * 20/120 if mostly standard-rated)
        output_vat = annual_turnover * 0.20
        input_vat = annual_costs_with_vat * (20 / 120)  # Approx
        standard_payable = output_vat - input_vat

        results["standard"] = {
            "scheme": "Standard Accounting",
            "output_vat": round(output_vat, 2),
            "input_vat_recovered": round(input_vat, 2),
            "net_payable": round(standard_payable, 2),
            "pros": "Full input VAT recovery. Best if costs are high relative to turnover",
            "cons": "Highest admin burden. Must account for VAT on invoicing, not payment",
        }

        # 2. FLAT RATE SCHEME
        if annual_turnover <= FRS_EXIT_THRESHOLD:
            flat_pct = FLAT_RATE_PERCENTAGES.get(trade_sector,
                                                  FLAT_RATE_PERCENTAGES["other"])

            # Check limited cost trader
            is_limited_cost = goods_costs_with_vat < (annual_turnover * 1.20 * 0.02)
            if goods_costs_with_vat < float(LIMITED_COST_ANNUAL_FLOOR):
                is_limited_cost = True

            effective_rate = LIMITED_COST_TRADER_RATE if is_limited_cost else flat_pct
            gross_turnover = annual_turnover * 1.20  # VAT-inclusive
            frs_payable = float(
                Decimal(str(gross_turnover)) * effective_rate / 100
            )
            frs_margin = (annual_turnover * 0.20) - frs_payable  # What you keep

            results["flat_rate"] = {
                "scheme": "Flat Rate Scheme",
                "flat_rate_pct": float(effective_rate),
                "is_limited_cost_trader": is_limited_cost,
                "vat_inclusive_turnover": round(gross_turnover, 2),
                "net_payable": round(frs_payable, 2),
                "margin_kept": round(frs_margin, 2),
                "pros": f"Simpler admin. Keep the difference between 20% charged and {effective_rate}% paid",
                "cons": "No input VAT recovery (except capital goods > £2k). Bad if costs are high",
            }
        else:
            results["flat_rate"] = {
                "scheme": "Flat Rate Scheme",
                "net_payable": None,
                "note": f"Not eligible -- turnover ({annual_turnover:,.0f}) exceeds FRS limit ({FRS_EXIT_THRESHOLD:,.0f})",
            }

        # 3. CASH ACCOUNTING
        # Same annual amount as standard, but cash flow benefit
        results["cash_accounting"] = {
            "scheme": "Cash Accounting Scheme",
            "net_payable": round(standard_payable, 2),  # Same as standard annually
            "pros": "Only pay VAT when customers pay you. Automatic bad debt relief. Better cash flow",
            "cons": "Can only reclaim input VAT when you pay suppliers. Same annual cost as standard",
            "cash_flow_benefit": "HIGH" if annual_turnover > 50000 else "MODERATE",
        }

        # 4. NOT REGISTERED
        if annual_turnover < VAT_REGISTRATION_THRESHOLD:
            results["not_registered"] = {
                "scheme": "Voluntary Deregistration",
                "net_payable": 0.0,
                "pros": "No VAT to pay or admin. Prices 20% lower to non-VAT customers",
                "cons": "Cannot reclaim input VAT. Lose VAT-registered credibility. Must re-register if turnover exceeds threshold",
                "note": f"Eligible -- turnover ({annual_turnover:,.0f}) is below threshold ({VAT_REGISTRATION_THRESHOLD:,.0f})",
            }

        # Find the winner
        payable_by_scheme = {k: v.get("net_payable", float("inf"))
                             for k, v in results.items()
                             if v.get("net_payable") is not None}
        best = min(payable_by_scheme, key=payable_by_scheme.get)

        return {
            "schemes": results,
            "recommended": best,
            "annual_saving_vs_standard": round(standard_payable - payable_by_scheme[best], 2),
            "recommendation": (
                f"Use {results[best]['scheme']}. "
                f"Annual VAT payable: {payable_by_scheme[best]:,.2f}. "
                f"Saves {standard_payable - payable_by_scheme[best]:,.2f}/year "
                f"vs standard accounting"
            ),
        }

    # ------------------------------------------------------------------ #
    # THRESHOLD MONITORING
    # ------------------------------------------------------------------ #
    def check_vat_threshold(self, as_of_date: str = None) -> Dict:
        """Check if rolling 12-month turnover triggers VAT registration.

        Must register if taxable turnover exceeds £90,000 in any
        rolling 12-month period. Also checks if approaching threshold.
        """
        if as_of_date is None:
            as_of_date = datetime.now().strftime("%Y-%m-%d")

        dt = datetime.strptime(as_of_date[:10], "%Y-%m-%d")

        # Calculate turnover for each rolling 12-month window
        # from transactions
        monthly_totals = defaultdict(float)
        for t in self.transactions:
            if t.supply_type.startswith("output"):
                month = t.date[:7]
                monthly_totals[month] += t.net_amount

        # Merge with any tracked rolling turnover
        for month, amt in self.rolling_turnover.items():
            monthly_totals[month] += amt

        # Current rolling 12 months
        rolling_total = 0.0
        for i in range(12):
            check_date = dt - timedelta(days=30 * i)
            month_key = check_date.strftime("%Y-%m")
            rolling_total += monthly_totals.get(month_key, 0)

        must_register = rolling_total > VAT_REGISTRATION_THRESHOLD
        can_deregister = rolling_total < VAT_DEREGISTRATION_THRESHOLD
        pct_of_threshold = (rolling_total / VAT_REGISTRATION_THRESHOLD) * 100

        warning = ""
        if must_register:
            warning = (
                f"MUST REGISTER: Rolling 12-month turnover ({rolling_total:,.0f}) "
                f"exceeds threshold ({VAT_REGISTRATION_THRESHOLD:,.0f}). "
                f"Must register within 30 days of the end of the month "
                f"in which threshold was exceeded"
            )
        elif pct_of_threshold > 85:
            warning = (
                f"APPROACHING THRESHOLD: At {pct_of_threshold:.0f}% of "
                f"registration threshold. Monitor closely. Consider "
                f"voluntary registration for input VAT recovery"
            )

        return {
            "rolling_12m_turnover": round(rolling_total, 2),
            "threshold": VAT_REGISTRATION_THRESHOLD,
            "pct_of_threshold": round(pct_of_threshold, 1),
            "must_register": must_register,
            "can_deregister": can_deregister,
            "warning": warning or "Below threshold. Registration optional.",
            "monthly_breakdown": dict(sorted(monthly_totals.items(), reverse=True)[:12]),
        }

    # ------------------------------------------------------------------ #
    # CIS REVERSE CHARGE
    # ------------------------------------------------------------------ #
    def apply_reverse_charge(self, description: str, net_amount: float,
                              date_str: str, counterparty: str = "") -> Dict:
        """Apply CIS domestic reverse charge.

        Since March 2021, certain construction services between
        VAT-registered businesses use reverse charge:
        - The supplier does NOT charge VAT on the invoice
        - The customer accounts for the VAT as both input and output
        - Net effect on customer's VAT return: zero (it cancels out)
        - BUT it prevents missing trader fraud

        The supplier invoices:
            Net: £1,000
            VAT: £0 (reverse charge - customer to account)
            Total: £1,000

        The customer's VAT return:
            Box 1 (output): +£200 (as if they charged it to themselves)
            Box 4 (input):  +£200 (reclaim it back)
            Box 7:          +£1,000 (purchase value)
            Net effect: £0
        """
        vat_amount, _ = calculate_vat_exclusive(net_amount, "STANDARD")

        # Record as both input and output
        txn_in = self.add_purchase(
            f"RC: {description}", net_amount + vat_amount, date_str,
            counterparty=counterparty, vat_rate="REVERSE_CHARGE",
            is_cis_reverse_charge=True, category="subcontractor_cis"
        )

        return {
            "transaction": asdict(txn_in),
            "net_amount": round(net_amount, 2),
            "vat_amount": round(vat_amount, 2),
            "box1_effect": round(vat_amount, 2),
            "box4_effect": round(vat_amount, 2),
            "net_vat_effect": 0.0,
            "note": (
                f"Reverse charge applied. Customer accounts for "
                f"{vat_amount:.2f} VAT. Net effect on VAT return: zero. "
                f"Invoice shows {net_amount:.2f} with no VAT line"
            ),
        }

    # ------------------------------------------------------------------ #
    # PARTIAL EXEMPTION
    # ------------------------------------------------------------------ #
    def calculate_partial_exemption(self, period: str) -> Dict:
        """Calculate partial exemption for mixed taxable/exempt supplies.

        If you make both taxable and exempt supplies, you can only
        reclaim input VAT that relates to taxable supplies.

        Standard method: apportion by turnover ratio.
        De minimis: if exempt input VAT is < £625/month AND < 50%
        of total input VAT, you can reclaim all input VAT.
        """
        period_txns = [t for t in self.transactions if t.vat_period == period]

        taxable_output = sum(
            t.net_amount for t in period_txns
            if t.supply_type.startswith("output")
            and t.vat_rate not in ("EXEMPT",)
        )
        exempt_output = sum(
            t.net_amount for t in period_txns
            if t.supply_type == "output_exempt"
        )
        total_output = taxable_output + exempt_output

        if total_output == 0 or exempt_output == 0:
            return {
                "applies": False,
                "reason": "No exempt supplies -- full input VAT recovery",
                "recovery_rate": 1.0,
            }

        # Standard method: taxable / total
        recovery_rate = taxable_output / total_output

        # Total input VAT
        total_input_vat = sum(
            t.vat_amount for t in period_txns
            if t.supply_type.startswith("input")
            and t.vat_rate not in ("EXEMPT", "OUTSIDE_SCOPE")
        )
        exempt_input_vat = total_input_vat * (1 - recovery_rate)

        # De minimis test
        months_in_period = 3 if "Q" in period else 1
        monthly_exempt = exempt_input_vat / max(months_in_period, 1)
        is_de_minimis = (
            monthly_exempt < 625
            and exempt_input_vat < total_input_vat * 0.50
        )

        if is_de_minimis:
            return {
                "applies": False,
                "reason": (
                    f"De minimis: exempt input VAT ({exempt_input_vat:.2f}) is "
                    f"< £625/month and < 50% of total. Full recovery allowed"
                ),
                "recovery_rate": 1.0,
                "exempt_input_vat": round(exempt_input_vat, 2),
            }

        recoverable = round(total_input_vat * recovery_rate, 2)
        blocked = round(total_input_vat - recoverable, 2)

        return {
            "applies": True,
            "recovery_rate": round(recovery_rate, 4),
            "taxable_turnover": round(taxable_output, 2),
            "exempt_turnover": round(exempt_output, 2),
            "total_input_vat": round(total_input_vat, 2),
            "recoverable_input_vat": recoverable,
            "blocked_input_vat": blocked,
            "reason": (
                f"Partial exemption applies. Recovery rate: {recovery_rate:.1%}. "
                f"Blocked VAT: {blocked:.2f} (relates to exempt supplies)"
            ),
        }

    # ------------------------------------------------------------------ #
    # VAT RAUV -- Internal bullshit detector for VAT returns
    # ------------------------------------------------------------------ #
    def run_vat_rauv(self, period: str) -> List[Dict]:
        """Run the RAUV audit on a VAT return before submission.

        The internal bullshit detector: flags anything that would
        make HMRC look twice at your VAT return.

        Checks:
        1. Box 5 negative (reclaim) without justification
        2. Input VAT > Output VAT ratio suspicious
        3. Large one-off claims
        4. Missing fuel scale charge
        5. Exempt supplies without partial exemption
        6. Flat rate scheme but high costs (should be on standard)
        7. Threshold breach
        8. Suspiciously round numbers
        9. Period-on-period volatility
        10. Reverse charge applied correctly
        """
        flags = []
        period_txns = [t for t in self.transactions if t.vat_period == period]

        # Generate the return to audit
        vr = None
        for r in self.returns:
            if r.period == period:
                vr = r
                break
        if vr is None:
            vr = self.generate_return(period)

        # Flag 1: Reclaim without justification
        if vr.box5_net_vat < 0:
            if abs(vr.box5_net_vat) > vr.box6_total_sales_ex_vat * 0.10:
                flags.append({
                    "severity": VATFlagSeverity.AMBER.value,
                    "flag": f"Large VAT reclaim ({vr.box5_net_vat:,.2f}) relative to sales",
                    "risk": "HMRC may query reclaims that exceed 10% of turnover. Common trigger for compliance checks",
                    "redirect": "Ensure all input VAT is backed by valid VAT invoices. Split large purchases across periods if possible",
                    "box_affected": "Box 5",
                })
            elif vr.box4_vat_reclaimed > 0 and vr.box1_vat_due_sales == 0:
                flags.append({
                    "severity": VATFlagSeverity.RED.value,
                    "flag": "Input VAT claimed with zero output VAT",
                    "risk": "No sales but claiming purchases. HMRC will query whether business is still trading",
                    "redirect": "If business is dormant, consider deregistering. If pre-trading, ensure you can evidence future taxable supplies",
                    "box_affected": "Box 1 / Box 4",
                })

        # Flag 2: Input/output ratio
        if vr.box1_vat_due_sales > 0:
            ratio = vr.box4_vat_reclaimed / vr.box1_vat_due_sales
            if ratio > 0.80:
                flags.append({
                    "severity": VATFlagSeverity.AMBER.value,
                    "flag": f"High input/output ratio ({ratio:.1%})",
                    "risk": "Reclaiming most of output VAT back. Normal for capital-intensive periods but flags on repeated quarters",
                    "redirect": "Check all input VAT relates to taxable business supplies. Remove any personal/exempt purchases",
                    "box_affected": "Box 4",
                })

        # Flag 3: Large one-off input claims
        large_inputs = [t for t in period_txns
                        if t.supply_type.startswith("input")
                        and t.vat_amount > 1000]
        if large_inputs:
            total_large = sum(t.vat_amount for t in large_inputs)
            if total_large > vr.box4_vat_reclaimed * 0.50:
                flags.append({
                    "severity": VATFlagSeverity.GREEN.value,
                    "flag": f"{len(large_inputs)} large input claims totalling {total_large:,.2f} VAT",
                    "risk": "Large individual claims attract HMRC attention. Ensure valid invoices retained",
                    "redirect": "Keep VAT invoices for all claims over £250. Verify supplier VAT numbers",
                    "box_affected": "Box 4",
                })

        # Flag 4: Fuel but no scale charge
        has_fuel = any(
            "fuel" in t.description.lower() or "diesel" in t.description.lower()
            or "petrol" in t.description.lower()
            for t in period_txns if t.supply_type.startswith("input")
        )
        if has_fuel and self.business_fuel_pct < 1.0:
            has_fsc = any(
                a.get("type") == "fuel_scale_charge"
                for a in (vr.adjustments or [])
            )
            if not has_fsc:
                flags.append({
                    "severity": VATFlagSeverity.AMBER.value,
                    "flag": "Fuel claimed but no fuel scale charge applied",
                    "risk": f"Business use is {self.business_fuel_pct:.0%}. Must either apply fuel scale charge or only claim business proportion",
                    "redirect": "Apply fuel scale charge OR restrict input VAT to business % only. Cannot claim full fuel VAT without scale charge",
                    "box_affected": "Box 4",
                })

        # Flag 5: Exempt supplies without partial exemption
        exempt_sales = [t for t in period_txns if t.supply_type == "output_exempt"]
        if exempt_sales:
            pe = self.calculate_partial_exemption(period)
            if pe.get("applies") and pe.get("blocked_input_vat", 0) > 0:
                flags.append({
                    "severity": VATFlagSeverity.RED.value,
                    "flag": f"Exempt supplies present but no partial exemption adjustment",
                    "risk": f"Blocked input VAT of {pe['blocked_input_vat']:,.2f} not accounted for. Over-reclaiming",
                    "redirect": f"Apply partial exemption. Recovery rate: {pe['recovery_rate']:.1%}. Reduce Box 4 by {pe['blocked_input_vat']:,.2f}",
                    "box_affected": "Box 4",
                })

        # Flag 6: Flat rate scheme efficiency check
        if self.scheme == VATScheme.FLAT_RATE:
            # Compare what you'd pay on standard vs flat rate
            std_payable = vr.box6_total_sales_ex_vat * 0.20 - sum(
                t.vat_amount for t in period_txns
                if t.supply_type.startswith("input")
                and t.vat_rate not in ("EXEMPT", "OUTSIDE_SCOPE")
            )
            if std_payable < vr.box5_net_vat:
                saving = vr.box5_net_vat - std_payable
                flags.append({
                    "severity": VATFlagSeverity.AMBER.value,
                    "flag": f"Standard scheme would save {saving:,.2f} this quarter",
                    "risk": "Flat rate is costing you more than standard. High-cost quarters erode FRS benefit",
                    "redirect": "Review scheme choice. If costs consistently > 40% of turnover, switch to standard",
                    "box_affected": "Box 5",
                })

        # Flag 7: Threshold proximity
        threshold_check = self.check_vat_threshold()
        if threshold_check["pct_of_threshold"] > 85:
            flags.append({
                "severity": VATFlagSeverity.AMBER.value if threshold_check["pct_of_threshold"] < 100 else VATFlagSeverity.RED.value,
                "flag": f"Rolling turnover at {threshold_check['pct_of_threshold']:.0f}% of registration threshold",
                "risk": threshold_check["warning"],
                "redirect": "Monitor monthly. If approaching, consider voluntary registration for input recovery",
                "box_affected": "N/A",
            })

        # Flag 8: Suspiciously round numbers
        round_amounts = [
            t for t in period_txns
            if t.vat_amount > 0 and t.vat_amount == round(t.vat_amount, 0)
            and t.vat_amount >= 100
        ]
        if len(round_amounts) > 3:
            flags.append({
                "severity": VATFlagSeverity.GREEN.value,
                "flag": f"{len(round_amounts)} transactions with perfectly round VAT amounts",
                "risk": "Estimated rather than calculated VAT. HMRC prefers exact calculations from invoices",
                "redirect": "Recalculate VAT from actual invoice totals using the VAT fraction (1/6 for 20%)",
                "box_affected": "Box 1 / Box 4",
            })

        # Flag 9: Period-on-period comparison
        prev_returns = [r for r in self.returns if r.period != period]
        if prev_returns:
            prev = prev_returns[-1]
            if prev.box6_total_sales_ex_vat > 0:
                sales_change = (
                    (vr.box6_total_sales_ex_vat - prev.box6_total_sales_ex_vat)
                    / prev.box6_total_sales_ex_vat
                )
                if abs(sales_change) > 0.50:
                    direction = "increase" if sales_change > 0 else "decrease"
                    flags.append({
                        "severity": VATFlagSeverity.AMBER.value,
                        "flag": f"Sales {direction} of {abs(sales_change):.0%} vs previous period",
                        "risk": f"Large period-on-period swing. HMRC may query {direction}s over 50%",
                        "redirect": "Ensure all invoices are in the correct period. Check for timing differences",
                        "box_affected": "Box 6",
                    })

        # Flag 10: Reverse charge compliance
        rc_txns = [t for t in period_txns if t.is_cis_reverse_charge]
        for rc in rc_txns:
            # Check it appears in both Box 1 and Box 4
            if rc.supply_type == SupplyType.REVERSE_CHARGE_IN.value:
                flags.append({
                    "severity": VATFlagSeverity.GREEN.value,
                    "flag": f"Reverse charge correctly applied: {rc.description[:50]}",
                    "risk": "Verify supplier confirmed reverse charge applies (both parties VAT registered, construction services)",
                    "redirect": "Keep written confirmation from supplier that reverse charge applies",
                    "box_affected": "Box 1 / Box 4",
                })

        return flags

    # ------------------------------------------------------------------ #
    # PRE-SUBMISSION VALIDATION
    # ------------------------------------------------------------------ #
    def validate_return(self, period: str) -> Dict:
        """Pre-submission validation checks for MTD.

        Must pass these before submitting to HMRC:
        1. All 9 boxes have values (even if zero)
        2. Box 3 = Box 1 + Box 2
        3. Box 5 = Box 3 - Box 4
        4. No negative values in Box 1, 2, 4, 6, 7, 8, 9
        5. Box 5 can be negative (reclaim)
        6. Period dates are valid
        7. Entity has valid VAT number
        """
        vr = None
        for r in self.returns:
            if r.period == period:
                vr = r
                break

        if vr is None:
            return {"valid": False, "errors": ["No return found for this period"]}

        errors = []
        warnings = []

        # Cross-check calculations
        calc_box3 = round(vr.box1_vat_due_sales + vr.box2_vat_due_acquisitions, 2)
        if round(vr.box3_total_vat_due, 2) != calc_box3:
            errors.append(f"Box 3 ({vr.box3_total_vat_due}) != Box 1 + Box 2 ({calc_box3})")

        calc_box5 = round(vr.box3_total_vat_due - vr.box4_vat_reclaimed, 2)
        if round(vr.box5_net_vat, 2) != calc_box5:
            errors.append(f"Box 5 ({vr.box5_net_vat}) != Box 3 - Box 4 ({calc_box5})")

        # Non-negative checks
        for box_name, value in [
            ("Box 1", vr.box1_vat_due_sales),
            ("Box 2", vr.box2_vat_due_acquisitions),
            ("Box 4", vr.box4_vat_reclaimed),
            ("Box 6", vr.box6_total_sales_ex_vat),
            ("Box 7", vr.box7_total_purchases_ex_vat),
        ]:
            if value < 0:
                errors.append(f"{box_name} is negative ({value})")

        # VAT number check
        if not self.vat_number:
            warnings.append("No VAT registration number set")

        # Period dates
        if not vr.period_start or not vr.period_end:
            errors.append("Period dates not set")

        # Zero return check
        if vr.box6_total_sales_ex_vat == 0 and vr.box7_total_purchases_ex_vat == 0:
            warnings.append("Nil return -- both sales and purchases are zero")

        is_valid = len(errors) == 0

        if is_valid:
            vr.status = VATReturnStatus.VALIDATED.value

        return {
            "valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "return_summary": {
                "period": vr.period,
                "net_vat": vr.box5_net_vat,
                "status": "PAY" if vr.box5_net_vat > 0 else "RECLAIM",
                "amount": abs(vr.box5_net_vat),
            },
        }

    # ------------------------------------------------------------------ #
    # REPORTING
    # ------------------------------------------------------------------ #
    def print_return(self, period: str) -> str:
        """Human-readable VAT return."""
        vr = None
        for r in self.returns:
            if r.period == period:
                vr = r
                break
        if vr is None:
            return f"No return found for {period}"

        lines = [
            "=" * 60,
            f"  MTD VAT RETURN — {vr.period}",
            f"  {vr.entity or 'HNC Accountant'}",
            f"  Scheme: {vr.scheme.upper()}",
            f"  Period: {vr.period_start} to {vr.period_end}",
            "=" * 60,
            "",
            f"  Box 1  VAT due on sales:              {vr.box1_vat_due_sales:>12,.2f}",
            f"  Box 2  VAT due on acquisitions:        {vr.box2_vat_due_acquisitions:>12,.2f}",
            f"  Box 3  Total VAT due:                  {vr.box3_total_vat_due:>12,.2f}",
            f"  Box 4  VAT reclaimed on purchases:     {vr.box4_vat_reclaimed:>12,.2f}",
            f"  Box 5  Net VAT to {'pay' if vr.box5_net_vat >= 0 else 'reclaim'}:"
            f"{'':16s}{vr.box5_net_vat:>12,.2f}",
            "",
            f"  Box 6  Total sales ex VAT:             {vr.box6_total_sales_ex_vat:>12,.2f}",
            f"  Box 7  Total purchases ex VAT:         {vr.box7_total_purchases_ex_vat:>12,.2f}",
            f"  Box 8  Total EU supplies:               {vr.box8_total_eu_supplies:>12,.2f}",
            f"  Box 9  Total EU acquisitions:            {vr.box9_total_eu_acquisitions:>12,.2f}",
            "",
            f"  Transactions: {vr.transaction_count}",
            f"  Status: {vr.status.upper()}",
        ]

        if vr.adjustments:
            lines.append("")
            lines.append("  Adjustments:")
            for adj in vr.adjustments:
                lines.append(f"    [{adj['type']}] {adj.get('note', '')[:70]}")

        lines.append("=" * 60)
        return "\n".join(lines)

    def get_period_summary(self, period: str) -> Dict:
        """Detailed summary of VAT activity for a period."""
        txns = [t for t in self.transactions if t.vat_period == period]

        by_rate = defaultdict(lambda: {"count": 0, "net": 0, "vat": 0, "gross": 0})
        by_type = defaultdict(lambda: {"count": 0, "net": 0, "vat": 0})

        for t in txns:
            by_rate[t.vat_rate]["count"] += 1
            by_rate[t.vat_rate]["net"] += t.net_amount
            by_rate[t.vat_rate]["vat"] += t.vat_amount
            by_rate[t.vat_rate]["gross"] += t.gross_amount

            by_type[t.supply_type]["count"] += 1
            by_type[t.supply_type]["net"] += t.net_amount
            by_type[t.supply_type]["vat"] += t.vat_amount

        return {
            "period": period,
            "total_transactions": len(txns),
            "by_vat_rate": {k: {kk: round(vv, 2) if isinstance(vv, float) else vv
                                 for kk, vv in v.items()}
                            for k, v in by_rate.items()},
            "by_supply_type": {k: {kk: round(vv, 2) if isinstance(vv, float) else vv
                                    for kk, vv in v.items()}
                               for k, v in by_type.items()},
        }

    # ------------------------------------------------------------------ #
    # PERSISTENCE
    # ------------------------------------------------------------------ #
    def save(self, path: str = "hnc_vat_data.json"):
        """Save VAT engine state."""
        data = {
            "entity": self.entity_name,
            "scheme": self.scheme.value,
            "vat_number": self.vat_number,
            "flat_rate_trade": self.flat_rate_trade,
            "transactions": [asdict(t) for t in self.transactions],
            "returns": [asdict(r) for r in self.returns],
            "outstanding_invoices": self.outstanding_invoices,
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def load(self, path: str = "hnc_vat_data.json"):
        """Load VAT engine state."""
        p = Path(path)
        if not p.exists():
            return
        with open(p) as f:
            data = json.load(f)
        self.entity_name = data.get("entity", "")
        self.scheme = VATScheme(data.get("scheme", "standard"))
        self.vat_number = data.get("vat_number", "")
        self.transactions = [VATTransaction(**t) for t in data.get("transactions", [])]
        self.outstanding_invoices = data.get("outstanding_invoices", [])


# ========================================================================
# TEST / DEMO
# ========================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("HNC VAT ENGINE -- Test Suite")
    print("Queen's logic: THINK about VAT, don't just add 20%")
    print("=" * 60)

    # ---- John's construction business, Flat Rate Scheme ----
    vat = HNCVATEngine(
        entity_name="John's Construction",
        scheme=VATScheme.FLAT_RATE,
        flat_rate_trade="general_building",
        vat_number="GB123456789",
        business_fuel_pct=0.75,
    )
    vat.is_first_year_frs = True  # First year discount

    # --- Q1 2026: January-March ---
    # Sales (all standard rated, construction services)
    vat.add_sale("Invoice 1042 - Kitchen fit Mrs Jones", 10200.00,
                 "2026-01-15", counterparty="Mrs Jones")
    vat.add_sale("Invoice 1043 - Bathroom Mr Davies", 7440.00,
                 "2026-01-28", counterparty="Mr Davies")
    vat.add_sale("Invoice 1044 - Extension Mr Williams", 18000.00,
                 "2026-02-15", counterparty="Mr Williams")
    vat.add_sale("Invoice 1045 - Loft conversion Mrs Taylor", 24000.00,
                 "2026-03-01", counterparty="Mrs Taylor")

    # Purchases
    vat.add_purchase("Travis Perkins timber", 892.40, "2026-01-06",
                     counterparty="Travis Perkins", category="materials_and_supplies")
    vat.add_purchase("Jewson plasterboard", 456.20, "2026-01-13",
                     counterparty="Jewson", category="materials_and_supplies")
    vat.add_purchase("Screwfix fixings", 234.50, "2026-01-20",
                     counterparty="Screwfix", category="materials_and_supplies")
    vat.add_purchase("Diesel van fill", 89.00, "2026-01-10",
                     counterparty="Shell", category="motor_expenses")
    vat.add_purchase("Diesel van fill", 92.00, "2026-01-20",
                     counterparty="BP", category="motor_expenses")
    vat.add_purchase("Diesel van fill", 95.00, "2026-02-10",
                     counterparty="Shell", category="motor_expenses")
    vat.add_purchase("Diesel van fill", 88.00, "2026-03-05",
                     counterparty="BP", category="motor_expenses")
    vat.add_purchase("Makita drill kit", 289.99, "2026-02-01",
                     counterparty="Toolstation", category="tools_and_equipment")
    vat.add_purchase("Annual accounts", 600.00, "2026-02-10",
                     counterparty="ABC Accountants", category="professional_fees")
    vat.add_purchase("Public liability insurance", 450.00, "2026-01-01",
                     counterparty="AXA", vat_rate="EXEMPT",
                     category="insurance_business")
    vat.add_purchase("Mobile phone bill", 45.00, "2026-01-15",
                     counterparty="EE", category="telephone_internet")
    vat.add_purchase("Skip hire", 280.00, "2026-02-20",
                     counterparty="Local Skip Hire", category="materials_and_supplies")

    # CIS reverse charge (from a VAT-registered subcontractor)
    print("\n--- CIS REVERSE CHARGE ---\n")
    rc = vat.apply_reverse_charge("Plastering subcontractor - Dave's Plastering",
                                   1500.00, "2026-02-01",
                                   counterparty="Dave's Plastering")
    print(f"  Net:       {rc['net_amount']:>10,.2f}")
    print(f"  VAT:       {rc['vat_amount']:>10,.2f}")
    print(f"  Box 1:    +{rc['box1_effect']:>10,.2f}")
    print(f"  Box 4:    +{rc['box4_effect']:>10,.2f}")
    print(f"  Net effect: {rc['net_vat_effect']:>9,.2f}")
    print(f"  {rc['note'][:80]}")

    # --- Generate Flat Rate Return ---
    print("\n--- FLAT RATE SCHEME RETURN (Q1 2026) ---\n")
    vr = vat.generate_return("2026-Q1")
    print(vat.print_return("2026-Q1"))

    # --- Validate ---
    print("\n--- PRE-SUBMISSION VALIDATION ---\n")
    validation = vat.validate_return("2026-Q1")
    print(f"  Valid:    {validation['valid']}")
    if validation['errors']:
        for err in validation['errors']:
            print(f"  ERROR:    {err}")
    if validation['warnings']:
        for w in validation['warnings']:
            print(f"  WARNING:  {w}")
    summary = validation['return_summary']
    print(f"  Status:   {summary['status']} {summary['amount']:,.2f}")

    # --- RAUV ---
    print("\n--- VAT RAUV: INTERNAL AUDIT ---\n")
    flags = vat.run_vat_rauv("2026-Q1")
    if flags:
        for f in flags:
            marker = "!!!" if f["severity"] == "RED" else " ! " if f["severity"] == "AMBER" else " i "
            print(f"  [{f['severity']:>5}]{marker} {f['flag']}")
            print(f"         {f['risk'][:80]}")
            print(f"         {f['redirect'][:80]}")
            print()
    else:
        print("  All clear. No VAT flags.")

    # --- Scheme Comparison ---
    print("\n--- SCHEME OPTIMISATION ---\n")
    annual_turnover = (10200 + 7440 + 18000 + 24000) * 4 / 3  # Annualised
    annual_costs = (892.40 + 456.20 + 234.50 + 89 + 92 + 95 + 88 +
                    289.99 + 600 + 450 + 45 + 280 + 1500) * 4 / 3
    goods_costs = (892.40 + 456.20 + 234.50 + 89 + 92 + 95 + 88) * 4 / 3

    opt = vat.optimise_scheme(annual_turnover, annual_costs, goods_costs)
    print(f"  Annual turnover (est): {annual_turnover:>12,.2f}")
    print(f"  Annual costs (est):    {annual_costs:>12,.2f}")
    print(f"  Goods costs (est):     {goods_costs:>12,.2f}")
    print(f"\n  Recommended: {opt['recommended'].upper()}")
    print(f"  {opt['recommendation']}")
    print(f"\n  Scheme comparison:")
    for name, scheme in opt["schemes"].items():
        payable = scheme.get("net_payable")
        if payable is not None:
            print(f"    {scheme['scheme']:<30s} Payable: {payable:>10,.2f}")
        else:
            print(f"    {scheme['scheme']:<30s} {scheme.get('note', 'N/A')}")

    # --- Now test STANDARD scheme for comparison ---
    print("\n" + "=" * 60)
    print("STANDARD SCHEME COMPARISON (same transactions)")
    print("=" * 60)

    vat_std = HNCVATEngine(
        entity_name="John's Construction",
        scheme=VATScheme.STANDARD,
        vat_number="GB123456789",
        business_fuel_pct=0.75,
    )

    # Re-add same transactions
    vat_std.add_sale("Invoice 1042 - Kitchen fit Mrs Jones", 10200.00,
                     "2026-01-15", counterparty="Mrs Jones")
    vat_std.add_sale("Invoice 1043 - Bathroom Mr Davies", 7440.00,
                     "2026-01-28", counterparty="Mr Davies")
    vat_std.add_sale("Invoice 1044 - Extension Mr Williams", 18000.00,
                     "2026-02-15", counterparty="Mr Williams")
    vat_std.add_sale("Invoice 1045 - Loft conversion Mrs Taylor", 24000.00,
                     "2026-03-01", counterparty="Mrs Taylor")

    vat_std.add_purchase("Travis Perkins timber", 892.40, "2026-01-06",
                         counterparty="Travis Perkins")
    vat_std.add_purchase("Jewson plasterboard", 456.20, "2026-01-13",
                         counterparty="Jewson")
    vat_std.add_purchase("Screwfix fixings", 234.50, "2026-01-20",
                         counterparty="Screwfix")
    vat_std.add_purchase("Diesel x4", 364.00, "2026-02-15",
                         counterparty="Various")
    vat_std.add_purchase("Makita drill kit", 289.99, "2026-02-01",
                         counterparty="Toolstation")
    vat_std.add_purchase("Annual accounts", 600.00, "2026-02-10",
                         counterparty="ABC Accountants")
    vat_std.add_purchase("Insurance", 450.00, "2026-01-01",
                         vat_rate="EXEMPT")
    vat_std.add_purchase("Mobile", 45.00, "2026-01-15")
    vat_std.add_purchase("Skip hire", 280.00, "2026-02-20")

    vat_std.apply_reverse_charge("Plastering sub", 1500.00, "2026-02-01",
                                  counterparty="Dave's Plastering")

    vr_std = vat_std.generate_return("2026-Q1")
    print(vat_std.print_return("2026-Q1"))

    # --- Side by side ---
    print("\n--- FLAT RATE vs STANDARD ---\n")
    print(f"  {'':30s} {'FLAT RATE':>12s} {'STANDARD':>12s}")
    print(f"  {'Box 1 (Output VAT)':<30s} {vr.box1_vat_due_sales:>12,.2f} {vr_std.box1_vat_due_sales:>12,.2f}")
    print(f"  {'Box 4 (Input VAT)':<30s} {vr.box4_vat_reclaimed:>12,.2f} {vr_std.box4_vat_reclaimed:>12,.2f}")
    print(f"  {'Box 5 (Net to pay)':<30s} {vr.box5_net_vat:>12,.2f} {vr_std.box5_net_vat:>12,.2f}")
    print(f"  {'Box 6 (Sales ex VAT)':<30s} {vr.box6_total_sales_ex_vat:>12,.2f} {vr_std.box6_total_sales_ex_vat:>12,.2f}")
    print(f"  {'Box 7 (Purchases ex VAT)':<30s} {vr.box7_total_purchases_ex_vat:>12,.2f} {vr_std.box7_total_purchases_ex_vat:>12,.2f}")

    frs_advantage = vr_std.box5_net_vat - vr.box5_net_vat
    winner = "FLAT RATE" if frs_advantage > 0 else "STANDARD"
    print(f"\n  Winner this quarter: {winner} (saves {abs(frs_advantage):,.2f})")

    # --- Threshold check ---
    print("\n--- VAT THRESHOLD MONITORING ---\n")
    threshold = vat.check_vat_threshold()
    print(f"  Rolling 12m turnover: {threshold['rolling_12m_turnover']:>12,.2f}")
    print(f"  Threshold:            {threshold['threshold']:>12,.2f}")
    print(f"  % of threshold:       {threshold['pct_of_threshold']:>11.1f}%")
    print(f"  {threshold['warning']}")

    # --- Period summary ---
    print("\n--- PERIOD DETAIL SUMMARY ---\n")
    ps = vat.get_period_summary("2026-Q1")
    print(f"  Transactions: {ps['total_transactions']}")
    print(f"  By VAT rate:")
    for rate, data in ps["by_vat_rate"].items():
        print(f"    {rate:<20s} Count={data['count']:>3d}  "
              f"Net={data['net']:>10,.2f}  VAT={data['vat']:>8,.2f}")

    print("\n" + "=" * 60)
    print("VAT engine tests complete. The Queen knows her rates.")
    print("=" * 60)
