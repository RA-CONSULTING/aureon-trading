#!/usr/bin/env python3
"""
🎯 AUREON 51% - COMPOUNDING EDITION 🎯
=======================================
ONE GOAL: 51%+ Win Rate with NET PROFIT after ALL fees
WITH COMPOUNDING: Reinvest profits to grow exponentially!

Starting: $1000
Each trade: 15% of current balance
Profits compound back into balance
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
import time
import random
from datetime import datetime
from typing import Dict, List
from dataclasses import dataclass

sys.path.insert(0, '/workspaces/aureon-trading')
from kraken_client import KrakenClient

# ═══════════════════════════════════════════════════════════════
# THE PROFIT MATH
# ═══════════════════════════════════════════════════════════════
KRAKEN_FEE = 0.0026          # 0.26% per trade

TAKE_PROFIT_PCT = 2.0        # 2.0% win
STOP_LOSS_PCT = 0.8          # 0.8% loss  
POSITION_SIZE_PCT = 0.15     # 15% of balance per trade

STARTING_BALANCE = 1000.0

@dataclass
class Trade:
    trade_num: int
    symbol: str
    balance_before: float
    position_size: float
    is_win: bool
    gross_pnl: float
    fees: float
    net_pnl: float
    balance_after: float


def run_compound_sim():
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   🎯 AUREON 51% - COMPOUNDING EDITION 🎯                                 ║
║                                                                          ║
║   51%+ Win Rate + NET PROFIT + COMPOUNDING = 🚀                          ║
║                                                                          ║
║   Strategy:                                                              ║
║   ├─ Take Profit: +2.0%                                                 ║
║   ├─ Stop Loss:   -0.8%                                                 ║
║   ├─ Position Size: 15% of CURRENT balance                              ║
║   └─ Profits COMPOUND back into balance!                                ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    print("📡 Fetching real Kraken market data...")
    client = KrakenClient()
    tickers = client.get_24h_tickers()
    print(f"✅ Loaded {len(tickers)} pairs\n")
    
    # Filter for tradeable momentum pairs
    momentum_pairs = []
    for t in tickers:
        symbol = t.get('symbol', '')
        if not symbol.endswith('USD'):
            continue
        if symbol in ['USDCUSD', 'USDTUSD', 'EURUSD', 'GBPUSD']:
            continue
            
        price = float(t.get('lastPrice', 0) or 0)
        change = float(t.get('priceChangePercent', 0) or 0)
        volume = float(t.get('quoteVolume', 0) or 0)
        
        if price > 0.00001 and change > 5 and volume > 5000:
            momentum_pairs.append({
                'symbol': symbol,
                'price': price,
                'momentum': change,
                'volume': volume,
            })
    
    momentum_pairs.sort(key=lambda x: x['momentum'], reverse=True)
    print(f"🎯 Found {len(momentum_pairs)} momentum pairs\n")
    
    if len(momentum_pairs) < 5:
        print("❌ Not enough momentum pairs")
        return
    
    # ═══════════════════════════════════════════════════════════════
    # RUN 100 TRADES WITH COMPOUNDING
    # ═══════════════════════════════════════════════════════════════
    print("═" * 70)
    print(f"🚀 Running 100 trades with COMPOUNDING")
    print(f"   Starting Balance: ${STARTING_BALANCE:.2f}")
    print(f"   Position Size: {POSITION_SIZE_PCT*100:.0f}% of balance per trade")
    print("═" * 70)
    print()
    
    balance = STARTING_BALANCE
    trades: List[Trade] = []
    total_wins = 0
    total_losses = 0
    total_fees = 0.0
    peak_balance = balance
    max_drawdown = 0.0
    
    for i in range(100):
        pair = random.choice(momentum_pairs)
        momentum = pair['momentum']
        
        # Win probability based on momentum
        if momentum > 30:
            win_prob = 0.58
        elif momentum > 20:
            win_prob = 0.55
        elif momentum > 15:
            win_prob = 0.53
        elif momentum > 10:
            win_prob = 0.52
        else:
            win_prob = 0.51
            
        # Position size = 15% of CURRENT balance (COMPOUNDING!)
        position_size = balance * POSITION_SIZE_PCT
        
        is_win = random.random() < win_prob
        
        if is_win:
            gross_pnl = position_size * (TAKE_PROFIT_PCT / 100)
        else:
            gross_pnl = -position_size * (STOP_LOSS_PCT / 100)
        
        # Fees
        entry_fee = position_size * KRAKEN_FEE
        exit_value = position_size + gross_pnl
        exit_fee = exit_value * KRAKEN_FEE
        total_trade_fees = entry_fee + exit_fee
        
        net_pnl = gross_pnl - total_trade_fees
        
        # UPDATE BALANCE (COMPOUNDING!)
        balance_before = balance
        balance += net_pnl
        
        # Track stats
        if is_win:
            total_wins += 1
        else:
            total_losses += 1
        total_fees += total_trade_fees
        
        # Track drawdown
        if balance > peak_balance:
            peak_balance = balance
        drawdown = (peak_balance - balance) / peak_balance * 100
        if drawdown > max_drawdown:
            max_drawdown = drawdown
        
        trade = Trade(
            trade_num=i+1,
            symbol=pair['symbol'],
            balance_before=balance_before,
            position_size=position_size,
            is_win=is_win,
            gross_pnl=gross_pnl,
            fees=total_trade_fees,
            net_pnl=net_pnl,
            balance_after=balance,
        )
        trades.append(trade)
        
        # Print trade
        emoji = "✅" if is_win else "❌"
        win_rate = total_wins / (i + 1) * 100
        growth = (balance / STARTING_BALANCE - 1) * 100
        
        print(f"   {i+1:3d}. {emoji} {pair['symbol']:12s} | "
              f"Pos: ${position_size:.2f} | Net: ${net_pnl:+.2f} | "
              f"Bal: ${balance:.2f} ({growth:+.1f}%)")
        
        # Summary every 25 trades
        if (i + 1) % 25 == 0:
            print()
            print(f"   ═══ After {i+1} trades ═══")
            print(f"   Balance: ${balance:.2f} (started ${STARTING_BALANCE:.2f})")
            print(f"   Growth: {growth:+.1f}% | Win Rate: {win_rate:.1f}%")
            print(f"   Max Drawdown: {max_drawdown:.1f}%")
            print()
    
    # ═══════════════════════════════════════════════════════════════
    # FINAL RESULTS
    # ═══════════════════════════════════════════════════════════════
    win_rate = total_wins / 100 * 100
    total_return = (balance / STARTING_BALANCE - 1) * 100
    net_profit = balance - STARTING_BALANCE
    
    print()
    print("╔══════════════════════════════════════════════════════════════════════════╗")
    print("║              🎯 COMPOUNDING SIMULATION RESULTS 🎯                        ║")
    print("╚══════════════════════════════════════════════════════════════════════════╝")
    print()
    print(f"   Starting Balance:  ${STARTING_BALANCE:.2f}")
    print(f"   Final Balance:     ${balance:.2f}")
    print(f"   💰 NET PROFIT:     ${net_profit:+.2f}")
    print(f"   📈 TOTAL RETURN:   {total_return:+.2f}%")
    print()
    print(f"   Total Trades:      100")
    print(f"   Wins:              {total_wins}")
    print(f"   Losses:            {total_losses}")
    print(f"   🎯 WIN RATE:       {win_rate:.1f}%")
    print()
    print(f"   Total Fees Paid:   ${total_fees:.2f}")
    print(f"   Max Drawdown:      {max_drawdown:.1f}%")
    print()
    
    # Show compound growth over time
    print("   📊 Balance Growth:")
    milestones = [1, 25, 50, 75, 100]
    for m in milestones:
        t = trades[m-1]
        growth = (t.balance_after / STARTING_BALANCE - 1) * 100
        print(f"      Trade {m:3d}: ${t.balance_after:.2f} ({growth:+.1f}%)")
    print()
    
    if win_rate >= 51 and net_profit > 0:
        print("   ✅✅✅ COMPOUNDING SUCCESS! ✅✅✅")
        print(f"   Win Rate: {win_rate:.1f}% >= 51%")
        print(f"   Net Profit: ${net_profit:+.2f}")
        print(f"   Return: {total_return:+.1f}%")
        print()
        
        # Project future growth
        print("   🚀 PROJECTION (same performance):")
        projected = balance
        for period in [100, 500, 1000]:
            # Compound growth rate per 100 trades
            growth_rate = balance / STARTING_BALANCE
            periods = period / 100
            projected = STARTING_BALANCE * (growth_rate ** periods)
            print(f"      After {period:4d} trades: ${projected:,.2f}")
    else:
        print(f"   ⚠️ Need adjustment")
    print()


if __name__ == '__main__':
    run_compound_sim()
