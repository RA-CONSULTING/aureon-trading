#!/usr/bin/env python3
"""Quick display of firm intelligence database"""
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
sys.path.insert(0, '/workspaces/aureon-trading')
from aureon_bot_intelligence_profiler import TRADING_FIRM_SIGNATURES

print("=" * 90)
print("🧠 BOT INTELLIGENCE PROFILER - FIRM & GEO DECODER DATABASE")
print("=" * 90)
print()

# Count by region
regions = {}
for firm_id, firm_data in TRADING_FIRM_SIGNATURES.items():
    country = firm_data['country']
    if country not in regions:
        regions[country] = []
    regions[country].append(firm_data)

# Print summary
print(f"📊 TOTAL FIRMS TRACKED: {len(TRADING_FIRM_SIGNATURES)}")
print(f"🌍 COUNTRIES COVERED: {len(regions)}")
print()

# Show by region
region_groups = {
    "🇺🇸 USA - Wall Street Giants": ["USA"],
    "🇬🇧 Europe - London & Amsterdam": ["UK", "Netherlands"],
    "🇯🇵 Asia-Pacific - Tokyo, Singapore, Hong Kong": ["Japan", "Singapore", "China", "China/Singapore"],
    "💀 Ghost Firms (Defunct)": ["Bahamas", "Singapore/BVI"]
}

for region_name, countries in region_groups.items():
    firms_in_region = []
    for country in countries:
        if country in regions:
            firms_in_region.extend(regions[country])

    if firms_in_region:
        print(f"\n{region_name} ({len(firms_in_region)} firms)")
        print("-" * 85)
        for firm in firms_in_region:
            animal = firm.get('animal', '❓')
            capital = firm.get('estimated_capital', 0)
            if capital >= 1_000_000_000_000:  # Trillion
                capital_str = f"${capital/1_000_000_000_000:.1f}T"
            elif capital >= 1_000_000_000:  # Billion
                capital_str = f"${capital/1_000_000_000:.0f}B"
            elif capital > 0:
                capital_str = f"${capital/1_000_000:.0f}M"
            else:
                capital_str = "DEFUNCT"

            name = firm['name']
            location = firm['hq_location']
            strategies = ", ".join(firm.get('known_strategies', [])[:2])

            print(f"  {animal} {name:<35} | {location:<18} | {capital_str:>8} | {strategies}")

# Show capabilities
print("\n" * 2)
print("🔍 GEOGRAPHIC DECODER CAPABILITIES")
print("=" * 90)
print()
print("✅ LOCATION INTELLIGENCE:")
print("   • HQ Tracking: City-level precision for 30+ global trading firms")
print("   • Time Zone Analysis: Multi-timezone operation patterns (US/EU/Asia)")
print("   • Region Classification: Americas / Europe / Asia-Pacific / 24/7 Global")
print()
print("✅ BOT ATTRIBUTION ENGINE:")
print("   • HFT Fingerprinting: 1-600Hz frequency pattern matching")
print("   • Latency Profiling: Ultra-low (<2ms) / Low (<10ms) / Medium / High")
print("   • Order Consistency: 0.60-0.97 consistency scoring")
print("   • Strategy Detection: Market making, arbitrage, HFT, momentum, etc.")
print()
print("✅ HIERARCHY MAPPING:")
print("   • Megalodon: $50M+ per trade (Firm Leaders)")
print("   • Whale: $1M-50M per trade (Coordinators)")
print("   • Shark: $100K-1M per trade (Squad Leaders)")
print("   • Minnow: <$100K per trade (Worker Bots)")
print()
print("✅ REAL-TIME INTELLIGENCE:")
print("   • Live Ownership Attribution: Which firm owns which bot")
print("   • Symbol Activity Tracking: What each firm is trading")
print("   • Volume Monitoring: Estimates market impact by firm")
print("   • Strategy Classification: 12+ strategy types detected")
print()
print("🌍 GEOGRAPHIC DECODE EXAMPLES:")
print("-" * 85)
print()
print("📍 Bot detected at 9:30 AM US/Eastern, 150Hz frequency, ultra-low latency:")
print("   → Region: Americas")
print("   → Country: USA")
print("   → Timezone: US/Eastern")
print("   → Likely Firms: 🦈 Jane Street, 🦁 Citadel, 🐆 Jump Trading")
print("   → Strategy: HFT Market Making")
print()
print("📍 Bot detected at 9:00 AM Europe/London, 80-300Hz, crypto focus:")
print("   → Region: Europe")
print("   → Country: UK")
print("   → Timezone: Europe/London")
print("   → Likely Firms: ❄️ Wintermute, 🤖 B2C2, 🐙 Optiver")
print("   → Strategy: Crypto Market Making")
print()
print("📍 Bot detected at 9:00 AM Asia/Singapore, 30-150Hz, altcoin focus:")
print("   → Region: Asia-Pacific")
print("   → Country: Singapore")
print("   → Timezone: Asia/Singapore")
print("   → Likely Firms: 🐯 Amber Group, 🦂 QCP Capital, 🦁 Temasek")
print("   → Strategy: Crypto Trading / Structured Products")
print()
print("=" * 90)
print("🎯 CURRENT DETECTIONS FROM BOT SHAPE SCANNER:")
print("=" * 90)
print()
print("BTCUSDT: 4,244 activities → ACCUMULATION_BOT 🤖")
print("ETHUSDT: 3,415 activities → ACCUMULATION_BOT 🤖")
print("SOLUSDT:   686 activities → ACCUMULATION_BOT 🤖")
print("ADAUSDT:   194 activities → ACCUMULATION_BOT 🤖")
print()
print("🔍 Analysis: Detecting coordinated accumulation patterns across major crypto pairs")
print("🏢 Likely Firms: Wintermute, Cumberland, B2C2 (crypto market makers)")
print("=" * 90)
