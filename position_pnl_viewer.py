#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Position P&L Viewer - Shows all positions with entry prices and profit/loss

Usage:
    python position_pnl_viewer.py              # All exchanges
    python position_pnl_viewer.py --exchange kraken  # Specific exchange
    python position_pnl_viewer.py --csv        # Export to CSV
"""

import json
import sys
import os
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional
import argparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

@dataclass
class Position:
    """Position with cost basis info"""
    exchange: str
    symbol: str
    asset: str
    quote: str
    quantity: float
    avg_entry_price: float
    total_cost: float
    current_price: float
    current_value: float
    unrealized_pnl: float
    pnl_percent: float
    trade_count: int
    first_trade: Optional[datetime]
    last_trade: Optional[datetime]

def load_cost_basis() -> Dict:
    """Load cost basis history from JSON file"""
    try:
        with open('cost_basis_history.json') as f:
            data = json.load(f)
            return data.get('positions', {})
    except Exception as e:
        print(f"⚠️ Could not load cost_basis_history.json: {e}")
        return {}

def get_current_prices(positions: Dict) -> Dict[str, float]:
    """Get current prices for all positions"""
    prices = {}
    
    # Collect all symbols needed
    binance_symbols = set()
    kraken_symbols = set()
    
    for symbol, pos in positions.items():
        exchange = pos.get('exchange', 'unknown')
        if exchange == 'binance':
            binance_symbols.add(symbol)
        elif exchange == 'kraken':
            kraken_symbols.add(symbol)
    
    # Try Binance - get all tickers at once (public API)
    try:
        import requests
        response = requests.get('https://api.binance.com/api/v3/ticker/price', timeout=10)
        if response.status_code == 200:
            for ticker in response.json():
                symbol = ticker.get('symbol', '')
                price = float(ticker.get('price', 0))
                if price > 0:
                    prices[f"binance:{symbol}"] = price
                    prices[symbol] = price  # Also store without prefix
            print(f"   ✅ Binance: {len(prices)} prices loaded")
    except Exception as e:
        print(f"   ⚠️ Binance price fetch error: {e}")
    
    # Try Kraken - public ticker for multiple pairs
    try:
        if kraken_symbols:
            import requests
            # Get unique pairs 
            pairs = list(kraken_symbols)[:20]  # Limit to 20
            pair_str = ','.join(pairs)
            response = requests.get(f'https://api.kraken.com/0/public/Ticker?pair={pair_str}', timeout=10)
            if response.status_code == 200:
                result = response.json()
                if not result.get('error'):
                    for pair, data in result.get('result', {}).items():
                        if 'c' in data:  # 'c' is the last close price
                            price = float(data['c'][0])
                            prices[f"kraken:{pair}"] = price
                            prices[pair] = price
            print(f"   ✅ Kraken: {len(kraken_symbols)} prices requested")
    except Exception as e:
        print(f"   ⚠️ Kraken price fetch error: {e}")
    
    # Try Alpaca - positions come with current prices
    try:
        from alpaca_client import AlpacaClient
        alpaca = AlpacaClient()
        
        for pos in alpaca.get_positions():
            symbol = pos.get('symbol', '')
            current_price = float(pos.get('current_price', 0))
            if current_price > 0:
                prices[f"alpaca:{symbol}"] = current_price
                prices[symbol] = current_price
        print(f"   ✅ Alpaca: positions loaded")
    except Exception as e:
        print(f"   ⚠️ Alpaca price fetch error: {e}")
    
    return prices

def calculate_positions(filter_exchange: str = None) -> List[Position]:
    """Calculate all positions with P&L"""
    cost_basis = load_cost_basis()
    
    if not cost_basis:
        print("⚠️ No cost basis data found!")
        return []
    
    # Get current prices
    print("📡 Fetching current prices...")
    prices = get_current_prices(cost_basis)
    
    positions = []
    
    for symbol, data in cost_basis.items():
        exchange = data.get('exchange', 'unknown')
        
        # Filter by exchange if specified
        if filter_exchange and exchange.lower() != filter_exchange.lower():
            continue
        
        asset = data.get('asset', symbol[:3])
        quote = data.get('quote', 'USD')
        quantity = float(data.get('total_quantity', 0))
        avg_entry = float(data.get('avg_entry_price', 0))
        total_cost = float(data.get('total_cost', 0))
        trade_count = int(data.get('trade_count', 0))
        
        # Skip zero positions
        if quantity <= 0 or avg_entry <= 0:
            continue
        
        # Get current price
        price_key = f"{exchange}:{symbol}"
        current_price = prices.get(price_key, 0)
        
        # Also try without exchange prefix for Binance
        if current_price == 0:
            current_price = prices.get(f"binance:{symbol}", 0)
        
        # Calculate P&L
        current_value = quantity * current_price
        unrealized_pnl = current_value - total_cost
        pnl_percent = ((current_price / avg_entry) - 1) * 100 if avg_entry > 0 and current_price > 0 else 0
        
        # Parse timestamps
        first_ts = data.get('first_trade')
        last_ts = data.get('last_trade')
        first_trade = datetime.fromtimestamp(first_ts / 1000) if first_ts and first_ts > 1e12 else (
            datetime.fromtimestamp(first_ts) if first_ts else None
        )
        last_trade = datetime.fromtimestamp(last_ts / 1000) if last_ts and last_ts > 1e12 else (
            datetime.fromtimestamp(last_ts) if last_ts else None
        )
        
        positions.append(Position(
            exchange=exchange,
            symbol=symbol,
            asset=asset,
            quote=quote,
            quantity=quantity,
            avg_entry_price=avg_entry,
            total_cost=total_cost,
            current_price=current_price,
            current_value=current_value,
            unrealized_pnl=unrealized_pnl,
            pnl_percent=pnl_percent,
            trade_count=trade_count,
            first_trade=first_trade,
            last_trade=last_trade
        ))
    
    # Sort by exchange, then by P&L
    positions.sort(key=lambda p: (p.exchange, -p.unrealized_pnl))
    
    return positions

def print_positions(positions: List[Position], show_details: bool = False):
    """Print positions in a formatted table"""
    if not positions:
        print("📭 No positions found with cost basis data")
        return
    
    print("\n" + "="*100)
    print("   📊 POSITION P&L REPORT - ALL EXCHANGES")
    print("   " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*100)
    
    current_exchange = None
    exchange_totals = {}
    
    for pos in positions:
        # Print exchange header when it changes
        if pos.exchange != current_exchange:
            if current_exchange:
                print("-"*100)
                print(f"{'SUBTOTAL (' + current_exchange.upper() + '):':<50} ${exchange_totals.get(current_exchange, {}).get('cost', 0):>12.2f}  ${exchange_totals.get(current_exchange, {}).get('value', 0):>12.2f}  ${exchange_totals.get(current_exchange, {}).get('pnl', 0):>+12.2f}")
                print()
            
            current_exchange = pos.exchange
            exchange_emoji = {
                'binance': '🟡',
                'kraken': '🐙',
                'alpaca': '🦙',
                'capitalcom': '💼'
            }.get(pos.exchange.lower(), '📈')
            
            print(f"\n{exchange_emoji} {pos.exchange.upper()} POSITIONS:")
            print("-"*100)
            print(f"{'Symbol':<12} {'Asset':<6} {'Quantity':>14} {'Entry Price':>14} {'Current':>12} {'Cost':>12} {'Value':>12} {'P&L':>14}")
            print("-"*100)
        
        # Track exchange totals
        if pos.exchange not in exchange_totals:
            exchange_totals[pos.exchange] = {'cost': 0, 'value': 0, 'pnl': 0}
        exchange_totals[pos.exchange]['cost'] += pos.total_cost
        exchange_totals[pos.exchange]['value'] += pos.current_value
        exchange_totals[pos.exchange]['pnl'] += pos.unrealized_pnl
        
        # Color coding for P&L
        if pos.current_price > 0:
            pnl_str = f"${pos.unrealized_pnl:+.2f} ({pos.pnl_percent:+.1f}%)"
            current_str = f"${pos.current_price:.6f}" if pos.current_price < 1 else f"${pos.current_price:.2f}"
            value_str = f"${pos.current_value:.2f}"
        else:
            pnl_str = "N/A"
            current_str = "N/A"
            value_str = "N/A"
        
        entry_str = f"${pos.avg_entry_price:.6f}" if pos.avg_entry_price < 1 else f"${pos.avg_entry_price:.2f}"
        cost_str = f"${pos.total_cost:.2f}"
        qty_str = f"{pos.quantity:.4f}" if pos.quantity < 100 else f"{pos.quantity:.0f}"
        
        print(f"{pos.symbol:<12} {pos.asset:<6} {qty_str:>14} {entry_str:>14} {current_str:>12} {cost_str:>12} {value_str:>12} {pnl_str:>14}")
    
    # Print last exchange subtotal
    if current_exchange:
        print("-"*100)
        print(f"{'SUBTOTAL (' + current_exchange.upper() + '):':<50} ${exchange_totals.get(current_exchange, {}).get('cost', 0):>12.2f}  ${exchange_totals.get(current_exchange, {}).get('value', 0):>12.2f}  ${exchange_totals.get(current_exchange, {}).get('pnl', 0):>+12.2f}")
    
    # Grand totals
    total_cost = sum(e['cost'] for e in exchange_totals.values())
    total_value = sum(e['value'] for e in exchange_totals.values())
    total_pnl = sum(e['pnl'] for e in exchange_totals.values())
    total_pct = ((total_value / total_cost) - 1) * 100 if total_cost > 0 and total_value > 0 else 0
    
    print("\n" + "="*100)
    print(f"💰 GRAND TOTALS:")
    print(f"   Total Cost Basis:    ${total_cost:,.2f}")
    print(f"   Current Value:       ${total_value:,.2f}")
    print(f"   Unrealized P&L:      ${total_pnl:+,.2f} ({total_pct:+.1f}%)")
    print("="*100)
    
    # Summary by exchange
    print("\n📊 SUMMARY BY EXCHANGE:")
    print("-"*60)
    for exchange, totals in sorted(exchange_totals.items()):
        pct = ((totals['value'] / totals['cost']) - 1) * 100 if totals['cost'] > 0 and totals['value'] > 0 else 0
        emoji = {'binance': '🟡', 'kraken': '🐙', 'alpaca': '🦙'}.get(exchange.lower(), '📈')
        print(f"  {emoji} {exchange.upper():<10}: Cost ${totals['cost']:>10,.2f} | Value ${totals['value']:>10,.2f} | P&L ${totals['pnl']:>+10,.2f} ({pct:+.1f}%)")
    print("-"*60)

def export_csv(positions: List[Position], filename: str = None):
    """Export positions to CSV"""
    if not filename:
        filename = f"positions_pnl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    import csv
    
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Exchange', 'Symbol', 'Asset', 'Quote', 'Quantity', 
            'Entry Price', 'Total Cost', 'Current Price', 'Current Value',
            'Unrealized P&L', 'P&L %', 'Trade Count', 'First Trade', 'Last Trade'
        ])
        
        for pos in positions:
            writer.writerow([
                pos.exchange,
                pos.symbol,
                pos.asset,
                pos.quote,
                pos.quantity,
                pos.avg_entry_price,
                pos.total_cost,
                pos.current_price,
                pos.current_value,
                pos.unrealized_pnl,
                pos.pnl_percent,
                pos.trade_count,
                pos.first_trade.isoformat() if pos.first_trade else '',
                pos.last_trade.isoformat() if pos.last_trade else ''
            ])
    
    print(f"✅ Exported to {filename}")

def main():
    parser = argparse.ArgumentParser(description='View all positions with cost basis and P&L')
    parser.add_argument('--exchange', '-e', help='Filter by exchange (binance, kraken, alpaca)')
    parser.add_argument('--csv', action='store_true', help='Export to CSV')
    parser.add_argument('--details', '-d', action='store_true', help='Show extra details')
    args = parser.parse_args()
    
    positions = calculate_positions(filter_exchange=args.exchange)
    
    if args.csv:
        export_csv(positions)
    else:
        print_positions(positions, show_details=args.details)

if __name__ == '__main__':
    main()
