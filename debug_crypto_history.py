
import os
import sys
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.append(os.getcwd())

from binance_client import BinanceClient
from kraken_client import KrakenClient

def debug_binance():
    print("\n" + "="*50)
    print("🔍 DIAGNOSTIC: BINANCE")
    print("="*50)
    
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_SECRET_KEY")
    
    if not api_key:
        print("❌ Missing BINANCE_API_KEY")
        return

    # FIXED: No args for init (loads from env)
    client = BinanceClient()
    
    # Check Connectivity
    try:
        status = client.get_system_status()
        print(f"✅ System Status: {status.get('msg', 'OK')}")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        return

    # Check Balances
    try:
        account = client.account()
        balances = [b for b in account.get("balances", []) if float(b.get("free", 0)) > 0 or float(b.get("locked", 0)) > 0]
        
        if not balances:
            print("⚠️ No non-zero balances found.")
        else:
            print(f"💰 Found {len(balances)} assets with balance:")
            for b in balances:
                asset = b['asset']
                amount = float(b['free']) + float(b['locked'])
                print(f"   - {asset}: {amount}")
                
                # Try to find trades for this asset
                quotes = ['USDT', 'USDC', 'GBP', 'EUR', 'BTC', 'ETH', 'FDUSD']
                found_trades = False
                
                for quote in quotes:
                    if asset == quote: continue
                    symbol = f"{asset}{quote}"
                    try:
                        trades = client.get_my_trades(symbol, limit=5)
                        orders = client.get_all_orders(symbol, limit=5, silent=True)
                        
                        if trades:
                            print(f"     ✅ Found {len(trades)} trades for {symbol}")
                            print(f"        Sample Trade: {trades[0]}")
                            found_trades = True
                        
                        if orders:
                            print(f"     ✅ Found {len(orders)} orders for {symbol}")
                            filled_orders = [o for o in orders if o['status'] == 'FILLED']
                            print(f"        Filled: {len(filled_orders)}")
                            if filled_orders:
                                print(f"        Sample Order: {filled_orders[0]}")
                            found_trades = True
                            
                            # Calculate cost basis from Orders if possible
                            if filled_orders:
                                total_qty = 0.0
                                total_cost = 0.0
                                for o in filled_orders:
                                    if o['side'] == 'BUY':
                                        qty = float(o['executedQty'])
                                        cost = float(o['cummulativeQuoteQty'])
                                        total_qty += qty
                                        total_cost += cost
                                if total_qty > 0:
                                    print(f"        Derived Avg Buy Price: {total_cost/total_qty}")

                        if not trades and not orders:
                            # print(f"     . No trades for {symbol}")
                            pass
                    except Exception as e:
                        print(f"     x Error checking {symbol}: {str(e)}")
                        pass
                        
                if not found_trades:
                    print(f"     ⚠️ No trades found for {asset} with standard pairs.")
                    
    except Exception as e:
        print(f"❌ Account/Trade fetch failed: {e}")

def debug_kraken():
    print("\n" + "="*50)
    print("🔍 DIAGNOSTIC: KRAKEN")
    print("="*50)
    
    api_key = os.getenv("KRAKEN_API_KEY")
    api_secret = os.getenv("KRAKEN_PRIVATE_KEY")
    
    if not api_key:
        print("❌ Missing KRAKEN_API_KEY")
        return

    client = KrakenClient(api_key, api_secret)
    
    # Check Balances
    try:
        balance = client.get_account_balance()
        if not balance:
            print("⚠️ No balances returned.")
        else:
            print(f"💰 Balances: {balance}")
            
        print("\n--- Checking History Sources ---")
        
        # 1. Check Trades History
        print("1️⃣  Checking 'TradesHistory' endpoint...")
        trades = client.get_trades_history()
        if trades:
            count = len(trades)
            print(f"   ✅ Found {count} historical trades.")
            first_key = list(trades.keys())[0]
            print(f"   Sample Key: {first_key}")
            print(f"   Sample Data: {trades[first_key]}")
            
            # Check Pairs in history
            pairs = set(t.get('pair') for t in trades.values())
            print(f"   Pairs found in history: {pairs}")
        else:
            print("   ⚠️ TradesHistory returned empty/None.")

        # 2. Check Ledgers (User suggestion)
        print("\n2️⃣  Checking 'Ledgers' endpoint...")
        ledgers = client.get_ledgers()
        if ledgers:
            count = len(ledgers)
            print(f"   ✅ Found {count} ledger entries.")
            first_key = list(ledgers.keys())[0]
            print(f"   Sample Key: {first_key}")
            print(f"   Sample Data: {ledgers[first_key]}")
            
            # types in ledger
            types = set(l.get('type') for l in ledgers.values())
            print(f"   Ledger Types found: {types}")
        else:
            print("   ⚠️ Ledgers returned empty/None.")
            
    except Exception as e:
        print(f"❌ Kraken Diagnostics failed: {e}")

if __name__ == "__main__":
    debug_binance()
    debug_kraken()
