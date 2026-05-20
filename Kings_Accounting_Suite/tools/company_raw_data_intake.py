"""Inventory all raw company accounting evidence before account generation.

This is the safe intake layer for a company's raw data folder. It does not
classify transactions into tax boxes or submit anything externally. It records
what evidence exists, which accounting path can use it, and which files remain
review-only evidence.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence


KAS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = KAS_DIR.parent

DEFAULT_COMPANY_NUMBER = "00000000"
DEFAULT_PERIOD_START = "2024-05-01"
DEFAULT_PERIOD_END = "2025-04-30"

RAW_EVIDENCE_SUFFIXES = {
    ".csv",
    ".pdf",
    ".xlsx",
    ".xls",
    ".json",
    ".jpg",
    ".jpeg",
    ".png",
    ".txt",
    ".md",
}

SKIP_DIR_NAMES = {
    ".git",
    ".claude",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    "output",
    "cache",
}


@dataclass
class RawDataFile:
    path: str
    name: str
    suffix: str
    bytes: int
    modified_at: str
    category: str
    provider: str
    ingestion_path: str
    evidence_role: str
    warnings: list[str] = field(default_factory=list)


@dataclass
class RawDataManifest:
    schema_version: str
    generated_at: str
    company_number: str
    period_start: str
    period_end: str
    repo_root: str
    raw_roots: list[str]
    files: list[RawDataFile]
    summary: dict[str, Any]
    safe_boundaries: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def resolve_raw_roots(
    repo_root: str | Path = REPO_ROOT,
    raw_roots: Sequence[str | Path] | None = None,
    *,
    include_default_roots: bool = True,
) -> list[Path]:
    root = Path(repo_root).resolve()
    candidates: list[Path] = []
    if include_default_roots:
        candidates.extend([root / "uploads", root / "bussiness accounts"])
    for raw in raw_roots or []:
        path = Path(raw)
        if not path.is_absolute():
            path = root / path
        candidates.append(path)

    resolved: list[Path] = []
    seen: set[str] = set()
    for path in candidates:
        key = str(path.resolve() if path.exists() else path).lower()
        if key in seen:
            continue
        seen.add(key)
        resolved.append(path)
    return resolved


def build_company_raw_data_manifest(
    repo_root: str | Path = REPO_ROOT,
    *,
    company_number: str = DEFAULT_COMPANY_NUMBER,
    period_start: str = DEFAULT_PERIOD_START,
    period_end: str = DEFAULT_PERIOD_END,
    raw_roots: Sequence[str | Path] | None = None,
    include_default_roots: bool = True,
) -> RawDataManifest:
    root = Path(repo_root).resolve()
    roots = resolve_raw_roots(root, raw_roots, include_default_roots=include_default_roots)
    files: list[RawDataFile] = []
    for raw_root in roots:
        if not raw_root.exists():
            continue
        for path in sorted(raw_root.rglob("*"), key=lambda p: str(p).lower()):
            if not path.is_file() or is_skipped(path):
                continue
            files.append(file_record(path))

    summary = summarise_files(files)
    return RawDataManifest(
        schema_version="company-raw-data-intake-v1",
        generated_at=datetime.now(timezone.utc).isoformat(),
        company_number=company_number,
        period_start=period_start,
        period_end=period_end,
        repo_root=str(root),
        raw_roots=[str(path) for path in roots],
        files=files,
        summary=summary,
        safe_boundaries={
            "official_companies_house_filing": "manual_only",
            "official_hmrc_submission": "manual_only",
            "tax_or_penalty_payment": "manual_only",
            "exchange_or_trading_mutation": "blocked_from_accounting_intake",
        },
    )


def file_record(path: Path) -> RawDataFile:
    stat = path.stat()
    category, provider, ingestion_path, evidence_role, warnings = classify_raw_data_file(path)
    return RawDataFile(
        path=str(path),
        name=path.name,
        suffix=path.suffix.lower(),
        bytes=stat.st_size,
        modified_at=datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        category=category,
        provider=provider,
        ingestion_path=ingestion_path,
        evidence_role=evidence_role,
        warnings=warnings,
    )


def classify_raw_data_file(path: Path) -> tuple[str, str, str, str, list[str]]:
    name = path.name.lower()
    suffix = path.suffix.lower()
    warnings: list[str] = []

    provider = "unknown"
    if "zempler" in name or name.startswith("statement__gbp_"):
        provider = "zempler"
    elif (
        "revolut" in name
        or name.startswith("account-statement_")
        or name.startswith("transactions report ")
        or name.startswith("statement_")
    ):
        provider = "revolut"
    elif "sumup" in name:
        provider = "sumup"
    elif "hmrc" in name or "government gateway" in name:
        provider = "hmrc"
    elif "companies house" in name or "company house" in name:
        provider = "companies_house"

    if suffix == ".csv":
        if name.startswith("transactions report ") or name.startswith("statement_") or "bank" in name:
            return "bank_transactions", provider, "combined_bank_data", "transaction_source", warnings
        return "tabular_accounting_data", provider, "combined_bank_data_candidate", "transaction_or_schedule_source", warnings

    if suffix == ".pdf":
        if name.startswith("statement__gbp_"):
            return "bank_statement_pdf", provider, "combined_bank_data_pdf_parser", "transaction_source", warnings
        if name.startswith("account-statement_"):
            return "bank_statement_pdf", provider, "evidence_only_no_double_count", "supporting_statement", warnings
        if name.startswith("inv_") or "invoice" in name:
            return "invoice_or_sales_evidence", provider, "evidence_review", "invoice_source", warnings
        if "subcontractor" in name or "supplier" in name:
            return "supplier_or_subcontractor_statement", provider, "evidence_review", "expense_support", warnings
        if provider in {"hmrc", "companies_house"}:
            return "compliance_evidence", provider, "evidence_review", "filing_or_gateway_evidence", warnings
        warnings.append("pdf_not_parsed_as_transactions")
        return "pdf_evidence", provider, "evidence_review", "supporting_evidence", warnings

    if suffix in {".xlsx", ".xls"}:
        return "workbook_or_ledger", provider, "evidence_review", "ledger_or_schedule", warnings

    if suffix == ".json":
        return "machine_manifest_or_export", provider, "manifest_context", "machine_readable_context", warnings

    if suffix in {".jpg", ".jpeg", ".png"}:
        return "receipt_or_image_evidence", provider, "evidence_review", "receipt_photo", warnings

    warnings.append("nonstandard_suffix_included_for_no_skip_review")
    return "supporting_text_evidence", provider, "evidence_review", "supporting_evidence", warnings


def summarise_files(files: list[RawDataFile]) -> dict[str, Any]:
    by_category = Counter(file.category for file in files)
    by_provider = Counter(file.provider for file in files)
    by_ingestion = Counter(file.ingestion_path for file in files)
    transaction_sources = [
        file for file in files
        if file.ingestion_path in {"combined_bank_data", "combined_bank_data_pdf_parser"}
    ]
    evidence_only = [
        file for file in files
        if file.ingestion_path not in {"combined_bank_data", "combined_bank_data_pdf_parser"}
    ]
    return {
        "file_count": len(files),
        "bytes": sum(file.bytes for file in files),
        "category_counts": dict(sorted(by_category.items())),
        "provider_counts": dict(sorted(by_provider.items())),
        "ingestion_path_counts": dict(sorted(by_ingestion.items())),
        "transaction_source_count": len(transaction_sources),
        "evidence_only_count": len(evidence_only),
        "warnings": sorted({warning for file in files for warning in file.warnings}),
    }


def write_raw_data_manifest_artifacts(
    manifest: RawDataManifest,
    *,
    output_dir: str | Path | None = None,
) -> tuple[Path, Path]:
    out_dir = Path(output_dir) if output_dir else (
        Path(manifest.repo_root)
        / "Kings_Accounting_Suite"
        / "output"
        / "company_raw_data"
        / manifest.company_number
        / f"{manifest.period_start}_to_{manifest.period_end}"
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "raw_data_manifest.json"
    md_path = out_dir / "raw_data_manifest.md"

    data = manifest.to_dict()
    json_path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

    summary = manifest.summary
    lines = [
        "# Company Raw Data Intake",
        "",
        f"- Generated: {manifest.generated_at}",
        f"- Company number: {manifest.company_number}",
        f"- Period: {manifest.period_start} to {manifest.period_end}",
        f"- Raw roots: {', '.join(manifest.raw_roots) or 'none'}",
        f"- Files: {summary.get('file_count', 0)}",
        f"- Transaction sources: {summary.get('transaction_source_count', 0)}",
        f"- Evidence-only files: {summary.get('evidence_only_count', 0)}",
        "",
        "## Providers",
        "",
    ]
    for provider, count in (summary.get("provider_counts") or {}).items():
        lines.append(f"- {provider}: {count}")
    lines.extend(["", "## Ingestion Paths", ""])
    for path, count in (summary.get("ingestion_path_counts") or {}).items():
        lines.append(f"- {path}: {count}")
    lines.extend(["", "## Files", ""])
    for item in manifest.files:
        lines.append(f"- `{item.ingestion_path}` {item.provider} {item.category}: `{item.path}`")
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- This intake does not file Companies House accounts.",
            "- This intake does not submit HMRC returns.",
            "- This intake does not pay tax or penalties.",
            "- This intake does not mutate exchange or trading state.",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


def is_skipped(path: Path) -> bool:
    return any(part in SKIP_DIR_NAMES for part in path.parts)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inventory raw company accounting evidence.")
    parser.add_argument("--company-number", default=DEFAULT_COMPANY_NUMBER)
    parser.add_argument("--period-start", default=DEFAULT_PERIOD_START)
    parser.add_argument("--period-end", default=DEFAULT_PERIOD_END)
    parser.add_argument("--raw-data-dir", action="append", default=[])
    parser.add_argument("--no-default-roots", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = build_company_raw_data_manifest(
        REPO_ROOT,
        company_number=args.company_number,
        period_start=args.period_start,
        period_end=args.period_end,
        raw_roots=args.raw_data_dir,
        include_default_roots=not args.no_default_roots,
    )
    json_path, md_path = write_raw_data_manifest_artifacts(manifest)
    print(json_path)
    print(md_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
