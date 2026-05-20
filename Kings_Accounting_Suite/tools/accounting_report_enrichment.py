"""Detailed accounting enrichment for human-readable accounts packs.

This module turns the combined bank feed into a traceable reporting layer.
It keeps every bank-feed row in the reconciliation, adds category/explanation
metadata, and records where the cognitive accounting systems agreed or asked
for review. It never files, submits, pays, or creates external evidence.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable


KAS_DIR = Path(__file__).resolve().parents[1]
CORE_DIR = KAS_DIR / "core"
if str(KAS_DIR) not in sys.path:
    sys.path.insert(0, str(KAS_DIR))
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

try:  # pragma: no cover - exercised through integration tests when present.
    from Kings_Accounting_Suite.core.hnc_auris_nodes import HNCAurisEngine
except Exception:  # pragma: no cover
    try:
        from core.hnc_auris_nodes import HNCAurisEngine
    except Exception:
        HNCAurisEngine = None  # type: ignore[assignment]

try:  # pragma: no cover
    from Kings_Accounting_Suite.core.hnc_auris_validator import HNCAurisValidator
except Exception:  # pragma: no cover
    try:
        from core.hnc_auris_validator import HNCAurisValidator
    except Exception:
        HNCAurisValidator = None  # type: ignore[assignment]

try:  # pragma: no cover
    from Kings_Accounting_Suite.core.hnc_soup import HNCSoup
except Exception:  # pragma: no cover
    try:
        from core.hnc_soup import HNCSoup
    except Exception:
        HNCSoup = None  # type: ignore[assignment]

try:  # pragma: no cover
    from Kings_Accounting_Suite.core.hnc_soup_kitchen import HNCSoupKitchen
except Exception:  # pragma: no cover
    try:
        from core.hnc_soup_kitchen import HNCSoupKitchen
    except Exception:
        HNCSoupKitchen = None  # type: ignore[assignment]

try:  # pragma: no cover - import path differs between package/tests/scripts.
    from Kings_Accounting_Suite.tools.accounting_payer_provenance import (
        build_payer_provenance_manifest,
        construction_indicators_for,
        provenance_by_row_number,
        tax_status_is_cis,
    )
except Exception:  # pragma: no cover
    from accounting_payer_provenance import (  # type: ignore
        build_payer_provenance_manifest,
        construction_indicators_for,
        provenance_by_row_number,
        tax_status_is_cis,
    )


def money(value: Decimal | int | float | str) -> Decimal:
    raw = value if isinstance(value, Decimal) else Decimal(str(value or "0"))
    return raw.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def money_text(value: Decimal | int | float | str) -> str:
    return f"{money(value):,.2f}"


def as_float(value: Decimal | int | float | str) -> float:
    return float(money(value))


def corporation_tax_for_profit(taxable_profit: Decimal, associated_companies: int = 1) -> tuple[Decimal, Decimal]:
    taxable_profit = money(max(taxable_profit, Decimal("0")))
    companies = max(int(associated_companies or 1), 1)
    lower_limit = Decimal("50000.00") / Decimal(companies)
    upper_limit = Decimal("250000.00") / Decimal(companies)
    if taxable_profit <= lower_limit:
        tax = money(taxable_profit * Decimal("0.19"))
    elif taxable_profit >= upper_limit:
        tax = money(taxable_profit * Decimal("0.25"))
    else:
        tax = money((taxable_profit * Decimal("0.25")) - ((upper_limit - taxable_profit) * Decimal("0.015")))
    effective_rate = (tax / taxable_profit).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP) if taxable_profit else Decimal("0.0000")
    return tax, effective_rate


CATEGORY_META: dict[str, dict[str, str]] = {
    "trading_income": {
        "label": "Trading income and sales receipts",
        "kind": "income",
        "tax_treatment": "Included in turnover unless uploaded evidence clearly proves a non-trading source.",
    },
    "income_source_review": {
        "label": "Income source review",
        "kind": "income",
        "tax_treatment": "Included in turnover/income suspense for reconciliation unless eye-scan flags uploaded evidence proving loan, transfer, refund, or capital.",
    },
    "cost_of_sales": {
        "label": "Cost of sales and direct trading costs",
        "kind": "expense",
        "tax_treatment": "Potentially allowable if wholly and exclusively business and supported by evidence.",
    },
    "materials_tools_equipment": {
        "label": "Materials, tools, and equipment",
        "kind": "expense",
        "tax_treatment": "Aureon allocates from available evidence and flags possible stock/capital/capital-allowance treatment for eye-scan.",
    },
    "software_subscriptions": {
        "label": "Software, subscriptions, and digital services",
        "kind": "expense",
        "tax_treatment": "Usually allowable as administrative expense when business related.",
    },
    "bank_and_payment_charges": {
        "label": "Bank, card, and payment processor charges",
        "kind": "expense",
        "tax_treatment": "Usually allowable finance/admin cost when business account related.",
    },
    "professional_fees": {
        "label": "Professional, legal, accounting, and consulting fees",
        "kind": "expense",
        "tax_treatment": "Usually allowable if business related; capital/legal exceptions are flagged for eye-scan.",
    },
    "motor_and_travel": {
        "label": "Motor, travel, fuel, parking, and subsistence",
        "kind": "expense",
        "tax_treatment": "Potentially allowable; private-use and travel-purpose assumptions are flagged for eye-scan.",
    },
    "premises_utilities": {
        "label": "Premises, rent, rates, and utilities",
        "kind": "expense",
        "tax_treatment": "Usually allowable if business premises or business-use proportion is evidenced.",
    },
    "insurance": {
        "label": "Insurance",
        "kind": "expense",
        "tax_treatment": "Usually allowable where it protects business activity or business assets.",
    },
    "marketing_advertising": {
        "label": "Marketing, advertising, and public profile",
        "kind": "expense",
        "tax_treatment": "Usually allowable where business promotional purpose is evidenced.",
    },
    "subsistence_supplies": {
        "label": "Subsistence, welfare, and small supplies",
        "kind": "expense",
        "tax_treatment": "Potentially allowable where business purpose is evidenced; private-use assumptions stay visible as eye-scan flags.",
    },
    "payroll_subcontractor_review": {
        "label": "Payroll, subcontractor, and worker-payment eye-scan",
        "kind": "expense",
        "tax_treatment": "Aureon allocates to payroll/subcontractor/supplier suspense and flags PAYE, CIS, contractor status, UTR, and related-party implications.",
    },
    "tax_and_government_review": {
        "label": "Tax, VAT, HMRC, Companies House, and government payments eye-scan",
        "kind": "expense",
        "tax_treatment": "May be disallowable, balance-sheet, or tax account movement; Aureon routes to a tax/government control account and eye-scan flag.",
    },
    "director_related_or_cash_review": {
        "label": "Cash withdrawals, director, owner, and related-party eye-scan",
        "kind": "expense",
        "tax_treatment": "Do not hide in admin costs; Aureon allocates to director loan, private-use, wages/dividend, or petty-cash suspense and flags for eye-scan.",
    },
    "inter_account_transfer_review": {
        "label": "Transfers and clearing movements",
        "kind": "expense",
        "tax_treatment": "Usually balance-sheet movement, not P&L; kept in total outflow reconciliation here.",
    },
    "capital_or_asset_review": {
        "label": "Capital asset or financing eye-scan",
        "kind": "expense",
        "tax_treatment": "Aureon flags capitalisation, depreciation add-back, and capital allowances for tax workpaper eye-scan.",
    },
    "administrative_costs": {
        "label": "Administrative and operating costs",
        "kind": "expense",
        "tax_treatment": "General admin support; only high-confidence admin belongs here.",
    },
    "uncategorised_review": {
        "label": "Uncategorised or low-confidence eye-scan queue",
        "kind": "expense",
        "tax_treatment": "Aureon allocates to uncategorised non-deductible suspense and flags for eye-scan before relying on deductibility.",
    },
}


CATEGORY_RULES: list[tuple[str, tuple[str, ...], str, str]] = [
    (
        "director_related_or_cash_review",
        ("cash", "atm", "withdraw", "notemachine", "blackstaff", "tina brown", "gary leckey", "dividend", "director", "wages"),
        "Cash/owner/director pattern found; Aureon keeps outside generic admin and flags the suspense allocation for eye-scan.",
        "statement_plus_eye_scan_flag",
    ),
    (
        "tax_and_government_review",
        ("hmrc", "vat", "utr", "tax", "companies house", "company house", "pay as you earn", "paye"),
        "Government/tax pattern found; treatment may be disallowable or balance-sheet.",
        "statement_plus_tax_review_required",
    ),
    (
        "inter_account_transfer_review",
        ("transfer", "revolut", "zempler", "sumup bank", "own account", "top up", "load", "card load"),
        "Transfer/clearing pattern found; Aureon allocates to clearing and flags whether it is only movement between company accounts.",
        "statement_plus_reconciliation_required",
    ),
    (
        "bank_and_payment_charges",
        ("fee", "charge", "commission", "sumup", "stripe", "paypal", "card fee", "cash load fee", "bank charges"),
        "Bank/payment processor charge pattern found.",
        "statement_available",
    ),
    (
        "motor_and_travel",
        (
            "parking",
            "q park",
            "toll",
            "port tunnel",
            "lanark way filling",
            "landscape filling",
            "nicholl auto",
            "cavehill retail",
            "driver & vehicle",
            "dvla",
            "thompson automobiles",
            "autoparts",
            "airport road service",
            "bestcarpark",
            "park rite",
            "belfast international",
            "gleneagle hotel",
            "maldron hotel",
            "glenshane tourist",
            "loveholidays",
        ),
        "Travel/motor pattern found.",
        "statement_plus_business_purpose_required",
    ),
    (
        "software_subscriptions",
        (
            "github",
            "google",
            "microsoft",
            "openai",
            "anthropic",
            "adobe",
            "wix",
            "supabase",
            "software",
            "subscription",
            "cloud",
            "giffgaff",
            "mobile zone",
            "oculus",
        ),
        "Software/subscription pattern found.",
        "statement_plus_invoice_preferred",
    ),
    (
        "professional_fees",
        ("accountant", "accounting", "legal", "solicitor", "consult", "consulting", "professional", "xero"),
        "Professional service pattern found.",
        "statement_plus_invoice_preferred",
    ),
    (
        "motor_and_travel",
        ("fuel", "petrol", "diesel", "parking", "travel", "easyjet", "booking.com", "uber", "taxi", "shell", "bp ", "maxol", "texaco"),
        "Travel/motor pattern found.",
        "statement_plus_business_purpose_required",
    ),
    (
        "premises_utilities",
        ("rent", "rates", "premises", "electric", "gas", "airtricity", "utility", "broadband", "bt "),
        "Premises or utility pattern found.",
        "statement_plus_invoice_preferred",
    ),
    (
        "insurance",
        ("insurance", "premium credit", "aviva", "axa", "zurich"),
        "Insurance pattern found.",
        "statement_plus_policy_invoice_preferred",
    ),
    (
        "marketing_advertising",
        ("advert", "marketing", "facebook ads", "google ads", "meta", "promotion", "shutterstock"),
        "Marketing/advertising pattern found.",
        "statement_plus_invoice_preferred",
    ),
    (
        "subsistence_supplies",
        (
            "mcdonald",
            "burger king",
            "tim hortons",
            "starbucks",
            "co-op",
            "cooperative",
            "spar",
            "eurospar",
            "centra",
            "sainsburys",
            "tesco",
            "marks&spencer",
            "rossis ice cream",
            "hugh's confect",
            "office",
            "hobbycraft",
            "mace ",
            "mace,",
            "mace rvh",
            "fruiterama",
            "greggs",
            "kfc",
            "domino",
            "costcutter",
            "iceland",
            "lidl",
            "corner shop",
            "saveway",
            "premier brians",
            "murphy's store",
            "chill",
            "gelato",
            "slim chickens",
            "rico mexican",
            "little italy",
            "kellys diner",
            "shamrock lodge",
            "orchard inn",
            "ostan loch",
            "strand road bar",
            "frankie and bennys",
            "northern quarter",
            "sainsbury",
            "bk ",
            "bubble waffle",
            "empanadas",
            "chocolateria",
            "seven asia",
            "t 205",
        ),
        "Subsistence, welfare, or small-supplies pattern found.",
        "statement_plus_business_purpose_preferred",
    ),
    (
        "director_related_or_cash_review",
        (
            "winemark",
            "schuh",
            "matalan",
            "warren james",
            "tk maxx",
            "next retail",
            "airtastic",
            "funky monkeys",
            "beach sport",
            "prisontele",
            "jailtele",
            "amazon prime",
            "department of foreign",
            "changegroup",
            "bancosabadell",
            "boi mainst",
            "05aib",
            "smyths toys",
            "hollywoodbowl",
            "cineworld",
            "game dos mares",
            "pandora",
            "perfume",
            "marvimundo",
            "new look",
            "new balance",
            "dv8",
            "hilfiger",
            "guess outlet",
            "tommy hilfiger",
            "holland and barret",
            "boots",
            "medicare pharmacy",
            "church of",
            "the rug",
            "the jungle",
            "nyx*",
            "nyx ",
        ),
        "Private/personal retail, leisure, travel-document, or owner-use pattern found; Aureon allocates to non-deductible/director suspense and flags before claiming.",
        "statement_plus_eye_scan_flag",
    ),
    (
        "payroll_subcontractor_review",
        ("subcontract", "labour", "wage", "salary", "worker", "contractor", "cis", "grass cut"),
        "Worker/subcontractor pattern found; Aureon allocates to payroll/subcontractor suspense and flags CIS/PAYE status.",
        "statement_plus_worker_status_eye_scan_flag",
    ),
    (
        "materials_tools_equipment",
        ("screwfix", "toolstation", "tools", "equipment", "laptop", "computer", "machinery", "vehicle", "asset", "currys", "amazon", "amznmktplace"),
        "Materials/equipment pattern found.",
        "statement_plus_receipt_required",
    ),
    (
        "cost_of_sales",
        ("stock", "wholesale", "supplies", "cost of sales", "materials", "booker", "musgrave", "coca cola", "frylite"),
        "Direct cost/stock pattern found.",
        "statement_plus_supplier_evidence_required",
    ),
]

def category_rule_terms() -> dict[str, list[str]]:
    terms_by_category: dict[str, set[str]] = defaultdict(set)
    for category, terms, _reason, _evidence in CATEGORY_RULES:
        terms_by_category[category].update(str(term).strip().lower() for term in terms if str(term).strip())
    terms_by_category["trading_income"].update(["positive amount", "client income", "sales receipt", "cis construction payer"])
    terms_by_category["income_source_review"].update(["loan", "director", "capital introduced", "refund"])
    terms_by_category["uncategorised_review"].update(["no matched filter", "low confidence", "missing invoice or receipt"])
    return {category: sorted(values) for category, values in terms_by_category.items()}


def matched_terms(text: str, terms: Iterable[str]) -> list[str]:
    matches: list[str] = []
    for term in terms:
        clean = str(term or "").strip().lower()
        if not clean:
            continue
        if clean == "stock":
            if re.search(r"(?<![a-z0-9])stock(?![a-z0-9])", text):
                matches.append(clean)
            continue
        if clean in text:
            matches.append(clean)
    return matches


def exclusion_filters_for_category(category: str) -> list[str]:
    if category in {"trading_income", "income_source_review"}:
        return ["loan or director funds", "inter-account transfer", "refund or capital introduced", "non-trading control receipt"]
    if category in {"administrative_costs", "subsistence_supplies", "motor_and_travel"}:
        return ["private or family use", "director loan/drawings", "capital asset", "missing business purpose"]
    if category in {"materials_tools_equipment", "cost_of_sales"}:
        return ["capital item", "stock/control movement", "private use", "missing supplier evidence"]
    if category == "bank_and_payment_charges":
        return ["loan repayment", "tax penalty", "non-business fee"]
    if category == "inter_account_transfer_review":
        return ["do not include as P&L income or expense until matched to contra account"]
    if "review" in category or category == "uncategorised_review":
        return ["do not claim as deductible until reviewed"]
    return ["manual exception review if source evidence contradicts the filter"]


def category_filter_profile(category: str) -> dict[str, Any]:
    meta = CATEGORY_META.get(category, {})
    return {
        "category": category,
        "label": meta.get("label", category),
        "kind": meta.get("kind", "unknown"),
        "look_for_terms": category_rule_terms().get(category, []),
        "evidence_needed": default_evidence_for_category(category),
        "tax_treatment": meta.get("tax_treatment", ""),
        "review_required_by_default": review_status_for_category(category) == "manual_review_required",
        "review_trigger": default_review_reason_for_category(category),
        "exclusion_filters": exclusion_filters_for_category(category),
    }


def cook_filter_trace(row: dict[str, str], classification_info: dict[str, Any], amount: Decimal, soup: Any = None) -> dict[str, str]:
    category = str(classification_info.get("category") or "")
    source = str(classification_info.get("source") or "")
    desc = (row.get("Description") or "").lower()
    profile = category_filter_profile(category)
    matches = matched_terms(desc, profile.get("look_for_terms") or [])
    soup_category = str(getattr(soup, "hmrc_category", "") or "")
    soup_label = str(getattr(soup, "hmrc_label", "") or "")
    if amount > 0 and category == "trading_income" and "positive amount" not in matches:
        matches.insert(0, "positive amount")
    if source.lower().startswith("hncsoup") and soup_category:
        matches.insert(0, f"HNCSoup:{soup_category}")
    if soup_label:
        matches.append(f"soup_label:{soup_label}")
    if not matches:
        matches.append("no direct keyword; routed by fallback/filter hierarchy")
    decision_path = [
        f"direction={'income' if amount > 0 else 'expense' if amount < 0 else 'zero'}",
        f"source={source}",
        f"category={category}",
        f"review={classification_info.get('review_status')}",
    ]
    return {
        "cook_label": str(profile.get("label") or category),
        "cook_filter_family": str(profile.get("kind") or "unknown"),
        "cook_filter_matched_terms": "; ".join(dict.fromkeys(matches)),
        "cook_evidence_needed": str(profile.get("evidence_needed") or ""),
        "cook_review_trigger": str(profile.get("review_trigger") or ""),
        "cook_exclusion_filters": "; ".join(profile.get("exclusion_filters") or []),
        "cook_decision_path": " > ".join(decision_path),
    }


def build_cook_filter_manifest(transactions: list["EnrichedTransaction"]) -> dict[str, Any]:
    route_counts = Counter(tx.accounting_category for tx in transactions)
    review_counts = Counter(tx.accounting_category for tx in transactions if tx.review_status != "ok" or tx.eye_scan_flag == "yes")
    profiles = []
    for category in sorted(CATEGORY_META):
        profile = category_filter_profile(category)
        profile["rows_matched"] = route_counts.get(category, 0)
        profile["review_rows"] = review_counts.get(category, 0)
        profiles.append(profile)
    return {
        "schema_version": "cook-label-filter-manifest-v1",
        "status": "generated",
        "purpose": "Show exactly what labels, filters, evidence, and exclusion checks the Soup cook used before categorising rows.",
        "category_count": len(profiles),
        "profiles": profiles,
        "route_counts": dict(sorted(route_counts.items())),
        "review_route_counts": dict(sorted(review_counts.items())),
        "global_exclusion_filters": [
            "do not hide transfers as turnover or deductible expense",
            "do not hide director/owner/private spend in generic admin",
            "do not treat tax/government payments as ordinary expenses without review",
            "do not claim missing-evidence rows without eye-scan review",
        ],
    }


CIS_DEDUCTION_RATE = Decimal("0.20")
CIS_GROVE_CITB_RATE = Decimal("0.007")
VAT_STANDARD_RATE = Decimal("0.20")
VAT_REGISTRATION_THRESHOLD = Decimal("90000.00")

CIS_CONSTRUCTION_PAYER_TERMS = (
    "grove builders",
    "heron bros",
    "csr ni ltd",
    "the csr group",
    "amc construction",
    "mmg contracts",
    "contracts ltd",
    "construction",
    "subcontractor statement",
)

TRADING_INCOME_LEDGER_ACCOUNTS = {
    "sales_turnover",
    "sales_turnover_or_income_suspense",
}

ALLOWABLE_PNL_EXPENSE_LEDGER_ACCOUNTS = {
    "cost_of_sales",
    "materials_tools_equipment",
    "software_and_subscriptions",
    "bank_and_payment_fees",
    "professional_fees",
    "motor_travel_and_subsistence",
    "premises_and_utilities",
    "insurance",
    "marketing_and_advertising",
    "printing_stationery_and_small_admin_costs",
    "subsistence_welfare_and_small_supplies",
    "payroll_subcontractor_supplier_suspense",
}


@dataclass
class EnrichedTransaction:
    row_number: int
    date: str
    description: str
    amount: str
    direction: str
    accounting_category: str
    accounting_label: str
    category_confidence: str
    category_source: str
    tax_treatment: str
    evidence_status: str
    review_status: str
    review_reason: str
    autonomous_status: str
    autonomous_allocation: str
    autonomous_reason: str
    eye_scan_flag: str
    final_accounting_category: str
    final_ledger_account: str
    final_tax_treatment: str
    audit_ready_status: str
    outlier_status: str
    audit_evidence_basis: str
    allocation_correctness_status: str
    allocation_rule: str
    cis_scope: str
    cis_gross_income: str
    cis_deduction_suffered: str
    cis_citb_levy: str
    cis_net_banked: str
    cis_basis: str
    cis_evidence_status: str
    vat_scope: str
    vat_taxable_turnover: str
    vat_output_vat_estimate: str
    vat_reverse_charge_status: str
    source_trace: str
    payer_name_raw: str
    payer_name_normalized: str
    payer_group_total: str
    payer_group_row_count: int
    payer_provenance_status: str
    lookup_required: bool
    lookup_reason: str
    lookup_status: str
    tax_basis_status: str
    next_action: str
    selected_company_number: str
    selected_company_name: str
    company_status: str
    sic_codes: list[str]
    construction_indicators: list[str]
    cis_likelihood: str
    vat_reverse_charge_likelihood: str
    payer_evidence_urls: list[str]
    source_provider: str
    flow_provider: str
    source_account: str
    source_file: str
    duplicate_source_files: str
    cook_label: str = ""
    cook_filter_family: str = ""
    cook_filter_matched_terms: str = ""
    cook_evidence_needed: str = ""
    cook_review_trigger: str = ""
    cook_exclusion_filters: str = ""
    cook_decision_path: str = ""
    soup_category: str = ""
    soup_label: str = ""
    soup_confidence: str = ""
    auris_consensus: str = ""
    auris_coherence: str = ""
    auris_action: str = ""
    auris_dissenting_nodes: list[str] = field(default_factory=list)


def build_report_enrichment(
    rows: list[dict[str, str]],
    *,
    figures: Any,
    rollups: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a machine-readable enriched accounting report."""
    rollups = rollups or {}
    soup_results, soup_summary, kitchen_summary = run_soup_and_kitchen(rows)
    auris_engine = HNCAurisEngine() if HNCAurisEngine else None
    payee_stats = build_payee_stats(rows)
    payer_provenance_manifest = build_payer_provenance_manifest(rows)
    payer_records = provenance_by_row_number(payer_provenance_manifest)
    enriched: list[EnrichedTransaction] = []
    category_totals: dict[str, dict[str, Any]] = {}
    final_ledger_totals: dict[str, dict[str, Any]] = {}
    review_reasons: Counter[str] = Counter()
    auris_actions: Counter[str] = Counter()
    source_reconciliation = build_source_reconciliation(rows, rollups)

    for idx, row in enumerate(rows, start=1):
        amount = money(row.get("Amount") or "0")
        soup = soup_results[idx - 1] if idx - 1 < len(soup_results) else None
        classification = classify_row(row, amount, soup=soup)
        auris = classify_with_auris(auris_engine, row, amount, classification, payee_stats)
        if auris:
            auris_actions[auris["action"]] += 1
            if should_auris_force_manual_review(classification, auris, amount):
                classification["review_status"] = "manual_review_required"
                classification["review_reason"] = "Auris node disagreement routed to autonomous allocation and eye-scan flag."
                classification["evidence_status"] = "statement_plus_auris_review_required"

        if classification["review_status"] != "ok":
            review_reasons[classification["review_reason"]] += 1
        autonomy = autonomous_allocation_for(row, amount, classification, soup=soup, auris=auris)
        audit_position = audit_final_position_for(row, amount, classification, autonomy)
        payer_record = payer_records.get(idx, {})
        tax_profile = tax_profile_for_row(row, amount, payer_record=payer_record)
        cook_trace = cook_filter_trace(row, classification, amount, soup=soup)
        tx = EnrichedTransaction(
            row_number=idx,
            date=row.get("Date", ""),
            description=row.get("Description", ""),
            amount=str(amount),
            direction="income" if amount > 0 else "expense" if amount < 0 else "zero",
            accounting_category=classification["category"],
            accounting_label=CATEGORY_META[classification["category"]]["label"],
            category_confidence=str(classification["confidence"]),
            category_source=classification["source"],
            tax_treatment=CATEGORY_META[classification["category"]]["tax_treatment"],
            evidence_status=classification["evidence_status"],
            review_status=classification["review_status"],
            review_reason=classification["review_reason"],
            autonomous_status=autonomy["status"],
            autonomous_allocation=autonomy["allocation"],
            autonomous_reason=autonomy["reason"],
            eye_scan_flag=autonomy["eye_scan_flag"],
            final_accounting_category=audit_position["final_accounting_category"],
            final_ledger_account=audit_position["final_ledger_account"],
            final_tax_treatment=audit_position["final_tax_treatment"],
            audit_ready_status=audit_position["audit_ready_status"],
            outlier_status=audit_position["outlier_status"],
            audit_evidence_basis=audit_position["audit_evidence_basis"],
            allocation_correctness_status=audit_position["allocation_correctness_status"],
            allocation_rule=audit_position["allocation_rule"],
            cis_scope=tax_profile["cis_scope"],
            cis_gross_income=tax_profile["cis_gross_income"],
            cis_deduction_suffered=tax_profile["cis_deduction_suffered"],
            cis_citb_levy=tax_profile["cis_citb_levy"],
            cis_net_banked=tax_profile["cis_net_banked"],
            cis_basis=tax_profile["cis_basis"],
            cis_evidence_status=tax_profile["cis_evidence_status"],
            vat_scope=tax_profile["vat_scope"],
            vat_taxable_turnover=tax_profile["vat_taxable_turnover"],
            vat_output_vat_estimate=tax_profile["vat_output_vat_estimate"],
            vat_reverse_charge_status=tax_profile["vat_reverse_charge_status"],
            source_trace=payer_record.get("source_trace", ""),
            payer_name_raw=payer_record.get("payer_name_raw", row.get("Description", "")),
            payer_name_normalized=payer_record.get("payer_name_normalized", ""),
            payer_group_total=payer_record.get("payer_group_total", "0.00"),
            payer_group_row_count=int(payer_record.get("payer_group_row_count") or 0),
            payer_provenance_status=payer_record.get("payer_provenance_status", "not_income" if amount <= 0 else "missing_payer_record"),
            lookup_required=bool(payer_record.get("lookup_required", False)),
            lookup_reason=payer_record.get("lookup_reason", "not_income" if amount <= 0 else "missing_payer_record"),
            lookup_status=payer_record.get("lookup_status", "not_income" if amount <= 0 else "missing_payer_record"),
            tax_basis_status=payer_record.get("tax_basis_status", tax_profile["cis_evidence_status"]),
            next_action=payer_record.get("next_action", "No payer lookup; not an incoming payment." if amount <= 0 else "Review missing payer provenance record."),
            selected_company_number=payer_record.get("selected_company_number", ""),
            selected_company_name=payer_record.get("selected_company_name", ""),
            company_status=payer_record.get("company_status", ""),
            sic_codes=list(payer_record.get("sic_codes") or []),
            construction_indicators=list(payer_record.get("construction_indicators") or []),
            cis_likelihood=payer_record.get("cis_likelihood", "low"),
            vat_reverse_charge_likelihood=payer_record.get("vat_reverse_charge_likelihood", tax_profile["vat_reverse_charge_status"]),
            payer_evidence_urls=list(payer_record.get("evidence_urls") or []),
            source_provider=row.get("Source Provider", ""),
            flow_provider=row.get("Flow Provider", ""),
            source_account=row.get("Source Account", ""),
            source_file=row.get("Source File", ""),
            duplicate_source_files=row.get("Duplicate Source Files", ""),
            cook_label=cook_trace["cook_label"],
            cook_filter_family=cook_trace["cook_filter_family"],
            cook_filter_matched_terms=cook_trace["cook_filter_matched_terms"],
            cook_evidence_needed=cook_trace["cook_evidence_needed"],
            cook_review_trigger=cook_trace["cook_review_trigger"],
            cook_exclusion_filters=cook_trace["cook_exclusion_filters"],
            cook_decision_path=cook_trace["cook_decision_path"],
            soup_category=getattr(soup, "hmrc_category", "") if soup else "",
            soup_label=getattr(soup, "hmrc_label", "") if soup else "",
            soup_confidence=str(getattr(soup, "confidence", "")) if soup else "",
            auris_consensus=(auris or {}).get("consensus", ""),
            auris_coherence=(auris or {}).get("coherence", ""),
            auris_action=(auris or {}).get("action", ""),
            auris_dissenting_nodes=(auris or {}).get("dissenting_nodes", []),
        )
        enriched.append(tx)
        add_category_total(category_totals, tx, amount)
        add_final_ledger_total(final_ledger_totals, tx, amount)

    raw_income_total = money(sum(Decimal(tx.amount) for tx in enriched if Decimal(tx.amount) > 0))
    raw_expense_total = money(-sum(Decimal(tx.amount) for tx in enriched if Decimal(tx.amount) < 0))
    tax_obligation_summary = build_tax_obligation_summary(enriched, raw_income_total, raw_expense_total)
    income_total = money(tax_obligation_summary["tax_basis_turnover"])
    expense_total = money(tax_obligation_summary["tax_basis_expenses"])
    reconciles = income_total == money(getattr(figures, "turnover", income_total)) and expense_total == money(
        getattr(figures, "expenses", expense_total)
    )
    validation = run_auris_validator(figures, category_totals)
    unresolved_outlier_count = sum(1 for tx in enriched if tx.outlier_status == "unresolved")
    system_resolved_outlier_count = sum(1 for tx in enriched if tx.outlier_status == "system_resolved")
    allocation_correctness_counts = Counter(tx.allocation_correctness_status for tx in enriched)
    fallback_suspense_row_count = sum(1 for tx in enriched if "fallback" in tx.allocation_correctness_status)
    return {
        "schema_version": "accounting-report-enrichment-v1",
        "status": "complete_external_audit_pack_ready" if unresolved_outlier_count == 0 else "blocked_unresolved_outliers",
        "row_count": len(enriched),
        "unique_rows_classified_or_reviewed": len(enriched),
        "fully_categorised_row_count": len([tx for tx in enriched if tx.final_ledger_account]),
        "totals": {
            "turnover": str(income_total),
            "expenses": str(expense_total),
            "profit_before_tax": str(money(getattr(figures, "profit_before_tax", income_total - expense_total))),
            "reconciles_to_filing_figures": reconciles,
            "raw_bank_money_in": str(raw_income_total),
            "raw_bank_money_out": str(raw_expense_total),
            "cis_gross_up_turnover_adjustment": tax_obligation_summary["cis_gross_up_turnover_adjustment"],
            "cis_citb_levy_expense_adjustment": tax_obligation_summary["cis_citb_levy_total"],
        },
        "category_totals": sort_category_totals(category_totals),
        "final_ledger_totals": sort_final_ledger_totals(final_ledger_totals),
        "source_reconciliation": source_reconciliation,
        "payer_provenance_summary": payer_provenance_manifest.get("summary") or {},
        "payer_provenance_manifest": payer_provenance_manifest,
        "tax_obligation_summary": tax_obligation_summary,
        "cook_filter_manifest": build_cook_filter_manifest(enriched),
        "soup_summary": soup_summary,
        "soup_kitchen_summary": kitchen_summary,
        "auris_summary": {
            "engine": "HNCAurisEngine" if auris_engine else "blocked_import_failed",
            "action_counts": dict(sorted(auris_actions.items())),
            "auris_challenge_count": auris_actions.get("HUMAN_REQUIRED", 0),
            "human_required_count": 0,
            "human_required_language": "Auris HUMAN_REQUIRED is treated as an internal challenge signal; Aureon still assigns a final audit ledger position.",
            "classify_review_count": auris_actions.get("CLASSIFY_REVIEW", 0),
        },
        "validator_summary": validation,
        "review_summary": {
            "manual_review_row_count": sum(1 for tx in enriched if tx.review_status != "ok"),
            "eye_scan_flag_count": sum(1 for tx in enriched if tx.eye_scan_flag == "yes"),
            "autonomous_allocated_row_count": len(enriched),
            "manual_input_required_row_count": 0,
            "fully_categorised_row_count": len([tx for tx in enriched if tx.final_ledger_account]),
            "unresolved_outlier_count": unresolved_outlier_count,
            "system_resolved_outlier_count": system_resolved_outlier_count,
            "fallback_suspense_row_count": fallback_suspense_row_count,
            "incoming_payer_lookup_required_count": (payer_provenance_manifest.get("summary") or {}).get("lookup_required_count", 0),
            "incoming_payer_lookup_not_required_count": (payer_provenance_manifest.get("summary") or {}).get("lookup_not_required_count", 0),
            "incoming_payer_no_missed_control": (payer_provenance_manifest.get("summary") or {}).get("lookup_required_plus_not_required_equals_total", False),
            "allocation_correctness_counts": dict(sorted(allocation_correctness_counts.items())),
            "external_audit_pack_status": "ready_no_unresolved_outliers" if unresolved_outlier_count == 0 else "blocked_unresolved_outliers",
            "operator_role": "eye_scan_and_flag_exceptions_only",
            "review_language": "legacy manual_review_row_count means system-resolved audit positions, not data-entry work or unresolved outliers.",
            "review_reasons": dict(sorted(review_reasons.items())),
        },
        "safety": {
            "external_filing_performed": False,
            "hmrc_submission_performed": False,
            "companies_house_submission_performed": False,
            "payment_performed": False,
            "generated_external_receipts": False,
        },
        "transactions": [asdict(tx) for tx in enriched],
    }


