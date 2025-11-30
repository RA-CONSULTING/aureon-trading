#!/usr/bin/env python3
"""
🐙🔄 AUREON INFINITE - KRAKEN EDITION 🔄🐙
============================================
"If you don't quit, you can't lose"

10-9-1 QUEEN HIVE MODEL:
- Make profit on every trade
- 90% compounds back into the hive
- 10% harvests for new hives
- Never stops, always growing

KRAKEN ADAPTATION:
- Uses Kraken API instead of Binance
- USD pairs for maximum liquidity
- 0.26% taker fees factored in
- Momentum-based entry signals

FROM ATOM TO MULTIVERSE 🌌
We don't stop. We compound. We grow. We prove we're alive.

Gary Leckey & GitHub Copilot | November 2025
"""

import os
import sys
import time
import math
from datetime import datetime
from typing import Dict, List, Tuple, Optional

sys.path.insert(0, '/workspaces/aureon-trading')
from kraken_client import KrakenClient

# Trading parameters
MIN_TRADE_USD = 15.0          # Minimum trade size
TARGET_PROFIT_PCT = 0.8       # 0.8% profit target (higher to overcome fees)
STOP_LOSS_PCT = 0.5           # 0.5% stop loss
COMPOUND_PCT = 0.90           # 90% compounds
HARVEST_PCT = 0.10            # 10% harvests
MAX_POSITION_SIZE = 0.20      # Max 20% of capital per trade
MAX_POSITIONS = 5             # Maximum concurrent positions
KRAKEN_FEE = 0.0026           # 0.26% taker fee

