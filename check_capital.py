import os
from capital_client import CapitalClient

def main():
    print("--- CAPITAL.COM CHECK ---")
    api_key = os.getenv('CAPITAL_API_KEY')
    identifier = os.getenv('CAPITAL_IDENTIFIER')
    password = os.getenv('CAPITAL_PASSWORD')
    
    print(f"API Key: {'SET' if api_key else 'NOT SET'}")
    print(f"Identifier: {'SET' if identifier else 'NOT SET'}")
    print(f"Password: {'SET' if password else 'NOT SET'}")
    
    if not (api_key and identifier and password):
        print("⚠️  Please set CAPITAL_API_KEY, CAPITAL_IDENTIFIER, and CAPITAL_PASSWORD in .env")
        return

    client = CapitalClient()
    if client.enabled:
        print("✅ Session Established!")
        
        print("\n--- BALANCES ---")
        bals = client.get_account_balance()
        print(bals)
        
        print("\n--- TICKER CHECK (BTCUSD) ---")
        ticker = client.get_ticker("BTCUSD")
        print(ticker)
        
        print("\n--- MARKET SCAN ---")
        # Debug raw response
        url = f"{client.base_url}/markets"
        params = {'searchTerm': 'BTC', 'limit': 1}
        import requests
        res = requests.get(url, headers=client._get_headers(), params=params)
        print(f"Raw BTC Search: {res.json()}")

        tickers = client.get_24h_tickers()
        print(f"Found {len(tickers)} markets")
        if tickers:
            print(f"Sample: {tickers[0]}")
    else:
        print("❌ Failed to connect.")

if __name__ == "__main__":
    main()
