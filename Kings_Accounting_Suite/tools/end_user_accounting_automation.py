"""End-user raw-data-to-final-accounts automation for Aureon.

This is the user-facing wrapper around the accounting organism. The end user
provides raw data folders; Aureon runs intake, bank normalisation, final-ready
accounts, Companies House/HMRC manual filing packs, evidence requests, UK
requirement checks, vault memory, and cognitive review.

It never submits Companies House accounts, submits HMRC returns, pays tax, or
creates external evidence. It prepares the full document pack a
human/director/accountant can approve, sign, upload, enter, and file manually.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import textwrap
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Sequence


KAS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = KAS_DIR.parent
TOOLS_DIR = KAS_DIR / "tools"
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(KAS_DIR))
sys.path.insert(0, str(TOOLS_DIR))

from accounting_evidence_authoring import OFFICIAL_EVIDENCE_SOURCES  # noqa: E402
from accounting_swarm_data_wave_scan import (  # noqa: E402
    run_accounting_swarm_data_wave_scan,
    write_end_user_confirmation_artifacts,
    write_logic_chain_artifacts,
)
from autonomous_full_accounts_workflow import run_autonomous_full_accounts_workflow  # noqa: E402
from company_house_tax_audit import (  # noqa: E402
    DEFAULT_COMPANY_NAME,
    DEFAULT_COMPANY_NUMBER,
    DEFAULT_PERIOD_END,
    DEFAULT_PERIOD_START,
)
from generate_statutory_filing_pack import OFFICIAL_REQUIREMENT_SOURCES  # noqa: E402


SAFE_BOUNDARIES = {
    "official_companies_house_filing": "manual_only",
    "official_hmrc_submission": "manual_only",
    "tax_or_penalty_payment": "manual_only",
    "external_receipt_or_invoice_creation": "blocked",
    "exchange_or_trading_mutation": "blocked_from_accounting",
}

FINAL_READY_STATUS = "final_ready_manual_upload_required"


def resolve_desktop_dir() -> Path:
    """Return the Desktop that Windows shows to the user, including OneDrive."""
    userprofile = Path(os.environ.get("USERPROFILE") or str(Path.home()))
    candidates = [
        userprofile / "OneDrive" / "Desktop",
        Path.home() / "OneDrive" / "Desktop",
        Path(os.path.expanduser("~/Desktop")),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[-1]


def run_end_user_accounting_automation(
    *,
    repo_root: str | Path = REPO_ROOT,
    company_name: str = DEFAULT_COMPANY_NAME,
    company_number: str = DEFAULT_COMPANY_NUMBER,
    period_start: str = DEFAULT_PERIOD_START,
    period_end: str = DEFAULT_PERIOD_END,
    as_of: date | None = None,
    raw_data_roots: Sequence[str | Path] | None = None,
    include_default_roots: bool = True,
    no_fetch: bool = True,
    enable_cognitive_review: bool = True,
    desktop_copy: bool = False,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    apply_safe_environment()
    workflow = run_autonomous_full_accounts_workflow(
        repo_root=root,
        company_name=company_name,
        company_number=company_number,
        period_start=period_start,
        period_end=period_end,
        as_of=as_of or date.today(),
        raw_data_roots=raw_data_roots,
        include_default_roots=include_default_roots,
        no_fetch=no_fetch,
        enable_cognitive_review=enable_cognitive_review,
    )
    out_dir = (
        root
        / "Kings_Accounting_Suite"
        / "output"
        / "end_user_accounts"
        / company_number
        / f"{period_start}_to_{period_end}"
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    swarm_scan = run_accounting_swarm_data_wave_scan(
        repo_root=root,
        company_name=company_name,
        company_number=company_number,
        period_start=period_start,
        period_end=period_end,
        raw_data_roots=raw_data_roots,
        include_default_roots=include_default_roots,
        output_dir=out_dir,
    )
    coverage = build_requirement_coverage(workflow, swarm_scan=swarm_scan)
    outputs = collect_end_user_outputs(workflow)
    outputs.update(swarm_scan.get("outputs") or {})
    generated_ready = all(
        item["status"] in {"generated", "generated_ready_manual_review_required", FINAL_READY_STATUS, "manual_required", "eye_scan_required"}
        for item in coverage
    )
    manifest = {
        "schema_version": "end-user-accounting-automation-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed" if workflow.get("status") == "completed" and generated_ready else "partial",
        "company_name": company_name,
        "company_number": company_number,
        "period_start": period_start,
        "period_end": period_end,
        "as_of": (as_of or date.today()).isoformat(),
        "user_input_contract": build_user_input_contract(root, raw_data_roots, include_default_roots),
        "workflow_manifest": workflow,
        "swarm_raw_data_wave_scan": swarm_scan,
        "internal_logic_chain_checklist": swarm_scan.get("internal_logic_chain_checklist") or [],
        "end_user_confirmation": swarm_scan.get("end_user_confirmation") or {},
        "requirement_coverage": coverage,
        "outputs": outputs,
        "official_requirement_sources": {
            **dict(OFFICIAL_REQUIREMENT_SOURCES),
            **dict(OFFICIAL_EVIDENCE_SOURCES),
        },
        "safe_boundaries": dict(SAFE_BOUNDARIES),
        "end_user_next_step": (
            "Open END_USER_START_HERE.md, eye-scan the generated pack for visible issues, then manually upload "
            "or enter the generated Companies House/HMRC document pack."
        ),
    }
    manifest_path = out_dir / "end_user_accounting_automation_manifest.json"
    start_here = out_dir / "END_USER_START_HERE.md"
    manifest["outputs"]["end_user_automation_manifest"] = str(manifest_path)
    manifest["outputs"]["end_user_start_here"] = str(start_here)
    manifest["outputs"].update(write_logic_chain_artifacts(swarm_scan, output_dir=out_dir))
    manifest["outputs"].update(write_end_user_confirmation_artifacts(manifest, output_dir=out_dir))
    manifest["outputs"].update(write_final_filing_readiness_artifacts(manifest, output_dir=out_dir))
    final_readiness = manifest.get("final_filing_readiness_audit") or {}
    manifest["requirement_coverage"].append(
        coverage_item(
            "final_filing_ready_folder_audit",
            "Post-generation audit proving the folder has the manual filing documents and evidence",
            final_readiness.get("status") == FINAL_READY_STATUS,
            (
                f"{final_readiness.get('passed_count', 0)} passed; "
                f"{final_readiness.get('blocked_count', 0)} blocked; "
                f"{final_readiness.get('review_count', 0)} review"
            ),
            ["end_user_accounting_automation", "final_filing_readiness_auditor"],
        )
    )
    if final_readiness.get("status") != FINAL_READY_STATUS:
        manifest["status"] = "partial"
    manifest["outputs"].update(write_end_user_pdf_guides(manifest, output_dir=out_dir))
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True, default=str), encoding="utf-8")
    start_here.write_text(render_end_user_start_here(manifest), encoding="utf-8")
    if desktop_copy:
        desktop_result = publish_desktop_manual_filing_pack(manifest)
        manifest["desktop_manual_filing_pack"] = desktop_result
        if desktop_result.get("status") == "copied":
            manifest["outputs"]["desktop_manual_filing_pack"] = str(desktop_result.get("path") or "")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True, default=str), encoding="utf-8")
    start_here.write_text(render_end_user_start_here(manifest), encoding="utf-8")
    return manifest


def apply_safe_environment() -> None:
    os.environ["AUREON_ACCOUNTING_ON_DEMAND"] = "1"
    os.environ["AUREON_DISABLE_GOVERNMENT_SUBMISSION"] = "1"
    os.environ["AUREON_DISABLE_REAL_ORDERS"] = os.environ.get("AUREON_DISABLE_REAL_ORDERS", "1")
    os.environ["AUREON_LIVE_TRADING"] = os.environ.get("AUREON_LIVE_TRADING", "0")


def build_user_input_contract(
    repo_root: Path,
    raw_data_roots: Sequence[str | Path] | None,
    include_default_roots: bool,
) -> dict[str, Any]:
    roots: list[str] = []
    if include_default_roots:
        roots.extend([str(repo_root / "uploads"), str(repo_root / "bussiness accounts")])
    roots.extend(str(Path(item)) for item in raw_data_roots or [])
    return {
        "raw_data_roots": roots,
        "accepted_file_types": [".csv", ".pdf", ".xlsx", ".xls", ".json", ".jpg", ".jpeg", ".png", ".txt", ".md"],
        "known_provider_patterns": ["sumup", "zempler", "revolut", "hmrc", "companies house"],
        "user_action": "Put bank statements, sales exports, invoices, receipts, HMRC/Companies House evidence, and ledgers into the raw-data roots, then run this automation.",
    }


def build_requirement_coverage(workflow: dict[str, Any], *, swarm_scan: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    raw_summary = ((workflow.get("raw_data_manifest") or {}).get("summary") or {})
    full_run = workflow.get("full_accounts_result") or {}
    full_manifest = full_run.get("manifest") or {}
    source_inventory = full_manifest.get("source_data_inventory") or {}
    combined = source_inventory.get("combined_bank_data") or {}
    outputs = full_manifest.get("outputs") or {}
    statutory = full_manifest.get("statutory_filing_pack") or {}
    statutory_outputs = statutory.get("outputs") or {}
    handoff = workflow.get("human_filing_handoff_pack") or {}
    handoff_outputs = handoff.get("outputs") or {}
    evidence = workflow.get("accounting_evidence_authoring") or {}
    evidence_summary = evidence.get("summary") or {}
    uk_brain = workflow.get("uk_accounting_requirements_brain") or {}
    uk_summary = uk_brain.get("summary") or {}
    uk_outputs = uk_brain.get("outputs") or {}

    swarm_scan = swarm_scan or {}
    consensus = ((swarm_scan.get("waves") or {}).get("phi_swarm_consensus") or {})
    benchmark = swarm_scan.get("benchmark") or {}
    readability = swarm_scan.get("file_readability") or ((swarm_scan.get("waves") or {}).get("file_readability") or {})
    source_closure = swarm_scan.get("source_closure") or ((swarm_scan.get("waves") or {}).get("source_closure") or {})
    return [
        coverage_item(
            "raw_data_intake",
            "User raw data inventory",
            raw_summary.get("file_count", 0) > 0,
            f"{raw_summary.get('file_count', 0)} files, {raw_summary.get('transaction_source_count', 0)} transaction sources",
            ["company_raw_data_intake"],
        ),
        coverage_item(
            "raw_data_swarm_wave_scan",
            "Wave-based swarm scan across all raw-data files",
            swarm_scan.get("status") == "completed",
            (
                f"{benchmark.get('files_scanned', 0)} files swept; "
                f"consensus={consensus.get('status', 'unknown')}; "
                f"score={consensus.get('score', 'n/a')}"
            ),
            ["accounting_swarm_data_wave_scan", "PhiBridge", "swarm_agents"],
        ),
        coverage_item(
            "all_source_file_readability",
            "Autonomous read/extraction audit for every raw source file",
            int(readability.get("readable_file_count", 0) or 0) == int(readability.get("file_count", 0) or 0)
            and int(readability.get("file_count", 0) or 0) > 0,
            (
                f"{readability.get('readable_file_count', 0)} content-readable; "
                f"{readability.get('metadata_only_file_count', 0)} metadata-only/OCR-needed; "
                f"{readability.get('blocked_file_count', 0)} converter-needed; "
                f"ratio={readability.get('readability_ratio', 'n/a')}"
            ),
            ["accounting_swarm_data_wave_scan", "file_readability_agent", "converter_or_ocr_queue"],
        ),
        coverage_item(
            "no_data_skipped_source_closure",
            "No-silent-skip source closure across every candidate accounting file",
            source_closure.get("status") == "closed_no_silent_skips",
            (
                f"{source_closure.get('included_file_count', 0)} included; "
                f"{source_closure.get('excluded_file_count', 0)} excluded with reasons; "
                f"{source_closure.get('missing_root_count', 0)} missing roots; "
                f"{source_closure.get('unaccounted_file_count', 0)} unaccounted"
            ),
            ["accounting_swarm_data_wave_scan", "source_closure_agent", "file_readability_agent"],
        ),
        coverage_item(
            "internal_logic_chain_checklist",
            "Internal checklist and logic-chain observance for the accounting organism",
            bool(swarm_scan.get("internal_logic_chain_checklist")),
            f"{len(swarm_scan.get('internal_logic_chain_checklist') or [])} checklist items",
            ["accounting_swarm_data_wave_scan", "end_user_accounting_automation"],
        ),
        coverage_item(
            "end_user_confirmation_feed",
            "End-user confirmation and observance feed",
            bool(swarm_scan.get("end_user_confirmation")),
            str((swarm_scan.get("end_user_confirmation") or {}).get("status") or "unknown"),
            ["accounting_swarm_data_wave_scan", "end_user_accounting_automation"],
        ),
        coverage_item(
            "combined_transaction_feed",
            "Normalised bank/payment transaction feed",
            combined.get("unique_rows_in_period", 0) > 0,
            f"{combined.get('transaction_source_count', combined.get('csv_source_count', 0))} sources, {combined.get('unique_rows_in_period', 0)} unique rows",
            ["combined_bank_data", "HNCGateway"],
        ),
        coverage_item(
            "final_ready_accounts_pack",
            "Final-ready accounts, ledgers, reports, and management workbooks",
            output_exists(outputs, "accounts_pack_pdf"),
            output_path(outputs, "accounts_pack_pdf"),
            ["generate_full_company_accounts", "build_period_accounts_pack", "HNCGateway"],
        ),
        coverage_item(
            "companies_house_annual_accounts",
            "Companies House accounts support",
            output_exists(statutory_outputs, "companies_house_accounts_pdf"),
            output_path(statutory_outputs, "companies_house_accounts_pdf"),
            ["generate_statutory_filing_pack"],
        ),
        coverage_item(
            "hmrc_company_tax_return",
            "HMRC CT600 data and Company Tax Return support",
            output_exists_any(statutory_outputs, "ct600_manual_entry_json", "hmrc_ct600_draft_json"),
            output_path_any(statutory_outputs, "ct600_manual_entry_json", "hmrc_ct600_draft_json"),
            ["generate_statutory_filing_pack", "KingTax"],
        ),
        coverage_item(
            "hmrc_tax_computation",
            "Corporation Tax computation support",
            output_exists(statutory_outputs, "hmrc_tax_computation_pdf"),
            output_path(statutory_outputs, "hmrc_tax_computation_pdf"),
            ["generate_statutory_filing_pack", "KingTax"],
        ),
        coverage_item(
            "incoming_payer_provenance_and_cis_vat",
            "Incoming payment payer lookup, CIS suffered, VAT taxable turnover, and reverse-charge assurance",
            output_exists(statutory_outputs, "payer_provenance_pdf")
            and output_exists(statutory_outputs, "cis_vat_tax_basis_assurance_pdf"),
            (
                f"{output_path(statutory_outputs, 'payer_provenance_pdf')} | "
                f"{output_path(statutory_outputs, 'cis_vat_tax_basis_assurance_pdf')}"
            ),
            ["accounting_payer_provenance", "generate_statutory_filing_pack", "KingTax", "CISReconciliation"],
        ),
        coverage_item(
            "ixbrl_readiness",
            "Readable accounts/computation HTML and iXBRL readiness note",
            output_exists(statutory_outputs, "ixbrl_readiness_note"),
            output_path(statutory_outputs, "ixbrl_readiness_note"),
            ["generate_statutory_filing_pack"],
        ),
        coverage_item(
            "confirmation_statement_readiness",
            "Companies House confirmation statement readiness",
            output_exists(statutory_outputs, "confirmation_statement_readiness_markdown"),
            output_path(statutory_outputs, "confirmation_statement_readiness_markdown"),
            ["generate_statutory_filing_pack"],
        ),
        coverage_item(
            "evidence_requests_and_workpapers",
            "Autonomous allocation memos and eye-scan workpapers",
            evidence_summary.get("draft_count", 0) > 0,
            f"{evidence_summary.get('draft_count', 0)} system allocation memos, {evidence_summary.get('generated_document_count', 0)} internal documents, {evidence_summary.get('human_data_entry_required_count', 0)} data-entry rows",
            ["accounting_evidence_authoring", "OllamaBridge", "SelfQuestioningAI"],
        ),
        coverage_item(
            "uk_requirement_brain",
            "HMRC/Companies House requirement map and accountant self-questions",
            uk_summary.get("requirement_count", 0) > 0,
            f"{uk_summary.get('requirement_count', 0)} requirements, {uk_summary.get('question_count', 0)} questions",
            ["uk_accounting_requirements_brain", "HNCLawDataset"],
        ),
        coverage_item(
            "expanded_uk_accounting_self_questioning",
            "Expanded UK accounting self-questioning brain, missing-data plan, and contradiction register",
            bool(uk_outputs.get("expanded_accounting_self_questions_pdf"))
            and bool(uk_outputs.get("missing_data_and_evidence_action_plan_pdf"))
            and bool(uk_outputs.get("risk_and_contradiction_register_pdf")),
            (
                f"{uk_summary.get('question_count', 0)} questions; "
                f"open={uk_summary.get('unresolved_question_count', 0)}; "
                f"domains={len(uk_summary.get('question_domain_counts') or {})}"
            ),
            ["uk_accounting_requirements_brain", "SelfQuestioningAI", "ThoughtBus"],
        ),
        coverage_item(
            "human_filing_handoff_pack",
            "End-user filing data room",
            bool(handoff_outputs.get("manifest") or handoff.get("output_dir")),
            str(handoff.get("output_dir") or handoff_outputs.get("manifest") or ""),
            ["accounting_handoff_pack"],
        ),
        eye_scan_item(
            "end_user_eye_scan",
            "End-user eye-scan, declarations, signatures, and final judgement",
            "Aureon generates and allocates the accounts; the user flags only visible issues before legal approval/submission.",
        ),
        manual_item(
            "official_filing_and_payment",
            "Official Companies House filing, HMRC submission, and tax/payment actions",
            "The automation prepares the final-ready local document pack; it does not submit, declare, authenticate, or pay.",
        ),
    ]


def coverage_item(
    requirement_id: str,
    requirement: str,
    ok: bool,
    evidence: str,
    systems: list[str],
) -> dict[str, Any]:
    return {
        "id": requirement_id,
        "requirement": requirement,
        "status": FINAL_READY_STATUS if ok else "missing_or_blocked",
        "evidence": evidence,
        "systems": systems,
        "manual_required": False,
    }


def manual_item(requirement_id: str, requirement: str, evidence: str) -> dict[str, Any]:
    return {
        "id": requirement_id,
        "requirement": requirement,
        "status": "manual_required",
        "evidence": evidence,
        "systems": ["end_user_accounting_automation"],
        "manual_required": True,
    }


def eye_scan_item(requirement_id: str, requirement: str, evidence: str) -> dict[str, Any]:
    return {
        "id": requirement_id,
        "requirement": requirement,
        "status": "eye_scan_required",
        "evidence": evidence,
        "systems": ["end_user_accounting_automation", "accounting_report_enrichment", "accounting_evidence_authoring"],
        "manual_required": False,
        "human_input_role": "eye_scan_and_flag_exceptions_only",
    }


def output_exists(outputs: dict[str, Any], key: str) -> bool:
    item = outputs.get(key) or {}
    if not isinstance(item, dict):
        return False
    if "exists" in item:
        return bool(item.get("exists"))
    path = item.get("path")
    return bool(path and Path(str(path)).exists())


def output_path(outputs: dict[str, Any], key: str) -> str:
    item = outputs.get(key) or {}
    return str(item.get("path") or "") if isinstance(item, dict) else ""


def output_exists_any(outputs: dict[str, Any], *keys: str) -> bool:
    return any(output_exists(outputs, key) for key in keys)


def output_path_any(outputs: dict[str, Any], *keys: str) -> str:
    for key in keys:
        path = output_path(outputs, key)
        if path:
            return path
    return ""


def collect_end_user_outputs(workflow: dict[str, Any]) -> dict[str, str]:
    full_run = workflow.get("full_accounts_result") or {}
    full_manifest = full_run.get("manifest") or {}
    outputs = full_manifest.get("outputs") or {}
    statutory_outputs = ((full_manifest.get("statutory_filing_pack") or {}).get("outputs") or {})
    handoff = workflow.get("human_filing_handoff_pack") or {}
    evidence = workflow.get("accounting_evidence_authoring") or {}
    uk_brain = workflow.get("uk_accounting_requirements_brain") or {}
    uk_outputs = uk_brain.get("outputs") or {}
    collected = {
        "autonomous_workflow_manifest": str(workflow.get("manifest_path") or ""),
        "autonomous_workflow_summary": str(workflow.get("summary_path") or ""),
        "accounts_pack_pdf": output_path(statutory_outputs, "full_accounts_pack_pdf") or output_path(outputs, "accounts_pack_pdf"),
        "management_accounts": output_path(outputs, "management_accounts"),
        "general_ledger": output_path(outputs, "general_ledger"),
        "trial_balance": output_path(outputs, "trial_balance"),
        "profit_and_loss_pdf": output_path(statutory_outputs, "profit_and_loss_detailed_pdf") or output_path(outputs, "profit_and_loss"),
        "tax_summary_pdf": output_path(statutory_outputs, "corporation_tax_summary_pdf") or output_path(outputs, "tax_summary"),
        "companies_house_accounts_pdf": output_path(statutory_outputs, "companies_house_accounts_pdf"),
        "directors_report_pdf": output_path(statutory_outputs, "directors_report_pdf"),
        "hmrc_tax_computation_pdf": output_path(statutory_outputs, "hmrc_tax_computation_pdf"),
        "expense_breakdown_pdf": output_path(statutory_outputs, "expense_breakdown_pdf"),
        "transaction_classification_audit_pdf": output_path(statutory_outputs, "transaction_classification_audit_pdf"),
        "source_reconciliation_pdf": output_path(statutory_outputs, "source_reconciliation_pdf"),
        "data_truth_checklist_pdf": output_path(statutory_outputs, "data_truth_checklist_pdf"),
        "math_stress_test_pdf": output_path(statutory_outputs, "math_stress_test_pdf"),
        "payer_provenance_pdf": output_path(statutory_outputs, "payer_provenance_pdf"),
        "payer_provenance_json": output_path(statutory_outputs, "payer_provenance_json"),
        "payer_provenance_csv": output_path(statutory_outputs, "payer_provenance_csv"),
        "cis_vat_tax_basis_assurance_pdf": output_path(statutory_outputs, "cis_vat_tax_basis_assurance_pdf"),
        "official_template_audit": output_path(statutory_outputs, "official_template_audit_markdown"),
        "enriched_transactions_csv": output_path(statutory_outputs, "enriched_transactions_csv"),
        "ct600_manual_entry_json": output_path_any(statutory_outputs, "ct600_manual_entry_json", "hmrc_ct600_draft_json"),
        "hmrc_ct600_draft_json": output_path_any(statutory_outputs, "hmrc_ct600_draft_json", "ct600_manual_entry_json"),
        "filing_checklist": output_path(statutory_outputs, "filing_checklist"),
        "government_requirements_matrix": output_path(statutory_outputs, "government_requirements_matrix_markdown"),
        "audit_exemption_statement_markdown": output_path(statutory_outputs, "audit_exemption_statement_markdown"),
        "ct600_box_map_markdown": output_path(statutory_outputs, "ct600_box_map_markdown"),
        "supplementary_pages_review_json": output_path(statutory_outputs, "supplementary_pages_review_json"),
        "confirmation_statement_readiness_json": output_path(statutory_outputs, "confirmation_statement_readiness_json"),
        "confirmation_statement_readiness_markdown": output_path(statutory_outputs, "confirmation_statement_readiness_markdown"),
        "accounts_readable_for_ixbrl_html": output_path(statutory_outputs, "accounts_readable_for_ixbrl_html")
        or output_path(statutory_outputs, "draft_accounts_html"),
        "computation_readable_for_ixbrl_html": output_path(statutory_outputs, "computation_readable_for_ixbrl_html")
        or output_path(statutory_outputs, "draft_computation_html"),
        "ixbrl_readiness_note": output_path(statutory_outputs, "ixbrl_readiness_note"),
        "expanded_accounting_self_questions_pdf": str(uk_outputs.get("expanded_accounting_self_questions_pdf") or ""),
        "expanded_accounting_self_questions_json": str(uk_outputs.get("expanded_accounting_self_questions_json") or ""),
        "expanded_accounting_self_questions_csv": str(uk_outputs.get("expanded_accounting_self_questions_csv") or ""),
        "missing_data_and_evidence_action_plan_pdf": str(uk_outputs.get("missing_data_and_evidence_action_plan_pdf") or ""),
        "missing_data_and_evidence_action_plan_json": str(uk_outputs.get("missing_data_and_evidence_action_plan_json") or ""),
        "missing_data_and_evidence_action_plan_csv": str(uk_outputs.get("missing_data_and_evidence_action_plan_csv") or ""),
        "risk_and_contradiction_register_pdf": str(uk_outputs.get("risk_and_contradiction_register_pdf") or ""),
        "risk_and_contradiction_register_json": str(uk_outputs.get("risk_and_contradiction_register_json") or ""),
        "risk_and_contradiction_register_csv": str(uk_outputs.get("risk_and_contradiction_register_csv") or ""),
        "human_filing_handoff_folder": str(handoff.get("output_dir") or ""),
        "human_filing_handoff_manifest": str((handoff.get("outputs") or {}).get("manifest") or ""),
        "human_filing_handoff_start_here": str((handoff.get("outputs") or {}).get("start_here") or ""),
        "evidence_requests_csv": str((evidence.get("outputs") or {}).get("accounting_evidence_requests_csv") or ""),
        "uk_accounting_requirements_brain": str((uk_brain.get("outputs") or {}).get("uk_accounting_requirements_brain_markdown") or ""),
    }
    return {key: value for key, value in collected.items() if value}


def publish_desktop_manual_filing_pack(manifest: dict[str, Any]) -> dict[str, Any]:
    """Copy the generated filing handoff data room to the user's Desktop."""
    outputs = manifest.get("outputs") or {}
    handoff_folder = outputs.get("human_filing_handoff_folder")
    source = Path(str(handoff_folder or ""))
    if not source.exists() or not source.is_dir():
        return {
            "status": "blocked",
            "reason": "handoff_folder_missing",
            "source": str(source) if handoff_folder else "",
        }
    desktop = resolve_desktop_dir()
    desktop.mkdir(parents=True, exist_ok=True)
    destination = desktop / "AUREON_ACCOUNTS_OPEN_THIS_FOLDER"
    handoff_manifest_path = Path(str(outputs.get("human_filing_handoff_manifest") or ""))
    if handoff_manifest_path.exists():
        handoff_manifest = json.loads(handoff_manifest_path.read_text(encoding="utf-8", errors="replace"))
        destination.mkdir(parents=True, exist_ok=True)
        copied = 0
        for artifact in handoff_manifest.get("artifacts") or []:
            if not artifact.get("exists"):
                continue
            src = Path(str(artifact.get("destination_path") or artifact.get("source_path") or ""))
            if not src.exists() or not src.is_file():
                continue
            try:
                rel = src.relative_to(source)
            except ValueError:
                rel = Path(str(artifact.get("section") or "misc")) / src.name
            target = destination / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target)
            copied += 1
        for key in ("manifest", "index", "start_here"):
            path = Path(str((handoff_manifest.get("outputs") or {}).get(key) or ""))
            if path.exists() and path.is_file():
                try:
                    rel = path.relative_to(source)
                except ValueError:
                    rel = Path(path.name)
                target = destination / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
                copied += 1
        copied += copy_end_user_observance_files(manifest, destination)
        return {
            "status": "copied",
            "path": str(destination),
            "source": str(source),
            "artifact_count": copied,
            "manual_upload_only": True,
        }
    shutil.copytree(source, destination)
    copy_end_user_observance_files(manifest, destination)
    return {
        "status": "copied",
        "path": str(destination),
        "source": str(source),
        "artifact_count": "copytree",
        "manual_upload_only": True,
    }


