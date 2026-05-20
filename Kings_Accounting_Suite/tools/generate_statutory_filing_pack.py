"""Generate final-ready local Companies House and HMRC filing packs.

This tool builds on the unified accounting period pack. It prepares the files
that the end user/director needs for manual Companies House and HMRC filing:
final-ready statutory accounts, CT600 manual-entry data, tax computation,
iXBRL conversion inputs/readiness notes, and a filing checklist.

It does not file with Companies House, submit a CT600, create an HMRC-approved
iXBRL instance, authenticate, declare, or pay tax. The human role is manual
upload/entry/signature/submission only, using official portals or commercial
filing software where required.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import sys
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any


KAS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = KAS_DIR.parent
TOOLS_DIR = KAS_DIR / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from company_house_tax_audit import (  # noqa: E402
    DEFAULT_COMPANY_NAME,
    DEFAULT_COMPANY_NUMBER,
    DEFAULT_PERIOD_END,
    DEFAULT_PERIOD_START,
)
from accounting_report_enrichment import (  # noqa: E402
    ALLOWABLE_PNL_EXPENSE_LEDGER_ACCOUNTS,
    TRADING_INCOME_LEDGER_ACCOUNTS,
    build_official_template_audit,
    build_report_enrichment,
    render_classification_audit_markdown,
    render_expense_breakdown_markdown,
    render_full_accounts_pack_markdown,
    render_data_truth_checklist_markdown,
    render_math_stress_test_markdown,
    render_official_template_audit_markdown,
    render_profit_and_loss_markdown,
    render_source_reconciliation_markdown,
    render_tax_summary_markdown,
    tax_profile_for_row,
    write_enrichment_artifacts,
)
from accounting_payer_provenance import (  # noqa: E402
    render_cis_vat_tax_basis_markdown,
    render_payer_provenance_markdown,
    write_payer_provenance_artifacts,
)


OFFICIAL_REQUIREMENT_SOURCES = {
    "company_tax_return_obligations": "https://www.gov.uk/guidance/company-tax-return-obligations",
    "company_tax_returns_overview": "https://www.gov.uk/company-tax-returns",
    "accounts_and_tax_returns_limited_company": "https://www.gov.uk/prepare-file-annual-accounts-for-limited-company/file-your-accounts-and-company-tax-return",
    "ct600_form": "https://www.gov.uk/government/publications/corporation-tax-company-tax-return-ct600-2015-version-3",
    "company_tax_return_guide": "https://www.gov.uk/guidance/the-company-tax-return-guide",
    "company_tax_return_accounts_format": "https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/1078382/Format_for_accounts_forming_part_of_an_online_Company_Tax_Return.pdf",
    "companies_house_accounts": "https://www.gov.uk/government/publications/life-of-a-company-annual-requirements/life-of-a-company-part-1-accounts",
    "companies_house_micro_entity": "https://find-and-update.company-information.service.gov.uk/guides/accounts/chooser/micro-entity",
    "companies_house_confirmation_statement": "https://www.gov.uk/file-your-confirmation-statement-with-companies-house",
    "companies_house_identity_verification": "https://www.gov.uk/guidance/identity-verification-for-companies-house",
    "corporation_tax_rates": "https://www.gov.uk/corporation-tax-rates/rates",
    "companies_house_api_search": "https://developer-specs.company-information.service.gov.uk/companies-house-public-data-api/reference/search/search-companies",
    "companies_house_api_company_profile": "https://developer-specs.company-information.service.gov.uk/companies-house-public-data-api/reference/company-profile/company-profile",
    "vat_domestic_reverse_charge": "https://www.gov.uk/guidance/vat-domestic-reverse-charge-for-building-and-construction-services",
}

FINAL_READY_STATUS = "final_ready_manual_upload_required"
MANUAL_SUBMISSION_STATUS = "manual_submission_required"


@dataclass
class FilingFigures:
    turnover: Decimal
    expenses: Decimal
    profit_before_tax: Decimal
    taxable_profit: Decimal
    corporation_tax_rate: Decimal
    corporation_tax: Decimal
    profit_after_tax: Decimal
    bank_net_assets: Decimal
    net_assets: Decimal
    raw_bank_turnover: Decimal = Decimal("0.00")
    raw_bank_expenses: Decimal = Decimal("0.00")
    cis_gross_income_total: Decimal = Decimal("0.00")
    cis_deduction_suffered_total: Decimal = Decimal("0.00")
    cis_citb_levy_total: Decimal = Decimal("0.00")
    cis_net_banked_total: Decimal = Decimal("0.00")
    cis_gross_up_turnover_adjustment: Decimal = Decimal("0.00")
    corporation_tax_after_cis_credit: Decimal = Decimal("0.00")
    cis_credit_surplus_or_refund_review: Decimal = Decimal("0.00")
    cis_limited_company_claim_route: str = "monthly_payroll_eps_or_refund_review_not_ct600"
    vat_taxable_turnover_estimate: Decimal = Decimal("0.00")
    vat_registration_threshold: Decimal = Decimal("90000.00")
    vat_threshold_exceeded: bool = False


def money(value: Decimal | int | float | str) -> Decimal:
    if isinstance(value, Decimal):
        raw = value
    else:
        raw = Decimal(str(value or "0"))
    return raw.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def money_text(value: Decimal | int | float | str) -> str:
    return f"{money(value):,.2f}"


def parse_transaction_date(value: str) -> date | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def corporation_tax_for_profit(taxable_profit: Decimal, associated_companies: int = 1) -> tuple[Decimal, Decimal]:
    """Estimate UK Corporation Tax with small profits rate and marginal relief."""
    taxable_profit = money(max(taxable_profit, Decimal("0")))
    companies = max(int(associated_companies or 1), 1)
    lower_limit = Decimal("50000.00") / Decimal(companies)
    upper_limit = Decimal("250000.00") / Decimal(companies)
    small_rate = Decimal("0.19")
    main_rate = Decimal("0.25")
    if taxable_profit <= lower_limit:
        tax = money(taxable_profit * small_rate)
    elif taxable_profit >= upper_limit:
        tax = money(taxable_profit * main_rate)
    else:
        tax = money((taxable_profit * main_rate) - ((upper_limit - taxable_profit) * Decimal("0.015")))
    effective_rate = (tax / taxable_profit).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP) if taxable_profit else Decimal("0.0000")
    return tax, effective_rate


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_combined_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def source_pack_paths(company_number: str, period_start: str, period_end: str) -> dict[str, Path]:
    period_dir = KAS_DIR / "output" / "gateway" / f"{period_start}_to_{period_end}"
    compliance_dir = KAS_DIR / "output" / "company_compliance" / company_number
    return {
        "period_dir": period_dir,
        "period_manifest": period_dir / "period_pack_manifest.json",
        "combined_csv": period_dir / f"combined_bank_transactions_{period_start}_to_{period_end}.csv",
        "full_run_manifest": compliance_dir / "full_company_accounts_run_manifest.json",
        "full_run_summary": compliance_dir / "full_company_accounts_run_summary.md",
        "company_house_tax_audit": compliance_dir / "company_house_tax_audit.md",
    }


def build_figures(rows: list[dict[str, str]]) -> FilingFigures:
    raw_turnover = money(sum((Decimal(row.get("Amount") or "0") for row in rows if Decimal(row.get("Amount") or "0") > 0), Decimal("0")))
    raw_expenses = money(-sum((Decimal(row.get("Amount") or "0") for row in rows if Decimal(row.get("Amount") or "0") < 0), Decimal("0")))
    tax_profiles = []
    for row in rows:
        amount = money(row.get("Amount") or "0")
        tax_profiles.append(tax_profile_for_row(row, amount))
    cis_gross = money(sum((Decimal(item["cis_gross_income"]) for item in tax_profiles), Decimal("0")))
    cis_net = money(sum((Decimal(item["cis_net_banked"]) for item in tax_profiles), Decimal("0")))
    cis_deducted = money(sum((Decimal(item["cis_deduction_suffered"]) for item in tax_profiles), Decimal("0")))
    cis_citb = money(sum((Decimal(item["cis_citb_levy"]) for item in tax_profiles), Decimal("0")))
    cis_gross_up_adjustment = money(cis_gross - cis_net)
    vat_taxable_turnover = money(sum((Decimal(item["vat_taxable_turnover"]) for item in tax_profiles), Decimal("0")))
    turnover = money(raw_turnover + cis_gross_up_adjustment)
    expenses = money(raw_expenses + cis_citb)
    profit_before_tax = money(turnover - expenses)
    taxable_profit = money(max(profit_before_tax, Decimal("0")))
    corporation_tax, corporation_tax_rate = corporation_tax_for_profit(taxable_profit)
    corporation_tax_after_cis_credit = corporation_tax
    cis_credit_surplus_or_refund_review = cis_deducted
    profit_after_tax = money(profit_before_tax - corporation_tax)
    bank_net_assets = money(profit_before_tax)
    net_assets = money(bank_net_assets - corporation_tax)
    return FilingFigures(
        turnover=turnover,
        expenses=expenses,
        profit_before_tax=profit_before_tax,
        taxable_profit=taxable_profit,
        corporation_tax_rate=corporation_tax_rate,
        corporation_tax=corporation_tax,
        profit_after_tax=profit_after_tax,
        bank_net_assets=bank_net_assets,
        net_assets=net_assets,
        raw_bank_turnover=raw_turnover,
        raw_bank_expenses=raw_expenses,
        cis_gross_income_total=cis_gross,
        cis_deduction_suffered_total=cis_deducted,
        cis_citb_levy_total=cis_citb,
        cis_net_banked_total=cis_net,
        cis_gross_up_turnover_adjustment=cis_gross_up_adjustment,
        corporation_tax_after_cis_credit=corporation_tax_after_cis_credit,
        cis_credit_surplus_or_refund_review=cis_credit_surplus_or_refund_review,
        vat_taxable_turnover_estimate=vat_taxable_turnover,
        vat_threshold_exceeded=vat_taxable_turnover >= Decimal("90000.00"),
    )


def build_figures_from_enrichment(enrichment: dict[str, Any]) -> FilingFigures:
    """Use final audit ledgers for the filing/tax basis, not raw cash totals."""
    tax = enrichment.get("tax_obligation_summary") or {}
    turnover = money(tax.get("tax_basis_turnover", tax.get("adjusted_turnover_after_cis_gross_up", "0")))
    expenses = money(tax.get("tax_basis_expenses", tax.get("adjusted_expenses_after_citb", "0")))
    profit_before_tax = money(turnover - expenses)
    taxable_profit = money(max(profit_before_tax, Decimal("0")))
    corporation_tax, corporation_tax_rate = corporation_tax_for_profit(taxable_profit)
    profit_after_tax = money(profit_before_tax - corporation_tax)
    bank_net_assets = money(profit_before_tax)
    net_assets = money(bank_net_assets - corporation_tax)
    cis_deducted = money(tax.get("cis_deduction_suffered_total", "0"))
    vat_taxable_turnover = money(tax.get("vat_taxable_turnover_estimate", turnover))
    return FilingFigures(
        turnover=turnover,
        expenses=expenses,
        profit_before_tax=profit_before_tax,
        taxable_profit=taxable_profit,
        corporation_tax_rate=corporation_tax_rate,
        corporation_tax=corporation_tax,
        profit_after_tax=profit_after_tax,
        bank_net_assets=bank_net_assets,
        net_assets=net_assets,
        raw_bank_turnover=money(tax.get("raw_bank_money_in", turnover)),
        raw_bank_expenses=money(tax.get("raw_bank_money_out", expenses)),
        cis_gross_income_total=money(tax.get("cis_gross_income_total", "0")),
        cis_deduction_suffered_total=cis_deducted,
        cis_citb_levy_total=money(tax.get("cis_citb_levy_total", "0")),
        cis_net_banked_total=money(tax.get("cis_net_banked_total", "0")),
        cis_gross_up_turnover_adjustment=money(tax.get("cis_gross_up_turnover_adjustment", "0")),
        corporation_tax_after_cis_credit=corporation_tax,
        cis_credit_surplus_or_refund_review=cis_deducted,
        vat_taxable_turnover_estimate=vat_taxable_turnover,
        vat_threshold_exceeded=bool(tax.get("vat_threshold_exceeded", vat_taxable_turnover >= Decimal("90000.00"))),
    )


def ct_financial_year_for(day: date) -> int:
    return day.year if day >= date(day.year, 4, 1) else day.year - 1


def ct_financial_year_slices(period_start: str, period_end: str) -> list[dict[str, Any]]:
    start = date.fromisoformat(period_start)
    end = date.fromisoformat(period_end)
    if end < start:
        raise ValueError(f"Period end {period_end} is before period start {period_start}")

    slices: list[dict[str, Any]] = []
    current = start
    while current <= end:
        fy = ct_financial_year_for(current)
        fy_start = date(fy, 4, 1)
        fy_end = date(fy + 1, 3, 31)
        slice_start = max(current, fy_start)
        slice_end = min(end, fy_end)
        slices.append(
            {
                "label": f"FY{fy}",
                "financial_year_start": fy,
                "date_start": slice_start.isoformat(),
                "date_end": slice_end.isoformat(),
                "day_count": (slice_end - slice_start).days + 1,
            }
        )
        current = slice_end + timedelta(days=1)
    return slices


def empty_ct_split_slice(base: dict[str, Any]) -> dict[str, Any]:
    return {
        **base,
        "transaction_count": 0,
        "allocation_method": "transaction_date_actual_row_allocation",
        "raw_money_in": "0.00",
        "raw_money_out": "0.00",
        "non_cis_trading_income": "0.00",
        "cis_gross_income": "0.00",
        "cis_net_banked": "0.00",
        "cis_deduction_suffered": "0.00",
        "cis_citb_levy": "0.00",
        "cis_gross_up_turnover_adjustment": "0.00",
        "turnover": "0.00",
        "expenses": "0.00",
        "profit_before_tax": "0.00",
        "taxable_profit_support": "0.00",
        "vat_taxable_turnover": "0.00",
        "corporation_tax_allocated_from_whole_period": "0.00",
        "corporation_tax_allocation_method": "whole_period_tax_allocated_by_positive_taxable_profit_share_review_required",
        "source_reconciliation_note": "slice totals reconcile to whole accounting-period figures in ct_financial_year_split.reconciliation",
    }


def decimal_field(row: dict[str, Any], key: str) -> Decimal:
    return money(row.get(key) or "0")


def allocate_total_by_weight(total: Decimal, weights: list[Decimal]) -> list[Decimal]:
    total = money(total)
    positive_weights = [max(weight, Decimal("0")) for weight in weights]
    weight_total = sum(positive_weights, Decimal("0"))
    if not weights:
        return []
    if weight_total <= 0:
        return [Decimal("0.00") for _ in weights]

    allocations: list[Decimal] = []
    running = Decimal("0.00")
    for index, weight in enumerate(positive_weights):
        if index == len(positive_weights) - 1:
            allocated = money(total - running)
        else:
            allocated = money(total * (weight / weight_total))
            running = money(running + allocated)
        allocations.append(allocated)
    return allocations


def reconciliation_item(field: str, whole: Decimal, split: Decimal) -> dict[str, str]:
    difference = money(whole - split)
    return {
        "field": field,
        "whole_period": str(money(whole)),
        "split_total": str(money(split)),
        "difference": str(difference),
        "status": "reconciled" if abs(difference) <= Decimal("0.01") else "review_required",
    }


def build_ct_financial_year_split(
    *,
    period_start: str,
    period_end: str,
    figures: FilingFigures,
    enrichment: dict[str, Any],
) -> dict[str, Any]:
    """Build an additive HMRC Corporation Tax financial-year support schedule."""
    slices = [empty_ct_split_slice(item) for item in ct_financial_year_slices(period_start, period_end)]
    by_label = {item["label"]: item for item in slices}

    for tx in enrichment.get("transactions") or []:
        tx_date = parse_transaction_date(str(tx.get("date") or ""))
        if not tx_date:
            continue
        label = f"FY{ct_financial_year_for(tx_date)}"
        target = by_label.get(label)
        if not target:
            continue

        amount = decimal_field(tx, "amount")
        target["transaction_count"] += 1
        if amount > 0:
            target["raw_money_in"] = str(money(Decimal(target["raw_money_in"]) + amount))
        elif amount < 0:
            target["raw_money_out"] = str(money(Decimal(target["raw_money_out"]) - amount))

        cis_scope = str(tx.get("cis_scope") or "")
        final_ledger = str(tx.get("final_ledger_account") or "")
        non_cis_trading_income = Decimal("0.00")
        if amount > 0 and cis_scope != "cis_net_receipt_detected" and final_ledger in TRADING_INCOME_LEDGER_ACCOUNTS:
            non_cis_trading_income = amount
        allowable_expense = Decimal("0.00")
        if amount < 0 and final_ledger in ALLOWABLE_PNL_EXPENSE_LEDGER_ACCOUNTS:
            allowable_expense = -amount

        cis_gross = decimal_field(tx, "cis_gross_income")
        cis_net = decimal_field(tx, "cis_net_banked")
        cis_deducted = decimal_field(tx, "cis_deduction_suffered")
        cis_citb = decimal_field(tx, "cis_citb_levy")
        vat_taxable = cis_gross if cis_scope == "cis_net_receipt_detected" else non_cis_trading_income

        target["non_cis_trading_income"] = str(money(Decimal(target["non_cis_trading_income"]) + non_cis_trading_income))
        target["cis_gross_income"] = str(money(Decimal(target["cis_gross_income"]) + cis_gross))
        target["cis_net_banked"] = str(money(Decimal(target["cis_net_banked"]) + cis_net))
        target["cis_deduction_suffered"] = str(money(Decimal(target["cis_deduction_suffered"]) + cis_deducted))
        target["cis_citb_levy"] = str(money(Decimal(target["cis_citb_levy"]) + cis_citb))
        target["vat_taxable_turnover"] = str(money(Decimal(target["vat_taxable_turnover"]) + vat_taxable))
        target["turnover"] = str(money(Decimal(target["non_cis_trading_income"]) + Decimal(target["cis_gross_income"])))
        target["expenses"] = str(money(Decimal(target["expenses"]) + allowable_expense + cis_citb))
        target["cis_gross_up_turnover_adjustment"] = str(
            money(Decimal(target["cis_gross_income"]) - Decimal(target["cis_net_banked"]))
        )
        target["profit_before_tax"] = str(money(Decimal(target["turnover"]) - Decimal(target["expenses"])))
        target["taxable_profit_support"] = str(money(max(Decimal(target["profit_before_tax"]), Decimal("0"))))

    tax_allocations = allocate_total_by_weight(
        figures.corporation_tax,
        [Decimal(item["taxable_profit_support"]) for item in slices],
    )
    for item, allocated_tax in zip(slices, tax_allocations):
        item["corporation_tax_allocated_from_whole_period"] = str(allocated_tax)

    totals = {
        "raw_money_in": money(sum((Decimal(item["raw_money_in"]) for item in slices), Decimal("0"))),
        "raw_money_out": money(sum((Decimal(item["raw_money_out"]) for item in slices), Decimal("0"))),
        "turnover": money(sum((Decimal(item["turnover"]) for item in slices), Decimal("0"))),
        "expenses": money(sum((Decimal(item["expenses"]) for item in slices), Decimal("0"))),
        "profit_before_tax": money(sum((Decimal(item["profit_before_tax"]) for item in slices), Decimal("0"))),
        "taxable_profit_support": money(sum((Decimal(item["taxable_profit_support"]) for item in slices), Decimal("0"))),
        "cis_gross_income": money(sum((Decimal(item["cis_gross_income"]) for item in slices), Decimal("0"))),
        "cis_deduction_suffered": money(sum((Decimal(item["cis_deduction_suffered"]) for item in slices), Decimal("0"))),
        "cis_citb_levy": money(sum((Decimal(item["cis_citb_levy"]) for item in slices), Decimal("0"))),
        "cis_net_banked": money(sum((Decimal(item["cis_net_banked"]) for item in slices), Decimal("0"))),
        "vat_taxable_turnover": money(sum((Decimal(item["vat_taxable_turnover"]) for item in slices), Decimal("0"))),
        "corporation_tax_allocated_from_whole_period": money(
            sum((Decimal(item["corporation_tax_allocated_from_whole_period"]) for item in slices), Decimal("0"))
        ),
    }
    comparisons = [
        reconciliation_item("raw_money_in", figures.raw_bank_turnover, totals["raw_money_in"]),
        reconciliation_item("raw_money_out", figures.raw_bank_expenses, totals["raw_money_out"]),
        reconciliation_item("turnover", figures.turnover, totals["turnover"]),
        reconciliation_item("expenses", figures.expenses, totals["expenses"]),
        reconciliation_item("profit_before_tax", figures.profit_before_tax, totals["profit_before_tax"]),
        reconciliation_item("taxable_profit_support", figures.taxable_profit, totals["taxable_profit_support"]),
        reconciliation_item("cis_gross_income", figures.cis_gross_income_total, totals["cis_gross_income"]),
        reconciliation_item("cis_deduction_suffered", figures.cis_deduction_suffered_total, totals["cis_deduction_suffered"]),
        reconciliation_item("cis_citb_levy", figures.cis_citb_levy_total, totals["cis_citb_levy"]),
        reconciliation_item("cis_net_banked", figures.cis_net_banked_total, totals["cis_net_banked"]),
        reconciliation_item("vat_taxable_turnover", figures.vat_taxable_turnover_estimate, totals["vat_taxable_turnover"]),
        reconciliation_item(
            "corporation_tax_allocated_from_whole_period",
            figures.corporation_tax,
            totals["corporation_tax_allocated_from_whole_period"],
        ),
    ]
    whole_period = {
        "label": "whole_period",
        "date_start": period_start,
        "date_end": period_end,
        "day_count": (date.fromisoformat(period_end) - date.fromisoformat(period_start)).days + 1,
        "transaction_count": sum(int(item["transaction_count"]) for item in slices),
        "raw_money_in": str(figures.raw_bank_turnover),
        "raw_money_out": str(figures.raw_bank_expenses),
        "turnover": str(figures.turnover),
        "expenses": str(figures.expenses),
        "profit_before_tax": str(figures.profit_before_tax),
        "taxable_profit_support": str(figures.taxable_profit),
        "cis_gross_income": str(figures.cis_gross_income_total),
        "cis_deduction_suffered": str(figures.cis_deduction_suffered_total),
        "cis_citb_levy": str(figures.cis_citb_levy_total),
        "cis_net_banked": str(figures.cis_net_banked_total),
        "vat_taxable_turnover": str(figures.vat_taxable_turnover_estimate),
        "corporation_tax": str(figures.corporation_tax),
    }
    return {
        "schema_version": "ct-financial-year-split-v1",
        "status": "generated_additive_support_only",
        "basis": "uk_corporation_tax_financial_years_start_1_april",
        "accounting_period_start": period_start,
        "accounting_period_end": period_end,
        "allocation_method": "transaction_date_actual_row_allocation",
        "fallback_allocation_method": "pro_rata_days_review_required_if_non_row_allocated_adjustments_are_added",
        "whole_period": whole_period,
        "slices": slices,
        "slice_totals": {key: str(value) for key, value in totals.items()},
        "reconciliation": {
            "tolerance": "0.01",
            "status": "reconciled" if all(item["status"] == "reconciled" for item in comparisons) else "review_required",
            "items": comparisons,
        },
        "manual_review_required": True,
        "official_sources": {
            "company_tax_return_guide": OFFICIAL_REQUIREMENT_SOURCES["company_tax_return_guide"],
            "company_tax_returns_overview": OFFICIAL_REQUIREMENT_SOURCES["company_tax_returns_overview"],
            "corporation_tax_rates": OFFICIAL_REQUIREMENT_SOURCES["corporation_tax_rates"],
        },
    }


def ct_financial_year_split_table_lines(split: dict[str, Any] | None) -> list[str]:
    if not split:
        return ["- CT financial-year split: not generated."]
    lines = [
        "| Slice | Date range | Days | Rows | Turnover | Expenses | Profit before tax | Taxable profit support | CT allocation |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in split.get("slices") or []:
        lines.append(
            f"| {item.get('label')} | {item.get('date_start')} to {item.get('date_end')} | "
            f"{item.get('day_count')} | {item.get('transaction_count')} | "
            f"GBP {money_text(item.get('turnover', 0))} | GBP {money_text(item.get('expenses', 0))} | "
            f"GBP {money_text(item.get('profit_before_tax', 0))} | "
            f"GBP {money_text(item.get('taxable_profit_support', 0))} | "
            f"GBP {money_text(item.get('corporation_tax_allocated_from_whole_period', 0))} |"
        )
    return lines


def render_ct_financial_year_split_markdown(
    *,
    company_name: str,
    company_number: str,
    split: dict[str, Any],
) -> str:
    reconciliation = split.get("reconciliation") or {}
    reconciliation_lines = [
        "| Field | Whole period | Split total | Difference | Status |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for item in reconciliation.get("items") or []:
        reconciliation_lines.append(
            f"| {item.get('field')} | GBP {money_text(item.get('whole_period', 0))} | "
            f"GBP {money_text(item.get('split_total', 0))} | GBP {money_text(item.get('difference', 0))} | "
            f"{item.get('status')} |"
        )
    return "\n".join(
        [
            "# HMRC Corporation Tax Financial-Year Split",
            "",
            f"Company: {company_name}",
            f"Company number: {company_number}",
            f"Accounting period: {split.get('accounting_period_start')} to {split.get('accounting_period_end')}",
            "",
            "This is an additive support schedule for HMRC Corporation Tax review. It does not replace the full accounting-period accounts.",
            "",
            "## Corporation Tax Financial-Year Slices",
            "",
            *ct_financial_year_split_table_lines(split),
            "",
            "## Reconciliation Back To Whole Accounting Period",
            "",
            f"- Status: {reconciliation.get('status')}",
            f"- Tolerance: GBP {reconciliation.get('tolerance')}",
            "",
            *reconciliation_lines,
            "",
            "## Review Notes",
            "",
            f"- Allocation method: {split.get('allocation_method')}",
            f"- Fallback method if future non-row adjustments are added: {split.get('fallback_allocation_method')}",
            "- Companies House accounts stay as whole accounting-period accounts.",
            "- HMRC/Companies House submission and any payment remain manual only.",
            "",
            "## Official Sources",
            "",
            *[f"- {name}: {url}" for name, url in (split.get("official_sources") or {}).items()],
            "",
        ]
    )


def write_ct_financial_year_split_csv(split: dict[str, Any], path: Path) -> None:
    fieldnames = [
        "record_type",
        "label",
        "financial_year_start",
        "date_start",
        "date_end",
        "day_count",
        "transaction_count",
        "allocation_method",
        "raw_money_in",
        "raw_money_out",
        "turnover",
        "expenses",
        "profit_before_tax",
        "taxable_profit_support",
        "cis_gross_income",
        "cis_deduction_suffered",
        "cis_citb_levy",
        "cis_net_banked",
        "vat_taxable_turnover",
        "corporation_tax_allocated_from_whole_period",
    ]
    rows: list[dict[str, Any]] = []
    rows.append({"record_type": "whole_period", **(split.get("whole_period") or {})})
    for item in split.get("slices") or []:
        rows.append({"record_type": "financial_year_slice", **item})
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def provider_rollups(combined: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_provider_summary": combined.get("source_provider_summary") or {},
        "flow_provider_summary": combined.get("flow_provider_summary") or {},
        "source_accounts": combined.get("source_accounts") or [],
        "transaction_source_count": combined.get("transaction_source_count", 0),
        "csv_source_count": combined.get("csv_source_count", 0),
        "pdf_source_count": combined.get("pdf_source_count", 0),
        "unique_rows_in_period": combined.get("unique_rows_in_period", 0),
        "duplicate_rows_removed": combined.get("duplicate_rows_removed", 0),
    }


def render_accounts_markdown(
    *,
    company_name: str,
    company_number: str,
    period_start: str,
    period_end: str,
    figures: FilingFigures,
    rollups: dict[str, Any],
    enrichment: dict[str, Any],
) -> str:
    source_rollup_lines = []
    for provider, info in sorted((rollups.get("source_provider_summary") or {}).items()):
        source_rollup_lines.append(
            f"- {provider}: {info.get('rows', 0)} rows; in GBP {info.get('money_in', '0.00')}; "
            f"out GBP {info.get('money_out', '0.00')}; net GBP {info.get('net', '0.00')}"
        )
    flow_rollup_lines = []
    for provider, info in sorted((rollups.get("flow_provider_summary") or {}).items()):
        flow_rollup_lines.append(
            f"- {provider}: {info.get('rows', 0)} rows; in GBP {info.get('money_in', '0.00')}; "
            f"out GBP {info.get('money_out', '0.00')}; net GBP {info.get('net', '0.00')}"
        )
    expense_breakdown_lines = [
        "| Category | Rows | Amount | Review rows |",
        "| --- | ---: | ---: | ---: |",
    ]
    for item in enrichment.get("category_totals") or []:
        if item.get("kind") != "expense":
            continue
        expense_breakdown_lines.append(
            f"| {item.get('label')} | {item.get('rows')} | GBP {item.get('money_out')} | {item.get('manual_review_rows')} |"
        )
    payer_summary = enrichment.get("payer_provenance_summary") or {}
    return "\n".join(
        [
            f"# Companies House Accounts - Final-Ready Manual Filing Pack",
            "",
            f"Company: {company_name}",
            f"Company number: {company_number}",
            f"Period: {period_start} to {period_end}",
            f"Generated: {datetime.now(timezone.utc).isoformat()}",
            "",
            "## Filing Status",
            "",
            "- Final-ready local accounts pack generated from the unified company data in the repo.",
            "- Ready for the end user/director to manually upload or enter after approval and signature.",
            "- Not filed with Companies House.",
            "- Not submitted to HMRC.",
            "- Not an HMRC-approved iXBRL accounts instance; use approved/commercial filing software where required.",
            "",
            "## Profit And Loss Account",
            "",
            f"- Raw bank money in before CIS gross-up: GBP {money_text(getattr(figures, 'raw_bank_turnover', figures.turnover))}",
            "- Non-trading income, director-loan movements, transfers, and control receipts are excluded from statutory turnover where final audit ledgers identify them.",
            f"- CIS gross-up adjustment to recognise tax deducted before payment: GBP {money_text(getattr(figures, 'cis_gross_up_turnover_adjustment', 0))}",
            f"- Turnover: GBP {money_text(figures.turnover)}",
            f"- Raw bank money out before CIS/CITB adjustment: GBP {money_text(getattr(figures, 'raw_bank_expenses', figures.expenses))}",
            "- Non-P&L outflows such as transfers, cash/director controls, private-use controls, and non-deductible suspense are excluded from the expense figure where final audit ledgers identify them.",
            f"- CITB/CIS-linked levy expense adjustment: GBP {money_text(getattr(figures, 'cis_citb_levy_total', 0))}",
            f"- Administrative and operating expenses: GBP {money_text(figures.expenses)}",
            f"- Profit before Corporation Tax: GBP {money_text(figures.profit_before_tax)}",
            f"- Corporation Tax provision: GBP {money_text(figures.corporation_tax)}",
            f"- CIS suffered/tax deducted at source for PAYE/EPS set-off or refund review: GBP {money_text(getattr(figures, 'cis_deduction_suffered_total', 0))}",
            f"- Estimated Corporation Tax before any separate CIS claim route: GBP {money_text(getattr(figures, 'corporation_tax_after_cis_credit', figures.corporation_tax))}",
            f"- Profit after Corporation Tax: GBP {money_text(figures.profit_after_tax)}",
            "",
            "### Expense Breakdown",
            "",
            *expense_breakdown_lines,
            "",
            "## Balance Sheet",
            "",
            f"- Fixed assets: GBP 0.00",
            f"- Current assets / bank net assets from period records: GBP {money_text(figures.bank_net_assets)}",
            f"- Creditors due within one year - Corporation Tax provision: GBP {money_text(figures.corporation_tax)}",
            f"- Net assets: GBP {money_text(figures.net_assets)}",
            f"- Capital and reserves: GBP {money_text(figures.net_assets)}",
            "",
            "## Notes To The Accounts",
            "",
            "- Accounting basis: micro-entity/small-company manual filing pack prepared from repo-held bank records.",
            "- Turnover and expense figures are generated from the unified transaction feed and carried into the manual filing pack.",
            "- Where bank receipts indicate CIS construction income, Aureon grosses up the banked net cash to gross income and records CIS suffered as a tax-credit/control item.",
            "- VAT threshold and domestic reverse-charge indicators are prepared as workpapers only; no VAT return, HMRC submission, or payment is made.",
            f"- Incoming payer provenance covers {payer_summary.get('incoming_rows_total', 0)} incoming rows; {payer_summary.get('lookup_required_count', 0)} rows require public-register lookup; no-missed control={payer_summary.get('lookup_required_plus_not_required_equals_total')}.",
            "- The one-line administrative expense total is supported by the detailed expense schedule and review queue.",
            "- Share capital, director loan account, accruals, prepayments, depreciation, and tax adjustments must be confirmed before filing.",
            "- The company appears to be below the turnover size used for micro/small-company accounts, but final eligibility must be confirmed by the director/accountant.",
            "",
            "## Source Data Coverage",
            "",
            f"- Transaction sources: {rollups.get('transaction_source_count', 0)}",
            f"- CSV sources: {rollups.get('csv_source_count', 0)}",
            f"- Parsed statement PDF sources: {rollups.get('pdf_source_count', 0)}",
            f"- Unique period rows: {rollups.get('unique_rows_in_period', 0)}",
            f"- Duplicate overlaps removed: {rollups.get('duplicate_rows_removed', 0)}",
            f"- Source accounts: {', '.join(rollups.get('source_accounts') or []) or 'none'}",
            "",
            "### Source Provider Rollup",
            "",
            *(source_rollup_lines or ["- none"]),
            "",
            "### Flow Provider Rollup",
            "",
            *(flow_rollup_lines or ["- none"]),
            "",
            "## Director Approval",
            "",
            "These final-ready accounts must be approved and signed by the director before manual filing.",
            "",
            "Director name: ________________________________",
            "",
            "Signature: _____________________________________",
            "",
            "Date: __________________________________________",
            "",
        ]
    )


def render_tax_computation_markdown(
    *,
    company_name: str,
    company_number: str,
    period_start: str,
    period_end: str,
    figures: FilingFigures,
    enrichment: dict[str, Any],
    ct_financial_year_split: dict[str, Any] | None = None,
) -> str:
    tax_adjustment_lines = [
        "| Area | Amount in accounts | Current treatment | Review action |",
        "| --- | ---: | --- | --- |",
    ]
    for item in enrichment.get("category_totals") or []:
        if item.get("kind") != "expense":
            continue
        label = item.get("label")
        amount = item.get("money_out")
        review_rows = int(item.get("manual_review_rows") or 0)
        if review_rows:
            action = f"Review {review_rows} rows before CT600/iXBRL entry."
            treatment = "manual tax treatment review"
        else:
            action = "Carry as allowable unless director/accountant identifies exceptions."
            treatment = "no add-back generated by local rules"
        tax_adjustment_lines.append(f"| {label} | GBP {amount} | {treatment} | {action} |")
    payer_summary = enrichment.get("payer_provenance_summary") or {}
    return "\n".join(
        [
            "# HMRC Corporation Tax Computation - Final-Ready Manual Entry Pack",
            "",
            f"Company: {company_name}",
            f"Company number: {company_number}",
            f"Accounting period: {period_start} to {period_end}",
            "",
            "## Computation",
            "",
            f"- Raw bank receipts before CIS gross-up: GBP {money_text(getattr(figures, 'raw_bank_turnover', figures.turnover))}",
            "- Final tax basis excludes non-trading/control receipts from turnover.",
            f"- CIS gross income recognised from net receipts: GBP {money_text(getattr(figures, 'cis_gross_income_total', 0))}",
            f"- CIS deducted before money reached the bank: GBP {money_text(getattr(figures, 'cis_deduction_suffered_total', 0))}",
            f"- CIS/CITB levy expense adjustment: GBP {money_text(getattr(figures, 'cis_citb_levy_total', 0))}",
            f"- Profit before tax per generated accounts: GBP {money_text(figures.profit_before_tax)}",
            "- Add backs currently generated by local rules: GBP 0.00",
            "- Deductions/reliefs currently generated by local rules: GBP 0.00",
            f"- Taxable total profits: GBP {money_text(figures.taxable_profit)}",
            f"- Corporation Tax effective rate used: {figures.corporation_tax_rate * Decimal('100')}%",
            "- Corporation Tax method: UK small profits/main rate estimate with marginal relief; associated companies assumed to be 1 unless reviewed.",
            f"- Corporation Tax due estimate: GBP {money_text(figures.corporation_tax)}",
            f"- CIS suffered is not deducted through this CT600 pack; limited-company claim route: {getattr(figures, 'cis_limited_company_claim_route', 'monthly_payroll_eps_or_refund_review_not_ct600')}",
            f"- CIS available for PAYE/EPS set-off or refund review: GBP {money_text(getattr(figures, 'cis_credit_surplus_or_refund_review', 0))}",
            "",
            "## VAT / CIS Control Workpaper",
            "",
            f"- VAT taxable turnover estimate: GBP {money_text(getattr(figures, 'vat_taxable_turnover_estimate', figures.turnover))}",
            f"- VAT registration threshold used: GBP {money_text(getattr(figures, 'vat_registration_threshold', 90000))}",
            f"- VAT threshold exceeded by generated data: {getattr(figures, 'vat_threshold_exceeded', False)}",
            "- Construction income is routed to domestic reverse-charge review where bank/source descriptions indicate CIS construction work.",
            f"- Payer provenance controls checked {payer_summary.get('incoming_rows_total', 0)} incoming rows and routed {payer_summary.get('lookup_required_count', 0)} rows to public-register lookup/evidence status.",
            "",
            "## Tax Adjustment And Expense Review Schedule",
            "",
            *tax_adjustment_lines,
            "",
            "## CT600 Manual Entry Support",
            "",
            f"- Trading turnover support: GBP {money_text(figures.turnover)}",
            f"- Total P&L expense support before manual add-back review: GBP {money_text(figures.expenses)}",
            "- Transfer, director/cash, private-use, and non-P&L control movements are not included as deductible expenses.",
            f"- Manual review rows affecting tax treatment: {(enrichment.get('review_summary') or {}).get('manual_review_row_count', 0)}",
            "",
            "## Corporation Tax Financial-Year Split Support",
            "",
            "The full accounting-period totals above remain the accounts figures. The table below adds HMRC CT financial-year support for periods crossing 1 April.",
            "",
            *ct_financial_year_split_table_lines(ct_financial_year_split),
            "",
            f"- Split reconciliation status: {((ct_financial_year_split or {}).get('reconciliation') or {}).get('status', 'not_generated')}",
            "- Split is support evidence only; final HMRC entry/review remains manual.",
            "",
            "## Human Checks Before Manual Submission",
            "",
            "- Confirm allowable/disallowable expenditure.",
            "- Confirm associated companies for Corporation Tax thresholds.",
            "- Confirm capital allowances, losses, R&D/creative relief, chargeable gains, loan relationships, director loan account, and VAT/CIS treatment.",
            "- Final HMRC submission must be made manually through HMRC-approved/commercial software where required.",
            "",
        ]
    )


def render_ixbrl_readiness_markdown() -> str:
    return "\n".join(
        [
            "# iXBRL Readiness Note",
            "",
            "This folder contains final-ready accounts and tax computation inputs for manual filing, but it does not create or submit an HMRC-approved iXBRL instance.",
            "",
            "HMRC online Company Tax Returns require CT600, accounts, and tax computations; for most companies, online accounts and computations must be supplied in iXBRL format.",
            "",
            "Action required:",
            "",
            "1. Approve the final-ready accounts figures.",
            "2. Import the CT600 manual-entry JSON and tax computation into approved commercial Corporation Tax filing software.",
            "3. Generate and validate iXBRL accounts/computations in that software.",
            "4. Manually file Companies House/HMRC submissions after director/accountant approval.",
            "",
        ]
    )


def render_checklist_markdown(outputs: dict[str, str]) -> str:
    return "\n".join(
        [
            "# Companies House And HMRC Filing Checklist",
            "",
            "## Generated Final-Ready Pack",
            "",
            *[f"- {name}: `{path}`" for name, path in outputs.items()],
            "",
            "## Manual Review Before Filing",
            "",
            "- Confirm company details, registered office, SIC, share capital, directors, and accounting period.",
            "- Confirm Zempler, Revolut, and SumUp flows are correctly classified.",
            "- Confirm director loan account, personal drawings, accruals, prepayments, depreciation, VAT/CIS, and tax add-backs.",
            "- Confirm the HMRC Corporation Tax financial-year split where the accounting period crosses 1 April.",
            "- Confirm CT600 boxes in commercial Corporation Tax software.",
            "- Generate/validate iXBRL accounts and computations where required.",
            "- Manually upload/enter the generated files with Companies House and HMRC after approval.",
            "",
            "## Official Guidance Sources",
            "",
            *[f"- {name}: {url}" for name, url in OFFICIAL_REQUIREMENT_SOURCES.items()],
            "",
        ]
    )


def render_directors_report_markdown(
    *,
    company_name: str,
    company_number: str,
    period_start: str,
    period_end: str,
    figures: FilingFigures,
) -> str:
    return "\n".join(
        [
            "# Directors Report - Final-Ready Manual Filing Pack",
            "",
            f"Company: {company_name}",
            f"Company number: {company_number}",
            f"Period: {period_start} to {period_end}",
            "",
            "## Principal Activity",
            "",
            "The principal activity of the company during the period was consulting and brokerage services. Confirm before filing.",
            "",
            "## Results",
            "",
            f"The generated profit after Corporation Tax for the period is GBP {money_text(figures.profit_after_tax)}.",
            "",
            "## Dividends",
            "",
            "No dividend has been generated by this pack. Confirm manually before filing.",
            "",
            "## Directors",
            "",
            "Director names and appointment dates must be confirmed from the statutory register before filing.",
            "",
            "## Small Company / Micro-Entity Exemptions",
            "",
            "This report is generated as a review artifact. Confirm whether the company is entitled to micro-entity or small-company exemptions before deciding what must be filed.",
            "",
            "Director approval: ________________________________",
            "",
            "Date: _____________________________________________",
            "",
        ]
    )


def render_audit_exemption_statement_markdown(
    *,
    company_name: str,
    company_number: str,
    period_start: str,
    period_end: str,
) -> str:
    return "\n".join(
        [
            "# Audit Exemption And Filing Statement - Final-Ready Manual Filing Pack",
            "",
            f"Company: {company_name}",
            f"Company number: {company_number}",
            f"Period: {period_start} to {period_end}",
            "",
            "This record captures the audit-exemption and filing statements that may be required when preparing small-company or micro-entity accounts.",
            "",
            "## Review Points",
            "",
            "- Confirm the company qualifies for audit exemption.",
            "- Confirm shareholders have not required an audit.",
            "- Confirm the balance sheet contains the required director signature and exemption wording in the final filing software.",
            "- Confirm whether micro-entity, abridged, filleted, or full accounts are being filed.",
            "",
            f"Status: {FINAL_READY_STATUS}.",
            "",
        ]
    )


def render_ct600_box_map_markdown(
    *,
    company_name: str,
    company_number: str,
    period_start: str,
    period_end: str,
    figures: FilingFigures,
    enrichment: dict[str, Any],
    ct_financial_year_split: dict[str, Any] | None = None,
) -> str:
    review_count = (enrichment.get("review_summary") or {}).get("manual_review_row_count", 0)
    return "\n".join(
        [
            "# CT600 Box Map - Final-Ready Manual Entry Pack",
            "",
            f"Company: {company_name}",
            f"Company number: {company_number}",
            f"Accounting period: {period_start} to {period_end}",
            "",
            "| CT600 Area | Generated value | Review status |",
            "| --- | ---: | --- |",
            f"| Raw bank receipts | GBP {money_text(getattr(figures, 'raw_bank_turnover', figures.turnover))} | source-bank reconciliation value |",
            f"| CIS gross-up adjustment | GBP {money_text(getattr(figures, 'cis_gross_up_turnover_adjustment', 0))} | recognises CIS deducted before payment reached bank |",
            f"| Turnover / trading income support | GBP {money_text(figures.turnover)} | generated from unified bank feed plus CIS gross-up control |",
            f"| CIS suffered / tax deducted at source | GBP {money_text(getattr(figures, 'cis_deduction_suffered_total', 0))} | limited-company PAYE/EPS set-off or refund review control, not CT600 auto-deduction |",
            f"| VAT taxable turnover estimate | GBP {money_text(getattr(figures, 'vat_taxable_turnover_estimate', figures.turnover))} | VAT registration/reverse-charge workpaper value |",
            f"| Administrative and operating expenses support | GBP {money_text(figures.expenses)} | generated from unified bank feed plus CITB/CIS levy adjustment; classification confirmation required |",
            f"| Profit before tax | GBP {money_text(figures.profit_before_tax)} | generated |",
            f"| Taxable total profits | GBP {money_text(figures.taxable_profit)} | generated; add-backs/reliefs review required |",
            f"| Corporation Tax charge | GBP {money_text(figures.corporation_tax)} | UK small profits/main rate estimate with marginal relief before separate CIS claim route |",
            f"| CIS claim route | {getattr(figures, 'cis_limited_company_claim_route', 'monthly_payroll_eps_or_refund_review_not_ct600')} | manual PAYE/EPS/refund review; not silently offset in CT600 |",
            f"| Manual classification review queue | {review_count} rows | review before final filing software entry |",
            "| UTR | blank | manual HMRC value required if not present in secrets/config |",
            "| Declaration | not signed | director/agent manual approval and submission required |",
            "| Repayment/bank details | blank | manual if applicable |",
            "",
            "## Corporation Tax Financial-Year Split Support",
            "",
            "Use the full accounting-period totals for the accounts and CT600 computation, with the split below as HMRC review support when the period crosses 1 April.",
            "",
            *ct_financial_year_split_table_lines(ct_financial_year_split),
            "",
            f"Split reconciliation status: {((ct_financial_year_split or {}).get('reconciliation') or {}).get('status', 'not_generated')}.",
            "",
            "Box placement is ready for manual entry/review in commercial Corporation Tax filing software.",
            "",
        ]
    )


def build_supplementary_pages_review(figures: FilingFigures) -> dict[str, Any]:
    return {
        "schema_version": "ct600-supplementary-pages-review-v1",
        "status": FINAL_READY_STATUS,
        "generated_review_flags": {
            "loans_to_participators_ct600a": "review_director_loan_account",
            "controlled_foreign_companies_ct600b": "not_detected_from_bank_feed",
            "group_and_consortium_relief_ct600c": "not_detected_from_bank_feed",
            "insurance_ct600d": "not_detected_from_bank_feed",
            "charities_ct600e": "not_detected_from_bank_feed",
            "tonnage_tax_ct600f": "not_detected_from_bank_feed",
            "northern_ireland_ct600g": "review_if_applicable",
            "cross_border_royalties_ct600h": "not_detected_from_bank_feed",
            "supplementary_charge_ct600i": "not_detected_from_bank_feed",
            "restoration_tax_ct600j": "not_detected_from_bank_feed",
            "creative_reliefs_ct600l": "not_detected_from_bank_feed",
            "freeports_and_investment_zones_ct600m": "not_detected_from_bank_feed",
        },
        "figures_reviewed": {
            "taxable_profit": str(figures.taxable_profit),
            "corporation_tax": str(figures.corporation_tax),
            "cis_deduction_suffered": str(figures.cis_deduction_suffered_total),
            "corporation_tax_after_cis_credit": str(figures.corporation_tax_after_cis_credit),
            "vat_taxable_turnover_estimate": str(figures.vat_taxable_turnover_estimate),
        },
        "manual_review_required": True,
        "manual_submission_required": True,
    }


def build_confirmation_statement_readiness(
    *,
    company_name: str,
    company_number: str,
    period_start: str,
    period_end: str,
) -> dict[str, Any]:
    return {
        "schema_version": "companies-house-confirmation-statement-readiness-v1",
        "status": "manual_filing_required",
        "company_name": company_name,
        "company_number": company_number,
        "period_context": f"{period_start} to {period_end}",
        "generated_fields": {
            "company_number": company_number,
            "company_name": company_name,
        },
        "manual_fields_required": [
            "confirmation_date",
            "registered_office_address_confirmation",
            "officers_and_pscs_confirmation",
            "share_capital_and_shareholders_confirmation",
            "sic_codes_confirmation",
            "lawful_purpose_statement",
            "presenter_authentication_or_authorised_filer_credentials",
        ],
        "safety": {
            "filed_with_companies_house": False,
            "payment_made": False,
            "requires_human_approval": True,
        },
        "official_sources": {
            "confirmation_statement": OFFICIAL_REQUIREMENT_SOURCES["companies_house_confirmation_statement"],
            "identity_verification": OFFICIAL_REQUIREMENT_SOURCES["companies_house_identity_verification"],
        },
    }


def render_confirmation_statement_readiness_markdown(readiness: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Confirmation Statement Readiness",
            "",
            f"- Company: {readiness.get('company_number')} {readiness.get('company_name')}",
            f"- Status: {readiness.get('status')}",
            "",
            "## Generated",
            "",
            *[f"- {key}: {value}" for key, value in (readiness.get("generated_fields") or {}).items()],
            "",
            "## Manual Fields Required",
            "",
            *[f"- {item}" for item in readiness.get("manual_fields_required") or []],
            "",
            "This pack does not file the confirmation statement or make a payment.",
            "",
        ]
    )


def build_government_requirements_matrix(
    *,
    outputs: dict[str, Path],
    figures: FilingFigures,
) -> dict[str, Any]:
    def output_ref(key: str) -> dict[str, Any]:
        path = outputs.get(key)
        return {
            "output_key": key,
            "path": str(path) if path else "",
            "exists": bool(path and path.exists()),
        }

    requirements = [
        {
            "id": "companies_house.annual_accounts.balance_sheet",
            "authority": "Companies House",
            "requirement": "Balance sheet / statement of financial position",
            "coverage": "final_ready_manual_upload",
            "outputs": [output_ref("companies_house_accounts_final_ready_markdown"), output_ref("companies_house_accounts_final_ready_pdf")],
            "manual_inputs": ["director approval", "final filing format choice", "company register confirmation"],
            "notes": "Balance sheet is generated from the unified accounting feed and ready for manual filing workflow after approval.",
        },
        {
            "id": "companies_house.annual_accounts.profit_and_loss",
            "authority": "Companies House",
            "requirement": "Profit and loss account where required",
            "coverage": "final_ready_manual_upload",
            "outputs": [output_ref("companies_house_accounts_final_ready_markdown"), output_ref("companies_house_accounts_final_ready_pdf"), output_ref("profit_and_loss_detailed_pdf")],
            "manual_inputs": ["classification review", "micro/small-company filing exemption decision"],
            "notes": "Generated in the final-ready statutory accounts pack.",
        },
        {
            "id": "companies_house.hmrc.expense_breakdown_support",
            "authority": "Companies House / HMRC",
            "requirement": "Readable expense breakdown and supporting schedules behind the accounts totals",
            "coverage": "complete_with_manual_review",
            "outputs": [output_ref("expense_breakdown_pdf"), output_ref("transaction_classification_audit_pdf"), output_ref("data_truth_checklist_pdf"), output_ref("math_stress_test_pdf"), output_ref("enriched_transactions_csv")],
            "manual_inputs": ["review low-confidence rows", "confirm director/cash/transfer/tax treatment"],
            "notes": "Detailed schedules prevent total expense/admin costs being presented as an unexplained lump.",
        },
        {
            "id": "companies_house.annual_accounts.notes",
            "authority": "Companies House",
            "requirement": "Notes to the accounts and exemption statements where applicable",
            "coverage": "final_ready_manual_upload_with_review",
            "outputs": [output_ref("companies_house_accounts_final_ready_markdown"), output_ref("audit_exemption_statement_final_ready_markdown")],
            "manual_inputs": ["share capital", "director loan account", "accruals/prepayments", "audit exemption eligibility"],
            "notes": "The system generates review notes; final wording must match the filing route.",
        },
        {
            "id": "companies_house.annual_accounts.director_approval",
            "authority": "Companies House",
            "requirement": "Director approval/signature and authentication",
            "coverage": "manual_required_with_generated_prompt",
            "outputs": [output_ref("directors_report_final_ready_markdown"), output_ref("companies_house_accounts_final_ready_markdown")],
            "manual_inputs": ["director signature", "Companies House authentication/authorised filer credentials"],
            "notes": "The system generates signature prompts but cannot approve or authenticate filing.",
        },
        {
            "id": "companies_house.confirmation_statement",
            "authority": "Companies House",
            "requirement": "Confirmation statement data and lawful-purpose confirmation",
            "coverage": "readiness_generated_manual_filing_required",
            "outputs": [output_ref("confirmation_statement_readiness_json"), output_ref("confirmation_statement_readiness_markdown")],
            "manual_inputs": ["officers", "PSCs", "shareholders", "SIC", "lawful-purpose confirmation", "payment/authentication"],
            "notes": "Generated as a readiness/gap artifact; no filing or payment occurs.",
        },
        {
            "id": "hmrc.company_tax_return.ct600",
            "authority": "HMRC",
            "requirement": "Company Tax Return CT600",
            "coverage": "final_ready_manual_entry_json",
            "outputs": [output_ref("ct600_manual_entry_json"), output_ref("ct600_box_map_final_ready_markdown")],
            "manual_inputs": ["UTR", "agent/company credentials", "declaration", "commercial filing software entry/review"],
            "notes": "CT600 manual-entry data is generated; official submission remains manual.",
        },
        {
            "id": "hmrc.company_tax_return.ct_financial_year_split",
            "authority": "HMRC",
            "requirement": "Corporation Tax financial-year split support where an accounting period crosses 1 April",
            "coverage": "generated_additive_support_manual_review_required",
            "outputs": [
                output_ref("ct_financial_year_split_json"),
                output_ref("ct_financial_year_split_csv"),
                output_ref("ct_financial_year_split_markdown"),
                output_ref("ct_financial_year_split_pdf"),
            ],
            "manual_inputs": ["confirm tax rate period treatment", "confirm add-backs/reliefs before final CT600 filing"],
            "notes": "The split supports HMRC review without replacing the whole accounting-period statutory accounts totals.",
        },
        {
            "id": "hmrc.company_tax_return.accounts",
            "authority": "HMRC",
            "requirement": "Accounts attached to Company Tax Return, normally iXBRL for online filing",
            "coverage": "readable_html_for_ixbrl_conversion",
            "outputs": [output_ref("accounts_readable_for_ixbrl_html"), output_ref("ixbrl_readiness_note")],
            "manual_inputs": ["commercial iXBRL generation/validation"],
            "notes": "The system creates readable HTML and readiness notes, not an HMRC-approved iXBRL instance.",
        },
        {
            "id": "hmrc.company_tax_return.computations",
            "authority": "HMRC",
            "requirement": "Tax computations, normally iXBRL for online filing",
            "coverage": "final_ready_computation_plus_readable_html",
            "outputs": [output_ref("hmrc_tax_computation_final_ready_markdown"), output_ref("hmrc_tax_computation_final_ready_pdf"), output_ref("corporation_tax_summary_pdf"), output_ref("computation_readable_for_ixbrl_html")],
            "manual_inputs": ["tax add-back/relief review", "commercial iXBRL validation"],
            "notes": "Computation is generated from bank-feed figures and must be reviewed for tax adjustments.",
        },
        {
            "id": "hmrc.cis_vat.payer_provenance",
            "authority": "HMRC / Companies House",
            "requirement": "Incoming payment provenance, CIS deducted-at-source support, VAT/reverse-charge workpapers",
            "coverage": "payer_lookup_and_tax_basis_workpapers_generated",
            "outputs": [
                output_ref("payer_provenance_pdf"),
                output_ref("payer_provenance_json"),
                output_ref("payer_provenance_csv"),
                output_ref("cis_vat_tax_basis_assurance_pdf"),
                output_ref("enriched_transactions_csv"),
            ],
            "manual_inputs": ["real CIS deduction statements/invoices where probable CIS is flagged", "VAT/CIS filing route confirmation"],
            "notes": "Every incoming row is retained in the provenance manifest; public-register lookups are read-only and never submit or verify with HMRC.",
        },
        {
            "id": "hmrc.company_tax_return.supplementary_pages",
            "authority": "HMRC",
            "requirement": "CT600 supplementary pages where applicable",
            "coverage": "review_matrix_generated",
            "outputs": [output_ref("supplementary_pages_review_json")],
            "manual_inputs": ["director/accountant applicability review"],
            "notes": "The system produces a supplementary-page review matrix, not legal/tax advice.",
        },
        {
            "id": "hmrc.corporation_tax.payment",
            "authority": "HMRC",
            "requirement": "Corporation Tax payment/reference where tax is due",
            "coverage": "estimate_generated_payment_manual",
            "outputs": [output_ref("hmrc_tax_computation_final_ready_markdown"), output_ref("ct600_manual_entry_json")],
            "manual_inputs": ["payment reference", "actual payment approval", "HMRC account check"],
            "notes": f"Corporation Tax estimate is GBP {money_text(figures.corporation_tax)}. The system never pays.",
        },
    ]
    generated = sum(
        1
        for item in requirements
        if any(token in item["coverage"] for token in ("generated", "readiness", "final_ready", "readable_html"))
    )
    manual = sum(1 for item in requirements if item.get("manual_inputs"))
    return {
        "schema_version": "government-filing-requirements-matrix-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "requirement_count": len(requirements),
            "generated_or_readiness_count": generated,
            "manual_review_required_count": manual,
            "official_submission_supported": False,
        },
        "requirements": requirements,
        "official_sources": OFFICIAL_REQUIREMENT_SOURCES,
    }


def render_government_requirements_markdown(matrix: dict[str, Any]) -> str:
    lines = [
        "# Government Filing Requirements Matrix",
        "",
        f"- Generated: {matrix.get('generated_at')}",
        f"- Requirements tracked: {(matrix.get('summary') or {}).get('requirement_count', 0)}",
        f"- Generated/readiness coverage: {(matrix.get('summary') or {}).get('generated_or_readiness_count', 0)}",
        "- Official filing/submission: manual only",
        "",
        "| Authority | Requirement | Coverage | Outputs | Manual inputs |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in matrix.get("requirements") or []:
        output_text = ", ".join(
            out.get("output_key", "")
            for out in item.get("outputs") or []
            if out.get("output_key")
        )
        manual_text = ", ".join(item.get("manual_inputs") or []) or "none"
        lines.append(
            f"| {item.get('authority')} | {item.get('requirement')} | "
            f"{item.get('coverage')} | {output_text} | {manual_text} |"
        )
    lines.extend(["", "## Official Sources", ""])
    for name, url in (matrix.get("official_sources") or {}).items():
        lines.append(f"- {name}: {url}")
    lines.append("")
    return "\n".join(lines)


def render_draft_ixbrl_html(title: str, body_markdown: str) -> str:
    body = "\n".join(f"<p>{html.escape(line)}</p>" if line else "<br>" for line in body_markdown.splitlines())
    return "\n".join(
        [
            "<!doctype html>",
            "<html lang=\"en\">",
            "<head>",
            "  <meta charset=\"utf-8\">",
            f"  <title>{html.escape(title)}</title>",
            "</head>",
            "<body>",
            f"  <h1>{html.escape(title)}</h1>",
            "  <p><strong>Final-ready readable filing input. Not a validated iXBRL filing instance.</strong></p>",
            body,
            "</body>",
            "</html>",
            "",
        ]
    )


def write_pdf(path: Path, title: str, markdown_text: str) -> bool:
    try:
        from pdf_markdown_renderer import render_markdown_pdf
    except Exception:
        return False
    return render_markdown_pdf(path, title, markdown_text)


def build_pack(
    *,
    company_name: str,
    company_number: str,
    period_start: str,
    period_end: str,
) -> dict[str, Any]:
    paths = source_pack_paths(company_number, period_start, period_end)
    if not paths["period_manifest"].exists():
        raise FileNotFoundError(f"Missing period manifest: {paths['period_manifest']}")
    period_manifest = read_json(paths["period_manifest"])
    combined = period_manifest.get("combined_bank_data") or {}
    combined_csv = Path(combined.get("combined_csv_path") or paths["combined_csv"])
    if not combined_csv.exists():
        raise FileNotFoundError(f"Missing combined bank transactions CSV: {combined_csv}")

    rows = read_combined_rows(combined_csv)
    raw_figures = build_figures(rows)
    rollups = provider_rollups(combined)
    enrichment = build_report_enrichment(rows, figures=raw_figures, rollups=rollups)
    figures = build_figures_from_enrichment(enrichment)
    enrichment = build_report_enrichment(rows, figures=figures, rollups=rollups)
    ct_financial_year_split = build_ct_financial_year_split(
        period_start=period_start,
        period_end=period_end,
        figures=figures,
        enrichment=enrichment,
    )

    out_dir = KAS_DIR / "output" / "statutory" / company_number / f"{period_start}_to_{period_end}"
    out_dir.mkdir(parents=True, exist_ok=True)

    full_accounts_pack_md = render_full_accounts_pack_markdown(
        company_name=company_name,
        company_number=company_number,
        period_start=period_start,
        period_end=period_end,
        figures=figures,
        report=enrichment,
    )
    accounts_md = render_accounts_markdown(
        company_name=company_name,
        company_number=company_number,
        period_start=period_start,
        period_end=period_end,
        figures=figures,
        rollups=rollups,
        enrichment=enrichment,
    )
    computation_md = render_tax_computation_markdown(
        company_name=company_name,
        company_number=company_number,
        period_start=period_start,
        period_end=period_end,
        figures=figures,
        enrichment=enrichment,
        ct_financial_year_split=ct_financial_year_split,
    )
    profit_and_loss_md = render_profit_and_loss_markdown(
        company_name=company_name,
        company_number=company_number,
        period_start=period_start,
        period_end=period_end,
        figures=figures,
        report=enrichment,
    )
    expense_breakdown_md = render_expense_breakdown_markdown(
        company_name=company_name,
        company_number=company_number,
        period_start=period_start,
        period_end=period_end,
        report=enrichment,
    )
    classification_audit_md = render_classification_audit_markdown(
        company_name=company_name,
        company_number=company_number,
        period_start=period_start,
        period_end=period_end,
        report=enrichment,
    )
    source_reconciliation_md = render_source_reconciliation_markdown(
        company_name=company_name,
        company_number=company_number,
        period_start=period_start,
        period_end=period_end,
        report=enrichment,
    )
    data_truth_checklist_md = render_data_truth_checklist_markdown(
        company_name=company_name,
        company_number=company_number,
        period_start=period_start,
        period_end=period_end,
        report=enrichment,
        source_paths={
            "combined_bank_transactions_csv": str(combined_csv),
            "period_pack_manifest": str(paths["period_manifest"]),
            "statutory_output_folder": str(out_dir),
            "gateway_output_folder": str(paths["period_dir"]),
            "company_compliance_folder": str(paths["full_run_manifest"].parent),
            "raw_data_roots": "uploads; bussiness accounts",
        },
    )
    math_stress_test_md = render_math_stress_test_markdown(
        company_name=company_name,
        company_number=company_number,
        period_start=period_start,
        period_end=period_end,
        figures=figures,
        report=enrichment,
    )
    corporation_tax_summary_md = render_tax_summary_markdown(
        company_name=company_name,
        company_number=company_number,
        period_start=period_start,
        period_end=period_end,
        figures=figures,
        report=enrichment,
    )
    payer_provenance_manifest = enrichment.get("payer_provenance_manifest") or {}
    payer_provenance_md = render_payer_provenance_markdown(
        company_name=company_name,
        company_number=company_number,
        period_start=period_start,
        period_end=period_end,
        manifest=payer_provenance_manifest,
    )
    cis_vat_tax_basis_md = render_cis_vat_tax_basis_markdown(
        company_name=company_name,
        company_number=company_number,
        period_start=period_start,
        period_end=period_end,
        manifest=payer_provenance_manifest,
        tax_summary=enrichment.get("tax_obligation_summary") or {},
    )
    ixbrl_note = render_ixbrl_readiness_markdown()
    directors_report_md = render_directors_report_markdown(
        company_name=company_name,
        company_number=company_number,
        period_start=period_start,
        period_end=period_end,
        figures=figures,
    )
    audit_exemption_md = render_audit_exemption_statement_markdown(
        company_name=company_name,
        company_number=company_number,
        period_start=period_start,
        period_end=period_end,
    )
    ct600_box_map_md = render_ct600_box_map_markdown(
        company_name=company_name,
        company_number=company_number,
        period_start=period_start,
        period_end=period_end,
        figures=figures,
        enrichment=enrichment,
        ct_financial_year_split=ct_financial_year_split,
    )
    ct_financial_year_split_md = render_ct_financial_year_split_markdown(
        company_name=company_name,
        company_number=company_number,
        split=ct_financial_year_split,
    )
    supplementary_pages = build_supplementary_pages_review(figures)
    confirmation_statement = build_confirmation_statement_readiness(
        company_name=company_name,
        company_number=company_number,
        period_start=period_start,
        period_end=period_end,
    )
    official_template_audit = build_official_template_audit(
        {
            "full_accounts_pack": full_accounts_pack_md,
            "companies_house_accounts": accounts_md,
            "hmrc_tax_computation": computation_md,
            "profit_and_loss": profit_and_loss_md,
            "expense_breakdown": expense_breakdown_md,
            "classification_audit": classification_audit_md,
            "source_reconciliation": source_reconciliation_md,
            "data_truth_checklist": data_truth_checklist_md,
            "math_stress_test": math_stress_test_md,
            "payer_provenance": payer_provenance_md,
            "cis_vat_tax_basis": cis_vat_tax_basis_md,
            "ct_financial_year_split": ct_financial_year_split_md,
        }
    )
    official_template_audit_md = render_official_template_audit_markdown(official_template_audit)

    outputs = {
        "full_accounts_pack_markdown": out_dir / "full_accounts_pack.md",
        "full_accounts_pack_pdf": out_dir / "full_accounts_pack.pdf",
        "companies_house_accounts_final_ready_markdown": out_dir / "companies_house_accounts_final_ready.md",
        "companies_house_accounts_final_ready_pdf": out_dir / "companies_house_accounts_final_ready.pdf",
        "directors_report_final_ready_markdown": out_dir / "directors_report_final_ready.md",
        "directors_report_final_ready_pdf": out_dir / "directors_report_final_ready.pdf",
        "audit_exemption_statement_final_ready_markdown": out_dir / "audit_exemption_statement_final_ready.md",
        "hmrc_tax_computation_final_ready_markdown": out_dir / "hmrc_tax_computation_final_ready.md",
        "hmrc_tax_computation_final_ready_pdf": out_dir / "hmrc_tax_computation_final_ready.pdf",
        "corporation_tax_summary_markdown": out_dir / "corporation_tax_summary.md",
        "corporation_tax_summary_pdf": out_dir / "corporation_tax_summary.pdf",
        "profit_and_loss_detailed_markdown": out_dir / "profit_and_loss_detailed.md",
        "profit_and_loss_detailed_pdf": out_dir / "profit_and_loss_detailed.pdf",
        "expense_breakdown_markdown": out_dir / "expense_breakdown_and_admin_costs.md",
        "expense_breakdown_pdf": out_dir / "expense_breakdown_and_admin_costs.pdf",
        "transaction_classification_audit_markdown": out_dir / "transaction_classification_audit.md",
        "transaction_classification_audit_pdf": out_dir / "transaction_classification_audit.pdf",
            "source_reconciliation_markdown": out_dir / "source_reconciliation_sumup_zempler_revolut.md",
            "source_reconciliation_pdf": out_dir / "source_reconciliation_sumup_zempler_revolut.pdf",
            "data_truth_checklist_markdown": out_dir / "data_truth_checklist_and_benchmark.md",
            "data_truth_checklist_pdf": out_dir / "data_truth_checklist_and_benchmark.pdf",
            "math_stress_test_markdown": out_dir / "math_stress_test_and_reconciliation.md",
            "math_stress_test_pdf": out_dir / "math_stress_test_and_reconciliation.pdf",
            "official_template_audit_markdown": out_dir / "official_template_alignment_audit.md",
            "official_template_audit_json": out_dir / "official_template_alignment_audit.json",
            "payer_provenance_markdown": out_dir / "payer_provenance_manifest.md",
            "payer_provenance_pdf": out_dir / "payer_provenance_manifest.pdf",
            "payer_provenance_json": out_dir / "payer_provenance_manifest.json",
            "payer_provenance_csv": out_dir / "payer_provenance_manifest.csv",
            "cis_vat_tax_basis_assurance_markdown": out_dir / "cis_vat_tax_basis_assurance.md",
            "cis_vat_tax_basis_assurance_pdf": out_dir / "cis_vat_tax_basis_assurance.pdf",
        "enriched_transactions_json": out_dir / "enriched_transactions.json",
        "enriched_transactions_csv": out_dir / "enriched_transactions.csv",
        "ct_financial_year_split_json": out_dir / "ct_financial_year_split.json",
        "ct_financial_year_split_csv": out_dir / "ct_financial_year_split.csv",
        "ct_financial_year_split_markdown": out_dir / "ct_financial_year_split.md",
        "ct_financial_year_split_pdf": out_dir / "ct_financial_year_split.pdf",
        "ct600_manual_entry_json": out_dir / "hmrc_ct600_manual_entry.json",
        "ct600_box_map_final_ready_markdown": out_dir / "ct600_box_map_final_ready.md",
        "supplementary_pages_review_json": out_dir / "ct600_supplementary_pages_review.json",
        "confirmation_statement_readiness_json": out_dir / "confirmation_statement_readiness.json",
        "confirmation_statement_readiness_markdown": out_dir / "confirmation_statement_readiness.md",
        "accounts_readable_for_ixbrl_html": out_dir / "accounts_readable_for_ixbrl.html",
        "computation_readable_for_ixbrl_html": out_dir / "computation_readable_for_ixbrl.html",
        "ixbrl_readiness_note": out_dir / "ixbrl_readiness_note.md",
        "government_requirements_matrix_json": out_dir / "government_filing_requirements_matrix.json",
        "government_requirements_matrix_markdown": out_dir / "government_filing_requirements_matrix.md",
        "filing_checklist": out_dir / "filing_checklist.md",
        "manifest": out_dir / "statutory_filing_pack_manifest.json",
    }
    outputs.update(
        {
            # Legacy aliases kept so older Aureon surfaces still resolve.
            "accounts_pack_markdown": outputs["full_accounts_pack_markdown"],
            "accounts_pack_pdf": outputs["full_accounts_pack_pdf"],
            "companies_house_accounts_markdown": outputs["companies_house_accounts_final_ready_markdown"],
            "companies_house_accounts_pdf": outputs["companies_house_accounts_final_ready_pdf"],
            "directors_report_markdown": outputs["directors_report_final_ready_markdown"],
            "directors_report_pdf": outputs["directors_report_final_ready_pdf"],
            "audit_exemption_statement_markdown": outputs["audit_exemption_statement_final_ready_markdown"],
            "hmrc_tax_computation_markdown": outputs["hmrc_tax_computation_final_ready_markdown"],
            "hmrc_tax_computation_pdf": outputs["hmrc_tax_computation_final_ready_pdf"],
            "profit_and_loss": outputs["profit_and_loss_detailed_pdf"],
            "tax_summary": outputs["corporation_tax_summary_pdf"],
            "hmrc_ct600_draft_json": outputs["ct600_manual_entry_json"],
            "ct600_box_map_markdown": outputs["ct600_box_map_final_ready_markdown"],
            "ct_financial_year_split": outputs["ct_financial_year_split_pdf"],
            "draft_accounts_html": outputs["accounts_readable_for_ixbrl_html"],
            "draft_computation_html": outputs["computation_readable_for_ixbrl_html"],
        }
    )

    outputs["full_accounts_pack_markdown"].write_text(full_accounts_pack_md, encoding="utf-8")
    outputs["companies_house_accounts_final_ready_markdown"].write_text(accounts_md, encoding="utf-8")
    outputs["directors_report_final_ready_markdown"].write_text(directors_report_md, encoding="utf-8")
    outputs["audit_exemption_statement_final_ready_markdown"].write_text(audit_exemption_md, encoding="utf-8")
    outputs["hmrc_tax_computation_final_ready_markdown"].write_text(computation_md, encoding="utf-8")
    outputs["corporation_tax_summary_markdown"].write_text(corporation_tax_summary_md, encoding="utf-8")
    outputs["profit_and_loss_detailed_markdown"].write_text(profit_and_loss_md, encoding="utf-8")
    outputs["expense_breakdown_markdown"].write_text(expense_breakdown_md, encoding="utf-8")
    outputs["transaction_classification_audit_markdown"].write_text(classification_audit_md, encoding="utf-8")
    outputs["source_reconciliation_markdown"].write_text(source_reconciliation_md, encoding="utf-8")
    outputs["data_truth_checklist_markdown"].write_text(data_truth_checklist_md, encoding="utf-8")
    outputs["math_stress_test_markdown"].write_text(math_stress_test_md, encoding="utf-8")
    outputs["official_template_audit_markdown"].write_text(official_template_audit_md, encoding="utf-8")
    outputs["official_template_audit_json"].write_text(json.dumps(official_template_audit, indent=2, sort_keys=True), encoding="utf-8")
    outputs["payer_provenance_markdown"].write_text(payer_provenance_md, encoding="utf-8")
    outputs["cis_vat_tax_basis_assurance_markdown"].write_text(cis_vat_tax_basis_md, encoding="utf-8")
    write_payer_provenance_artifacts(
        payer_provenance_manifest,
        json_path=outputs["payer_provenance_json"],
        csv_path=outputs["payer_provenance_csv"],
    )
    write_enrichment_artifacts(
        enrichment,
        json_path=outputs["enriched_transactions_json"],
        csv_path=outputs["enriched_transactions_csv"],
    )
    outputs["ct_financial_year_split_json"].write_text(
        json.dumps(ct_financial_year_split, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    write_ct_financial_year_split_csv(ct_financial_year_split, outputs["ct_financial_year_split_csv"])
    outputs["ct_financial_year_split_markdown"].write_text(ct_financial_year_split_md, encoding="utf-8")
    outputs["ct600_box_map_final_ready_markdown"].write_text(ct600_box_map_md, encoding="utf-8")
    outputs["supplementary_pages_review_json"].write_text(json.dumps(supplementary_pages, indent=2, sort_keys=True), encoding="utf-8")
    outputs["confirmation_statement_readiness_json"].write_text(json.dumps(confirmation_statement, indent=2, sort_keys=True), encoding="utf-8")
    outputs["confirmation_statement_readiness_markdown"].write_text(render_confirmation_statement_readiness_markdown(confirmation_statement), encoding="utf-8")
    outputs["ixbrl_readiness_note"].write_text(ixbrl_note, encoding="utf-8")
    outputs["accounts_readable_for_ixbrl_html"].write_text(render_draft_ixbrl_html("Final-Ready Accounts", accounts_md), encoding="utf-8")
    outputs["computation_readable_for_ixbrl_html"].write_text(render_draft_ixbrl_html("Final-Ready Tax Computation", computation_md), encoding="utf-8")
    write_pdf(outputs["full_accounts_pack_pdf"], "Full Accounts Pack", full_accounts_pack_md)
    write_pdf(outputs["companies_house_accounts_final_ready_pdf"], "Companies House Accounts - Final Ready", accounts_md)
    write_pdf(outputs["directors_report_final_ready_pdf"], "Directors Report - Final Ready", directors_report_md)
    write_pdf(outputs["hmrc_tax_computation_final_ready_pdf"], "HMRC Corporation Tax Computation - Final Ready", computation_md)
    write_pdf(outputs["corporation_tax_summary_pdf"], "Corporation Tax And CT600 Summary", corporation_tax_summary_md)
    write_pdf(outputs["profit_and_loss_detailed_pdf"], "Detailed Profit And Loss", profit_and_loss_md)
    write_pdf(outputs["expense_breakdown_pdf"], "Expense Breakdown And Admin Costs", expense_breakdown_md)
    write_pdf(outputs["transaction_classification_audit_pdf"], "Transaction Classification Audit", classification_audit_md)
    write_pdf(outputs["source_reconciliation_pdf"], "Source Reconciliation", source_reconciliation_md)
    write_pdf(outputs["data_truth_checklist_pdf"], "Full Data Truth Checklist And Benchmark", data_truth_checklist_md)
    write_pdf(outputs["math_stress_test_pdf"], "Math Stress Test And Reconciliation", math_stress_test_md)
    write_pdf(outputs["payer_provenance_pdf"], "Incoming Payment Payer Provenance And CIS Lookup", payer_provenance_md)
    write_pdf(outputs["cis_vat_tax_basis_assurance_pdf"], "CIS VAT Tax Basis Assurance", cis_vat_tax_basis_md)
    write_pdf(outputs["ct_financial_year_split_pdf"], "HMRC Corporation Tax Financial-Year Split", ct_financial_year_split_md)

    ct600 = {
        "schema_version": "hmrc-ct600-manual-entry-v1",
        "schema_features": ["ct_financial_year_split_v1"],
        "status": FINAL_READY_STATUS,
        "company_name": company_name,
        "company_number": company_number,
        "accounting_period_start": period_start,
        "accounting_period_end": period_end,
        "utr": "",
        "figures": {
            key: str(value)
            for key, value in asdict(figures).items()
        },
        "ct_financial_year_split": ct_financial_year_split,
        "ct600_support": {
            "ct600_required": True,
            "supplementary_pages_required": "director/accountant_review",
            "ct_financial_year_split_required_for_period_crossing_1_april": len(ct_financial_year_split.get("slices") or []) > 1,
            "ct_financial_year_split_reconciliation_status": (ct_financial_year_split.get("reconciliation") or {}).get("status"),
            "ct_financial_year_split_json": str(outputs["ct_financial_year_split_json"]),
            "ct_financial_year_split_csv": str(outputs["ct_financial_year_split_csv"]),
            "ct_financial_year_split_markdown": str(outputs["ct_financial_year_split_markdown"]),
            "ct_financial_year_split_pdf": str(outputs["ct_financial_year_split_pdf"]),
            "computed_tax_rate_note": "Small profits rate used where taxable profit is GBP 50,000 or less; confirm associated companies and reliefs.",
            "cis_deducted_before_bank_payment": str(figures.cis_deduction_suffered_total),
            "corporation_tax_payable_after_cis_credit_estimate": str(figures.corporation_tax_after_cis_credit),
            "vat_taxable_turnover_estimate": str(figures.vat_taxable_turnover_estimate),
            "vat_threshold_exceeded": figures.vat_threshold_exceeded,
            "hmrc_submission": "manual_commercial_software_required",
            "ixbrl_accounts_required": True,
            "ixbrl_computations_required": True,
            "manual_classification_review_rows": (enrichment.get("review_summary") or {}).get("manual_review_row_count", 0),
            "incoming_payer_lookup_required_rows": (enrichment.get("payer_provenance_summary") or {}).get("lookup_required_count", 0),
            "incoming_payer_no_missed_control": (enrichment.get("payer_provenance_summary") or {}).get("lookup_required_plus_not_required_equals_total", False),
            "expense_breakdown_pdf": str(outputs["expense_breakdown_pdf"]),
            "transaction_classification_audit_pdf": str(outputs["transaction_classification_audit_pdf"]),
            "payer_provenance_pdf": str(outputs["payer_provenance_pdf"]),
            "cis_vat_tax_basis_assurance_pdf": str(outputs["cis_vat_tax_basis_assurance_pdf"]),
        },
        "manual_filing_contract": {
            "aureon_generates": "final_ready_manual_entry_data",
            "human_does": "manual_entry_upload_declaration_submission_and_payment",
            "legacy_alias": "hmrc_ct600_draft_json",
        },
        "safety": {
            "submitted_to_hmrc": False,
            "filed_with_companies_house": False,
            "tax_paid": False,
            "requires_director_or_accountant_review": True,
        },
        "official_sources": OFFICIAL_REQUIREMENT_SOURCES,
    }
    outputs["ct600_manual_entry_json"].write_text(json.dumps(ct600, indent=2, sort_keys=True), encoding="utf-8")

    requirements_matrix = build_government_requirements_matrix(outputs=outputs, figures=figures)
    outputs["government_requirements_matrix_json"].write_text(
        json.dumps(requirements_matrix, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    outputs["government_requirements_matrix_markdown"].write_text(
        render_government_requirements_markdown(requirements_matrix),
        encoding="utf-8",
    )

    checklist_outputs = {key: str(value) for key, value in outputs.items() if key != "manifest"}
    outputs["filing_checklist"].write_text(render_checklist_markdown(checklist_outputs), encoding="utf-8")

    pack_status = (
        FINAL_READY_STATUS
        if official_template_audit.get("status") != "blocked_missing_breakdown"
        else "blocked_missing_breakdown"
    )
    manifest = {
        "schema_version": "statutory-filing-pack-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "company_name": company_name,
        "company_number": company_number,
        "period_start": period_start,
        "period_end": period_end,
        "figures": {key: str(value) for key, value in asdict(figures).items()},
        "filing_readiness_contract": {
            "status": pack_status,
            "aureon_role": "generate final-ready local Companies House and HMRC document pack",
            "human_role": "manual upload, entry, approval, declaration, submission, and payment",
            "not_automated": [
                "Companies House filing",
                "HMRC CT600 submission",
                "HMRC iXBRL validation/submission",
                "tax or penalty payment",
                "director/accountant approval",
            ],
            "canonical_final_ready_outputs": [
                "full_accounts_pack_pdf",
                "companies_house_accounts_final_ready_pdf",
                "companies_house_accounts_final_ready_markdown",
                "directors_report_final_ready_pdf",
                "hmrc_tax_computation_final_ready_pdf",
                "corporation_tax_summary_pdf",
                "profit_and_loss_detailed_pdf",
            "expense_breakdown_pdf",
            "transaction_classification_audit_pdf",
            "source_reconciliation_pdf",
            "data_truth_checklist_pdf",
            "math_stress_test_pdf",
            "payer_provenance_pdf",
            "payer_provenance_json",
            "payer_provenance_csv",
            "cis_vat_tax_basis_assurance_pdf",
            "ct_financial_year_split_pdf",
            "ct_financial_year_split_json",
            "ct600_manual_entry_json",
                "accounts_readable_for_ixbrl_html",
                "computation_readable_for_ixbrl_html",
                "filing_checklist",
            ],
        },
        "source_data": rollups,
        "accounting_report_enrichment": {
            "status": enrichment.get("status"),
            "row_count": enrichment.get("row_count"),
            "totals": enrichment.get("totals"),
            "tax_obligation_summary": enrichment.get("tax_obligation_summary"),
            "payer_provenance_summary": enrichment.get("payer_provenance_summary"),
            "review_summary": enrichment.get("review_summary"),
            "auris_summary": enrichment.get("auris_summary"),
            "soup_kitchen_summary": enrichment.get("soup_kitchen_summary"),
            "validator_summary": enrichment.get("validator_summary"),
        },
        "ct_financial_year_split": ct_financial_year_split,
        "official_template_audit": official_template_audit,
        "payer_provenance_manifest": payer_provenance_manifest,
        "input_period_manifest": str(paths["period_manifest"]),
        "input_combined_csv": str(combined_csv),
        "outputs": {
            key: {
                "path": str(path),
                "exists": path.exists(),
                "bytes": path.stat().st_size if path.exists() else 0,
            }
            for key, path in outputs.items()
            if key != "manifest"
        },
        "government_requirements_matrix": requirements_matrix,
        "confirmation_statement_readiness": confirmation_statement,
        "supplementary_pages_review": supplementary_pages,
        "safety": {
            "filed_with_companies_house": False,
            "submitted_to_hmrc": False,
            "paid_tax": False,
            "requires_director_or_accountant_review": True,
            "requires_commercial_ct_filing_software": True,
            "manual_submission_required": True,
        },
        "official_sources": OFFICIAL_REQUIREMENT_SOURCES,
    }
    outputs["manifest"].write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Companies House/HMRC final-ready manual filing pack.")
    parser.add_argument("--company-name", default=DEFAULT_COMPANY_NAME)
    parser.add_argument("--company-number", default=DEFAULT_COMPANY_NUMBER)
    parser.add_argument("--period-start", default=DEFAULT_PERIOD_START)
    parser.add_argument("--period-end", default=DEFAULT_PERIOD_END)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = build_pack(
        company_name=args.company_name,
        company_number=args.company_number,
        period_start=args.period_start,
        period_end=args.period_end,
    )
    print(manifest["outputs"]["companies_house_accounts_final_ready_markdown"]["path"])
    print(manifest["outputs"]["ct600_manual_entry_json"]["path"])
    print(manifest["outputs"]["filing_checklist"]["path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
