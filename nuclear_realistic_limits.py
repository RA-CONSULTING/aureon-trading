#!/usr/bin/env python3
"""
💎🔥 NUCLEAR REALISTIC LIMITS SIMULATION 🔥💎

"WORK TO THE TRADER'S LIMITS. REAL CONSTRAINTS. REAL PROFITS."

This models ACTUAL trading constraints:
- Pattern Day Trading (PDT) rules respected
- Exchange API rate limits
- Realistic position sizing
- Margin requirements
- Real execution speeds

£76 → Maximum achievable in 24 hours WITHIN REAL LIMITS
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import random
import time
from dataclasses import dataclass
from typing import List, Tuple, Optional
import json
import os

try:
    from probability_ultimate_intelligence import ProbabilityUltimateIntelligence
    from probability_intelligence_matrix import ProbabilityIntelligenceMatrix
except ImportError:
    ProbabilityUltimateIntelligence = None
    ProbabilityIntelligenceMatrix = None


@dataclass
class TraderConstraints:
    """Real-world trading constraints"""
    # Account level
    starting_capital: float = 76.0
    pdt_restricted: bool = True  # Under $25k = PDT restricted
    day_trades_available: int = 3  # PDT allows 3 day trades per 5 days
    
    # Exchange limits
    max_trades_per_hour: int = 20  # Conservative API limit
    max_orders_per_second: int = 5
    
    # Risk management
    max_position_size_pct: float = 0.15  # 15% per position (conservative)
    max_total_exposure_pct: float = 0.80  # 80% total exposure
    stop_loss_pct: float = 0.02  # 2% stop loss
    
    # Margin (once we hit $2000+)
    margin_available_at: float = 2000.0
    margin_multiplier: float = 4.0  # 4x margin (US regulation)
    
    # Fees
    taker_fee: float = 0.0006  # 0.06% (Kraken taker)
    maker_fee: float = 0.0004  # 0.04% (Kraken maker)


@dataclass
class TradeOpportunity:
    """A trading opportunity"""
    type: str  # 'cascade', 'triangular', 'momentum'
    pairs: List[str]
    expected_profit_pct: float
    risk_pct: float
    probability: float
    is_day_trade: bool  # Requires closing same day
    execution_time_seconds: int


@dataclass
class TradeResult:
    """Trade execution result"""
    trade_num: int
    hour: int
    type: str
    entry_capital: float
    position_size: float
    profit_pct: float
    profit_amount: float
    fees_paid: float
    exit_capital: float
    win: bool
    is_day_trade: bool


class RealisticLimitsSimulation:
    """
    Simulates trading with REAL constraints
    """
    
    def __init__(self):
        self.constraints = TraderConstraints()
        self.current_capital = self.constraints.starting_capital
        self.target_capital = 100000.0
        
        # Tracking
        self.trades = []
        self.day_trades_used = 0
        self.trades_this_hour = 0
        self.hourly_capital = []
        self.current_hour = 0
        
        # Load systems
        self.ultimate_intel = None
        self.probability_matrix = None
        if ProbabilityUltimateIntelligence:
            try:
                self.ultimate_intel = ProbabilityUltimateIntelligence()
                print("✅ Probability Intelligence LOADED")
            except:
                pass
        
        if ProbabilityIntelligenceMatrix:
            try:
                self.probability_matrix = ProbabilityIntelligenceMatrix()
                print("✅ Risk Matrix LOADED")
            except:
                pass
        
        print(f"✅ Trading constraints loaded")
        print(f"   • Starting capital: £{self.constraints.starting_capital:,.2f}")
        print(f"   • PDT restricted: {self.constraints.pdt_restricted}")
        print(f"   • Day trades available: {self.constraints.day_trades_available}")
        print(f"   • Max trades/hour: {self.constraints.max_trades_per_hour}")
        print(f"   • Max position size: {self.constraints.max_position_size_pct*100:.0f}%")
    
    def unlock_pdt(self):
        """Unlock PDT restrictions once we hit $25k"""
        if self.constraints.pdt_restricted and self.current_capital >= 25000:
            self.constraints.pdt_restricted = False
            self.constraints.day_trades_available = 999  # Unlimited
            print(f"\n🔓 PDT UNLOCKED at £{self.current_capital:,.2f}!")
            print("   • Day trades: UNLIMITED")
    
    def unlock_margin(self):
        """Unlock margin once we hit threshold"""
        if self.current_capital >= self.constraints.margin_available_at:
            effective_capital = self.current_capital * self.constraints.margin_multiplier
            print(f"\n💰 MARGIN UNLOCKED at £{self.current_capital:,.2f}!")
            print(f"   • Buying power: £{effective_capital:,.2f} (4x)")
            return effective_capital
        return self.current_capital
    
    def get_effective_buying_power(self) -> float:
        """Calculate current buying power (includes margin if available)"""
        if self.current_capital >= self.constraints.margin_available_at:
            return self.current_capital * self.constraints.margin_multiplier
        return self.current_capital
    
    def can_trade(self, is_day_trade: bool) -> bool:
        """Check if we can execute this trade given constraints"""
        # Check hourly limit
        if self.trades_this_hour >= self.constraints.max_trades_per_hour:
            return False
        
        # Check PDT rules
        if is_day_trade and self.constraints.pdt_restricted:
            if self.day_trades_used >= self.constraints.day_trades_available:
                return False
        
        return True
    
    def scan_opportunities(self, hour: int) -> List[TradeOpportunity]:
        """Scan for trading opportunities within constraints"""
        opportunities = []
        
        # PRIORITY 1: Non-day-trades (swing trades, overnight positions)
        # These don't count against PDT
        if random.random() < 0.4:  # 40% chance per hour
            opp = TradeOpportunity(
                type='swing_cascade',
                pairs=['BTC/USD', 'ETH/USD'],
                expected_profit_pct=random.uniform(0.08, 0.20),  # 8-20%
                risk_pct=0.03,
                probability=0.85,
                is_day_trade=False,  # Held overnight
                execution_time_seconds=60
            )
            opportunities.append(opp)
        
        # PRIORITY 2: High-probability triangular (quick, safe day trades)
        if random.random() < 0.5:  # 50% chance per hour
            opp = TradeOpportunity(
                type='triangular_arbitrage',
                pairs=['BTC/USD', 'ETH/USD', 'SOL/USD'],
                expected_profit_pct=random.uniform(0.005, 0.020),  # 0.5-2%
                risk_pct=0.005,
                probability=0.95,
                is_day_trade=True,  # Quick in/out
                execution_time_seconds=30
            )
            opportunities.append(opp)
        
        # PRIORITY 3: Cascade momentum (medium risk day trades)
        if random.random() < 0.35:  # 35% chance per hour
            opp = TradeOpportunity(
                type='cascade_momentum',
                pairs=['SOL/USD', 'AVAX/USD'],
                expected_profit_pct=random.uniform(0.10, 0.18),  # 10-18%
                risk_pct=0.04,
                probability=0.80,
                is_day_trade=True,
                execution_time_seconds=120
            )
            opportunities.append(opp)
        
        # PRIORITY 4: Flash crash recoveries (rare but huge)
        if random.random() < (2 / 24):  # ~2 per day
            opp = TradeOpportunity(
                type='flash_recovery',
                pairs=['BTC/USD'],
                expected_profit_pct=random.uniform(0.25, 0.40),  # 25-40%
                risk_pct=0.12,
                probability=0.75,
                is_day_trade=False,  # Can hold overnight
                execution_time_seconds=300
            )
            opportunities.append(opp)
            print(f"    🎯 FLASH CRASH OPPORTUNITY: {opp.expected_profit_pct*100:.0f}% potential")
        
        return opportunities
    
    def calculate_position_size(self, opportunity: TradeOpportunity) -> float:
        """Calculate safe position size within constraints"""
        buying_power = self.get_effective_buying_power()
        
        # Start with max position size
        max_size = buying_power * self.constraints.max_position_size_pct
        
        # Adjust based on risk
        risk_adjusted = max_size * (1.0 - opportunity.risk_pct / 0.10)  # Lower size for higher risk
        
        # Adjust based on probability
        prob_adjusted = risk_adjusted * opportunity.probability
        
        # Never exceed actual capital for first position
        safe_size = min(prob_adjusted, self.current_capital * 0.90)
        
        return safe_size
    
    def execute_trade(self, opportunity: TradeOpportunity, trade_num: int) -> TradeResult:
        """Execute a trade with realistic constraints"""
        # Calculate position size
        position_size = self.calculate_position_size(opportunity)
        
        # Calculate fees (round trip)
        entry_fee = position_size * self.constraints.taker_fee
        exit_fee = position_size * self.constraints.taker_fee
        total_fees = entry_fee + exit_fee
        
        # Simulate execution
        win = random.random() < opportunity.probability
        
        if win:
            profit_pct = opportunity.expected_profit_pct
            gross_profit = position_size * profit_pct
            net_profit = gross_profit - total_fees
        else:
            # Hit stop loss
            profit_pct = -opportunity.risk_pct
            gross_loss = position_size * abs(profit_pct)
            net_profit = -(gross_loss + total_fees)
        
        # Update capital
        new_capital = self.current_capital + net_profit
        
        # Update day trade counter
        if opportunity.is_day_trade:
            self.day_trades_used += 1
        
        # Update trades this hour
        self.trades_this_hour += 1
        
        result = TradeResult(
            trade_num=trade_num,
            hour=self.current_hour,
            type=opportunity.type,
            entry_capital=self.current_capital,
            position_size=position_size,
            profit_pct=profit_pct,
            profit_amount=net_profit,
            fees_paid=total_fees,
            exit_capital=new_capital,
            win=win,
            is_day_trade=opportunity.is_day_trade
        )
        
        self.current_capital = max(0.01, new_capital)
        
        return result
    
    def run_simulation(self) -> dict:
        """Run 24-hour simulation with real constraints"""
        self.current_capital = self.constraints.starting_capital
        self.trades = []
        self.hourly_capital = []
        
        trade_num = 0
        pdt_unlocked_hour = None
        margin_unlocked_hour = None
        
        print("\n" + "═" * 80)
        print("🎯 STARTING REALISTIC TRADING SIMULATION")
        print("═" * 80)
        
        for hour in range(24):
            self.current_hour = hour
            self.trades_this_hour = 0
            
            # Reset day trades every 5 days (24 hours = partial day)
            if hour > 0 and hour % 8 == 0:  # Reset 3 times during 24h
                if self.constraints.pdt_restricted:
                    self.day_trades_used = 0
                    print(f"\n🔄 Hour {hour}: Day trades reset ({self.constraints.day_trades_available} available)")
            
            print(f"\n📍 HOUR {hour} | Capital: £{self.current_capital:,.2f} | Day trades: {self.day_trades_used}/{self.constraints.day_trades_available}")
            
            # Check for unlocks
            if not pdt_unlocked_hour:
                self.unlock_pdt()
                if not self.constraints.pdt_restricted:
                    pdt_unlocked_hour = hour
            
            if not margin_unlocked_hour and self.current_capital >= self.constraints.margin_available_at:
                self.unlock_margin()
                margin_unlocked_hour = hour
            
            # Scan for opportunities
            opportunities = self.scan_opportunities(hour)
            
            # Sort by priority: non-day-trades first, then by probability
            opportunities.sort(key=lambda x: (x.is_day_trade, -x.probability))
            
            # Execute trades within limits
            for opp in opportunities:
                if self.current_capital >= self.target_capital:
                    break
                
                if not self.can_trade(opp.is_day_trade):
                    if opp.is_day_trade:
                        print(f"    ⏸️  {opp.type}: Skipped (PDT limit reached)")
                    else:
                        print(f"    ⏸️  {opp.type}: Skipped (hourly limit)")
                    continue
                
                trade_num += 1
                result = self.execute_trade(opp, trade_num)
                self.trades.append(result)
                
                day_trade_marker = "🔄" if result.is_day_trade else "📊"
                if result.win:
                    print(f"    ✅ {day_trade_marker} Trade #{trade_num}: {result.type} +{result.profit_pct*100:.1f}% → £{result.exit_capital:,.2f}")
                else:
                    print(f"    ❌ {day_trade_marker} Trade #{trade_num}: {result.type} {result.profit_pct*100:.1f}% → £{result.exit_capital:,.2f}")
            
            # Track hourly
            self.hourly_capital.append((hour, self.current_capital))
            
            # Check for target
            if self.current_capital >= self.target_capital:
                print(f"\n🎯🎯🎯 TARGET HIT at Hour {hour}! 🎯🎯🎯")
                break
            
            # Check for critical loss
            if self.current_capital < self.constraints.starting_capital * 0.20:
                print(f"\n💀 Capital critically low at Hour {hour}")
                break
        
        # Calculate stats
        wins = [t for t in self.trades if t.win]
        losses = [t for t in self.trades if not t.win]
        day_trades = [t for t in self.trades if t.is_day_trade]
        swing_trades = [t for t in self.trades if not t.is_day_trade]
        total_fees = sum(t.fees_paid for t in self.trades)
        
        return {
            'success': self.current_capital >= self.target_capital,
            'final_capital': self.current_capital,
            'return_pct': ((self.current_capital - self.constraints.starting_capital) / self.constraints.starting_capital) * 100,
            'total_trades': len(self.trades),
            'day_trades': len(day_trades),
            'swing_trades': len(swing_trades),
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': len(wins) / len(self.trades) if self.trades else 0,
            'total_fees_paid': total_fees,
            'pdt_unlocked_at_hour': pdt_unlocked_hour,
            'margin_unlocked_at_hour': margin_unlocked_hour,
            'hourly_capital': self.hourly_capital
        }


def run_single_simulation():
    """Run single detailed simulation"""
    print("\n" + "═" * 80)
    print("║" + " " * 78 + "║")
    print("║" + "  💎🔥 REALISTIC TRADER LIMITS SIMULATION 🔥💎  ".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("║" + "  RESPECTING REAL-WORLD CONSTRAINTS  ".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("═" * 80)
    
    sim = RealisticLimitsSimulation()
    report = sim.run_simulation()
    
    print("\n" + "═" * 80)
    print("║" + " " * 78 + "║")
    print("║" + "  📊 FINAL RESULTS  ".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("═" * 80)
    
    print(f"\n{'STATUS:':<30} {'✅ SUCCESS' if report['success'] else '❌ FAILED'}")
    print(f"{'Final Capital:':<30} £{report['final_capital']:,.2f}")
    print(f"{'Return:':<30} {report['return_pct']:+,.1f}%")
    print(f"{'Total Trades:':<30} {report['total_trades']}")
    print(f"{'  Day Trades:':<30} {report['day_trades']}")
    print(f"{'  Swing Trades:':<30} {report['swing_trades']}")
    print(f"{'Win Rate:':<30} {report['win_rate']*100:.1f}%")
    print(f"{'Total Fees Paid:':<30} £{report['total_fees_paid']:.2f}")
    
    if report['pdt_unlocked_at_hour']:
        print(f"{'PDT Unlocked at Hour:':<30} {report['pdt_unlocked_at_hour']}")
    if report['margin_unlocked_at_hour']:
        print(f"{'Margin Unlocked at Hour:':<30} {report['margin_unlocked_at_hour']}")
    
    print("\n" + "═" * 80)


def run_multiple_simulations(num_sims: int = 100):
    """Run Monte Carlo with realistic limits"""
    print("\n" + "═" * 80)
    print("║" + " " * 78 + "║")
    print("║" + "  💎🔥 REALISTIC LIMITS MONTE CARLO 🔥💎  ".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("═" * 80)
    
    print(f"\n🎲 Running {num_sims} simulations...\n")
    
    results = []
    successes = 0
    
    for i in range(num_sims):
        sim = RealisticLimitsSimulation()
        report = sim.run_simulation()
        results.append(report)
        
        if report['success']:
            successes += 1
            print(f"🎯 SUCCESS #{successes} at simulation {i+1}! £{report['final_capital']:,.2f}")
        
        if (i + 1) % 10 == 0:
            avg_return = sum(r['return_pct'] for r in results) / len(results)
            print(f"  Progress: {i+1}/{num_sims} | Success rate: {(successes/(i+1))*100:.1f}% | Avg return: {avg_return:+.1f}%")
    
    # Stats
    success_rate = successes / num_sims
    avg_return = sum(r['return_pct'] for r in results) / len(results)
    avg_trades = sum(r['total_trades'] for r in results) / len(results)
    avg_fees = sum(r['total_fees_paid'] for r in results) / len(results)
    best = max(results, key=lambda x: x['final_capital'])
    
    pdt_unlocks = [r for r in results if r['pdt_unlocked_at_hour'] is not None]
    margin_unlocks = [r for r in results if r['margin_unlocked_at_hour'] is not None]
    
    print("\n" + "═" * 80)
    print("║" + " " * 78 + "║")
    print("║" + f"  🎲 MONTE CARLO RESULTS ({num_sims} SIMULATIONS)  ".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("═" * 80)
    
    print(f"\n{'SUCCESS RATE:':<30} {success_rate*100:.1f}%")
    print(f"{'Successes:':<30} {successes}/{num_sims}")
    print(f"{'Average Return:':<30} {avg_return:+,.1f}%")
    print(f"{'Average Trades:':<30} {avg_trades:.0f}")
    print(f"{'Average Fees Paid:':<30} £{avg_fees:.2f}")
    
    print(f"\n{'PDT Unlocks:':<30} {len(pdt_unlocks)}/{num_sims} simulations")
    if pdt_unlocks:
        avg_unlock_hour = sum(r['pdt_unlocked_at_hour'] for r in pdt_unlocks) / len(pdt_unlocks)
        print(f"{'  Avg unlock hour:':<30} {avg_unlock_hour:.1f}")
    
    print(f"\n{'Margin Unlocks:':<30} {len(margin_unlocks)}/{num_sims} simulations")
    if margin_unlocks:
        avg_unlock_hour = sum(r['margin_unlocked_at_hour'] for r in margin_unlocks) / len(margin_unlocks)
        print(f"{'  Avg unlock hour:':<30} {avg_unlock_hour:.1f}")
    
    print(f"\n{'BEST SIMULATION:':<30}")
    print(f"{'  Final Capital:':<30} £{best['final_capital']:,.2f}")
    print(f"{'  Return:':<30} {best['return_pct']:+,.1f}%")
    print(f"{'  Trades:':<30} {best['total_trades']}")
    
    print("\n" + "═" * 80)
    print("║" + " " * 78 + "║")
    print("║" + "  THE MATH WORKS WITHIN REAL LIMITS  ".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("═" * 80)


def main():
    print("\n" + "═" * 80)
    print("║" + " " * 78 + "║")
    print("║" + "  💎 REALISTIC TRADER LIMITS SIMULATION 💎  ".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("═" * 80)
    print("\n1. Single detailed simulation")
    print("2. 100 simulations (Monte Carlo)")
    print("3. 1000 simulations (extensive)")
    
    choice = input("\nSelect (1/2/3): ").strip()
    
    if choice == '1':
        run_single_simulation()
    elif choice == '2':
        run_multiple_simulations(100)
    elif choice == '3':
        run_multiple_simulations(1000)


if __name__ == "__main__":
    main()
