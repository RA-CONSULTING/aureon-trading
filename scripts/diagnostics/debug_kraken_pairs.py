
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import requests
import time

KRAKEN_BASE = "https://api.kraken.com"

def get_asset_pairs():
    print("Fetching AssetPairs...")
    r = requests.get(f"{KRAKEN_BASE}/0/public/AssetPairs")
    r.raise_for_status()
    data = r.json()
    if data.get("error"):
        raise RuntimeError(f"Error: {data['error']}")
    return data["result"]

def check_ticker(pairs):
    pairs_param = ",".join(pairs)
    r = requests.get(f"{KRAKEN_BASE}/0/public/Ticker", params={"pair": pairs_param})
    data = r.json()
    if data.get("error"):
        return False, data["error"]
    return True, None

def main():
    pairs_map = get_asset_pairs()
    print(f"Found {len(pairs_map)} pairs.")

    # Filter like kraken_client.py
    alts = []
    internal_map = {}
    
    for internal, info in pairs_map.items():
        alt = info.get("altname") or internal
        wsname = info.get("wsname", "")
        
        # Logic from kraken_client.py
        if any(alt.endswith(q) for q in ["USDC", "USDT", "USD", "EUR", "BTC", "XBT", "ETH", "GBP", "AUD", "CAD", "JPY"]):
            alts.append(alt)
            internal_map[alt] = internal
        elif "/" in wsname and wsname.split("/")[-1] in ["USDC", "USDT", "USD", "EUR", "BTC", "XBT", "ETH", "GBP", "AUD", "CAD", "JPY"]:
            alts.append(alt)
            internal_map[alt] = internal

    alts = sorted(set(alts))
    print(f"Filtered to {len(alts)} pairs of interest.")

    # Check in batches
    batch_size = 40
    bad_pairs = []

    for i in range(0, len(alts), batch_size):
        chunk = alts[i:i+batch_size]
        # Convert to internal names as kraken_client does
        chunk_internal = [internal_map[a] for a in chunk]
        
        success, error = check_ticker(chunk_internal)
        if not success:
            print(f"Batch {i//batch_size} failed: {error}")
            # Bisect to find bad pair
            for pair_alt, pair_int in zip(chunk, chunk_internal):
                s, e = check_ticker([pair_int])
                if not s:
                    print(f"  BAD PAIR: {pair_alt} ({pair_int}) -> {e}")
                    bad_pairs.append(pair_alt)
                time.sleep(0.1) # Rate limit
        else:
            print(f"Batch {i//batch_size} OK")
        
        time.sleep(1) # Rate limit

    print("\nSummary of bad pairs:")
    for p in bad_pairs:
        print(p)

if __name__ == "__main__":
    main()