def copy_end_user_observance_files(manifest: dict[str, Any], destination: Path) -> int:
    outputs = manifest.get("outputs") or {}
    target_map = {
        "end_user_start_here": "00_start_here/END_USER_START_HERE.md",
        "end_user_automation_manifest": "00_start_here/end_user_accounting_automation_manifest.json",
        "end_user_confirmation_markdown": "00_start_here/END_USER_CONFIRMATION.md",
        "end_user_confirmation_json": "00_start_here/END_USER_CONFIRMATION.json",
        "internal_logic_chain_checklist_markdown": "07_review_workpapers/internal_logic_chain_checklist.md",
        "internal_logic_chain_checklist_json": "07_review_workpapers/internal_logic_chain_checklist.json",
        "swarm_raw_data_wave_scan_markdown": "07_review_workpapers/swarm_raw_data_wave_scan.md",
        "swarm_raw_data_wave_scan_json": "07_review_workpapers/swarm_raw_data_wave_scan.json",
        "all_source_file_readability_audit_markdown": "07_review_workpapers/all_source_file_readability_audit.md",
        "all_source_file_readability_audit_json": "07_review_workpapers/all_source_file_readability_audit.json",
        "all_source_file_readability_audit_csv": "07_review_workpapers/all_source_file_readability_audit.csv",
        "no_data_skipped_source_closure_audit_markdown": "07_review_workpapers/no_data_skipped_source_closure_audit.md",
        "no_data_skipped_source_closure_audit_json": "07_review_workpapers/no_data_skipped_source_closure_audit.json",
        "no_data_skipped_source_closure_audit_csv": "07_review_workpapers/no_data_skipped_source_closure_audit.csv",
        "final_filing_readiness_audit_markdown": "07_review_workpapers/final_filing_readiness_audit_and_upload_map.md",
        "final_filing_readiness_audit_json": "07_review_workpapers/final_filing_readiness_audit_and_upload_map.json",
        "read_me_first_folder_pdf": "00_READ_ME_FIRST_WHAT_THIS_FOLDER_IS.pdf",
        "full_accounts_pdf_index": "01_FULL_ACCOUNTS_PDF_INDEX.pdf",
        "end_user_confirmation_pdf": "02_END_USER_CONFIRMATION.pdf",
    }
    copied = 0
    for key, rel in target_map.items():
        src = Path(str(outputs.get(key) or ""))
        if not src.exists() or not src.is_file():
            continue
        target = destination / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
        copied += 1
    copied += copy_main_full_account_pdfs(manifest, destination)
    return copied


