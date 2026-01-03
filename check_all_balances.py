#!/usr/bin/env python3
"""
Quick check of all exchange balances
"""
from dotenv import load_dotenv
load_dotenv(override=True)

print('=' * 60)
print('💰 AUREON LIVE EXCHANGE BALANCES 💰')
print('=' * 60)
print()

total_usd = 0.0

# Test Binance
try:
    from binance_client import BinanceClient
    b = BinanceClient()
    usdt = b.get_free_balance('USDT')
    btc = b.get_free_balance('BTC')
    eth = b.get_free_balance('ETH')
    # Estimate USD value
    btc_price = 95000  # Approximate
    eth_price = 3400   # Approximate
    binance_usd = usdt + (btc * btc_price) + (eth * eth_price)
    total_usd += binance_usd
    print(f'🟡 BINANCE:')
    print(f'   USDT: ${usdt:.2f}')
    print(f'   BTC:  {btc:.8f} (~${btc * btc_price:.2f})')
    print(f'   ETH:  {eth:.8f} (~${eth * eth_price:.2f})')
    print(f'   Est. Total: ${binance_usd:.2f}')
except Exception as e:
    print(f'❌ BINANCE: {e}')

print()

# Test Kraken
try:
    from kraken_client import KrakenClient
    k = KrakenClient()
    bal = k.get_account_balance()
    print(f'🐙 KRAKEN:')
    kraken_usd = 0
    for asset, amount in bal.items():
        if float(amount) > 0.0001:
            print(f'   {asset}: {float(amount):.6f}')
            if asset in ['ZUSD', 'USD']:
                kraken_usd += float(amount)
    total_usd += kraken_usd
    print(f'   Est. USD: ${kraken_usd:.2f}')
except Exception as e:
    print(f'❌ KRAKEN: {e}')

print()

# Test Alpaca
try:
    from alpaca_client import AlpacaClient
    a = AlpacaClient()
    acc = a.get_account()
    equity = float(acc.get('equity', 0))
    cash = float(acc.get('cash', 0))
    total_usd += equity
    print(f'🦙 ALPACA:')
    print(f'   Equity: ${equity:.2f}')
    print(f'   Cash:   ${cash:.2f}')
    print(f'   Buying Power: ${float(acc.get("buying_power", 0)):.2f}')
except Exception as e:
    print(f'❌ ALPACA: {e}')

print()
print('=' * 60)
print(f'💎 TOTAL ESTIMATED VALUE: ${total_usd:.2f}')
print('=' * 60)
