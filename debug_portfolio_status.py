#!/usr/bin/env python3
"""
DEBUG PORTFOLIO STATUS - Quick diagnostic of trading system health.

Shows:
1. Current cash on each exchange
2. Open positions and their P&L
3. System component status (Seer, King, Queen, Lyra)
4. Why trades might be blocked
5. Recent trade history

Gary Leckey | March 2026
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

def main():
    print("\n" + "=" * 70)
    print("  AUREON TRADING SYSTEM - PORTFOLIO DEBUG STATUS")
    print("=" * 70)
    print(f"  Timestamp: {datetime.now().isoformat()}")
    print()

    # 1. Check pre-trade balance snapshot
    print("--- EXCHANGE BALANCES (last snapshot) ---")
    try:
        with open('_pre_trade_balance_snapshot.json', 'r') as f:
            snap = json.load(f)
        snap_time = snap.get('datetime', 'unknown')
        print(f"  Snapshot from: {snap_time}")
        total_est = snap.get('total_estimated_usd', 0)
        print(f"  Total estimated USD: ${total_est:.2f}")

        for ex, data in snap.get('exchanges', {}).items():
            bals = data.get('balances', {})
            if ex == 'alpaca':
                cash = bals.get('cash', 0)
                pv = bals.get('portfolio_value', 0)
                print(f"\n  ALPACA: Cash=${cash:.2f}, Portfolio=${pv:.2f}")
                for sym, pos in bals.items():
                    if isinstance(pos, dict):
                        print(f"    {sym}: qty={pos.get('qty',0):.6f} entry=${pos.get('avg_entry_price',0):.4f} current=${pos.get('current_price',0):.4f} value=${pos.get('market_value',0):.4f}")
            elif ex == 'kraken':
                # Sum up stablecoins
                usd = float(bals.get('USD', 0))
                usdc = float(bals.get('USDC', 0))
                usdt = float(bals.get('USDT', 0))
                gbp = float(bals.get('GBP', 0))
                print(f"\n  KRAKEN: USD=${usd:.2f}, USDC=${usdc:.2f}, USDT=${usdt:.2f}, GBP={gbp:.2f}")
                crypto_count = sum(1 for k, v in bals.items()
                                   if k not in ['USD', 'USDC', 'USDT', 'GBP', 'EUR', 'TUSD']
                                   and float(v) > 0.0001)
                print(f"    Crypto positions: {crypto_count}")
            elif ex == 'binance':
                crypto_count = sum(1 for k, v in bals.items()
                                   if k not in ['USDT', 'USDC', 'BUSD', 'FDUSD', 'LDUSDC']
                                   and float(v) > 0.0001)
                print(f"\n  BINANCE: {crypto_count} crypto positions")
    except FileNotFoundError:
        print("  No balance snapshot found")
    except Exception as e:
        print(f"  Error reading snapshot: {e}")

    # 2. Check orca configuration
    print("\n--- ORCA KILL CYCLE CONFIGURATION ---")
    try:
        # Check key constants by importing
        sys.path.insert(0, os.getcwd())

        # Just read the values from the file
        with open('orca_complete_kill_cycle.py', 'r') as f:
            content = f.read()

        for line in content.split('\n'):
            stripped = line.strip()
            if stripped.startswith('QUEEN_MIN_COP ='):
                print(f"  {stripped}")
            elif stripped.startswith('QUEEN_MIN_PROFIT_PCT ='):
                print(f"  {stripped}")
            elif stripped.startswith('DEADLINE_MODE ='):
                print(f"  {stripped}")
            elif 'buy_amount >= ' in stripped and 'Minimum' in stripped:
                print(f"  Buy gate: {stripped}")
            elif 'cash.get(o.exchange, 0.0) >= ' in stripped:
                print(f"  Funded filter: {stripped}")
    except Exception as e:
        print(f"  Error reading config: {e}")

    # 3. Check order audit for recent trade results
    print("\n--- RECENT ORDER AUDIT ---")
    try:
        with open('aureon_order_audit.json', 'r') as f:
            audit = json.load(f)
        orders = audit.get('orders', [])
        print(f"  Total audited orders: {len(orders)}")

        # Show last 5
        for order in orders[-5:]:
            ts = order.get('timestamp', '?')
            status = order.get('final_status', '?')
            exchange = order.get('exchange', '?')
            pv = order.get('profit_verification', {})
            valid = pv.get('math_valid', False)
            expected = pv.get('expected_pnl', 0)
            verified = pv.get('verified_pnl', 0)
            print(f"  [{ts}] {exchange}: status={status} math_valid={valid} expected=${expected:.4f} verified=${verified:.4f}")
    except FileNotFoundError:
        print("  No order audit found")
    except Exception as e:
        print(f"  Error reading audit: {e}")

    # 4. Check Quadrumvirate availability
    print("\n--- QUADRUMVIRATE STATUS ---")
    modules = {
        'Queen Hive Mind': 'aureon_queen_hive_mind',
        'King Accounting': 'king_accounting',
        'Seer': 'aureon_seer',
        'Seer Integration': 'aureon_seer_integration',
        'Lyra': 'aureon_lyra',
        'Lyra Integration': 'aureon_lyra_integration',
        'Adaptive Profit Gate': 'adaptive_prime_profit_gate',
        'Cost Basis Tracker': 'cost_basis_tracker',
        'ThoughtBus': 'aureon_thought_bus',
    }
    for name, mod in modules.items():
        try:
            __import__(mod)
            print(f"  {name}: AVAILABLE")
        except ImportError as e:
            print(f"  {name}: MISSING ({e})")
        except Exception as e:
            print(f"  {name}: ERROR ({e})")

    # 5. Check live portfolio state
    print("\n--- LIVE PORTFOLIO STATE ---")
    try:
        with open('live_profit_state.json', 'r') as f:
            live = json.load(f)
        print(f"  Total portfolio: ${live.get('total_portfolio_usd', 0):.2f}")
        print(f"  Total P&L: ${live.get('total_pnl_usd', 0):.2f}")
        print(f"  Total positions: {live.get('total_positions', 0)}")
        print(f"  Profitable: {live.get('profitable_positions', 0)}")
    except FileNotFoundError:
        print("  No live profit state found")
    except Exception as e:
        print(f"  Error reading live state: {e}")

    # 6. Avalanche Treasury
    print("\n--- AVALANCHE TREASURY ---")
    try:
        with open('state/avalanche_treasury.json', 'r') as f:
            treasury = json.load(f)
        print(f"  Total USD: ${treasury.get('total_usd', 0):.4f}")
        print(f"  All-time harvested: ${treasury.get('total_harvested_all_time', 0):.4f}")
    except FileNotFoundError:
        print("  No treasury found")
    except Exception as e:
        print(f"  Error: {e}")

    # Summary
    print("\n" + "=" * 70)
    print("  DIAGNOSIS SUMMARY")
    print("=" * 70)
    print("""
  KEY FIXES APPLIED:
  1. Buy gate lowered from $50 to $1 (was blocking ALL trades)
  2. Funded filter lowered from $50 to $1 (was filtering ALL opportunities)
  3. quick_init auto-override REMOVED (was killing intelligence systems)
  4. DEADLINE_MODE disabled (was expired, causing stale parameters)
  5. Cost basis fallback strengthened (was blocking sells on unknown entries)
  6. Min trade sizes adjusted per exchange (Alpaca $1, Kraken $5, Binance $10)
  7. Cash threshold lowered to $1 (was blocking scan with <$3 total)
  8. QUEEN_MIN_PROFIT_PCT set to 0.40% (achievable on micro-positions)

  FOR 100% OPERATIONAL COGNITION:
  - Run with: python orca_complete_kill_cycle.py --autonomous --live
  - Seer, King, Queen, Lyra all wire up in run_autonomous()
  - Quadrumvirate 4-pillar consensus gates every trade
  - All intelligence systems boot with autonomous_mode=True
""")
    print("=" * 70)


if __name__ == '__main__':
    main()