def copy_main_full_account_pdfs(manifest: dict[str, Any], destination: Path) -> int:
    outputs = manifest.get("outputs") or {}
    pdf_map = {
        "accounts_pack_pdf": "10_FULL_ACCOUNTS_PACK.pdf",
        "companies_house_accounts_pdf": "11_COMPANIES_HOUSE_ACCOUNTS_FINAL_READY.pdf",
        "directors_report_pdf": "12_DIRECTORS_REPORT_FINAL_READY.pdf",
        "hmrc_tax_computation_pdf": "13_HMRC_CORPORATION_TAX_COMPUTATION.pdf",
        "profit_and_loss_pdf": "14_PROFIT_AND_LOSS.pdf",
        "tax_summary_pdf": "15_TAX_SUMMARY.pdf",
        "expense_breakdown_pdf": "16_EXPENSE_BREAKDOWN_AND_ADMIN_COSTS.pdf",
        "transaction_classification_audit_pdf": "17_TRANSACTION_CLASSIFICATION_AUDIT.pdf",
        "source_reconciliation_pdf": "18_SOURCE_RECONCILIATION_SUMUP_ZEMPLER_REVOLUT.pdf",
        "data_truth_checklist_pdf": "19_FULL_DATA_TRUTH_CHECKLIST_AND_BENCHMARK.pdf",
        "math_stress_test_pdf": "20_MATH_STRESS_TEST_AND_RECONCILIATION.pdf",
        "expanded_accounting_self_questions_pdf": "21_EXPANDED_ACCOUNTING_SELF_QUESTIONS.pdf",
        "missing_data_and_evidence_action_plan_pdf": "22_MISSING_DATA_AND_EVIDENCE_ACTION_PLAN.pdf",
        "risk_and_contradiction_register_pdf": "23_RISK_AND_CONTRADICTION_REGISTER.pdf",
        "all_source_file_readability_audit_pdf": "24_ALL_SOURCE_FILE_READABILITY_AUDIT.pdf",
        "no_data_skipped_source_closure_audit_pdf": "25_NO_DATA_SKIPPED_SOURCE_CLOSURE_AUDIT.pdf",
        "final_filing_readiness_audit_pdf": "26_FINAL_FILING_READY_FOLDER_AUDIT_AND_UPLOAD_MAP.pdf",
        "payer_provenance_pdf": "29_INCOMING_PAYMENT_PAYER_PROVENANCE_AND_CIS_LOOKUP.pdf",
        "cis_vat_tax_basis_assurance_pdf": "30_CIS_VAT_TAX_BASIS_ASSURANCE.pdf",
    }
    copied = 0
    for key, filename in pdf_map.items():
        src = Path(str(outputs.get(key) or ""))
        if not src.exists() or not src.is_file():
            continue
        target = destination / filename
        shutil.copy2(src, target)
        copied += 1
    return copied


