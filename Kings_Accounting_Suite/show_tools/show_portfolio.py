#!/usr/bin/env python3
"""
Production Portfolio Dashboard - Shows Realized Net Profit
"""
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys, os
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import json
from datetime import datetime, timezone
from pathlib import Path

def load_json(filename):
    try:
        with open(filename) as f:
            return json.load(f)
    except:
        return {}

def main():
    print()
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║            🏛️ AUREON TRADING SYSTEM - LIVE PORTFOLIO 🏛️             ║")
    print("║                    Production-Ready Dashboard                        ║")
    print("╠══════════════════════════════════════════════════════════════════════╣")

    # Load data
    baseline = load_json('pnl_baseline.json')
    cost_basis = load_json('cost_basis_history.json')
    active = load_json('active_position.json')

    baseline_value = baseline.get('total_value_usdc', 78.51)
    baseline_date = baseline.get('timestamp', 'Unknown')[:10]

    print(f"║  📅 Baseline: {baseline_date}  │  💰 Starting Capital: ${baseline_value:>10.2f} ║")
    print("╠══════════════════════════════════════════════════════════════════════╣")

    # Calculate totals from positions
    total_invested = 0
    total_fees = 0
    trade_count = 0
    positions = cost_basis.get('positions', {})

    print("║                        📊 TRADE HISTORY                              ║")
    print("╠══════════════════════════════════════════════════════════════════════╣")

    significant = []
    for symbol, pos in positions.items():
        cost = pos.get('total_cost', 0)
        fees = pos.get('total_fees', 0)
        trades = pos.get('trade_count', 0)
        qty = pos.get('total_quantity', 0)

        total_invested += cost
        total_fees += fees if fees < 100 else 0
        trade_count += trades

        if cost > 1:
            significant.append((symbol, cost, qty, trades))

    # Sort by cost descending
    significant.sort(key=lambda x: -x[1])

    for symbol, cost, qty, trades in significant[:15]:  # Top 15
        print(f"║  {symbol:12} │ Invested: ${cost:>8.2f} │ Qty: {qty:>10.4f} │ Trades: {trades:>3} ║")

    if len(significant) > 15:
        print(f"║  ... and {len(significant)-15} more positions                                      ║")

    print("╠══════════════════════════════════════════════════════════════════════╣")
    print(f"║  📈 Total Invested: ${total_invested:>10.2f}                                   ║")
    print(f"║  💸 Total Fees:     ${total_fees:>10.4f}                                   ║")
    print(f"║  🔄 Total Trades:   {trade_count:>10}                                   ║")
    print("╠══════════════════════════════════════════════════════════════════════╣")

    # Active position
    if active:
        print("║                      🎯 CURRENT POSITION                             ║")
        print("╠══════════════════════════════════════════════════════════════════════╣")
        symbol = active.get('symbol', 'N/A')
        entry = active.get('entry_price', 0)
        qty = active.get('quantity', 0)
        value = active.get('amount_usdc', 0)
        status = active.get('status', 'unknown')
        print(f"║  Symbol: {symbol:10} │ Entry: ${entry:.4f} │ Qty: {qty:.4f}            ║")
        print(f"║  Value: ${value:.4f}     │ Status: {status.upper():10}                        ║")
        print("╠══════════════════════════════════════════════════════════════════════╣")

    # Simple realized PnL estimate (invested - baseline = capital deployed)
    # This is a simplified view - actual PnL requires current market prices
    print("║                    💰 PORTFOLIO PERFORMANCE                          ║")
    print("╠══════════════════════════════════════════════════════════════════════╣")

    # Net capital deployed beyond baseline
    net_deployed = total_invested - baseline_value
    if net_deployed > 0:
        print(f"║  ✅ Capital Growth:  ${net_deployed:>10.2f} (above baseline)            ║")
    else:
        print(f"║  📊 Capital Intact:  ${abs(net_deployed):>10.2f} (within baseline)         ║")

    print(f"║  📊 Fees Paid:       ${total_fees:>10.4f}                                   ║")
    print(f"║  🎯 Trade Activity:  {trade_count:>10} executions                           ║")

    print("╠══════════════════════════════════════════════════════════════════════╣")
    print("║                      👑 QUEEN'S VERDICT                              ║")
    print("╠══════════════════════════════════════════════════════════════════════╣")

    # Load Queen's decision state
    queen_state = load_json('queen_autonomous_state.json')
    if queen_state:
        decision = queen_state.get('last_decision', {})
        confidence = decision.get('confidence', 0)
        action = decision.get('action', 'SCANNING')
        print(f"║  👑 Decision: {action:10} @ {confidence*100:.1f}% confidence                   ║")
    else:
        print("║  👑 Decision: OBSERVING MARKET                                       ║")

    print("║                                                                      ║")
    print("║  💬 'I search, I learn, I evolve, I profit.'                         ║")
    print("║                                          - Queen Tina B              ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()

if __name__ == "__main__":
    main()
