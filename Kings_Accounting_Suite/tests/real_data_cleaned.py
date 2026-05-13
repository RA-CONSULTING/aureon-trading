"""
REAL DATA CLEANED — Aureon Creator's Bank Statements
===================================================
Strips out internal transfers (SumUp cashouts, self-transfers)
to show the REAL trading picture.

Money moves. SumUp terminal → bank account is not income or expense,
it's the same money changing pockets.

Aureon Creator / Aureon Research — April 2026
"""

import sys
import os
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.hnc_import import HNCImportEngine

# ========================================================================
# FILE HANDLING
# ========================================================================

SEARCH_DIRS = [
    os.path.join(os.path.dirname(__file__), "..", "..", "uploads"),
    os.path.join(os.path.dirname(__file__), "..", "data"),
    "/sessions/upbeat-stoic-hamilton/mnt/uploads",
]


def find_csv_files():
    seen = set()
    csv_files = []
    for d in SEARCH_DIRS:
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if f.endswith(".csv") and "Statement" in f and f not in seen:
                seen.add(f)
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


# ========================================================================
# TRANSFER DETECTION
# ========================================================================

def is_internal_transfer(txn):
    """
    Identify internal transfers that shouldn't count as income or expense.

    SumUp pattern: Gary pays via card terminal → SumUp collects →
    SumUp pays out to bank account. The OUT to "Gary leckey Sumup" and
    the matching IN are the same money moving.

    Self-transfers: "aureon creator gary" — moving between own accounts.
    """
    desc = txn["description"].lower()

    # SumUp terminal transfers — NOT a real expense
    if "sumup" in desc:
        return True, "SumUp terminal transfer"

    # Self-transfers between own accounts
    if desc.startswith("aureon creator gary") or desc == "aureon creator gary":
        return True, "Self-transfer"

    # Cashback rewards — tiny amounts, not real income
    if "cashback" in desc:
        return True, "Cashback reward"

    return False, ""


def classify_transaction(txn):
    """
    Classify a real (non-transfer) transaction into business categories.
    Uses the bank's own Category field plus description matching.
    """
    desc = txn["description"].lower()
    bank_cat = txn.get("category", "Other") or "Other"
    direction = txn["direction"]

    # === INCOME CLASSIFICATION ===
    if direction == "in":
        if "construction client alpha" in desc:
            return "Construction Income"
        elif "construction client beta" in desc:
            return "Construction Income"
        elif "food venture" in desc:
            return "Food Business Income (Food Venture)"
        elif "aureon consulting entity" in desc:
            return "Consulting Income"
        else:
            return f"Other Income"

    # === EXPENSE CLASSIFICATION ===

    # Wages & subcontractors
    wage_names = [
        "subcontractor alpha", "subcontractor beta", "subcontractor beta",
        "aureon queen anchor", "subcontractor gamma", "subcontractor delta",
        "subcontractor epsilon",
    ]
    if any(name in desc for name in wage_names):
        return "Wages & Subcontractors"

    # Equipment Seller — looks like equipment purchase (Quest 3 gumtree)
    if "equipment seller" in desc:
        return "Equipment / Capital"

    # Rent & property
    if "landlord alpha" in desc:
        return "Rent (Landlord Alpha)"
    if "property provider" in desc:
        return "Rent (Property Provider)"

    # Use bank categories where they're meaningful
    if bank_cat == "Travel":
        return "Motor & Travel"
    if bank_cat == "Food and Drink":
        # Check if it's wholesale (Musgrave) vs personal
        if "musgrave" in desc:
            return "Cost of Sales (Food Wholesale)"
        return "Food & Subsistence"
    if bank_cat == "Materials and Stock":
        return "Materials & Stock"
    if bank_cat == "Cash":
        return "Cash Withdrawals"
    if bank_cat == "Personal":
        return "Personal (Non-Allowable)"
    if bank_cat == "Fees and Services":
        if "google" in desc:
            return "Software & Subscriptions"
        if "monthly subscription" in desc:
            return "Software & Subscriptions"
        return "Professional Fees"

    return "Other Expenses"


# ========================================================================
# MAIN
# ========================================================================

