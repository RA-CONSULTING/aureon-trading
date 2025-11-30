#!/usr/bin/env python3
"""
🎯 AUREON 51% - THE NET PROFIT MACHINE 🎯
==========================================
ONE GOAL: 51%+ Win Rate with NET PROFIT after ALL fees

MATH FOR SUCCESS:
- Kraken fee: 0.26% per trade (0.52% round-trip)
- To profit after fees with 51% win rate:
  - Win size must be > Loss size × (49/51) + fees
  - If we win $1.50 and lose $1.00, we profit with 51% wins!
  
STRATEGY:
- Take Profit: 1.5% (bigger wins)
- Stop Loss: 1.0% (smaller losses)
- Asymmetric R:R = 1.5:1
- With 51% win rate: Expected value = positive!

Gary Leckey & GitHub Copilot | November 2025
"""

import os
import sys
import time
import random
from datetime import datetime
from typing import Dict, List

sys.path.insert(0, '/workspaces/aureon-trading')
from kraken_client import KrakenClient

# ═══════════════════════════════════════════════════════════════
# THE MATH THAT GUARANTEES PROFIT
# ═══════════════════════════════════════════════════════════════
KRAKEN_FEE = 0.0026          # 0.26% per trade
ROUND_TRIP_FEE = 0.0052      # 0.52% total fees

TAKE_PROFIT_PCT = 1.5        # 1.5% profit target
STOP_LOSS_PCT = 1.0          # 1.0% stop loss
# R:R = 1.5:1, so with 51% wins we profit!

# Expected value per $100 trade at 51% win rate:
# Wins: 51% × ($1.50 - $0.52 fees) = 51% × $0.98 = $0.50
# Loss: 49% × ($1.00 + $0.52 fees) = 49% × $1.52 = $0.74
# Wait, that's negative! Let's adjust...

# NEW MATH - need bigger R:R for 51% to work with fees:
TAKE_PROFIT_PCT = 2.0        # 2.0% profit target  
STOP_LOSS_PCT = 0.8          # 0.8% stop loss
# R:R = 2.5:1
# Wins: 51% × ($2.00 - $0.52) = 51% × $1.48 = $0.75
# Loss: 49% × ($0.80 + $0.52) = 49% × $1.32 = $0.65
# NET: +$0.10 per $100 traded! ✅

POSITION_SIZE_PCT = 0.15     # 15% of capital per trade
MAX_POSITIONS = 4            # Max concurrent positions
MIN_TRADE_USD = 20.0         # Minimum trade size
MIN_MOMENTUM = 8.0           # Minimum 24h change to enter

class Position:
    def __init__(self, symbol: str, entry_price: float, quantity: float, 
                 entry_fee: float, momentum: float, position_value: float):
        self.symbol = symbol
        self.entry_price = entry_price
        self.quantity = quantity
        self.entry_fee = entry_fee
        self.momentum = momentum
        self.position_value = position_value
        self.entry_time = time.time()
        self.peak_price = entry_price  # Track peak for trailing
        self.cycles_held = 0


class Aureon51:
    """
    🎯 The 51% Win Rate Net Profit Machine
    """
    
    def __init__(self, initial_balance: float = 1000.0):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.client = KrakenClient()
        self.positions: Dict[str, Position] = {}
        self.ticker_cache: Dict[str, Dict] = {}
        self.price_history: Dict[str, List[float]] = {}  # Track price movement
        
        # Stats
        self.total_trades = 0
        self.wins = 0
        self.losses = 0
        self.total_fees = 0.0
        self.gross_profit = 0.0
        self.net_profit = 0.0
        self.iteration = 0
        
    def banner(self):
        print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   🎯 AUREON 51% - THE NET PROFIT MACHINE 🎯                              ║
