#!/usr/bin/env python3
"""
🔍 KRAKEN API DIAGNOSTICS - Check if your Kraken setup is ready for real trading
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
from kraken_client import KrakenClient
import os

print('🔍 KRAKEN API DIAGNOSTICS')
print('=' * 40)

# Check environment variables
print('📋 Environment Variables:')
print(f'  KRAKEN_API_KEY: {"SET" if os.getenv("KRAKEN_API_KEY") else "NOT SET"}')
print(f'  KRAKEN_API_SECRET: {"SET" if os.getenv("KRAKEN_API_SECRET") else "NOT SET"}')
print(f'  KRAKEN_DRY_RUN: {os.getenv("KRAKEN_DRY_RUN", "false")}')
print()

client = KrakenClient()
print('🔗 Client Configuration:')
print(f'  Dry Run: {client.dry_run}')
print(f'  API Key Set: {bool(client.api_key)}')
print(f'  API Secret Set: {bool(client.api_secret)}')
print()

# Test public API first
print('🌐 Testing Public API (no auth required):')
try:
    ticker = client.get_ticker('BTCUSD')
    print(f'  ✅ BTCUSD Ticker: ${ticker.get("price", "N/A")}')
except Exception as e:
    print(f'  ❌ Public API Failed: {str(e)[:50]}')
print()

# Test private API
print('🔐 Testing Private API (requires valid keys):')
try:
    balance = client.get_balance()
    if balance:
        total_usd = 0
        for asset, amount in balance.items():
            if asset in ['USD', 'USDC', 'USDT']:
                total_usd += amount
            print(f'  💰 {asset}: {amount}')
        print(f'  💵 Total USD Value: ${total_usd:.2f}')
    else:
        print('  ❌ Empty balance - API keys may be invalid or account has no funds')
except Exception as e:
    print(f'  ❌ Private API Failed: {str(e)[:100]}')
    if 'Missing KRAKEN_API_KEY' in str(e):
        print('    → API keys not set in environment')
    elif 'invalid' in str(e).lower():
        print('    → API keys are invalid or expired')
    elif 'permission' in str(e).lower():
        print('    → API keys lack required permissions')
print()

print('📝 RECOMMENDATIONS:')
if not client.api_key or not client.api_secret:
    print('  1. Set KRAKEN_API_KEY and KRAKEN_API_SECRET in your .env file')
    print('  2. Or set them as environment variables')
elif not balance:
    print('  1. Verify API keys are correct on Kraken.com')
    print('  2. Ensure keys have Query Funds permission')
    print('  3. Deposit funds to your Kraken account')
    print('  4. For testing, add KRAKEN_DRY_RUN=true to .env')
else:
    print('  ✅ Kraken is ready for real trading!')