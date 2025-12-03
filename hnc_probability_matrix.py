#!/usr/bin/env python3
"""
🌍⚡ HNC PROBABILITY MATRIX - TEMPORAL FREQUENCY ANALYSIS ⚡🌍
═══════════════════════════════════════════════════════════════

2-HOUR PROBABILITY WINDOW:
├─ HOUR -1 (LOOKBACK):  Base signal source - historical frequency patterns
├─ HOUR  0 (NOW):       Current state calibration point
├─ HOUR +1 (FORECAST):  High probability trading window (PRIMARY)
└─ HOUR +2 (FINE-TUNE): Secondary window to refine Hour +1 predictions

The base signal from Hour -1 establishes the frequency foundation.
Hour +2 predictions are used ONLY to fine-tune Hour +1 high probability windows.

Gary Leckey & GitHub Copilot | November 2025
"From Prime to Probability - The Frequency Unfolds"
"""

import os
import sys
import json
import time
import math
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import deque
from enum import Enum
from lighthouse_metrics import LighthouseMetricsEngine

# ═══════════════════════════════════════════════════════════════
# CONSTANTS - PROBABILITY MATRIX PARAMETERS
# ═══════════════════════════════════════════════════════════════

# Prime sequence for temporal anchoring
PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71]

# Fibonacci for probability scaling
FIBONACCI = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987]

# Golden Ratio
PHI = (1 + math.sqrt(5)) / 2  # 1.618033988749895

# Solfeggio Frequencies for state mapping
FREQ_MAP = {
    'SCHUMANN': 7.83,      # Earth resonance
    'FOUNDATION': 174.0,   # Pain reduction
    'ROOT': 256.0,         # C4 Scientific Pitch (ANCHOR)
    'LIBERATION': 396.0,   # Release fear
    'TRANSFORMATION': 417.0,  # Facilitating change
    'NATURAL_A': 432.0,    # Natural tuning
    'DISTORTION': 440.0,   # Standard A (artificial)
    'VISION': 512.0,       # C5 Octave
    'LOVE': 528.0,         # DNA repair / Miracles
    'CONNECTION': 639.0,   # Relationships
    'AWAKENING': 741.0,    # Expression
    'INTUITION': 852.0,    # Third eye
    'UNITY': 963.0,        # Oneness
}

# Probability thresholds
PROB_THRESHOLDS = {
    'EXTREME_HIGH': 0.90,   # 90%+ probability
    'HIGH': 0.75,           # 75-90%
    'MODERATE': 0.55,       # 55-75%
    'NEUTRAL': 0.45,        # 45-55%
    'LOW': 0.25,            # 25-45%
    'EXTREME_LOW': 0.10,    # <25%
}


class ProbabilityState(Enum):
    """Probability state classification"""
    EXTREME_BULLISH = "🚀 EXTREME BULLISH"
    BULLISH = "📈 BULLISH"
    SLIGHT_BULLISH = "↗️ SLIGHT BULLISH"
    NEUTRAL = "⚖️ NEUTRAL"
    SLIGHT_BEARISH = "↘️ SLIGHT BEARISH"
    BEARISH = "📉 BEARISH"
    EXTREME_BEARISH = "💥 EXTREME BEARISH"


@dataclass
class FrequencySnapshot:
    """Single point-in-time frequency measurement"""
    timestamp: datetime
    symbol: str
    price: float
    frequency: float
    resonance: float
    is_harmonic: bool
    momentum: float  # % change
    volume: float
    coherence: float
    phase_angle: float  # 0-360 degrees
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'price': self.price,
            'frequency': self.frequency,
            'resonance': self.resonance,
            'is_harmonic': self.is_harmonic,
            'momentum': self.momentum,
            'volume': self.volume,
            'coherence': self.coherence,
            'phase_angle': self.phase_angle,
        }


@dataclass
class HourlyProbabilityWindow:
    """Probability analysis for a 1-hour window"""
    hour_offset: int  # -1, 0, +1, +2
    start_time: datetime
    end_time: datetime
    
    # Probability metrics
    bullish_probability: float = 0.5
    bearish_probability: float = 0.5
    confidence: float = 0.0
    
    # Frequency metrics
    avg_frequency: float = 256.0
    dominant_frequency: float = 256.0
    frequency_trend: str = "STABLE"  # RISING, FALLING, STABLE
    harmonic_ratio: float = 0.0
    
    # Pattern metrics
    prime_alignment: float = 0.0
    fibonacci_alignment: float = 0.0
    golden_ratio_proximity: float = 0.0
    
    # Signal strength
    signal_strength: float = 0.0
    noise_ratio: float = 0.0
    clarity: float = 0.0
    
    # State
    state: ProbabilityState = ProbabilityState.NEUTRAL
    
    def compute_state(self):
        """Determine probability state from metrics"""
        net_prob = self.bullish_probability - self.bearish_probability
        
        if net_prob > 0.4:
            self.state = ProbabilityState.EXTREME_BULLISH
        elif net_prob > 0.25:
            self.state = ProbabilityState.BULLISH
        elif net_prob > 0.10:
            self.state = ProbabilityState.SLIGHT_BULLISH
        elif net_prob > -0.10:
            self.state = ProbabilityState.NEUTRAL
        elif net_prob > -0.25:
            self.state = ProbabilityState.SLIGHT_BEARISH
        elif net_prob > -0.40:
            self.state = ProbabilityState.BEARISH
        else:
            self.state = ProbabilityState.EXTREME_BEARISH


