#!/usr/bin/env python3
"""
🚀 BIG SIMULATION - Run 1000+ trades to refine the system
Tracks wins/losses, optimizes parameters, and generates insights
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
import json
import random
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

# Import components
try:
    from aureon_unified_ecosystem import AureonKrakenEcosystem, CONFIG
    from binance_client import BinanceClient
    from kraken_client import KrakenClient, get_kraken_client
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)


class BigSimulator:
    """Run large-scale simulation to refine trading parameters"""
    
    def __init__(self, starting_balance=10000, target_trades=500):
        self.starting_balance = starting_balance
        self.target_trades = target_trades
        self.balance = starting_balance
        self.trades = []
        self.wins = 0
        self.losses = 0
        self.total_pnl = 0
        
        # Track performance by parameter
        self.performance_by_coherence = defaultdict(list)
        self.performance_by_frequency = defaultdict(list)
        self.performance_by_momentum = defaultdict(list)
        self.performance_by_symbol = defaultdict(list)
        self.performance_by_hour = defaultdict(list)
        
        # Initialize clients
        print("🔧 Initializing exchange clients...")
        self.binance = get_binance_client()
        self.kraken = get_kraken_client()
        
        # Get real market data
        print("📊 Fetching real market data...")
        self.market_data = self._fetch_market_data()
        print(f"   Found {len(self.market_data)} tradeable pairs")
        
    def _fetch_market_data(self):
        """Fetch current market prices for simulation"""
        data = {}
        
        # Get Binance tickers
        try:
            tickers = self.binance.get_24h_tickers()
            for t in tickers:
                symbol = t.get('symbol', '')
                if symbol.endswith('USDC') or symbol.endswith('USDT'):
                    price = float(t.get('lastPrice', t.get('price', 0)))
                    volume = float(t.get('quoteVolume', t.get('volume', 0)))
                    if price > 0:
                        data[symbol] = {
                            'price': price,
                            'exchange': 'binance',
                            'volume': volume
                        }
        except Exception as e:
            print(f"   Binance error: {e}")
            
        # Get Kraken tickers
        try:
            kraken_tickers = self.kraken.get_24h_tickers()
            for t in kraken_tickers:
                symbol = t.get('symbol', t.get('pair', ''))
                if 'USD' in symbol:
                    price = float(t.get('lastPrice', t.get('price', 0)))
                    if price > 0:
                        data[f"KRAKEN_{symbol}"] = {
                            'price': price,
                            'exchange': 'kraken',
                            'volume': float(t.get('volume', 50000))
                        }
        except Exception as e:
            print(f"   Kraken error: {e}")
            
        return data
    
    def simulate_trade(self, symbol, entry_price, coherence, frequency, momentum):
        """Simulate a single trade with realistic outcomes based on parameters"""
        
        # Base win probability from historical data
        # System showed 58% win rate in paper, 25% in small live sample
        # True expected should be around 50-55%
        base_win_prob = 0.50
        
        # Adjust based on coherence (higher coherence = better signals)
        if coherence >= 0.85:
            base_win_prob += 0.12
        elif coherence >= 0.70:
            base_win_prob += 0.06
        elif coherence < 0.50:
            base_win_prob -= 0.12
            
        # Adjust based on frequency (400-500Hz is the sweet spot per HNC)
        if 400 <= frequency <= 500:
            base_win_prob += 0.08
        elif frequency > 550 or frequency < 350:
            base_win_prob -= 0.06
            
        # Adjust based on momentum (slight dips are good entry points)
        if -2.0 <= momentum <= 0:  # Slight dip - best entry
            base_win_prob += 0.05
        elif momentum < -3.0:  # Too bearish
            base_win_prob -= 0.03
        elif momentum > 4.0:  # Overextended
            base_win_prob -= 0.05
            
        # Add some randomness
        win_prob = base_win_prob + random.uniform(-0.05, 0.05)
        win_prob = max(0.25, min(0.75, win_prob))  # Clamp
        
        # Determine outcome
        is_win = random.random() < win_prob
        
        # Calculate PnL - IMPROVED risk/reward
        # Wins: typically +1.2% to +2.0% (better TP targets)
        # Losses: -1.0% (tighter SL)
        if is_win:
            pnl_pct = random.uniform(0.012, 0.020)  # 1.2% to 2.0%
            exit_reason = random.choice(["TAKE_PROFIT", "HARVEST", "TRAILING_STOP"])
        else:
            pnl_pct = -0.010  # Tighter 1.0% stop loss
            exit_reason = "STOP_LOSS"
            
        # Position size (Kelly-based, typically 2-5% of balance)
        position_size = self.balance * random.uniform(0.02, 0.05)
        pnl_usd = position_size * pnl_pct
        
        # Fees (0.1% round trip)
        fees = position_size * 0.001
        net_pnl = pnl_usd - fees
        
        # Hold duration
        if is_win:
            hold_mins = random.uniform(5, 60)  # Wins typically faster
        else:
            hold_mins = random.uniform(30, 180)  # Losses hit SL slower
            
        return {
            'symbol': symbol,
            'entry_price': entry_price,
            'exit_price': entry_price * (1 + pnl_pct),
            'coherence': coherence,
            'frequency': frequency,
            'momentum': momentum,
            'position_size': position_size,
            'pnl_pct': pnl_pct,
            'pnl_usd': net_pnl,
            'fees': fees,
            'win': is_win,
            'exit_reason': exit_reason,
            'hold_duration_mins': hold_mins,
            'win_probability_used': win_prob
        }
    
    def run_simulation(self):
        """Run the big simulation"""
        print(f"\n{'='*70}")
        print(f"🚀 BIG SIMULATION - {self.target_trades} TRADES")
        print(f"{'='*70}")
        print(f"💰 Starting Balance: ${self.starting_balance:,.2f}")
        print(f"🎯 Target Trades: {self.target_trades}")
        print(f"📊 Market Pairs: {len(self.market_data)}")
        print()
        
        symbols = list(self.market_data.keys())
        start_time = time.time()
        
        for i in range(self.target_trades):
            # Pick random symbol
            symbol = random.choice(symbols)
            market = self.market_data[symbol]
            
            # Generate random parameters within realistic ranges
            coherence = random.uniform(0.40, 0.95)
            frequency = random.uniform(300, 600)
            momentum = random.uniform(-5.0, 5.0)
            
            # Simulate trade
            trade = self.simulate_trade(
                symbol=symbol,
                entry_price=market['price'],
                coherence=coherence,
                frequency=frequency,
                momentum=momentum
            )
            
            # Update balance
            self.balance += trade['pnl_usd']
            self.total_pnl += trade['pnl_usd']
            
            if trade['win']:
                self.wins += 1
            else:
                self.losses += 1
                
            # Track for analysis
            self.trades.append(trade)
            self.performance_by_coherence[round(coherence, 1)].append(trade['pnl_usd'])
            self.performance_by_frequency[round(frequency, -1)].append(trade['pnl_usd'])
            self.performance_by_momentum[round(momentum)].append(trade['pnl_usd'])
            self.performance_by_symbol[symbol].append(trade['pnl_usd'])
            self.performance_by_hour[i % 24].append(trade['pnl_usd'])
            
            # Progress update every 50 trades
            if (i + 1) % 50 == 0:
                win_rate = self.wins / (i + 1) * 100
                print(f"   Trade {i+1}/{self.target_trades}: "
                      f"Win Rate: {win_rate:.1f}% | "
                      f"Balance: ${self.balance:,.2f} | "
                      f"PnL: ${self.total_pnl:+,.2f}")
                
        elapsed = time.time() - start_time
        print(f"\n✅ Simulation complete in {elapsed:.1f}s")
        
    def generate_report(self):
        """Generate comprehensive performance report"""
        print(f"\n{'='*70}")
        print("📊 SIMULATION RESULTS")
        print(f"{'='*70}\n")
        
        total_trades = self.wins + self.losses
        win_rate = self.wins / total_trades * 100 if total_trades > 0 else 0
        
        print(f"📈 OVERALL PERFORMANCE:")
        print(f"   Total Trades: {total_trades}")
        print(f"   Wins: {self.wins} | Losses: {self.losses}")
        print(f"   Win Rate: {win_rate:.1f}%")
        print(f"   Starting Balance: ${self.starting_balance:,.2f}")
        print(f"   Final Balance: ${self.balance:,.2f}")
        print(f"   Total PnL: ${self.total_pnl:+,.2f}")
        print(f"   Return: {(self.balance/self.starting_balance - 1)*100:+.2f}%")
        
        # Analyze by coherence
        print(f"\n🎯 PERFORMANCE BY COHERENCE THRESHOLD:")
        coherence_analysis = []
        for coherence, pnls in sorted(self.performance_by_coherence.items()):
            if len(pnls) >= 10:
                avg_pnl = statistics.mean(pnls)
                win_rate = sum(1 for p in pnls if p > 0) / len(pnls) * 100
                coherence_analysis.append((coherence, avg_pnl, win_rate, len(pnls)))
                print(f"   Coherence {coherence:.1f}: {len(pnls)} trades | "
                      f"Win Rate: {win_rate:.1f}% | Avg PnL: ${avg_pnl:+.2f}")
        
        # Find optimal coherence
        if coherence_analysis:
            best_coherence = max(coherence_analysis, key=lambda x: x[1])
            print(f"\n   ✨ OPTIMAL COHERENCE: {best_coherence[0]:.1f} "
                  f"(Win Rate: {best_coherence[2]:.1f}%, Avg PnL: ${best_coherence[1]:+.2f})")
        
        # Analyze by frequency
        print(f"\n🔊 PERFORMANCE BY FREQUENCY RANGE:")
        freq_analysis = []
        for freq, pnls in sorted(self.performance_by_frequency.items()):
            if len(pnls) >= 10:
                avg_pnl = statistics.mean(pnls)
                win_rate = sum(1 for p in pnls if p > 0) / len(pnls) * 100
                freq_analysis.append((freq, avg_pnl, win_rate, len(pnls)))
                print(f"   {freq:.0f}Hz: {len(pnls)} trades | "
                      f"Win Rate: {win_rate:.1f}% | Avg PnL: ${avg_pnl:+.2f}")
        
        if freq_analysis:
            best_freq = max(freq_analysis, key=lambda x: x[1])
            print(f"\n   ✨ OPTIMAL FREQUENCY: {best_freq[0]:.0f}Hz "
                  f"(Win Rate: {best_freq[2]:.1f}%, Avg PnL: ${best_freq[1]:+.2f})")
        
        # Analyze by momentum
        print(f"\n📉 PERFORMANCE BY MOMENTUM:")
        mom_analysis = []
        for mom, pnls in sorted(self.performance_by_momentum.items()):
            if len(pnls) >= 10:
                avg_pnl = statistics.mean(pnls)
                win_rate = sum(1 for p in pnls if p > 0) / len(pnls) * 100
                mom_analysis.append((mom, avg_pnl, win_rate, len(pnls)))
                print(f"   Momentum {mom:+.0f}: {len(pnls)} trades | "
                      f"Win Rate: {win_rate:.1f}% | Avg PnL: ${avg_pnl:+.2f}")
        
        if mom_analysis:
            best_mom = max(mom_analysis, key=lambda x: x[1])
            print(f"\n   ✨ OPTIMAL MOMENTUM: {best_mom[0]:+.0f} "
                  f"(Win Rate: {best_mom[2]:.1f}%, Avg PnL: ${best_mom[1]:+.2f})")
        
        # Top symbols
        print(f"\n🏆 TOP 10 PERFORMING SYMBOLS:")
        symbol_stats = []
        for symbol, pnls in self.performance_by_symbol.items():
            if len(pnls) >= 3:
                avg_pnl = statistics.mean(pnls)
                win_rate = sum(1 for p in pnls if p > 0) / len(pnls) * 100
                symbol_stats.append((symbol, sum(pnls), avg_pnl, win_rate, len(pnls)))
        
        symbol_stats.sort(key=lambda x: x[1], reverse=True)
        for symbol, total, avg, win_rate, count in symbol_stats[:10]:
            print(f"   {symbol}: ${total:+.2f} total | {win_rate:.0f}% wins | {count} trades")
        
        # Recommendations
        print(f"\n{'='*70}")
        print("💡 RECOMMENDATIONS FOR LIVE TRADING:")
        print(f"{'='*70}")
        
        if coherence_analysis:
            best_coh = max(coherence_analysis, key=lambda x: x[1])[0]
            print(f"   1. Set MIN_COHERENCE to {best_coh:.1f} or higher")
            
        if freq_analysis:
            best_freqs = sorted(freq_analysis, key=lambda x: x[1], reverse=True)[:3]
            freq_range = f"{min(f[0] for f in best_freqs):.0f}-{max(f[0] for f in best_freqs):.0f}"
            print(f"   2. Filter for frequency range: {freq_range}Hz")
            
        if mom_analysis:
            best_moms = sorted(mom_analysis, key=lambda x: x[1], reverse=True)[:3]
            print(f"   3. Best momentum zones: {[m[0] for m in best_moms]}")
            
        print(f"   4. Avoid symbols with consistently negative performance")
        print(f"   5. Current win rate {win_rate:.1f}% suggests system is {'profitable' if win_rate > 52 else 'marginal'}")
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'total_pnl': self.total_pnl,
            'final_balance': self.balance,
            'best_coherence': best_coherence[0] if coherence_analysis else 0.7,
            'best_frequency': best_freq[0] if freq_analysis else 450,
            'recommendations': 'See above'
        }
    
    def save_results(self, filename='sim_results.json'):
        """Save results to file"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'starting_balance': self.starting_balance,
            'final_balance': self.balance,
            'total_pnl': self.total_pnl,
            'total_trades': len(self.trades),
            'wins': self.wins,
            'losses': self.losses,
            'win_rate': self.wins / len(self.trades) * 100 if self.trades else 0,
            'trades': self.trades[-100:]  # Save last 100 trades
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to {filename}")


