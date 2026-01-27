#!/usr/bin/env python3
"""
🧪 PROFIT GATE SIMULATION TEST

This script simulates the trading logic to verify that:
1. Positions are only sold when NET PROFIT >= 0.5% after ALL fees
2. The harvester correctly blocks unprofitable sells
3. Round-trip costs are properly calculated

Run this BEFORE live trading to ensure the logic is correct!
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
from dataclasses import dataclass
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# Configuration (mirrors aureon_unified_ecosystem.py)
# ─────────────────────────────────────────────────────────────────────────────

CONFIG = {
    'KRAKEN_FEE_TAKER': 0.0040,      # 0.40% Kraken taker fee (ACTUAL observed)
    'BINANCE_FEE_TAKER': 0.001,      # 0.10% Binance taker fee
    'SLIPPAGE_PCT': 0.001,           # 0.10% estimated slippage
    'SPREAD_COST_PCT': 0.001,        # 0.10% spread cost estimate
    'MIN_PROFIT_PCT': 0.005,         # 0.50% minimum NET profit required
}

def get_platform_fee(exchange: str, fee_type: str = 'taker') -> float:
    """Get fee rate for a specific exchange"""
    if exchange == 'binance':
        return CONFIG['BINANCE_FEE_TAKER']
    elif exchange == 'kraken':
        return CONFIG['KRAKEN_FEE_TAKER']
    return 0.0026  # Default

# ─────────────────────────────────────────────────────────────────────────────
# Position Simulation
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SimPosition:
    symbol: str
    entry_price: float
    quantity: float
    entry_fee: float
    entry_value: float
    exchange: str = 'kraken'

def should_exit_trade(pos: SimPosition, current_price: float, reason: str) -> tuple[bool, str, float]:
    """
    Smart exit gate - only sell if we're making NET PROFIT after fees.
    Returns: (should_exit, explanation, net_pnl)
    
    📐 Uses consistent fee model matching penny profit formula:
    Combined rate = fee + slippage + spread for both legs
    """
    change_pct = (current_price - pos.entry_price) / pos.entry_price
    
    # Calculate P&L using combined rate (matches penny profit formula)
    fee_rate = get_platform_fee(pos.exchange, 'taker')
    slippage = CONFIG.get('SLIPPAGE_PCT', 0.002)
    spread = CONFIG.get('SPREAD_COST_PCT', 0.001)
    total_rate = fee_rate + slippage + spread
    
    exit_value = pos.quantity * current_price
    exit_fee = exit_value * total_rate
    
    total_expenses = pos.entry_fee + exit_fee  # Both use combined rate
    gross_pnl = exit_value - pos.entry_value
    net_pnl = gross_pnl - total_expenses
    
    # Calculate minimum required profit (0.5% buffer above breakeven)
    min_profit_buffer = pos.entry_value * CONFIG['MIN_PROFIT_PCT']
    min_net_profit = min_profit_buffer
    
    # Build explanation
    explanation = f"""
    📊 P&L Calculation for {pos.symbol}:
    ─────────────────────────────────────────
    Entry: {pos.quantity:.6f} @ ${pos.entry_price:.6f} = ${pos.entry_value:.4f}
    Entry Fee: ${pos.entry_fee:.4f} (combined rate: {total_rate*100:.2f}%)
    
    Exit: {pos.quantity:.6f} @ ${current_price:.6f} = ${exit_value:.4f}
    Exit Fee: ${exit_fee:.4f} (combined rate)
    Spread: ${spread_cost:.4f}
    
    Total Expenses: ${total_expenses:.4f}
    Gross P&L: ${gross_pnl:+.4f} ({change_pct*100:+.2f}%)
    Net P&L: ${net_pnl:+.4f}
    
    Minimum Required: ${min_net_profit:.4f} (0.5% of entry)
    Price Change Required for Profit: {((total_expenses + min_net_profit) / pos.entry_value) * 100:.2f}%
    """
    
    # HARVEST/TP check
    if reason in ("HARVEST", "TP", "bridge_harvest"):
        if net_pnl >= min_net_profit:
            return True, explanation + f"\n    ✅ EXIT APPROVED: Net ${net_pnl:.4f} >= Min ${min_net_profit:.4f}", net_pnl
        else:
            return False, explanation + f"\n    🛑 HOLDING: Net ${net_pnl:.4f} < Min ${min_net_profit:.4f}", net_pnl
    
    return net_pnl >= min_net_profit, explanation, net_pnl

# ─────────────────────────────────────────────────────────────────────────────
# Simulation Tests
# ─────────────────────────────────────────────────────────────────────────────

def simulate_round_trip(entry_price: float, exit_price: float, position_size_usd: float = 28.0, exchange: str = 'kraken'):
    """Simulate a complete buy → sell round trip"""
    
    quantity = position_size_usd / entry_price
    entry_fee = position_size_usd * get_platform_fee(exchange, 'taker')
    
    pos = SimPosition(
        symbol='TEST/USDC',
        entry_price=entry_price,
        quantity=quantity,
        entry_fee=entry_fee,
        entry_value=position_size_usd,
        exchange=exchange
    )
    
    should_exit, explanation, net_pnl = should_exit_trade(pos, exit_price, "HARVEST")
    
    return should_exit, explanation, net_pnl

def run_tests():
    print("=" * 70)
    print("🧪 PROFIT GATE SIMULATION TEST")
    print("=" * 70)
    print(f"\n📋 Configuration:")
    print(f"   Kraken Fee: {CONFIG['KRAKEN_FEE_TAKER']*100:.2f}%")
    print(f"   Slippage: {CONFIG['SLIPPAGE_PCT']*100:.2f}%")
    print(f"   Spread: {CONFIG['SPREAD_COST_PCT']*100:.2f}%")
    print(f"   Min Profit: {CONFIG['MIN_PROFIT_PCT']*100:.2f}%")
    
    # Calculate theoretical minimum price change needed
    # Round-trip cost = entry_fee + exit_fee + slippage + spread + min_profit
    # = 0.40% + 0.40% + 0.10% + 0.10% + 0.50% = 1.50%
    total_round_trip_pct = (CONFIG['KRAKEN_FEE_TAKER'] * 2 + CONFIG['SLIPPAGE_PCT'] + CONFIG['SPREAD_COST_PCT'] + CONFIG['MIN_PROFIT_PCT']) * 100
    print(f"\n   📈 Theoretical minimum price increase needed: {total_round_trip_pct:.2f}%")
    
    print("\n" + "─" * 70)
    
    # Test cases
    test_cases = [
        ("Small gain (0.5%)", 1.000, 1.005, False),   # Should HOLD - not enough
        ("Medium gain (1.0%)", 1.000, 1.010, False),  # Should HOLD - not enough
        ("Break-even gain (1.2%)", 1.000, 1.012, False),  # Should HOLD - barely covers fees
        ("Profitable gain (1.5%)", 1.000, 1.015, True),   # Should SELL - just profitable
        ("Good gain (2.0%)", 1.000, 1.020, True),    # Should SELL - clear profit
        ("Small loss (-0.5%)", 1.000, 0.995, False), # Should HOLD
        ("No change (0%)", 1.000, 1.000, False),     # Should HOLD
    ]
    
    passed = 0
    failed = 0
    
    for name, entry, exit_price, expected_sell in test_cases:
        should_sell, explanation, net_pnl = simulate_round_trip(entry, exit_price)
        
        change_pct = (exit_price - entry) / entry * 100
        result = "✅ PASS" if should_sell == expected_sell else "❌ FAIL"
        
        if should_sell == expected_sell:
            passed += 1
        else:
            failed += 1
        
        action = "SELL" if should_sell else "HOLD"
        expected_action = "SELL" if expected_sell else "HOLD"
        
        print(f"\n🧪 Test: {name}")
        print(f"   Price: ${entry:.4f} → ${exit_price:.4f} ({change_pct:+.2f}%)")
        print(f"   Net P&L: ${net_pnl:+.4f}")
        print(f"   Action: {action} | Expected: {expected_action}")
        print(f"   {result}")
        
        if should_sell != expected_sell:
            print(explanation)
    
    print("\n" + "=" * 70)
    print(f"📊 Results: {passed}/{passed+failed} tests passed")
    
    if failed > 0:
        print("❌ SOME TESTS FAILED - Do NOT run live trading!")
        return False
    else:
        print("✅ ALL TESTS PASSED - Profit gate logic is correct!")
        return True

def simulate_real_scenario():
    """Simulate based on actual recent trades"""
    print("\n" + "=" * 70)
    print("📊 REAL SCENARIO SIMULATION (Based on recent Kraken trades)")
    print("=" * 70)
    
    # Actual recent trade patterns observed:
    # Buy at $0.0728, need to sell above what price?
    scenarios = [
        # (name, entry_price, current_price, position_usd)
        ("CC @ $0.0733 (current)", 0.0733, 0.0733, 28.0),  # Break-even
        ("CC @ $0.0737 (+0.5%)", 0.0733, 0.0737, 28.0),
        ("CC @ $0.0744 (+1.5%)", 0.0733, 0.0744, 28.0),
        ("CC @ $0.0755 (+3.0%)", 0.0733, 0.0755, 28.0),
        ("FARTCOIN @ $0.371 (current)", 0.371, 0.371, 28.0),
        ("FARTCOIN @ $0.377 (+1.5%)", 0.371, 0.377, 28.0),
    ]
    
    for name, entry, current, pos_size in scenarios:
        should_sell, explanation, net_pnl = simulate_round_trip(entry, current, pos_size)
        change_pct = (current - entry) / entry * 100
        action = "🔴 SELL" if should_sell else "⚪ HOLD"
        profit_emoji = "💚" if net_pnl > 0 else "❤️"
        print(f"\n{action} {name}")
        print(f"   Change: {change_pct:+.2f}% | Net P&L: {profit_emoji} ${net_pnl:+.4f}")

if __name__ == "__main__":
    success = run_tests()
    simulate_real_scenario()
    
    print("\n" + "=" * 70)
    if success:
        print("✅ Ready for live trading - profit gate will prevent loss trades!")
    else:
        print("❌ Fix the logic before running live!")
    print("=" * 70)
    
    sys.exit(0 if success else 1)