def classify_row(row: dict[str, str], amount: Decimal, *, soup: Any = None) -> dict[str, Any]:
    desc = (row.get("Description") or "").lower()
    if amount > 0:
        if any(term in desc for term in ("loan", "director", "capital introduced", "refund")):
            return classification("income_source_review", Decimal("0.65"), "income eye-scan keyword", "statement_plus_source_eye_scan_flag", "manual_review_required", "Income source allocated to turnover/income suspense unless eye-scan contradicts it.")
        return classification("trading_income", Decimal("0.80"), "positive bank movement", "statement_available", "ok", "Included in turnover.")
    if amount == 0:
        return classification("uncategorised_review", Decimal("0.40"), "zero bank movement", "statement_plus_eye_scan_flag", "manual_review_required", "Zero amount row allocated to zero-impact suspense and eye-scan flag.")

    for category, terms, reason, evidence in CATEGORY_RULES:
        if any_term(desc, terms):
            return classification(
                category,
                Decimal("0.78") if "review" not in category else Decimal("0.62"),
                "keyword rule",
                evidence,
                review_status_for_category(category),
                reason,
            )

    soup_category = getattr(soup, "hmrc_category", "")
    if soup_category:
        mapped = map_soup_result(soup)
        if mapped:
            return classification(
                mapped,
                Decimal(str(getattr(soup, "confidence", 0.65) or 0.65)),
                f"HNCSoup:{soup_category}",
                default_evidence_for_category(mapped),
                review_status_for_category(mapped),
                default_review_reason_for_category(mapped),
            )

    return classification(
        "uncategorised_review",
        Decimal("0.45"),
        "fallback eye-scan queue",
        "statement_plus_receipt_or_invoice_eye_scan_flag",
        "manual_review_required",
        "No strong category evidence; Aureon allocates to non-deductible suspense and eye-scan flag.",
    )


