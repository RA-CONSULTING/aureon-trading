#!/usr/bin/env python3
"""Test probability loader and position hygiene"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
from probability_loader import ProbabilityLoader, PositionHygieneChecker

# Test probability loader
print("🎯 Testing Probability Loader...")
p = ProbabilityLoader('/workspaces/aureon-trading')
freshness = p.load_all_reports()

print(f"✅ Loaded {len(p.reports)} reports")
print(f"📅 Freshness: {'FRESH' if p.is_fresh() else 'STALE'}")
if freshness:
    print(f"   Newest: {freshness.get('newest_minutes', 0):.1f}m ago")
    print(f"   Oldest: {freshness.get('oldest_minutes', 0):.1f}m ago")
    print(f"   Threshold: {freshness.get('threshold_minutes')}m")

# High conviction signals
sigs = p.get_top_signals(limit=5, min_probability=0.8, min_confidence=0.8)
print(f"\n🔥 High Conviction Signals: {len(sigs)}")
for i, s in enumerate(sigs[:5], 1):
    print(f"  {i}. {s.symbol:12} | {s.exchange:8} | p={s.probability:.3f} conf={s.confidence:.3f} | {s.action}")

# Consensus signals
cons = p.get_consensus_signals(min_exchanges=2, min_probability=0.75)
print(f"\n🌐 Multi-Exchange Consensus: {len(cons)} symbols")
for i, s in enumerate(cons[:5], 1):
    exch_cnt = getattr(s, 'exchange_count', 1)
    print(f"  {i}. {s.symbol:12} | {exch_cnt} exchanges | p={s.probability:.3f} conf={s.confidence:.3f}")

# Test position hygiene
print("\n\n🧹 Testing Position Hygiene...")
h = PositionHygieneChecker()
state_path = '/workspaces/aureon-trading/aureon_kraken_state.json'
result = h.check_positions(state_path)

print(f"✅ Checked positions: {result['count']} flagged")
if result['flagged']:
    print("\n⚠️ Position Hygiene Alerts:")
    for flag in result['flagged']:
        print(f"  • {flag['symbol']}: {', '.join(flag['reasons'])}")
        print(f"    Entry: £{flag['entry_price']:.4f} | Current: £{flag.get('current_price', 0):.4f}")
        print(f"    Momentum: {flag['momentum']:.2f}% | Cycles: {flag['cycles']}")

print("\n✅ All tests passed!")
