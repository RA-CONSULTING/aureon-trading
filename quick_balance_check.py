#!/usr/bin/env python3
"""Quick check of Binance liquid balances"""

import os
from dotenv import load_dotenv
from binance.client import Client

load_dotenv()

try:
    client = Client(
        os.getenv('BINANCE_API_KEY'),
        os.getenv('BINANCE_API_SECRET')
    )
    
    print("=== BINANCE SPOT WALLET BALANCES ===\n")
    
    account = client.get_account()
    liquid_stablecoins = ['USDT', 'USDC', 'BUSD', 'FDUSD', 'TUSD', 'USDD']
    staked_coins = ['LDUSDC', 'LDUSDT', 'LDBNB', 'LDETH']
    
    total_liquid = 0
    total_staked = 0
    
    for balance in account['balances']:
        asset = balance['asset']
        free = float(balance['free'])
        locked = float(balance['locked'])
        total = free + locked
        
        if total > 0.01:
            if asset in liquid_stablecoins:
                print(f"✅ {asset}: {total:.2f} (FREE: {free:.2f}, LOCKED: {locked:.2f})")
                total_liquid += total
            elif asset in staked_coins:
                print(f"🔒 {asset}: {total:.2f} (STAKED - Not tradable)")
                total_staked += total
            else:
                print(f"   {asset}: {total:.8f}")
    
    print(f"\n{'='*50}")
    print(f"LIQUID STABLECOINS TOTAL: ${total_liquid:.2f}")
    print(f"STAKED ASSETS TOTAL: ${total_staked:.2f}")
    print(f"{'='*50}\n")
    
    if total_liquid >= 10:
        print("✅ YOU HAVE ENOUGH LIQUID FUNDS TO TRADE!")
        print(f"   Ready to deploy with ${total_liquid:.2f}")
        exit(0)
    elif total_staked > 0:
        print("❌ PROBLEM: You have staked assets but not enough liquid funds")
        print(f"   Staked: ${total_staked:.2f}")
        print(f"   Liquid: ${total_liquid:.2f}")
        print("\n📋 ACTION NEEDED:")
        print("   1. Go to Binance → Earn → Simple Earn")
        print("   2. Find your staked LDUSDC")
        print("   3. Click 'Redeem' to unstake")
        print("   4. Wait 1-2 minutes for settlement")
        exit(1)
    else:
        print("❌ NO FUNDS FOUND")
        print("   Please deposit USDT or USDC to your Spot Wallet")
        exit(1)
        
except Exception as e:
    print(f"❌ ERROR: {e}")
    exit(2)
