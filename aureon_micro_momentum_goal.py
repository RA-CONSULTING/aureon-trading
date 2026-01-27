#!/usr/bin/env python3
"""
🎯⚡ AUREON MICRO-MOMENTUM GOAL ⚡🎯
═══════════════════════════════════════════════════════════════════════════════

THE GOAL: Find coins moving FAST ENOUGH to beat trading costs in 30 seconds!

💸 COST REALITY (per round trip):
   - Fee (entry+exit):  0.30%
   - Spread:            0.02%
   - Slippage:          0.02%
   ─────────────────────────────
   TOTAL COST:          0.34%
   
🎯 THE MISSION: Find coins that have ALREADY moved > 0.34% in the last few minutes
   - This proves momentum EXISTS
   - We ride the wave, not predict it
   - Enter when momentum is CONFIRMED, exit in 30 seconds

📊 MOMENTUM TIERS:
   🔥 TIER 1: > 0.5% move in last 1 min  → IMMEDIATE ENTRY
   ⚡ TIER 2: > 0.4% move in last 5 min  → HIGH PRIORITY
   🌊 TIER 3: > 0.34% move in last 5 min → VALID (covers costs)
   ❄️ TIER 4: < 0.34% move              → SKIP (won't cover costs)

Gary Leckey | Aureon Trading System | January 2026
═══════════════════════════════════════════════════════════════════════════════
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        def _is_utf8_wrapper(stream):
            return (isinstance(stream, io.TextIOWrapper) and 
                    hasattr(stream, 'encoding') and stream.encoding and
                    stream.encoding.lower().replace('-', '') == 'utf8')
        if hasattr(sys.stdout, 'buffer') and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        # Skip stderr wrapping (causes Windows exit errors)
    except Exception:
        pass

import requests
import time
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# 💸 THE GOAL - COST THRESHOLDS (WE CANNOT BLEED!)
# ═══════════════════════════════════════════════════════════════════════════════

class CostProfile:
    """Trading cost profiles for different exchanges"""
    
    ALPACA = {
        'name': 'Alpaca',
        'fee_one_way': 0.0015,      # 0.15%
        'spread': 0.0002,           # 0.02%
        'slippage': 0.0001,         # 0.01%
        'round_trip': 0.0034,       # 0.34%
    }
    
    KRAKEN_MAKER = {
        'name': 'Kraken Maker',
        'fee_one_way': 0.0016,      # 0.16%
        'spread': 0.0001,           # 0.01%
        'slippage': 0.0001,         # 0.01%
        'round_trip': 0.0036,       # 0.36%
    }
    
    KRAKEN_TAKER = {
        'name': 'Kraken Taker',
        'fee_one_way': 0.0026,      # 0.26%
        'spread': 0.0001,           # 0.01%
        'slippage': 0.0001,         # 0.01%
        'round_trip': 0.0056,       # 0.56%
    }
    
    BINANCE = {
        'name': 'Binance',
        'fee_one_way': 0.0010,      # 0.10%
        'spread': 0.0001,           # 0.01%
        'slippage': 0.0001,         # 0.01%
        'round_trip': 0.0024,       # 0.24%
    }

# Default: Alpaca
DEFAULT_COST = CostProfile.ALPACA
BREAK_EVEN_THRESHOLD = DEFAULT_COST['round_trip'] * 100  # 0.34%

# 👑 QUEEN'S SACRED 1.88% LAW - MOMENTUM MUST SERVE PROFIT
QUEEN_MIN_COP = 1.0188              # Sacred constant: 1.88% minimum realized profit
QUEEN_MIN_PROFIT_PCT = 1.88         # Percentage form
QUEEN_MIN_GROSS_PCT = 2.60          # Gross move needed to net 1.88% (after ~0.72% fees)
QUEEN_MOMENTUM_PROFIT_FREQ = 188.0  # Hz - Sacred frequency for momentum profits


# ═══════════════════════════════════════════════════════════════════════════════
# 🎯 MOMENTUM TIERS - QUEEN'S 1.88% ALIGNED
# ═══════════════════════════════════════════════════════════════════════════════

class MomentumTier(Enum):
    """Momentum classification for micro-scalping"""
    TIER_1_HOT = "🔥 TIER 1"      # > 0.5% in 1 min - IMMEDIATE
    TIER_2_STRONG = "⚡ TIER 2"   # > 0.4% in 5 min - HIGH PRIORITY
    TIER_3_VALID = "🌊 TIER 3"    # > 0.34% in 5 min - VALID
    TIER_4_SKIP = "❄️ SKIP"       # < 0.34% - NOT WORTH IT


@dataclass
class MomentumSignal:
    """A detected momentum signal"""
    symbol: str
    exchange: str
    tier: MomentumTier
    
    # Price data
    current_price: float
    price_1m_ago: float
    price_5m_ago: float
    
    # Momentum metrics
    momentum_1m_pct: float        # % change in last 1 min
    momentum_5m_pct: float        # % change in last 5 min
    
    # Cost analysis
    break_even_threshold: float   # Cost to beat
    net_profit_potential: float   # Gross move - costs
    
    # Timing
    timestamp: float = field(default_factory=time.time)
    
    # Direction
    direction: str = "LONG"       # LONG or SHORT
    
    def is_profitable(self) -> bool:
        """Is this signal expected to be profitable after costs?"""
        return self.net_profit_potential > 0
    
    def __str__(self) -> str:
        return (f"{self.tier.value} | {self.symbol:12s} | "
                f"1m: {self.momentum_1m_pct:+.3f}% | "
                f"5m: {self.momentum_5m_pct:+.3f}% | "
                f"Net: {self.net_profit_potential:+.3f}%")


# ═══════════════════════════════════════════════════════════════════════════════
# 🔍 MICRO-MOMENTUM SCANNER
# ═══════════════════════════════════════════════════════════════════════════════

class MicroMomentumScanner:
    """
    Scans for MICRO-MOMENTUM opportunities that can beat trading costs.
    
    THE GOAL: Find coins moving > 0.34% so we can profit in 30 seconds!
    """
    
    # All available crypto pairs
    ALL_COINS = [
        "BTC/USD", "ETH/USD", "SOL/USD", "DOGE/USD", "XRP/USD", 
        "LINK/USD", "AVAX/USD", "MATIC/USD", "DOT/USD", "ADA/USD",
        "UNI/USD", "LTC/USD", "BCH/USD", "ATOM/USD", "AAVE/USD",
        "MKR/USD", "CRV/USD", "SUSHI/USD", "ALGO/USD", "NEAR/USD",
        "GRT/USD", "BAT/USD"
    ]
    
    def __init__(self, cost_profile: Dict = None):
        """Initialize with cost profile"""
        self.cost_profile = cost_profile or DEFAULT_COST
        self.break_even = self.cost_profile['round_trip'] * 100
        
        # Cache for 1-minute bars
        self._bar_cache: Dict[str, List] = {}
        self._cache_time: float = 0
        self._cache_duration = 10  # seconds
        
        logger.info(f"🎯 MicroMomentumScanner initialized")
        logger.info(f"   Break-even threshold: {self.break_even:.3f}%")
        logger.info(f"   Cost profile: {self.cost_profile['name']}")
    
    def _fetch_1min_bars(self, symbols: List[str], lookback_minutes: int = 10) -> Dict[str, List]:
        """Fetch 1-minute bars for momentum calculation"""
        
        # Use cache if fresh
        if time.time() - self._cache_time < self._cache_duration and self._bar_cache:
            return self._bar_cache
        
        bars_by_symbol = {}
        
        end = datetime.now(timezone.utc)
        start = end - timedelta(minutes=lookback_minutes)
        
        # Fetch in batches to avoid rate limits
        symbols_str = ','.join(symbols)
        
        try:
            resp = requests.get(
                'https://data.alpaca.markets/v1beta3/crypto/us/bars',
                params={
                    'symbols': symbols_str,
                    'timeframe': '1Min',
                    'start': start.isoformat(),
                    'end': end.isoformat(),
                    'limit': 1000
                },
                timeout=10
            )
            
            data = resp.json()
            
            for symbol, bars in data.get('bars', {}).items():
                if bars:
                    bars_by_symbol[symbol] = bars
            
            self._bar_cache = bars_by_symbol
            self._cache_time = time.time()
            
        except Exception as e:
            logger.error(f"Failed to fetch 1-min bars: {e}")
        
        return bars_by_symbol
    
    def scan_for_momentum(self, symbols: List[str] = None) -> List[MomentumSignal]:
        """
        🎯 THE MAIN SCAN - Find coins with enough momentum to beat costs!
        
        Returns list of MomentumSignal sorted by profit potential.
        """
        if symbols is None:
            symbols = self.ALL_COINS
        
        # Fetch fresh 1-minute bars
        bars_by_symbol = self._fetch_1min_bars(symbols, lookback_minutes=10)
        
        signals: List[MomentumSignal] = []
        
        for symbol in symbols:
            bars = bars_by_symbol.get(symbol, [])
            
            if len(bars) < 6:  # Need at least 6 bars (5 min history)
                continue
            
            # Current price
            current_bar = bars[-1]
            current_price = float(current_bar['c'])
            
            # Price 1 minute ago
            price_1m_ago = float(bars[-2]['c']) if len(bars) >= 2 else current_price
            
            # Price 5 minutes ago
            price_5m_ago = float(bars[-6]['c']) if len(bars) >= 6 else current_price
            
            # Calculate momentum
            momentum_1m = ((current_price - price_1m_ago) / price_1m_ago) * 100 if price_1m_ago > 0 else 0
            momentum_5m = ((current_price - price_5m_ago) / price_5m_ago) * 100 if price_5m_ago > 0 else 0
            
            # Classify tier based on momentum
            abs_momentum_1m = abs(momentum_1m)
            abs_momentum_5m = abs(momentum_5m)
            
            if abs_momentum_1m >= 0.5:
                tier = MomentumTier.TIER_1_HOT
            elif abs_momentum_5m >= 0.4:
                tier = MomentumTier.TIER_2_STRONG
            elif abs_momentum_5m >= self.break_even:
                tier = MomentumTier.TIER_3_VALID
            else:
                tier = MomentumTier.TIER_4_SKIP
            
            # Calculate net profit potential (use higher of 1m or 5m momentum)
            gross_move = max(abs_momentum_1m, abs_momentum_5m)
            net_profit = gross_move - self.break_even
            
            # Direction
            direction = "LONG" if (momentum_1m + momentum_5m) > 0 else "SHORT"
            
            signal = MomentumSignal(
                symbol=symbol,
                exchange='alpaca',
                tier=tier,
                current_price=current_price,
                price_1m_ago=price_1m_ago,
                price_5m_ago=price_5m_ago,
                momentum_1m_pct=momentum_1m,
                momentum_5m_pct=momentum_5m,
                break_even_threshold=self.break_even,
                net_profit_potential=net_profit,
                direction=direction
            )
            
            signals.append(signal)
        
        # Sort by net profit potential (descending)
        signals.sort(key=lambda s: s.net_profit_potential, reverse=True)
        
        return signals
    
    def get_actionable_signals(self) -> List[MomentumSignal]:
        """Get only signals that are worth acting on (TIER 1-3)"""
        all_signals = self.scan_for_momentum()
        return [s for s in all_signals if s.tier != MomentumTier.TIER_4_SKIP]
    
    def get_hot_signals(self) -> List[MomentumSignal]:
        """Get only TIER 1 (hot) signals - > 0.5% in 1 min"""
        all_signals = self.scan_for_momentum()
        return [s for s in all_signals if s.tier == MomentumTier.TIER_1_HOT]
    
    def print_scan_results(self, signals: List[MomentumSignal] = None):
        """Pretty print scan results showing THE GOAL"""
        if signals is None:
            signals = self.scan_for_momentum()
        
        print("\n" + "="*70)
        print("🎯 MICRO-MOMENTUM SCAN - THE GOAL: Beat 0.34% trading costs!")
        print("="*70)
        print(f"\n💸 Cost Breakdown ({self.cost_profile['name']}):")
        print(f"   Fee (entry+exit):  {self.cost_profile['fee_one_way']*2*100:.3f}%")
        print(f"   Spread:            {self.cost_profile['spread']*100:.3f}%")
        print(f"   Slippage:          {self.cost_profile['slippage']*2*100:.3f}%")
        print(f"   ─────────────────────────────")
        print(f"   BREAK-EVEN:        {self.break_even:.3f}%")
        print()
        
        # Count tiers
        tier_counts = {t: 0 for t in MomentumTier}
        for s in signals:
            tier_counts[s.tier] += 1
        
        print(f"📊 Momentum Tiers Detected:")
        print(f"   🔥 TIER 1 (>0.5% in 1min): {tier_counts[MomentumTier.TIER_1_HOT]} coins")
        print(f"   ⚡ TIER 2 (>0.4% in 5min): {tier_counts[MomentumTier.TIER_2_STRONG]} coins")
        print(f"   🌊 TIER 3 (>0.34% in 5min): {tier_counts[MomentumTier.TIER_3_VALID]} coins")
        print(f"   ❄️ SKIP  (<0.34%):          {tier_counts[MomentumTier.TIER_4_SKIP]} coins")
        print()
        
        print("-"*70)
        print(f"{'Tier':<12} | {'Symbol':<12} | {'1min':>8} | {'5min':>8} | {'Net Profit':>10}")
        print("-"*70)
        
        for signal in signals:
            if signal.tier != MomentumTier.TIER_4_SKIP:
                profit_str = f"+{signal.net_profit_potential:.3f}%" if signal.net_profit_potential > 0 else f"{signal.net_profit_potential:.3f}%"
                print(f"{signal.tier.value:<12} | {signal.symbol:<12} | "
                      f"{signal.momentum_1m_pct:>+7.3f}% | "
                      f"{signal.momentum_5m_pct:>+7.3f}% | "
                      f"{profit_str:>10}")
        
        print("-"*70)
        
        # Best opportunity
        actionable = [s for s in signals if s.tier != MomentumTier.TIER_4_SKIP and s.net_profit_potential > 0]
        if actionable:
            best = actionable[0]
            print(f"\n🎯 BEST OPPORTUNITY:")
            print(f"   Symbol:       {best.symbol}")
            print(f"   Direction:    {best.direction}")
            print(f"   1min Move:    {best.momentum_1m_pct:+.3f}%")
            print(f"   5min Move:    {best.momentum_5m_pct:+.3f}%")
            print(f"   Gross Move:   {max(abs(best.momentum_1m_pct), abs(best.momentum_5m_pct)):.3f}%")
            print(f"   Cost:         {self.break_even:.3f}%")
            print(f"   NET PROFIT:   {best.net_profit_potential:+.3f}%")
            print(f"\n   ✅ EXECUTE: {best.direction} {best.symbol} @ ${best.current_price:.4f}")
        else:
            print(f"\n⏳ No coins currently moving > {self.break_even:.3f}%")
            print("   Waiting for momentum spike...")
        
        print("="*70)
        
        return signals


# ═══════════════════════════════════════════════════════════════════════════════
# 🚀 MAIN - Show scanners THE GOAL!
# ═══════════════════════════════════════════════════════════════════════════════

def show_the_goal():
    """Show the existing scanners what THE GOAL is!"""
    
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║     🎯⚡ THE GOAL - MICRO-MOMENTUM THAT BEATS COSTS ⚡🎯                      ║
║                                                                              ║
║     MISSION: Find coins moving FAST ENOUGH to profit in 30 seconds!         ║
║                                                                              ║
║     💸 COST TO BEAT: 0.34% per trade                                        ║
║                                                                              ║
║     📊 WHAT WE'RE LOOKING FOR:                                              ║
║        🔥 TIER 1: > 0.5% move in 1 min  → IMMEDIATE ENTRY                   ║
║        ⚡ TIER 2: > 0.4% move in 5 min  → HIGH PRIORITY                     ║
║        🌊 TIER 3: > 0.34% move in 5 min → VALID (covers costs)              ║
║        ❄️ TIER 4: < 0.34% move          → SKIP (won't cover costs)          ║
║                                                                              ║
║     ⚠️ WE CANNOT BLEED! Every trade must beat 0.34% to profit!              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    scanner = MicroMomentumScanner()
    signals = scanner.print_scan_results()
    
    return signals


if __name__ == "__main__":
    show_the_goal()
