#!/usr/bin/env python3
"""
🔄 POSITION RECONCILIATION SYSTEM
═════════════════════════════════════════════════════════════════

Syncs tracked_positions.json with actual exchange balances and cost basis.
Corrects mismatches and remembers buy-in prices for all current assets.

Usage:
    python reconcile_positions.py
"""

import json
import os
import sys
from datetime import datetime

# UTF-8 wrapper for Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        if hasattr(sys.stderr, 'buffer'):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

def reconcile_positions():
    """Synchronize tracked positions with actual exchange balances."""
    
    print("\n🔄 POSITION RECONCILIATION STARTING...")
    print("=" * 60)
    
    # Load clients
    from alpaca_client import AlpacaClient
    from binance_client import BinanceClient
    from kraken_client import KrakenClient
    
    clients = {
        'alpaca': AlpacaClient(),
        'binance': BinanceClient(),
        'kraken': KrakenClient()
    }
    
    # Load tracked positions
    if not os.path.exists('tracked_positions.json'):
        tracked = {}
    else:
        with open('tracked_positions.json') as f:
            tracked = json.load(f)
    
    # Load cost basis
    if not os.path.exists('cost_basis_history.json'):
        cost_basis = {'positions': {}}
    else:
        with open('cost_basis_history.json') as f:
            cost_basis = json.load(f)
    
    cost_positions = cost_basis.get('positions', {})
    
    # Actual positions from exchanges
    actual = {
        'alpaca': {},
        'binance': {},
        'kraken': {}
    }
    
    # Fetch Alpaca positions
    try:
        positions = clients['alpaca'].get_positions()
        print(f"\n📊 ALPACA: Found {len(positions or [])} positions")
        for pos in (positions or []):
            symbol = pos.get('symbol', '')
            qty = float(pos.get('qty', 0) or 0)
            entry_price = float(pos.get('avg_entry_price', 0) or 0)
            
            if qty > 0:
                actual['alpaca'][symbol] = {
                    'quantity': qty,
                    'entry_price': entry_price,
                    'total_cost': qty * entry_price
                }
                print(f"   {symbol}: qty={qty}, entry_price=${entry_price:.8f}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Fetch Binance balances
    try:
        balances = clients['binance'].get_balance()
        print(f"\n📊 BINANCE: Checking {len(balances or {})} assets")
        count = 0
        for asset, qty in (balances or {}).items():
            qty = float(qty or 0)
            if qty > 0.00001:
                # Try to find cost basis for this asset
                cost_key = asset.upper()
                entry_price = 0
                if cost_key in cost_positions:
                    entry_price = cost_positions[cost_key].get('avg_entry_price', 0)
                
                actual['binance'][asset] = {
                    'quantity': qty,
                    'entry_price': entry_price,
                    'total_cost': qty * entry_price
                }
                print(f"   {asset}: qty={qty:.8f}, entry_price=${entry_price:.8f}")
                count += 1
        print(f"   (showing {count} non-dust assets)")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Fetch Kraken balances
    try:
        balances = clients['kraken'].get_balance()
        print(f"\n📊 KRAKEN: Checking {len(balances or {})} assets")
        count = 0
        for asset, qty in (balances or {}).items():
            qty = float(qty or 0)
            if qty > 0.00001:
                cost_key = asset.upper()
                entry_price = 0
                if cost_key in cost_positions:
                    entry_price = cost_positions[cost_key].get('avg_entry_price', 0)
                
                actual['kraken'][asset] = {
                    'quantity': qty,
                    'entry_price': entry_price,
                    'total_cost': qty * entry_price
                }
                count += 1
        print(f"   (showing {count} non-dust assets)")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Now reconcile
    print("\n" + "=" * 60)
    print("🔄 RECONCILIATION RESULTS")
    print("=" * 60)
    
    updates = 0
    removals = 0
    
    # Check tracked positions against actual
    tracked_copy = dict(tracked)
    for symbol, track_data in tracked_copy.items():
        exchange = track_data.get('exchange', 'unknown')
        tracked_qty = float(track_data.get('entry_qty', 0) or 0)
        
        # Get actual position
        actual_pos = actual.get(exchange, {}).get(symbol.replace('/', '').upper(), {})
        actual_qty = actual_pos.get('quantity', 0)
        actual_price = actual_pos.get('entry_price', 0)
        
        if tracked_qty > 0 and actual_qty <= 0:
            # Position was tracked but no longer exists - remove it
            print(f"🗑️  REMOVE: {exchange:8} | {symbol:15} | tracked={tracked_qty:12.8f} → actual=0")
            del tracked[symbol]
            removals += 1
        elif actual_qty > 0:
            # Position exists on exchange - update if quantities differ
            if abs(tracked_qty - actual_qty) > 0.000001:
                print(f"✏️  UPDATE: {exchange:8} | {symbol:15} | qty {tracked_qty:12.8f} → {actual_qty:12.8f}")
                tracked[symbol]['entry_qty'] = actual_qty
                tracked[symbol]['entry_price'] = actual_price
                tracked[symbol]['entry_cost'] = actual_qty * actual_price
                tracked[symbol]['entry_time'] = datetime.now().isoformat()
                tracked[symbol]['reconciled'] = True
                updates += 1
                
                # Also update cost basis
                cost_key = symbol.replace('/', '').upper()
                if cost_key not in cost_positions:
                    cost_positions[cost_key] = {
                        'exchange': exchange,
                        'avg_entry_price': actual_price,
                        'total_quantity': actual_qty,
                        'total_cost': actual_qty * actual_price,
                        'total_fees': 0,
                        'trade_count': 1,
                        'last_trade': datetime.now().isoformat()
                    }
    
    # Check for untracked actual positions
    print("\n🆕 NEWLY DISCOVERED POSITIONS:")
    new_tracked = 0
    for exchange, assets in actual.items():
        for symbol, pos_data in assets.items():
            # Check if tracked
            found = any(
                tracked.get(sym, {}).get('exchange') == exchange and
                sym.replace('/', '').upper() == symbol.upper()
                for sym in tracked
            )
            
            if not found and pos_data['quantity'] > 0.000001:
                print(f"➕ AUTO-TRACK: {exchange:8} | {symbol:15} | qty={pos_data['quantity']:12.8f} @ ${pos_data['entry_price']:.8f}")
                tracked[symbol] = {
                    'exchange': exchange,
                    'entry_price': pos_data['entry_price'],
                    'entry_qty': pos_data['quantity'],
                    'entry_cost': pos_data['total_cost'],
                    'entry_time': datetime.now().isoformat(),
                    'auto_discovered': True,
                    'reconciled': True
                }
                new_tracked += 1
                
                # Update cost basis
                cost_key = symbol.upper()
                if cost_key not in cost_positions:
                    cost_positions[cost_key] = {
                        'exchange': exchange,
                        'avg_entry_price': pos_data['entry_price'],
                        'total_quantity': pos_data['quantity'],
                        'total_cost': pos_data['total_cost'],
                        'total_fees': 0,
                        'trade_count': 1,
                        'last_trade': datetime.now().isoformat(),
                        'auto_discovered': True
                    }
    
    # Save updated files
    print("\n" + "=" * 60)
    print("💾 SAVING RECONCILED DATA")
    print("=" * 60)
    
    with open('tracked_positions.json', 'w') as f:
        json.dump(tracked, f, indent=2)
    print(f"✅ Updated tracked_positions.json ({len(tracked)} total positions)")
    
    cost_basis['positions'] = cost_positions
    cost_basis['last_sync'] = datetime.now().isoformat()
    with open('cost_basis_history.json', 'w') as f:
        json.dump(cost_basis, f, indent=2)
    print(f"✅ Updated cost_basis_history.json ({len(cost_positions)} positions with cost data)")
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"✏️  Updated: {updates} positions")
    print(f"🗑️  Removed: {removals} stale positions")
    print(f"➕ New tracked: {new_tracked} positions")
    print(f"📦 Final total: {len(tracked)} tracked positions")
    print(f"💰 Cost basis records: {len(cost_positions)}")
    print("\n✅ RECONCILIATION COMPLETE!")

if __name__ == '__main__':
    try:
        reconcile_positions()
    except Exception as e:
        print(f"\n❌ RECONCILIATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
