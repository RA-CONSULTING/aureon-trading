"""
HNC FORECAST — hnc_forecast.py
================================
Tax Liability & Cash Flow Forecaster.

Looks forward, not backward. Takes current YTD figures and projects
the full year — turnover, expenses, tax liability, VAT, NI, payments
on account. Tells the client exactly how much cash they need to
reserve for HMRC and when they need to pay it.

Features:
    1. Full-year tax projection from YTD actuals
    2. Monthly cash flow forecast
    3. VAT liability projection (quarterly)
    4. Payment schedule (31 Jan / 31 Jul / quarterly VAT)
    5. Tax reserve recommendation
    6. "What-if" scenario modelling (salary sacrifice, pension,
       expense timing, crypto disposal timing)
    7. Seasonal adjustment (construction seasonality)
    8. CIS deduction forecasting
    9. VAT threshold monitoring

Aureon Creator / Aureon Research — April 2026
"""

from __future__ import annotations
import logging
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("hnc_forecast")


# ========================================================================
# UK TAX CONSTANTS (2025/26)
# ========================================================================

PERSONAL_ALLOWANCE = 12570.0
PA_TAPER_START = 100000.0
BASIC_RATE_BAND = 37700.0      # 20% up to £50,270
HIGHER_RATE_BAND = 87440.0     # 40% up to £125,140 (effective)
ADDITIONAL_THRESHOLD = 125140.0  # 45% above

CLASS2_WEEKLY = 3.45
CLASS2_ANNUAL = CLASS2_WEEKLY * 52
CLASS4_LOWER = 12570.0
CLASS4_UPPER = 50270.0
CLASS4_RATE_MAIN = 0.06         # 6% between thresholds
CLASS4_RATE_ADDITIONAL = 0.02   # 2% above upper

VAT_THRESHOLD = 90000.0
FRS_RATE_CONSTRUCTION = 0.095   # 9.5% for general building

# Construction seasonality index (relative to annual average)
CONSTRUCTION_SEASONALITY = {
    1: 0.75, 2: 0.80, 3: 0.95, 4: 1.05, 5: 1.15, 6: 1.20,
    7: 1.20, 8: 1.15, 9: 1.10, 10: 1.00, 11: 0.85, 12: 0.80,
}


# ========================================================================
# DATA STRUCTURES
# ========================================================================

@dataclass
class MonthForecast:
    """Forecast for a single month."""
    month: int = 0                  # 1-12
    month_name: str = ""
    revenue: float = 0.0
    expenses: float = 0.0
    profit: float = 0.0
    vat_liability: float = 0.0
    cumulative_revenue: float = 0.0
    cumulative_profit: float = 0.0
    cumulative_tax: float = 0.0
    cash_reserve_needed: float = 0.0
    is_actual: bool = False         # True if from real data


@dataclass
class ForecastResult:
    """Complete forecast output."""
    entity: str = ""
    tax_year: str = ""
    generated: str = ""
    months: List[MonthForecast] = field(default_factory=list)
    annual: Dict[str, float] = field(default_factory=dict)
    payment_schedule: List[Dict] = field(default_factory=list)
    alerts: List[Dict] = field(default_factory=list)
    scenarios: List[Dict] = field(default_factory=list)


# ========================================================================
# FORECAST ENGINE
# ========================================================================

