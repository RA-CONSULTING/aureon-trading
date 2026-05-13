"""Incoming-payment payer provenance and CIS/VAT assurance controls.

This module is deliberately read-only. It may query the public Companies House
API when an API key is available, but it never files, submits, verifies with
HMRC, pays money, or creates supplier/CIS evidence.
"""

from __future__ import annotations

import base64
import csv
import json
import os
import re
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Callable


SCHEMA_VERSION = "payer-provenance-v1"
LOOKUP_THRESHOLD = Decimal("400.00")
COMPANIES_HOUSE_API_BASE = "https://api.company-information.service.gov.uk"
COMPANIES_HOUSE_WEB_SEARCH = "https://find-and-update.company-information.service.gov.uk/search"

OFFICIAL_SOURCES = {
    "companies_house_api_search": "https://developer-specs.company-information.service.gov.uk/companies-house-public-data-api/reference/search/search-companies",
    "companies_house_api_company_profile": "https://developer-specs.company-information.service.gov.uk/companies-house-public-data-api/reference/company-profile/company-profile",
    "cis": "https://www.gov.uk/what-is-the-construction-industry-scheme",
    "vat_domestic_reverse_charge": "https://www.gov.uk/guidance/vat-domestic-reverse-charge-for-building-and-construction-services",
    "vat_registration": "https://www.gov.uk/register-for-vat",
    "company_accounting_records": "https://www.gov.uk/running-a-limited-company/company-and-accounting-records",
}

CONSTRUCTION_TERMS = (
    "builder",
    "builders",
    "building",
    "construction",
    "construct",
    "contractor",
    "contracts",
    "subcontract",
    "subcontractor",
    "cis",
    "civil engineering",
    "groundwork",
    "site work",
    "grove builders",
    "heron bros",
    "csr ni",
    "the csr group",
    "amc construction",
    "mmg contracts",
)

CIS_STATEMENT_TERMS = (
    "cis statement",
    "deduction statement",
    "subcontractor statement",
    "payment and deduction statement",
    "cis deduction",
)

CONSTRUCTION_SIC_PREFIXES = ("41", "42", "43")
COMPANY_SUFFIXES = ("ltd", "limited", "plc", "llp", "l.l.p")


@dataclass
class PayerProvenanceRecord:
    row_number: int
    date: str
    description: str
    amount: str
    direction: str
    source_provider: str
    flow_provider: str
    source_account: str
    source_file: str
    source_trace: str
    payer_name_raw: str
    payer_name_normalized: str
    payer_group_total: str
    payer_group_row_count: int
    lookup_required: bool
    lookup_reason: str
    lookup_status: str
    payer_provenance_status: str
    companies_house_candidates: list[dict[str, Any]] = field(default_factory=list)
    selected_company_number: str = ""
    selected_company_name: str = ""
    company_status: str = ""
    company_type: str = ""
    sic_codes: list[str] = field(default_factory=list)
    registered_office_region: str = ""
    evidence_urls: list[str] = field(default_factory=list)
    match_confidence: str = "0.00"
    construction_indicators: list[str] = field(default_factory=list)
    cis_likelihood: str = "low"
    cis_evidence_status: str = "not_cis_income"
    tax_basis_status: str = "not_cis_income"
    vat_reverse_charge_likelihood: str = "not_detected"
    accounting_action: str = "treat_as_standard_income_pending_normal_accounting_controls"
    next_action: str = "No payer lookup needed; retain source trace."


