#!/usr/bin/env python3
"""
📊 AUREON STATUS CHECK 📊
Quick diagnostic to see system health and positions.
"""

from aureon.core.aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

def check_status():
    print()
    print("=" * 70)
    print("📊 AUREON SYSTEM STATUS CHECK 📊")
    print("=" * 70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check if trading process is running
    import subprocess
    ps_result = subprocess.run(
        ['pgrep', '-af', 'python.*aureon.*(unified|kraken)_ecosystem'],
        capture_output=True, text=True
    )
    
    if ps_result.returncode == 0 and ps_result.stdout.strip():
        print("🟢 TRADING SYSTEM: RUNNING")
        for line in ps_result.stdout.strip().split('\n'):
            print(f"   PID: {line.split()[0]}")
    else:
        print("🔴 TRADING SYSTEM: NOT RUNNING")
    
    # Check watchdog
    ps_watchdog = subprocess.run(
        ['pgrep', '-af', 'python.*aureon_watchdog'],
        capture_output=True, text=True
    )
    
    if ps_watchdog.returncode == 0 and ps_watchdog.stdout.strip():
        print("🟢 WATCHDOG: RUNNING")
    else:
        print("🟡 WATCHDOG: NOT RUNNING")
    
    print()
    
    # Check heartbeat
    hb_file = Path('.aureon_heartbeat')
    if hb_file.exists():
        hb_age = time.time() - hb_file.stat().st_mtime
        try:
            with open(hb_file) as f:
                hb = json.load(f)
            status = "🟢 FRESH" if hb_age < 60 else "🟡 STALE" if hb_age < 300 else "🔴 DEAD"
            print(f"💓 HEARTBEAT: {status} ({hb_age:.0f}s old)")
            print(f"   Iteration: {hb.get('iteration', '?')}")
            print(f"   Positions: {hb.get('positions', '?')}")
            print(f"   Equity: ${hb.get('equity', 0):.2f}")
        except:
            print(f"💓 HEARTBEAT: 🟡 Unreadable ({hb_age:.0f}s old)")
    else:
        print("💓 HEARTBEAT: 🔴 NO FILE")
    
    print()
    
    # Check state file
    state_file = Path('aureon_kraken_state.json')
    if state_file.exists():
        state_age = time.time() - state_file.stat().st_mtime
        status = "🟢 FRESH" if state_age < 60 else "🟡 STALE" if state_age < 300 else "🔴 DEAD"
        print(f"💾 STATE FILE: {status} ({state_age:.0f}s old)")
        
        try:
            with open(state_file) as f:
                state = json.load(f)
            
            positions = state.get('positions', {})
            balance = state.get('balance', 0)
            total_trades = state.get('total_trades', 0)
            wins = state.get('wins', 0)
            losses = state.get('losses', 0)
            wr = (wins / total_trades * 100) if total_trades > 0 else 0
            
            print(f"   Balance: ${balance:.2f}")
            print(f"   Trades: {total_trades} (W:{wins}/L:{losses}) WR: {wr:.1f}%")
            print(f"   Open Positions: {len(positions)}")
            
            if positions:
                print()
                print("   📈 POSITIONS:")
                
                # Try to get current prices
                try:
                    from aureon.exchanges.kraken_client import KrakenClient, get_kraken_client
                    client = get_kraken_client()
                    can_price = True
                except:
                    can_price = False
                
                total_value = 0
                total_pnl = 0
                
                for symbol, pos in positions.items():
                    entry_value = pos.get('entry_value', 0)
                    entry_price = pos.get('entry_price', 0)
                    qty = pos.get('quantity', 0)
                    
                    if can_price:
                        try:
                            ticker = client._ticker([symbol])
                            if ticker:
                                t_data = list(ticker.values())[0]
                                current_price = float(t_data.get('c', [0])[0])
                                current_value = qty * current_price
                                pnl = current_value - entry_value
                                pnl_pct = (pnl / entry_value * 100) if entry_value > 0 else 0
                                total_value += current_value
                                total_pnl += pnl
                                
                                icon = "🟢" if pnl > 0 else "🔴"
                                print(f"      {icon} {symbol:12s}: ${pnl:+.4f} ({pnl_pct:+.2f}%)")
                            else:
                                print(f"      ⚪ {symbol:12s}: ${entry_value:.2f} (no price)")
                        except:
                            print(f"      ⚪ {symbol:12s}: ${entry_value:.2f} (price error)")
                    else:
                        print(f"      ⚪ {symbol:12s}: Entry ${entry_value:.2f}")
                        total_value += entry_value
                
                print()
                print(f"   📊 TOTALS:")
                print(f"      Position Value: ${total_value:.2f}")
                print(f"      Unrealized P&L: ${total_pnl:+.4f}")
                
        except Exception as e:
            print(f"   ⚠️  Cannot read state: {e}")
    else:
        print("💾 STATE FILE: 🔴 NOT FOUND")
    
    print()
    print("=" * 70)
    print()


if __name__ == '__main__':
    check_status()
