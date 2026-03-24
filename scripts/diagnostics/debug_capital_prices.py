
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
import json
from dotenv import load_dotenv
from capital_client import CapitalClient

load_dotenv()

def check_capital():
    print("Checking Capital.com...")
    api_key = os.environ.get("CAPITAL_API_KEY")
    password = os.environ.get("CAPITAL_PASSWORD")
    identifier = os.environ.get("CAPITAL_IDENTIFIER")
    
    if not all([api_key, password, identifier]):
        print("Missing Capital credentials")
        return

    # client = CapitalClient(api_key, password, identifier) # Incorrect
    client = CapitalClient() # Correct, reads from env
    # if not client.connect(): # connect is not a method, _create_session is called in init
    #    print("Failed to connect")
    #    return
    
    if not client.enabled:
        print("Client disabled (check logs/credentials)")
        return

    print("Connected. Searching for tickers...")
    
    # Try to find BTC
    print("Searching for 'BTC'...")
    # We can't easily change the search term in get_24h_tickers without modifying the class or adding a method.
    # But get_ticker uses searchTerm.
    
    ticker = client.get_ticker('BTC')
    print(f"Ticker for 'BTC': {ticker}")

    ticker = client.get_ticker('Bitcoin')
    print(f"Ticker for 'Bitcoin': {ticker}")
    
    # Let's try to use the internal method if possible or just rely on get_ticker
    # get_ticker returns the first match.
    
    # Let's try to list markets with 'BTC' using the same logic as get_24h_tickers but we can't pass params there.
    # We will just use get_ticker for now.
    
    import requests
    headers = client._get_headers()
    
    print("Fetching Market Navigation...")
    url = f"{client.base_url}/marketnavigation"
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        nodes = data.get('nodes', [])
        for node in nodes:
            print(f"Node: {node.get('name')} (ID: {node.get('id')})")
            if 'Crypto' in node.get('name', '') or 'Bitcoin' in node.get('name', ''):
                print(f"FOUND CRYPTO NODE: {node}")
    else:
        print(f"Error fetching navigation: {resp.text}")

if __name__ == "__main__":
    check_capital()
