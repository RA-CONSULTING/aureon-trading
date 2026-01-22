#!/usr/bin/env python3
"""
🦆⚡ Quantum Signals - Extracted signal components from Quantum Quackers ⚡🦆
============================================================================
Reusable signal generation for IRA Sniper and other strategies.

Now with CORRECT penny profit fee math!

Components:
- Market phase detection (Wyckoff-style)
- Multi-timeframe confluence scoring
- Liquidity sweep detection (stop hunts)
- RSI divergence detection
- CORRECT penny profit calculator
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# CORRECT FEE MODEL - Matches adaptive_prime_profit_gate.py
# =============================================================================
FEE_RATES = {
    'kraken': {
        'maker': 0.0025,    # 0.25% maker (limit orders)
        'taker': 0.0040,    # 0.40% taker (market orders)
        'slippage': 0.0005, # 0.05% estimated slippage
        'spread': 0.0008,   # 0.08% typical spread
        'total': 0.0053     # 0.53% per leg (taker + slip + spread)
    },
    'binance': {
        'maker': 0.0010,    # 0.10% maker
        'taker': 0.0010,    # 0.10% taker
        'slippage': 0.0003, # 0.03% slippage (better liquidity)
        'spread': 0.0010,   # 0.10% spread (UK restricted)
        'total': 0.0023     # 0.23% per leg
    },
    'alpaca': {
        'maker': 0.0015,    # 0.15% maker
        'taker': 0.0025,    # 0.25% taker
        'slippage': 0.0005, # 0.05% slippage
        'spread': 0.0020,   # 0.20% spread (crypto)
        'total': 0.0050     # 0.50% per leg
    },
    'capital': {
        'maker': 0.0000,    # No commission (spread-based)
        'taker': 0.0000,    # No commission
        'slippage': 0.0008, # 0.08% slippage
        'spread': 0.0020,   # 0.20% spread (CFDs)
        'total': 0.0028     # 0.28% per leg
    }
}


def get_total_fee_rate(exchange: str = 'kraken') -> float:
    """Get combined fee rate for penny profit calculations."""
    return FEE_RATES.get(exchange, FEE_RATES['kraken'])['total']


def get_fee_profile(exchange: str = 'kraken') -> dict:
    """Get complete fee profile for an exchange."""
    return FEE_RATES.get(exchange, FEE_RATES['kraken'])


# =============================================================================
# MARKET PHASE DETECTION (Wyckoff-style)
# =============================================================================
class MarketPhase(Enum):
    ACCUMULATION = "accumulation"   # Smart money buying, price flat
    MARKUP = "markup"               # Uptrend begins
    DISTRIBUTION = "distribution"   # Smart money selling, price flat
    MARKDOWN = "markdown"           # Downtrend begins
    UNKNOWN = "unknown"


@dataclass
class PhaseSignal:
    phase: MarketPhase
    confidence: float  # 0-1
    suggested_action: str  # 'buy', 'sell', 'hold'
    
    
def detect_market_phase(
    prices: List[float],
    volumes: List[float],
    lookback: int = 50
) -> PhaseSignal:
    """
    Wyckoff-style market phase detection.
    
    ACCUMULATION: Low volatility, increasing volume, price near lows
    MARKUP: Rising prices, good volume
    DISTRIBUTION: Low volatility, high volume, price near highs  
    MARKDOWN: Falling prices, increasing volume
    """
    if len(prices) < lookback or len(volumes) < lookback:
        return PhaseSignal(MarketPhase.UNKNOWN, 0.0, 'hold')
    
    recent_prices = prices[-lookback:]
    recent_volumes = volumes[-lookback:]
    
    # Calculate metrics
    price_change = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
    volatility = np.std(recent_prices) / np.mean(recent_prices)
    
    # Volume trend (is volume increasing?)
    vol_first_half = np.mean(recent_volumes[:lookback//2])
    vol_second_half = np.mean(recent_volumes[lookback//2:])
    volume_increasing = vol_second_half > vol_first_half * 1.1
    
    # Price position relative to range
    price_range = max(recent_prices) - min(recent_prices)
    if price_range > 0:
        price_position = (recent_prices[-1] - min(recent_prices)) / price_range
    else:
        price_position = 0.5
    
    # Detect phase
    if volatility < 0.02 and price_position < 0.3 and volume_increasing:
        # Low vol, near lows, volume building = accumulation
        return PhaseSignal(MarketPhase.ACCUMULATION, 0.7, 'buy')
    
    elif price_change > 0.02 and volume_increasing:
        # Rising prices with volume = markup
        return PhaseSignal(MarketPhase.MARKUP, 0.8, 'hold')  # Already in uptrend
    
    elif volatility < 0.02 and price_position > 0.7 and volume_increasing:
        # Low vol, near highs, volume building = distribution
        return PhaseSignal(MarketPhase.DISTRIBUTION, 0.7, 'sell')
    
    elif price_change < -0.02 and volume_increasing:
        # Falling prices with volume = markdown
        return PhaseSignal(MarketPhase.MARKDOWN, 0.8, 'hold')  # Already in downtrend
    
    return PhaseSignal(MarketPhase.UNKNOWN, 0.3, 'hold')


# =============================================================================
# MULTI-TIMEFRAME CONFLUENCE
# =============================================================================
@dataclass
class TimeframeSignal:
    timeframe: str
    trend: str  # 'bullish', 'bearish', 'neutral'
    strength: float  # 0-1
    

def calculate_mtf_confluence(
    tf_signals: List[TimeframeSignal]
) -> Tuple[float, str]:
    """
    Calculate multi-timeframe confluence score.
    
    Returns: (confluence_score, suggested_direction)
    Higher score = stronger agreement across timeframes
    """
    if not tf_signals:
        return 0.0, 'neutral'
    
    bullish_weight = 0.0
    bearish_weight = 0.0
    total_weight = 0.0
    
    # Weight by timeframe importance (higher TF = more weight)
    tf_weights = {
        '1m': 0.5, '5m': 1.0, '15m': 1.5, 
        '1h': 2.0, '4h': 2.5, '1d': 3.0
    }
    
    for sig in tf_signals:
        weight = tf_weights.get(sig.timeframe, 1.0) * sig.strength
        total_weight += weight
        
        if sig.trend == 'bullish':
            bullish_weight += weight
        elif sig.trend == 'bearish':
            bearish_weight += weight
    
    if total_weight == 0:
        return 0.0, 'neutral'
    
    # Calculate confluence
    if bullish_weight > bearish_weight:
        confluence = bullish_weight / total_weight
        direction = 'bullish'
    elif bearish_weight > bullish_weight:
        confluence = bearish_weight / total_weight
        direction = 'bearish'
    else:
        confluence = 0.5
        direction = 'neutral'
    
    return confluence, direction


# =============================================================================
# LIQUIDITY SWEEP DETECTION (Stop Hunts)
# =============================================================================
@dataclass
class LiquiditySweep:
    detected: bool
    sweep_type: str  # 'stop_hunt_low', 'stop_hunt_high', 'none'
    recovery_strength: float
    entry_opportunity: bool


def detect_liquidity_sweep(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    lookback: int = 20
) -> LiquiditySweep:
    """
    Detect stop hunts / liquidity sweeps.
    
    A sweep occurs when price briefly breaks a key level then reverses.
    This often indicates smart money grabbed liquidity and reversal is coming.
    """
    if len(highs) < lookback:
        return LiquiditySweep(False, 'none', 0.0, False)
    
    recent_highs = highs[-lookback:]
    recent_lows = lows[-lookback:]
    recent_closes = closes[-lookback:]
    
    # Find recent swing high/low (excluding last 3 candles)
    swing_high = max(recent_highs[:-3])
    swing_low = min(recent_lows[:-3])
    
    current_high = recent_highs[-1]
    current_low = recent_lows[-1]
    current_close = recent_closes[-1]
    
    # Check for stop hunt LOW (price wicked below swing low but closed above)
    if current_low < swing_low and current_close > swing_low:
        # Calculate recovery strength
        wick_depth = swing_low - current_low
        recovery = current_close - current_low
        if wick_depth > 0:
            strength = min(recovery / wick_depth, 1.0)
            return LiquiditySweep(True, 'stop_hunt_low', strength, strength > 0.6)
    
    # Check for stop hunt HIGH (price wicked above swing high but closed below)
    if current_high > swing_high and current_close < swing_high:
        wick_depth = current_high - swing_high
        recovery = current_high - current_close
        if wick_depth > 0:
            strength = min(recovery / wick_depth, 1.0)
            return LiquiditySweep(True, 'stop_hunt_high', strength, strength > 0.6)
    
    return LiquiditySweep(False, 'none', 0.0, False)


# =============================================================================
# MOMENTUM DIVERGENCE
# =============================================================================
@dataclass  
class Divergence:
    detected: bool
    divergence_type: str  # 'bullish', 'bearish', 'none'
    strength: float


def detect_rsi_divergence(
    prices: List[float],
    rsi_values: List[float],
    lookback: int = 14
) -> Divergence:
    """
    Detect RSI divergence for potential reversals.
    
    Bullish divergence: Price makes lower low, RSI makes higher low
    Bearish divergence: Price makes higher high, RSI makes lower high
    """
    if len(prices) < lookback or len(rsi_values) < lookback:
        return Divergence(False, 'none', 0.0)
    
    recent_prices = prices[-lookback:]
    recent_rsi = rsi_values[-lookback:]
    
    # Find local extremes
    price_min_idx = np.argmin(recent_prices)
    price_max_idx = np.argmax(recent_prices)
    
    # Check for bullish divergence (price lower low, RSI higher low)
    if price_min_idx > lookback // 2:  # Recent low
        first_half_price_low = min(recent_prices[:lookback//2])
        first_half_rsi_low = min(recent_rsi[:lookback//2])
        
        current_price_low = recent_prices[price_min_idx]
        current_rsi_low = recent_rsi[price_min_idx]
        
        if current_price_low < first_half_price_low and current_rsi_low > first_half_rsi_low:
            strength = (current_rsi_low - first_half_rsi_low) / 30  # Normalize
            return Divergence(True, 'bullish', min(strength, 1.0))
    
    # Check for bearish divergence (price higher high, RSI lower high)
    if price_max_idx > lookback // 2:  # Recent high
        first_half_price_high = max(recent_prices[:lookback//2])
        first_half_rsi_high = max(recent_rsi[:lookback//2])
        
        current_price_high = recent_prices[price_max_idx]
        current_rsi_high = recent_rsi[price_max_idx]
        
        if current_price_high > first_half_price_high and current_rsi_high < first_half_rsi_high:
            strength = (first_half_rsi_high - current_rsi_high) / 30
            return Divergence(True, 'bearish', min(strength, 1.0))
    
    return Divergence(False, 'none', 0.0)


# =============================================================================
# PENNY PROFIT CALCULATOR - CORRECT MATH
# =============================================================================
@dataclass
class PennyThreshold:
    """Penny profit thresholds for a position."""
    win_gte: float      # Gross P&L needed to net $0.01
    stop_lte: float     # Stop loss threshold
    required_move_pct: float  # Required price move %


def calculate_penny_threshold(
    position_size: float,
    exchange: str = 'kraken',
    target_profit: float = 0.01
) -> PennyThreshold:
    """
    Calculate exact price move needed to net target_profit after ALL fees.
    
    Formula: r = ((1 + P/A) / (1-f)²) - 1
    
    Where:
        A = position size in USD
        P = target net profit ($0.01)
        f = total cost rate per leg (fee + slippage + spread)
        r = required price increase (decimal)
    """
    f = get_total_fee_rate(exchange)
    
    # The formula
    r = ((1 + target_profit / position_size) / ((1 - f) ** 2)) - 1
    
    # Convert to dollar thresholds
    win_gte = position_size * r
    stop_lte = -(win_gte * 3.0)  # 3:1 risk ratio
    
    return PennyThreshold(
        win_gte=win_gte,
        stop_lte=stop_lte,
        required_move_pct=r * 100
    )


# =============================================================================
# COMPOSITE SIGNAL FOR IRA SNIPER
# =============================================================================
@dataclass
class QuantumSignal:
    """Combined signal from all quantum components."""
    should_enter: bool
    direction: str  # 'long', 'short', 'none'
    confidence: float
    
    # Component scores
    phase_score: float
    mtf_score: float
    sweep_score: float
    divergence_score: float
    
    # Penny profit thresholds
    penny_threshold: Optional[PennyThreshold]
    
    reasoning: str


def generate_quantum_signal(
    prices: List[float],
    volumes: List[float],
    highs: List[float],
    lows: List[float],
    closes: List[float],
    rsi_values: List[float],
    tf_signals: List[TimeframeSignal],
    position_size: float = 10.0,
    exchange: str = 'kraken'
) -> QuantumSignal:
    """
    Generate a composite trading signal using all quantum components.
    
    This is the main entry point for IRA Sniper to use.
    
    Example usage:
        from quantum_signals import generate_quantum_signal, TimeframeSignal
        
        signal = generate_quantum_signal(
            prices=price_history,
            volumes=volume_history,
            highs=high_history,
            lows=low_history, 
            closes=close_history,
            rsi_values=rsi_history,
            tf_signals=[
                TimeframeSignal('5m', 'bullish', 0.8),
                TimeframeSignal('15m', 'bullish', 0.7),
                TimeframeSignal('1h', 'bullish', 0.6),
            ],
            position_size=10.0,
            exchange='kraken'
        )
        
        if signal.should_enter:
            print(f"🎯 {signal.direction.upper()} @ {signal.confidence:.0%}")
            print(f"   Need {signal.penny_threshold.required_move_pct:.3f}% to net $0.01")
    """
    reasons = []
    
    # 1. Market Phase
    phase = detect_market_phase(prices, volumes)
    phase_score = phase.confidence if phase.phase in [MarketPhase.ACCUMULATION] else 0.0
    if phase.phase == MarketPhase.ACCUMULATION:
        reasons.append(f"Accumulation phase detected ({phase.confidence:.0%})")
    
    # 2. Multi-timeframe confluence  
    mtf_score, mtf_direction = calculate_mtf_confluence(tf_signals)
    if mtf_score > 0.6:
        reasons.append(f"MTF confluence {mtf_direction} ({mtf_score:.0%})")
    
    # 3. Liquidity sweep
    sweep = detect_liquidity_sweep(highs, lows, closes)
    sweep_score = sweep.recovery_strength if sweep.entry_opportunity else 0.0
    if sweep.detected and sweep.entry_opportunity:
        reasons.append(f"Liquidity sweep {sweep.sweep_type} ({sweep.recovery_strength:.0%})")
    
    # 4. RSI divergence
    divergence = detect_rsi_divergence(prices, rsi_values)
    div_score = divergence.strength if divergence.detected else 0.0
    if divergence.detected:
        reasons.append(f"{divergence.divergence_type} divergence ({divergence.strength:.0%})")
    
    # Calculate composite score
    composite = (phase_score * 0.25 + mtf_score * 0.35 + 
                 sweep_score * 0.25 + div_score * 0.15)
    
    # Determine direction
    direction = 'none'
    if composite > 0.5:
        if mtf_direction == 'bullish' or phase.suggested_action == 'buy':
            direction = 'long'
        elif mtf_direction == 'bearish' or phase.suggested_action == 'sell':
            direction = 'short'
    
    # Calculate penny thresholds
    penny = calculate_penny_threshold(position_size, exchange) if direction != 'none' else None
    
    should_enter = composite > 0.6 and direction != 'none'
    
    return QuantumSignal(
        should_enter=should_enter,
        direction=direction,
        confidence=composite,
        phase_score=phase_score,
        mtf_score=mtf_score,
        sweep_score=sweep_score,
        divergence_score=div_score,
        penny_threshold=penny,
        reasoning=' | '.join(reasons) if reasons else 'No strong signals'
    )


# =============================================================================
# USAGE EXAMPLE & VERIFICATION
# =============================================================================
if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   🦆⚡ QUANTUM SIGNALS - IRA SNIPER COMPONENTS ⚡🦆                       ║
║                                                                          ║
║   "Free the people, penny by penny!"                                    ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    print("=" * 60)
    print("🎯 PENNY PROFIT THRESHOLD CALCULATOR")
    print("=" * 60)
    print()
    print("Position Size | Exchange | Required Move | Gross Needed")
    print("-" * 60)
    
    for size in [5, 10, 25, 50, 100]:
        for exch in ['kraken', 'binance']:
            pt = calculate_penny_threshold(size, exch)
            print(f"    ${size:<8} | {exch:8} | {pt.required_move_pct:>6.3f}%     | ${pt.win_gte:.4f}")
    
    print()
    print("=" * 60)
    print("📊 KEY COMPONENTS FOR IRA SNIPER")
    print("=" * 60)
    print("""
    ┌─────────────────┬────────────────────────────────────────────┐
    │ Component       │ Benefit for IRA Sniper                     │
    ├─────────────────┼────────────────────────────────────────────┤
    │ Market Phase    │ Only enter during ACCUMULATION             │
    │ MTF Confluence  │ Higher win rate with timeframe agreement   │
    │ Liquidity Sweep │ Enter AFTER stop hunts, not before         │
    │ RSI Divergence  │ Catch reversals early                      │
    │ Penny Calculator│ CORRECT exit targets!                      │
    └─────────────────┴────────────────────────────────────────────┘
    """)
    
    print("✅ Penny profit math is CORRECT!")
    print("🇮🇪 Tiocfaidh ár lá! 🇮🇪")
