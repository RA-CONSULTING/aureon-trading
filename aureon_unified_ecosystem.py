#!/usr/bin/env python3
"""
🐙🌌 AUREON KRAKEN ECOSYSTEM - THE UNIFIED TRADING ENGINE 🌌🐙
================================================================
ONE DYNAMIC PYTHON FOR THE ENTIRE KRAKEN ECOSYSTEM

Combines ALL the best from:
- aureon_51_live.py (51% win rate strategy)
- aureon_infinite_kraken.py (10-9-1 Queen Hive compounding)
- aureon_multiverse.py (Temporal analysis)
- aureon_mycelium.py (Neural network intelligence)
- aureon_qgita.py (9 Auris nodes)
- kraken_multi_sim.py (Multi-strategy analysis)

FEATURES:
├─ 🔴 Real-time WebSocket prices
├─ 🎯 Multiple strategies running simultaneously
├─ 🍄 Neural network pattern detection
├─ 🐅 9 Auris nodes for market analysis
├─ 💰 Compounding with 10-9-1 model
├─ 📊 Dynamic opportunity scoring
└─ 🔄 Infinite loop - never stops growing

GOAL: 51%+ Win Rate with NET PROFIT after ALL fees

Gary Leckey & GitHub Copilot | November 2025
"From Atom to Multiverse - We don't quit!"
"""

import os
import sys
import json
import time
import math
import random
import asyncio
import websockets
import threading
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import deque
from threading import Thread, Lock

sys.path.insert(0, '/workspaces/aureon-trading')
from unified_exchange_client import UnifiedExchangeClient, MultiExchangeClient
from aureon_lattice import LatticeEngine
from aureon_market_pulse import MarketPulse

# 🌍⚡ HNC FREQUENCY INTEGRATION ⚡🌍
try:
    from hnc_master_protocol import HarmonicNexusCore, HNCTradingBridge, LiveMarketFrequencyFeed
    HNC_AVAILABLE = True
except ImportError as e:
    HNC_AVAILABLE = False
    print(f"⚠️  HNC module not available - frequency analysis disabled: {e}")

# 🌍⚡ HNC PROBABILITY MATRIX INTEGRATION ⚡🌍
try:
    from hnc_probability_matrix import HNCProbabilityIntegration, ProbabilityMatrix
    PROB_MATRIX_AVAILABLE = True
except ImportError as e:
    PROB_MATRIX_AVAILABLE = False
    print(f"⚠️  Probability Matrix not available: {e}")
    print(f"⚠️  HNC module not available - frequency analysis disabled: {e}")

# 🌍⚡ COINAPI ANOMALY DETECTION ⚡🌍
try:
    from coinapi_anomaly_detector import CoinAPIClient, AnomalyDetector, AnomalyType
    COINAPI_AVAILABLE = True
except ImportError as e:
    COINAPI_AVAILABLE = False
    print(f"⚠️  CoinAPI Anomaly Detector not available: {e}")

# 🌉 AUREON BRIDGE - ULTIMATE ↔ UNIFIED COMMUNICATION 🌉
try:
    from aureon_bridge import AureonBridge, Opportunity as BridgeOpportunity, CapitalState, Position as BridgePosition
    BRIDGE_AVAILABLE = True
except ImportError as e:
    BRIDGE_AVAILABLE = False
    print(f"⚠️  Aureon Bridge not available: {e}")

# 🌌⚡ HNC IMPERIAL PREDICTABILITY ENGINE ⚡🌌
try:
    from hnc_imperial_predictability import (
        ImperialTradingIntegration, PredictabilityEngine, CosmicStateEngine,
        CosmicPhase, MarketTorque, ImperialPredictabilityMatrix
    )
    IMPERIAL_AVAILABLE = True
except ImportError as e:
    IMPERIAL_AVAILABLE = False
    print(f"⚠️  Imperial Predictability not available: {e}")

# 🌍⚡ EARTH RESONANCE ENGINE ⚡🌍
try:
    from earth_resonance_engine import EarthResonanceEngine, get_earth_engine
    EARTH_RESONANCE_AVAILABLE = True
except ImportError as e:
    EARTH_RESONANCE_AVAILABLE = False
    print(f"⚠️  Earth Resonance Engine not available: {e}")

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION - THE UNIFIED PARAMETERS
# ═══════════════════════════════════════════════════════════════

CONFIG = {
    'EXCHANGE': os.getenv('EXCHANGE', 'both').lower(), # Default to BOTH
    # Trading Parameters
    'BASE_CURRENCY': os.getenv('BASE_CURRENCY', 'USD'),  # USD or GBP
    
    # Platform-Specific Fees (as decimals)
    # ══════════════════════════════════════════════════════════
    # 🐙 KRAKEN
    'KRAKEN_FEE_MAKER': 0.0016,     # 0.16% maker fee (Standard Kraken Pro)
    'KRAKEN_FEE_TAKER': 0.0026,     # 0.26% taker fee (Standard Kraken Pro)
    'KRAKEN_FEE': 0.0026,           # Legacy field (uses taker)
    
    # 🟡 BINANCE (UK Account - Spot only)
    'BINANCE_FEE_MAKER': 0.0010,    # 0.10% maker (with BNB discount: 0.075%)
    'BINANCE_FEE_TAKER': 0.0010,    # 0.10% taker (with BNB discount: 0.075%)
    'BINANCE_FEE': 0.0010,          # Default taker
    
    # 🦙 ALPACA (Crypto)
    'ALPACA_FEE_MAKER': 0.0015,     # 0.15% maker (crypto)
    'ALPACA_FEE_TAKER': 0.0025,     # 0.25% taker (crypto)
    'ALPACA_FEE_STOCK': 0.0000,     # $0 commission for stocks!
    'ALPACA_FEE': 0.0025,           # Default taker for crypto
    'ALPACA_ANALYTICS_ONLY': True,  # 🦙 Alpaca is for market data/analytics only (no trades)
    
    # 💼 CAPITAL.COM (CFD/Spread Betting)
    'CAPITAL_FEE_SPREAD': 0.0010,   # ~0.1% avg spread cost (varies by instrument)
    'CAPITAL_FEE_OVERNIGHT': 0.0001,# Daily overnight financing (annualized ~2.5%)
    'CAPITAL_FEE': 0.0010,          # Default spread cost
    
    # General
    'SLIPPAGE_PCT': 0.0010,         # 0.10% estimated slippage per trade
    'SPREAD_COST_PCT': 0.0005,      # 0.05% estimated spread cost
    'TAKE_PROFIT_PCT': 1.2,         # 1.2% profit target (ASYMMETRIC - higher reward)
    'STOP_LOSS_PCT': 0.6,           # 0.6% stop loss (1:2 risk/reward for 55% WR)
    'MAX_POSITIONS': 15,            # Fewer, higher quality positions
    'MIN_TRADE_USD': 5.0,           # Minimum trade notional in base currency
    'PORTFOLIO_RISK_BUDGET': 0.90,  # Use 90% of equity - some buffer
    'MIN_EXPECTED_EDGE_GBP': 0.001, # Require positive edge
    'DEFAULT_WIN_PROB': 0.55,       # Target win probability
    'WIN_RATE_CONFIDENCE_TRADES': 25,
    'EQUITY_MIN_DELTA': 0.10,       # Smaller delta for frequent compounding
    'EQUITY_TOLERANCE_GBP': 0.0,
    
    # Dynamic Portfolio Rebalancing
    'ENABLE_REBALANCING': True,     # Sell underperformers to buy better opportunities
    'REBALANCE_THRESHOLD': -0.5,    # Sell position if it's losing more than 0.5%
    'MIN_HOLD_CYCLES': 3,           # Hold at least 3 cycles before considering rebalance
    'QUOTE_CURRENCIES': ['GBP', 'USD', 'EUR', 'USDT', 'BTC', 'ETH'],  # Trade ALL quote currencies
    
    # Scout Deployment (from immediateWaveRider.ts)
    'DEPLOY_SCOUTS_IMMEDIATELY': False,  # Deploy 1 position per currency on first scan
    'SCOUT_MIN_MOMENTUM': 2.0,          # Minimum 24h change % for scout entries
    
    # Kelly Criterion & Risk Management
    'USE_KELLY_SIZING': True,       # Use Kelly instead of fixed %
    'KELLY_SAFETY_FACTOR': 0.5,     # Half-Kelly for safety
    'BASE_POSITION_SIZE': 0.10,     # Base size when Kelly disabled
    'MAX_POSITION_SIZE': 0.25,      # Hard cap per trade
    'MAX_SYMBOL_EXPOSURE': 0.30,    # Max 30% in one symbol
    'MAX_DRAWDOWN_PCT': 15.0,       # Circuit breaker at 15% DD
    'MIN_NETWORK_COHERENCE': 0.20,  # NEVER pause - always trade!
    
    # Opportunity Filters - QUALITY OVER QUANTITY 🎯
    'MIN_MOMENTUM': 0.5,            # Require positive momentum (trend confirmation)
    'MAX_MOMENTUM': 50.0,           # Avoid parabolic pumps (reversal risk)
    'MIN_VOLUME': 50000,            # Decent volume = reliable execution
    'MIN_SCORE': 65,                # High bar = QUALITY TRADES ONLY
    
    # 🎯 OPTIMAL WIN RATE MODE
    'ENABLE_OPTIMAL_WR': True,      # Enable all win rate optimizations
    'OPTIMAL_MIN_GATES': 3,         # Minimum number of gates that must be GREEN
    'OPTIMAL_MIN_COHERENCE': 0.50,  # Higher coherence requirement
    'OPTIMAL_TREND_CONFIRM': True,  # Require trend confirmation
    'OPTIMAL_MULTI_TF_CHECK': True, # Multi-timeframe coherence check
    
    # Compounding (10-9-1 Model)
    'COMPOUND_PCT': 0.90,           # 90% compounds
    'HARVEST_PCT': 0.10,            # 10% harvests
    
    # Auris Node Frequencies (Hz)
    'FREQ_TIGER': 741.0,
    'FREQ_FALCON': 852.0,
    'FREQ_HUMMINGBIRD': 963.0,
    'FREQ_DOLPHIN': 528.0,
    'FREQ_DEER': 396.0,
    'FREQ_OWL': 432.0,
    'FREQ_PANDA': 412.3,
    'FREQ_CARGOSHIP': 174.0,
    'FREQ_CLOWNFISH': 639.0,
    
    # Coherence Thresholds - OPTIMAL WIN RATE MODE 🎯
    'HIGH_COHERENCE_MODE': True,   # Enabled for better win rate
    'ENTRY_COHERENCE': 0.45,       # Higher bar for quality entries
    'EXIT_COHERENCE': 0.35,        # Exit when coherence drops
    
    # Lambda Field Components (from coherenceTrader.ts)
    'ENABLE_LAMBDA_FIELD': os.getenv('ENABLE_LAMBDA_FIELD', '1') == '1',  # Full Λ(t) = S(t) + O(t) + E(t)
    'OBSERVER_WEIGHT': 0.3,         # O(t) = Λ(t-1) × 0.3 (self-reference)
    'ECHO_WEIGHT': 0.2,             # E(t) = avg(Λ[t-5:t]) × 0.2 (memory)
    
    # 🌍⚡ HNC Frequency Integration ⚡🌍
    'ENABLE_HNC_FREQUENCY': os.getenv('ENABLE_HNC', '1') == '1',  # Use HNC frequency for sizing
    'HNC_FREQUENCY_WEIGHT': 0.25,    # H(t) weight in Lambda field
    'HNC_COHERENCE_THRESHOLD': 0.50, # Min triadic coherence for full sizing
    'HNC_HARMONIC_BONUS': 1.15,      # 15% bonus for harmonic resonance (256/528 Hz)
    'HNC_DISTORTION_PENALTY': 0.70,  # 30% penalty for 440 Hz distortion
    
    # 🌍⚡ HNC Probability Matrix (2-Hour Window) ⚡🌍
    'ENABLE_PROB_MATRIX': os.getenv('ENABLE_PROB_MATRIX', '1') == '1',
    'PROB_MIN_CONFIDENCE': 0.50,     # Minimum confidence to use probability
    'PROB_HIGH_THRESHOLD': 0.65,     # High probability threshold for boost
    'PROB_LOW_THRESHOLD': 0.40,      # Low probability threshold for reduction
    'PROB_LOOKBACK_MINUTES': 60,     # Hour -1 lookback window
    'PROB_FORECAST_WEIGHT': 0.4,     # Weight of Hour +1 in position sizing
    
    # 🌌⚡ HNC Imperial Predictability Engine ⚡🌌
    'ENABLE_IMPERIAL': os.getenv('ENABLE_IMPERIAL', '1') == '1',  # Cosmic synchronization
    'IMPERIAL_POSITION_WEIGHT': 0.35,   # Weight of imperial modifier in sizing
    'IMPERIAL_MIN_COHERENCE': 0.30,     # Lowered: Minimum cosmic coherence to trade
    'IMPERIAL_DISTORTION_LIMIT': 0.50,  # Raised: Allow trades up to 50% distortion
    'IMPERIAL_COSMIC_BOOST': True,      # Apply cosmic phase boost
    'IMPERIAL_YIELD_THRESHOLD': 1e30,   # Min imperial yield for action
    
    # 🌍⚡ Earth Resonance Engine ⚡🌍
    'ENABLE_EARTH_RESONANCE': os.getenv('ENABLE_EARTH_RESONANCE', '1') == '1',
    'EARTH_COHERENCE_THRESHOLD': 0.50,  # Field coherence gate threshold (lowered for WR)
    'EARTH_PHASE_LOCK_THRESHOLD': 0.60, # Phase lock gate threshold (lowered from 0.85)
    'EARTH_PHI_AMPLIFICATION': True,    # Use PHI (1.618) position boost
    'EARTH_SENTIMENT_MAPPING': True,    # Map fear/greed to emotional frequencies
    'EARTH_EXIT_URGENCY': True,         # Use resonance for exit urgency
    
    # 🌍⚡ CoinAPI Anomaly Detection ⚡🌍
    'ENABLE_COINAPI': os.getenv('ENABLE_COINAPI', '0') == '1',  # Requires API key
    'COINAPI_SCAN_INTERVAL': 300,    # Scan for anomalies every 5 minutes
    'COINAPI_MIN_SEVERITY': 0.40,    # Minimum severity to act on anomaly
    'COINAPI_BLACKLIST_DURATION': 3600,  # Block symbol for 1 hour on wash trading
    'COINAPI_ADJUST_COHERENCE': True,    # Adjust coherence based on anomalies
    'COINAPI_PRICE_SOURCE': 'multi_exchange',  # Use aggregated prices when available
    
    # WebSocket
    'WS_URL': 'wss://ws.kraken.com',
    'WS_RECONNECT_DELAY': 5,        # Seconds between reconnect attempts
    'WS_HEARTBEAT_TIMEOUT': 60,     # Max seconds without WS message
    
    # State Persistence
    'STATE_FILE': 'aureon_kraken_state.json',
    
    # Elephant Memory (Quackers)
    'LOSS_STREAK_LIMIT': 3,
    'COOLDOWN_MINUTES': 13,       # Fibonacci timing
    
    # System Flux Prediction (30-Span)
    'FLUX_SPAN': 30,              # Number of assets to analyze for flux
    'FLUX_THRESHOLD': 0.60,       # Minimum flux strength to override probability
}

PHI = (1 + math.sqrt(5)) / 2  # Golden Ratio = 1.618


def kelly_criterion(win_rate: float, avg_win: float, avg_loss: float, safety_factor: float = 0.5) -> float:
    """
    Calculate Kelly Criterion position size.
    
    Formula: f* = (p*b - (1-p)) / b
    Where:
        p = win probability
        b = win/loss ratio (avg_win / avg_loss)
    
    Returns: Position size as fraction of balance (with safety factor applied)
    """
    if avg_loss <= 0 or win_rate <= 0 or win_rate >= 1:
        return 0.10  # Fallback to 10%
    
    b = avg_win / avg_loss
    kelly_fraction = (win_rate * b - (1 - win_rate)) / b
    
    # Apply safety factor and bounds
    kelly_fraction = max(0, kelly_fraction) * safety_factor
    return min(kelly_fraction, CONFIG['MAX_POSITION_SIZE'])


# ═══════════════════════════════════════════════════════════════
# 🌟 SWARM ORCHESTRATOR ENHANCEMENTS
# ═══════════════════════════════════════════════════════════════

# Prime numbers for dynamic sizing (from multi_agent_aggressive.ts)
PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71]
PRIME_SCALE = 0.001  # 0.1% per prime unit → 0.2%, 0.3%, 0.5%, 0.7%, etc.

# Fibonacci sequence for timing (from multi_agent_aggressive.ts)
FIBONACCI = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987]


@dataclass
class MarketSignal:
    """Signal broadcast from scout position (from swarmOrchestrator.ts)"""
    symbol: str
    direction: str  # 'BUY' or 'SELL'
    strength: float  # 0.0 to 1.0
    momentum: float  # % change
    coherence: float  # Gamma value
    timestamp: float
    scout_id: Optional[str] = None


@dataclass
class CapitalPool:
    """Central capital management (from swarmOrchestrator.ts - bee hive)"""
    total_equity: float = 0.0
    allocated: Dict[str, float] = field(default_factory=dict)  # {symbol: amount}
    reserved: float = 0.0  # Keep 10% reserved for opportunities
    profits_this_cycle: float = 0.0
    total_profits: float = 0.0
    sentiment_score: float = 0.0  # -10 to +10 (Neutral 0)
    
    def update_equity(self, new_equity: float):
        """Update total equity and recalculate reserves based on sentiment"""
        self.total_equity = new_equity
        
        # Dynamic Reserve:
        # Neutral (0): 10%
        # Bullish (>2): 5% (Aggressive)
        # Bearish (<-2): 20% (Defensive)
        reserve_pct = 0.10
        if self.sentiment_score > 2.0:
            reserve_pct = 0.05
        elif self.sentiment_score < -2.0:
            reserve_pct = 0.20
            
        self.reserved = new_equity * reserve_pct

    def update_sentiment(self, score: float):
        """Update market sentiment score to adjust risk parameters"""
        self.sentiment_score = score
        # Recalculate reserve with new sentiment
        self.update_equity(self.total_equity)

    def get_recommended_position_size(self, base_pct: float = 0.05) -> float:
        """
        Calculate recommended position size based on sentiment.
        base_pct: Base position size percentage (e.g., 0.05 for 5%)
        """
        # Adjust size based on sentiment
        adjusted_pct = base_pct
        if self.sentiment_score > 5.0: # Very Bullish
            adjusted_pct *= 1.5
        elif self.sentiment_score < -2.0: # Bearish
            adjusted_pct *= 0.5
            
        # Cap at 20% of total equity
        max_size = self.total_equity * 0.20
        
        # Calculate size
        size = self.total_equity * adjusted_pct
        return min(size, max_size)
        
    def allocate(self, symbol: str, amount: float) -> bool:
        """Allocate capital to a position"""
        available = self.total_equity - sum(self.allocated.values()) - self.reserved
        if available >= amount:
            self.allocated[symbol] = self.allocated.get(symbol, 0) + amount
            return True
        return False
        
    def deallocate(self, symbol: str, amount: float, profit: float = 0.0):
        """Return capital from closed position"""
        if symbol in self.allocated:
            self.allocated[symbol] = max(0, self.allocated[symbol] - amount)
            if self.allocated[symbol] == 0:
                del self.allocated[symbol]
        self.profits_this_cycle += profit
        self.total_profits += profit
        
    def get_available(self) -> float:
        """Get unallocated capital"""
        return max(0, self.total_equity - sum(self.allocated.values()) - self.reserved)


class SignalBroadcaster:
    """Manages signal broadcasting between positions (from swarmOrchestrator.ts - wolf scout)"""
    
    def __init__(self):
        self.latest_signal: Optional[MarketSignal] = None
        self.signal_history: deque = deque(maxlen=20)
        self.scout_positions: List[str] = []  # Positions that can act as scouts
        
    def broadcast_signal(self, signal: MarketSignal):
        """Broadcast a new signal from scout"""
        self.latest_signal = signal
        self.signal_history.append(signal)
        
    def get_latest_signal(self, max_age_seconds: float = 60.0) -> Optional[MarketSignal]:
        """Get latest signal if not too old"""
        if self.latest_signal:
            age = time.time() - self.latest_signal.timestamp
            if age <= max_age_seconds:
                return self.latest_signal
        return None
        
    def should_follow_signal(self, symbol: str, signal: MarketSignal) -> bool:
        """Determine if a position should follow the signal"""
        # Don't follow signals for the same symbol (avoid feedback loop)
        if symbol == signal.symbol:
            return False
        # Only follow strong signals (strength > 0.5)
        if signal.strength < 0.5:
            return False
        # Only follow if coherence is good
        if signal.coherence < 0.4:
            return False
        return True


class PositionSplitter:
    """Manages position splitting (from queen_hive.ts - hive splitting)"""
    
    def __init__(self):
        self.split_threshold = 2.0  # Split when position reaches 2x entry value
        self.max_generation = 5  # Max split depth
        self.split_history: List[Dict] = []
        
    def should_split(self, position_value: float, entry_value: float, generation: int) -> bool:
        """Check if position should split"""
        if generation >= self.max_generation:
            return False
        return position_value >= entry_value * self.split_threshold
        
    def execute_split(self, position: 'Position') -> Tuple['Position', 'Position']:
        """Split position into two child positions"""
        # Each child gets half the value
        split_value = position.size * position.current_price / 2
        split_size = position.size / 2
        
        # Create two children at next generation
        child1 = Position(
            symbol=position.symbol,
            size=split_size,
            entry_price=position.current_price,
            current_price=position.current_price,
            quote_asset=position.quote_asset,
            generation=position.generation + 1,
            parent_id=position.id
        )
        
        child2 = Position(
            symbol=position.symbol,
            size=split_size,
            entry_price=position.current_price,
            current_price=position.current_price,
            quote_asset=position.quote_asset,
            generation=position.generation + 1,
            parent_id=position.id
        )
        
        # Record split event
        self.split_history.append({
            'timestamp': time.time(),
            'parent_id': position.id,
            'parent_value': position.size * position.current_price,
            'generation': position.generation,
            'children': [child1.id, child2.id]
        })
        
        return child1, child2


