"""Generate safe internal accounting evidence requests and draft vouchers.

This tool reads the unified bank/account feed and creates accountant review
documents for transactions that need support: petty-cash withdrawals, missing
expense receipts, unclear income, bank fees, and related-party/director queries.

Generated documents are internal drafts only. They are not supplier receipts,
not customer invoices, not external evidence, and not proof that a transaction
was allowable for tax. Human evidence and review remain required.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
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


OFFICIAL_EVIDENCE_SOURCES = {
    "company_accounting_records": "https://www.gov.uk/running-a-limited-company/company-and-accounting-records",
    "company_tax_return_obligations": "https://www.gov.uk/guidance/company-tax-return-obligations",
}


SAFE_BOUNDARIES = {
    "creates_supplier_receipts": False,
    "creates_customer_invoices_as_filed_documents": False,
    "writes_external_evidence": False,
    "writes_raw_bank_data": False,
    "official_companies_house_filing": "manual_only",
    "official_hmrc_submission": "manual_only",
    "tax_or_penalty_payment": "manual_only",
}


LLM_PROMPT_VERSION = "accounting-document-drafts-v1"
LLM_SAFE_BOUNDARY_NOTE = (
    "This LLM text is an internal accounting workpaper draft only. It must not be "
    "treated as a supplier receipt, customer invoice, third-party statement, HMRC "
    "submission, Companies House filing, or proof that the transaction is tax deductible."
)


@dataclass
class EvidenceDraft:
    id: str
    transaction_date: str
    description: str
    amount: str
    balance: str
    source_provider: str
    source_account: str
    source_file: str
    evidence_kind: str
    document_type: str
    status: str
    risk: str
    suggested_ledger_treatment: str
    rationale: str
    required_human_fields: list[str] = field(default_factory=list)
    llm_status: str = "not_requested"
    llm_model: str = ""
    llm_prompt_version: str = ""
    llm_generated_sections: dict[str, Any] = field(default_factory=dict)
    llm_error: str = ""
    generated_document_path: str = ""
    safe_boundary: str = "internal_draft_not_external_evidence"


def build_accounting_evidence_authoring_pack(
    *,
    repo_root: str | Path = REPO_ROOT,
    company_name: str = DEFAULT_COMPANY_NAME,
    company_number: str = DEFAULT_COMPANY_NUMBER,
    period_start: str = DEFAULT_PERIOD_START,
    period_end: str = DEFAULT_PERIOD_END,
    combined_csv: str | Path | None = None,
    enriched_transactions_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    max_document_templates: int = 250,
    use_llm: bool | None = None,
    llm_limit: int = 5,
    llm_model: str | None = None,
    llm_bridge: Any | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    combined_path = Path(combined_csv) if combined_csv else default_combined_csv(root, period_start, period_end)
    out_dir = Path(output_dir) if output_dir else (
        root
        / "Kings_Accounting_Suite"
        / "output"
        / "evidence_authoring"
        / company_number
        / f"{period_start}_to_{period_end}"
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = read_combined_transactions(combined_path)
    enrichment_by_row, enrichment_source = load_enrichment_by_row(enriched_transactions_path)
    auto_resolved_rows: list[dict[str, Any]] = []
    drafts: list[EvidenceDraft] = []
    for index, row in enumerate(rows, start=1):
        enrichment = enrichment_by_row.get(index)
        draft = classify_transaction(index, row, enrichment=enrichment)
        if draft is None and enrichment and enrichment.get("review_status") == "ok":
            auto_resolved_rows.append(auto_resolved_summary(index, row, enrichment))
            continue
        if draft is not None:
            drafts.append(draft)
    drafts = [draft for draft in drafts if draft is not None]

    selected = select_document_templates(drafts, max_document_templates=max_document_templates)
    llm_document_authoring = enrich_selected_drafts_with_llm(
        selected,
        company_name=company_name,
        company_number=company_number,
        period_start=period_start,
        period_end=period_end,
        enabled=use_llm if use_llm is not None else env_flag("AUREON_ACCOUNTING_LLM_DOCS", default=True),
        limit=int_env("AUREON_ACCOUNTING_LLM_LIMIT", default=llm_limit),
        model=llm_model,
        llm_bridge=llm_bridge,
    )
    for draft in selected:
        path = write_draft_document(draft, out_dir)
        draft.generated_document_path = str(path)

    manifest_path = out_dir / "evidence_authoring_manifest.json"
    summary_path = out_dir / "evidence_authoring_summary.md"
    requests_csv = out_dir / "evidence_requests.csv"
    document_index = out_dir / "generated_document_index.md"
    generated_at = datetime.now(timezone.utc).isoformat()
    summary = summarise_drafts(drafts, selected)
    summary.update(summarise_classification_passthrough(rows, auto_resolved_rows, enrichment_source))
    summary["llm_document_authoring"] = {
        "enabled": llm_document_authoring.get("enabled", False),
        "status": llm_document_authoring.get("status", "unknown"),
        "model": llm_document_authoring.get("model", ""),
        "requested_count": llm_document_authoring.get("requested_count", 0),
        "completed_count": llm_document_authoring.get("completed_count", 0),
        "fallback_count": llm_document_authoring.get("fallback_count", 0),
        "error_count": llm_document_authoring.get("error_count", 0),
    }
    manifest = {
        "schema_version": "accounting-evidence-authoring-v1",
        "generated_at": generated_at,
        "company_name": company_name,
        "company_number": company_number,
        "period_start": period_start,
        "period_end": period_end,
        "status": "completed",
        "mode": "autonomous_allocation_memos_and_eye_scan_flags_only",
        "combined_csv": str(combined_path),
        "enriched_transactions_path": str(enrichment_source) if enrichment_source else "",
        "output_dir": str(out_dir),
        "summary": summary,
        "llm_document_authoring": llm_document_authoring,
        "drafts": [asdict(draft) for draft in drafts],
        "official_sources": dict(OFFICIAL_EVIDENCE_SOURCES),
        "safe_boundaries": dict(SAFE_BOUNDARIES),
        "human_next_step": (
            "Eye-scan the generated allocation memos and flag only visible issues. "
            "Aureon applies conservative suspense/clearing/non-deductible treatments where evidence is not present."
        ),
    }
    write_requests_csv(requests_csv, drafts)
    summary_path.write_text(render_evidence_authoring_summary(manifest), encoding="utf-8")
    document_index.write_text(render_document_index(manifest), encoding="utf-8")
    manifest["outputs"] = {
        "accounting_evidence_authoring_manifest": str(manifest_path),
        "accounting_evidence_authoring_summary": str(summary_path),
        "accounting_evidence_requests_csv": str(requests_csv),
        "accounting_evidence_document_index": str(document_index),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest


def default_combined_csv(root: Path, period_start: str, period_end: str) -> Path:
    return (
        root
        / "Kings_Accounting_Suite"
        / "output"
        / "gateway"
        / f"{period_start}_to_{period_end}"
        / f"combined_bank_transactions_{period_start}_to_{period_end}.csv"
    )


def read_combined_transactions(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return [dict(row) for row in csv.DictReader(fh)]


def load_enrichment_by_row(path: str | Path | None) -> tuple[dict[int, dict[str, Any]], Path | None]:
    if not path:
        return {}, None
    source = Path(path)
    if not source.exists():
        return {}, source
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except Exception:
        return {}, source
    transactions = data.get("transactions") if isinstance(data, dict) else None
    if not isinstance(transactions, list):
        return {}, source
    by_row: dict[int, dict[str, Any]] = {}
    for item in transactions:
        if not isinstance(item, dict):
            continue
        try:
            row_number = int(item.get("row_number") or 0)
        except (TypeError, ValueError):
            row_number = 0
        if row_number:
            by_row[row_number] = item
    return by_row, source


def auto_resolved_summary(index: int, row: dict[str, str], enrichment: dict[str, Any]) -> dict[str, Any]:
    return {
        "row_number": index,
        "date": row.get("Date") or row.get("date") or "",
        "amount": money_text(row.get("Amount") or row.get("amount")),
        "category": enrichment.get("accounting_category") or "",
        "label": enrichment.get("accounting_label") or "",
        "source": enrichment.get("category_source") or "",
        "evidence_status": enrichment.get("evidence_status") or "",
    }


def classify_transaction(
    index: int,
    row: dict[str, str],
    *,
    enrichment: dict[str, Any] | None = None,
) -> EvidenceDraft | None:
    description = str(row.get("Description") or row.get("description") or "").strip()
    amount = money(row.get("Amount") or row.get("amount"))
    if not description or amount == 0:
        return None
    date = str(row.get("Date") or row.get("date") or "").strip()
    balance = str(row.get("Balance") or row.get("balance") or "").strip()
    source_provider = str(row.get("Source Provider") or row.get("source_provider") or "").strip()
    source_account = str(row.get("Source Account") or row.get("source_account") or "").strip()
    source_file = str(row.get("Source File") or row.get("source_file") or "").strip()
    text = description.lower()
    draft_id = f"ev_{date.replace('-', '')}_{index:05d}"
    base = {
        "id": draft_id,
        "transaction_date": date,
        "description": description,
        "amount": money_text(amount),
        "balance": balance,
        "source_provider": source_provider,
        "source_account": source_account,
        "source_file": source_file,
    }

    if enrichment:
        if enrichment.get("review_status") == "ok":
            return None
        enriched = classify_enriched_review(base, amount, enrichment)
        if enriched is not None:
            return enriched

    if amount < 0 and any(term in text for term in ("atm", "notemachine", "cash machine", "cash withdrawal")):
        return EvidenceDraft(
            id=draft_id,
            transaction_date=date,
            description=description,
            amount=money_text(amount),
            balance=balance,
            source_provider=source_provider,
            source_account=source_account,
            source_file=source_file,
            evidence_kind="petty_cash_withdrawal",
            document_type="petty_cash_voucher_template",
            status="system_allocated_eye_scan",
            risk="high",
            suggested_ledger_treatment="Aureon posts to petty_cash_clearing or director_loan_suspense and treats as non-deductible until uploaded source evidence proves a business expense.",
            rationale="Cash withdrawals need a petty-cash book/allocation and real supporting receipts before expense treatment; Aureon creates the allocation memo and eye-scan flag.",
            required_human_fields=[
                "eye-scan cash custodian looks plausible",
                "flag if uploaded receipts/logs prove business purpose",
                "flag if unspent cash returned is visible in uploaded data",
            ],
        )
    if amount < 0 and any(term in text for term in ("fee", "charge", "monthly fee", "cash loads")):
        return EvidenceDraft(
            id=draft_id,
            transaction_date=date,
            description=description,
            amount=money_text(amount),
            balance=balance,
            source_provider=source_provider,
            source_account=source_account,
            source_file=source_file,
            evidence_kind="bank_fee",
            document_type="bank_fee_internal_memo",
            status="bank_statement_supports_charge",
            risk="low",
            suggested_ledger_treatment="Aureon posts as bank charges using the statement row as support.",
            rationale="The bank statement itself is usually the supporting evidence for bank fees.",
            required_human_fields=["eye-scan only: flag if fee is visibly not a business bank charge"],
        )
    if amount < 0 and looks_like_person_or_related_party(text):
        return EvidenceDraft(
            id=draft_id,
            transaction_date=date,
            description=description,
            amount=money_text(amount),
            balance=balance,
            source_provider=source_provider,
            source_account=source_account,
            source_file=source_file,
            evidence_kind="director_or_related_party_payment",
            document_type="related_party_query_memo",
            status="system_allocated_eye_scan",
            risk="high",
            suggested_ledger_treatment="Aureon holds in director_loan_suspense/private_use_suspense unless uploaded payroll, dividend, reimbursement, invoice, or supplier evidence proves a different treatment.",
            rationale="Payments to named people may be salary, reimbursement, loan, dividend, drawings, or supplier payment; Aureon creates the safest suspense allocation and eye-scan flag.",
            required_human_fields=[
                "eye-scan recipient identity looks plausible",
                "flag if uploaded payroll/dividend/invoice evidence supports a different treatment",
            ],
        )
    if amount < 0:
        return EvidenceDraft(
            id=draft_id,
            transaction_date=date,
            description=description,
            amount=money_text(amount),
            balance=balance,
            source_provider=source_provider,
            source_account=source_account,
            source_file=source_file,
            evidence_kind="expense_support_required",
            document_type="expense_receipt_request",
            status="system_allocated_eye_scan",
            risk="medium",
            suggested_ledger_treatment="Aureon holds as expense_suspense_non_deductible unless uploaded evidence supports a more precise category.",
            rationale="Outgoing payments need a receipt, invoice, contract, or other evidence before final expense classification; Aureon creates the conservative allocation and eye-scan flag.",
            required_human_fields=["eye-scan only: flag if uploaded evidence clearly supports a better category"],
        )
    if amount > 0 and any(term in text for term in ("sumup", "card payment", "sales", "settlement")):
        return EvidenceDraft(
            id=draft_id,
            transaction_date=date,
            description=description,
            amount=money_text(amount),
            balance=balance,
            source_provider=source_provider,
            source_account=source_account,
            source_file=source_file,
            evidence_kind="sales_reconciliation",
            document_type="sales_reconciliation_request",
            status="system_allocated_eye_scan",
            risk="medium",
            suggested_ledger_treatment="Aureon includes as sales income or payment-processor clearing based on source patterns unless uploaded evidence proves otherwise.",
            rationale="Incoming sales deposits need support from invoice, sales report, contract, or till/payment records; Aureon applies the conservative sales/clearing treatment and eye-scan flag.",
            required_human_fields=["eye-scan only: flag if uploaded sales/platform evidence contradicts the allocation"],
        )
    if amount > 0:
        return EvidenceDraft(
            id=draft_id,
            transaction_date=date,
            description=description,
            amount=money_text(amount),
            balance=balance,
            source_provider=source_provider,
            source_account=source_account,
            source_file=source_file,
            evidence_kind="income_source_query",
            document_type="income_invoice_or_source_request",
            status="system_allocated_eye_scan",
            risk="medium",
            suggested_ledger_treatment="Aureon includes as turnover/income_suspense by default unless uploaded source evidence proves loan, transfer, refund, director funds, or capital.",
            rationale="Incoming money must be classified as sales, loan, refund, transfer, capital, or other income with evidence; Aureon applies the working treatment and eye-scan flag.",
            required_human_fields=["eye-scan only: flag if this is visibly not trading income"],
        )
    return None


def classify_enriched_review(
    base: dict[str, str],
    amount: Decimal,
    enrichment: dict[str, Any],
) -> EvidenceDraft | None:
    category = str(enrichment.get("accounting_category") or "")
    evidence_status = str(enrichment.get("evidence_status") or "")
    review_reason = str(enrichment.get("review_reason") or "Classification routed to autonomous allocation and eye-scan flag.")
    tax_treatment = str(enrichment.get("tax_treatment") or "")
    source_note = (
        f"{review_reason} Category={category or 'unknown'}; "
        f"evidence_status={evidence_status or 'unknown'}; tax_treatment={tax_treatment or 'not recorded'}."
    )
    common = dict(base)
    if category == "director_related_or_cash_review":
        return EvidenceDraft(
            **common,
            evidence_kind="director_cash_or_personal_allocation",
            document_type="director_cash_or_personal_allocation_memo",
            status="system_allocated_eye_scan",
            risk="high",
            suggested_ledger_treatment="Aureon allocates to director_loan/petty_cash/private_use_suspense and treats as non-deductible unless real evidence already in the data proves business treatment.",
            rationale=source_note,
            required_human_fields=[
                "eye-scan recipient/cash custodian looks plausible",
                "flag only if this is clearly business with evidence",
                "flag only if real receipt/invoice/log exists but was not read",
            ],
        )
    if category == "inter_account_transfer_review":
        return EvidenceDraft(
            **common,
            evidence_kind="transfer_reconciliation_request",
            document_type="inter_account_transfer_reconciliation_memo",
            status="system_allocated_eye_scan",
            risk="medium",
            suggested_ledger_treatment="Aureon allocates to inter_account_transfer_clearing by default and keeps it out of ordinary expense/income logic unless source evidence proves otherwise.",
            rationale=source_note,
            required_human_fields=["eye-scan only: flag if this is not a transfer/clearing movement"],
        )
    if category == "tax_and_government_review":
        return EvidenceDraft(
            **common,
            evidence_kind="tax_government_treatment_review",
            document_type="tax_government_treatment_review_memo",
            status="system_allocated_eye_scan",
            risk="high",
            suggested_ledger_treatment="Aureon allocates to tax_government_control_account_or_disallowable by default and excludes it from generic admin costs.",
            rationale=source_note,
            required_human_fields=["eye-scan only: flag if authority/tax type is visibly wrong"],
        )
    if category == "payroll_subcontractor_review":
        return EvidenceDraft(
            **common,
            evidence_kind="payroll_subcontractor_status_review",
            document_type="payroll_subcontractor_status_review_memo",
            status="system_allocated_eye_scan",
            risk="high",
            suggested_ledger_treatment="Aureon allocates to payroll_subcontractor_or_supplier_suspense and keeps PAYE/CIS/status risk visible.",
            rationale=source_note,
            required_human_fields=["eye-scan only: flag if worker/supplier status is visibly wrong or evidence is missing from uploaded data"],
        )
    if category == "income_source_review" or amount > 0:
        return EvidenceDraft(
            **common,
            evidence_kind="income_source_query",
            document_type="income_invoice_or_source_request",
            status="system_allocated_eye_scan",
            risk="medium",
            suggested_ledger_treatment="Aureon includes as turnover by default unless source evidence proves loan, transfer, refund, director funds, or capital.",
            rationale=source_note,
            required_human_fields=["eye-scan only: flag if this is visibly not trading income"],
        )
    if category == "uncategorised_review":
        return EvidenceDraft(
            **common,
            evidence_kind="uncategorised_transaction_review",
            document_type="uncategorised_transaction_review_memo",
            status="system_allocated_eye_scan",
            risk="medium",
            suggested_ledger_treatment="Aureon allocates to uncategorised_expense_suspense_non_deductible so the accounts can proceed without user classification.",
            rationale=source_note,
            required_human_fields=["eye-scan only: flag if uploaded evidence clearly supports a better category"],
        )
    if "review" in category:
        return EvidenceDraft(
            **common,
            evidence_kind="specialist_accounting_review",
            document_type="specialist_accounting_review_memo",
            status="system_allocated_eye_scan",
            risk="medium",
            suggested_ledger_treatment="Aureon allocates to specialist suspense and exposes the assumption for eye-scan exception flagging.",
            rationale=source_note,
            required_human_fields=["eye-scan only: flag if this assumption is visibly wrong"],
        )
    return None


def looks_like_person_or_related_party(text: str) -> bool:
    terms = ("director", "salary", "wage", "dividend", "loan", "gary", "tina", "brown")
    return any(term in text for term in terms)


def select_document_templates(
    drafts: Sequence[EvidenceDraft],
    *,
    max_document_templates: int,
) -> list[EvidenceDraft]:
    priority = {"high": 0, "medium": 1, "low": 2}
    selected = sorted(drafts, key=lambda item: (priority.get(item.risk, 9), item.transaction_date, item.id))
    return selected[: max(0, int(max_document_templates))]


def env_flag(name: str, *, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off", "disabled"}


def int_env(name: str, *, default: int) -> int:
    value = os.environ.get(name)
    if value is None:
        return int(default)
    try:
        return int(value)
    except ValueError:
        return int(default)


def enrich_selected_drafts_with_llm(
    drafts: Sequence[EvidenceDraft],
    *,
    company_name: str,
    company_number: str,
    period_start: str,
    period_end: str,
    enabled: bool,
    limit: int,
    model: str | None,
    llm_bridge: Any | None = None,
) -> dict[str, Any]:
    target = list(drafts)[: max(0, int(limit))]
    report: dict[str, Any] = {
        "enabled": bool(enabled),
        "status": "disabled" if not enabled else "pending",
        "model": model or "",
        "prompt_version": LLM_PROMPT_VERSION,
        "requested_count": 0,
        "completed_count": 0,
        "fallback_count": 0,
        "error_count": 0,
        "skipped_count": max(0, len(drafts) - len(target)),
        "max_error_count": int(os.environ.get("AUREON_ACCOUNTING_LLM_MAX_ERRORS", "3") or "3"),
        "aborted_after_errors": False,
        "aborted_after_unusable_output": False,
        "errors": [],
        "safe_boundaries": {
            "internal_workpaper_drafts_only": True,
            "creates_supplier_receipts": False,
            "creates_customer_invoices_as_filed_documents": False,
            "official_companies_house_filing": "manual_only",
            "official_hmrc_submission": "manual_only",
        },
    }
    if not enabled:
        for draft in drafts:
            draft.llm_status = "disabled"
        return report
    if not target:
        report["status"] = "completed"
        return report

    try:
        bridge = llm_bridge if llm_bridge is not None else make_ollama_bridge()
    except Exception as exc:
        return mark_llm_unavailable(target, report, f"Could not initialise OllamaBridge: {exc}")

    if not bridge_health_check(bridge):
        return mark_llm_unavailable(target, report, "Ollama is not reachable")

    selected_model = resolve_llm_model(bridge, model)
    report["model"] = selected_model
    if not selected_model:
        return mark_llm_unavailable(target, report, "No local Ollama chat model is available")

    consecutive_errors = 0
    for offset, draft in enumerate(target):
        report["requested_count"] += 1
        draft.llm_status = "requested"
        draft.llm_model = selected_model
        draft.llm_prompt_version = LLM_PROMPT_VERSION
        payload = {
            "company": {"name": company_name, "number": company_number},
            "period": {"start": period_start, "end": period_end},
            "transaction": {
                "id": draft.id,
                "date": draft.transaction_date,
                "description": draft.description,
                "amount_gbp": draft.amount,
                "balance": draft.balance,
                "source_provider": draft.source_provider,
                "source_account": draft.source_account,
                "source_file": draft.source_file,
            },
            "evidence_kind": draft.evidence_kind,
            "document_type": draft.document_type,
            "risk": draft.risk,
            "suggested_ledger_treatment": draft.suggested_ledger_treatment,
            "required_human_fields": draft.required_human_fields,
        }
        try:
            response = bridge.generate(
                model=selected_model,
                prompt=llm_document_prompt(payload),
                options={"temperature": 0, "num_predict": 260},
            )
            if response.get("error"):
                raise RuntimeError(str(response.get("error")))
            text = response.get("response") or ""
            sections = coerce_llm_sections(text)
            if not sections:
                draft.llm_status = "fallback_empty"
                draft.llm_error = "LLM returned no usable document sections"
                report["fallback_count"] += 1
                consecutive_errors += 1
                if consecutive_errors >= int(report["max_error_count"]):
                    stop_llm_after_errors(target[offset + 1 :], report, draft.llm_error)
                    break
                continue
            draft.llm_status = "completed"
            draft.llm_generated_sections = sections
            report["completed_count"] += 1
            consecutive_errors = 0
        except Exception as exc:
            draft.llm_status = "error"
            draft.llm_error = str(exc)
            report["error_count"] += 1
            consecutive_errors += 1
            if len(report["errors"]) < 10:
                report["errors"].append({"draft_id": draft.id, "error": str(exc)})
            if consecutive_errors >= int(report["max_error_count"]):
                stop_llm_after_errors(target[offset + 1 :], report, str(exc))
                break

    for draft in list(drafts)[len(target):]:
        draft.llm_status = "not_requested_limit"

    if report["completed_count"]:
        report["status"] = "completed" if report["error_count"] == 0 and report["fallback_count"] == 0 else "partial"
    elif report["error_count"] or report["fallback_count"]:
        report["status"] = "fallback"
    else:
        report["status"] = "unknown"
    return report


def stop_llm_after_errors(
    remaining: Sequence[EvidenceDraft],
    report: dict[str, Any],
    reason: str,
) -> None:
    for draft in remaining:
        draft.llm_status = "not_requested_after_unusable_llm_output"
        draft.llm_error = reason
    report["aborted_after_unusable_output"] = True
    if int(report.get("error_count", 0)):
        report["aborted_after_errors"] = True
    report["skipped_count"] = int(report.get("skipped_count", 0)) + len(remaining)


def make_ollama_bridge() -> Any:
    from aureon.integrations.ollama.ollama_bridge import OllamaBridge

    timeout_s = float(os.environ.get("AUREON_ACCOUNTING_LLM_TIMEOUT_S", "45") or "45")
    return OllamaBridge(timeout_s=timeout_s)


def bridge_health_check(bridge: Any) -> bool:
    try:
        return bool(bridge.health_check(max_age_s=0))
    except TypeError:
        try:
            return bool(bridge.health_check())
        except Exception:
            return False
    except Exception:
        return False


def mark_llm_unavailable(
    drafts: Sequence[EvidenceDraft],
    report: dict[str, Any],
    reason: str,
) -> dict[str, Any]:
    for draft in drafts:
        draft.llm_status = "unavailable"
        draft.llm_error = reason
    report["status"] = "unavailable"
    report["error_count"] = max(int(report.get("error_count", 0)), 1)
    report["errors"].append({"draft_id": "", "error": reason})
    return report


def resolve_llm_model(bridge: Any, requested_model: str | None) -> str:
    preferred = requested_model or os.environ.get("AUREON_ACCOUNTING_LLM_MODEL") or getattr(bridge, "chat_model", "")
    available = available_llm_model_names(bridge)
    if preferred and (not available or preferred in available):
        return str(preferred)
    if available:
        return available[0]
    return str(preferred or "")


def available_llm_model_names(bridge: Any) -> list[str]:
    try:
        models = bridge.list_models()
    except Exception:
        return []
    names: list[str] = []
    for item in models or []:
        name = getattr(item, "name", "") or getattr(item, "model", "")
        if isinstance(item, dict):
            name = str(item.get("name") or item.get("model") or name)
        if name:
            names.append(str(name))
    return names


def llm_system_prompt() -> str:
    return (
        "You are Aureon's accounting document authoring subsystem. Create internal UK accounting "
        "workpaper text from the supplied bank transaction facts. Return strict JSON only with keys: "
        "plain_english_summary, document_body, questions_for_human, evidence_to_attach, ledger_options, "
        "safety_note. Never invent supplier receipts, VAT numbers, invoice numbers, customer contracts, "
        "cash spend details, HMRC submissions, Companies House filings, or third-party evidence. If a fact "
        "is missing, write a clear placeholder or question. The output is an internal draft support memo only."
    )


def llm_document_prompt(payload: dict[str, Any]) -> str:
    compact = {
        "document_type": payload.get("document_type"),
        "evidence_kind": payload.get("evidence_kind"),
        "required_human_fields": payload.get("required_human_fields"),
        "possible_ledger_treatment": payload.get("suggested_ledger_treatment"),
    }
    compact_payload = json.dumps(compact, ensure_ascii=True, sort_keys=True)
    return (
        "Return valid minified JSON only. No markdown. You draft an internal UK accounting workpaper. "
        "Do not invent facts. Do not mention real names, dates, amounts, bank descriptions, payers, payees, "
        "approval, VAT, receipt, invoice, filing, or tax status. Use placeholders like [BANK DESCRIPTION], "
        "[SIGNED AMOUNT], [TRANSACTION DATE], [SUPPLIER], [CUSTOMER], [APPROVAL STATUS]. "
        "Use UNKNOWN or REVIEW REQUIRED for missing facts. Schema: {\"plain_english_summary\":\"\","
        "\"document_body\":\"\",\"questions_for_human\":[\"\"],\"evidence_to_attach\":[\"\"],"
        "\"ledger_options\":[\"\"],\"safety_note\":\"\"}. Use at most 12 words per string. "
        f"Facts JSON: {compact_payload}"
    )


def coerce_llm_sections(text: str) -> dict[str, Any]:
    data = parse_jsonish_text(text)
    if not isinstance(data, dict):
        clean_text = str(text or "").strip()
        if not clean_text:
            return {}
        data = {"document_body": clean_text}
    nested_arrays = data.get("array_fields")
    if isinstance(nested_arrays, dict):
        for key in ("questions_for_human", "evidence_to_attach", "ledger_options"):
            if key not in data and key in nested_arrays:
                data[key] = nested_arrays.get(key)
    allowed = [
        "plain_english_summary",
        "document_body",
        "questions_for_human",
        "evidence_to_attach",
        "ledger_options",
        "safety_note",
    ]
    sections: dict[str, Any] = {}
    for key in allowed:
        value = data.get(key)
        if value in (None, "", [], {}):
            continue
        if isinstance(value, list):
            sections[key] = [str(item).strip() for item in value if str(item).strip()]
        elif isinstance(value, dict):
            sections[key] = {str(k): str(v) for k, v in value.items()}
        else:
            sections[key] = str(value).strip()
    if not sections:
        return {}
    sections = {
        key: value
        for key, value in sections.items()
        if not contains_unsafe_llm_assertion({key: value})
    }
    if not sections:
        return {}
    if set(sections) <= {"safety_note"}:
        return {}
    safety = str(sections.get("safety_note") or "").strip()
    if LLM_SAFE_BOUNDARY_NOTE not in safety:
        sections["safety_note"] = f"{safety}\n{LLM_SAFE_BOUNDARY_NOTE}".strip()
    return sections


def contains_unsafe_llm_assertion(sections: dict[str, Any]) -> bool:
    text = json.dumps(sections, ensure_ascii=True).lower()
    unsafe_patterns = [
        r"\b(receipt|invoice|contract|sales report|approval)\s+(is|was|has been)\s+(attached|provided|approved|available|confirmed)",
        r"\b(has|have|had)\s+provided\s+(the\s+)?(receipt|invoice|contract|sales report|approval|evidence)\b",
        r"\bapproved\b",
        r"\bwith\s+[a-z\s]{0,40}(receipt|invoice|contract|sales report|approval|evidence)\b",
        r"\bdirector[_\s-]*approval[\"'\s:,-]+yes\b",
        r"\b(vat|invoice|receipt)\s+number[\"'\s:,-]+[a-z0-9][a-z0-9/-]{2,}",
        r"\b\d{3,}(?:[,.]\d+)?\b",
        r"\bsigned\s+(a\s+)?(bill|receipt|invoice|approval)\b",
        r"\bhmrc\s+(submitted|filed|accepted|paid)\b",
        r"\bcompanies house\s+(submitted|filed|accepted)\b",
    ]
    return any(re.search(pattern, text) for pattern in unsafe_patterns)


def parse_jsonish_text(text: str) -> Any:
    raw = str(text or "").strip()
    if not raw:
        return None
    candidates = [raw]
    fenced = re.search(r"```(?:json)?\s*(.*?)```", raw, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        candidates.append(fenced.group(1).strip())
    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        candidates.append(raw[start : end + 1])
    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    return None


def write_draft_document(draft: EvidenceDraft, out_dir: Path) -> Path:
    folder = out_dir / "document_templates" / safe_slug(draft.evidence_kind)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{draft.id}_{safe_slug(draft.document_type)}.md"
    path.write_text(render_draft_document(draft), encoding="utf-8")
    return path


def render_draft_document(draft: EvidenceDraft) -> str:
    lines = [
        f"# {draft.document_type.replace('_', ' ').title()}",
        "",
        "Status: INTERNAL DRAFT - NOT EXTERNAL EVIDENCE",
        "",
        "## Transaction",
        "",
        f"- Date: {draft.transaction_date}",
        f"- Description: {draft.description}",
        f"- Amount: GBP {draft.amount}",
        f"- Balance: {draft.balance}",
        f"- Source provider: {draft.source_provider or 'unknown'}",
        f"- Source account: {draft.source_account or 'unknown'}",
        f"- Source file: {draft.source_file or 'unknown'}",
        "",
        "## Suggested Accounting Treatment",
        "",
        draft.suggested_ledger_treatment,
        "",
        "## Why Aureon Generated This",
        "",
        draft.rationale,
        "",
        "## Eye-Scan Flags",
        "",
    ]
    for item in draft.required_human_fields:
        lines.append(f"- [ ] {item}")
    if draft.llm_generated_sections:
        lines.extend(
            [
                "",
                "## LLM Drafted Internal Workpaper",
                "",
                f"- Model: {draft.llm_model or 'unknown'}",
                f"- Prompt version: {draft.llm_prompt_version or LLM_PROMPT_VERSION}",
                f"- Status: {draft.llm_status}",
                "",
            ]
        )
        for title, key in [
            ("Plain-English Summary", "plain_english_summary"),
            ("Draft Body", "document_body"),
            ("Eye-Scan Questions", "questions_for_human"),
            ("Evidence To Attach", "evidence_to_attach"),
            ("Ledger Options", "ledger_options"),
            ("LLM Safety Note", "safety_note"),
        ]:
            value = draft.llm_generated_sections.get(key)
            if value in (None, "", [], {}):
                continue
            lines.extend(["", f"### {title}", ""])
            append_rendered_value(lines, value)
    elif draft.llm_status not in {"not_requested", "disabled"}:
        lines.extend(
            [
                "",
                "## LLM Drafting Status",
                "",
                f"- Status: {draft.llm_status}",
                f"- Model: {draft.llm_model or 'unknown'}",
                f"- Error: {draft.llm_error or 'none'}",
                "- Deterministic document sections above remain available for eye-scan exception checking.",
            ]
        )
    lines.extend(
        [
            "",
            "## Safety Declaration",
            "",
            "- This document was generated from bank/account data by Aureon.",
            "- It is not a supplier receipt, customer invoice, signed declaration, or proof of tax deductibility.",
            "- Attach real receipts, invoices, contracts, sales reports, petty-cash logs, or approval evidence before filing.",
            "- Unsupported amounts are routed to suspense/director loan/private drawings unless uploaded evidence supports another treatment.",
            "",
        ]
    )
    return "\n".join(lines)


def append_rendered_value(lines: list[str], value: Any) -> None:
    if isinstance(value, list):
        for item in value:
            lines.append(f"- {item}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            lines.append(f"- {key}: {item}")
        return
    for part in str(value).splitlines():
        lines.append(part)


def summarise_drafts(drafts: Sequence[EvidenceDraft], selected: Sequence[EvidenceDraft]) -> dict[str, Any]:
    by_kind: dict[str, int] = {}
    by_status: dict[str, int] = {}
    by_risk: dict[str, int] = {}
    total_amount = Decimal("0")
    for draft in drafts:
        by_kind[draft.evidence_kind] = by_kind.get(draft.evidence_kind, 0) + 1
        by_status[draft.status] = by_status.get(draft.status, 0) + 1
        by_risk[draft.risk] = by_risk.get(draft.risk, 0) + 1
        total_amount += abs(money(draft.amount))
    return {
        "draft_count": len(drafts),
        "generated_document_count": len(selected),
        "by_kind": by_kind,
        "by_status": by_status,
        "by_risk": by_risk,
        "absolute_value_requiring_review": money_text(total_amount),
        "petty_cash_withdrawal_count": by_kind.get("petty_cash_withdrawal", 0),
        "related_party_query_count": by_kind.get("director_or_related_party_payment", 0),
        "expense_receipt_request_count": by_kind.get("expense_support_required", 0),
        "income_source_query_count": by_kind.get("income_source_query", 0),
        "manual_review_required": False,
        "eye_scan_required": bool(drafts),
        "human_data_entry_required_count": 0,
        "system_allocation_memo_count": len(drafts),
        "absolute_value_eye_scan_flagged": money_text(total_amount),
        "generated_documents_are_external_evidence": False,
    }


def summarise_classification_passthrough(
    rows: Sequence[dict[str, str]],
    auto_resolved_rows: Sequence[dict[str, Any]],
    enrichment_source: Path | None,
) -> dict[str, Any]:
    by_category: dict[str, int] = {}
    for row in auto_resolved_rows:
        category = str(row.get("category") or "unknown")
        by_category[category] = by_category.get(category, 0) + 1
    return {
        "source_row_count": len(rows),
        "classification_enrichment_path": str(enrichment_source) if enrichment_source else "",
        "classification_passthrough_enabled": bool(enrichment_source and auto_resolved_rows),
        "auto_resolved_row_count": len(auto_resolved_rows),
        "auto_resolved_by_category": dict(sorted(by_category.items())),
        "auto_resolved_basis": (
            "Rows marked ok by accounting_report_enrichment are not turned into eye-scan allocation memos; "
            "they remain traceable in enriched_transactions.json/csv and source manifests."
        ),
        "cook_systems_used": [
            "HNCSoup",
            "HNCSoupKitchen",
            "HNCAurisEngine",
            "HNCAurisValidator",
            "accounting_report_enrichment",
        ]
        if enrichment_source
        else [],
    }


def write_requests_csv(path: Path, drafts: Sequence[EvidenceDraft]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "id",
        "transaction_date",
        "description",
        "amount",
        "source_provider",
        "source_account",
        "evidence_kind",
        "document_type",
        "status",
        "risk",
        "suggested_ledger_treatment",
        "llm_status",
        "llm_model",
        "llm_error",
        "generated_document_path",
    ]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for draft in drafts:
            row = asdict(draft)
            writer.writerow({key: row.get(key, "") for key in fields})


def render_evidence_authoring_summary(manifest: dict[str, Any]) -> str:
    summary = manifest.get("summary") or {}
    llm_summary = manifest.get("llm_document_authoring") or summary.get("llm_document_authoring") or {}
    lines = [
        "# Accounting Evidence Authoring Summary",
        "",
        f"- Company: {manifest.get('company_number')} {manifest.get('company_name')}",
        f"- Period: {manifest.get('period_start')} to {manifest.get('period_end')}",
        f"- Status: {manifest.get('status')}",
        f"- Autonomous allocation memos / eye-scan flags: {summary.get('draft_count', 0)}",
        f"- Source rows scanned: {summary.get('source_row_count', 0)}",
        f"- Auto-resolved by cook/classification layer: {summary.get('auto_resolved_row_count', 0)}",
        f"- Generated internal document templates: {summary.get('generated_document_count', 0)}",
        f"- Absolute value eye-scan flagged: GBP {summary.get('absolute_value_eye_scan_flagged', summary.get('absolute_value_requiring_review', '0.00'))}",
        f"- Manual data-entry rows: {summary.get('human_data_entry_required_count', 0)}",
        f"- Petty cash withdrawals: {summary.get('petty_cash_withdrawal_count', 0)}",
        f"- Related-party/director queries: {summary.get('related_party_query_count', 0)}",
        f"- LLM document authoring: {llm_summary.get('status', 'unknown')} "
        f"({llm_summary.get('completed_count', 0)} drafted, model={llm_summary.get('model') or 'not selected'})",
        "",
        "## Evidence Types",
        "",
    ]
    for kind, count in sorted((summary.get("by_kind") or {}).items()):
        lines.append(f"- {kind}: {count}")
    if summary.get("auto_resolved_by_category"):
        lines.extend(["", "## Auto-Resolved Categories", ""])
        for category, count in sorted((summary.get("auto_resolved_by_category") or {}).items()):
            lines.append(f"- {category}: {count}")
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Generated documents are internal autonomous allocation support and eye-scan flags only.",
            "- They are not supplier receipts, customer invoices, official filings, or tax-payment instructions.",
            "- Raw bank/source files are not overwritten.",
            "- Aureon keeps unsupported items in conservative suspense/clearing/non-deductible treatments unless uploaded source evidence says otherwise.",
            "",
            "## Official Sources",
            "",
        ]
    )
    for name, url in (manifest.get("official_sources") or {}).items():
        lines.append(f"- {name}: {url}")
    lines.append("")
    return "\n".join(lines)


def render_document_index(manifest: dict[str, Any]) -> str:
    lines = [
        "# Generated Accounting Evidence Document Index",
        "",
        "These documents are internal autonomous allocation memos and eye-scan flags only.",
        "",
        "| ID | Date | Amount | Kind | Status | LLM | Document |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for draft in manifest.get("drafts") or []:
        path = draft.get("generated_document_path") or ""
        doc = f"`{path}`" if path else "not generated"
        lines.append(
            f"| `{draft.get('id')}` | {draft.get('transaction_date')} | GBP {draft.get('amount')} | "
            f"{draft.get('evidence_kind')} | {draft.get('status')} | {draft.get('llm_status', 'not_requested')} | {doc} |"
        )
    lines.append("")
    return "\n".join(lines)


def money(value: Any) -> Decimal:
    try:
        return Decimal(str(value if value is not None else "0").replace(",", "").replace("GBP", "").strip() or "0")
    except (InvalidOperation, ValueError):
        return Decimal("0")


def money_text(value: Any) -> str:
    return f"{money(value):.2f}"


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value).strip().lower())
    return slug.strip("_") or "unknown"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate safe internal accounting evidence requests.")
    parser.add_argument("--company-name", default=DEFAULT_COMPANY_NAME)
    parser.add_argument("--company-number", default=DEFAULT_COMPANY_NUMBER)
    parser.add_argument("--period-start", default=DEFAULT_PERIOD_START)
    parser.add_argument("--period-end", default=DEFAULT_PERIOD_END)
    parser.add_argument("--combined-csv", default="")
    parser.add_argument("--enriched-transactions", default="", help="Optional enriched_transactions.json from the statutory pack.")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--max-document-templates", type=int, default=250)
    parser.add_argument("--no-llm", action="store_true", help="Disable local Ollama/Aureon LLM document drafting.")
    parser.add_argument("--llm-limit", type=int, default=5, help="Maximum generated documents to enrich with LLM sections.")
    parser.add_argument("--llm-model", default="", help="Optional Ollama chat model for document drafting.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = build_accounting_evidence_authoring_pack(
        company_name=args.company_name,
        company_number=args.company_number,
        period_start=args.period_start,
        period_end=args.period_end,
        combined_csv=args.combined_csv or None,
        enriched_transactions_path=args.enriched_transactions or None,
        output_dir=args.output_dir or None,
        max_document_templates=args.max_document_templates,
        use_llm=not args.no_llm,
        llm_limit=args.llm_limit,
        llm_model=args.llm_model or None,
    )
    print((manifest.get("outputs") or {}).get("accounting_evidence_authoring_manifest", ""))
    print((manifest.get("outputs") or {}).get("accounting_evidence_authoring_summary", ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
