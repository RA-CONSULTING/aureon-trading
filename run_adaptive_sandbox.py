#!/usr/bin/env python3
"""
🧠 ADAPTIVE PENNY PROFIT SANDBOX
================================
A continuous feedback loop where the Samuel brain LEARNS from its mistakes.
The system is NOT made easier - it must FIGURE IT OUT through trial and error.

The brain adapts:
- Entry timing
- Position sizing
- Exit thresholds
- Volatility filters
- Coherence requirements

This is a SANDBOXED learning environment. The brain evolves until it finds
a profitable configuration, then persists that knowledge.

Gary Leckey | December 2025
"The system must learn. Not be handed answers."
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
import json
import random
import math
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Constants
KRAKEN_TAKER_FEE = 0.0026  # 0.26%
KRAKEN_MAKER_FEE = 0.0016  # 0.16%
LEARNING_FILE = "sandbox_brain_learning.json"


@dataclass
class BrainParameters:
    """
    The parameters the brain can evolve.
    These start random and the brain learns optimal values.
    """
    # Entry parameters
    min_coherence: float = 0.5          # Minimum coherence to enter
    min_volatility: float = 0.3         # Minimum volatility to enter
    max_volatility: float = 3.0         # Maximum volatility (avoid chaos)
    
    # Position sizing
    position_size_pct: float = 0.05     # % of capital per trade
    
    # Exit parameters
    take_profit_pct: float = 0.5        # % move to take profit
    stop_loss_pct: float = 0.3          # % move to stop loss
    
    # Timing
    hold_cycles_min: int = 1            # Minimum hold time
    hold_cycles_max: int = 50           # Maximum hold time
    
    # Maker vs Taker
    use_maker_orders: bool = False      # Try to use maker orders
    
    def mutate(self, mutation_rate: float = 0.1, aggressive: bool = False):
        """Randomly mutate parameters to explore new strategies."""
        scale = 3.0 if aggressive else 1.0
        
        if random.random() < mutation_rate:
            self.min_coherence = max(0.3, min(0.9, self.min_coherence + random.gauss(0, 0.05 * scale)))
        if random.random() < mutation_rate:
            self.min_volatility = max(0.1, min(1.0, self.min_volatility + random.gauss(0, 0.1 * scale)))
        if random.random() < mutation_rate:
            self.max_volatility = max(1.0, min(5.0, self.max_volatility + random.gauss(0, 0.3 * scale)))
        if random.random() < mutation_rate:
            self.position_size_pct = max(0.02, min(0.3, self.position_size_pct + random.gauss(0, 0.02 * scale)))
        if random.random() < mutation_rate:
            self.take_profit_pct = max(0.2, min(3.0, self.take_profit_pct + random.gauss(0, 0.15 * scale)))
        if random.random() < mutation_rate:
            self.stop_loss_pct = max(0.1, min(2.0, self.stop_loss_pct + random.gauss(0, 0.08 * scale)))
        if random.random() < mutation_rate:
            self.hold_cycles_max = max(10, min(200, self.hold_cycles_max + int(random.gauss(0, 15 * scale))))
        if random.random() < mutation_rate:
            self.use_maker_orders = not self.use_maker_orders
    
    def randomize(self):
        """Completely randomize parameters for fresh exploration."""
        self.min_coherence = random.uniform(0.3, 0.8)
        self.min_volatility = random.uniform(0.1, 0.8)
        self.max_volatility = random.uniform(1.5, 4.0)
        self.position_size_pct = random.uniform(0.03, 0.25)
        self.take_profit_pct = random.uniform(0.3, 2.0)
        self.stop_loss_pct = random.uniform(0.15, 1.5)
        self.hold_cycles_max = random.randint(20, 150)
        self.use_maker_orders = random.choice([True, False])


@dataclass
class TradeResult:
    """Result of a single trade."""
    entry_price: float
    exit_price: float
    quantity: float
    entry_fee: float
    exit_fee: float
    gross_pnl: float
    net_pnl: float
    hold_cycles: int
    outcome: str  # WIN, LOSS, BREAKEVEN
    market_volatility: float
    market_coherence: float
    parameters_used: Dict


@dataclass
class LearningState:
    """The brain's accumulated learning."""
    generation: int = 0
    total_trades: int = 0
    total_wins: int = 0
    total_losses: int = 0
    best_win_rate: float = 0.0
    best_parameters: Optional[Dict] = None
    best_total_pnl: float = float('-inf')
    
    # Learning history
    generation_history: List[Dict] = field(default_factory=list)
    
    # Lessons learned (what works, what doesn't)
    lessons: List[str] = field(default_factory=list)


