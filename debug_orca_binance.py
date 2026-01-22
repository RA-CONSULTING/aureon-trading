import os
import sys

# Add workspace root to path
sys.path.append("/workspaces/aureon-trading")

from orca_complete_kill_cycle import OrcaKillCycle as Orca
from binance_client import BinanceClient

# Initialize Orca properly
orca = Orca()

# Force add binance client if not added (it usually loads from env)
if 'binance' not in orca.clients:
    print("Warning: Binance client not in orca.clients, attempting manual load")
    orca.clients['binance'] = BinanceClient()

orca.clients['binance'].uk_mode = True # Ensure UK mode is on for repro

print(f"Has Binance Client: {'binance' in orca.clients}")
if 'binance' in orca.clients:
    print(f"Binance UK Mode: {orca.clients['binance'].uk_mode}")

# We need to monkey patch the _scan_binance_market to see what's inside, or just run it and see.
# But running it as is produced 0 results before.
# Let's write a modified version of the function here and run it to see diagnostics.

def debug_scan_binance(self, min_change_pct: float, min_volume: float):
    print("DEBUG: Entering scan...")
    opportunities = []
    client = self.clients.get('binance')
    if not client:
        print("DEBUG: No client")
        return opportunities
    
    try:
        url = f"{client.base}/api/v3/ticker/24hr"
        print(f"DEBUG: Fetching {url}")
        r = client.session.get(url, timeout=10)
        print(f"DEBUG: Status Code: {r.status_code}")
        
        if r.status_code != 200:
            return opportunities
        
        tickers = r.json()
        print(f"DEBUG: Total tickers fetched: {len(tickers)}")
        
        count_restricted = 0
        count_futures_lookalike = 0
        count_zero_price = 0
        count_low_change = 0
        count_passed = 0
        
        for ticker in tickers:
            try:
                symbol = ticker.get('symbol', '')
                if not symbol:
                    continue
                
                # 🇬🇧 UK Mode Check
                if client.uk_mode and client.is_uk_restricted_symbol(symbol):
                    count_restricted += 1
                    continue
                
                # Futures/Margin Check
                if any(x in symbol for x in ['_', 'BULL', 'BEAR', 'UP', 'DOWN']):
                    count_futures_lookalike += 1
                    continue
                
                last_price = float(ticker.get('lastPrice', 0))
                change_pct = float(ticker.get('priceChangePercent', 0))
                volume = float(ticker.get('quoteVolume', 0)) # Using quote volume
                
                if last_price <= 0:
                    count_zero_price += 1
                    continue
                
                if abs(change_pct) < min_change_pct:
                    count_low_change += 1
                    continue
                    
                # Passed all checks
                count_passed += 1
                
                # Just print the first 5 passed ones
                if count_passed <= 5:
                    print(f"DEBUG: Passed: {symbol} Scan Change: {change_pct}% Vol: {volume}")

            except Exception as e:
                pass
        
        print(f"DEBUG: Summary:")
        print(f"  Restricted (UK): {count_restricted}")
        print(f"  Futures Lookalike: {count_futures_lookalike}")
        print(f"  Zero Price: {count_zero_price}")
        print(f"  Low Change (<{min_change_pct}%): {count_low_change}")
        print(f"  Passed: {count_passed}")
            
    except Exception as e:
        print(f"DEBUG: Error: {e}")

# Run the debug function
debug_scan_binance(orca, min_change_pct=0.5, min_volume=1000)
