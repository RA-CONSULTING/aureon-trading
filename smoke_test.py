import os
import sys
import time
from aureon_kraken_ecosystem import AureonKrakenEcosystem, CONFIG

print("🚬 Running Smoke Test on Aureon Kraken Ecosystem...")

# 1. Initialize in Dry Run Mode
print("\n1. Initializing Ecosystem (Dry Run)...")
try:
    bot = AureonKrakenEcosystem(initial_balance=1000.0, dry_run=True)
    print("✅ Initialization successful.")
except Exception as e:
    print(f"❌ Initialization failed: {e}")
    sys.exit(1)

# 2. Check Lattice Engine
print("\n2. Checking Lattice Engine...")
try:
    state = bot.lattice.get_state()
    print(f"✅ Lattice State: {state.phase} ({state.frequency}Hz)")
    print(f"   Risk Mod: {state.risk_mod}x | TP Mod: {state.tp_mod}x")
except Exception as e:
    print(f"❌ Lattice check failed: {e}")

# 3. Check Wallet Detection (Trade Everything Logic)
print("\n3. Checking Wallet Detection & Currency Support...")
print(f"   Tradeable Currencies: {bot.tradeable_currencies}")
if 'GBP' in bot.tradeable_currencies or 'USD' in bot.tradeable_currencies:
    print("✅ Wallet currency detected.")
else:
    print("⚠️  No major currency detected (might be expected if API key invalid or empty wallet).")

# 4. Check Ticker Fetching (Expanded Universe)
print("\n4. Fetching Tickers (Aggressive Filters)...")
try:
    count = bot.refresh_tickers()
    print(f"✅ Fetched {count} tickers.")
    
    # Check if we have some exotic pairs
    exotic_count = sum(1 for s in bot.ticker_cache if 'XBT' in s or 'ETH' in s)
    print(f"   Found {exotic_count} pairs involving XBT/ETH.")
except Exception as e:
    print(f"❌ Ticker fetch failed: {e}")

# 5. Check Opportunity Finding
print("\n5. Finding Opportunities...")
try:
    opps = bot.find_opportunities()
    print(f"✅ Found {len(opps)} opportunities.")
    if opps:
        top = opps[0]
        print(f"   Top Pick: {top['symbol']} (Score: {top['score']})")
except Exception as e:
    print(f"❌ Opportunity finding failed: {e}")

# 6. Test Sell Signal Logic (Force Refresh)
print("\n6. Testing Sell Signal Logic (Force Refresh)...")
try:
    # Mock a position
    test_symbol = "ETHGBP"
    bot.positions[test_symbol] = type('obj', (object,), {
        'symbol': test_symbol,
        'entry_price': 2000.0,
        'quantity': 1.0,
        'cycles': 9, # Will hit 10 next
        'entry_value': 2000.0,
        'entry_fee': 5.0,
        'dominant_node': 'Tiger'
    })
    
    # Mock ticker cache to simulate price change
    bot.ticker_cache[test_symbol] = {'price': 2100.0} # +5% gain
    
    print("   Running check_positions()...")
    # We capture stdout to verify the log message appears
    from io import StringIO
    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()
    
    bot.check_positions()
    
    sys.stdout = old_stdout
    output = mystdout.getvalue()
    print(output)
    
    if "Curr=2100.00" in output or "TP" in output or "CACHE" in output or "REST_FORCE" in output:
        print("✅ Position check logic executed successfully.")
    else:
        print("⚠️  Position check didn't produce expected output (might be due to mocking limitations).")
        
except Exception as e:
    print(f"❌ Sell signal test failed: {e}")

print("\n✨ Smoke Test Complete.")