def write_end_user_pdf_guides(manifest: dict[str, Any], *, output_dir: str | Path) -> dict[str, str]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    folder_pdf = out_dir / "00_READ_ME_FIRST_WHAT_THIS_FOLDER_IS.pdf"
    index_pdf = out_dir / "01_FULL_ACCOUNTS_PDF_INDEX.pdf"
    confirmation_pdf = out_dir / "02_END_USER_CONFIRMATION.pdf"

    pdfs = discover_full_account_pdfs(manifest)
    write_simple_pdf(
        folder_pdf,
        "Read Me First - What This Folder Is",
        build_folder_explainer_lines(manifest, pdfs),
    )
    write_simple_pdf(
        index_pdf,
        "Full Accounts PDF Index",
        build_full_accounts_index_lines(manifest, pdfs),
    )
    write_simple_pdf(
        confirmation_pdf,
        "End-User Confirmation",
        build_confirmation_pdf_lines(manifest),
    )
    return {
        "read_me_first_folder_pdf": str(folder_pdf),
        "full_accounts_pdf_index": str(index_pdf),
        "end_user_confirmation_pdf": str(confirmation_pdf),
    }


def write_final_filing_readiness_artifacts(manifest: dict[str, Any], *, output_dir: str | Path) -> dict[str, str]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = build_final_filing_readiness_audit(manifest)
    manifest["final_filing_readiness_audit"] = payload.get("summary") or {}

    json_path = out_dir / "final_filing_readiness_audit_and_upload_map.json"
    md_path = out_dir / "final_filing_readiness_audit_and_upload_map.md"
    pdf_path = out_dir / "final_filing_readiness_audit_and_upload_map.pdf"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    md_text = render_final_filing_readiness_markdown(payload)
    md_path.write_text(md_text, encoding="utf-8")
    write_simple_pdf(pdf_path, "Final Filing Ready Folder Audit And Upload Map", md_text.splitlines())
    return {
        "final_filing_readiness_audit_json": str(json_path),
        "final_filing_readiness_audit_markdown": str(md_path),
        "final_filing_readiness_audit_pdf": str(pdf_path),
    }


