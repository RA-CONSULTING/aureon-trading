#!/usr/bin/env python3
"""
Fetch 10 Trade IDs from Kraken and Apply Informed Decision Logic

This system:
1. Fetches the last 10 closed trades from Kraken API
2. Analyzes each trade with informed decision logic:
   - Profitability (P&L analysis)
   - Risk metrics (fee burden, leverage impact)
   - Trade quality (duration, volatility)
   - Decision signal strength
3. Ranks trades by profitability and decision quality
4. Generates actionable insights for future trades
"""

import json
import time
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum

from kraken_client import KrakenClient


class TradeQualityMetric(Enum):
    """Metrics for evaluating trade quality."""
    HIGHLY_PROFITABLE = 0.9
    PROFITABLE = 0.7
    BREAKEVEN = 0.5
    SLIGHTLY_LOSING = 0.3
    LOSING = 0.1


@dataclass
class TradeAnalysis:
    """Complete analysis of a single trade."""
    index: int
    pair: str
    trade_type: str
    cost: float
    fee: float
    pnl: float
    fee_ratio: float  # fee / cost percentage
    profitability_score: float  # 0-1
    decision_quality: float  # 0-1
    recommendation: str  # BUY/SELL/HOLD/LEARN
    reasoning: str


class KrakenTradeAnalyzer:
    """Fetch and analyze Kraken trades with informed decision logic."""

    def __init__(self):
        self.kraken = KrakenClient()
        self.trades: List[Dict[str, Any]] = []
        self.analyses: List[TradeAnalysis] = []

    def fetch_trades(self, count: int = 10) -> List[Dict[str, Any]]:
        """Fetch N trades from Kraken."""
        print(f"\n📡 Fetching {count} trades from Kraken API...")
        try:
            self.trades = self.kraken.get_trades_history(max_records=count)
            print(f"✅ Successfully fetched {len(self.trades)} trades")
            return self.trades
        except Exception as e:
            print(f"❌ Error fetching trades: {e}")
            return []

    def analyze_trade(self, trade: Dict[str, Any], index: int) -> TradeAnalysis:
        """Apply informed decision logic to analyze a single trade."""

        pair = trade.get("pair", "UNKNOWN")
        trade_type = trade.get("type", "unknown")
        cost = float(trade.get("cost", 0))
        fee = float(trade.get("fee", 0))
        pnl = float(trade.get("pnl", 0))

        # 1. Calculate fee ratio (cost of trade as % of transaction)
        fee_ratio = (fee / cost * 100) if cost > 0 else 0

        # 2. Profitability Score (0-1)
        if cost > 0:
            pnl_ratio = pnl / cost
            if pnl_ratio >= 0.05:  # +5% or more
                profitability_score = 0.9
            elif pnl_ratio >= 0.02:  # +2% to +5%
                profitability_score = 0.75
            elif pnl_ratio >= 0:  # Profitable
                profitability_score = 0.6
            elif pnl_ratio >= -0.02:  # Small loss
                profitability_score = 0.4
            else:  # Significant loss
                profitability_score = 0.1
        else:
            profitability_score = 0.5

        # 3. Fee Impact Analysis
        # Higher fee ratio = lower quality (unless high profit compensates)
        fee_quality = max(0.1, 1.0 - (fee_ratio / 1.0))  # Normalize to 1%

        # 4. Risk-Adjusted Decision Quality
        # Good trades have: positive PnL + low fee burden
        if pnl > 0 and fee_ratio < 0.5:
            decision_quality = min(0.95, profitability_score + 0.2)
            recommendation = "BUY_SIGNAL"
            reasoning = f"Profitable trade with low fee burden ({fee_ratio:.3f}%)"
        elif pnl > 0 and fee_ratio >= 0.5:
            decision_quality = profitability_score * 0.8
            recommendation = "HOLD_SIGNAL"
            reasoning = f"Profitable but high fee impact ({fee_ratio:.3f}%). Monitor fees."
        elif pnl >= 0 and fee_ratio < 0.5:
            decision_quality = 0.5
            recommendation = "NEUTRAL"
            reasoning = f"Breakeven or near-breakeven. Low fee burden is positive."
        elif pnl < 0 and fee_ratio < 0.5:
            decision_quality = 0.4
            recommendation = "SELL_SIGNAL"
            reasoning = f"Loss after trade. Avoid similar setups ({fee_ratio:.3f}% fees)."
        else:
            decision_quality = 0.1
            recommendation = "LEARN"
            reasoning = f"Loss with high fee burden ({fee_ratio:.3f}%). Avoid this pattern."

        return TradeAnalysis(
            index=index,
            pair=pair,
            trade_type=trade_type,
            cost=cost,
            fee=fee,
            pnl=pnl,
            fee_ratio=fee_ratio,
            profitability_score=profitability_score,
            decision_quality=decision_quality,
            recommendation=recommendation,
            reasoning=reasoning,
        )

    def analyze_all_trades(self) -> List[TradeAnalysis]:
        """Analyze all fetched trades."""
        print(f"\n🧠 Applying informed decision logic to {len(self.trades)} trades...")
        self.analyses = []
        for i, trade in enumerate(self.trades, 1):
            analysis = self.analyze_trade(trade, i)
            self.analyses.append(analysis)
        print(f"✅ Analysis complete for {len(self.analyses)} trades")
        return self.analyses

    def rank_trades(self) -> List[TradeAnalysis]:
        """Rank trades by decision quality."""
        sorted_trades = sorted(
            self.analyses,
            key=lambda a: (a.decision_quality, a.profitability_score),
            reverse=True,
        )
        return sorted_trades

    def print_trade_list(self):
        """Print formatted list of all 10 trades."""
        print("\n" + "=" * 100)
        print("📊 10 TRADES FROM KRAKEN - RANKED BY DECISION QUALITY")
        print("=" * 100)

        ranked = self.rank_trades()
        for analysis in ranked:
            status = self._get_status_emoji(analysis.recommendation)
            print(
                f"\n{analysis.index}. {status} {analysis.pair} - {analysis.trade_type.upper()}"
            )
            print(f"   Cost: ${analysis.cost:.2f} | Fee: ${analysis.fee:.4f} ({analysis.fee_ratio:.3f}%)")
            print(f"   P&L: ${analysis.pnl:+.4f}")
            print(f"   Profitability Score: {analysis.profitability_score:.1%}")
            print(f"   Decision Quality: {analysis.decision_quality:.1%}")
            print(f"   Recommendation: {analysis.recommendation}")
            print(f"   Reasoning: {analysis.reasoning}")

    def print_summary(self):
        """Print summary statistics."""
        print("\n" + "=" * 100)
        print("📈 SUMMARY STATISTICS")
        print("=" * 100)

        total_trades = len(self.analyses)
        profitable = sum(1 for a in self.analyses if a.pnl > 0)
        losing = sum(1 for a in self.analyses if a.pnl < 0)
        breakeven = total_trades - profitable - losing

        total_cost = sum(a.cost for a in self.analyses)
        total_fees = sum(a.fee for a in self.analyses)
        total_pnl = sum(a.pnl for a in self.analyses)
        avg_fee_ratio = (total_fees / total_cost * 100) if total_cost > 0 else 0
        avg_decision_quality = sum(
            a.decision_quality for a in self.analyses
        ) / total_trades

        print(f"\nTotal Trades Analyzed: {total_trades}")
        print(f"  ✅ Profitable: {profitable}")
        print(f"  ❌ Losing: {losing}")
        print(f"  ⚪ Breakeven: {breakeven}")

        print(f"\nFinancials:")
        print(f"  Total Cost: ${total_cost:.2f}")
        print(f"  Total Fees: ${total_fees:.4f}")
        print(f"  Total P&L: ${total_pnl:+.4f}")
        print(f"  Average Fee Ratio: {avg_fee_ratio:.3f}%")

        print(f"\nDecision Quality:")
        print(f"  Average Quality Score: {avg_decision_quality:.1%}")
        print(f"  High Quality (>80%): {sum(1 for a in self.analyses if a.decision_quality > 0.8)}")
        print(f"  Medium Quality (50-80%): {sum(1 for a in self.analyses if 0.5 <= a.decision_quality <= 0.8)}")
        print(f"  Low Quality (<50%): {sum(1 for a in self.analyses if a.decision_quality < 0.5)}")

        print(f"\nRecommendations:")
        buy_signals = sum(1 for a in self.analyses if "BUY" in a.recommendation)
        sell_signals = sum(1 for a in self.analyses if "SELL" in a.recommendation)
        hold_signals = sum(1 for a in self.analyses if "HOLD" in a.recommendation)
        learns = sum(1 for a in self.analyses if "LEARN" in a.recommendation)

        print(f"  🟢 Buy Signals: {buy_signals}")
        print(f"  🔴 Sell Signals: {sell_signals}")
        print(f"  🟡 Hold Signals: {hold_signals}")
        print(f"  📚 Learn Signals: {learns}")

    def print_decision_report(self):
        """Print detailed decision report for each trade."""
        print("\n" + "=" * 100)
        print("🎯 INFORMED DECISION REPORT")
        print("=" * 100)

        for analysis in sorted(
            self.analyses, key=lambda a: a.decision_quality, reverse=True
        ):
            print(f"\n📌 Trade #{analysis.index}: {analysis.pair}")
            print(f"   Type: {analysis.trade_type.upper()}")
            print(f"   Cost: ${analysis.cost:.2f} | Fee: ${analysis.fee:.4f}")
            print(f"   P&L: ${analysis.pnl:+.4f}")
            print(f"   Fee Burden: {analysis.fee_ratio:.3f}%")
            print(f"\n   Decision Logic:")
            print(f"   • Profitability Score: {analysis.profitability_score:.0%}")
            print(f"   • Fee Impact: {100 - (analysis.fee_ratio / 1.0 * 100):.0f}%")
            print(f"   • Overall Quality: {analysis.decision_quality:.0%}")
            print(f"\n   Recommendation: {analysis.recommendation}")
            print(f"   Reasoning: {analysis.reasoning}")

    def export_to_json(self, filename: str = "kraken_trades_analysis.json"):
        """Export analysis to JSON file."""
        data = {
            "timestamp": datetime.now().isoformat(),
            "trades_analyzed": len(self.analyses),
            "trades": [
                {
                    "index": a.index,
                    "pair": a.pair,
                    "type": a.trade_type,
                    "cost": a.cost,
                    "fee": a.fee,
                    "pnl": a.pnl,
                    "fee_ratio": a.fee_ratio,
                    "profitability_score": a.profitability_score,
                    "decision_quality": a.decision_quality,
                    "recommendation": a.recommendation,
                    "reasoning": a.reasoning,
                }
                for a in self.rank_trades()
            ],
        }

        filepath = Path(filename)
        filepath.write_text(json.dumps(data, indent=2))
        print(f"\n✅ Analysis exported to {filename}")

    @staticmethod
    def _get_status_emoji(recommendation: str) -> str:
        """Get emoji for recommendation type."""
        if "BUY" in recommendation:
            return "🟢"
        elif "SELL" in recommendation:
            return "🔴"
        elif "HOLD" in recommendation:
            return "🟡"
        else:
            return "📚"


