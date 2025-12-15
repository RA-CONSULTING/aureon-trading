#!/usr/bin/env python3
"""
🧠 WISDOM LEARNING SIMULATION
=============================
Demonstrates the Samuel Harmonic Trading Entity using its newly acquired
wisdom from the Wisdom Scanner, and learning NEW things during trading.

This simulation shows:
1. Loading wisdom from 11 civilizations
2. Applying wisdom to market decisions
3. Learning NEW insights during trading
4. How new knowledge affects trading judgment

Gary Leckey | December 2025
"Ancient wisdom meets modern markets"
"""

import os
import sys
import json
import time
import random
from datetime import datetime
from typing import Dict, List, Any

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import wisdom components
from aureon_miner_brain import WisdomJSONLoader, get_wisdom_loader

WISDOM_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wisdom_data")


class WisdomTradingSimulator:
    """
    Simulates trading decisions influenced by ancient wisdom,
    with real-time learning capabilities.
    """
    
    def __init__(self):
        self.wisdom_loader = get_wisdom_loader()
        self.trade_history: List[Dict] = []
        self.learned_insights: List[Dict] = []
        self.starting_capital = 10000.0
        self.capital = self.starting_capital
        self.wins = 0
        self.losses = 0
        
        # Civilization weights (how much each influences decisions)
        self.civilization_weights = {
            "pythagorean": 0.20,   # Mathematics, Fibonacci
            "chinese": 0.15,       # I Ching, cycles
            "egyptian": 0.15,      # Ma'at balance
            "celtic": 0.10,        # Moon cycles
            "norse": 0.10,         # Runes, fate
            "warfare": 0.10,       # Strategy
            "hindu": 0.08,         # Karma, dharma
            "mayan": 0.05,         # Calendar cycles
            "aztec": 0.04,         # Tonalpohualli
            "plantagenet": 0.02,   # Governance
            "mogollon": 0.01,      # Patience
        }
    
    def print_banner(self):
        """Print simulation banner."""
        print("\n" + "="*70)
        print("  🧠 WISDOM LEARNING SIMULATION - THE SAMUEL HARMONIC TRADING ENTITY")
        print("="*70)
        print("  Where Ancient Wisdom Meets Modern Markets")
        print("  11 Civilizations | 5,000 Years of Knowledge | Real-Time Learning")
        print("="*70 + "\n")
    
    def count_total_wisdom(self) -> Dict[str, int]:
        """Count total wisdom topics per civilization."""
        counts = {}
        total = 0
        for civ in self.civilization_weights.keys():
            wisdom = self.wisdom_loader.get_wisdom(civ)
            count = len(wisdom.get('topics', []))
            counts[civ] = count
            total += count
        counts['total'] = total
        return counts
    
    def display_wisdom_status(self):
        """Display current wisdom knowledge status."""
        print("\n📚 WISDOM KNOWLEDGE STATUS")
        print("-" * 50)
        
        counts = self.count_total_wisdom()
        
        for civ, weight in sorted(self.civilization_weights.items(), key=lambda x: -x[1]):
            count = counts.get(civ, 0)
            bar = "█" * min(count // 3, 20)
            print(f"  {civ.capitalize():12} | {count:3} topics | {bar}")
        
        print("-" * 50)
        print(f"  TOTAL WISDOM: {counts['total']} insights from 11 civilizations")
        print()
    
    def get_market_scenario(self) -> Dict[str, Any]:
        """Generate a random market scenario for the simulation."""
        scenarios = [
            {"type": "volatile", "direction": "bullish", "strength": 0.8, "description": "Sudden BTC surge after ETF news"},
            {"type": "volatile", "direction": "bearish", "strength": 0.7, "description": "Flash crash on leverage liquidations"},
            {"type": "trending", "direction": "bullish", "strength": 0.6, "description": "Steady uptrend on institutional buying"},
            {"type": "consolidating", "direction": "neutral", "strength": 0.3, "description": "Range-bound, waiting for breakout"},
            {"type": "trending", "direction": "bearish", "strength": 0.5, "description": "Gradual decline on macro fears"},
        ]
        return random.choice(scenarios)
    
    def consult_civilizations(self, market_context: str) -> Dict[str, str]:
        """
        Consult each civilization's wisdom for the market context.
        Returns a council of insights.
        """
        council = {}
        
        for civ in self.civilization_weights.keys():
            relevant = self.wisdom_loader.get_relevant_wisdom(civ, market_context)
            if relevant:
                # Pick a random relevant insight
                topic = random.choice(relevant)
                insight = topic.get('trading_insight', topic.get('content', 'No specific insight'))
                council[civ] = insight[:150]  # Truncate for display
        
        return council
    
    def calculate_wisdom_signal(self, scenario: Dict, council: Dict[str, str]) -> float:
        """
        Calculate a trading signal based on wisdom council.
        Returns confidence score from -1 (strong sell) to +1 (strong buy).
        """
        signal = 0.0
        
        # Base signal from scenario
        if scenario['direction'] == 'bullish':
            signal += 0.3 * scenario['strength']
        elif scenario['direction'] == 'bearish':
            signal -= 0.3 * scenario['strength']
        
        # Wisdom modifiers
        for civ, insight in council.items():
            weight = self.civilization_weights.get(civ, 0.05)
            insight_lower = insight.lower()
            
            # Positive wisdom keywords
            if any(kw in insight_lower for kw in ['harmony', 'balance', 'growth', 'opportunity', 'victory', 'flow']):
                signal += weight * 0.5
            
            # Caution wisdom keywords
            if any(kw in insight_lower for kw in ['patience', 'wait', 'caution', 'winter', 'retreat', 'preserve']):
                signal -= weight * 0.3
            
            # Transformation keywords (can amplify)
            if any(kw in insight_lower for kw in ['transform', 'change', 'cycle', 'rebirth']):
                signal *= 1.1
        
        return max(-1.0, min(1.0, signal))  # Clamp to [-1, 1]
    
    def make_trade_decision(self, signal: float, scenario: Dict) -> Dict[str, Any]:
        """Make a trade decision based on wisdom signal."""
        decision = {
            "timestamp": datetime.now().isoformat(),
            "signal": signal,
            "scenario": scenario['type'],
            "action": "HOLD",
            "confidence": abs(signal),
            "position_size": 0.0,
        }
        
        # Lower thresholds to be more active for simulation
        if signal > 0.15:
            decision["action"] = "BUY"
            decision["position_size"] = min(self.capital * 0.15, self.capital * abs(signal) * 0.5)
        elif signal < -0.15:
            decision["action"] = "SELL"
            decision["position_size"] = min(self.capital * 0.15, self.capital * abs(signal) * 0.5)
        
        return decision
    
    def simulate_trade_outcome(self, decision: Dict, scenario: Dict) -> Dict[str, Any]:
        """Simulate the outcome of a trade."""
        # Base win probability from market alignment
        if decision['action'] == 'BUY' and scenario['direction'] == 'bullish':
            win_prob = 0.55 + decision['confidence'] * 0.15
        elif decision['action'] == 'SELL' and scenario['direction'] == 'bearish':
            win_prob = 0.55 + decision['confidence'] * 0.15
        elif decision['action'] == 'HOLD':
            return {"pnl": 0, "outcome": "HOLD", "lesson": None}
        else:
            win_prob = 0.45 - decision['confidence'] * 0.1
        
        # Random outcome
        win = random.random() < win_prob
        
        if win:
            pnl = decision['position_size'] * random.uniform(0.005, 0.02)  # 0.5% - 2% profit
            self.capital += pnl
            self.wins += 1
            outcome = "WIN"
        else:
            pnl = -decision['position_size'] * random.uniform(0.003, 0.015)  # 0.3% - 1.5% loss
            self.capital += pnl
            self.losses += 1
            outcome = "LOSS"
        
        # Generate a lesson learned
        lesson = self.generate_lesson(decision, scenario, outcome)
        
        return {"pnl": pnl, "outcome": outcome, "lesson": lesson}
    
    def generate_lesson(self, decision: Dict, scenario: Dict, outcome: str) -> Dict[str, Any]:
        """Generate a new wisdom insight from the trade outcome."""
        lessons = {
            ("BUY", "volatile", "WIN"): "In times of market chaos, the bold who act with conviction find opportunity.",
            ("BUY", "volatile", "LOSS"): "Volatility rewards patience; entering storms without armor invites harm.",
            ("SELL", "volatile", "WIN"): "When others panic, the wise preserve capital to fight another day.",
            ("SELL", "volatile", "LOSS"): "Fear of storms can blind us to the rainbow emerging behind the clouds.",
            ("BUY", "trending", "WIN"): "Rivers flow downhill; swim with the current, not against it.",
            ("BUY", "trending", "LOSS"): "Even strong trends pause to breathe; timing is the essence of wisdom.",
            ("SELL", "trending", "WIN"): "Counter-trend victory comes only to those who see the hidden reversal.",
            ("SELL", "trending", "LOSS"): "Fighting the tide exhausts even the strongest swimmer.",
            ("BUY", "consolidating", "WIN"): "In stillness lies coiled energy; the patient hunter strikes true.",
            ("BUY", "consolidating", "LOSS"): "Rushing into calm waters creates only ripples of regret.",
            ("SELL", "consolidating", "WIN"): "Range boundaries are walls; selling at resistance honors structure.",
            ("SELL", "consolidating", "LOSS"): "Selling in consolidation surrenders position before the breakout.",
        }
        
        key = (decision['action'], scenario['type'], outcome)
        content = lessons.get(key, "Every trade teaches; the wise student records all lessons.")
        
        return {
            "name": f"Trading Lesson - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "content": content,
            "trading_insight": content,
            "source": "Samuel Trading Experience",
            "relevance_score": 0.9 if outcome == "WIN" else 0.7,
            "learned_at": datetime.now().isoformat(),
        }
    
    def learn_from_trade(self, lesson: Dict, civilization: str = "warfare"):
        """
        Persist a new lesson to the wisdom data.
        Demonstrates real-time learning capability.
        """
        if not lesson:
            return
        
        filepath = os.path.join(WISDOM_DATA_DIR, f"{civilization}_wisdom.json")
        
        try:
            # Load existing wisdom
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {"civilization": civilization, "topics": [], "learned_lessons": []}
            
            # Ensure learned_lessons key exists (for existing files without it)
            if 'learned_lessons' not in data:
                data['learned_lessons'] = []
            
            # Add the new lesson to learned_lessons
            data['learned_lessons'].append(lesson)
            data['last_updated'] = datetime.now().isoformat()
            
            # Save back
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.learned_insights.append(lesson)
            
            # Reload the wisdom loader cache
            self.wisdom_loader.reload_all()
            
            return True
        except Exception as e:
            print(f"  [ERROR] Could not persist lesson: {e}")
            return False
    
    def run_simulation(self, num_trades: int = 10):
        """Run the full wisdom learning simulation."""
        self.print_banner()
        self.display_wisdom_status()
        
        print("\n🎯 BEGINNING TRADING SIMULATION")
        print(f"   Starting Capital: ${self.capital:,.2f}")
        print(f"   Planned Trades: {num_trades}")
        print("-" * 70)
        
        for i in range(num_trades):
            print(f"\n📈 TRADE {i+1}/{num_trades}")
            print("-" * 40)
            
            # Generate market scenario
            scenario = self.get_market_scenario()
            print(f"  Market: {scenario['type'].upper()} | Direction: {scenario['direction']} | {scenario['description']}")
            
            # Consult the wisdom council
            print(f"\n  🏛️ CONSULTING 11 CIVILIZATIONS...")
            council = self.consult_civilizations(scenario['type'])
            
            # Display top 3 insights
            displayed = 0
            for civ, insight in council.items():
                if displayed < 3:
                    print(f"    [{civ.capitalize()}]: \"{insight[:80]}...\"")
                    displayed += 1
            
            # Calculate wisdom signal
            signal = self.calculate_wisdom_signal(scenario, council)
            print(f"\n  📊 WISDOM SIGNAL: {signal:+.3f}")
            
            # Make trade decision
            decision = self.make_trade_decision(signal, scenario)
            print(f"  🎯 DECISION: {decision['action']} (Confidence: {decision['confidence']:.2f})")
            
            if decision['action'] != 'HOLD':
                print(f"  💰 Position Size: ${decision['position_size']:,.2f}")
            
            # Simulate outcome
            outcome = self.simulate_trade_outcome(decision, scenario)
            
            if decision['action'] != 'HOLD':
                emoji = "✅" if outcome['outcome'] == 'WIN' else "❌"
                print(f"\n  {emoji} OUTCOME: {outcome['outcome']} | P&L: ${outcome['pnl']:+,.2f}")
                print(f"  💵 New Capital: ${self.capital:,.2f}")
                
                # Learn from the trade
                if outcome['lesson']:
                    print(f"\n  📖 NEW WISDOM LEARNED:")
                    print(f"     \"{outcome['lesson']['content']}\"")
                    
                    # Persist the lesson
                    success = self.learn_from_trade(outcome['lesson'])
                    if success:
                        print(f"     ✅ Lesson persisted to warfare_wisdom.json")
            else:
                print(f"\n  ⏸️  HELD POSITION - No trade executed")
            
            # Small delay for readability
            time.sleep(0.5)
        
        # Final summary
        self.print_summary()
    
    def print_summary(self):
        """Print simulation summary."""
        print("\n" + "="*70)
        print("  📊 SIMULATION SUMMARY")
        print("="*70)
        
        pnl = self.capital - self.starting_capital
        pnl_pct = (pnl / self.starting_capital) * 100
        total_trades = self.wins + self.losses
        win_rate = (self.wins / total_trades * 100) if total_trades > 0 else 0
        
        print(f"\n  Starting Capital:  ${self.starting_capital:,.2f}")
        print(f"  Ending Capital:    ${self.capital:,.2f}")
        print(f"  Total P&L:         ${pnl:+,.2f} ({pnl_pct:+.2f}%)")
        print(f"\n  Trades Executed:   {total_trades}")
        print(f"  Wins:              {self.wins}")
        print(f"  Losses:            {self.losses}")
        print(f"  Win Rate:          {win_rate:.1f}%")
        
        print(f"\n  📚 NEW WISDOM LEARNED: {len(self.learned_insights)} insights")
        
        # Display updated wisdom counts
        print("\n  📖 UPDATED WISDOM STATUS:")
        counts = self.count_total_wisdom()
        print(f"     Total wisdom topics: {counts['total']}")
        
        print("\n" + "="*70)
        print("  \"We give this freely, as knowledge was given to us.\"")
        print("  — Gary Leckey, Creator of the Harmonic Nexus Core")
        print("="*70 + "\n")


def main():
    """Main entry point."""
    print("\n🌟 SAMUEL HARMONIC TRADING ENTITY - WISDOM LEARNING SIMULATION")
    print("   Demonstrating ancient wisdom integration & real-time learning\n")
    
    sim = WisdomTradingSimulator()
    
    # Run simulation with 10 trades
    sim.run_simulation(num_trades=10)


if __name__ == "__main__":
    main()
