from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from Kings_Accounting_Suite.tools.accounting_report_enrichment import (
    build_report_enrichment,
    render_classification_audit_markdown,
)


@dataclass
class Figures:
    turnover: Decimal
    expenses: Decimal
    profit_before_tax: Decimal
    taxable_profit: Decimal = Decimal("0.00")
    corporation_tax_rate: Decimal = Decimal("0.19")
    corporation_tax: Decimal = Decimal("0.00")
    profit_after_tax: Decimal = Decimal("0.00")
    bank_net_assets: Decimal = Decimal("0.00")
    net_assets: Decimal = Decimal("0.00")


def test_report_enrichment_classifies_or_reviews_every_row_and_reconciles() -> None:
    rows = [
        {"Date": "2024-05-01", "Description": "Client income", "Amount": "1000.00", "Source Provider": "zempler", "Flow Provider": "zempler"},
        {"Date": "2024-05-02", "Description": "GitHub subscription", "Amount": "-40.00", "Source Provider": "revolut", "Flow Provider": "revolut"},
        {"Date": "2024-05-03", "Description": "Fee for cash loads over 0/month", "Amount": "-3.00", "Source Provider": "zempler", "Flow Provider": "zempler"},
        {"Date": "2024-05-04", "Description": "ATM cash withdrawal", "Amount": "-100.00", "Source Provider": "zempler", "Flow Provider": "zempler"},
    ]
    figures = Figures(turnover=Decimal("1000.00"), expenses=Decimal("43.00"), profit_before_tax=Decimal("957.00"))

    report = build_report_enrichment(rows, figures=figures, rollups={"unique_rows_in_period": 4})

    assert report["row_count"] == 4
    assert report["unique_rows_classified_or_reviewed"] == 4
    assert report["fully_categorised_row_count"] == 4
    assert report["status"] == "complete_external_audit_pack_ready"
    assert report["totals"]["turnover"] == "1000.00"
    assert report["totals"]["expenses"] == "43.00"
    assert report["totals"]["reconciles_to_filing_figures"] is True

    categories = {item["category"] for item in report["category_totals"]}
    assert "trading_income" in categories
    assert "software_subscriptions" in categories
    assert "director_related_or_cash_review" in categories
    assert report["review_summary"]["manual_review_row_count"] >= 1
    assert report["review_summary"]["unresolved_outlier_count"] == 0
    assert report["review_summary"]["system_resolved_outlier_count"] >= 1
    assert report["review_summary"]["external_audit_pack_status"] == "ready_no_unresolved_outliers"
    assert report["payer_provenance_summary"]["incoming_rows_total"] == 1
    assert report["payer_provenance_summary"]["lookup_required_count"] == 1
    assert report["payer_provenance_summary"]["lookup_required_plus_not_required_equals_total"] is True
    assert report["cook_filter_manifest"]["status"] == "generated"
    assert report["cook_filter_manifest"]["route_counts"]["trading_income"] == 1
    assert report["cook_filter_manifest"]["route_counts"]["software_subscriptions"] == 1
    final_ledgers = {item["ledger_account"] for item in report["final_ledger_totals"]}
    assert "cash_withdrawal_petty_cash_control_non_deductible_until_receipted" in final_ledgers
    assert "bank_and_payment_fees" in final_ledgers
    assert report["safety"]["hmrc_submission_performed"] is False


