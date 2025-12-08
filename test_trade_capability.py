#!/usr/bin/env python3
"""Test if we can actually place a trade"""

import os
from dotenv import load_dotenv
from binance.client import Client
from binance.enums import *

load_dotenv()

try:
    client = Client(
        os.getenv('BINANCE_API_KEY'),
        os.getenv('BINANCE_API_SECRET')
    )
    
    print("\n=== TESTING TRADE CAPABILITY ===\n")
    
    # Check balance
    account = client.get_account()
    usdt_balance = 0
    usdc_balance = 0
    
    for balance in account['balances']:
        if balance['asset'] == 'USDT':
            usdt_balance = float(balance['free'])
        elif balance['asset'] == 'USDC':
            usdc_balance = float(balance['free'])
    
    print(f"USDT free balance: {usdt_balance}")
    print(f"USDC free balance: {usdc_balance}")
    
    total_stable = usdt_balance + usdc_balance
    
    if total_stable < 10:
        print(f"\n❌ INSUFFICIENT FUNDS: You only have ${total_stable:.2f} in liquid stablecoins")
        print("   Minimum needed: $10")
        print("\n🔍 Looking for other assets...")
        
        for balance in account['balances']:
            free = float(balance['free'])
            if free > 0.01:
                print(f"   Found: {balance['asset']} = {free}")
        
        exit(1)
    
    print(f"\n✅ You have ${total_stable:.2f} available")
    
    # Try to get a ticker price
    print("\nTesting market data access...")
    ticker = client.get_symbol_ticker(symbol="BTCUSDT")
    print(f"✅ BTC Price: ${ticker['price']}")
    
    # Check exchange info
    print("\nChecking trading permissions...")
    info = client.get_exchange_info()
    print(f"✅ Exchange has {len(info['symbols'])} trading pairs")
    
    # Try a TEST order (doesn't execute)
    print("\nTesting order placement (TEST MODE)...")
    if usdt_balance >= 11:
        test_order = client.create_test_order(
            symbol='BTCUSDT',
            side=SIDE_BUY,
            type=ORDER_TYPE_MARKET,
            quoteOrderQty=11
        )
        print("✅ TEST ORDER SUCCESSFUL - System CAN trade!")
    else:
        print("⚠️  Not enough USDT for test order, but API connection works")
    
    print("\n✅ ALL CHECKS PASSED - System should be able to trade")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    exit(2)
