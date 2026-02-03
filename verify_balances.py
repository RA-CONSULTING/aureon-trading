
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import asyncio

try:
    from dotenv import load_dotenv
except ImportError:  # Fallback when python-dotenv is not installed
    def load_dotenv(*args, **kwargs):  # type: ignore[unused-arg]
        return None

# Load env vars
load_dotenv()

async def check_balances():
    print("🔍 VERIFYING REAL BALANCES FROM EXCHANGES...")
    
    # Check Alpaca
    try:
        from alpaca_client import AlpacaClient
        alpaca = AlpacaClient()
        acct = alpaca.get_account()
        print(f"\n🦙 ALPACA ACCOUNT ({'PAPER' if alpaca.use_paper else 'LIVE'}):")
        if isinstance(acct, dict) and 'equity' in acct:
            print(f"   Status: {acct.get('status', 'Unknown')}")
            print(f"   Equity: ${float(acct.get('equity', 0)):,.2f}")
            print(f"   Cash:   ${float(acct.get('cash', 0)):,.2f}")
            print(f"   Buying Power: ${float(acct.get('buying_power', 0)):,.2f}")
        else:
            print(f"   ⚠️ Unexpected response: {acct}")
    except Exception as e:
        print(f"\n🦙 Alpaca Error: {e}")

    # Check Kraken
    try:
        from kraken_client import KrakenClient, get_kraken_client
        kraken = get_kraken_client()
        bal = kraken.get_account_balance()
        print(f"\n🐙 KRAKEN BALANCES:")
        if bal:
            for asset, amount in bal.items():
                if float(amount) > 0:
                    print(f"   {asset}: {amount}")
        else:
            print("   No balances found or error.")
    except Exception as e:
        print(f"\n🐙 Kraken Error: {e}")

    # Check Binance
    try:
        from binance_client import BinanceClient
        binance = BinanceClient()
        # Use simple account() method
        info = binance.account()
        print(f"\n🟡 BINANCE BALANCES:")
        if info and 'balances' in info:
            for b in info['balances']:
                free = float(b['free'])
                locked = float(b['locked'])
                if free + locked > 0:
                    print(f"   {b['asset']}: {free} (Locked: {locked})")
        else:
            print("   No balances found or error.")
    except Exception as e:
        print(f"\n🟡 Binance Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_balances())
