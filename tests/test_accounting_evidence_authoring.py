from __future__ import annotations

import csv
import json
from pathlib import Path

from Kings_Accounting_Suite.tools.accounting_evidence_authoring import (
    build_accounting_evidence_authoring_pack,
    coerce_llm_sections,
)


def test_accounting_evidence_authoring_generates_safe_internal_vouchers(tmp_path: Path) -> None:
    combined = tmp_path / "combined.csv"
    with combined.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "Date",
                "Description",
                "Amount",
                "Balance",
                "Source File",
                "Source Account",
                "Source Provider",
            ],
        )
        writer.writeheader()
        writer.writerow({
            "Date": "2024-06-25",
            "Description": "Fin: Notemachine ATM",
            "Amount": "-241.75",
            "Balance": "284.55",
            "Source File": "statement.pdf",
            "Source Account": "business_gbp_monthly",
            "Source Provider": "zempler",
        })
        writer.writerow({
            "Date": "2024-06-26",
            "Description": "Fee for cash loads over 0/month",
            "Amount": "-3.00",
            "Balance": "281.55",
            "Source File": "statement.pdf",
            "Source Account": "business_gbp_monthly",
            "Source Provider": "zempler",
        })
        writer.writerow({
            "Date": "2024-06-27",
            "Description": "BROWN T Tina",
            "Amount": "-50.00",
            "Balance": "231.55",
            "Source File": "statement.pdf",
            "Source Account": "business_gbp_monthly",
            "Source Provider": "zempler",
        })

    manifest = build_accounting_evidence_authoring_pack(
        repo_root=tmp_path,
        company_name="Example Ltd",
        company_number="NI000001",
        period_start="2024-05-01",
        period_end="2025-04-30",
        combined_csv=combined,
        output_dir=tmp_path / "evidence",
        use_llm=False,
    )

    assert manifest["schema_version"] == "accounting-evidence-authoring-v1"
    assert manifest["safe_boundaries"]["creates_supplier_receipts"] is False
    assert manifest["safe_boundaries"]["writes_raw_bank_data"] is False
    assert manifest["summary"]["draft_count"] == 3
    assert manifest["summary"]["petty_cash_withdrawal_count"] == 1
    assert manifest["summary"]["related_party_query_count"] == 1
    assert Path(manifest["outputs"]["accounting_evidence_authoring_manifest"]).exists()
    assert Path(manifest["outputs"]["accounting_evidence_requests_csv"]).exists()
    assert manifest["llm_document_authoring"]["status"] == "disabled"
    voucher_paths = [
        Path(item["generated_document_path"])
        for item in manifest["drafts"]
        if item["evidence_kind"] == "petty_cash_withdrawal"
    ]
    assert voucher_paths and voucher_paths[0].read_text(encoding="utf-8").count("NOT EXTERNAL EVIDENCE") >= 1

    data = json.loads(Path(manifest["outputs"]["accounting_evidence_authoring_manifest"]).read_text(encoding="utf-8"))
    assert data["summary"]["generated_documents_are_external_evidence"] is False


