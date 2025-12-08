#!/usr/bin/env python3
"""Check current Binance balance after redemption"""

import os
from dotenv import load_dotenv
from binance.client import Client

load_dotenv()

try:
    client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
    account = client.get_account()
    
    print("\n" + "="*60)
    print("🔄 CURRENT BINANCE BALANCE (After Redemption)")
    print("="*60 + "\n")
    
    liquid_total = 0
    staked_total = 0
    other = []
    
    for balance in account['balances']:
        asset = balance['asset']
        free = float(balance['free'])
        locked = float(balance['locked'])
        total = free + locked
        
        if total > 0.01:
            if asset in ['USDT', 'USDC', 'BUSD', 'FDUSD']:
                print(f"✅ {asset}: ${total:.2f} (FREE: ${free:.2f})")
                liquid_total += free  # Only count free, not locked
            elif asset.startswith('LD'):
                print(f"🔒 {asset}: {total:.8f} (STILL STAKED)")
                staked_total += total
            else:
                other.append((asset, total))
    
    if other:
        print("\n📦 Other assets:")
        for asset, total in other[:5]:  # Show first 5
            print(f"   {asset}: {total:.8f}")
    
    print("\n" + "="*60)
    print(f"💰 LIQUID STABLECOINS (Free): ${liquid_total:.2f}")
    print(f"🔒 STAKED: ${staked_total:.2f}")
    print("="*60)
    
    if liquid_total >= 10:
        print(f"\n✅ READY TO TRADE!")
        print(f"   You have ${liquid_total:.2f} in liquid funds")
        print(f"   System can trade immediately on Binance")
    elif liquid_total >= 5:
        print(f"\n⚠️  PARTIAL FUNDING")
        print(f"   You have ${liquid_total:.2f} (need $10 for optimal)")
        print(f"   Can still trade, but might hit size limits")
    else:
        print(f"\n❌ INSUFFICIENT FUNDS")
        print(f"   You have ${liquid_total:.2f}")
        print(f"   Need at least $5-10 to trade")
    
    print()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
