#!/usr/bin/env python3
"""
⛰️ AUREON MOUNTAIN CLIMBER - LEARNING TO CLIMB THE MOUNTAIN
═══════════════════════════════════════════════════════════════════════════════

THE COMPLETE MOUNTAIN PILGRIMAGE:
  🔽 DESCENT: DCA down collecting pebbles (breadcrumbs) on the way down
  ⬆️ ASCENT: Learn optimal climbing strategy - when to take profits, when to HODL
  
The Queen learns to climb the mountain by studying:
  1. HISTORICAL PEAKS - Where do coins typically reverse?
  2. FIBONACCI LEVELS - Optimal profit-taking zones (23.6%, 38.2%, 50%, 61.8%, 78.6%)
  3. VOLUME PATTERNS - When do climbers stop and take profit?
  4. TIME CYCLES - What's the optimal hold duration?
  5. MOMENTUM SATURATION - When does the climb get too steep (bubble)?
  
CLIMBING STRATEGY:
  • Establish base camp at cost basis
  • Place ropes at Fibonacci levels
  • Use partial profit-taking (pyramid up)
  • Learn when to summit vs when to HODL for bigger climb
  • Build new base camp at higher level for next climb
  
Gary Leckey | The Queen Learns to Climb | February 2026
═══════════════════════════════════════════════════════════════════════════════
"""

import json
import logging
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import statistics

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# 📊 MOUNTAIN CLIMBING DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ClimbingRope:
    """A profit-taking level along the climb."""
    level: float  # Price level (absolute)
    level_percent: float  # % above entry (e.g., 0.236 = 23.6%)
    name: str  # "Fibonacci 38.2%" or "Volume Peak"
    take_profit_percent: float = 0.25  # How much to sell at this level (25% = quarter positions)
    times_triggered: int = 0
    times_hit_target: int = 0  # Did price climb PAST this level?
    avg_profit_realization: float = 0.0  # Avg $ profit when rope triggered
    

@dataclass
class BaseCamp:
    """State of a position's base camp (starting point for a climb)."""
    symbol: str
    entry_price: float
    entry_time: datetime
    quantity_at_camp: float
    cost_basis_at_camp: float  # Total cost to establish camp
    max_price_seen: float = 0.0  # Highest we've climbed from this camp
    current_price: float = 0.0
    ropes: Dict[str, ClimbingRope] = field(default_factory=dict)  # Profit-taking levels
    profit_realized: float = 0.0  # Total profit taken from this camp
    positions_closed: int = 0  # How many profit-taking events occurred
    is_active: bool = True
    

@dataclass
class ClimbingPath:
    """Historical record of a successful climb (entry to exit)."""
    symbol: str
    entry_price: float
    entry_time: datetime
    exit_price: float
    exit_time: datetime
    peak_price: float
    peak_time: datetime
    total_gain_pct: float
    duration: timedelta
    ropes_triggered: List[str] = field(default_factory=list)  # Which levels were hit?
    profit_realized: float = 0.0
    
    def climb_efficiency(self) -> float:
        """How close to peak price did we take profits?"""
        if self.peak_price <= self.entry_price:
            return 0.0
        peak_potential = self.peak_price - self.entry_price
        actual_gain = self.exit_price - self.entry_price
        if peak_potential == 0:
            return 0.0
        return actual_gain / peak_potential
    

@dataclass
class MountainLearner:
    """Learns climbing patterns across all mountains."""
    symbol: str
    total_climbs: int = 0
    successful_climbs: int = 0  # Hit profit target
    avg_climb_height: float = 0.0  # Avg % gain per climb
    avg_climb_duration: timedelta = field(default_factory=lambda: timedelta(hours=1))
    
    # Fibonacci learning
    fib_238_hit_rate: float = 0.0  # How often does 23.8% level get hit?
    fib_382_hit_rate: float = 0.0
    fib_500_hit_rate: float = 0.0
    fib_618_hit_rate: float = 0.0
    fib_786_hit_rate: float = 0.0
    
    # Optimal exit strategy
    best_exit_level: float = 0.382  # Learn which Fib level is most profitable
    optimal_hold_time: timedelta = field(default_factory=lambda: timedelta(hours=4))
    avg_efficiency: float = 0.0  # How much of peak gain do we capture?
    
    # Volume learning
    volume_peaks: Dict[float, float] = field(default_factory=dict)  # price_level -> frequency
    

