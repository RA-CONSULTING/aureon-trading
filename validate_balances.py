#!/usr/bin/env python3
"""
Validate actual exchange balances to check if reported profit is real
"""
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
from binance_client import BinanceClient
from kraken_client import KrakenClient, get_kraken_client
from alpaca_client import AlpacaClient

print('=== REAL BALANCE VALIDATION ===')

# Binance
try:
    binance = BinanceClient()
    account = binance.account()
    usdt_balance = float([b for b in account["balances"] if b["asset"] == "USDT"][0]["free"])
    print(f'Binance USDT: ${usdt_balance:.2f}')
except Exception as e:
    print(f'Binance error: {e}')

# Kraken
try:
    kraken = get_kraken_client()
    balances = kraken.get_account_balance()
    usd_total = balances.get('USD', 0) + balances.get('ZUSD', 0) + balances.get('USDT', 0)
    print(f'Kraken USD: ${usd_total:.2f}')
except Exception as e:
    print(f'Kraken error: {e}')

# Alpaca
try:
    alpaca = AlpacaClient()
    account = alpaca.get_account()
    usd_balance = float(account.get('cash', 0))
    print(f'Alpaca USD: ${usd_balance:.2f}')
except Exception as e:
    print(f'Alpaca error: {e}')

print(f'Total Cash: ${usdt_balance + usd_total + usd_balance:.2f}')