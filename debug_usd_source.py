
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import asyncio

try:
    from dotenv import load_dotenv
except ImportError:  # Fallback when python-dotenv is unavailable
    def load_dotenv(*args, **kwargs):  # type: ignore[unused-arg]
        return None

# Load env vars
load_dotenv()

async def debug_usd_source():
    print("🕵️ DEBUGGING USD SOURCE...")
    combined = {}
    
    # KRAKEN
    try:
        from kraken_client import KrakenClient, get_kraken_client
        kraken = get_kraken_client()
        if hasattr(kraken, 'get_account_balance'):
            print("\n🐙 FETCHING KRAKEN...")
            raw = kraken.get_account_balance() or {}
            for asset, amount in raw.items():
                print(f"   Raw: {asset} = {amount}")
                try:
                    amount = float(amount)
                except:
                    continue
                if amount > 0:
                    clean = asset
                    if len(asset) == 4 and asset[0] in ('X', 'Z'):
                        clean = asset[1:]
                    if clean == 'XBT':
                        clean = 'BTC'
                    if clean == 'USD':
                        print(f"   🚨 FOUND USD ON KRAKEN: {amount}")
                    combined[clean] = combined.get(clean, 0) + amount
    except Exception as e:
        print(f"kraken error: {e}")

    # BINANCE
    try:
        from binance_client import BinanceClient
        binance = BinanceClient()
        if hasattr(binance, 'account'):
            print("\n🟡 FETCHING BINANCE...")
            acct = binance.account() or {}
            for bal in acct.get('balances', []):
                asset = bal.get('asset', '')
                free = float(bal.get('free', 0))
                if free > 0:
                    print(f"   Binance Asset: {asset} = {free}")
                    if asset == 'USD':
                        print(f"   🚨 FOUND USD ON BINANCE: {free}")
                    combined[asset] = combined.get(asset, 0) + free
    except Exception as e:
        print(f"binance error: {e}")

    # ALPACA
    try:
        from alpaca_client import AlpacaClient
        alpaca = AlpacaClient()
        if hasattr(alpaca, 'get_account'):
            print("\n🦙 FETCHING ALPACA...")
            acct = alpaca.get_account() or {}
            print(f"   Alpaca Account Data: {acct}")
            cash = float(acct.get('cash', 0))
            if cash > 0:
                print(f"   🚨 FOUND USD ON ALPACA: {cash}")
                combined['USD'] = combined.get('USD', 0) + cash
    except Exception as e:
        print(f"alpaca error: {e}")

    print("\n💰 FINAL COMBINED USD: ", combined.get('USD', 0))

if __name__ == "__main__":
    asyncio.run(debug_usd_source())
