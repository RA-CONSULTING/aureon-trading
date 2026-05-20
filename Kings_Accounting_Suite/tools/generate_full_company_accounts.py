"""Generate the full final-ready local company accounts pack from repo-held data.

This is the one-command, non-filing accounting workflow for the company. It
uses the CSV and statement evidence already stored in the repo, rebuilds the
accounts pack, refreshes the Companies House/HMRC triage report, writes a
machine-readable run manifest, and creates the final-ready manual filing pack.

It does not submit accounts, submit a CT600, pay tax, or contact HMRC beyond
read-only public guidance/profile lookups performed by the audit step.

Usage from repo root:
  .venv\\Scripts\\python.exe Kings_Accounting_Suite\\tools\\generate_full_company_accounts.py
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Sequence


KAS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = KAS_DIR.parent
TOOLS_DIR = KAS_DIR / "tools"
sys.path.insert(0, str(KAS_DIR))
sys.path.insert(0, str(TOOLS_DIR))

from company_house_tax_audit import (  # noqa: E402
    DEFAULT_COMPANY_NUMBER,
    DEFAULT_PERIOD_END,
    DEFAULT_PERIOD_START,
    build_report,
    write_report,
)
from combined_bank_data import combine_bank_data_for_period  # noqa: E402
from accounting_system_registry import build_accounting_system_registry  # noqa: E402
from generate_statutory_filing_pack import build_pack as build_statutory_filing_pack  # noqa: E402
from company_raw_data_intake import (  # noqa: E402
    build_company_raw_data_manifest,
    resolve_raw_roots,
    write_raw_data_manifest_artifacts,
)


@dataclass
class SourceDataInventory:
    uploads_dir: str
    business_accounts_dir: str
    csv_files: list[dict[str, Any]]
    evidence_files: list[dict[str, Any]]
    combined_bank_data: dict[str, Any] = field(default_factory=dict)
    accounting_system_registry: dict[str, Any] = field(default_factory=dict)
    raw_data_manifest: dict[str, Any] = field(default_factory=dict)


def file_record(path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "path": str(path),
        "name": path.name,
        "bytes": stat.st_size,
        "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
    }


def inventory_source_data(
    *,
    company_number: str = DEFAULT_COMPANY_NUMBER,
    period_start: str = DEFAULT_PERIOD_START,
    period_end: str = DEFAULT_PERIOD_END,
    raw_data_roots: Sequence[str | Path] | None = None,
    include_default_roots: bool = True,
) -> SourceDataInventory:
    roots = resolve_raw_roots(
        REPO_ROOT,
        raw_data_roots,
        include_default_roots=include_default_roots,
    )
    uploads_dir = REPO_ROOT / "uploads"
    business_accounts_dir = REPO_ROOT / "bussiness accounts"
    csv_files: list[dict[str, Any]] = []
    evidence_files = []
    for root in roots:
        if not root.exists():
            continue
        csv_files.extend(file_record(path) for path in sorted(root.rglob("*.csv"), key=lambda p: str(p).lower()))
        evidence_files.extend(
            file_record(path)
            for path in sorted(root.rglob("*"), key=lambda p: str(p).lower())
            if path.is_file() and path.suffix.lower() in {".pdf", ".jpg", ".jpeg", ".png", ".csv", ".xlsx", ".xls"}
        )
    raw_manifest = build_company_raw_data_manifest(
        REPO_ROOT,
        company_number=company_number,
        period_start=period_start,
        period_end=period_end,
        raw_roots=raw_data_roots,
        include_default_roots=include_default_roots,
    )
    write_raw_data_manifest_artifacts(raw_manifest)
    combined = combine_bank_data_for_period(
        REPO_ROOT,
        period_start,
        period_end,
        raw_roots=raw_data_roots,
        include_default_roots=include_default_roots,
    )
    registry = build_accounting_system_registry(REPO_ROOT, period_start=period_start, period_end=period_end)
    return SourceDataInventory(
        uploads_dir=str(uploads_dir),
        business_accounts_dir=str(business_accounts_dir),
        csv_files=csv_files,
        evidence_files=evidence_files,
        combined_bank_data=combined.to_summary(),
        accounting_system_registry=registry.compact(max_entries=8, max_artifacts=8),
        raw_data_manifest=raw_manifest.to_dict(),
    )


def run_accounts_pack_builder(
    *,
    company_name: str,
    period_start: str,
    period_end: str,
    raw_data_roots: Sequence[str | Path] | None = None,
    include_default_roots: bool = True,
) -> int:
    # Import lazily so tests and manifest tools can load without pulling the
    # whole accounting pipeline into memory.
    from build_period_accounts_pack import build_period_accounts_pack

    build_period_accounts_pack(
        company_name=company_name,
        period_start=period_start,
        period_end=period_end,
        raw_data_roots=raw_data_roots,
        include_default_roots=include_default_roots,
    )
    return 0


def build_manifest(
    *,
    company_number: str,
    period_start: str,
    period_end: str,
    as_of: date,
    accounts_build_exit_code: int,
    audit_json: Path,
    audit_md: Path,
    source_inventory: SourceDataInventory,
    statutory_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    pack_dir = KAS_DIR / "output" / "gateway" / f"{period_start}_to_{period_end}"
    expected_outputs = {
        "accounts_pack_pdf": pack_dir / f"ra_consulting_and_brokerage_accounts_pack_{period_start}_to_{period_end}.pdf",
        "management_accounts": pack_dir / "management_accounts.xlsx",
        "general_ledger": pack_dir / "general_ledger.xlsx",
        "trial_balance": pack_dir / "trial_balance.xlsx",
        "profit_and_loss": pack_dir / "pnl.pdf",
        "tax_summary": pack_dir / "tax_summary.pdf",
        "period_manifest": pack_dir / "period_pack_manifest.json",
        "compliance_audit_json": audit_json,
        "compliance_audit_markdown": audit_md,
    }
    if statutory_manifest:
        statutory_outputs = statutory_manifest.get("outputs") or {}
        def statutory_path(key: str) -> Path | None:
            info = statutory_outputs.get(key) or {}
            path = Path(info.get("path", ""))
            return path if str(path) else None

        expected_outputs["accounts_pack_pdf"] = (
            statutory_path("full_accounts_pack_pdf") or expected_outputs["accounts_pack_pdf"]
        )
        expected_outputs["profit_and_loss"] = (
            statutory_path("profit_and_loss_detailed_pdf") or expected_outputs["profit_and_loss"]
        )
        expected_outputs["tax_summary"] = (
            statutory_path("corporation_tax_summary_pdf") or expected_outputs["tax_summary"]
        )
        for key, info in statutory_outputs.items():
            path = Path(info.get("path", ""))
            expected_outputs[f"statutory_{key}"] = path
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "company_number": company_number,
        "period_start": period_start,
        "period_end": period_end,
        "as_of": as_of.isoformat(),
        "mode": "final_ready_manual_filing_pack_no_submission",
        "source_data_inventory": asdict(source_inventory),
        "accounts_build": {
            "exit_code": accounts_build_exit_code,
            "status": "completed" if accounts_build_exit_code == 0 else "failed",
        },
        "outputs": {
            key: {
                "path": str(path),
                "exists": path.exists(),
                "bytes": path.stat().st_size if path.exists() else 0,
            }
            for key, path in expected_outputs.items()
        },
        "statutory_filing_pack": statutory_manifest or {},
        "safety": {
            "submits_to_companies_house": False,
            "submits_to_hmrc": False,
            "pays_tax_or_penalties": False,
            "requires_director_or_accountant_review": True,
            "manual_upload_submission_and_payment_only": True,
        },
        "next_human_step": (
            "Open the final-ready filing handoff pack, approve/sign where required, "
            "then manually upload or enter the generated Companies House/HMRC documents."
        ),
    }


def write_full_run_summary(manifest: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "full_company_accounts_run_manifest.json"
    summary_path = output_dir / "full_company_accounts_run_summary.md"

    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    outputs = manifest["outputs"]
    lines = [
        "# Full Company Accounts Run",
        "",
        f"- Generated: {manifest['generated_at']}",
        f"- Company number: {manifest['company_number']}",
        f"- Period: {manifest['period_start']} to {manifest['period_end']}",
        f"- Mode: {manifest['mode']}",
        f"- Accounts build: {manifest['accounts_build']['status']}",
        "",
        "## Source Data",
        "",
        f"- CSV files found: {len(manifest['source_data_inventory']['csv_files'])}",
        f"- Evidence files found: {len(manifest['source_data_inventory']['evidence_files'])}",
    ]
    raw_manifest = manifest["source_data_inventory"].get("raw_data_manifest") or {}
    raw_summary = raw_manifest.get("summary") or {}
    if raw_summary:
        lines.extend(
            [
                f"- Raw intake files inventoried: {raw_summary.get('file_count', 0)}",
                f"- Raw transaction sources routed: {raw_summary.get('transaction_source_count', 0)}",
                f"- Raw evidence-only files retained: {raw_summary.get('evidence_only_count', 0)}",
            ]
        )
    combined = manifest["source_data_inventory"].get("combined_bank_data") or {}
    if combined:
        transaction_source_count = combined.get("transaction_source_count", combined.get("csv_source_count", 0))
        lines.extend(
            [
                f"- Bank/account transaction sources combined: {transaction_source_count}",
                f"- CSV sources combined: {combined.get('csv_source_count', 0)}",
                f"- Parsed statement PDF sources combined: {combined.get('pdf_source_count', 0)}",
                f"- Unique bank/account rows in period: {combined.get('unique_rows_in_period', 0)}",
                f"- Duplicate overlap rows removed: {combined.get('duplicate_rows_removed', 0)}",
                f"- Source accounts detected: {', '.join(combined.get('source_accounts') or []) or 'none'}",
            ]
        )
        source_summary = combined.get("source_provider_summary") or {}
        if source_summary:
            lines.append("- Source provider rollup:")
            for provider, info in sorted(source_summary.items()):
                lines.append(
                    f"  - {provider}: {info.get('rows', 0)} rows; "
                    f"in {info.get('money_in', '0.00')}; out {info.get('money_out', '0.00')}; net {info.get('net', '0.00')}"
                )
        flow_summary = combined.get("flow_provider_summary") or {}
        if flow_summary:
            lines.append("- Flow provider rollup:")
            for provider, info in sorted(flow_summary.items()):
                lines.append(
                    f"  - {provider}: {info.get('rows', 0)} rows; "
                    f"in {info.get('money_in', '0.00')}; out {info.get('money_out', '0.00')}; net {info.get('net', '0.00')}"
                )
    registry = manifest["source_data_inventory"].get("accounting_system_registry") or {}
    if registry:
        domains = registry.get("domain_counts") or {}
        domain_text = ", ".join(f"{key}={value}" for key, value in sorted(domains.items())[:8])
        lines.extend(
            [
                f"- Accounting modules/tools unified: {registry.get('module_count', 0)}",
                f"- Accounting artifacts indexed: {registry.get('artifact_count', 0)}",
                f"- Accounting domains: {domain_text or 'none'}",
            ]
        )
    lines.extend(["", "## Generated Outputs", ""])
    for label, info in outputs.items():
        marker = "OK" if info["exists"] else "MISSING"
        lines.append(f"- {marker} {label}: `{info['path']}`")
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- No Companies House filing was submitted.",
            "- No HMRC filing was submitted.",
            "- No tax, penalty, or government payment was made.",
            "- HMRC iXBRL/CT600 official submission remains a manual commercial-software step.",
            "- The human/director/accountant performs approval, upload, declaration, submission, and payment manually.",
            "",
            f"Next: {manifest['next_human_step']}",
            "",
        ]
    )
    summary_path.write_text("\n".join(lines), encoding="utf-8")
    return manifest_path, summary_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build full local company accounts from repo data.")
    parser.add_argument("--company-name", default="EXAMPLE TRADING LTD")
    parser.add_argument("--company-number", default=DEFAULT_COMPANY_NUMBER)
    parser.add_argument("--period-start", default=DEFAULT_PERIOD_START)
    parser.add_argument("--period-end", default=DEFAULT_PERIOD_END)
    parser.add_argument("--as-of", default=date.today().isoformat())
    parser.add_argument("--raw-data-dir", action="append", default=[])
    parser.add_argument("--no-default-roots", action="store_true")
    parser.add_argument("--no-fetch", action="store_true", help="Skip live Companies House public profile lookup.")
    return parser.parse_args()


def build_full_company_accounts(
    *,
    company_name: str = "EXAMPLE TRADING LTD",
    company_number: str = DEFAULT_COMPANY_NUMBER,
    period_start: str = DEFAULT_PERIOD_START,
    period_end: str = DEFAULT_PERIOD_END,
    as_of: date | None = None,
    no_fetch: bool = True,
    raw_data_roots: Sequence[str | Path] | None = None,
    include_default_roots: bool = True,
) -> dict[str, Any]:
    as_of_value = as_of or date.today()
    source_inventory = inventory_source_data(
        company_number=company_number,
        period_start=period_start,
        period_end=period_end,
        raw_data_roots=raw_data_roots,
        include_default_roots=include_default_roots,
    )
    accounts_build_exit_code = run_accounts_pack_builder(
        company_name=company_name,
        period_start=period_start,
        period_end=period_end,
        raw_data_roots=raw_data_roots,
        include_default_roots=include_default_roots,
    )
    statutory_manifest: dict[str, Any] = {}
    if accounts_build_exit_code == 0:
        statutory_manifest = build_statutory_filing_pack(
            company_name=company_name,
            company_number=company_number,
            period_start=period_start,
            period_end=period_end,
        )

    audit = build_report(
        company_number=company_number,
        period_start=period_start,
        period_end=period_end,
        as_of=as_of_value,
        fetch_public=not no_fetch,
    )
    audit_output_dir = KAS_DIR / "output" / "company_compliance" / company_number
    audit_json, audit_md = write_report(audit, audit_output_dir)

    manifest = build_manifest(
        company_number=company_number,
        period_start=period_start,
        period_end=period_end,
        as_of=as_of_value,
        accounts_build_exit_code=accounts_build_exit_code,
        audit_json=audit_json,
        audit_md=audit_md,
        source_inventory=source_inventory,
        statutory_manifest=statutory_manifest,
    )
    manifest_path, summary_path = write_full_run_summary(manifest, audit_output_dir)

    print(f"Wrote {manifest_path}")
    print(f"Wrote {summary_path}")
    print(f"Wrote {audit_json}")
    print(f"Wrote {audit_md}")
    return {
        "status": "completed" if accounts_build_exit_code == 0 else "failed",
        "exit_code": 0 if accounts_build_exit_code == 0 else accounts_build_exit_code,
        "manifest": manifest,
        "manifest_path": str(manifest_path),
        "summary_path": str(summary_path),
        "audit_json": str(audit_json),
        "audit_markdown": str(audit_md),
    }


def main() -> int:
    args = parse_args()
    result = build_full_company_accounts(
        company_name=args.company_name,
        company_number=args.company_number,
        period_start=args.period_start,
        period_end=args.period_end,
        as_of=date.fromisoformat(args.as_of),
        no_fetch=args.no_fetch,
        raw_data_roots=args.raw_data_dir,
        include_default_roots=not args.no_default_roots,
    )
    return int(result.get("exit_code", 1))


if __name__ == "__main__":
    raise SystemExit(main())