def main():
    print("=" * 75)
    print("  HNC REAL DATA — CLEANED ANALYSIS")
    print("  Aureon Creator | Q1 2026 (Jan–Mar)")
    print("  Internal transfers stripped — real trading picture")
    print("=" * 75)

    # Import
    csv_files = find_csv_files()
    if not csv_files:
        print("  No CSV files found.")
        return

    importer = HNCImportEngine()
    for filepath in csv_files:
        csv_text = read_utf16_csv(filepath)
        importer.import_csv_string(csv_text, os.path.basename(filepath))

    all_txns = importer.get_bank_transactions()
    print(f"\n  Raw transactions: {len(all_txns)}")

    # ---- Separate transfers from real transactions ----
    real_txns = []
    transfers = []

    for t in all_txns:
        is_transfer, reason = is_internal_transfer(t)
        if is_transfer:
            transfers.append((t, reason))
        else:
            real_txns.append(t)

    transfer_in = sum(t["amount"] for t, _ in transfers if t["direction"] == "in")
    transfer_out = sum(t["amount"] for t, _ in transfers if t["direction"] == "out")

    print(f"  Internal transfers removed: {len(transfers)}")
    print(f"    Transfer IN total:  £{transfer_in:>10,.2f}")
    print(f"    Transfer OUT total: £{transfer_out:>10,.2f}")
    print(f"    Net transfer flow:  £{transfer_in - transfer_out:>10,.2f}")
    print(f"  Real transactions: {len(real_txns)}")

    # ---- Transfer detail ----
    print(f"\n  --- Internal Transfers (removed) ---")
    for t, reason in sorted(transfers, key=lambda x: x[0]["date"]):
        print(f"    {t['date']}  {t['direction']:>3}  £{t['amount']:>9,.2f}  "
              f"[{reason}]  {t['description'][:35]}")

    # ---- Classify real transactions ----
    income_txns = [t for t in real_txns if t["direction"] == "in"]
    expense_txns = [t for t in real_txns if t["direction"] == "out"]
    total_income = sum(t["amount"] for t in income_txns)
    total_expenses = sum(t["amount"] for t in expense_txns)
    net_profit = total_income - total_expenses

    print(f"\n  {'='*60}")
    print(f"  REAL TRADING POSITION — Q1 2026")
    print(f"  {'='*60}")
    print(f"  Gross Income:   £{total_income:>10,.2f}")
    print(f"  Total Expenses: £{total_expenses:>10,.2f}")
    print(f"  NET PROFIT:     £{net_profit:>10,.2f}")
    print(f"  {'='*60}")

    # ---- Income by category ----
    print(f"\n  --- INCOME BREAKDOWN ---")
    income_cats = defaultdict(lambda: {"total": 0, "count": 0, "items": []})
    for t in income_txns:
        cat = classify_transaction(t)
        income_cats[cat]["total"] += t["amount"]
        income_cats[cat]["count"] += 1
        income_cats[cat]["items"].append(t)

    for cat, data in sorted(income_cats.items(), key=lambda x: -x[1]["total"]):
        print(f"    {cat:<40}  £{data['total']:>9,.2f}  ({data['count']} txns)")

    # ---- Expense by category ----
    print(f"\n  --- EXPENSE BREAKDOWN ---")
    expense_cats = defaultdict(lambda: {"total": 0, "count": 0, "items": []})
    for t in expense_txns:
        cat = classify_transaction(t)
        expense_cats[cat]["total"] += t["amount"]
        expense_cats[cat]["count"] += 1
        expense_cats[cat]["items"].append(t)

    allowable = 0
    non_allowable = 0

    for cat, data in sorted(expense_cats.items(), key=lambda x: -x[1]["total"]):
        # Flag non-allowable
        is_allowable = cat not in ("Personal (Non-Allowable)", "Cash Withdrawals", "Equipment / Capital")
        flag = "  ✓" if is_allowable else "  ✗ NON-ALLOWABLE"
        print(f"    {cat:<40}  £{data['total']:>9,.2f}  ({data['count']} txns){flag}")
        if is_allowable:
            allowable += data["total"]
        else:
            non_allowable += data["total"]

    # ---- Tax position ----
    print(f"\n  {'='*60}")
    print(f"  TAX POSITION — 2025/26")
    print(f"  {'='*60}")
    print(f"  Gross Turnover:       £{total_income:>10,.2f}")
    print(f"  Allowable Expenses:   £{allowable:>10,.2f}")
    print(f"  Non-Allowable:        £{non_allowable:>10,.2f}")
    print(f"  Adjusted Profit:      £{total_income - allowable:>10,.2f}")
    print()

    # Annualise (Q1 = 3 months of 12)
    annual_factor = 4  # rough — Q1 × 4
    est_annual_profit = (total_income - allowable) * annual_factor
    print(f"  ESTIMATED ANNUAL PROFIT (×4): £{est_annual_profit:>10,.2f}")

    personal_allowance = 12_570
    taxable = max(0, est_annual_profit - personal_allowance)

    # Income tax
    if taxable <= 37_700:
        income_tax = taxable * 0.20
    elif taxable <= 125_140:
        income_tax = 37_700 * 0.20 + (taxable - 37_700) * 0.40
    else:
        income_tax = 37_700 * 0.20 + 87_440 * 0.40 + (taxable - 125_140) * 0.45

    # NI Class 4
    if est_annual_profit > 12_570:
        ni4 = min(est_annual_profit - 12_570, 50_270 - 12_570) * 0.06
        if est_annual_profit > 50_270:
            ni4 += (est_annual_profit - 50_270) * 0.02
    else:
        ni4 = 0

    ni2 = 179.40  # £3.45/week × 52

    total_tax = income_tax + ni4 + ni2

    print(f"  Personal Allowance:   £{personal_allowance:>10,}")
    print(f"  Taxable Income:       £{taxable:>10,.2f}")
    print(f"  Income Tax (est):     £{income_tax:>10,.2f}")
    print(f"  NI Class 2:           £{ni2:>10,.2f}")
    print(f"  NI Class 4:           £{ni4:>10,.2f}")
    print(f"  TOTAL TAX (est ann.): £{total_tax:>10,.2f}")
    print(f"  {'='*60}")

    # ---- VAT threshold check ----
    est_annual_turnover = total_income * annual_factor
    vat_threshold = 90_000  # 2025/26 threshold
    print(f"\n  VAT CHECK:")
    print(f"    Estimated annual turnover: £{est_annual_turnover:>10,.2f}")
    print(f"    VAT threshold:             £{vat_threshold:>10,}")
    if est_annual_turnover > vat_threshold:
        print(f"    ⚠️  ABOVE THRESHOLD — VAT registration may be required")
    else:
        print(f"    Below threshold — no VAT registration needed")
        print(f"    Headroom: £{vat_threshold - est_annual_turnover:>10,.2f}")

    # ---- Monthly breakdown ----
    print(f"\n  --- MONTHLY BREAKDOWN (real transactions only) ---")
    monthly = defaultdict(lambda: {"income": 0, "expenses": 0, "txns": 0})
    for t in real_txns:
        m = t["date"][:7]
        monthly[m]["txns"] += 1
        if t["direction"] == "in":
            monthly[m]["income"] += t["amount"]
        else:
            monthly[m]["expenses"] += t["amount"]

    for m in sorted(monthly.keys()):
        d = monthly[m]
        net = d["income"] - d["expenses"]
        print(f"    {m}  IN £{d['income']:>9,.2f}  OUT £{d['expenses']:>9,.2f}  "
              f"NET £{net:>9,.2f}  ({d['txns']} txns)")

    # ---- Real transaction listing ----
    print(f"\n  --- REAL TRANSACTIONS ---")
    print(f"  {'Date':<12} {'Dir':>3} {'Amount':>10} {'Category':<35} {'Description'}")
    print(f"  {'-'*12} {'---':>3} {'-'*10} {'-'*35} {'-'*30}")
    for t in sorted(real_txns, key=lambda x: x["date"]):
        cat = classify_transaction(t)
        print(f"  {t['date']:<12} {t['direction']:>3} £{t['amount']:>9,.2f} "
              f"{cat:<35} {t['description'][:30]}")

    print(f"\n  {'='*75}")
    print(f"  ANALYSIS COMPLETE — {len(real_txns)} real transactions")
    print(f"  {len(transfers)} internal transfers excluded")
    print(f"  {'='*75}")

    # Return data for document generation
    return {
        "real_txns": real_txns,
        "transfers": transfers,
        "income_txns": income_txns,
        "expense_txns": expense_txns,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "allowable": allowable,
        "non_allowable": non_allowable,
        "net_profit": net_profit,
        "income_cats": dict(income_cats),
        "expense_cats": dict(expense_cats),
    }


if __name__ == "__main__":
    main()
