"""
TEST SOUP KITCHEN
=================
Run the Soup then the Kitchen on all data.
Shows before/after comparison.
"""

import sys, os, re
from datetime import datetime, date
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.hnc_import import HNCImportEngine
from core.hnc_soup import HNCSoup, SA103_CATEGORIES
from core.hnc_soup_kitchen import HNCSoupKitchen

SEARCH_DIRS = [
    os.path.join(os.path.dirname(__file__), "..", "..", "uploads"),
    "/sessions/upbeat-stoic-hamilton/mnt/uploads",
]

TAX_YEAR_2425_END = date(2025, 4, 5)
TAX_YEAR_2526_END = date(2026, 4, 5)
TAX_YEAR_2425_START = date(2024, 4, 6)

def find_csv_files():
    seen_names = set()
    csv_files = []
    for d in SEARCH_DIRS:
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if not f.endswith(".csv") or "Statement" not in f:
                continue
            match = re.search(r'Statement_(\d{2}_\w{3}_\d{4}_\d{2}_\w{3}_\d{4})', f)
            date_key = match.group(1) if match else f
            if date_key not in seen_names:
                seen_names.add(date_key)
                csv_files.append(os.path.join(d, f))
    csv_files.sort()
    return csv_files

def read_utf16_csv(filepath):
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
    if not date_str:
        return None
    for fmt in ("%d %b %Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except:
            continue
    return None

def get_tax_year(d):
    if d is None:
        return "unknown"
    if d < TAX_YEAR_2425_START:
        return "pre-2024/25"
    elif d <= TAX_YEAR_2425_END:
        return "2024/25"
    elif d <= TAX_YEAR_2526_END:
        return "2025/26"
    return "post-2025/26"

# Import
csv_files = find_csv_files()
importer = HNCImportEngine()
for f in csv_files:
    try:
        importer.import_csv_string(read_utf16_csv(f), os.path.basename(f))
    except:
        pass

all_txns = importer.get_bank_transactions()

# Dedup
seen = set()
unique_txns = []
for t in all_txns:
    key = (t.get("date", ""), t.get("amount", 0), t.get("description", "")[:40])
    if key not in seen:
        seen.add(key)
        unique_txns.append(t)

# Split by year
by_year = defaultdict(list)
for t in unique_txns:
    d = parse_date_str(t.get("date", ""))
    by_year[get_tax_year(d)].append(t)

print("=" * 80)
print("  SOUP KITCHEN — BEFORE vs AFTER")
print("=" * 80)

for year_key in ["2024/25", "2025/26"]:
    txns = by_year.get(year_key, [])
    if not txns:
        continue

    # Run Soup
    soup = HNCSoup(entity_name="Aureon Creator",
                   trades=["construction", "food", "consulting", "digital", "property"])
    soup.classify_all(txns)

    # Snapshot BEFORE
    before_expenses = dict(soup.get_sa103_summary())
    before_income = dict(soup.get_income_by_trade())
    before_total_exp = sum(before_expenses.values())
    before_total_inc = sum(before_income.values())
    before_profit = before_total_inc - before_total_exp

    # Run Kitchen
    kitchen = HNCSoupKitchen(soup)
    report = kitchen.audit_and_correct()

    # Snapshot AFTER
    after_expenses = dict(soup.get_sa103_summary())
    after_income = dict(soup.get_income_by_trade())
    after_total_exp = sum(after_expenses.values())
    after_total_inc = sum(after_income.values())
    after_profit = after_total_inc - after_total_exp

    print(f"\n{'='*80}")
    print(f"  TAX YEAR {year_key}")
    print(f"{'='*80}")

    print(f"\n  EXPENSES BY SA103 BOX — BEFORE vs AFTER:")
    print(f"  {'Box':<8} {'Category':<35} {'BEFORE':>12} {'AFTER':>12} {'CHANGE':>12}")
    print(f"  {'-'*8} {'-'*35} {'-'*12} {'-'*12} {'-'*12}")

    all_cats = sorted(set(list(before_expenses.keys()) + list(after_expenses.keys())))
    for cat in all_cats:
        info = SA103_CATEGORIES.get(cat, {})
        box = info.get("box", "?")
        label = info.get("label", cat)[:35]
        b = before_expenses.get(cat, 0)
        a = after_expenses.get(cat, 0)
        change = a - b
        marker = "▲" if change > 0 else ("▼" if change < 0 else "—")
        print(f"  {box:<8} {label:<35} £{b:>10,.2f} £{a:>10,.2f} {marker} £{abs(change):>9,.2f}")

    print(f"  {'':8} {'TOTAL':<35} £{before_total_exp:>10,.2f} £{after_total_exp:>10,.2f}")

    print(f"\n  INCOME BY TRADE — BEFORE vs AFTER:")
    all_trades = sorted(set(list(before_income.keys()) + list(after_income.keys())))
    for trade in all_trades:
        b = before_income.get(trade, 0)
        a = after_income.get(trade, 0)
        change = a - b
        if change != 0:
            print(f"    {trade:<20} £{b:>10,.2f} → £{a:>10,.2f} ({'+' if change > 0 else ''}{change:,.2f})")
        else:
            print(f"    {trade:<20} £{b:>10,.2f} (unchanged)")

    print(f"\n  NET PROFIT: £{before_profit:,.2f} → £{after_profit:,.2f}")

    # Print full Kitchen report
    print(kitchen.print_report())

print("\n" + "=" * 80)
print("  DONE")
print("=" * 80)