def test_report_enrichment_trusts_cook_classifications_without_auris_review_flood() -> None:
    rows = [
        {"Date": "2024-06-01", "Description": "Client income", "Amount": "200.00", "Source Provider": "zempler", "Flow Provider": "zempler"},
        {"Date": "2024-06-02", "Description": "Fin: MCDONALDS,KENNEDY WAY,BELFAST", "Amount": "-6.73", "Source Provider": "zempler", "Flow Provider": "zempler"},
        {"Date": "2024-06-03", "Description": "Fin: MAXOL EDENDERRY SSTN,298 CRU,BELFAST", "Amount": "-10.00", "Source Provider": "zempler", "Flow Provider": "zempler"},
        {"Date": "2024-06-04", "Description": "Stephen leckey Steven", "Amount": "-200.00", "Source Provider": "zempler", "Flow Provider": "zempler"},
    ]
    figures = Figures(turnover=Decimal("200.00"), expenses=Decimal("216.73"), profit_before_tax=Decimal("-16.73"))

    report = build_report_enrichment(rows, figures=figures, rollups={"unique_rows_in_period": 4})
    transactions = {item["description"]: item for item in report["transactions"]}

    assert transactions["Fin: MCDONALDS,KENNEDY WAY,BELFAST"]["accounting_category"] == "subsistence_supplies"
    assert transactions["Fin: MCDONALDS,KENNEDY WAY,BELFAST"]["review_status"] == "ok"
    assert "mcdonald" in transactions["Fin: MCDONALDS,KENNEDY WAY,BELFAST"]["cook_filter_matched_terms"]
    assert transactions["Fin: MCDONALDS,KENNEDY WAY,BELFAST"]["cook_evidence_needed"] == "statement_plus_business_purpose_preferred"
    assert transactions["Fin: MAXOL EDENDERRY SSTN,298 CRU,BELFAST"]["accounting_category"] == "motor_and_travel"
    assert transactions["Fin: MAXOL EDENDERRY SSTN,298 CRU,BELFAST"]["review_status"] == "ok"
    assert "maxol" in transactions["Fin: MAXOL EDENDERRY SSTN,298 CRU,BELFAST"]["cook_filter_matched_terms"]
    assert transactions["Stephen leckey Steven"]["accounting_category"] == "payroll_subcontractor_review"
    assert transactions["Stephen leckey Steven"]["review_status"] == "manual_review_required"
    assert "subcontractor" in transactions["Stephen leckey Steven"]["cook_review_trigger"].lower()
    assert transactions["Stephen leckey Steven"]["final_ledger_account"] == "payroll_subcontractor_supplier_suspense"
    assert transactions["Stephen leckey Steven"]["outlier_status"] == "system_resolved"

    audit_md = render_classification_audit_markdown(
        company_name="EXAMPLE TRADING LTD",
        company_number="00000000",
        period_start="2024-05-01",
        period_end="2025-04-30",
        report=report,
    )
    assert "Cook Label And Filter Manifest" in audit_md
    assert "Subsistence, welfare, and small supplies" in audit_md


def test_report_enrichment_grosses_up_cis_net_receipts_and_tracks_vat_control() -> None:
    rows = [
        {"Date": "2025-03-05", "Description": "GROVE BUILDERS LTD GROVE BUILDERS LTD", "Amount": "476.64", "Source Provider": "zempler", "Flow Provider": "zempler"},
        {"Date": "2025-03-06", "Description": "GitHub subscription", "Amount": "-20.00", "Source Provider": "revolut", "Flow Provider": "revolut"},
    ]
    figures = Figures(turnover=Decimal("600.00"), expenses=Decimal("24.20"), profit_before_tax=Decimal("575.80"))

    report = build_report_enrichment(rows, figures=figures, rollups={"unique_rows_in_period": 2})
    tax = report["tax_obligation_summary"]

    assert tax["cis_net_receipt_row_count"] == 1
    assert tax["cis_net_banked_total"] == "476.64"
    assert tax["cis_gross_income_total"] == "600.00"
    assert tax["cis_deduction_suffered_total"] == "119.16"
    assert tax["cis_citb_levy_total"] == "4.20"
    assert tax["cis_gross_up_turnover_adjustment"] == "123.36"
    assert tax["cis_evidence_status_counts"]["probable_cis_suffered"] == 1
    assert tax["cis_credit_not_claimed_through_ct600"] is True
    assert tax["cis_limited_company_claim_route"].endswith("not_ct600")
    assert report["totals"]["turnover"] == "600.00"
    assert report["totals"]["expenses"] == "24.20"
    assert report["totals"]["reconciles_to_filing_figures"] is True
    tx = report["transactions"][0]
    assert tx["final_ledger_account"] == "cis_construction_turnover_net_receipt_plus_tax_suffered"
    assert tx["payer_name_normalized"] == "grove builders ltd"
    assert tx["lookup_required"] is True
    assert tx["tax_basis_status"] == "probable_cis_suffered"
    assert tx["vat_reverse_charge_status"].startswith("domestic_reverse_charge_possible")
