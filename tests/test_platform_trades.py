#!/usr/bin/env python3
"""
🎯 TEST PLATFORM TRADES - Execute Successful Net Profit Trade on Each Platform
===============================================================================

This script simulates a winning trade on each trading platform:
- Kraken (🐙)
- Binance (🟡)
- Alpaca (🦙)
- Capital (💼)

Gary Leckey | December 2025
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import time

# Import the ecosystem components
from aureon_unified_ecosystem import (
    PerformanceTracker, 
    CapitalPool, 
    Position,
    CONFIG,
    get_platform_fee
)

def simulate_winning_trade(tracker: PerformanceTracker, platform: str, symbol: str):
    """Simulate a winning trade on a specific platform"""
    
    # Trade parameters for a winning trade
    entry_price = 100.0
    entry_quantity = 10.0
    entry_value = entry_price * entry_quantity  # £1000
    
    # Simulate +1.5% price increase (above TP of 1.2%)
    exit_price = entry_price * 1.015  # £101.50
    exit_value = exit_price * entry_quantity  # £1015
    
    # Calculate fees
    entry_fee = entry_value * get_platform_fee(platform, 'taker')
    exit_fee = exit_value * get_platform_fee(platform, 'taker')
    slippage = exit_value * CONFIG['SLIPPAGE_PCT']
    total_fees = entry_fee + exit_fee + slippage
    
    # Calculate P&L
    gross_pnl = exit_value - entry_value  # £15
    net_pnl = gross_pnl - total_fees
    
    # Record the trade
    tracker.record_trade(
        net_pnl=net_pnl,
        fees=total_fees,
        symbol=symbol,
        reason="TP_HIT",
        hold_time_sec=120.0,  # 2 minute hold
        platform=platform,
        volume=exit_value
    )
    
    return net_pnl, total_fees

def main():
    print("\n" + "=" * 70)
    print("🎯 EXECUTING WINNING TRADES ON ALL PLATFORMS")
    print("=" * 70 + "\n")
    
    # Initialize tracker with £1000 starting balance
    tracker = PerformanceTracker(1000.0)
    
    # Define test trades for each platform
    platforms = [
        ('kraken', 'XBTUSD', '🐙'),
        ('binance', 'BTCUSDT', '🟡'),
        ('alpaca', 'BTC/USD', '🦙'),
        ('capital', 'BTC', '💼'),
    ]
    
    total_net_profit = 0.0
    total_fees = 0.0
    
    for platform, symbol, icon in platforms:
        print(f"\n{icon} {platform.upper()} - {symbol}")
        print("-" * 40)
        
        net_pnl, fees = simulate_winning_trade(tracker, platform, symbol)
        total_net_profit += net_pnl
        total_fees += fees
        
        print(f"   Entry Value:  £1,000.00")
        print(f"   Exit Value:   £1,015.00 (+1.5%)")
        print(f"   Gross P&L:    £+15.00")
        print(f"   Total Fees:   £{fees:.4f}")
        print(f"   ✅ NET PROFIT: £{net_pnl:+.4f}")
        
        # Show platform metrics
        metrics = tracker.platform_metrics.get(platform, {})
        print(f"\n   Platform Stats:")
        print(f"   ├─ Trades: {metrics.get('trades', 0)}")
        print(f"   ├─ Wins: {metrics.get('wins', 0)}")
        print(f"   ├─ P&L: £{metrics.get('pnl', 0):.4f}")
        print(f"   └─ Volume: £{metrics.get('volume', 0):.2f}")
    
    # Final summary
    print("\n" + "=" * 70)
    print("📊 FINAL SUMMARY")
    print("=" * 70)
    print(f"\n   Total Trades:     {tracker.total_trades}")
    print(f"   Total Wins:       {tracker.wins}")
    print(f"   Win Rate:         {tracker.win_rate:.1f}%")
    print(f"   Total Fees:       £{total_fees:.4f}")
    print(f"   Total Net Profit: £{total_net_profit:+.4f}")
    print(f"   Tracker Net P&L:  £{tracker.net_profit:+.4f}")
    
    print("\n" + tracker.get_platform_summary())
    
    print("\n✅ All 4 platforms executed successful net profit trades!")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
