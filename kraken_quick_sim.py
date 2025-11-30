#!/usr/bin/env python3
"""
🐙 KRAKEN QUICK STRATEGY ANALYSIS 🐙
=====================================
Fast simulation using current market snapshot to evaluate strategies.
Runs 50 simulated cycles per strategy to give quick flavor of Kraken ecosystem.
"""

import os
import sys
import random
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List

sys.path.insert(0, '/workspaces/aureon-trading')
from kraken_client import KrakenClient

# Kraken fees
TAKER_FEE = 0.0026  # 0.26%

@dataclass
class SimResult:
    strategy: str
    trades: int
    wins: int
    losses: int
    win_rate: float
    gross_pnl: float
    total_fees: float
    net_pnl: float
    best_trade: float
    worst_trade: float
    avg_hold_cycles: float

def banner():
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║   🐙 KRAKEN QUICK STRATEGY ANALYZER 🐙                                   ║
║                                                                          ║
║   Fast 50-cycle simulation per strategy using REAL market data          ║
║   Analyzing: MOMENTUM | MEAN_REVERSION | SCALPING | SWING               ║
╚══════════════════════════════════════════════════════════════════════════╝
""")

def run_analysis():
    banner()
    
    print("📡 Connecting to Kraken and fetching market data...")
    client = KrakenClient()
    
    # Get all tickers
    tickers = client.get_24h_tickers()
    print(f"✅ Loaded {len(tickers)} trading pairs from Kraken\n")
    
    # Filter for USD pairs with volume
    usd_pairs = []
    for t in tickers:
        symbol = t.get('symbol', '')
        if symbol.endswith('USD') and not symbol.endswith('USDT') and not symbol.endswith('USDC'):
            price = float(t.get('lastPrice', 0) or 0)
            # Kraken uses quoteVolume, not volume
            vol = float(t.get('quoteVolume', 0) or t.get('volume', 0) or 0)
            change = float(t.get('priceChangePercent', 0) or 0)
            if price > 0 and vol > 100:  # At least $100 in volume
                # Use price for high/low if not available
                high = float(t.get('highPrice', 0) or 0)
                low = float(t.get('lowPrice', 0) or 0)
                if high == 0:
                    high = price * 1.02  # Estimate 2% range
                if low == 0:
                    low = price * 0.98
                usd_pairs.append({
                    'symbol': symbol,
                    'price': price,
                    'volume': vol,
                    'change24h': change,
                    'high': high,
                    'low': low,
                })
    
    print(f"📊 Found {len(usd_pairs)} active USD trading pairs\n")
    
    # Sort by different criteria for different strategies
    by_momentum = sorted([p for p in usd_pairs if p['change24h'] > 5], 
                         key=lambda x: x['change24h'], reverse=True)[:30]
    by_reversal = sorted([p for p in usd_pairs if p['change24h'] < -5],
                         key=lambda x: x['change24h'])[:30]
    by_volume = sorted(usd_pairs, key=lambda x: x['volume'], reverse=True)[:30]
    by_range = sorted([p for p in usd_pairs if p['high'] > p['low']], 
                      key=lambda x: (x['high']-x['low'])/x['low'] if x['low'] > 0 else 0,
                      reverse=True)[:30]
    
    strategies = {
        'MOMENTUM': {
            'description': 'Ride strong upward moves (24h change > 5%)',
            'pairs': by_momentum,
            'take_profit': 0.03,  # 3% profit target
            'stop_loss': 0.02,    # 2% stop loss
            'win_chance': 0.55,   # Slightly edge-positive
        },
        'MEAN_REVERSION': {
            'description': 'Buy oversold assets (24h change < -5%)',
            'pairs': by_reversal,
            'take_profit': 0.025,  # 2.5% bounce target
            'stop_loss': 0.015,    # 1.5% stop loss
            'win_chance': 0.52,
        },
        'SCALPING': {
            'description': 'High-frequency on highest volume pairs',
            'pairs': by_volume,
            'take_profit': 0.008,  # 0.8% quick profits
            'stop_loss': 0.004,    # 0.4% tight stop
            'win_chance': 0.60,    # Higher win rate but smaller gains
        },
        'SWING': {
            'description': 'Trade wide price ranges (high volatility)',
            'pairs': by_range,
            'take_profit': 0.05,   # 5% profit target
            'stop_loss': 0.025,    # 2.5% stop loss
            'win_chance': 0.48,    # Lower win rate but bigger wins
        },
    }
    
    results: List[SimResult] = []
    
    for name, config in strategies.items():
        print(f"\n{'='*70}")
        print(f"🎯 Simulating {name} Strategy")
        print(f"   {config['description']}")
        print(f"   Available pairs: {len(config['pairs'])}")
        print(f"{'='*70}")
        
        if len(config['pairs']) == 0:
            print(f"   ⚠️ No qualifying pairs for this strategy right now")
            results.append(SimResult(
                strategy=name, trades=0, wins=0, losses=0, win_rate=0,
                gross_pnl=0, total_fees=0, net_pnl=0, best_trade=0, 
                worst_trade=0, avg_hold_cycles=0
            ))
            continue
        
        # Simulate 50 trades per strategy
        balance = 1000.0
        trades = []
        wins = 0
        losses = 0
        total_fees = 0
        gross_pnl = 0
        
        for i in range(50):
            if len(config['pairs']) == 0:
                break
                
            # Pick a random pair from qualifying candidates
            pair = random.choice(config['pairs'])
            entry_price = pair['price']
            position_size = balance * 0.10  # 10% per trade
            
            # Entry fee
            entry_fee = position_size * TAKER_FEE
            total_fees += entry_fee
            
            # Simulate outcome based on strategy's edge
            is_win = random.random() < config['win_chance']
            
            # Add some variance to profit/loss
            if is_win:
                # Win: hit take profit (with some variance)
                tp_mult = config['take_profit'] * (0.7 + random.random() * 0.6)
                exit_price = entry_price * (1 + tp_mult)
                pnl = position_size * tp_mult
            else:
                # Loss: hit stop loss (with some variance)
                sl_mult = config['stop_loss'] * (0.5 + random.random() * 0.7)
                exit_price = entry_price * (1 - sl_mult)
                pnl = -position_size * sl_mult
            
            # Exit fee
            exit_value = position_size + pnl
            exit_fee = exit_value * TAKER_FEE
            total_fees += exit_fee
            
            # Net PnL after fees
            net_pnl = pnl - entry_fee - exit_fee
            gross_pnl += pnl
            balance += net_pnl
            
            trade_result = {
                'symbol': pair['symbol'],
                'pnl': net_pnl,
                'win': is_win,
            }
            trades.append(trade_result)
            
            if is_win:
                wins += 1
            else:
                losses += 1
            
            # Print some trades
            if i < 5 or i >= 45:
                status = "✅" if is_win else "❌"
                print(f"   Trade {i+1:2d}: {pair['symbol']:15s} | Net: ${net_pnl:+8.2f} | {status}")
        
        if trades:
            pnls = [t['pnl'] for t in trades]
            best_trade = max(pnls)
            worst_trade = min(pnls)
            win_rate = wins / len(trades) * 100 if trades else 0
            net_total = sum(pnls)
        else:
            best_trade = worst_trade = win_rate = net_total = 0
        
        result = SimResult(
            strategy=name,
            trades=len(trades),
            wins=wins,
            losses=losses,
            win_rate=win_rate,
            gross_pnl=gross_pnl,
            total_fees=total_fees,
            net_pnl=net_total,
            best_trade=best_trade,
            worst_trade=worst_trade,
            avg_hold_cycles=1.0,
        )
        results.append(result)
        
        print(f"\n   📈 {name} Summary:")
        print(f"      Final Balance: ${balance:.2f} (started $1000)")
        print(f"      Trades: {len(trades)} | Wins: {wins} | Losses: {losses}")
        print(f"      Win Rate: {win_rate:.1f}%")
        print(f"      Gross P&L: ${gross_pnl:+.2f}")
        print(f"      Total Fees: ${total_fees:.2f}")
        print(f"      💰 NET P&L: ${net_total:+.2f}")
    
    # Final comparison
    print("\n")
    print("╔══════════════════════════════════════════════════════════════════════════╗")
    print("║                    📊 STRATEGY COMPARISON RESULTS 📊                     ║")
    print("╚══════════════════════════════════════════════════════════════════════════╝")
    print()
    print(f"{'Strategy':<18} {'Trades':>7} {'Win%':>7} {'Gross':>10} {'Fees':>8} {'NET P&L':>12}")
    print("-" * 70)
    
    for r in results:
        net_emoji = "🟢" if r.net_pnl > 0 else "🔴"
        print(f"{r.strategy:<18} {r.trades:>7} {r.win_rate:>6.1f}% {r.gross_pnl:>+10.2f} {r.total_fees:>8.2f} {net_emoji} ${r.net_pnl:>+9.2f}")
    
    print("-" * 70)
    
    # Find best strategy
    best = max(results, key=lambda x: x.net_pnl)
    total_net = sum(r.net_pnl for r in results)
    total_fees = sum(r.total_fees for r in results)
    
    print()
    print(f"🏆 BEST STRATEGY: {best.strategy} with ${best.net_pnl:+.2f} net profit")
    print(f"   Total Kraken Fees Paid: ${total_fees:.2f}")
    print(f"   Combined Net Across All Strategies: ${total_net:+.2f}")
    print()
    
    # Kraken ecosystem insights
    print("╔══════════════════════════════════════════════════════════════════════════╗")
    print("║                    🐙 KRAKEN ECOSYSTEM INSIGHTS 🐙                       ║")
    print("╚══════════════════════════════════════════════════════════════════════════╝")
    print()
    print(f"   📈 Total USD pairs available: {len(usd_pairs)}")
    print(f"   🚀 High momentum pairs (>5% gain): {len(by_momentum)}")
    print(f"   📉 Oversold pairs (>5% drop): {len(by_reversal)}")
    print(f"   💎 High volatility pairs: {len(by_range)}")
    print()
    print("   Top 5 Momentum Leaders:")
    for p in by_momentum[:5]:
        print(f"      {p['symbol']:12s} @ ${p['price']:<12.6f}  +{p['change24h']:.1f}%")
    print()
    print("   Top 5 Oversold (Reversal Candidates):")
    for p in by_reversal[:5]:
        print(f"      {p['symbol']:12s} @ ${p['price']:<12.6f}  {p['change24h']:.1f}%")
    print()
    print("   Top 5 by Volume (Scalping Candidates):")
    for p in by_volume[:5]:
        print(f"      {p['symbol']:12s} @ ${p['price']:<12.6f}  Vol: ${p['volume']/1e6:.1f}M")
    print()

if __name__ == '__main__':
    run_analysis()
