"""
HNC SEER — hnc_seer.py
========================
Adapted from Aureon's aureon_seer.py (3,576 lines).

In Aureon, the Seer predicts price movements using multi-timeframe
analysis, pattern recognition, Fibonacci levels, and truth-weighted
conviction scoring. It looks FORWARD.

For the HNC Accountant, the Seer predicts:
    - Full-year tax liability from partial-year data
    - Optimal timing for expenses and income
    - Cash flow pressure points
    - Tax payment deadlines and required reserves
    - When to trigger specific weapons (pension, AIA, etc.)
    - Future policy changes and their impact

AUREON SEER                  →  HNC TAX SEER
──────────────────────────────────────────────────
Price Prediction             →  Tax Liability Prediction
Multi-Timeframe Analysis     →  Multi-Period Tax Analysis
Fibonacci Levels             →  Tax Band Boundaries
Support/Resistance           →  Threshold Proximity Alerts
Pattern Recognition          →  Expense Pattern Forecasting
Truth Prediction Engine      →  Compliance Truth Scoring
Volume Analysis              →  Cash Flow Volume Analysis
Trend Detection              →  Income/Expense Trend Detection
Reversal Signals             →  Policy Change Alerts

The Seer answers: "Based on what we know NOW, what will the
tax bill look like at year end — and what can we still do about it?"

Legal basis:
    - All predictions use current legislation as at 2025/26
    - Payment on account rules: ITA 2007 s.59A
    - Tax year: 6 April 2025 to 5 April 2026

Aureon Creator / Aureon Research — April 2026
"""

from __future__ import annotations
import logging
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import date, datetime, timedelta
from enum import Enum

logger = logging.getLogger("hnc_seer")

PHI = (1 + math.sqrt(5)) / 2  # 1.618 — The Golden Ratio


# ═══════════════════════════════════════════════════════════════════
# PREDICTION CONFIDENCE LEVELS
# ═══════════════════════════════════════════════════════════════════

class PredictionConfidence(Enum):
    """How sure are we about the prediction?"""
    CERTAIN = "CERTAIN"        # Based on actual filed data
    HIGH = "HIGH"              # 9+ months of data, clear trend
    MODERATE = "MODERATE"      # 6-9 months, some variance
    LOW = "LOW"                # <6 months or high variance
    SPECULATIVE = "SPECULATIVE" # Very early in year or major unknowns


class AlertSeverity(Enum):
    """Severity of a Seer alert"""
    INFO = "INFO"
    WARNING = "WARNING"
    URGENT = "URGENT"
    CRITICAL = "CRITICAL"


# ═══════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════

@dataclass
class MonthlySnapshot:
    """Financial data for a single month"""
    month: int  # 1-12
    year: int
    gross_income: float = 0
    expenses: float = 0
    net_profit: float = 0
    cis_deducted: float = 0
    vat_collected: float = 0
    vat_paid: float = 0


@dataclass
class TaxBandProximity:
    """How close are we to a tax band boundary?"""
    band_name: str
    threshold: float
    current_distance: float       # Positive = below, negative = above
    projected_distance: float     # Where we'll be at year end
    action: str                   # What to do about it
    saving_if_acted: float        # £ saved by staying below


@dataclass
class SeerAlert:
    """A predictive alert from the Seer"""
    severity: AlertSeverity
    title: str
    description: str
    action: str
    deadline: Optional[date] = None
    saving_potential: float = 0


@dataclass
class CashFlowForecast:
    """Monthly cash flow projection"""
    month: str
    income_projected: float
    expenses_projected: float
    tax_reserve_needed: float
    cumulative_reserve: float
    notes: str = ""


