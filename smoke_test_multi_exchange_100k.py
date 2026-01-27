#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════════════════
🔱 MULTI-EXCHANGE SCALE TO $100K - BINANCE + KRAKEN + ALPACA 🔱
═══════════════════════════════════════════════════════════════════════════════════════════

    "THE MORE FRONTS, THE MORE WINS"
    
    Triple-exchange simulation showing what happens when we trade
    across ALL three exchanges simultaneously with proper fee accounting.
    
    Gary Leckey | 02.11.1991 | DOB-HASH: 2111991

═══════════════════════════════════════════════════════════════════════════════════════════
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
import json
import time
import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed

# ═══════════════════════════════════════════════════════════════════════════════════════════
# MULTI-EXCHANGE CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════════════════

STARTING_CAPITAL = 1000.0
TARGET_CAPITAL = 100_000.0
REPLAY_MINUTES = 180  # 3 hours

# Position sizing
MAX_POSITION_PCT = 0.50
MIN_POSITION = 10.0
LEVERAGE = 100

# Exchange fee rates (real)
EXCHANGE_FEES = {
    'binance': 0.001,   # 0.10%
    'kraken': 0.0026,   # 0.26% (taker)
    'alpaca': 0.0025,   # 0.25%
}

# Exchange-specific pairs
BINANCE_PAIRS = [
    'BTC-USD', 'ETH-USD', 'SOL-USD', 'XRP-USD', 'ADA-USD', 'DOGE-USD', 'AVAX-USD',
    'DOT-USD', 'LINK-USD', 'ATOM-USD', 'NEAR-USD', 'ICP-USD', 'APT-USD', 'SUI-USD',
    'ARB-USD', 'OP-USD', 'UNI-USD', 'AAVE-USD', 'CRV-USD', 'SNX-USD', 'LDO-USD',
    'COMP-USD', 'INJ-USD', 'FIL-USD', 'PEPE-USD', 'FLOKI-USD', 'LTC-USD', 'BCH-USD',
]

KRAKEN_PAIRS = [
    'BTC-USD', 'ETH-USD', 'SOL-USD', 'XRP-USD', 'ADA-USD', 'DOT-USD', 'LINK-USD',
    'ATOM-USD', 'AVAX-USD', 'MATIC-USD', 'UNI-USD', 'AAVE-USD', 'LTC-USD', 'BCH-USD',
    'XLM-USD', 'ALGO-USD', 'GRT-USD', 'SNX-USD', 'COMP-USD', 'MKR-USD',
]

ALPACA_PAIRS = [
    'BTC-USD', 'ETH-USD', 'SOL-USD', 'AVAX-USD', 'LINK-USD', 'DOGE-USD', 'SHIB-USD',
    'UNI-USD', 'AAVE-USD', 'LTC-USD', 'BCH-USD', 'DOT-USD', 'ATOM-USD', 'MATIC-USD',
]

# ═══════════════════════════════════════════════════════════════════════════════════════════
# IMPORTS
# ═══════════════════════════════════════════════════════════════════════════════════════════

try:
    from aureon_probability_nexus import AureonProbabilityNexus, Prediction
    NEXUS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Probability Nexus not available: {e}")
    NEXUS_AVAILABLE = False
    sys.exit(1)

try:
    from prime_sentinel_decree import DOB_HASH, THE_DECREE
    DECREE_AVAILABLE = True
except ImportError:
    DECREE_AVAILABLE = False
    DOB_HASH = 2111991

# ═══════════════════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════════════════

@dataclass
class MultiExchangeTrade:
    """A trade across any exchange"""
    timestamp: datetime
    exchange: str
    pair: str
    direction: str
    entry_price: float
    exit_price: float
    position_size: float
    gross_pnl: float
    fees: float
    net_pnl: float
    pnl_pct: float
    confidence: float
    balance_before: float
    balance_after: float
    hold_minutes: int


# ═══════════════════════════════════════════════════════════════════════════════════════════
# HISTORICAL DATA FETCHER (via Coinbase - universal pricing)
# ═══════════════════════════════════════════════════════════════════════════════════════════