def build_final_filing_readiness_audit(manifest: dict[str, Any]) -> dict[str, Any]:
    outputs = manifest.get("outputs") or {}
    scan = manifest.get("swarm_raw_data_wave_scan") or {}
    closure = scan.get("source_closure") or {}
    readability = scan.get("file_readability") or {}
    checks: list[dict[str, Any]] = []

    checks.extend(
        [
            readiness_file_check(
                "companies_house_accounts",
                "Companies House accounts support PDF",
                outputs.get("companies_house_accounts_pdf"),
                "04_companies_house / 11_COMPANIES_HOUSE_ACCOUNTS_FINAL_READY.pdf",
                required_tokens=("balance sheet", "profit and loss", "notes", "director"),
            ),
            readiness_file_check(
                "directors_report",
                "Directors report PDF",
                outputs.get("directors_report_pdf"),
                "04_companies_house / 12_DIRECTORS_REPORT_FINAL_READY.pdf",
                required_tokens=("directors report", "director", "approval", "date"),
            ),
            readiness_file_check(
                "full_accounts_pack",
                "Full accounts pack PDF",
                outputs.get("accounts_pack_pdf"),
                "03_accounts_workpapers / 10_FULL_ACCOUNTS_PACK.pdf",
                required_tokens=("balance sheet", "profit and loss", "notes", "tax computation", "source"),
            ),
            readiness_file_check(
                "hmrc_tax_computation",
                "HMRC Corporation Tax computation PDF",
                outputs.get("hmrc_tax_computation_pdf"),
                "05_hmrc_corporation_tax / 13_HMRC_CORPORATION_TAX_COMPUTATION.pdf",
                required_tokens=("corporation tax", "taxable", "ct600", "profit before tax"),
            ),
            readiness_file_check(
                "ct600_manual_entry",
                "CT600 manual-entry JSON",
                outputs.get("ct600_manual_entry_json"),
                "05_hmrc_corporation_tax / hmrc_ct600_manual_entry.json",
                json_required=True,
            ),
            readiness_file_check(
                "ct600_box_map",
                "CT600 box map",
                outputs.get("ct600_box_map_markdown"),
                "05_hmrc_corporation_tax / ct600_box_map_final_ready.md",
                required_tokens=("ct600", "turnover", "taxable", "corporation tax"),
            ),
            readiness_file_check(
                "ixbrl_accounts_html",
                "Accounts HTML for iXBRL conversion",
                outputs.get("accounts_readable_for_ixbrl_html"),
                "05_hmrc_corporation_tax / accounts_readable_for_ixbrl.html",
                required_tokens=("accounts", "balance sheet", "profit"),
            ),
            readiness_file_check(
                "ixbrl_computation_html",
                "Computation HTML for iXBRL conversion",
                outputs.get("computation_readable_for_ixbrl_html"),
                "05_hmrc_corporation_tax / computation_readable_for_ixbrl.html",
                required_tokens=("computation", "corporation tax", "taxable"),
            ),
            readiness_file_check(
                "ixbrl_readiness_note",
                "iXBRL readiness note",
                outputs.get("ixbrl_readiness_note"),
                "05_hmrc_corporation_tax / ixbrl_readiness_note.md",
                required_tokens=("ixbrl", "commercial", "software", "manual"),
            ),
            readiness_file_check(
                "profit_and_loss",
                "Detailed profit and loss PDF",
                outputs.get("profit_and_loss_pdf"),
                "03_accounts_workpapers / 14_PROFIT_AND_LOSS.pdf",
                required_tokens=("profit and loss", "turnover", "expense"),
            ),
            readiness_file_check(
                "expense_breakdown",
                "Expense breakdown and admin-cost support PDF",
                outputs.get("expense_breakdown_pdf"),
                "03_accounts_workpapers / 16_EXPENSE_BREAKDOWN_AND_ADMIN_COSTS.pdf",
                required_tokens=("expense", "admin", "category", "system-resolved"),
            ),
            readiness_file_check(
                "source_reconciliation",
                "SumUp/Zempler/Revolut source reconciliation PDF",
                outputs.get("source_reconciliation_pdf"),
                "07_review_workpapers / 18_SOURCE_RECONCILIATION_SUMUP_ZEMPLER_REVOLUT.pdf",
                required_tokens=("sumup", "zempler", "revolut", "reconciliation"),
            ),
            readiness_file_check(
                "payer_provenance",
                "Incoming payment payer provenance and CIS lookup PDF",
                outputs.get("payer_provenance_pdf"),
                "07_review_workpapers / 29_INCOMING_PAYMENT_PAYER_PROVENANCE_AND_CIS_LOOKUP.pdf",
                required_tokens=("incoming payment", "payer provenance", "lookup", "cis"),
            ),
            readiness_file_check(
                "cis_vat_tax_basis",
                "CIS/VAT tax basis assurance PDF",
                outputs.get("cis_vat_tax_basis_assurance_pdf"),
                "07_review_workpapers / 30_CIS_VAT_TAX_BASIS_ASSURANCE.pdf",
                required_tokens=("tax basis", "vat", "cis", "reverse-charge"),
            ),
            readiness_file_check(
                "all_source_readability",
                "All-source readability audit PDF",
                outputs.get("all_source_file_readability_audit_pdf"),
                "07_review_workpapers / 24_ALL_SOURCE_FILE_READABILITY_AUDIT.pdf",
                required_tokens=("files accounted for", "content-readable", "readability ratio"),
            ),
            readiness_file_check(
                "no_data_skipped",
                "No-data-skipped source closure PDF",
                outputs.get("no_data_skipped_source_closure_audit_pdf"),
                "07_review_workpapers / 25_NO_DATA_SKIPPED_SOURCE_CLOSURE_AUDIT.pdf",
                required_tokens=("closed_no_silent_skips", "unaccounted files", "included"),
            ),
            readiness_file_check(
                "evidence_requests",
                "Evidence requests CSV",
                outputs.get("evidence_requests_csv"),
                "07_review_workpapers / evidence_authoring / evidence_requests.csv",
            ),
            readiness_file_check(
                "filing_checklist",
                "Generated filing checklist",
                outputs.get("filing_checklist"),
                "07_review_workpapers / filing_checklist.md",
                required_tokens=("companies house", "hmrc", "ixbrl", "manual"),
            ),
            readiness_file_check(
                "government_requirements_matrix",
                "Government requirements matrix",
                outputs.get("government_requirements_matrix"),
                "07_review_workpapers / government_filing_requirements_matrix.md",
                required_tokens=("companies house", "hmrc"),
            ),
        ]
    )

    handoff_folder = Path(str(outputs.get("human_filing_handoff_folder") or ""))
    raw_evidence_folder = handoff_folder / "01_raw_evidence"
    hmrc_folder = handoff_folder / "05_hmrc_corporation_tax"
    companies_house_folder = handoff_folder / "04_companies_house"
    checks.extend(
        [
            readiness_folder_check("raw_evidence_folder", "Raw evidence folder", raw_evidence_folder, "01_raw_evidence"),
            readiness_folder_check("companies_house_folder", "Companies House folder", companies_house_folder, "04_companies_house"),
            readiness_folder_check("hmrc_folder", "HMRC Corporation Tax folder", hmrc_folder, "05_hmrc_corporation_tax"),
            readiness_value_check(
                "source_closure",
                "No source data silently skipped",
                closure.get("status") == "closed_no_silent_skips"
                and int(closure.get("unaccounted_file_count", 0) or 0) == 0,
                f"{closure.get('included_file_count', 0)} included; {closure.get('unaccounted_file_count', 0)} unaccounted",
                "Use 25_NO_DATA_SKIPPED_SOURCE_CLOSURE_AUDIT.pdf",
            ),
            readiness_value_check(
                "readability",
                "Every included source file is content-readable",
                int(readability.get("readable_file_count", 0) or 0) == int(readability.get("file_count", 0) or 0)
                and int(readability.get("file_count", 0) or 0) > 0,
                f"{readability.get('readable_file_count', 0)} / {readability.get('file_count', 0)} readable",
                "Use 24_ALL_SOURCE_FILE_READABILITY_AUDIT.pdf",
            ),
            readiness_value_check(
                "safe_boundaries",
                "Official submission and payment remain manual only",
                (manifest.get("safe_boundaries") or {}).get("official_hmrc_submission") == "manual_only"
                and (manifest.get("safe_boundaries") or {}).get("official_companies_house_filing") == "manual_only",
                "No automatic HMRC/Companies House filing, tax payment, or trading mutation.",
                "Human/director/accountant must submit/pay manually.",
            ),
        ]
    )

    blocked = [item for item in checks if item.get("status") == "blocked"]
    review = [item for item in checks if item.get("status") == "review"]
    passed = [item for item in checks if item.get("status") == "passed"]
    summary = {
        "schema_version": "final-filing-readiness-audit-v1",
        "status": FINAL_READY_STATUS if not blocked else "blocked_missing_filing_ready_artifact",
        "passed_count": len(passed),
        "review_count": len(review),
        "blocked_count": len(blocked),
        "check_count": len(checks),
        "manual_review_required": False,
        "eye_scan_required": True,
        "autonomous_allocation_enabled": True,
        "human_data_entry_required": False,
        "human_input_role": "eye_scan_and_flag_exceptions_only",
        "manual_submission_required": True,
        "companies_house_ready_for_manual_upload": not any(
            item.get("id") in {"companies_house_accounts", "directors_report", "companies_house_folder"} and item.get("status") == "blocked"
            for item in checks
        ),
        "hmrc_ready_for_manual_software_entry": not any(
            item.get("id") in {
                "hmrc_tax_computation",
                "ct600_manual_entry",
                "ct600_box_map",
                "ixbrl_accounts_html",
                "ixbrl_computation_html",
                "ixbrl_readiness_note",
                "hmrc_folder",
            }
            and item.get("status") == "blocked"
            for item in checks
        ),
    }
    return {
        "schema_version": "final-filing-ready-folder-audit-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "company_name": manifest.get("company_name"),
        "company_number": manifest.get("company_number"),
        "period_start": manifest.get("period_start"),
        "period_end": manifest.get("period_end"),
        "summary": summary,
        "checks": checks,
        "manual_upload_map": build_manual_upload_map(outputs),
        "official_requirement_sources": manifest.get("official_requirement_sources") or {},
        "safe_boundaries": manifest.get("safe_boundaries") or {},
    }


