from __future__ import annotations

import json
from pathlib import Path

from Kings_Accounting_Suite.tools.accounting_system_registry import (
    build_accounting_system_registry,
    write_registry_artifacts,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_accounting_system_registry_discovers_full_accounting_surface() -> None:
    registry = build_accounting_system_registry(REPO_ROOT)
    modules = {entry.module for entry in registry.entries}
    domains = registry.summary["domain_counts"]

    assert registry.schema_version == "accounting-system-registry-v1"
    assert registry.summary["module_count"] >= 25
    assert "Kings_Accounting_Suite.core.hnc_gateway" in modules
    assert "Kings_Accounting_Suite.core.king_ledger" in modules
    assert "Kings_Accounting_Suite.core.king_accounting" in modules
    assert "Kings_Accounting_Suite.tools.combined_bank_data" in modules
    assert "Kings_Accounting_Suite.show_tools.show_portfolio" in modules
    assert "Kings_Accounting_Suite.show_tools.check_system_flow" in modules
    assert "Kings_Accounting_Suite.tools.generate_full_company_accounts" in modules
    assert "Kings_Accounting_Suite.tools.end_user_accounting_automation" in modules
    assert "Kings_Accounting_Suite.aureon_systems.aureon_deep_money_flow_analyzer" in modules
    assert "aureon.analytics.lighthouse_financial_analyzer" in modules
    assert "aureon.trading.compound_king" in modules
    assert domains["accounting_status_tools"] >= 6
    assert domains["financial_analysis"] >= 3
    assert domains["compound_projection"] >= 1
    assert domains["gateway_orchestration"] >= 1
    assert domains["ledger_double_entry"] >= 1
    assert domains["king_accounting"] >= 1
    assert domains["reports_exports"] >= 1
    assert registry.summary["mirrored_module_count"] >= 8
    assert registry.summary["nonstandard_surfaces"]["accounting_vault_memory"] is True
    assert registry.summary["nonstandard_surfaces"]["root_aureon_financial_analytics"] is True
    assert registry.summary["nonstandard_surfaces"]["root_aureon_compound_projection"] is True
    assert registry.combined_bank_data["csv_source_count"] >= 4
    assert registry.combined_bank_data["pdf_source_count"] >= 30
    assert registry.combined_bank_data["transaction_source_count"] >= 30
    assert registry.combined_bank_data["unique_rows_in_period"] >= 1000
    assert "business_gbp_monthly" in registry.combined_bank_data["source_accounts"]
    assert registry.combined_bank_data["source_provider_summary"]["zempler"]["rows"] >= 1000
    assert registry.combined_bank_data["source_provider_summary"]["revolut"]["rows"] >= 20
    assert registry.combined_bank_data["flow_provider_summary"]["sumup"]["rows"] >= 10
    assert registry.safe_boundaries["official_hmrc_submission"] == "manual_only"


def test_accounting_system_registry_writes_machine_and_human_reports(tmp_path: Path) -> None:
    registry = build_accounting_system_registry(REPO_ROOT)
    json_path, md_path = write_registry_artifacts(
        registry,
        json_path=tmp_path / "registry.json",
        markdown_path=tmp_path / "registry.md",
    )

    data = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = md_path.read_text(encoding="utf-8")

    assert data["summary"]["module_count"] == registry.summary["module_count"]
    assert "Accounting System Registry" in markdown
    assert "How The Accounting Organism Works Together" in markdown
    assert "Full Accounts For A Business" in markdown
    assert "Package end-user accounting automation" in markdown
    assert "Bridge nonstandard and mirrored accounting systems" in markdown
    assert "Complete Accounting Module List" in markdown
    assert "Kings_Accounting_Suite/core/hnc_gateway.py" in markdown
    assert "accounting/full_accounts_index.md" in markdown
    assert "Official filing/payment boundary: manual only" in markdown