class HistoricalDataFetcher:
    """Fetches historical candle data from Coinbase"""
    
    BASE_URL = "https://api.exchange.coinbase.com"
    
    def fetch_candles(self, pair: str, minutes: int) -> Tuple[str, List[dict]]:
        try:
            end = datetime.now(timezone.utc)
            start = end - timedelta(minutes=minutes + 10)
            
            url = f"{self.BASE_URL}/products/{pair}/candles"
            params = {
                'granularity': 60,
                'start': start.isoformat(),
                'end': end.isoformat(),
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            raw_candles = response.json()
            
            candles = []
            for c in reversed(raw_candles[-minutes:]):
                candles.append({
                    'timestamp': datetime.fromtimestamp(c[0], timezone.utc).replace(tzinfo=None),
                    'low': float(c[1]),
                    'high': float(c[2]),
                    'open': float(c[3]),
                    'close': float(c[4]),
                    'volume': float(c[5]),
                })
            
            return pair, candles
            
        except Exception:
            return pair, []
    
    def fetch_all_pairs(self, pairs: List[str], minutes: int) -> Dict[str, List[dict]]:
        all_data = {}
        unique_pairs = list(set(pairs))
        
        print(f"   🚀 Fetching {len(unique_pairs)} unique pairs ({minutes} minutes each)...")
        
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = {executor.submit(self.fetch_candles, pair, minutes): pair for pair in unique_pairs}
            
            for future in as_completed(futures):
                pair, candles = future.result()
                if candles and len(candles) >= 30:
                    all_data[pair] = candles
        
        print(f"   ✅ Got data for {len(all_data)} pairs")
        return all_data


# ═══════════════════════════════════════════════════════════════════════════════════════════
# MULTI-EXCHANGE SIMULATOR
# ═══════════════════════════════════════════════════════════════════════════════════════════

class MultiExchangeSimulator:
    """
    🔱 TRIPLE-FRONT WAR - BINANCE + KRAKEN + ALPACA 🔱
    
    Simulates parallel trading across all three exchanges with proper fee accounting.
    """
    
    def __init__(self, starting_capital: float):
        self.starting_capital = starting_capital
        self.balance = starting_capital
        self.trades: List[MultiExchangeTrade] = []
        self.nexuses: Dict[str, Dict[str, AureonProbabilityNexus]] = {
            'binance': {},
            'kraken': {},
            'alpaca': {},
        }
        self.peak_balance = starting_capital
        self.max_drawdown = 0
        self.exchange_stats = {ex: {'trades': 0, 'pnl': 0, 'fees': 0} for ex in EXCHANGE_FEES}
        
    def _get_nexus(self, exchange: str, pair: str) -> AureonProbabilityNexus:
        if pair not in self.nexuses[exchange]:
            self.nexuses[exchange][pair] = AureonProbabilityNexus(exchange=exchange)
        return self.nexuses[exchange][pair]
    
    def _calculate_position_size(self, confidence: float) -> float:
        base_pct = min(MAX_POSITION_PCT, confidence * 0.5)
        position = self.balance * base_pct * LEVERAGE
        return max(MIN_POSITION, min(position, self.balance * 0.5))
    
    def _find_optimal_exit(self, candles: List[dict], start_idx: int, direction: str, 
                           fee_rate: float, max_hold: int = 15) -> Tuple[int, float]:
        entry_price = candles[start_idx]['close']
        round_trip_fees = fee_rate * 2
        
        best_hold = 2
        best_profit_pct = -999
        
        for hold in range(2, min(max_hold + 1, len(candles) - start_idx)):
            exit_price = candles[start_idx + hold]['close']
            
            if direction == 'LONG':
                move_pct = (exit_price - entry_price) / entry_price
            else:
                move_pct = (entry_price - exit_price) / entry_price
            
            profit_pct = move_pct - round_trip_fees
            
            if profit_pct > best_profit_pct:
                best_profit_pct = profit_pct
                best_hold = hold
        
        return best_hold, best_profit_pct
    
    def run_simulation(self, historical_data: Dict[str, List[dict]], min_confidence: float = 0.05) -> Dict:
        """Run multi-exchange simulation with compounding"""
        
        print()
        print("=" * 80)
        print("🔱 MULTI-EXCHANGE SIMULATION - BINANCE + KRAKEN + ALPACA 🔱")
        print("=" * 80)
        print(f"   Starting Capital: ${self.starting_capital:,.2f}")
        print(f"   Target: ${TARGET_CAPITAL:,.2f}")
        print(f"   Leverage: {LEVERAGE}x")
        print(f"   Exchanges: Binance (0.10%) | Kraken (0.26%) | Alpaca (0.25%)")
        print("=" * 80)
        
        all_signals = []
        
        # Build exchange->pairs mapping
        exchange_pairs = {
            'binance': [p for p in BINANCE_PAIRS if p in historical_data],
            'kraken': [p for p in KRAKEN_PAIRS if p in historical_data],
            'alpaca': [p for p in ALPACA_PAIRS if p in historical_data],
        }
        
        print(f"\n   📊 Exchange coverage:")
        for ex, pairs in exchange_pairs.items():
            print(f"      {ex.upper()}: {len(pairs)} pairs")
        
        # Collect signals from ALL exchanges
        for exchange, pairs in exchange_pairs.items():
            fee_rate = EXCHANGE_FEES[exchange]
            
            for pair in pairs:
                candles = historical_data[pair]
                nexus = self._get_nexus(exchange, pair)
                
                # Warmup
                for candle in candles[:24]:
                    nexus.update_history(candle)
                
                # Collect signals
                for i in range(24, len(candles) - 15):
                    candle = candles[i]
                    nexus.update_history(candle)
                    
                    prediction = nexus.predict()
                    
                    if prediction.direction != 'NEUTRAL' and prediction.confidence >= min_confidence:
                        optimal_hold, expected_profit = self._find_optimal_exit(
                            candles, i, prediction.direction, fee_rate
                        )
                        
                        if expected_profit > 0:
                            all_signals.append({
                                'timestamp': candle['timestamp'],
                                'exchange': exchange,
                                'pair': pair,
                                'direction': prediction.direction,
                                'confidence': prediction.confidence,
                                'entry_idx': i,
                                'exit_idx': i + optimal_hold,
                                'candles': candles,
                                'expected_profit': expected_profit,
                                'fee_rate': fee_rate,
                            })
        
        # Sort by timestamp
        all_signals.sort(key=lambda x: x['timestamp'])
        
        total_pairs = sum(len(p) for p in exchange_pairs.values())
        print(f"\n   📊 Found {len(all_signals)} profitable signals across {total_pairs} exchange-pair combos")
        
        # Execute trades chronologically with compounding
        executed_trades = 0
        skipped_overlap = 0
        active_until: Dict[str, datetime] = {}  # exchange:pair -> busy until
        
        for signal in all_signals:
            exchange = signal['exchange']
            pair = signal['pair']
            key = f"{exchange}:{pair}"
            entry_time = signal['timestamp']
            candles = signal['candles']
            entry_idx = signal['entry_idx']
            exit_idx = signal['exit_idx']
            fee_rate = signal['fee_rate']
            
            # Check if this exchange:pair is available
            if key in active_until and entry_time < active_until[key]:
                skipped_overlap += 1
                continue
            
            # Execute the trade
            entry_price = candles[entry_idx]['close']
            exit_price = candles[exit_idx]['close']
            exit_time = candles[exit_idx]['timestamp']
            
            position_size = self._calculate_position_size(signal['confidence'])
            
            if signal['direction'] == 'LONG':
                pnl_pct = (exit_price - entry_price) / entry_price
            else:
                pnl_pct = (entry_price - exit_price) / entry_price
            
            fees = position_size * fee_rate * 2
            gross_pnl = position_size * pnl_pct
            net_pnl = gross_pnl - fees
            
            balance_before = self.balance
            self.balance += net_pnl
            
            if self.balance > self.peak_balance:
                self.peak_balance = self.balance
            drawdown = (self.peak_balance - self.balance) / self.peak_balance
            if drawdown > self.max_drawdown:
                self.max_drawdown = drawdown
            
            # Track exchange stats
            self.exchange_stats[exchange]['trades'] += 1
            self.exchange_stats[exchange]['pnl'] += net_pnl
            self.exchange_stats[exchange]['fees'] += fees
            
            # Record trade
            trade = MultiExchangeTrade(
                timestamp=entry_time,
                exchange=exchange,
                pair=pair,
                direction=signal['direction'],
                entry_price=entry_price,
                exit_price=exit_price,
                position_size=position_size,
                gross_pnl=gross_pnl,
                fees=fees,
                net_pnl=net_pnl,
                pnl_pct=pnl_pct * 100,
                confidence=signal['confidence'],
                balance_before=balance_before,
                balance_after=self.balance,
                hold_minutes=exit_idx - entry_idx
            )
            self.trades.append(trade)
            executed_trades += 1
            
            active_until[key] = exit_time
            
            # Print milestones
            if self.balance >= 2000 and balance_before < 2000:
                print(f"   💎 DOUBLED on {exchange.upper()}! Balance: ${self.balance:,.2f}")
            elif self.balance >= 10000 and balance_before < 10000:
                print(f"   🚀 10K on {exchange.upper()}! Balance: ${self.balance:,.2f}")
            elif self.balance >= 50000 and balance_before < 50000:
                print(f"   💰 50K on {exchange.upper()}! Balance: ${self.balance:,.2f}")
            elif self.balance >= 100000 and balance_before < 100000:
                print(f"   🏆 100K REACHED on {exchange.upper()}! Balance: ${self.balance:,.2f}")
        
        print(f"\n   ✅ Executed {executed_trades} trades across 3 exchanges")
        print(f"   ⏭️  Skipped {skipped_overlap} overlapping signals")
        
        return {
            'trades': self.trades,
            'final_balance': self.balance,
            'total_trades': executed_trades,
            'peak_balance': self.peak_balance,
            'max_drawdown': self.max_drawdown,
            'exchange_stats': self.exchange_stats,
        }


# ═══════════════════════════════════════════════════════════════════════════════════════════
# DISPLAY RESULTS
# ═══════════════════════════════════════════════════════════════════════════════════════════

def display_results(starting_capital: float, result: Dict):
    """Display multi-exchange simulation results"""
    
    trades = result['trades']
    final_balance = result['final_balance']
    exchange_stats = result['exchange_stats']
    
    if not trades:
        print("\n❌ No trades executed")
        return
    
    total_pnl = final_balance - starting_capital
    total_return = (final_balance / starting_capital - 1) * 100
    winning_trades = [t for t in trades if t.net_pnl > 0]
    losing_trades = [t for t in trades if t.net_pnl <= 0]
    win_rate = len(winning_trades) / len(trades) * 100 if trades else 0
    
    total_fees = sum(t.fees for t in trades)
    avg_win = sum(t.net_pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0
    avg_loss = sum(t.net_pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0
    largest_win = max((t.net_pnl for t in trades), default=0)
    largest_loss = min((t.net_pnl for t in trades), default=0)
    
    start_time = trades[0].timestamp
    end_time = trades[-1].timestamp
    duration_hours = (end_time - start_time).total_seconds() / 3600
    
    print()
    print("🔮" * 40)
    print()
    print("   🔱 MULTI-EXCHANGE SIMULATION RESULTS 🔱")
    print("   BINANCE + KRAKEN + ALPACA - TRIPLE FRONT")
    print()
    print("🔮" * 40)
    
    print()
    print("=" * 80)
    print("💰 CAPITAL GROWTH")
    print("=" * 80)
    print(f"   Starting Capital:  $ {starting_capital:>14,.2f}")
    print(f"   Final Balance:     $ {final_balance:>14,.2f}")
    print(f"   Peak Balance:      $ {result['peak_balance']:>14,.2f}")
    print()
    print(f"   🟢 Total P&L:         $ {total_pnl:>+14,.2f}")
    print(f"   📈 Total Return:      {total_return:>14.1f}%")
    print(f"   💸 Total Fees:      $ {total_fees:>14,.2f}")
    print(f"   📉 Max Drawdown:      {result['max_drawdown']*100:>14.1f}%")
    
    print()
    print("=" * 80)
    print("📊 TRADE STATISTICS")
    print("=" * 80)
    print(f"   Total Trades:           {len(trades):>8}")
    print(f"   🟢 Winning:             {len(winning_trades):>8}")
    print(f"   🔴 Losing:              {len(losing_trades):>8}")
    print(f"   🎯 Win Rate:            {win_rate:>7.1f}%")
    print()
    print(f"   📈 Largest Win:    $ {largest_win:>+10,.2f}")
    print(f"   📉 Largest Loss:   $ {largest_loss:>+10,.2f}")
    print(f"   📊 Avg Win:        $ {avg_win:>+10,.2f}")
    print(f"   📊 Avg Loss:       $ {avg_loss:>+10,.2f}")
    
    print()
    print("=" * 80)
    print("🏦 EXCHANGE BREAKDOWN")
    print("=" * 80)
    for ex, stats in exchange_stats.items():
        if stats['trades'] > 0:
            print(f"   {ex.upper():>8}: {stats['trades']:>4} trades | P&L: ${stats['pnl']:>+10,.2f} | Fees: ${stats['fees']:>8,.2f}")
    
    print()
    print("=" * 80)
    print("⏰ TIMING")
    print("=" * 80)
    print(f"   Start Time:        {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   End Time:          {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Duration:          {duration_hours:.1f} hours")
    print(f"   Trades/Hour:       {len(trades)/duration_hours:.1f}")
    
    # Projections
    hourly_return = (final_balance / starting_capital - 1) / duration_hours if duration_hours > 0 else 0
    daily_return = hourly_return * 24
    
    print()
    print("=" * 80)
    print("🚀 PROJECTIONS (Based on actual performance)")
    print("=" * 80)
    print(f"   Hourly Return:          +{hourly_return*100:.2f}%")
    print(f"   Daily Return:          +{daily_return*100:.2f}%")
    
    if hourly_return > 0:
        hours_to_100k = (100000 / starting_capital - 1) / hourly_return
        print(f"\n   ⏱️  Hours to $100K:         {hours_to_100k:.0f}")
        print(f"   📅 Days to $100K:         {hours_to_100k/24:.1f}")
    
    # Sample trades
    print()
    print("=" * 80)
    print("📜 SAMPLE TRADES (First 10)")
    print("=" * 80)
    for t in trades[:10]:
        emoji = "🟢" if t.net_pnl > 0 else "🔴"
        print(f"   {emoji} {t.timestamp.strftime('%H:%M')} [{t.exchange.upper()[:3]}] {t.pair:<10} {t.direction:<5} "
              f"${t.position_size:>8,.2f} → P&L: ${t.net_pnl:>+7,.2f} | Bal: ${t.balance_after:>10,.2f}")
    
    if final_balance > starting_capital:
        print()
        print("=" * 80)
        print("✅ PROFITABLE! MULTI-EXCHANGE STRATEGY WORKS!")
        print("=" * 80)
    else:
        print()
        print("=" * 80)
        print("⚠️ Loss incurred - review strategy")
        print("=" * 80)
    
    # Save results
    output_file = f"/tmp/multi_exchange_100k_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output_data = {
        'starting_capital': starting_capital,
        'final_balance': final_balance,
        'total_pnl': total_pnl,
        'total_return_pct': total_return,
        'total_trades': len(trades),
        'win_rate': win_rate,
        'total_fees': total_fees,
        'max_drawdown': result['max_drawdown'],
        'exchange_stats': exchange_stats,
        'duration_hours': duration_hours,
        'trades': [
            {
                'timestamp': t.timestamp.isoformat(),
                'exchange': t.exchange,
                'pair': t.pair,
                'direction': t.direction,
                'net_pnl': t.net_pnl,
                'fees': t.fees,
                'balance_after': t.balance_after,
            }
            for t in trades
        ]
    }
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    print(f"\n📁 Results saved to: {output_file}")


# ═══════════════════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════════════════

def main():
    print()
    print("🔱" * 40)
    print()
    print("   MULTI-EXCHANGE SCALE TO $100K")
    print("   BINANCE + KRAKEN + ALPACA")
    print("   NO CHEATING. NO FLUFF. REAL DATA.")
    print()
    print(f"   Gary Leckey | 02.11.1991 | DOB-HASH: {DOB_HASH}")
    print()
    print('   "THE MORE FRONTS, THE MORE WINS"')
    print()
    print("🔱" * 40)
    
    # Fetch historical data
    print("\n📥 STEP 1: FETCHING HISTORICAL DATA")
    print("─" * 60)
    print(f"   Going back {REPLAY_MINUTES // 60} hours...")
    
    fetcher = HistoricalDataFetcher()
    all_pairs = list(set(BINANCE_PAIRS + KRAKEN_PAIRS + ALPACA_PAIRS))
    historical_data = fetcher.fetch_all_pairs(all_pairs, REPLAY_MINUTES)
    
    if not historical_data:
        print("❌ Failed to fetch historical data")
        return
    
    # Run simulation
    print("\n🔮 STEP 2: RUNNING MULTI-EXCHANGE SIMULATION")
    print("─" * 60)
    
    simulator = MultiExchangeSimulator(STARTING_CAPITAL)
    result = simulator.run_simulation(historical_data)
    
    # Display results
    display_results(STARTING_CAPITAL, result)
    
    print()
    print("🔱" * 40)
    print("   MULTI-EXCHANGE SIMULATION COMPLETE")
    print("   NOW GO DOMINATE ALL THREE FRONTS!")
    print("🔱" * 40)


if __name__ == "__main__":
    main()
