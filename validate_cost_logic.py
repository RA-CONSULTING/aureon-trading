#!/usr/bin/env python3
"""
Validate Alpaca cost calculation logic
"""
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os

if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Test the cost logic
print("=" * 70)
print("ALPACA COST CALCULATION VALIDATION")
print("=" * 70)
print()

# Alpaca Crypto Fee Tiers
print("📊 ALPACA FEE TIERS (Crypto):")
print("  Tier 1 ($0-$100K):        Maker 0.15%, Taker 0.25%")
print("  Tier 2 ($100K-$500K):     Maker 0.12%, Taker 0.22%")
print("  Tier 3 ($500K-$1M):       Maker 0.10%, Taker 0.20%")
print()

# Test calculation
from_value_usd = 9.50  # ETH value in USD
print(f"Test Trade: ETH → USDC")
print(f"From Value: ${from_value_usd:.2f}")
print()

# Scenario 1: Direct conversion (if supported)
print("SCENARIO 1: Direct ETH/USDC pair (if available)")
print("-" * 70)
taker_fee_pct = 0.0025  # 0.25% (Tier 1)
spread_pct = 0.0001  # 0.01% typical for liquid pairs
slippage_pct = 0.0001  # 0.01% minimal for small trades

total_cost_pct_direct = taker_fee_pct + spread_pct + slippage_pct
total_cost_usd_direct = from_value_usd * total_cost_pct_direct

print(f"  Taker Fee:  {taker_fee_pct*100:.4f}% = ${from_value_usd * taker_fee_pct:.4f}")
print(f"  Spread:     {spread_pct*100:.4f}% = ${from_value_usd * spread_pct:.4f}")
print(f"  Slippage:   {slippage_pct*100:.4f}% = ${from_value_usd * slippage_pct:.4f}")
print(f"  TOTAL:      {total_cost_pct_direct*100:.4f}% = ${total_cost_usd_direct:.4f}")
print()

# Scenario 2: Two-leg conversion ETH→USD→USDC
print("SCENARIO 2: Two-leg conversion ETH→USD→USDC")
print("-" * 70)

# Leg 1: ETH → USD
print("Leg 1: Sell ETH for USD")
leg1_fee = from_value_usd * taker_fee_pct
leg1_spread = from_value_usd * spread_pct
leg1_total = leg1_fee + leg1_spread
usd_received = from_value_usd - leg1_total

print(f"  Taker Fee:  {taker_fee_pct*100:.4f}% = ${leg1_fee:.4f}")
print(f"  Spread:     {spread_pct*100:.4f}% = ${leg1_spread:.4f}")
print(f"  Leg 1 Cost: ${leg1_total:.4f}")
print(f"  USD Received: ${usd_received:.2f}")
print()

# Leg 2: USD → USDC
print("Leg 2: Buy USDC with USD")
leg2_fee = usd_received * taker_fee_pct
leg2_spread = usd_received * spread_pct
leg2_total = leg2_fee + leg2_spread
usdc_received = usd_received - leg2_total

print(f"  Taker Fee:  {taker_fee_pct*100:.4f}% = ${leg2_fee:.4f}")
print(f"  Spread:     {spread_pct*100:.4f}% = ${leg2_spread:.4f}")
print(f"  Leg 2 Cost: ${leg2_total:.4f}")
print(f"  USDC Received: ${usdc_received:.2f}")
print()

total_cost_usd_twolegs = leg1_total + leg2_total
total_cost_pct_twolegs = total_cost_usd_twolegs / from_value_usd

print("TOTAL CONVERSION COST (Two-leg):")
print(f"  Combined Cost: ${total_cost_usd_twolegs:.4f} ({total_cost_pct_twolegs*100:.4f}%)")
print(f"  Net USDC: ${usdc_received:.2f}")
print()

# What momentum is needed to break even?
print("=" * 70)
print("MOMENTUM REQUIRED TO BREAK EVEN:")
print("=" * 70)
print()
print(f"With {total_cost_pct_direct*100:.4f}% costs (direct), need momentum >  {total_cost_pct_direct*100:.4f}%/min")
print(f"With {total_cost_pct_twolegs*100:.4f}% costs (two-leg), need momentum > {total_cost_pct_twolegs*100:.4f}%/min")
print()

# Check current reported costs
print("=" * 70)
print("CURRENT SYSTEM COST CALCULATION:")
print("=" * 70)
print()
print("From logs: Total Costs = $0.0481 (0.51%)")
print()
print("Analysis:")
cost_reported = 0.0481
cost_pct_reported = 0.51 / 100  # 0.51%

print(f"  Reported Cost: ${cost_reported:.4f} ({cost_pct_reported*100:.2f}%)")
print()

# Check if this is reasonable
if cost_pct_reported > total_cost_pct_twolegs * 1.5:
    print("❌ ISSUE DETECTED:")
    print(f"   Expected cost (two-leg): {total_cost_pct_twolegs*100:.4f}%")
    print(f"   Reported cost: {cost_pct_reported*100:.2f}%")
    print(f"   Difference: {(cost_pct_reported - total_cost_pct_twolegs)*100:.2f}%")
    print()
    print("   Possible issues:")
    print("   1. Costs being counted twice (entry + exit)?")
    print("   2. Spread estimate too high?")
    print("   3. Including slippage that hasn't happened yet?")
    print("   4. Using wrong fee tier?")
elif cost_pct_reported < total_cost_pct_direct * 0.5:
    print("⚠️  WARNING: Reported cost seems too LOW")
    print(f"   Expected minimum (direct): {total_cost_pct_direct*100:.4f}%")
    print(f"   Reported cost: {cost_pct_reported*100:.2f}%")
else:
    print("✅ Cost calculation appears reasonable")
    print(f"   Within expected range: {total_cost_pct_direct*100:.4f}% - {total_cost_pct_twolegs*100:.4f}%")
    print(f"   Reported: {cost_pct_reported*100:.2f}%")

print()
print("=" * 70)
print("GROSS EDGE ANALYSIS:")
print("=" * 70)
print()
print("From logs: Gross Edge = $0.0216")
print()

gross_edge = 0.0216
gross_edge_pct = (gross_edge / from_value_usd) * 100

print(f"  As percentage of trade: {gross_edge_pct:.4f}%")
print()
print("Components of gross edge:")
print("  - Momentum capture (30-80% of observed momentum)")
print("  - Signal score bonus (up to 0.3%)")
print("  - Dream score bonus (very small)")
print()
print(f"For trade to be profitable:")
print(f"  Need: Gross Edge > Total Costs")
print(f"  Currently: ${gross_edge:.4f} vs ${cost_reported:.4f}")
print(f"  Shortfall: ${cost_reported - gross_edge:.4f}")
print()

if gross_edge < cost_reported:
    shortfall_pct = ((cost_reported - gross_edge) / from_value_usd) * 100
    print(f"❌ INSUFFICIENT MOMENTUM:")
    print(f"   Need additional {shortfall_pct:.4f}% momentum to break even")
    print()
    momentum_needed = shortfall_pct / 0.30  # Assuming 30% capture rate
    print(f"   With 30% capture rate, need {momentum_needed:.2f}%/min momentum")
    print(f"   With 50% capture rate, need {momentum_needed * 0.30 / 0.50:.2f}%/min momentum")
    print(f"   With 80% capture rate, need {momentum_needed * 0.30 / 0.80:.2f}%/min momentum")
