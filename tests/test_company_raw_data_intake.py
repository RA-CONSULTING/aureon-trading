from __future__ import annotations

import json
from pathlib import Path

from Kings_Accounting_Suite.tools.company_raw_data_intake import (
    build_company_raw_data_manifest,
    write_raw_data_manifest_artifacts,
)


def test_company_raw_data_intake_classifies_all_company_evidence(tmp_path: Path) -> None:
    raw = tmp_path / "client_data"
    raw.mkdir()
    (raw / "Transactions Report MSAGM9YS 20260414.csv").write_text(
        "Transaction date,Transaction code,Reference,Amount,Available balance\n"
        "2024-05-03,FPI,Client receipt,250.00,250.00\n",
        encoding="utf-8",
    )
    (raw / "Statement__GBP_20240501-20240531.pdf").write_text("statement", encoding="utf-8")
    (raw / "INV_001.PDF").write_text("invoice", encoding="utf-8")
    (raw / "receipt.jpg").write_text("image", encoding="utf-8")
    (raw / "director-cash-note.weird").write_text("cash note", encoding="utf-8")

    manifest = build_company_raw_data_manifest(
        tmp_path,
        company_number="NI000001",
        period_start="2024-05-01",
        period_end="2025-04-30",
        raw_roots=[raw],
        include_default_roots=False,
    )

    assert manifest.summary["file_count"] == 5
    assert manifest.summary["transaction_source_count"] == 2
    assert manifest.summary["provider_counts"]["revolut"] == 1
    assert manifest.summary["provider_counts"]["zempler"] == 1
    assert manifest.summary["ingestion_path_counts"]["combined_bank_data"] == 1
    assert manifest.summary["ingestion_path_counts"]["combined_bank_data_pdf_parser"] == 1
    assert manifest.summary["ingestion_path_counts"]["evidence_review"] == 3
    assert "nonstandard_suffix_included_for_no_skip_review" in manifest.summary["warnings"]

    json_path, md_path = write_raw_data_manifest_artifacts(manifest)
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["schema_version"] == "company-raw-data-intake-v1"
    assert "Company Raw Data Intake" in md_path.read_text(encoding="utf-8")
