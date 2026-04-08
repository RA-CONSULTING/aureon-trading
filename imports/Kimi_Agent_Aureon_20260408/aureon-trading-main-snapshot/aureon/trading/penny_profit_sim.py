#!/usr/bin/env python3
"""
🪙 PENNY PROFIT SIMULATOR
========================
Creates a validated lookup table for the brain.

For each coin + trade size + exchange:
- Calculate EXACT fees
- Calculate minimum price move for 1 penny net profit
- Output a JSON the brain can load

The stupidest AND smartest strategy:
"Am I up by X? SELL. Next trade."

Gary Leckey & GitHub Copilot | December 2025
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import json
import os
from datetime import datetime
from typing import Dict, List

# Exchange fee structures (taker fees - worst case)
EXCHANGE_FEES = {
    'binance': {
        'maker': 0.001,    # 0.10%
        'taker': 0.001,    # 0.10% (with BNB)
        'min_notional': 1.0,
        'slippage': 0.0003,  # Lower slippage (high liquidity)
        'spread': 0.0005,
    },
    'kraken': {
        'maker': 0.0016,   # 0.16%
        'taker': 0.0026,   # 0.26%
        'min_notional': 5.0,
        'slippage': 0.0005,
        'spread': 0.0008,
    },
    'alpaca': {
        'maker': 0.0015,   # 0.15% Tier 1
        'taker': 0.0025,   # 0.25% Tier 1
        'min_notional': 1.0,
        'slippage': 0.0005,
        'spread': 0.0008,
    },
    'capital': {
        'maker': 0.001,    # ~0.1% spread
        'taker': 0.001,
        'min_notional': 10.0,
        'slippage': 0.0008,
        'spread': 0.0020,  # Wider spread on CFDs
    },
}

# Additional costs
SLIPPAGE_PCT = 0.001      # 0.1% estimated slippage per side
SPREAD_PCT = 0.0005       # 0.05% spread cost

# Target net profit
TARGET_NET_PROFIT = 0.01  # 1 penny = $0.01

# Trade sizes to simulate
TRADE_SIZES = [5.0, 7.50, 10.0, 15.0, 20.0, 25.0, 50.0]


def calculate_penny_profit_threshold(
    trade_size: float,
    exchange: str,
    use_maker: bool = False
) -> Dict:
    """
    Calculate the exact gross profit needed for 1 penny net profit.
    
    Returns dict with:
    - total_fees: All fees for round-trip
    - min_gross_profit: Gross profit needed for 1p net
    - min_price_move_pct: Percentage price move needed
    - breakeven_price_multiplier: Multiply entry price by this for exit
    """
    fees = EXCHANGE_FEES.get(exchange, EXCHANGE_FEES['binance'])
    fee_rate = fees['maker'] if use_maker else fees['taker']
    
    # Use exchange-specific slippage/spread if available, else global fallback
    slippage_rate = fees.get('slippage', SLIPPAGE_PCT)
    spread_rate = fees.get('spread', SPREAD_PCT)
    
    # Round-trip costs (BUY + SELL)
    entry_fee = trade_size * fee_rate
    exit_fee = trade_size * fee_rate  # Approximate (actual exit value varies slightly)
    slippage = trade_size * slippage_rate * 2  # Both sides
    spread = trade_size * spread_rate * 2
    
    total_costs = entry_fee + exit_fee + slippage + spread
    
    # Minimum gross profit = costs + target net profit
    min_gross_profit = total_costs + TARGET_NET_PROFIT
    
    # Price move percentage needed
    min_price_move_pct = (min_gross_profit / trade_size) * 100
    
    # Multiplier for exit price (entry * this = min exit price)
    breakeven_multiplier = 1 + (min_gross_profit / trade_size)
    
    return {
        'trade_size': trade_size,
        'exchange': exchange,
        'fee_type': 'maker' if use_maker else 'taker',
        'entry_fee': round(entry_fee, 6),
        'exit_fee': round(exit_fee, 6),
        'slippage': round(slippage, 6),
        'spread': round(spread, 6),
        'total_costs': round(total_costs, 6),
        'target_net_profit': TARGET_NET_PROFIT,
        'min_gross_profit': round(min_gross_profit, 6),
        'min_price_move_pct': round(min_price_move_pct, 4),
        'exit_multiplier': round(breakeven_multiplier, 6),
    }


def simulate_trades(num_trades: int, win_rate: float, avg_trade_size: float, exchange: str) -> Dict:
    """
    Simulate N trades with penny profit strategy.
    
    Assumes:
    - Win = hit penny profit target
    - Loss = hit stop loss (assume 2x the profit target as max loss)
    """
    threshold = calculate_penny_profit_threshold(avg_trade_size, exchange)
    
    import random
    
    total_pnl = 0.0
    wins = 0
    losses = 0
    
    for _ in range(num_trades):
        if random.random() < win_rate:
            # WIN: Made penny profit
            total_pnl += TARGET_NET_PROFIT
            wins += 1
        else:
            # LOSS: Hit stop loss (assume lose the costs + small buffer)
            loss = threshold['total_costs'] * 1.5  # Lose 1.5x costs on bad trade
            total_pnl -= loss
            losses += 1
    
    return {
        'num_trades': num_trades,
        'win_rate_target': win_rate,
        'actual_win_rate': wins / num_trades if num_trades > 0 else 0,
        'wins': wins,
        'losses': losses,
        'total_pnl': round(total_pnl, 4),
        'avg_pnl_per_trade': round(total_pnl / num_trades, 6) if num_trades > 0 else 0,
        'threshold_used': threshold,
    }


def generate_lookup_table() -> Dict:
    """
    Generate the complete lookup table for all exchanges and trade sizes.
    This is what the brain loads to know exact exit targets.
    """
    table = {
        'generated_at': datetime.now().isoformat(),
        'target_net_profit': TARGET_NET_PROFIT,
        'strategy': 'PENNY_PROFIT',
        'description': 'Exit when gross profit >= min_gross_profit for 1 penny net',
        'thresholds': {},
    }
    
    for exchange in EXCHANGE_FEES.keys():
        table['thresholds'][exchange] = {}
        
        for size in TRADE_SIZES:
            # Calculate for taker fees (worst case, most common)
            taker = calculate_penny_profit_threshold(size, exchange, use_maker=False)
            # Also calculate maker for reference
            maker = calculate_penny_profit_threshold(size, exchange, use_maker=True)
            
            table['thresholds'][exchange][f'${size:.2f}'] = {
                'taker': taker,
                'maker': maker,
                'quick_ref': {
                    'min_gross_taker': taker['min_gross_profit'],
                    'min_gross_maker': maker['min_gross_profit'],
                    'min_move_pct_taker': taker['min_price_move_pct'],
                    'min_move_pct_maker': maker['min_price_move_pct'],
                }
            }
    
    return table


def print_summary():
    """Print a human-readable summary."""
    print("=" * 70)
    print("🪙 PENNY PROFIT STRATEGY - LOOKUP TABLE")
    print("=" * 70)
    print(f"Target Net Profit: ${TARGET_NET_PROFIT:.2f} (1 penny)")
    print()
    
    for exchange in EXCHANGE_FEES.keys():
        fees = EXCHANGE_FEES[exchange]
        print(f"\n{'='*70}")
        print(f"🏦 {exchange.upper()}")
        print(f"   Maker: {fees['maker']*100:.2f}% | Taker: {fees['taker']*100:.2f}%")
        print(f"   Min Notional: ${fees['min_notional']:.2f}")
        print("-" * 70)
        print(f"   {'Size':>8} | {'Total Cost':>10} | {'Need Gross':>10} | {'Move %':>8} | Exit Rule")
        print(f"   {'-'*8}-+-{'-'*10}-+-{'-'*10}-+-{'-'*8}-+-{'-'*20}")
        
        for size in TRADE_SIZES:
            t = calculate_penny_profit_threshold(size, exchange, use_maker=False)
            print(f"   ${size:>7.2f} | ${t['total_costs']:>9.4f} | ${t['min_gross_profit']:>9.4f} | {t['min_price_move_pct']:>7.3f}% | P&L >= ${t['min_gross_profit']:.4f}")
    
    print("\n" + "=" * 70)
    print("🧠 BRAIN RULE:")
    print("=" * 70)
    print("""
    For each position:
    1. Look up exchange + trade_size in penny_profit_thresholds.json
    2. Get 'min_gross_profit' value
    3. IF (current_value - entry_value) >= min_gross_profit THEN SELL
    4. Pocket your penny. Next trade.
    
    Example ($7.50 on Binance):
    - Entry: $7.50
    - Min Gross Profit: $0.04
    - Exit when position value >= $7.54
    - Net profit after fees: $0.01 ✓
    """)
    
    # Run a quick simulation
    print("=" * 70)
    print("📊 SIMULATION: 1000 trades at 55% win rate, $7.50 avg")
    print("=" * 70)
    sim = simulate_trades(1000, 0.55, 7.50, 'binance')
    print(f"   Wins: {sim['wins']} | Losses: {sim['losses']}")
    print(f"   Win Rate: {sim['actual_win_rate']*100:.1f}%")
    print(f"   Total P&L: ${sim['total_pnl']:.2f}")
    print(f"   Avg per trade: ${sim['avg_pnl_per_trade']:.4f}")
    print()
    
    # Different win rates
    print("=" * 70)
    print("📊 WIN RATE SENSITIVITY (1000 trades, $7.50 Binance)")
    print("=" * 70)
    for wr in [0.50, 0.52, 0.55, 0.58, 0.60, 0.65, 0.70]:
        sim = simulate_trades(1000, wr, 7.50, 'binance')
        profit_icon = "✅" if sim['total_pnl'] > 0 else "❌"
        print(f"   {wr*100:.0f}% WR → P&L: ${sim['total_pnl']:>7.2f} {profit_icon}")


def save_lookup_table(filepath: str = 'penny_profit_thresholds.json'):
    """Save the lookup table for the brain to load."""
    table = generate_lookup_table()
    
    with open(filepath, 'w') as f:
        json.dump(table, f, indent=2)
    
    print(f"\n💾 Saved lookup table to: {filepath}")
    return table


if __name__ == '__main__':
    print_summary()
    save_lookup_table()
    
    print("\n" + "=" * 70)
    print("🎯 NEXT STEP: Load penny_profit_thresholds.json in the brain")
    print("=" * 70)
