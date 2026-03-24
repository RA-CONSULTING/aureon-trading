#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛡️ ORCA KILL CYCLE DEFENSE - Protect 41 friends from whale attacks
Monitor and defend against large whale dumps on friend positions
"""

import sys
sys.path.insert(0, '.')

from queen_eternal_machine import QueenEternalMachine
import logging

logging.basicConfig(level=logging.WARNING, format='%(message)s')

print("\n" + "=" * 95)
print("🛡️ ORCA KILL CYCLE DEFENSE SYSTEM - PROTECT OUR 41 FRIENDS!")
print("=" * 95)

# Initialize frog with protection systems
frog = QueenEternalMachine()

# Fetch market data for all coins
print("\n📊 Fetching live market data for all positions...")
frog.fetch_market_data()
print(f"✅ Market data loaded: {len(frog.market_data)} coins")

# Scan entire ocean for whale activity
print("\n🌊 Scanning ocean for whale attacks on friend positions...")
ocean = frog.scan_entire_ocean_for_whales()
print(f"✅ Ocean scan complete")

# Check friend protection status
print("\n" + frog.get_friend_protection_status(top_n=15))

# Apply protective stops
print("\n🛡️ Applying protective stops to endangered friends...")
protected = frog.apply_friend_protection_stops()

if protected:
    print(f"\n✅ {len(protected)} friends PROTECTED with emergency stops:\n")
    for symbol, protection in protected.items():
        print(f"   {symbol}")
        print(f"   ├─ Protective Stop: ${protection['protective_stop']:.8f}")
        print(f"   ├─ Emergency Floor: ${protection['emergency_floor']:.8f}")
        print(f"   └─ Reason: {protection['reason']}\n")
else:
    print("\n✅ All friends are safe - no emergency stops needed!")

# Summary of all friends
print("\n" + "=" * 95)
print("👥 COMPLETE FRIEND ROSTER WITH OCEAN STATUS")
print("=" * 95 + "\n")

friend_summary = []
for symbol in frog.friends.keys():
    friend = frog.friends[symbol]
    ocean_status = ocean.get(symbol, {})
    
    friend_summary.append({
        "symbol": symbol,
        "value": friend.current_value,
        "loss": friend.baggage_percent,
        "ocean": ocean_status.get('size_class', '⚪ UNKNOWN'),
        "change": ocean_status.get('change_24h', 0),
    })

# Sort by loss (most endangered first)
friend_summary.sort(key=lambda x: x['loss'], reverse=True)

print(f"{'Symbol':<10} {'Value':<15} {'Loss %':<10} {'Ocean Status':<20} {'24h Change':<12}")
print("─" * 95)

endangered_count = 0
for friend_data in friend_summary[:30]:  # Show top 30
    ocean_icon = "🔴" if friend_data['loss'] > 20 else "🟠" if friend_data['loss'] > 10 else "🟡" if friend_data['loss'] > 5 else "✅"
    
    if friend_data['loss'] > 5:
        endangered_count += 1
    
    print(f"{friend_data['symbol']:<10} ${friend_data['value']:<14.2f} {friend_data['loss']:<9.1f}% "
          f"{friend_data['ocean']:<20} {friend_data['change']:+6.2f}% {ocean_icon}")

print(f"\n📊 Summary: {len(frog.friends)} total friends | {endangered_count} showing losses > 5%")

# Main position status
print(f"\n" + "=" * 95)
print("🐸 MAIN POSITION DEFENSE STATUS")
print("=" * 95 + "\n")

if frog.main_position:
    main = frog.main_position
    main_ocean = ocean.get(main.symbol, {})
    
    print(f"🐸 {main.symbol} - Main Position")
    print(f"   Value: ${main.current_value:.2f}")
    print(f"   Cost Basis: ${main.cost_basis:.2f}")
    
    # Calculate loss
    loss_pct = ((main.cost_basis - main.current_value) / main.cost_basis * 100) if main.cost_basis > 0 else 0
    print(f"   Loss: {loss_pct:.1f}%")
    print(f"   Ocean Status: {main_ocean.get('size_class', '⚪ UNKNOWN')}")
    print(f"   24h Change: {main_ocean.get('change_24h', 0):+.2f}%")
    
    if loss_pct > 10:
        print(f"\n   🛡️ PROTECTION STATUS: UNDERWATER")
        print(f"   ├─ Cost Basis Price: ${main.entry_price:.8f}")
        print(f"   ├─ Current Price: ${main.current_price:.8f}")
        print(f"   ├─ Protective Stop: ${main.entry_price * 0.95:.8f}")
        print(f"   └─ Emergency Floor: ${main.entry_price * 0.90:.8f}")
    else:
        print(f"\n   ✅ SAFE - Above cost basis")

print("\n" + "=" * 95)
print("✅ ORCA KILL CYCLE DEFENSE READY - ALL FRIENDS MONITORED!")
print("=" * 95 + "\n")
