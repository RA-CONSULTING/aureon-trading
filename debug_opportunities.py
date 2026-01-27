#!/usr/bin/env python3
"""Quick debug script to see why no opportunities are being found."""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load env
from dotenv import load_dotenv
load_dotenv()

from kraken_client import KrakenClient

def main():
    print("=" * 60)
    print("🔍 DEBUGGING OPPORTUNITY SCANNER")
    print("=" * 60)
    
    # Connect to Kraken
    kraken = KrakenClient()
    
    # Get balances
    print("\n📊 Getting balances from Kraken...")
    balances = kraken.get_balances()
    
    for asset, amount in balances.items():
        if amount > 0:
            print(f"   {asset}: {amount}")
    
    # Get ticker info
    print("\n📊 Getting trading pairs...")
    pairs_resp = kraken.get_tradeable_pairs()
    pairs = pairs_resp.get('result', {})
    print(f"   Total pairs: {len(pairs)}")
    
    # Check what pairs exist for our assets
    print("\n🔍 Checking trading pairs for held assets...")
    
    held_assets = {k: v for k, v in balances.items() if v > 0}
    
    for asset in held_assets:
        print(f"\n   {asset}:")
        
        # Find USD pairs
        usd_pairs = [p for p in pairs.keys() 
                     if (asset in p and 'USD' in p) or 
                        (pairs[p].get('base') == asset) or
                        (pairs[p].get('quote') == asset)]
        
        if usd_pairs:
            print(f"      USD pairs: {usd_pairs[:5]}...")  # First 5
        else:
            print(f"      ❌ No USD pairs found!")
        
        # Check if the asset can be converted
        # Kraken uses weird names - e.g., XBT for BTC
        alt_names = pairs.get(f"{asset}USD", {}).get('altname', '')
        if alt_names:
            print(f"      Alt name: {alt_names}")

if __name__ == "__main__":
    main()