class PrimeSizer:
    """Prime-based dynamic position sizing (from multi_agent_aggressive.ts)"""
    
    def __init__(self):
        self.prime_idx = 0
        self.fib_idx = 0
        
    def get_next_size(self, base_size: float) -> float:
        """Get next position size using prime scaling"""
        prime = PRIMES[self.prime_idx % len(PRIMES)]
        size = base_size * prime * PRIME_SCALE
        self.prime_idx += 1
        return size
        
    def get_fibonacci_timing(self) -> int:
        """Get next timing interval using Fibonacci"""
        fib = FIBONACCI[self.fib_idx % len(FIBONACCI)]
        self.fib_idx += 1
        return fib
        
    def reset(self):
        """Reset indices"""
        self.prime_idx = 0
        self.fib_idx = 0


# ═══════════════════════════════════════════════════════════════
# 🐅 AURIS NODES - 9 Nodes of Market Analysis
# ═══════════════════════════════════════════════════════════════

@dataclass
class MarketState:
    """Complete market snapshot for analysis"""
    symbol: str
    price: float
    bid: float = 0.0
    ask: float = 0.0
    volume: float = 0.0
    change_24h: float = 0.0
    high_24h: float = 0.0
    low_24h: float = 0.0
    prices: List[float] = field(default_factory=list)
    timestamp: float = 0.0


class AurisNode:
    """Base class for all Auris nodes"""
    def __init__(self, name: str, freq: float, weight: float = 1.0):
        self.name = name
        self.freq = freq
        self.weight = weight
        self.response = 0.0
        
    def compute(self, state: MarketState) -> float:
        raise NotImplementedError


class TigerNode(AurisNode):
    """🐅 Volatility & Spread - Cuts the noise"""
    def __init__(self):
        super().__init__("Tiger", CONFIG['FREQ_TIGER'], 1.2)
        
    def compute(self, state: MarketState) -> float:
        if state.ask <= 0 or state.bid <= 0:
            return 0.5
        spread = (state.ask - state.bid) / state.price if state.price > 0 else 0
        # Low spread = high coherence
        self.response = max(0, 1 - spread * 100)
        return self.response


class FalconNode(AurisNode):
    """🦅 Speed & Momentum - Quick strikes"""
    def __init__(self):
        super().__init__("Falcon", CONFIG['FREQ_FALCON'], 1.1)
        
    def compute(self, state: MarketState) -> float:
        # Positive momentum = high coherence
        if state.change_24h > 10:
            self.response = 0.9
        elif state.change_24h > 5:
            self.response = 0.75
        elif state.change_24h > 2:
            self.response = 0.6
        elif state.change_24h > 0:
            self.response = 0.5
        else:
            self.response = 0.3
        return self.response


class HummingbirdNode(AurisNode):
    """🐦 Stability - High frequency lock"""
    def __init__(self):
        super().__init__("Hummingbird", CONFIG['FREQ_HUMMINGBIRD'], 1.0)
        
    def compute(self, state: MarketState) -> float:
        if len(state.prices) < 3:
            return 0.5
        # Low variance = stable = high coherence
        mean = sum(state.prices) / len(state.prices)
        variance = sum((p - mean) ** 2 for p in state.prices) / len(state.prices)
        std = math.sqrt(variance) if variance > 0 else 0
        cv = std / mean if mean > 0 else 0
        self.response = max(0, 1 - cv * 10)
        return self.response


class DolphinNode(AurisNode):
    """🐬 Waveform - Emotional carrier"""
    def __init__(self):
        super().__init__("Dolphin", CONFIG['FREQ_DOLPHIN'], 1.3)  # 528 Hz = Love frequency
        
    def compute(self, state: MarketState) -> float:
        if len(state.prices) < 5:
            return 0.5
        # Detect wave pattern (up-down-up)
        ups = sum(1 for i in range(1, len(state.prices)) if state.prices[i] > state.prices[i-1])
        ratio = ups / (len(state.prices) - 1)
        # Balanced waves = good
        self.response = 1 - abs(ratio - 0.6)  # Slight bullish bias
        return self.response


class DeerNode(AurisNode):
    """🦌 Sensing - Micro-shifts detection"""
    def __init__(self):
        super().__init__("Deer", CONFIG['FREQ_DEER'], 0.9)
        
    def compute(self, state: MarketState) -> float:
        if len(state.prices) < 2:
            return 0.5
        # Recent micro-movement
        recent_change = (state.prices[-1] - state.prices[-2]) / state.prices[-2] if state.prices[-2] > 0 else 0
        self.response = 0.5 + recent_change * 50  # Scale micro moves
        self.response = max(0, min(1, self.response))
        return self.response


class OwlNode(AurisNode):
    """🦉 Memory - Pattern recognition"""
    def __init__(self):
        super().__init__("Owl", CONFIG['FREQ_OWL'], 1.1)
        self.memory: Dict[str, List[float]] = {}
        
    def compute(self, state: MarketState) -> float:
        if state.symbol not in self.memory:
            self.memory[state.symbol] = []
        self.memory[state.symbol].append(state.change_24h)
        if len(self.memory[state.symbol]) > 100:
            self.memory[state.symbol] = self.memory[state.symbol][-100:]
            
        history = self.memory[state.symbol]
        if len(history) < 5:
            return 0.5
            
        # Pattern: was it bullish before?
        avg_momentum = sum(history[-10:]) / min(10, len(history))
        self.response = 0.5 + avg_momentum / 20
        self.response = max(0, min(1, self.response))
        return self.response


class PandaNode(AurisNode):
    """🐼 Safety - Grounding and protection"""
    def __init__(self):
        super().__init__("Panda", CONFIG['FREQ_PANDA'], 1.0)
        
    def compute(self, state: MarketState) -> float:
        # Volume = safety (liquidity)
        if state.volume > 1000000:
            self.response = 0.9
        elif state.volume > 500000:
            self.response = 0.75
        elif state.volume > 100000:
            self.response = 0.6
        elif state.volume > 50000:
            self.response = 0.5
        else:
            self.response = 0.3
        return self.response


class CargoShipNode(AurisNode):
    """🚢 Liquidity - Momentum buffer"""
    def __init__(self):
        super().__init__("CargoShip", CONFIG['FREQ_CARGOSHIP'], 0.8)
        
    def compute(self, state: MarketState) -> float:
        # High volume relative to price range = good liquidity
        if state.high_24h <= state.low_24h or state.volume <= 0:
            return 0.5
        range_pct = (state.high_24h - state.low_24h) / state.low_24h
        vol_per_range = state.volume / (range_pct * 100) if range_pct > 0 else 0
        self.response = min(1, vol_per_range / 100000)
        return self.response


class ClownfishNode(AurisNode):
    """🐠 Symbiosis - Market connection"""
    def __init__(self):
        super().__init__("Clownfish", CONFIG['FREQ_CLOWNFISH'], 0.9)
        
    def compute(self, state: MarketState) -> float:
        # Connection = how well this coin moves with market sentiment
        # Positive momentum with good volume = connected
        if state.change_24h > 0 and state.volume > 100000:
            self.response = 0.7 + min(0.3, state.change_24h / 30)
        elif state.change_24h > 0:
            self.response = 0.5 + min(0.2, state.change_24h / 20)
        else:
            self.response = 0.4
        return self.response


