#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LIVE Position Viewer - Shows REAL positions with REAL cost basis from trade history

This queries actual exchange APIs to get:
1. Current holdings
2. Trade history to calculate TRUE cost basis
3. Current prices to calculate P&L

Usage:
    python live_position_viewer.py
"""

import os
import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode
from datetime import datetime

# Load credentials from .env
def load_env():
    creds = {}
    try:
        with open('.env') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    creds[key] = value
    except:
        pass
    return creds

creds = load_env()

# Binance API helpers
BINANCE_KEY = os.getenv("BINANCE_API_KEY") or creds.get("BINANCE_API_KEY", "")
BINANCE_SECRET = os.getenv("BINANCE_API_SECRET") or creds.get("BINANCE_API_SECRET", "")

def binance_sign(params):
    query = urlencode(params)
    signature = hmac.new(BINANCE_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    return query + '&signature=' + signature

def get_binance_positions():
    """Get current Binance holdings with cost basis from trade history"""
    positions = []
    
    # Get account balances
    params = {'timestamp': int(time.time() * 1000)}
    response = requests.get(
        'https://api.binance.com/api/v3/account?' + binance_sign(params),
        headers={'X-MBX-APIKEY': BINANCE_KEY},
        timeout=10
    )
    account = response.json()
    
    # Get all current prices at once
    prices_response = requests.get('https://api.binance.com/api/v3/ticker/price', timeout=10)
    prices = {p['symbol']: float(p['price']) for p in prices_response.json()}
    
    # Get holdings
    holdings = {}
    for b in account.get('balances', []):
        total = float(b['free']) + float(b['locked'])
        if total > 0.0001:
            holdings[b['asset']] = total
    
    # For each holding, get trade history to calculate cost basis
    for asset, qty in holdings.items():
        if asset in ['USDC', 'USDT', 'FDUSD', 'EUR', 'GBP', 'BUSD']:
            continue
        
        # Try USDC pair first, then USDT
        for quote in ['USDC', 'USDT']:
            symbol = asset + quote
            params = {
                'symbol': symbol,
                'timestamp': int(time.time() * 1000),
                'limit': 500
            }
            
            try:
                response = requests.get(
                    'https://api.binance.com/api/v3/myTrades?' + binance_sign(params),
                    headers={'X-MBX-APIKEY': BINANCE_KEY},
                    timeout=10
                )
                trades = response.json()
                
                if isinstance(trades, list) and len(trades) > 0:
                    # Calculate cost basis (only BUY trades)
                    total_bought_qty = 0
                    total_bought_cost = 0
                    
                    for t in trades:
                        trade_qty = float(t['qty'])
                        trade_price = float(t['price'])
                        
                        if t.get('isBuyer'):
                            total_bought_qty += trade_qty
                            total_bought_cost += trade_qty * trade_price
                    
                    if total_bought_qty > 0:
                        avg_entry = total_bought_cost / total_bought_qty
                        current_price = prices.get(symbol, 0)
                        current_value = qty * current_price
                        cost_basis = qty * avg_entry  # Cost for CURRENT holding
                        pnl = current_value - cost_basis
                        pnl_pct = ((current_price / avg_entry) - 1) * 100 if avg_entry > 0 else 0
                        
                        positions.append({
                            'exchange': 'Binance',
                            'symbol': symbol,
                            'asset': asset,
                            'quantity': qty,
                            'avg_entry': avg_entry,
                            'cost_basis': cost_basis,
                            'current_price': current_price,
                            'current_value': current_value,
                            'pnl': pnl,
                            'pnl_pct': pnl_pct,
                            'trades': len(trades)
                        })
                        break  # Found trades, don't check other quote
            except Exception as e:
                pass
    
    return positions

def get_alpaca_positions():
    """Get Alpaca positions (already includes entry price)"""
    positions = []
    
    try:
        from alpaca_client import AlpacaClient
        alpaca = AlpacaClient()
        
        for pos in alpaca.get_positions():
            symbol = pos.get('symbol', '')
            qty = float(pos.get('qty', 0))
            entry = float(pos.get('avg_entry_price', 0))
            current = float(pos.get('current_price', 0))
            pnl = float(pos.get('unrealized_pl', 0))
            cost_basis = qty * entry
            pnl_pct = ((current / entry) - 1) * 100 if entry > 0 else 0
            
            positions.append({
                'exchange': 'Alpaca',
                'symbol': symbol,
                'asset': symbol.replace('USD', ''),
                'quantity': qty,
                'avg_entry': entry,
                'cost_basis': cost_basis,
                'current_price': current,
                'current_value': qty * current,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'trades': 0
            })
    except Exception as e:
        print(f"⚠️ Alpaca error: {e}")
    
    return positions

def get_kraken_positions():
    """Get Kraken positions with cost basis"""
    positions = []
    
    # Try to get from Kraken - but they need trade history too
    # For now, skip as nonce issues persist
    
    return positions

def print_report(all_positions):
    """Print formatted report"""
    
    print("\n" + "="*90)
    print("   📊 LIVE POSITION P&L REPORT")
    print("   " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*90)
    
    # Group by exchange
    by_exchange = {}
    for pos in all_positions:
        ex = pos['exchange']
        if ex not in by_exchange:
            by_exchange[ex] = []
        by_exchange[ex].append(pos)
    
    grand_cost = 0
    grand_value = 0
    grand_pnl = 0
    
    for exchange, positions in sorted(by_exchange.items()):
        emoji = {'Binance': '🟡', 'Alpaca': '🦙', 'Kraken': '🐙'}.get(exchange, '📈')
        
        print(f"\n{emoji} {exchange.upper()} POSITIONS:")
        print("-"*90)
        print(f"{'Asset':<10} {'Quantity':>14} {'Entry':>12} {'Current':>12} {'Cost':>12} {'Value':>12} {'P&L':>16}")
        print("-"*90)
        
        # Sort by P&L descending
        positions.sort(key=lambda x: x['pnl'], reverse=True)
        
        ex_cost = 0
        ex_value = 0
        ex_pnl = 0
        
        for pos in positions:
            asset = pos['asset']
            qty = pos['quantity']
            entry = pos['avg_entry']
            current = pos['current_price']
            cost = pos['cost_basis']
            value = pos['current_value']
            pnl = pos['pnl']
            pnl_pct = pos['pnl_pct']
            
            ex_cost += cost
            ex_value += value
            ex_pnl += pnl
            
            # Format numbers
            qty_str = f"{qty:,.4f}" if qty < 1000 else f"{qty:,.0f}"
            entry_str = f"${entry:.6f}" if entry < 1 else f"${entry:.2f}"
            current_str = f"${current:.6f}" if current < 1 else f"${current:.2f}"
            cost_str = f"${cost:.2f}"
            value_str = f"${value:.2f}"
            pnl_str = f"${pnl:+.2f} ({pnl_pct:+.1f}%)"
            
            print(f"{asset:<10} {qty_str:>14} {entry_str:>12} {current_str:>12} {cost_str:>12} {value_str:>12} {pnl_str:>16}")
        
        print("-"*90)
        ex_pnl_pct = ((ex_value / ex_cost) - 1) * 100 if ex_cost > 0 else 0
        print(f"{'SUBTOTAL':<10} {'':<14} {'':<12} {'':<12} ${ex_cost:>10.2f} ${ex_value:>10.2f} ${ex_pnl:>+10.2f} ({ex_pnl_pct:+.1f}%)")
        
        grand_cost += ex_cost
        grand_value += ex_value
        grand_pnl += ex_pnl
    
    # Grand totals
    print("\n" + "="*90)
    grand_pnl_pct = ((grand_value / grand_cost) - 1) * 100 if grand_cost > 0 else 0
    print(f"💰 GRAND TOTALS:")
    print(f"   Total Cost Basis:    ${grand_cost:,.2f}")
    print(f"   Current Value:       ${grand_value:,.2f}")
    print(f"   Unrealized P&L:      ${grand_pnl:+,.2f} ({grand_pnl_pct:+.1f}%)")
    print("="*90)

def main():
    print("📡 Fetching LIVE positions from exchanges...")
    
    all_positions = []
    
    # Get Binance positions
    print("   🟡 Querying Binance trade history...")
    binance_pos = get_binance_positions()
    all_positions.extend(binance_pos)
    print(f"      Found {len(binance_pos)} positions")
    
    # Get Alpaca positions
    print("   🦙 Querying Alpaca positions...")
    alpaca_pos = get_alpaca_positions()
    all_positions.extend(alpaca_pos)
    print(f"      Found {len(alpaca_pos)} positions")
    
    # Print report
    print_report(all_positions)

if __name__ == '__main__':
    main()