@dataclass
class SeerVision:
    """Complete Seer prediction output"""
    # Current position
    months_of_data: int
    confidence: PredictionConfidence
    ytd_gross_income: float
    ytd_net_profit: float
    ytd_cis_deducted: float

    # Full year projections
    projected_gross_income: float
    projected_net_profit: float
    projected_cis_total: float
    projected_tax_liability: float
    projected_ni_liability: float
    projected_total_liability: float

    # After optimisation
    optimised_liability: float
    total_saving: float

    # Band proximity analysis
    band_alerts: List[TaxBandProximity]

    # Cash flow
    monthly_reserve_needed: float
    cash_flow_forecast: List[CashFlowForecast]

    # Timing recommendations
    timing_actions: List[str]

    # Alerts
    alerts: List[SeerAlert]

    # Payment schedule
    payment_schedule: List[dict]


# ═══════════════════════════════════════════════════════════════════
# UK TAX THRESHOLDS — The "Fibonacci Levels" of Tax
# ═══════════════════════════════════════════════════════════════════

TAX_THRESHOLDS_2025_26 = {
    "personal_allowance": 12_570,
    "basic_rate_limit": 50_270,       # PA + basic band
    "higher_rate_limit": 125_140,     # PA taper begins
    "pa_taper_start": 100_000,
    "class2_threshold": 12_570,
    "class4_lower": 12_570,
    "class4_upper": 50_270,
    "vat_threshold": 90_000,
    "aia_limit": 1_000_000,
    "pension_annual_allowance": 60_000,
    "cgt_annual_exempt": 3_000,
    "marriage_allowance_transfer": 1_260,
    "trading_allowance": 1_000,
}

TAX_RATES_2025_26 = {
    "basic": 0.20,
    "higher": 0.40,
    "additional": 0.45,
    "class4_main": 0.06,
    "class4_upper": 0.02,
    "class2_weekly": 3.45,
}


# ═══════════════════════════════════════════════════════════════════
# THE SEER ENGINE
# ═══════════════════════════════════════════════════════════════════

