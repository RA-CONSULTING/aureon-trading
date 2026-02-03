from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
from binance_client import BinanceClient
import json
import logging
import time
from datetime import datetime, timedelta

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def diagnose():
    client = get_binance_client()
    
    # Target problem assets from previous logs
    target_assets = ['ROSE', 'LPT', 'BEAMX']
    
    print("\n🔍 BINANCE API DIAGNOSTIC 🔍")
    print("="*60)
    
    if not client.api_key:
        print("❌ Connect: No API Key found.")
        return

    print("✅ Connect: Client initialized.")
    acct = client.account()
    
    # --- FETCH CONVERT HISTORY (Global) ---
    print("⏳ Fetching Convert History (Last 90 days)...")
    all_conversions = []
    end_time = datetime.now()
    for i in range(3):
        start_time = end_time - timedelta(days=30)
        ts_end = int(end_time.timestamp() * 1000)
        ts_start = int(start_time.timestamp() * 1000)
        try:
            params = {"startTime": ts_start, "endTime": ts_end, "limit": 500}
            res = client._signed_request("GET", "/sapi/v1/convert/tradeFlow", params)
            if res and 'list' in res:
                all_conversions.extend(res['list'])
                print(f"   Chunk {i+1}: Found {len(res['list'])} conversions.")
        except Exception as e:
            print(f"   Chunk {i+1} Error: {e}")
        end_time = start_time
        time.sleep(0.2)
    print(f"✅ Total Conversions Found: {len(all_conversions)}")

    print(f"✅ Account: Found {len(acct.get('balances', []))} balances.")
    
    for asset in target_assets:
        print(f"\n👉 ANALYZING ASSET: {asset}")
        
        # 1. Check Balance
        qty = client.get_free_balance(asset)
        print(f"   Balance: {qty} {asset}")
        
        # 2. Check Pairs
        pairs_to_check = [f"{asset}USDT", f"{asset}BTC", f"{asset}ETH", f"{asset}BUSD", f"{asset}BNB"]
        
        for pair in pairs_to_check:
            print(f"   🔎 Checking Pair: {pair}")
            
            # 3. Check Price/Existence
            try:
                ticker = client.get_ticker(pair)
                price = ticker.get('price')
                if not price or float(price) == 0:
                    print(f"      Status: Pair likely inactive or no price (Ticker: {ticker})")
                    continue
                print(f"      Status: ACTIVE (Price: {price})")
            except Exception as e:
                print(f"      Status: ERROR ({e})")
                continue

            # 4. Check MyTrades (Spot)
            try:
                trades = client.get_my_trades(pair, limit=10) # Just get last 10
                print(f"      📚 MyTrades (limit=10): Found {len(trades)} entries.")
                if trades:
                    print(f"          Last Trade: {trades[-1]}")
                else:
                    print("          (Result is empty list [])")
            except Exception as e:
                print(f"      ❌ MyTrades Error: {e}")

            # 5. Check AllOrders (Spot)
            try:
                orders = client.get_all_orders(pair, limit=10)
                print(f"      🗂️ AllOrders (limit=10): Found {len(orders)} entries.")
                if orders:
                    buy_orders = [o for o in orders if o['side'] == 'BUY']
                    print(f"          Buy Orders: {len(buy_orders)} found in last 10.")
                    if buy_orders:
                         print(f"          Last Buy: {buy_orders[-1]}")
                else:
                    print("          (Result is empty list [])")
            except Exception as e:
                print(f"      ❌ AllOrders Error: {e}")

        # 6. Check Convert History (Filtered)
        print(f"   🔎 Checking Convert History for {asset}...")
        try:
            asset_converts = [c for c in all_conversions if c.get('fromAsset') == asset or c.get('toAsset') == asset]
            print(f"      🔄 Conversions: Found {len(asset_converts)} entries.")
            for c in asset_converts[:5]:
                 ts = datetime.fromtimestamp(c['createTime']/1000).strftime('%Y-%m-%d %H:%M:%S')
                 print(f"          - {ts}: {c['fromAsset']} -> {c['toAsset']} ({c['toAmount']})")
        except Exception as e:
            print(f"      ❌ Convert Check Error: {e}")

    print("-" * 60)
    print("🧠 TESTING NEW COST BASIS CALCULATION")
    for asset in target_assets:
        pair = f"{asset}USDT"
        print(f"👉 Calculating Cost Basis for {pair}...")
        try:
            basis = client.calculate_cost_basis(pair)
            if basis:
                print(f"   ✅ SUCCESS: {basis}")
            else:
                print("   ❌ RESULT: None (Still no history found)")
        except Exception as e:
            print(f"   ⚠️ ERROR: {e}")

if __name__ == "__main__":
    diagnose()
