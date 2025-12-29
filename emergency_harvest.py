#!/usr/bin/env python3
"""
🚨 EMERGENCY HARVESTER 🚨
Run this to close all profitable positions that have been stuck open.

Usage: python3 emergency_harvest.py [--dry-run]
"""

import os
import sys
import json
import time
from datetime import datetime

def main():
    dry_run = '--dry-run' in sys.argv
    
    # Import dependencies
    try:
        from kraken_client import KrakenClient
        from penny_profit_engine import get_penny_engine, check_penny_exit
    except ImportError as e:
        print(f"❌ Import error: {e}")
        sys.exit(1)
    
    # Load state
    state_file = 'aureon_kraken_state.json'
    try:
        with open(state_file) as f:
            state = json.load(f)
    except Exception as e:
        print(f"❌ Cannot load state: {e}")
        sys.exit(1)
    
    client = KrakenClient()
    engine = get_penny_engine()
    
    print()
    print("=" * 70)
    print(f"🚨 EMERGENCY HARVESTER - {'DRY RUN' if dry_run else 'LIVE MODE'} 🚨")
    print("=" * 70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    positions = state.get('positions', {}).copy()
    sold = []
    failed = []
    total_gross = 0
    total_net = 0
    
    for symbol, pos in positions.items():
        entry_price = pos.get('entry_price', 0)
        entry_value = pos.get('entry_value', 0)
        entry_fee = pos.get('entry_fee', 0)
        qty = pos.get('quantity', 0)
        
        # Get current price
        try:
            ticker = client._ticker([symbol])
            if ticker:
                t_data = list(ticker.values())[0]
                current_price = float(t_data.get('c', [0])[0])
            else:
                print(f"⚠️  {symbol}: No ticker data")
                continue
        except Exception as e:
            print(f"⚠️  {symbol}: Price error - {e}")
            continue
        
        current_value = qty * current_price
        gross_pnl = current_value - entry_value
        pnl_pct = (gross_pnl / entry_value * 100) if entry_value > 0 else 0
        
        # Calculate net P&L
        fee_rate = 0.004 + 0.002 + 0.001  # fee + slippage + spread
        exit_fee = current_value * fee_rate
        net_pnl = gross_pnl - entry_fee - exit_fee
        
        # Check if profitable (gross > $0.05 or net > $0.03)
        threshold = engine.get_threshold('kraken', entry_value)
        action, _ = check_penny_exit('kraken', entry_value, current_value)
        
        should_sell = action == 'TAKE_PROFIT' or gross_pnl > 0.05 or net_pnl > 0.03
        
        if should_sell:
            icon = "✅" if net_pnl > 0 else "⚠️"
            print(f"{icon} {symbol:12s} | Gross: ${gross_pnl:+.4f} ({pnl_pct:+.2f}%) | Net: ${net_pnl:+.4f}")
            
            if not dry_run:
                try:
                    result = client.place_market_order(symbol, 'SELL', quantity=qty)
                    if result.get('orderId') or result.get('txid'):
                        sold.append(symbol)
                        total_gross += gross_pnl
                        total_net += net_pnl
                        del state['positions'][symbol]
                        print(f"   🎯 SOLD!")
                        time.sleep(0.5)  # Rate limit
                    else:
                        failed.append((symbol, str(result)))
                        print(f"   ❌ Failed: {result}")
                except Exception as e:
                    failed.append((symbol, str(e)))
                    print(f"   ❌ Error: {e}")
            else:
                sold.append(symbol)
                total_gross += gross_pnl
                total_net += net_pnl
        else:
            if pnl_pct < -5:
                print(f"❌ {symbol:12s} | Gross: ${gross_pnl:+.4f} ({pnl_pct:+.2f}%) | LOSS - HOLDING")
            else:
                print(f"⏳ {symbol:12s} | Gross: ${gross_pnl:+.4f} ({pnl_pct:+.2f}%) | WAITING")
    
    print()
    print("=" * 70)
    
    if sold:
        print(f"💰 {'WOULD SELL' if dry_run else 'SOLD'}: {len(sold)} positions")
        print(f"   Gross P&L: ${total_gross:+.4f}")
        print(f"   Net P&L:   ${total_net:+.4f}")
        
        if not dry_run:
            # Update state
            state['timestamp'] = time.time()
            state['balance'] = state.get('balance', 0) + total_net
            state['total_trades'] = state.get('total_trades', 0) + len(sold)
            state['wins'] = state.get('wins', 0) + len([s for s in sold])
            state['harvested'] = state.get('harvested', 0) + max(0, total_net)
            
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
            print(f"   Updated balance: ${state['balance']:.2f}")
    else:
        print("No profitable positions to close")
    
    if failed:
        print()
        print(f"❌ FAILED: {len(failed)} positions")
        for sym, err in failed:
            print(f"   {sym}: {err}")
    
    print("=" * 70)
    print()
    
    return len(sold), total_net


if __name__ == "__main__":
    main()
