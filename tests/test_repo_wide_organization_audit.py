import json
from pathlib import Path

from aureon.autonomous.repo_wide_organization_audit import (
    CONTRACT_CHECKS,
    build_audit,
    classify_path,
    render_markdown,
    write_report,
)


def _seed_contract_surfaces(root: Path) -> None:
    for rel_path in CONTRACT_CHECKS.values():
        target = root / rel_path
        if target.suffix:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("# test surface\n", encoding="utf-8")
        else:
            target.mkdir(parents=True, exist_ok=True)


def test_classify_path_maps_core_accounting_frontend_and_raw_data(tmp_path):
    root = tmp_path
    paths = [
        root / "aureon" / "core" / "organism_contracts.py",
        root / "Kings_Accounting_Suite" / "tools" / "generate_full_company_accounts.py",
        root / "frontend" / "src" / "App.tsx",
        root / "bussiness accounts" / "statement.csv",
    ]
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x", encoding="utf-8")

    core = classify_path(paths[0], root)
    accounting = classify_path(paths[1], root)
    frontend = classify_path(paths[2], root)
    raw_data = classify_path(paths[3], root)

    assert core.stage == "01_core_contracts_and_bus"
    assert accounting.stage == "05_accounting_tax_compliance_and_raw_business_data"
    assert frontend.stage == "06_frontend_apis_and_operator_interfaces"
    assert raw_data.domain == "accounting"
    assert "legacy_misspelled_business_data_root_preserved" in raw_data.attention


def test_secret_and_unstaged_paths_are_visible(tmp_path):
    root = tmp_path
    env_file = root / ".env"
    mystery = root / "mystery.bin"
    env_file.write_text("KRAKEN_API_SECRET=hidden\n", encoding="utf-8")
    mystery.write_bytes(b"x")

    env_record = classify_path(env_file, root)
    mystery_record = classify_path(mystery, root)

    assert env_record.secret_risk is True
    assert "secret_or_credential_surface" in env_record.attention
    assert mystery_record.stage == "99_unstaged_or_needs_owner"
    assert "unstaged_path" in mystery_record.attention


def test_build_audit_reports_contract_surfaces_and_attention_items(tmp_path):
    root = tmp_path
    _seed_contract_surfaces(root)
    (root / "mystery.bin").write_bytes(b"x")

    report = build_audit(root)

    assert report.status == "organized_with_attention_items"
    assert report.summary["total_discovered_files"] >= sum(1 for value in CONTRACT_CHECKS.values() if Path(value).suffix)
    assert report.summary["unstaged_file_count"] == 1
    assert all(surface.status == "present" for surface in report.contract_surfaces)
    assert any(surface.id == "boot_ignition" for surface in report.contract_surfaces)


def test_render_and_write_repo_wide_audit(tmp_path):
    root = tmp_path
    _seed_contract_surfaces(root)
    report = build_audit(root)

    markdown = render_markdown(report)
    assert "Aureon Repo-Wide Organization Audit" in markdown
    assert "Organism Stages" in markdown
    assert "boot_ignition" in markdown

    md_path, json_path = write_report(
        report,
        tmp_path / "repo_wide_organization_audit.md",
        tmp_path / "repo_wide_organization_audit.json",
    )

    assert md_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["schema_version"] == "aureon-repo-wide-organization-audit-v1"
    assert "stage_counts" in data
