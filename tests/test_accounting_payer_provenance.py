from __future__ import annotations

from decimal import Decimal

from Kings_Accounting_Suite.tools.accounting_payer_provenance import (
    build_payer_provenance_manifest,
    construction_indicators_for,
    normalise_payer_name,
)


def test_payer_provenance_queues_over_400_cis_and_repeat_payer_rows() -> None:
    rows = [
        {"Date": "2025-03-05", "Description": "Grove Builders Ltd GROVE BUILDERS LTD", "Amount": "476.64", "Source Provider": "zempler", "Flow Provider": "zempler"},
        {"Date": "2025-03-06", "Description": "BROWN T TINA", "Amount": "200.00", "Source Provider": "zempler", "Flow Provider": "zempler"},
        {"Date": "2025-03-07", "Description": "BROWN T TINA", "Amount": "250.00", "Source Provider": "zempler", "Flow Provider": "zempler"},
        {"Date": "2025-03-08", "Description": "Small cash receipt", "Amount": "50.00", "Source Provider": "sumup", "Flow Provider": "sumup"},
        {"Date": "2025-03-09", "Description": "GitHub subscription", "Amount": "-20.00", "Source Provider": "revolut", "Flow Provider": "revolut"},
    ]

    def fake_lookup(query: str) -> dict:
        if "grove" in query:
            return {
                "lookup_status": "matched_companies_house_profile",
                "selected": {
                    "company_number": "NI000001",
                    "company_name": "GROVE BUILDERS LIMITED",
                    "company_status": "active",
                    "company_type": "ltd",
                    "sic_codes": ["41201"],
                    "registered_office_region": "Northern Ireland",
                    "match_confidence": "0.92",
                },
                "companies_house_candidates": [{"company_number": "NI000001", "company_name": "GROVE BUILDERS LIMITED", "match_confidence": "0.92"}],
                "evidence_urls": ["https://find-and-update.company-information.service.gov.uk/company/NI000001"],
                "match_confidence": "0.92",
            }
        return {"lookup_status": "companies_house_no_match", "companies_house_candidates": [], "evidence_urls": [], "match_confidence": "0.00"}

    manifest = build_payer_provenance_manifest(rows, companies_house_lookup=fake_lookup, lookup_threshold=Decimal("400.00"))
    summary = manifest["summary"]

    assert normalise_payer_name("Grove Builders Ltd GROVE BUILDERS LTD") == "grove builders ltd"
    assert summary["incoming_rows_total"] == 4
    assert summary["lookup_required_count"] == 3
    assert summary["lookup_not_required_count"] == 1
    assert summary["lookup_required_plus_not_required_equals_total"] is True

    by_row = manifest["records_by_row_number"]
    assert by_row["1"]["lookup_required"] is True
    assert by_row["1"]["tax_basis_status"] == "probable_cis_suffered"
    assert by_row["1"]["vat_reverse_charge_likelihood"] == "possible_construction_domestic_reverse_charge"
    assert by_row["1"]["selected_company_number"] == "NI000001"
    assert by_row["2"]["lookup_reason"] == "repeat_payer_aggregate_at_or_above_400"
    assert by_row["3"]["lookup_required"] is True
    assert by_row["4"]["lookup_status"] == "not_required_below_threshold_or_no_cis_signal"
    assert "5" not in by_row


def test_payer_provenance_blocks_lookup_without_api_key_but_keeps_control() -> None:
    rows = [
        {"Date": "2025-02-14", "Description": "CSR NI LTD THE CSR GROUP", "Amount": "2533.00", "Source Provider": "zempler", "Flow Provider": "zempler"},
    ]

    manifest = build_payer_provenance_manifest(rows, perform_online=False)
    record = manifest["records"][0]

    assert manifest["status"] == "completed_no_missed_incoming_rows"
    assert record["lookup_required"] is True
    assert record["lookup_status"] == "public_lookup_disabled_offline_mode"
    assert record["tax_basis_status"] == "probable_cis_suffered"
    assert record["cis_likelihood"] in {"medium", "high"}
    assert record["accounting_action"] == "provisional_cis_gross_up_workpaper_with_visible_evidence_request"


def test_payer_provenance_does_not_treat_creditbuilder_as_builder() -> None:
    rows = [
        {"Date": "2024-08-01", "Description": "CREDITBUILDER LOAN", "Amount": "108.00", "Source Provider": "zempler", "Flow Provider": "zempler"},
    ]

    manifest = build_payer_provenance_manifest(rows, perform_online=False)
    record = manifest["records"][0]

    assert construction_indicators_for("CREDITBUILDER LOAN") == []
    assert record["lookup_required"] is False
    assert record["tax_basis_status"] == "not_cis_income"
