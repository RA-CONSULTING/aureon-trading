from __future__ import annotations

import csv
import json
from pathlib import Path

from Kings_Accounting_Suite.tools.accounting_handoff_pack import build_accounting_handoff_pack


def write(path: Path, text: str = "artifact") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_accounting_handoff_pack_gathers_raw_workpapers_and_manual_filing_support(tmp_path: Path) -> None:
    company_number = "NI000001"
    period_start = "2024-05-01"
    period_end = "2025-04-30"
    raw_root = tmp_path / "uploads"
    raw_root.mkdir(parents=True)
    write(raw_root / "Statement_06_Apr_2024_05_Apr_2025.csv", "Date,Description,Amount\n2024-05-03,Sale,100\n")

    period_dir = tmp_path / "Kings_Accounting_Suite" / "output" / "gateway" / f"{period_start}_to_{period_end}"
    combined_csv = period_dir / f"combined_bank_transactions_{period_start}_to_{period_end}.csv"
    period_dir.mkdir(parents=True)
    with combined_csv.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["Date", "Description", "Amount", "Balance"])
        writer.writeheader()
        writer.writerow({"Date": "2024-05-03", "Description": "Sale", "Amount": "100.00", "Balance": "100.00"})
    period_manifest = {
        "combined_bank_data": {
            "combined_csv_path": str(combined_csv),
            "transaction_source_count": 1,
            "unique_rows_in_period": 1,
        }
    }
    write(period_dir / "period_pack_manifest.json", json.dumps(period_manifest))

    company_dir = tmp_path / "Kings_Accounting_Suite" / "output" / "company_compliance" / company_number
    full_manifest_path = company_dir / "full_company_accounts_run_manifest.json"
    write(company_dir / "full_company_accounts_run_summary.md", "# Summary")
    write(company_dir / "company_house_tax_audit.json", "{}")
    write(company_dir / "company_house_tax_audit.md", "# Audit")
    write(company_dir / "autonomous_full_accounts_workflow_manifest.json", "{}")
    write(company_dir / "autonomous_full_accounts_workflow_summary.md", "# Workflow")

    statutory_dir = tmp_path / "Kings_Accounting_Suite" / "output" / "statutory" / company_number / f"{period_start}_to_{period_end}"
    statutory_files = {
        "companies_house_accounts_markdown": "companies_house_accounts_draft.md",
        "companies_house_accounts_pdf": "companies_house_accounts_draft.pdf",
        "directors_report_markdown": "directors_report_draft.md",
        "audit_exemption_statement_markdown": "audit_exemption_statement_draft.md",
        "hmrc_tax_computation_markdown": "hmrc_tax_computation_draft.md",
        "hmrc_ct600_draft_json": "hmrc_ct600_draft.json",
        "ct600_box_map_markdown": "ct600_box_map_draft.md",
        "confirmation_statement_readiness_json": "confirmation_statement_readiness.json",
        "confirmation_statement_readiness_markdown": "confirmation_statement_readiness.md",
        "draft_accounts_html": "draft_accounts_readable_not_ixbrl.html",
        "draft_computation_html": "draft_computation_readable_not_ixbrl.html",
        "ixbrl_readiness_note": "ixbrl_readiness_note.md",
    }
    outputs = {}
    for key, filename in statutory_files.items():
        path = write(statutory_dir / filename)
        outputs[key] = {"path": str(path), "exists": True, "bytes": path.stat().st_size}
    write(
        statutory_dir / "statutory_filing_pack_manifest.json",
        json.dumps({"schema_version": "statutory-filing-pack-v1", "outputs": outputs}),
    )
    write(full_manifest_path, json.dumps({"outputs": {}, "statutory_filing_pack": {"outputs": outputs}}))

    manifest = build_accounting_handoff_pack(
        repo_root=tmp_path,
        company_name="Example Ltd",
        company_number=company_number,
        period_start=period_start,
        period_end=period_end,
        raw_data_roots=[raw_root],
        include_default_roots=False,
    )

    assert manifest["readiness"]["ready_for_manual_review"] is True
    assert manifest["readiness"]["ready_for_manual_upload"] is True
    assert manifest["safe_boundaries"]["official_hmrc_submission"] == "manual_only"
    assert Path(manifest["outputs"]["start_here"]).exists()
    assert Path(manifest["outputs"]["manifest"]).exists()
    raw_copies = [item for item in manifest["artifacts"] if item["section"] == "01_raw_evidence"]
    assert raw_copies and Path(raw_copies[0]["destination_path"]).exists()
    ids = {item["id"] for item in manifest["requirements"]}
    assert "companies_house_annual_accounts" in ids
    assert "hmrc_company_tax_return" in ids
    assert "companies_house_confirmation_statement" in ids
    brain = manifest["uk_accounting_requirements_brain"]
    assert brain["schema_version"] == "uk-accounting-requirements-brain-v1"
    assert brain["summary"]["requirement_count"] >= 7
    assert brain["summary"]["question_count"] >= 8
    assert any(item["id"] == "uk.hmrc.vat_registration_and_mtd" for item in brain["requirements"])
    evidence = manifest["accounting_evidence_authoring"]
    assert evidence["schema_version"] == "accounting-evidence-authoring-v1"
    assert evidence["safe_boundaries"]["creates_supplier_receipts"] is False
    output_keys = {item["output_key"] for item in manifest["artifacts"]}
    assert "uk_accounting_requirements_brain_json" in output_keys
    assert "accountant_self_questions_markdown" in output_keys
    assert "accounting_evidence_authoring_manifest" in output_keys
