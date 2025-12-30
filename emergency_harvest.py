#!/usr/bin/env python3
"""🚨 EMERGENCY HARVESTER 🚨

Closes ONLY positions that are already at confirmed penny-profit.
Never forces loss exits.

Usage: python3 emergency_harvest.py [--dry-run]

Notes:
- Uses the unified state file (default: aureon_kraken_state.json)
- Routes sells through MultiExchangeClient so it works across exchanges
"""

import json
import os
import sys
import time
from datetime import datetime
from typing import Optional, Tuple, List


DEFAULT_STATE_FILE = 'aureon_kraken_state.json'


def _detect_exchange_for_symbol(multi_client, symbol: str, preferred: Optional[str] = None) -> Optional[str]:
    if preferred and preferred in getattr(multi_client, 'clients', {}):
        return preferred

    # Fast heuristic: Alpaca crypto uses BASE/QUOTE format
    if '/' in str(symbol) and 'alpaca' in getattr(multi_client, 'clients', {}):
        return 'alpaca'

    # Probe tickers to see which exchange recognizes the symbol
    for ex in (getattr(multi_client, 'clients', {}) or {}).keys():
        try:
            t = multi_client.get_ticker(ex, symbol) or {}
            price = float(t.get('price', 0) or t.get('last', 0) or 0)
            if price > 0:
                return ex
        except Exception:
            continue
    return None


def _is_order_success(result: dict) -> bool:
    if not isinstance(result, dict):
        return False
    if result.get('rejected') or result.get('error'):
        return False
    return bool(result.get('orderId') or result.get('txid') or result.get('id'))


def main() -> Tuple[int, float]:
    dry_run = '--dry-run' in sys.argv

    try:
        from unified_exchange_client import MultiExchangeClient
        from penny_profit_engine import get_penny_engine, check_penny_exit
    except ImportError as e:
        print(f"❌ Import error: {e}")
        sys.exit(1)

    state_file = os.getenv('AUREON_STATE_FILE', DEFAULT_STATE_FILE)
    try:
        with open(state_file) as f:
            state = json.load(f)
    except Exception as e:
        print(f"❌ Cannot load state '{state_file}': {e}")
        sys.exit(1)

    multi_client = MultiExchangeClient()
    engine = get_penny_engine()

    print()
    print("=" * 70)
    print(f"🚨 EMERGENCY HARVESTER - {'DRY RUN' if dry_run else 'LIVE MODE'} 🚨")
    print("=" * 70)
    print(f"State: {state_file}")
    print(f"Time:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    positions = (state.get('positions', {}) or {}).copy()
    sold: List[str] = []
    failed: List[Tuple[str, str]] = []
    total_gross = 0.0
    total_net = 0.0

    for symbol, pos in positions.items():
        try:
            qty = float((pos or {}).get('quantity', 0) or 0)
            entry_value = float((pos or {}).get('entry_value', 0) or 0)
        except Exception:
            continue

        if qty <= 0 or entry_value <= 0:
            continue

        exchange_hint = (pos or {}).get('exchange')
        exchange = _detect_exchange_for_symbol(multi_client, symbol, preferred=str(exchange_hint).lower() if exchange_hint else None)
        if not exchange:
            print(f"⚠️  {symbol}: Cannot detect exchange - HOLDING")
            continue

        # Get current price
        try:
            t = multi_client.get_ticker(exchange, symbol) or {}
            current_price = float(t.get('price', 0) or t.get('last', 0) or 0)
        except Exception as e:
            print(f"⚠️  {exchange.upper()} {symbol}: Price error - {e}")
            continue

        if current_price <= 0:
            print(f"⚠️  {exchange.upper()} {symbol}: No ticker price")
            continue

        current_value = qty * current_price

        # PennyProfitEngine works off (entry_value, current_value)
        action, gross_pnl = check_penny_exit(exchange, entry_value, current_value)
        pnl_pct = (gross_pnl / entry_value * 100) if entry_value > 0 else 0.0

        threshold = engine.get_threshold(exchange, entry_value)
        total_cost = float(getattr(threshold, 'total_cost', 0.0) or 0.0)
        net_pnl_est = gross_pnl - total_cost

        # 🔒 NO-FORCED-LOSS: only sell on confirmed penny profit.
        should_sell = (action == 'TAKE_PROFIT') and (net_pnl_est >= 0.01)

        if should_sell:
            print(f"✅ {exchange.upper():7s} {symbol:12s} | Gross: ${gross_pnl:+.4f} ({pnl_pct:+.2f}%) | Net≈ ${net_pnl_est:+.4f}")

            if dry_run:
                sold.append(symbol)
                total_gross += gross_pnl
                total_net += net_pnl_est
                continue

            try:
                result = multi_client.place_market_order(exchange, symbol, 'SELL', quantity=qty)
                if _is_order_success(result):
                    sold.append(symbol)
                    total_gross += gross_pnl
                    total_net += net_pnl_est
                    if symbol in state.get('positions', {}):
                        del state['positions'][symbol]
                    print("   🎯 SOLD!")
                    time.sleep(0.25)
                else:
                    failed.append((symbol, str(result)))
                    print(f"   ❌ Failed: {result}")
            except Exception as e:
                failed.append((symbol, str(e)))
                print(f"   ❌ Error: {e}")
        else:
            verdict = "WAITING" if gross_pnl >= 0 else "HOLDING"
            print(f"⏳ {exchange.upper():7s} {symbol:12s} | Gross: ${gross_pnl:+.4f} ({pnl_pct:+.2f}%) | {verdict}")

    print()
    print("=" * 70)

    if sold:
        print(f"💰 {'WOULD SELL' if dry_run else 'SOLD'}: {len(sold)} positions")
        print(f"   Gross P&L: ${total_gross:+.4f}")
        print(f"   Net P&L≈  ${total_net:+.4f}")

        if not dry_run:
            state['timestamp'] = time.time()
            state['balance'] = float(state.get('balance', 0) or 0) + max(0.0, total_net)
            state['total_trades'] = int(state.get('total_trades', 0) or 0) + len(sold)
            state['wins'] = int(state.get('wins', 0) or 0) + len(sold)
            state['harvested'] = float(state.get('harvested', 0) or 0) + max(0.0, total_net)

            try:
                with open(state_file, 'w') as f:
                    json.dump(state, f, indent=2)
                print(f"   Updated balance: ${state['balance']:.2f}")
            except Exception as e:
                print(f"   ⚠️ Failed to write state: {e}")
    else:
        print("No confirmed penny-profit positions to close")

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
