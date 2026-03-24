import os
from dotenv import load_dotenv
from kraken_client import KrakenClient, get_kraken_client

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

def check_kraken_orders():
    """
    Connects to Kraken and fetches the trade history.
    """
    print("🐙 Initializing Kraken client...")
    try:
        client = get_kraken_client()
        if not client.api_key or not client.api_secret:
            print("❌ ERROR: Kraken API key or secret not found in .env file.")
            return

        print("🔐 Credentials loaded. Fetching trade history from Kraken...")
        
        # Fetch raw trade history
        trades_history = client.get_trades_history()
        if not trades_history:
            print("No trade history returned from Kraken API.")
            return
        if isinstance(trades_history, dict) and 'trades' in trades_history:
            trades = trades_history.get('trades', {})
            count = trades_history.get('count', len(trades))
        else:
            trades = trades_history
            count = len(trades)

        print(f"\n✅ Found {count} total trades in history. Showing the {len(trades)} most recent trades:\n")

        if not trades:
            print("Trade history is empty.")
            return

        # Print details for each trade
        for trade_id, trade_info in trades.items():
            pair = trade_info.get('pair')
            side = trade_info.get('type')
            price = trade_info.get('price')
            cost = trade_info.get('cost')
            fee = trade_info.get('fee')
            vol = trade_info.get('vol')
            margin = trade_info.get('margin')
            time_s = trade_info.get('time')
            
            print(f"  - Order ID: {trade_id}")
            print(f"    - Pair: {pair}, Side: {side}")
            print(f"    - Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(time_s)))}")
            print(f"    - Volume: {vol} @ ${price}")
            print(f"    - Total Cost: ${cost}, Fee: ${fee}\n")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    check_kraken_orders()