║                                                                          ║
║   ONE GOAL: 51%+ Win Rate with NET PROFIT after ALL fees                ║
║                                                                          ║
║   📊 STRATEGY MATH:                                                      ║
║   ├─ Take Profit: +2.0% (bigger wins)                                   ║
║   ├─ Stop Loss:   -0.8% (smaller losses)                                ║
║   ├─ R:R Ratio:   2.5:1 (asymmetric edge)                               ║
║   └─ Kraken Fee:  0.52% round-trip                                      ║
║                                                                          ║
║   💰 Expected Value @ 51% Win Rate:                                      ║
║   Win: 51% × (2.0% - 0.52%) = +0.75%                                    ║
║   Loss: 49% × (0.8% + 0.52%) = -0.65%                                   ║
║   NET: +0.10% per trade cycle ✅                                         ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
        """)
        print(f"   💵 Starting Balance: ${self.initial_balance:.2f}")
        print(f"   📦 Position Size: {POSITION_SIZE_PCT*100:.0f}% | Max Positions: {MAX_POSITIONS}")
        print()
        
    def update_tickers(self) -> bool:
        """Fetch latest Kraken tickers and track price history"""
        try:
            tickers = self.client.get_24h_tickers()
            
            for t in tickers:
                symbol = t.get('symbol', '')
                price = float(t.get('lastPrice', 0) or 0)
                change = float(t.get('priceChangePercent', 0) or 0)
                volume = float(t.get('quoteVolume', 0) or 0)
                
                if price > 0:
                    # Track price history for movement detection
                    if symbol not in self.price_history:
                        self.price_history[symbol] = []
                    self.price_history[symbol].append(price)
                    # Keep last 50 prices
                    if len(self.price_history[symbol]) > 50:
                        self.price_history[symbol] = self.price_history[symbol][-50:]
                    
                    self.ticker_cache[symbol] = {
                        'price': price,
                        'change24h': change,
                        'volume': volume,
                    }
            return True
        except Exception as e:
            print(f"   ⚠️ Ticker update failed: {e}")
            return False
            
    def find_opportunities(self) -> List[Dict]:
        """Find high-probability momentum entries"""
        candidates = []
        
        for symbol, data in self.ticker_cache.items():
            # Only USD pairs, skip stablecoins
            if not symbol.endswith('USD'):
                continue
            if symbol in ['USDCUSD', 'USDTUSD', 'DAIUSD', 'PAXUSD', 'EURUSD', 'GBPUSD']:
                continue
            if symbol.endswith('USDT') or symbol.endswith('USDC'):
                continue
                
            change = data['change24h']
            price = data['price']
            volume = data['volume']
            
            # Only enter on strong momentum (increases win probability)
            if change >= MIN_MOMENTUM and price > 0.0001 and volume > 10000:
                
                # Check recent price trend (need upward momentum)
                history = self.price_history.get(symbol, [])
                if len(history) >= 3:
                    recent_trend = (history[-1] - history[-3]) / history[-3] * 100 if history[-3] > 0 else 0
                else:
                    recent_trend = 0
                
                # Score based on momentum strength and trend
                score = 50
                
                # 24h momentum
                if change > 30:
                    score += 25
                elif change > 20:
                    score += 20
                elif change > 15:
                    score += 15
                elif change > 10:
                    score += 10
                else:
                    score += 5
                    
                # Recent trend confirmation
                if recent_trend > 0.5:
                    score += 15
                elif recent_trend > 0.2:
                    score += 10
                elif recent_trend > 0:
                    score += 5
                elif recent_trend < -0.5:
                    score -= 20  # Avoid reversing momentum
                    
                # Volume bonus
                if volume > 500000:
                    score += 10
                elif volume > 100000:
                    score += 5
                    
                if score >= 65:  # Only high-quality setups
                    candidates.append({
                        'symbol': symbol,
                        'price': price,
                        'momentum': change,
                        'volume': volume,
                        'score': score,
                        'trend': recent_trend,
                    })
        
        candidates.sort(key=lambda x: x['score'], reverse=True)
        return candidates[:10]
        
    def check_positions(self):
        """Check positions for TP/SL - THE CORE PROFIT ENGINE"""
        closed = []
        
        for symbol, pos in list(self.positions.items()):
            pos.cycles_held += 1
            
            # Get current price from history (simulates real movement)
            history = self.price_history.get(symbol, [])
            if not history:
                continue
                
            current_price = history[-1]
            
            # Track peak for potential trailing stop
            if current_price > pos.peak_price:
                pos.peak_price = current_price
            
            pnl_pct = (current_price - pos.entry_price) / pos.entry_price * 100
            position_value = pos.quantity * current_price
            
            should_close = False
            is_win = False
            reason = ""
            
            # ═══════════════════════════════════════════════════
            # TAKE PROFIT - Lock in the WIN! 🎉
            # ═══════════════════════════════════════════════════
            if pnl_pct >= TAKE_PROFIT_PCT:
                should_close = True
                is_win = True
                reason = f"TP +{pnl_pct:.2f}%"
                
            # ═══════════════════════════════════════════════════
            # STOP LOSS - Cut the loss small 🛑
            # ═══════════════════════════════════════════════════
            elif pnl_pct <= -STOP_LOSS_PCT:
                should_close = True
                is_win = False
                reason = f"SL {pnl_pct:.2f}%"
                
            # ═══════════════════════════════════════════════════
            # TRAILING STOP - Protect big gains
            # ═══════════════════════════════════════════════════
            elif pos.peak_price > pos.entry_price * 1.015:  # 1.5% above entry
                trailing_stop = pos.peak_price * 0.992  # 0.8% below peak
                if current_price < trailing_stop:
                    should_close = True
                    is_win = pnl_pct > 0
                    reason = f"TRAIL {pnl_pct:.2f}%"
                    
            # ═══════════════════════════════════════════════════
            # TIME STOP - Don't hold losers too long
            # ═══════════════════════════════════════════════════
            elif pos.cycles_held > 60 and pnl_pct < 0.5:  # 5 min with no profit
                should_close = True
                is_win = pnl_pct > 0
                reason = f"TIME {pnl_pct:.2f}%"
                
            if should_close:
                # Calculate P&L with fees
                exit_fee = position_value * KRAKEN_FEE
                gross_pnl = (current_price - pos.entry_price) * pos.quantity
                total_fees = pos.entry_fee + exit_fee
                net_pnl = gross_pnl - total_fees
                
                # Update balance
                self.balance += position_value - exit_fee
                
                # Update stats
                self.total_trades += 1
                self.total_fees += total_fees
                self.gross_profit += gross_pnl
                
                if net_pnl > 0:
                    self.wins += 1
                    self.net_profit += net_pnl
                    emoji = "✅"
                else:
                    self.losses += 1
                    self.net_profit += net_pnl
                    emoji = "❌"
                    
                win_rate = (self.wins / self.total_trades * 100) if self.total_trades > 0 else 0
                
                print(f"   {emoji} CLOSE {symbol:12s} | {reason:12s} | "
                      f"Net: ${net_pnl:+.2f} | Fees: ${total_fees:.2f} | "
                      f"WR: {win_rate:.1f}%")
                
                closed.append(symbol)
                
        for symbol in closed:
            del self.positions[symbol]
            
    def enter_positions(self, candidates: List[Dict]):
        """Enter new high-probability positions"""
        if len(self.positions) >= MAX_POSITIONS:
            return
            
        available_slots = MAX_POSITIONS - len(self.positions)
        
        for candidate in candidates[:available_slots]:
            symbol = candidate['symbol']
            
            if symbol in self.positions:
                continue
                
            price = candidate['price']
            momentum = candidate['momentum']
            score = candidate['score']
            
            # Calculate position size
            position_usd = self.balance * POSITION_SIZE_PCT
            if position_usd < MIN_TRADE_USD:
                continue
                
            # Entry fee
            entry_fee = position_usd * KRAKEN_FEE
            quantity = (position_usd - entry_fee) / price
            
            self.balance -= position_usd
            
            self.positions[symbol] = Position(
                symbol=symbol,
                entry_price=price,
                quantity=quantity,
                entry_fee=entry_fee,
                momentum=momentum,
                position_value=position_usd,
            )
            
            print(f"   🎯 BUY  {symbol:12s} @ ${price:<12.6f} | "
                  f"${position_usd:.2f} | Score: {score} | +{momentum:.1f}%")
                  
    def get_equity(self) -> float:
        """Calculate total equity"""
        total = self.balance
        for symbol, pos in self.positions.items():
            history = self.price_history.get(symbol, [])
            price = history[-1] if history else pos.entry_price
            total += pos.quantity * price
        return total
        
    def print_status(self):
        """Print current status"""
        equity = self.get_equity()
        net_pnl = equity - self.initial_balance
        win_rate = (self.wins / self.total_trades * 100) if self.total_trades > 0 else 0
        
        print()
        print(f"   {'═'*65}")
        print(f"   🎯 Iteration {self.iteration} | Win Rate: {win_rate:.1f}% | Target: 51%+")
        print(f"   {'═'*65}")
        print(f"   💰 Equity: ${equity:.2f} | Net P&L: ${net_pnl:+.2f} ({net_pnl/self.initial_balance*100:+.2f}%)")
        print(f"   📊 Trades: {self.total_trades} | Wins: {self.wins} | Losses: {self.losses}")
        print(f"   💸 Total Fees: ${self.total_fees:.2f} | Net Profit: ${self.net_profit:+.2f}")
        
        # Show win rate status
        if self.total_trades >= 5:
            if win_rate >= 51:
                print(f"   ✅ WIN RATE TARGET MET: {win_rate:.1f}% >= 51%")
            else:
                print(f"   ⚠️ Win rate below target: {win_rate:.1f}% < 51%")
                
        if self.positions:
            print(f"   \n   📋 Open Positions ({len(self.positions)}):")
            for symbol, pos in self.positions.items():
                history = self.price_history.get(symbol, [])
                current = history[-1] if history else pos.entry_price
                pnl_pct = ((current - pos.entry_price) / pos.entry_price) * 100
                emoji = "🟢" if pnl_pct > 0 else "🔴"
                print(f"      {emoji} {symbol:12s} {pnl_pct:+.2f}% | Held: {pos.cycles_held} cycles")
        print()
        
    def run(self, cycles: int = 200, interval: float = 5.0):
        """Run the 51% profit machine"""
        self.banner()
        
        print("🎯 Connecting to Kraken...")
        if not self.update_tickers():
            print("❌ Failed to connect!")
            return
        print(f"✅ Connected! {len(self.ticker_cache)} pairs\n")
        
        try:
            for self.iteration in range(1, cycles + 1):
                print(f"{'━'*70}")
                print(f"🔄 Cycle {self.iteration}/{cycles} - {datetime.now().strftime('%H:%M:%S')}")
                print(f"{'━'*70}")
                
                # Update prices
                self.update_tickers()
                
                # Check positions for exits (THE PROFIT ENGINE)
                self.check_positions()
                
                # Find new opportunities
                candidates = self.find_opportunities()
                
                if candidates and len(self.positions) < MAX_POSITIONS:
                    print(f"\n   🔮 Top opportunities:")
                    for c in candidates[:3]:
                        print(f"      {c['symbol']:12s} +{c['momentum']:.1f}% | Score: {c['score']}")
                    self.enter_positions(candidates)
                    
                # Status every 10 cycles
                if self.iteration % 10 == 0:
                    self.print_status()
                else:
                    equity = self.get_equity()
                    win_rate = (self.wins / self.total_trades * 100) if self.total_trades > 0 else 0
                    print(f"\n   💎 ${equity:.2f} | Trades: {self.total_trades} | WR: {win_rate:.1f}%")
                    
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n🎯 Stopping...")
            
        self.final_report()
        
    def final_report(self):
        """Print final results"""
        equity = self.get_equity()
        net_pnl = equity - self.initial_balance
        win_rate = (self.wins / self.total_trades * 100) if self.total_trades > 0 else 0
        
        print()
        print("╔══════════════════════════════════════════════════════════════════════════╗")
        print("║                    🎯 AUREON 51% - FINAL REPORT 🎯                       ║")
        print("╚══════════════════════════════════════════════════════════════════════════╝")
        print()
        print(f"   Starting:     ${self.initial_balance:.2f}")
        print(f"   Final:        ${equity:.2f}")
        print(f"   💰 NET P&L:   ${net_pnl:+.2f} ({net_pnl/self.initial_balance*100:+.2f}%)")
        print()
        print(f"   Total Trades: {self.total_trades}")
        print(f"   Wins:         {self.wins}")
        print(f"   Losses:       {self.losses}")
        print(f"   🎯 WIN RATE:  {win_rate:.1f}%")
        print()
        print(f"   Gross Profit: ${self.gross_profit:+.2f}")
        print(f"   Total Fees:   ${self.total_fees:.2f}")
        print(f"   Net Profit:   ${self.net_profit:+.2f}")
        print()
        
        if win_rate >= 51 and self.net_profit > 0:
            print("   ✅ GOAL ACHIEVED: 51%+ Win Rate with NET PROFIT! ✅")
        elif win_rate >= 51:
            print("   ⚠️ Win rate good but need more profit margin")
        else:
            print("   ❌ Need to improve entry/exit strategy")
        print()


def main():
    cycles = int(os.getenv('CYCLES', '100'))
    interval = float(os.getenv('INTERVAL', '5'))
    balance = float(os.getenv('BALANCE', '1000'))
    
    trader = Aureon51(initial_balance=balance)
    trader.run(cycles=cycles, interval=interval)


if __name__ == '__main__':
    main()
