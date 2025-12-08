#!/usr/bin/env python3
"""Show raw Binance balances"""

import os
import json
from dotenv import load_dotenv
from binance.client import Client

load_dotenv()

try:
    client = Client(
        os.getenv('BINANCE_API_KEY'),
        os.getenv('BINANCE_API_SECRET')
    )
    
    print("\n=== RAW BINANCE ACCOUNT DATA ===\n")
    
    # Get account info
    account = client.get_account()
    
    print("All balances with any value:")
    for balance in account['balances']:
        free = float(balance['free'])
        locked = float(balance['locked'])
        total = free + locked
        
        if total > 0:
            print(f"{balance['asset']}: free={free}, locked={locked}, total={total}")
    
    print("\n=== CHECKING EARN PRODUCTS ===\n")
    
    # Try to get Earn holdings
    try:
        savings = client.get_lending_position()
        if savings:
            print("Savings/Earn positions found:")
            print(json.dumps(savings, indent=2))
        else:
            print("No Earn positions found")
    except Exception as e:
        print(f"Cannot check Earn positions: {e}")
    
    print("\n=== ACCOUNT STATUS ===")
    print(f"Can Trade: {account['canTrade']}")
    print(f"Can Withdraw: {account['canWithdraw']}")
    print(f"Can Deposit: {account['canDeposit']}")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
