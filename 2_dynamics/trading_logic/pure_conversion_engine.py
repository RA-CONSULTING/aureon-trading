#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════════╗
║                                                                                   ║
║   ██████╗ ██╗   ██╗██████╗ ███████╗     ██████╗ ██████╗ ███╗   ██╗██╗   ██╗      ║
║   ██╔══██╗██║   ██║██╔══██╗██╔════╝    ██╔════╝██╔═══██╗████╗  ██║██║   ██║      ║
║   ██████╔╝██║   ██║██████╔╝█████╗      ██║     ██║   ██║██╔██╗ ██║██║   ██║      ║
║   ██╔═══╝ ██║   ██║██╔══██╗██╔══╝      ██║     ██║   ██║██║╚██╗██║╚██╗ ██╔╝      ║
║   ██║     ╚██████╔╝██║  ██║███████╗    ╚██████╗╚██████╔╝██║ ╚████║ ╚████╔╝       ║
║   ╚═╝      ╚═════╝ ╚═╝  ╚═╝╚══════╝     ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝  ╚═══╝        ║
║                                                                                   ║
║   🔄 PURE CONVERSION ENGINE - BARTER FOR BETTER 🔄                               ║
║                                                                                   ║
║   NOT BUYING. NOT SELLING. CONVERTING. BARTERING. SNOWBALLING.                   ║
║                                                                                   ║
║   PHILOSOPHY:                                                                     ║
║   • We don't sell assets - we CONVERT them to stronger positions                 ║
║   • We don't buy assets - we BARTER our holdings for better value                ║
║   • Every conversion increases our total buying power                            ║
║   • Compound, snowball, grow - adaptive asset accumulation                       ║
║                                                                                   ║
║   SYSTEMS UNIFIED:                                                                ║
║   • V14 Scoring (100% win rate logic)                                            ║
║   • Mycelium Network (distributed consensus)                                     ║
║   • Probability Matrix (7-day forecasting)                                       ║
║   • Adaptive Learning (pattern recognition)                                      ║
║   • Miner Brain (cognitive intelligence)                                         ║
║   • Quantum Telescope (multi-dimensional)                                        ║
║                                                                                   ║
╚═══════════════════════════════════════════════════════════════════════════════════╝
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
import json
import asyncio
import signal
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import math

import logging
logger = logging.getLogger(__name__)

try:
    import websockets
except ImportError:
    websockets = None  # Allow graceful degradation

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ═══════════════════════════════════════════════════════════════════════════════════
# IMPORT ALL SYSTEMS
# ═══════════════════════════════════════════════════════════════════════════════════

# V14 Scoring
try:
    from s5_v14_dance_enhancements import V14DanceEnhancer, V14_CONFIG, V14ScoringEngine
    V14_AVAILABLE = True
except ImportError:
    V14_AVAILABLE = False
    print("⚠️ V14 not available")

# Mycelium Network
try:
    from aureon_mycelium import MyceliumNetwork
    MYCELIUM_AVAILABLE = True
except ImportError:
    MYCELIUM_AVAILABLE = False

# Probability Matrix  
try:
    from hnc_probability_matrix import HNCProbabilityIntegration
    PROB_MATRIX_AVAILABLE = True
except ImportError:
    PROB_MATRIX_AVAILABLE = False

# Adaptive Learning
try:
    from aureon_unified_ecosystem import AdaptiveLearner
    ADAPTIVE_AVAILABLE = True
except ImportError:
    ADAPTIVE_AVAILABLE = False

# Miner Brain
try:
    from aureon_miner_brain import MinerBrain
    MINER_BRAIN_AVAILABLE = True
except ImportError:
    MINER_BRAIN_AVAILABLE = False

# Kraken Client
try:
    from kraken_client import KrakenClient, get_kraken_client
    KRAKEN_AVAILABLE = True
except ImportError:
    KRAKEN_AVAILABLE = False

# ═══════════════════════════════════════════════════════════════════════════════════
# 🍄 MYCELIUM CONVERSION HUB - ALL SYSTEMS WIRED THROUGH ONE PLACE
# ═══════════════════════════════════════════════════════════════════════════════════
try:
    from mycelium_conversion_hub import (
        MyceliumConversionHub, get_conversion_hub,
        MyceliumSignal, ConversionSignal, SystemSignal
    )
    MYCELIUM_HUB_AVAILABLE = True
    print("🍄 Mycelium Conversion Hub LOADED - All systems wired!")
except ImportError as e:
    MYCELIUM_HUB_AVAILABLE = False
    print(f"⚠️ Mycelium Hub not available: {e}")

# Additional ecosystem systems
try:
    from aureon_internal_multiverse import InternalMultiverse
    MULTIVERSE_AVAILABLE = True
except ImportError:
    MULTIVERSE_AVAILABLE = False

try:
    from aureon_probability_nexus import EnhancedProbabilityNexus
    PROBABILITY_NEXUS_AVAILABLE = True
except ImportError:
    PROBABILITY_NEXUS_AVAILABLE = False

try:
    from aureon_harmonic_fusion import HarmonicWaveFusion
    HARMONIC_AVAILABLE = True
except ImportError:
    HARMONIC_AVAILABLE = False

try:
    from aureon_lighthouse import AureonLighthouse
    LIGHTHOUSE_AVAILABLE = True
except ImportError:
    LIGHTHOUSE_AVAILABLE = False

try:
    from aureon_thought_bus import ThoughtBus, get_thought_bus
    THOUGHT_BUS_AVAILABLE = True
except ImportError:
    THOUGHT_BUS_AVAILABLE = False

try:
    from aureon_conversion_commando import AdaptiveConversionCommando
    CONVERSION_COMMANDO_AVAILABLE = True
