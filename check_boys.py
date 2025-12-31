#!/usr/bin/env python3
"""
🇮🇪 CHECK THE BOYS - Quick status of scouts and sniper 🇮🇪

Usage: python3 check_boys.py
"""

import json
import subprocess
import sys
from datetime import datetime

def main():
    try:
        from unified_exchange_client import MultiExchangeClient
        client = MultiExchangeClient()
    except ImportError as e:
        print(f"❌ Import error: {e}")
        sys.exit(1)

    print()
    print('=' * 60)
    print('🇮🇪 THE BOYS - LIVE BATTLEFIELD STATUS 🇮🇪')
    print('=' * 60)
    print(f'Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print()

    # Check if auto_sniper is running
    result = subprocess.run(['pgrep', '-f', 'auto_sniper.py'], capture_output=True, text=True)
    pids = result.stdout.strip().split('\n') if result.stdout.strip() else []
    if pids and pids[0]:
        print(f'🎯 AUTO SNIPER: ✅ RUNNING (PID: {pids[0]})')
    else:
        print('🎯 AUTO SNIPER: ❌ NOT RUNNING')
        print('   Start with: nohup python3 auto_sniper.py > auto_sniper.log 2>&1 &')

    print()

    # Load state
    try:
        with open('aureon_kraken_state.json') as f:
            state = json.load(f)
    except Exception as e:
        print(f"❌ Cannot load state: {e}")
        return

    positions = state.get('positions', {})
    
    # Cash check
    print('💰 AMMUNITION:')
    try:
        all_bal = client.get_all_balances()
        for ex in ['kraken', 'alpaca', 'binance']:
            bal = all_bal.get(ex, {})
            for asset in ['ZUSD', 'USD', 'USDC', 'USDT', 'LDUSDC']:
                data = bal.get(asset, {})
                if isinstance(data, dict):
                    free = float(data.get('free', 0) or 0)
                else:
                    free = float(data or 0)
                if free > 0.1:
                    print(f'   {ex.upper():8s} {asset:8s}: ${free:.2f}')
    except Exception as e:
        print(f'   ⚠️ Balance error: {e}')

    print()
    print(f'⚔️  ACTIVE POSITIONS: {len(positions)}')
    print('-' * 60)

    kills_ready = []
    waiting = []
    holding = []

    for sym, pos in positions.items():
        ex = pos.get('exchange', 'kraken')
        entry_val = float(pos.get('entry_value', 0) or 0)
        qty = float(pos.get('quantity', 0) or 0)
        is_scout = pos.get('is_scout', False)
        
        try:
            t = client.get_ticker(ex, sym)
            price = float(t.get('price', 0) or 0) if t else 0
        except:
            price = 0
        
        if price > 0 and entry_val > 0:
            current_val = qty * price
            gross = current_val - entry_val
            pnl_pct = (gross / entry_val * 100)
            
            # Net calc
            fee_rate = {'binance': 0.001, 'kraken': 0.0026, 'alpaca': 0.0025}.get(ex.lower(), 0.002)
            total_rate = fee_rate + 0.002 + 0.001  # fee + slippage + spread
            entry_fee = float(pos.get('entry_fee', 0) or entry_val * total_rate)
            exit_fee = current_val * total_rate
            net = gross - entry_fee - exit_fee
            
            scout_tag = '🏹' if is_scout else '⚔️'
            
            if net >= 0.01:
                kills_ready.append((sym, ex, net, pnl_pct, scout_tag))
            elif gross > 0:
                waiting.append((sym, ex, net, pnl_pct, scout_tag))
            else:
                holding.append((sym, ex, net, pnl_pct, scout_tag))

    if kills_ready:
        print('🎯 KILL READY:')
        for sym, ex, net, pct, tag in kills_ready:
            print(f'   {tag} {ex.upper():8s} {sym:12s} | Net: ${net:+.4f} ({pct:+.1f}%)')
        print()

    if waiting:
        print('⏳ WAITING (profitable, not yet penny):')
        for sym, ex, net, pct, tag in waiting:
            print(f'   {tag} {ex.upper():8s} {sym:12s} | Net: ${net:+.4f} ({pct:+.1f}%)')
        print()

    if holding:
        print('🛡️ HOLDING (no forced loss):')
        for sym, ex, net, pct, tag in holding:
            print(f'   {tag} {ex.upper():8s} {sym:12s} | Net: ${net:+.4f} ({pct:+.1f}%)')
        print()

    print('-' * 60)
    print(f'📊 SUMMARY:')
    print(f'   🎯 Kills Ready: {len(kills_ready)}')
    print(f'   ⏳ Waiting: {len(waiting)}')
    print(f'   🛡️ Holding: {len(holding)}')
    print()
    print(f'   Total Trades: {state.get("total_trades", 0)}')
    print(f'   Wins: {state.get("wins", 0)}')
    print(f'   Harvested: ${state.get("harvested", 0):.4f}')
    print()
    print('=' * 60)
    print()
    print('☘️ "The boys are watching. Every penny will be taken."')
    print()


if __name__ == "__main__":
    main()