# Performance tracker
class PerformanceTracker:
    def __init__(self):
        self.total_trades = 0
        self.profitable_trades = 0
        self.total_profit_usd = 0.0
        self.compounded_usd = 0.0
        self.harvested_usd = 0.0
        self.generation = 1
        self.start_capital = 0.0
        self.current_capital = 0.0
        self.total_fees = 0.0
        
    def record_trade(self, profit_usd: float, fees: float):
        """Record a trade result"""
        self.total_trades += 1
        self.total_fees += fees
        
        if profit_usd > 0:
            self.profitable_trades += 1
            net_profit = profit_usd - fees
            self.total_profit_usd += net_profit
            
            # 10-9-1: Compound 90%, Harvest 10%
            compound = net_profit * COMPOUND_PCT
            harvest = net_profit * HARVEST_PCT
            self.compounded_usd += compound
            self.harvested_usd += harvest
            
            print(f"      💰 Gross: ${profit_usd:.2f} | Fees: ${fees:.2f} | Net: ${net_profit:.2f}")
            print(f"      🔄 Compound: ${compound:.2f} | 🌱 Harvest: ${harvest:.2f}")
        else:
            loss = profit_usd - fees
            self.total_profit_usd += loss
            print(f"      😢 Loss: ${profit_usd:.2f} | Fees: ${fees:.2f} | Net: ${loss:.2f}")
    
    def display_stats(self):
        """Display performance statistics"""
        win_rate = (self.profitable_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        roi = ((self.current_capital - self.start_capital) / self.start_capital * 100) if self.start_capital > 0 else 0
        
        print(f"\n{'═'*70}")
        print(f"📊 PERFORMANCE STATISTICS - Generation {self.generation}")
        print(f"{'═'*70}")
        print(f"  Trades: {self.total_trades} | Win Rate: {win_rate:.1f}%")
        print(f"  Net Profit: ${self.total_profit_usd:.2f}")
        print(f"  Total Fees: ${self.total_fees:.2f}")
        print(f"  Compounded: ${self.compounded_usd:.2f} (90%)")
        print(f"  Harvested: ${self.harvested_usd:.2f} (10%)")
        if self.start_capital > 0:
            print(f"  ROI: {roi:+.2f}% | Growth: {self.current_capital / self.start_capital:.3f}x")
        print(f"{'═'*70}")


class Position:
    """Track an open position"""
    def __init__(self, symbol: str, entry_price: float, quantity: float, 
                 entry_fee: float, momentum: float):
        self.symbol = symbol
        self.entry_price = entry_price
        self.quantity = quantity
        self.entry_fee = entry_fee
        self.momentum = momentum
        self.entry_time = time.time()
        self.position_value = quantity * entry_price


class AureonInfiniteKraken:
    """
    🐙🔄 The Infinite Loop - Kraken Edition
    """
    
    def __init__(self, initial_balance: float = 1000.0, dry_run: bool = True):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.dry_run = dry_run
        self.client = KrakenClient()
        self.positions: Dict[str, Position] = {}
        self.tracker = PerformanceTracker()
        self.ticker_cache: Dict[str, Dict] = {}
        self.iteration = 0
        
        # Top momentum pairs to watch
        self.watchlist = []
        
    def banner(self):
        print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   🐙🔄 AUREON INFINITE - KRAKEN EDITION 🔄🐙                             ║
║                                                                          ║
║   "If you don't quit, you can't lose"                                   ║
║                                                                          ║
║   10-9-1 QUEEN HIVE MODEL:                                              ║
║   💰 Profit → 90% Compound + 10% Harvest                                ║
║                                                                          ║
║   🎯 TP: +0.8%  |  🛑 SL: -0.5%  |  💸 Fee: 0.26%                       ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
        """)
        mode = "🧪 PAPER TRADING" if self.dry_run else "💰 LIVE TRADING"
        print(f"   Mode: {mode}")
        print(f"   Starting Balance: ${self.initial_balance:.2f}")
        print(f"   Max Positions: {MAX_POSITIONS}")
        print()
        
    def update_tickers(self) -> bool:
        """Fetch latest Kraken tickers"""
        try:
            tickers = self.client.get_24h_tickers()
            self.ticker_cache.clear()
            
            for t in tickers:
                symbol = t.get('symbol', '')
                price = float(t.get('lastPrice', 0) or 0)
                change = float(t.get('priceChangePercent', 0) or 0)
                volume = float(t.get('quoteVolume', 0) or 0)
                
                if price > 0:
                    self.ticker_cache[symbol] = {
                        'price': price,
                        'change24h': change,
                        'volume': volume,
                    }
            return True
        except Exception as e:
            print(f"   ⚠️ Ticker update failed: {e}")
            return False
            
    def find_momentum_opportunities(self) -> List[Dict]:
        """Find coins with strong momentum - the juicy ones!"""
        candidates = []
        
        for symbol, data in self.ticker_cache.items():
            # Only USD pairs, skip stablecoins
            if not symbol.endswith('USD'):
                continue
            if symbol in ['USDCUSD', 'USDTUSD', 'DAIUSD', 'PAXUSD']:
                continue
            if symbol.endswith('USDT') or symbol.endswith('USDC'):
                continue
                
            change = data['change24h']
            price = data['price']
            volume = data['volume']
            
            # Strong positive momentum with decent volume
            if change > 5 and price > 0 and volume > 5000:
                # Calculate momentum score
                score = 50
                
                # Higher momentum = higher score
                if change > 30:
                    score += 30
                elif change > 20:
                    score += 25
                elif change > 10:
                    score += 15
                else:
                    score += 8
                    
                # Volume bonus
                if volume > 1000000:
                    score += 15
                elif volume > 100000:
                    score += 10
                elif volume > 10000:
                    score += 5
                    
                candidates.append({
                    'symbol': symbol,
                    'price': price,
                    'momentum': change,
                    'volume': volume,
                    'score': score,
                })
        
        # Sort by score
        candidates.sort(key=lambda x: x['score'], reverse=True)
        return candidates[:20]
        
    def check_positions(self):
        """Check existing positions for TP/SL"""
        closed = []
        
        for symbol, pos in list(self.positions.items()):
            ticker = self.ticker_cache.get(symbol, {})
            current_price = ticker.get('price', pos.entry_price)
            
            if current_price <= 0:
                continue
                
            pnl_pct = (current_price - pos.entry_price) / pos.entry_price * 100
            position_value = pos.quantity * current_price
            
            should_close = False
            result = ""
            
            # Take profit hit! 🎉
            if pnl_pct >= TARGET_PROFIT_PCT:
                should_close = True
                result = "WIN"
                emoji = "🎉"
                
            # Stop loss hit 😢
            elif pnl_pct <= -STOP_LOSS_PCT:
                should_close = True
                result = "LOSS"
                emoji = "😢"
                
            if should_close:
                # Calculate exit
                exit_fee = position_value * KRAKEN_FEE
                gross_pnl = (current_price - pos.entry_price) * pos.quantity
                total_fees = pos.entry_fee + exit_fee
                
                # Return position value to balance
                self.balance += position_value - exit_fee
                
                # Record trade
                self.tracker.record_trade(gross_pnl, total_fees)
                
                win_emoji = "✅" if result == "WIN" else "❌"
                print(f"   {emoji} CLOSE {symbol:12s} @ ${current_price:<10.6f} | "
                      f"{win_emoji} {result} ({pnl_pct:+.2f}%)")
                
                closed.append(symbol)
                
        # Remove closed positions
        for symbol in closed:
            del self.positions[symbol]
            
    def enter_positions(self, candidates: List[Dict]):
        """Enter new momentum positions"""
        if len(self.positions) >= MAX_POSITIONS:
            return
            
        available_slots = MAX_POSITIONS - len(self.positions)
        
        for candidate in candidates[:available_slots]:
            symbol = candidate['symbol']
            
            # Skip if already in position
            if symbol in self.positions:
                continue
                
            price = candidate['price']
            momentum = candidate['momentum']
            score = candidate['score']
            
            # Only take high-quality setups
            if score < 60:
                continue
            
            # Calculate position size
            position_usd = self.balance * MAX_POSITION_SIZE
            if position_usd < MIN_TRADE_USD:
                continue
                
            # Entry fee
            entry_fee = position_usd * KRAKEN_FEE
            quantity = (position_usd - entry_fee) / price
            
            # Deduct from balance
            self.balance -= position_usd
            
            # Create position
            self.positions[symbol] = Position(
                symbol=symbol,
                entry_price=price,
                quantity=quantity,
                entry_fee=entry_fee,
                momentum=momentum,
            )
            
            print(f"   🎯 BUY  {symbol:12s} @ ${price:<10.6f} | "
                  f"Size: ${position_usd:.2f} | Score: {score} | Mom: +{momentum:.1f}%")
                  
    def get_portfolio_value(self) -> float:
        """Calculate total portfolio value"""
        total = self.balance
        for symbol, pos in self.positions.items():
            ticker = self.ticker_cache.get(symbol, {})
            price = ticker.get('price', pos.entry_price)
            total += pos.quantity * price
        return total
        
    def print_status(self):
        """Print current status"""
        total_equity = self.get_portfolio_value()
        net_pnl = total_equity - self.initial_balance
        positions_value = sum(
            pos.quantity * self.ticker_cache.get(pos.symbol, {}).get('price', pos.entry_price)
            for pos in self.positions.values()
        )
        
        print()
        print(f"   {'═'*60}")
        print(f"   🐙 Iteration {self.iteration} Status")
        print(f"   {'═'*60}")
        print(f"   💰 Cash: ${self.balance:.2f} | Positions: ${positions_value:.2f}")
        print(f"   📊 Total Equity: ${total_equity:.2f}")
        print(f"   📈 Net P&L: ${net_pnl:+.2f} ({(net_pnl/self.initial_balance)*100:+.2f}%)")
        
        if self.positions:
            print(f"   \n   📋 Open Positions:")
            for symbol, pos in self.positions.items():
                current = self.ticker_cache.get(symbol, {}).get('price', pos.entry_price)
                pnl_pct = ((current - pos.entry_price) / pos.entry_price) * 100
                emoji = "🟢" if pnl_pct > 0 else "🔴"
                print(f"      {emoji} {symbol:12s} Entry: ${pos.entry_price:.6f} | "
                      f"Now: ${current:.6f} | P&L: {pnl_pct:+.2f}%")
        print()
        
    def run(self, interval: float = 5.0):
        """Run the infinite loop!"""
        self.banner()
        
        print("🐙 Connecting to Kraken...")
        if not self.update_tickers():
            print("❌ Failed to connect to Kraken!")
            return
        print(f"✅ Connected! {len(self.ticker_cache)} pairs available\n")
        
        # Initialize tracker
        self.tracker.start_capital = self.initial_balance
        self.tracker.current_capital = self.initial_balance
        
        try:
            while True:  # INFINITE!
                self.iteration += 1
                
                print(f"\n{'━'*70}")
                print(f"🔄 ITERATION {self.iteration} - {datetime.now().strftime('%H:%M:%S')}")
                print(f"{'━'*70}")
                
                # Update market data
                self.update_tickers()
                
                # Check existing positions for exits
                self.check_positions()
                
                # Find new momentum plays
                candidates = self.find_momentum_opportunities()
                
                if candidates:
                    print(f"\n   🔮 Found {len(candidates)} momentum candidates")
                    # Show top 3
                    for c in candidates[:3]:
                        print(f"      {c['symbol']:12s} +{c['momentum']:.1f}% | Score: {c['score']}")
                
                # Enter new positions if we have cash
                if self.balance >= MIN_TRADE_USD:
                    self.enter_positions(candidates)
                    
                # Update tracker
                self.tracker.current_capital = self.get_portfolio_value()
                
                # Print status every 10 iterations
                if self.iteration % 10 == 0:
                    self.print_status()
                    self.tracker.display_stats()
                else:
                    total = self.get_portfolio_value()
                    print(f"\n   💎 Equity: ${total:.2f} | Trades: {self.tracker.total_trades} | "
                          f"Wins: {self.tracker.profitable_trades}")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n🐙 Stopping gracefully...")
            self.tracker.display_stats()
            
    def final_summary(self):
        """Print final summary"""
        total_equity = self.get_portfolio_value()
        net_pnl = total_equity - self.initial_balance
        
        print()
        print("╔══════════════════════════════════════════════════════════════════════════╗")
        print("║            🐙🔄 AUREON INFINITE - FINAL REPORT 🔄🐙                      ║")
        print("╚══════════════════════════════════════════════════════════════════════════╝")
        print()
        print(f"   Starting Balance:  ${self.initial_balance:.2f}")
        print(f"   Final Equity:      ${total_equity:.2f}")
        print(f"   💰 NET PROFIT:     ${net_pnl:+.2f} ({(net_pnl/self.initial_balance)*100:+.2f}%)")
        print()
        self.tracker.display_stats()


def main():
    # Check for dry run mode
    dry_run = os.getenv('DRY_RUN', 'true').lower() == 'true'
    initial_balance = float(os.getenv('INITIAL_BALANCE', '1000'))
    interval = float(os.getenv('INTERVAL', '5'))
    
    infinite = AureonInfiniteKraken(
        initial_balance=initial_balance,
        dry_run=dry_run,
    )
    
    infinite.run(interval=interval)


if __name__ == '__main__':
    main()
