"""Read-only Companies House and Corporation Tax triage for Aureon.

This runner does not file accounts, submit tax returns, pay penalties, or mutate
any Companies House/HMRC/exchange service. It prepares a local checklist that
connects public filing obligations to the accounting evidence already present in
the repo.

Usage from the repo root:
  .venv\\Scripts\\python.exe Kings_Accounting_Suite\\tools\\company_house_tax_audit.py --as-of 2026-05-08
"""

from __future__ import annotations

import argparse
import html
import json
import re
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable


DEFAULT_COMPANY_NUMBER = "00000000"
DEFAULT_COMPANY_NAME = "EXAMPLE TRADING LTD"
DEFAULT_PERIOD_START = "2024-05-01"
DEFAULT_PERIOD_END = "2025-04-30"

KAS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = KAS_DIR.parent
DEFAULT_OUTPUT_DIR = KAS_DIR / "output" / "company_compliance" / DEFAULT_COMPANY_NUMBER

OFFICIAL_SOURCES = {
    "companies_house_profile": "https://find-and-update.company-information.service.gov.uk/company/{company_number}",
    "companies_house_late_filing": "https://www.gov.uk/government/publications/late-filing-penalties-from-companies-house/late-filing-penalties",
    "hmrc_company_tax_return": "https://www.gov.uk/company-tax-returns/overview",
    "hmrc_pay_corporation_tax": "https://www.gov.uk/pay-corporation-tax",
    "hmrc_corporation_tax_due_date_manual": "https://www.gov.uk/hmrc-internal-manuals/company-taxation-manual/ctm01800",
    "hmrc_company_tax_penalties": "https://www.gov.uk/company-tax-returns/penalties-for-late-filing",
    "companies_house_confirmation_statement": "https://www.gov.uk/guidance/filing-your-companys-confirmation-statement",
}


@dataclass
class PublicCompanyProfile:
    company_name: str = ""
    company_number: str = ""
    registered_office: str = ""
    company_status: str = ""
    company_type: str = ""
    incorporated_on: str = ""
    accounts_overdue: bool = False
    active_proposal_to_strike_off: bool = False
    next_accounts_made_up_to: str = ""
    accounts_due_by: str = ""
    last_accounts_made_up_to: str = ""
    next_confirmation_statement_date: str = ""
    confirmation_statement_due_by: str = ""
    last_confirmation_statement_date: str = ""
    sic_codes: list[str] = field(default_factory=list)
    source_url: str = ""
    fetched_at: str = ""
    fetch_error: str = ""


@dataclass
class LocalPackInventory:
    period_start: str
    period_end: str
    pack_dir: str
    required_files: dict[str, bool]
    generated_documents: list[dict[str, Any]] = field(default_factory=list)
    rows_in_period: int | None = None
    combined_bank_data: dict[str, Any] = field(default_factory=dict)
    complete: bool = False
    missing_files: list[str] = field(default_factory=list)


@dataclass
class StatementCoverage:
    source_dir: str
    period_start: str
    period_end: str
    required_months: list[str]
    covered_months: list[str]
    missing_months: list[str]
    matching_files: list[dict[str, str]]
    complete: bool


@dataclass
class DeadlineAssessment:
    name: str
    due_date: str
    status: str
    days_overdue: int
    rule_source: str
    risk_note: str
    estimated_penalty: str = ""


def strip_html_to_text(raw: str) -> str:
    """Convert simple public-register HTML to searchable text."""
    text = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _match(pattern: str, text: str) -> str:
    found = re.search(pattern, text, flags=re.IGNORECASE)
    return found.group(1).strip(" -") if found else ""