@dataclass
class ProbabilityMatrix:
    """Complete 2-hour probability matrix with 4 windows"""
    symbol: str
    generated_at: datetime
    
    # The 4 hourly windows
    hour_minus_1: HourlyProbabilityWindow = None  # LOOKBACK (base signal)
    hour_0: HourlyProbabilityWindow = None        # NOW (calibration)
    hour_plus_1: HourlyProbabilityWindow = None   # FORECAST (primary)
    hour_plus_2: HourlyProbabilityWindow = None   # FINE-TUNE (secondary)
    
    # Combined metrics
    combined_probability: float = 0.5
    fine_tuned_probability: float = 0.5
    confidence_score: float = 0.0
    recommended_action: str = "HOLD"
    position_modifier: float = 1.0
    
    # Fine-tuning results
    fine_tune_adjustment: float = 0.0
    fine_tune_reason: str = ""


class TemporalFrequencyAnalyzer:
    """
    Analyzes frequency patterns across time windows.
    Uses Hour -1 as base signal, forecasts Hour +1, 
    and uses Hour +2 to fine-tune Hour +1 predictions.
    """
    
    def __init__(self, lookback_minutes: int = 60, sample_interval_sec: int = 60):
        self.lookback_minutes = lookback_minutes
        self.sample_interval = sample_interval_sec
        
        # Historical data storage (keyed by symbol)
        self.history: Dict[str, deque] = {}
        self.max_history = 180  # 3 hours of minute data
        
        # Probability cache
        self.probability_cache: Dict[str, ProbabilityMatrix] = {}
        self.cache_ttl = 60  # seconds
        
        # Pattern recognition
        self.pattern_memory: Dict[str, List[Dict]] = {}
        
    def add_snapshot(self, snapshot: FrequencySnapshot):
        """Add a frequency snapshot to history"""
        symbol = snapshot.symbol
        if symbol not in self.history:
            self.history[symbol] = deque(maxlen=self.max_history)
        self.history[symbol].append(snapshot)
        
    def get_hourly_data(self, symbol: str, hour_offset: int) -> List[FrequencySnapshot]:
        """Get data for a specific hour window relative to now"""
        if symbol not in self.history:
            return []
        
        now = datetime.now()
        
        if hour_offset < 0:
            # Historical data
            start = now + timedelta(hours=hour_offset)
            end = now + timedelta(hours=hour_offset + 1)
        elif hour_offset == 0:
            # Current hour
            start = now - timedelta(minutes=30)
            end = now + timedelta(minutes=30)
        else:
            # Future - use recent patterns to project
            return []  # Will be computed from patterns
        
        return [
            s for s in self.history[symbol]
            if start <= s.timestamp <= end
        ]
    
    def compute_base_signal(self, symbol: str) -> HourlyProbabilityWindow:
        """
        Compute base signal from Hour -1 (lookback).
        This establishes the frequency foundation for forecasting.
        """
        now = datetime.now()
        window = HourlyProbabilityWindow(
            hour_offset=-1,
            start_time=now - timedelta(hours=1),
            end_time=now,
        )
        
        data = self.get_hourly_data(symbol, -1)
        if not data:
            return window
        
        # Calculate frequency metrics
        frequencies = [s.frequency for s in data]
        momentums = [s.momentum for s in data]
        coherences = [s.coherence for s in data]
        harmonics = [s.is_harmonic for s in data]
        volumes = [s.volume for s in data]
        
        window.avg_frequency = np.mean(frequencies)
        window.dominant_frequency = self._find_dominant_frequency(frequencies)
        window.harmonic_ratio = sum(harmonics) / len(harmonics)
        
        # Frequency trend
        if len(frequencies) >= 2:
            freq_change = frequencies[-1] - frequencies[0]
            if freq_change > 20:
                window.frequency_trend = "RISING"
            elif freq_change < -20:
                window.frequency_trend = "FALLING"
            else:
                window.frequency_trend = "STABLE"
        
        # Momentum analysis for probability
        avg_momentum = np.mean(momentums)
        momentum_std = np.std(momentums) if len(momentums) > 1 else 0
        
        # Volume Analysis
        avg_volume = np.mean(volumes) if volumes else 0
        volume_trend = 0
        if len(volumes) >= 2 and avg_volume > 0:
            volume_trend = (volumes[-1] - volumes[0]) / avg_volume
            
        # Convert momentum to probability
        # Positive momentum = bullish, negative = bearish
        momentum_signal = np.tanh(avg_momentum / 10)  # Normalize to [-1, 1]
        
        # Volume confirmation
        volume_factor = 1.0
        if volume_trend > 0.1:  # Rising volume
            volume_factor = 1.1
        elif volume_trend < -0.1:  # Falling volume
            volume_factor = 0.9
            
        window.bullish_probability = 0.5 + (momentum_signal * 0.3 * volume_factor)
        window.bearish_probability = 1 - window.bullish_probability
        
        # Coherence affects confidence
        window.confidence = np.mean(coherences)
        
        # Signal strength from harmonic ratio
        window.signal_strength = window.harmonic_ratio * window.confidence
        
        # Noise = inverse of coherence variance stability
        window.noise_ratio = 1 - min(1, np.std(coherences) * 2) if len(coherences) > 1 else 0.5
        
        # Clarity = signal / (signal + noise)
        window.clarity = window.signal_strength / (window.signal_strength + window.noise_ratio + 0.01)
        
        # Prime alignment
        window.prime_alignment = self._compute_prime_alignment(data)
        
        # Fibonacci alignment
        window.fibonacci_alignment = self._compute_fibonacci_alignment(data)
        
        # Golden ratio proximity
        window.golden_ratio_proximity = self._compute_golden_proximity(data)
        
        window.compute_state()
        return window
    
    def compute_current_state(self, symbol: str, current_data: Dict) -> HourlyProbabilityWindow:
        """
        Compute current state (Hour 0) as calibration point.
        """
        now = datetime.now()
        window = HourlyProbabilityWindow(
            hour_offset=0,
            start_time=now - timedelta(minutes=30),
            end_time=now + timedelta(minutes=30),
        )
        
        # Use current data directly
        window.avg_frequency = current_data.get('frequency', 256)
        window.dominant_frequency = current_data.get('frequency', 256)
        window.harmonic_ratio = 1.0 if current_data.get('is_harmonic', False) else 0.0
        
        momentum = current_data.get('momentum', 0)
        volume = current_data.get('volume', 0)
        momentum_signal = np.tanh(momentum / 10)
        
        # Volume impact on current state
        # High volume increases confidence in the move
        volume_confidence = 1.0
        if volume > 0:
            # Assuming volume is normalized or we just check for non-zero
            volume_confidence = 1.05
            
        window.bullish_probability = 0.5 + (momentum_signal * 0.35 * volume_confidence)
        window.bearish_probability = 1 - window.bullish_probability
        
        window.confidence = current_data.get('coherence', 0.5)
        window.signal_strength = current_data.get('resonance', 0.5)
        
        window.compute_state()
        return window
    
    def forecast_hour_plus_1(self, symbol: str, base_signal: HourlyProbabilityWindow, 
                              current: HourlyProbabilityWindow) -> HourlyProbabilityWindow:
        """
        Forecast Hour +1 (PRIMARY trading window).
        Uses base signal from Hour -1 and current state for calibration.
        """
        now = datetime.now()
        window = HourlyProbabilityWindow(
            hour_offset=1,
            start_time=now,
            end_time=now + timedelta(hours=1),
        )
        
        # Project frequency based on trend
        if base_signal.frequency_trend == "RISING":
            freq_delta = (current.avg_frequency - base_signal.avg_frequency)
            window.avg_frequency = current.avg_frequency + (freq_delta * 0.5)
        elif base_signal.frequency_trend == "FALLING":
            freq_delta = (base_signal.avg_frequency - current.avg_frequency)
            window.avg_frequency = current.avg_frequency - (freq_delta * 0.5)
        else:
            window.avg_frequency = current.avg_frequency
        
        window.dominant_frequency = window.avg_frequency
        window.frequency_trend = base_signal.frequency_trend
        
        # Probability projection with momentum continuation
        # Weight: 40% base signal, 60% current state
        base_weight = 0.4
        current_weight = 0.6
        
        projected_bullish = (
            base_signal.bullish_probability * base_weight +
            current.bullish_probability * current_weight
        )
        
        # Volume confirmation for forecast
        # If base signal had rising volume, increase confidence in trend
        if base_signal.bullish_probability > 0.55 and base_signal.signal_strength > 0.6:
             projected_bullish *= 1.05
        
        # Apply harmonic boost/penalty
        if current.harmonic_ratio > 0.5:
            projected_bullish *= 1.1  # 10% boost for harmonic state
        elif window.avg_frequency >= 435 and window.avg_frequency <= 445:
            projected_bullish *= 0.9  # 10% penalty for distortion
        
        # Clamp probability
        window.bullish_probability = max(0.1, min(0.9, projected_bullish))
        window.bearish_probability = 1 - window.bullish_probability
        
        # Confidence from alignment metrics
        window.confidence = (
            base_signal.confidence * 0.3 +
            current.confidence * 0.5 +
            base_signal.prime_alignment * 0.1 +
            base_signal.fibonacci_alignment * 0.1
        )
        
        # Harmonic ratio projection
        window.harmonic_ratio = (base_signal.harmonic_ratio + current.harmonic_ratio) / 2
        
        # Inherit pattern alignments
        window.prime_alignment = base_signal.prime_alignment
        window.fibonacci_alignment = base_signal.fibonacci_alignment
        window.golden_ratio_proximity = base_signal.golden_ratio_proximity
        
        # Signal clarity
        window.signal_strength = window.harmonic_ratio * window.confidence
        window.clarity = window.signal_strength * base_signal.clarity
        
        window.compute_state()
        return window
    
    def forecast_hour_plus_2(self, symbol: str, base_signal: HourlyProbabilityWindow,
                              current: HourlyProbabilityWindow,
                              hour_1: HourlyProbabilityWindow) -> HourlyProbabilityWindow:
        """
        Forecast Hour +2 (FINE-TUNING window).
        Used ONLY to refine Hour +1 predictions, not for direct trading.
        """
        now = datetime.now()
        window = HourlyProbabilityWindow(
            hour_offset=2,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
        )
        
        # Extended projection with decay
        decay = 0.7  # Confidence decays further out
        
        # Frequency with momentum decay
        if hour_1.frequency_trend == "RISING":
            window.avg_frequency = hour_1.avg_frequency * 1.02 * decay + 256 * (1 - decay)
        elif hour_1.frequency_trend == "FALLING":
            window.avg_frequency = hour_1.avg_frequency * 0.98 * decay + 256 * (1 - decay)
        else:
            window.avg_frequency = hour_1.avg_frequency * decay + 256 * (1 - decay)
        
        window.dominant_frequency = window.avg_frequency
        window.frequency_trend = hour_1.frequency_trend
        
        # Probability with reversion to mean
        mean_reversion = 0.3
        projected_bullish = hour_1.bullish_probability * (1 - mean_reversion) + 0.5 * mean_reversion
        
        window.bullish_probability = projected_bullish
        window.bearish_probability = 1 - window.bullish_probability
        
        # Lower confidence for extended forecast
        window.confidence = hour_1.confidence * decay
        window.harmonic_ratio = hour_1.harmonic_ratio * decay
        
        # Pattern alignment decay
        window.prime_alignment = hour_1.prime_alignment * decay
        window.fibonacci_alignment = hour_1.fibonacci_alignment * decay
        window.golden_ratio_proximity = hour_1.golden_ratio_proximity * decay
        
        window.signal_strength = hour_1.signal_strength * decay
        window.clarity = hour_1.clarity * decay
        
        window.compute_state()
        return window
    
    def fine_tune_forecast(self, hour_1: HourlyProbabilityWindow, 
                           hour_2: HourlyProbabilityWindow) -> Tuple[float, float, str]:
        """
        Use Hour +2 forecast to fine-tune Hour +1 predictions.
        Returns: (adjustment, fine_tuned_probability, reason)
        """
        adjustment = 0.0
        reasons = []
        
        # Check for trend continuation vs reversal
        h1_bullish = hour_1.bullish_probability > 0.5
        h2_bullish = hour_2.bullish_probability > 0.5
        
        if h1_bullish and h2_bullish:
            # Trend continuation - boost confidence
            if hour_2.bullish_probability > hour_1.bullish_probability:
                adjustment = 0.05  # Strengthen bullish signal
                reasons.append("H+2 confirms bullish continuation")
            else:
                adjustment = -0.02  # Slight caution - momentum fading
                reasons.append("H+2 shows momentum decay")
                
        elif h1_bullish and not h2_bullish:
            # Potential reversal ahead - reduce position
            adjustment = -0.10
            reasons.append("H+2 signals potential reversal")
            
        elif not h1_bullish and not h2_bullish:
            # Bearish continuation
            if hour_2.bearish_probability > hour_1.bearish_probability:
                adjustment = -0.05  # Strengthen bearish signal
                reasons.append("H+2 confirms bearish continuation")
            else:
                adjustment = 0.02  # Slight recovery
                reasons.append("H+2 shows bearish momentum decay")
                
        elif not h1_bullish and h2_bullish:
            # Potential bullish reversal - opportunity
            adjustment = 0.08
            reasons.append("H+2 signals potential bullish reversal")
        
        # Frequency alignment check
        if abs(hour_2.avg_frequency - 528) < 30:  # Near LOVE frequency
            adjustment += 0.03
            reasons.append("H+2 approaching 528Hz LOVE resonance")
        elif abs(hour_2.avg_frequency - 440) < 10:  # Near DISTORTION
            adjustment -= 0.05
            reasons.append("H+2 approaching 440Hz distortion")
        
        # Apply harmonic ratio influence
        if hour_2.harmonic_ratio > hour_1.harmonic_ratio:
            adjustment += 0.02
            reasons.append("H+2 harmonic ratio improving")
        elif hour_2.harmonic_ratio < hour_1.harmonic_ratio * 0.8:
            adjustment -= 0.03
            reasons.append("H+2 harmonic ratio degrading")
        
        # Calculate fine-tuned probability
        fine_tuned = hour_1.bullish_probability + adjustment
        fine_tuned = max(0.1, min(0.9, fine_tuned))
        
        reason = " | ".join(reasons) if reasons else "No significant H+2 adjustment"
        
        return adjustment, fine_tuned, reason
    
    def generate_probability_matrix(self, symbol: str, current_data: Dict) -> ProbabilityMatrix:
        """
        Generate complete 2-hour probability matrix for a symbol.
        """
        now = datetime.now()
        matrix = ProbabilityMatrix(
            symbol=symbol,
            generated_at=now,
        )
        
        # Step 1: Compute base signal from Hour -1
        matrix.hour_minus_1 = self.compute_base_signal(symbol)
        
        # Step 2: Compute current state (Hour 0)
        matrix.hour_0 = self.compute_current_state(symbol, current_data)
        
        # Step 3: Forecast Hour +1 (PRIMARY)
        matrix.hour_plus_1 = self.forecast_hour_plus_1(
            symbol, matrix.hour_minus_1, matrix.hour_0
        )
        
        # Step 4: Forecast Hour +2 (FINE-TUNING)
        matrix.hour_plus_2 = self.forecast_hour_plus_2(
            symbol, matrix.hour_minus_1, matrix.hour_0, matrix.hour_plus_1
        )
        
        # Step 5: Fine-tune Hour +1 using Hour +2
        adjustment, fine_tuned, reason = self.fine_tune_forecast(
            matrix.hour_plus_1, matrix.hour_plus_2
        )
        
        matrix.fine_tune_adjustment = adjustment
        matrix.fine_tuned_probability = fine_tuned
        matrix.fine_tune_reason = reason
        
        # Combined probability (weighted average)
        matrix.combined_probability = (
            matrix.hour_minus_1.bullish_probability * 0.2 +
            matrix.hour_0.bullish_probability * 0.3 +
            matrix.hour_plus_1.bullish_probability * 0.5
        )
        
        # Confidence score
        matrix.confidence_score = (
            matrix.hour_minus_1.confidence * 0.3 +
            matrix.hour_0.confidence * 0.4 +
            matrix.hour_plus_1.confidence * 0.3
        )
        
        # Determine action
        if matrix.fine_tuned_probability >= 0.70:
            matrix.recommended_action = "STRONG BUY"
            matrix.position_modifier = 1.2
        elif matrix.fine_tuned_probability >= 0.60:
            matrix.recommended_action = "BUY"
            matrix.position_modifier = 1.0
        elif matrix.fine_tuned_probability >= 0.55:
            matrix.recommended_action = "SLIGHT BUY"
            matrix.position_modifier = 0.8
        elif matrix.fine_tuned_probability >= 0.45:
            matrix.recommended_action = "HOLD"
            matrix.position_modifier = 0.5
        elif matrix.fine_tuned_probability >= 0.40:
            matrix.recommended_action = "SLIGHT SELL"
            matrix.position_modifier = 0.3
        elif matrix.fine_tuned_probability >= 0.30:
            matrix.recommended_action = "SELL"
            matrix.position_modifier = 0.2
        else:
            matrix.recommended_action = "STRONG SELL"
            matrix.position_modifier = 0.1
        
        # Cache result
        self.probability_cache[symbol] = matrix
        
        return matrix
    
    def _find_dominant_frequency(self, frequencies: List[float]) -> float:
        """Find the most common frequency band"""
        if not frequencies:
            return 256.0
        
        # Bucket into frequency bands
        bands = {}
        for f in frequencies:
            band = round(f / 50) * 50  # 50Hz bands
            bands[band] = bands.get(band, 0) + 1
        
        dominant = max(bands.items(), key=lambda x: x[1])
        return dominant[0]
    
    def _compute_prime_alignment(self, data: List[FrequencySnapshot]) -> float:
        """Compute alignment with prime number patterns"""
        if not data:
            return 0.0
        
        alignments = []
        for i, s in enumerate(data):
            # Check if index or frequency aligns with primes
            idx_prime = any(i % p == 0 for p in PRIMES[:8])
            freq_prime = any(abs(s.frequency - p * 10) < 5 for p in PRIMES[:10])
            
            alignments.append(1.0 if (idx_prime or freq_prime) else 0.0)
        
        return np.mean(alignments)
    
    def _compute_fibonacci_alignment(self, data: List[FrequencySnapshot]) -> float:
        """Compute alignment with Fibonacci patterns"""
        if len(data) < 3:
            return 0.0
        
        alignments = []
        prices = [s.price for s in data]
        
        for i in range(2, len(prices)):
            # Check Fibonacci ratio between consecutive moves
            move1 = abs(prices[i-1] - prices[i-2])
            move2 = abs(prices[i] - prices[i-1])
            
            if move1 > 0:
                ratio = move2 / move1
                # Check proximity to Fibonacci ratios
                fib_ratios = [0.382, 0.5, 0.618, 1.0, 1.618, 2.618]
                min_diff = min(abs(ratio - fr) for fr in fib_ratios)
                alignments.append(1.0 - min(1.0, min_diff * 2))
        
        return np.mean(alignments) if alignments else 0.0
    
    def _compute_golden_proximity(self, data: List[FrequencySnapshot]) -> float:
        """Compute proximity to golden ratio in price movements"""
        if len(data) < 2:
            return 0.0
        
        prices = [s.price for s in data]
        total_move = prices[-1] - prices[0]
        
        if abs(total_move) < 0.001:
            return 0.5
        
        # Find retracement levels
        retracements = []
        for p in prices[1:-1]:
            if total_move != 0:
                ret = (p - prices[0]) / total_move
                retracements.append(ret)
        
        if not retracements:
            return 0.5
        
        # Check proximity to golden ratio levels
        golden_levels = [0.236, 0.382, 0.5, 0.618, 0.786]
        proximities = []
        
        for ret in retracements:
            min_dist = min(abs(ret - gl) for gl in golden_levels)
            proximities.append(1.0 - min(1.0, min_dist * 3))
        
        return np.mean(proximities)
    
    def print_probability_matrix(self, matrix: ProbabilityMatrix):
        """Print formatted probability matrix"""
        print(f"""
╔══════════════════════════════════════════════════════════════════════════╗
║  🌍⚡ HNC PROBABILITY MATRIX: {matrix.symbol:12s}                       ║
║  Generated: {matrix.generated_at.strftime('%Y-%m-%d %H:%M:%S')}                                    ║
╠══════════════════════════════════════════════════════════════════════════╣
║  TEMPORAL WINDOW          │ PROBABILITY │  FREQ  │ CONFIDENCE │ STATE   ║
╠═══════════════════════════╪═════════════╪════════╪════════════╪═════════╣""")
        
        for name, window in [
            ("⏪ HOUR -1 (BASE SIGNAL)", matrix.hour_minus_1),
            ("⏺️  HOUR  0 (CURRENT)   ", matrix.hour_0),
            ("⏩ HOUR +1 (FORECAST)  ", matrix.hour_plus_1),
            ("⏭️  HOUR +2 (FINE-TUNE) ", matrix.hour_plus_2),
        ]:
            bull = window.bullish_probability
            freq = window.avg_frequency
            conf = window.confidence
            state = window.state.value[:10]
            
            # Probability bar
            bar_len = int(bull * 10)
            bar = "█" * bar_len + "░" * (10 - bar_len)
            
            print(f"║  {name} │ {bar} {bull:.0%} │ {freq:6.0f} │    {conf:.0%}     │ {state} ║")
        
        print(f"""╠══════════════════════════════════════════════════════════════════════════╣
║  FINE-TUNING RESULTS                                                     ║
╠══════════════════════════════════════════════════════════════════════════╣
║  Adjustment: {matrix.fine_tune_adjustment:+.2%}                                                  ║
║  Final Probability: {matrix.fine_tuned_probability:.1%}                                           ║
║  Reason: {matrix.fine_tune_reason[:60]:60s} ║
╠══════════════════════════════════════════════════════════════════════════╣
║  📊 COMBINED PROBABILITY: {matrix.combined_probability:.1%}                                       ║
║  🎯 CONFIDENCE SCORE:     {matrix.confidence_score:.1%}                                       ║
║  💡 RECOMMENDED ACTION:   {matrix.recommended_action:15s}                           ║
║  📐 POSITION MODIFIER:    ×{matrix.position_modifier:.2f}                                        ║
╚══════════════════════════════════════════════════════════════════════════╝
""")