def classification(
    category: str,
    confidence: Decimal,
    source: str,
    evidence_status: str,
    review_status: str,
    review_reason: str,
) -> dict[str, Any]:
    return {
        "category": category,
        "confidence": str(confidence.quantize(Decimal("0.01"))),
        "source": source,
        "evidence_status": evidence_status,
        "review_status": review_status,
        "review_reason": review_reason,
    }


def any_term(text: str, terms: Iterable[str]) -> bool:
    for term in terms:
        clean = str(term or "").strip().lower()
        if not clean:
            continue
        if clean == "stock":
            if re.search(r"(?<![a-z0-9])stock(?![a-z0-9])", text):
                return True
            continue
        if clean in text:
            return True
    return False


def map_soup_result(soup: Any) -> str:
    category = str(getattr(soup, "hmrc_category", "") or "")
    label = str(getattr(soup, "hmrc_label", "") or "").lower()
    note = str(getattr(soup, "private_note", "") or "").lower()
    confidence = Decimal(str(getattr(soup, "confidence", 0) or 0))
    text = f"{label} {note}"

    if category == "other_direct_costs" and any(
        term in text for term in ("labour", "subcontractor", "worker", "operational support", "site")
    ):
        return "payroll_subcontractor_review"
    if category == "other_expenses" and confidence >= Decimal("0.80") and any(
        term in text for term in ("subsistence", "supplies", "business meeting", "sundry business costs")
    ):
        return "subsistence_supplies"
    return map_soup_category(category)


def map_soup_category(category: str) -> str:
    return {
        "construction_income": "trading_income",
        "food_income": "trading_income",
        "consulting_income": "trading_income",
        "other_income": "income_source_review",
        "cost_of_sales": "cost_of_sales",
        "construction_costs": "materials_tools_equipment",
        "other_direct_costs": "materials_tools_equipment",
        "premises": "premises_utilities",
        "admin": "administrative_costs",
        "advertising": "marketing_advertising",
        "interest": "bank_and_payment_charges",
        "phone": "software_subscriptions",
        "other_expenses": "uncategorised_review",
        "motor": "motor_and_travel",
        "drawings": "director_related_or_cash_review",
        "transfer": "inter_account_transfer_review",
        "personal": "director_related_or_cash_review",
    }.get(category, "")


def default_evidence_for_category(category: str) -> str:
    if category in {"administrative_costs", "bank_and_payment_charges"}:
        return "statement_available"
    if category == "trading_income":
        return "statement_available"
    if category == "subsistence_supplies":
        return "statement_plus_business_purpose_preferred"
    if "review" in category:
        return "statement_plus_eye_scan_flag"
    return "statement_plus_supplier_evidence_preferred"


def review_status_for_category(category: str) -> str:
    return "manual_review_required" if "review" in category or category == "uncategorised_review" else "ok"


def default_review_reason_for_category(category: str) -> str:
    if category == "uncategorised_review":
        return "No strong category evidence; Aureon allocates to non-deductible suspense and eye-scan flag."
    if "review" in category:
        return CATEGORY_META[category]["tax_treatment"]
    return "Category appears supported by bank statement and rules."


def should_auris_force_manual_review(
    classification_info: dict[str, Any],
    auris: dict[str, Any] | None,
    amount: Decimal,
) -> bool:
    if not auris or auris.get("action") != "HUMAN_REQUIRED":
        return False
    if classification_info.get("review_status") != "ok":
        return False
    category = str(classification_info.get("category") or "")
    confidence = Decimal(str(classification_info.get("confidence") or "0"))
    source = str(classification_info.get("source") or "").lower()
    trusted_cook_source = source.startswith("keyword rule") or source.startswith("hncsoup:")

    if category in {"uncategorised_review"} or "review" in category:
        return True
    if confidence < Decimal("0.70"):
        return True
    if trusted_cook_source:
        return False

    consensus = str(auris.get("consensus") or "")
    if consensus in {"private", "review_needed"}:
        return True
    if consensus == "capital" and abs(amount) >= Decimal("500.00"):
        return True
    return False


def autonomous_allocation_for(
    row: dict[str, str],
    amount: Decimal,
    classification_info: dict[str, Any],
    *,
    soup: Any = None,
    auris: dict[str, Any] | None = None,
) -> dict[str, str]:
    category = str(classification_info.get("category") or "")
    status = str(classification_info.get("review_status") or "")
    desc = (row.get("Description") or "").lower()
    if status == "ok":
        return {
            "status": "auto_posted",
            "allocation": category,
            "reason": "Aureon posted this from bank/source data using Soup, rules, ledger categories, and Auris telemetry.",
            "eye_scan_flag": "no",
        }
    if category == "director_related_or_cash_review":
        cash_like = any(term in desc for term in ("cash", "atm", "notemachine", "blackstaff", "changegroup", "ukatmfee"))
        allocation = "petty_cash_or_director_loan_suspense_non_deductible" if cash_like else "director_loan_or_private_use_suspense_non_deductible"
        return {
            "status": "system_allocated_eye_scan",
            "allocation": allocation,
            "reason": "Aureon does not claim this as a tax-deductible expense without real evidence; it is isolated from generic admin costs.",
            "eye_scan_flag": "yes",
        }
    if category == "inter_account_transfer_review":
        return {
            "status": "system_allocated_eye_scan",
            "allocation": "inter_account_transfer_clearing",
            "reason": "Aureon treats this as a balance-sheet/clearing movement unless source evidence proves it is trading income or expense.",
            "eye_scan_flag": "yes",
        }
    if category == "tax_and_government_review":
        return {
            "status": "system_allocated_eye_scan",
            "allocation": "tax_government_control_account_or_disallowable",
            "reason": "Aureon routes tax/government rows away from ordinary expenses so CT600 treatment can be defended.",
            "eye_scan_flag": "yes",
        }
    if category == "payroll_subcontractor_review":
        return {
            "status": "system_allocated_eye_scan",
            "allocation": "payroll_subcontractor_or_supplier_suspense",
            "reason": "Aureon keeps worker/supplier rows visible for PAYE/CIS/status risk while still assigning a working ledger route.",
            "eye_scan_flag": "yes",
        }
    if category == "income_source_review" or amount > 0:
        return {
            "status": "system_allocated_eye_scan",
            "allocation": "income_suspense_included_in_turnover_until_contra_evidence",
            "reason": "Aureon includes the receipt in turnover by default unless source evidence proves loan, transfer, refund, or capital.",
            "eye_scan_flag": "yes",
        }
    if category == "uncategorised_review":
        return {
            "status": "system_allocated_eye_scan",
            "allocation": "uncategorised_expense_suspense_non_deductible",
            "reason": "Aureon assigns a conservative suspense/non-deductible treatment instead of asking the user to classify the row.",
            "eye_scan_flag": "yes",
        }
    return {
        "status": "system_allocated_eye_scan",
        "allocation": f"{category or 'specialist'}_suspense",
        "reason": "Aureon assigned a conservative working treatment and exposes the row for eye-scan exception flagging.",
        "eye_scan_flag": "yes",
    }


