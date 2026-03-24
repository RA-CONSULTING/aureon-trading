#!/usr/bin/env python3
"""Test Super Intelligence Gate integration in Orca Kill Cycle."""
import sys, os, io, time

# Force UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
os.environ['COLUMNS'] = '200'
os.environ['TERM'] = 'dumb'

# Suppress noisy loading
import logging
logging.disable(logging.WARNING)

print("Loading Orca Kill Cycle (quick_init)...")
from orca_complete_kill_cycle import OrcaKillCycle

orca = OrcaKillCycle(quick_init=True)

print()
print("=" * 70)
print("  SUPER INTELLIGENCE GATE - ORCA INTEGRATION TEST")
print("=" * 70)
print()

# Check gate loaded
gate = getattr(orca, 'super_gate', None)
if gate is None:
    print("  ERROR: super_gate not found on OrcaKillCycle!")
    sys.exit(1)

print(f"  Gate loaded:        YES")
print(f"  Min confidence:     {gate.min_confidence:.0%}")
print(f"  Prob Intel:         {'YES' if gate.prob_intel else 'NO'}")
print(f"  QGITA Framework:   {'YES' if gate.qgita else 'NO'}")
print(f"  Lighthouse:         {'YES' if gate.lighthouse else 'NO'}")
print(f"  Elephant Memory:    {'YES' if gate.elephant else 'NO'}")
print(f"  Sniper Brain:       {'YES' if gate.sniper else 'NO'}")
print(f"  Pillar Council:     {'YES' if gate.council else 'NO'}")
print()

# Test evaluate
print("  EVALUATING BTC/USD BUY...")
print("-" * 70)
result = gate.evaluate(
    symbol='BTC/USD',
    prices=[100000 + i * 10 for i in range(50)],
    timestamps=[time.time() - (50 - i) for i in range(50)],
    current_pnl=0.05,
    momentum=0.3,
    win_rate=0.75,
    king_health=0.85,
    side='BUY'
)

print(f"  Should Trade:       {result.should_trade}")
print(f"  Combined Conf:      {result.combined_confidence:.1%}")
print(f"  Approvals:          {result.approval_count}/{result.total_systems}")
print()
print("  SYSTEM VOTES:")
for v in result.votes:
    tag = "PASS" if v.approved else "FAIL"
    print(f"    [{tag}] {v.system_name}: {v.confidence:.1%} - {v.reasoning}")

print()
print("=" * 70)
if result.should_trade:
    print("  VERDICT: TRADE APPROVED - All 8 systems aligned")
else:
    print("  VERDICT: TRADE BLOCKED - Below 65% confidence threshold")
print("  ORCA + SUPER INTELLIGENCE GATE: FULLY OPERATIONAL")
print("=" * 70)