def readiness_file_check(
    check_id: str,
    label: str,
    path_value: Any,
    folder_hint: str,
    *,
    required_tokens: Sequence[str] = (),
    json_required: bool = False,
) -> dict[str, Any]:
    path = Path(str(path_value or ""))
    if not path.exists() or not path.is_file():
        return readiness_value_check(check_id, label, False, "Missing file.", folder_hint)
    status = "passed"
    issues: list[str] = []
    extracted = ""
    if required_tokens:
        extracted = extract_file_text(path).lower()
        missing = [token for token in required_tokens if token.lower() not in extracted]
        if missing:
            status = "blocked"
            issues.append(f"Missing required text markers: {', '.join(missing)}")
    if json_required:
        try:
            json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except Exception as exc:
            status = "blocked"
            issues.append(f"JSON could not be parsed: {type(exc).__name__}: {exc}")
    return {
        "id": check_id,
        "label": label,
        "status": status,
        "path": str(path),
        "folder_hint": folder_hint,
        "bytes": path.stat().st_size,
        "evidence": "Exists and passed content checks." if status == "passed" else "; ".join(issues),
        "next_action": "Use this artifact in the manual filing workflow." if status == "passed" else "Regenerate or repair this artifact before relying on the pack.",
    }


def readiness_folder_check(check_id: str, label: str, path: Path, folder_hint: str) -> dict[str, Any]:
    if not path.exists() or not path.is_dir():
        return readiness_value_check(check_id, label, False, "Missing folder.", folder_hint)
    files = [item for item in path.rglob("*") if item.is_file()]
    return {
        "id": check_id,
        "label": label,
        "status": "passed" if files else "blocked",
        "path": str(path),
        "folder_hint": folder_hint,
        "file_count": len(files),
        "evidence": f"{len(files)} files present.",
        "next_action": "Use the folder as the manual filing/evidence source." if files else "Regenerate the handoff pack.",
    }


def readiness_value_check(check_id: str, label: str, ok: bool, evidence: str, next_action: str) -> dict[str, Any]:
    return {
        "id": check_id,
        "label": label,
        "status": "passed" if ok else "blocked",
        "evidence": evidence,
        "next_action": next_action,
    }