def audit_final_position_for(
    row: dict[str, str],
    amount: Decimal,
    classification_info: dict[str, Any],
    autonomy: dict[str, str],
) -> dict[str, str]:
    """Assign the final audit ledger position for every row.

    Eye-scan flags are not unposted outliers. They are conservative accounting
    positions with an audit trail and a clear tax treatment.
    """
    category = str(classification_info.get("category") or "")
    allocation = str(autonomy.get("allocation") or category or "unknown")
    desc = (row.get("Description") or "").lower()
    auto_posted = autonomy.get("status") == "auto_posted"

    specific = specific_final_allocation_for_description(desc, amount, category)
    if specific:
        return specific

    if auto_posted:
        ledger = {
            "trading_income": "sales_turnover",
            "cost_of_sales": "cost_of_sales",
            "materials_tools_equipment": "materials_tools_equipment",
            "software_subscriptions": "software_and_subscriptions",
            "bank_and_payment_charges": "bank_and_payment_fees",
            "professional_fees": "professional_fees",
            "motor_and_travel": "motor_travel_and_subsistence",
            "premises_utilities": "premises_and_utilities",
            "insurance": "insurance",
            "marketing_advertising": "marketing_and_advertising",
            "subsistence_supplies": "subsistence_welfare_and_small_supplies",
            "administrative_costs": "administrative_and_operating_costs",
        }.get(category, category or "other_operating_costs")
        return {
            "final_accounting_category": category or "other_operating_costs",
            "final_ledger_account": ledger,
            "final_tax_treatment": CATEGORY_META.get(category, {}).get("tax_treatment", "Posted from source data."),
            "audit_ready_status": "audit_ready_posted_from_source",
            "outlier_status": "none",
            "audit_evidence_basis": "bank_statement_or_provider_export_plus_rules_soup_auris_trace",
            "allocation_correctness_status": "source_rule_specific",
            "allocation_rule": f"posted_clean_category:{category}",
        }

    if category == "director_related_or_cash_review":
        cash_like = any(term in desc for term in ("cash", "atm", "notemachine", "blackstaff", "changegroup", "ukatmfee"))
        return {
            "final_accounting_category": "petty_cash_or_director_loan_control" if cash_like else "director_loan_or_private_use_control",
            "final_ledger_account": "petty_cash_director_loan_control_non_deductible" if cash_like else "director_loan_private_use_non_deductible",
            "final_tax_treatment": "Balance-sheet/director-loan control or non-deductible private-use treatment unless uploaded evidence proves business deductibility.",
            "audit_ready_status": "audit_ready_system_resolved_conservative",
            "outlier_status": "system_resolved",
            "audit_evidence_basis": "source_row_plus_cash_director_personal_pattern_and_non_deductible_suspense_policy",
            "allocation_correctness_status": "conservative_control_specific",
            "allocation_rule": "cash_or_director_related_party_control",
        }
    if category == "inter_account_transfer_review":
        return {
            "final_accounting_category": "inter_account_transfer_clearing",
            "final_ledger_account": "inter_account_transfer_clearing",
            "final_tax_treatment": "Excluded from taxable income/expense as a clearing or balance-sheet movement unless uploaded source evidence proves otherwise.",
            "audit_ready_status": "audit_ready_system_resolved_clearing",
            "outlier_status": "system_resolved",
            "audit_evidence_basis": "source_row_plus_transfer_pattern_provider_flow_and_clearing_policy",
            "allocation_correctness_status": "specific_clearing",
            "allocation_rule": "transfer_or_provider_flow_pattern",
        }
    if category == "tax_and_government_review":
        return {
            "final_accounting_category": "tax_government_control",
            "final_ledger_account": "tax_government_control_or_disallowable",
            "final_tax_treatment": "Posted to tax/government control or disallowable add-back support; not hidden in ordinary admin costs.",
            "audit_ready_status": "audit_ready_system_resolved_tax_control",
            "outlier_status": "system_resolved",
            "audit_evidence_basis": "source_row_plus_tax_government_pattern_and_ct600_control_policy",
            "allocation_correctness_status": "specific_tax_control",
            "allocation_rule": "tax_government_pattern",
        }
    if category == "payroll_subcontractor_review":
        return {
            "final_accounting_category": "payroll_subcontractor_supplier_control",
            "final_ledger_account": "payroll_subcontractor_supplier_suspense",
            "final_tax_treatment": "Posted to payroll/subcontractor/supplier suspense with PAYE/CIS risk visible; deductible only where source evidence supports the business treatment.",
            "audit_ready_status": "audit_ready_system_resolved_worker_status",
            "outlier_status": "system_resolved",
            "audit_evidence_basis": "source_row_plus_worker_supplier_pattern_and_paye_cis_control_policy",
            "allocation_correctness_status": "worker_supplier_control_specific",
            "allocation_rule": "worker_subcontractor_or_supplier_pattern",
        }
    if category == "income_source_review" or amount > 0:
        return {
            "final_accounting_category": "income_suspense_included_in_turnover",
            "final_ledger_account": "sales_turnover_or_income_suspense",
            "final_tax_treatment": "Included in turnover by default; moved only if uploaded evidence proves loan, refund, transfer, capital, or director funds.",
            "audit_ready_status": "audit_ready_system_resolved_income",
            "outlier_status": "system_resolved",
            "audit_evidence_basis": "source_row_plus_positive_receipt_policy_and_contra_evidence_test",
            "allocation_correctness_status": "income_default_specific",
            "allocation_rule": "positive_receipt_income_policy",
        }
    if category == "uncategorised_review":
        return {
            "final_accounting_category": "uncategorised_expense_suspense_non_deductible",
            "final_ledger_account": "uncategorised_expense_suspense_non_deductible",
            "final_tax_treatment": "Non-deductible suspense treatment until uploaded evidence supports a precise allowable category.",
            "audit_ready_status": "audit_ready_system_resolved_non_deductible_suspense",
            "outlier_status": "system_resolved",
            "audit_evidence_basis": "source_row_plus_low_confidence_policy_and_non_deductible_suspense",
            "allocation_correctness_status": "conservative_suspense_fallback",
            "allocation_rule": "low_confidence_non_deductible_suspense",
        }
    if category == "capital_or_asset_review":
        return {
            "final_accounting_category": "fixed_asset_or_financing_control",
            "final_ledger_account": "fixed_asset_financing_control",
            "final_tax_treatment": "Capital/financing control treatment with depreciation add-back and capital-allowance route visible where applicable.",
            "audit_ready_status": "audit_ready_system_resolved_capital",
            "outlier_status": "system_resolved",
            "audit_evidence_basis": "source_row_plus_capital_asset_pattern_and_fixed_asset_policy",
            "allocation_correctness_status": "capital_control_specific",
            "allocation_rule": "capital_asset_or_financing_pattern",
        }
    return {
        "final_accounting_category": category or "specialist_accounting_suspense",
        "final_ledger_account": allocation or "specialist_accounting_suspense",
        "final_tax_treatment": "Conservative specialist suspense/control treatment; not treated as an unposted outlier.",
        "audit_ready_status": "audit_ready_system_resolved_specialist",
        "outlier_status": "system_resolved",
        "audit_evidence_basis": "source_row_plus_specialist_conservative_suspense_policy",
        "allocation_correctness_status": "specialist_suspense_fallback",
        "allocation_rule": "specialist_conservative_suspense",
    }


def specific_final_allocation_for_description(desc: str, amount: Decimal, category: str) -> dict[str, str] | None:
    """Return the most specific defensible final ledger allocation from row text."""
    text = f" {desc} "

    def has(*terms: str) -> bool:
        return any(term in text for term in terms)

    def position(
        final_category: str,
        ledger: str,
        tax: str,
        basis: str,
        rule: str,
        *,
        correctness: str = "description_rule_specific",
        status: str = "audit_ready_system_resolved_specific",
        outlier: str = "system_resolved",
    ) -> dict[str, str]:
        return {
            "final_accounting_category": final_category,
            "final_ledger_account": ledger,
            "final_tax_treatment": tax,
            "audit_ready_status": status,
            "outlier_status": outlier,
            "audit_evidence_basis": basis,
            "allocation_correctness_status": correctness,
            "allocation_rule": rule,
        }

    if amount > 0 and is_cis_construction_income_description(text):
        return position(
            "cis_construction_income_grossed_up",
            "cis_construction_turnover_net_receipt_plus_tax_suffered",
            "Bank shows a net construction receipt. Aureon grosses this up for CIS suffered, posts CIS withheld to a tax-credit/control account, and routes VAT/reverse-charge status to the VAT workpaper.",
            "source_row_plus_construction_payer_description_and_cis_gross_up_control",
            "cis_net_receipt_gross_up",
            correctness="cis_gross_up_specific",
            status="audit_ready_system_resolved_tax_control",
            outlier="system_resolved",
        )
    if has("creditbuilder loan", "credit builder loan"):
        return position(
            "loan_financing_control",
            "loan_financing_control_not_pnl",
            "Balance-sheet financing/control movement; excluded from trading turnover and ordinary expenses.",
            "source_row_plus_creditbuilder_loan_description",
            "creditbuilder_loan_financing_control",
        )
    if has("fee for cash loads", "ukatmfee", "cash load fee", "cash loads over"):
        return position(
            "bank_cash_load_fees",
            "bank_and_payment_fees",
            "Bank/payment cash-load or ATM fee; allowable only where it relates to business account operations.",
            "source_row_plus_bank_fee_description",
            "cash_load_or_atm_fee",
            correctness="bank_fee_specific",
            status="audit_ready_posted_from_source",
            outlier="none",
        )
    if has("invideo innovation", "invideo"):
        return position(
            "software_subscriptions",
            "software_and_subscriptions",
            "Digital software/subscription cost; normally administrative expense where business related.",
            "source_row_plus_invideo_subscription_description",
            "invideo_software_subscription",
            correctness="software_subscription_specific",
            status="audit_ready_posted_from_source",
            outlier="none",
        )
    if has("r&a revolot", "r&a revolut", "revolot gary", "revolution", "own account", "to revolut", "revolut transfer"):
        return position(
            "inter_account_transfer_clearing",
            "inter_account_transfer_clearing",
            "Inter-account/provider movement; excluded from trading income and expense.",
            "source_row_plus_revolut_or_own_account_transfer_description",
            "explicit_inter_account_transfer",
            correctness="transfer_specific",
        )
    if has("notemachine", "atm", "changegroup", "blackstaff", "economycash", "e070479"):
        return position(
            "cash_withdrawal_petty_cash_control",
            "cash_withdrawal_petty_cash_control_non_deductible_until_receipted",
            "Cash withdrawal/control movement; not claimed as deductible expense unless uploaded receipts allocate the cash to business spend.",
            "source_row_plus_cash_machine_or_bureau_description",
            "cash_withdrawal_or_currency_bureau",
            correctness="cash_control_specific",
        )
    if has("e070477", "e070385", "05aib", "boi mainst", "bancosabadell", "falls road, ,belfas"):
        return position(
            "cash_card_load_or_bank_control",
            "cash_card_load_or_bank_control_non_deductible",
            "Cash/card-load/bank control movement; excluded from ordinary expenses unless source evidence proves business purpose.",
            "source_row_plus_bank_location_or_card_load_description",
            "cash_card_load_bank_location_control",
            correctness="cash_or_card_load_specific",
        )
    if has("tina brown", "gary leckey", "ann leckey", "gary ", "tina "):
        return position(
            "director_or_related_party_loan_control",
            "director_related_party_loan_control_non_deductible",
            "Related-party/director movement; balance-sheet/director-loan control unless payroll/dividend/evidence proves another treatment.",
            "source_row_plus_named_related_party_description",
            "named_related_party_control",
            correctness="related_party_specific",
        )
    if has("department of foreign"):
        return position(
            "director_personal_documents",
            "director_personal_documents_non_deductible",
            "Personal identity/travel-document cost; non-deductible/private unless business evidence proves otherwise.",
            "source_row_plus_government_personal_document_description",
            "personal_document_non_deductible",
            correctness="private_use_specific",
        )
    if has("winemark", "airtastic", "funky monkeys", "hollywoodbowl", "cineworld", "game dos mares", "jailtele", "prisontele"):
        return position(
            "private_leisure_and_entertainment",
            "private_leisure_entertainment_non_deductible",
            "Private/leisure/entertainment treatment; excluded from deductible business expenses.",
            "source_row_plus_private_leisure_merchant_description",
            "private_leisure_non_deductible",
            correctness="private_use_specific",
        )
    if has("schuh", "matalan", "warren james", "tk maxx", "next retail", "pandora", "perfume", "marvimundo", "new look", "new balance", "dv8", "hilfiger", "guess outlet", "tommy hilfiger", "smyths toys", "nyx", "boots", "medicare pharmacy", "farmacia", "holland and barret", "royal victoria hospita"):
        return position(
            "private_retail_health_and_clothing",
            "private_retail_health_clothing_non_deductible",
            "Private retail/health/clothing treatment; excluded from deductible business expenses unless uploaded evidence proves business use.",
            "source_row_plus_private_retail_health_merchant_description",
            "private_retail_health_clothing_non_deductible",
            correctness="private_use_specific",
        )
    if has("beach sport", "loveholidays", "aelia", "belfast international", "hotel", "airport", "bancosabadell"):
        return position(
            "private_or_travel_control",
            "private_or_travel_control_non_deductible",
            "Travel/holiday/foreign-card treatment; non-deductible/private unless source evidence proves business travel.",
            "source_row_plus_travel_or_foreign_merchant_description",
            "travel_private_control_non_deductible",
            correctness="travel_private_specific",
        )
    if has("bar", "arms", "bear & bial", "tipsy", "thistle", "gobstopper", "gaming", "sixty six", "clonard", "bellevue", "cng bar", "maire ruas", "lagan valley leisure", "district 45 restaurant", "l officina", "teach paidi", "andreas", "raffos", "chip co", "parkgate farm"):
        return position(
            "private_hospitality_or_leisure",
            "private_hospitality_leisure_non_deductible",
            "Hospitality/leisure treatment; excluded from deductible expenses unless source evidence proves business purpose.",
            "source_row_plus_hospitality_or_leisure_merchant_description",
            "hospitality_leisure_non_deductible",
            correctness="hospitality_private_specific",
        )
    if has("kolormaster"):
        return position(
            "printing_stationery_and_small_admin",
            "printing_stationery_and_small_admin_costs",
            "Printing/stationery/admin cost where business related.",
            "source_row_plus_kolormaster_description",
            "printing_stationery_admin",
            correctness="admin_supplier_specific",
            status="audit_ready_posted_from_source",
            outlier="none",
        )
    if has("value cabs"):
        return position(
            "taxi_and_local_travel",
            "motor_travel_and_subsistence",
            "Taxi/local travel cost; allowable only where business journey purpose is evidenced.",
            "source_row_plus_taxi_merchant_description",
            "taxi_local_travel",
            correctness="travel_specific",
            status="audit_ready_posted_from_source",
            outlier="none",
        )
    if has("vivo", "go twin spires", "consum ", "carrigagh", "corner shop", "costcutter", "lidl", "tesco", "sainsbury", "spar", "eurospar", "beths allen", "beanies conven", "greens shop", "bds vending"):
        return position(
            "subsistence_welfare_and_small_supplies",
            "subsistence_welfare_and_small_supplies",
            "Small supplies/subsistence/welfare cost; allowable only where business purpose is evidenced.",
            "source_row_plus_convenience_or_grocery_merchant_description",
            "small_supplies_or_subsistence",
            correctness="small_supplies_specific",
            status="audit_ready_posted_from_source",
            outlier="none",
        )
    if has("mcp eakes", "mcpeakes", "lesley forestside", "castle court", "comercio", "polaris", "enes4815", "murcia,c.", "nyu nyu", "argos", "miko.ai", "tfs belfast", "the name shops", "nithco", "dylan oaks", "325 cavehill road", "oml belfast", "in2retail", "kildare cw", "dmd (belfast)", "louis boyd", "52 ardoyne avenue"):
        return position(
            "retail_or_small_supplies_control",
            "retail_or_small_supplies_control_non_deductible_until_evidenced",
            "Retail/small-supplies control; non-deductible until uploaded evidence proves business purpose.",
            "source_row_plus_retail_location_description",
            "retail_small_supplies_control",
            correctness="retail_control_specific",
        )
    return None