class HNCProbabilityIntegration:
    """
    Integrates Probability Matrix with HNC trading system.
    Provides position sizing and entry/exit signals based on temporal analysis.
    """
    
    def __init__(self):
        self.analyzer = TemporalFrequencyAnalyzer()
        self.matrices: Dict[str, ProbabilityMatrix] = {}
        self.lighthouse = LighthouseMetricsEngine()
        self._last_log_ts: Optional[datetime] = None
        self._log_cache: List[Dict[str, Any]] = []

    def _load_frequency_log(self, path: str = "hnc_frequency_log.json") -> List[Dict[str, Any]]:
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r") as f:
                data = json.load(f)
            if isinstance(data, list):
                self._log_cache = data
                try:
                    self._last_log_ts = max(
                        datetime.fromisoformat(entry.get("timestamp"))
                        for entry in data if entry.get("timestamp")
                    )
                except Exception:
                    pass
                return data
        except Exception:
            return []
        return []

    def _compute_lighthouse_adjustment(self, symbol: str) -> Tuple[float, str]:
        logs = self._log_cache or self._load_frequency_log()
        if not logs:
            return 0.0, "No lighthouse log data"

        timestamps: List[float] = []
        values: List[float] = []
        for entry in logs[-50:]:
            ts = entry.get("timestamp")
            readings = entry.get("readings", [])
            if not ts or not readings:
                continue
            for r in readings:
                if r.get("symbol") == symbol:
                    try:
                        dt = datetime.fromisoformat(ts)
                        timestamps.append(dt.timestamp())
                        values.append(float(r.get("price", 0)))
                    except Exception:
                        pass
                    break

        if len(values) < 8:
            return 0.0, "Insufficient lighthouse samples"

        try:
            metrics = self.lighthouse.analyze_series(timestamps, values)
        except Exception as e:
            return 0.0, f"Lighthouse analysis error: {e}"

        coherence = float(metrics.get("coherence_score", 0.0))
        distortion = float(metrics.get("distortion_index", 0.0))
        gamma = float(metrics.get("gamma_ratio", 0.0))
        maker_bias = float(metrics.get("maker_bias", 0.5))

        adj = 0.0
        reason_bits = []

        if coherence > 0.35:
            boost = min(0.05, (coherence - 0.35) * 0.2)
            adj += boost
            reason_bits.append(f"coherence +{boost:.2%}")
        if distortion > 0.40:
            cut = min(0.08, (distortion - 0.40) * 0.3)
            adj -= cut
            reason_bits.append(f"distortion -{cut:.2%}")
        if gamma > 0.25:
            cut = min(0.03, (gamma - 0.25) * 0.1)
            adj -= cut
            reason_bits.append(f"gamma -{cut:.2%}")

        bias_adj = (maker_bias - 0.5) * 0.06
        if abs(bias_adj) > 0.002:
            adj += bias_adj
            reason_bits.append(f"maker_bias {bias_adj:+.2%}")

        adj = max(-0.10, min(0.10, adj))
        reason = ", ".join(reason_bits) if reason_bits else "neutral lighthouse state"
        return adj, reason
        
    def update_and_analyze(self, symbol: str, price: float, frequency: float,
                           momentum: float, coherence: float, 
                           is_harmonic: bool, volume: float = 0.0) -> ProbabilityMatrix:
        """Update data and generate probability matrix"""
        
        # Create snapshot
        snapshot = FrequencySnapshot(
            timestamp=datetime.now(),
            symbol=symbol,
            price=price,
            frequency=frequency,
            resonance=1.0 if is_harmonic else 0.6,
            is_harmonic=is_harmonic,
            momentum=momentum,
            volume=volume,
            coherence=coherence,
            phase_angle=0,
        )
        
        # Add to history
        self.analyzer.add_snapshot(snapshot)
        
        # Generate matrix
        current_data = {
            'frequency': frequency,
            'momentum': momentum,
            'coherence': coherence,
            'is_harmonic': is_harmonic,
            'resonance': snapshot.resonance,
            'volume': volume,
        }
        
        matrix = self.analyzer.generate_probability_matrix(symbol, current_data)
        # Lighthouse refinement on Hour +1 using recent logs
        lh_adj, lh_reason = self._compute_lighthouse_adjustment(symbol)
        if lh_adj != 0.0:
            pre = matrix.hour_plus_1.bullish_probability
            matrix.hour_plus_1.bullish_probability = max(0.1, min(0.9, pre + lh_adj))
            matrix.hour_plus_1.bearish_probability = 1 - matrix.hour_plus_1.bullish_probability
            matrix.hour_plus_1.compute_state()

            # Recompute Hour +2 and fine-tuning
            matrix.hour_plus_2 = self.analyzer.forecast_hour_plus_2(
                symbol, matrix.hour_minus_1, matrix.hour_0, matrix.hour_plus_1
            )
            adjustment, fine_tuned, reason = self.analyzer.fine_tune_forecast(
                matrix.hour_plus_1, matrix.hour_plus_2
            )
            matrix.fine_tune_adjustment = adjustment
            matrix.fine_tuned_probability = fine_tuned
            matrix.fine_tune_reason = f"{reason} | Lighthouse: {lh_reason} ({lh_adj:+.2%})"

        self.matrices[symbol] = matrix
        
        return matrix
    
    def get_trading_signal(self, symbol: str) -> Dict[str, Any]:
        """Get trading signal based on probability matrix"""
        if symbol not in self.matrices:
            return {
                'action': 'HOLD',
                'probability': 0.5,
                'confidence': 0.0,
                'modifier': 1.0,
                'reason': 'No probability matrix available'
            }
        
        matrix = self.matrices[symbol]
        
        return {
            'action': matrix.recommended_action,
            'probability': matrix.fine_tuned_probability,
            'confidence': matrix.confidence_score,
            'modifier': matrix.position_modifier,
            'reason': matrix.fine_tune_reason,
            'h1_state': matrix.hour_plus_1.state.value,
            'h2_influence': matrix.fine_tune_adjustment,
        }
    
    def get_high_probability_opportunities(self, 
                                            min_probability: float = 0.65,
                                            min_confidence: float = 0.50) -> List[Dict]:
        """Get symbols with high probability windows"""
        opportunities = []
        
        for symbol, matrix in self.matrices.items():
            if (matrix.fine_tuned_probability >= min_probability and
                matrix.confidence_score >= min_confidence):
                opportunities.append({
                    'symbol': symbol,
                    'probability': matrix.fine_tuned_probability,
                    'confidence': matrix.confidence_score,
                    'action': matrix.recommended_action,
                    'modifier': matrix.position_modifier,
                    'h1_state': matrix.hour_plus_1.state.value,
                    'frequency': matrix.hour_plus_1.avg_frequency,
                })
        
        # Sort by probability
        opportunities.sort(key=lambda x: x['probability'], reverse=True)
        return opportunities


