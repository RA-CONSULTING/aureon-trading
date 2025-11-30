import os
import sys
import json
import time
from kraken_client import KrakenClient

if len(sys.argv) < 2:
    print("Usage: python manual_sell.py <SYMBOL> [QUANTITY]")
    print("Example: python manual_sell.py ETHGBP")
    sys.exit(1)

symbol = sys.argv[1].upper()
qty_arg = float(sys.argv[2]) if len(sys.argv) > 2 else None

# Load config to find position
try:
    with open('aureon_kraken_state.json', 'r') as f:
        state = json.load(f)
        positions = state.get('positions', {})
except FileNotFoundError:
    print("No state file found.")
    positions = {}

pos = positions.get(symbol)
if pos:
    print(f"Found tracked position for {symbol}: {pos['quantity']} units @ {pos['entry_price']}")
    qty_to_sell = qty_arg if qty_arg else float(pos['quantity'])
else:
    print(f"⚠️  Warning: {symbol} is NOT in the bot's state file.")
    qty_to_sell = qty_arg

if not qty_to_sell:
    print("Error: You must specify a quantity if the symbol is not in the state file.")
    sys.exit(1)

print(f"\nPreparing to sell {qty_to_sell} of {symbol}...")

# Initialize Client
api_key = os.environ.get('KRAKEN_API_KEY')
api_secret = os.environ.get('KRAKEN_API_SECRET')
client = KrakenClient(api_key, api_secret)

confirm = input(f"Type 'YES' to confirm MARKET SELL of {qty_to_sell} {symbol}: ")
if confirm != "YES":
    print("Aborted.")
    sys.exit(0)

try:
    res = client.place_market_order(symbol, 'SELL', quantity=qty_to_sell)
    print(f"✅ Sold {symbol}: {res.get('orderId', 'Unknown ID')}")
    
    # Update state file if it was a tracked position
    if pos and not qty_arg: # Only remove if we sold the full tracked amount
        print("Removing from state file...")
        del positions[symbol]
        state['positions'] = positions
        with open('aureon_kraken_state.json', 'w') as f:
            json.dump(state, f, indent=2)
        print("State updated.")
        
except Exception as e:
    print(f"❌ Failed to sell {symbol}: {e}")