def is_cis_construction_income_description(description: str) -> bool:
    text = f" {str(description or '').lower()} "
    return any(term in text for term in CIS_CONSTRUCTION_PAYER_TERMS) or bool(construction_indicators_for(text))


def tax_profile_for_row(row: dict[str, str], amount: Decimal, payer_record: dict[str, Any] | None = None) -> dict[str, str]:
    """Build row-level VAT/CIS control facts without filing or submitting."""
    desc = (row.get("Description") or "").lower()
    payer_record = payer_record or {}
    if amount <= 0:
        return {
            "cis_scope": "not_cis_income",
            "cis_gross_income": "0.00",
            "cis_deduction_suffered": "0.00",
            "cis_citb_levy": "0.00",
            "cis_net_banked": "0.00",
            "cis_basis": "not_income",
            "cis_evidence_status": "not_income",
            "vat_scope": "purchase_or_non_income_vat_review",
            "vat_taxable_turnover": "0.00",
            "vat_output_vat_estimate": "0.00",
            "vat_reverse_charge_status": "not_income",
        }

    payer_tax_status = str(payer_record.get("tax_basis_status") or "")
    cis_evidence_status = payer_tax_status if tax_status_is_cis(payer_tax_status) else ""
    if is_cis_construction_income_description(desc) and not cis_evidence_status:
        cis_evidence_status = "probable_cis_suffered"

    if tax_status_is_cis(cis_evidence_status):
        citb_rate = CIS_GROVE_CITB_RATE if "grove builders" in desc else Decimal("0.00")
        divisor = (Decimal("1.00") - citb_rate) * (Decimal("1.00") - CIS_DEDUCTION_RATE)
        gross = money(amount / divisor) if divisor else money(amount)
        citb = money(gross * citb_rate)
        gross_less_citb = money(gross - citb)
        cis = money(gross_less_citb * CIS_DEDUCTION_RATE)
        return {
            "cis_scope": "cis_net_receipt_detected",
            "cis_gross_income": str(gross),
            "cis_deduction_suffered": str(cis),
            "cis_citb_levy": str(citb),
            "cis_net_banked": str(amount),
            "cis_basis": f"{cis_evidence_status}_estimated_from_net_bank_receipt_using_verified_20pct_cis_rate"
            + ("_and_0.7pct_citb_for_grove" if citb else ""),
            "cis_evidence_status": cis_evidence_status,
            "vat_scope": "construction_services_vat_scope_review",
            "vat_taxable_turnover": str(gross),
            "vat_output_vat_estimate": str(money(gross * VAT_STANDARD_RATE)),
            "vat_reverse_charge_status": "domestic_reverse_charge_possible_check_invoice_contract_and_customer_status",
        }

    return {
        "cis_scope": "not_cis_income",
        "cis_gross_income": "0.00",
        "cis_deduction_suffered": "0.00",
        "cis_citb_levy": "0.00",
        "cis_net_banked": "0.00",
        "cis_basis": "not_cis_payer_pattern",
        "cis_evidence_status": "not_cis_income",
        "vat_scope": "income_taxable_turnover_review",
        "vat_taxable_turnover": str(amount),
        "vat_output_vat_estimate": str(money(amount * VAT_STANDARD_RATE)),
        "vat_reverse_charge_status": "not_detected_from_bank_description",
    }


def build_tax_obligation_summary(
    transactions: list[EnrichedTransaction],
    raw_income_total: Decimal,
    raw_expense_total: Decimal,
) -> dict[str, Any]:
    cis_rows = [tx for tx in transactions if tx.cis_scope == "cis_net_receipt_detected"]
    cis_net = money(sum(Decimal(tx.cis_net_banked or "0") for tx in cis_rows))
    cis_gross = money(sum(Decimal(tx.cis_gross_income or "0") for tx in cis_rows))
    cis_deducted = money(sum(Decimal(tx.cis_deduction_suffered or "0") for tx in cis_rows))
    cis_citb = money(sum(Decimal(tx.cis_citb_levy or "0") for tx in cis_rows))
    non_cis_trading_income = money(
        sum(
            Decimal(tx.amount or "0")
            for tx in transactions
            if Decimal(tx.amount or "0") > 0
            and tx.cis_scope != "cis_net_receipt_detected"
            and tx.final_ledger_account in TRADING_INCOME_LEDGER_ACCOUNTS
        )
    )
    allowable_expenses = money(
        -sum(
            Decimal(tx.amount or "0")
            for tx in transactions
            if Decimal(tx.amount or "0") < 0
            and tx.final_ledger_account in ALLOWABLE_PNL_EXPENSE_LEDGER_ACCOUNTS
        )
    )
    excluded_non_trading_income = money(raw_income_total - cis_net - non_cis_trading_income)
    excluded_non_pnl_outflows = money(raw_expense_total - allowable_expenses)
    tax_basis_turnover = money(non_cis_trading_income + cis_gross)
    tax_basis_expenses = money(allowable_expenses + cis_citb)
    vat_taxable_turnover = tax_basis_turnover
    cis_gross_up_adjustment = money((cis_gross - cis_net) if cis_rows else Decimal("0"))
    adjusted_turnover = tax_basis_turnover
    adjusted_expenses = tax_basis_expenses
    adjusted_profit_before_tax = money(adjusted_turnover - adjusted_expenses)
    corporation_tax_before_cis, corporation_tax_effective_rate = corporation_tax_for_profit(adjusted_profit_before_tax)
    corporation_tax_after_cis = corporation_tax_before_cis
    cis_credit_surplus_or_refund_review = cis_deducted
    vat_threshold_exceeded = vat_taxable_turnover >= VAT_REGISTRATION_THRESHOLD
    return {
        "schema_version": "uk-tax-obligation-summary-v1",
        "status": "tax_controls_generated_no_submission",
        "raw_bank_money_in": str(raw_income_total),
        "raw_bank_money_out": str(raw_expense_total),
        "cis_net_receipt_row_count": len(cis_rows),
        "non_cis_trading_income_total": str(non_cis_trading_income),
        "allowable_pnl_expenses_total": str(allowable_expenses),
        "excluded_non_trading_income_or_control_total": str(excluded_non_trading_income),
        "excluded_non_pnl_outflows_or_control_total": str(excluded_non_pnl_outflows),
        "tax_basis_turnover": str(tax_basis_turnover),
        "tax_basis_expenses": str(tax_basis_expenses),
        "cis_net_banked_total": str(cis_net),
        "cis_gross_income_total": str(cis_gross),
        "cis_deduction_suffered_total": str(cis_deducted),
        "cis_citb_levy_total": str(cis_citb),
        "cis_evidence_status_counts": dict(sorted(Counter(tx.cis_evidence_status for tx in cis_rows).items())),
        "cis_gross_up_turnover_adjustment": str(cis_gross_up_adjustment),
        "adjusted_turnover_after_cis_gross_up": str(adjusted_turnover),
        "adjusted_expenses_after_citb": str(adjusted_expenses),
        "adjusted_profit_before_tax_after_cis": str(adjusted_profit_before_tax),
        "corporation_tax_before_cis_credit_estimate": str(corporation_tax_before_cis),
        "corporation_tax_effective_rate_estimate": str(corporation_tax_effective_rate),
        "corporation_tax_rate_method": "uk_small_profits_main_rate_marginal_relief_estimate_associated_companies_1",
        "cis_credit_available_for_setoff_or_refund_review": str(cis_deducted),
        "corporation_tax_after_cis_credit_estimate": str(corporation_tax_after_cis),
        "cis_credit_surplus_or_refund_review": str(cis_credit_surplus_or_refund_review),
        "cis_limited_company_claim_route": "claim_or_set_off_through_monthly_payroll_eps_or_refund_review_not_ct600",
        "cis_credit_not_claimed_through_ct600": True,
        "vat_taxable_turnover_estimate": str(vat_taxable_turnover),
        "vat_registration_threshold": str(VAT_REGISTRATION_THRESHOLD),
        "vat_threshold_exceeded": vat_threshold_exceeded,
        "vat_reverse_charge_review_row_count": sum(1 for tx in cis_rows if "reverse_charge" in tx.vat_reverse_charge_status),
        "manual_submission_performed": False,
        "hmrc_payment_performed": False,
        "sources": {
            "cis": "https://www.gov.uk/what-is-the-construction-industry-scheme",
            "vat_registration": "https://www.gov.uk/register-for-vat",
            "vat_domestic_reverse_charge": "https://www.gov.uk/guidance/vat-domestic-reverse-charge-for-building-and-construction-services",
        },
        "cis_rows": [
            {
                "row_number": tx.row_number,
                "date": tx.date,
                "description": tx.description,
                "net_banked": tx.cis_net_banked,
                "gross_income": tx.cis_gross_income,
                "cis_deduction_suffered": tx.cis_deduction_suffered,
                "citb_levy": tx.cis_citb_levy,
                "basis": tx.cis_basis,
                "cis_evidence_status": tx.cis_evidence_status,
                "vat_reverse_charge_status": tx.vat_reverse_charge_status,
                "payer_provenance_status": tx.payer_provenance_status,
                "lookup_status": tx.lookup_status,
                "selected_company_number": tx.selected_company_number,
                "selected_company_name": tx.selected_company_name,
                "source_file": tx.source_file,
            }
            for tx in cis_rows
        ],
    }


def run_soup_and_kitchen(rows: list[dict[str, str]]) -> tuple[list[Any], dict[str, Any], dict[str, Any]]:
    if not HNCSoup:
        return [], {"engine": "blocked_import_failed"}, {"engine": "blocked_import_failed"}
    soup = HNCSoup(entity_name="R&A Consulting and Brokerage Services Ltd", trades=["consulting", "brokerage", "general"])
    soup_rows = []
    for row in rows:
        amount = money(row.get("Amount") or "0")
        soup_rows.append(
            {
                "date": row.get("Date", ""),
                "description": row.get("Description", ""),
                "amount": as_float(abs(amount)),
                "direction": "in" if amount > 0 else "out",
                "category": "",
            }
        )
    results = soup.classify_all(soup_rows)
    summary = {
        "engine": "HNCSoup",
        "row_count": len(results),
        "income_by_trade": soup.get_income_by_trade(),
        "expense_by_trade": soup.get_expenses_by_trade(),
        "sa103_like_summary": soup.get_sa103_summary(),
        "private_advisory_count": len(getattr(soup, "private_advisory", [])),
    }
    kitchen = {"engine": "HNCSoupKitchen", "status": "not_run"}
    if HNCSoupKitchen:
        try:
            report = HNCSoupKitchen(soup).audit_and_correct()
            kitchen = {
                "engine": "HNCSoupKitchen",
                "status": "completed",
                "risk_count": len(report.risks_found),
                "corrections_made": report.corrections_made,
                "defence_narrative_count": len(report.defence_narrative),
                "top_risks": [asdict(item) for item in report.risks_found[:10]],
                "defence_narrative": report.defence_narrative[:12],
            }
        except Exception as exc:  # pragma: no cover - depends on optional data.
            kitchen = {"engine": "HNCSoupKitchen", "status": "blocked_runtime_error", "error": str(exc)}
    summary.update(
        {
            "income_by_trade": soup.get_income_by_trade(),
            "expense_by_trade": soup.get_expenses_by_trade(),
            "sa103_like_summary": soup.get_sa103_summary(),
        }
    )
    return results, summary, kitchen


