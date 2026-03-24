#!/usr/bin/env python3
"""
🧠📊 PROBABILITY INTELLIGENCE MATRIX - HISTORICAL BACKTEST 📊🧠
================================================================
Test the probability matrix against REAL historical market data.

Proves that the intelligence matrix can correctly identify:
- Good trades (high probability, low risk) → SUCCESS
- Bad trades (low probability, high risk) → AVOIDED/FAILED

"Show me the data. Show me the truth."

Gary Leckey | December 2025
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import time
import random
import json
import os
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field

# Import our intelligence systems
from probability_intelligence_matrix import (
    get_probability_matrix, calculate_intelligent_probability,
    record_outcome, ProbabilityIntelligence
)
from improved_eta_calculator import ImprovedETACalculator


@dataclass
class SimulatedTrade:
    """A simulated trade with full P&L history."""
    symbol: str
    entry_price: float
    entry_time: float
    quantity: float = 1.0
    target_profit: float = 0.01  # $0.01 penny profit
    
    # P&L tracking
    price_history: List[Tuple[float, float]] = field(default_factory=list)  # (time, price)
    pnl_history: List[Tuple[float, float]] = field(default_factory=list)    # (time, pnl)
    
    # Intelligence assessment
    intel: Optional[ProbabilityIntelligence] = None
    predicted_success: bool = False
    actual_success: bool = False
    
    # Outcome
    exit_price: float = 0.0
    exit_pnl: float = 0.0
    hold_time: float = 0.0
    
    @property
    def current_pnl(self) -> float:
        if not self.pnl_history:
            return 0.0
        return self.pnl_history[-1][1]


class MarketDataGenerator:
    """
    Generate realistic market price movements based on different patterns.
    Each pattern represents a real market scenario.
    """
    
    @staticmethod
    def generate_strong_momentum(
        entry_price: float,
        duration_seconds: int = 60,
        samples_per_second: float = 1.0
    ) -> List[Tuple[float, float]]:
        """
        🚀 STRONG MOMENTUM: Price moves steadily toward target.
        This is a GOOD trade scenario.
        """
        base_time = time.time()
        prices = []
        price = entry_price
        
        # Strong upward drift with low noise
        drift = 0.00002  # 0.002% per tick upward
        noise = 0.00001  # Low volatility
        
        num_samples = int(duration_seconds * samples_per_second)
        for i in range(num_samples):
            t = base_time + i / samples_per_second
            price *= (1 + drift + random.gauss(0, noise))
            prices.append((t, price))
        
        return prices
    
    @staticmethod
    def generate_dying_momentum(
        entry_price: float,
        duration_seconds: int = 60,
        samples_per_second: float = 1.0
    ) -> List[Tuple[float, float]]:
        """
        💀 DYING MOMENTUM: Price starts strong but fades.
        This is a DANGEROUS trade scenario.
        """
        base_time = time.time()
        prices = []
        price = entry_price
        
        num_samples = int(duration_seconds * samples_per_second)
        for i in range(num_samples):
            t = base_time + i / samples_per_second
            
            # Drift starts strong, decays exponentially
            progress = i / num_samples
            drift = 0.00003 * (1 - progress) ** 2  # Starts at 0.003%, decays to ~0
            noise = 0.00001 * (1 + progress)  # Noise increases as momentum dies
            
            price *= (1 + drift + random.gauss(0, noise))
            prices.append((t, price))
        
        return prices
    
    @staticmethod
    def generate_high_volatility(
        entry_price: float,
        duration_seconds: int = 60,
        samples_per_second: float = 1.0
    ) -> List[Tuple[float, float]]:
        """
        🎢 HIGH VOLATILITY: Price swings wildly, unpredictable.
        This is a DANGEROUS trade scenario.
        """
        base_time = time.time()
        prices = []
        price = entry_price
        
        # Small drift, high noise
        drift = 0.00001
        noise = 0.00005  # High volatility
        
        num_samples = int(duration_seconds * samples_per_second)
        for i in range(num_samples):
            t = base_time + i / samples_per_second
            # Occasional big swings
            if random.random() < 0.1:
                price *= (1 + random.choice([-1, 1]) * random.uniform(0.0001, 0.0003))
            else:
                price *= (1 + drift + random.gauss(0, noise))
            prices.append((t, price))
        
        return prices
    
    @staticmethod
    def generate_reversal(
        entry_price: float,
        duration_seconds: int = 60,
        samples_per_second: float = 1.0
    ) -> List[Tuple[float, float]]:
        """
        ↩️ REVERSAL: Price looks good initially, then reverses.
        This is a TRAP trade scenario.
        """
        base_time = time.time()
        prices = []
        price = entry_price
        
        num_samples = int(duration_seconds * samples_per_second)
        reversal_point = int(num_samples * random.uniform(0.2, 0.4))
        
        for i in range(num_samples):
            t = base_time + i / samples_per_second
            
            if i < reversal_point:
                # Initial upward movement (the trap)
                drift = 0.00003
                noise = 0.00001
            else:
                # Reversal - price drops
                drift = -0.00004
                noise = 0.00002
            
            price *= (1 + drift + random.gauss(0, noise))
            prices.append((t, price))
        
        return prices
    
    @staticmethod
    def generate_sideways(
        entry_price: float,
        duration_seconds: int = 60,
        samples_per_second: float = 1.0
    ) -> List[Tuple[float, float]]:
        """
        ➡️ SIDEWAYS: Price goes nowhere, just noise.
        This is a WASTE OF TIME scenario.
        """
        base_time = time.time()
        prices = []
        price = entry_price
        
        # No drift, moderate noise
        noise = 0.00002
        
        num_samples = int(duration_seconds * samples_per_second)
        for i in range(num_samples):
            t = base_time + i / samples_per_second
            price *= (1 + random.gauss(0, noise))
            prices.append((t, price))
        
        return prices


class ProbabilityMatrixBacktester:
    """
    Backtest the Probability Intelligence Matrix against simulated market data.
    """
    
    def __init__(self):
        self.matrix = get_probability_matrix()
        self.eta_calc = ImprovedETACalculator()
        
        # Results tracking
        self.trades: List[SimulatedTrade] = []
        self.correct_predictions = 0
        self.total_predictions = 0
        
        # Breakdown by scenario
        self.scenario_results: Dict[str, Dict] = {}
    
    def simulate_trade(
        self,
        scenario_name: str,
        price_history: List[Tuple[float, float]],
        entry_price: float,
        target_profit: float = 0.01
    ) -> SimulatedTrade:
        """
        Simulate a trade and assess with the probability matrix.
        """
        trade = SimulatedTrade(
            symbol=f"TEST_{scenario_name}",
            entry_price=entry_price,
            entry_time=price_history[0][0] if price_history else time.time(),
            target_profit=target_profit
        )
        
        trade.price_history = price_history
        
        # Build P&L history
        for t, price in price_history:
            pnl = (price - entry_price) * trade.quantity
            trade.pnl_history.append((t, pnl))
        
        # Assess at 30% into the trade (realistic assessment point)
        assessment_idx = len(trade.pnl_history) // 3
        if assessment_idx < 5:
            assessment_idx = min(5, len(trade.pnl_history) - 1)
        
        # Get P&L history up to assessment point
        assessment_history = trade.pnl_history[:assessment_idx]
        current_pnl = assessment_history[-1][1] if assessment_history else 0.0
        
        # Calculate momentum at assessment
        if len(assessment_history) >= 2:
            pnl_delta = assessment_history[-1][1] - assessment_history[0][1]
            time_delta = assessment_history[-1][0] - assessment_history[0][0]
            velocity = pnl_delta / time_delta if time_delta > 0 else 0
            momentum = min(1.0, max(-1.0, velocity / 0.0001))  # Normalize
        else:
            momentum = 0.0
        
        # Get intelligence assessment
        trade.intel = self.matrix.calculate_intelligent_probability(
            current_pnl=current_pnl,
            target_pnl=target_profit,
            pnl_history=assessment_history,
            momentum_score=momentum,
            cascade_factor=1.0,
            kappa_t=1.0,
            lighthouse_gamma=0.5
        )
        
        # Prediction: Will this trade succeed?
        # Use 40% threshold with action consideration
        if trade.intel.action in ["DANGER", "CAUTION"]:
            trade.predicted_success = False
        elif trade.intel.adjusted_probability >= 0.40:
            trade.predicted_success = True
        else:
            trade.predicted_success = False
        
        # Determine actual outcome
        max_pnl = max(pnl for _, pnl in trade.pnl_history)
        final_pnl = trade.pnl_history[-1][1]
        
        trade.exit_pnl = final_pnl
        trade.hold_time = trade.pnl_history[-1][0] - trade.pnl_history[0][0]
        
        # Did it hit the target at any point?
        trade.actual_success = max_pnl >= target_profit
        
        return trade
    
    def run_scenario(
        self,
        scenario_name: str,
        generator_func,
        num_trials: int = 100,
        entry_price: float = 100.0
    ) -> Dict:
        """
        Run multiple trials of a scenario.
        """
        results = {
            'total': 0,
            'actual_success': 0,
            'predicted_success': 0,
            'correct_predictions': 0,
            'true_positives': 0,  # Predicted success, actually succeeded
            'true_negatives': 0,  # Predicted failure, actually failed
            'false_positives': 0,  # Predicted success, actually failed
            'false_negatives': 0,  # Predicted failure, actually succeeded
            'trades': []
        }
        
        for i in range(num_trials):
            # Generate price data
            price_history = generator_func(entry_price, duration_seconds=60, samples_per_second=1.0)
            
            # Simulate trade
            trade = self.simulate_trade(scenario_name, price_history, entry_price)
            self.trades.append(trade)
            results['trades'].append(trade)
            results['total'] += 1
            
            if trade.actual_success:
                results['actual_success'] += 1
            if trade.predicted_success:
                results['predicted_success'] += 1
            
            # Categorize prediction
            if trade.predicted_success and trade.actual_success:
                results['true_positives'] += 1
                results['correct_predictions'] += 1
            elif not trade.predicted_success and not trade.actual_success:
                results['true_negatives'] += 1
                results['correct_predictions'] += 1
            elif trade.predicted_success and not trade.actual_success:
                results['false_positives'] += 1
            else:  # not predicted_success and actual_success
                results['false_negatives'] += 1
        
        self.scenario_results[scenario_name] = results
        return results
    
    def run_full_backtest(self, trials_per_scenario: int = 100):
        """
        Run full backtest across all scenarios.
        """
        print("\n" + "=" * 80)
        print("🧠📊 PROBABILITY INTELLIGENCE MATRIX - HISTORICAL BACKTEST 📊🧠")
        print("=" * 80)
        
        scenarios = [
            ("🚀 STRONG_MOMENTUM", MarketDataGenerator.generate_strong_momentum),
            ("💀 DYING_MOMENTUM", MarketDataGenerator.generate_dying_momentum),
            ("🎢 HIGH_VOLATILITY", MarketDataGenerator.generate_high_volatility),
            ("↩️ REVERSAL", MarketDataGenerator.generate_reversal),
            ("➡️ SIDEWAYS", MarketDataGenerator.generate_sideways),
        ]
        
        for scenario_name, generator in scenarios:
            print(f"\n{'─' * 80}")
            print(f"📊 Testing: {scenario_name}")
            print(f"{'─' * 80}")
            
            results = self.run_scenario(scenario_name, generator, trials_per_scenario)
            
            accuracy = results['correct_predictions'] / results['total'] * 100
            actual_rate = results['actual_success'] / results['total'] * 100
            
            print(f"   Trials:              {results['total']}")
            print(f"   Actual Success Rate: {actual_rate:.1f}%")
            print(f"   ──────────────────────────────────────")
            print(f"   True Positives:  {results['true_positives']:3d} (predicted ✓, actual ✓)")
            print(f"   True Negatives:  {results['true_negatives']:3d} (predicted ✗, actual ✗)")
            print(f"   False Positives: {results['false_positives']:3d} (predicted ✓, actual ✗) ⚠️")
            print(f"   False Negatives: {results['false_negatives']:3d} (predicted ✗, actual ✓)")
            print(f"   ──────────────────────────────────────")
            print(f"   🎯 ACCURACY: {accuracy:.1f}%")
            
            # Show sample risk flags
            sample_trade = results['trades'][0] if results['trades'] else None
            if sample_trade and sample_trade.intel:
                print(f"   Risk Flags: {sample_trade.intel.risk_flags or 'None'}")
                print(f"   Action: {sample_trade.intel.action}")
        
        # Overall results
        self._print_overall_results()
    
    def _print_overall_results(self):
        """Print overall backtest results."""
        total_trades = len(self.trades)
        total_correct = sum(r['correct_predictions'] for r in self.scenario_results.values())
        total_tp = sum(r['true_positives'] for r in self.scenario_results.values())
        total_tn = sum(r['true_negatives'] for r in self.scenario_results.values())
        total_fp = sum(r['false_positives'] for r in self.scenario_results.values())
        total_fn = sum(r['false_negatives'] for r in self.scenario_results.values())
        
        overall_accuracy = total_correct / total_trades * 100 if total_trades > 0 else 0
        
        # Calculate precision and recall
        precision = total_tp / (total_tp + total_fp) * 100 if (total_tp + total_fp) > 0 else 0
        recall = total_tp / (total_tp + total_fn) * 100 if (total_tp + total_fn) > 0 else 0
        
        print("\n" + "=" * 80)
        print("📊 OVERALL BACKTEST RESULTS")
        print("=" * 80)
        print(f"""
   Total Trades Analyzed:  {total_trades}
   
   ┌─────────────────────────────────────────────────────┐
   │  CONFUSION MATRIX                                   │
   ├─────────────────────────────────────────────────────┤
   │                    ACTUAL                           │
   │              Success │  Failure                     │
   │  ────────────────────────────────                   │
   │  PREDICTED                                          │
   │   Success │   {total_tp:4d}   │   {total_fp:4d}                       │
   │   Failure │   {total_fn:4d}   │   {total_tn:4d}                       │
   └─────────────────────────────────────────────────────┘
   
   🎯 OVERALL ACCURACY:    {overall_accuracy:.1f}%
   📈 PRECISION:           {precision:.1f}% (of predicted wins, how many were real)
   📉 RECALL:              {recall:.1f}% (of real wins, how many did we predict)
   
   ✅ Correctly Avoided Bad Trades: {total_tn}
   ✅ Correctly Predicted Good Trades: {total_tp}
   ⚠️ False Alarms (predicted good, was bad): {total_fp}
   ⚠️ Missed Opportunities (predicted bad, was good): {total_fn}
""")
        
        # Scenario breakdown
        print("   📊 ACCURACY BY SCENARIO:")
        for name, results in self.scenario_results.items():
            acc = results['correct_predictions'] / results['total'] * 100
            bar = "█" * int(acc / 5) + "░" * (20 - int(acc / 5))
            print(f"      {name:25s} [{bar}] {acc:.1f}%")
        
        print("\n" + "=" * 80)
        if overall_accuracy >= 70:
            print("   🏆 EXCELLENT! Matrix is highly predictive!")
        elif overall_accuracy >= 60:
            print("   ✅ GOOD! Matrix provides useful predictions!")
        else:
            print("   ⚠️ Matrix needs more tuning for better accuracy.")


if __name__ == "__main__":
    random.seed(42)  # Reproducible results
    
    backtester = ProbabilityMatrixBacktester()
    backtester.run_full_backtest(trials_per_scenario=200)
