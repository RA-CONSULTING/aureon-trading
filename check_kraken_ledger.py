import os
from dotenv import load_dotenv
from kraken_client import KrakenClient, get_kraken_client
import time

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

def check_kraken_ledger():
    """
    Connects to Kraken and fetches the ledger history.
    """
    print("🐙 Initializing Kraken client...")
    try:
        client = get_kraken_client()
        if not client.api_key or not client.api_secret:
            print("❌ ERROR: Kraken API key or secret not found in .env file.")
            return

        print("🔐 Credentials loaded. Fetching ledger history from Kraken...")
        
        # Fetch ledger history
        ledger_history = client.get_ledgers()
        
        if not ledger_history:
            print("No ledger history returned from Kraken API.")
            return

        count = len(ledger_history)

        print(f"\n✅ Found {count} total ledger entries. Showing the most recent entries:\n")

        # Print details for each ledger entry
        for ledger_id, ledger_info in ledger_history.items():
            ref_id = ledger_info.get('refid')
            ledger_time = ledger_info.get('time')
            ledger_type = ledger_info.get('type')
            asset = ledger_info.get('asset')
            amount = ledger_info.get('amount')
            fee = ledger_info.get('fee')
            balance = ledger_info.get('balance')
            
            print(f"  - Ledger ID: {ledger_id}")
            print(f"    - Ref ID: {ref_id}")
            print(f"    - Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(ledger_time)))}")
            print(f"    - Type: {ledger_type}, Asset: {asset}")
            print(f"    - Amount: {amount}, Fee: {fee}")
            print(f"    - New Balance: {balance}\n")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    check_kraken_ledger()
