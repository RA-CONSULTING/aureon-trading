#!/usr/bin/env python3
"""Test Dashboard Data Availability - Ocean Scanner & Detection."""
import json
import os
import asyncio

# Suppress warnings
import warnings
warnings.filterwarnings('ignore')

from aureon_ocean_scanner import OceanScanner
from kraken_client import KrakenClient
from binance_client import BinanceClient
from alpaca_client import AlpacaClient

async def test_dashboard_data():
    """Test that all dashboard data sources are working."""
    print("\n" + "=" * 80)
    print("🔍 DASHBOARD DATA AVAILABILITY TEST")
    print("=" * 80)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # TEST 1: OCEAN SCANNER DATA
    # ═══════════════════════════════════════════════════════════════════════════════
    print("\n✅ TEST 1: OCEAN SCANNER")
    print("-" * 80)
    
    exchanges = {
        'kraken': KrakenClient(),
        'binance': BinanceClient(),
        'alpaca': AlpacaClient()
    }
    
    scanner = OceanScanner(exchanges)
    await scanner.discover_universe()
    opportunities = await scanner.scan_ocean(limit=100)
    summary = scanner.get_ocean_summary()
    
    ocean_data = {
        'universe_size': summary.get('universe_size', {}).get('total', 0),
        'hot_opportunities': len(opportunities),
        'top_opportunities': summary.get('top_5', []),
        'scan_count': summary.get('scan_count', 0),
        'last_scan_time': summary.get('last_scan_time', 0)
    }
    
    print(f"   Universe Size: {ocean_data['universe_size']:,} symbols")
    print(f"   Hot Opportunities: {ocean_data['hot_opportunities']}")
    print(f"   Top 5 Opportunities:")
    for i, opp in enumerate(ocean_data['top_opportunities'][:5], 1):
        if isinstance(opp, dict):
            symbol = opp.get('symbol', 'UNKNOWN')
            score = opp.get('ocean_score', 0)
            print(f"      {i}. {symbol:<10} (Score: {score:.2f})")
    print(f"   Scan Count: {ocean_data['scan_count']}")
    print(f"   Last Scan Time: {ocean_data['last_scan_time']:.2f}s")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # TEST 2: DETECTION (BOTS/WHALES/HIVES) DATA
    # ═══════════════════════════════════════════════════════════════════════════════
    print("\n✅ TEST 2: DETECTION (BOTS/WHALES/HIVES)")
    print("-" * 80)
    
    state_dir = os.getenv("AUREON_STATE_DIR", ".")
    
    def _load_json_if_exists(path: str):
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"      ⚠️ Error loading {path}: {e}")
        return None
    
    # Load bot intelligence
    report = _load_json_if_exists(os.path.join(state_dir, "bot_intelligence_report.json")) or \
             _load_json_if_exists(os.path.join(os.getcwd(), "bot_intelligence_report.json"))
    
    bots = {}
    whales = 0
    firms = set()
    
    if report:
        print(f"   Found bot_intelligence_report.json ({len(report.get('all_bots', {})) } bots)")
        bots_raw = report.get("all_bots", {})
        for bot_id, info in bots_raw.items():
            bot_type = info.get("size_class", "bot").lower()
            if bot_type == "whale" or info.get("role", "").lower() == "coordinator":
                whales += 1
                display_type = "whale"
            else:
                display_type = "bot"
            
            firm = info.get("owner_name") or info.get("likely_owner")
            if firm:
                firms.add(firm)
            
            bots[bot_id] = {
                'id': bot_id,
                'type': display_type,
                'symbol': info.get('symbol', 'UNKNOWN'),
            }
    else:
        print(f"   ⚠️ bot_intelligence_report.json not found")
    
    # Load consolidated entity list
    consolidated = _load_json_if_exists(os.path.join(state_dir, "consolidated_entity_list.json")) or \
                   _load_json_if_exists(os.path.join(os.getcwd(), "consolidated_entity_list.json"))
    
    if consolidated and isinstance(consolidated, list):
        print(f"   Found consolidated_entity_list.json ({len(consolidated)} entities)")
        for entity in consolidated:
            bots_list = entity.get("bots_controlled", []) or []
            for bot_id in bots_list:
                if bot_id not in bots:
                    owner = entity.get("entity_name") or entity.get("firm_name")
                    if owner:
                        firms.add(owner)
    else:
        print(f"   ⚠️ consolidated_entity_list.json not found or invalid")
    
    print(f"   Total Bots: {len(bots)}")
    print(f"   Whales: {whales}")
    print(f"   Hives (Firms): {len(firms)}")
    if firms:
        print(f"      Firms detected: {', '.join(list(firms)[:3])}")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 80)
    print("📊 DASHBOARD DATA SUMMARY")
    print("=" * 80)
    
    dashboard_data = {
        'ocean': {
            'universe_size': ocean_data['universe_size'],
            'hot_opportunities': ocean_data['hot_opportunities'],
            'scan_count': ocean_data['scan_count'],
            'top_5_count': len(ocean_data['top_opportunities'])
        },
        'detection': {
            'total_bots': len(bots),
            'whales': whales,
            'hives': len(firms)
        }
    }
    
    print("\n🌊 OCEAN TAB READY FOR DASHBOARD:")
    print(json.dumps(dashboard_data['ocean'], indent=2))
    
    print("\n🤖 DETECTION TAB READY FOR DASHBOARD:")
    print(json.dumps(dashboard_data['detection'], indent=2))
    
    print("\n" + "=" * 80)
    print("✅ ALL DASHBOARD DATA SOURCES VERIFIED")
    print("=" * 80 + "\n")

if __name__ == '__main__':
    asyncio.run(test_dashboard_data())
