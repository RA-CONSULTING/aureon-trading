"""
SUMUP FLOW ANALYSIS — Understanding the money movement
========================================================
The SumUp card terminal creates a specific pattern:
  1. Customer pays via card → SumUp collects
  2. SumUp batches and settles to bank account (appears as credit)
  3. SumUp may deduct fees before settlement
  4. Owner may move money between SumUp balance and bank

We need to understand what's real revenue, what's fees,
and what's just money shuffling.

Aureon Creator / Aureon Research — April 2026
"""

import sys
import os
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.hnc_import import HNCImportEngine

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


def main():
    print("=" * 75)
    print("  SUMUP & MONEY FLOW ANALYSIS")
    print("  Aureon Creator | Q1 2026")
    print("=" * 75)

    csv_files = find_csv_files()
    importer = HNCImportEngine()
    for filepath in csv_files:
        csv_text = read_utf16_csv(filepath)
        importer.import_csv_string(csv_text, os.path.basename(filepath))

    all_txns = importer.get_bank_transactions()

    # ---- Categorise every transaction by its nature ----
    sumup_out = []
    sumup_in = []  # if any
    food_venture_in = []
    grove_in = []
    heron_in = []
    rna_in = []
    self_transfers = []
    cashback = []
    wages = []
    rent = []
    personal_spend = []
    business_costs = []
    cash_withdrawals = []
    other = []

    for t in all_txns:
        desc = t["description"].lower()
        d = t["direction"]
        amt = t["amount"]

        if "sumup" in desc:
            if d == "out":
                sumup_out.append(t)
            else:
                sumup_in.append(t)
        elif "aureon creator gary" in desc:
            self_transfers.append(t)
        elif "cashback" in desc:
            cashback.append(t)
        elif "food venture" in desc:
            food_venture_in.append(t)
        elif "construction client alpha" in desc:
            grove_in.append(t)
        elif "construction client beta" in desc:
            heron_in.append(t)
        elif "aureon consulting entity" in desc:
            rna_in.append(t)
        elif any(name in desc for name in ["subcontractor alpha", "subcontractor beta", "subcontractor beta",
                                            "aureon queen anchor", "subcontractor gamma", "subcontractor delta",
                                            "subcontractor epsilon", "equipment seller"]):
            wages.append(t)
        elif any(name in desc for name in ["landlord alpha", "property provider"]):
            rent.append(t)
        elif t.get("category") in ("Cash",) or "blackstaff" in desc:
            cash_withdrawals.append(t)
        elif t.get("category") in ("Personal",):
            personal_spend.append(t)
        elif d == "out":
            business_costs.append(t)
        else:
            other.append(t)

    # ---- SumUp Analysis ----
    print("\n  === SUMUP TRANSACTIONS ===")
    sumup_total_out = sum(t["amount"] for t in sumup_out)
    sumup_total_in = sum(t["amount"] for t in sumup_in)
    print(f"  SumUp OUT (bank → SumUp): {len(sumup_out)} txns, £{sumup_total_out:,.2f}")
    print(f"  SumUp IN (SumUp → bank):  {len(sumup_in)} txns, £{sumup_total_in:,.2f}")
    print()

    print("  SumUp OUT detail:")
    for t in sorted(sumup_out, key=lambda x: x["date"]):
        print(f"    {t['date']}  £{t['amount']:>9,.2f}  {t['description'][:40]}")

    print(f"\n  SumUp IN detail:")
    for t in sorted(sumup_in, key=lambda x: x["date"]):
        print(f"    {t['date']}  £{t['amount']:>9,.2f}  {t['description'][:40]}")

    # ---- Food Venture Analysis ----
    print(f"\n  === RAVENOUS CREDITS ===")
    rav_total = sum(t["amount"] for t in food_venture_in)
    print(f"  Food Venture IN: {len(food_venture_in)} txns, £{rav_total:,.2f}")
    for t in sorted(food_venture_in, key=lambda x: x["date"]):
        print(f"    {t['date']}  £{t['amount']:>9,.2f}  {t['description'][:40]}")

    # ---- Self-Transfer Analysis ----
    print(f"\n  === SELF-TRANSFERS ===")
    self_in = sum(t["amount"] for t in self_transfers if t["direction"] == "in")
    self_out = sum(t["amount"] for t in self_transfers if t["direction"] == "out")
    print(f"  Self IN:  £{self_in:,.2f}")
    print(f"  Self OUT: £{self_out:,.2f}")
    for t in sorted(self_transfers, key=lambda x: x["date"]):
        print(f"    {t['date']}  {t['direction']:>3}  £{t['amount']:>9,.2f}  {t['description'][:40]}")

    # ---- Day-by-day matching ----
    print(f"\n  === DAY-BY-DAY FLOW (SumUp + Food Venture) ===")
    print(f"  Looking for patterns: does SumUp OUT match Food Venture IN?")
    print()

    # Group by date
    by_date = defaultdict(list)
    for t in all_txns:
        by_date[t["date"]].append(t)

    for date_key in sorted(by_date.keys()):
        txns = by_date[date_key]
        has_sumup = any("sumup" in t["description"].lower() for t in txns)
        has_food_venture = any("food venture" in t["description"].lower() for t in txns)

        if has_sumup or has_food_venture:
            day_in = sum(t["amount"] for t in txns if t["direction"] == "in")
            day_out = sum(t["amount"] for t in txns if t["direction"] == "out")
            print(f"  {date_key}  (IN £{day_in:>9,.2f}  OUT £{day_out:>9,.2f}  NET £{day_in-day_out:>9,.2f})")
            for t in txns:
                marker = ""
                if "sumup" in t["description"].lower():
                    marker = " [SUMUP]"
                elif "food venture" in t["description"].lower():
                    marker = " [RAVENOUS]"
                elif "grove" in t["description"].lower():
                    marker = " [GROVE]"
                print(f"      {t['direction']:>3}  £{t['amount']:>9,.2f}  {t['description'][:35]}{marker}")

    # ---- The real picture ----
    print(f"\n  {'='*60}")
    print(f"  MONEY FLOW SUMMARY")
    print(f"  {'='*60}")
    print(f"\n  MONEY IN (genuine external income):")
    print(f"    Construction Client Alpha Ltd:        £{sum(t['amount'] for t in grove_in):>10,.2f}  ({len(grove_in)} txns)")
    print(f"    Construction Client Beta Limited:        £{sum(t['amount'] for t in heron_in):>10,.2f}  ({len(heron_in)} txns)")
    print(f"    Aureon Consulting Entity:            £{sum(t['amount'] for t in rna_in):>10,.2f}  ({len(rna_in)} txns)")
    print(f"    Food Venture (SumUp settle):   £{rav_total:>10,.2f}  ({len(food_venture_in)} txns)")
    print(f"    Cashback:                  £{sum(t['amount'] for t in cashback):>10,.2f}  ({len(cashback)} txns)")
    total_real_in = sum(t['amount'] for t in grove_in) + sum(t['amount'] for t in heron_in) + \
                    sum(t['amount'] for t in rna_in) + rav_total
    print(f"    TOTAL REAL INCOME:         £{total_real_in:>10,.2f}")

    print(f"\n  MONEY OUT (genuine expenses):")
    print(f"    Wages & Subcontractors:    £{sum(t['amount'] for t in wages):>10,.2f}  ({len(wages)} txns)")
    print(f"    Rent:                      £{sum(t['amount'] for t in rent):>10,.2f}  ({len(rent)} txns)")
    print(f"    Business costs (food/fuel):£{sum(t['amount'] for t in business_costs):>10,.2f}  ({len(business_costs)} txns)")
    print(f"    Cash withdrawals:          £{sum(t['amount'] for t in cash_withdrawals):>10,.2f}  ({len(cash_withdrawals)} txns)")
    print(f"    Personal:                  £{sum(t['amount'] for t in personal_spend):>10,.2f}  ({len(personal_spend)} txns)")
    total_real_out = sum(t['amount'] for t in wages) + sum(t['amount'] for t in rent) + \
                     sum(t['amount'] for t in business_costs) + sum(t['amount'] for t in cash_withdrawals) + \
                     sum(t['amount'] for t in personal_spend)
    print(f"    TOTAL REAL EXPENSES:       £{total_real_out:>10,.2f}")

    print(f"\n  INTERNAL MOVEMENT (not income or expense):")
    print(f"    SumUp OUT (to terminal):   £{sumup_total_out:>10,.2f}  ({len(sumup_out)} txns)")
    print(f"    Self-transfers:            £{self_out:>10,.2f} out / £{self_in:>10,.2f} in")

    print(f"\n  NET TRADING PROFIT:          £{total_real_in - total_real_out:>10,.2f}")

    # ---- But wait — SumUp OUT is interesting ----
    print(f"\n  {'='*60}")
    print(f"  KEY INSIGHT: SumUp OUT = £{sumup_total_out:,.2f}")
    print(f"  {'='*60}")
    print(f"  This is money going FROM the bank TO SumUp.")
    print(f"  But Food Venture takes card payments VIA SumUp.")
    print(f"  SumUp settles (pays back) as 'Food Venture P' credits.")
    print(f"  Food Venture total IN = £{rav_total:,.2f}")
    print(f"")
    print(f"  If SumUp OUT > Food Venture IN, the difference could be:")
    print(f"    - SumUp fees retained")
    print(f"    - Money moved to SumUp for refunds")
    print(f"    - Float/timing differences")
    print(f"")
    print(f"  SumUp OUT - Food Venture IN = £{sumup_total_out - rav_total:,.2f}")
    print(f"")
    print(f"  But MORE LIKELY: SumUp OUT entries are NOT transfers TO SumUp.")
    print(f"  They're probably PURCHASES/EXPENSES paid via the SumUp-linked card.")
    print(f"  The description 'Gary leckey Sumup' might just be the card ID.")
    print(f"")
    print(f"  CRITICAL: We need to check if 'Gary leckey Sumup' debits are")
    print(f"  actually card purchases (expenses) or terminal transfers.")
    print(f"  The fact they vary wildly (£0.11 to £2,447) suggests MIXED usage.")
    print()

    # ---- Analyse SumUp amounts ----
    print(f"  SumUp OUT amount distribution:")
    small = [t for t in sumup_out if t["amount"] < 10]
    medium = [t for t in sumup_out if 10 <= t["amount"] < 200]
    large = [t for t in sumup_out if 200 <= t["amount"] < 1000]
    xlarge = [t for t in sumup_out if t["amount"] >= 1000]

    print(f"    Under £10:      {len(small)} txns  (likely fees)")
    for t in small:
        print(f"      {t['date']}  £{t['amount']:>9,.2f}")
    print(f"    £10-£200:       {len(medium)} txns  (could be either)")
    for t in medium:
        print(f"      {t['date']}  £{t['amount']:>9,.2f}")
    print(f"    £200-£1000:     {len(large)} txns  (likely payouts/transfers)")
    for t in large:
        print(f"      {t['date']}  £{t['amount']:>9,.2f}")
    print(f"    £1000+:         {len(xlarge)} txns  (bulk transfers)")
    for t in xlarge:
        print(f"      {t['date']}  £{t['amount']:>9,.2f}")

    # ---- Check same-day pairs ----
    print(f"\n  === SAME-DAY SumUp OUT + Food Venture IN PAIRS ===")
    for date_key in sorted(by_date.keys()):
        txns = by_date[date_key]
        su_outs = [t for t in txns if "sumup" in t["description"].lower() and t["direction"] == "out"]
        rav_ins = [t for t in txns if "food venture" in t["description"].lower() and t["direction"] == "in"]

        if su_outs and rav_ins:
            su_total = sum(t["amount"] for t in su_outs)
            rav_total_day = sum(t["amount"] for t in rav_ins)
            diff = abs(su_total - rav_total_day)
            match = "MATCH" if diff < 5 else f"DIFF £{diff:,.2f}"

            print(f"    {date_key}:")
            for t in su_outs:
                print(f"      OUT £{t['amount']:>9,.2f}  SumUp")
            for t in rav_ins:
                print(f"       IN £{t['amount']:>9,.2f}  Food Venture")
            print(f"      → SumUp OUT: £{su_total:,.2f}  Food Venture IN: £{rav_total_day:,.2f}  [{match}]")

    print(f"\n  {'='*75}")
    print(f"  ANALYSIS COMPLETE")
    print(f"  {'='*75}")


if __name__ == "__main__":
    main()
