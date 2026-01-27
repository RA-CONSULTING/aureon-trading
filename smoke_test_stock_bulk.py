from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
from alpaca_client import AlpacaClient
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load env
load_dotenv()

def test_bulk_fetch():
    print("Testing Bulk Stock Data Fetch...")
    
    # Init client
    key = os.getenv("ALPACA_API_KEY")
    secret = os.getenv("ALPACA_SECRET_KEY")
    
    if not key or not secret:
        print("ERROR: API Keys missing")
        return

    # Client reads from env directly
    os.environ['ALPACA_API_KEY'] = key
    os.environ['ALPACA_SECRET_KEY'] = secret
    client = AlpacaClient() 
    
    # Test specific symbols
    symbols = ["AAPL", "MSFT", "TSLA", "NVDA", "AMD", "GOOGL", "AMZN", "META", "BRK.B", "LLY"]
    
    print(f"Fetching snapshots for {len(symbols)} symbols: {symbols}")
    
    try:
        if hasattr(client, 'get_stock_snapshots'):
            snapshots = client.get_stock_snapshots(symbols)
            print(f"Success! Received {len(snapshots)} snapshots.")
            for sym, snap in snapshots.items():
                price = snap.get('latestTrade', {}).get('p')
                print(f"  {sym}: {price}")
        else:
            print("ERROR: get_stock_snapshots not found on client!")
            
    except Exception as e:
        print(f"ERROR calling API: {e}")

if __name__ == "__main__":
    test_bulk_fetch()
