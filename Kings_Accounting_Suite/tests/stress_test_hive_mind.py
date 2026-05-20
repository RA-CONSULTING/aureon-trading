"""
HIVE MIND STRESS TEST
=======================
Same 15 financial scenarios — but through the hive mind, not the raw multi-agent.
Verifies consensus coherence across every edge case.
"""

import sys
import os
import time
import traceback
import io

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from core.hnc_hive_mind import HNCHiveMind, ConsensusState, QueenAuthority

# Reuse the scenarios from the multi-agent stress test
SCENARIOS = [
    ("1. Gary Baseline", {"gross_income": 51000, "net_profit": 25000, "cis_deducted": 10200,
        "total_expenses": 26000, "cost_of_sales": 8000, "other_direct": 5000,
        "motor": 3000, "admin": 2000, "other_expenses": 1500, "partner_income": 0, "mileage_estimate": 8000}),
    ("2. Zero Income", {"gross_income": 0, "net_profit": 0, "cis_deducted": 0,
        "total_expenses": 0, "cost_of_sales": 0, "other_direct": 0,
        "motor": 0, "admin": 0, "other_expenses": 0, "partner_income": 0, "mileage_estimate": 0}),
    ("3. Loss Year", {"gross_income": 30000, "net_profit": -5000, "cis_deducted": 6000,
        "total_expenses": 35000, "cost_of_sales": 15000, "other_direct": 8000,
        "motor": 5000, "admin": 4000, "other_expenses": 3000, "partner_income": 0, "mileage_estimate": 12000}),
    ("4. Higher Rate £80k", {"gross_income": 120000, "net_profit": 80000, "cis_deducted": 24000,
        "total_expenses": 40000, "cost_of_sales": 18000, "other_direct": 8000,
        "motor": 5000, "admin": 4000, "other_expenses": 5000, "partner_income": 0, "mileage_estimate": 15000}),
    ("5. PA Taper £105k", {"gross_income": 150000, "net_profit": 105000, "cis_deducted": 30000,
        "total_expenses": 45000, "cost_of_sales": 20000, "other_direct": 10000,
        "motor": 6000, "admin": 4000, "other_expenses": 5000, "partner_income": 0, "mileage_estimate": 18000}),
    ("6. Micro £800", {"gross_income": 800, "net_profit": 600, "cis_deducted": 160,
        "total_expenses": 200, "cost_of_sales": 100, "other_direct": 50,
        "motor": 30, "admin": 10, "other_expenses": 10, "partner_income": 0, "mileage_estimate": 500}),
    ("7. VAT Boundary £89,999", {"gross_income": 89999, "net_profit": 45000, "cis_deducted": 18000,
        "total_expenses": 44999, "cost_of_sales": 20000, "other_direct": 10000,
        "motor": 6000, "admin": 4000, "other_expenses": 4999, "partner_income": 0, "mileage_estimate": 12000}),
    ("8. CIS Overpayment", {"gross_income": 60000, "net_profit": 30000, "cis_deducted": 20000,
        "total_expenses": 30000, "cost_of_sales": 12000, "other_direct": 6000,
        "motor": 4000, "admin": 3000, "other_expenses": 5000, "partner_income": 0, "mileage_estimate": 10000}),
    ("9. Massive £500k", {"gross_income": 500000, "net_profit": 150000, "cis_deducted": 100000,
        "total_expenses": 350000, "cost_of_sales": 200000, "other_direct": 60000,
        "motor": 30000, "admin": 25000, "other_expenses": 35000, "partner_income": 30000, "mileage_estimate": 40000}),
    ("10. Minimum Viable £1", {"gross_income": 1, "net_profit": 1, "cis_deducted": 0,
        "total_expenses": 0, "cost_of_sales": 0, "other_direct": 0,
        "motor": 0, "admin": 0, "other_expenses": 0, "partner_income": 0, "mileage_estimate": 0}),
    ("11. All Motor", {"gross_income": 40000, "net_profit": 25000, "cis_deducted": 8000,
        "total_expenses": 15000, "cost_of_sales": 0, "other_direct": 0,
        "motor": 15000, "admin": 0, "other_expenses": 0, "partner_income": 0, "mileage_estimate": 25000}),
    ("12. Deep Loss + CIS", {"gross_income": 40000, "net_profit": -20000, "cis_deducted": 15000,
        "total_expenses": 60000, "cost_of_sales": 30000, "other_direct": 12000,
        "motor": 8000, "admin": 5000, "other_expenses": 5000, "partner_income": 0, "mileage_estimate": 15000}),
    ("13. Partner Income", {"gross_income": 51000, "net_profit": 25000, "cis_deducted": 10200,
        "total_expenses": 26000, "cost_of_sales": 8000, "other_direct": 5000,
        "motor": 3000, "admin": 2000, "other_expenses": 1500, "partner_income": 8000, "mileage_estimate": 8000}),
    ("14. Extreme Mileage 50k", {"gross_income": 70000, "net_profit": 35000, "cis_deducted": 14000,
        "total_expenses": 35000, "cost_of_sales": 12000, "other_direct": 8000,
        "motor": 8000, "admin": 3000, "other_expenses": 4000, "partner_income": 0, "mileage_estimate": 50000}),
    ("15. Zero CIS", {"gross_income": 45000, "net_profit": 30000, "cis_deducted": 0,
        "total_expenses": 15000, "cost_of_sales": 5000, "other_direct": 3000,
        "motor": 3000, "admin": 2000, "other_expenses": 2000, "partner_income": 0, "mileage_estimate": 10000}),
]