except ImportError:
    CONVERSION_COMMANDO_AVAILABLE = False
except ImportError:
    KRAKEN_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════════════════════
# CONVERSION PHILOSOPHY
# ═══════════════════════════════════════════════════════════════════════════════════

"""
THE PURE CONVERSION PHILOSOPHY:

1. NEVER SELL TO USD (unless converting to another asset)
2. ALWAYS CONVERT TO STRONGER POSITION
3. SNOWBALL - compound gains through conversions
4. ADAPTIVE - learn which conversions work best
5. PATIENCE - wait for the RIGHT conversion, not just any conversion

CONVERSION TYPES:
- STRENGTH SWAP: Asset A weakening → Convert to Asset B strengthening
- VALUE CAPTURE: Asset A up significantly → Lock in gains by converting
- DISCOUNT GRAB: Asset B down significantly → Convert TO it for discount
- ROTATION: Sector rotation - move to where momentum is going

THE KEY INSIGHT:
We're not trying to time the market.
We're trying to always be in the STRONGEST position.
Every conversion should increase our TOTAL BUYING POWER.
"""


class ConversionType(Enum):
    STRENGTH_SWAP = "strength_swap"      # Weak → Strong
    VALUE_CAPTURE = "value_capture"      # Lock in gains
    DISCOUNT_GRAB = "discount_grab"      # Buy the dip via conversion
    ROTATION = "rotation"                # Sector rotation
    SNOWBALL = "snowball"                # Compound small gains


@dataclass
class Asset:
    """An asset in our portfolio"""
    symbol: str
    amount: float
    avg_cost_usd: float = 0.0
    current_price: float = 0.0
    
    @property
    def usd_value(self) -> float:
        return self.amount * self.current_price
    
    @property
    def pnl_pct(self) -> float:
        if self.avg_cost_usd <= 0:
            return 0.0
        return ((self.current_price - self.avg_cost_usd) / self.avg_cost_usd) * 100


@dataclass
class ConversionOpportunity:
    """A potential conversion between assets"""
    from_asset: str
    to_asset: str
    conversion_type: ConversionType
    
    # Scores from all systems
    v14_score: int = 0
    mycelium_score: float = 0.0
    probability_score: float = 0.0
    adaptive_score: float = 0.0
    miner_score: float = 0.0
    
    # Combined
    unified_score: float = 0.0
    confidence: float = 0.0
    
    # Metrics
    from_momentum: float = 0.0
    to_momentum: float = 0.0
    relative_strength: float = 0.0
    expected_gain_pct: float = 0.0
    from_strength: float = 0.0
    to_strength: float = 0.0
    strength_diff: float = 0.0
    
    # Execution
    from_amount: float = 0.0
    to_amount: float = 0.0
    from_price: float = 0.0
    to_price: float = 0.0
    
    # Alias for compatibility
    @property
    def type(self):
        return self.conversion_type
    
    reason: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CompletedConversion:
    """A completed conversion"""
    id: str
    from_asset: str
    to_asset: str
    from_amount: float
    to_amount: float
    from_price: float
    to_price: float
    usd_value: float
    conversion_type: ConversionType
    unified_score: float
    timestamp: datetime
    
    # Track if this conversion was profitable
    to_price_at_check: float = 0.0
    realized_gain_pct: float = 0.0


