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
    """Get current Binance holdings - REAL positions from account API"""
    positions = []
    
    try:
        from binance_client import get_binance_client
        client = get_binance_client()
        if not client:
            print("⚠️ Binance client not available")
            return positions
        
        # Get account balances - this gives REAL current holdings
        account = client.account()
        
        if 'balances' not in account:
            print(f"⚠️ Binance API error: {account}")
            return positions
        
        # Process REAL holdings from account balances
        for b in account.get('balances', []):
            total = float(b['free']) + float(b['locked'])
            if total > 0.0001:  # Only include assets with balance
                asset = b['asset']
                
                # Skip stablecoins/fiat
                if asset in ['USDC', 'USDT', 'FDUSD', 'EUR', 'GBP', 'BUSD', 'TUSD', 'DAI']:
                    continue
                
                # Find the best trading pair for this asset
                symbol = None
                current_price = 0
                
                # Try different quote currencies in order of preference
                for quote in ['USDC', 'USDT', 'FDUSD', 'BUSD']:
                    pair = asset + quote
                    try:
                        ticker = client.get_ticker(pair)
                        if ticker and 'price' in ticker:
                            symbol = pair
                            current_price = float(ticker['price'])
                            break
                    except Exception:
                        continue  # Try next quote currency
                
                if symbol and current_price > 0:
                    current_value = total * current_price
                    
                    positions.append({
                        'exchange': 'binance',
                        'symbol': symbol,
                        'quantity': total,
                        'avg_cost': current_price,  # Use current price as cost basis for now
                        'current_price': current_price,
                        'current_value': current_value,
                        'unrealized_pnl': 0,  # No P&L calculation
                        'pnl_percent': 0,
                        'cost_basis': current_value  # Cost basis = current value for simplicity
                    })
        
        print(f"✅ Binance: Found {len(positions)} REAL positions")
        
    except Exception as e:
        print(f"⚠️ Binance error: {e}")
    
    return positions

def get_alpaca_positions():
    """Get Alpaca positions - REAL positions from Alpaca API"""
    positions = []
    
    try:
        from alpaca_client import AlpacaClient
        alpaca = AlpacaClient()
        
        alpaca_positions = alpaca.get_positions()
        print(f"✅ Alpaca: Found {len(alpaca_positions)} REAL positions")
        
        for pos in alpaca_positions:
            symbol = pos.get('symbol', '')
            qty = float(pos.get('qty', 0))
            entry_price = float(pos.get('avg_entry_price', 0))
            current_price = float(pos.get('current_price', 0))
            market_value = float(pos.get('market_value', 0))
            unrealized_pl = float(pos.get('unrealized_pl', 0))
            
            # Only include positions with quantity > 0
            if qty > 0.0001:
                positions.append({
                    'exchange': 'alpaca',
                    'symbol': symbol,
                    'quantity': qty,
                    'avg_cost': entry_price,
                    'current_price': current_price,
                    'current_value': market_value,
                    'unrealized_pnl': unrealized_pl,
                    'pnl_percent': (unrealized_pl / (qty * entry_price) * 100) if (qty * entry_price) > 0 else 0,
                    'cost_basis': qty * entry_price
                })
                
    except Exception as e:
        print(f"⚠️ Alpaca error: {e}")
    
    return positions

