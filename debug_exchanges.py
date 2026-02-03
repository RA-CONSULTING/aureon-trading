from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
from binance_client import BinanceClient
from kraken_client import KrakenClient, get_kraken_client
import json
import os

def debug_balances():
    print("\n🧐 --- BINANCE RAW DEBUG ---")
    try:
        if not os.getenv("BINANCE_API_KEY"):
            print("⚠️ No Binance API Key in env")
        else:
            b = BinanceClient()
            acct = b.account()
            # Print ALL non-zero balances
            found_any = False
            if acct and 'balances' in acct:
                for x in acct['balances']:
                    total = float(x['free']) + float(x['locked'])
                    if total > 0:
                        print(f"💰 {x['asset']}: {total} (Free: {x['free']}, Locked: {x['locked']})")
                        found_any = True
            else:
                print("❌ No 'balances' key in response or empty.")
                print(f"Raw Response keys: {acct.keys() if acct else 'None'}")
            
            if not found_any:
                print("⚠️ Account exists but ALL balances are 0.0")
            
    except Exception as e:
        print(f"🔥 Error: {e}")

    print("\n🧐 --- KRAKEN RAW DEBUG ---")
    try:
        if not os.getenv("KRAKEN_API_KEY"):
            print("⚠️ No Kraken API Key in env")
        else:
            k = get_kraken_client()
            # Debug the internal account() method vs get_account_balance
            print("Calling k.account()...")
            raw = k.account()
            
            found_any = False
            if raw and 'balances' in raw:
                for x in raw['balances']:
                    # Kraken client normalizes names in account() method usually, let's see
                    # output is list of dicts: {'asset': 'BTC', 'free': ..., 'locked': ...}
                    try:
                        total = float(x.get('free', 0)) + float(x.get('locked', 0))
                    except:
                        total = 0
                        
                    if total > 0:
                        print(f"💰 {x.get('asset')}: {total}")
                        found_any = True
            else:
                print(f"❌ Raw response weird: {raw}")
                
            if not found_any:
                print("⚠️ Account exists but ALL balances are 0.0")

    except Exception as e:
        print(f"🔥 Error: {e}")

if __name__ == "__main__":
    debug_balances()
