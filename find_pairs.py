import requests
import json

symbols = ["BTC", "DOGE", "SOL", "XRP", "LTC", "ADA", "HBAR", "TUSD"]
target_quote = ["USD", "USDC"]

url = "https://api.kraken.com/0/public/AssetPairs"
try:
    resp = requests.get(url)
    data = resp.json()
    pairs = data.get('result', {})
    
    print("Found pairs:")
    for name, info in pairs.items():
        base = info.get('base')
        quote = info.get('quote')
        altname = info.get('altname')
        
        # Check if this pair matches any of our symbols
        for sym in symbols:
            # Kraken uses XBT for BTC, XDG for DOGE
            check_sym = sym
            if sym == "BTC": check_sym = "XBT"
            if sym == "DOGE": check_sym = "XDG"
            
            if (check_sym in base or sym in base) and (quote in ["ZUSD", "USDC", "USD"]):
                print(f"  {sym}: {name} (Alt: {altname})")

except Exception as e:
    print(e)
