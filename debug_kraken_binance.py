import os
import sys
import time
from dotenv import load_dotenv

# Load env before imports
load_dotenv("/workspaces/aureon-trading/.env")

from binance_client import BinanceClient
from kraken_client import KrakenClient

def debug_check():
    print("=== DEBUG START ===")
    
    # KRAKEN
    print("\n\n--- KRAKEN ---")
    try:
        # Check env vars expected by Client
        k_key = os.getenv("KRAKEN_API_KEY")
        k_secret = os.getenv("KRAKEN_API_SECRET")
        print(f"   Env KRAKEN_API_KEY present: {bool(k_key)}")
        print(f"   Env KRAKEN_API_SECRET present: {bool(k_secret)}")
        
        # Instantiate with NO ARGS
        kraken = KrakenClient()
        
        # 1. Check Account
        print("1. Testing account()...")
        try:
            acct = kraken.account()
            print(f"✅ account() result keys: {list(acct.keys())}")
            if 'balances' in acct:
                print(f"   Balances count: {len(acct['balances'])}")
                print(f"   Example Bal: {acct['balances'][0] if acct['balances'] else 'None'}")
            else:
                print(f"   Full Result: {acct}")
        except Exception as e:
            print(f"❌ account() failed: {e}")

        # 2. Check get_account_balance()
        print("2. Testing get_account_balance()...")
        bal = kraken.get_account_balance()
        print(f"   Balance Map count: {len(bal)}")
        print(f"   Sample: {list(bal.items())[:5] if bal else 'None'}")
        
        # 3. Check Ledgers
        print("3. Testing get_ledgers()...")
        try:
            ledgers = kraken.get_ledgers()
            print(f"   Result type: {type(ledgers)}")
            if ledgers:
                print(f"   Count: {len(ledgers)}")
                first_k = next(iter(ledgers))
                print(f"   Sample ({first_k}): {ledgers[first_k]}")
            else:
                print("   (No ledgers returned)")
        except Exception as e:
            print(f"❌ get_ledgers() failed: {e}")

    except Exception as e:
        print(f"❌ KRAKEN INIT FAILED: {e}")

    # BINANCE
    print("\n\n--- BINANCE ---")
    try:
        b_key = os.getenv("BINANCE_API_KEY")
        b_secret = os.getenv("BINANCE_API_SECRET")
        print(f"   Env BINANCE_API_KEY present: {bool(b_key)}")

        # Instantiate with NO ARGS
        binance = BinanceClient()
        
        # Test ZROUSDT
        print("1. Testing get_all_orders('ZROUSDT', limit=1000)...")
        orders = binance.get_all_orders("ZROUSDT", limit=1000)
        print(f"   Result count: {len(orders)}")
        if orders:
            # Check for buys
            buys = [o for o in orders if o['side'] == 'BUY' and o['status'] == 'FILLED']
            print(f"   Filled BUYs: {len(buys)}")
            if buys:
                print(f"   Sample BUY: {buys[0]}")
        else:
            print("   (No orders returned)")

    except Exception as e:
        print(f"❌ BINANCE FAILED: {e}")

    print("\n=== DEBUG END ===")

if __name__ == "__main__":
    debug_check()
