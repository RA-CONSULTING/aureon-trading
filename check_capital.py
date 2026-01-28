from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import json
from capital_client import CapitalClient

def main():
    print("--- CAPITAL.COM DIAGNOSTIC ---")
    client = CapitalClient()
    if client.enabled and client.cst:
        print("✅ Connected")
        
        print("\n--- RAW POSITION DATA ---")
        res = client._request('GET', '/positions')
        positions = res.json().get('positions', [])
        
        if positions:
            # Print FIRST position completely to see structure
            print(json.dumps(positions[0], indent=2))
        else:
            print("No positions found.")

    else:
        print("❌ Not connected")

if __name__ == "__main__":
    main()
