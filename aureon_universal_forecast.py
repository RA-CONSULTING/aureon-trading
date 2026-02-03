#!/usr/bin/env python3
"""
🌌🎯 AUREON UNIVERSAL FORECAST SYSTEM 🎯🌌
==========================================

COMPLETE MULTI-PLATFORM PREDICTION ENGINE
Uses ALL systems across ALL trading platforms:

PREDICTION SYSTEMS:
├─ 🌍 Earth Resonance Engine (Schumann coherence, PHI multiplier)
├─ ⚡ HNC Imperial Predictability (Cosmic state, planetary torque)
├─ 📊 HNC Probability Matrix (2-hour temporal windows)
├─ 🎵 Auris Nodes (Multi-node consensus)
└─ 🌙 Lunar/Planetary Calendar (Torque timing)

TRADING PLATFORMS:
├─ 💰 Binance (Crypto - UK USDC pairs)
├─ 🦑 Kraken (Crypto - GBP/EUR pairs)
├─ 🦙 Alpaca (US Stocks & Crypto)
└─ 💷 Capital.com (CFDs - Indices/Forex/Commodities)

Gary Leckey & GitHub Copilot | December 2025
"All Systems. All Platforms. One Forecast."
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
import time
import math
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import deque
from enum import Enum
import json

# Force LIVE mode for real trading
os.environ['LIVE'] = '1'
os.environ['DRY_RUN'] = '0'

# Import all prediction systems
from earth_resonance_engine import EarthResonanceEngine, get_earth_engine
from hnc_imperial_predictability import CosmicStateEngine, PredictabilityEngine, CosmicPhase, CosmicState
from hnc_probability_matrix import TemporalFrequencyAnalyzer, ProbabilityMatrix, ProbabilityState

# Import all exchange clients
from binance_client import BinanceClient
from kraken_client import KrakenClient, get_kraken_client
from alpaca_client import AlpacaClient
from capital_client import CapitalClient
from unified_exchange_client import MultiExchangeClient

# ═══════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

PHI = (1 + math.sqrt(5)) / 2  # Golden Ratio = 1.618033988749895

# Solfeggio Frequencies
FREQ_MAP = {
    'SCHUMANN': 7.83,
    'ROOT': 256.0,
    'LIBERATION': 396.0,
    'TRANSFORMATION': 417.0,
    'NATURAL': 432.0,
    'DISTORTION': 440.0,
    'LOVE': 528.0,
    'CONNECTION': 639.0,
    'AWAKENING': 741.0,
    'INTUITION': 852.0,
    'UNITY': 963.0,
}

# Platform Fee Structures
PLATFORM_FEES = {
    'binance': {'maker': 0.001, 'taker': 0.001},    # 0.1%
    'kraken': {'maker': 0.0016, 'taker': 0.0026},   # 0.16%/0.26%
    'alpaca': {'maker': 0.0, 'taker': 0.0015},      # 0%/0.15% crypto
    'capital': {'spread': 0.0008},                   # ~0.08% spread
}

# Minimum profit thresholds (above fees)
MIN_PROFIT_PCT = 0.0005  # 0.05%


class Platform(Enum):
    """Trading platforms"""
    BINANCE = "binance"
    KRAKEN = "kraken"
    ALPACA = "alpaca"
    CAPITAL = "capital"


class AssetClass(Enum):
    """Asset classes"""
    CRYPTO = "crypto"
    STOCK = "stock"
    FOREX = "forex"
    INDEX = "index"
    COMMODITY = "commodity"


@dataclass
class PriceSnapshot:
    """Single price observation"""
    timestamp: float
    price: float
    bid: float = 0.0
    ask: float = 0.0
    volume: float = 0.0
    momentum: float = 0.0  # % change


@dataclass
class CosmicGateStatus:
    """Complete cosmic gate status"""
    # Earth Resonance
    earth_open: bool = False
    earth_coherence: float = 0.0
    earth_phase_lock: float = 0.0
    earth_phi_boost: float = 1.0
    earth_reason: str = ""
    
    # Cosmic State
    cosmic_open: bool = False
    cosmic_phase: str = "UNKNOWN"
    cosmic_coherence: float = 0.0
    cosmic_distortion: float = 0.0
    cosmic_boost: float = 1.0
    cosmic_joy: float = 0.0
    cosmic_reciprocity: float = 0.0
    
    # Planetary
    planetary_torque: float = 1.0
    lunar_phase: float = 0.0
    
    # Combined
    all_gates_open: bool = False
    combined_multiplier: float = 1.0


@dataclass
class ProbabilityForecast:
    """60-second probability forecast"""
    symbol: str
    platform: str
    asset_class: str
    
    # Current state
    current_price: float = 0.0
    bid: float = 0.0
    ask: float = 0.0
    spread_pct: float = 0.0
    
    # Forecast
    forecast_price: float = 0.0
    price_change_pct: float = 0.0
    
    # Probability
    bullish_probability: float = 0.5
    bearish_probability: float = 0.5
    confidence: float = 0.0
    
    # Frequency analysis
    frequency: float = 432.0
    is_harmonic: bool = False
    frequency_state: str = "NEUTRAL"
    
    # Pattern alignment
    prime_alignment: float = 0.0
    fibonacci_alignment: float = 0.0
    golden_ratio_proximity: float = 0.0
    
    # Decision
    recommended_action: str = "HOLD"
    position_multiplier: float = 1.0
    expected_profit_pct: float = 0.0
    
    # Timing
    forecast_window_sec: int = 60
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class UniversalForecast:
    """Complete forecast using all systems for one opportunity"""
    # Identity
    symbol: str
    platform: Platform
    asset_class: AssetClass
    
    # Cosmic Gates
    cosmic_gates: CosmicGateStatus = None
    
    # Probability Forecast
    probability: ProbabilityForecast = None
    
    # Final Decision
    should_trade: bool = False
    reason: str = ""
    action: str = "HOLD"  # BUY, SELL, HOLD
    
    # Position Sizing
    position_usd: float = 0.0
    quantity: float = 0.0
    
    # Risk Management
    stop_loss_pct: float = 0.02  # 2%
    take_profit_pct: float = 0.01  # 1%
    risk_reward_ratio: float = 0.5
    
    # Timing
    entry_window_sec: int = 60
    generated_at: datetime = field(default_factory=datetime.now)


# ═══════════════════════════════════════════════════════════════════════════
# UNIVERSAL FORECAST ENGINE
# ═══════════════════════════════════════════════════════════════════════════

class UniversalForecastEngine:
    """
    Master forecasting engine that integrates ALL prediction systems
    across ALL trading platforms.
    """
    
    def __init__(self):
        print("\n🌌 Initializing Universal Forecast Engine...")
        
        # Initialize prediction systems
        self.earth_engine = EarthResonanceEngine()
        self.earth_engine.COHERENCE_THRESHOLD = 0.45  # Lowered for current cycle
        self.cosmic_engine = CosmicStateEngine()
        self.predictability_engine = PredictabilityEngine()
        self.temporal_analyzer = TemporalFrequencyAnalyzer()
        
        print("   ✅ Earth Resonance Engine")
        print("   ✅ Cosmic State Engine")
        print("   ✅ Imperial Predictability Engine")
        print("   ✅ Temporal Frequency Analyzer")
        
        # Initialize exchange clients
        self.clients = {}
        self._init_exchanges()
        
        # Price history for each symbol
        self.price_history: Dict[str, deque] = {}
        self.max_history = 180  # 3 minutes at 1/sec
        
        # Forecast cache
        self.forecast_cache: Dict[str, UniversalForecast] = {}
        self.cache_ttl = 30  # seconds
        
        print("\n🌌 Universal Forecast Engine Ready!")
    
    def _init_exchanges(self):
        """Initialize all exchange clients"""
        # Binance
        try:
            self.clients['binance'] = BinanceClient()
            print("   ✅ Binance Client")
        except Exception as e:
            print(f"   ⚠️ Binance: {e}")
            self.clients['binance'] = None
        
        # Kraken
        try:
            self.clients['kraken'] = get_kraken_client()
            print("   ✅ Kraken Client")
        except Exception as e:
            print(f"   ⚠️ Kraken: {e}")
            self.clients['kraken'] = None
        
        # Alpaca
        try:
            self.clients['alpaca'] = AlpacaClient()
            print("   ✅ Alpaca Client")
        except Exception as e:
            print(f"   ⚠️ Alpaca: {e}")
            self.clients['alpaca'] = None
        
        # Capital.com
        try:
            self.clients['capital'] = CapitalClient()
            if self.clients['capital'].enabled:
                print("   ✅ Capital.com Client")
            else:
                print("   ⚠️ Capital.com: Disabled (no credentials)")
                self.clients['capital'] = None
        except Exception as e:
            print(f"   ⚠️ Capital.com: {e}")
            self.clients['capital'] = None
    
    # ═══════════════════════════════════════════════════════════════════════
    # LAYER 1: COSMIC GATE CHECKS
    # ═══════════════════════════════════════════════════════════════════════
    
    def check_cosmic_gates(self) -> CosmicGateStatus:
        """
        Check ALL cosmic gates before any trading decision.
        Returns complete gate status with all metrics.
        """
        status = CosmicGateStatus()
        
        # ─────────────────────────────────────────────────────────────────
        # 1A. EARTH RESONANCE ENGINE
        # ─────────────────────────────────────────────────────────────────
        self.earth_engine.update_schumann_state(market_volatility=0.0)
        gate_dict = self.earth_engine.get_trading_gate_status_dict()
        
        status.earth_coherence = gate_dict['coherence']
        status.earth_phase_lock = 0.7 if gate_dict['phase_locked'] else 0.4
        status.earth_phi_boost = self.earth_engine.get_phi_position_multiplier()
        status.earth_open = gate_dict['gate_open']
        status.earth_reason = gate_dict['reason']
        
        # ─────────────────────────────────────────────────────────────────
        # 1B. COSMIC STATE ENGINE (Imperial Predictability)
        # ─────────────────────────────────────────────────────────────────
        cosmic_state = self.cosmic_engine.compute_state()
        
        status.cosmic_phase = cosmic_state.phase.name
        status.cosmic_coherence = cosmic_state.coherence
        status.cosmic_distortion = cosmic_state.distortion
        status.cosmic_joy = cosmic_state.joy
        status.cosmic_reciprocity = cosmic_state.reciprocity
        status.lunar_phase = cosmic_state.lunar_phase
        
        # Cosmic gate logic (with early-day override)
        if cosmic_state.phase == CosmicPhase.DISTORTION:
            # Allow trading if distortion is actually low
            if cosmic_state.distortion < 0.02 and cosmic_state.coherence > 0.30:
                status.cosmic_open = True
                status.cosmic_phase = "TRANSITION"  # Upgrade
            else:
                status.cosmic_open = False
        else:
            status.cosmic_open = True
        
        # Cosmic boost based on phase
        boost_map = {
            'UNITY': 1.5,
            'COHERENCE': 1.3,
            'HARMONIC': 1.1,
            'TRANSITION': 0.9,
            'DISTORTION': 0.5,
        }
        status.cosmic_boost = boost_map.get(status.cosmic_phase, 1.0)
        
        # ─────────────────────────────────────────────────────────────────
        # 1C. PLANETARY TORQUE
        # ─────────────────────────────────────────────────────────────────
        status.planetary_torque = self.cosmic_engine.compute_planetary_torque(datetime.now())
        
        # ─────────────────────────────────────────────────────────────────
        # COMBINED STATUS
        # ─────────────────────────────────────────────────────────────────
        status.all_gates_open = status.earth_open and status.cosmic_open
        
        # Combined multiplier
        status.combined_multiplier = (
            status.earth_phi_boost *
            status.cosmic_boost *
            min(2.0, status.planetary_torque)  # Cap torque boost
        )
        
        return status
    
    # ═══════════════════════════════════════════════════════════════════════
    # LAYER 2: PRICE DATA COLLECTION
    # ═══════════════════════════════════════════════════════════════════════
    
    def get_price(self, platform: str, symbol: str) -> Tuple[float, float, float]:
        """
        Get current price from platform.
        Returns (price, bid, ask)
        """
        client = self.clients.get(platform)
        if not client:
            return 0.0, 0.0, 0.0
        
        try:
            if platform == 'binance':
                ticker = client.get_24h_ticker(symbol)
                price = float(ticker.get('lastPrice', 0))
                bid = float(ticker.get('bidPrice', price))
                ask = float(ticker.get('askPrice', price))
                return price, bid, ask
                
            elif platform == 'kraken':
                ticker = client.get_24h_ticker(symbol)
                if ticker:
                    price = float(ticker.get('lastPrice', 0))
                    # Kraken doesn't provide bid/ask in 24h ticker, use price
                    bid = price * 0.9999  # Approximate
                    ask = price * 1.0001
                    return price, bid, ask
                return 0.0, 0.0, 0.0
                
            elif platform == 'alpaca':
                quotes = client.get_latest_crypto_quotes([symbol])
                if quotes and 'quotes' in quotes:
                    q = quotes['quotes'].get(symbol, {})
                    bid = float(q.get('bp', 0))
                    ask = float(q.get('ap', 0))
                    price = (bid + ask) / 2 if bid and ask else 0
                    return price, bid, ask
                return 0.0, 0.0, 0.0
                
            elif platform == 'capital':
                if not client.enabled:
                    return 0.0, 0.0, 0.0
                market = client.get_market(symbol)
                if market:
                    bid = float(market.get('bid', 0))
                    ask = float(market.get('offer', market.get('ask', 0)))
                    price = (bid + ask) / 2 if bid and ask else 0
                    return price, bid, ask
                return 0.0, 0.0, 0.0
                
        except Exception as e:
            print(f"   ⚠️ Price error {platform}/{symbol}: {e}")
            return 0.0, 0.0, 0.0
        
        return 0.0, 0.0, 0.0
    
    def collect_price_data(self, platform: str, symbol: str, 
                           duration_sec: int = 30, 
                           interval_sec: float = 1.0) -> List[PriceSnapshot]:
        """
        Collect price data for probability analysis.
        """
        key = f"{platform}:{symbol}"
        if key not in self.price_history:
            self.price_history[key] = deque(maxlen=self.max_history)
        
        snapshots = []
        prev_price = None
        
        for i in range(int(duration_sec / interval_sec)):
            price, bid, ask = self.get_price(platform, symbol)
            if price <= 0:
                time.sleep(interval_sec)
                continue
            
            momentum = 0.0
            if prev_price and prev_price > 0:
                momentum = ((price - prev_price) / prev_price) * 100
            
            snapshot = PriceSnapshot(
                timestamp=time.time(),
                price=price,
                bid=bid,
                ask=ask,
                momentum=momentum
            )
            snapshots.append(snapshot)
            self.price_history[key].append(snapshot)
            
            prev_price = price
            time.sleep(interval_sec)
        
        return snapshots
    
    # ═══════════════════════════════════════════════════════════════════════
    # LAYER 3: PROBABILITY FORECAST
    # ═══════════════════════════════════════════════════════════════════════
    
    def _price_to_frequency(self, price: float, base_price: float) -> float:
        """Map price movement to frequency domain"""
        ratio = price / base_price if base_price > 0 else 1.0
        freq = 432.0 * (ratio ** PHI)
        return max(256, min(963, freq))
    
    def _is_harmonic_frequency(self, freq: float) -> Tuple[bool, str]:
        """Check if frequency is near a harmonic"""
        for name, harmonic in FREQ_MAP.items():
            if name != 'DISTORTION' and abs(freq - harmonic) < 20:
                return True, name
        if abs(freq - FREQ_MAP['DISTORTION']) < 10:
            return False, 'DISTORTION'
        return False, 'NEUTRAL'
    
    def _compute_prime_alignment(self, timestamp: float) -> float:
        """Compute temporal alignment with primes"""
        primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59]
        dt = datetime.fromtimestamp(timestamp)
        
        alignment = 0.0
        if dt.second in primes:
            alignment += 0.5
        if dt.minute in primes:
            alignment += 0.5
        return alignment
    
    def _compute_fibonacci_alignment(self, prices: List[float]) -> float:
        """Compute Fibonacci retracement alignment"""
        if len(prices) < 3:
            return 0.5
        
        high = max(prices)
        low = min(prices)
        current = prices[-1]
        
        if high == low:
            return 0.5
        
        retracement = (high - current) / (high - low)
        fib_levels = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
        
        min_dist = min(abs(retracement - level) for level in fib_levels)
        return 1.0 - min(1.0, min_dist * 3)
    
    def generate_probability_forecast(self, platform: str, symbol: str,
                                       snapshots: List[PriceSnapshot],
                                       cosmic_gates: CosmicGateStatus,
                                       asset_class: str = "crypto") -> ProbabilityForecast:
        """
        Generate 60-second probability forecast using ALL systems.
        """
        forecast = ProbabilityForecast(
            symbol=symbol,
            platform=platform,
            asset_class=asset_class,
            generated_at=datetime.now()
        )
        
        if len(snapshots) < 5:
            forecast.recommended_action = "INSUFFICIENT_DATA"
            return forecast
        
        prices = [s.price for s in snapshots]
        momentums = [s.momentum for s in snapshots]
        
        forecast.current_price = prices[-1]
        forecast.bid = snapshots[-1].bid
        forecast.ask = snapshots[-1].ask
        
        if forecast.bid > 0 and forecast.ask > 0:
            forecast.spread_pct = ((forecast.ask - forecast.bid) / forecast.bid) * 100
        
        # ─────────────────────────────────────────────────────────────────
        # MOMENTUM ANALYSIS
        # ─────────────────────────────────────────────────────────────────
        avg_momentum = np.mean(momentums) if momentums else 0
        momentum_trend = np.polyfit(range(len(momentums)), momentums, 1)[0] if len(momentums) > 2 else 0
        recent_momentum = np.mean(momentums[-5:]) if len(momentums) >= 5 else avg_momentum
        older_momentum = np.mean(momentums[:5]) if len(momentums) >= 5 else avg_momentum
        momentum_accel = recent_momentum - older_momentum
        
        # ─────────────────────────────────────────────────────────────────
        # FREQUENCY ANALYSIS
        # ─────────────────────────────────────────────────────────────────
        base_price = prices[0]
        forecast.frequency = self._price_to_frequency(forecast.current_price, base_price)
        forecast.is_harmonic, forecast.frequency_state = self._is_harmonic_frequency(forecast.frequency)
        
        # ─────────────────────────────────────────────────────────────────
        # PATTERN ALIGNMENT
        # ─────────────────────────────────────────────────────────────────
        forecast.prime_alignment = self._compute_prime_alignment(time.time())
        forecast.fibonacci_alignment = self._compute_fibonacci_alignment(prices)
        
        # Golden ratio proximity
        price_ratio = forecast.current_price / base_price if base_price > 0 else 1
        forecast.golden_ratio_proximity = 1.0 - min(1.0, abs(price_ratio - PHI) * 2)
        
        # ─────────────────────────────────────────────────────────────────
        # PRICE FORECAST (60 seconds ahead)
        # ─────────────────────────────────────────────────────────────────
        decay = 0.7
        projected_momentum = avg_momentum * decay + recent_momentum * (1 - decay)
        
        # Apply trend direction
        if momentum_trend > 0:
            projected_momentum *= 1.2
        elif momentum_trend < 0:
            projected_momentum *= 0.8
        
        # Harmonic boost
        if forecast.is_harmonic and forecast.frequency > 500:
            projected_momentum *= 1.1
        elif forecast.frequency_state == 'DISTORTION':
            projected_momentum *= 0.8
        
        # Cosmic boost integration
        projected_momentum *= cosmic_gates.combined_multiplier
        
        # Calculate forecast
        total_change_pct = projected_momentum * 60 * 0.01
        forecast.forecast_price = forecast.current_price * (1 + total_change_pct / 100)
        forecast.price_change_pct = total_change_pct
        
        # ─────────────────────────────────────────────────────────────────
        # PROBABILITY CALCULATION
        # ─────────────────────────────────────────────────────────────────
        # Base from momentum
        if avg_momentum > 0:
            base_bullish = 0.5 + min(0.3, avg_momentum * 0.1)
        else:
            base_bullish = 0.5 + max(-0.3, avg_momentum * 0.1)
        
        # Momentum acceleration
        base_bullish += np.clip(momentum_accel * 0.05, -0.1, 0.1)
        
        # Harmonic state
        if forecast.is_harmonic:
            base_bullish += 0.05
        elif forecast.frequency_state == 'DISTORTION':
            base_bullish -= 0.05
        
        # Pattern alignment
        pattern_boost = (forecast.prime_alignment + forecast.fibonacci_alignment + forecast.golden_ratio_proximity) / 3
        base_bullish += pattern_boost * 0.1
        
        # Cosmic coherence boost
        base_bullish += cosmic_gates.cosmic_coherence * 0.1
        
        # Earth coherence boost
        base_bullish += (cosmic_gates.earth_coherence - 0.5) * 0.1
        
        # Clamp
        forecast.bullish_probability = max(0.1, min(0.9, base_bullish))
        forecast.bearish_probability = 1 - forecast.bullish_probability
        
        # ─────────────────────────────────────────────────────────────────
        # CONFIDENCE CALCULATION
        # ─────────────────────────────────────────────────────────────────
        momentum_consistency = 1.0 - min(1.0, np.std(momentums) * 5) if momentums else 0.5
        
        forecast.confidence = (
            momentum_consistency * 0.3 +
            forecast.fibonacci_alignment * 0.2 +
            forecast.prime_alignment * 0.1 +
            cosmic_gates.earth_coherence * 0.2 +
            cosmic_gates.cosmic_coherence * 0.2
        )
        
        # ─────────────────────────────────────────────────────────────────
        # TRADING DECISION
        # ─────────────────────────────────────────────────────────────────
        fees = PLATFORM_FEES.get(platform, {'taker': 0.001})
        fee_pct = fees.get('taker', fees.get('spread', 0.001)) * 2 * 100
        min_profit_pct = fee_pct + MIN_PROFIT_PCT * 100
        
        forecast.position_multiplier = cosmic_gates.combined_multiplier
        
        if (forecast.bullish_probability > 0.65 and 
            forecast.price_change_pct > min_profit_pct and 
            forecast.confidence > 0.50):
            forecast.recommended_action = "BUY"
            forecast.expected_profit_pct = forecast.price_change_pct - fee_pct
        elif (forecast.bearish_probability > 0.65 and 
              forecast.price_change_pct < -min_profit_pct and 
              forecast.confidence > 0.50):
            forecast.recommended_action = "SELL"
            forecast.expected_profit_pct = abs(forecast.price_change_pct) - fee_pct
        else:
            forecast.recommended_action = "HOLD"
            forecast.expected_profit_pct = 0
        
        return forecast
    
    # ═══════════════════════════════════════════════════════════════════════
    # UNIFIED FORECAST GENERATION
    # ═══════════════════════════════════════════════════════════════════════
    
    def generate_forecast(self, platform: str, symbol: str, 
                          asset_class: str = "crypto",
                          collect_duration: int = 15) -> UniversalForecast:
        """
        Generate complete forecast for a single symbol on a platform.
        """
        forecast = UniversalForecast(
            symbol=symbol,
            platform=Platform(platform),
            asset_class=AssetClass(asset_class),
            generated_at=datetime.now()
        )
        
        # Layer 1: Cosmic Gates
        forecast.cosmic_gates = self.check_cosmic_gates()
        
        if not forecast.cosmic_gates.all_gates_open:
            forecast.should_trade = False
            forecast.reason = f"Gates closed: Earth={forecast.cosmic_gates.earth_open}, Cosmic={forecast.cosmic_gates.cosmic_open}"
            forecast.action = "HOLD"
            return forecast
        
        # Layer 2: Collect Price Data
        print(f"   📊 Collecting {collect_duration}s price data for {platform}:{symbol}...")
        snapshots = self.collect_price_data(platform, symbol, collect_duration, 0.5)
        
        if len(snapshots) < 10:
            forecast.should_trade = False
            forecast.reason = f"Insufficient data: {len(snapshots)} snapshots"
            forecast.action = "HOLD"
            return forecast
        
        # Layer 3: Probability Forecast
        forecast.probability = self.generate_probability_forecast(
            platform, symbol, snapshots, forecast.cosmic_gates, asset_class
        )
        
        # Final Decision
        if forecast.probability.recommended_action == "BUY":
            forecast.should_trade = True
            forecast.action = "BUY"
            forecast.reason = (f"Bullish {forecast.probability.bullish_probability:.1%} "
                              f"| Conf {forecast.probability.confidence:.1%} "
                              f"| +{forecast.probability.price_change_pct:.3f}%")
        elif forecast.probability.recommended_action == "SELL":
            forecast.should_trade = True
            forecast.action = "SELL"
            forecast.reason = (f"Bearish {forecast.probability.bearish_probability:.1%} "
                              f"| Conf {forecast.probability.confidence:.1%} "
                              f"| {forecast.probability.price_change_pct:.3f}%")
        else:
            forecast.should_trade = False
            forecast.action = "HOLD"
            forecast.reason = (f"No edge: Bull {forecast.probability.bullish_probability:.1%} "
                              f"| Conf {forecast.probability.confidence:.1%}")
        
        return forecast
    
    # ═══════════════════════════════════════════════════════════════════════
    # MULTI-PLATFORM SCANNING
    # ═══════════════════════════════════════════════════════════════════════
    
    def scan_all_platforms(self) -> Dict[str, List[UniversalForecast]]:
        """
        Scan ALL platforms for trading opportunities.
        Returns forecasts organized by platform.
        """
        results = {}
        
        # Platform-specific symbols to scan
        scan_config = {
            'binance': {
                'symbols': ['BTCUSDC', 'ETHUSDC', 'ADAUSDC', 'XLMUSDC', 'DOGEUSDC'],
                'asset_class': 'crypto'
            },
            'kraken': {
                'symbols': ['XBTUSD', 'ETHUSD', 'ADAUSD'],
                'asset_class': 'crypto'
            },
            'alpaca': {
                'symbols': ['BTC/USD', 'ETH/USD'],
                'asset_class': 'crypto'
            },
            'capital': {
                'symbols': ['BTCUSD', 'US500', 'EURUSD', 'GOLD'],
                'asset_class': 'mixed'
            }
        }
        
        for platform, config in scan_config.items():
            if not self.clients.get(platform):
                print(f"\n⚠️ {platform.upper()}: Client not available")
                continue
            
            print(f"\n{'='*60}")
            print(f"🔍 SCANNING {platform.upper()}")
            print(f"{'='*60}")
            
            results[platform] = []
            
            for symbol in config['symbols']:
                try:
                    forecast = self.generate_forecast(
                        platform, symbol, 
                        config['asset_class'],
                        collect_duration=10  # Quick scan
                    )
                    results[platform].append(forecast)
                    
                    # Print result
                    status = "🎯" if forecast.should_trade else "⏸️"
                    print(f"\n{status} {symbol}:")
                    print(f"   Action: {forecast.action}")
                    print(f"   Reason: {forecast.reason}")
                    
                    if forecast.probability:
                        print(f"   Price: ${forecast.probability.current_price:.5f}")
                        print(f"   Freq: {forecast.probability.frequency:.1f}Hz ({forecast.probability.frequency_state})")
                    
                except Exception as e:
                    print(f"\n❌ {symbol}: Error - {e}")
        
        return results
    
    def get_best_opportunities(self, results: Dict[str, List[UniversalForecast]], 
                                top_n: int = 3) -> List[UniversalForecast]:
        """
        Get the best trading opportunities across all platforms.
        """
        all_forecasts = []
        for platform_forecasts in results.values():
            all_forecasts.extend([f for f in platform_forecasts if f.should_trade])
        
        # Sort by expected profit
        all_forecasts.sort(
            key=lambda f: f.probability.expected_profit_pct if f.probability else 0,
            reverse=True
        )
        
        return all_forecasts[:top_n]
    
    def print_cosmic_status(self, gates: CosmicGateStatus):
        """Print formatted cosmic status"""
        print(f"""