class HNCSeer:
    """
    Tax Liability Prediction Engine.

    Adapted from Aureon Seer: replaces price prediction with tax
    liability prediction. Same multi-timeframe, same Fibonacci
    precision, same forward-looking logic.
    """

    def __init__(self, monthly_data: List[MonthlySnapshot] = None, tax_year_start: int = 2025):
        self.monthly_data = monthly_data or []
        self.tax_year_start = tax_year_start
        self.thresholds = TAX_THRESHOLDS_2025_26
        self.rates = TAX_RATES_2025_26

    def _months_in_data(self) -> int:
        """How many months of data do we have?"""
        return len(self.monthly_data)

    def _confidence_level(self) -> PredictionConfidence:
        months = self._months_in_data()
        if months >= 12:
            return PredictionConfidence.CERTAIN
        if months >= 9:
            return PredictionConfidence.HIGH
        if months >= 6:
            return PredictionConfidence.MODERATE
        if months >= 3:
            return PredictionConfidence.LOW
        return PredictionConfidence.SPECULATIVE

    def _ytd_totals(self) -> dict:
        """Sum up year-to-date figures."""
        return {
            "gross_income": sum(m.gross_income for m in self.monthly_data),
            "expenses": sum(m.expenses for m in self.monthly_data),
            "net_profit": sum(m.net_profit for m in self.monthly_data),
            "cis_deducted": sum(m.cis_deducted for m in self.monthly_data),
        }

    def _project_full_year(self, ytd: dict) -> dict:
        """Project full year from YTD using trend-weighted extrapolation."""
        months = self._months_in_data()
        if months == 0:
            return {k: 0 for k in ytd}

        if months >= 12:
            return ytd  # We have the full year

        # Phi-weighted projection: recent months weighted more heavily
        # This is the Aureon Seer's core innovation adapted for tax
        if months >= 3:
            recent_3 = self.monthly_data[-3:]
            recent_avg = {
                "gross_income": sum(m.gross_income for m in recent_3) / 3,
                "expenses": sum(m.expenses for m in recent_3) / 3,
                "net_profit": sum(m.net_profit for m in recent_3) / 3,
                "cis_deducted": sum(m.cis_deducted for m in recent_3) / 3,
            }
            overall_avg = {k: v / months for k, v in ytd.items()}

            # Blend: phi-weight towards recent trend
            phi_weight = 1 / PHI  # ~0.618
            blended_monthly = {}
            for k in ytd:
                blended_monthly[k] = (
                    recent_avg[k] * phi_weight +
                    overall_avg[k] * (1 - phi_weight)
                )
            remaining_months = 12 - months
            projected = {k: ytd[k] + blended_monthly[k] * remaining_months for k in ytd}
        else:
            # Not enough data for trend — simple extrapolation
            factor = 12 / months
            projected = {k: v * factor for k, v in ytd.items()}

        return projected

    def _calc_tax(self, net_profit: float) -> Tuple[float, float]:
        """Calculate income tax and NI on given profit."""
        pa = self.thresholds["personal_allowance"]
        basic_limit = self.thresholds["basic_rate_limit"]

        taxable = max(0, net_profit - pa)
        basic_band = basic_limit - pa  # 37,700

        # Income tax
        if taxable <= basic_band:
            tax = taxable * self.rates["basic"]
        else:
            tax = basic_band * self.rates["basic"]
            tax += (taxable - basic_band) * self.rates["higher"]

        # Class 4 NI
        ni_profit = max(0, net_profit - self.thresholds["class4_lower"])
        upper_band = self.thresholds["class4_upper"] - self.thresholds["class4_lower"]
        if ni_profit <= upper_band:
            ni = ni_profit * self.rates["class4_main"]
        else:
            ni = upper_band * self.rates["class4_main"]
            ni += (ni_profit - upper_band) * self.rates["class4_upper"]

        # Class 2 NI
        if net_profit >= self.thresholds["class2_threshold"]:
            ni += self.rates["class2_weekly"] * 52

        return round(tax, 2), round(ni, 2)

    def _analyse_band_proximity(self, projected_profit: float) -> List[TaxBandProximity]:
        """Analyse how close we are to each tax band boundary."""
        alerts = []

        # Personal Allowance
        pa = self.thresholds["personal_allowance"]
        if projected_profit < pa + 5_000:
            alerts.append(TaxBandProximity(
                band_name="Personal Allowance",
                threshold=pa,
                current_distance=pa - projected_profit,
                projected_distance=pa - projected_profit,
                action="Below PA = zero income tax" if projected_profit < pa else "Just above PA — consider pension to drop below",
                saving_if_acted=min(projected_profit - pa, 0) * -self.rates["basic"] if projected_profit > pa else 0,
            ))

        # Basic/Higher rate boundary
        higher_start = self.thresholds["basic_rate_limit"]
        distance = higher_start - projected_profit
        if abs(distance) < 10_000:
            action = (
                "DANGER: Approaching higher rate (40%). "
                "Pension contribution or expense acceleration can keep you in basic rate."
                if distance > 0 and distance < 5_000
                else "IN HIGHER RATE. Pension contributions will save 40p per £1."
                if distance < 0
                else "Safely in basic rate."
            )
            saving = abs(distance) * 0.20 if distance < 0 else 0  # 20% diff between basic and higher
            alerts.append(TaxBandProximity(
                band_name="Basic → Higher Rate Boundary",
                threshold=higher_start,
                current_distance=distance,
                projected_distance=distance,
                action=action,
                saving_if_acted=saving,
            ))

        # VAT threshold
        vat_t = self.thresholds["vat_threshold"]
        ytd = self._ytd_totals()
        vat_distance = vat_t - (ytd.get("gross_income", 0) * (12 / max(self._months_in_data(), 1)))
        if vat_distance < 15_000:
            alerts.append(TaxBandProximity(
                band_name="VAT Registration Threshold",
                threshold=vat_t,
                current_distance=vat_distance,
                projected_distance=vat_distance,
                action="WATCH: Approaching VAT threshold. Consider voluntary registration for input recovery." if vat_distance > 0 else "ABOVE VAT THRESHOLD — must register.",
                saving_if_acted=0,
            ))

        # PA taper (£100k)
        pa_taper = self.thresholds["pa_taper_start"]
        taper_distance = pa_taper - projected_profit
        if taper_distance < 20_000 and taper_distance > -30_000:
            alerts.append(TaxBandProximity(
                band_name="Personal Allowance Taper (£100k)",
                threshold=pa_taper,
                current_distance=taper_distance,
                projected_distance=taper_distance,
                action="CRITICAL: PA taper zone = effective 60% marginal rate. Pension NOW." if taper_distance < 0 else "Approaching taper zone. Plan pension contributions.",
                saving_if_acted=min(abs(taper_distance), pa) * 0.40 if taper_distance < 0 else 0,
            ))

        return alerts

    def _build_cash_flow_forecast(self, projected: dict) -> List[CashFlowForecast]:
        """Build month-by-month cash flow forecast."""
        monthly_income = projected["gross_income"] / 12
        monthly_expenses = projected["expenses"] / 12
        monthly_profit = projected["net_profit"] / 12

        # Tax reserve calculation
        tax, ni = self._calc_tax(projected["net_profit"])
        total_liability = tax + ni - projected.get("cis_deducted", 0)
        monthly_reserve = max(0, total_liability) / 12

        forecast = []
        months = ["Apr", "May", "Jun", "Jul", "Aug", "Sep",
                   "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
        cumulative = 0

        for i, month in enumerate(months):
            cumulative += monthly_reserve
            notes = ""
            if month == "Jan":
                notes = "PAYMENT ON ACCOUNT 1 DUE (31 Jan)"
            elif month == "Jul":
                notes = "PAYMENT ON ACCOUNT 2 DUE (31 Jul)"
            elif month == "Oct":
                notes = "SA FILING DEADLINE approaching (31 Jan)"

            forecast.append(CashFlowForecast(
                month=month,
                income_projected=round(monthly_income, 2),
                expenses_projected=round(monthly_expenses, 2),
                tax_reserve_needed=round(monthly_reserve, 2),
                cumulative_reserve=round(cumulative, 2),
                notes=notes,
            ))

        return forecast

    def _generate_timing_actions(self, projected: dict, bands: List[TaxBandProximity]) -> List[str]:
        """Generate timing-specific recommendations."""
        actions = []
        today = date.today()
        tax_year_end = date(self.tax_year_start + 1, 4, 5)
        months_remaining = max(0, (tax_year_end - today).days // 30)

        if months_remaining <= 3:
            actions.append(f"URGENT: Only {months_remaining} months left in tax year. Accelerate any planned expenses NOW.")

        if months_remaining <= 6:
            actions.append("Consider pension contribution before 5 April to reduce this year's liability.")

        for band in bands:
            if band.band_name == "Basic → Higher Rate Boundary" and band.projected_distance < 5_000 and band.projected_distance > 0:
                excess = abs(band.projected_distance)
                actions.append(
                    f"You're £{excess:,.0f} from higher rate. "
                    f"A pension contribution of £{excess:,.0f} keeps you at 20%."
                )

        # Payment on account
        tax, ni = self._calc_tax(projected["net_profit"])
        total = tax + ni - projected.get("cis_deducted", 0)
        if total > 1_000:
            poa = total / 2
            actions.append(
                f"Payment on Account: 2 x £{poa:,.0f}. "
                f"Due 31 Jan {self.tax_year_start + 2} and 31 Jul {self.tax_year_start + 2}."
            )

        return actions

    def _generate_alerts(self, projected: dict, bands: List[TaxBandProximity]) -> List[SeerAlert]:
        """Generate predictive alerts."""
        alerts = []
        today = date.today()
        tax_year_end = date(self.tax_year_start + 1, 4, 5)

        # Filing deadline alert
        filing_deadline = date(self.tax_year_start + 2, 1, 31)
        days_to_filing = (filing_deadline - today).days
        if days_to_filing <= 90:
            alerts.append(SeerAlert(
                severity=AlertSeverity.URGENT,
                title="SA Filing Deadline Approaching",
                description=f"{days_to_filing} days until Self Assessment filing deadline.",
                action="Ensure all records are complete. File early for early refund of any overpayment.",
                deadline=filing_deadline,
            ))

        # Band proximity alerts
        for band in bands:
            if band.projected_distance < 0 and "Higher Rate" in band.band_name:
                alerts.append(SeerAlert(
                    severity=AlertSeverity.WARNING,
                    title="Higher Rate Tax Band Breached",
                    description=f"Projected profit puts you £{abs(band.projected_distance):,.0f} into higher rate.",
                    action="Pension contribution or expense acceleration recommended.",
                    saving_potential=band.saving_if_acted,
                ))

        # CIS refund alert
        cis = projected.get("cis_deducted", 0)
        tax, ni = self._calc_tax(projected["net_profit"])
        if cis > (tax + ni):
            refund = cis - (tax + ni)
            alerts.append(SeerAlert(
                severity=AlertSeverity.INFO,
                title="CIS Refund Due",
                description=f"CIS deductions (£{cis:,.0f}) exceed liability (£{tax + ni:,.0f}). Refund: £{refund:,.0f}.",
                action="File SA return to trigger refund. Earlier filing = earlier refund.",
                saving_potential=refund,
            ))

        # VAT threshold approaching
        projected_turnover = projected.get("gross_income", 0)
        if projected_turnover > 75_000 and projected_turnover < 95_000:
            alerts.append(SeerAlert(
                severity=AlertSeverity.WARNING,
                title="VAT Threshold Proximity",
                description=f"Projected turnover £{projected_turnover:,.0f} vs threshold £90,000.",
                action="Monitor rolling 12-month turnover. Consider voluntary registration for input VAT recovery.",
            ))

        return alerts

    def predict(self) -> SeerVision:
        """
        The main prediction. Produces a complete forward-looking vision.
        """
        ytd = self._ytd_totals()
        months = self._months_in_data()
        confidence = self._confidence_level()
        projected = self._project_full_year(ytd)

        # Tax calculations
        tax, ni = self._calc_tax(projected["net_profit"])
        total_liability = tax + ni
        cis_credit = projected.get("cis_deducted", 0)

        # Band analysis
        bands = self._analyse_band_proximity(projected["net_profit"])

        # Optimised estimate (rough — full optimisation is done by TaxWarfare)
        # Here we just show the CIS credit effect
        optimised = max(0, total_liability - cis_credit)

        # Cash flow
        projected_with_cis = {**projected, "cis_deducted": cis_credit}
        cash_flow = self._build_cash_flow_forecast(projected_with_cis)
        monthly_reserve = cash_flow[0].tax_reserve_needed if cash_flow else 0

        # Timing actions
        timing = self._generate_timing_actions(projected_with_cis, bands)

        # Alerts
        alerts = self._generate_alerts(projected_with_cis, bands)

        # Payment schedule
        total_due = max(0, total_liability - cis_credit)
        payment_schedule = []
        if total_due > 1_000:
            poa = total_due / 2
            payment_schedule = [
                {
                    "date": f"31 Jan {self.tax_year_start + 2}",
                    "description": "Balancing Payment + 1st Payment on Account",
                    "amount": round(total_due / 2 + poa, 2),
                },
                {
                    "date": f"31 Jul {self.tax_year_start + 2}",
                    "description": "2nd Payment on Account",
                    "amount": round(poa, 2),
                },
            ]
        elif total_due > 0:
            payment_schedule = [
                {
                    "date": f"31 Jan {self.tax_year_start + 2}",
                    "description": "Balancing Payment (no POA — under £1,000)",
                    "amount": round(total_due, 2),
                },
            ]

        return SeerVision(
            months_of_data=months,
            confidence=confidence,
            ytd_gross_income=round(ytd["gross_income"], 2),
            ytd_net_profit=round(ytd["net_profit"], 2),
            ytd_cis_deducted=round(ytd.get("cis_deducted", 0), 2),
            projected_gross_income=round(projected["gross_income"], 2),
            projected_net_profit=round(projected["net_profit"], 2),
            projected_cis_total=round(cis_credit, 2),
            projected_tax_liability=round(tax, 2),
            projected_ni_liability=round(ni, 2),
            projected_total_liability=round(total_liability, 2),
            optimised_liability=round(optimised, 2),
            total_saving=round(total_liability - optimised, 2),
            band_alerts=bands,
            monthly_reserve_needed=round(monthly_reserve, 2),
            cash_flow_forecast=cash_flow,
            timing_actions=timing,
            alerts=alerts,
            payment_schedule=payment_schedule,
        )


# ═══════════════════════════════════════════════════════════════════
# DEMO / TEST
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("HNC SEER — TAX LIABILITY PREDICTION ENGINE")
    print("Adapted from Aureon Seer (3,576 lines)")
    print("=" * 70)

    # Simulate 9 months of data (Apr 2025 - Dec 2025)
    months_data = []
    for i in range(9):
        month_num = 4 + i  # Apr=4 through Dec=12
        if month_num > 12:
            month_num -= 12
        months_data.append(MonthlySnapshot(
            month=month_num,
            year=2025 if month_num >= 4 else 2026,
            gross_income=5_666,    # ~£51k/year
            expenses=2_888,        # ~£26k/year
            net_profit=2_778,      # ~£25k/year
            cis_deducted=1_133,    # ~£10.2k/year
        ))

    seer = HNCSeer(monthly_data=months_data, tax_year_start=2025)
    vision = seer.predict()

    print(f"\nConfidence: {vision.confidence.value} ({vision.months_of_data} months of data)")
    print(f"\nYTD Position:")
    print(f"  Gross Income:  £{vision.ytd_gross_income:>10,.2f}")
    print(f"  Net Profit:    £{vision.ytd_net_profit:>10,.2f}")
    print(f"  CIS Deducted:  £{vision.ytd_cis_deducted:>10,.2f}")

    print(f"\nFull Year Projection:")
    print(f"  Gross Income:  £{vision.projected_gross_income:>10,.2f}")
    print(f"  Net Profit:    £{vision.projected_net_profit:>10,.2f}")
    print(f"  CIS Total:     £{vision.projected_cis_total:>10,.2f}")

    print(f"\nTax Liability:")
    print(f"  Income Tax:    £{vision.projected_tax_liability:>10,.2f}")
    print(f"  National Ins:  £{vision.projected_ni_liability:>10,.2f}")
    print(f"  Total:         £{vision.projected_total_liability:>10,.2f}")
    print(f"  After CIS:     £{vision.optimised_liability:>10,.2f}")
    print(f"  CIS Saving:    £{vision.total_saving:>10,.2f}")

    print(f"\nMonthly Reserve Needed: £{vision.monthly_reserve_needed:,.2f}")

    print(f"\n{'─' * 70}")
    print("TAX BAND PROXIMITY ALERTS")
    print(f"{'─' * 70}")
    for band in vision.band_alerts:
        direction = "below" if band.current_distance > 0 else "ABOVE"
        print(f"  {band.band_name}: £{abs(band.current_distance):,.0f} {direction} (£{band.threshold:,.0f})")
        print(f"    Action: {band.action}")

    print(f"\n{'─' * 70}")
    print("SEER ALERTS")
    print(f"{'─' * 70}")
    for alert in vision.alerts:
        print(f"  [{alert.severity.value}] {alert.title}")
        print(f"    {alert.description}")
        if alert.saving_potential:
            print(f"    Potential: £{alert.saving_potential:,.0f}")

    print(f"\n{'─' * 70}")
    print("TIMING ACTIONS")
    print(f"{'─' * 70}")
    for action in vision.timing_actions:
        print(f"  → {action}")

    if vision.payment_schedule:
        print(f"\n{'─' * 70}")
        print("PAYMENT SCHEDULE")
        print(f"{'─' * 70}")
        for p in vision.payment_schedule:
            print(f"  {p['date']}: £{p['amount']:,.2f} — {p['description']}")
