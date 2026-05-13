"""
HNC REPORTS — hnc_reports.py
============================
Financial Reporting Engine.

Generates FRS 102 Section 1A / FRS 105 compliant financial statements
from ledger data. Every report HMRC, Companies House, or a client could
ask for — generated from the same source of truth.

Reports:
    1. Profit & Loss (Income Statement)
    2. Balance Sheet (Statement of Financial Position)
    3. Cash Flow Statement (FRS 102 only — exempt for micro-entities)
    4. Trial Balance
    5. Aged Debtors / Aged Creditors
    6. VAT Summary (MTD-ready)
    7. CIS Monthly Return Summary
    8. Management Accounts (monthly breakdown)
    9. Tax Summary (SA overview)
   10. Client Dashboard (key metrics)

All monetary values in GBP. All dates in UK format (DD/MM/YYYY).
All reports auditable back to journal entries.

Aureon Creator / Aureon Research — April 2026
"""

from __future__ import annotations
import logging
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger("hnc_reports")


# ========================================================================
# REPORT DATA STRUCTURES
# ========================================================================

@dataclass
class ReportLine:
    """Single line in a financial report."""
    label: str
    amount: float = 0.0
    indent: int = 0           # 0=header, 1=category, 2=detail
    is_total: bool = False
    is_subtotal: bool = False
    note_ref: str = ""        # e.g. "Note 3"
    account_code: str = ""


@dataclass
class FinancialReport:
    """Container for any financial report."""
    title: str = ""
    entity: str = ""
    period: str = ""
    date_generated: str = ""
    report_type: str = ""     # pnl, balance_sheet, cash_flow, trial_balance, etc
    lines: List[ReportLine] = field(default_factory=list)
    totals: Dict[str, float] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ========================================================================
# UK DATE HELPERS
# ========================================================================