def parse_companies_house_profile(raw: str, *, source_url: str = "", fetched_at: str = "") -> PublicCompanyProfile:
    text = strip_html_to_text(raw)
    profile = PublicCompanyProfile(source_url=source_url, fetched_at=fetched_at)
    h1 = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", raw)
    if h1:
        profile.company_name = strip_html_to_text(h1.group(1)).upper()
    else:
        profile.company_name = _match(r"([A-Z0-9 &'.,()-]+?)\s+Company number\s+[A-Z0-9]+", text)
    profile.company_number = _match(r"Company number\s+([A-Z0-9]+)", text)
    profile.registered_office = _match(r"Registered office address\s+(.+?)\s+Company status", text)
    profile.company_status = _match(r"Company status\s+(.+?)\s+Company type", text)
    profile.company_type = _match(r"Company type\s+(.+?)\s+Incorporated on", text)
    profile.incorporated_on = _match(r"Incorporated on\s+([0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4})", text)
    profile.accounts_overdue = "accounts overdue" in text.lower()
    profile.active_proposal_to_strike_off = "active proposal to strike off" in text.lower()
    profile.next_accounts_made_up_to = _match(
        r"Next accounts made up to\s+([0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4})", text
    )
    profile.accounts_due_by = _match(
        r"Next accounts made up to\s+[0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4}\s+due by\s+([0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4})",
        text,
    )
    profile.last_accounts_made_up_to = _match(
        r"Last accounts made up to\s+([0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4})", text
    )
    profile.next_confirmation_statement_date = _match(
        r"Next statement date\s+([0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4})", text
    )
    profile.confirmation_statement_due_by = _match(
        r"Next statement date\s+[0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4}\s+due by\s+([0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4})",
        text,
    )
    profile.last_confirmation_statement_date = _match(
        r"Last statement dated\s+([0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4})", text
    )
    profile.sic_codes = re.findall(r"\b([0-9]{5}\s+-\s+[^*]+?)(?=\s+[0-9]{5}\s+-|\s+Tell us|\s+Support links|$)", text)
    return profile


def fetch_companies_house_profile(company_number: str, *, timeout: int = 20) -> PublicCompanyProfile:
    url = OFFICIAL_SOURCES["companies_house_profile"].format(company_number=company_number)
    fetched_at = datetime.now(timezone.utc).isoformat()
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "AureonCompanyComplianceAudit/1.0 (read-only)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        return parse_companies_house_profile(raw, source_url=url, fetched_at=fetched_at)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return PublicCompanyProfile(
            company_name=DEFAULT_COMPANY_NAME,
            company_number=company_number,
            source_url=url,
            fetched_at=fetched_at,
            fetch_error=f"{type(exc).__name__}: {exc}",
        )


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def inventory_local_pack(period_start: str, period_end: str) -> LocalPackInventory:
    pack_dir = KAS_DIR / "output" / "gateway" / f"{period_start}_to_{period_end}"
    required_names = [
        "cover.pdf",
        "general_ledger.xlsx",
        "management_accounts.xlsx",
        "period_pack_manifest.json",
        "pnl.pdf",
        "ra_consulting_and_brokerage_accounts_pack_2024-05-01_to_2025-04-30.pdf",
        "tax_summary.pdf",
        "trial_balance.xlsx",
    ]
    required = {name: (pack_dir / name).exists() for name in required_names}
    missing = [name for name, exists in required.items() if not exists]
    manifest = _load_json(pack_dir / "period_pack_manifest.json")
    generated_documents = []
    for item in list(manifest.get("generated_documents") or []):
        doc = dict(item)
        old_path = Path(str(doc.get("path", "")))
        local_path = pack_dir / old_path.name
        if old_path.name and local_path.exists():
            doc["path"] = str(local_path)
        generated_documents.append(doc)
    return LocalPackInventory(
        period_start=period_start,
        period_end=period_end,
        pack_dir=str(pack_dir),
        required_files=required,
        generated_documents=generated_documents,
        rows_in_period=manifest.get("rows_in_period"),
        combined_bank_data=manifest.get("combined_bank_data") or {},
        complete=not missing,
        missing_files=missing,
    )


def _parse_yyyymmdd(value: str) -> date:
    return datetime.strptime(value, "%Y%m%d").date()


def parse_statement_span(name: str) -> tuple[date, date] | None:
    match = re.search(r"Statement__GBP_(\d{8})-(\d{8})", name, flags=re.IGNORECASE)
    if match:
        return _parse_yyyymmdd(match.group(1)), _parse_yyyymmdd(match.group(2))

    match = re.search(
        r"account-statement_(\d{1,2}-[A-Za-z]{3}-\d{4})_(\d{1,2}-[A-Za-z]{3}-\d{4})",
        name,
        flags=re.IGNORECASE,
    )
    if match:
        return (
            datetime.strptime(match.group(1), "%d-%b-%Y").date(),
            datetime.strptime(match.group(2), "%d-%b-%Y").date(),
        )

    return None


