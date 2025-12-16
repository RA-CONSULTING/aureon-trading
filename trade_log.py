#!/usr/bin/env python3
"""
AUREON TRADING - COMPLETE TRADE LOG GENERATOR
Shows journey from losses to gains with timestamps
Run this on Windows: python trade_log.py
"""

import krakenex
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def generate_trade_log():
    # Connect to Kraken
    kraken = krakenex.API()
    kraken.key = os.getenv('KRAKEN_API_KEY')
    kraken.secret = os.getenv('KRAKEN_API_SECRET')

    # Get trade history
    result = kraken.query_private('TradesHistory', {'trades': True})

    if result.get('error'):
        print(f"❌ Error: {result['error']}")
        return

    trades = result.get('result', {}).get('trades', {})
    
    print("=" * 130)
    print("📜 AUREON TRADING SYSTEM - COMPLETE TRADE LOG: JOURNEY FROM LOSS TO GAIN")
    print("=" * 130)
    
    # Sort trades by time
    trade_list = []
    for tid, trade in trades.items():
        trade['id'] = tid
        trade_list.append(trade)
    
    trade_list.sort(key=lambda x: float(x.get('time', 0)))
    
    starting_capital = 93.21  # GBP
    
    print(f"\n💰 Starting Capital: £{starting_capital:.2f}")
    print(f"📅 Trade Period: {datetime.fromtimestamp(float(trade_list[0].get('time', 0))).strftime('%Y-%m-%d')} to {datetime.fromtimestamp(float(trade_list[-1].get('time', 0))).strftime('%Y-%m-%d')}")
    print("-" * 130)
    
    # Track holdings and P&L
    pair_holdings = {}
    running_cash = starting_capital
    total_fees = 0
    wins = 0
    losses = 0
    
    # Print header
    print(f"{'#':>3} | {'Timestamp':<20} | {'Action':<6} | {'Pair':<12} | {'Quantity':>14} | {'Price':>14} | {'Value':>12} | {'Fee':>8} | {'Running P&L':>14}")
    print("-" * 130)
    
    for i, trade in enumerate(trade_list, 1):
        ts = datetime.fromtimestamp(float(trade.get('time', 0))).strftime('%Y-%m-%d %H:%M:%S')
        pair = trade.get('pair', 'N/A')
        side = trade.get('type', 'N/A').upper()
        price = float(trade.get('price', 0))
        vol = float(trade.get('vol', 0))
        cost = float(trade.get('cost', 0))
        fee = float(trade.get('fee', 0))
        
        total_fees += fee
        realized_pnl = 0
        
        if side == 'BUY':
            running_cash -= (cost + fee)
            if pair not in pair_holdings:
                pair_holdings[pair] = {'qty': 0, 'cost_basis': 0}
            pair_holdings[pair]['qty'] += vol
            pair_holdings[pair]['cost_basis'] += cost + fee
            emoji = "🔵"
        else:  # SELL
            running_cash += (cost - fee)
            # Calculate realized P&L on this sale
            if pair in pair_holdings and pair_holdings[pair]['qty'] > 0:
                avg_cost_per_unit = pair_holdings[pair]['cost_basis'] / pair_holdings[pair]['qty']
                cost_of_sold = avg_cost_per_unit * vol
                proceeds = cost - fee
                realized_pnl = proceeds - cost_of_sold
                
                if realized_pnl >= 0:
                    wins += 1
                    emoji = "🟢"
                else:
                    losses += 1
                    emoji = "🔴"
                
                # Update holdings
                pair_holdings[pair]['qty'] -= vol
                pair_holdings[pair]['cost_basis'] -= cost_of_sold
            else:
                emoji = "⚪"
        
        # Calculate running P&L (cash vs starting)
        net_change = running_cash - starting_capital
        status = "🟢" if net_change >= 0 else "🔴"
        
        pnl_str = f"{status} £{net_change:+.2f}"
        if side == 'SELL' and realized_pnl != 0:
            pnl_str += f" (trade: £{realized_pnl:+.2f})"
        
        print(f"{i:>3} | {ts:<20} | {emoji} {side:<4} | {pair:<12} | {vol:>14.8f} | ${price:>13.6f} | ${cost:>11.2f} | ${fee:>7.4f} | {pnl_str}")
    
    print("-" * 130)
    
    # Calculate unrealized P&L in open positions
    print(f"\n📊 CURRENT HOLDINGS (Unrealized):")
    print("-" * 60)
    
    total_holding_value = 0
    for pair, holding in pair_holdings.items():
        if holding['qty'] > 0.0001:
            avg_cost = holding['cost_basis'] / holding['qty'] if holding['qty'] > 0 else 0
            print(f"   {pair}: {holding['qty']:.8f} @ avg ${avg_cost:.6f} (cost basis: ${holding['cost_basis']:.2f})")
            total_holding_value += holding['cost_basis']
    
    print("-" * 60)
    
    # Final summary
    final_cash_pnl = running_cash - starting_capital
    
    print(f"\n" + "=" * 130)
    print(f"📈 TRADING JOURNEY SUMMARY")
    print(f"=" * 130)
    print(f"   💰 Starting Capital:     £{starting_capital:.2f}")
    print(f"   💵 Current Cash:         £{running_cash:.2f}")
    print(f"   📦 In Open Positions:    ${total_holding_value:.2f}")
    print(f"   💸 Total Fees Paid:      ${total_fees:.4f}")
    print(f"   ")
    print(f"   📊 Total Trades:         {len(trade_list)}")
    print(f"   🟢 Winning Trades:       {wins}")
    print(f"   🔴 Losing Trades:        {losses}")
    print(f"   📈 Win Rate:             {(wins/(wins+losses)*100) if (wins+losses) > 0 else 0:.1f}%")
    print(f"   ")
    
    # Note: The actual portfolio value includes unrealized gains
    print(f"   💎 Cash P&L:             £{final_cash_pnl:+.2f} ({(final_cash_pnl/starting_capital)*100:+.1f}%)")
    print(f"   ")
    
    if final_cash_pnl >= 0:
        print(f"   ✅ STATUS: NET POSITIVE - Recovered all losses and in profit!")
    else:
        print(f"   ⚠️ STATUS: Cash shows drawdown but open positions contain value")
    
    print(f"=" * 130)
    
    # Save to file
    with open('trade_log_output.txt', 'w', encoding='utf-8') as f:
        f.write(f"AUREON TRADING - TRADE LOG GENERATED {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Starting: £{starting_capital:.2f} | Trades: {len(trade_list)} | Wins: {wins} | Losses: {losses}\n")
        f.write(f"Cash P&L: £{final_cash_pnl:+.2f}\n")
    
    print(f"\n💾 Log saved to trade_log_output.txt")

if __name__ == "__main__":
    generate_trade_log()
