#!/usr/bin/env python3
"""
Deep dive into Binance account - check EVERYTHING
"""
from aureon.core.aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
from aureon.exchanges.binance_client import BinanceClient
from dotenv import load_dotenv
import json

load_dotenv()

print("=" * 60)
print("🔍 DEEP BINANCE ACCOUNT ANALYSIS")
print("=" * 60)

try:
    client = BinanceClient(dry_run=False)
    
    # 1. Spot Balances
    print("\n1️⃣ SPOT WALLET:")
    try:
        spot_balances = client.client.get_account()
        assets_with_balance = [a for a in spot_balances.get('balances', []) if float(a['free']) > 0 or float(a['locked']) > 0]
        
        if assets_with_balance:
            for asset in assets_with_balance:
                free = float(asset['free'])
                locked = float(asset['locked'])
                total = free + locked
                print(f"  {asset['asset']:10s} | Free: {free:15.8f} | Locked: {locked:15.8f} | Total: {total:15.8f}")
        else:
            print("  ❌ No spot balances")
    except Exception as e:
        print(f"  ❌ Error getting spot balances: {e}")

    # 2. Check if any USD equivalent
    print("\n2️⃣ USD-EQUIVALENT ASSETS:")
    usd_assets = ['USDT', 'USDC', 'BUSD', 'FDUSD', 'TUSD']
    total_usd = 0
    for asset in usd_assets:
        try:
            bal = client.get_balance(asset)
            if bal > 0:
                print(f"  ✅ {asset}: ${bal:.2f}")
                total_usd += bal
        except:
            pass
    
    if total_usd > 0:
        print(f"\n  💰 TOTAL LIQUID USD: ${total_usd:.2f}")
    else:
        print(f"\n  ❌ NO LIQUID USD STABLECOINS")

    # 3. Check Earn products
    print("\n3️⃣ BINANCE EARN (Staked/Locked):")
    # Note: Binance Earn API requires additional permissions
    # But we can infer from LDUSDC balance
    ldusdc = client.get_balance('LDUSDC')
    if ldusdc > 0:
        print(f"  🔒 LDUSDC: ${ldusdc:.2f} (Lido Staked USDC)")
        print(f"     ⚠️  This is NOT tradable")
        print(f"     ℹ️  Redeem via: Binance Earn → Simple Earn → Flexible → Redeem")
    
    # 4. Any crypto holdings that could be sold?
    print("\n4️⃣ CRYPTO HOLDINGS (Can be sold for USDT):")
    crypto_assets = ['BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'DOGE', 'MATIC']
    has_crypto = False
    for asset in crypto_assets:
        try:
            bal = client.get_balance(asset)
            if bal > 0:
                # Try to get USD value
                try:
                    ticker = client.client.get_symbol_ticker(symbol=f"{asset}USDT")
                    price = float(ticker['price'])
                    usd_value = bal * price
                    print(f"  {asset:6s}: {bal:.8f} ≈ ${usd_value:.2f}")
                    has_crypto = True
                except:
                    print(f"  {asset:6s}: {bal:.8f}")
                    has_crypto = True
        except:
            pass
    
    if not has_crypto:
        print("  ❌ No crypto holdings")
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print("=" * 60)
    if total_usd >= 5:
        print(f"✅ You have ${total_usd:.2f} liquid - READY TO TRADE!")
    elif has_crypto:
        print("⚠️  You have crypto but no stablecoins")
        print("   Consider selling some for USDT to start trading")
    elif ldusdc > 0:
        print(f"⚠️  You have ${ldusdc:.2f} in LDUSDC (staked)")
        print("   ACTION REQUIRED: Redeem LDUSDC → USDC on Binance Earn")
    else:
        print("❌ No funds detected - deposit required")
    print("=" * 60)

except Exception as e:
    print(f"❌ FATAL ERROR: {e}")
    import traceback
    traceback.print_exc()