class MarketSimulator:
    """Simulates realistic market conditions."""
    
    def __init__(self):
        self.current_price = 100.0
        self.volatility = 1.0  # % per cycle
        self.trend = 0.0       # Slight bias
        self.coherence = 0.5   # Market "quality"
    
    def tick(self) -> Tuple[float, float, float]:
        """
        Advance one market cycle.
        Returns: (new_price, volatility, coherence)
        """
        # Random walk with trend
        move = random.gauss(self.trend, self.volatility)
        self.current_price *= (1 + move / 100)
        
        # Volatility regime changes
        if random.random() < 0.05:
            self.volatility = random.uniform(0.2, 3.0)
        
        # Coherence changes (market quality)
        if random.random() < 0.1:
            self.coherence = random.uniform(0.3, 0.9)
        
        # Trend shifts
        if random.random() < 0.02:
            self.trend = random.uniform(-0.1, 0.1)
        
        return self.current_price, self.volatility, self.coherence


class AdaptiveBrain:
    """
    The brain that learns through trial and error.
    It does NOT get easier - it must figure out the solution.
    """
    
    def __init__(self, starting_capital: float = 100.0):
        self.starting_capital = starting_capital
        self.capital = starting_capital
        self.parameters = BrainParameters()
        self.learning = LearningState()
        self.trade_history: List[TradeResult] = []
        self.position: Optional[Dict] = None
        self.market = MarketSimulator()
        
        # Load previous learning if exists
        self._load_learning()
    
    def _load_learning(self):
        """Load previous learning from file."""
        if os.path.exists(LEARNING_FILE):
            try:
                with open(LEARNING_FILE, 'r') as f:
                    data = json.load(f)
                self.learning.generation = data.get('generation', 0)
                self.learning.best_win_rate = data.get('best_win_rate', 0)
                self.learning.best_parameters = data.get('best_parameters')
                self.learning.best_total_pnl = data.get('best_total_pnl', float('-inf'))
                self.learning.lessons = data.get('lessons', [])
                
                # Start from best known parameters if available
                if self.learning.best_parameters:
                    for key, value in self.learning.best_parameters.items():
                        if hasattr(self.parameters, key):
                            setattr(self.parameters, key, value)
                
                print(f"📖 Loaded learning from generation {self.learning.generation}")
                print(f"   Best win rate so far: {self.learning.best_win_rate:.1f}%")
            except Exception as e:
                print(f"⚠️ Could not load learning: {e}")
    
    def _save_learning(self):
        """Persist learning to file."""
        data = {
            'generation': self.learning.generation,
            'total_trades': self.learning.total_trades,
            'total_wins': self.learning.total_wins,
            'total_losses': self.learning.total_losses,
            'best_win_rate': self.learning.best_win_rate,
            'best_parameters': self.learning.best_parameters,
            'best_total_pnl': self.learning.best_total_pnl,
            'lessons': self.learning.lessons[-20:],  # Keep last 20 lessons
            'generation_history': self.learning.generation_history[-50:],  # Keep last 50 gens
            'last_updated': datetime.now().isoformat(),
        }
        with open(LEARNING_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    
    def should_enter(self, volatility: float, coherence: float) -> bool:
        """Decide if we should enter a trade based on current parameters."""
        if self.position is not None:
            return False  # Already in a trade
        
        # Check coherence threshold
        if coherence < self.parameters.min_coherence:
            return False
        
        # Check volatility range
        if volatility < self.parameters.min_volatility:
            return False
        if volatility > self.parameters.max_volatility:
            return False
        
        return True
    
    def should_exit(self, entry_price: float, current_price: float, cycles_held: int) -> Tuple[bool, str]:
        """Decide if we should exit a trade."""
        # Calculate current P&L percentage
        pnl_pct = ((current_price / entry_price) - 1) * 100
        
        # Take profit
        if pnl_pct >= self.parameters.take_profit_pct:
            return True, "TAKE_PROFIT"
        
        # Stop loss
        if pnl_pct <= -self.parameters.stop_loss_pct:
            return True, "STOP_LOSS"
        
        # Time-based exit
        if cycles_held >= self.parameters.hold_cycles_max:
            return True, "TIME_EXIT"
        
        return False, ""
    
    def execute_trade(self, entry_price: float, exit_price: float, 
                     volatility: float, coherence: float, cycles: int) -> TradeResult:
        """Execute a trade and calculate results."""
        # Position size
        position_value = self.capital * self.parameters.position_size_pct
        quantity = position_value / entry_price
        
        # Fees
        fee_rate = KRAKEN_MAKER_FEE if self.parameters.use_maker_orders else KRAKEN_TAKER_FEE
        entry_fee = position_value * fee_rate
        exit_value = quantity * exit_price
        exit_fee = exit_value * fee_rate
        
        # P&L
        gross_pnl = exit_value - position_value
        net_pnl = gross_pnl - entry_fee - exit_fee
        
        # Outcome
        if net_pnl >= 0.0001:
            outcome = "WIN"
        elif net_pnl <= -0.01:
            outcome = "LOSS"
        else:
            outcome = "BREAKEVEN"
        
        # Update capital
        self.capital += net_pnl
        
        return TradeResult(
            entry_price=entry_price,
            exit_price=exit_price,
            quantity=quantity,
            entry_fee=entry_fee,
            exit_fee=exit_fee,
            gross_pnl=gross_pnl,
            net_pnl=net_pnl,
            hold_cycles=cycles,
            outcome=outcome,
            market_volatility=volatility,
            market_coherence=coherence,
            parameters_used=asdict(self.parameters),
        )
    
    def analyze_and_learn(self, trades: List[TradeResult]) -> str:
        """
        Analyze trades and extract lessons.
        This is where the brain LEARNS from mistakes.
        """
        if not trades:
            return "No trades to analyze"
        
        wins = [t for t in trades if t.outcome == "WIN"]
        losses = [t for t in trades if t.outcome == "LOSS"]
        
        lessons = []
        
        # Analyze winning trades - what conditions worked?
        if wins:
            avg_win_volatility = sum(t.market_volatility for t in wins) / len(wins)
            avg_win_coherence = sum(t.market_coherence for t in wins) / len(wins)
            avg_win_cycles = sum(t.hold_cycles for t in wins) / len(wins)
            avg_win_pnl = sum(t.net_pnl for t in wins) / len(wins)
            
            lessons.append(f"Wins: vol={avg_win_volatility:.2f}, coh={avg_win_coherence:.2f}, hold={avg_win_cycles:.0f}")
            
            # Learn optimal volatility for winning
            if avg_win_volatility > 1.5:
                # Wins happen in higher volatility - seek it
                self.parameters.min_volatility = max(0.2, self.parameters.min_volatility + 0.03)
        
        # Analyze losing trades - what to avoid?
        if losses:
            avg_loss_volatility = sum(t.market_volatility for t in losses) / len(losses)
            avg_loss_coherence = sum(t.market_coherence for t in losses) / len(losses)
            avg_loss_cycles = sum(t.hold_cycles for t in losses) / len(losses)
            
            lessons.append(f"Loss: vol={avg_loss_volatility:.2f}, coh={avg_loss_coherence:.2f}, hold={avg_loss_cycles:.0f}")
            
            # Learn: if losses happen at low coherence, raise threshold
            if avg_loss_coherence < 0.55:
                self.parameters.min_coherence = min(0.85, self.parameters.min_coherence + 0.02)
                lessons.append(f"↑ min_coherence to {self.parameters.min_coherence:.2f}")
            
            # Learn: if losses from holding too long, reduce
            if avg_loss_cycles > avg_win_cycles * 1.5 if wins else 30:
                self.parameters.hold_cycles_max = max(15, self.parameters.hold_cycles_max - 5)
                lessons.append(f"↓ hold_max to {self.parameters.hold_cycles_max}")
        
        # Win/loss ratio analysis
        win_rate = len(wins) / len(trades) * 100 if trades else 0
        total_pnl = sum(t.net_pnl for t in trades)
        
        # Key insight: if win rate is OK but still losing money, issue is profit vs loss size
        if win_rate >= 45 and total_pnl < 0:
            avg_win = sum(t.net_pnl for t in wins) / len(wins) if wins else 0
            avg_loss = sum(t.net_pnl for t in losses) / len(losses) if losses else 0
            
            if abs(avg_loss) > avg_win * 1.5:
                # Losses are too big relative to wins - tighten stop
                self.parameters.stop_loss_pct = max(0.15, self.parameters.stop_loss_pct - 0.03)
                lessons.append(f"↓ stop_loss to {self.parameters.stop_loss_pct:.2f}% (losses too big)")
            else:
                # Need bigger wins - widen take profit
                self.parameters.take_profit_pct = min(2.5, self.parameters.take_profit_pct + 0.05)
                lessons.append(f"↑ take_profit to {self.parameters.take_profit_pct:.2f}% (wins too small)")
        
        # If win rate is low, need to be pickier or faster
        if win_rate < 40:
            if self.parameters.take_profit_pct > 0.4:
                self.parameters.take_profit_pct = max(0.25, self.parameters.take_profit_pct - 0.05)
                lessons.append(f"↓ take_profit to {self.parameters.take_profit_pct:.2f}% (be faster)")
            else:
                # Already fast - need to be pickier
                self.parameters.min_coherence = min(0.85, self.parameters.min_coherence + 0.02)
                lessons.append(f"↑ min_coherence to {self.parameters.min_coherence:.2f} (be pickier)")
        
        # If doing well, maybe we can optimize position sizing
        if win_rate > 55 and total_pnl > 0:
            self.parameters.position_size_pct = min(0.25, self.parameters.position_size_pct + 0.01)
            lessons.append(f"↑ position_size to {self.parameters.position_size_pct:.1%} (winning!)")
        
        # Persist lessons
        self.learning.lessons.extend(lessons)
        
        return "\n".join(lessons)
    
    def run_generation(self, num_cycles: int = 500) -> Dict:
        """
        Run one generation of trading.
        The brain trades, learns, and evolves.
        """
        self.learning.generation += 1
        gen_trades: List[TradeResult] = []
        self.capital = self.starting_capital
        self.position = None
        
        entry_price = None
        entry_volatility = None
        entry_coherence = None
        cycles_in_trade = 0
        
        for cycle in range(num_cycles):
            # Market tick
            price, volatility, coherence = self.market.tick()
            
            if self.position is None:
                # Look for entry
                if self.should_enter(volatility, coherence):
                    self.position = {
                        'entry_price': price,
                        'entry_volatility': volatility,
                        'entry_coherence': coherence,
                    }
                    entry_price = price
                    entry_volatility = volatility
                    entry_coherence = coherence
                    cycles_in_trade = 0
            else:
                # In a trade - check for exit
                cycles_in_trade += 1
                should_exit, reason = self.should_exit(entry_price, price, cycles_in_trade)
                
                if should_exit:
                    # Execute exit
                    result = self.execute_trade(
                        entry_price, price,
                        entry_volatility, entry_coherence,
                        cycles_in_trade
                    )
                    gen_trades.append(result)
                    self.position = None
                    
                    # Update stats
                    self.learning.total_trades += 1
                    if result.outcome == "WIN":
                        self.learning.total_wins += 1
                    elif result.outcome == "LOSS":
                        self.learning.total_losses += 1
        
        # Close any open position at end
        if self.position is not None:
            price, _, _ = self.market.tick()
            result = self.execute_trade(
                entry_price, price,
                entry_volatility, entry_coherence,
                cycles_in_trade
            )
            gen_trades.append(result)
            self.position = None
        
        # Calculate generation stats
        wins = len([t for t in gen_trades if t.outcome == "WIN"])
        losses = len([t for t in gen_trades if t.outcome == "LOSS"])
        total_pnl = sum(t.net_pnl for t in gen_trades)
        win_rate = (wins / len(gen_trades) * 100) if gen_trades else 0
        
        # Learn from this generation
        lessons = self.analyze_and_learn(gen_trades)
        
        # Check if this is best generation
        if win_rate > self.learning.best_win_rate or \
           (win_rate == self.learning.best_win_rate and total_pnl > self.learning.best_total_pnl):
            self.learning.best_win_rate = win_rate
            self.learning.best_total_pnl = total_pnl
            self.learning.best_parameters = asdict(self.parameters)
        
        # Record generation
        gen_result = {
            'generation': self.learning.generation,
            'trades': len(gen_trades),
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'final_capital': self.capital,
            'parameters': asdict(self.parameters),
        }
        self.learning.generation_history.append(gen_result)
        
        # Evolutionary strategy: if stuck, try aggressive mutation or randomization
        gens_since_improvement = self.learning.generation - len([
            g for g in self.learning.generation_history[-20:]
            if g.get('win_rate', 0) >= self.learning.best_win_rate
        ])
        
        if gens_since_improvement > 15:
            # Stuck! Randomize to explore new space
            self.parameters.randomize()
            self.learning.lessons.append(f"Gen {self.learning.generation}: STUCK - randomizing parameters")
        elif gens_since_improvement > 8:
            # Getting stuck - try aggressive mutation
            self.parameters.mutate(mutation_rate=0.5, aggressive=True)
        else:
            # Normal evolution
            self.parameters.mutate(mutation_rate=0.2)
        
        # Save learning
        self._save_learning()
        
        return gen_result


def run_sandbox(max_generations: int = 100, target_win_rate: float = 55.0):
    """
    Run the sandbox until the brain figures it out or hits max generations.
    """
    print("\n" + "="*70)
    print("  🧠 ADAPTIVE PENNY PROFIT SANDBOX")
    print("="*70)
    print("  The brain must LEARN to make penny profit.")
    print("  It will NOT be made easier. Trial and error only.")
    print(f"  Target: {target_win_rate}% win rate")
    print(f"  Max Generations: {max_generations}")
    print("="*70 + "\n")
    
    brain = AdaptiveBrain(starting_capital=100.0)
    
    print(f"🧬 Starting from generation {brain.learning.generation}")
    if brain.learning.best_win_rate > 0:
        print(f"   Previous best: {brain.learning.best_win_rate:.1f}% win rate")
    print()
    
    success = False
    start_time = time.time()
    
    for i in range(max_generations):
        result = brain.run_generation(num_cycles=500)
        
        # Progress output
        emoji = "✅" if result['win_rate'] >= 50 else "⚠️" if result['win_rate'] >= 35 else "❌"
        print(f"Gen {result['generation']:3d} | {emoji} Win: {result['win_rate']:5.1f}% | "
              f"Trades: {result['trades']:3d} | P&L: ${result['total_pnl']:+7.4f} | "
              f"Capital: ${result['final_capital']:.2f}")
        
        # Check if brain has figured it out
        if result['win_rate'] >= target_win_rate and result['total_pnl'] > 0:
            success = True
            print(f"\n🎉 BRAIN FIGURED IT OUT in generation {result['generation']}!")
            break
        
        # Show learning every 10 generations
        if (i + 1) % 10 == 0:
            print(f"\n📖 Lessons learned so far:")
            for lesson in brain.learning.lessons[-3:]:
                print(f"   - {lesson}")
            print()
    
    elapsed = time.time() - start_time
    
    # Final summary
    print("\n" + "="*70)
    print("  📊 SANDBOX RESULTS")
    print("="*70)
    
    if success:
        print(f"\n  ✅ SUCCESS! Brain achieved {target_win_rate}% win rate")
    else:
        print(f"\n  ⏳ Brain still learning (best: {brain.learning.best_win_rate:.1f}%)")
    
    print(f"\n  Generations Run: {brain.learning.generation}")
    print(f"  Total Trades: {brain.learning.total_trades}")
    print(f"  Time Elapsed: {elapsed:.1f}s")
    
    if brain.learning.best_parameters:
        print(f"\n  🏆 BEST PARAMETERS FOUND:")
        for key, value in brain.learning.best_parameters.items():
            print(f"     {key}: {value}")
    
    print(f"\n  📚 KEY LESSONS LEARNED:")
    for lesson in brain.learning.lessons[-5:]:
        print(f"     - {lesson}")
    
    print("\n" + "="*70)
    print("  Learning persisted to: sandbox_brain_learning.json")
    print("  Run again to continue learning from where it left off.")
    print("="*70 + "\n")
    
    return brain


def main():
    print("\n🧠 SAMUEL HARMONIC TRADING ENTITY - ADAPTIVE LEARNING SANDBOX")
    print("   The brain learns through trial and error. No shortcuts.\n")
    
    # Check for infinite mode
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--infinite':
        print("♾️  INFINITE LEARNING MODE - Press Ctrl+C to stop\n")
        generation = 0
        try:
            while True:
                brain = run_sandbox(max_generations=25, target_win_rate=58.0)
                generation += 25
                print(f"\n🔄 Completed batch. Total generations: {brain.learning.generation}")
                print(f"   Best ever: {brain.learning.best_win_rate:.1f}% win rate")
                print("   Continuing...\n")
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n\n⏹️  Learning stopped by user.")
            print(f"   Final generation: {brain.learning.generation}")
            print(f"   Best win rate achieved: {brain.learning.best_win_rate:.1f}%")
    else:
        # Run until brain figures it out or 50 generations
        brain = run_sandbox(max_generations=50, target_win_rate=52.0)


if __name__ == "__main__":
    main()
