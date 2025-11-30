import os
import sys
import json
import time
from kraken_client import KrakenClient

# Load config
try:
    with open('aureon_kraken_state.json', 'r') as f:
        state = json.load(f)
        positions = state.get('positions', {})
except FileNotFoundError:
    print("No state file found.")
    sys.exit(1)

if not positions:
    print("No open positions found in state file.")
    sys.exit(0)

print(f"Found {len(positions)} open positions:")
for sym, pos in positions.items():
    print(f" - {sym}: {pos['quantity']} units (Entry: {pos['entry_price']})")

confirm = input("\n⚠️  WARNING: This will market sell ALL positions immediately. Type 'SELL ALL' to confirm: ")

if confirm != "SELL ALL":
    print("Aborted.")
    sys.exit(0)

# Initialize Client
api_key = os.environ.get('KRAKEN_API_KEY')
api_secret = os.environ.get('KRAKEN_API_SECRET')
client = KrakenClient(api_key, api_secret)

print("\n🚀 Executing Emergency Sell...")

for sym, pos in positions.items():
    print(f"Selling {sym}...")
    try:
        res = client.place_market_order(sym, 'SELL', quantity=pos['quantity'])
        print(f"✅ Sold {sym}: {res.get('orderId', 'Unknown ID')}")
    except Exception as e:
        print(f"❌ Failed to sell {sym}: {e}")

print("\nDone. Please restart the main bot with FRESH_START=1 to clear the state if you sold everything.")