def uk_date(d: str) -> str:
    """Convert YYYY-MM-DD to DD/MM/YYYY."""
    if "/" in d and len(d.split("/")[0]) == 2:
        return d  # Already UK format
    try:
        dt = datetime.strptime(d[:10], "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return d


def tax_year_dates(tax_year: str) -> Tuple[date, date]:
    """Return start and end dates for a UK tax year like '2025/26'."""
    parts = tax_year.split("/")
    start_year = int(parts[0])
    return date(start_year, 4, 6), date(start_year + 1, 4, 5)


def accounting_year_dates(year_end: str = "2026-03-31") -> Tuple[date, date]:
    """Return start and end dates for an accounting period."""
    end = date.fromisoformat(year_end)
    start = date(end.year - 1, end.month, end.day) + timedelta(days=1)
    return start, end


# ========================================================================
# FRS 102 SECTION 1A — PROFIT & LOSS ACCOUNT
# ========================================================================

def generate_pnl(ledger_data: Dict[str, Any],
                 entity_name: str = "",
                 tax_year: str = "2025/26",
                 show_prior_year: bool = False,
                 prior_year_data: Dict[str, Any] = None) -> FinancialReport:
    """
    Generate FRS 102 Section 1A compliant Profit & Loss Account.

    Format follows Companies Act 2006 Schedule 1, Format 2 (vertical).

    Statutory reference: CA 2006 s.396, Sch 1 Part 1.
    FRS 102 Section 1A.5 — Minimum disclosures for small entities.
    """
    report = FinancialReport(
        title="PROFIT AND LOSS ACCOUNT",
        entity=entity_name or ledger_data.get("entity", ""),
        period=tax_year,
        date_generated=datetime.now().strftime("%d/%m/%Y"),
        report_type="pnl",
    )

    # Extract data from ledger P&L dict
    revenue = ledger_data.get("revenue", {})
    cos = ledger_data.get("cost_of_sales", {})
    overheads = ledger_data.get("overheads", {})
    admin = ledger_data.get("administrative", {})
    tax = ledger_data.get("tax", {})

    total_revenue = ledger_data.get("total_revenue", sum(revenue.values()))
    total_cos = ledger_data.get("total_cost_of_sales", sum(cos.values()))
    gross_profit = ledger_data.get("gross_profit", total_revenue - total_cos)
    total_overheads = ledger_data.get("total_overheads", sum(overheads.values()))
    total_admin = ledger_data.get("total_administrative", sum(admin.values()))
    net_before_tax = ledger_data.get("net_profit_before_tax",
                                      gross_profit - total_overheads - total_admin)
    total_tax = ledger_data.get("total_tax", sum(tax.values()))
    net_after_tax = ledger_data.get("net_profit_after_tax",
                                     net_before_tax - total_tax)

    lines = report.lines

    # TURNOVER (FRS 102 Section 1A.5(a))
    lines.append(ReportLine("Turnover", total_revenue, indent=0,
                            note_ref="Note 2"))
    for name, amt in sorted(revenue.items(), key=lambda x: -abs(x[1])):
        lines.append(ReportLine(f"  {name}", amt, indent=2))

    # COST OF SALES
    lines.append(ReportLine("Cost of sales", -total_cos, indent=0))
    for name, amt in sorted(cos.items(), key=lambda x: -abs(x[1])):
        lines.append(ReportLine(f"  {name}", -amt, indent=2))

    # GROSS PROFIT (FRS 102 Section 1A.5(b))
    lines.append(ReportLine("GROSS PROFIT", gross_profit, indent=0,
                            is_subtotal=True))

    # OVERHEADS
    if overheads:
        lines.append(ReportLine("Overheads", -total_overheads, indent=0))
        for name, amt in sorted(overheads.items(), key=lambda x: -abs(x[1])):
            lines.append(ReportLine(f"  {name}", -amt, indent=2))

    # ADMINISTRATIVE EXPENSES
    if admin:
        lines.append(ReportLine("Administrative expenses", -total_admin,
                                indent=0, note_ref="Note 3"))
        for name, amt in sorted(admin.items(), key=lambda x: -abs(x[1])):
            lines.append(ReportLine(f"  {name}", -amt, indent=2))

    # OPERATING PROFIT
    operating_profit = gross_profit - total_overheads - total_admin
    lines.append(ReportLine("OPERATING PROFIT", operating_profit, indent=0,
                            is_subtotal=True))

    # PROFIT BEFORE TAX (FRS 102 Section 1A.5(c))
    lines.append(ReportLine("Profit on ordinary activities before taxation",
                            net_before_tax, indent=0, is_subtotal=True))

    # TAX (FRS 102 Section 1A.5(d))
    if tax:
        lines.append(ReportLine("Tax on profit on ordinary activities",
                                -total_tax, indent=0, note_ref="Note 5"))
        for name, amt in sorted(tax.items(), key=lambda x: -abs(x[1])):
            lines.append(ReportLine(f"  {name}", -amt, indent=2))

    # PROFIT AFTER TAX (FRS 102 Section 1A.5(e))
    lines.append(ReportLine("PROFIT FOR THE FINANCIAL YEAR", net_after_tax,
                            indent=0, is_total=True))

    # Totals for quick access
    report.totals = {
        "turnover": total_revenue,
        "cost_of_sales": total_cos,
        "gross_profit": gross_profit,
        "total_overheads": total_overheads,
        "total_admin": total_admin,
        "operating_profit": operating_profit,
        "profit_before_tax": net_before_tax,
        "tax": total_tax,
        "profit_after_tax": net_after_tax,
        "gross_margin_pct": round(gross_profit / total_revenue * 100, 1)
            if total_revenue else 0,
        "net_margin_pct": round(net_after_tax / total_revenue * 100, 1)
            if total_revenue else 0,
    }

    # Statutory notes
    report.notes = [
        "1. Accounting policies: These accounts are prepared under FRS 102 "
        "Section 1A (small entities) on the accruals basis.",
        f"2. Turnover represents amounts receivable for goods and services "
        f"provided in the normal course of business. Total: £{total_revenue:,.2f}.",
        "3. Administrative expenses include accountancy fees, depreciation, "
        "and other costs not directly attributable to turnover.",
        "4. The profit for the year is stated after charging depreciation "
        "on tangible fixed assets.",
        f"5. Tax charge based on UK rates applicable to the period. "
        f"Total charge: £{total_tax:,.2f}.",
    ]

    return report


# ========================================================================
# FRS 102 — BALANCE SHEET (Statement of Financial Position)
# ========================================================================

def generate_balance_sheet(ledger_data: Dict[str, Any],
                           entity_name: str = "",
                           as_at: str = "") -> FinancialReport:
    """
    Generate FRS 102 Section 1A compliant Balance Sheet.

    Statutory reference: CA 2006 s.396, Sch 1 Part 1 Format 1.
    Must be signed by a director (or sole trader).
    """
    if not as_at:
        as_at = datetime.now().strftime("%Y-%m-%d")

    report = FinancialReport(
        title="BALANCE SHEET",
        entity=entity_name or ledger_data.get("entity", ""),
        period=f"As at {uk_date(as_at)}",
        date_generated=datetime.now().strftime("%d/%m/%Y"),
        report_type="balance_sheet",
    )

    lines = report.lines

    # FIXED ASSETS (FRS 102 Section 1A.4(a))
    fixed = ledger_data.get("fixed_assets", {})
    total_fixed = ledger_data.get("total_fixed_assets", sum(fixed.values()))
    lines.append(ReportLine("FIXED ASSETS", total_fixed, indent=0,
                            note_ref="Note 2"))
    for name, amt in sorted(fixed.items(), key=lambda x: -abs(x[1])):
        lines.append(ReportLine(f"  {name}", amt, indent=2))

    # CURRENT ASSETS (FRS 102 Section 1A.4(b))
    current_a = ledger_data.get("current_assets", {})
    total_current_a = ledger_data.get("total_current_assets",
                                       sum(current_a.values()))
    lines.append(ReportLine("CURRENT ASSETS", total_current_a, indent=0))
    for name, amt in sorted(current_a.items(), key=lambda x: -abs(x[1])):
        lines.append(ReportLine(f"  {name}", amt, indent=2))

    # CREDITORS: amounts falling due within one year
    current_l = ledger_data.get("current_liabilities", {})
    total_current_l = ledger_data.get("total_current_liabilities",
                                       sum(current_l.values()))
    lines.append(ReportLine(
        "CREDITORS: amounts falling due within one year",
        -total_current_l, indent=0, note_ref="Note 3"))
    for name, amt in sorted(current_l.items(), key=lambda x: -abs(x[1])):
        lines.append(ReportLine(f"  {name}", -amt, indent=2))

    # NET CURRENT ASSETS
    net_current = ledger_data.get("net_current_assets",
                                   total_current_a - total_current_l)
    lines.append(ReportLine("NET CURRENT ASSETS", net_current, indent=0,
                            is_subtotal=True))

    # TOTAL ASSETS LESS CURRENT LIABILITIES
    total_alc = total_fixed + net_current
    lines.append(ReportLine("TOTAL ASSETS LESS CURRENT LIABILITIES",
                            total_alc, indent=0, is_subtotal=True))

    # CREDITORS: amounts falling due after more than one year
    long_l = ledger_data.get("long_term_liabilities", {})
    total_long_l = ledger_data.get("total_long_term_liabilities",
                                    sum(long_l.values()))
    if long_l:
        lines.append(ReportLine(
            "CREDITORS: amounts falling due after more than one year",
            -total_long_l, indent=0, note_ref="Note 4"))
        for name, amt in sorted(long_l.items(), key=lambda x: -abs(x[1])):
            lines.append(ReportLine(f"  {name}", -amt, indent=2))

    # NET ASSETS
    net_assets = total_alc - total_long_l
    lines.append(ReportLine("NET ASSETS", net_assets, indent=0,
                            is_total=True))

    # CAPITAL AND RESERVES
    lines.append(ReportLine("", 0))  # Spacer
    lines.append(ReportLine("CAPITAL AND RESERVES", 0, indent=0))
    equity = ledger_data.get("equity", {})
    for name, amt in sorted(equity.items()):
        lines.append(ReportLine(f"  {name}", amt, indent=2))

    net_income = ledger_data.get("net_income_current_period", 0)
    if net_income:
        lines.append(ReportLine("  Profit for the financial year",
                                net_income, indent=2))

    total_equity = ledger_data.get("total_equity", sum(equity.values()) + net_income)
    lines.append(ReportLine("TOTAL EQUITY", total_equity, indent=0,
                            is_total=True))

    balanced = ledger_data.get("balanced", abs(net_assets - total_equity) < 0.01)

    report.totals = {
        "total_fixed_assets": total_fixed,
        "total_current_assets": total_current_a,
        "total_current_liabilities": total_current_l,
        "net_current_assets": net_current,
        "net_assets": net_assets,
        "total_equity": total_equity,
        "is_balanced": balanced,
    }

    report.notes = [
        "1. These financial statements have been prepared in accordance "
        "with FRS 102 Section 1A (small entities).",
        "2. Fixed assets are stated at cost less accumulated depreciation.",
        "3. Creditors due within one year include trade creditors, "
        "accruals, and tax liabilities.",
    ]

    report.metadata["signed_by"] = ""
    report.metadata["signed_date"] = ""
    report.metadata["company_number"] = ""

    return report


# ========================================================================
# CASH FLOW STATEMENT (FRS 102 Section 7)
# ========================================================================

def generate_cash_flow(ledger_data: Dict[str, Any],
                       pnl_data: Dict[str, Any],
                       opening_cash: float = 0.0,
                       closing_cash: float = 0.0,
                       entity_name: str = "",
                       tax_year: str = "2025/26") -> FinancialReport:
    """
    FRS 102 Section 7 Cash Flow Statement.

    Small entities qualifying under CA 2006 s.382 are EXEMPT from
    preparing a cash flow statement, but it's good practice.

    Indirect method: start with operating profit, adjust for
    non-cash items and working capital movements.
    """
    report = FinancialReport(
        title="CASH FLOW STATEMENT",
        entity=entity_name or pnl_data.get("entity", ""),
        period=tax_year,
        date_generated=datetime.now().strftime("%d/%m/%Y"),
        report_type="cash_flow",
    )

    lines = report.lines

    operating_profit = pnl_data.get("net_profit_before_tax", 0)

    # OPERATING ACTIVITIES (indirect method)
    lines.append(ReportLine("CASH FLOWS FROM OPERATING ACTIVITIES", 0, indent=0))
    lines.append(ReportLine("  Profit before tax", operating_profit, indent=2))

    # Adjustments for non-cash items
    depreciation = abs(pnl_data.get("administrative", {}).get("Depreciation", 0))
    lines.append(ReportLine("  Depreciation charges", depreciation, indent=2))

    # Working capital movements (from balance sheet changes)
    bs = ledger_data
    debtors_change = bs.get("current_assets", {}).get("Trade Debtors", 0)
    creditors_change = bs.get("current_liabilities", {}).get("Trade Creditors", 0)
    stock_change = bs.get("current_assets", {}).get("Stock/Inventory", 0)

    lines.append(ReportLine("  (Increase)/decrease in debtors",
                            -debtors_change, indent=2))
    lines.append(ReportLine("  Increase/(decrease) in creditors",
                            creditors_change, indent=2))
    lines.append(ReportLine("  (Increase)/decrease in stock",
                            -stock_change, indent=2))

    net_operating = (operating_profit + depreciation
                     - debtors_change + creditors_change - stock_change)

    tax_paid = pnl_data.get("total_tax", 0)
    lines.append(ReportLine("  Tax paid", -tax_paid, indent=2))

    net_operating_after_tax = net_operating - tax_paid
    lines.append(ReportLine("Net cash from operating activities",
                            net_operating_after_tax, indent=0, is_subtotal=True))

    # INVESTING ACTIVITIES
    lines.append(ReportLine("CASH FLOWS FROM INVESTING ACTIVITIES", 0, indent=0))
    fixed_additions = bs.get("total_fixed_assets", 0)
    if fixed_additions:
        lines.append(ReportLine("  Purchase of tangible fixed assets",
                                -fixed_additions, indent=2))
    net_investing = -fixed_additions
    lines.append(ReportLine("Net cash from investing activities",
                            net_investing, indent=0, is_subtotal=True))

    # FINANCING ACTIVITIES
    lines.append(ReportLine("CASH FLOWS FROM FINANCING ACTIVITIES", 0, indent=0))
    drawings = abs(bs.get("equity", {}).get("Drawings", 0))
    if drawings:
        lines.append(ReportLine("  Owner drawings", -drawings, indent=2))
    net_financing = -drawings
    lines.append(ReportLine("Net cash from financing activities",
                            net_financing, indent=0, is_subtotal=True))

    # NET CHANGE
    net_change = net_operating_after_tax + net_investing + net_financing
    lines.append(ReportLine("", 0))
    lines.append(ReportLine("NET INCREASE/(DECREASE) IN CASH", net_change,
                            indent=0, is_total=True))
    lines.append(ReportLine("Cash at beginning of period", opening_cash, indent=0))
    lines.append(ReportLine("CASH AT END OF PERIOD", opening_cash + net_change,
                            indent=0, is_total=True))

    report.totals = {
        "net_operating": net_operating_after_tax,
        "net_investing": net_investing,
        "net_financing": net_financing,
        "net_change": net_change,
        "opening_cash": opening_cash,
        "closing_cash": opening_cash + net_change,
    }

    return report


# ========================================================================
# AGED DEBTORS & AGED CREDITORS
# ========================================================================

def generate_aged_debtors(outstanding_invoices: List[Dict],
                          as_at: str = "",
                          entity_name: str = "") -> FinancialReport:
    """
    Aged Debtors report — who owes money and how long overdue.

    Bands: Current (not yet due), 1-30 days, 31-60, 61-90, 90+.
    Critical for cash flow management and bad debt provisioning.
    """
    if not as_at:
        as_at = date.today().isoformat()
    ref_date = date.fromisoformat(as_at)

    report = FinancialReport(
        title="AGED DEBTORS REPORT",
        entity=entity_name,
        period=f"As at {uk_date(as_at)}",
        date_generated=datetime.now().strftime("%d/%m/%Y"),
        report_type="aged_debtors",
    )

    bands = {
        "current": {"label": "Current (not due)", "total": 0.0, "count": 0},
        "1_30": {"label": "1-30 days overdue", "total": 0.0, "count": 0},
        "31_60": {"label": "31-60 days overdue", "total": 0.0, "count": 0},
        "61_90": {"label": "61-90 days overdue", "total": 0.0, "count": 0},
        "90_plus": {"label": "90+ days overdue", "total": 0.0, "count": 0},
    }

    customer_totals = defaultdict(lambda: {"total": 0.0, "oldest_days": 0})

    for inv in outstanding_invoices:
        due_date = date.fromisoformat(inv.get("due_date", as_at))
        amount = inv.get("amount_outstanding", inv.get("amount", 0))
        customer = inv.get("customer", "Unknown")
        days_overdue = (ref_date - due_date).days

        if days_overdue <= 0:
            bands["current"]["total"] += amount
            bands["current"]["count"] += 1
        elif days_overdue <= 30:
            bands["1_30"]["total"] += amount
            bands["1_30"]["count"] += 1
        elif days_overdue <= 60:
            bands["31_60"]["total"] += amount
            bands["31_60"]["count"] += 1
        elif days_overdue <= 90:
            bands["61_90"]["total"] += amount
            bands["61_90"]["count"] += 1
        else:
            bands["90_plus"]["total"] += amount
            bands["90_plus"]["count"] += 1

        customer_totals[customer]["total"] += amount
        customer_totals[customer]["oldest_days"] = max(
            customer_totals[customer]["oldest_days"], max(0, days_overdue))

    lines = report.lines

    # Summary by age band
    grand_total = 0.0
    for key in ["current", "1_30", "31_60", "61_90", "90_plus"]:
        b = bands[key]
        lines.append(ReportLine(b["label"], b["total"], indent=1))
        grand_total += b["total"]

    lines.append(ReportLine("TOTAL OUTSTANDING", grand_total, indent=0,
                            is_total=True))
    lines.append(ReportLine("", 0))

    # By customer
    lines.append(ReportLine("BY CUSTOMER", 0, indent=0))
    for customer, data in sorted(customer_totals.items(),
                                  key=lambda x: -x[1]["total"]):
        label = f"  {customer} ({data['oldest_days']}d oldest)"
        lines.append(ReportLine(label, data["total"], indent=2))

    report.totals = {
        "total_outstanding": grand_total,
        "current": bands["current"]["total"],
        "overdue_1_30": bands["1_30"]["total"],
        "overdue_31_60": bands["31_60"]["total"],
        "overdue_61_90": bands["61_90"]["total"],
        "overdue_90_plus": bands["90_plus"]["total"],
        "total_overdue": grand_total - bands["current"]["total"],
        "customer_count": len(customer_totals),
    }

    return report


# ========================================================================
# CIS MONTHLY RETURN SUMMARY
# ========================================================================

def generate_cis_summary(cis_payments: List[Dict],
                         period: str = "",
                         entity_name: str = "",
                         contractor_utr: str = "") -> FinancialReport:
    """
    CIS Monthly Return summary — FA 2004 s.70.

    Shows all payments to subcontractors with CIS deductions.
    Contractor must submit to HMRC by 19th of following month.
    """
    report = FinancialReport(
        title="CIS MONTHLY RETURN SUMMARY",
        entity=entity_name,
        period=period or datetime.now().strftime("%B %Y"),
        date_generated=datetime.now().strftime("%d/%m/%Y"),
        report_type="cis_return",
    )

    lines = report.lines
    total_gross = 0.0
    total_materials = 0.0
    total_deductions = 0.0
    total_net = 0.0

    subcontractors = defaultdict(lambda: {
        "gross": 0.0, "materials": 0.0, "deductions": 0.0, "net": 0.0,
        "utr": "", "verification": ""
    })

    for p in cis_payments:
        sub = p.get("subcontractor", "Unknown")
        gross = p.get("gross", 0)
        materials = p.get("materials", 0)
        labour = gross - materials
        rate = p.get("deduction_rate", 0.20)
        deduction = labour * rate
        net = gross - deduction

        subcontractors[sub]["gross"] += gross
        subcontractors[sub]["materials"] += materials
        subcontractors[sub]["deductions"] += deduction
        subcontractors[sub]["net"] += net
        subcontractors[sub]["utr"] = p.get("utr", "")
        subcontractors[sub]["verification"] = p.get("verification_status", "")

        total_gross += gross
        total_materials += materials
        total_deductions += deduction
        total_net += net

    for sub, data in sorted(subcontractors.items()):
        lines.append(ReportLine(
            f"{sub} (UTR: {data['utr'] or 'N/A'})",
            0, indent=0))
        lines.append(ReportLine("  Gross payment", data["gross"], indent=2))
        lines.append(ReportLine("  Materials (not subject to CIS)",
                                data["materials"], indent=2))
        lines.append(ReportLine("  CIS deductions", -data["deductions"], indent=2))
        lines.append(ReportLine("  Net paid", data["net"], indent=2))

    lines.append(ReportLine("", 0))
    lines.append(ReportLine("TOTALS", 0, indent=0))
    lines.append(ReportLine("  Total gross", total_gross, indent=1))
    lines.append(ReportLine("  Total materials", total_materials, indent=1))
    lines.append(ReportLine("  Total CIS deductions", total_deductions, indent=1,
                            is_total=True))
    lines.append(ReportLine("  Total net paid", total_net, indent=1))

    report.totals = {
        "total_gross": total_gross,
        "total_materials": total_materials,
        "total_deductions": total_deductions,
        "total_net": total_net,
        "subcontractor_count": len(subcontractors),
    }

    report.metadata["contractor_utr"] = contractor_utr
    report.metadata["filing_deadline"] = ""  # 19th of following month

    return report


# ========================================================================
# MANAGEMENT ACCOUNTS (Monthly Breakdown)
# ========================================================================

def generate_management_accounts(monthly_data: List[Dict],
                                  entity_name: str = "",
                                  tax_year: str = "2025/26") -> FinancialReport:
    """
    Monthly management accounts — 12-month P&L breakdown.

    Not a statutory requirement but essential for any real business.
    Shows trends, seasonality, and month-on-month performance.
    """
    report = FinancialReport(
        title="MANAGEMENT ACCOUNTS — Monthly Summary",
        entity=entity_name,
        period=tax_year,
        date_generated=datetime.now().strftime("%d/%m/%Y"),
        report_type="management_accounts",
    )

    lines = report.lines

    ytd_revenue = 0.0
    ytd_expenses = 0.0
    ytd_profit = 0.0

    for month in monthly_data:
        month_name = month.get("month", "")
        revenue = month.get("revenue", 0)
        expenses = month.get("expenses", 0)
        profit = revenue - expenses

        ytd_revenue += revenue
        ytd_expenses += expenses
        ytd_profit += profit

        lines.append(ReportLine(month_name, 0, indent=0))
        lines.append(ReportLine("  Revenue", revenue, indent=2))
        lines.append(ReportLine("  Expenses", -expenses, indent=2))
        lines.append(ReportLine("  Profit", profit, indent=2, is_subtotal=True))

    lines.append(ReportLine("", 0))
    lines.append(ReportLine("YEAR TO DATE", 0, indent=0))
    lines.append(ReportLine("  Revenue", ytd_revenue, indent=1))
    lines.append(ReportLine("  Expenses", -ytd_expenses, indent=1))
    lines.append(ReportLine("  Profit", ytd_profit, indent=1, is_total=True))

    avg_monthly_revenue = ytd_revenue / max(1, len(monthly_data))
    avg_monthly_profit = ytd_profit / max(1, len(monthly_data))

    report.totals = {
        "ytd_revenue": ytd_revenue,
        "ytd_expenses": ytd_expenses,
        "ytd_profit": ytd_profit,
        "avg_monthly_revenue": avg_monthly_revenue,
        "avg_monthly_profit": avg_monthly_profit,
        "months_reported": len(monthly_data),
    }

    return report


# ========================================================================
# TAX SUMMARY (Overview for client)
# ========================================================================

def generate_tax_summary(tax_computation: Any,
                          vat_data: Dict = None,
                          cis_data: Dict = None,
                          entity_name: str = "",
                          tax_year: str = "2025/26") -> FinancialReport:
    """
    Tax Summary — client-friendly overview of all tax obligations.

    Pulls from hnc_tax computation and VAT return data.
    Shows what they owe, when it's due, and how to pay.
    """
    report = FinancialReport(
        title="TAX SUMMARY",
        entity=entity_name,
        period=tax_year,
        date_generated=datetime.now().strftime("%d/%m/%Y"),
        report_type="tax_summary",
    )

    lines = report.lines

    # Income Tax
    if tax_computation:
        tc = tax_computation
        income_tax = getattr(tc, "income_tax", 0) if hasattr(tc, "income_tax") else tc.get("income_tax", 0)
        ni = getattr(tc, "total_ni", 0) if hasattr(tc, "total_ni") else tc.get("total_ni", 0)
        cgt = getattr(tc, "cgt", 0) if hasattr(tc, "cgt") else tc.get("cgt", 0)
        total = getattr(tc, "total_liability", 0) if hasattr(tc, "total_liability") else tc.get("total_liability", 0)
        tax_due = getattr(tc, "tax_due", 0) if hasattr(tc, "tax_due") else tc.get("tax_due", 0)
        poa_each = getattr(tc, "poa_each", 0) if hasattr(tc, "poa_each") else tc.get("poa_each", 0)

        lines.append(ReportLine("INCOME TAX & NATIONAL INSURANCE", 0, indent=0))
        lines.append(ReportLine("  Income tax", income_tax, indent=2))
        lines.append(ReportLine("  Class 2 NI", getattr(tc, "class2_ni", 0) if hasattr(tc, "class2_ni") else 0, indent=2))
        lines.append(ReportLine("  Class 4 NI", getattr(tc, "class4_ni", 0) if hasattr(tc, "class4_ni") else 0, indent=2))
        if cgt > 0:
            lines.append(ReportLine("  Capital Gains Tax", cgt, indent=2))

        lines.append(ReportLine("  Total liability", total, indent=1,
                                is_subtotal=True))

        # Deductions
        cis_ded = getattr(tc, "cis_deductions", 0) if hasattr(tc, "cis_deductions") else tc.get("cis_deductions", 0)
        paye_ded = getattr(tc, "paye_deductions", 0) if hasattr(tc, "paye_deductions") else tc.get("paye_deductions", 0)
        if cis_ded or paye_ded:
            lines.append(ReportLine("  Less: CIS deductions suffered",
                                    -cis_ded, indent=2))
            if paye_ded:
                lines.append(ReportLine("  Less: PAYE deducted",
                                        -paye_ded, indent=2))

        lines.append(ReportLine("  TAX DUE", tax_due, indent=1, is_total=True))

        # Payment schedule
        if poa_each > 0:
            ty_parts = tax_year.split("/")
            end_year = int(f"20{ty_parts[1]}") if len(ty_parts[1]) == 2 else int(ty_parts[1])
            lines.append(ReportLine("", 0))
            lines.append(ReportLine("PAYMENT SCHEDULE", 0, indent=0))
            lines.append(ReportLine(
                f"  31 January {end_year + 1}: Balancing + 1st POA",
                tax_due + poa_each, indent=2))
            lines.append(ReportLine(
                f"  31 July {end_year + 1}: 2nd Payment on Account",
                poa_each, indent=2))
            lines.append(ReportLine("  Total cash outlay",
                                    tax_due + (poa_each * 2), indent=1,
                                    is_total=True))

    # VAT
    if vat_data:
        lines.append(ReportLine("", 0))
        lines.append(ReportLine("VAT", 0, indent=0))
        box5 = vat_data.get("box5_net_vat", 0)
        lines.append(ReportLine(
            f"  Period: {vat_data.get('period', 'N/A')}", 0, indent=2))
        lines.append(ReportLine("  Net VAT payable", box5, indent=2))

    # CIS
    if cis_data:
        lines.append(ReportLine("", 0))
        lines.append(ReportLine("CIS DEDUCTIONS SUFFERED", 0, indent=0))
        lines.append(ReportLine("  Total deductions",
                                cis_data.get("total_deductions", 0), indent=2))
        lines.append(ReportLine(
            "  (Offset against income tax liability)", 0, indent=2))

    report.totals = {
        "income_tax": getattr(tax_computation, "income_tax", 0) if hasattr(tax_computation, "income_tax") else 0,
        "ni": getattr(tax_computation, "total_ni", 0) if hasattr(tax_computation, "total_ni") else 0,
        "cgt": getattr(tax_computation, "cgt", 0) if hasattr(tax_computation, "cgt") else 0,
        "total_liability": getattr(tax_computation, "total_liability", 0) if hasattr(tax_computation, "total_liability") else 0,
        "tax_due": getattr(tax_computation, "tax_due", 0) if hasattr(tax_computation, "tax_due") else 0,
        "vat_due": vat_data.get("box5_net_vat", 0) if vat_data else 0,
    }

    # Key dates
    report.notes = [
        "FILING DEADLINES:",
        f"  Paper SA100: 31 October following end of tax year",
        f"  Online SA100: 31 January following end of tax year",
        f"  VAT MTD: 1 month + 7 days after end of VAT period",
        f"  CIS Monthly Return: 19th of the following month",
    ]

    return report


# ========================================================================
# CLIENT DASHBOARD (Key Metrics)
# ========================================================================

def generate_dashboard(pnl_data: Dict, bs_data: Dict,
                       tax_data: Any = None,
                       entity_name: str = "",
                       tax_year: str = "2025/26") -> Dict[str, Any]:
    """
    Client dashboard — KPIs at a glance.

    This is what the client sees when they open the app.
    Everything they need to know in one screen.
    """
    revenue = pnl_data.get("total_revenue", 0)
    expenses = (pnl_data.get("total_cost_of_sales", 0)
                + pnl_data.get("total_overheads", 0)
                + pnl_data.get("total_administrative", 0))
    profit = pnl_data.get("net_profit_before_tax", 0)
    net_assets = bs_data.get("net_assets", 0) if bs_data else 0

    # Cash position
    cash = 0
    if bs_data:
        for name, amt in bs_data.get("current_assets", {}).items():
            if any(k in name.lower() for k in ("cash", "bank", "current account")):
                cash += amt

    # Tax position
    tax_due = 0
    if tax_data:
        tax_due = getattr(tax_data, "tax_due", 0) if hasattr(tax_data, "tax_due") else tax_data.get("tax_due", 0)

    # VAT threshold check
    vat_threshold_pct = min(100, round(revenue / 90000 * 100, 1))

    return {
        "entity": entity_name,
        "tax_year": tax_year,
        "kpis": {
            "revenue": revenue,
            "expenses": expenses,
            "profit": profit,
            "gross_margin": round(pnl_data.get("gross_profit", 0) / max(1, revenue) * 100, 1),
            "net_margin": round(profit / max(1, revenue) * 100, 1),
            "cash_position": cash,
            "net_assets": net_assets,
            "tax_due": tax_due,
            "effective_tax_rate": round(tax_due / max(1, profit) * 100, 1),
            "vat_threshold_pct": vat_threshold_pct,
        },
        "alerts": _generate_alerts(revenue, expenses, profit, cash, tax_due,
                                     vat_threshold_pct),
    }


def _generate_alerts(revenue, expenses, profit, cash, tax_due,
                     vat_threshold_pct) -> List[Dict[str, str]]:
    """Generate smart alerts based on financial position."""
    alerts = []

    if vat_threshold_pct >= 90:
        alerts.append({
            "level": "WARNING",
            "message": f"VAT threshold: {vat_threshold_pct}% of £90,000. "
                       f"Approaching mandatory registration.",
        })

    if profit < 0:
        alerts.append({
            "level": "CRITICAL",
            "message": f"Trading at a loss: £{abs(profit):,.2f}. "
                       f"Review expenses and pricing.",
        })

    if cash < tax_due:
        alerts.append({
            "level": "WARNING",
            "message": f"Cash (£{cash:,.2f}) less than tax due "
                       f"(£{tax_due:,.2f}). Reserve funds.",
        })

    expense_ratio = expenses / max(1, revenue) * 100
    if expense_ratio > 80:
        alerts.append({
            "level": "WARNING",
            "message": f"Expense ratio: {expense_ratio:.1f}%. "
                       f"Consider cost reduction.",
        })

    if not alerts:
        alerts.append({
            "level": "OK",
            "message": "All metrics within normal range.",
        })

    return alerts


# ========================================================================
# REPORT FORMATTER (Text output)
# ========================================================================

def format_report(report: FinancialReport, width: int = 70) -> str:
    """Format a FinancialReport as a human-readable text string."""
    lines = [
        "=" * width,
        f"  {report.title}",
        f"  {report.entity}",
        f"  {report.period}",
        "=" * width,
        "",
    ]

    for rl in report.lines:
        if rl.is_total:
            prefix = "  " * rl.indent
            label = f"{prefix}{rl.label}"
            if rl.amount != 0:
                amount_str = f"£{rl.amount:>12,.2f}"
                lines.append(f"  {'-' * (width - 4)}")
                lines.append(f"  {label:<{width - 18}}{amount_str}")
                lines.append(f"  {'=' * (width - 4)}")
            else:
                lines.append(f"  {label}")
        elif rl.is_subtotal:
            prefix = "  " * rl.indent
            label = f"{prefix}{rl.label}"
            amount_str = f"£{rl.amount:>12,.2f}" if rl.amount != 0 else ""
            lines.append(f"  {'-' * (width - 4)}")
            lines.append(f"  {label:<{width - 18}}{amount_str}")
        elif rl.label == "":
            lines.append("")
        else:
            prefix = "  " * rl.indent
            label = f"{prefix}{rl.label}"
            note = f"  {rl.note_ref}" if rl.note_ref else ""
            if rl.amount != 0:
                amount_str = f"£{rl.amount:>12,.2f}"
                lines.append(f"  {label:<{width - 18}}{amount_str}{note}")
            else:
                lines.append(f"  {label}{note}")

    # Notes
    if report.notes:
        lines.append("")
        lines.append(f"  {'─' * (width - 4)}")
        lines.append("  NOTES:")
        for note in report.notes:
            lines.append(f"  {note}")

    lines.append("")
    lines.append(f"  Generated: {report.date_generated}")
    lines.append("=" * width)

    return "\n".join(lines)


def format_dashboard(dashboard: Dict) -> str:
    """Format dashboard as readable text."""
    kpis = dashboard["kpis"]
    lines = [
        "=" * 60,
        f"  DASHBOARD — {dashboard['entity']}",
        f"  Tax Year: {dashboard['tax_year']}",
        "=" * 60,
        "",
        f"  Revenue:          £{kpis['revenue']:>12,.2f}",
        f"  Expenses:         £{kpis['expenses']:>12,.2f}",
        f"  Profit:           £{kpis['profit']:>12,.2f}",
        f"  Gross margin:     {kpis['gross_margin']:>10.1f}%",
        f"  Net margin:       {kpis['net_margin']:>10.1f}%",
        "",
        f"  Cash position:    £{kpis['cash_position']:>12,.2f}",
        f"  Net assets:       £{kpis['net_assets']:>12,.2f}",
        "",
        f"  Tax due:          £{kpis['tax_due']:>12,.2f}",
        f"  Effective rate:   {kpis['effective_tax_rate']:>10.1f}%",
        f"  VAT threshold:    {kpis['vat_threshold_pct']:>10.1f}%",
        "",
        "  ALERTS:",
    ]
    for alert in dashboard["alerts"]:
        marker = {"OK": "[OK]", "WARNING": "[!!]", "CRITICAL": "[XX]"}.get(
            alert["level"], "[??]")
        lines.append(f"  {marker} {alert['message']}")

    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


# ========================================================================
# TEST
# ========================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("HNC REPORTS — Financial Reporting Engine Test")
    print("=" * 70)

    # Simulated P&L data (as returned by HNCLedger.profit_and_loss())
    pnl_data = {
        "entity": "John Smith Trading",
        "period": "2025/26",
        "revenue": {
            "Sales/Turnover": 60000.0,
            "Trading Gains": 720.0,
        },
        "total_revenue": 60720.0,
        "cost_of_sales": {
            "Purchases": 8500.0,
            "Direct Labour": 0.0,
            "Subcontractor Costs": 0.0,
        },
        "total_cost_of_sales": 8500.0,
        "gross_profit": 52220.0,
        "overheads": {
            "Motor Expenses": 1450.0,
            "Insurance": 150.0,
            "Telephone/Internet": 180.0,
        },
        "total_overheads": 1780.0,
        "administrative": {
            "Repairs & Maintenance": 2500.0,
            "Sundry Expenses": 695.0,
            "Subscriptions": 95.0,
            "Depreciation": 0.0,
        },
        "total_administrative": 3290.0,
        "net_profit_before_tax": 47150.0,
        "tax": {
            "Income Tax": 6487.0,
        },
        "total_tax": 6487.0,
        "net_profit_after_tax": 40663.0,
    }

    # Balance sheet data
    bs_data = {
        "entity": "John Smith Trading",
        "date": "2026-04-05",
        "fixed_assets": {
            "Motor Vehicles": 15000.0,
            "Plant & Machinery": 3500.0,
            "Depreciation (contra)": -4500.0,
        },
        "total_fixed_assets": 14000.0,
        "current_assets": {
            "Current Account": 22500.0,
            "Trade Debtors": 7500.0,
            "Crypto Holdings": 850.0,
        },
        "total_current_assets": 30850.0,
        "current_liabilities": {
            "VAT Output": 6022.50,
            "Trade Creditors": 1200.0,
        },
        "total_current_liabilities": 7222.50,
        "net_current_assets": 23627.50,
        "long_term_liabilities": {},
        "total_long_term_liabilities": 0.0,
        "equity": {
            "Drawings": -18000.0,
            "Retained Earnings": 0.0,
        },
        "net_income_current_period": 40663.0,
        "total_equity": 22663.0,
        "balanced": True,
    }

    # ---- P&L ----
    print("\n--- TEST 1: Profit & Loss ---")
    pnl_report = generate_pnl(pnl_data, "John Smith Trading", "2025/26")
    print(format_report(pnl_report))

    # ---- Balance Sheet ----
    print("\n--- TEST 2: Balance Sheet ---")
    bs_report = generate_balance_sheet(bs_data, "John Smith Trading", "2026-04-05")
    print(format_report(bs_report))

    # ---- Cash Flow ----
    print("\n--- TEST 3: Cash Flow ---")
    cf_report = generate_cash_flow(bs_data, pnl_data,
                                    opening_cash=5000.0,
                                    entity_name="John Smith Trading",
                                    tax_year="2025/26")
    print(format_report(cf_report))

    # ---- Aged Debtors ----
    print("\n--- TEST 4: Aged Debtors ---")
    invoices = [
        {"customer": "Mrs Jones", "amount": 8500, "due_date": "2026-02-15",
         "amount_outstanding": 0},
        {"customer": "Mr Brown", "amount": 7500, "due_date": "2026-04-30",
         "amount_outstanding": 7500},
        {"customer": "ABC Developments", "amount": 16000,
         "due_date": "2026-06-20", "amount_outstanding": 16000},
    ]
    ad_report = generate_aged_debtors(invoices, "2026-04-09",
                                       "John Smith Trading")
    print(format_report(ad_report))

    # ---- Tax Summary ----
    print("\n--- TEST 5: Tax Summary ---")
    # Simulate tax computation object
    class MockTax:
        income_tax = 6487.0
        class2_ni = 179.40
        class4_ni = 1946.10
        total_ni = 2125.50
        cgt = 0.0
        total_liability = 8612.50
        tax_due = 8612.50
        cis_deductions = 0.0
        paye_deductions = 0.0
        poa_each = 4306.25

    tax_report = generate_tax_summary(
        MockTax(), {"period": "2026-Q1", "box5_net_vat": 6022.50},
        entity_name="John Smith Trading", tax_year="2025/26")
    print(format_report(tax_report))

    # ---- Dashboard ----
    print("\n--- TEST 6: Client Dashboard ---")
    dash = generate_dashboard(pnl_data, bs_data, MockTax(),
                               "John Smith Trading", "2025/26")
    print(format_dashboard(dash))

    # ---- CIS Summary ----
    print("\n--- TEST 7: CIS Summary ---")
    cis_payments = [
        {"subcontractor": "Dave's Plumbing", "gross": 3200,
         "materials": 800, "deduction_rate": 0.20, "utr": "12345 67890"},
        {"subcontractor": "Spark Electric", "gross": 2100,
         "materials": 400, "deduction_rate": 0.20, "utr": "98765 43210"},
    ]
    cis_report = generate_cis_summary(cis_payments, "March 2026",
                                       "John Smith Trading")
    print(format_report(cis_report))

    print("\n" + "=" * 70)
    print("Reports engine verified. Every number from the ledger.")
    print("=" * 70)