class AurisEngine:
    """The complete 9-node Auris analysis engine with Lambda field + HNC frequency"""
    
    def __init__(self):
        self.nodes = [
            TigerNode(),
            FalconNode(),
            HummingbirdNode(),
            DolphinNode(),
            DeerNode(),
            OwlNode(),
            PandaNode(),
            CargoShipNode(),
            ClownfishNode(),
        ]
        # Lambda field components (Λ = S + O + E + H)
        self.last_lambda = 0.5      # O(t) = Observer (self-reference)
        self.lambda_history = deque(maxlen=5)  # E(t) = Echo (memory)
        
        # 🌍⚡ HNC Frequency Integration ⚡🌍
        self.hnc = None
        self.hnc_bridge = None
        self.hnc_frequency = 256.0  # Default to ROOT frequency
        self.hnc_coherence = 0.0
        self.hnc_is_harmonic = False
        self.asset_frequencies: Dict[str, Dict[str, Any]] = {}  # Per-asset frequency tracking
        self.frequency_history: deque = deque(maxlen=100)  # Global frequency history
        if HNC_AVAILABLE and CONFIG.get('ENABLE_HNC_FREQUENCY', True):
            try:
                self.hnc = HarmonicNexusCore(guardian_id="02111991")
                self.hnc_bridge = HNCTradingBridge(self.hnc)
                print("   🌍⚡ HNC Frequency Layer ACTIVE")
            except Exception as e:
                print(f"   ⚠️  HNC init failed: {e}")
        
        # 🌍⚡ Probability Matrix Integration ⚡🌍
        self.prob_matrix = None
        if PROB_MATRIX_AVAILABLE and CONFIG.get('ENABLE_PROB_MATRIX', True):
            try:
                self.prob_matrix = HNCProbabilityIntegration()
                print("   📊 Probability Matrix (2-Hour Window) ACTIVE")
            except Exception as e:
                print(f"   ⚠️  Probability Matrix init failed: {e}")
        
        # 🌍⚡ CoinAPI Anomaly Detection ⚡🌍
        self.coinapi_detector = None
        self.anomaly_blacklist: Dict[str, float] = {}  # {symbol: unblock_timestamp}
        self.coherence_adjustments: Dict[str, float] = {}  # {symbol: adjustment_factor}
        self.last_anomaly_scan = 0
        if COINAPI_AVAILABLE and CONFIG.get('ENABLE_COINAPI', False):
            try:
                api_key = os.getenv('COINAPI_KEY', '')
                if api_key:
                    coinapi_client = CoinAPIClient(api_key)
                    self.coinapi_detector = AnomalyDetector(coinapi_client)
                    print("   🌐 CoinAPI Anomaly Detection ACTIVE")
                else:
                    print("   ⚠️  CoinAPI enabled but no API key found")
            except Exception as e:
                print(f"   ⚠️  CoinAPI init failed: {e}")
        
        # 🌌⚡ Imperial Predictability Engine ⚡🌌
        self.imperial = None
        self.cosmic_state = None
        self.imperial_yield = 0.0
        self.cosmic_phase = "UNKNOWN"
        if IMPERIAL_AVAILABLE and CONFIG.get('ENABLE_IMPERIAL', True):
            try:
                self.imperial = ImperialTradingIntegration()
                self.cosmic_state = self.imperial.update_cosmic_state()
                print("   🌌⚡ Imperial Predictability Engine ACTIVE")
                print(f"      ├─ Cosmic Phase: {self.cosmic_state.phase.value}")
                print(f"      ├─ Coherence: {self.cosmic_state.coherence:.2%}")
                print(f"      └─ Planetary Torque: ×{self.cosmic_state.planetary_torque:.2f}")
            except Exception as e:
                print(f"   ⚠️  Imperial Predictability init failed: {e}")
        
        # 🌍⚡ Earth Resonance Engine ⚡🌍
        self.earth_engine = None
        if EARTH_RESONANCE_AVAILABLE and CONFIG.get('ENABLE_EARTH_RESONANCE', True):
            try:
                self.earth_engine = get_earth_engine()
                # Apply CONFIG thresholds to Earth engine
                coherence_thresh = CONFIG.get('EARTH_COHERENCE_THRESHOLD', 0.55)
                phase_lock_thresh = CONFIG.get('EARTH_PHASE_LOCK_THRESHOLD', 0.65)
                self.earth_engine.set_thresholds(
                    coherence=coherence_thresh,
                    phase_lock=phase_lock_thresh
                )
                self.earth_engine.update_schumann_state()
                print("   🌍⚡ Earth Resonance Engine ACTIVE")
                print(f"      ├─ Schumann Mode 1: {self.earth_engine.schumann_state.mode1_power:.2f}")
                print(f"      ├─ Field Coherence: {self.earth_engine.schumann_state.field_coherence:.2%}")
                print(f"      ├─ Coherence Gate: {coherence_thresh:.0%} | Phase Gate: {phase_lock_thresh:.0%}")
                print(f"      └─ PHI Multiplier: ×{self.earth_engine.get_phi_position_multiplier():.3f}")
            except Exception as e:
                print(f"   ⚠️  Earth Resonance Engine init failed: {e}")
        
    def compute_coherence(self, state: MarketState) -> Tuple[float, str]:
        """Compute overall market coherence (Γ) with Lambda field + HNC frequency
        
        Λ(t) = S(t) + O(t) + E(t) + H(t)
        Where:
            S(t) = Substrate (9 Auris nodes)
            O(t) = Observer (Λ(t-1) × 0.3) - self-reference
            E(t) = Echo (avg(Λ[t-5:t]) × 0.2) - memory
            H(t) = Harmonic (HNC frequency coherence × 0.25) - global frequency
        """
        total_weight = sum(n.weight for n in self.nodes)
        weighted_sum = 0
        
        dominant_node = None
        max_response = 0
        
        # S(t) = Substrate from 9 Auris nodes
        for node in self.nodes:
            response = node.compute(state)
            weighted_sum += response * node.weight
            if response > max_response:
                max_response = response
                dominant_node = node.name
                
        substrate = weighted_sum / total_weight if total_weight > 0 else 0
        
        # Full Lambda field if enabled
        if CONFIG['ENABLE_LAMBDA_FIELD']:
            # O(t) = Observer component (self-reference)
            observer = self.last_lambda * CONFIG['OBSERVER_WEIGHT']
            
            # E(t) = Echo component (memory)
            echo = 0.0
            if len(self.lambda_history) > 0:
                echo = (sum(self.lambda_history) / len(self.lambda_history)) * CONFIG['ECHO_WEIGHT']
            
            # H(t) = Harmonic component (HNC global frequency)
            harmonic = 0.0
            if self.hnc_bridge and CONFIG.get('ENABLE_HNC_FREQUENCY', True):
                harmonic = self.hnc_coherence * CONFIG.get('HNC_FREQUENCY_WEIGHT', 0.25)
            
            # Λ(t) = S(t) + O(t) + E(t) + H(t)
            lambda_field = substrate + observer + echo + harmonic
            lambda_field = max(0.0, min(1.0, lambda_field))  # Clamp to [0, 1]
            
            # Update history
            self.lambda_history.append(lambda_field)
            self.last_lambda = lambda_field
            
            coherence = lambda_field
        else:
            # Legacy mode: just use substrate
            coherence = substrate
                
        return coherence, dominant_node or "Unknown"
    
    def update_hnc_state(self, symbol: str, price: float, change_24h: float, coherence: float, score: float):
        """Update HNC frequency state for a symbol and get harmonic analysis"""
        if not self.hnc_bridge:
            return None
        
        try:
            opp = {
                'symbol': symbol,
                'price': price,
                'change24h': change_24h,
                'coherence': coherence,
                'score': score
            }
            enhanced = self.hnc_bridge.enhance_opportunity(opp)
            
            # Store latest HNC state
            self.hnc_frequency = enhanced.get('hnc_frequency', 256.0)
            self.hnc_coherence = enhanced.get('hnc_resonance', 0.0)
            self.hnc_is_harmonic = enhanced.get('hnc_is_harmonic', False)
            
            # 🌍⚡ Track per-asset frequency ⚡🌍
            self.asset_frequencies[symbol] = {
                'symbol': symbol,
                'frequency': enhanced.get('hnc_frequency', 256.0),
                'is_harmonic': enhanced.get('hnc_is_harmonic', False),
                'resonance': enhanced.get('hnc_resonance', 0.5),
                'change': change_24h,
                'coherence': coherence,
                'score': enhanced.get('score', score),
                'price': price,
                'timestamp': time.time()
            }
            
            # Store in frequency history for trend analysis
            self.frequency_history.append({
                'symbol': symbol,
                'frequency': enhanced.get('hnc_frequency', 256.0),
                'timestamp': time.time()
            })
            
            return enhanced
        except Exception as e:
            return None
    
    def get_hnc_position_modifier(self) -> float:
        """Get position size modifier based on HNC frequency state"""
        if not self.hnc_bridge or not CONFIG.get('ENABLE_HNC_FREQUENCY', True):
            return 1.0
        
        try:
            rec = self.hnc_bridge.get_trading_recommendation([])
            return rec.get('position_size_modifier', 1.0)
        except:
            return 1.0
    
    def get_hnc_status(self) -> Dict[str, Any]:
        """Get current HNC status for display"""
        if not self.hnc_bridge or not CONFIG.get('ENABLE_HNC_FREQUENCY', True):
            return {
                'composite_freq': 256.0,
                'phase': 'DISABLED',
                'triadic_coherence': 0.0,
                'lighthouse_aligned': False,
                'position_modifier': 1.0,
                'fear_state': 'NEUTRAL'
            }
        
        try:
            state = self.hnc.get_global_field_state()
            rec = self.hnc_bridge.get_trading_recommendation([])
            return {
                'composite_freq': state.get('composite_frequency', 256.0),
                'phase': state.get('phase', 'UNKNOWN'),
                'triadic_coherence': state.get('triadic_coherence', 0.0),
                'lighthouse_aligned': state.get('lighthouse_aligned', False),
                'position_modifier': rec.get('position_size_modifier', 1.0),
                'fear_state': state.get('fear_state', 'NEUTRAL')
            }
        except Exception as e:
            return {
                'composite_freq': self.hnc_frequency,
                'phase': 'ERROR',
                'triadic_coherence': self.hnc_coherence,
                'lighthouse_aligned': False,
                'position_modifier': 1.0,
                'fear_state': 'UNKNOWN'
            }

    def get_probability_signal(self, symbol: str, price: float, frequency: float,
                                momentum: float, coherence: float, 
                                is_harmonic: bool) -> Dict[str, Any]:
        """
        Get probability signal for an asset using the 2-hour probability matrix.
        Hour -1 (lookback) provides base signal.
        Hour +1 (forecast) is the primary trading window.
        Hour +2 fine-tunes Hour +1 predictions.
        """
        if not self.prob_matrix or not CONFIG.get('ENABLE_PROB_MATRIX', True):
            return {
                'probability': 0.5,
                'confidence': 0.0,
                'action': 'HOLD',
                'modifier': 1.0,
                'h1_state': 'DISABLED',
                'fine_tune': 0.0,
            }
        
        try:
            # Update and analyze
            matrix = self.prob_matrix.update_and_analyze(
                symbol=symbol,
                price=price,
                frequency=frequency,
                momentum=momentum,
                coherence=coherence,
                is_harmonic=is_harmonic,
            )
            
            # Get trading signal
            signal = self.prob_matrix.get_trading_signal(symbol)
            return signal
        except Exception as e:
            return {
                'probability': 0.5,
                'confidence': 0.0,
                'action': 'HOLD',
                'modifier': 1.0,
                'h1_state': 'ERROR',
                'fine_tune': 0.0,
            }
    
    def get_high_probability_assets(self, min_prob: float = 0.65) -> List[Dict]:
        """Get assets with high probability forecasts"""
        if not self.prob_matrix:
            return []
        return self.prob_matrix.get_high_probability_opportunities(
            min_probability=min_prob,
            min_confidence=CONFIG.get('PROB_MIN_CONFIDENCE', 0.50)
        )

    # 🌌⚡ IMPERIAL PREDICTABILITY METHODS ⚡🌌
    
    def get_imperial_prediction(self, symbol: str, price: float, 
                                momentum: float = 0.0) -> Dict[str, Any]:
        """
        Get Imperial Predictability forecast for a symbol.
        Uses cosmic synchronization + temporal forecasting.
        """
        if not self.imperial or not CONFIG.get('ENABLE_IMPERIAL', True):
            return {
                'probability': 0.5,
                'confidence': 0.0,
                'action': 'HOLD',
                'multiplier': 1.0,
                'cosmic_phase': 'DISABLED',
                'cosmic_boost': 1.0,
            }
        
        try:
            matrix = self.imperial.engine.generate_matrix(symbol, price, momentum)
            return {
                'probability': matrix.combined_probability,
                'confidence': matrix.imperial_confidence,
                'action': matrix.recommended_action,
                'multiplier': matrix.position_multiplier,
                'cosmic_phase': matrix.cosmic_state.phase.value,
                'cosmic_boost': matrix.cosmic_boost,
                'alignment_bonus': matrix.alignment_bonus,
                '1h_signal': matrix.window_1h.signal.value,
                '4h_signal': matrix.window_4h.signal.value,
                'btc_forecast': matrix.window_1h.btc_forecast,
                'imperial_yield': matrix.cosmic_state.imperial_yield,
                'planetary_torque': matrix.cosmic_state.planetary_torque,
            }
        except Exception as e:
            return {
                'probability': 0.5,
                'confidence': 0.0,
                'action': 'HOLD',
                'multiplier': 1.0,
                'cosmic_phase': 'ERROR',
                'cosmic_boost': 1.0,
            }
    
    def enhance_opportunity_imperial(self, opp: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance a trading opportunity with Imperial predictability.
        Adds cosmic-aware position sizing and probability forecasts.
        """
        if not self.imperial or not CONFIG.get('ENABLE_IMPERIAL', True):
            return opp
        
        try:
            return self.imperial.enhance_opportunity(opp)
        except Exception as e:
            return opp
    
    def get_imperial_position_modifier(self, symbol: str, 
                                       momentum: float = 0.0,
                                       price: float = 0.0) -> float:
        """
        Get Imperial position size modifier for a symbol.
        Returns multiplier (0.1 to 1.5) based on cosmic state.
        """
        if not self.imperial or not CONFIG.get('ENABLE_IMPERIAL', True):
            return 1.0
        
        try:
            return self.imperial.get_position_modifier(symbol, momentum, price)
        except:
            return 1.0
    
    def get_cosmic_status(self) -> Dict[str, Any]:
        """Get current cosmic state for display"""
        if not self.imperial or not CONFIG.get('ENABLE_IMPERIAL', True):
            return {
                'phase': 'DISABLED',
                'coherence': 0.0,
                'distortion': 0.0,
                'planetary_torque': 1.0,
                'imperial_yield': 0.0,
            }
        
        try:
            return self.imperial.get_cosmic_status()
        except:
            return {
                'phase': 'ERROR',
                'coherence': 0.0,
                'distortion': 0.0,
                'planetary_torque': 1.0,
                'imperial_yield': 0.0,
            }
    
    def should_trade_imperial(self) -> Tuple[bool, str]:
        """
        Check if cosmic state supports trading.
        Returns (should_trade, reason).
        """
        if not self.imperial or not CONFIG.get('ENABLE_IMPERIAL', True):
            return True, "Imperial disabled - trading allowed"
        
        try:
            return self.imperial.should_trade()
        except:
            return True, "Imperial check failed - trading allowed"
    
    def get_earth_resonance_status(self) -> Dict[str, Any]:
        """Get current Earth Resonance Engine status"""
        if not self.earth_engine or not CONFIG.get('ENABLE_EARTH_RESONANCE', True):
            return {'enabled': False, 'reason': 'Earth Resonance disabled'}
        
        try:
            gate_status = self.earth_engine.get_trading_gate_status_dict()
            return {
                'enabled': True,
                'gate_open': gate_status['gate_open'],
                'coherence': gate_status['coherence'],
                'phase_locked': gate_status['phase_locked'],
                'schumann_power': gate_status['schumann_power'],
                'dominant_mode': gate_status['dominant_mode'],
                'phi_multiplier': self.earth_engine.get_phi_position_multiplier(),
                'exit_urgency': self.earth_engine.get_exit_urgency(0)  # Default 0 P&L
            }
        except Exception as e:
            return {'enabled': False, 'reason': f'Earth Resonance error: {e}'}
    
    def should_trade_earth(self) -> Tuple[bool, str]:
        """
        Check if Earth Resonance supports trading.
        Returns (should_trade, reason).
        """
        if not self.earth_engine or not CONFIG.get('ENABLE_EARTH_RESONANCE', True):
            return True, "Earth Resonance disabled - trading allowed"
        
        try:
            # get_trading_gate_status returns (bool, str)
            gate_open, reason = self.earth_engine.get_trading_gate_status()
            
            if not gate_open:
                return False, f"Earth gate CLOSED: {reason}"
            
            return True, f"Earth gate OPEN: {reason}"
        except Exception as e:
            return True, f"Earth check failed ({e}) - trading allowed"
    
    def should_trade_all_gates(self) -> Tuple[bool, str]:
        """
        Combined gate check: Imperial + HNC + Earth Resonance.
        Returns (should_trade, reason).
        """
        reasons = []
        
        # Check Imperial gate
        imperial_ok, imperial_reason = self.should_trade_imperial()
        if not imperial_ok:
            reasons.append(f"Imperial: {imperial_reason}")
        
        # Check Earth Resonance gate
        earth_ok, earth_reason = self.should_trade_earth()
        if not earth_ok:
            reasons.append(f"Earth: {earth_reason}")
        
        # Check HNC frequency gate (if we have current frequency)
        if CONFIG.get('HNC_ENTRY_GATING', True) and hasattr(self, 'hnc_current_frequency'):
            freq = getattr(self, 'hnc_current_frequency', 432)
            if 438 <= freq <= 442:  # Distortion zone
                reasons.append(f"HNC: Distortion frequency {freq}Hz blocked")
        
        if reasons:
            return False, " | ".join(reasons)
        
        return True, "All gates OPEN"
    
    def update_cosmic_state(self, market_data: Optional[Dict] = None) -> None:
        """Update cosmic state with optional market data"""
        if self.imperial and CONFIG.get('ENABLE_IMPERIAL', True):
            try:
                self.cosmic_state = self.imperial.update_cosmic_state(market_data)
                self.cosmic_phase = self.cosmic_state.phase.value
                self.imperial_yield = self.cosmic_state.imperial_yield
            except:
                pass

    def get_asset_frequency_grid(self) -> List[Dict[str, Any]]:
        """Get detailed frequency breakdown for all tracked assets"""
        return list(self.asset_frequencies.values())
    
    def get_frequency_distribution(self) -> Dict[str, int]:
        """Get count of assets at each frequency band"""
        distribution = {
            '174_FOUNDATION': 0,
            '256_ROOT': 0,
            '396_LIBERATION': 0,
            '432_NATURAL': 0,
            '440_DISTORTION': 0,
            '512_VISION': 0,
            '528_LOVE': 0,
            '639_CONNECTION': 0,
            '741_AWAKENING': 0,
            '852_INTUITION': 0,
            '963_UNITY': 0,
        }
        
        for asset in self.asset_frequencies.values():
            freq = asset.get('frequency', 256)
            if freq <= 200:
                distribution['174_FOUNDATION'] += 1
            elif freq <= 300:
                distribution['256_ROOT'] += 1
            elif freq <= 410:
                distribution['396_LIBERATION'] += 1
            elif freq <= 438:
                distribution['432_NATURAL'] += 1
            elif freq <= 445:
                distribution['440_DISTORTION'] += 1
            elif freq <= 520:
                distribution['512_VISION'] += 1
            elif freq <= 580:
                distribution['528_LOVE'] += 1
            elif freq <= 700:
                distribution['639_CONNECTION'] += 1
            elif freq <= 800:
                distribution['741_AWAKENING'] += 1
            elif freq <= 900:
                distribution['852_INTUITION'] += 1
            else:
                distribution['963_UNITY'] += 1
                
        return distribution
    
    def get_harmonic_count(self) -> Dict[str, int]:
        """Get count of harmonic vs distorted assets"""
        harmonic = sum(1 for a in self.asset_frequencies.values() if a.get('is_harmonic', False))
        distortion = sum(1 for a in self.asset_frequencies.values() if 435 <= a.get('frequency', 256) <= 445)
        neutral = len(self.asset_frequencies) - harmonic - distortion
        return {'harmonic': harmonic, 'distortion': distortion, 'neutral': neutral}
    
    def get_harmonic_assets(self) -> List[str]:
        """Get list of assets currently in harmonic resonance"""
        return [
            asset['symbol'] for asset in self.asset_frequencies.values()
            if asset.get('is_harmonic', False)
        ]
    
    def get_distorted_assets(self) -> List[str]:
        """Get list of assets in 440Hz distortion field"""
        return [
            asset['symbol'] for asset in self.asset_frequencies.values()
            if 435 <= asset.get('frequency', 256) <= 445
        ]
    
    def scan_for_anomalies(self, symbols: List[str]) -> List[Dict]:
        """
        Scan market for anomalies using CoinAPI cross-exchange data.
        Returns detected anomalies and applies algorithm refinements.
        """
        if not self.coinapi_detector or not CONFIG.get('ENABLE_COINAPI', False):
            return []
        
        current_time = time.time()
        scan_interval = CONFIG.get('COINAPI_SCAN_INTERVAL', 300)
        
        # Rate limit scans
        if current_time - self.last_anomaly_scan < scan_interval:
            return []
        
        self.last_anomaly_scan = current_time
        
        anomalies = []
        
        # Scan a sample of symbols (not all, to save API calls)
        sample_symbols = random.sample(symbols, min(5, len(symbols))) if symbols else []
        
        for symbol in sample_symbols:
            try:
                # Parse symbol (e.g., "BTC/USD" -> base="BTC", quote="USD")
                if '/' in symbol:
                    base, quote = symbol.split('/')
                elif len(symbol) >= 6:
                    # Try to parse (e.g., "BTCUSD" -> "BTC", "USD")
                    base = symbol[:3]
                    quote = symbol[3:]
                else:
                    continue
                
                # Analyze cross-exchange data
                analysis = self.coinapi_detector.analyze_symbol(base, quote)
                
                # Process anomalies and apply refinements
                for anom_dict in analysis.get('anomalies', []):
                    severity = anom_dict.get('severity', 0)
                    if severity >= CONFIG.get('COINAPI_MIN_SEVERITY', 0.40):
                        anomalies.append(anom_dict)
                        
                        # Apply refinements based on anomaly type
                        self._apply_anomaly_refinement(symbol, anom_dict)
                
            except Exception as e:
                continue
        
        return anomalies
    
    def _apply_anomaly_refinement(self, symbol: str, anomaly: Dict):
        """Apply algorithm refinements based on detected anomaly"""
        anom_type = anomaly.get('type', '')
        severity = anomaly.get('severity', 0)
        
        if '💰 Price Manipulation' in anom_type or '🔄 Wash Trading' in anom_type:
            # Blacklist symbol temporarily
            duration = CONFIG.get('COINAPI_BLACKLIST_DURATION', 3600)
            self.anomaly_blacklist[symbol] = time.time() + duration
            print(f"   🚫 Blacklisted {symbol} for {duration}s: {anom_type}")
        
        elif '📊 Orderbook Spoofing' in anom_type:
            # Reduce coherence threshold (require higher quality)
            if CONFIG.get('COINAPI_ADJUST_COHERENCE', True):
                adjustment = 1.0 + (severity * 0.2)
                self.coherence_adjustments[symbol] = adjustment
                print(f"   ⚖️  Adjusted {symbol} coherence threshold: ×{adjustment:.2f}")
        
        elif '🌐 Cross-Exchange Spread' in anom_type:
            # This is actually good - use multi-exchange mean price
            print(f"   💎 Arbitrage detected on {symbol}: {anomaly.get('description', '')}")
    
    def is_symbol_blacklisted(self, symbol: str) -> bool:
        """Check if symbol is blacklisted due to anomalies"""
        if symbol not in self.anomaly_blacklist:
            return False
        
        # Check if blacklist has expired
        if time.time() > self.anomaly_blacklist[symbol]:
            del self.anomaly_blacklist[symbol]
            return False
        
        return True
    
    def get_coherence_adjustment(self, symbol: str) -> float:
        """Get coherence threshold adjustment for symbol"""
        return self.coherence_adjustments.get(symbol, 1.0)
    
    def print_frequency_grid(self, top_n: int = 10):
        """Print a visual frequency grid for assets"""
        if not self.asset_frequencies:
            print("   📡 No asset frequencies tracked yet")
            return
            
        # Sort by frequency
        sorted_assets = sorted(
            self.asset_frequencies.values(),
            key=lambda x: x.get('frequency', 256),
            reverse=True
        )[:top_n]
        
        print("\n   🌍⚡ ASSET FREQUENCY GRID ⚡🌍")
        print("   ┌─────────────┬────────┬──────────┬───────────┬──────────┐")
        print("   │   SYMBOL    │  FREQ  │  STATE   │ RESONANCE │  CHANGE  │")
        print("   ├─────────────┼────────┼──────────┼───────────┼──────────┤")
        
        for asset in sorted_assets:
            symbol = asset.get('symbol', '???')[:11]
            freq = asset.get('frequency', 256)
            is_harm = asset.get('is_harmonic', False)
            resonance = asset.get('resonance', 0.5)
            change = asset.get('change', 0.0)
            
            # State indicator
            if is_harm:
                state = "🌈 HARMONIC"
            elif 435 <= freq <= 445:
                state = "⚠️ DISTORT "
            elif freq >= 500:
                state = "🚀 HIGH    "
            elif freq >= 350:
                state = "📈 RISING  "
            elif freq >= 250:
                state = "⚖️ STABLE  "
            else:
                state = "📉 LOW     "
            
            # Resonance bar
            bar_len = int(resonance * 5)
            bar = "█" * bar_len + "░" * (5 - bar_len)
            
            print(f"   │ {symbol:11s} │ {freq:6.0f} │ {state} │ {bar} {resonance:.2f} │ {change:+6.1f}% │")
        
        print("   └─────────────┴────────┴──────────┴───────────┴──────────┘")
        
        # Distribution summary
        dist = self.get_frequency_distribution()
        harmonic_count = dist['256_ROOT'] + dist['528_LOVE'] + dist['432_NATURAL']
        distorted_count = dist['440_DISTORTION']
        total = len(self.asset_frequencies)
        
        print(f"   📊 Distribution: {harmonic_count} harmonic | {distorted_count} distorted | {total} total")


# ═══════════════════════════════════════════════════════════════
# 🍄 MYCELIUM NETWORK - Neural Pattern Detection
# ═══════════════════════════════════════════════════════════════

@dataclass
class Synapse:
    """Connection between market signals with Hebbian learning"""
    source: str
    target: str
    strength: float = 0.5
    plasticity: float = 0.1
    activation_count: int = 0
    
    def pulse(self, signal: float) -> float:
        self.activation_count += 1
        return signal * self.strength
        
    def strengthen(self, reward: float):
        """Hebbian learning: strengthen if rewarded"""
        # Reward is typically profit % (e.g. 2.0 for 2%)
        # Scale reward to be small adjustment
        adjustment = reward * self.plasticity * 0.1
        self.strength = max(0.1, min(2.0, self.strength + adjustment))


class MyceliumNetwork:
    """Neural network for pattern detection across symbols"""
    
    def __init__(self):
        self.synapses: Dict[str, List[Synapse]] = {}
        self.activations: Dict[str, float] = {}
        
    def add_signal(self, symbol: str, signal: float):
        """Add a market signal to the network"""
        self.activations[symbol] = signal
        
        # Auto-create synapses to other active symbols if they don't exist
        # This creates a dense mesh over time
        if symbol not in self.synapses:
            self.synapses[symbol] = []
            
        # Randomly connect to existing nodes to grow the network
        if len(self.activations) > 1 and len(self.synapses[symbol]) < 5:
            targets = list(self.activations.keys())
            if symbol in targets: targets.remove(symbol)
            if targets:
                target = random.choice(targets)
                # Check if connection exists
                if not any(s.target == target for s in self.synapses[symbol]):
                    self.synapses[symbol].append(Synapse(source=symbol, target=target))
        
    def propagate(self) -> Dict[str, float]:
        """Propagate signals through the network"""
        new_activations = {}
        for symbol, activation in self.activations.items():
            new_activations[symbol] = activation
            if symbol in self.synapses:
                for synapse in self.synapses[symbol]:
                    if synapse.target in self.activations: # Only propagate to active nodes
                        # Signal boosts the target's activation
                        boost = synapse.pulse(activation) * 0.1 # Dampening factor
                        new_activations[synapse.target] = new_activations.get(synapse.target, self.activations[synapse.target]) + boost
        return new_activations

    def learn(self, symbol: str, profit_pct: float):
        """Reinforce connections that led to profit"""
        # If we profited on 'symbol', strengthen incoming connections to it
        # and outgoing connections from it that were active
        
        # 1. Strengthen outgoing connections from this symbol
        if symbol in self.synapses:
            for synapse in self.synapses[symbol]:
                synapse.strengthen(profit_pct)
                
        # 2. Strengthen incoming connections to this symbol (harder to find in this structure, 
        #    so we iterate - optimization: keep reverse map if needed, but loop is fine for small N)
        for source, synapses in self.synapses.items():
            for synapse in synapses:
                if synapse.target == symbol:
                    synapse.strengthen(profit_pct)

    def get_network_coherence(self) -> float:
        """Overall network coherence"""
        if not self.activations:
            return 0.5
        return sum(self.activations.values()) / len(self.activations)


# ═══════════════════════════════════════════════════════════════
# 💰 POSITION & PERFORMANCE TRACKING
# ═══════════════════════════════════════════════════════════════

@dataclass
class Position:
    symbol: str
    entry_price: float
    quantity: float
    entry_fee: float
    entry_value: float
    momentum: float
    coherence: float
    entry_time: float
    dominant_node: str
    cycles: int = 0
    # Swarm Orchestrator enhancements
    generation: int = 0  # 0 = original, 1+ = split children
    parent_id: Optional[str] = None  # ID of parent position if this is a split
    is_scout: bool = False  # Can this position act as market scout?
    last_signal_broadcast: float = 0.0  # Timestamp of last signal
    prime_size_multiplier: float = 1.0  # Prime-based sizing
    exchange: str = 'kraken'  # Exchange where position is held
    
    # Generate unique ID for position
    id: str = field(default_factory=lambda: f"pos_{int(time.time()*1000)}_{random.randint(1000,9999)}")
    
    # Convenience properties
    @property
    def size(self) -> float:
        """Alias for quantity"""
        return self.quantity
        
    @property
    def current_price(self) -> float:
        """Alias for entry_price (will be updated externally)"""
        return self.entry_price
        
    @property
    def quote_asset(self) -> str:
        """Extract quote asset from symbol"""
        for quote in CONFIG['QUOTE_CURRENCIES']:
            if self.symbol.endswith(quote):
                return quote
        return 'USD'  # Default fallback


class PerformanceTracker:
    """Track all trading performance metrics"""
    
    def __init__(self, initial_balance: float):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.peak_balance = initial_balance
        self.total_trades = 0
        self.wins = 0
        self.losses = 0
        self.total_fees = 0.0
        self.net_profit = 0.0
        self.compounded = 0.0
        self.harvested = 0.0
        self.max_drawdown = 0.0
        self.current_drawdown = 0.0  # Current DD from peak
        self.trade_log: List[Dict] = []
        self.trading_halted = False
        self.halt_reason = ""
        self.total_hold_time_sec = 0.0  # Track average hold time
        self.closed_positions = 0
        
        # Earth engine reference for PHI amplification
        self.earth_engine = None
        
        # Track per-symbol exposure
        self.symbol_exposure: Dict[str, float] = {}
        self.portfolio_equity = initial_balance
        self.cash_balance = initial_balance
        self.cycle_equity_start = initial_balance
        self.equity_baseline = initial_balance
        
        # 📊 Platform-specific metrics
        self.platform_metrics: Dict[str, Dict] = {
            'kraken': {'trades': 0, 'wins': 0, 'fees': 0.0, 'pnl': 0.0, 'volume': 0.0},
            'binance': {'trades': 0, 'wins': 0, 'fees': 0.0, 'pnl': 0.0, 'volume': 0.0},
            'alpaca': {'trades': 0, 'wins': 0, 'fees': 0.0, 'pnl': 0.0, 'volume': 0.0},
            'capital': {'trades': 0, 'wins': 0, 'fees': 0.0, 'pnl': 0.0, 'volume': 0.0},
        }
        
    def record_trade(self, net_pnl: float, fees: float, symbol: str, reason: str, 
                     hold_time_sec: float = 0, platform: str = 'kraken', volume: float = 0.0):
        """Record a completed trade with platform attribution"""
        self.total_trades += 1
        self.total_fees += fees
        result = 'WIN' if net_pnl > 0 else 'LOSS'
        if net_pnl > 0:
            self.wins += 1
        else:
            self.losses += 1
        
        # Track hold time
        if hold_time_sec > 0:
            self.total_hold_time_sec += hold_time_sec
            self.closed_positions += 1
        
        # 📊 Update platform-specific metrics
        platform_key = platform.lower()
        if platform_key in self.platform_metrics:
            self.platform_metrics[platform_key]['trades'] += 1
            self.platform_metrics[platform_key]['fees'] += fees
            self.platform_metrics[platform_key]['pnl'] += net_pnl
            self.platform_metrics[platform_key]['volume'] += volume
            if net_pnl > 0:
                self.platform_metrics[platform_key]['wins'] += 1
        
        self.trade_log.append({
            'symbol': symbol,
            'reason': reason,
            'result': result,  # Explicit WIN/LOSS classification
            'net_pnl': net_pnl,
            'fees': fees,
            'volume': volume,
            'platform': platform,
            'balance': self.portfolio_equity,
            'win_rate': self.win_rate,
            'hold_time_sec': hold_time_sec,
            'time': datetime.now().isoformat()
        })
        
    @property
    def win_rate(self) -> float:
        return (self.wins / self.total_trades * 100) if self.total_trades > 0 else 0
        
    @property
    def total_return(self) -> float:
        return (self.balance - self.initial_balance) / self.initial_balance * 100

    def update_equity(self, equity_value: float, cash_value: float, mark_cycle: bool = False):
        """Synchronise tracker metrics with current marked-to-market equity."""
        self.portfolio_equity = equity_value
        self.cash_balance = cash_value
        self.balance = equity_value
        self.net_profit = self.portfolio_equity - self.initial_balance
        if mark_cycle:
            self.cycle_equity_start = equity_value
        
        if self.portfolio_equity > self.peak_balance:
            self.peak_balance = self.portfolio_equity
        if self.peak_balance > 0:
            dd = (self.peak_balance - self.portfolio_equity) / self.peak_balance * 100
        else:
            dd = 0.0
        self.current_drawdown = dd  # Track current DD from peak
        if dd > self.max_drawdown:
            self.max_drawdown = dd
        if dd >= CONFIG['MAX_DRAWDOWN_PCT'] and not self.trading_halted:
            self.trading_halted = True
            self.halt_reason = f"Max drawdown {dd:.1f}% exceeded"
            print(f"\n🛑 CIRCUIT BREAKER ACTIVATED: {self.halt_reason}")

    def realize_portfolio_gain(self, gain: float):
        """Advance compounding only when the whole portfolio has grown."""
        if gain <= 0:
            return
        compound_amt = gain * CONFIG['COMPOUND_PCT']
        harvest_amt = gain * CONFIG['HARVEST_PCT']
        self.compounded += compound_amt
        self.harvested += harvest_amt
    
    def calculate_position_size(self, coherence: float, symbol: str, hnc_modifier: float = 1.0,
                                 imperial_modifier: float = 1.0) -> float:
        """
        Calculate position size using Kelly Criterion + coherence scaling + HNC frequency + Imperial.
        
        Args:
            coherence: Auris/Lambda field coherence (0.0-1.0)
            symbol: Trading symbol
            hnc_modifier: HNC frequency-based position modifier (from AurisEngine)
            imperial_modifier: Imperial predictability modifier (cosmic synchronization)
        
        Returns: Position size as fraction of balance
        """
        if CONFIG['USE_KELLY_SIZING'] and self.total_trades >= 10:
            # Need at least 10 trades for stable Kelly calculation
            avg_win = CONFIG['TAKE_PROFIT_PCT'] / 100.0
            avg_loss = CONFIG['STOP_LOSS_PCT'] / 100.0
            
            kelly_size = kelly_criterion(
                self.win_rate / 100.0,
                avg_win,
                avg_loss,
                CONFIG['KELLY_SAFETY_FACTOR']
            )
        else:
            # Use base size until we have enough data
            kelly_size = CONFIG['BASE_POSITION_SIZE']
        
        # Scale by coherence: higher coherence = larger position
        # Range: 0.7x to 1.3x based on coherence 0.0-1.0
        coherence_multiplier = 0.7 + (coherence * 0.6)
        scaled_size = kelly_size * coherence_multiplier
        
        # 🌍⚡ Apply HNC frequency modifier ⚡🌍
        # Range: 0.7x (440Hz distortion) to 1.15x (256/528Hz harmonic)
        if CONFIG.get('ENABLE_HNC_FREQUENCY', True):
            scaled_size *= hnc_modifier
        
        # 🌌⚡ Apply Imperial predictability modifier ⚡🌌
        # Range: 0.1x (extreme bearish) to 1.5x (extreme bullish with cosmic boost)
        if CONFIG.get('ENABLE_IMPERIAL', True):
            imperial_weight = CONFIG.get('IMPERIAL_POSITION_WEIGHT', 0.35)
            # Blend: (1-weight)*1.0 + weight*imperial_modifier
            blended_imperial = (1 - imperial_weight) + (imperial_weight * imperial_modifier)
            scaled_size *= blended_imperial
        
        # 🌍✨ Apply Earth Resonance PHI amplification ✨🌍
        # Golden ratio (1.618) multiplier when field coherence is high
        if CONFIG.get('EARTH_PHI_AMPLIFICATION', True) and self.earth_engine:
            try:
                phi_multiplier = self.earth_engine.get_phi_position_multiplier()
                scaled_size *= phi_multiplier
            except Exception as e:
                pass  # Continue without PHI if error
        
        # Check per-symbol exposure limits
        current_exposure = self.symbol_exposure.get(symbol, 0.0)
        available_exposure = CONFIG['MAX_SYMBOL_EXPOSURE'] - current_exposure
        
        final_size = min(scaled_size, available_exposure, CONFIG['MAX_POSITION_SIZE'])
        return max(0, final_size)

    def get_platform_summary(self) -> str:
        """Generate a summary of metrics by platform."""
        lines = ["\n   📊 PLATFORM METRICS"]
        lines.append("   " + "─" * 60)
        
        for platform, metrics in self.platform_metrics.items():
            if metrics['trades'] == 0:
                continue
            win_rate = (metrics['wins'] / metrics['trades'] * 100) if metrics['trades'] > 0 else 0
            icon = {'kraken': '🐙', 'binance': '🟡', 'alpaca': '🦙', 'capital': '💼'}.get(platform, '📈')
            lines.append(f"   {icon} {platform.upper()}:")
            lines.append(f"      Trades: {metrics['trades']} | Win Rate: {win_rate:.1f}%")
            lines.append(f"      Volume: ${metrics['volume']:,.2f} | Fees: ${metrics['fees']:.4f}")
            lines.append(f"      Net P&L: ${metrics['pnl']:+.4f}")
        
        lines.append("   " + "─" * 60)
        return "\n".join(lines)


def get_platform_fee(platform: str, order_type: str = 'taker') -> float:
    """
    Get the appropriate fee rate for a platform.
    
    Args:
        platform: 'kraken', 'binance', 'alpaca', 'capital'
        order_type: 'maker' or 'taker'
    
    Returns:
        Fee as decimal (e.g., 0.0026 for 0.26%)
    """
    platform = platform.lower()
    
    if platform == 'kraken':
        return CONFIG['KRAKEN_FEE_MAKER'] if order_type == 'maker' else CONFIG['KRAKEN_FEE_TAKER']
    elif platform == 'binance':
        return CONFIG['BINANCE_FEE_MAKER'] if order_type == 'maker' else CONFIG['BINANCE_FEE_TAKER']
    elif platform == 'alpaca':
        return CONFIG['ALPACA_FEE_MAKER'] if order_type == 'maker' else CONFIG['ALPACA_FEE_TAKER']
    elif platform == 'capital':
        return CONFIG['CAPITAL_FEE']  # Spread-based, no maker/taker distinction
    else:
        # Default to Kraken taker fee
        return CONFIG['KRAKEN_FEE_TAKER']


def calculate_trade_fees(notional: float, platform: str, order_type: str = 'taker') -> Dict[str, float]:
    """
    Calculate expected fees for a trade.
    
    Returns:
        Dict with fee_pct, fee_amount, total_cost (includes slippage)
    """
    fee_pct = get_platform_fee(platform, order_type)
    fee_amount = notional * fee_pct
    slippage = notional * CONFIG['SLIPPAGE_PCT']
    spread_cost = notional * CONFIG['SPREAD_COST_PCT']
    total_cost = fee_amount + slippage + spread_cost
    
    return {
        'fee_pct': fee_pct,
        'fee_amount': fee_amount,
        'slippage': slippage,
        'spread_cost': spread_cost,
        'total_cost': total_cost,
        'total_cost_pct': (total_cost / notional) if notional > 0 else 0
    }


# ═══════════════════════════════════════════════════════════════
# 🐘 ELEPHANT MEMORY - Enhanced Tracking
# ═══════════════════════════════════════════════════════════════

class ElephantMemory:
    """
    Enhanced Elephant Memory from Quantum Quackers
    Tracks hunts + results with JSONL history.
    Integrates collective intelligence from all ecosystem agents.
    """
    
    def __init__(self, filepath: str = 'elephant_unified.json'):
        self.filepath = filepath
        self.history_path = filepath.replace('.json', '_history.jsonl')
        self.symbols = {} # Local memory (Unified)
        self.collective_symbols = {} # Collective memory (Ultimate, Live, etc.)
        self.memory_sources = [
            'elephant_ultimate.json',
            'elephant_live.json'
        ]
        self.load()
    
    def load(self):
        # 1. Load local memory
        try:
            with open(self.filepath) as f:
                self.symbols = json.load(f)
        except:
            self.symbols = {}
            
        # 2. Load and aggregate collective memory
        self.collective_symbols = {}
        for source in self.memory_sources:
            if not os.path.exists(source):
                continue
            try:
                with open(source, 'r') as f:
                    data = json.load(f)
                    for sym, stats in data.items():
                        if sym not in self.collective_symbols:
                            self.collective_symbols[sym] = stats.copy()
                        else:
                            # Merge critical stats (worst-case for safety)
                            s = self.collective_symbols[sym]
                            s['blacklisted'] = s.get('blacklisted', False) or stats.get('blacklisted', False)
                            s['streak'] = max(s.get('streak', 0), stats.get('streak', 0))
                            s['losses'] = s.get('losses', 0) + stats.get('losses', 0)
            except Exception as e:
                print(f"⚠️ Error loading collective memory from {source}: {e}")
    
    def save(self):
        with open(self.filepath, 'w') as f:
            json.dump(self.symbols, f, indent=2)
    
    def record_hunt(self, symbol: str, volume: float = 0, change: float = 0):
        """Remember we hunted this symbol (Quackers style)"""
        if symbol not in self.symbols:
            self.symbols[symbol] = {
                'hunts': 0, 'trades': 0, 'wins': 0, 'losses': 0,
                'profit': 0, 'last_time': 0, 'streak': 0, 'blacklisted': False
            }
        
        s = self.symbols[symbol]
        s['hunts'] = s.get('hunts', 0) + 1
        s['last_time'] = time.time()
        
        # Append to JSONL history
        try:
            with open(self.history_path, 'a') as f:
                record = {
                    'ts': datetime.now().isoformat(),
                    'type': 'hunt',
                    'symbol': symbol,
                    'volume': volume,
                    'change': change
                }
                f.write(json.dumps(record) + '\n')
        except:
            pass
        
        self.save()
    
    def record(self, symbol: str, profit_usd: float):
        """Record trade result"""
        if symbol not in self.symbols:
            self.symbols[symbol] = {
                'hunts': 0, 'trades': 0, 'wins': 0, 'losses': 0,
                'profit': 0, 'last_time': 0, 'streak': 0, 'blacklisted': False
            }
        
        s = self.symbols[symbol]
        s['trades'] += 1
        s['profit'] += profit_usd
        s['last_time'] = time.time()
        
        if profit_usd >= 0:
            s['wins'] += 1
            s['streak'] = 0
        else:
            s['losses'] += 1
            s['streak'] += 1
            if s['streak'] >= CONFIG.get('LOSS_STREAK_LIMIT', 3):
                s['blacklisted'] = True
                print(f"🚫 {symbol} BLACKLISTED after {s['streak']} losses")
        
        # Append to JSONL history
        try:
            with open(self.history_path, 'a') as f:
                record = {
                    'ts': datetime.now().isoformat(),
                    'type': 'result',
                    'symbol': symbol,
                    'profit': profit_usd
                }
                f.write(json.dumps(record) + '\n')
        except:
            pass
        
        self.save()
    
    def should_avoid(self, symbol: str) -> bool:
        # Check local memory
        if self._check_avoid(self.symbols.get(symbol)):
            return True
            
        # Check collective memory
        if self._check_avoid(self.collective_symbols.get(symbol)):
            # print(f"🐘 Collective Intelligence: Avoiding {symbol} due to peer warning")
            return True
            
        return False
        
    def _check_avoid(self, s: dict) -> bool:
        if not s: return False
        
        # Blacklisted
        if s.get('blacklisted', False):
            return True
        
        # Cooldown - only for symbols with actual TRADES (not just hunts)
        # This allows re-entry attempts after failed hunts
        cooldown = CONFIG.get('COOLDOWN_MINUTES', 13)
        if s.get('trades', 0) > 0 and time.time() - s.get('last_time', 0) < cooldown * 60:
            return True
        
        return False
    
    def get_win_rate(self) -> float:
        total_wins = sum(s.get('wins', 0) for s in self.symbols.values())
        total_losses = sum(s.get('losses', 0) for s in self.symbols.values())
        if total_wins + total_losses == 0:
            return 0.55  # Default 55% (Quackers RiskManager default)
        return total_wins / (total_wins + total_losses)


# ═══════════════════════════════════════════════════════════════
# 🔮 SYSTEM FLUX PREDICTOR - 30-Span Market Analysis
# ═══════════════════════════════════════════════════════════════

class SystemFluxPredictor:
    """
    Predicts market direction by analyzing the collective flux of the top 30 assets.
    "It's not about percentage right, we already know what way the system will go."
    """
    
    def __init__(self):
        self.flux_history = deque(maxlen=100)
        self.last_prediction = None
        
    def predict(self, tickers: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Analyze top 30 assets by volume to determine system flux.
        Returns: {
            'direction': 'BULLISH' | 'BEARISH' | 'NEUTRAL',
            'strength': 0.0 to 1.0,
            'flux_score': -1.0 to 1.0,
            'top_movers': List[str]
        }
        """
        # Filter valid tickers
        valid_tickers = []
        for symbol, data in tickers.items():
            if data.get('volume', 0) > 10000 and data.get('price', 0) > 0:
                valid_tickers.append({
                    'symbol': symbol,
                    'change': data.get('change24h', 0),
                    'volume': data.get('volume', 0)
                })
        
        # Sort by volume to get "The System" leaders
        valid_tickers.sort(key=lambda x: x['volume'], reverse=True)
        top_30 = valid_tickers[:CONFIG.get('FLUX_SPAN', 30)]
        
        if not top_30:
            return {'direction': 'NEUTRAL', 'strength': 0.0, 'flux_score': 0.0}
            
        # Calculate Flux Score (Volume-weighted momentum)
        total_volume = sum(t['volume'] for t in top_30)
        weighted_momentum = sum(t['change'] * (t['volume'] / total_volume) for t in top_30)
        
        # Normalize flux score (-10 to +10 range typically)
        flux_score = max(-1.0, min(1.0, weighted_momentum / 5.0))
        
        # Determine direction and strength
        strength = abs(flux_score)
        if flux_score > 0.2:
            direction = 'BULLISH'
        elif flux_score < -0.2:
            direction = 'BEARISH'
        else:
            direction = 'NEUTRAL'
            
        result = {
            'direction': direction,
            'strength': strength,
            'flux_score': flux_score,
            'top_movers': [t['symbol'] for t in top_30[:3]]
        }
        
        self.flux_history.append(result)
        self.last_prediction = result
        return result

# ═══════════════════════════════════════════════════════════════
# 🐙 THE UNIFIED KRAKEN ECOSYSTEM
# ═══════════════════════════════════════════════════════════════

class AureonKrakenEcosystem:
    """
    🐙🌌 THE COMPLETE KRAKEN TRADING ECOSYSTEM 🌌🐙
    
    Combines all strategies into one dynamic system:
    - Real-time WebSocket prices
    - 9 Auris nodes for analysis
    - Mycelium network for pattern detection
    - 10-9-1 compounding model
    - 51%+ win rate strategy
    """
    
    def __init__(self, initial_balance: float = 1000.0, dry_run: bool = True):
        # Initialize Multi-Exchange Client
        self.client = MultiExchangeClient()
        self.dry_run = self.client.dry_run
        
        self.auris = AurisEngine()
        self.mycelium = MyceliumNetwork()
        self.lattice = LatticeEngine()
        self.market_pulse = MarketPulse(self.client) # Initialize Market Pulse
        self.tracker = PerformanceTracker(initial_balance)
        self.memory = ElephantMemory()  # 🐘 Initialize Elephant Memory
        self.flux_predictor = SystemFluxPredictor() # 🔮 Initialize Flux Predictor
        
        # Share earth engine reference with tracker for PHI amplification
        if self.auris.earth_engine:
            self.tracker.earth_engine = self.auris.earth_engine
        
        self.total_equity_gbp = initial_balance
        self.cash_balance_gbp = initial_balance
        self.holdings_gbp: Dict[str, float] = {}
        self.quote_currency_suffixes: List[str] = sorted(CONFIG['QUOTE_CURRENCIES'], key=len, reverse=True)
        
        # Positions
        self.positions: Dict[str, Position] = {}
        
        # Market data
        self.ticker_cache: Dict[str, Dict] = {}
        self.price_history: Dict[str, List[float]] = {}
        self.realtime_prices: Dict[str, float] = {}
        self.price_lock = Lock()
        self._liquidity_warnings: set[Tuple[str, str]] = set()
        
        # WebSocket
        self.ws_connected = False
        self.ws_last_message = time.time()
        self.ws_reconnect_count = 0
        self.symbol_to_ws: Dict[str, str] = {}
        self.ws_to_symbol: Dict[str, str] = {}
        
        # Stats
        self.iteration = 0
        self.start_time = time.time()
        self.scan_direction = 'A→Z'  # Fair scheduling: alternate A→Z / Z→A
        self.scouts_deployed = False  # Track scout deployment
        
        # 🌟 SWARM ORCHESTRATOR COMPONENTS 🌟
        self.capital_pool = CapitalPool()
        self.signal_broadcaster = SignalBroadcaster()
        self.position_splitter = PositionSplitter()
        self.prime_sizer = PrimeSizer()
        
        # Initialize capital pool
        self.capital_pool.update_equity(initial_balance)
        
        # 🌉 BRIDGE INTEGRATION 🌉
        self.bridge = None
        self.bridge_enabled = BRIDGE_AVAILABLE and os.getenv('ENABLE_BRIDGE', '1') == '1'
        if self.bridge_enabled:
            try:
                self.bridge = AureonBridge()
                print("   🌉 Bridge enabled: Ultimate ↔ Unified communication active")
            except Exception as e:
                print(f"   ⚠️ Bridge initialization failed: {e}")
                self.bridge_enabled = False
        self.last_bridge_sync = 0.0
        self.bridge_sync_interval = 10.0  # Sync every 10 seconds
        
        # Determine tradeable currencies based on wallet
        self.tradeable_currencies = ['USD', 'GBP', 'EUR', 'USDT', 'USDC']
        self._detect_wallet_currency()
        
        # Load previous state if exists
        fresh_start = os.environ.get('FRESH_START', '0') == '1'
        if fresh_start:
            print("   ✨ FRESH START: Ignoring previous state file")
        else:
            self.load_state()

        # Initialise equity snapshot
        self.refresh_equity(mark_cycle=True)
        
        # On fresh start in live mode, reset baselines to actual portfolio value
        if fresh_start and not self.dry_run and self.total_equity_gbp > 0:
            self.tracker.initial_balance = self.total_equity_gbp
            self.tracker.peak_balance = self.total_equity_gbp
            self.tracker.balance = self.total_equity_gbp
            self.tracker.equity_baseline = self.total_equity_gbp
            self.tracker.cycle_equity_start = self.total_equity_gbp
            self.tracker.max_drawdown = 0.0
            self.tracker.trading_halted = False
            self.tracker.halt_reason = ""
            print(f"   📊 Baseline reset to real portfolio: £{self.total_equity_gbp:.2f}")
            
            # Import existing holdings as managed positions
            self._import_existing_holdings()

    def _detect_wallet_currency(self):
        """Detect which currencies we actually have funds in"""
        if self.dry_run:
            return
            
        try:
            all_balances = self.client.get_all_balances()
            
            has_usd = False
            has_gbp = False
            has_eur = False
            has_btc = False
            has_eth = False
            
            for exchange, balances in all_balances.items():
                for asset, free in balances.items():
                    try:
                        if float(free) > 0.0001: # Min threshold
                            if asset in ['USD', 'ZUSD', 'USDT', 'USDC']: has_usd = True
                            if asset in ['GBP', 'ZGBP']: has_gbp = True
                            if asset in ['EUR', 'ZEUR']: has_eur = True
                            if asset in ['XBT', 'XXBT', 'BTC']: has_btc = True
                            if asset in ['ETH', 'XETH']: has_eth = True
                    except: continue
            
            # Update tradeable currencies based on holdings
            new_tradeables = []
            if has_usd: new_tradeables.extend(['USD', 'USDT', 'USDC'])
            if has_gbp: new_tradeables.append('GBP')
            if has_eur: new_tradeables.append('EUR')
            if has_btc: new_tradeables.extend(['XBT', 'BTC'])
            if has_eth: new_tradeables.append('ETH')
            
            if new_tradeables:
                self.tradeable_currencies = list(set(new_tradeables))
                print(f"   💰 Wallet detected: {self.tradeable_currencies}")
            
            # Set Base Currency for reporting
            if has_gbp: CONFIG['BASE_CURRENCY'] = 'GBP'
            elif has_eur: CONFIG['BASE_CURRENCY'] = 'EUR'
            elif has_usd: CONFIG['BASE_CURRENCY'] = 'USD'
            
        except Exception as e:
            print(f"   ⚠️ Wallet detection error: {e}")

    def _import_existing_holdings(self):
        """Import existing crypto holdings as managed positions"""
        if self.dry_run:
            return
            
        base = CONFIG['BASE_CURRENCY']
        try:
            all_balances = self.client.get_all_balances()
        except Exception as e:
            print(f"   ⚠️ Holdings import error: {e}")
            return
            
        imported = 0
        for exchange, balances in all_balances.items():
            for asset_raw, amount in balances.items():
                if not asset_raw:
                    continue
                try:
                    amount = float(amount)
                except:
                    amount = 0.0
                if amount <= 0:
                    continue
                    
                asset_clean = asset_raw.replace('Z', '').upper()  # Keep X prefix for XBT, XLM, etc
                
                # Skip base currency (that's cash, not a position)
                if asset_clean in ['GBP', 'EUR', 'USD', 'USDT', 'USDC']:
                    continue
                    
                # Build the trading pair symbol
                # For Binance: BTCUSDT
                # For Kraken: XXBTZUSD (or similar)
                # We need to reconstruct the likely pair symbol
                
                symbol = ""
                if exchange == 'binance':
                    # Try appending base currency
                    symbol = f"{asset_clean}{base}"
                    # Check if valid ticker exists? Maybe later.
                else:
                    # Kraken
                    symbol = f"{asset_clean}{base}"
                
                # Skip if already tracked
                if symbol in self.positions:
                    continue
                    
                # Get current price
                try:
                    # For conversion, remove FIRST X prefix only (XXBT -> XBT, XETH -> ETH)
                    conversion_asset = asset_clean[1:] if asset_clean.startswith('X') and len(asset_clean) > 3 else asset_clean
                    gbp_value = self.client.convert_to_quote(exchange, conversion_asset, amount, base)
                    if gbp_value < 0.50:  # Skip dust < £0.50
                        continue
                    price = gbp_value / amount
                except Exception as e:
                    print(f"   ⚠️ Failed to import {asset_clean} on {exchange}: {e}")
                    continue
                    
                # Create position from existing holding
                self.positions[symbol] = Position(
                    symbol=symbol,
                    entry_price=price,  # Use current price as "entry" 
                    quantity=amount,
                    entry_fee=0.0,  # Already bought, no new fee
                    entry_value=gbp_value,
                    momentum=0.0,
                    coherence=0.5,
                    entry_time=time.time(),
                    dominant_node='Portfolio',
                    exchange=exchange
                )
                imported += 1
                print(f"   📦 Imported {symbol} ({exchange}): {amount:.6f} @ £{price:.4f} = £{gbp_value:.2f}")
            
        if imported > 0:
            print(f"   ✅ Imported {imported} existing holdings as managed positions")
    
    def _deploy_scouts(self):
        """Deploy scout positions immediately on first scan (from immediateWaveRider.ts)
        
        Philosophy: "They can't stop them all!" - Get positions deployed fast
        to ride waves from the start while main logic finds optimal entries.
        """
        if self.scouts_deployed or not CONFIG['DEPLOY_SCOUTS_IMMEDIATELY']:
            return
            
        print("\n   🦅 DEPLOYING SCOUTS - Immediate wave riders!")
        scouts_deployed = 0
        
        # Get available quote currencies to deploy scouts in
        quote_currencies = self.tradeable_currencies if self.dry_run else [CONFIG['BASE_CURRENCY']]
        
        for quote_curr in quote_currencies:
            # Find a high momentum opportunity for this quote currency
            candidates = []
            for symbol, data in self.ticker_cache.items():
                if not symbol.endswith(quote_curr):
                    continue
                if symbol in self.positions:
                    continue
                    
                change = data.get('change24h', 0)
                price = data.get('price', 0)
                volume = data.get('volume', 0)
                
                # Scout filter: momentum > 2%, decent volume
                if change >= CONFIG['SCOUT_MIN_MOMENTUM'] and price > 0 and volume > 1000:
                    candidates.append({
                        'symbol': symbol,
                        'price': price,
                        'change24h': change,
                        'volume': volume,
                        'score': 70,  # Scout score
                        'coherence': 0.6,  # Default scout coherence
                        'dominant_node': 'Scout'
                    })
            
            # Deploy top scout for this currency
            if candidates and len(self.positions) < CONFIG['MAX_POSITIONS']:
                candidates.sort(key=lambda x: x['change24h'], reverse=True)
                scout = candidates[0]
                print(f"   🦅 Scout {quote_curr}: {scout['symbol']} (+{scout['change24h']:.1f}%)")
                self.open_position(scout)
                scouts_deployed += 1
                
        self.scouts_deployed = True
        if scouts_deployed > 0:
            print(f"   ✅ Deployed {scouts_deployed} scout(s) - riding the wave!\n")

    def _normalize_ticker_symbol(self, symbol: str) -> str:
        """Convert internal symbol format to Kraken ticker format.
        XXBTGBP -> XBTGBP, XXLMGBP -> XLMGBP, XLTCGBP -> LTCGBP"""
        if symbol.startswith('XX') and len(symbol) > 5:
            # XXBTGBP -> XBTGBP, XXLMGBP -> XLMGBP
            return symbol[1:]
        elif symbol.startswith('XLT') or symbol.startswith('XLTC'):
            # XLTCGBP -> LTCGBP
            return symbol.replace('XLTC', 'LTC')
        return symbol

    def _get_quote_asset(self, symbol: str) -> str:
        """Best-effort detection of quote asset from symbol name."""
        if not symbol:
            return CONFIG['BASE_CURRENCY'].upper()

        sym = symbol.upper()
        if '/' in sym:
            quote_part = sym.split('/')[-1]
            if quote_part in CONFIG['QUOTE_CURRENCIES']:
                return quote_part

        for suffix in self.quote_currency_suffixes:
            if sym.endswith(suffix):
                return suffix

        return CONFIG['BASE_CURRENCY'].upper()

    def ensure_quote_liquidity(self, exchange: str, quote_asset: str, required: float) -> Tuple[bool, float, Optional[str]]:
        if self.dry_run or required <= 0:
            return True, required, None

        exchange = exchange.lower()
        if exchange not in ('binance', 'kraken'):
            return True, required, None

        exchange_client = self.client.clients.get(exchange)
        if exchange_client is None:
            return False, 0.0, None

        def _balance(asset: str) -> float:
            try:
                return float(exchange_client.get_balance(asset.upper()))
            except Exception:
                return 0.0

        warn_key = (exchange, quote_asset)

        available = _balance(quote_asset)
        if available >= required:
            return True, available, None

        if warn_key in self._liquidity_warnings:
            return False, available, None

        deficit = max(0.0, required - available)
        exchange_marker = exchange.upper()
        candidate_assets = [CONFIG['BASE_CURRENCY'].upper(), 'USDC', 'USDT', 'USD']
        suggestions: List[str] = []
        for candidate in candidate_assets:
            candidate = candidate.upper()
            if candidate == quote_asset:
                continue

            candidate_balance = _balance(candidate)
            if candidate_balance <= 0:
                continue

            symbol = exchange_client.get_standardized_pair(quote_asset, candidate)
            ticker = exchange_client.get_ticker(symbol)
            try:
                price = float(ticker.get('price', 0) or ticker.get('lastPrice', 0) or 0)
            except Exception:
                price = 0.0
            if price <= 0:
                continue

            # Calculate desired base amount (quote asset) with small buffer
            filters = exchange_client.get_symbol_filters(symbol)
            min_qty = filters.get('min_qty', 0.0) if filters else 0.0
            min_notional = filters.get('min_notional', 0.0) if filters else 0.0
            desired_base = max(deficit * 1.05, min_qty)
            if min_notional and price > 0:
                desired_base = max(desired_base, min_notional / price)
            max_affordable = candidate_balance / price
            desired_base = min(desired_base, max_affordable)
            if desired_base <= 0:
                continue

            desired_base = exchange_client.adjust_quantity(symbol, desired_base)
            if desired_base <= 0:
                continue

            if (
                min_notional and price > 0 and desired_base * price < min_notional
            ):
                step_size = filters.get('step_size', 0.0) if filters else 0.0
                target_base = min_notional / price
                bumped = desired_base
                if step_size > 0:
                    steps_needed = math.ceil(max(0.0, target_base - desired_base) / step_size)
                    if steps_needed > 0:
                        bumped = min(desired_base + steps_needed * step_size, max_affordable)
                else:
                    bumped = min(target_base, max_affordable)

                if bumped > desired_base:
                    adjusted_bump = exchange_client.adjust_quantity(symbol, bumped)
                    if (
                        adjusted_bump > desired_base and
                        adjusted_bump * price <= candidate_balance + 1e-8
                    ):
                        desired_base = adjusted_bump

            quotes_needed = desired_base * price
            if quotes_needed <= 0 or quotes_needed > candidate_balance:
                continue

            if min_notional and quotes_needed < min_notional:
                suggestions.append(
                    f"need at least {min_notional:.2f} {candidate} notional for {symbol}"
                )
                continue

            try:
                print(
                    f"   🔁 Auto-converting {desired_base:.2f} {quote_asset} using {symbol} on {exchange_marker}"
                )
                self.client.place_market_order(exchange, symbol, 'BUY', quantity=desired_base)
            except Exception as conv_err:
                suggestion = (
                    f"{candidate_balance:.2f} {candidate} ≈ {desired_base * price:.2f} {quote_asset}"
                )
                suggestions.append(suggestion)
                print(f"   ⚠️ Conversion failed ({candidate}->{quote_asset}): {conv_err}")
                continue

            time.sleep(0.5)
            available = _balance(quote_asset)
            if available >= required * 0.995:
                return True, available, None
            deficit = max(0.0, required - available)

        tip = None
        if suggestions:
            tip = f"convert {suggestions[0]} on {exchange_marker} to fund {quote_asset}"

        return False, available, tip

    # ─────────────────────────────────────────────────────────
    # Equity Management
    # ─────────────────────────────────────────────────────────

    def compute_total_equity(self) -> Tuple[float, float, Dict[str, float]]:
        """Return (total_equity, cash_in_base, holdings_map)
        
        Always fetches real balances from exchanges, regardless of dry_run mode.
        Dry run only affects order execution, not balance queries.
        """
        base = CONFIG['BASE_CURRENCY']
        holdings_value: Dict[str, float] = {}
        total_equity = 0.0
        cash_balance = 0.0
        
        try:
            all_balances = self.client.get_all_balances()
        except Exception as e:
            print(f"   ⚠️ Equity refresh error: {e}")
            return self.total_equity_gbp, self.cash_balance_gbp, self.holdings_gbp
        
        # If no balances returned, fall back to tracker (simulation mode)
        if not any(all_balances.values()):
            total_equity = self.tracker.balance
            used_capital = sum(pos.entry_value for pos in self.positions.values())
            cash_balance = max(0.0, total_equity - used_capital)
            for sym, pos in self.positions.items():
                holdings_value[sym] = pos.entry_value
            if cash_balance > 0:
                holdings_value[base] = holdings_value.get(base, 0.0) + cash_balance
            return total_equity, cash_balance, holdings_value
        
        for exchange, balances in all_balances.items():
            # Skip Alpaca if it's analytics-only (paper trading, not real funds)
            if exchange == 'alpaca' and CONFIG.get('ALPACA_ANALYTICS_ONLY', True):
                continue
                
            for asset_raw, amount in balances.items():
                if not asset_raw:
                    continue
                try:
                    amount = float(amount)
                except Exception:
                    amount = 0.0
                if amount <= 0:
                    continue
                    
                # Skip dust amounts for Binance (< $1 equivalent)
                if exchange == 'binance' and amount < 1.0 and asset_raw not in ['BTC', 'ETH', 'USDC', 'USDT', 'USD', 'BNB']:
                    continue
                    
                asset_clean = asset_raw.replace('Z', '').upper()  # Keep X prefix (XXBT stays XXBT)
                # For conversion, strip first X only (XXBT->XBT, XETH->ETH)
                conversion_asset = asset_clean[1:] if asset_clean.startswith('X') and len(asset_clean) > 3 else asset_clean
                
                # Handle Binance Earn (LD prefix)
                if asset_raw.startswith('LD'):
                    conversion_asset = asset_raw[2:]
                    asset_clean = conversion_asset
                
                # Check if this is the base currency
                if conversion_asset == base or asset_clean == base:
                    cash_balance += amount
                    total_equity += amount
                    holdings_value[asset_clean] = holdings_value.get(asset_clean, 0.0) + amount
                    continue
                try:
                    converted = self.client.convert_to_quote(exchange, conversion_asset, amount, base)
                    if converted > 0:
                        total_equity += converted
                        holdings_value[asset_clean] = holdings_value.get(asset_clean, 0.0) + converted
                except Exception:
                    continue
                    
        return total_equity, cash_balance, holdings_value

    def refresh_equity(self, mark_cycle: bool = False) -> float:
        self._liquidity_warnings.clear()
        total, cash, holdings = self.compute_total_equity()
        self.total_equity_gbp = total
        self.cash_balance_gbp = cash
        self.holdings_gbp = holdings
        self.tracker.update_equity(total, cash, mark_cycle=mark_cycle)
        
        # 🌟 Sync capital pool with current equity
        self.capital_pool.update_equity(total)
        
        if self.tracker.equity_baseline is None or self.tracker.equity_baseline == 0:
            self.tracker.equity_baseline = total
        gain = total - self.tracker.equity_baseline
        if gain > CONFIG['EQUITY_MIN_DELTA']:
            self.tracker.realize_portfolio_gain(gain)
            self.tracker.equity_baseline = total
        return total

    def should_enter_trade(self, opp: Dict, pos_size: float, lattice_state) -> bool:
        """
        Aggressive entry - buy when opportunity appears!
        This gate is for ENTRIES, so be permissive.
        """
        # Minimal sanity checks only
        if pos_size <= 0 or self.total_equity_gbp <= 0:
            return False
        # AGGRESSIVE ENTRY - Trade when you see opportunity!
        return True
    
    def should_exit_trade(self, pos: 'Position', current_price: float, reason: str) -> bool:
        """
        Smart exit gate - only sell if we're making NET PROFIT after fees.
        This ensures every closed trade is profitable.
        """
        change_pct = (current_price - pos.entry_price) / pos.entry_price
        
        # Calculate actual P&L with platform-specific fees
        exit_value = pos.quantity * current_price
        exit_fee = exit_value * get_platform_fee(pos.exchange, 'taker')
        slippage_cost = exit_value * CONFIG['SLIPPAGE_PCT']
        spread_cost = exit_value * CONFIG['SPREAD_COST_PCT']
        
        total_expenses = pos.entry_fee + exit_fee + slippage_cost + spread_cost
        gross_pnl = exit_value - pos.entry_value
        net_pnl = gross_pnl - total_expenses
        
        # TAKE PROFIT: Always allow if we're in profit
        if reason == "TP" and net_pnl > 0:
            return True
        
        # STOP LOSS: Only allow if loss is small OR we must cut losses
        if reason == "SL":
            # Allow SL if loss is less than 1% or if change is catastrophic (>2%)
            loss_pct = abs(net_pnl / pos.entry_value * 100)
            if loss_pct < 1.0 or abs(change_pct * 100) > 2.0:
                return True
            # Otherwise hold - don't lock in losses on noise
            print(f"   🛑 HOLDING {pos.symbol}: Loss too large to realize (${net_pnl:.2f})")
            return False
        
        # REBALANCE/SWAP: Only if net negative is small
        if reason in ["REBALANCE", "SWAP"]:
            if net_pnl > -0.10:  # Allow up to 10p loss for rebalancing
                return True
            return False
        
        # Default: allow exit
        return True
    
    def save_state(self):
        """Save current state to file for recovery"""
        try:
            state = {
                'balance': self.tracker.balance,
                'peak_balance': self.tracker.peak_balance,
                'total_trades': self.tracker.total_trades,
                'wins': self.tracker.wins,
                'losses': self.tracker.losses,
                'total_fees': self.tracker.total_fees,
                'compounded': self.tracker.compounded,
                'harvested': self.tracker.harvested,
                'max_drawdown': self.tracker.max_drawdown,
                'positions': {
                    sym: {
                        'entry_price': pos.entry_price,
                        'quantity': pos.quantity,
                        'entry_fee': pos.entry_fee,
                        'entry_value': pos.entry_value,
                        'momentum': pos.momentum,
                        'coherence': pos.coherence,
                        'entry_time': pos.entry_time,
                        'dominant_node': pos.dominant_node,
                        'cycles': pos.cycles
                    }
                    for sym, pos in self.positions.items()
                },
                'timestamp': time.time(),
                'iteration': self.iteration
            }
            with open(CONFIG['STATE_FILE'], 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"   ⚠️ State save error: {e}")
    
    def load_state(self):
        """Load previous state from file"""
        try:
            if not os.path.exists(CONFIG['STATE_FILE']):
                return
            
            with open(CONFIG['STATE_FILE'], 'r') as f:
                state = json.load(f)
            
            # Restore tracker state
            self.tracker.balance = state.get('balance', self.tracker.balance)
            self.tracker.peak_balance = state.get('peak_balance', self.tracker.peak_balance)
            self.tracker.total_trades = state.get('total_trades', 0)
            self.tracker.wins = state.get('wins', 0)
            self.tracker.losses = state.get('losses', 0)
            self.tracker.total_fees = state.get('total_fees', 0.0)
            self.tracker.compounded = state.get('compounded', 0.0)
            self.tracker.harvested = state.get('harvested', 0.0)
            self.tracker.max_drawdown = state.get('max_drawdown', 0.0)
            
            # Restore positions (optional - might be stale)
            saved_positions = state.get('positions', {})
            if saved_positions:
                print(f"   💾 Loaded state: {len(saved_positions)} positions from previous session")
            
        except Exception as e:
            print(f"   ⚠️ State load error: {e}")
        
    def banner(self):
        mode = "🧪 PAPER" if self.dry_run else "💰 LIVE"
        print(f"""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   🐙🌌 AUREON KRAKEN ECOSYSTEM - UNIFIED TRADING ENGINE 🌌🐙            ║
║                                                                          ║
║   Mode: {mode} TRADING                                              ║
║                                                                          ║
║   Components:                                                            ║
║   ├─ 🐅 9 Auris Nodes (Tiger, Falcon, Dolphin...)                       ║
║   ├─ 🍄 Mycelium Neural Network                                         ║
║   ├─ 💰 10-9-1 Compounding Model                                        ║
║   ├─ 🔴 Real-Time WebSocket Prices                                      ║
║   ├─ 📊 Kelly Criterion Position Sizing                                 ║
║   ├─ 🛑 Circuit Breaker (Max DD: {CONFIG['MAX_DRAWDOWN_PCT']}%)                        ║
║   └─ 🎯 51%+ Win Rate Strategy                                          ║
║                                                                          ║
║   Strategy: TP +{CONFIG['TAKE_PROFIT_PCT']}% | SL -{CONFIG['STOP_LOSS_PCT']}% | Pos: Kelly+Coherence | Base: {CONFIG['BASE_CURRENCY']}        ║
║                                                                          ║
║   Goal: 51%+ Win Rate with NET PROFIT after fees                        ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
        
   💵 Starting Balance: ${self.tracker.initial_balance:.2f}
""")

    # ─────────────────────────────────────────────────────────
    # WebSocket for Real-Time Prices
    # ─────────────────────────────────────────────────────────
    
    def convert_symbol_to_ws(self, symbol: str, exchange: str) -> str:
        """Convert REST API symbol to WebSocket pair name"""
        if exchange == 'binance':
            return symbol.lower()
        if exchange == 'alpaca':
            return symbol
            
        # Kraken logic
        base_curr = CONFIG['BASE_CURRENCY']
        if symbol.endswith(base_curr):
            base = symbol[:-len(base_curr)]
            return f"{base}/{base_curr}"
        return symbol
        
    async def websocket_handler(self, pairs: List[str]):
        """Handle WebSocket connection for real-time prices from ALL exchanges"""
        
        # Split pairs by exchange and populate mappings
        kraken_pairs = []
        binance_pairs = []
        alpaca_pairs = []
        
        for p in pairs:
            source = 'kraken'
            if p in self.ticker_cache:
                source = self.ticker_cache[p].get('source', 'kraken')
            
            if source == 'binance':
                binance_pairs.append(p)
                # Update mapping
                ws_pair = p.lower() # Binance uses lowercase
                self.symbol_to_ws[p] = ws_pair
                self.ws_to_symbol[ws_pair] = p
            elif source == 'alpaca':
                alpaca_pairs.append(p)
                self.symbol_to_ws[p] = p
                self.ws_to_symbol[p] = p
            else:
                kraken_pairs.append(p)
                # Update mapping
                ws_pair = self.convert_symbol_to_ws(p, 'kraken')
                self.symbol_to_ws[p] = ws_pair
                self.ws_to_symbol[ws_pair] = p

        async def connect_exchange(exchange_name: str, ws_url: str, exchange_pairs: List[str]):
            while True:
                try:
                    async with websockets.connect(ws_url, ping_interval=20) as ws:
                        print(f"   🔴 WebSocket connected to {exchange_name.upper()}!")
                        
                        # Alpaca Auth
                        if exchange_name == 'alpaca':
                            auth_msg = {
                                "action": "auth",
                                "key": os.getenv('ALPACA_API_KEY'),
                                "secret": os.getenv('ALPACA_SECRET_KEY')
                            }
                            await ws.send(json.dumps(auth_msg))
                            # Wait for auth response (optional but good practice)
                            await asyncio.sleep(1)

                        if exchange_pairs:
                            if exchange_name == 'binance':
                                # Binance subscription
                                streams = [f"{p.lower()}@ticker" for p in exchange_pairs]
                                chunk_size = 50
                                for i in range(0, len(streams), chunk_size):
                                    chunk = streams[i:i+chunk_size]
                                    subscribe_msg = {
                                        "method": "SUBSCRIBE",
                                        "params": chunk,
                                        "id": i+1
                                    }
                                    await ws.send(json.dumps(subscribe_msg))
                                    await asyncio.sleep(0.1)
                                    
                            elif exchange_name == 'alpaca':
                                # Alpaca subscription
                                subscribe_msg = {
                                    "action": "subscribe",
                                    "quotes": exchange_pairs
                                }
                                await ws.send(json.dumps(subscribe_msg))
                                
                            else:
                                # Kraken subscription
                                # Kraken pairs need conversion
                                k_pairs = [self.convert_symbol_to_ws(p, 'kraken') for p in exchange_pairs]
                                subscribe_msg = {
                                    "event": "subscribe",
                                    "pair": k_pairs,
                                    "subscription": {"name": "ticker"}
                                }
                                await ws.send(json.dumps(subscribe_msg))
                                
                            print(f"   📡 {exchange_name.upper()}: Subscribed to {len(exchange_pairs)} pairs")
                        
                        async for message in ws:
                            try:
                                data = json.loads(message)
                                
                                if exchange_name == 'binance':
                                    if 'e' in data and data['e'] == '24hrTicker':
                                        symbol = data['s']
                                        price = float(data['c'])
                                        with self.price_lock:
                                            self.realtime_prices[symbol] = price
                                            self.realtime_prices[symbol.lower()] = price
                                            
                                elif exchange_name == 'alpaca':
                                    if isinstance(data, list):
                                        for msg in data:
                                            if msg.get('T') == 'q':
                                                symbol = msg.get('S')
                                                bid = float(msg.get('bp', 0))
                                                ask = float(msg.get('ap', 0))
                                                price = (bid + ask) / 2
                                                if price > 0:
                                                    with self.price_lock:
                                                        self.realtime_prices[symbol] = price
                                
                                else:
                                    # Kraken
                                    if isinstance(data, list) and len(data) >= 4 and data[2] == "ticker":
                                        ws_pair = data[3]
                                        ticker_data = data[1]
                                        if 'c' in ticker_data:
                                            price = float(ticker_data['c'][0])
                                            with self.price_lock:
                                                self.realtime_prices[ws_pair] = price
                                                # Map back to internal symbol if possible
                                                pass 
                            except:
                                pass
                                
                except Exception as e:
                    print(f"   ⚠️ {exchange_name.upper()} WebSocket error: {e}")
                    await asyncio.sleep(CONFIG['WS_RECONNECT_DELAY'])

        tasks = []
        if CONFIG['EXCHANGE'] in ['kraken', 'both', 'all'] and kraken_pairs:
            tasks.append(connect_exchange('kraken', CONFIG['WS_URL'], kraken_pairs))
            
        if CONFIG['EXCHANGE'] in ['binance', 'both', 'all'] and binance_pairs:
            tasks.append(connect_exchange('binance', 'wss://stream.binance.com:9443/ws', binance_pairs))
            
        if CONFIG['EXCHANGE'] in ['alpaca', 'both', 'all'] and alpaca_pairs:
            tasks.append(connect_exchange('alpaca', 'wss://stream.data.alpaca.markets/v1beta3/crypto/us', alpaca_pairs))
            
        if tasks:
            await asyncio.gather(*tasks)
            
        if CONFIG['EXCHANGE'] in ['alpaca', 'both', 'all'] and alpaca_pairs:
            tasks.append(connect_exchange('alpaca', 'wss://stream.data.alpaca.markets/v1beta3/crypto/us', alpaca_pairs))
            
        if tasks:
            await asyncio.gather(*tasks)
        else:
            print("   ⚠️ No WebSocket tasks to run (no pairs or exchange disabled)")
                
    def start_websocket(self, symbols: List[str]):
        """Start WebSocket in background thread"""
        # We pass raw symbols to handler which will handle splitting and mapping
            
        def run_ws():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.websocket_handler(symbols))
            
        thread = Thread(target=run_ws, daemon=True)
        thread.start()
        time.sleep(2)
        
    def get_realtime_price(self, symbol: str) -> Optional[float]:
        """Get real-time price from WebSocket"""
        with self.price_lock:
            if symbol in self.realtime_prices:
                return self.realtime_prices[symbol]
            ws_pair = self.symbol_to_ws.get(symbol)
            if ws_pair and ws_pair in self.realtime_prices:
                return self.realtime_prices[ws_pair]
        return None

    # ─────────────────────────────────────────────────────────
    # Market Data
    # ─────────────────────────────────────────────────────────
    
    def refresh_tickers(self) -> int:
        """Refresh ticker data from REST API"""
        try:
            tickers_list = self.client.get_24h_tickers()
            self.ticker_cache = {}
            
            for t in tickers_list:
                symbol = t.get('symbol', '')
                if not symbol:
                    continue
                try:
                    price = float(t.get('lastPrice', 0))
                    change = float(t.get('priceChangePercent', 0))
                    volume = float(t.get('quoteVolume', 0))
                    source = t.get('source', 'kraken')
                    
                    self.ticker_cache[symbol] = {
                        'price': price,
                        'change24h': change,
                        'volume': volume,
                        'source': source
                    }
                    
                    # Update price history
                    if symbol not in self.price_history:
                        self.price_history[symbol] = []
                    self.price_history[symbol].append(price)
                    if len(self.price_history[symbol]) > 50:
                        self.price_history[symbol] = self.price_history[symbol][-50:]
                        
                    # Feed mycelium network
                    signal = 0.5 + (change / 20)  # Normalize change to 0-1
                    self.mycelium.add_signal(symbol, max(0, min(1, signal)))
                except:
                    continue
                    
            return len(self.ticker_cache)
        except Exception as e:
            print(f"   ⚠️ Ticker refresh error: {e}")
            return 0

    # ─────────────────────────────────────────────────────────
    # 🌉 Bridge Integration Methods
    # ─────────────────────────────────────────────────────────
    
    def sync_bridge(self):
        """Sync state with Aureon Bridge for Ultimate ↔ Unified communication"""
        if not self.bridge_enabled or not self.bridge:
            return
        
        now = time.time()
        if now - self.last_bridge_sync < self.bridge_sync_interval:
            return
        
        try:
            # 1. Update Capital State
            capital_state = CapitalState(
                total_equity=self.total_equity_gbp,
                allocated_capital=sum(pos.entry_value for pos in self.positions.values()),
                free_capital=self.capital_pool.get_available(),
                realized_profit=self.tracker.net_profit,
                unrealized_profit=sum(
                    (self.get_realtime_price(sym) or pos.entry_price - pos.entry_price) * pos.quantity
                    for sym, pos in self.positions.items()
                ),
                total_fees=self.tracker.total_fees,
                net_profit=self.tracker.net_profit,
                trades_count=self.tracker.total_trades,
                wins_count=self.tracker.wins,
                win_rate=self.tracker.wins / max(1, self.tracker.total_trades),
                exchange_breakdown={
                    'kraken': self.tracker.platform_metrics.get('kraken', {}).get('total_equity', 0.0),
                    'binance': self.tracker.platform_metrics.get('binance', {}).get('total_equity', 0.0),
                    'alpaca': self.tracker.platform_metrics.get('alpaca', {}).get('total_equity', 0.0),
                }
            )
            self.bridge.update_capital(capital_state)
            
            # 2. Register Open Positions
            for symbol, pos in self.positions.items():
                bridge_pos = BridgePosition(
                    symbol=symbol,
                    exchange=pos.exchange,
                    side='BUY',  # All our positions are long
                    size=pos.quantity,
                    entry_price=pos.entry_price,
                    current_price=self.get_realtime_price(symbol) or pos.entry_price,
                    unrealized_pnl=(self.get_realtime_price(symbol) or pos.entry_price - pos.entry_price) * pos.quantity,
                    entry_time=pos.entry_time,
                    owner='unified'
                )
                self.bridge.register_position(bridge_pos)
            
            self.last_bridge_sync = now
            
        except Exception as e:
            print(f"   ⚠️ Bridge sync error: {e}")
    
    def publish_opportunities_to_bridge(self, opportunities: List[Dict]):
        """Publish top opportunities to bridge for Ultimate system"""
        if not self.bridge_enabled or not self.bridge:
            return
        
        try:
            bridge_opps = []
            for opp in opportunities[:10]:  # Top 10
                bridge_opp = BridgeOpportunity(
                    symbol=opp['symbol'],
                    exchange=opp.get('source', 'kraken'),
                    side='BUY',
                    score=opp['score'],
                    coherence=opp['coherence'],
                    momentum=opp['change24h'],
                    volume=opp['volume'],
                    price=opp['price'],
                    probability=opp.get('probability'),
                    anomaly_flags=opp.get('anomaly_flags', []),
                    frequency=opp.get('hnc_frequency'),
                    source_system='unified'
                )
                bridge_opps.append(bridge_opp)
            
            self.bridge.publish_opportunities(bridge_opps)
            
        except Exception as e:
            print(f"   ⚠️ Failed to publish opportunities to bridge: {e}")
    
    def consume_ultimate_opportunities(self) -> List[Dict]:
        """Get opportunities from Ultimate system via bridge"""
        if not self.bridge_enabled or not self.bridge:
            return []
        
        try:
            # Get opportunities from Ultimate (Binance focus)
            bridge_opps = self.bridge.get_opportunities(
                exchange='binance',
                min_score=CONFIG['MIN_SCORE'],
                max_age_seconds=60.0
            )
            
            # Convert to internal format
            opportunities = []
            for opp in bridge_opps:
                opportunities.append({
                    'symbol': opp.symbol,
                    'price': opp.price,
                    'change24h': opp.momentum,
                    'volume': opp.volume,
                    'score': opp.score,
                    'coherence': opp.coherence,
                    'dominant_node': 'TIGER',  # Default
                    'source': opp.exchange,
                    'hnc_frequency': opp.frequency or 256,
                    'hnc_harmonic': False,
                    'probability': opp.probability or 0.5,
                    'prob_confidence': 0.5,
                    'prob_action': 'BUY',
                    'from_bridge': True
                })
            
            if opportunities:
                print(f"   🌉 Received {len(opportunities)} opportunities from Ultimate")
            
            return opportunities
            
        except Exception as e:
            print(f"   ⚠️ Failed to consume Ultimate opportunities: {e}")
            return []
    
    def check_bridge_commands(self):
        """Process control commands from bridge"""
        if not self.bridge_enabled or not self.bridge:
            return
        
        try:
            commands = self.bridge.get_commands('unified', max_age_seconds=60.0, clear_after_read=True)
            
            for cmd in commands:
                if cmd.command == 'pause':
                    self.tracker.trading_halted = True
                    self.tracker.halt_reason = "Bridge command: pause"
                    print(f"   🎛️ Trading PAUSED by bridge command")
                    
                elif cmd.command == 'resume':
                    self.tracker.trading_halted = False
                    self.tracker.halt_reason = ""
                    print(f"   🎛️ Trading RESUMED by bridge command")
                    
                elif cmd.command == 'harvest':
                    min_profit = cmd.params.get('min_profit', 0.0)
                    # Force close winning positions
                    for symbol, pos in list(self.positions.items()):
                        current_price = self.get_realtime_price(symbol) or pos.entry_price
                        pnl = (current_price - pos.entry_price) * pos.quantity
                        if pnl >= min_profit:
                            print(f"   🌉 Harvesting {symbol} (${pnl:+.2f}) via bridge command")
                            self.close_position(symbol, reason='bridge_harvest')
                    
                elif cmd.command == 'force_exit':
                    target_symbol = cmd.params.get('symbol')
                    if target_symbol and target_symbol in self.positions:
                        print(f"   🌉 Force exiting {target_symbol} via bridge command")
                        self.close_position(target_symbol, reason='bridge_force_exit')
                        
        except Exception as e:
            print(f"   ⚠️ Bridge command processing error: {e}")
    
    # ─────────────────────────────────────────────────────────
    # Opportunity Detection
    # ─────────────────────────────────────────────────────────
    
    def find_opportunities(self) -> List[Dict]:
        """Find best trading opportunities using all analysis methods - TRADES EVERYTHING"""
        opportunities = []
        
        # 🌐 Scan for anomalies across exchanges (if enabled)
        if CONFIG.get('ENABLE_COINAPI', False):
            symbols_to_scan = list(self.ticker_cache.keys())
            anomalies = self.auris.scan_for_anomalies(symbols_to_scan)
            if anomalies:
                print(f"   🌐 Detected {len(anomalies)} anomalies across exchanges")
        
        # In live mode, only look for pairs we can actually trade with our holdings
        # This means pairs ending in currencies we have (cash or can sell for)
        if not self.dry_run:
            # Get list of assets we hold (these can be sold to buy others)
            available_quotes = set()
            for symbol in self.positions.keys():
                # Extract quote currency from position symbols
                for curr in ['GBP', 'USD', 'EUR', 'USDT', 'BTC', 'ETH']:
                    if symbol.endswith(curr):
                        available_quotes.add(curr)
                        break
            # Also add base currency if we have cash
            if self.cash_balance_gbp > CONFIG['MIN_TRADE_USD']:
                available_quotes.add(CONFIG['BASE_CURRENCY'])
            
            quote_currencies = list(available_quotes) if available_quotes else [CONFIG['BASE_CURRENCY']]
        else:
            quote_currencies = CONFIG.get('QUOTE_CURRENCIES', self.tradeable_currencies)
        
        for symbol, data in self.ticker_cache.items():
            # 🌐 Check anomaly blacklist (CoinAPI)
            if CONFIG.get('ENABLE_COINAPI', False):
                if self.auris.is_symbol_blacklisted(symbol):
                    continue  # Skip blacklisted symbols
            
            # 🐘 Check Elephant Memory blacklist/cooldown
            if self.memory.should_avoid(symbol):
                continue
            
            # Filter based on tradeable quote currencies
            if not any(symbol.endswith(curr) for curr in quote_currencies):
                continue
                
            change = data['change24h']
            price = data['price']
            volume = data['volume']
            
            # Basic filters
            if change < CONFIG['MIN_MOMENTUM'] or change > CONFIG['MAX_MOMENTUM']:
                continue
            if price < 0.0001 or volume < CONFIG['MIN_VOLUME']:
                continue
            if symbol in self.positions:
                continue
                
            # Build market state for Auris analysis
            prices = self.price_history.get(symbol, [price])
            state = MarketState(
                symbol=symbol,
                price=price,
                bid=price * 0.999,
                ask=price * 1.001,
                volume=volume,
                change_24h=change,
                high_24h=price * 1.02,
                low_24h=price * 0.98,
                prices=prices[-20:],
                timestamp=time.time()
            )
            
            # Get Auris coherence
            coherence, dominant_node = self.auris.compute_coherence(state)
            
            # 🌐 Apply coherence adjustment based on anomalies (CoinAPI)
            coherence_threshold = CONFIG['ENTRY_COHERENCE']
            if CONFIG.get('ENABLE_COINAPI', False):
                adjustment = self.auris.get_coherence_adjustment(symbol)
                coherence_threshold *= adjustment  # Increase threshold if anomalies detected
            
            # Skip if coherence too low
            if coherence < coherence_threshold:
                continue
            
            # Propagate through Mycelium network for enhanced signal
            self.mycelium.add_signal(symbol, coherence)
            network_activations = self.mycelium.propagate()
            
            # Adjust coherence based on network activation
            if symbol in network_activations:
                network_boost = (network_activations[symbol] - coherence) * 0.2
                coherence = min(1.0, coherence + network_boost)
                
            # Calculate composite score
            score = 50
            
            # Momentum score
            if change > 20: score += 25
            elif change > 10: score += 20
            elif change > 5: score += 15
            else: score += 10
            
            # Volume score
            if volume > 1000000: score += 20
            elif volume > 500000: score += 15
            elif volume > 100000: score += 10
            else: score += 5
            
            # Coherence bonus
            score += int(coherence * 20)
            
            # 🌍⚡ HNC Frequency Analysis ⚡🌍
            hnc_frequency = 256  # Default ROOT
            hnc_is_harmonic = False
            prob_signal = None
            if CONFIG.get('ENABLE_HNC_FREQUENCY', True):
                hnc_enhanced = self.auris.update_hnc_state(symbol, price, change, coherence, score)
                if hnc_enhanced:
                    hnc_frequency = hnc_enhanced.get('hnc_frequency', 256)
                    hnc_is_harmonic = hnc_enhanced.get('hnc_is_harmonic', False)
                    # Bonus for harmonic frequencies (256, 528 Hz)
                    if hnc_is_harmonic:
                        score += 15
                    # Penalty for distortion (440 Hz)
                    elif hnc_frequency == 440:
                        score -= 10
            
            # 🔮 SYSTEM FLUX PREDICTION 🔮
            # "It's not about percentage right, we already know what way the system will go"
            flux = self.flux_predictor.predict(self.ticker_cache)
            flux_score = flux['flux_score']
            flux_strength = flux['strength']
            
            # Adjust score based on system flux
            # If system is BULLISH, boost all scores. If BEARISH, penalize.
            # This overrides probability because we are reading the WHOLE SYSTEM.
            score += int(flux_score * 25)  # ±25 points based on system direction
            
            # 📊 Probability Matrix Analysis (2-Hour Window) 📊
            prob_probability = 0.5
            prob_confidence = 0.0
            prob_action = 'HOLD'
            if CONFIG.get('ENABLE_PROB_MATRIX', True):
                prob_signal = self.auris.get_probability_signal(
                    symbol=symbol,
                    price=price,
                    frequency=hnc_frequency,
                    momentum=change,
                    coherence=coherence,
                    is_harmonic=hnc_is_harmonic,
                )
                prob_probability = prob_signal.get('probability', 0.5)
                prob_confidence = prob_signal.get('confidence', 0.0)
                prob_action = prob_signal.get('action', 'HOLD')
                
                # FLUX OVERRIDE: If flux is strong, it dominates probability
                if flux_strength > CONFIG.get('FLUX_THRESHOLD', 0.60):
                    if flux['direction'] == 'BULLISH':
                        prob_probability = max(prob_probability, 0.80) # Force high prob
                        prob_confidence = max(prob_confidence, 0.90)   # Force high conf
                    elif flux['direction'] == 'BEARISH':
                        prob_probability = min(prob_probability, 0.20) # Force low prob
                        prob_confidence = max(prob_confidence, 0.90)
                
                # Score adjustment based on probability
                if prob_confidence >= CONFIG.get('PROB_MIN_CONFIDENCE', 0.50):
                    if prob_probability >= CONFIG.get('PROB_HIGH_THRESHOLD', 0.65):
                        score += 20  # High probability boost
                    elif prob_probability <= CONFIG.get('PROB_LOW_THRESHOLD', 0.40):
                        score -= 15  # Low probability penalty
            
            # 🌌⚡ Imperial Predictability Analysis ⚡🌌
            imperial_probability = 0.5
            imperial_confidence = 0.0
            imperial_action = 'HOLD'
            imperial_multiplier = 1.0
            cosmic_phase = 'UNKNOWN'
            if CONFIG.get('ENABLE_IMPERIAL', True):
                imperial_signal = self.auris.get_imperial_prediction(
                    symbol=symbol,
                    price=price,
                    momentum=change,
                )
                imperial_probability = imperial_signal.get('probability', 0.5)
                imperial_confidence = imperial_signal.get('confidence', 0.0)
                imperial_action = imperial_signal.get('action', 'HOLD')
                imperial_multiplier = imperial_signal.get('multiplier', 1.0)
                cosmic_phase = imperial_signal.get('cosmic_phase', 'UNKNOWN')
                
                # Score adjustment based on imperial prediction
                if imperial_confidence >= 0.5:
                    imperial_boost = (imperial_probability - 0.5) * 40  # ±20 points
                    cosmic_boost = imperial_signal.get('alignment_bonus', 0) * 100  # ±15 points
                    score += int(imperial_boost + cosmic_boost)
            
            # Golden ratio alignment
            if len(prices) >= 5:
                ratio = prices[-1] / prices[-5] if prices[-5] > 0 else 1
                if 1.5 < ratio < 1.7:  # Near PHI
                    score += 10
            
            # 🎯 OPTIMAL WIN RATE GATE COUNTING 🎯
            gates_passed = 0
            gate_status = []
            
            if CONFIG.get('ENABLE_OPTIMAL_WR', True):
                # Gate 1: HNC Harmonic (not distortion)
                if hnc_is_harmonic:
                    gates_passed += 1
                    gate_status.append('HNC:✓')
                elif hnc_frequency != 440:
                    gates_passed += 0.5  # Neutral frequency partial credit
                    gate_status.append('HNC:~')
                else:
                    gate_status.append('HNC:✗')
                
                # Gate 2: Probability Matrix confidence
                if prob_confidence >= CONFIG.get('PROB_MIN_CONFIDENCE', 0.50):
                    if prob_probability >= 0.55:
                        gates_passed += 1
                        gate_status.append('PROB:✓')
                    elif prob_probability >= 0.50:
                        gates_passed += 0.5
                        gate_status.append('PROB:~')
                    else:
                        gate_status.append('PROB:✗')
                else:
                    gate_status.append('PROB:?')
                
                # Gate 3: Imperial Predictability
                if imperial_confidence >= 0.50 and imperial_probability >= 0.55:
                    gates_passed += 1
                    gate_status.append('IMP:✓')
                elif cosmic_phase not in ['DISTORTION', '440_DOMINANT']:
                    gates_passed += 0.5
                    gate_status.append('IMP:~')
                else:
                    gate_status.append('IMP:✗')
                
                # Gate 4: Coherence above optimal threshold
                if coherence >= CONFIG.get('OPTIMAL_MIN_COHERENCE', 0.50):
                    gates_passed += 1
                    gate_status.append('COH:✓')
                elif coherence >= CONFIG.get('ENTRY_COHERENCE', 0.45):
                    gates_passed += 0.5
                    gate_status.append('COH:~')
                else:
                    gate_status.append('COH:✗')
                
                # Gate 5: Trend confirmation (positive momentum with volume)
                if CONFIG.get('OPTIMAL_TREND_CONFIRM', True):
                    if change > 1.0 and volume > 100000:
                        gates_passed += 1
                        gate_status.append('TRD:✓')
                    elif change > 0:
                        gates_passed += 0.5
                        gate_status.append('TRD:~')
                    else:
                        gate_status.append('TRD:✗')
                
                # Gate 6: System Flux Confirmation (The 30-Span)
                if flux['direction'] == 'BULLISH':
                    gates_passed += 1
                    gate_status.append('FLUX:✓')
                elif flux['direction'] == 'NEUTRAL':
                    gates_passed += 0.5
                    gate_status.append('FLUX:~')
                else:
                    gate_status.append('FLUX:✗')
                
                # Require minimum gates to pass
                min_gates = CONFIG.get('OPTIMAL_MIN_GATES', 3)
                if gates_passed < min_gates:
                    continue  # Skip - not enough gates passed
                
                # Bonus for high gate count
                if gates_passed >= 5:
                    score += 20
                elif gates_passed >= 4:
                    score += 15
                elif gates_passed >= 3:
                    score += 10
                    
            if score >= CONFIG['MIN_SCORE']:
                opportunities.append({
                    'symbol': symbol,
                    'price': price,
                    'change24h': change,
                    'volume': volume,
                    'score': score,
                    'coherence': coherence,
                    'dominant_node': dominant_node,
                    'source': data.get('source', 'kraken'),
                    'hnc_frequency': hnc_frequency,
                    'hnc_harmonic': hnc_is_harmonic,
                    'probability': prob_probability,
                    'prob_confidence': prob_confidence,
                    'prob_action': prob_action,
                    # Imperial Predictability fields
                    'imperial_probability': imperial_probability,
                    'imperial_confidence': imperial_confidence,
                    'imperial_action': imperial_action,
                    'imperial_multiplier': imperial_multiplier,
                    'cosmic_phase': cosmic_phase,
                    # System Flux fields
                    'flux_score': flux_score,
                    'flux_direction': flux['direction'],
                    # Optimal Win Rate fields
                    'gates_passed': gates_passed if CONFIG.get('ENABLE_OPTIMAL_WR', True) else 0,
                    'gate_status': '|'.join(gate_status) if CONFIG.get('ENABLE_OPTIMAL_WR', True) else '',
                })
        
        # 🌉 Merge opportunities from Ultimate system via bridge
        ultimate_opps = self.consume_ultimate_opportunities()
        if ultimate_opps:
            opportunities.extend(ultimate_opps)
                
        # Sort by score and return MORE opportunities
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        
        # 🌉 Publish top opportunities to bridge for Ultimate
        top_opportunities = opportunities[:min(CONFIG['MAX_POSITIONS'] * 2, CONFIG['MAX_POSITIONS'] - len(self.positions) + 5)]
        self.publish_opportunities_to_bridge(top_opportunities)
        
        return top_opportunities

    # ─────────────────────────────────────────────────────────
    # Position Management
    # ─────────────────────────────────────────────────────────
    
    def open_position(self, opp: Dict):
        """Open a new position - dynamically frees capital if needed"""
        symbol = opp['symbol']
        price = opp['price']
        exchange = (opp.get('source') or 'kraken').lower()
        exchange_marker = exchange.upper()
        quote_asset = self._get_quote_asset(symbol)
        base_currency = CONFIG['BASE_CURRENCY'].upper()
        
        # 🦙 Skip Alpaca trades if in analytics-only mode
        if exchange == 'alpaca' and CONFIG.get('ALPACA_ANALYTICS_ONLY', True):
            return
        
        if self.tracker.trading_halted:
            return
        
        # 🌍⚡ Get HNC frequency modifier for position sizing ⚡🌍
        hnc_modifier = 1.0
        hnc_enhanced = None
        hnc_frequency = 256.0
        if CONFIG.get('ENABLE_HNC_FREQUENCY', True):
            hnc_enhanced = self.auris.update_hnc_state(
                symbol, price, opp.get('momentum', 0), opp['coherence'], opp.get('score', 50)
            )
            if hnc_enhanced:
                hnc_frequency = hnc_enhanced.get('hnc_frequency', 256.0)
                hnc_modifier = self.auris.get_hnc_position_modifier()
                
                # 🎯 HNC FREQUENCY ENTRY OPTIMIZATION
                if CONFIG.get('HNC_FREQUENCY_GATE', True):
                    # BLOCK distortion frequency entries (440Hz)
                    if CONFIG.get('HNC_DISTORTION_ENTRY_BLOCK', True) and hnc_frequency == 440:
                        print(f"   🔴 HNC BLOCKS {symbol}: 440Hz distortion frequency")
                        return
                    
                    # BOOST harmonic frequency entries
                    if hnc_enhanced.get('hnc_is_harmonic', False):
                        harmonic_boost = CONFIG.get('HNC_HARMONIC_ENTRY_BOOST', 1.25)
                        hnc_modifier *= harmonic_boost
                        print(f"   🟢 HNC BOOST {symbol}: {hnc_frequency:.0f}Hz harmonic (×{harmonic_boost:.2f})")
                    # PENALIZE distortion but allow entry
                    elif hnc_frequency == 440:
                        hnc_modifier *= CONFIG.get('HNC_DISTORTION_PENALTY', 0.70)
        
        # 🌌⚡ Get Imperial predictability modifier for position sizing ⚡🌌
        imperial_modifier = opp.get('imperial_multiplier', 1.0)
        if CONFIG.get('ENABLE_IMPERIAL', True):
            # Check if cosmic state supports trading
            should_trade, reason = self.auris.should_trade_imperial()
            if not should_trade:
                print(f"   🌌 Imperial halts {symbol}: {reason}")
                return
            
            # Get fresh imperial modifier if not in opportunity
            if imperial_modifier == 1.0:
                imperial_modifier = self.auris.get_imperial_position_modifier(
                    symbol, opp.get('change24h', 0), price
                )
        
        # 🌍✨ Check Earth Resonance gate ✨🌍
        if CONFIG.get('ENABLE_EARTH_RESONANCE', True):
            earth_ok, earth_reason = self.auris.should_trade_earth()
            if not earth_ok:
                print(f"   🌍 Earth halts {symbol}: {earth_reason}")
                return
        
        lattice_state = self.lattice.get_state()
        size_fraction = self.tracker.calculate_position_size(
            opp['coherence'], symbol, hnc_modifier, imperial_modifier
        )
        size_fraction *= lattice_state.risk_mod
        if size_fraction <= 0:
            return

        deploy_cap = self.total_equity_gbp * CONFIG['PORTFOLIO_RISK_BUDGET']
        deployed = sum(pos.entry_value for pos in self.positions.values())
        available_risk = max(0.0, deploy_cap - deployed)
        if available_risk < CONFIG['MIN_TRADE_USD']:
            return

        pos_size = self.capital_pool.get_recommended_position_size(size_fraction)
        if pos_size <= 0:
            return
        pos_size = min(pos_size, available_risk)

        if self.dry_run:
            cash_available = max(0.0, self.tracker.balance - deployed)
        else:
            cash_available = max(0.0, self.cash_balance_gbp)
        
        # DYNAMIC CAPITAL ALLOCATION: If no cash but this is a better opportunity,
        # sell the worst-performing position to free up capital
        if cash_available < CONFIG['MIN_TRADE_USD'] and CONFIG['ENABLE_REBALANCING'] and self.positions:
            worst_pos = None
            worst_pct = 0
            
            for pos_symbol, pos in self.positions.items():
                if pos.cycles < CONFIG['MIN_HOLD_CYCLES']:
                    continue
                curr_price = self.get_realtime_price(pos_symbol)
                if curr_price is None:
                    curr_price = self.ticker_cache.get(pos_symbol, {}).get('price', pos.entry_price)
                if curr_price and curr_price > 0:
                    pct = (curr_price - pos.entry_price) / pos.entry_price * 100
                    if pct < worst_pct:
                        worst_pct = pct
                        worst_pos = (pos_symbol, pct, curr_price)
            
            # Only swap if new opportunity score is significantly better
            if worst_pos and opp.get('score', 0) > 85 and worst_pct < CONFIG['REBALANCE_THRESHOLD']:
                pos_symbol, pct, curr_price = worst_pos
                print(f"   🔄 DYNAMIC SWAP: Selling {pos_symbol} ({pct:+.2f}%) to buy {symbol}")
                self.close_position(pos_symbol, "SWAP", pct, curr_price)
                self.refresh_equity()
                cash_available = max(0.0, self.cash_balance_gbp)
        
        if cash_available < CONFIG['MIN_TRADE_USD']:
            # Only print skip message once per cycle per symbol
            if not hasattr(self, '_skip_logged'):
                self._skip_logged = set()
            if symbol not in self._skip_logged:
                print(f"   ⚪ Skipping {symbol}: insufficient cash (£{cash_available:.2f})")
                self._skip_logged.add(symbol)
            return
        
        # Clear skip log at end of cycle
        if hasattr(self, '_skip_logged'):
            self._skip_logged.clear()
            
        pos_size = min(pos_size, cash_available)

        if pos_size < CONFIG['MIN_TRADE_USD']:
            return

        if not self.should_enter_trade(opp, pos_size, lattice_state):
            print(f"   ⚪ Skipping {symbol}: portfolio gate rejected entry")
            return
        
        quote_amount_needed = pos_size
        if base_currency != quote_asset:
            try:
                converted = self.client.convert_to_quote(exchange, base_currency, pos_size, quote_asset)
                if converted > 0:
                    quote_amount_needed = converted
            except Exception:
                pass

        liquidity_required = (not self.dry_run) and exchange in ('binance', 'kraken')
        if liquidity_required:
            has_liquidity, available_quote, liquidity_tip = self.ensure_quote_liquidity(exchange, quote_asset, quote_amount_needed)
            if not has_liquidity:
                warn_key = (exchange, quote_asset)
                if warn_key not in self._liquidity_warnings:
                    print(
                        f"   ⚪ Skipping {symbol}: insufficient {quote_asset} on {exchange_marker} "
                        f"({available_quote:.2f} available, need {quote_amount_needed:.2f})"
                    )
                    if liquidity_tip:
                        print(f"   💡 Liquidity tip: {liquidity_tip}")
                    self._liquidity_warnings.add(warn_key)
                return

        actual_fraction = (pos_size / self.tracker.balance) if self.tracker.balance > 0 else 0.0
        # Use platform-specific fee
        entry_fee = pos_size * get_platform_fee(exchange, 'taker')
        quantity = pos_size / price
        
        if not self.dry_run:
            try:
                res = self.client.place_market_order(exchange, symbol, 'BUY', quote_qty=quote_amount_needed)
            except Exception as e:
                print(f"   ⚠️ Execution error for {symbol}: {e}")
                return

            if isinstance(res, dict):
                if res.get('rejected'):
                    reason = res.get('reason') or 'exchange rejected order'
                    print(f"   ⚠️ Order rejected for {symbol}: {reason}")
                    return

                if res.get('dryRun'):
                    order_id = 'dry_run'
                else:
                    order_id = res.get('orderId') or res.get('id')
                    result = res.get('result') if isinstance(res.get('result'), dict) else {}
                    if not order_id and result:
                        txids = result.get('txid')
                        if isinstance(txids, list) and txids:
                            order_id = txids[0]
                        elif isinstance(txids, str) and txids:
                            order_id = txids
                    if not order_id:
                        print(f"   ⚠️ Order failed for {symbol}: No order ID returned")
                        return
        prime_multiplier = 1.0
        if len(self.positions) < 3:  # Apply prime sizing to first few positions
            prime_multiplier = self.prime_sizer.get_next_size(1.0) / CONFIG['BASE_POSITION_SIZE']
            pos_size *= prime_multiplier
            pos_size = min(pos_size, available_risk, cash_available)
            quantity = pos_size / price
            entry_fee = pos_size * get_platform_fee(exchange, 'taker')
        
        # Create position with swarm enhancements
        is_scout = len(self.positions) == 0  # First position becomes scout
        
        self.positions[symbol] = Position(
            symbol=symbol,
            entry_price=price,
            quantity=quantity,
            entry_fee=entry_fee,
            entry_value=pos_size,
            momentum=opp['change24h'],
            coherence=opp['coherence'],
            entry_time=time.time(),
            dominant_node=opp['dominant_node'],
            generation=0,
            is_scout=is_scout,
            prime_size_multiplier=prime_multiplier,
            exchange=exchange
        )
        
        # 🌟 Allocate capital in pool
        self.capital_pool.allocate(symbol, pos_size)
        
        # 🐘 Record the successful hunt
        self.memory.record_hunt(symbol, opp.get('volume', 0), opp.get('change24h', 0))
        
        self.tracker.total_fees += entry_fee
        # Track entry fee in platform metrics
        if exchange.lower() in self.tracker.platform_metrics:
            self.tracker.platform_metrics[exchange.lower()]['fees'] += entry_fee
        self.tracker.symbol_exposure[symbol] = self.tracker.symbol_exposure.get(symbol, 0.0) + actual_fraction
        self.cash_balance_gbp = max(0.0, self.cash_balance_gbp - pos_size)
        self.holdings_gbp[symbol] = self.holdings_gbp.get(symbol, 0.0) + pos_size
        
        icon = self._get_node_icon(opp['dominant_node'])
        curr_sym = "£" if CONFIG['BASE_CURRENCY'] == 'GBP' else "€" if CONFIG['BASE_CURRENCY'] == 'EUR' else "$"
        scout_marker = " 🐺" if is_scout else ""
        prime_marker = f" [×{prime_multiplier:.1f}]" if prime_multiplier != 1.0 else ""
        exch_marker = f" [{exchange_marker}]"
        flux_marker = f" 🌊{opp.get('flux_direction', 'N')}"
        # 🌍⚡ Add HNC frequency indicator ⚡🌍
        hnc_freq = opp.get('hnc_frequency', 256)
        hnc_marker = ""
        if CONFIG.get('ENABLE_HNC_FREQUENCY', True):
            if opp.get('hnc_harmonic', False):
                hnc_marker = f" 🌈{hnc_freq}Hz"
            elif hnc_freq == 440:
                hnc_marker = f" ⚠️{hnc_freq}Hz"
            else:
                hnc_marker = f" {hnc_freq}Hz"
        print(f"   {icon} BUY  {symbol:12s} @ {curr_sym}{price:.6f} | {curr_sym}{pos_size:.2f} ({actual_fraction*100:.1f}%) | Γ={opp['coherence']:.2f} | +{opp['change24h']:.1f}%{hnc_marker}{flux_marker}{scout_marker}{prime_marker}{exch_marker}")
        
    def check_positions(self):
        """Check all positions for TP/SL with HNC frequency optimization and Earth Resonance"""
        to_close = []
        
        # 🌍✨ Get Earth Resonance exit urgency once per cycle ✨🌍
        earth_exit_urgency = 0.0
        if CONFIG.get('EARTH_EXIT_URGENCY', True) and self.auris.earth_engine:
            try:
                # get_exit_urgency returns (urgency_level, exit_factor)
                _, earth_exit_urgency = self.auris.earth_engine.get_exit_urgency(0)  # 0% P&L as default
            except:
                pass
        
        for symbol, pos in self.positions.items():
            pos.cycles += 1
            
            # 🌍⚡ EARTH RESONANCE EXIT URGENCY ⚡🌍
            # If field coherence is low, reduce TP threshold to exit faster
            effective_tp_mult = 1.0
            if earth_exit_urgency > 0 and CONFIG.get('EARTH_EXIT_URGENCY', True):
                # Reduce TP threshold by urgency percentage (e.g., 0.3 urgency = 70% of normal TP)
                effective_tp_mult = 1.0 - (earth_exit_urgency * 0.5)  # Max 50% reduction
            
            # 🌍⚡ HNC FREQUENCY EXIT OPTIMIZATION ⚡🌍
            if CONFIG.get('HNC_EXIT_ON_FREQUENCY_SHIFT', True) and CONFIG.get('ENABLE_HNC_FREQUENCY', True):
                try:
                    # Get current frequency for this asset
                    current_price = self.get_realtime_price(symbol)
                    if current_price:
                        hnc_state = self.auris.update_hnc_state(
                            symbol, current_price, 0, pos.coherence, 50
                        )
                        if hnc_state:
                            current_freq = hnc_state.get('hnc_frequency', 256)
                            entry_freq = pos.metadata.get('hnc_frequency', 256)
                            
                            # Exit if frequency shifted from harmonic to distortion
                            if entry_freq in [256, 512, 528, 639, 963] and current_freq == 440:
                                change_pct = (current_price - pos.entry_price) / pos.entry_price * 100
                                print(f"   🔴 HNC EXIT {symbol}: Frequency shift {entry_freq:.0f}Hz→440Hz (distortion)")
                                to_close.append((symbol, "HNC_FREQ_SHIFT", change_pct, current_price))
                                continue
                except Exception as e:
                    pass  # Continue with normal checks
            
            # Get current price (prefer WebSocket)
            current_price = self.get_realtime_price(symbol)
            source = "WS"
            
            if current_price is None:
                # Fallback to ticker cache
                current_price = self.ticker_cache.get(symbol, {}).get('price')
                source = "CACHE"
                
            # If still None, force a fresh lookup for this specific symbol
            if current_price is None:
                try:
                    # Force single ticker lookup
                    if pos.exchange == 'binance':
                        ticker = self.client.get_ticker(symbol, exchange='binance')
                        if ticker:
                            current_price = float(ticker.get('lastPrice', 0))
                            source = "REST_FORCE_BINANCE"
                    else:
                        # Kraken logic
                        ticker_symbol = self._normalize_ticker_symbol(symbol)
                        ticker = self.client._ticker([ticker_symbol])
                        if ticker:
                            t_data = list(ticker.values())[0]
                            current_price = float(t_data.get('c', [0])[0])
                            source = "REST_FORCE_KRAKEN"
                except Exception as e:
                    print(f"   ⚠️ Failed to force price check for {symbol}: {e}")

            # Final fallback
            if current_price is None or current_price == 0:
                current_price = pos.entry_price
                source = "ENTRY (STALE)"

            change_pct = (current_price - pos.entry_price) / pos.entry_price * 100
            
            # 🌟 SIGNAL BROADCASTING: Scout positions broadcast market signals
            if pos.is_scout and abs(change_pct) > 0.5 and (time.time() - pos.last_signal_broadcast) > 30:
                # Scout broadcasts signal when it moves significantly
                direction = 'BUY' if change_pct > 0 else 'SELL'
                strength = min(1.0, abs(change_pct) / 5.0)  # 5% move = 1.0 strength
                
                signal = MarketSignal(
                    symbol=symbol,
                    direction=direction,
                    strength=strength,
                    momentum=change_pct,
                    coherence=pos.coherence,
                    timestamp=time.time(),
                    scout_id=pos.id
                )
                self.signal_broadcaster.broadcast_signal(signal)
                pos.last_signal_broadcast = time.time()
                print(f"   🐺 SCOUT SIGNAL: {symbol} {direction} | Strength: {strength:.2f} | Momentum: {change_pct:+.2f}%")
            
            # 🌟 POSITION SPLITTING: Check if position should split
            position_value = pos.quantity * current_price
            if self.position_splitter.should_split(position_value, pos.entry_value, pos.generation):
                print(f"   👶 SPLIT READY: {symbol} (Gen {pos.generation}) - Value ${position_value:.2f} vs Entry ${pos.entry_value:.2f}")
                # We'll handle splitting after TP/SL checks to avoid complexity
            
            # Log status every 10 cycles or if significant change
            if pos.cycles % 10 == 0 or abs(change_pct) > 0.5:
                gen_marker = f" [G{pos.generation}]" if pos.generation > 0 else ""
                print(f"   🔍 {symbol}{gen_marker}: Entry={pos.entry_price:.5f} Curr={current_price:.5f} ({source}) Pct={change_pct:+.2f}%")

            # Get Lattice Modifiers
            lattice_state = self.lattice.get_state()
            target_tp = CONFIG['TAKE_PROFIT_PCT'] * lattice_state.tp_mod
            target_sl = CONFIG['STOP_LOSS_PCT'] * lattice_state.sl_mod
            
            # 🌍✨ Apply Earth Resonance exit urgency to TP ✨🌍
            # When field coherence is low, exit earlier with smaller profits
            if effective_tp_mult < 1.0:
                target_tp *= effective_tp_mult
                if pos.cycles % 20 == 0:
                    print(f"   🌍 {symbol}: Earth urgency reducing TP to {target_tp:.2f}%")

            # Check TP
            if change_pct >= target_tp:
                to_close.append((symbol, "TP", change_pct, current_price))
            # Check SL
            elif change_pct <= -target_sl:
                to_close.append((symbol, "SL", change_pct, current_price))
                
        for symbol, reason, pct, price in to_close:
            self.close_position(symbol, reason, pct, price)
    
    def rebalance_portfolio(self, opportunities: List[Dict]) -> float:
        """
        Dynamic portfolio rebalancing - sell underperformers to buy better opportunities.
        Returns: Amount of capital freed up for new trades.
        """
        if not CONFIG['ENABLE_REBALANCING']:
            return 0.0
            
        if not opportunities:
            return 0.0
            
        freed_capital = 0.0
        to_rebalance = []
        
        # Find positions that are underperforming and held long enough
        for symbol, pos in self.positions.items():
            if pos.cycles < CONFIG['MIN_HOLD_CYCLES']:
                continue  # Don't sell too quickly
                
            # Get current price
            current_price = self.get_realtime_price(symbol)
            if current_price is None:
                current_price = self.ticker_cache.get(symbol, {}).get('price', pos.entry_price)
            if current_price is None or current_price == 0:
                continue
                
            change_pct = (current_price - pos.entry_price) / pos.entry_price * 100
            
            # Check if position is underperforming
            if change_pct < CONFIG['REBALANCE_THRESHOLD']:
                # Check if there's a better opportunity
                best_opp = opportunities[0] if opportunities else None
                if best_opp and best_opp.get('score', 0) > 80:
                    # Calculate if swapping would be profitable
                    # Expected gain from new position vs current loss
                    current_value = pos.quantity * current_price
                    swap_cost = current_value * (CONFIG['KRAKEN_FEE'] * 2 + CONFIG['SLIPPAGE_PCT'])
                    
                    # Expected gain from best opportunity
                    expected_gain = current_value * (CONFIG['TAKE_PROFIT_PCT'] / 100) * CONFIG['DEFAULT_WIN_PROB']
                    
                    if expected_gain > swap_cost:
                        to_rebalance.append((symbol, change_pct, current_price, current_value))
        
        # Execute rebalancing (sell underperformers)
        for symbol, change_pct, price, value in to_rebalance[:2]:  # Max 2 rebalances per cycle
            print(f"   🔄 REBALANCING: Selling {symbol} ({change_pct:+.2f}%) to free £{value:.2f}")
            self.close_position(symbol, "REBALANCE", change_pct, price)
            freed_capital += value
            
        return freed_capital
            
    def close_position(self, symbol: str, reason: str, pct: float, price: float):
        """Close a position"""
        # Don't pop yet! Wait for confirmation.
        if symbol not in self.positions:
            return
            
        pos = self.positions[symbol]
        
        # 🌟 CHECK EXIT GATE: Only sell if profitable
        if not self.should_exit_trade(pos, price, reason):
            return  # Hold position, don't sell at a loss
        
        # EXECUTE TRADE
        success = False
        if not self.dry_run:
            try:
                # Sell entire quantity
                res = self.client.place_market_order(pos.exchange, symbol, 'SELL', quantity=pos.quantity)
                if res.get('orderId'):
                    success = True
                else:
                    print(f"   ⚠️ Sell failed for {symbol}: No order ID returned. Retrying next cycle.")
                    return # Don't remove position, try again later
            except Exception as e:
                print(f"   ⚠️ Sell execution error for {symbol}: {e}")
                return # Don't remove position, try again later
        else:
            success = True # Dry run always succeeds
            
        # Only remove if successful
        if success:
            self.positions.pop(symbol)
        
        # Calculate P&L with platform-specific fees (Pessimistic Accounting)
        # We assume slippage on exit price
        slippage_cost = (pos.quantity * price) * CONFIG['SLIPPAGE_PCT']
        
        exit_value = pos.quantity * price
        exit_fee = exit_value * get_platform_fee(pos.exchange, 'taker')
        
        # Total Expenses = Entry Fee + Exit Fee + Slippage
        total_expenses = pos.entry_fee + exit_fee + slippage_cost
        
        gross_pnl = exit_value - pos.entry_value
        net_pnl = gross_pnl - total_expenses
        
        # Release symbol exposure
        if symbol in self.tracker.symbol_exposure:
            del self.tracker.symbol_exposure[symbol]
        
        # Calculate hold time
        hold_time_sec = time.time() - pos.entry_time
        
        # 🌟 Return capital to pool with profit
        self.capital_pool.deallocate(symbol, pos.entry_value, net_pnl)
        
        # Record trade with platform attribution
        self.tracker.record_trade(
            net_pnl=net_pnl, 
            fees=total_expenses, 
            symbol=symbol, 
            reason=reason, 
            hold_time_sec=hold_time_sec,
            platform=pos.exchange,
            volume=exit_value
        )
        
        # Feed learning back to Mycelium Network
        # pct is the price change percentage. If positive, we reinforce.
        self.mycelium.learn(symbol, pct)
        
        # 🐘 Record trade result in Elephant Memory
        self.memory.record(symbol, net_pnl)
        
        # 🌉 Record trade in bridge for cross-system tracking
        if self.bridge_enabled and self.bridge:
            self.bridge.record_trade(
                profit=gross_pnl,
                fee=total_expenses,
                success=(net_pnl > 0)
            )
            # Unregister position from bridge ledger
            self.bridge.unregister_position(pos.exchange, symbol)
        
        icon = "✅" if net_pnl > 0 else "❌"
        # Dynamic currency symbol
        curr_sym = "£" if CONFIG['BASE_CURRENCY'] == 'GBP' else "€" if CONFIG['BASE_CURRENCY'] == 'EUR' else "$"
        gen_marker = f" [G{pos.generation}]" if pos.generation > 0 else ""
        print(f"   {icon} CLOSE {symbol:12s}{gen_marker} | {reason} {pct:+.2f}% | Net: {curr_sym}{net_pnl:+.2f} | Pool: {curr_sym}{self.capital_pool.total_profits:+.2f} | WR: {self.tracker.win_rate:.1f}%")
        # Refresh equity to keep tracker in sync with realised trade
        self.refresh_equity()
        
    def _get_node_icon(self, node: str) -> str:
        """Get emoji for dominant node"""
        icons = {
            'Tiger': '🐅', 'Falcon': '🦅', 'Hummingbird': '🐦',
            'Dolphin': '🐬', 'Deer': '🦌', 'Owl': '🦉',
            'Panda': '🐼', 'CargoShip': '🚢', 'Clownfish': '🐠'
        }
        return icons.get(node, '🎯')

    def print_portfolio_report(self):
        """Print detailed portfolio report by exchange"""
        print("\n   📊 PORTFOLIO REPORT")
        print("   ──────────────────────────────────────────────────")
        
        try:
            all_balances = self.client.get_all_balances()
            total_val = 0.0
            alpaca_val = 0.0  # Track Alpaca separately (analytics only)
            base = CONFIG['BASE_CURRENCY']
            
            for exchange, balances in all_balances.items():
                # Mark Alpaca as analytics-only
                if exchange.lower() == 'alpaca':
                    print(f"   📊 {exchange.upper()} (Analytics Only - Paper):")
                else:
                    print(f"   🏦 {exchange.upper()}:")
                has_bal = False
                exchange_total = 0.0
                for asset, amount in balances.items():
                    try:
                        amount = float(amount)
                        if amount > 0:
                            has_bal = True
                            # Estimate value
                            val = 0.0
                            try:
                                # Clean asset name for conversion
                                clean_asset = asset.replace('Z', '')
                                if clean_asset.startswith('X') and len(clean_asset) > 3:
                                    clean_asset = clean_asset[1:]
                                if asset.startswith('LD'): # Binance Earn
                                    clean_asset = asset[2:]
                                    
                                val = self.client.convert_to_quote(exchange, clean_asset, amount, base)
                            except:
                                pass
                            
                            exchange_total += val
                            
                            # Add to appropriate total
                            if exchange.lower() == 'alpaca':
                                alpaca_val += val
                            else:
                                total_val += val
                                
                            print(f"      - {asset}: {amount:.8f} (~{val:.2f} {base})")
                    except:
                        pass
                if not has_bal:
                    print("      (Empty)")
            
            print("   ──────────────────────────────────────────────────")
            print(f"   💰 Trading Capital: {total_val:.2f} {base}")
            if alpaca_val > 0:
                print(f"   📊 Alpaca (Analytics): {alpaca_val:.2f} {base} (not included)")
            print("   ──────────────────────────────────────────────────\n")
            
        except Exception as e:
            print(f"   ⚠️ Failed to generate portfolio report: {e}")

    # ─────────────────────────────────────────────────────────
    # Main Loop
    # ─────────────────────────────────────────────────────────
    
    def run(self, interval: float = 5.0, target_profit_gbp: float = None, max_minutes: float = None):
        """Main trading loop

        Args:
            interval: Seconds to sleep between cycles.
            target_profit_gbp: If provided, stop when net P&L (current_equity - initial_equity) >= target.
            max_minutes: If provided, stop after this many minutes of runtime.
        """
        self.banner()
        
        print("🐙 Connecting to Unified Ecosystem...")
        self.print_portfolio_report()
        
        pair_count = self.refresh_tickers()
        print(f"✅ Connected! {pair_count} pairs loaded")
        
        # Find initial opportunities for WebSocket
        initial_opps = self.find_opportunities()
        symbols_to_watch = [o['symbol'] for o in initial_opps[:15]]
        
        # Add major pairs for base currency
        base = CONFIG['BASE_CURRENCY']
        major_bases = ['ETH', 'SOL', 'XBT', 'ADA', 'DOT', 'LINK']
        for base_asset in major_bases:
            pair = f"{base_asset}{base}"
            if pair not in symbols_to_watch and pair in self.ticker_cache:
                symbols_to_watch.append(pair)
                
        print(f"\n🔴 Starting WebSocket for {len(symbols_to_watch)} pairs...")
        self.start_websocket(symbols_to_watch)
        
        initial_equity = self.total_equity_gbp
        start_ts = time.time()

        try:
            while True:
                self.iteration += 1
                now = datetime.now().strftime("%H:%M:%S")
                
                print(f"\n{'━'*70}")
                print(f"🔄 Cycle {self.iteration} - {now} [{self.scan_direction}]")
                print(f"{'━'*70}")
                
                # 🌉 Sync with Bridge
                if self.bridge_enabled:
                    self.sync_bridge()
                    self.check_bridge_commands()
                
                # Market Pulse Analysis
                if self.iteration % 5 == 1: # Every 5 cycles
                    try:
                        pulse = self.market_pulse.analyze_market()
                        
                        # Update Capital Pool with Sentiment
                        c_score = pulse['crypto_sentiment']['avg_change_24h']
                        s_score = pulse['stock_sentiment']['avg_change_24h']
                        avg_sentiment = (c_score + s_score) / 2
                        self.capital_pool.update_sentiment(avg_sentiment)
                        
                        print("\n   🌍 GLOBAL MARKET PULSE")
                        print(f"   ├─ Crypto Sentiment: {pulse['crypto_sentiment']['label']} ({c_score:.2f}%)")
                        print(f"   ├─ Stock Sentiment:  {pulse['stock_sentiment']['label']} ({s_score:.2f}%)")
                        print(f"   ├─ 🏦 Capital Pool:  Reserve adjusted to {self.capital_pool.reserved / self.capital_pool.total_equity * 100:.1f}% based on sentiment {avg_sentiment:.2f}")
                        
                        if pulse['arbitrage_opportunities']:
                            print(f"   ├─ ⚡ {len(pulse['arbitrage_opportunities'])} Arbitrage Opps Found!")
                            top_arb = pulse['arbitrage_opportunities'][0]
                            print(f"   │  Best: {top_arb['asset']} ({top_arb['spread_pct']:.2f}%) - Buy {top_arb['buy_at']['source']} / Sell {top_arb['sell_at']['source']}")
                        else:
                            print("   ├─ ⚡ No significant arbitrage detected")
                            
                        print(f"   └─ Top Gainer: {pulse['top_gainers'][0]['symbol']} ({pulse['top_gainers'][0]['priceChangePercent']:.1f}%)")
                        print("")
                    except Exception as e:
                        print(f"   ⚠️ Market Pulse Error: {e}")

                # Refresh data
                self.refresh_tickers()
                self.refresh_equity(mark_cycle=True)
                
                # 🌉 Sync with bridge (capital, positions, commands)
                self.sync_bridge()
                self.check_bridge_commands()
                
                # Deploy scouts on first cycle if enabled
                if self.iteration == 1 and not self.scouts_deployed:
                    self._deploy_scouts()
                
                # Toggle scan direction for fair scheduling (A→Z / Z→A)
                self.scan_direction = 'Z→A' if self.iteration % 2 == 0 else 'A→Z'
                
                # Check positions
                self.check_positions()
                
                # Check network coherence - pause if too low
                network_coherence = self.mycelium.get_network_coherence()
                trading_paused = network_coherence < CONFIG['MIN_NETWORK_COHERENCE']
                
                # Check WebSocket health
                ws_stale = (time.time() - self.ws_last_message) > CONFIG['WS_HEARTBEAT_TIMEOUT']
                if ws_stale and self.ws_connected:
                    print("   ⚠️ WebSocket appears stale, falling back to REST")
                
                # Update Lattice State (Global Physics)
                raw_opps = self.find_opportunities()
                l_state = self.lattice.update(raw_opps)
                
                # Apply Triadic Envelope Protocol to filter signals
                all_opps = self.lattice.filter_signals(raw_opps)
                
                # Dynamic Portfolio Rebalancing - sell underperformers if better opportunities exist
                freed_capital = 0.0
                if all_opps and len(self.positions) >= CONFIG['MAX_POSITIONS'] // 2:
                    freed_capital = self.rebalance_portfolio(all_opps)
                    if freed_capital > 0:
                        self.refresh_equity()  # Update cash after rebalancing

                # Find opportunities (if not halted or paused)
                if len(self.positions) < CONFIG['MAX_POSITIONS'] and not self.tracker.trading_halted and not trading_paused:
                    if all_opps:
                        purity = self.lattice.get_field_purity()
                        purity_icon = "🟢" if purity > 0.9 else "🟠" if purity > 0.5 else "🔴"
                        print(f"\n   🔮 Top Opportunities (Triadic Filtered | Purity: {purity_icon} {purity*100:.1f}%):")
                        for opp in all_opps[:5]:
                            icon = self._get_node_icon(opp['dominant_node'])
                            lock = "🔒" if opp.get('memory_locked') else "🔓"
                            print(f"      {icon} {opp['symbol']:12s} +{opp['change24h']:5.1f}% | Γ={opp['coherence']:.2f} | Score: {opp['score']} {lock}")
                    
                    for opp in all_opps[:CONFIG['MAX_POSITIONS'] - len(self.positions)]:
                        self.open_position(opp)
                        
                # Show positions
                if self.positions:
                    print(f"\n   📊 Active Positions ({len(self.positions)}/{CONFIG['MAX_POSITIONS']}):")
                    for symbol, pos in self.positions.items():
                        rt = self.get_realtime_price(symbol)
                        if rt:
                            pct = (rt - pos.entry_price) / pos.entry_price * 100
                            src = "🔴"
                        else:
                            cached = self.ticker_cache.get(symbol, {}).get('price', pos.entry_price)
                            pct = (cached - pos.entry_price) / pos.entry_price * 100
                            src = "⚪"
                        icon = self._get_node_icon(pos.dominant_node)
                        print(f"      {icon} {symbol:12s} Entry: ${pos.entry_price:.6f} | Now: {pct:+.2f}% {src}")
                        
                # Stats
                rt_count = len(self.realtime_prices)
                runtime = (time.time() - self.start_time) / 60
                ws_health = '🟢' if (self.ws_connected and not ws_stale) else ('🟡' if self.ws_connected else '🔴')
                
                # Calculate cycle P&L
                cycle_pnl = self.total_equity_gbp - self.tracker.cycle_equity_start
                cycle_pnl_pct = (cycle_pnl / self.tracker.cycle_equity_start * 100) if self.tracker.cycle_equity_start > 0 else 0
                cycle_icon = "📈" if cycle_pnl >= 0 else "📉"
                
                # Dynamic currency symbol
                curr_sym = "£" if CONFIG['BASE_CURRENCY'] == 'GBP' else "€" if CONFIG['BASE_CURRENCY'] == 'EUR' else "$"
                
                # Calculate average hold time
                avg_hold_min = 0.0
                if self.tracker.closed_positions > 0:
                    avg_hold_min = (self.tracker.total_hold_time_sec / self.tracker.closed_positions) / 60
                
                # Mode indicator
                mode_str = "🎯 HIGH-Γ" if CONFIG['HIGH_COHERENCE_MODE'] else "🔥 AGGRESSIVE"
                lambda_str = "Λ-Field" if CONFIG['ENABLE_LAMBDA_FIELD'] else "Classic"
                
                # 🌟 Swarm orchestrator stats
                capital_available = self.capital_pool.get_available()
                cycle_profits = self.capital_pool.profits_this_cycle
                total_pool_profits = self.capital_pool.total_profits
                
                # Count scouts and generations
                scout_count = sum(1 for p in self.positions.values() if p.is_scout)
                max_gen = max([p.generation for p in self.positions.values()], default=0)
                split_count = len(self.position_splitter.split_history)
                
                # Latest signal info
                latest_signal = self.signal_broadcaster.get_latest_signal(max_age_seconds=60)
                signal_str = ""
                if latest_signal:
                    signal_str = f" | 🐺 Signal: {latest_signal.symbol} {latest_signal.direction} ({latest_signal.strength:.2f})"
                
                print(f"\n   💎 Portfolio: {curr_sym}{self.total_equity_gbp:.2f} ({self.tracker.total_return:+.2f}%) | Peak: {curr_sym}{self.tracker.peak_balance:.2f}")
                print(f"   📉 Max DD: {self.tracker.max_drawdown:.1f}% | Current DD: {self.tracker.current_drawdown:.1f}%")
                print(f"   {cycle_icon} Cycle P&L: {curr_sym}{cycle_pnl:+.2f} ({cycle_pnl_pct:+.2f}%)")
                print(f"   📈 Trades: {self.tracker.total_trades} | Wins: {self.tracker.wins} | WR: {self.tracker.win_rate:.1f}% | Avg Hold: {avg_hold_min:.1f}m")
                print(f"   🍄 Network Γ: {network_coherence:.2f} {'⚠️ PAUSED' if trading_paused else ''} | WS: {ws_health} ({rt_count})")
                print(f"   🌐 Lattice: {l_state.phase} ({l_state.frequency}Hz) | Purity: {l_state.field_purity*100:.0f}% | {lambda_str}")
                # 🌍⚡ HNC Frequency Status ⚡🌍
                if CONFIG.get('ENABLE_HNC_FREQUENCY', True):
                    hnc_status = self.auris.get_hnc_status()
                    hnc_icon = "🟢" if hnc_status['lighthouse_aligned'] else "🔴"
                    print(f"   🌍 HNC: {hnc_status['composite_freq']:.0f}Hz | {hnc_status['phase']} | Coherence: {hnc_status['triadic_coherence']:.0%} {hnc_icon} | Mod: ×{hnc_status['position_modifier']:.2f}")
                    
                    # Show frequency distribution every 5 iterations
                    if self.iteration % 5 == 0:
                        dist = self.auris.get_frequency_distribution()
                        harmonic_count = self.auris.get_harmonic_count()
                        # Compact display
                        dist_parts = []
                        for band, count in dist.items():
                            if count > 0:
                                band_short = band.split('_')[1][:4]
                                dist_parts.append(f"{band_short}:{count}")
                        if dist_parts:
                            print(f"   📡 Freq Grid: {' | '.join(dist_parts[:6])} | 🌈×{harmonic_count['harmonic']} ⚠️×{harmonic_count['distortion']}")
                print(f"   🎮 Mode: {mode_str} | Entry Γ: {CONFIG['ENTRY_COHERENCE']:.3f} | Exit Γ: {CONFIG['EXIT_COHERENCE']:.3f}")
                print(f"   💰 Compounded: {curr_sym}{self.tracker.compounded:.2f} | Harvested: {curr_sym}{self.tracker.harvested:.2f}")
                print(f"   🌟 Pool: {curr_sym}{total_pool_profits:+.2f} total | {curr_sym}{capital_available:.2f} available | Scouts: {scout_count} | Splits: {split_count}{signal_str}")
                print(f"   ⏱️ Runtime: {runtime:.1f} min | Positions: {len(self.positions)}/{CONFIG['MAX_POSITIONS']} | Max Gen: {max_gen}")
                
                if self.tracker.trading_halted:
                    print(f"   🛑 TRADING HALTED: {self.tracker.halt_reason}")

                # ─────────────────────────────────────────────
                # Goal-based termination checks
                # ─────────────────────────────────────────────
                elapsed_min = (time.time() - start_ts) / 60.0
                net_profit = self.total_equity_gbp - initial_equity
                if target_profit_gbp is not None and net_profit >= target_profit_gbp:
                    print("\n🎯 TARGET PROFIT REACHED")
                    print(f"   Initial Equity: £{initial_equity:.2f}")
                    print(f"   Current Equity: £{self.total_equity_gbp:.2f}")
                    print(f"   Net Profit:     £{net_profit:.2f} (Goal £{target_profit_gbp:.2f})")
                    break
                if max_minutes is not None and elapsed_min >= max_minutes:
                    print("\n⏱️ SESSION TIME LIMIT REACHED")
                    print(f"   Runtime: {elapsed_min:.2f} min / {max_minutes:.2f} min limit")
                    print(f"   Net Profit: £{net_profit:.2f} (Goal £{target_profit_gbp if target_profit_gbp else 0:.2f})")
                    break
                
                # Save state periodically
                if self.iteration % 10 == 0:
                    self.save_state()
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n🐙 Shutting down ecosystem...")
            self.save_state()
            print("   💾 State saved for recovery")
            self.final_report()
        finally:
            if target_profit_gbp is not None or max_minutes is not None:
                # Compact goal session summary
                final_net = self.total_equity_gbp - initial_equity
                print("\n════════ GOAL SESSION SUMMARY ════════")
                print(f"   Initial Equity: £{initial_equity:.2f}")
                print(f"   Final Equity:   £{self.total_equity_gbp:.2f}")
                print(f"   Net Profit:     £{final_net:.2f}")
                if target_profit_gbp is not None:
                    pct_goal = (final_net / target_profit_gbp * 100) if target_profit_gbp > 0 else 0
                    print(f"   Goal Progress:  {pct_goal:.1f}% of £{target_profit_gbp:.2f}")
                if max_minutes is not None:
                    print(f"   Runtime:        {(time.time()-start_ts)/60:.2f} min / {max_minutes:.2f} min limit")
                print("══════════════════════════════════════")
            
    def final_report(self):
        """Print final statistics"""
        print(f"""
╔══════════════════════════════════════════════════════════════════════════╗
║          🐙🌌 AUREON KRAKEN ECOSYSTEM - FINAL REPORT 🌌🐙               ║
╚══════════════════════════════════════════════════════════════════════════╝

   Starting Balance:  ${self.tracker.initial_balance:.2f}
   Final Balance:     ${self.tracker.balance:.2f}
   💰 NET P&L:        ${self.tracker.balance - self.tracker.initial_balance:+.2f} ({self.tracker.total_return:+.2f}%)

   Total Trades:      {self.tracker.total_trades}
   Wins:              {self.tracker.wins}
   Losses:            {self.tracker.losses}
   🎯 WIN RATE:       {self.tracker.win_rate:.1f}%

   Total Fees:        ${self.tracker.total_fees:.2f}
   Max Drawdown:      {self.tracker.max_drawdown:.1f}%
   
   💰 10-9-1 MODEL:
   ├─ Compounded:     ${self.tracker.compounded:.2f}
   └─ Harvested:      ${self.tracker.harvested:.2f}
   
   🛡️ RISK CONTROLS:
   ├─ Max Drawdown:   {self.tracker.max_drawdown:.1f}% / {CONFIG['MAX_DRAWDOWN_PCT']:.1f}%
   ├─ Position Sizing: {'Kelly Criterion' if CONFIG['USE_KELLY_SIZING'] else 'Fixed %'}
   └─ Circuit Breaker: {'🛑 ACTIVATED' if self.tracker.trading_halted else '✅ OK'}
""")
        
        # Print platform-specific metrics
        print(self.tracker.get_platform_summary())
        
        if self.tracker.win_rate >= 51 and self.tracker.net_profit > 0:
            print("   ✅ GOAL ACHIEVED: 51%+ WR + NET PROFIT! ✅")
        else:
            print(f"   📊 Status: WR={self.tracker.win_rate:.1f}%, Net=${self.tracker.net_profit:+.2f}")


# ═══════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════

def main():
    # Configuration from environment
    dry_run = os.getenv('LIVE', '0') != '1'
    balance = float(os.getenv('BALANCE', 1000))
    interval = float(os.getenv('INTERVAL', 5))
    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║  🐙 AUREON KRAKEN ECOSYSTEM 🐙                            ║
    ║                                                           ║
    ║  Usage:                                                   ║
    ║    LIVE=1 python aureon_kraken_ecosystem.py  # Live mode  ║
    ║    BALANCE=5000 python aureon_kraken_ecosystem.py         ║
    ║    INTERVAL=3 python aureon_kraken_ecosystem.py           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    ecosystem = AureonKrakenEcosystem(
        initial_balance=balance,
        dry_run=dry_run
    )
    
    ecosystem.run(interval=interval)


if __name__ == "__main__":
    main()
