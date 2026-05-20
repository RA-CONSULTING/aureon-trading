"""
REAL DATA TEST — Aureon Creator's Bank Statements
================================================
Runs the 3 real uploaded CSV files (Jan/Feb/Mar 2026) through
the full HNC pipeline: Import → Queen → Export.

Aureon Creator / Aureon Research — April 2026
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.hnc_import import HNCImportEngine, parse_amount, parse_date

# ========================================================================
# LOCATE THE REAL CSV FILES
# ========================================================================

SEARCH_DIRS = [
    os.path.join(os.path.dirname(__file__), "..", "..", "uploads"),
    os.path.join(os.path.dirname(__file__), "..", "data"),
    "/sessions/upbeat-stoic-hamilton/mnt/uploads",
]


def find_csv_files():
    """Find Gary's uploaded CSV files — deduplicated by filename."""
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
    """Read a UTF-16 encoded CSV file and return decoded text."""
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
# MAIN TEST
# ========================================================================

def main():
    print("=" * 70)
    print("  HNC REAL DATA TEST — Aureon Creator Bank Statements")
    print("  Jan / Feb / Mar 2026")
    print("=" * 70)

    csv_files = find_csv_files()

    if not csv_files:
        print("\n  [!] No CSV files found.")
        for d in SEARCH_DIRS:
            exists = os.path.isdir(d)
            print(f"    {d}  {'EXISTS' if exists else 'NOT FOUND'}")
            if exists:
                for f in os.listdir(d):
                    print(f"      - {f}")
        return

    print(f"\n  Found {len(csv_files)} CSV files:")
    for f in csv_files:
        print(f"    - {os.path.basename(f)}")

    # ================================================================
    # STAGE 1: IMPORT
    # ================================================================
    print("\n" + "-" * 70)
    print("  STAGE 1: IMPORT")
    print("-" * 70)

    importer = HNCImportEngine()

    for filepath in csv_files:
        basename = os.path.basename(filepath)
        print(f"\n  Importing: {basename}")

        try:
            csv_text = read_utf16_csv(filepath)
            lines = csv_text.strip().split("\n")
            print(f"    Decoded — {len(lines)} lines")
            print(f"    Header: {lines[0][:80]}...")
        except Exception as e:
            print(f"    [ERROR] {e}")
            continue

        result = importer.import_csv_string(csv_text, basename)
        print(f"    Format: {result.format_detected}")
        print(f"    Rows: {result.rows_read} read / {result.rows_imported} imported")
        if result.date_range[0]:
            print(f"    Dates: {result.date_range[0]} to {result.date_range[1]}")
        print(f"    In:  £{result.total_in:>10,.2f}   Out: £{result.total_out:>10,.2f}")
        for e in result.errors:
            print(f"    [ERROR] {e}")
        for w in result.warnings:
            print(f"    [WARN] {w}")

    all_txns = importer.get_bank_transactions()
    print(f"\n  TOTAL TRANSACTIONS: {len(all_txns)}")

    if not all_txns:
        print("  [!] No transactions — stopping.")
        return

    # Breakdown
    income_txns = [t for t in all_txns if t["direction"] == "in"]
    expense_txns = [t for t in all_txns if t["direction"] == "out"]
    total_income = sum(t["amount"] for t in income_txns)
    total_expenses = sum(t["amount"] for t in expense_txns)

    print(f"  Income:   {len(income_txns)} txns  £{total_income:>10,.2f}")
    print(f"  Expenses: {len(expense_txns)} txns  £{total_expenses:>10,.2f}")
    print(f"  Net: £{total_income - total_expenses:>10,.2f}")

    # Top counterparties
    print("\n  --- Top Income Sources ---")
    income_by_cp = {}
    for t in income_txns:
        cp = t["description"][:40]
        income_by_cp[cp] = income_by_cp.get(cp, 0) + t["amount"]
    for cp, amt in sorted(income_by_cp.items(), key=lambda x: -x[1])[:10]:
        print(f"    £{amt:>10,.2f}  {cp}")

    print("\n  --- Top Expense Destinations ---")
    expense_by_cp = {}
    for t in expense_txns:
        cp = t["description"][:40]
        expense_by_cp[cp] = expense_by_cp.get(cp, 0) + t["amount"]
    for cp, amt in sorted(expense_by_cp.items(), key=lambda x: -x[1])[:10]:
        print(f"    £{amt:>10,.2f}  {cp}")

    # Categories
    print("\n  --- Category Breakdown ---")
    cat_totals_in = {}
    cat_totals_out = {}
    for t in all_txns:
        cat = t.get("category", "Unknown") or "Unknown"
        if t["direction"] == "in":
            cat_totals_in[cat] = cat_totals_in.get(cat, 0) + t["amount"]
        else:
            cat_totals_out[cat] = cat_totals_out.get(cat, 0) + t["amount"]

    all_cats = set(list(cat_totals_in.keys()) + list(cat_totals_out.keys()))
    for cat in sorted(all_cats):
        cin = cat_totals_in.get(cat, 0)
        cout = cat_totals_out.get(cat, 0)
        print(f"    {cat:<25}  IN £{cin:>9,.2f}  OUT £{cout:>9,.2f}")

    # ================================================================
    # STAGE 2: QUEEN PROCESSING
    # ================================================================
    print("\n" + "-" * 70)
    print("  STAGE 2: QUEEN PROCESSING")
    print("-" * 70)

    pipeline_result = None
    try:
        from core.hnc_queen import HNCQueen

        queen = HNCQueen(
            entity_name="Aureon Creator t/a Food Venture",
            entity_type="sole_trader",
            trade_sector="food_hospitality",
            tax_year="2025/26",
            vat_registered=False,
        )

        pipeline_result = queen.process(
            bank_transactions=all_txns,
            gross_turnover=total_income,
            allowable_expenses=total_expenses,
            trading_profit=total_income - total_expenses,
        )

        print(f"\n  Status: {pipeline_result.status}")

        # Stages
        for stage in pipeline_result.stages:
            name = getattr(stage, "name", "?")
            status = getattr(stage, "status", "?")
            print(f"    {name}: {status}")

        # Tax computation
        tax = pipeline_result.tax_computation
        if tax:
            print("\n  --- Tax Computation ---")
            if hasattr(tax, "__dict__"):
                for k, v in tax.__dict__.items():
                    if isinstance(v, (int, float)) and v != 0:
                        print(f"    {k}: £{v:,.2f}")
            elif isinstance(tax, dict):
                for k, v in tax.items():
                    if isinstance(v, (int, float)) and v != 0:
                        print(f"    {k}: £{v:,.2f}")

        # VAT
        vat = pipeline_result.vat_return
        if vat:
            print("\n  --- VAT Return ---")
            if isinstance(vat, dict):
                for k, v in vat.items():
                    if isinstance(v, (int, float)):
                        print(f"    {k}: £{v:,.2f}")

        # Inspector
        inspector = pipeline_result.inspector_report
        if inspector:
            verdict = getattr(inspector, "verdict", None) if hasattr(inspector, "verdict") else (inspector.get("verdict") if isinstance(inspector, dict) else None)
            score = getattr(inspector, "risk_score", None) if hasattr(inspector, "risk_score") else (inspector.get("risk_score") if isinstance(inspector, dict) else None)
            findings = getattr(inspector, "findings", []) if hasattr(inspector, "findings") else (inspector.get("findings", []) if isinstance(inspector, dict) else [])

            print(f"\n  INSPECTOR VERDICT: {verdict}")
            print(f"  Risk Score: {score}/100")
            print(f"  Findings: {len(findings)}")

            for f in findings[:20]:
                if isinstance(f, dict):
                    sev = f.get("severity", "?")
                    msg = f.get("message", f.get("description", ""))
                else:
                    sev = getattr(f, "severity", "?")
                    msg = getattr(f, "message", getattr(f, "description", ""))
                print(f"    [{sev}] {str(msg)[:70]}")

        # SA100 boxes
        sa100 = pipeline_result.sa100_boxes
        if sa100:
            print("\n  --- SA100 Boxes ---")
            for k, v in sa100.items():
                print(f"    {k}: {v}")

    except Exception as e:
        print(f"  [ERROR] Queen failed: {e}")
        import traceback
        traceback.print_exc()

    # ================================================================
    # STAGE 3: DOCUMENT GENERATION
    # ================================================================
    print("\n" + "-" * 70)
    print("  STAGE 3: DOCUMENT GENERATION")
    print("-" * 70)

    output_dir = os.path.join(os.path.dirname(__file__), "..", "output", "real_data")
    os.makedirs(output_dir, exist_ok=True)

    try:
        from core.hnc_export import (
            export_pnl_pdf,
            export_tax_summary_pdf,
            export_ledger_xlsx,
            export_management_accounts_xlsx,
            export_trial_balance_xlsx,
        )

        # P&L
        try:
            pnl_data = {
                "entity_name": "Aureon Creator t/a Food Venture",
                "period": "01 January 2026 — 31 March 2026",
                "turnover": total_income,
                "cost_of_sales": sum(t["amount"] for t in expense_txns if t.get("category") == "Materials and Stock"),
                "gross_profit": total_income - sum(t["amount"] for t in expense_txns if t.get("category") == "Materials and Stock"),
                "admin_expenses": sum(t["amount"] for t in expense_txns if t.get("category") in ("Fees and Services",)),
                "other_expenses": sum(t["amount"] for t in expense_txns if t.get("category") not in ("Materials and Stock", "Fees and Services")),
                "total_expenses": total_expenses,
                "net_profit": total_income - total_expenses,
                "expenses": {
                    "Materials & Stock": sum(t["amount"] for t in expense_txns if t.get("category") == "Materials and Stock"),
                    "Travel": sum(t["amount"] for t in expense_txns if t.get("category") == "Travel"),
                    "Food & Drink": sum(t["amount"] for t in expense_txns if t.get("category") == "Food and Drink"),
                    "Fees & Services": sum(t["amount"] for t in expense_txns if t.get("category") == "Fees and Services"),
                    "Personal": sum(t["amount"] for t in expense_txns if t.get("category") == "Personal"),
                    "Cash Withdrawals": sum(t["amount"] for t in expense_txns if t.get("category") == "Cash"),
                    "Wages & Subcontractors": sum(t["amount"] for t in expense_txns
                        if any(name in t["description"].lower() for name in
                               ["subcontractor alpha", "subcontractor beta", "aureon queen anchor",
                                "subcontractor gamma", "subcontractor delta", "equipment seller", "subcontractor epsilon"])),
                    "Rent & Property": sum(t["amount"] for t in expense_txns
                        if any(name in t["description"].lower() for name in
                               ["landlord alpha", "property provider"])),
                    "SumUp Terminal Fees": sum(t["amount"] for t in expense_txns
                        if "sumup" in t["description"].lower()),
                    "Other": sum(t["amount"] for t in expense_txns
                        if t.get("category", "Other") == "Other"
                        and "sumup" not in t["description"].lower()
                        and not any(name in t["description"].lower() for name in
                               ["subcontractor alpha", "subcontractor beta", "aureon queen anchor",
                                "subcontractor gamma", "subcontractor delta", "equipment seller",
                                "subcontractor epsilon", "landlord alpha", "property provider"])),
                },
            }
            fpath = os.path.join(output_dir, "pnl.pdf")
            export_pnl_pdf(pnl_data, fpath)
            print(f"  [OK] P&L PDF — {os.path.getsize(fpath):,} bytes")
        except Exception as e:
            print(f"  [ERROR] P&L PDF: {e}")

        # Tax Summary
        try:
            taxable = max(0, (total_income - total_expenses) - 12570)
            if taxable <= 37700:
                income_tax = taxable * 0.20
            else:
                income_tax = 37700 * 0.20 + (taxable - 37700) * 0.40

            tax_data = {
                "entity_name": "Aureon Creator",
                "period": "Q1 2026 (01 Jan — 31 Mar)",
                "tax_year": "2025/26",
                "turnover": total_income,
                "allowable_expenses": total_expenses,
                "net_profit": total_income - total_expenses,
                "personal_allowance": 12570,
                "taxable_income": taxable,
                "income_tax": income_tax,
                "ni_class2": 179.40,  # £3.45/week * 52 (annual)
                "ni_class4": max(0, (total_income - total_expenses - 12570)) * 0.06 if (total_income - total_expenses) > 12570 else 0,
                "total_tax_due": income_tax + 179.40 + (max(0, (total_income - total_expenses - 12570)) * 0.06 if (total_income - total_expenses) > 12570 else 0),
            }
            fpath = os.path.join(output_dir, "tax_summary.pdf")
            export_tax_summary_pdf(tax_data, fpath)
            print(f"  [OK] Tax Summary PDF — {os.path.getsize(fpath):,} bytes")
        except Exception as e:
            print(f"  [ERROR] Tax Summary PDF: {e}")

        # General Ledger
        try:
            fpath = os.path.join(output_dir, "general_ledger.xlsx")
            export_ledger_xlsx(all_txns, fpath)
            print(f"  [OK] General Ledger XLSX — {os.path.getsize(fpath):,} bytes")
        except Exception as e:
            print(f"  [ERROR] Ledger XLSX: {e}")

        # Trial Balance
        try:
            # Build accounts from categories
            accounts = []
            for cat in sorted(all_cats):
                dr = cat_totals_out.get(cat, 0)
                cr = cat_totals_in.get(cat, 0)
                accounts.append({
                    "code": f"{'1' if cr > dr else '5'}{'len(accounts)+1:03d'}",
                    "name": cat,
                    "debit": dr,
                    "credit": cr,
                })
            fpath = os.path.join(output_dir, "trial_balance.xlsx")
            export_trial_balance_xlsx(accounts, fpath)
            print(f"  [OK] Trial Balance XLSX — {os.path.getsize(fpath):,} bytes")
        except Exception as e:
            print(f"  [ERROR] Trial Balance XLSX: {e}")

        # Management Accounts
        try:
            # Build monthly data
            monthly = {}
            for t in all_txns:
                month_key = t["date"][:7]  # YYYY-MM
                if month_key not in monthly:
                    monthly[month_key] = {"month": month_key, "income": 0, "expenses": 0}
                if t["direction"] == "in":
                    monthly[month_key]["income"] += t["amount"]
                else:
                    monthly[month_key]["expenses"] += t["amount"]

            for m in monthly.values():
                m["net_profit"] = m["income"] - m["expenses"]

            monthly_list = [monthly[k] for k in sorted(monthly.keys())]
            fpath = os.path.join(output_dir, "management_accounts.xlsx")
            export_management_accounts_xlsx(monthly_list, fpath)
            print(f"  [OK] Management Accounts XLSX — {os.path.getsize(fpath):,} bytes")
        except Exception as e:
            print(f"  [ERROR] Management Accounts XLSX: {e}")

    except ImportError as e:
        print(f"  [ERROR] Missing dependency: {e}")
        print("  Attempting pip install...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install",
                       "reportlab", "openpyxl", "--break-system-packages", "-q"])
        print("  Dependencies installed. Re-run test.")
    except Exception as e:
        print(f"  [ERROR] Export stage: {e}")
        import traceback
        traceback.print_exc()

    # Output listing
    print(f"\n  Output: {output_dir}")
    if os.path.isdir(output_dir):
        for f in sorted(os.listdir(output_dir)):
            fpath = os.path.join(output_dir, f)
            size = os.path.getsize(fpath)
            print(f"    {f}  ({size:,} bytes)")

    # ================================================================
    # FULL TRANSACTION LISTING
    # ================================================================
    print("\n" + "-" * 70)
    print("  FULL TRANSACTION LISTING")
    print("-" * 70)
    print(f"  {'Date':<12} {'Dir':>3} {'Amount':>10} {'Category':<22} {'Description'}")
    print(f"  {'-'*12} {'---':>3} {'-'*10} {'-'*22} {'-'*35}")
    for t in sorted(all_txns, key=lambda x: x["date"]):
        print(f"  {t['date']:<12} {t['direction']:>3} £{t['amount']:>9,.2f} "
              f"{(t.get('category','') or ''):<22} {t['description'][:35]}")

    print("\n" + "=" * 70)
    print("  REAL DATA TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