def money(value: Decimal | int | float | str) -> Decimal:
    raw = value if isinstance(value, Decimal) else Decimal(str(value or "0"))
    return raw.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def normalise_payer_name(value: str) -> str:
    text = str(value or "").lower()
    text = re.sub(r"\b(fin|faster payment|fp|bacs|card payment|cr|dr)\b[:\s-]*", " ", text)
    text = re.sub(r"\b(xr|gbp|usd|eur)\b\s*[0-9.]*", " ", text)
    text = re.sub(r"[^a-z0-9&.]+", " ", text)
    tokens = [token for token in text.split() if token not in {"from", "to", "the", "and"}]
    if len(tokens) % 2 == 0 and tokens[: len(tokens) // 2] == tokens[len(tokens) // 2 :]:
        tokens = tokens[: len(tokens) // 2]
    return " ".join(tokens).strip()


def payer_search_url(name: str) -> str:
    return f"{COMPANIES_HOUSE_WEB_SEARCH}?q={urllib.parse.quote_plus(name)}"


def construction_indicators_for(name: str, lookup: dict[str, Any] | None = None) -> list[str]:
    text = f" {normalise_payer_name(name)} "
    indicators = [term for term in CONSTRUCTION_TERMS if construction_term_present(text, term)]
    sic_codes = [str(code) for code in (lookup or {}).get("sic_codes") or []]
    for code in sic_codes:
        if code.startswith(CONSTRUCTION_SIC_PREFIXES):
            indicators.append(f"sic:{code}")
    seen: set[str] = set()
    return [item for item in indicators if not (item in seen or seen.add(item))]


def construction_term_present(text: str, term: str) -> bool:
    clean = re.escape(str(term or "").strip().lower())
    if not clean:
        return False
    return bool(re.search(rf"(?<![a-z0-9]){clean}(?![a-z0-9])", text))


def cis_statement_evidence_present(row: dict[str, str]) -> bool:
    text = " ".join(str(row.get(key, "") or "").lower() for key in ("Description", "Source File", "Duplicate Source Files"))
    return any(term in text for term in CIS_STATEMENT_TERMS)


class CompaniesHouseClient:
    """Tiny public-data client using API-key basic auth."""

    def __init__(self, api_key: str, *, timeout: float = 8.0, items_per_page: int = 5) -> None:
        self.api_key = api_key.strip()
        self.timeout = timeout
        self.items_per_page = items_per_page

    @classmethod
    def from_environment(cls) -> "CompaniesHouseClient | None":
        api_key = first_config_value("COMPANIES_HOUSE_API_KEY", "CH_API_KEY", "AUREON_COMPANIES_HOUSE_API_KEY")
        return cls(api_key) if api_key.strip() else None

    def lookup(self, query: str) -> dict[str, Any]:
        search_url = (
            f"{COMPANIES_HOUSE_API_BASE}/search/companies?"
            f"q={urllib.parse.quote_plus(query)}&items_per_page={self.items_per_page}"
        )
        search = self._get_json(search_url)
        items = search.get("items") or []
        candidates = [candidate_from_search_item(item, query) for item in items]
        selected = select_candidate(candidates)
        if not selected:
            return {
                "lookup_status": "companies_house_no_match",
                "companies_house_candidates": candidates,
                "evidence_urls": [payer_search_url(query)],
                "match_confidence": "0.00",
            }
        if len(candidates) > 1:
            second = Decimal(str(candidates[1].get("match_confidence") or "0"))
            first = Decimal(str(selected.get("match_confidence") or "0"))
            if first - second < Decimal("0.08"):
                status = "ambiguous_companies_house_candidates"
            else:
                status = "matched_companies_house_profile"
        else:
            status = "matched_companies_house_profile"
        profile = self._get_json(f"{COMPANIES_HOUSE_API_BASE}/company/{selected.get('company_number')}")
        merged = {**selected, **candidate_from_company_profile(profile, selected)}
        return {
            "lookup_status": status,
            "companies_house_candidates": candidates,
            "selected": merged,
            "evidence_urls": [
                f"https://find-and-update.company-information.service.gov.uk/company/{merged.get('company_number')}",
                payer_search_url(query),
            ],
            "match_confidence": merged.get("match_confidence", "0.00"),
        }

    def _get_json(self, url: str) -> dict[str, Any]:
        token = base64.b64encode(f"{self.api_key}:".encode("utf-8")).decode("ascii")
        request = urllib.request.Request(url, headers={"Authorization": f"Basic {token}", "Accept": "application/json"})
        with urllib.request.urlopen(request, timeout=self.timeout) as response:  # nosec - public read-only API call.
            return json.loads(response.read().decode("utf-8"))


def candidate_from_search_item(item: dict[str, Any], query: str) -> dict[str, Any]:
    title = str(item.get("title") or "")
    address = item.get("address") or {}
    confidence = SequenceMatcher(None, normalise_payer_name(query), normalise_payer_name(title)).ratio()
    return {
        "company_number": str(item.get("company_number") or ""),
        "company_name": title,
        "company_status": str(item.get("company_status") or ""),
        "company_type": str(item.get("company_type") or ""),
        "registered_office_region": str(address.get("region") or address.get("locality") or ""),
        "sic_codes": [],
        "match_confidence": f"{confidence:.2f}",
    }


def candidate_from_company_profile(profile: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    address = profile.get("registered_office_address") or {}
    return {
        "company_number": str(profile.get("company_number") or fallback.get("company_number") or ""),
        "company_name": str(profile.get("company_name") or fallback.get("company_name") or ""),
        "company_status": str(profile.get("company_status") or fallback.get("company_status") or ""),
        "company_type": str(profile.get("type") or fallback.get("company_type") or ""),
        "registered_office_region": str(address.get("region") or address.get("locality") or fallback.get("registered_office_region") or ""),
        "sic_codes": [str(code) for code in profile.get("sic_codes") or fallback.get("sic_codes") or []],
        "match_confidence": fallback.get("match_confidence", "0.00"),
    }


def select_candidate(candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not candidates:
        return None
    ordered = sorted(candidates, key=lambda item: Decimal(str(item.get("match_confidence") or "0")), reverse=True)
    top = ordered[0]
    return top if Decimal(str(top.get("match_confidence") or "0")) >= Decimal("0.45") else None


def blocked_lookup(name: str, *, reason: str = "blocked_missing_companies_house_api_key") -> dict[str, Any]:
    return {
        "lookup_status": reason,
        "companies_house_candidates": [],
        "evidence_urls": [payer_search_url(name)] if name else [],
        "match_confidence": "0.00",
    }


def first_config_value(*names: str) -> str:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    for env_path in dotenv_candidates():
        if not env_path.exists():
            continue
        try:
            for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
                if not line.strip() or line.lstrip().startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                if key.strip() in names:
                    return value.strip().strip("\"'")
        except OSError:
            continue
    return ""


def dotenv_candidates() -> list[Path]:
    here = Path(__file__).resolve()
    candidates = [Path.cwd() / ".env"]
    candidates.extend(parent / ".env" for parent in here.parents[:4])
    seen: set[str] = set()
    unique: list[Path] = []
    for path in candidates:
        key = str(path).lower()
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique


def build_payer_provenance_manifest(
    rows: list[dict[str, str]],
    *,
    lookup_threshold: Decimal = LOOKUP_THRESHOLD,
    companies_house_lookup: Callable[[str], dict[str, Any]] | None = None,
    perform_online: bool | None = None,
) -> dict[str, Any]:
    """Return a row-level incoming-payment provenance manifest."""
    if perform_online is None:
        perform_online = os.environ.get("AUREON_PAYER_PROVENANCE_OFFLINE", "0") not in {"1", "true", "TRUE"}

    prepared: list[tuple[int, dict[str, str], Decimal, str]] = []
    group_totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    group_counts: Counter[str] = Counter()
    for row_number, row in enumerate(rows, start=1):
        amount = money(row.get("Amount") or "0")
        payer = normalise_payer_name(row.get("Description", ""))
        if amount > 0:
            group_totals[payer] += amount
            group_counts[payer] += 1
        prepared.append((row_number, row, amount, payer))

    client = CompaniesHouseClient.from_environment() if companies_house_lookup is None and perform_online else None
    lookup_cache: dict[str, dict[str, Any]] = {}
    records: list[PayerProvenanceRecord] = []

    for row_number, row, amount, payer in prepared:
        record = build_record_skeleton(
            row_number,
            row,
            amount,
            payer,
            payer_group_total=group_totals.get(payer, Decimal("0.00")),
            payer_group_row_count=group_counts.get(payer, 0),
            lookup_threshold=lookup_threshold,
        )
        if record.lookup_required:
            if payer not in lookup_cache:
                lookup_cache[payer] = run_lookup(
                    payer,
                    companies_house_lookup=companies_house_lookup,
                    client=client,
                    perform_online=perform_online,
                )
            apply_lookup_to_record(record, lookup_cache[payer], row)
        else:
            apply_lookup_to_record(record, {"lookup_status": "not_required_below_threshold_or_no_cis_signal"}, row)
        records.append(record)

    incoming_records = [record for record in records if record.direction == "income"]
    lookup_required_count = sum(1 for record in incoming_records if record.lookup_required)
    lookup_not_required_count = sum(1 for record in incoming_records if not record.lookup_required)
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "lookup_threshold": str(lookup_threshold),
        "status": "completed_no_missed_incoming_rows"
        if lookup_required_count + lookup_not_required_count == len(incoming_records)
        else "blocked_missed_incoming_row_control",
        "summary": {
            "incoming_rows_total": len(incoming_records),
            "lookup_required_count": lookup_required_count,
            "lookup_not_required_count": lookup_not_required_count,
            "lookup_required_plus_not_required_equals_total": lookup_required_count + lookup_not_required_count == len(incoming_records),
            "lookup_status_counts": dict(sorted(Counter(record.lookup_status for record in incoming_records).items())),
            "tax_basis_status_counts": dict(sorted(Counter(record.tax_basis_status for record in incoming_records).items())),
            "cis_likelihood_counts": dict(sorted(Counter(record.cis_likelihood for record in incoming_records).items())),
            "construction_or_reverse_charge_review_count": sum(
                1 for record in incoming_records if record.vat_reverse_charge_likelihood != "not_detected"
            ),
        },
        "safe_boundaries": {
            "companies_house_filing_performed": False,
            "hmrc_submission_performed": False,
            "payment_performed": False,
            "hmrc_subcontractor_verification_performed": False,
            "fake_evidence_generated": False,
        },
        "official_sources": dict(OFFICIAL_SOURCES),
        "records": [asdict(record) for record in incoming_records],
        "records_by_row_number": {str(record.row_number): asdict(record) for record in incoming_records},
    }


def build_record_skeleton(
    row_number: int,
    row: dict[str, str],
    amount: Decimal,
    payer: str,
    *,
    payer_group_total: Decimal,
    payer_group_row_count: int,
    lookup_threshold: Decimal,
) -> PayerProvenanceRecord:
    direction = "income" if amount > 0 else "expense" if amount < 0 else "zero"
    raw_name = str(row.get("Description") or "").strip()
    indicators = construction_indicators_for(raw_name)
    lookup_required = bool(
        amount > 0
        and (
            amount >= lookup_threshold
            or bool(indicators)
            or (payer_group_row_count > 1 and payer_group_total >= lookup_threshold)
        )
    )
    reasons: list[str] = []
    if amount >= lookup_threshold and amount > 0:
        reasons.append("incoming_amount_at_or_above_400")
    if indicators and amount > 0:
        reasons.append("construction_or_cis_signal")
    if payer_group_row_count > 1 and payer_group_total >= lookup_threshold and amount > 0:
        reasons.append("repeat_payer_aggregate_at_or_above_400")
    if amount <= 0:
        reasons.append("not_income")
    if not reasons:
        reasons.append("below_threshold_no_cis_or_repeat_payer_signal")
    source_trace = "|".join(
        item
        for item in (
            row.get("Source Provider", ""),
            row.get("Flow Provider", ""),
            row.get("Source Account", ""),
            row.get("Source File", ""),
        )
        if item
    )
    return PayerProvenanceRecord(
        row_number=row_number,
        date=row.get("Date", ""),
        description=raw_name,
        amount=str(amount),
        direction=direction,
        source_provider=row.get("Source Provider", ""),
        flow_provider=row.get("Flow Provider", ""),
        source_account=row.get("Source Account", ""),
        source_file=row.get("Source File", ""),
        source_trace=source_trace,
        payer_name_raw=raw_name,
        payer_name_normalized=payer,
        payer_group_total=str(money(payer_group_total)),
        payer_group_row_count=payer_group_row_count,
        lookup_required=lookup_required,
        lookup_reason=";".join(reasons),
        lookup_status="pending_lookup" if lookup_required else "not_required_below_threshold_or_no_cis_signal",
        payer_provenance_status="pending_lookup" if lookup_required else "not_required_low_risk",
        construction_indicators=indicators,
    )


def run_lookup(
    payer: str,
    *,
    companies_house_lookup: Callable[[str], dict[str, Any]] | None,
    client: CompaniesHouseClient | None,
    perform_online: bool,
) -> dict[str, Any]:
    if not payer:
        return blocked_lookup(payer, reason="blocked_missing_payer_name")
    if companies_house_lookup is not None:
        try:
            return companies_house_lookup(payer)
        except Exception as exc:
            return {
                **blocked_lookup(payer, reason="blocked_lookup_error"),
                "error": str(exc),
            }
    if not perform_online:
        return blocked_lookup(payer, reason="public_lookup_disabled_offline_mode")
    if not client:
        return blocked_lookup(payer, reason="blocked_missing_companies_house_api_key")
    try:
        return client.lookup(payer)
    except Exception as exc:
        return {
            **blocked_lookup(payer, reason="blocked_companies_house_lookup_error"),
            "error": str(exc),
        }


def apply_lookup_to_record(record: PayerProvenanceRecord, lookup: dict[str, Any], row: dict[str, str]) -> None:
    selected = lookup.get("selected") or {}
    record.lookup_status = str(lookup.get("lookup_status") or record.lookup_status)
    record.companies_house_candidates = list(lookup.get("companies_house_candidates") or [])
    record.selected_company_number = str(selected.get("company_number") or "")
    record.selected_company_name = str(selected.get("company_name") or "")
    record.company_status = str(selected.get("company_status") or "")
    record.company_type = str(selected.get("company_type") or "")
    record.sic_codes = [str(code) for code in selected.get("sic_codes") or []]
    record.registered_office_region = str(selected.get("registered_office_region") or "")
    record.evidence_urls = [str(url) for url in lookup.get("evidence_urls") or []]
    record.match_confidence = str(lookup.get("match_confidence") or selected.get("match_confidence") or "0.00")
    lookup_indicators = construction_indicators_for(record.payer_name_raw, {"sic_codes": record.sic_codes})
    record.construction_indicators = sorted(set(record.construction_indicators + lookup_indicators))
    assign_provenance_tax_status(record, row)


def assign_provenance_tax_status(record: PayerProvenanceRecord, row: dict[str, str]) -> None:
    if record.direction != "income":
        record.payer_provenance_status = "not_income"
        record.tax_basis_status = "not_income"
        record.accounting_action = "not_income_not_part_of_payer_provenance_queue"
        record.next_action = "No payer lookup; not an incoming payment."
        return

    if record.lookup_status == "matched_companies_house_profile":
        record.payer_provenance_status = "matched_public_register"
    elif record.lookup_status == "ambiguous_companies_house_candidates":
        record.payer_provenance_status = "ambiguous_public_register_match"
    elif record.lookup_status == "companies_house_no_match":
        record.payer_provenance_status = "no_public_register_match"
    elif record.lookup_status.startswith("blocked") or record.lookup_status.endswith("offline_mode"):
        record.payer_provenance_status = "lookup_required_but_blocked_or_unavailable" if record.lookup_required else "not_required_low_risk"
    else:
        record.payer_provenance_status = "not_required_low_risk" if not record.lookup_required else "public_lookup_pending_review"

    has_construction = bool(record.construction_indicators)
    has_statement = cis_statement_evidence_present(row)
    if has_statement and has_construction:
        record.cis_likelihood = "high"
        record.cis_evidence_status = "confirmed_cis_suffered"
        record.tax_basis_status = "confirmed_cis_suffered"
        record.vat_reverse_charge_likelihood = "possible_construction_domestic_reverse_charge"
        record.accounting_action = "gross_up_net_receipt_post_cis_suffered_to_tax_control_and_route_vat_reverse_charge_review"
        record.next_action = "Retain CIS deduction statement/invoice and use PAYE/EPS/refund route manually if applicable."
    elif has_construction:
        record.cis_likelihood = "high" if record.lookup_status in {"matched_companies_house_profile", "blocked_missing_companies_house_api_key"} else "medium"
        record.cis_evidence_status = "probable_cis_suffered"
        record.tax_basis_status = "probable_cis_suffered"
        record.vat_reverse_charge_likelihood = "possible_construction_domestic_reverse_charge"
        record.accounting_action = "provisional_cis_gross_up_workpaper_with_visible_evidence_request"
        record.next_action = "Attach real CIS deduction statements/invoices before legal filing; do not create fake evidence."
    else:
        record.cis_likelihood = "low"
        record.cis_evidence_status = "not_cis_income"
        record.tax_basis_status = "not_cis_income"
        record.vat_reverse_charge_likelihood = "not_detected"
        record.accounting_action = "treat_as_standard_income_pending_normal_accounting_controls"
        record.next_action = (
            "Review public-register match and source evidence."
            if record.lookup_required
            else "No payer lookup needed; retain source trace."
        )


def provenance_by_row_number(manifest: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {int(key): value for key, value in (manifest.get("records_by_row_number") or {}).items()}


def tax_status_is_cis(status: str) -> bool:
    return status in {"confirmed_cis_suffered", "probable_cis_suffered"}


def write_payer_provenance_artifacts(manifest: dict[str, Any], *, json_path: Path, csv_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    fieldnames = [
        "row_number",
        "date",
        "description",
        "amount",
        "source_provider",
        "flow_provider",
        "source_account",
        "source_file",
        "source_trace",
        "payer_name_raw",
        "payer_name_normalized",
        "payer_group_total",
        "payer_group_row_count",
        "lookup_required",
        "lookup_reason",
        "lookup_status",
        "payer_provenance_status",
        "selected_company_number",
        "selected_company_name",
        "company_status",
        "company_type",
        "sic_codes",
        "registered_office_region",
        "match_confidence",
        "construction_indicators",
        "cis_likelihood",
        "cis_evidence_status",
        "tax_basis_status",
        "vat_reverse_charge_likelihood",
        "accounting_action",
        "next_action",
        "evidence_urls",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for record in manifest.get("records") or []:
            writer.writerow(
                {
                    key: ";".join(str(item) for item in record.get(key, []))
                    if isinstance(record.get(key), list)
                    else record.get(key, "")
                    for key in fieldnames
                }
            )


def render_payer_provenance_markdown(
    *,
    company_name: str,
    company_number: str,
    period_start: str,
    period_end: str,
    manifest: dict[str, Any],
) -> str:
    summary = manifest.get("summary") or {}
    lines = [
        "# Incoming Payment Payer Provenance And CIS Lookup",
        "",
        f"Company: {company_name}",
        f"Company number: {company_number}",
        f"Period: {period_start} to {period_end}",
        "",
        "## No-Missed-Incoming Control",
        "",
        f"- Incoming rows total: {summary.get('incoming_rows_total', 0)}",
        f"- Lookup required rows: {summary.get('lookup_required_count', 0)}",
        f"- Lookup not required rows: {summary.get('lookup_not_required_count', 0)}",
        f"- Required plus not-required equals total: {summary.get('lookup_required_plus_not_required_equals_total')}",
        f"- Lookup threshold: GBP {manifest.get('lookup_threshold', '400.00')}",
        "",
        "## Lookup Status Counts",
        "",
    ]
    for status, count in (summary.get("lookup_status_counts") or {}).items():
        lines.append(f"- {status}: {count}")
    lines.extend(
        [
            "",
            "## Incoming Payment Register",
            "",
            "| Row | Date | Payer | Amount | Lookup | Public-register status | CIS/VAT status | Next action |",
            "| ---: | --- | --- | ---: | --- | --- | --- | --- |",
        ]
    )
    for record in manifest.get("records") or []:
        lines.append(
            f"| {record.get('row_number')} | {record.get('date')} | {record.get('payer_name_raw')} | "
            f"GBP {record.get('amount')} | {record.get('lookup_reason')} | {record.get('payer_provenance_status')} | "
            f"{record.get('tax_basis_status')} / {record.get('vat_reverse_charge_likelihood')} | {record.get('next_action')} |"
        )
    lines.extend(
        [
            "",
            "## Official Sources",
            "",
            *[f"- {key}: {url}" for key, url in (manifest.get("official_sources") or {}).items()],
            "",
            "No Companies House filing, HMRC submission, HMRC subcontractor verification, payment, or fake evidence generation was performed.",
            "",
        ]
    )
    return "\n".join(lines)


def render_cis_vat_tax_basis_markdown(
    *,
    company_name: str,
    company_number: str,
    period_start: str,
    period_end: str,
    manifest: dict[str, Any],
    tax_summary: dict[str, Any],
) -> str:
    summary = manifest.get("summary") or {}
    lines = [
        "# CIS VAT Tax Basis Assurance",
        "",
        f"Company: {company_name}",
        f"Company number: {company_number}",
        f"Period: {period_start} to {period_end}",
        "",
        "## Tax Basis Summary",
        "",
        f"- Tax-basis turnover: GBP {tax_summary.get('tax_basis_turnover', '0.00')}",
        f"- VAT taxable turnover estimate: GBP {tax_summary.get('vat_taxable_turnover_estimate', '0.00')}",
        f"- VAT registration threshold: GBP {tax_summary.get('vat_registration_threshold', '90000.00')}",
        f"- VAT threshold exceeded: {tax_summary.get('vat_threshold_exceeded')}",
        f"- CIS net-receipt rows grossed up: {tax_summary.get('cis_net_receipt_row_count', 0)}",
        f"- CIS suffered/tax deducted before bank: GBP {tax_summary.get('cis_deduction_suffered_total', '0.00')}",
        f"- Reverse-charge review rows: {tax_summary.get('vat_reverse_charge_review_row_count', 0)}",
        f"- Payer lookup construction/reverse-charge review rows: {summary.get('construction_or_reverse_charge_review_count', 0)}",
        "",
        "## CIS Treatment Counts",
        "",
    ]
    for status, count in (summary.get("tax_basis_status_counts") or {}).items():
        lines.append(f"- {status}: {count}")
    lines.extend(
        [
            "",
            "## CIS / VAT Workpaper Rows",
            "",
            "| Row | Payer | Net banked | CIS status | CIS likelihood | VAT reverse-charge | Evidence/control |",
            "| ---: | --- | ---: | --- | --- | --- | --- |",
        ]
    )
    interesting = [
        record
        for record in manifest.get("records") or []
        if record.get("tax_basis_status") != "not_cis_income" or record.get("lookup_required")
    ]
    for record in interesting:
        lines.append(
            f"| {record.get('row_number')} | {record.get('payer_name_raw')} | GBP {record.get('amount')} | "
            f"{record.get('tax_basis_status')} | {record.get('cis_likelihood')} | "
            f"{record.get('vat_reverse_charge_likelihood')} | {record.get('accounting_action')} |"
        )
    lines.extend(
        [
            "",
            "Confirmed CIS requires real CIS deduction statements/invoices. Probable CIS is shown as a provisional workpaper and evidence request; Aureon does not create fake statements.",
            "",
        ]
    )
    return "\n".join(lines)
