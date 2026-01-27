#!/usr/bin/env python3
"""Check Kraken account for liquid trading funds"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
from dotenv import load_dotenv

load_dotenv()

try:
    import krakenex
    from pykrakenapi import KrakenAPI
    
    api = krakenex.API()
    api.load_key(os.path.expanduser('~/.kraken/kraken.key'))
    
    print("\n=== KRAKEN ACCOUNT CHECK ===\n")
    
    # Get account balance
    result = api.query_private('Balance')
    
    if 'error' in result and result['error']:
        print(f"❌ Kraken API Error: {result['error']}")
    else:
        balances = result.get('result', {})
        
        print("Kraken Balances:")
        liquid_usd = 0
        staked = 0
        
        for asset, amount in balances.items():
            amount = float(amount)
            if amount > 0.01:
                # Clean up asset names
                clean_asset = asset.replace('X', '').replace('Z', '')
                
                if clean_asset in ['USD', 'EUR', 'GBP', 'USDT', 'USDC']:
                    print(f"  ✅ {clean_asset}: ${amount:.2f} (LIQUID)")
                    if clean_asset in ['USD', 'USDT', 'USDC']:
                        liquid_usd += amount
                elif 'STAKE' in asset.upper() or asset.startswith('LD'):
                    print(f"  🔒 {asset}: {amount:.8f} (STAKED)")
                    staked += amount
                else:
                    print(f"  📦 {asset}: {amount:.8f}")
        
        print(f"\n💰 LIQUID USD/STABLECOIN TOTAL: ${liquid_usd:.2f}")
        if staked > 0:
            print(f"🔒 STAKED TOTAL: {staked:.8f}")
        
        if liquid_usd >= 5:
            print(f"\n✅ KRAKEN HAS ENOUGH LIQUID FUNDS TO TRADE!")
            print(f"   Ready to deploy with ${liquid_usd:.2f}")
        else:
            print(f"\n❌ INSUFFICIENT LIQUID FUNDS ON KRAKEN")
            print(f"   Have: ${liquid_usd:.2f}, Need: $5+")
            
except ImportError:
    print("❌ Kraken libraries not installed")
    print("   Install with: pip install krakenex pykrakenapi")
except FileNotFoundError:
    print("❌ Kraken API key not configured")
    print("   Need: ~/.kraken/kraken.key")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