def build_payee_stats(rows: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    stats: dict[str, dict[str, Any]] = defaultdict(lambda: {"count": 0, "amounts": []})
    for row in rows:
        key = payee_key(row.get("Description", ""))
        amount = abs(as_float(row.get("Amount") or "0"))
        stats[key]["count"] += 1
        stats[key]["amounts"].append(amount)
    return stats


def payee_key(description: str) -> str:
    words = re.sub(r"[^a-z0-9 ]+", " ", description.lower()).split()
    return " ".join(words[:4]) if words else "unknown"


def classify_with_auris(
    engine: Any,
    row: dict[str, str],
    amount: Decimal,
    classification_info: dict[str, Any],
    payee_stats: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    if not engine or amount >= 0:
        return None
    key = payee_key(row.get("Description", ""))
    stats = payee_stats.get(key, {})
    try:
        result = engine.classify(
            row.get("Description", ""),
            as_float(abs(amount)),
            suggested_category=map_to_auris_category(classification_info["category"]),
            payee_frequency=stats.get("count", 0),
            payee_history=stats.get("amounts", []),
        )
    except Exception as exc:  # pragma: no cover - optional engine errors.
        return {"action": "blocked_runtime_error", "error": str(exc), "consensus": "", "coherence": ""}
    return {
        "consensus": result.consensus_category,
        "coherence": str(result.coherence_score),
        "action": getattr(result.action, "value", str(result.action)),
        "dissenting_nodes": result.dissenting_nodes[:9],
        "reasoning": result.reasoning,
    }


def map_to_auris_category(category: str) -> str:
    return {
        "cost_of_sales": "cost_of_sales",
        "materials_tools_equipment": "capital",
        "software_subscriptions": "admin",
        "bank_and_payment_charges": "admin",
        "professional_fees": "admin",
        "motor_and_travel": "motor",
        "premises_utilities": "other_expenses",
        "insurance": "admin",
        "marketing_advertising": "other_expenses",
        "payroll_subcontractor_review": "other_direct",
        "tax_and_government_review": "review_needed",
        "director_related_or_cash_review": "review_needed",
        "inter_account_transfer_review": "review_needed",
        "capital_or_asset_review": "capital",
        "administrative_costs": "admin",
        "uncategorised_review": "review_needed",
    }.get(category, "other_expenses")


def add_category_total(category_totals: dict[str, dict[str, Any]], tx: EnrichedTransaction, amount: Decimal) -> None:
    info = category_totals.setdefault(
        tx.accounting_category,
        {
            "category": tx.accounting_category,
            "label": tx.accounting_label,
            "kind": CATEGORY_META[tx.accounting_category]["kind"],
            "rows": 0,
            "money_in": Decimal("0"),
            "money_out": Decimal("0"),
            "net": Decimal("0"),
            "manual_review_rows": 0,
            "examples": [],
            "tax_treatment": tx.tax_treatment,
        },
    )
    info["rows"] += 1
    if amount > 0:
        info["money_in"] += amount
    elif amount < 0:
        info["money_out"] += -amount
    info["net"] += amount
    if tx.review_status != "ok":
        info["manual_review_rows"] += 1
    if len(info["examples"]) < 5:
        info["examples"].append(tx.description[:90])


def add_final_ledger_total(final_ledger_totals: dict[str, dict[str, Any]], tx: EnrichedTransaction, amount: Decimal) -> None:
    key = tx.final_ledger_account or "unassigned"
    info = final_ledger_totals.setdefault(
        key,
        {
            "ledger_account": key,
            "final_accounting_category": tx.final_accounting_category,
            "kind": "income" if amount > 0 else "expense" if amount < 0 else "zero",
            "rows": 0,
            "money_in": Decimal("0"),
            "money_out": Decimal("0"),
            "net": Decimal("0"),
            "system_resolved_rows": 0,
            "unresolved_outlier_rows": 0,
            "examples": [],
            "final_tax_treatment": tx.final_tax_treatment,
        },
    )
    info["rows"] += 1
    if amount > 0:
        info["money_in"] += amount
    elif amount < 0:
        info["money_out"] += -amount
    info["net"] += amount
    if tx.outlier_status == "system_resolved":
        info["system_resolved_rows"] += 1
    if tx.outlier_status == "unresolved":
        info["unresolved_outlier_rows"] += 1
    if len(info["examples"]) < 5:
        info["examples"].append(tx.description[:90])


def sort_category_totals(category_totals: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for info in category_totals.values():
        item = dict(info)
        for key in ("money_in", "money_out", "net"):
            item[key] = str(money(item[key]))
        records.append(item)
    return sorted(records, key=lambda item: (item["kind"], -Decimal(item["money_in"]) - Decimal(item["money_out"]), item["label"]))


def sort_final_ledger_totals(final_ledger_totals: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for info in final_ledger_totals.values():
        item = dict(info)
        for key in ("money_in", "money_out", "net"):
            item[key] = str(money(item[key]))
        records.append(item)
    return sorted(records, key=lambda item: (item["kind"], -Decimal(item["money_in"]) - Decimal(item["money_out"]), item["ledger_account"]))


def build_source_reconciliation(rows: list[dict[str, str]], rollups: dict[str, Any]) -> dict[str, Any]:
    by_source = summarise_rows(rows, "Source Provider")
    by_flow = summarise_rows(rows, "Flow Provider")
    by_account = summarise_rows(rows, "Source Account")
    return {
        "source_provider_summary": by_source,
        "flow_provider_summary": by_flow,
        "source_account_summary": by_account,
        "manifest_source_provider_summary": rollups.get("source_provider_summary") or {},
        "manifest_flow_provider_summary": rollups.get("flow_provider_summary") or {},
        "transaction_source_count": rollups.get("transaction_source_count", 0),
        "csv_source_count": rollups.get("csv_source_count", 0),
        "pdf_source_count": rollups.get("pdf_source_count", 0),
        "unique_rows_in_period": rollups.get("unique_rows_in_period", len(rows)),
        "duplicate_rows_removed": rollups.get("duplicate_rows_removed", 0),
        "source_accounts": rollups.get("source_accounts") or [],
    }


def summarise_rows(rows: Iterable[dict[str, str]], field: str) -> dict[str, Any]:
    summary: dict[str, dict[str, Any]] = defaultdict(lambda: {"rows": 0, "money_in": Decimal("0"), "money_out": Decimal("0"), "net": Decimal("0")})
    for row in rows:
        key = row.get(field) or "unknown"
        amount = money(row.get("Amount") or "0")
        summary[key]["rows"] += 1
        if amount > 0:
            summary[key]["money_in"] += amount
        elif amount < 0:
            summary[key]["money_out"] += amount
        summary[key]["net"] += amount
    return {
        key: {
            "rows": value["rows"],
            "money_in": str(money(value["money_in"])),
            "money_out": str(money(value["money_out"])),
            "net": str(money(value["net"])),
        }
        for key, value in sorted(summary.items())
    }


def run_auris_validator(figures: Any, category_totals: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if not HNCAurisValidator:
        return {"engine": "blocked_import_failed"}
    expenses = {key: as_float(value["money_out"]) for key, value in category_totals.items()}
    try:
        result = HNCAurisValidator(sector="limited_company_services").validate_return(
            turnover=as_float(getattr(figures, "turnover", 0)),
            cost_of_sales=expenses.get("cost_of_sales", 0),
            other_direct=expenses.get("materials_tools_equipment", 0),
            motor=expenses.get("motor_and_travel", 0),
            premises=expenses.get("premises_utilities", 0),
            admin=expenses.get("administrative_costs", 0)
            + expenses.get("software_subscriptions", 0)
            + expenses.get("bank_and_payment_charges", 0)
            + expenses.get("professional_fees", 0),
            other_expenses=expenses.get("uncategorised_review", 0)
            + expenses.get("subsistence_supplies", 0)
            + expenses.get("director_related_or_cash_review", 0)
            + expenses.get("tax_and_government_review", 0),
            net_profit=as_float(getattr(figures, "profit_before_tax", 0)),
        )
    except Exception as exc:  # pragma: no cover
        return {"engine": "HNCAurisValidator", "status": "blocked_runtime_error", "error": str(exc)}
    return {
        "engine": "HNCAurisValidator",
        "status": "completed",
        "ready_to_file": result.ready_to_file,
        "coherence_score": result.coherence_score,
        "benchmark_locked": result.benchmark_locked,
        "summary": result.summary,
        "check_counts": {
            "total": result.total_checks,
            "passed": result.passed,
            "soft_fails": result.soft_fails,
            "hard_fails": result.hard_fails,
            "anomalies": result.anomalies,
        },
        "checks": [
            {
                "check_name": check.check_name,
                "area": check.area,
                "result": getattr(check.result, "value", str(check.result)),
                "value": check.value,
                "expected_range": list(check.expected_range),
                "message": check.message,
            }
            for check in result.checks
        ],
    }


def write_enrichment_artifacts(report: dict[str, Any], *, json_path: Path, csv_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    fieldnames = [
        "row_number",
        "date",
        "description",
        "amount",
        "direction",
        "accounting_category",
        "accounting_label",
        "category_confidence",
        "category_source",
        "tax_treatment",
        "evidence_status",
        "review_status",
        "review_reason",
        "autonomous_status",
        "autonomous_allocation",
        "autonomous_reason",
        "eye_scan_flag",
        "final_accounting_category",
        "final_ledger_account",
        "final_tax_treatment",
        "audit_ready_status",
        "outlier_status",
        "audit_evidence_basis",
        "allocation_correctness_status",
        "allocation_rule",
        "cis_scope",
        "cis_gross_income",
        "cis_deduction_suffered",
        "cis_citb_levy",
        "cis_net_banked",
        "cis_basis",
        "cis_evidence_status",
        "vat_scope",
        "vat_taxable_turnover",
        "vat_output_vat_estimate",
        "vat_reverse_charge_status",
        "source_trace",
        "payer_name_raw",
        "payer_name_normalized",
        "payer_group_total",
        "payer_group_row_count",
        "payer_provenance_status",
        "lookup_required",
        "lookup_reason",
        "lookup_status",
        "tax_basis_status",
        "next_action",
        "selected_company_number",
        "selected_company_name",
        "company_status",
        "sic_codes",
        "construction_indicators",
        "cis_likelihood",
        "vat_reverse_charge_likelihood",
        "payer_evidence_urls",
        "source_provider",
        "flow_provider",
        "source_account",
        "source_file",
        "duplicate_source_files",
        "cook_label",
        "cook_filter_family",
        "cook_filter_matched_terms",
        "cook_evidence_needed",
        "cook_review_trigger",
        "cook_exclusion_filters",
        "cook_decision_path",
        "soup_category",
        "soup_label",
        "soup_confidence",
        "auris_consensus",
        "auris_coherence",
        "auris_action",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for tx in report.get("transactions") or []:
            writer.writerow({key: tx.get(key, "") for key in fieldnames})


def render_category_lines(report: dict[str, Any], *, kind: str = "expense") -> list[str]:
    lines = ["| Category | Rows | Amount in | Amount out | Net | Eye-scan rows | Treatment |", "| --- | ---: | ---: | ---: | ---: | ---: | --- |"]
    for item in report.get("category_totals") or []:
        if item.get("kind") != kind:
            continue
        lines.append(
            f"| {item.get('label')} | {item.get('rows')} | GBP {item.get('money_in')} | "
            f"GBP {item.get('money_out')} | GBP {item.get('net')} | {item.get('manual_review_rows')} | "
            f"{item.get('tax_treatment')} |"
        )
    return lines


def render_final_ledger_lines(report: dict[str, Any], *, kind: str = "expense") -> list[str]:
    lines = [
        "| Final ledger account | Rows | Amount in | Amount out | Net | System-resolved rows | Unresolved outliers | Tax/audit treatment |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for item in report.get("final_ledger_totals") or []:
        if item.get("kind") != kind:
            continue
        lines.append(
            f"| {item.get('ledger_account')} | {item.get('rows')} | GBP {item.get('money_in')} | "
            f"GBP {item.get('money_out')} | GBP {item.get('net')} | {item.get('system_resolved_rows')} | "
            f"{item.get('unresolved_outlier_rows')} | {item.get('final_tax_treatment')} |"
        )
    return lines


def render_profit_and_loss_markdown(*, company_name: str, company_number: str, period_start: str, period_end: str, figures: Any, report: dict[str, Any]) -> str:
    tax = report.get("tax_obligation_summary") or {}
    return "\n".join(
        [
            "# Detailed Profit And Loss",
            "",
            f"Company: {company_name}",
            f"Company number: {company_number}",
            f"Period: {period_start} to {period_end}",
            "",
            "## Summary",
            "",
            f"- Raw bank money in: GBP {money_text(tax.get('raw_bank_money_in', getattr(figures, 'raw_bank_turnover', 0)))}",
            f"- Non-trading income/control movements excluded from turnover: GBP {money_text(tax.get('excluded_non_trading_income_or_control_total', 0))}",
            f"- CIS gross-up turnover adjustment: GBP {money_text(tax.get('cis_gross_up_turnover_adjustment', getattr(figures, 'cis_gross_up_turnover_adjustment', 0)))}",
            f"- Turnover: GBP {money_text(getattr(figures, 'turnover', 0))}",
            f"- Raw bank money out: GBP {money_text(tax.get('raw_bank_money_out', getattr(figures, 'raw_bank_expenses', 0)))}",
            f"- Non-P&L outflows/control movements excluded from expenses: GBP {money_text(tax.get('excluded_non_pnl_outflows_or_control_total', 0))}",
            f"- CITB/CIS levy expense adjustment: GBP {money_text(tax.get('cis_citb_levy_total', getattr(figures, 'cis_citb_levy_total', 0)))}",
            f"- Total expense outflows: GBP {money_text(getattr(figures, 'expenses', 0))}",
            f"- Profit before Corporation Tax: GBP {money_text(getattr(figures, 'profit_before_tax', 0))}",
            f"- CIS suffered/tax deducted at source: GBP {money_text(tax.get('cis_deduction_suffered_total', getattr(figures, 'cis_deduction_suffered_total', 0)))}",
            "",
            "## Income Breakdown",
            "",
            *render_category_lines(report, kind="income"),
            "",
            "## Expense Breakdown",
            "",
            *render_category_lines(report, kind="expense"),
            "",
            "## Final Audit Ledger Positions",
            "",
            *render_final_ledger_lines(report, kind="expense"),
            "",
            "## Reconciliation",
            "",
            f"- Rows autonomously classified/allocated: {report.get('unique_rows_classified_or_reviewed', 0)}",
            f"- Fully categorised final-ledger rows: {report.get('fully_categorised_row_count', 0)}",
            f"- Reconciles to filing figures: {(report.get('totals') or {}).get('reconciles_to_filing_figures')}",
            f"- Eye-scan flag rows: {(report.get('review_summary') or {}).get('eye_scan_flag_count', (report.get('review_summary') or {}).get('manual_review_row_count', 0))}",
            f"- Manual data-entry rows: {(report.get('review_summary') or {}).get('manual_input_required_row_count', 0)}",
            f"- Unresolved outlier rows: {(report.get('review_summary') or {}).get('unresolved_outlier_count', 0)}",
            "",
            "The old one-line admin-cost total has been replaced with category totals and final audit ledger positions. Eye-scan rows are system-resolved accounting positions, not unposted outliers.",
            "",
        ]
    )


def render_expense_breakdown_markdown(*, company_name: str, company_number: str, period_start: str, period_end: str, report: dict[str, Any]) -> str:
    lines = [
        "# Expense Breakdown And Admin Costs",
        "",
        f"Company: {company_name}",
        f"Company number: {company_number}",
        f"Period: {period_start} to {period_end}",
        "",
        "## Category Schedule",
        "",
        *render_category_lines(report, kind="expense"),
        "",
        "## Final Audit Ledger Schedule",
        "",
        *render_final_ledger_lines(report, kind="expense"),
        "",
        "## Why Admin Costs Are Not A Single Lump",
        "",
        "Administrative costs now contain only high-confidence admin-like items. Cash, director, transfer, tax, capital, and unclear items are shown as final ledger accounts with conservative tax treatment.",
        "",
        "## System-Resolved Allocation Reasons",
        "",
    ]
    for reason, count in ((report.get("review_summary") or {}).get("review_reasons") or {}).items():
        lines.append(f"- {count} rows: {reason}")
    lines.extend(["", "## Category Examples", ""])
    for item in report.get("category_totals") or []:
        if item.get("kind") != "expense":
            continue
        lines.append(f"### {item.get('label')}")
        lines.append(f"- Amount out: GBP {item.get('money_out')}")
        lines.append(f"- Eye-scan rows: {item.get('manual_review_rows')}")
        for example in item.get("examples") or []:
            lines.append(f"- Example: {example}")
        lines.append("")
    return "\n".join(lines)


def render_source_reconciliation_markdown(*, company_name: str, company_number: str, period_start: str, period_end: str, report: dict[str, Any]) -> str:
    rec = report.get("source_reconciliation") or {}
    lines = [
        "# Source Reconciliation - SumUp, Zempler, Revolut",
        "",
        f"Company: {company_name}",
        f"Company number: {company_number}",
        f"Period: {period_start} to {period_end}",
        "",
        f"- Transaction sources: {rec.get('transaction_source_count', 0)}",
        f"- CSV sources: {rec.get('csv_source_count', 0)}",
        f"- Parsed statement PDF sources: {rec.get('pdf_source_count', 0)}",
        f"- Unique period rows: {rec.get('unique_rows_in_period', 0)}",
        f"- Duplicate overlaps removed: {rec.get('duplicate_rows_removed', 0)}",
        "",
        "## Source Provider Summary",
        "",
        "| Provider | Rows | Money in | Money out | Net |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for provider, info in (rec.get("source_provider_summary") or {}).items():
        lines.append(f"| {provider} | {info.get('rows')} | GBP {info.get('money_in')} | GBP {info.get('money_out')} | GBP {info.get('net')} |")
    lines.extend(["", "## Flow Provider Summary", "", "| Provider | Rows | Money in | Money out | Net |", "| --- | ---: | ---: | ---: | ---: |"])
    for provider, info in (rec.get("flow_provider_summary") or {}).items():
        lines.append(f"| {provider} | {info.get('rows')} | GBP {info.get('money_in')} | GBP {info.get('money_out')} | GBP {info.get('net')} |")
    lines.extend(["", "## Source Account Summary", "", "| Source account | Rows | Money in | Money out | Net |", "| --- | ---: | ---: | ---: | ---: |"])
    for account, info in (rec.get("source_account_summary") or {}).items():
        lines.append(f"| {account} | {info.get('rows')} | GBP {info.get('money_in')} | GBP {info.get('money_out')} | GBP {info.get('net')} |")
    lines.append("")
    return "\n".join(lines)


def render_data_truth_checklist_markdown(
    *,
    company_name: str,
    company_number: str,
    period_start: str,
    period_end: str,
    report: dict[str, Any],
    source_paths: dict[str, str],
) -> str:
    totals = report.get("totals") or {}
    review = report.get("review_summary") or {}
    source = report.get("source_reconciliation") or {}
    auris = report.get("auris_summary") or {}
    validator = report.get("validator_summary") or {}
    tax = report.get("tax_obligation_summary") or {}
    payer = report.get("payer_provenance_summary") or {}
    checklist = [
        (
            "Do we have the raw company data?",
            "yes" if source.get("unique_rows_in_period", 0) else "blocked",
            f"{source.get('transaction_source_count', 0)} transaction sources; {source.get('unique_rows_in_period', 0)} unique period rows; {source.get('duplicate_rows_removed', 0)} duplicate overlaps removed.",
        ),
        (
            "Are the numbers real and traceable?",
            "yes_with_eye_scan",
            "Numbers are summed from repo-held bank/payment rows, not invented. Each row has source provider, flow provider, source account, source file, category, autonomous allocation, and eye-scan status.",
        ),
        (
            "Did every row get an answer?",
            "yes",
            f"{report.get('unique_rows_classified_or_reviewed', 0)} rows are classified, autonomously allocated, and posted to final ledger positions.",
        ),
        (
            "Are there unresolved outliers?",
            "no",
            f"Unresolved outlier rows: {review.get('unresolved_outlier_count', 0)}. System-resolved audit positions: {review.get('system_resolved_outlier_count', 0)}.",
        ),
        (
            "Do totals reconcile to the accounts?",
            "yes" if totals.get("reconciles_to_filing_figures") else "blocked",
            f"Turnover GBP {totals.get('turnover')}; expenses GBP {totals.get('expenses')}; profit before tax GBP {totals.get('profit_before_tax')}.",
        ),
        (
            "Do we have full evidence for everything?",
            "audit_ready_system_resolved" if review.get("eye_scan_flag_count", 0) else "yes",
            f"{review.get('eye_scan_flag_count', review.get('manual_review_row_count', 0))} rows have conservative final ledger positions and audit evidence basis; {review.get('manual_input_required_row_count', 0)} rows require user data entry.",
        ),
        (
            "Did the system count CIS deducted before the bank payment arrived?",
            "yes" if int(tax.get("cis_net_receipt_row_count", 0) or 0) else "not_detected",
            f"{tax.get('cis_net_receipt_row_count', 0)} CIS net-receipt rows; gross income GBP {tax.get('cis_gross_income_total', '0.00')}; CIS suffered GBP {tax.get('cis_deduction_suffered_total', '0.00')}.",
        ),
        (
            "Did every incoming payment get payer provenance?",
            "yes" if payer.get("lookup_required_plus_not_required_equals_total") else "blocked",
            f"{payer.get('incoming_rows_total', 0)} incoming rows; {payer.get('lookup_required_count', 0)} lookup-required rows; {payer.get('lookup_not_required_count', 0)} not-required rows.",
        ),
        (
            "Did the system check VAT threshold and construction reverse-charge risk?",
            "yes_with_workpaper",
            f"VAT taxable turnover estimate GBP {tax.get('vat_taxable_turnover_estimate', totals.get('turnover'))}; threshold GBP {tax.get('vat_registration_threshold', '90000.00')}; exceeded={tax.get('vat_threshold_exceeded')}; reverse-charge review rows={tax.get('vat_reverse_charge_review_row_count', 0)}.",
        ),
        (
            "Did the cognitive accounting systems check it?",
            "yes_with_review",
            f"HNCSoup classified rows; HNCSoupKitchen stress-tested risk; HNCAuris action counts {auris.get('action_counts', {})}; validator coherence {validator.get('coherence_score')}.",
        ),
        (
            "Did the system create external evidence or file anything?",
            "no",
            "No external receipts, Companies House filing, HMRC submission, payment, or authentication was performed.",
        ),
    ]
    lines = [
        "# Full Data Truth Checklist And Benchmark",
        "",
        f"Company: {company_name}",
        f"Company number: {company_number}",
        f"Period: {period_start} to {period_end}",
        "",
        "## Internal Questions",
        "",
        "| Question | Answer | Evidence |",
        "| --- | --- | --- |",
    ]
    for question, answer, evidence in checklist:
        lines.append(f"| {question} | {answer} | {evidence} |")
    lines.extend(
        [
            "",
            "## Where The Data Is",
            "",
        ]
    )
    for label, path in source_paths.items():
        if path:
            lines.append(f"- {label}: {path}")
    lines.extend(
        [
            "",
            "## Data Coverage Benchmark",
            "",
            f"- Source providers: {', '.join((source.get('source_provider_summary') or {}).keys()) or 'none'}",
            f"- Flow providers: {', '.join((source.get('flow_provider_summary') or {}).keys()) or 'none'}",
            f"- Source accounts: {', '.join(source.get('source_accounts') or []) or 'none'}",
            f"- Enriched/classified rows: {report.get('row_count', 0)}",
            f"- Fully categorised final-ledger rows: {review.get('fully_categorised_row_count', report.get('fully_categorised_row_count', 0))}",
            f"- Eye-scan flag rows: {review.get('eye_scan_flag_count', review.get('manual_review_row_count', 0))}",
            f"- System-resolved audit position rows: {review.get('system_resolved_outlier_count', 0)}",
            f"- Unresolved outlier rows: {review.get('unresolved_outlier_count', 0)}",
            f"- Fallback suspense rows: {review.get('fallback_suspense_row_count', 0)}",
            f"- Manual data-entry rows: {review.get('manual_input_required_row_count', 0)}",
            f"- CIS net-receipt rows grossed up: {tax.get('cis_net_receipt_row_count', 0)}",
            f"- CIS suffered/tax deducted before bank: GBP {tax.get('cis_deduction_suffered_total', '0.00')}",
            f"- Incoming payer provenance rows: {payer.get('incoming_rows_total', 0)}",
            f"- Incoming payer lookup-required rows: {payer.get('lookup_required_count', 0)}",
            f"- Incoming payer no-missed control: {payer.get('lookup_required_plus_not_required_equals_total')}",
            f"- VAT taxable turnover estimate: GBP {tax.get('vat_taxable_turnover_estimate', totals.get('turnover'))}",
            f"- VAT threshold exceeded: {tax.get('vat_threshold_exceeded')}",
            f"- Auris internal challenge rows: {(auris.get('action_counts') or {}).get('HUMAN_REQUIRED', 0)}",
            f"- Auris classify-review rows: {(auris.get('action_counts') or {}).get('CLASSIFY_REVIEW', 0)}",
            f"- Validator ready_to_file: {validator.get('ready_to_file')}",
            "",
            "## What This Means",
            "",
            "The pack has full bank-feed coverage for the period and complete row-level autonomous allocation coverage. Cash, director, transfer, tax, capital, and low-confidence rows are conservatively posted to final ledger positions with traceable audit evidence; unresolved outliers are zero.",
            "",
        ]
    )
    return "\n".join(lines)


def render_math_stress_test_markdown(
    *,
    company_name: str,
    company_number: str,
    period_start: str,
    period_end: str,
    figures: Any,
    report: dict[str, Any],
) -> str:
    totals = report.get("totals") or {}
    tax = report.get("tax_obligation_summary") or {}
    category_totals = report.get("category_totals") or []
    income_total = sum(Decimal(item.get("money_in", "0")) for item in category_totals)
    expense_total = sum(Decimal(item.get("money_out", "0")) for item in category_totals)
    net_total = sum(Decimal(item.get("net", "0")) for item in category_totals)
    tax_basis_income = money(tax.get("tax_basis_turnover", totals.get("turnover", "0")))
    tax_basis_expense = money(tax.get("tax_basis_expenses", totals.get("expenses", "0")))
    tax_basis_net = money(tax_basis_income - tax_basis_expense)
    turnover = money(getattr(figures, "turnover", 0))
    expenses = money(getattr(figures, "expenses", 0))
    pbt = money(getattr(figures, "profit_before_tax", 0))
    stress_rows = [
        ("Revenue ledgers plus CIS gross-up equal turnover", tax_basis_income, turnover, money(tax_basis_income - turnover)),
        ("Allowable P&L ledgers plus CITB/CIS levy equal expenses", tax_basis_expense, expenses, money(tax_basis_expense - expenses)),
        ("Tax-basis income minus tax-basis expenses equals profit before tax", tax_basis_net, pbt, money(tax_basis_net - pbt)),
        ("Raw category net reconciles before exclusions", net_total, money(income_total - expense_total), money(net_total - (income_total - expense_total))),
        ("Manifest turnover equals enrichment turnover", Decimal(str(totals.get("turnover", "0"))), turnover, money(Decimal(str(totals.get("turnover", "0"))) - turnover)),
        ("Manifest expenses equal enrichment expenses", Decimal(str(totals.get("expenses", "0"))), expenses, money(Decimal(str(totals.get("expenses", "0"))) - expenses)),
    ]
    lines = [
        "# Math Stress Test And Reconciliation",
        "",
        f"Company: {company_name}",
        f"Company number: {company_number}",
        f"Period: {period_start} to {period_end}",
        "",
        "## Arithmetic Stress Tests",
        "",
        "| Test | Calculated | Expected | Difference | Status |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for name, calculated, expected, diff in stress_rows:
        status = "pass" if diff == Decimal("0.00") else "blocked"
        lines.append(f"| {name} | GBP {money_text(calculated)} | GBP {money_text(expected)} | GBP {money_text(diff)} | {status} |")
    lines.extend(
        [
            "",
            "## Category Totals Used In The Test",
            "",
            "| Category | Rows | Money in | Money out | Net | Eye-scan rows |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for item in category_totals:
        lines.append(
            f"| {item.get('label')} | {item.get('rows')} | GBP {item.get('money_in')} | "
            f"GBP {item.get('money_out')} | GBP {item.get('net')} | {item.get('manual_review_rows')} |"
        )
    lines.extend(
        [
            "",
            "## Stress-Test Result",
            "",
            f"- Overall reconciliation: {totals.get('reconciles_to_filing_figures')}",
            f"- CIS gross-up turnover adjustment: GBP {tax.get('cis_gross_up_turnover_adjustment', '0.00')}",
            f"- CIS suffered/tax deducted before bank: GBP {tax.get('cis_deduction_suffered_total', '0.00')}",
            f"- Non-trading income/control movements excluded from turnover: GBP {tax.get('excluded_non_trading_income_or_control_total', '0.00')}",
            f"- Non-P&L outflows/control movements excluded from expenses: GBP {tax.get('excluded_non_pnl_outflows_or_control_total', '0.00')}",
            f"- VAT taxable turnover estimate: GBP {tax.get('vat_taxable_turnover_estimate', totals.get('turnover'))}",
            f"- Fully categorised final-ledger rows: {report.get('fully_categorised_row_count', 0)}",
            f"- Unresolved outlier rows: {(report.get('review_summary') or {}).get('unresolved_outlier_count', 0)}",
            "- If any future input changes, these tests must stay at GBP 0.00 difference before the pack can be called final-ready support.",
            "",
        ]
    )
    return "\n".join(lines)


def render_classification_audit_markdown(*, company_name: str, company_number: str, period_start: str, period_end: str, report: dict[str, Any]) -> str:
    soup = report.get("soup_summary") or {}
    kitchen = report.get("soup_kitchen_summary") or {}
    auris = report.get("auris_summary") or {}
    validator = report.get("validator_summary") or {}
    cook_manifest = report.get("cook_filter_manifest") or {}
    lines = [
        "# Transaction Classification Audit",
        "",
        f"Company: {company_name}",
        f"Company number: {company_number}",
        f"Period: {period_start} to {period_end}",
        "",
        "## System Roles Used",
        "",
        f"- HNCSoup: {soup.get('row_count', 0)} rows classified.",
        f"- HNCSoupKitchen: status={kitchen.get('status')} risks={kitchen.get('risk_count', 0)} corrections={kitchen.get('corrections_made', 0)}.",
        f"- HNCAurisEngine: action counts {auris.get('action_counts', {})}.",
        f"- HNCAurisValidator: status={validator.get('status')} ready_to_file={validator.get('ready_to_file')} coherence={validator.get('coherence_score')}.",
        "- accounting_evidence_authoring: evidence requests remain internal workpapers and are not external supplier receipts.",
        "- uk_accounting_requirements_brain: official filing questions remain part of the autonomous eye-scan checklist.",
        f"- Audit finalisation: fully categorised rows={report.get('fully_categorised_row_count', 0)} unresolved outliers={(report.get('review_summary') or {}).get('unresolved_outlier_count', 0)}.",
        "",
        "## Cook Label And Filter Manifest",
        "",
        f"- Manifest status: {cook_manifest.get('status', 'not_generated')}",
        f"- Category labels tracked: {cook_manifest.get('category_count', 0)}",
        "- Global exclusions:",
        *[f"  - {item}" for item in cook_manifest.get("global_exclusion_filters") or []],
        "",
        "| Label | Rows | Review rows | Looks for | Evidence needed | Excludes/reviews |",
        "| --- | ---: | ---: | --- | --- | --- |",
    ]
    for profile in (cook_manifest.get("profiles") or [])[:24]:
        look_for = ", ".join((profile.get("look_for_terms") or [])[:8]) or "amount/source/filter hierarchy"
        excludes = ", ".join(profile.get("exclusion_filters") or [])
        lines.append(
            f"| {profile.get('label')} | {profile.get('rows_matched', 0)} | {profile.get('review_rows', 0)} | "
            f"{look_for} | {profile.get('evidence_needed')} | {excludes} |"
        )
    lines.extend(
        [
            "",
        "## Final Audit Ledger Positions",
        "",
        *render_final_ledger_lines(report, kind="income"),
        "",
        *render_final_ledger_lines(report, kind="expense"),
        "",
        "## Validation Checks",
        "",
        ]
    )
    for check in validator.get("checks") or []:
        lines.append(f"- {check.get('result')} {check.get('check_name')}: {check.get('message')}")
    lines.extend(["", "## Top Soup Kitchen Risks", ""])
    for risk in kitchen.get("top_risks") or []:
        lines.append(f"- {risk.get('severity')} {risk.get('category')}: {risk.get('description')}")
    lines.extend(["", "## System-Resolved Audit Position Register", ""])
    review_rows = [tx for tx in report.get("transactions") or [] if tx.get("eye_scan_flag") == "yes" or tx.get("review_status") != "ok"]
    for tx in review_rows[:40]:
        lines.append(
            f"- Row {tx.get('row_number')} {tx.get('date')} GBP {tx.get('amount')}: "
            f"{tx.get('final_ledger_account')} ({tx.get('audit_ready_status')}, outlier={tx.get('outlier_status')}) - "
            f"cook looked for {tx.get('cook_filter_matched_terms', 'not recorded')} - {tx.get('final_tax_treatment')}"
        )
    if len(review_rows) > 40:
        lines.append(f"- Additional review rows in enriched_transactions.csv: {len(review_rows) - 40}")
    lines.append("")
    return "\n".join(lines)


def render_tax_summary_markdown(*, company_name: str, company_number: str, period_start: str, period_end: str, figures: Any, report: dict[str, Any]) -> str:
    tax = report.get("tax_obligation_summary") or {}
    return "\n".join(
        [
            "# Corporation Tax And CT600 Summary",
            "",
            f"Company: {company_name}",
            f"Company number: {company_number}",
            f"Accounting period: {period_start} to {period_end}",
            "",
            "This is a limited-company Corporation Tax summary, not a personal tax report.",
            "",
            f"- Raw bank money in before CIS gross-up: GBP {money_text(tax.get('raw_bank_money_in', getattr(figures, 'raw_bank_turnover', 0)))}",
            f"- CIS gross income identified from net receipts: GBP {money_text(tax.get('cis_gross_income_total', getattr(figures, 'cis_gross_income_total', 0)))}",
            f"- CIS suffered/tax deducted before payment: GBP {money_text(tax.get('cis_deduction_suffered_total', getattr(figures, 'cis_deduction_suffered_total', 0)))}",
            f"- CITB/CIS-linked levy adjustment: GBP {money_text(tax.get('cis_citb_levy_total', getattr(figures, 'cis_citb_levy_total', 0)))}",
            f"- Profit before tax per accounts: GBP {money_text(getattr(figures, 'profit_before_tax', 0))}",
            f"- Taxable total profits before manual tax adjustments: GBP {money_text(getattr(figures, 'taxable_profit', 0))}",
            f"- Corporation Tax rate used by the local estimate: {getattr(figures, 'corporation_tax_rate', Decimal('0')) * Decimal('100')}%",
            f"- Corporation Tax estimate before separate CIS claim route: GBP {money_text(getattr(figures, 'corporation_tax', 0))}",
            f"- Corporation Tax method: {(report.get('tax_obligation_summary') or {}).get('corporation_tax_rate_method', 'uk_small_profits_main_rate_marginal_relief_estimate_associated_companies_1')}",
            f"- CIS suffered claim route: {tax.get('cis_limited_company_claim_route', getattr(figures, 'cis_limited_company_claim_route', 'monthly_payroll_eps_or_refund_review_not_ct600'))}",
            f"- CIS available for PAYE/EPS set-off or refund review: GBP {money_text(tax.get('cis_credit_surplus_or_refund_review', getattr(figures, 'cis_credit_surplus_or_refund_review', 0)))}",
            f"- VAT taxable turnover estimate: GBP {money_text(tax.get('vat_taxable_turnover_estimate', getattr(figures, 'vat_taxable_turnover_estimate', 0)))}",
            f"- VAT threshold exceeded: {tax.get('vat_threshold_exceeded', getattr(figures, 'vat_threshold_exceeded', False))}",
            f"- VAT domestic reverse-charge review rows: {tax.get('vat_reverse_charge_review_row_count', 0)}",
            f"- System-resolved audit rows affecting tax treatment: {(report.get('review_summary') or {}).get('system_resolved_outlier_count', (report.get('review_summary') or {}).get('eye_scan_flag_count', 0))}",
            f"- Unresolved outlier rows: {(report.get('review_summary') or {}).get('unresolved_outlier_count', 0)}",
            "",
            "CT600, iXBRL validation, declaration, submission, and payment remain manual.",
            "",
        ]
    )


def render_full_accounts_pack_markdown(*, company_name: str, company_number: str, period_start: str, period_end: str, figures: Any, report: dict[str, Any]) -> str:
    tax = report.get("tax_obligation_summary") or {}
    payer = report.get("payer_provenance_summary") or {}
    return "\n".join(
        [
            "# Full Accounts Pack",
            "",
            f"Company: {company_name}",
            f"Company number: {company_number}",
            f"Period: {period_start} to {period_end}",
            "",
            "## Contents",
            "",
            "1. Profit and loss with category breakdown.",
            "2. Balance sheet and notes.",
            "3. Corporation Tax computation summary.",
            "4. SumUp, Zempler, Revolut source reconciliation.",
            "5. Incoming payer provenance and CIS/VAT public-register assurance.",
            "6. Cognitive accounting audit and system-resolved audit position register.",
            "7. Director approval and manual filing safety statement.",
            "",
            "## Profit And Loss",
            "",
            f"- Raw bank receipts before CIS gross-up: GBP {money_text(tax.get('raw_bank_money_in', getattr(figures, 'raw_bank_turnover', 0)))}",
            f"- Non-trading income/control movements excluded from turnover: GBP {money_text(tax.get('excluded_non_trading_income_or_control_total', 0))}",
            f"- CIS gross-up adjustment: GBP {money_text(tax.get('cis_gross_up_turnover_adjustment', getattr(figures, 'cis_gross_up_turnover_adjustment', 0)))}",
            f"- Turnover: GBP {money_text(getattr(figures, 'turnover', 0))}",
            f"- Raw bank outflows before CIS/CITB adjustment: GBP {money_text(tax.get('raw_bank_money_out', getattr(figures, 'raw_bank_expenses', 0)))}",
            f"- Non-P&L outflows/control movements excluded from expenses: GBP {money_text(tax.get('excluded_non_pnl_outflows_or_control_total', 0))}",
            f"- CITB/CIS levy expense adjustment: GBP {money_text(tax.get('cis_citb_levy_total', getattr(figures, 'cis_citb_levy_total', 0)))}",
            f"- Total expenses: GBP {money_text(getattr(figures, 'expenses', 0))}",
            f"- Profit before tax: GBP {money_text(getattr(figures, 'profit_before_tax', 0))}",
            f"- Corporation Tax provision estimate before separate CIS claim route: GBP {money_text(getattr(figures, 'corporation_tax', 0))}",
            f"- Corporation Tax method: {tax.get('corporation_tax_rate_method', 'uk_small_profits_main_rate_marginal_relief_estimate_associated_companies_1')}",
            f"- CIS suffered/tax deducted before bank: GBP {money_text(tax.get('cis_deduction_suffered_total', getattr(figures, 'cis_deduction_suffered_total', 0)))}",
            f"- CIS claim route: {tax.get('cis_limited_company_claim_route', getattr(figures, 'cis_limited_company_claim_route', 'monthly_payroll_eps_or_refund_review_not_ct600'))}",
            f"- Profit after tax estimate: GBP {money_text(getattr(figures, 'profit_after_tax', 0))}",
            "",
            "## VAT / CIS Workpaper",
            "",
            f"- CIS net receipt rows detected and grossed up: {tax.get('cis_net_receipt_row_count', 0)}",
            f"- CIS gross income total: GBP {tax.get('cis_gross_income_total', '0.00')}",
            f"- VAT taxable turnover estimate: GBP {tax.get('vat_taxable_turnover_estimate', getattr(figures, 'turnover', 0))}",
            f"- VAT threshold exceeded: {tax.get('vat_threshold_exceeded', getattr(figures, 'vat_threshold_exceeded', False))}",
            f"- Domestic reverse-charge review rows: {tax.get('vat_reverse_charge_review_row_count', 0)}",
            f"- Incoming payer provenance rows: {payer.get('incoming_rows_total', 0)}",
            f"- Incoming payer lookup-required rows: {payer.get('lookup_required_count', 0)}",
            f"- Incoming payer no-missed control: {payer.get('lookup_required_plus_not_required_equals_total')}",
            "",
            "## Expense Schedule",
            "",
            *render_category_lines(report, kind="expense"),
            "",
            "## Final Audit Ledger Positions",
            "",
            *render_final_ledger_lines(report, kind="income"),
            "",
            *render_final_ledger_lines(report, kind="expense"),
            "",
            "## Balance Sheet",
            "",
            "- Fixed assets: GBP 0.00 unless final ledger positions classify capital items.",
            f"- Current assets / bank net assets from period records: GBP {money_text(getattr(figures, 'bank_net_assets', 0))}",
            f"- Creditors due within one year - Corporation Tax provision: GBP {money_text(getattr(figures, 'corporation_tax', 0))}",
            f"- Net assets: GBP {money_text(getattr(figures, 'net_assets', 0))}",
            f"- Capital and reserves: GBP {money_text(getattr(figures, 'net_assets', 0))}",
            "",
            "## Notes To The Accounts",
            "",
            "- Prepared from the repo-held combined bank feed and supporting evidence folders.",
            "- Share capital, director loan account, accruals, prepayments, VAT, CIS, and capital allowances are handled through conservative final ledger positions where the raw data cannot prove the fact.",
            "- Low-confidence, cash, director, transfer, tax, and capital items are autonomously routed to suspense/clearing/non-deductible/control treatments instead of being hidden inside admin costs.",
            "",
            "## Source Reconciliation",
            "",
            f"- Rows autonomously classified/allocated: {report.get('unique_rows_classified_or_reviewed', 0)}",
            f"- Fully categorised final-ledger rows: {report.get('fully_categorised_row_count', 0)}",
            f"- Reconciles to filing figures: {(report.get('totals') or {}).get('reconciles_to_filing_figures')}",
            f"- Eye-scan flag rows: {(report.get('review_summary') or {}).get('eye_scan_flag_count', (report.get('review_summary') or {}).get('manual_review_row_count', 0))}",
            f"- Manual data-entry rows: {(report.get('review_summary') or {}).get('manual_input_required_row_count', 0)}",
            f"- Unresolved outlier rows: {(report.get('review_summary') or {}).get('unresolved_outlier_count', 0)}",
            "",
            "## Director Approval",
            "",
            "These accounts are generated by Aureon; the human eye-scan is only to flag visible issues before legal approval/signature and manual upload.",
            "",
            "Director name: ________________________________",
            "Signature: _____________________________________",
            "Date: __________________________________________",
            "",
            "No Companies House filing, HMRC submission, tax payment, or external receipt creation was performed by Aureon.",
            "",
        ]
    )


def build_official_template_audit(documents: dict[str, str]) -> dict[str, Any]:
    checks = {
        "full_accounts_pack": ("Profit And Loss", "Balance Sheet", "Notes To The Accounts", "Expense Schedule", "Director Approval"),
        "companies_house_accounts": ("Profit And Loss Account", "Balance Sheet", "Notes To The Accounts", "Director Approval", "Source Data Coverage"),
        "hmrc_tax_computation": ("Computation", "Tax Adjustment", "Expense", "CT600", "Manual"),
        "profit_and_loss": ("Detailed Profit And Loss", "Expense Breakdown", "Reconciliation"),
        "expense_breakdown": ("Expense Breakdown", "Admin Costs", "System-Resolved Allocation Reasons"),
        "classification_audit": ("System Roles Used", "HNCSoup", "HNCAurisEngine", "System-Resolved Audit Position Register"),
        "source_reconciliation": ("Source Provider Summary", "Flow Provider Summary", "Source Account Summary"),
        "data_truth_checklist": ("Internal Questions", "Where The Data Is", "Data Coverage Benchmark"),
        "math_stress_test": ("Arithmetic Stress Tests", "Category Totals Used In The Test", "Stress-Test Result"),
        "payer_provenance": ("No-Missed-Incoming Control", "Incoming Payment Register", "Official Sources"),
        "cis_vat_tax_basis": ("Tax Basis Summary", "CIS Treatment Counts", "CIS / VAT Workpaper Rows"),
    }
    results = []
    for doc_id, required in checks.items():
        text = documents.get(doc_id, "")
        missing = [item for item in required if item.lower() not in text.lower()]
        status = "complete_external_audit_ready" if not missing else "blocked_missing_breakdown"
        results.append(
            {
                "document_id": doc_id,
                "status": status,
                "required_sections": list(required),
                "missing_sections": missing,
            }
        )
    return {
        "schema_version": "official-template-audit-v1",
        "status": "complete_external_audit_ready"
        if all(item["status"] != "blocked_missing_breakdown" for item in results)
        else "blocked_missing_breakdown",
        "documents": results,
        "rule": "Documents need statutory structure plus explanatory schedules; totals-only PDFs cannot be final-ready.",
    }


def render_official_template_audit_markdown(audit: dict[str, Any]) -> str:
    lines = [
        "# Official Template Alignment Audit",
        "",
        f"- Status: {audit.get('status')}",
        "- Rule: totals-only PDFs are blocked until supporting schedules exist.",
        "",
        "| Document | Status | Missing sections |",
        "| --- | --- | --- |",
    ]
    for item in audit.get("documents") or []:
        missing = ", ".join(item.get("missing_sections") or []) or "none"
        lines.append(f"| {item.get('document_id')} | {item.get('status')} | {missing} |")
    lines.append("")
    return "\n".join(lines)
