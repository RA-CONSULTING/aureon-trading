import requests
import json
import time

# Positions from the state file
positions = {
    "TUSDUSD": {"entry_price": 0.9789, "quantity": 11.80156, "entry_value": 11.552547084},
    "BTCUSDC": {"entry_price": 89471.435, "quantity": 6.74e-06, "entry_value": 0.6030374719},
    "DOGEUSDC": {"entry_price": 0.13705, "quantity": 55.0, "entry_value": 7.53775},
    "SOLUSDC": {"entry_price": 131.79, "quantity": 0.057, "entry_value": 7.51203},
    "XRPUSDC": {"entry_price": 2.0046, "quantity": 3.7, "entry_value": 7.41702},
    "LTCUSDC": {"entry_price": 80.33, "quantity": 0.093, "entry_value": 7.470689999999999},
    "ADAUSDC": {"entry_price": 0.4041, "quantity": 18.6, "entry_value": 7.516260000000001},
    "HBARUSDC": {"entry_price": 0.12188, "quantity": 61.0, "entry_value": 7.43468}
}

# Map to Kraken pairs if needed (Kraken often uses XBT instead of BTC)
pair_map = {
    "BTCUSDC": "XBTUSDC",
    "TUSDUSD": "TUSDUSD",
    "DOGEUSDC": "XDGUSDC",
    "SOLUSDC": "SOLUSDC",
    "XRPUSDC": "XRPUSDC",
    "LTCUSDC": "LTCUSDC",
    "ADAUSDC": "ADAUSDC",
    "HBARUSDC": "HBARUSD"
}

pairs_str = ",".join([pair_map.get(k, k) for k in positions.keys()])
url = f"https://api.kraken.com/0/public/Ticker?pair={pairs_str}"

print(f"Fetching prices for: {pairs_str}")
try:
    resp = requests.get(url)
    data = resp.json()
    
    if data.get('error'):
        print(f"Error fetching prices: {data['error']}")
        # Try fetching individually if batch fails or some pairs are wrong
    
    results = data.get('result', {})
    
    print("\n📊 UNREALIZED P&L ANALYSIS")
    print("="*80)
    print(f"{'SYMBOL':<10} | {'ENTRY':<10} | {'CURRENT':<10} | {'QTY':<10} | {'VALUE NOW':<10} | {'P&L (£)':<10} | {'P&L (%)':<10}")
    print("-" * 80)
    
    total_entry_value = 0
    total_current_value = 0
    
    # Helper to find the result key (Kraken returns weird keys like XXBTZUSD)
    def find_price(symbol):
        mapped = pair_map.get(symbol, symbol)
        # Direct match
        if mapped in results: return float(results[mapped]['c'][0])
        # Search for it
        for k in results:
            if mapped in k or k in mapped:
                return float(results[k]['c'][0])
        return None

    for sym, pos in positions.items():
        current_price = find_price(sym)
        
        entry_price = pos['entry_price']
        qty = pos['quantity']
        entry_val = pos['entry_value']
        
        total_entry_value += entry_val
        
        if current_price:
            current_val = qty * current_price
            pnl = current_val - entry_val
            pnl_pct = (pnl / entry_val) * 100
            
            total_current_value += current_val
            
            icon = "🟢" if pnl >= 0 else "🔴"
            print(f"{icon} {sym:<7} | {entry_price:<10.4f} | {current_price:<10.4f} | {qty:<10.4f} | £{current_val:<9.2f} | £{pnl:<9.2f} | {pnl_pct:+.2f}%")
        else:
            print(f"❓ {sym:<7} | {entry_price:<10.4f} | {'???':<10} | {qty:<10.4f} | {'???':<9} | {'???':<9} | ???")
            total_current_value += entry_val # Assume no change if price not found

    print("="*80)
    print(f"TOTAL ENTRY VALUE:   £{total_entry_value:.2f}")
    print(f"TOTAL CURRENT VALUE: £{total_current_value:.2f}")
    print(f"TOTAL UNREALIZED P&L: £{total_current_value - total_entry_value:.2f} ({(total_current_value - total_entry_value)/total_entry_value*100:.2f}%)")

except Exception as e:
    print(f"Script error: {e}")
