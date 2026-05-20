"""Build a final-ready manual filing handoff pack from all local accounting data.

The handoff pack is the data-room layer: it copies relevant raw evidence,
combined transaction files, generated accounts, statutory/HMRC support files,
confirmation-statement readiness, workpapers, manifests, and review prompts into
one folder for a director/accountant/user to approve, sign, upload, enter, and
file manually.

It does not submit to Companies House, submit to HMRC, make payments, or mutate
bank/trading state.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence


KAS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = KAS_DIR.parent
TOOLS_DIR = KAS_DIR / "tools"
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(KAS_DIR))
sys.path.insert(0, str(TOOLS_DIR))

from company_house_tax_audit import (  # noqa: E402
    DEFAULT_COMPANY_NAME,
    DEFAULT_COMPANY_NUMBER,
    DEFAULT_PERIOD_END,
    DEFAULT_PERIOD_START,
)
from company_raw_data_intake import (  # noqa: E402
    build_company_raw_data_manifest,
    write_raw_data_manifest_artifacts,
)
from accounting_evidence_authoring import build_accounting_evidence_authoring_pack  # noqa: E402
from generate_statutory_filing_pack import OFFICIAL_REQUIREMENT_SOURCES  # noqa: E402
from uk_accounting_requirements_brain import (  # noqa: E402
    UK_ACCOUNTING_OFFICIAL_SOURCES,
    build_uk_accounting_requirements_brain,
    write_uk_accounting_brain_artifacts,
)


SAFE_BOUNDARIES = {
    "official_companies_house_filing": "manual_only",
    "official_hmrc_submission": "manual_only",
    "tax_or_penalty_payment": "manual_only",
    "external_bank_payment": "manual_only",
    "exchange_or_trading_mutation": "blocked_from_accounting_handoff",
    "generated_internal_documents_are_external_evidence": False,
    "raw_source_evidence_overwrite": "blocked",
}

FINAL_READY_STATUS = "final_ready_manual_upload_required"
FINAL_READY_ALIAS_KEYS = {
    "companies_house_accounts_markdown": "companies_house_accounts_final_ready_markdown",
    "companies_house_accounts_pdf": "companies_house_accounts_final_ready_pdf",
    "directors_report_markdown": "directors_report_final_ready_markdown",
    "directors_report_pdf": "directors_report_final_ready_pdf",
    "audit_exemption_statement_markdown": "audit_exemption_statement_final_ready_markdown",
    "hmrc_tax_computation_markdown": "hmrc_tax_computation_final_ready_markdown",
    "hmrc_tax_computation_pdf": "hmrc_tax_computation_final_ready_pdf",
    "hmrc_ct600_draft_json": "ct600_manual_entry_json",
    "ct600_box_map_markdown": "ct600_box_map_final_ready_markdown",
    "draft_accounts_html": "accounts_readable_for_ixbrl_html",
    "draft_computation_html": "computation_readable_for_ixbrl_html",
}


@dataclass
class HandoffArtifact:
    id: str
    section: str
    label: str
    role: str
    source_path: str
    destination_path: str
    exists: bool
    bytes: int = 0
    output_key: str = ""
    required_for: list[str] = field(default_factory=list)
    manual_review_required: bool = True
    notes: str = ""


@dataclass
class HandoffRequirement:
    id: str
    authority: str
    form_or_task: str
    status: str
    generated_artifacts: list[str]
    missing_artifacts: list[str]
    manual_inputs: list[str]
    official_sources: list[str]
    notes: str = ""


def build_accounting_handoff_pack(
    *,
    repo_root: str | Path = REPO_ROOT,
    company_name: str = DEFAULT_COMPANY_NAME,
    company_number: str = DEFAULT_COMPANY_NUMBER,
    period_start: str = DEFAULT_PERIOD_START,
    period_end: str = DEFAULT_PERIOD_END,
    raw_data_roots: Sequence[str | Path] | None = None,
    include_default_roots: bool = True,
    copy_raw_evidence: bool = True,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    out_dir = (
        root
        / "Kings_Accounting_Suite"
        / "output"
        / "filing_handoff"
        / company_number
        / f"{period_start}_to_{period_end}"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    raw_manifest = build_company_raw_data_manifest(
        root,
        company_number=company_number,
        period_start=period_start,
        period_end=period_end,
        raw_roots=raw_data_roots,
        include_default_roots=include_default_roots,
    )
    raw_json, raw_md = write_raw_data_manifest_artifacts(raw_manifest)
    context = load_accounting_context(root, company_number, period_start, period_end)
    context["raw_data_manifest"] = raw_manifest.to_dict()

    artifacts: list[HandoffArtifact] = []
    seen_destinations: set[str] = set()

    add_path_artifact(
        artifacts,
        root=root,
        out_dir=out_dir,
        source_path=raw_json,
        section="00_start_here",
        dest_rel="00_start_here/raw_data_manifest.json",
        label="Raw data manifest JSON",
        role="source_inventory",
        output_key="raw_data_manifest_json",
        required_for=["source_evidence_data_room"],
        seen_destinations=seen_destinations,
    )
    add_path_artifact(
        artifacts,
        root=root,
        out_dir=out_dir,
        source_path=raw_md,
        section="00_start_here",
        dest_rel="00_start_here/raw_data_manifest.md",
        label="Raw data manifest Markdown",
        role="source_inventory",
        output_key="raw_data_manifest_markdown",
        required_for=["source_evidence_data_room"],
        seen_destinations=seen_destinations,
    )

    if copy_raw_evidence:
        for item in raw_manifest.to_dict().get("files") or []:
            source = Path(item.get("path") or "")
            provider = safe_slug(str(item.get("provider") or "unknown"))
            category = safe_slug(str(item.get("category") or "evidence"))
            dest_name = unique_dest_name(
                seen_destinations,
                f"01_raw_evidence/{provider}/{category}/{safe_filename(source.name)}",
            )
            add_path_artifact(
                artifacts,
                root=root,
                out_dir=out_dir,
                source_path=source,
                section="01_raw_evidence",
                dest_rel=dest_name,
                label=source.name,
                role=str(item.get("evidence_role") or "raw_evidence"),
                output_key="raw_evidence",
                required_for=["source_evidence_data_room"],
                seen_destinations=seen_destinations,
                notes=f"provider={item.get('provider')} ingestion_path={item.get('ingestion_path')}",
            )

    add_period_and_full_outputs(
        artifacts,
        root=root,
        out_dir=out_dir,
        context=context,
        seen_destinations=seen_destinations,
    )
    add_statutory_outputs(
        artifacts,
        root=root,
        out_dir=out_dir,
        context=context,
        seen_destinations=seen_destinations,
    )
    evidence_authoring = build_accounting_evidence_authoring_pack(
        repo_root=root,
        company_name=company_name,
        company_number=company_number,
        period_start=period_start,
        period_end=period_end,
        combined_csv=(context.get("paths") or {}).get("combined_csv"),
        enriched_transactions_path=(context.get("paths") or {}).get("enriched_transactions_json"),
        output_dir=out_dir / "07_review_workpapers" / "evidence_authoring",
    )
    context["accounting_evidence_authoring"] = evidence_authoring
    add_evidence_authoring_outputs(
        artifacts,
        root=root,
        out_dir=out_dir,
        evidence_authoring=evidence_authoring,
        seen_destinations=seen_destinations,
    )

    requirements = build_handoff_requirements(artifacts)
    uk_accounting_brain = build_uk_accounting_requirements_brain(
        company_name=company_name,
        company_number=company_number,
        period_start=period_start,
        period_end=period_end,
        context=context,
        artifacts=artifacts,
        handoff_requirements=requirements,
    )
    brain_outputs = write_uk_accounting_brain_artifacts(uk_accounting_brain, out_dir)
    uk_accounting_brain["outputs"] = dict(brain_outputs)
    brain_outputs = write_uk_accounting_brain_artifacts(uk_accounting_brain, out_dir)
    for output_key, path in brain_outputs.items():
        section = "00_start_here" if "questions" in output_key else "07_review_workpapers"
        add_path_artifact(
            artifacts,
            root=root,
            out_dir=out_dir,
            source_path=path,
            section=section,
            dest_rel=str(Path(path).relative_to(out_dir)).replace("\\", "/"),
            label=output_key,
            role="uk_accounting_requirements_brain",
            output_key=output_key,
            required_for=["manual_review", "uk_accounting_requirements"],
            seen_destinations=seen_destinations,
        )
    readiness = summarise_readiness(requirements)
    generated_at = datetime.now(timezone.utc).isoformat()
    manifest = {
        "schema_version": "accounting-human-filing-handoff-v1",
        "generated_at": generated_at,
        "status": "completed" if readiness.get("ready_for_manual_upload", readiness.get("ready_for_manual_review")) else "partial",
        "company_name": company_name,
        "company_number": company_number,
        "period_start": period_start,
        "period_end": period_end,
        "output_dir": str(out_dir),
        "raw_data_summary": (raw_manifest.to_dict().get("summary") or {}),
        "requirements": [asdict(item) for item in requirements],
        "accounting_evidence_authoring": evidence_authoring,
        "uk_accounting_requirements_brain": uk_accounting_brain,
        "readiness": readiness,
        "artifacts": [asdict(item) for item in artifacts],
        "official_sources": {**OFFICIAL_REQUIREMENT_SOURCES, **UK_ACCOUNTING_OFFICIAL_SOURCES},
        "safe_boundaries": SAFE_BOUNDARIES,
        "manual_next_step": (
            "Review the START_HERE index, confirm missing/manual fields, then use Companies House/HMRC "
            "or commercial filing software manually after director/accountant approval."
        ),
    }

    start_here = out_dir / "00_start_here" / "START_HERE.md"
    index_md = out_dir / "filing_handoff_index.md"
    manifest_json = out_dir / "filing_handoff_manifest.json"
    start_here.parent.mkdir(parents=True, exist_ok=True)
    start_here.write_text(render_start_here(manifest), encoding="utf-8")
    index_md.write_text(render_handoff_index(manifest), encoding="utf-8")
    manifest_json.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    manifest["outputs"] = {
        "manifest": str(manifest_json),
        "index": str(index_md),
        "start_here": str(start_here),
    }
    manifest_json.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest


def load_accounting_context(
    root: Path,
    company_number: str,
    period_start: str,
    period_end: str,
) -> dict[str, Any]:
    company_dir = root / "Kings_Accounting_Suite" / "output" / "company_compliance" / company_number
    period_dir = root / "Kings_Accounting_Suite" / "output" / "gateway" / f"{period_start}_to_{period_end}"
    statutory_dir = (
        root
        / "Kings_Accounting_Suite"
        / "output"
        / "statutory"
        / company_number
        / f"{period_start}_to_{period_end}"
    )
    raw_dir = (
        root
        / "Kings_Accounting_Suite"
        / "output"
        / "company_raw_data"
        / company_number
        / f"{period_start}_to_{period_end}"
    )
    paths = {
        "period_manifest": period_dir / "period_pack_manifest.json",
        "combined_csv": period_dir / f"combined_bank_transactions_{period_start}_to_{period_end}.csv",
        "full_run_manifest": company_dir / "full_company_accounts_run_manifest.json",
        "full_run_summary": company_dir / "full_company_accounts_run_summary.md",
        "compliance_audit_json": company_dir / "company_house_tax_audit.json",
        "compliance_audit_md": company_dir / "company_house_tax_audit.md",
        "autonomous_workflow_manifest": company_dir / "autonomous_full_accounts_workflow_manifest.json",
        "autonomous_workflow_summary": company_dir / "autonomous_full_accounts_workflow_summary.md",
        "statutory_manifest": statutory_dir / "statutory_filing_pack_manifest.json",
        "enriched_transactions_json": statutory_dir / "enriched_transactions.json",
        "enriched_transactions_csv": statutory_dir / "enriched_transactions.csv",
        "raw_data_manifest": raw_dir / "raw_data_manifest.json",
        "raw_data_manifest_markdown": raw_dir / "raw_data_manifest.md",
    }
    return {
        "paths": paths,
        "period_manifest": read_json(paths["period_manifest"]),
        "full_run_manifest": read_json(paths["full_run_manifest"]),
        "statutory_manifest": read_json(paths["statutory_manifest"]),
        "autonomous_workflow": read_json(paths["autonomous_workflow_manifest"]),
    }


def add_period_and_full_outputs(
    artifacts: list[HandoffArtifact],
    *,
    root: Path,
    out_dir: Path,
    context: dict[str, Any],
    seen_destinations: set[str],
) -> None:
    paths = context.get("paths") or {}
    fixed = [
        ("period_manifest", paths.get("period_manifest"), "02_data_and_workpapers", "period_pack_manifest.json", "period_manifest", ["source_evidence_data_room"]),
        ("combined_bank_transactions", paths.get("combined_csv"), "02_data_and_workpapers", "combined_bank_transactions.csv", "combined_bank_feed", ["source_evidence_data_room", "hmrc_company_tax_return"]),
        ("full_run_manifest", paths.get("full_run_manifest"), "02_data_and_workpapers", "full_company_accounts_run_manifest.json", "full_run_manifest", ["source_evidence_data_room"]),
        ("full_run_summary", paths.get("full_run_summary"), "00_start_here", "full_company_accounts_run_summary.md", "full_run_summary", ["source_evidence_data_room"]),
        ("compliance_audit_json", paths.get("compliance_audit_json"), "07_review_workpapers", "company_house_tax_audit.json", "compliance_audit", ["manual_review"]),
        ("compliance_audit_markdown", paths.get("compliance_audit_md"), "07_review_workpapers", "company_house_tax_audit.md", "compliance_audit", ["manual_review"]),
        ("autonomous_workflow_manifest", paths.get("autonomous_workflow_manifest"), "07_review_workpapers", "autonomous_full_accounts_workflow_manifest.json", "autonomous_workflow", ["manual_review"]),
        ("autonomous_workflow_summary", paths.get("autonomous_workflow_summary"), "00_start_here", "autonomous_full_accounts_workflow_summary.md", "autonomous_workflow", ["manual_review"]),
    ]
    for output_key, path, section, dest_name, role, required_for in fixed:
        add_path_artifact(
            artifacts,
            root=root,
            out_dir=out_dir,
            source_path=path,
            section=section,
            dest_rel=f"{section}/{dest_name}",
            label=output_key,
            role=role,
            output_key=output_key,
            required_for=required_for,
            seen_destinations=seen_destinations,
        )

    full_run = context.get("full_run_manifest") or {}
    full_outputs = full_run.get("outputs") or {}
    statutory_outputs_available = bool((context.get("statutory_manifest") or {}).get("outputs"))
    for output_key, info in sorted(full_outputs.items()):
        if statutory_outputs_available and output_key.startswith("statutory_"):
            continue
        if output_key.startswith("statutory_"):
            unprefixed = output_key.removeprefix("statutory_")
            canonical = FINAL_READY_ALIAS_KEYS.get(unprefixed)
            if canonical and f"statutory_{canonical}" in full_outputs:
                continue
        path = Path(info.get("path") or "")
        section = section_for_full_output(output_key)
        add_path_artifact(
            artifacts,
            root=root,
            out_dir=out_dir,
            source_path=path,
            section=section,
            dest_rel=unique_dest_name(seen_destinations, f"{section}/{safe_filename(path.name or output_key)}"),
            label=output_key,
            role="generated_accounts_workpaper",
            output_key=output_key,
            required_for=requirements_for_output(output_key),
            seen_destinations=seen_destinations,
        )


def add_statutory_outputs(
    artifacts: list[HandoffArtifact],
    *,
    root: Path,
    out_dir: Path,
    context: dict[str, Any],
    seen_destinations: set[str],
) -> None:
    statutory = context.get("statutory_manifest") or {}
    statutory_outputs = statutory.get("outputs") or {}
    for output_key, info in sorted(statutory_outputs.items()):
        canonical = FINAL_READY_ALIAS_KEYS.get(output_key)
        if canonical and canonical in statutory_outputs:
            continue
        path = Path(info.get("path") or "")
        section = section_for_statutory_output(output_key)
        add_path_artifact(
            artifacts,
            root=root,
            out_dir=out_dir,
            source_path=path,
            section=section,
            dest_rel=unique_dest_name(seen_destinations, f"{section}/{safe_filename(path.name or output_key)}"),
            label=output_key,
            role="statutory_or_tax_support",
            output_key=output_key,
            required_for=requirements_for_output(output_key),
            seen_destinations=seen_destinations,
        )


def add_evidence_authoring_outputs(
    artifacts: list[HandoffArtifact],
    *,
    root: Path,
    out_dir: Path,
    evidence_authoring: dict[str, Any],
    seen_destinations: set[str],
) -> None:
    for output_key, path in sorted((evidence_authoring.get("outputs") or {}).items()):
        source_path = Path(path)
        try:
            dest_rel = str(source_path.relative_to(out_dir)).replace("\\", "/")
        except ValueError:
            dest_rel = unique_dest_name(
                seen_destinations,
                f"07_review_workpapers/evidence_authoring/{safe_filename(source_path.name or output_key)}",
            )
        add_path_artifact(
            artifacts,
            root=root,
            out_dir=out_dir,
            source_path=source_path,
            section="07_review_workpapers",
            dest_rel=dest_rel,
            label=output_key,
            role="accounting_evidence_authoring",
            output_key=output_key,
            required_for=["source_evidence_data_room", "transaction_evidence_authoring", "manual_review"],
            seen_destinations=seen_destinations,
            notes="Internal support only; not external evidence or raw receipt/invoice proof.",
        )


def add_path_artifact(
    artifacts: list[HandoffArtifact],
    *,
    root: Path,
    out_dir: Path,
    source_path: str | Path | None,
    section: str,
    dest_rel: str,
    label: str,
    role: str,
    output_key: str,
    required_for: list[str],
    seen_destinations: set[str],
    notes: str = "",
) -> None:
    source = Path(source_path) if source_path else Path("")
    exists = bool(source_path and source.exists() and source.is_file())
    destination = out_dir / dest_rel
    bytes_count = source.stat().st_size if exists else 0
    if exists:
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.resolve() != destination.resolve():
            shutil.copy2(source, destination)
    seen_destinations.add(str(destination).lower())
    artifacts.append(
        HandoffArtifact(
            id=f"{safe_slug(output_key)}_{len(artifacts) + 1:04d}",
            section=section,
            label=label,
            role=role,
            source_path=str(source) if source_path else "",
            destination_path=str(destination) if exists else "",
            exists=exists,
            bytes=bytes_count,
            output_key=output_key,
            required_for=required_for,
            notes=notes,
        )
    )


def build_handoff_requirements(artifacts: Iterable[HandoffArtifact]) -> list[HandoffRequirement]:
    by_key: dict[str, list[HandoffArtifact]] = {}
    for artifact in artifacts:
        by_key.setdefault(artifact.output_key, []).append(artifact)

    def has_any(keys: Sequence[str]) -> list[str]:
        found: list[str] = []
        for key in keys:
            aliases = [key]
            if key in FINAL_READY_ALIAS_KEYS:
                aliases.append(FINAL_READY_ALIAS_KEYS[key])
            aliases.extend(old for old, new in FINAL_READY_ALIAS_KEYS.items() if new == key)
            if any(item.exists for alias in aliases for item in by_key.get(alias, [])):
                found.append(key)
        return found

    def requirement(
        *,
        id: str,
        authority: str,
        form_or_task: str,
        required: list[str],
        manual_inputs: list[str],
        official_sources: list[str],
        notes: str,
    ) -> HandoffRequirement:
        generated = has_any(required)
        missing = [key for key in required if key not in generated]
        status = FINAL_READY_STATUS if not missing else "missing_generated_artifacts"
        return HandoffRequirement(
            id=id,
            authority=authority,
            form_or_task=form_or_task,
            status=status,
            generated_artifacts=generated,
            missing_artifacts=missing,
            manual_inputs=manual_inputs,
            official_sources=official_sources,
            notes=notes,
        )

    return [
        requirement(
            id="source_evidence_data_room",
            authority="Internal",
            form_or_task="Evidence and workpaper data room",
            required=["raw_data_manifest_json", "combined_bank_transactions", "period_manifest", "full_run_manifest"],
            manual_inputs=["confirm no bank/account source is missing", "confirm duplicated exports were correctly removed"],
            official_sources=[],
            notes="This makes the raw and transformed source data inspectable before any filing.",
        ),
        requirement(
            id="transaction_evidence_authoring",
            authority="Internal / HMRC records support",
            form_or_task="Transaction evidence requests and internal support vouchers",
            required=[
                "accounting_evidence_authoring_manifest",
                "accounting_evidence_authoring_summary",
                "accounting_evidence_requests_csv",
                "accounting_evidence_document_index",
            ],
            manual_inputs=[
                "attach real supplier receipts/invoices",
                "complete petty-cash allocation fields",
                "confirm income invoices/sales reports",
                "approve director/related-party classifications",
            ],
            official_sources=[
                "https://www.gov.uk/running-a-limited-company/company-and-accounting-records",
                OFFICIAL_REQUIREMENT_SOURCES.get("company_tax_return_obligations", ""),
            ],
            notes="The system writes internal evidence requests and voucher templates only; it does not create external proof.",
        ),
        requirement(
            id="companies_house_annual_accounts",
            authority="Companies House",
            form_or_task="Annual accounts",
            required=["companies_house_accounts_markdown", "companies_house_accounts_pdf", "directors_report_markdown", "audit_exemption_statement_markdown"],
            manual_inputs=["director approval/signature", "filing route choice", "Companies House authentication", "audit exemption eligibility"],
            official_sources=[
                OFFICIAL_REQUIREMENT_SOURCES.get("companies_house_accounts", ""),
                OFFICIAL_REQUIREMENT_SOURCES.get("accounts_and_tax_returns_limited_company", ""),
            ],
            notes="Generated final-ready accounts and approval prompts are present; official filing remains manual.",
        ),
        requirement(
            id="hmrc_company_tax_return",
            authority="HMRC",
            form_or_task="Company Tax Return / CT600 support",
            required=["hmrc_ct600_draft_json", "ct600_box_map_markdown", "hmrc_tax_computation_markdown", "draft_accounts_html", "draft_computation_html", "ixbrl_readiness_note"],
            manual_inputs=["company UTR", "HMRC credentials/agent authority", "commercial filing software", "iXBRL generation/validation", "tax add-backs and reliefs review"],
            official_sources=[
                OFFICIAL_REQUIREMENT_SOURCES.get("company_tax_return_obligations", ""),
                OFFICIAL_REQUIREMENT_SOURCES.get("ct600_form", ""),
                OFFICIAL_REQUIREMENT_SOURCES.get("company_tax_return_accounts_format", ""),
            ],
            notes="The system provides final-ready manual-entry data and readable HTML, not an HMRC-approved iXBRL submission.",
        ),
        requirement(
            id="companies_house_confirmation_statement",
            authority="Companies House",
            form_or_task="Confirmation statement readiness",
            required=["confirmation_statement_readiness_json", "confirmation_statement_readiness_markdown"],
            manual_inputs=["officers", "PSCs", "shareholders", "registered office", "SIC codes", "lawful-purpose statement", "authentication/payment"],
            official_sources=[
                OFFICIAL_REQUIREMENT_SOURCES.get("companies_house_confirmation_statement", ""),
                OFFICIAL_REQUIREMENT_SOURCES.get("companies_house_identity_verification", ""),
            ],
            notes="The system prepares a readiness checklist; the user/director completes and files manually.",
        ),
        requirement(
            id="hmrc_corporation_tax_payment",
            authority="HMRC",
            form_or_task="Corporation Tax payment estimate and manual payment support",
            required=["hmrc_tax_computation_markdown", "hmrc_ct600_draft_json"],
            manual_inputs=["HMRC payment reference", "actual tax account balance check", "human payment approval"],
            official_sources=[OFFICIAL_REQUIREMENT_SOURCES.get("corporation_tax_rates", "")],
            notes="The system estimates tax but never pays.",
        ),
    ]


def summarise_readiness(requirements: Sequence[HandoffRequirement]) -> dict[str, Any]:
    missing = [item for item in requirements if item.missing_artifacts]
    return {
        "ready_for_manual_review": not missing,
        "ready_for_manual_upload": not missing,
        "requirement_count": len(requirements),
        "generated_ready_count": len(requirements) - len(missing),
        "missing_generated_artifact_count": sum(len(item.missing_artifacts) for item in missing),
        "manual_inputs_required_count": sum(len(item.manual_inputs) for item in requirements),
        "missing_requirements": [item.id for item in missing],
        "official_submission_supported": False,
        "human_filing_required": True,
    }


def render_start_here(manifest: dict[str, Any]) -> str:
    readiness = manifest.get("readiness") or {}
    uk_brain = manifest.get("uk_accounting_requirements_brain") or {}
    brain_summary = uk_brain.get("summary") or {}
    brain_figures = uk_brain.get("figures") or {}
    evidence_authoring = manifest.get("accounting_evidence_authoring") or {}
    evidence_summary = evidence_authoring.get("summary") or {}
    llm_authoring = evidence_authoring.get("llm_document_authoring") or evidence_summary.get("llm_document_authoring") or {}
    lines = [
        "# Accounting Filing Handoff Pack",
        "",
        f"- Company: {manifest.get('company_number')} {manifest.get('company_name')}",
        f"- Period: {manifest.get('period_start')} to {manifest.get('period_end')}",
        f"- Generated: {manifest.get('generated_at')}",
        f"- Ready for manual upload: {readiness.get('ready_for_manual_upload', readiness.get('ready_for_manual_review'))}",
        f"- UK requirements tracked: {brain_summary.get('requirement_count', 0)}",
        f"- Accountant self-questions: {brain_summary.get('question_count', 0)}",
        f"- Evidence requests generated: {evidence_summary.get('draft_count', 0)}",
        f"- LLM internal workpapers: {llm_authoring.get('completed_count', 0)} ({llm_authoring.get('status', 'unknown')})",
        f"- Turnover over VAT threshold: {brain_figures.get('turnover_over_vat_threshold')}",
        "",
        "## What This Pack Does",
        "",
        "- Pulls repo-held raw evidence into one review folder.",
        "- Includes the combined transaction feed and generated workpapers.",
        "- Includes Companies House accounts support and HMRC CT600/computation support.",
        "- Includes confirmation statement readiness prompts.",
        "- Generates internal evidence requests and support vouchers for cash, receipts, invoices, and unclear allocations.",
        "- Includes a UK accounting requirements brain and accountant self-question checklist.",
        "- Leaves filing, submission, declaration, authentication, and payment to the human/director/accountant.",
        "",
        "## Manual Actions Still Required",
        "",
    ]
    manual_inputs = []
    for requirement in manifest.get("requirements") or []:
        manual_inputs.extend(requirement.get("manual_inputs") or [])
    for item in sorted(set(manual_inputs)):
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Folders",
            "",
            "- `01_raw_evidence`: uploaded statements, invoices, receipts, and evidence files.",
            "- `02_data_and_workpapers`: source manifests and combined bank/account feed.",
            "- `03_accounts_workpapers`: generated accounts workbooks/PDFs.",
            "- `04_companies_house`: final-ready accounts and Companies House support.",
            "- `05_hmrc_corporation_tax`: CT600, tax computation, and iXBRL readiness support.",
            "- `06_confirmation_statement`: CS01/confirmation-statement readiness.",
            "- `07_review_workpapers`: audits, matrices, UK requirements brain, and autonomous workflow evidence.",
            "- `07_review_workpapers/evidence_authoring`: internal support vouchers, receipt requests, invoice prompts, and allocation memos.",
            "",
            "## Safety",
            "",
            "- No Companies House filing was submitted.",
            "- No HMRC filing was submitted.",
            "- No payment was made.",
            "- No trading/exchange state was mutated.",
            "",
        ]
    )
    return "\n".join(lines)


def render_handoff_index(manifest: dict[str, Any]) -> str:
    uk_brain = manifest.get("uk_accounting_requirements_brain") or {}
    brain_summary = uk_brain.get("summary") or {}
    evidence_authoring = manifest.get("accounting_evidence_authoring") or {}
    evidence_summary = evidence_authoring.get("summary") or {}
    llm_authoring = evidence_authoring.get("llm_document_authoring") or evidence_summary.get("llm_document_authoring") or {}
    lines = [
        "# Filing Handoff Index",
        "",
        f"- Output folder: `{manifest.get('output_dir')}`",
        f"- Raw files inventoried: `{(manifest.get('raw_data_summary') or {}).get('file_count', 0)}`",
        f"- Transaction sources: `{(manifest.get('raw_data_summary') or {}).get('transaction_source_count', 0)}`",
        f"- Evidence-only files: `{(manifest.get('raw_data_summary') or {}).get('evidence_only_count', 0)}`",
        f"- UK requirements tracked: `{brain_summary.get('requirement_count', 0)}`",
        f"- Accountant self-questions: `{brain_summary.get('question_count', 0)}`",
        f"- Evidence requests: `{evidence_summary.get('draft_count', 0)}`",
        f"- Generated internal document templates: `{evidence_summary.get('generated_document_count', 0)}`",
        f"- LLM internal workpapers: `{llm_authoring.get('completed_count', 0)}` ({llm_authoring.get('status', 'unknown')})",
        f"- Manual-input requirement groups: `{brain_summary.get('manual_input_requirement_count', 0)}`",
        "",
        "## Requirement Readiness",
        "",
        "| Requirement | Authority | Status | Missing generated artifacts | Manual inputs |",
        "| --- | --- | --- | --- | --- |",
    ]
    for requirement in manifest.get("requirements") or []:
        missing = ", ".join(requirement.get("missing_artifacts") or []) or "none"
        manual = ", ".join(requirement.get("manual_inputs") or []) or "none"
        lines.append(
            f"| `{requirement.get('id')}` | {requirement.get('authority')} | "
            f"{requirement.get('status')} | {missing} | {manual} |"
        )
    if uk_brain:
        lines.extend(["", "## UK Accounting Brain", ""])
        lines.append("| Requirement | Authority | Status | Manual inputs |")
        lines.append("| --- | --- | --- | --- |")
        for requirement in uk_brain.get("requirements") or []:
            manual = ", ".join(requirement.get("manual_inputs") or []) or "none"
            lines.append(
                f"| `{requirement.get('id')}` | {requirement.get('authority')} | "
                f"{requirement.get('status')} | {manual} |"
            )
        lines.extend(["", "## Accountant Self-Questions", ""])
        for question in uk_brain.get("accountant_self_questions") or []:
            lines.append(
                f"- `{question.get('id')}` {question.get('status')}: {question.get('question')}"
            )
    if evidence_authoring:
        lines.extend(["", "## Evidence Authoring", ""])
        lines.append(
            f"- Status: {evidence_authoring.get('status', 'unknown')} "
            f"requests={evidence_summary.get('draft_count', 0)} "
            f"documents={evidence_summary.get('generated_document_count', 0)} "
            f"llm_status={llm_authoring.get('status', 'unknown')} "
            f"llm_docs={llm_authoring.get('completed_count', 0)} "
            f"petty_cash={evidence_summary.get('petty_cash_withdrawal_count', 0)} "
            f"related_party={evidence_summary.get('related_party_query_count', 0)}"
        )
        lines.append("- Generated documents are internal support records and evidence requests only, not external receipts or invoices.")
    lines.extend(["", "## Artifacts", ""])
    by_section: dict[str, list[dict[str, Any]]] = {}
    for artifact in manifest.get("artifacts") or []:
        by_section.setdefault(artifact.get("section") or "unknown", []).append(artifact)
    for section, items in sorted(by_section.items()):
        lines.extend(["", f"### {section}", ""])
        for item in items:
            marker = "OK" if item.get("exists") else "MISSING"
            destination = item.get("destination_path") or item.get("source_path") or ""
            lines.append(f"- {marker} `{item.get('output_key')}` {item.get('label')}: `{destination}`")
    lines.extend(["", "## Official Sources", ""])
    for name, url in (manifest.get("official_sources") or {}).items():
        lines.append(f"- {name}: {url}")
    lines.append("")
    return "\n".join(lines)


def section_for_full_output(output_key: str) -> str:
    key = output_key.lower()
    if "statutory_" in key:
        return section_for_statutory_output(key.replace("statutory_", ""))
    if any(term in key for term in ("general_ledger", "trial_balance", "management_accounts", "period_manifest")):
        return "03_accounts_workpapers"
    if any(term in key for term in ("accounts_pack", "profit_and_loss", "pnl", "tax_summary")):
        return "03_accounts_workpapers"
    if "compliance" in key:
        return "07_review_workpapers"
    return "02_data_and_workpapers"


def section_for_statutory_output(output_key: str) -> str:
    key = output_key.lower()
    if "companies_house" in key or "directors_report" in key or "audit_exemption" in key:
        return "04_companies_house"
    if "confirmation_statement" in key:
        return "06_confirmation_statement"
    if any(term in key for term in ("payer_provenance", "cis_vat_tax_basis")):
        return "07_review_workpapers"
    if any(term in key for term in ("hmrc", "ct600", "ixbrl", "computation")):
        return "05_hmrc_corporation_tax"
    if "government" in key or "filing_checklist" in key or "supplementary" in key:
        return "07_review_workpapers"
    return "07_review_workpapers"


def requirements_for_output(output_key: str) -> list[str]:
    key = output_key.lower().replace("statutory_", "")
    requirements: list[str] = []
    if any(term in key for term in ("raw_data", "combined_bank", "period_manifest", "full_run_manifest")):
        requirements.append("source_evidence_data_room")
    if any(term in key for term in ("companies_house", "directors_report", "audit_exemption", "accounts_pack", "profit_and_loss")):
        requirements.append("companies_house_annual_accounts")
    if any(term in key for term in ("hmrc", "ct600", "ixbrl", "computation", "tax_summary")):
        requirements.append("hmrc_company_tax_return")
    if any(term in key for term in ("payer_provenance", "cis_vat_tax_basis")):
        requirements.extend(["hmrc_company_tax_return", "source_evidence_data_room"])
    if "confirmation_statement" in key:
        requirements.append("companies_house_confirmation_statement")
    if "tax_computation" in key or "hmrc_ct600" in key:
        requirements.append("hmrc_corporation_tax_payment")
    return sorted(set(requirements or ["manual_review"]))


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip().lower())
    return slug.strip("_") or "unknown"


def safe_filename(value: str) -> str:
    name = re.sub(r"[^A-Za-z0-9_.() -]+", "_", value.strip())
    return name.strip(" .") or "artifact"


def unique_dest_name(seen: set[str], dest_rel: str) -> str:
    base = Path(dest_rel)
    candidate = dest_rel
    index = 2
    while candidate.lower() in seen:
        candidate = str(base.with_name(f"{base.stem}_{index}{base.suffix}")).replace("\\", "/")
        index += 1
    seen.add(candidate.lower())
    return candidate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the safe human filing handoff pack.")
    parser.add_argument("--company-name", default=DEFAULT_COMPANY_NAME)
    parser.add_argument("--company-number", default=DEFAULT_COMPANY_NUMBER)
    parser.add_argument("--period-start", default=DEFAULT_PERIOD_START)
    parser.add_argument("--period-end", default=DEFAULT_PERIOD_END)
    parser.add_argument("--raw-data-dir", action="append", default=[])
    parser.add_argument("--no-default-roots", action="store_true")
    parser.add_argument("--no-copy-raw-evidence", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = build_accounting_handoff_pack(
        company_name=args.company_name,
        company_number=args.company_number,
        period_start=args.period_start,
        period_end=args.period_end,
        raw_data_roots=args.raw_data_dir,
        include_default_roots=not args.no_default_roots,
        copy_raw_evidence=not args.no_copy_raw_evidence,
    )
    print(manifest["outputs"]["manifest"])
    print(manifest["outputs"]["start_here"])
    readiness = manifest.get("readiness") or {}
    return 0 if readiness.get("ready_for_manual_upload", readiness.get("ready_for_manual_review")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
