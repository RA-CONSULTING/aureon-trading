#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌊 ENTIRE OCEAN SCAN - Complete whale detection across all coins
Shows every whale, shark, minnow in the trading waters
"""

import sys
sys.path.insert(0, '.')

from queen_eternal_machine import QueenEternalMachine
import logging

logging.basicConfig(level=logging.WARNING, format='%(message)s')

print("\n" + "=" * 90)
print("🌊 OCEAN WAVE SCANNER - ENTIRE MARKET WHALE DETECTION")
print("=" * 90)

# Initialize frog with ocean scanner
frog = QueenEternalMachine()

# Fetch market data for all 197+ coins
print("\n📊 Fetching market data for entire ocean...")
frog.fetch_market_data()
print(f"✅ Market data loaded: {len(frog.market_data)} coins")

# Scan the entire ocean
print("\n🌊 Scanning entire ocean for whale activity...\n")

# Get ocean summary
summary = frog.get_ocean_summary(top_n=25)
print(summary)

# Get detailed ocean map
ocean_map = frog.scan_entire_ocean_for_whales()

print("\n" + "=" * 90)
print("🔍 DETAILED OCEAN MAP - Every coin with whale indicators")
print("=" * 90 + "\n")

# Sort by volume for viewing
sorted_coins = sorted(
    ocean_map.items(),
    key=lambda x: x[1]['total_volume_usd'],
    reverse=True
)

print(f"{'Symbol':<10} {'Size Class':<20} {'Price':<12} {'Change':<8} {'Activity':<30} {'Volume USD':<15}")
print("─" * 110)

for symbol, data in sorted_coins[:50]:
    # Create whale/shark/minnow indicator
    activity = f"🐋×{data['whale_count']} 🦈×{data['shark_count']} 🐟×{data['minnow_count']}"
    
    print(f"{symbol:<10} {data['size_class']:<20} ${data['price']:<11.8f} "
          f"{data['change_24h']:+7.2f}% {activity:<30} ${data['total_volume_usd']:<14,.0f}")

print("\n" + "=" * 90)
print("🐸 FROG'S POSITION IN THE OCEAN")
print("=" * 90 + "\n")

# Show main position
if frog.main_position:
    main = frog.main_position
    frog.fetch_market_data()
    main_data = frog.market_data.get(main.symbol, {})
    
    print(f"🐸 Main Position: {main.symbol}")
    print(f"   Current Value: ${main.current_value:.2f}")
    
    # Handle both dict and MarketCoin object
    if hasattr(main_data, 'price'):
        price = main_data.price
        change = main_data.change_24h
    else:
        price = main_data.get('price', 0)
        change = main_data.get('change_24h', 0)
    
    print(f"   Current Price: ${price:.8f}")
    print(f"   24h Change: {change:+.2f}%")
    
    if main.symbol in ocean_map:
        ocean_status = ocean_map[main.symbol]
        print(f"   Ocean Status: {ocean_status['size_class']}")
        print(f"   Whale Activity: {ocean_status['whale_count']} whales, {ocean_status['shark_count']} sharks")

print(f"\n👥 Friends (Alt Positions): {len(frog.friends)}")

# Show which friends are in whale territory
friends_in_whale_territory = []
friend_symbols = list(frog.friends.keys()) if isinstance(frog.friends, dict) else frog.friends
for friend_symbol in friend_symbols[:10]:  # Top 10
    if friend_symbol in ocean_map:
        ocean_status = ocean_map[friend_symbol]
        if ocean_status['whale_count'] > 0:
            friends_in_whale_territory.append((friend_symbol, ocean_status))

if friends_in_whale_territory:
    print(f"\n🐋 FRIENDS IN WHALE TERRITORY:")
    for symbol, status in friends_in_whale_territory:
        print(f"   {symbol:<8} {status['size_class']:<20} - {status['whale_count']} whales active")
else:
    print(f"\n ℹ️  No friends in whale territory. All friends in quiet or minnow waters.")

print("\n" + "=" * 90)
print("✅ OCEAN SCAN COMPLETE")
print("=" * 90 + "\n")
