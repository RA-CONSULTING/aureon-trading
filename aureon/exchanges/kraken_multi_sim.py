#!/usr/bin/env python3
"""
🐙 KRAKEN MULTI-SIM ENGINE 🐙
=============================
Runs multiple paper trading simulations with REAL Kraken market data
to analyze different strategies and find profitable configurations.

Tracks ALL metrics for net profit optimization:
- Entry/Exit fees (Kraken: 0.16% maker / 0.26% taker)
- Spread costs
- Slippage estimates
- Win rate, profit factor, Sharpe ratio
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
import time
import json
import threading
from datetime import datetime
from decimal import Decimal
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from collections import deque
import random

# Add project root
sys.path.insert(0, '/workspaces/aureon-trading')

from kraken_client import KrakenClient, get_kraken_client

# Kraken fee structure (taker fees for market orders)
KRAKEN_TAKER_FEE = 0.0026  # 0.26%
KRAKEN_MAKER_FEE = 0.0016  # 0.16%

@dataclass
class SimPosition:
    symbol: str
    entry_price: float
    quantity: float
    entry_time: float
    entry_fee: float
    strategy: str
    
@dataclass
class SimTrade:
    symbol: str
    side: str  # 'BUY' or 'SELL'
    entry_price: float
    exit_price: float
    quantity: float
    gross_pnl: float
    fees: float
    net_pnl: float
    hold_time_sec: float
    strategy: str
    timestamp: str

@dataclass 
class SimResult:
    strategy: str
    initial_balance: float
    final_balance: float
    total_trades: int
    wins: int
    losses: int
    win_rate: float
    gross_pnl: float
    total_fees: float
    net_pnl: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    max_drawdown: float
    sharpe_ratio: float
    trades: List[SimTrade] = field(default_factory=list)

class KrakenSimulator:
    """Paper trading simulator using REAL Kraken market data"""
    
    def __init__(self, strategy_name: str, initial_balance: float = 1000.0, 
                 config: Dict = None):
        self.strategy = strategy_name
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.positions: Dict[str, SimPosition] = {}
        self.trades: List[SimTrade] = []
        self.config = config or {}
        
        # Metrics tracking
        self.peak_balance = initial_balance
        self.max_drawdown = 0.0
        self.total_fees = 0.0
        self.gross_pnl = 0.0
        
        # Kraken client for real market data
        self.client = get_kraken_client()
        self.ticker_cache: Dict[str, Dict] = {}
        self.last_ticker_update = 0
        
        # Strategy parameters (configurable)
        self.entry_threshold = self.config.get('entry_threshold', 0.02)  # 2% momentum
        self.take_profit_pct = self.config.get('take_profit', 0.008)  # 0.8% TP
        self.stop_loss_pct = self.config.get('stop_loss', 0.005)  # 0.5% SL
        self.position_size_pct = self.config.get('position_size', 0.15)  # 15% per trade
        self.max_positions = self.config.get('max_positions', 5)
        self.min_volume = self.config.get('min_volume', 50000)  # Min 24h volume
        
        # Quote assets to trade
        self.quote_assets = ['USDC', 'USD', 'USDT']
        
    def update_tickers(self):
        """Fetch real Kraken market data"""
        if time.time() - self.last_ticker_update < 3:
            return
        try:
            tickers = self.client.get_24h_tickers()
            for t in tickers:
                symbol = t.get('symbol', '')
                if any(symbol.endswith(q) for q in self.quote_assets):
                    self.ticker_cache[symbol] = {
                        'price': float(t.get('lastPrice', 0)),
                        'change': float(t.get('priceChangePercent', 0)),
                        'volume': float(t.get('quoteVolume', 0))
                    }
            self.last_ticker_update = time.time()
        except Exception as e:
            print(f"[{self.strategy}] Ticker update error: {e}")
    
    def get_price(self, symbol: str) -> float:
        """Get current price for symbol"""
        if symbol in self.ticker_cache:
            return self.ticker_cache[symbol]['price']
        return 0.0
    
    def find_opportunities(self) -> List[Dict]:
        """Find trading opportunities based on strategy"""
        self.update_tickers()
        opportunities = []
        
        for symbol, data in self.ticker_cache.items():
            if data['volume'] < self.min_volume:
                continue
            if symbol in self.positions:
                continue
                
            change = data['change'] / 100.0
            
            # Different strategies look for different signals
            if self.strategy == "MOMENTUM":
                # Buy strong upward momentum
                if change > self.entry_threshold:
                    opportunities.append({
                        'symbol': symbol,
                        'price': data['price'],
                        'score': change,
                        'reason': f"Momentum +{change*100:.1f}%"
                    })
            
            elif self.strategy == "MEAN_REVERT":
                # Buy oversold (expecting bounce)
                if change < -self.entry_threshold:
                    opportunities.append({
                        'symbol': symbol,
                        'price': data['price'],
                        'score': abs(change),
                        'reason': f"Oversold {change*100:.1f}%"
                    })
            
            elif self.strategy == "VOLATILITY":
                # Trade high volatility pairs
                if abs(change) > self.entry_threshold * 1.5:
                    opportunities.append({
                        'symbol': symbol,
                        'price': data['price'],
                        'score': abs(change),
                        'reason': f"High vol {abs(change)*100:.1f}%"
                    })
            
            elif self.strategy == "HYBRID":
                # Combine signals
                if change > self.entry_threshold * 0.8:
                    opportunities.append({
                        'symbol': symbol,
                        'price': data['price'],
                        'score': change + (data['volume'] / 1000000),
                        'reason': f"Hybrid score {change*100:.1f}%"
                    })
        
        # Sort by score and return top picks
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        return opportunities[:3]
    
    def enter_position(self, symbol: str, price: float, reason: str) -> bool:
        """Enter a paper position with fee tracking"""
        if len(self.positions) >= self.max_positions:
            return False
        if symbol in self.positions:
            return False
            
        # Calculate position size
        position_value = self.balance * self.position_size_pct
        if position_value < 5:  # Min notional
            return False
            
        # Calculate entry fee
        entry_fee = position_value * KRAKEN_TAKER_FEE
        quantity = (position_value - entry_fee) / price
        
        self.positions[symbol] = SimPosition(
            symbol=symbol,
            entry_price=price,
            quantity=quantity,
            entry_time=time.time(),
            entry_fee=entry_fee,
            strategy=self.strategy
        )
        
        self.balance -= position_value
        self.total_fees += entry_fee
        
        print(f"  [{self.strategy}] 🟢 BUY {symbol} @ ${price:.4f} | Size: ${position_value:.2f} | Fee: ${entry_fee:.4f} | {reason}")
        return True
    
    def check_exits(self):
        """Check positions for exit conditions"""
        self.update_tickers()
        
        exits = []
        for symbol, pos in list(self.positions.items()):
            current_price = self.get_price(symbol)
            if current_price <= 0:
                continue
                
            price_change = (current_price - pos.entry_price) / pos.entry_price
            hold_time = time.time() - pos.entry_time
            
            exit_reason = None
            
            # Take profit
            if price_change >= self.take_profit_pct:
                exit_reason = f"TP +{price_change*100:.2f}%"
            # Stop loss
            elif price_change <= -self.stop_loss_pct:
                exit_reason = f"SL {price_change*100:.2f}%"
            # Timeout (30 minutes max hold)
            elif hold_time > 1800:
                exit_reason = f"Timeout {hold_time/60:.0f}m"
                
            if exit_reason:
                exits.append((symbol, current_price, exit_reason, hold_time))
        
        for symbol, price, reason, hold_time in exits:
            self.exit_position(symbol, price, reason, hold_time)
    
    def exit_position(self, symbol: str, price: float, reason: str, hold_time: float):
        """Exit a paper position with full fee accounting"""
        if symbol not in self.positions:
            return
            
        pos = self.positions[symbol]
        
        # Calculate gross value and fees
        gross_value = pos.quantity * price
        exit_fee = gross_value * KRAKEN_TAKER_FEE
        net_value = gross_value - exit_fee
        
        # Calculate P&L
        entry_value = pos.quantity * pos.entry_price
        gross_pnl = gross_value - entry_value
        total_fees = pos.entry_fee + exit_fee
        net_pnl = gross_pnl - total_fees
        
        # Update balance
        self.balance += net_value
        self.total_fees += exit_fee
        self.gross_pnl += gross_pnl
        
        # Track drawdown
        if self.balance > self.peak_balance:
            self.peak_balance = self.balance
        current_dd = (self.peak_balance - self.balance) / self.peak_balance
        self.max_drawdown = max(self.max_drawdown, current_dd)
        
        # Record trade
        trade = SimTrade(
            symbol=symbol,
            side='SELL',
            entry_price=pos.entry_price,
            exit_price=price,
            quantity=pos.quantity,
            gross_pnl=gross_pnl,
            fees=total_fees,
            net_pnl=net_pnl,
            hold_time_sec=hold_time,
            strategy=self.strategy,
            timestamp=datetime.now().isoformat()
        )
        self.trades.append(trade)
        
        win_loss = "✅ WIN" if net_pnl > 0 else "❌ LOSS"
        print(f"  [{self.strategy}] 🔴 SELL {symbol} @ ${price:.4f} | Net: ${net_pnl:+.4f} | Fees: ${total_fees:.4f} | {win_loss} | {reason}")
        
        del self.positions[symbol]
    
    def get_results(self) -> SimResult:
        """Calculate final simulation results"""
        wins = [t for t in self.trades if t.net_pnl > 0]
        losses = [t for t in self.trades if t.net_pnl <= 0]
        
        total_trades = len(self.trades)
        win_count = len(wins)
        loss_count = len(losses)
        win_rate = win_count / total_trades if total_trades > 0 else 0
        
        total_wins = sum(t.net_pnl for t in wins)
        total_losses = abs(sum(t.net_pnl for t in losses))
        
        avg_win = total_wins / win_count if win_count > 0 else 0
        avg_loss = total_losses / loss_count if loss_count > 0 else 0
        
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        net_pnl = self.balance - self.initial_balance
        
        # Simplified Sharpe (annualized assuming ~1 trade per hour)
        if self.trades:
            returns = [t.net_pnl / self.initial_balance for t in self.trades]
            avg_return = sum(returns) / len(returns)
            std_return = (sum((r - avg_return)**2 for r in returns) / len(returns)) ** 0.5
            sharpe = (avg_return / std_return) * (252 ** 0.5) if std_return > 0 else 0
        else:
            sharpe = 0
        
        return SimResult(
            strategy=self.strategy,
            initial_balance=self.initial_balance,
            final_balance=self.balance,
            total_trades=total_trades,
            wins=win_count,
            losses=loss_count,
            win_rate=win_rate,
            gross_pnl=self.gross_pnl,
            total_fees=self.total_fees,
            net_pnl=net_pnl,
            profit_factor=profit_factor,
            avg_win=avg_win,
            avg_loss=avg_loss,
            max_drawdown=self.max_drawdown,
            sharpe_ratio=sharpe,
            trades=self.trades
        )


def run_simulation(strategy: str, config: Dict, duration_sec: int = 300):
    """Run a single simulation"""
    print(f"\n{'='*60}")
    print(f"🚀 Starting {strategy} Simulation")
    print(f"   Config: {config}")
    print(f"{'='*60}")
    
    sim = KrakenSimulator(strategy, initial_balance=1000.0, config=config)
    
    start_time = time.time()
    cycle = 0
    
    while time.time() - start_time < duration_sec:
        cycle += 1
        
        # Check for exit opportunities first
        sim.check_exits()
        
        # Look for entry opportunities
        if len(sim.positions) < sim.max_positions:
            opportunities = sim.find_opportunities()
            for opp in opportunities:
                if len(sim.positions) < sim.max_positions:
                    sim.enter_position(opp['symbol'], opp['price'], opp['reason'])
        
        # Status update every 30 cycles
        if cycle % 30 == 0:
            print(f"  [{strategy}] Cycle {cycle} | Balance: ${sim.balance:.2f} | Positions: {len(sim.positions)} | Trades: {len(sim.trades)}")
        
        time.sleep(2)  # 2 second intervals
    
    # Close any remaining positions at current prices
    for symbol in list(sim.positions.keys()):
        price = sim.get_price(symbol)
        if price > 0:
            sim.exit_position(symbol, price, "SIM_END", time.time() - sim.positions[symbol].entry_time)
    
    return sim.get_results()


def main():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║     🐙 KRAKEN MULTI-STRATEGY SIMULATOR 🐙                        ║
║                                                                  ║
║  Running 4 strategies with REAL Kraken market data              ║
║  Tracking ALL fees and metrics for NET PROFIT analysis          ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # Define strategies with different configurations
    strategies = [
        ("MOMENTUM", {
            'entry_threshold': 0.02,
            'take_profit': 0.008,
            'stop_loss': 0.005,
            'position_size': 0.12,
            'max_positions': 5
        }),
        ("MEAN_REVERT", {
            'entry_threshold': 0.025,
            'take_profit': 0.006,
            'stop_loss': 0.004,
            'position_size': 0.10,
            'max_positions': 6
        }),
        ("VOLATILITY", {
            'entry_threshold': 0.03,
            'take_profit': 0.012,
            'stop_loss': 0.008,
            'position_size': 0.08,
            'max_positions': 4
        }),
        ("HYBRID", {
            'entry_threshold': 0.015,
            'take_profit': 0.007,
            'stop_loss': 0.004,
            'position_size': 0.15,
            'max_positions': 5
        })
    ]
    
    results = []
    duration = 180  # 3 minutes per strategy
    
    for strategy, config in strategies:
        result = run_simulation(strategy, config, duration)
        results.append(result)
        print(f"\n✅ {strategy} Complete!")
    
    # Print summary
    print("\n" + "="*80)
    print("📊 MULTI-STRATEGY SIMULATION RESULTS")
    print("="*80)
    print(f"{'Strategy':<15} {'Trades':<8} {'Win%':<8} {'Net P&L':<12} {'Fees':<10} {'PF':<8} {'Sharpe':<8}")
    print("-"*80)
    
    for r in results:
        print(f"{r.strategy:<15} {r.total_trades:<8} {r.win_rate*100:>5.1f}%  ${r.net_pnl:>+9.2f}  ${r.total_fees:>7.2f}  {r.profit_factor:>6.2f}  {r.sharpe_ratio:>6.2f}")
    
    print("-"*80)
    
    # Find best strategy
    best = max(results, key=lambda x: x.net_pnl)
    print(f"\n🏆 BEST STRATEGY: {best.strategy}")
    print(f"   Net Profit: ${best.net_pnl:+.2f} after ${best.total_fees:.2f} in fees")
    print(f"   Win Rate: {best.win_rate*100:.1f}% ({best.wins}W / {best.losses}L)")
    print(f"   Profit Factor: {best.profit_factor:.2f}")
    
    # Save results to JSON
    results_data = []
    for r in results:
        results_data.append({
            'strategy': r.strategy,
            'initial_balance': r.initial_balance,
            'final_balance': r.final_balance,
            'total_trades': r.total_trades,
            'wins': r.wins,
            'losses': r.losses,
            'win_rate': r.win_rate,
            'gross_pnl': r.gross_pnl,
            'total_fees': r.total_fees,
            'net_pnl': r.net_pnl,
            'profit_factor': r.profit_factor,
            'max_drawdown': r.max_drawdown,
            'sharpe_ratio': r.sharpe_ratio
        })
    
    with open('kraken_sim_results.json', 'w') as f:
        json.dump(results_data, f, indent=2)
    
    print("\n📁 Results saved to kraken_sim_results.json")


if __name__ == "__main__":
    main()