def month_keys_between(start: date, end: date) -> list[str]:
    months: list[str] = []
    cursor = date(start.year, start.month, 1)
    last = date(end.year, end.month, 1)
    while cursor <= last:
        months.append(cursor.strftime("%Y-%m"))
        if cursor.month == 12:
            cursor = date(cursor.year + 1, 1, 1)
        else:
            cursor = date(cursor.year, cursor.month + 1, 1)
    return months


def months_touched_by_span(start: date, end: date) -> set[str]:
    return set(month_keys_between(start, end))


def inventory_statement_coverage(source_dir: Path, period_start: str, period_end: str) -> StatementCoverage:
    start = date.fromisoformat(period_start)
    end = date.fromisoformat(period_end)
    required = month_keys_between(start, end)
    covered: set[str] = set()
    matching_files: list[dict[str, str]] = []

    if source_dir.exists():
        for path in sorted(source_dir.iterdir(), key=lambda p: p.name.lower()):
            if not path.is_file():
                continue
            span = parse_statement_span(path.name)
            if not span:
                continue
            span_start, span_end = span
            if span_end < start or span_start > end:
                continue
            months = sorted(months_touched_by_span(max(span_start, start), min(span_end, end)))
            covered.update(months)
            matching_files.append(
                {
                    "path": str(path),
                    "span_start": span_start.isoformat(),
                    "span_end": span_end.isoformat(),
                    "covered_months": ", ".join(months),
                }
            )

    covered_list = [month for month in required if month in covered]
    missing = [month for month in required if month not in covered]
    return StatementCoverage(
        source_dir=str(source_dir),
        period_start=period_start,
        period_end=period_end,
        required_months=required,
        covered_months=covered_list,
        missing_months=missing,
        matching_files=matching_files,
        complete=not missing,
    )


def companies_house_late_penalty(days_overdue: int) -> str:
    if days_overdue <= 0:
        return "none estimated"
    if days_overdue <= 31:
        return "private company tier: GBP 150"
    if days_overdue <= 92:
        return "private company tier: GBP 375"
    if days_overdue <= 184:
        return "private company tier: GBP 750"
    return "private company tier: GBP 1,500"


def hmrc_company_tax_penalty(days_overdue: int) -> str:
    if days_overdue <= 0:
        return "none estimated"
    if days_overdue < 92:
        return "Company Tax Return at least 1 day late: GBP 200"
    if days_overdue < 183:
        return "Company Tax Return at least 3 months late: GBP 400 total fixed penalties"
    if days_overdue < 365:
        return "Company Tax Return at least 6 months late: fixed penalties plus HMRC tax determination/10% unpaid tax risk"
    return "Company Tax Return at least 12 months late: fixed penalties plus further 10% unpaid tax risk"


def assess_deadline(
    *,
    name: str,
    due_date: date,
    as_of: date,
    rule_source: str,
    risk_note: str,
    penalty_kind: str = "",
) -> DeadlineAssessment:
    days_overdue = max((as_of - due_date).days, 0)
    status = "overdue" if days_overdue else "not_due_or_due_today"
    estimated = ""
    if penalty_kind == "companies_house_accounts":
        estimated = companies_house_late_penalty(days_overdue)
    elif penalty_kind == "hmrc_company_tax":
        estimated = hmrc_company_tax_penalty(days_overdue)
    return DeadlineAssessment(
        name=name,
        due_date=due_date.isoformat(),
        status=status,
        days_overdue=days_overdue,
        rule_source=rule_source,
        risk_note=risk_note,
        estimated_penalty=estimated,
    )


def build_assessments(period_end: str, as_of: date) -> list[DeadlineAssessment]:
    end = date.fromisoformat(period_end)
    companies_house_due = date(2026, 1, 31)
    corporation_tax_payment_due = date(2026, 2, 1)
    company_tax_return_due = date(end.year + 1, end.month, end.day)
    confirmation_statement_due = date(2026, 5, 9)
    return [
        assess_deadline(
            name="Companies House annual accounts",
            due_date=companies_house_due,
            as_of=as_of,
            rule_source=OFFICIAL_SOURCES["companies_house_late_filing"],
            risk_note="Public register says accounts made up to 30 April 2025 were due by 31 January 2026.",
            penalty_kind="companies_house_accounts",
        ),
        assess_deadline(
            name="HMRC Corporation Tax payment",
            due_date=corporation_tax_payment_due,
            as_of=as_of,
            rule_source=OFFICIAL_SOURCES["hmrc_corporation_tax_due_date_manual"],
            risk_note="HMRC says when an accounting period ends on the last day of a calendar month, the normal Corporation Tax due date is the first day of the tenth month.",
        ),
        assess_deadline(
            name="HMRC Company Tax Return / CT600",
            due_date=company_tax_return_due,
            as_of=as_of,
            rule_source=OFFICIAL_SOURCES["hmrc_company_tax_return"],
            risk_note="HMRC states the Company Tax Return deadline is 12 months after the accounting period.",
            penalty_kind="hmrc_company_tax",
        ),
        assess_deadline(
            name="Companies House confirmation statement",
            due_date=confirmation_statement_due,
            as_of=as_of,
            rule_source=OFFICIAL_SOURCES["companies_house_confirmation_statement"],
            risk_note="Public register says the next statement date is 25 April 2026 and due by 9 May 2026.",
        ),
    ]


