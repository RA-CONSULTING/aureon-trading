#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                      ║
║     🧪 AUREON CALIBRATION TEST SUITE 🧪                                              ║
║     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                                ║
║                                                                                      ║
║     Paper trading test to calibrate probability thresholds and risk parameters       ║
║                                                                                      ║
║     Tests:                                                                           ║
║       1. Signal accuracy vs actual price movement                                    ║
║       2. Coherence threshold optimization                                            ║
║       3. 6D Harmonic waveform effectiveness                                          ║
║       4. News sentiment impact                                                       ║
║       5. Cross-exchange arbitrage validity                                           ║
║                                                                                      ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
import time
import json
import logging
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from collections import defaultdict

# Set paper mode
os.environ['PAPER_MODE'] = 'true'

# Import the main trader
from aureon_multi_exchange_live import (
    AureonMultiExchangeTrader, 
    CONFIG, 
    calculate_coherence,
    PHI
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('calibration_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class PaperTrade:
    """Record of a paper trade for analysis"""
    id: str
    exchange: str
    symbol: str
    side: str
    entry_price: float
    entry_time: datetime
    quantity: float
    probability: float
    coherence: float
    frequency: float
    asset_class: str
    sentiment: float = 0.0
    harmonic_6d_score: float = 0.0
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    pnl_pct: Optional[float] = None
    pnl_usd: Optional[float] = None
    exit_reason: Optional[str] = None


@dataclass
class CalibrationMetrics:
    """Metrics for calibration analysis"""
    total_signals: int = 0
    trades_taken: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    
    # By probability bucket
    prob_buckets: Dict[str, Dict] = field(default_factory=lambda: {
        '50-60': {'count': 0, 'wins': 0, 'pnl': 0.0},
        '60-70': {'count': 0, 'wins': 0, 'pnl': 0.0},
        '70-80': {'count': 0, 'wins': 0, 'pnl': 0.0},
        '80-90': {'count': 0, 'wins': 0, 'pnl': 0.0},
        '90-100': {'count': 0, 'wins': 0, 'pnl': 0.0},
    })
    
    # By coherence bucket
    coherence_buckets: Dict[str, Dict] = field(default_factory=lambda: {
        '0.70-0.75': {'count': 0, 'wins': 0, 'pnl': 0.0},
        '0.75-0.80': {'count': 0, 'wins': 0, 'pnl': 0.0},
        '0.80-0.85': {'count': 0, 'wins': 0, 'pnl': 0.0},
        '0.85-0.90': {'count': 0, 'wins': 0, 'pnl': 0.0},
        '0.90-1.00': {'count': 0, 'wins': 0, 'pnl': 0.0},
    })
    
    # By asset class
    asset_class_stats: Dict[str, Dict] = field(default_factory=lambda: defaultdict(
        lambda: {'count': 0, 'wins': 0, 'pnl': 0.0}
    ))
    
    # By exchange
    exchange_stats: Dict[str, Dict] = field(default_factory=lambda: defaultdict(
        lambda: {'count': 0, 'wins': 0, 'pnl': 0.0}
    ))
    
    # 6D Harmonic effectiveness
    harmonic_trades: int = 0
    harmonic_wins: int = 0
    harmonic_pnl: float = 0.0
    
    # Sentiment effectiveness
    sentiment_positive_trades: int = 0
    sentiment_positive_wins: int = 0
    sentiment_negative_trades: int = 0
    sentiment_negative_wins: int = 0


class CalibrationTrader(AureonMultiExchangeTrader):
    """Extended trader with calibration tracking"""
    
    def __init__(self):
        super().__init__()
        self.paper_trades: List[PaperTrade] = []
        self.metrics = CalibrationMetrics()
        self.paper_balance = {
            'binance': CONFIG.get('PAPER_BALANCE', 10000.0),
            'kraken': CONFIG.get('PAPER_BALANCE', 10000.0),
            'capital': CONFIG.get('PAPER_BALANCE', 10000.0),
            'alpaca': CONFIG.get('PAPER_BALANCE', 10000.0),
        }
        self.trade_counter = 0
        
    def enter_position(self, opp: Dict):
        """Override to track paper trades"""
        exchange = opp['exchange']
        symbol = opp['symbol']
        
        # Check if we can trade
        if len(self.positions) >= CONFIG['MAX_POSITIONS']:
            return
        
        # Check if we already have a position in this symbol
        key = f"{exchange}:{symbol}"
        if key in self.positions:
            return
        
        # Calculate position size
        balance = self.paper_balance.get(exchange, 0)
        if balance < CONFIG['MIN_TRADE_USD']:
            logger.warning(f"Insufficient paper balance on {exchange}: ${balance:.2f}")
            return
        
        trade_size = min(CONFIG['MIN_TRADE_USD'], balance * 0.25)
        qty = trade_size / opp['price']
        
        # Create paper trade
        self.trade_counter += 1
        trade = PaperTrade(
            id=f"PAPER_{self.trade_counter:04d}",
            exchange=exchange,
            symbol=symbol,
            side='BUY',
            entry_price=opp['price'],
            entry_time=datetime.now(),
            quantity=qty,
            probability=opp['probability'],
            coherence=opp['coherence'],
            frequency=opp.get('frequency', 432),
            asset_class=opp.get('asset_class', 'crypto'),
            sentiment=opp.get('sentiment', 0.0),
            harmonic_6d_score=opp.get('harmonic_6d_score', 0.0),
        )
        
        self.paper_trades.append(trade)
        self.paper_balance[exchange] -= trade_size
        
        # Track in positions
        key = f"{exchange}:{symbol}"
        self.positions[key] = {
            'exchange': exchange,
            'symbol': symbol,
            'qty': qty,
            'entry': opp['price'],
            'entry_time': time.time(),
            'trade_id': trade.id,
        }
        
        self.trades += 1
        self.metrics.total_signals += 1
        self.metrics.trades_taken += 1
        
        logger.info(f"""
╔════════════════════════════════════════════════════════════════╗
║ 📝 PAPER TRADE #{trade.id}
║ [{exchange.upper()}] {symbol}
║ Entry: ${opp['price']:.4f} | Qty: {qty:.6f}
║ Probability: {opp['probability']:.0%} | Coherence: {opp['coherence']:.3f}
║ Sentiment: {opp.get('sentiment', 0):+.2f} | 6D: {opp.get('harmonic_6d_score', 0):.2f}
╚════════════════════════════════════════════════════════════════╝
""")
    
    def check_exits(self):
        """Override to track paper trade exits"""
        for key, pos in list(self.positions.items()):
            exchange = pos['exchange']
            symbol = pos['symbol']
            entry = pos['entry']
            
            ticker = self.ticker_cache.get(exchange, {}).get(symbol, {})
            if not ticker:
                continue
            
            price = ticker.get('price', entry)
            pnl_pct = (price - entry) / entry
            pnl_usd = pnl_pct * pos['qty'] * entry
            
            # Track peak for trailing stop
            peak_key = key
            if peak_key not in self.peak_prices:
                self.peak_prices[peak_key] = price
            elif price > self.peak_prices[peak_key]:
                self.peak_prices[peak_key] = price
            
            should_exit = False
            reason = ""
            
            # Trailing stop logic
            if CONFIG['ENABLE_TRAILING_STOP']:
                peak = self.peak_prices[peak_key]
                gain_from_entry = (peak - entry) / entry
                
                if gain_from_entry >= CONFIG['TRAIL_ACTIVATION_PCT']:
                    trail_distance = CONFIG['TRAIL_DISTANCE_PCT']
                    trail_price = peak * (1 - trail_distance)
                    
                    if price <= trail_price:
                        should_exit = True
                        reason = f"📈 TRAILING STOP (Peak: ${peak:.4f})"
            
            # Standard exits
            if not should_exit:
                if pnl_pct >= CONFIG['TAKE_PROFIT_PCT']:
                    should_exit = True
                    reason = "💰 TAKE PROFIT"
                elif pnl_pct <= -CONFIG['STOP_LOSS_PCT']:
                    should_exit = True
                    reason = "🛑 STOP LOSS"
                elif time.time() - pos['entry_time'] > CONFIG['TIMEOUT_SEC']:
                    should_exit = True
                    reason = "⏰ TIMEOUT"
            
            if should_exit:
                # Find the paper trade
                trade_id = pos.get('trade_id')
                for trade in self.paper_trades:
                    if trade.id == trade_id:
                        trade.exit_price = price
                        trade.exit_time = datetime.now()
                        trade.pnl_pct = pnl_pct
                        trade.pnl_usd = pnl_usd
                        trade.exit_reason = reason
                        
                        # Update metrics
                        self._update_metrics(trade)
                        break
                
                # Update balance
                self.paper_balance[exchange] += pos['qty'] * price
                
                self.total_profit += pnl_usd
                if pnl_usd >= 0:
                    self.wins += 1
                    self.metrics.winning_trades += 1
                else:
                    self.metrics.losing_trades += 1
                
                logger.info(f"""
╔════════════════════════════════════════════════════════════════╗
║ ⚡ PAPER EXIT [{exchange.upper()}] {symbol}
║ Reason: {reason}
║ Entry: ${entry:.4f} | Exit: ${price:.4f}
║ P&L: {pnl_pct*100:+.2f}% (${pnl_usd:+.2f})
╚════════════════════════════════════════════════════════════════╝
""")
                
                if key in self.peak_prices:
                    del self.peak_prices[key]
                del self.positions[key]
    
    def _update_metrics(self, trade: PaperTrade):
        """Update calibration metrics based on trade outcome"""
        is_win = trade.pnl_usd >= 0 if trade.pnl_usd is not None else False
        pnl = trade.pnl_usd or 0.0
        
        # Probability bucket
        prob_pct = trade.probability * 100
        if prob_pct < 60:
            bucket = '50-60'
        elif prob_pct < 70:
            bucket = '60-70'
        elif prob_pct < 80:
            bucket = '70-80'
        elif prob_pct < 90:
            bucket = '80-90'
        else:
            bucket = '90-100'
        
        self.metrics.prob_buckets[bucket]['count'] += 1
        if is_win:
            self.metrics.prob_buckets[bucket]['wins'] += 1
        self.metrics.prob_buckets[bucket]['pnl'] += pnl
        
        # Coherence bucket
        coh = trade.coherence
        if coh < 0.75:
            coh_bucket = '0.70-0.75'
        elif coh < 0.80:
            coh_bucket = '0.75-0.80'
        elif coh < 0.85:
            coh_bucket = '0.80-0.85'
        elif coh < 0.90:
            coh_bucket = '0.85-0.90'
        else:
            coh_bucket = '0.90-1.00'
        
        self.metrics.coherence_buckets[coh_bucket]['count'] += 1
        if is_win:
            self.metrics.coherence_buckets[coh_bucket]['wins'] += 1
        self.metrics.coherence_buckets[coh_bucket]['pnl'] += pnl
        
        # Asset class
        self.metrics.asset_class_stats[trade.asset_class]['count'] += 1
        if is_win:
            self.metrics.asset_class_stats[trade.asset_class]['wins'] += 1
        self.metrics.asset_class_stats[trade.asset_class]['pnl'] += pnl
        
        # Exchange
        self.metrics.exchange_stats[trade.exchange]['count'] += 1
        if is_win:
            self.metrics.exchange_stats[trade.exchange]['wins'] += 1
        self.metrics.exchange_stats[trade.exchange]['pnl'] += pnl
        
        # 6D Harmonic
        if trade.harmonic_6d_score > 0.5:
            self.metrics.harmonic_trades += 1
            if is_win:
                self.metrics.harmonic_wins += 1
            self.metrics.harmonic_pnl += pnl
        
        # Sentiment
        if trade.sentiment > 0.1:
            self.metrics.sentiment_positive_trades += 1
            if is_win:
                self.metrics.sentiment_positive_wins += 1
        elif trade.sentiment < -0.1:
            self.metrics.sentiment_negative_trades += 1
            if is_win:
                self.metrics.sentiment_negative_wins += 1
        
        self.metrics.total_pnl += pnl
    
    def print_calibration_report(self):
        """Print detailed calibration analysis"""
        m = self.metrics
        
        print("""
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                      ║
║     📊 CALIBRATION REPORT 📊                                                         ║
║                                                                                      ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
""")
        
        # Overall stats
        win_rate = m.winning_trades / max(1, m.trades_taken) * 100
        print(f"""
┌─────────────────────────────────────────────────────────────────┐
│ OVERALL STATISTICS                                              │
├─────────────────────────────────────────────────────────────────┤
│ Total Signals:    {m.total_signals:5d}                                        │
│ Trades Taken:     {m.trades_taken:5d}                                        │
│ Winning Trades:   {m.winning_trades:5d}                                        │
│ Losing Trades:    {m.losing_trades:5d}                                        │
│ Win Rate:         {win_rate:5.1f}%                                       │
│ Total P&L:       ${m.total_pnl:+8.2f}                                    │
└─────────────────────────────────────────────────────────────────┘
""")
        
        # Probability buckets
        print("""
┌─────────────────────────────────────────────────────────────────┐
│ PROBABILITY BUCKET ANALYSIS                                     │
├─────────────────────────────────────────────────────────────────┤""")
        for bucket, stats in m.prob_buckets.items():
            if stats['count'] > 0:
                wr = stats['wins'] / stats['count'] * 100
                print(f"│ {bucket}%:  {stats['count']:3d} trades | WR: {wr:5.1f}% | P&L: ${stats['pnl']:+7.2f}     │")
        print("└─────────────────────────────────────────────────────────────────┘")
        
        # Coherence buckets
        print("""
┌─────────────────────────────────────────────────────────────────┐
│ COHERENCE BUCKET ANALYSIS                                       │
├─────────────────────────────────────────────────────────────────┤""")
        for bucket, stats in m.coherence_buckets.items():
            if stats['count'] > 0:
                wr = stats['wins'] / stats['count'] * 100
                print(f"│ Γ={bucket}:  {stats['count']:3d} trades | WR: {wr:5.1f}% | P&L: ${stats['pnl']:+7.2f}  │")
        print("└─────────────────────────────────────────────────────────────────┘")
        
        # Asset class analysis
        print("""
┌─────────────────────────────────────────────────────────────────┐
│ ASSET CLASS ANALYSIS                                            │
├─────────────────────────────────────────────────────────────────┤""")
        for asset, stats in dict(m.asset_class_stats).items():
            if stats['count'] > 0:
                wr = stats['wins'] / stats['count'] * 100
                print(f"│ {asset:12s}:  {stats['count']:3d} trades | WR: {wr:5.1f}% | P&L: ${stats['pnl']:+7.2f}  │")
        print("└─────────────────────────────────────────────────────────────────┘")
        
        # Exchange analysis
        print("""
┌─────────────────────────────────────────────────────────────────┐
│ EXCHANGE ANALYSIS                                               │
├─────────────────────────────────────────────────────────────────┤""")
        for exch, stats in dict(m.exchange_stats).items():
            if stats['count'] > 0:
                wr = stats['wins'] / stats['count'] * 100
                print(f"│ {exch:12s}:  {stats['count']:3d} trades | WR: {wr:5.1f}% | P&L: ${stats['pnl']:+7.2f}  │")
        print("└─────────────────────────────────────────────────────────────────┘")
        
        # 6D Harmonic effectiveness
        if m.harmonic_trades > 0:
            h_wr = m.harmonic_wins / m.harmonic_trades * 100
            print(f"""
┌─────────────────────────────────────────────────────────────────┐
│ 6D HARMONIC WAVEFORM EFFECTIVENESS                              │
├─────────────────────────────────────────────────────────────────┤
│ Harmonic Trades:  {m.harmonic_trades:3d}                                         │
│ Harmonic Wins:    {m.harmonic_wins:3d}                                         │
│ Harmonic WR:      {h_wr:5.1f}%                                       │
│ Harmonic P&L:    ${m.harmonic_pnl:+8.2f}                                    │
└─────────────────────────────────────────────────────────────────┘
""")
        
        # Sentiment effectiveness
        if m.sentiment_positive_trades > 0 or m.sentiment_negative_trades > 0:
            pos_wr = m.sentiment_positive_wins / max(1, m.sentiment_positive_trades) * 100
            neg_wr = m.sentiment_negative_wins / max(1, m.sentiment_negative_trades) * 100
            print(f"""
┌─────────────────────────────────────────────────────────────────┐
│ NEWS SENTIMENT EFFECTIVENESS                                    │
├─────────────────────────────────────────────────────────────────┤
│ Positive Sentiment Trades: {m.sentiment_positive_trades:3d} | WR: {pos_wr:5.1f}%              │
│ Negative Sentiment Trades: {m.sentiment_negative_trades:3d} | WR: {neg_wr:5.1f}%              │
└─────────────────────────────────────────────────────────────────┘
""")
        
        # Recommendations
        print("""
┌─────────────────────────────────────────────────────────────────┐
│ 🎯 CALIBRATION RECOMMENDATIONS                                  │
├─────────────────────────────────────────────────────────────────┤""")
        
        # Find best probability bucket
        best_prob = max(m.prob_buckets.items(), 
                       key=lambda x: x[1]['wins']/max(1, x[1]['count']) if x[1]['count'] > 2 else 0)
        if best_prob[1]['count'] > 2:
            print(f"│ ✅ Best probability range: {best_prob[0]}%                          │")
        
        # Find best coherence bucket
        best_coh = max(m.coherence_buckets.items(),
                      key=lambda x: x[1]['wins']/max(1, x[1]['count']) if x[1]['count'] > 2 else 0)
        if best_coh[1]['count'] > 2:
            print(f"│ ✅ Best coherence range: Γ={best_coh[0]}                        │")
        
        print("└─────────────────────────────────────────────────────────────────┘")
    
    def save_trades_to_file(self, filepath: str = 'calibration_trades.json'):
        """Save all paper trades to JSON for analysis"""
        trades_data = []
        for t in self.paper_trades:
            trades_data.append({
                'id': t.id,
                'exchange': t.exchange,
                'symbol': t.symbol,
                'side': t.side,
                'entry_price': t.entry_price,
                'entry_time': t.entry_time.isoformat() if t.entry_time else None,
                'exit_price': t.exit_price,
                'exit_time': t.exit_time.isoformat() if t.exit_time else None,
                'quantity': t.quantity,
                'probability': t.probability,
                'coherence': t.coherence,
                'frequency': t.frequency,
                'asset_class': t.asset_class,
                'sentiment': t.sentiment,
                'harmonic_6d_score': t.harmonic_6d_score,
                'pnl_pct': t.pnl_pct,
                'pnl_usd': t.pnl_usd,
                'exit_reason': t.exit_reason,
            })
        
        with open(filepath, 'w') as f:
            json.dump(trades_data, f, indent=2)
        
        logger.info(f"Saved {len(trades_data)} trades to {filepath}")


def run_calibration_test(duration_minutes: int = 10):
    """Run paper trading calibration test"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                      ║
║     🧪 AUREON CALIBRATION TEST 🧪                                                    ║
║     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                                ║
║                                                                                      ║
║     Running paper trades to calibrate probability thresholds                         ║
║                                                                                      ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
    """)
    
    trader = CalibrationTrader()
    duration_sec = duration_minutes * 60
    
    try:
        trader.run(duration_sec=duration_sec)
    except KeyboardInterrupt:
        logger.info("Calibration test interrupted by user")
    
    # Print report
    trader.print_calibration_report()
    
    # Save trades
    trader.save_trades_to_file()
    
    return trader


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Aureon Calibration Test')
    parser.add_argument('--duration', type=int, default=10, 
                       help='Test duration in minutes (default: 10)')
    args = parser.parse_args()
    
    run_calibration_test(duration_minutes=args.duration)
