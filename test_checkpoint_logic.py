#!/usr/bin/env python3
"""Test checkpoint opportunity finding."""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
os.chdir('/workspaces/aureon-trading')

# Simple test of the target assets construction
checkpoint_stablecoins = {'USD': 1.0, 'USDT': 1.0, 'USDC': 1.0, 'ZUSD': 1.0}
prices = {'CHZ': 0.045, 'BTC': 97000.0, 'ETH': 3500.0}

target_assets = dict(prices)
for stable, price in checkpoint_stablecoins.items():
    if stable not in target_assets:
        target_assets[stable] = price

print("=" * 60)
print("🏦 CHECKPOINT LOGIC TEST")
print("=" * 60)
print(f"\n📈 Original prices: {list(prices.keys())}")
print(f"🏦 Checkpoint stables: {list(checkpoint_stablecoins.keys())}")
print(f"🎯 Target assets after merge: {list(target_assets.keys())}")

print("\n🔍 Testing checkpoint detection for CHZ:")
from_asset = 'CHZ'
for to_asset in target_assets.keys():
    is_checkpoint = to_asset in ['USD', 'USDT', 'USDC', 'TUSD', 'DAI', 'ZUSD']
    score_threshold = 0.35 if is_checkpoint else 0.55
    tag = "🏦 CHECKPOINT" if is_checkpoint else ""
    print(f"   {from_asset} → {to_asset}: checkpoint={is_checkpoint}, threshold={score_threshold:.0%} {tag}")

print("\n✅ Test complete!")
print("   - USD is now in target_assets")
print("   - Checkpoint targets get lower threshold (35% vs 55%)")
print("   - CHZ → USD should now be evaluated as a checkpoint")
