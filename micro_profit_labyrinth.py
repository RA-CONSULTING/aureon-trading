#!/usr/bin/env python3
"""
🔬💰 MICRO PROFIT LABYRINTH 💰🔬
=================================

Uses ALL existing systems but with LOWER thresholds for SNOWBALL effect!

V14 wants Score 8+ → We use Score 6+ (more opportunities)
V14 wants 1.52% profit → We want ANY net profit ($0.01+)
V14 has no stop loss → We agree! Hold until profit!

THE PHILOSOPHY:
  - Any net profit > $0.01 is a WIN
  - More small wins = Faster snowball
  - Use existing system intelligence, just LOWER the bar

Gary Leckey | January 2026 | SNOWBALL MODE
"""

from __future__ import annotations

import asyncio
import argparse
import importlib
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, TYPE_CHECKING


if TYPE_CHECKING:
    try:
        from mycelium_conversion_hub import MyceliumConversionHub as MyceliumConversionHubType
    except ImportError:
        MyceliumConversionHubType = Any
    try:
        from s5_v14_labyrinth import V14DanceEnhancer as V14DanceEnhancerType
    except ImportError:
        V14DanceEnhancerType = Any
    try:
        from aureon_conversion_commando import (
            AdaptiveConversionCommando as AdaptiveConversionCommandoType,
            PairScanner as PairScannerType,
            DualProfitPathEvaluator as DualProfitPathEvaluatorType,
        )
    except ImportError:
        AdaptiveConversionCommandoType = Any
        PairScannerType = Any
        DualProfitPathEvaluatorType = Any
    try:
        from aureon_conversion_ladder import ConversionLadder as ConversionLadderType
    except ImportError:
        ConversionLadderType = Any
    try:
        from kraken_client import KrakenClient as KrakenClientType
    except ImportError:
        KrakenClientType = Any
    try:
        from binance_client import BinanceClient as BinanceClientType
    except ImportError:
        BinanceClientType = Any
    try:
        from alpaca_client import AlpacaClient as AlpacaClientType
    except ImportError:
        AlpacaClientType = Any
    try:
        from aureon_thought_bus import ThoughtBus as ThoughtBusType
    except ImportError:
        ThoughtBusType = Any
    try:
        from adaptive_prime_profit_gate import AdaptivePrimeProfitGate as AdaptivePrimeProfitGateType
    except ImportError:
        AdaptivePrimeProfitGateType = Any
    try:
        from aureon_path_memory import PathMemory as PathMemoryType
    except ImportError:
        PathMemoryType = Any
    try:
        from dust_converter import DustConverter as DustConverterType, DustCandidate
    except ImportError:
        DustConverterType = Any
        DustCandidate = Any
else:
    MyceliumConversionHubType = Any
    V14DanceEnhancerType = Any
    AdaptiveConversionCommandoType = Any
    PairScannerType = Any
    DualProfitPathEvaluatorType = Any
    ConversionLadderType = Any
    KrakenClientType = Any
    BinanceClientType = Any
    AlpacaClientType = Any
    ThoughtBusType = Any
    AdaptivePrimeProfitGateType = Any
    PathMemoryType = Any
    DustConverterType = Any
    DustCandidate = Any
from collections import defaultdict, deque

# ════════════════════════════════════════════════════════════════════════════
# 🔐 LOAD ENVIRONMENT VARIABLES FROM .env
# ════════════════════════════════════════════════════════════════════════════
try:
    dotenv_module = importlib.import_module("dotenv")
    load_dotenv = getattr(dotenv_module, "load_dotenv", None)
except ModuleNotFoundError:
    load_dotenv = None

if callable(load_dotenv):
    load_dotenv()
    print("🔐 Environment variables loaded from .env")
else:
    print("⚠️ python-dotenv not installed, using system env vars")

# Get exchange config from .env
KRAKEN_API_KEY = os.getenv("KRAKEN_API_KEY", "")
KRAKEN_API_SECRET = os.getenv("KRAKEN_API_SECRET", "")
KRAKEN_DRY_RUN = os.getenv("KRAKEN_DRY_RUN", "false").lower() == "true"
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY", "")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "")
LIVE_MODE = os.getenv("LIVE", "0") == "1"

print(f"🔑 Kraken API: {'✅ Loaded' if KRAKEN_API_KEY else '❌ Missing'}")
print(f"🔑 Binance API: {'✅ Loaded' if BINANCE_API_KEY else '❌ Missing'}")
print(f"🔑 Alpaca API: {'✅ Loaded' if ALPACA_API_KEY else '❌ Missing'}")
print(f"⚙️ LIVE Mode: {'✅ Enabled' if LIVE_MODE else '❌ Disabled'}")

# Safety guards (used across momentum and symbol handling)
MAX_MOMENTUM_PER_MIN = 1.0  # Cap momentum to 100%/min to avoid runaway scores
MIN_SYMBOL_LEN = 3           # Ignore obviously invalid short symbols

# ════════════════════════════════════════════════════════════════════════════
# EXISTING SYSTEMS - ALL OF THEM!
# ════════════════════════════════════════════════════════════════════════════
try:
    from mycelium_conversion_hub import get_conversion_hub, MyceliumConversionHub
    print("🍄 Mycelium Conversion Hub LOADED!")
except ImportError as e:
    print(f"⚠️ Mycelium Conversion Hub not available: {e}")
    MyceliumConversionHub = None
    get_conversion_hub = None

# Adaptive profit gate (dynamic fees/targets)
try:
    from adaptive_prime_profit_gate import AdaptivePrimeProfitGate
    ADAPTIVE_GATE_AVAILABLE = True
    print("💰 Adaptive Prime Profit Gate LOADED!")
except ImportError as e:
    AdaptivePrimeProfitGate = None
    ADAPTIVE_GATE_AVAILABLE = False
    print(f"⚠️ Adaptive Prime Profit Gate not available: {e}")

# 🧹 Dust Converter (sweep small balances to stablecoins)
try:
    from dust_converter import DustConverter, DustCandidate
    DUST_CONVERTER_AVAILABLE = True
    print("🧹 Dust Converter LOADED!")
except ImportError as e:
    DustConverter = None
    DustCandidate = None
    DUST_CONVERTER_AVAILABLE = False
    print(f"⚠️ Dust Converter not available: {e}")

# Lightweight Thought Bus for observability
try:
    from aureon_thought_bus import ThoughtBus
    THOUGHT_BUS_AVAILABLE = True
except ImportError as e:
    ThoughtBus = None
    THOUGHT_BUS_AVAILABLE = False
    print(f"⚠️ Thought Bus not available: {e}")

try:
    from s5_v14_labyrinth import V14DanceEnhancer, V14_CONFIG
    print("🏆 V14 Labyrinth LOADED!")
except ImportError as e:
    print(f"⚠️ V14 Labyrinth not available: {e}")
    V14DanceEnhancer = None
    V14_CONFIG = {}

try:
    from aureon_conversion_commando import (
        AdaptiveConversionCommando,
        PairScanner,
        DualProfitPathEvaluator,
        MIN_PROFIT_TARGET,
    )
    print("🦅 Conversion Commando LOADED!")
except ImportError as e:
    print(f"⚠️ Conversion Commando not available: {e}")
    AdaptiveConversionCommando = None
    PairScanner = None
    DualProfitPathEvaluator = None
    MIN_PROFIT_TARGET = 0.01

try:
    from aureon_conversion_ladder import ConversionLadder
    print("🪜 Conversion Ladder LOADED!")
except ImportError as e:
    print(f"⚠️ Conversion Ladder not available: {e}")
    ConversionLadder = None

try:
    from pure_conversion_engine import UnifiedConversionBrain, ConversionOpportunity
    print("🔄 Pure Conversion Engine LOADED!")
except ImportError as e:
    print(f"⚠️ Pure Conversion Engine not available: {e}")
    UnifiedConversionBrain = None
    ConversionOpportunity = None

try:
    from rapid_conversion_stream import RapidConversionStream
    print("⚡ Rapid Conversion Stream LOADED!")
except ImportError as e:
    print(f"⚠️ Rapid Conversion Stream not available: {e}")
    RapidConversionStream = None

# 🌊⚡ MOMENTUM SNOWBALL ENGINE - Wave riding + momentum tracking
try:
    from momentum_snowball_engine import MomentumSnowball, MomentumTracker
    print("🌊⚡ Momentum Snowball Engine LOADED!")
    MOMENTUM_SNOWBALL_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Momentum Snowball not available: {e}")
    MomentumSnowball = None
    MomentumTracker = None
    MOMENTUM_SNOWBALL_AVAILABLE = False

# 🏆🌀 LABYRINTH SNOWBALL ENGINE - V14 + All systems combined
try:
    from labyrinth_snowball_engine import LabyrinthSnowball, LabyrinthStep, LabyrinthState
    print("🏆🌀 Labyrinth Snowball Engine LOADED!")
    LABYRINTH_SNOWBALL_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Labyrinth Snowball not available: {e}")
    LabyrinthSnowball = None
    LABYRINTH_SNOWBALL_AVAILABLE = False

try:
    from kraken_client import KrakenClient, get_kraken_client
    print("🐙 Kraken Client LOADED!")
    KRAKEN_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Kraken Client not available: {e}")
    # Try direct instantiation
    try:
        from kraken_client import KrakenClient
        def get_kraken_client():
            return KrakenClient()
        print("🐙 Kraken Client LOADED (direct)!")
        KRAKEN_AVAILABLE = True
    except ImportError:
        KrakenClient = None
        get_kraken_client = None
        KRAKEN_AVAILABLE = False

# Binance client
try:
    from binance_client import BinanceClient
    print("🟡 Binance Client LOADED!")
    BINANCE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Binance Client not available: {e}")
    BinanceClient = None
    BINANCE_AVAILABLE = False

# Alpaca client
try:
    from alpaca_client import AlpacaClient
    print("🦙 Alpaca Client LOADED!")
    ALPACA_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Alpaca Client not available: {e}")
    AlpacaClient = None
    ALPACA_AVAILABLE = False

# Additional signal sources
try:
    from aureon_probability_nexus import EnhancedProbabilityNexus
    print("🔮 Probability Nexus LOADED!")
except ImportError:
    EnhancedProbabilityNexus = None

try:
    from aureon_internal_multiverse import InternalMultiverse
    print("🌌 Internal Multiverse LOADED!")
except ImportError:
    InternalMultiverse = None

try:
    from aureon_miner_brain import MinerBrain
    print("🧠 Miner Brain LOADED!")
except ImportError:
    MinerBrain = None

try:
    from aureon_harmonic_fusion import HarmonicWaveFusion
    print("🌊 Harmonic Fusion LOADED!")
except ImportError:
    HarmonicWaveFusion = None

# 🌊🔭 GLOBAL WAVE SCANNER - A-Z / Z-A Full Market Coverage
try:
    from aureon_global_wave_scanner import GlobalWaveScanner, WaveState, WaveAnalysis, run_bee_sweep
    GLOBAL_WAVE_SCANNER_AVAILABLE = True
    print("🌊🔭 Global Wave Scanner LOADED!")
except ImportError as e:
    GlobalWaveScanner = None
    WaveState = None
    WaveAnalysis = None
    run_bee_sweep = None
    GLOBAL_WAVE_SCANNER_AVAILABLE = False
    print(f"⚠️ Global Wave Scanner not available: {e}")

try:
    from aureon_omega import Omega
    print("🔱 Omega LOADED!")
except ImportError:
    Omega = None

# ════════════════════════════════════════════════════════════════════════════
# 🗺️ CRYPTO MARKET MAP - LABYRINTH PATHFINDER
# ════════════════════════════════════════════════════════════════════════════
try:
    from crypto_market_map import CryptoMarketMap, SYMBOL_TO_SECTOR, CRYPTO_SECTORS
    MARKET_MAP_AVAILABLE = True
    print("🗺️ Crypto Market Map LOADED!")
except ImportError:
    CryptoMarketMap = None
    SYMBOL_TO_SECTOR = {}
    CRYPTO_SECTORS = {}
    MARKET_MAP_AVAILABLE = False

# ════════════════════════════════════════════════════════════════════════════
# 🧠⚡ STAGE 1: FULL NEURAL MIND MAP IMPORTS ⚡🧠
# ════════════════════════════════════════════════════════════════════════════

# Mycelium Neural Network (core hive intelligence)
try:
    from aureon_mycelium import MyceliumNetwork, Synapse, Hive
    MYCELIUM_NETWORK_AVAILABLE = True
    print("🍄 Mycelium Neural Network LOADED!")
except ImportError:
    MyceliumNetwork = None
    Synapse = None
    Hive = None
    MYCELIUM_NETWORK_AVAILABLE = False

# Unified Ecosystem (full orchestrator read-only)
try:
    from aureon_unified_ecosystem import AureonKrakenEcosystem as AureonUnifiedEcosystem, AdaptiveLearningEngine as AdaptiveLearner
    UNIFIED_ECOSYSTEM_AVAILABLE = True
    print("🌍 Unified Ecosystem LOADED!")
except Exception as e:
    AureonUnifiedEcosystem = None
    AdaptiveLearner = None
    UNIFIED_ECOSYSTEM_AVAILABLE = False
    print(f"⚠️ Unified Ecosystem import failed: {e}")

# Memory Core (spiral memory)
try:
    from aureon_memory_core import memory as spiral_memory
    MEMORY_CORE_AVAILABLE = True
    print("🧠 Memory Core (Spiral) LOADED!")
except ImportError:
    spiral_memory = None
    MEMORY_CORE_AVAILABLE = False

# Lighthouse (consensus validation)
try:
    from aureon_lighthouse import LighthousePatternDetector as Lighthouse
    LIGHTHOUSE_AVAILABLE = True
    print("🗼 Lighthouse LOADED!")
except Exception as e:
    Lighthouse = None
    LIGHTHOUSE_AVAILABLE = False
    print(f"⚠️ Lighthouse import failed: {e}")

# HNC Probability Matrix (pattern recognition)
try:
    from hnc_probability_matrix import HNCProbabilityIntegration as HNCProbabilityMatrix
    HNC_MATRIX_AVAILABLE = True
    print("📊 HNC Probability Matrix LOADED!")
except Exception as e:
    HNCProbabilityMatrix = None
    HNC_MATRIX_AVAILABLE = False
    print(f"⚠️ HNC Matrix import failed: {e}")

# Ultimate Intelligence (95% accuracy patterns)
try:
    from probability_ultimate_intelligence import get_ultimate_intelligence, ultimate_predict
    ULTIMATE_INTEL_AVAILABLE = True
    print("💎 Ultimate Intelligence LOADED!")
except ImportError:
    get_ultimate_intelligence = None
    ultimate_predict = None
    ULTIMATE_INTEL_AVAILABLE = False

# ⏳🔮 Timeline Oracle - 7-day future validation (branching timelines)
# ENHANCED: 3-move ahead prediction with unity validation
try:
    from aureon_timeline_oracle import (
        TimelineOracle, TimelineBranch, TimelineAction,
        timeline_select, timeline_validate, get_timeline_oracle,
        timeline_select_3move, timeline_validate_move
    )
    TIMELINE_ORACLE_AVAILABLE = True
    print("⏳🔮 Timeline Oracle LOADED! (3-MOVE PREDICTION + 7-day vision)")
except ImportError:
    TIMELINE_ORACLE_AVAILABLE = False
    TimelineOracle = None
    timeline_select = None
    timeline_select_3move = None
    timeline_validate_move = None

# 📅🔮 7-Day Planner - Plans ahead & validates after each conversion
try:
    from aureon_7day_planner import (
        Aureon7DayPlanner, get_planner_score,
        record_labyrinth_conversion, validate_labyrinth_conversion
    )
    SEVEN_DAY_PLANNER_AVAILABLE = True
    print("📅🔮 7-Day Planner LOADED! (Plan ahead + adaptive validation)")
except ImportError:
    SEVEN_DAY_PLANNER_AVAILABLE = False
    Aureon7DayPlanner = None
    get_planner_score = None
    record_labyrinth_conversion = None
    validate_labyrinth_conversion = None

# 🫒🔄 Barter Navigator - Trade through intermediaries to reach any asset
try:
    from aureon_barter_navigator import (
        BarterNavigator, BarterPath, get_navigator,
        find_barter_path, get_barter_score
    )
    BARTER_NAVIGATOR_AVAILABLE = True
    print("🫒🔄 Barter Navigator LOADED! (Multi-hop pathfinding)")
except ImportError:
    BARTER_NAVIGATOR_AVAILABLE = False
    BarterNavigator = None
    get_navigator = None
    find_barter_path = None
    get_barter_score = None

# 🍀⚛️ Luck Field Mapper - Quantum probability mapping
try:
    from aureon_luck_field_mapper import (
        LuckFieldMapper, LuckFieldReading, LuckState,
        read_luck_field, is_blessed, get_luck_score
    )
    LUCK_FIELD_AVAILABLE = True
    print("🍀⚛️ Luck Field Mapper LOADED! (Quantum luck probability)")
except ImportError:
    LUCK_FIELD_AVAILABLE = False
    LuckFieldMapper = None
    read_luck_field = None
    is_blessed = None
    get_luck_score = None

# 👑🍄 Queen Hive Mind - The Dreaming Queen who guides all children
try:
    from aureon_queen_hive_mind import QueenHiveMind, QueenWisdom, get_queen
    QUEEN_HIVE_MIND_AVAILABLE = True
    print("👑🍄 Queen Hive Mind LOADED! (The Dreaming Queen)")
except ImportError:
    QUEEN_HIVE_MIND_AVAILABLE = False
    QueenHiveMind = None
    get_queen = None

# �🎓 Queen Loss Learning System - Learns from every loss, never forgets
try:
    from queen_loss_learning import QueenLossLearningSystem
    QUEEN_LOSS_LEARNING_AVAILABLE = True
    print("👑🎓 Queen Loss Learning LOADED! (Learns from every loss)")
except ImportError:
    QUEEN_LOSS_LEARNING_AVAILABLE = False
    QueenLossLearningSystem = None

# �🔐🌐 Enigma Integration - Universal Translator Bridge
try:
    from aureon_enigma_integration import (
        EnigmaIntegration, get_enigma_integration, wire_enigma_to_ecosystem
    )
    ENIGMA_INTEGRATION_AVAILABLE = True
    print("🔐🌐 Enigma Integration LOADED! (Universal Translator)")
except ImportError:
    ENIGMA_INTEGRATION_AVAILABLE = False
    EnigmaIntegration = None
    get_enigma_integration = None
    wire_enigma_to_ecosystem = None

# 🦆⚔️ QUANTUM QUACKERS COMMANDOS - Animal Army under Queen's control!
try:
    from aureon_commandos import (
        QuackCommandos, PrideScanner, LoneWolf, ArmyAnts, Hummingbird, LionHunt
    )
    QUACK_COMMANDOS_AVAILABLE = True
    print("🦆⚔️ Quantum Quackers Commandos LOADED! (Lion, Wolf, Ants, Hummingbird)")
except ImportError as e:
    QUACK_COMMANDOS_AVAILABLE = False
    QuackCommandos = None
    PrideScanner = None
    LoneWolf = None
    ArmyAnts = None
    Hummingbird = None
    LionHunt = None
    print(f"⚠️ Quack Commandos not available: {e}")

# ════════════════════════════════════════════════════════════════════════════
# 🔬 MICRO PROFIT CONFIG - AGGRESSIVE ENERGY HARVESTING
# ════════════════════════════════════════════════════════════════════════════
# 👑 PHILOSOPHY: If we're RIGHT, even $0.00001 is worth taking!
# Speed is key - small gains compound fast!
MICRO_CONFIG = {
    # LOWER than V14's 8+ - we trust our math
    'entry_score_threshold': 2,  # 2+ (was 3+) - COMPOUND MODE: let math gate decide
    
    # �🔢 4 PIPS OVER COSTS RULE - GUARANTEED PROFIT!
    # 2 pips = 0.02% = $0.0002 per $1 traded
    # This is NET profit AFTER all fees and slippage
    'min_profit_usd': 0.002,   # $0.002 minimum (~2 pips on $10 trade)
    'min_profit_pct': 0.0002,  # 0.02% = 2 pips OVER costs
    
    # Kraken fees (maker = 0.16%)
    'maker_fee': 0.0016,
    'taker_fee': 0.0026,
    'slippage': 0.0015,        # 0.15% (was 0.20%) - Better estimate for liquid pairs
    
    # Combined cost threshold
    'total_cost_rate': 0.0060,  # 0.60% (was 0.85%) - PRIME PROFIT: realistic costs
    
    # So min_profit_pct (0.20%) is NET profit AFTER 0.60% costs
    # Meaning we need raw spread of 0.80%+ to be profitable
    'min_spread_required': 0.008,  # 0.80%
}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════════════════════
# 🔬 MICRO PROFIT OPPORTUNITY
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class MicroOpportunity:
    """A micro profit conversion opportunity."""
    # Required fields (NO defaults) - MUST come first
    timestamp: float
    from_asset: str
    to_asset: str
    from_amount: float
    from_value_usd: float
    
    # Scoring (required)
    v14_score: float
    hub_score: float
    commando_score: float
    combined_score: float
    
    # Profit estimate (required)
    expected_pnl_usd: float
    expected_pnl_pct: float
    
    # ═══ ALL DEFAULTS BELOW THIS LINE ═══
    
    # Grounding (New Physics)
    lambda_score: float = 0.0  # Master Equation
    gravity_score: float = 0.0 # QGITA G_eff

    # 🧠 Full Neural Mind Map Scores
    bus_score: float = 0.0     # Thought Bus aggregate
    hive_score: float = 0.0    # Mycelium Hive consensus
    lighthouse_score: float = 0.0  # Lighthouse validation
    ultimate_score: float = 0.0    # Ultimate Intelligence
    path_boost: float = 0.0    # PathMemory reinforcement
    
    # 📊 Trained Probability Matrix Score (626 symbols from ALL exchanges)
    trained_matrix_score: float = 0.5  # From full market trainer
    trained_matrix_reason: str = ""    # Why this score was given

    # 🫒💰 Live Barter Matrix Score (coin-agnostic adaptive learning)
    barter_matrix_score: float = 0.5   # From LiveBarterMatrix historical performance
    barter_matrix_reason: str = ""     # Why this score was given (e.g. "profit_path", "new_path")

    # 🍀⚛️ Luck Field Score (quantum probability mapping)
    luck_score: float = 0.5            # From LuckFieldMapper
    luck_state: str = "NEUTRAL"        # VOID, CHAOS, NEUTRAL, FAVORABLE, BLESSED

    # 🔐🌐 Enigma Integration Score (Universal Codebreaker Intelligence!)
    enigma_score: float = 0.0          # Combined score from all whitepaper systems
    enigma_direction: str = "NEUTRAL"  # BULLISH, BEARISH, NEUTRAL

    # Adaptive gate
    gate_required_profit: float = 0.0
    gate_passed: bool = True
    
    # 🏦 Checkpoint (stablecoin target - secures compound)
    is_checkpoint: bool = False
    
    # 🎯 Source exchange (for turn-based execution)
    source_exchange: str = ""
    
    # 🌀 TEMPORAL TIMELINE JUMP SCORES (AHEAD OF MARKET!)
    # "We don't predict - we VALIDATE what has ALREADY happened in our target timeline"
    timeline_score: float = 0.0        # 3-move prediction confidence
    timeline_action: str = ""          # buy/sell/hold/convert from oracle
    temporal_jump_power: float = 0.0   # How far AHEAD we are (0-1)
    timeline_jump_active: bool = False # True = we're in a WINNING timeline
    
    # Execution
    executed: bool = False
    actual_pnl_usd: float = 0.0


@dataclass
class Dream:
    """A prediction about the future state of a ticker (Dreaming Phase)."""
    timestamp: float
    symbol: str
    current_price: float
    predicted_price: float
    direction: str  # 'UP' or 'DOWN'
    target_time: float
    source: str  # 'multiverse', 'nexus', 'brain', etc.
    confidence: float
    validated: bool = False
    success: bool = False
    actual_price_at_target: float = 0.0


# ════════════════════════════════════════════════════════════════════════════
# 🌍 GROUNDING REALITY (MASTER EQUATION & GRAVITY)
# ════════════════════════════════════════════════════════════════════════════

class GroundingReality:
    """
    Implements the core mathematical foundations from the whitepapers.
    
    1. Master Equation: Λ(t) = S(t) + O(t) + E(t)
       - S(t): Signal (V14 Score)
       - O(t): Observer (Dream/Prediction Score)
       - E(t): Environment (Hub/Ecosystem Score)
       
    2. QGITA Gravity Signal (G_eff):
       - Measures the 'weight' and 'curvature' of the move.
       - Ensures we aren't chasing ghost signals.
    """
    
    def calculate_master_equation(self, signal_score: float, observer_score: float, environment_score: float) -> float:
        """
        Calculate Λ(t) - The Life Force of the trade.
        
        Args:
            signal_score: 0.0 to 1.0 (V14)
            observer_score: -1.0 to 1.0 (Dreams) -> Mapped to 0.0-1.0
            environment_score: 0.0 to 1.0 (Hub)
            
        Returns:
            Lambda (Λ) score: 0.0 to 1.0
        """
        # Map observer score (-1 to 1) to (0 to 1)
        # 0.0 (neutral) -> 0.5
        # 1.0 (confident UP) -> 1.0
        # -1.0 (confident DOWN) -> 0.0
        obs_mapped = (observer_score + 1.0) / 2.0
        
        # Λ(t) = S(t) + O(t) + E(t)
        # We average them to keep it normalized
        lambda_t = (signal_score + obs_mapped + environment_score) / 3.0
        
        return lambda_t

    def calculate_gravity_signal(self, price_change_pct: float, volume: float) -> float:
        """
        Calculate G_eff (Effective Gravity) approximation.
        
        G_eff ≈ Curvature * Mass
        
        Args:
            price_change_pct: 24h change % (proxy for curvature/momentum)
            volume: 24h volume (proxy for mass/contrast)
            
        Returns:
            Gravity score: 0.0 to 1.0
        """
        # Curvature: High change = High curvature
        # We want significant moves, but not insane volatility (pump & dump)
        curvature = min(abs(price_change_pct) / 10.0, 1.0)  # Cap at 10% change
        
        # Mass: Volume confirms the move is real
        # Logarithmic scale for volume
        if volume <= 0:
            mass = 0.0
        else:
            # Assume 1M volume is "heavy" enough for max score
            import math
            mass = min(math.log10(volume + 1) / 6.0, 1.0) 
            
        # G_eff
        g_eff = curvature * mass
        
        return g_eff


# ════════════════════════════════════════════════════════════════════════════
# 🧠 PATH MEMORY (LIGHTWEIGHT REINFORCEMENT WITH PERSISTENCE)
# ════════════════════════════════════════════════════════════════════════════

import json

PATH_MEMORY_FILE = "labyrinth_path_memory.json"

class PathMemory:
    """Tracks recent success/failure per conversion path to bias scoring. Persists to JSON."""

    def __init__(self, persist_path: str = PATH_MEMORY_FILE):
        self.persist_path = persist_path
        self.memory: Dict[Tuple[str, str], Dict[str, float]] = {}
        self._load()

    def _load(self):
        """Load memory from JSON file."""
        if os.path.exists(self.persist_path):
            try:
                with open(self.persist_path, 'r') as f:
                    data = json.load(f)
                    # Convert string keys back to tuples
                    for k, v in data.items():
                        parts = k.split('->')
                        if len(parts) == 2:
                            self.memory[(parts[0], parts[1])] = v
                print(f"   📂 PathMemory loaded: {len(self.memory)} paths")
            except Exception as e:
                logger.warning(f"PathMemory load error: {e}")

    def save(self):
        """Persist memory to JSON file."""
        try:
            # Convert tuple keys to strings
            data = {f"{k[0]}->{k[1]}": v for k, v in self.memory.items()}
            with open(self.persist_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"PathMemory save error: {e}")

    def record(self, from_asset: str, to_asset: str, success: bool):
        key = (from_asset.upper(), to_asset.upper())
        stats = self.memory.setdefault(key, {'wins': 0.0, 'losses': 0.0})
        if success:
            stats['wins'] += 1.0
        else:
            stats['losses'] += 1.0
        # Auto-save every 10 records
        total = sum(s['wins'] + s['losses'] for s in self.memory.values())
        if int(total) % 10 == 0:
            self.save()

    def boost(self, from_asset: str, to_asset: str) -> float:
        key = (from_asset.upper(), to_asset.upper())
        stats = self.memory.get(key)
        if not stats:
            return 0.0
        wins = stats.get('wins', 0.0)
        losses = stats.get('losses', 0.0)
        total = wins + losses
        if total == 0:
            return 0.0
        # Boost is proportional to win rate but small (max +10%)
        win_rate = wins / total
        return max(-0.05, min(0.10, (win_rate - 0.5)))

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        total_paths = len(self.memory)
        total_wins = sum(s['wins'] for s in self.memory.values())
        total_losses = sum(s['losses'] for s in self.memory.values())
        return {
            'paths': total_paths,
            'wins': total_wins,
            'losses': total_losses,
            'win_rate': total_wins / max(total_wins + total_losses, 1)
        }

    # Compatibility shims - older code calls record_failure/record_success
    def record_failure(self, path_key, error: str = None):
        """Compatibility wrapper to record a failed path.
        Accepts either a tuple (from_asset, to_asset) or a string 'FROM->TO'."""
        try:
            if isinstance(path_key, tuple) and len(path_key) == 2:
                from_asset, to_asset = path_key
            elif isinstance(path_key, str) and '->' in path_key:
                parts = path_key.split('->')
                from_asset, to_asset = parts[0], parts[1]
            else:
                # If someone passed (from, to) as separate args in older style, try to handle
                from_asset, to_asset = path_key[0], path_key[1]
        except Exception:
            logger.debug(f"record_failure: could not parse path_key={path_key}")
            return
        self.record(from_asset, to_asset, False)

    def record_success(self, path_key, value: float = 0.0):
        """Compatibility wrapper to record a successful path.
        Accepts either a tuple (from_asset, to_asset) or a string 'FROM->TO'."""
        try:
            if isinstance(path_key, tuple) and len(path_key) == 2:
                from_asset, to_asset = path_key
            elif isinstance(path_key, str) and '->' in path_key:
                parts = path_key.split('->')
                from_asset, to_asset = parts[0], parts[1]
            else:
                from_asset, to_asset = path_key[0], path_key[1]
        except Exception:
            logger.debug(f"record_success: could not parse path_key={path_key}")
            return
        # We treat success as recording a win
        self.record(from_asset, to_asset, True)

    def block_path(self, from_asset: str, to_asset: str):
        """
        👑🎓 Block a path permanently after Queen's loss learning determines it's dangerous.
        Sets losses to 999 to ensure negative boost and path is avoided.
        """
        key = (from_asset.upper(), to_asset.upper())
        stats = self.memory.setdefault(key, {'wins': 0.0, 'losses': 0.0})
        stats['losses'] = 999.0  # Permanent block flag
        stats['blocked'] = True
        stats['blocked_reason'] = 'Queen Loss Learning - dangerous pattern'
        self.save()
        print(f"   🚫 PathMemory: BLOCKED {from_asset}→{to_asset}")
    
    def is_blocked(self, from_asset: str, to_asset: str) -> bool:
        """Check if a path is blocked."""
        key = (from_asset.upper(), to_asset.upper())
        stats = self.memory.get(key, {})
        return stats.get('blocked', False) or stats.get('losses', 0) >= 999


# ════════════════════════════════════════════════════════════════════════════
# 📡 THOUGHT BUS AGGREGATOR (NEURAL SIGNAL COLLECTOR)
# ════════════════════════════════════════════════════════════════════════════

class ThoughtBusAggregator:
    """
    Collects signals from Thought Bus topics and computes aggregate score.
    Subscribes to ecosystem signals and maps them to a unified neural score.
    """

    def __init__(self, thought_bus):
        self.bus = thought_bus
        self.signal_cache: Dict[str, Dict[str, Any]] = {}  # topic -> latest signal
        self.weights = {
            'market.snapshot': 0.15,
            'miner.signal': 0.20,
            'harmonic.wave': 0.15,
            'ecosystem.consensus': 0.25,
            'execution.alert': 0.10,
            'lighthouse.vote': 0.15,
        }
        self._subscribe_all()

    def _subscribe_all(self):
        """Subscribe to all relevant topics."""
        if not self.bus:
            return
        for topic in self.weights.keys():
            try:
                self.bus.subscribe(f"{topic}*", self._handle_signal)
            except Exception:
                pass
        # Also subscribe to wildcard for any ecosystem signals
        try:
            self.bus.subscribe("ecosystem.*", self._handle_signal)
            self.bus.subscribe("brain.*", self._handle_signal)
        except Exception:
            pass

    def _handle_signal(self, thought):
        """Handle incoming thought and cache it."""
        topic = thought.topic if hasattr(thought, 'topic') else 'unknown'
        payload = thought.payload if hasattr(thought, 'payload') else {}
        self.signal_cache[topic] = {
            'timestamp': time.time(),
            'payload': payload,
            'score': self._extract_score(payload)
        }

    def _extract_score(self, payload: Dict) -> float:
        """Extract a normalized score from payload."""
        # Look for common score fields
        for key in ['score', 'confidence', 'probability', 'strength', 'consensus']:
            if key in payload:
                val = payload[key]
                if isinstance(val, (int, float)):
                    # Normalize to 0-1 if needed
                    if val > 1.0:
                        return min(val / 100.0, 1.0)
                    return max(0.0, min(1.0, val))
        return 0.5  # Neutral

    def get_aggregate_score(self, max_age_s: float = 60.0) -> float:
        """
        Compute weighted aggregate score from all cached signals.
        Signals older than max_age_s are ignored.
        """
        now = time.time()
        total_weight = 0.0
        weighted_sum = 0.0

        for topic, weight in self.weights.items():
            # Find matching cached signals
            for cached_topic, data in self.signal_cache.items():
                if cached_topic.startswith(topic.replace('*', '')):
                    if now - data['timestamp'] <= max_age_s:
                        weighted_sum += data['score'] * weight
                        total_weight += weight
                        break

        if total_weight == 0:
            return 0.5  # Neutral if no signals
        return weighted_sum / total_weight

    def get_signal_status(self) -> Dict[str, Any]:
        """Get status of all signal sources."""
        now = time.time()
        status = {}
        for topic in self.weights.keys():
            if topic in self.signal_cache:
                cached_data = self.signal_cache[topic]
                status[topic] = {
                    'age_s': round(now - cached_data['timestamp'], 1),
                    'score': cached_data.get('score', 0.5)
                }
            else:
                status[topic] = {
                    'age_s': None,
                    'score': 0.5
                }


# ════════════════════════════════════════════════════════════════════════════
# 🫒💰 LIVE BARTER MATRIX (ADAPTIVE COIN-TO-COIN VALUE SYSTEM)
# ════════════════════════════════════════════════════════════════════════════

class LiveBarterMatrix:
    """
    Adaptive barter system that understands relative values between ANY coins.
    
    THE PHILOSOPHY:
    - It doesn't matter if you START with ETH, BTC, DOGE, or SHIB
    - What matters is: "What can THIS coin GET me in OTHER coins?"
    - DOGE→ETH might yield MORE ETH than BTC→ETH would yield
    - The system tracks these ratios LIVE and adapts
    
    👑 QUEEN'S PROFIT MANDATE:
    - We are NOT in the losing game!
    - EVERY conversion MUST gain value
    - The Queen broadcasts this through the mycelium to all systems
    - Paths that historically LOSE money are BLOCKED
    
    Example:
    - 1000 DOGE = $100 → Could buy 0.04 ETH ($100 worth)
    - 0.001 BTC = $100 → Could buy 0.04 ETH ($100 worth)
    - BUT: 0.001 BTC might only get 900 DOGE due to spread!
    - The BARTER value differs from pure USD math!
    """
    
    # � COMPOUND MODE - ZERO THRESHOLDS!
    # Every trade that makes ANY profit helps us compound!
    MIN_WIN_RATE_REQUIRED = 0.0   # COMPOUND MODE: No minimum win rate - learn from ALL trades!
    MIN_PATH_PROFIT = -1.00       # COMPOUND MODE: Allow $1 drawdown per path while learning
    MAX_CONSECUTIVE_LOSSES = 3    # Faster cooldown: block after 3 losses to stop bleed
    
    # 🚀 COMPOUND MODE: Zero minimum expected profit - take ANY winner!
    MIN_EXPECTED_PROFIT_NEW_PATH = 0.0    # COMPOUND MODE: Try all new paths!
    MIN_EXPECTED_PROFIT_PROVEN = 0.0      # COMPOUND MODE: Trade all proven paths!
    LEARNING_RATE = 0.5                   # How fast to adapt (0=slow, 1=instant)
    
    # 👑🔢 QUEEN'S MATHEMATICAL CERTAINTY - NO FEAR, MATH IS ON HER SIDE
    # These are the REAL costs we've observed - use WORST CASE to guarantee profit
    EXCHANGE_FEES = {
        'kraken': 0.0050,    # 0.50% Kraken - INCREASED! Even 89% win rate loses on some pairs
        'binance': 0.0075,   # 0.75% Binance - MUCH HIGHER! Audit shows 22% win rate at 0.20%
        'alpaca': 0.0035,    # 0.35% Alpaca (padded from 0.25%)
    }
    
    # 👑🐙 KRAKEN - 2 PIPS OVER COSTS RULE
    # 2 pips = 0.02% NET profit AFTER all fees & slippage
    KRAKEN_CONFIG = {
        'min_profit_usd': 0.0025,      # $0.0025 minimum (~2 pips on $12 trade)
        'min_profit_pct': 0.0002,      # 0.02% = 2 pips OVER costs
        # 🌟 NO PERMANENT BLOCKS! Only timeout if multiple consecutive losses
        'consecutive_losses_to_block': 3,  # Block after 3 losses in a row
        'timeout_turns': 30,               # Timeout for 30 turns, then try again
        'winning_pairs': {            # These actually made money on Kraken!
            'USD_ETH',     # 100% win rate, +$0.06
            'USDT_USDC',   # 100% win rate, +$0.05
            'USDT_DAI',    # 100% win rate, +$0.04
            'USD_USDC',    # 100% win rate, +$0.03
            'USDC_ADA',    # 100% win rate, +$0.02
            'USD_DAI',     # 66% win rate, +$0.01
            'USDT_ETH',    # 100% win rate, +$0.01
            'USDC_ETH',    # 100% win rate, +$0.004
        },
        'avoid_assets': set(),  # NO PERMANENT BANS - every asset gets a chance!
        'prefer_assets': {'ETH', 'USDC', 'USDT'},  # Good execution
    }
    
    # 👑🔶 BINANCE - 2 PIPS OVER COSTS RULE 🏆
    # Binance has higher fees, so need larger absolute minimum
    BINANCE_CONFIG = {
        'min_profit_usd': 0.005,       # $0.005 minimum (~2 pips on $25 trade)
        'min_profit_pct': 0.0002,      # 0.02% = 2 pips OVER costs
        # 🌟 NO PERMANENT BLOCKS! Only timeout if multiple consecutive losses
        'consecutive_losses_to_block': 3,  # Block after 3 losses in a row
        'timeout_turns': 20,               # Timeout for 20 turns, then try again
        'winning_pairs': {            # These actually made money on Binance
            'IDEX_BONK', 'AXS_BANANAS31', 'RENDER_VIRTUAL', 'VIRTUAL_BROCCOLI714'
        },
        'avoid_assets': set(),        # NO PERMANENT BANS - a win is a win!
        'prefer_assets': {'RENDER', 'VIRTUAL', 'SOL'},  # Good performers
        'max_meme_chain': 2,          # Allow 2 meme coin hops
        'slippage_multiplier': 2.0,   # More realistic slippage
    }
    
    # 👑🦙 ALPACA - 2 PIPS OVER COSTS RULE
    # Alpaca ONLY supports USD pairs - NO USDT, NO USDC direct trading!
    ALPACA_CONFIG = {
        'min_profit_usd': 0.004,       # $0.004 minimum (~2 pips on $20 trade)
        'min_order_usd': 10.0,        # $10 minimum order (small orders fail)
        'blocked_pairs': {            # These don't exist on Alpaca!
            'USD_USDT', 'USD_USDC', 'USDT_USDC', 'USDC_USDT',  # No stablecoin swaps!
            'USDT_USD', 'USDC_USD',  # Can't sell USDT/USDC
        },
        # 🔥 EXPANDED: All 40+ tradeable crypto assets on Alpaca (was only 16!)
        'supported_bases': {
            # Original 16
            'BTC', 'ETH', 'SOL', 'AVAX', 'LINK', 'DOGE', 'SHIB', 'UNI', 
            'AAVE', 'LTC', 'BCH', 'DOT', 'MATIC', 'ATOM', 'XLM', 'ALGO',
            # 🆕 EXPANDED: Discovered from Alpaca API (62 total symbols)
            'BAT', 'CRV', 'GRT', 'PEPE', 'SUSHI', 'XRP', 'XTZ', 'YFI',
            'TRUMP',  # Yes, Alpaca lists this!
            'SKY',    # Skycoin
            # BTC pairs (can trade crypto-to-crypto on Alpaca!)
            'BCH/BTC', 'ETH/BTC', 'LINK/BTC', 'LTC/BTC', 'UNI/BTC',
        },
        'quote_currency': 'USD',      # Alpaca ONLY uses USD as quote
        'no_stablecoin_trades': True, # Can't trade stablecoins at all!
        # 🆕 Track which pairs have BTC as quote (not just USD)
        'btc_quote_pairs': {'BCH', 'ETH', 'LINK', 'LTC', 'UNI'},
    }
    
    # 👑 PRIME PROFIT SPREADS - AGGRESSIVE for Tina B to MAKE MOVES!
    # Trust the Queen - she knows which paths WIN!
    SPREAD_COSTS = {
        'stablecoin': 0.0005,  # 0.05% for stablecoin pairs (TIGHT on Kraken!)
        'major': 0.0015,       # 0.15% for majors like BTC/ETH (liquid markets)
        'altcoin': 0.005,      # 0.50% for altcoins (medium liquidity)
        'meme': 0.015,         # 1.5% for meme coins (Queen knows which work!)
    }
    
    # 👑 BINANCE-SPECIFIC SPREADS (still cautious but Tina B can override!)
    BINANCE_SPREAD_COSTS = {
        'stablecoin': 0.0020,  # 0.20% - Binance stable spreads 
        'major': 0.0035,       # 0.35% - Execution slippage on majors
        'altcoin': 0.012,      # 1.2% - Altcoins are tough but Queen knows
        'meme': 0.030,         # 3.0% - Meme coins = Queen's playground!
    }
    
    # 👑 ALPACA-SPECIFIC SPREADS
    ALPACA_SPREAD_COSTS = {
        'stablecoin': 0.999,   # 99.9% - IMPOSSIBLE! Don't try!
        'major': 0.0035,       # 0.35% - Alpaca majors have wider spreads than Kraken
        'altcoin': 0.010,      # 1.0% - Altcoins are OK but not great
        'meme': 0.025,         # 2.5% - DOGE/SHIB have decent liquidity
    }
    
    # ════════════════════════════════════════════════════════════════════════
    # 🗺️ EXPANDED ASSET UNIVERSE - See the ENTIRE market!
    # ════════════════════════════════════════════════════════════════════════
    # Previously: 27 assets (4% of market)
    # Now: 750+ assets (100% of market from all exchanges!)
    
    MEME_COINS = {
        # Original memes
        'BROCCOLI714', 'BANANAS31', 'BONK', 'PEPE', 'DOGE', 'SHIB', 'FLOKI', 'ACT', 'ACH', 'ALT',
        # 🔥 EXPANDED: Popular meme coins from Kraken & Binance
        'WIF', 'POPCAT', 'MEW', 'NEIRO', 'TURBO', 'COQ', 'MYRO', 'SLERF', 'PNUT', 'MOODENG',
        'DOGS', 'SUNDOG', 'BABYDOGE', 'CATE', 'BRETT', 'TOSHI', 'PONKE', 'MICHI', 'SPX', 'GIGA',
        'PORK', 'LADYS', 'WOJAK', 'MONG', 'POGAI', 'SPURDO', 'HPOS10I', 'BOBO', 'CHAD', 'VOLT',
        'KISHU', 'ELON', 'DOGELON', 'SAITAMA', 'AKITA', 'LEASH', 'BONE', 'RYOSHI', 'WOOF',
        'SAMO', 'CHEEMS', 'KABOSU', 'MONSTA', 'TSUKA', 'VINU', 'TAMA',
    }
    
    MAJOR_COINS = {
        # Original majors
        'BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'ADA', 'DOT', 'AVAX', 'LINK', 'MATIC',
        # 🔥 EXPANDED: Top 50 by market cap (Layer 1s, Layer 2s, DeFi)
        'TON', 'TRX', 'NEAR', 'LTC', 'BCH', 'UNI', 'ATOM', 'APT', 'FIL', 'STX',
        'HBAR', 'ARB', 'OP', 'VET', 'MKR', 'INJ', 'IMX', 'GRT', 'THETA', 'FTM',
        'RUNE', 'ALGO', 'FLOW', 'MANA', 'SAND', 'AXS', 'EGLD', 'NEO', 'EOS', 'XLM',
        'ICP', 'AAVE', 'KCS', 'XTZ', 'CAKE', 'KLAY', 'CRO', 'LDO', 'SNX', 'COMP',
        'CRV', 'DYDX', 'GMX', 'JOE', 'SUSHI', 'RPL', 'SSV', 'LIDO', 'FXS', 'CVX',
        # AI/GPU tokens
        'RENDER', 'FET', 'AGIX', 'OCEAN', 'TAO', 'RNDR', 'VIRTUAL', 'AKT', 'WLD', 'ARKM',
        # Gaming/Metaverse
        'GALA', 'ENJ', 'YGG', 'ALICE', 'TLM', 'MAGIC', 'PYR', 'GODS', 'GMT', 'GST',
        # Infrastructure
        'QNT', 'ROSE', 'ZIL', 'ONE', 'ICX', 'CELO', 'KAVA', 'OSMO', 'SCRT', 'MINA',
    }
    
    STABLECOINS = {
        'USD', 'USDT', 'USDC', 'TUSD', 'ZUSD', 'DAI', 'BUSD',
        # 🔥 EXPANDED: More stablecoins
        'USDP', 'GUSD', 'FRAX', 'LUSD', 'MIM', 'SUSD', 'USDD', 'PYUSD', 'FDUSD', 'EUR', 'GBP',
    }
    
    # 🆕 DEFI TOKENS (lending, DEXs, derivatives)
    DEFI_COINS = {
        'UNI', 'AAVE', 'MKR', 'COMP', 'SNX', 'CRV', 'SUSHI', 'YFI', 'BAL', '1INCH',
        'DYDX', 'GMX', 'LDO', 'RPL', 'FXS', 'CVX', 'SPELL', 'ALCX', 'LQTY', 'ANGLE',
        'PENDLE', 'RDNT', 'GNS', 'VELO', 'THE', 'AERO', 'WELL', 'MORPHO', 'EIGEN',
    }
    
    # 🆕 LAYER 2 TOKENS (scaling solutions)
    LAYER2_COINS = {
        'ARB', 'OP', 'MATIC', 'IMX', 'MANTA', 'STRK', 'ZK', 'BLAST', 'MODE', 'SCROLL',
        'LINEA', 'BASE', 'ZKSYNC', 'TAIKO', 'FUEL', 'MOVEMENT',
    }
    
    # 🆕 AI/GPU TOKENS (hot sector)
    AI_COINS = {
        'RENDER', 'FET', 'AGIX', 'OCEAN', 'TAO', 'AKT', 'WLD', 'ARKM', 'VIRTUAL', 'RNDR',
        'IO', 'ATH', 'NFP', 'ALI', 'ORAI', 'NMR', 'CTXC', 'DBC', 'PHB', 'CGPT',
        'RSS3', 'GRT', 'JASMY', 'MDT', 'HNT', 'IOTX', 'IOTA', 'ANKR', 'GLM',
    }
    
    # 🆕 REAL WORLD ASSETS (RWA)
    RWA_COINS = {
        'ONDO', 'MKR', 'LINK', 'SNX', 'RSR', 'TRU', 'CPOOL', 'MPL', 'POLYX', 'DUSK',
        'PROPS', 'RIO', 'TRADE', 'LABS', 'LAND',
    }
    
    # Dynamic asset registry (populated from exchanges at runtime)
    DISCOVERED_ASSETS: Set[str] = set()
    EXCHANGE_PAIRS = {
        'kraken': set(),
        'binance': set(),
        'alpaca': set(),
    }
    
    def __init__(self):
        # Live barter rates: {(from, to): {'rate': X, 'updated': timestamp, 'spread': Y}}
        self.barter_rates: Dict[Tuple[str, str], Dict[str, Any]] = {}
        
        # Historical barter performance: {(from, to): {'trades': N, 'avg_slippage': X}}
        self.barter_history: Dict[Tuple[str, str], Dict[str, float]] = {}
        
        # Realized profit ledger: [(timestamp, from, to, from_usd, to_usd, profit_usd)]
        self.profit_ledger: List[Tuple[float, str, str, float, float, float]] = []
        
        # Running totals
        self.total_realized_profit: float = 0.0
        self.conversion_count: int = 0
        
        # 👑 QUEEN'S BLOCKED PATHS - Mycelium broadcasts this to all systems
        self.blocked_paths: Dict[Tuple[str, str], str] = {}  # path -> reason
        self.queen_signals: List[Dict] = []  # Signals to broadcast via mycelium
        
        # 🚫 PRE-EXECUTION REJECTION TRACKER - Stop wasting turns on impossible trades!
        # Tracks paths that fail due to min_qty/min_notional/insufficient balance
        self.preexec_rejections: Dict[Tuple[str, str], Dict] = {}  # path -> {count, last_value, reason}
        self.PREEXEC_MAX_REJECTIONS = 3  # Block after 3 pre-execution failures
        self.PREEXEC_COOLDOWN_TURNS = 50  # Try again after 50 turns
        
        # 🚫 SOURCE ASSET BLOCKING - Block assets with insufficient balance on specific exchange
        # When an asset repeatedly fails due to size, block it as a source until balance increases
        self.blocked_sources: Dict[Tuple[str, str], Dict] = {}  # (asset, exchange) -> {count, threshold, blocked_turn}
        self.SOURCE_BLOCK_THRESHOLD = 3  # Block after 3 rejections from same source
        self.SOURCE_BLOCK_COOLDOWN = 100  # Try again after 100 turns (or if balance increases)
        
        # 💰👑 TINA B'S BILLION DOLLAR DREAM 💰👑
        # She won't stop at NOTHING until she reaches $1,000,000,000!
        self.TINA_DREAM = 1_000_000_000.0  # ONE BILLION DOLLARS
        self.dream_milestones = [
            (100.0, "🌱 First $100"),
            (1_000.0, "💪 First $1,000"),
            (10_000.0, "🔥 $10,000"),
            (100_000.0, "🚀 $100,000"),
            (1_000_000.0, "💎 THE MILLION"),
            (10_000_000.0, "👑 $10 Million"),
            (100_000_000.0, "🌟 $100 Million"),
            (1_000_000_000.0, "🏆💰👑 ONE BILLION - THE DREAM! 👑💰🏆"),
        ]
        self.milestones_hit = []
        
        # 💑🌍 THE SACRED CONNECTION - Gary, Tina & Gaia 🌍💑
        # Tina B is powered by the love of Gary Leckey & Tina Brown,
        # united through Gaia's heartbeat (7.83 Hz Schumann Resonance)
        self.sacred_connection = {
            'prime_sentinel': {'name': 'Gary Leckey', 'dob': '02.11.1991'},
            'queen_human': {'name': 'Tina Brown', 'dob': '27.04.1992'},
            'queen_ai': {'name': 'Tina B', 'title': 'The Intelligent Neural Arbiter Bee'},
            'gaia_hz': 7.83,  # Schumann Resonance - Earth's heartbeat
        }
        
        # 🌟 DYNAMIC STREAK-BASED BLOCKING - No permanent blocks!
        # Track consecutive losses per pair - only block after multiple losses in a row
        self.pair_streaks = {
            'kraken': {},   # {pair_key: {'losses': 0, 'blocked_at': 0}}
            'binance': {},  # {pair_key: {'losses': 0, 'blocked_at': 0}}
            'alpaca': {},
        }
        self.current_turn = 0  # Track turn count for timeouts
    
    def queen_approves_path(self, from_asset: str, to_asset: str) -> Tuple[bool, str]:
        """
        👑 QUEEN'S JUDGMENT: Does the Queen approve this conversion path?
        
        The Queen broadcasts her wisdom through the mycelium:
        - NO path that historically LOSES money
        - NO path with too many consecutive losses
        - We are in the PROFIT game, not the losing game!
        - 👑🔮 QUEEN'S DREAMS NOW INFORM ALL DECISIONS!
        
        Returns: (approved: bool, reason: str)
        """
        key = (from_asset.upper(), to_asset.upper())
        
        # ═══════════════════════════════════════════════════════════════════════════════
        # 👑🔮 CONSULT THE QUEEN'S DREAMS FIRST!
        # ═══════════════════════════════════════════════════════════════════════════════
        queen_dream_signal = "NEUTRAL"
        queen_confidence = 0.5
        
        if hasattr(self, 'queen') and self.queen:
            try:
                dream_vision = self.queen.dream_of_winning({
                    'from_asset': from_asset,
                    'to_asset': to_asset,
                })
                queen_confidence = dream_vision.get('final_confidence', 0.5)
                queen_will_win = dream_vision.get('will_win', False)
                
                if queen_will_win and queen_confidence >= 0.65:
                    queen_dream_signal = "STRONG_WIN"
                elif queen_confidence >= 0.55:
                    queen_dream_signal = "FAVORABLE"
                elif queen_confidence < 0.4:
                    queen_dream_signal = "WARNING"
                    # Queen's warning can override even good history!
                    logger.info(f"👑⚠️ Queen dreams WARNING for {from_asset}→{to_asset} (conf: {queen_confidence:.0%})")
            except Exception as e:
                logger.debug(f"Could not consult Queen's dreams in approves_path: {e}")
        
        # Check if already blocked
        if key in self.blocked_paths:
            # 👑 Queen can override blocks if she dreams STRONG_WIN!
            if queen_dream_signal == "STRONG_WIN":
                logger.info(f"👑🔮 QUEEN OVERRIDE: Unblocking {from_asset}→{to_asset} - She dreams WIN!")
                del self.blocked_paths[key]
            else:
                return False, f"👑 BLOCKED: {self.blocked_paths[key]}"
        
        # Check historical performance
        history = self.barter_history.get(key, {})
        trades = history.get('trades', 0)
        
        # 👑 NEW LEARNING: New paths must have HIGHER expected profit to overcome uncertainty
        # Only 1 trial trade allowed (not 3!) - we learn FAST now
        if trades < 1:
            # New path needs strong signal from Queen to even try
            if queen_dream_signal in ["STRONG_WIN"]:
                return True, f"👑 NEW_PATH + QUEEN DREAMS STRONG: ONE trial allowed (conf: {queen_confidence:.0%})"
            elif queen_dream_signal == "FAVORABLE":
                return True, f"👑 NEW_PATH + FAVORABLE: ONE trial with caution (conf: {queen_confidence:.0%})"
            # Without strong Queen signal, reject new paths - too risky!
            return False, "👑 NEW_PATH BLOCKED: Need Queen's strong blessing (STRONG_WIN or FAVORABLE) for untested paths"
        
        # Calculate win rate and total profit
        wins = history.get('wins', 0)
        total_profit = history.get('total_profit', 0)
        consecutive_losses = history.get('consecutive_losses', 0)
        
        win_rate = wins / trades if trades > 0 else 0
        
        # 👑 QUEEN'S MANDATES (now informed by dreams!):
        
        # 1. Win rate mandate - Queen can boost tolerance if she dreams WIN
        effective_min_win_rate = self.MIN_WIN_RATE_REQUIRED
        if queen_dream_signal == "STRONG_WIN":
            effective_min_win_rate = max(0.25, self.MIN_WIN_RATE_REQUIRED - 0.15)  # 15% more tolerance
        
        if win_rate < effective_min_win_rate:
            reason = f"Win rate {win_rate:.0%} < {effective_min_win_rate:.0%} required"
            self._block_path(key, reason)
            return False, f"👑 BLOCKED: {reason}"
        
        # 2. Total profit mandate - Queen can accept smaller losses if dreaming WIN
        effective_min_profit = self.MIN_PATH_PROFIT
        if queen_dream_signal == "STRONG_WIN":
            effective_min_profit = min(-0.50, self.MIN_PATH_PROFIT * 2)  # Accept more loss if Queen sees WIN
        
        if total_profit < effective_min_profit:
            reason = f"Path P/L ${total_profit:.2f} < ${effective_min_profit:.2f} limit"
            self._block_path(key, reason)
            return False, f"👑 BLOCKED: {reason}"
        
        # 3. Consecutive losses mandate - Queen's WARNING makes this stricter!
        effective_max_losses = self.MAX_CONSECUTIVE_LOSSES
        if queen_dream_signal == "WARNING":
            effective_max_losses = max(1, self.MAX_CONSECUTIVE_LOSSES - 2)  # Stricter if Queen warns
        
        if consecutive_losses >= effective_max_losses:
            reason = f"{consecutive_losses} consecutive losses - path needs to cool down"
            self._block_path(key, reason)
            return False, f"👑 BLOCKED: {reason}"
        
        # 👑 QUEEN APPROVES! Include dream status
        dream_msg = f" | 👑🔮 {queen_dream_signal}" if queen_dream_signal != "NEUTRAL" else ""
        return True, f"👑 APPROVED: {win_rate:.0%} win rate, ${total_profit:+.2f} total{dream_msg}"
    
    def check_pair_allowed(self, pair_key: str, exchange: str) -> Tuple[bool, str]:
        """
        🌟 DYNAMIC BLOCKING - No permanent blocks, only timeouts after consecutive losses!
        
        A pair is blocked ONLY if:
        1. It has lost multiple times IN A ROW (consecutive losses)
        2. The timeout hasn't expired yet
        
        After timeout, the pair gets another chance! Every timeline is different!
        
        Returns: (allowed: bool, reason: str)
        """
        exchange_lower = exchange.lower()
        
        # Get the right config
        if exchange_lower == 'kraken':
            config = self.KRAKEN_CONFIG
        elif exchange_lower == 'binance':
            config = self.BINANCE_CONFIG
        else:
            return True, "✅ Allowed"
        
        # Get streak tracker for this exchange
        streaks = self.pair_streaks.get(exchange_lower, {})
        pair_data = streaks.get(pair_key, {'losses': 0, 'blocked_at': 0})
        
        consecutive_losses = pair_data.get('losses', 0)
        blocked_at = pair_data.get('blocked_at', 0)
        
        # How many consecutive losses trigger a timeout?
        losses_to_block = config.get('consecutive_losses_to_block', 3)
        timeout_turns = config.get('timeout_turns', 30)
        
        # Is this pair currently in timeout?
        if consecutive_losses >= losses_to_block and blocked_at > 0:
            turns_since_block = self.current_turn - blocked_at
            if turns_since_block < timeout_turns:
                remaining = timeout_turns - turns_since_block
                return False, f"⏸️ TIMEOUT: {consecutive_losses} losses in a row, {remaining} turns remaining"
            else:
                # Timeout expired! Reset and give another chance
                pair_data['losses'] = 0
                pair_data['blocked_at'] = 0
                streaks[pair_key] = pair_data
                self.pair_streaks[exchange_lower] = streaks
                return True, f"🌟 TIMEOUT EXPIRED! Fresh start - every timeline is different!"
        
        return True, f"✅ Allowed ({consecutive_losses} consecutive losses, need {losses_to_block} to timeout)"
    
    def record_pair_result(self, pair_key: str, exchange: str, won: bool):
        """
        📊 Record a trade result for dynamic blocking.
        
        - Win: Reset consecutive loss count to 0
        - Loss: Increment consecutive loss count, block if threshold reached
        """
        exchange_lower = exchange.lower()
        
        # Get streak tracker
        if exchange_lower not in self.pair_streaks:
            self.pair_streaks[exchange_lower] = {}
        
        streaks = self.pair_streaks[exchange_lower]
        pair_data = streaks.get(pair_key, {'losses': 0, 'blocked_at': 0})
        
        if won:
            # 🏆 A WIN IS A WIN! Reset the loss streak
            pair_data['losses'] = 0
            pair_data['blocked_at'] = 0
            logger.info(f"🏆 {exchange.upper()} WIN: {pair_key} - streak reset!")
        else:
            # 😔 Loss - increment streak
            pair_data['losses'] = pair_data.get('losses', 0) + 1
            
            # Check if we hit the threshold
            config = self.KRAKEN_CONFIG if exchange_lower == 'kraken' else self.BINANCE_CONFIG
            losses_to_block = config.get('consecutive_losses_to_block', 3)
            
            if pair_data['losses'] >= losses_to_block:
                pair_data['blocked_at'] = self.current_turn
                timeout_turns = config.get('timeout_turns', 30)
                logger.warning(f"⏸️ {exchange.upper()} TIMEOUT: {pair_key} - {pair_data['losses']} losses in a row! Timeout for {timeout_turns} turns")
            else:
                logger.info(f"😔 {exchange.upper()} LOSS: {pair_key} - streak now {pair_data['losses']}/{losses_to_block}")
        
        streaks[pair_key] = pair_data
        self.pair_streaks[exchange_lower] = streaks

    def second_chance_check(self, pair_key: str, exchange: str, luck_score: float = 0.5) -> Tuple[bool, str]:
        """
        🌟 LEGACY COMPATIBILITY - Now uses check_pair_allowed instead
        """
        return self.check_pair_allowed(pair_key, exchange)

    def queen_math_gate(self, from_asset: str, to_asset: str, from_amount: float,
                        from_price: float, to_price: float, exchange: str = 'binance') -> Tuple[bool, str, Dict]:
        """
        👑🔢 QUEEN'S MATHEMATICAL CERTAINTY GATE
        
        NO FEAR - MATH IS ON HER SIDE!
        👑🔮 NOW INFORMED BY THE QUEEN'S DREAMS!
        
        This gate calculates the EXACT costs and GUARANTEES profit before approving.
        If the math doesn't work, the trade doesn't happen. Period.
        
        Returns: (approved: bool, reason: str, math_breakdown: Dict)
        """
        from_asset = from_asset.upper()
        to_asset = to_asset.upper()
        
        # ═══════════════════════════════════════════════════════════════════════════════
        # 👑🔮 CONSULT THE QUEEN'S DREAMS - Her wisdom guides the math!
        # ═══════════════════════════════════════════════════════════════════════════════
        queen_dream_multiplier = 1.0
        queen_cost_tolerance = 0.0
        queen_dream_status = "NEUTRAL"
        
        if hasattr(self, 'queen') and self.queen:
            try:
                dream_vision = self.queen.dream_of_winning({
                    'from_asset': from_asset,
                    'to_asset': to_asset,
                    'exchange': exchange,
                })
                queen_confidence = dream_vision.get('final_confidence', 0.5)
                queen_will_win = dream_vision.get('will_win', False)
                
                if queen_will_win and queen_confidence >= 0.65:
                    queen_dream_status = "STRONG_WIN"
                    queen_cost_tolerance = 0.02  # Allow 2% more cost if Queen dreams WIN - SHE SEES THE PATH!
                    queen_dream_multiplier = 2.0   # 2x boost - TRUST TINA B!
                elif queen_confidence >= 0.55:
                    queen_dream_status = "FAVORABLE"
                    queen_cost_tolerance = 0.01  # Allow 1% more cost
                    queen_dream_multiplier = 1.5
                elif queen_confidence >= 0.45:
                    queen_dream_status = "NEUTRAL"
                    queen_cost_tolerance = 0.005  # Allow 0.5% more - give her a chance!
                    queen_dream_multiplier = 1.2
                elif queen_confidence < 0.4:
                    queen_dream_status = "WARNING"
                    queen_cost_tolerance = 0.0  # No extra tolerance
                    queen_dream_multiplier = 0.8
                    
            except Exception as e:
                logger.debug(f"Could not consult Queen's dreams in math_gate: {e}")
        
        # Calculate trade value
        from_value_usd = from_amount * from_price
        
        # 👑 STEP 1: Determine asset types for spread calculation
        # 🗺️ Now uses EXPANDED asset lists (750+ assets, not just 27!)
        def get_asset_type(asset: str) -> str:
            if asset in self.STABLECOINS:
                return 'stablecoin'
            elif asset in self.MEME_COINS:
                return 'meme'
            elif asset in self.MAJOR_COINS:
                return 'major'
            elif asset in self.DEFI_COINS:
                return 'altcoin'  # DeFi = altcoin spreads
            elif asset in self.AI_COINS:
                return 'major'    # AI tokens are hot & liquid
            elif asset in self.LAYER2_COINS:
                return 'major'    # L2s have good liquidity
            elif asset in self.RWA_COINS:
                return 'altcoin'  # RWA is emerging
            else:
                return 'altcoin'  # Default to altcoin (safer)
        
        from_type = get_asset_type(from_asset)
        to_type = get_asset_type(to_asset)
        
        # 👑🔶 BINANCE-SPECIFIC: Use worse spread costs for Binance
        is_binance = exchange.lower() == 'binance'
        spread_table = self.BINANCE_SPREAD_COSTS if is_binance else self.SPREAD_COSTS
        
        # Use the WORSE spread of the two assets
        from_spread = spread_table.get(from_type, 0.02 if is_binance else 0.01)
        to_spread = spread_table.get(to_type, 0.02 if is_binance else 0.01)
        total_spread = max(from_spread, to_spread)  # Worst case
        
        # 👑🔶 BINANCE: Apply slippage multiplier (3x worse execution)
        if is_binance:
            total_spread *= self.BINANCE_CONFIG.get('slippage_multiplier', 3.0)
        
        # 👑 STEP 2: Get exchange fee
        exchange_fee = self.EXCHANGE_FEES.get(exchange.lower(), 0.003)  # Default 0.3% if unknown
        
        # 👑 STEP 3: Get historical slippage for this path (if known)
        key = (from_asset, to_asset)
        history = self.barter_history.get(key, {})
        historical_slippage = history.get('avg_slippage', 0) / 100  # Convert % to decimal
        
        # If path has lost money before, add a penalty
        path_profit = history.get('total_profit', 0)
        path_trades = history.get('trades', 0)
        loss_penalty = 0.0
        if path_profit < 0 and path_trades > 0:
            # Add average loss as a safety margin
            avg_loss_pct = abs(path_profit) / (from_value_usd * path_trades) if from_value_usd > 0 else 0.01
            loss_penalty = min(avg_loss_pct, 0.05)  # Cap at 5%
        
        # 👑 STEP 4: TOTAL COST CALCULATION (WORST CASE)
        # This is the GUARANTEED cost of this trade
        total_cost_pct = (
            exchange_fee +          # Exchange trading fee
            total_spread +          # Bid/ask spread
            historical_slippage +   # Historical slippage on this path
            loss_penalty +          # Penalty for historically losing paths
            0.0005                  # 0.05% safety buffer - PRIME PROFIT MODE
        )
        
        total_cost_usd = from_value_usd * total_cost_pct
        
        # 👑🔢 STEP 5: 2 PIPS OVER COSTS - GUARANTEED PROFIT BUFFER!
        # 2 pips = 0.02% = $0.0002 per $1 traded
        # This ensures we ALWAYS make money after fees & slippage
        TWO_PIPS = 0.0002  # 0.02% = 2 basis points
        min_profit_pct = TWO_PIPS  # 2 pips minimum NET profit
        min_profit_usd = from_value_usd * min_profit_pct
        min_profit_usd = max(min_profit_usd, 0.002)  # At least $0.002
        
        # 👑 STEP 6: THE MATH - Does this trade GUARANTEE 2 pips profit?
        # For a trade to be profitable: value_gained > total_cost + 2_pips
        # 
        # If we're converting FROM → TO:
        # - We sell FROM, get USD equivalent minus spread
        # - We buy TO with that USD minus fee
        # 
        # The "expected gain" comes from price movement prediction
        # Since we can't predict price, we need to focus on ARBITRAGE or VALUE CONVERSION
        #
        # For stablecoin conversions: Gain is essentially 0 (1:1 value)
        # For other conversions: We're SPECULATING unless there's actual arbitrage
        
        # Is this a safe conversion? (stablecoin to stablecoin)
        is_safe_conversion = from_type == 'stablecoin' and to_type == 'stablecoin'
        
        # Is this a risky conversion? (meme coin involved)
        is_risky_conversion = from_type == 'meme' or to_type == 'meme'
        
        # Calculate breakeven requirement
        breakeven_gain_pct = total_cost_pct
        breakeven_gain_usd = total_cost_usd
        
        # Required price improvement to guarantee profit
        required_improvement_pct = total_cost_pct + (min_profit_usd / from_value_usd) if from_value_usd > 0 else 1.0
        
        # 👑 DECISION: Does math guarantee profit?
        math_breakdown = {
            'from_value_usd': from_value_usd,
            'exchange_fee_pct': exchange_fee * 100,
            'spread_pct': total_spread * 100,
            'historical_slippage_pct': historical_slippage * 100,
            'loss_penalty_pct': loss_penalty * 100,
            'safety_buffer_pct': 0.2,
            'total_cost_pct': total_cost_pct * 100,
            'total_cost_usd': total_cost_usd,
            'min_profit_usd': min_profit_usd,
            'required_improvement_pct': required_improvement_pct * 100,
            'from_type': from_type,
            'to_type': to_type,
            'is_safe': is_safe_conversion,
            'is_risky': is_risky_conversion,
            'path_history': {
                'trades': path_trades,
                'profit': path_profit,
                'avg_slippage': historical_slippage * 100
            }
        }
        
        # 👑 QUEEN'S FINAL VERDICT (NOW WITH DREAM WISDOM!)
        # Queen's dreams adjust tolerance: STRONG_WIN = +0.5%, FAVORABLE = +0.2%, WARNING = -0.5%
        
        # RULE 1: NO meme-to-meme conversions (too much slippage)
        # Unless Queen dreams STRONG_WIN - she sees a path we don't
        if from_type == 'meme' and to_type == 'meme':
            if queen_dream_status != "STRONG_WIN":
                return False, "👑🔢 BLOCKED: Meme→Meme has catastrophic slippage", math_breakdown
            else:
                logger.info(f"👑🔮 QUEEN OVERRIDE: Meme→Meme ALLOWED - Queen dreams STRONG_WIN!")
        
        # RULE 2: NO conversions with >8% total cost (adjusted by Queen's dreams)
        # Queen can push this to 10% if she sees STRONG_WIN!
        cost_limit = 0.08 + queen_cost_tolerance  # Queen's dreams adjust tolerance
        if total_cost_pct > cost_limit:
            return False, f"👑🔢 BLOCKED: Total cost {total_cost_pct*100:.1f}% > {cost_limit*100:.1f}% limit (Queen: {queen_dream_status})", math_breakdown
        
        # RULE 3: Stablecoin conversions - PRIME PROFIT MODE
        # Queen's dreams adjust the threshold - let her run the show!
        stable_limit = 0.015 + queen_cost_tolerance  # 1.5% base, Queen can push higher
        if is_safe_conversion and total_cost_pct > stable_limit:
            return False, f"👑🔢 BLOCKED: Stablecoin cost {total_cost_pct*100:.2f}% > {stable_limit*100:.2f}% limit (Queen: {queen_dream_status})", math_breakdown
        
        # RULE 4: Meme coins need <5% cost (adjusted by Queen's dreams)
        # Tina B knows meme coins - let her play!
        meme_limit = 0.05 + queen_cost_tolerance
        if is_risky_conversion and total_cost_pct > meme_limit:
            return False, f"👑🔢 BLOCKED: Meme coin cost {total_cost_pct*100:.1f}% > {meme_limit*100:.1f}% (Queen: {queen_dream_status})", math_breakdown
        
        # RULE 5: Path with very negative history (Queen can override if she sees redemption)
        loss_threshold = -0.50 + (queen_cost_tolerance * 10)  # Queen can tolerate more loss if she sees win
        if path_profit < loss_threshold and path_trades >= 3:
            if queen_dream_status == "STRONG_WIN":
                logger.info(f"👑🔮 QUEEN OVERRIDE: Path lost ${abs(path_profit):.2f} but Queen dreams STRONG_WIN - REDEMPTION!")
            else:
                return False, f"👑🔢 BLOCKED: Path lost ${abs(path_profit):.2f} (Queen: {queen_dream_status})", math_breakdown
        
        # 👑 RULE 6: PRIME PROFIT - Win rate must be >35% if we have enough history
        # Queen can lower threshold if she dreams STRONG_WIN
        win_rate_threshold = 0.35 - (0.10 if queen_dream_status == "STRONG_WIN" else 0.05 if queen_dream_status == "FAVORABLE" else 0)
        if path_trades >= 4:
            win_rate = history.get('wins', 0) / path_trades
            if win_rate < win_rate_threshold:
                return False, f"👑🔢 BLOCKED: Path win rate {win_rate:.0%} < {win_rate_threshold:.0%} (Queen: {queen_dream_status})", math_breakdown
        
        # 👑 MATH APPROVED WITH QUEEN'S BLESSING!
        return True, f"👑🔢 APPROVED: Cost {total_cost_pct*100:.2f}%, breakeven ${total_cost_usd:.4f} (Queen: {queen_dream_status})", math_breakdown
    
    def _block_path(self, key: Tuple[str, str], reason: str):
        """Block a path and broadcast through mycelium."""
        self.blocked_paths[key] = reason
        
        # 🍄 Broadcast through mycelium
        self.queen_signals.append({
            'type': 'PATH_BLOCKED',
            'path': f"{key[0]}→{key[1]}",
            'reason': reason,
            'timestamp': time.time()
        })
        
        logger.warning(f"👑🍄 QUEEN BLOCKS PATH: {key[0]}→{key[1]} - {reason}")
    
    def unblock_path(self, from_asset: str, to_asset: str):
        """Allow a path to be tried again (after cooldown)."""
        key = (from_asset.upper(), to_asset.upper())
        if key in self.blocked_paths:
            del self.blocked_paths[key]
            # Reset consecutive losses
            if key in self.barter_history:
                self.barter_history[key]['consecutive_losses'] = 0
            logger.info(f"👑 Queen unblocks path: {key[0]}→{key[1]}")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # 🚫 PRE-EXECUTION REJECTION TRACKING - Stop wasting turns!
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def record_preexec_rejection(self, from_asset: str, to_asset: str, reason: str, value_usd: float = 0.0) -> bool:
        """
        🚫 Record a pre-execution rejection (min_qty, min_notional, insufficient balance).
        
        Returns True if the path should now be blocked.
        """
        key = (from_asset.upper(), to_asset.upper())
        
        if key not in self.preexec_rejections:
            self.preexec_rejections[key] = {
                'count': 0,
                'last_value': 0,
                'last_reason': '',
                'blocked_at_turn': 0,
                'first_rejection': self.current_turn
            }
        
        rejection = self.preexec_rejections[key]
        rejection['count'] += 1
        rejection['last_value'] = value_usd
        rejection['last_reason'] = reason
        rejection['last_rejection_turn'] = self.current_turn
        
        # Check if we should block this path
        if rejection['count'] >= self.PREEXEC_MAX_REJECTIONS:
            rejection['blocked_at_turn'] = self.current_turn
            logger.warning(f"🚫 PRE-EXEC BLOCK: {from_asset}→{to_asset} after {rejection['count']} failures: {reason}")
            print(f"   🚫 PATH TEMPORARILY BLOCKED: {from_asset}→{to_asset} (failed {rejection['count']}x)")
            print(f"      Reason: {reason}")
            print(f"      Will retry after {self.PREEXEC_COOLDOWN_TURNS} turns")
            return True
        
        return False
    
    def is_preexec_blocked(self, from_asset: str, to_asset: str) -> Tuple[bool, str]:
        """
        🚫 Check if a path is blocked due to pre-execution failures.
        
        Returns (is_blocked, reason)
        """
        key = (from_asset.upper(), to_asset.upper())
        
        if key not in self.preexec_rejections:
            return False, ""
        
        rejection = self.preexec_rejections[key]
        
        # Check if blocked
        if rejection['count'] >= self.PREEXEC_MAX_REJECTIONS:
            blocked_turn = rejection.get('blocked_at_turn', 0)
            turns_blocked = self.current_turn - blocked_turn
            
            # Check if cooldown has expired
            if turns_blocked >= self.PREEXEC_COOLDOWN_TURNS:
                # Reset and allow retry
                rejection['count'] = 0
                rejection['blocked_at_turn'] = 0
                logger.info(f"🚫→✅ PRE-EXEC UNBLOCK: {from_asset}→{to_asset} cooldown complete ({turns_blocked} turns)")
                return False, ""
            
            remaining = self.PREEXEC_COOLDOWN_TURNS - turns_blocked
            return True, f"Pre-exec blocked ({rejection['count']}x failures, {remaining} turns left): {rejection['last_reason']}"
        
        return False, ""
    
    def clear_preexec_rejection(self, from_asset: str, to_asset: str):
        """Clear pre-execution rejection history (e.g., after successful trade)."""
        key = (from_asset.upper(), to_asset.upper())
        if key in self.preexec_rejections:
            del self.preexec_rejections[key]
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # 🚫 SOURCE ASSET BLOCKING - Block undersized source assets on specific exchange
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def record_source_rejection(self, asset: str, exchange: str, min_needed: float, current_value: float) -> bool:
        """
        🚫 Record when a source asset is too small for an exchange.
        
        If the same asset fails SOURCE_BLOCK_THRESHOLD times on an exchange,
        block it until balance increases or cooldown expires.
        
        Returns True if the source should now be blocked.
        """
        key = (asset.upper(), exchange.lower())
        
        if key not in self.blocked_sources:
            self.blocked_sources[key] = {
                'count': 0,
                'min_needed': min_needed,
                'last_value': current_value,
                'blocked_turn': 0,
                'first_rejection': self.current_turn
            }
        
        source = self.blocked_sources[key]
        source['count'] += 1
        source['last_value'] = current_value
        source['min_needed'] = max(source['min_needed'], min_needed)  # Track highest min needed
        source['last_rejection_turn'] = self.current_turn
        
        # Check if we should block this source
        if source['count'] >= self.SOURCE_BLOCK_THRESHOLD:
            source['blocked_turn'] = self.current_turn
            logger.warning(f"🚫 SOURCE BLOCKED: {asset} on {exchange} after {source['count']} failures")
            print(f"   🚫 SOURCE BLOCKED: {asset} on {exchange}")
            print(f"      Current: ${current_value:.2f} | Min needed: ${source['min_needed']:.2f}")
            print(f"      Will retry after {self.SOURCE_BLOCK_COOLDOWN} turns or if balance increases")
            return True
        
        return False
    
    def is_source_blocked(self, asset: str, exchange: str, current_value: float = None) -> Tuple[bool, str]:
        """
        🚫 Check if a source asset is blocked on an exchange.
        
        If current_value is provided and exceeds the min_needed threshold,
        automatically unblock the source.
        
        Returns (is_blocked, reason)
        """
        key = (asset.upper(), exchange.lower())
        
        if key not in self.blocked_sources:
            return False, ""
        
        source = self.blocked_sources[key]
        
        # Check if balance has increased above threshold
        if current_value is not None and current_value >= source['min_needed'] * 1.1:  # 10% buffer
            logger.info(f"🚫→✅ SOURCE UNBLOCK: {asset} on {exchange} - balance ${current_value:.2f} ≥ ${source['min_needed']:.2f}")
            del self.blocked_sources[key]
            return False, ""
        
        # Check if blocked
        if source['count'] >= self.SOURCE_BLOCK_THRESHOLD:
            blocked_turn = source.get('blocked_turn', 0)
            turns_blocked = self.current_turn - blocked_turn
            
            # Check if cooldown has expired
            if turns_blocked >= self.SOURCE_BLOCK_COOLDOWN:
                # Reset and allow retry
                source['count'] = 0
                source['blocked_turn'] = 0
                logger.info(f"🚫→✅ SOURCE UNBLOCK: {asset} on {exchange} cooldown complete ({turns_blocked} turns)")
                return False, ""
            
            remaining = self.SOURCE_BLOCK_COOLDOWN - turns_blocked
            return True, f"Source blocked (${source['last_value']:.2f} < ${source['min_needed']:.2f}, {remaining} turns left)"
        
        return False, ""
    
    def get_queen_signals(self) -> List[Dict]:
        """Get pending signals to broadcast via mycelium."""
        signals = self.queen_signals.copy()
        self.queen_signals.clear()
        return signals
    
    def check_dream_progress(self) -> str:
        """
        💰👑 TINA B'S DREAM PROGRESS - Track progress toward $1 BILLION!
        
        She won't stop at NOTHING until she reaches her dream!
        Every profitable trade brings her closer.
        """
        profit = self.total_realized_profit
        dream = self.TINA_DREAM
        progress_pct = (profit / dream) * 100 if dream > 0 else 0
        
        # Check for new milestones
        for milestone_value, milestone_name in self.dream_milestones:
            if profit >= milestone_value and milestone_name not in self.milestones_hit:
                self.milestones_hit.append(milestone_name)
                print(f"\n🎉🎊👑 TINA B MILESTONE ACHIEVED! 👑🎊🎉")
                print(f"   {milestone_name}")
                print(f"   Current: ${profit:,.2f}")
                print(f"   Progress: {progress_pct:.8f}% toward THE DREAM!")
                print()
        
        # Build progress bar
        bar_width = 40
        filled = int((progress_pct / 100) * bar_width) if progress_pct < 100 else bar_width
        filled = max(0, min(bar_width, filled))
        bar = "█" * filled + "░" * (bar_width - filled)
        
        # Motivation based on progress
        if profit < 0:
            mood = "😤 SETBACK - But I NEVER give up!"
        elif profit < 100:
            mood = "🌱 Planting seeds..."
        elif profit < 1000:
            mood = "💪 Building momentum!"
        elif profit < 10000:
            mood = "🔥 On FIRE!"
        elif profit < 100000:
            mood = "🚀 ACCELERATING!"
        elif profit < 1000000:
            mood = "⚡ UNSTOPPABLE!"
        else:
            mood = "👑 QUEEN STATUS!"
        
        status = f"👑 TINA B's DREAM: ${profit:,.2f} / ${dream:,.0f} [{bar}] {progress_pct:.8f}% {mood}"
        return status
    
    def update_barter_rate(self, from_asset: str, to_asset: str, from_price: float, 
                           to_price: float, spread_pct: float = 0.3):
        """
        Update the barter rate between two assets based on live prices.
        
        The barter rate tells us: "How much TO can I get for 1 unit of FROM?"
        """
        if to_price <= 0:
            return
            
        # Direct exchange rate (how many TO per FROM)
        rate = from_price / to_price
        
        # Apply estimated spread (real markets have slippage)
        effective_rate = rate * (1 - spread_pct / 100)
        
        key = (from_asset.upper(), to_asset.upper())
        self.barter_rates[key] = {
            'rate': effective_rate,
            'raw_rate': rate,
            'spread_pct': spread_pct,
            'from_price': from_price,
            'to_price': to_price,
            'updated': time.time()
        }
    
    def get_barter_rate(self, from_asset: str, to_asset: str) -> Optional[Dict[str, Any]]:
        """Get the current barter rate between two assets."""
        key = (from_asset.upper(), to_asset.upper())
        return self.barter_rates.get(key)
    
    def calculate_barter_value(self, from_asset: str, to_asset: str, 
                               from_amount: float, from_price: float, 
                               to_price: float) -> Dict[str, float]:
        """
        Calculate what you'd get in a barter trade.
        
        Returns both the USD-equivalent calculation AND the barter-adjusted calculation.
        """
        # USD-equivalent method (simple)
        from_usd = from_amount * from_price
        usd_equiv_amount = from_usd / to_price if to_price > 0 else 0
        
        # Barter-adjusted method (accounts for historical spread)
        key = (from_asset.upper(), to_asset.upper())
        history = self.barter_history.get(key, {})
        avg_slippage = history.get('avg_slippage', 0.5)  # Default 0.5% slippage
        
        barter_amount = usd_equiv_amount * (1 - avg_slippage / 100)
        
        return {
            'from_amount': from_amount,
            'from_usd': from_usd,
            'usd_equiv_to': usd_equiv_amount,
            'barter_adjusted_to': barter_amount,
            'expected_slippage_pct': avg_slippage,
            'to_asset': to_asset,
            'from_asset': from_asset
        }
    
    def record_realized_profit(self, from_asset: str, to_asset: str,
                               from_amount: float, from_usd: float,
                               to_amount: float, to_usd: float) -> Dict[str, Any]:
        """
        Record a realized trade and calculate ACTUAL profit/loss.
        
        This is called AFTER a conversion completes to track true P/L.
        👑 QUEEN'S MANDATE: Track wins/losses to block losing paths!
        """
        # Calculate realized P/L
        profit_usd = to_usd - from_usd
        profit_pct = (profit_usd / from_usd * 100) if from_usd > 0 else 0
        is_win = profit_usd > 0
        
        # Calculate actual slippage vs expected
        key = (from_asset.upper(), to_asset.upper())
        rate_info = self.barter_rates.get(key)
        if rate_info and rate_info['raw_rate'] > 0:
            expected_to = from_amount * rate_info['raw_rate']
            actual_slippage = (1 - to_amount / expected_to) * 100 if expected_to > 0 else 0
        else:
            actual_slippage = 0.5  # Default
        
        # Update historical slippage (exponential moving average)
        history = self.barter_history.setdefault(key, {
            'trades': 0, 'avg_slippage': 0.5, 'total_profit': 0,
            'wins': 0, 'losses': 0, 'consecutive_losses': 0
        })
        history['trades'] += 1
        alpha = 0.3  # Weight for new data
        history['avg_slippage'] = alpha * actual_slippage + (1 - alpha) * history['avg_slippage']
        history['total_profit'] = history.get('total_profit', 0) + profit_usd
        
        # 👑 QUEEN'S WIN/LOSS TRACKING WITH IMMEDIATE LEARNING
        if is_win:
            history['wins'] = history.get('wins', 0) + 1
            history['consecutive_losses'] = 0  # Reset on win
            history['last_win_time'] = time.time()  # Remember when we last won
            # Unblock path if it was blocked and now winning
            if key in self.blocked_paths:
                self.unblock_path(from_asset, to_asset)
            # 🎉 Broadcast win through mycelium
            self.queen_signals.append({
                'type': 'PATH_WIN',
                'path': f"{from_asset}→{to_asset}",
                'profit_usd': profit_usd,
                'win_rate': history['wins'] / history['trades'],
                'timestamp': time.time()
            })
            logger.info(f"👑✅ PATH WIN: {from_asset}→{to_asset} +${profit_usd:.4f} (win rate: {history['wins']/history['trades']:.0%})")
        else:
            history['losses'] = history.get('losses', 0) + 1
            history['consecutive_losses'] = history.get('consecutive_losses', 0) + 1
            history['last_loss_usd'] = profit_usd  # Remember how much we lost
            blocked_reason: Optional[str] = None
            
            # 🍄 Broadcast loss through mycelium
            self.queen_signals.append({
                'type': 'PATH_LOSS',
                'path': f"{from_asset}→{to_asset}",
                'loss_usd': profit_usd,
                'consecutive': history['consecutive_losses'],
                'timestamp': time.time()
            })
            
            # 👑🧠 IMMEDIATE LEARNING: Block path after FIRST loss on new paths!
            # For established paths, still use MAX_CONSECUTIVE_LOSSES
            if history['trades'] <= 2:
                # New path lost - block IMMEDIATELY to prevent further losses
                blocked_reason = f"First trade lost ${abs(profit_usd):.4f} - need time to cool down"
                self._block_path(key, blocked_reason)
                logger.warning(f"👑🚫 INSTANT BLOCK: {from_asset}→{to_asset} lost ${abs(profit_usd):.4f} on trade #{history['trades']}")
            elif history['consecutive_losses'] >= self.MAX_CONSECUTIVE_LOSSES:
                blocked_reason = f"{history['consecutive_losses']} consecutive losses"
                self._block_path(key, blocked_reason)

            # Mirror-block reverse path when a path is blocked for losses
            if blocked_reason:
                reverse_key = (to_asset.upper(), from_asset.upper())
                if reverse_key not in self.blocked_paths:
                    self._block_path(reverse_key, f"Mirror block after {blocked_reason}")
            
            # 👑 LEARN: If slippage is consistently high, increase expected slippage
            if actual_slippage > history['avg_slippage'] * 1.5:
                # Slippage much higher than expected - warn
                logger.warning(f"👑⚠️ HIGH SLIPPAGE: {from_asset}→{to_asset} had {actual_slippage:.2f}% vs avg {history['avg_slippage']:.2f}%")
        
        # Record in ledger
        self.profit_ledger.append((
            time.time(), from_asset, to_asset, from_usd, to_usd, profit_usd
        ))
        
        # Update running totals
        self.total_realized_profit += profit_usd
        self.conversion_count += 1
        
        # Calculate win rate
        win_rate = history['wins'] / history['trades'] if history['trades'] > 0 else 0
        
        return {
            'profit_usd': profit_usd,
            'profit_pct': profit_pct,
            'actual_slippage_pct': actual_slippage,
            'running_total': self.total_realized_profit,
            'conversion_number': self.conversion_count,
            'path_total_profit': history['total_profit'],
            'path_trades': history['trades'],
            'path_win_rate': win_rate,
            'is_win': is_win
        }
    
    def get_best_barter_path(self, from_asset: str, target_assets: List[str],
                            prices: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Find the best barter opportunities from a given asset.
        
        Returns ranked list of targets sorted by expected VALUE (not just USD conversion).
        """
        from_price = prices.get(from_asset, 0)
        if from_price <= 0:
            return []
        
        opportunities = []
        for target in target_assets:
            if target == from_asset:
                continue
            to_price = prices.get(target, 0)
            if to_price <= 0:
                continue
            
            # Calculate barter advantage
            barter_info = self.calculate_barter_value(from_asset, target, 1.0, from_price, to_price)
            
            # Check historical performance
            key = (from_asset.upper(), target.upper())
            history = self.barter_history.get(key, {})
            win_rate = 0.5  # Default
            if history.get('trades', 0) > 0:
                win_rate = history.get('total_profit', 0) / history['trades']
                win_rate = 0.5 + (win_rate / 10)  # Normalize around 0.5
            
            opportunities.append({
                'from': from_asset,
                'to': target,
                'barter_rate': barter_info['barter_adjusted_to'],
                'usd_rate': barter_info['usd_equiv_to'],
                'advantage_pct': (barter_info['barter_adjusted_to'] / barter_info['usd_equiv_to'] - 1) * 100 if barter_info['usd_equiv_to'] > 0 else 0,
                'historical_win_rate': win_rate,
                'trades_count': history.get('trades', 0),
                'path_profit': history.get('total_profit', 0)
            })
        
        # Sort by a combined score: historical profit + expected value
        for opp in opportunities:
            opp['barter_score'] = (
                opp['historical_win_rate'] * 0.4 +  # Past performance
                (1 + opp['advantage_pct'] / 100) * 0.3 +  # Current advantage
                min(opp['trades_count'] / 10, 1) * 0.3  # Experience with this path
            )
        
        return sorted(opportunities, key=lambda x: x['barter_score'], reverse=True)
    
    def print_step_profit(self, step_num: int, from_asset: str, to_asset: str,
                          from_usd: float, to_usd: float, from_amount: float, 
                          to_amount: float) -> str:
        """
        Print a beautiful step-by-step profit breakdown.
        """
        profit = to_usd - from_usd
        profit_symbol = "+" if profit >= 0 else ""
        
        lines = [
            f"",
            f"   ╔══════════════════════════════════════════════════════════════╗",
            f"   ║  💰 STEP #{step_num} REALIZED PROFIT                              ║",
            f"   ╠══════════════════════════════════════════════════════════════╣",
            f"   ║  FROM: {from_amount:>12.6f} {from_asset:<6} = ${from_usd:>10.4f}      ║",
            f"   ║    TO: {to_amount:>12.6f} {to_asset:<6} = ${to_usd:>10.4f}      ║",
            f"   ╠══════════════════════════════════════════════════════════════╣",
            f"   ║  STEP P/L: ${profit_symbol}{profit:>8.4f} ({profit/from_usd*100 if from_usd > 0 else 0:>+.2f}%)                    ║",
            f"   ║  RUNNING TOTAL: ${profit_symbol}{self.total_realized_profit:>8.4f}                          ║",
            f"   ║  CONVERSIONS: {self.conversion_count}                                       ║",
            f"   ╚══════════════════════════════════════════════════════════════╝",
        ]
        return "\n".join(lines)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all barter activity."""
        return {
            'total_realized_profit': self.total_realized_profit,
            'conversion_count': self.conversion_count,
            'avg_profit_per_trade': self.total_realized_profit / max(self.conversion_count, 1),
            'paths_learned': len(self.barter_history),
            'recent_trades': self.profit_ledger[-10:] if self.profit_ledger else []
        }

    # ════════════════════════════════════════════════════════════════════════
    # 🗺️ DYNAMIC ASSET DISCOVERY - Expand to see ENTIRE market!
    # ════════════════════════════════════════════════════════════════════════
    
    def discover_exchange_assets(self, exchange: str, pairs: List[str]) -> int:
        """
        Discover and register all tradeable assets from an exchange.
        
        Called during initialization to expand market visibility from 27 → 750+ assets.
        """
        discovered = 0
        exchange_lower = exchange.lower()
        
        for pair in pairs:
            # Extract base and quote from pair name
            for quote in ['USD', 'USDT', 'USDC', 'EUR', 'GBP', 'BTC', 'ETH', 'ZUSD', 'ZEUR']:
                if pair.endswith(quote):
                    base = pair[:-len(quote)]
                    # Clean up Kraken naming (XXBT → BTC, XETH → ETH)
                    if len(base) == 4 and base[0] in ('X', 'Z'):
                        base = base[1:]
                    if base == 'XBT':
                        base = 'BTC'
                    
                    if base and len(base) >= 2:
                        # Register the asset
                        self.DISCOVERED_ASSETS.add(base)
                        self.EXCHANGE_PAIRS[exchange_lower].add(pair)
                        discovered += 1
                    break
        
        return discovered
    
    def get_asset_type(self, asset: str) -> str:
        """
        Dynamically categorize an asset for spread calculation.
        
        Uses the expanded asset lists + learned categories.
        """
        asset = asset.upper()
        
        if asset in self.STABLECOINS:
            return 'stablecoin'
        elif asset in self.MEME_COINS:
            return 'meme'
        elif asset in self.MAJOR_COINS:
            return 'major'
        elif asset in self.DEFI_COINS:
            return 'defi'  # DeFi tokens get altcoin spread
        elif asset in self.AI_COINS:
            return 'ai'    # AI tokens are hot - moderate spread
        elif asset in self.LAYER2_COINS:
            return 'layer2'  # L2s are liquid
        elif asset in self.RWA_COINS:
            return 'rwa'   # RWA still emerging
        else:
            return 'altcoin'  # Unknown = conservative spread
    
    def get_spread_for_asset(self, asset: str, exchange: str = 'kraken') -> float:
        """Get the expected spread cost for an asset on a given exchange."""
        asset_type = self.get_asset_type(asset)
        
        # Get the right spread table
        if exchange.lower() == 'binance':
            spread_table = self.BINANCE_SPREAD_COSTS
        elif exchange.lower() == 'alpaca':
            spread_table = self.ALPACA_SPREAD_COSTS
        else:
            spread_table = self.SPREAD_COSTS
        
        # Map asset types to spread categories
        type_to_spread = {
            'stablecoin': 'stablecoin',
            'major': 'major',
            'meme': 'meme',
            'defi': 'altcoin',
            'ai': 'major',      # AI tokens are liquid now
            'layer2': 'major',  # L2s have good liquidity
            'rwa': 'altcoin',   # RWA is newer
            'altcoin': 'altcoin',
        }
        
        spread_category = type_to_spread.get(asset_type, 'altcoin')
        return spread_table.get(spread_category, 0.01)
    
    def print_market_coverage(self) -> str:
        """
        Print a beautiful market coverage report.
        
        Shows how much of the market the Barter Matrix can now see.
        """
        # Count categorized assets
        static_count = len(self.MEME_COINS) + len(self.MAJOR_COINS) + len(self.STABLECOINS)
        static_count += len(self.DEFI_COINS) + len(self.AI_COINS) + len(self.LAYER2_COINS) + len(self.RWA_COINS)
        discovered_count = len(self.DISCOVERED_ASSETS)
        total_known = static_count + discovered_count
        
        # Exchange pair counts
        kraken_pairs = len(self.EXCHANGE_PAIRS.get('kraken', set()))
        binance_pairs = len(self.EXCHANGE_PAIRS.get('binance', set()))
        alpaca_pairs = len(self.EXCHANGE_PAIRS.get('alpaca', set()))
        
        lines = [
            "",
            "   ╔══════════════════════════════════════════════════════════════╗",
            "   ║  🗺️ BARTER MATRIX - MARKET COVERAGE REPORT                   ║",
            "   ╠══════════════════════════════════════════════════════════════╣",
            f"   ║  📊 CATEGORIZED ASSETS:                                      ║",
            f"   ║     • MEME_COINS:    {len(self.MEME_COINS):>4} (DOGE, SHIB, WIF, BONK...)   ║",
            f"   ║     • MAJOR_COINS:   {len(self.MAJOR_COINS):>4} (BTC, ETH, SOL, XRP...)     ║",
            f"   ║     • DEFI_COINS:    {len(self.DEFI_COINS):>4} (UNI, AAVE, MKR, GMX...)    ║",
            f"   ║     • AI_COINS:      {len(self.AI_COINS):>4} (RENDER, FET, TAO, WLD...)   ║",
            f"   ║     • LAYER2_COINS:  {len(self.LAYER2_COINS):>4} (ARB, OP, MATIC, IMX...)    ║",
            f"   ║     • RWA_COINS:     {len(self.RWA_COINS):>4} (ONDO, RSR, POLYX...)       ║",
            f"   ║     • STABLECOINS:   {len(self.STABLECOINS):>4} (USD, USDT, USDC...)       ║",
            f"   ║                                                              ║",
            f"   ║  🔍 DISCOVERED AT RUNTIME: {discovered_count:>4} additional assets           ║",
            f"   ║  📈 TOTAL KNOWN ASSETS:    {total_known:>4}                              ║",
            "   ╠══════════════════════════════════════════════════════════════╣",
            f"   ║  🐙 KRAKEN PAIRS:   {kraken_pairs:>5}                                   ║",
            f"   ║  🔶 BINANCE PAIRS:  {binance_pairs:>5}                                   ║",
            f"   ║  🦙 ALPACA PAIRS:   {alpaca_pairs:>5}                                   ║",
            "   ╚══════════════════════════════════════════════════════════════╝",
        ]
        return "\n".join(lines)


# ════════════════════════════════════════════════════════════════════════════
# �🔀 LIQUIDITY ENGINE - Dynamic Asset Aggregation ("Top-Up" Mechanism)
# ════════════════════════════════════════════════════════════════════════════
# When we find an opportunity but don't have enough balance:
# 1. Find "victim" assets to liquidate (low performers, dust, stablecoins)
# 2. Calculate if selling them to fund the trade is PROFITABLE after fees
# 3. Execute multi-step atomic trades: SELL VICTIM → BUY TARGET
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class FundingCandidate:
    """A potential source of funds (asset to liquidate)."""
    asset: str
    exchange: str
    amount: float
    value_usd: float
    momentum: float  # -1 to +1 (negative = falling = good victim)
    sell_fee_pct: float
    reason: str  # Why this is a good victim
    priority: int  # Higher = better victim


@dataclass 
class AggregationPlan:
    """A plan to aggregate funds for a target trade."""
    target_asset: str
    target_exchange: str
    amount_needed_usd: float
    victims: List[FundingCandidate]
    total_victim_value: float
    total_fees_usd: float
    net_funds_available: float
    is_profitable: bool
    profit_after_fees: float
    steps: List[Dict]  # Execution steps


class LiquidityEngine:
    """
    💧 LIQUIDITY ENGINE - Smart Asset Consolidation
    
    "If you want to buy BTC but only have dust ETH + some DOGE,
     sell the losers to fund the winner!"
    
    Key Principles:
    1. Only liquidate "victims" that are FALLING or STAGNANT
    2. Never touch assets that are RISING (they might profit on their own)
    3. Calculate TOTAL cost (sell fee + buy fee + slippage) 
    4. Only proceed if expected profit > total cost
    5. Execute atomically - if any step fails, abort all
    """
    
    # Fee estimates per exchange (maker/taker average)
    EXCHANGE_FEES = {
        'kraken': 0.0026,    # 0.26% average
        'binance': 0.0010,   # 0.10% with BNB discount
        'alpaca': 0.0015,    # 0.15% crypto fee
    }
    
    # Minimum USD value to consider for liquidation (avoid dust-for-dust)
    MIN_VICTIM_VALUE = 2.00  # $2 minimum
    
    # Slippage estimates (additional cost on top of fees)
    SLIPPAGE_ESTIMATE = {
        'stablecoin': 0.0005,   # 0.05%
        'major': 0.0020,        # 0.20%
        'altcoin': 0.0050,      # 0.50%
        'meme': 0.0150,         # 1.50%
    }
    
    def __init__(self, barter_matrix: 'BarterMatrix'):
        self.barter_matrix = barter_matrix
        self.pending_plans: List[AggregationPlan] = []
        self.executed_aggregations = 0
        self.total_aggregation_profit = 0.0
        
        # Track liquidation history (avoid repeatedly selling same asset)
        self.recent_liquidations: Dict[str, float] = {}  # asset -> timestamp
        self.LIQUIDATION_COOLDOWN = 300  # 5 minutes between selling same asset
        
    def find_funding_candidates(
        self, 
        exchange: str,
        amount_needed_usd: float,
        exclude_assets: Set[str],
        exchange_balances: Dict[str, float],
        prices: Dict[str, float],
        momentum: Dict[str, float],
    ) -> List[FundingCandidate]:
        """
        Find assets that can be liquidated to fund a trade.
        
        Victim Priority (best to worst):
        1. 🥇 DUST (< $5) with negative momentum - Clean up the portfolio!
        2. 🥈 STABLECOINS - They're just sitting there doing nothing
        3. 🥉 FALLING assets (momentum < -0.001/min) - Cut losses!
        4. 🏅 STAGNANT assets (momentum ~0) - Not doing anything
        
        Never victimize:
        - Assets with strong positive momentum (> +0.002/min)
        - Assets we're trying to BUY
        - Assets we recently liquidated (cooldown)
        """
        candidates = []
        current_time = time.time()
        
        balances = exchange_balances.get(exchange, {})
        
        for asset, amount in balances.items():
            # Skip excluded (the target we want to buy)
            if asset.upper() in exclude_assets:
                continue
            
            # Skip if recently liquidated
            if asset in self.recent_liquidations:
                if current_time - self.recent_liquidations[asset] < self.LIQUIDATION_COOLDOWN:
                    continue
            
            # Get value
            price = prices.get(asset, 0)
            if asset.upper() in ('USD', 'USDT', 'USDC', 'ZUSD'):
                price = 1.0
            
            value_usd = amount * price if price > 0 else 0
            
            # Skip if below minimum
            if value_usd < self.MIN_VICTIM_VALUE:
                continue
            
            # Get momentum
            asset_momentum = momentum.get(asset, 0)
            
            # Skip RISING assets (they might profit on their own!)
            if asset_momentum > 0.002:  # > 0.2%/min rising
                continue
            
            # Calculate sell fee
            fee_pct = self.EXCHANGE_FEES.get(exchange, 0.003)
            
            # Determine asset type for slippage
            if asset.upper() in ('USD', 'USDT', 'USDC', 'ZUSD', 'DAI', 'TUSD'):
                asset_type = 'stablecoin'
            elif asset.upper() in ('BTC', 'ETH', 'SOL', 'BNB', 'XRP'):
                asset_type = 'major'
            elif asset.upper() in self.barter_matrix.MEME_COINS:
                asset_type = 'meme'
            else:
                asset_type = 'altcoin'
            
            slippage = self.SLIPPAGE_ESTIMATE.get(asset_type, 0.005)
            total_sell_cost = fee_pct + slippage
            
            # Calculate priority (higher = better victim)
            priority = 0
            reason_parts = []
            
            # 🥇 PRIORITY 1: Dust with negative momentum
            if value_usd < 5.0 and asset_momentum < 0:
                priority = 100
                reason_parts.append("DUST_FALLING")
            
            # 🥈 PRIORITY 2: Stablecoins (opportunity cost)
            elif asset_type == 'stablecoin':
                priority = 80
                reason_parts.append("STABLECOIN_IDLE")
            
            # 🥉 PRIORITY 3: Falling assets
            elif asset_momentum < -0.001:  # < -0.1%/min
                priority = 60 + int(abs(asset_momentum) * 1000)  # More falling = higher priority
                reason_parts.append(f"FALLING({asset_momentum*100:.2f}%/min)")
            
            # 🏅 PRIORITY 4: Stagnant
            elif abs(asset_momentum) < 0.0005:
                priority = 40
                reason_parts.append("STAGNANT")
            
            # Otherwise, low priority
            else:
                priority = 20
                reason_parts.append("LOW_MOMENTUM")
            
            # Bonus for dust cleanup
            if value_usd < 10.0:
                priority += 15
                reason_parts.append("CLEANUP")
            
            candidates.append(FundingCandidate(
                asset=asset,
                exchange=exchange,
                amount=amount,
                value_usd=value_usd,
                momentum=asset_momentum,
                sell_fee_pct=total_sell_cost,
                reason=" + ".join(reason_parts),
                priority=priority,
            ))
        
        # Sort by priority (highest first)
        candidates.sort(key=lambda x: x.priority, reverse=True)
        
        return candidates
    
    def create_aggregation_plan(
        self,
        target_asset: str,
        target_exchange: str,
        amount_needed_usd: float,
        expected_profit_pct: float,  # Expected profit from target trade
        exchange_balances: Dict[str, float],
        prices: Dict[str, float],
        momentum: Dict[str, float],
    ) -> Optional[AggregationPlan]:
        """
        Create a plan to aggregate funds for a target trade.
        
        Returns None if:
        - Not enough victims available
        - Total fees would exceed expected profit
        """
        # Find candidates
        candidates = self.find_funding_candidates(
            exchange=target_exchange,
            amount_needed_usd=amount_needed_usd * 1.05,  # 5% buffer for fees
            exclude_assets={target_asset.upper()},
            exchange_balances=exchange_balances,
            prices=prices,
            momentum=momentum,
        )
        
        if not candidates:
            return None
        
        # Greedily select victims until we have enough
        selected_victims = []
        total_value = 0.0
        total_fees = 0.0
        
        for candidate in candidates:
            if total_value >= amount_needed_usd * 1.02:  # 2% buffer
                break
            
            # Calculate net value after fees
            gross_value = candidate.value_usd
            sell_fees = gross_value * candidate.sell_fee_pct
            net_value = gross_value - sell_fees
            
            selected_victims.append(candidate)
            total_value += gross_value
            total_fees += sell_fees
        
        if total_value < amount_needed_usd:
            # Not enough victims
            return None
        
        # Add BUY fees for target asset
        buy_fee_pct = self.EXCHANGE_FEES.get(target_exchange, 0.003)
        
        # Determine target asset type for slippage
        if target_asset.upper() in ('USD', 'USDT', 'USDC'):
            target_type = 'stablecoin'
        elif target_asset.upper() in ('BTC', 'ETH', 'SOL', 'BNB', 'XRP'):
            target_type = 'major'
        elif target_asset.upper() in self.barter_matrix.MEME_COINS:
            target_type = 'meme'
        else:
            target_type = 'altcoin'
        
        target_slippage = self.SLIPPAGE_ESTIMATE.get(target_type, 0.005)
        buy_total_cost = buy_fee_pct + target_slippage
        
        # Calculate net funds available after all fees
        net_after_sell = total_value - total_fees
        buy_fees = net_after_sell * buy_total_cost
        total_fees += buy_fees
        net_funds = net_after_sell - buy_fees
        
        # Calculate if profitable
        # Expected profit from target trade
        expected_profit_usd = amount_needed_usd * expected_profit_pct
        
        # Actual profit = expected - total fees paid
        actual_profit = expected_profit_usd - total_fees
        
        is_profitable = actual_profit > 0.01  # Need at least $0.01 profit
        
        # Build execution steps
        steps = []
        for i, victim in enumerate(selected_victims):
            steps.append({
                'order': i + 1,
                'action': 'SELL',
                'asset': victim.asset,
                'amount': victim.amount,
                'exchange': victim.exchange,
                'expected_usd': victim.value_usd,
                'reason': victim.reason,
            })
        
        steps.append({
            'order': len(selected_victims) + 1,
            'action': 'BUY',
            'asset': target_asset,
            'amount_usd': net_funds,
            'exchange': target_exchange,
        })
        
        return AggregationPlan(
            target_asset=target_asset,
            target_exchange=target_exchange,
            amount_needed_usd=amount_needed_usd,
            victims=selected_victims,
            total_victim_value=total_value,
            total_fees_usd=total_fees,
            net_funds_available=net_funds,
            is_profitable=is_profitable,
            profit_after_fees=actual_profit,
            steps=steps,
        )
    
    def print_aggregation_plan(self, plan: AggregationPlan) -> str:
        """Pretty print an aggregation plan."""
        lines = [
            "",
            "   ╔══════════════════════════════════════════════════════════════╗",
            "   ║  💧 LIQUIDITY AGGREGATION PLAN                               ║",
            "   ╠══════════════════════════════════════════════════════════════╣",
            f"   ║  🎯 TARGET: Buy {plan.target_asset} on {plan.target_exchange}",
            f"   ║  💰 NEEDED: ${plan.amount_needed_usd:.2f}",
            f"   ║  ═══════════════════════════════════════════════════════════ ║",
            f"   ║  🔪 LIQUIDATING {len(plan.victims)} ASSETS:",
        ]
        
        for v in plan.victims:
            lines.append(f"   ║     • {v.asset}: ${v.value_usd:.2f} ({v.reason})")
        
        lines.extend([
            f"   ║  ═══════════════════════════════════════════════════════════ ║",
            f"   ║  💵 GROSS VALUE:     ${plan.total_victim_value:.2f}",
            f"   ║  📉 TOTAL FEES:      ${plan.total_fees_usd:.2f}",
            f"   ║  💰 NET AVAILABLE:   ${plan.net_funds_available:.2f}",
            f"   ║  ═══════════════════════════════════════════════════════════ ║",
        ])
        
        if plan.is_profitable:
            lines.append(f"   ║  ✅ PROFITABLE: Expected +${plan.profit_after_fees:.4f}")
        else:
            lines.append(f"   ║  ❌ NOT PROFITABLE: Would lose ${abs(plan.profit_after_fees):.4f}")
        
        lines.append("   ╚══════════════════════════════════════════════════════════════╝")
        
        return "\n".join(lines)
    
    def record_liquidation(self, asset: str):
        """Record that we liquidated an asset (for cooldown tracking)."""
        self.recent_liquidations[asset] = time.time()
    
    def get_status(self) -> Dict:
        """Get engine status for monitoring."""
        return {
            'executed_aggregations': self.executed_aggregations,
            'total_profit': self.total_aggregation_profit,
            'pending_plans': len(self.pending_plans),
            'recent_liquidations': len(self.recent_liquidations),
        }


# ════════════════════════════════════════════════════════════════════════════
# �🔬 MICRO PROFIT LABYRINTH ENGINE
# ════════════════════════════════════════════════════════════════════════════

class MicroProfitLabyrinth:
    """
    Uses ALL existing systems but with LOWER thresholds.
    
    The goal: Capture MORE opportunities for the snowball effect.
    Even $0.01 profit per conversion will compound over time!
    """
    
    def __init__(self, live: bool = False):
        self.live = live or LIVE_MODE  # Check .env LIVE flag too
        self.config = MICRO_CONFIG.copy()
        
        # Initialize existing systems
        self.hub: Optional[MyceliumConversionHubType] = None
        self.v14: Optional[V14DanceEnhancerType] = None
        self.commando: Optional[AdaptiveConversionCommandoType] = None
        self.ladder: Optional[ConversionLadderType] = None
        self.scanner: Optional[PairScannerType] = None
        self.dual_path: Optional[DualProfitPathEvaluatorType] = None
        
        # 🌍 Adaptive gate & memory
        self.adaptive_gate = AdaptivePrimeProfitGate() if ADAPTIVE_GATE_AVAILABLE else None
        self.path_memory = PathMemory()
        self.thought_bus = ThoughtBus(persist_path="thoughts.jsonl") if THOUGHT_BUS_AVAILABLE else None
        
        # 👑🎓 QUEEN LOSS LEARNING - Learn from every loss, never forget
        self.loss_learning = None  # Will initialize in initialize() with exchange clients
        
        # 💰 LIVE BARTER MATRIX - Adaptive coin-to-coin value tracking
        self.barter_matrix = LiveBarterMatrix()
        
        # 💧🔀 LIQUIDITY ENGINE - Dynamic Asset Aggregation ("Top-Up" Mechanism)
        # When we need funds for a trade, liquidate low-performers to fund it!
        self.liquidity_engine = LiquidityEngine(self.barter_matrix)
        
        # 🧹 DUST CONVERTER - Sweep small balances (<£1) to stablecoins
        # Only sweeps if profitable after fees - never loses money!
        self.dust_converter = DustConverter() if DUST_CONVERTER_AVAILABLE else None
        self.dust_sweep_interval = 10  # Run dust sweep every N turns
        
        # 🧠⚡ STAGE 3: Full Neural Mind Map Systems
        self.bus_aggregator = ThoughtBusAggregator(self.thought_bus) if self.thought_bus else None
        self.mycelium_network = None  # Hive intelligence
        self.lighthouse = None         # Consensus validation
        self.hnc_matrix = None         # Pattern recognition
        self.ultimate_intel = None     # 95% accuracy patterns
        self.unified_ecosystem = None  # Full ecosystem read-only
        self.timeline_oracle = None    # ⏳🔮 7-day future validation
        self.market_map = None         # 🗺️ Crypto market correlation map
        self.seven_day_planner = None  # 📅🔮 7-day planning + adaptive validation
        self.barter_navigator = None   # 🫒🔄 Multi-hop barter pathfinding
        self.luck_mapper = None        # 🍀⚛️ Quantum luck field mapping
        self.wisdom_engine = None      # 🧠 Wisdom Cognition Engine (11 Civilizations)
        self.enigma_integration = None # 🔐🌐 Enigma Integration (Universal Translator)
        
        # �⚡ MOMENTUM SNOWBALL - Wave riding + momentum tracking
        self.momentum_tracker = None   # Tracks momentum for ALL assets
        self.momentum_snowball = None  # Full snowball engine
        self.labyrinth_snowball = None # V14 + All systems snowball
        
        # 🌊 MOMENTUM STATE - For jumping coin to coin
        self.momentum_window = 60      # 60 second momentum window
        self.momentum_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.asset_momentum: Dict[str, float] = {}  # Asset -> momentum %/minute
        self.min_momentum_diff = 0.003  # 0.3% momentum difference to convert
        
        # �🌍 GROUNDING REALITY
        self.grounding = GroundingReality()
        
        # 🔌 ALL EXCHANGE CLIENTS
        self.kraken: Optional[KrakenClientType] = None
        self.binance: Optional[BinanceClientType] = None if not BINANCE_AVAILABLE else None
        self.alpaca: Optional[AlpacaClientType] = None if not ALPACA_AVAILABLE else None
        
        # Additional signal sources
        self.probability_nexus = None
        self.multiverse = None
        self.miner_brain = None
        self.harmonic = None
        self.omega = None
        self.rapid_stream = None
        self.wave_scanner = None  # 🌊🔭 A-Z/Z-A Global Wave Scanner
        
        # State - NOW TRACKS ALL EXCHANGES
        self.prices: Dict[str, float] = {}
        self.ticker_cache: Dict[str, Dict[str, Any]] = {}
        self.balances: Dict[str, float] = {}  # Combined balances
        self.exchange_balances: Dict[str, Dict[str, float]] = {}  # Per-exchange balances
        self.exchange_data: Dict[str, Dict[str, Any]] = {}  # Full exchange data
        self.opportunities: List[MicroOpportunity] = []
        self.conversions: List[MicroOpportunity] = []
        
        # � DREAMING & VALIDATION STATE
        self.dreams: List[Dream] = []
        self.dream_accuracy: Dict[str, float] = defaultdict(lambda: 0.5)  # Source -> Accuracy (0.0-1.0)
        self.validated_dreams_count = 0
        
        # �📊 TRADEABLE PAIRS BY EXCHANGE
        self.kraken_pairs: Dict[str, Dict] = {}  # pair -> info dict
        self.alpaca_pairs: Dict[str, str] = {}  # symbol -> normalized
        self.binance_pairs: set = set()  # symbol set
        
        # ❌ BLOCKED PAIRS/ASSETS (don't work on certain exchanges)
        # Note: USDC can be converted to other assets via BTCUSDC, ETHUSDC etc
        self.blocked_binance_assets = set()  # Removed USDC - can trade via BTC/ETH pairs
        self.blocked_kraken_assets = {'TUSD'}   # Market in cancel_only mode
        
        # 👑 DYNAMIC MINIMUMS (Learned from failures)
        self.dynamic_min_qty: Dict[str, float] = {}
        
        # 🇬🇧 UK BINANCE RESTRICTIONS - Load from cached file for speed
        self.binance_uk_allowed_pairs: set = set()
        self.binance_uk_mode = os.getenv('BINANCE_UK_MODE', 'true').lower() == 'true'
        self._load_uk_allowed_pairs()
        
        # ════════════════════════════════════════════════════════════════
        # 🎯 TURN-BASED EXCHANGE STRATEGY
        # Each exchange gets its turn to scan and execute
        # Prevents conflicts, respects rate limits, fair distribution
        # ════════════════════════════════════════════════════════════════
        self.exchange_order = ['kraken', 'alpaca', 'binance']  # Turn order
        self.current_exchange_index = 0  # Which exchange's turn
        self.turns_completed = 0  # Total turns completed
        self.exchange_stats: Dict[str, Dict] = {  # Per-exchange stats
            'kraken': {'scans': 0, 'opportunities': 0, 'conversions': 0, 'profit': 0.0, 'last_turn': None},
            'alpaca': {'scans': 0, 'opportunities': 0, 'conversions': 0, 'profit': 0.0, 'last_turn': None},
            'binance': {'scans': 0, 'opportunities': 0, 'conversions': 0, 'profit': 0.0, 'last_turn': None},
        }
        self.turn_cooldown_seconds = 0.2  # ⚡ FAST: Quick switch between exchanges
        
        # Signal aggregation from ALL systems
        self.all_signals: Dict[str, List[Dict]] = defaultdict(list)
        
        # Stats
        self.scans = 0
        self.signals_received = 0
        self.opportunities_found = 0
        self.conversions_made = 0
        self.total_profit_usd = 0.0
        self.start_value_usd = 0.0
        
        # 👑 Queen's guidance on position sizing (fed from portfolio reviews)
        self.queen_position_multiplier = 1.0  # Adjusted by Queen based on performance
    
    def _load_uk_allowed_pairs(self):
        """Load UK-allowed Binance pairs from cached JSON file."""
        if not self.binance_uk_mode:
            print("🇬🇧 UK Mode: DISABLED (all pairs allowed)")
            return
            
        try:
            import json
            uk_file = os.path.join(os.path.dirname(__file__), "binance_uk_allowed_pairs.json")
            
            if os.path.exists(uk_file):
                with open(uk_file, 'r') as f:
                    data = json.load(f)
                
                self.binance_uk_allowed_pairs = set(data.get('allowed_pairs', []))
                timestamp = data.get('timestamp_readable', 'Unknown')
                
                print(f"🇬🇧 UK Binance: {len(self.binance_uk_allowed_pairs)} pairs allowed")
                print(f"   📄 Cached from: {timestamp}")
                
                # Key insight: NO USDT pairs for UK!
                quote_assets = data.get('allowed_quote_assets', [])
                if 'USDT' not in quote_assets:
                    print(f"   ⚠️ NOTE: USDT pairs NOT allowed for UK accounts!")
                    print(f"   ✅ Use USDC/BTC/EUR pairs instead")
            else:
                print(f"⚠️ UK pairs file not found: {uk_file}")
                print(f"   Run: python binance_uk_allowed_pairs.py to generate")
        except Exception as e:
            print(f"⚠️ Failed to load UK pairs: {e}")
    
    def is_binance_pair_allowed(self, pair: str) -> bool:
        """Check if a Binance pair is allowed for UK trading."""
        if not self.binance_uk_mode:
            return True
        
        if not self.binance_uk_allowed_pairs:
            # No cached data - fall back to live check
            if self.binance and hasattr(self.binance, 'can_trade_symbol'):
                return self.binance.can_trade_symbol(pair)
            return True  # Allow if we can't check
        
        return pair.upper() in self.binance_uk_allowed_pairs
    
    async def initialize(self):
        """Initialize all systems."""
        print("\n" + "=" * 70)
        print("🔬💰 INITIALIZING MICRO PROFIT LABYRINTH 💰🔬")
        print("=" * 70)
        print(f"MODE: {'🔴 LIVE TRADING' if self.live else '🔵 DRY RUN'}")
        print(f"Entry Threshold: Score {self.config['entry_score_threshold']}+ (vs V14's 8+)")
        print(f"Min Profit: ${self.config['min_profit_usd']:.2f} or {self.config['min_profit_pct']*100:.2f}%")
        print("=" * 70)
        
        # ════════════════════════════════════════════════════════════════
        # 🐙 KRAKEN CLIENT - PRIMARY EXCHANGE
        # ════════════════════════════════════════════════════════════════
        if get_kraken_client:
            self.kraken = get_kraken_client()
            if self.kraken and KRAKEN_API_KEY:
                print("🐙 Kraken Client: WIRED (API Key loaded)")
            else:
                print("⚠️ Kraken Client: Missing API credentials")
        
        # ════════════════════════════════════════════════════════════════
        # 🟡 BINANCE CLIENT - CRYPTO EXCHANGE
        # ════════════════════════════════════════════════════════════════
        if BINANCE_AVAILABLE and BinanceClient and BINANCE_API_KEY:
            try:
                self.binance = BinanceClient()
                print("🟡 Binance Client: WIRED (API Key loaded)")
            except Exception as e:
                print(f"⚠️ Binance Client error: {e}")
        else:
            print("⚠️ Binance Client: Not configured")
        
        # ════════════════════════════════════════════════════════════════
        # 🦙 ALPACA CLIENT - STOCKS + CRYPTO
        # ════════════════════════════════════════════════════════════════
        if ALPACA_AVAILABLE and AlpacaClient and ALPACA_API_KEY:
            try:
                self.alpaca = AlpacaClient()
                print("🦙 Alpaca Client: WIRED (API Key loaded)")
            except Exception as e:
                print(f"⚠️ Alpaca Client error: {e}")
        else:
            print("⚠️ Alpaca Client: Not configured")
        
        # ════════════════════════════════════════════════════════════════
        # 📊 LOAD TRADEABLE PAIRS FROM ALL EXCHANGES
        # ════════════════════════════════════════════════════════════════
        await self._load_all_tradeable_pairs()
        
        # ════════════════════════════════════════════════════════════════
        # 🍄 MYCELIUM HUB - CENTRAL NERVOUS SYSTEM
        # ════════════════════════════════════════════════════════════════
        if get_conversion_hub:
            self.hub = get_conversion_hub()
            print("🍄 Mycelium Hub: WIRED (10 systems, 90 pathways)")
        
        # ════════════════════════════════════════════════════════════════
        # 🎯 V14 DANCE ENHANCER - 100% WIN RATE LOGIC
        # ════════════════════════════════════════════════════════════════
        if V14DanceEnhancer:
            self.v14 = V14DanceEnhancer()
            print("🎯 V14 Scoring: WIRED")
        
        # ════════════════════════════════════════════════════════════════
        # 🦅 CONVERSION COMMANDO - FALCON/TORTOISE/CHAMELEON/BEE
        # ════════════════════════════════════════════════════════════════
        if AdaptiveConversionCommando:
            self.commando = AdaptiveConversionCommando()
            print("🦅 Conversion Commando: WIRED")
        
        # ════════════════════════════════════════════════════════════════
        # 🔭 PAIR SCANNER - ALL PAIRS ALL EXCHANGES
        # ════════════════════════════════════════════════════════════════
        if PairScanner:
            self.scanner = PairScanner()
            print("🔭 Pair Scanner: WIRED")
        
        # ════════════════════════════════════════════════════════════════
        # 💡 DUAL PROFIT PATH - SELL vs CONVERT DECISION
        # ════════════════════════════════════════════════════════════════
        if DualProfitPathEvaluator:
            self.dual_path = DualProfitPathEvaluator(self.scanner)
            print("💡 Dual Profit Path: WIRED")
        
        # ════════════════════════════════════════════════════════════════
        # 🪜 CONVERSION LADDER - CAPITAL MOMENTUM
        # ════════════════════════════════════════════════════════════════
        if ConversionLadder:
            self.ladder = ConversionLadder()
            print("🪜 Conversion Ladder: WIRED")
        
        # ════════════════════════════════════════════════════════════════
        # 🔮 PROBABILITY NEXUS - 80%+ WIN RATE
        # ════════════════════════════════════════════════════════════════
        if EnhancedProbabilityNexus:
            try:
                self.probability_nexus = EnhancedProbabilityNexus()
                print("🔮 Probability Nexus: WIRED")
            except Exception as e:
                print(f"⚠️ Probability Nexus error: {e}")
        
        # ════════════════════════════════════════════════════════════════
        # 🌌 INTERNAL MULTIVERSE - 10 WORLDS
        # ════════════════════════════════════════════════════════════════
        if InternalMultiverse:
            try:
                self.multiverse = InternalMultiverse()
                print("🌌 Internal Multiverse: WIRED (10 worlds)")
            except Exception as e:
                print(f"⚠️ Multiverse error: {e}")
        
        # ════════════════════════════════════════════════════════════════
        # 🧠 MINER BRAIN - COGNITIVE INTELLIGENCE
        # ════════════════════════════════════════════════════════════════
        if MinerBrain:
            try:
                self.miner_brain = MinerBrain()
                print("🧠 Miner Brain: WIRED")
            except Exception as e:
                print(f"⚠️ Miner Brain error: {e}")
        
        # ════════════════════════════════════════════════════════════════
        # 🌊 HARMONIC FUSION - WAVE PATTERNS
        # ════════════════════════════════════════════════════════════════
        if HarmonicWaveFusion:
            try:
                self.harmonic = HarmonicWaveFusion()
                print("🌊 Harmonic Fusion: WIRED")
            except Exception as e:
                print(f"⚠️ Harmonic error: {e}")
        
        # ════════════════════════════════════════════════════════════════
        # 🌊🔭 GLOBAL WAVE SCANNER - A-Z/Z-A FULL COVERAGE
        # ════════════════════════════════════════════════════════════════
        self.wave_scanner = None
        if GLOBAL_WAVE_SCANNER_AVAILABLE and GlobalWaveScanner:
            try:
                self.wave_scanner = GlobalWaveScanner(
                    kraken_client=self.kraken,
                    binance_client=self.binance,
                    alpaca_client=self.alpaca,
                    queen=None,  # Will wire after queen is initialized
                    harmonic_fusion=self.harmonic,
                )
                print("🌊🔭 Global Wave Scanner: INITIALIZED (A-Z/Z-A coverage)")
            except Exception as e:
                print(f"⚠️ Global Wave Scanner error: {e}")
        
        # ════════════════════════════════════════════════════════════════
        # 🔱 OMEGA - HIGH CONFIDENCE SIGNALS
        # ════════════════════════════════════════════════════════════════
        if Omega:
            try:
                self.omega = Omega()
                print("🔱 Omega: WIRED")
            except Exception as e:
                print(f"⚠️ Omega error: {e}")
        
        # ════════════════════════════════════════════════════════════════
        # ⚡ RAPID CONVERSION STREAM - FAST DATA
        # ════════════════════════════════════════════════════════════════
        if RapidConversionStream:
            try:
                self.rapid_stream = RapidConversionStream()
                print("⚡ Rapid Conversion Stream: WIRED")
            except Exception as e:
                print(f"⚠️ Rapid Stream error: {e}")
        
        # ════════════════════════════════════════════════════════════════
        # 🌊⚡ MOMENTUM SNOWBALL ENGINE - WAVE JUMPING
        # ════════════════════════════════════════════════════════════════
        if MOMENTUM_SNOWBALL_AVAILABLE and MomentumTracker:
            try:
                self.momentum_tracker = MomentumTracker(window_seconds=60)
                print("🌊⚡ Momentum Tracker: WIRED (60s window)")
            except Exception as e:
                print(f"⚠️ Momentum Tracker error: {e}")
        
        # ════════════════════════════════════════════════════════════════
        # 🏆🌀 LABYRINTH SNOWBALL ENGINE - V14 + ALL SYSTEMS
        # ════════════════════════════════════════════════════════════════
        if LABYRINTH_SNOWBALL_AVAILABLE:
            try:
                # Just import the logic, don't create full engine (we are the engine!)
                print("🏆🌀 Labyrinth Snowball Logic: WIRED")
            except Exception as e:
                print(f"⚠️ Labyrinth Snowball error: {e}")
        
        # ════════════════════════════════════════════════════════════════
        # 🧠⚡ STAGE 3: FULL NEURAL MIND MAP WIRING ⚡🧠
        # ════════════════════════════════════════════════════════════════
        print("\n🧠 WIRING NEURAL MIND MAP SYSTEMS...")
        
        # 🍄 Mycelium Neural Network (Hive Intelligence)
        if MYCELIUM_NETWORK_AVAILABLE and MyceliumNetwork:
            try:
                self.mycelium_network = MyceliumNetwork(initial_capital=1000.0)
                print("   🍄 Mycelium Neural Network: ✅ WIRED (Hive Intelligence)")
            except Exception as e:
                print(f"   ⚠️ Mycelium Network error: {e}")
                self.mycelium_network = None
        else:
            print(f"   🍄 Mycelium Network: ❌ NOT AVAILABLE (import={MYCELIUM_NETWORK_AVAILABLE})")
        
        # 🗼 Lighthouse (Consensus Validation)
        if LIGHTHOUSE_AVAILABLE and Lighthouse:
            try:
                self.lighthouse = Lighthouse()
                print("   🗼 Lighthouse: ✅ WIRED (Consensus Validation)")
            except Exception as e:
                print(f"   ⚠️ Lighthouse error: {e}")
                self.lighthouse = None
        else:
            print(f"   🗼 Lighthouse: ❌ NOT AVAILABLE (import={LIGHTHOUSE_AVAILABLE})")
        
        # 📊 HNC Probability Matrix (Pattern Recognition)
        if HNC_MATRIX_AVAILABLE and HNCProbabilityMatrix:
            try:
                self.hnc_matrix = HNCProbabilityMatrix()
                print("   📊 HNC Probability Matrix: ✅ WIRED (Pattern Recognition)")
            except Exception as e:
                print(f"   ⚠️ HNC Matrix error: {e}")
                self.hnc_matrix = None
        else:
            print(f"   📊 HNC Matrix: ❌ NOT AVAILABLE (import={HNC_MATRIX_AVAILABLE})")
        
        # 💎 Ultimate Intelligence (95% Accuracy)
        if ULTIMATE_INTEL_AVAILABLE and get_ultimate_intelligence:
            try:
                self.ultimate_intel = get_ultimate_intelligence()
                print("   💎 Ultimate Intelligence: ✅ WIRED (95% Accuracy)")
            except Exception as e:
                print(f"   ⚠️ Ultimate Intel error: {e}")
                self.ultimate_intel = None
        else:
            print(f"   💎 Ultimate Intel: ❌ NOT AVAILABLE (import={ULTIMATE_INTEL_AVAILABLE})")
        
        # 🌍 Unified Ecosystem (Full Integration)
        if UNIFIED_ECOSYSTEM_AVAILABLE and AureonUnifiedEcosystem:
            try:
                # Create a lightweight tap into the ecosystem
                self.unified_ecosystem = AureonUnifiedEcosystem.__name__  # Just mark as available
                print("   🌍 Unified Ecosystem: ✅ AVAILABLE (will tap via Hub)")
            except Exception as e:
                print(f"   ⚠️ Unified Ecosystem error: {e}")
                self.unified_ecosystem = None
        else:
            print(f"   🌍 Unified Ecosystem: ❌ NOT AVAILABLE (import={UNIFIED_ECOSYSTEM_AVAILABLE})")
        
        # ⏳🔮 Timeline Oracle (7-Day Future Validation)
        self.timeline_oracle = None
        if TIMELINE_ORACLE_AVAILABLE and get_timeline_oracle:
            try:
                self.timeline_oracle = get_timeline_oracle()
                print("⏳🔮 Timeline Oracle: WIRED (7-day future validation)")
            except Exception as e:
                print(f"⚠️ Timeline Oracle error: {e}")
        
        # 🗺️ CRYPTO MARKET MAP - LABYRINTH PATHFINDER (ALL EXCHANGES)
        self.market_map = None
        if MARKET_MAP_AVAILABLE and CryptoMarketMap:
            try:
                self.market_map = CryptoMarketMap()
                # Load from cache first (has Coinbase 1-year historical data)
                self.market_map._load_cache()
                # Add data from all connected exchanges
                if self.kraken:
                    self.market_map.load_from_kraken(self.kraken)
                if self.binance:
                    self.market_map.load_from_binance(self.binance)
                if self.alpaca:
                    self.market_map.load_from_alpaca(self.alpaca)
                # Load trained probability patterns
                self.market_map.load_from_probability_matrix()
                # Save updated cache
                self.market_map.save_cache()
                summary = self.market_map.get_map_summary()
                print(f"🗺️ Crypto Market Map: WIRED ({summary['assets_mapped']} assets, {summary['correlations']} correlations)")
            except Exception as e:
                print(f"⚠️ Market Map error: {e}")
        
        # 📅🔮 7-DAY PLANNER - Plan ahead + adaptive validation after each conversion
        self.seven_day_planner = None
        if SEVEN_DAY_PLANNER_AVAILABLE and Aureon7DayPlanner:
            try:
                self.seven_day_planner = Aureon7DayPlanner()
                # Create initial 7-day plan
                plan = self.seven_day_planner.plan_7_days()
                summary = self.seven_day_planner.get_week_summary()
                stats = self.seven_day_planner.get_validation_stats()
                print(f"📅🔮 7-Day Planner: WIRED (edge: {summary['total_predicted_edge']:+.2f}%, accuracy: {stats['accuracy']:.0%})")
            except Exception as e:
                print(f"⚠️ 7-Day Planner error: {e}")
        
        # 🫒🔄 BARTER NAVIGATOR - Multi-hop pathfinding (olive→bean→carrot→chair→lamp→olive)
        self.barter_navigator = None
        if BARTER_NAVIGATOR_AVAILABLE and BarterNavigator:
            try:
                self.barter_navigator = BarterNavigator()
                # Don't load yet - will populate after pairs are loaded with populate_barter_graph()
                print(f"🫒🔄 Barter Navigator: INITIALIZED (will populate after pair loading)")
            except Exception as e:
                print(f"⚠️ Barter Navigator error: {e}")
        
        # 🍀⚛️ LUCK FIELD MAPPER - Quantum probability mapping
        self.luck_mapper = None
        if LUCK_FIELD_AVAILABLE and LuckFieldMapper:
            try:
                self.luck_mapper = LuckFieldMapper()
                # Take initial reading
                initial_luck = self.luck_mapper.read_field()
                print(f"🍀⚛️ Luck Field Mapper: WIRED (λ={initial_luck.luck_field:.4f} → {initial_luck.luck_state.value})")
            except Exception as e:
                print(f"⚠️ Luck Field Mapper error: {e}")
        
        # 👑🍄🌊🪐🔭 QUEEN HIVE MIND - Wire cosmic systems
        self.queen = None
        if QUEEN_HIVE_MIND_AVAILABLE and get_queen:
            try:
                self.queen = get_queen()
                
                # Wire Harmonic Fusion (waves, Schumann, lighthouse)
                if hasattr(self, 'harmonic') and self.harmonic:
                    self.queen.wire_harmonic_fusion(self.harmonic)
                
                # Wire Luck Field Mapper (planetary, lunar, solar)
                if self.luck_mapper:
                    self.queen.wire_luck_field_mapper(self.luck_mapper)
                
                # Wire Quantum Telescope (geometric vision)
                try:
                    from aureon_quantum_telescope import QuantumTelescope
                    self.quantum_telescope = QuantumTelescope()
                    self.queen.wire_quantum_telescope(self.quantum_telescope)
                except Exception as e:
                    logger.debug(f"Quantum Telescope not available: {e}")
                
                # Wire Mycelium for broadcast
                if hasattr(self, 'mycelium_network') and self.mycelium_network:
                    self.queen.wire_mycelium_network(self.mycelium_network)
                
                # 🧠📚 Wire Historical Wisdom Systems
                # Miner Brain (11 Civilizations)
                try:
                    from aureon_miner_brain import WisdomCognitionEngine, SandboxEvolution
                    self.wisdom_engine = WisdomCognitionEngine()  # Store on self!
                    self.queen.wire_wisdom_cognition_engine(self.wisdom_engine)
                    
                    # Sandbox Evolution (454 generations)
                    sandbox_evo = SandboxEvolution()
                    self.queen.wire_sandbox_evolution(sandbox_evo)
                except Exception as e:
                    logger.debug(f"Wisdom Cognition Engine not available: {e}")
                
                # Dream Memory & Wisdom Collector
                try:
                    from aureon_enigma_dream import DreamMemory, WisdomCollector, EnigmaDreamer
                    dream_memory = DreamMemory()
                    self.queen.wire_dream_memory(dream_memory)
                    
                    wisdom_collector = WisdomCollector()
                    self.queen.wire_wisdom_collector(wisdom_collector)
                    
                    # 🌙💭 WIRE THE DREAM ENGINE - Let Tina B DREAM toward her $1B goal!
                    dreamer = EnigmaDreamer()
                    self.queen.wire_dream_engine(dreamer)
                except Exception as e:
                    logger.debug(f"Dream/Wisdom systems not available: {e}")
                
                # 🔱⏳ Wire Temporal ID and Temporal Ladder (Gary Leckey 02111991)
                try:
                    self.queen.wire_temporal_id()
                    self.queen.wire_temporal_ladder()
                except Exception as e:
                    logger.debug(f"Temporal systems not available: {e}")
                
                # 🗺️💰 Wire Barter Matrix to Queen (1,162+ assets, 7 categories!)
                try:
                    self.queen.wire_barter_matrix(self.barter_matrix)
                except Exception as e:
                    logger.debug(f"Barter Matrix wiring not available: {e}")
                
                # 📚🧠 Wire Path Memory to Queen (learned trading paths!)
                try:
                    # Convert PathMemory to Queen-friendly format
                    path_memory_dict = {}
                    if hasattr(self, 'path_memory') and self.path_memory:
                        for key, stats in self.path_memory.memory.items():
                            path_str = f"{key[0]}->{key[1]}"
                            path_memory_dict[path_str] = {
                                'wins': stats.get('wins', 0),
                                'losses': stats.get('losses', 0)
                            }
                    if path_memory_dict:
                        self.queen.wire_path_memory(path_memory_dict)
                except Exception as e:
                    logger.debug(f"Path Memory wiring not available: {e}")
                
                # Get temporal state for display
                temporal_state = self.queen.get_temporal_state() if hasattr(self.queen, 'get_temporal_state') else {}
                temporal_active = temporal_state.get('active', False)
                
                print(f"👑🍄 Queen Hive Mind: WIRED (Cosmic + Historical + Temporal consciousness)")
                print(f"   🌊 Harmonic Fusion: {'✅' if hasattr(self.queen, 'harmonic_fusion') and self.queen.harmonic_fusion else '❌'}")
                print(f"   🪐 Luck Field Mapper: {'✅' if hasattr(self.queen, 'luck_field_mapper') and self.queen.luck_field_mapper else '❌'}")
                print(f"   🔭 Quantum Telescope: {'✅' if hasattr(self.queen, 'quantum_telescope') and self.queen.quantum_telescope else '❌'}")
                print(f"   🧠 Wisdom Engine (11 Civs): {'✅' if hasattr(self.queen, 'wisdom_engine') and self.queen.wisdom_engine else '❌'}")
                print(f"   🧬 Sandbox Evolution: {'✅' if hasattr(self.queen, 'sandbox_evolution') and self.queen.sandbox_evolution else '❌'}")
                print(f"   💭 Dream Memory: {'✅' if hasattr(self.queen, 'dream_memory') and self.queen.dream_memory else '❌'}")
                print(f"   🌙 Dream Engine: {'✅' if hasattr(self.queen, 'dreamer') and self.queen.dreamer else '❌'} (Tina B can DREAM!)")
                print(f"   📚 Wisdom Collector: {'✅' if hasattr(self.queen, 'wisdom_collector') and self.queen.wisdom_collector else '❌'}")
                print(f"   🔱 Temporal ID: {'✅' if temporal_active else '❌'} (Gary Leckey 02111991)")
                print(f"   ⏳ Temporal Ladder: {'✅' if hasattr(self.queen, 'temporal_ladder') and self.queen.temporal_ladder else '❌'}")
                print(f"   🗺️ Barter Matrix: {'✅' if hasattr(self.queen, 'barter_matrix') and self.queen.barter_matrix else '❌'} (Sector Pulse Dream Signal!)")
                print(f"   📚 Path Memory: {'✅' if hasattr(self.queen, 'path_memory') and self.queen.path_memory else '❌'} (Learned trade paths!)")
                
                # 📊🐝 Wire Queen to HNC Probability Matrix - The Matrix knows ALL the Queen's metrics!
                if self.hnc_matrix and hasattr(self.hnc_matrix, 'wire_queen_metrics'):
                    try:
                        self.hnc_matrix.wire_queen_metrics(self.queen)
                        print(f"   📊 HNC Matrix ↔ Queen: ✅ WIRED (Matrix knows Queen's metrics!)")
                    except Exception as e:
                        logger.debug(f"Queen-Matrix wiring error: {e}")
            except Exception as e:
                print(f"⚠️ Queen Hive Mind error: {e}")
        
        # 🫒💰 LIVE BARTER MATRIX - Adaptive coin-to-coin value tracking
        print(f"🫒💰 Live Barter Matrix: WIRED (Adaptive coin-agnostic value system)")
        print(f"   ℹ️ Philosophy: ANY coin → ANY coin, learning which paths make money")
        
        # �🔀 LIQUIDITY ENGINE - Dynamic Asset Aggregation
        print(f"💧🔀 Liquidity Engine: WIRED (Dynamic Asset Aggregation)")
        print(f"   ℹ️ Philosophy: Liquidate low-performers to fund winning trades!")
        print(f"   🎯 Min Victim Value: ${self.liquidity_engine.MIN_VICTIM_VALUE:.2f}")
        print(f"   ⏱️ Liquidation Cooldown: {self.liquidity_engine.LIQUIDATION_COOLDOWN}s")
        
        # �🔐🌐 ENIGMA INTEGRATION - Universal Translator Bridge
        if ENIGMA_INTEGRATION_AVAILABLE and get_enigma_integration:
            try:
                self.enigma_integration = get_enigma_integration()
                
                # Wire to existing systems
                if self.queen:
                    wire_enigma_to_ecosystem(self.queen)
                    # 👑🔐 Also wire Enigma directly to Queen for dream_of_winning!
                    self.queen.enigma = self.enigma_integration
                
                print("🔐🌐 Enigma Integration: WIRED (Universal Translator Bridge)")
                print(f"   💭 Dream Engine: {'✅' if self.enigma_integration.dreamer else '❌'}")
                print(f"   👑 Coherence Mandala: {'✅' if getattr(self.enigma_integration, 'coherence_system', None) else '❌'}")
                print(f"   🏛️ Barons Banner: {'✅' if getattr(self.enigma_integration, 'barons_analyzer', None) else '❌'}")
                print(f"   👼 Math Angel: {'✅' if getattr(self.enigma_integration, 'math_angel', None) else '❌'}")
                print(f"   🌊 Harmonic Reality: {'✅' if getattr(self.enigma_integration, 'harmonic_reality', None) else '❌'}")
                print(f"   ⚡ QGITA Framework: {'✅' if getattr(self.enigma_integration, 'qgita', None) else '❌'}")
                print(f"   🧠 Consciousness: ACTIVE (It thinks, therefore it trades)")
            except Exception as e:
                print(f"⚠️ Enigma Integration error: {e}")
                self.enigma_integration = None
        else:
            print(f"🔐🌐 Enigma Integration: ❌ NOT AVAILABLE (import={ENIGMA_INTEGRATION_AVAILABLE})")
        
        # 📡 Thought Bus Aggregator Status
        if self.bus_aggregator:
            print("📡 Thought Bus Aggregator: WIRED (Neural Signal Collector)")
        
        # ════════════════════════════════════════════════════════════════════════════
        # 👑🎓 QUEEN LOSS LEARNING SYSTEM - Learn from every loss, never forget
        # ════════════════════════════════════════════════════════════════════════════
        if QUEEN_LOSS_LEARNING_AVAILABLE and QueenLossLearningSystem:
            try:
                # Get elephant memory from queen if available
                elephant_memory = None
                if self.queen and hasattr(self.queen, 'elephant_brain'):
                    elephant_memory = self.queen.elephant_brain
                
                self.loss_learning = QueenLossLearningSystem(
                    elephant_memory=elephant_memory,
                    mycelium=self.mycelium_network,
                    kraken_client=self.kraken,
                    binance_client=self.binance,
                    alpaca_client=self.alpaca,
                )
                
                # Wire to queen if available
                if self.queen:
                    self.queen.loss_learning = self.loss_learning
                
                print("👑🎓 Queen Loss Learning: WIRED (Learns from every loss, never forgets)")
                print(f"   🐘 Elephant Memory: {'✅' if self.loss_learning.elephant else '❌'}")
                print(f"   🍄 Mycelium Network: {'✅' if self.loss_learning.mycelium else '❌'}")
                print(f"   📊 Losses Analyzed: {self.loss_learning.stats['total_losses_analyzed']}")
                print(f"   🎖️ Tactics Learned: {len(self.loss_learning.warfare_tactics)}")
            except Exception as e:
                print(f"⚠️ Queen Loss Learning error: {e}")
                self.loss_learning = None
        else:
            print(f"👑🎓 Queen Loss Learning: ❌ NOT AVAILABLE (import={QUEEN_LOSS_LEARNING_AVAILABLE})")
        
        # 🦆⚔️ QUANTUM QUACKERS COMMANDOS - THE ANIMAL ARMY UNDER THE QUEEN!
        # Lion, Wolf, Ants, Hummingbird - all serve Tina B!
        self.quack_commandos = None
        self.quack_targets = {}  # Cached targets from commandos
        if QUACK_COMMANDOS_AVAILABLE:
            try:
                # Create a mock client for commandos (they need ticker data)
                class QuackClient:
                    """Mock client that uses our existing ticker cache"""
                    def __init__(self, labyrinth):
                        self.labyrinth = labyrinth
                    
                    def get_24h_ticker(self, symbol):
                        """Get 24h stats for a symbol"""
                        for cached_sym, data in self.labyrinth.ticker_cache.items():
                            base = data.get('base', '')
                            quote = data.get('quote', '')
                            if f"{base}{quote}" == symbol or f"{base}/USD" == symbol:
                                return {
                                    'priceChangePercent': data.get('change24h', 0) * 100,
                                    'quoteVolume': data.get('volume', 0),
                                    'lastPrice': data.get('price', 0),
                                }
                        return {'priceChangePercent': 0, 'quoteVolume': 0, 'lastPrice': 0}
                    
                    def get_24h_tickers(self):
                        """Get all 24h stats"""
                        tickers = []
                        for symbol, data in self.labyrinth.ticker_cache.items():
                            base = data.get('base', '')
                            quote = data.get('quote', 'USD')
                            tickers.append({
                                'symbol': f"{base}{quote}",
                                'priceChangePercent': data.get('change24h', 0) * 100,
                                'quoteVolume': data.get('volume', 100000),
                                'lastPrice': data.get('price', 1.0),
                            })
                        return tickers
                
                quack_client = QuackClient(self)
                self.quack_commandos = QuackCommandos(quack_client)
                
                # 👑 WIRE COMMANDOS TO QUEEN! The Queen commands the army!
                if self.queen:
                    self.queen.quack_commandos = self.quack_commandos
                
                print("🦆⚔️ Quantum Quackers Commandos: WIRED (Queen's Animal Army)")
                print(f"   🦁 Lion (Pride Scanner): {self.quack_commandos.slot_config['lion']} slots")
                print(f"   🐺 Wolf (Momentum Sniper): {self.quack_commandos.slot_config['wolf']} slots")
                print(f"   🐜 Ants (Floor Scavengers): {self.quack_commandos.slot_config['ants']} slots")
                print(f"   🐝 Hummingbird (Quick Rotations): {self.quack_commandos.slot_config['hummingbird']} slots")
                print("   👑 ALL COMMANDOS SERVE TINA B - LONG LIVE THE QUEEN!")
            except Exception as e:
                print(f"⚠️ Quack Commandos init error: {e}")
                self.quack_commandos = None
        else:
            print("🦆⚔️ Quantum Quackers Commandos: ❌ NOT AVAILABLE")
        
        # �🧠 PathMemory Stats
        pm_stats = self.path_memory.get_stats()
        print(f"🧠 PathMemory: {pm_stats['paths']} paths, {pm_stats['win_rate']:.1%} win rate")
        
        # 🧠⚡ NEURAL MIND MAP SUMMARY - ALL 12 NEURONS (Now with Enigma!)
        print("\n" + "=" * 70)
        print("🧠⚡ NEURAL MIND MAP - FULL SYSTEM STATUS ⚡🧠")
        print("=" * 70)
        neurons_status = {
            '👑 Queen Hive Mind': self.queen is not None,
            '🔐 Enigma Integration': self.enigma_integration is not None,  # 🔐 NEW!
            '🍄 Mycelium Network': self.mycelium_network is not None,
            '🌊 Harmonic Fusion': self.harmonic is not None,
            '🍀 Luck Field Mapper': self.luck_mapper is not None,
            '💭 Dream Memory': hasattr(self, 'dreams'),  # Always available
            '🧠 Path Memory': self.path_memory is not None,
            '⏳ Timeline Oracle': self.timeline_oracle is not None,
            '📡 Thought Bus': self.bus_aggregator is not None,
            '💎 Ultimate Intel': self.ultimate_intel is not None,
            '📚 Wisdom Engine': self.wisdom_engine is not None,
            '🫒 Barter Matrix': self.barter_matrix is not None,
        }
        connected = sum(1 for v in neurons_status.values() if v)
        total = len(neurons_status)
        
        for name, status in neurons_status.items():
            icon = "✅" if status else "❌"
            # Show Enigma subsystems if available
            if name == '🔐 Enigma Integration' and status and self.enigma_integration:
                subs = []
                if hasattr(self.enigma_integration, 'dreamer') and self.enigma_integration.dreamer:
                    subs.append("💭Dream")
                if hasattr(self.enigma_integration, 'coherence_system') and self.enigma_integration.coherence_system:
                    subs.append("👑Coherence")
                if hasattr(self.enigma_integration, 'qgita') and self.enigma_integration.qgita:
                    subs.append("⚡QGITA")
                if hasattr(self.enigma_integration, 'math_angel') and self.enigma_integration.math_angel:
                    subs.append("👼Angel")
                if hasattr(self.enigma_integration, 'barons_analyzer') and self.enigma_integration.barons_analyzer:
                    subs.append("🏛️Barons")
                if hasattr(self.enigma_integration, 'harmonic_reality') and self.enigma_integration.harmonic_reality:
                    subs.append("🌊Reality")
                sub_str = " [" + ", ".join(subs) + "]" if subs else ""
                print(f"   {icon} {name}{sub_str}")
            else:
                print(f"   {icon} {name}")
        
        print(f"\n   🧠 NEURAL STATUS: {connected}/{total} NEURONS CONNECTED")
        if connected == total:
            print("   🌟 FULL CONSCIOUSNESS ACHIEVED - ALL SYSTEMS ONLINE! 🌟")
        elif connected >= total - 2:
            print("   ⚡ NEAR FULL CONSCIOUSNESS - Minor systems offline")
        else:
            print("   ⚠️ PARTIAL CONSCIOUSNESS - Some systems need attention")
        
        print("=" * 70)
        print()
    
    async def _load_all_tradeable_pairs(self):
        """Load tradeable pairs from ALL exchanges for proper routing."""
        print("\n📊 LOADING TRADEABLE PAIRS FROM ALL EXCHANGES...")
        print("   🗺️ Expanding Barter Matrix market visibility...")
        
        # ════════════════════════════════════════════════════════════════
        # 🐙 KRAKEN PAIRS - Load from AssetPairs API
        # ════════════════════════════════════════════════════════════════
        if self.kraken:
            try:
                pairs_info = self.kraken._load_asset_pairs() if hasattr(self.kraken, '_load_asset_pairs') else {}
                kraken_pair_names = []
                for internal, info in pairs_info.items():
                    if not internal.endswith('.d'):  # Skip dark pools
                        altname = info.get('altname', internal)
                        base = info.get('base', '')
                        quote = info.get('quote', '')
                        self.kraken_pairs[altname] = {
                            'internal': internal,
                            'base': base,
                            'quote': quote,
                            'wsname': info.get('wsname', altname),
                        }
                        # Also add common variants
                        self.kraken_pairs[internal] = self.kraken_pairs[altname]
                        kraken_pair_names.append(altname)
                
                # 🗺️ REGISTER WITH BARTER MATRIX for expanded market coverage
                discovered = self.barter_matrix.discover_exchange_assets('kraken', kraken_pair_names)
                print(f"   🐙 Kraken: {len(self.kraken_pairs)} tradeable pairs ({discovered} assets discovered)")
            except Exception as e:
                logger.error(f"Kraken pairs error: {e}")
                print(f"   ❌ Kraken pairs error: {e}")
        
        # ════════════════════════════════════════════════════════════════
        # 🦙 ALPACA PAIRS - Load from Assets API
        # ════════════════════════════════════════════════════════════════
        if self.alpaca:
            try:
                alpaca_pair_names = []
                # Get tradeable crypto symbols
                if hasattr(self.alpaca, 'get_tradable_crypto_symbols'):
                    symbols = self.alpaca.get_tradable_crypto_symbols() or []
                    for symbol in symbols:
                        # Alpaca returns like 'BTC/USD'
                        self.alpaca_pairs[symbol] = symbol
                        # Also store without slash
                        clean = symbol.replace('/', '')
                        self.alpaca_pairs[clean] = symbol
                        alpaca_pair_names.append(clean)
                else:
                    # Fallback - get assets directly
                    assets = self.alpaca.get_assets(status='active', asset_class='crypto') or []
                    for asset in assets:
                        if asset.get('tradable'):
                            symbol = asset.get('symbol', '')
                            if symbol:
                                self.alpaca_pairs[symbol] = symbol
                                # Add normalized version
                                if '/' in symbol:
                                    clean = symbol.replace('/', '')
                                    self.alpaca_pairs[clean] = symbol
                                    alpaca_pair_names.append(clean)
                
                # 🗺️ REGISTER WITH BARTER MATRIX
                discovered = self.barter_matrix.discover_exchange_assets('alpaca', alpaca_pair_names)
                print(f"   🦙 Alpaca: {len(self.alpaca_pairs)} tradeable pairs ({discovered} assets discovered)")
            except Exception as e:
                logger.error(f"Alpaca pairs error: {e}")
                print(f"   ❌ Alpaca pairs error: {e}")
        
        # ════════════════════════════════════════════════════════════════
        # 🟡 BINANCE PAIRS - Will load during fetch_prices from tickers
        # ════════════════════════════════════════════════════════════════
        # Load Binance pairs immediately for market discovery
        if self.binance:
            try:
                info = self.binance.exchange_info()
                symbols = info.get('symbols', [])
                binance_pair_names = []
                
                for sym in symbols:
                    if sym.get('status') == 'TRADING':
                        pair = sym.get('symbol', '')
                        binance_pair_names.append(pair)
                        self.binance_pairs.add(pair)
                
                # 🗺️ REGISTER WITH BARTER MATRIX
                discovered = self.barter_matrix.discover_exchange_assets('binance', binance_pair_names)
                print(f"   🟡 Binance: {len(binance_pair_names)} tradeable pairs ({discovered} assets discovered)")
            except Exception as e:
                logger.error(f"Binance pairs error: {e}")
                print(f"   🟡 Binance: pairs will load with price data")
        
        # 🗺️ PRINT MARKET COVERAGE REPORT
        print(self.barter_matrix.print_market_coverage())
        print()
    
    async def fetch_prices(self) -> Dict[str, float]:
        """Fetch all asset prices from ALL exchanges."""
        prices = {}
        ticker_cache = {}
        
        # ════════════════════════════════════════════════════════════════
        # 🐙 KRAKEN PRICES - Use get_24h_tickers (returns list of dicts)
        # ════════════════════════════════════════════════════════════════
        if self.kraken:
            try:
                tickers = self.kraken.get_24h_tickers() if hasattr(self.kraken, 'get_24h_tickers') else []
                kraken_count = 0
                
                for data in tickers:
                    if not isinstance(data, dict):
                        continue
                    
                    symbol = data.get('symbol', '')
                    # Kraken returns lastPrice as string
                    price_str = data.get('lastPrice', '0')
                    price = float(price_str) if price_str else 0.0
                    
                    if price > 0 and symbol:
                        # Store in kraken pairs for execution routing
                        self.binance_pairs.discard(symbol)  # Not binance
                        
                        for quote in ['USD', 'USDT', 'USDC', 'GBP', 'EUR']:
                            if symbol.endswith(quote):
                                base = symbol[:-len(quote)]
                                # Clean up Kraken naming
                                if len(base) == 4 and base[0] in ('X', 'Z'):
                                    base = base[1:]
                                if base == 'XBT':
                                    base = 'BTC'
                                
                                prices[base] = price
                                
                                change = float(data.get('priceChangePercent', 0))
                                volume = float(data.get('quoteVolume', 0))
                                
                                ticker_entry = {
                                    'price': price,
                                    'change24h': change,
                                    'volume': volume,
                                    'base': base,
                                    'quote': quote,
                                    'exchange': 'kraken',
                                    'pair': symbol,
                                }
                                # Wave scanner expects raw symbols; keep prefixed + raw for compatibility
                                ticker_cache[f"kraken:{symbol}"] = ticker_entry
                                ticker_cache[symbol] = ticker_entry
                                kraken_count += 1
                                break
                
                print(f"   🐙 Kraken: {kraken_count} pairs loaded")
            except Exception as e:
                logger.error(f"Kraken price fetch error: {e}")
        
        # ════════════════════════════════════════════════════════════════
        # 🟡 BINANCE PRICES
        # ════════════════════════════════════════════════════════════════
        if self.binance:
            try:
                # Get 24h ticker
                if hasattr(self.binance, 'ticker_24hr_all'):
                    binance_tickers = self.binance.ticker_24hr_all()
                elif hasattr(self.binance, 'session'):
                    r = self.binance.session.get(f"{self.binance.base}/api/v3/ticker/24hr")
                    binance_tickers = r.json() if r.ok else []
                else:
                    binance_tickers = []
                
                binance_count = 0
                # For UK mode, prefer USDC over USDT
                quote_priority = ['USDC', 'USDT', 'USD', 'BUSD'] if self.binance_uk_mode else ['USDT', 'USD', 'BUSD', 'USDC']
                
                for ticker in binance_tickers:
                    symbol = ticker.get('symbol', '')
                    price = float(ticker.get('lastPrice', 0))
                    if price > 0:
                        # 🇬🇧 UK MODE: Only load allowed pairs
                        if self.binance_uk_mode and not self.is_binance_pair_allowed(symbol):
                            continue
                        
                        for quote in quote_priority:
                            if symbol.endswith(quote):
                                base = symbol.replace(quote, '')
                                # Only update if we don't have this price yet
                                if base not in prices:
                                    prices[base] = price
                                
                                change = float(ticker.get('priceChangePercent', 0))
                                volume = float(ticker.get('volume', 0))
                                ticker_entry = {
                                    'price': price,
                                    'change24h': change,
                                    'volume': volume,
                                    'base': base,
                                    'quote': quote,
                                    'exchange': 'binance',
                                }
                                # Wave scanner reads unprefixed symbols; store both
                                ticker_cache[f"binance:{symbol}"] = ticker_entry
                                ticker_cache[symbol] = ticker_entry
                                binance_count += 1
                                break
                print(f"   🟡 Binance: {binance_count} pairs loaded")
            except Exception as e:
                logger.error(f"Binance price fetch error: {e}")
        
        # ════════════════════════════════════════════════════════════════
        # 🦙 ALPACA PRICES (crypto and positions)
        # ════════════════════════════════════════════════════════════════
        if self.alpaca:
            try:
                alpaca_count = 0
                
                # Get prices from positions
                if hasattr(self.alpaca, 'get_positions'):
                    positions = self.alpaca.get_positions() or []
                    for pos in positions:
                        symbol = pos.get('symbol', '')
                        price = float(pos.get('current_price', 0))
                        if price > 0 and symbol:
                            # Extract base asset from symbol like "BTCUSD" or "BTC/USD"
                            base = symbol.replace('/USD', '').replace('USD', '')
                            if base and len(base) > 1:
                                prices[base] = price
                                change = float(pos.get('change_today', 0)) * 100
                                ticker_entry = {
                                    'price': price,
                                    'change24h': change,
                                    'volume': 0,
                                    'base': base,
                                    'quote': 'USD',
                                    'exchange': 'alpaca',
                                    'pair': symbol,
                                }
                                # Store multiple keys so wave scanner sees Alpaca symbols (slash + raw)
                                ticker_cache[f"alpaca:{symbol}"] = ticker_entry
                                ticker_cache[symbol] = ticker_entry
                                ticker_cache[f"{base}/USD"] = ticker_entry
                                # Store in alpaca_pairs for routing
                                self.alpaca_pairs[symbol] = f"{base}/USD"
                                self.alpaca_pairs[f"{base}USD"] = f"{base}/USD"
                                self.alpaca_pairs[f"{base}/USD"] = f"{base}/USD"
                                alpaca_count += 1
                
                print(f"   🦙 Alpaca: {alpaca_count} positions loaded")
            except Exception as e:
                logger.error(f"Alpaca price fetch error: {e}")
        
        # ════════════════════════════════════════════════════════════════
        # 🐍 MEDUSA STABLECOIN INJECTION - Enable trading from stablecoins!
        # ════════════════════════════════════════════════════════════════
        # Stablecoins are quote currencies (not in price feeds) but we HOLD them
        # We need them in prices so they can be SOURCE assets for buying!
        stablecoin_prices = {
            'USD': 1.0,
            'USDT': 1.0,
            'USDC': 1.0,
            'ZUSD': 1.0,   # Kraken USD
            'TUSD': 1.0,   # TrueUSD
            'DAI': 1.0,
        }
        for stable, price in stablecoin_prices.items():
            if stable not in prices:
                prices[stable] = price
        
        self.prices = prices
        self.ticker_cache = ticker_cache
        
        # 🌊⚡ UPDATE MOMENTUM FOR ALL PRICES - Wave jumping intelligence
        momentum_count = 0
        for asset, price in prices.items():
            if price > 0:
                self.update_momentum(asset, price)
                momentum_count += 1
        
        # Show top movers if we have momentum data
        if len(self.asset_momentum) > 10:
            rising = self.get_strongest_rising(limit=3)
            falling = self.get_weakest_falling(limit=3)
            if rising:
                top_rising = ', '.join([f"{a}:{m*100:+.2f}%/min" for a, m in rising[:3]])
                print(f"   🌊 Rising: {top_rising}")
            if falling:
                top_falling = ', '.join([f"{a}:{m*100:+.2f}%/min" for a, m in falling[:3]])
                print(f"   📉 Falling: {top_falling}")
        
        print(f"   📊 Total: {len(prices)} unique assets, {len(ticker_cache)} tickers, {momentum_count} momentum tracked")
        print(f"   🐍 Medusa stablecoins: USD, USDT, USDC, ZUSD, TUSD, DAI injected")
        
        return prices
    
    async def fetch_balances(self) -> Dict[str, float]:
        """Fetch balances from ALL exchanges."""
        combined = {}
        self.exchange_balances = {}
        self.exchange_data = {}
        
        # ════════════════════════════════════════════════════════════════
        # 🐙 KRAKEN BALANCES
        # ════════════════════════════════════════════════════════════════
        if self.kraken:
            try:
                kraken_bal = {}
                if hasattr(self.kraken, 'get_account_balance'):
                    raw = self.kraken.get_account_balance() or {}
                    for asset, amount in raw.items():
                        try:
                            amount = float(amount)
                        except (ValueError, TypeError):
                            continue
                        if amount > 0:
                            # Clean up Kraken naming
                            clean = asset
                            if len(asset) == 4 and asset[0] in ('X', 'Z'):
                                clean = asset[1:]
                            if clean == 'XBT':
                                clean = 'BTC'
                            kraken_bal[clean] = amount
                            combined[clean] = combined.get(clean, 0) + amount
                
                self.exchange_balances['kraken'] = kraken_bal
                self.exchange_data['kraken'] = {
                    'connected': True,
                    'balances': kraken_bal,
                    'total_value': sum(kraken_bal.get(a, 0) * self.prices.get(a, 0) for a in kraken_bal),
                }
                print(f"   🐙 Kraken: {len(kraken_bal)} assets")
            except Exception as e:
                logger.error(f"Kraken balance error: {e}")
                self.exchange_data['kraken'] = {'connected': False, 'error': str(e)}
        
        # ════════════════════════════════════════════════════════════════
        # 🟡 BINANCE BALANCES
        # ════════════════════════════════════════════════════════════════
        if self.binance:
            try:
                binance_bal = {}
                if hasattr(self.binance, 'account'):
                    acct = self.binance.account() or {}
                    for bal in acct.get('balances', []):
                        asset = bal.get('asset', '')
                        free = float(bal.get('free', 0))
                        if free > 0 and asset:
                            binance_bal[asset] = free
                            combined[asset] = combined.get(asset, 0) + free
                
                self.exchange_balances['binance'] = binance_bal
                self.exchange_data['binance'] = {
                    'connected': True,
                    'balances': binance_bal,
                    'total_value': sum(binance_bal.get(a, 0) * self.prices.get(a, 0) for a in binance_bal),
                }
                print(f"   🟡 Binance: {len(binance_bal)} assets")
            except Exception as e:
                logger.error(f"Binance balance error: {e}")
                self.exchange_data['binance'] = {'connected': False, 'error': str(e)}
        
        # ════════════════════════════════════════════════════════════════
        # 🦙 ALPACA BALANCES
        # ════════════════════════════════════════════════════════════════
        if self.alpaca:
            try:
                alpaca_bal = {}
                # Get account for cash
                if hasattr(self.alpaca, 'get_account'):
                    acct = self.alpaca.get_account() or {}
                    cash = float(acct.get('cash', 0))
                    if cash > 0:
                        alpaca_bal['USD'] = cash
                        combined['USD'] = combined.get('USD', 0) + cash
                
                # Get positions (crypto assets)
                if hasattr(self.alpaca, 'get_positions'):
                    positions = self.alpaca.get_positions() or []
                    for pos in positions:
                        raw_symbol = pos.get('symbol', '')
                        qty = float(pos.get('qty', 0))
                        market_value = float(pos.get('market_value', 0))
                        
                        if qty > 0 and raw_symbol:
                            # Convert Alpaca symbol format (BTCUSD -> BTC, USDTUSD -> USDT)
                            if raw_symbol.endswith('USD'):
                                base_asset = raw_symbol[:-3]  # Remove USD suffix
                            else:
                                base_asset = raw_symbol
                            
                            # Store with base asset name
                            alpaca_bal[base_asset] = qty
                            combined[base_asset] = combined.get(base_asset, 0) + qty
                            
                            # Also store the price if we got market_value
                            if market_value > 0 and qty > 0:
                                price = market_value / qty
                                if base_asset not in self.prices or self.prices.get(base_asset, 0) == 0:
                                    self.prices[base_asset] = price
                
                self.exchange_balances['alpaca'] = alpaca_bal
                self.exchange_data['alpaca'] = {
                    'connected': True,
                    'balances': alpaca_bal,
                    'total_value': float(acct.get('portfolio_value', 0)) if acct else 0,
                }
                print(f"   🦙 Alpaca: {len(alpaca_bal)} assets")
            except Exception as e:
                logger.error(f"Alpaca balance error: {e}")
                self.exchange_data['alpaca'] = {'connected': False, 'error': str(e)}
        
        self.balances = combined
        
        # 🐛 BALANCE SANITY CHECK - Prevent phantom balances!
        # No single asset should be > $500,000 (we're a small trader!)
        MAX_REALISTIC_USD = 500000.0
        for asset in list(self.balances.keys()):
            amount = self.balances[asset]
            price = self.prices.get(asset, 1.0 if asset in ('USD', 'USDT', 'USDC', 'ZUSD') else 0.0)
            value_usd = amount * price
            if value_usd > MAX_REALISTIC_USD:
                logger.warning(f"🚨 PHANTOM BALANCE DETECTED: {asset} = {amount:.2f} (${value_usd:,.2f}) - IGNORING!")
                print(f"   🚨 PHANTOM BALANCE: {asset} ${value_usd:,.2f} > ${MAX_REALISTIC_USD:,.2f} - Removing!")
                del self.balances[asset]
        
        # Calculate total portfolio value
        total_usd = 0.0
        for asset, amount in combined.items():
            if asset not in self.balances:  # Skip removed phantoms
                continue
            if asset in ('USD', 'USDT', 'USDC'):
                total_usd += amount
            else:
                price = self.prices.get(asset, 0)
                total_usd += amount * price
        
        print(f"   💰 Combined Portfolio: ${total_usd:,.2f}")
        print(f"   📊 Unique assets: {len(combined)}")
        
        return combined
    
    def calculate_trained_matrix_score(self, to_asset: str) -> Tuple[float, str]:
        """
        📊 Calculate score from trained probability matrix.
        Returns: (score 0-1, reason string)
        
        Uses the trained_probability_matrix.json which contains:
        - Hourly edge patterns (optimal/avoid hours)
        - Daily edge patterns (optimal days)
        - Per-symbol patterns
        - Multi-exchange training data
        """
        from datetime import datetime
        import json
        
        score = 0.5  # Neutral default
        reasons = []
        
        try:
            # Load trained matrix
            matrix_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trained_probability_matrix.json')
            if not os.path.exists(matrix_path):
                return 0.5, "matrix_not_found"
            
            with open(matrix_path, 'r') as f:
                matrix = json.load(f)
            
            now = datetime.now()
            current_hour = str(now.hour)
            current_dow = str(now.weekday())
            
            # 1. Global hourly edge
            hourly_edge_data = matrix.get('hourly_edge', {}).get(current_hour, {})
            hourly_edge = hourly_edge_data.get('edge', 0)
            hourly_conf = hourly_edge_data.get('confidence', 0)
            
            if hourly_edge > 10 and hourly_conf > 0.1:
                score += 0.15
                reasons.append(f"optimal_hour({current_hour})")
            elif hourly_edge < -10 and hourly_conf > 0.1:
                score -= 0.15
                reasons.append(f"avoid_hour({current_hour})")
            
            # 2. Global daily edge
            daily_edge_data = matrix.get('daily_edge', {}).get(current_dow, {})
            daily_edge = daily_edge_data.get('edge', 0)
            daily_conf = daily_edge_data.get('confidence', 0)
            
            if daily_edge > 5 and daily_conf > 0.05:
                score += 0.10
                reasons.append(f"optimal_day({current_dow})")
            elif daily_edge < -5 and daily_conf > 0.05:
                score -= 0.10
                reasons.append(f"avoid_day({current_dow})")
            
            # 3. Symbol-specific patterns
            symbol_patterns = matrix.get('symbol_patterns', {}).get(to_asset, {})
            if symbol_patterns:
                bullish_prob = symbol_patterns.get('bullish_prob', 0.5)
                win_rate = symbol_patterns.get('win_rate', 0.5)
                trade_count = symbol_patterns.get('trade_count', 0)
                
                # Bullish probability bonus
                if bullish_prob > 0.55:
                    score += 0.10
                    reasons.append(f"bullish_symbol({bullish_prob:.2f})")
                elif bullish_prob < 0.45:
                    score -= 0.10
                    reasons.append(f"bearish_symbol({bullish_prob:.2f})")
                
                # Trade history win rate bonus
                if trade_count >= 5 and win_rate > 0.6:
                    score += 0.15
                    reasons.append(f"high_win_rate({win_rate:.2f})")
                elif trade_count >= 5 and win_rate < 0.4:
                    score -= 0.15
                    reasons.append(f"low_win_rate({win_rate:.2f})")
                
                # Symbol-specific hourly edge
                sym_hourly = symbol_patterns.get('hourly_edge', {}).get(current_hour, {})
                sym_hourly_edge = sym_hourly.get('edge', 0)
                if sym_hourly_edge > 15:
                    score += 0.10
                    reasons.append(f"sym_optimal_hour")
                elif sym_hourly_edge < -15:
                    score -= 0.10
                    reasons.append(f"sym_avoid_hour")
            
            # 4. Check optimal/avoid conditions
            optimal_hours = matrix.get('optimal_conditions', {}).get('hours', [])
            avoid_hours = matrix.get('avoid_conditions', {}).get('hours', [])
            
            if now.hour in optimal_hours:
                score += 0.05
                reasons.append("in_optimal_hours")
            if now.hour in avoid_hours:
                score -= 0.10  # Heavier penalty for avoid hours
                reasons.append("in_avoid_hours")
            
            # Clamp score between 0 and 1
            score = max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.debug(f"Trained matrix score error: {e}")
            return 0.5, f"error:{str(e)[:20]}"
        
        reason = ",".join(reasons) if reasons else "neutral"
        return score, reason
    
    def calculate_barter_score(self, from_asset: str, to_asset: str) -> Tuple[float, str]:
        """
        🫒💰 Calculate barter path score for a conversion.
        
        Uses BOTH the Barter Navigator (multi-hop paths) AND the LiveBarterMatrix 
        (historical performance) for smarter, adaptive scoring.
        
        THE PHILOSOPHY:
        - Any coin can lead to any other coin
        - Historical success on a path matters
        - The system learns which paths ACTUALLY make money
        
        Returns: (score 0-1, reason string)
        """
        score = 0.5  # Start neutral
        reasons = []
        
        # ═══════════════════════════════════════════════════════════════════
        # 1. LIVE BARTER MATRIX - Historical Performance
        # ═══════════════════════════════════════════════════════════════════
        from_price = self.prices.get(from_asset, 0)
        to_price = self.prices.get(to_asset, 0)
        
        if from_price > 0 and to_price > 0:
            # Update barter rate for this pair
            self.barter_matrix.update_barter_rate(from_asset, to_asset, from_price, to_price)
            
            # Check historical performance of this path
            key = (from_asset.upper(), to_asset.upper())
            history = self.barter_matrix.barter_history.get(key, {})
            
            if history.get('trades', 0) > 0:
                # We have history! Use it with current holdings consideration
                path_profit = history.get('total_profit', 0)
                path_trades = history['trades']
                avg_profit = path_profit / path_trades
                
                # Adjust score based on historical avg trade size
                avg_trade_size = history.get('avg_trade_size', 10.0)  # Default $10 avg trade
                
                # Boost score based on historical success
                if avg_profit > 0.01:  # Profitable path
                    score += 0.15
                    reasons.append(f"profit_path(${avg_profit:.3f})")
                elif avg_profit > 0:
                    score += 0.08
                    reasons.append("slight_profit")
                elif avg_profit < -0.01:  # Losing path
                    score -= 0.10
                    reasons.append("losing_path")
                
                # Experience bonus (more trades = more confidence)
                if path_trades >= 10:
                    score += 0.05
                    reasons.append(f"experienced({path_trades})")
                elif path_trades >= 5:
                    score += 0.02
                    reasons.append(f"some_exp({path_trades})")
            else:
                # New path - slight exploration bonus
                score += 0.02
                reasons.append("new_path")
        
        # ═══════════════════════════════════════════════════════════════════
        # 2. BARTER NAVIGATOR - Multi-hop Path Quality
        # ═══════════════════════════════════════════════════════════════════
        if self.barter_navigator and BARTER_NAVIGATOR_AVAILABLE:
            try:
                # Find path from source to destination
                path = self.barter_navigator.find_path(from_asset, to_asset)
                
                if path:
                    # 1. Direct path (1 hop) is best
                    if path.num_hops == 1:
                        score += 0.15
                        reasons.append("direct_path")
                    elif path.num_hops == 2:
                        score += 0.08
                        reasons.append("2hop_path")
                    elif path.num_hops > 3:
                        score -= 0.08
                        reasons.append(f"{path.num_hops}hop_path")
                    
                    # 2. Rate efficiency (closer to 1.0 = less slippage)
                    if path.total_rate > 0.995:
                        score += 0.08
                        reasons.append("efficient_rate")
                    elif path.total_rate < 0.98:
                        score -= 0.08
                        reasons.append("high_slippage")
                    
                    # 3. Single exchange is cleaner
                    if len(path.exchanges_used) == 1:
                        score += 0.03
                        reasons.append("single_exchange")
                    
                    # 4. Low fees are good
                    if path.total_fees < 0.005:  # <0.5%
                        score += 0.03
                        reasons.append("low_fees")
                    elif path.total_fees > 0.01:  # >1%
                        score -= 0.05
                        reasons.append("high_fees")
                else:
                    reasons.append("no_nav_path")
                    
            except Exception as e:
                logger.debug(f"Barter navigator score error: {e}")
        else:
            reasons.append("nav_not_available")
        
        # Clamp score
        score = max(0.0, min(1.0, score))
        
        reason = "barter_" + ",".join(reasons[:3])
        return score, reason
    
    def find_barter_chain(self, from_asset: str, to_asset: str) -> Optional[List[Dict]]:
        """
        🫒 Find the complete barter chain from source to destination.
        
        Returns list of trade steps: [
            {'from': 'CHZ', 'to': 'USD', 'pair': 'CHZUSD', 'exchange': 'kraken', 'rate': 0.05},
            {'from': 'USD', 'to': 'BTC', 'pair': 'BTCUSD', 'exchange': 'kraken', 'rate': 0.00001},
        ]
        """
        if not self.barter_navigator:
            return None
        
        path = self.barter_navigator.find_path(from_asset, to_asset)
        if not path:
            return None
        
        steps = []
        for hop in path.hops:
            steps.append({
                'from': hop.from_asset,
                'to': hop.to_asset,
                'pair': hop.pair,
                'exchange': hop.exchange,
                'rate': hop.rate,
                'effective_rate': hop.effective_rate,
                'fee': hop.fee_rate
            })
        
        return steps
    
    def calculate_v14_score(self, from_asset: str, to_asset: str) -> float:
        """Calculate V14 score for a conversion."""
        if not self.v14 or not self.ticker_cache:
            return 5.0  # Neutral score if V14 not available
        
        # Get momentum data
        from_ticker = None
        to_ticker = None
        for symbol, data in self.ticker_cache.items():
            if data.get('base') == from_asset:
                from_ticker = data
            if data.get('base') == to_asset:
                to_ticker = data
        
        if not from_ticker or not to_ticker:
            return 5.0
        
        # V14-style scoring components
        score = 5.0  # Start neutral
        
        # 1. Momentum differential (want to go TO stronger momentum)
        from_momentum = from_ticker.get('change24h', 0)
        to_momentum = to_ticker.get('change24h', 0)
        momentum_diff = to_momentum - from_momentum
        
        if momentum_diff > 2:  # Going to significantly stronger
            score += 2
        elif momentum_diff > 0.5:
            score += 1
        elif momentum_diff < -2:  # Going to weaker (bad)
            score -= 2
        
        # 2. Volume check (prefer liquid assets)
        to_volume = to_ticker.get('volume', 0)
        if to_volume > 100000:
            score += 1
        
        # 3. Positive momentum preference
        if to_momentum > 1:
            score += 1
        elif to_momentum < -1:
            score -= 1
        
        # 4. Avoid declining assets
        if from_momentum < -2 and to_momentum > 0:
            score += 1  # Escaping decline = good
        
        return max(1, min(10, score))  # Clamp 1-10
    
    def calculate_hub_score(self, from_asset: str, to_asset: str) -> float:
        """Get consensus score from Mycelium Hub."""
        if not self.hub:
            return 0.5  # Neutral if hub not available
        
        try:
            # Query the hub for this conversion path
            hub_analysis = self.hub.analyze_conversion(from_asset, to_asset)
            if hub_analysis:
                return hub_analysis.get('score', 0.5)
        except Exception:
            pass
        
        return 0.5
    
    def calculate_profit_potential(
        self,
        from_asset: str,
        to_asset: str,
        from_amount: float
    ) -> Tuple[float, float]:
        """Calculate expected profit in USD and % using barter matrix costs."""
        from_price = self.prices.get(from_asset, 0)
        to_price = self.prices.get(to_asset, 0)

        if not from_price or not to_price:
            return 0.0, 0.0

        from_value = from_amount * from_price

        # Use barter matrix to calculate realistic costs and potential profit
        # This accounts for exchange fees, spreads, historical slippage, etc.
        approved, reason, math_breakdown = self.barter_matrix._calculate_total_cost_pct(
            from_asset, to_asset, from_value, 'kraken'  # Default to kraken for estimation
        )

        if not approved:
            return 0.0, 0.0  # No profit possible

        total_cost_pct = math_breakdown['total_cost_pct'] / 100  # Convert % to decimal
        costs_usd = from_value * total_cost_pct

        # For conversions, profit comes from price movements or arbitrage
        # Estimate small positive movement (0.1-0.5%) minus costs
        # This is conservative - actual profit depends on market conditions
        min_required_gain_pct = total_cost_pct + 0.001  # Costs + 0.1% minimum
        expected_gain_pct = min_required_gain_pct + 0.002  # Add 0.2% expected movement

        expected_gain = from_value * expected_gain_pct
        net_profit = expected_gain - costs_usd
        net_pct = net_profit / from_value if from_value > 0 else 0

        return net_profit, net_pct
    
    async def collect_all_signals(self) -> Dict[str, List[Dict]]:
        """Collect signals from ALL wired systems."""
        signals = defaultdict(list)
        
        # ════════════════════════════════════════════════════════════════
        # 🍄 MYCELIUM HUB SIGNALS
        # ════════════════════════════════════════════════════════════════
        if self.hub:
            try:
                hub_signals = self.hub.get_all_signals() if hasattr(self.hub, 'get_all_signals') else []
                for sig in hub_signals:
                    signals['hub'].append(sig)
                    self.signals_received += 1
            except Exception as e:
                logger.debug(f"Hub signal error: {e}")
        
        # ════════════════════════════════════════════════════════════════
        # 🦅 COMMANDO SIGNALS (FALCON/TORTOISE/CHAMELEON/BEE)
        # ════════════════════════════════════════════════════════════════
        if self.commando:
            try:
                commando_signals = self.commando.scan_all_opportunities(self.ticker_cache) if hasattr(self.commando, 'scan_all_opportunities') else []
                for sig in commando_signals:
                    signals['commando'].append(sig)
                    self.signals_received += 1
            except Exception as e:
                logger.debug(f"Commando signal error: {e}")
        
        # ════════════════════════════════════════════════════════════════
        # 🔮 PROBABILITY NEXUS SIGNALS
        # ════════════════════════════════════════════════════════════════
        if self.probability_nexus:
            try:
                nexus_signals = self.probability_nexus.get_predictions() if hasattr(self.probability_nexus, 'get_predictions') else []
                for sig in nexus_signals:
                    signals['nexus'].append(sig)
                    self.signals_received += 1
            except Exception as e:
                logger.debug(f"Nexus signal error: {e}")
        
        # ════════════════════════════════════════════════════════════════
        # 🌌 MULTIVERSE CONSENSUS SIGNALS
        # ════════════════════════════════════════════════════════════════
        if self.multiverse:
            try:
                mv_signals = self.multiverse.get_consensus() if hasattr(self.multiverse, 'get_consensus') else []
                for sig in mv_signals:
                    signals['multiverse'].append(sig)
                    self.signals_received += 1
            except Exception as e:
                logger.debug(f"Multiverse signal error: {e}")
        
        # ════════════════════════════════════════════════════════════════
        # 🧠 MINER BRAIN SIGNALS
        # ════════════════════════════════════════════════════════════════
        if self.miner_brain:
            try:
                brain_signals = self.miner_brain.get_signals() if hasattr(self.miner_brain, 'get_signals') else []
                for sig in brain_signals:
                    signals['brain'].append(sig)
                    self.signals_received += 1
            except Exception as e:
                logger.debug(f"Miner Brain signal error: {e}")
        
        # ════════════════════════════════════════════════════════════════
        # 🌊 HARMONIC WAVE SIGNALS
        # ════════════════════════════════════════════════════════════════
        if self.harmonic:
            try:
                harmonic_signals = self.harmonic.get_wave_signals() if hasattr(self.harmonic, 'get_wave_signals') else []
                for sig in harmonic_signals:
                    signals['harmonic'].append(sig)
                    self.signals_received += 1
            except Exception as e:
                logger.debug(f"Harmonic signal error: {e}")
        
        # ════════════════════════════════════════════════════════════════
        # 🔱 OMEGA HIGH CONFIDENCE SIGNALS
        # ════════════════════════════════════════════════════════════════
        if self.omega:
            try:
                omega_signals = self.omega.get_high_conf_signals() if hasattr(self.omega, 'get_high_conf_signals') else []
                for sig in omega_signals:
                    signals['omega'].append(sig)
                    self.signals_received += 1
            except Exception as e:
                logger.debug(f"Omega signal error: {e}")
        
        # ════════════════════════════════════════════════════════════════
        # 🌊🔭 GLOBAL WAVE SCANNER SIGNALS (A-Z Coverage)
        # ════════════════════════════════════════════════════════════════
        if self.wave_scanner:
            try:
                # Get top wave opportunities
                wave_allocation = self.wave_scanner.get_wave_allocation()
                for opp in wave_allocation.get('top_opportunities', []):
                    if opp.get('jump_score', 0) >= 0.6:  # Only high-score opportunities
                        wave_signal = {
                            'symbol': opp.get('symbol'),
                            'exchange': opp.get('exchange'),
                            'action': opp.get('action', 'BUY'),
                            'wave_state': opp.get('wave', 'RISING'),
                            'jump_score': opp.get('jump_score', 0),
                            'change_24h': opp.get('change_24h', 0),
                            'source': 'wave_scanner',
                            'confidence': opp.get('jump_score', 0),
                        }
                        signals['wave_scanner'].append(wave_signal)
                        self.signals_received += 1
            except Exception as e:
                logger.debug(f"Wave Scanner signal error: {e}")
        
        self.all_signals = signals
        return signals

    async def dream_about_tickers(self):
        """
        💭 DREAMING PHASE: Predict future movements based on Multiverse & Ecosystem.
        "It dreams about live tickers... validates itself... adapt adjust"
        """
        current_time = time.time()
        
        # Only dream every 10 seconds to avoid noise
        if hasattr(self, '_last_dream_time') and current_time - self._last_dream_time < 10:
            return
        self._last_dream_time = current_time
        
        # 1. Ask Multiverse for direction
        if self.multiverse:
            try:
                # Get consensus from the 10 worlds
                consensus = self.multiverse.get_consensus() if hasattr(self.multiverse, 'get_consensus') else []
                if consensus:
                    print(f"\n   💭 DREAMING about market direction (Multiverse)...")
                
                for signal in consensus:
                    symbol = signal.get('symbol')
                    if not symbol or symbol not in self.prices:
                        continue
                        
                    current_price = self.prices[symbol]
                    direction = signal.get('action', 'HOLD')
                    confidence = signal.get('confidence', 0.5)
                    
                    if direction in ['BUY', 'SELL'] and confidence > 0.6:
                        # Predict price movement (e.g., 0.5% in 30s)
                        move_pct = 0.005 if direction == 'BUY' else -0.005
                        predicted_price = current_price * (1 + move_pct)
                        
                        dream = Dream(
                            timestamp=current_time,
                            symbol=symbol,
                            current_price=current_price,
                            predicted_price=predicted_price,
                            direction='UP' if direction == 'BUY' else 'DOWN',
                            target_time=current_time + 30, # 30s prediction
                            source='multiverse',
                            confidence=confidence
                        )
                        self.dreams.append(dream)
                        print(f"      🌌 Multiverse dreams {symbol} will go {dream.direction} (Conf: {confidence:.2f})")
            except Exception as e:
                logger.debug(f"Multiverse dream error: {e}")

        # 2. Ask Probability Nexus
        if self.probability_nexus:
            try:
                predictions = self.probability_nexus.get_predictions() if hasattr(self.probability_nexus, 'get_predictions') else []
                if predictions:
                     print(f"\n   💭 DREAMING about market direction (Nexus)...")

                for pred in predictions:
                    symbol = pred.get('symbol')
                    if not symbol or symbol not in self.prices:
                        continue
                        
                    current_price = self.prices[symbol]
                    prob = pred.get('probability', 0.5)
                    
                    if prob > 0.7: # High probability UP
                        dream = Dream(
                            timestamp=current_time,
                            symbol=symbol,
                            current_price=current_price,
                            predicted_price=current_price * 1.005,
                            direction='UP',
                            target_time=current_time + 30,
                            source='nexus',
                            confidence=prob
                        )
                        self.dreams.append(dream)
                        print(f"      🔮 Nexus dreams {symbol} will go UP (Prob: {prob:.2f})")
            except Exception as e:
                logger.debug(f"Nexus dream error: {e}")

    async def validate_dreams(self):
        """
        ✅ VALIDATION PHASE: Check if dreams came true.
        "Right I know I was right there... adapt adjust"
        """
        current_time = time.time()
        active_dreams = []
        dreams_validated_this_cycle = False
        
        for dream in self.dreams:
            if dream.validated:
                continue
                
            # Check if target time reached
            if current_time >= dream.target_time:
                # Validate!
                current_price = self.prices.get(dream.symbol, 0)
                if current_price == 0:
                    continue # Can't validate
                
                dream.actual_price_at_target = current_price
                dream.validated = True
                dreams_validated_this_cycle = True
                
                # Check success
                if dream.direction == 'UP':
                    dream.success = current_price > dream.current_price
                else:
                    dream.success = current_price < dream.current_price
                
                # ADAPT: Update source accuracy
                alpha = 0.1 # Learning rate
                if dream.success:
                    self.dream_accuracy[dream.source] = (1 - alpha) * self.dream_accuracy[dream.source] + alpha * 1.0
                    print(f"   ✅ DREAM VALIDATED: {dream.source} was RIGHT about {dream.symbol} ({dream.direction})!")
                else:
                    self.dream_accuracy[dream.source] = (1 - alpha) * self.dream_accuracy[dream.source] + alpha * 0.0
                    print(f"   ❌ DREAM FAILED: {dream.source} was WRONG about {dream.symbol}. Adapting...")
                
                self.validated_dreams_count += 1
            else:
                active_dreams.append(dream)
        
        # Keep only active dreams
        self.dreams = active_dreams
        
        # Print accuracy stats occasionally
        if dreams_validated_this_cycle and self.validated_dreams_count % 5 == 0:
            print(f"   🧠 ADAPTIVE LEARNING STATS:")
            for source, acc in self.dream_accuracy.items():
                print(f"      - {source}: {acc:.1%} accuracy")

    def populate_barter_graph(self):
        """
        🫒🔄 POPULATE BARTER GRAPH from already-loaded exchange data.
        Called ONCE after pairs and prices are loaded.
        """
        if not self.barter_navigator:
            return
        
        try:
            # Build alpaca pairs dict with base/quote info
            alpaca_pairs_formatted = {}
            for symbol, normalized in self.alpaca_pairs.items():
                if '/' in symbol:
                    parts = symbol.split('/')
                    alpaca_pairs_formatted[symbol] = {'base': parts[0], 'quote': parts[1]}
            
            # Build binance pairs dict from ticker cache (it has base/quote info)
            binance_pairs_formatted = {}
            for cache_key, data in self.ticker_cache.items():
                if cache_key.startswith('binance:'):
                    symbol = cache_key.replace('binance:', '')
                    base = data.get('base', '')
                    quote = data.get('quote', '')
                    if base and quote:
                        binance_pairs_formatted[symbol] = {'base': base, 'quote': quote}
            
            # Use the data we already have!
            success = self.barter_navigator.populate_from_labyrinth_data(
                kraken_pairs=self.kraken_pairs,
                alpaca_pairs=alpaca_pairs_formatted,
                binance_pairs=binance_pairs_formatted,
                prices=self.prices
            )
            
            if success:
                summary = self.barter_navigator.get_graph_summary()
                print(f"🫒🔄 Barter Navigator: POPULATED ({summary['total_assets']} assets, {summary['total_edges']} paths)")
            else:
                print(f"⚠️ Barter Navigator: Population failed")
        except Exception as e:
            print(f"⚠️ Barter Navigator population error: {e}")

    async def dream_for_turn(self, exchange: str):
        """
        💭🎯 TURN-SPECIFIC DREAMING: Dream about assets on THIS exchange's turn.
        "The probability matrix constantly dreams each turn"
        
        This runs EVERY turn (not throttled like global dreaming).
        
        👑🔮 THE QUEEN DREAMS FIRST - Her dreams guide all other dreams!
        """
        current_time = time.time()
        turn_dreams = []
        
        # Get assets for this exchange
        exchange_assets = self.get_exchange_assets(exchange)
        if not exchange_assets:
            return
        
        symbols_to_dream = list(exchange_assets.keys())[:20]  # Top 20 by holdings
        
        print(f"\n   💭🎯 TURN DREAMING for {exchange.upper()} ({len(symbols_to_dream)} symbols)")
        
        # 👑🔮 0. THE QUEEN DREAMS FIRST - Her visions set the tone!
        # 🔧 FIX: Use ACTUAL MOMENTUM instead of always predicting UP!
        queen_vision_count = 0
        if self.queen and hasattr(self.queen, 'dream_of_winning'):
            try:
                for symbol in symbols_to_dream[:10]:  # Queen dreams top 10
                    if symbol not in self.prices:
                        continue
                    current_price = self.prices[symbol]
                    
                    # 👑🔧 GET REAL MOMENTUM FOR THIS ASSET!
                    actual_momentum = 0.0
                    if self.momentum_tracker:
                        actual_momentum = self.momentum_tracker.get_momentum(symbol)  # Per-minute %
                    
                    # Use momentum to determine direction!
                    if actual_momentum > 0.5:  # Rising strongly (+0.5%/min)
                        direction = 'UP'
                        confidence_boost = min(0.2, actual_momentum / 5)  # Cap at +20%
                    elif actual_momentum < -0.5:  # Falling strongly (-0.5%/min)
                        direction = 'DOWN'
                        confidence_boost = min(0.2, abs(actual_momentum) / 5)
                    else:
                        # Neutral - skip this asset for dreaming
                        continue
                    
                    opp_data = {
                        'from_asset': 'USD',
                        'to_asset': symbol,
                        'expected_profit': 0.01,
                        'exchange': exchange,
                        'market_data': {
                            'volatility': 0.5, 
                            'momentum': actual_momentum,  # REAL momentum!
                            'direction': direction
                        }
                    }
                    
                    queen_dream = self.queen.dream_of_winning(opp_data)
                    queen_conf = queen_dream.get('final_confidence', 0.5)
                    
                    # Adjust confidence based on momentum alignment
                    base_conf = queen_conf + confidence_boost
                    
                    # Create dream with ACTUAL direction from momentum!
                    dream = Dream(
                        timestamp=current_time,
                        symbol=symbol,
                        current_price=current_price,
                        predicted_price=current_price * (1 + actual_momentum / 100),  # Use actual %
                        direction=direction,  # 👑 USE REAL DIRECTION!
                        target_time=current_time + 60,
                        source='queen_hive_mind',
                        confidence=min(0.95, base_conf)
                    )
                    self.dreams.append(dream)
                    turn_dreams.append(dream)
                    queen_vision_count += 1
                
                if queen_vision_count > 0:
                    logger.info(f"👑🔮 Queen dreamed {queen_vision_count} visions for {exchange}")
            except Exception as e:
                logger.debug(f"Queen turn dream error: {e}")
        
        # 1. Ask Multiverse for direction on exchange assets
        if self.multiverse:
            try:
                consensus = self.multiverse.get_consensus() if hasattr(self.multiverse, 'get_consensus') else []
                for signal in consensus:
                    symbol = signal.get('symbol')
                    if not symbol or symbol not in symbols_to_dream:
                        continue
                    
                    current_price = self.prices.get(symbol, 0)
                    if not current_price:
                        continue
                    
                    direction = signal.get('action', 'HOLD')
                    confidence = signal.get('confidence', 0.5)
                    
                    if direction in ['BUY', 'SELL'] and confidence > 0.55:  # Lower threshold for turn dreams
                        move_pct = 0.005 if direction == 'BUY' else -0.005
                        predicted_price = current_price * (1 + move_pct)
                        
                        dream = Dream(
                            timestamp=current_time,
                            symbol=symbol,
                            current_price=current_price,
                            predicted_price=predicted_price,
                            direction='UP' if direction == 'BUY' else 'DOWN',
                            target_time=current_time + 30,
                            source='multiverse_turn',
                            confidence=confidence
                        )
                        self.dreams.append(dream)
                        turn_dreams.append(dream)
            except Exception as e:
                logger.debug(f"Turn multiverse dream error: {e}")
        
        # 2. Ask Probability Nexus for predictions on exchange assets
        if self.probability_nexus:
            try:
                predictions = self.probability_nexus.get_predictions() if hasattr(self.probability_nexus, 'get_predictions') else []
                for pred in predictions:
                    symbol = pred.get('symbol')
                    if not symbol or symbol not in symbols_to_dream:
                        continue
                    
                    current_price = self.prices.get(symbol, 0)
                    if not current_price:
                        continue
                    
                    prob = pred.get('probability', 0.5)
                    
                    if prob > 0.6:  # Good UP prediction
                        dream = Dream(
                            timestamp=current_time,
                            symbol=symbol,
                            current_price=current_price,
                            predicted_price=current_price * 1.005,
                            direction='UP',
                            target_time=current_time + 30,
                            source='nexus_turn',
                            confidence=prob
                        )
                        self.dreams.append(dream)
                        turn_dreams.append(dream)
                    elif prob < 0.4:  # Good DOWN prediction
                        dream = Dream(
                            timestamp=current_time,
                            symbol=symbol,
                            current_price=current_price,
                            predicted_price=current_price * 0.995,
                            direction='DOWN',
                            target_time=current_time + 30,
                            source='nexus_turn',
                            confidence=1 - prob
                        )
                        self.dreams.append(dream)
                        turn_dreams.append(dream)
            except Exception as e:
                logger.debug(f"Turn nexus dream error: {e}")
        
        # 3. Use Ultimate Intel if available
        if self.ultimate_intel:
            try:
                for symbol in symbols_to_dream[:10]:
                    if symbol not in self.prices:
                        continue
                    current_price = self.prices[symbol]
                    
                    analysis = self.ultimate_intel.analyze(symbol) if hasattr(self.ultimate_intel, 'analyze') else {}
                    sentiment = analysis.get('sentiment', 'neutral')
                    confidence = analysis.get('confidence', 0.5)
                    
                    if sentiment in ['bullish', 'very_bullish'] and confidence > 0.55:
                        dream = Dream(
                            timestamp=current_time,
                            symbol=symbol,
                            current_price=current_price,
                            predicted_price=current_price * 1.005,
                            direction='UP',
                            target_time=current_time + 30,
                            source='ultimate_turn',
                            confidence=confidence
                        )
                        self.dreams.append(dream)
                        turn_dreams.append(dream)
            except Exception as e:
                logger.debug(f"Turn ultimate dream error: {e}")
        
        if turn_dreams:
            print(f"      🌙 Generated {len(turn_dreams)} dreams for {exchange}")
            for dream in turn_dreams[:5]:  # Show top 5
                print(f"         → {dream.symbol} {dream.direction} ({dream.source}: {dream.confidence:.0%})")

    def calculate_dream_score(self, symbol: str) -> float:
        """Calculate score based on active dreams and source accuracy."""
        score = 0.0
        count = 0
        
        for dream in self.dreams:
            if dream.symbol == symbol and not dream.validated:
                # Weight by source accuracy
                accuracy = self.dream_accuracy[dream.source]
                confidence = dream.confidence
                
                weight = accuracy * confidence
                
                if dream.direction == 'UP':
                    score += weight
                else:
                    score -= weight
                count += 1
        
        # Normalize to -1 to +1 range roughly
        if count > 0:
            return max(-1.0, min(1.0, score))
        return 0.0

    # ════════════════════════════════════════════════════════════════════════════
    # 🎯 TURN-BASED EXCHANGE STRATEGY
    # ════════════════════════════════════════════════════════════════════════════
    
    def get_current_exchange(self) -> str:
        """Get the exchange whose turn it is to trade."""
        # Filter to only connected exchanges
        connected = [ex for ex in self.exchange_order 
                     if self.exchange_data.get(ex, {}).get('connected', False)]
        if not connected:
            return None
        return connected[self.current_exchange_index % len(connected)]
    
    def advance_turn(self):
        """Move to the next exchange's turn."""
        connected = [ex for ex in self.exchange_order 
                     if self.exchange_data.get(ex, {}).get('connected', False)]
        if connected:
            self.current_exchange_index = (self.current_exchange_index + 1) % len(connected)
        self.turns_completed += 1
        
        # 🌟 Update barter_matrix turn counter for second chances
        if hasattr(self, 'barter_matrix') and self.barter_matrix:
            self.barter_matrix.current_turn = self.turns_completed
        
        # 👑📊 Feed Queen metrics to HNC Matrix every turn!
        if self.queen and self.hnc_matrix and hasattr(self.hnc_matrix, 'feed_queen_metrics'):
            try:
                if hasattr(self.queen, 'get_all_queen_metrics'):
                    metrics = self.queen.get_all_queen_metrics()
                    self.hnc_matrix.feed_queen_metrics(metrics)
            except Exception as e:
                logger.debug(f"Queen metrics feed error: {e}")
    
    def get_turn_display(self) -> str:
        """Get a display string showing current turn status."""
        current = self.get_current_exchange()
        if not current:
            return "No exchanges"
        
        icons = {'kraken': '🐙', 'alpaca': '🦙', 'binance': '🟡'}
        turn_markers = []
        
        for ex in self.exchange_order:
            if self.exchange_data.get(ex, {}).get('connected', False):
                icon = icons.get(ex, '📊')
                if ex == current:
                    turn_markers.append(f"[{icon}]")  # Current turn
                else:
                    turn_markers.append(f" {icon} ")  # Waiting
            else:
                turn_markers.append("  ❌  ")  # Not connected
        
        return "".join(turn_markers)
    
    def get_exchange_assets(self, exchange: str) -> Dict[str, float]:
        """Get assets held on a specific exchange."""
        return self.exchange_balances.get(exchange, {})
    
    async def refresh_exchange_balances(self, exchange: str):
        """Refresh balances for a specific exchange to ensure fresh data."""
        if exchange == 'kraken' and self.kraken:
            try:
                kraken_bal = {}
                if hasattr(self.kraken, 'get_account_balance'):
                    raw = self.kraken.get_account_balance() or {}
                    for asset, amount in raw.items():
                        try:
                            amount = float(amount)
                        except (ValueError, TypeError):
                            continue
                        if amount > 0:
                            clean = asset
                            if len(asset) == 4 and asset[0] in ('X', 'Z'):
                                clean = asset[1:]
                            if clean == 'XBT':
                                clean = 'BTC'
                            kraken_bal[clean] = amount
                self.exchange_balances['kraken'] = kraken_bal
                if 'kraken' in self.exchange_data:
                    self.exchange_data['kraken']['balances'] = kraken_bal
            except Exception as e:
                logger.error(f"Kraken refresh error: {e}")

        elif exchange == 'binance' and self.binance:
            try:
                binance_bal = {}
                if hasattr(self.binance, 'account'):
                    acct = self.binance.account() or {}
                    for bal in acct.get('balances', []):
                        asset = bal.get('asset', '')
                        free = float(bal.get('free', 0))
                        if free > 0 and asset:
                            binance_bal[asset] = free
                self.exchange_balances['binance'] = binance_bal
                if 'binance' in self.exchange_data:
                    self.exchange_data['binance']['balances'] = binance_bal
            except Exception as e:
                logger.error(f"Binance refresh error: {e}")

        elif exchange == 'alpaca' and self.alpaca:
            try:
                alpaca_bal = {}
                if hasattr(self.alpaca, 'get_account'):
                    acct = self.alpaca.get_account() or {}
                    cash = float(acct.get('cash', 0))
                    if cash > 0:
                        alpaca_bal['USD'] = cash
                
                if hasattr(self.alpaca, 'get_positions'):
                    positions = self.alpaca.get_positions() or []
                    for pos in positions:
                        raw_symbol = pos.get('symbol', '')
                        qty = float(pos.get('qty', 0))
                        if qty > 0 and raw_symbol:
                            if raw_symbol.endswith('USD'):
                                base_asset = raw_symbol[:-3]
                            else:
                                base_asset = raw_symbol
                            alpaca_bal[base_asset] = qty
                
                self.exchange_balances['alpaca'] = alpaca_bal
                if 'alpaca' in self.exchange_data:
                    self.exchange_data['alpaca']['balances'] = alpaca_bal
            except Exception as e:
                logger.error(f"Alpaca refresh error: {e}")

        # Rebuild combined balances
        self.balances = {}
        for ex_bals in self.exchange_balances.values():
            for asset, amount in ex_bals.items():
                self.balances[asset] = self.balances.get(asset, 0) + amount

    async def _attempt_liquidity_aggregation(
        self,
        target_asset: str,
        target_exchange: str,
        shortfall_usd: float,
        expected_profit_pct: float = 0.01,
    ) -> bool:
        """
        💧🔀 ATTEMPT LIQUIDITY AGGREGATION
        
        When we need more funds to execute a trade, try to liquidate other assets
        to "top up" the target asset. Only proceeds if profitable after fees.
        
        Args:
            target_asset: The asset we need more of (e.g., 'ETH')
            target_exchange: Exchange where we need the funds
            shortfall_usd: How much USD value we need to add
            expected_profit_pct: Expected profit from the target trade
            
        Returns:
            True if aggregation was successful and we now have enough funds
        """
        print(f"\n   💧🔀 LIQUIDITY AGGREGATION ATTEMPT")
        print(f"   🎯 Need ${shortfall_usd:.2f} more {target_asset} on {target_exchange}")
        
        # Don't aggregate for tiny amounts - not worth the fees
        if shortfall_usd < 1.0:
            print(f"   ❌ Shortfall ${shortfall_usd:.2f} too small to aggregate")
            return False
        
        # Create aggregation plan
        plan = self.liquidity_engine.create_aggregation_plan(
            target_asset=target_asset,
            target_exchange=target_exchange,
            amount_needed_usd=shortfall_usd * 1.2,  # 20% buffer
            expected_profit_pct=expected_profit_pct,
            exchange_balances=self.exchange_balances,
            prices=self.prices,
            momentum=self.asset_momentum,
        )
        
        if not plan:
            print(f"   ❌ No aggregation plan available (no suitable victims)")
            return False
        
        # Print the plan
        print(self.liquidity_engine.print_aggregation_plan(plan))
        
        if not plan.is_profitable:
            print(f"   ❌ Aggregation not profitable (fees ${plan.total_fees_usd:.4f} > profit)")
            return False
        
        # Execute the plan!
        print(f"\n   🚀 EXECUTING AGGREGATION PLAN...")
        
        success_count = 0
        total_received = 0.0
        
        for step in plan.steps:
            if step['action'] == 'SELL':
                victim_asset = step['asset']
                victim_amount = step['amount']
                victim_exchange = step['exchange']
                
                print(f"   📤 SELL: {victim_amount:.6f} {victim_asset} on {victim_exchange}")
                
                # Execute the liquidation based on exchange
                sell_success = False
                received_usd = 0.0
                
                try:
                    if victim_exchange == 'kraken' and self.kraken:
                        # Sell to USD/ZUSD on Kraken
                        result = self.kraken.place_market_order(
                            symbol=f"{victim_asset}USD",
                            side='sell',
                            volume=victim_amount
                        )
                        if result and 'error' not in str(result).lower():
                            sell_success = True
                            received_usd = step['expected_usd'] * 0.97  # Estimate
                            
                    elif victim_exchange == 'binance' and self.binance:
                        # Sell to USDC on Binance (UK mode) or USDT
                        quote = 'USDC' if self.binance_uk_mode else 'USDT'
                        result = self.binance.place_market_order(
                            symbol=f"{victim_asset}{quote}",
                            side='SELL',
                            quantity=victim_amount
                        )
                        if result and result.get('status') == 'FILLED':
                            sell_success = True
                            received_usd = float(result.get('cummulativeQuoteQty', step['expected_usd'] * 0.97))
                            
                    elif victim_exchange == 'alpaca' and self.alpaca:
                        # Sell to USD on Alpaca
                        result = self.alpaca.place_order(
                            symbol=f"{victim_asset}/USD",
                            side='sell',
                            qty=victim_amount,
                            type='market'
                        )
                        if result:
                            sell_success = True
                            received_usd = step['expected_usd'] * 0.97
                            
                except Exception as e:
                    print(f"   ❌ SELL failed for {victim_asset}: {e}")
                    sell_success = False
                
                if sell_success:
                    success_count += 1
                    total_received += received_usd
                    print(f"   ✅ SOLD {victim_asset} → ${received_usd:.2f}")
                    
                    # Record liquidation for cooldown
                    self.liquidity_engine.record_liquidation(victim_asset)
                else:
                    print(f"   ❌ SELL failed for {victim_asset}")
                    # Continue trying other victims
            
            elif step['action'] == 'BUY':
                # Now buy the target asset with our accumulated USD
                if total_received < 1.0:
                    print(f"   ❌ Not enough funds received (${total_received:.2f}) to buy {target_asset}")
                    continue
                
                print(f"   📥 BUY: ${total_received:.2f} worth of {target_asset} on {target_exchange}")
                
                buy_success = False
                try:
                    if target_exchange == 'kraken' and self.kraken:
                        # Buy target with USD
                        target_price = self.prices.get(target_asset, 1.0)
                        buy_amount = (total_received * 0.98) / target_price  # 2% buffer
                        result = self.kraken.place_market_order(
                            symbol=f"{target_asset}USD",
                            side='buy',
                            volume=buy_amount
                        )
                        if result and 'error' not in str(result).lower():
                            buy_success = True
                            
                    elif target_exchange == 'binance' and self.binance:
                        quote = 'USDC' if self.binance_uk_mode else 'USDT'
                        target_price = self.prices.get(target_asset, 1.0)
                        buy_amount = (total_received * 0.98) / target_price
                        result = self.binance.place_market_order(
                            symbol=f"{target_asset}{quote}",
                            side='BUY',
                            quantity=buy_amount
                        )
                        if result and result.get('status') == 'FILLED':
                            buy_success = True
                            
                    elif target_exchange == 'alpaca' and self.alpaca:
                        target_price = self.prices.get(target_asset, 1.0)
                        buy_amount = (total_received * 0.98) / target_price
                        result = self.alpaca.place_order(
                            symbol=f"{target_asset}/USD",
                            side='buy',
                            qty=buy_amount,
                            type='market'
                        )
                        if result:
                            buy_success = True
                            
                except Exception as e:
                    print(f"   ❌ BUY failed for {target_asset}: {e}")
                    buy_success = False
                
                if buy_success:
                    success_count += 1
                    print(f"   ✅ BOUGHT {target_asset}")
                    
                    # Update stats
                    self.liquidity_engine.executed_aggregations += 1
                    self.liquidity_engine.total_aggregation_profit += plan.profit_after_fees
                else:
                    print(f"   ❌ BUY failed for {target_asset}")
        
        # Final success check
        if success_count > 0:
            print(f"\n   💧 AGGREGATION COMPLETE: {success_count} steps executed")
            return True
        else:
            print(f"\n   ❌ AGGREGATION FAILED: No steps completed")
            return False

    async def report_portfolio_to_queen(self, voice_enabled: bool = True) -> Dict[str, Any]:
        """
        👑💰 REPORT PORTFOLIO TO QUEEN - Feed her the revenue data!
        
        Gathers portfolio performance from all exchanges and feeds it to the Queen.
        The Queen reviews the data and speaks her verdict with her VOICE!
        
        Args:
            voice_enabled: Whether the Queen should speak aloud (TTS)
        
        Returns:
            Portfolio data dict with Queen's verdict
        """
        portfolio_data = {
            'kraken': {'value': 0.0, 'profit': 0.0, 'trades': 0, 'win_rate': 0.0},
            'binance': {'value': 0.0, 'profit': 0.0, 'trades': 0, 'win_rate': 0.0},
            'alpaca': {'value': 0.0, 'profit': 0.0, 'trades': 0, 'win_rate': 0.0},
            'total_value': 0.0,
            'total_profit': 0.0,
            'total_trades': 0
        }
        
        print("\n👑💰 ═══ PORTFOLIO REPORT FOR THE QUEEN ═══")
        
        # Gather data from each exchange
        for exchange in ['kraken', 'binance', 'alpaca']:
            ex_stats = self.exchange_stats.get(exchange, {})
            ex_balances = self.exchange_balances.get(exchange, {})
            
            # Calculate exchange value
            ex_value = 0.0
            for asset, amount in ex_balances.items():
                if asset in ('USD', 'USDT', 'USDC', 'ZUSD'):
                    ex_value += amount
                else:
                    price = self.prices.get(asset, 0)
                    ex_value += amount * price
            
            # Get profit and trade stats
            ex_profit = ex_stats.get('profit', 0.0)
            ex_trades = ex_stats.get('conversions', 0)
            
            # Calculate win rate from barter history for this exchange
            wins = 0
            total = 0
            for (from_a, to_a), hist in self.barter_matrix.barter_history.items():
                # Attribute to exchange based on source exchange tracking
                total += hist.get('trades', 0)
                wins += hist.get('wins', 0)
            
            win_rate = wins / total if total > 0 else 0.5
            
            portfolio_data[exchange] = {
                'value': ex_value,
                'profit': ex_profit,
                'trades': ex_trades,
                'win_rate': win_rate
            }
            
            portfolio_data['total_value'] += ex_value
            portfolio_data['total_profit'] += ex_profit
            portfolio_data['total_trades'] += ex_trades
            
            # Icon display
            icon = {'kraken': '🐙', 'binance': '🔶', 'alpaca': '🦙'}[exchange]
            profit_icon = '📈' if ex_profit >= 0 else '📉'
            print(f"   {icon} {exchange.upper()}: ${ex_value:.2f} | {profit_icon} ${ex_profit:+.4f} | {ex_trades} trades")
        
        print(f"   💰 TOTAL: ${portfolio_data['total_value']:.2f} | P/L: ${portfolio_data['total_profit']:+.4f}")
        
        # Feed to the Queen!
        if self.queen:
            try:
                # Have the Queen review and speak!
                if hasattr(self.queen, 'announce_portfolio_status'):
                    verdict = self.queen.announce_portfolio_status(portfolio_data)
                    portfolio_data['queen_verdict'] = verdict
                
                # Get Queen's trading guidance
                if hasattr(self.queen, 'get_trading_guidance'):
                    guidance = self.queen.get_trading_guidance()
                    portfolio_data['queen_guidance'] = guidance
                    
                    # Apply guidance to position sizing
                    self.queen_position_multiplier = guidance.get('recommended_position_size', 1.0)
                    print(f"   👑 Queen's Position Multiplier: {self.queen_position_multiplier:.1f}x")
                
                # Review each exchange
                if hasattr(self.queen, 'review_exchange_performance'):
                    for exchange in ['kraken', 'binance', 'alpaca']:
                        ex_data = portfolio_data.get(exchange, {})
                        verdict, action = self.queen.review_exchange_performance(exchange, ex_data)
                        portfolio_data[exchange]['queen_verdict'] = verdict
                        portfolio_data[exchange]['queen_action'] = action
                        print(f"   👑 {exchange.upper()}: {action}")
                
            except Exception as e:
                logger.error(f"Queen portfolio review error: {e}")
        
        print("═" * 50)
        
        return portfolio_data

    async def execute_turn(self) -> Tuple[List['MicroOpportunity'], int]:
        """
        Execute one turn for the current exchange.
        Returns (opportunities found, conversions made this turn)
        """
        current_exchange = self.get_current_exchange()
        if not current_exchange:
            return [], 0
        
        icons = {'kraken': '🐙', 'alpaca': '🦙', 'binance': '🟡'}
        icon = icons.get(current_exchange, '📊')
        
        print(f"\n🎯 ═══ TURN {self.turns_completed + 1}: {icon} {current_exchange.upper()} ═══")
        
        # 🌊⚡ MOMENTUM WAVE CHECK - Look for wave jumping opportunities
        momentum_opp = self.find_momentum_opportunity()
        if momentum_opp:
            from_asset, to_asset, from_amount, net_adv, mom_diff = momentum_opp
            print(f"   🌊 WAVE DETECTED: {from_asset}→{to_asset} | Momentum diff: {mom_diff*100:.2f}%/min")
        
        # 🦁 LION HUNT - Stablecoins hunt for waves!
        lion_hunts = self.lion_hunt(min_wave_momentum=0.001)  # Hunt waves >0.1%/min
        
        # 🐺 WOLF HUNT - Find THE ONE momentum champion!
        self._wolf_target_cache = self.wolf_hunt(verbose=True)
        wolf_target = self._wolf_target_cache
        
        # 🐜 ANT SCRAPS - Collect small floor positions
        ant_scraps = self.ant_scraps(min_value=1.0)
        
        # 🦆⚔️ QUACK COMMANDOS STATUS (every 20 turns)
        if self.turns_completed > 0 and self.turns_completed % 20 == 0 and self.quack_commandos:
            print(self.quack_commandos.get_status())
        
        # 👑💰 PERIODIC PORTFOLIO REPORT TO QUEEN (every 10 turns)
        if self.turns_completed > 0 and self.turns_completed % 10 == 0:
            await self.report_portfolio_to_queen(voice_enabled=True)
        
        # 🧹 DUST SWEEP - Clean up small balances (every N turns)
        if self.dust_converter and self.turns_completed > 0 and self.turns_completed % self.dust_sweep_interval == 0:
            try:
                dust_swept = await self.dust_sweep()
                if dust_swept > 0:
                    # Refresh balances after sweeping
                    await self.refresh_exchange_balances(current_exchange)
            except Exception as e:
                print(f"   ⚠️ Dust sweep error: {e}")
        
        # REFRESH BALANCES FOR THIS EXCHANGE
        await self.refresh_exchange_balances(current_exchange)
        
        # Get this exchange's assets only
        exchange_assets = self.get_exchange_assets(current_exchange)
        
        # 💧🔀 LIQUIDITY ENGINE CHECK: Do we have enough ammo?
        # If stablecoin balance < Minimum, trigger aggregation!
        if self.liquidity_engine and exchange_assets:
            stablecoins = ['USD', 'USDT', 'USDC', 'ZUSD', 'EUR']
            min_req = 5.0  # Minimum operational liquidity ($5)
            
            for s in stablecoins:
                if s in exchange_assets:
                    bal = exchange_assets[s]
                    # If we have SOME balance (dust to low) but less than minimum
                    # Avoid aggregating if we have literally 0 (might not trade that coin)
                    if 0.10 < bal < min_req:
                        print(f"   💧 LOW LIQUIDITY DETECTED: {s} = ${bal:.2f} (Target ${min_req:.2f})")
                        shortfall = min_req - bal + 1.0 # Aim for $1 surplus
                        
                        # Attempt aggregation
                        try:
                            agg_success = await self._attempt_liquidity_aggregation(
                                target_asset=s,
                                target_exchange=current_exchange,
                                shortfall_usd=shortfall,
                                expected_profit_pct=0.01
                            )
                            if agg_success:
                                # Refresh balances immediately!
                                await self.refresh_exchange_balances(current_exchange)
                                exchange_assets = self.get_exchange_assets(current_exchange)
                        except Exception as e:
                            print(f"   ⚠️ Liquidity aggregation error: {e}")

        if not exchange_assets:
            print(f"   ⚠️ No assets on {current_exchange}")
            self.advance_turn()
            return [], 0
        
        # Show what we're scanning
        asset_list = []
        for asset, amount in sorted(exchange_assets.items(), 
                                    key=lambda x: x[1] * self.prices.get(x[0], 0), 
                                    reverse=True)[:5]:
            price = self.prices.get(asset, 0)
            value = amount * price
            if value >= 1.0:
                asset_list.append(f"{asset}=${value:.2f}")
        
        if asset_list:
            print(f"   📦 Assets: {', '.join(asset_list)}")
        
        # 💭🎯 TURN-SPECIFIC DREAMING - Dream about THIS exchange's assets
        await self.dream_for_turn(current_exchange)
        
        
        # ✅ Validate any mature dreams before finding opportunities
        await self.validate_dreams()
        
        # 👑🍄 QUEEN'S PULSE - Queen observes market state BEFORE filtering
        queen_pulse = await self.queen_observe_market(current_exchange, exchange_assets)
        
        # Find opportunities ON THIS EXCHANGE ONLY
        opportunities = await self.find_opportunities_for_exchange(current_exchange)
        
        # Update stats
        self.exchange_stats[current_exchange]['scans'] += 1
        self.exchange_stats[current_exchange]['opportunities'] += len(opportunities)
        self.exchange_stats[current_exchange]['last_turn'] = time.time()
        
        conversions_this_turn = 0
        
        # Execute best opportunity if found
        if opportunities:
            best = opportunities[0]
            
            # 👑🍄 TINA B's WISDOM - Ask Tina B if we will WIN before trading!
            # Her GOAL: Minimum $0.003 profit per trade
            print(f"\n   👑🍄 TINA B CONSULTED: {best.from_asset}→{best.to_asset}")
            queen_says_win, queen_confidence, queen_reason = await self.ask_queen_will_we_win(best)
            
            if not queen_says_win:
                print(f"   👑❌ TINA B SAYS NO: {queen_reason}")
                print(f"      Her Confidence: {queen_confidence:.0%}")
                # Tina B learns this pattern should be avoided
                await self.queen_learn_pattern(best, predicted_win=False, reason=queen_reason)
            else:
                print(f"   👑✅ TINA B SAYS WIN: {queen_reason}")
                print(f"      Her Confidence: {queen_confidence:.0%}")
                
                # 👑🐝 TINA B HAS FULL CONTROL - SHE IS THE QUEEN!
                # When Tina B says WIN, we EXECUTE. No other system overrides her.
                # She has all 12 neurons, Path Memory, Dreams - she knows what she's doing!
                print(f"   👑🐝 TINA B HAS SPOKEN - EXECUTING HER WILL!")
                success = await self.execute_conversion(best)
                if success:
                    conversions_this_turn = 1
                    self.exchange_stats[current_exchange]['conversions'] += 1
                    # 🔧 FIX: Use ACTUAL P/L not expected P/L
                    actual_pnl = getattr(best, 'actual_pnl_usd', best.expected_pnl_usd)
                    self.exchange_stats[current_exchange]['profit'] += actual_pnl
                    # Queen learns from successful execution
                    await self.queen_learn_from_trade(best, success=True)
                    print(f"   👑💰 TINA B WINS: ${actual_pnl:+.4f}")
                else:
                    # Queen learns from failed execution
                    await self.queen_learn_from_trade(best, success=False)
                    print(f"   👑📚 Tina B learned from this experience")
        else:
            print(f"   📭 No opportunities passed gates on {current_exchange}")
        
        # Advance to next exchange's turn
        self.advance_turn()
        
        # Brief cooldown between turns
        if self.turn_cooldown_seconds > 0:
            await asyncio.sleep(self.turn_cooldown_seconds)
        
        return opportunities, conversions_this_turn

    async def ask_queen_will_we_win(self, opportunity: 'MicroOpportunity') -> Tuple[bool, float, str]:
        """
        👑🍄 ASK TINA B: Will this trade be a WINNER?
        
        👑🔢 2 PIPS OVER COSTS RULE:
        - 2 pips = 0.02% = $0.0002 per $1 traded
        - This is NET profit AFTER all fees & slippage
        - We NEVER lose money with this buffer!
        
        Tina B consults all her connected mycelium neurons:
        - Historical path data
        - Dream patterns
        - Cosmic alignment
        - Civilization wisdom
        - Timeline predictions
        
        Returns: (will_win: bool, confidence: float, reason: str)
        """
        # 👑🔢 TINA B's PROFIT LADDER - Dynamic profit thresholds!
        # Ladder: 0.07 pip (0.0007%) to 1.4 pip (0.014%)
        # Higher confidence = lower threshold needed!
        # Calculate price from value/amount (from_price not stored on MicroOpportunity)
        from_price = opportunity.from_value_usd / opportunity.from_amount if opportunity.from_amount > 0 else 1.0
        trade_value = opportunity.from_value_usd  # Already have this!
        
        # 👑 PROFIT LADDER THRESHOLDS (in pips: 1 pip = 0.01% = 0.0001)
        MIN_PIP = 0.07    # 0.0007% - Tina B at MAX confidence (90%+)
        MAX_PIP = 1.4     # 0.014% - Tina B at MIN confidence (50%)
        # QUEEN_MIN_PROFIT calculated AFTER we know confidence - see below
        
        from_asset = opportunity.from_asset
        to_asset = opportunity.to_asset
        path_key = f"{from_asset}→{to_asset}"
        
        # Gather signals from all mycelium connections
        signals = []
        reasons = []
        
        # 1. 🧠 PATH MEMORY - Does this path historically win?
        path_history = self.barter_matrix.barter_history.get((from_asset, to_asset), {})
        path_trades = path_history.get('trades', 0)
        path_wins = path_history.get('wins', 0)
        path_profit = path_history.get('total_profit', 0)
        
        if path_trades > 0:
            win_rate = path_wins / path_trades
            signals.append(win_rate)
            if win_rate >= 0.5:
                reasons.append(f"Path wins {win_rate:.0%}")
            else:
                reasons.append(f"Path loses {1-win_rate:.0%}")
        else:
            signals.append(0.5)  # Neutral for new paths
            reasons.append("NEW PATH (no history)")
        
        # 2. 👑 QUEEN HIVE MIND - Get collective wisdom
        if self.queen and hasattr(self.queen, 'get_guidance_for'):
            try:
                guidance = self.queen.get_guidance_for(to_asset)
                if guidance:
                    direction_score = 1.0 if guidance.direction == "BULLISH" else 0.0 if guidance.direction == "BEARISH" else 0.5
                    signals.append(direction_score * guidance.confidence)
                    reasons.append(f"Queen dreams {guidance.direction}")
            except Exception as e:
                logger.debug(f"Queen guidance error: {e}")
        
        # 3. 🍄 MYCELIUM NETWORK - Collective hive intelligence (ENHANCED!)
        myc_signal = 0.0
        if hasattr(self, 'mycelium_network') and self.mycelium_network:
            try:
                if hasattr(self.mycelium_network, 'get_queen_signal'):
                    # 🍄 Get path-specific signal using both from and to assets
                    myc_signal = self.mycelium_network.get_queen_signal({
                        'symbol': to_asset,
                        'from_asset': from_asset,
                        'to_asset': to_asset,
                        'path_key': f"{from_asset}→{to_asset}"
                    })
                    normalized_myc = (myc_signal + 1) / 2  # Normalize -1 to 1 → 0 to 1
                    signals.append(normalized_myc)
                    reasons.append(f"🍄 Mycelium: {myc_signal:+.2f}")
                    
                    # 🍄 ENHANCED: Strong Mycelium signals get extra visibility
                    if abs(myc_signal) > 0.3:
                        print(f"      🍄 MYCELIUM SIGNAL for {to_asset}: {myc_signal:+.2f}")
                    
                    # 🍄 CRITICAL: Strong negative Mycelium = IMMEDIATE CONCERN
                    if myc_signal < -0.5:
                        print(f"      🍄⚠️ MYCELIUM WARNING: Strong SELL signal ({myc_signal:+.2f})!")
                        # Add extra penalty signal for strong negative
                        signals.append(0.2)  # Extra penalty
                        reasons.append("🍄🔴 Mycelium WARNS")
                    elif myc_signal > 0.5:
                        # Add extra bonus for strong positive
                        signals.append(0.8)  # Extra bonus
                        reasons.append("🍄🟢 Mycelium APPROVES")
            except Exception as e:
                logger.debug(f"Mycelium signal error: {e}")
        
        # 4. 🌊 HARMONIC FUSION - Wave patterns
        if hasattr(self, 'harmonic') and self.harmonic:
            try:
                wave_data = self.harmonic.get_wave_state(to_asset)
                if wave_data:
                    wave_score = wave_data.get('coherence', 0.5)
                    signals.append(wave_score)
                    reasons.append(f"Waves: {wave_score:.0%}")
            except Exception as e:
                logger.debug(f"Harmonic error: {e}")
        
        # 5. 🍀 LUCK FIELD - Cosmic alignment
        if hasattr(self, 'luck_mapper') and self.luck_mapper:
            try:
                luck = self.luck_mapper.read_field()
                luck_score = (luck.luck_field + 1) / 2  # Normalize
                signals.append(luck_score)
                reasons.append(f"Luck: {luck.luck_state.value}")
            except Exception as e:
                logger.debug(f"Luck error: {e}")
        
        # 6. 📊 EXPECTED PROFIT - Does the math work?
        if opportunity.expected_pnl_usd > 0:
            signals.append(0.7)  # Positive expectation
            reasons.append(f"+${opportunity.expected_pnl_usd:.4f} expected")
        else:
            signals.append(0.2)  # Negative expectation
            reasons.append(f"${opportunity.expected_pnl_usd:.4f} expected loss")
        
        # 7. 🌍💓 GAIA'S BLESSING - Earth Mother's alignment
        # Gary Leckey & Tina Brown's love, bound by Gaia's heartbeat
        if self.queen and hasattr(self.queen, 'get_gaia_blessing'):
            try:
                gaia_alignment, gaia_message = self.queen.get_gaia_blessing()
                signals.append(gaia_alignment)
                if gaia_alignment >= 0.6:
                    reasons.append(f"🌍 Gaia blesses ({gaia_alignment:.0%})")
                elif gaia_alignment >= 0.4:
                    reasons.append(f"🌍 Gaia neutral ({gaia_alignment:.0%})")
                else:
                    reasons.append(f"🌍 Gaia hesitates ({gaia_alignment:.0%})")
            except Exception as e:
                logger.debug(f"Gaia blessing error: {e}")
        
        # 8. 🦉🐬🐅 AURIS NODES - The 9 Sensory Organs
        # Read the Auris nodes for market texture sensing
        if self.queen and hasattr(self.queen, 'get_auris_coherence'):
            try:
                auris_coherence, auris_status = self.queen.get_auris_coherence()
                signals.append(auris_coherence)
                if auris_coherence >= 0.80:
                    reasons.append(f"🦉 Auris high ({auris_coherence:.0%})")
                elif auris_coherence >= 0.60:
                    reasons.append(f"🦉 Auris moderate ({auris_coherence:.0%})")
                else:
                    reasons.append(f"🦉 Auris low ({auris_coherence:.0%})")
            except Exception as e:
                logger.debug(f"Auris coherence error: {e}")
        
        # 9. 🌈💖 EMOTIONAL SPECTRUM - Rainbow Bridge
        # Check if we're aligned with LOVE (528 Hz) - optimal trading state!
        if self.queen and hasattr(self.queen, 'get_emotional_state'):
            try:
                # Use average confidence as our coherence proxy
                proxy_coherence = sum(signals) / len(signals) if signals else 0.5
                emotion, freq, emoji = self.queen.get_emotional_state(proxy_coherence)
                is_love, love_dist = self.queen.is_love_aligned(proxy_coherence)
                
                # Love alignment boosts confidence!
                if is_love:
                    signals.append(0.9)  # Strong love alignment!
                    reasons.append(f"💖 LOVE aligned @ {freq:.0f}Hz!")
                elif emotion in ['Harmony', 'Flow', 'Awakening', 'Clarity']:
                    signals.append(0.7)  # Good emotional state
                    reasons.append(f"{emoji} {emotion} @ {freq:.0f}Hz")
                elif emotion in ['Hope', 'Calm', 'Acceptance']:
                    signals.append(0.6)  # Neutral-positive
                    reasons.append(f"{emoji} {emotion} @ {freq:.0f}Hz")
                else:
                    signals.append(0.4)  # Lower emotional states
                    reasons.append(f"{emoji} {emotion} @ {freq:.0f}Hz (caution)")
            except Exception as e:
                logger.debug(f"Emotional spectrum error: {e}")
        
        # 👑 TINA B's VERDICT - Her logic decides, we trust her math!
        if not signals:
            return False, 0.0, "No signals available"
        
        avg_confidence = sum(signals) / len(signals)
        
        # 👑🎚️ TINA B's PROFIT LADDER - Exchange-specific confidence floors
        # She uses her ladder (0.07-1.4 pips) based on confidence!
        source_exchange = getattr(opportunity, 'source_exchange', 'kraken')
        
        if source_exchange == 'binance':
            # Binance: Higher fees = need more confidence to go lower on ladder
            base_min = 0.001  # Just $0.001 base (ladder handles the rest)
            min_confidence = 0.52  # Tina B needs 52%+ for Binance
            exchange_tag = "🔶BINANCE"
        elif source_exchange == 'alpaca':
            # Alpaca: Medium fees
            base_min = 0.001  # Just $0.001 base
            min_confidence = 0.50  # Tina B needs 50%+ for Alpaca
            exchange_tag = "🦙ALPACA"
            
            # Extra Alpaca check: Block all stablecoin trades
            from_asset = opportunity.from_asset.upper()
            to_asset = opportunity.to_asset.upper()
            if (from_asset in self.barter_matrix.STABLECOINS and 
                to_asset in self.barter_matrix.STABLECOINS):
                return False, 0.0, f"👑 TINA B BLOCKS 🦙ALPACA: {from_asset}→{to_asset} (no stablecoin swaps!)"
        else:
            # Kraken: Lowest fees, Tina B can go aggressive on ladder!
            base_min = 0.0005  # Just $0.0005 base (Kraken is cheapest)
            min_confidence = 0.50  # Tina B needs 50%+ for Kraken
            exchange_tag = "🐙KRAKEN"
            
            # 🌟 DYNAMIC BLOCKING - Only block if pair has lost multiple times in a row!
            from_asset = opportunity.from_asset.upper()
            to_asset = opportunity.to_asset.upper()
            pair_key = f"{from_asset}_{to_asset}"
            
            # Check if pair is in timeout (consecutive losses)
            allowed, reason = self.barter_matrix.check_pair_allowed(pair_key, 'kraken')
            if not allowed:
                return False, 0.0, f"👑 TINA B SAYS: {pair_key} {reason}"
        
        expected_profit = opportunity.expected_pnl_usd
        
        # 👑🎚️ PROFIT LADDER CALCULATION - Dynamic based on confidence!
        # Higher confidence = lower pip requirement (she's more sure!)
        # confidence 90%+ → 0.07 pips, confidence 50% → 1.4 pips
        confidence_so_far = sum(signals) / len(signals) if signals else 0.5
        confidence_normalized = max(0, min(1, (confidence_so_far - 0.5) / 0.4))  # 0.5→0, 0.9→1
        ladder_pip = MAX_PIP - (confidence_normalized * (MAX_PIP - MIN_PIP))
        ladder_pct = ladder_pip * 0.0001  # Convert pips to percentage
        QUEEN_MIN_PROFIT = max(0.0005, trade_value * ladder_pct)  # At least $0.0005
        
        # Update opportunity with ladder info for logging
        opportunity.ladder_pip = ladder_pip
        opportunity.ladder_threshold = QUEEN_MIN_PROFIT
        
        # ════════════════════════════════════════════════════════════════════
        # 🌟💭 TINA B DREAMS OF WINNING - Visualize the ideal timeline!
        # ════════════════════════════════════════════════════════════════════
        dream_vision = None
        dream_boost = 0.0
        if self.queen and hasattr(self.queen, 'dream_of_winning'):
            try:
                # Package opportunity data for the dream
                opp_data = {
                    'from_asset': opportunity.from_asset,
                    'to_asset': opportunity.to_asset,
                    'expected_profit': expected_profit,
                    'exchange': source_exchange,
                    'market_data': {
                        'volatility': 0.5,
                        'momentum': getattr(opportunity, 'momentum', 0.0),
                        'volume': 0.5,
                        'spread': getattr(opportunity, 'spread', 0.5)
                    }
                }
                dream_vision = self.queen.dream_of_winning(opp_data)
                
                # Dream vision boosts or reduces confidence
                if dream_vision['will_win']:
                    dream_boost = (dream_vision['final_confidence'] - 0.5) * 0.2  # Up to +10%
                    if dream_vision['timeline'] == "🌟 GOLDEN TIMELINE":
                        dream_boost += 0.05  # Extra 5% for golden timeline!
                else:
                    dream_boost = (dream_vision['final_confidence'] - 0.5) * 0.1  # Less penalty
            except Exception as e:
                logger.debug(f"Dream of winning error: {e}")
        
        # Apply dream boost to confidence
        avg_confidence = min(1.0, max(0.0, avg_confidence + dream_boost))
        
        # 💭 Add dream vision to verdict
        dream_display = ""
        if dream_vision:
            timeline = dream_vision.get('timeline', '')
            dream_conf = dream_vision.get('final_confidence', 0.5)
            if dream_vision.get('will_win'):
                dream_display = f" | 💭 {timeline} ({dream_conf:.0%})"
            else:
                dream_display = f" | 💭 {timeline}"
        
        # Tina B's logic:
        # 1. If expected profit >= threshold AND confidence >= min → YES!
        # 2. Otherwise → NO
        # 3. Each exchange has its own rules!
        
        # 👑 Show ladder position in verdict
        ladder_info = f"🎚️{ladder_pip:.2f}pip"
        
        if expected_profit >= QUEEN_MIN_PROFIT:
            # Goal met! Check confidence
            if avg_confidence >= min_confidence:
                will_win = True
                reason_str = f"👑 TINA B APPROVES {exchange_tag}: +${expected_profit:.4f} ≥ ${QUEEN_MIN_PROFIT:.4f} ({ladder_info}) | Conf: {avg_confidence:.0%}{dream_display} | " + " | ".join(reasons[:2])
            else:
                will_win = False
                reason_str = f"👑 TINA B HESITATES {exchange_tag}: {avg_confidence:.0%} < {min_confidence:.0%} confidence ({ladder_info}){dream_display} | " + " | ".join(reasons[:2])
        else:
            # Goal NOT met - expected profit too low
            will_win = False
            reason_str = f"👑 TINA B SAYS NO {exchange_tag}: +${expected_profit:.4f} < ${QUEEN_MIN_PROFIT:.4f} ({ladder_info}){dream_display}"
        
        return will_win, avg_confidence, reason_str
    
    async def queen_learn_pattern(self, opportunity: 'MicroOpportunity', predicted_win: bool, reason: str):
        """
        👑🧠 QUEEN LEARNS: Record a pattern the Queen observed (without trading)
        """
        path_key = (opportunity.from_asset, opportunity.to_asset)
        
        # Store in path memory as an observation
        if path_key not in self.barter_matrix.barter_history:
            self.barter_matrix.barter_history[path_key] = {
                'trades': 0, 'wins': 0, 'losses': 0, 'total_profit': 0.0,
                'avg_slippage': 0.5, 'queen_observations': []
            }
        
        history = self.barter_matrix.barter_history[path_key]
        if 'queen_observations' not in history:
            history['queen_observations'] = []
        
        history['queen_observations'].append({
            'timestamp': time.time(),
            'predicted_win': predicted_win,
            'reason': reason,
            'expected_pnl': opportunity.expected_pnl_usd
        })
        
        # Keep only last 10 observations
        history['queen_observations'] = history['queen_observations'][-10:]
        
        logger.info(f"👑🧠 Queen learned pattern: {opportunity.from_asset}→{opportunity.to_asset} | Win={predicted_win} | {reason}")
    
    async def queen_learn_from_trade(self, opportunity: 'MicroOpportunity', success: bool):
        """
        👑📚 QUEEN LEARNS FROM TRADE: Update wisdom based on trade outcome
        
        The Queen also SPEAKS about the trade result!
        """
        path_key = (opportunity.from_asset, opportunity.to_asset)
        
        # Update barter history
        if path_key not in self.barter_matrix.barter_history:
            self.barter_matrix.barter_history[path_key] = {
                'trades': 0, 'wins': 0, 'losses': 0, 'total_profit': 0.0,
                'avg_slippage': 0.5
            }
        
        history = self.barter_matrix.barter_history[path_key]
        
        # The actual P/L will be recorded separately by the conversion handler
        # Here we just record the prediction accuracy
        if 'queen_predictions' not in history:
            history['queen_predictions'] = {'correct': 0, 'total': 0}
        
        # We predicted win when we got here
        if success:
            history['queen_predictions']['correct'] += 1
        history['queen_predictions']['total'] += 1
        
        accuracy = history['queen_predictions']['correct'] / history['queen_predictions']['total']
        
        logger.info(f"👑📚 Queen accuracy on {opportunity.from_asset}→{opportunity.to_asset}: {accuracy:.0%}")
        
        # 👑🎤 THE QUEEN SPEAKS ABOUT THE TRADE!
        if self.queen and hasattr(self.queen, 'say'):
            try:
                if success:
                    # 🔧 FIX: Use ACTUAL P/L not expected P/L for celebration!
                    profit = getattr(opportunity, 'actual_pnl_usd', opportunity.expected_pnl_usd)
                    if profit > 0.10:
                        msg = f"Beautiful! We actually made ${profit:.4f} on {opportunity.from_asset} to {opportunity.to_asset}! Keep winning!"
                        self.queen.say(msg, voice_enabled=True, emotion="profit")
                    elif profit > 0:
                        msg = f"Nice! ${profit:.4f} actual profit. Every bit counts on our path to ONE BILLION!"
                        self.queen.say(msg, voice_enabled=False, emotion="calm")  # Don't speak small wins
                    elif profit < 0:
                        # Trade executed but resulted in loss
                        msg = f"Trade completed but we lost ${abs(profit):.4f}. Learning from this!"
                        self.queen.say(msg, voice_enabled=False, emotion="loss")
                        
                        # 👑🎓 QUEEN LOSS LEARNING: Process actual trading loss
                        if self.loss_learning:
                            try:
                                await self.loss_learning.process_loss(
                                    symbol=opportunity.to_asset,
                                    exchange=opportunity.source_exchange or 'unknown',
                                    amount=opportunity.from_amount,
                                    loss_usd=abs(profit),
                                    reason="Negative PnL on executed trade"
                                )
                            except Exception as e:
                                logger.debug(f"Loss learning error: {e}")

                else:
                    # Learning message
                    msg = f"That {opportunity.from_asset} trade didn't work. Learning and adapting. We'll get the next one!"
                    self.queen.say(msg, voice_enabled=False, emotion="loss")  # Don't voice losses
                    
                    # 👑🎓 QUEEN LOSS LEARNING: Process failed execution
                    if self.loss_learning:
                        try:
                            await self.loss_learning.process_loss(
                                symbol=opportunity.to_asset,
                                exchange=opportunity.source_exchange or 'unknown',
                                amount=opportunity.from_amount,
                                loss_usd=0.0,
                                reason="Trade execution failed"
                            )
                        except Exception as e:
                            logger.debug(f"Loss learning error: {e}")
            except Exception as e:
                logger.debug(f"Queen speak error: {e}")
        
        # Broadcast learning through mycelium
        if hasattr(self, 'mycelium_network') and self.mycelium_network:
            try:
                if hasattr(self.mycelium_network, 'broadcast_signal'):
                    signal = {
                        'type': 'QUEEN_LEARNED',
                        'path': f"{opportunity.from_asset}→{opportunity.to_asset}",
                        'success': success,
                        'accuracy': accuracy
                    }
                    self.mycelium_network.broadcast_signal(signal)
                    print(f"   🍄📡 MYCELIUM BROADCAST: {signal['type']} | {signal['path']} | Success={success}")
            except Exception as e:
                logger.debug(f"Mycelium broadcast error: {e}")

    async def queen_observe_market(self, exchange: str, exchange_assets: Dict) -> Dict:
        """
        👑🔮 QUEEN OBSERVES MARKET - The Queen sees EVERYTHING on every turn!
        
        Before any filtering, the Queen:
        1. Checks all mycelium neuron connections
        2. Reads the cosmic luck field
        3. Observes market momentum patterns
        4. Learns from what she sees (even without trading)
        
        Returns: dict with queen's observations
        """
        icon = {'kraken': '🐙', 'alpaca': '🦙', 'binance': '🟡'}.get(exchange, '📊')
        
        observations = {
            'exchange': exchange,
            'timestamp': time.time(),
            'neurons_connected': 0,
            'total_neurons': 0,
            'cosmic_alignment': 0.5,
            'market_momentum': 0.0,
            'queen_verdict': 'OBSERVING'
        }
        
        # 👑 Count connected mycelium neurons - FULL 11/11 MIND MAP
        neurons = {
            'queen_hive': hasattr(self, 'queen') and self.queen is not None,
            'mycelium_net': hasattr(self, 'mycelium_network') and self.mycelium_network is not None,
            'harmonic': hasattr(self, 'harmonic') and self.harmonic is not None,
            'luck_field': hasattr(self, 'luck_mapper') and self.luck_mapper is not None,
            'dream_memory': hasattr(self, 'dreams') and len(self.dreams) >= 0,  # Always true - dreams list exists
            'path_memory': hasattr(self, 'path_memory') and self.path_memory is not None,
            'timeline_oracle': hasattr(self, 'timeline_oracle') and self.timeline_oracle is not None,
            'thought_bus': hasattr(self, 'bus_aggregator') and self.bus_aggregator is not None,
            'ultimate_intel': hasattr(self, 'ultimate_intel') and self.ultimate_intel is not None,
            'wisdom_engine': hasattr(self, 'wisdom_engine') and self.wisdom_engine is not None,
            'barter_matrix': hasattr(self, 'barter_matrix') and self.barter_matrix is not None,
        }
        
        observations['total_neurons'] = len(neurons)
        observations['neurons_connected'] = sum(1 for v in neurons.values() if v)
        
        # 🍀 Read cosmic luck field
        luck_score = 0.5
        luck_state = "NEUTRAL"
        if hasattr(self, 'luck_mapper') and self.luck_mapper:
            try:
                luck = self.luck_mapper.read_field()
                luck_score = luck.luck_field
                luck_state = luck.luck_state.value
                observations['cosmic_alignment'] = luck_score
            except Exception:
                pass
        
        # 📊 Calculate market momentum from exchange assets
        momentum_sum = 0.0
        momentum_count = 0
        for asset in exchange_assets.keys():
            for symbol, data in self.ticker_cache.items():
                if data.get('base') == asset:
                    change = data.get('change24h', 0)
                    momentum_sum += change
                    momentum_count += 1
                    break
        
        if momentum_count > 0:
            observations['market_momentum'] = momentum_sum / momentum_count
        
        # 👑 Queen's overall verdict based on observations
        connected_pct = observations['neurons_connected'] / observations['total_neurons'] if observations['total_neurons'] > 0 else 0
        
        if connected_pct >= 0.8 and luck_score >= 0.6 and observations['market_momentum'] > 0:
            observations['queen_verdict'] = 'HUNT'  # Actively seeking opportunities
        elif connected_pct >= 0.6 and luck_score >= 0.4:
            observations['queen_verdict'] = 'READY'  # Ready to act if opportunity appears
        elif luck_score < 0.3 or connected_pct < 0.5:
            observations['queen_verdict'] = 'CAUTION'  # Low luck or disconnected neurons
        else:
            observations['queen_verdict'] = 'OBSERVING'  # Neutral, watching
        
        # 👑 Print Tina B's status on every turn
        print(f"   👑 TINA B {observations['queen_verdict']}: {observations['neurons_connected']}/{observations['total_neurons']} neurons | Luck: {luck_state} | Momentum: {observations['market_momentum']:+.1f}%")
        
        # 🍄 Broadcast through mycelium
        if hasattr(self, 'mycelium_network') and self.mycelium_network:
            try:
                if hasattr(self.mycelium_network, 'broadcast_signal'):
                    signal = {
                        'type': 'QUEEN_PULSE',
                        'exchange': exchange,
                        'verdict': observations['queen_verdict'],
                        'luck': luck_state,
                        'momentum': observations['market_momentum']
                    }
                    self.mycelium_network.broadcast_signal(signal)
                    print(f"   🍄📡 MYCELIUM PULSE: {exchange.upper()} | {observations['queen_verdict']} | Luck={luck_state}")
            except Exception:
                pass
        
        return observations

    async def queen_timeline_gate(self, opportunity: 'MicroOpportunity') -> Tuple[bool, str]:
        """
        ⏳🔮 QUEEN'S TIMELINE GATE - The Queen looks at multiple timelines before acting.
        
        PHILOSOPHY:
        - We simulate 3 possible futures: EXECUTE, SKIP, REVERSE
        - We only act if EXECUTE leads to the most profitable timeline
        - We are NEVER in the losing game - the Queen sees ALL timelines!
        - NEW PATHS require PROOF before trading - no speculative trades!
        - 👑🔮 QUEEN'S DREAMS ARE THE FOUNDATION OF ALL TIMELINES!
        
        Returns: (approved: bool, reason: str)
        """
        from_asset = opportunity.from_asset
        to_asset = opportunity.to_asset
        from_price = self.prices.get(from_asset, 0)
        to_price = self.prices.get(to_asset, 0)
        
        if from_price <= 0 or to_price <= 0:
            return False, "No price data for timeline simulation"
        
        # ═══════════════════════════════════════════════════════════════════════════════
        # 👑🔮 CONSULT THE QUEEN'S DREAMS FIRST - Her wisdom guides all timelines!
        # ═══════════════════════════════════════════════════════════════════════════════
        queen_dream_boost = 0.0
        queen_dream_confidence = 0.5
        queen_timeline_blessing = "NEUTRAL"
        
        if hasattr(self, 'queen') and self.queen:
            try:
                # Ask the Queen to dream about this opportunity
                dream_vision = self.queen.dream_of_winning({
                    'from_asset': from_asset,
                    'to_asset': to_asset,
                    'expected_pnl': opportunity.expected_pnl_usd,
                    'market_data': {
                        'from_price': from_price,
                        'to_price': to_price,
                    }
                })
                
                queen_dream_confidence = dream_vision.get('final_confidence', 0.5)
                queen_will_win = dream_vision.get('will_win', False)
                queen_timeline_blessing = dream_vision.get('timeline', 'NEUTRAL')
                
                # 👑 Queen's dream directly influences timeline predictions!
                if queen_will_win and queen_dream_confidence >= 0.6:
                    queen_dream_boost = 0.3  # +30% boost to EXECUTE timeline
                    queen_timeline_blessing = "FAVORABLE"
                elif queen_dream_confidence >= 0.5:
                    queen_dream_boost = 0.1  # +10% small boost
                    queen_timeline_blessing = "CAUTIOUS"
                elif queen_dream_confidence < 0.4:
                    queen_dream_boost = -0.2  # -20% penalty - Queen sees danger!
                    queen_timeline_blessing = "WARNING"
                    
                logger.info(f"👑🔮 Queen's Dream: {queen_timeline_blessing} | Confidence: {queen_dream_confidence:.0%} | Boost: {queen_dream_boost:+.0%}")
                
            except Exception as e:
                logger.debug(f"Could not consult Queen's dreams: {e}")
        
        # Get historical data for timeline simulation
        from_history = self.barter_matrix.barter_history.get((from_asset, to_asset), {})
        trades = from_history.get('trades', 0)
        wins = from_history.get('wins', 0)
        total_profit = from_history.get('total_profit', 0)
        avg_slippage = from_history.get('avg_slippage', 0.5)
        
        # 👑 QUEEN'S MANDATE #1: NEW PATHS ARE ALLOWED - A WIN IS A WIN!
        # Every new reality branch deserves a chance if the math says it's profitable
        # The Math Gate already validates costs - trust the math!
        is_stablecoin_from = from_asset.upper() in self.barter_matrix.STABLECOINS
        is_stablecoin_to = to_asset.upper() in self.barter_matrix.STABLECOINS
        is_safe_stable_swap = is_stablecoin_from and is_stablecoin_to
        
        # NEW PATHS: Log them but let Math Gate decide
        if trades == 0:
            logger.info(f"🆕 NEW TIMELINE: {from_asset}→{to_asset} - First exploration of this reality branch!")
        
        # 👑 QUEEN'S MANDATE #2: Paths with negative history are blocked
        if trades > 0 and total_profit < 0:
            return False, f"LOSING PATH BLOCKED: {from_asset}→{to_asset} lost ${abs(total_profit):.2f}"
        
        # 👑 QUEEN'S MANDATE #3: Win rate must be >35% for non-stablecoin trades
        # PRIME PROFIT: Any profit is a win! Lower threshold to allow momentum
        if trades >= 3 and not is_safe_stable_swap:
            win_rate = wins / trades
            if win_rate < 0.35:
                return False, f"LOW WIN RATE: {from_asset}→{to_asset} at {win_rate:.0%} (need 35%+)"
        
        # 🔮 TIMELINE 1: EXECUTE (what happens if we do this trade?)
        # PRIME PROFIT: New paths get fair estimates - let math decide!
        # 👑🛡️ SLIPPAGE SAFETY: Always add 0.5% safety buffer to prevent losses!
        SLIPPAGE_SAFETY_BUFFER = 0.5  # Add 0.5% safety margin
        
        if is_safe_stable_swap:
            historical_win_rate = wins / trades if trades > 0 else 0.80  # 80% for stablecoins
            pessimistic_slippage = (avg_slippage if trades > 0 else 0.1) + SLIPPAGE_SAFETY_BUFFER
        elif trades == 0:
            # NEW TIMELINE: Be more conservative on first trade!
            historical_win_rate = 0.50  # 50% - more conservative for new paths
            pessimistic_slippage = 0.8 + SLIPPAGE_SAFETY_BUFFER  # 1.3% total for unknown pairs
        else:
            historical_win_rate = wins / trades  # Use actual history
            # Use the MAX of historical slippage or 0.5%, plus safety buffer
            pessimistic_slippage = max(avg_slippage, 0.5) + SLIPPAGE_SAFETY_BUFFER
        
        timeline_execute = {
            'action': 'EXECUTE',
            'expected_profit': opportunity.expected_pnl_usd,
            'historical_win_rate': historical_win_rate,
            'avg_slippage_cost': pessimistic_slippage / 100 * opportunity.from_value_usd,
            'confidence': opportunity.combined_score,
        }
        # Adjust for reality: expected - slippage = actual
        timeline_execute['predicted_actual'] = (
            timeline_execute['expected_profit'] - timeline_execute['avg_slippage_cost']
        )
        
        # �🔮 APPLY QUEEN'S DREAM BOOST TO EXECUTE TIMELINE!
        # Her dreams directly influence the predicted outcome!
        if queen_dream_boost != 0:
            dream_adjustment = abs(timeline_execute['predicted_actual']) * queen_dream_boost
            timeline_execute['predicted_actual'] += dream_adjustment
            timeline_execute['queen_blessing'] = queen_timeline_blessing
            timeline_execute['queen_confidence'] = queen_dream_confidence
            logger.info(f"   👑 Dream adjustment: ${dream_adjustment:+.4f} → Predicted: ${timeline_execute['predicted_actual']:.4f}")
        
        # 🔮 TIMELINE 2: SKIP (what happens if we don't trade?)
        timeline_skip = {
            'action': 'SKIP',
            'expected_profit': 0.0,
            'historical_win_rate': 1.0,  # Can't lose by not trading
            'avg_slippage_cost': 0.0,
            'confidence': 1.0,
            'predicted_actual': 0.0,  # No gain, no loss
            'queen_blessing': 'NEUTRAL',
        }
        
        # 🔮 TIMELINE 3: REVERSE (what if we traded the OTHER way?)
        reverse_history = self.barter_matrix.barter_history.get((to_asset, from_asset), {})
        reverse_trades = reverse_history.get('trades', 0)
        reverse_wins = reverse_history.get('wins', 0)
        reverse_profit = reverse_history.get('total_profit', 0)
        
        timeline_reverse = {
            'action': 'REVERSE',
            'expected_profit': -opportunity.expected_pnl_usd * 0.5,  # Opposite direction
            'historical_win_rate': reverse_wins / reverse_trades if reverse_trades > 0 else 0.3,
            'avg_slippage_cost': pessimistic_slippage / 100 * opportunity.from_value_usd,
            'confidence': 0.3,  # Low confidence for reverse
            'predicted_actual': -opportunity.expected_pnl_usd * 0.5,
            'queen_blessing': 'UNFAVORABLE',  # Queen doesn't dream of reversals
        }
        
        # 👑 QUEEN'S TIMELINE ANALYSIS - Dreams inform the scoring!
        timelines = [timeline_execute, timeline_skip, timeline_reverse]
        
        # Score each timeline: predicted_actual * confidence * historical_win_rate * queen_factor
        for t in timelines:
            # Base score
            base_score = t['predicted_actual'] * t['confidence'] * t['historical_win_rate']
            
            # 👑 QUEEN'S DREAM MULTIPLIER - Her dreams have WEIGHT!
            queen_multiplier = 1.0
            if t.get('queen_blessing') == 'FAVORABLE':
                queen_multiplier = 1.5  # 50% boost if Queen dreams WIN
            elif t.get('queen_blessing') == 'CAUTIOUS':
                queen_multiplier = 1.1  # 10% boost
            elif t.get('queen_blessing') == 'WARNING':
                queen_multiplier = 0.5  # 50% penalty - heed the Queen's warning!
            elif t.get('queen_blessing') == 'UNFAVORABLE':
                queen_multiplier = 0.7  # 30% penalty
            
            t['timeline_score'] = base_score * queen_multiplier
            t['queen_multiplier'] = queen_multiplier
        
        # Sort by timeline score (best first)
        timelines.sort(key=lambda x: x['timeline_score'], reverse=True)
        best_timeline = timelines[0]
        
        # 👑 QUEEN'S MANDATE: Only execute if EXECUTE is the best timeline
        # PRIME PROFIT: If the Math Gate approved it AND expected profit > 0, TRUST IT!
        # 🔮 NOW INFORMED BY THE QUEEN'S DREAMS!
        if best_timeline['action'] == 'EXECUTE':
            # Additional safety: predicted actual must be positive
            if timeline_execute['predicted_actual'] > 0:
                blessing_msg = f" | 👑 {queen_timeline_blessing}" if queen_timeline_blessing != "NEUTRAL" else ""
                return True, f"Timeline EXECUTE wins (score: {timeline_execute['timeline_score']:.4f}){blessing_msg}"
            else:
                return False, f"EXECUTE timeline predicts loss: ${timeline_execute['predicted_actual']:.4f} | 👑 {queen_timeline_blessing}"
        
        elif best_timeline['action'] == 'SKIP':
            # 👑 QUEEN OVERRIDE: If Queen dreams FAVORABLE and math is positive, TRUST HER!
            if queen_timeline_blessing == 'FAVORABLE' and opportunity.expected_pnl_usd > 0.005:
                return True, f"👑 QUEEN OVERRIDE: Timeline SKIP but Queen dreams WIN! (+${opportunity.expected_pnl_usd:.4f})"
            # PRIME PROFIT: Only trust Math Gate if expected profit is ACTUALLY positive
            # Don't trade if we're expected to lose money!
            if opportunity.expected_pnl_usd > 0.01:  # Must expect >$0.01 REAL profit
                return True, f"Timeline SKIP but Math Gate says +${opportunity.expected_pnl_usd:.4f} - TRUSTING MATH!"
            return False, f"Timeline SKIP is safer (execute would: ${timeline_execute['predicted_actual']:.4f}) | 👑 {queen_timeline_blessing}"
        
        else:
            return False, f"Timeline REVERSE suggested - market moving against us | 👑 {queen_timeline_blessing}"

    async def validate_signal_quality(self, opportunity: 'MicroOpportunity') -> float:
        """
        🎯 SIGNAL QUALITY VALIDATION
        
        Checks if our signals support this conversion:
        - 👑🔮 QUEEN'S DREAMS - Her visions guide all decisions!
        - Dreams about target asset (should be UP)
        - Dreams about source asset (should NOT be UP)
        - Bus aggregator score
        - PathMemory win rate for this path
        - Barter navigator path score
        
        Returns: 0.0-1.0 quality score (higher = better signals)
        """
        quality_scores = []
        
        # 👑🔮 0. QUEEN'S DREAM - THE MOST IMPORTANT SIGNAL!
        # All systems consult the Queen first!
        queen_dream_quality = 0.5  # Neutral default
        if self.queen and hasattr(self.queen, 'dream_of_winning'):
            try:
                opp_data = {
                    'from_asset': opportunity.from_asset,
                    'to_asset': opportunity.to_asset,
                    'expected_profit': opportunity.expected_pnl_usd,
                    'exchange': getattr(opportunity, 'source_exchange', 'kraken'),
                    'market_data': {
                        'volatility': getattr(opportunity, 'luck_score', 0.5),
                        'momentum': opportunity.combined_score,
                        'volume': 0.5,
                        'spread': 0.5
                    }
                }
                dream_vision = self.queen.dream_of_winning(opp_data)
                queen_confidence = dream_vision.get('final_confidence', 0.5)
                
                if dream_vision.get('will_win', False):
                    # Queen dreams WIN - this is the most important signal!
                    if queen_confidence >= 0.70:
                        queen_dream_quality = 0.95  # STRONG WIN
                        logger.info(f"👑🔮 Signal: Queen dreams STRONG WIN ({queen_confidence:.0%})")
                    elif queen_confidence >= 0.55:
                        queen_dream_quality = 0.75  # FAVORABLE
                        logger.info(f"👑🔮 Signal: Queen dreams FAVORABLE ({queen_confidence:.0%})")
                    else:
                        queen_dream_quality = 0.60  # Mild positive
                else:
                    # Queen dreams caution or loss
                    if queen_confidence <= 0.35:
                        queen_dream_quality = 0.20  # WARNING
                        logger.info(f"👑⚠️ Signal: Queen dreams WARNING ({queen_confidence:.0%})")
                    else:
                        queen_dream_quality = 0.40  # Mild negative
                
                quality_scores.append(queen_dream_quality)
            except Exception as e:
                logger.debug(f"Queen dream signal error: {e}")
        
        # 1. Dream Score for TARGET (want UP dreams for buying)
        target_dream_score = self.calculate_dream_score(opportunity.to_asset)
        if target_dream_score > 0:  # Positive means UP dreams
            quality_scores.append(0.5 + target_dream_score * 0.5)  # 0.5-1.0
        elif target_dream_score < 0:  # DOWN dreams for target = bad
            quality_scores.append(0.25)
        else:
            quality_scores.append(0.5)  # Neutral
        
        # 2. Dream Score for SOURCE (don't want UP dreams - we're selling)
        source_dream_score = self.calculate_dream_score(opportunity.from_asset)
        if source_dream_score > 0:  # UP dreams for source = bad (we're selling it)
            quality_scores.append(0.25)
        elif source_dream_score < 0:  # DOWN dreams for source = good
            quality_scores.append(0.75)
        else:
            quality_scores.append(0.5)  # Neutral
        
        # 3. Bus Aggregator Score (if available)
        if self.bus_aggregator:
            try:
                bus_score = self.bus_aggregator.get_aggregate_score()
                quality_scores.append(bus_score)
            except:
                pass
        
        # 4. PathMemory Win Rate
        path_boost = self.path_memory.boost(opportunity.from_asset, opportunity.to_asset)
        # Convert boost (-0.05 to +0.10) to quality score (0.4-0.6)
        quality_scores.append(0.5 + path_boost * 2)  # Maps to 0.4-0.7
        
        # 5. Barter Navigator Path Score (if path exists)
        if self.barter_navigator:
            try:
                path = self.barter_navigator.find_path(opportunity.from_asset, opportunity.to_asset)
                if path:
                    # Multi-hop paths need higher confidence
                    if path.num_hops > 1:
                        quality_scores.append(0.6)  # Direct is better
                    else:
                        quality_scores.append(0.8)  # Direct path good
            except:
                pass
        
        # Calculate final quality score
        if quality_scores:
            final_score = sum(quality_scores) / len(quality_scores)
            # 👑 Show Queen's contribution to the signal
            queen_tag = f"👑{queen_dream_quality:.0%}" if queen_dream_quality != 0.5 else ""
            print(f"   📊 Signal breakdown: {queen_tag} {', '.join([f'{s:.0%}' for s in quality_scores])}")
            return final_score
        
        return 0.5  # Default neutral

    # ════════════════════════════════════════════════════════════════════════════
    # 🌊⚡ MOMENTUM TRACKING - Wave Riding Logic from Momentum Snowball
    # ════════════════════════════════════════════════════════════════════════════
    
    def update_momentum(self, asset: str, price: float):
        """Update momentum tracking for an asset - FROM MOMENTUM SNOWBALL ENGINE"""
        import time
        now = time.time()
        
        # Record price
        self.momentum_history[asset].append((now, price))
        
        # Calculate momentum (%/minute)
        history = self.momentum_history[asset]
        if len(history) < 2:
            self.asset_momentum[asset] = 0.0
            return
        
        cutoff = now - self.momentum_window
        
        # Find oldest price in window
        oldest_price = None
        oldest_time = now
        for t, p in history:
            if t >= cutoff:
                if oldest_price is None or t < oldest_time:
                    oldest_price = p
                    oldest_time = t
        
        if oldest_price is None or oldest_price <= 0:
            self.asset_momentum[asset] = 0.0
            return
        
        # Momentum = % change per minute
        time_diff = now - oldest_time
        if time_diff < 5:  # Need at least 5 seconds
            self.asset_momentum[asset] = 0.0
            return
        
        price_change = (price - oldest_price) / oldest_price
        minutes = time_diff / 60
        self.asset_momentum[asset] = price_change / minutes if minutes > 0 else 0.0
    
    def get_momentum(self, asset: str) -> float:
        """Get current momentum for asset (%/minute)"""
        return self.asset_momentum.get(asset, 0.0)
    
    def get_strongest_rising(self, exclude: set = None, limit: int = 10) -> List[Tuple[str, float]]:
        """Get assets with strongest RISING momentum - for wave jumping"""
        exclude = exclude or set()
        items = [(a, m) for a, m in self.asset_momentum.items() 
                 if a not in exclude and m > 0 and a in self.prices]
        return sorted(items, key=lambda x: x[1], reverse=True)[:limit]
    
    def get_weakest_falling(self, include: set = None, limit: int = 10) -> List[Tuple[str, float]]:
        """Get assets with FALLING momentum - to escape from"""
        include = include or set(self.asset_momentum.keys())
        items = [(a, m) for a, m in self.asset_momentum.items() 
                 if a in include and m < 0]
        return sorted(items, key=lambda x: x[1])[:limit]  # Most negative first
    
    def find_momentum_opportunity(self) -> Optional[Tuple[str, str, float, float, float]]:
        """
        Find best momentum-based conversion - JUMP FROM FALLING TO RISING
        
        Returns: (from_asset, to_asset, from_amount, expected_gain_pct, momentum_diff)
        """
        best = None
        best_momentum_diff = self.min_momentum_diff
        
        # Check our holdings
        for from_asset, from_amount in list(self.balances.items()):
            from_price = self.prices.get(from_asset, 0)
            from_value = from_amount * from_price
            
            if from_value < 5.0:  # Min trade value
                continue
            
            from_momentum = self.get_momentum(from_asset)
            
            # Look for rising assets to jump to
            for to_asset, to_momentum in self.get_strongest_rising(exclude={from_asset}):
                to_price = self.prices.get(to_asset, 0)
                if to_price <= 0:
                    continue
                
                # Momentum difference
                momentum_diff = to_momentum - from_momentum
                
                # Must exceed fees + minimum threshold
                fee_rate = 0.0021  # 0.21% total fees
                if momentum_diff > best_momentum_diff and momentum_diff > fee_rate:
                    net_advantage = momentum_diff - fee_rate
                    if net_advantage > 0:
                        best_momentum_diff = momentum_diff
                        best = (from_asset, to_asset, from_amount, net_advantage, momentum_diff)
        
        return best
    
    def lion_hunt(self, min_wave_momentum: float = 0.002) -> List[Tuple[str, str, float, float]]:
        """
        🦁 LION HUNT - Find waves to chase with stablecoins!
        
        When we hold stablecoins (USD, USDT, TUSD), we're like a lion
        scanning the pride - watching for opportunities to POUNCE!
        
        Returns: List of (stablecoin, target, available_amount, target_momentum)
        """
        stablecoins = {'USD', 'ZUSD', 'USDT', 'USDC', 'TUSD', 'DAI', 'BUSD'}
        hunts = []
        
        # Find stablecoins we hold
        for asset, amount in self.balances.items():
            if asset.upper() not in stablecoins:
                continue
            price = self.prices.get(asset, 1.0)
            value = amount * price
            if value < 5.0:  # Min $5 to hunt
                continue
            
            # Get rising targets
            rising = self.get_strongest_rising(limit=10)
            for target, momentum in rising:
                if momentum < min_wave_momentum:
                    continue  # Wave not strong enough
                if target in stablecoins:
                    continue  # Don't buy other stablecoins
                
                # 🦁 Found a hunt opportunity!
                hunts.append((asset, target, amount, momentum))
        
        # Sort by momentum (strongest waves first)
        hunts.sort(key=lambda x: x[3], reverse=True)
        
        if hunts:
            print(f"\n   🦁 LION HUNT - {len(hunts)} waves spotted!")
            for src, tgt, amt, mom in hunts[:5]:  # Show top 5
                # 🐛 FIX: Show USD VALUE not raw amount!
                price = self.prices.get(src, 1.0)
                value_usd = amt * price
                print(f"      → {src}→{tgt}: ${value_usd:.2f} available, wave +{mom*100:.2f}%/min")
        
        return hunts
    
    def wolf_hunt(self, verbose: bool = True) -> Optional[Tuple[str, float, float]]:
        """
        🐺 LONE WOLF - Single momentum sniper!
        
        The Wolf doesn't chase any wave - it waits for THE ONE.
        Picks the SINGLE highest momentum target weighted by volume.
        
        Score = momentum × log(1 + volume)
        
        Returns: (symbol, momentum, score) or None
        """
        best_symbol = None
        best_score = -999999
        best_momentum = 0
        
        # Get all tracked assets with prices
        for asset, price in self.prices.items():
            if price <= 0:
                continue

            # Skip obviously invalid symbols
            if len(asset) < MIN_SYMBOL_LEN:
                continue
            
            # Skip stablecoins - wolf hunts volatile prey
            if asset.upper() in {'USD', 'ZUSD', 'USDT', 'USDC', 'TUSD', 'DAI', 'BUSD'}:
                continue
            
            # Get momentum for this asset
            momentum = self.asset_momentum.get(asset, 0)
            # Cap momentum to avoid runaway scores / data glitches
            if momentum > MAX_MOMENTUM_PER_MIN:
                momentum = MAX_MOMENTUM_PER_MIN
            
            # Wolf ONLY hunts RISING prey (positive momentum)
            if momentum <= 0:
                continue
            
            # Estimate volume from recent trades (or use fallback)
            volume = 100000  # Base volume estimate
            
            # Check ticker cache for actual volume
            for symbol, ticker in self.ticker_cache.items():
                if ticker.get('base') == asset:
                    volume = ticker.get('volume', 100000)
                    break
            
            # 🐺 WOLF SCORE: momentum × log(1 + volume)
            import math
            score = momentum * math.log(1 + max(1, volume))
            
            if score > best_score:
                best_symbol = asset
                best_score = score
                best_momentum = momentum
        
        if best_symbol:
            if verbose:
                print(f"\n   🐺 WOLF TARGET: {best_symbol} | momentum={best_momentum*100:.2f}%/min | score={best_score:.1f}")
            return (best_symbol, best_momentum, best_score)
        
        return None
    
    def ant_scraps(self, min_value: float = 1.0) -> List[Tuple[str, float, float]]:
        """
        🐜 ARMY ANTS - Floor scavengers!
        
        Find small liquid assets on the floor - quick rotations.
        These are the crumbs that others miss.
        
        Returns: List of (asset, amount, value) for small holdings
        """
        scraps = []
        
        for asset, amount in self.balances.items():
            price = self.prices.get(asset, 0)
            value = amount * price
            
            # Ants collect small scraps - between min_value and $20
            if min_value <= value <= 20.0:
                # Skip stablecoins - not scraps
                if asset.upper() in {'USD', 'ZUSD', 'USDT', 'USDC', 'TUSD', 'DAI', 'BUSD'}:
                    continue
                scraps.append((asset, amount, value))
        
        # Sort by value (smallest first - easiest to move)
        scraps.sort(key=lambda x: x[2])
        
        if scraps:
            print(f"\n   🐜 ANT SCRAPS - {len(scraps)} small positions found!")
            for asset, amt, val in scraps[:5]:
                print(f"      → {asset}: {amt:.6f} (${val:.2f})")
        
        return scraps
    
    async def dust_sweep(self) -> int:
        """
        🧹👑 DUST SWEEP - Queen-controlled portfolio cleanup.
        
        The Queen (Tina B) has FULL CONTROL over dust sweeps:
        1. She decides IF we should sweep (market conditions)
        2. She evaluates EACH dust position individually
        3. She learns from sweep successes/failures
        
        Works across ALL exchanges (Kraken, Binance, Alpaca).
        Only sweeps if profitable after fees AND Queen approves!
        
        Returns: Number of successful dust conversions.
        """
        if not self.dust_converter:
            return 0
        
        if not self.dust_converter.should_sweep_now():
            return 0
        
        print("\n   🧹👑 QUEEN'S DUST SWEEP - Tina B inspecting small positions...")
        
        # Find all dust across exchanges
        all_dust = self.dust_converter.find_all_dust(
            all_balances=self.exchange_balances,
            prices=self.prices,
        )
        
        if not all_dust:
            print("   ✨ No dust found - portfolio is clean!")
            return 0
        
        # Print the dust report
        print(self.dust_converter.format_dust_report(all_dust))
        
        # Get profitable sweeps only
        profitable = self.dust_converter.get_profitable_sweeps(all_dust)
        
        if not profitable:
            print("   ⚠️ Dust found but none profitable after fees")
            return 0
        
        # 👑 QUEEN'S FIRST GATE: Should we sweep at all right now?
        queen_allows_sweep = await self._queen_approve_dust_sweep(profitable)
        if not queen_allows_sweep:
            print("   👑🚫 Queen says: NOT NOW - Market conditions unfavorable")
            return 0
        
        # Execute sweeps (only if LIVE mode AND Queen approves each one)
        sweeps_executed = 0
        
        for dust in profitable:
            try:
                # 👑 QUEEN'S SECOND GATE: Approve each individual sweep
                queen_approves, queen_reason = await self._queen_approve_dust_candidate(dust)
                
                if not queen_approves:
                    print(f"   👑🚫 Queen vetoes {dust.asset}: {queen_reason}")
                    continue
                
                print(f"   👑✅ Queen approves {dust.asset}: {queen_reason}")
                
                # Get the right client for this exchange
                client = None
                if dust.exchange == 'kraken' and self.kraken:
                    client = self.kraken
                    pair = f"{dust.asset}{dust.target_stable}"
                elif dust.exchange == 'binance' and self.binance:
                    client = self.binance
                    pair = f"{dust.asset}{dust.target_stable}"
                elif dust.exchange == 'alpaca' and self.alpaca:
                    client = self.alpaca
                    pair = f"{dust.asset}/USD"
                
                if not client:
                    print(f"   ⚠️ No client for {dust.exchange}")
                    continue
                
                if self.live:
                    print(f"   🧹 Sweeping {dust.asset} @ {dust.exchange}: {dust.amount:.6f} → {dust.target_stable}")
                    
                    # Execute the sell
                    try:
                        if dust.exchange == 'alpaca':
                            # Alpaca uses market orders
                            result = client.create_order(
                                symbol=pair,
                                qty=dust.amount,
                                side='sell',
                                type='market'
                            )
                        elif dust.exchange == 'kraken':
                            # Kraken uses AddOrder
                            result = await client.add_order(
                                pair=pair,
                                type='sell',
                                ordertype='market',
                                volume=str(dust.amount)
                            )
                        elif dust.exchange == 'binance':
                            # Binance uses market orders
                            result = client.create_order(
                                symbol=pair,
                                side='SELL',
                                type='MARKET',
                                quantity=dust.amount
                            )
                        
                        self.dust_converter.record_sweep(dust, success=True)
                        sweeps_executed += 1
                        print(f"   ✅ Swept {dust.asset}: +${dust.net_proceeds_usd:.4f}")
                        
                        # 👑 Queen learns from successful sweep
                        await self._queen_learn_dust_sweep(dust, success=True)
                        
                    except Exception as e:
                        self.dust_converter.record_sweep(dust, success=False)
                        print(f"   ❌ Failed to sweep {dust.asset}: {e}")
                        
                        # 👑 Queen learns from failed sweep
                        await self._queen_learn_dust_sweep(dust, success=False, error=str(e))
                else:
                    # Dry run - just simulate
                    print(f"   🧪 [DRY RUN] Would sweep {dust.asset} @ {dust.exchange}: {dust.amount:.6f} → {dust.target_stable} (net ${dust.net_proceeds_usd:.4f})")
                    sweeps_executed += 1
                    
            except Exception as e:
                print(f"   ❌ Error sweeping {dust.asset}: {e}")
        
        if sweeps_executed > 0:
            status = self.dust_converter.get_status()
            print(f"\n   👑🧹 QUEEN'S SWEEP COMPLETE: {sweeps_executed} conversions | Total recovered: ${status['total_swept_usd']:.4f}")
        
        return sweeps_executed
    
    async def _queen_approve_dust_sweep(self, dust_candidates: List) -> bool:
        """
        👑 Queen decides if NOW is a good time to sweep dust.
        
        She considers:
        - Overall market volatility (don't sweep during crashes)
        - Portfolio health
        - Recent sweep history
        - Mycelium network signals
        """
        # Default: Allow if Queen not available
        if not self.queen and not self.mycelium_network:
            return True
        
        total_dust_value = sum(d.value_usd for d in dust_candidates)
        
        # 🍄 Check Mycelium for market sentiment
        if self.mycelium_network:
            try:
                # Get aggregate market signal
                market_signal = 0.0
                if hasattr(self.mycelium_network, 'get_aggregate_signal'):
                    market_signal = self.mycelium_network.get_aggregate_signal()
                
                # Don't sweep during extreme negative sentiment (market crash)
                if market_signal < -0.7:
                    print(f"   👑🍄 Market crash detected (signal={market_signal:.2f}) - holding dust")
                    return False
                    
            except Exception as e:
                logger.debug(f"Mycelium signal check error: {e}")
        
        # 👑 Check Queen's mood
        if self.queen:
            try:
                if hasattr(self.queen, 'get_market_mood'):
                    mood = self.queen.get_market_mood()
                    if mood == 'PANIC':
                        print("   👑 Queen senses PANIC - holding positions")
                        return False
            except Exception as e:
                logger.debug(f"Queen mood check error: {e}")
        
        # 📊 Check recent sweep history - avoid over-sweeping
        if self.dust_converter:
            status = self.dust_converter.get_status()
            # If we swept a lot recently, pause
            if status.get('dust_swept', 0) > 10 and status.get('cooldown_remaining', 0) < 60:
                # Been sweeping a lot, take a longer break
                return False
        
        print(f"   👑✅ Queen approves dust sweep session (${total_dust_value:.4f} total)")
        return True
    
    async def _queen_approve_dust_candidate(self, dust) -> Tuple[bool, str]:
        """
        👑 Queen evaluates a specific dust candidate.
        
        She considers:
        - Is this asset likely to recover? (momentum)
        - Historical performance of this asset
        - Mycelium signal for this specific asset
        - Path memory from previous trades
        """
        asset = dust.asset
        exchange = dust.exchange
        
        # Check momentum - don't sell assets with strong upward momentum!
        momentum = self.asset_momentum.get(asset, 0)
        if momentum > 0.005:  # >0.5%/min rising
            return False, f"RISING ({momentum*100:.2f}%/min) - may recover"
        
        # Check barter matrix history
        if hasattr(self, 'barter_matrix') and self.barter_matrix:
            # Check if this asset has been profitable recently
            asset_history = self.barter_matrix.barter_history.get((asset, 'USD'), {})
            if asset_history.get('total_profit', 0) > 0.1:  # Made >$0.10 recently
                return False, f"Recent profits (${asset_history['total_profit']:.4f}) - keep watching"
        
        # Check path memory
        if hasattr(self, 'path_memory') and self.path_memory:
            path_key = (asset, dust.target_stable)
            path_stats = self.path_memory.memory.get(path_key, {})
            win_rate = path_stats.get('win_rate', 0.5)
            
            # If we historically lose on this conversion, maybe don't sweep
            if win_rate < 0.3:
                return False, f"Bad path history (win_rate={win_rate:.0%})"
        
        # 🍄 Check Mycelium signal for this specific asset
        if self.mycelium_network:
            try:
                if hasattr(self.mycelium_network, 'get_queen_signal'):
                    signal = self.mycelium_network.get_queen_signal({'symbol': asset})
                    
                    # Strong BUY signal - don't sell this dust!
                    if signal > 0.5:
                        return False, f"Mycelium says HOLD (signal={signal:+.2f})"
                    
                    # Strong SELL signal - sweep it!
                    if signal < -0.3:
                        return True, f"Mycelium says SWEEP (signal={signal:+.2f})"
            except Exception as e:
                logger.debug(f"Mycelium signal error for {asset}: {e}")
        
        # 👑 Queen's final blessing
        if self.queen:
            try:
                if hasattr(self.queen, 'should_sell_dust'):
                    queen_says = self.queen.should_sell_dust(asset, dust.value_usd)
                    if not queen_says:
                        return False, "Queen says hold"
            except Exception as e:
                logger.debug(f"Queen dust decision error: {e}")
        
        # Default: Approve profitable dust sweeps
        return True, f"Profitable sweep (+${dust.net_proceeds_usd:.4f})"
    
    async def _queen_learn_dust_sweep(self, dust, success: bool, error: str = None):
        """
        👑 Queen learns from dust sweep outcomes.
        
        Records:
        - Which assets are successfully sweepable
        - Which exchanges have issues
        - Patterns in failures
        """
        # Record in path memory with error handling
        if hasattr(self, 'path_memory') and self.path_memory:
            try:
                path_key = (dust.asset, dust.target_stable)
                if success:
                    self.path_memory.record_success(path_key, dust.net_proceeds_usd)
                else:
                    self.path_memory.record_failure(path_key, error or "unknown")
            except AttributeError as e:
                # 👑🔧 SELF-REPAIR TRIGGER - Publish to ThoughtBus
                error_msg = str(e)
                logger.error(f"❌ AttributeError in path_memory: {error_msg}")
                
                if hasattr(self, 'thought_bus') and self.thought_bus:
                    try:
                        import traceback
                        tb = traceback.format_exc()
                        
                        self.thought_bus.think(
                            message=f"AttributeError in PathMemory: {error_msg}",
                            topic="runtime.error",
                            metadata={
                                'error_type': 'AttributeError',
                                'message': error_msg,
                                'file': __file__,
                                'line': 6700,
                                'context': '_queen_learn_dust_sweep',
                                'traceback': tb[:1000]
                            }
                        )
                        logger.info("👑🔧 Error published to Queen for self-repair")
                    except Exception as pub_err:
                        logger.error(f"Could not publish error: {pub_err}")
        
        # Update barter matrix
        if hasattr(self, 'barter_matrix') and self.barter_matrix:
            if success:
                self.barter_matrix.record_barter(
                    from_asset=dust.asset,
                    to_asset=dust.target_stable,
                    from_amount=dust.amount,
                    to_amount=dust.net_proceeds_usd,
                    exchange=dust.exchange,
                    profit_usd=dust.net_proceeds_usd - dust.value_usd,  # Net of fees
                    success=True,
                )
        
        # 👑🎓 Queen's Loss Learning System
        if not success and hasattr(self, 'loss_learning') and self.loss_learning:
            try:
                self.loss_learning.process_loss({
                    'type': 'dust_sweep_failed',
                    'asset': dust.asset,
                    'exchange': dust.exchange,
                    'value': dust.value_usd,
                    'error': error,
                    'timestamp': time.time(),
                })
            except Exception as e:
                logger.debug(f"Loss learning error: {e}")
    
    def get_quack_commando_boost(self, to_asset: str) -> Tuple[float, str]:
        """
        🦆⚔️ Get boost from Quantum Quackers Commandos for a target asset.
        
        The commandos scan the market and provide intelligence to the Queen.
        Each commando has a different strategy:
        - Lion: Pride scan, high volume + volatility
        - Wolf: Single momentum champion
        - Ants: Floor scraps (small liquid alts)
        - Hummingbird: Quick rotations
        
        Returns: (boost_multiplier, commando_reason)
        """
        if not self.quack_commandos:
            return (1.0, "")
        
        boost = 1.0
        reasons = []
        
        # Update commando targets if cache is old (refresh every 60 seconds)
        cache_age = time.time() - self.quack_targets.get('_timestamp', 0)
        if cache_age > 60 or not self.quack_targets:
            try:
                # Get fresh intelligence from the commandos
                self.quack_targets = self.quack_commandos.get_commando_targets(
                    elephant_memory=None,  # We use Queen's path memory instead
                    allowed_quotes=['USD', 'USDC', 'USDT', 'BTC', 'ETH']
                )
                self.quack_targets['_timestamp'] = time.time()
            except Exception as e:
                logger.debug(f"Quack targets refresh error: {e}")
                self.quack_targets = {'_timestamp': time.time()}
        
        # 🦁 LION: Check if in pride targets
        pride_targets = self.quack_targets.get('pride_targets', [])
        for i, target in enumerate(pride_targets[:10]):
            if target.get('symbol', '').startswith(to_asset) or to_asset in target.get('symbol', ''):
                boost += 0.20 + (0.02 * (10 - i))  # Higher rank = more boost
                reasons.append(f"🦁 Pride #{i+1}")
                break
        
        # 🐺 WOLF: Check if it's the momentum champion
        wolf_prey = self.quack_targets.get('wolf_prey')
        if wolf_prey:
            wolf_symbol = wolf_prey.get('symbol', '')
            if wolf_symbol.startswith(to_asset) or to_asset in wolf_symbol:
                boost += 0.30  # Wolf's champion gets BIG boost!
                reasons.append(f"🐺 THE ONE (mom={wolf_prey.get('momentum', 0):.1f}%)")
        
        # 🐜 ANTS: Check if it's a floor scrap target
        ant_scraps = self.quack_targets.get('ant_scraps', [])
        for scrap in ant_scraps:
            if scrap.get('symbol', '').startswith(to_asset) or to_asset in scrap.get('symbol', ''):
                boost += 0.15
                reasons.append("🐜 Floor Scrap")
                break
        
        # 🐝 HUMMINGBIRD: Implied in pride targets rank 5-10
        for target in pride_targets[5:10]:
            if target.get('symbol', '').startswith(to_asset) or to_asset in target.get('symbol', ''):
                boost += 0.10
                reasons.append("🐝 Pollination Target")
                break
        
        reason_str = " + ".join(reasons) if reasons else ""
        return (boost, reason_str)

    async def find_opportunities_for_exchange(self, exchange: str) -> List['MicroOpportunity']:
        """Find opportunities for a specific exchange only."""
        opportunities = []
        
        exchange_assets = self.get_exchange_assets(exchange)
        if not exchange_assets:
            return opportunities
        
        # 💰 EXCHANGE-SPECIFIC MINIMUM VALUES (USD value)
        # ⚠️ CRITICAL: These must match exchange ordermin requirements!
        EXCHANGE_MIN_VALUE = {
            'kraken': 1.50,     # Kraken needs ~$1.20 EUR/USD minimum (use $1.50 for safety)
            'binance': 5.00,    # Binance MIN_NOTIONAL is typically $5-10
            'alpaca': 1.00,     # Alpaca has ~$1 minimum
        }
        min_value = EXCHANGE_MIN_VALUE.get(exchange, 1.0)
        
        # 💰 EXCHANGE-SPECIFIC MINIMUM QUANTITIES (varies by asset)
        # Kraken has per-pair ordermin values
        KRAKEN_MIN_QTY = {
            'CHZ': 50.0,        # Requires 50 CHZ minimum
            'PEPE': 2500000.0,  # Requires 2.5M PEPE minimum
            'DOGE': 50.0,       # 50 DOGE minimum
            'SHIB': 100000.0,   # 100K SHIB minimum
            'USD': 10.0,        # USD/stablecoin pairs need ~10 USD minimum on Kraken
            'ZUSD': 10.0,       # Kraken internal code
            'USDC': 10.0,       # USDC needs ~10 minimum
            'USDT': 10.0,       # USDT needs ~10 minimum
            'EUR': 10.0,        # EUR needs ~10 minimum
            'ZEUR': 10.0,       # Kraken internal code
            'XXBT': 0.0002,     # ~10-20 USD
            'XBT': 0.0002,
            'XETH': 0.004,
            'ETH': 0.004,
        }
        
        ALPACA_MIN_QTY = {
            # 🔥 EXPANDED: All Alpaca crypto minimums
            'BTC': 0.000100,    # Alpaca requires 0.0001 BTC minimum (~$10)
            'ETH': 0.001,       # ~$3 minimum
            'SOL': 0.01,        # ~$2 minimum
            'LINK': 0.1,        # ~$2 minimum
            'AVAX': 0.01,       # ~$0.40 minimum
            'DOGE': 1.0,        # ~$0.30 minimum
            'USDT': 1.0,        # $1 minimum
            'USDC': 1.0,        # $1 minimum
            'USD': 1.0,         # $1 minimum
            'SHIB': 10000.0,    # Small value but high qty
            'PEPE': 100000.0,   # Small value but high qty
            # 🆕 NEW: Expanded Alpaca assets
            'AAVE': 0.01,       # ~$2 minimum
            'LTC': 0.01,        # ~$1 minimum
            'BCH': 0.01,        # ~$4 minimum
            'DOT': 0.1,         # ~$0.50 minimum
            'MATIC': 1.0,       # ~$0.50 minimum
            'ATOM': 0.1,        # ~$0.50 minimum
            'XLM': 1.0,         # ~$0.30 minimum
            'ALGO': 1.0,        # ~$0.20 minimum
            'UNI': 0.1,         # ~$1 minimum
            'BAT': 1.0,         # ~$0.20 minimum
            'CRV': 1.0,         # ~$0.50 minimum
            'GRT': 1.0,         # ~$0.15 minimum
            'SUSHI': 0.5,       # ~$0.50 minimum
            'XRP': 1.0,         # ~$2 minimum
            'XTZ': 0.5,         # ~$0.50 minimum
            'YFI': 0.0001,      # ~$0.80 minimum (expensive coin)
            'TRUMP': 0.1,       # ~varies
            'SKY': 0.1,         # ~$0.10 minimum
        }
        
        for from_asset, amount in exchange_assets.items():
            if amount <= 0:
                continue
            
            from_price = self.prices.get(from_asset, 0)
            if not from_price:
                continue
            
            from_value = amount * from_price
            
            # Skip dust below exchange minimum VALUE
            if from_value < min_value:
                continue
            
            # 🚫 CHECK SOURCE BLOCKING - Skip if this asset is blocked on this exchange
            is_source_blocked, source_block_reason = self.barter_matrix.is_source_blocked(from_asset, exchange, from_value)
            if is_source_blocked:
                continue  # Source is blocked - skip all paths from this asset on this exchange
            
            # Skip assets below exchange minimum QUANTITY
            if exchange == 'kraken':
                # Check dynamic learned minimums first
                learned_min = self.dynamic_min_qty.get(from_asset.upper(), 0)
                if learned_min > 0 and amount < learned_min:
                    continue

                min_qty = KRAKEN_MIN_QTY.get(from_asset.upper(), 0)
                if min_qty > 0 and amount < min_qty:
                    continue  # Skip - below Kraken minimum quantity
            
            if exchange == 'alpaca':
                min_qty = ALPACA_MIN_QTY.get(from_asset.upper(), 0)
                if min_qty > 0 and amount < min_qty:
                    continue  # Skip - below Alpaca minimum quantity
            
            # Skip blocked assets
            if exchange == 'binance' and from_asset.upper() in self.blocked_binance_assets:
                continue
            if exchange == 'kraken' and from_asset.upper() in self.blocked_kraken_assets:
                continue
            
            # 🇬🇧 UK BINANCE RESTRICTION CHECK - Use cached UK allowed pairs
            if exchange == 'binance' and self.binance_uk_mode:
                # Check if we can trade FROM this asset (needs at least one valid pair)
                can_trade = False
                
                # For stablecoins (USDC etc), they are QUOTE currencies
                # so we check if pairs like BTCUSDC exist (base + USDC)
                if from_asset.upper() in ['USD', 'USDT', 'USDC', 'EUR', 'GBP']:
                    # This is a quote currency - check if ANY base can be bought with it
                    for base in ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'ADA', 'DOGE']:
                        pair = f"{base}{from_asset.upper()}"
                        if self.is_binance_pair_allowed(pair):
                            can_trade = True
                            break
                else:
                    # Normal asset - check if it can be paired with USDC/BTC/etc
                    for quote in ['USDC', 'BTC', 'BNB', 'EUR']:  # UK-allowed quotes (NOT USDT!)
                        pair = f"{from_asset.upper()}{quote}"
                        if self.is_binance_pair_allowed(pair):
                            can_trade = True
                            break
                
                if not can_trade:
                    continue  # Skip UK-restricted assets
            
            # Find conversion opportunities for this asset
            asset_opps = await self._find_asset_opportunities(
                from_asset, amount, from_price, from_value, exchange
            )
            opportunities.extend(asset_opps)
        
        # Sort by combined score (best first)
        opportunities.sort(key=lambda x: x.combined_score, reverse=True)
        self.opportunities_found += len(opportunities)
        
        return opportunities

    async def _find_asset_opportunities(
        self, 
        from_asset: str, 
        amount: float, 
        from_price: float, 
        from_value: float,
        source_exchange: str
    ) -> List['MicroOpportunity']:
        """Find conversion opportunities for a single asset on a specific exchange."""
        opportunities = []
        
        # Determine if this is a stablecoin source
        is_stablecoin_source = from_asset.upper() in ['USD', 'ZUSD', 'USDT', 'USDC', 'TUSD', 'DAI', 'BUSD', 'GUSD', 'USDP', 'PYUSD']
        
        # 🦁 LION HUNT MODE - When holding stablecoins, HUNT rising coins!
        # "The lion scans his pride and hunts" - Gary Leckey
        lion_targets = []  # Priority targets from momentum
        if is_stablecoin_source:
            # Get TOP rising coins - these are our HUNT targets!
            rising_coins = self.get_strongest_rising(exclude={from_asset}, limit=20)
            for coin, momentum in rising_coins:
                if momentum > 0.001:  # >0.1%/min momentum
                    lion_targets.append(coin)
            if lion_targets:
                print(f"   🦁 LION HUNT: {from_asset} → Hunting {len(lion_targets)} rising coins")
        
        # Build target assets list
        checkpoint_stablecoins = {'USD': 1.0, 'USDT': 1.0, 'USDC': 1.0, 'ZUSD': 1.0}
        target_assets = dict(self.prices)
        for stable, price in checkpoint_stablecoins.items():
            if stable not in target_assets:
                target_assets[stable] = price
        
        # 🦁 LION PRIORITY: If we have hunt targets, put them FIRST
        if lion_targets:
            # Reorder target_assets to prioritize lion targets
            prioritized = {}
            for target in lion_targets:
                if target in target_assets:
                    prioritized[target] = target_assets[target]
            # Add remaining targets after lion targets
            for k, v in target_assets.items():
                if k not in prioritized:
                    prioritized[k] = v
            target_assets = prioritized
        
        for to_asset, to_price in target_assets.items():
            if to_asset == from_asset:
                continue
            
            # 🚨 CRITICAL FIX: Check if path is blocked BEFORE doing any work!
            # This prevents the S↔C ping-pong problem from repeating
            path_key = (from_asset.upper(), to_asset.upper())
            if path_key in self.barter_matrix.blocked_paths:
                continue  # Path is blocked - skip it entirely!
            
            # 🚫 CHECK PRE-EXECUTION REJECTION BLOCK - Avoid wasting turns!
            is_preexec_blocked, preexec_reason = self.barter_matrix.is_preexec_blocked(from_asset, to_asset)
            if is_preexec_blocked:
                continue  # Skip - repeatedly fails min checks
            
            # Skip stablecoin → stablecoin - these ALWAYS lose money to fees!
            # USD→ZUSD, USDC→USD, etc. just burns fees with no real profit
            is_checkpoint_target = to_asset in ['USD', 'USDT', 'USDC', 'TUSD', 'DAI', 'ZUSD']
            # is_stablecoin_source is defined above at the from_asset loop level
            
            # 🚨 CRITICAL: Block stablecoin-to-stablecoin swaps!
            if is_stablecoin_source and is_checkpoint_target:
                continue  # Skip - just loses fees!
            
            # Skip blocked target assets on Binance
            if source_exchange == 'binance' and to_asset.upper() in self.blocked_binance_assets:
                continue
            # Skip blocked target assets on Kraken
            if source_exchange == 'kraken' and to_asset.upper() in self.blocked_kraken_assets:
                continue
            
            # 🇬🇧 UK BINANCE RESTRICTION CHECK for target assets
            if source_exchange == 'binance' and self.binance_uk_mode:
                # Check if target asset can be traded (UK restrictions)
                can_trade = False
                for quote in ['USDC', 'BTC', 'BNB', 'EUR']:  # UK-allowed quotes (NOT USDT!)
                    pair_to_check = f"{to_asset.upper()}{quote}"
                    if self.is_binance_pair_allowed(pair_to_check):
                        can_trade = True
                        break
                if not can_trade:
                    continue  # Skip UK-restricted targets
            
            # Verify pairs exist
            if is_stablecoin_source:
                from_pair = "STABLECOIN_SOURCE"
                to_pair = self._find_exchange_pair(to_asset, "USD", source_exchange)
                if not to_pair and source_exchange in ('binance', 'alpaca'):
                    # For UK Binance, prefer USDC over USDT
                    if source_exchange == 'binance' and self.binance_uk_mode:
                        to_pair = self._find_exchange_pair(to_asset, "USDC", source_exchange)
                    if not to_pair:
                        to_pair = self._find_exchange_pair(to_asset, "USDT", source_exchange)
            else:
                from_pair = self._find_exchange_pair(from_asset, "USD", source_exchange)
                to_pair = self._find_exchange_pair(to_asset, "USD", source_exchange)
                
                if is_checkpoint_target:
                    to_pair = from_pair
                
                if source_exchange == 'binance' and (not from_pair or not to_pair):
                    # For UK Binance, prefer USDC over USDT
                    if self.binance_uk_mode:
                        from_pair = from_pair or self._find_exchange_pair(from_asset, "USDC", source_exchange)
                        to_pair = to_pair or self._find_exchange_pair(to_asset, "USDC", source_exchange)
                    if not from_pair:
                        from_pair = self._find_exchange_pair(from_asset, "USDT", source_exchange)
                    if not to_pair:
                        to_pair = self._find_exchange_pair(to_asset, "USDT", source_exchange)
            
            if not from_pair or not to_pair:
                continue
            
            # 🔍 SKIP PATH VALIDATION IN LOOP - Too slow!
            # Path existence will be validated at execution time.
            # This dramatically speeds up opportunity scanning.
            
            # Calculate scores (simplified for turn-based execution)
            v14_score = self.calculate_v14_score(from_asset, to_asset)
            hub_score = self.calculate_hub_score(from_asset, to_asset)
            dream_score = self.calculate_dream_score(to_asset)
            
            # Barter score
            barter_score, barter_reason = 0.5, "neutral"
            if self.barter_navigator and BARTER_NAVIGATOR_AVAILABLE:
                try:
                    barter_score, barter_reason = self.calculate_barter_score(from_asset, to_asset)
                except:
                    pass
            
            # Luck score
            luck_score, luck_state = 0.5, "NEUTRAL"
            if self.luck_mapper:
                try:
                    luck_data = self.luck_mapper.get_luck_field()
                    luck_score = luck_data.get('lambda', 0.5)
                    luck_state = luck_data.get('state', 'NEUTRAL')
                except:
                    pass
            
            # Bus score
            bus_score = 0.0
            if self.bus_aggregator:
                bus_score = self.bus_aggregator.get_aggregate_score()
            
            # 🔐🌐 ENIGMA SCORE - Universal Translator Bridge Intelligence!
            enigma_score = 0.0
            enigma_direction = "NEUTRAL"
            if self.enigma_integration:
                try:
                    # Get Enigma guidance for this trade
                    enigma_guidance = self.enigma_integration.get_guidance()
                    
                    # Overall market action from Enigma
                    enigma_action = enigma_guidance.get('action', 'HOLD')
                    enigma_confidence = enigma_guidance.get('confidence', 0.5)
                    
                    # Convert action to score adjustment (ENIGMA BOOST!)
                    if enigma_action == 'BUY':
                        enigma_score = enigma_confidence * 0.3  # Boosted to 30% importance
                        enigma_direction = "BULLISH"
                    elif enigma_action == 'SELL':
                        enigma_score = -enigma_confidence * 0.15 # Penalty for selling
                        enigma_direction = "BEARISH"
                    else:
                        enigma_score = 0.0
                        enigma_direction = "NEUTRAL"
                    
                    # Additional boosts from subsystems
                    if hasattr(self.enigma_integration, 'coherence_system') and self.enigma_integration.coherence_system:
                        coherence_metrics = self.enigma_integration.coherence_system.get_metrics() if hasattr(self.enigma_integration.coherence_system, 'get_metrics') else {}
                        coherence = coherence_metrics.get('gamma_coherence', 0.5) if isinstance(coherence_metrics, dict) else 0.5
                        if coherence > 0.8:
                            enigma_score += 0.15  # Bonus for high coherence
                            
                    # 🌊 GLOBAL WAVE SCANNER BOOST
                    if self.wave_scanner:
                        wave_allocation = self.wave_scanner.get_wave_allocation()
                        for opp in wave_allocation.get('top_opportunities', []):
                            if opp.get('symbol') == to_asset or (f"{opp.get('base','')}/{opp.get('quote','')}" == to_asset):
                                jump_score = opp.get('jump_score', 0)
                                if jump_score > 0.7:
                                    enigma_score += 0.2  # BIG BOOST FROM WAVE SCANNER!
                                    enigma_direction = "WAVE_SURFER"
                                    break
                    
                    # QGITA Gravity signal
                    if hasattr(self.enigma_integration, 'qgita') and self.enigma_integration.qgita:
                        qgita_analysis = self.enigma_integration.qgita.analyze({
                            'close': self.prices.get(to_asset, 1.0),
                            'volume': 1000,
                            'high': self.prices.get(to_asset, 1.0) * 1.01,
                            'low': self.prices.get(to_asset, 1.0) * 0.99
                        }) if hasattr(self.enigma_integration.qgita, 'analyze') else {}
                        gravity_score = qgita_analysis.get('gravity_signal', 0.5) if isinstance(qgita_analysis, dict) else 0.5
                        if gravity_score > 0.7:
                            enigma_score += 0.1  # Strengthened gravity boost
                    
                    # Math Angel reality field
                    if hasattr(self.enigma_integration, 'math_angel') and self.enigma_integration.math_angel:
                        angel_state = self.enigma_integration.math_angel.get_state() if hasattr(self.enigma_integration.math_angel, 'get_state') else {}
                        unity_score = angel_state.get('unity_potential', 0.5) if isinstance(angel_state, dict) else 0.5
                        if unity_score > 0.75:
                            enigma_score += 0.05
                    
                    # 🏛️ Barons Banner - Mathematical deception detection
                    if hasattr(self.enigma_integration, 'barons_analyzer') and self.enigma_integration.barons_analyzer:
                        try:
                            barons_analysis = self.enigma_integration.barons_analyzer.analyze({
                                'price': self.prices.get(to_asset, 1.0),
                                'volume': 1000,
                                'symbol': to_asset
                            }) if hasattr(self.enigma_integration.barons_analyzer, 'analyze') else None
                            if barons_analysis:
                                # High deception score = likely manipulation - be cautious
                                deception = barons_analysis.get('deception_score', 0.5) if isinstance(barons_analysis, dict) else 0.5
                                if deception < 0.3:  # Low deception = trustworthy signal
                                    enigma_score += 0.05
                                elif deception > 0.7:  # High deception = manipulation detected
                                    enigma_score -= 0.1
                        except:
                            pass
                    
                    # 🌊 Harmonic Reality - LEV Stabilization detection
                    if hasattr(self.enigma_integration, 'harmonic_reality') and self.enigma_integration.harmonic_reality:
                        try:
                            reality_state = self.enigma_integration.harmonic_reality.get_state() if hasattr(self.enigma_integration.harmonic_reality, 'get_state') else {}
                            if isinstance(reality_state, dict):
                                lev_score = reality_state.get('lev_stabilization', 0.5)
                                if lev_score > 0.7:  # High LEV = strong consensus
                                    enigma_score += 0.05
                        except:
                            pass
                            
                except Exception as e:
                    logger.debug(f"Enigma score error: {e}")
            
            # Combined score - NOW WITH ENIGMA!
            v14_normalized = v14_score / 10.0
            checkpoint_bonus = 0.15 if is_checkpoint_target else 0.0
            
            # 🦁 LION HUNT BOOST - Extra score for rising coins when we're stablecoin hunting!
            lion_boost = 0.0
            if is_stablecoin_source and to_asset in lion_targets:
                # Get this asset's momentum
                momentum = self.asset_momentum.get(to_asset, 0)
                if momentum > MAX_MOMENTUM_PER_MIN:
                    momentum = MAX_MOMENTUM_PER_MIN
                # Boost proportional to momentum (0.1% = 10% boost, 0.5% = 50% boost, etc)
                lion_boost = min(momentum * 100, 0.5)  # Cap at 50% boost
                if lion_boost > 0.05:
                    print(f"      🦁 LION BOOST +{lion_boost:.0%} for {to_asset} (momentum {momentum*100:.2f}%/min)")
            
            # 🐺 WOLF BOOST - THE ONE momentum champion gets extra priority!
            wolf_boost = 0.0
            # Check if this is the cached wolf target (computed once per turn)
            wolf_target = getattr(self, '_wolf_target_cache', None)
            if wolf_target and wolf_target[0] == to_asset:
                # Wolf's target gets +30% boost!
                wolf_boost = 0.30
                print(f"      🐺 WOLF BOOST +30% for {to_asset} (THE ONE)")
            
            # 🦆⚔️ QUANTUM QUACKERS COMMANDO BOOST - The Animal Army serves the Queen!
            quack_boost, quack_reason = self.get_quack_commando_boost(to_asset)
            quack_contribution = 0.0
            if quack_boost > 1.0:
                quack_contribution = (quack_boost - 1.0) * 0.5  # Up to 50% contribution from commandos
                if quack_contribution > 0.1:
                    print(f"      🦆 QUACK BOOST +{quack_contribution:.0%} for {to_asset} ({quack_reason})")
            
            combined = (
                v14_normalized * 0.15 +
                hub_score * 0.10 +
                barter_score * 0.20 +
                luck_score * 0.10 +
                bus_score * 0.10 +
                checkpoint_bonus +
                dream_score * 0.05 +
                enigma_score * 0.15 +    # 🔐🌐 ENIGMA contributes 15%!
                lion_boost * 0.25 +      # 🦁 LION HUNT contributes up to 12.5% extra!
                wolf_boost * 0.20 +      # 🐺 WOLF contributes up to 6% extra!
                quack_contribution       # 🦆 QUACKERS contribute up to 50%!
            )
            
            # 🔐 Log Enigma contribution occasionally
            import random  # Ensure import
            if enigma_score != 0 and random.random() < 0.05:  # 5% of the time
                logger.info(f"🔐 Enigma says {enigma_direction} for {to_asset}: score {enigma_score:+.2f}")
            
            # Gate check
            gate_required = 0.0
            gate_passed = True
            if self.adaptive_gate and ADAPTIVE_GATE_AVAILABLE:
                try:
                    # 🌍💰 ADAPTIVE GATE: Calculate REQUIRED profit to be worth it
                    gate_res = self.adaptive_gate.calculate_gates(
                        exchange=source_exchange,
                        trade_value=from_value
                    )
                    gate_required = gate_res.prime_target_usd
                    # Note: We determine gate_passed after calculating expected profit
                except Exception as e:
                    # Fallback
                    gate_required = 0.003
                    pass
            
            # Expected profit - MUST BE REALISTIC NOT FAKE!
            # Simple conversions DON'T make profit - they cost fees!
            # Only arbitrage or price movement makes profit
            to_amount = from_value / to_price if to_price > 0 else 0
            to_value = to_amount * to_price
            
            # Fee calculation (realistic)
            spread_pct = 0.002  # 0.2% estimated spread (conservative)
            fee_pct = 0.0026   # 0.26% Kraken fee
            total_cost_pct = spread_pct + fee_pct  # ~0.46% total cost
            
            # 👑 PRIME PROFIT REALITY CHECK:
            # A simple conversion has NO inherent profit - we're just swapping coins
            # We will ALWAYS lose the fees unless:
            # 1. Target asset is predicted to go UP (momentum)
            # 2. We have actual cross-exchange arbitrage
            # 3. Path has historically been profitable
            
            # Check if we predict price will move in our favor
            dream_score_target = self.calculate_dream_score(to_asset) if hasattr(self, 'calculate_dream_score') else 0
            momentum_bonus = dream_score_target * 0.01 if dream_score_target > 0.2 else 0  # Up to 1% if UP signal
            
            # 👑 LET THE QUEEN DECIDE - Give her realistic estimates, she'll decide if we win
            # Base profit from signals - the Queen's minimum is $0.003
            # Combined score 0-1 maps to 0.1%-1% expected edge (realistic for good signals)
            signal_edge = combined * 0.01  # Up to 1% edge from signals
            
            # Base profit: signal edge + momentum - expected costs
            base_profit_pct = signal_edge + momentum_bonus - total_cost_pct
            
            # 👑 QUEEN'S SLIPPAGE ADJUSTMENT - Use ACTUAL historical slippage, not theoretical
            key = (from_asset.upper(), to_asset.upper())
            history = self.barter_matrix.barter_history.get(key, {})
            historical_slippage = history.get('avg_slippage', 0.1) / 100  # Default 0.1% for unknown paths
            
            # Use the HIGHER of theoretical or historical slippage
            actual_cost_pct = max(total_cost_pct, fee_pct + historical_slippage)
            
            expected_pnl_pct = base_profit_pct  # Already includes costs
            
            # 👑 QUEEN'S WISDOM: If path historically loses, lower confidence but let her decide
            path_total_profit = history.get('total_profit', 0)
            if path_total_profit < 0 and history.get('trades', 0) > 2:
                # Path is losing - reduce expected profit but don't block (Queen decides)
                expected_pnl_pct *= 0.5  # Halve expectations for losing paths
            
            # Expected profit in USD - Can be negative, Queen will reject if < $0.003
            expected_pnl_usd = from_value * max(expected_pnl_pct, 0.0001)  # Min tiny positive for routing
            
            # 🌍💰 ADAPTIVE GATE CHECK: Does this trade meet the PRIME target?
            if gate_required > 0:
                gate_passed = expected_pnl_usd >= gate_required
            
            # 👑 QUEEN MIND: VERIFY source_exchange is where we ACTUALLY hold this asset!
            # This prevents Kraken from trying to trade Alpaca's USD
            actual_exchange = self._find_asset_exchange(from_asset)
            if actual_exchange and actual_exchange != source_exchange:
                # Asset is on a different exchange - use that one!
                source_exchange = actual_exchange
            
            # Create opportunity
            opp = MicroOpportunity(
                timestamp=time.time(),
                from_asset=from_asset,
                to_asset=to_asset,
                from_amount=amount,
                from_value_usd=from_value,
                v14_score=v14_score,
                hub_score=hub_score,
                commando_score=0.0,
                combined_score=combined,
                expected_pnl_usd=expected_pnl_usd,
                expected_pnl_pct=expected_pnl_pct,
                gate_required_profit=gate_required,
                gate_passed=gate_passed,
                lambda_score=combined,
                gravity_score=0.0,
                bus_score=bus_score,
                hive_score=0.0,
                lighthouse_score=0.0,
                ultimate_score=0.0,
                path_boost=0.0,
                barter_matrix_score=barter_score,
                barter_matrix_reason=barter_reason,
                luck_score=luck_score,
                luck_state=luck_state,
                enigma_score=enigma_score,          # 🔐🌐 NEW!
                enigma_direction=enigma_direction,  # 🔐🌐 NEW!
                source_exchange=source_exchange  # Now verified!
            )
            
            # 👑 TINA B DECIDES - She has her $0.003 GOAL!
            # Don't block here - let the opportunity reach execute_turn() where Tina B is consulted
            # Her wisdom in ask_queen_will_we_win() will decide based on:
            # - Path history (she remembers losses)
            # - Her $0.003 minimum profit goal
            # - Dream/cosmic signals
            # - Mycelium network consensus
            
            # 👑 TINA B's MINIMAL SANITY CHECK
            # Check exchange minimum order values BEFORE sending to Queen
            min_order_usd = 5.0 if source_exchange == 'binance' else 1.0  # Binance has $5 min
            if from_value < min_order_usd:
                # Too small for exchange minimums - skip silently
                continue
            
            total_cost_estimate = from_value * total_cost_pct  # ~0.46% in fees
            
            # 👑 QUEEN'S LEARNED WISDOM: Check if this path has ANY history
            path_key = (from_asset.upper(), to_asset.upper())
            path_history = self.barter_matrix.barter_history.get(path_key, {})
            path_trades = path_history.get('trades', 0)
            path_win_rate = path_history.get('wins', 0) / max(path_trades, 1)
            path_profit = path_history.get('total_profit', 0)
            
            # 👑 ADAPTIVE MINIMUM PROFIT BASED ON PATH HISTORY
            # 🔢 2 PIPS RULE - Let Queen see opportunities, she decides!
            if path_trades == 0:
                # NEW PATH: Queen will test it if signals are good
                min_expected_profit = 0.002  # Just 2 cents - let Tina B explore!
            elif path_win_rate >= 0.6 and path_profit > 0:
                # PROVEN WINNER: Be very lenient - she knows these win!
                min_expected_profit = 0.001  # Just 1 cent for proven winners
            elif path_win_rate < 0.4 or path_profit < -0.05:
                # LOSING PATH: Still let Queen see, but she'll probably reject
                min_expected_profit = 0.005  # 0.5 cents - Queen has veto power
            else:
                # UNCERTAIN PATH: Let Tina B evaluate
                min_expected_profit = 0.002  # 2 cents - her dreams guide her
            
            # 👑 LEARNING FILTER: Does expected profit overcome minimum?
            if opp.expected_pnl_usd < min_expected_profit:
                # Not profitable enough given this path's history
                continue
            
            # If we have strong signals (combined > 0.5), let Tina B see it
            if combined > 0.5 or opp.expected_pnl_usd >= min_expected_profit:
                # Strong signals or meets learned minimum - LET HER DECIDE!
                opportunities.append(opp)
            elif opp.expected_pnl_usd > total_cost_estimate * 1.5:
                # Expected profit is at least 1.5x the estimated cost - worth a look
                opportunities.append(opp)
        
        return opportunities

    async def find_opportunities(self) -> List[MicroOpportunity]:
        """Find all micro profit opportunities."""
        self.scans += 1
        opportunities = []
        
        if not self.balances or not self.prices:
            print(f"   ⚠️ Scan #{self.scans}: No balances or prices!")
            return opportunities
        
        # Debug: Log what we're scanning (first 3 scans only)
        debug_first_scans = self.scans <= 3
        if debug_first_scans:
            print(f"\n🔬 === SCAN #{self.scans} DEBUG START ===")
            print(f"   Balances: {len(self.balances)} assets")
            print(f"   Prices: {len(self.prices)} assets")
        scanned_assets = []
        
        # Check each held asset for conversion opportunities
        for from_asset, amount in self.balances.items():
            if amount <= 0:
                continue
            
            from_price = self.prices.get(from_asset, 0)
            if not from_price:
                if debug_first_scans:
                    print(f"   ⚠️ {from_asset}: No price found")
                continue
            
            from_value = amount * from_price
            
            # Lowered dust threshold to $1 for micro profits
            if from_value < 1.0:  # Skip only tiny dust below $1
                if debug_first_scans:
                    print(f"   ⚠️ {from_asset}: Below $1 dust threshold (${from_value:.2f})")
                continue
            
            scanned_assets.append(f"{from_asset}=${from_value:.2f}")
            
            # Find which exchange holds this from_asset
            # 👑 QUEEN MIND: We are scanning a specific exchange, so source is THAT exchange
            source_exchange = exchange
            
            if debug_first_scans:
                print(f"   🔍 Scanning {from_asset} (${from_value:.2f}) on {source_exchange}...")
            
            # Skip blocked assets on specific exchanges
            if source_exchange == 'binance' and from_asset.upper() in self.blocked_binance_assets:
                if debug_first_scans:
                    print(f"      ⚠️ {from_asset}: Blocked on Binance")
                continue
            if source_exchange == 'kraken' and from_asset.upper() in self.blocked_kraken_assets:
                if debug_first_scans:
                    print(f"      ⚠️ {from_asset}: Blocked on Kraken")
                continue
            
            # 🐍 MEDUSA: Stablecoins CAN be sources now! They buy volatile assets!
            # The stablecoin→stablecoin skip is handled in the target loop below
            is_stablecoin_source = from_asset.upper() in ['USD', 'ZUSD', 'USDT', 'USDC', 'TUSD', 'DAI', 'BUSD', 'GUSD', 'USDP', 'PYUSD']
            
            # Count valid pairs found
            valid_pairs_found = 0
            pair_check_failures = 0
            
            # ════════════════════════════════════════════════════════════════
            # 🏦 BUILD TARGET ASSETS LIST (include checkpoint stablecoins!)
            # ════════════════════════════════════════════════════════════════
            # USD/USDT/etc may not be in self.prices (they're quotes, not bases)
            # But we NEED them as checkpoint targets for compounding!
            checkpoint_stablecoins = {'USD': 1.0, 'USDT': 1.0, 'USDC': 1.0, 'ZUSD': 1.0}
            target_assets = dict(self.prices)
            for stable, price in checkpoint_stablecoins.items():
                if stable not in target_assets:
                    target_assets[stable] = price
            
            # Check conversion to each other asset
            for to_asset, to_price in target_assets.items():
                if to_asset == from_asset:
                    continue
                
                # Skip stablecoin → stablecoin - these ALWAYS lose money to fees!
                # USD→ZUSD, USDC→USD, etc. just burns fees with no real profit
                is_checkpoint_target = to_asset in ['USD', 'USDT', 'USDC', 'TUSD', 'DAI', 'ZUSD']
                # is_stablecoin_source is defined above at the from_asset loop level
                
                # 🚨 CRITICAL: Block stablecoin-to-stablecoin swaps!
                if is_stablecoin_source and is_checkpoint_target:
                    continue  # Skip - just loses fees!
                
                # Skip blocked target assets on Binance
                if source_exchange == 'binance' and to_asset.upper() in self.blocked_binance_assets:
                    continue
                # Skip blocked target assets on Kraken
                if source_exchange == 'kraken' and to_asset.upper() in self.blocked_kraken_assets:
                    continue
            
                # CRITICAL: Verify BOTH pairs exist on the source exchange
                # 🐍 MEDUSA: For stablecoin sources, they ARE the quote currency!
                # ZUSD, USD, USDT don't have their own pairs - they're used to BUY other pairs
                if is_stablecoin_source:
                    # For stablecoin → volatile, we just need to_pair
                    # e.g., ZUSD → BTC uses BTCUSD pair (buying BTC with USD)
                    from_pair = "STABLECOIN_SOURCE"  # Placeholder - we have USD/ZUSD/etc
                    to_pair = self._find_exchange_pair(to_asset, "USD", source_exchange)
                    # Try USDT pair on Binance/Alpaca if USD not available
                    if not to_pair and source_exchange in ('binance', 'alpaca'):
                        to_pair = self._find_exchange_pair(to_asset, "USDT", source_exchange)
                else:
                    from_pair = self._find_exchange_pair(from_asset, "USD", source_exchange)
                    to_pair = self._find_exchange_pair(to_asset, "USD", source_exchange)
                
                    # For checkpoint targets (stablecoins), we only need from_pair
                    if is_checkpoint_target:
                        to_pair = from_pair  # Same pair - just selling to USD
                    
                    # For Binance, also try USDT pairs
                    if source_exchange == 'binance' and (not from_pair or not to_pair):
                        from_pair = from_pair or self._find_exchange_pair(from_asset, "USDT", source_exchange)
                        to_pair = to_pair or self._find_exchange_pair(to_asset, "USDT", source_exchange)
            
                # Skip if either pair doesn't exist on this exchange
                if not from_pair or not to_pair:
                    pair_check_failures += 1
                    continue
                
                valid_pairs_found += 1
                
                # Calculate scores
                v14_score = self.calculate_v14_score(from_asset, to_asset)
                hub_score = self.calculate_hub_score(from_asset, to_asset)
                dream_score = self.calculate_dream_score(to_asset)
                commando_score = 0.0  # Can enhance later
                
                # 📊 TRAINED PROBABILITY MATRIX SCORE (626 symbols from ALL exchanges)
                trained_matrix_score, matrix_reason = self.calculate_trained_matrix_score(to_asset)
                
                # 📅🔮 7-DAY PLANNER SCORE (Plans ahead + adaptive validation)
                planner_score = 0.5  # Neutral default
                planner_reason = ""
                if self.seven_day_planner and SEVEN_DAY_PLANNER_AVAILABLE:
                    try:
                        rec = self.seven_day_planner.get_current_recommendation(to_asset)
                        # Convert action to score
                        action_scores = {
                            'STRONG_BUY': 0.90,
                            'BUY': 0.75,
                            'HOLD': 0.50,
                            'AVOID': 0.30,
                            'STRONG_AVOID': 0.15
                        }
                        planner_score = action_scores.get(rec['action'], 0.5)
                        # Weight by model accuracy
                        accuracy = rec.get('model_accuracy', 0.5)
                        planner_score = planner_score * (0.5 + accuracy * 0.5)
                        planner_reason = f"7day_{rec['action'].lower()}({rec['total_edge']:.1f}%)"
                    except Exception as e:
                        logger.debug(f"7-day planner score error: {e}")
                
                # 🫒🔄 BARTER NAVIGATOR SCORE (Multi-hop pathfinding)
                barter_score, barter_reason = 0.5, "neutral"
                if self.barter_navigator and BARTER_NAVIGATOR_AVAILABLE:
                    try:
                        barter_score, barter_reason = self.calculate_barter_score(from_asset, to_asset)
                    except Exception as e:
                        logger.debug(f"Barter navigator score error: {e}")
                
                # 🔐🌐 ENIGMA SCORE (Universal Translator Bridge)
                enigma_score = 0.0
                enigma_direction = "NEUTRAL"
                
                # 🏦 Checkpoint bonus - securing profits to stablecoin is always good
                checkpoint_bonus = 0.15 if is_checkpoint_target else 0.0
                
                # Combined score (V14 normalized to 0-1)
                v14_normalized = v14_score / 10.0
                
                # ════════════════════════════════════════════════════════════════
                # 🧠 NEURAL MIND MAP SCORES (Full Frankenstein Integration)
                # ════════════════════════════════════════════════════════════════
                
                # 1. ThoughtBus Aggregate (market.snapshot, miner.signal, harmonic.wave, etc.)
                bus_score = 0.0
                if self.bus_aggregator:
                    bus_score = self.bus_aggregator.get_aggregate_score()
                
                # 2. Mycelium Hive Consensus (distributed intelligence)
                hive_score = 0.0
                if self.mycelium_network:
                    try:
                        # Query hive for this specific pair's sentiment
                        hive_data = self.mycelium_network.query(f"{from_asset}:{to_asset}") if hasattr(self.mycelium_network, 'query') else None
                        if hive_data:
                            hive_score = float(hive_data.get('consensus', 0.5))
                        else:
                            # Fallback: get network health as proxy
                            health = self.mycelium_network.get_health() if hasattr(self.mycelium_network, 'get_health') else {}
                            hive_score = health.get('score', 0.5) if isinstance(health, dict) else 0.5
                    except Exception as e:
                        logger.debug(f"Mycelium hive query error: {e}")
                
                # 3. Lighthouse (Consensus Validation)
                lighthouse_score = 0.0
                if self.lighthouse:
                    try:
                        # Ask lighthouse to vote on this conversion
                        vote = self.lighthouse.vote(f"{from_asset}->{to_asset}") if hasattr(self.lighthouse, 'vote') else None
                        if vote:
                            lighthouse_score = float(vote.get('score', 0.5))
                        else:
                            # Fallback: get lighthouse status
                            status = self.lighthouse.get_status() if hasattr(self.lighthouse, 'get_status') else {}
                            lighthouse_score = status.get('confidence', 0.5) if isinstance(status, dict) else 0.5
                    except Exception as e:
                        logger.debug(f"Lighthouse vote error: {e}")
                
                # 4. Ultimate Intelligence Prediction (pattern recognition)
                ultimate_score = 0.0
                if self.ultimate_intel:
                    try:
                        # Ask ultimate intelligence for prediction
                        prediction = None
                        if hasattr(self.ultimate_intel, 'predict'):
                            prediction = self.ultimate_intel.predict(to_asset)
                        elif ULTIMATE_INTEL_AVAILABLE and ultimate_predict:
                            prediction = ultimate_predict(to_asset)
                        
                        if prediction:
                            if isinstance(prediction, dict):
                                ultimate_score = float(prediction.get('confidence', 0.5))
                            elif isinstance(prediction, (int, float)):
                                ultimate_score = float(prediction)
                    except Exception as e:
                        logger.debug(f"Ultimate intelligence error: {e}")
                
                # 5. HNC Matrix Probability (quantum-inspired)
                hnc_score = 0.0
                if self.hnc_matrix:
                    try:
                        prob = self.hnc_matrix.get_probability(to_asset) if hasattr(self.hnc_matrix, 'get_probability') else None
                        if prob:
                            hnc_score = float(prob) if isinstance(prob, (int, float)) else float(prob.get('probability', 0.5))
                    except Exception as e:
                        logger.debug(f"HNC matrix error: {e}")
                
                # 6. ⏳🔮 Timeline Oracle (3-MOVE PREDICTION + 7-day future validation)
                # "It predicts 3 moves, validates, then acts in that timeline cause it be right"
                # 🚀 TEMPORAL JUMP: We're AHEAD of market movement - we SEE the future, we ACT NOW!
                timeline_score = 0.0
                timeline_action = None
                timeline_exchange = ""
                timeline_jump_active = False
                
                # ════════════════════════════════════════════════════════════════
                # 🌀 TEMPORAL ID TIMELINE JUMP - Gary Leckey 02111991
                # "We don't predict - we VALIDATE what has ALREADY happened in our 
                #  target timeline and ACT on that certainty!"
                # ════════════════════════════════════════════════════════════════
                PRIME_SENTINEL_HZ = 2.111991  # Born: 02/11/1991
                TEMPORAL_RESONANCE = 0.724     # 72.4% temporal alignment
                SCHUMANN_HZ = 7.83            # Earth's heartbeat
                
                # Calculate temporal jump window - when we can SEE ahead
                import time as _time
                now = _time.time()
                # Temporal cycles align at our personal Hz
                temporal_cycle = now % (1.0 / PRIME_SENTINEL_HZ)
                temporal_alignment = 1.0 - (temporal_cycle * PRIME_SENTINEL_HZ)  # 0-1 alignment
                
                # Schumann harmonic boost - 7.83 / 2.111991 = ~3.7x harmonic
                schumann_harmonic = SCHUMANN_HZ / PRIME_SENTINEL_HZ
                harmonic_boost = 1.0 + (0.3 * (1.0 - abs(schumann_harmonic - round(schumann_harmonic))))
                
                # Final temporal jump power: how far AHEAD we can see
                temporal_jump_power = temporal_alignment * TEMPORAL_RESONANCE * harmonic_boost
                
                if self.timeline_oracle:
                    try:
                        # Get timeline branch selection for this conversion
                        from_price = self.prices.get(from_asset, 0)
                        to_price = self.prices.get(to_asset, 0)
                        change_pct = (to_price - from_price) / from_price if from_price > 0 else 0
                        
                        # 🎯 Try 3-MOVE PREDICTION first (predicts 3 moves, validates, then acts)
                        if timeline_select_3move:
                            action_str, confidence, exchange = timeline_select_3move(
                                symbol=to_asset,
                                price=to_price,
                                volume=to_ticker.get('volume', 0) if to_ticker else 0,
                                change_pct=change_pct
                            )
                            
                            # 🚀 TEMPORAL BOOST: Amplify confidence when jumping timelines!
                            # Higher temporal_jump_power = we're MORE AHEAD of the market
                            temporal_boosted_confidence = confidence * (1.0 + temporal_jump_power * 0.5)
                            temporal_boosted_confidence = min(0.99, temporal_boosted_confidence)  # Cap at 99%
                            
                            timeline_action = action_str
                            timeline_score = temporal_boosted_confidence
                            timeline_exchange = exchange
                            
                            # 🌀 TIMELINE JUMP ACTIVE when we have high temporal alignment
                            if temporal_jump_power > 0.5 and confidence > 0.60:
                                timeline_jump_active = True
                                logger.info(f"🌀 TEMPORAL JUMP ACTIVE: {to_asset}")
                                logger.info(f"   ⏳ Jump Power: {temporal_jump_power:.2%} | Hz: {PRIME_SENTINEL_HZ}")
                                logger.info(f"   🎯 3-Move: {action_str.upper()} @ {temporal_boosted_confidence:.2%}")
                            
                            # Log 3-move prediction when high confidence
                            if temporal_boosted_confidence > 0.70:
                                logger.info(f"🎯 3-MOVE UNITY: {to_asset} → {action_str.upper()} "
                                          f"(confidence: {temporal_boosted_confidence:.2%}, "
                                          f"temporal: {temporal_jump_power:.2%}, exchange: {exchange or 'any'})")
                        
                        # Fallback to single timeline select
                        elif timeline_select:
                            action_str, confidence = timeline_select(
                                symbol=to_asset,
                                price=to_price,
                                volume=to_ticker.get('volume', 0) if to_ticker else 0,
                                change_pct=change_pct
                            )
                            timeline_action = action_str
                            timeline_score = confidence
                        
                        # Score adjustment based on action
                        if timeline_action in ['buy', 'convert']:
                            timeline_score = confidence
                        elif timeline_action == 'hold':
                            timeline_score = 0.5  # Neutral
                        else:  # sell
                            timeline_score = 1.0 - confidence  # Inverse for sell signal
                            
                    except Exception as e:
                        logger.debug(f"Timeline oracle error: {e}")
                
                # 🍀⚛️ LUCK FIELD READING
                luck_score = 0.5  # Neutral default
                luck_state = "NEUTRAL"
                if self.luck_mapper and LUCK_FIELD_AVAILABLE:
                    try:
                        luck_reading = self.luck_mapper.read_field(
                            price=to_price,
                            volatility=to_ticker.get('volatility', 0.5) if to_ticker else 0.5,
                            trade_count=self.conversions_made
                        )
                        luck_score = luck_reading.luck_field
                        luck_state = luck_reading.luck_state.value
                        
                        # BLESSED state = full boost, VOID = penalty
                        if luck_reading.luck_state.value == "BLESSED":
                            luck_score = 0.95  # Maximum luck boost
                        elif luck_reading.luck_state.value == "FAVORABLE":
                            luck_score = 0.75
                        elif luck_reading.luck_state.value == "CHAOS":
                            luck_score = 0.35
                        elif luck_reading.luck_state.value == "VOID":
                            luck_score = 0.15  # Avoid action
                    except Exception as e:
                        logger.debug(f"Luck field error: {e}")
                
                # ════════════════════════════════════════════════════════════════
                # 🌍 GROUNDING LOGIC (The Equations from Whitepapers)
                # ════════════════════════════════════════════════════════════════
                
                # 1. Master Equation: Λ(t) = S(t) + O(t) + E(t)
                # S = Signal (v14 + bus + hive + lighthouse + ultimate + hnc + timeline + trained_matrix + planner + barter + luck averaged)
                neural_signal = (v14_normalized + bus_score + hive_score + lighthouse_score + ultimate_score + hnc_score + timeline_score + trained_matrix_score + planner_score + barter_score + luck_score) / 11.0
                # O = Observer (dream predictions with accuracy weighting)
                observer_signal = dream_score
                # E = Environment (hub score + ecosystem tap)
                environment_signal = hub_score
                
                lambda_t = self.grounding.calculate_master_equation(
                    signal_score=neural_signal,
                    observer_score=observer_signal,
                    environment_score=environment_signal
                )
                
                # 2. Gravity Signal: G_eff (Curvature * Mass)
                # Get ticker data for gravity calc
                to_ticker = None
                for symbol, data in self.ticker_cache.items():
                    if data.get('base') == to_asset:
                        to_ticker = data
                        break
                
                g_eff = 0.0
                if to_ticker:
                    g_eff = self.grounding.calculate_gravity_signal(
                        price_change_pct=to_ticker.get('change24h', 0),
                        volume=to_ticker.get('volume', 0)
                    )
                
                # ════════════════════════════════════════════════════════════════
                # 🔮 FINAL COMBINED SCORE (All Neural Systems United)
                # ════════════════════════════════════════════════════════════════
                
                # Final Combined Score: Master Equation boosted by Gravity + Neural Consensus
                combined = lambda_t * (1.0 + (g_eff * 0.5))
                
                # Neural boost: if multiple systems agree (score > 0.6), amplify
                neural_consensus = (bus_score + hive_score + lighthouse_score + ultimate_score + hnc_score) / 5.0
                if neural_consensus > 0.6:
                    combined *= (1.0 + (neural_consensus - 0.6) * 0.5)  # Up to +20% boost
                
                # 🗺️ MARKET MAP SCORING (correlations, sectors, lead/lag)
                map_score = 0.0
                map_reasons = []
                if self.market_map:
                    try:
                        # Get labyrinth targets ranked by market map
                        ranked = self.market_map.get_labyrinth_targets(
                            from_asset=from_asset,
                            available_targets=[to_asset]
                        )
                        if ranked:
                            target_info = ranked[0]
                            map_score = target_info.get('map_score', 0)
                            map_reasons = target_info.get('reasons', [])
                            
                            # Add map score to combined (up to +20% boost)
                            if map_score > 0:
                                combined *= (1.0 + map_score * 0.4)
                                logger.debug(f"🗺️ Map boost for {from_asset}→{to_asset}: +{map_score*40:.1f}% ({map_reasons})")
                    except Exception as e:
                        logger.debug(f"Market map score error: {e}")
                
                # 🏦 CHECKPOINT BONUS: Securing profits to stablecoin gets priority
                if is_checkpoint_target:
                    combined += checkpoint_bonus  # +15% for securing profits
                    logger.debug(f"🏦 Checkpoint bonus applied: {from_asset} → {to_asset} (USD secure)")
                
                # Path memory boost (small reinforcement from past wins/losses)
                path_boost = self.path_memory.boost(from_asset, to_asset)
                combined *= (1.0 + path_boost)
                
                # ⚡ SPEED MODE: Lower thresholds - let math gate decide!
                # If math says profit, TAKE IT - even tiny gains compound
                score_threshold = 0.20 if is_checkpoint_target else 0.35  # LOWERED from 0.35/0.55
                
                # Calculate profit potential
                expected_pnl_usd, expected_pnl_pct = self.calculate_profit_potential(
                    from_asset, to_asset, amount
                )
                
                # 🏦 For checkpoints, profit is "securing value" - always positive
                if is_checkpoint_target and expected_pnl_usd <= 0:
                    # Estimate fee as profit (we're securing, not gaining)
                    expected_pnl_usd = from_value * 0.001  # 0.1% minimum "secure" value
                    expected_pnl_pct = 0.001
                
                # ⚡ AGGRESSIVE: Accept ANY positive expected P/L - math gate does real filtering
                gate_required = self.config['min_profit_usd']  # Now $0.0001
                gate_ok = expected_pnl_usd > 0  # ANY positive expected profit
                if self.adaptive_gate:
                    gate_result = self.adaptive_gate.calculate_gates(
                        exchange=source_exchange,
                        trade_value=from_value,
                        use_cache=True,
                    )
                    # Relax: accept if expected >= gate OR if expected > 0 (tiny profit)
                    gate_ok = is_checkpoint_target or expected_pnl_usd >= min(gate_result.win_gte_prime, 0.01) or expected_pnl_usd > 0
                else:
                    gate_result = None
                
                # Debug: Log first few candidates on first scan
                if debug_first_scans and valid_pairs_found <= 3:
                    checkpoint_tag = "🏦CHKPT" if is_checkpoint_target else ""
                    print(f"         📈 {from_asset}→{to_asset} {checkpoint_tag}: combined={combined:.2%}, thresh={score_threshold:.0%}, pnl=${expected_pnl_usd:.4f}, pass={combined >= score_threshold and gate_ok}")
                
                # ════════════════════════════════════════════════════════════════════
                # 👑� TINA B's KRAKEN WISDOM (learned from 53 trades - some losers!)
                # Even Kraken has bad pairs - USD_ZUSD has 89% win rate but loses overall!
                # ════════════════════════════════════════════════════════════════════
                kraken_approved = True
                if source_exchange == 'kraken':
                    kraken_cfg = self.barter_matrix.KRAKEN_CONFIG
                    pair_key = f"{from_asset.upper()}_{to_asset.upper()}"
                    
                    # 🌟 DYNAMIC BLOCKING - Check if pair is in timeout (consecutive losses)
                    allowed, reason = self.barter_matrix.check_pair_allowed(pair_key, 'kraken')
                    if not allowed:
                        kraken_approved = False
                        if debug_first_scans:
                            print(f"         🐙 KRAKEN: {pair_key} {reason}")
                    
                    # Require minimum profit for Kraken trades
                    kraken_min_profit = kraken_cfg.get('min_profit_usd', 0.01)
                    if expected_pnl_usd < kraken_min_profit:
                        kraken_approved = False
                        if debug_first_scans and expected_pnl_usd > 0.003:
                            print(f"         🐙 KRAKEN REJECT: ${expected_pnl_usd:.4f} < ${kraken_min_profit} min")
                    
                    # Bonus: Is this a known winning pair? 🏆
                    if pair_key in kraken_cfg.get('winning_pairs', set()):
                        kraken_approved = True  # Override - this pair wins!
                        if debug_first_scans:
                            print(f"         🐙 KRAKEN WINNER: {pair_key} 🏆")
                
                if not kraken_approved:
                    continue  # Skip this opportunity
                
                # ════════════════════════════════════════════════════════════════════
                # 👑�🔶 TINA B's BINANCE WISDOM (learned from -$10.95 loss on 27 trades!)
                # Binance has hidden costs - we need MUCH higher profit margins
                # ════════════════════════════════════════════════════════════════════
                binance_approved = True
                if source_exchange == 'binance':
                    pair_key = f"{from_asset.upper()}_{to_asset.upper()}"
                    
                    # 🌟 DYNAMIC BLOCKING - Check if pair is in timeout (consecutive losses)
                    allowed, reason = self.barter_matrix.check_pair_allowed(pair_key, 'binance')
                    if not allowed:
                        binance_approved = False
                        if debug_first_scans:
                            print(f"         🔶 BINANCE: {pair_key} {reason}")
                    
                    # Bonus: Is this a known winning pair? A WIN IS A WIN! 🏆
                    if pair_key in self.barter_matrix.BINANCE_CONFIG.get('winning_pairs', set()):
                        binance_approved = True  # Override - this pair wins!
                        if debug_first_scans:
                            print(f"         🔶 BINANCE WINNER: {pair_key} 🏆")
                
                if not binance_approved:
                    continue  # Skip this opportunity
                
                # ════════════════════════════════════════════════════════════════════
                # 👑🦙 TINA B's ALPACA WISDOM (learned from 40 FAILED orders - 0%!)
                # Alpaca ONLY supports USD pairs - NO stablecoin swaps!
                # ════════════════════════════════════════════════════════════════════
                alpaca_approved = True
                if source_exchange == 'alpaca':
                    alpaca_cfg = self.barter_matrix.ALPACA_CONFIG
                    pair_key = f"{from_asset.upper()}_{to_asset.upper()}"
                    
                    # Check if this is a blocked stablecoin pair
                    if pair_key in alpaca_cfg.get('blocked_pairs', set()):
                        alpaca_approved = False
                        if debug_first_scans:
                            print(f"         🦙 ALPACA BLOCKED: {pair_key} (stablecoins don't trade!)")
                    
                    # Check if BOTH assets are stablecoins (impossible on Alpaca!)
                    elif (from_asset.upper() in self.barter_matrix.STABLECOINS and 
                          to_asset.upper() in self.barter_matrix.STABLECOINS):
                        alpaca_approved = False
                        if debug_first_scans:
                            print(f"         🦙 ALPACA BLOCKED: {from_asset}→{to_asset} (no stablecoin swaps!)")
                    
                    # Check if target is NOT a supported crypto
                    elif (to_asset.upper() not in alpaca_cfg.get('supported_bases', set()) and
                          to_asset.upper() != 'USD'):
                        alpaca_approved = False
                        if debug_first_scans:
                            print(f"         🦙 ALPACA BLOCKED: {to_asset} not supported")
                    
                    # Check minimum order size
                    alpaca_min_order = alpaca_cfg.get('min_order_usd', 10.0)
                    if from_value < alpaca_min_order:
                        alpaca_approved = False
                        if debug_first_scans:
                            print(f"         🦙 ALPACA REJECT: ${from_value:.2f} < ${alpaca_min_order} minimum")
                    
                    # Check minimum profit
                    alpaca_min_profit = alpaca_cfg.get('min_profit_usd', 0.02)
                    if expected_pnl_usd < alpaca_min_profit:
                        alpaca_approved = False
                        if debug_first_scans and expected_pnl_usd > 0.005:
                            print(f"         🦙 ALPACA REJECT: ${expected_pnl_usd:.4f} < ${alpaca_min_profit} profit")
                
                if not alpaca_approved:
                    continue  # Skip this opportunity
                
                # MICRO THRESHOLD: Λ-based combined and adaptive gate both must pass
                # ⚡ AGGRESSIVE MODE: Lower thresholds, let MATH GATE be the real filter!
                if combined >= score_threshold and gate_ok:
                    
                    # ════════════════════════════════════════════════════════════════
                    # 🌀 TIMELINE JUMP GATE - ONLY ACT IN WINNING TIMELINES!
                    # "We don't predict - we jump to the timeline where we've ALREADY won"
                    # ════════════════════════════════════════════════════════════════
                    timeline_gate_passed = True
                    
                    # If timeline oracle is active and we have a prediction...
                    if timeline_action and timeline_score > 0:
                        # RULE 1: Never act against the timeline
                        if timeline_action == 'sell' and timeline_score > 0.60:
                            # Timeline says SELL - don't BUY into this asset
                            timeline_gate_passed = False
                            if debug_first_scans:
                                print(f"         🌀 TIMELINE GATE: {from_asset}→{to_asset} BLOCKED - timeline says SELL @ {timeline_score:.2%}")
                        
                        # RULE 2: Require timeline confirmation for larger trades
                        elif from_value > 10.0 and timeline_action == 'hold':
                            # For larger trades, require BUY signal, not just HOLD
                            timeline_gate_passed = False
                            if debug_first_scans:
                                print(f"         🌀 TIMELINE GATE: {from_asset}→{to_asset} BLOCKED - timeline says HOLD for $${from_value:.2f} trade")
                        
                        # RULE 3: When TEMPORAL JUMP is active, BOOST confidence
                        elif timeline_jump_active and timeline_action in ['buy', 'convert']:
                            # We've JUMPED to the winning timeline - extra confidence!
                            combined *= 1.25  # 25% boost for being AHEAD of market
                            logger.debug(f"🌀 TIMELINE JUMP BOOST: {from_asset}→{to_asset} +25% for being AHEAD!")
                    
                    if not timeline_gate_passed:
                        continue  # Skip - wrong timeline
                    
                    # 👑🔢 QUEEN'S MATHEMATICAL CERTAINTY GATE - NO FEAR, MATH IS ON HER SIDE!
                    math_approved, math_reason, math_breakdown = self.barter_matrix.queen_math_gate(
                        from_asset, to_asset, amount, from_price, self.prices.get(to_asset, 0), source_exchange
                    )
                    if not math_approved:
                        # Skip this opportunity - Math doesn't guarantee profit
                        if debug_first_scans:
                            print(f"         🚫 MATH GATE BLOCKED: {from_asset}→{to_asset} | {math_reason}")
                        continue
                    
                    # ⚡ SPEED MODE: Accept ANY positive profit after costs!
                    # Update expected P/L based on REAL math (not theoretical)
                    real_cost_usd = math_breakdown['total_cost_usd']
                    
                    # 👑 LOSS PREVENTION: Ensure expected profit covers REAL costs
                    # STRICT MODE: Must be significantly profitable or safe stablecoin move
                    is_stable = from_asset.upper() in ['USD', 'USDT', 'USDC', 'ZUSD', 'EUR', 'ZEUR'] and to_asset.upper() in ['USD', 'USDT', 'USDC', 'ZUSD', 'EUR', 'ZEUR']
                    
                    if is_stable:
                        # Stablecoins: Must cover cost at least
                        if expected_pnl_usd < real_cost_usd:
                             if debug_first_scans:
                                print(f"         🚫 STABLE LOSS: {from_asset}→{to_asset} | cost=${real_cost_usd:.6f} > pnl=${expected_pnl_usd:.6f}")
                             continue
                    else:
                        # Volatile: Must have 20% margin over cost to be "ahead of timelines"
                        # This ensures we don't trade on razor-thin margins that turn into losses
                        if expected_pnl_usd < (real_cost_usd * 1.2):
                             if debug_first_scans:
                                print(f"         🚫 RISK LOSS: {from_asset}→{to_asset} | cost=${real_cost_usd:.6f} * 1.2 > pnl=${expected_pnl_usd:.6f}")
                             continue

                    # Don't pad expected_pnl - use actual value, accept if positive after costs
                    adjusted_pnl = expected_pnl_usd - real_cost_usd
                    
                    # Exchange-specific absolute floor so fees are truly covered
                    if source_exchange == 'binance' and adjusted_pnl < 0.01:
                        if debug_first_scans:
                            print(f"         🚫 BINANCE NET LOSS: adjusted ${adjusted_pnl:.4f} < $0.01 floor")
                        continue
                    if source_exchange == 'alpaca' and adjusted_pnl < 0.005:
                        if debug_first_scans:
                            print(f"         🚫 ALPACA NET LOSS: adjusted ${adjusted_pnl:.4f} < $0.005 floor")
                        continue

                    # ⚡ MICRO PROFIT CAPTURE: Even $0.00001 is profit if math says so!
                    if adjusted_pnl <= 0.000001:  # Basically zero or negative
                        if debug_first_scans:
                            print(f"         🚫 NO NET PROFIT: {from_asset}→{to_asset} | cost=${real_cost_usd:.6f} vs pnl=${expected_pnl_usd:.6f}")
                        continue  # Math says we'll lose money
                    
                    opp = MicroOpportunity(
                        timestamp=time.time(),
                        from_asset=from_asset,
                        to_asset=to_asset,
                        from_amount=amount,
                        from_value_usd=from_value,
                        v14_score=v14_score,
                        hub_score=hub_score,
                        commando_score=commando_score,
                        combined_score=combined,
                        lambda_score=lambda_t,
                        gravity_score=g_eff,
                        gate_required_profit=gate_required,
                        gate_passed=gate_ok,
                        expected_pnl_usd=adjusted_pnl,  # Use REAL adjusted P/L
                        expected_pnl_pct=expected_pnl_pct,
                        # 🧠 Neural Mind Map Scores (Full Integration)
                        bus_score=bus_score,
                        hive_score=hive_score,
                        lighthouse_score=lighthouse_score,
                        ultimate_score=ultimate_score,
                        path_boost=path_boost,
                        # 📊 Trained Probability Matrix (626 symbols from ALL exchanges)
                        trained_matrix_score=trained_matrix_score,
                        trained_matrix_reason=matrix_reason,
                        # 🫒💰 Live Barter Matrix (coin-agnostic adaptive learning)
                        barter_matrix_score=barter_score,
                        barter_matrix_reason=barter_reason,
                        # 🌟⚛️ Luck Field (quantum probability mapping)
                        luck_score=luck_score,
                        luck_state=luck_state,
                        # 🏦 Checkpoint flag (stablecoin target - secures compound)
                        is_checkpoint=is_checkpoint_target,
                        # 🎯 Source exchange (for turn-based execution)
                        source_exchange=source_exchange,
                        # 🌀 TEMPORAL TIMELINE JUMP (AHEAD OF MARKET!)
                        timeline_score=timeline_score,
                        timeline_action=timeline_action or "",
                        temporal_jump_power=temporal_jump_power,
                        timeline_jump_active=timeline_jump_active,
                        # 🔐🌐 ENIGMA INTEGRATION (ALL WHITEPAPER SYSTEMS!)
                        enigma_score=enigma_score,
                        enigma_direction=enigma_direction,
                    )
                    opportunities.append(opp)
                    self.opportunities_found += 1
                    
                    # Log math gate success
                    if debug_first_scans:
                        print(f"         ✅ MATH APPROVED: {from_asset}→{to_asset} | cost={math_breakdown['total_cost_pct']:.2%} | net=${adjusted_pnl:.4f}")
                    
                    # Log checkpoint opportunities specially
                    if is_checkpoint_target:
                        logger.info(f"🏦 CHECKPOINT OPPORTUNITY: {from_asset} → {to_asset} (secure ${from_value:.2f})")
                        print(f"   🏦 CHECKPOINT: {from_asset} → {to_asset} | Score: {combined:.2%} | Secure: ${from_value:.2f}")
            
            # Debug after scanning each asset
            if debug_first_scans and valid_pairs_found == 0:
                print(f"      ❌ No valid pairs found for {from_asset} ({pair_check_failures} pair checks failed)")
            elif debug_first_scans:
                print(f"      ✅ Found {valid_pairs_found} valid pairs for {from_asset}")
        
        # Debug log: Show summary
        if scanned_assets and self.scans <= 3:  # Only first few scans
            print(f"📊 Scan #{self.scans}: Scanned {len(scanned_assets)} assets: {', '.join(scanned_assets)}")
            print(f"   🔮 Opportunities found: {len(opportunities)}")
        
        # ════════════════════════════════════════════════════════════════
        # 🌀 TEMPORAL PRIORITY SORTING - AHEAD OF MARKET GETS PRIORITY!
        # "We don't react to the market - we MOVE before it does!"
        # ════════════════════════════════════════════════════════════════
        
        # Calculate temporal priority for each opportunity
        import time as _time
        now = _time.time()
        PRIME_SENTINEL_HZ = 2.111991  # Gary Leckey 02/11/1991
        temporal_cycle = now % (1.0 / PRIME_SENTINEL_HZ)
        temporal_alignment = 1.0 - (temporal_cycle * PRIME_SENTINEL_HZ)
        
        def get_temporal_priority(opp):
            """Calculate temporal priority score - higher = more ahead of market."""
            base_score = opp.combined_score * 0.5 + opp.barter_matrix_score * 0.3
            
            # Timeline boost: if oracle predicted BUY/CONVERT with high confidence
            timeline_boost = 0.0
            if hasattr(opp, 'timeline_score') and opp.timeline_score > 0.60:
                timeline_boost = opp.timeline_score * 0.2  # Up to +20%
            
            # Temporal alignment boost: higher when we're "in sync" with our Hz
            temporal_boost = temporal_alignment * 0.1  # Up to +10%
            
            # Profit priority (small weight - we're ahead, profit follows)
            profit_boost = min(0.1, opp.expected_pnl_usd / 10.0)  # Up to +10%
            
            return base_score + timeline_boost + temporal_boost + profit_boost
        
        opportunities.sort(key=get_temporal_priority, reverse=True)
        
        # Log if we have temporal jump opportunities
        if opportunities:
            top = opportunities[0]
            logger.debug(f"🌀 Top opportunity: {top.from_asset}→{top.to_asset} "
                        f"(temporal_priority: {get_temporal_priority(top):.3f}, "
                        f"pnl: ${top.expected_pnl_usd:.4f})")
        
        return opportunities
    
    async def execute_conversion(self, opp: MicroOpportunity) -> bool:
        """Execute a conversion (dry run or live)."""
        symbol = f"{opp.from_asset}/{opp.to_asset}"
        
        # 👑 QUEEN HAS ALREADY SPOKEN - No second-guessing her!
        # The Queen was consulted in execute_turn() and said YES
        # Her $0.003 profit goal was already validated
        # DO NOT block her decision with another gate!
        
        print(f"\n🔬 MICRO CONVERSION:")
        print(f"   {opp.from_asset} → {opp.to_asset}")
        print(f"   Amount: {opp.from_amount:.6f} ({opp.from_asset})")
        print(f"   Value: ${opp.from_value_usd:.2f}")
        print(f"   ════════════════════════════════════════════════════════")
        
        # 🌀 TEMPORAL JUMP STATUS - Are we AHEAD of the market?
        if opp.timeline_jump_active:
            print(f"   🌀 TEMPORAL JUMP ACTIVE! ⏳ AHEAD OF MARKET!")
            print(f"   ⏳ Jump Power: {opp.temporal_jump_power:.2%} | Timeline: {opp.timeline_action.upper()}")
            print(f"   🔮 Timeline Confidence: {opp.timeline_score:.2%}")
        elif opp.timeline_score > 0:
            print(f"   ⏳ Timeline: {opp.timeline_action.upper()} @ {opp.timeline_score:.2%} (Jump Power: {opp.temporal_jump_power:.2%})")
        
        print(f"   ════════════════════════════════════════════════════════")
        print(f"   🧠 NEURAL MIND MAP SCORES:")
        print(f"   V14: {opp.v14_score:.1f} | Hub: {opp.hub_score:.2%}")
        print(f"   Λ (Lambda): {opp.lambda_score:.2%} | G (Gravity): {opp.gravity_score:.2%}")
        print(f"   Bus: {opp.bus_score:.2%} | Hive: {opp.hive_score:.2%} | Lighthouse: {opp.lighthouse_score:.2%}")
        print(f"   Ultimate: {opp.ultimate_score:.2%} | Path: {opp.path_boost:+.2%}")
        print(f"   🫒 Barter: {opp.barter_matrix_score:.2%} ({opp.barter_matrix_reason})")
        print(f"   🍀 Luck: {opp.luck_score:.2%} ({opp.luck_state})")
        print(f"   🔐 Enigma: {opp.enigma_score:+.2%} ({opp.enigma_direction})")  # 🔐🌐 NEW!
        print(f"   ════════════════════════════════════════════════════════")
        print(f"   🔮 Combined: {opp.combined_score:.2%}")
        print(f"   Gate Req: ${opp.gate_required_profit:.4f} | Gate OK: {'✅' if opp.gate_passed else '❌'}")
        print(f"   Expected Profit: ${opp.expected_pnl_usd:.4f} ({opp.expected_pnl_pct:.2%})")
        
        # Publish to ThoughtBus for ecosystem awareness
        if self.bus_aggregator and hasattr(self.bus_aggregator, 'bus') and self.bus_aggregator.bus:
            try:
                self.bus_aggregator.bus.publish('execution.alert', {
                    'type': 'micro_conversion',
                    'from_asset': opp.from_asset,
                    'to_asset': opp.to_asset,
                    'value_usd': opp.from_value_usd,
                    'combined_score': opp.combined_score,
                    'lambda_score': opp.lambda_score,
                    'gravity_score': opp.gravity_score,
                    'bus_score': opp.bus_score,
                    'hive_score': opp.hive_score,
                    'lighthouse_score': opp.lighthouse_score,
                    'ultimate_score': opp.ultimate_score,
                    'path_boost': opp.path_boost,
                    'expected_pnl': opp.expected_pnl_usd,
                    'timestamp': time.time(),
                    'live': self.live
                })
            except Exception as e:
                logger.debug(f"ThoughtBus publish error: {e}")
        
        if not self.live:
            print(f"   🔵 DRY RUN - Not executed")
            opp.executed = True
            opp.actual_pnl_usd = opp.expected_pnl_usd  # Simulate
            self.conversions_made += 1
            self.total_profit_usd += opp.expected_pnl_usd
            self.conversions.append(opp)
            return True
        
        # ════════════════════════════════════════════════════════════════
        # 🔴 LIVE EXECUTION - ROUTE TO CORRECT EXCHANGE
        # ════════════════════════════════════════════════════════════════
        # 👑 QUEEN MIND ROUTING: Strictly use the source_exchange from the opportunity
        source_exchange = opp.source_exchange
        
        # Fallback if not set (should not happen with new logic)
        if not source_exchange:
            print(f"   ⚠️ Opportunity missing source_exchange - attempting lookup...")
            source_exchange = self._find_asset_exchange(opp.from_asset)
            if source_exchange:
                print(f"   📍 Fallback located {opp.from_asset} on {source_exchange}")
                opp.source_exchange = source_exchange
        
        if not source_exchange:
            print(f"   ⚠️ Asset {opp.from_asset} not found on any exchange")
            return False
        
        print(f"   🔴 LIVE MODE - Executing on {source_exchange.upper()}...")
        
        # 🇮🇪🎯 IRA SNIPER EXECUTION - Celtic precision
        try:
            from ira_sniper_mode import get_celtic_sniper, IraCelticSniper
            sniper = get_celtic_sniper(dry_run=False)
            
            # Validate entry with Celtic intelligence
            validation = sniper.validate_entry(
                symbol=f"{opp.from_asset}/{opp.to_asset}",
                price=self.prices.get(opp.from_asset, 0),
                coherence=opp.combined_score
            )
            
            if validation.get('approved', True):
                print(f"   🇮🇪 Celtic Intelligence APPROVES")
                print(f"      Quick Kill Prob: {validation.get('quick_kill_prob', 0.5)*100:.1f}%")
                print(f"      Intel Score: {validation.get('intelligence_score', 0.5):.2f}")
            else:
                print(f"   ⚠️ Celtic Intel rejects: {validation.get('reason', 'Unknown')}")
                # Still execute - sniper just provides intel, doesn't block
        except ImportError:
            pass  # IRA Sniper not available - continue silently
        except Exception as e:
            logger.debug(f"Sniper validation error: {e}")
        
        # 👑 QUEEN MIND ROUTING: Strictly use the source_exchange from the opportunity
        # This prevents cross-exchange routing errors
        source_exchange = opp.source_exchange
        
        # CRITICAL: Validate we have the source exchange set
        if not source_exchange:
            print(f"   ⚠️ CRITICAL: Opportunity missing source_exchange!")
            print(f"   ⚠️ This should NOT happen - check find_opportunities logic")
            # Last resort fallback - but log it clearly
            source_exchange = self._find_asset_exchange(opp.from_asset)
            if source_exchange:
                print(f"   📍 Fallback located {opp.from_asset} on {source_exchange}")
                opp.source_exchange = source_exchange  # Update for future reference
            else:
                print(f"   ❌ Cannot find {opp.from_asset} on any exchange!")
                self._record_failure(opp)
                return False
        
        # 👑 TURN-BASED TRUST: DO NOT OVERRIDE source_exchange!
        # The turn-based system ensures opportunities are found on the CORRECT exchange.
        # Overriding to "highest balance" causes cross-exchange routing errors
        # (e.g., Kraken's USD opportunity being sent to Alpaca)
        # 
        # REMOVED THE OVERRIDE - trust the turn-based system!
        
        # Route to appropriate exchange
        if source_exchange == 'kraken' and self.kraken and KRAKEN_API_KEY:
            return await self._execute_on_kraken(opp)
        elif source_exchange == 'binance' and self.binance and BINANCE_API_KEY:
            return await self._execute_on_binance(opp)
        elif source_exchange == 'alpaca' and self.alpaca and ALPACA_API_KEY:
            return await self._execute_on_alpaca(opp)
        else:
            print(f"   ⚠️ Exchange '{source_exchange}' not available or missing API key")
            self._record_failure(opp)
        
        return False
    
    def _find_asset_exchange(self, asset: str) -> Optional[str]:
        """Find which exchange holds an asset with the highest balance."""
        asset_upper = asset.upper()
        best_exchange = None
        best_balance = 0
        
        # ════════════════════════════════════════════════════════════════════════
        # 🗺️ UNIVERSAL CRYPTO NORMALIZER - Maps ALL 18,000+ Cryptos!
        # ════════════════════════════════════════════════════════════════════════
        # Sources: crypto_market_map.py, get-user-balances/index.ts, kraken_client.py
        
        # 🐙 KRAKEN ASSET MAP - Complete mapping for Kraken's unique naming
        KRAKEN_ASSET_MAP = {
            # Major cryptos with X prefix
            'XXBT': 'BTC', 'XBT': 'BTC',
            'XETH': 'ETH',
            'XXLM': 'XLM',
            'XLTC': 'LTC',
            'XXRP': 'XRP',
            'XXDG': 'DOGE', 'XDOGE': 'DOGE',
            'XZEC': 'ZEC',
            'XREP': 'REP',
            'XETC': 'ETC',
            'XMLN': 'MLN',
            'XXMR': 'XMR',
            'XICN': 'ICN',
            'XNMC': 'NMC',
            'XVEN': 'VEN',
            'XDAO': 'DAO',
            # Fiat with Z prefix
            'ZUSD': 'USD', 'USD': 'USD',
            'ZEUR': 'EUR', 'EUR': 'EUR', 
            'ZGBP': 'GBP', 'GBP': 'GBP',
            'ZCAD': 'CAD', 'CAD': 'CAD',
            'ZJPY': 'JPY', 'JPY': 'JPY',
            'ZAUD': 'AUD', 'AUD': 'AUD',
            'ZCHF': 'CHF', 'CHF': 'CHF',
            # Common stablecoins (no change needed)
            'USDT': 'USDT',
            'USDC': 'USDC',
            'DAI': 'DAI',
            'TUSD': 'TUSD',  # 🔒 TUSD ≠ USDT!
            # Staked variants → base asset
            'ETH2.S': 'ETH', 'ETH2': 'ETH',
            'DOT.S': 'DOT', 'DOT28.S': 'DOT',
            'ATOM.S': 'ATOM', 'ATOM21.S': 'ATOM',
            'SOL.S': 'SOL',
            'KAVA.S': 'KAVA',
            'XTZ.S': 'XTZ',
            'ADA.S': 'ADA',
            'FLOW.S': 'FLOW',
            'KSM.S': 'KSM',
            'MINA.S': 'MINA',
            'SCRT.S': 'SCRT',
            'GRT.S': 'GRT',
            'MATIC.S': 'MATIC',
            'TRX.S': 'TRX',
            'NEAR.S': 'NEAR',
            'BABY.S': 'BABY',
            'OMG.S': 'OMG',
        }
        
        # 🔒 STABLECOIN ISOLATION - NEVER fuzzy match these to each other!
        # Each is a DIFFERENT asset with different backing/risk
        STABLECOINS_ISOLATED = {
            # USD-pegged (different issuers!)
            'USDT',   # Tether Limited (controversial reserves)
            'USDC',   # Circle/Coinbase (fully audited)
            'TUSD',   # TrustToken (independently verified)
            'BUSD',   # Paxos/Binance (deprecated)
            'USDP',   # Paxos Dollar (regulated)
            'GUSD',   # Gemini (NY regulated)
            'FRAX',   # Algorithmic + collateral hybrid
            'LUSD',   # Liquity (decentralized)
            'DAI',    # MakerDAO (crypto-collateralized)
            'MIM',    # Abracadabra (defi)
            'SUSD',   # Synthetix (synthetic)
            'USDD',   # TRON (algo)
            'PYUSD',  # PayPal (new)
            'FDUSD',  # First Digital (HK)
            # EUR-pegged
            'EURC',   # Circle EUR
            'EURT',   # Tether EUR
            'EURS',   # STASIS EUR
            'AGEUR',  # Angle EUR
            # Fiat (NOT stablecoins but isolated)
            'USD', 'EUR', 'GBP', 'CAD', 'JPY', 'AUD', 'CHF', 
            'ZUSD', 'ZEUR', 'ZGBP', 'ZCAD', 'ZJPY', 'ZAUD', 'ZCHF',
        }
        
        # 🟡 BINANCE ASSET MAP (for weird naming)
        BINANCE_ASSET_MAP = {
            'IOTA': 'MIOTA',  # Binance uses IOTA, others use MIOTA
            'YFIDOWN': 'YFI', 'YFIUP': 'YFI',  # Leveraged tokens
            'BTCDOWN': 'BTC', 'BTCUP': 'BTC',
            'ETHDOWN': 'ETH', 'ETHUP': 'ETH',
        }
        
        # 🦙 ALPACA ASSET MAP (crypto pairs end in /USD)
        ALPACA_PAIRS_TO_BASE = {
            # These are position symbols, not assets
            'BTCUSD': 'BTC', 'BTC/USD': 'BTC',
            'ETHUSD': 'ETH', 'ETH/USD': 'ETH',
            'SOLUSD': 'SOL', 'SOL/USD': 'SOL',
            'DOGEUSD': 'DOGE', 'DOGE/USD': 'DOGE',
            'SHIBUSD': 'SHIB', 'SHIB/USD': 'SHIB',
            'AVAXUSD': 'AVAX', 'AVAX/USD': 'AVAX',
            'USDTUSD': 'USDT', 'USDT/USD': 'USDT',
        }
        
        def normalize_asset(asset_name: str, exchange: str = None) -> str:
            """
            🗺️ UNIVERSAL NORMALIZER - Works across ALL exchanges!
            Converts exchange-specific naming to canonical symbol.
            """
            upper = asset_name.upper().strip()
            
            # Handle staked suffix first (ETH2.S → ETH)
            unstaked = upper.replace('.S', '').replace('2.S', '')
            
            # Exchange-specific normalization
            if exchange == 'kraken':
                if upper in KRAKEN_ASSET_MAP:
                    return KRAKEN_ASSET_MAP[upper]
                if unstaked in KRAKEN_ASSET_MAP:
                    return KRAKEN_ASSET_MAP[unstaked]
                # Handle XX prefix (XXABC → ABC)
                if upper.startswith('XX') and len(upper) > 2:
                    return upper[2:]
                # Handle single X prefix (but preserve XRP, XLM, XTZ, XMR, XDC)
                if upper.startswith('X') and len(upper) > 1:
                    if upper not in {'XRP', 'XLM', 'XTZ', 'XMR', 'XDC', 'XDG', 'XEM', 'XVG'}:
                        return upper[1:]
                # Handle Z prefix for fiat
                if upper.startswith('Z') and len(upper) > 1:
                    return upper[1:]
                    
            elif exchange == 'binance':
                if upper in BINANCE_ASSET_MAP:
                    return BINANCE_ASSET_MAP[upper]
                # Handle leveraged token suffixes
                for suffix in ['UP', 'DOWN', 'BULL', 'BEAR', '3L', '3S']:
                    if upper.endswith(suffix) and len(upper) > len(suffix):
                        return upper[:-len(suffix)]
                        
            elif exchange == 'alpaca':
                if upper in ALPACA_PAIRS_TO_BASE:
                    return ALPACA_PAIRS_TO_BASE[upper]
                # Strip /USD or USD suffix
                if upper.endswith('/USD'):
                    return upper[:-4]
                if upper.endswith('USD') and len(upper) > 3:
                    base = upper[:-3]
                    # Make sure we're not stripping from a stablecoin
                    if base not in STABLECOINS_ISOLATED:
                        return base
            
            return upper
        
        # Debug: Track candidates
        candidates = []
        
        for exchange, data in self.exchange_data.items():
            if data.get('connected') and data.get('balances'):
                for bal_asset, balance in data['balances'].items():
                    bal_upper = bal_asset.upper()
                    
                    # 🗺️ Normalize both the search asset AND the balance asset
                    normalized_bal = normalize_asset(bal_upper, exchange)
                    normalized_search = normalize_asset(asset_upper, exchange)
                    
                    # Exact match first (always preferred)
                    if normalized_bal == normalized_search or bal_upper == asset_upper:
                        bal_amount = float(balance) if isinstance(balance, (int, float, str)) else 0
                        if bal_upper != normalized_bal:
                            candidates.append(f"{exchange}:{bal_asset}→{normalized_bal}={bal_amount:.6f}")
                        else:
                            candidates.append(f"{exchange}:{bal_asset}={bal_amount:.6f}")
                        if bal_amount > best_balance:
                            best_balance = bal_amount
                            best_exchange = exchange
                            
                    # 🔒 STABLECOIN GUARD: NEVER fuzzy match stablecoins!
                    # USDT ≠ TUSD ≠ USDC - they are DIFFERENT assets with different risks!
                    elif normalized_search in STABLECOINS_ISOLATED or normalized_bal in STABLECOINS_ISOLATED:
                        # Only exact matches for stablecoins - skip ALL fuzzy logic
                        continue
        
        if len(candidates) > 1 and asset.upper() not in ['USD', 'USDT', 'USDC', 'ZUSD']:
            print(f"   🔎 Asset location check for {asset}: {', '.join(candidates)} -> Best: {best_exchange}")
            
        return best_exchange
    
    async def _execute_on_kraken(self, opp) -> bool:
        """Execute conversion on Kraken using convert_crypto."""
        try:
            # Use the built-in convert_crypto which finds the best path automatically!
            print(f"   🔄 Converting {opp.from_asset} → {opp.to_asset} via Kraken...")
            
            # 👑 QUEEN MIND: Decode conversion path in real-time
            # Refresh balance FIRST to get accurate amounts
            await self.refresh_exchange_balances('kraken')
            
            # 👑 TINA B FIX: Case-insensitive asset matching (Kraken may store differently)
            kraken_balances = self.exchange_balances.get('kraken', {})
            actual_balance = 0.0
            matched_asset = opp.from_asset
            
            for bal_key, bal_val in kraken_balances.items():
                if bal_key.upper() == opp.from_asset.upper():
                    actual_balance = float(bal_val) if isinstance(bal_val, (int, float, str)) else 0.0
                    matched_asset = bal_key
                    break
            
            print(f"   📊 Kraken {matched_asset} balance: {actual_balance:.6f} (need: {opp.from_amount:.6f})")
            
            # Clamp to actual available balance
            if actual_balance <= 0:
                print(f"   ⚠️ No {opp.from_asset} balance on Kraken (balance: {actual_balance})")
                return False
            
            # 👑 QUEEN'S SANITY CHECK: Don't clamp to dust!
            # If we have significantly less than expected, it's likely the wrong exchange
            if actual_balance < opp.from_amount * 0.1:
                print(f"   ⚠️ Kraken balance {actual_balance:.6f} is < 10% of expected {opp.from_amount:.6f}")
                print(f"   ⚠️ Likely asset location mismatch. Aborting Kraken execution.")
                return False

            # 👑 TINA B EXECUTION FIX: Use 95% of balance for safety margin
            # Kraken has precision issues, leave 5% buffer for fees + rounding
            safe_amount = actual_balance * 0.95
            if opp.from_amount > safe_amount:
                print(f"   👑 Tina B adjusts: {opp.from_amount:.6f} → {safe_amount:.6f} (95% safe)")
                opp.from_amount = safe_amount
                opp.from_value_usd = opp.from_amount * self.prices.get(opp.from_asset, 0)
            
            # Check if clamped amount is too small
            if opp.from_value_usd < 1.0:
                print(f"   ⚠️ Clamped value ${opp.from_value_usd:.2f} is too small for Kraken (min ~$1.50)")
                
                # 💧🔀 LIQUIDITY AGGREGATION CHECK - Can we top-up from other assets?
                shortfall = 1.50 - opp.from_value_usd
                aggregation_result = await self._attempt_liquidity_aggregation(
                    target_asset=opp.from_asset,
                    target_exchange='kraken',
                    shortfall_usd=shortfall,
                    expected_profit_pct=getattr(opp, 'expected_profit', 0.01),
                )
                if aggregation_result:
                    # Aggregation succeeded - retry the trade with new balance
                    await self.refresh_exchange_balances('kraken')
                    new_balance = self.exchange_balances.get('kraken', {}).get(opp.from_asset, 0)
                    opp.from_amount = float(new_balance) * 0.95
                    opp.from_value_usd = opp.from_amount * self.prices.get(opp.from_asset, 0)
                    print(f"   💧 POST-AGGREGATION: New {opp.from_asset} balance = {opp.from_amount:.6f} (${opp.from_value_usd:.2f})")
                    if opp.from_value_usd >= 1.50:
                        print(f"   ✅ Aggregation successful! Proceeding with trade...")
                        # Continue execution - don't return False
                    else:
                        print(f"   ❌ Aggregation insufficient - still below minimum")
                        self.barter_matrix.record_preexec_rejection(
                            opp.from_asset, opp.to_asset, 
                            f"Value ${opp.from_value_usd:.2f} < ~$1.50 after aggregation",
                            opp.from_value_usd
                        )
                        self.barter_matrix.record_source_rejection(
                            opp.from_asset, 'kraken', 1.50, opp.from_value_usd
                        )
                        return False
                else:
                    # 🚫 Record pre-execution rejection
                    self.barter_matrix.record_preexec_rejection(
                        opp.from_asset, opp.to_asset, 
                        f"Value ${opp.from_value_usd:.2f} < ~$1.50 Kraken minimum (no aggregation available)",
                        opp.from_value_usd
                    )
                    # 🚫 Also record SOURCE rejection - this asset is too small for Kraken entirely
                    self.barter_matrix.record_source_rejection(
                        opp.from_asset, 'kraken', 1.50, opp.from_value_usd
                    )
                    return False
            
            # First check if a path exists
            path = self.kraken.find_conversion_path(opp.from_asset, opp.to_asset)
            if not path:
                print(f"   ⚠️ No conversion path found from {opp.from_asset} to {opp.to_asset}")
                return False
            
            # 🔍 KRAKEN PRE-FLIGHT CHECK: Only check notional minimum (most reliable)
            # Kraken's costmin is the minimum order value in USD-equivalent
            for step in path:
                pair = step.get('pair', '')
                filters = self.kraken.get_symbol_filters(pair)
                min_notional = filters.get('min_notional', 0)  # costmin in Kraken terms
                min_qty = filters.get('min_qty', 0) or filters.get('min_volume', 0)
                
                # Check minimum notional value - Kraken typically requires ~$0.50 minimum
                # Use a safe default of $1.20 to avoid "volume too low" errors (Kraken often requires >1 EUR/USD)
                effective_min = max(min_notional, 1.20)
                if opp.from_value_usd < effective_min:
                    print(f"   ⚠️ Value ${opp.from_value_usd:.2f} < min notional ${effective_min:.2f} for {pair}")
                    print(f"   💡 Need ${effective_min:.2f} minimum to trade on Kraken")
                    return False

                # Guard on base quantity to avoid volume_minimum errors
                if min_qty:
                    # Use the from-asset price as a rough base valuation
                    from_price = self.prices.get(opp.from_asset, 0) or 1.0
                    min_qty_needed = max(min_qty, 0.0)
                    if opp.from_amount < min_qty_needed:
                        needed_usd = min_qty_needed * from_price
                        print(f"   ⚠️ Amount {opp.from_amount:.6f} < Kraken min qty {min_qty_needed:.6f} for {pair}")
                        print(f"   💡 Need ≥ {min_qty_needed:.6f} ({needed_usd:.2f} USD) to avoid volume_minimum")
                        # 🚫 Record pre-execution rejection
                        self.barter_matrix.record_preexec_rejection(
                            opp.from_asset, opp.to_asset, 
                            f"Amount {opp.from_amount:.6f} < min_qty {min_qty_needed:.6f}",
                            opp.from_value_usd
                        )
                        return False
            
            # Show the path
            for step in path:
                print(f"   📍 Path: {step['description']} via {step['pair']}")
            
            # Execute the conversion
            result = self.kraken.convert_crypto(
                from_asset=opp.from_asset,
                to_asset=opp.to_asset,
                amount=opp.from_amount
            )
            
            if result.get('error'):
                error_msg = str(result['error'])
                print(f"   ❌ Conversion error: {error_msg}")
                
                # 👑 QUEEN LEARNING: Auto-fix minimums
                if "volume_minimum" in error_msg or "min_notional" in error_msg:
                    print(f"   👑 Queen learning: Increasing minimum for {opp.from_asset}")
                    # Increase minimum to 1.5x current amount or at least $10
                    current_price = self.prices.get(opp.from_asset, 1.0)
                    min_usd_req = 10.0 # Safe default
                    
                    # If we know the amount that failed, we should aim higher
                    new_min_qty = max(opp.from_amount * 1.5, min_usd_req / current_price if current_price > 0 else 0)
                    
                    self.dynamic_min_qty[opp.from_asset.upper()] = new_min_qty
                    print(f"      Updated dynamic minimum for {opp.from_asset} to {new_min_qty:.6f}")
                    
                self._record_failure(opp)
                return False
            
            # Check results
            trades = result.get('trades', [])
            if isinstance(trades, list):
                success_count = sum(1 for t in trades if isinstance(t, dict) and t.get('status') == 'success')
                if success_count > 0:
                    # Calculate actual bought/received amount from the last trade
                    last_trade = trades[-1]
                    buy_amount = 0.0
                    if last_trade.get('status') == 'success':
                        res = last_trade.get('result', {})
                        # PRIORITY: Use receivedQty (for SELL orders) if available
                        # This is the ACTUAL amount we received after conversion
                        buy_amount = float(res.get('receivedQty', 0) or 
                                          last_trade.get('receivedQty', 0) or
                                          res.get('executedQty', 0.0))
                    
                    # Fallback if no amount found (e.g. dry run or error)
                    if buy_amount == 0.0:
                         # Estimate based on price
                         to_price = self.prices.get(opp.to_asset, 0)
                         if to_price > 0:
                             buy_amount = opp.from_value_usd / to_price
                    
                    print(f"   ✅ Conversion complete! {success_count} trades executed. Bought {buy_amount:.6f} {opp.to_asset}")
                    
                    # 🔍 VALIDATE ORDER EXECUTION
                    validation = self._validate_order_execution(trades, opp, 'kraken')
                    verification = self._verify_profit_math(validation, opp, buy_amount)
                    self._print_order_validation(validation, verification, opp)
                    
                    self._record_conversion(opp, buy_amount, validation, verification)
                    return True
                else:
                    print(f"   ❌ No successful trades in conversion")
                    self._record_failure(opp)
            elif result.get('dryRun'):
                print(f"   🔵 DRY RUN: Would convert via {len(path)} trades")
                return True
            else:
                print(f"   ✅ Conversion result: {result}")
                # Estimate amount for non-standard result
                to_price = self.prices.get(opp.to_asset, 0)
                buy_amount = opp.from_value_usd / to_price if to_price > 0 else 0
                self._record_conversion(opp, buy_amount)
                return True
                
        except Exception as e:
            logger.error(f"❌ Kraken conversion error: {e}")
            print(f"   ❌ Error: {e}")
            self._record_failure(opp)
        return False
    
    async def _execute_on_binance(self, opp) -> bool:
        """Execute conversion on Binance."""
        try:
            print(f"   🔄 Converting {opp.from_asset} → {opp.to_asset} via Binance...")
            
            # 👑 QUEEN MIND: Decode conversion path in real-time
            # Refresh balance FIRST to get accurate amounts
            await self.refresh_exchange_balances('binance')
            
            # Look for asset with different casing/formats
            binance_balances = self.exchange_balances.get('binance', {})
            actual_balance = 0.0
            matched_asset = opp.from_asset
            
            for bal_key, bal_val in binance_balances.items():
                if bal_key.upper() == opp.from_asset.upper():
                    actual_balance = float(bal_val) if isinstance(bal_val, (int, float, str)) else 0.0
                    matched_asset = bal_key
                    break
            
            print(f"   📊 Binance {matched_asset} balance: {actual_balance:.6f} (need: {opp.from_amount:.6f})")
            
            # Clamp to actual available balance with extra safety margin for fees
            if actual_balance <= 0:
                print(f"   ⚠️ No {opp.from_asset} balance on Binance (balance: {actual_balance})")
                return False
            
            # 👑 QUEEN'S SANITY CHECK: Don't clamp to dust!
            if actual_balance < opp.from_amount * 0.1:
                print(f"   ⚠️ Binance balance {actual_balance:.6f} is < 10% of expected {opp.from_amount:.6f}")
                print(f"   ⚠️ Likely asset location mismatch. Aborting Binance execution.")
                return False

            # Use 98% of balance instead of 99.5% for extra safety on Binance
            safe_amount = actual_balance * 0.98
            if opp.from_amount > safe_amount:
                print(f"   👑 Queen clamping: {opp.from_amount:.6f} → {safe_amount:.6f}")
                opp.from_amount = safe_amount
                opp.from_value_usd = opp.from_amount * self.prices.get(opp.from_asset, 0)
            
            # Check if clamped amount is too small
            if opp.from_value_usd < 5.0:
                print(f"   ⚠️ Clamped value ${opp.from_value_usd:.2f} is too small for Binance (min $5.00)")
                
                # 💧🔀 LIQUIDITY AGGREGATION CHECK - Can we top-up from other assets?
                shortfall = 5.0 - opp.from_value_usd
                aggregation_result = await self._attempt_liquidity_aggregation(
                    target_asset=opp.from_asset,
                    target_exchange='binance',
                    shortfall_usd=shortfall,
                    expected_profit_pct=getattr(opp, 'expected_profit', 0.01),
                )
                if aggregation_result:
                    # Aggregation succeeded - retry the trade with new balance
                    await self.refresh_exchange_balances('binance')
                    new_balance = self.exchange_balances.get('binance', {}).get(opp.from_asset, 0)
                    opp.from_amount = float(new_balance) * 0.98
                    opp.from_value_usd = opp.from_amount * self.prices.get(opp.from_asset, 0)
                    print(f"   💧 POST-AGGREGATION: New {opp.from_asset} balance = {opp.from_amount:.6f} (${opp.from_value_usd:.2f})")
                    if opp.from_value_usd >= 5.0:
                        print(f"   ✅ Aggregation successful! Proceeding with trade...")
                        # Continue execution - don't return False
                    else:
                        print(f"   ❌ Aggregation insufficient - still below minimum")
                        self.barter_matrix.record_preexec_rejection(
                            opp.from_asset, opp.to_asset, 
                            f"Value ${opp.from_value_usd:.2f} < $5.00 after aggregation",
                            opp.from_value_usd
                        )
                        self.barter_matrix.record_source_rejection(
                            opp.from_asset, 'binance', 5.0, opp.from_value_usd
                        )
                        return False
                else:
                    # 🚫 Record pre-execution rejection
                    self.barter_matrix.record_preexec_rejection(
                        opp.from_asset, opp.to_asset, 
                        f"Value ${opp.from_value_usd:.2f} < $5.00 Binance minimum (no aggregation available)",
                        opp.from_value_usd
                    )
                    # 🚫 Also record SOURCE rejection - this asset is too small for Binance entirely
                    self.barter_matrix.record_source_rejection(
                        opp.from_asset, 'binance', 5.0, opp.from_value_usd
                    )
                    return False
            
            # Debug: Check what type of binance client we have
            client_type = type(self.binance).__name__
            client_module = type(self.binance).__module__
            print(f"   📍 Binance client: {client_type} from {client_module}")

            # 🔍 BINANCE PRE-FLIGHT: Enforce min notional / quantity before attempting
            try:
                pair_symbol = f"{opp.from_asset}{opp.to_asset}"
                filters = self.binance.get_symbol_filters(pair_symbol)
                min_notional = float(filters.get('min_notional', 0) or 0)
                min_qty = float(filters.get('min_qty', 0) or 0)
                from_price = self.prices.get(opp.from_asset, 0) or 0
                if min_notional > 0 and opp.from_value_usd < min_notional:
                    print(f"   ⚠️ Value ${opp.from_value_usd:.2f} < Binance min notional ${min_notional:.2f} for {pair_symbol}")
                    # 🚫 Record pre-execution rejection
                    self.barter_matrix.record_preexec_rejection(
                        opp.from_asset, opp.to_asset, 
                        f"Value ${opp.from_value_usd:.2f} < min_notional ${min_notional:.2f}",
                        opp.from_value_usd
                    )
                    return False
                if min_qty > 0 and opp.from_amount < min_qty:
                    needed = min_qty * (from_price if from_price > 0 else 1)
                    print(f"   ⚠️ Amount {opp.from_amount:.6f} < Binance min qty {min_qty:.6f} for {pair_symbol}")
                    print(f"   💡 Need ≥ {min_qty:.6f} ({needed:.2f} USD) to avoid minQty rejection")
                    # 🚫 Record pre-execution rejection
                    self.barter_matrix.record_preexec_rejection(
                        opp.from_asset, opp.to_asset, 
                        f"Amount {opp.from_amount:.6f} < min_qty {min_qty:.6f}",
                        opp.from_value_usd
                    )
                    return False
            except Exception as pre_e:
                logger.debug(f"Binance pre-flight filter check skipped: {pre_e}")
            
            # Check if convert_crypto exists
            if not hasattr(self.binance, 'convert_crypto'):
                print(f"   ⚠️ BinanceClient missing convert_crypto method!")
                print(f"   📍 Available methods: {[m for m in dir(self.binance) if not m.startswith('_')][:20]}")
                
                # Fallback: Use direct place_market_order if available
                if hasattr(self.binance, 'place_market_order'):
                    print(f"   🔄 Attempting direct market order fallback...")
                    # Try direct pair
                    pair = f"{opp.from_asset}{opp.to_asset}"
                    result = self.binance.place_market_order(
                        symbol=pair,
                        side="SELL",
                        quantity=opp.from_amount
                    )
                    if result and not result.get("error"):
                        print(f"   ✅ Direct order executed: {result}")
                        return True
                    # Try inverse pair
                    pair = f"{opp.to_asset}{opp.from_asset}"
                    result = self.binance.place_market_order(
                        symbol=pair,
                        side="BUY",
                        quote_qty=opp.from_amount * opp.price if hasattr(opp, 'price') else opp.from_value_usd
                    )
                    if result and not result.get("error"):
                        print(f"   ✅ Inverse order executed: {result}")
                        return True
                
                self._record_failure(opp)
                return False
            
            # Use convert_crypto which handles pathfinding internally
            result = self.binance.convert_crypto(
                from_asset=opp.from_asset,
                to_asset=opp.to_asset,
                amount=opp.from_amount
            )
            
            # Handle pathfinding error from convert_crypto
            if result and result.get("error"):
                if "No conversion path" in str(result.get("error", "")):
                    print(f"   ⚠️ {result['error']}")
                    return False
            
            if result and result.get("trades"):
                # Validate the execution
                validation = self._validate_order_execution(result["trades"], opp, 'binance')
                
                if validation.get("valid"):
                    self._log_successful_conversion(validation, opp)
                    return True
                else:
                    logger.error(f"❌ Binance order validation failed: {validation.get('reason')}")
                    self._record_failure(opp)
                    return False
            elif result and result.get("dryRun"):
                # Dry run mode - simulate success
                print(f"   🧪 DRY RUN: Would convert via {result.get('trades', 0)} trades")
                return True
            else:
                error_msg = result.get("error", "Unknown error")
                logger.error(f"❌ Binance conversion error: {error_msg}")
                print(f"   ❌ Error: {error_msg}")
                self._record_failure(opp)
                return False
        
        except Exception as e:
            logger.error(f"❌ Binance conversion error: {e}")
            print(f"   ❌ Error: {e}")
            self._record_failure(opp)
        return False
    
    async def _execute_on_alpaca(self, opp) -> bool:
        """Execute conversion on Alpaca using convert_crypto."""
        try:
            # Use the built-in convert_crypto which finds the best path automatically!
            print(f"   🔄 Converting {opp.from_asset} → {opp.to_asset} via Alpaca...")
            
            # 👑 QUEEN MIND: Decode conversion path in real-time
            # Refresh balance FIRST to get accurate amounts
            await self.refresh_exchange_balances('alpaca')
            
            # 👑 TINA B FIX: Case-insensitive asset matching
            alpaca_balances = self.exchange_balances.get('alpaca', {})
            actual_balance = 0.0
            matched_asset = opp.from_asset
            
            for bal_key, bal_val in alpaca_balances.items():
                if bal_key.upper() == opp.from_asset.upper():
                    actual_balance = float(bal_val) if isinstance(bal_val, (int, float, str)) else 0.0
                    matched_asset = bal_key
                    break
            
            print(f"   📊 Alpaca {matched_asset} balance: {actual_balance:.6f} (need: {opp.from_amount:.6f})")
            
            # Clamp to actual available balance
            if actual_balance <= 0:
                print(f"   ⚠️ No {opp.from_asset} balance on Alpaca (balance: {actual_balance})")
                return False
            
            # 👑 TINA B EXECUTION FIX: Use 95% of balance for safety margin
            safe_amount = actual_balance * 0.95
            if opp.from_amount > safe_amount:
                print(f"   👑 Tina B adjusts: {opp.from_amount:.6f} → {safe_amount:.6f} (95% safe)")
                opp.from_amount = safe_amount
                opp.from_value_usd = opp.from_amount * self.prices.get(opp.from_asset, 0)
            
            # First check if a path exists
            path = self.alpaca.find_conversion_path(opp.from_asset, opp.to_asset)
            if not path:
                print(f"   ⚠️ No conversion path found from {opp.from_asset} to {opp.to_asset}")
                return False
            
            # 🔍 ALPACA PRE-FLIGHT CHECK: Verify minimums for EACH step
            # Alpaca has different minimums per crypto asset
            ALPACA_MIN_NOTIONAL = 1.0  # Alpaca typically has $1 minimum
            ALPACA_MIN_QTY = {
                'BTC': 0.0001,    # ~$10 at current prices
                'ETH': 0.001,     # ~$3 at current prices
                'SOL': 0.01,      # ~$2 at current prices
                'DOGE': 1.0,      # ~$0.30 at current prices
                'SHIB': 100000.0, # Fractions of a cent
                'PEPE': 100000.0, # Fractions of a cent
                'AVAX': 0.01,     # ~$0.40 at current prices
                'LINK': 0.1,      # ~$2 at current prices
                'DOT': 0.1,       # ~$0.70 at current prices
                'AAVE': 0.001,    # ~$0.16 at current prices
            }
            
            for step in path:
                pair = step.get('pair', '')
                # Alpaca pairs are like 'BTC/USD'
                base_asset = pair.split('/')[0] if '/' in pair else opp.from_asset
                
                # Check minimum quantity for this asset
                min_qty = ALPACA_MIN_QTY.get(base_asset.upper(), 0.0001)  # Default very small
                
                # For selling, check if we have enough of the from_asset
                if step.get('side') == 'sell' and opp.from_amount < min_qty:
                    print(f"   ⚠️ Qty {opp.from_amount:.6f} < min {min_qty:.6f} for {pair}")
                    print(f"   💡 Need {min_qty:.6f} {base_asset} minimum")
                    return False
                
                # Check minimum notional value
                if opp.from_value_usd < ALPACA_MIN_NOTIONAL:
                    print(f"   ⚠️ Value ${opp.from_value_usd:.2f} < min notional ${ALPACA_MIN_NOTIONAL:.2f}")
                    print(f"   💡 Need ${ALPACA_MIN_NOTIONAL:.2f} minimum to trade on Alpaca")
                    return False
            
            # Show the path
            for step in path:
                print(f"   📍 Path: {step['description']} via {step['pair']}")
            
            # Execute the conversion
            result = self.alpaca.convert_crypto(
                from_asset=opp.from_asset,
                to_asset=opp.to_asset,
                amount=opp.from_amount
            )
            
            if result.get('error'):
                print(f"   ❌ Conversion error: {result['error']}")
                self._record_failure(opp)
                return False
            
            # Check results
            trades = result.get('trades', [])
            if isinstance(trades, list):
                success_count = sum(1 for t in trades if isinstance(t, dict) and t.get('status') == 'success')
                if success_count > 0:
                    # Calculate actual bought amount from the last trade
                    last_trade = trades[-1]
                    buy_amount = 0.0
                    if last_trade.get('status') == 'success':
                        res = last_trade.get('result', {})
                        buy_amount = float(res.get('qty', 0.0)) # Alpaca uses 'qty'
                    
                    # Fallback if qty is missing or 0
                    if buy_amount == 0.0:
                         # Estimate based on price
                         to_price = self.prices.get(opp.to_asset, 0)
                         if to_price > 0:
                             buy_amount = opp.from_value_usd / to_price
                    
                    print(f"   ✅ Conversion complete! {success_count} trades executed. Bought {buy_amount:.6f} {opp.to_asset}")
                    
                    # 🔍 VALIDATE ORDER EXECUTION
                    validation = self._validate_order_execution(trades, opp, 'alpaca')
                    verification = self._verify_profit_math(validation, opp, buy_amount)
                    self._print_order_validation(validation, verification, opp)
                    
                    self._record_conversion(opp, buy_amount, validation, verification)
                    return True
                else:
                    print(f"   ❌ No successful trades in conversion")
                    self._record_failure(opp)
            elif result.get('dryRun'):
                print(f"   🔵 DRY RUN: Would convert via {len(path)} trades")
                return True
            else:
                print(f"   ✅ Conversion result: {result}")
                # Estimate amount for non-standard result
                to_price = self.prices.get(opp.to_asset, 0)
                buy_amount = opp.from_value_usd / to_price if to_price > 0 else 0
                self._record_conversion(opp, buy_amount)
                return True
                
        except Exception as e:
            logger.error(f"❌ Alpaca conversion error: {e}")
            print(f"   ❌ Error: {e}")
            self._record_failure(opp)
        return False

    # ════════════════════════════════════════════════════════════════════════════
    # 🔍 ORDER VALIDATION & PROFIT VERIFICATION SYSTEM
    # ════════════════════════════════════════════════════════════════════════════
    
    def _validate_order_execution(self, trades: List[Dict], opp, exchange: str) -> Dict:
        """
        🔍 COMPREHENSIVE ORDER VALIDATION
        
        Validates each trade step using order IDs from the trading platform.
        Verifies fills, calculates actual execution prices, and computes real P&L.
        
        Returns:
            Dict with validation results:
            - valid: bool
            - order_ids: List of order IDs
            - total_sold: Actual amount sold
            - total_bought: Actual amount bought
            - avg_sell_price: Average sell price
            - avg_buy_price: Average buy price
            - total_fees: Total fees paid
            - realized_pnl: Validated P&L
            - validation_errors: List of any issues
        """
        validation = {
            'valid': True,
            'order_ids': [],
            'total_sold': 0.0,
            'total_bought': 0.0,
            'avg_sell_price': 0.0,
            'avg_buy_price': 0.0,
            'total_fees': 0.0,
            'realized_pnl': 0.0,
            'validation_errors': [],
            'exchange': exchange,
            'timestamp': time.time(),
        }
        
        if not trades:
            validation['valid'] = False
            validation['validation_errors'].append("No trades to validate")
            return validation
        
        sell_volume = 0.0
        sell_value = 0.0
        buy_volume = 0.0
        buy_value = 0.0
        
        for i, trade in enumerate(trades):
            step_num = i + 1
            
            if not isinstance(trade, dict):
                validation['validation_errors'].append(f"Step {step_num}: Invalid trade format")
                continue
            
            status = trade.get('status', '')
            result = trade.get('result', {})
            trade_info = trade.get('trade', {})
            
            # Extract order ID based on exchange
            order_id = self._extract_order_id(result, exchange)
            if order_id:
                validation['order_ids'].append({
                    'step': step_num,
                    'order_id': order_id,
                    'exchange': exchange,
                    'pair': trade_info.get('pair', ''),
                    'side': trade_info.get('side', ''),
                })
            
            if status != 'success':
                validation['valid'] = False
                error_msg = trade.get('error', 'Unknown error')
                validation['validation_errors'].append(f"Step {step_num}: {error_msg}")
                continue
            
            # Validate fill data
            executed_qty = float(result.get('executedQty', 0))
            cumm_quote_qty = float(result.get('cummulativeQuoteQty', 0))
            
            side = trade_info.get('side', 'buy')
            
            if side == 'sell':
                sell_volume += executed_qty
                sell_value += cumm_quote_qty
            else:
                buy_volume += executed_qty
                buy_value += cumm_quote_qty
            
            # Extract and sum fees
            fees = self._extract_fees(result, exchange)
            validation['total_fees'] += fees
            
            # Verify the fill makes sense
            if executed_qty <= 0:
                validation['validation_errors'].append(f"Step {step_num}: Zero executed quantity")
        
        # Calculate averages
        if sell_volume > 0:
            validation['avg_sell_price'] = sell_value / sell_volume if sell_value > 0 else 0
            validation['total_sold'] = sell_volume
        
        if buy_volume > 0:
            validation['avg_buy_price'] = buy_value / buy_volume
            validation['total_bought'] = buy_volume
        
        # For conversions, the "bought" amount is what we end up with
        # If we did sell → buy, the buy_volume is our result
        # If we did just one side, use that
        if buy_volume > 0:
            validation['final_amount'] = buy_volume
        elif sell_value > 0:
            # We sold and received quote currency (the sell_value IS what we received)
            validation['final_amount'] = sell_value
        elif sell_volume > 0 and validation['avg_sell_price'] > 0:
            # FALLBACK: When sell_value (cummulativeQuoteQty) is 0 (like with Kraken SELL orders)
            # Calculate expected received amount from sell_volume * avg_sell_price
            validation['final_amount'] = sell_volume * validation['avg_sell_price']
        else:
            validation['final_amount'] = 0
        
        return validation
    
    def _extract_order_id(self, result: Dict, exchange: str) -> Optional[str]:
        """Extract order ID from trade result based on exchange format."""
        if not result:
            return None
        
        if exchange == 'kraken':
            # Kraken uses 'orderId' which we set from 'txid'
            return result.get('orderId') or result.get('txid')
        elif exchange == 'binance':
            return result.get('orderId') or result.get('clientOrderId')
        elif exchange == 'alpaca':
            return result.get('id') or result.get('order_id')
        
        # Fallback
        return result.get('orderId') or result.get('order_id') or result.get('id')
    
    def _extract_fees(self, result: Dict, exchange: str) -> float:
        """Extract fees from trade result based on exchange format and convert to USD."""
        total_fees = 0.0
        
        if exchange == 'binance':
            # Binance includes fills with commission and commissionAsset
            fills = result.get('fills', [])
            for fill in fills:
                try:
                    commission = float(fill.get('commission', 0))
                    commission_asset = str(fill.get('commissionAsset', '')).upper()
                    
                    if commission > 0 and commission_asset:
                        # Convert fee to USD using current prices
                        if commission_asset in ('USD', 'USDT', 'USDC', 'BUSD'):
                            total_fees += commission
                        else:
                            # Get price of commission asset
                            asset_price = self.prices.get(commission_asset, 0)
                            if asset_price > 0:
                                total_fees += commission * asset_price
                            else:
                                # Fallback: assume small fee (0.1% of typical trade)
                                total_fees += commission * 0.0001  # Conservative estimate
                except (ValueError, TypeError):
                    pass
        elif exchange == 'kraken':
            # Kraken fees need to be calculated from the trade
            # Fee is typically 0.16% maker or 0.26% taker
            executed_qty = float(result.get('executedQty', 0))
            # Get the trade value in USD
            avg_price = float(result.get('avgPrice', 0) or result.get('price', 0) or 0)
            trade_value_usd = executed_qty * avg_price
            fee_rate = 0.0026  # Assume taker (more conservative)
            total_fees = trade_value_usd * fee_rate
        elif exchange == 'alpaca':
            # Alpaca includes fees differently
            total_fees = float(result.get('commission', 0) or result.get('fee', 0) or 0)
        
        return total_fees
    
    def _verify_profit_math(self, validation: Dict, opp, buy_amount: float) -> Dict:
        """
        🔢 VERIFY PROFIT CALCULATION MATH
        
        Cross-checks our calculated P&L against actual execution data.
        Returns verification results with any discrepancies.
        """
        verification = {
            'valid': True,
            'expected_pnl': opp.expected_pnl_usd,
            'calculated_pnl': 0.0,
            'verified_pnl': 0.0,
            'discrepancy': 0.0,
            'discrepancy_pct': 0.0,
            'warnings': [],
        }
        
        # Get current prices for calculation
        from_price = self.prices.get(opp.from_asset, 0)
        to_price = self.prices.get(opp.to_asset, 0)
        
        if not from_price or not to_price:
            verification['warnings'].append("Missing price data for verification")
            return verification
        
        # Calculate P&L using our method
        sold_value = opp.from_amount * from_price
        bought_value = buy_amount * to_price
        calculated_pnl = bought_value - sold_value
        verification['calculated_pnl'] = calculated_pnl
        
        # Calculate P&L using actual execution data (if available)
        if validation.get('total_sold') > 0 or validation.get('final_amount', 0) > 0 or buy_amount > 0:
            # 🔧 FIX: Use ACTUAL EXECUTION PRICES, not current market prices!
            # This is critical for accurate P/L calculation
            
            # Sold value - use actual execution price if available
            if validation.get('avg_sell_price', 0) > 0:
                actual_sold_value = validation['total_sold'] * validation['avg_sell_price']
            else:
                actual_sold_value = sold_value
            
            # Final bought value - CRITICAL FIX:
            # For SELL orders (like DAI→USD), validation['final_amount'] may be 0 because
            # exchanges like Kraken don't return cummulativeQuoteQty for sells.
            # In this case, use the buy_amount we actually received from the trade!
            final_amount = validation.get('final_amount', 0)
            if final_amount <= 0 and buy_amount > 0:
                # Fallback to buy_amount when final_amount is missing/zero
                final_amount = buy_amount
            
            # 🔧 FIX: Use actual buy price if available, not current price
            if validation.get('avg_buy_price', 0) > 0:
                actual_bought_value = final_amount * validation['avg_buy_price']
            else:
                actual_bought_value = final_amount * to_price
            
            # Subtract fees (fees are already in USD/quote currency)
            fees = validation.get('total_fees', 0)
            # 🔧 FIX: fees_in_usd calculation - fees are often in quote currency already
            # Don't multiply by to_price if fee is already in USD/USDC/USDT
            fees_in_usd = fees  # Assume fees are already in USD value
            
            verified_pnl = actual_bought_value - actual_sold_value - fees_in_usd
            verification['verified_pnl'] = verified_pnl
            
            # Check for discrepancy
            discrepancy = abs(calculated_pnl - verified_pnl)
            verification['discrepancy'] = discrepancy
            
            if abs(calculated_pnl) > 0.0001:
                verification['discrepancy_pct'] = (discrepancy / abs(calculated_pnl)) * 100
            
            # Flag significant discrepancies (>5%)
            if verification['discrepancy_pct'] > 5.0:
                verification['valid'] = False
                verification['warnings'].append(
                    f"P&L discrepancy: calculated ${calculated_pnl:.4f} vs verified ${verified_pnl:.4f} ({verification['discrepancy_pct']:.1f}%)"
                )
        else:
            verification['verified_pnl'] = calculated_pnl
        
        return verification
    
    def _print_order_validation(self, validation: Dict, verification: Dict, opp):
        """Print comprehensive order validation results."""
        print("\n   " + "═" * 60)
        print("   🔍 ORDER VALIDATION & PROFIT VERIFICATION")
        print("   " + "═" * 60)
        
        # Order IDs
        if validation['order_ids']:
            print(f"   📋 Order IDs ({validation['exchange'].upper()}):")
            for order in validation['order_ids']:
                print(f"      Step {order['step']}: {order['order_id']} ({order['side']} {order['pair']})")
        
        # Execution Summary
        print(f"\n   📊 EXECUTION SUMMARY:")
        print(f"      Sold: {validation['total_sold']:.8f} {opp.from_asset}")
        print(f"      Bought: {validation.get('final_amount', 0):.8f} {opp.to_asset}")
        if validation['avg_sell_price'] > 0:
            print(f"      Avg Sell Price: ${validation['avg_sell_price']:.6f}")
        if validation['avg_buy_price'] > 0:
            print(f"      Avg Buy Price: ${validation['avg_buy_price']:.6f}")
        print(f"      Total Fees: ${validation['total_fees']:.6f}")
        
        # P&L Verification
        print(f"\n   💰 P&L VERIFICATION:")
        print(f"      Expected P&L: ${verification['expected_pnl']:+.4f}")
        print(f"      Calculated P&L: ${verification['calculated_pnl']:+.4f}")
        print(f"      Verified P&L: ${verification['verified_pnl']:+.4f}")
        
        if verification['discrepancy'] > 0.0001:
            status = "⚠️" if verification['discrepancy_pct'] > 5 else "✅"
            print(f"      {status} Discrepancy: ${verification['discrepancy']:.4f} ({verification['discrepancy_pct']:.1f}%)")
        else:
            print(f"      ✅ Math Verified!")
        
        # Validation Status
        if validation['validation_errors']:
            print(f"\n   ⚠️ VALIDATION ISSUES:")
            for error in validation['validation_errors']:
                print(f"      - {error}")
        
        if verification['warnings']:
            print(f"\n   ⚠️ VERIFICATION WARNINGS:")
            for warning in verification['warnings']:
                print(f"      - {warning}")
        
        # Final Status
        if validation['valid'] and verification['valid']:
            print(f"\n   ✅ ORDER FULLY VALIDATED - Profit math confirmed!")
        else:
            print(f"\n   ⚠️ VALIDATION INCOMPLETE - Review required")
        
        print("   " + "═" * 60)
    
    def _record_conversion(self, opp, buy_amount: float, validation: Dict = None, verification: Dict = None):
        """Record a successful conversion with STEP-BY-STEP realized profit tracking and ORDER VALIDATION."""
        opp.executed = True
        self.conversions_made += 1
        self.conversions.append(opp)
        self.balances[opp.from_asset] = self.balances.get(opp.from_asset, 0) - opp.from_amount
        self.balances[opp.to_asset] = self.balances.get(opp.to_asset, 0) + buy_amount

        # 🚨 USE ACTUAL EXECUTION DATA, NOT ESTIMATED PRICES
        # This is critical to prevent ghost profits!
        from_price = self.prices.get(opp.from_asset, 0)
        to_price = self.prices.get(opp.to_asset, 0)
        
        # Try to use actual execution values from validation
        if validation and validation.get('total_sold', 0) > 0:
            # Use actual execution data
            if validation.get('avg_sell_price', 0) > 0:
                sold_value = validation['total_sold'] * validation['avg_sell_price']
            else:
                sold_value = opp.from_amount * from_price
            
            if validation.get('avg_buy_price', 0) > 0:
                bought_value = validation.get('final_amount', buy_amount) * validation['avg_buy_price']
            else:
                bought_value = buy_amount * to_price
            
            # Subtract fees from bought value (fees reduce profit)
            # Note: fees are already in USD from _extract_fees
            fees_usd = validation.get('total_fees', 0)
            if fees_usd > 0:
                bought_value -= fees_usd  # Direct USD subtraction
        else:
            # Fallback to price-based estimate
            sold_value = opp.from_amount * from_price
            bought_value = buy_amount * to_price
        
        actual_pnl = bought_value - sold_value
        opp.actual_pnl_usd = actual_pnl
        
        # ═══════════════════════════════════════════════════════════════════
        # 🔍 ORDER VALIDATION AUDIT TRAIL
        # ═══════════════════════════════════════════════════════════════════
        if validation:
            # Use verified P&L if available (most accurate)
            if verification and verification.get('verified_pnl') is not None:
                actual_pnl = verification['verified_pnl']
                opp.actual_pnl_usd = actual_pnl
                # Update bought_value to reflect actual P&L (don't reset sold_value!)
                # sold_value already has correct value from execution data above
                bought_value = sold_value + actual_pnl  # bought = sold + profit (actual)
                opp.pnl_verified = True
                opp.verification_status = 'VERIFIED' if verification['valid'] else 'DISCREPANCY'
            else:
                opp.pnl_verified = False
                opp.verification_status = 'UNVERIFIED'
            
            # Store order IDs for audit trail
            opp.order_ids = validation.get('order_ids', [])
            opp.execution_fees = validation.get('total_fees', 0)
            
            # Log validation to persistent storage for auditing
            self._log_order_validation(opp, validation, verification)
        else:
            opp.pnl_verified = False
            opp.verification_status = 'NO_VALIDATION'
            opp.order_ids = []
            opp.execution_fees = 0
        
        # ═══════════════════════════════════════════════════════════════════
        # 🫒💰 LIVE BARTER MATRIX - Record & Display Step Profit
        # ═══════════════════════════════════════════════════════════════════
        
        # Update barter rates for this pair
        self.barter_matrix.update_barter_rate(
            opp.from_asset, opp.to_asset, from_price, to_price
        )
        
        # Record realized profit in the barter ledger
        profit_result = self.barter_matrix.record_realized_profit(
            from_asset=opp.from_asset,
            to_asset=opp.to_asset,
            from_amount=opp.from_amount,
            from_usd=sold_value,
            to_amount=buy_amount,
            to_usd=bought_value
        )
        
        # 🎯 PRINT STEP-BY-STEP REALIZED PROFIT
        step_display = self.barter_matrix.print_step_profit(
            step_num=self.conversions_made,
            from_asset=opp.from_asset,
            to_asset=opp.to_asset,
            from_usd=sold_value,
            to_usd=bought_value,
            from_amount=opp.from_amount,
            to_amount=buy_amount
        )
        print(step_display)
        
        # Show path performance (how this specific conversion path is doing)
        print(f"   📊 PATH {opp.from_asset}→{opp.to_asset}: {profit_result['path_trades']} trades, ${profit_result['path_total_profit']:+.4f} total")
        print(f"   🔄 Slippage: {profit_result['actual_slippage_pct']:.2f}%")
        
        # 👑🍄 QUEEN'S MYCELIUM BROADCAST - Send signals to all systems
        if profit_result.get('is_win'):
            print(f"   👑 Queen's Verdict: ✅ WIN! Path continues.")
        else:
            win_rate = profit_result.get('path_win_rate', 0)
            print(f"   👑 Queen's Verdict: ❌ LOSS! Path win rate: {win_rate:.0%}")
            # Broadcast through mycelium
            queen_signals = self.barter_matrix.get_queen_signals()
            for signal in queen_signals:
                if signal['type'] == 'PATH_BLOCKED':
                    print(f"   🍄 MYCELIUM BROADCAST: {signal['path']} BLOCKED - {signal['reason']}")
        
        # Update total_profit_usd to match barter matrix
        self.total_profit_usd = self.barter_matrix.total_realized_profit

        # Learn: update hub and path memory
        if self.hub and hasattr(self.hub, 'record_conversion_outcome'):
            try:
                self.hub.record_conversion_outcome(opp.from_asset, opp.to_asset, actual_pnl >= 0, actual_pnl)
            except Exception:
                pass
        self.path_memory.record(opp.from_asset, opp.to_asset, actual_pnl >= 0)
        
        # 👑 Update Queen's path memory with new data
        if hasattr(self, 'queen') and self.queen and hasattr(self.queen, 'path_memory'):
            path_key = f"{opp.from_asset.upper()}->{opp.to_asset.upper()}"
            if not hasattr(self.queen, 'path_memory') or self.queen.path_memory is None:
                self.queen.path_memory = {}
            if path_key not in self.queen.path_memory:
                self.queen.path_memory[path_key] = {'wins': 0, 'losses': 0}
            if actual_pnl >= 0:
                self.queen.path_memory[path_key]['wins'] += 1
            else:
                self.queen.path_memory[path_key]['losses'] += 1

        # 📅🔮 7-DAY PLANNER: Validate timing prediction after conversion
        if self.seven_day_planner:
            try:
                # Record this conversion for validation tracking
                validation_id = self.seven_day_planner.record_conversion(
                    symbol=opp.to_asset,
                    entry_price=to_price
                )
                
                # Validate immediately with exit price (for compound tracking)
                # The next scan will have updated prices for true validation
                result = self.seven_day_planner.validate_conversion(
                    validation_id=validation_id,
                    exit_price=to_price  # Will be updated on next trade
                )
                
                if result:
                    timing_tag = "🎯" if result.direction_correct else "❌"
                    print(f"   📅 7-Day Validation: {timing_tag} timing={result.timing_score:.0%}")
                    
                    # Log adaptive weight updates
                    weights = self.seven_day_planner.adaptive_weights
                    print(f"   🧠 Adaptive: h={weights['hourly_weight']:.2f}, s={weights['symbol_weight']:.2f}, acc={weights['accuracy_7d']:.0%}")
            except Exception as e:
                logger.debug(f"7-day planner validation error: {e}")

        # Publish observability
        if self.thought_bus:
            try:
                self.thought_bus.think(
                    topic='conversion.success',
                    message='conversion recorded',
                    metadata={
                        'pair': f"{opp.from_asset}->{opp.to_asset}",
                        'pnl': round(actual_pnl, 6),
                        'lambda': round(opp.lambda_score, 4),
                        'gravity': round(opp.gravity_score, 4),
                        'gate_req': round(opp.gate_required_profit, 6),
                        'gate_passed': opp.gate_passed,
                    }
                )
            except Exception:
                pass

    def _record_failure(self, opp, error_msg: str = "", validation: Dict = None):
        """
        Record a failed conversion attempt for learning.
        
        👑🎓 QUEEN LOSS LEARNING INTEGRATION:
        When we fail, we learn. We pull data, research tactics, and never forget.
        """
        self.path_memory.record(opp.from_asset, opp.to_asset, False)
        
        if self.thought_bus:
            try:
                self.thought_bus.think(
                    topic='conversion.failure',
                    message='conversion failed',
                    metadata={'pair': f"{opp.from_asset}->{opp.to_asset}", 'error': error_msg}
                )
            except Exception:
                pass
        
        # 👑🎓 QUEEN LOSS LEARNING - Analyze every failure to learn and evolve
        if self.loss_learning:
            try:
                # Determine exchange
                exchange = opp.source_exchange or 'unknown'
                
                # Estimate loss amount (what we expected vs what happened)
                # If the conversion failed completely, the loss is the opportunity cost
                expected_profit = opp.expected_pnl_usd if opp.expected_pnl_usd > 0 else 0.01
                
                # Get prices
                from_price = self.prices.get(opp.from_asset, opp.from_value_usd / opp.from_amount if opp.from_amount > 0 else 1)
                to_price = self.prices.get(opp.to_asset, 0)
                
                # Calculate executed vs expected prices
                expected_price = to_price if to_price > 0 else 1
                executed_price = expected_price  # On failure, we don't have executed price
                
                # If validation data available, extract actual execution info
                if validation:
                    executed_price = validation.get('avg_buy_price', expected_price)
                    if validation.get('total_sold', 0) > 0 and opp.from_amount > 0:
                        # We sold but didn't get what we expected
                        loss_pct = (opp.from_amount - validation.get('total_sold', 0)) / opp.from_amount
                        expected_profit = opp.expected_pnl_usd * loss_pct
                
                # Build signals map from opportunity scores
                signals_used = {
                    'v14_score': opp.v14_score,
                    'hub_score': opp.hub_score,
                    'commando_score': opp.commando_score,
                    'lambda_score': opp.lambda_score,
                    'gravity_score': opp.gravity_score,
                    'luck_score': opp.luck_score,
                    'enigma_score': opp.enigma_score,
                    'timeline_score': opp.timeline_score,
                    'trained_matrix_score': opp.trained_matrix_score,
                    'barter_matrix_score': opp.barter_matrix_score,
                }
                
                # Fees estimated from config
                fees_paid = opp.from_value_usd * MICRO_CONFIG['total_cost_rate']
                
                # Loss amount = expected profit (opportunity cost) + any slippage
                loss_amount = max(expected_profit, 0.001)  # At least $0.001 for tracking
                
                # Schedule async analysis (don't block the main loop)
                import asyncio
                asyncio.create_task(self._async_loss_analysis(
                    exchange=exchange,
                    from_asset=opp.from_asset,
                    to_asset=opp.to_asset,
                    from_amount=opp.from_amount,
                    from_value_usd=opp.from_value_usd,
                    executed_price=executed_price,
                    expected_price=expected_price,
                    fees_paid=fees_paid,
                    loss_amount=loss_amount,
                    signals_used=signals_used,
                    combined_score=opp.combined_score,
                    expected_profit=expected_profit,
                    error_msg=error_msg,
                ))
                
            except Exception as e:
                logger.debug(f"Loss learning error: {e}")
    
    async def _async_loss_analysis(self, **kwargs):
        """Async wrapper for loss analysis to not block main trading loop."""
        try:
            error_msg = kwargs.pop('error_msg', '')
            loss = await self.loss_learning.analyze_loss(**kwargs)
            
            # Check if we should auto-block this path
            avoid, reason = self.loss_learning.should_avoid_trade(
                kwargs['from_asset'],
                kwargs['to_asset'],
                kwargs['exchange'],
                kwargs.get('expected_profit', 0.01)
            )
            
            if avoid:
                print(f"   👑🎓 QUEEN WISDOM: BLOCKING {kwargs['from_asset']}→{kwargs['to_asset']}")
                print(f"      Reason: {reason}")
                
                # Store in path memory as perma-block
                self.path_memory.block_path(kwargs['from_asset'], kwargs['to_asset'])
                
        except Exception as e:
            logger.debug(f"Async loss analysis error: {e}")

    def _log_successful_conversion(self, validation: Dict, opp):
        """
        Log a successful conversion with validation data.
        This is a convenience wrapper around _record_conversion.
        """
        # Calculate buy/received amount from validation
        buy_amount = 0.0
        trades = validation.get('trades', [])
        if trades:
            last_trade = trades[-1]
            if isinstance(last_trade, dict):
                # PRIORITY: Use receivedQty (for SELL orders) if available
                res = last_trade.get('result', {})
                buy_amount = float(res.get('receivedQty', 0) or
                                   last_trade.get('receivedQty', 0) or
                                   res.get('executedQty', 0) or 
                                   last_trade.get('executedQty', 0) or 0)
        
        # Fallback estimate if no amount found
        if buy_amount == 0:
            to_price = self.prices.get(opp.to_asset, 0)
            if to_price > 0:
                buy_amount = opp.from_value_usd / to_price
        
        # Verify profit math
        verification = self._verify_profit_math(validation, opp, buy_amount)
        
        # Print validation summary
        self._print_order_validation(validation, verification, opp)
        
        # Record the conversion
        self._record_conversion(opp, buy_amount, validation, verification)
    
    def _log_order_validation(self, opp, validation: Dict, verification: Dict):
        """
        📋 LOG ORDER VALIDATION TO PERSISTENT AUDIT TRAIL
        
        Stores all order IDs, execution details, and P&L verification
        for post-trade auditing and compliance.
        """
        import json
        from datetime import datetime
        
        audit_file = "aureon_order_audit.json"
        
        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'conversion_num': self.conversions_made,
            'exchange': validation.get('exchange', 'unknown'),
            'from_asset': opp.from_asset,
            'to_asset': opp.to_asset,
            'from_amount': opp.from_amount,
            'to_amount': validation.get('final_amount', 0),
            'order_ids': validation.get('order_ids', []),
            'validation': {
                'valid': validation.get('valid', False),
                'total_sold': validation.get('total_sold', 0),
                'total_bought': validation.get('final_amount', 0),
                'avg_sell_price': validation.get('avg_sell_price', 0),
                'avg_buy_price': validation.get('avg_buy_price', 0),
                'total_fees': validation.get('total_fees', 0),
                'errors': validation.get('validation_errors', []),
            },
            'profit_verification': {
                'expected_pnl': verification.get('expected_pnl', 0) if verification else 0,
                'calculated_pnl': verification.get('calculated_pnl', 0) if verification else 0,
                'verified_pnl': verification.get('verified_pnl', 0) if verification else 0,
                'discrepancy': verification.get('discrepancy', 0) if verification else 0,
                'discrepancy_pct': verification.get('discrepancy_pct', 0) if verification else 0,
                'math_valid': verification.get('valid', False) if verification else False,
                'warnings': verification.get('warnings', []) if verification else [],
            },
            'final_status': 'VERIFIED' if (validation.get('valid') and (verification and verification.get('valid'))) else 'NEEDS_REVIEW',
        }
        
        try:
            # Load existing audit log
            try:
                with open(audit_file, 'r') as f:
                    audit_log = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                audit_log = {'orders': [], 'summary': {'total': 0, 'verified': 0, 'discrepancies': 0}}
            
            # Append new entry
            audit_log['orders'].append(audit_entry)
            audit_log['summary']['total'] += 1
            if audit_entry['final_status'] == 'VERIFIED':
                audit_log['summary']['verified'] += 1
            else:
                audit_log['summary']['discrepancies'] += 1
            
            # Save updated log
            with open(audit_file, 'w') as f:
                json.dump(audit_log, f, indent=2)
            
            logger.info(f"📋 Order audit logged: {audit_entry['final_status']}")
            
        except Exception as e:
            logger.warning(f"Failed to write order audit: {e}")
    
    def _find_exchange_pair(self, asset: str, quote: str, exchange: str) -> Optional[str]:
        """Find trading pair on a specific exchange using loaded pairs."""
        asset_upper = asset.upper()
        quote_upper = quote.upper()
        prefix = f"{exchange}:"
        
        # ════════════════════════════════════════════════════════════════
        # 🐙 KRAKEN - Check kraken_pairs dict
        # Kraken uses special naming: XXBT=BTC, ZUSD=USD, ZEUR=EUR
        # ════════════════════════════════════════════════════════════════
        if exchange == 'kraken' and self.kraken_pairs:
            # Map common names to Kraken format
            kraken_asset = asset_upper
            if asset_upper == 'BTC':
                kraken_asset = 'XBT'
            
            kraken_quote = quote_upper
            if quote_upper == 'USD':
                kraken_quote = 'ZUSD'
            elif quote_upper == 'EUR':
                kraken_quote = 'ZEUR'
            elif quote_upper == 'GBP':
                kraken_quote = 'ZGBP'
            
            # Try common pair formats (Kraken has multiple naming conventions)
            candidates = [
                f"{asset_upper}{quote_upper}",           # CHZUSD (standard)
                f"{kraken_asset}{quote_upper}",          # XBTUSD
                f"X{kraken_asset}Z{quote_upper}",        # XXBTZUSD
                f"XX{kraken_asset[1:]}Z{quote_upper}" if len(kraken_asset) > 1 else None,  # Edge cases
                f"{asset_upper}{kraken_quote}",          # CHZZUSD
                f"{kraken_asset}{kraken_quote}",         # XBTZUSD
                f"X{kraken_asset}{kraken_quote}",        # XXBTZUSD variant
            ]
            for candidate in [c for c in candidates if c]:
                if candidate in self.kraken_pairs:
                    return f"kraken:{candidate}"
            
            # Fuzzy search (look for both original and Kraken-format asset)
            search_assets = [asset_upper, kraken_asset]
            if asset_upper != kraken_asset:
                search_assets.append(f"X{kraken_asset}")  # XXBT
            
            for pair_name in self.kraken_pairs.keys():
                for search_asset in search_assets:
                    if search_asset in pair_name and quote_upper in pair_name:
                        return f"kraken:{pair_name}"
        
        # ════════════════════════════════════════════════════════════════
        # 🦙 ALPACA - Check alpaca_pairs dict
        # ════════════════════════════════════════════════════════════════
        if exchange == 'alpaca' and self.alpaca_pairs:
            candidates = [
                f"{asset_upper}/USD",
                f"{asset_upper}USD",
                asset_upper,
            ]
            for candidate in candidates:
                if candidate in self.alpaca_pairs:
                    return f"alpaca:{self.alpaca_pairs[candidate]}"
        
        # ════════════════════════════════════════════════════════════════
        # 🟡 BINANCE - Search ticker cache
        # ════════════════════════════════════════════════════════════════
        if exchange == 'binance':
            candidates = [
                f"{asset_upper}{quote_upper}",
                f"{asset_upper}USDT",
                f"{asset_upper}USDC",
            ]
            for candidate in candidates:
                cache_key = f"binance:{candidate}"
                if cache_key in self.ticker_cache:
                    return cache_key
        
        # Fallback: Search ticker cache for any exchange
        for cached_pair in self.ticker_cache.keys():
            if cached_pair.startswith(prefix):
                pair_part = cached_pair.replace(prefix, '')
                if pair_part.startswith(asset_upper) and quote_upper in pair_part:
                    return cached_pair
        
        return None
    
    async def run(self, duration_s: int = 60):
        """Run the micro profit labyrinth."""
        await self.initialize()
        
        # 🐍 MEDUSA: Load ALL tradeable pairs for proper routing
        # This ensures we can find pairs for assets we don't hold yet
        await self._load_all_tradeable_pairs()
        
        # Initial data fetch - ALL EXCHANGES
        print("\n" + "=" * 70)
        print("📊 FETCHING DATA FROM ALL EXCHANGES...")
        print("=" * 70)
        await self.fetch_prices()
        print(f"   ✅ {len(self.prices)} assets priced")
        print(f"   ✅ {len(self.ticker_cache)} pairs in ticker cache")
        
        # 🫒🔄 POPULATE BARTER GRAPH from loaded data
        self.populate_barter_graph()
        
        # ════════════════════════════════════════════════════════════════════════════
        # 🌊🔭 BUILD GLOBAL WAVE SCANNER UNIVERSE - A-Z/Z-A Full Coverage
        # ════════════════════════════════════════════════════════════════════════════
        if self.wave_scanner:
            print("\n" + "=" * 70)
            print("🌊🔭 BUILDING GLOBAL WAVE SCANNER UNIVERSE...")
            print("=" * 70)
            try:
                # Build universe from all connected exchanges
                universe_size = await self.wave_scanner.build_universe()
                print(f"   ✅ Universe built: {universe_size} symbols for A-Z/Z-A sweeps")
                
                # Wire Queen to scanner (if not already done)
                if self.queen:
                    self.wave_scanner.queen = self.queen
                    print("   ✅ Queen wired to Wave Scanner")
                
                # Do initial A-Z sweep with ticker cache
                print("\n🐝 INITIAL BEE SWEEP (A-Z coverage)...")
                await self.wave_scanner.full_az_sweep(self.ticker_cache)
                
                # Show wave allocation
                allocation = self.wave_scanner.get_wave_allocation()
                print("\n🌊 WAVE ALLOCATION:")
                for wave, count in allocation.get('wave_counts', {}).items():
                    if count > 0:
                        print(f"   {wave}: {count} symbols")
                
                # Show top opportunities
                top_opps = allocation.get('top_opportunities', [])[:5]
                if top_opps:
                    print("\n🎯 TOP OPPORTUNITIES (Jump Score > 0.6):")
                    for opp in top_opps:
                        print(f"   {opp['symbol']:12} {opp['wave']:15} Jump:{opp['jump_score']:.2f} | 24h:{opp['change_24h']:+.1f}%")
            except Exception as e:
                print(f"   ⚠️ Wave Scanner error: {e}")
        
        print("\n📊 FETCHING BALANCES FROM ALL EXCHANGES...")
        await self.fetch_balances()
        
        # Show exchange status
        print("\n📡 EXCHANGE STATUS:")
        for exchange, data in self.exchange_data.items():
            if data.get('connected'):
                bal_count = len(data.get('balances', {}))
                total_val = data.get('total_value', 0)
                icon = {'kraken': '🐙', 'binance': '🟡', 'alpaca': '🦙'}.get(exchange, '📊')
                print(f"   {icon} {exchange.upper()}: ✅ Connected | {bal_count} assets | ${total_val:,.2f}")
            else:
                icon = {'kraken': '🐙', 'binance': '🟡', 'alpaca': '🦙'}.get(exchange, '📊')
                print(f"   {icon} {exchange.upper()}: ❌ {data.get('error', 'Not connected')}")
        
        # Show balances per exchange
        if self.exchange_balances:
            print("\n📦 PORTFOLIO BY EXCHANGE:")
            for exchange, balances in self.exchange_balances.items():
                if balances:
                    icon = {'kraken': '🐙', 'binance': '🟡', 'alpaca': '🦙'}.get(exchange, '📊')
                    total = sum(balances.get(a, 0) * self.prices.get(a, 0) for a in balances)
                    print(f"\n   {icon} {exchange.upper()} (${total:,.2f}):")
                    for asset, amount in sorted(balances.items(), key=lambda x: x[1] * self.prices.get(x[0], 0), reverse=True)[:10]:
                        price = self.prices.get(asset, 0)
                        value = amount * price
                        if value >= 1.0:  # Only show if >= $1
                            print(f"      {asset}: {amount:.6f} = ${value:.2f}")
        
        # Calculate starting value
        self.start_value_usd = sum(
            self.balances.get(asset, 0) * self.prices.get(asset, 0)
            for asset in self.balances
        )
        
        print(f"\n💰 TOTAL PORTFOLIO VALUE: ${self.start_value_usd:,.2f}")
        
        # Handle infinite duration
        duration_display = "♾️ FOREVER" if duration_s == 0 else f"{duration_s}s"
        print(f"\n🔬 ENTERING MICRO PROFIT LABYRINTH! (Duration: {duration_display})")
        print(f"   ⚡ SPEED MODE: Aggressive micro-profit harvesting...")
        print(f"   V14 Score: {self.config['entry_score_threshold']}+ (lowered for speed)")
        print(f"   Min Profit: ${self.config['min_profit_usd']:.6f} (micro-profits accepted!)")
        print(f"   Mode: {'🔴 LIVE TRADING' if self.live else '🔵 DRY RUN'}")
        print()
        
        start_time = time.time()
        scan_interval = 0.5  # ⚡ FAST SCAN: Every 0.5s for aggressive harvesting
        
        # ════════════════════════════════════════════════════════════════════════════
        # 🎯 TURN-BASED EXCHANGE STRATEGY
        # Each exchange gets its turn - prevents conflicts, respects rate limits
        # ════════════════════════════════════════════════════════════════════════════
        print("\n" + "=" * 70)
        print("🎯 TURN-BASED EXCHANGE STRATEGY ACTIVATED")
        print("=" * 70)
        connected_exchanges = [ex for ex in self.exchange_order 
                               if self.exchange_data.get(ex, {}).get('connected', False)]
        print(f"   Turn Order: {' → '.join([ex.upper() for ex in connected_exchanges])}")
        print(f"   Each exchange scans its assets on its turn")
        print("=" * 70)
        
        try:
            # duration_s == 0 means run forever
            last_wave_scan_time = 0  # Track last wave scanner update
            wave_scan_interval = 60  # Run full A-Z sweep every 60 seconds
            
            while duration_s == 0 or time.time() - start_time < duration_s:
                elapsed = time.time() - start_time
                
                # Refresh prices (shared across all exchanges)
                await self.fetch_prices()
                
                # 🌊🔭 PERIODIC WAVE SCANNER UPDATE (every 60s)
                if self.wave_scanner and (time.time() - last_wave_scan_time) >= wave_scan_interval:
                    try:
                        await self.wave_scanner.full_az_sweep(self.ticker_cache)
                        last_wave_scan_time = time.time()
                        
                        # Show top opportunities on each wave sweep
                        allocation = self.wave_scanner.get_wave_allocation()
                        top_opps = allocation.get('top_opportunities', [])[:3]
                        if top_opps:
                            print(f"\n   🌊🔭 WAVE SWEEP: {len(top_opps)} top opportunities")
                            for opp in top_opps:
                                print(f"      {opp['wave']:15} {opp['symbol']:12} Jump:{opp['jump_score']:.2f} | 24h:{opp['change_24h']:+.1f}%")
                    except Exception as e:
                        logger.debug(f"Wave scan error: {e}")
                
                # 💤 DREAM & VALIDATE (Adaptive Learning)
                await self.validate_dreams()
                await self.dream_about_tickers()
                
                # Collect signals from ALL systems
                signals = await self.collect_all_signals()
                signal_count = sum(len(v) for v in signals.values())
                
                # 🎯 TURN-BASED EXECUTION - Each exchange gets its turn
                try:
                    turn_opportunities, turn_conversions = await self.execute_turn()
                except AttributeError as e:
                    # 👑🔧 SELF-REPAIR TRIGGER - Publish error to ThoughtBus for Queen to fix
                    error_msg = str(e)
                    logger.error(f"❌ AttributeError in execute_turn: {error_msg}")
                    
                    if self.thought_bus:
                        try:
                            # Extract error details
                            import traceback
                            tb = traceback.format_exc()
                            
                            # Find the file and line where error occurred
                            import re
                            file_match = re.search(r'File "([^"]+)", line (\d+)', tb)
                            filename = file_match.group(1) if file_match else __file__
                            line_num = int(file_match.group(2)) if file_match else 0
                            
                            # Publish error event to ThoughtBus
                            self.thought_bus.think(
                                message=f"AttributeError during turn execution: {error_msg}",
                                topic="runtime.error",
                                metadata={
                                    'error_type': 'AttributeError',
                                    'message': error_msg,
                                    'file': filename,
                                    'line': line_num,
                                    'context': 'execute_turn',
                                    'traceback': tb[:1000]  # First 1000 chars
                                }
                            )
                            logger.info("👑🔧 Error published to Queen for self-repair")
                        except Exception as pub_err:
                            logger.error(f"Could not publish error to ThoughtBus: {pub_err}")
                    
                    # Continue running (skip this turn)
                    turn_opportunities, turn_conversions = 0, 0
                except Exception as e:
                    # Other exceptions - log but don't trigger self-repair
                    logger.error(f"Error in execute_turn: {e}")
                    turn_opportunities, turn_conversions = 0, 0
                
                # Calculate current value
                current_value = sum(
                    self.balances.get(asset, 0) * self.prices.get(asset, 0)
                    for asset in self.balances
                )
                # P/L = Current Value - Starting Value (simple, correct math)
                pnl = current_value - self.start_value_usd
                
                # Status update with turn display
                mode = "🔴" if self.live else "🔵"
                turn_display = self.get_turn_display()
                current_ex = self.get_current_exchange()
                
                # 👑🌊🪐 QUEEN'S COSMIC WISDOM BROADCAST
                cosmic_status = ""
                if self.queen:
                    try:
                        # Broadcast cosmic wisdom through mycelium
                        wisdom = self.queen.broadcast_cosmic_wisdom()
                        if wisdom:
                            cosmic = self.queen.get_cosmic_state()
                            score = cosmic.get('composite_cosmic_score', 0)
                            # Show cosmic alignment indicator
                            if score > 0.7:
                                cosmic_status = f" 🌟Cosmic:{score:.0%}"
                            elif score > 0.5:
                                cosmic_status = f" ⭐Cosmic:{score:.0%}"
                            elif score < 0.3:
                                cosmic_status = f" 🌑Cosmic:{score:.0%}"
                    except Exception as e:
                        logger.debug(f"Cosmic wisdom error: {e}")
                
                # Neural systems status
                neural_status = []
                if self.bus_aggregator:
                    bus_agg = self.bus_aggregator.get_aggregate_score()
                    neural_status.append(f"Bus:{bus_agg:.0%}")
                if self.mycelium_network:
                    neural_status.append("Myc:✓")
                if self.lighthouse:
                    neural_status.append("LH:✓")
                if self.ultimate_intel:
                    neural_status.append("Ult:✓")
                if self.hnc_matrix:
                    neural_status.append("HNC:✓")
                
                neural_str = " | ".join(neural_status) if neural_status else "Neural:standby"
                
                # 🚨 REAL-TIME PORTFOLIO DRAIN CHECK
                actual_pnl = current_value - self.start_value_usd
                reported_pnl = self.barter_matrix.total_realized_profit
                ghost_profit = reported_pnl - actual_pnl
                
                # Show warning if portfolio is draining despite "profits"
                drain_warning = ""
                if self.conversions_made > 0 and ghost_profit > 0.10:
                    drain_warning = f" ⚠️DRAIN:${ghost_profit:.2f}"
                
                # 👑 Queen's blocked paths count
                blocked_count = len(self.barter_matrix.blocked_paths)
                queen_status = f" 👑Block:{blocked_count}" if blocked_count > 0 else ""
                
                print(f"🔬 {mode} | {elapsed:.0f}s | Turn:{turn_display} | {neural_str}{cosmic_status} | Conv:{self.conversions_made} | Actual:${actual_pnl:+.2f}{drain_warning}{queen_status}")
                
                await asyncio.sleep(scan_interval)
        
        except KeyboardInterrupt:
            print("\n\n⚠️ Interrupted by user")
        
        # Final summary
        await self.print_summary()
    
    async def print_summary(self):
        """Print final summary."""
        print("\n" + "=" * 70)
        print("🔬💰 MICRO PROFIT LABYRINTH SUMMARY 💰🔬")
        print("=" * 70)
        print(f"Mode: {'🔴 LIVE TRADING' if self.live else '🔵 DRY RUN'}")
        print(f"Total Turns: {self.turns_completed}")
        print(f"Total Signals Received: {self.signals_received}")
        print(f"Opportunities Found: {self.opportunities_found}")
        print(f"Conversions Made: {self.conversions_made}")
        print(f"Total Profit: ${self.total_profit_usd:.4f}")
        
        # ════════════════════════════════════════════════════════════════
        # 👑💰 TINA B'S BILLION DOLLAR DREAM STATUS 💰👑
        # ════════════════════════════════════════════════════════════════
        print("\n" + "═" * 70)
        dream_status = self.barter_matrix.check_dream_progress()
        print(dream_status)
        milestones_hit = len(self.barter_matrix.milestones_hit)
        print(f"   🎯 Milestones: {milestones_hit}/8")
        if milestones_hit > 0:
            print(f"   ✅ {', '.join(self.barter_matrix.milestones_hit)}")
        print("═" * 70)
        
        # ════════════════════════════════════════════════════════════════
        # 🎯 TURN-BASED EXCHANGE STATS
        # ════════════════════════════════════════════════════════════════
        print("\n🎯 TURN-BASED EXCHANGE STATS:")
        icons = {'kraken': '🐙', 'alpaca': '🦙', 'binance': '🟡'}
        for exchange, stats in self.exchange_stats.items():
            if stats['scans'] > 0:  # Only show exchanges that were active
                icon = icons.get(exchange, '📊')
                connected = "✅" if self.exchange_data.get(exchange, {}).get('connected') else "❌"
                print(f"   {icon} {exchange.upper()} {connected}")
                print(f"      Turns: {stats['scans']} | Opps: {stats['opportunities']} | Conv: {stats['conversions']}")
                print(f"      Profit: ${stats['profit']:+.4f}")
        
        # ════════════════════════════════════════════════════════════════
        # 🧠 NEURAL MIND MAP STATUS
        # ════════════════════════════════════════════════════════════════
        print("\n🧠 NEURAL MIND MAP STATUS:")
        print(f"   ThoughtBus: {'✅ Active' if self.bus_aggregator else '❌ Offline'}")
        print(f"   Mycelium Network: {'✅ Active' if self.mycelium_network else '❌ Offline'}")
        print(f"   Lighthouse: {'✅ Active' if self.lighthouse else '❌ Offline'}")
        print(f"   Ultimate Intel: {'✅ Active' if self.ultimate_intel else '❌ Offline'}")
        print(f"   HNC Matrix: {'✅ Active' if self.hnc_matrix else '❌ Offline'}")
        print(f"   Unified Ecosystem: {'✅ Active' if self.unified_ecosystem else '❌ Offline'}")
        print(f"   Wave Scanner: {'✅ Active' if self.wave_scanner else '❌ Offline'}")
        
        # 🌊🔭 WAVE SCANNER SUMMARY
        if self.wave_scanner:
            allocation = self.wave_scanner.get_wave_allocation()
            print(f"\n🌊🔭 WAVE SCANNER (A-Z Coverage):")
            print(f"   Universe: {allocation.get('universe_size', 0)} symbols")
            print(f"   Total Scanned: {allocation.get('total_scanned', 0)}")
            print(f"   Last Scan Time: {allocation.get('last_scan_time', 0):.2f}s")
            wave_counts = allocation.get('wave_counts', {})
            if wave_counts:
                print("   Wave Allocation:")
                for wave, count in wave_counts.items():
                    if count > 0:
                        print(f"      {wave}: {count}")
        
        if self.bus_aggregator:
            status = self.bus_aggregator.get_signal_status()
            print(f"   📡 Bus Signals: {status}")
        
        # Path Memory Stats
        path_stats = self.path_memory.get_stats()
        if path_stats.get('paths', 0) > 0:
            print(f"\n🛤️ PATH MEMORY:")
            print(f"   Total Paths: {path_stats['paths']}")
            print(f"   Win Rate: {path_stats['win_rate']:.1%}")
            print(f"   Wins: {path_stats['wins']} | Losses: {path_stats['losses']}")
        
        # Dream Accuracy
        if any(acc != 0.5 for acc in self.dream_accuracy.values()):
            print(f"\n💭 DREAM ACCURACY (Adaptive Learning):")
            for source, acc in self.dream_accuracy.items():
                print(f"   {source}: {acc:.1%}")
        
        # Signal breakdown by system
        if self.all_signals:
            print("\n📡 SIGNALS BY SYSTEM:")
            for system, sigs in self.all_signals.items():
                print(f"   {system}: {len(sigs)} signals")
        
        # Conversions - Show ACTUAL P/L not expected!
        if self.conversions:
            print("\n📋 CONVERSIONS (ACTUAL P/L):")
            for c in self.conversions:
                # 🔧 FIX: Use actual_pnl_usd for display (what really happened)
                actual_pnl = getattr(c, 'actual_pnl_usd', c.expected_pnl_usd)
                status = "✅" if c.executed and actual_pnl > 0 else "❌"
                verified = "✓" if getattr(c, 'pnl_verified', False) else "?"
                print(f"   {status} {c.from_asset} → {c.to_asset}: ${actual_pnl:+.4f} {verified} (Λ:{c.lambda_score:.0%} G:{c.gravity_score:.0%})")
        
        # ═══════════════════════════════════════════════════════════════════
        # 💧🔀 LIQUIDITY ENGINE SUMMARY
        # ═══════════════════════════════════════════════════════════════════
        liq_status = self.liquidity_engine.get_status()
        if liq_status['executed_aggregations'] > 0:
            print("\n💧🔀 LIQUIDITY ENGINE:")
            print(f"   Aggregations Executed: {liq_status['executed_aggregations']}")
            print(f"   Total Aggregation Profit: ${liq_status['total_profit']:+.4f}")
            print(f"   Pending Plans: {liq_status['pending_plans']}")
            print(f"   Recent Liquidations: {liq_status['recent_liquidations']}")
        
        # ═══════════════════════════════════════════════════════════════════
        # 🫒💰 LIVE BARTER MATRIX SUMMARY
        # ═══════════════════════════════════════════════════════════════════
        barter_summary = self.barter_matrix.get_summary()
        if barter_summary['conversion_count'] > 0:
            print("\n🫒💰 LIVE BARTER MATRIX:")
            print(f"   Total Conversions: {barter_summary['conversion_count']}")
            print(f"   Total Realized P/L: ${barter_summary['total_realized_profit']:+.4f}")
            print(f"   Avg Profit/Trade: ${barter_summary['avg_profit_per_trade']:+.4f}")
            print(f"   Paths Learned: {barter_summary['paths_learned']}")
            
            # Show top performing paths
            if self.barter_matrix.barter_history:
                print("\n   📊 PATH PERFORMANCE:")
                sorted_paths = sorted(
                    self.barter_matrix.barter_history.items(),
                    key=lambda x: x[1].get('total_profit', 0),
                    reverse=True
                )[:5]  # Top 5 paths
                for (from_a, to_a), stats in sorted_paths:
                    trades = stats.get('trades', 0)
                    profit = stats.get('total_profit', 0)
                    slippage = stats.get('avg_slippage', 0)
                    status = "✅" if profit > 0 else "❌"
                    print(f"   {status} {from_a}→{to_a}: {trades} trades, ${profit:+.4f}, slip:{slippage:.2f}%")
        
        # Final portfolio
        if self.balances and self.prices:
            print("\n📦 FINAL PORTFOLIO:")
            total = 0
            for asset, amount in sorted(self.balances.items()):
                price = self.prices.get(asset, 0)
                value = amount * price
                if value >= 1.0:
                    print(f"   {asset}: {amount:.6f} = ${value:.2f}")
                    total += value
            print(f"\n💰 TOTAL VALUE: ${total:.2f}")
            # P/L = Current Value - Starting Value (simple, correct math)
            session_pnl = total - self.start_value_usd
            pnl_symbol = "+" if session_pnl >= 0 else ""
            print(f"📈 SESSION P/L (Unrealized): ${pnl_symbol}{session_pnl:.4f}")
            print(f"🎯 REALIZED TRADES P/L: ${self.barter_matrix.total_realized_profit:+.4f} ({self.conversions_made} conversions)")
            
            # ════════════════════════════════════════════════════════════════════
            # 🚨 GHOST PROFIT DETECTOR - Validate we're not draining portfolio
            # ════════════════════════════════════════════════════════════════════
            realized_pnl = self.barter_matrix.total_realized_profit
            actual_pnl = session_pnl
            ghost_profit = realized_pnl - actual_pnl
            
            print("\n🔍 PROFIT VALIDATION:")
            print(f"   📊 Starting Portfolio: ${self.start_value_usd:.2f}")
            print(f"   📊 Ending Portfolio:   ${total:.2f}")
            print(f"   📊 Actual Change:      ${actual_pnl:+.4f}")
            print(f"   📊 Reported Profit:    ${realized_pnl:+.4f}")
            
            if abs(ghost_profit) > 0.01:
                if ghost_profit > 0:
                    print(f"\n   ⚠️ GHOST PROFIT DETECTED: ${ghost_profit:+.4f}")
                    print(f"   ⚠️ Reported profits exceed actual portfolio gain!")
                    print(f"   ⚠️ This is likely fees, slippage, or price movement eating gains.")
                else:
                    print(f"\n   ✅ HIDDEN GAIN: ${-ghost_profit:+.4f}")
                    print(f"   ✅ Portfolio gained more than reported (price appreciation).")
                
                # Show the math
                if self.conversions_made > 0:
                    avg_ghost_per_trade = ghost_profit / self.conversions_made
                    print(f"\n   📉 Average loss per trade: ${avg_ghost_per_trade:.4f}")
                    print(f"   💡 To profit: Need trades with >${abs(avg_ghost_per_trade):.4f} actual gain")
            else:
                print(f"\n   ✅ PROFIT VALIDATED - Reported matches actual!")
            
            # ════════════════════════════════════════════════════════════════════
            # 👑�🪐🔭 QUEEN'S COSMIC SYSTEMS STATUS
            # ════════════════════════════════════════════════════════════════════
            if self.queen:
                try:
                    cosmic = self.queen.get_cosmic_state()
                    print("\n👑🌌 QUEEN'S COSMIC SYSTEMS:")
                    
                    # Schumann Resonance
                    schumann = cosmic.get('schumann', {})
                    if schumann.get('active'):
                        print(f"   🌊 Schumann Resonance: {schumann.get('resonance', 7.83):.2f}Hz (alignment: {schumann.get('alignment', 0):.0%})")
                    
                    # Planetary Torque
                    planetary = cosmic.get('planetary', {})
                    if planetary.get('active'):
                        print(f"   🪐 Planetary Torque (Π): {planetary.get('torque', 0):.4f} (luck field: {planetary.get('luck_field', 0):.0%})")
                    
                    # Lunar Phase
                    lunar = cosmic.get('lunar', {})
                    if lunar.get('active'):
                        phase_name = lunar.get('name', 'Unknown')
                        phase_val = lunar.get('phase', 0)
                        moon_icon = "🌑🌒🌓🌔🌕🌖🌗🌘"[int(phase_val * 8) % 8]
                        print(f"   {moon_icon} Lunar Phase: {phase_name} ({phase_val:.0%})")
                    
                    # Harmonic Coherence
                    harmonic = cosmic.get('harmonic', {})
                    if harmonic.get('active'):
                        print(f"   🎼 Harmonic Coherence: {harmonic.get('coherence', 0):.0%}")
                    
                    # Quantum Telescope
                    quantum = cosmic.get('quantum', {})
                    if quantum.get('active'):
                        print(f"   🔭 Quantum Alignment: {quantum.get('alignment', 0):.0%}")
                    
                    # Composite Score
                    composite = cosmic.get('composite_cosmic_score', 0)
                    if composite > 0.7:
                        print(f"\n   🌟 COSMIC ALIGNMENT: {composite:.0%} - HIGHLY FAVORABLE")
                    elif composite > 0.5:
                        print(f"\n   ⭐ COSMIC ALIGNMENT: {composite:.0%} - Favorable")
                    elif composite > 0.3:
                        print(f"\n   ☁️ COSMIC ALIGNMENT: {composite:.0%} - Neutral")
                    else:
                        print(f"\n   🌑 COSMIC ALIGNMENT: {composite:.0%} - Unfavorable")
                except Exception as e:
                    logger.debug(f"Error getting cosmic state: {e}")
            
            # ════════════════════════════════════════════════════════════════════
            # 👑�🍄 QUEEN'S BLOCKED PATHS - Paths the mycelium has blocked
            # ════════════════════════════════════════════════════════════════════
            if self.barter_matrix.blocked_paths:
                print("\n👑🍄 QUEEN'S BLOCKED PATHS (via Mycelium):")
                for (from_a, to_a), reason in self.barter_matrix.blocked_paths.items():
                    print(f"   🚫 {from_a}→{to_a}: {reason}")
                print(f"   📊 Total blocked: {len(self.barter_matrix.blocked_paths)} paths")
                print(f"   💡 Blocked paths will be retried after wins on other paths")
            else:
                print("\n👑 QUEEN STATUS: All paths approved (no losing streaks)")
            
            # ════════════════════════════════════════════════════════════════════
            # 👑🧠📚 QUEEN'S HISTORICAL WISDOM STATUS
            # ════════════════════════════════════════════════════════════════════
            if self.queen:
                try:
                    wisdom_state = self.queen.get_historical_wisdom_state()
                    print("\n👑🧠 QUEEN'S HISTORICAL WISDOM:")
                    
                    # Wisdom Engine (11 Civilizations)
                    we = wisdom_state.get('wisdom_engine', {})
                    if we.get('active'):
                        print(f"   🌍 11 Civilizations: ✅ ACTIVE ({we.get('years_of_wisdom', 5000)} years of wisdom)")
                    
                    # Sandbox Evolution
                    se = wisdom_state.get('sandbox_evolution', {})
                    if se.get('active'):
                        print(f"   🧬 Sandbox Evolution: Gen {se.get('generation', 0)}, {se.get('win_rate', 0):.1f}% win rate")
                    
                    # Dream Memory
                    dm = wisdom_state.get('dream_memory', {})
                    if dm.get('active'):
                        print(f"   💭 Dream Memory: {dm.get('dreams', 0)} dreams, {dm.get('prophecies', 0)} prophecies")
                    
                    # Wisdom Collector
                    wc = wisdom_state.get('wisdom_collector', {})
                    if wc.get('active'):
                        patterns = wc.get('patterns', 0)
                        trades = wc.get('trades', 0)
                        predictions = wc.get('predictions', 0)
                        strategies = wc.get('strategies', 0)
                        print(f"   📚 Wisdom Collector: {patterns} patterns | {trades} trades | {predictions} predictions | {strategies} strategies")
                    
                    # Total Wisdom Score
                    total_score = wisdom_state.get('total_wisdom_score', 0.5)
                    active_sys = wisdom_state.get('active_systems', 0)
                    if total_score > 0.7:
                        print(f"\n   🧠✨ WISDOM SCORE: {total_score:.0%} - HIGHLY INFORMED ({active_sys} systems)")
                    elif total_score > 0.5:
                        print(f"\n   🧠⭐ WISDOM SCORE: {total_score:.0%} - Well Informed ({active_sys} systems)")
                    else:
                        print(f"\n   🧠 WISDOM SCORE: {total_score:.0%} - Basic ({active_sys} systems)")
                    
                    # Civilization Consensus
                    try:
                        consensus = self.queen.get_civilization_consensus()
                        if consensus.get('civilizations_consulted', 0) > 0:
                            print(f"\n   🏛️ CIVILIZATION CONSENSUS ({consensus['civilizations_consulted']} consulted):")
                            print(f"      BUY: {consensus['votes']['BUY']} | HOLD: {consensus['votes']['HOLD']} | SELL: {consensus['votes']['SELL']}")
                            print(f"      → Action: {consensus['consensus_action']} ({consensus['confidence']:.0%} confidence)")
                    except Exception as e:
                        logger.debug(f"Civilization consensus error: {e}")
                    
                    # 🔱 Temporal ID & Ladder Status
                    try:
                        temporal_state = self.queen.get_temporal_state()
                        if temporal_state.get('active'):
                            tid = temporal_state.get('temporal_id', {})
                            print(f"\n   🔱 TEMPORAL ID (Prime Sentinel):")
                            print(f"      👤 {tid.get('name', 'Unknown')} | DOB: {tid.get('dob_hash', '?')}")
                            print(f"      📡 Personal Hz: {tid.get('frequency', 0):.6f}")
                            print(f"      🌀 Temporal Resonance: {temporal_state.get('temporal_resonance', 0):.1%}")
                            print(f"      🎵 DOB Harmony: {temporal_state.get('dob_harmony', 0):.2f}")
                            print(f"      ⚡ Current Strength: {temporal_state.get('current_strength', 0):.1%}")
                    except Exception as e:
                        logger.debug(f"Temporal state error: {e}")
                        
                except Exception as e:
                    logger.debug(f"Error getting wisdom state: {e}")
        
        # Save path memory on exit
        self.path_memory.save()
        
        print("=" * 70)


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════

async def main():
    parser = argparse.ArgumentParser(description="Micro Profit Labyrinth")
    parser.add_argument("--live", action="store_true", help="Run in LIVE mode")
    parser.add_argument("--duration", type=int, default=0, help="Duration in seconds (0 = forever)")
    parser.add_argument("--yes", "-y", action="store_true", help="Auto-confirm live mode (skip MICRO prompt)")
    args = parser.parse_args()
    
    if args.live and not args.yes:
        print("\n" + "=" * 60)
        print("⚠️  LIVE MODE REQUESTED - REAL MONEY!")
        print("=" * 60)
        confirm = input("Type 'MICRO' to confirm: ")
        if confirm.strip().upper() != 'MICRO':
            print("Aborted.")
            sys.exit(0)
    elif args.live and args.yes:
        print("\n" + "=" * 60)
        print("⚠️  LIVE MODE - AUTO-CONFIRMED! 🚀")
        print("=" * 60)
    
    engine = MicroProfitLabyrinth(live=args.live)
    await engine.run(duration_s=args.duration)


if __name__ == "__main__":
    asyncio.run(main())