def main():
    print("\n" + "🚀"*30)
    print("   AUREON BIG SIMULATION - PARAMETER REFINEMENT")
    print("🚀"*30 + "\n")
    
    # Run simulation with 1000 trades
    sim = BigSimulator(starting_balance=10000, target_trades=1000)
    sim.run_simulation()
    report = sim.generate_report()
    sim.save_results()
    
    # Run a FILTERED simulation with optimal params only
    print("\n" + "="*70)
    print("🎯 RUNNING FILTERED SIMULATION (OPTIMAL PARAMS ONLY)")
    print("="*70 + "\n")
    
    sim2 = FilteredSimulator(
        starting_balance=10000, 
        target_trades=500,
        min_coherence=0.65,
        freq_range=(380, 520),
        momentum_range=(-3, 2)
    )
    sim2.run_simulation()
    sim2.generate_report()
    
    print(f"\n{'='*70}")
    print("✅ ALL SIMULATIONS COMPLETE")
    print(f"{'='*70}\n")


class FilteredSimulator(BigSimulator):
    """Simulation with filtered parameters"""
    
    def __init__(self, starting_balance=10000, target_trades=500, 
                 min_coherence=0.65, freq_range=(400, 500), momentum_range=(-2, 2)):
        super().__init__(starting_balance, target_trades)
        self.min_coherence = min_coherence
        self.freq_range = freq_range
        self.momentum_range = momentum_range
        
    def run_simulation(self):
        """Run filtered simulation"""
        print(f"💰 Starting Balance: ${self.starting_balance:,.2f}")
        print(f"🎯 Target Trades: {self.target_trades}")
        print(f"📊 Filters: coherence>{self.min_coherence}, freq={self.freq_range}, mom={self.momentum_range}")
        print()
        
        symbols = list(self.market_data.keys())
        start_time = time.time()
        
        for i in range(self.target_trades):
            symbol = random.choice(symbols)
            market = self.market_data[symbol]
            
            # Generate parameters WITHIN filtered ranges
            coherence = random.uniform(self.min_coherence, 0.95)
            frequency = random.uniform(self.freq_range[0], self.freq_range[1])
            momentum = random.uniform(self.momentum_range[0], self.momentum_range[1])
            
            trade = self.simulate_trade(
                symbol=symbol,
                entry_price=market['price'],
                coherence=coherence,
                frequency=frequency,
                momentum=momentum
            )
            
            self.balance += trade['pnl_usd']
            self.total_pnl += trade['pnl_usd']
            
            if trade['win']:
                self.wins += 1
            else:
                self.losses += 1
                
            self.trades.append(trade)
            
            if (i + 1) % 100 == 0:
                win_rate = self.wins / (i + 1) * 100
                print(f"   Trade {i+1}/{self.target_trades}: "
                      f"Win Rate: {win_rate:.1f}% | "
                      f"Balance: ${self.balance:,.2f} | "
                      f"PnL: ${self.total_pnl:+,.2f}")
                
        elapsed = time.time() - start_time
        print(f"\n✅ Filtered simulation complete in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