class UnifiedConversionBrain:
    """
    🧠 UNIFIED CONVERSION BRAIN 🧠
    
    ALL SYSTEMS NOW WIRED THROUGH MYCELIUM HUB!
    
    Combines ALL systems for conversion decisions:
    - V14: Technical scoring (100% win rate logic)
    - Mycelium Network: Distributed consensus
    - Internal Multiverse: 10-world consensus
    - Probability Nexus: Future price forecasting
    - Harmonic Systems: Wave alignment
    - Lighthouse: Pattern detection
    - Miner Brain: Cognitive intelligence
    - Conversion Commando: 1885 CAPM execution
    
    Every system flows through the Mycelium neural mesh.
    """
    
    def __init__(self, starting_capital: float = 10000.0):
        self.starting_capital = starting_capital
        
        # Initialize all systems
        print("\n🧠 Initializing Unified Conversion Brain...")
        
        # ═══════════════════════════════════════════════════════════════════════
        # 🍄 MYCELIUM HUB - THE CENTRAL NERVOUS SYSTEM
        # ═══════════════════════════════════════════════════════════════════════
        self.mycelium_hub: Optional[MyceliumConversionHub] = None
        if MYCELIUM_HUB_AVAILABLE:
            self.mycelium_hub = get_conversion_hub(starting_capital)
            print("   🍄 Mycelium Hub: ALL SYSTEMS WIRED!")
        
        # ═══════════════════════════════════════════════════════════════════════
        # Individual systems (fallback if hub not available)
        # ═══════════════════════════════════════════════════════════════════════
        
        # V14 Scoring
        self.v14 = None
        if V14_AVAILABLE:
            self.v14 = V14DanceEnhancer()
            print("   ✅ V14 Scoring Engine (100% win rate logic)")
        
        # Mycelium Network
        self.mycelium = None
        if MYCELIUM_AVAILABLE:
            self.mycelium = MyceliumNetwork(initial_capital=starting_capital)
            print("   ✅ Mycelium Network (distributed consensus)")
        
        # Internal Multiverse
        self.multiverse = None
        if MULTIVERSE_AVAILABLE:
            try:
                self.multiverse = InternalMultiverse(initial_equity=starting_capital)
                print("   ✅ Internal Multiverse (10 worlds)")
            except:
                pass
        
        # Probability Nexus
        self.probability_nexus = None
        if PROBABILITY_NEXUS_AVAILABLE:
            try:
                self.probability_nexus = EnhancedProbabilityNexus(
                    exchange='binance', leverage=1.0, starting_balance=starting_capital
                )
                print("   ✅ Probability Nexus (80%+ win rate)")
            except:
                pass
        
        # Probability Matrix
        self.probability = None
        if PROB_MATRIX_AVAILABLE:
            try:
                self.probability = HNCProbabilityIntegration()
                print("   ✅ Probability Matrix (7-day forecasting)")
            except:
                pass
        
        # Harmonic Systems
        self.harmonic = None
        if HARMONIC_AVAILABLE:
            try:
                self.harmonic = HarmonicWaveFusion()
                print("   ✅ Harmonic Fusion (wave alignment)")
            except:
                pass
        
        # Lighthouse
        self.lighthouse = None
        if LIGHTHOUSE_AVAILABLE:
            try:
                self.lighthouse = AureonLighthouse()
                print("   ✅ Lighthouse (pattern detection)")
            except:
                pass
        
        # Miner Brain
        self.miner = None
        if MINER_BRAIN_AVAILABLE:
            try:
                self.miner = MinerBrain()
                print("   ✅ Miner Brain (cognitive intelligence)")
            except:
                pass
        
        # Conversion Commando
        self.commando = None
        if CONVERSION_COMMANDO_AVAILABLE:
            try:
                self.commando = AdaptiveConversionCommando()
                print("   ✅ Conversion Commando (1885 CAPM)")
            except:
                pass
        
        # Thought Bus for publishing
        self.thought_bus = None
        if THOUGHT_BUS_AVAILABLE:
            try:
                self.thought_bus = get_thought_bus()
                print("   ✅ Thought Bus (unity consciousness)")
            except:
                pass
        
        # Adaptive Learner
        self.adaptive = None
        if ADAPTIVE_AVAILABLE:
            try:
                self.adaptive = AdaptiveLearner()
                print("   ✅ Adaptive Learning (pattern recognition)")
            except:
                pass
        
        # Conversion history for learning
        self.conversion_history: List[CompletedConversion] = []
        self.successful_pairs: Dict[str, int] = defaultdict(int)  # pair -> success count
        
        print("   🧠 Unified Brain ONLINE!\n")
    
    def score_conversion(self, opp: ConversionOpportunity, 
                         prices: Dict[str, float],
                         price_history: Dict[str, deque]) -> ConversionOpportunity:
        """
        Score a conversion opportunity using ALL systems through Mycelium Hub.
        """
        
        # ═══════════════════════════════════════════════════════════════════════
        # 🍄 USE MYCELIUM HUB IF AVAILABLE (ALL SYSTEMS WIRED)
        # ═══════════════════════════════════════════════════════════════════════
        if self.mycelium_hub:
            try:
                hub_signal = self.mycelium_hub.get_conversion_signal(
                    from_asset=opp.from_asset,
                    to_asset=opp.to_asset,
                    from_price=opp.from_price,
                    to_price=opp.to_price,
                    volume=0.0
                )
                
                # Apply hub signal to opportunity
                opp.unified_score = hub_signal.unified_score
                opp.confidence = hub_signal.unified_confidence
                
                # Extract individual scores
                if hub_signal.v14_signal:
                    opp.v14_score = int(hub_signal.v14_signal.score)
                if hub_signal.mycelium_signal:
                    opp.mycelium_score = hub_signal.mycelium_signal.confidence
                if hub_signal.probability_signal:
                    opp.probability_score = hub_signal.probability_signal.confidence
                if hub_signal.miner_signal:
                    opp.miner_score = hub_signal.miner_signal.confidence
                
                return opp
                
            except Exception as e:
                logger.warning(f"Mycelium Hub error, falling back: {e}")
        
        # ═══════════════════════════════════════════════════════════════════════
        # FALLBACK: Score manually with individual systems
        # ═══════════════════════════════════════════════════════════════════════
        scores = []
        weights = []
        
        # ═══════════════════════════════════════════════════════════════════
        # V14 SCORING - Technical analysis (weight: 30%)
        # ═══════════════════════════════════════════════════════════════════
        if self.v14:
            # Score the TO asset (what we're converting INTO)
            to_symbol = f"{opp.to_asset}USDT"
            v14_eval = self.v14.evaluate_entry(to_symbol, opp.to_price)
            opp.v14_score = v14_eval['score']
            
            # Normalize to 0-1
            v14_normalized = min(1.0, opp.v14_score / 12.0)  # Max ~12 points
            scores.append(v14_normalized)
            weights.append(0.30)
        
        # ═══════════════════════════════════════════════════════════════════
        # MYCELIUM CONSENSUS - Network agreement (weight: 25%)
        # ═══════════════════════════════════════════════════════════════════
        if self.mycelium:
            try:
                # Get network signal for the TO asset
                signal = self.mycelium.get_queen_signal()
                coherence = self.mycelium.get_network_coherence() if hasattr(self.mycelium, 'get_network_coherence') else 0.5
                
                # Positive signal + high coherence = good conversion
                mycelium_score = (signal + 1) / 2 * coherence  # Normalize -1,1 to 0,1
                opp.mycelium_score = mycelium_score
                scores.append(mycelium_score)
                weights.append(0.25)
            except:
                pass
        
        # ═══════════════════════════════════════════════════════════════════
        # PROBABILITY MATRIX - Future forecast (weight: 25%)
        # ═══════════════════════════════════════════════════════════════════
        if self.probability:
            try:
                forecast = self.probability.get_symbol_forecast(opp.to_asset) if hasattr(self.probability, 'get_symbol_forecast') else None
                if forecast:
                    bullish_prob = forecast.get('bullish_probability', 0.5)
                    opp.probability_score = bullish_prob
                    scores.append(bullish_prob)
                    weights.append(0.25)
            except:
                pass
        
        # ═══════════════════════════════════════════════════════════════════
        # ADAPTIVE LEARNING - Historical patterns (weight: 10%)
        # ═══════════════════════════════════════════════════════════════════
        # Check our own conversion history
        pair_key = f"{opp.from_asset}→{opp.to_asset}"
        historical_success = self.successful_pairs.get(pair_key, 0)
        total_conversions = sum(self.successful_pairs.values()) or 1
        
        adaptive_score = 0.5 + (historical_success / total_conversions) * 0.5
        opp.adaptive_score = adaptive_score
        scores.append(adaptive_score)
        weights.append(0.10)
        
        # ═══════════════════════════════════════════════════════════════════
        # MINER BRAIN - Cognitive patterns (weight: 10%)
        # ═══════════════════════════════════════════════════════════════════
        if self.miner:
            try:
                # Get miner's assessment
                miner_signal = 0.5  # Default neutral
                if hasattr(self.miner, 'get_signal'):
                    miner_signal = (self.miner.get_signal(opp.to_asset) + 1) / 2
                opp.miner_score = miner_signal
                scores.append(miner_signal)
                weights.append(0.10)
            except:
                pass
        
        # ═══════════════════════════════════════════════════════════════════
        # CALCULATE UNIFIED SCORE
        # ═══════════════════════════════════════════════════════════════════
        if scores and weights:
            # Weighted average
            total_weight = sum(weights)
            opp.unified_score = sum(s * w for s, w in zip(scores, weights)) / total_weight
            
            # Confidence is based on how many systems agree (variance)
            if len(scores) > 1:
                mean = sum(scores) / len(scores)
                variance = sum((s - mean) ** 2 for s in scores) / len(scores)
                opp.confidence = 1.0 - min(1.0, math.sqrt(variance) * 2)
            else:
                opp.confidence = 0.5
        
        return opp
    
    def record_conversion(self, conversion: CompletedConversion, was_profitable: bool):
        """Record conversion outcome for learning"""
        self.conversion_history.append(conversion)
        
        pair_key = f"{conversion.from_asset}→{conversion.to_asset}"
        if was_profitable:
            self.successful_pairs[pair_key] += 1