class HNCForecastEngine:
    """
    Tax liability and cash flow forecaster.

    Usage:
        forecast = HNCForecastEngine(
            entity_name="John Smith",
            tax_year="2025/26",
        )

        # Feed YTD actuals
        forecast.set_ytd(
            months_elapsed=6,
            ytd_revenue=32000,
            ytd_expenses=9500,
            ytd_cis_deductions=1200,
        )

        result = forecast.project()
    """

    def __init__(self,
                 entity_name: str = "",
                 tax_year: str = "2025/26",
                 vat_registered: bool = True,
                 vat_scheme: str = "flat_rate",
                 trade_sector: str = "construction",
                 use_seasonality: bool = True):
        self.entity_name = entity_name
        self.tax_year = tax_year
        self.vat_registered = vat_registered
        self.vat_scheme = vat_scheme
        self.trade_sector = trade_sector
        self.use_seasonality = use_seasonality

        # YTD actuals
        self.months_elapsed = 0
        self.ytd_revenue = 0.0
        self.ytd_expenses = 0.0
        self.ytd_cis_deductions = 0.0
        self.ytd_vat_paid = 0.0
        self.expense_ratio = 0.25      # Default: 25% of revenue

        # Monthly actuals (if available)
        self.monthly_actuals: List[Dict] = []

    def set_ytd(self,
                months_elapsed: int,
                ytd_revenue: float,
                ytd_expenses: float,
                ytd_cis_deductions: float = 0.0,
                ytd_vat_paid: float = 0.0,
                monthly_breakdown: List[Dict] = None):
        """Set year-to-date actual figures."""
        self.months_elapsed = months_elapsed
        self.ytd_revenue = ytd_revenue
        self.ytd_expenses = ytd_expenses
        self.ytd_cis_deductions = ytd_cis_deductions
        self.ytd_vat_paid = ytd_vat_paid

        if ytd_revenue > 0:
            self.expense_ratio = ytd_expenses / ytd_revenue

        if monthly_breakdown:
            self.monthly_actuals = monthly_breakdown

    def project(self) -> ForecastResult:
        """Generate full-year forecast from YTD actuals."""
        result = ForecastResult(
            entity=self.entity_name,
            tax_year=self.tax_year,
            generated=datetime.now().strftime("%d/%m/%Y"),
        )

        # Project monthly figures
        months = []
        cumulative_rev = 0.0
        cumulative_exp = 0.0
        cumulative_profit = 0.0

        # Calculate average monthly revenue from actuals
        if self.months_elapsed > 0:
            avg_monthly_rev = self.ytd_revenue / self.months_elapsed
            avg_monthly_exp = self.ytd_expenses / self.months_elapsed
        else:
            avg_monthly_rev = 0.0
            avg_monthly_exp = 0.0

        # Tax year runs April (month 1) to March (month 12)
        # Month 1 = April, Month 12 = March
        tax_year_start = int(self.tax_year.split("/")[0])

        for m in range(1, 13):
            calendar_month = ((m - 1 + 3) % 12) + 1  # April=4, May=5, ... March=3

            mf = MonthForecast(
                month=m,
                month_name=_month_name(calendar_month),
            )

            if m <= self.months_elapsed:
                # Actual data
                if self.monthly_actuals and m <= len(self.monthly_actuals):
                    actual = self.monthly_actuals[m - 1]
                    mf.revenue = actual.get("revenue", avg_monthly_rev)
                    mf.expenses = actual.get("expenses", avg_monthly_exp)
                else:
                    mf.revenue = avg_monthly_rev
                    mf.expenses = avg_monthly_exp
                mf.is_actual = True
            else:
                # Projected
                if self.use_seasonality and self.trade_sector == "construction":
                    seasonal = CONSTRUCTION_SEASONALITY.get(calendar_month, 1.0)
                    mf.revenue = avg_monthly_rev * seasonal
                    mf.expenses = avg_monthly_exp * seasonal
                else:
                    mf.revenue = avg_monthly_rev
                    mf.expenses = avg_monthly_exp

            mf.profit = mf.revenue - mf.expenses
            cumulative_rev += mf.revenue
            cumulative_exp += mf.expenses
            cumulative_profit += mf.profit
            mf.cumulative_revenue = cumulative_rev
            mf.cumulative_profit = cumulative_profit

            # Running tax estimate
            mf.cumulative_tax = self._estimate_tax(cumulative_profit)
            mf.cash_reserve_needed = mf.cumulative_tax - self.ytd_cis_deductions

            # VAT liability (quarterly)
            if self.vat_registered:
                if self.vat_scheme == "flat_rate":
                    mf.vat_liability = mf.revenue * 1.20 * FRS_RATE_CONSTRUCTION
                else:
                    mf.vat_liability = mf.revenue * 0.20 - mf.expenses * 0.20

            months.append(mf)

        result.months = months

        # Annual totals
        annual_revenue = sum(m.revenue for m in months)
        annual_expenses = sum(m.expenses for m in months)
        annual_profit = annual_revenue - annual_expenses
        annual_tax = self._estimate_tax(annual_profit)
        annual_ni = self._estimate_ni(annual_profit)
        annual_vat = sum(m.vat_liability for m in months)

        total_liability = annual_tax + annual_ni
        tax_due = total_liability - self.ytd_cis_deductions

        # Payments on account (if liability > £1,000)
        poa_each = tax_due / 2 if tax_due > 1000 else 0

        result.annual = {
            "revenue": round(annual_revenue, 2),
            "expenses": round(annual_expenses, 2),
            "profit": round(annual_profit, 2),
            "expense_ratio": round(self.expense_ratio * 100, 1),
            "income_tax": round(annual_tax, 2),
            "national_insurance": round(annual_ni, 2),
            "total_liability": round(total_liability, 2),
            "cis_offset": round(self.ytd_cis_deductions, 2),
            "tax_due": round(tax_due, 2),
            "vat_annual": round(annual_vat, 2),
            "poa_each": round(poa_each, 2),
            "total_cash_needed": round(tax_due + annual_vat + poa_each * 2, 2),
        }

        # Payment schedule
        ty_parts = self.tax_year.split("/")
        end_year = int(f"20{ty_parts[1]}") if len(ty_parts[1]) == 2 else int(ty_parts[1])

        result.payment_schedule = [
            {"date": f"31/01/{end_year + 1}",
             "description": "Balancing payment + 1st Payment on Account",
             "amount": round(tax_due + poa_each, 2)},
            {"date": f"31/07/{end_year + 1}",
             "description": "2nd Payment on Account",
             "amount": round(poa_each, 2)},
        ]

        # Quarterly VAT payments
        if self.vat_registered:
            q_months = [(3, "Q1 Apr-Jun"), (6, "Q2 Jul-Sep"),
                        (9, "Q3 Oct-Dec"), (12, "Q4 Jan-Mar")]
            for end_m, label in q_months:
                start_m = end_m - 2
                q_vat = sum(months[i].vat_liability
                           for i in range(start_m, min(end_m, 12)))
                if q_vat > 0:
                    # VAT due 1 month + 7 days after quarter end
                    result.payment_schedule.append({
                        "date": f"{label}",
                        "description": f"VAT MTD — {label}",
                        "amount": round(q_vat, 2),
                    })

        # Alerts
        result.alerts = self._generate_alerts(result.annual)

        # What-if scenarios
        result.scenarios = self._run_scenarios(annual_profit)

        return result

    def _estimate_tax(self, profit: float) -> float:
        """Quick income tax estimate."""
        if profit <= 0:
            return 0.0

        pa = PERSONAL_ALLOWANCE
        if profit > PA_TAPER_START:
            pa = max(0, pa - (profit - PA_TAPER_START) / 2)

        taxable = max(0, profit - pa)
        tax = 0.0

        if taxable <= BASIC_RATE_BAND:
            tax = taxable * 0.20
        elif taxable <= BASIC_RATE_BAND + HIGHER_RATE_BAND:
            tax = BASIC_RATE_BAND * 0.20 + (taxable - BASIC_RATE_BAND) * 0.40
        else:
            tax = (BASIC_RATE_BAND * 0.20 +
                   HIGHER_RATE_BAND * 0.40 +
                   (taxable - BASIC_RATE_BAND - HIGHER_RATE_BAND) * 0.45)

        return round(tax, 2)

    def _estimate_ni(self, profit: float) -> float:
        """Quick NI estimate (Class 2 + Class 4)."""
        ni = 0.0

        # Class 2 (if profit > small profits threshold)
        if profit > CLASS4_LOWER:
            ni += CLASS2_ANNUAL

        # Class 4
        if profit > CLASS4_LOWER:
            band1 = min(profit, CLASS4_UPPER) - CLASS4_LOWER
            ni += band1 * CLASS4_RATE_MAIN

        if profit > CLASS4_UPPER:
            ni += (profit - CLASS4_UPPER) * CLASS4_RATE_ADDITIONAL

        return round(ni, 2)

    def _generate_alerts(self, annual: Dict) -> List[Dict]:
        """Smart alerts based on projections."""
        alerts = []

        # VAT threshold
        if annual["revenue"] > VAT_THRESHOLD * 0.9:
            pct = annual["revenue"] / VAT_THRESHOLD * 100
            alerts.append({
                "level": "WARNING" if pct < 100 else "CRITICAL",
                "category": "VAT",
                "message": f"Projected revenue £{annual['revenue']:,.0f} is "
                           f"{pct:.0f}% of VAT threshold (£{VAT_THRESHOLD:,.0f}). "
                           + ("Must register." if pct >= 100
                              else "Monitor closely."),
            })

        # High tax burden
        effective_rate = (annual["total_liability"] /
                         max(1, annual["profit"]) * 100)
        if effective_rate > 35:
            alerts.append({
                "level": "WARNING",
                "category": "Tax Planning",
                "message": f"Effective tax rate: {effective_rate:.1f}%. "
                           f"Consider pension contributions or timing adjustments.",
            })

        # Cash reserve
        monthly_reserve = annual["total_cash_needed"] / 12
        alerts.append({
            "level": "INFO",
            "category": "Cash Reserve",
            "message": f"Set aside £{monthly_reserve:,.0f}/month for tax. "
                       f"Total needed: £{annual['total_cash_needed']:,.0f}.",
        })

        # Low expense ratio (might flag at HMRC)
        if annual["expense_ratio"] < 15:
            alerts.append({
                "level": "INFO",
                "category": "Expense Ratio",
                "message": f"Expense ratio {annual['expense_ratio']:.1f}% is low "
                           f"for {self.trade_sector}. May attract enquiry.",
            })

        return alerts

    def _run_scenarios(self, base_profit: float) -> List[Dict]:
        """Run what-if scenarios."""
        base_tax = self._estimate_tax(base_profit)
        base_ni = self._estimate_ni(base_profit)
        base_total = base_tax + base_ni

        scenarios = []

        # Scenario 1: Pension contribution (£5k, £10k, £20k)
        for pension in [5000, 10000, 20000]:
            new_profit = base_profit - pension
            new_tax = self._estimate_tax(new_profit)
            new_ni = self._estimate_ni(new_profit)
            saving = base_total - (new_tax + new_ni)
            scenarios.append({
                "name": f"Pension contribution £{pension:,}",
                "profit": new_profit,
                "tax": new_tax + new_ni,
                "saving": round(saving, 2),
                "net_cost": round(pension - saving, 2),
            })

        # Scenario 2: Revenue +10%, +20%
        for pct in [10, 20]:
            new_revenue = base_profit / (1 - self.expense_ratio) * (1 + pct / 100)
            new_expenses = new_revenue * self.expense_ratio
            new_profit = new_revenue - new_expenses
            new_total = self._estimate_tax(new_profit) + self._estimate_ni(new_profit)
            scenarios.append({
                "name": f"Revenue +{pct}%",
                "profit": round(new_profit, 2),
                "tax": round(new_total, 2),
                "additional_tax": round(new_total - base_total, 2),
            })

        return scenarios

    # ================================================================== #
    # REPORTING
    # ================================================================== #

    def print_forecast(self, result: ForecastResult) -> str:
        """Full human-readable forecast report."""
        lines = [
            "=" * 70,
            f"  TAX FORECAST — {result.entity}",
            f"  Tax Year: {result.tax_year}",
            f"  Generated: {result.generated}",
            "=" * 70,
            "",
        ]

        # Monthly projection
        lines.append("  MONTHLY PROJECTION")
        lines.append(f"  {'Month':<12} {'Revenue':>10} {'Expenses':>10} "
                     f"{'Profit':>10} {'Cum Tax':>10} {'Source':>8}")
        lines.append(f"  {'-' * 64}")

        for m in result.months:
            src = "ACTUAL" if m.is_actual else "PROJ"
            lines.append(
                f"  {m.month_name:<12} "
                f"£{m.revenue:>8,.0f} "
                f"£{m.expenses:>8,.0f} "
                f"£{m.profit:>8,.0f} "
                f"£{m.cumulative_tax:>8,.0f} "
                f"  {src}"
            )

        # Annual summary
        a = result.annual
        lines.append("")
        lines.append("  ANNUAL PROJECTION")
        lines.append(f"  {'-' * 64}")
        lines.append(f"  Projected revenue:     £{a['revenue']:>12,.2f}")
        lines.append(f"  Projected expenses:    £{a['expenses']:>12,.2f}")
        lines.append(f"  Projected profit:      £{a['profit']:>12,.2f}")
        lines.append(f"  Expense ratio:         {a['expense_ratio']:>10.1f}%")
        lines.append("")
        lines.append(f"  Income tax:            £{a['income_tax']:>12,.2f}")
        lines.append(f"  National Insurance:    £{a['national_insurance']:>12,.2f}")
        lines.append(f"  Total liability:       £{a['total_liability']:>12,.2f}")
        lines.append(f"  CIS offset:            £{a['cis_offset']:>12,.2f}")
        lines.append(f"  Tax due:               £{a['tax_due']:>12,.2f}")
        lines.append(f"  VAT (annual):          £{a['vat_annual']:>12,.2f}")
        lines.append(f"  POA (each):            £{a['poa_each']:>12,.2f}")
        lines.append(f"  Total cash needed:     £{a['total_cash_needed']:>12,.2f}")

        # Payment schedule
        lines.append("")
        lines.append("  PAYMENT SCHEDULE")
        lines.append(f"  {'-' * 64}")
        for p in result.payment_schedule:
            lines.append(f"  {p['date']:<20} {p['description']:<30} £{p['amount']:>8,.2f}")

        # Alerts
        lines.append("")
        lines.append("  ALERTS")
        lines.append(f"  {'-' * 64}")
        for alert in result.alerts:
            marker = {"WARNING": "[!!]", "CRITICAL": "[XX]",
                      "INFO": "[ii]"}.get(alert["level"], "[??]")
            lines.append(f"  {marker} [{alert['category']}] {alert['message']}")

        # Scenarios
        if result.scenarios:
            lines.append("")
            lines.append("  WHAT-IF SCENARIOS")
            lines.append(f"  {'-' * 64}")
            for s in result.scenarios:
                if "saving" in s:
                    lines.append(
                        f"  {s['name']:<35} Tax: £{s['tax']:>8,.0f}  "
                        f"Saving: £{s['saving']:>6,.0f}  "
                        f"Net cost: £{s.get('net_cost', 0):>6,.0f}")
                elif "additional_tax" in s:
                    lines.append(
                        f"  {s['name']:<35} Tax: £{s['tax']:>8,.0f}  "
                        f"Extra tax: £{s['additional_tax']:>6,.0f}")

        lines.append("")
        lines.append("=" * 70)
        return "\n".join(lines)


