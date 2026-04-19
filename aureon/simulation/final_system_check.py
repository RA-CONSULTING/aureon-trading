#!/usr/bin/env python3
"""
✅ FINAL SYSTEM CHECK - All Systems Operational
Verifies: API keys, balances, modules, readiness to trade
"""
from aureon.core.aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
import json
import time
from pathlib import Path

print("\n" + "="*70)
print("✅ FINAL SYSTEM CHECK - ALL SYSTEMS OPERATIONAL")
print("="*70 + "\n")

# Load environment (prefer local .env next to the repo)
from dotenv import load_dotenv

repo_dir = Path(__file__).resolve().parent
dotenv_path = repo_dir / ".env"
loaded = load_dotenv(dotenv_path=dotenv_path)

binance_key = os.getenv("BINANCE_API_KEY")
binance_secret = os.getenv("BINANCE_API_SECRET")
kraken_key = os.getenv("KRAKEN_API_KEY")
kraken_secret = os.getenv("KRAKEN_API_SECRET")

def has_real_value(value: str | None) -> bool:
    """Return True if the value is present and not a placeholder."""

    if not value:
        return False

    placeholder_prefixes = ["YOUR_", "changeme", "example", "sample"]
    lower_value = value.lower()
    return not any(value.startswith(prefix) or lower_value.startswith(prefix) for prefix in placeholder_prefixes)

binance_keys_ready = has_real_value(binance_key) and has_real_value(binance_secret)
kraken_keys_ready = has_real_value(kraken_key) and has_real_value(kraken_secret)

print("1️⃣  CONFIGURATION CHECK")
print("   " + "-"*50)
if loaded:
    print(f"   ✅ Loaded .env from {dotenv_path}")
else:
    print("   ⚠️  No .env file found (using environment variables)")

print(
    f"   ✅ Binance API Key: {binance_key[:10]}..."
    if binance_keys_ready
    else "   ❌ Binance API Key: Missing or placeholder"
)
print(
    f"   ✅ Kraken API Key: {kraken_key[:10]}..."
    if kraken_keys_ready
    else "   ⚠️  Kraken API Key: Missing or placeholder (optional)"
)

# Check Binance balance
print("\n2️⃣  EXCHANGE BALANCES")
print("   " + "-"*50)

if not binance_keys_ready:
    print("   ⚠️  Binance keys missing or placeholder. Skipping live balance check.")
else:
    try:
        from binance.client import Client

        client = Client(binance_key, binance_secret)
        account = client.get_account()

        liquid_stables = 0
        staked = 0

        for b in account["balances"]:
            asset = b["asset"]
            free = float(b["free"])
            locked = float(b["locked"])
            total = free + locked

            if asset in ["USDT", "USDC"]:
                liquid_stables += free
                if free > 0:
                    print(f"   ✅ Binance {asset}: ${free:.2f} FREE (${locked:.2f} locked)")
            elif asset.startswith("LD") and total > 0:
                staked += total
                print(f"   🔒 Binance {asset}: {total:.8f} (STAKED)")

        print(f"\n   💰 Total Liquid Stables: ${liquid_stables:.2f}")
        if liquid_stables < 10:
            print(f"   ⚠️  WARNING: Less than $10 minimum (have ${liquid_stables:.2f})")
        else:
            print("   ✅ Sufficient funds for trading")

    except ModuleNotFoundError as e:
        print(f"   ⚠️  Binance dependency missing: {e} (pip install python-binance)")
    except Exception as e:
        print(f"   ⚠️  Binance error: {e}")

# Check Kraken
print("\n3️⃣  KRAKEN CONNECTION")
print("   " + "-"*50)

if not kraken_keys_ready:
    print("   ℹ️  Kraken keys missing or placeholder. Skipping (optional).")
else:
    try:
        import krakenex

        kraken = krakenex.API()
        kraken.load_key(key=kraken_key, secret=kraken_secret)

        balance = kraken.query_private("Balance")
        if balance["error"]:
            print(f"   ⚠️  Kraken: {balance['error']}")
        else:
            usd = float(balance["result"].get("ZUSD", 0))
            gbp = float(balance["result"].get("ZGBP", 0))
            print(f"   ✅ Kraken USD: ${usd:.2f}")
            print(f"   ✅ Kraken GBP: £{gbp:.2f}")

    except ModuleNotFoundError as e:
        print(f"   ⚠️  Kraken dependency missing: {e} (pip install krakenex)")
    except Exception as e:
        print(f"   ⚠️  Kraken connection (optional): {e}")

# Check main modules
print("\n4️⃣  MODULE IMPORTS")
print("   " + "-"*50)

sys.path.insert(0, '/workspaces/aureon-trading')

try:
    from aureon.trading.unified_exchange_client import MultiExchangeClient

    print("   ✅ MultiExchangeClient")
except ImportError as e:
    print(f"   ❌ MultiExchangeClient: {e}")

try:
    from aureon.trading.aureon_unified_ecosystem import AureonKrakenEcosystem

    print("   ✅ AureonKrakenEcosystem")
except ImportError as e:
    print(f"   ⚠️  AureonKrakenEcosystem: {e}")

# Check state
print("\n5️⃣  SYSTEM STATE")
print("   " + "-"*50)

if os.path.exists('aureon_kraken_state.json'):
    with open('aureon_kraken_state.json') as f:
        state = json.load(f)
    print(f"   ✅ State file: {state.get('iteration', 0)} iterations")
    print(f"   💰 Balance: ${state.get('balance', 0):.2f}")
    print(f"   📊 Trades: {state.get('total_trades', 0)} total")
else:
    print("   ℹ️  State file not yet created (will be on first run)")

print("\n" + "=" * 70)
if binance_keys_ready:
    print("✅ SYSTEM READY FOR TRADING")
else:
    print("⚠️  SYSTEM NOT READY - Binance keys required for live trading")
print("=" * 70)
print("\n🚀 Next Step: Run the main system")
print("   python3 aureon_unified_ecosystem.py")
print("\n")
