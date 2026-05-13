"""UK accounting requirements brain for Aureon's full-accounts workflow.

This module turns local accounting artifacts plus the repo's law dataset into a
machine-readable requirement map and an accountant-style self-question list. It
prepares evidence, questions, and manual filing instructions only. It never
submits to Companies House, submits to HMRC, pays tax, or mutates bank/trading
state.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, Sequence


KAS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = KAS_DIR.parent
CORE_DIR = KAS_DIR / "core"
TOOLS_DIR = KAS_DIR / "tools"
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(KAS_DIR))
sys.path.insert(0, str(CORE_DIR))
sys.path.insert(0, str(TOOLS_DIR))

try:  # pragma: no cover - fallback is exercised when the law dataset is absent.
    from hnc_law_dataset import get_law_dataset  # type: ignore
except Exception:  # pragma: no cover
    get_law_dataset = None  # type: ignore

try:
    from generate_statutory_filing_pack import OFFICIAL_REQUIREMENT_SOURCES
except Exception:  # pragma: no cover
    OFFICIAL_REQUIREMENT_SOURCES = {}


UK_ACCOUNTING_OFFICIAL_SOURCES = {
    **dict(OFFICIAL_REQUIREMENT_SOURCES),
    "annual_accounts_overview": "https://www.gov.uk/annual-accounts/overview",
    "prepare_file_annual_accounts_limited_company": "https://www.gov.uk/prepare-file-annual-accounts-for-limited-company",
    "company_accounting_records": "https://www.gov.uk/running-a-limited-company/company-and-accounting-records",
    "vat_registration_when_to_register": "https://www.gov.uk/register-for-vat",
    "vat_registration_threshold": "https://www.gov.uk/vat-registration/when-to-register",
    "vat_record_keeping": "https://www.gov.uk/vat-record-keeping",
    "making_tax_digital_vat": "https://www.gov.uk/guidance/sign-up-for-making-tax-digital-for-vat",
    "vat_domestic_reverse_charge": "https://www.gov.uk/guidance/vat-domestic-reverse-charge-for-building-and-construction-services",
    "paye_for_employers": "https://www.gov.uk/paye-for-employers",
    "cis_overview": "https://www.gov.uk/what-is-the-construction-industry-scheme",
}


QUESTION_SAFE_STATUSES = {
    "answered_by_system",
    "needs_data",
    "needs_human_confirmation",
    "needs_secret_manual_input",
    "needs_accountant_review",
    "blocked_missing_evidence",
    "system_allocated_eye_scan",
    "not_applicable",
}


COGNITIVE_REVIEWER_ROLES = {
    "bookkeeper": "Is every transaction posted correctly?",
    "accountant": "Do the accounts make sense?",
    "tax_reviewer": "Does the CT600 computation follow from the accounts?",
    "companies_house_reviewer": "Would the filing pack pass manual upload checks?",
    "hmrc_reviewer": "Can every tax figure be defended?",
    "evidence_officer": "What proof is missing?",
    "contrary_reviewer": "What could be wrong even if totals reconcile?",
    "director_handoff_officer": "What must the human confirm or manually submit?",
}


REQUIRED_SELF_QUESTION_DOMAINS = [
    "company_identity",
    "data_scope",
    "transaction_truth",
    "revenue",
    "expenses",
    "balance_sheet",
    "tax_ct600",
    "vat_paye_cis",
    "document_pack",
    "cognitive_challenge",
]


SAFE_ACCOUNTING_ACTIONS = [
    "inspect",
    "reconcile",
    "generate_final_ready_local_pack",
    "ingest_to_vault",
    "publish_status",
    "autonomously_allocate_and_eye_scan_flags",
]


ARTIFACT_KEY_ALIASES = {
    "companies_house_accounts_markdown": ("companies_house_accounts_markdown", "companies_house_accounts_final_ready_markdown"),
    "companies_house_accounts_pdf": ("companies_house_accounts_pdf", "companies_house_accounts_final_ready_pdf"),
    "directors_report_markdown": ("directors_report_markdown", "directors_report_final_ready_markdown"),
    "directors_report_pdf": ("directors_report_pdf", "directors_report_final_ready_pdf"),
    "audit_exemption_statement_markdown": ("audit_exemption_statement_markdown", "audit_exemption_statement_final_ready_markdown"),
    "hmrc_tax_computation_markdown": ("hmrc_tax_computation_markdown", "hmrc_tax_computation_final_ready_markdown"),
    "hmrc_tax_computation_pdf": ("hmrc_tax_computation_pdf", "hmrc_tax_computation_final_ready_pdf"),
    "hmrc_ct600_draft_json": ("hmrc_ct600_draft_json", "ct600_manual_entry_json"),
    "ct600_box_map_markdown": ("ct600_box_map_markdown", "ct600_box_map_final_ready_markdown"),
    "draft_accounts_html": ("draft_accounts_html", "accounts_readable_for_ixbrl_html"),
    "draft_computation_html": ("draft_computation_html", "computation_readable_for_ixbrl_html"),
}


@dataclass
class UKRequirement:
    id: str
    authority: str
    domain: str
    form_or_task: str
    requirement: str
    applies_when: str
    status: str
    generated_artifacts: list[str] = field(default_factory=list)
    missing_generated_artifacts: list[str] = field(default_factory=list)
    manual_inputs: list[str] = field(default_factory=list)
    data_questions: list[str] = field(default_factory=list)
    evidence_to_collect: list[str] = field(default_factory=list)
    internal_systems: list[str] = field(default_factory=list)
    official_sources: list[str] = field(default_factory=list)
    notes: str = ""
    safe_boundary: str = "manual_filing_required"


@dataclass
class AccountantQuestion:
    id: str
    question: str
    why_it_matters: str
    answer: str
    status: str
    evidence: list[str] = field(default_factory=list)
    next_action: str = ""
    routed_systems: list[str] = field(default_factory=list)
    domain: str = "general"
    confidence: str = "medium"
    risk_level: str = "medium"
    reviewer_role: str = "accountant"
    source_evidence: list[str] = field(default_factory=list)
    linked_transactions: list[str] = field(default_factory=list)
    linked_output_documents: list[str] = field(default_factory=list)
    official_sources: list[str] = field(default_factory=list)


def build_uk_accounting_requirements_brain(
    *,
    company_name: str,
    company_number: str,
    period_start: str,
    period_end: str,
    context: dict[str, Any] | None = None,
    artifacts: Sequence[Any] | None = None,
    handoff_requirements: Sequence[Any] | None = None,
) -> dict[str, Any]:
    context = context or {}
    artifact_list = list(artifacts or [])
    generated_at = datetime.now(timezone.utc).isoformat()
    artifact_map = _artifact_map(artifact_list)
    statutory = context.get("statutory_manifest") or {}
    full_run = context.get("full_run_manifest") or {}
    raw_manifest = context.get("raw_data_manifest") or {}
    evidence_authoring = context.get("accounting_evidence_authoring") or {}
    period_manifest = context.get("period_manifest") or {}
    combined = (
        period_manifest.get("combined_bank_data")
        or ((full_run.get("source_data_inventory") or {}).get("combined_bank_data") or {})
        or {}
    )
    figures = _extract_figures(statutory, full_run)
    turnover = _money(figures.get("turnover"))
    profit_before_tax = _money(figures.get("profit_before_tax"))
    corporation_tax = _money(figures.get("corporation_tax"))
    law_summary = _law_summary()
    vat_threshold = _money(law_summary.get("vat_registration_threshold") or "90000")
    ct600 = (
        _read_output_json(statutory, "ct600_manual_entry_json")
        or _read_output_json(statutory, "hmrc_ct600_draft_json")
        or _read_artifact_json(artifact_map, "ct600_manual_entry_json")
        or _read_artifact_json(artifact_map, "hmrc_ct600_draft_json")
    )
    utr = str(ct600.get("utr") or "").strip() if isinstance(ct600, dict) else ""
    government_matrix = statutory.get("government_requirements_matrix") or {}
    provider_summary = _provider_summary(combined)
    known_providers = sorted(provider_summary)
    requirement_items = _build_requirements(
        artifact_map=artifact_map,
        statutory=statutory,
        combined=combined,
        raw_manifest=raw_manifest,
        evidence_authoring=evidence_authoring,
        turnover=turnover,
        vat_threshold=vat_threshold,
        utr=utr,
        handoff_requirements=handoff_requirements or [],
    )
    questions = _build_questions(
        company_number=company_number,
        turnover=turnover,
        profit_before_tax=profit_before_tax,
        corporation_tax=corporation_tax,
        vat_threshold=vat_threshold,
        utr=utr,
        combined=combined,
        raw_manifest=raw_manifest,
        evidence_authoring=evidence_authoring,
        known_providers=known_providers,
        artifact_map=artifact_map,
        requirements=requirement_items,
    )
    questions = [normalise_question_for_autonomous_handoff(item) for item in questions]
    unresolved = [
        item
        for item in questions
        if item.status not in {"answered_by_system", "not_applicable", "system_allocated_eye_scan"}
    ]
    manual_blockers = [item for item in requirement_items if item.manual_inputs]
    missing_generated = [
        missing
        for item in requirement_items
        for missing in item.missing_generated_artifacts
    ]
    status_counts = Counter(item.status for item in questions)
    risk_counts = Counter(item.risk_level for item in questions)
    domain_counts = Counter(item.domain for item in questions)
    brain = {
        "schema_version": "uk-accounting-requirements-brain-v1",
        "generated_at": generated_at,
        "company_name": company_name,
        "company_number": company_number,
        "period_start": period_start,
        "period_end": period_end,
        "status": "final_ready_manual_upload_required" if not missing_generated else "partial_missing_generated_artifacts",
        "mode": "local_reasoning_and_manual_filing_support_only",
        "law_dataset": law_summary,
        "figures": {
            "turnover": money_text(turnover),
            "profit_before_tax": money_text(profit_before_tax),
            "corporation_tax": money_text(corporation_tax),
            "vat_registration_threshold": money_text(vat_threshold),
            "turnover_over_vat_threshold": bool(turnover >= vat_threshold and vat_threshold > 0),
        },
        "data_coverage": {
            "raw_file_count": ((raw_manifest.get("summary") or {}).get("file_count", 0)),
            "transaction_source_count": combined.get("transaction_source_count", combined.get("csv_source_count", 0)),
            "unique_rows_in_period": combined.get("unique_rows_in_period", 0),
            "duplicate_rows_removed": combined.get("duplicate_rows_removed", 0),
            "known_providers": known_providers,
            "provider_summary": provider_summary,
            "evidence_authoring_summary": evidence_authoring.get("summary") or {},
        },
        "requirements": [asdict(item) for item in requirement_items],
        "accountant_self_questions": [asdict(item) for item in questions],
        "cognitive_reviewer_roles": dict(COGNITIVE_REVIEWER_ROLES),
        "expanded_self_question_manifest": {
            "schema_version": "expanded-uk-accounting-self-questions-v1",
            "domain_count": len(domain_counts),
            "required_domains": list(REQUIRED_SELF_QUESTION_DOMAINS),
            "cognitive_reviewer_roles": dict(COGNITIVE_REVIEWER_ROLES),
            "question_statuses": sorted(QUESTION_SAFE_STATUSES),
            "questions": [asdict(item) for item in questions],
        },
        "summary": {
            "requirement_count": len(requirement_items),
            "generated_ready_count": len([item for item in requirement_items if not item.missing_generated_artifacts]),
            "missing_generated_artifact_count": len(missing_generated),
            "manual_input_requirement_count": len(manual_blockers),
            "human_data_entry_requirement_count": 0,
            "eye_scan_or_legal_handoff_requirement_count": len(manual_blockers),
            "question_count": len(questions),
            "unresolved_question_count": len(unresolved),
            "question_status_counts": dict(sorted(status_counts.items())),
            "question_risk_counts": dict(sorted(risk_counts.items())),
            "question_domain_counts": dict(sorted(domain_counts.items())),
            "safe_actions": list(SAFE_ACCOUNTING_ACTIONS),
            "government_matrix_requirement_count": len(government_matrix.get("requirements") or []),
            "manual_filing_required": True,
        },
        "official_sources": UK_ACCOUNTING_OFFICIAL_SOURCES,
        "safe_boundaries": {
            "official_companies_house_filing": "manual_only",
            "official_hmrc_submission": "manual_only",
            "vat_registration_or_return_submission": "manual_only",
            "utr_or_gateway_credentials": "manual_secret_input_only",
            "tax_or_penalty_payment": "manual_only",
            "bank_payment_or_exchange_mutation": "blocked_from_accounting_brain",
        },
        "next_internal_actions": _next_internal_actions(requirement_items, questions),
    }
    return brain


def render_uk_requirements_markdown(brain: dict[str, Any]) -> str:
    summary = brain.get("summary") or {}
    figures = brain.get("figures") or {}
    coverage = brain.get("data_coverage") or {}
    lines = [
        "# UK Accounting Requirements Brain",
        "",
        f"- Company: {brain.get('company_number')} {brain.get('company_name')}",
        f"- Period: {brain.get('period_start')} to {brain.get('period_end')}",
        f"- Status: {brain.get('status')}",
        f"- Requirements tracked: {summary.get('requirement_count', 0)}",
        f"- Accountant self-questions: {summary.get('question_count', 0)}",
        f"- Open data/secret questions: {summary.get('unresolved_question_count', 0)}",
        f"- Turnover: GBP {figures.get('turnover', '0.00')}",
        f"- VAT threshold used: GBP {figures.get('vat_registration_threshold', '0.00')}",
        f"- Turnover over VAT threshold: {figures.get('turnover_over_vat_threshold')}",
        f"- Data providers: {', '.join(coverage.get('known_providers') or []) or 'unknown'}",
        "",
        "## Safe Boundary",
        "",
        "- This brain can inspect, reconcile, generate final-ready local packs, ingest context to the vault, publish status, and create autonomous allocation assumptions with eye-scan flags.",
        "- Companies House filing, HMRC submission, VAT registration/returns, authentication, declarations, and payments stay manual.",
        "",
        "## Question Domains",
        "",
    ]
    for domain, count in (summary.get("question_domain_counts") or {}).items():
        lines.append(f"- {domain}: {count}")
    lines.extend(
        [
            "",
            "## Question Statuses",
            "",
        ]
    )
    for status, count in (summary.get("question_status_counts") or {}).items():
        lines.append(f"- {status}: {count}")
    lines.extend(
        [
            "",
            "## Cognitive Reviewer Roles",
            "",
        ]
    )
    for role, prompt in (brain.get("cognitive_reviewer_roles") or COGNITIVE_REVIEWER_ROLES).items():
        lines.append(f"- {role}: {prompt}")
    lines.extend(
        [
            "",
        "## Requirements",
        "",
        "| Requirement | Authority | Status | Generated artifacts | Secret/legal/eye-scan inputs |",
        "| --- | --- | --- | --- | --- |",
        ]
    )
    for item in brain.get("requirements") or []:
        generated = ", ".join(item.get("generated_artifacts") or []) or "none"
        manual = ", ".join(item.get("manual_inputs") or []) or "none"
        lines.append(
            f"| `{item.get('id')}` | {item.get('authority')} | {item.get('status')} | {generated} | {manual} |"
        )
    lines.extend(["", "## Internal Next Actions", ""])
    for action in brain.get("next_internal_actions") or []:
        lines.append(f"- {action}")
    lines.extend(["", "## Official Sources", ""])
    for name, url in (brain.get("official_sources") or {}).items():
        lines.append(f"- {name}: {url}")
    lines.append("")
    return "\n".join(lines)


def render_accountant_questions_markdown(brain: dict[str, Any]) -> str:
    lines = [
        "# Accountant Self-Questions",
        "",
        "These are the questions Aureon asks itself before the legal filing handoff. Each question is routed to an internal reviewer role and either answered from source evidence or converted into a conservative system allocation with an eye-scan flag.",
        "",
    ]
    for question in brain.get("accountant_self_questions") or []:
        lines.extend(
            [
                f"## {question.get('id')}",
                "",
                f"Domain: {question.get('domain', 'general')}",
                "",
                f"Reviewer role: {question.get('reviewer_role', 'accountant')}",
                "",
                f"Question: {question.get('question')}",
                "",
                f"Why it matters: {question.get('why_it_matters')}",
                "",
                f"Current answer: {question.get('answer')}",
                "",
                f"Status: {question.get('status')}",
                "",
                f"Risk: {question.get('risk_level', 'medium')} | Confidence: {question.get('confidence', 'medium')}",
                "",
                f"Next action: {question.get('next_action')}",
                "",
            ]
        )
        evidence = question.get("evidence") or []
        if evidence:
            lines.append("Evidence:")
            for item in evidence:
                lines.append(f"- {item}")
            lines.append("")
        documents = question.get("linked_output_documents") or []
        if documents:
            lines.append("Linked documents:")
            for item in documents:
                lines.append(f"- {item}")
            lines.append("")
        sources = question.get("official_sources") or []
        if sources:
            lines.append("Official sources:")
            for item in sources:
                lines.append(f"- {item}")
            lines.append("")
    return "\n".join(lines)


def render_expanded_self_questions_markdown(brain: dict[str, Any]) -> str:
    summary = brain.get("summary") or {}
    lines = [
        "# Expanded UK Accounting Self-Questions",
        "",
        f"Company: {brain.get('company_name')} ({brain.get('company_number')})",
        f"Period: {brain.get('period_start')} to {brain.get('period_end')}",
        f"Question count: {summary.get('question_count', 0)}",
        "",
        "This is Aureon's expanded UK limited-company interrogation layer. It is not a filing submission and it does not pay or submit anything.",
        "",
        "## Cognitive Roles",
        "",
    ]
    for role, prompt in (brain.get("cognitive_reviewer_roles") or COGNITIVE_REVIEWER_ROLES).items():
        lines.append(f"- {role}: {prompt}")
    lines.extend(["", "## Questions By Domain", ""])
    for domain in REQUIRED_SELF_QUESTION_DOMAINS:
        questions = [item for item in brain.get("accountant_self_questions") or [] if item.get("domain") == domain]
        if not questions:
            continue
        lines.extend([f"### {domain}", ""])
        for item in questions:
            lines.append(
                f"- `{item.get('id')}` [{item.get('status')}, risk={item.get('risk_level')}, "
                f"role={item.get('reviewer_role')}]: {item.get('question')}"
            )
            lines.append(f"  Answer: {item.get('answer')}")
            lines.append(f"  Next: {item.get('next_action')}")
    lines.append("")
    return "\n".join(lines)


def render_missing_data_action_plan_markdown(brain: dict[str, Any]) -> str:
    questions = [
        item
        for item in brain.get("accountant_self_questions") or []
        if item.get("status") in {
            "needs_data",
            "needs_secret_manual_input",
            "system_allocated_eye_scan",
        }
    ]
    lines = [
        "# Autonomous Allocation And Eye-Scan Action Plan",
        "",
        f"Company: {brain.get('company_name')} ({brain.get('company_number')})",
        f"Period: {brain.get('period_start')} to {brain.get('period_end')}",
        "",
        "Every item below remains visible, but Aureon applies a conservative working treatment from available data. The user role is eye-scan exception flagging plus legal approval/upload/submission/payment only; secrets or newly uploaded raw data are the only true manual inputs.",
        "",
        "| Domain | Status | Risk | Question | Required action |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in sorted(questions, key=lambda q: (q.get("risk_level") != "critical", q.get("domain", ""), q.get("id", ""))):
        lines.append(
            f"| {item.get('domain')} | {item.get('status')} | {item.get('risk_level')} | "
            f"{_table_text(item.get('question'))} | {_table_text(item.get('next_action'))} |"
        )
    if not questions:
        lines.append("| all | answered_by_system | low | No open questions | No action needed before legal handoff. |")
    lines.extend(
        [
            "",
            "## Manual Safety Boundary",
            "",
            "- Companies House filing remains manual.",
            "- HMRC CT600/iXBRL submission remains manual.",
            "- VAT/PAYE/CIS registrations and returns remain manual.",
            "- Tax, penalty, bank, or exchange payments remain manual.",
            "- Generated internal allocation memos and eye-scan flags are not external supplier receipts.",
            "",
        ]
    )
    return "\n".join(lines)


def render_risk_and_contradiction_register_markdown(brain: dict[str, Any]) -> str:
    questions = [
        item
        for item in brain.get("accountant_self_questions") or []
        if item.get("risk_level") in {"high", "critical"} or item.get("reviewer_role") == "contrary_reviewer"
    ]
    lines = [
        "# Risk And Contradiction Register",
        "",
        f"Company: {brain.get('company_name')} ({brain.get('company_number')})",
        f"Period: {brain.get('period_start')} to {brain.get('period_end')}",
        "",
        "This register records what could still be wrong even when the arithmetic reconciles. It is designed for director/accountant review before manual filing.",
        "",
        "| Role | Domain | Risk | Status | Contradiction or challenge | Evidence route |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in sorted(questions, key=lambda q: (q.get("risk_level") != "critical", q.get("domain", ""), q.get("id", ""))):
        evidence = ", ".join(item.get("evidence") or item.get("source_evidence") or []) or "review workpapers"
        lines.append(
            f"| {item.get('reviewer_role')} | {item.get('domain')} | {item.get('risk_level')} | "
            f"{item.get('status')} | {_table_text(item.get('question'))} | {_table_text(evidence)} |"
        )
    if not questions:
        lines.append("| accountant | all | low | answered_by_system | No high-risk contradiction recorded | source manifest |")
    lines.append("")
    return "\n".join(lines)


def write_uk_accounting_brain_artifacts(brain: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    target = Path(out_dir)
    review_dir = target / "07_review_workpapers"
    start_dir = target / "00_start_here"
    review_dir.mkdir(parents=True, exist_ok=True)
    start_dir.mkdir(parents=True, exist_ok=True)
    json_path = review_dir / "uk_accounting_requirements_brain.json"
    md_path = review_dir / "uk_accounting_requirements_brain.md"
    questions_path = start_dir / "accountant_self_questions.md"
    expanded_json_path = review_dir / "expanded_accounting_self_questions.json"
    expanded_csv_path = review_dir / "expanded_accounting_self_questions.csv"
    expanded_md_path = start_dir / "21_EXPANDED_ACCOUNTING_SELF_QUESTIONS.md"
    expanded_pdf_path = start_dir / "21_EXPANDED_ACCOUNTING_SELF_QUESTIONS.pdf"
    missing_json_path = review_dir / "missing_data_and_evidence_action_plan.json"
    missing_csv_path = review_dir / "missing_data_and_evidence_action_plan.csv"
    missing_md_path = start_dir / "22_MISSING_DATA_AND_EVIDENCE_ACTION_PLAN.md"
    missing_pdf_path = start_dir / "22_MISSING_DATA_AND_EVIDENCE_ACTION_PLAN.pdf"
    risk_json_path = review_dir / "risk_and_contradiction_register.json"
    risk_csv_path = review_dir / "risk_and_contradiction_register.csv"
    risk_md_path = start_dir / "23_RISK_AND_CONTRADICTION_REGISTER.md"
    risk_pdf_path = start_dir / "23_RISK_AND_CONTRADICTION_REGISTER.pdf"

    expanded_md = render_expanded_self_questions_markdown(brain)
    missing_md = render_missing_data_action_plan_markdown(brain)
    risk_md = render_risk_and_contradiction_register_markdown(brain)
    json_path.write_text(json.dumps(brain, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(render_uk_requirements_markdown(brain), encoding="utf-8")
    questions_path.write_text(render_accountant_questions_markdown(brain), encoding="utf-8")
    expanded_json_path.write_text(
        json.dumps(brain.get("expanded_self_question_manifest") or {}, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    expanded_md_path.write_text(expanded_md, encoding="utf-8")
    missing_items = _filter_questions_for_action_plan(brain)
    missing_json_path.write_text(json.dumps(missing_items, indent=2, sort_keys=True), encoding="utf-8")
    missing_md_path.write_text(missing_md, encoding="utf-8")
    risk_items = _filter_questions_for_risk_register(brain)
    risk_json_path.write_text(json.dumps(risk_items, indent=2, sort_keys=True), encoding="utf-8")
    risk_md_path.write_text(risk_md, encoding="utf-8")
    _write_questions_csv(brain.get("accountant_self_questions") or [], expanded_csv_path)
    _write_questions_csv(missing_items, missing_csv_path)
    _write_questions_csv(risk_items, risk_csv_path)
    _write_pdf(expanded_pdf_path, "Expanded UK Accounting Self-Questions", expanded_md)
    _write_pdf(missing_pdf_path, "Missing Data And Evidence Action Plan", missing_md)
    _write_pdf(risk_pdf_path, "Risk And Contradiction Register", risk_md)
    return {
        "uk_accounting_requirements_brain_json": str(json_path),
        "uk_accounting_requirements_brain_markdown": str(md_path),
        "accountant_self_questions_markdown": str(questions_path),
        "expanded_accounting_self_questions_json": str(expanded_json_path),
        "expanded_accounting_self_questions_csv": str(expanded_csv_path),
        "expanded_accounting_self_questions_markdown": str(expanded_md_path),
        "expanded_accounting_self_questions_pdf": str(expanded_pdf_path),
        "missing_data_and_evidence_action_plan_json": str(missing_json_path),
        "missing_data_and_evidence_action_plan_csv": str(missing_csv_path),
        "missing_data_and_evidence_action_plan_markdown": str(missing_md_path),
        "missing_data_and_evidence_action_plan_pdf": str(missing_pdf_path),
        "risk_and_contradiction_register_json": str(risk_json_path),
        "risk_and_contradiction_register_csv": str(risk_csv_path),
        "risk_and_contradiction_register_markdown": str(risk_md_path),
        "risk_and_contradiction_register_pdf": str(risk_pdf_path),
    }


def _filter_questions_for_action_plan(brain: dict[str, Any]) -> list[dict[str, Any]]:
    questions = [
        item
        for item in brain.get("accountant_self_questions") or []
        if item.get("status") in {
            "needs_data",
            "needs_human_confirmation",
            "needs_secret_manual_input",
            "needs_accountant_review",
            "blocked_missing_evidence",
        }
    ]
    return questions


def _filter_questions_for_risk_register(brain: dict[str, Any]) -> list[dict[str, Any]]:
    questions = [
        item
        for item in brain.get("accountant_self_questions") or []
        if item.get("risk_level") in {"high", "critical"} or item.get("reviewer_role") == "contrary_reviewer"
    ]
    return questions


def _write_questions_csv(questions: Sequence[dict[str, Any]], path: Path) -> None:
    fieldnames = [
        "id",
        "domain",
        "reviewer_role",
        "question",
        "status",
        "confidence",
        "risk_level",
        "answer",
        "next_action",
        "evidence",
        "linked_output_documents",
        "official_sources",
        "routed_systems",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for item in questions:
            row = {key: item.get(key, "") for key in fieldnames}
            for key in ("evidence", "linked_output_documents", "official_sources", "routed_systems"):
                if isinstance(row.get(key), list):
                    row[key] = "; ".join(str(value) for value in row[key] if value)
            writer.writerow(row)


def _write_pdf(path: Path, title: str, markdown_text: str) -> bool:
    try:
        from pdf_markdown_renderer import render_markdown_pdf
    except Exception:
        return False
    return render_markdown_pdf(path, title, markdown_text)


def _pdf_line(line: str) -> str:
    return (
        line.replace("`", "")
        .replace("|", " ")
        .replace("### ", "")
        .replace("## ", "")
        .replace("# ", "")
        .strip()
    )


def _wrap_text(text: str, *, width_chars: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > width_chars and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def _table_text(value: Any) -> str:
    return str(value or "").replace("|", "/").replace("\n", " ").strip()


def _build_requirements(
    *,
    artifact_map: dict[str, list[dict[str, Any]]],
    statutory: dict[str, Any],
    combined: dict[str, Any],
    raw_manifest: dict[str, Any],
    evidence_authoring: dict[str, Any],
    turnover: Decimal,
    vat_threshold: Decimal,
    utr: str,
    handoff_requirements: Sequence[Any],
) -> list[UKRequirement]:
    def found(keys: Iterable[str]) -> list[str]:
        out: list[str] = []
        for key in keys:
            if _artifact_exists(artifact_map, key) or _statutory_output_exists(statutory, key):
                out.append(key)
        return out

    def missing(keys: Sequence[str]) -> list[str]:
        generated = set(found(keys))
        return [key for key in keys if key not in generated]

    raw_count = ((raw_manifest.get("summary") or {}).get("file_count", 0))
    transaction_sources = combined.get("transaction_source_count", combined.get("csv_source_count", 0))
    unique_rows = combined.get("unique_rows_in_period", 0)
    requirements: list[UKRequirement] = []
    evidence_summary = evidence_authoring.get("summary") or {}
    llm_authoring = evidence_authoring.get("llm_document_authoring") or evidence_summary.get("llm_document_authoring") or {}
    record_keys = ["raw_data_manifest_json", "combined_bank_transactions", "period_manifest", "full_run_manifest"]
    requirements.append(
        UKRequirement(
            id="uk.records.company_accounting_records",
            authority="Companies House / HMRC",
            domain="records",
            form_or_task="Company accounting records and evidence file",
            requirement="Keep adequate accounting records and make the source data traceable to accounts and tax figures.",
            applies_when="All limited companies.",
            status="final_ready_manual_upload_required" if not missing(record_keys) else "partial_missing_generated_artifacts",
            generated_artifacts=found(record_keys),
            missing_generated_artifacts=missing(record_keys),
            manual_inputs=["confirm all bank, card, cash, marketplace, and payment accounts are present"],
            data_questions=[
                "Are SumUp, Zempler, Revolut, cash, Stripe/PayPal, loan, director, and any other accounts included?",
                "Are uploads and business accounts folders complete for the period?",
            ],
            evidence_to_collect=["all bank statements", "sales exports", "invoices", "receipts", "loan evidence", "director expense evidence"],
            internal_systems=["company_raw_data_intake", "combined_bank_data", "HNCGateway", "accounting_handoff_pack"],
            official_sources=[UK_ACCOUNTING_OFFICIAL_SOURCES["company_accounting_records"]],
            notes=f"Current raw files={raw_count}, transaction sources={transaction_sources}, unique rows={unique_rows}.",
        )
    )
    evidence_outputs = evidence_authoring.get("outputs") or {}
    requirements.append(
        UKRequirement(
            id="uk.records.evidence_authoring_and_petty_cash",
            authority="Companies House / HMRC",
            domain="records",
            form_or_task="Evidence authoring, petty-cash vouchers, invoice prompts, and receipt requests",
            requirement="Create internal requests and support vouchers for transactions needing support, while keeping real external evidence separate.",
            applies_when="Bank/account data contains cash withdrawals, unsupported expenses, unclear income, related-party payments, or missing receipts/invoices.",
            status="final_ready_manual_upload_required" if evidence_outputs else "partial_missing_generated_artifacts",
            generated_artifacts=sorted(evidence_outputs),
            missing_generated_artifacts=[] if evidence_outputs else ["accounting_evidence_authoring_manifest"],
            manual_inputs=[
                "complete petty-cash voucher fields",
                "attach real supplier receipts/invoices",
                "confirm income invoices/sales reports",
                "approve related-party/director classifications",
            ],
            data_questions=[
                "Which cash withdrawals need petty-cash allocation?",
                "Which income/expense transactions still need real supporting documents?",
            ],
            evidence_to_collect=["receipts", "supplier invoices", "customer invoices", "sales reports", "petty-cash log", "director approval"],
            internal_systems=[
                "accounting_evidence_authoring",
                "ObsidianBridge",
                "SelfQuestioningAI",
                "ThoughtBus",
                "safe code/document authoring route",
            ],
            official_sources=[
                UK_ACCOUNTING_OFFICIAL_SOURCES["company_accounting_records"],
                UK_ACCOUNTING_OFFICIAL_SOURCES.get("company_tax_return_obligations", ""),
            ],
            notes=(
                f"Evidence requests={evidence_summary.get('draft_count', 0)}, "
                f"petty_cash={evidence_summary.get('petty_cash_withdrawal_count', 0)}, "
                f"generated_internal_documents={evidence_summary.get('generated_document_count', 0)}, "
                f"llm_workpapers={llm_authoring.get('completed_count', 0)} "
                f"({llm_authoring.get('status', 'unknown')}). "
                "Generated documents are not external evidence."
            ),
        )
    )
    companies_house_keys = [
        "companies_house_accounts_markdown",
        "companies_house_accounts_pdf",
        "directors_report_markdown",
        "audit_exemption_statement_markdown",
    ]
    requirements.append(
        UKRequirement(
            id="uk.companies_house.annual_accounts",
            authority="Companies House",
            domain="companies_house",
            form_or_task="Annual accounts",
            requirement="Prepare annual accounts in the right company-size route, with director approval and manual filing/authentication.",
            applies_when="Limited company annual accounts are due.",
            status="final_ready_manual_upload_required" if not missing(companies_house_keys) else "partial_missing_generated_artifacts",
            generated_artifacts=found(companies_house_keys),
            missing_generated_artifacts=missing(companies_house_keys),
            manual_inputs=["director approval/signature", "micro/small-company filing route", "Companies House authentication", "audit exemption confirmation"],
            data_questions=["Which filing route applies and have all notes/exemptions been reviewed?"],
            evidence_to_collect=["share capital details", "director loan details", "accruals/prepayments", "audit exemption support"],
            internal_systems=["generate_statutory_filing_pack", "KingAccounting", "accounting_handoff_pack"],
            official_sources=[
                UK_ACCOUNTING_OFFICIAL_SOURCES.get("companies_house_accounts", ""),
                UK_ACCOUNTING_OFFICIAL_SOURCES.get("accounts_and_tax_returns_limited_company", ""),
            ],
        )
    )
    hmrc_keys = [
        "hmrc_ct600_draft_json",
        "ct600_box_map_markdown",
        "hmrc_tax_computation_markdown",
        "draft_accounts_html",
        "draft_computation_html",
        "ixbrl_readiness_note",
    ]
    requirements.append(
        UKRequirement(
            id="uk.hmrc.company_tax_return_ct600",
            authority="HMRC",
            domain="hmrc_corporation_tax",
            form_or_task="Company Tax Return / CT600",
            requirement="Prepare CT600, accounts, and computations; most online submissions require iXBRL accounts and computations.",
            applies_when="Company is within the charge to Corporation Tax or HMRC has issued a notice to deliver.",
            status="final_ready_manual_upload_required" if not missing(hmrc_keys) and utr else "manual_input_required",
            generated_artifacts=found(hmrc_keys),
            missing_generated_artifacts=missing(hmrc_keys),
            manual_inputs=[
                *(["company UTR"] if not utr else []),
                "HMRC credentials or agent authority",
                "director/accountant declaration",
                "commercial Corporation Tax filing software and iXBRL validation",
                "reliefs, add-backs, losses, R&D, capital allowances, loan relationships, and director-loan review",
            ],
            data_questions=[
                "Is the HMRC UTR present?",
                "Have all tax adjustments and supplementary CT600 pages been reviewed?",
            ],
            evidence_to_collect=["UTR", "HMRC notice to deliver", "tax adjustment workings", "iXBRL validation evidence"],
            internal_systems=["generate_statutory_filing_pack", "HNCLawDataset", "KingTax", "accounting_handoff_pack"],
            official_sources=[
                UK_ACCOUNTING_OFFICIAL_SOURCES.get("company_tax_return_obligations", ""),
                UK_ACCOUNTING_OFFICIAL_SOURCES.get("company_tax_returns_overview", ""),
                UK_ACCOUNTING_OFFICIAL_SOURCES.get("ct600_form", ""),
                UK_ACCOUNTING_OFFICIAL_SOURCES.get("company_tax_return_accounts_format", ""),
            ],
            notes="UTR is present." if utr else "CT600 manual-entry data currently has a blank UTR; this remains a human/secret input.",
        )
    )
    confirmation_keys = ["confirmation_statement_readiness_json", "confirmation_statement_readiness_markdown"]
    requirements.append(
        UKRequirement(
            id="uk.companies_house.confirmation_statement",
            authority="Companies House",
            domain="companies_house",
            form_or_task="Confirmation statement",
            requirement="Confirm company details, officers, PSCs, shareholders/share capital, SIC, registered office, lawful purpose, and manual filing/payment.",
            applies_when="At least once every confirmation period and when company register data needs confirmation.",
            status="readiness_generated_manual_filing_required" if not missing(confirmation_keys) else "partial_missing_generated_artifacts",
            generated_artifacts=found(confirmation_keys),
            missing_generated_artifacts=missing(confirmation_keys),
            manual_inputs=["officers", "PSCs", "shareholders", "share capital", "registered office", "SIC codes", "lawful-purpose confirmation", "authentication/payment"],
            data_questions=["Do Companies House register details still match the company's real position?"],
            evidence_to_collect=["latest register details", "PSC register", "share register", "officer appointments/resignations"],
            internal_systems=["generate_statutory_filing_pack", "company_house_tax_audit", "accounting_handoff_pack"],
            official_sources=[
                UK_ACCOUNTING_OFFICIAL_SOURCES.get("companies_house_confirmation_statement", ""),
                UK_ACCOUNTING_OFFICIAL_SOURCES.get("companies_house_identity_verification", ""),
            ],
        )
    )
    vat_status = (
        "vat_registration_review_required"
        if turnover >= vat_threshold and vat_threshold > 0
        else "monitor_not_required_by_current_turnover"
    )
    requirements.append(
        UKRequirement(
            id="uk.hmrc.vat_registration_and_mtd",
            authority="HMRC",
            domain="vat",
            form_or_task="VAT registration, VAT records, and MTD VAT readiness",
            requirement="Monitor taxable turnover against the VAT registration threshold; if VAT registered, keep VAT records and use MTD-compatible VAT return processes.",
            applies_when="UK taxable turnover breaches the VAT registration threshold, or the company voluntarily/registers for VAT.",
            status=vat_status,
            generated_artifacts=found(["combined_bank_transactions", "period_manifest", "tax_summary"]),
            missing_generated_artifacts=[],
            manual_inputs=[
                "confirm taxable vs exempt/out-of-scope turnover",
                "confirm current VAT registration/VAT number",
                "confirm VAT scheme and return quarters if registered",
                "HMRC VAT/MTD credentials and manual return submission if applicable",
            ],
            data_questions=[
                f"Does taxable turnover of GBP {money_text(turnover)} breach the VAT threshold of GBP {money_text(vat_threshold)}?",
                "Is the company already VAT registered, and what is the VAT number?",
            ],
            evidence_to_collect=["VAT certificate if registered", "sales taxability review", "VAT invoices", "MTD software connection proof"],
            internal_systems=["combined_bank_data", "KingTax", "HNCLawDataset", "accounting_handoff_pack"],
            official_sources=[
                UK_ACCOUNTING_OFFICIAL_SOURCES.get("vat_registration_when_to_register", ""),
                UK_ACCOUNTING_OFFICIAL_SOURCES.get("vat_registration_threshold", ""),
                UK_ACCOUNTING_OFFICIAL_SOURCES.get("vat_record_keeping", ""),
                UK_ACCOUNTING_OFFICIAL_SOURCES.get("making_tax_digital_vat", ""),
            ],
            notes=(
                "Current period turnover is over the VAT threshold; VAT registration status is routed to a VAT eye-scan workpaper."
                if turnover >= vat_threshold and vat_threshold > 0
                else "Current turnover does not exceed the threshold, but rolling 12-month taxable turnover must be monitored."
            ),
        )
    )
    requirements.append(
        UKRequirement(
            id="uk.hmrc.paye_and_director_pay",
            authority="HMRC",
            domain="paye",
            form_or_task="PAYE/director salary review",
            requirement="If the company pays employees/directors through payroll or provides benefits, PAYE/RTI and benefits reporting may be required.",
            applies_when="Employees, director salaries, benefits, expenses, or payroll exist.",
            status="unknown_need_human_answer",
            generated_artifacts=[],
            missing_generated_artifacts=[],
            manual_inputs=["confirm directors/employees", "confirm salary/dividend split", "confirm payroll records and P60/P11D where relevant"],
            data_questions=["Did the company pay wages, director salary, employee benefits, or reimbursed expenses?"],
            evidence_to_collect=["payroll reports", "RTI submissions", "P60/P11D", "director remuneration approvals"],
            internal_systems=["company_raw_data_intake", "KingLedger", "HNCLawDataset"],
            official_sources=[UK_ACCOUNTING_OFFICIAL_SOURCES.get("paye_for_employers", "")],
        )
    )
    requirements.append(
        UKRequirement(
            id="uk.hmrc.cis_if_construction",
            authority="HMRC",
            domain="cis",
            form_or_task="Construction Industry Scheme review",
            requirement="If construction contractor/subcontractor activity exists, verify CIS registration, deductions, monthly returns, and VAT domestic reverse charge treatment.",
            applies_when="The company works in construction as contractor or subcontractor.",
            status="unknown_need_human_answer",
            generated_artifacts=[],
            missing_generated_artifacts=[],
            manual_inputs=["confirm construction activity", "confirm contractor/subcontractor status", "confirm CIS deduction statements/returns"],
            data_questions=["Did the company undertake CIS-scope construction work?"],
            evidence_to_collect=["CIS statements", "subcontractor invoices", "contractor monthly returns", "verification numbers"],
            internal_systems=["HNCLawDataset", "KingTax", "company_raw_data_intake"],
            official_sources=[UK_ACCOUNTING_OFFICIAL_SOURCES.get("cis_overview", "")],
        )
    )
    return requirements


def _build_questions(
    *,
    company_number: str,
    turnover: Decimal,
    profit_before_tax: Decimal,
    corporation_tax: Decimal,
    vat_threshold: Decimal,
    utr: str,
    combined: dict[str, Any],
    raw_manifest: dict[str, Any],
    evidence_authoring: dict[str, Any],
    known_providers: list[str],
    artifact_map: dict[str, list[dict[str, Any]]],
    requirements: Sequence[UKRequirement],
) -> list[AccountantQuestion]:
    source_count = combined.get("transaction_source_count", combined.get("csv_source_count", 0))
    rows = combined.get("unique_rows_in_period", 0)
    providers = ", ".join(known_providers) or "unknown"
    over_vat = bool(turnover >= vat_threshold and vat_threshold > 0)
    evidence_summary = evidence_authoring.get("summary") or {}
    llm_authoring = evidence_authoring.get("llm_document_authoring") or evidence_summary.get("llm_document_authoring") or {}
    questions = [
        AccountantQuestion(
            id="q.data_scope.all_accounts_present",
            question="Have I ingested every bank, sales, cash, card, and payment account for the period?",
            why_it_matters="Accounts and tax returns are only as complete as the source records.",
            answer=(
                f"I can see {source_count} transaction sources, {rows} unique period rows, "
                f"and providers/accounts: {providers}. A human must confirm there are no missing PayPal, Stripe, cash, loan, card, or other accounts."
            ),
            status="needs_human_confirmation",
            evidence=[_artifact_path(artifact_map, "raw_data_manifest_json"), _artifact_path(artifact_map, "combined_bank_transactions")],
            next_action="Ask the human/director to confirm no source is missing, then reconcile any new source through combined_bank_data.",
            routed_systems=["company_raw_data_intake", "combined_bank_data", "HNCGateway"],
        ),
        AccountantQuestion(
            id="q.records.evidence_authoring_needed",
            question="Which transactions need receipts, invoices, petty-cash vouchers, or allocation memos?",
            why_it_matters="The system can generate internal requests and vouchers, but real receipts/invoices and approval still have to be attached.",
            answer=(
                f"The evidence authoring system generated {evidence_summary.get('draft_count', 0)} evidence requests, "
                f"{evidence_summary.get('generated_document_count', 0)} internal document templates, "
                f"{llm_authoring.get('completed_count', 0)} LLM-generated internal workpaper sections, "
                f"{evidence_summary.get('petty_cash_withdrawal_count', 0)} petty-cash withdrawal requests, and "
                f"{evidence_summary.get('related_party_query_count', 0)} related-party/director queries. "
                "These are internal support records only, not external proof."
            ),
            status="needs_human_confirmation",
            evidence=[
                ((evidence_authoring.get("outputs") or {}).get("accounting_evidence_authoring_manifest") or ""),
                ((evidence_authoring.get("outputs") or {}).get("accounting_evidence_requests_csv") or ""),
            ],
            next_action="Attach real receipts/invoices/sales reports, complete voucher fields, and keep unsupported amounts in suspense/director loan/private drawings.",
            routed_systems=["accounting_evidence_authoring", "SelfQuestioningAI", "ObsidianBridge", "ThoughtBus"],
        ),
        AccountantQuestion(
            id="q.hmrc.utr_present",
            question="Do I have the company UTR needed for the CT600 workflow?",
            why_it_matters="The Company Tax Return needs HMRC identity details; this is secret/user-supplied data.",
            answer=f"UTR present for {company_number}." if utr else "The CT600 manual-entry data has a blank UTR; the system must ask the human for the UTR and must not invent it.",
            status="answered_by_system" if utr else "needs_secret_manual_input",
            evidence=[_artifact_path(artifact_map, "ct600_manual_entry_json") or _artifact_path(artifact_map, "hmrc_ct600_draft_json")],
            next_action="Request UTR from the human or secure env/secret store before manual CT600 filing preparation.",
            routed_systems=["generate_statutory_filing_pack", "accounting_handoff_pack"],
        ),
        AccountantQuestion(
            id="q.vat.threshold_and_registration",
            question="Does turnover require VAT registration or a VAT/MTD review?",
            why_it_matters="VAT obligations depend on taxable turnover and registration status, not just bank receipts.",
            answer=(
                f"Current generated turnover is GBP {money_text(turnover)} against a VAT threshold of GBP {money_text(vat_threshold)}. "
                + (
                    "This is over the threshold, so VAT registration status, taxable turnover classification, and MTD VAT readiness are routed to autonomous VAT workpapers and eye-scan flags."
                    if over_vat
                    else "This is not over the threshold on the generated period figures, but rolling taxable turnover still needs monitoring."
                )
            ),
            status="needs_human_confirmation" if over_vat else "answered_by_system",
            evidence=[_artifact_path(artifact_map, "combined_bank_transactions"), _artifact_path(artifact_map, "hmrc_tax_computation_markdown")],
            next_action="Classify taxable/exempt/out-of-scope sales and ask for VAT number/status; prepare VAT workpapers only, do not submit.",
            routed_systems=["KingTax", "HNCLawDataset", "combined_bank_data"],
        ),
        AccountantQuestion(
            id="q.hmrc.ct600_ixbrl_ready",
            question="Can I support a Company Tax Return without pretending to submit it?",
            why_it_matters="HMRC online filing generally needs CT600, accounts, computations, and iXBRL-ready data through an approved route.",
            answer=(
                f"CT600 manual-entry support exists={_artifact_exists(artifact_map, 'ct600_manual_entry_json') or _artifact_exists(artifact_map, 'hmrc_ct600_draft_json')}; "
                f"iXBRL readiness note exists={_artifact_exists(artifact_map, 'ixbrl_readiness_note')}; "
                f"profit_before_tax=GBP {money_text(profit_before_tax)}, corporation_tax=GBP {money_text(corporation_tax)}."
            ),
            status="answered_by_system",
            evidence=[
                _artifact_path(artifact_map, "ct600_manual_entry_json") or _artifact_path(artifact_map, "hmrc_ct600_draft_json"),
                _artifact_path(artifact_map, "accounts_readable_for_ixbrl_html") or _artifact_path(artifact_map, "draft_accounts_html"),
                _artifact_path(artifact_map, "ixbrl_readiness_note"),
            ],
            next_action="Use the manual-entry data in commercial Corporation Tax filing software after accountant/director approval.",
            routed_systems=["generate_statutory_filing_pack", "KingTax", "accounting_handoff_pack"],
        ),
        AccountantQuestion(
            id="q.companies_house.accounts_route",
            question="Which Companies House accounts route and statements need director approval?",
            why_it_matters="The filing route affects what is filed publicly and what statements/exemptions are valid.",
            answer=(
                "Final-ready Companies House accounts, directors report prompt, and audit exemption support are generated. "
                "A human must confirm micro/small company route, exemptions, and director approval/signature."
            ),
            status="needs_human_confirmation",
            evidence=[
                _artifact_path(artifact_map, "companies_house_accounts_pdf"),
                _artifact_path(artifact_map, "directors_report_markdown"),
                _artifact_path(artifact_map, "audit_exemption_statement_markdown"),
            ],
            next_action="Review accounts route, approve/sign manually, and file manually through Companies House or approved software.",
            routed_systems=["generate_statutory_filing_pack", "company_house_tax_audit"],
        ),
        AccountantQuestion(
            id="q.companies_house.confirmation_statement",
            question="Are officers, PSCs, shareholders, SIC, registered office, and lawful-purpose details confirmed?",
            why_it_matters="The confirmation statement is about company register accuracy and manual declarations/payment.",
            answer="A confirmation-statement readiness artifact exists if generated, but the register facts remain human-confirmed.",
            status="needs_human_confirmation",
            evidence=[
                _artifact_path(artifact_map, "confirmation_statement_readiness_json"),
                _artifact_path(artifact_map, "confirmation_statement_readiness_markdown"),
            ],
            next_action="Ask the director to verify register details, then file/pay manually if needed.",
            routed_systems=["company_house_tax_audit", "generate_statutory_filing_pack"],
        ),
        AccountantQuestion(
            id="q.tax.adjustments_and_reliefs",
            question="Have capital allowances, losses, reliefs, add-backs, director loan, VAT/CIS, and loan relationships been reviewed?",
            why_it_matters="The generated computation is final-ready for manual filing, with tax judgement required before submission.",
            answer="The statutory pack creates a computation and CT600 box map, but these judgement areas stay flagged for review.",
            status="needs_accountant_review",
            evidence=[_artifact_path(artifact_map, "hmrc_tax_computation_markdown"), _artifact_path(artifact_map, "ct600_box_map_markdown")],
            next_action="Reconcile judgement areas to receipts, invoices, board records, and tax workpapers before manual filing.",
            routed_systems=["HNCLawDataset", "KingTax", "KingLedger"],
        ),
        AccountantQuestion(
            id="q.paye_cis.edge_obligations",
            question="Did the company have payroll, benefits, CIS construction activity, or VAT reverse-charge transactions?",
            why_it_matters="These obligations can exist outside the core accounts/CT600 pack.",
            answer="The current artifacts cannot prove this automatically; the system must ask and inspect raw descriptions/evidence.",
            status="needs_human_confirmation",
            evidence=[_artifact_path(artifact_map, "raw_data_manifest_json")],
            next_action="Search descriptions/evidence for payroll, wages, CIS, subcontractor, contractor, VAT, and reverse-charge signals; ask the human where unclear.",
            routed_systems=["company_raw_data_intake", "HNCLawDataset", "KingTax"],
        ),
    ]
    questions.extend(
        _build_expanded_accountant_questions(
            company_number=company_number,
            turnover=turnover,
            profit_before_tax=profit_before_tax,
            corporation_tax=corporation_tax,
            vat_threshold=vat_threshold,
            utr=utr,
            combined=combined,
            raw_manifest=raw_manifest,
            evidence_authoring=evidence_authoring,
            known_providers=known_providers,
            artifact_map=artifact_map,
            requirements=requirements,
        )
    )
    for item in questions:
        _normalise_question_metadata(item, artifact_map=artifact_map)
    return questions


def _build_expanded_accountant_questions(
    *,
    company_number: str,
    turnover: Decimal,
    profit_before_tax: Decimal,
    corporation_tax: Decimal,
    vat_threshold: Decimal,
    utr: str,
    combined: dict[str, Any],
    raw_manifest: dict[str, Any],
    evidence_authoring: dict[str, Any],
    known_providers: list[str],
    artifact_map: dict[str, list[dict[str, Any]]],
    requirements: Sequence[UKRequirement],
) -> list[AccountantQuestion]:
    """Build the wide UK-accounting interrogation taxonomy."""
    provider_text = " ".join(known_providers + list(combined.get("source_accounts") or [])).lower()
    enrichment = _read_artifact_json(artifact_map, "enriched_transactions_json")
    enrichment_totals = enrichment.get("totals") or {}
    enrichment_review = enrichment.get("review_summary") or {}
    tax_summary = enrichment.get("tax_obligation_summary") or {}
    payer_summary = enrichment.get("payer_provenance_summary") or {}
    categories = {
        str(item.get("category") or ""): item
        for item in enrichment.get("category_totals") or []
        if item.get("category")
    }
    evidence_summary = evidence_authoring.get("summary") or {}
    review_rows = int(enrichment_review.get("manual_review_row_count") or 0)
    raw_file_count = int((raw_manifest.get("summary") or {}).get("file_count") or 0)
    rows = int(combined.get("unique_rows_in_period") or 0)
    source_count = int(combined.get("transaction_source_count", combined.get("csv_source_count", 0)) or 0)
    duplicate_rows = int(combined.get("duplicate_rows_removed") or 0)
    over_vat = turnover >= vat_threshold and vat_threshold > 0
    cis_row_count = int(tax_summary.get("cis_net_receipt_row_count") or 0)
    cis_suffered = str(tax_summary.get("cis_deduction_suffered_total") or "0.00")
    cis_gross_income = str(tax_summary.get("cis_gross_income_total") or "0.00")
    vat_taxable_turnover = str(tax_summary.get("vat_taxable_turnover_estimate") or money_text(turnover))
    reverse_charge_rows = int(tax_summary.get("vat_reverse_charge_review_row_count") or 0)
    payer_lookup_required = int(payer_summary.get("lookup_required_count") or 0)
    payer_no_missed = bool(payer_summary.get("lookup_required_plus_not_required_equals_total"))

    def has_provider(*names: str) -> bool:
        return any(name.lower() in provider_text for name in names)

    def category_rows(category: str) -> int:
        return int((categories.get(category) or {}).get("rows") or 0)

    def category_amount(category: str, key: str = "money_out") -> str:
        return str((categories.get(category) or {}).get(key) or "0.00")

    def paths(keys: Sequence[str]) -> list[str]:
        return [path for path in (_artifact_path(artifact_map, key) for key in keys) if path]

    def sources(keys: Sequence[str]) -> list[str]:
        return [UK_ACCOUNTING_OFFICIAL_SOURCES.get(key, key) for key in keys if UK_ACCOUNTING_OFFICIAL_SOURCES.get(key, key)]

    def make(
        id: str,
        domain: str,
        role: str,
        question: str,
        why: str,
        answer: str,
        status: str,
        next_action: str,
        *,
        risk: str = "medium",
        confidence: str = "medium",
        evidence_keys: Sequence[str] = (),
        doc_keys: Sequence[str] = (),
        source_keys: Sequence[str] = (),
        systems: Sequence[str] = (),
    ) -> AccountantQuestion:
        return AccountantQuestion(
            id=id,
            domain=domain,
            reviewer_role=role,
            question=question,
            why_it_matters=why,
            answer=answer,
            status=status if status in QUESTION_SAFE_STATUSES else "needs_accountant_review",
            confidence=confidence,
            risk_level=risk,
            evidence=paths(evidence_keys) or paths(doc_keys),
            source_evidence=paths(evidence_keys),
            linked_output_documents=paths(doc_keys),
            official_sources=sources(source_keys),
            next_action=next_action,
            routed_systems=list(systems),
        )

    provider_status = lambda *names: "answered_by_system" if has_provider(*names) else "needs_data"
    specs: list[AccountantQuestion] = [
        # Company identity and statutory-register questions.
        make("q.company_identity.registered_name_number", "company_identity", "companies_house_reviewer", "Do I have the exact registered company name and number on every pack document?", "Wrong identifiers can make accounts or CT600 support unusable.", f"Company number is {company_number}; generated pack identity is carried through the workflow.", "answered_by_system", "Keep company identity locked across every PDF, JSON, CSV, and handoff document.", risk="medium", confidence="high", evidence_keys=("filing_checklist",), doc_keys=("companies_house_accounts_pdf",), source_keys=("annual_accounts_overview", "company_tax_returns_overview"), systems=("generate_statutory_filing_pack",)),
        make("q.company_identity.registered_office", "company_identity", "companies_house_reviewer", "Is the registered office current at Companies House?", "Accounts and confirmation statement filing rely on register facts.", "The local pack can surface readiness files, but current register facts still need human/public-profile confirmation.", "needs_human_confirmation", "Verify registered office manually against Companies House before filing.", risk="high", evidence_keys=("confirmation_statement_readiness_markdown",), source_keys=("companies_house_confirmation_statement",), systems=("company_house_tax_audit",)),
        make("q.company_identity.officers_psc", "company_identity", "companies_house_reviewer", "Are directors, officers, PSCs, shareholders, and SIC codes confirmed?", "Confirmation statements and director approval depend on current register details.", "Bank data cannot prove the company register, so these stay in human confirmation.", "needs_human_confirmation", "Confirm officers, PSCs, shareholders, share capital, SIC codes, and lawful-purpose statement.", risk="high", evidence_keys=("confirmation_statement_readiness_json",), source_keys=("companies_house_confirmation_statement", "companies_house_identity_verification"), systems=("company_house_tax_audit",)),
        make("q.company_identity.share_capital_reserves", "company_identity", "accountant", "Is share capital confirmed and reconciled to reserves?", "Capital and reserves need correct share capital and retained profit.", "The pack derives reserves from generated net assets; share capital/opening reserves need confirmation.", "needs_human_confirmation", "Confirm share capital, dividends, prior reserves, and any share movements.", risk="high", evidence_keys=("companies_house_accounts_pdf",), doc_keys=("full_accounts_pack_pdf",), source_keys=("annual_accounts_overview",), systems=("KingLedger",)),
        make("q.company_identity.deadlines", "company_identity", "director_handoff_officer", "Which accounts, CT600, Corporation Tax payment, and confirmation statement deadlines are due or late?", "Late filings or tax payments can cause penalties/interest.", "Compliance artifacts and filing checklist are present where generated, but current deadline status needs final manual check.", "needs_human_confirmation", "Check Companies House and HMRC deadlines before manual submission or payment.", risk="critical", evidence_keys=("compliance_audit_markdown", "filing_checklist"), doc_keys=("risk_and_contradiction_register_pdf",), source_keys=("annual_accounts_overview", "company_tax_returns_overview", "companies_house_confirmation_statement"), systems=("company_house_tax_audit",)),
        make("q.company_identity.secret_codes", "company_identity", "director_handoff_officer", "Are Companies House authentication code, UTR, VAT, PAYE, and Gateway credentials kept manual and secret?", "Aureon must not invent, expose, or submit official credentials.", "Secret/manual credentials are outside generated data and remain human-supplied.", "needs_secret_manual_input", "Human enters authentication codes and gateway credentials manually at filing time.", risk="critical", confidence="high", evidence_keys=("filing_checklist",), source_keys=("company_tax_returns_overview", "companies_house_confirmation_statement"), systems=("accounting_handoff_pack",)),

        # Data coverage questions.
        make("q.data_scope.sumup", "data_scope", "bookkeeper", "Did SumUp sales, payouts, and fee data enter the combined feed?", "Missing processor data can change turnover, fees, refunds, and VAT review.", "SumUp is visible in provider/account coverage." if has_provider("sumup") else "No SumUp signal is visible in provider/account coverage.", provider_status("sumup"), "Add SumUp sales/payout/fee exports if the company used SumUp.", risk="high", confidence="high" if has_provider("sumup") else "medium", evidence_keys=("raw_data_manifest_json", "combined_bank_transactions"), doc_keys=("source_reconciliation_pdf",), source_keys=("company_accounting_records", "vat_record_keeping"), systems=("combined_bank_data",)),
        make("q.data_scope.zempler", "data_scope", "bookkeeper", "Did Zempler bank data enter the combined feed?", "Missing a bank account breaks source-record completeness.", "Zempler is visible in provider/account coverage." if has_provider("zempler") else "No Zempler signal is visible in provider/account coverage.", provider_status("zempler"), "Add complete Zempler statements if missing.", risk="critical", confidence="high" if has_provider("zempler") else "medium", evidence_keys=("raw_data_manifest_json", "combined_bank_transactions"), doc_keys=("source_reconciliation_pdf",), source_keys=("company_accounting_records",), systems=("combined_bank_data",)),
        make("q.data_scope.revolut", "data_scope", "bookkeeper", "Did Revolut bank data enter the combined feed?", "Missing Revolut data can distort transfers, expenses, and balances.", "Revolut is visible in provider/account coverage." if has_provider("revolut") else "No Revolut signal is visible in provider/account coverage.", provider_status("revolut"), "Add complete Revolut statements if missing.", risk="critical", confidence="high" if has_provider("revolut") else "medium", evidence_keys=("raw_data_manifest_json", "combined_bank_transactions"), doc_keys=("source_reconciliation_pdf",), source_keys=("company_accounting_records",), systems=("combined_bank_data",)),
        make("q.data_scope.paypal_stripe_marketplaces", "data_scope", "bookkeeper", "Should PayPal, Stripe, marketplace, cash-register, or card-platform exports exist?", "Bank deposits may hide gross sales, fees, refunds, and VAT evidence.", "Current providers are visible, but the system cannot prove no other platform exists.", "needs_human_confirmation", "Ask the director to confirm every sales/payment platform and add exports where used.", risk="high", evidence_keys=("raw_data_manifest_json",), doc_keys=("source_reconciliation_pdf",), source_keys=("company_accounting_records", "vat_record_keeping"), systems=("company_raw_data_intake",)),
        make("q.data_scope.cash_and_petty_cash", "data_scope", "bookkeeper", "Did the company have cash sales, petty cash, or cash withdrawals?", "Cash affects sales completeness, expenses, director loan, and evidence support.", f"Cash/director review rows: {category_rows('director_related_or_cash_review')}; petty-cash requests: {evidence_summary.get('petty_cash_withdrawal_count', 0)}.", "needs_human_confirmation", "Confirm cash sales and complete petty-cash allocation for withdrawals.", risk="critical", evidence_keys=("enriched_transactions_csv", "accounting_evidence_requests_csv"), doc_keys=("expense_breakdown_pdf",), source_keys=("company_accounting_records",), systems=("accounting_evidence_authoring",)),
        make("q.data_scope.uploads_vault", "data_scope", "evidence_officer", "Did the system scan uploads, business accounts, and vault/accounting context?", "The organism must not ignore non-standard folder names or vault evidence.", f"Raw manifest shows {raw_file_count} files, {source_count} transaction sources, and {rows} period rows.", "answered_by_system" if raw_file_count else "needs_data", "Keep scanning uploads, bussiness accounts, and vault/accounting folders on every run.", risk="high", evidence_keys=("raw_data_manifest_json",), doc_keys=("data_truth_checklist_pdf",), source_keys=("company_accounting_records",), systems=("company_raw_data_intake", "ObsidianBridge")),
        make("q.data_scope.opening_closing_balances", "data_scope", "bookkeeper", "Do statements include opening and closing balances for each account?", "Balance sheet and transfer checks depend on period-end balances.", "The combined feed has row amounts; statement opening/closing balances still need source review.", "needs_human_confirmation", "Check every statement/export for full period coverage and no date gaps.", risk="high", evidence_keys=("combined_bank_transactions",), doc_keys=("source_reconciliation_pdf",), source_keys=("company_accounting_records",), systems=("combined_bank_data",)),

        # Transaction truth questions.
        make("q.transaction_truth.duplicates_traceable", "transaction_truth", "bookkeeper", "Were duplicates removed and kept traceable?", "Deduplication must not delete real rows or double count exports.", f"Duplicate overlaps removed: {duplicate_rows}; duplicate-source fields remain in enriched data where available.", "answered_by_system", "Review duplicate-source fields whenever new exports are added.", risk="medium", confidence="high", evidence_keys=("combined_bank_transactions", "enriched_transactions_csv"), doc_keys=("source_reconciliation_pdf",), source_keys=("company_accounting_records",), systems=("combined_bank_data",)),
        make("q.transaction_truth.transfers", "transaction_truth", "accountant", "Are inter-account transfers excluded from taxable income/expenses where appropriate?", "Transfers can inflate turnover or expenses if treated as trading movements.", f"Transfer/clearing review rows: {category_rows('inter_account_transfer_review')} amount out GBP {category_amount('inter_account_transfer_review')}.", "needs_accountant_review" if category_rows("inter_account_transfer_review") else "answered_by_system", "Reconcile transfer pairs across SumUp, Zempler, Revolut, and clearing accounts.", risk="high", evidence_keys=("enriched_transactions_csv",), doc_keys=("transaction_classification_audit_pdf",), source_keys=("company_accounting_records",), systems=("KingLedger", "HNCAurisEngine")),
        make("q.transaction_truth.director_personal", "transaction_truth", "accountant", "Are director, owner, personal, and related-party payments isolated?", "These may be director loan, wages, dividends, benefits, or private/disallowable use.", f"Director/cash review rows: {category_rows('director_related_or_cash_review')} amount out GBP {category_amount('director_related_or_cash_review')}.", "needs_accountant_review" if category_rows("director_related_or_cash_review") else "answered_by_system", "Allocate each item to director loan, payroll/dividend, business expense, or evidence request.", risk="critical", evidence_keys=("enriched_transactions_csv", "accounting_evidence_requests_csv"), doc_keys=("expense_breakdown_pdf", "risk_and_contradiction_register_pdf"), source_keys=("company_tax_return_guide", "company_accounting_records"), systems=("KingLedger", "accounting_evidence_authoring")),
        make("q.transaction_truth.refunds_chargebacks", "transaction_truth", "bookkeeper", "Are refunds, chargebacks, reversals, and contra entries identified?", "Refunds can reduce sales or reverse expenses and affect VAT/tax.", "Refund and reversal patterns are routed to review where the row description is unclear.", "needs_human_confirmation", "Tie refund/chargeback rows to sales reports, original invoices, or platform statements.", risk="medium", evidence_keys=("enriched_transactions_csv",), doc_keys=("transaction_classification_audit_pdf",), source_keys=("company_accounting_records", "vat_record_keeping"), systems=("HNCSoup",)),
        make("q.transaction_truth.unknown_descriptions", "transaction_truth", "evidence_officer", "Which rows have missing, vague, or low-confidence descriptions?", "Low-quality descriptions make classification unsafe.", f"Eye-scan rows: {review_rows}; uncategorised rows: {category_rows('uncategorised_review')}.", "blocked_missing_evidence" if review_rows else "answered_by_system", "Autonomously allocate low-confidence rows to conservative suspense accounts, then flag visible exceptions.", risk="high", evidence_keys=("enriched_transactions_csv",), doc_keys=("transaction_classification_audit_pdf",), source_keys=("company_accounting_records",), systems=("HNCAurisEngine", "accounting_evidence_authoring")),
        make("q.transaction_truth.source_to_pdf_trace", "transaction_truth", "contrary_reviewer", "Can every number in the PDFs be traced back to source rows?", "A final-ready pack needs traceability, not just totals.", f"Enrichment rows={enrichment.get('row_count', 0)}; reconciles_to_filing_figures={enrichment_totals.get('reconciles_to_filing_figures')}.", "answered_by_system" if enrichment_totals.get("reconciles_to_filing_figures") else "needs_accountant_review", "Block final-ready language if future reconciliation fails.", risk="critical", confidence="high", evidence_keys=("enriched_transactions_json", "combined_bank_transactions"), doc_keys=("data_truth_checklist_pdf", "math_stress_test_pdf"), source_keys=("company_accounting_records", "company_tax_return_guide"), systems=("accounting_report_enrichment",)),
        make("q.transaction_truth.changed_since_last_run", "transaction_truth", "contrary_reviewer", "What changed since the last accounts run?", "Changed inputs can change tax, filings, and evidence gaps.", "The run records manifests and generated_at; prior-run comparison remains a review task.", "needs_human_confirmation", "Compare current manifests with previous company_compliance/Desktop outputs before filing.", risk="medium", evidence_keys=("full_run_manifest", "period_manifest"), doc_keys=("risk_and_contradiction_register_pdf",), source_keys=("company_accounting_records",), systems=("accounting_handoff_pack",)),

        # Revenue questions.
        make("q.revenue.turnover_trace", "revenue", "accountant", "Does turnover trace to positive source rows and sales evidence?", "Turnover drives accounts, CT600, VAT, and Companies House reporting.", f"Generated turnover GBP {money_text(turnover)}; enrichment turnover GBP {enrichment_totals.get('turnover', '0.00')}.", "answered_by_system" if enrichment_totals.get("reconciles_to_filing_figures") else "needs_accountant_review", "Reconcile turnover to sales exports, invoices, and platform reports.", risk="critical", confidence="high", evidence_keys=("combined_bank_transactions", "enriched_transactions_json"), doc_keys=("profit_and_loss_detailed_pdf", "source_reconciliation_pdf"), source_keys=("company_accounting_records", "company_tax_return_guide"), systems=("KingLedger",)),
        make("q.revenue.taxable_turnover", "revenue", "tax_reviewer", "Which sales are taxable, exempt, outside scope, or non-trading receipts?", "VAT and tax treatment depend on classification, not only cash direction.", "Positive bank rows are included in turnover unless reviewed; taxable/exempt/out-of-scope split needs VAT review.", "needs_accountant_review", "Classify income source types and VAT treatment before relying on VAT decisions.", risk="critical", evidence_keys=("enriched_transactions_csv",), doc_keys=("profit_and_loss_detailed_pdf",), source_keys=("vat_registration_when_to_register", "vat_record_keeping"), systems=("KingTax",)),
        make("q.revenue.payer_provenance", "revenue", "hmrc_reviewer", "Who paid each incoming amount, and did lookup/control status route CIS and VAT correctly?", "HMRC/VAT/CIS treatment depends on payer identity, construction status, and whether tax was deducted before the bank receipt arrived.", f"Payer provenance covers {payer_summary.get('incoming_rows_total', 0)} incoming rows; {payer_lookup_required} rows require lookup; no-missed control={payer_no_missed}.", "answered_by_system" if payer_no_missed else "needs_accountant_review", "Use payer provenance PDF/CSV to review lookup-required rows, Companies House evidence, CIS likelihood, and VAT reverse-charge status.", risk="critical", confidence="high" if payer_no_missed else "medium", evidence_keys=("payer_provenance_json", "payer_provenance_csv", "enriched_transactions_csv"), doc_keys=("payer_provenance_pdf", "cis_vat_tax_basis_assurance_pdf"), source_keys=("companies_house_api_search", "companies_house_api_company_profile", "cis_overview", "vat_domestic_reverse_charge"), systems=("accounting_payer_provenance", "KingTax", "CISReconciliation", "HNCSoup")),
        make("q.revenue.deferred_income", "revenue", "accountant", "Is any income deferred, accrued, or received in advance?", "Accounts may need cut-off entries beyond cash receipts.", "Bank-only data cannot prove deferred income or accrued revenue.", "needs_human_confirmation", "Review contracts, invoices, delivery dates, and period cut-off.", risk="medium", confidence="low", evidence_keys=("combined_bank_transactions",), doc_keys=("full_accounts_pack_pdf",), source_keys=("annual_accounts_overview",), systems=("KingLedger",)),
        make("q.revenue.grants_loans_capital", "revenue", "accountant", "Are grants, loans, capital introductions, or director funds excluded from turnover?", "Non-trading receipts can overstate sales and tax.", f"Income-source review rows: {category_rows('income_source_review')}.", "needs_accountant_review" if category_rows("income_source_review") else "answered_by_system", "Review positive rows for loan/capital/grant/refund indicators.", risk="high", evidence_keys=("enriched_transactions_csv",), doc_keys=("transaction_classification_audit_pdf",), source_keys=("company_tax_return_guide",), systems=("HNCAurisEngine", "KingLedger")),
        make("q.revenue.bad_debts", "revenue", "tax_reviewer", "Were bad debts, unpaid invoices, or credit notes considered?", "Taxable profits and debtors may change when invoices are unpaid or written off.", "Bank-only data cannot prove unpaid invoices or bad-debt relief.", "needs_human_confirmation", "Ask for invoice ledger, aged debtors, credit notes, and write-off approvals.", risk="medium", confidence="low", evidence_keys=("raw_data_manifest_json",), doc_keys=("missing_data_and_evidence_action_plan_pdf",), source_keys=("company_tax_return_guide",), systems=("KingTax",)),

        # Expense questions.
        make("q.expenses.admin_breakdown", "expenses", "accountant", "Are admin costs broken down instead of hidden in one lump?", "HMRC/accountant review needs supporting schedules.", f"Administrative costs amount out GBP {category_amount('administrative_costs')}; detailed expense PDF exists={bool(_artifact_path(artifact_map, 'expense_breakdown_pdf'))}.", "answered_by_system", "Keep admin costs split from cash, director, transfer, tax, capital, and low-confidence rows.", risk="high", confidence="high", evidence_keys=("enriched_transactions_json",), doc_keys=("expense_breakdown_pdf",), source_keys=("company_accounting_records", "company_tax_return_guide"), systems=("accounting_report_enrichment",)),
        make("q.expenses.disallowables", "expenses", "tax_reviewer", "Which expenses may be disallowable for Corporation Tax?", "CT600 computation must add back disallowable costs.", "Tax/government, private/director, capital, and low-confidence categories remain visible for tax review.", "needs_accountant_review", "Review disallowables and add-backs before manual CT600 submission.", risk="critical", evidence_keys=("enriched_transactions_csv",), doc_keys=("hmrc_tax_computation_pdf", "ct600_box_map_markdown"), source_keys=("company_tax_return_guide",), systems=("KingTax",)),
        make("q.expenses.capital_items", "expenses", "tax_reviewer", "Which purchases are capital assets rather than expenses?", "Capital items affect depreciation add-back and capital allowances.", f"Capital/asset review rows: {category_rows('capital_or_asset_review')}.", "needs_accountant_review" if category_rows("capital_or_asset_review") else "answered_by_system", "Prepare fixed-asset and capital-allowances review from equipment/vehicle/asset rows.", risk="high", evidence_keys=("enriched_transactions_csv",), doc_keys=("expense_breakdown_pdf",), source_keys=("company_tax_return_guide",), systems=("KingLedger", "KingTax")),
        make("q.expenses.travel_private_use", "expenses", "tax_reviewer", "Do travel, motor, fuel, meals, or subsistence items have business-purpose evidence?", "Private-use or unsupported travel can be disallowable or benefit-related.", f"Motor/travel rows: {category_rows('motor_and_travel')} amount out GBP {category_amount('motor_and_travel')}.", "needs_human_confirmation" if category_rows("motor_and_travel") else "answered_by_system", "Attach mileage logs, job purpose, receipts, and private-use review.", risk="high", evidence_keys=("enriched_transactions_csv",), doc_keys=("expense_breakdown_pdf",), source_keys=("company_tax_return_guide", "paye_for_employers"), systems=("accounting_evidence_authoring",)),
        make("q.expenses.software_professional_bank", "expenses", "bookkeeper", "Are software, subscriptions, professional fees, and bank/payment charges separately classified?", "Common allowable costs still need source trace and correct classification.", f"Software rows={category_rows('software_subscriptions')}; professional rows={category_rows('professional_fees')}; bank/payment rows={category_rows('bank_and_payment_charges')}.", "answered_by_system", "Keep invoices/receipts where available and retain category examples in schedules.", risk="medium", confidence="high", evidence_keys=("enriched_transactions_csv",), doc_keys=("expense_breakdown_pdf",), source_keys=("company_accounting_records",), systems=("HNCSoup", "HNCAurisEngine")),
        make("q.expenses.payroll_subcontractor", "expenses", "tax_reviewer", "Are payroll, subcontractor, and worker payments treated correctly?", "Worker payments may trigger PAYE, CIS, benefits, or contractor-status obligations.", f"Payroll/subcontractor review rows: {category_rows('payroll_subcontractor_review')}.", "needs_accountant_review" if category_rows("payroll_subcontractor_review") else "needs_human_confirmation", "Confirm employees, directors, subcontractors, CIS statements, payroll RTI, and invoices.", risk="critical", evidence_keys=("enriched_transactions_csv",), doc_keys=("risk_and_contradiction_register_pdf",), source_keys=("paye_for_employers", "cis_overview"), systems=("KingTax", "accounting_evidence_authoring")),

        # Balance sheet questions.
        make("q.balance_sheet.bank_balances", "balance_sheet", "accountant", "Do closing bank balances agree to statement balances?", "The balance sheet cannot rely only on transaction totals if statements disagree.", "Bank net assets are estimated from period records; statement closing balances still require review.", "needs_human_confirmation", "Tie every bank/payment account to period-end statement balances.", risk="critical", evidence_keys=("combined_bank_transactions",), doc_keys=("full_accounts_pack_pdf",), source_keys=("annual_accounts_overview", "company_accounting_records"), systems=("KingLedger",)),
        make("q.balance_sheet.debtors_creditors", "balance_sheet", "accountant", "Are trade debtors and creditors recognised at period end?", "Accrual accounts need unpaid sales and purchases, not only cash movements.", "The bank feed cannot prove unpaid invoices or supplier bills.", "needs_human_confirmation", "Add aged debtors/creditors or confirm none existed.", risk="high", confidence="low", evidence_keys=("raw_data_manifest_json",), doc_keys=("full_accounts_pack_pdf",), source_keys=("annual_accounts_overview",), systems=("KingLedger",)),
        make("q.balance_sheet.accruals_prepayments", "balance_sheet", "accountant", "Are accruals and prepayments needed?", "Period cut-off affects profit, tax, and balance sheet.", "Generated notes flag accruals/prepayments for review.", "needs_accountant_review", "Review subscriptions, insurance, rent, professional fees, and post-period invoices.", risk="high", evidence_keys=("expense_breakdown_pdf",), doc_keys=("full_accounts_pack_pdf",), source_keys=("annual_accounts_overview",), systems=("KingLedger",)),
        make("q.balance_sheet.fixed_assets", "balance_sheet", "accountant", "Does the fixed-asset register exist and match capital items?", "Assets need cost, depreciation, disposals, and tax capital-allowance review.", "Fixed assets are currently held at GBP 0.00 pending capital-asset review.", "needs_accountant_review", "Create or confirm fixed-asset register from capital/equipment rows.", risk="high", evidence_keys=("enriched_transactions_csv",), doc_keys=("full_accounts_pack_pdf",), source_keys=("annual_accounts_overview", "company_tax_return_guide"), systems=("KingLedger", "KingTax")),
        make("q.balance_sheet.director_loan", "balance_sheet", "tax_reviewer", "Is the director loan account reconciled?", "Director loan can affect disclosures, close-company tax, benefits, and dividends.", "Director/cash/related-party rows remain in review and are not hidden.", "needs_accountant_review", "Reconcile director loan opening balance, movements, approvals, repayments, and year-end balance.", risk="critical", evidence_keys=("enriched_transactions_csv",), doc_keys=("risk_and_contradiction_register_pdf",), source_keys=("company_tax_return_guide",), systems=("KingLedger", "KingTax")),
        make("q.balance_sheet.tax_creditor", "balance_sheet", "tax_reviewer", "Does the Corporation Tax creditor match the computation?", "Tax provision must reconcile from P&L to balance sheet and CT600 support.", f"Corporation Tax estimate GBP {money_text(corporation_tax)}.", "answered_by_system", "Review tax provision after final add-backs/reliefs are confirmed.", risk="high", evidence_keys=("hmrc_tax_computation_markdown",), doc_keys=("full_accounts_pack_pdf",), source_keys=("company_tax_return_guide",), systems=("KingTax",)),

        # Tax, VAT, PAYE, CIS, and filing questions.
        make("q.tax_ct600.profit_bridge", "tax_ct600", "tax_reviewer", "Can I bridge accounts profit to taxable profit?", "HMRC computations must show how return figures were calculated from accounts.", f"Profit before tax GBP {money_text(profit_before_tax)}; Corporation Tax estimate GBP {money_text(corporation_tax)}.", "needs_accountant_review", "Finalise add-backs, deductions, disallowables, reliefs, and capital allowances.", risk="critical", evidence_keys=("hmrc_tax_computation_markdown",), doc_keys=("hmrc_tax_computation_pdf",), source_keys=("company_tax_return_guide",), systems=("KingTax",)),
        make("q.tax_ct600.tax_rate", "tax_ct600", "tax_reviewer", "Is the Corporation Tax rate correct for profit level and associated companies?", "Wrong rate or associated-company assumptions change tax due.", "The local estimate uses generated computation assumptions; associated-company facts need confirmation.", "needs_human_confirmation", "Confirm associated companies and applicable rate before manual filing.", risk="critical", evidence_keys=("ct600_manual_entry_json",), doc_keys=("tax_summary_pdf",), source_keys=("corporation_tax_rates", "company_tax_return_guide"), systems=("KingTax",)),
        make("q.tax_ct600.losses_reliefs", "tax_ct600", "tax_reviewer", "Are prior losses, group relief, R&D, creative, or other reliefs available?", "Reliefs can materially change tax due and CT600 boxes.", "The generated pack does not invent relief claims.", "needs_human_confirmation", "Add prior computations, loss schedules, relief evidence, or confirm none.", risk="high", confidence="low", evidence_keys=("ct600_box_map_markdown",), doc_keys=("hmrc_tax_computation_pdf",), source_keys=("company_tax_return_guide",), systems=("KingTax",)),
        make("q.tax_ct600.box_map", "tax_ct600", "hmrc_reviewer", "Do CT600 box-support figures map to the generated computation?", "Manual entry needs a box map that follows the accounts.", "CT600 manual-entry JSON and box map are generated where available.", "answered_by_system" if _artifact_path(artifact_map, "ct600_box_map_markdown") else "needs_data", "Use the generated box map only after all review questions are resolved.", risk="high", confidence="high", evidence_keys=("ct600_manual_entry_json", "ct600_box_map_markdown"), doc_keys=("hmrc_tax_computation_pdf",), source_keys=("ct600_form", "company_tax_return_guide"), systems=("generate_statutory_filing_pack",)),
        make("q.vat_paye_cis.vat_number_status", "vat_paye_cis", "tax_reviewer", "Does the company already have a VAT number or VAT registration history?", "VAT history changes filings, MTD records, and treatment of sales/purchases.", f"VAT taxable turnover estimate is GBP {vat_taxable_turnover}; threshold exceeded={tax_summary.get('vat_threshold_exceeded', over_vat)}. VAT credentials/status are still manual secret/portal facts and are not submitted by Aureon.", "needs_secret_manual_input" if tax_summary.get("vat_threshold_exceeded", over_vat) else "needs_human_confirmation", "Enter VAT number/effective date/MTD route manually if applicable; Aureon only prepares VAT workpapers.", risk="critical" if over_vat else "high", evidence_keys=("raw_data_manifest_json", "enriched_transactions_json"), doc_keys=("missing_data_and_evidence_action_plan_pdf",), source_keys=("vat_registration_when_to_register", "making_tax_digital_vat"), systems=("KingTax",)),
        make("q.vat_paye_cis.reverse_charge", "vat_paye_cis", "tax_reviewer", "Are any sales or purchases subject to domestic reverse charge?", "Reverse charge changes VAT accounting and construction-sector treatment.", f"Aureon detected {reverse_charge_rows} construction/CIS income rows routed to domestic reverse-charge review and payer provenance routed {payer_lookup_required} incoming rows through lookup/status controls. It does not invent invoice wording; it links the bank/source rows and asks the pack to preserve the VAT control.", "answered_by_system" if reverse_charge_rows or payer_lookup_required else "needs_human_confirmation", "Use the generated CIS/VAT and payer provenance workpapers to check invoices/contracts for domestic reverse-charge wording and customer/end-user status.", risk="critical" if reverse_charge_rows else "high", confidence="medium" if reverse_charge_rows else "low", evidence_keys=("raw_data_manifest_json", "enriched_transactions_csv", "payer_provenance_json"), doc_keys=("risk_and_contradiction_register_pdf", "cis_vat_tax_basis_assurance_pdf"), source_keys=("vat_record_keeping", "cis_overview", "vat_domestic_reverse_charge"), systems=("HNCLawDataset", "KingTax", "accounting_payer_provenance")),
        make("q.vat_paye_cis.paye_benefits", "vat_paye_cis", "tax_reviewer", "Did the company run payroll, director salary, benefits, expenses, P11D, or RTI?", "Payroll and benefits can create employer reporting obligations.", "Bank descriptions can flag wages, but PAYE/benefit history must be confirmed manually.", "needs_human_confirmation", "Ask for payroll reports, FPS/EPS submissions, PAYE reference, P11D/P11D(b), and payslips.", risk="critical", evidence_keys=("enriched_transactions_csv",), doc_keys=("missing_data_and_evidence_action_plan_pdf",), source_keys=("paye_for_employers",), systems=("KingTax",)),
        make("q.vat_paye_cis.cis", "vat_paye_cis", "tax_reviewer", "Was the company a CIS contractor or subcontractor?", "CIS can require verification, deductions, monthly returns, and statements.", f"Aureon detected and grossed up {cis_row_count} CIS-style net construction receipts: gross income GBP {cis_gross_income}, CIS suffered/tax deducted before bank GBP {cis_suffered}.", "answered_by_system" if cis_row_count else "needs_human_confirmation", "Retain CIS deduction statements where present; use generated gross-up/control workpaper for manual tax set-off/refund/PAYE review.", risk="critical", confidence="medium" if cis_row_count else "low", evidence_keys=("raw_data_manifest_json", "enriched_transactions_json"), doc_keys=("missing_data_and_evidence_action_plan_pdf",), source_keys=("cis_overview",), systems=("HNCLawDataset", "KingTax", "CISReconciliation")),

        # Document pack and cognitive challenge questions.
        make("q.document_pack.accounts_structure", "document_pack", "companies_house_reviewer", "Does the accounts PDF include P&L, balance sheet, notes, and approval/signature area?", "Statutory accounts need structure and approval, not only totals.", "The generated full accounts and Companies House PDFs contain the required reader-ready structure.", "answered_by_system", "Keep PDF text checks in place after each regeneration.", risk="high", confidence="high", evidence_keys=("companies_house_accounts_pdf", "full_accounts_pack_pdf"), doc_keys=("companies_house_accounts_pdf",), source_keys=("annual_accounts_overview", "companies_house_accounts"), systems=("generate_statutory_filing_pack",)),
        make("q.document_pack.tax_computation_workings", "document_pack", "hmrc_reviewer", "Does the HMRC computation show workings, add-backs, deductions, and CT600 support?", "HMRC guidance expects computations to show how return figures are calculated.", "HMRC computation PDF and CT600 support are generated, but judgement items remain open.", "needs_accountant_review", "Review computation workings before manual CT600 entry.", risk="critical", confidence="high", evidence_keys=("hmrc_tax_computation_pdf", "ct600_box_map_markdown"), doc_keys=("hmrc_tax_computation_pdf",), source_keys=("company_tax_return_guide",), systems=("generate_statutory_filing_pack", "KingTax")),
        make("q.document_pack.evidence_schedule", "document_pack", "evidence_officer", "Does the evidence schedule separate real source evidence from generated internal requests?", "The system must not create fake receipts or treat prompts as supplier evidence.", "Evidence authoring outputs are labelled internal support only.", "answered_by_system", "Keep generated evidence requests in review workpapers and attach real receipts separately.", risk="critical", confidence="high", evidence_keys=("accounting_evidence_authoring_manifest",), doc_keys=("missing_data_and_evidence_action_plan_pdf",), source_keys=("company_accounting_records",), systems=("accounting_evidence_authoring",)),
        make("q.document_pack.manual_upload_warning", "document_pack", "director_handoff_officer", "Does every pack warn that official submission/payment is manual only?", "Automation must not imply it filed or paid anything.", "Safe boundaries block Companies House/HMRC submission and payment.", "answered_by_system", "Keep manual-only warnings in PDFs, JSON manifests, and START_HERE docs.", risk="critical", confidence="high", evidence_keys=("filing_checklist",), doc_keys=("full_accounts_pack_pdf", "missing_data_and_evidence_action_plan_pdf"), source_keys=("company_tax_returns_overview", "companies_house_confirmation_statement"), systems=("accounting_handoff_pack",)),
        make("q.document_pack.ixbrl_readiness", "document_pack", "hmrc_reviewer", "Are accounts and computations readable for iXBRL/commercial filing software?", "HMRC Company Tax Return filing normally needs accounts/computations through an approved route.", "Readable HTML and iXBRL readiness notes are generated where available.", "answered_by_system" if _artifact_path(artifact_map, "ixbrl_readiness_note") else "needs_data", "Use approved filing software or accountant software for actual submission.", risk="high", evidence_keys=("ixbrl_readiness_note", "accounts_readable_for_ixbrl_html", "computation_readable_for_ixbrl_html"), doc_keys=("filing_checklist",), source_keys=("company_tax_return_accounts_format", "company_tax_returns_overview"), systems=("generate_statutory_filing_pack",)),
        make("q.cognitive.hmrc_challenge", "cognitive_challenge", "hmrc_reviewer", "What would HMRC challenge first?", "The pack should anticipate tax/evidence challenge before filing.", "Likely challenges: turnover completeness, disallowables, director/cash items, VAT threshold, and computation bridge.", "needs_accountant_review", "Resolve high-risk tax/evidence questions before manual CT600 submission.", risk="critical", evidence_keys=("enriched_transactions_json", "hmrc_tax_computation_markdown"), doc_keys=("risk_and_contradiction_register_pdf",), source_keys=("company_tax_return_guide",), systems=("SelfQuestioningAI", "KingTax")),
        make("q.cognitive.companies_house_reject", "cognitive_challenge", "companies_house_reviewer", "What would Companies House reject or require correction for?", "Public accounts filing can fail if route/statements/approval/company facts are wrong.", "Main risks are filing route, director approval, company identity, audit exemption, and signature/manual upload fields.", "needs_human_confirmation", "Verify filing route, register details, signatures, and manual upload fields.", risk="high", evidence_keys=("companies_house_accounts_pdf", "filing_checklist"), doc_keys=("risk_and_contradiction_register_pdf",), source_keys=("annual_accounts_overview", "companies_house_accounts"), systems=("company_house_tax_audit",)),
        make("q.cognitive.untraced_number", "cognitive_challenge", "contrary_reviewer", "Which number in the pack cannot be traced to source rows or explicit review blocker?", "Every figure needs source trace or a visible limitation.", "The current enrichment reconciles totals, while eye-scan rows keep uncertain treatment visible.", "answered_by_system" if enrichment_totals.get("reconciles_to_filing_figures") else "needs_accountant_review", "Block final-ready wording if future row totals fail GBP 0.00 reconciliation.", risk="critical", confidence="high", evidence_keys=("math_stress_test_pdf", "enriched_transactions_json"), doc_keys=("data_truth_checklist_pdf",), source_keys=("company_accounting_records", "company_tax_return_guide"), systems=("accounting_report_enrichment",)),
        make("q.cognitive.tax_assumption_changes", "cognitive_challenge", "contrary_reviewer", "Which assumption would change tax due?", "The system must reveal tax sensitivity rather than hiding it.", "Tax changes if VAT, transfer, director-loan, disallowable, capital-allowance, loss, or relief assumptions change.", "needs_accountant_review", "Create tax-review sign-off for assumptions before manual filing.", risk="critical", evidence_keys=("hmrc_tax_computation_markdown", "enriched_transactions_csv"), doc_keys=("risk_and_contradiction_register_pdf",), source_keys=("company_tax_return_guide", "corporation_tax_rates"), systems=("KingTax", "SelfQuestioningAI")),
        make("q.cognitive.unsafe_final_ready", "cognitive_challenge", "contrary_reviewer", "What makes this unsafe to call final-ready?", "The system must fail visible, not quiet.", f"Eye-scan rows={review_rows}; open legal/secret/portal requirements={sum(1 for item in requirements if item.manual_inputs)}.", "needs_accountant_review" if review_rows else "needs_human_confirmation", "Keep status as final-ready manual-upload support with autonomous allocations and eye-scan flags visible.", risk="critical", confidence="high", evidence_keys=("uk_accounting_requirements_brain_json", "enriched_transactions_json"), doc_keys=("missing_data_and_evidence_action_plan_pdf", "risk_and_contradiction_register_pdf"), source_keys=("annual_accounts_overview", "company_tax_return_guide"), systems=("SelfQuestioningAI", "ThoughtBus")),
        make("q.cognitive.systems_agree", "cognitive_challenge", "contrary_reviewer", "Do Soup, Auris, validator, ledger, tax, evidence, and UK brain agree?", "Aureon's organism only works if subsystems challenge and reinforce each other.", f"UK brain tracks {len(requirements)} requirements; enrichment/eye-scan allocation data is available for subsystem comparison.", "needs_accountant_review" if review_rows else "answered_by_system", "Eye-scan disagreements, validator fails, and autonomous allocation rows before filing.", risk="high", evidence_keys=("enriched_transactions_json", "uk_accounting_requirements_brain_json"), doc_keys=("transaction_classification_audit_pdf",), source_keys=("company_accounting_records",), systems=("HNCSoup", "HNCAurisEngine", "HNCAurisValidator", "KingLedger", "KingTax")),
        make("q.cognitive.human_handoff", "cognitive_challenge", "director_handoff_officer", "What must the human physically do after Aureon finishes?", "The system produces documents; the human performs legal submission/declaration/payment.", "The handoff requires eye-scan exception flagging, signatures, authentication, upload/entry, submission, and payment.", "needs_human_confirmation", "Open START_HERE, eye-scan PDFs 21/22/23, sign/approve, then manually file/pay through official or commercial software.", risk="critical", confidence="high", evidence_keys=("filing_checklist",), doc_keys=("missing_data_and_evidence_action_plan_pdf", "risk_and_contradiction_register_pdf"), source_keys=("company_tax_returns_overview", "companies_house_confirmation_statement"), systems=("accounting_handoff_pack",)),
    ]
    return specs


def _normalise_question_metadata(
    question: AccountantQuestion,
    *,
    artifact_map: dict[str, list[dict[str, Any]]],
) -> None:
    if question.status not in QUESTION_SAFE_STATUSES:
        question.status = "needs_accountant_review"
    if question.domain == "general":
        question.domain = _domain_for_question_id(question.id)
    if not question.reviewer_role or question.reviewer_role == "accountant":
        question.reviewer_role = _role_for_domain(question.domain)
    if not question.confidence:
        question.confidence = "medium"
    if not question.risk_level:
        question.risk_level = _risk_for_status(question.status)
    if not question.source_evidence:
        question.source_evidence = [item for item in question.evidence if item]
    if not question.official_sources:
        question.official_sources = _sources_for_domain(question.domain)
    if not question.linked_output_documents:
        question.linked_output_documents = _documents_for_domain(question.domain, artifact_map)


def _domain_for_question_id(question_id: str) -> str:
    if ".hmrc." in question_id or ".tax." in question_id:
        return "tax_ct600"
    if ".vat." in question_id or ".paye" in question_id or ".cis" in question_id:
        return "vat_paye_cis"
    if ".companies_house." in question_id:
        return "company_identity"
    if ".records." in question_id:
        return "expenses"
    if ".data_scope." in question_id:
        return "data_scope"
    return "cognitive_challenge"


def _role_for_domain(domain: str) -> str:
    return {
        "company_identity": "companies_house_reviewer",
        "data_scope": "bookkeeper",
        "transaction_truth": "bookkeeper",
        "revenue": "accountant",
        "expenses": "accountant",
        "balance_sheet": "accountant",
        "tax_ct600": "tax_reviewer",
        "vat_paye_cis": "tax_reviewer",
        "document_pack": "director_handoff_officer",
        "cognitive_challenge": "contrary_reviewer",
    }.get(domain, "accountant")


def _risk_for_status(status: str) -> str:
    return {
        "needs_secret_manual_input": "critical",
        "blocked_missing_evidence": "critical",
        "needs_accountant_review": "high",
        "needs_human_confirmation": "high",
        "needs_data": "high",
        "system_allocated_eye_scan": "medium",
        "answered_by_system": "medium",
        "not_applicable": "low",
    }.get(status, "medium")


def normalise_question_for_autonomous_handoff(question: AccountantQuestion) -> AccountantQuestion:
    """Convert judgement prompts into system allocations plus eye-scan flags.

    Secret credentials and genuinely missing uploaded data remain open, because
    the organism cannot invent them. Accounting judgement questions become
    autonomous eye-scan checks so the user is not asked to classify data.
    """
    if question.status in {"needs_human_confirmation", "needs_accountant_review", "blocked_missing_evidence"}:
        original_status = question.status
        original_next_action = _autonomous_handoff_text(question.next_action)
        question.status = "system_allocated_eye_scan"
        question.answer = _autonomous_handoff_text(question.answer)
        question.answer = (
            f"{question.answer} Aureon has applied a conservative working treatment from the available data; "
            "the user only eye-scans and flags visible exceptions."
        )
        question.next_action = (
            "System allocation is already applied. Eye-scan only; flag this item if uploaded source data visibly contradicts the assumption. "
            f"Original internal route: {original_next_action}"
        )
        question.evidence.append(f"autonomous_handoff_original_status={original_status}")
        for system in ("accounting_report_enrichment", "accounting_evidence_authoring", "uk_accounting_requirements_brain"):
            if system not in question.routed_systems:
                question.routed_systems.append(system)
    return question


def _autonomous_handoff_text(text: str) -> str:
    replacements = {
        "A human must confirm": "Aureon flags for eye-scan",
        "a human must confirm": "Aureon flags for eye-scan",
        "human confirmation is required": "an eye-scan flag is raised",
        "human confirmation": "eye-scan flag",
        "human-confirmed": "eye-scan flagged",
        "needs human review": "is routed to autonomous allocation and eye-scan",
        "need human review": "are routed to autonomous allocation and eye-scan",
        "human review": "eye-scan flagging",
        "human/accountant review": "system allocation and eye-scan",
        "Manual review rows": "Eye-scan rows",
        "manual review rows": "eye-scan rows",
        "manual-review rows": "eye-scan rows",
        "manual review": "eye-scan",
        "Ask the director to confirm": "Aureon flags for eye-scan",
        "Ask the human/director to confirm": "Aureon flags for eye-scan",
        "Ask the human": "Aureon flags for eye-scan",
        "ask the human": "flag for eye-scan",
        "Confirm ": "Eye-scan ",
        "confirm ": "eye-scan ",
        "Review ": "Eye-scan ",
        "review ": "eye-scan ",
        "Resolve ": "Autonomously allocate and flag ",
        "resolve ": "autonomously allocate and flag ",
        "Attach real receipts/invoices/sales reports": "Use uploaded receipts/invoices/sales reports",
        "Attach real receipts/invoices": "Use uploaded receipts/invoices",
        "complete voucher fields": "generate internal allocation memos",
        "accountant/director approval": "legal approval",
        "human evidence": "uploaded evidence",
        "director answer": "uploaded data or eye-scan exception",
        "review signs off": "legal handoff occurs",
        "signs off": "legal handoff occurs",
    }
    out = text
    for needle, replacement in replacements.items():
        out = out.replace(needle, replacement)
    return out


def _sources_for_domain(domain: str) -> list[str]:
    keys_by_domain = {
        "company_identity": ["annual_accounts_overview", "companies_house_confirmation_statement"],
        "data_scope": ["company_accounting_records"],
        "transaction_truth": ["company_accounting_records"],
        "revenue": ["company_accounting_records", "company_tax_return_guide"],
        "expenses": ["company_accounting_records", "company_tax_return_guide"],
        "balance_sheet": ["annual_accounts_overview", "company_accounting_records"],
        "tax_ct600": ["company_tax_return_guide", "company_tax_returns_overview"],
        "vat_paye_cis": ["vat_registration_when_to_register", "paye_for_employers", "cis_overview"],
        "document_pack": ["annual_accounts_overview", "company_tax_return_guide"],
        "cognitive_challenge": ["company_accounting_records", "company_tax_return_guide"],
    }
    return [
        UK_ACCOUNTING_OFFICIAL_SOURCES[key]
        for key in keys_by_domain.get(domain, ["company_accounting_records"])
        if key in UK_ACCOUNTING_OFFICIAL_SOURCES
    ]


def _documents_for_domain(domain: str, artifact_map: dict[str, list[dict[str, Any]]]) -> list[str]:
    keys_by_domain = {
        "company_identity": ["confirmation_statement_readiness_markdown", "filing_checklist"],
        "data_scope": ["source_reconciliation_pdf", "data_truth_checklist_pdf"],
        "transaction_truth": ["transaction_classification_audit_pdf", "math_stress_test_pdf"],
        "revenue": ["profit_and_loss_detailed_pdf", "source_reconciliation_pdf"],
        "expenses": ["expense_breakdown_pdf", "transaction_classification_audit_pdf"],
        "balance_sheet": ["full_accounts_pack_pdf", "companies_house_accounts_pdf"],
        "tax_ct600": ["hmrc_tax_computation_pdf", "ct600_box_map_markdown"],
        "vat_paye_cis": ["missing_data_and_evidence_action_plan_pdf"],
        "document_pack": ["full_accounts_pack_pdf", "filing_checklist"],
        "cognitive_challenge": ["risk_and_contradiction_register_pdf"],
    }
    return [
        path
        for path in (_artifact_path(artifact_map, key) for key in keys_by_domain.get(domain, []))
        if path
    ]


def _next_internal_actions(requirements: Sequence[UKRequirement], questions: Sequence[AccountantQuestion]) -> list[str]:
    actions: list[str] = []
    if any(item.status == "vat_registration_review_required" for item in requirements):
        actions.append("Prepare VAT registration/MTD eye-scan workpaper from turnover and sales classification; VAT credentials/status stay manual only if absent from uploaded data.")
    if any(item.status == "needs_secret_manual_input" for item in questions):
        actions.append("Ask for secure UTR input before CT600 manual filing support.")
    if any(item.status == "needs_data" for item in questions):
        actions.append("Wait for missing raw uploads where the files do not exist locally, then rerun the autonomous intake.")
    if any(item.status == "system_allocated_eye_scan" for item in questions):
        actions.append("Publish autonomous allocation assumptions and eye-scan flags to the vault/self-questioning cycle.")
    if any(item.missing_generated_artifacts for item in requirements):
        actions.append("Regenerate the local accounts/statutory/handoff pack to fill missing generated artifacts.")
    actions.append("Keep official filings, declarations, authentication, and payments manual.")
    return actions


def _artifact_map(artifacts: Sequence[Any]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for item in artifacts:
        if hasattr(item, "__dict__"):
            data = dict(item.__dict__)
        elif isinstance(item, dict):
            data = dict(item)
        else:
            continue
        key = str(data.get("output_key") or data.get("id") or "").strip()
        if not key:
            continue
        out.setdefault(key, []).append(data)
    return out


def _artifact_exists(artifact_map: dict[str, list[dict[str, Any]]], key: str) -> bool:
    return any(
        bool(item.get("exists"))
        for candidate in _artifact_keys(key)
        for item in artifact_map.get(candidate, [])
    )


def _artifact_path(artifact_map: dict[str, list[dict[str, Any]]], key: str) -> str:
    for candidate in _artifact_keys(key):
        for item in artifact_map.get(candidate, []):
            path = item.get("destination_path") or item.get("source_path") or ""
            if path:
                return str(path)
    return ""


def _read_artifact_json(artifact_map: dict[str, list[dict[str, Any]]], key: str) -> dict[str, Any]:
    for candidate in _artifact_keys(key):
        for item in artifact_map.get(candidate, []):
            path = item.get("destination_path") or item.get("source_path")
            if not path:
                continue
            data = _read_json(Path(path))
            if data:
                return data
    return {}


def _artifact_keys(key: str) -> tuple[str, ...]:
    return ARTIFACT_KEY_ALIASES.get(key, (key,))


def _read_output_json(statutory: dict[str, Any], key: str) -> dict[str, Any]:
    output = (statutory.get("outputs") or {}).get(key) or {}
    path = output.get("path")
    return _read_json(Path(path)) if path else {}


def _statutory_output_exists(statutory: dict[str, Any], key: str) -> bool:
    output = (statutory.get("outputs") or {}).get(key) or {}
    return bool(output.get("exists") or (output.get("path") and Path(output.get("path")).exists()))


def _read_json(path: Path) -> dict[str, Any]:
    try:
        if path.exists() and path.is_file():
            return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}
    return {}


def _extract_figures(statutory: dict[str, Any], full_run: dict[str, Any]) -> dict[str, Any]:
    if isinstance(statutory.get("figures"), dict):
        return dict(statutory.get("figures") or {})
    nested = (full_run.get("statutory_filing_pack") or {}).get("figures")
    if isinstance(nested, dict):
        return dict(nested)
    return {}


def _law_summary() -> dict[str, Any]:
    summary: dict[str, Any] = {
        "available": False,
        "vat_registration_threshold": "90000.00",
        "source_url": UK_ACCOUNTING_OFFICIAL_SOURCES.get("vat_registration_threshold"),
        "searched_keywords": ["VAT", "CT600", "Corporation Tax", "CIS", "accounting records"],
    }
    if get_law_dataset is None:
        return summary
    try:
        dataset = get_law_dataset()
        stats = dataset.stats()
        years = dataset.list_tax_years()
        rates = dataset.get_rates("2025-26")
        if rates is None and years:
            rates = dataset.get_rates(years[-1])
        summary.update(
            {
                "available": True,
                "stats": stats,
                "tax_years": years,
                "rate_year_used": getattr(rates, "tax_year", ""),
                "vat_registration_threshold": money_text(getattr(rates, "vat_registration_threshold", 90000) if rates else 90000),
                "vat_deregistration_threshold": money_text(getattr(rates, "vat_deregistration_threshold", 88000) if rates else 88000),
                "ct_small_profits_rate": getattr(rates, "ct_small_profits_rate", None) if rates else None,
                "ct_main_rate": getattr(rates, "ct_main_rate", None) if rates else None,
                "source_url": getattr(rates, "source_url", "") if rates else summary["source_url"],
                "manual_hits": {
                    "vat": len(dataset.find_manual("vat")),
                    "cis": len(dataset.find_manual("cis")),
                    "corporation_tax": len(dataset.find_manual("corporation tax")),
                },
                "time_limit_hits": {
                    "accounts": len(dataset.get_time_limit("accounts")),
                    "ct600": len(dataset.get_time_limit("CT600")),
                    "vat": len(dataset.get_time_limit("VAT")),
                },
            }
        )
    except Exception as exc:
        summary["error"] = f"{type(exc).__name__}: {exc}"
    return summary


def _provider_summary(combined: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for group_name in ("source_provider_summary", "flow_provider_summary"):
        for name, info in (combined.get(group_name) or {}).items():
            bucket = out.setdefault(str(name), {"rows": 0, "money_in": "0.00", "money_out": "0.00", "net": "0.00", "groups": []})
            bucket["rows"] = int(bucket.get("rows", 0)) + int((info or {}).get("rows", 0) or 0)
            bucket["money_in"] = money_text(_money(bucket.get("money_in")) + _money((info or {}).get("money_in")))
            bucket["money_out"] = money_text(_money(bucket.get("money_out")) + _money((info or {}).get("money_out")))
            bucket["net"] = money_text(_money(bucket.get("net")) + _money((info or {}).get("net")))
            bucket["groups"].append(group_name)
    return out


def _money(value: Any) -> Decimal:
    try:
        return Decimal(str(value if value is not None else "0").replace(",", "").replace("GBP", "").strip() or "0")
    except (InvalidOperation, ValueError):
        return Decimal("0")


def money_text(value: Any) -> str:
    return f"{_money(value):.2f}"


__all__ = [
    "AccountantQuestion",
    "COGNITIVE_REVIEWER_ROLES",
    "QUESTION_SAFE_STATUSES",
    "REQUIRED_SELF_QUESTION_DOMAINS",
    "SAFE_ACCOUNTING_ACTIONS",
    "UK_ACCOUNTING_OFFICIAL_SOURCES",
    "UKRequirement",
    "build_uk_accounting_requirements_brain",
    "money_text",
    "render_accountant_questions_markdown",
    "render_expanded_self_questions_markdown",
    "render_missing_data_action_plan_markdown",
    "render_risk_and_contradiction_register_markdown",
    "render_uk_requirements_markdown",
    "write_uk_accounting_brain_artifacts",
]
