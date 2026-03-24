#!/usr/bin/env python3
"""Quick test of 7-day planner."""
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
sys.path.insert(0, '/workspaces/aureon-trading')

from aureon_7day_planner import Aureon7DayPlanner

print("\n" + "=" * 70)
print("📅🔮 TESTING 7-DAY PLANNER")
print("=" * 70)

planner = Aureon7DayPlanner()

# Get week summary
summary = planner.get_week_summary()
print(f"\n📊 Week predicted edge: {summary['total_predicted_edge']:+.2f}%")

print("\n📅 DAILY FORECAST:")
for day in summary['days']:
    status = "🟢" if day['is_optimal'] else ("🔴" if day['is_avoid'] else "🟡")
    print(f"  {day['date']}: {day['daily_edge']:+.2f}% {status}")
    if day['best_window']:
        bw = day['best_window']
        print(f"    └─ Best: {bw['symbol']} @ {bw['hour']:02d}:00 ({bw['edge']:+.2f}%)")

print("\n🏆 TOP 5 WINDOWS:")
for i, w in enumerate(summary['top_5_windows'], 1):
    print(f"  {i}. {w['symbol']} @ {w['datetime']}: {w['edge']:+.2f}%")

# Current recommendation
rec = planner.get_current_recommendation('BTC')
print(f"\n🔮 CURRENT (BTC): {rec['action']} | Edge: {rec['total_edge']:+.2f}%")

print("\n" + "=" * 70)
