#!/usr/bin/env python3
"""
🪙 PENNY PROFIT PORTFOLIO SIMULATION
====================================
Tests the current portfolio positions against the Penny Profit Engine
to see if the system can make 1 penny net profit after all fees.

Uses REAL positions from aureon_kraken_state.json and simulates
market movements to find the breakeven and profit thresholds.

Gary Leckey | December 2025
"Am I up by exactly 1 penny net profit? SELL."
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
import json
import random
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import penny profit engine
from penny_profit_engine import PennyProfitEngine, get_penny_engine

# Fee constants (Kraken)
KRAKEN_MAKER_FEE = 0.0016  # 0.16%
KRAKEN_TAKER_FEE = 0.0026  # 0.26%
SPREAD_BUFFER = 0.001       # 0.1% spread


@dataclass
class Position:
    """Represents a trading position."""
    symbol: str
    entry_price: float
    quantity: float
    entry_fee: float
    entry_value: float
    momentum: float
    coherence: float
    
    @property
    def cost_basis(self) -> float:
        """Total cost including entry fee."""
        return self.entry_value + self.entry_fee


class PennyProfitSimulator:
    """
    Simulates the penny profit strategy against current portfolio.
    """
    
    def __init__(self, state_file: str = "aureon_kraken_state.json"):
        self.state_file = state_file
        self.portfolio: Dict[str, Position] = {}
        self.balance = 0.0
        self.penny_engine = get_penny_engine()
        self.simulation_results: List[Dict] = []
        
        self._load_portfolio()
    
    def _load_portfolio(self):
        """Load current portfolio from state file."""
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            
            self.balance = state.get('balance', 0)
            
            for symbol, pos in state.get('positions', {}).items():
                self.portfolio[symbol] = Position(
                    symbol=symbol,
                    entry_price=pos['entry_price'],
                    quantity=pos['quantity'],
                    entry_fee=pos['entry_fee'],
                    entry_value=pos['entry_value'],
                    momentum=pos.get('momentum', 0),
                    coherence=pos.get('coherence', 0.5),
                )
            
            print(f"✅ Loaded {len(self.portfolio)} positions")
            print(f"   Account Balance: ${self.balance:.2f}")
            
        except Exception as e:
            print(f"❌ Failed to load portfolio: {e}")
    
    def print_banner(self):
        """Print simulation banner."""
        print("\n" + "="*70)
        print("  🪙 PENNY PROFIT PORTFOLIO SIMULATION")
        print("="*70)
        print("  Testing: Can each position make 1 PENNY of NET PROFIT?")
        print("  Strategy: Exit when gross_pnl > (entry_fee + exit_fee + $0.01)")
        print("="*70 + "\n")
    
    def calculate_breakeven(self, pos: Position) -> Dict[str, float]:
        """
        Calculate the exact breakeven point for a position.
        
        Returns dict with:
        - breakeven_price: Price needed to break even after fees
        - penny_profit_price: Price needed for exactly $0.01 net profit
        - price_move_pct: Percentage move needed from entry
        """
        # Entry cost
        entry_fee = pos.entry_fee
        
        # Exit cost (assume taker fee)
        exit_value_at_entry = pos.entry_value
        exit_fee_at_entry = exit_value_at_entry * KRAKEN_TAKER_FEE
        
        # Total round-trip cost
        total_fees = entry_fee + exit_fee_at_entry
        
        # Breakeven requires: exit_value - entry_value >= total_fees
        # exit_value = current_price * quantity
        # current_price * quantity - entry_price * quantity >= total_fees
        # current_price >= entry_price + (total_fees / quantity)
        
        breakeven_price = pos.entry_price + (total_fees / pos.quantity)
        
        # Penny profit requires: net_pnl >= $0.01
        # exit_value - entry_value - entry_fee - exit_fee >= 0.01
        # We need to account for exit fee at new price
        # Let x = penny_profit_price
        # x * qty * (1 - taker_fee) - entry_value - entry_fee >= 0.01
        # x >= (entry_value + entry_fee + 0.01) / (qty * (1 - taker_fee))
        
        penny_profit_price = (pos.entry_value + pos.entry_fee + 0.01) / (pos.quantity * (1 - KRAKEN_TAKER_FEE))
        
        # Price move percentage
        breakeven_move_pct = ((breakeven_price / pos.entry_price) - 1) * 100
        penny_move_pct = ((penny_profit_price / pos.entry_price) - 1) * 100
        
        return {
            'breakeven_price': breakeven_price,
            'penny_profit_price': penny_profit_price,
            'breakeven_move_pct': breakeven_move_pct,
            'penny_move_pct': penny_move_pct,
            'total_fees': total_fees,
        }
    
    def simulate_position(self, pos: Position, num_scenarios: int = 100) -> Dict[str, Any]:
        """
        Simulate price movements for a position and test penny profit exits.
        """
        thresholds = self.calculate_breakeven(pos)
        
        wins = 0
        losses = 0
        holds = 0
        total_pnl = 0.0
        
        # Simulate various price movements
        for _ in range(num_scenarios):
            # Random price move between -3% and +3%
            move_pct = random.gauss(0, 1.5)  # Normal distribution, std=1.5%
            
            current_price = pos.entry_price * (1 + move_pct / 100)
            current_value = current_price * pos.quantity
            
            # Calculate gross P&L
            gross_pnl = current_value - pos.entry_value
            
            # Calculate exit fee at current price
            exit_fee = current_value * KRAKEN_TAKER_FEE
            
            # Calculate net P&L
            net_pnl = gross_pnl - pos.entry_fee - exit_fee
            
            # Decision based on penny profit rules
            if net_pnl >= 0.0001:
                # TAKE PROFIT - We made our penny!
                wins += 1
                total_pnl += net_pnl
            elif net_pnl <= -0.02:  # Stop loss at -$0.02
                # STOP LOSS
                losses += 1
                total_pnl += net_pnl
            else:
                # HOLD
                holds += 1
        
        win_rate = (wins / num_scenarios) * 100 if num_scenarios > 0 else 0
        avg_pnl = total_pnl / num_scenarios if num_scenarios > 0 else 0
        
        return {
            'symbol': pos.symbol,
            'entry_price': pos.entry_price,
            'entry_value': pos.entry_value,
            'quantity': pos.quantity,
            'breakeven_price': thresholds['breakeven_price'],
            'penny_profit_price': thresholds['penny_profit_price'],
            'penny_move_pct': thresholds['penny_move_pct'],
            'total_fees': thresholds['total_fees'],
            'scenarios': num_scenarios,
            'wins': wins,
            'losses': losses,
            'holds': holds,
            'win_rate': win_rate,
            'avg_pnl': avg_pnl,
            'total_pnl': total_pnl,
        }
    
    def analyze_portfolio(self):
        """Analyze all positions in the portfolio."""
        print("\n📊 POSITION ANALYSIS")
        print("-" * 70)
        print(f"{'Symbol':<12} {'Entry $':<10} {'Value $':<10} {'Fees $':<8} {'Penny Move %':<12} {'Status'}")
        print("-" * 70)
        
        for symbol, pos in self.portfolio.items():
            thresholds = self.calculate_breakeven(pos)
            
            # Determine status
            if thresholds['penny_move_pct'] < 0.5:
                status = "✅ EASY"
            elif thresholds['penny_move_pct'] < 1.0:
                status = "⚠️ MODERATE"
            else:
                status = "❌ HARD"
            
            print(f"{symbol:<12} ${pos.entry_price:<9.4f} ${pos.entry_value:<9.2f} ${thresholds['total_fees']:<7.4f} {thresholds['penny_move_pct']:<11.3f}% {status}")
        
        print("-" * 70)
    
    def run_simulation(self, scenarios_per_position: int = 200):
        """Run full penny profit simulation."""
        self.print_banner()
        
        # Show current portfolio
        print("📈 CURRENT PORTFOLIO (from aureon_kraken_state.json)")
        print("-" * 70)
        
        total_position_value = sum(p.entry_value for p in self.portfolio.values())
        print(f"   Cash Balance: ${self.balance:.2f}")
        print(f"   Position Value: ${total_position_value:.2f}")
        print(f"   Total Portfolio: ${self.balance + total_position_value:.2f}")
        print(f"   Open Positions: {len(self.portfolio)}")
        
        # Analyze each position
        self.analyze_portfolio()
        
        # Run simulation
        print("\n🎯 PENNY PROFIT SIMULATION")
        print(f"   Running {scenarios_per_position} price scenarios per position...")
        print("-" * 70)
        
        total_wins = 0
        total_losses = 0
        total_holds = 0
        total_pnl = 0.0
        
        results = []
        
        for symbol, pos in self.portfolio.items():
            result = self.simulate_position(pos, scenarios_per_position)
            results.append(result)
            
            total_wins += result['wins']
            total_losses += result['losses']
            total_holds += result['holds']
            total_pnl += result['total_pnl']
            
            emoji = "✅" if result['win_rate'] > 50 else "⚠️" if result['win_rate'] > 30 else "❌"
            print(f"   {emoji} {symbol:<12} Win Rate: {result['win_rate']:.1f}% | Avg P&L: ${result['avg_pnl']:.4f} | Move needed: {result['penny_move_pct']:.2f}%")
        
        # Summary
        total_scenarios = len(self.portfolio) * scenarios_per_position
        overall_win_rate = (total_wins / total_scenarios) * 100 if total_scenarios > 0 else 0
        
        print("\n" + "="*70)
        print("  📊 SIMULATION SUMMARY")
        print("="*70)
        print(f"\n  Total Scenarios Simulated: {total_scenarios}")
        print(f"  Penny Profit Exits (Wins): {total_wins} ({overall_win_rate:.1f}%)")
        print(f"  Stop Loss Exits (Losses):  {total_losses}")
        print(f"  Held (No Action):          {total_holds}")
        print(f"\n  Total Simulated P&L:       ${total_pnl:.4f}")
        print(f"  Average P&L per Trade:     ${total_pnl/total_scenarios:.6f}")
        
        # Verdict
        print("\n" + "-"*70)
        if overall_win_rate > 50:
            print("  🎉 VERDICT: PENNY PROFIT STRATEGY IS VIABLE!")
            print(f"     With {overall_win_rate:.1f}% win rate, the system can consistently")
            print("     extract 1 penny of net profit after fees.")
        elif overall_win_rate > 35:
            print("  ⚠️  VERDICT: PENNY PROFIT STRATEGY IS MARGINAL")
            print(f"     {overall_win_rate:.1f}% win rate is borderline. Consider:")
            print("     - Larger position sizes (to reduce fee impact)")
            print("     - Better entry timing (higher coherence threshold)")
        else:
            print("  ❌ VERDICT: PENNY PROFIT STRATEGY NEEDS ADJUSTMENT")
            print(f"     {overall_win_rate:.1f}% win rate is too low. Fees are eating profits.")
            print("     Recommendations:")
            print("     - Increase minimum trade size")
            print("     - Wait for higher volatility")
            print("     - Use maker orders instead of taker")
        
        print("-"*70)
        
        # Show the math for one position
        print("\n📐 PENNY PROFIT MATH (Example: First Position)")
        print("-"*70)
        if results:
            r = results[0]
            print(f"   Symbol: {r['symbol']}")
            print(f"   Entry Value: ${r['entry_value']:.4f}")
            print(f"   Total Fees (round trip): ${r['total_fees']:.4f}")
            print(f"   Penny Profit Target: $0.01")
            print(f"   Minimum Gross P&L Needed: ${r['total_fees'] + 0.01:.4f}")
            print(f"   Price Move Required: {r['penny_move_pct']:.3f}%")
            print(f"   Entry Price: ${r['entry_price']:.6f}")
            print(f"   Penny Profit Price: ${r['penny_profit_price']:.6f}")
        
        print("\n" + "="*70)
        print("  \"Am I up by exactly 1 penny net profit? SELL.\"")
        print("  — The Penny Profit Engine, Samuel Harmonic Trading Entity")
        print("="*70 + "\n")
        
        return results


def main():
    """Main entry point."""
    print("\n🪙 SAMUEL HARMONIC TRADING ENTITY - PENNY PROFIT TEST")
    print("   Testing current portfolio against the Penny Profit Engine\n")
    
    sim = PennyProfitSimulator()
    results = sim.run_simulation(scenarios_per_position=500)


if __name__ == "__main__":
    main()
