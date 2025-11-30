#!/usr/bin/env python3
"""Count assets with balance"""

from binance_client import BinanceClient

client = BinanceClient()
account = client.account()

assets = [b for b in account['balances'] if float(b['free']) + float(b['locked']) > 0]
print(f"Total assets with balance: {len(assets)}")
print("\nAll holdings:")
for b in assets:
    total = float(b['free']) + float(b['locked'])
    print(f"  {b['asset']}: {total:.8f}")