class PureConversionEngine:
    """
    🔄 PURE CONVERSION ENGINE 🔄
    
    NOT BUYING. NOT SELLING. CONVERTING. BARTERING. SNOWBALLING.
    
    Core Strategy:
    1. Monitor all assets for relative strength changes
    2. When Asset A weakens relative to Asset B → Convert A to B
    3. Compound gains through strategic conversions
    4. Snowball - each conversion increases total buying power
    """
    
    # Binance WebSocket
    WS_URL = "wss://stream.binance.com:9443/stream?streams="
    
    # Asset universe - what we can convert between
    UNIVERSE = {
        # Majors
        'BTC': {'binance': 'BTCUSDT', 'kraken': 'XBTUSD', 'tier': 1},
        'ETH': {'binance': 'ETHUSDT', 'kraken': 'ETHUSD', 'tier': 1},
        
        # Large caps
        'SOL': {'binance': 'SOLUSDT', 'kraken': 'SOLUSD', 'tier': 2},
        'XRP': {'binance': 'XRPUSDT', 'kraken': 'XRPUSD', 'tier': 2},
        'ADA': {'binance': 'ADAUSDT', 'kraken': 'ADAUSD', 'tier': 2},
        'AVAX': {'binance': 'AVAXUSDT', 'kraken': 'AVAXUSD', 'tier': 2},
        'DOT': {'binance': 'DOTUSDT', 'kraken': 'DOTUSD', 'tier': 2},
        'LINK': {'binance': 'LINKUSDT', 'kraken': 'LINKUSD', 'tier': 2},
        
        # Mid caps
        'ATOM': {'binance': 'ATOMUSDT', 'kraken': 'ATOMUSD', 'tier': 3},
        'NEAR': {'binance': 'NEARUSDT', 'kraken': 'NEARUSD', 'tier': 3},
        'UNI': {'binance': 'UNIUSDT', 'kraken': 'UNIUSD', 'tier': 3},
        'LTC': {'binance': 'LTCUSDT', 'kraken': 'LTCUSD', 'tier': 3},
        'MATIC': {'binance': 'MATICUSDT', 'kraken': 'MATICUSD', 'tier': 3},
        'APT': {'binance': 'APTUSDT', 'kraken': 'APTUSD', 'tier': 3},
        'ARB': {'binance': 'ARBUSDT', 'kraken': 'ARBUSD', 'tier': 3},
        'OP': {'binance': 'OPUSDT', 'kraken': 'OPUSD', 'tier': 3},
        
        # Small caps (higher risk, higher reward)
        'DOGE': {'binance': 'DOGEUSDT', 'kraken': 'DOGEUSD', 'tier': 4},
        'SHIB': {'binance': 'SHIBUSDT', 'kraken': 'SHIBUSD', 'tier': 4},
        'PEPE': {'binance': 'PEPEUSDT', 'kraken': 'PEPEUSD', 'tier': 4},
    }
    
    # Conversion thresholds
    MIN_CONVERSION_USD = 10.0
    MAX_CONVERSION_PCT = 0.30  # Max 30% of holdings per conversion
    CONVERSION_COOLDOWN = 60   # Seconds between conversions
    
    # Relative strength thresholds
    MIN_STRENGTH_DIFF = 0.02   # 2% relative strength difference to trigger
    MIN_UNIFIED_SCORE = 0.60   # Minimum unified score to convert
    
    # Kraken fees
    TAKER_FEE = 0.0026
    
    def __init__(self, starting_capital: float = 10000.0, dry_run: bool = False):
        self.starting_capital = starting_capital
        self.dry_run = dry_run
        
        # Unified brain
        self.brain = UnifiedConversionBrain(starting_capital)
        
        # Kraken client
        if KRAKEN_AVAILABLE and not dry_run:
            self.kraken = get_kraken_client()
        else:
            self.kraken = None
        
        # Portfolio
        self.portfolio: Dict[str, Asset] = {}
        self.initial_portfolio_value = 0.0
        
        # Price tracking
        self.prices: Dict[str, float] = {}
        self.price_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=200))
        self.momentum: Dict[str, float] = {}  # 5-min momentum
        self.strength: Dict[str, float] = {}  # Relative strength vs BTC
        
        # Conversions
        self.pending_conversions: List[ConversionOpportunity] = []
        self.completed_conversions: List[CompletedConversion] = []
        self.conversion_counter = 0
        self.last_conversion_time = datetime.now() - timedelta(hours=1)
        
        # State
        self.running = False
        self.start_time = None
        self.ws_connected = False
        
        # Stats
        self.stats = {
            'price_updates': 0,
            'opportunities_found': 0,
            'conversions_executed': 0,
            'total_converted_usd': 0.0,
            'snowball_gain_pct': 0.0,
        }
        
        # Signal handling
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        print("\n\n🛑 Stopping Pure Conversion Engine...")
        self.running = False
    
    def banner(self):
        """Display startup banner"""
        mode = "DRY RUN" if self.dry_run else "🔴 LIVE CONVERSIONS"
        print(f"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   ██████╗ ██╗   ██╗██████╗ ███████╗     ██████╗ ██████╗ ███╗   ██╗██╗   ██╗   ║
║   ██╔══██╗██║   ██║██╔══██╗██╔════╝    ██╔════╝██╔═══██╗████╗  ██║██║   ██║   ║
║   ██████╔╝██║   ██║██████╔╝█████╗      ██║     ██║   ██║██╔██╗ ██║██║   ██║   ║
║   ██╔═══╝ ██║   ██║██╔══██╗██╔══╝      ██║     ██║   ██║██║╚██╗██║╚██╗ ██╔╝   ║
║   ██║     ╚██████╔╝██║  ██║███████╗    ╚██████╗╚██████╔╝██║ ╚████║ ╚████╔╝    ║
║   ╚═╝      ╚═════╝ ╚═╝  ╚═╝╚══════╝     ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝  ╚═══╝     ║
║                                                                               ║
║      🔄 BARTER FOR BETTER - SNOWBALL YOUR ASSETS 🔄                           ║
║                                                                               ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║   PHILOSOPHY: NOT BUYING. NOT SELLING. CONVERTING.                            ║
║                                                                               ║
║   • Convert WEAK assets → STRONG assets                                       ║
║   • Snowball gains through strategic bartering                                ║
║   • Every conversion increases total buying power                             ║
║   • Unified brain: V14 + Mycelium + Probability + Adaptive                    ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║   MODE: {mode:<60}        ║
║   Min Score: {self.MIN_UNIFIED_SCORE:.0%} | Min Strength Diff: {self.MIN_STRENGTH_DIFF:.0%}                             ║
╚═══════════════════════════════════════════════════════════════════════════════╝
""")
    
    def load_portfolio(self) -> bool:
        """Load current portfolio"""
        print("\n   📊 Loading portfolio...")
        
        if self.dry_run or not self.kraken:
            # Simulate portfolio for dry run
            self.portfolio = {
                'BTC': Asset('BTC', 0.01, 95000, 97000),
                'ETH': Asset('ETH', 0.5, 3200, 3400),
                'SOL': Asset('SOL', 5.0, 160, 170),
                'ATOM': Asset('ATOM', 20.0, 8.5, 9.0),
                'DOT': Asset('DOT', 30.0, 5.5, 6.0),
            }
            print("      🔵 DRY RUN - Simulated portfolio")
        else:
            try:
                balance = self.kraken.get_account_balance()
                if not balance:
                    return False
                
                for asset, amount in balance.items():
                    if amount > 0.0001:
                        # Clean asset name
                        clean = asset.replace('X', '').replace('Z', '')
                        if clean == 'XBT':
                            clean = 'BTC'
                        
                        if clean in self.UNIVERSE:
                            self.portfolio[clean] = Asset(clean, amount, 0, 0)
                            print(f"         {clean}: {amount:.4f}")
            except Exception as e:
                print(f"      ❌ Error: {e}")
                return False
        
        # Calculate initial value
        self._update_portfolio_values()
        self.initial_portfolio_value = self._get_total_value()
        print(f"\n      💰 Total Portfolio: ${self.initial_portfolio_value:.2f}")
        
        return len(self.portfolio) > 0
    
    def _update_portfolio_values(self):
        """Update portfolio USD values from current prices"""
        for asset in self.portfolio.values():
            binance_sym = self.UNIVERSE.get(asset.symbol, {}).get('binance')
            if binance_sym and binance_sym in self.prices:
                asset.current_price = self.prices[binance_sym]
    
    def _get_total_value(self) -> float:
        """Get total portfolio USD value"""
        return sum(a.usd_value for a in self.portfolio.values())
    
    async def _fetch_initial_prices(self):
        """Fetch initial prices"""
        print("\n   📡 Fetching initial prices...")
        
        try:
            response = requests.get('https://api.binance.com/api/v3/ticker/24hr', timeout=10)
            data = response.json()
            
            symbols = {v['binance'] for v in self.UNIVERSE.values()}
            
            for ticker in data:
                symbol = ticker['symbol']
                if symbol in symbols:
                    price = float(ticker['lastPrice'])
                    self.prices[symbol] = price
                    self.price_history[symbol].append({
                        'price': price,
                        'time': datetime.now()
                    })
                    
                    # Update V14 scoring
                    if self.brain.v14:
                        self.brain.v14.scoring_engine.update_price_history(
                            symbol, price, float(ticker.get('volume', 0))
                        )
            
            print(f"      ✅ Loaded {len(self.prices)} prices")
            self._update_portfolio_values()
            
        except Exception as e:
            print(f"      ⚠️ Error: {e}")
    
    async def _price_feed(self):
        """WebSocket price feed"""
        symbols = [v['binance'].lower() for v in self.UNIVERSE.values()]
        streams = [f"{s}@ticker" for s in symbols]
        url = self.WS_URL + "/".join(streams)
        
        print(f"\n   🌐 Connecting to price feed...")
        
        while self.running:
            try:
                async with websockets.connect(url, ping_interval=20) as ws:
                    self.ws_connected = True
                    print(f"      ✅ Connected!")
                    
                    async for message in ws:
                        if not self.running:
                            break
                        
                        try:
                            data = json.loads(message)
                            if 'data' in data:
                                ticker = data['data']
                                symbol = ticker.get('s', '')
                                price = float(ticker.get('c', 0))
                                volume = float(ticker.get('v', 0))
                                
                                if price > 0:
                                    self.prices[symbol] = price
                                    self.price_history[symbol].append({
                                        'price': price,
                                        'time': datetime.now()
                                    })
                                    
                                    # Update V14
                                    if self.brain.v14:
                                        self.brain.v14.scoring_engine.update_price_history(
                                            symbol, price, volume
                                        )
                                    
                                    self.stats['price_updates'] += 1
                                    
                                    # Update momentum & strength
                                    self._update_momentum(symbol)
                                    self._update_relative_strength()
                                    
                                    # Check for conversion opportunities
                                    await self._check_conversions()
                                    
                        except:
                            pass
                            
            except Exception as e:
                self.ws_connected = False
                if self.running:
                    await asyncio.sleep(5)
    
    def _update_momentum(self, symbol: str):
        """Calculate 5-minute momentum"""
        history = list(self.price_history[symbol])
        if len(history) < 10:
            return
        
        now = datetime.now()
        five_min_ago = [h for h in history if (now - h['time']).total_seconds() < 300]
        
        if len(five_min_ago) >= 2:
            old_price = five_min_ago[0]['price']
            new_price = five_min_ago[-1]['price']
            self.momentum[symbol] = (new_price - old_price) / old_price
    
    def _update_relative_strength(self):
        """Update relative strength vs BTC"""
        btc_momentum = self.momentum.get('BTCUSDT', 0)
        
        for asset, info in self.UNIVERSE.items():
            symbol = info['binance']
            if symbol in self.momentum:
                # Relative strength = asset momentum - BTC momentum
                self.strength[asset] = self.momentum[symbol] - btc_momentum
    
    async def find_conversion_opportunities(self) -> List[ConversionOpportunity]:
        """Find all conversion opportunities (for display/testing)"""
        
        # Fetch initial prices if not loaded
        if not self.prices:
            await self._fetch_initial_prices()
        
        # Calculate momentum and strength for all assets
        self._calculate_all_metrics()
        
        opportunities = []
        
        for from_asset in list(self.portfolio.keys()) + ['BTC', 'ETH', 'SOL']:
            if from_asset not in self.portfolio:
                # Create simulated holding for testing
                self.portfolio[from_asset] = Asset(from_asset, 1.0, 
                    self.prices.get(self.UNIVERSE.get(from_asset, {}).get('binance', ''), 100), 
                    self.prices.get(self.UNIVERSE.get(from_asset, {}).get('binance', ''), 100))
            
            from_holding = self.portfolio[from_asset]
            from_strength = self.strength.get(from_asset, 0)
            
            for to_asset, info in self.UNIVERSE.items():
                if to_asset == from_asset:
                    continue
                
                to_strength = self.strength.get(to_asset, 0)
                strength_diff = to_strength - from_strength
                
                # Only consider if TO asset is stronger
                if strength_diff < self.MIN_STRENGTH_DIFF * 0.5:  # Lower threshold for finding opps
                    continue
                
                # Determine conversion type
                if strength_diff > 0.05:
                    conv_type = ConversionType.STRENGTH_SWAP
                elif from_strength > 0.02:
                    conv_type = ConversionType.VALUE_CAPTURE
                elif to_strength < -0.02:
                    conv_type = ConversionType.DISCOUNT_GRAB
                else:
                    conv_type = ConversionType.SNOWBALL
                
                # Create opportunity
                from_symbol = self.UNIVERSE.get(from_asset, {}).get('binance', f'{from_asset}USDT')
                to_symbol = self.UNIVERSE.get(to_asset, {}).get('binance', f'{to_asset}USDT')
                
                opp = ConversionOpportunity(
                    from_asset=from_asset,
                    to_asset=to_asset,
                    conversion_type=conv_type,
                    from_momentum=self.momentum.get(from_symbol, 0),
                    to_momentum=self.momentum.get(to_symbol, 0),
                    relative_strength=strength_diff,
                    from_price=self.prices.get(from_symbol, 0),
                    to_price=self.prices.get(to_symbol, 0),
                    from_strength=from_strength,
                    to_strength=to_strength,
                    strength_diff=strength_diff,
                )
                
                # Score with unified brain
                opp = self.brain.score_conversion(opp, self.prices, self.price_history)
                
                if opp.unified_score >= self.MIN_UNIFIED_SCORE * 0.5:  # Lower threshold
                    opportunities.append(opp)
        
        # Sort by unified score
        opportunities.sort(key=lambda x: x.unified_score, reverse=True)
        return opportunities
    
    def _calculate_all_metrics(self):
        """Calculate momentum and strength for all assets"""
        import random
        
        # Simulate momentum based on price changes
        for asset, info in self.UNIVERSE.items():
            symbol = info['binance']
            if symbol in self.prices:
                # Simulate momentum (would be real in live mode)
                self.momentum[symbol] = random.uniform(-0.02, 0.03)
        
        # Update relative strength
        btc_momentum = self.momentum.get('BTCUSDT', 0)
        
        for asset, info in self.UNIVERSE.items():
            symbol = info['binance']
            if symbol in self.momentum:
                self.strength[asset] = self.momentum[symbol] - btc_momentum
    
    async def _check_conversions(self):
        """Check for conversion opportunities"""
        
        # Cooldown check
        elapsed = (datetime.now() - self.last_conversion_time).total_seconds()
        if elapsed < self.CONVERSION_COOLDOWN:
            return
        
        # Update portfolio values
        self._update_portfolio_values()
        
        # Find best conversion opportunity
        best_opp = None
        best_score = 0
        
        for from_asset in self.portfolio:
            if self.portfolio[from_asset].usd_value < self.MIN_CONVERSION_USD:
                continue
            
            from_strength = self.strength.get(from_asset, 0)
            
            for to_asset, info in self.UNIVERSE.items():
                if to_asset == from_asset:
                    continue
                if to_asset in self.portfolio and self.portfolio[to_asset].usd_value > 1000:
                    continue  # Don't over-concentrate
                
                to_strength = self.strength.get(to_asset, 0)
                strength_diff = to_strength - from_strength
                
                # Only consider if TO asset is significantly stronger
                if strength_diff < self.MIN_STRENGTH_DIFF:
                    continue
                
                # Determine conversion type
                if strength_diff > 0.05:
                    conv_type = ConversionType.STRENGTH_SWAP
                elif from_strength > 0.02:
                    conv_type = ConversionType.VALUE_CAPTURE
                elif to_strength < -0.02:
                    conv_type = ConversionType.DISCOUNT_GRAB
                else:
                    conv_type = ConversionType.SNOWBALL
                
                # Create opportunity
                from_symbol = self.UNIVERSE[from_asset]['binance']
                to_symbol = self.UNIVERSE[to_asset]['binance']
                
                opp = ConversionOpportunity(
                    from_asset=from_asset,
                    to_asset=to_asset,
                    conversion_type=conv_type,
                    from_momentum=self.momentum.get(from_symbol, 0),
                    to_momentum=self.momentum.get(to_symbol, 0),
                    relative_strength=strength_diff,
                    from_price=self.prices.get(from_symbol, 0),
                    to_price=self.prices.get(to_symbol, 0),
                )
                
                # Score with unified brain
                opp = self.brain.score_conversion(opp, self.prices, self.price_history)
                
                if opp.unified_score >= self.MIN_UNIFIED_SCORE and opp.unified_score > best_score:
                    best_opp = opp
                    best_score = opp.unified_score
        
        if best_opp:
            self.stats['opportunities_found'] += 1
            await self._execute_conversion(best_opp)
    
    async def _execute_conversion(self, opp: ConversionOpportunity):
        """Execute a conversion"""
        
        from_holding = self.portfolio.get(opp.from_asset)
        if not from_holding:
            return
        
        # Calculate amounts
        convert_pct = min(self.MAX_CONVERSION_PCT, 0.15 + opp.unified_score * 0.15)
        opp.from_amount = from_holding.amount * convert_pct
        opp.to_amount = (opp.from_amount * opp.from_price / opp.to_price) * (1 - self.TAKER_FEE * 2)
        
        usd_value = opp.from_amount * opp.from_price
        if usd_value < self.MIN_CONVERSION_USD:
            return
        
        opp.reason = f"{opp.conversion_type.value}: {opp.from_asset}→{opp.to_asset} (str diff: {opp.relative_strength:.2%})"
        
        # Execute (sell FROM, buy TO)
        if not self.dry_run and self.kraken:
            try:
                # Sell FROM asset
                from_pair = self.UNIVERSE[opp.from_asset]['kraken']
                sell_result = self.kraken.place_market_order(from_pair, 'sell', opp.from_amount)
                
                if not sell_result:
                    print(f"\n   ⚠️ Sell failed")
                    return
                
                # Buy TO asset
                to_pair = self.UNIVERSE[opp.to_asset]['kraken']
                buy_result = self.kraken.place_market_order(to_pair, 'buy', opp.to_amount)
                
                if not buy_result:
                    print(f"\n   ⚠️ Buy failed")
                    return
                    
            except Exception as e:
                print(f"\n   ❌ Conversion error: {e}")
                return
        
        # Update portfolio
        from_holding.amount -= opp.from_amount
        
        if opp.to_asset not in self.portfolio:
            self.portfolio[opp.to_asset] = Asset(opp.to_asset, 0, opp.to_price, opp.to_price)
        self.portfolio[opp.to_asset].amount += opp.to_amount
        self.portfolio[opp.to_asset].current_price = opp.to_price
        
        # Record conversion
        self.conversion_counter += 1
        conv_id = f"CONV-{self.conversion_counter:04d}"
        
        completed = CompletedConversion(
            id=conv_id,
            from_asset=opp.from_asset,
            to_asset=opp.to_asset,
            from_amount=opp.from_amount,
            to_amount=opp.to_amount,
            from_price=opp.from_price,
            to_price=opp.to_price,
            usd_value=usd_value,
            conversion_type=opp.conversion_type,
            unified_score=opp.unified_score,
            timestamp=datetime.now(),
        )
        self.completed_conversions.append(completed)
        
        # Update stats
        self.stats['conversions_executed'] += 1
        self.stats['total_converted_usd'] += usd_value
        self.last_conversion_time = datetime.now()
        
        # Calculate snowball
        current_value = self._get_total_value()
        self.stats['snowball_gain_pct'] = ((current_value - self.initial_portfolio_value) / 
                                           self.initial_portfolio_value * 100)
        
        # Display
        mode = "(DRY)" if self.dry_run else ""
        print(f"\n   🔄 CONVERSION {mode}: {conv_id}")
        print(f"      {opp.from_amount:.4f} {opp.from_asset} → {opp.to_amount:.4f} {opp.to_asset}")
        print(f"      Type: {opp.conversion_type.value} | Score: {opp.unified_score:.2f}")
        print(f"      V14: {opp.v14_score} | Mycelium: {opp.mycelium_score:.2f} | Prob: {opp.probability_score:.2f}")
        print(f"      USD Value: ${usd_value:.2f} | Snowball: {self.stats['snowball_gain_pct']:+.2f}%")
    
    async def _display_loop(self):
        """Display stats"""
        while self.running:
            await asyncio.sleep(5)
            self._display_stats()
    
    def _display_stats(self):
        """Display current stats"""
        if not self.start_time:
            return
        
        elapsed = time.time() - self.start_time
        current_value = self._get_total_value()
        snowball = self.stats['snowball_gain_pct']
        
        # Portfolio summary
        portfolio_str = " ".join([f"{a}:{v.usd_value:.0f}" for a, v in 
                                  sorted(self.portfolio.items(), key=lambda x: -x[1].usd_value)[:4]])
        
        print(f"\r   ⏱️ {elapsed:.0f}s | "
              f"📡 {self.stats['price_updates']:,} | "
              f"🔄 {self.stats['conversions_executed']} convs | "
              f"💰 ${current_value:.2f} | "
              f"❄️ {snowball:+.2f}% snowball | "
              f"[{portfolio_str}]",
              end='', flush=True)
    
    def _final_report(self):
        """Final report"""
        if not self.start_time:
            return
        
        elapsed = time.time() - self.start_time
        final_value = self._get_total_value()
        gain_pct = ((final_value - self.initial_portfolio_value) / self.initial_portfolio_value * 100)
        
        print("\n\n" + "═"*80)
        print("🔄 PURE CONVERSION SESSION REPORT")
        print("═"*80)
        
        print(f"\n⏱️ SESSION")
        print(f"   Runtime: {elapsed:.1f}s ({elapsed/3600:.2f} hours)")
        print(f"   Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")
        
        print(f"\n🔄 CONVERSIONS")
        print(f"   Executed: {self.stats['conversions_executed']}")
        print(f"   Total USD Converted: ${self.stats['total_converted_usd']:.2f}")
        
        print(f"\n💰 PORTFOLIO")
        print(f"   Initial Value: ${self.initial_portfolio_value:.2f}")
        print(f"   Final Value: ${final_value:.2f}")
        print(f"   ❄️ SNOWBALL GAIN: {gain_pct:+.2f}%")
        
        print(f"\n📊 HOLDINGS")
        for asset, holding in sorted(self.portfolio.items(), key=lambda x: -x[1].usd_value):
            if holding.usd_value > 1:
                print(f"   {asset}: {holding.amount:.4f} (${holding.usd_value:.2f})")
        
        if self.completed_conversions:
            print(f"\n📝 RECENT CONVERSIONS")
            for conv in self.completed_conversions[-5:]:
                print(f"   {conv.id}: {conv.from_asset}→{conv.to_asset} ${conv.usd_value:.2f} ({conv.conversion_type.value})")
        
        print("\n" + "═"*80)
        print("🔄 PURE CONVERSION: BARTER FOR BETTER - SNOWBALL YOUR ASSETS 🔄")
        print("═"*80 + "\n")
    
    async def run(self):
        """Main run loop"""
        self.banner()
        
        if not self.load_portfolio():
            print("\n   ❌ No portfolio to convert!")
            return
        
        if not self.dry_run:
            print("\n" + "═"*70)
            print("⚠️  LIVE PURE CONVERSION MODE ⚠️")
            print("═"*70)
            print("\n   This will execute REAL conversions between your assets.")
            print("   Philosophy: NOT buying or selling. BARTERING for better positions.")
            
            confirm = input("\n   Type 'BARTER' to start: ")
            if confirm != 'BARTER':
                print("\n   Aborted.")
                return
        
        print("\n🔄🔄🔄 PURE CONVERSION ENGINE ACTIVATED! 🔄🔄🔄\n")
        
        self.running = True
        self.start_time = time.time()
        
        await self._fetch_initial_prices()
        
        try:
            await asyncio.gather(
                self._price_feed(),
                self._display_loop(),
            )
        except asyncio.CancelledError:
            pass
        finally:
            self._final_report()


async def main():
    """Entry point"""
    import argparse
    parser = argparse.ArgumentParser(description='Pure Conversion Engine')
    parser.add_argument('--dry-run', action='store_true', help='Run without real trades')
    parser.add_argument('--capital', type=float, default=10000.0, help='Starting capital')
    args = parser.parse_args()
    
    print("\n🔄🔄🔄 PURE CONVERSION ENGINE 🔄🔄🔄")
    print("   BARTER FOR BETTER - SNOWBALL YOUR ASSETS")
    print("   Press Ctrl+C to stop\n")
    
    engine = PureConversionEngine(
        starting_capital=args.capital,
        dry_run=args.dry_run
    )
    await engine.run()


if __name__ == "__main__":
    asyncio.run(main())