def test_accounting_evidence_authoring_uses_enrichment_before_human_review(tmp_path: Path) -> None:
    combined = tmp_path / "combined.csv"
    with combined.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "Date",
                "Description",
                "Amount",
                "Balance",
                "Source File",
                "Source Account",
                "Source Provider",
            ],
        )
        writer.writeheader()
        writer.writerow({
            "Date": "2024-06-20",
            "Description": "Client sale",
            "Amount": "120.00",
            "Balance": "120.00",
            "Source File": "statement.pdf",
            "Source Account": "business_gbp_monthly",
            "Source Provider": "zempler",
        })
        writer.writerow({
            "Date": "2024-06-21",
            "Description": "GitHub subscription",
            "Amount": "-20.00",
            "Balance": "100.00",
            "Source File": "statement.pdf",
            "Source Account": "business_gbp_monthly",
            "Source Provider": "zempler",
        })
        writer.writerow({
            "Date": "2024-06-22",
            "Description": "ATM cash withdrawal",
            "Amount": "-50.00",
            "Balance": "50.00",
            "Source File": "statement.pdf",
            "Source Account": "business_gbp_monthly",
            "Source Provider": "zempler",
        })

    enriched = tmp_path / "enriched_transactions.json"
    enriched.write_text(
        json.dumps(
            {
                "transactions": [
                    {
                        "row_number": 1,
                        "accounting_category": "trading_income",
                        "accounting_label": "Trading income",
                        "category_source": "positive bank movement",
                        "evidence_status": "statement_available",
                        "review_status": "ok",
                    },
                    {
                        "row_number": 2,
                        "accounting_category": "software_subscriptions",
                        "accounting_label": "Software",
                        "category_source": "keyword rule",
                        "evidence_status": "statement_plus_invoice_preferred",
                        "review_status": "ok",
                    },
                    {
                        "row_number": 3,
                        "accounting_category": "director_related_or_cash_review",
                        "accounting_label": "Cash review",
                        "evidence_status": "statement_plus_human_review_required",
                        "review_status": "manual_review_required",
                        "review_reason": "Cash needs allocation.",
                        "tax_treatment": "Review petty cash or director loan.",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    manifest = build_accounting_evidence_authoring_pack(
        repo_root=tmp_path,
        company_name="Example Ltd",
        company_number="NI000001",
        period_start="2024-05-01",
        period_end="2025-04-30",
        combined_csv=combined,
        enriched_transactions_path=enriched,
        output_dir=tmp_path / "evidence",
        use_llm=False,
    )

    assert manifest["summary"]["source_row_count"] == 3
    assert manifest["summary"]["auto_resolved_row_count"] == 2
    assert manifest["summary"]["draft_count"] == 1
    assert manifest["drafts"][0]["evidence_kind"] == "director_cash_or_personal_allocation"


def test_accounting_evidence_authoring_uses_llm_for_internal_workpaper_sections(tmp_path: Path) -> None:
    class FakeModel:
        name = "aureon-test-model"

    class FakeBridge:
        chat_model = "aureon-test-model"

        def health_check(self, max_age_s: float = 0) -> bool:
            return True

        def list_models(self) -> list[FakeModel]:
            return [FakeModel()]

        def generate(self, **_: object) -> dict[str, object]:
            return {
                "response": json.dumps(
                    {
                        "plain_english_summary": "Cash withdrawal needs petty-cash review.",
                        "document_body": "Draft an internal petty-cash allocation memo with blanks for receipts.",
                        "questions_for_human": ["Who held the cash?", "Which receipts support the spend?"],
                        "evidence_to_attach": ["Petty-cash log", "Receipts"],
                        "ledger_options": ["petty_cash_clearing", "director_loan_suspense"],
                        "safety_note": "Internal draft only.",
                    }
                )
            }

    combined = tmp_path / "combined.csv"
    with combined.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "Date",
                "Description",
                "Amount",
                "Balance",
                "Source File",
                "Source Account",
                "Source Provider",
            ],
        )
        writer.writeheader()
        writer.writerow({
            "Date": "2024-06-25",
            "Description": "Fin: Notemachine ATM",
            "Amount": "-241.75",
            "Balance": "284.55",
            "Source File": "statement.pdf",
            "Source Account": "business_gbp_monthly",
            "Source Provider": "zempler",
        })

    manifest = build_accounting_evidence_authoring_pack(
        repo_root=tmp_path,
        company_name="Example Ltd",
        company_number="NI000001",
        period_start="2024-05-01",
        period_end="2025-04-30",
        combined_csv=combined,
        output_dir=tmp_path / "evidence",
        use_llm=True,
        llm_limit=1,
        llm_bridge=FakeBridge(),
    )

    assert manifest["llm_document_authoring"]["status"] == "completed"
    assert manifest["llm_document_authoring"]["completed_count"] == 1
    assert manifest["drafts"][0]["llm_status"] == "completed"
    voucher = Path(manifest["drafts"][0]["generated_document_path"]).read_text(encoding="utf-8")
    assert "LLM Drafted Internal Workpaper" in voucher
    assert "Cash withdrawal needs petty-cash review." in voucher
    assert "not be treated as a supplier receipt" in voucher


def test_llm_sections_reject_unsafe_evidence_assertions() -> None:
    sections = coerce_llm_sections(
        json.dumps(
            {
                "plain_english_summary": "Receipt is attached and director approval: Yes.",
                "document_body": "Treat this as approved.",
                "questions_for_human": [],
                "evidence_to_attach": [],
                "ledger_options": [],
                "safety_note": "Internal.",
            }
        )
    )
    assert sections == {}