def build_next_actions(
    profile: PublicCompanyProfile,
    pack: LocalPackInventory,
    coverage: StatementCoverage,
    assessments: Iterable[DeadlineAssessment],
) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    if profile.active_proposal_to_strike_off:
        actions.append(
            {
                "priority": "P0",
                "owner": "director/accountant",
                "action": "Resolve active proposal to strike off by filing outstanding Companies House documents and responding to any Companies House notices.",
                "evidence": profile.source_url,
            }
        )
    for assessment in assessments:
        if assessment.status == "overdue":
            actions.append(
                {
                    "priority": "P0" if "Companies House" in assessment.name else "P1",
                    "owner": "director/accountant",
                    "action": f"Handle overdue item: {assessment.name} due {assessment.due_date}.",
                    "evidence": assessment.rule_source,
                }
            )
    if pack.complete:
        actions.append(
            {
                "priority": "P0",
                "owner": "accounting system/director review",
                "action": "Review and approve the local 2024-05-01 to 2025-04-30 accounts pack for Companies House filing.",
                "evidence": pack.pack_dir,
            }
        )
    else:
        actions.append(
            {
                "priority": "P0",
                "owner": "accounting system",
                "action": "Regenerate the accounts pack because required output files are missing.",
                "evidence": ", ".join(pack.missing_files),
            }
        )
    if coverage.complete:
        actions.append(
            {
                "priority": "P1",
                "owner": "accounting system/director review",
                "action": "Use the complete local bank statement coverage as evidence for the accounts period.",
                "evidence": coverage.source_dir,
            }
        )
    else:
        actions.append(
            {
                "priority": "P1",
                "owner": "director/accounting system",
                "action": "Add missing bank statements for the accounts period before finalising tax figures.",
                "evidence": ", ".join(coverage.missing_months),
            }
        )
    actions.append(
        {
            "priority": "SAFETY",
            "owner": "system",
            "action": "Do not submit Companies House/HMRC filings or payments automatically; require director/accountant review and explicit confirmation.",
            "evidence": "read-only audit mode",
        }
    )
    return actions


