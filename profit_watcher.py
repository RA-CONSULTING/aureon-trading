#!/usr/bin/env python3
"""
🎯 PROFIT WATCHER - Monitor position and sell at target
"""
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
os.chdir('/workspaces/aureon-trading')

from dotenv import load_dotenv
load_dotenv('/workspaces/aureon-trading/.env')

from kraken_client import KrakenClient, get_kraken_client
import time
import json

kraken = get_kraken_client()

# Load position
try:
    with open('active_sniper_position.json') as f:
        pos = json.load(f)
    SYMBOL = pos['symbol']
    ENTRY = pos['entry_price']
    QTY = pos['quantity']
except:
    SYMBOL = 'LMWRUSD'
    ENTRY = 0.0524
    QTY = 267.68642

TARGET = 2.0  # 2% profit target
STOP = -5.0  # 5% stop loss

print('=' * 50)
print('🎯 PROFIT WATCHER - LMWR POSITION')
print('=' * 50)
print(f'Symbol: {SYMBOL}')
print(f'Entry: ${ENTRY:.4f}')
print(f'Quantity: {QTY:.2f}')
print(f'Target: +{TARGET}%')
print(f'Stop: {STOP}%')
print('=' * 50)
print()

check_num = 0
while True:
    check_num += 1
    try:
        tickers = kraken.get_24h_tickers()
        for t in tickers:
            if t.get('symbol') == SYMBOL:
                price = float(t.get('lastPrice', 0))
                pnl = ((price - ENTRY) / ENTRY) * 100
                value = QTY * price
                
                print(f'[{check_num:3d}] ${price:.4f} | PnL: {pnl:+.2f}% | Value: ${value:.2f}', end='')
                
                if pnl >= TARGET:
                    print(' 🎯 TARGET HIT!')
                    print(f'\n🚀 SELLING {QTY:.2f} {SYMBOL}...')
                    result = kraken.place_market_order(SYMBOL, 'sell', quantity=QTY)
                    print(f'✅ SOLD: {result}')
                    
                    # Clear position file
                    os.remove('active_sniper_position.json')
                    print('\n💰 PROFIT TAKEN! Looking for next opportunity...')
                    sys.exit(0)
                    
                elif pnl <= STOP:
                    print(' ⚠️ STOP LOSS!')
                    print(f'\n🛑 CUTTING LOSS...')
                    result = kraken.place_market_order(SYMBOL, 'sell', quantity=QTY)
                    print(f'✅ SOLD: {result}')
                    os.remove('active_sniper_position.json')
                    sys.exit(1)
                else:
                    print()
                break
    except Exception as e:
        print(f'Error: {e}')
    
    time.sleep(5)  # Check every 5 seconds
