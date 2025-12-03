#!/usr/bin/env python3
"""
Verify that the unified ecosystem is pulling from both Kraken and Binance
"""
import sys
sys.path.insert(0, '/workspaces/aureon-trading')

from unified_exchange_client import MultiExchangeClient

print("🔍 Verifying dual exchange connectivity...\n")

# Initialize multi-exchange client
client = MultiExchangeClient()

# 1. Check balances from both exchanges
print("=" * 70)
print("📊 CHECKING BALANCES FROM BOTH EXCHANGES")
print("=" * 70)

try:
    all_balances = client.get_all_balances()
    
    for exchange, balances in all_balances.items():
        print(f"\n🏦 {exchange.upper()}:")
        if balances:
            for asset, amount in list(balances.items())[:10]:  # Show first 10
                try:
                    val = float(amount)
                    if val > 0:
                        print(f"   ✓ {asset}: {val:.8f}")
                except:
                    pass
            if len(balances) > 10:
                print(f"   ... and {len(balances) - 10} more assets")
        else:
            print("   (No balances)")
            
except Exception as e:
    print(f"   ❌ Error: {e}")

# 2. Check tickers from both exchanges
print("\n" + "=" * 70)
print("📈 CHECKING TICKERS FROM BOTH EXCHANGES")
print("=" * 70)

try:
    tickers = client.get_24h_tickers()
    
    kraken_tickers = [t for t in tickers if t.get('source') == 'kraken']
    binance_tickers = [t for t in tickers if t.get('source') == 'binance']
    
    print(f"\n✅ Kraken: {len(kraken_tickers)} tickers")
    if kraken_tickers:
        for t in kraken_tickers[:5]:
            print(f"   - {t.get('symbol')}: {t.get('lastPrice', 'N/A')}")
        if len(kraken_tickers) > 5:
            print(f"   ... and {len(kraken_tickers) - 5} more")
    
    print(f"\n✅ Binance: {len(binance_tickers)} tickers")
    if binance_tickers:
        for t in binance_tickers[:5]:
            print(f"   - {t.get('symbol')}: {t.get('lastPrice', 'N/A')}")
        if len(binance_tickers) > 5:
            print(f"   ... and {len(binance_tickers) - 5} more")
            
except Exception as e:
    print(f"   ❌ Error: {e}")

# 3. Test conversion across exchanges
print("\n" + "=" * 70)
print("💱 TESTING PRICE CONVERSION")
print("=" * 70)

try:
    val_kraken = client.convert_to_quote('kraken', 'BTC', 1.0, 'GBP')
    val_binance = client.convert_to_quote('binance', 'BTC', 1.0, 'USDT')
    
    print(f"   Kraken BTC → GBP: £{val_kraken:.2f}")
    print(f"   Binance BTC → USDT: {val_binance:.2f}")
    
except Exception as e:
    print(f"   ⚠️ Conversion error (may be expected): {e}")

print("\n" + "=" * 70)
print("✅ DUAL EXCHANGE VERIFICATION COMPLETE")
print("=" * 70)
