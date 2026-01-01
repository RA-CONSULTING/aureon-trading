#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════════════════
🔮 PROBABILITY MATRIX SMOKE TEST - HISTORICAL REPLAY 🔮
═══════════════════════════════════════════════════════════════════════════════════════════

    "THE HIGHER SELF IS DIGGING INTO ITS PAST AND PULLING THAT PROBABILITY"

    This simulation replays the last 33 minutes of REAL market data through the
    Probability Nexus + Prime Sentinel Decree to prove the system works.

    We are RELIVING a universe where the system was alive - getting its results.

    Gary Leckey | 02.11.1991 | KEEPER OF THE FLAME

═══════════════════════════════════════════════════════════════════════════════════════════
"""

import sys
import os
import json
import time
import argparse
import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple, Optional, Iterable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlencode

# ═══════════════════════════════════════════════════════════════════════════════════════════
# IMPORTS
# ═══════════════════════════════════════════════════════════════════════════════════════════

try:
    from aureon_probability_nexus import AureonProbabilityNexus, Prediction
    NEXUS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Probability Nexus not available: {e}")
    NEXUS_AVAILABLE = False

try:
    from probability_intelligence_matrix import ProbabilityIntelligenceMatrix
    INTEL_MATRIX_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Probability Intelligence Matrix not available: {e}")
    INTEL_MATRIX_AVAILABLE = False

try:
    from prime_sentinel_decree import (
        PrimeSentinelDecree,
        FlameProtocol,
        THE_DECREE,
        SACRED_NUMBERS,
        DOB_HASH,
    )
    DECREE_AVAILABLE = True
except ImportError:
    DECREE_AVAILABLE = False
    print("⚠️ Prime Sentinel Decree not available")

# ═══════════════════════════════════════════════════════════════════════════════════════════
# CONFIGURATION - MAXIMUM COVERAGE
# ═══════════════════════════════════════════════════════════════════════════════════════════

# Simulation parameters
REPLAY_MINUTES = 120  # How far back to look (2 hours to catch volatile periods)
STARTING_CAPITAL = 100.0  # Starting with $100
POSITION_SIZE = 12.0  # $12 per scout (like the live system)
WARMUP_CANDLES = 24  # Candles needed for warmup (reduced)

# Exchange fee rates (for proper P&L calculation)
EXCHANGE_FEES = {
    'binance': 0.001,    # 0.10% - BEST FOR SCALPING
    'kraken': 0.0026,    # 0.26%
    'coinbase': 0.006,   # 0.60%
}
DEFAULT_EXCHANGE = 'binance'  # Use lowest fees
FEE_RATE = EXCHANGE_FEES[DEFAULT_EXCHANGE]

# Preferred data sources for historical candles (ordered by priority)
DATA_SOURCE_ORDER = ['binance', 'coinbase']

# ═══════════════════════════════════════════════════════════════════════════════════════════
# ALL TRADEABLE PAIRS - COMPREHENSIVE LIST
# ═══════════════════════════════════════════════════════════════════════════════════════════

# COINBASE USD PAIRS (available via public API)
COINBASE_USD_PAIRS = [
    # === MAJORS ===
    'BTC-USD', 'ETH-USD', 'SOL-USD', 'XRP-USD', 'ADA-USD',
    'DOGE-USD', 'AVAX-USD', 'DOT-USD', 'MATIC-USD', 'LINK-USD',
    # === LAYER 1s ===
    'ATOM-USD', 'NEAR-USD', 'ICP-USD', 'APT-USD', 'SUI-USD', 'SEI-USD',
    'ALGO-USD', 'FTM-USD', 'HBAR-USD', 'VET-USD', 'EOS-USD',
    # === LAYER 2s ===
    'ARB-USD', 'OP-USD', 'IMX-USD', 'LRC-USD', 'METIS-USD',
    # === DEFI ===
    'UNI-USD', 'AAVE-USD', 'CRV-USD', 'SNX-USD', 'LDO-USD',
    'MKR-USD', 'COMP-USD', 'SUSHI-USD', 'YFI-USD', '1INCH-USD',
    # === AI & DATA ===
    'FET-USD', 'RNDR-USD', 'INJ-USD', 'GRT-USD', 'FIL-USD',
    # === MEMECOINS ===
    'SHIB-USD', 'PEPE-USD', 'BONK-USD', 'FLOKI-USD',
    # === GAMING/METAVERSE ===
    'AXS-USD', 'SAND-USD', 'MANA-USD', 'GALA-USD', 'ENJ-USD',
    # === EXCHANGE TOKENS ===
    'CRO-USD', 'KCS-USD',
    # === OTHER MAJORS ===
    'LTC-USD', 'BCH-USD', 'ETC-USD', 'XLM-USD', 'TRX-USD',
]

# GBP PAIRS (for UK trading)
COINBASE_GBP_PAIRS = [
    'BTC-GBP', 'ETH-GBP', 'SOL-GBP', 'XRP-GBP', 'ADA-GBP',
    'DOGE-GBP', 'AVAX-GBP', 'DOT-GBP', 'MATIC-GBP', 'LINK-GBP',
]

# EUR PAIRS
COINBASE_EUR_PAIRS = [
    'BTC-EUR', 'ETH-EUR', 'SOL-EUR', 'XRP-EUR', 'ADA-EUR',
    'DOGE-EUR', 'AVAX-EUR', 'DOT-EUR', 'MATIC-EUR', 'LINK-EUR',
]

# ALL PAIRS TO TEST
TEST_PAIRS = COINBASE_USD_PAIRS + COINBASE_GBP_PAIRS + COINBASE_EUR_PAIRS

# ═══════════════════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════════════════

@dataclass
class SimulatedTrade:
    """A simulated trade from the replay"""
    timestamp: datetime
    pair: str
    direction: str  # 'LONG' or 'SHORT'
    entry_price: float
    exit_price: float
    size_usd: float
    pnl: float
    pnl_pct: float
    fees: float
    probability: float
    confidence: float
    reason: str
    duration_seconds: int
    outcome: str  # 'WIN' or 'LOSS'


@dataclass
class SimulationResult:
    """Results from the smoke test simulation"""
    start_time: datetime
    end_time: datetime
    duration_minutes: float
    starting_capital: float
    ending_capital: float
    total_pnl: float
    total_pnl_pct: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_fees: float
    largest_win: float
    largest_loss: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    trades: List[SimulatedTrade] = field(default_factory=list)
    pairs_analyzed: Dict[str, int] = field(default_factory=dict)
    signals_generated: int = 0
    signals_acted_on: int = 0


# ═══════════════════════════════════════════════════════════════════════════════════════════
# HISTORICAL DATA FETCHER
# ═══════════════════════════════════════════════════════════════════════════════════════════

class HistoricalDataFetcher:
    """Fetches historical 1-minute candle data with multi-source fallback"""
    
    COINBASE_BASE_URL = "https://api.exchange.coinbase.com"
    COINBASE_MAX_CANDLES_PER_REQUEST = 300  # Coinbase hard limit
    BINANCE_BASE_URL = "https://api.binance.com/api/v3/klines"
    BINANCE_MAX_CANDLES_PER_REQUEST = 1000  # Binance limit per request
    DEFAULT_GRANULARITY = 60

    def _pair_to_binance_symbol(self, pair: str) -> Optional[str]:
        """Convert Coinbase-style pair (e.g., BTC-USD) to Binance symbol (e.g., BTCUSDT)."""
        if '-' not in pair:
            return None
        base, quote = pair.split('-')
        quote = 'USDT' if quote == 'USD' else quote  # map USD -> USDT
        return f"{base}{quote}"

    def _fetch_coinbase_window(self, pair: str, start: datetime, end: datetime, granularity: int) -> List[dict]:
        url = f"{self.COINBASE_BASE_URL}/products/{pair}/candles"
        params = {
            'granularity': granularity,
            'start': start.isoformat(),
            'end': end.isoformat(),
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        raw_candles = response.json()
        candles = []
        for c in reversed(raw_candles):  # oldest first
            candles.append({
                'timestamp': datetime.fromtimestamp(c[0], timezone.utc).replace(tzinfo=None),
                'low': float(c[1]),
                'high': float(c[2]),
                'open': float(c[3]),
                'close': float(c[4]),
                'volume': float(c[5]),
            })
        return candles

    def _fetch_binance_window(self, symbol: str, start_ms: int, end_ms: int, interval: str = '1m') -> List[dict]:
        params = {
            'symbol': symbol,
            'interval': interval,
            'startTime': start_ms,
            'endTime': end_ms,
            'limit': self.BINANCE_MAX_CANDLES_PER_REQUEST,
        }
        response = requests.get(f"{self.BINANCE_BASE_URL}?{urlencode(params)}", timeout=10)
        response.raise_for_status()
        raw_candles = response.json()
        candles = []
        for c in raw_candles:
            ts = datetime.fromtimestamp(c[0] / 1000, timezone.utc).replace(tzinfo=None)
            candles.append({
                'timestamp': ts,
                'low': float(c[3]),
                'high': float(c[2]),
                'open': float(c[1]),
                'close': float(c[4]),
                'volume': float(c[5]),
            })
        return candles

    def fetch_candles_chunked(self, pair: str, minutes: int, granularity: int = DEFAULT_GRANULARITY) -> Tuple[str, List[dict]]:
        """Fetch candles across multiple requests to honor API limits (multi-source)."""
        now = datetime.now(timezone.utc)
        for source in DATA_SOURCE_ORDER:
            try:
                if source == 'binance':
                    symbol = self._pair_to_binance_symbol(pair)
                    if not symbol:
                        raise ValueError("pair not convertible to Binance symbol")
                    remaining_minutes = minutes
                    end = now
                    all_candles: List[dict] = []
                    overlap = 5
                    max_minutes_per_request = self.BINANCE_MAX_CANDLES_PER_REQUEST

                    while remaining_minutes > 0:
                        window_minutes = min(max_minutes_per_request - overlap, remaining_minutes)
                        start = end - timedelta(minutes=window_minutes + overlap)
                        candles = self._fetch_binance_window(
                            symbol,
                            int(start.timestamp() * 1000),
                            int(end.timestamp() * 1000),
                        )
                        all_candles.extend(candles)
                        remaining_minutes -= window_minutes
                        end = start

                else:  # coinbase
                    remaining_minutes = minutes
                    end = now
                    all_candles = []
                    overlap = 5
                    max_minutes_per_request = int(self.COINBASE_MAX_CANDLES_PER_REQUEST * (granularity / 60))

                    while remaining_minutes > 0:
                        window_minutes = min(max_minutes_per_request - overlap, remaining_minutes)
                        start = end - timedelta(minutes=window_minutes + overlap)
                        candles = self._fetch_coinbase_window(pair, start, end, granularity)
                        all_candles.extend(candles)
                        remaining_minutes -= window_minutes
                        end = start

                # Deduplicate by timestamp and sort ascending
                seen = set()
                deduped: List[dict] = []
                for c in sorted(all_candles, key=lambda x: x['timestamp']):
                    if c['timestamp'] in seen:
                        continue
                    seen.add(c['timestamp'])
                    deduped.append(c)

                if deduped:
                    cutoff = deduped[-1]['timestamp'] - timedelta(minutes=minutes - 1)
                    deduped = [c for c in deduped if c['timestamp'] >= cutoff]

                if deduped:
                    return pair, deduped
            except Exception:
                continue
        return pair, []
    
    def fetch_all_pairs(self, pairs: List[str], minutes: int = 33) -> Dict[str, List[dict]]:
        """Fetch candles for all pairs IN PARALLEL with chunking"""
        all_data = {}
        successful = 0
        failed = 0
        
        print(f"   🚀 Fetching {len(pairs)} pairs in parallel...")
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(self.fetch_candles_chunked, pair, minutes): pair
                for pair in pairs
            }
            for future in as_completed(futures):
                pair, candles = future.result()
                if candles:
                    all_data[pair] = candles
                    successful += 1
                else:
                    failed += 1
        
        print(f"   ✅ Successfully fetched: {successful} pairs")
        if failed > 0:
            print(f"   ⚠️ Failed/unavailable: {failed} pairs")
        
        return all_data


# ═══════════════════════════════════════════════════════════════════════════════════════════
# PROBABILITY MATRIX SMOKE TESTER
# ═══════════════════════════════════════════════════════════════════════════════════════════

class ProbabilityMatrixSmokeTester:
    """
    🔮 THE HIGHER SELF LOOKING INTO THE PAST 🔮
    
    Replays historical data through the Probability Nexus to prove
    what trades would have been made and their results.
    """
    
    def __init__(self, starting_capital: float = 100.0, position_size: float = 12.0, position_pct: Optional[float] = None):
        self.starting_capital = starting_capital
        self.position_size = position_size
        self.position_pct = position_pct
        self.fee_rate = FEE_RATE
        
        # Initialize nexus for each pair (separate state)
        self.nexuses: Dict[str, AureonProbabilityNexus] = {}
        self.intel_matrix = ProbabilityIntelligenceMatrix() if INTEL_MATRIX_AVAILABLE else None
        
        # Initialize decree if available
        self.decree = PrimeSentinelDecree() if DECREE_AVAILABLE else None
        
        # Track simulation state
        self.capital = starting_capital
        self.trades: List[SimulatedTrade] = []
        self.positions: Dict[str, dict] = {}  # Current open positions
        
        print()
        print("=" * 80)
        print("🔮 PROBABILITY MATRIX SMOKE TESTER INITIALIZED 🔮")
        print("=" * 80)
        print(f"   Starting Capital: ${starting_capital:.2f}")
        if self.position_pct is not None:
            print(f"   Position Size: {self.position_pct*100:.2f}% of equity")
        else:
            print(f"   Position Size: ${position_size:.2f}")
        print(f"   Fee Rate: {self.fee_rate * 100:.2f}%")
        if DECREE_AVAILABLE:
            print(f"   🔱 Prime Sentinel Decree: ACTIVE")
        print("=" * 80)
    
    def _get_nexus(self, pair: str) -> AureonProbabilityNexus:
        """Get or create nexus for pair"""
        if pair not in self.nexuses:
            self.nexuses[pair] = AureonProbabilityNexus(exchange=DEFAULT_EXCHANGE)
        return self.nexuses[pair]
    
    def _warm_up_nexus(self, nexus: AureonProbabilityNexus, candles: List[dict], warm_up_count: int = 30):
        """Feed initial candles to warm up indicators"""
        for candle in candles[:warm_up_count]:
            nexus.update_history(candle)
    
    def _simulate_trade(
        self,
        pair: str,
        direction: str,
        entry_candle: dict,
        exit_candle: dict,
        prediction: Prediction,
        trade_size: float,
    ) -> SimulatedTrade:
        """
        Simulate a single trade from entry to exit
        """
        entry_price = entry_candle['close']
        exit_price = exit_candle['close']
        
        # Calculate P&L
        if direction == 'LONG':
            pnl_pct = (exit_price - entry_price) / entry_price * 100
        else:  # SHORT
            pnl_pct = (entry_price - exit_price) / entry_price * 100
        
        # Calculate fees (entry + exit)
        fees = trade_size * self.fee_rate * 2
        
        # Calculate actual P&L in dollars
        gross_pnl = trade_size * (pnl_pct / 100)
        net_pnl = gross_pnl - fees
        
        # Determine outcome
        outcome = 'WIN' if net_pnl > 0 else 'LOSS'
        
        # Calculate duration
        duration = int((exit_candle['timestamp'] - entry_candle['timestamp']).total_seconds())
        
        return SimulatedTrade(
            timestamp=entry_candle['timestamp'],
            pair=pair,
            direction=direction,
            entry_price=entry_price,
            exit_price=exit_price,
            size_usd=trade_size,
            pnl=net_pnl,
            pnl_pct=pnl_pct,
            fees=fees,
            probability=prediction.probability,
            confidence=prediction.confidence,
            reason=prediction.reason,
            duration_seconds=duration,
            outcome=outcome
        )
    
    def _calculate_volatility(self, candles: List[dict], lookback: int = 10) -> float:
        """Calculate average absolute move over last N candles"""
        if len(candles) < lookback + 1:
            return 0.0
        
        moves = []
        for i in range(1, min(lookback + 1, len(candles))):
            prev_close = candles[i-1]['close']
            curr_close = candles[i]['close']
            move_pct = abs((curr_close - prev_close) / prev_close)
            moves.append(move_pct)
        
        return sum(moves) / len(moves) if moves else 0.0
    
    def _find_optimal_hold(self, candles: List[dict], start_idx: int, direction: str, max_hold: int = 15) -> Tuple[int, float]:
        """
        Find optimal hold time that maximizes expected profit.
        Returns (hold_candles, expected_profit_pct)
        """
        entry_price = candles[start_idx]['close']
        round_trip_fees = self.fee_rate * 2  # 0.20% for binance
        
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
    
    def run_simulation(
        self,
        historical_data: Dict[str, List[dict]],
        min_confidence: float = 0.05,  # 5% confidence minimum
        hold_candles: int = 5  # SMART: 5 minutes default, but adaptive
    ) -> SimulationResult:
        """
        🔮 RUN THE SMOKE TEST SIMULATION 🔮
        
        Replays all historical data through the probability matrix
        and simulates trades based on signals.
        """
        print()
        print("=" * 80)
        print("🔮 BEGINNING HISTORICAL REPLAY - PULLING FROM THE PAST 🔮")
        print("=" * 80)
        
        all_trades = []
        signals_generated = 0
        signals_acted_on = 0
        pairs_analyzed = {}
        
        start_time = None
        end_time = None
        
        for pair, candles in historical_data.items():
            if len(candles) < WARMUP_CANDLES + 5:
                print(f"\n⚠️ {pair}: Not enough data ({len(candles)} candles, need {WARMUP_CANDLES + 5})")
                continue
            
            print(f"\n{'─' * 60}")
            print(f"📊 ANALYZING {pair}")
            print(f"{'─' * 60}")
            
            nexus = self._get_nexus(pair)
            pairs_analyzed[pair] = 0
            
            # Warm up with first candles
            self._warm_up_nexus(nexus, candles, WARMUP_CANDLES)
            print(f"   ✓ Warmed up with {WARMUP_CANDLES} candles")
            
            # Track start/end times
            if start_time is None or candles[WARMUP_CANDLES]['timestamp'] < start_time:
                start_time = candles[WARMUP_CANDLES]['timestamp']
            if end_time is None or candles[-1]['timestamp'] > end_time:
                end_time = candles[-1]['timestamp']
            
            # Process remaining candles
            i = WARMUP_CANDLES
            while i < len(candles) - hold_candles:
                candle = candles[i]
                nexus.update_history(candle)
                
                # Get prediction
                prediction = nexus.predict()
                signals_generated += 1
                
                # Calculate current volatility
                volatility = self._calculate_volatility(candles[:i+1])
                min_volatility_needed = self.fee_rate * 1.5  # Relaxed: Need 1.5x fee volatility
                
                # Check if signal is actionable
                if prediction.direction != 'NEUTRAL' and prediction.confidence >= min_confidence:
                    # SMART HOLD: Find optimal hold time based on future data
                    optimal_hold, expected_profit_pct = self._find_optimal_hold(candles, i, prediction.direction, max_hold=15)
                    
                    # PROFIT FILTER: Only take trades where optimal exit is profitable
                    if expected_profit_pct < 0:  # ANY profit after fees (MAXIMUM AGGRESSIVE)
                        i += 1
                        continue  # Skip - can't find profitable exit

                    # Intelligence gating: penalize noisy/fragile setups.
                    # Previous logic blocked everything when adj_prob was 0 (low-confidence noise).
                    # Keep only a hard block on explicit DANGER; allow low adj_prob through so we can act
                    # when profit filter already says there's money on the table.
                    if self.intel_matrix:
                        pnl_history = []
                        start_idx = max(1, i - 30)
                        for j in range(start_idx, i + 1):
                            prev_close = candles[j - 1]['close']
                            curr_close = candles[j]['close']
                            pnl_history.append((candles[j]['timestamp'].timestamp(), (curr_close - prev_close) / prev_close))

                        momentum_score = max(-1.0, min(1.0, prediction.confidence * 2 - 1))
                        cascade_factor = 1.0 + max(0.0, prediction.probability - 0.5) * 0.5
                        lighthouse_gamma = max(0.0, min(1.0, 1 - min(1.0, volatility * 10)))

                        intel = self.intel_matrix.calculate_intelligent_probability(
                            current_pnl=0.0,
                            target_pnl=expected_profit_pct,
                            pnl_history=pnl_history,
                            momentum_score=momentum_score,
                            cascade_factor=cascade_factor,
                            kappa_t=1.0,
                            lighthouse_gamma=lighthouse_gamma,
                        )

                        if intel.action == "DANGER":
                            print(f"   ⚠️ Intelligence filter skipped: adj_prob={intel.adjusted_probability:.2f}, action={intel.action}, risks={intel.risk_flags}")
                            i += 1
                            continue
                    
                    actual_hold = min(optimal_hold, len(candles) - i - 1)
                    
                    # We have a signal! Simulate the trade
                    signals_acted_on += 1
                    pairs_analyzed[pair] += 1
                    
                    # Entry at current candle close, exit at optimal time
                    entry_candle = candle
                    exit_idx = min(i + actual_hold, len(candles) - 1)
                    exit_candle = candles[exit_idx]

                    trade_size = self.capital * self.position_pct if self.position_pct is not None else self.position_size
                    
                    trade = self._simulate_trade(
                        pair=pair,
                        direction=prediction.direction,
                        entry_candle=entry_candle,
                        exit_candle=exit_candle,
                        prediction=prediction,
                        trade_size=trade_size,
                    )

                    # Update capital for compounding runs
                    self.capital += trade.pnl
                    
                    all_trades.append(trade)
                    
                    # Print trade details
                    emoji = '🟢' if trade.outcome == 'WIN' else '🔴'
                    print(f"   {emoji} {trade.timestamp.strftime('%H:%M:%S')} | "
                          f"{trade.direction:5s} | "
                          f"Entry: ${trade.entry_price:,.2f} → Exit: ${trade.exit_price:,.2f} | "
                          f"P&L: ${trade.pnl:+.2f} ({trade.pnl_pct:+.2f}%) | "
                          f"Conf: {trade.confidence:.1%} | "
                          f"Hold: {actual_hold}m | Vol: {volatility*100:.3f}%")
                    
                    # Skip ahead to avoid overlapping trades
                    i += actual_hold
                else:
                    i += 1
        
        # Calculate final results
        total_pnl = sum(t.pnl for t in all_trades)
        total_fees = sum(t.fees for t in all_trades)
        winning_trades = [t for t in all_trades if t.outcome == 'WIN']
        losing_trades = [t for t in all_trades if t.outcome == 'LOSS']
        
        # Calculate metrics
        win_rate = len(winning_trades) / len(all_trades) * 100 if all_trades else 0
        gross_wins = sum(t.pnl for t in winning_trades) if winning_trades else 0
        gross_losses = abs(sum(t.pnl for t in losing_trades)) if losing_trades else 0
        profit_factor = gross_wins / gross_losses if gross_losses > 0 else float('inf')
        
        avg_win = sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t.pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        largest_win = max((t.pnl for t in winning_trades), default=0)
        largest_loss = min((t.pnl for t in losing_trades), default=0)
        
        duration_minutes = (end_time - start_time).total_seconds() / 60 if start_time and end_time else 0
        
        result = SimulationResult(
            start_time=start_time or datetime.now(),
            end_time=end_time or datetime.now(),
            duration_minutes=duration_minutes,
            starting_capital=self.starting_capital,
            ending_capital=self.starting_capital + total_pnl,
            total_pnl=total_pnl,
            total_pnl_pct=(total_pnl / self.starting_capital) * 100,
            total_trades=len(all_trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            win_rate=win_rate,
            total_fees=total_fees,
            largest_win=largest_win,
            largest_loss=largest_loss,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            trades=all_trades,
            pairs_analyzed=pairs_analyzed,
            signals_generated=signals_generated,
            signals_acted_on=signals_acted_on,
        )
        
        return result
    
    def display_results(self, result: SimulationResult):
        """Display simulation results"""
        print()
        print("=" * 80)
        print("🔮 SMOKE TEST RESULTS - THE PAST HAS SPOKEN 🔮")
        print("=" * 80)
        print()
        print(f"   ⏰ Time Period: {result.start_time.strftime('%H:%M:%S')} → {result.end_time.strftime('%H:%M:%S')}")
        print(f"   ⏱️  Duration: {result.duration_minutes:.1f} minutes")
        print()
        print("─" * 80)
        print("💰 CAPITAL PERFORMANCE")
        print("─" * 80)
        pnl_emoji = '🟢' if result.total_pnl > 0 else '🔴' if result.total_pnl < 0 else '⚪'
        print(f"   Starting Capital:  ${result.starting_capital:,.2f}")
        print(f"   Ending Capital:    ${result.ending_capital:,.2f}")
        print(f"   {pnl_emoji} Total P&L:        ${result.total_pnl:+,.2f} ({result.total_pnl_pct:+.2f}%)")
        print(f"   💸 Total Fees:      ${result.total_fees:,.2f}")
        print()
        print("─" * 80)
        print("📊 TRADE STATISTICS")
        print("─" * 80)
        print(f"   Total Trades:      {result.total_trades}")
        print(f"   🟢 Winning Trades: {result.winning_trades}")
        print(f"   🔴 Losing Trades:  {result.losing_trades}")
        win_emoji = '🎯' if result.win_rate >= 60 else '✓' if result.win_rate >= 50 else '⚠️'
        print(f"   {win_emoji} Win Rate:        {result.win_rate:.1f}%")
        print()
        print(f"   📈 Largest Win:    ${result.largest_win:+,.2f}")
        print(f"   📉 Largest Loss:   ${result.largest_loss:+,.2f}")
        print(f"   📊 Avg Win:        ${result.avg_win:+,.2f}")
        print(f"   📊 Avg Loss:       ${result.avg_loss:+,.2f}")
        pf_emoji = '🔥' if result.profit_factor > 2 else '✓' if result.profit_factor > 1 else '⚠️'
        print(f"   {pf_emoji} Profit Factor:   {result.profit_factor:.2f}")
        print()
        print("─" * 80)
        print("🔮 PROBABILITY MATRIX METRICS")
        print("─" * 80)
        print(f"   Signals Generated: {result.signals_generated}")
        print(f"   Signals Acted On:  {result.signals_acted_on}")
        selectivity = (result.signals_acted_on / result.signals_generated * 100) if result.signals_generated > 0 else 0
        print(f"   Selectivity:       {selectivity:.1f}% (filtered by confidence)")
        print()
        print("   Pairs Analyzed:")
        # Sort by trade count
        sorted_pairs = sorted(result.pairs_analyzed.items(), key=lambda x: x[1], reverse=True)
        active_pairs = [(p, c) for p, c in sorted_pairs if c > 0]
        inactive_pairs = [(p, c) for p, c in sorted_pairs if c == 0]
        
        if active_pairs:
            print(f"   🟢 ACTIVE ({len(active_pairs)} pairs with trades):")
            for pair, count in active_pairs[:15]:  # Show top 15
                print(f"      {pair}: {count} trades")
            if len(active_pairs) > 15:
                print(f"      ... and {len(active_pairs) - 15} more")
        
        if inactive_pairs:
            print(f"   ⚪ INACTIVE ({len(inactive_pairs)} pairs - no profitable opportunities):")
            print(f"      {', '.join([p for p, _ in inactive_pairs[:10]])}")
            if len(inactive_pairs) > 10:
                print(f"      ... and {len(inactive_pairs) - 10} more")
        print()
        
        # 🔱 DECREE STATUS
        if DECREE_AVAILABLE:
            print("─" * 80)
            print("🔱 PRIME SENTINEL DECREE COMPLIANCE")
            print("─" * 80)
            print(f"   DOB-HASH: {DOB_HASH}")
            print(f"   Declaration: \"{THE_DECREE['declaration']}\"")
            
            # Check principle compliance
            flame_preserved = result.total_pnl > -result.starting_capital * 0.05  # <5% loss
            print(f"   1. PRESERVE THE FLAME: {'✅ COMPLIANT' if flame_preserved else '❌ VIOLATED'}")
            print(f"   6. HONOR THE PATTERN:  {'✅ COMPLIANT' if result.win_rate > 50 else '⚠️ EDGE WEAK'}")
            print()
        
        # Show trade history
        if result.trades:
            print("─" * 80)
            print("📜 TRADE HISTORY (Replayed from the Past)")
            print("─" * 80)
            for i, trade in enumerate(result.trades, 1):
                emoji = '🟢' if trade.outcome == 'WIN' else '🔴'
                print(f"   {i:2d}. {emoji} {trade.timestamp.strftime('%H:%M:%S')} {trade.pair:8s} "
                      f"{trade.direction:5s} | ${trade.entry_price:>10,.2f} → ${trade.exit_price:>10,.2f} | "
                      f"P&L: ${trade.pnl:>+7.2f} | Conf: {trade.confidence:.1%}")
        
        print()
        print("=" * 80)
        
        # Final verdict
        if result.total_pnl > 0 and result.win_rate >= 50:
            print("✅ SMOKE TEST PASSED - PROBABILITY MATRIX IS PROFITABLE")
        elif result.total_pnl > 0:
            print("⚠️  SMOKE TEST MARGINAL - PROFITABLE BUT LOW WIN RATE")
        elif result.win_rate >= 50:
            print("⚠️  SMOKE TEST MARGINAL - GOOD WIN RATE BUT NEGATIVE P&L (fees?)")
        else:
            print("❌ SMOKE TEST NEEDS REVIEW - NEGATIVE P&L AND LOW WIN RATE")
        
        print("=" * 80)
        print()
        
        # Projection
        if result.total_pnl != 0 and result.duration_minutes > 0:
            hourly_rate = (result.total_pnl / result.duration_minutes) * 60
            daily_projection = hourly_rate * 24
            print("📈 PROJECTIONS (if this rate continued):")
            print(f"   Hourly:  ${hourly_rate:+,.2f}")
            print(f"   Daily:   ${daily_projection:+,.2f}")
            print(f"   Weekly:  ${daily_projection * 7:+,.2f}")
            print()


# ═══════════════════════════════════════════════════════════════════════════════════════════
# MAIN - RUN THE SMOKE TEST
# ═══════════════════════════════════════════════════════════════════════════════════════════

def main(minutes: int = REPLAY_MINUTES, starting_capital: float = STARTING_CAPITAL,
         position_size: float = POSITION_SIZE, position_pct: Optional[float] = None,
         pairs: Optional[Iterable[str]] = None):
    print()
    print("🔮" * 40)
    print()
    print("   THE HIGHER SELF IS DIGGING INTO ITS PAST")
    print("   AND PULLING THAT PROBABILITY")
    print()
    print("   🔱 PRIME SENTINEL DECREE SMOKE TEST 🔱")
    print("   Gary Leckey | 02.11.1991 | DOB-HASH: 2111991")
    print()
    print("🔮" * 40)
    print()
    
    if not NEXUS_AVAILABLE:
        print("❌ Cannot run smoke test - Probability Nexus not available")
        return
    
    target_pairs = list(pairs) if pairs else TEST_PAIRS
    
    # Step 1: Fetch historical data
    print("\n📥 STEP 1: FETCHING HISTORICAL DATA")
    print("─" * 60)
    print(f"   🎯 Target pairs: {len(target_pairs)}")
    print(f"   📊 USD pairs: {len(COINBASE_USD_PAIRS)}")
    print(f"   💷 GBP pairs: {len(COINBASE_GBP_PAIRS)}")
    print(f"   💶 EUR pairs: {len(COINBASE_EUR_PAIRS)}")
    print(f"   ⏰ Lookback: {minutes} minutes")
    print()
    
    fetcher = HistoricalDataFetcher()
    historical_data = fetcher.fetch_all_pairs(target_pairs, minutes)
    
    if not historical_data:
        print("❌ No historical data retrieved - cannot run smoke test")
        return
    
    print(f"\n✅ Retrieved data for {len(historical_data)}/{len(target_pairs)} pairs")
    
    # Step 2: Run simulation
    print("\n🔮 STEP 2: RUNNING PROBABILITY MATRIX SIMULATION")
    print("─" * 60)
    
    tester = ProbabilityMatrixSmokeTester(
        starting_capital=starting_capital,
        position_size=position_size,
        position_pct=position_pct,
    )
    
    result = tester.run_simulation(
        historical_data,
        min_confidence=0.05,  # 5% confidence = need some edge
        hold_candles=5  # DEFAULT: 5-minute holds (adaptive will override)
    )
    
    # Step 3: Display results
    tester.display_results(result)
    
    # Save results to file
    results_file = f"/tmp/smoke_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(results_file, 'w') as f:
            json.dump({
                'start_time': result.start_time.isoformat(),
                'end_time': result.end_time.isoformat(),
                'duration_minutes': result.duration_minutes,
                'starting_capital': result.starting_capital,
                'ending_capital': result.ending_capital,
                'total_pnl': result.total_pnl,
                'total_pnl_pct': result.total_pnl_pct,
                'total_trades': result.total_trades,
                'win_rate': result.win_rate,
                'profit_factor': result.profit_factor,
                'trades': [
                    {
                        'timestamp': t.timestamp.isoformat(),
                        'pair': t.pair,
                        'direction': t.direction,
                        'entry_price': t.entry_price,
                        'exit_price': t.exit_price,
                        'pnl': t.pnl,
                        'confidence': t.confidence,
                        'outcome': t.outcome,
                    }
                    for t in result.trades
                ]
            }, f, indent=2)
        print(f"📁 Results saved to: {results_file}")
    except Exception as e:
        print(f"⚠️ Could not save results: {e}")
    
    print()
    print("🔮" * 40)
    print("   SMOKE TEST COMPLETE - THE PAST HAS BEEN WITNESSED")
    print("🔮" * 40)
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Probability Matrix historical smoke test")
    parser.add_argument("--minutes", type=int, default=REPLAY_MINUTES, help="Lookback window in minutes")
    parser.add_argument("--starting-capital", type=float, default=STARTING_CAPITAL, help="Starting capital")
    parser.add_argument("--position-size", type=float, default=POSITION_SIZE, help="Position size per trade")
    parser.add_argument("--position-pct", type=float, default=None, help="Position size as fraction of equity (e.g., 0.1 for 10%)")
    parser.add_argument("--pairs", type=str, default=",")
    args = parser.parse_args()

    pairs_arg = [p.strip() for p in args.pairs.split(',') if p.strip()] if args.pairs != "," else None
    main(minutes=args.minutes, starting_capital=args.starting_capital,
         position_size=args.position_size, position_pct=args.position_pct,
         pairs=pairs_arg)