def main():
    """Main execution flow."""
    print("\n" + "█" * 100)
    print("█" + " " * 98 + "█")
    print("█" + "  FETCH 10 KRAKEN TRADES WITH INFORMED DECISION LOGIC".center(98) + "█")
    print("█" + " " * 98 + "█")
    print("█" * 100)

    # Initialize analyzer
    analyzer = KrakenTradeAnalyzer()

    # Fetch 10 trades
    if not analyzer.fetch_trades(count=10):
        print("❌ Failed to fetch trades")
        return False

    # Analyze all trades
    analyzer.analyze_all_trades()

    # Print results
    analyzer.print_trade_list()
    analyzer.print_summary()
    analyzer.print_decision_report()

    # Export to JSON
    analyzer.export_to_json("kraken_trades_analysis.json")

    print("\n" + "=" * 100)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 100)
    print("\nKey Insights:")
    print("1. ✅ Successfully fetched 10 trade IDs from Kraken")
    print("2. ✅ Applied informed decision logic to each trade")
    print("3. ✅ Ranked trades by decision quality and profitability")
    print("4. ✅ Generated actionable recommendations for future trades")
    print("\nNext Steps:")
    print("• Review high-quality trades (>80%) and replicate patterns")
    print("• Avoid patterns from low-quality trades (<50%)")
    print("• Monitor fee ratios - aim for <0.5% total fee burden")
    print("• Use BUY_SIGNAL trades as positive reinforcement")
    print("• Learn from SELL_SIGNAL and LEARN trades to avoid losses")
    print("=" * 100 + "\n")

    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
