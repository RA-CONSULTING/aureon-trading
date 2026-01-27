#!/usr/bin/env python3
"""
🦆⚡ QUANTUM QUACKERS - KRAKEN MOMENTUM TRADER ⚡🦆
===================================================
The duckiest momentum trader in the Kraken pond!

Strategy: Ride the wave on coins with strong 24h momentum
- Entry: 24h change > 5% (duck sees the wave forming)
- Take Profit: 3% gain (quack quack, bag secured!)
- Stop Loss: 2% (duck knows when to fly away)
- Position Size: 12% of balance per trade
- Max Positions: 5 concurrent ducks in the water

Features:
- Real Kraken market data
- Full fee tracking (0.70% combined: fee + slippage + spread)
- Net profit optimization with CORRECT penny profit math
- Live portfolio tracking
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
import time
import json
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import random

sys.path.insert(0, '/workspaces/aureon-trading')
from kraken_client import KrakenClient

# =============================================================================
# CONFIGURATION - CORRECTED FEE MODEL (matches penny profit formula)
# =============================================================================
KRAKEN_FEE_RATE = 0.004      # 0.40% taker fee
SLIPPAGE_PCT = 0.002         # 0.20% slippage  
SPREAD_COST_PCT = 0.001      # 0.10% spread
TOTAL_COST_RATE = KRAKEN_FEE_RATE + SLIPPAGE_PCT + SPREAD_COST_PCT  # 0.70% per leg

# Legacy compatibility - use combined rate everywhere
TAKER_FEE = TOTAL_COST_RATE

# Quacker Config
MOMENTUM_THRESHOLD = 0.05  # 5% 24h change to enter
TAKE_PROFIT = 0.03         # 3% profit target
STOP_LOSS = 0.02           # 2% stop loss
POSITION_SIZE = 0.12       # 12% of balance per trade
MAX_POSITIONS = 5          # Max concurrent positions

@dataclass
class QuackerPosition:
    symbol: str
    entry_price: float
    quantity: float
    entry_time: float
    entry_fee: float
    momentum: float  # The 24h change when we entered

@dataclass
class QuackerTrade:
    symbol: str
    side: str
    entry_price: float
    exit_price: float
    quantity: float
    gross_pnl: float
    fees: float
    net_pnl: float
    hold_time_sec: float
    momentum: float
    result: str  # WIN or LOSS

class QuantumQuackers:
    """🦆 The Quantum Quacker - Kraken Momentum Hunter 🦆"""
    
    def __init__(self, initial_balance: float = 1000.0, dry_run: bool = True):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.dry_run = dry_run
        self.positions: Dict[str, QuackerPosition] = {}
        self.trades: List[QuackerTrade] = []
        self.total_fees = 0.0
        self.peak_balance = initial_balance
        self.max_drawdown = 0.0
        
        # Kraken client
        self.client = KrakenClient()
        self.ticker_cache: Dict[str, Dict] = {}
        
        # Stats
        self.wins = 0
        self.losses = 0
        self.cycle = 0
        
    def quack_banner(self):
        print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   🦆⚡ QUANTUM QUACKERS - KRAKEN MOMENTUM TRADER ⚡🦆                     ║
║                                                                          ║
║   "If it quacks like profit, it IS profit!"                             ║
║                                                                          ║
║   Strategy: MOMENTUM SURFING                                             ║
║   Entry: 24h change > 5%  |  TP: +3%  |  SL: -2%                        ║
║   Position Size: 12%  |  Max Positions: 5                               ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
        """)
        mode = "🧪 PAPER TRADING" if self.dry_run else "💰 LIVE TRADING"
        print(f"   Mode: {mode}")
        print(f"   Starting Balance: ${self.initial_balance:.2f}")
        print(f"   Kraken Fee: {TAKER_FEE*100:.2f}% per trade")
        print()
        
    def update_tickers(self):
        """Fetch latest Kraken tickers"""
        try:
            tickers = self.client.get_24h_tickers()
            for t in tickers:
                symbol = t.get('symbol', '')
                self.ticker_cache[symbol] = {
                    'price': float(t.get('lastPrice', 0) or 0),
                    'change24h': float(t.get('priceChangePercent', 0) or 0),
                    'volume': float(t.get('quoteVolume', 0) or 0),
                }
            return True
        except Exception as e:
            print(f"   ⚠️ Ticker update failed: {e}")
            return False
            
    def find_momentum_ducks(self) -> List[Dict]:
        """Find coins with strong momentum - the juicy ducks!"""
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
            if change > MOMENTUM_THRESHOLD * 100 and price > 0 and volume > 1000:
                candidates.append({
                    'symbol': symbol,
                    'price': price,
                    'momentum': change,
                    'volume': volume,
                })
        
        # Sort by momentum strength
        candidates.sort(key=lambda x: x['momentum'], reverse=True)
        return candidates[:20]  # Top 20 momentum plays
        
    def check_positions(self):
        """Check existing positions for TP/SL"""
        closed = []
        for symbol, pos in list(self.positions.items()):
            ticker = self.ticker_cache.get(symbol, {})
            current_price = ticker.get('price', pos.entry_price)
            
            if current_price <= 0:
                continue
                
            pnl_pct = (current_price - pos.entry_price) / pos.entry_price
            position_value = pos.quantity * current_price
            
            should_close = False
            result = ""
            
            # Take profit hit! 🎉
            if pnl_pct >= TAKE_PROFIT:
                should_close = True
                result = "WIN"
                emoji = "🎉"
                
            # Stop loss hit 😢
            elif pnl_pct <= -STOP_LOSS:
                should_close = True
                result = "LOSS"
                emoji = "😢"
                
            if should_close:
                # Calculate exit
                exit_fee = position_value * TAKER_FEE
                gross_pnl = (current_price - pos.entry_price) * pos.quantity
                net_pnl = gross_pnl - pos.entry_fee - exit_fee
                total_fees = pos.entry_fee + exit_fee
                
                self.balance += position_value - exit_fee
                self.total_fees += exit_fee
                
                # Track peak/drawdown
                if self.balance > self.peak_balance:
                    self.peak_balance = self.balance
                drawdown = (self.peak_balance - self.balance) / self.peak_balance
                if drawdown > self.max_drawdown:
                    self.max_drawdown = drawdown
                
                # Record trade
                trade = QuackerTrade(
                    symbol=symbol,
                    side='SELL',
                    entry_price=pos.entry_price,
                    exit_price=current_price,
                    quantity=pos.quantity,
                    gross_pnl=gross_pnl,
                    fees=total_fees,
                    net_pnl=net_pnl,
                    hold_time_sec=time.time() - pos.entry_time,
                    momentum=pos.momentum,
                    result=result,
                )
                self.trades.append(trade)
                
                if result == "WIN":
                    self.wins += 1
                else:
                    self.losses += 1
                    
                win_emoji = "✅" if result == "WIN" else "❌"
                print(f"   🦆 CLOSE {symbol:12s} @ ${current_price:<10.6f} | "
                      f"Net: ${net_pnl:+8.2f} | Fees: ${total_fees:.2f} | "
                      f"{win_emoji} {result} ({pnl_pct*100:+.1f}%)")
                
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
            
            # Calculate position size
            position_usd = self.balance * POSITION_SIZE
            if position_usd < 10:  # Minimum $10 position
                continue
                
            # Entry fee
            entry_fee = position_usd * TAKER_FEE
            quantity = (position_usd - entry_fee) / price
            
            # Deduct from balance
            self.balance -= position_usd
            self.total_fees += entry_fee
            
            # Create position
            self.positions[symbol] = QuackerPosition(
                symbol=symbol,
                entry_price=price,
                quantity=quantity,
                entry_time=time.time(),
                entry_fee=entry_fee,
                momentum=momentum,
            )
            
            print(f"   🦆 BUY  {symbol:12s} @ ${price:<10.6f} | "
                  f"Size: ${position_usd:.2f} | Fee: ${entry_fee:.2f} | "
                  f"Momentum: +{momentum:.1f}%")
                  
    def print_status(self):
        """Print current quacker status"""
        total_position_value = sum(
            pos.quantity * self.ticker_cache.get(pos.symbol, {}).get('price', pos.entry_price)
            for pos in self.positions.values()
        )
        total_equity = self.balance + total_position_value
        net_pnl = total_equity - self.initial_balance
        win_rate = (self.wins / (self.wins + self.losses) * 100) if (self.wins + self.losses) > 0 else 0
        
        print()
        print(f"   {'='*60}")
        print(f"   🦆 Cycle {self.cycle} Status")
        print(f"   {'='*60}")
        print(f"   💰 Balance: ${self.balance:.2f} | Positions: ${total_position_value:.2f}")
        print(f"   📊 Total Equity: ${total_equity:.2f}")
        print(f"   📈 Net P&L: ${net_pnl:+.2f} ({(net_pnl/self.initial_balance)*100:+.1f}%)")
        print(f"   🎯 Trades: {len(self.trades)} | Wins: {self.wins} | Losses: {self.losses} | Win Rate: {win_rate:.1f}%")
        print(f"   💸 Total Fees Paid: ${self.total_fees:.2f}")
        print(f"   📉 Max Drawdown: {self.max_drawdown*100:.1f}%")
        
        if self.positions:
            print(f"   \n   📋 Open Positions:")
            for symbol, pos in self.positions.items():
                current = self.ticker_cache.get(symbol, {}).get('price', pos.entry_price)
                pnl_pct = ((current - pos.entry_price) / pos.entry_price) * 100
                emoji = "🟢" if pnl_pct > 0 else "🔴"
                print(f"      {emoji} {symbol:12s} Entry: ${pos.entry_price:.6f} | "
                      f"Now: ${current:.6f} | P&L: {pnl_pct:+.2f}%")
        print()
        
    def run(self, cycles: int = 100, interval: float = 5.0):
        """Run the Quantum Quacker!"""
        self.quack_banner()
        
        print("🦆 Connecting to Kraken pond...")
        if not self.update_tickers():
            print("❌ Failed to connect to Kraken!")
            return
        print(f"✅ Connected! {len(self.ticker_cache)} pairs in the pond\n")
        
        try:
            for self.cycle in range(1, cycles + 1):
                # Update market data
                self.update_tickers()
                
                # Check existing positions for exits
                self.check_positions()
                
                # Find new momentum plays
                candidates = self.find_momentum_ducks()
                
                # Enter new positions
                if candidates:
                    self.enter_positions(candidates)
                    
                # Print status every 10 cycles
                if self.cycle % 10 == 0:
                    self.print_status()
                    
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n🦆 Quacker interrupted! Waddle waddle...")
            
        # Final summary
        self.final_summary()
        
    def final_summary(self):
        """Print final quacker summary"""
        total_position_value = sum(
            pos.quantity * self.ticker_cache.get(pos.symbol, {}).get('price', pos.entry_price)
            for pos in self.positions.values()
        )
        total_equity = self.balance + total_position_value
        net_pnl = total_equity - self.initial_balance
        win_rate = (self.wins / (self.wins + self.losses) * 100) if (self.wins + self.losses) > 0 else 0
        
        print()
        print("╔══════════════════════════════════════════════════════════════════════════╗")
        print("║               🦆⚡ QUANTUM QUACKERS FINAL REPORT ⚡🦆                     ║")
        print("╚══════════════════════════════════════════════════════════════════════════╝")
        print()
        print(f"   Starting Balance:  ${self.initial_balance:.2f}")
        print(f"   Final Equity:      ${total_equity:.2f}")
        print(f"   💰 NET PROFIT:     ${net_pnl:+.2f} ({(net_pnl/self.initial_balance)*100:+.1f}%)")
        print()
        print(f"   Total Trades:      {len(self.trades)}")
        print(f"   Wins:              {self.wins}")
        print(f"   Losses:            {self.losses}")
        print(f"   Win Rate:          {win_rate:.1f}%")
        print(f"   Total Fees:        ${self.total_fees:.2f}")
        print(f"   Max Drawdown:      {self.max_drawdown*100:.1f}%")
        print()
        
        if net_pnl > 0:
            print("   🎉 QUACK QUACK! The duck made profit! 🎉")
        else:
            print("   😢 The duck needs a better pond...")
        print()


def main():
    # Check for dry run mode
    dry_run = os.getenv('DRY_RUN', 'true').lower() == 'true'
    initial_balance = float(os.getenv('INITIAL_BALANCE', '1000'))
    cycles = int(os.getenv('CYCLES', '100'))
    interval = float(os.getenv('INTERVAL', '5'))
    
    quacker = QuantumQuackers(
        initial_balance=initial_balance,
        dry_run=dry_run,
    )
    
    quacker.run(cycles=cycles, interval=interval)


if __name__ == '__main__':
    main()