def extract_file_text(path: Path) -> str:
    try:
        if path.suffix.lower() == ".pdf":
            from pypdf import PdfReader  # type: ignore

            reader = PdfReader(str(path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        if path.suffix.lower() in {".html", ".htm", ".md", ".txt", ".json", ".csv"}:
            return path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return f"EXTRACTION_ERROR {type(exc).__name__}: {exc}"
    return ""


def build_manual_upload_map(outputs: dict[str, str]) -> list[dict[str, Any]]:
    return [
        {
            "step": 1,
            "portal_or_tool": "Companies House manual accounts filing",
            "folder": "04_companies_house",
            "use_files": [
                outputs.get("companies_house_accounts_pdf", ""),
                outputs.get("directors_report_pdf", ""),
                outputs.get("audit_exemption_statement_markdown", ""),
            ],
            "human_action": "Eye-scan for obvious issues, approve/sign, confirm filing route and exemptions, then manually upload or enter accounts.",
        },
        {
            "step": 2,
            "portal_or_tool": "HMRC Corporation Tax / commercial filing software",
            "folder": "05_hmrc_corporation_tax",
            "use_files": [
                outputs.get("hmrc_tax_computation_pdf", ""),
                outputs.get("ct600_manual_entry_json", ""),
                outputs.get("ct600_box_map_markdown", ""),
                outputs.get("accounts_readable_for_ixbrl_html", ""),
                outputs.get("computation_readable_for_ixbrl_html", ""),
                outputs.get("ixbrl_readiness_note", ""),
            ],
            "human_action": "Eye-scan figures, enter/import CT600 and computation data, generate/validate iXBRL where required, then submit manually.",
        },
        {
            "step": 3,
            "portal_or_tool": "Evidence and review data room",
            "folder": "01_raw_evidence, 02_data_and_workpapers, 07_review_workpapers",
            "use_files": [
                outputs.get("all_source_file_readability_audit_pdf", ""),
                outputs.get("no_data_skipped_source_closure_audit_pdf", ""),
                outputs.get("source_reconciliation_pdf", ""),
                outputs.get("evidence_requests_csv", ""),
            ],
            "human_action": "Keep these as support evidence; eye-scan flags are exception checks, not data-entry tasks.",
        },
    ]


def render_final_filing_readiness_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Final Filing Ready Folder Audit And Upload Map",
        "",
        f"- Company: `{payload.get('company_number')}` {payload.get('company_name')}",
        f"- Period: `{payload.get('period_start')}` to `{payload.get('period_end')}`",
        f"- Status: `{summary.get('status', 'unknown')}`",
        f"- Checks: `{summary.get('passed_count', 0)}` passed, `{summary.get('review_count', 0)}` review, `{summary.get('blocked_count', 0)}` blocked",
        f"- Companies House ready for manual upload: `{summary.get('companies_house_ready_for_manual_upload', False)}`",
        f"- HMRC ready for manual software entry: `{summary.get('hmrc_ready_for_manual_software_entry', False)}`",
        f"- Autonomous accounting allocation enabled: `{summary.get('autonomous_allocation_enabled', True)}`",
        f"- Human data-entry required: `{summary.get('human_data_entry_required', False)}`",
        f"- Human input role: `{summary.get('human_input_role', 'eye_scan_and_flag_exceptions_only')}`",
        "",
        "## Manual Upload Map",
        "",
    ]
    for item in payload.get("manual_upload_map") or []:
        lines.append(f"### Step {item.get('step')}: {item.get('portal_or_tool')}")
        lines.append(f"- Folder: `{item.get('folder')}`")
        lines.append(f"- Human action: {item.get('human_action')}")
        for file_path in item.get("use_files") or []:
            if file_path:
                lines.append(f"- Use: `{file_path}`")
        lines.append("")
    lines.extend(["## Readiness Checks", ""])
    for item in payload.get("checks") or []:
        lines.append(f"- `{item.get('id')}`: {item.get('status')} - {item.get('evidence')}")
        if item.get("folder_hint"):
            lines.append(f"  - Folder/use: `{item.get('folder_hint')}`")
    lines.extend(
        [
            "",
            "## Official Requirement Anchors",
            "",
            "- GOV.UK annual accounts: statutory accounts include balance sheet, profit and loss, notes, and director report checks.",
            "- GOV.UK Company Tax Return guidance: CT600 support must reconcile to company accounts and computations.",
            "- HMRC iXBRL/commercial-software handoff remains manual and outside this local generator.",
            "",
            "## Safety",
            "",
            "- This folder was generated locally only.",
            "- No Companies House filing was submitted.",
            "- No HMRC return was submitted.",
            "- No tax, penalty, or filing fee was paid.",
            "- Human input is limited to eye-scan exception flagging plus legal approval/signature, portal upload/entry, submission, and payment.",
            "",
        ]
    )
    return "\n".join(lines)


def discover_full_account_pdfs(manifest: dict[str, Any]) -> list[dict[str, str]]:
    outputs = manifest.get("outputs") or {}
    handoff_root = Path(str(outputs.get("human_filing_handoff_folder") or ""))
    records: list[dict[str, str]] = []

    if handoff_root.exists() and handoff_root.is_dir():
        for path in sorted(handoff_root.rglob("*.pdf"), key=lambda item: str(item).lower()):
            try:
                rel = str(path.relative_to(handoff_root)).replace("\\", "/")
            except ValueError:
                rel = path.name
            if not include_in_pdf_index(path.name, rel):
                continue
            records.append(
                {
                    "name": path.name,
                    "role": role_for_pdf(path.name, rel),
                    "source_path": str(path),
                    "desktop_relative_path": rel,
                }
            )

    seen = {record["source_path"].lower() for record in records}
    for key, value in sorted(outputs.items()):
        if not str(value).lower().endswith(".pdf"):
            continue
        path = Path(str(value))
        if not path.exists() or str(path).lower() in seen:
            continue
        records.append(
            {
                "name": path.name,
                "role": role_for_pdf(path.name, key),
                "source_path": str(path),
                "desktop_relative_path": path.name,
            }
        )
    priority = {
        "full_accounts_pack": 0,
        "companies_house_accounts": 1,
        "directors_report": 2,
        "hmrc_tax_computation": 3,
        "profit_and_loss": 4,
        "tax_summary": 5,
        "expense_breakdown": 6,
        "classification_audit": 7,
        "source_reconciliation": 8,
        "data_truth_checklist": 9,
        "math_stress_test": 10,
        "expanded_self_questions": 11,
        "missing_data_action_plan": 12,
        "risk_contradiction_register": 13,
        "file_readability_audit": 14,
        "source_closure_audit": 15,
        "final_filing_readiness_audit": 16,
        "raw_statement_or_evidence": 17,
    }
    records = dedupe_pdf_records(records)
    return sorted(records, key=lambda item: (priority.get(item["role"], 9), item["desktop_relative_path"].lower()))


def dedupe_pdf_records(records: list[dict[str, str]]) -> list[dict[str, str]]:
    generated_roles = {
        "full_accounts_pack",
        "companies_house_accounts",
        "directors_report",
        "hmrc_tax_computation",
        "profit_and_loss",
        "tax_summary",
        "expense_breakdown",
        "classification_audit",
        "source_reconciliation",
        "data_truth_checklist",
        "math_stress_test",
        "expanded_self_questions",
        "missing_data_action_plan",
        "risk_contradiction_register",
        "file_readability_audit",
        "source_closure_audit",
        "final_filing_readiness_audit",
    }
    preferred_tokens = {
        "full_accounts_pack": ("full_accounts_pack.pdf",),
        "companies_house_accounts": ("companies_house_accounts_final_ready.pdf",),
        "directors_report": ("directors_report_final_ready.pdf",),
        "hmrc_tax_computation": ("hmrc_tax_computation_final_ready.pdf",),
        "profit_and_loss": ("profit_and_loss_detailed.pdf",),
        "tax_summary": ("corporation_tax_summary.pdf",),
        "expense_breakdown": ("expense_breakdown_and_admin_costs.pdf",),
        "classification_audit": ("transaction_classification_audit.pdf",),
        "source_reconciliation": ("source_reconciliation_sumup_zempler_revolut.pdf",),
        "data_truth_checklist": ("data_truth_checklist_and_benchmark.pdf",),
        "math_stress_test": ("math_stress_test_and_reconciliation.pdf",),
        "expanded_self_questions": ("21_expanded_accounting_self_questions.pdf", "expanded_accounting_self_questions.pdf"),
        "missing_data_action_plan": ("22_missing_data_and_evidence_action_plan.pdf", "missing_data_and_evidence_action_plan.pdf"),
        "risk_contradiction_register": ("23_risk_and_contradiction_register.pdf", "risk_and_contradiction_register.pdf"),
        "file_readability_audit": ("24_all_source_file_readability_audit.pdf", "all_source_file_readability_audit.pdf"),
        "source_closure_audit": ("25_no_data_skipped_source_closure_audit.pdf", "no_data_skipped_source_closure_audit.pdf"),
        "final_filing_readiness_audit": ("26_final_filing_ready_folder_audit_and_upload_map.pdf", "final_filing_readiness_audit_and_upload_map.pdf"),
    }
    chosen: dict[str, dict[str, str]] = {}
    output: list[dict[str, str]] = []
    for record in records:
        role = record.get("role", "")
        if role not in generated_roles:
            output.append(record)
            continue
        current = chosen.get(role)
        if current is None or pdf_record_score(record, preferred_tokens.get(role, ())) < pdf_record_score(current, preferred_tokens.get(role, ())):
            chosen[role] = record
    output.extend(chosen.values())
    return output


def pdf_record_score(record: dict[str, str], preferred_tokens: tuple[str, ...]) -> int:
    rel = record.get("desktop_relative_path", "").lower()
    name = record.get("name", "").lower()
    score = len(rel)
    if any(token in name or token in rel for token in preferred_tokens):
        score -= 1000
    if "07_review_workpapers" in rel:
        score += 100
    if "03_accounts_workpapers" in rel:
        score += 50
    return score


def include_in_pdf_index(name: str, rel: str) -> bool:
    text = f"{name} {rel}".lower()
    if "01_raw_evidence" in text:
        return True
    if "draft" in text:
        return False
    if re.search(r"_(2|3|4|5|6|7|8|9)\.(pdf|html|md|json)$", name.lower()):
        return False
    return True


def role_for_pdf(name: str, context: str = "") -> str:
    text = f"{name} {context}".lower()
    if "accounts_pack" in text or "full_accounts" in text or "ra_consulting" in text:
        return "full_accounts_pack"
    if "companies_house_accounts" in text:
        return "companies_house_accounts"
    if "directors_report" in text:
        return "directors_report"
    if "tax_computation" in text:
        return "hmrc_tax_computation"
    if "pnl" in text or "profit" in text:
        return "profit_and_loss"
    if "tax_summary" in text:
        return "tax_summary"
    if "expense_breakdown" in text or "admin_costs" in text:
        return "expense_breakdown"
    if "classification_audit" in text or "transaction_classification" in text:
        return "classification_audit"
    if "source_reconciliation" in text or "sumup_zempler_revolut" in text:
        return "source_reconciliation"
    if "payer_provenance" in text or "incoming_payment_payer" in text:
        return "payer_provenance"
    if "cis_vat_tax_basis" in text or "vat_tax_basis" in text:
        return "cis_vat_tax_basis"
    if "data_truth_checklist" in text or "truth_checklist" in text:
        return "data_truth_checklist"
    if "math_stress_test" in text or "stress_test_and_reconciliation" in text:
        return "math_stress_test"
    if "expanded_accounting_self_questions" in text or "expanded_self_questions" in text:
        return "expanded_self_questions"
    if "missing_data_and_evidence_action_plan" in text:
        return "missing_data_action_plan"
    if "risk_and_contradiction_register" in text:
        return "risk_contradiction_register"
    if "all_source_file_readability_audit" in text or "file_readability" in text:
        return "file_readability_audit"
    if "no_data_skipped_source_closure" in text or "source_closure" in text:
        return "source_closure_audit"
    if "final_filing_ready_folder" in text or "final_filing_readiness" in text or "upload_map" in text:
        return "final_filing_readiness_audit"
    if "statement" in text or "raw_evidence" in text:
        return "raw_statement_or_evidence"
    return "supporting_pdf"


def build_folder_explainer_lines(manifest: dict[str, Any], pdfs: list[dict[str, str]]) -> list[str]:
    confirmation = manifest.get("end_user_confirmation") or {}
    return [
        "This folder is the Aureon final-ready manual filing pack.",
        f"Company: {manifest.get('company_number')} {manifest.get('company_name')}",
        f"Period: {manifest.get('period_start')} to {manifest.get('period_end')}",
        f"Pack status: {manifest.get('status')}",
        "",
        "What is inside:",
        "1. Full accounts PDFs and tax PDFs for eye-scan.",
        "2. Companies House accounts support documents.",
        "3. HMRC corporation tax computation and CT600 manual-entry data.",
        "4. Raw bank/payment evidence from SumUp, Zempler, Revolut and uploaded files.",
        "5. Workpapers, autonomous allocation memos, internal logic chain, and swarm scan benchmark.",
        "",
        "Important safety boundary:",
        "Aureon prepared local documents only. It did not submit to Companies House, submit to HMRC, pay tax, pay penalties, or authenticate to government services.",
        "Human input is limited to eye-scan exception flagging plus legal approval/signature, portal upload/entry, submission, and payment.",
        "",
        "Start with these PDFs in the top of the folder:",
        "00_READ_ME_FIRST_WHAT_THIS_FOLDER_IS.pdf",
        "01_FULL_ACCOUNTS_PDF_INDEX.pdf",
        "02_END_USER_CONFIRMATION.pdf",
        "10_FULL_ACCOUNTS_PACK.pdf",
        "11_COMPANIES_HOUSE_ACCOUNTS_FINAL_READY.pdf",
        "13_HMRC_CORPORATION_TAX_COMPUTATION.pdf",
        "16_EXPENSE_BREAKDOWN_AND_ADMIN_COSTS.pdf",
        "17_TRANSACTION_CLASSIFICATION_AUDIT.pdf",
        "18_SOURCE_RECONCILIATION_SUMUP_ZEMPLER_REVOLUT.pdf",
        "19_FULL_DATA_TRUTH_CHECKLIST_AND_BENCHMARK.pdf",
        "20_MATH_STRESS_TEST_AND_RECONCILIATION.pdf",
        "21_EXPANDED_ACCOUNTING_SELF_QUESTIONS.pdf",
        "22_MISSING_DATA_AND_EVIDENCE_ACTION_PLAN.pdf",
        "23_RISK_AND_CONTRADICTION_REGISTER.pdf",
        "24_ALL_SOURCE_FILE_READABILITY_AUDIT.pdf",
        "25_NO_DATA_SKIPPED_SOURCE_CLOSURE_AUDIT.pdf",
        "26_FINAL_FILING_READY_FOLDER_AUDIT_AND_UPLOAD_MAP.pdf",
        "29_INCOMING_PAYMENT_PAYER_PROVENANCE_AND_CIS_LOOKUP.pdf",
        "30_CIS_VAT_TAX_BASIS_ASSURANCE.pdf",
        "",
        f"End-user confirmation status: {confirmation.get('status', 'unknown')}",
        f"Total PDFs found in handoff/source pack: {len(pdfs)}",
    ]


def build_full_accounts_index_lines(manifest: dict[str, Any], pdfs: list[dict[str, str]]) -> list[str]:
    lines = [
        "These are the PDFs Aureon generated or gathered for the accounts pack.",
        f"Company: {manifest.get('company_number')} {manifest.get('company_name')}",
        f"Period: {manifest.get('period_start')} to {manifest.get('period_end')}",
        "",
        "Main PDFs copied to the top of the Desktop folder:",
        "10_FULL_ACCOUNTS_PACK.pdf - full accounts pack.",
        "11_COMPANIES_HOUSE_ACCOUNTS_FINAL_READY.pdf - Companies House accounts support.",
        "12_DIRECTORS_REPORT_FINAL_READY.pdf - directors report.",
        "13_HMRC_CORPORATION_TAX_COMPUTATION.pdf - corporation tax computation.",
        "14_PROFIT_AND_LOSS.pdf - profit and loss report.",
        "15_TAX_SUMMARY.pdf - limited-company Corporation Tax and CT600 summary.",
        "16_EXPENSE_BREAKDOWN_AND_ADMIN_COSTS.pdf - expense categories and admin-cost support.",
        "17_TRANSACTION_CLASSIFICATION_AUDIT.pdf - Soup Kitchen, Auris, validator, and autonomous eye-scan queue.",
        "18_SOURCE_RECONCILIATION_SUMUP_ZEMPLER_REVOLUT.pdf - SumUp, Zempler, Revolut reconciliation.",
        "19_FULL_DATA_TRUTH_CHECKLIST_AND_BENCHMARK.pdf - internal questions, data locations, and truth benchmark.",
        "20_MATH_STRESS_TEST_AND_RECONCILIATION.pdf - arithmetic stress test and category reconciliation.",
        "21_EXPANDED_ACCOUNTING_SELF_QUESTIONS.pdf - expanded UK accounting self-questioning brain.",
        "22_MISSING_DATA_AND_EVIDENCE_ACTION_PLAN.pdf - open data, evidence, secret-input, and eye-scan actions.",
        "23_RISK_AND_CONTRADICTION_REGISTER.pdf - HMRC, Companies House, and contrary-review challenge register.",
        "24_ALL_SOURCE_FILE_READABILITY_AUDIT.pdf - every raw source file's extractor/readability/OCR/converter status.",
        "25_NO_DATA_SKIPPED_SOURCE_CLOSURE_AUDIT.pdf - proof every candidate source file was included or explicitly excluded with a reason.",
        "26_FINAL_FILING_READY_FOLDER_AUDIT_AND_UPLOAD_MAP.pdf - final Companies House/HMRC/iXBRL/evidence readiness and upload map.",
        "29_INCOMING_PAYMENT_PAYER_PROVENANCE_AND_CIS_LOOKUP.pdf - every incoming payment, lookup trigger, public-register status, and payer evidence.",
        "30_CIS_VAT_TAX_BASIS_ASSURANCE.pdf - CIS suffered, VAT taxable turnover, and reverse-charge assurance.",
        "",
        "PDF inventory:",
    ]
    for item in pdfs:
        lines.append(f"- {item['role']}: {item['desktop_relative_path']}")
    return lines


def build_confirmation_pdf_lines(manifest: dict[str, Any]) -> list[str]:
    confirmation = manifest.get("end_user_confirmation") or {}
    scan = manifest.get("swarm_raw_data_wave_scan") or {}
    benchmark = scan.get("benchmark") or {}
    consensus = ((scan.get("waves") or {}).get("phi_swarm_consensus") or {})
    lines = [
        "Aureon accounting confirmation for the end user.",
        f"Company: {manifest.get('company_number')} {manifest.get('company_name')}",
        f"Period: {manifest.get('period_start')} to {manifest.get('period_end')}",
        f"Confirmation status: {confirmation.get('status', 'unknown')}",
        "",
        "What Aureon confirmed:",
    ]
    for item in confirmation.get("what_aureon_confirmed") or []:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            f"Swarm files scanned: {benchmark.get('files_scanned', 0)}",
            f"Swarm benchmark: {benchmark.get('total_duration_seconds', 0)} seconds, {benchmark.get('files_per_second', 0)} files/sec",
            f"Phi/swarm consensus: {consensus.get('status', 'unknown')} score={consensus.get('score', 'n/a')}",
            "",
            "Manual actions left:",
        ]
    )
    for item in confirmation.get("human_actions_left") or []:
        lines.append(f"- {item}")
    lines.extend(["", "No external actions were taken:"])
    for item in confirmation.get("no_external_actions_taken") or []:
        lines.append(f"- {item}")
    return lines


