#!/usr/bin/env python3
"""
Full Binance balance check - ALL assets including Earn products
"""
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

from dotenv import load_dotenv
load_dotenv(override=True)

from binance.client import Client

try:
    client = Client(
        os.getenv('BINANCE_API_KEY'),
        os.getenv('BINANCE_API_SECRET')
    )
    
    print("\n" + "=" * 70)
    print("💰 FULL BINANCE ACCOUNT BREAKDOWN")
    print("=" * 70)
    
    # Get spot account
    account = client.get_account()
    
    # Collect all non-zero balances
    spot_balances = []
    total_usdc_value = 0.0
    
    for balance in account['balances']:
        free = float(balance['free'])
        locked = float(balance['locked'])
        total = free + locked
        
        if total > 0.00001:
            asset = balance['asset']
            spot_balances.append({
                'asset': asset,
                'free': free,
                'locked': locked,
                'total': total
            })
    
    # Get prices for valuation
    print("\n📊 SPOT BALANCES:")
    print("-" * 70)
    print(f"{'ASSET':10s} | {'FREE':>15s} | {'LOCKED':>15s} | {'USD VALUE':>15s}")
    print("-" * 70)
    
    # Get all tickers for price lookup
    try:
        all_tickers = {t['symbol']: float(t['price']) for t in client.get_all_tickers()}
    except:
        all_tickers = {}
    
    stablecoins = ['USDC', 'USDT', 'BUSD', 'DAI', 'TUSD', 'USD', 'FDUSD']
    
    for b in sorted(spot_balances, key=lambda x: x['total'], reverse=True):
        asset = b['asset']
        
        # Calculate USD value
        if asset in stablecoins:
            usd_value = b['total']
        else:
            # Try different quote pairs
            usd_value = 0
            for quote in ['USDC', 'USDT', 'BUSD']:
                symbol = f"{asset}{quote}"
                if symbol in all_tickers:
                    usd_value = b['total'] * all_tickers[symbol]
                    break
        
        total_usdc_value += usd_value
        
        if usd_value > 0.01 or b['total'] > 0.001:
            print(f"{asset:10s} | {b['free']:>15.8f} | {b['locked']:>15.8f} | ${usd_value:>14.2f}")
    
    print("-" * 70)
    print(f"{'SPOT TOTAL':10s} | {'':<15s} | {'':<15s} | ${total_usdc_value:>14.2f}")
    
    # Check Earn/Savings products
    earn_total = 0.0
    print("\n📈 EARN/SAVINGS PRODUCTS:")
    print("-" * 70)
    
    try:
        # Simple Earn Flexible
        flexible = client.get_simple_earn_flexible_product_list()
        if flexible and 'rows' in flexible:
            for p in flexible['rows']:
                if float(p.get('totalAmount', 0)) > 0:
                    print(f"Flexible: {p['asset']} = {p['totalAmount']}")
                    earn_total += float(p.get('totalAmount', 0))
    except Exception as e:
        print(f"Flexible Earn: {e}")
    
    try:
        # Simple Earn Locked
        locked = client.get_simple_earn_locked_product_list()
        if locked and 'rows' in locked:
            for p in locked['rows']:
                if float(p.get('totalAmount', 0)) > 0:
                    print(f"Locked: {p['asset']} = {p['totalAmount']}")
                    earn_total += float(p.get('totalAmount', 0))
    except Exception as e:
        print(f"Locked Earn: {e}")
    
    try:
        # Get account positions
        positions = client.get_simple_earn_account()
        if positions:
            print(f"Simple Earn Account: {positions}")
    except Exception as e:
        pass
    
    if earn_total == 0:
        print("No Earn products found (or API doesn't have permissions)")
    
    # Pool mining earnings
    print("\n⛏️ POOL MINING:")
    print("-" * 70)
    try:
        pool_account = client.get_mining_pool_account()
        if pool_account and 'data' in pool_account:
            for entry in pool_account['data']:
                print(f"Pool: {entry}")
    except Exception as e:
        print(f"Pool API: {e}")
    
    # Final summary
    print("\n" + "=" * 70)
    print(f"💎 SPOT TOTAL:       ${total_usdc_value:.2f}")
    print(f"💎 EARN TOTAL:       ${earn_total:.2f}")
    print(f"💎 GRAND TOTAL:      ${total_usdc_value + earn_total:.2f}")
    print("=" * 70)
    
    # Account status
    print(f"\nAccount Can Trade: {account['canTrade']}")
    print(f"Account Can Withdraw: {account['canWithdraw']}")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
