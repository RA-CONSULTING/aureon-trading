from __future__ import annotations

from datetime import date
from pathlib import Path

from Kings_Accounting_Suite.tools import generate_full_company_accounts as full_accounts


def test_full_accounts_manifest_tracks_outputs_and_safety(tmp_path: Path, monkeypatch) -> None:
    fake_kas = tmp_path / "Kings_Accounting_Suite"
    pack_dir = fake_kas / "output" / "gateway" / "2024-05-01_to_2025-04-30"
    pack_dir.mkdir(parents=True)
    for name in [
        "ra_consulting_and_brokerage_accounts_pack_2024-05-01_to_2025-04-30.pdf",
        "management_accounts.xlsx",
        "general_ledger.xlsx",
        "trial_balance.xlsx",
        "pnl.pdf",
        "tax_summary.pdf",
        "period_pack_manifest.json",
    ]:
        (pack_dir / name).write_text("x", encoding="utf-8")

    audit_json = tmp_path / "audit.json"
    audit_md = tmp_path / "audit.md"
    audit_json.write_text("{}", encoding="utf-8")
    audit_md.write_text("# audit", encoding="utf-8")

    monkeypatch.setattr(full_accounts, "KAS_DIR", fake_kas)

    manifest = full_accounts.build_manifest(
        company_number="00000000",
        period_start="2024-05-01",
        period_end="2025-04-30",
        as_of=date(2026, 5, 8),
        accounts_build_exit_code=0,
        audit_json=audit_json,
        audit_md=audit_md,
        source_inventory=full_accounts.SourceDataInventory(
            uploads_dir=str(tmp_path / "uploads"),
            business_accounts_dir=str(tmp_path / "bussiness accounts"),
            csv_files=[],
            evidence_files=[],
        ),
    )

    assert manifest["accounts_build"]["status"] == "completed"
    assert manifest["outputs"]["accounts_pack_pdf"]["exists"] is True
    assert manifest["outputs"]["compliance_audit_json"]["exists"] is True
    assert manifest["safety"]["submits_to_companies_house"] is False
    assert manifest["safety"]["submits_to_hmrc"] is False
    assert manifest["safety"]["requires_director_or_accountant_review"] is True