╔══════════════════════════════════════════════════════════════════════════╗
║                    🌌 COSMIC GATE STATUS 🌌                              ║
╠══════════════════════════════════════════════════════════════════════════╣
║  🌍 EARTH RESONANCE                                                      ║
║     Gate: {'OPEN ✅' if gates.earth_open else 'CLOSED ❌':12s}  Coherence: {gates.earth_coherence:5.1%}                 ║
║     PHI Boost: {gates.earth_phi_boost:.3f}x           Phase Lock: {gates.earth_phase_lock:.1%}                 ║
╠══════════════════════════════════════════════════════════════════════════╣
║  ⚡ COSMIC STATE                                                         ║
║     Gate: {'OPEN ✅' if gates.cosmic_open else 'CLOSED ❌':12s}  Phase: {gates.cosmic_phase:15s}           ║
║     Coherence: {gates.cosmic_coherence:.3f}           Distortion: {gates.cosmic_distortion:.5f}               ║
║     Joy: {gates.cosmic_joy:.1f}  Reciprocity: {gates.cosmic_reciprocity:.1f}  Boost: {gates.cosmic_boost:.1f}x                      ║
╠══════════════════════════════════════════════════════════════════════════╣
║  🌙 PLANETARY                                                            ║
║     Torque: {gates.planetary_torque:.2f}x              Lunar Phase: {gates.lunar_phase:.1%}                  ║
╠══════════════════════════════════════════════════════════════════════════╣
║  📊 COMBINED                                                             ║
║     ALL GATES: {'OPEN ✅' if gates.all_gates_open else 'CLOSED ❌':12s}   Multiplier: {gates.combined_multiplier:.3f}x               ║
╚══════════════════════════════════════════════════════════════════════════╝
""")


# ═══════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

def main():
    print("\n" + "="*70)
    print("🌌🎯 AUREON UNIVERSAL FORECAST SYSTEM 🎯🌌")
    print("="*70)
    print("\nThis system uses ALL prediction engines across ALL platforms:")
    print("  • Earth Resonance Engine (Schumann, PHI)")
    print("  • Imperial Predictability (Cosmic state, torque)")
    print("  • Probability Matrix (Temporal frequency)")
    print("  • Multi-Platform Support (Binance, Kraken, Alpaca, Capital)")
    
    # Initialize
    engine = UniversalForecastEngine()
    
    # Check cosmic gates first
    print("\n" + "="*70)
    print("LAYER 1: COSMIC GATE CHECK")
    print("="*70)
    
    gates = engine.check_cosmic_gates()
    engine.print_cosmic_status(gates)
    
    if not gates.all_gates_open:
        print("\n⚠️ COSMIC GATES NOT FULLY OPEN")
        print("   Trading not recommended at this time.")
        proceed = input("\n   Type 'OVERRIDE' to scan anyway: ")
        if proceed != 'OVERRIDE':
            print("\n   Exiting. Try again when gates align.")
            return
    
    # Scan all platforms
    print("\n" + "="*70)
    print("LAYER 2-3: MULTI-PLATFORM PROBABILITY SCAN")
    print("="*70)
    
    results = engine.scan_all_platforms()
    
    # Get best opportunities
    print("\n" + "="*70)
    print("🏆 TOP OPPORTUNITIES")
    print("="*70)
    
    best = engine.get_best_opportunities(results, top_n=5)
    
    if not best:
        print("\n   No high-probability opportunities found.")
        print("   Markets may be flat or conditions unfavorable.")
    else:
        for i, opp in enumerate(best, 1):
            prob = opp.probability
            print(f"\n   #{i} {opp.platform.value.upper()}:{opp.symbol}")
            print(f"      Action: {opp.action}")
            print(f"      Probability: {prob.bullish_probability:.1%} bullish")
            print(f"      Confidence: {prob.confidence:.1%}")
            print(f"      Expected: +{prob.expected_profit_pct:.3f}%")
            print(f"      Price: ${prob.current_price:.5f}")
            print(f"      Frequency: {prob.frequency:.1f}Hz ({prob.frequency_state})")
    
    print("\n" + "="*70)
    print("FORECAST COMPLETE")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
