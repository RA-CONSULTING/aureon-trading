"""
BUILD THE FULL PICTURE
======================
Process all 20 CSV files (Sep 2024 → Apr 2026)
Split into tax years: 2024/25 and 2025/26
Run everything through the Soup
Generate comprehensive Excel workbook

Aureon Creator / Aureon Research — April 2026
"""

import sys, os, json, re
from datetime import datetime, date
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.hnc_import import HNCImportEngine
from core.hnc_soup import HNCSoup, SA103_CATEGORIES

# ========================================================================
# CONFIG
# ========================================================================

SEARCH_DIRS = [
    os.path.join(os.path.dirname(__file__), "..", "..", "uploads"),
    "/sessions/upbeat-stoic-hamilton/mnt/uploads",
]

TAX_YEAR_2425_START = date(2024, 4, 6)
TAX_YEAR_2425_END = date(2025, 4, 5)
TAX_YEAR_2526_START = date(2025, 4, 6)
TAX_YEAR_2526_END = date(2026, 4, 5)

# Pre-April 2024 data goes into "pre-period" bucket
# Post-April 2026 data goes into "current" bucket

# ========================================================================
# FILE DISCOVERY & DEDUP
# ========================================================================

def find_csv_files():
    """Find all statement CSVs, dedup by date range (not filename)."""
    seen_names = set()
    csv_files = []

    for d in SEARCH_DIRS:
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if not f.endswith(".csv") or "Statement" not in f:
                continue
            # Extract the date portion to dedup _1 vs _1_1 copies
            # Pattern: Statement_DD_Mon_YYYY_DD_Mon_YYYY
            match = re.search(r'Statement_(\d{2}_\w{3}_\d{4}_\d{2}_\w{3}_\d{4})', f)
            if match:
                date_key = match.group(1)
            else:
                date_key = f

            if date_key not in seen_names:
                seen_names.add(date_key)
                csv_files.append(os.path.join(d, f))

    csv_files.sort()
    return csv_files


def read_utf16_csv(filepath):
    """Read UTF-16 encoded CSV with fallback."""
    for enc in ("utf-16", "utf-16-le", "utf-16-be", "utf-8-sig", "latin-1"):
        try:
            with open(filepath, "r", encoding=enc) as f:
                text = f.read()
            text = text.replace("\x00", "")
            if "Date" in text:
                return text
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise RuntimeError(f"Could not decode {filepath}")