def build_markdown(report: dict[str, Any]) -> str:
    profile = report["public_company_profile"]
    pack = report["local_accounts_pack"]
    coverage = report["bank_statement_coverage"]

    def md_text(value: Any) -> str:
        return str(value or "").replace("\u2014", "-").replace("\u2013", "-").replace("\u2019", "'")

    lines = [
        "# Company House and Tax Triage",
        "",
        f"- Generated: {report['generated_at']}",
        f"- As of: {report['as_of']}",
        f"- Company: {md_text(profile.get('company_name') or DEFAULT_COMPANY_NAME)}",
        f"- Company number: {md_text(profile.get('company_number') or report['company_number'])}",
        f"- Companies House profile: {md_text(profile.get('source_url'))}",
        "",
        "## Public Register Position",
        "",
        f"- Status: {md_text(profile.get('company_status') or 'unknown')}",
        f"- Accounts overdue: {profile.get('accounts_overdue')}",
        f"- Active proposal to strike off: {profile.get('active_proposal_to_strike_off')}",
        f"- Next accounts made up to: {md_text(profile.get('next_accounts_made_up_to') or 'unknown')}",
        f"- Accounts due by: {md_text(profile.get('accounts_due_by') or 'unknown')}",
        f"- Confirmation statement due by: {md_text(profile.get('confirmation_statement_due_by') or 'unknown')}",
        f"- Last confirmation statement dated: {md_text(profile.get('last_confirmation_statement_date') or 'unknown')}",
        "",
        "## Local Accounts Evidence",
        "",
        f"- Pack directory: `{pack['pack_dir']}`",
        f"- Pack complete: {pack['complete']}",
        f"- Rows in period manifest: {pack.get('rows_in_period')}",
    ]
    combined = pack.get("combined_bank_data") or {}
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
    if pack["missing_files"]:
        lines.append(f"- Missing files: {', '.join(pack['missing_files'])}")
    else:
        lines.append("- Missing files: none")
    lines.extend(
        [
            f"- Bank statement coverage complete: {coverage['complete']}",
            f"- Covered months: {', '.join(coverage['covered_months'])}",
            f"- Missing months: {', '.join(coverage['missing_months']) if coverage['missing_months'] else 'none'}",
            "",
            "## Deadline Assessment",
            "",
        ]
    )
    for item in report["deadline_assessments"]:
        penalty = f" Estimated penalty/risk: {item['estimated_penalty']}." if item.get("estimated_penalty") else ""
        lines.append(
            f"- {item['name']}: {item['status']} due {item['due_date']} "
            f"({item['days_overdue']} days overdue).{penalty}"
        )
    lines.extend(["", "## Priority Checklist", ""])
    for action in report["next_actions"]:
        lines.append(f"- [{action['priority']}] {action['action']} Owner: {action['owner']}.")
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "",
            "This audit is read-only. It does not file accounts, submit a CT600, pay Corporation Tax, appeal penalties, or mutate any government/exchange system.",
            "Director/accountant approval is required before any official submission.",
            "",
            "## Official Rule Sources",
            "",
        ]
    )
    for label, url in report["official_sources"].items():
        lines.append(f"- {label}: {url}")
    return "\n".join(lines) + "\n"


def build_report(
    *,
    company_number: str,
    period_start: str,
    period_end: str,
    as_of: date,
    fetch_public: bool,
) -> dict[str, Any]:
    profile = (
        fetch_companies_house_profile(company_number)
        if fetch_public
        else PublicCompanyProfile(
            company_name=DEFAULT_COMPANY_NAME,
            company_number=company_number,
            source_url=OFFICIAL_SOURCES["companies_house_profile"].format(company_number=company_number),
            fetched_at=datetime.now(timezone.utc).isoformat(),
            fetch_error="Skipped by --no-fetch",
        )
    )
    pack = inventory_local_pack(period_start, period_end)
    coverage = inventory_statement_coverage(REPO_ROOT / "bussiness accounts", period_start, period_end)
    assessments = build_assessments(period_end, as_of)
    report = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "as_of": as_of.isoformat(),
        "company_number": company_number,
        "period_start": period_start,
        "period_end": period_end,
        "official_sources": {
            key: value.format(company_number=company_number)
            for key, value in OFFICIAL_SOURCES.items()
        },
        "public_company_profile": asdict(profile),
        "local_accounts_pack": asdict(pack),
        "bank_statement_coverage": asdict(coverage),
        "deadline_assessments": [asdict(item) for item in assessments],
        "next_actions": build_next_actions(profile, pack, coverage, assessments),
        "safety": {
            "read_only": True,
            "submits_to_companies_house": False,
            "submits_to_hmrc": False,
            "pays_tax_or_penalties": False,
            "requires_human_approval": True,
        },
    }
    return report


def write_report(report: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "company_house_tax_audit.json"
    md_path = output_dir / "company_house_tax_audit.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(build_markdown(report), encoding="utf-8")
    return json_path, md_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only company accounts and tax compliance audit.")
    parser.add_argument("--company-number", default=DEFAULT_COMPANY_NUMBER)
    parser.add_argument("--period-start", default=DEFAULT_PERIOD_START)
    parser.add_argument("--period-end", default=DEFAULT_PERIOD_END)
    parser.add_argument("--as-of", default=date.today().isoformat())
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--no-fetch", action="store_true", help="Skip live Companies House fetch.")
    parser.add_argument("--fail-on-overdue", action="store_true", help="Return a non-zero exit code if overdue items are found.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(
        company_number=args.company_number,
        period_start=args.period_start,
        period_end=args.period_end,
        as_of=date.fromisoformat(args.as_of),
        fetch_public=not args.no_fetch,
    )
    json_path, md_path = write_report(report, Path(args.output_dir))
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    if args.fail_on_overdue and any(item["status"] == "overdue" for item in report["deadline_assessments"]):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