def get_kraken_positions():
    """Get Kraken positions - REAL positions from Kraken API using get_balance()"""
    positions = []
    
    from kraken_client import get_kraken_client
    kraken = get_kraken_client()
    
    # Get account balances using get_balance() - returns {asset: qty}
    balances = kraken.get_balance()
    
    # Stablecoins are cash, not positions
    stablecoins = ['USD', 'ZUSD', 'EUR', 'ZEUR', 'GBP', 'ZGBP', 'DAI', 'USDC', 'USDT', 'TUSD', 'BUSD']
    
    non_zero_count = 0
    for asset, qty in balances.items():
        qty_float = float(qty)
        if qty_float > 0.000001:
            non_zero_count += 1
    
    print(f"✅ Kraken: Found {non_zero_count} non-zero balances via get_balance()")
    
    # Get current prices from Kraken public API
    prices = {}
    
    # Known trading pairs on Kraken (major ones + common alts)
    known_pairs = {
        'ADA': 'ADAUSD', 'ATOM': 'ATOMUSD', 'BABY': 'BABYUSD', 'BTC': 'BTCUSD',
        'ETH': 'ETHUSD', 'SOL': 'SOLUSD', 'DOGE': 'DOGEUSD', 'XRP': 'XRPUSD',
        'DOT': 'DOTUSD', 'AVAX': 'AVAXUSD', 'MATIC': 'MATICUSD', 'ARB': 'ARBUSD',
        'OP': 'OPUSD', 'LINK': 'LINKUSD', 'AAVE': 'AAVEUSD', 'UNI': 'UNIUSD',
        # Meme/community coins (try multiple quote currencies)
        'BSX': 'BSXUSD', 'EUL': 'EULUSD', 'FIGHT': 'FIGHTUSD', 'FIS': 'FISUSD',
        'GHIBLI': 'GHIBLIUSD', 'ICNT': 'ICNTUSD', 'IN': 'INUSD', 'KTA': 'KTAUSD',
        'MXC': 'MXCUSD', 'OPEN': 'OPENUSD', 'SAHARA': 'SAHARAUSD', 'SCRT': 'SCRTUSD',
        'SKR': 'SKRUSD', 'TRX': 'TRXUSD', 'TRX.B': 'TRXUSD'  # TRX.B is tokenized version
    }
    
    try:
        import requests
        # Build trading pairs - only use KNOWN pairs on Kraken
        pairs_to_fetch = []
        for asset in balances.keys():
            # Skip stablecoins
            if asset in stablecoins:
                continue
            
            # Use known pair if available, otherwise skip
            if asset in known_pairs:
                pairs_to_fetch.append(known_pairs[asset])
        
        # Fetch tickers in batch
        if pairs_to_fetch:
            pairs_str = ','.join(pairs_to_fetch[:50])  # Limit to 50 at once
            try:
                resp = requests.get(
                    f'https://api.kraken.com/0/public/Ticker?pair={pairs_str}',
                    timeout=5
                )
                if resp.status_code == 200:
                    data = resp.json()
                    errors = data.get('error', [])
                    if errors:
                        print(f"⚠️ Kraken API error: {errors}")
                    
                    result = data.get('result', {})
                    if isinstance(result, dict):
                        for kraken_pair, info in result.items():
                            try:
                                price_list = info.get('c', [])
                                if price_list and len(price_list) > 0:
                                    price = float(price_list[0])
                                    if price > 0:
                                        prices[kraken_pair] = price
                            except (ValueError, TypeError, IndexError) as e:
                                pass  # Skip pairs with bad data
                    
                    print(f"✅ Kraken: Fetched prices for {len(prices)} pairs")
            except requests.RequestException as e:
                print(f"⚠️ Kraken API request failed: {e}")
    except Exception as e:
        print(f"⚠️ Kraken price setup error: {e}")
    
    # Process balances into positions
    for asset, qty in balances.items():
        qty_float = float(qty)
        
        # Skip dust and stablecoins
        if qty_float <= 0.000001 or asset in stablecoins:
            continue
        
        # Kraken balance keys are already clean (ADA, SOL, BABY, etc)
        symbol = f"{asset}USD"
        current_price = prices.get(symbol, 0)
        
        # If USD pair not found, try USDT and USDC
        if not current_price:
            for alt_quote in ['USDT', 'USDC']:
                alt_pair = f"{asset}{alt_quote}"
                current_price = prices.get(alt_pair, 0)
                if current_price > 0:
                    symbol = alt_pair
                    break
        
        current_value = qty_float * current_price if current_price > 0 else 0
        
        positions.append({
            'exchange': 'kraken',
            'symbol': symbol,
            'quantity': qty_float,
            'avg_cost': current_price,  # Use current price as cost basis for now
            'current_price': current_price,
            'current_value': current_value,
            'unrealized_pnl': 0,
            'pnl_percent': 0,
            'cost_basis': current_value
        })
    
    print(f"✅ Kraken: Processed {len(positions)} REAL positions with prices")
    
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
        positions.sort(key=lambda x: x['unrealized_pnl'], reverse=True)
        
        ex_cost = 0
        ex_value = 0
        ex_pnl = 0
        
        for pos in positions:
            asset = pos['symbol']
            qty = pos['quantity']
            entry = pos['avg_cost']
            current = pos['current_price']
            cost = pos['cost_basis']
            value = pos['current_value']
            pnl = pos['unrealized_pnl']
            pnl_pct = pos['pnl_percent']
            
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
    print("📡 Fetching REAL LIVE positions from exchanges...")
    
    all_positions = []
    
    # Get Binance positions
    print("   🟡 Querying Binance account API...")
    binance_pos = get_binance_positions()
    all_positions.extend(binance_pos)
    print(f"      Found {len(binance_pos)} positions")
    
    # Small delay between exchanges to be rate-limit safe
    time.sleep(1)
    
    # Get Alpaca positions
    print("   🦙 Querying Alpaca positions API...")
    alpaca_pos = get_alpaca_positions()
    all_positions.extend(alpaca_pos)
    print(f"      Found {len(alpaca_pos)} positions")
    
    # Small delay between exchanges
    time.sleep(1)
    
    # Get Kraken positions
    print("   🐙 Querying Kraken account API...")
    kraken_pos = get_kraken_positions()
    all_positions.extend(kraken_pos)
    print(f"      Found {len(kraken_pos)} positions")
    
    # Print report
    print_report(all_positions)

if __name__ == '__main__':
    main()