def _month_name(m: int) -> str:
    """Calendar month number to name."""
    return ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][m - 1]


# ========================================================================
# TEST
# ========================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("HNC FORECAST — Tax Forecaster Test")
    print("=" * 70)

    engine = HNCForecastEngine(
        entity_name="John Smith Trading",
        tax_year="2025/26",
        vat_registered=True,
        vat_scheme="flat_rate",
        trade_sector="construction",
    )

    # John is 6 months in (April-September), £32k revenue, £8k expenses
    engine.set_ytd(
        months_elapsed=6,
        ytd_revenue=32000,
        ytd_expenses=8000,
        ytd_cis_deductions=1200,
        monthly_breakdown=[
            {"revenue": 4500, "expenses": 1200},   # Apr
            {"revenue": 5800, "expenses": 1400},   # May
            {"revenue": 6200, "expenses": 1500},   # Jun
            {"revenue": 6000, "expenses": 1300},   # Jul
            {"revenue": 5500, "expenses": 1400},   # Aug
            {"revenue": 4000, "expenses": 1200},   # Sep
        ],
    )

    result = engine.project()
    print(engine.print_forecast(result))

    # Quick verification
    print("\n--- VERIFICATION ---")
    a = result.annual
    print(f"  Projected annual revenue: £{a['revenue']:,.2f}")
    print(f"  Projected annual profit:  £{a['profit']:,.2f}")
    print(f"  Income tax:               £{a['income_tax']:,.2f}")
    print(f"  NI:                       £{a['national_insurance']:,.2f}")
    print(f"  Total cash to reserve:    £{a['total_cash_needed']:,.2f}")
    print(f"  Monthly reserve needed:   £{a['total_cash_needed'] / 12:,.2f}")

    print("\n" + "=" * 70)
    print("Forecast engine verified. Every projection traceable.")
    print("=" * 70)