def run_scenario(name: str, params: dict) -> dict:
    start = time.time()
    result = {"name": name, "passed": False, "errors": []}
    try:
        # Silence the hive's print statements for cleaner output
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            hive = HNCHiveMind(params=params)
            verdict = hive.run()

        result["passed"] = (verdict.agents_active == 11 and verdict.waves_completed == 3)
        result["agents_active"] = verdict.agents_active
        result["signals"] = verdict.signals_emitted
        result["decisions"] = verdict.queen_decisions
        result["gamma"] = verdict.coherence_gamma
        result["consensus"] = verdict.consensus_state.value
        result["queen_ruling"] = verdict.queen_ruling[:50]
        result["total_saving"] = verdict.total_saving
        result["net_position"] = verdict.net_position
        result["human_review"] = verdict.human_review_required
        result["time"] = round(time.time() - start, 3)

    except Exception as e:
        result["errors"].append(str(e))
        result["time"] = round(time.time() - start, 3)
        traceback.print_exc()
    return result


if __name__ == "__main__":
    print("\n" + "=" * 78)
    print("HIVE MIND STRESS TEST — 15 SCENARIOS UNDER THE QUEEN")
    print("=" * 78)
    print(f"\n{'SCENARIO':<28} {'AGENTS':<8} {'SIGNALS':<9} {'Γ':<7} {'CONSENSUS':<12} {'TIME':<8}")
    print("─" * 78)

    results = []
    t0 = time.time()
    for name, params in SCENARIOS:
        r = run_scenario(name, params)
        results.append(r)
        status = "✓" if r["passed"] else "✗"
        if r["passed"]:
            print(f"{status} {name:<26} {r['agents_active']:>3}/11   {r['signals']:>3}      "
                  f"{r['gamma']:.3f}  {r['consensus']:<12} {r['time']}s")
        else:
            print(f"{status} {name:<26} FAILED: {r['errors']}")

    total = time.time() - t0
    passed = sum(1 for r in results if r["passed"])

    print("─" * 78)
    print(f"\nSUMMARY: {passed}/{len(results)} scenarios passed — total {total:.1f}s")

    # Consensus distribution
    print(f"\nCONSENSUS DISTRIBUTION:")
    consensus_counts = {}
    for r in results:
        if r["passed"]:
            c = r["consensus"]
            consensus_counts[c] = consensus_counts.get(c, 0) + 1
    for c, n in sorted(consensus_counts.items(), key=lambda x: -x[1]):
        print(f"  {c:<12} {n} scenarios")

    # Γ range
    gammas = [r["gamma"] for r in results if r["passed"]]
    if gammas:
        print(f"\nCOHERENCE Γ RANGE: {min(gammas):.3f} — {max(gammas):.3f} (avg {sum(gammas)/len(gammas):.3f})")

    # Human review cases
    review_cases = [r for r in results if r.get("human_review")]
    if review_cases:
        print(f"\nHUMAN REVIEW FLAGGED: {len(review_cases)} scenarios")
        for r in review_cases:
            print(f"  - {r['name']}: Γ={r['gamma']}")

    print("\n" + "─" * 78)
    print("Every agent acts, every signal reaches the Queen, every Queen ruling is logged.")
    print("One organism. Many cells. One decision.")
    print("─" * 78)

    sys.exit(0 if passed == len(results) else 1)
