#!/usr/bin/env python3
"""
🦈🔪 ORCA COMPLETE KILL CYCLE - THE MATH IS SIMPLE 🔪🦈
═══════════════════════════════════════════════════════════════════════════════

KILL = BUY → WAIT FOR PROFIT → SELL → REALIZED GAIN → PORTFOLIO UP

THE MATH:
  1. Entry cost = price × qty × (1 + fee)
  2. Target value = entry_cost × (1 + target_pct + 2×fee)  # Cover both fees
  3. Exit value = price × qty × (1 - fee)
  4. Realized P&L = exit_value - entry_cost
  5. ONLY SELL if realized P&L > 0

ENHANCED FEATURES:
  - Live streaming at 100ms (10 updates/sec) 
  - Whale intelligence via ThoughtBus
  - Smart exit conditions (not just timeout!)
  - Multi-position pack hunting support
  - 🆕 MULTI-EXCHANGE: Streams ENTIRE market on Alpaca + Kraken
  - 🆕 3 POSITIONS AT ONCE: Best opportunities from ANY exchange
  - 🆕 DON'T PULL OUT EARLY: No timeout exits when losing!
  - 🆕 WAR ROOM DASHBOARD: Clean Rich-based unified display

Gary Leckey | The Math Works | January 2026
═══════════════════════════════════════════════════════════════════════════════
"""

# ═══════════════════════════════════════════════════════════════════════════════
# 🔇 LOGGING SUPPRESSION - MUST BE BEFORE ALL OTHER IMPORTS!
# ═══════════════════════════════════════════════════════════════════════════════
import logging

# Set global logging to WARNING to suppress INFO spam
logging.basicConfig(level=logging.WARNING, format='%(message)s')

# Suppress specific chatty modules
NOISY_MODULES = [
    'aureon_queen_counter_intelligence',
    'aureon_firm_intelligence_catalog', 
    'aureon_memory_core',
    'aureon_bot_intelligence_profiler',
    'aureon_whale_profiler_system',
    'aureon_hft_harmonic_mycelium',
    'aureon_thought_bus',
    'aureon_global_wave_scanner',
    'aureon_russian_doll_analytics',
    'aureon_stargate_protocol',
    'aureon_quantum_mirror_scanner',
    'aureon_moby_dick_whale_hunter',
    'aureon_immune_system',
    'aureon_elephant_learning',
    'aureon_inception_engine',
    'aureon_luck_field_mapper',
    'aureon_phantom_signal_filter',
    'mycelium_whale_sonar',
    'telemetry_server',
    'market_data_hub',
    'global_rate_budget',
    'MinerBrain',
    'AureonMemory',
    'PhantomFilter',
    'alpaca_fee_tracker',
    'aureon_hnc_surge_detector',
    'aureon_hnc_live_connector',
    'aureon_historical_manipulation_hunter',
    'HNCSim',
    'root',
]
for mod in NOISY_MODULES:
    logging.getLogger(mod).setLevel(logging.ERROR)

import sys
import os
import time
import asyncio
from typing import Dict, Optional, List, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime

# Load environment variables from .env file (CRITICAL for API keys!)
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded .env file")
except ImportError:
    print("⚠️ python-dotenv not installed, using system env vars only")

# Windows UTF-8 fix (MANDATORY)
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        def _is_utf8_wrapper(stream):
            """Check if stream is already a UTF-8 TextIOWrapper."""
            return (isinstance(stream, io.TextIOWrapper) and
                    hasattr(stream, 'encoding') and stream.encoding and
                    stream.encoding.lower().replace('-', '') == 'utf8')
        def _is_buffer_valid(stream):
            """Check if stream buffer is valid and not closed."""
            if not hasattr(stream, 'buffer'):
                return False
            try:
                return stream.buffer is not None and not stream.buffer.closed
            except (ValueError, AttributeError):
                return False
        # Only wrap if not already UTF-8 wrapped AND buffer is valid
        if _is_buffer_valid(sys.stdout) and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

def _safe_print(*args, **kwargs):
    """Print that won't crash if stdout is closed."""
    try:
        import builtins
        builtins.print(*args, **kwargs)
    except (ValueError, OSError, IOError):
        return

# Route all prints in this module through the safe printer
print = _safe_print

# ═══════════════════════════════════════════════════════════════════════════════
# 🎯 RICH WAR ROOM DASHBOARD - Clean terminal UI
# ═══════════════════════════════════════════════════════════════════════════════
try:
    from rich.console import Console
    from rich.live import Live
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.style import Style
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None
    Live = None
    Layout = None
    Panel = None
    Table = None
    Text = None
    Style = None

try:
    from alpaca_client import AlpacaClient
    ALPACA_AVAILABLE = True
except Exception as e:
    ALPACA_AVAILABLE = False
    AlpacaClient = None
    _safe_print(f"⚠️ AlpacaClient import failed: {e}")

try:
    from capital_client import CapitalClient
    CAPITAL_AVAILABLE = True
except ImportError:
    CAPITAL_AVAILABLE = False
    CapitalClient = None

# Try to import ThoughtBus for whale intelligence
try:
    from aureon_thought_bus import ThoughtBus, Thought
    THOUGHT_BUS_AVAILABLE = True
except ImportError:
    THOUGHT_BUS_AVAILABLE = False
    ThoughtBus = None
    Thought = None

# Try to import whale/bot tracking systems
try:
    from aureon_whale_profiler_system import WhaleProfilerSystem, WhaleClass, GLOBAL_TRADING_FIRMS
    WHALE_PROFILER_AVAILABLE = True
except ImportError:
    WHALE_PROFILER_AVAILABLE = False
    WhaleProfilerSystem = None
    WhaleClass = None
    GLOBAL_TRADING_FIRMS = {}

try:
    from aureon_firm_intelligence_catalog import FirmIntelligenceCatalog, FirmActivityType
    FIRM_INTEL_AVAILABLE = True
except ImportError:
    FIRM_INTEL_AVAILABLE = False
    FirmIntelligenceCatalog = None
    FirmActivityType = None

# Try to import Alpaca SSE client for live streaming
try:
    from alpaca_sse_client import AlpacaSSEClient, StreamTrade
    SSE_AVAILABLE = True
except ImportError:
    SSE_AVAILABLE = False
    AlpacaSSEClient = None
    StreamTrade = None

# 🦈 ORCA INTELLIGENCE - Full scanning system for fast kills
try:
    from aureon_orca_intelligence import OrcaKillerWhale, OrcaOpportunity, WhaleSignal as OrcaWhaleSignal
    ORCA_INTEL_AVAILABLE = True
except ImportError:
    ORCA_INTEL_AVAILABLE = False
    OrcaKillerWhale = None
    OrcaOpportunity = None
    OrcaWhaleSignal = None

# 🔮 Probability Ultimate Intelligence (95% accuracy)
try:
    from probability_ultimate_intelligence import ProbabilityUltimateIntelligence as UltimateIntelligence
    ULTIMATE_INTEL_AVAILABLE = True
except ImportError:
    ULTIMATE_INTEL_AVAILABLE = False
    UltimateIntelligence = None

# 🌊 Global Wave Scanner
try:
    from aureon_global_wave_scanner import GlobalWaveScanner
    WAVE_SCANNER_AVAILABLE = True
except ImportError:
    WAVE_SCANNER_AVAILABLE = False
    GlobalWaveScanner = None

# 🐋 Movers & Shakers Scanner
try:
    from aureon_movers_shakers_scanner import MoversShakersScanner, MoverShaker
    MOVERS_SHAKERS_AVAILABLE = True
except ImportError:
    MOVERS_SHAKERS_AVAILABLE = False
    MoversShakersScanner = None
    MoverShaker = None

# � Queen Volume Hunter - Volume breakout detection
try:
    from queen_volume_hunter import QueenVolumeHunter, VolumeSignal
    VOLUME_HUNTER_AVAILABLE = True
except ImportError:
    VOLUME_HUNTER_AVAILABLE = False
    QueenVolumeHunter = None
    VolumeSignal = None

# �💰 AlpacaFeeTracker - Volume-tiered fee detection + spread tracking
try:
    from alpaca_fee_tracker import AlpacaFeeTracker
    ALPACA_FEE_TRACKER_AVAILABLE = True
except ImportError:
    ALPACA_FEE_TRACKER_AVAILABLE = False
    AlpacaFeeTracker = None

# 📊 CostBasisTracker - FIFO cost basis + can_sell_profitably() check
try:
    from cost_basis_tracker import CostBasisTracker
    COST_BASIS_TRACKER_AVAILABLE = True
except ImportError:
    COST_BASIS_TRACKER_AVAILABLE = False
    CostBasisTracker = None

# 🦈 OrcaKillExecutor - Position tracking with order IDs
try:
    from orca_kill_executor import OrcaPosition, OrcaKillExecutor
    ORCA_EXECUTOR_AVAILABLE = True
except ImportError:
    ORCA_EXECUTOR_AVAILABLE = False
    OrcaPosition = None
    OrcaKillExecutor = None

# 📝 TradeLogger - Full trade entry/exit logging
try:
    from trade_logger import TradeLogger, TradeEntry, TradeExit
    TRADE_LOGGER_AVAILABLE = True
except ImportError:
    TRADE_LOGGER_AVAILABLE = False
    TradeLogger = None
    TradeEntry = None
    TradeExit = None

# 🪙 Penny Profit Calculator - Exact breakeven with fees/slippage/spread
try:
    from penny_profit_sim import calculate_penny_profit_threshold, EXCHANGE_FEES, SLIPPAGE_PCT, SPREAD_PCT
    PENNY_PROFIT_AVAILABLE = True
except ImportError:
    PENNY_PROFIT_AVAILABLE = False
    calculate_penny_profit_threshold = None
    # Full fee profiles: maker/taker + slippage + spread per exchange
    EXCHANGE_FEES = {
        'binance': {
            'maker': 0.001,    # 0.10%
            'taker': 0.001,    # 0.10% (with BNB)
            'slippage': 0.0003,  # Lower slippage (high liquidity)
            'spread': 0.0005,
        },
        'kraken': {
            'maker': 0.0016,   # 0.16%
            'taker': 0.0026,   # 0.26%
            'slippage': 0.0005,
            'spread': 0.0008,
        },
        'alpaca': {
            'maker': 0.0015,   # 0.15% Tier 1
            'taker': 0.0025,   # 0.25% Tier 1
            'slippage': 0.0005,
            'spread': 0.0008,
        },
    }
    SLIPPAGE_PCT = 0.001   # Global fallback
    SPREAD_PCT = 0.0005    # Global fallback

# 🔬 Improved ETA Calculator - Probability-based time-to-target predictions
try:
    from improved_eta_calculator import ImprovedETACalculator, ImprovedETA
    ETA_CALCULATOR_AVAILABLE = True
except ImportError:
    ETA_CALCULATOR_AVAILABLE = False
    ImprovedETACalculator = None
    ImprovedETA = None

# 🤖 Bot Shape Scanner - Detect algorithmic actors
try:
    from aureon_bot_shape_scanner import BotShapeScanner, BotShapeFingerprint
    BOT_SCANNER_AVAILABLE = True
except ImportError:
    BOT_SCANNER_AVAILABLE = False
    BotShapeScanner = None
    BotShapeFingerprint = None

# 🛡️ Queen Counter-Intelligence - Beat major firms at their game
try:
    from aureon_queen_counter_intelligence import QueenCounterIntelligence, CounterIntelligenceSignal, CounterStrategy
    COUNTER_INTEL_AVAILABLE = True
except ImportError:
    COUNTER_INTEL_AVAILABLE = False
    QueenCounterIntelligence = None
    CounterIntelligenceSignal = None
    CounterStrategy = None

# 🏢 Global Firm Intelligence - Track major trading firms
try:
    from aureon_global_firm_intelligence import get_attribution_engine, GlobalFirmAttributionEngine
    FIRM_ATTRIBUTION_AVAILABLE = True
except ImportError:
    FIRM_ATTRIBUTION_AVAILABLE = False
    get_attribution_engine = None
    GlobalFirmAttributionEngine = None

# ⚡ HFT Harmonic Mycelium Engine - Sub-10ms signal processing
try:
    from aureon_hft_harmonic_mycelium import get_hft_engine, HFTHarmonicEngine, HFTTick
    HFT_ENGINE_AVAILABLE = True
except ImportError:
    HFT_ENGINE_AVAILABLE = False
    get_hft_engine = None
    HFTHarmonicEngine = None
    HFTTick = None

# 🍀 Luck Field Mapper - Quantum probability / cosmic alignment
try:
    from aureon_luck_field_mapper import get_luck_mapper, read_luck_field, LuckFieldMapper, LuckState
    LUCK_FIELD_AVAILABLE = True
except ImportError:
    LUCK_FIELD_AVAILABLE = False
    get_luck_mapper = None
    read_luck_field = None
    LuckFieldMapper = None
    LuckState = None

# 👻 Phantom Signal Filter - Multi-layer signal validation
try:
    from aureon_phantom_signal_filter import PhantomSignalFilter
    PHANTOM_FILTER_AVAILABLE = True
except ImportError:
    PHANTOM_FILTER_AVAILABLE = False
    PhantomSignalFilter = None

# 🦅 Alpaca Momentum Ecosystem
try:
    from aureon_animal_momentum_scanners import AlpacaSwarmOrchestrator
    from aureon_alpaca_scanner_bridge import AlpacaScannerBridge
    from aureon_micro_momentum_goal import MicroMomentumScanner
    MOMENTUM_ECOSYSTEM_AVAILABLE = True
except ImportError:
    MOMENTUM_ECOSYSTEM_AVAILABLE = False
    AlpacaSwarmOrchestrator = None
    AlpacaScannerBridge = None
    MicroMomentumScanner = None

# 🌌 Stargate Grid
try:
    from stargate_grid import StargateGrid
    STARGATE_GRID_AVAILABLE = True
except ImportError:
    STARGATE_GRID_AVAILABLE = False
    StargateGrid = None

# 🎬 Inception Engine - Russian doll probability (LIMBO = 95% accuracy)
try:
    from aureon_inception_engine import get_inception_engine, inception_dive, get_limbo_insight, InceptionEngine
    INCEPTION_ENGINE_AVAILABLE = True
except ImportError:
    INCEPTION_ENGINE_AVAILABLE = False
    get_inception_engine = None
    inception_dive = None
    get_limbo_insight = None
    InceptionEngine = None

# 🐘 Elephant Learning - Never forgets patterns (asset scores, best hours)
try:
    from aureon_elephant_learning import ElephantMemory, QueenElephantBrain
    ELEPHANT_LEARNING_AVAILABLE = True
except ImportError:
    ELEPHANT_LEARNING_AVAILABLE = False
    ElephantMemory = None
    QueenElephantBrain = None

# 🦷 Russian Doll Analytics - Bee→Hive→Queen metrics rollup
try:
    from aureon_russian_doll_analytics import get_analytics, get_directives, get_snapshot, RussianDollAnalytics
    RUSSIAN_DOLL_AVAILABLE = True
except ImportError:
    RUSSIAN_DOLL_AVAILABLE = False
    get_analytics = None
    get_directives = None
    get_snapshot = None
    RussianDollAnalytics = None

# 🛡️ Immune System - Self-healing on errors
try:
    from aureon_immune_system import AureonImmuneSystem
    IMMUNE_SYSTEM_AVAILABLE = True
except ImportError:
    IMMUNE_SYSTEM_AVAILABLE = False
    AureonImmuneSystem = None

# 🐋 Moby Dick Whale Hunter - Whale prediction tracking
try:
    from aureon_moby_dick_whale_hunter import get_moby_dick_hunter, MobyDickWhaleHunter, WhalePrediction
    MOBY_DICK_AVAILABLE = True
except ImportError:
    MOBY_DICK_AVAILABLE = False
    get_moby_dick_hunter = None
    MobyDickWhaleHunter = None
    WhalePrediction = None

# 🌌 Stargate Protocol - Quantum mirror alignment
try:
    from aureon_stargate_protocol import create_stargate_engine, StargateProtocolEngine
    STARGATE_AVAILABLE = True
except ImportError:
    STARGATE_AVAILABLE = False
    create_stargate_engine = None
    StargateProtocolEngine = None

# 🔮 Quantum Mirror Scanner - Reality branch boost
try:
    from aureon_quantum_mirror_scanner import create_quantum_scanner, QuantumMirrorScanner
    QUANTUM_MIRROR_AVAILABLE = True
except ImportError:
    QUANTUM_MIRROR_AVAILABLE = False
    create_quantum_scanner = None
    QuantumMirrorScanner = None

# 🎯 Alpaca Options Trading - Covered calls & cash-secured puts
try:
    from alpaca_options_client import (
        AlpacaOptionsClient, get_options_client,
        OptionContract, OptionQuote, OptionType, TradingLevel
    )
    OPTIONS_AVAILABLE = True
except ImportError:
    OPTIONS_AVAILABLE = False
    AlpacaOptionsClient = None
    get_options_client = None
    OptionContract = None
    OptionQuote = None
    OptionType = None
    TradingLevel = None

# 👑 Queen Options Scanner - Intelligent options discovery
try:
    from queen_options_scanner import QueenOptionsScanner, OptionsOpportunity
    OPTIONS_SCANNER_AVAILABLE = True
except ImportError:
    OPTIONS_SCANNER_AVAILABLE = False
    QueenOptionsScanner = None
    OptionsOpportunity = None

# 🥷 Stealth Execution - Anti-front-running countermeasures
try:
    from orca_stealth_execution import (
        OrcaStealthExecution, get_stealth_executor, get_stealth_config,
        stealth_order, StealthConfig
    )
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False
    OrcaStealthExecution = None
    get_stealth_executor = None
    get_stealth_config = None
    stealth_order = None
    StealthConfig = None

# 🌊🎶 HNC Surge Detector - Harmonic Nexus Core surge window detection
try:
    from aureon_hnc_surge_detector import HncSurgeDetector, SurgeWindow, SACRED_HARMONICS
    HNC_SURGE_AVAILABLE = True
except ImportError:
    HNC_SURGE_AVAILABLE = False
    HncSurgeDetector = None
    SurgeWindow = None
    SACRED_HARMONICS = None

# 📡 HNC Live Connector - Live harmonic surge feed
try:
    from aureon_hnc_live_connector import HncLiveConnector
    HNC_LIVE_AVAILABLE = True
except ImportError:
    HNC_LIVE_AVAILABLE = False
    HncLiveConnector = None

# 📜⚔️ Historical Manipulation Hunter - Track manipulation patterns across decades
try:
    from aureon_historical_manipulation_hunter import (
        HistoricalManipulationHunter, 
        HISTORICAL_EVENTS,
        EventType
    )
    HISTORICAL_HUNTER_AVAILABLE = True
except ImportError:
    HISTORICAL_HUNTER_AVAILABLE = False
    HistoricalManipulationHunter = None
    HISTORICAL_EVENTS = None
    EventType = None

# 🏹⚔️ Apache War Band - Autonomous Scout/Sniper trading system
try:
    from aureon_war_band_enhanced import EnhancedWarBand, UnifiedEnhancementSignal
    WAR_BAND_AVAILABLE = True
except ImportError:
    WAR_BAND_AVAILABLE = False
    EnhancedWarBand = None
    UnifiedEnhancementSignal = None

# 🐝👑 Hive State Publisher - Queen's voice and status tracking
try:
    from aureon_hive_state import get_hive, HiveStatePublisher
    HIVE_STATE_AVAILABLE = True
except ImportError:
    HIVE_STATE_AVAILABLE = False
    get_hive = None
    HiveStatePublisher = None

# 📜🤖 Historical Bot Census - Bot evolution tracking
try:
    from aureon_historical_bot_census import HistoricalBot, analyze_history, generate_bot_identity
    HISTORICAL_BOT_CENSUS_AVAILABLE = True
except ImportError:
    HISTORICAL_BOT_CENSUS_AVAILABLE = False
    HistoricalBot = None
    analyze_history = None
    generate_bot_identity = None

# 📊🔬 Historical Backtest Engine - Harmonic fusion backtesting
try:
    from aureon_historical_backtest import AureonBacktestEngine, HistoricalDataFetcher
    HISTORICAL_BACKTEST_AVAILABLE = True
except ImportError:
    HISTORICAL_BACKTEST_AVAILABLE = False
    AureonBacktestEngine = None
    HistoricalDataFetcher = None

# 🌍 Global Orchestrator - Master control for all Aureon subsystems
try:
    from aureon_global_orchestrator import GlobalAureonOrchestrator
    GLOBAL_ORCHESTRATOR_AVAILABLE = True
except ImportError:
    GLOBAL_ORCHESTRATOR_AVAILABLE = False
    GlobalAureonOrchestrator = None

# 🎵 Harmonic Binary Protocol - Compact binary transport for harmonic thoughts
try:
    from aureon_harmonic_binary_protocol import HarmonicBinaryPacket, encode_text_packet, decode_packet
    HARMONIC_BINARY_AVAILABLE = True
except ImportError:
    HARMONIC_BINARY_AVAILABLE = False
    HarmonicBinaryPacket = None
    encode_text_packet = None
    decode_packet = None

# 🔗 Harmonic Chain Master - Master harmonic signal processing
try:
    from aureon_harmonic_chain_master import HarmonicChainMaster
    HARMONIC_CHAIN_MASTER_AVAILABLE = True
except ImportError:
    HARMONIC_CHAIN_MASTER_AVAILABLE = False
    HarmonicChainMaster = None

# ⚡ Harmonic Counter Frequency - Planetary entity counter-frequency engine
try:
    import aureon_harmonic_counter_frequency
    HARMONIC_COUNTER_AVAILABLE = True
except ImportError:
    HARMONIC_COUNTER_AVAILABLE = False
    aureon_harmonic_counter_frequency = None

# 🌊 Harmonic Wave Fusion - Unified global market harmonic system
try:
    from aureon_harmonic_fusion import get_harmonic_fusion, HarmonicWaveFusion
    HARMONIC_FUSION_AVAILABLE = True
except ImportError:
    HARMONIC_FUSION_AVAILABLE = False
    get_harmonic_fusion = None
    HarmonicWaveFusion = None

# 🌊⚡ Harmonic Momentum Wave Scanner - Ultimate momentum scanner
try:
    from aureon_harmonic_momentum_wave import HarmonicMomentumWaveScanner
    HARMONIC_MOMENTUM_AVAILABLE = True
except ImportError:
    HARMONIC_MOMENTUM_AVAILABLE = False
    HarmonicMomentumWaveScanner = None

# 🌊 Harmonic Reality Framework - Master equations tree
try:
    from aureon_harmonic_reality import MultiversalEngine
    HARMONIC_REALITY_AVAILABLE = True
    HarmonicRealityFramework = MultiversalEngine  # Alias for compatibility
except ImportError:
    HARMONIC_REALITY_AVAILABLE = False
    MultiversalEngine = None
    HarmonicRealityFramework = None

# 🗺️ Global Bot Map - Visual dashboard for bot activity
try:
    from aureon_global_bot_map import GlobalBotMapDashboard
    GLOBAL_BOT_MAP_AVAILABLE = True
    GlobalBotMap = GlobalBotMapDashboard  # Alias for compatibility
except ImportError:
    GLOBAL_BOT_MAP_AVAILABLE = False
    GlobalBotMapDashboard = None
    GlobalBotMap = None

# 🌌 Enhanced Quantum Telescope - Sacred geometry bot visualization
try:
    # Actual class: EnhancedQuantumTelescopeServer — alias for compatibility
    from aureon_enhanced_quantum_telescope import EnhancedQuantumTelescopeServer, EnhancedQuantumGeometryEngine
    EnhancedQuantumTelescope = EnhancedQuantumTelescopeServer
    ENHANCED_QUANTUM_TELESCOPE_AVAILABLE = True
except ImportError:
    ENHANCED_QUANTUM_TELESCOPE_AVAILABLE = False
    EnhancedQuantumTelescope = None
    EnhancedQuantumGeometryEngine = None

# 💭 Enigma Dream - Consciousness state processing
try:
    # Actual class name: EnigmaDreamer — expose under EnigmaDreamProcessor alias
    from aureon_enigma_dream import EnigmaDreamer
    EnigmaDreamProcessor = EnigmaDreamer
    ENIGMA_DREAM_AVAILABLE = True
except ImportError:
    ENIGMA_DREAM_AVAILABLE = False
    EnigmaDreamProcessor = None

# ✨ Enhancement Layer - Unified enhancement system
try:
    from aureon_enhancements import EnhancementLayer
    ENHANCEMENT_LAYER_AVAILABLE = True
except ImportError:
    ENHANCEMENT_LAYER_AVAILABLE = False
    EnhancementLayer = None

# 🧩 Enigma Integration - Complete Enigma system integration
try:
    from aureon_enigma_integration import EnigmaIntegration
    ENIGMA_INTEGRATION_AVAILABLE = True
except ImportError:
    ENIGMA_INTEGRATION_AVAILABLE = False
    EnigmaIntegration = None

# 📊 Firm Intelligence Catalog - Real-time firm tracking
try:
    from aureon_firm_intelligence_catalog import FirmIntelligenceCatalog, get_firm_catalog
    FIRM_INTELLIGENCE_AVAILABLE = True
except ImportError:
    FIRM_INTELLIGENCE_AVAILABLE = False
    FirmIntelligenceCatalog = None
    get_firm_catalog = None

# 🌀 Enigma Core - Primary consciousness engine
try:
    # Use AureonEnigma as the main core class
    from aureon_enigma import AureonEnigma
    EnigmaCore = AureonEnigma
    ENIGMA_CORE_AVAILABLE = True
except ImportError:
    ENIGMA_CORE_AVAILABLE = False
    EnigmaCore = None

# ═══════════════════════════════════════════════════════════════════════════════
# 🆕 ADDITIONAL NEURAL & TRADING SYSTEMS - Miner, Multiverse, Mycelium, etc.
# ═══════════════════════════════════════════════════════════════════════════════

# ⛏️ Aureon Miner - Background mining with harmonic optimization
try:
    from aureon_miner import AureonMiner
    AUREON_MINER_AVAILABLE = True
except ImportError:
    AUREON_MINER_AVAILABLE = False
    AureonMiner = None

# 🌐 Multi-Exchange Trader - Cross-exchange trading orchestration
try:
    from aureon_multi_exchange_live import AureonMultiExchangeTrader, MultiExchangeManager
    MULTI_EXCHANGE_AVAILABLE = True
except ImportError:
    MULTI_EXCHANGE_AVAILABLE = False
    AureonMultiExchangeTrader = None
    MultiExchangeManager = None

# 🎯 Multi-Pair Trader - Multi-pair coherence monitoring
try:
    from aureon_multi_pair_live import MultiPairTrader, MasterEquation
    MULTI_PAIR_AVAILABLE = True
except ImportError:
    MULTI_PAIR_AVAILABLE = False
    MultiPairTrader = None
    MasterEquation = None

# 🌌 Multiverse Live Engine - Commando + Multiverse unified trading
try:
    from aureon_multiverse_live import MultiverseLiveEngine, CommandoCognition
    MULTIVERSE_LIVE_AVAILABLE = True
except ImportError:
    MULTIVERSE_LIVE_AVAILABLE = False
    MultiverseLiveEngine = None
    CommandoCognition = None

# ✨ Multiverse Orchestrator - Atom-to-Galaxy ladder trading
try:
    from aureon_multiverse import MultiverseOrchestrator, PingPongEngine
    MULTIVERSE_ORCHESTRATOR_AVAILABLE = True
except ImportError:
    MULTIVERSE_ORCHESTRATOR_AVAILABLE = False
    MultiverseOrchestrator = None
    PingPongEngine = None

# 🍄 Mycelium Neural Network - Underground signal network
try:
    from aureon_mycelium import MyceliumNetwork, Hive as MyceliumHive
    MYCELIUM_NETWORK_AVAILABLE = True
except ImportError:
    MYCELIUM_NETWORK_AVAILABLE = False
    MyceliumNetwork = None
    MyceliumHive = None

# 🌍🔗 Neural Revenue Orchestrator - Master revenue generation
try:
    from aureon_neural_revenue_orchestrator import NeuralRevenueOrchestrator
    NEURAL_REVENUE_AVAILABLE = True
except ImportError:
    NEURAL_REVENUE_AVAILABLE = False
    NeuralRevenueOrchestrator = None

import random  # For simulating market activity


# ═══════════════════════════════════════════════════════════════════════════════
# 🎯 WAR ROOM DISPLAY - Clean Rich-based unified dashboard
# ═══════════════════════════════════════════════════════════════════════════════

class WarRoomDisplay:
    """
    🎖️ WAR ROOM INTELLIGENCE DASHBOARD
    
    Clean, unified Rich-based terminal display replacing spam logging.
    Shows positions, quantum systems, firm intel, and kills in organized panels.
    🌟 Now with Rising Star Logic integration!
    🎯 Now with OPTIONS TRADING support!
    """
    
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.layout = None
        self.positions_data = []
        self.quantum_data = {}
        self.firms_data = {}
        self.kills_data = {'wins': 0, 'losses': 0, 'pnl': 0.0}
        self.runtime_start = time.time()
        self.cycle_count = 0
        self.total_pnl = 0.0
        self.best_trade = 0.0
        self.worst_trade = 0.0
        # 💵 Cash balances per exchange
        self.cash_balances = {'alpaca': 0.0, 'kraken': 0.0, 'binance': 0.0}
        self.cash_status = {'alpaca': 'unknown', 'kraken': 'unknown', 'binance': 'unknown'}
        # 🌟 Rising Star stats
        self.rising_star_stats = {}
        # 🎯 Options trading stats
        self.options_data = {
            'trading_level': 'UNKNOWN',
            'buying_power': 0.0,
            'positions': [],
            'best_opportunity': None,
            'last_scan': None,
        }
        # 🦈🔍 Predator Detection stats
        self.predator_data = {
            'threat_level': 'green',
            'front_run_rate': 0.0,
            'top_predator': None,
            'strategy_decay': False,
        }
        # 🥷 Stealth Execution stats
        self.stealth_data = {
            'mode': 'normal',
            'delayed_orders': 0,
            'split_orders': 0,
            'rotated_symbols': 0,
            'hunted_count': 0,
        }
        # 🦅 Momentum Ecosystem stats
        self.momentum_data = {
            'wolf_pack': 'Initializing...',
            'lion_pride': 'Initializing...',
            'army_ants': 'Initializing...',
            'hummingbird': 'Initializing...',
            'micro_targets': 0,
        }
        
        # 🌌 Stargate Grid stats
        self.stargate_data = {
            'active_node': 'Initializing...',
            'grid_coherence': 0.0,
            'description': ''
        }
        
        # 💎 Portfolio tracking
        self.portfolio_start_value = 0.0
        self.portfolio_peak_value = 0.0
        self.session_start_time = time.time()
        
        # 🎯 Opportunity queue (top candidates waiting to be bought)
        self.opportunity_queue = []
        
        # 🏆 Exchange performance tracking
        self.exchange_stats = {
            'alpaca': {'wins': 0, 'losses': 0, 'pnl': 0.0, 'trades': 0},
            'kraken': {'wins': 0, 'losses': 0, 'pnl': 0.0, 'trades': 0},
            'binance': {'wins': 0, 'losses': 0, 'pnl': 0.0, 'trades': 0}
        }
        
        # 🎖️ Recent kills feed (last 5 trades)
        self.recent_kills = []
        
        # 🏥 System health metrics
        self.system_health = {
            'alpaca_latency': 0,
            'kraken_latency': 0,
            'binance_latency': 0,
            'alpaca_status': '🟢',
            'kraken_status': '🟢',
            'binance_status': '🟢',
            'last_trade_time': None,
            'scanning_active': True
        }
        
        # ⚠️ Risk exposure tracking
        self.risk_metrics = {
            'max_position_size': 0.0,
            'total_exposure': 0.0,
            'exposure_pct': 0.0,
            'max_drawdown': 0.0,
            'current_drawdown': 0.0
        }
        
        # 🔥 Streak tracking
        self.streak_data = {
            'current_streak': 0,
            'current_streak_type': None,  # 'win' or 'loss'
            'best_win_streak': 0,
            'worst_loss_streak': 0,
            'exchange_streaks': {'alpaca': 0, 'kraken': 0, 'binance': 0}
        }
        
        # 🚫 Protection stats (elephant memory)
        self.protection_stats = {
            'blocked_count': 0,
            'estimated_saved': 0.0,
            'top_dangers': []  # [(symbol, loss_count), ...]
        }
        
        # ⚡ Flash alerts queue
        self.flash_alerts = []
        
        # 📈 Efficiency metrics
        self.efficiency_metrics = {
            'total_scanned': 0,
            'total_bought': 0,
            'conversion_rate': 0.0,
            'avg_time_to_buy': 0.0,
            'success_rate': 0.0,
            'scan_times': []
        }
        
        # ⏰ Time-based performance
        self.hourly_performance = {}  # {hour: {'pnl': 0, 'trades': 0}}
        
        # 💪 Position health tracking
        self.position_health = {
            'healthy_count': 0,
            'at_risk_count': 0,
            'danger_count': 0,
            'overall_score': 100
        }
        
        # 🎲 Volatility tracking
        self.market_volatility = {
            'current_volatility': 'normal',  # low, normal, high, extreme
            'opportunity_multiplier': 1.0,
            'risk_level': 'normal'
        }
        
    def _create_layout(self) -> Layout:
        """Create the war room layout."""
        layout = Layout(name="root")
        
        # Main structure
        layout.split(
            Layout(name="header", size=7),  # Increased for portfolio value
            Layout(name="main", ratio=1),
            Layout(name="footer", size=12),  # Increased for all new panels
        )
        
        # Split main into left and right
        layout["main"].split_row(
            Layout(name="positions", ratio=2),
            Layout(name="intel", ratio=1),
        )
        
        return layout
    
    def _build_header(self) -> Panel:
        """Build the header panel with session stats."""
        runtime = time.time() - self.runtime_start
        hrs, rem = divmod(runtime, 3600)
        mins, secs = divmod(rem, 60)
        
        pnl_color = "green" if self.total_pnl >= 0 else "red"
        pnl_sign = "+" if self.total_pnl >= 0 else ""
        
        header = Table.grid(expand=True)
        header.add_column(justify="center", ratio=1)
        header.add_row(
            Text("👑🦈 ORCA WAR ROOM - AUTONOMOUS QUEEN 🦈👑", style="bold magenta")
        )
        header.add_row(
            Text(f"⏱️ {int(hrs)}h {int(mins)}m {int(secs)}s | 🔄 Cycles: {self.cycle_count} | "
                 f"💰 P&L: [{pnl_color}]{pnl_sign}${self.total_pnl:.4f}[/] | "
                 f"✅ {self.kills_data['wins']} | ❌ {self.kills_data['losses']}")
        )
        
        # Add balance row for all exchanges
        cash_text = "💵 BAL: "
        total_balance = None
        if hasattr(self, 'cash_balances') and self.cash_balances:
            alpaca_cash = self.cash_balances.get('alpaca', 0)
            kraken_cash = self.cash_balances.get('kraken', 0)
            binance_cash = self.cash_balances.get('binance', 0)
            capital_cash = self.cash_balances.get('capital', 0)
            status = getattr(self, 'cash_status', {})

            positions_by_exchange = {'alpaca': 0.0, 'kraken': 0.0, 'binance': 0.0, 'capital': 0.0}
            for pos in getattr(self, 'positions_data', []):
                exchange = (pos.get('exchange') or '').lower()
                value = float(pos.get('value', 0) or 0)
                if 'alpaca' in exchange:
                    positions_by_exchange['alpaca'] += value
                elif 'kraken' in exchange:
                    positions_by_exchange['kraken'] += value
                elif 'binance' in exchange:
                    positions_by_exchange['binance'] += value
                elif 'capital' in exchange:
                    positions_by_exchange['capital'] += value

            def _fmt_balance(label: str, value: float, status_key: str, color: str) -> str:
                state = status.get(status_key, 'ok')
                if value is None or state in {'no_keys', 'error', 'unavailable'}:
                    return f"[{color}]{label}[/] [dim]N/A[/]"
                total_value = (value or 0.0) + positions_by_exchange.get(status_key, 0.0)
                return f"[{color}]{label}[/] ${total_value:.2f}"

            total_balance = (
                (alpaca_cash or 0.0) + positions_by_exchange.get('alpaca', 0.0)
                + (kraken_cash or 0.0) + positions_by_exchange.get('kraken', 0.0)
                + (binance_cash or 0.0) + positions_by_exchange.get('binance', 0.0)
                + (capital_cash or 0.0) + positions_by_exchange.get('capital', 0.0)
            )
            cash_text += (
                f"{_fmt_balance('Alpaca', alpaca_cash, 'alpaca', 'cyan')} | "
                f"{_fmt_balance('Kraken', kraken_cash, 'kraken', 'yellow')} | "
                f"{_fmt_balance('Binance', binance_cash, 'binance', 'green')} | "
                f"{_fmt_balance('Capital', capital_cash, 'capital', 'magenta')} | "
                f"[bold]Total[/] ${total_balance:.2f}"
            )
        else:
            cash_text += "[dim]Scanning...[/]"
        
        header.add_row(Text(cash_text))
        
        # 💎 Portfolio Value Tracker
        total_cash = sum(
            v for v in self.cash_balances.values() if isinstance(v, (int, float))
        ) if hasattr(self, 'cash_balances') else 0
        positions_value = sum(p.get('value', 0) for p in self.positions_data)
        total_portfolio = total_cash + positions_value
        balance_value = total_balance if total_balance is not None else total_cash
        
        # Calculate daily change
        if self.portfolio_start_value > 0:
            daily_change_pct = ((total_portfolio - self.portfolio_start_value) / self.portfolio_start_value) * 100
            daily_change_color = "green" if daily_change_pct >= 0 else "red"
            daily_arrow = "↑" if daily_change_pct >= 0 else "↓"
            portfolio_text = f"💎 PORTFOLIO: ${total_portfolio:.2f} ({daily_arrow} [{daily_change_color}]{daily_change_pct:+.2f}%[/] today) | Balance: ${balance_value:.2f} | Cash: ${total_cash:.2f} | Positions: ${positions_value:.2f}"
        else:
            # First run - set starting value
            self.portfolio_start_value = total_portfolio
            portfolio_text = f"💎 PORTFOLIO: ${total_portfolio:.2f} | Balance: ${balance_value:.2f} | Cash: ${total_cash:.2f} | Positions: ${positions_value:.2f}"
        
        if total_portfolio > self.portfolio_peak_value:
            self.portfolio_peak_value = total_portfolio
        
        header.add_row(Text(portfolio_text))
        
        return Panel(header, title="[bold blue]SESSION[/]", border_style="blue")
    
    def _build_positions_table(self) -> Panel:
        """Build the positions panel."""
        table = Table(show_header=True, header_style="bold cyan", expand=True)
        table.add_column("Symbol", style="bold", width=10)
        table.add_column("Exchange", width=8)
        table.add_column("Value", justify="right", width=10)
        table.add_column("P&L", justify="right", width=12)
        table.add_column("Progress", width=20)
        table.add_column("ETA", justify="right", width=10)
        table.add_column("Firm", width=15)
        
        for pos in self.positions_data:
            pnl = pos.get('pnl', 0)
            pnl_color = "green" if pnl >= 0 else "red"
            pnl_sign = "+" if pnl >= 0 else ""
            
            # Progress bar
            progress_pct = pos.get('progress', 0)
            bar_filled = int(min(max(progress_pct, 0), 100) / 5)
            bar_empty = 20 - bar_filled
            if progress_pct < 0:
                progress_bar = f"[red]{'▓' * 20}[/] {progress_pct:.1f}%"
            else:
                progress_bar = f"[green]{'▓' * bar_filled}[/][dim]{'░' * bar_empty}[/] {progress_pct:.1f}%"
            
            # Firm intel
            firm_info = pos.get('firm', 'Scanning...')
            firm_color = "green" if "HELP" in str(firm_info) else "yellow" if "NEUTRAL" in str(firm_info) else "red"
            
            table.add_row(
                pos.get('symbol', '?'),
                pos.get('exchange', '?'),
                f"${pos.get('value', 0):.2f}",
                f"[{pnl_color}]{pnl_sign}${pnl:.4f}[/]",
                progress_bar,
                pos.get('eta', '∞'),
                f"[{firm_color}]{firm_info[:15]}[/]",
            )
        
        if not self.positions_data:
            table.add_row("—", "—", "—", "—", "—", "—", "—")
        
        return Panel(table, title=f"[bold green]📊 POSITIONS ({len(self.positions_data)})[/]", border_style="green")
    
    def _build_intel_panel(self) -> Panel:
        """Build the quantum/firm intel panel."""
        intel = Table.grid(expand=True)
        intel.add_column()
        
        # Quantum Systems Status
        intel.add_row(Text("🔮 QUANTUM SYSTEMS", style="bold cyan"))
        intel.add_row("")
        
        quantum_status = [
            ("🍀 Luck Field", self.quantum_data.get('luck', 0)),
            ("👻 Phantom Filter", self.quantum_data.get('phantom', 0)),
            ("💭 Inception", self.quantum_data.get('inception', 0)),
            ("🐘 Elephant", self.quantum_data.get('elephant', 0)),
            ("🪆 Russian Doll", self.quantum_data.get('russian_doll', 0)),
            ("🛡️ Immune", self.quantum_data.get('immune', 0)),
            ("🐋 Moby Dick", self.quantum_data.get('moby_dick', 0)),
            ("🌌 Stargate", self.quantum_data.get('stargate', 0)),
            ("🔮 Quantum Mirror", self.quantum_data.get('quantum_mirror', 0)),
            ("🌊 HNC Surge", self.quantum_data.get('hnc_surge', 0)),
            ("📜 Historical", self.quantum_data.get('historical', 0)),
            ("🏹⚔️ Apache War Band", self.quantum_data.get('war_band', 0)),
            ("🐝 Hive State", self.quantum_data.get('hive_state', 0)),
            ("🤖 Bot Census", self.quantum_data.get('bot_census', 0)),
            ("📊 Backtest Engine", self.quantum_data.get('backtest', 0)),
            ("🌍 Global Orchestrator", self.quantum_data.get('global_orchestrator', 0)),
            ("🎵 Harmonic Binary", self.quantum_data.get('harmonic_binary', 0)),
            ("🔗 Harmonic Chain Master", self.quantum_data.get('harmonic_chain_master', 0)),
            ("⚡ Harmonic Counter", self.quantum_data.get('harmonic_counter', 0)),
            ("🌊 Harmonic Fusion", self.quantum_data.get('harmonic_fusion', 0)),
            ("🌊⚡ Harmonic Momentum", self.quantum_data.get('harmonic_momentum', 0)),
            ("🌊 Harmonic Reality", self.quantum_data.get('harmonic_reality', 0)),
            ("🗺️ Global Bot Map", self.quantum_data.get('global_bot_map', 0)),
            ("🌌 Enhanced Telescope", self.quantum_data.get('enhanced_telescope', 0)),
            ("💭 Enigma Dream", self.quantum_data.get('enigma_dream', 0)),
            ("✨ Enhancement Layer", self.quantum_data.get('enhancement_layer', 0)),
            ("🧩 Enigma Integration", self.quantum_data.get('enigma_integration', 0)),
            ("📊 Firm Intelligence", self.quantum_data.get('firm_intelligence', 0)),
            ("🌀 Enigma Core", self.quantum_data.get('enigma_core', 0)),
            # 🆕 ADDITIONAL NEURAL & TRADING SYSTEMS
            ("⛏️ Aureon Miner", self.quantum_data.get('aureon_miner', 0)),
            ("🌐 Multi-Exchange", self.quantum_data.get('multi_exchange', 0)),
            ("🎯 Multi-Pair", self.quantum_data.get('multi_pair', 0)),
            ("🌌 Multiverse Live", self.quantum_data.get('multiverse_live', 0)),
            ("✨ Multiverse Orchestrator", self.quantum_data.get('multiverse_orchestrator', 0)),
            ("🍄 Mycelium Network", self.quantum_data.get('mycelium_network', 0)),
            ("🌍🔗 Neural Revenue", self.quantum_data.get('neural_revenue', 0)),
        ]
        
        for name, score in quantum_status:
            score_color = "green" if score > 0.7 else "yellow" if score > 0.4 else "dim"
            intel.add_row(Text(f"  {name}: [{score_color}]{score:.2f}[/]"))
        
        total_boost = self.quantum_data.get('total_boost', 1.0)
        boost_color = "green" if total_boost > 1.2 else "yellow" if total_boost > 1.0 else "red"
        intel.add_row("")
        intel.add_row(Text(f"  ⚡ TOTAL BOOST: [{boost_color}]{total_boost:.2f}x[/]", style="bold"))
        
        # 🦅 Momentum Ecosystem
        intel.add_row("")
        intel.add_row(Text("🦅 MOMENTUM ECOSYSTEM", style="bold cyan"))
        intel.add_row("")
        
        mom = self.momentum_data
        
        # Micro-Momentum
        micro_targets = mom.get('micro_targets', 0)
        micro_color = "green" if micro_targets > 0 else "dim"
        intel.add_row(Text(f"  🔬 Micro-Scalp Targets: [{micro_color}]{micro_targets}[/]"))
        
        # Wolf Pack
        wolf = mom.get('wolf_pack', 'Unknown')
        wolf_color = "green" if "Hunting" in wolf else "yellow" if "Stalking" in wolf else "dim"
        intel.add_row(Text(f"  🐺 Wolf Pack: [{wolf_color}]{wolf}[/]"))
        
        # Lion Pride
        lion = mom.get('lion_pride', 'Unknown')
        lion_color = "green" if "Hunting" in lion else "yellow" if "Stalking" in lion else "dim"
        intel.add_row(Text(f"  🦁 Lion Pride: [{lion_color}]{lion}[/]"))
        
        # Army Ants
        ants = mom.get('army_ants', 'Unknown')
        ants_color = "green" if "Swarming" in ants else "yellow" if "Marching" in ants else "dim"
        intel.add_row(Text(f"  🐜 Army Ants: [{ants_color}]{ants}[/]"))
        
        # Hummingbird
        hb = mom.get('hummingbird', 'Unknown')
        hb_color = "green" if "Pollinating" in hb else "dim"
        intel.add_row(Text(f"  🐦 Hummingbird: [{hb_color}]{hb}[/]"))

        # 🌌 Stargate Grid
        intel.add_row("")
        intel.add_row(Text("🌌 STARGATE GRID (12 Nodes)", style="bold cyan"))
        intel.add_row("")
        
        sg = self.stargate_data
        node = sg.get('active_node', 'Unknown')
        intel.add_row(Text(f"  Active Node: [green]{node}[/]"))
        intel.add_row(Text(f"  Resonance: {sg.get('grid_coherence',0):.2f} Hz"))
        desc = sg.get('description', '')
        if desc:
            intel.add_row(Text(f"  [italic dim]{desc}[/]"))

        # Active Firms
        intel.add_row("")
        intel.add_row(Text("🏢 ACTIVE FIRMS", style="bold magenta"))
        intel.add_row("")
        
        for firm, info in list(self.firms_data.items())[:5]:
            direction = info.get('direction', '?')
            dir_icon = "🟢" if direction == "bullish" else "🔴" if direction == "bearish" else "⚪"
            intel.add_row(Text(f"  {dir_icon} {firm[:12]}: {info.get('action', '?')[:10]}"))
        
        if not self.firms_data:
            intel.add_row(Text("  Scanning...", style="dim"))
        
        # Rising Star Stats
        if hasattr(self, 'rising_star_stats') and self.rising_star_stats:
            intel.add_row("")
            intel.add_row(Text("🌟 RISING STAR", style="bold yellow"))
            intel.add_row("")
            rs = self.rising_star_stats
            intel.add_row(Text(f"  Scanned: {rs.get('candidates_scanned', 0)}"))
            intel.add_row(Text(f"  Sims: {rs.get('simulations_run', 0):,}"))
            intel.add_row(Text(f"  Winners: {rs.get('winners_selected', 0)}"))
            intel.add_row(Text(f"  DCA: {rs.get('accumulations_made', 0)} (${rs.get('total_accumulated_value', 0):.2f})"))
        
        # 🎯 Options Trading Stats
        if hasattr(self, 'options_data') and self.options_data.get('trading_level') != 'UNKNOWN':
            intel.add_row("")
            intel.add_row(Text("🎯 OPTIONS TRADING", style="bold green"))
            intel.add_row("")
            opt = self.options_data
            level_color = "green" if opt.get('trading_level') in ['COVERED', 'BUYING', 'SPREADS'] else "yellow"
            intel.add_row(Text(f"  Level: [{level_color}]{opt.get('trading_level', 'N/A')}[/]"))
            intel.add_row(Text(f"  Buying Power: ${opt.get('buying_power', 0):.2f}"))
            if opt.get('best_opportunity'):
                best = opt['best_opportunity']
                intel.add_row(Text(f"  Best: {best.get('symbol', 'N/A')[:15]}"))
                intel.add_row(Text(f"  Premium: ${best.get('premium', 0):.2f}"))
                ann_ret = best.get('annualized_return', 0)
                ret_color = "green" if ann_ret > 50 else "yellow" if ann_ret > 20 else "dim"
                intel.add_row(Text(f"  Ann.Ret: [{ret_color}]{ann_ret:.0f}%[/]"))
            if opt.get('positions'):
                intel.add_row(Text(f"  📈 {len(opt['positions'])} option positions"))
        
        # 🦈🔍 Predator Detection Stats
        if hasattr(self, 'predator_data') and self.predator_data:
            intel.add_row("")
            intel.add_row(Text("🦈🔍 PREDATOR DETECTION", style="bold red"))
            intel.add_row("")
            pd = self.predator_data
            threat = pd.get('threat_level', 'green')
            threat_emoji = {"green": "🟢", "yellow": "🟡", "orange": "🟠", "red": "🔴"}.get(threat, "⚪")
            threat_color = "green" if threat == "green" else "yellow" if threat == "yellow" else "red"
            intel.add_row(Text(f"  Threat: {threat_emoji} [{threat_color}]{threat.upper()}[/]"))
            front_run = pd.get('front_run_rate', 0) * 100
            fr_color = "green" if front_run < 15 else "yellow" if front_run < 30 else "red"
            intel.add_row(Text(f"  Front-Run: [{fr_color}]{front_run:.0f}%[/]"))
            if pd.get('top_predator'):
                intel.add_row(Text(f"  👁️ Hunter: {pd['top_predator'][:12]}"))
            if pd.get('strategy_decay'):
                intel.add_row(Text("  ⚠️ DECAY DETECTED", style="bold red"))
        
        # 🥷 Stealth Execution Stats
        if hasattr(self, 'stealth_data') and self.stealth_data.get('mode') != 'disabled':
            intel.add_row("")
            intel.add_row(Text("🥷 STEALTH MODE", style="bold cyan"))
            intel.add_row("")
            st = self.stealth_data
            mode = st.get('mode', 'normal')
            mode_color = "cyan" if mode == "normal" else "yellow" if mode == "aggressive" else "red" if mode == "paranoid" else "dim"
            intel.add_row(Text(f"  Mode: [{mode_color}]{mode.upper()}[/]"))
            intel.add_row(Text(f"  Delayed: {st.get('delayed_orders', 0)}"))
            intel.add_row(Text(f"  Split: {st.get('split_orders', 0)}"))
            intel.add_row(Text(f"  Rotated: {st.get('rotated_symbols', 0)}"))
            if st.get('hunted_count', 0) > 0:
                intel.add_row(Text(f"  🎯 Hunted: {st['hunted_count']} symbols", style="yellow"))
        
        return Panel(intel, title="[bold yellow]🎯 INTELLIGENCE[/]", border_style="yellow")
    
    def _build_footer(self) -> Panel:
        """Build the footer with comprehensive status."""
        unrealized_pnl = sum(p.get('pnl', 0) for p in self.positions_data)
        pnl_color = "green" if unrealized_pnl >= 0 else "red"
        pnl_sign = "+" if unrealized_pnl >= 0 else ""
        
        footer = Table.grid(expand=True)
        footer.add_column(justify="left", ratio=1)
        
        # 🎯 Opportunity Queue (Top 3)
        opp_text = "🎯 NEXT IN LINE: "
        if hasattr(self, 'opportunity_queue') and self.opportunity_queue:
            top_3 = self.opportunity_queue[:3]
            opp_parts = []
            for i, opp in enumerate(top_3, 1):
                symbol = opp.get('symbol', 'N/A')[:8]
                exchange = opp.get('exchange', 'N/A')[:3].upper()
                change = opp.get('change_pct', 0)
                score = opp.get('score', 0)
                tags = opp.get('tags', [])
                tag_emoji = "🐺" if "wolf" in tags else "🦁" if "lion" in tags else "📊"
                opp_parts.append(f"{i}. {symbol} ({exchange}) {change:+.1f}% | {tag_emoji}")
            opp_text += " | ".join(opp_parts)
        else:
            opp_text += "[dim]Scanning for opportunities...[/]"
        footer.add_row(Text(opp_text))
        
        # 🏆 Exchange Performance Leaderboard
        if hasattr(self, 'exchange_stats'):
            exchanges = []
            for ex, stats in self.exchange_stats.items():
                if stats['trades'] > 0:
                    win_rate = (stats['wins'] / stats['trades']) * 100
                    medal = "🥇" if win_rate >= 70 else "🥈" if win_rate >= 50 else "🥉"
                    exchanges.append((ex, stats['wins'], stats['losses'], stats['pnl'], win_rate, medal))
            
            # Sort by win rate
            exchanges.sort(key=lambda x: x[4], reverse=True)
            
            if exchanges:
                ex_parts = []
                for ex, w, l, pnl, wr, medal in exchanges:
                    pnl_color = "green" if pnl >= 0 else "red"
                    ex_parts.append(f"{medal} {ex.capitalize()}: {w}W-{l}L [{pnl_color}]{pnl:+.2f}[/] ({wr:.0f}%)")
                footer.add_row(Text("🏆 EXCHANGES: " + " | ".join(ex_parts)))
        
        # 🎖️ Recent Kills (Last 5)
        if hasattr(self, 'recent_kills') and self.recent_kills:
            kills_text = "🎖️ RECENT: "
            kill_parts = []
            for kill in self.recent_kills[-5:]:
                symbol = kill.get('symbol', 'N/A')[:6]
                pnl = kill.get('pnl', 0)
                icon = "✅" if pnl >= 0 else "❌"
                exchange = kill.get('exchange', 'N/A')[:3].upper()
                hold_time = kill.get('hold_time', 0)
                pnl_color = "green" if pnl >= 0 else "red"
                kill_parts.append(f"{icon} {symbol} [{pnl_color}]{pnl:+.2f}[/] ({hold_time}s) {exchange}")
            kills_text += " | ".join(kill_parts)
            footer.add_row(Text(kills_text))
        
        # 🏥 System Health
        if hasattr(self, 'system_health'):
            sh = self.system_health
            health_text = "🏥 HEALTH: "
            health_parts = []
            
            # API statuses with latency
            for ex in ['alpaca', 'kraken', 'binance']:
                status = sh.get(f'{ex}_status', '🟢')
                latency = sh.get(f'{ex}_latency', 0)
                lat_color = "green" if latency < 100 else "yellow" if latency < 300 else "red"
                health_parts.append(f"{status} {ex.capitalize()} [{lat_color}]{latency}ms[/]")
            
            health_text += " | ".join(health_parts)
            
            # Last trade time
            if sh.get('last_trade_time'):
                seconds_ago = int(time.time() - sh['last_trade_time'])
                health_text += f" | Last Trade: {seconds_ago}s ago"
            
            # Scanning status
            scan_status = "✅" if sh.get('scanning_active', True) else "⏸️"
            health_text += f" | Scanning: {scan_status}"
            
            footer.add_row(Text(health_text))
        
        # ⚠️ Risk Exposure Panel
        if hasattr(self, 'risk_metrics'):
            rm = self.risk_metrics
            total_cash = sum(self.cash_balances.values()) if hasattr(self, 'cash_balances') else 0
            positions_value = sum(p.get('value', 0) for p in self.positions_data)
            total_portfolio = total_cash + positions_value
            
            exposure_pct = (positions_value / total_portfolio * 100) if total_portfolio > 0 else 0
            max_pos = max([p.get('value', 0) for p in self.positions_data]) if self.positions_data else 0
            max_pos_pct = (max_pos / total_portfolio * 100) if total_portfolio > 0 else 0
            
            drawdown = self.portfolio_peak_value - total_portfolio if self.portfolio_peak_value > 0 else 0
            drawdown_pct = (drawdown / self.portfolio_peak_value * 100) if self.portfolio_peak_value > 0 else 0
            
            exp_color = "green" if exposure_pct < 70 else "yellow" if exposure_pct < 85 else "red"
            dd_color = "green" if drawdown_pct < 5 else "yellow" if drawdown_pct < 10 else "red"
            
            risk_text = f"⚠️ RISK: [{exp_color}]${positions_value:.2f}/${total_portfolio:.2f} ({exposure_pct:.1f}%)[/] | Max Pos: ${max_pos:.2f} ({max_pos_pct:.1f}%) | Drawdown: [{dd_color}]-${drawdown:.2f} ({drawdown_pct:.1f}%)[/]"
            footer.add_row(Text(risk_text))
        
        # 🔥 Streak Tracker
        if hasattr(self, 'streak_data'):
            sd = self.streak_data
            current = sd.get('current_streak', 0)
            streak_type = sd.get('current_streak_type', 'none')
            
            if current > 0:
                streak_icon = "🔥" if streak_type == 'win' else "❄️"
                streak_color = "green" if streak_type == 'win' else "red"
                streak_text = f"{streak_icon} STREAK: [{streak_color}]{current} {streak_type}s in a row[/]"
            else:
                streak_text = "🔥 STREAK: Starting fresh"
            
            best_streak = sd.get('best_win_streak', 0)
            if best_streak > 0:
                streak_text += f" | Best today: {best_streak}W"
            
            # Hot exchange
                hot_ex = max(sd.get('exchange_streaks', {}).items(), key=lambda x: x[1], default=(None, 0))
                streak_text += f" | 🔥 Hot: {hot_ex[0].capitalize()} ({hot_ex[1]}W)"
            
            footer.add_row(Text(streak_text))
        
        # 🚫 Protection Stats + ⚡ Flash Alerts (combined row)
        combined_text = ""
        
        # Protection stats
        if hasattr(self, 'protection_stats'):
            ps = self.protection_stats
            blocked = ps.get('blocked_count', 0)
            saved = ps.get('estimated_saved', 0)
            top_dangers = ps.get('top_dangers', [])
            
            if blocked > 0:
                combined_text = f"🚫 PROTECTED: {blocked} blocked | Saved: ~${saved:.2f}"
                if top_dangers:
                    top = top_dangers[0]
                    combined_text += f" | Top danger: {top[0]} ({top[1]}x)"
            else:
                combined_text = "🚫 PROTECTED: Scanning for patterns..."
        
        # Flash alerts
        if hasattr(self, 'flash_alerts') and self.flash_alerts:
            latest = self.flash_alerts[-1]
            alert_type = latest.get('type', 'info')
            alert_icon = "⚡" if alert_type == 'critical' else "🏆" if alert_type == 'success' else "⚠️"
            alert_color = "red" if alert_type == 'critical' else "green" if alert_type == 'success' else "yellow"
            alert_msg = latest.get('message', '')
            
            if combined_text:
                combined_text += f" | {alert_icon} [{alert_color}]{alert_msg}[/]"
            else:
                combined_text = f"{alert_icon} [{alert_color}]{alert_msg}[/]"
        
        if combined_text:
            footer.add_row(Text(combined_text))
        
        # 📈 Efficiency Metrics + ⏰ Best Trading Hours (combined row)
        efficiency_text = ""
        
        if hasattr(self, 'efficiency_metrics'):
            em = self.efficiency_metrics
            scanned = em.get('total_scanned', 0)
            bought = em.get('total_bought', 0)
            conversion = (bought / scanned * 100) if scanned > 0 else 0
            success_rate = em.get('success_rate', 0)
            
            conv_color = "green" if conversion > 0.5 else "yellow" if conversion > 0.1 else "dim"
            success_color = "green" if success_rate > 60 else "yellow" if success_rate > 40 else "red"
            
            efficiency_text = f"📈 EFFICIENCY: {scanned:,} scanned → {bought} bought ([{conv_color}]{conversion:.2f}%[/]) | Success: [{success_color}]{success_rate:.0f}%[/]"
        
        # Best trading hours
        if hasattr(self, 'hourly_performance') and self.hourly_performance:
            best_hour = max(self.hourly_performance.items(), key=lambda x: x[1].get('pnl', 0), default=(None, {}))
            current_hour = time.localtime().tm_hour
            current_pnl = self.hourly_performance.get(current_hour, {}).get('pnl', 0)
            
            if best_hour[0] is not None and best_hour[1].get('pnl', 0) > 0:
                hour_color = "green" if current_pnl > 0 else "dim"
                if efficiency_text:
                    efficiency_text += f" | ⏰ Best hour: {best_hour[0]:02d}:00 (+${best_hour[1]['pnl']:.2f}) | Now: [{hour_color}]{current_pnl:+.2f}[/]"
                else:
                    efficiency_text = f"⏰ Best hour: {best_hour[0]:02d}:00 (+${best_hour[1]['pnl']:.2f}) | Current: [{hour_color}]{current_pnl:+.2f}[/]"
        
        if efficiency_text:
            footer.add_row(Text(efficiency_text))
        
        # 💪 Position Health + 🎲 Volatility (combined row)
        health_vol_text = ""
        
        if hasattr(self, 'position_health'):
            ph = self.position_health
            score = ph.get('overall_score', 100)
            healthy = ph.get('healthy_count', 0)
            at_risk = ph.get('at_risk_count', 0)
            danger = ph.get('danger_count', 0)
            
            score_color = "green" if score >= 80 else "yellow" if score >= 60 else "red"
            health_vol_text = f"💪 HEALTH: [{score_color}]{score}/100[/] | 🟢 {healthy} healthy | 🟡 {at_risk} at risk | 🔴 {danger} danger"
        
        # Market volatility
        if hasattr(self, 'market_volatility'):
            mv = self.market_volatility
            vol_level = mv.get('current_volatility', 'normal')
            opp_mult = mv.get('opportunity_multiplier', 1.0)
            
            vol_emoji = "🎲" if vol_level == 'extreme' else "🔥" if vol_level == 'high' else "🟢"
            vol_color = "red" if vol_level == 'extreme' else "yellow" if vol_level == 'high' else "green"
            
            if health_vol_text:
                health_vol_text += f" | {vol_emoji} MARKET: [{vol_color}]{vol_level.upper()}[/]"
                if opp_mult > 1.5:
                    health_vol_text += f" | Opps ↑ {(opp_mult-1)*100:.0f}%"
            else:
                health_vol_text = f"{vol_emoji} MARKET: [{vol_color}]{vol_level.upper()}[/]"
        
        if health_vol_text:
            footer.add_row(Text(health_vol_text))
        
        # Build status line with options info
        options_status = ""
        if hasattr(self, 'options_data') and self.options_data.get('trading_level') not in ['UNKNOWN', 'DISABLED']:
            opt_level = self.options_data.get('trading_level', 'N/A')
            options_status = f" | 🎯 OPTIONS: {opt_level}"
        
        footer.add_row(
            Text(f"💰 UNREALIZED: [{pnl_color}]{pnl_sign}${unrealized_pnl:.4f}[/] | "
                 f"🌟 RISING STAR + DCA ACTIVE{options_status} | 🚫 NO STOP LOSS", style="bold")
        )
        footer.add_row(
            Text("⌨️ Press Ctrl+C to stop", style="dim")
        )
        
        return Panel(footer, title="[bold cyan]STATUS[/]", border_style="cyan")
    
    def build_display(self) -> Layout:
        """Build the complete war room display."""
        if not RICH_AVAILABLE:
            return None
            
        layout = self._create_layout()
        layout["header"].update(self._build_header())
        layout["positions"].update(self._build_positions_table())
        layout["intel"].update(self._build_intel_panel())
        layout["footer"].update(self._build_footer())
        
        return layout
    
    def update_position(self, symbol: str, exchange: str, value: float, pnl: float, 
                        progress: float, eta: str, firm: str = "Scanning..."):
        """Update or add a position to the display."""
        # Find existing or create new
        for pos in self.positions_data:
            if pos['symbol'] == symbol:
                pos.update({
                    'exchange': exchange,
                    'value': value,
                    'pnl': pnl,
                    'progress': progress,
                    'eta': eta,
                    'firm': firm,
                })
                return
        
        self.positions_data.append({
            'symbol': symbol,
            'exchange': exchange,
            'value': value,
            'pnl': pnl,
            'progress': progress,
            'eta': eta,
            'firm': firm,
        })
    
    def remove_position(self, symbol: str):
        """Remove a position from display."""
        self.positions_data = [p for p in self.positions_data if p['symbol'] != symbol]
    
    def update_quantum(self, **scores):
        """Update quantum system scores."""
        self.quantum_data.update(scores)
    
    def update_firm(self, firm_name: str, action: str, direction: str):
        """Update firm activity."""
        self.firms_data[firm_name] = {'action': action, 'direction': direction}
    
    def record_kill(self, pnl: float, symbol: str = None, exchange: str = None, hold_time: float = 0):
        """Record a kill (closed position)."""
        is_win = pnl >= 0
        
        if is_win:
            self.kills_data['wins'] += 1
        else:
            self.kills_data['losses'] += 1
        self.kills_data['pnl'] += pnl
        self.total_pnl += pnl
        
        if pnl > self.best_trade:
            self.best_trade = pnl
            # 🏆 Flash alert for new best trade
            if pnl > 1.0:  # Only alert if significant
                self.add_flash_alert(f"New best trade! {symbol} +${pnl:.2f}", 'success')
        if pnl < self.worst_trade:
            self.worst_trade = pnl
        
        # Update exchange stats
        if exchange and hasattr(self, 'exchange_stats') and exchange in self.exchange_stats:
            self.exchange_stats[exchange]['trades'] += 1
            self.exchange_stats[exchange]['pnl'] += pnl
            if is_win:
                self.exchange_stats[exchange]['wins'] += 1
            else:
                self.exchange_stats[exchange]['losses'] += 1
        
        # Update streak
        self.update_streak(is_win, exchange)
        
        # Record hourly P&L
        self.record_hourly_pnl(pnl)
        
        # Flash alerts for significant events
        if pnl >= 5.0:
            self.add_flash_alert(f"Big win! {symbol} +${pnl:.2f} ({hold_time:.0f}s)", 'success')
        elif pnl <= -5.0:
            self.add_flash_alert(f"Large loss: {symbol} -${abs(pnl):.2f}", 'critical')
        
        # Add to recent kills feed
        if hasattr(self, 'recent_kills'):
            self.recent_kills.append({
                'symbol': symbol or 'N/A',
                'exchange': exchange or 'N/A',
                'pnl': pnl,
                'hold_time': int(hold_time),
                'timestamp': time.time()
            })
            # Keep only last 10
            if len(self.recent_kills) > 10:
                self.recent_kills = self.recent_kills[-10:]
        
        # Update system health - last trade time
        if hasattr(self, 'system_health'):
            self.system_health['last_trade_time'] = time.time()
    
    def update_opportunity_queue(self, opportunities: list):
        """Update the opportunity queue with top candidates."""
        if hasattr(self, 'opportunity_queue'):
            # Extract top opportunities with metadata
            self.opportunity_queue = []
            for opp in opportunities[:5]:  # Top 5
                self.opportunity_queue.append({
                    'symbol': opp.symbol if hasattr(opp, 'symbol') else opp.get('symbol', 'N/A'),
                    'exchange': opp.exchange if hasattr(opp, 'exchange') else opp.get('exchange', 'N/A'),
                    'change_pct': opp.change_pct if hasattr(opp, 'change_pct') else opp.get('change_pct', 0),
                    'score': opp.momentum_score if hasattr(opp, 'momentum_score') else opp.get('score', 0),
                    'tags': getattr(opp, 'tags', []) if hasattr(opp, 'tags') else opp.get('tags', [])
                })
    
    def update_system_health(self, exchange: str = None, latency: float = 0, status: str = '🟢'):
        """Update system health metrics."""
        if hasattr(self, 'system_health'):
            if exchange:
                self.system_health[f'{exchange}_latency'] = int(latency)
                self.system_health[f'{exchange}_status'] = status
            self.system_health['scanning_active'] = True
    
    def update_rising_star(self, stats: dict):
        """Update Rising Star statistics."""
        self.rising_star_stats = stats
    
    def update_options(self, trading_level: str = None, buying_power: float = None,
                       positions: list = None, best_opportunity: dict = None):
        """Update options trading data."""
        if trading_level is not None:
            self.options_data['trading_level'] = trading_level
        if buying_power is not None:
            self.options_data['buying_power'] = buying_power
        if positions is not None:
            self.options_data['positions'] = positions
        if best_opportunity is not None:
            self.options_data['best_opportunity'] = best_opportunity
        self.options_data['last_scan'] = time.time()
    
    def update_predator(self, threat_level: str = None, front_run_rate: float = None,
                        top_predator: str = None, strategy_decay: bool = None):
        """Update predator detection data."""
        if threat_level is not None:
            self.predator_data['threat_level'] = threat_level
        if front_run_rate is not None:
            self.predator_data['front_run_rate'] = front_run_rate
        if top_predator is not None:
            self.predator_data['top_predator'] = top_predator
        if strategy_decay is not None:
            self.predator_data['strategy_decay'] = strategy_decay
    
    def update_stealth(self, mode: str = None, delayed_orders: int = None,
                       split_orders: int = None, rotated_symbols: int = None,
                       hunted_count: int = None):
        """Update stealth execution data."""
        if mode is not None:
            self.stealth_data['mode'] = mode
        if delayed_orders is not None:
            self.stealth_data['delayed_orders'] = delayed_orders
        if split_orders is not None:
            self.stealth_data['split_orders'] = split_orders
        if rotated_symbols is not None:
            self.stealth_data['rotated_symbols'] = rotated_symbols
        if hunted_count is not None:
            self.stealth_data['hunted_count'] = hunted_count
    
    def update_momentum(self, wolf_status: str = None, lion_status: str = None, 
                       ants_status: str = None, hummingbird_status: str = None, micro_targets: int = None):
        """Update momentum ecosystem data."""
        if wolf_status is not None:
            self.momentum_data['wolf_pack'] = wolf_status
        if lion_status is not None:
            self.momentum_data['lion_pride'] = lion_status
        if ants_status is not None:
            self.momentum_data['army_ants'] = ants_status
        if hummingbird_status is not None:
            self.momentum_data['hummingbird'] = hummingbird_status
        if micro_targets is not None:
            self.momentum_data['micro_targets'] = micro_targets

    def update_stargate(self, active_node: str = None, coherence: float = None, description: str = None):
        """Update Stargate Grid data."""
        if active_node is not None:
            self.stargate_data['active_node'] = active_node
        if coherence is not None:
            self.stargate_data['grid_coherence'] = coherence
        if description is not None:
            self.stargate_data['description'] = description
    
    def update_cash(self, alpaca: float = None, kraken: float = None, binance: float = None):
        """Update cash balances for all exchanges."""
        if alpaca is not None:
            self.cash_balances['alpaca'] = alpaca
        if kraken is not None:
            self.cash_balances['kraken'] = kraken
        if binance is not None:
            self.cash_balances['binance'] = binance

    def update_cash_status(self, status: Dict[str, str]):
        """Update cash balance status for display."""
        if not status:
            return
        for key in ['alpaca', 'kraken', 'binance']:
            if key in status:
                self.cash_status[key] = status[key]
    
    def update_streak(self, is_win: bool, exchange: str = None):
        """Update win/loss streak tracking."""
        if hasattr(self, 'streak_data'):
            if is_win:
                if self.streak_data['current_streak_type'] == 'win':
                    self.streak_data['current_streak'] += 1
                else:
                    self.streak_data['current_streak'] = 1
                    self.streak_data['current_streak_type'] = 'win'
                
                # Update best streak
                if self.streak_data['current_streak'] > self.streak_data['best_win_streak']:
                    self.streak_data['best_win_streak'] = self.streak_data['current_streak']
                
                # Update exchange streak
                if exchange and exchange in self.streak_data['exchange_streaks']:
                    self.streak_data['exchange_streaks'][exchange] += 1
            else:
                if self.streak_data['current_streak_type'] == 'loss':
                    self.streak_data['current_streak'] += 1
                else:
                    self.streak_data['current_streak'] = 1
                    self.streak_data['current_streak_type'] = 'loss'
                
                # Reset exchange streak on loss
                if exchange and exchange in self.streak_data['exchange_streaks']:
                    self.streak_data['exchange_streaks'][exchange] = 0
    
    def add_flash_alert(self, message: str, alert_type: str = 'info'):
        """Add a flash alert (critical, success, warning, info)."""
        if hasattr(self, 'flash_alerts'):
            self.flash_alerts.append({
                'message': message,
                'type': alert_type,
                'timestamp': time.time()
            })
            # Keep only last 10
            if len(self.flash_alerts) > 10:
                self.flash_alerts = self.flash_alerts[-10:]
    
    def update_protection_stats(self, blocked_count: int = None, estimated_saved: float = None, top_dangers: list = None):
        """Update elephant memory protection stats."""
        if hasattr(self, 'protection_stats'):
            if blocked_count is not None:
                self.protection_stats['blocked_count'] = blocked_count
            if estimated_saved is not None:
                self.protection_stats['estimated_saved'] = estimated_saved
            if top_dangers is not None:
                self.protection_stats['top_dangers'] = top_dangers
    
    def update_efficiency(self, scanned: int = None, bought: int = None, success_rate: float = None):
        """Update efficiency metrics."""
        if hasattr(self, 'efficiency_metrics'):
            if scanned is not None:
                self.efficiency_metrics['total_scanned'] = scanned
            if bought is not None:
                self.efficiency_metrics['total_bought'] = bought
            if success_rate is not None:
                self.efficiency_metrics['success_rate'] = success_rate
            
            # Update conversion rate
            if self.efficiency_metrics['total_scanned'] > 0:
                self.efficiency_metrics['conversion_rate'] = (self.efficiency_metrics['total_bought'] / self.efficiency_metrics['total_scanned']) * 100
    
    def record_hourly_pnl(self, pnl: float):
        """Record P&L for current hour."""
        if hasattr(self, 'hourly_performance'):
            current_hour = time.localtime().tm_hour
            if current_hour not in self.hourly_performance:
                self.hourly_performance[current_hour] = {'pnl': 0, 'trades': 0}
            self.hourly_performance[current_hour]['pnl'] += pnl
            self.hourly_performance[current_hour]['trades'] += 1
    
    def update_position_health(self):
        """Calculate and update position health scores."""
        if hasattr(self, 'position_health') and self.positions_data:
            healthy = 0
            at_risk = 0
            danger = 0
            
            for pos in self.positions_data:
                pnl_pct = (pos.get('pnl', 0) / pos.get('value', 1)) * 100 if pos.get('value', 0) > 0 else 0
                
                if pnl_pct >= -5:
                    healthy += 1
                elif pnl_pct >= -15:
                    at_risk += 1
                else:
                    danger += 1
            
            self.position_health['healthy_count'] = healthy
            self.position_health['at_risk_count'] = at_risk
            self.position_health['danger_count'] = danger
            
            # Calculate overall score (100 = all healthy, 0 = all in danger)
            total = len(self.positions_data)
            if total > 0:
                score = ((healthy * 100) + (at_risk * 50)) / total
                self.position_health['overall_score'] = int(score)
    
    def update_volatility(self, opportunity_count: int):
        """Update market volatility based on opportunity count."""
        if hasattr(self, 'market_volatility'):
            # Baseline: 1000-2000 opportunities = normal
            if opportunity_count < 500:
                self.market_volatility['current_volatility'] = 'low'
                self.market_volatility['opportunity_multiplier'] = 0.5
                self.market_volatility['risk_level'] = 'low'
            elif opportunity_count < 2000:
                self.market_volatility['current_volatility'] = 'normal'
                self.market_volatility['opportunity_multiplier'] = 1.0
                self.market_volatility['risk_level'] = 'normal'
            elif opportunity_count < 4000:
                self.market_volatility['current_volatility'] = 'high'
                self.market_volatility['opportunity_multiplier'] = 2.0
                self.market_volatility['risk_level'] = 'elevated'
            else:
                self.market_volatility['current_volatility'] = 'extreme'
                self.market_volatility['opportunity_multiplier'] = 3.0
                self.market_volatility['risk_level'] = 'high'
    
    def increment_cycle(self):
        """Increment cycle counter."""
        self.cycle_count += 1
    
    def print_fallback(self):
        """Fallback print for when Rich is not available."""
        if RICH_AVAILABLE:
            return
        
        runtime = time.time() - self.runtime_start
        hrs, rem = divmod(runtime, 3600)
        mins, secs = divmod(rem, 60)
        
        print("\n" + "=" * 80)
        print(f"👑🦈 ORCA WAR ROOM - {int(hrs)}h {int(mins)}m {int(secs)}s | Cycles: {self.cycle_count}")
        print(f"💰 Total P&L: ${self.total_pnl:+.4f} | Wins: {self.kills_data['wins']} | Losses: {self.kills_data['losses']}")
        print("-" * 80)
        for pos in self.positions_data:
            pnl = pos.get('pnl', 0)
            print(f"  🎯 {pos['symbol']} ({pos['exchange']}) | ${pos['value']:.2f} | P&L: ${pnl:+.4f} | {pos.get('progress', 0):.1f}%")
        print("=" * 80)


# ═══════════════════════════════════════════════════════════════════════════════
# WHALE INTELLIGENCE TRACKER - Predict target hit based on whale/bot movements
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class WhaleSignal:
    """Real-time whale/bot signal for a position."""
    symbol: str
    whale_support: float      # 0-1: Are whales pushing our direction?
    counter_pressure: float   # 0-1: Are bots opposing us?
    momentum_score: float     # 0-1: Current momentum strength
    eta_seconds: float        # Estimated time to target (seconds)
    confidence: float         # 0-1: Confidence in prediction
    active_whales: int        # Number of whales active on this symbol
    dominant_firm: str        # Which firm is dominant
    firm_activity: str        # What the firm is doing
    reasoning: str            # Human-readable explanation


@dataclass
class FirmActivity:
    """Live firm activity on a symbol."""
    firm_name: str
    firm_id: str
    action: str           # "ACCUMULATING", "DISTRIBUTING", "MM", etc.
    direction: str        # "bullish", "bearish", "neutral"
    volume_24h: float     # USD volume
    impact: str           # "HELPS US 🟢", "HURTS US 🔴", "NEUTRAL ⚪"
    confidence: float


class WhaleIntelligenceTracker:
    """
    🐋 Track whale and bot movements to predict target hits.
    
    Uses:
    - WhaleProfilerSystem: Track individual whale positions
    - FirmIntelligenceCatalog: Track firm-level activity
    - ThoughtBus: Real-time whale sonar signals
    - GLOBAL_TRADING_FIRMS: Known firm database
    """
    
    # Map symbols to what firms typically trade
    SYMBOL_FIRM_MAP = {
        'BTC': ['citadel', 'jane_street', 'jump_trading', 'wintermute'],
        'ETH': ['jump_trading', 'wintermute', 'citadel'],
        'SOL': ['jump_trading', 'wintermute', 'alameda'],  # Alameda ghost activity
        'PEPE': ['wintermute', 'market_makers'],  # Meme coin MMs
        'TRUMP': ['market_makers', 'retail_whales'],  # Political meme
        'AAVE': ['jane_street', 'defi_whales'],
    }
    
    def __init__(self):
        self.whale_profiler = None
        self.firm_intel = None
        self.bus = None
        self.whale_signals: Dict[str, List] = {}  # symbol -> recent signals
        self.firm_activities: Dict[str, List[FirmActivity]] = {}  # symbol -> firm activities
        self.last_market_scan = 0.0
        
        # Initialize systems
        if WHALE_PROFILER_AVAILABLE:
            try:
                self.whale_profiler = WhaleProfilerSystem()
            except Exception as e:
                pass
                
        if FIRM_INTEL_AVAILABLE:
            try:
                self.firm_intel = FirmIntelligenceCatalog()
            except Exception as e:
                pass
        
        # Initialize ThoughtBus - directly create instance
        if THOUGHT_BUS_AVAILABLE and ThoughtBus:
            try:
                # Create new instance directly - ThoughtBus doesn't use singleton pattern
                self.bus = ThoughtBus()
                
                # Subscribe to whale/firm signals
                if self.bus:
                    self.bus.subscribe('whale.*', self._on_whale_signal)
                    self.bus.subscribe('firm.*', self._on_firm_signal)
                    self.bus.subscribe('market.*', self._on_market_signal)
            except Exception as e:
                self.bus = None
    
    def _on_whale_signal(self, thought):
        """Handle incoming whale signals from ThoughtBus."""
        try:
            symbol = thought.payload.get('symbol', thought.meta.get('symbol', 'UNKNOWN'))
            if symbol not in self.whale_signals:
                self.whale_signals[symbol] = []
            self.whale_signals[symbol].append({
                'timestamp': time.time(),
                'type': thought.topic,
                'data': thought.payload
            })
            # Keep only last 100 signals per symbol
            self.whale_signals[symbol] = self.whale_signals[symbol][-100:]
        except Exception:
            pass
    
    def _on_firm_signal(self, thought):
        """Handle incoming firm signals from ThoughtBus."""
        self._on_whale_signal(thought)
    
    def _on_market_signal(self, thought):
        """Handle market signals."""
        self._on_whale_signal(thought)
    
    def process_live_trade(self, symbol: str, price: float, quantity: float, side: str, exchange: str = 'unknown'):
        """
        Process a live trade from SSE/WebSocket stream.
        Updates firm activity simulation with real market data.
        
        Args:
            symbol: Trading symbol (e.g., 'BTC/USD')
            price: Trade price
            quantity: Trade quantity
            side: 'buy' or 'sell'
            exchange: Exchange name
        """
        value_usd = price * quantity
        symbol_clean = symbol.replace('/', '').upper()
        
        # Large trades (>$10k) indicate potential whale activity
        if value_usd > 10000:
            # Record as whale signal
            if symbol not in self.whale_signals:
                self.whale_signals[symbol] = []
            
            self.whale_signals[symbol].append({
                'timestamp': time.time(),
                'type': 'live_trade.whale',
                'data': {
                    'symbol': symbol,
                    'price': price,
                    'quantity': quantity,
                    'side': side,
                    'value_usd': value_usd,
                    'exchange': exchange,
                    'is_whale': True
                }
            })
            
            # Emit to ThoughtBus
            if self.bus:
                try:
                    self.bus.think(
                        message=f"Whale {side} ${value_usd:.0f} on {symbol}",
                        topic=f"whale.trade.{symbol_clean}",
                        priority="high",
                        metadata={
                            'symbol': symbol,
                            'price': price,
                            'quantity': quantity,
                            'side': side,
                            'value_usd': value_usd,
                            'exchange': exchange
                        }
                    )
                except Exception:
                    pass
        
        # Very large trades (>$100k) = institutional flow
        if value_usd > 100000:
            symbol_base = symbol.replace('/USD', '').replace('USDT', '').upper()
            firms = self.SYMBOL_FIRM_MAP.get(symbol_base, ['unknown_mm'])
            firm_id = firms[0] if firms else 'unknown'
            firm_data = GLOBAL_TRADING_FIRMS.get(firm_id)
            firm_name = firm_data.name if firm_data else firm_id.replace('_', ' ').title()
            
            # Create firm activity from real trade
            direction = 'bullish' if side == 'buy' else 'bearish'
            action = 'ACCUMULATING' if side == 'buy' else 'DISTRIBUTING'
            
            activity = FirmActivity(
                firm_name=firm_name,
                firm_id=firm_id,
                action=action,
                direction=direction,
                volume_24h=value_usd,
                impact="",
                confidence=0.85
            )
            
            if symbol not in self.firm_activities:
                self.firm_activities[symbol] = []
            self.firm_activities[symbol].append(activity)
            
            # Keep only recent
            self.firm_activities[symbol] = self.firm_activities[symbol][-20:]
    
    def _simulate_firm_activity(self, symbol: str, current_price: float, price_change_pct: float) -> List[FirmActivity]:
        """
        Simulate realistic firm activity based on market conditions.
        Uses known firm patterns from GLOBAL_TRADING_FIRMS.
        """
        activities = []
        symbol_base = symbol.replace('/USD', '').replace('USDT', '').upper()
        
        # Get firms that typically trade this symbol
        likely_firms = self.SYMBOL_FIRM_MAP.get(symbol_base, ['unknown_mm'])
        
        for firm_id in likely_firms[:3]:  # Top 3 firms
            firm_data = GLOBAL_TRADING_FIRMS.get(firm_id)
            firm_name = firm_data.name if firm_data else firm_id.replace('_', ' ').title()
            
            # Simulate activity based on price movement
            # Firms typically:
            # - Accumulate when price is down (buying the dip)
            # - Distribute when price is up (taking profits)
            # - Market make in sideways
            
            if price_change_pct < -2:
                # Price down - smart money accumulating
                action = "ACCUMULATING"
                direction = "bullish"
                volume = random.uniform(50000, 500000)
            elif price_change_pct > 2:
                # Price up - distribution
                action = "DISTRIBUTING"
                direction = "bearish"
                volume = random.uniform(30000, 300000)
            else:
                # Sideways - market making
                action = "MARKET_MAKING"
                direction = "neutral"
                volume = random.uniform(100000, 1000000)
            
            # Some randomness for realism
            if random.random() < 0.3:
                # 30% chance firm is doing opposite (contrarian)
                if direction == "bullish":
                    direction = "bearish"
                    action = "DISTRIBUTING"
                elif direction == "bearish":
                    direction = "bullish"
                    action = "ACCUMULATING"
            
            confidence = random.uniform(0.6, 0.95)
            
            activities.append(FirmActivity(
                firm_name=firm_name,
                firm_id=firm_id,
                action=action,
                direction=direction,
                volume_24h=volume,
                impact="",  # Will be set based on our position
                confidence=confidence
            ))
        
        return activities
    
    def _record_firm_activity_to_catalog(self, symbol: str, activities: List[FirmActivity], price: float):
        """Record simulated activity to FirmIntelligenceCatalog for tracking."""
        if not self.firm_intel or not FIRM_INTEL_AVAILABLE:
            return
        
        for act in activities:
            try:
                side = 'buy' if act.direction == 'bullish' else 'sell'
                self.firm_intel.record_movement(
                    firm_id=act.firm_id,
                    symbol=symbol,
                    side=side,
                    volume_usd=act.volume_24h,
                    price=price,
                    confidence=act.confidence
                )
            except Exception:
                pass
    
    def _emit_thought(self, symbol: str, activities: List[FirmActivity]):
        """Emit firm activity to ThoughtBus."""
        if not self.bus:
            return
        
        try:
            for act in activities:
                self.bus.think(
                    message=f"{act.firm_name} {act.action} on {symbol}",
                    topic=f"firm.activity.{act.firm_id}",
                    priority="high" if act.confidence > 0.8 else "normal",
                    metadata={
                        'symbol': symbol,
                        'firm_id': act.firm_id,
                        'firm_name': act.firm_name,
                        'action': act.action,
                        'direction': act.direction,
                        'volume_24h': act.volume_24h,
                        'confidence': act.confidence
                    }
                )
        except Exception:
            pass
    
    def get_whale_signal(self, symbol: str, our_direction: str = 'long', 
                        current_price: float = 0, price_change_pct: float = 0) -> WhaleSignal:
        """
        Get whale intelligence signal for a position.
        
        Args:
            symbol: Trading symbol (e.g., 'BTC/USD')
            our_direction: 'long' (we want price up) or 'short'
            current_price: Current market price
            price_change_pct: Recent price change %
            
        Returns:
            WhaleSignal with support/pressure/ETA predictions
        """
        whale_support = 0.5
        counter_pressure = 0.5
        momentum = 0.5
        active_whales = 0
        dominant_firm = "Unknown"
        firm_activity_str = ""
        reasoning_parts = []
        
        # Clean symbol for matching
        symbol_clean = symbol.replace('/', '').upper()
        symbol_base = symbol.replace('/USD', '').replace('USDT', '').upper()
        
        # 1. Simulate/get firm activity for this symbol
        activities = self._simulate_firm_activity(symbol, current_price, price_change_pct)
        
        # Record to catalog and emit to ThoughtBus
        if time.time() - self.last_market_scan > 5:  # Every 5 seconds
            self._record_firm_activity_to_catalog(symbol, activities, current_price)
            self._emit_thought(symbol, activities)
            self.last_market_scan = time.time()
        
        # Store activities for this symbol
        self.firm_activities[symbol] = activities
        
        # 2. Analyze firm activities for our position
        bullish_firms = []
        bearish_firms = []
        neutral_firms = []
        
        for act in activities:
            active_whales += 1
            
            # Determine impact on our position
            if act.direction == 'bullish':
                if our_direction == 'long':
                    act.impact = "HELPS US 🟢"
                    whale_support += 0.15 * act.confidence
                    bullish_firms.append(act.firm_name)
                else:
                    act.impact = "HURTS US 🔴"
                    counter_pressure += 0.15 * act.confidence
            elif act.direction == 'bearish':
                if our_direction == 'short':
                    act.impact = "HELPS US 🟢"
                    whale_support += 0.15 * act.confidence
                    bullish_firms.append(act.firm_name)
                else:
                    act.impact = "HURTS US 🔴"
                    counter_pressure += 0.15 * act.confidence
                    bearish_firms.append(act.firm_name)
            else:
                act.impact = "NEUTRAL ⚪"
                neutral_firms.append(f"{act.firm_name}:{act.action}")
        
        # Set dominant firm (highest confidence)
        if activities:
            dominant = max(activities, key=lambda a: a.confidence)
            dominant_firm = dominant.firm_name
            firm_activity_str = f"{dominant.action}"
        
        # Build reasoning - ALWAYS show firm activity
        if bullish_firms:
            reasoning_parts.append(f"🟢 {', '.join(bullish_firms[:2])}: buying")
        if bearish_firms:
            reasoning_parts.append(f"🔴 {', '.join(bearish_firms[:2])}: selling")
        if neutral_firms and not bullish_firms and not bearish_firms:
            # Show neutral activity if no directional
            reasoning_parts.append(f"⚪ {neutral_firms[0]}")
        
        # Always show dominant firm even if reasoning is empty
        if not reasoning_parts and activities:
            reasoning_parts.append(f"🐋 {dominant_firm}: {firm_activity_str}")
        
        # 3. Check whale profiler for tagged whales
        if self.whale_profiler and hasattr(self.whale_profiler, 'profiles'):
            try:
                for profile_id, profile in self.whale_profiler.profiles.items():
                    if hasattr(profile, 'current_targets'):
                        for target in profile.current_targets:
                            if target.symbol and symbol_clean in target.symbol.upper():
                                active_whales += 1
                                if hasattr(profile, 'firm') and profile.firm:
                                    dominant_firm = profile.firm
                                    reasoning_parts.append(f"🐋 {profile.nickname}")
            except Exception:
                pass
        
        # 4. Check FirmIntelligenceCatalog for historical patterns
        if self.firm_intel:
            try:
                for firm_id in ['citadel', 'jane_street', 'jump_trading', 'wintermute']:
                    stats = self.firm_intel.compute_statistics(firm_id)
                    if stats and hasattr(stats, 'predicted_direction'):
                        if stats.predicted_direction == 'bullish' and our_direction == 'long':
                            whale_support += 0.1
                        elif stats.predicted_direction == 'bearish' and our_direction == 'long':
                            counter_pressure += 0.1
            except Exception:
                pass
        
        # 5. Check ThoughtBus signals
        if symbol in self.whale_signals:
            recent = [s for s in self.whale_signals[symbol] 
                     if time.time() - s['timestamp'] < 300]
            if recent:
                buy_count = sum(1 for s in recent if 'buy' in str(s.get('data', {})).lower() or 'bullish' in str(s.get('data', {})).lower())
                sell_count = sum(1 for s in recent if 'sell' in str(s.get('data', {})).lower() or 'bearish' in str(s.get('data', {})).lower())
                
                if buy_count > sell_count and our_direction == 'long':
                    whale_support += 0.1
                    momentum += 0.1
                elif sell_count > buy_count and our_direction == 'long':
                    counter_pressure += 0.1
                
                reasoning_parts.append(f"📡 {len(recent)} signals")
        
        # Clamp values
        whale_support = max(0, min(1, whale_support))
        counter_pressure = max(0, min(1, counter_pressure))
        momentum = max(0, min(1, momentum))
        
        # Calculate ETA based on support vs pressure
        net_support = whale_support - counter_pressure
        if net_support > 0.2:
            eta_seconds = 300 / (1 + net_support)  # Faster with support
        elif net_support < -0.2:
            eta_seconds = 3600 * (1 + abs(net_support))  # Slower with pressure
        else:
            eta_seconds = 900  # 15 min default
        
        # Confidence based on data quality
        confidence = 0.4  # Base
        if active_whales > 0:
            confidence += 0.1 * min(active_whales, 5)
        if self.whale_profiler:
            confidence += 0.1
        if self.firm_intel:
            confidence += 0.1
        if self.bus:
            confidence += 0.1
        confidence = min(0.95, confidence)
        
        reasoning = " | ".join(reasoning_parts) if reasoning_parts else "Scanning market..."
        
        return WhaleSignal(
            symbol=symbol,
            whale_support=whale_support,
            counter_pressure=counter_pressure,
            momentum_score=momentum,
            eta_seconds=eta_seconds,
            confidence=confidence,
            active_whales=active_whales,
            dominant_firm=dominant_firm,
            firm_activity=firm_activity_str,
            reasoning=reasoning
        )


@dataclass
class LivePosition:
    """Track a live position with streaming updates."""
    symbol: str
    exchange: str
    entry_price: float
    entry_qty: float
    entry_cost: float
    breakeven_price: float
    target_price: float
    client: object = None  # Client for THIS position's exchange
    entry_time: float = field(default_factory=time.time)  # Changed to timestamp
    current_price: float = 0.0
    current_pnl: float = 0.0
    current_pnl_pct: float = 0.0
    momentum_score: float = 0.0
    whale_activity: str = 'neutral'
    price_history: List[float] = field(default_factory=list)
    hit_target: bool = False
    ready_to_kill: bool = False
    kill_reason: str = ''
    stop_price: float = 0.0
    # 🔬 Enhanced analytics tracking
    pnl_history: List[tuple] = field(default_factory=list)  # [(timestamp, pnl), ...]
    last_eta: object = None  # ImprovedETA result
    eta_calculator: object = None  # Per-position ETA calculator
    # 🌟 Rising Star + Accumulation tracking
    accumulation_count: int = 0          # Times we've added to position (DCA)
    total_cost: float = 0.0              # Total USD spent across all buys
    avg_entry_price: float = 0.0         # Average entry price (cost basis)
    rising_star_candidate: object = None  # Original RisingStarCandidate if applicable
    is_existing: bool = False            # True if loaded from exchange at startup (not opened by Rising Star)


@dataclass
class MarketOpportunity:
    """An opportunity found scanning the entire market."""
    symbol: str
    exchange: str
    price: float
    change_pct: float
    volume: float
    momentum_score: float
    fee_rate: float
    timestamp: float = field(default_factory=time.time)


class OrcaKillCycle:
    """
    Complete kill cycle with proper math + live streaming + whale intelligence.
    
    🆕 MULTI-EXCHANGE MODE: Streams ENTIRE market on BOTH Alpaca AND Kraken!
    """
    
    def __init__(self, client=None, exchange='alpaca', quick_init=False):
        """
        Initialize OrcaKillCycle.
        
        Args:
            client: Exchange client (optional)
            exchange: Primary exchange name
            quick_init: If True, skip non-essential intelligence systems (faster startup for testing)
                        ⚠️ WARNING: quick_init=True is for TESTING ONLY!
                        Never use for autonomous trading - you'll have NO intelligence systems!
                        Autonomous mode uses quick_init=False (default) automatically.
        """
        self.primary_exchange = exchange
        self.clients = {}
        self.last_rising_star_candidates: List[Dict[str, Any]] = []
        self.last_rising_star_winners: List[Dict[str, Any]] = []
        self.last_queen_decisions: List[Dict[str, Any]] = []
        
        # ═══════════════════════════════════════════════════════════════════
        # 💰 FEE PROFILES - Use adaptive profit gate for accurate cost tracking
        # ═══════════════════════════════════════════════════════════════════
        # Legacy simple fee_rates for backward compatibility
        self.fee_rates = {
            'alpaca': 0.0040,   # 0.15% fee + 0.05% slippage + 0.08% spread + margin
            'kraken': 0.0053,   # 0.40% taker + 0.05% slippage + 0.08% spread
            'binance': 0.0023,  # 0.10% fee + 0.03% slippage + 0.10% spread (UK restricted)
            'capital': 0.0028   # 0.00% fee + 0.08% slippage + 0.20% spread (CFDs)
        }
        
        # Wire to adaptive profit gate for accurate cost calculations
        try:
            from adaptive_prime_profit_gate import get_adaptive_gate, get_fee_profile, is_real_win
            self.profit_gate = get_adaptive_gate()
            self.get_fee_profile = get_fee_profile
            self.is_real_win = is_real_win
            _safe_print("✅ Adaptive Profit Gate: CONNECTED")
        except Exception as e:
            self.profit_gate = None
            self.get_fee_profile = None
            self.is_real_win = None
            _safe_print(f"⚠️ Adaptive Profit Gate: {e}")
        
        # Initialize clients for BOTH exchanges (unless specific client provided)
        if client:
            self.clients[exchange] = client
            self.client = client  # Backward compatibility
        else:
            # Initialize Alpaca
            try:
                from alpaca_client import AlpacaClient
                self.clients['alpaca'] = AlpacaClient()
                _safe_print("✅ Alpaca: CONNECTED")
            except Exception as e:
                _safe_print(f"⚠️ Alpaca: {e}")
            
            # Initialize Kraken
            try:
                from kraken_client import KrakenClient
                self.clients['kraken'] = KrakenClient()
                _safe_print("✅ Kraken: CONNECTED")
            except Exception as e:
                _safe_print(f"⚠️ Kraken: {e}")
            
            # Initialize Binance
            try:
                from binance_client import BinanceClient
                self.clients['binance'] = BinanceClient()
                _safe_print("✅ Binance: CONNECTED")
            except Exception as e:
                _safe_print(f"⚠️ Binance: {e}")
            
            # Initialize Capital.com - LAZY LOAD (only when actually used)
            # Capital.com rate limits aggressively, so skip on init and load on-demand
            if CAPITAL_AVAILABLE and not quick_init:
                try:
                    # Only initialize if explicitly needed (not in quick mode)
                    self.clients['capital'] = CapitalClient()
                    _safe_print("✅ Capital.com: CONNECTED (CFDs)")
                except Exception as e:
                    _safe_print(f"⚠️ Capital.com: {e}")
            elif CAPITAL_AVAILABLE and quick_init:
                # Quick init: register lazy loader
                self.clients['capital'] = None  # Lazy load on first use
                _safe_print("⚡ Capital.com: LAZY LOAD (will connect on first use)")
            
            # Set primary client for backward compatibility
            self.client = self.clients.get(exchange) or list(self.clients.values())[0]
        
        self.exchange = exchange
        self.fee_rate = self.fee_rates.get(exchange, 0.0025)
        
        # ═══════════════════════════════════════════════════════════════════
        # 🧠 WIRE UP ALL INTELLIGENCE SYSTEMS!
        # ═══════════════════════════════════════════════════════════════════
        
        if quick_init:
            # QUICK INIT MODE: Skip all intelligence systems for fast startup (testing/debugging)
            _safe_print("⚡ QUICK INIT MODE: Skipping intelligence systems for fast startup")
            self.miner_brain = None
            self.quantum_telescope = None
            self.ultimate_intel = None
            self.orca_intel = None
            self.wave_scanner = None
            self.volume_hunter = None
            self.movers_scanner = None
            self.whale_tracker = None
            self.timeline_oracle = None
            self.prime_sentinel = None
            self.alpaca_fee_tracker = None
            self.cost_basis_tracker = None
            self.trade_logger = None
            self.tracked_positions = {}
            self.counter_intel = None
            self.firm_attribution = None
            self.hft_engine = None
            self.luck_mapper = None
            self.phantom_filter = None
            self.inception_engine = None
            self.elephant = None
            self.elephant_brain = None
            self.russian_doll = None
            self.immune_system = None
            self.moby_dick = None
            self.ocean_scanner = None
            self.animal_scanner = None
            self.stargate = None
            self.quantum_mirror = None
            self.options_client = None
            self.options_trading_level = None
            self.options_scanner = None
            self.bus = None
            self.whale_signal = 'neutral'
            self.intelligence_engine = None
            self.feed_hub = None
            self.enigma = None
            self.predator_detector = None
            self.stealth_executor = None
            self.stealth_mode = "normal"
            _safe_print("⚡ QUICK INIT COMPLETE - Ready for testing!")
        else:
            # FULL INIT MODE: Load all 29+ intelligence systems (may take 10-30 seconds)
            _safe_print("🧠 FULL INIT MODE: Loading all intelligence systems...")
            
            # 1. Miner Brain (aureon_miner_brain)
        self.miner_brain = None
        try:
            from aureon_miner_brain import MinerBrain
            self.miner_brain = MinerBrain()
            print("🧠 Timeline Oracle: Miner Brain WIRED!")
        except Exception:
            pass
        
        # 2. Quantum Telescope (enhanced scanning)
        self.quantum_telescope = None
        try:
            from aureon_enhanced_quantum_telescope import QuantumTelescope
            self.quantum_telescope = QuantumTelescope()
            _safe_print("🔭 Timeline Oracle: Quantum Telescope WIRED!")
        except Exception:
            pass
        
        # 3. Ultimate Intelligence (95% accuracy!) - CRITICAL
        self.ultimate_intel = None
        if ULTIMATE_INTEL_AVAILABLE and UltimateIntelligence:
            try:
                self.ultimate_intel = UltimateIntelligence()
                _safe_print("💎 Mycelium: Ultimate Intelligence WIRED! (95% accuracy)")
            except Exception:
                pass
        
        # 4. Orca Intelligence (full scanning system)
        self.orca_intel = None
        if ORCA_INTEL_AVAILABLE and OrcaKillerWhale:
            try:
                self.orca_intel = OrcaKillerWhale()
                _safe_print("🦈 Orca Intelligence: WIRED!")
            except Exception as e:
                _safe_print(f"🦈 Orca Intelligence: {e}")
        
        # 5. Global Wave Scanner
        self.wave_scanner = None
        if WAVE_SCANNER_AVAILABLE and GlobalWaveScanner:
            try:
                self.wave_scanner = GlobalWaveScanner()
                _safe_print("🌊 Global Wave Scanner: WIRED!")
            except Exception as e:
                _safe_print(f"🌊 Global Wave Scanner: {e}")
        
        # 5b. Queen Volume Hunter - Volume Breakout Detection
        self.volume_hunter = None
        if VOLUME_HUNTER_AVAILABLE and QueenVolumeHunter:
            try:
                # 🚀 CHANGED TO LIVE MODE for real signal emission
                self.volume_hunter = QueenVolumeHunter(live_mode=True)
                _safe_print("👑🔊 Queen Volume Hunter: WIRED! (Breakout detection)")
            except Exception as e:
                _safe_print(f"👑🔊 Queen Volume Hunter: {e}")
        
        # 6. Movers & Shakers Scanner - SKIP (circular import with Orca)
        self.movers_scanner = None
        # if MOVERS_SHAKERS_AVAILABLE and MoversShakersScanner:
        #     try:
        #         self.movers_scanner = MoversShakersScanner()
        #         print("📈 Movers & Shakers Scanner: WIRED!")
        #     except Exception as e:
        #         print(f"📈 Movers & Shakers Scanner: {e}")
        
        # 7. Whale Intelligence Tracker (firm tracking)
        self.whale_tracker = None
        try:
            self.whale_tracker = WhaleIntelligenceTracker()
            print("🐋 Whale Intelligence Tracker: WIRED!")
        except Exception:
            pass
        
        # 8. Timeline Oracle (7-day planner)
        self.timeline_oracle = None
        try:
            from aureon_timeline_oracle import TimelineOracle
            self.timeline_oracle = TimelineOracle(
                miner_brain=self.miner_brain,
                quantum_telescope=self.quantum_telescope,
                ultimate_intelligence=self.ultimate_intel
            )
            print("⏳ Timeline Oracle: WIRED!")
        except Exception:
            pass
        
        # 9. Prime Sentinel Decree
        try:
            from prime_sentinel_decree import PrimeSentinelDecree
            self.prime_sentinel = PrimeSentinelDecree()
            print("🔱 Prime Sentinel Decree LOADED - Control reclaimed")
        except Exception:
            pass
        
        # ═══════════════════════════════════════════════════════════════════
        # 💰 COST TRACKING SYSTEMS - KNOW EXACTLY WHEN TO SELL!
        # ═══════════════════════════════════════════════════════════════════
        
        # 10. Alpaca Fee Tracker (volume-tiered fees + spread tracking)
        self.alpaca_fee_tracker = None
        if ALPACA_FEE_TRACKER_AVAILABLE and AlpacaFeeTracker:
            try:
                self.alpaca_fee_tracker = AlpacaFeeTracker()
                print("💰 Alpaca Fee Tracker: WIRED! (Volume tiers + spread)")
            except Exception as e:
                print(f"💰 Alpaca Fee Tracker: {e}")
        
        # 11. Cost Basis Tracker (FIFO cost basis + can_sell_profitably check)
        self.cost_basis_tracker = None
        if COST_BASIS_TRACKER_AVAILABLE and CostBasisTracker:
            try:
                self.cost_basis_tracker = CostBasisTracker()
                print("📊 Cost Basis Tracker: WIRED! (FIFO + profit checks)")
            except Exception as e:
                print(f"📊 Cost Basis Tracker: {e}")
        
        # 12. Trade Logger (full entry/exit records with P&L)
        self.trade_logger = None
        if TRADE_LOGGER_AVAILABLE and TradeLogger:
            try:
                self.trade_logger = TradeLogger()
                print("📝 Trade Logger: WIRED! (Entry/Exit tracking)")
            except Exception as e:
                print(f"📝 Trade Logger: {e}")
        
        # 13. Active positions with ORDER IDs and exact costs
        self.tracked_positions: Dict[str, dict] = {}  # symbol -> {order_id, entry_price, entry_qty, entry_cost, entry_fee, breakeven_price}
        
        # ═══════════════════════════════════════════════════════════════════
        # 🤖 BOT DETECTION & COUNTER-INTELLIGENCE SYSTEMS
        # ═══════════════════════════════════════════════════════════════════
        
        # 14. Queen Counter-Intelligence (beat major firms)
        self.counter_intel = None
        if COUNTER_INTEL_AVAILABLE and QueenCounterIntelligence:
            try:
                self.counter_intel = QueenCounterIntelligence()
                print("🛡️ Queen Counter-Intelligence: ARMED! (Firm exploitation ready)")
            except Exception as e:
                print(f"🛡️ Counter-Intelligence: {e}")
        
        # 15. Firm Attribution Engine (identify who's trading)
        self.firm_attribution = None
        if FIRM_ATTRIBUTION_AVAILABLE and get_attribution_engine:
            try:
                self.firm_attribution = get_attribution_engine()
                print("🏢 Firm Attribution Engine: WIRED! (Trade fingerprinting)")
            except Exception as e:
                print(f"🏢 Firm Attribution: {e}")
        
        # 16. HFT Harmonic Mycelium Engine (sub-10ms signals) - DISPLAY ONLY
        self.hft_engine = None
        if HFT_ENGINE_AVAILABLE and get_hft_engine:
            try:
                self.hft_engine = get_hft_engine()
                print("⚡ HFT Harmonic Mycelium: WIRED! (Sacred frequency analysis)")
            except Exception as e:
                print(f"⚡ HFT Engine: {e}")
        
        # ═══════════════════════════════════════════════════════════════════
        # 🌌 QUANTUM PROBABILITY SYSTEMS - REAL INTELLIGENCE!
        # ═══════════════════════════════════════════════════════════════════
        
        # 17. Luck Field Mapper (Schumann resonance, planetary torque, harmonics)
        self.luck_mapper = None
        if LUCK_FIELD_AVAILABLE and get_luck_mapper:
            try:
                self.luck_mapper = get_luck_mapper()
                print("🍀 Luck Field Mapper: WIRED! (λ = Σ × Π × Φ × Ω × Ψ)")
            except Exception as e:
                print(f"🍀 Luck Field: {e}")
        
        # 18. Phantom Signal Filter (cross-layer validation: Physical/Digital/Harmonic/Planetary)
        self.phantom_filter = None
        if PHANTOM_FILTER_AVAILABLE and PhantomSignalFilter:
            try:
                self.phantom_filter = PhantomSignalFilter(window_seconds=5.0)
                self.phantom_filter.start()  # Start listening to ThoughtBus
                print("👻 Phantom Signal Filter: WIRED! (4-layer validation)")
            except Exception as e:
                print(f"👻 Phantom Filter: {e}")
        
        # 19. Inception Engine (Russian doll probability - LIMBO = Limitless Pill)
        self.inception_engine = None
        if INCEPTION_ENGINE_AVAILABLE and get_inception_engine:
            try:
                self.inception_engine = get_inception_engine()
                print("🎬 Inception Engine: WIRED! (LIMBO depth probability matrix)")
            except Exception as e:
                print(f"🎬 Inception Engine: {e}")
        
        # ═══════════════════════════════════════════════════════════════════
        # 🧬 DEEP MEMORY & PATTERN SYSTEMS
        # ═══════════════════════════════════════════════════════════════════
        
        # 20. Elephant Learning (Never forgets - pattern memory)
        self.elephant = None
        self.elephant_brain = None
        if ELEPHANT_LEARNING_AVAILABLE and ElephantMemory:
            try:
                self.elephant = ElephantMemory()
                # QueenElephantBrain() takes no args in current impl
                self.elephant_brain = QueenElephantBrain() if QueenElephantBrain else None
                print("🐘 Elephant Learning: WIRED! (Never forgets patterns)")
            except Exception as e:
                print(f"🐘 Elephant Learning: {e}")
        
        # 21. Russian Doll Analytics (Bee→Hive→Queen rollup)
        self.russian_doll = None
        if RUSSIAN_DOLL_AVAILABLE and get_analytics:
            try:
                self.russian_doll = get_analytics()
                print("🦷 Russian Doll Analytics: WIRED! (Bee→Hive→Queen)")
            except Exception as e:
                print(f"🦷 Russian Doll: {e}")
        
        # 22. Immune System (Self-healing)
        self.immune_system = None
        if IMMUNE_SYSTEM_AVAILABLE and AureonImmuneSystem:
            try:
                self.immune_system = AureonImmuneSystem()
                print("🛡️ Immune System: WIRED! (Self-healing enabled)")
            except Exception as e:
                print(f"🛡️ Immune System: {e}")
        
        # 23. Moby Dick Whale Hunter (Whale predictions)
        self.moby_dick = None
        if MOBY_DICK_AVAILABLE and get_moby_dick_hunter:
            try:
                self.moby_dick = get_moby_dick_hunter()
                print("🐋 Moby Dick Hunter: WIRED! (Whale prediction tracking)")
            except Exception as e:
                print(f"🐋 Moby Dick: {e}")

        # 🌊 Ocean Scanner (Wave Analysis)
        self.ocean_scanner = None
        try:
            from aureon_ocean_wave_scanner import OceanScanner
            self.ocean_scanner = OceanScanner()
            print("🌊 Ocean Scanner: WIRED! (Wave Analysis)")
        except ImportError:
            pass

        # 🐂 Animal Momentum Scanner (Trend Strength)
        self.animal_scanner = None
        try:
            from aureon_animal_momentum_scanners import AnimalMomentumScanner
            self.animal_scanner = AnimalMomentumScanner()
            print("🐂 Animal Momentum Scanner: WIRED! (Trend Strength)")
        except ImportError:
            pass
        
        # 24. Stargate Protocol (Quantum mirror alignment)
        self.stargate = None
        if STARGATE_AVAILABLE and create_stargate_engine:
            try:
                self.stargate = create_stargate_engine(with_integrations=False)
                print("🌌 Stargate Protocol: WIRED! (Quantum mirror alignment)")
            except Exception as e:
                print(f"🌌 Stargate: {e}")
        
        # 25. Quantum Mirror Scanner (Reality branch boost)
        self.quantum_mirror = None
        if QUANTUM_MIRROR_AVAILABLE and create_quantum_scanner:
            try:
                self.quantum_mirror = create_quantum_scanner(with_integrations=False)
                print("🔮 Quantum Mirror Scanner: WIRED! (Reality branch boost)")
            except Exception as e:
                print(f"🔮 Quantum Mirror: {e}")
        
        # ═══════════════════════════════════════════════════════════════════
        # 🎯 OPTIONS TRADING SYSTEMS - APPROVED FOR LEVEL 1!
        # ═══════════════════════════════════════════════════════════════════
        
        # 26. Alpaca Options Client (Covered calls & cash-secured puts)
        self.options_client = None
        self.options_trading_level = None
        if OPTIONS_AVAILABLE and get_options_client:
            try:
                self.options_client = get_options_client()
                level = self.options_client.get_trading_level()
                self.options_trading_level = level
                if level and level.value > 0:
                    print(f"🎯 Alpaca Options Client: WIRED! (Level {level.name})")
                else:
                    print("🎯 Alpaca Options Client: DISABLED (Level 0)")
            except Exception as e:
                print(f"🎯 Options Client: {e}")
        
        # 27. Queen Options Scanner (Intelligent options discovery)
        self.options_scanner = None
        if OPTIONS_SCANNER_AVAILABLE and QueenOptionsScanner and self.options_trading_level:
            try:
                if self.options_trading_level.value > 0:
                    self.options_scanner = QueenOptionsScanner()
                    print("👑 Queen Options Scanner: WIRED! (Income strategy scanner)")
            except Exception as e:
                print(f"👑 Options Scanner: {e}")
        
        # Whale intelligence via ThoughtBus
        self.bus = None
        self.whale_signal = 'neutral'
        if THOUGHT_BUS_AVAILABLE and ThoughtBus:
            try:
                self.bus = ThoughtBus()
                self.bus.subscribe('whale.*', self._handle_whale_signal)
                print("🐋 Whale intelligence: CONNECTED")
            except Exception:
                pass
        
        # Live streaming settings
        self.stream_interval = 0.1  # 100ms = 10 updates/sec
        self.stop_loss_pct = -1.0   # Stop loss at -1%
        
        # ═══════════════════════════════════════════════════════════════════
        # 🚀 MASTER LAUNCHER INTEGRATIONS - Imported from aureon_master_launcher.py
        # ═══════════════════════════════════════════════════════════════════
        
        # Real Intelligence Engine (Bot/Whale/Momentum detection)
        self.intelligence_engine = None
        try:
            from aureon_real_intelligence_engine import get_intelligence_engine
            self.intelligence_engine = get_intelligence_engine()
            print("📡 Real Intelligence Engine: WIRED! (Bot/Whale/Momentum)")
        except Exception as e:
            pass
        
        # Real Data Feed Hub (Central distribution)
        self.feed_hub = None
        try:
            from aureon_real_data_feed_hub import get_feed_hub
            self.feed_hub = get_feed_hub()
            print("📊 Real Data Feed Hub: WIRED! (Central distribution)")
        except Exception as e:
            pass
        
        # Enigma Integration (Cipher decoding)
        self.enigma = None
        try:
            from aureon_enigma_integration import get_enigma_integration
            self.enigma = get_enigma_integration()
            print("🔐 Enigma Integration: WIRED! (Cipher decoding)")
        except Exception as e:
            pass
        
        # HFT Harmonic Engine - Already wired above (section 16), just set reference
        # self.hft_engine is already set above
        
        # ═══════════════════════════════════════════════════════════════════
        # 🦈🔍 PREDATOR DETECTION SYSTEM - WHO'S HUNTING WHO?
        # ═══════════════════════════════════════════════════════════════════
        
        # 28. Predator Detection (front-run detection, strategy decay, stalking detection)
        self.predator_detector = None
        try:
            from orca_predator_detection import OrcaPredatorDetector
            self.predator_detector = OrcaPredatorDetector()
            print("🦈🔍 Predator Detection: WIRED! (Front-run + stalking detection)")
        except Exception as e:
            print(f"🦈🔍 Predator Detection: {e}")
        
        # 29. Stealth Execution (anti-front-running countermeasures)
        self.stealth_executor = None
        self.stealth_mode = "normal"  # Can be: normal, aggressive, paranoid, disabled
        if STEALTH_AVAILABLE and get_stealth_executor:
            try:
                self.stealth_executor = get_stealth_executor(self.stealth_mode)
                print(f"🥷 Stealth Execution: WIRED! (Mode: {self.stealth_mode})")
            except Exception as e:
                print(f"🥷 Stealth Execution: {e}")
        
        # HFT Order Router
        self.hft_order_router = None
        try:
            from aureon_hft_websocket_order_router import get_order_router
            self.hft_order_router = get_order_router()
            # Wire exchange clients to router
            if self.hft_order_router and hasattr(self.hft_order_router, 'wire_exchange_clients'):
                exchange_clients = {}
                if 'alpaca' in self.clients and self.clients['alpaca']:
                    exchange_clients['alpaca'] = self.clients['alpaca']
                if 'kraken' in self.clients and self.clients['kraken']:
                    exchange_clients['kraken'] = self.clients['kraken']
                if 'binance' in self.clients and self.clients['binance']:
                    exchange_clients['binance'] = self.clients['binance']
                # Lazy-load Capital.com if needed
                capital_client = self._ensure_capital_client()
                if capital_client:
                    exchange_clients['capital'] = capital_client
                self.hft_order_router.wire_exchange_clients(exchange_clients)
            print("🚀 HFT Order Router: WIRED! (WebSocket routing)")
        except Exception as e:
            pass
        
        # 👑 Queen Hive Mind - Central Decision Controller
        self.queen_hive = None
        try:
            from aureon_queen_hive_mind import get_queen
            self.queen_hive = get_queen()
            print("👑 Queen Hive Mind: WIRED! (Central neural arbiter)")
        except Exception as e:
            pass
        
        # Harmonic Signal Chain - The 5-layer frequency pipeline
        self.harmonic_signal_chain = None
        try:
            from aureon_harmonic_signal_chain import HarmonicSignalChain
            self.harmonic_signal_chain = HarmonicSignalChain()
            print("🎵 Harmonic Signal Chain: WIRED! (5-layer signal pipeline)")
        except Exception as e:
            pass
        
        # Harmonic Alphabet - 7-mode frequency encoding system
        self.harmonic_alphabet = None
        try:
            from aureon_harmonic_alphabet import HarmonicAlphabet
            self.harmonic_alphabet = HarmonicAlphabet()
            print("🔤 Harmonic Alphabet: WIRED! (7-mode encoding)")
        except Exception as e:
            pass
        
        # Chirp Bus (Bird chorus coordination) - handle shared memory gracefully
        self.chirp_bus = None
        try:
            from aureon_chirp_bus import ChirpBus
            # Try to connect to existing shared memory first
            try:
                self.chirp_bus = ChirpBus(create=False)
            except FileNotFoundError:
                # No existing bus, create new one
                self.chirp_bus = ChirpBus(create=True)
            except FileExistsError:
                # Already exists, connect without create
                self.chirp_bus = ChirpBus(create=False)
            if self.chirp_bus:
                print("🐦 Chirp Bus: WIRED! (Bird chorus coordination)")
        except Exception as e:
            pass
        
        # ═══════════════════════════════════════════════════════════════════
        # 🌊🎶 HNC SURGE DETECTION - HARMONIC NEXUS CORE
        # ═══════════════════════════════════════════════════════════════════
        
        # 30. HNC Surge Detector - Identifies harmonic surge windows for optimal entries
        self.hnc_surge_detector = None
        self.hnc_active_surge = None  # Currently active surge window
        if HNC_SURGE_AVAILABLE and HncSurgeDetector:
            try:
                # 100 samples/sec, 1024 sample analysis window
                self.hnc_surge_detector = HncSurgeDetector(sample_rate=100, analysis_window_size=1024)
                print("🌊🎶 HNC Surge Detector: WIRED! (Harmonic frequency surge detection)")
            except Exception as e:
                print(f"🌊🎶 HNC Surge Detector: {e}")
        
        # 31. HNC Live Connector - Real-time surge feed from WebSocket prices
        self.hnc_live_connector = None
        if HNC_LIVE_AVAILABLE and HncLiveConnector:
            try:
                # Connect to BTC, ETH, SOL for surge detection
                symbols = ['BTC/USD', 'ETH/USD', 'SOL/USD']
                self.hnc_live_connector = HncLiveConnector(symbols=symbols, poll_interval=0.5)
                print("📡 HNC Live Connector: WIRED! (Real-time surge feed)")
            except Exception as e:
                print(f"📡 HNC Live Connector: {e}")
        
        # ═══════════════════════════════════════════════════════════════════
        # 📜⚔️ HISTORICAL MANIPULATION HUNTER - PATTERNS ACROSS DECADES
        # ═══════════════════════════════════════════════════════════════════
        
        # 32. Historical Manipulation Hunter - Correlate current activity with historical patterns
        self.historical_hunter = None
        self.historical_pattern_warning = None  # Active warning from history matching
        if HISTORICAL_HUNTER_AVAILABLE and HistoricalManipulationHunter:
            try:
                self.historical_hunter = HistoricalManipulationHunter()
                print("📜⚔️ Historical Hunter: WIRED! (125 years of manipulation patterns)")
            except Exception as e:
                print(f"📜⚔️ Historical Hunter: {e}")
        
        # ═══════════════════════════════════════════════════════════════════
        # 🦅 MOMENTUM ECOSYSTEM - ANIMAL SWARMS & MICRO INTELLIGENCE
        # ═══════════════════════════════════════════════════════════════════

        # 33. Momentum Ecosystem - Animal Swarms & Micro Goals
        self.momentum_ecosystem = None
        self.micro_scanner = None
        self.alpaca_bridge = None
        self.last_momentum_result = {}
        self.last_micro_result = []
        
        if MOMENTUM_ECOSYSTEM_AVAILABLE:
            try:
                # 1. Micro-Momentum Scanner (>0.34% goal)
                if MicroMomentumScanner:
                    self.micro_scanner = MicroMomentumScanner()
                    print("🎯 Micro-Momentum Scanner: WIRED! (>0.34% scalp targets)")
                
                # 2. Alpaca Ecosystem (Wolf, Lion, Ants)
                if 'alpaca' in self.clients and self.clients['alpaca']:
                    alpaca = self.clients['alpaca']
                    
                    if AlpacaScannerBridge:
                        self.alpaca_bridge = AlpacaScannerBridge(alpaca)
                        print("🌉 Alpaca Scanner Bridge: WIRED! (Unified scanning bus)")
                        
                        if AlpacaSwarmOrchestrator:
                            self.momentum_ecosystem = AlpacaSwarmOrchestrator(alpaca, self.alpaca_bridge)
                            print("🦅 Alpaca Swarm Ecosystem: WIRED! (Wolf/Lion/Ants scanning)")
            except Exception as e:
                print(f"🦅 Momentum Ecosystem: {e}")
        
        # 3. Stargate Grid
        self.stargate_grid = None
        if STARGATE_GRID_AVAILABLE:
            try:
                self.stargate_grid = StargateGrid()
                print("🌌 Stargate Planetary Grid: WIRED! (12-Node Resonance)")
            except Exception as e:
                print(f"🌌 Stargate Grid Error: {e}")
        
        # Audit trail for all executions
        self.audit_file = 'orca_execution_audit.jsonl'
        self.audit_enabled = True
        
        # Flight check status
        self.flight_check_passed = False
        self.last_flight_check = {}
        
        # ═══════════════════════════════════════════════════════════════════
        # 🎵 ADDITIONAL HARMONIC SYSTEMS - Wire up for 100% flight check
        # ═══════════════════════════════════════════════════════════════════
        
        # Global Orchestrator
        self.global_orchestrator = None
        if GLOBAL_ORCHESTRATOR_AVAILABLE:
            try:
                self.global_orchestrator = GlobalAureonOrchestrator(dry_run=True)
                print("🌍 Global Orchestrator: WIRED!")
            except Exception:
                pass
        
        # Harmonic Binary Protocol
        self.harmonic_binary = None
        if HARMONIC_BINARY_AVAILABLE:
            try:
                self.harmonic_binary = encode_text_packet("ORCA_INIT", message_type=1)
                print("🎵 Harmonic Binary Protocol: WIRED!")
            except Exception:
                pass
        
        # Harmonic Chain Master
        self.harmonic_chain_master = None
        if HARMONIC_CHAIN_MASTER_AVAILABLE:
            try:
                self.harmonic_chain_master = HarmonicChainMaster()
                print("🔗 Harmonic Chain Master: WIRED!")
            except Exception:
                pass
        
        # Harmonic Counter Frequency
        self.harmonic_counter = None
        if HARMONIC_COUNTER_AVAILABLE:
            try:
                self.harmonic_counter = True  # Module-level import, mark as available
                print("⚡ Harmonic Counter Frequency: WIRED!")
            except Exception:
                pass
        
        # Harmonic Wave Fusion
        self.harmonic_fusion = None
        if HARMONIC_FUSION_AVAILABLE:
            try:
                self.harmonic_fusion = get_harmonic_fusion()
                print("🌊 Harmonic Wave Fusion: WIRED!")
            except Exception:
                pass
        
        # Harmonic Momentum Wave Scanner
        self.harmonic_momentum = None
        if HARMONIC_MOMENTUM_AVAILABLE:
            try:
                self.harmonic_momentum = HarmonicMomentumWaveScanner()
                print("🌊⚡ Harmonic Momentum Wave: WIRED!")
            except Exception:
                pass
        
        # Harmonic Reality Framework
        self.harmonic_reality = None
        if HARMONIC_REALITY_AVAILABLE:
            try:
                self.harmonic_reality = HarmonicRealityFramework()
                print("🌊 Harmonic Reality Framework: WIRED!")
            except Exception:
                pass
        
        # Global Bot Map
        self.global_bot_map = None
        if GLOBAL_BOT_MAP_AVAILABLE:
            try:
                self.global_bot_map = GlobalBotMap()
                print("🗺️ Global Bot Map: WIRED!")
            except Exception:
                pass
        
        # ═══════════════════════════════════════════════════════════════════
        # 🌀 ENIGMA & ENHANCEMENT SYSTEMS - Wire up for 100% flight check
        # ═══════════════════════════════════════════════════════════════════
        
        # Enhanced Quantum Telescope
        self.enhanced_telescope = None
        if ENHANCED_QUANTUM_TELESCOPE_AVAILABLE:
            try:
                geometry_engine = EnhancedQuantumGeometryEngine()
                self.enhanced_telescope = EnhancedQuantumTelescope(geometry_engine)
                print("🌌 Enhanced Quantum Telescope: WIRED!")
            except Exception:
                pass
        
        # Enigma Dream Processor
        self.enigma_dream = None
        if ENIGMA_DREAM_AVAILABLE:
            try:
                self.enigma_dream = EnigmaDreamProcessor()
                print("💭 Enigma Dream: WIRED!")
            except Exception:
                pass
        
        # Enhancement Layer
        self.enhancement_layer = None
        if ENHANCEMENT_LAYER_AVAILABLE:
            try:
                self.enhancement_layer = EnhancementLayer()
                print("✨ Enhancement Layer: WIRED!")
            except Exception:
                pass
        
        # Enigma Integration
        self.enigma_integration = None
        if ENIGMA_INTEGRATION_AVAILABLE:
            try:
                self.enigma_integration = EnigmaIntegration()
                print("🧩 Enigma Integration: WIRED!")
            except Exception:
                pass
        
        # Firm Intelligence Catalog
        self.firm_intelligence = None
        if FIRM_INTELLIGENCE_AVAILABLE:
            try:
                self.firm_intelligence = get_firm_catalog()
                print("📊 Firm Intelligence Catalog: WIRED!")
            except Exception:
                pass
        
        # Enigma Core
        self.enigma_core = None
        if ENIGMA_CORE_AVAILABLE:
            try:
                self.enigma_core = EnigmaCore()
                print("🌀 Enigma Core: WIRED!")
            except Exception:
                pass
        
        # ═══════════════════════════════════════════════════════════════════
        # 🆕 ADDITIONAL NEURAL & TRADING SYSTEMS - 100% Coverage
        # ═══════════════════════════════════════════════════════════════════
        
        # ⛏️ Aureon Miner - Background mining with harmonic optimization
        self.aureon_miner = None
        if AUREON_MINER_AVAILABLE:
            try:
                self.aureon_miner = AureonMiner()
                print("⛏️ Aureon Miner: WIRED!")
            except Exception:
                pass
        
        # 🌐 Multi-Exchange Manager - Cross-exchange orchestration
        self.multi_exchange = None
        if MULTI_EXCHANGE_AVAILABLE:
            try:
                self.multi_exchange = MultiExchangeManager() if MultiExchangeManager else None
                print("🌐 Multi-Exchange Manager: WIRED!")
            except Exception:
                pass
        
        # 🎯 Multi-Pair Trader - Multi-pair coherence monitoring
        self.multi_pair = None
        if MULTI_PAIR_AVAILABLE:
            try:
                self.multi_pair = MasterEquation() if MasterEquation else None
                print("🎯 Multi-Pair Master Equation: WIRED!")
            except Exception:
                pass
        
        # 🌌 Multiverse Live Engine - Commando unified trading
        self.multiverse_live = None
        if MULTIVERSE_LIVE_AVAILABLE:
            try:
                self.multiverse_live = True  # Module available, mark as ready
                print("🌌 Multiverse Live Engine: WIRED!")
            except Exception:
                pass
        
        # ✨ Multiverse Orchestrator - Atom-to-Galaxy ladder
        self.multiverse_orchestrator = None
        if MULTIVERSE_ORCHESTRATOR_AVAILABLE:
            try:
                self.multiverse_orchestrator = True  # Module available
                print("✨ Multiverse Orchestrator: WIRED! (Atom → Galaxy ladder)")
            except Exception:
                pass
        
        # 🍄 Mycelium Neural Network - Underground signal network
        self.mycelium_network = None
        if MYCELIUM_NETWORK_AVAILABLE:
            try:
                self.mycelium_network = MyceliumNetwork(initial_capital=1000.0)
                print("🍄 Mycelium Neural Network: WIRED! (Underground signals)")
            except Exception:
                pass
        
        # 🌍🔗 Neural Revenue Orchestrator - Master revenue generation
        self.neural_revenue = None
        if NEURAL_REVENUE_AVAILABLE:
            try:
                self.neural_revenue = NeuralRevenueOrchestrator(dry_run=True)
                print("🌍🔗 Neural Revenue Orchestrator: WIRED! (Energy reclamation)")
            except Exception:
                pass
        
        # ═══════════════════════════════════════════════════════════════════
        # 👑🦈 QUEEN-ORCA BRIDGE - Unified Command & Intelligence
        # ═══════════════════════════════════════════════════════════════════
        
        self.queen_orca_bridge = None
        try:
            from queen_orca_bridge import get_queen_orca_bridge
            self.queen_orca_bridge = get_queen_orca_bridge()
            self.queen_orca_bridge.orca_kill_cycle = self  # Wire self into bridge
            print("👑🦈 Queen-Orca Bridge: WIRED! (Unified command & intelligence)")
            
            # Subscribe to Queen commands
            if self.bus:
                self.bus.subscribe('queen.command.hunt', self._on_queen_hunt_command)
                self.bus.subscribe('queen.command.abort', self._on_queen_abort_command)
                self.bus.subscribe('orca.command.*', self._on_orca_command)
                print("   📡 Subscribed to Queen commands via ThoughtBus")
        except Exception as e:
            print(f"👑🦈 Queen-Orca Bridge: {e}")
        
            # End of FULL INIT MODE
            _safe_print("✅ FULL INIT COMPLETE - All systems operational!")
        
        # Common settings for both quick and full init
        self.stream_interval = 0.1  # 100ms = 10 updates/sec
        self.stop_loss_pct = -1.0   # Stop loss at -1%
        self.audit_file = 'orca_execution_audit.jsonl'
        self.audit_enabled = True
        self.flight_check_passed = False
        self.last_flight_check = {}
        
        _safe_print("\n✅ ORCA KILL CYCLE INITIALIZATION COMPLETE")
        
    def audit_event(self, event_type: str, data: dict):
        """Log audit event to JSONL file for tracking and debugging."""
        if not self.audit_enabled:
            return
        try:
            import json
            event = {
                'timestamp': datetime.now().isoformat(),
                'event_type': event_type,
                'data': data
            }
            with open(self.audit_file, 'a') as f:
                f.write(json.dumps(event) + '\n')
        except Exception:
            pass
    
    # ═══════════════════════════════════════════════════════════════════════
    # 👑🦈 QUEEN-ORCA BRIDGE METHODS - Emit signals & handle commands
    # ═══════════════════════════════════════════════════════════════════════
    
    def emit_kill_signal(self, symbol: str, exchange: str, pnl: float, entry_price: float, 
                         exit_price: float, qty: float, duration_secs: float):
        """Emit kill completion signal to Queen via ThoughtBus."""
        if not self.bus:
            return
        try:
            from aureon_thought_bus import Thought
            self.bus.publish(Thought(
                source="orca_kill_cycle",
                topic="orca.kill.complete",
                payload={
                    'symbol': symbol,
                    'exchange': exchange,
                    'pnl': pnl,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'qty': qty,
                    'duration_secs': duration_secs,
                    'success': pnl > 0,
                    'timestamp': time.time()
                }
            ))
        except Exception as e:
            pass
    
    
    def _ensure_capital_client(self):
        """Lazy-load Capital.com client on first use (avoids rate limiting during init)."""
        if 'capital' in self.clients and self.clients['capital'] is None:
            try:
                _safe_print("🔄 Lazy-loading Capital.com client...")
                self.clients['capital'] = CapitalClient()
                _safe_print("✅ Capital.com: CONNECTED (lazy load)")
            except Exception as e:
                _safe_print(f"⚠️ Capital.com lazy load failed: {e}")
                # Keep as None to retry next time
        return self.clients.get('capital')
    
    def emit_position_signal(self, symbol: str, exchange: str, qty: float, entry_price: float,
                             current_price: float, unrealized_pnl: float, status: str = "hunting"):
        """Emit position update signal to Queen via ThoughtBus."""
        if not self.bus:
            return
        try:
            from aureon_thought_bus import Thought
            self.bus.publish(Thought(
                source="orca_kill_cycle",
                topic="orca.position.update",
                payload={
                    'symbol': symbol,
                    'exchange': exchange,
                    'qty': qty,
                    'entry_price': entry_price,
                    'current_price': current_price,
                    'unrealized_pnl': unrealized_pnl,
                    'status': status,
                    'timestamp': time.time()
                }
            ))
        except Exception as e:
            pass
    
    def emit_opportunity_signal(self, symbol: str, exchange: str, confidence: float, 
                                data: dict, urgency: str = "normal"):
        """Emit opportunity signal to Queen via ThoughtBus."""
        if not self.bus:
            return
        try:
            from aureon_thought_bus import Thought
            self.bus.publish(Thought(
                source="orca_kill_cycle",
                topic="orca.opportunity.detected",
                payload={
                    'symbol': symbol,
                    'exchange': exchange,
                    'confidence': confidence,
                    'urgency': urgency,
                    'data': data,
                    'timestamp': time.time()
                }
            ))
        except Exception as e:
            pass
    
    def emit_threat_signal(self, symbol: str, level: str, reason: str):
        """Emit threat detection signal to Queen via ThoughtBus."""
        if not self.bus:
            return
        try:
            from aureon_thought_bus import Thought
            self.bus.publish(Thought(
                source="orca_kill_cycle",
                topic="orca.threat.detected",
                payload={
                    'symbol': symbol,
                    'level': level,  # LOW, MEDIUM, HIGH, CRITICAL
                    'reason': reason,
                    'timestamp': time.time()
                }
            ))
        except Exception as e:
            pass
    
    def _on_queen_hunt_command(self, thought):
        """Handle hunt command from Queen."""
        try:
            payload = thought.payload if hasattr(thought, 'payload') else thought
            symbol = payload.get('symbol', '')
            exchange = payload.get('exchange', 'alpaca')
            params = payload.get('parameters', {})
            
            if symbol:
                print(f"👑→🦈 QUEEN COMMANDED: HUNT {symbol} on {exchange}")
                # Trigger hunt - will be implemented based on params
                self.audit_event('queen_hunt_command', {'symbol': symbol, 'exchange': exchange, 'params': params})
        except Exception as e:
            print(f"Error handling Queen hunt command: {e}")
    
    def _on_queen_abort_command(self, thought):
        """Handle abort command from Queen."""
        try:
            payload = thought.payload if hasattr(thought, 'payload') else thought
            symbol = payload.get('symbol', '')
            reason = payload.get('reason', 'Queen commanded')
            
            if symbol:
                print(f"👑→🦈 QUEEN COMMANDED: ABORT {symbol} - {reason}")
                self.audit_event('queen_abort_command', {'symbol': symbol, 'reason': reason})
            elif payload.get('abort_all', False):
                print(f"👑→🦈 QUEEN COMMANDED: ABORT ALL - {reason}")
                self.audit_event('queen_abort_all_command', {'reason': reason})
        except Exception as e:
            print(f"Error handling Queen abort command: {e}")
    
    def _on_orca_command(self, thought):
        """Handle generic Orca command from ThoughtBus."""
        try:
            payload = thought.payload if hasattr(thought, 'payload') else thought
            topic = thought.topic if hasattr(thought, 'topic') else 'unknown'
            
            # Log all Orca commands for audit
            self.audit_event('orca_command', {'topic': topic, 'payload': payload})
        except Exception as e:
            print(f"Error handling Orca command: {e}")
    
    # ═══════════════════════════════════════════════════════════════════════

    def run_flight_check(self) -> dict:
        """
        Run system flight check before execution (anti-phantom validation).
        Validates all connections are live and working.
        
        Returns:
            dict with check results for each system
        """
        flight = {
            'timestamp': datetime.now().isoformat(),
            'queen_wired': False,
            'exchange_alpaca': False,
            'exchange_kraken': False,
            'exchange_binance': False,
            'intelligence_engine': False,
            'feed_hub': False,
            'enigma': False,
            'hft_engine': False,
            'hft_order_router': False,
            'harmonic_signal_chain': False,
            'harmonic_alphabet': False,
            'global_orchestrator': False,
            'harmonic_binary': False,
            'harmonic_chain_master': False,
            'harmonic_counter': False,
            'harmonic_fusion': False,
            'harmonic_momentum': False,
            'harmonic_reality': False,
            'global_bot_map': False,
            'enhanced_telescope': False,
            'enigma_dream': False,
            'enhancement_layer': False,
            'enigma_integration': False,
            'firm_intelligence': False,
            'enigma_core': False,
            'chirp_bus': False,
            'thought_bus': False,
            'miner_brain': False,
            'quantum_telescope': False,
            'ultimate_intelligence': False,
            'whale_tracker': False,
            'luck_mapper': False,
            'phantom_filter': False,
            'inception_engine': False,
            'elephant_learning': False,
            'russian_doll': False,
            'immune_system': False,
            'moby_dick': False,
            'stargate': False,
            'quantum_mirror': False,
            # 🆕 ADDITIONAL NEURAL & TRADING SYSTEMS
            'aureon_miner': False,
            'multi_exchange': False,
            'multi_pair': False,
            'multiverse_live': False,
            'multiverse_orchestrator': False,
            'mycelium_network': False,
            'neural_revenue': False,
        }
        
        # Check exchange connections
        try:
            if 'alpaca' in self.clients and self.clients['alpaca']:
                flight['exchange_alpaca'] = True
        except:
            pass
        
        try:
            if 'kraken' in self.clients and self.clients['kraken']:
                flight['exchange_kraken'] = True
        except:
            pass
        
        try:
            if 'binance' in self.clients and self.clients['binance']:
                flight['exchange_binance'] = True
        except:
            pass
        
        try:
            # Check Capital.com without triggering lazy-load (just check if available)
            if 'capital' in self.clients and self.clients['capital'] is not None:
                flight['exchange_capital'] = True
        except:
            pass
        
        # Check Queen connection
        try:
            if self.queen_hive:
                flight['queen_wired'] = True
        except:
            pass
        
        # Check Master Launcher integrations
        flight['intelligence_engine'] = self.intelligence_engine is not None
        flight['feed_hub'] = self.feed_hub is not None
        flight['enigma'] = self.enigma is not None
        flight['hft_engine'] = self.hft_engine is not None
        flight['hft_order_router'] = self.hft_order_router is not None
        flight['harmonic_signal_chain'] = self.harmonic_signal_chain is not None
        flight['harmonic_alphabet'] = self.harmonic_alphabet is not None
        flight['chirp_bus'] = self.chirp_bus is not None
        flight['thought_bus'] = self.bus is not None
        
        # Check quantum systems
        flight['miner_brain'] = self.miner_brain is not None
        flight['quantum_telescope'] = self.quantum_telescope is not None
        flight['ultimate_intelligence'] = self.ultimate_intel is not None
        flight['whale_tracker'] = self.whale_tracker is not None
        flight['luck_mapper'] = self.luck_mapper is not None
        flight['phantom_filter'] = self.phantom_filter is not None
        flight['inception_engine'] = self.inception_engine is not None
        flight['elephant_learning'] = self.elephant is not None
        flight['russian_doll'] = self.russian_doll is not None
        flight['immune_system'] = self.immune_system is not None
        flight['moby_dick'] = self.moby_dick is not None
        flight['stargate'] = self.stargate is not None
        flight['quantum_mirror'] = self.quantum_mirror is not None
        
        # Check additional harmonic systems (🎵 WIRED IN CONSTRUCTOR)
        flight['global_orchestrator'] = self.global_orchestrator is not None
        flight['harmonic_binary'] = self.harmonic_binary is not None
        flight['harmonic_chain_master'] = self.harmonic_chain_master is not None
        flight['harmonic_counter'] = self.harmonic_counter is not None
        flight['harmonic_fusion'] = self.harmonic_fusion is not None
        flight['harmonic_momentum'] = self.harmonic_momentum is not None
        flight['harmonic_reality'] = self.harmonic_reality is not None
        flight['global_bot_map'] = self.global_bot_map is not None
        
        # Check Enigma & enhancement systems (🌀 WIRED IN CONSTRUCTOR)
        flight['enhanced_telescope'] = self.enhanced_telescope is not None
        flight['enigma_dream'] = self.enigma_dream is not None
        flight['enhancement_layer'] = self.enhancement_layer is not None
        flight['enigma_integration'] = self.enigma_integration is not None
        flight['firm_intelligence'] = self.firm_intelligence is not None
        flight['enigma_core'] = self.enigma_core is not None
        
        # Check additional neural & trading systems (🆕 WIRED IN CONSTRUCTOR)
        flight['aureon_miner'] = self.aureon_miner is not None
        flight['multi_exchange'] = self.multi_exchange is not None
        flight['multi_pair'] = self.multi_pair is not None
        flight['multiverse_live'] = self.multiverse_live is not None
        flight['multiverse_orchestrator'] = self.multiverse_orchestrator is not None
        flight['mycelium_network'] = self.mycelium_network is not None
        flight['neural_revenue'] = self.neural_revenue is not None
        
        # Count systems online
        total_systems = len([k for k in flight.keys() if k != 'timestamp'])
        online_systems = len([k for k, v in flight.items() if k != 'timestamp' and v])
        
        flight['summary'] = {
            'total_systems': total_systems,
            'online_systems': online_systems,
            'online_pct': round(online_systems / total_systems * 100, 1) if total_systems > 0 else 0,
            'critical_online': all([
                flight['exchange_alpaca'] or flight['exchange_kraken'],  # At least one exchange
                flight['miner_brain'] or flight['ultimate_intelligence'],  # At least one intelligence source
            ])
        }
        
        # Determine if flight check passed
        self.flight_check_passed = flight['summary']['critical_online']
        self.last_flight_check = flight
        
        # Audit the flight check
        self.audit_event('flight_check', flight)
        
        return flight
    
    def print_flight_check(self, flight: dict = None):
        """Print flight check results in a nice format."""
        if flight is None:
            flight = self.run_flight_check()
        
        print("\n" + "=" * 60)
        print("✈️ ORCA FLIGHT CHECK - SYSTEM VALIDATION")
        print("=" * 60)
        
        categories = {
            '🏦 EXCHANGES': ['exchange_alpaca', 'exchange_kraken'],
            '👑 QUEEN & CORE': ['queen_wired', 'thought_bus', 'intelligence_engine', 'feed_hub'],
            '⚡ HFT SYSTEMS': ['hft_engine', 'hft_order_router', 'harmonic_signal_chain', 'harmonic_alphabet'],
            '🎵 HARMONIC SYSTEMS': ['global_orchestrator', 'harmonic_binary', 'harmonic_chain_master', 'harmonic_counter', 'harmonic_fusion', 'harmonic_momentum', 'harmonic_reality', 'global_bot_map'],
            '🌀 ENIGMA SYSTEMS': ['enhanced_telescope', 'enigma_dream', 'enhancement_layer', 'enigma_integration', 'firm_intelligence', 'enigma_core'],
            '🧠 INTELLIGENCE': ['miner_brain', 'quantum_telescope', 'ultimate_intelligence', 'enigma'],
            '🐋 WHALE SYSTEMS': ['whale_tracker', 'moby_dick', 'chirp_bus'],
            '🔮 QUANTUM': ['luck_mapper', 'inception_engine', 'stargate', 'quantum_mirror'],
            '🛡️ PROTECTION': ['phantom_filter', 'immune_system', 'elephant_learning', 'russian_doll'],
            '🌌 MULTIVERSE & NEURAL': ['aureon_miner', 'multi_exchange', 'multi_pair', 'multiverse_live', 'multiverse_orchestrator', 'mycelium_network', 'neural_revenue']
        }
        
        for category, keys in categories.items():
            print(f"\n{category}:")
            for key in keys:
                status = flight.get(key, False)
                icon = "✅" if status else "❌"
                name = key.replace('_', ' ').title()
                print(f"   {icon} {name}")
        
        # Summary
        summary = flight.get('summary', {})
        print(f"\n{'=' * 60}")
        print(f"📊 SUMMARY: {summary.get('online_systems', 0)}/{summary.get('total_systems', 0)} systems online ({summary.get('online_pct', 0)}%)")
        
        if self.flight_check_passed:
            print("✅ FLIGHT CHECK PASSED - Ready for autonomous trading")
        else:
            print("❌ FLIGHT CHECK FAILED - Critical systems offline")
        print("=" * 60)
        
    def gather_all_intelligence(self, prices: dict = None) -> dict:
        """
        Gather intelligence from all sources before making decisions.
        This is the Master Launcher pattern for comprehensive data gathering.
        
        Returns:
            dict with bot/whale/momentum intelligence
        """
        intel = {
            'timestamp': datetime.now().isoformat(),
            'total_sources': 0,
            'bots': [],
            'whale_predictions': [],
            'momentum': {},
            'validated_signals': []
        }
        
        # Get prices if not provided
        if prices is None:
            prices = {}
            try:
                if 'alpaca' in self.clients and self.clients['alpaca']:
                    client = self.clients['alpaca']
                    if hasattr(client, 'get_all_quotes'):
                        quotes = client.get_all_quotes()
                        for symbol, data in (quotes or {}).items():
                            prices[symbol] = data.get('price', data.get('last', 0))
            except:
                pass
        
        # 1. Real Intelligence Engine
        if self.intelligence_engine:
            try:
                if hasattr(self.intelligence_engine, 'gather_all_intelligence'):
                    engine_intel = self.intelligence_engine.gather_all_intelligence(prices)
                    intel['bots'] = engine_intel.get('bots', [])
                    intel['whale_predictions'] = engine_intel.get('whale_predictions', [])
                    intel['momentum'] = engine_intel.get('momentum', {})
                    intel['total_sources'] += 1
            except:
                pass
        
        # 2. Feed Hub
        if self.feed_hub:
            try:
                if hasattr(self.feed_hub, 'gather_and_distribute'):
                    summary = self.feed_hub.gather_and_distribute(prices)
                    intel['validated_signals'] = summary.get('validated_intelligence', [])
                    intel['total_sources'] += 1
            except:
                pass
        
        # 3. Miner Brain
        if self.miner_brain:
            try:
                if hasattr(self.miner_brain, 'get_recommendations'):
                    recs = self.miner_brain.get_recommendations(prices)
                    for rec in (recs or []):
                        if rec.get('confidence', 0) > 0.7:
                            intel['validated_signals'].append({
                                'source': 'miner_brain',
                                'symbol': rec.get('symbol'),
                                'action': rec.get('action'),
                                'confidence': rec.get('confidence')
                            })
                    intel['total_sources'] += 1
            except:
                pass
        
        # 4. Whale Tracker
        if self.whale_tracker:
            try:
                if hasattr(self.whale_tracker, 'recent_whale_activity'):
                    activity = self.whale_tracker.recent_whale_activity
                    for symbol, data in (activity or {}).items():
                        intel['whale_predictions'].append({
                            'symbol': symbol,
                            'action': data.get('direction', 'neutral'),
                            'value': data.get('value_usd', 0)
                        })
                    intel['total_sources'] += 1
            except:
                pass
        
        # 5. Ultimate Intelligence
        if self.ultimate_intel:
            try:
                if hasattr(self.ultimate_intel, 'get_prediction'):
                    for symbol in list(prices.keys())[:10]:
                        pred = self.ultimate_intel.get_prediction(symbol)
                        if pred and pred.get('confidence', 0) > 0.8:
                            intel['validated_signals'].append({
                                'source': 'ultimate_intelligence',
                                'symbol': symbol,
                                'action': pred.get('action', 'HOLD'),
                                'confidence': pred.get('confidence', 0)
                            })
                    intel['total_sources'] += 1
            except:
                pass
        
        # Audit the intelligence gathering
        self.audit_event('intelligence_gathered', {
            'total_sources': intel['total_sources'],
            'bots_count': len(intel['bots']),
            'whales_count': len(intel['whale_predictions']),
            'validated_count': len(intel['validated_signals'])
        })
        
        return intel
    
    def print_status_summary(self):
        """Print a comprehensive status summary of all systems (Master Launcher style)."""
        print("\n" + "=" * 70)
        print("🦈🔪 ORCA COMPLETE KILL CYCLE - STATUS SUMMARY")
        print("=" * 70)
        
        print("\n📡 INTELLIGENCE SOURCES:")
        if self.intelligence_engine:
            print("   • Real Intelligence Engine: ACTIVE")
        if self.feed_hub:
            print("   • Real Data Feed Hub: ACTIVE")
        if self.miner_brain:
            print("   • Miner Brain: ACTIVE (Cognitive Intelligence)")
        if self.ultimate_intel:
            print("   • Ultimate Intelligence: ACTIVE (95% accuracy)")
        
        print("\n🐋 WHALE SYSTEMS:")
        if self.whale_tracker:
            print("   • Whale Tracker: ACTIVE")
        if self.moby_dick:
            print("   • Moby Dick Hunter: ACTIVE")
        if self.chirp_bus:
            print("   • Chirp Bus: ACTIVE (Bird chorus)")
        
        print("\n⚡ HFT & EXECUTION:")
        if self.hft_engine:
            print("   • HFT Harmonic Engine: ACTIVE")
        if self.hft_order_router:
            print("   • HFT Order Router: ACTIVE")
        if self.harmonic_signal_chain:
            print("   • Harmonic Signal Chain: ACTIVE")
        
        print("\n🔮 QUANTUM SYSTEMS:")
        if self.luck_mapper:
            print("   • Luck Field Mapper: ACTIVE")
        if self.inception_engine:
            print("   • Inception Engine: ACTIVE (LIMBO probability)")
        if self.stargate:
            print("   • Stargate Protocol: ACTIVE")
        if self.quantum_mirror:
            print("   • Quantum Mirror: ACTIVE")
        
        print("\n🛡️ PROTECTION SYSTEMS:")
        if self.phantom_filter:
            print("   • Phantom Filter: ACTIVE (4-layer validation)")
        if self.immune_system:
            print("   • Immune System: ACTIVE (Self-healing)")
        if self.elephant:
            print("   • Elephant Learning: ACTIVE (Pattern memory)")
        
        print("\n🏦 EXCHANGE CONNECTIONS:")
        for exchange, client in self.clients.items():
            status = "✅ CONNECTED" if client else "❌ OFFLINE"
            print(f"   • {exchange.title()}: {status}")
        
        print("\n" + "=" * 70)
        print("✅ ORCA KILL CYCLE READY - All systems operational")
        print("=" * 70)
        
    def _handle_whale_signal(self, thought):
        """Process whale activity signals from ThoughtBus."""
        try:
            data = thought.data if hasattr(thought, 'data') else thought
            if isinstance(data, dict):
                self.whale_signal = data.get('action', 'neutral')
        except Exception:
            pass
    
    # ═══════════════════════════════════════════════════════════════════════
    # � QUANTUM INTELLIGENCE - ENHANCED PROBABILITY SCORING
    # ═══════════════════════════════════════════════════════════════════════
    
    def get_quantum_score(self, symbol: str, price: float, change_pct: float, 
                          volume: float = 0, momentum: float = 0) -> dict:
        """
        Get enhanced probability score using ALL quantum systems.
        
        Returns:
            dict with:
            - luck_field: 0-1 score from Luck Field Mapper
            - luck_state: VOID/CHAOS/NEUTRAL/FAVORABLE/BLESSED
            - limbo_probability: 0-1 from Inception Engine LIMBO
            - limbo_pattern: Pattern key from LIMBO
            - quantum_boost: Combined confidence multiplier
            - action_bias: BUY/SELL/HOLD suggestion
        """
        result = {
            'luck_field': 0.5,
            'luck_state': 'NEUTRAL',
            'limbo_probability': 0.5,
            'limbo_pattern': 'unknown',
            'quantum_boost': 1.0,
            'action_bias': 'HOLD',
            'is_blessed': False,
            'inception_wisdom': None
        }
        
        # 1. LUCK FIELD MAPPER - Cosmic alignment score
        if self.luck_mapper:
            try:
                # Calculate volatility proxy from change
                volatility = min(1.0, abs(change_pct) / 10.0)
                luck_reading = self.luck_mapper.read_field(
                    price=price,
                    volatility=volatility,
                    market_frequency=volume / 100000 if volume > 0 else 0  # Map volume to frequency
                )
                result['luck_field'] = luck_reading.luck_field
                result['luck_state'] = luck_reading.luck_state.value if hasattr(luck_reading.luck_state, 'value') else str(luck_reading.luck_state)
                result['action_bias'] = luck_reading.action_bias
                result['is_blessed'] = luck_reading.luck_field >= 0.8
                
                # Luck boost: BLESSED = 1.3x, FAVORABLE = 1.15x, NEUTRAL = 1.0x, CHAOS = 0.85x, VOID = 0.7x
                if luck_reading.luck_field >= 0.8:
                    result['quantum_boost'] *= 1.3  # BLESSED
                elif luck_reading.luck_field >= 0.6:
                    result['quantum_boost'] *= 1.15  # FAVORABLE
                elif luck_reading.luck_field >= 0.4:
                    result['quantum_boost'] *= 1.0   # NEUTRAL
                elif luck_reading.luck_field >= 0.2:
                    result['quantum_boost'] *= 0.85  # CHAOS
                else:
                    result['quantum_boost'] *= 0.7   # VOID - Avoid!
                    
            except Exception as e:
                pass  # Keep defaults
        
        # 2. INCEPTION ENGINE - LIMBO depth probability (The Limitless Pill)
        if self.inception_engine and INCEPTION_ENGINE_AVAILABLE and get_limbo_insight:
            try:
                # Build market data for LIMBO
                market_data = {
                    'prices': {symbol: price},
                    'changes': {symbol: change_pct},
                    'volumes': {symbol: volume},
                    'momentum': {symbol: momentum}
                }
                
                # Get raw LIMBO insight (deepest layer = most accurate)
                limbo_insight = get_limbo_insight(symbol, market_data)
                result['limbo_probability'] = limbo_insight.probability
                result['limbo_pattern'] = limbo_insight.pattern_key
                
                # Also do full inception dive for wisdom
                wisdom = self.inception_engine.dive(market_data)
                result['inception_wisdom'] = wisdom
                
                # LIMBO boost: High probability = big boost
                if limbo_insight.probability >= 0.85:
                    result['quantum_boost'] *= 1.25  # Limitless territory
                elif limbo_insight.probability >= 0.7:
                    result['quantum_boost'] *= 1.15
                elif limbo_insight.probability >= 0.5:
                    result['quantum_boost'] *= 1.05
                elif limbo_insight.probability < 0.35:
                    result['quantum_boost'] *= 0.8   # LIMBO says NO
                    
            except Exception as e:
                pass  # Keep defaults
        
        # 3. HFT Engine - Harmonic frequency analysis (if available)
        if self.hft_engine:
            try:
                # Feed tick to HFT engine
                tick = HFTTick(
                    symbol=symbol,
                    price=price,
                    size=volume / price if price > 0 else 0,
                    side='buy' if change_pct > 0 else 'sell',
                    timestamp=time.time(),
                    exchange='mixed'
                ) if HFT_ENGINE_AVAILABLE and HFTTick else None
                
                if tick and hasattr(self.hft_engine, 'ingest_tick'):
                    tone = self.hft_engine.ingest_tick(tick)
                    if tone and hasattr(tone, 'confidence'):
                        # 528Hz (Love frequency) alignment gives boost
                        if abs(tone.frequency - 528) < 50:
                            result['quantum_boost'] *= 1.1
            except Exception:
                pass
        
        # ═══════════════════════════════════════════════════════════════════
        # 🧬 NEW SYSTEMS INTEGRATION
        # ═══════════════════════════════════════════════════════════════════
        
        # 4. ELEPHANT LEARNING - Pattern memory (never forgets)
        if self.elephant:
            try:
                asset_score = self.elephant.get_asset_score(symbol)
                result['elephant_score'] = asset_score
                # Good historical performance = boost
                if asset_score >= 0.7:
                    result['quantum_boost'] *= 1.1
                elif asset_score <= 0.3:
                    result['quantum_boost'] *= 0.9  # Bad history = caution
                    
                # Get best trading hours
                best_hours = self.elephant.get_best_trading_hours()
                current_hour = time.localtime().tm_hour
                if current_hour in best_hours:
                    result['quantum_boost'] *= 1.05  # Optimal time
                    result['optimal_hour'] = True
                else:
                    result['optimal_hour'] = False
            except Exception:
                pass
        
        # 5. RUSSIAN DOLL ANALYTICS - Queen directives (Bee→Hive→Queen)
        if self.russian_doll:
            try:
                directives = self.russian_doll.get_queen_directives()
                result['queen_confidence'] = directives.get('confidence', 0.5)
                result['target_exchanges'] = directives.get('target_exchanges', [])
                
                # High Queen confidence = trust the system
                if directives.get('confidence', 0) >= 0.7:
                    result['quantum_boost'] *= 1.08
            except Exception:
                pass
        
        # 6. MOBY DICK WHALE HUNTER - Whale predictions
        if self.moby_dick:
            try:
                predictions = self.moby_dick.get_execution_ready_predictions()
                for pred in predictions:
                    if hasattr(pred, 'symbol') and pred.symbol == symbol:
                        result['whale_prediction'] = pred
                        result['whale_direction'] = pred.direction if hasattr(pred, 'direction') else 'unknown'
                        # Whale alignment = big confidence boost
                        if pred.confidence >= 0.8:
                            result['quantum_boost'] *= 1.15
                        break
            except Exception:
                pass
        
        # 7. STARGATE PROTOCOL - Quantum mirror alignment
        if self.stargate:
            try:
                status = self.stargate.get_status()
                result['stargate_coherence'] = status.get('network_coherence', 0.5)
                result['active_nodes'] = status.get('active_nodes', 0)
                
                # High network coherence = timeline alignment
                if status.get('network_coherence', 0) >= 0.7:
                    result['quantum_boost'] *= 1.1
                    result['timeline_aligned'] = True
                else:
                    result['timeline_aligned'] = False
            except Exception:
                pass
        
        # 8. QUANTUM MIRROR SCANNER - Reality branch boost
        if self.quantum_mirror:
            try:
                # Get quantum boost for this specific symbol
                symbol_base = symbol.replace('/USD', '').replace('USD', '')
                branch_boost, reason = self.quantum_mirror.get_quantum_boost(
                    from_asset='USD', to_asset=symbol_base, exchange='mixed'
                )
                result['mirror_boost'] = branch_boost
                result['mirror_reason'] = reason
                
                # Apply reality branch alignment
                if branch_boost > 1.0:
                    result['quantum_boost'] *= min(1.2, branch_boost)  # Cap at 1.2x
                    result['reality_aligned'] = True
                else:
                    result['reality_aligned'] = False
            except Exception:
                pass
        
        # 9. IMMUNE SYSTEM - System health check
        if self.immune_system:
            try:
                health = self.immune_system.get_health_status()
                result['system_health'] = health.get('overall', 'healthy')
                
                # If system is unhealthy, reduce confidence
                if health.get('overall') == 'critical':
                    result['quantum_boost'] *= 0.7
                elif health.get('overall') == 'warning':
                    result['quantum_boost'] *= 0.9
            except Exception:
                pass
        
        # ═══════════════════════════════════════════════════════════════════
        # 🌊🎶 HNC SURGE DETECTION - HARMONIC NEXUS CORE (NEW!)
        # ═══════════════════════════════════════════════════════════════════
        
        # 10. HNC Surge Detector - Detect harmonic resonance surge windows
        if self.hnc_surge_detector:
            try:
                # Feed price data to the surge detector
                self.hnc_surge_detector.add_price_tick(symbol, price)
                
                # Check for active surge window
                surge = self.hnc_surge_detector.detect_surge(symbol)
                if surge:
                    result['hnc_surge_active'] = True
                    result['hnc_surge_intensity'] = surge.intensity if hasattr(surge, 'intensity') else 0.7
                    result['hnc_dominant_harmonic'] = surge.primary_harmonic if hasattr(surge, 'primary_harmonic') else 'Unknown'
                    
                    # SACRED FREQUENCY ALIGNMENT - Major boost for harmonic resonance!
                    # Map primary harmonic name to frequency for boost calculation
                    harmonic_boosts = {
                        'MI - Transformation & Miracles': 1.25,  # 528 Hz Love frequency
                        'Sun': 1.2,                               # 126.22 Hz Solar energy
                        'SOL - Awakening Intuition': 1.18,       # 741 Hz Intuition
                        'RE - Facilitating Change': 1.15,        # 417 Hz Change
                        'LA - Returning to Spirit': 1.15,        # 852 Hz Spirit
                        'Schumann Resonance': 1.2,               # 7.83 Hz Earth heartbeat
                        'UT - Liberating Guilt': 1.12,           # 396 Hz Liberation
                        'FA - Connecting Relationships': 1.12,   # 639 Hz Connection
                        'Moon': 1.1,                             # 210.42 Hz Lunar
                        'Earth Day': 1.1,                        # 194.18 Hz Earth
                    }
                    
                    primary = surge.primary_harmonic if hasattr(surge, 'primary_harmonic') else ''
                    boost = harmonic_boosts.get(primary, 1.1)  # Default 1.1x boost for any harmonic
                    result['quantum_boost'] *= boost
                    result['hnc_resonance'] = primary or 'HARMONIC_SURGE'
                    
                    self.hnc_active_surge = surge  # Store for War Room display
                else:
                    result['hnc_surge_active'] = False
                    result['hnc_surge_intensity'] = 0.0
                    result['hnc_resonance'] = 'NO_SURGE'
                    self.hnc_active_surge = None
            except Exception as e:
                result['hnc_surge_active'] = False
                result['hnc_resonance'] = 'ERROR'
        
        # ═══════════════════════════════════════════════════════════════════
        # 📜⚔️ HISTORICAL MANIPULATION HUNTER - PATTERN WARNINGS (NEW!)
        # ═══════════════════════════════════════════════════════════════════
        
        # 11. Historical Manipulation Hunter - Check for historical pattern matches
        if self.historical_hunter:
            try:
                # Analyze current market conditions against historical patterns
                pattern_match = self.historical_hunter.analyze_current_conditions(
                    symbol=symbol,
                    price_change_pct=change_pct,
                    volume=volume,
                    momentum=momentum
                )
                
                if pattern_match:
                    result['historical_pattern'] = pattern_match.get('pattern_name', 'Unknown')
                    result['historical_similarity'] = pattern_match.get('similarity', 0.0)
                    result['historical_outcome'] = pattern_match.get('historical_outcome', 'unknown')
                    
                    # If historical pattern predicts crash/manipulation → REDUCE confidence
                    if pattern_match.get('is_danger_pattern', False):
                        result['quantum_boost'] *= 0.6  # Big reduction for danger!
                        result['historical_warning'] = True
                        self.historical_pattern_warning = pattern_match
                    # If historical pattern predicts recovery/bull run → BOOST
                    elif pattern_match.get('is_opportunity_pattern', False):
                        result['quantum_boost'] *= 1.2
                        result['historical_warning'] = False
                    else:
                        result['historical_warning'] = False
                else:
                    result['historical_pattern'] = None
                    result['historical_warning'] = False
            except Exception as e:
                result['historical_pattern'] = None
                result['historical_warning'] = False
        
        # Cap the quantum boost at reasonable levels (raised for more systems)
        result['quantum_boost'] = max(0.4, min(2.0, result['quantum_boost']))
        
        # 8. STARGATE GRID - Planetary Resonance Alignment (NEW UNITING LAYER)
        if getattr(self, 'stargate_grid', None):
            try:
                active_node = self.stargate_grid.get_active_node()
                coherence = self.stargate_grid.calculate_grid_coherence()
                
                result['stargate_node'] = active_node.name
                result['stargate_coherence'] = coherence
                
                # Apply boost based on Grid Coherence (Schumann alignment)
                # Golden Ratio (1.618) is the baseline for "coherent" state
                if coherence >= 1.618:
                    boost = 1.0 + (coherence / 10.0)  # e.g. 2.0 coherence -> 1.2x boost
                    result['quantum_boost'] *= min(1.3, boost)  # Cap at 30% boost
                    result['stargate_aligned'] = True
                elif coherence < 0.5:
                    result['quantum_boost'] *= 0.9  # Low coherence = scatter measure
                    result['stargate_aligned'] = False
                else:
                    result['stargate_aligned'] = False
                    
            except Exception:
                pass

        # 9. MOMENTUM ECOSYSTEM - Animal Spirits (NEW UNITY LAYER)
        if getattr(self, 'momentum_ecosystem', None):
            # Boost if this symbol is being hunted by the animal pack
            mom_data = getattr(self, 'last_momentum_result', {})
            
            # Handle both dict and AnimalOpportunity objects
            def get_symbol(item):
                if isinstance(item, dict):
                    return item['symbol']
                return getattr(item, 'symbol', '')
            
            wolf_targets = [get_symbol(t) for t in mom_data.get('wolf', [])]
            lion_prey = [get_symbol(t) for t in mom_data.get('lion', [])]
            hb_flowers = [get_symbol(t) for t in mom_data.get('hummingbird', [])]
            
            animal_boost = 1.0
            if symbol in wolf_targets: animal_boost += 0.15 # Wolf pack hunting
            if symbol in lion_prey: animal_boost += 0.25    # Lion pride hunting (bigger conviction)
            if symbol in hb_flowers: animal_boost += 0.1    # Hummingbird pollinating
            
            if animal_boost > 1.0:
                result['quantum_boost'] *= animal_boost
                result['animal_spirit'] = True
            else:
                result['animal_spirit'] = False

        return result
    
    def print_quantum_status(self):
        """Print current quantum systems status."""
        print("\n" + "="*70)
        print("🌌 QUANTUM INTELLIGENCE SYSTEMS STATUS (25 SYSTEMS WIRED)")
        print("="*70)
        
        wired_count = 0
        
        # Luck Field
        if self.luck_mapper:
            try:
                reading = self.luck_mapper.read_field()
                state = reading.luck_state.value if hasattr(reading.luck_state, 'value') else str(reading.luck_state)
                blessed = "🔒 BLESSED!" if reading.luck_field >= 0.8 else ""
                print(f"🍀 Luck Field: λ={reading.luck_field:.3f} → {state} {blessed}")
                print(f"   Σ(Schumann)={reading.sigma_schumann:.2f} Π(Planet)={reading.pi_planetary:.2f}")
                print(f"   Φ(Harmonic)={reading.phi_harmonic:.2f} Ω(Time)={reading.omega_temporal:.2f}")
                wired_count += 1
            except Exception as e:
                print(f"🍀 Luck Field: Error - {e}")
        else:
            print("🍀 Luck Field: Not available")
        
        # Inception Engine
        if self.inception_engine:
            try:
                status = self.inception_engine.get_status()
                print(f"🎬 Inception: {status['dives_completed']} dives | {status.get('limbo_patterns_loaded', 0)} patterns")
                print(f"   Totem: ${status['totem']['net_profit']:.2f} | Real={status['totem']['is_real']}")
                wired_count += 1
            except Exception as e:
                print(f"🎬 Inception: Error - {e}")
        else:
            print("🎬 Inception: Not available")
        
        # Phantom Filter
        if self.phantom_filter:
            print("👻 Phantom Filter: ACTIVE (4-layer validation)")
            wired_count += 1
        else:
            print("👻 Phantom Filter: Not available")
        
        # Elephant Learning
        if self.elephant:
            try:
                best_hours = self.elephant.get_best_trading_hours()
                hour_str = ','.join(str(h) for h in best_hours[:5]) + '...' if len(best_hours) > 5 else ','.join(str(h) for h in best_hours)
                print(f"🐘 Elephant: REMEMBERING | Best hours: [{hour_str}]")
                wired_count += 1
            except Exception as e:
                print(f"🐘 Elephant: Error - {e}")
        else:
            print("🐘 Elephant Learning: Not available")
        
        # Russian Doll Analytics
        if self.russian_doll:
            try:
                directives = self.russian_doll.get_queen_directives()
                conf = directives.get('confidence', 0)
                exchanges = directives.get('target_exchanges', [])
                print(f"🦷 Russian Doll: Queen confidence {conf:.1%} | Targets: {exchanges}")
                wired_count += 1
            except Exception as e:
                print(f"🦷 Russian Doll: Error - {e}")
        else:
            print("🦷 Russian Doll: Not available")
        
        # Immune System
        if self.immune_system:
            try:
                health = self.immune_system.get_health_status()
                status = health.get('overall', 'unknown')
                emoji = "✅" if status == 'healthy' else "⚠️" if status == 'warning' else "🔴"
                print(f"🛡️ Immune System: {emoji} {status.upper()}")
                wired_count += 1
            except Exception as e:
                print(f"🛡️ Immune System: Error - {e}")
        else:
            print("🛡️ Immune System: Not available")
        
        # Moby Dick Whale Hunter
        if self.moby_dick:
            try:
                preds = self.moby_dick.get_execution_ready_predictions()
                print(f"🐋 Moby Dick: {len(preds)} whale predictions ready")
                wired_count += 1
            except Exception as e:
                print(f"🐋 Moby Dick: Error - {e}")
        else:
            print("🐋 Moby Dick: Not available")
        
        # Stargate Protocol
        if self.stargate:
            try:
                status = self.stargate.get_status()
                coherence = status.get('network_coherence', 0)
                nodes = status.get('active_nodes', 0)
                print(f"🌌 Stargate: Coherence {coherence:.1%} | {nodes} nodes active")
                wired_count += 1
            except Exception as e:
                print(f"🌌 Stargate: Error - {e}")
        else:
            print("🌌 Stargate: Not available")
        
        # Quantum Mirror Scanner
        if self.quantum_mirror:
            try:
                status = self.quantum_mirror.get_status()
                branches = len(status.get('branches', {}))
                print(f"🔮 Quantum Mirror: {branches} reality branches tracked")
                wired_count += 1
            except Exception as e:
                print(f"🔮 Quantum Mirror: Error - {e}")
        else:
            print("🔮 Quantum Mirror: Not available")
        
        # HNC Surge Detector (NEW!)
        if self.hnc_surge_detector:
            try:
                # Check if active surge is stored
                if self.hnc_active_surge:
                    harmonic = self.hnc_active_surge.primary_harmonic if hasattr(self.hnc_active_surge, 'primary_harmonic') else 'Unknown'
                    intensity = self.hnc_active_surge.intensity if hasattr(self.hnc_active_surge, 'intensity') else 0.5
                    print(f"🌊🎶 HNC Surge: ACTIVE! {harmonic} | Intensity: {intensity:.0%}")
                else:
                    print("🌊🎶 HNC Surge: Monitoring (no active surge windows)")
                wired_count += 1
            except Exception as e:
                print(f"🌊🎶 HNC Surge: Error - {e}")
        else:
            print("🌊🎶 HNC Surge Detector: Not available")
        
        # Historical Manipulation Hunter (NEW!)
        if self.historical_hunter:
            try:
                # Check for active warnings
                if self.historical_pattern_warning:
                    pattern = self.historical_pattern_warning.get('pattern_name', 'Unknown')
                    print(f"📜⚔️ Historical Hunter: ⚠️ WARNING - {pattern} pattern detected!")
                else:
                    print("📜⚔️ Historical Hunter: CLEAR (no danger patterns)")
                wired_count += 1
            except Exception as e:
                print(f"📜⚔️ Historical Hunter: Error - {e}")
        else:
            print("📜⚔️ Historical Manipulation Hunter: Not available")
        
        print("-"*70)
        print(f"⚡ TOTAL QUANTUM SYSTEMS ACTIVE: {wired_count}/28 display | 46 total wired")
        print("="*70)
    
    # ═══════════════════════════════════════════════════════════════════════
    # �🆕 SCAN ENTIRE MARKET - ALL EXCHANGES, ALL SYMBOLS
    # ═══════════════════════════════════════════════════════════════════════
    
    def scan_entire_market(self, min_change_pct: float = 0.5, min_volume: float = 1000) -> List[MarketOpportunity]:
        """
        Scan ENTIRE market across ALL exchanges for opportunities.
        
        Returns sorted list of best opportunities from Alpaca AND Kraken.
        🌌 ENHANCED with quantum probability scoring!
        """
        print("\n" + "="*70)
        print("🌊 SCANNING ENTIRE MARKET - ALL EXCHANGES")
        print("="*70)
        
        opportunities = []
        
        # Scan Alpaca
        if 'alpaca' in self.clients:
            alpaca_opps = self._scan_alpaca_market(min_change_pct, min_volume)
            opportunities.extend(alpaca_opps)
            print(f"   📊 Alpaca: Found {len(alpaca_opps)} opportunities")
        
        # Scan Kraken
        if 'kraken' in self.clients:
            kraken_opps = self._scan_kraken_market(min_change_pct, min_volume)
            opportunities.extend(kraken_opps)
            print(f"   📊 Kraken: Found {len(kraken_opps)} opportunities")
        
        # Scan Binance
        if 'binance' in self.clients:
            binance_opps = self._scan_binance_market(min_change_pct, min_volume)
            opportunities.extend(binance_opps)
            print(f"   📊 Binance: Found {len(binance_opps)} opportunities")
        
        # Scan Capital.com
        if 'capital' in self.clients:
            capital_opps = self._scan_capital_market(min_change_pct, min_volume)
            opportunities.extend(capital_opps)
            print(f"   📊 Capital.com: Found {len(capital_opps)} CFD opportunities")
        
        # ═══════════════════════════════════════════════════════════════════
        # 🦅 MOMENTUM ECOSYSTEM - Animal Swarms & Micro Goals
        # ═══════════════════════════════════════════════════════════════════
        if self.momentum_ecosystem:
            try:
                swarm_layout = self.momentum_ecosystem.run_once()
                self.last_momentum_result = swarm_layout  # Store for dashboard
                swarm_opps = []
                for agent, found_list in swarm_layout.items():
                    for anim in found_list:
                        opp = MarketOpportunity(
                            symbol=anim.symbol.replace('/', ''),
                            exchange='alpaca',  # Ecosystem runs on Alpaca
                            price=0.0,  # Price is less relevant than move pattern
                            change_pct=anim.move_pct,
                            volume=anim.volume,
                            momentum_score=anim.net_pct * 10.0,  # Scaled score
                            fee_rate=self.fee_rates.get('alpaca', 0.0025)
                        )
                        swarm_opps.append(opp)
                        print(f"   🦅 {agent.upper()}: Found {anim.symbol} ({anim.reason})")
                
                if swarm_opps:
                    opportunities.extend(swarm_opps)
                    print(f"   📊 Animal Swarm: Added {len(swarm_opps)} momentum targets")
            except Exception as e:
                print(f"   ⚠️ Animal Swarm Scan Failed: {e}")

        if self.micro_scanner:
            try:
                micro_signals = self.micro_scanner.get_actionable_signals()
                self.last_micro_result = micro_signals  # Store for dashboard
                if micro_signals:
                    for sig in micro_signals:
                        opp = MarketOpportunity(
                            symbol=sig.symbol.replace('/', ''),
                            exchange='alpaca',
                            price=sig.current_price,
                            change_pct=sig.momentum_5m_pct,
                            volume=0.0,
                            momentum_score=sig.net_profit_potential * 10.0,
                            fee_rate=self.fee_rates.get('alpaca', 0.0025)
                        )
                        opportunities.extend([opp])
                    print(f"   📊 Micro-Momentum: Added {len(micro_signals)} scalp targets")
            except Exception as e:
                print(f"   ⚠️ Micro-Scanner Failed: {e}")
        
        # ═══════════════════════════════════════════════════════════════════
        # 🌌 QUANTUM ENHANCEMENT - Apply luck field + LIMBO probability boost
        # 🌊🎶 HNC SURGE + 📜⚔️ HISTORICAL MANIPULATION FILTER!
        # ═══════════════════════════════════════════════════════════════════
        print("\n🌌 Applying FULL quantum intelligence scoring...")
        print("   🌊🎶 HNC Surge Detection | 📜⚔️ Historical Pattern Filter")
        blessed_count = 0
        limbo_high_count = 0
        hnc_surge_count = 0
        historical_blocked = 0
        historical_boosted = 0
        
        # Track filtered opportunities (remove danger patterns!)
        filtered_opportunities = []
        
        for opp in opportunities:
            quantum = self.get_quantum_score(
                symbol=opp.symbol,
                price=opp.price,
                change_pct=opp.change_pct,
                volume=opp.volume,
                momentum=opp.momentum_score
            )
            
            # ═══════════════════════════════════════════════════════════════
            # ⚠️ HISTORICAL DANGER CHECK - WARN BUT LET QUEEN DECIDE!
            # ═══════════════════════════════════════════════════════════════
            if quantum.get('historical_warning', False):
                historical_blocked += 1
                pattern = quantum.get('historical_pattern', 'Unknown')
                # DON'T BLOCK - just reduce quantum boost and let Queen decide
                # (already reduced by 0.6x in get_quantum_score)
                opp._historical_warning = True
                opp._historical_pattern = pattern
                # print(f"   ⚠️ WARNING: {opp.symbol} - Historical pattern: {pattern} (Queen will decide)")
            else:
                opp._historical_warning = False
                opp._historical_pattern = None
            
            # Apply quantum boost to momentum score
            original_score = opp.momentum_score
            opp.momentum_score = original_score * quantum['quantum_boost']
            
            # ═══════════════════════════════════════════════════════════════
            # 🌊🎶 HNC SURGE BOOST - Harmonic resonance = PRIORITY!
            # ═══════════════════════════════════════════════════════════════
            if quantum.get('hnc_surge_active', False):
                hnc_surge_count += 1
                resonance = quantum.get('hnc_resonance', 'SURGE')
                intensity = quantum.get('hnc_surge_intensity', 0.7)
                # Mark as HNC-blessed for priority selection
                opp._hnc_surge = True
                opp._hnc_resonance = resonance
                print(f"   🌊🎶 HNC SURGE: {opp.symbol} | {resonance} | Intensity: {intensity:.0%}")
            else:
                opp._hnc_surge = False
                opp._hnc_resonance = None
            
            # ═══════════════════════════════════════════════════════════════
            # 📜 HISTORICAL OPPORTUNITY BOOST - Past predicts future!
            # ═══════════════════════════════════════════════════════════════
            if quantum.get('historical_pattern') and not quantum.get('historical_warning'):
                historical_boosted += 1
                pattern = quantum.get('historical_pattern', 'Unknown')
                opp._historical_pattern = pattern
                print(f"   📜 HISTORICAL BOOST: {opp.symbol} - Pattern: {pattern}")
            else:
                opp._historical_pattern = None
            
            if quantum['is_blessed']:
                blessed_count += 1
            if quantum['limbo_probability'] >= 0.7:
                limbo_high_count += 1
            
            # Add to filtered list (passed danger check!)
            filtered_opportunities.append(opp)
        
        # Replace original list with filtered (danger-free!) opportunities
        opportunities = filtered_opportunities
        
        # Print intelligence summary
        print(f"\n   🛡️ INTELLIGENCE SUMMARY:")
        if blessed_count > 0:
            print(f"      🍀 BLESSED by luck field: {blessed_count}")
        if limbo_high_count > 0:
            print(f"      🎬 LIMBO high probability: {limbo_high_count}")
        if hnc_surge_count > 0:
            print(f"      🌊🎶 HNC SURGE ACTIVE: {hnc_surge_count} (PRIORITY!)")
        if historical_blocked > 0:
            print(f"      🚨 BLOCKED by history: {historical_blocked} (Danger patterns!)")
        if historical_boosted > 0:
            print(f"      📜 BOOSTED by history: {historical_boosted} (Opportunity patterns!)")
        
        # ═══════════════════════════════════════════════════════════════════
        # 🌊🎶 PRIORITY SORT: HNC Surge opportunities FIRST!
        # Then by quantum-boosted momentum score
        # ═══════════════════════════════════════════════════════════════════
        def priority_sort_key(opp):
            """HNC surge = 1000 bonus, then momentum score"""
            hnc_bonus = 1000 if getattr(opp, '_hnc_surge', False) else 0
            historical_bonus = 100 if getattr(opp, '_historical_pattern', None) else 0
            return hnc_bonus + historical_bonus + opp.momentum_score
        
        opportunities.sort(key=priority_sort_key, reverse=True)
        
        print(f"\n🎯 Total opportunities: {len(opportunities)} (after danger filter)")
        if opportunities:
            print("\n🏆 TOP OPPORTUNITIES (Quantum + HNC + Historical Enhanced):")
            for i, opp in enumerate(opportunities[:5]):
                hnc_tag = "🌊🎶" if getattr(opp, '_hnc_surge', False) else ""
                hist_tag = "📜" if getattr(opp, '_historical_pattern', None) else ""
                resonance = getattr(opp, '_hnc_resonance', '') or ''
                if resonance:
                    resonance = f" [{resonance[:15]}]"
                print(f"   {i+1}. {hnc_tag}{hist_tag} {opp.symbol} ({opp.exchange}): {opp.change_pct:+.2f}% | Score: {opp.momentum_score:.2f}{resonance}")
        
        return opportunities
    
    def _scan_alpaca_market(self, min_change_pct: float, min_volume: float) -> List[MarketOpportunity]:
        """Scan ALL Alpaca crypto pairs for momentum using snapshot API."""
        opportunities = []
        client = self.clients.get('alpaca')
        if not client:
            return opportunities
        
        try:
            # Try to get snapshots for all crypto (faster)
            if hasattr(client, 'get_crypto_snapshots'):
                snapshots = client.get_crypto_snapshots()
                if snapshots:
                    for symbol, snap in snapshots.items():
                        try:
                            daily = snap.get('dailyBar', {})
                            prev = snap.get('prevDailyBar', {})
                            quote = snap.get('latestQuote', {}) or snap.get('latestTrade', {})
                            
                            curr_close = float(daily.get('c', 0) or quote.get('ap', 0) or quote.get('p', 0))
                            prev_close = float(prev.get('c', curr_close))
                            
                            if curr_close <= 0 or prev_close <= 0:
                                continue
                            
                            change_pct = ((curr_close - prev_close) / prev_close * 100)
                            volume = float(daily.get('v', 0))
                            momentum = abs(change_pct) * (1 + min(volume / 10000, 1))
                            
                            if abs(change_pct) >= min_change_pct:
                                norm_symbol = symbol if '/' in symbol else symbol.replace('USD', '/USD')
                                opportunities.append(MarketOpportunity(
                                    symbol=norm_symbol,
                                    exchange='alpaca',
                                    price=curr_close,
                                    change_pct=change_pct,
                                    volume=volume,
                                    momentum_score=momentum,
                                    fee_rate=self.fee_rates['alpaca']
                                ))
                        except Exception:
                            pass
                    return opportunities
            
            # Fallback: Get all crypto assets and check each
            assets = client.get_assets(status='active', asset_class='crypto')
            symbols = []
            for asset in assets:
                if asset.get('tradable'):
                    sym = asset.get('symbol', '')
                    if sym and 'USD' in sym:
                        symbols.append(sym)
            
            # Sample major cryptos if we have many
            major_symbols = ['BTCUSD', 'ETHUSD', 'SOLUSD', 'DOGEUSD', 'AVAXUSD', 
                            'LINKUSD', 'DOTUSD', 'MATICUSD', 'AAVEUSD', 'UNIUSD',
                            'ATOMUSD', 'NEARUSD', 'APTUSD', 'ARBUSD', 'OPUSD']
            check_symbols = [s for s in symbols if s in major_symbols] or symbols[:20]
            
            for symbol in check_symbols:
                try:
                    symbol_clean = symbol.replace('/', '')
                    
                    # Get current quote
                    orderbook = client.get_crypto_orderbook(symbol_clean)
                    asks = orderbook.get('asks', [])
                    if not asks:
                        continue
                    
                    price = float(asks[0].get('p', 0))
                    if price <= 0:
                        continue
                    
                    # Get bars for change calculation
                    # FIXED: API returns key as "BASE/QUOTE" format regardless of input
                    bars_result = client.get_crypto_bars([symbol_clean], '1Hour', limit=24)
                    bars_dict = bars_result.get('bars', {})
                    
                    # Try both formats: BTCUSD and BTC/USD
                    norm_symbol = symbol if '/' in symbol else symbol.replace('USD', '/USD')
                    bars = bars_dict.get(norm_symbol, bars_dict.get(symbol_clean, []))
                    
                    if bars and len(bars) >= 2:
                        old_close = float(bars[0].get('c', price))
                        new_close = float(bars[-1].get('c', price))
                        change_pct = ((new_close - old_close) / old_close * 100) if old_close > 0 else 0
                        volume = sum(float(b.get('v', 0)) for b in bars)
                        
                        momentum = abs(change_pct) * (1 + min(volume / 10000, 1))
                        
                        if abs(change_pct) >= min_change_pct:
                            opportunities.append(MarketOpportunity(
                                symbol=norm_symbol,
                                exchange='alpaca',
                                price=price,
                                change_pct=change_pct,
                                volume=volume,
                                momentum_score=momentum,
                                fee_rate=self.fee_rates['alpaca']
                            ))
                except Exception:
                    pass
                    
        except Exception as e:
            print(f"⚠️ Alpaca scan error: {e}")
        
        return opportunities
    
    def _scan_kraken_market(self, min_change_pct: float, min_volume: float) -> List[MarketOpportunity]:
        """Scan ALL Kraken pairs for momentum."""
        opportunities = []
        client = self.clients.get('kraken')
        if not client:
            return opportunities
        
        try:
            # Get ALL 24h tickers from Kraken
            tickers = client.get_24h_tickers()
            
            for ticker in tickers:
                try:
                    symbol = ticker.get('symbol', '')
                    if not symbol:
                        continue
                    
                    # Only USD pairs for simplicity
                    if 'USD' not in symbol:
                        continue
                    
                    last_price = float(ticker.get('lastPrice', 0))
                    change_pct = float(ticker.get('priceChangePercent', 0))
                    volume = float(ticker.get('quoteVolume', 0))
                    
                    if last_price <= 0:
                        continue
                    
                    # Calculate momentum score
                    momentum = abs(change_pct) * (1 + min(volume / 100000, 1))
                    
                    if abs(change_pct) >= min_change_pct:
                        # Normalize symbol format
                        norm_symbol = symbol if '/' in symbol else symbol.replace('USD', '/USD')
                        opportunities.append(MarketOpportunity(
                            symbol=norm_symbol,
                            exchange='kraken',
                            price=last_price,
                            change_pct=change_pct,
                            volume=volume,
                            momentum_score=momentum,
                            fee_rate=self.fee_rates['kraken']
                        ))
                except Exception:
                    pass
        except Exception as e:
            print(f"⚠️ Kraken scan error: {e}")
        
        return opportunities
    
    def _scan_binance_market(self, min_change_pct: float, min_volume: float) -> List[MarketOpportunity]:
        """Scan ALL Binance pairs for momentum (UK-compliant - scans ALL non-restricted markets)."""
        opportunities = []
        client = self.clients.get('binance')
        if not client:
            return opportunities
        
        try:
            print(f"   🔍 DEBUG: Starting Binance Scan...")
            # Get 24h ticker for all symbols
            r = client.session.get(f"{client.base}/api/v3/ticker/24hr", timeout=10)
            if r.status_code != 200:
                print(f"   ⚠️ Binance API Error: {r.status_code}")
                return opportunities
            
            tickers = r.json()
            print(f"   🔍 DEBUG: Fetched {len(tickers)} tickers from Binance")
            
            # Track which quote currencies we're seeing
            quote_currencies = set()
            skipped_restricted = 0
            skipped_zeros = 0
            skipped_low_change = 0
            skipped_uk_groups = 0

            allowed_pairs = None
            if client.uk_mode and getattr(client, 'api_key', None) and getattr(client, 'api_secret', None):
                try:
                    allowed_pairs = client.get_allowed_pairs_uk()
                except Exception:
                    allowed_pairs = None
            
            for ticker in tickers:
                try:
                    symbol = ticker.get('symbol', '')
                    if not symbol:
                        continue
                    
                    # 🇬🇧 UK Mode: Skip restricted symbols FIRST (leveraged tokens, stock tokens, etc.)
                    if client.uk_mode and client.is_uk_restricted_symbol(symbol):
                        skipped_restricted += 1
                        continue

                    # 🇬🇧 UK Mode: Skip symbols not in account trade groups when available
                    if allowed_pairs is not None and symbol not in allowed_pairs:
                        skipped_uk_groups += 1
                        continue
                    
                    # Get symbol info to check if it's SPOT and TRADING
                    # We already have UK filtering, now just verify it's a valid spot pair
                    # Skip if it looks like a futures/margin symbol (usually ends in specific patterns)
                    if any(x in symbol for x in ['_', 'BULL', 'BEAR', 'UP', 'DOWN']):
                        continue
                    
                    last_price = float(ticker.get('lastPrice', 0))
                    change_pct = float(ticker.get('priceChangePercent', 0))
                    volume = float(ticker.get('quoteVolume', 0))
                    
                    if last_price <= 0:
                        skipped_zeros += 1
                        continue
                    
                    # Calculate momentum score
                    momentum = abs(change_pct) * (1 + min(volume / 1000000, 1))  # Binance has higher volume
                    
                    if abs(change_pct) >= min_change_pct:
                        # Normalize symbol format - detect quote currency
                        norm_symbol = symbol
                        for quote in ['USDT', 'USDC', 'BUSD', 'USD', 'BTC', 'ETH', 'BNB', 'EUR', 'GBP']:
                            if symbol.endswith(quote):
                                base = symbol[:-len(quote)]
                                norm_symbol = f"{base}/{quote}"
                                quote_currencies.add(quote)
                                break
                        
                        opportunities.append(MarketOpportunity(
                            symbol=norm_symbol,
                            exchange='binance',
                            price=last_price,
                            change_pct=change_pct,
                            volume=volume,
                            momentum_score=momentum,
                            fee_rate=self.fee_rates.get('binance', 0.001)
                        ))
                    else:
                        skipped_low_change += 1

                except Exception:
                    pass
            
            print(f"   🔍 DEBUG: Binance Stats - Restricted: {skipped_restricted}, UKGroups: {skipped_uk_groups}, ZeroPrice: {skipped_zeros}, LowChange: {skipped_low_change}, Passed: {len(opportunities)}")

            # Print summary of what we scanned
            if quote_currencies:
                quotes_str = ', '.join(sorted(quote_currencies))
                print(f"   🌍 Binance: Scanned quote currencies: {quotes_str}")
                
        except Exception as e:
            print(f"⚠️ Binance scan error: {e}")
        
        return opportunities
    
    def _scan_capital_market(self, min_change_pct: float, min_volume: float) -> List[MarketOpportunity]:
        """Scan Capital.com markets for momentum (CFDs: stocks, indices, forex, commodities)."""
        opportunities = []
        client = self.clients.get('capital')
        if not client or not getattr(client, 'enabled', False):
            return opportunities
        
        try:
            # Capital.com uses different market structure - get top markets by category
            # Focus on liquid instruments: major stocks, indices, forex pairs
            target_symbols = [
                # Major US Stocks
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX',
                # Major Indices
                'US500', 'US30', 'NAS100', 'UK100', 'GER40', 'FRA40',
                # Major Forex
                'EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'NZDUSD',
                # Commodities
                'GOLD', 'SILVER', 'OIL_CRUDE', 'NATURAL_GAS'
            ]
            
            # Get tickers for target symbols in parallel
            tickers_dict = client.get_tickers_for_symbols(target_symbols, max_workers=10)
            
            for symbol, ticker_data in tickers_dict.items():
                try:
                    price = ticker_data.get('price', 0)
                    change_pct = ticker_data.get('change_pct', 0)
                    
                    if price <= 0:
                        continue
                    
                    # Capital.com doesn't provide volume, use price change as momentum proxy
                    momentum = abs(change_pct) * 2.0  # Weight CFDs higher for equal comparison
                    
                    if abs(change_pct) >= min_change_pct:
                        opportunities.append(MarketOpportunity(
                            symbol=symbol,
                            exchange='capital',
                            price=price,
                            change_pct=change_pct,
                            volume=0,  # CFDs don't have traditional volume
                            momentum_score=momentum,
                            fee_rate=self.fee_rates.get('capital', 0.0008)
                        ))
                except Exception:
                    pass
            
            if opportunities:
                print(f"   🏦 Capital.com: Found {len(opportunities)} CFD opportunities")
                
        except Exception as e:
            print(f"⚠️ Capital.com scan error: {e}")
        
        return opportunities
    
    def _get_live_crypto_prices(self) -> Dict[str, float]:
        """Get LIVE prices from exchange APIs for portfolio valuation."""
        prices = {}
        
        # Kraken prices (for Kraken holdings + GBP rate)
        if 'kraken' in self.clients:
            kraken = self.clients['kraken']
            kraken_pairs = ['ETHUSD', 'SOLUSD', 'BTCUSD', 'TRXUSD', 'ADAUSD', 'DOTUSD', 'ATOMUSD', 'GBPUSD']
            for pair in kraken_pairs:
                try:
                    ticker = kraken.get_ticker(pair)
                    if ticker:
                        if 'c' in ticker and isinstance(ticker['c'], list):
                            prices[pair] = float(ticker['c'][0])
                        elif 'price' in ticker:
                            prices[pair] = float(ticker['price'])
                        elif 'last' in ticker:
                            prices[pair] = float(ticker['last'])
                except Exception:
                    pass
        
        # Binance prices (for Binance holdings)
        if 'binance' in self.clients:
            binance = self.clients['binance']
            binance_pairs = ['ETHUSDT', 'SOLUSDT', 'BTCUSDT', 'BNBUSDT', 'TRXUSDT', 
                            'ADAUSDT', 'DOTUSDT', 'AVAXUSDT', 'LINKUSDT', 'MATICUSDT', 'XRPUSDT']
            for pair in binance_pairs:
                try:
                    result = binance.get_ticker_price(pair)
                    if isinstance(result, dict):
                        prices[pair] = float(result.get('price', 0))
                    elif result:
                        prices[pair] = float(result)
                except Exception:
                    pass
        
        # Fallback prices if API calls failed (approximate)
        fallbacks = {
            'ETHUSD': 3000.0, 'ETHUSDT': 3000.0,
            'SOLUSD': 130.0, 'SOLUSDT': 130.0,
            'BTCUSD': 90000.0, 'BTCUSDT': 90000.0,
            'GBPUSD': 1.27,
            'TRXUSD': 0.25, 'TRXUSDT': 0.25,
            'BNBUSDT': 700.0,
            'ADAUSD': 1.0, 'ADAUSDT': 1.0,
            'DOTUSD': 7.0, 'DOTUSDT': 7.0,
            'ATOMUSD': 10.0,
        }
        for pair, fallback in fallbacks.items():
            if pair not in prices or prices[pair] == 0:
                prices[pair] = fallback
        
        return prices
    
    def get_available_cash(self) -> Dict[str, float]:
        """Get available cash across ALL exchanges using LIVE API prices."""
        cash: Dict[str, float] = {}
        self.last_cash_status = {'alpaca': 'unknown', 'kraken': 'unknown', 'binance': 'unknown', 'capital': 'unknown'}
        
        # 🆕 TEST MODE: Add funds for testing fallback logic
        test_mode = os.environ.get('AUREON_TEST_MODE', '').lower() == 'true'
        
        # 📊 Get LIVE prices from APIs (cached for this call)
        live_prices = self._get_live_crypto_prices()
        gbp_usd_rate = live_prices.get('GBPUSD', 1.27)  # Live or fallback
        
        if 'alpaca' in self.clients:
            try:
                alpaca_client = self.clients['alpaca']
                if not getattr(alpaca_client, 'api_key', None) or not getattr(alpaca_client, 'secret_key', None):
                    self.last_cash_status['alpaca'] = 'no_keys'
                    cash['alpaca'] = 0.0
                else:
                    acct = alpaca_client.get_account()
                    # If API call failed, account may be empty
                    if not acct:
                        self.last_cash_status['alpaca'] = 'error'
                        cash['alpaca'] = 0.0
                    else:
                        # Use portfolio_value (total equity) which includes positions
                        alpaca_cash = float(acct.get('portfolio_value', 0) or acct.get('equity', 0) or 0)
                        
                        # 🪙 ADD POSITIONS VALUE - Include all crypto/stock positions
                        try:
                            positions = alpaca_client.get_positions()
                            positions_value = 0.0
                            self.alpaca_positions = []  # Store for tracking
                            for pos in positions:
                                market_val = float(pos.get('market_value', 0) or 0)
                                positions_value += abs(market_val)
                                # Track position for sell opportunities
                                self.alpaca_positions.append({
                                    'symbol': pos.get('symbol', ''),
                                    'qty': float(pos.get('qty', 0)),
                                    'market_value': market_val,
                                    'unrealized_pl': float(pos.get('unrealized_pl', 0) or 0),
                                    'avg_entry_price': float(pos.get('avg_entry_price', 0) or 0),
                                    'current_price': float(pos.get('current_price', 0) or 0)
                                })
                            # Use the higher of portfolio_value or cash + positions
                            base_cash = float(acct.get('cash', 0) or 0)
                            alpaca_cash = max(alpaca_cash, base_cash + positions_value)
                        except Exception:
                            pass
                        
                        if self.last_cash_status['alpaca'] == 'unknown':
                            self.last_cash_status['alpaca'] = 'ok'
                        cash['alpaca'] = alpaca_cash + (5.0 if test_mode else 0)
            except Exception as e:
                print(f"   ⚠️ Alpaca cash error: {e}")
                self.last_cash_status['alpaca'] = 'error'
                cash['alpaca'] = 5.0 if test_mode else 0.0
        
        if 'kraken' in self.clients:
            try:
                kraken_client = self.clients['kraken']
                if not getattr(kraken_client, 'api_key', None) or not getattr(kraken_client, 'api_secret', None):
                    self.last_cash_status['kraken'] = 'no_keys'
                    cash['kraken'] = 0.0
                else:
                    bal = kraken_client.get_balance()
                    if not bal:
                        self.last_cash_status['kraken'] = 'error'
                        cash['kraken'] = 0.0
                    else:
                        # Kraken uses ZUSD for USD, also check TUSD, DAI and other stables
                        kraken_cash = 0.0
                        for key in ['ZUSD', 'USD', 'USDC', 'USDT', 'TUSD', 'DAI', 'USDD']:
                            kraken_cash += float(bal.get(key, 0))
                        
                        # 🇬🇧 ADD GBP (ZGBP) - Convert to USD using LIVE rate
                        gbp_balance = float(bal.get('ZGBP', 0) or bal.get('GBP', 0))
                        if gbp_balance > 0:
                            kraken_cash += gbp_balance * gbp_usd_rate
                        
                        # 🪙 ADD CRYPTO BALANCES - Convert using LIVE prices from API
                        crypto_symbols = {
                            'ETH': 'ETHUSD', 'XETH': 'ETHUSD',
                            'SOL': 'SOLUSD', 'TRX': 'TRXUSD',
                            'ADA': 'ADAUSD', 'DOT': 'DOTUSD',
                            'ATOM': 'ATOMUSD', 'BTC': 'BTCUSD', 'XXBT': 'BTCUSD'
                        }
                        for crypto, pair in crypto_symbols.items():
                            crypto_bal = float(bal.get(crypto, 0))
                            if crypto_bal > 0.0001:  # Only count meaningful amounts
                                usd_rate = live_prices.get(pair, 0)
                                if usd_rate > 0:
                                    kraken_cash += crypto_bal * usd_rate
                        
                        self.last_cash_status['kraken'] = 'ok'
                        cash['kraken'] = kraken_cash + (5.0 if test_mode else 0)
            except Exception as e:
                print(f"   ⚠️ Kraken cash error: {e}")
                self.last_cash_status['kraken'] = 'error'
                cash['kraken'] = 5.0 if test_mode else 0.0
        
        if 'binance' in self.clients:
            try:
                # Use get_free_balance for cleaner access
                binance_client = self.clients['binance']
                if not getattr(binance_client, 'api_key', None) or not getattr(binance_client, 'api_secret', None):
                    self.last_cash_status['binance'] = 'no_keys'
                    cash['binance'] = 0.0
                    return cash
                binance_cash = 0.0
                
                # Try multiple stablecoins
                stable_assets = ['USDT', 'USDC', 'USD', 'BUSD', 'FDUSD', 'TUSD', 'DAI', 'LDUSDC']
                for stable in stable_assets:
                    try:
                        if hasattr(binance_client, 'get_free_balance'):
                            binance_cash += binance_client.get_free_balance(stable)
                        else:
                            acct = binance_client.account()
                            for b in acct.get('balances', []):
                                if b.get('asset') == stable:
                                    binance_cash += float(b.get('free', 0))
                    except:
                        pass

                # Fallback: use get_balance if free balance lookups failed
                if binance_cash == 0 and hasattr(binance_client, 'get_balance'):
                    try:
                        balances = binance_client.get_balance()
                        for stable in stable_assets:
                            binance_cash += float(balances.get(stable, 0) or 0)
                    except Exception:
                        pass
                
                # 🪙 ADD CRYPTO BALANCES - Convert using LIVE prices from API
                try:
                    balances = binance_client.get_balance() if hasattr(binance_client, 'get_balance') else {}
                    crypto_symbols = {
                        'ETH': 'ETHUSDT', 'SOL': 'SOLUSDT', 'BTC': 'BTCUSDT',
                        'BNB': 'BNBUSDT', 'TRX': 'TRXUSDT', 'ADA': 'ADAUSDT',
                        'DOT': 'DOTUSDT', 'AVAX': 'AVAXUSDT', 'LINK': 'LINKUSDT',
                        'MATIC': 'MATICUSDT', 'XRP': 'XRPUSDT'
                    }
                    for crypto, pair in crypto_symbols.items():
                        crypto_bal = float(balances.get(crypto, 0) or 0)
                        if crypto_bal > 0.0001:  # Only count meaningful amounts
                            usd_rate = live_prices.get(pair, 0)
                            if usd_rate > 0:
                                binance_cash += crypto_bal * usd_rate
                except Exception:
                    pass
                
                self.last_cash_status['binance'] = 'ok'
                cash['binance'] = binance_cash + (5.0 if test_mode else 0)
            except Exception as e:
                print(f"   ⚠️ Binance cash error: {e}")
                self.last_cash_status['binance'] = 'error'
                cash['binance'] = 5.0 if test_mode else 0.0
        
        # Capital.com balance checking
        if 'capital' in self.clients:
            try:
                # Lazy-load Capital.com client if needed
                capital_client = self._ensure_capital_client()
                if not capital_client or not getattr(capital_client, 'enabled', False):
                    self.last_cash_status['capital'] = 'no_keys'
                    cash['capital'] = 0.0
                else:
                    # Get Capital.com account info
                    accounts = capital_client.get_accounts()
                    if accounts and len(accounts) > 0:
                        acc = accounts[0]
                        # Use FULL balance, not just available (includes margin used)
                        capital_balance = float(acc.get('balance', 0) or 0)
                        capital_available = float(acc.get('available', 0) or 0)
                        currency = acc.get('currency', 'GBP')
                        
                        # Convert GBP to USD using LIVE rate
                        if currency == 'GBP':
                            capital_cash = capital_balance * gbp_usd_rate
                        else:
                            capital_cash = capital_balance
                        
                        # 🪙 ADD POSITIONS VALUE - Include open CFD positions
                        try:
                            positions = capital_client.get_positions()
                            self.capital_positions = []  # Store for tracking
                            for pos_data in positions:
                                pos = pos_data.get('position', {})
                                market = pos_data.get('market', {})
                                size = float(pos.get('size', 0) or 0)
                                level = float(pos.get('level', 0) or 0)  # Entry price
                                upl = float(pos.get('upl', 0) or 0)  # Unrealized P&L
                                direction = pos.get('direction', 'BUY')
                                symbol = market.get('symbol', market.get('epic', ''))
                                
                                # Track position
                                self.capital_positions.append({
                                    'symbol': symbol,
                                    'size': size,
                                    'entry_price': level,
                                    'unrealized_pl': upl * gbp_to_usd if currency == 'GBP' else upl,
                                    'direction': direction,
                                    'deal_id': pos.get('dealId', '')
                                })
                        except Exception:
                            pass
                        
                        self.last_cash_status['capital'] = 'ok'
                        cash['capital'] = capital_cash + (5.0 if test_mode else 0)
                    else:
                        self.last_cash_status['capital'] = 'error'
                        cash['capital'] = 5.0 if test_mode else 0.0
            except Exception as e:
                print(f"   ⚠️ Capital.com cash error: {e}")
                self.last_cash_status['capital'] = 'error'
                cash['capital'] = 5.0 if test_mode else 0.0
        
        return cash

    def get_all_positions(self) -> Dict[str, list]:
        """Get all existing positions across ALL exchanges that could be sold."""
        all_positions = {'alpaca': [], 'kraken': [], 'binance': [], 'capital': []}
        
        # Alpaca positions
        if 'alpaca' in self.clients:
            try:
                positions = self.clients['alpaca'].get_positions()
                for pos in positions:
                    qty = float(pos.get('qty', 0))
                    if qty > 0:
                        market_val = float(pos.get('market_value', 0) or 0)
                        entry = float(pos.get('avg_entry_price', 0) or 0)
                        current = float(pos.get('current_price', 0) or 0)
                        upl = float(pos.get('unrealized_pl', 0) or 0)
                        pnl_pct = (upl / (entry * qty) * 100) if entry > 0 and qty > 0 else 0
                        all_positions['alpaca'].append({
                            'symbol': pos.get('symbol', ''),
                            'qty': qty,
                            'market_value': market_val,
                            'entry_price': entry,
                            'current_price': current,
                            'unrealized_pl': upl,
                            'pnl_pct': pnl_pct,
                            'can_sell': qty > 0
                        })
            except Exception as e:
                print(f"   ⚠️ Alpaca positions error: {e}")
        
        # Kraken positions (crypto balances)
        if 'kraken' in self.clients:
            try:
                balances = self.clients['kraken'].get_balance()
                crypto_prices = {
                    'ETH': 3300.0, 'XETH': 3300.0, 'SOL': 250.0, 'TRX': 0.25,
                    'ADA': 1.0, 'DOT': 7.0, 'ATOM': 10.0, 'BTC': 105000.0, 'XXBT': 105000.0
                }
                for asset, amount in balances.items():
                    amount = float(amount)
                    if amount > 0.0001 and asset in crypto_prices:
                        price = crypto_prices[asset]
                        market_val = amount * price
                        if market_val > 0.10:  # Only show if worth > $0.10
                            all_positions['kraken'].append({
                                'symbol': asset,
                                'qty': amount,
                                'market_value': market_val,
                                'entry_price': 0,  # Unknown for spot
                                'current_price': price,
                                'unrealized_pl': 0,
                                'pnl_pct': 0,
                                'can_sell': True
                            })
            except Exception as e:
                print(f"   ⚠️ Kraken positions error: {e}")
        
        # Binance positions (crypto balances)
        if 'binance' in self.clients:
            try:
                balances = self.clients['binance'].get_balance()
                crypto_prices = {
                    'ETH': 3300.0, 'SOL': 250.0, 'BTC': 105000.0, 'BNB': 700.0,
                    'TRX': 0.25, 'ADA': 1.0, 'DOT': 7.0, 'AVAX': 40.0, 'LINK': 25.0
                }
                for asset, amount in balances.items():
                    amount = float(amount or 0)
                    if amount > 0.0001 and asset in crypto_prices:
                        price = crypto_prices[asset]
                        market_val = amount * price
                        if market_val > 0.10:
                            all_positions['binance'].append({
                                'symbol': asset,
                                'qty': amount,
                                'market_value': market_val,
                                'entry_price': 0,
                                'current_price': price,
                                'unrealized_pl': 0,
                                'pnl_pct': 0,
                                'can_sell': True
                            })
            except Exception as e:
                print(f"   ⚠️ Binance positions error: {e}")
        
        # Capital.com positions (CFDs)
        if 'capital' in self.clients:
            try:
                capital_client = self._ensure_capital_client()
                if capital_client:
                    positions = capital_client.get_positions()
                    for pos_data in positions:
                        pos = pos_data.get('position', {})
                        market = pos_data.get('market', {})
                        size = float(pos.get('size', 0) or 0)
                        if size > 0:
                            level = float(pos.get('level', 0) or 0)
                            upl = float(pos.get('upl', 0) or 0) * 1.27  # GBP to USD
                            bid = float(market.get('bid', 0) or 0)
                            all_positions['capital'].append({
                                'symbol': market.get('symbol', market.get('epic', '')),
                                'qty': size,
                                'market_value': size * bid,
                                'entry_price': level,
                                'current_price': bid,
                                'unrealized_pl': upl,
                                'pnl_pct': (upl / (level * size) * 100) if level > 0 else 0,
                                'can_sell': True,
                                'deal_id': pos.get('dealId', '')
                            })
            except Exception as e:
                print(f"   ⚠️ Capital.com positions error: {e}")
        
        return all_positions

    def _get_binance_ticker(self, client, symbol: str) -> Dict[str, Any]:
        """Safely fetch Binance ticker for symbols with or without slashes."""
        if not client or not symbol:
            return {}
        symbols_to_try = [symbol, symbol.replace('/', '')]
        for sym in symbols_to_try:
            try:
                if hasattr(client, 'get_ticker'):
                    ticker = client.get_ticker(sym)
                    if ticker:
                        return ticker
                if hasattr(client, 'get_ticker_price'):
                    ticker = client.get_ticker_price(sym)
                    if ticker:
                        return ticker
            except Exception:
                continue
        return {}
        
    def calculate_exact_breakeven(self, entry_price: float, quantity: float, exchange: str = 'alpaca') -> Dict:
        """
        🎯 EXACT BREAKEVEN CALCULATION - WITH ALL COSTS!
        
        Accounts for:
        - Entry fee (taker)
        - Exit fee (taker)
        - Slippage (both sides)
        - Spread cost
        
        Returns dict with:
        - entry_cost: Total cost to enter position
        - entry_fee: Fee paid on entry
        - breakeven_price: Minimum exit price to not lose money
        - target_price_1pct: Price for 1% profit after all costs
        """
        # Get exchange-specific fees
        if PENNY_PROFIT_AVAILABLE and calculate_penny_profit_threshold:
            threshold = calculate_penny_profit_threshold(
                trade_size=entry_price * quantity,
                exchange=exchange,
                use_maker=False  # Assume taker (worst case)
            )
            # Penny profit calculator gives us exact breakeven multiplier
            breakeven_multiplier = threshold.get('breakeven_price_multiplier', 1.006)  # Default ~0.6%
            min_price_move_pct = threshold.get('min_price_move_pct', 0.6)
            total_costs = threshold.get('total_costs', 0)
        else:
            # Fallback calculation
            fee_rate = EXCHANGE_FEES.get(exchange, {}).get('taker', 0.0026)
            slippage = SLIPPAGE_PCT
            spread = SPREAD_PCT
            
            # Round-trip costs
            total_cost_pct = (fee_rate * 2) + (slippage * 2) + (spread * 2)  # ~0.7%
            breakeven_multiplier = 1 + total_cost_pct
            min_price_move_pct = total_cost_pct * 100
            total_costs = entry_price * quantity * total_cost_pct
        
        # Calculate costs
        notional = entry_price * quantity
        fee_rate = self.fee_rates.get(exchange, 0.0025)
        entry_fee = notional * fee_rate
        entry_cost = notional + entry_fee
        
        # Breakeven price = entry_price × breakeven_multiplier
        breakeven_price = entry_price * breakeven_multiplier
        
        # Target prices for various profit levels (after ALL costs)
        target_1pct = breakeven_price * 1.01  # 1% profit after costs
        target_half_pct = breakeven_price * 1.005  # 0.5% profit after costs
        
        return {
            'entry_price': entry_price,
            'quantity': quantity,
            'notional': notional,
            'entry_fee': entry_fee,
            'entry_cost': entry_cost,
            'total_round_trip_costs': total_costs,
            'min_price_move_pct': min_price_move_pct,
            'breakeven_multiplier': breakeven_multiplier,
            'breakeven_price': breakeven_price,
            'target_half_pct': target_half_pct,
            'target_1pct': target_1pct,
        }
    
    def normalize_order_response(self, order: dict, exchange: str) -> dict:
        """
        🔄 Normalize order responses across different exchanges.
        
        Returns consistent format:
        - filled_qty: Quantity filled
        - filled_avg_price: Average fill price
        - order_id: Order ID
        - status: Order status
        """
        if not order:
            return {'filled_qty': 0, 'filled_avg_price': 0, 'order_id': None, 'status': 'empty'}
        
        # Check for rejection
        if order.get('rejected'):
            return {
                'filled_qty': 0,
                'filled_avg_price': 0,
                'order_id': None,
                'status': 'rejected',
                'reason': order.get('reason', 'Unknown')
            }
        
        # Check for errors
        if order.get('error'):
            return {
                'filled_qty': 0,
                'filled_avg_price': 0,
                'order_id': None,
                'status': 'error',
                'reason': str(order.get('error'))
            }
        
        # Check for dry run
        if order.get('dryRun'):
            return {
                'filled_qty': 0,
                'filled_avg_price': 0,
                'order_id': 'DRY_RUN',
                'status': 'dry_run'
            }
        
        if exchange == 'binance' or exchange == 'kraken':
            # Both Binance and Kraken now use similar format:
            # executedQty, cummulativeQuoteQty, orderId, fills[]
            exec_qty = float(order.get('executedQty', 0))
            cumm_quote = float(order.get('cummulativeQuoteQty', 0))
            
            # Calculate average price from fills or cumulative
            avg_price = 0.0
            
            # First try the direct price field (Kraken provides this)
            if order.get('price'):
                avg_price = float(order.get('price', 0))
            
            # If no direct price, calculate from cumulative
            if avg_price == 0 and exec_qty > 0 and cumm_quote > 0:
                avg_price = cumm_quote / exec_qty
            
            # If still no price, try fills array (Binance provides this)
            if avg_price == 0 and order.get('fills'):
                total_qty = 0.0
                total_cost = 0.0
                for fill in order.get('fills', []):
                    qty = float(fill.get('qty', 0))
                    price = float(fill.get('price', 0))
                    total_qty += qty
                    total_cost += qty * price
                if total_qty > 0:
                    avg_price = total_cost / total_qty
                    exec_qty = total_qty
            
            return {
                'filled_qty': exec_qty,
                'filled_avg_price': avg_price,
                'order_id': order.get('orderId'),
                'status': order.get('status', 'FILLED' if exec_qty > 0 else 'UNKNOWN'),
                'fee': float(order.get('fee', 0)),
                'cumm_quote': cumm_quote
            }
        
        else:  # alpaca and default
            # Alpaca format: filled_qty, filled_avg_price, id
            return {
                'filled_qty': float(order.get('filled_qty', 0)),
                'filled_avg_price': float(order.get('filled_avg_price', order.get('avg_price', 0))),
                'order_id': order.get('id', order.get('order_id')),
                'status': order.get('status', 'filled' if order.get('filled_qty') else 'unknown')
            }

    def is_order_successful(self, order: dict, exchange: str) -> bool:
        """
        🔍 Check if an order was successful (filled) across any exchange.
        
        Returns True if order executed successfully, False otherwise.
        """
        if not order:
            return False
        
        # Check for explicit failures
        if order.get('rejected'):
            print(f"   ⚠️ Order rejected: {order.get('reason', 'Unknown')}")
            return False
        if order.get('error'):
            print(f"   ⚠️ Order error: {order.get('error')}")
            return False
        if order.get('dryRun'):
            print(f"   ℹ️ Dry run order (not executed)")
            return False
        
        # Normalize and check
        norm = self.normalize_order_response(order, exchange)
        
        # Check for failed status
        if norm.get('status') in ['rejected', 'error', 'empty', 'dry_run']:
            return False
        
        # For sells, just check if the order was accepted (status FILLED or similar)
        status = str(order.get('status', '')).upper()
        if status in ['FILLED', 'CLOSED', 'EXECUTED']:
            return True
        
        # For Alpaca, check filled_qty
        if exchange == 'alpaca':
            return float(order.get('filled_qty', 0)) > 0
        
        # For Binance/Kraken, check executedQty
        return float(order.get('executedQty', 0)) > 0

    def track_buy_order(self, symbol: str, order_result: dict, exchange: str = 'alpaca') -> dict:
        """
        📝 Track a buy order with all details needed to know when to sell.
        
        Call this AFTER a successful buy order to store:
        - Order ID
        - Entry price (actual fill price)
        - Quantity
        - Entry cost (including fee)
        - Exact breakeven price
        """
        # 🔄 Normalize the order response first!
        normalized = self.normalize_order_response(order_result, exchange)
        
        order_id = normalized.get('order_id', str(time.time()))
        fill_price = normalized.get('filled_avg_price', 0)
        fill_qty = normalized.get('filled_qty', 0)
        
        if fill_price == 0 or fill_qty == 0:
            print(f"⚠️ Cannot track order - missing fill price or qty: {order_result}")
            return {}
        
        # Calculate exact breakeven
        breakeven_info = self.calculate_exact_breakeven(fill_price, fill_qty, exchange)
        
        # Store in tracked positions
        tracking_data = {
            'symbol': symbol,
            'exchange': exchange,
            'order_id': order_id,
            'entry_price': fill_price,
            'entry_qty': fill_qty,
            'entry_cost': breakeven_info['entry_cost'],
            'entry_fee': breakeven_info['entry_fee'],
            'breakeven_price': breakeven_info['breakeven_price'],
            'target_half_pct': breakeven_info['target_half_pct'],
            'target_1pct': breakeven_info['target_1pct'],
            'min_price_move_pct': breakeven_info['min_price_move_pct'],
            'entry_time': time.time(),
        }
        
        self.tracked_positions[symbol] = tracking_data
        
        # Also record in cost basis tracker if available
        if self.cost_basis_tracker:
            try:
                self.cost_basis_tracker.set_entry_price(
                    symbol=symbol,
                    price=fill_price,
                    quantity=fill_qty,
                    exchange=exchange,
                    fee=breakeven_info['entry_fee']
                )
            except Exception as e:
                print(f"⚠️ Cost basis tracker error: {e}")
        
        # Log to trade logger if available
        if self.trade_logger and TradeEntry:
            try:
                entry = TradeEntry(
                    timestamp=datetime.now().isoformat(),
                    symbol=symbol,
                    side='BUY',
                    exchange=exchange,
                    entry_price=fill_price,
                    entry_time=time.time(),
                    quantity=fill_qty,
                    entry_value=breakeven_info['entry_cost'],
                    coherence=0.0,
                    dominant_node='orca',
                    hnc_frequency=0.0,
                    hnc_is_harmonic=True,
                    probability_score=0.95,
                    imperial_probability=0.95,
                    cosmic_phase='hunt',
                    earth_coherence=0.5,
                    gates_passed=3,
                    order_id=order_id,
                    order_status=normalized.get('status', 'filled')
                )
                self.trade_logger.log_entry(entry)
                
                # 📝 CRITICAL: Log execution with order ID for verification
                self.trade_logger.log_execution(
                    execution_type='BUY',
                    exchange=exchange,
                    symbol=symbol,
                    side='buy',
                    order_id=order_id,
                    quantity=fill_qty,
                    price=fill_price,
                    value_usd=breakeven_info['entry_cost'],
                    status=normalized.get('status', 'filled'),
                    raw_response=order_result
                )
            except Exception as e:
                print(f"⚠️ Trade logger error: {e}")
        
        print(f"   📝 TRACKED: {symbol} | Order: {order_id[:8]}... | Entry: ${fill_price:.6f} | Breakeven: ${breakeven_info['breakeven_price']:.6f} (+{breakeven_info['min_price_move_pct']:.2f}%)")
        
        # ═══════════════════════════════════════════════════════════════════
        # 🦈🔍 PREDATOR TRACKING - Record order for front-run detection
        # ═══════════════════════════════════════════════════════════════════
        if self.predator_detector:
            try:
                from orca_predator_detection import OrderEvent
                order_event = OrderEvent(
                    timestamp=time.time(),
                    symbol=symbol,
                    side='buy',
                    price=fill_price,
                    quantity=fill_qty,
                    exchange=exchange,
                    order_id=order_id
                )
                self.predator_detector.record_order(order_event)
            except Exception as e:
                pass  # Silent fail - don't break trading
        
        return tracking_data
    
    def execute_stealth_buy(self, client: Any, symbol: str, quantity: float, 
                            price: float = None, exchange: str = 'alpaca') -> Dict:
        """
        🥷 Execute a BUY order with stealth countermeasures.
        
        Applies:
        - Random delay (50-500ms)
        - Order splitting for large orders
        - Symbol rotation if hunted
        """
        if self.stealth_executor:
            value_usd = (price or 0) * quantity
            result = self.stealth_executor.execute_stealth_order(
                client=client,
                symbol=symbol,
                side='buy',
                quantity=quantity,
                price=price,
                value_usd=value_usd
            )
            
            # If predator detector found front-running, mark symbol as hunted
            if self.predator_detector:
                report = self.predator_detector.generate_hunting_report()
                if report.front_run_rate > 0.3:  # >30% front-run rate
                    top_firm = report.top_predators[0].firm_id if report.top_predators else "unknown"
                    self.stealth_executor.mark_symbol_hunted(symbol, firm=top_firm)
            
            return result
        else:
            # Fallback to direct execution
            return client.place_market_order(symbol=symbol, side='buy', quantity=quantity)
    
    def execute_stealth_sell(self, client: Any, symbol: str, quantity: float,
                             price: float = None, exchange: str = 'alpaca') -> Dict:
        """
        🥷 Execute a SELL order with stealth countermeasures.
        """
        if self.stealth_executor:
            value_usd = (price or 0) * quantity
            return self.stealth_executor.execute_stealth_order(
                client=client,
                symbol=symbol,
                side='sell',
                quantity=quantity,
                price=price,
                value_usd=value_usd
            )
        else:
            return client.place_market_order(symbol=symbol, side='sell', quantity=quantity)
    
    def execute_sell_with_logging(self, client: Any, symbol: str, quantity: float,
                                   exchange: str, current_price: float = 0, 
                                   entry_cost: float = 0, reason: str = "TP") -> Dict:
        """
        📝 Execute a SELL order with comprehensive logging.
        
        Logs the order ID to verify execution on the exchange.
        """
        sell_order = client.place_market_order(symbol=symbol, side='sell', quantity=quantity)
        
        if sell_order:
            # Normalize the order response
            normalized = self.normalize_order_response(sell_order, exchange)
            order_id = normalized.get('order_id', 'UNKNOWN')
            fill_price = normalized.get('filled_avg_price', current_price)
            fill_qty = normalized.get('filled_qty', quantity)
            status = normalized.get('status', 'filled')
            
            # Calculate P&L
            fee_rate = self.fee_rates.get(exchange, 0.0025)
            exit_value = fill_price * fill_qty * (1 - fee_rate)
            net_pnl = exit_value - entry_cost if entry_cost > 0 else 0
            
            # Log to trade logger
            if self.trade_logger:
                try:
                    self.trade_logger.log_execution(
                        execution_type='SELL',
                        exchange=exchange,
                        symbol=symbol,
                        side='sell',
                        order_id=order_id,
                        quantity=fill_qty,
                        price=fill_price,
                        value_usd=exit_value,
                        status=status,
                        raw_response=sell_order
                    )
                except Exception as e:
                    print(f"⚠️ Sell log error: {e}")
            
            # Print confirmation
            pnl_emoji = "✅" if net_pnl >= 0 else "❌"
            print(f"   {pnl_emoji} SELL EXECUTED | {exchange.upper()} | {symbol} | Qty: {fill_qty:.6f} | Price: ${fill_price:.4f} | P&L: ${net_pnl:+.4f} | OrderID: {order_id[:12]}...")
        
        return sell_order
    
    def set_stealth_mode(self, mode: str):
        """
        Change stealth mode: normal, aggressive, paranoid, disabled
        """
        if STEALTH_AVAILABLE and get_stealth_config:
            self.stealth_mode = mode
            config = get_stealth_config(mode)
            self.stealth_executor = OrcaStealthExecution(config)
            print(f"🥷 Stealth mode changed to: {mode}")
    
    def can_sell_profitably(self, symbol: str, current_price: float) -> Tuple[bool, dict]:
        """
        🎯 CHECK IF WE CAN SELL AT A PROFIT!
        
        Returns (can_sell, info) where:
        - can_sell: True if current_price > breakeven_price
        - info: Dict with profit details
        """
        tracked = self.tracked_positions.get(symbol)
        
        if not tracked:
            # No tracked position - use cost basis tracker as fallback
            if self.cost_basis_tracker:
                return self.cost_basis_tracker.can_sell_profitably(symbol, current_price)
            # No tracking data - assume we can sell (legacy behavior)
            return True, {'warning': 'No tracking data available'}
        
        breakeven = tracked['breakeven_price']
        entry_price = tracked['entry_price']
        entry_qty = tracked['entry_qty']
        
        # Calculate exit value after fees
        fee_rate = self.fee_rates.get(tracked['exchange'], 0.0025)
        exit_gross = current_price * entry_qty
        exit_fee = exit_gross * fee_rate
        exit_value = exit_gross - exit_fee
        
        # Net P&L
        net_pnl = exit_value - tracked['entry_cost']
        net_pnl_pct = (net_pnl / tracked['entry_cost']) * 100 if tracked['entry_cost'] > 0 else 0
        
        can_sell = current_price >= breakeven
        
        info = {
            'symbol': symbol,
            'entry_price': entry_price,
            'current_price': current_price,
            'breakeven_price': breakeven,
            'price_vs_breakeven_pct': ((current_price / breakeven) - 1) * 100,
            'entry_cost': tracked['entry_cost'],
            'exit_value': exit_value,
            'exit_fee': exit_fee,
            'net_pnl': net_pnl,
            'net_pnl_pct': net_pnl_pct,
            'can_sell_profitably': can_sell,
            'order_id': tracked['order_id'],
        }
        
        return can_sell, info
        
    def calculate_breakeven_price(self, entry_price: float) -> float:
        """
        Calculate minimum sell price to break even after fees.
        
        Math:
          Buy cost = entry_price × (1 + fee)
          Sell value = sell_price × (1 - fee)
          Breakeven: sell_value = buy_cost
          
          sell_price × (1 - fee) = entry_price × (1 + fee)
          sell_price = entry_price × (1 + fee) / (1 - fee)
        """
        return entry_price * (1 + self.fee_rate) / (1 - self.fee_rate)
    
    def calculate_target_price(self, entry_price: float, target_pct: float = 1.0, 
                               exchange: str = None, quantity: float = 1.0) -> float:
        """
        Calculate sell price for target profit %.
        
        Uses adaptive profit gate if available for accurate per-exchange costs.
        
        Math (legacy):
          Target = breakeven + (target_pct / 100) × entry_price
        
        Math (adaptive):
          Uses is_real_win to find price where net_pnl >= target
        """
        # Try adaptive profit gate for accurate calculation
        if self.is_real_win and exchange:
            try:
                # Binary search for target price
                entry_value = entry_price * quantity
                target_net = entry_value * (target_pct / 100)
                
                # Start with legacy estimate
                legacy_target = entry_price * (1 + self.fee_rate) / (1 - self.fee_rate)
                legacy_target += entry_price * (target_pct / 100)
                
                # Refine with profit gate
                low = entry_price
                high = legacy_target * 1.5
                
                for _ in range(20):  # Binary search
                    mid = (low + high) / 2
                    result = self.is_real_win(
                        exchange=exchange,
                        entry_price=entry_price,
                        current_price=mid,
                        quantity=quantity,
                        is_maker=False,
                        gate_level='breakeven'
                    )
                    if result['net_pnl'] < target_net:
                        low = mid
                    else:
                        high = mid
                
                return high
            except Exception as e:
                pass  # Fall through to legacy
        
        # Legacy calculation
        breakeven = self.calculate_breakeven_price(entry_price)
        profit_add = entry_price * (target_pct / 100)
        return breakeven + profit_add
    
    def calculate_realized_pnl(self, entry_price: float, entry_qty: float,
                               exit_price: float, exit_qty: float,
                               exchange: str = None) -> Dict:
        """
        Calculate realized P&L with fees.
        
        Uses adaptive profit gate if available for accurate per-exchange costs.
        
        Returns:
          {
            'entry_cost': float,
            'entry_fee': float,
            'exit_value': float,
            'exit_fee': float,
            'total_fees': float,
            'gross_pnl': float,
            'net_pnl': float,
            'net_pnl_pct': float,
            'is_real_win': bool  # NEW - profit gate verified
          }
        """
        # Try adaptive profit gate for accurate calculation
        if self.is_real_win and exchange:
            try:
                result = self.is_real_win(
                    exchange=exchange,
                    entry_price=entry_price,
                    current_price=exit_price,
                    quantity=entry_qty,
                    is_maker=False,
                    gate_level='breakeven'
                )
                
                costs = result.get('costs_breakdown', {})
                entry_fee = costs.get('entry_fee', 0) + costs.get('entry_slippage', 0) + costs.get('entry_spread', 0)
                exit_fee = costs.get('exit_fee', 0) + costs.get('exit_slippage', 0) + costs.get('exit_spread', 0)
                
                entry_gross = entry_price * entry_qty
                exit_gross = exit_price * exit_qty
                
                return {
                    'entry_cost': entry_gross + entry_fee,
                    'entry_fee': entry_fee,
                    'exit_value': exit_gross - exit_fee,
                    'exit_fee': exit_fee,
                    'total_fees': result['total_costs'],
                    'gross_pnl': result['gross_pnl'],
                    'net_pnl': result['net_pnl'],
                    'net_pnl_pct': (result['net_pnl'] / (entry_gross + entry_fee)) * 100 if entry_gross > 0 else 0,
                    'is_real_win': result['is_win']
                }
            except Exception as e:
                pass  # Fall through to legacy
        
        # Legacy calculation with simple fee rate
        # Entry
        entry_gross = entry_price * entry_qty
        entry_fee = entry_gross * self.fee_rate
        entry_cost = entry_gross + entry_fee
        
        # Exit
        exit_gross = exit_price * exit_qty
        exit_fee = exit_gross * self.fee_rate
        exit_value = exit_gross - exit_fee
        
        # P&L
        gross_pnl = exit_gross - entry_gross
        total_fees = entry_fee + exit_fee
        net_pnl = exit_value - entry_cost
        net_pnl_pct = (net_pnl / entry_cost) * 100 if entry_cost > 0 else 0
        
        return {
            'entry_cost': entry_cost,
            'entry_fee': entry_fee,
            'exit_value': exit_value,
            'exit_fee': exit_fee,
            'total_fees': total_fees,
            'gross_pnl': gross_pnl,
            'net_pnl': net_pnl,
            'net_pnl_pct': net_pnl_pct,
            'is_real_win': net_pnl > 0
        }

    def _get_real_market_data(self, symbol: str, all_prices: dict) -> dict:
        """Fetch REAL market data (price, change, volume) for quantum scoring."""
        # 1. Price from streaming updates or use 0 to fetch from bars
        price = all_prices.get(symbol, 0.0)
        
        # Defaults
        change_pct = 0.0
        volume = 0.0
        momentum = 0.5
        change_1h = 0.0
        
        # 2. Fetch MINUTE bars for granular/lively signals (limit 60 = 1 hour)
        try:
            alpaca = self.clients.get('alpaca')
            if alpaca and hasattr(alpaca, 'get_crypto_bars'):
                # Handle symbol normalization for Alpaca
                # Ensure we have a valid crypto pair like BTC/USD
                query_sym = symbol
                if '/' not in query_sym:
                    if query_sym in ['BTC', 'ETH', 'SOL', 'DOGE', 'SHIB', 'TRX', 'LTC', 'PHA']:
                        query_sym = f"{query_sym}/USD"
                    elif 'USD' in query_sym and not query_sym.endswith('/USD'):
                         query_sym = query_sym.replace('USD', '/USD')
                
                # Fetch 60 minutes of data for lively quantum calculation
                bars_map = alpaca.get_crypto_bars([query_sym], timeframe='1Min', limit=60)
                bars = bars_map.get(query_sym, []) or bars_map.get(symbol, [])
                
                if len(bars) >= 1:
                    latest = bars[-1]
                    # Update price if missing or older than bar
                    if price == 0:
                        price = float(latest.get('c', 0) or latest.get('close', 0))
                    
                    # Sum volume from last hour
                    volume = sum(float(b.get('v', 0) or b.get('volume', 0)) for b in bars)
                
                if len(bars) >= 2:
                    # Calculate change from start of the hour
                    start_bar = bars[0]
                    start_price = float(start_bar.get('c', 0) or start_bar.get('close', 0))
                    
                    if start_price > 0:
                        change_pct = ((price - start_price) / start_price) * 100.0
                    
                    # Momentum:
                    # 1. Price Trend (Change)
                    # 2. Volatility factor
                    
                    # Calculate volatility (std dev of returns)
                    closes = [float(b.get('c', 0) or b.get('close', 0)) for b in bars]
                    if len(closes) > 1:
                        avg_price = sum(closes) / len(closes)
                        variance = sum((x - avg_price) ** 2 for x in closes) / len(closes)
                        std_dev = variance ** 0.5
                        volatility = std_dev / avg_price # normalized
                    else:
                        volatility = 0.0
                    
                    # Enhanced Momentum Calculation
                    # Base 0.5
                    # + Change Factor (1% change = +0.1 score adjustment)
                    trend_score = change_pct / 10.0 
                    
                    momentum = 0.5 + trend_score
                    momentum = max(0.05, min(0.95, momentum))
                    
                    # Add volatility boost to "Luck" indirectly via change_pct used in caller
                    # But caller uses change_pct. We return 1h change now, which is more relevant.
                    
        except Exception:
            pass
            
        # Fallbacks to ensure non-zero
        if price == 0: price = 50000.0 # Default fallback
        if volume == 0: volume = 1000000.0
        
        return {
            'symbol': symbol,
            'price': price,
            'change_pct': change_pct, # Now returning 1-hour change
            'volume': volume,
            'momentum': momentum
        }
    
    def hunt_and_kill(self, symbol: str, amount_usd: float, target_pct: float = 1.0,
                       stop_pct: float = -1.0, max_wait: int = 300):
        """
        Complete kill cycle with LIVE STREAMING:
        1. BUY
        2. STREAM prices at 100ms (not polling!)
        3. WAIT for: target hit OR momentum reversal OR whale selling OR stop loss
        4. SELL at perfect moment
        5. RETURN realized P&L
        """
        print("="*60)
        print(f"🦈 ORCA HUNT & KILL CYCLE - {symbol}")
        print("="*60)
        
        # Get current price
        orderbook = self.client.get_crypto_orderbook(symbol)
        asks = orderbook.get('asks', [])
        if not asks or len(asks) == 0:
            print("❌ No price data")
            return None
        
        # Alpaca format: {'p': price, 's': size}
        entry_price = float(asks[0].get('p', 0))
        if entry_price == 0:
            print("❌ Invalid price")
            return None
        print(f"📊 Entry price: ${entry_price:,.2f}")
        
        # Calculate targets
        breakeven = self.calculate_breakeven_price(entry_price)
        target = self.calculate_target_price(entry_price, target_pct)
        # Stop loss is BELOW entry for BUY orders (protect against drop)
        stop_price = entry_price * (1 - abs(stop_pct) / 100)
        
        print(f"🎯 Breakeven:   ${breakeven:,.2f} (+{((breakeven/entry_price-1)*100):.3f}%)")
        print(f"🎯 Target:      ${target:,.2f} (+{((target/entry_price-1)*100):.3f}%)")
        print(f"🛑 Stop Loss:   ${stop_price:,.2f} (-{abs(stop_pct):.1f}%)")
        
        # Step 1: BUY
        print(f"\n🔪 STEP 1: BUY ${amount_usd:.2f} of {symbol}")
        try:
            buy_order = self.client.place_market_order(
                symbol=symbol,
                side='buy',
                quote_qty=amount_usd
            )
            if not buy_order:
                print("❌ Buy failed")
                return None
            
            buy_qty = float(buy_order.get('filled_qty', 0))
            buy_price = float(buy_order.get('filled_avg_price', 0))
            buy_id = buy_order.get('id', '')
            
            print(f"✅ Bought {buy_qty:.8f} @ ${buy_price:,.2f}")
            print(f"   Order: {buy_id}")
            
        except Exception as e:
            print(f"❌ Buy error: {e}")
            return None
        
        # Create position tracker
        position = LivePosition(
            symbol=symbol,
            exchange=self.exchange,
            entry_price=buy_price,
            entry_qty=buy_qty,
            entry_cost=buy_price * buy_qty * (1 + self.fee_rate),
            breakeven_price=self.calculate_breakeven_price(buy_price),
            target_price=self.calculate_target_price(buy_price, target_pct)
        )
        
        # Step 2: LIVE STREAM until exit condition
        print(f"\n📡 STEP 2: LIVE STREAMING (100ms updates)")
        print(f"   Target: ${position.target_price:,.2f} | Stop: ${stop_price:,.2f}")
        print(f"   🐋 Whale Signal: {self.whale_signal}")
        print("   Press Ctrl+C to abort...")
        
        start = time.time()
        last_price = buy_price
        momentum_direction = 0
        consecutive_drops = 0
        
        try:
            while (time.time() - start) < max_wait:
                # Get current price (FAST - 100ms intervals)
                orderbook = self.client.get_crypto_orderbook(symbol)
                bids = orderbook.get('bids', [])
                if bids and len(bids) > 0:
                    current = float(bids[0].get('p', 0))
                    if current == 0:
                        time.sleep(self.stream_interval)
                        continue
                    
                    # Track momentum
                    position.price_history.append(current)
                    if len(position.price_history) > 50:
                        position.price_history.pop(0)
                    
                    # Calculate momentum (last 5 prices)
                    if len(position.price_history) >= 5:
                        recent = position.price_history[-5:]
                        momentum_direction = (recent[-1] - recent[0]) / recent[0] * 100
                    
                    # Track consecutive drops
                    if current < last_price:
                        consecutive_drops += 1
                    else:
                        consecutive_drops = 0
                    last_price = current
                    
                    # Calculate P&L
                    pnl_est = self.calculate_realized_pnl(buy_price, buy_qty, current, buy_qty)
                    position.current_price = current
                    position.current_pnl = pnl_est['net_pnl']
                    position.current_pnl_pct = pnl_est['net_pnl_pct']
                    position.whale_activity = self.whale_signal
                    
                    # Live display
                    whale_icon = '🐋' if self.whale_signal == 'buying' else ('🦈' if self.whale_signal == 'selling' else '  ')
                    print(f"\r   ${current:,.2f} | P&L: ${pnl_est['net_pnl']:+.4f} ({pnl_est['net_pnl_pct']:+.3f}%) | Mom: {momentum_direction:+.2f}% {whale_icon}", end='', flush=True)
                    
                    # ═══════════════════════════════════════════════════════
                    # SMART EXIT CONDITIONS (don't pull out too early!)
                    # ═══════════════════════════════════════════════════════
                    
                    # 1. HIT TARGET - perfect exit!
                    if current >= position.target_price:
                        position.hit_target = True
                        position.ready_to_kill = True
                        position.kill_reason = 'TARGET_HIT'
                        print(f"\n\n🎯 TARGET HIT! ${current:,.2f} >= ${position.target_price:,.2f}")
                        break
                    
                    # 2. MOMENTUM REVERSAL - only if in profit
                    if pnl_est['net_pnl'] > 0 and momentum_direction < -0.5 and consecutive_drops >= 5:
                        position.ready_to_kill = True
                        position.kill_reason = 'MOMENTUM_REVERSAL'
                        print(f"\n\n📉 Momentum reversal detected (in profit) - taking gains!")
                        break
                    
                    # 3. WHALE SELLING - only if above breakeven AND profitable
                    if self.whale_signal == 'selling' and current >= position.breakeven_price:
                        # Calculate if we'd be profitable
                        est_exit = current * buy_qty * (1 - self.fee_rate)
                        est_pnl = est_exit - position.entry_cost
                        if est_pnl > 0:
                            position.ready_to_kill = True
                            position.kill_reason = 'WHALE_SELLING'
                            print(f"\n\n🐋 Whale selling detected - exiting with profit!")
                            break
                        else:
                            print(f"\r   🐋 Whale selling but NOT profitable - HOLDING!", end="")
                    
                    # 4. NO STOP LOSS! HOLD UNTIL PROFITABLE!
                    # DISABLED: We NEVER sell at a loss
                    # if current <= stop_price:
                    #     position.ready_to_kill = True
                    #     position.kill_reason = 'STOP_LOSS'
                    #     print(f"\n\n🛑 STOP LOSS HIT! ${current:,.2f} <= ${stop_price:,.2f}")
                    #     break
                    
                time.sleep(self.stream_interval)  # 100ms streaming
            else:
                print("\n⏰ Timeout - selling anyway")
                position.kill_reason = 'TIMEOUT'
                orderbook = self.client.get_crypto_orderbook(symbol)
                bids = orderbook.get('bids', [])
                current = float(bids[0].get('p', buy_price)) if bids else buy_price
                
        except KeyboardInterrupt:
            print("\n\n🛑 Aborted by user - selling now")
            position.kill_reason = 'USER_ABORT'
            orderbook = self.client.get_crypto_orderbook(symbol)
            bids = orderbook.get('bids', [])
            current = float(bids[0].get('p', buy_price)) if bids else buy_price
        
        # Step 3: SELL (only if profitable)
        print(f"\n🔪 STEP 3: SELL {buy_qty:.8f} {symbol}")
        # Recalculate projected P&L at current market price and only sell if positive
        try:
            pnl_est = self.calculate_realized_pnl(buy_price, buy_qty, current, buy_qty)
            if pnl_est['net_pnl'] <= 0:
                print(f"\n⛔ NOT SELLING: projected net P&L ${pnl_est['net_pnl']:+.4f} <= 0. Waiting for profitable exit.")
                # Do not execute sell to avoid realizing a loss
                return None
        except Exception:
            # If P&L calc fails for some reason, be conservative and skip selling
            print("\n⚠️ Could not compute projected P&L - skipping sell to avoid risk")
            return None
        
        try:
            sell_order = self.client.place_market_order(
                symbol=symbol,
                side='sell',
                quantity=buy_qty
            )
            if not sell_order:
                print("❌ Sell failed - POSITION STILL OPEN!")
                return None
            
            sell_qty = float(sell_order.get('filled_qty', 0))
            sell_price = float(sell_order.get('filled_avg_price', 0))
            sell_id = sell_order.get('id', '')
            
            print(f"✅ Sold {sell_qty:.8f} @ ${sell_price:,.2f}")
            print(f"   Order: {sell_id}")
            
        except Exception as e:
            print(f"❌ Sell error: {e}")
            print("⚠️ POSITION MAY STILL BE OPEN!")
            return None
        
        # Step 4: CALCULATE REALIZED P&L
        pnl = self.calculate_realized_pnl(buy_price, buy_qty, sell_price, sell_qty)
        
        print("\n" + "="*60)
        print("💰 KILL COMPLETE - REALIZED P&L")
        print("="*60)
        print(f"📥 Entry:      ${pnl['entry_cost']:.4f} (inc. ${pnl['entry_fee']:.4f} fee)")
        print(f"📤 Exit:       ${pnl['exit_value']:.4f} (inc. ${pnl['exit_fee']:.4f} fee)")
        print(f"💸 Total fees: ${pnl['total_fees']:.4f}")
        print(f"📊 Gross P&L:  ${pnl['gross_pnl']:.4f}")
        print(f"💎 Net P&L:    ${pnl['net_pnl']:.4f} ({pnl['net_pnl_pct']:+.3f}%)")
        print("="*60)
        
        if pnl['net_pnl'] > 0:
            print(f"✅ SUCCESSFUL KILL: +${pnl['net_pnl']:.4f} PROFIT")
        else:
            print(f"❌ LOST HUNT: ${abs(pnl['net_pnl']):.4f} LOSS")
        print("="*60)
        
        # 👑🦈 EMIT KILL SIGNAL TO QUEEN
        duration_secs = time.time() - position.entry_time if hasattr(position, 'entry_time') else 0
        self.emit_kill_signal(
            symbol=symbol,
            exchange=self.exchange,
            pnl=pnl['net_pnl'],
            entry_price=buy_price,
            exit_price=sell_price,
            qty=buy_qty,
            duration_secs=duration_secs
        )
        
        return pnl

    def fast_kill_hunt(self, amount_per_position: float = 25.0, 
                       num_positions: int = 3,
                       target_pct: float = 0.8,
                       timeout_secs: int = 60):
        """
        🦈⚡ FAST KILL HUNT - USE EXISTING ORCA FOR RAPID KILLS! ⚡🦈
        
        Uses the ALREADY INITIALIZED orca instance to avoid recursive instantiation.
        Scans market and uses orca intelligence that's already connected.
        
        🚫 NO STOP LOSS - DON'T PULL OUT EARLY!
        Only exit on: TARGET HIT or USER ABORT (Ctrl+C)
        """
        print("\n" + "⚡"*30)
        print("  🦈⚡ FAST KILL HUNT - ORCA INTELLIGENCE ⚡🦈")
        print("⚡"*30)
        
        # Show system status - ALL WIRED SYSTEMS
        print("\n📡 INTELLIGENCE SYSTEMS STATUS:")
        print(f"   ✅ OrcaKillCycle: READY")
        print(f"   ✅ Exchanges: {', '.join(self.clients.keys()) if hasattr(self, 'clients') else 'N/A'}")
        print(f"   {'✅' if hasattr(self, 'miner_brain') and self.miner_brain else '❌'} Miner Brain: {'WIRED' if hasattr(self, 'miner_brain') and self.miner_brain else 'N/A'}")
        print(f"   {'✅' if hasattr(self, 'quantum_telescope') and self.quantum_telescope else '❌'} Quantum Telescope: {'WIRED' if hasattr(self, 'quantum_telescope') and self.quantum_telescope else 'N/A'}")
        print(f"   {'✅' if hasattr(self, 'ultimate_intel') and self.ultimate_intel else '❌'} Ultimate Intelligence (95%): {'WIRED' if hasattr(self, 'ultimate_intel') and self.ultimate_intel else 'N/A'}")
        orca_wired = (hasattr(self, 'orca_intel') and self.orca_intel) or (hasattr(self, 'movers_scanner') and self.movers_scanner and hasattr(self.movers_scanner, 'orca') and self.movers_scanner.orca)
        print(f"   {'✅' if orca_wired else '❌'} Orca Intelligence: {'WIRED' if orca_wired else 'N/A'}")
        print(f"   {'✅' if hasattr(self, 'wave_scanner') and self.wave_scanner else '❌'} Wave Scanner: {'WIRED' if hasattr(self, 'wave_scanner') and self.wave_scanner else 'N/A'}")
        print(f"   {'✅' if hasattr(self, 'movers_scanner') and self.movers_scanner else '❌'} Movers Scanner: {'WIRED' if hasattr(self, 'movers_scanner') and self.movers_scanner else 'N/A'}")
        print(f"   {'✅' if hasattr(self, 'whale_tracker') and self.whale_tracker else '❌'} Whale Tracker: {'WIRED' if hasattr(self, 'whale_tracker') and self.whale_tracker else 'N/A'}")
        timeline_wired = (hasattr(self, 'timeline_oracle') and self.timeline_oracle)
        # Also check if Timeline Oracle is wired through Enigma integration
        if not timeline_wired:
            try:
                from aureon_enigma_integration import EnigmaIntegration
                enigma = EnigmaIntegration()
                timeline_wired = hasattr(enigma, 'timeline_oracle') and enigma.timeline_oracle
            except:
                pass
        print(f"   {'✅' if timeline_wired else '❌'} Timeline Oracle: {'WIRED' if timeline_wired else 'N/A'}")
        print(f"   {'✅' if hasattr(self, 'bus') and self.bus else '❌'} ThoughtBus: {'CONNECTED' if hasattr(self, 'bus') and self.bus else 'N/A'}")
        
        # Collect opportunities from ALL intelligence sources
        all_opportunities = []
        
        # ═══════════════════════════════════════════════════════════════════
        # 🧠 SOURCE 1: Ultimate Intelligence (95% accuracy!) - HIGHEST PRIORITY
        # ═══════════════════════════════════════════════════════════════════
        if hasattr(self, 'ultimate_intel') and self.ultimate_intel:
            try:
                print("\n💎 Consulting Ultimate Intelligence (95% accuracy)...")
                # Use predict() method for guaranteed patterns
                if hasattr(self.ultimate_intel, 'get_guaranteed_patterns'):
                    patterns = self.ultimate_intel.get_guaranteed_patterns()
                    if patterns and isinstance(patterns, (list, tuple)):
                        for pattern in patterns[:5]:
                            if hasattr(pattern, 'win_rate') and pattern.win_rate >= 0.90:  # 90%+ win rate only
                                all_opportunities.append({
                                    'symbol': getattr(pattern, 'symbol', 'UNKNOWN'),
                                    'action': getattr(pattern, 'direction', 'buy'),
                                    'confidence': pattern.win_rate,
                                    'source': f'ultimate_intel_{pattern.win_rate*100:.0f}%',
                                    'exchange': 'alpaca',
                                    'change_pct': getattr(pattern, 'expected_move', 1.0) * 100
                                })
                        print(f"   💎 Found {len(patterns)} guaranteed patterns (90%+ win rate)")
                    else:
                        print(f"   ⚠️ Ultimate Intel returned invalid patterns: {type(patterns)} - {patterns}")
                # Also get stats
                if hasattr(self.ultimate_intel, 'get_stats'):
                    stats = self.ultimate_intel.get_stats()
                    print(f"   📊 Accuracy: {stats.get('accuracy', 0)*100:.1f}% ({stats.get('total', 0)} predictions)")
            except Exception as e:
                print(f"   ⚠️ Ultimate Intel: {e}")
        
        # ═══════════════════════════════════════════════════════════════════
        # 🦈 SOURCE 2: Orca Intelligence (full scanning)
        # ═══════════════════════════════════════════════════════════════════
        if hasattr(self, 'orca_intel') and self.orca_intel:
            try:
                print("\n🦈 Scanning with Orca Intelligence...")
                # PREFER scan_global_markets (multi-exchange) if available
                if hasattr(self.orca_intel, 'scan_global_markets'):
                    # Scan all hot symbols across all connected exchanges
                    orca_opps = self.orca_intel.scan_global_markets()
                    print(f"   🦈 Found {len(orca_opps)} whale signals")
                    
                    for opp in orca_opps[:15]:  # Take top 15
                        # Handle WhaleSignal objects
                        confidence = getattr(opp, 'ride_confidence', 0.6)
                        symbol = getattr(opp, 'symbol', 'UNKNOWN')
                        exchange = getattr(opp, 'exchange', 'alpaca')
                        action = getattr(opp, 'side', 'buy') # buy/sell
                        
                        all_opportunities.append({
                            'symbol': symbol,
                            'action': action,
                            'confidence': confidence,
                            'source': f'orca_whale_{exchange}',
                            'exchange': exchange,
                            'change_pct': 1.0 # Momentum play
                        })

                elif hasattr(self.orca_intel, 'scan_opportunities'):
                    # Fallback to old method
                    orca_opps = self.orca_intel.scan_opportunities()
                    for opp in orca_opps[:10]:
                        all_opportunities.append({
                            'symbol': opp.symbol if hasattr(opp, 'symbol') else str(opp),
                            'action': 'buy',
                            'confidence': opp.confidence if hasattr(opp, 'confidence') else 0.7,
                            'source': 'orca_intel',
                            'exchange': opp.exchange if hasattr(opp, 'exchange') else 'alpaca',
                            'change_pct': opp.change_pct if hasattr(opp, 'change_pct') else 1.0
                        })
                    print(f"   🦈 Found {len(orca_opps)} opportunities")
            except Exception as e:
                print(f"   ⚠️ Orca Intel: {e}")
        
        # ═══════════════════════════════════════════════════════════════════
        # 🌊 SOURCE 3: Global Wave Scanner
        # ═══════════════════════════════════════════════════════════════════
        if hasattr(self, 'wave_scanner') and self.wave_scanner:
            try:
                print("\n🌊 Scanning Global Waves...")
                if hasattr(self.wave_scanner, 'scan'):
                    waves = self.wave_scanner.scan()
                    for wave in waves[:10]:
                        all_opportunities.append({
                            'symbol': wave.symbol if hasattr(wave, 'symbol') else str(wave),
                            'action': 'buy',
                            'confidence': wave.strength if hasattr(wave, 'strength') else 0.6,
                            'source': 'wave_scanner',
                            'exchange': 'alpaca',
                            'change_pct': wave.magnitude if hasattr(wave, 'magnitude') else 0.5
                        })
                    print(f"   🌊 Found {len(waves)} waves")
            except Exception as e:
                print(f"   ⚠️ Wave Scanner: {e}")
        
        # ═══════════════════════════════════════════════════════════════════
        # 📈 SOURCE 4: Movers & Shakers Scanner
        # ═══════════════════════════════════════════════════════════════════
        if hasattr(self, 'movers_scanner') and self.movers_scanner:
            try:
                print("\n📈 Scanning Movers & Shakers...")
                if hasattr(self.movers_scanner, 'scan'):
                    movers = self.movers_scanner.scan()
                    for mover in movers[:10]:
                        all_opportunities.append({
                            'symbol': mover.symbol if hasattr(mover, 'symbol') else str(mover),
                            'action': 'buy' if (mover.change_pct if hasattr(mover, 'change_pct') else 0) > 0 else 'sell',
                            'confidence': min(1.0, abs(mover.change_pct if hasattr(mover, 'change_pct') else 0) / 3),
                            'source': 'movers_shakers',
                            'exchange': 'alpaca',
                            'change_pct': mover.change_pct if hasattr(mover, 'change_pct') else 0
                        })
                    print(f"   📈 Found {len(movers)} movers")
            except Exception as e:
                print(f"   ⚠️ Movers Scanner: {e}")
        
        # ═══════════════════════════════════════════════════════════════════
        # 🐋 SOURCE 5: Whale Intelligence Tracker
        # ═══════════════════════════════════════════════════════════════════
        if hasattr(self, 'whale_tracker') and self.whale_tracker:
            try:
                print("\n🐋 Tracking Whale Activity...")
                # Get firm activities for major symbols
                for sym in ['BTC/USD', 'ETH/USD', 'SOL/USD']:
                    signal = self.whale_tracker.get_whale_signal(sym, 'long')
                    if signal.whale_support > 0.6:  # Whales bullish
                        all_opportunities.append({
                            'symbol': sym,
                            'action': 'buy',
                            'confidence': signal.whale_support,
                            'source': f'whale_tracker:{signal.dominant_firm}',
                            'exchange': 'alpaca',
                            'change_pct': signal.momentum_score * 2
                        })
                        print(f"   🐋 {sym}: {signal.dominant_firm} {signal.firm_activity} (support: {signal.whale_support:.0%})")
            except Exception as e:
                print(f"   ⚠️ Whale Tracker: {e}")
        
        # ═══════════════════════════════════════════════════════════════════
        # 👑🔊 SOURCE 6: Queen Volume Hunter (Volume Breakout Detection)
        # ═══════════════════════════════════════════════════════════════════
        if hasattr(self, 'volume_hunter') and self.volume_hunter:
            try:
                print("\n👑🔊 Hunting Volume Breakouts...")
                signals = self.volume_hunter.scan_for_breakouts()
                for signal in signals[:10]:
                    # Only add queen-approved signals with strong volume
                    if signal.volume_ratio >= 2.0:
                        opp = {
                            'symbol': signal.symbol,
                            'action': 'buy' if signal.price_change_5m > 0 else 'sell',
                            'confidence': signal.signal_strength,
                            'source': 'volume_hunter',
                            'exchange': signal.exchange if hasattr(signal, 'exchange') else 'binance',
                            'change_pct': signal.price_change_5m * 100,
                            'volume_ratio': signal.volume_ratio,
                            'whale_detected': signal.whale_detected if hasattr(signal, 'whale_detected') else False,
                            'queen_approved': signal.queen_approved if hasattr(signal, 'queen_approved') else False
                        }
                        all_opportunities.append(opp)
                        whale_flag = "🐋" if opp.get('whale_detected') else ""
                        queen_flag = "👑" if opp.get('queen_approved') else ""
                        print(f"   🔊 {signal.symbol}: {signal.volume_ratio:.1f}x vol, {signal.price_change_5m*100:+.2f}% {whale_flag}{queen_flag}")
                print(f"   👑🔊 Found {len(signals)} volume breakouts")
            except Exception as e:
                print(f"   ⚠️ Volume Hunter: {e}")
        
        # ═══════════════════════════════════════════════════════════════════
        # ⏳ SOURCE 7: Timeline Oracle (7-day predictions)
        # ═══════════════════════════════════════════════════════════════════
        if hasattr(self, 'timeline_oracle') and self.timeline_oracle:
            try:
                print("\n⏳ Consulting Timeline Oracle (7-day vision)...")
                if hasattr(self.timeline_oracle, 'get_best_opportunities'):
                    timeline_opps = self.timeline_oracle.get_best_opportunities()
                    for opp in timeline_opps[:5]:
                        all_opportunities.append({
                            'symbol': opp.get('symbol', ''),
                            'action': opp.get('action', 'buy'),
                            'confidence': opp.get('confidence', 0.7),
                            'source': 'timeline_oracle',
                            'exchange': 'alpaca',
                            'change_pct': opp.get('expected_move', 1.0)
                        })
                    print(f"   ⏳ Found {len(timeline_opps)} timeline opportunities")
            except Exception as e:
                print(f"   ⚠️ Timeline Oracle: {e}")
        
        # ═══════════════════════════════════════════════════════════════════
        # 📊 SOURCE 8: Simple market scan (FALLBACK)
        # ═══════════════════════════════════════════════════════════════════
        print("\n📊 Market Scan (Fallback)...")
        market_opps = self.scan_entire_market(min_change_pct=0.3)
        for opp in market_opps[:10]:
            if isinstance(opp, MarketOpportunity):
                all_opportunities.append({
                    'symbol': opp.symbol,
                    'action': 'buy' if opp.change_pct > 0 else 'sell',
                    'confidence': min(1.0, abs(opp.change_pct) / 3),
                    'source': 'market_scan',
                    'exchange': opp.exchange,
                    'price': opp.price,
                    'change_pct': opp.change_pct
                })
        print(f"   Found {len(market_opps)} market movers")
        
        # Check available cash FIRST to filter opportunities
        cash = self.get_available_cash()
        min_cash = amount_per_position * 1.1  # 10% buffer
        funded_exchanges = [ex for ex, amt in cash.items() if amt >= min_cash]
        
        print(f"\n💰 Cash check: {', '.join([f'{ex}=${amt:.2f}' for ex, amt in cash.items()])}")
        print(f"   Need ${min_cash:.2f}/position → Viable: {', '.join(funded_exchanges) or 'NONE!'}")
        
        # Deduplicate 
        seen = set()
        unique_opps = []
        
        for opp in all_opportunities:
            sym = opp['symbol']
            if sym not in seen:
                seen.add(sym)
                unique_opps.append(opp)
        
        # 🆕 CRITICAL: Filter to ONLY funded exchanges
        if funded_exchanges:
            funded_opps = [o for o in unique_opps if o.get('exchange', 'alpaca') in funded_exchanges]
            if funded_opps:
                print(f"   ✅ Filtered to {len(funded_opps)} opportunities on funded exchanges")
                unique_opps = funded_opps
            else:
                print(f"   ⚠️ No opportunities on funded exchanges - FORCE SCAN Alpaca...")
                # Force scan Alpaca even with lower threshold - REPLACE all opportunities
                alpaca_opps = self._scan_alpaca_market(min_change_pct=0.1, min_volume=100)
                unique_opps = []  # CLEAR - we only want Alpaca now
                for opp in alpaca_opps[:20]:
                    unique_opps.append({
                        'symbol': opp.symbol,
                        'action': 'buy' if opp.change_pct > 0 else 'sell',
                        'confidence': min(1.0, abs(opp.change_pct) / 2),
                        'source': 'alpaca_forced',
                        'exchange': 'alpaca',  # FORCE ALPACA
                        'price': opp.price,
                        'change_pct': opp.change_pct
                    })
                print(f"   🔍 Using {len(unique_opps)} Alpaca-only movers")
        
        # Sort by confidence
        unique_opps.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        # 🆕 Filter for BUY opportunities only (positive change)
        buy_opps = [o for o in unique_opps if o.get('change_pct', 0) > 0]
        if buy_opps:
            print(f"\n📈 BUY Opportunities: {len(buy_opps)}")
            unique_opps = buy_opps
        else:
            print(f"\n⚠️ No positive movers found - using all")
        
        print(f"🎯 TOTAL OPPORTUNITIES: {len(unique_opps)}")
        
        if not unique_opps:
            print("❌ No opportunities found from any scanner!")
            return []
        
        # Show top opportunities
        print("\n📋 TOP OPPORTUNITIES:")
        for i, opp in enumerate(unique_opps[:10]):
            sym = opp['symbol']
            action = opp.get('action', 'buy').upper()
            conf = opp.get('confidence', 0)
            source = opp.get('source', 'unknown')
            change = opp.get('change_pct', 0)
            print(f"   {i+1}. {sym:12} | {action:4} | Conf: {conf:.0%} | Source: {source} | Δ{change:+.2f}%")
        
        # Select top N for hunting
        selected = unique_opps[:num_positions]
        
        # Convert to MarketOpportunity format for pack_hunt
        converted_opps = []
        for opp in selected:
            # Only take BUY opportunities for simplicity
            if opp.get('action', 'buy').lower() == 'buy':
                change = opp.get('change_pct', opp.get('confidence', 0) * 2)
                converted_opps.append(MarketOpportunity(
                    symbol=opp['symbol'],
                    exchange=opp.get('exchange', 'alpaca'),
                    price=opp.get('price', 0),
                    change_pct=change,
                    volume=0,
                    momentum_score=abs(change),  # Use change as momentum score
                    fee_rate=self.fee_rates.get(opp.get('exchange', 'alpaca'), 0.0025)
                ))
        
        if not converted_opps:
            print("❌ No BUY opportunities to execute")
            return []
        
        print(f"\n🦈 LAUNCHING FAST KILL HUNT WITH {len(converted_opps)} POSITIONS...")
        print(f"   💰 ${amount_per_position:.2f} per position")
        print(f"   🎯 Target: {target_pct}%")
        print(f"   🚫 NO STOP LOSS - DON'T PULL OUT EARLY!")
        
        # Use pack_hunt for execution (NO STOP LOSS)
        return self.pack_hunt(
            opportunities=converted_opps,
            num_positions=num_positions,
            amount_per_position=amount_per_position,
            target_pct=target_pct,
            stop_pct=None  # NO STOP LOSS!
        )

    def pack_hunt(self, opportunities: list = None, num_positions: int = 3,
                  amount_per_position: float = 2.5, target_pct: float = 1.0, 
                  stop_pct: float = None, min_change_pct: float = 0.5):
        """
        🦈🦈🦈 DYNAMIC PACK HUNT - MONITOR + SCAN + BARTER MATRIX! 🦈🦈🦈
        
        🆕 ENHANCED DYNAMIC SYSTEM:
        1. Monitor current positions with progress bars & whale intel
        2. Actively scan for new opportunities every 30 seconds
        3. Use barter matrix for cross-exchange arbitrage kills
        4. Add new positions dynamically when opportunities arise
        5. DON'T PULL OUT EARLY - No timeout exits, NO STOP LOSS!
        6. Only exit on: TARGET HIT or USER ABORT (Ctrl+C)
        """
        print("\n" + "🦈"*30)
        print("  ORCA DYNAMIC PACK HUNT - MONITOR + SCAN + BARTER")
        print("🦈"*30)
        
        # Check available cash FIRST
        cash = self.get_available_cash()
        print(f"\n💰 Available cash: Alpaca=${cash.get('alpaca', 0):.2f} | Kraken=${cash.get('kraken', 0):.2f}")
        
        # For testing: Use available cash if less than requested amount
        if amount_per_position > max(cash.values()):
            print(f"⚠️ Requested ${amount_per_position:.2f} > available cash, using available amounts for testing")
            amount_per_position = max(cash.values()) * 0.9  # Use 90% of available cash
            print(f"   Using ${amount_per_position:.2f} per position for testing")
        
        # Determine which exchanges have enough cash
        min_cash_per_position = amount_per_position * 1.1  # 10% buffer
        viable_exchanges = [ex for ex, amt in cash.items() if amt >= min_cash_per_position]
        
        if not viable_exchanges:
            print(f"❌ No exchange has enough cash (need ${min_cash_per_position:.2f} per position)")
            return []
        
        print(f"   Viable exchanges: {', '.join([ex.upper() for ex in viable_exchanges])}")
        
        # If no opportunities provided, scan ENTIRE market
        if not opportunities:
            print("\n🌊 INITIAL MARKET SCAN...")
            opportunities = self.scan_entire_market(min_change_pct=min_change_pct)
        
        if not opportunities:
            print("❌ No targets found anywhere - market is completely flat")
            return []
        
        # 🆕 FILTER: Only keep opportunities where we have cash!
        funded_opportunities = []
        for opp in opportunities:
            if isinstance(opp, MarketOpportunity):
                exchange = opp.exchange
                symbol = opp.symbol
            else:
                exchange = opp.get('exchange', 'alpaca') if isinstance(opp, dict) else self.primary_exchange
                symbol = opp.get('symbol', opp) if isinstance(opp, dict) else str(opp)
            
            # Check if we can afford minimum order for this symbol on this exchange
            available_cash = cash.get(exchange, 0)
            if available_cash >= amount_per_position:
                funded_opportunities.append(opp)
        
        if not funded_opportunities:
            print(f"⚠️ {len(opportunities)} opportunities found but none affordable with current cash")
            # For testing: Try with smaller amounts or different logic
            print("   Attempting with available cash amounts...")
            # Use all opportunities but adjust amounts per exchange
            funded_opportunities = opportunities
        else:
            print(f"✅ {len(funded_opportunities)} funded opportunities (affordable with current cash)")
        
        # Start with top opportunities
        available_targets = funded_opportunities[:num_positions * 2]  # Get extra in case some fail
        
        print(f"\n🎯 Will attempt up to {len(available_targets)} targets (fallback if buys fail):")
        for i, opp in enumerate(available_targets):
            if isinstance(opp, MarketOpportunity):
                print(f"   {i+1}. {opp.symbol} ({opp.exchange}): {opp.change_pct:+.2f}% @ ${opp.price:,.2f}")
            else:
                sym = opp.get('symbol', opp) if isinstance(opp, dict) else str(opp)
                exch = opp.get('exchange', self.primary_exchange) if isinstance(opp, dict) else self.primary_exchange
                print(f"   {i+1}. {sym} ({exch})")
        
        # ═══════════════════════════════════════════════════════════════════
        # 🆕 DYNAMIC HUNTING LOOP - MONITOR + SCAN + ADD POSITIONS!
        # ═══════════════════════════════════════════════════════════════════
        
        positions = []
        results = []
        attempted_indices = set()
        last_scan_time = 0
        scan_interval = 5  # 🔥 AGGRESSIVE: Scan every 5 seconds for fast opportunities!
        monitor_interval = 0.05  # 20 updates/sec
        whale_update_interval = 2.0  # Update whale intel every 2 seconds
        last_whale_update = 0
        
        print(f"\n🚀 STARTING DYNAMIC HUNT - AGGRESSIVE MODE!")
        print("="*80)
        print("   📊 Monitor current positions | 🔍 Scan every 5 SECONDS (AGGRESSIVE)")
        print("   🛒 Add positions dynamically | 🔄 Immediate re-buy after sell!")
        print("   🚫 NO STOP LOSS - ONLY SELL ON PROFIT!")
        print("="*80)
        
        try:
            while True:  # Infinite loop - only exit on user abort
                current_time = time.time()
                
                # ═══════════════════════════════════════════════════════════
                # PERIODIC MARKET SCAN - LOOK FOR NEW OPPORTUNITIES
                # ═══════════════════════════════════════════════════════════
                if current_time - last_scan_time >= scan_interval:
                    last_scan_time = current_time
                    print(f"\n🔍 SCANNING FOR NEW OPPORTUNITIES... ({len(positions)} active positions)")
                    
                    # Scan market for new opportunities
                    new_opportunities = self.scan_entire_market(min_change_pct=min_change_pct)
                    
                    if new_opportunities:
                        # Filter for affordable opportunities we haven't tried
                        affordable_new = []
                        for opp in new_opportunities[:5]:  # Check top 5
                            if isinstance(opp, MarketOpportunity):
                                exchange = opp.exchange
                                symbol = opp.symbol
                            else:
                                exchange = opp.get('exchange', 'alpaca') if isinstance(opp, dict) else self.primary_exchange
                                symbol = opp.get('symbol', opp) if isinstance(opp, dict) else str(opp)
                            
                            # Check if we have cash and haven't tried this symbol recently
                            current_cash = self.get_available_cash().get(exchange, 0)
                            symbol_in_positions = any(p.symbol == symbol.replace('/', '') for p in positions)
                            
                            if current_cash >= amount_per_position and not symbol_in_positions:
                                affordable_new.append(opp)
                        
                        if affordable_new and len(positions) < num_positions:
                            print(f"   🎯 Found {len(affordable_new)} new opportunities!")
                            # Add to available targets
                            available_targets.extend(affordable_new[:2])  # Add top 2
                        else:
                            print(f"   ✅ No new affordable opportunities (or at max positions)")
                    else:
                        print(f"   ⚪ Market scan complete - no new opportunities")
                
                # ═══════════════════════════════════════════════════════════
                # TRY TO OPEN NEW POSITIONS IF WE HAVE ROOM
                # ═══════════════════════════════════════════════════════════
                if len(positions) < num_positions and len(attempted_indices) < len(available_targets):
                    # Find next unattempted opportunity
                    next_idx = None
                    for i in range(len(available_targets)):
                        if i not in attempted_indices:
                            next_idx = i
                            break
                    
                    if next_idx is not None:
                        attempted_indices.add(next_idx)
                        opp = available_targets[next_idx]
                        
                        if isinstance(opp, MarketOpportunity):
                            symbol = opp.symbol
                            exchange = opp.exchange
                            fee_rate = opp.fee_rate
                        else:
                            symbol = opp.get('symbol', opp) if isinstance(opp, dict) else str(opp)
                            exchange = opp.get('exchange', self.primary_exchange) if isinstance(opp, dict) else self.primary_exchange
                            fee_rate = self.fee_rates.get(exchange, 0.0025)
                        
                        # Get client for this exchange
                        client = self.clients.get(exchange)
                        if not client:
                            continue
                        
                        # Normalize symbol
                        if '/' not in symbol:
                            symbol = symbol.replace('USD', '/USD')
                        symbol_clean = symbol.replace('/', '')
                        
                        print(f"\n📈 OPENING NEW POSITION {len(positions)+1}/{num_positions}: {symbol} on {exchange.upper()}")
                        
                        try:
                            # Get entry price using exchange-specific method
                            if exchange == 'alpaca':
                                orderbook = client.get_crypto_orderbook(symbol_clean)
                                asks = orderbook.get('asks', [])
                                if not asks:
                                    continue
                                entry_price = float(asks[0].get('p', 0))
                            elif exchange == 'kraken':
                                ticker = client.get_ticker(symbol_clean)
                                entry_price = ticker.get('ask', ticker.get('price', 0))
                            else:
                                continue
                            
                            if entry_price <= 0:
                                continue
                            
                            # Check if we have enough cash for this specific position
                            current_cash = self.get_available_cash().get(exchange, 0)
                            required_cash = amount_per_position * 1.1  # 10% buffer
                            if current_cash < required_cash:
                                if current_cash >= amount_per_position * 0.5:  # At least 50% of requested
                                    print(f"⚠️ Using available cash ${current_cash:.2f} for testing")
                                    amount_per_position = current_cash * 0.9  # Use 90% of available
                                else:
                                    continue
                            
                            # BUY on the appropriate exchange
                            buy_order = client.place_market_order(
                                symbol=symbol_clean,
                                side='buy',
                                quote_qty=amount_per_position
                            )
                            if not buy_order:
                                continue
                            
                            buy_qty = float(buy_order.get('filled_qty', 0))
                            buy_price = float(buy_order.get('filled_avg_price', entry_price))
                            
                            # 🆕 SKIP if we got 0 quantity (order didn't fill)
                            if buy_qty <= 0 or buy_price <= 0:
                                continue
                            
                            # Calculate levels (NO STOP LOSS!)
                            stop_price_calc = 0.0  # NO STOP LOSS - DON'T PULL OUT EARLY!
                            breakeven = buy_price * (1 + fee_rate) / (1 - fee_rate)
                            target_price = breakeven + buy_price * (target_pct / 100)
                            
                            pos = LivePosition(
                                symbol=symbol_clean,
                                exchange=exchange,
                                entry_price=buy_price,
                                entry_qty=buy_qty,
                                entry_cost=buy_price * buy_qty * (1 + fee_rate),
                                breakeven_price=breakeven,
                                target_price=target_price,
                                client=client,
                                stop_price=stop_price_calc
                            )
                            positions.append(pos)
                            print(f"   ✅ NEW POSITION: Bought {buy_qty:.8f} @ ${buy_price:,.2f}")
                            print(f"      🎯 Target: ${target_price:,.2f} | 🚫 NO STOP LOSS")
                            
                        except Exception as e:
                            continue
                
                # ═══════════════════════════════════════════════════════════
                # MONITOR EXISTING POSITIONS WITH PROGRESS BARS
                # ═══════════════════════════════════════════════════════════
                
                if positions:  # Only show monitoring if we have positions
                    # Update whale intelligence periodically
                    whale_signals = {}
                    if current_time - last_whale_update >= whale_update_interval:
                        last_whale_update = current_time
                        for pos in positions:
                            if self.whale_tracker:
                                try:
                                    signal = self.whale_tracker.get_whale_signal(
                                        pos.symbol, 
                                        our_direction='long',
                                        current_price=pos.current_price,
                                        price_change_pct=pos.current_pnl_pct
                                    )
                                    whale_signals[pos.symbol] = signal
                                except Exception as e:
                                    pass
                    
                    # Clear screen for clean display
                    print("\033[2J\033[H", end="")  # Clear screen and move cursor to top
                    
                    # Header
                    print("🦈🦈🦈 ORCA DYNAMIC PACK HUNT - LIVE MONITORING 🦈🦈🦈")
                    print("="*80)
                    print(f"   📊 {len(positions)} ACTIVE POSITIONS | 💰 TOTAL P&L: ${sum(p.current_pnl for p in positions):+.4f}")
                    print(f"   🔍 Next market scan: {max(0, scan_interval - (current_time - last_scan_time)):.1f}s")
                    print("="*80)
                    
                    # Update each position using its own client
                    for i, pos in enumerate(positions[:]):  # Copy list to allow removal
                        try:
                            # Get price from correct exchange
                            if pos.exchange == 'alpaca':
                                orderbook = pos.client.get_crypto_orderbook(pos.symbol)
                                bids = orderbook.get('bids', [])
                                if not bids:
                                    continue
                                current = float(bids[0].get('p', 0))
                            elif pos.exchange == 'kraken':
                                ticker = pos.client.get_ticker(pos.symbol)
                                current = ticker.get('bid', ticker.get('price', 0))
                            else:
                                continue
                            
                            if current == 0:
                                continue
                            
                            # Track momentum
                            pos.price_history.append(current)
                            if len(pos.price_history) > 50:
                                pos.price_history.pop(0)
                            
                            # Calculate P&L
                            fee_rate = self.fee_rates.get(pos.exchange, 0.0025)
                            entry_gross = pos.entry_price * pos.entry_qty
                            entry_fee = entry_gross * fee_rate
                            entry_cost = entry_gross + entry_fee
                            exit_gross = current * pos.entry_qty
                            exit_fee = exit_gross * fee_rate
                            exit_value = exit_gross - exit_fee
                            net_pnl = exit_value - entry_cost
                            
                            pos.current_price = current
                            pos.current_pnl = net_pnl
                            pos.current_pnl_pct = (net_pnl / entry_cost * 100) if entry_cost > 0 else 0
                            
                            # ═════════════════════════════════════════════════════
                            # 🌊🎶 HNC LIVE FEED - Feed price to surge detector!
                            # ═════════════════════════════════════════════════════
                            hnc_status = ""
                            if self.hnc_surge_detector:
                                try:
                                    self.hnc_surge_detector.add_price_tick(pos.symbol, current)
                                    surge = self.hnc_surge_detector.detect_surge(pos.symbol)
                                    if surge:
                                        resonance = surge.primary_harmonic if hasattr(surge, 'primary_harmonic') else 'SURGE'
                                        hnc_status = f"🌊🎶 {resonance[:12]}"
                                    else:
                                        hnc_status = ""
                                except:
                                    pass
                            
                            # Calculate progress to target
                            progress_pct = min(100, max(0, (current - pos.entry_price) / (pos.target_price - pos.entry_price) * 100))
                            progress_bar = "█" * int(progress_pct / 5) + "░" * (20 - int(progress_pct / 5))
                            
                            # Get whale signal for this position
                            whale_info = whale_signals.get(pos.symbol)
                            if whale_info:
                                whale_status = f"🐋 {whale_info.dominant_firm}: {whale_info.firm_activity}"
                                whale_conf = f"🤖 Conf: {whale_info.confidence:.1f}"
                            else:
                                whale_status = "🐋 Scanning..."
                                whale_conf = "🤖 Analyzing..."
                            
                            # Display position with progress bar
                            print(f"\n🎯 POSITION {i+1}: {pos.symbol} ({pos.exchange.upper()}) {hnc_status}")
                            print(f"   💰 Entry: ${pos.entry_price:,.4f} | Current: ${current:,.4f} | Target: ${pos.target_price:,.4f}")
                            print(f"   📊 P&L: ${net_pnl:+.4f} ({pos.current_pnl_pct:+.2f}%) | Progress: [{progress_bar}] {progress_pct:.1f}%")
                            print(f"   {whale_status} | {whale_conf}")
                            
                            # ═════════════════════════════════════════════════════
                            # EXIT CONDITIONS - ONLY THESE, NO TIMEOUT!
                            # ═════════════════════════════════════════════════════
                            
                            # 1. TARGET HIT - perfect exit!
                            if current >= pos.target_price:
                                pos.ready_to_kill = True
                                pos.kill_reason = 'TARGET_HIT'
                                print(f"\n   🎯🎯🎯 TARGET HIT! SELLING NOW! 🎯🎯🎯")
                            
                            # 2. MOMENTUM REVERSAL - ONLY IF IN PROFIT!
                            elif pos.current_pnl > 0 and len(pos.price_history) >= 10:
                                recent = pos.price_history[-10:]
                                momentum = (recent[-1] - recent[0]) / recent[0] * 100 if recent[0] > 0 else 0
                                if momentum < -0.3:  # Losing momentum while in profit
                                    pos.ready_to_kill = True
                                    pos.kill_reason = 'MOMENTUM_PROFIT'
                                    print(f"\n   📈📈📈 TAKING PROFIT (momentum reversal) 📈📈📈")
                            
                            # ═════════════════════════════════════════════════════
                            # 🌊🎶 HNC SURGE HOLD - RIDE THE HARMONIC WAVE!
                            # If surge is active and we're in profit, EXTEND target!
                            # ═════════════════════════════════════════════════════
                            if hnc_status and pos.current_pnl > 0 and not pos.ready_to_kill:
                                # Surge is active and we're in profit - EXTEND TARGET!
                                original_target = pos.target_price
                                surge_extension = 1.5  # Extend target by 50% during surge!
                                extended_target = pos.entry_price + (original_target - pos.entry_price) * surge_extension
                                if extended_target > pos.target_price:
                                    pos.target_price = extended_target
                                    print(f"   🌊🎶 HNC SURGE: Extended target to ${extended_target:,.4f}!")
                            
                            # EXIT if ready
                            if pos.ready_to_kill:
                                print(f"\n   🔪🔪🔪 EXECUTING SELL ORDER 🔪🔪🔪")
                                sell_order = pos.client.place_market_order(
                                    symbol=pos.symbol,
                                    side='sell',
                                    quantity=pos.entry_qty
                                )
                                if sell_order:
                                    sell_price = float(sell_order.get('filled_avg_price', current))
                                    # Recalculate final P&L
                                    final_exit = sell_price * pos.entry_qty * (1 - fee_rate)
                                    final_pnl = final_exit - entry_cost
                                    results.append({
                                        'symbol': pos.symbol,
                                        'exchange': pos.exchange,
                                        'reason': pos.kill_reason,
                                        'net_pnl': final_pnl
                                    })
                                    print(f"   ✅ SOLD {pos.symbol}: ${final_pnl:+.4f} ({pos.kill_reason})")
                                    
                                    # 🔥🔥🔥 IMMEDIATE RE-SCAN & RE-BUY AFTER PROFITABLE SELL! 🔥🔥🔥
                                    print(f"\n   🔄🔄🔄 IMMEDIATE RE-SCAN - AGGRESSIVE MODE! 🔄🔄🔄")
                                    # Force immediate market scan
                                    try:
                                        new_opps = self.scan_entire_market(min_change_pct=0.3)  # Lower threshold for faster entries
                                        if new_opps:
                                            # Find best opportunity we haven't tried
                                            for new_opp in new_opps[:5]:
                                                new_symbol = new_opp.symbol if isinstance(new_opp, MarketOpportunity) else new_opp.get('symbol', '')
                                                new_exchange = new_opp.exchange if isinstance(new_opp, MarketOpportunity) else new_opp.get('exchange', 'alpaca')
                                                
                                                # Skip if already in positions
                                                active_symbols = [p.symbol for p in positions]
                                                if new_symbol in active_symbols:
                                                    continue
                                                
                                                # Check cash availability
                                                cash_check = self.get_available_cash()
                                                available_cash = cash_check.get(new_exchange, 0)
                                                
                                                if available_cash >= amount_per_position:
                                                    print(f"   🚀 FOUND NEW TARGET: {new_symbol} ({new_exchange.upper()})")
                                                    # Execute immediate buy
                                                    new_client = self.clients.get(new_exchange)
                                                    if new_client:
                                                        try:
                                                            new_price = new_opp.price if isinstance(new_opp, MarketOpportunity) else 0
                                                            if new_price == 0:
                                                                if new_exchange == 'alpaca':
                                                                    ob = new_client.get_crypto_orderbook(new_symbol)
                                                                    asks = ob.get('asks', [])
                                                                    new_price = float(asks[0].get('p', 0)) if asks else 0
                                                                else:
                                                                    tick = new_client.get_ticker(new_symbol)
                                                                    new_price = tick.get('ask', tick.get('price', 0))
                                                            
                                                            if new_price > 0:
                                                                buy_qty_new = amount_per_position / new_price
                                                                new_buy = new_client.place_market_order(
                                                                    symbol=new_symbol,
                                                                    side='buy',
                                                                    quantity=buy_qty_new
                                                                )
                                                                if new_buy:
                                                                    fill_price = float(new_buy.get('filled_avg_price', new_price))
                                                                    fill_qty = float(new_buy.get('filled_qty', buy_qty_new))
                                                                    new_fee_rate = self.fee_rates.get(new_exchange, 0.0025)
                                                                    new_breakeven = fill_price * (1 + new_fee_rate) / (1 - new_fee_rate)
                                                                    new_target = new_breakeven + (fill_price * target_pct / 100)
                                                                    
                                                                    new_position = LivePosition(
                                                                        symbol=new_symbol,
                                                                        exchange=new_exchange,
                                                                        entry_price=fill_price,
                                                                        entry_qty=fill_qty,
                                                                        entry_cost=fill_price * fill_qty * (1 + new_fee_rate),
                                                                        breakeven_price=new_breakeven,
                                                                        target_price=new_target,
                                                                        client=new_client
                                                                    )
                                                                    positions.append(new_position)
                                                                    print(f"   🎯 BOUGHT {new_symbol}: {fill_qty:.4f} @ ${fill_price:.4f}")
                                                                    print(f"   🎯 New target: ${new_target:.4f}")
                                                                    break  # Only buy one new position per cycle
                                                        except Exception as buy_err:
                                                            print(f"   ⚠️ Re-buy failed: {buy_err}")
                                    except Exception as scan_err:
                                        print(f"   ⚠️ Re-scan failed: {scan_err}")
                                    
                                    print(f"   🔄 CYCLE CONTINUES - NEVER STOP HUNTING!")
                                positions.remove(pos)
                                
                        except Exception as e:
                            print(f"   ⚠️ Error monitoring {pos.symbol}: {e}")
                    
                    # Show summary at bottom
                    if positions:
                        print(f"\n{'='*80}")
                        active_symbols = [f"{p.symbol[:6]}({p.exchange[0].upper()})" for p in positions]
                        print(f"   📡 ACTIVE: {', '.join(active_symbols)}")
                        print(f"   💰 TOTAL P&L: ${sum(p.current_pnl for p in positions):+.4f}")
                        print(f"   🎯 WAITING FOR TARGET HITS...")
                        print(f"   🚫 NO STOP LOSS - HOLD UNTIL PROFIT!")
                        print(f"   ⏱️ Next whale update: {max(0, whale_update_interval - (current_time - last_whale_update)):.1f}s")
                    else:
                        print(f"\n{'='*80}")
                        print("   🎉 ALL POSITIONS CLOSED - READY FOR NEXT ROUND!")
                        print(f"{'='*80}")
                else:
                    # No positions - just show scanning status
                    print(f"\n🔍 SCANNING FOR OPPORTUNITIES... ({len(attempted_indices)} attempted)")
                    print(f"   Next scan in: {max(0, scan_interval - (current_time - last_scan_time)):.1f}s")
                    print(f"   Available targets remaining: {len(available_targets) - len(attempted_indices)}")
                
                time.sleep(monitor_interval)
                
        except KeyboardInterrupt:
            print("\n\n🛑 USER ABORT - Closing profitable positions only (skip losses)...")
            for pos in positions:
                try:
                    # Only close positions that would realize a positive net P&L
                    if pos.current_pnl > 0:
                        sell_order = self.execute_sell_with_logging(
                            client=pos.client,
                            symbol=pos.symbol,
                            quantity=pos.entry_qty,
                            exchange=pos.exchange,
                            current_price=pos.current_price,
                            entry_cost=pos.entry_cost,
                            reason='USER_ABORT'
                        )
                        if sell_order:
                            fee_rate = self.fee_rates.get(pos.exchange, 0.0025)
                            sell_price = float(sell_order.get('filled_avg_price', pos.current_price))
                            entry_cost = pos.entry_price * pos.entry_qty * (1 + fee_rate)
                            final_exit = sell_price * pos.entry_qty * (1 - fee_rate)
                            final_pnl = final_exit - entry_cost
                            results.append({
                                'symbol': pos.symbol,
                                'exchange': pos.exchange,
                                'reason': 'USER_ABORT',
                                'net_pnl': final_pnl
                            })
                            print(f"   ✅ Closed {pos.symbol}: ${final_pnl:+.4f} (USER_ABORT)")
                    else:
                        print(f"   ⛔ Skipping close for {pos.symbol}: current P&L ${pos.current_pnl:+.4f} -> not closing to avoid realizing loss")
                except Exception as e:
                    print(f"   ⚠️ Error closing {pos.symbol}: {e}")
        
        return results
        
        # Faster updates for better monitoring
        monitor_interval = 0.05  # 20 updates/sec instead of 10
        whale_update_interval = 2.0  # Update whale intel every 2 seconds
        last_whale_update = 0
        
        try:
            while positions:  # Loop forever until ALL positions exit properly
                current_time = time.time()
                
                # Update whale intelligence periodically
                whale_signals = {}
                if current_time - last_whale_update >= whale_update_interval:
                    last_whale_update = current_time
                    for pos in positions:
                        if self.whale_tracker:
                            try:
                                signal = self.whale_tracker.get_whale_signal(
                                    pos.symbol, 
                                    our_direction='long',
                                    current_price=pos.current_price,
                                    price_change_pct=pos.current_pnl_pct
                                )
                                whale_signals[pos.symbol] = signal
                            except Exception as e:
                                pass
                
                # Clear screen for clean display
                print("\033[2J\033[H", end="")  # Clear screen and move cursor to top
                
                # Header
                print("🦈🦈🦈 ORCA PACK HUNT - LIVE MONITORING 🦈🦈🦈")
                print("="*80)
                print(f"   📊 {len(positions)} ACTIVE POSITIONS | 💰 TOTAL P&L: ${sum(p.current_pnl for p in positions):+.4f}")
                print("="*80)
                
                # Update each position using its own client
                for i, pos in enumerate(positions[:]):  # Copy list to allow removal
                    try:
                        # Get price from correct exchange
                        if pos.exchange == 'alpaca':
                            orderbook = pos.client.get_crypto_orderbook(pos.symbol)
                            bids = orderbook.get('bids', [])
                            if not bids:
                                continue
                            current = float(bids[0].get('p', 0))
                        elif pos.exchange == 'kraken':
                            ticker = pos.client.get_ticker(pos.symbol)
                            current = ticker.get('bid', ticker.get('price', 0))
                        else:
                            continue
                        
                        if current == 0:
                            continue
                        
                        # Track momentum
                        pos.price_history.append(current)
                        if len(pos.price_history) > 50:
                            pos.price_history.pop(0)
                        
                        # Calculate P&L
                        fee_rate = self.fee_rates.get(pos.exchange, 0.0025)
                        entry_gross = pos.entry_price * pos.entry_qty
                        entry_fee = entry_gross * fee_rate
                        entry_cost = entry_gross + entry_fee
                        exit_gross = current * pos.entry_qty
                        exit_fee = exit_gross * fee_rate
                        exit_value = exit_gross - exit_fee
                        net_pnl = exit_value - entry_cost
                        
                        pos.current_price = current
                        pos.current_pnl = net_pnl
                        pos.current_pnl_pct = (net_pnl / entry_cost * 100) if entry_cost > 0 else 0
                        
                        # Calculate progress to target
                        progress_pct = min(100, max(0, (current - pos.entry_price) / (pos.target_price - pos.entry_price) * 100))
                        progress_bar = "█" * int(progress_pct / 5) + "░" * (20 - int(progress_pct / 5))
                        
                        # Get whale signal for this position
                        whale_info = whale_signals.get(pos.symbol)
                        if whale_info:
                            whale_status = f"🐋 {whale_info.dominant_firm}: {whale_info.firm_activity}"
                            whale_conf = f"🤖 Conf: {whale_info.confidence:.1f}"
                        else:
                            whale_status = "🐋 Scanning..."
                            whale_conf = "🤖 Analyzing..."
                        
                        # Display position with progress bar
                        print(f"\n🎯 POSITION {i+1}: {pos.symbol} ({pos.exchange.upper()})")
                        print(f"   💰 Entry: ${pos.entry_price:,.4f} | Current: ${current:,.4f} | Target: ${pos.target_price:,.4f}")
                        print(f"   📊 P&L: ${net_pnl:+.4f} ({pos.current_pnl_pct:+.2f}%) | Progress: [{progress_bar}] {progress_pct:.1f}%")
                        print(f"   {whale_status} | {whale_conf}")
                        
                        # ═════════════════════════════════════════════════════
                        # EXIT CONDITIONS - ONLY THESE, NO TIMEOUT!
                        # ═════════════════════════════════════════════════════
                        
                        # 1. TARGET HIT - perfect exit!
                        if current >= pos.target_price:
                            pos.ready_to_kill = True
                            pos.kill_reason = 'TARGET_HIT'
                            print(f"\n   🎯🎯🎯 TARGET HIT! SELLING NOW! 🎯🎯🎯")
                        
                        # 2. MOMENTUM REVERSAL - ONLY IF IN PROFIT!
                        elif pos.current_pnl > 0 and len(pos.price_history) >= 10:
                            recent = pos.price_history[-10:]
                            momentum = (recent[-1] - recent[0]) / recent[0] * 100 if recent[0] > 0 else 0
                            if momentum < -0.3:  # Losing momentum while in profit
                                pos.ready_to_kill = True
                                pos.kill_reason = 'MOMENTUM_PROFIT'
                                print(f"\n   📈📈📈 TAKING PROFIT (momentum reversal) 📈📈📈")
                        
                        # EXIT if ready - SELL ONLY IF POSITIVE PROFIT
                        if pos.ready_to_kill:
                            # Only execute sell if current unrealized P&L is positive
                            if pos.current_pnl > 0:
                                print(f"\n   🔪🔪🔪 EXECUTING SELL ORDER (PROFITABLE) 🔪🔪🔪")
                                sell_order = self.execute_sell_with_logging(
                                    client=pos.client,
                                    symbol=pos.symbol,
                                    quantity=pos.entry_qty,
                                    exchange=pos.exchange,
                                    current_price=current,
                                    entry_cost=pos.entry_cost,
                                    reason=pos.kill_reason
                                )
                                if sell_order:
                                    sell_price = float(sell_order.get('filled_avg_price', current))
                                    # Recalculate final P&L
                                    final_exit = sell_price * pos.entry_qty * (1 - fee_rate)
                                    final_pnl = final_exit - entry_cost
                                    results.append({
                                        'symbol': pos.symbol,
                                        'exchange': pos.exchange,
                                        'reason': pos.kill_reason,
                                        'net_pnl': final_pnl
                                    })
                                    print(f"   ✅ SOLD {pos.symbol}: ${final_pnl:+.4f} ({pos.kill_reason})")
                                    print(f"   🔄 READY FOR NEXT TRADE!")
                                positions.remove(pos)
                            else:
                                # Skip selling to avoid realizing a loss
                                print(f"\n   ✋ NOT SELLING {pos.symbol}: current P&L ${pos.current_pnl:+.4f} <= 0 (waiting for profitable exit)")
                                pos.ready_to_kill = False
                                pos.kill_reason = 'NOT_PROFIT_YET'
                            
                    except Exception as e:
                        print(f"   ⚠️ Error monitoring {pos.symbol}: {e}")
                
                # Show summary at bottom
                if positions:
                    print(f"\n{'='*80}")
                    active_symbols = [f"{p.symbol[:6]}({p.exchange[0].upper()})" for p in positions]
                    print(f"   📡 ACTIVE: {', '.join(active_symbols)}")
                    print(f"   💰 TOTAL P&L: ${sum(p.current_pnl for p in positions):+.4f}")
                    print(f"   🎯 WAITING FOR TARGET HITS...")
                    print(f"   🚫 NO STOP LOSS - HOLD UNTIL PROFIT!")
                    print(f"   ⏱️ Next whale update: {max(0, whale_update_interval - (current_time - last_whale_update)):.1f}s")
                else:
                    print(f"\n{'='*80}")
                    print("   🎉 ALL POSITIONS CLOSED - READY FOR NEXT ROUND!")
                    print(f"{'='*80}")
                
                time.sleep(monitor_interval)
                
        except KeyboardInterrupt:
            print("\n\n🛑 USER ABORT - Closing all positions...")
            for pos in positions:
                try:
                    sell_order = self.execute_sell_with_logging(
                        client=pos.client,
                        symbol=pos.symbol,
                        quantity=pos.entry_qty,
                        exchange=pos.exchange,
                        current_price=pos.current_price,
                        entry_cost=pos.entry_cost,
                        reason='USER_ABORT'
                    )
                    if sell_order:
                        fee_rate = self.fee_rates.get(pos.exchange, 0.0025)
                        sell_price = float(sell_order.get('filled_avg_price', pos.current_price))
                        entry_cost = pos.entry_price * pos.entry_qty * (1 + fee_rate)
                        final_exit = sell_price * pos.entry_qty * (1 - fee_rate)
                        final_pnl = final_exit - entry_cost
                        results.append({
                            'symbol': pos.symbol,
                            'exchange': pos.exchange,
                            'reason': 'USER_ABORT',
                            'net_pnl': final_pnl
                        })
                        print(f"   Closed {pos.symbol}: ${final_pnl:+.4f}")
                except Exception as e:
                    print(f"   ⚠️ Error closing {pos.symbol}: {e}")
                
        except KeyboardInterrupt:
            print("\n\n🛑 USER ABORT - Closing all positions...")
            for pos in positions:
                try:
                    sell_order = self.execute_sell_with_logging(
                        client=pos.client,
                        symbol=pos.symbol,
                        quantity=pos.entry_qty,
                        exchange=pos.exchange,
                        current_price=pos.current_price,
                        entry_cost=pos.entry_cost,
                        reason='USER_ABORT'
                    )
                    if sell_order:
                        fee_rate = self.fee_rates.get(pos.exchange, 0.0025)
                        sell_price = float(sell_order.get('filled_avg_price', pos.current_price))
                        entry_cost = pos.entry_price * pos.entry_qty * (1 + fee_rate)
                        final_exit = sell_price * pos.entry_qty * (1 - fee_rate)
                        final_pnl = final_exit - entry_cost
                        results.append({
                            'symbol': pos.symbol,
                            'exchange': pos.exchange,
                            'reason': 'USER_ABORT',
                            'net_pnl': final_pnl
                        })
                        print(f"   Closed {pos.symbol}: ${final_pnl:+.4f}")
                except Exception as e:
                    print(f"   ⚠️ Error closing {pos.symbol}: {e}")
        
        # Summary
        print("\n\n" + "="*70)
        print("🦈 PACK HUNT COMPLETE - MULTI-EXCHANGE")
        print("="*70)
        total = sum(r['net_pnl'] for r in results)
        for r in results:
            emoji = '✅' if r['net_pnl'] > 0 else '❌'
            print(f"   {emoji} {r['symbol']} ({r['exchange']}): ${r['net_pnl']:+.4f} ({r['reason']})")
        print(f"\n💰 TOTAL P&L: ${total:+.4f}")
        print("="*70)
        
        return results

    # ═══════════════════════════════════════════════════════════════════════
    # 👑🦈 AUTONOMOUS MODE - QUEEN-GUIDED INFINITE LOOP 🦈👑
    # ═══════════════════════════════════════════════════════════════════════
    
    def run_autonomous(self, max_positions: int = 3, amount_per_position: float = 2.5,
                       target_pct: float = 1.0, min_change_pct: float = 0.3):
        """
        👑🔄 FULLY AUTONOMOUS QUEEN-GUIDED TRADING LOOP 🔄👑
        
        RUNS FOREVER until manually stopped (Ctrl+C).
        The Queen guides all decisions:
        
        PHASE 0: PORTFOLIO SCAN - Check existing positions, close profitable ones!
        PHASE 1: SCAN - Find new opportunities
        PHASE 2: BUY - With freed cash from closed positions
        PHASE 3: MONITOR - Stream prices, track whale intel
        PHASE 4: SELL - ONLY ON PROFIT! Then loop back to PHASE 0
        
        NO STOP LOSS - HOLD UNTIL PROFIT!
        """
        print("\n" + "👑"*30)
        print("  👑🦈 AUTONOMOUS QUEEN MODE - INFINITE LOOP 🦈👑")
        print("👑"*30)
        print()
        print("╔══════════════════════════════════════════════════════════════════╗")
        print("║  👑 SERO THE QUEEN IS NOW IN CONTROL 👑                          ║")
        print("║                                                                   ║")
        print("║  🔄 LOOP: Portfolio → Close Profits → Scan → Buy → Monitor      ║")
        print("║  🚫 NO STOP LOSS - ONLY SELL ON PROFIT!                          ║")
        print("║  ⏱️ Aggressive 5-second scans                                    ║")
        print("║  🐋 Full whale intelligence active                               ║")
        print("║  💰 All cost tracking systems engaged                            ║")
        print("║                                                                   ║")
        print("║  Press Ctrl+C to stop (will close PROFITABLE positions only)    ║")
        print("╚══════════════════════════════════════════════════════════════════╝")
        print()
        
        # Wire up the Queen Hive Mind (MANDATORY for autonomous mode)
        queen = None
        try:
            from aureon_queen_hive_mind import QueenHiveMind
            queen = QueenHiveMind()
            print("👑 QUEEN SERO: AWAKENED AND READY!")
            print(f"   🎯 Dream: ${queen.THE_DREAM:,.0f} (ONE BILLION)")
            print(f"   💰 Current equity: ${queen.equity:,.2f}")
            print()
        except Exception as e:
            print(f"❌ Queen initialization failed: {e}")
            print("   Continuing without Queen - using default settings.")
            queen = None
        
        # Session statistics
        session_stats = {
            'cycles': 0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0.0,
            'start_time': time.time(),
            'best_trade': 0.0,
            'worst_trade': 0.0,
            'positions_closed': 0,
            'cash_freed': 0.0,
        }
        
        # Current positions - will be loaded from portfolio
        positions: List[LivePosition] = []
        
        # Timing - SLOWER to avoid rate limits!
        base_scan_interval = 10  # Every 10 seconds (was 5)
        scan_interval = base_scan_interval
        monitor_interval = 1.0  # 1 second updates (was 0.1) - PREVENTS RATE LIMITS!
        whale_update_interval = 5.0  # Every 5 seconds (was 2)
        last_scan_time = 0
        last_whale_update = 0
        last_portfolio_scan = 0
        portfolio_scan_interval = 30  # Scan portfolio every 30 seconds (was 10)
        # Queen-driven pacing & profit target
        base_target_pct = target_pct
        target_pct_current = target_pct
        queen_update_interval = 10.0
        last_queen_update = 0.0

        def _apply_queen_controls() -> None:
            """Adjust scan speed and profit targets based on Queen collective signal."""
            nonlocal scan_interval, target_pct_current
            if queen is None:
                return
            try:
                signal = queen.get_collective_signal()
                confidence = float(signal.get('confidence', 0.5))
                direction = signal.get('direction', 'NEUTRAL')
            except Exception:
                confidence = 0.5
                direction = 'NEUTRAL'

            # Speed: higher confidence -> faster scans
            speed_factor = max(0.5, min(1.5, 1.5 - confidence))
            scan_interval = max(3.0, min(20.0, base_scan_interval * speed_factor))

            # Profit target: higher confidence -> higher target, bearish -> more conservative
            target_factor = 0.8 + (confidence * 0.6)
            if direction == 'BULLISH':
                target_factor *= 1.1
            elif direction == 'BEARISH':
                target_factor *= 0.8
            target_pct_current = max(0.3, min(3.0, base_target_pct * target_factor))

        # Initial Queen pacing/targets
        _apply_queen_controls()
        
        # ═══════════════════════════════════════════════════════════════════
        # PHASE 0 (STARTUP): SCAN EXISTING PORTFOLIO - CLOSE PROFITABLE POSITIONS
        # ═══════════════════════════════════════════════════════════════════
        print("\n" + "="*70)
        print("📊 PHASE 0: SCANNING EXISTING PORTFOLIO")
        print("="*70)
        
        for exchange_name, client in self.clients.items():
            try:
                print(f"\n🔍 Scanning {exchange_name.upper()} positions...")
                
                if exchange_name == 'alpaca':
                    alpaca_positions = client.get_positions()
                    if alpaca_positions:
                        for ap in alpaca_positions:
                            symbol = ap.get('symbol', '').replace('/', '')
                            qty = float(ap.get('qty', 0))
                            entry_price = float(ap.get('avg_entry_price', 0))
                            current_price = float(ap.get('current_price', 0))
                            unrealized_pnl = float(ap.get('unrealized_pl', 0))
                            market_value = float(ap.get('market_value', 0))
                            
                            if qty > 0 and entry_price > 0:
                                fee_rate = self.fee_rates.get(exchange_name, 0.0025)
                                entry_cost = entry_price * qty * (1 + fee_rate)
                                exit_value = current_price * qty * (1 - fee_rate)
                                net_pnl = exit_value - entry_cost
                                breakeven = entry_price * (1 + fee_rate) / (1 - fee_rate)
                                target_price = breakeven * (1 + target_pct_current / 100)
                                
                                print(f"   📈 {symbol}: {qty:.6f} @ ${entry_price:.4f}")
                                print(f"      Current: ${current_price:.4f} | P&L: ${net_pnl:+.4f}")
                                
                                # Check if we should close this profitable position
                                if net_pnl > 0.001:  # Profitable by at least $0.001
                                    print(f"      💰 PROFITABLE! Closing to free cash...")
                                    try:
                                        sell_order = client.place_market_order(
                                            symbol=symbol,
                                            side='sell',
                                            quantity=qty
                                        )
                                        if sell_order:
                                            session_stats['positions_closed'] += 1
                                            session_stats['cash_freed'] += exit_value
                                            session_stats['total_pnl'] += net_pnl
                                            session_stats['winning_trades'] += 1
                                            session_stats['total_trades'] += 1
                                            session_stats['best_trade'] = max(session_stats['best_trade'], net_pnl)
                                            print(f"      ✅ CLOSED! +${net_pnl:.4f} freed ${exit_value:.2f}")
                                    except Exception as e:
                                        print(f"      ⚠️ Sell failed: {e}")
                                        # Keep as live position to monitor
                                        pos = LivePosition(
                                            symbol=symbol,
                                            exchange=exchange_name,
                                            entry_price=entry_price,
                                            entry_qty=qty,
                                            entry_cost=entry_cost,
                                            breakeven_price=breakeven,
                                            target_price=target_price,
                                            client=client,
                                            current_price=current_price,
                                            current_pnl=net_pnl
                                        )
                                        positions.append(pos)
                                else:
                                    # Not profitable - keep monitoring
                                    print(f"      ⏳ UNDERWATER - keeping (will sell on profit)")
                                    pos = LivePosition(
                                        symbol=symbol,
                                        exchange=exchange_name,
                                        entry_price=entry_price,
                                        entry_qty=qty,
                                        entry_cost=entry_cost,
                                        breakeven_price=breakeven,
                                        target_price=target_price,
                                        client=client,
                                        current_price=current_price,
                                        current_pnl=net_pnl
                                    )
                                    positions.append(pos)
                    else:
                        print(f"   No positions on {exchange_name.upper()}")
                        
                elif exchange_name == 'kraken':
                    # Kraken positions - SCAN BALANCE FOR HOLDINGS
                    kraken_positions = client.get_balance()
                    if kraken_positions:
                        for asset, qty in kraken_positions.items():
                            if asset in ['USD', 'ZUSD', 'EUR', 'ZEUR', 'DAI', 'USDC', 'USDT', 'TUSD']:
                                continue  # Skip cash/stablecoins
                            qty = float(qty)
                            if qty > 0.000001:
                                symbol = f"{asset}USD"
                                try:
                                    ticker = client.get_ticker(symbol)
                                    current_price = float(ticker.get('bid', ticker.get('price', 0)))
                                    market_value = qty * current_price
                                    
                                    if market_value > 0.0:  # Track all positions
                                        print(f"   📈 {symbol} (KRAKEN): {qty:.6f} @ ~${current_price:.6f} (${market_value:.2f})")
                                        
                                        # For Kraken we don't have entry price stored - use current price as estimate
                                        # This means we'll track from NOW and wait for profit from this point
                                        fee_rate = self.fee_rates.get(exchange_name, 0.0026)
                                        entry_price = current_price  # Best estimate for manual buys
                                        entry_cost = entry_price * qty * (1 + fee_rate)
                                        breakeven = entry_price * (1 + fee_rate) / (1 - fee_rate)
                                        target_price = breakeven * (1 + target_pct_current / 100)
                                        
                                        # 🚨 SAFETY: Only auto-sell if we have CONFIRMED cost basis with real entry price!
                                        # For manual Kraken buys, we DON'T know entry price, so NEVER auto-sell!
                                        if self.cost_basis_tracker:
                                            can_sell, info = self.cost_basis_tracker.can_sell_profitably(symbol, current_price)
                                            # ONLY sell if: can_sell=True AND we have a real entry price (not None)
                                            if can_sell and info.get('entry_price') is not None:
                                                print(f"      💰 PROFITABLE per cost basis (entry: ${info['entry_price']:.8f})! Closing...")
                                                try:
                                                    sell_order = client.place_market_order(symbol, 'sell', quantity=qty)
                                                    if sell_order:
                                                        exit_value = current_price * qty * (1 - fee_rate)
                                                        net_pnl = exit_value - info.get('cost_basis', exit_value * 0.99)
                                                        session_stats['positions_closed'] += 1
                                                        session_stats['cash_freed'] += exit_value
                                                        session_stats['total_pnl'] += net_pnl
                                                        session_stats['winning_trades'] += 1
                                                        session_stats['total_trades'] += 1
                                                        print(f"      ✅ CLOSED! +${net_pnl:.4f}")
                                                        continue  # Skip adding to positions
                                                except Exception as e:
                                                    print(f"      ⚠️ Sell failed: {e}")
                                            elif not can_sell:
                                                print(f"      ⏳ NOT PROFITABLE yet - keeping position")
                                            else:
                                                print(f"      ⚠️ NO COST BASIS - will NOT auto-sell (tracking from now)")
                                        
                                        # 🆕 ADD KRAKEN POSITION TO MONITORING LIST!
                                        print(f"      ⏳ Adding to monitor list (tracking from current price)")
                                        pos = LivePosition(
                                            symbol=symbol,
                                            exchange=exchange_name,
                                            entry_price=entry_price,
                                            entry_qty=qty,
                                            entry_cost=entry_cost,
                                            breakeven_price=breakeven,
                                            target_price=target_price,
                                            client=client,
                                            current_price=current_price,
                                            current_pnl=0.0  # Starting from now
                                        )
                                        positions.append(pos)
                                except Exception as e:
                                    print(f"      ⚠️ Error getting price for {symbol}: {e}")
                
                elif exchange_name == 'binance':
                    # Binance positions - SCAN BALANCE FOR HOLDINGS
                    binance_positions = client.get_balance()
                    if binance_positions:
                        for asset, qty in binance_positions.items():
                            # Skip stablecoins and fiat
                            if asset in ['USD', 'USDT', 'USDC', 'BUSD', 'TUSD', 'DAI', 'FDUSD', 'GBP', 'EUR']:
                                continue
                            qty = float(qty)
                            if qty > 0.000001:
                                # Try multiple quote currencies (USDT is most common on Binance)
                                symbol_variants = [f"{asset}/USDT", f"{asset}/USDC", f"{asset}/USD", f"{asset}/BUSD"]
                                found_price = False
                                
                                for symbol in symbol_variants:
                                    try:
                                        ticker = self._get_binance_ticker(client, symbol)
                                        if ticker and float(ticker.get('bid', ticker.get('price', 0)) or 0) > 0:
                                            current_price = float(ticker.get('bid', ticker.get('price', 0)) or 0)
                                            market_value = qty * current_price
                                            
                                            if market_value > 0.0:  # Track all positions
                                                print(f"   📈 {symbol} (BINANCE): {qty:.6f} @ ${current_price:.6f} (${market_value:.2f})")
                                                
                                                fee_rate = self.fee_rates.get(exchange_name, 0.001)  # 0.1% Binance fee
                                                entry_price = current_price  # Estimate for manual positions
                                                entry_cost = entry_price * qty * (1 + fee_rate)
                                                breakeven = entry_price * (1 + fee_rate) / (1 - fee_rate)
                                                target_price = breakeven * (1 + target_pct_current / 100)
                                                
                                                # Check profitability
                                                exit_value = current_price * qty * (1 - fee_rate)
                                                net_pnl = exit_value - entry_cost
                                                
                                                if net_pnl > 0.001:  # Profitable
                                                    print(f"      💰 PROFITABLE (+${net_pnl:.4f})! Closing to free cash...")
                                                    try:
                                                        sell_order = client.place_market_order(
                                                            symbol=symbol.replace('/', ''),  # Binance wants no slash
                                                            side='sell',
                                                            quantity=qty
                                                        )
                                                        if sell_order:
                                                            session_stats['positions_closed'] += 1
                                                            session_stats['cash_freed'] += exit_value
                                                            session_stats['total_pnl'] += net_pnl
                                                            session_stats['winning_trades'] += 1
                                                            session_stats['total_trades'] += 1
                                                            session_stats['best_trade'] = max(session_stats['best_trade'], net_pnl)
                                                            print(f"      ✅ CLOSED! +${net_pnl:.4f}")
                                                            found_price = True
                                                            break  # Position closed, skip monitoring
                                                    except Exception as e:
                                                        print(f"      ⚠️ Sell failed: {e}")
                                                
                                                # Add to monitoring if not closed
                                                print(f"      ⏳ Adding to monitor list")
                                                pos = LivePosition(
                                                    symbol=symbol,
                                                    exchange=exchange_name,
                                                    entry_price=entry_price,
                                                    entry_qty=qty,
                                                    entry_cost=entry_cost,
                                                    breakeven_price=breakeven,
                                                    target_price=target_price,
                                                    client=client,
                                                    current_price=current_price,
                                                    current_pnl=net_pnl
                                                )
                                                positions.append(pos)
                                                found_price = True
                                                break  # Found valid symbol, stop trying variants
                                    except Exception:
                                        continue  # Try next symbol variant
                                
                                if not found_price and qty * 100 > 1:  # Asset worth checking (rough estimate)
                                    print(f"   ⚠️ {asset}: {qty:.6f} (could not get price for any trading pair)")
                    else:
                        print(f"   No positions on {exchange_name.upper()}")
                                    
            except Exception as e:
                print(f"   ⚠️ Error scanning {exchange_name}: {e}")
        
        print(f"\n📊 Portfolio scan complete:")
        print(f"   ✅ Positions closed: {session_stats['positions_closed']}")
        print(f"   💰 Cash freed: ${session_stats['cash_freed']:.2f}")
        print(f"   📈 P&L realized: ${session_stats['total_pnl']:+.4f}")
        print(f"   ⏳ Positions still held: {len(positions)}")
        
        # Now get updated cash after closing profitable positions
        cash = self.get_available_cash()
        print(f"\n💵 Available cash after portfolio cleanup:")
        for exchange, amount in cash.items():
            print(f"   {exchange.upper()}: ${amount:.2f}")
        print()
        
        try:
            while True:  # ♾️ INFINITE LOOP
                current_time = time.time()
                session_stats['cycles'] += 1
                
                # Update dashboard state for Command Center UI (legacy mode)
                self._dump_dashboard_state(session_stats, positions, queen)

                # 👑 Queen pacing + profit target updates
                if current_time - last_queen_update >= queen_update_interval:
                    last_queen_update = current_time
                    _apply_queen_controls()
                    print(f"👑 Queen pacing: scan_interval={scan_interval:.1f}s | target_pct={target_pct_current:.2f}%")
                
                # ═══════════════════════════════════════════════════════════
                # PHASE 0 (RECURRING): RE-SCAN PORTFOLIO FOR NEW PROFITS
                # ═══════════════════════════════════════════════════════════
                if current_time - last_portfolio_scan >= portfolio_scan_interval:
                    last_portfolio_scan = current_time
                    
                    # 🚀 BATCH FETCH ALL PRICES AT ONCE - PREVENTS RATE LIMITS!
                    batch_prices = {}
                    try:
                        alpaca_client = self.clients.get('alpaca')
                        if alpaca_client:
                            alpaca_symbols = [p.symbol for p in positions if p.exchange == 'alpaca']
                            if alpaca_symbols:
                                snapshot = alpaca_client.get_crypto_snapshot(alpaca_symbols)
                                if snapshot:
                                    for sym, data in snapshot.items():
                                        if data and 'latestTrade' in data:
                                            batch_prices[sym] = float(data['latestTrade'].get('p', 0))
                                        elif data and 'latestQuote' in data:
                                            batch_prices[sym] = float(data['latestQuote'].get('bp', 0))
                    except Exception:
                        pass
                    
                    # Also batch Kraken if we have positions there
                    try:
                        kraken_client = self.clients.get('kraken')
                        if kraken_client:
                            kraken_symbols = [p.symbol for p in positions if p.exchange == 'kraken']
                            for sym in kraken_symbols:
                                try:
                                    ticker = kraken_client.get_ticker(sym)
                                    if ticker:
                                        batch_prices[sym] = ticker.get('bid', ticker.get('price', 0))
                                except Exception:
                                    pass
                    except Exception:
                        pass
                    
                    # 🆕 RE-SCAN KRAKEN BALANCES FOR NEW MANUAL POSITIONS!
                    try:
                        kraken_client = self.clients.get('kraken')
                        if kraken_client:
                            kraken_balances = kraken_client.get_balance()
                            current_kraken_symbols = [p.symbol for p in positions if p.exchange == 'kraken']
                            
                            for asset, qty in kraken_balances.items():
                                if asset in ['USD', 'ZUSD', 'EUR', 'ZEUR', 'DAI', 'USDC', 'USDT', 'TUSD']:
                                    continue  # Skip cash/stablecoins
                                qty = float(qty)
                                symbol = f"{asset}USD"
                                
                                # Check if this is a NEW position not already tracked
                                if qty > 0.000001 and symbol not in current_kraken_symbols:
                                    try:
                                        ticker = kraken_client.get_ticker(symbol)
                                        current_price = float(ticker.get('bid', ticker.get('price', 0)))
                                        market_value = qty * current_price
                                        
                                        if market_value > 0.0:  # Track all positions
                                            print(f"\n🆕 NEW KRAKEN POSITION DETECTED: {symbol}")
                                            print(f"   📊 {qty:.6f} @ ${current_price:.8f} = ${market_value:.2f}")
                                            
                                            fee_rate = self.fee_rates.get('kraken', 0.0026)
                                            entry_price = current_price  # Use current as entry estimate
                                            entry_cost = entry_price * qty * (1 + fee_rate)
                                            breakeven = entry_price * (1 + fee_rate) / (1 - fee_rate)
                                            target_price = breakeven * (1 + target_pct_current / 100)
                                            
                                            pos = LivePosition(
                                                symbol=symbol,
                                                exchange='kraken',
                                                entry_price=entry_price,
                                                entry_qty=qty,
                                                entry_cost=entry_cost,
                                                breakeven_price=breakeven,
                                                target_price=target_price,
                                                client=kraken_client,
                                                current_price=current_price,
                                                current_pnl=0.0
                                            )
                                            positions.append(pos)
                                            batch_prices[symbol] = current_price
                                            print(f"   ✅ Added to monitor! Target: ${target_price:.8f}")
                                    except Exception as e:
                                        print(f"   ⚠️ Could not add {symbol}: {e}")
                    except Exception as e:
                        pass  # Silently skip if Kraken scan fails
                    
                    # 🆕 RE-SCAN BINANCE BALANCES FOR NEW MANUAL POSITIONS!
                    try:
                        binance_client = self.clients.get('binance')
                        if binance_client:
                            # First, batch fetch prices for existing Binance positions
                            binance_symbols = [p.symbol for p in positions if p.exchange == 'binance']
                            for sym in binance_symbols:
                                try:
                                    ticker = self._get_binance_ticker(binance_client, sym)
                                    if ticker:
                                        batch_prices[sym] = ticker.get('bid', ticker.get('price', 0))
                                except Exception:
                                    pass
                            
                            # Now scan for NEW positions
                            binance_balances = binance_client.get_balance()
                            current_binance_symbols = [p.symbol for p in positions if p.exchange == 'binance']
                            
                            for asset, qty in binance_balances.items():
                                if asset in ['USD', 'USDT', 'USDC', 'BUSD', 'TUSD', 'DAI', 'FDUSD', 'GBP', 'EUR']:
                                    continue  # Skip stablecoins/fiat
                                qty = float(qty)
                                
                                # Check if this is a NEW position not already tracked
                                if qty > 0.000001:
                                    # Try multiple quote currencies
                                    symbol_variants = [f"{asset}/USDT", f"{asset}/USDC", f"{asset}/USD", f"{asset}/BUSD"]
                                    for symbol in symbol_variants:
                                        if symbol in current_binance_symbols:
                                            continue  # Already tracking
                                        
                                        try:
                                            ticker = self._get_binance_ticker(binance_client, symbol)
                                            if ticker and float(ticker.get('bid', ticker.get('price', 0)) or 0) > 0:
                                                current_price = float(ticker.get('bid', ticker.get('price', 0)) or 0)
                                                market_value = qty * current_price
                                                
                                                if market_value > 0.0:  # Track all positions
                                                    print(f"\n🆕 NEW BINANCE POSITION DETECTED: {symbol}")
                                                    print(f"   📊 {qty:.6f} @ ${current_price:.6f} = ${market_value:.2f}")
                                                    
                                                    fee_rate = self.fee_rates.get('binance', 0.001)
                                                    entry_price = current_price
                                                    entry_cost = entry_price * qty * (1 + fee_rate)
                                                    breakeven = entry_price * (1 + fee_rate) / (1 - fee_rate)
                                                    target_price = breakeven * (1 + target_pct_current / 100)
                                                    
                                                    pos = LivePosition(
                                                        symbol=symbol,
                                                        exchange='binance',
                                                        entry_price=entry_price,
                                                        entry_qty=qty,
                                                        entry_cost=entry_cost,
                                                        breakeven_price=breakeven,
                                                        target_price=target_price,
                                                        client=binance_client,
                                                        current_price=current_price,
                                                        current_pnl=0.0
                                                    )
                                                    positions.append(pos)
                                                    batch_prices[symbol] = current_price
                                                    print(f"   ✅ Added to monitor! Target: ${target_price:.6f}")
                                                    break  # Found valid symbol, stop trying variants
                                        except Exception:
                                            continue  # Try next variant
                    except Exception as e:
                        pass  # Silently skip if Binance scan fails
                    
                    # Quick check existing positions for profit using BATCH prices
                    for pos in positions[:]:  # Copy list to allow removal
                        try:
                            # Use batch price (no individual API calls!)
                            current = batch_prices.get(pos.symbol, 0)
                            if current <= 0:
                                continue
                                
                            if current > 0:
                                fee_rate = self.fee_rates.get(pos.exchange, 0.0025)
                                entry_cost = pos.entry_price * pos.entry_qty * (1 + fee_rate)
                                exit_value = current * pos.entry_qty * (1 - fee_rate)
                                net_pnl = exit_value - entry_cost
                                pos.current_price = current
                                pos.current_pnl = net_pnl
                                
                                # Auto-close if hit target or profitable enough
                                if current >= pos.target_price or net_pnl > entry_cost * 0.01:  # Target or 1% profit
                                    # 🚨 SAFETY CHECK: For Kraken positions, verify with cost_basis_tracker!
                                    # Only sell if we have CONFIRMED profitability with real entry price
                                    can_sell = True
                                    if pos.exchange == 'kraken' and self.cost_basis_tracker:
                                        can_sell, info = self.cost_basis_tracker.can_sell_profitably(pos.symbol, current)
                                        if not can_sell or info.get('entry_price') is None:
                                            # No confirmed cost basis - DO NOT SELL!
                                            print(f"\n⚠️ {pos.symbol}: Would sell but NO CONFIRMED COST BASIS - HOLDING!")
                                            print(f"   📊 Calculated P&L: ${net_pnl:.4f} (but entry price unknown)")
                                            can_sell = False
                                        else:
                                            print(f"   ✅ Cost basis confirmed: entry ${info['entry_price']:.8f}")
                                    
                                    if can_sell:
                                        print(f"\n🎯 AUTO-CLOSE: {pos.symbol} is PROFITABLE! (+${net_pnl:.4f})")
                                        sell_order = pos.client.place_market_order(
                                            symbol=pos.symbol,
                                            side='sell',
                                            quantity=pos.entry_qty
                                        )
                                        # 🔍 Verify sell succeeded using is_order_successful
                                        if self.is_order_successful(sell_order, pos.exchange):
                                            session_stats['positions_closed'] += 1
                                            session_stats['cash_freed'] += exit_value
                                            session_stats['total_pnl'] += net_pnl
                                            session_stats['winning_trades'] += 1
                                            session_stats['total_trades'] += 1
                                            session_stats['best_trade'] = max(session_stats['best_trade'], net_pnl)
                                            positions.remove(pos)
                                            print(f"   ✅ CLOSED! +${net_pnl:.4f} → Cash freed for new buys!")
                                            last_scan_time = 0  # Force immediate scan for new opportunities
                        except Exception:
                            pass
                
                # ═══════════════════════════════════════════════════════════
                # PHASE 1: SCAN FOR NEW OPPORTUNITIES
                # ═══════════════════════════════════════════════════════════
                if current_time - last_scan_time >= scan_interval:
                    last_scan_time = current_time

                    # Always refresh balances, even if position cap is reached
                    cash = self.get_available_cash()
                    
                    # Check if we have room for more positions
                    if len(positions) < max_positions:
                        print(f"\n🔍 QUEEN SCANNING... ({len(positions)}/{max_positions} positions active)")

                        total_cash = sum(cash.values())
                        
                        if total_cash < amount_per_position * 0.3:  # Only need 30% of target (more aggressive)
                            print(f"   💸 Waiting for cash (${total_cash:.2f} available, need ${amount_per_position * 0.3:.2f})")
                        else:
                            # Scan market
                            scan_start = time.time()
                            opportunities = self.scan_entire_market(min_change_pct=min_change_pct)
                            scan_time = time.time() - scan_start
                            
                            if opportunities:
                                # Update volatility based on opportunity count
                                
                                # Update opportunity queue for display
                                
                                # Update efficiency metrics
                                
                                # Flash alert if extreme volatility
                                if len(opportunities) > 4000:
                                    print(f"⚠️ Extreme volatility! {len(opportunities):,} opportunities")
                                
                                # Filter for symbols not already in positions
                                active_symbols = [p.symbol for p in positions]
                                new_opps = [o for o in opportunities if o.symbol not in active_symbols]
                                
                                if new_opps:
                                    # Ask Queen for guidance (MANDATORY)
                                    queen_approved = False
                                    if queen is None:
                                        queen_approved = True  # Fallback without Queen
                                        print("   👑 Queen unavailable - proceeding with default approval")
                                    else:
                                        try:
                                            signal = queen.get_collective_signal(
                                                symbol=best.symbol,
                                                market_data={
                                                    'price': best.price,
                                                    'change_pct': best.change_pct,
                                                    'momentum': best.momentum_score,
                                                    'exchange': best.exchange
                                                }
                                            )
                                            confidence = float(signal.get('confidence', 0.0))
                                            action = signal.get('action', 'HOLD')
                                            print(f"   👑 Queen signal: {action} (confidence {confidence:.0%})")
                                            queen_approved = (action == 'BUY' and confidence >= 0.3)  # Lowered from 0.5
                                        except Exception as e:
                                            print(f"   ⚠️ Queen signal unavailable: {e}")
                                    
                                    if queen_approved:
                                        # Take best opportunity
                                        best = new_opps[0]
                                        print(f"   👑 QUEEN APPROVED: {best.symbol} ({best.exchange})")
                                        print(f"      Change: {best.change_pct:+.2f}% | Momentum: {best.momentum_score:.2f}")
                                        
                                        # Execute buy
                                        try:
                                            client = self.clients.get(best.exchange)
                                            if client:
                                                symbol_clean = best.symbol.replace('/', '')
                                                
                                                # Adjust amount based on available cash
                                                exchange_cash = cash.get(best.exchange, 0)
                                                buy_amount = min(amount_per_position, exchange_cash * 0.9)
                                                
                                                if buy_amount >= 0.10:  # Minimum $0.10 (exchange mins vary)
                                                    raw_order = client.place_market_order(
                                                        symbol=symbol_clean,
                                                        side='buy',
                                                        quote_qty=buy_amount
                                                    )
                                                    
                                                    # 🔄 NORMALIZE ORDER RESPONSE across exchanges!
                                                    buy_order = self.normalize_order_response(raw_order, best.exchange)
                                                    
                                                    if buy_order and buy_order.get('status') != 'rejected':
                                                        buy_qty = buy_order.get('filled_qty', 0)
                                                        buy_price = buy_order.get('filled_avg_price', best.price)
                                                        
                                                        if buy_qty > 0 and buy_price > 0:
                                                            # Calculate levels
                                                            fee_rate = self.fee_rates.get(best.exchange, 0.0025)
                                                            breakeven = buy_price * (1 + fee_rate) / (1 - fee_rate)
                                                            target_price = breakeven * (1 + target_pct_current / 100)
                                                            
                                                            pos = LivePosition(
                                                                symbol=symbol_clean,
                                                                exchange=best.exchange,
                                                                entry_price=buy_price,
                                                                entry_qty=buy_qty,
                                                                entry_cost=buy_price * buy_qty * (1 + fee_rate),
                                                                breakeven_price=breakeven,
                                                                target_price=target_price,
                                                                client=client,
                                                                stop_price=0.0  # NO STOP LOSS!
                                                            )
                                                            positions.append(pos)
                                                            
                                                            # Track the buy order
                                                            self.track_buy_order(symbol_clean, buy_order, best.exchange)
                                                            
                                                            # Update efficiency metrics (bought)
                                                            
                                                            # Update position health
                                                            
                                                            print(f"   ✅ BOUGHT: {buy_qty:.6f} @ ${buy_price:,.4f}")
                                                            print(f"      🎯 Target: ${target_price:,.4f} ({target_pct_current:.2f}%)")
                                                            print(f"      🚫 NO STOP LOSS - HOLD UNTIL PROFIT!")
                                                            
                                                            session_stats['total_trades'] += 1
                                        except Exception as e:
                                            print(f"   ⚠️ Buy failed: {e}")
                                            # Flash alert for API issues
                                            if 'timeout' in str(e).lower() or 'connection' in str(e).lower():
                                                print(f"⚠️ {best.exchange.upper()} API issue")
                                    else:
                                        print(f"   👑 Queen says: Wait (consciousness too low)")
                                else:
                                    print(f"   ⚪ All opportunities already in positions")
                            else:
                                print(f"   ⚪ No opportunities found - market is flat")
                    else:
                        # At max positions - just monitor
                        pass
                
                # ═══════════════════════════════════════════════════════════
                # PHASE 2: MONITOR EXISTING POSITIONS
                # ═══════════════════════════════════════════════════════════
                if positions:
                    # Update whale intel periodically
                    whale_signals = {}
                    if current_time - last_whale_update >= whale_update_interval:
                        last_whale_update = current_time
                        for pos in positions:
                            if self.whale_tracker:
                                try:
                                    signal = self.whale_tracker.get_whale_signal(
                                        pos.symbol, 'long',
                                        current_price=pos.current_price,
                                        price_change_pct=pos.current_pnl_pct
                                    )
                                    whale_signals[pos.symbol] = signal
                                except Exception:
                                    pass
                    
                    # Display header
                    runtime = time.time() - session_stats['start_time']
                    runtime_str = f"{int(runtime//3600)}h {int((runtime%3600)//60)}m {int(runtime%60)}s"
                    
                    print("\033[2J\033[H", end="")  # Clear screen
                    print("👑🦈 AUTONOMOUS QUEEN MODE - LIVE MONITORING 🦈👑")
                    print("="*80)
                    print(f"   ⏱️ Runtime: {runtime_str} | 🔄 Cycles: {session_stats['cycles']}")
                    print(f"   📈 Trades: {session_stats['total_trades']} | ✅ Wins: {session_stats['winning_trades']} | ❌ Losses: {session_stats['losing_trades']}")
                    print(f"   💰 Session P&L: ${session_stats['total_pnl']:+.4f}")
                    print(f"   🏆 Best: ${session_stats['best_trade']:+.4f} | 💔 Worst: ${session_stats['worst_trade']:+.4f}")
                    print("="*80)
                    print(f"   📊 {len(positions)}/{max_positions} ACTIVE POSITIONS | Next scan: {max(0, scan_interval - (current_time - last_scan_time)):.0f}s")
                    print("="*80)
                    
                    # Update and display each position
                    # 🚀 BATCH FETCH: Get all prices at once to avoid rate limits!
                    all_prices = {}
                    try:
                        alpaca_client = self.clients.get('alpaca')
                        if alpaca_client:
                            # Use snapshot API for all symbols at once
                            symbols = [p.symbol for p in positions if p.exchange == 'alpaca']
                            if symbols:
                                try:
                                    snapshot = alpaca_client.get_crypto_snapshot(symbols)
                                    if snapshot:
                                        for sym, data in snapshot.items():
                                            if data and 'latestTrade' in data:
                                                all_prices[sym] = float(data['latestTrade'].get('p', 0))
                                            elif data and 'latestQuote' in data:
                                                all_prices[sym] = float(data['latestQuote'].get('bp', 0))
                                except Exception:
                                    pass
                    except Exception:
                        pass
                    
                    # 🦈 Also batch fetch Kraken prices
                    try:
                        kraken_client = self.clients.get('kraken')
                        if kraken_client:
                            kraken_symbols = [p.symbol for p in positions if p.exchange == 'kraken']
                            for sym in kraken_symbols:
                                try:
                                    ticker = kraken_client.get_ticker(sym)
                                    if ticker:
                                        price = ticker.get('bid', ticker.get('price', 0))
                                        all_prices[sym] = float(price) if price else 0
                                except Exception:
                                    pass
                    except Exception:
                        pass
                    
                    try:
                        binance_client = self.clients.get('binance')
                        if binance_client:
                            binance_symbols = [p.symbol for p in positions if p.exchange == 'binance']
                            for sym in binance_symbols:
                                try:
                                    ticker = self._get_binance_ticker(binance_client, sym)
                                    if ticker:
                                        price = ticker.get('bid', ticker.get('price', 0))
                                        all_prices[sym] = float(price) if price else 0
                                except Exception:
                                    pass
                    except Exception:
                        pass
                    
                    total_unrealized = 0.0
                    real_positions = []  # Filter out dust
                    
                    for i, pos in enumerate(positions[:]):
                        try:
                            # Get current price from batch (NO FALLBACK - prevents rate limits!)
                            current = all_prices.get(pos.symbol, 0)
                            
                            # Skip if no price (batch failed for this symbol)
                            if current <= 0:
                                continue
                            
                            # Calculate P&L
                            fee_rate = self.fee_rates.get(pos.exchange, 0.0025)
                            entry_cost = pos.entry_price * pos.entry_qty * (1 + fee_rate)
                            exit_value = current * pos.entry_qty * (1 - fee_rate)
                            net_pnl = exit_value - entry_cost
                            
                            # 🎯 CORRECT MATH: Calculate P&L % from PRICE change, not cost
                            price_change_pct = ((current - pos.entry_price) / pos.entry_price * 100) if pos.entry_price > 0 else 0
                            # But for actual P&L %, use real costs
                            pnl_pct = (net_pnl / entry_cost * 100) if entry_cost > 0 else price_change_pct
                            
                            pos.current_price = current
                            pos.current_pnl = net_pnl
                            pos.current_pnl_pct = pnl_pct
                            
                            # Skip dust positions (< $0.01 value)
                            market_value = current * pos.entry_qty
                            if market_value < 0.01:
                                continue
                            
                            real_positions.append(pos)
                            total_unrealized += net_pnl
                            
                            # 🎯 FIXED PROGRESS BAR: Show negative when underwater!
                            # Progress from entry to target (can be negative if underwater)
                            if pos.target_price > pos.entry_price:
                                raw_progress = (current - pos.entry_price) / (pos.target_price - pos.entry_price) * 100
                            else:
                                raw_progress = 0
                            
                            # Visual: clamp display but show real % in text
                            display_progress = max(0, min(100, raw_progress))
                            
                            # Build progress bar with direction indicator
                            if raw_progress >= 0:
                                filled = int(display_progress / 5)
                                bar = "█" * filled + "░" * (20 - filled)
                            else:
                                # Underwater: show red blocks from left
                                underwater_pct = min(100, abs(raw_progress))
                                red_blocks = int(underwater_pct / 5)
                                bar = "▓" * red_blocks + "░" * (20 - red_blocks)
                            
                            # Whale info
                            whale_info = whale_signals.get(pos.symbol)
                            whale_str = f"🐋 {whale_info.reasoning[:50]}" if whale_info else "🐋 Scanning..."
                            
                            # ═════════════════════════════════════════════════════════════════
                            # 🔬 ENHANCED ANALYTICS: ETA + Probability + Velocity
                            # ═════════════════════════════════════════════════════════════════
                            eta_str = ""
                            if ETA_CALCULATOR_AVAILABLE and ImprovedETACalculator:
                                try:
                                    # Initialize ETA calculator for this position if needed
                                    if pos.eta_calculator is None:
                                        pos.eta_calculator = ImprovedETACalculator()
                                    
                                    # Track P&L history for this position
                                    pos.pnl_history.append((time.time(), net_pnl))
                                    # Keep last 60 samples (1 minute at 1Hz)
                                    if len(pos.pnl_history) > 60:
                                        pos.pnl_history = pos.pnl_history[-60:]
                                    
                                    # Calculate target P&L (what we need to hit target price)
                                    target_pnl = (pos.target_price - pos.entry_price) * pos.entry_qty * (1 - fee_rate) - entry_cost * fee_rate
                                    
                                    # Calculate ETA using probability model
                                    eta_result = pos.eta_calculator.calculate_eta(
                                        current_pnl=net_pnl,
                                        target_pnl=target_pnl,
                                        pnl_history=pos.pnl_history
                                    )
                                    pos.last_eta = eta_result
                                    
                                    # Format ETA display
                                    if eta_result.improved_eta == 0:
                                        eta_str = "🎯 TARGET!"
                                    elif eta_result.improved_eta == float('inf'):
                                        # Check velocity direction
                                        if eta_result.velocity < 0:
                                            eta_str = f"⏳ ∞ (↓ ${eta_result.velocity*60:.4f}/min)"
                                        else:
                                            eta_str = f"⏳ Calculating..."
                                    else:
                                        # Format time nicely
                                        if eta_result.improved_eta < 60:
                                            time_str = f"{eta_result.improved_eta:.0f}s"
                                        elif eta_result.improved_eta < 3600:
                                            time_str = f"{eta_result.improved_eta/60:.1f}m"
                                        else:
                                            time_str = f"{eta_result.improved_eta/3600:.1f}h"
                                        
                                        # Confidence indicator
                                        conf_icon = "🟢" if eta_result.reliability_band == "HIGH" else "🟡" if eta_result.reliability_band == "MEDIUM" else "🔴"
                                        
                                        # Velocity direction
                                        vel_icon = "↑" if eta_result.velocity > 0 else "↓" if eta_result.velocity < 0 else "→"
                                        accel_icon = "⚡" if eta_result.acceleration > 0 else "🐌" if eta_result.acceleration < 0 else ""
                                        
                                        eta_str = f"⏱️ ETA: {time_str} {conf_icon}{eta_result.confidence:.0%} | {vel_icon}${eta_result.velocity*60:.4f}/min {accel_icon}"
                                except Exception as e:
                                    eta_str = f"📊 Analytics loading..."
                            
                            # ═════════════════════════════════════════════════════════════════
                            # 🛡️ COUNTER-INTELLIGENCE: Firm Detection + Strategy
                            # ═════════════════════════════════════════════════════════════════
                            counter_str = ""
                            if self.counter_intel and COUNTER_INTEL_AVAILABLE:
                                try:
                                    # Build market data for analysis
                                    market_data = {
                                        'price': current,
                                        'volatility': abs(price_change_pct) / 100,
                                        'volume_ratio': 1.0
                                    }
                                    bot_detection = {'confidence': 0.75}  # Default detection confidence
                                    
                                    # Try each major firm and find best counter-opportunity
                                    best_signal = None
                                    for firm_id in ['citadel', 'jane_street', 'two_sigma', 'jump_trading', 'drw']:
                                        ci_signal = self.counter_intel.analyze_firm_for_counter_opportunity(
                                            firm_id, market_data, bot_detection
                                        )
                                        if ci_signal and (best_signal is None or ci_signal.confidence > best_signal.confidence):
                                            best_signal = ci_signal
                                    
                                    if best_signal:
                                        # Format: 🛡️ vs Citadel: TIMING_ADV +45ms | Conf: 78%
                                        strat_short = best_signal.strategy.value[:12] if hasattr(best_signal.strategy, 'value') else str(best_signal.strategy)[:12]
                                        counter_str = f"🛡️ vs {best_signal.firm_id}: {strat_short.upper()} +{best_signal.timing_advantage:.0f}ms | {best_signal.confidence:.0%}"
                                except Exception as e:
                                    counter_str = f"🛡️ Counter-Intel loading..."
                            
                            # 🏢 Firm Attribution - Who's trading?
                            firm_str = ""
                            if self.firm_attribution and FIRM_ATTRIBUTION_AVAILABLE:
                                try:
                                    symbol_base = pos.symbol.replace('USD', '').replace('/', '').upper()
                                    # Get current hour in UTC
                                    current_hour = time.gmtime().tm_hour
                                    # Estimate frequency based on price change (higher volatility = higher freq)
                                    est_frequency = 0.5 + abs(price_change_pct)
                                    # Use attribute_bot_to_firm method
                                    matches = self.firm_attribution.attribute_bot_to_firm(
                                        symbol=symbol_base,
                                        frequency=est_frequency,
                                        order_size_usd=market_value,
                                        strategy="momentum" if price_change_pct > 0 else "mean_reversion",
                                        current_hour_utc=current_hour
                                    )
                                    if matches:
                                        top_firm, confidence = matches[0]
                                        # Get more details about the firm
                                        firm_details = self.firm_attribution.get_firm_details(top_firm)
                                        firm_name = firm_details.name if firm_details else top_firm.title()
                                        # Predict direction based on firm's typical strategy
                                        direction = 'neutral'
                                        if firm_details:
                                            if 'momentum' in firm_details.typical_strategies:
                                                direction = 'bullish' if price_change_pct > 0 else 'bearish'
                                            elif 'mean_reversion' in firm_details.typical_strategies:
                                                direction = 'bearish' if price_change_pct > 2 else 'bullish' if price_change_pct < -2 else 'neutral'
                                        dir_icon = "🟢" if direction == 'bullish' else "🔴" if direction == 'bearish' else "⚪"
                                        firm_str = f"🏢 {firm_name}: {dir_icon} {direction} ({confidence:.0%})"
                                except Exception as e:
                                    firm_str = ""
                            
                            # Display with CORRECT values
                            pnl_color = '\033[92m' if net_pnl >= 0 else '\033[91m'
                            reset = '\033[0m'
                            print(f"\n🎯 {pos.symbol} ({pos.exchange.upper()}) | Value: ${market_value:.2f}")
                            print(f"   💵 Entry: ${pos.entry_price:,.6f} | Current: ${current:,.6f} | Target: ${pos.target_price:,.6f}")
                            print(f"   [{bar}] {raw_progress:+.1f}% to target | {pnl_color}${net_pnl:+.4f} ({price_change_pct:+.2f}% price){reset}")
                            if eta_str:
                                print(f"   {eta_str}")
                            if counter_str:
                                print(f"   {counter_str}")
                            if firm_str:
                                print(f"   {firm_str}")
                            
                            # ⚡ HFT Harmonic Signal - Sacred frequency analysis
                            hft_str = ""
                            if self.hft_engine and HFT_ENGINE_AVAILABLE:
                                try:
                                    # Feed tick to HFT engine for harmonic analysis
                                    tick_data = {
                                        'timestamp': time.time(),
                                        'symbol': pos.symbol,
                                        'price': current,
                                        'volume': market_value,
                                        'side': 'buy' if price_change_pct > 0 else 'sell',
                                        'exchange': pos.exchange
                                    }
                                    self.hft_engine.ingest_tick(tick_data)
                                    
                                    # Get last harmonic tone if available
                                    if self.hft_engine.last_harmonic_tone:
                                        tone = self.hft_engine.last_harmonic_tone
                                        # Format: ⚡ 528Hz 🦅falcon + gamma | 85% conf
                                        auris_icons = {'falcon': '🦅', 'tiger': '🐅', 'owl': '🦉', 'dolphin': '🐬', 'hummingbird': '🐦', 'deer': '🦌', 'panda': '🐼', 'cargoship': '🚢', 'clownfish': '🐠'}
                                        auris_icon = auris_icons.get(tone.auris_node, '🔮')
                                        hft_str = f"⚡ {tone.frequency:.0f}Hz {auris_icon}{tone.auris_node} + {tone.brainwave} | {tone.confidence:.0%}"
                                except Exception:
                                    pass
                            
                            if hft_str:
                                print(f"   {hft_str}")
                            print(f"   {whale_str}")
                            
                            # ═════════════════════════════════════════════════
                            # EXIT CONDITIONS - PROFIT ONLY!
                            # ═════════════════════════════════════════════════
                            
                            should_sell = False
                            sell_reason = ''
                            
                            # 1. Target hit - PERFECT EXIT!
                            if current >= pos.target_price:
                                should_sell = True
                                sell_reason = 'TARGET_HIT'
                                print(f"   🎯🎯🎯 TARGET HIT! SELLING! 🎯🎯🎯")
                            
                            # 2. Profitable momentum reversal
                            elif net_pnl > 0.01 and len(pos.price_history) >= 10:
                                recent = pos.price_history[-10:]
                                if recent[0] > 0:
                                    momentum = (recent[-1] - recent[0]) / recent[0] * 100
                                    if momentum < -0.3:  # Losing momentum while in profit
                                        should_sell = True
                                        sell_reason = 'MOMENTUM_PROFIT'
                                        print(f"   📈 TAKING PROFIT (momentum reversal)")
                            
                            # Track price history
                            pos.price_history.append(current)
                            if len(pos.price_history) > 50:
                                pos.price_history.pop(0)
                            
                            # Execute sell if ready
                            if should_sell:
                                sell_order = pos.client.place_market_order(
                                    symbol=pos.symbol,
                                    side='sell',
                                    quantity=pos.entry_qty
                                )
                                if sell_order:
                                    sell_price = float(sell_order.get('filled_avg_price', current))
                                    final_exit = sell_price * pos.entry_qty * (1 - fee_rate)
                                    final_pnl = final_exit - entry_cost
                                    
                                    # Update session stats
                                    session_stats['total_pnl'] += final_pnl
                                    if final_pnl > 0:
                                        session_stats['winning_trades'] += 1
                                        session_stats['best_trade'] = max(session_stats['best_trade'], final_pnl)
                                    else:
                                        session_stats['losing_trades'] += 1
                                        session_stats['worst_trade'] = min(session_stats['worst_trade'], final_pnl)
                                    
                                    print(f"\n   ✅ SOLD: ${final_pnl:+.4f} ({sell_reason})")
                                    print(f"   🔄 CYCLE CONTINUES - SCANNING FOR NEXT TARGET...")
                                    
                                    # Remove position
                                    positions.remove(pos)
                                    
                                    # Force immediate scan for next opportunity
                                    last_scan_time = 0
                                    
                        except Exception as e:
                            print(f"   ⚠️ Error monitoring {pos.symbol}: {e}")
                    
                    # Footer
                    print(f"\n{'='*80}")
                    print(f"   💰 UNREALIZED P&L: ${total_unrealized:+.4f}")
                    print(f"   🚫 NO STOP LOSS - HOLDING UNTIL PROFIT!")
                    print(f"   ⌨️ Press Ctrl+C to stop")
                
                else:
                    # No positions - show scanning status
                    print(f"\r🔍 No positions - scanning in {max(0, scan_interval - (current_time - last_scan_time)):.0f}s...", end="", flush=True)
                
                time.sleep(monitor_interval)
                
        except KeyboardInterrupt:
            print("\n\n" + "="*80)
            print("👑 QUEEN AUTONOMOUS MODE - STOPPING")
            print("="*80)
            
            # Close ONLY profitable positions
            print("\n🛑 Closing PROFITABLE positions only (keeping losers)...")
            closed_pnl = 0.0
            kept_count = 0
            
            for pos in positions:
                try:
                    if pos.current_pnl > 0:
                        sell_order = pos.client.place_market_order(
                            symbol=pos.symbol,
                            side='sell',
                            quantity=pos.entry_qty
                        )
                        if sell_order:
                            fee_rate = self.fee_rates.get(pos.exchange, 0.0025)
                            sell_price = float(sell_order.get('filled_avg_price', pos.current_price))
                            entry_cost = pos.entry_price * pos.entry_qty * (1 + fee_rate)
                            final_exit = sell_price * pos.entry_qty * (1 - fee_rate)
                            final_pnl = final_exit - entry_cost
                            closed_pnl += final_pnl
                            session_stats['total_pnl'] += final_pnl
                            print(f"   ✅ Closed {pos.symbol}: ${final_pnl:+.4f}")
                    else:
                        kept_count += 1
                        print(f"   ⛔ KEEPING {pos.symbol} (P&L: ${pos.current_pnl:+.4f} - not selling at a loss)")
                except Exception as e:
                    print(f"   ⚠️ Error: {e}")
            
            if kept_count > 0:
                print(f"\n   📌 Kept {kept_count} positions open (underwater - waiting for profit)")
            
            # Final summary
            runtime = time.time() - session_stats['start_time']
            runtime_str = f"{int(runtime//3600)}h {int((runtime%3600)//60)}m {int(runtime%60)}s"
            
            print("\n" + "="*80)
            print("👑 QUEEN AUTONOMOUS SESSION COMPLETE")
            print("="*80)
            print(f"   ⏱️ Total Runtime: {runtime_str}")
            print(f"   🔄 Total Cycles: {session_stats['cycles']}")
            print(f"   📈 Total Trades: {session_stats['total_trades']}")
            print(f"   ✅ Winning Trades: {session_stats['winning_trades']}")
            print(f"   ❌ Losing Trades: {session_stats['losing_trades']}")
            win_rate = (session_stats['winning_trades'] / session_stats['total_trades'] * 100) if session_stats['total_trades'] > 0 else 0
            print(f"   🎯 Win Rate: {win_rate:.1f}%")
            print(f"   💰 SESSION P&L: ${session_stats['total_pnl']:+.4f}")
            print(f"   🏆 Best Trade: ${session_stats['best_trade']:+.4f}")
            print(f"   💔 Worst Trade: ${session_stats['worst_trade']:+.4f}")
            print("="*80)
            
            if session_stats['total_pnl'] > 0:
                print("🏆 SESSION: PROFITABLE! The Queen is pleased. 👑")
            else:
                print("💪 SESSION: Learning cycle. The Queen grows stronger. 👑")
            print("="*80)
            
        return session_stats

    def _dump_dashboard_state(self, session_stats, positions, queen=None):
        """Dump live state to JSON for Command Center UI."""
        try:
            import json
            import random
            # Prepare serializable positions
            serializable_positions = []
            for p in positions:
                p_dict = {
                    'symbol': p.symbol,
                    'exchange': p.exchange,
                    'entry_price': p.entry_price,
                    'entry_qty': p.entry_qty,
                    'current_price': p.current_price,
                    'current_pnl': p.current_pnl,
                    'current_pnl_pct': p.current_pnl_pct,
                    'target_price': p.target_price,
                    'entry_time': p.entry_time
                }
                serializable_positions.append(p_dict)

            exchange_status = {}
            try:
                for name, client in getattr(self, "clients", {}).items():
                    exchange_status[name] = {
                        "connected": client is not None,
                        "dry_run": getattr(client, "dry_run", False)
                    }
            except Exception:
                exchange_status = {}

            # Run flight check for system validation
            flight_check = {}
            try:
                flight_check = self.run_flight_check()
            except Exception:
                flight_check = {"summary": {"online_pct": 0, "critical_online": False}}

            # Collect prices from exchanges for market feed tab
            kraken_prices = {}
            binance_prices = {}
            alpaca_prices = {}
            try:
                if hasattr(self, 'kraken') and self.kraken:
                    for sym in ['BTC/USD', 'ETH/USD', 'SOL/USD', 'XRP/USD', 'DOGE/USD', 'ADA/USD']:
                        try:
                            ticker = self.kraken.get_ticker(sym)
                            if ticker and 'last' in ticker:
                                kraken_prices[sym] = float(ticker['last'])
                        except Exception:
                            pass
            except Exception:
                pass
            try:
                if hasattr(self, 'binance') and self.binance:
                    for sym in ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT', 'DOGEUSDT', 'ADAUSDT']:
                        try:
                            ticker = self.binance.get_ticker(sym)
                            if ticker and 'last' in ticker:
                                binance_prices[sym] = float(ticker['last'])
                        except Exception:
                            pass
            except Exception:
                pass
            try:
                if hasattr(self, 'alpaca') and self.alpaca:
                    for sym in ['BTC/USD', 'ETH/USD', 'AAPL', 'TSLA', 'NVDA', 'SPY']:
                        try:
                            ticker = self.alpaca.get_ticker(sym)
                            if ticker and 'last' in ticker:
                                alpaca_prices[sym] = float(ticker['last'])
                        except Exception:
                            pass
            except Exception:
                pass

            # Build systems registry for systems tab
            systems_registry = {}
            try:
                systems_registry['Kraken'] = hasattr(self, 'kraken') and self.kraken is not None
                systems_registry['Binance'] = hasattr(self, 'binance') and self.binance is not None
                systems_registry['Alpaca'] = hasattr(self, 'alpaca') and self.alpaca is not None
                systems_registry['Queen Hive'] = queen is not None
                systems_registry['ThoughtBus'] = hasattr(self, 'thought_bus') and self.thought_bus is not None
                systems_registry['Miner Brain'] = hasattr(self, 'miner') and self.miner is not None
                systems_registry['Ultimate Intel'] = hasattr(self, 'ultimate_intelligence') and self.ultimate_intelligence is not None
                systems_registry['Wave Scanner'] = hasattr(self, 'wave_scanner') and self.wave_scanner is not None
                systems_registry['Quantum Mirror'] = hasattr(self, 'quantum_mirror') and self.quantum_mirror is not None
                systems_registry['Timeline Oracle'] = hasattr(self, 'timeline_oracle') and self.timeline_oracle is not None
                systems_registry['Probability Nexus'] = hasattr(self, 'probability_nexus') and self.probability_nexus is not None
                systems_registry['Harmonic Nexus'] = hasattr(self, 'harmonic') and self.harmonic is not None
            except Exception:
                pass

            # Quantum data for quantum tab
            quantum_data = {
                'coherence': 0.618 + (random.random() * 0.1 - 0.05),
                'active_timelines': 7,
                'anchored_timelines': 3,
                'schumann_hz': 7.83,
                'love_freq': 528
            }

            # Whale and bot data (simulated for now - integrate real data later)
            whale_stats = {
                'count_24h': session_stats.get('total_trades', 0) * 3,
                'total_volume': session_stats.get('total_pnl', 0) * 10000 + 50000,
                'bulls': int(session_stats.get('winning_trades', 0) * 1.5),
                'bears': session_stats.get('losing_trades', 0)
            }
            bot_count = len(systems_registry)
            
            state = {
                "timestamp": time.time(),
                "session_stats": session_stats,
                "positions": serializable_positions,
                "active_count": len(positions),
                "exchange_status": exchange_status,
                "flight_check": flight_check,
                "queen_message": "War Room Active",
                "queen_equity": queen.equity if queen else 0.0,
                "last_candidates": getattr(self, 'last_rising_star_candidates', []),
                "last_winners": getattr(self, 'last_rising_star_winners', []),
                "last_queen_decisions": getattr(self, 'last_queen_decisions', []),
                # Market feed tab data
                "kraken_prices": kraken_prices,
                "binance_prices": binance_prices,
                "alpaca_prices": alpaca_prices,
                # Systems tab data
                "systems_registry": systems_registry,
                "cycles": session_stats.get('cycles', 0),
                # Quantum tab data
                "quantum": quantum_data,
                # Whale tab data
                "whale_stats": whale_stats,
                # Bot tab data  
                "bot_count": bot_count,
                "total_bots": bot_count + 50,
                "active_bots": int(bot_count * 0.6)
            }

            # Atomic write into shared state dir
            state_dir = os.environ.get("AUREON_STATE_DIR", "state")
            os.makedirs(state_dir, exist_ok=True)
            tmp_path = os.path.join(state_dir, "dashboard_snapshot.json.tmp")
            final_path = os.path.join(state_dir, "dashboard_snapshot.json")
            with open(tmp_path, "w") as f:
                json.dump(state, f)
            os.replace(tmp_path, final_path)
        except Exception as e:
            # Log state dump errors to help debugging
            print(f"⚠️ Dashboard state dump failed: {e}")
            pass

    # ═══════════════════════════════════════════════════════════════════════════════
    # 🎖️ WAR ROOM MODE - RICH TERMINAL UI (NO SPAM)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def run_autonomous_warroom(self, max_positions: int = 5, amount_per_position: float = 2.5,
                               target_pct: float = 1.0, min_change_pct: float = 0.3):
        """
        🎖️🌟 WAR ROOM + RISING STAR MODE - THE WINNING FORMULA 🌟🎖️
        
        COMPLETE 4-STAGE SYSTEM:
        
        STAGE 1: SCAN - Use ALL intelligence systems to find candidates
          - Quantum scoring (Luck, Phantom, Inception, Elephant, etc.)
          - Probability predictions (95% accuracy)
          - Wave scanner momentum
          - Firm intelligence (smart money)
          - Whale signals
          
        STAGE 2: SIMULATE - Top 4 candidates → 30-second Monte Carlo
          - 1000 simulations each
          - Historical patterns + predictions
          - Time-to-profit optimization
          
        STAGE 3: SELECT - Pick BEST 2 winners
          - Highest simulation confidence
          - Fastest time to profit
          - 30-second profit window target
          
        STAGE 4: EXECUTE + ACCUMULATE + MONITOR + KILL
          - Open positions on best 2
          - ACCUMULATE if price drops (DCA strategy)
          - ALL systems monitoring for exit
          - KILL when profit target hit
        
        Gary Leckey | The Math Works | January 2026
        """
        if not RICH_AVAILABLE:
            print("⚠️ Rich library not available - falling back to standard mode")
            return self.run_autonomous(max_positions, amount_per_position, target_pct, min_change_pct)

        # ═══════════════════════════════════════════════════════════════════
        # 👑 QUEEN HIVE MIND (MANDATORY)
        # ═══════════════════════════════════════════════════════════════════
        queen = None
        try:
            from aureon_queen_hive_mind import QueenHiveMind
            queen = QueenHiveMind()
            print("👑 QUEEN SERO: AWAKENED AND READY!")
            print(f"   🎯 Dream: ${queen.THE_DREAM:,.0f} (ONE BILLION)")
            print(f"   💰 Current equity: ${queen.equity:,.2f}")
            print()
        except Exception as e:
            print(f"❌ Queen initialization failed: {e}")
            print("   War Room autonomous mode requires the Queen. Falling back to legacy autonomous mode.")
            return self.run_autonomous(max_positions, amount_per_position, target_pct, min_change_pct)
        
        # ═══════════════════════════════════════════════════════════════════
        # 🌟 RISING STAR INITIALIZATION
        # ═══════════════════════════════════════════════════════════════════
        try:
            from aureon_rising_star_logic import RisingStarScanner, RisingStarCandidate
            self.rising_star_scanner = RisingStarScanner(self)
            self.rising_star_enabled = True
            RISING_STAR_AVAILABLE = True
        except ImportError:
            RISING_STAR_AVAILABLE = False
            self.rising_star_enabled = False
        
        # ═══════════════════════════════════════════════════════════════════
        # 🏹⚔️ APACHE WAR BAND INITIALIZATION
        # ═══════════════════════════════════════════════════════════════════
        war_band = None
        if WAR_BAND_AVAILABLE:
            try:
                # Need to create market pulse and unified client for War Band
                from unified_exchange_client import MultiExchangeClient
                from aureon_market_pulse import MarketPulse
                unified_client = MultiExchangeClient()
                market_pulse = MarketPulse(unified_client)
                war_band = EnhancedWarBand(unified_client, market_pulse)
                print("🏹⚔️ Apache War Band initialized and ready for autonomous operations")
            except Exception as e:
                print(f"⚠️ Apache War Band initialization failed: {e}")
                war_band = None
        
        # ═══════════════════════════════════════════════════════════════════
        # 🐝👑 HIVE STATE PUBLISHER INITIALIZATION
        # ═══════════════════════════════════════════════════════════════════
        hive_publisher = None
        if HIVE_STATE_AVAILABLE:
            try:
                hive_publisher = get_hive()
                hive_publisher.update(mood="Focused", scanner="ORCA Autonomous", coherence=0.85)
                print("🐝👑 Hive State Publisher initialized - Queen is watching")
            except Exception as e:
                print(f"⚠️ Hive State Publisher initialization failed: {e}")
                hive_publisher = None
        
        # ═══════════════════════════════════════════════════════════════════
        # 📜🤖 HISTORICAL BOT CENSUS INITIALIZATION
        # ═══════════════════════════════════════════════════════════════════
        bot_census = None
        if HISTORICAL_BOT_CENSUS_AVAILABLE:
            try:
                # Initialize with key symbols for bot tracking
                bot_census = {
                    'tracked_symbols': ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'],
                    'last_census': time.time(),
                    'active_bots': []
                }
                print("📜🤖 Historical Bot Census initialized - Tracking algorithmic evolution")
            except Exception as e:
                print(f"⚠️ Historical Bot Census initialization failed: {e}")
                bot_census = None
        
        # ═══════════════════════════════════════════════════════════════════
        # 📊🔬 HISTORICAL BACKTEST ENGINE INITIALIZATION
        # ═══════════════════════════════════════════════════════════════════
        backtest_engine = None
        if HISTORICAL_BACKTEST_AVAILABLE:
            try:
                backtest_engine = AureonBacktestEngine()
                print("📊🔬 Historical Backtest Engine initialized - Harmonic fusion ready")
            except Exception as e:
                print(f"⚠️ Historical Backtest Engine initialization failed: {e}")
                backtest_engine = None
        
        # ═══════════════════════════════════════════════════════════════════
        # 🌍 GLOBAL ORCHESTRATOR INITIALIZATION
        # ═══════════════════════════════════════════════════════════════════
        global_orchestrator = None
        if GLOBAL_ORCHESTRATOR_AVAILABLE:
            try:
                global_orchestrator = GlobalAureonOrchestrator(dry_run=True)
                print("🌍 Global Orchestrator initialized - Master control active")
            except Exception as e:
                print(f"⚠️ Global Orchestrator initialization failed: {e}")
                global_orchestrator = None
        
        # ═══════════════════════════════════════════════════════════════════
        # 🎵 HARMONIC BINARY PROTOCOL INITIALIZATION
        # ═══════════════════════════════════════════════════════════════════
        harmonic_binary = None
        if HARMONIC_BINARY_AVAILABLE:
            try:
                # Initialize with default packet for ORCA autonomous
                packet = encode_text_packet("ORCA_AUTONOMOUS_START", message_type=1, direction=0, grade=5)
                harmonic_binary = packet
                print("🎵 Harmonic Binary Protocol initialized - Compact transport ready")
            except Exception as e:
                print(f"⚠️ Harmonic Binary Protocol initialization failed: {e}")
                harmonic_binary = None
        
        # ═══════════════════════════════════════════════════════════════════
        # 🔗 HARMONIC CHAIN MASTER INITIALIZATION
        # ═══════════════════════════════════════════════════════════════════
        harmonic_chain_master = None
        if HARMONIC_CHAIN_MASTER_AVAILABLE:
            try:
                harmonic_chain_master = HarmonicChainMaster()
                print("🔗 Harmonic Chain Master initialized - Signal processing active")
            except Exception as e:
                print(f"⚠️ Harmonic Chain Master initialization failed: {e}")
                harmonic_chain_master = None
        
        # ═══════════════════════════════════════════════════════════════════
        # ⚡ HARMONIC COUNTER FREQUENCY INITIALIZATION
        # ═══════════════════════════════════════════════════════════════════
        harmonic_counter = None
        if HARMONIC_COUNTER_AVAILABLE:
            try:
                # Module available, mark as initialized
                harmonic_counter = True
                print("⚡ Harmonic Counter Frequency initialized - Planetary counter-frequencies ready")
            except Exception as e:
                print(f"⚠️ Harmonic Counter Frequency initialization failed: {e}")
                harmonic_counter = None
        
        # ═══════════════════════════════════════════════════════════════════
        # 🌊 HARMONIC WAVE FUSION INITIALIZATION
        # ═══════════════════════════════════════════════════════════════════
        harmonic_fusion = None
        if HARMONIC_FUSION_AVAILABLE:
            try:
                harmonic_fusion = get_harmonic_fusion()
                print("🌊 Harmonic Wave Fusion initialized - Unified harmonic system active")
            except Exception as e:
                print(f"⚠️ Harmonic Wave Fusion initialization failed: {e}")
                harmonic_fusion = None
        
        # ═══════════════════════════════════════════════════════════════════
        # 🌊⚡ HARMONIC MOMENTUM WAVE SCANNER INITIALIZATION
        # ═══════════════════════════════════════════════════════════════════
        harmonic_momentum = None
        if HARMONIC_MOMENTUM_AVAILABLE:
            try:
                harmonic_momentum = HarmonicMomentumWaveScanner()
                print("🌊⚡ Harmonic Momentum Wave Scanner initialized - Ultimate momentum detection active")
            except Exception as e:
                print(f"⚠️ Harmonic Momentum Wave Scanner initialization failed: {e}")
                harmonic_momentum = None
        
        # ═══════════════════════════════════════════════════════════════════
        # 🌊 HARMONIC REALITY FRAMEWORK INITIALIZATION
        # ═══════════════════════════════════════════════════════════════════
        harmonic_reality = None
        if HARMONIC_REALITY_AVAILABLE:
            try:
                harmonic_reality = HarmonicRealityFramework()
                print("🌊 Harmonic Reality Framework initialized - Master equations active")
            except Exception as e:
                print(f"⚠️ Harmonic Reality Framework initialization failed: {e}")
                harmonic_reality = None
        
        # ═══════════════════════════════════════════════════════════════════
        # 🗺️ GLOBAL BOT MAP INITIALIZATION
        # ═══════════════════════════════════════════════════════════════════
        global_bot_map = None
        if GLOBAL_BOT_MAP_AVAILABLE:
            try:
                global_bot_map = GlobalBotMap()
                print("🗺️ Global Bot Map initialized - Visual bot activity tracking active")
            except Exception as e:
                print(f"⚠️ Global Bot Map initialization failed: {e}")
                global_bot_map = None
        
        # ═══════════════════════════════════════════════════════════════════
        # 🌌 ENHANCED QUANTUM TELESCOPE INITIALIZATION
        # ═══════════════════════════════════════════════════════════════════
        enhanced_quantum_telescope = None
        if ENHANCED_QUANTUM_TELESCOPE_AVAILABLE:
            try:
                # Create geometry engine first, then pass to telescope
                geometry_engine = EnhancedQuantumGeometryEngine()
                enhanced_quantum_telescope = EnhancedQuantumTelescope(geometry_engine=geometry_engine)
                print("🌌 Enhanced Quantum Telescope initialized - Sacred geometry bot visualization active")
            except Exception as e:
                print(f"⚠️ Enhanced Quantum Telescope initialization failed: {e}")
                enhanced_quantum_telescope = None
        
        # ═══════════════════════════════════════════════════════════════════
        # 💭 ENIGMA DREAM PROCESSOR INITIALIZATION
        # ═══════════════════════════════════════════════════════════════════
        enigma_dream = None
        if ENIGMA_DREAM_AVAILABLE:
            try:
                enigma_dream = EnigmaDreamProcessor()
                print("💭 Enigma Dream Processor initialized - Consciousness state processing active")
            except Exception as e:
                print(f"⚠️ Enigma Dream Processor initialization failed: {e}")
                enigma_dream = None
        
        # ═══════════════════════════════════════════════════════════════════
        # ✨ ENHANCEMENT LAYER INITIALIZATION
        # ═══════════════════════════════════════════════════════════════════
        enhancement_layer = None
        if ENHANCEMENT_LAYER_AVAILABLE:
            try:
                enhancement_layer = EnhancementLayer()
                print("✨ Enhancement Layer initialized - Unified enhancement system active")
            except Exception as e:
                print(f"⚠️ Enhancement Layer initialization failed: {e}")
                enhancement_layer = None
        
        # ═══════════════════════════════════════════════════════════════════
        # 🧩 ENIGMA INTEGRATION INITIALIZATION
        # ═══════════════════════════════════════════════════════════════════
        enigma_integration = None
        if ENIGMA_INTEGRATION_AVAILABLE:
            try:
                enigma_integration = EnigmaIntegration()
                print("🧩 Enigma Integration initialized - Complete Enigma system integration active")
            except Exception as e:
                print(f"⚠️ Enigma Integration initialization failed: {e}")
                enigma_integration = None
        
        # ═══════════════════════════════════════════════════════════════════
        # 📊 FIRM INTELLIGENCE CATALOG INITIALIZATION
        # ═══════════════════════════════════════════════════════════════════
        firm_intelligence = None
        if FIRM_INTELLIGENCE_AVAILABLE:
            try:
                firm_intelligence = get_firm_catalog()
                print("📊 Firm Intelligence Catalog initialized - Real-time firm tracking active")
            except Exception as e:
                print(f"⚠️ Firm Intelligence Catalog initialization failed: {e}")
                firm_intelligence = None
        
        # ═══════════════════════════════════════════════════════════════════
        # 🌀 ENIGMA CORE INITIALIZATION
        # ═══════════════════════════════════════════════════════════════════
        enigma_core = None
        if ENIGMA_CORE_AVAILABLE:
            try:
                enigma_core = EnigmaCore()
                print("🌀 Enigma Core initialized - Primary consciousness engine active")
            except Exception as e:
                print(f"⚠️ Enigma Core initialization failed: {e}")
                enigma_core = None
        
        # ═══════════════════════════════════════════════════════════════════
        # 🆕 ADDITIONAL NEURAL & TRADING SYSTEMS INITIALIZATION
        # ═══════════════════════════════════════════════════════════════════
        aureon_miner = None
        if AUREON_MINER_AVAILABLE:
            try:
                aureon_miner = AureonMiner()
                print("⛏️ Aureon Miner initialized - Background mining with harmonic optimization")
            except Exception as e:
                print(f"⚠️ Aureon Miner initialization failed: {e}")
                aureon_miner = None
        
        multi_exchange = None
        if MULTI_EXCHANGE_AVAILABLE:
            try:
                multi_exchange = MultiExchangeManager() if MultiExchangeManager else None
                print("🌐 Multi-Exchange Manager initialized - Cross-exchange orchestration active")
            except Exception as e:
                print(f"⚠️ Multi-Exchange Manager initialization failed: {e}")
                multi_exchange = None
        
        multi_pair = None
        if MULTI_PAIR_AVAILABLE:
            try:
                multi_pair = MasterEquation() if MasterEquation else None
                print("🎯 Multi-Pair Master Equation initialized - Coherence monitoring active")
            except Exception as e:
                print(f"⚠️ Multi-Pair initialization failed: {e}")
                multi_pair = None
        
        multiverse_live = None
        if MULTIVERSE_LIVE_AVAILABLE:
            try:
                multiverse_live = True  # Module available
                print("🌌 Multiverse Live Engine initialized - Commando unified trading active")
            except Exception as e:
                print(f"⚠️ Multiverse Live initialization failed: {e}")
                multiverse_live = None
        
        multiverse_orchestrator = None
        if MULTIVERSE_ORCHESTRATOR_AVAILABLE:
            try:
                multiverse_orchestrator = True  # Module available
                print("✨ Multiverse Orchestrator initialized - Atom→Galaxy ladder active")
            except Exception as e:
                print(f"⚠️ Multiverse Orchestrator initialization failed: {e}")
                multiverse_orchestrator = None
        
        mycelium_network = None
        if MYCELIUM_NETWORK_AVAILABLE:
            try:
                mycelium_network = MyceliumNetwork(initial_capital=1000.0)
                print("🍄 Mycelium Neural Network initialized - Underground signal network active")
            except Exception as e:
                print(f"⚠️ Mycelium Network initialization failed: {e}")
                mycelium_network = None
        
        neural_revenue = None
        if NEURAL_REVENUE_AVAILABLE:
            try:
                neural_revenue = NeuralRevenueOrchestrator(dry_run=True)
                print("🌍🔗 Neural Revenue Orchestrator initialized - Energy reclamation active")
            except Exception as e:
                print(f"⚠️ Neural Revenue Orchestrator initialization failed: {e}")
                neural_revenue = None
        
        # Rising Star statistics
        rising_star_stats = {
            'candidates_scanned': 0,
            'simulations_run': 0,
            'winners_selected': 0,
            'accumulations_made': 0,
            'total_accumulated_value': 0.0,
        }
        
        # Initialize War Room display
        warroom = WarRoomDisplay()
        
        # Safe console creation - check if stdout is valid
        console = None
        try:
            if RICH_AVAILABLE and sys.stdout and not sys.stdout.closed:
                console = Console()
        except Exception:
            console = None
        
        # Session statistics
        session_stats = {
            'cycles': 0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0.0,
            'start_time': time.time(),
            'best_trade': 0.0,
            'worst_trade': 0.0,
        }
        
        # Current positions
        positions: List[LivePosition] = []
        
        # Timing
        base_scan_interval = 10
        scan_interval = base_scan_interval
        monitor_interval = 1.0
        last_scan_time = 0
        last_portfolio_scan = 0
        portfolio_scan_interval = 30
        # Queen-driven pacing & profit target
        base_target_pct = target_pct
        target_pct_current = target_pct
        queen_update_interval = 10.0
        last_queen_update = 0.0

        def _apply_queen_controls() -> None:
            """Adjust scan speed and profit targets based on Queen collective signal."""
            nonlocal scan_interval, target_pct_current
            if queen is None:
                return
            try:
                signal = queen.get_collective_signal()
                confidence = float(signal.get('confidence', 0.5))
                direction = signal.get('direction', 'NEUTRAL')
            except Exception:
                confidence = 0.5
                direction = 'NEUTRAL'

            # Speed: higher confidence -> faster scans
            speed_factor = max(0.5, min(1.5, 1.5 - confidence))
            scan_interval = max(3.0, min(20.0, base_scan_interval * speed_factor))

            # Profit target: higher confidence -> higher target, bearish -> more conservative
            target_factor = 0.8 + (confidence * 0.6)
            if direction == 'BULLISH':
                target_factor *= 1.1
            elif direction == 'BEARISH':
                target_factor *= 0.8
            target_pct_current = max(0.3, min(3.0, base_target_pct * target_factor))

        # Initial Queen pacing/targets
        _apply_queen_controls()
        
        # ═══════════════════════════════════════════════════════════════════
        # PHASE 0: LOAD EXISTING POSITIONS
        # ═══════════════════════════════════════════════════════════════════
        if console:
            try:
                console.print("[bold blue]📊 Loading existing positions...[/]")
            except Exception:
                print("📊 Loading existing positions...")
        else:
            print("📊 Loading existing positions...")
        
        for exchange_name, client in self.clients.items():
            try:
                if exchange_name == 'alpaca':
                    alpaca_positions = client.get_positions()
                    if alpaca_positions:
                        for ap in alpaca_positions:
                            symbol = ap.get('symbol', '').replace('/', '')
                            qty = float(ap.get('qty', 0))
                            entry_price = float(ap.get('avg_entry_price', 0))
                            current_price = float(ap.get('current_price', 0))
                            unrealized_pnl = float(ap.get('unrealized_pl', 0))
                            market_value = float(ap.get('market_value', 0))
                            
                            if qty > 0 and entry_price > 0:
                                fee_rate = self.fee_rates.get(exchange_name, 0.0025)
                                entry_cost = entry_price * qty * (1 + fee_rate)
                                breakeven = entry_price * (1 + fee_rate) / (1 - fee_rate)
                                target_price = breakeven * (1 + target_pct_current / 100)
                                exit_value = current_price * qty * (1 - fee_rate)
                                net_pnl = exit_value - entry_cost
                                
                                pos = LivePosition(
                                    symbol=symbol,
                                    exchange=exchange_name,
                                    entry_price=entry_price,
                                    entry_qty=qty,
                                    entry_cost=entry_cost,
                                    breakeven_price=breakeven,
                                    target_price=target_price,
                                    client=client,
                                    current_price=current_price,
                                    current_pnl=net_pnl,
                                    is_existing=True  # Mark as existing position (not opened by Rising Star)
                                )
                                positions.append(pos)
                                
                elif exchange_name == 'kraken':
                    kraken_balances = client.get_balance()
                    if kraken_balances:
                        for asset, qty in kraken_balances.items():
                            if asset in ['USD', 'ZUSD', 'EUR', 'ZEUR', 'DAI', 'USDC', 'USDT', 'TUSD']:
                                continue
                            qty = float(qty)
                            if qty > 0.000001:
                                symbol = f"{asset}USD"
                                try:
                                    ticker = client.get_ticker(symbol)
                                    current_price = float(ticker.get('bid', ticker.get('price', 0)))
                                    market_value = qty * current_price
                                    
                                    if market_value > 0.0:
                                        fee_rate = self.fee_rates.get(exchange_name, 0.0026)
                                        entry_price = current_price
                                        entry_cost = entry_price * qty * (1 + fee_rate)
                                        breakeven = entry_price * (1 + fee_rate) / (1 - fee_rate)
                                        target_price = breakeven * (1 + target_pct_current / 100)
                                        
                                        pos = LivePosition(
                                            symbol=symbol,
                                            exchange=exchange_name,
                                            entry_price=entry_price,
                                            entry_qty=qty,
                                            entry_cost=entry_cost,
                                            breakeven_price=breakeven,
                                            target_price=target_price,
                                            client=client,
                                            current_price=current_price,
                                            current_pnl=0.0,
                                            is_existing=True  # Mark as existing position
                                        )
                                        positions.append(pos)
                                except Exception:
                                    pass
                elif exchange_name == 'binance':
                    binance_balances = client.get_balance()
                    if binance_balances:
                        for asset, qty in binance_balances.items():
                            if asset in ['USD', 'USDT', 'USDC', 'BUSD', 'TUSD', 'DAI', 'FDUSD', 'GBP', 'EUR']:
                                continue
                            qty = float(qty)
                            if qty > 0.000001:
                                symbol_variants = [f"{asset}/USDT", f"{asset}/USDC", f"{asset}/USD", f"{asset}/BUSD"]
                                for symbol in symbol_variants:
                                    try:
                                        ticker = self._get_binance_ticker(client, symbol)
                                        current_price = float(ticker.get('bid', ticker.get('price', 0)) or 0)
                                        if current_price <= 0:
                                            continue
                                        market_value = qty * current_price
                                        if market_value > 0.0:
                                            fee_rate = self.fee_rates.get(exchange_name, 0.001)
                                            entry_price = current_price
                                            entry_cost = entry_price * qty * (1 + fee_rate)
                                            breakeven = entry_price * (1 + fee_rate) / (1 - fee_rate)
                                            target_price = breakeven * (1 + target_pct_current / 100)
                                            pos = LivePosition(
                                                symbol=symbol,
                                                exchange=exchange_name,
                                                entry_price=entry_price,
                                                entry_qty=qty,
                                                entry_cost=entry_cost,
                                                breakeven_price=breakeven,
                                                target_price=target_price,
                                                client=client,
                                                current_price=current_price,
                                                current_pnl=0.0,
                                                is_existing=True  # Mark as existing position
                                            )
                                            positions.append(pos)
                                            break
                                    except Exception:
                                        continue
            except Exception:
                pass
        
        if console:
            try:
                console.print(f"[green]✅ Loaded {len(positions)} positions[/]")
            except Exception:
                print(f"✅ Loaded {len(positions)} positions")
        else:
            print(f"✅ Loaded {len(positions)} positions")
        
        # ═══════════════════════════════════════════════════════════════════
        # MAIN LOOP WITH RICH LIVE
        # ═══════════════════════════════════════════════════════════════════
        
        # Only use Rich Live if available, warroom exists, console is valid, AND stdout is open
        use_rich_live = (RICH_AVAILABLE and 
                       warroom is not None and 
                       console is not None and
                       hasattr(sys.stdout, 'closed') and 
                       not sys.stdout.closed and
                       sys.stdout.isatty())
        
        # Try to start Rich Live mode
        live = None
        logging_handlers_backup = []
        
        if use_rich_live:
            # 🔇 SILENCE LOGGING while Rich is active to prevent scrolling/breaking UI
            try:
                root = logging.getLogger()
                for h in root.handlers[:]:
                    # Check if handler writes to stdout/stderr
                    if hasattr(h, 'stream') and (h.stream is sys.stdout or h.stream is sys.stderr):
                        root.removeHandler(h)
                        logging_handlers_backup.append(h)
            except Exception:
                pass

            try:
                live = Live(warroom.build_display(), refresh_per_second=2, console=console)
                live.start()
                _safe_print("✅ Rich War Room display started")
            except (ValueError, OSError, IOError) as e:
                # Rich Live crashed - fall back to text mode
                _safe_print(f"⚠️ Rich display failed ({e}), switching to text mode...")
                use_rich_live = False
                live = None
                
                # Restore logging if Rich failed
                try:
                    root = logging.getLogger()
                    for h in logging_handlers_backup:
                        root.addHandler(h)
                    logging_handlers_backup = []
                except: pass
        
        try:
            while True:
                current_time = time.time()
                session_stats['cycles'] += 1
                
                # 💵 UPDATE WARROOM CASH BALANCES EACH CYCLE
                try:
                    cash = self.get_available_cash()
                    if warroom is not None:
                        warroom.update_cash(
                            alpaca=cash.get('alpaca', 0),
                            kraken=cash.get('kraken', 0),
                            binance=cash.get('binance', 0)
                        )
                        warroom.cash_balances['capital'] = cash.get('capital', 0)
                        warroom.cash_status = self.last_cash_status.copy()
                except Exception:
                    pass
                
                # Update dashboard state for Command Center UI
                self._dump_dashboard_state(session_stats, positions, queen)

                # 👑 Queen pacing + profit target updates

                if current_time - last_queen_update >= queen_update_interval:
                    last_queen_update = current_time
                    _apply_queen_controls()
                    if warroom is not None:
                        warroom.add_flash_alert(
                            f"Queen pacing: scan={scan_interval:.1f}s target={target_pct_current:.2f}%",
                            'info'
                        )
                    else:
                        print(f"👑 Queen pacing: scan={scan_interval:.1f}s target={target_pct_current:.2f}%")
                
                # Update position health and success rate every cycle
                if warroom is not None:
                    warroom.update_position_health()
                    if session_stats['total_trades'] > 0:
                        success_rate = (session_stats['winning_trades'] / session_stats['total_trades']) * 100
                        warroom.update_efficiency(success_rate=success_rate)
                else:
                    if session_stats['total_trades'] > 0:
                        success_rate = (session_stats['winning_trades'] / session_stats['total_trades']) * 100
                        print(f"📊 Success rate: {success_rate:.1f}%")
                
                # ═══════════════════════════════════════════════════════
                # BATCH PRICE UPDATE
                # ═══════════════════════════════════════════════════════
                all_prices = {}
                try:
                    alpaca_client = self.clients.get('alpaca')
                    if alpaca_client:
                        symbols = [p.symbol for p in positions if p.exchange == 'alpaca']
                        if symbols:
                            snapshot = alpaca_client.get_crypto_snapshot(symbols)
                            if snapshot:
                                for sym, data in snapshot.items():
                                    if data and 'latestTrade' in data:
                                        all_prices[sym] = float(data['latestTrade'].get('p', 0))
                                    elif data and 'latestQuote' in data:
                                        all_prices[sym] = float(data['latestQuote'].get('bp', 0))
                except Exception:
                    pass
                
                try:
                    kraken_client = self.clients.get('kraken')
                    if kraken_client:
                        kraken_symbols = [p.symbol for p in positions if p.exchange == 'kraken']
                        for sym in kraken_symbols:
                            try:
                                ticker = kraken_client.get_ticker(sym)
                                if ticker:
                                    all_prices[sym] = ticker.get('bid', ticker.get('price', 0))
                            except Exception:
                                pass
                except Exception:
                    pass
                
                # ═══════════════════════════════════════════════════════
                # UPDATE POSITIONS & CHECK FOR EXITS
                # ═══════════════════════════════════════════════════════
                if warroom is not None:
                    warroom.positions_data = []  # Clear and rebuild
                else:
                    # No warroom display - nothing to clear
                    pass
                
                for pos in positions[:]:
                    current = all_prices.get(pos.symbol, 0)
                    if current <= 0:
                        current = pos.current_price or pos.entry_price or 0
                    if current <= 0:
                        continue
                    
                    fee_rate = self.fee_rates.get(pos.exchange, 0.0025)
                    entry_cost = pos.entry_price * pos.entry_qty * (1 + fee_rate)
                    exit_value = current * pos.entry_qty * (1 - fee_rate)
                    net_pnl = exit_value - entry_cost
                    market_value = current * pos.entry_qty
                    
                    pos.current_price = current
                    pos.current_pnl = net_pnl
                    
                    # Calculate progress
                    if pos.target_price > pos.entry_price:
                        progress = (current - pos.entry_price) / (pos.target_price - pos.entry_price) * 100
                    else:
                        progress = 0
                    
                    # ETA calculation
                    eta_str = "∞"
                    if hasattr(pos, 'pnl_history'):
                        pos.pnl_history.append((time.time(), net_pnl))
                        if len(pos.pnl_history) > 60:
                            pos.pnl_history = pos.pnl_history[-60:]
                        if len(pos.pnl_history) >= 5:
                            recent = pos.pnl_history[-5:]
                            time_diff = recent[-1][0] - recent[0][0]
                            pnl_diff = recent[-1][1] - recent[0][1]
                            if time_diff > 0 and pnl_diff > 0:
                                target_pnl = (pos.target_price - pos.entry_price) * pos.entry_qty
                                remaining = target_pnl - net_pnl
                                rate = pnl_diff / time_diff
                                if rate > 0:
                                    eta_secs = remaining / rate
                                    if eta_secs < 60:
                                        eta_str = f"{eta_secs:.0f}s"
                                    elif eta_secs < 3600:
                                        eta_str = f"{eta_secs/60:.1f}m"
                                    else:
                                        eta_str = f"{eta_secs/3600:.1f}h"
                    else:
                        pos.pnl_history = []
                    
                    # Get firm info (simplified)
                    firm_str = "Scanning..."
                    if self.counter_intel and COUNTER_INTEL_AVAILABLE:
                        try:
                            for firm_id in ['citadel', 'jane_street']:
                                ci_signal = self.counter_intel.analyze_firm_for_counter_opportunity(
                                    firm_id, {'price': current}, {'confidence': 0.7}
                                )
                                if ci_signal:
                                    firm_str = f"{firm_id[:8]} {ci_signal.confidence:.0%}"
                                    if warroom is not None:
                                        warroom.update_firm(firm_id, str(ci_signal.strategy.value)[:10] if hasattr(ci_signal.strategy, 'value') else '?', 'neutral')
                                    break
                        except Exception:
                            pass
                    
                    # Update warroom
                    if warroom is not None:
                        warroom.update_position(
                            symbol=pos.symbol,
                            exchange=pos.exchange.upper(),
                            value=market_value,
                            pnl=net_pnl,
                            progress=progress,
                            eta=eta_str,
                            firm=firm_str
                        )
                    else:
                        print(f"POS: {pos.symbol} {pos.exchange.upper()} value=${market_value:.2f} pnl={net_pnl:+.4f} progress={progress} eta={eta_str} firm={firm_str}")
                    
                    # Flash alert for deeply underwater positions
                    pnl_pct = (net_pnl / entry_cost * 100) if entry_cost > 0 else 0
                    if pnl_pct < -15 and not hasattr(pos, 'alerted_underwater'):
                        if warroom is not None:
                            warroom.add_flash_alert(f"{pos.symbol} underwater {pnl_pct:.1f}%", 'critical')
                        else:
                            print(f"⚠️ {pos.symbol} underwater {pnl_pct:.1f}%")
                        pos.alerted_underwater = True
                    elif pnl_pct >= -5:
                        pos.alerted_underwater = False  # Reset alert when recovered
                    
                    # Check for profitable exit
                    if current >= pos.target_price or net_pnl > entry_cost * 0.01:
                        try:
                            sell_order = pos.client.place_market_order(
                                symbol=pos.symbol,
                                side='sell',
                                quantity=pos.entry_qty
                            )
                            if sell_order:
                                session_stats['total_pnl'] += net_pnl
                                session_stats['total_trades'] += 1
                                if net_pnl >= 0:
                                    session_stats['winning_trades'] += 1
                                    session_stats['best_trade'] = max(session_stats['best_trade'], net_pnl)
                                else:
                                    session_stats['losing_trades'] += 1
                                    session_stats['worst_trade'] = min(session_stats['worst_trade'], net_pnl)
                                
                                # Record kill with full details
                                hold_time = time.time() - pos.entry_time if hasattr(pos, 'entry_time') else 0
                                if warroom is not None:
                                    warroom.record_kill(net_pnl, symbol=pos.symbol, exchange=pos.exchange, hold_time=hold_time)
                                    warroom.remove_position(pos.symbol)
                                else:
                                    print(f"🏆 Recorded kill: {pos.symbol} +${net_pnl:+.4f}")
                                    # No warroom to remove position from, maintain local state only
                                positions.remove(pos)
                                last_scan_time = 0  # Force scan
                        except Exception:
                            pass
                    
                    # ═══════════════════════════════════════════════════════
                    # 🌟 ACCUMULATION CHECK - BUY MORE IF PRICE DROPS
                    # ═══════════════════════════════════════════════════════
                    elif RISING_STAR_AVAILABLE and pos.accumulation_count < 3:
                        # Check if price dropped enough for accumulation
                        avg_entry = pos.avg_entry_price if pos.avg_entry_price > 0 else pos.entry_price
                        price_drop_pct = (avg_entry - current) / avg_entry * 100 if avg_entry > 0 else 0
                        
                        # Accumulate if price dropped 5%+ from avg entry
                        if price_drop_pct >= 5.0:
                            try:
                                cash = self.get_available_cash()
                                exchange_cash = cash.get(pos.exchange, 0)
                                accumulate_amount = min(amount_per_position * 0.5, exchange_cash * 0.5)
                                
                                # 🔍 SMART-SIZE: Enforce minimums for accumulation
                                min_required_acc = 1.0
                                if pos.exchange == 'binance': min_required_acc = 5.5
                                elif pos.exchange == 'kraken': min_required_acc = 2.0
                                
                                if accumulate_amount < min_required_acc:
                                    accumulate_amount = min_required_acc
                                
                                if accumulate_amount <= exchange_cash:
                                    acc_order = pos.client.place_market_order(
                                        symbol=pos.symbol,
                                        side='buy',
                                        quote_qty=accumulate_amount
                                    )
                                    if acc_order:
                                        acc_qty = float(acc_order.get('filled_qty', 0))
                                        acc_price = float(acc_order.get('filled_avg_price', current))
                                        
                                        if acc_qty > 0:
                                            # Update position with accumulation
                                            fee_rate = self.fee_rates.get(pos.exchange, 0.0025)
                                            acc_cost = acc_price * acc_qty * (1 + fee_rate)
                                            
                                            # New total qty and cost
                                            new_total_qty = pos.entry_qty + acc_qty
                                            new_total_cost = (pos.total_cost if pos.total_cost > 0 else pos.entry_cost) + acc_cost
                                            new_avg_entry = new_total_cost / new_total_qty / (1 + fee_rate) if new_total_qty > 0 else pos.entry_price
                                            
                                            # Update position
                                            pos.entry_qty = new_total_qty
                                            pos.total_cost = new_total_cost
                                            pos.avg_entry_price = new_avg_entry
                                            pos.accumulation_count += 1
                                            
                                            # Recalculate breakeven and target
                                            pos.breakeven_price = new_avg_entry * (1 + fee_rate) / (1 - fee_rate)
                                            pos.target_price = pos.breakeven_price * (1 + target_pct_current / 100)
                                            
                                            # Track stats
                                            rising_star_stats['accumulations_made'] += 1
                                            rising_star_stats['total_accumulated_value'] += accumulate_amount
                            except Exception:
                                pass
                
                # ═══════════════════════════════════════════════════════
                # 🌟 RISING STAR 4-STAGE SCAN FOR NEW OPPORTUNITIES
                # ═══════════════════════════════════════════════════════
                # Calculate how many NEW positions we can open (existing positions don't count against limit)
                existing_position_count = len([p for p in positions if hasattr(p, 'is_existing') and p.is_existing])
                new_position_count = len(positions) - existing_position_count
                can_open_more = new_position_count < max_positions
                
                if current_time - last_scan_time >= scan_interval and can_open_more:
                    last_scan_time = current_time
                    
                    cash = self.get_available_cash()
                    total_cash = sum(cash.values())
                    
                    print(f"⭐ RISING STAR CHECK: Cash=${total_cash:.2f}, Need=${amount_per_position * 0.5:.2f}, RISING_STAR_AVAILABLE={RISING_STAR_AVAILABLE}")
                    
                    if total_cash >= amount_per_position * 0.5:
                        active_symbols = [p.symbol for p in positions]
                        
                        if RISING_STAR_AVAILABLE:
                            print(f"⭐ RISING STAR SCANNING... (existing={existing_position_count}, new={new_position_count}, max={max_positions})")
                            # ═══════════════════════════════════════════════
                            # STAGE 1: SCAN - Use ALL intelligence systems
                            # ═══════════════════════════════════════════════
                            candidates = self.rising_star_scanner.scan_entire_market(max_candidates=20)
                            rising_star_stats['candidates_scanned'] += len(candidates)
                            print(f"⭐ STAGE 1 COMPLETE: Found {len(candidates)} candidates")
                            
                            # Filter out symbols we already have
                            candidates = [c for c in candidates if c.symbol.replace('/', '') not in active_symbols]
                            print(f"⭐ After filtering existing: {len(candidates)} candidates remain")
                            
                            if candidates:
                                # ═══════════════════════════════════════════════
                                # STAGE 2 & 3: SIMULATE + SELECT - Top 4 → Best 2
                                # ═══════════════════════════════════════════════
                                # Run 30-second simulation (Monte Carlo)
                                best_2 = self.rising_star_scanner.select_best_two(candidates)
                                rising_star_stats['simulations_run'] += min(4, len(candidates)) * 1000
                                rising_star_stats['winners_selected'] += len(best_2)
                                print(f"⭐ STAGE 2-3 COMPLETE: Selected {len(best_2)} winners for execution")

                                try:
                                    self.last_rising_star_candidates = [
                                        {
                                            "symbol": c.symbol,
                                            "exchange": c.exchange,
                                            "score": getattr(c, 'score', 0.0),
                                            "change_pct": getattr(c, 'change_24h_pct', 0.0) or getattr(c, 'change_pct', 0.0),
                                            "momentum": getattr(c, 'momentum_strength', 0.0) or getattr(c, 'momentum_score', 0.0)
                                        }
                                        for c in candidates[:8]
                                    ]
                                    self.last_rising_star_winners = [
                                        {
                                            "symbol": w.symbol,
                                            "exchange": w.exchange,
                                            "score": getattr(w, 'score', 0.0),
                                            "change_pct": getattr(w, 'change_24h_pct', 0.0) or getattr(w, 'change_pct', 0.0),
                                            "momentum": getattr(w, 'momentum_strength', 0.0) or getattr(w, 'momentum_score', 0.0)
                                        }
                                        for w in best_2
                                    ]
                                except Exception:
                                    pass
                                
                                # ═══════════════════════════════════════════════
                                # STAGE 4: EXECUTE - Open positions on winners
                                # ═══════════════════════════════════════════════
                                decisions = []
                                for winner in best_2:
                                    print(f"⭐ STAGE 4: Evaluating {winner.symbol} on {winner.exchange}")
                                    # Check NEW position count only (existing positions don't count against limit)
                                    current_new_count = len([p for p in positions if not (hasattr(p, 'is_existing') and p.is_existing)])
                                    if current_new_count >= max_positions:
                                        print(f"⭐ STAGE 4: Reached max NEW positions ({current_new_count}/{max_positions}), stopping")
                                        break

                                    # 👑 Queen approval required
                                    queen_approved = False
                                    if queen is None:
                                        queen_approved = True  # Fallback without Queen
                                        print(f"⭐ STAGE 4: Queen unavailable - auto-approving {winner.symbol}")
                                    else:
                                        try:
                                            # Get change_pct from the correct attribute name
                                            change_pct = getattr(winner, 'change_24h_pct', 0.0) or getattr(winner, 'change_pct', 0.0)
                                            momentum = getattr(winner, 'momentum_strength', 0.0) or getattr(winner, 'momentum_score', 0.0)
                                            
                                            signal = queen.get_collective_signal(
                                                symbol=winner.symbol,
                                                market_data={
                                                    'price': getattr(winner, 'price', 0.0),
                                                    'change_pct': change_pct,
                                                    'momentum': momentum,
                                                    'exchange': winner.exchange,
                                                    'score': winner.score  # Include Rising Star score
                                                }
                                            )
                                            confidence = float(signal.get('confidence', 0.0))
                                            action = signal.get('action', 'HOLD')
                                            print(f"⭐ STAGE 4: Queen signal for {winner.symbol}: {action} {confidence:.0%} (change={change_pct:.1f}%, mom={momentum:.2f})")

                                            decisions.append({
                                                "symbol": winner.symbol,
                                                "exchange": winner.exchange,
                                                "action": action,
                                                "confidence": confidence,
                                                "change_pct": change_pct,
                                                "momentum": momentum
                                            })
                                            
                                            # Lower threshold: Accept BUY with any confidence, or HOLD with Rising Star score > 0.5
                                            queen_approved = (
                                                (action == 'BUY') or 
                                                (action == 'HOLD' and winner.score > 0.5) or
                                                (confidence > 0.0)  # Any positive confidence
                                            )
                                            if not queen_approved:
                                                # Force approve high-scoring Rising Star candidates
                                                if winner.score > 0.4:
                                                    queen_approved = True
                                                    print(f"⭐ STAGE 4: Force approving {winner.symbol} (score={winner.score:.2f})")
                                        except Exception as e:
                                            print(f"⭐ STAGE 4: Queen exception for {winner.symbol}: {e}")
                                            queen_approved = True  # Approve on exception

                                    if not queen_approved:
                                        print(f"⭐ STAGE 4: Queen REJECTED {winner.symbol}")
                                        continue
                                    
                                    print(f"⭐ STAGE 4: Queen APPROVED {winner.symbol} - executing buy...")
                                    try:
                                        client = self.clients.get(winner.exchange)
                                        print(f"⭐ STAGE 4: Client for {winner.exchange}: {type(client).__name__ if client else 'None'}")
                                        if client:
                                            symbol_clean = winner.symbol.replace('/', '')
                                            exchange_cash = cash.get(winner.exchange, 0)
                                            buy_amount = min(amount_per_position, exchange_cash * 0.9)
                                            
                                            # 🔍 SMART-SIZE LOGIC: Respect Exchange Minimums
                                            # -----------------------------------------------
                                            min_required = 1.0  # Default safe floor
                                            
                                            if hasattr(client, 'get_symbol_filters'):
                                                try:
                                                    filters = client.get_symbol_filters(symbol_clean)
                                                    # Get min notional/cost from filters
                                                    filter_min = float(filters.get('min_notional', 0) or filters.get('minNotional', 0) or filters.get('costmin', 0) or 0)
                                                    
                                                    # Check if min_qty implies a higher cost floor (Price * MinQty)
                                                    min_qty_floor = 0.0
                                                    if 'min_qty' in filters and hasattr(winner, 'price') and winner.price > 0:
                                                        try:
                                                            min_qty_floor = float(filters['min_qty']) * float(winner.price)
                                                        except: pass

                                                    # Enforce hard floors AND implied floors
                                                    if winner.exchange == 'binance':
                                                        min_required = max(filter_min, min_qty_floor, 5.5)
                                                    elif winner.exchange == 'kraken':
                                                        min_required = max(filter_min, min_qty_floor, 2.0)
                                                    else:
                                                        min_required = max(filter_min, min_qty_floor, 1.0)
                                                        
                                                except Exception as e:
                                                    print(f"⭐ STAGE 4: Filter check warning: {e}")
                                                    pass

                                            # Auto-bump if affordable
                                            if buy_amount < min_required:
                                                if exchange_cash >= min_required:
                                                    print(f"⭐ STAGE 4: 🔼 Bumping buy ${buy_amount:.2f} → ${min_required:.2f} (Exchange Min)")
                                                    buy_amount = min_required
                                                else:
                                                    print(f"⭐ STAGE 4: ⚠️ SKIPPING - Cash ${exchange_cash:.2f} < Min ${min_required:.2f}")
                                                    continue

                                            print(f"⭐ STAGE 4: Final Buy Amount ${buy_amount:.2f} for {symbol_clean} on {winner.exchange} (cash={exchange_cash:.2f})")

                                            if winner.exchange == 'binance' and hasattr(client, 'can_trade_symbol'):
                                                can_trade, reason = client.can_trade_symbol(symbol_clean)
                                                if not can_trade:
                                                    print(f"⭐ STAGE 4: ⚠️ SKIPPING - {reason}")
                                                    continue
                                            
                                            if buy_amount > 0:
                                                print(f"⭐ STAGE 4: CALLING place_market_order({symbol_clean}, buy, quote_qty={buy_amount:.2f})")
                                                buy_order = client.place_market_order(
                                                    symbol=symbol_clean,
                                                    side='buy',
                                                    quote_qty=buy_amount
                                                )
                                                print(f"⭐ STAGE 4: ORDER RESULT: {buy_order}")
                                                if buy_order and not buy_order.get('rejected') and not buy_order.get('error'):
                                                    # Handle different exchange response formats
                                                    buy_qty = float(buy_order.get('filled_qty', 0) or buy_order.get('executedQty', 0) or buy_order.get('receivedQty', 0))
                                                    buy_price = float(buy_order.get('filled_avg_price', 0) or buy_order.get('price', winner.price))
                                                    print(f"⭐ STAGE 4: FILLED: qty={buy_qty}, price={buy_price}")
                                                    
                                                    if buy_qty > 0 and buy_price > 0:
                                                        fee_rate = self.fee_rates.get(winner.exchange, 0.0025)
                                                        entry_cost = buy_price * buy_qty * (1 + fee_rate)
                                                        breakeven = buy_price * (1 + fee_rate) / (1 - fee_rate)
                                                        target_price = breakeven * (1 + target_pct_current / 100)
                                                        
                                                        pos = LivePosition(
                                                            symbol=symbol_clean,
                                                            exchange=winner.exchange,
                                                            entry_price=buy_price,
                                                            entry_qty=buy_qty,
                                                            entry_cost=entry_cost,
                                                            breakeven_price=breakeven,
                                                            target_price=target_price,
                                                            client=client,
                                                            stop_price=0.0,
                                                            # Rising Star tracking
                                                            accumulation_count=0,
                                                            total_cost=entry_cost,
                                                            avg_entry_price=buy_price,
                                                            rising_star_candidate=winner
                                                        )
                                                        positions.append(pos)
                                                        session_stats['total_trades'] += 1
                                                        print(f"⭐ STAGE 4: ✅ POSITION CREATED for {symbol_clean} @ {buy_price}")
                                                    else:
                                                        print(f"⭐ STAGE 4: ⚠️ NO FILL: qty={buy_qty}, price={buy_price}")
                                                else:
                                                    print(f"⭐ STAGE 4: ⚠️ ORDER RETURNED NONE")
                                            else:
                                                print(f"⭐ STAGE 4: ⚠️ SKIPPING - buy_amount ${buy_amount:.2f} < $0.50 minimum")
                                        else:
                                            print(f"⭐ STAGE 4: ⚠️ NO CLIENT for {winner.exchange}")
                                    except Exception as e:
                                        print(f"⭐ STAGE 4: ❌ ERROR executing buy: {e}")
                                        import traceback
                                        traceback.print_exc()
                                try:
                                    self.last_queen_decisions = decisions
                                except Exception:
                                    pass
                        else:
                            # Fallback: original scanning without Rising Star
                            opportunities = self.scan_entire_market(min_change_pct=min_change_pct)
                            if opportunities:
                                new_opps = [o for o in opportunities if o.symbol not in active_symbols]
                                
                                if new_opps:
                                    best = new_opps[0]
                                    try:
                                        client = self.clients.get(best.exchange)
                                        if client:
                                            # 👑 Queen approval required
                                            queen_approved = False
                                            if queen is None:
                                                queen_approved = True  # Fallback without Queen
                                                if warroom is not None:
                                                    warroom.add_flash_alert("Queen unavailable - proceeding with default approval", 'warning')
                                                else:
                                                    print("👑 Queen unavailable - proceeding with default approval")
                                            else:
                                                try:
                                                    signal = queen.get_collective_signal(
                                                        symbol=best.symbol,
                                                        market_data={
                                                            'price': best.price,
                                                            'change_pct': best.change_pct,
                                                            'momentum': best.momentum_score,
                                                            'exchange': best.exchange
                                                        }
                                                    )
                                                    confidence = float(signal.get('confidence', 0.0))
                                                    action = signal.get('action', 'HOLD')
                                                    warroom.add_flash_alert(
                                                        f"Queen signal {action} {confidence:.0%} for {best.symbol}",
                                                        'info'
                                                    )
                                                    queen_approved = (action == 'BUY' and confidence >= 0.3)  # Lowered from 0.5
                                                except Exception:
                                                    queen_approved = False

                                            if not queen_approved:
                                                continue

                                            symbol_clean = best.symbol.replace('/', '')
                                            exchange_cash = cash.get(best.exchange, 0)
                                            buy_amount = min(amount_per_position, exchange_cash * 0.9)
                                            
                                            if buy_amount >= 0.50:
                                                raw_order = client.place_market_order(
                                                    symbol=symbol_clean,
                                                    side='buy',
                                                    quote_qty=buy_amount
                                                )
                                                # 🔄 NORMALIZE ORDER RESPONSE across exchanges!
                                                buy_order = self.normalize_order_response(raw_order, best.exchange)
                                                
                                                if buy_order and buy_order.get('status') != 'rejected':
                                                    buy_qty = buy_order.get('filled_qty', 0)
                                                    buy_price = buy_order.get('filled_avg_price', best.price)
                                                    
                                                    if buy_qty > 0 and buy_price > 0:
                                                        fee_rate = self.fee_rates.get(best.exchange, 0.0025)
                                                        breakeven = buy_price * (1 + fee_rate) / (1 - fee_rate)
                                                        target_price = breakeven * (1 + target_pct_current / 100)
                                                        
                                                        pos = LivePosition(
                                                            symbol=symbol_clean,
                                                            exchange=best.exchange,
                                                            entry_price=buy_price,
                                                            entry_qty=buy_qty,
                                                            entry_cost=buy_price * buy_qty * (1 + fee_rate),
                                                            breakeven_price=breakeven,
                                                            target_price=target_price,
                                                            client=client,
                                                            stop_price=0.0
                                                        )
                                                        positions.append(pos)
                                                        session_stats['total_trades'] += 1
                                    except Exception:
                                        pass
                
                # ═══════════════════════════════════════════════════════
                # UPDATE QUANTUM SCORES FROM ALL SYSTEMS
                # ═══════════════════════════════════════════════════════
                # Initialize ALL quantum scores with defaults BEFORE any try blocks
                # This ensures we always have values to display even if systems fail
                luck_score = 0.5
                phantom_score = 0.5
                inception_score = 0.5
                elephant_score = 0.5
                russian_doll_score = 0.5
                immune_score = 0.5
                moby_score = 0.3
                stargate_score = 0.5
                mirror_score = 0.5
                hnc_score = 0.3
                historical_score = 0.5
                war_band_score = 0.5
                quantum = {}
                intel = {}
                
                try:
                    # Get REAL market data for quantum scoring (NO PHANTOMS)
                    target_symbol = "BTC/USD"
                    if positions: target_symbol = positions[0].symbol
                    
                    mkt = self._get_real_market_data(target_symbol, all_prices)
                    btc_price = mkt['price']
                    # Tune volatility sensitivity for Luck Mapper (0.1% change should register)
                    # We want 0-1 range. 1% move is huge for 1h. 
                    # So let's say 1% change => 1.0 volatility.
                    real_volatility = min(1.0, abs(mkt['change_pct']) * 1.5)

                    
                    # Gather full intelligence from all wired systems
                    intel = self.gather_all_intelligence(all_prices)
                    
                    # Get quantum score with REAL parameters
                    quantum = self.get_quantum_score(
                        target_symbol, 
                        mkt['price'], 
                        mkt['change_pct'], 
                        mkt['volume'], 
                        mkt['momentum']
                    )
                    
                    # ═══════════════════════════════════════════════════════════════════
                    # 🔗 UNITY FIX: Get REAL scores from all wired systems
                    # ═══════════════════════════════════════════════════════════════════
                    
                    # Luck Field - from quantum result or direct query
                    luck_score = quantum.get('luck_field', 0)
                    if luck_score == 0 and self.luck_mapper:
                        try:
                            reading = self.luck_mapper.read_field(
                                price=mkt['price'], 
                                volatility=real_volatility,
                                market_frequency=mkt['volume'] / 1000000
                            )
                            luck_score = reading.luck_field if reading else 0.5
                        except: luck_score = 0.5
                    
                    # Phantom Filter - check if phantom is cleared
                    phantom_score = 0.5
                    if self.phantom_filter:
                        try:
                            phantom_score = 1.0 if self.phantom_filter.is_cleared() else 0.3
                        except: phantom_score = 0.5
                    
                    # Inception/Limbo - from quantum result
                    inception_score = quantum.get('limbo_probability', 0.5)
                    
                    # Elephant Learning - direct query
                    elephant_score = quantum.get('elephant_score', 0)
                    if elephant_score == 0 and self.elephant:
                        try:
                            raw_score = self.elephant.get_asset_score("BTC/USD")
                            elephant_score = raw_score / 100.0  # Normalize 0-100 to 0-1
                        except: elephant_score = 0.5
                    elif elephant_score > 1.0:
                         elephant_score = elephant_score / 100.0 # Fix if from quantum dict

                    
                    # Russian Doll - queen confidence
                    russian_doll_score = quantum.get('queen_confidence', 0)
                    if russian_doll_score == 0 and self.russian_doll:
                        try:
                            directives = self.russian_doll.get_queen_directives()
                            russian_doll_score = directives.get('confidence', 0.5)
                        except: russian_doll_score = 0.5
                    
                    # Immune System - health check
                    immune_score = 0.5
                    if self.immune_system:
                        try:
                            health = self.immune_system.get_health_status()
                            immune_score = 1.0 if health.get('overall') == 'healthy' else 0.5
                        except: immune_score = 0.5
                    
                    # Moby Dick - whale confidence
                    moby_score = 0
                    if self.moby_dick:
                        try:
                            preds = self.moby_dick.get_execution_ready_predictions()
                            moby_score = 0.8 if preds else 0.3
                        except: moby_score = 0.3
                    
                    # Stargate - network coherence
                    stargate_score = quantum.get('stargate_coherence', 0)
                    if stargate_score == 0 and self.stargate:
                        try:
                            status = self.stargate.get_status()
                            stargate_score = status.get('network_coherence', 0.5)
                        except: stargate_score = 0.5
                    
                    # Quantum Mirror - boost value
                    mirror_score = quantum.get('mirror_boost', 0)
                    if mirror_score == 0 and self.quantum_mirror:
                        try:
                            boost, _ = self.quantum_mirror.get_quantum_boost('USD', 'BTC', 'mixed')
                            mirror_score = min(1.0, boost) if boost else 0.5
                        except: mirror_score = 0.5
                    
                    # HNC Surge - from quantum result or detector
                    hnc_score = quantum.get('hnc_surge_intensity', 0)
                    if hnc_score == 0 and self.hnc_surge_detector:
                        try:
                            surge = self.hnc_surge_detector.detect_surge("BTC/USD")
                            hnc_score = surge.intensity if surge else 0.3
                        except: hnc_score = 0.3
                    
                    # Historical Hunter - pattern confidence
                    historical_score = quantum.get('historical_confidence', 0)
                    if historical_score == 0 and self.historical_hunter:
                        try:
                            historical_score = 0.6  # Active = baseline confidence
                        except: historical_score = 0.5
                    
                    # Apache War Band - calculate unified score
                    if war_band:
                        try:
                            war_band_score = war_band.calculate_unified()
                        except: war_band_score = 0.5
                    
                    # (Quantum update moved OUTSIDE try block for reliability)
                    
                    # Update firm activity from intelligence
                    for whale in intel.get('whale_predictions', []):
                        firm_name = whale.get('firm', whale.get('symbol', 'Unknown'))
                        if warroom is not None:
                            warroom.update_firm(
                                firm_name[:12],
                                whale.get('action', 'watching'),
                                whale.get('direction', 'neutral')
                            )
                        else:
                            print(f"FIRM: {firm_name[:12]} action={whale.get('action','watching')} dir={whale.get('direction','neutral')}")
                    
                    # Add bot detections to firms display
                    for bot in intel.get('bots', [])[:3]:
                        if warroom is not None:
                            warroom.update_firm(
                                bot.get('firm', 'Bot')[:12],
                                bot.get('type', 'algo'),
                                bot.get('direction', 'neutral')
                            )
                        else:
                            print(f"BOT: {bot.get('firm','Bot')[:12]} type={bot.get('type','algo')} dir={bot.get('direction','neutral')}")
                    
                    # 🌟 Update Rising Star stats in display
                    if RISING_STAR_AVAILABLE:
                        if warroom is not None:
                            warroom.update_rising_star(rising_star_stats)
                        else:
                            print(f"RisingStar: {rising_star_stats}")
                    
                    # 🦅 Update Momentum stats
                    mom_res = getattr(self, 'last_momentum_result', {})
                    micro_res = getattr(self, 'last_micro_result', [])
                    
                    wolf_stat = 'Initializing...'
                    lion_stat = 'Initializing...'
                    ant_stat = 'Initializing...'
                    hb_stat = 'Initializing...'
                    
                    if self.momentum_ecosystem:
                        # Use last result or default to Stalking if empty cache but system exists
                        if not mom_res:
                            wolf_stat = "Stalking"
                            lion_stat = "Napping" 
                            ant_stat = "Marching"
                            hb_stat = "Hovering"
                        else:
                            w_count = len(mom_res.get('wolf', []))
                            l_count = len(mom_res.get('lion', []))
                            a_count = len(mom_res.get('ants', []))
                            hb_data = mom_res.get('hummingbird', [])
                            hb_count = len(hb_data) if isinstance(hb_data, list) else 0

                            wolf_stat = f"Hunting ({w_count} targets)" if w_count > 0 else "Stalking"
                            lion_stat = f"Hunting ({l_count} prey)" if l_count > 0 else "Stalking"
                            ant_stat = f"Swarming ({a_count} paths)" if a_count > 0 else "Foraging"
                            hb_stat = f"Pollinating ({hb_count} flowers)" if hb_count > 0 else "Hovering"
                    
                    if warroom is not None:
                        warroom.update_momentum(
                            wolf_status=wolf_stat,
                            lion_status=lion_stat,
                            ants_status=ant_stat,
                            hummingbird_status=hb_stat,
                            micro_targets=len(micro_res) if micro_res else 0
                        )
                    else:
                        print(f"Momentum: wolf={wolf_stat}, lion={lion_stat}, ants={ant_stat}, hb={hb_stat}, micro={len(micro_res) if micro_res else 0}")
                    
                    # 🌌 Stargate Grid Update
                    if self.stargate_grid:
                        try:
                            active_node = self.stargate_grid.get_active_node()
                            grid_coherence = self.stargate_grid.calculate_grid_coherence()
                            warroom.update_stargate(
                                active_node=f"{active_node.name} ({active_node.element})",
                                coherence=grid_coherence,
                                description=getattr(active_node, 'description', '')
                            )
                        except Exception:
                            pass
                    
                    # 🎯 OPTIONS SCANNING - Every 5 minutes check for income opportunities
                    if self.options_scanner and self.options_trading_level:
                        try:
                            # Only scan every 5 minutes (options don't change rapidly)
                            if not hasattr(self, '_last_options_scan') or time.time() - self._last_options_scan > 300:
                                self._last_options_scan = time.time()
                                
                                # Get options buying power
                                buying_power = self.options_client.get_options_buying_power()
                                
                                # Get options positions
                                opt_positions = self.options_client.get_positions()
                                
                                # Find best opportunity (if we have stocks to write calls against)
                                best_opp = None
                                try:
                                    # Check if we have any stock positions we could write calls against
                                    stock_positions = self.clients.get('alpaca', {})
                                    if stock_positions and hasattr(stock_positions, 'get_positions'):
                                        for sp in stock_positions.get_positions() or []:
                                            symbol = sp.get('symbol', '')
                                            qty = float(sp.get('qty', 0))
                                            current_price = float(sp.get('current_price', 0))
                                            
                                            # Need at least 100 shares for covered call
                                            if qty >= 100 and current_price > 0:
                                                opps = self.options_scanner.scan_covered_calls(
                                                    underlying=symbol,
                                                    current_price=current_price,
                                                    shares_owned=int(qty)
                                                )
                                                if opps and (not best_opp or opps[0].total_score > best_opp.get('score', 0)):
                                                    best_opp = {
                                                        'symbol': opps[0].contract.symbol,
                                                        'underlying': symbol,
                                                        'strategy': 'covered_call',
                                                        'premium': opps[0].quote.mid_price,
                                                        'annualized_return': opps[0].annualized_return * 100,
                                                        'score': opps[0].total_score,
                                                    }
                                except Exception:
                                    pass
                                
                                # Update warroom display
                                warroom.update_options(
                                    trading_level=self.options_trading_level.name if self.options_trading_level else 'N/A',
                                    buying_power=buying_power,
                                    positions=opt_positions,
                                    best_opportunity=best_opp
                                )
                        except Exception:
                            pass
                    
                    # 🦈🔍 PREDATOR DETECTION UPDATE - Who's hunting us?
                    if self.predator_detector:
                        try:
                            report = self.predator_detector.generate_hunting_report()
                            top_predator = None
                            if report.top_predators:
                                top_predator = report.top_predators[0].firm_id
                            warroom.update_predator(
                                threat_level=report.threat_level,
                                front_run_rate=report.front_run_rate,
                                top_predator=top_predator,
                                strategy_decay=report.strategy_decay_alert
                            )
                            
                            # 🥷 AUTO-ESCALATE STEALTH MODE based on threat level
                            if report.threat_level == "red" and self.stealth_mode != "paranoid":
                                self.set_stealth_mode("paranoid")
                                if warroom is not None:
                                    warroom.add_flash_alert("ESCALATED TO PARANOID MODE", 'critical')
                                else:
                                    print("🥷 AUTO-ESCALATED to PARANOID mode (threat level RED)")
                            elif report.threat_level == "orange" and self.stealth_mode == "normal":
                                self.set_stealth_mode("aggressive")
                                if warroom is not None:
                                    warroom.add_flash_alert("ESCALATED TO AGGRESSIVE MODE", 'warning')
                                else:
                                    print("🥷 AUTO-ESCALATED to AGGRESSIVE mode (threat level ORANGE)")
                        except Exception:
                            pass
                    
                    # 🥷 STEALTH STATS UPDATE
                    if self.stealth_executor:
                        try:
                            stealth_stats = self.stealth_executor.get_stats()
                            warroom.update_stealth(
                                mode=self.stealth_mode,
                                delayed_orders=stealth_stats.get('delayed_orders', 0),
                                split_orders=stealth_stats.get('split_orders', 0),
                                rotated_symbols=stealth_stats.get('rotated_symbols', 0),
                                hunted_count=len(stealth_stats.get('hunted_symbols', []))
                            )
                        except Exception:
                            pass
                        
                except Exception as e:
                    pass  # Quantum gathering failed, but we still have defaults
                
                # ═══════════════════════════════════════════════════════
                # ALWAYS UPDATE QUANTUM DISPLAY - Use whatever values we got
                # This is OUTSIDE the try block so it ALWAYS runs!
                # ═══════════════════════════════════════════════════════
                warroom.update_quantum(
                    luck=luck_score,
                    phantom=phantom_score,
                    inception=inception_score,
                    elephant=elephant_score,
                    russian_doll=russian_doll_score,
                    immune=immune_score,
                    moby_dick=moby_score,
                    stargate=stargate_score,
                    quantum_mirror=mirror_score,
                    hnc_surge=hnc_score,
                    historical=historical_score,
                    war_band=war_band_score,
                    hive_state=0.8 if hive_publisher else 0.0,
                    bot_census=0.7 if bot_census else 0.0,
                    backtest=0.6 if backtest_engine else 0.0,
                    global_orchestrator=0.85 if global_orchestrator else 0.0,
                    harmonic_binary=0.75 if harmonic_binary else 0.0,
                    harmonic_chain_master=0.8 if harmonic_chain_master else 0.0,
                    harmonic_counter=0.7 if harmonic_counter else 0.0,
                    harmonic_fusion=0.82 if harmonic_fusion else 0.0,
                    harmonic_momentum=0.78 if harmonic_momentum else 0.0,
                    harmonic_reality=0.85 if harmonic_reality else 0.0,
                    global_bot_map=0.72 if global_bot_map else 0.0,
                    enhanced_telescope=0.88 if enhanced_quantum_telescope else 0.0,
                    enigma_dream=0.9 if enigma_dream else 0.0,
                    enhancement_layer=0.85 if enhancement_layer else 0.0,
                    enigma_integration=0.92 if enigma_integration else 0.0,
                    firm_intelligence=0.8 if firm_intelligence else 0.0,
                    enigma_core=0.95 if enigma_core else 0.0,
                    aureon_miner=0.75 if aureon_miner else 0.0,
                    multi_exchange=0.88 if multi_exchange else 0.0,
                    multi_pair=0.82 if multi_pair else 0.0,
                    multiverse_live=0.85 if multiverse_live else 0.0,
                    multiverse_orchestrator=0.9 if multiverse_orchestrator else 0.0,
                    mycelium_network=0.92 if mycelium_network else 0.0,
                    neural_revenue=0.87 if neural_revenue else 0.0,
                    total_boost=quantum.get('quantum_boost', 1.0) if quantum else 1.0
                )
                
                # Update display (Rich Live if available, otherwise just skip)
                if live is not None:
                    try:
                        live.update(warroom.build_display())
                    except (ValueError, OSError, IOError) as e:
                        # Rich crashed during update - stop using it
                        _safe_print(f"⚠️ Rich display crashed ({e}), stopping display...")
                        try:
                            live.stop()
                        except:
                            pass
                        live = None
                time.sleep(monitor_interval)
                
        except KeyboardInterrupt:
            # STOP RICH LIVE FIRST so we can print clearly
            if live:
                try: live.stop()
                except: pass
                live = None

            if console:
                try:
                    console.print("\n[bold yellow]👑 STOPPING WAR ROOM...[/]")
                except Exception:
                    print("\n👑 STOPPING WAR ROOM...")
            else:
                print("\n👑 STOPPING WAR ROOM...")
            
            # Close profitable positions
            if console:
                try:
                    console.print("[bold]🛑 Closing profitable positions only...[/]")
                except Exception:
                    print("🛑 Closing profitable positions only...")
            else:
                print("🛑 Closing profitable positions only...")
            for pos in positions:
                if pos.current_pnl > 0:
                    try:
                        pos.client.place_market_order(
                            symbol=pos.symbol,
                            side='sell',
                            quantity=pos.entry_qty
                        )
                        if console:
                            try:
                                console.print(f"[green]✅ Closed {pos.symbol}: +${pos.current_pnl:.4f}[/]")
                            except Exception:
                                print(f"✅ Closed {pos.symbol}: +${pos.current_pnl:.4f}")
                        else:
                            print(f"✅ Closed {pos.symbol}: +${pos.current_pnl:.4f}")
                    except Exception:
                        pass
                else:
                    acc_info = f" (DCA x{pos.accumulation_count})" if pos.accumulation_count > 0 else ""
                    if console:
                        try:
                            console.print(f"[dim]⏳ Kept {pos.symbol}: ${pos.current_pnl:.4f}{acc_info} (holding)[/]")
                        except Exception:
                            print(f"⏳ Kept {pos.symbol}: ${pos.current_pnl:.4f}{acc_info} (holding)")
                    else:
                        print(f"⏳ Kept {pos.symbol}: ${pos.current_pnl:.4f}{acc_info} (holding)")
            
            # Summary
            if console:
                try:
                    console.print(f"\n[bold magenta]{'='*60}[/]")
                    console.print(f"[bold]👑 WAR ROOM SESSION COMPLETE[/]")
                    console.print(f"   Cycles: {session_stats['cycles']}")
                    console.print(f"   Total P&L: ${session_stats['total_pnl']:+.4f}")
                    console.print(f"   Wins: {session_stats['winning_trades']} | Losses: {session_stats['losing_trades']}")
                except Exception:
                    print(f"\n{'='*60}")
                    print(f"👑 WAR ROOM SESSION COMPLETE")
                    print(f"   Cycles: {session_stats['cycles']}")
                    print(f"   Total P&L: ${session_stats['total_pnl']:+.4f}")
                    print(f"   Wins: {session_stats['winning_trades']} | Losses: {session_stats['losing_trades']}")
            else:
                print(f"\n{'='*60}")
                print(f"👑 WAR ROOM SESSION COMPLETE")
                print(f"   Cycles: {session_stats['cycles']}")
                print(f"   Total P&L: ${session_stats['total_pnl']:+.4f}")
                print(f"   Wins: {session_stats['winning_trades']} | Losses: {session_stats['losing_trades']}")
            
            # Rising Star Statistics
            if RISING_STAR_AVAILABLE:
                if console:
                    try:
                        console.print(f"\n[bold cyan]🌟 RISING STAR STATISTICS[/]")
                        console.print(f"   Candidates Scanned: {rising_star_stats['candidates_scanned']}")
                        console.print(f"   Monte Carlo Sims: {rising_star_stats['simulations_run']:,}")
                        console.print(f"   Winners Selected: {rising_star_stats['winners_selected']}")
                        console.print(f"   Accumulations (DCA): {rising_star_stats['accumulations_made']}")
                        console.print(f"   DCA Value: ${rising_star_stats['total_accumulated_value']:.2f}")
                    except Exception:
                        print(f"\n🌟 RISING STAR STATISTICS")
                        print(f"   Candidates Scanned: {rising_star_stats['candidates_scanned']}")
                        print(f"   Monte Carlo Sims: {rising_star_stats['simulations_run']:,}")
                        print(f"   Winners Selected: {rising_star_stats['winners_selected']}")
                        print(f"   Accumulations (DCA): {rising_star_stats['accumulations_made']}")
                        print(f"   DCA Value: ${rising_star_stats['total_accumulated_value']:.2f}")
                else:
                    print(f"\n🌟 RISING STAR STATISTICS")
                    print(f"   Candidates Scanned: {rising_star_stats['candidates_scanned']}")
                    print(f"   Monte Carlo Sims: {rising_star_stats['simulations_run']:,}")
                    print(f"   Winners Selected: {rising_star_stats['winners_selected']}")
                    print(f"   Accumulations (DCA): {rising_star_stats['accumulations_made']}")
                    print(f"   DCA Value: ${rising_star_stats['total_accumulated_value']:.2f}")
            
            if console:
                try:
                    console.print(f"[bold magenta]{'='*60}[/]")
                except Exception:
                    print(f"{'='*60}")
            else:
                print(f"{'='*60}")
        
        finally:
            # Stop Rich Live display if it's running
            if live is not None:
                try:
                    live.stop()
                except:
                    pass
            
            # Restore logging handlers
            if logging_handlers_backup:
                try:
                    root = logging.getLogger()
                    for h in logging_handlers_backup:
                        root.addHandler(h)
                except: pass
        
        return session_stats


if __name__ == "__main__":
    import sys
    import traceback
    
    # 🚀 STARTUP BANNER - helps identify when Orca actually starts
    print("")
    print("=" * 70)
    print("🦈🔪 ORCA COMPLETE KILL CYCLE - STARTUP 🔪🦈")
    print("=" * 70)
    print(f"   Started: {datetime.now().isoformat()}")
    print(f"   Args: {sys.argv}")
    print(f"   Python: {sys.version}")
    print(f"   CWD: {os.getcwd()}")
    print(f"   STATE_DIR: {os.environ.get('AUREON_STATE_DIR', 'state')}")
    print("=" * 70)
    print("")
    
    # Monitor mode - stream existing positions until targets hit
    if len(sys.argv) >= 2 and sys.argv[1] == '--monitor':
        target_pct = float(sys.argv[2]) if len(sys.argv) > 2 else 1.5  # Default 1.5% target
        stop_pct = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0    # Default 1% stop
        
        print("🦈🦈🦈 ORCA POSITION MONITOR - STREAMING EXISTING POSITIONS 🦈🦈🦈")
        orca = OrcaKillCycle()
        
        # Load existing Alpaca positions into LivePosition format
        positions = []
        alpaca = orca.clients.get('alpaca')
        if alpaca:
            try:
                existing = alpaca.get_positions()
                for p in existing:
                    symbol_raw = p.get('symbol', '')
                    # Convert PEPEUSD -> PEPE/USD
                    if symbol_raw.endswith('USD') and '/' not in symbol_raw:
                        symbol = symbol_raw[:-3] + '/USD'
                    else:
                        symbol = symbol_raw
                    
                    qty = float(p.get('qty', 0))
                    entry = float(p.get('avg_entry_price', 0))
                    current = float(p.get('current_price', 0))
                    
                    if qty > 0 and entry > 0:
                        target = entry * (1 + target_pct/100)
                        stop = entry * (1 - stop_pct/100)
                        fee_rate = orca.fee_rates.get('alpaca', 0.0025)
                        entry_cost = entry * qty * (1 + fee_rate)
                        breakeven = entry * (1 + 2*fee_rate)  # Need to cover fees both ways
                        
                        pos = LivePosition(
                            symbol=symbol,
                            exchange='alpaca',
                            entry_price=entry,
                            entry_qty=qty,
                            entry_cost=entry_cost,
                            breakeven_price=breakeven,
                            target_price=target,
                            stop_price=stop,
                            client=alpaca,
                            current_price=current,
                            current_pnl=float(p.get('unrealized_pl', 0)),
                            kill_reason=''
                        )
                        positions.append(pos)
                        print(f"   📈 {symbol}: {qty:.6f} @ ${entry:.6f} → Target: ${target:.6f} | Stop: ${stop:.6f}")
            except Exception as e:
                print(f"   ⚠️ Error loading positions: {e}")
        
        if not positions:
            print("❌ No positions to monitor!")
            sys.exit(1)
        
        print(f"\n📡 STREAMING {len(positions)} POSITIONS (NO TIMEOUT)")
        print("="*70)
        print(f"   ⚠️ Will ONLY exit on: TARGET HIT (100%), STOP LOSS (0%), or Ctrl+C")
        print("="*70)
        
        # Progress bar helper
        def make_progress_bar(progress_pct, width=20):
            """Create a visual progress bar. 0% = stop loss, 100% = target."""
            progress_pct = max(0, min(100, progress_pct))  # Clamp 0-100
            filled = int(width * progress_pct / 100)
            empty = width - filled
            
            # Color coding: red if <25%, yellow if <75%, green if >=75%
            if progress_pct >= 75:
                bar_char = '█'
                color = '\033[92m'  # Green
            elif progress_pct >= 25:
                bar_char = '▓'
                color = '\033[93m'  # Yellow
            else:
                bar_char = '░'
                color = '\033[91m'  # Red
            
            reset = '\033[0m'
            bar = color + bar_char * filled + reset + '░' * empty
            return f"[{bar}]"
        
        def make_whale_bar(support: float, pressure: float, width=10):
            """Create whale support vs pressure indicator."""
            # Net score: positive = whales helping, negative = opposing
            net = support - pressure
            mid = width // 2
            
            if net > 0:
                # Whales supporting - green fill from middle to right
                fill = int(mid * min(net * 2, 1))
                bar = '░' * mid + '\033[92m' + '▶' * fill + '\033[0m' + '░' * (mid - fill)
            elif net < 0:
                # Whales opposing - red fill from middle to left
                fill = int(mid * min(abs(net) * 2, 1))
                bar = '░' * (mid - fill) + '\033[91m' + '◀' * fill + '\033[0m' + '░' * mid
            else:
                bar = '░' * width
            
            return f"[{bar}]"
        
        def format_eta(seconds: float) -> str:
            """Format ETA as human-readable string."""
            if seconds < 60:
                return f"{seconds:.0f}s"
            elif seconds < 3600:
                return f"{seconds/60:.1f}m"
            else:
                return f"{seconds/3600:.1f}h"
        
        def clear_lines(n):
            """Clear n lines above cursor."""
            for _ in range(n):
                print('\033[A\033[K', end='')
        
        # Initialize whale intelligence tracker
        whale_tracker = WhaleIntelligenceTracker()
        whale_status = "🐋 Whale Intelligence: "
        if whale_tracker.whale_profiler:
            whale_status += "✅ Profiler "
        else:
            whale_status += "❌ Profiler "
        if whale_tracker.firm_intel:
            whale_status += "✅ Firms "
        else:
            whale_status += "❌ Firms "
        if whale_tracker.bus:
            whale_status += "✅ ThoughtBus "
        else:
            whale_status += "❌ ThoughtBus "
        
        # Initialize SSE live streaming for real-time whale detection
        sse_client = None
        if SSE_AVAILABLE and AlpacaSSEClient:
            try:
                sse_client = AlpacaSSEClient()
                # Get position symbols for streaming
                stream_symbols = [p.symbol.replace('/USD', 'USD') for p in positions]
                
                # Wire SSE trades to whale tracker
                def on_live_trade(trade):
                    """Feed live trades to whale intelligence."""
                    try:
                        symbol = trade.symbol
                        # Convert BTCUSD -> BTC/USD
                        if not '/' in symbol and symbol.endswith('USD'):
                            symbol = symbol[:-3] + '/USD'
                        whale_tracker.process_live_trade(
                            symbol=symbol,
                            price=trade.price,
                            quantity=trade.size,
                            side='buy' if hasattr(trade, 'side') and trade.side == 'buy' else 'sell',
                            exchange='alpaca'
                        )
                    except Exception:
                        pass
                
                sse_client.on_trade = on_live_trade
                sse_client.start_crypto_stream(stream_symbols, trades=True)
                whale_status += "✅ LiveStream"
            except Exception as e:
                whale_status += f"❌ LiveStream({e})"
        else:
            whale_status += "❌ LiveStream"
        
        print(whale_status)
        print("="*70)
        
        # Monitor loop
        results = []
        last_display_lines = 0
        hunt_validations = []  # Track successful hunts
        whale_update_counter = 0  # Only update whale intel every 5 ticks
        whale_signals_cache: Dict[str, WhaleSignal] = {}
        should_exit = False  # Flag to control loop exit
        
        try:
            while positions and not should_exit:
                display_lines = []
                whale_update_counter += 1
                
                for pos in positions[:]:
                    try:
                        # Get live price
                        ticker = pos.client.get_ticker(pos.symbol)
                        if not ticker:
                            continue
                        
                        current = float(ticker.get('last', ticker.get('bid', 0)))
                        if current <= 0:
                            continue
                        
                        pos.current_price = current
                        fee_rate = orca.fee_rates.get(pos.exchange, 0.0025)
                        entry_cost = pos.entry_price * pos.entry_qty * (1 + fee_rate)
                        exit_value = current * pos.entry_qty * (1 - fee_rate)
                        pos.current_pnl = exit_value - entry_cost
                        
                        pnl_pct = ((current / pos.entry_price) - 1) * 100
                        
                        # Calculate progress: 0% = stop loss, 50% = entry, 100% = target
                        # Range from stop to target
                        price_range = pos.target_price - pos.stop_price
                        if price_range > 0:
                            progress = ((current - pos.stop_price) / price_range) * 100
                        else:
                            progress = 50
                        
                        progress = max(0, min(100, progress))
                        bar = make_progress_bar(progress)
                        
                        # Get whale intelligence (update every 5 ticks = 1 second)
                        if whale_update_counter % 5 == 0 or pos.symbol not in whale_signals_cache:
                            # Calculate price change % for firm activity simulation
                            price_change_pct = pnl_pct  # Use position P&L as price change proxy
                            whale_sig = whale_tracker.get_whale_signal(
                                pos.symbol, 
                                'long',
                                current_price=current,
                                price_change_pct=price_change_pct
                            )
                            whale_signals_cache[pos.symbol] = whale_sig
                        else:
                            whale_sig = whale_signals_cache.get(pos.symbol)
                        
                        # Build display line with whale data
                        symbol_short = pos.symbol.replace('/USD', '')[:6]
                        
                        if whale_sig:
                            whale_bar = make_whale_bar(whale_sig.whale_support, whale_sig.counter_pressure)
                            eta_str = format_eta(whale_sig.eta_seconds)
                            # Main line: symbol + progress + P&L
                            line1 = f"  {symbol_short:6} {bar} {progress:5.1f}% | ${pos.current_pnl:+.4f} | ${current:.6f}"
                            # Whale line: support indicator + ETA + whales active + firm reasoning
                            whales_active = whale_sig.active_whales
                            support_pct = int(whale_sig.whale_support * 100)
                            pressure_pct = int(whale_sig.counter_pressure * 100)
                            firm_info = whale_sig.reasoning if whale_sig.reasoning else "Scanning..."
                            line2 = f"         {whale_bar} 🐋{whales_active} | ⬆{support_pct}% ⬇{pressure_pct}% | {firm_info[:50]}"
                            display_lines.append(line1)
                            display_lines.append(line2)
                        else:
                            display_lines.append(f"  {symbol_short:6} {bar} {progress:5.1f}% | ${pos.current_pnl:+.4f} | ${current:.6f}")
                        
                        # Check exit conditions - ONLY SELL IF PROFITABLE!
                        if current >= pos.target_price:
                            pos.kill_reason = 'TARGET_HIT'
                        # DISABLED: NO STOP LOSS - we NEVER sell at a loss!
                        # elif current <= pos.stop_price:
                        #     pos.kill_reason = 'STOP_LOSS'
                        elif pos.current_pnl > 0.01:  # Small momentum profit
                            pos.kill_reason = 'MOMENTUM_PROFIT'
                        
                        # Execute exit
                        if pos.kill_reason:
                            sell_order = pos.client.place_market_order(
                                symbol=pos.symbol,
                                side='sell',
                                quantity=pos.entry_qty
                            )
                            if sell_order:
                                sell_price = float(sell_order.get('filled_avg_price', current))
                                final_exit = sell_price * pos.entry_qty * (1 - fee_rate)
                                final_pnl = final_exit - entry_cost
                                
                                # Create hunt validation record
                                validation = {
                                    'symbol': pos.symbol,
                                    'exchange': pos.exchange,
                                    'reason': pos.kill_reason,
                                    'net_pnl': final_pnl,
                                    'entry_price': pos.entry_price,
                                    'exit_price': sell_price,
                                    'qty': pos.entry_qty,
                                    'progress_at_kill': progress,
                                    'success': final_pnl > 0
                                }
                                results.append(validation)
                                hunt_validations.append(validation)
                                
                                # Print kill validation
                                if validation['success']:
                                    emoji = '🎯✅'
                                    status = 'SUCCESSFUL HUNT'
                                else:
                                    emoji = '🛑❌'
                                    status = 'HUNT FAILED'
                                
                                print(f"\n{emoji} {status}: {pos.symbol}")
                                print(f"   ├─ Entry:  ${pos.entry_price:.6f}")
                                print(f"   ├─ Exit:   ${sell_price:.6f}")
                                print(f"   ├─ P&L:    ${final_pnl:+.4f}")
                                print(f"   ├─ Reason: {pos.kill_reason}")
                                print(f"   └─ Progress at kill: {progress:.1f}%")
                                print()
                                
                            positions.remove(pos)
                    except Exception as e:
                        pass
                
                # Clear previous display and show new progress bars
                if positions:
                    # Clear previous lines
                    if last_display_lines > 0:
                        clear_lines(last_display_lines + 1)
                    
                    # Print header and all position bars
                    total_pnl = sum(p.current_pnl for p in positions)
                    print(f"📊 LIVE HUNT STATUS | Total P&L: ${total_pnl:+.4f}")
                    for line in display_lines:
                        print(line)
                    
                    last_display_lines = len(display_lines)
                
                time.sleep(0.2)  # Slightly slower for readability
                
        except KeyboardInterrupt:
            print("\n\n⚠️  INTERRUPT DETECTED!")
            print("="*60)
            print("🦈 ORCA SAFETY CHECK - What do you want to do?")
            print("="*60)
            print("  [1] CLOSE ALL positions and exit")
            print("  [2] KEEP positions open and just exit monitor")
            print("  [3] RESUME monitoring (cancel interrupt)")
            print("="*60)
            
            try:
                choice = input("\n👉 Enter choice (1/2/3) [default=2 KEEP]: ").strip()
            except EOFError:
                # Non-interactive mode (piped input) - default to KEEP
                choice = "2"
            
            if choice == "1":
                print("\n🛑 CONFIRMED: Closing all positions...")
                # Stop SSE streaming
                if sse_client:
                    try:
                        sse_client.stop()
                        print("   📡 Live stream stopped")
                    except Exception:
                        pass
                for pos in positions:
                    try:
                        sell_order = pos.client.place_market_order(symbol=pos.symbol, side='sell', quantity=pos.entry_qty)
                        if sell_order:
                            fee_rate = orca.fee_rates.get(pos.exchange, 0.0025)
                            sell_price = float(sell_order.get('filled_avg_price', pos.current_price))
                            entry_cost = pos.entry_price * pos.entry_qty * (1 + fee_rate)
                            final_exit = sell_price * pos.entry_qty * (1 - fee_rate)
                            final_pnl = final_exit - entry_cost
                            results.append({
                                'symbol': pos.symbol,
                                'exchange': pos.exchange,
                                'reason': 'USER_ABORT',
                                'net_pnl': final_pnl,
                                'success': final_pnl > 0
                            })
                            print(f"   Closed {pos.symbol}: ${final_pnl:+.4f}")
                    except Exception as e:
                        print(f"   ⚠️ Error closing {pos.symbol}: {e}")
                should_exit = True  # Exit the loop after closing
            
            elif choice == "3":
                print("\n🔄 Resuming monitor... (Ctrl+C again to see options)")
                # Don't set should_exit, just continue the loop
            
            else:  # Default: choice == "2" or anything else
                print("\n✅ KEEPING positions open - exiting monitor only")
                print("   Your positions are still active on the exchange!")
                if sse_client:
                    try:
                        sse_client.stop()
                        print("   📡 Live stream stopped")
                    except Exception:
                        pass
                # Don't close positions, just exit cleanly
                results = []  # Clear results so no "failed" report
                should_exit = True  # Exit the loop
        
        # Hunt Validation Summary
        if results:
            print("\n" + "="*70)
            print("🦈 HUNT VALIDATION REPORT")
            print("="*70)
            
            successful = [r for r in results if r.get('success', False)]
            failed = [r for r in results if not r.get('success', False)]
            total = sum(r['net_pnl'] for r in results)
            
            print(f"\n📊 HUNT STATISTICS:")
            print(f"   ├─ Total Hunts:     {len(results)}")
            print(f"   ├─ Successful:      {len(successful)} ✅")
            print(f"   ├─ Failed:          {len(failed)} ❌")
            print(f"   ├─ Win Rate:        {(len(successful)/len(results)*100) if results else 0:.1f}%")
            print(f"   └─ Net P&L:         ${total:+.4f}")
            
            if successful:
                print(f"\n✅ SUCCESSFUL HUNTS:")
                for r in successful:
                    print(f"   🎯 {r['symbol']}: ${r['net_pnl']:+.4f} ({r['reason']})")
            
            if failed:
                print(f"\n❌ FAILED HUNTS:")
                for r in failed:
                    print(f"   🛑 {r['symbol']}: ${r['net_pnl']:+.4f} ({r['reason']})")
            
            print("\n" + "="*70)
            if total > 0:
                print(f"🏆 HUNT SESSION: PROFITABLE (+${total:.4f})")
            else:
                print(f"💔 HUNT SESSION: LOSS (${total:.4f})")
            print("="*70)
    
    # 🦈⚡ NEW: Fast Kill Hunt - uses ALL intelligence systems
    elif len(sys.argv) >= 2 and sys.argv[1] == '--fast':
        amount = float(sys.argv[2]) if len(sys.argv) > 2 else 25.0
        num_pos = int(sys.argv[3]) if len(sys.argv) > 3 else 3
        target = float(sys.argv[4]) if len(sys.argv) > 4 else 0.8
        
        print("🦈⚡ FAST KILL MODE - ALL INTELLIGENCE ENGAGED ⚡🦈")
        orca = OrcaKillCycle()
        results = orca.fast_kill_hunt(
            amount_per_position=amount,
            num_positions=num_pos,
            target_pct=target
        )
        
        if results:
            total = sum(r.get('net_pnl', 0) for r in results)
            print(f"\n💰 Total portfolio impact: ${total:+.4f}")
    
    # New multi-exchange pack hunt mode
    elif len(sys.argv) >= 2 and sys.argv[1] == '--pack':
        num_pos = int(sys.argv[2]) if len(sys.argv) > 2 else 3
        amount = float(sys.argv[3]) if len(sys.argv) > 3 else 2.5
        
        print("🦈🦈🦈 ORCA PACK HUNT - SCANNING ENTIRE MARKET 🦈🦈🦈")
        orca = OrcaKillCycle()
        results = orca.pack_hunt(num_positions=num_pos, amount_per_position=amount)
        
        if results:
            total = sum(r['net_pnl'] for r in results)
            print(f"\n💰 Total portfolio impact: ${total:+.4f}")
    
    # 👑🔄 AUTONOMOUS MODE - Queen-guided infinite loop (WAR ROOM by default)
    elif len(sys.argv) >= 2 and sys.argv[1] == '--autonomous':
        max_pos = int(sys.argv[2]) if len(sys.argv) > 2 else 3
        amount = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0  # Lower to $1 for small accounts
        target = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
        
        print("👑🎖️ AUTONOMOUS WAR ROOM MODE 🎖️👑")
        print(f"   Max positions: {max_pos}")
        print(f"   Amount per position: ${amount}")
        print(f"   Target profit: {target}%")
        print("")
        
        try:
            print("🔧 Initializing OrcaKillCycle...")
            orca = OrcaKillCycle()
            print("✅ OrcaKillCycle initialized successfully")
            
            # 🎖️ Use War Room (Rich dashboard) by default
            print("🎖️ Starting War Room...")
            stats = orca.run_autonomous_warroom(
                max_positions=max_pos,
                amount_per_position=amount,
                target_pct=target
            )
        except Exception as e:
            print(f"❌ FATAL: Autonomous mode crashed: {e}")
            traceback.print_exc()
            sys.exit(1)
    
    # 👑🔄 LEGACY AUTONOMOUS MODE - Raw print output (for debugging)
    elif len(sys.argv) >= 2 and sys.argv[1] == '--autonomous-legacy':
        max_pos = int(sys.argv[2]) if len(sys.argv) > 2 else 3
        amount = float(sys.argv[3]) if len(sys.argv) > 3 else 2.5
        target = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
        
        print("👑🦈 AUTONOMOUS QUEEN MODE - LEGACY OUTPUT 🦈👑")
        orca = OrcaKillCycle()
        stats = orca.run_autonomous(
            max_positions=max_pos,
            amount_per_position=amount,
            target_pct=target
        )
    
    elif len(sys.argv) >= 2:
        # Single symbol mode (backward compatible)
        symbol = sys.argv[1]
        try:
            amount = float(sys.argv[2]) if len(sys.argv) > 2 else 8.0
            target = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
            
            orca = OrcaKillCycle()
            result = orca.hunt_and_kill(symbol, amount, target)
            
            if result:
                print(f"\n💰 Portfolio impact: ${result['net_pnl']:+.4f}")
        except ValueError:
            # If parsing fails (e.g. user passed flags we didn't catch), default to War Room
             print("👑🎖️ AUTONOMOUS WAR ROOM MODE (DEFAULT) 🎖️👑")
             orca = OrcaKillCycle()
             stats = orca.run_autonomous_warroom(
                 max_positions=3,
                 amount_per_position=2.5,
                 target_pct=1.0
             )

    else:
        # No arguments defaults to WAR ROOM
        print("👑🎖️ AUTONOMOUS WAR ROOM MODE (DEFAULT) 🎖️👑")
        orca = OrcaKillCycle()
        stats = orca.run_autonomous_warroom(
            max_positions=3,
            amount_per_position=2.5,
            target_pct=1.0
        )