def parse_date_str(date_str):
    """Parse DD Mon YYYY or YYYY-MM-DD into date object."""
    if not date_str:
        return None
    for fmt in ("%d %b %Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except (ValueError, AttributeError):
            continue
    return None


def get_tax_year(d):
    """Return tax year string for a date."""
    if d is None:
        return "unknown"
    if d < TAX_YEAR_2425_START:
        return "pre-2024/25"
    elif d <= TAX_YEAR_2425_END:
        return "2024/25"
    elif d <= TAX_YEAR_2526_END:
        return "2025/26"
    else:
        return "post-2025/26"


# ========================================================================
# MAIN
# ========================================================================

print("=" * 80)
print("  HNC — BUILDING THE FULL PICTURE")
print("  Aureon Creator | Sep 2024 → Apr 2026")
print("=" * 80)

# Step 1: Find and import all CSVs
csv_files = find_csv_files()
print(f"\n  Found {len(csv_files)} unique statement files:")
for f in csv_files:
    print(f"    {os.path.basename(f)}")

importer = HNCImportEngine()
total_imported = 0
for filepath in csv_files:
    try:
        csv_text = read_utf16_csv(filepath)
        result = importer.import_csv_string(csv_text, os.path.basename(filepath))
        total_imported += result.rows_imported
        print(f"    ✓ {os.path.basename(filepath)}: {result.rows_imported} transactions")
    except Exception as e:
        print(f"    ✗ {os.path.basename(filepath)}: ERROR — {e}")

all_txns = importer.get_bank_transactions()
print(f"\n  Total raw transactions: {len(all_txns)}")

# Step 2: Deduplicate (same date + same amount + same description)
seen = set()
unique_txns = []
dupes = 0
for t in all_txns:
    key = (t.get("date", ""), t.get("amount", 0), t.get("description", "")[:40])
    if key not in seen:
        seen.add(key)
        unique_txns.append(t)
    else:
        dupes += 1
print(f"  Duplicates removed: {dupes}")
print(f"  Unique transactions: {len(unique_txns)}")

# Step 3: Split by tax year
by_year = defaultdict(list)
for t in unique_txns:
    d = parse_date_str(t.get("date", ""))
    ty = get_tax_year(d)
    by_year[ty].append(t)

print(f"\n  TRANSACTIONS BY TAX YEAR:")
for year in sorted(by_year.keys()):
    count = len(by_year[year])
    income = sum(t.get("amount", 0) for t in by_year[year] if t.get("direction") == "in")
    outflow = sum(abs(t.get("amount", 0)) for t in by_year[year] if t.get("direction") == "out")
    print(f"    {year}: {count} transactions | IN £{income:,.2f} | OUT £{outflow:,.2f}")

# Step 4: Run each tax year through the Soup
print("\n" + "=" * 80)
print("  SOUP CLASSIFICATION — BY TAX YEAR")
print("=" * 80)

all_results = {}

for year_key in ["2024/25", "2025/26"]:
    txns = by_year.get(year_key, [])
    if not txns:
        print(f"\n  {year_key}: No transactions")
        continue

    soup = HNCSoup(
        entity_name="Aureon Creator",
        trades=["construction", "food", "consulting", "digital", "property"],
    )
    results = soup.classify_all(txns)
    all_results[year_key] = {
        "soup": soup,
        "results": results,
        "txns": txns,
    }

    print(soup.print_full_report())
    print(f"\n  --- {year_key} END ---\n")

# Step 5: Combined summary
print("\n" + "=" * 80)
print("  COMBINED SUMMARY — BOTH TAX YEARS")
print("=" * 80)

for year_key in ["2024/25", "2025/26"]:
    data = all_results.get(year_key)
    if not data:
        continue
    soup = data["soup"]

    income = soup.get_income_by_trade()
    expenses = soup.get_sa103_summary()
    transfers = soup.get_transfer_summary()

    total_income = sum(income.values())
    total_expenses = sum(expenses.values())
    net_profit = total_income - total_expenses

    print(f"\n  ═══ TAX YEAR {year_key} ═══")
    print(f"  Transactions: {len(data['txns'])}")
    print(f"  Transfers excluded: {transfers['count']}")
    print(f"  Gross Turnover: £{total_income:,.2f}")
    print(f"  Allowable Expenses: £{total_expenses:,.2f}")
    print(f"  Net Profit: £{net_profit:,.2f}")

    # Income breakdown
    print(f"\n  Income by Trade:")
    for trade, amount in sorted(income.items(), key=lambda x: -x[1]):
        pct = (amount / total_income * 100) if total_income else 0
        print(f"    {trade:<20} £{amount:>10,.2f}  ({pct:.1f}%)")

    # Expense breakdown by SA103 box
    print(f"\n  Expenses by SA103 Box:")
    for cat, amount in sorted(expenses.items(), key=lambda x: -x[1]):
        info = SA103_CATEGORIES.get(cat, {})
        box = info.get("box", "?")
        label = info.get("label", cat)[:40]
        print(f"    {box} {label:<40} £{amount:>10,.2f}")

    # Tax estimate
    pa = 12_570
    taxable = max(0, net_profit - pa)
    if taxable <= 37_700:
        tax = taxable * 0.20
    elif taxable <= 125_140:
        tax = 37_700 * 0.20 + (taxable - 37_700) * 0.40
    else:
        tax = 37_700 * 0.20 + 87_440 * 0.40 + (taxable - 125_140) * 0.45

    # NI Class 2 and 4
    ni_class2 = 179.40 if net_profit >= 12_570 else 0  # £3.45/week × 52
    ni_class4 = 0
    if net_profit > 12_570:
        ni_band1 = min(net_profit, 50_270) - 12_570
        ni_class4 = ni_band1 * 0.06
        if net_profit > 50_270:
            ni_class4 += (net_profit - 50_270) * 0.02

    total_tax = tax + ni_class2 + ni_class4

    print(f"\n  TAX ESTIMATE:")
    print(f"    Net Profit:          £{net_profit:>10,.2f}")
    print(f"    Personal Allowance:  £{pa:>10,}")
    print(f"    Taxable Income:      £{taxable:>10,.2f}")
    print(f"    Income Tax:          £{tax:>10,.2f}")
    print(f"    NI Class 2:          £{ni_class2:>10,.2f}")
    print(f"    NI Class 4:          £{ni_class4:>10,.2f}")
    print(f"    TOTAL TAX:           £{total_tax:>10,.2f}")
    print(f"    Take-home:           £{net_profit - total_tax:>10,.2f}")

# Step 6: Private advisory
print("\n" + "=" * 80)
print("  PRIVATE ADVISORY NOTES")
print("  (FOR YOUR EYES ONLY — NEVER sent to HMRC)")
print("=" * 80)

for year_key in ["2024/25", "2025/26"]:
    data = all_results.get(year_key)
    if not data:
        continue
    advisory = data["soup"].get_private_advisory()
    if advisory:
        print(f"\n  === {year_key} ===")
        for note in advisory:
            print(f"  {note}")

# Step 7: Unclassified transactions (need attention)
print("\n" + "=" * 80)
print("  UNCLASSIFIED / LOW-CONFIDENCE TRANSACTIONS")
print("  (Review these for manual classification)")
print("=" * 80)

for year_key in ["2024/25", "2025/26"]:
    data = all_results.get(year_key)
    if not data:
        continue

    low_conf = [r for r in data["results"]
                if r.confidence < 0.6 and not r.is_transfer]

    if low_conf:
        print(f"\n  === {year_key} ({len(low_conf)} items) ===")
        for r in sorted(low_conf, key=lambda x: x.original.get("date", "")):
            t = r.original
            d = t.get("direction", "")
            print(f"    {t.get('date',''):<12} {d:>3} £{t.get('amount',0):>9,.2f}  "
                  f"{t.get('description','')[:45]}  [{r.hmrc_category}]")

# Step 8: Output summary data as JSON for Excel generation
summary = {}
for year_key in ["2024/25", "2025/26"]:
    data = all_results.get(year_key)
    if not data:
        continue
    soup = data["soup"]

    income = soup.get_income_by_trade()
    expenses = soup.get_sa103_summary()
    transfers = soup.get_transfer_summary()

    total_income = sum(income.values())
    total_expenses = sum(expenses.values())

    summary[year_key] = {
        "total_transactions": len(data["txns"]),
        "transfers_excluded": transfers["count"],
        "income_by_trade": income,
        "total_income": total_income,
        "expenses_by_sa103": expenses,
        "total_expenses": total_expenses,
        "net_profit": total_income - total_expenses,
    }

output_path = os.path.join(os.path.dirname(__file__), "..", "output", "full_picture_data.json")
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, "w") as f:
    json.dump(summary, f, indent=2, default=str)

print(f"\n\n  Summary data saved to: {output_path}")
print("=" * 80)