def write_simple_pdf(path: Path, title: str, lines: Sequence[str]) -> bool:
    try:
        from pdf_markdown_renderer import render_markdown_pdf
    except Exception:
        return False
    return render_markdown_pdf(path, title, list(lines))


def render_end_user_start_here(manifest: dict[str, Any]) -> str:
    outputs = manifest.get("outputs") or {}
    lines = [
        "# End-User Accounting Automation",
        "",
        "Raw data in -> accounts pack out.",
        "",
        f"- Company: {manifest.get('company_number')} {manifest.get('company_name')}",
        f"- Period: {manifest.get('period_start')} to {manifest.get('period_end')}",
        f"- Status: {manifest.get('status')}",
        "",
        "## What Aureon Did",
        "",
    ]
    for item in manifest.get("requirement_coverage") or []:
        lines.append(f"- `{item.get('id')}`: {item.get('status')} - {item.get('evidence')}")
    lines.extend(
        [
            "",
            "## Main Outputs",
            "",
        ]
    )
    for key, value in sorted(outputs.items()):
        lines.append(f"- {key}: `{value}`")
    confirmation = manifest.get("end_user_confirmation") or {}
    if confirmation:
        lines.extend(["", "## End-User Confirmation", ""])
        for item in confirmation.get("what_aureon_confirmed") or []:
            lines.append(f"- {item}")
    scan = manifest.get("swarm_raw_data_wave_scan") or {}
    if scan:
        benchmark = scan.get("benchmark") or {}
        consensus = ((scan.get("waves") or {}).get("phi_swarm_consensus") or {})
        lines.extend(
            [
                "",
                "## Swarm Wave Scan",
                "",
                f"- Files scanned: {benchmark.get('files_scanned', 0)}",
                f"- Benchmark: {benchmark.get('total_duration_seconds', 0)} seconds; {benchmark.get('files_per_second', 0)} files/sec",
                f"- Consensus: {consensus.get('status', 'unknown')} score={consensus.get('score', 'n/a')}",
            ]
        )
    lines.extend(
        [
            "",
            "## End-User Input Contract",
            "",
            f"- Raw data roots: {', '.join((manifest.get('user_input_contract') or {}).get('raw_data_roots') or [])}",
            f"- Accepted file types: {', '.join((manifest.get('user_input_contract') or {}).get('accepted_file_types') or [])}",
            "",
            "## Safety",
            "",
            "- No Companies House filing was submitted.",
            "- No HMRC return was submitted.",
            "- No tax, penalty, or filing fee was paid.",
            "- Generated receipts/invoices/workpapers are internal support documents and autonomous allocation memos only.",
            "- Human input is limited to eye-scan exception flagging plus official filing/submission/payment steps.",
            "",
            "## Next Step",
            "",
            str(manifest.get("end_user_next_step") or ""),
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run end-user raw-data-to-accounts automation.")
    parser.add_argument("--company-name", default=DEFAULT_COMPANY_NAME)
    parser.add_argument("--company-number", default=DEFAULT_COMPANY_NUMBER)
    parser.add_argument("--period-start", default=DEFAULT_PERIOD_START)
    parser.add_argument("--period-end", default=DEFAULT_PERIOD_END)
    parser.add_argument("--as-of", default=date.today().isoformat())
    parser.add_argument("--raw-data-dir", action="append", default=[])
    parser.add_argument("--no-default-roots", action="store_true")
    parser.add_argument("--no-fetch", action="store_true", default=True)
    parser.add_argument("--skip-cognitive-review", action="store_true")
    parser.add_argument("--desktop-copy", action="store_true", help="Copy the final-ready manual filing pack to the Desktop.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = run_end_user_accounting_automation(
        company_name=args.company_name,
        company_number=args.company_number,
        period_start=args.period_start,
        period_end=args.period_end,
        as_of=date.fromisoformat(args.as_of),
        raw_data_roots=args.raw_data_dir,
        include_default_roots=not args.no_default_roots,
        no_fetch=args.no_fetch,
        enable_cognitive_review=not args.skip_cognitive_review,
        desktop_copy=args.desktop_copy,
    )
    print((manifest.get("outputs") or {}).get("end_user_automation_manifest", ""))
    print((manifest.get("outputs") or {}).get("end_user_start_here", ""))
    return 0 if manifest.get("status") == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
