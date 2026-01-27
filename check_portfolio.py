#!/usr/bin/env python3
"""Quick portfolio value check"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
from binance_client import BinanceClient
import os
from dotenv import load_dotenv

load_dotenv()

client = BinanceClient()
account = client.account()

total_usd = 0
print('\n💼 Current Portfolio:')
for balance in account['balances']:
    free = float(balance['free'])
    locked = float(balance['locked'])
    total = free + locked
    if total > 0.0001:
        try:
            ticker = client.best_price(f"{balance['asset']}USDT")
            usd_value = total * float(ticker['price'])
            total_usd += usd_value
            print(f"  {balance['asset']}: {total:.4f} (${usd_value:.2f})")
        except:
            print(f"  {balance['asset']}: {total:.4f}")

print(f'\n💰 Total Portfolio Value: ${total_usd:.2f}')
print(f'📊 Net P&L from $121.83 start: ${total_usd - 121.83:.2f}')
