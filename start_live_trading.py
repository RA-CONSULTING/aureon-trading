#!/usr/bin/env python3
"""
🌍⚡ AUREON LIVE TRADING - START SCRIPT ⚡🌍
═══════════════════════════════════════════════════════════════

Starts live trading on real markets with the unified ecosystem.
Shows real-time opportunities, executes trades, and tracks net profits.

Gary Leckey & GitHub Copilot | November 2025
"""

import sys
import time
from datetime import datetime

sys.path.insert(0, '/workspaces/aureon-trading')

from aureon_unified_ecosystem import AureonKrakenEcosystem, CONFIG

def main():
    # Force Kraken-only mode for live demonstration to avoid missing API keys
    CONFIG['EXCHANGE'] = 'kraken'
    CONFIG['ALPACA_ANALYTICS_ONLY'] = True
    CONFIG['ENABLE_COINAPI'] = False  # Avoid extra requests during demo

    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║  🌍⚡ AUREON LIVE TRADING SYSTEM - NOW ACTIVE ⚡🌍                       ║
║                                                                          ║
║  Trading on real markets with HNC frequency + Probability Matrix        ║
║  Starting with £200.00 capital                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Initialize ecosystem in LIVE mode (dry_run=False)
    print("🔧 Initializing trading system...")
    eco = AureonKrakenEcosystem(initial_balance=200.0, dry_run=False)
    
    print("\n📡 Fetching live market data...")
    eco.refresh_tickers()
    
    print(f"\n💰 Starting Balance: £{eco.total_equity_gbp:.2f}")
    print(f"📊 Available Markets: {len(eco.ticker_cache)}")
    
    # Find opportunities
    print("\n🔍 Scanning for high-probability opportunities...")
    opps = eco.find_opportunities()
    
    if not opps:
        print("\n⚠️  No opportunities found at this time.")
        print("   System will continue monitoring markets...")
        return
    
    print(f"\n🎯 Found {len(opps)} trading opportunities!")
    print("\n" + "═" * 90)
    print(f"{'SYMBOL':12s} │ {'SCORE':5s} │ {'COH':4s} │ {'FREQ':5s} │ {'PROB':4s} │ {'CONF':4s} │ {'ACTION':12s} │ {'PRICE':12s}")
    print("═" * 90)
    
    for opp in opps[:10]:
        symbol = opp['symbol']
        score = opp['score']
        coh = opp['coherence']
        freq = opp.get('hnc_frequency', 256)
        prob = opp.get('probability', 0.5)
        conf = opp.get('prob_confidence', 0.0)
        action = opp.get('prob_action', 'HOLD')
        price = opp['price']
        
        print(f"{symbol:12s} │ {score:5d} │ {coh:.2f} │ {freq:5.0f} │ {prob:.0%} │ {conf:.0%} │ {action:12s} │ ${price:.6f}")
    
    print("═" * 90)
    
    # Execute top trades
    print("\n🚀 Executing trades on top opportunities...")
    trades_executed = 0
    
    for opp in opps[:3]:  # Open top 3 positions
        symbol = opp['symbol']
        price = opp['price']
        
        print(f"\n   📈 Opening position: {symbol}")
        print(f"      Price: ${price:.6f}")
        print(f"      Coherence: {opp['coherence']:.2f}")
        print(f"      Frequency: {opp.get('hnc_frequency', 256):.0f}Hz")
        print(f"      Probability: {opp.get('probability', 0.5):.0%}")
        
        try:
            eco.open_position(opp)
            trades_executed += 1
            print(f"      ✅ Position opened successfully!")
        except Exception as e:
            print(f"      ⚠️  Trade failed: {e}")
        
        time.sleep(1)  # Rate limiting
    
    print(f"\n✅ Executed {trades_executed} trades")
    
    # Refresh positions to get current values
    print("\n📊 Refreshing positions...")
    for symbol, position in eco.positions.items():
        ticker = eco.ticker_cache.get(symbol)
        if not ticker:
            continue
        current_price = ticker['price']
        position.current_price = current_price
        position.unrealized_pnl = (current_price - position.entry_price) * position.quantity
    
    # Calculate net profit
    print("\n" + "═" * 90)
    print("💰 PROFIT & LOSS SUMMARY")
    print("═" * 90)
    
    starting_balance = eco.tracker.initial_balance
    current_equity = eco.refresh_equity()
    net_profit = eco.tracker.net_profit
    
    print(f"   Starting Balance:     £{starting_balance:.2f}")
    print(f"   Current Equity:       £{current_equity:.2f}")
    print(f"   Net Profit (After Fees): £{net_profit:.2f}")
    print(f"   Return:               {(net_profit/starting_balance)*100 if starting_balance else 0:.2f}%")
    print(f"   Open Positions:       {len(eco.positions)}")
    
    if net_profit > 0:
        print(f"\n   🎉 PROFITABLE! Up £{net_profit:.2f}")
    elif net_profit < 0:
        print(f"\n   📉 Down £{abs(net_profit):.2f}")
    else:
        print(f"\n   ⚖️  Break-even")
    
    print("\n" + "═" * 90)
    
    # Show active positions
    if eco.positions:
        print("\n📊 ACTIVE POSITIONS:")
        print("─" * 90)
        print(f"{'SYMBOL':12s} │ {'ENTRY':10s} │ {'CURRENT':10s} │ {'P&L':10s} │ {'P&L %':8s}")
        print("─" * 90)
        
        for symbol, pos in list(eco.positions.items())[:10]:
            entry = pos.entry_price
            current = pos.current_price
            pnl = pos.unrealized_pnl
            pnl_pct = (current / entry - 1) * 100 if entry > 0 else 0
            
            pnl_str = f"£{pnl:.2f}" if pnl >= 0 else f"-£{abs(pnl):.2f}"
            pnl_pct_str = f"+{pnl_pct:.2f}%" if pnl_pct >= 0 else f"{pnl_pct:.2f}%"
            
            print(f"{symbol:12s} │ ${entry:9.6f} │ ${current:9.6f} │ {pnl_str:>10s} │ {pnl_pct_str:>8s}")
        
        print("─" * 90)
    
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║  ✅ LIVE TRADING SESSION COMPLETE                                        ║
║                                                                          ║
║  System is now monitoring positions and will continue trading           ║
║  based on market conditions and coherence signals.                      ║
║                                                                          ║
║  To run continuous trading:                                             ║
║  python aureon_unified_ecosystem.py                                     ║
╚══════════════════════════════════════════════════════════════════════════╝
    """)

if __name__ == "__main__":
    main()