# ═══════════════════════════════════════════════════════════════════════════════
# ⛰️ MOUNTAIN CLIMBER ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class MountainClimber:
    """
    Learns optimal climbing strategy for each coin.
    
    Monitors positions as they climb and learns:
    - Where do most coins reverse?
    - What % gains trigger profit-taking?
    - How long do climbs typically take?
    - When to pyramid up vs when to HODL
    """
    
    def __init__(self, state_file: str = "mountain_climbing_state.json"):
        self.state_file = Path(state_file)
        self.base_camps: Dict[str, BaseCamp] = {}  # Current climbing positions
        self.completed_climbs: Dict[str, List[ClimbingPath]] = {}  # Historical climbs
        self.learners: Dict[str, MountainLearner] = {}  # Learned patterns per coin
        
        logger.info("⛰️ MOUNTAIN CLIMBER ENGINE INITIALIZED")
        self._load_state()
    
    def establish_base_camp(
        self,
        symbol: str,
        entry_price: float,
        quantity: float,
        cost_basis: float
    ) -> BaseCamp:
        """
        Establish a base camp for a new climb.
        
        Sets up Fibonacci ropes and learning parameters.
        """
        camp = BaseCamp(
            symbol=symbol,
            entry_price=entry_price,
            entry_time=datetime.now(),
            quantity_at_camp=quantity,
            cost_basis_at_camp=cost_basis,
            max_price_seen=entry_price,
            current_price=entry_price
        )
        
        # Set up Fibonacci profit-taking ropes
        fib_levels = {
            "Fibonacci 23.8%": 0.238,
            "Fibonacci 38.2%": 0.382,
            "Fibonacci 50.0%": 0.500,
            "Fibonacci 61.8%": 0.618,
            "Fibonacci 78.6%": 0.786,
        }
        
        for name, fib_pct in fib_levels.items():
            rope_price = entry_price * (1 + fib_pct)
            camp.ropes[name] = ClimbingRope(
                level=rope_price,
                level_percent=fib_pct,
                name=name,
                take_profit_percent=0.20  # Default: sell 20% at each level
            )
        
        # Adjust profit-taking based on learned patterns for this symbol
        if symbol in self.learners:
            learner = self.learners[symbol]
            # Use optimal exit level learned from history
            for rope_name, rope in camp.ropes.items():
                if rope.level_percent == learner.best_exit_level:
                    rope.take_profit_percent = 0.35  # Sell more at the best level
        
        self.base_camps[symbol] = camp
        logger.info(f"⛰️ BASE CAMP ESTABLISHED on {symbol}")
        logger.info(f"   Entry: ${entry_price:.6f}")
        logger.info(f"   Quantity: {quantity:.4f}")
        logger.info(f"   Cost Basis: ${cost_basis:.2f}")
        logger.info(f"   Fibonacci Ropes:")
        for rope_name, rope in camp.ropes.items():
            logger.info(f"      🪢 {rope_name}: ${rope.level:.6f} (sell {rope.take_profit_percent:.0%})")
        
        return camp
    
    def update_climb(
        self,
        symbol: str,
        current_price: float,
        current_time: Optional[datetime] = None
    ) -> Dict:
        """
        Update a climb with current price.
        
        Returns: {
            'ropes_triggered': [list of profit-taking events],
            'current_profit_pct': percent gain,
            'is_climbing': bool,
            'ropes_ahead': [upcoming levels]
        }
        """
        if symbol not in self.base_camps:
            return {'error': 'No active climb for this symbol'}
        
        if current_time is None:
            current_time = datetime.now()
        
        camp = self.base_camps[symbol]
        camp.current_price = current_price
        
        # Track max price (peak of climb)
        if current_price > camp.max_price_seen:
            camp.max_price_seen = current_price
        
        current_gain_pct = (current_price - camp.entry_price) / camp.entry_price
        
        # Check for rope triggers
        triggered_ropes = []
        for rope_name, rope in camp.ropes.items():
            if current_price >= rope.level and rope.times_triggered == 0:
                # ROPE TRIGGERED! Time to take profit
                triggered_ropes.append(rope_name)
                rope.times_triggered += 1
                
                # Update rope statistics
                profit_at_level = (rope.level - camp.entry_price) * camp.quantity_at_camp
                rope.avg_profit_realization = profit_at_level
                
                logger.info(f"🪢 ROPE TRIGGERED on {symbol}!")
                logger.info(f"   Level: {rope.name}")
                logger.info(f"   Price: ${current_price:.6f}")
                logger.info(f"   Profit: {(rope.level - camp.entry_price) / camp.entry_price:.1%}")
                logger.info(f"   Action: Sell {rope.take_profit_percent:.0%} of position")
        
        # Check if we're descending (bear trap after climb)
        is_climbing = current_price > camp.max_price_seen or current_gain_pct > 0.02
        
        # Find ropes ahead
        ropes_ahead = [
            (rope_name, rope.level, rope.level_percent)
            for rope_name, rope in camp.ropes.items()
            if rope.times_triggered == 0 and current_price < rope.level
        ]
        ropes_ahead.sort(key=lambda x: x[1])  # Sort by price
        
        result = {
            'current_price': current_price,
            'current_gain_pct': current_gain_pct,
            'current_gain_usd': (current_price - camp.entry_price) * camp.quantity_at_camp,
            'is_climbing': is_climbing,
            'peak_price': camp.max_price_seen,
            'peak_gain_pct': (camp.max_price_seen - camp.entry_price) / camp.entry_price,
            'ropes_triggered': triggered_ropes,
            'ropes_ahead': [(name, f"${level:.6f}", f"+{pct:.1%}") for name, level, pct in ropes_ahead[:3]],
            'climb_duration': (current_time - camp.entry_time).total_seconds() / 3600  # Hours
        }
        
        return result
    
    def close_climb(
        self,
        symbol: str,
        exit_price: float,
        exit_time: Optional[datetime] = None
    ) -> Optional[ClimbingPath]:
        """
        Close a climb and record it for learning.
        
        This finalizes profit-taking decisions and learns from the outcome.
        """
        if symbol not in self.base_camps:
            return None
        
        if exit_time is None:
            exit_time = datetime.now()
        
        camp = self.base_camps[symbol]
        
        # Create climbing path record
        climb = ClimbingPath(
            symbol=symbol,
            entry_price=camp.entry_price,
            entry_time=camp.entry_time,
            exit_price=exit_price,
            exit_time=exit_time,
            peak_price=camp.max_price_seen,
            peak_time=exit_time,  # We'd need to track this properly
            total_gain_pct=(exit_price - camp.entry_price) / camp.entry_price,
            duration=exit_time - camp.entry_time,
            ropes_triggered=[rope.name for rope, r in camp.ropes.items() if r.times_triggered > 0],
            profit_realized=camp.profit_realized
        )
        
        # Record the climb
        if symbol not in self.completed_climbs:
            self.completed_climbs[symbol] = []
        self.completed_climbs[symbol].append(climb)
        
        # Update learner for this symbol
        self._update_learner(symbol, climb)
        
        # Remove base camp
        del self.base_camps[symbol]
        
        logger.info(f"⛰️ CLIMB CLOSED on {symbol}")
        logger.info(f"   Entry: ${camp.entry_price:.6f}")
        logger.info(f"   Exit: ${exit_price:.6f}")
        logger.info(f"   Gain: {climb.total_gain_pct:+.1%}")
        logger.info(f"   Peak: ${camp.max_price_seen:.6f} ({climb.peak_price - camp.entry_price:.0%})")
        logger.info(f"   Duration: {climb.duration.total_seconds() / 3600:.1f} hours")
        logger.info(f"   Efficiency: {climb.climb_efficiency():.1%} of peak captured")
        
        self._save_state()
        return climb
    
    def _update_learner(self, symbol: str, climb: ClimbingPath):
        """Learn from completed climb."""
        if symbol not in self.learners:
            self.learners[symbol] = MountainLearner(symbol=symbol)
        
        learner = self.learners[symbol]
        learner.total_climbs += 1
        
        if climb.climb_efficiency() > 0.5:  # Captured at least 50% of peak
            learner.successful_climbs += 1
        
        # Update statistics
        all_climbs = self.completed_climbs.get(symbol, [])
        if all_climbs:
            gains = [c.total_gain_pct for c in all_climbs]
            durations = [c.duration.total_seconds() for c in all_climbs]
            
            learner.avg_climb_height = statistics.mean(gains) if gains else 0.0
            learner.avg_climb_duration = timedelta(seconds=statistics.mean(durations)) if durations else timedelta(hours=1)
            learner.avg_efficiency = statistics.mean([c.climb_efficiency() for c in all_climbs]) if all_climbs else 0.0
            
            # Analyze which Fibonacci levels work best
            fib_stats = {
                0.238: sum(1 for c in all_climbs if 0.238 in [r[1] for r in enumerate([0.238, 0.382, 0.5, 0.618, 0.786])]) / len(all_climbs),
                0.382: sum(1 for c in all_climbs if "Fibonacci 38.2%" in c.ropes_triggered) / len(all_climbs),
                0.618: sum(1 for c in all_climbs if "Fibonacci 61.8%" in c.ropes_triggered) / len(all_climbs),
            }
            
            # Best level = highest efficiency
            best_level = 0.382  # Default
            efficiencies = [0.0] * 5
            for c in all_climbs:
                if "Fibonacci 38.2%" in c.ropes_triggered:
                    efficiencies[1] = max(efficiencies[1], c.climb_efficiency())
                if "Fibonacci 61.8%" in c.ropes_triggered:
                    efficiencies[3] = max(efficiencies[3], c.climb_efficiency())
            
            if efficiencies[3] > efficiencies[1]:
                best_level = 0.618
            
            learner.best_exit_level = best_level
        
        logger.info(f"🧠 LEARNING UPDATE for {symbol}")
        logger.info(f"   Total Climbs: {learner.total_climbs}")
        logger.info(f"   Success Rate: {learner.successful_climbs / learner.total_climbs:.0%}")
        logger.info(f"   Avg Gain: {learner.avg_climb_height:+.1%}")
        logger.info(f"   Avg Duration: {learner.avg_climb_duration}")
        logger.info(f"   Peak Capture Efficiency: {learner.avg_efficiency:.1%}")
        logger.info(f"   Best Exit Level: Fibonacci {learner.best_exit_level:.1%}")
    
    def get_climb_recommendations(self, symbol: str) -> Dict:
        """Get recommendations for optimal climbing strategy."""
        if symbol not in self.learners:
            return {
                'symbol': symbol,
                'recommendation': 'NOT ENOUGH DATA - New symbol',
                'profit_target_pct': 0.382,  # Default to 38.2% Fibonacci
                'optimal_hold_time': timedelta(hours=4)
            }
        
        learner = self.learners[symbol]
        return {
            'symbol': symbol,
            'total_climbs': learner.total_climbs,
            'success_rate': learner.successful_climbs / max(1, learner.total_climbs),
            'avg_climb_pct': f"{learner.avg_climb_height:+.1%}",
            'optimal_profit_target': f"Fibonacci {learner.best_exit_level:.1%}",
            'optimal_hold_time': f"{learner.avg_climb_duration.total_seconds() / 3600:.1f} hours",
            'peak_capture_efficiency': f"{learner.avg_efficiency:.1%}",
            'recommendation': f"Target +{learner.best_exit_level:.1%} gain, hold ~{learner.avg_climb_duration.total_seconds() / 3600:.1f}h"
        }
    
    def _save_state(self):
        """Save climbing state to file."""
        try:
            state = {
                'timestamp': datetime.now().isoformat(),
                'base_camps': {
                    symbol: asdict(camp) for symbol, camp in self.base_camps.items()
                },
                'learners': {
                    symbol: asdict(learner) for symbol, learner in self.learners.items()
                },
                'completed_climbs_count': {
                    symbol: len(climbs) for symbol, climbs in self.completed_climbs.items()
                }
            }
            
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save climbing state: {e}")
    
    def _load_state(self):
        """Load climbing state from file."""
        if not self.state_file.exists():
            logger.info("⛰️ No previous climbing state found. Starting fresh!")
            return
        
        try:
            with open(self.state_file) as f:
                state = json.load(f)
            
            logger.info(f"⛰️ Loaded climbing history with {len(state.get('learners', {}))} mountains learned!")
        except Exception as e:
            logger.warning(f"Could not load climbing state: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# 🧪 TEST & DEMONSTRATION
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
    )
    
    print("\n" + "=" * 100)
    print("⛰️ MOUNTAIN CLIMBER ENGINE - LEARNING TO CLIMB")
    print("=" * 100 + "\n")
    
    climber = MountainClimber()
    
    # Establish a base camp
    climber.establish_base_camp(
        symbol="BTC/USDT",
        entry_price=60000.0,
        quantity=0.01,
        cost_basis=600.0
    )
    
    # Simulate a climb
    print("\n📈 SIMULATING A CLIMB:\n")
    prices = [60000, 61000, 62000, 63000, 63500, 64500, 65000, 64800, 64500]
    for price in prices:
        result = climber.update_climb("BTC/USDT", price)
        print(f"  Price: ${price:>7.0f} | Gain: {result['current_gain_pct']:>+6.2%} | Peak: ${result['peak_price']:>7.0f}")
        if result['ropes_triggered']:
            print(f"    🎯 PROFIT TARGETS HIT: {', '.join(result['ropes_triggered'])}")
    
    # Close the climb
    print()
    climb = climber.close_climb("BTC/USDT", exit_price=64500.0)
    
    # Get recommendations
    print("\n🧠 LEARNING RECOMMENDATIONS:\n")
    rec = climber.get_climb_recommendations("BTC/USDT")
    for key, value in rec.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 100)
    print("✅ MOUNTAIN CLIMBER ENGINE OPERATIONAL")
    print("=" * 100 + "\n")