# ═══════════════════════════════════════════════════════════════
# DEMO / TEST
# ═══════════════════════════════════════════════════════════════

def demo_probability_matrix():
    """Demonstrate the probability matrix system"""
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║  🌍⚡ HNC PROBABILITY MATRIX DEMONSTRATION ⚡🌍                          ║
║  2-Hour Temporal Window Analysis                                         ║
╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    integration = HNCProbabilityIntegration()
    
    # Simulate data for a few symbols
    test_data = [
        {'symbol': 'BTCGBP', 'price': 69000, 'freq': 528, 'momentum': 3.5, 'coherence': 0.85, 'harmonic': True},
        {'symbol': 'ETHGBP', 'price': 2300, 'freq': 512, 'momentum': 2.1, 'coherence': 0.78, 'harmonic': True},
        {'symbol': 'SOLGBP', 'price': 105, 'freq': 440, 'momentum': -1.2, 'coherence': 0.45, 'harmonic': False},
        {'symbol': 'ADAGBP', 'price': 0.52, 'freq': 396, 'momentum': 5.8, 'coherence': 0.92, 'harmonic': True},
    ]
    
    # Simulate historical data (add multiple snapshots)
    print("📊 Building historical data...")
    for _ in range(30):  # 30 minutes of history
        for data in test_data:
            # Add some variation
            price_var = data['price'] * (1 + np.random.uniform(-0.01, 0.01))
            freq_var = data['freq'] + np.random.uniform(-20, 20)
            mom_var = data['momentum'] + np.random.uniform(-1, 1)
            coh_var = min(1.0, max(0.1, data['coherence'] + np.random.uniform(-0.1, 0.1)))
            
            snapshot = FrequencySnapshot(
                timestamp=datetime.now() - timedelta(minutes=30-_),
                symbol=data['symbol'],
                price=price_var,
                frequency=freq_var,
                resonance=1.0 if data['harmonic'] else 0.6,
                is_harmonic=data['harmonic'],
                momentum=mom_var,
                volume=1000000,
                coherence=coh_var,
                phase_angle=0,
            )
            integration.analyzer.add_snapshot(snapshot)
    
    print("✅ Historical data built\n")
    
    # Generate probability matrices
    print("🔮 Generating Probability Matrices...\n")
    
    for data in test_data:
        matrix = integration.update_and_analyze(
            symbol=data['symbol'],
            price=data['price'],
            frequency=data['freq'],
            momentum=data['momentum'],
            coherence=data['coherence'],
            is_harmonic=data['harmonic'],
        )
        integration.analyzer.print_probability_matrix(matrix)
        time.sleep(0.5)
    
    # Show high probability opportunities
    print("\n🎯 HIGH PROBABILITY OPPORTUNITIES:")
    print("=" * 70)
    
    opportunities = integration.get_high_probability_opportunities(
        min_probability=0.55,
        min_confidence=0.40
    )
    
    if opportunities:
        for opp in opportunities:
            print(f"   {opp['symbol']:12s} | Prob: {opp['probability']:.0%} | "
                  f"Conf: {opp['confidence']:.0%} | {opp['action']:12s} | "
                  f"×{opp['modifier']:.2f} | {opp['frequency']:.0f}Hz")
    else:
        print("   No high probability opportunities found")
    
    print("\n✨ Probability Matrix Demo Complete!")


if __name__ == "__main__":
    demo_probability_matrix()
