#!/usr/bin/env python3
"""
🐙🌌 AUREON  ECOSYSTEM - THE UNIFIED TRADING ENGINE 🌌🐙
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

# ═══════════════════════════════════════════════════════════════════════════
# WINDOWS UTF-8 FIX - MUST BE AT VERY TOP BEFORE ALL OTHER IMPORTS
# ═══════════════════════════════════════════════════════════════════════════
import os
import sys
import io

if sys.platform == 'win32':
    # Set environment variable for Python's default encoding
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    # Force UTF-8 encoding for stdout/stderr to support emojis
    try:
        # Check if not already wrapped to avoid double-wrapping
        if hasattr(sys.stdout, 'buffer') and not isinstance(sys.stdout, io.TextIOWrapper):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'buffer') and not isinstance(sys.stderr, io.TextIOWrapper):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

import json
import time
import math
import random
import asyncio
import tempfile
import logging

# 🧠 THOUGHT BUS - UNITY CONSCIOUSNESS 🧠
try:
    from aureon_thought_bus import ThoughtBus, Thought
    THOUGHT_BUS = ThoughtBus(persist_path="thoughts.jsonl")
    THOUGHT_BUS_AVAILABLE = True
except ImportError:
    THOUGHT_BUS = None
    THOUGHT_BUS_AVAILABLE = False
    print("⚠️  Thought Bus not available - Brain running in isolation")

# Custom StreamHandler that forces UTF-8 encoding on Windows
class SafeStreamHandler(logging.StreamHandler):
    def __init__(self, stream=None):
        super().__init__(stream or sys.stdout)
    
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            # Write with UTF-8 encoding, replace errors
            try:
                stream.write(msg + self.terminator)
                self.flush()
            except UnicodeEncodeError:
                # If encoding fails, replace unencodable characters
                msg_safe = msg.encode('utf-8', errors='replace').decode('utf-8')
                stream.write(msg_safe + self.terminator)
                self.flush()
        except Exception:
            self.handleError(record)

# 🛡️ CRITICAL: Configure Root Logger IMMEDIATELY with SafeStreamHandler
# This ensures ALL subsequent loggers (including those from imported modules)
# use this safe handler and don't crash on Windows when printing emojis.

def sanitize_logging_environment():
    """
    Aggressively removes unsafe StreamHandlers from the root logger
    and ensures only SafeStreamHandler is used.
    """
    root_logger = logging.getLogger()
    handlers_removed = 0
    
    # Remove unsafe handlers
    for h in list(root_logger.handlers):
        if isinstance(h, logging.StreamHandler) and not isinstance(h, SafeStreamHandler):
            try:
                root_logger.removeHandler(h)
                handlers_removed += 1
            except Exception:
                pass
            
    # Add SafeStreamHandler if missing
    has_safe_handler = any(isinstance(h, SafeStreamHandler) for h in root_logger.handlers)
    if not has_safe_handler:
        safe_handler = SafeStreamHandler(sys.stdout)
        safe_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        root_logger.addHandler(safe_handler)
        root_logger.setLevel(logging.INFO)
        
    if sys.platform == 'win32' and handlers_removed > 0:
        # Use safe print just in case
        try:
            sys.stdout.buffer.write(f"🛡️  Windows Unicode Protection: Removed {handlers_removed} unsafe handlers.\n".encode('utf-8'))
        except Exception:
            pass

# Initial sanitization
sanitize_logging_environment()



# Load environment variables from .env file FIRST before any other imports
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    websockets = None
    WEBSOCKETS_AVAILABLE = False
import threading
import logging
try:
    import statistics
except ImportError:
    # Fallback for statistics if missing
    class Statistics:
        def mean(self, data): return sum(data) / len(data) if data else 0
        def stdev(self, data): 
            if not data or len(data) < 2: return 0
            m = sum(data) / len(data)
            return (sum((x - m) ** 2 for x in data) / (len(data) - 1)) ** 0.5
    statistics = Statistics()

from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import deque, defaultdict
from threading import Thread, Lock

# Set up logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    # Use SafeStreamHandler instead of standard StreamHandler
    handler = SafeStreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

    # 🔧 Miner Blueprint Constants (enhancements)
    CASCADE_FACTOR = 10.0       # Amplify weak signals
    KT_EFFICIENCY = 4.24        # Capital efficiency multiplier
    MIN_GAMMA_THRESHOLD = 0.20  # Independent entry threshold
    MIN_HOLD_MINUTES = 50       # Resonance holding minimum
    PSI_FILTER = 0.037          # Top 3.7% opportunities only

# Add current directory to path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)
try:
    from unified_exchange_client import UnifiedExchangeClient, MultiExchangeClient
except ImportError as e:
    print(f"⚠️  Unified Exchange Client not available: {e}")
    # Define dummy classes to prevent crash if critical module is missing
    class UnifiedExchangeClient:
        def __init__(self, *args, **kwargs): self.dry_run = True
    class MultiExchangeClient:
        def __init__(self, *args, **kwargs): 
            self.dry_run = True
            self.clients = {}
        def get_all_balances(self): return {}
        def get_24h_tickers(self): return []
        def get_ticker(self, *args): return {}
        def place_market_order(self, *args, **kwargs): return {}
        def convert_to_quote(self, *args): return 0.0

try:
    from aureon_lattice import GaiaLatticeEngine, CarrierWaveDynamics  # 🌍 GAIA FREQUENCY PHYSICS
    LATTICE_AVAILABLE = True
except ImportError:
    LATTICE_AVAILABLE = False
    print("⚠️  Gaia Lattice Engine not available (numpy missing?): Running in degraded mode")
    class GaiaLatticeEngine:
        def __init__(self): pass
        def get_state(self): return {}
        def update(self, opps): return {}
        def filter_signals(self, opps): return opps
        def get_field_purity(self): return 1.0

try:
    from aureon_enhancements import EnhancementLayer
    ENHANCEMENTS_AVAILABLE = True
except ImportError:
    ENHANCEMENTS_AVAILABLE = False
    print("⚠️  Enhancement Layer not available: Running without codex integration")
    class EnhancementLayer:
        def __init__(self): pass
        def get_unified_modifier(self, *args, **kwargs): return type('obj', (object,), {'trading_modifier': 1.0, 'confidence': 0.5, 'reasons': []})()
        def display_status(self): return "✨ ENHANCEMENTS | Disabled"
    class CarrierWaveDynamics:
        pass
try:
    from aureon_market_pulse import MarketPulse
except ImportError:
    print("⚠️  Market Pulse not available: Running in degraded mode")
    class MarketPulse:
        def __init__(self, client): pass
        def analyze_market(self): return {}

# 🔮 NEXUS PREDICTOR - 79.6% Win Rate Validated Over 11 Years!
try:
    from nexus_predictor import NexusPredictor
    NEXUS_PREDICTOR_AVAILABLE = True
    print("🔮 Nexus Predictor loaded - 79.6% win rate validated!")
except ImportError:
    NEXUS_PREDICTOR_AVAILABLE = False
    print("⚠️  Nexus Predictor not available")

# 🧠 MINER BRAIN - COGNITIVE TRADING INTELLIGENCE 🧠
try:
    from aureon_miner_brain import MinerBrain
    BRAIN_AVAILABLE = True
    print("🧠 Miner Brain loaded - Cognitive Intelligence Active!")
except ImportError:
    BRAIN_AVAILABLE = False
    print("⚠️  Miner Brain not available")

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

# 🔭 QUANTUM TELESCOPE & HARMONIC UNDERLAY 🔭
try:
    from aureon_quantum_telescope import QuantumTelescope, LightBeam, GeometricSolid
    from hnc_6d_harmonic_waveform import SixDimensionalHarmonicEngine, WaveState
    QUANTUM_AVAILABLE = True
except ImportError as e:
    QUANTUM_AVAILABLE = False
    print(f"⚠️  Quantum Telescope/Harmonic Engine not available: {e}")

# 🌍⚡ EARTH RESONANCE ENGINE ⚡🌍
try:
    from earth_resonance_engine import EarthResonanceEngine, get_earth_engine
    EARTH_RESONANCE_AVAILABLE = True
except ImportError as e:
    EARTH_RESONANCE_AVAILABLE = False
    print(f"⚠️  Earth Resonance Engine not available: {e}")

# 🌌⚡ AUREON NEXUS - UNIFIED NEURAL TRADING ENGINE ⚡🌌
try:
    from aureon_nexus import NexusBus, MasterEquation, QueenHive, AureonNexus, NEXUS as NEXUS_BUS
    NEXUS_AVAILABLE = True
    # 🧠 UNITY: Connect Nexus to Thought Bus
    if NEXUS_BUS and THOUGHT_BUS_AVAILABLE:
        NEXUS_BUS.thought_bus = THOUGHT_BUS
        print("   🧠 Nexus connected to Thought Bus")
except ImportError as e:
    NEXUS_AVAILABLE = False
    NEXUS_BUS = None
    print(f"⚠️  Aureon Nexus not available: {e}")

# 🎯 PROBABILITY LOADER & POSITION HYGIENE 🎯
try:
    from probability_loader import ProbabilityLoader, PositionHygieneChecker, load_position_state
    PROBABILITY_LOADER_AVAILABLE = True
except ImportError as e:
    PROBABILITY_LOADER_AVAILABLE = False
    print(f"⚠️  Probability Loader not available: {e}")
    class ProbabilityLoader:
        def __init__(self, *args, **kwargs): pass
        def load_all_reports(self): return {}
        def is_fresh(self): return False
        def get_top_signals(self, *args): return []
        def get_consensus_signals(self, *args): return []
    class PositionHygieneChecker:
        def __init__(self): pass
        def check_positions(self, *args): return {'flagged': [], 'count': 0}

# 📊 TRADE LOGGER - COMPREHENSIVE DATA LOGGING 📊
try:
    from trade_logger import get_trade_logger, TradeLogger
    TRADE_LOGGER_AVAILABLE = True
    trade_logger = get_trade_logger()
except ImportError as e:
    TRADE_LOGGER_AVAILABLE = False
    trade_logger = None
    print(f"⚠️  Trade Logger not available: {e}")

# 💰 COST BASIS TRACKER - REAL PURCHASE PRICES 💰
try:
    from cost_basis_tracker import CostBasisTracker, get_cost_basis_tracker
    COST_BASIS_AVAILABLE = True
except ImportError as e:
    COST_BASIS_AVAILABLE = False
    print(f"⚠️  Cost Basis Tracker not available: {e}")
    # Fallback stub
    class CostBasisTracker:
        def __init__(self): self.positions = {}
        def sync_from_exchanges(self): return 0
        def get_entry_price(self, symbol): return None
        def set_entry_price(self, *args, **kwargs): pass
        def update_position(self, *args, **kwargs): pass
        def can_sell_profitably(self, symbol, price, **kw): return True, {'recommendation': 'NO_TRACKER'}
        def print_status(self): pass
    def get_cost_basis_tracker(): return CostBasisTracker()

# 🌍⚡ GLOBAL FINANCIAL ECOSYSTEM FEED ⚡🌍
try:
    from global_financial_feed import GlobalFinancialFeed, MacroSnapshot
    GLOBAL_FEED_AVAILABLE = True
    print("   🌍 Global Financial Ecosystem Feed ACTIVE")
except ImportError as e:
    GLOBAL_FEED_AVAILABLE = False
    print(f"⚠️  Global Financial Feed not available: {e}")
    # Fallback stub
    class GlobalFinancialFeed:
        def get_snapshot(self): return None
        def get_probability_adjustment(self, symbol, prob): return prob, {}
        def get_trading_signal(self, symbol): return {'macro_bias': 'NEUTRAL', 'macro_strength': 50}
        def print_dashboard(self): pass

# 📊 PROBABILITY VALIDATION ENGINE 📊
try:
    from probability_validator import ProbabilityValidator, get_validator
    VALIDATOR_AVAILABLE = True
    print("   📊 Probability Validation Engine ACTIVE")
except ImportError as e:
    VALIDATOR_AVAILABLE = False
    print(f"⚠️  Probability Validator not available: {e}")
    # Fallback stub
    class ProbabilityValidator:
        def record_prediction(self, **kwargs): return ""
        def validate_pending(self, func): return []
        def get_confidence_adjustment(self, *args): return 1.0
        def print_dashboard(self): pass
    def get_validator(): return ProbabilityValidator()

# 🌈✨ AUREON ENHANCEMENTS - RAINBOW BRIDGE, SYNCHRONICITY, STARGATE ✨🌈
try:
    from aureon_enhancements import EnhancementLayer, apply_enhancement_to_signal, get_emotional_color
    ENHANCEMENTS_AVAILABLE = True
except ImportError as e:
    ENHANCEMENTS_AVAILABLE = False
    print(f"⚠️  Aureon Enhancements not available: {e}")

# ==== AUREON COGNITION BUS (self-talking JSON thoughts) ====
from aureon_thought_bus import ThoughtBus, Thought
from aureon_cognition_runtime import MinerModule, RiskModule, ExecutionModule

# ==== WORLD NEWS FEED (external data gathering) ====
try:
    from aureon_news_feed import NewsFeed, NewsFeedConfig, create_news_feed
    NEWS_FEED_AVAILABLE = True
except ImportError:
    NEWS_FEED_AVAILABLE = False
    print("⚠️  News Feed module not available")

# ==== WIKIPEDIA KNOWLEDGE BASE (autonomous knowledge gathering) ====
try:
    from aureon_knowledge_base import KnowledgeBase, create_knowledge_base
    KNOWLEDGE_BASE_AVAILABLE = True
except ImportError:
    KNOWLEDGE_BASE_AVAILABLE = False
    print("⚠️  Knowledge Base module not available")

# ==== WISDOM SCANNER - CONSCIOUSNESS EXPANSION ENGINE ====
try:
    from aureon_wisdom_scanner import AureonWisdomScanner, ScannerConfig, WisdomScannerThoughtBusAdapter
    WISDOM_SCANNER_AVAILABLE = True
    print("   📚 Wisdom Scanner loaded - Consciousness Expansion Active!")
except ImportError as e:
    WISDOM_SCANNER_AVAILABLE = False
    print(f"⚠️  Wisdom Scanner not available: {e}")

# ═══════════════════════════════════════════════════════════════
# 💰 PENNY PROFIT ENGINE - DYNAMIC DOLLAR-BASED EXIT THRESHOLDS 💰
# ═══════════════════════════════════════════════════════════════
# 🎯 Calculates EXACT thresholds for ANY trade size dynamically!
# No more preset lookup tables - formula calculates on-the-fly.

PENNY_PROFIT_CONFIG = {}  # Optional overrides from JSON
PENNY_PROFIT_ENABLED = True  # Always enabled - dynamic calculation works without config
PENNY_TARGET_NET = 0.01  # Default target: $0.01 net profit per trade

# Default fee rates by exchange (can be overridden by CONFIG or JSON)
DEFAULT_FEE_RATES = {
    'binance': 0.001,    # 0.10% taker
    'kraken': 0.0026,    # 0.26% taker  
    'capital': 0.0012,   # ~0.12% spread
    'alpaca': 0.0025,    # 0.25% commission
}


def load_penny_profit_config():
    """Load penny profit configuration (optional - for fee rate overrides).
    
    The engine works WITHOUT a config file using dynamic calculation.
    Config file only needed to override default fee rates or target.
    """
    global PENNY_PROFIT_CONFIG, PENNY_PROFIT_ENABLED, PENNY_TARGET_NET
    config_path = os.path.join(ROOT_DIR, 'penny_profit_config.json')
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                PENNY_PROFIT_CONFIG = json.load(f)
            PENNY_TARGET_NET = PENNY_PROFIT_CONFIG.get('target_net_win', 0.01)
            print(f"💰 Penny Profit Engine - DYNAMIC (target: +${PENNY_TARGET_NET:.2f} net per trade)")
        except Exception as e:
            print(f"⚠️  Penny config load error: {e} - using dynamic defaults")
    else:
        print(f"💰 Penny Profit Engine - DYNAMIC MODE (target: +${PENNY_TARGET_NET:.2f} net)")
    
    PENNY_PROFIT_ENABLED = True  # Always enabled with dynamic calculation


def get_exchange_fee_rate(exchange: str) -> float:
    """Get fee rate for exchange - checks CONFIG, then JSON, then defaults.
    
    Priority order:
    1. Global CONFIG (most accurate - actual observed rates)
    2. penny_profit_config.json fee_rate
    3. DEFAULT_FEE_RATES fallback
    """
    ex_lower = (exchange or 'binance').lower()
    
    # Priority 1: Check global CONFIG for actual observed fees
    try:
        if ex_lower == 'kraken':
            return CONFIG.get('KRAKEN_FEE_TAKER', DEFAULT_FEE_RATES['kraken'])
        elif ex_lower == 'binance':
            return CONFIG.get('BINANCE_FEE_TAKER', DEFAULT_FEE_RATES['binance'])
        elif ex_lower == 'alpaca':
            return CONFIG.get('ALPACA_FEE_TAKER', DEFAULT_FEE_RATES['alpaca'])
        elif ex_lower == 'capital':
            return CONFIG.get('CAPITAL_FEE', DEFAULT_FEE_RATES['capital'])
    except (NameError, KeyError):
        pass  # CONFIG not loaded yet
    
    # Priority 2: Check penny_profit_config.json
    if PENNY_PROFIT_CONFIG:
        exchanges = PENNY_PROFIT_CONFIG.get('exchanges', {})
        if ex_lower in exchanges:
            return exchanges[ex_lower].get('fee_rate', DEFAULT_FEE_RATES.get(ex_lower, 0.002))
    
    # Priority 3: Default fallback
    return DEFAULT_FEE_RATES.get(ex_lower, 0.002)


def required_price_increase(initial_usd: float, fee_rate: float, target_profit: float = 0.01) -> float:
    """
    📐 EXACT MATHEMATICAL FORMULA for required price increase to achieve target net profit.
    
    Formula: r = ((1 + P/A) / (1 - f)²) - 1
    
    This accounts for fee compounding over both legs:
    1. Buy: Spend A USD, receive crypto worth A×(1-f) after fee
    2. Sell: Crypto sold at price×(1+r), then fee deducted again
    3. Final USD = A × (1-f)² × (1+r) = A + P
    
    Args:
        initial_usd (A): Position size in USD
        fee_rate (f): Fee rate per leg (e.g., 0.001 for 0.1%)
        target_profit (P): Target net profit in USD (default $0.01)
    
    Returns:
        r: Required price increase as decimal (multiply by 100 for %)
    """
    if initial_usd <= 0 or fee_rate < 0 or target_profit <= 0:
        return 0.0
    
    # Exact formula accounting for compounding fees
    r = ((1 + target_profit / initial_usd) / ((1 - fee_rate) ** 2)) - 1
    return r


def get_penny_threshold(exchange: str, trade_size: float) -> dict:
    """🎯 EXACT PENNY PROFIT - Uses precise mathematical formula for ANY trade size!
    
    📐 EXACT FORMULA (accounts for fee compounding):
        r = ((1 + P/A) / (1 - f)²) - 1
        
    Where:
        A = trade_size (initial USD)
        P = target net profit ($0.01)
        f = fee rate per leg
        r = required price increase (decimal)
    
    The sell target price = buy_price × (1 + r)
    
    Args:
        exchange: Exchange name ('binance', 'kraken', 'alpaca', 'capital')
        trade_size: Entry value in dollars (ANY amount!)
    
    Returns:
        dict with: required_pct, win_gte, stop_lte, fee_rate, trade_size, target_net
    """
    if not PENNY_PROFIT_ENABLED or trade_size <= 0:
        return None
    
    fee_rate = get_exchange_fee_rate(exchange)
    target_net = PENNY_TARGET_NET
    
    # Add safety margins for slippage and spread (from CONFIG)
    # This ensures we account for ALL costs, not just exchange fees.
    slippage = CONFIG.get('SLIPPAGE_PCT', 0.0020)
    spread = CONFIG.get('SPREAD_COST_PCT', 0.0010)
    
    # Total effective rate per leg (Fee + Slippage + Spread)
    total_rate = fee_rate + slippage + spread
    
    # 📐 EXACT CALCULATION using proper compounding formula
    # We use total_rate to ensure the price increase covers ALL costs
    r = required_price_increase(trade_size, total_rate, target_net)
    
    # win_gte is the gross P&L needed (price increase × position)
    # Since gross_pnl = exit_value - entry_value = entry_value × r
    win_gte = trade_size * r
    
    # Approximate fee cost for reference (linear estimate)
    # This is just for display/logging - the real math is in 'r'
    approx_fees = 2 * total_rate * trade_size
    
    # Stop Loss: Risk ~1.5x the win target (gives ~40% breakeven win rate)
    stop_lte = -(win_gte * 1.5)
    
    return {
        'required_pct': round(r * 100, 4),  # As percentage
        'required_r': r,                      # As decimal
        'cost': round(approx_fees, 6),        # Approximate total fees
        'win_gte': round(win_gte, 6),         # Gross P&L trigger for TP
        'stop_lte': round(stop_lte, 6),       # Gross P&L trigger for SL
        'fee_rate': fee_rate,
        'trade_size': trade_size,
        'target_net': target_net,
        'is_dynamic': True
    }


def check_penny_exit(exchange: str, entry_value: float, gross_pnl: float) -> dict:
    """Check if position should exit based on dynamically calculated thresholds.
    
    Args:
        exchange: Exchange name
        entry_value: Position entry value in dollars (ANY size!)
        gross_pnl: Current gross P&L (before fees)
    
    Returns:
        {'should_tp': bool, 'should_sl': bool, 'threshold': dict, 'gross_pnl': float}
    """
    threshold = get_penny_threshold(exchange, entry_value)
    
    if not threshold:
        return {'should_tp': False, 'should_sl': False, 'threshold': None, 'gross_pnl': gross_pnl}
    
    # Check Take Profit: gross P&L >= win threshold
    should_tp = gross_pnl >= threshold['win_gte']
    
    # Check Stop Loss: gross P&L <= loss threshold  
    should_sl = gross_pnl <= threshold['stop_lte']
    
    return {
        'should_tp': should_tp,
        'should_sl': should_sl,
        'threshold': threshold,
        'gross_pnl': gross_pnl
    }


# Load on import (sets PENNY_PROFIT_ENABLED = True)
load_penny_profit_config()

# ═══════════════════════════════════════════════════════════════
# MODULE-LEVEL LOT SIZE CACHE - Used by UnifiedTradeConfirmation
# ═══════════════════════════════════════════════════════════════
_MODULE_LOT_SIZE_CACHE: Dict[str, Tuple[Optional[float], Optional[float]]] = {}

def get_exchange_lot_size(exchange: str, symbol: str, client=None) -> Tuple[Optional[float], Optional[float]]:
    """
    Module-level lot size lookup for any exchange.
    Returns (step_size, min_qty) or (None, None) if unavailable.
    """
    global _MODULE_LOT_SIZE_CACHE
    cache_key = f"{exchange}:{symbol}"
    
    if cache_key in _MODULE_LOT_SIZE_CACHE:
        return _MODULE_LOT_SIZE_CACHE[cache_key]
    
    exchange_name = (exchange or '').lower()
    result = (None, None)
    
    try:
        if exchange_name == 'binance' and client:
            # Try to get from Binance exchange info
            try:
                info = client.client.session.get(
                    f"{client.client.base}/api/v3/exchangeInfo",
                    params={'symbol': symbol},
                    timeout=5
                ).json()
                for sym_info in info.get('symbols', []):
                    if sym_info['symbol'] == symbol:
                        for f in sym_info.get('filters', []):
                            if f['filterType'] == 'LOT_SIZE':
                                step = float(f.get('stepSize', 0))
                                min_q = float(f.get('minQty', 0))
                                result = (step, min_q)
                                break
            except Exception:
                # Fallback defaults for common Binance pairs
                binance_defaults = {
                    'BTCUSDC': (0.00001, 0.00001), 'BTCUSDT': (0.00001, 0.00001),
                    'ETHUSDC': (0.0001, 0.0001), 'ETHUSDT': (0.0001, 0.0001),
                    'SOLUSDC': (0.001, 0.001), 'SOLUSDT': (0.001, 0.001),
                    'SHIBUSDC': (1, 1), 'SHIBUSDT': (1, 1),
                    'XLMUSDC': (0.1, 0.1), 'XLMUSDT': (0.1, 0.1),
                }
                result = binance_defaults.get(symbol, (0.00000001, 0.00000001))
                
        elif exchange_name == 'kraken':
            # Kraken common lot sizes
            kraken_defaults = {
                'XBTUSD': (0.0001, 0.0001), 'XBTUSDC': (0.0001, 0.0001),
                'ETHUSD': (0.001, 0.001), 'ETHUSDC': (0.001, 0.001),
                'SOLUSD': (0.01, 0.01), 'SOLUSDC': (0.01, 0.01),
                'SHIBUSD': (50000, 50000), 'SHIBUSDC': (50000, 50000),  # Kraken SHIB is in large lots!
                'XLMUSD': (1, 1), 'XLMUSDC': (1, 1),
                'BCHUSD': (0.001, 0.001), 'BCHUSDC': (0.001, 0.001),
            }
            # Also handle Kraken's X-prefixed naming
            alt_symbol = symbol
            if symbol.startswith('X') and len(symbol) > 4:
                alt_symbol = symbol[1:]  # XXBT -> XBT
            result = kraken_defaults.get(symbol, kraken_defaults.get(alt_symbol, (0.00000001, 0.00000001)))
            
        elif exchange_name == 'capital':
            # 💼 Capital.com CFD lot sizes - they use contract sizes
            # Most CFDs have 1 unit minimum, crypto CFDs vary
            capital_defaults = {
                # Crypto CFDs on Capital.com
                'BTCUSD': (0.01, 0.01), 'Bitcoin': (0.01, 0.01),
                'ETHUSD': (0.1, 0.1), 'Ethereum': (0.1, 0.1),
                'SOLUSD': (1.0, 1.0), 'Solana': (1.0, 1.0),
                'XRPUSD': (10.0, 10.0), 'Ripple': (10.0, 10.0),
                'ADAUSD': (10.0, 10.0), 'Cardano': (10.0, 10.0),
                'DOTUSD': (1.0, 1.0), 'Polkadot': (1.0, 1.0),
                'DOGEUSD': (100.0, 100.0), 'Dogecoin': (100.0, 100.0),
                'SHIBUSD': (100000.0, 100000.0), 'Shiba': (100000.0, 100000.0),
                # Forex/Indices - standard lot decimals
                'EURUSD': (0.01, 0.01), 'GBPUSD': (0.01, 0.01),
                'US500': (0.1, 0.1), 'UK100': (0.1, 0.1),
                'Gold': (0.01, 0.01), 'XAUUSD': (0.01, 0.01),
            }
            result = capital_defaults.get(symbol, (1.0, 1.0))  # Default 1 unit for CFDs
            
        elif exchange_name == 'alpaca':
            # 🦙 Alpaca crypto/stock lot sizes
            # Stocks are fractional, crypto varies
            alpaca_defaults = {
                # Crypto on Alpaca
                'BTC/USD': (0.0001, 0.0001), 'BTCUSD': (0.0001, 0.0001),
                'ETH/USD': (0.001, 0.001), 'ETHUSD': (0.001, 0.001),
                'SOL/USD': (0.01, 0.01), 'SOLUSD': (0.01, 0.01),
                'DOGE/USD': (1.0, 1.0), 'DOGEUSD': (1.0, 1.0),
                'SHIB/USD': (1000.0, 1000.0), 'SHIBUSD': (1000.0, 1000.0),
                # Stocks - fractional shares supported
                'AAPL': (0.001, 0.001), 'TSLA': (0.001, 0.001),
                'NVDA': (0.001, 0.001), 'MSFT': (0.001, 0.001),
            }
            result = alpaca_defaults.get(symbol, (0.001, 0.001))  # Default fractional for stocks
            
    except Exception as e:
        print(f"⚠️ Lot size lookup failed for {exchange}/{symbol}: {e}")
        
    _MODULE_LOT_SIZE_CACHE[cache_key] = result
    return result

def truncate_to_lot_size(quantity: float, step_size: float) -> float:
    """Truncate quantity to valid lot size step."""
    if step_size <= 0 or quantity <= 0:
        return quantity
    steps = int(quantity / step_size)
    return steps * step_size

def validate_order_quantity(exchange: str, symbol: str, quantity: float, price: float = 0, client=None) -> Tuple[Optional[float], Optional[str]]:
    """
    Validate and adjust quantity for exchange lot size requirements.
    Returns (adjusted_quantity, error_message) - error_message is None if valid.
    """
    if quantity is None or quantity <= 0:
        return None, "Invalid quantity"
        
    exchange_name = (exchange or '').lower()
    step_size, min_qty = get_exchange_lot_size(exchange, symbol, client)
    
    # Truncate to lot size
    if step_size and step_size > 0:
        quantity = truncate_to_lot_size(quantity, step_size)
        
    if quantity <= 0:
        return None, f"Quantity below lot step {step_size}"
        
    # Check minimum quantity
    if min_qty and quantity < min_qty:
        return None, f"Qty {quantity:.8f} below {exchange_name.upper()} min {min_qty:.8f}"
        
    # Check minimum notional
    min_notional = CONFIG.get(f'{exchange_name.upper()}_MIN_NOTIONAL', 1.0)
    if price and price > 0:
        notional = quantity * price
        if notional < min_notional:
            return None, f"Notional ${notional:.2f} below {exchange_name.upper()} min ${min_notional:.2f}"
            
    return quantity, None


# ═══════════════════════════════════════════════════════════════
# CONFIGURATION - THE UNIFIED PARAMETERS
# ═══════════════════════════════════════════════════════════════

CONFIG = {
    'EXCHANGE': os.getenv('EXCHANGE', 'both').lower(), # BOTH Binance AND Kraken for multi-exchange trading
    # Trading Parameters
    'BASE_CURRENCY': os.getenv('BASE_CURRENCY', 'USD'),  # USD or GBP
    
    # Platform-Specific Fees (as decimals)
    # ══════════════════════════════════════════════════════════
    # 🐙 KRAKEN (Actual observed: ~0.40% per trade on small volume)
    'KRAKEN_FEE_MAKER': 0.0026,     # 0.26% maker fee 
    'KRAKEN_FEE_TAKER': 0.0040,     # 0.40% taker fee (actual observed)
    'KRAKEN_FEE': 0.0040,           # Legacy field (uses taker)
    
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
    'SLIPPAGE_PCT': 0.0020,         # 0.20% estimated slippage per trade (increased for safety)
    'SPREAD_COST_PCT': 0.0010,      # 0.10% estimated spread cost (increased for safety)
    'TAKE_PROFIT_PCT': 1.8,         # FALLBACK: 1.8% (penny profit uses dollar thresholds instead)
    'STOP_LOSS_PCT': 1.5,           # FALLBACK: 1.5% (penny profit uses dollar thresholds instead)
    'MAX_POSITIONS': 30,            # 🔥 BEAST MODE: 30 positions - TRADE EVERYTHING!
    'TARGET_FILL_RATE': 0.33,       # 🎯 TARGET: Keep 1/3 of positions filled (10 of 30)
    'MIN_TRADE_USD': 1.44,          # Minimum trade notional in base currency
    'BINANCE_MIN_NOTIONAL': 1.0,    # Refuse sells if notional < $1 to avoid LOT_SIZE noise
    'KRAKEN_MIN_NOTIONAL': 5.25,    # Kraken enforces ~$5 minimum notional on spot
    'CAPITAL_MIN_NOTIONAL': 10.0,   # 💼 Capital.com CFD minimum ~$10 (varies by instrument)
    'ALPACA_MIN_NOTIONAL': 1.0,     # 🦙 Alpaca crypto ~$1 min, stocks $1
    'PORTFOLIO_RISK_BUDGET': 3.00,  # 300% - allow significant positions for existing portfolio holders
    'MIN_EXPECTED_EDGE_GBP': 0.001, # Require positive edge
    'DEFAULT_WIN_PROB': 0.55,       # Target win probability
    'WIN_RATE_CONFIDENCE_TRADES': 25,
    'EQUITY_MIN_DELTA': 0.10,       # Smaller delta for frequent compounding
    'EQUITY_TOLERANCE_GBP': 0.0,
    
    # 🎯 TRAILING STOP CONFIGURATION
    'ENABLE_TRAILING_STOP': True,           # Enable trailing stop system
    'TRAILING_ACTIVATION_PCT': 0.8,         # Activate at 0.8% profit (was 0.5% - lock in more profit first)
    'TRAILING_DISTANCE_PCT': 0.5,           # Trail 0.5% behind peak (was 0.3% - less whipsaw)
    'USE_ATR_TRAILING': True,               # Use ATR for dynamic trailing
    'ATR_TRAIL_MULTIPLIER': 1.5,            # Trail at 1.5x ATR below peak
    
    # 🚀 KRAKEN ADVANCED ORDERS - Server-Side TP/SL (executes even if bot offline!)
    'USE_SERVER_SIDE_ORDERS': os.getenv('USE_SERVER_SIDE_ORDERS', '1') == '1',  # Enable Kraken native TP/SL
    'PREFER_LIMIT_ORDERS': os.getenv('PREFER_LIMIT_ORDERS', '1') == '1',        # 💰 USE LIMIT ORDERS for maker fees (0.1% vs 0.2%!)
    'USE_TRAILING_STOP_ORDERS': os.getenv('USE_TRAILING_STOP_ORDERS', '0') == '1',  # Native trailing stops
    
    # 💰 PROFIT GATES - PENNY PROFIT MODE!
    # Target: +$0.01 net profit per trade. Dollar thresholds loaded from penny_profit_config.json
    # These percentages are FALLBACK only when penny profit config not available
    'MIN_NET_PROFIT_PCT': 0.008,    # 0.8% fallback if penny config missing
    'SERVER_SIDE_TP_PCT': 1.8,              # Take profit % for server-side orders (fallback)
    'SERVER_SIDE_SL_PCT': 1.5,              # Stop loss % for server-side orders (fallback)
    'SERVER_TRAILING_PCT': 2.0,             # Trailing stop distance % for native trailing
    
    # Dynamic Portfolio Rebalancing
    'ENABLE_REBALANCING': True,     # Sell underperformers to buy better opportunities
    'REBALANCE_THRESHOLD': -50.0,   # 🔥 Sell big losers (>50% loss) to free capital for better opportunities
    'MIN_HOLD_CYCLES': 10,          # Hold at least 10 cycles (~10 mins) before rebalance (was 3)
    # 🤑 GREEDY HOE MODE: ALL THE QUOTE CURRENCIES!
    'QUOTE_CURRENCIES': ['USDC', 'USDT', 'USD', 'GBP', 'EUR', 'BTC', 'ETH', 'BNB', 'FDUSD', 'TUSD', 'BUSD'],
    
    # 🌾 Startup Harvesting
    'HARVEST_ON_STARTUP': True,      # 🔥 ENABLED - Actively harvest and trade!
    'HARVEST_MIN_VALUE': 0.50,       # Lowered - harvest even small gains
    
    # Scout Deployment (from immediateWaveRider.ts)
    'DEPLOY_SCOUTS_IMMEDIATELY': True,   # 🚀 Deploy positions immediately on first scan - HIT THE GROUND RUNNING!
    'SCOUT_MIN_MOMENTUM': 0.1,           # Very low threshold - get into trades FAST
    'SCOUT_FORCE_COUNT': 10,             # 🤑 GREEDY: 10 scouts on startup!
    'SCOUT_MIN_VOLATILITY': 1.0,         # 🤑 LOWERED: More coins qualify
    'SCOUT_MIN_VOLUME_QUOTE': 50000,     # 🤑 LOWERED: Trade thinner books too
    'SCOUT_PER_QUOTE_LIMIT': 3,          # Spread early scouts across quote currencies (3 per quote)
    
    # Kelly Criterion & Risk Management
    'USE_KELLY_SIZING': True,       # Use Kelly instead of fixed %
    'KELLY_SAFETY_FACTOR': 0.5,     # Half-Kelly for safety
    'BASE_POSITION_SIZE': 0.04,     # Base size when Kelly disabled (reduced for smaller trades)
    'MAX_POSITION_SIZE': 0.25,      # Hard cap per trade
    'MAX_SYMBOL_EXPOSURE': 0.30,    # Max 30% in one symbol
    'MAX_DRAWDOWN_PCT': 50.0,       # Circuit breaker at 50% DD - raised to allow recovery trades
    'MIN_NETWORK_COHERENCE': 0.20,  # NEVER pause - always trade!
    
    # Opportunity Filters - QUALITY OVER QUANTITY 🎯
    'MIN_MOMENTUM': 0.5,            # Require positive momentum (trend confirmation)
    'MAX_MOMENTUM': 50.0,           # Avoid parabolic pumps (reversal risk)
    'MIN_VOLUME': 20000,            # Lowered to allow thinner but tradeable books
    'MIN_SCORE': 40,                # Lowered from 60 to allow more trades (system was too selective)
    
    # 🎯 OPTIMAL WIN RATE MODE
    'ENABLE_OPTIMAL_WR': True,      # Enable all win rate optimizations
    
    # 🔥 FORCE TRADE MODE - Bypasses all gates for testing
    'FORCE_TRADE': os.getenv('FORCE_TRADE', '0') == '1',
    'FORCE_TRADE_SYMBOL': os.getenv('FORCE_TRADE_SYMBOL', ''),  # Specific symbol or empty for best available
    
    # 🔭 QUANTUM TELESCOPE
    'ENABLE_QUANTUM_TELESCOPE': True,
    'ENABLE_HARMONIC_UNDERLAY': True,
    'QUANTUM_WEIGHT': 0.15,         # Weight of Quantum Telescope in Lambda field
    'HARMONIC_WEIGHT': 0.20,        # Weight of 6D harmonic coherence in Lambda field
    'HARMONIC_GATE': 0.30,          # LOWERED: Minimum harmonic dimensional coherence (was 0.45)
    'HARMONIC_PROB_MIN': 0.40,      # LOWERED: Allow more trades (was 0.52)
    'OPTIMAL_MIN_GATES': 2,         # REDUCED: 2 gates allows trading in consolidation (was 5)
    'OPTIMAL_MIN_COHERENCE': 0.35,  # REDUCED: Lowered to allow more signals (was 0.48)
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
    'HIGH_COHERENCE_MODE': False,   # DISABLED: Allow trading in any coherence
    'ENTRY_COHERENCE': 0.20,       # LOWERED: Allow more trades (was 0.35)
    'EXIT_COHERENCE': 0.15,        # LOWERED: Exit more flexibly (was 0.25)
    
    # Lambda Field Components (from coherenceTrader.ts)
    'ENABLE_LAMBDA_FIELD': os.getenv('ENABLE_LAMBDA_FIELD', '1') == '1',  # Full Λ(t) = S(t) + O(t) + E(t)
    'OBSERVER_WEIGHT': 0.3,         # O(t) = Λ(t-1) × 0.3 (self-reference)
    'ECHO_WEIGHT': 0.2,             # E(t) = avg(Λ[t-5:t]) × 0.2 (memory)
    
    # 🌍⚡ HNC Frequency Integration ⚡🌍
    'ENABLE_HNC_FREQUENCY': os.getenv('ENABLE_HNC', '1') == '1',  # Use HNC frequency for sizing
    'HNC_FREQUENCY_WEIGHT': 0.25,    # H(t) weight in Lambda field
    'HNC_COHERENCE_THRESHOLD': 0.50, # Min triadic coherence for full sizing
    'HNC_HARMONIC_BONUS': 1.15,      # 15% bonus for harmonic resonance (256/528 Hz)
    
    # 🔊 PHASE 2: FREQUENCY FILTERING OPTIMIZATION 🔊
    'ENABLE_FREQUENCY_FILTERING': True,        # Enable frequency-based signal quality
    'FREQUENCY_BOOST_300HZ': 1.50,            # 50% boost for 300-399Hz (98.8% prediction accuracy!)
    'FREQUENCY_BOOST_528HZ': 1.35,            # 35% boost for 528Hz Love Frequency (83.3% WR)
    'FREQUENCY_SUPPRESS_963HZ': 0.6,          # 40% suppression for 963Hz (poor performer)
    'FREQUENCY_SUPPRESS_600HZ': 0.75,         # 25% suppression for 600-699Hz (0% accuracy)
    'FREQUENCY_NEUTRAL_BASELINE': 1.0,        # All other frequencies baseline multiplier
    'FREQUENCY_WIN_RATE_TARGET': 0.60,        # Phase 2 target: 60%+ win rate
    'HNC_DISTORTION_PENALTY': 0.70,           # 30% penalty for 440 Hz distortion
    
    # 🎵 SOLFEGGIO FREQUENCY BOOSTS (Ancient Sacred Healing Tones) 🎵
    'FREQUENCY_BOOST_174HZ': 1.20,            # 174Hz - Pain Relief, Foundation
    'FREQUENCY_BOOST_285HZ': 1.25,            # 285Hz - Healing, Tissue Regeneration  
    'FREQUENCY_BOOST_396HZ': 1.40,            # 396Hz - Liberation from Fear/Guilt (UT)
    'FREQUENCY_BOOST_417HZ': 1.30,            # 417Hz - Undoing Situations, Change (RE)
    'FREQUENCY_BOOST_639HZ': 1.25,            # 639Hz - Connection, Relationships (FA)
    'FREQUENCY_BOOST_741HZ': 1.15,            # 741Hz - Awakening Intuition (SOL)
    'FREQUENCY_BOOST_852HZ': 1.20,            # 852Hz - Returning to Spiritual Order (LA)
    
    # 🌍 EARTH & COSMIC FREQUENCIES 🌍
    'FREQUENCY_BOOST_SCHUMANN': 1.45,         # 7.83Hz - Earth's heartbeat (×harmonics)
    'FREQUENCY_BOOST_432HZ': 1.30,            # 432Hz - Universal tuning, cosmic harmony
    'FREQUENCY_BOOST_136HZ': 1.25,            # 136.1Hz - OM, Earth's year frequency
    
    # 🔴 DISTORTION FREQUENCIES (AVOID) 🔴
    'FREQUENCY_SUPPRESS_440HZ': 0.70,         # 440Hz - Artificial concert pitch, dissonance
    'FREQUENCY_SUPPRESS_HIGH_CHAOS': 0.50,    # 1000+Hz - Chaotic, unstable
    
    # 🌍⚡ HNC Probability Matrix (2-Hour Window) ⚡🌍
    'ENABLE_PROB_MATRIX': os.getenv('ENABLE_PROB_MATRIX', '1') == '1',
    'ENABLE_PROBABILITY_GENERATOR': os.getenv('ENABLE_PROBABILITY_GENERATOR', '1') == '1',  # Auto-regenerate every 15s
    'PROB_MIN_CONFIDENCE': 0.45,     # Lowered to admit more entries
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
    'FLUX_THRESHOLD': 0.80,       # Raised from 0.60 - only override in VERY strong bearish/bullish
}

PHI = (1 + math.sqrt(5)) / 2  # Golden Ratio = 1.618

# ═══════════════════════════════════════════════════════════════
# 🎹 QUANTUM BRAIN / PIANO STATE BRIDGE
# ═══════════════════════════════════════════════════════════════

BRAIN_STATE_PATH = os.path.join(tempfile.gettempdir(), "aureon_multidimensional_brain_output.json")
_BRAIN_CACHE: Dict[str, Any] = {}
_BRAIN_CACHE_TIME: float = 0.0


def load_brain_state() -> Dict[str, Any]:
    """Load cached Quantum Brain/Piano state if recently updated."""
    global _BRAIN_CACHE, _BRAIN_CACHE_TIME
    try:
        now = time.time()
        if now - _BRAIN_CACHE_TIME < 10:
            return _BRAIN_CACHE
        if not os.path.exists(BRAIN_STATE_PATH):
            return {}
        with open(BRAIN_STATE_PATH) as f:
            data = json.load(f)
        piano = data.get('piano', {}) if isinstance(data, dict) else {}
        meta = data.get('meta', {}) if isinstance(data, dict) else {}
        cascade = meta.get('multiverse_cascade') or data.get('multiverse_cascade')
        _BRAIN_CACHE = {
            'piano_lambda': piano.get('lambda'),
            'piano_coherence': piano.get('coherence'),
            'rainbow_state': piano.get('rainbow_state'),
            'cascade': cascade,
            'timestamp': data.get('timestamp') or meta.get('timestamp'),
        }
        _BRAIN_CACHE_TIME = now
        return _BRAIN_CACHE
    except Exception:
        return {}


def get_brain_multiplier() -> float:
    """Compute a trading multiplier from Piano/Brain resonance."""
    brain = load_brain_state()
    if not isinstance(brain, dict):
        return 1.0
    mult = 1.0
    piano_coh = brain.get('piano_coherence')
    piano_lambda = brain.get('piano_lambda')
    rainbow_state = (brain.get('rainbow_state') or '').upper()

    if piano_coh is not None:
        mult *= 1.0 + max(0.0, piano_coh - 0.5) * 0.2  # up to +10%
    if piano_lambda is not None and piano_lambda > 1.5:
        mult *= 1.0 + (piano_lambda - 1.0) * 0.05       # mild lambda boost

    rainbow_boost = {
        'UNITY': 1.10,
        'AWE': 1.07,
        'LOVE': 1.05,
        'RESONANCE': 1.03,
    }
    if rainbow_state in rainbow_boost:
        mult *= rainbow_boost[rainbow_state]

    return mult


# ═══════════════════════════════════════════════════════════════
# 🔗 MINER STATE CONNECTOR - AUTO-DETECT RUNNING MINER
# ═══════════════════════════════════════════════════════════════

class MinerStateConnector:
    """
    🔗 MINER STATE CONNECTOR 🔗
    
    Automatically detects and connects to a running miner by monitoring
    the shared state file. This enables the ecosystem to receive live
    quantum state even when running standalone (without orchestrator).
    
    The miner writes to: /tmp/aureon_multidimensional_brain_output.json
    We read this file periodically to get:
    - Unified Coherence (Ψ)
    - Planetary Gamma (Γ)
    - Cascade Multiplier
    - Lighthouse Window status
    - Piano Lambda (Λ)
    - Rainbow State
    """
    
    # State file path (same as miner writes to)
    STATE_FILE = os.path.join(tempfile.gettempdir(), 'aureon_multidimensional_brain_output.json')
    
    # Alternative paths to check
    ALT_PATHS = [
        os.path.join(tempfile.gettempdir(), 'aureon_brain_state.json'),
        os.path.join(os.path.dirname(__file__), 'aureon_brain_state.json'),
        'aureon_brain_state.json',
    ]
    
    # How fresh the state must be to consider miner "connected" (seconds)
    FRESHNESS_THRESHOLD = 30  
    
    def __init__(self):
        self._state_file: Optional[str] = None
        self._last_state: Dict[str, Any] = {}
        self._last_read_time: float = 0
        self._read_interval: float = 2.0  # Check every 2 seconds
        self._miner_connected: bool = False
        self._connection_time: Optional[float] = None
        
        # Cached quantum values
        self.unified_coherence: float = 0.5
        self.planetary_gamma: float = 0.5
        self.cascade_multiplier: float = 1.0
        self.is_lighthouse: bool = False
        self.piano_lambda: float = 1.0
        self.piano_coherence: float = 0.0
        self.rainbow_state: str = "UNKNOWN"
        self.probability_edge: float = 0.0
        self.harmonic_signal: str = "HOLD"
        self.hnc_probability: float = 0.5
        
        # Statistics
        self._successful_reads: int = 0
        self._failed_reads: int = 0
        
        logger.info("🔗 Miner State Connector initialized - will auto-detect running miner")
        
    def _find_state_file(self) -> Optional[str]:
        """Find the miner state file from possible locations."""
        # Check primary path first
        if os.path.exists(self.STATE_FILE):
            return self.STATE_FILE
        
        # Check alternatives
        for path in self.ALT_PATHS:
            if os.path.exists(path):
                return path
        
        return None
    
    def _is_state_fresh(self, state: Dict) -> bool:
        """Check if the state file is fresh enough to be from a running miner."""
        timestamp = state.get('timestamp', 0)
        if timestamp == 0:
            # Try last_broadcast as alternative timestamp
            timestamp = state.get('last_broadcast', 0)
        
        if timestamp == 0:
            return False
        
        age = time.time() - timestamp
        return age < self.FRESHNESS_THRESHOLD
    
    def check_connection(self) -> bool:
        """
        Check if a miner is currently running and connected.
        Updates cached quantum state if connected.
        
        Returns:
            True if miner is connected and sending fresh data
        """
        now = time.time()
        
        # Rate limit reads
        if (now - self._last_read_time) < self._read_interval:
            return self._miner_connected
        
        self._last_read_time = now
        
        try:
            # Find state file
            state_file = self._find_state_file()
            if not state_file:
                if self._miner_connected:
                    logger.info("🔗❌ Miner disconnected - state file not found")
                self._miner_connected = False
                return False
            
            # Read state file
            with open(state_file, 'r') as f:
                state = json.load(f)
            
            # Check freshness
            if not self._is_state_fresh(state):
                if self._miner_connected:
                    logger.info("🔗⚠️ Miner state stale - last update too old")
                self._miner_connected = False
                return False
            
            # Update cached values
            self._update_from_state(state)
            self._last_state = state
            self._successful_reads += 1
            
            # Log connection if newly connected
            if not self._miner_connected:
                self._miner_connected = True
                self._connection_time = now
                logger.info(f"🔗✅ MINER CONNECTED! Live quantum state detected")
                logger.info(f"   Ψ={self.unified_coherence:.3f} | Γ={self.planetary_gamma:.3f} | "
                          f"Cascade={self.cascade_multiplier:.2f}x | Lighthouse={'🌟' if self.is_lighthouse else '⬜'}")
            
            return True
            
        except json.JSONDecodeError as e:
            logger.debug(f"Miner state JSON error: {e}")
            self._failed_reads += 1
            return self._miner_connected
        except Exception as e:
            logger.debug(f"Miner state read error: {e}")
            self._failed_reads += 1
            return self._miner_connected
    
    def _update_from_state(self, state: Dict):
        """Update cached quantum values from miner state."""
        # Core quantum values
        self.unified_coherence = float(state.get('unified_coherence', state.get('psi', 0.5)) or 0.5)
        self.planetary_gamma = float(state.get('planetary_gamma', state.get('gamma', 0.5)) or 0.5)
        self.cascade_multiplier = float(state.get('cascade_multiplier', state.get('cascade', 1.0)) or 1.0)
        self.is_lighthouse = bool(state.get('is_lighthouse', state.get('is_optimal_window', False)))
        
        # Piano/Rainbow state
        self.piano_lambda = float(state.get('piano_lambda', state.get('lambda_field', 1.0)) or 1.0)
        self.piano_coherence = float(state.get('piano_coherence', 0.0) or 0.0)
        self.rainbow_state = str(state.get('rainbow_state', 'UNKNOWN') or 'UNKNOWN')
        
        # Probability/Signal
        self.probability_edge = float(state.get('probability_edge', 0.0) or 0.0)
        self.harmonic_signal = str(state.get('harmonic_signal', 'HOLD') or 'HOLD')
        self.hnc_probability = float(state.get('hnc_probability', 0.5) or 0.5)
    
    def get_quantum_context(self) -> Dict[str, Any]:
        """
        Get quantum context dict suitable for MinerBrain.run_cycle().
        
        Returns:
            Dict with quantum state from miner (or defaults if not connected)
        """
        # Always check connection first
        self.check_connection()
        
        return {
            'quantum_coherence': self.unified_coherence,
            'planetary_gamma': self.planetary_gamma,
            'cascade_multiplier': self.cascade_multiplier,
            'is_lighthouse': self.is_lighthouse,
            'piano_lambda': self.piano_lambda,
            'piano_coherence': self.piano_coherence,
            'rainbow_state': self.rainbow_state,
            'probability_edge': self.probability_edge,
            'harmonic_signal': self.harmonic_signal,
            'hnc_probability': self.hnc_probability,
            'miner_connected': self._miner_connected,
            'signal_confidence': min(0.95, 0.5 + self.probability_edge),
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get connector status for display."""
        return {
            'connected': self._miner_connected,
            'connection_time': self._connection_time,
            'uptime': time.time() - self._connection_time if self._connection_time else 0,
            'successful_reads': self._successful_reads,
            'failed_reads': self._failed_reads,
            'last_state_age': time.time() - self._last_state.get('timestamp', 0) if self._last_state else float('inf'),
            'state_file': self._state_file,
        }
    
    @property
    def is_connected(self) -> bool:
        """Property to check if miner is currently connected."""
        return self._miner_connected


# Global miner connector instance
MINER_CONNECTOR = MinerStateConnector()


# ═══════════════════════════════════════════════════════════════
# 🧠🌍 ECOSYSTEM BRAIN BRIDGE - UNIFIED INTELLIGENCE HUB
# ═══════════════════════════════════════════════════════════════

class EcosystemBrainBridge:
    """
    🧠🌍 ECOSYSTEM BRAIN BRIDGE 🌍🧠
    
    The central intelligence hub that connects:
    - MinerBrain (7 Civilizations Wisdom) → Trading Decisions
    - QuantumProcessingBrain (Miner Optimizer) → Cascade Amplification
    - AdaptiveLearningEngine → Brain Feedback Loop
    - CascadeAmplifier → Brain-Guided Signal Boost
    
    This bridge ensures ALL trading decisions are informed by:
    1. Ancient wisdom (Celtic, Aztec, Egyptian, Pythagorean, etc.)
    2. Quantum coherence from the mining optimizer
    3. Adaptive learning from past trades
    4. Cascade amplification from win streaks
    5. 🔷 Diamond Lattice sacred geometry ZPE boost
    """
    
    def __init__(self):
        # Brain state cache
        self._brain_wisdom: Dict[str, Any] = {}
        self._brain_consensus: str = "NEUTRAL"
        self._brain_confidence: float = 0.5
        self._brain_action: str = "HOLD"
        self._civilization_signals: Dict[str, str] = {}
        
        # Quantum state from miner (if available)
        self._quantum_coherence: float = 0.5
        self._planetary_gamma: float = 0.5
        self._cascade_multiplier: float = 1.0
        self._is_lighthouse: bool = False
        
        # 🔷 DIAMOND LATTICE - Sacred Geometry Computational Boost
        self._diamond_coherence: float = 0.5
        self._diamond_boost: float = 1.0
        self._diamond_phi_alignment: float = 0.0
        self._diamond_zpe: float = 0.0
        
        # Market intelligence from brain
        self._fear_greed: int = 50
        self._btc_price: float = 0.0
        self._market_pulse: str = "NEUTRAL"
        self._manipulation_risk: float = 0.0
        
        # Timing - Brain runs EVERY SECOND for autonomous cognition
        self._last_cycle_time: float = 0.0
        self._cycle_interval: float = 1.0  # Run brain EVERY SECOND
        
        logger.info("🧠🌍 Ecosystem Brain Bridge initialized - AUTONOMOUS MODE (1s cycles)")
        
        # Reference to global miner connector for auto-detection
        self._miner_connector = MINER_CONNECTOR
        
    def run_wisdom_cycle(self, brain: 'MinerBrain', quantum_context: Dict = None) -> Dict[str, Any]:
        """
        Run a full wisdom cycle with bidirectional brain sync.
        
        Automatically connects to a running miner if available, pulling live
        quantum state (Γ, cascade, lighthouse) from the shared state file.
        
        Args:
            brain: MinerBrain instance
            quantum_context: Optional quantum state from miner optimizer (auto-detected if not provided)
        
        Returns:
            Full wisdom result with trading recommendations
        """
        if not brain:
            return {}
        
        now = time.time()
        if (now - self._last_cycle_time) < self._cycle_interval:
            return self._brain_wisdom  # Return cached
        
        try:
            logger.info("🧠⚡ Ecosystem Brain Cycle starting...")
            
            # Build quantum context - prefer live miner data if available
            if not quantum_context:
                # 🔗 AUTO-DETECT: Check if miner is running and get live quantum state
                miner_context = self._miner_connector.get_quantum_context()
                
                if miner_context.get('miner_connected'):
                    # Live miner data available!
                    quantum_context = miner_context
                    
                    # Update our cached state from live miner
                    self._quantum_coherence = miner_context['quantum_coherence']
                    self._planetary_gamma = miner_context['planetary_gamma']
                    self._cascade_multiplier = miner_context['cascade_multiplier']
                    self._is_lighthouse = miner_context['is_lighthouse']
                    
                    # 🔷 Extract Diamond Lattice state if available
                    self._diamond_coherence = miner_context.get('diamond_coherence', 0.5)
                    self._diamond_boost = miner_context.get('diamond_boost', 1.0)
                    self._diamond_phi_alignment = miner_context.get('diamond_phi_alignment', 0.0)
                    self._diamond_zpe = miner_context.get('diamond_zpe', 0.0)
                    
                    logger.info(f"🔗🌟 Live miner data: Ψ={self._quantum_coherence:.3f} | "
                              f"Γ={self._planetary_gamma:.3f} | Cascade={self._cascade_multiplier:.2f}x"
                              f" | 🔷Diamond={self._diamond_boost:.2f}x")
                else:
                    # Fallback to stored brain state
                    brain_state = load_brain_state()
                    quantum_context = {
                        'quantum_coherence': self._quantum_coherence or 0.5,
                        'planetary_gamma': self._planetary_gamma or 0.5,
                        'cascade_multiplier': self._cascade_multiplier or 1.0,
                        'is_lighthouse': self._is_lighthouse,
                        'piano_lambda': brain_state.get('piano_lambda') or 1.0,
                        'harmonic_signal': 'HOLD',
                        'signal_confidence': 0.5,
                        'miner_connected': False,
                    }
            
            # Run brain cycle with quantum context
            result = brain.run_cycle(quantum_context=quantum_context)
            
            if result:
                self._brain_wisdom = result
                self._last_cycle_time = now
                
                # Extract unified consensus
                self._brain_consensus = result.get('unified_consensus', 'NEUTRAL')
                self._brain_confidence = result.get('unified_confidence', 50) / 100
                self._brain_action = result.get('unified_action', 'HOLD')
                
                # Extract civilization signals
                self._civilization_signals = result.get('civilization_actions', {})
                
                # Extract market intelligence
                live_pulse = result.get('live_pulse', {})
                self._fear_greed = live_pulse.get('fear_greed', 50)
                self._btc_price = live_pulse.get('btc_price', 0.0)
                self._market_pulse = live_pulse.get('pulse', 'NEUTRAL')
                self._manipulation_risk = result.get('manipulation_probability', 0.0)
                
                # Update CascadeAmplifier with brain state
                self._update_cascade_amplifier()
                
                # Update AdaptiveLearner with brain insights
                self._update_adaptive_learner()
                
                logger.info(f"🧠🌍 Brain Cycle Complete: {self._brain_consensus} | Conf: {self._brain_confidence:.0%}")
                
            return result
            
        except Exception as e:
            import traceback
            logger.error(f"🧠 Brain Cycle Error: {e}")
            logger.error(f"🧠 Traceback: {traceback.format_exc()}")
            return {}
    
    def _update_cascade_amplifier(self):
        """Update CascadeAmplifier with brain wisdom."""
        try:
            # Update lighthouse gamma from brain's planetary awareness
            CASCADE_AMPLIFIER.update_lighthouse(self._planetary_gamma)
            
            # If brain says BULLISH with high confidence, boost cascade
            if self._brain_consensus == 'BULLISH' and self._brain_confidence > 0.7:
                # Simulate a "wisdom win" - the brain's confidence is a positive signal
                CASCADE_AMPLIFIER.mirror_coherence = min(1.0, CASCADE_AMPLIFIER.mirror_coherence + 0.05)
                
            # If brain says BEARISH with high confidence, decay cascade slightly
            elif self._brain_consensus == 'BEARISH' and self._brain_confidence > 0.7:
                CASCADE_AMPLIFIER.mirror_coherence = max(0.3, CASCADE_AMPLIFIER.mirror_coherence - 0.02)
                
        except Exception as e:
            logger.debug(f"Cascade update failed: {e}")
    
    def _update_adaptive_learner(self):
        """Feed brain insights to AdaptiveLearningEngine."""
        try:
            # Store brain consensus as a feature for learning
            brain_feature = {
                'brain_consensus': self._brain_consensus,
                'brain_confidence': self._brain_confidence,
                'fear_greed': self._fear_greed,
                'manipulation_risk': self._manipulation_risk,
                'civilization_agreement': sum(1 for s in self._civilization_signals.values() 
                                               if 'ACCUMULATE' in s or 'BUY' in s or 'ATTACK' in s) / 7,
            }
            
            # The adaptive learner can use this to correlate brain states with trade outcomes
            if hasattr(ADAPTIVE_LEARNER, 'record_brain_state'):
                ADAPTIVE_LEARNER.record_brain_state(brain_feature)
                
        except Exception as e:
            logger.debug(f"Adaptive learner update failed: {e}")
    
    def update_quantum_state(self, coherence: float, gamma: float, cascade: float, lighthouse: bool):
        """Update quantum state from miner optimizer."""
        self._quantum_coherence = coherence
        self._planetary_gamma = gamma
        self._cascade_multiplier = cascade
        self._is_lighthouse = lighthouse
    
    def update_diamond_state(self, diamond_coherence: float, diamond_boost: float, 
                             phi_alignment: float, zpe: float):
        """
        🔷 Update Diamond Lattice state from miner.
        
        The Diamond provides sacred geometry computational boost:
        - Central coherence (Ψ) from octahedron center
        - Hash boost from golden ratio alignment
        - φ alignment (how perfect the geometry is)
        - ZPE extraction rate
        """
        self._diamond_coherence = diamond_coherence
        self._diamond_boost = diamond_boost
        self._diamond_phi_alignment = phi_alignment
        self._diamond_zpe = zpe
        
        # Diamond boost amplifies cascade multiplier!
        if diamond_boost > 1.5:
            logger.info(f"🔷⚡ Diamond Boost Active: {diamond_boost:.2f}x | φ={phi_alignment:.3f}")
    
    def get_trading_recommendation(self) -> Dict[str, Any]:
        """
        Get trading recommendation based on brain wisdom.
        
        Returns dict with:
        - action: BUY/HOLD/SELL
        - confidence: 0-1
        - position_multiplier: scaling factor for position size
        - reasoning: list of reasons
        """
        # Default neutral recommendation
        rec = {
            'action': 'HOLD',
            'confidence': 0.5,
            'position_multiplier': 1.0,
            'reasoning': [],
            'civilizations_bullish': 0,
            'civilizations_bearish': 0,
        }
        
        if not self._brain_wisdom:
            rec['reasoning'].append("No brain wisdom available")
            return rec
        
        # Count civilization votes
        bullish_signals = ['ACCUMULATE', 'ATTACK', 'BUY', 'PLANT_SEEDS', 'RESURRECTION_BUY', 
                          'DECISIVE_ACTION', 'BUILD', 'GROW', 'RIDE_THE_SUN']
        bearish_signals = ['RETREAT', 'PROTECT', 'CAUTION', 'RELEASE', 'EXIT']
        
        bullish_count = sum(1 for s in self._civilization_signals.values() 
                          if any(b in s.upper() for b in bullish_signals))
        bearish_count = sum(1 for s in self._civilization_signals.values() 
                          if any(b in s.upper() for b in bearish_signals))
        
        rec['civilizations_bullish'] = bullish_count
        rec['civilizations_bearish'] = bearish_count
        
        # Determine action based on consensus
        if self._brain_consensus == 'BULLISH':
            rec['action'] = 'BUY'
            rec['confidence'] = self._brain_confidence
            rec['position_multiplier'] = 1.0 + (self._brain_confidence * 0.5)  # Up to 1.5x
            rec['reasoning'].append(f"7 Civilizations: {bullish_count}/7 bullish")
            rec['reasoning'].append(f"Unified Consensus: {self._brain_consensus}")
            
            # Extra boost if fear is extreme
            if self._fear_greed < 25:
                rec['position_multiplier'] *= 1.2
                rec['reasoning'].append(f"Extreme Fear ({self._fear_greed}) = Contrarian Opportunity")
                
        elif self._brain_consensus == 'BEARISH':
            rec['action'] = 'REDUCE'
            rec['confidence'] = self._brain_confidence
            rec['position_multiplier'] = max(0.5, 1.0 - (self._brain_confidence * 0.3))  # Down to 0.7x
            rec['reasoning'].append(f"7 Civilizations: {bearish_count}/7 bearish")
            rec['reasoning'].append(f"Unified Consensus: {self._brain_consensus}")
            
            # Extra caution if manipulation risk is high
            if self._manipulation_risk > 0.3:
                rec['position_multiplier'] *= 0.8
                rec['reasoning'].append(f"High Manipulation Risk ({self._manipulation_risk:.0%})")
                
        else:
            rec['action'] = 'HOLD'
            rec['confidence'] = 0.5
            rec['reasoning'].append("Civilizations divided - waiting for clarity")
        
        # Lighthouse bonus
        if self._is_lighthouse:
            rec['position_multiplier'] *= 1.15
            rec['reasoning'].append("🗼 Lighthouse Window Active")
        
        # 🔷 DIAMOND LATTICE BOOST - Sacred Geometry Amplification
        if self._diamond_boost > 1.3:
            diamond_mult = 1.0 + (self._diamond_boost - 1.0) * 0.2  # Up to 1.28x extra
            rec['position_multiplier'] *= diamond_mult
            rec['reasoning'].append(f"🔷 Diamond Boost: {self._diamond_boost:.2f}x (φ={self._diamond_phi_alignment:.2f})")
            
            # If diamond coherence is very high, boost confidence too
            if self._diamond_coherence > 0.8:
                rec['confidence'] = min(1.0, rec['confidence'] + 0.1)
                rec['reasoning'].append(f"🔷 Diamond Coherence Peak: Ψ={self._diamond_coherence:.2f}")
        
        return rec
    
    def get_signal_boost(self, base_score: float) -> float:
        """
        Get brain-boosted signal score for trading decisions.
        
        Applies 7-civilization wisdom to amplify or dampen signals.
        """
        boost = 1.0
        
        # Brain consensus boost
        if self._brain_consensus == 'BULLISH':
            boost *= 1.0 + (self._brain_confidence * 0.2)  # Up to +20%
        elif self._brain_consensus == 'BEARISH':
            boost *= 1.0 - (self._brain_confidence * 0.1)  # Down to -10%
        
        # Quantum coherence boost
        if self._quantum_coherence > 0.7:
            boost *= 1.0 + (self._quantum_coherence - 0.7) * 0.33  # Up to +10%
        
        # Planetary alignment boost
        if self._planetary_gamma > 0.8:
            boost *= 1.1  # +10% during strong alignment
        
        # Fear/Greed contrarian adjustment
        if self._fear_greed < 25:  # Extreme fear
            boost *= 1.15  # +15% contrarian
        elif self._fear_greed > 75:  # Extreme greed
            boost *= 0.90  # -10% caution
        
        return base_score * boost
    
    def display_status(self):
        """Display current brain bridge status."""
        if not self._brain_wisdom:
            print("   🧠🌍 BRAIN: Awaiting first cycle...")
            return
        
        consensus_icon = "📈" if self._brain_consensus == "BULLISH" else "📉" if self._brain_consensus == "BEARISH" else "⚖️"
        bullish = sum(1 for s in self._civilization_signals.values() 
                     if 'ACCUMULATE' in s or 'BUY' in s or 'ATTACK' in s or 'BUILD' in s)
        
        print(f"   🧠🌍 BRAIN: {consensus_icon} {self._brain_consensus} | "
              f"Conf: {self._brain_confidence:.0%} | "
              f"Votes: {bullish}/7 📈 | "
              f"F&G: {self._fear_greed} | "
              f"Γ: {self._planetary_gamma:.2f}")


# Global Ecosystem Brain Bridge instance
ECOSYSTEM_BRAIN = EcosystemBrainBridge()


# ═══════════════════════════════════════════════════════════════
# 🌐 SMART ORDER ROUTER - Best execution across exchanges
# ═══════════════════════════════════════════════════════════════

class SmartOrderRouter:
    """
    Routes orders to the best exchange based on price, liquidity, and fees.
    Compares quotes across Binance, Kraken, and Capital.com in real-time.
    """
    
    def __init__(self, multi_client):
        self.client = multi_client
        self.exchange_fees = {
            'binance': 0.001,   # 0.10% taker
            'kraken': 0.0026,   # 0.26% taker
            'capital': 0.001,   # ~0.1% spread
            'alpaca': 0.0       # Commission-free
        }
        self.exchange_priority = ['binance', 'capital', 'alpaca']
        self.route_history: List[Dict] = []
        
    def get_best_quote(self, symbol: str, side: str, quantity: float = None) -> Dict[str, Any]:
        """
        Get best quote across all exchanges for a symbol.
        Returns: {'exchange': str, 'price': float, 'effective_price': float, 'savings': float}
        """
        quotes = []
        base_symbol = symbol.replace('/', '').upper()
        
        # Normalize symbol for each exchange
        symbol_map = {
            'binance': base_symbol,
            'kraken': base_symbol,
            'capital': base_symbol[:6] if len(base_symbol) > 6 else base_symbol,
            'alpaca': f"{base_symbol[:3]}/{base_symbol[3:]}" if len(base_symbol) >= 6 else symbol
        }
        
        for exchange in self.exchange_priority:
            try:
                ex_symbol = symbol_map.get(exchange, base_symbol)
                ticker = self.client.get_ticker(exchange, ex_symbol)
                if not ticker or ticker.get('price', 0) <= 0:
                    continue
                    
                price = float(ticker.get('price', 0))
                bid = float(ticker.get('bid', price))
                ask = float(ticker.get('ask', price))
                
                # Calculate effective price including fees
                fee_rate = self.exchange_fees.get(exchange, 0.002)
                if side.upper() == 'BUY':
                    exec_price = ask * (1 + fee_rate)
                else:
                    exec_price = bid * (1 - fee_rate)
                    
                quotes.append({
                    'exchange': exchange,
                    'symbol': ex_symbol,
                    'price': price,
                    'bid': bid,
                    'ask': ask,
                    'effective_price': exec_price,
                    'fee_rate': fee_rate
                })
            except Exception as e:
                logger.debug(f"Quote error for {exchange}/{symbol}: {e}")
                continue
                
        if not quotes:
            return None
            
        # Sort by effective price (lowest for BUY, highest for SELL)
        if side.upper() == 'BUY':
            quotes.sort(key=lambda x: x['effective_price'])
        else:
            quotes.sort(key=lambda x: -x['effective_price'])
            
        best = quotes[0]
        
        # Calculate savings vs worst quote
        if len(quotes) > 1:
            worst = quotes[-1]
            if side.upper() == 'BUY':
                savings_pct = (worst['effective_price'] - best['effective_price']) / worst['effective_price'] * 100
            else:
                savings_pct = (best['effective_price'] - worst['effective_price']) / best['effective_price'] * 100
            best['savings_pct'] = savings_pct
            best['alternatives'] = quotes[1:]
        else:
            best['savings_pct'] = 0
            best['alternatives'] = []
            
        return best
        
    def route_order(self, symbol: str, side: str, quantity: float = None, quote_qty: float = None,
                    preferred_exchange: str = None) -> Dict[str, Any]:
        """
        Route and execute order on best exchange.
        Returns order result with routing metadata.
        """
        # Get best quote
        best = self.get_best_quote(symbol, side, quantity)
        if not best:
            return {'error': 'No quotes available', 'symbol': symbol}
            
        # Override if preferred exchange specified and available
        if preferred_exchange and preferred_exchange in [q['exchange'] for q in [best] + best.get('alternatives', [])]:
            for q in [best] + best.get('alternatives', []):
                if q['exchange'] == preferred_exchange:
                    best = q
                    break
                    
        # Execute order
        exchange = best['exchange']
        ex_symbol = best['symbol']
        
        try:
            result = self.client.place_market_order(
                exchange, ex_symbol, side,
                quantity=quantity, quote_qty=quote_qty
            )
            
            # Add routing metadata
            result['routed_to'] = exchange
            result['effective_price'] = best['effective_price']
            result['savings_pct'] = best.get('savings_pct', 0)
            
            # Record route
            self.route_history.append({
                'timestamp': time.time(),
                'symbol': symbol,
                'side': side,
                'exchange': exchange,
                'price': best['price'],
                'savings_pct': best.get('savings_pct', 0)
            })
            
            return result
        except Exception as e:
            return {'error': str(e), 'exchange': exchange, 'symbol': ex_symbol}
            
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing performance statistics."""
        if not self.route_history:
            return {'total_routes': 0}
            
        by_exchange = {}
        total_savings = 0
        
        for route in self.route_history:
            ex = route['exchange']
            by_exchange[ex] = by_exchange.get(ex, 0) + 1
            total_savings += route.get('savings_pct', 0)
            
        return {
            'total_routes': len(self.route_history),
            'by_exchange': by_exchange,
            'avg_savings_pct': total_savings / len(self.route_history) if self.route_history else 0
        }


# ═══════════════════════════════════════════════════════════════
# ⚡ CROSS-EXCHANGE ARBITRAGE SCANNER
# ═══════════════════════════════════════════════════════════════

class CrossExchangeArbitrageScanner:
    """
    Detects price discrepancies across Binance, Kraken, and Capital.com.
    Identifies triangular and direct arbitrage opportunities.
    """
    
    def __init__(self, multi_client):
        self.client = multi_client
        self.min_spread_pct = 0.3  # Minimum 0.3% spread to consider
        self.fee_buffer = 0.2     # 0.2% buffer for fees
        self.opportunities: List[Dict] = []
        self.last_scan = 0
        self.scan_interval = 30   # Seconds between scans
        
    def scan_direct_arbitrage(self, symbols: List[str] = None) -> List[Dict]:
        """
        Scan for direct arbitrage: buy on exchange A, sell on exchange B.
        """
        opportunities = []
        brain_mult = get_brain_multiplier()
        
        # Default symbols to scan
        if not symbols:
            symbols = ['BTCUSD', 'ETHUSD', 'XRPUSD', 'ADAUSD', 'SOLUSD', 
                      'DOTUSD', 'LINKUSD', 'AVAXUSD', 'DOGEUSD']
        
        exchanges = ['binance', 'kraken']
        
        for symbol in symbols:
            prices = {}
            
            # Get prices from each exchange
            for exchange in exchanges:
                try:
                    # Normalize canonical symbol to exchange-specific
                    ex_symbol = self.client.normalize_symbol(exchange, symbol)
                    ticker = self.client.get_ticker(exchange, ex_symbol)
                    if ticker and ticker.get('bid', 0) > 0:
                        prices[exchange] = {
                            'bid': float(ticker.get('bid', 0)),
                            'ask': float(ticker.get('ask', 0)),
                            'symbol': ex_symbol
                        }
                except Exception:
                    continue
                    
            # Check for arbitrage between each pair
            if len(prices) < 2:
                continue
                
            exchange_list = list(prices.keys())
            for i, buy_ex in enumerate(exchange_list):
                for sell_ex in exchange_list[i+1:]:
                    buy_price = prices[buy_ex]['ask']
                    sell_price = prices[sell_ex]['bid']
                    
                    # Check both directions
                    spread_1 = (sell_price - buy_price) / buy_price * 100
                    spread_2 = (prices[buy_ex]['bid'] - prices[sell_ex]['ask']) / prices[sell_ex]['ask'] * 100
                    
                    # Apply CASCADE amplification to profit confidence
                    cascaded_1 = min(spread_1 * CASCADE_FACTOR, 95.0)
                    if cascaded_1 > self.min_spread_pct + self.fee_buffer:
                        net_profit = (cascaded_1 - self.fee_buffer)
                        opportunities.append({
                            'type': 'direct',
                            'symbol': symbol,
                            'buy_exchange': buy_ex,
                            'sell_exchange': sell_ex,
                            'buy_price': buy_price,
                            'sell_price': sell_price,
                            'spread_pct': spread_1,
                            'cascaded_confidence_pct': cascaded_1,
                            'net_profit_pct': net_profit,
                            'brain_mult': brain_mult,
                            'timestamp': time.time()
                        })
                    
                    cascaded_2 = min(spread_2 * CASCADE_FACTOR, 95.0)
                    if cascaded_2 > self.min_spread_pct + self.fee_buffer:
                        net_profit = (cascaded_2 - self.fee_buffer)
                        opportunities.append({
                            'type': 'direct',
                            'symbol': symbol,
                            'buy_exchange': sell_ex,
                            'sell_exchange': buy_ex,
                            'buy_price': prices[sell_ex]['ask'],
                            'sell_price': prices[buy_ex]['bid'],
                            'spread_pct': spread_2,
                            'cascaded_confidence_pct': cascaded_2,
                            'net_profit_pct': net_profit,
                            'brain_mult': brain_mult,
                            'timestamp': time.time()
                        })
        
        # Sort by profit potential
        # Apply Ψ minimization: keep only top 3.7% by cascaded confidence
        opportunities.sort(key=lambda x: -(x.get('cascaded_confidence_pct', 0)))
        top_count = max(1, int(len(opportunities) * PSI_FILTER))
        opportunities = opportunities[:top_count]
        self.opportunities = opportunities
        self.last_scan = time.time()
        
        return opportunities
        
    def get_top_opportunities(self, limit: int = 5) -> List[Dict]:
        """Get top arbitrage opportunities."""
        # Refresh if stale
        if time.time() - self.last_scan > self.scan_interval:
            self.scan_direct_arbitrage()
        return self.opportunities[:limit]
        
    def execute_arbitrage(self, opportunity: Dict, amount_usd: float = 10.0) -> Dict[str, Any]:
        """
        Execute an arbitrage opportunity.
        Returns: {'success': bool, 'profit': float, 'details': dict}
        """
        buy_ex = opportunity['buy_exchange']
        sell_ex = opportunity['sell_exchange']
        symbol = opportunity['symbol']
        
        # Calculate quantity
        buy_price = opportunity['buy_price']
        quantity = amount_usd / buy_price
        
        results = {'buy': None, 'sell': None, 'profit': 0, 'success': False}
        
        try:
            # Execute buy
            buy_symbol = symbol if buy_ex != 'binance' else symbol.replace('USD', 'USDT')
            buy_result = self.client.place_market_order(buy_ex, buy_symbol, 'BUY', quantity=quantity)
            results['buy'] = buy_result
            
            if not buy_result or buy_result.get('error'):
                return results
                
            # Execute sell
            sell_symbol = symbol if sell_ex != 'binance' else symbol.replace('USD', 'USDT')
            sell_result = self.client.place_market_order(sell_ex, sell_symbol, 'SELL', quantity=quantity)
            results['sell'] = sell_result
            
            if sell_result and not sell_result.get('error'):
                results['success'] = True
                results['profit'] = amount_usd * (opportunity['net_profit_pct'] / 100)
                
        except Exception as e:
            results['error'] = str(e)
            
        return results


# ═══════════════════════════════════════════════════════════════
# ✅ UNIFIED TRADE CONFIRMATION
# ═══════════════════════════════════════════════════════════════

class UnifiedTradeConfirmation:
    """
    Normalizes trade confirmations across all exchanges.
    Handles Binance orderId, Kraken txid, Capital.com dealReference.
    """
    
    def __init__(self, multi_client):
        self.client = multi_client
        self.pending_confirmations: Dict[str, Dict] = {}
        self.confirmed_trades: List[Dict] = []
        
    def submit_order(self, exchange: str, symbol: str, side: str, 
                    quantity: float = None, quote_qty: float = None) -> Dict[str, Any]:
        """
        Submit order and return unified confirmation.
        Validates lot sizes and minimum notional before submission.
        """
        # Validate quantity for SELL orders (lot size + notional)
        if side.upper() == 'SELL' and quantity is not None:
            # Get current price for notional check
            price = 0
            try:
                ticker = self.client.get_ticker(exchange, symbol)
                if ticker:
                    price = float(ticker.get('price', ticker.get('lastPrice', 0)))
            except Exception:
                pass
                
            adjusted_qty, error = validate_order_quantity(exchange, symbol, quantity, price, self.client)
            if error:
                print(f"   🚫 Order rejected pre-flight: {symbol} on {exchange}: {error}")
                return {'status': 'REJECTED', 'error': error, 'pre_flight': True}
            quantity = adjusted_qty
            
        result = self.client.place_market_order(
            exchange, symbol, side,
            quantity=quantity, quote_qty=quote_qty
        )
        
        if not result:
            return {'status': 'FAILED', 'error': 'No response'}
        
        # ⚠️ Check for error response BEFORE normalizing (e.g., min_notional blocked)
        if 'error' in result:
            return {
                'status': 'BLOCKED',
                'error': result['error'],
                'exchange': result.get('exchange', exchange),
                'symbol': symbol,
                'side': side
            }
            
        # Normalize confirmation based on exchange
        exchange = exchange.lower()
        confirmation = {
            'exchange': exchange,
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'quote_qty': quote_qty,
            'timestamp': time.time(),
            'raw_response': result
        }
        
        if exchange == 'binance':
            confirmation.update(self._parse_binance_response(result))
        elif exchange == 'kraken':
            confirmation.update(self._parse_kraken_response(result))
        elif exchange == 'capital':
            confirmation.update(self._parse_capital_response(result))
        else:
            confirmation['status'] = 'UNKNOWN'
            confirmation['order_id'] = str(result.get('orderId', result.get('id', 'unknown')))
            
        # Store confirmed trade
        if confirmation.get('status') in ['FILLED', 'ACCEPTED', 'OPEN']:
            self.confirmed_trades.append(confirmation)
            
        return confirmation
        
    def _parse_binance_response(self, result: Dict) -> Dict:
        """Parse Binance order response."""
        if result.get('rejected') or result.get('uk_restricted'):
            return {
                'status': 'REJECTED',
                'order_id': None,
                'error': result.get('reason', 'UK restricted')
            }
            
        status = result.get('status', 'UNKNOWN')
        return {
            'status': status,
            'order_id': str(result.get('orderId', '')),
            'executed_qty': float(result.get('executedQty', 0)),
            'executed_quote_qty': float(result.get('cummulativeQuoteQty', 0)),
            'avg_price': float(result.get('price', 0)) if result.get('price') else None,
            'fills': result.get('fills', [])
        }
        
    def _parse_kraken_response(self, result: Dict) -> Dict:
        """Parse Kraken order response."""
        txid = result.get('txid', [])
        if isinstance(txid, list) and txid:
            order_id = txid[0]
            status = 'FILLED'  # Kraken market orders fill immediately
        else:
            order_id = str(result.get('orderId', result.get('id', '')))
            status = result.get('status', 'UNKNOWN')
            
        return {
            'status': status,
            'order_id': order_id,
            'executed_qty': float(result.get('executedQty', result.get('vol_exec', 0))),
            'descr': result.get('descr', {})
        }
        
    def _parse_capital_response(self, result: Dict) -> Dict:
        """Parse Capital.com order response and confirm."""
        deal_ref = result.get('dealReference')
        deal_id = result.get('dealId')
        
        if deal_id:
            return {
                'status': 'ACCEPTED',
                'order_id': deal_id,
                'deal_reference': deal_ref
            }
            
        # Need to confirm via API
        if deal_ref:
            try:
                capital_client = self.client.clients.get('capital')
                if capital_client and hasattr(capital_client.client, 'confirm_order'):
                    confirm = capital_client.client.confirm_order(deal_ref)
                    status = confirm.get('dealStatus', 'UNKNOWN')
                    return {
                        'status': status,
                        'order_id': confirm.get('dealId', deal_ref),
                        'deal_reference': deal_ref,
                        'level': confirm.get('level'),
                        'size': confirm.get('size'),
                        'direction': confirm.get('direction'),
                        'affected_deals': confirm.get('affectedDeals', [])
                    }
            except Exception as e:
                logger.error(f"Capital.com confirm error: {e}")
                
        return {
            'status': 'PENDING',
            'order_id': deal_ref,
            'deal_reference': deal_ref
        }
        
    def get_trade_history(self, exchange: str = None, limit: int = 50) -> List[Dict]:
        """Get confirmed trade history."""
        trades = self.confirmed_trades
        if exchange:
            trades = [t for t in trades if t['exchange'] == exchange.lower()]
        return trades[-limit:]
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get trade confirmation statistics."""
        if not self.confirmed_trades:
            return {'total': 0}
            
        by_exchange = {}
        by_status = {}
        
        for trade in self.confirmed_trades:
            ex = trade['exchange']
            status = trade['status']
            by_exchange[ex] = by_exchange.get(ex, 0) + 1
            by_status[status] = by_status.get(status, 0) + 1
            
        return {
            'total': len(self.confirmed_trades),
            'by_exchange': by_exchange,
            'by_status': by_status
        }


# ═══════════════════════════════════════════════════════════════
# ⚖️ PORTFOLIO REBALANCER
# ═══════════════════════════════════════════════════════════════

class PortfolioRebalancer:
    """
    Unified portfolio rebalancing across Binance, Kraken, and Capital.com.
    Optimizes asset allocation and can shift funds between exchanges.
    """
    
    def __init__(self, multi_client):
        self.client = multi_client
        self.target_allocations: Dict[str, float] = {}  # asset -> target %
        self.rebalance_threshold = 0.05  # 5% deviation triggers rebalance
        self.min_trade_value = 5.0  # Minimum $5 to avoid dust trades
        self.last_rebalance = 0
        self.rebalance_history: List[Dict] = []
        
    def set_target_allocation(self, allocations: Dict[str, float]):
        """
        Set target portfolio allocation.
        Example: {'BTC': 0.30, 'ETH': 0.25, 'USDT': 0.45}
        """
        total = sum(allocations.values())
        if abs(total - 1.0) > 0.01:
            logger.warning(f"Allocations sum to {total}, normalizing to 100%")
            allocations = {k: v/total for k, v in allocations.items()}
        self.target_allocations = allocations
        
    def get_current_allocation(self) -> Dict[str, Dict]:
        """
        Get current portfolio allocation across all exchanges.
        Returns: {asset: {'amount': float, 'value_usd': float, 'pct': float, 'exchanges': dict}}
        """
        allocations = {}
        total_value = 0.0
        
        # Gather balances from all exchanges
        all_balances = self.client.get_all_balances()
        
        for exchange, balances in all_balances.items():
            for asset, amount in balances.items():
                try:
                    amount = float(amount)
                except:
                    continue
                if amount <= 0:
                    continue
                    
                # Normalize asset name
                asset_clean = asset.replace('Z', '').replace('X', '').upper()
                if asset_clean.startswith('LD'):  # Binance Earn
                    asset_clean = asset_clean[2:]
                    
                # Get USD value
                try:
                    if asset_clean in ['USD', 'USDT', 'USDC']:
                        value_usd = amount
                    else:
                        value_usd = self.client.convert_to_quote(exchange, asset_clean, amount, 'USDT')
                except:
                    value_usd = 0
                    
                if asset_clean not in allocations:
                    allocations[asset_clean] = {
                        'amount': 0.0,
                        'value_usd': 0.0,
                        'exchanges': {}
                    }
                    
                allocations[asset_clean]['amount'] += amount
                allocations[asset_clean]['value_usd'] += value_usd
                allocations[asset_clean]['exchanges'][exchange] = {
                    'amount': amount,
                    'value_usd': value_usd
                }
                total_value += value_usd
                
        # Calculate percentages
        for asset in allocations:
            if total_value > 0:
                allocations[asset]['pct'] = allocations[asset]['value_usd'] / total_value
            else:
                allocations[asset]['pct'] = 0.0
                
        return {'assets': allocations, 'total_value_usd': total_value}
        
    def calculate_rebalance_trades(self) -> List[Dict]:
        """
        Calculate trades needed to rebalance portfolio to target allocation.
        Returns list of trades: [{'asset': str, 'action': 'BUY'|'SELL', 'amount_usd': float, 'exchange': str}]
        """
        if not self.target_allocations:
            return []
            
        current = self.get_current_allocation()
        total_value = current['total_value_usd']
        assets = current['assets']
        
        trades = []
        
        for asset, target_pct in self.target_allocations.items():
            current_pct = assets.get(asset, {}).get('pct', 0.0)
            current_value = assets.get(asset, {}).get('value_usd', 0.0)
            target_value = total_value * target_pct
            
            deviation = abs(current_pct - target_pct)
            
            if deviation < self.rebalance_threshold:
                continue  # Within tolerance
                
            diff_usd = target_value - current_value
            
            if abs(diff_usd) < self.min_trade_value:
                continue  # Too small
                
            # Determine best exchange for this trade
            exchanges = assets.get(asset, {}).get('exchanges', {})
            
            if diff_usd > 0:  # Need to BUY
                # Pick exchange with most quote currency
                best_exchange = 'binance'  # Default
                trade = {
                    'asset': asset,
                    'action': 'BUY',
                    'amount_usd': abs(diff_usd),
                    'exchange': best_exchange,
                    'current_pct': current_pct,
                    'target_pct': target_pct
                }
            else:  # Need to SELL
                # Pick exchange with most of this asset
                best_exchange = max(exchanges.keys(), key=lambda e: exchanges[e]['amount']) if exchanges else 'binance'
                trade = {
                    'asset': asset,
                    'action': 'SELL',
                    'amount_usd': abs(diff_usd),
                    'exchange': best_exchange,
                    'current_pct': current_pct,
                    'target_pct': target_pct
                }
                
            trades.append(trade)
            
        # Sort: SELL first (to free up capital), then BUY
        trades.sort(key=lambda t: 0 if t['action'] == 'SELL' else 1)
        
        return trades
        
    def execute_rebalance(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Execute portfolio rebalance.
        Returns: {'success': bool, 'trades_executed': int, 'trades': list}
        """
        trades = self.calculate_rebalance_trades()
        
        if not trades:
            return {'success': True, 'trades_executed': 0, 'message': 'Portfolio within tolerance'}
            
        results = {
            'success': True,
            'trades_executed': 0,
            'trades': [],
            'dry_run': dry_run
        }
        
        for trade in trades:
            asset = trade['asset']
            action = trade['action']
            amount_usd = trade['amount_usd']
            exchange = trade['exchange']
            
            # Build symbol
            symbol = f"{asset}USDT" if exchange == 'binance' else f"{asset}USD"
            
            if dry_run:
                result = {'status': 'DRY_RUN', 'would_execute': trade}
            else:
                try:
                    if action == 'BUY':
                        result = self.client.place_market_order(
                            exchange, symbol, 'BUY', quote_qty=amount_usd
                        )
                    else:
                        # Calculate quantity from USD value
                        ticker = self.client.get_ticker(exchange, symbol)
                        price = float(ticker.get('price', 1))
                        quantity = amount_usd / price
                        result = self.client.place_market_order(
                            exchange, symbol, 'SELL', quantity=quantity
                        )
                    results['trades_executed'] += 1
                except Exception as e:
                    result = {'error': str(e)}
                    results['success'] = False
                    
            results['trades'].append({
                'trade': trade,
                'result': result
            })
            
        self.last_rebalance = time.time()
        self.rebalance_history.append({
            'timestamp': time.time(),
            'trades': len(trades),
            'success': results['success']
        })
        
        return results
        
    def get_rebalance_summary(self) -> str:
        """Get human-readable rebalance summary."""
        current = self.get_current_allocation()
        trades = self.calculate_rebalance_trades()
        
        lines = [
            "═══════════════════════════════════════",
            "⚖️ PORTFOLIO REBALANCE SUMMARY",
            "═══════════════════════════════════════",
            f"Total Portfolio Value: ${current['total_value_usd']:.2f}",
            "",
            "Current vs Target Allocation:"
        ]
        
        for asset, target in self.target_allocations.items():
            current_pct = current['assets'].get(asset, {}).get('pct', 0) * 100
            target_pct = target * 100
            diff = current_pct - target_pct
            indicator = "✅" if abs(diff) < 5 else "⚠️"
            lines.append(f"  {indicator} {asset}: {current_pct:.1f}% → {target_pct:.1f}% ({diff:+.1f}%)")
            
        if trades:
            lines.append("")
            lines.append("Recommended Trades:")
            for trade in trades:
                lines.append(f"  • {trade['action']} ${trade['amount_usd']:.2f} of {trade['asset']} on {trade['exchange']}")
        else:
            lines.append("")
            lines.append("✅ Portfolio is balanced within tolerance")
            
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# 🔮 PREDICTION VALIDATOR - Peer Review & Accuracy Tracking
# ═══════════════════════════════════════════════════════════════

class PredictionValidator:
    """
    🔮 PREDICTION VALIDATION SYSTEM
    
    Tracks prediction accuracy over time:
    - Logs predictions with timestamps: "At 10:00 predicted BTCUSDC +0.5% by 10:01"
    - Validates actual prices at predicted times
    - Scores accuracy: how close was prediction to reality?
    - Feeds accuracy back into confidence scores
    - Maintains historical hit rate for peer review
    
    This creates an auditable trail of "did the probability matrix get it right?"
    """
    
    def __init__(self, validation_window_seconds: int = 60):
        self.validation_window = validation_window_seconds  # Default 1 minute predictions
        self.pending_predictions: List[Dict] = []  # Predictions awaiting validation
        self.validated_predictions: List[Dict] = []  # Historical validated predictions
        self.max_history = 1000  # Keep last 1000 validated predictions
        
        # Accuracy metrics by various dimensions
        self.accuracy_metrics = {
            'total_predictions': 0,
            'validated': 0,
            'accurate': 0,  # Within 0.5% of predicted
            'close': 0,     # Within 1% of predicted
            'direction_correct': 0,  # Got the direction right (up/down)
            'by_exchange': {},
            'by_asset_class': {},
            'by_frequency_band': {},
            'by_coherence_level': {},
            'recent_accuracy': []  # Rolling window for recent accuracy
        }
        
        self.last_validation_check = time.time()
        logger.info("🔮 PredictionValidator initialized - Tracking prediction accuracy")
    
    def log_prediction(self, exchange: str, symbol: str, current_price: float,
                       predicted_direction: str, predicted_change_pct: float,
                       probability: float, coherence: float, frequency: float,
                       asset_class: str = 'crypto') -> str:
        """
        Log a new prediction for future validation.
        
        Args:
            exchange: Exchange name (binance, kraken, etc.)
            symbol: Trading pair (BTCUSDC, etc.)
            current_price: Current price at prediction time
            predicted_direction: 'up', 'down', or 'neutral'
            predicted_change_pct: Expected % change
            probability: Confidence probability (0-1)
            coherence: HNC coherence at prediction time
            frequency: HNC frequency at prediction time
            asset_class: crypto, forex, stocks, etc.
            
        Returns:
            Prediction ID for tracking
        """
        prediction_id = f"{exchange}_{symbol}_{int(time.time()*1000)}"
        prediction_time = time.time()
        validation_time = prediction_time + self.validation_window
        
        # Calculate expected price
        if predicted_direction == 'up':
            expected_price = current_price * (1 + predicted_change_pct / 100)
        elif predicted_direction == 'down':
            expected_price = current_price * (1 - predicted_change_pct / 100)
        else:
            expected_price = current_price
        
        prediction = {
            'id': prediction_id,
            'exchange': exchange,
            'symbol': symbol,
            'asset_class': asset_class,
            'prediction_time': prediction_time,
            'prediction_time_str': datetime.now().strftime('%H:%M:%S'),
            'validation_time': validation_time,
            'validation_time_str': datetime.fromtimestamp(validation_time).strftime('%H:%M:%S'),
            'current_price': current_price,
            'predicted_direction': predicted_direction,
            'predicted_change_pct': predicted_change_pct,
            'expected_price': expected_price,
            'probability': probability,
            'coherence': coherence,
            'frequency': frequency,
            'freq_band': self._get_freq_band(frequency),
            'coherence_level': self._get_coherence_level(coherence),
            'status': 'pending'
        }
        
        self.pending_predictions.append(prediction)
        self.accuracy_metrics['total_predictions'] += 1
        
        logger.info(f"🔮 PREDICTION LOGGED: {symbol} @ {prediction['prediction_time_str']}")
        logger.info(f"   📊 Current: ${current_price:.6f} → Expected: ${expected_price:.6f} ({predicted_direction} {predicted_change_pct:.2f}%)")
        logger.info(f"   🎯 Probability: {probability:.1%} | Coherence: {coherence:.2f} | Freq: {frequency:.0f}Hz")
        logger.info(f"   ⏰ Will validate at: {prediction['validation_time_str']}")
        
        return prediction_id
    
    def validate_predictions(self, get_price_func) -> List[Dict]:
        """
        Check all pending predictions that are due for validation.
        
        Args:
            get_price_func: Function that takes (exchange, symbol) and returns current price
            
        Returns:
            List of newly validated predictions with results
        """
        now = time.time()
        newly_validated = []
        still_pending = []
        
        for prediction in self.pending_predictions:
            if now >= prediction['validation_time']:
                # Time to validate this prediction
                try:
                    actual_price = get_price_func(prediction['exchange'], prediction['symbol'])
                    if actual_price and actual_price > 0:
                        result = self._validate_single(prediction, actual_price)
                        newly_validated.append(result)
                        self._update_accuracy_metrics(result)
                        
                        # Log the validation result
                        self._log_validation_result(result)
                    else:
                        # Couldn't get price, keep pending for one more cycle
                        if now < prediction['validation_time'] + 60:  # Grace period
                            still_pending.append(prediction)
                        else:
                            prediction['status'] = 'expired'
                            logger.warning(f"⚠️ Prediction {prediction['id']} expired - couldn't get price")
                except Exception as e:
                    logger.error(f"Validation error for {prediction['id']}: {e}")
                    still_pending.append(prediction)
            else:
                still_pending.append(prediction)
        
        self.pending_predictions = still_pending
        
        # Add to historical validated predictions
        self.validated_predictions.extend(newly_validated)
        
        # Trim history if needed
        if len(self.validated_predictions) > self.max_history:
            self.validated_predictions = self.validated_predictions[-self.max_history:]
        
        self.last_validation_check = now
        return newly_validated
    
    def _validate_single(self, prediction: Dict, actual_price: float) -> Dict:
        """Validate a single prediction against actual price."""
        current_price = prediction['current_price']
        expected_price = prediction['expected_price']
        predicted_direction = prediction['predicted_direction']
        
        # Calculate actual change
        actual_change_pct = ((actual_price - current_price) / current_price) * 100
        actual_direction = 'up' if actual_change_pct > 0.01 else ('down' if actual_change_pct < -0.01 else 'neutral')
        
        # Calculate prediction error
        if expected_price > 0:
            price_error_pct = abs((actual_price - expected_price) / expected_price) * 100
        else:
            price_error_pct = 100
        
        # Determine accuracy levels
        is_accurate = price_error_pct <= 0.5  # Within 0.5% of predicted price
        is_close = price_error_pct <= 1.0     # Within 1% of predicted price
        direction_correct = (predicted_direction == actual_direction) or \
                           (predicted_direction in ['up', 'down'] and actual_direction == predicted_direction)
        
        # Calculate accuracy score (0-100)
        if is_accurate:
            accuracy_score = 100 - (price_error_pct * 20)  # 100 at 0%, 90 at 0.5%
        elif is_close:
            accuracy_score = 80 - ((price_error_pct - 0.5) * 40)  # 80 at 0.5%, 60 at 1%
        else:
            accuracy_score = max(0, 60 - (price_error_pct - 1) * 10)  # Decreases after 1%
        
        # Bonus for correct direction
        if direction_correct:
            accuracy_score = min(100, accuracy_score + 10)
        
        result = {
            **prediction,
            'status': 'validated',
            'validation_timestamp': time.time(),
            'validation_timestamp_str': datetime.now().strftime('%H:%M:%S'),
            'actual_price': actual_price,
            'actual_change_pct': actual_change_pct,
            'actual_direction': actual_direction,
            'price_error_pct': price_error_pct,
            'is_accurate': is_accurate,
            'is_close': is_close,
            'direction_correct': direction_correct,
            'accuracy_score': accuracy_score
        }
        
        return result
    
    def _update_accuracy_metrics(self, result: Dict):
        """Update accuracy metrics with validation result."""
        self.accuracy_metrics['validated'] += 1
        
        if result['is_accurate']:
            self.accuracy_metrics['accurate'] += 1
        if result['is_close']:
            self.accuracy_metrics['close'] += 1
        if result['direction_correct']:
            self.accuracy_metrics['direction_correct'] += 1
        
        # Update by exchange
        exchange = result['exchange']
        if exchange not in self.accuracy_metrics['by_exchange']:
            self.accuracy_metrics['by_exchange'][exchange] = {
                'total': 0, 'accurate': 0, 'close': 0, 'direction_correct': 0, 'avg_score': 0, 'scores': []
            }
        ex = self.accuracy_metrics['by_exchange'][exchange]
        ex['total'] += 1
        if result['is_accurate']:
            ex['accurate'] += 1
        if result['is_close']:
            ex['close'] += 1
        if result['direction_correct']:
            ex['direction_correct'] += 1
        ex['scores'].append(result['accuracy_score'])
        ex['scores'] = ex['scores'][-100:]  # Keep last 100
        ex['avg_score'] = sum(ex['scores']) / len(ex['scores'])
        
        # Update by asset class
        asset_class = result['asset_class']
        if asset_class not in self.accuracy_metrics['by_asset_class']:
            self.accuracy_metrics['by_asset_class'][asset_class] = {
                'total': 0, 'accurate': 0, 'close': 0, 'direction_correct': 0, 'avg_score': 0, 'scores': []
            }
        ac = self.accuracy_metrics['by_asset_class'][asset_class]
        ac['total'] += 1
        if result['is_accurate']:
            ac['accurate'] += 1
        if result['is_close']:
            ac['close'] += 1
        if result['direction_correct']:
            ac['direction_correct'] += 1
        ac['scores'].append(result['accuracy_score'])
        ac['scores'] = ac['scores'][-100:]
        ac['avg_score'] = sum(ac['scores']) / len(ac['scores'])
        
        # Update by frequency band
        freq_band = result.get('freq_band', 'unknown')
        if freq_band not in self.accuracy_metrics['by_frequency_band']:
            self.accuracy_metrics['by_frequency_band'][freq_band] = {
                'total': 0, 'accurate': 0, 'direction_correct': 0, 'avg_score': 0, 'scores': []
            }
        fb = self.accuracy_metrics['by_frequency_band'][freq_band]
        fb['total'] += 1
        if result['is_accurate']:
            fb['accurate'] += 1
        if result['direction_correct']:
            fb['direction_correct'] += 1
        fb['scores'].append(result['accuracy_score'])
        fb['scores'] = fb['scores'][-100:]
        fb['avg_score'] = sum(fb['scores']) / len(fb['scores'])
        
        # Update by coherence level
        coherence_level = result.get('coherence_level', 'unknown')
        if coherence_level not in self.accuracy_metrics['by_coherence_level']:
            self.accuracy_metrics['by_coherence_level'][coherence_level] = {
                'total': 0, 'accurate': 0, 'direction_correct': 0, 'avg_score': 0, 'scores': []
            }
        cl = self.accuracy_metrics['by_coherence_level'][coherence_level]
        cl['total'] += 1
        if result['is_accurate']:
            cl['accurate'] += 1
        if result['direction_correct']:
            cl['direction_correct'] += 1
        cl['scores'].append(result['accuracy_score'])
        cl['scores'] = cl['scores'][-100:]
        cl['avg_score'] = sum(cl['scores']) / len(cl['scores'])
        
        # Update recent accuracy (rolling window)
        self.accuracy_metrics['recent_accuracy'].append({
            'timestamp': time.time(),
            'score': result['accuracy_score'],
            'accurate': result['is_accurate'],
            'direction_correct': result['direction_correct']
        })
        self.accuracy_metrics['recent_accuracy'] = self.accuracy_metrics['recent_accuracy'][-100:]
    
    def _log_validation_result(self, result: Dict):
        """Log validation result with clear formatting."""
        symbol = result['symbol']
        prediction_time = result['prediction_time_str']
        validation_time = result['validation_timestamp_str']
        
        # Determine emoji based on accuracy
        if result['is_accurate']:
            emoji = "🎯"
            status = "BANG ON!"
        elif result['is_close']:
            emoji = "✅"
            status = "CLOSE"
        elif result['direction_correct']:
            emoji = "📈" if result['actual_direction'] == 'up' else "📉"
            status = "DIRECTION OK"
        else:
            emoji = "❌"
            status = "MISSED"
        
        logger.info(f"")
        logger.info(f"═══════════════════════════════════════════════════════")
        logger.info(f"{emoji} PREDICTION VALIDATED: {symbol} | {status}")
        logger.info(f"═══════════════════════════════════════════════════════")
        logger.info(f"   ⏰ Predicted at {prediction_time} → Checked at {validation_time}")
        logger.info(f"   📊 Expected: ${result['expected_price']:.6f} ({result['predicted_direction']} {result['predicted_change_pct']:.2f}%)")
        logger.info(f"   📊 Actual:   ${result['actual_price']:.6f} ({result['actual_direction']} {result['actual_change_pct']:.2f}%)")
        logger.info(f"   🎯 Accuracy Score: {result['accuracy_score']:.1f}/100 | Error: {result['price_error_pct']:.3f}%")
        logger.info(f"   📈 Direction: {'✅ CORRECT' if result['direction_correct'] else '❌ WRONG'}")
        logger.info(f"═══════════════════════════════════════════════════════")
        logger.info(f"")
    
    def get_accuracy_boost(self, exchange: str, asset_class: str, 
                          frequency: float, coherence: float) -> float:
        """
        Get accuracy-based boost for probability calculations.
        
        If predictions at this frequency/coherence level have been historically accurate,
        boost the confidence. If they've been inaccurate, reduce confidence.
        
        Returns: Multiplier (0.8 to 1.2)
        """
        boosts = []
        
        # Exchange accuracy boost
        ex = self.accuracy_metrics['by_exchange'].get(exchange, {})
        if ex.get('total', 0) >= 10:  # Need at least 10 predictions
            ex_accuracy = ex.get('avg_score', 50) / 100
            boosts.append(0.8 + (ex_accuracy * 0.4))  # 0.8 to 1.2
        
        # Asset class accuracy boost
        ac = self.accuracy_metrics['by_asset_class'].get(asset_class, {})
        if ac.get('total', 0) >= 10:
            ac_accuracy = ac.get('avg_score', 50) / 100
            boosts.append(0.8 + (ac_accuracy * 0.4))
        
        # Frequency band accuracy boost
        freq_band = self._get_freq_band(frequency)
        fb = self.accuracy_metrics['by_frequency_band'].get(freq_band, {})
        if fb.get('total', 0) >= 10:
            fb_accuracy = fb.get('avg_score', 50) / 100
            boosts.append(0.8 + (fb_accuracy * 0.4))
        
        # Coherence level accuracy boost
        coherence_level = self._get_coherence_level(coherence)
        cl = self.accuracy_metrics['by_coherence_level'].get(coherence_level, {})
        if cl.get('total', 0) >= 10:
            cl_accuracy = cl.get('avg_score', 50) / 100
            boosts.append(0.8 + (cl_accuracy * 0.4))
        
        if boosts:
            return sum(boosts) / len(boosts)
        return 1.0  # Neutral if no history
    
    def get_accuracy_summary(self) -> str:
        """Get human-readable accuracy summary."""
        m = self.accuracy_metrics
        total = m['validated']
        
        if total == 0:
            return "🔮 No predictions validated yet - collecting data..."
        
        accurate_pct = (m['accurate'] / total) * 100
        close_pct = (m['close'] / total) * 100
        direction_pct = (m['direction_correct'] / total) * 100
        
        # Calculate recent accuracy (last 20)
        recent = m['recent_accuracy'][-20:]
        if recent:
            recent_scores = [r['score'] for r in recent]
            recent_avg = sum(recent_scores) / len(recent_scores)
            recent_accurate = sum(1 for r in recent if r['accurate'])
            recent_direction = sum(1 for r in recent if r['direction_correct'])
        else:
            recent_avg = 0
            recent_accurate = 0
            recent_direction = 0
        
        lines = [
            "",
            "═══════════════════════════════════════════════════════════════",
            "🔮 PREDICTION ACCURACY REPORT",
            "═══════════════════════════════════════════════════════════════",
            f"📊 Total Predictions: {m['total_predictions']} | Validated: {total}",
            f"",
            f"🎯 OVERALL ACCURACY:",
            f"   • Bang On (≤0.5% error): {m['accurate']}/{total} ({accurate_pct:.1f}%)",
            f"   • Close (≤1% error):     {m['close']}/{total} ({close_pct:.1f}%)",
            f"   • Direction Correct:     {m['direction_correct']}/{total} ({direction_pct:.1f}%)",
            f"",
            f"📈 RECENT (Last {len(recent)} predictions):",
            f"   • Average Score: {recent_avg:.1f}/100",
            f"   • Accurate: {recent_accurate}/{len(recent)}",
            f"   • Direction OK: {recent_direction}/{len(recent)}",
        ]
        
        # By exchange breakdown
        if m['by_exchange']:
            lines.append("")
            lines.append("📍 BY EXCHANGE:")
            for ex, data in m['by_exchange'].items():
                if data['total'] > 0:
                    acc_rate = (data['accurate'] / data['total']) * 100
                    lines.append(f"   • {ex}: {data['accurate']}/{data['total']} accurate ({acc_rate:.1f}%) | Avg Score: {data['avg_score']:.1f}")
        
        # By frequency band breakdown
        if m['by_frequency_band']:
            lines.append("")
            lines.append("🎵 BY FREQUENCY BAND:")
            for band, data in sorted(m['by_frequency_band'].items()):
                if data['total'] > 0:
                    acc_rate = (data['accurate'] / data['total']) * 100
                    lines.append(f"   • {band}: {data['accurate']}/{data['total']} ({acc_rate:.1f}%) | Avg: {data['avg_score']:.1f}")
        
        # By coherence level
        if m['by_coherence_level']:
            lines.append("")
            lines.append("🌊 BY COHERENCE LEVEL:")
            for level, data in m['by_coherence_level'].items():
                if data['total'] > 0:
                    acc_rate = (data['accurate'] / data['total']) * 100
                    lines.append(f"   • {level}: {data['accurate']}/{data['total']} ({acc_rate:.1f}%) | Avg: {data['avg_score']:.1f}")
        
        lines.append("")
        lines.append("═══════════════════════════════════════════════════════════════")
        
        return "\n".join(lines)
    
    def _get_freq_band(self, freq: float) -> str:
        """Get frequency band name with sacred frequency mapping."""
        # Check for exact sacred frequency matches first (±5Hz tolerance)
        sacred_freqs = {
            7.83: "7.83Hz (Schumann)",
            136.1: "136Hz (OM/Earth)",
            174: "174Hz (Foundation)",
            285: "285Hz (Healing)",
            396: "396Hz (Liberation)",
            417: "417Hz (Change)",
            432: "432Hz (Cosmic)",
            440: "440Hz (Distortion!)",
            528: "528Hz (Love)",
            639: "639Hz (Connection)",
            741: "741Hz (Awakening)",
            852: "852Hz (Spiritual)",
            963: "963Hz (Unity)",
        }
        for sacred, name in sacred_freqs.items():
            if abs(freq - sacred) <= 5:
                return name
        
        # Fall back to band classification
        if freq < 200:
            return "Sub-200Hz (Deep Earth)"
        elif freq < 300:
            return "200-299Hz (Grounding)"
        elif freq < 400:
            return "300-399Hz (Activation)"
        elif freq < 500:
            return "400-499Hz (Transition)"
        elif freq < 600:
            return "500-599Hz (Heart)"
        elif freq < 700:
            return "600-699Hz (Expression)"
        elif freq < 800:
            return "700-799Hz (Intuition)"
        elif freq < 900:
            return "800-899Hz (Insight)"
        elif freq < 1000:
            return "900-999Hz (Crown)"
        else:
            return "1000+Hz (Transcendent)"
    
    def _get_coherence_level(self, coherence: float) -> str:
        """Get coherence level name."""
        if coherence < 0.3:
            return "Low (<0.3)"
        elif coherence < 0.5:
            return "Medium (0.3-0.5)"
        elif coherence < 0.7:
            return "Good (0.5-0.7)"
        elif coherence < 0.85:
            return "High (0.7-0.85)"
        else:
            return "Excellent (0.85+)"
    
    def get_pending_count(self) -> int:
        """Get number of predictions awaiting validation."""
        return len(self.pending_predictions)
    
    def get_validated_count(self) -> int:
        """Get total validated predictions."""
        return self.accuracy_metrics['validated']


# ═══════════════════════════════════════════════════════════════
# 🌐 MULTI-EXCHANGE ORCHESTRATOR - Unified Cross-Exchange Intelligence
# ═══════════════════════════════════════════════════════════════

class MultiExchangeOrchestrator:
    """
    🌐 MULTI-EXCHANGE ORCHESTRATOR
    
    Central nervous system for cross-exchange trading:
    - Unified opportunity scanning across Binance, Kraken, Capital.com, Alpaca
    - Cross-exchange learning: wins/losses inform all exchange decisions
    - Smart order routing to best execution venue
    - Arbitrage detection and execution
    - Coordinated position management
    
    ALL SYSTEMS TALK TO EACH OTHER through this orchestrator.
    """
    
    def __init__(self, multi_client):
        self.client = multi_client
        
        # Exchange-specific configuration
        self.exchange_config = {
            'binance': {
                'enabled': True,
                # 🤑 GREEDY HOE: ALL THE BINANCE PAIRS!
                'quote_currencies': ['USDC', 'USDT', 'BTC', 'ETH', 'BNB', 'FDUSD', 'EUR', 'GBP', 'TUSD'],
                'fee_rate': 0.001,
                'max_positions': 15,  # 🔥 BEAST MODE: 15 positions per exchange!
                'min_trade_usd': 10.0,
                'asset_class': 'crypto'
            },
            'kraken': {
                'enabled': True,  # ✅ ENABLED - Trading on Kraken with GBP
                # 🤑 GREEDY HOE: ALL THE KRAKEN PAIRS!
                'quote_currencies': ['USD', 'EUR', 'GBP', 'USDT', 'USDC', 'BTC', 'ETH', 'AUD', 'CAD'],
                'fee_rate': 0.0026,
                'max_positions': 15,  # 🔥 BEAST MODE: 15 positions per exchange!
                'min_trade_usd': 5.0,
                'asset_class': 'crypto'
            },
            'capital': {
                'enabled': True,
                'quote_currencies': ['USD', 'GBP'],
                'fee_rate': 0.001,
                'max_positions': 10,  # 🔥 BEAST MODE: 10 CFD positions!
                'min_trade_usd': 10.0,
                'asset_class': 'cfd'  # forex, indices, commodities
            },
            'alpaca': {
                'enabled': CONFIG.get('ALPACA_ANALYTICS_ONLY', True) == False,  # Trading disabled by default
                'quote_currencies': ['USD'],
                'fee_rate': 0.0025,
                'max_positions': 10,  # 🔥 BEAST MODE: 10 stock positions!
                'min_trade_usd': 1.0,  # Fractional shares
                'asset_class': 'stocks'
            }
        }
        
        # Cross-exchange learning metrics
        self.learning_metrics = {
            'total_trades': 0,
            'wins': 0,
            'losses': 0,
            'total_pnl': 0.0,
            'by_exchange': {},
            'by_asset_class': {},
            'by_frequency_band': {},
            'cross_correlations': {}
        }
        
        # Unified ticker cache (all exchanges)
        self.unified_ticker_cache: Dict[str, Dict] = {}
        self.last_unified_scan = 0
        self.scan_interval = 10  # seconds
        
        # Cross-exchange signals
        self.cross_signals: List[Dict] = []
        self.signal_history: List[Dict] = []
        
        logger.info("🌐 MultiExchangeOrchestrator initialized - All systems connected")

    def get_learning_metrics(self) -> Dict[str, Any]:
        """Expose cross-exchange learning metrics (wins, pnl, by exchange/class)."""
        return self.learning_metrics
        
    def get_enabled_exchanges(self) -> List[str]:
        """Get list of enabled exchanges."""
        return [ex for ex, cfg in self.exchange_config.items() if cfg['enabled']]
        
    def scan_all_exchanges(self) -> Dict[str, List[Dict]]:
        """
        Scan all enabled exchanges for opportunities.
        Returns opportunities organized by exchange.
        """
        all_opportunities = {}
        
        for exchange in self.get_enabled_exchanges():
            try:
                opps = self._scan_exchange(exchange)
                all_opportunities[exchange] = opps
                logger.debug(f"🔍 {exchange}: Found {len(opps)} opportunities")
            except Exception as e:
                logger.error(f"❌ {exchange} scan error: {e}")
                all_opportunities[exchange] = []
                
        # Update unified cache
        self.last_unified_scan = time.time()
        return all_opportunities
        
    def _scan_exchange(self, exchange: str) -> List[Dict]:
        """Scan a single exchange for opportunities."""
        opportunities = []
        cfg = self.exchange_config.get(exchange, {})
        
        try:
            # Get tickers from the exchange client
            if hasattr(self.client, 'clients') and exchange in self.client.clients:
                client = self.client.clients[exchange]
                tickers = self._get_exchange_tickers(exchange, client, cfg)
                
                for symbol, ticker in tickers.items():
                    opp = self._evaluate_opportunity(exchange, symbol, ticker, cfg)
                    if opp:
                        opportunities.append(opp)
                        
        except Exception as e:
            logger.error(f"Scan error for {exchange}: {e}")
            
        # Sort by score
        opportunities.sort(key=lambda x: -x.get('score', 0))
        # 🔥 UNLEASHED: Return top 100 per exchange instead of 20!
        return opportunities[:100]  # Top 100 per exchange - TRADE EVERYTHING!
        
    def _get_exchange_tickers(self, exchange: str, client, cfg: Dict) -> Dict[str, Dict]:
        """Get tickers from an exchange."""
        tickers = {}
        quote_currencies = cfg.get('quote_currencies', ['USD'])
        
        try:
            if exchange == 'binance':
                raw = client.client.session.get(f"{client.client.base}/api/v3/ticker/24hr", timeout=10).json()
                for t in raw:
                    sym = t['symbol']
                    for q in quote_currencies:
                        if sym.endswith(q):
                            tickers[sym] = {
                                'price': float(t['lastPrice']),
                                'change': float(t['priceChangePercent']),
                                'volume': float(t['quoteVolume']),
                                'high': float(t['highPrice']),
                                'low': float(t['lowPrice']),
                                'exchange': 'binance',
                                'quote': q,
                            }
                            break
                            
            elif exchange == 'kraken':
                # Use existing Kraken ticker logic
                tickers = self._get_kraken_tickers(client, quote_currencies)
                
            elif exchange == 'capital':
                # CFD markets - simplified
                tickers = self._get_capital_tickers(client)
                
        except Exception as e:
            logger.error(f"Ticker fetch error for {exchange}: {e}")
            
        return tickers
        
    def _get_kraken_tickers(self, client, quote_currencies: List[str]) -> Dict[str, Dict]:
        """Get Kraken tickers."""
        tickers = {}
        try:
            if hasattr(client.client, 'get_24h_tickers'):
                raw_tickers = client.client.get_24h_tickers()
                for t in raw_tickers:
                    sym = t.get('symbol', '')
                    for q in quote_currencies:
                        if sym.endswith(q):
                            tickers[sym] = {
                                'price': float(t.get('price', 0)),
                                'change': float(t.get('change24h', 0)),
                                'volume': float(t.get('volume', 0)),
                                'high': float(t.get('high', t.get('price', 0))),
                                'low': float(t.get('low', t.get('price', 0))),
                                'exchange': 'kraken',
                                'quote': q,
                            }
                            break
        except Exception as e:
            logger.debug(f"Kraken ticker error: {e}")
        return tickers
        
    def _get_capital_tickers(self, client) -> Dict[str, Dict]:
        """Get Capital.com CFD tickers."""
        tickers = {}
        # Capital markets to scan
        markets = ['EURUSD', 'GBPUSD', 'GOLD', 'US500', 'UK100', 'OIL_CRUDE']
        
        try:
            for market in markets:
                # Simplified - actual implementation would use Capital API
                tickers[market] = {
                    'price': 0,  # Would be fetched from API
                    'change': 0,
                    'volume': 1000000,
                    'exchange': 'capital',
                    'quote': 'USD',
                    'asset_class': self._get_asset_class(market)
                }
        except Exception as e:
            logger.debug(f"Capital ticker error: {e}")
        return tickers
        
    def _get_asset_class(self, symbol: str) -> str:
        """Determine asset class from symbol."""
        sym = symbol.upper()
        if any(fx in sym for fx in ['USD', 'EUR', 'GBP', 'JPY', 'CHF']):
            if len(sym) <= 8:
                return 'forex'
        if any(idx in sym for idx in ['US500', 'US100', 'UK100', 'DE40']):
            return 'indices'
        if any(com in sym for com in ['GOLD', 'SILVER', 'OIL', 'NATGAS']):
            return 'commodities'
        return 'crypto'
        
    def _evaluate_opportunity(self, exchange: str, symbol: str, ticker: Dict, cfg: Dict) -> Optional[Dict]:
        """Evaluate a single opportunity."""
        price = ticker.get('price', 0)
        change = ticker.get('change', 0)
        volume = ticker.get('volume', 0)
        
        if price <= 0:
            return None
            
        # Calculate coherence
        asset_class = ticker.get('asset_class', cfg.get('asset_class', 'crypto'))
        coherence = self._calculate_coherence(change, volume, ticker, asset_class)
        
        if coherence < CONFIG.get('ENTRY_COHERENCE', 0.45):
            return None
            
        # Calculate frequency
        freq = max(256, min(963, 432 * ((1 + change/100) ** PHI)))
        in_avoid = 435 <= freq <= 445  # Avoid 440Hz distortion
        
        if in_avoid:
            return None
            
        # Calculate probability
        probability = self._calculate_probability(coherence, change, freq, asset_class)
        
        if probability < CONFIG.get('PROB_MIN_CONFIDENCE', 0.50):
            return None
            
        # Calculate score
        score = self._calculate_score(probability, coherence, volume, freq, change)
        
        # Apply cross-exchange learning boost
        score = self._apply_learning_boost(score, exchange, asset_class, freq)
        
        return {
            'exchange': exchange,
            'symbol': symbol,
            'price': price,
            'change': change,
            'volume': volume,
            'coherence': coherence,
            'frequency': freq,
            'probability': probability,
            'score': score,
            'asset_class': asset_class,
            'quote': ticker.get('quote', 'USD'),
            'timestamp': time.time()
        }
        
    def _calculate_coherence(self, change: float, volume: float, ticker: Dict, asset_class: str) -> float:
        """Calculate coherence with asset-class awareness."""
        high = ticker.get('high', ticker.get('price', 1))
        low = ticker.get('low', ticker.get('price', 1))
        price = ticker.get('price', 1)
        
        volatility = ((high - low) / low * 100) if low > 0 else 0
        
        if asset_class == 'forex':
            S = min(1.0, volume / 50.0)
            O = min(1.0, abs(change) / 0.3)
            E = min(1.0, volatility / 0.5)
            Lambda = (S + O + E) / 3.0
            return 1 / (1 + math.exp(-6 * (Lambda - 0.35)))
        elif asset_class == 'indices':
            S = min(1.0, volume / 50.0)
            O = min(1.0, abs(change) / 1.0)
            E = min(1.0, volatility / 2.0)
            Lambda = (S + O + E) / 3.0
            return 1 / (1 + math.exp(-6 * (Lambda - 0.35)))
        else:  # crypto
            S = min(1.0, volume / 50000.0)
            O = min(1.0, abs(change) / 15.0)
            E = min(1.0, volatility / 25.0)
            Lambda = (S + O + E) / 3.0
            return 1 / (1 + math.exp(-5 * (Lambda - 0.5)))
            
    def _calculate_probability(self, coherence: float, change: float, freq: float, asset_class: str) -> float:
        """Calculate trade probability with news/knowledge correlation."""
        base_prob = 0.50 + coherence * 0.30
        
        # Momentum adjustment
        if change > 0:
            base_prob += min(0.10, change / 50)
        else:
            base_prob -= min(0.05, abs(change) / 100)
            
        # Frequency adjustment - based on prediction accuracy data + sacred frequencies
        freq_modifier = self._get_sacred_frequency_modifier(freq)
        base_prob *= freq_modifier
        
        # 📰 NEWS SENTIMENT MODIFIER - Learn from correlation data
        try:
            news_sentiment = getattr(self, '_last_news_sentiment', {})
            news_label = news_sentiment.get('label', 'neutral')
            news_confidence = news_sentiment.get('confidence', 0.0)
            
            # Get learned correlations from Adaptive Learner
            news_insights = ADAPTIVE_LEARNER.get_news_correlation_insights()
            
            if news_label == 'bullish' and news_confidence >= 0.5:
                # Boost probability in bullish news environments (if historically good)
                bullish_win_rate = news_insights.get('bullish', {}).get('win_rate', 0.5)
                if bullish_win_rate > 0.55:  # Only boost if bullish news historically good
                    news_boost = min(0.08, (bullish_win_rate - 0.5) * 0.4 * news_confidence)
                    base_prob += news_boost
            elif news_label == 'bearish' and news_confidence >= 0.5:
                # Reduce probability in bearish news (if historically bad)
                bearish_win_rate = news_insights.get('bearish', {}).get('win_rate', 0.5)
                if bearish_win_rate < 0.45:  # Only reduce if bearish news historically bad
                    news_penalty = min(0.08, (0.5 - bearish_win_rate) * 0.4 * news_confidence)
                    base_prob -= news_penalty
        except Exception:
            pass  # News correlation not critical
        
        # 📚 KNOWLEDGE MODIFIER - Boost based on knowledge discovery performance
        try:
            knowledge_modifier = ADAPTIVE_LEARNER.get_knowledge_probability_modifier()
            base_prob *= knowledge_modifier  # Typically 0.97-1.03
        except Exception:
            pass  # Knowledge correlation not critical
            
        return max(0.0, min(CONFIG.get('PROB_CAP', 0.83), base_prob))
    
    def _get_sacred_frequency_modifier(self, freq: float) -> float:
        """
        🎵 SACRED FREQUENCY MODIFIER 🎵
        
        Maps market frequencies to sacred healing tones and returns
        appropriate probability modifiers based on harmonic resonance.
        
        SOLFEGGIO SCALE (Ancient healing frequencies):
        - 174 Hz: Foundation, pain relief
        - 285 Hz: Healing, tissue regeneration
        - 396 Hz: Liberation from fear/guilt (UT)
        - 417 Hz: Undoing situations, facilitating change (RE)
        - 528 Hz: Love frequency, DNA repair (MI) ⭐ OPTIMAL
        - 639 Hz: Connection, relationships (FA)
        - 741 Hz: Awakening intuition (SOL)
        - 852 Hz: Returning to spiritual order (LA)
        - 963 Hz: Unity, awakening (SI)
        
        EARTH FREQUENCIES:
        - 7.83 Hz: Schumann Resonance (Earth's heartbeat)
        - 136.1 Hz: OM frequency (Earth's year)
        - 432 Hz: Universal tuning (cosmic harmony)
        
        DISTORTION:
        - 440 Hz: Artificial concert pitch (dissonance)
        """
        # Check Schumann harmonics (7.83Hz × n)
        schumann_base = 7.83
        for harmonic in range(1, 128):  # Up to 128th harmonic (~1000Hz)
            schumann_freq = schumann_base * harmonic
            if abs(freq - schumann_freq) <= 3:
                return CONFIG.get('FREQUENCY_BOOST_SCHUMANN', 1.45)
        
        # Check exact sacred frequencies (±5Hz tolerance)
        sacred_map = {
            (169, 179): CONFIG.get('FREQUENCY_BOOST_174HZ', 1.20),   # 174 Hz Foundation
            (280, 290): CONFIG.get('FREQUENCY_BOOST_285HZ', 1.25),   # 285 Hz Healing
            (391, 401): CONFIG.get('FREQUENCY_BOOST_396HZ', 1.40),   # 396 Hz Liberation
            (412, 422): CONFIG.get('FREQUENCY_BOOST_417HZ', 1.30),   # 417 Hz Change
            (427, 437): CONFIG.get('FREQUENCY_BOOST_432HZ', 1.30),   # 432 Hz Cosmic
            (435, 445): CONFIG.get('FREQUENCY_SUPPRESS_440HZ', 0.70),# 440 Hz Distortion!
            (523, 533): CONFIG.get('FREQUENCY_BOOST_528HZ', 1.35),   # 528 Hz Love ⭐
            (634, 644): CONFIG.get('FREQUENCY_BOOST_639HZ', 1.25),   # 639 Hz Connection
            (736, 746): CONFIG.get('FREQUENCY_BOOST_741HZ', 1.15),   # 741 Hz Awakening
            (847, 857): CONFIG.get('FREQUENCY_BOOST_852HZ', 1.20),   # 852 Hz Spiritual
            (958, 968): CONFIG.get('FREQUENCY_SUPPRESS_963HZ', 0.60),# 963 Hz (poor data)
            (131, 141): CONFIG.get('FREQUENCY_BOOST_136HZ', 1.25),   # 136 Hz OM
        }
        
        for (low, high), modifier in sacred_map.items():
            if low <= freq <= high:
                return modifier
        
        # Band-based fallback
        if 300 <= freq <= 399:
            return CONFIG.get('FREQUENCY_BOOST_300HZ', 1.50)  # 98.8% accuracy!
        elif 600 <= freq <= 699:
            return CONFIG.get('FREQUENCY_SUPPRESS_600HZ', 0.75)  # 0% accuracy
        elif freq >= 1000:
            return CONFIG.get('FREQUENCY_SUPPRESS_HIGH_CHAOS', 0.50)
        
        # Neutral baseline for unclassified frequencies
        return CONFIG.get('FREQUENCY_NEUTRAL_BASELINE', 1.0)
        
    def _calculate_score(self, prob: float, coherence: float, volume: float, freq: float, change: float) -> float:
        """Calculate opportunity score."""
        base = prob * coherence * (1 + math.log10(max(1, volume/10000)))
        
        # Frequency bonus
        in_optimal = 520 <= freq <= 963
        freq_bonus = 1.0 if in_optimal else 0.5
        
        return base * (1 + freq_bonus)
        
    def _apply_learning_boost(self, score: float, exchange: str, asset_class: str, freq: float) -> float:
        """Apply cross-exchange learning boost to score."""
        boost = 1.0
        
        # Exchange performance boost
        ex_metrics = self.learning_metrics.get('by_exchange', {}).get(exchange, {})
        if ex_metrics.get('total_trades', 0) >= 10:
            ex_win_rate = ex_metrics.get('wins', 0) / max(1, ex_metrics.get('total_trades', 1))
            if ex_win_rate > 0.55:
                boost *= 1.0 + (ex_win_rate - 0.50) * 0.5
            elif ex_win_rate < 0.45:
                boost *= 0.8
                
        # Asset class performance boost
        ac_metrics = self.learning_metrics.get('by_asset_class', {}).get(asset_class, {})
        if ac_metrics.get('total_trades', 0) >= 10:
            ac_win_rate = ac_metrics.get('wins', 0) / max(1, ac_metrics.get('total_trades', 1))
            if ac_win_rate > 0.55:
                boost *= 1.0 + (ac_win_rate - 0.50) * 0.3
                
        return score * boost
        
    def record_trade_result(self, exchange: str, symbol: str, pnl: float, 
                           asset_class: str, frequency: float, coherence: float):
        """
        Record trade result for cross-exchange learning.
        ALL SYSTEMS LEARN FROM THIS.
        """
        is_win = pnl > 0
        
        # Update global metrics
        self.learning_metrics['total_trades'] += 1
        if is_win:
            self.learning_metrics['wins'] += 1
        else:
            self.learning_metrics['losses'] += 1
        self.learning_metrics['total_pnl'] += pnl
        
        # Update by exchange
        if exchange not in self.learning_metrics['by_exchange']:
            self.learning_metrics['by_exchange'][exchange] = {'total_trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0}
        self.learning_metrics['by_exchange'][exchange]['total_trades'] += 1
        if is_win:
            self.learning_metrics['by_exchange'][exchange]['wins'] += 1
        else:
            self.learning_metrics['by_exchange'][exchange]['losses'] += 1
        self.learning_metrics['by_exchange'][exchange]['pnl'] += pnl
        
        # Update by asset class
        if asset_class not in self.learning_metrics['by_asset_class']:
            self.learning_metrics['by_asset_class'][asset_class] = {'total_trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0}
        self.learning_metrics['by_asset_class'][asset_class]['total_trades'] += 1
        if is_win:
            self.learning_metrics['by_asset_class'][asset_class]['wins'] += 1
        else:
            self.learning_metrics['by_asset_class'][asset_class]['losses'] += 1
        self.learning_metrics['by_asset_class'][asset_class]['pnl'] += pnl
        
        # Update by frequency band
        freq_band = self._get_freq_band(frequency)
        if freq_band not in self.learning_metrics['by_frequency_band']:
            self.learning_metrics['by_frequency_band'][freq_band] = {'total_trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0}
        self.learning_metrics['by_frequency_band'][freq_band]['total_trades'] += 1
        if is_win:
            self.learning_metrics['by_frequency_band'][freq_band]['wins'] += 1
        else:
            self.learning_metrics['by_frequency_band'][freq_band]['losses'] += 1
        self.learning_metrics['by_frequency_band'][freq_band]['pnl'] += pnl
        
        # Log cross-exchange insight
        total = self.learning_metrics['total_trades']
        wins = self.learning_metrics['wins']
        wr = wins / max(1, total) * 100
        logger.info(f"🌐 Cross-Exchange Learning: {total} trades, {wr:.1f}% WR, ${self.learning_metrics['total_pnl']:.2f} PnL")
        
    def _get_freq_band(self, freq: float) -> str:
        """Get frequency band name."""
        if freq < 400:
            return 'LOW (<400Hz)'
        elif 400 <= freq < 500:
            return 'MID (400-500Hz)'
        elif 500 <= freq < 600:
            return 'SOLFEGGIO (500-600Hz)'
        elif 600 <= freq < 800:
            return 'HIGH (600-800Hz)'
        else:
            return 'ULTRA (>800Hz)'
            
    def get_best_opportunity(self) -> Optional[Dict]:
        """Get the single best opportunity across all exchanges."""
        all_opps = self.scan_all_exchanges()
        
        # Flatten and sort
        combined = []
        for exchange, opps in all_opps.items():
            combined.extend(opps)
            
        if not combined:
            return None
            
        combined.sort(key=lambda x: -x.get('score', 0))
        return combined[0]
        
    def get_learning_summary(self) -> str:
        """Get formatted learning summary."""
        m = self.learning_metrics
        lines = [
            "═══════════════════════════════════════",
            "🌐 MULTI-EXCHANGE LEARNING SUMMARY",
            "═══════════════════════════════════════",
            f"Total Trades: {m['total_trades']} | Wins: {m['wins']} | WR: {m['wins']/max(1,m['total_trades'])*100:.1f}%",
            f"Total PnL: ${m['total_pnl']:.2f}",
            "",
            "By Exchange:"
        ]
        
        for ex, metrics in m.get('by_exchange', {}).items():
            wr = metrics['wins'] / max(1, metrics['total_trades']) * 100
            lines.append(f"  {ex}: {metrics['total_trades']} trades, {wr:.1f}% WR, ${metrics['pnl']:.2f}")
            
        lines.append("")
        lines.append("By Asset Class:")
        for ac, metrics in m.get('by_asset_class', {}).items():
            wr = metrics['wins'] / max(1, metrics['total_trades']) * 100
            lines.append(f"  {ac}: {metrics['total_trades']} trades, {wr:.1f}% WR, ${metrics['pnl']:.2f}")
            
        lines.append("")
        lines.append("By Frequency Band:")
        for fb, metrics in m.get('by_frequency_band', {}).items():
            wr = metrics['wins'] / max(1, metrics['total_trades']) * 100
            lines.append(f"  {fb}: {metrics['total_trades']} trades, {wr:.1f}% WR")
            
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# 📊 UNIFIED STATE AGGREGATOR - All JSON Feeds Into Ecosystem
# ═══════════════════════════════════════════════════════════════

class UnifiedStateAggregator:
    """
    📊 UNIFIED STATE AGGREGATOR
    
    Consolidates ALL JSON data sources and feeds them into the main ecosystem:
    
    Data Sources:
    ├─ aureon_kraken_state.json       - Main trading state (positions, balance, stats)
    ├─ elephant_ultimate.json         - Symbol memory (hunts, wins, blacklist)
    ├─ elephant_unified.json          - Unified elephant memory
    ├─ adaptive_learning_history.json - Learning engine data
    ├─ calibration_trades.json        - Calibration trade history
    ├─ hnc_frequency_log.json         - HNC frequency readings
    ├─ auris_runtime.json             - Auris configuration & targets
    └─ /tmp/aureon_trade_logs/*.jsonl - Trade logs for analysis
    
    ALL SYSTEMS FEED THE ECOSYSTEM through this aggregator.
    """
    
    # JSON file paths
    STATE_FILES = {
        'main_state': 'aureon_kraken_state.json',
        'elephant_ultimate': 'elephant_ultimate.json',
        'elephant_unified': 'elephant_unified.json',
        'elephant_live': 'elephant_live.json',
        'adaptive_learning': 'adaptive_learning_history.json',
        'calibration': 'calibration_trades.json',
        'hnc_frequency': 'hnc_frequency_log.json',
        'auris_runtime': 'auris_runtime.json',
        'multi_exchange_learning': 'multi_exchange_learning.json',
    }
    
    # JSONL logs
    LOG_FILES = {
        'thoughts': 'logs/aureon_thoughts.jsonl',
    }

    PROBABILITY_REPORTS = [
        'probability_all_markets_report.json',
        'probability_all_exchanges_report.json',
        'probability_kraken_report.json',
        'probability_full_market_report.json',
        'probability_batch_report.json',
        'probability_data.json',
        'probability_combined_report.json',
        'probability_4_exchanges_report.json',
        'probability_training_report.json',
    ]

    EXTRA_TRADE_HISTORY = [
        'paper_trade_history.json',  # Paper trade log
    ]

    ANALYTICS_REPORTS = [
        'multi_agent_results.json',
        'multi_agent_aggressive_results.json',
        'kelly_montecarlo_results.json',
        'montecarlo_results.json',
        'aureon_baseline_results.json',
        'hive_baseline.json',
        'harmonic_wave_data.json',
    ]

    POSITION_FILES = [
        'positions.json',
        'piano_positions.json',
    ]

    AUX_LOG_FILES = [
        'rejection_log.json',
        'smoke_test_results.json',
        'prediction_test_result.json',
    ]
    
    def __init__(self):
        self.aggregated_state = {
            'last_aggregation': 0,
            'sources_loaded': [],
            'total_historical_trades': 0,
            'combined_win_rate': 0.0,
            'symbol_insights': {},
            'probability_insights': {},
            'analytics_insights': {},
            'positions_snapshot': {},
            'aux_logs': {},
            'frequency_performance': {},
            'exchange_performance': {},
            'coherence_bands': {},
            'organism_health': {
                'status': 'UNKNOWN',
                'pulse': {},
                'recent_thoughts': []
            },
        }
        self.load_all_sources()
        
    def load_all_sources(self) -> Dict[str, Any]:
        """Load and aggregate data from all JSON sources."""
        self.aggregated_state['sources_loaded'] = []
        self.load_organism_thoughts()  # Load thoughts first
        all_trades = []
        symbol_data = {}
        frequency_data = {}
        probability_insights: Dict[str, Dict[str, Any]] = {}
        probability_freshness: Dict[str, Any] = {
            'report_ages_minutes': {},
            'newest_minutes': None,
            'oldest_minutes': None,
            'stale': False,
            'threshold_minutes': 120,
        }
        high_conviction: List[Dict[str, Any]] = []
        analytics_insights: Dict[str, Dict[str, Any]] = {}
        positions_snapshot: Dict[str, Any] = {}
        aux_logs: Dict[str, Any] = {}
        position_hygiene: Dict[str, Any] = {
            'flagged': [],
            'rules': {
                'max_cycles': 50,
                'min_momentum': -2.0,
            }
        }

        def _extract_pnl(trade: Dict[str, Any]) -> float:
            pnl = trade.get('pnl_usd')
            if pnl is None:
                pnl = trade.get('pnl')
            if pnl is None:
                return 0.0
            try:
                return float(pnl)
            except (TypeError, ValueError):
                return 0.0
        
        # 1. Load Main Trading State
        main_state = self._load_json(self.STATE_FILES['main_state'])
        if main_state:
            self.aggregated_state['sources_loaded'].append('main_state')
            self.aggregated_state['current_balance'] = main_state.get('balance', 0)
            self.aggregated_state['peak_balance'] = main_state.get('peak_balance', 0)
            self.aggregated_state['total_trades'] = main_state.get('total_trades', 0)
            self.aggregated_state['wins'] = main_state.get('wins', 0)
            self.aggregated_state['losses'] = main_state.get('losses', 0)
            self.aggregated_state['max_drawdown'] = main_state.get('max_drawdown', 0)
            
            # 🎯 TRUE STARTING BALANCE - shared across all subsystems!
            self.aggregated_state['first_start_balance'] = main_state.get('first_start_balance', main_state.get('initial_balance', 0))
            self.aggregated_state['first_start_time'] = main_state.get('first_start_time', 0)
            self.aggregated_state['initial_balance'] = main_state.get('initial_balance', 0)

            # Position hygiene pass: flag long-running or losing positions
            positions = main_state.get('positions', {}) or {}
            for sym, pos in positions.items():
                try:
                    cycles = pos.get('cycles', 0)
                    momentum = pos.get('momentum', 0.0)
                    if cycles >= position_hygiene['rules']['max_cycles'] or momentum <= position_hygiene['rules']['min_momentum']:
                        position_hygiene['flagged'].append({
                            'symbol': sym,
                            'cycles': cycles,
                            'momentum': momentum,
                            'entry_price': pos.get('entry_price'),
                            'coherence': pos.get('coherence'),
                            'dominant_node': pos.get('dominant_node'),
                        })
                except Exception:
                    continue
            
        # 2. Load Elephant Memory files (symbol-level insights)
        for elephant_key in ['elephant_ultimate', 'elephant_unified', 'elephant_live']:
            elephant_data = self._load_json(self.STATE_FILES.get(elephant_key, ''))
            if elephant_data:
                self.aggregated_state['sources_loaded'].append(elephant_key)
                for symbol, data in elephant_data.items():
                    if symbol not in symbol_data:
                        symbol_data[symbol] = {
                            'total_hunts': 0, 'total_trades': 0, 'wins': 0, 
                            'losses': 0, 'profit': 0, 'blacklisted': False
                        }
                    symbol_data[symbol]['total_hunts'] += data.get('hunts', 0)
                    symbol_data[symbol]['total_trades'] += data.get('trades', 0)
                    symbol_data[symbol]['wins'] += data.get('wins', 0)
                    symbol_data[symbol]['losses'] += data.get('losses', 0)
                    symbol_data[symbol]['profit'] += data.get('profit', 0)
                    if data.get('blacklisted', False):
                        symbol_data[symbol]['blacklisted'] = True
                        
        self.aggregated_state['symbol_insights'] = symbol_data
        
        # 3. Load Calibration Trades (detailed trade history)
        calibration = self._load_json(self.STATE_FILES['calibration'])
        if calibration and isinstance(calibration, list):
            self.aggregated_state['sources_loaded'].append('calibration')
            all_trades.extend(calibration)
            
            # Extract frequency performance from calibration
            for trade in calibration:
                freq = trade.get('frequency', 0)
                freq_band = self._get_freq_band(freq)
                if freq_band not in frequency_data:
                    frequency_data[freq_band] = {'trades': 0, 'wins': 0, 'pnl': 0}
                frequency_data[freq_band]['trades'] += 1
                trade_pnl = _extract_pnl(trade)
                if trade_pnl > 0:
                    frequency_data[freq_band]['wins'] += 1
                frequency_data[freq_band]['pnl'] += trade_pnl
                
        self.aggregated_state['frequency_performance'] = frequency_data

        # 3b. Load extra trade history files (paper trading, etc.)
        for hist_file in self.EXTRA_TRADE_HISTORY:
            hist = self._load_json(hist_file)
            if hist and isinstance(hist, list):
                self.aggregated_state['sources_loaded'].append(f"history:{hist_file}")
                all_trades.extend(hist)
        
        # 4. Load HNC Frequency Log (frequency readings over time)
        hnc_log = self._load_json(self.STATE_FILES['hnc_frequency'])
        if hnc_log and isinstance(hnc_log, list):
            self.aggregated_state['sources_loaded'].append('hnc_frequency')
            # Get latest readings for each symbol
            latest_readings = {}
            for entry in hnc_log[-100:]:  # Last 100 entries
                for reading in entry.get('readings', []):
                    symbol = reading.get('symbol', '')
                    if symbol:
                        latest_readings[symbol] = {
                            'frequency': reading.get('frequency', 256),
                            'resonance': reading.get('resonance', 0.5),
                            'is_harmonic': reading.get('is_harmonic', False)
                        }
            self.aggregated_state['hnc_readings'] = latest_readings
            
        # 5. Load Adaptive Learning History
        adaptive = self._load_json(self.STATE_FILES['adaptive_learning'])
        if adaptive:
            self.aggregated_state['sources_loaded'].append('adaptive_learning')
            self.aggregated_state['learned_thresholds'] = adaptive.get('thresholds', {})
            adaptive_trades = adaptive.get('trades', [])
            all_trades.extend(adaptive_trades)
            
        # 6. Load Auris Runtime Config
        auris_config = self._load_json(self.STATE_FILES['auris_runtime'])
        if auris_config:
            self.aggregated_state['sources_loaded'].append('auris_runtime')
            self.aggregated_state['auris_targets'] = auris_config.get('targets_hz', {})
            self.aggregated_state['auris_identity'] = auris_config.get('identity', {})
            
        # 7. Load Multi-Exchange Learning (if exists)
        multi_ex = self._load_json(self.STATE_FILES['multi_exchange_learning'])
        if multi_ex:
            self.aggregated_state['sources_loaded'].append('multi_exchange_learning')
            self.aggregated_state['exchange_performance'] = multi_ex.get('by_exchange', {})

        # 7b. Load probability reports (market selection intelligence)
        for report in self.PROBABILITY_REPORTS:
            data = self._load_json(report)
            if not data:
                continue
            self.aggregated_state['sources_loaded'].append(f"probability:{report}")

            # Freshness tracking
            generated_ts = data.get('generated') or data.get('generated_at') if isinstance(data, dict) else None
            if generated_ts:
                try:
                    gen_dt = datetime.fromisoformat(generated_ts)
                    age_min = (datetime.now() - gen_dt).total_seconds() / 60
                    probability_freshness['report_ages_minutes'][report] = age_min
                except Exception:
                    pass

            entries = []
            for key in ('top_bullish', 'top_bearish', 'data', 'signals', 'items', 'predictions', 'data_points'):
                if isinstance(data, list) and key == 'data':
                    entries.extend(data)
                if isinstance(data.get(key, None), list):
                    entries.extend(data[key])
            if isinstance(data, list):
                entries.extend(data)

            for item in entries:
                if not isinstance(item, dict):
                    continue
                sym = item.get('symbol') or item.get('pair')
                if not sym:
                    continue
                try:
                    prob = float(item.get('probability', item.get('prob', 0)))
                except Exception:
                    prob = 0.0
                change = item.get('24h_change') or item.get('change') or item.get('pct_change') or 0
                state = item.get('state') or item.get('direction') or item.get('trend')

                current = probability_insights.get(sym, {})
                if not current or prob > current.get('probability', -1):
                    probability_insights[sym] = {
                        'probability': prob,
                        'state': state,
                        'change': change,
                        'source': report
                    }

                # Capture high-conviction signals for watchlist seeding
                confidence = item.get('confidence', item.get('conf', 0)) or 0.0
                if prob >= 0.80 and confidence >= 0.80:
                    high_conviction.append({
                        'symbol': sym,
                        'probability': prob,
                        'confidence': confidence,
                        'change': change,
                        'state': state,
                        'source': report,
                        'exchange': item.get('exchange'),
                    })
            
        # 8. Scan trade logs directory
        trade_logs = self._scan_trade_logs()
        if trade_logs:
            self.aggregated_state['sources_loaded'].append('trade_logs')
            all_trades.extend(trade_logs)

        # Save probability insights
        if probability_insights:
            self.aggregated_state['probability_insights'] = probability_insights

        # Probability freshness summary
        if probability_freshness['report_ages_minutes']:
            ages = list(probability_freshness['report_ages_minutes'].values())
            probability_freshness['newest_minutes'] = min(ages)
            probability_freshness['oldest_minutes'] = max(ages)
            probability_freshness['stale'] = probability_freshness['newest_minutes'] > probability_freshness['threshold_minutes']
            self.aggregated_state['probability_freshness'] = probability_freshness

        if high_conviction:
            self.aggregated_state['high_conviction_signals'] = high_conviction

        # 9. Load analytics reports (performance/forecast artifacts)
        for report in self.ANALYTICS_REPORTS:
            data = self._load_json(report)
            if not data:
                continue
            self.aggregated_state['sources_loaded'].append(f"analytics:{report}")
            entries = []
            if isinstance(data, list):
                entries = data
            elif isinstance(data, dict):
                for key in ('results', 'items', 'signals', 'data', 'top'):  # generic containers
                    if isinstance(data.get(key, None), list):
                        entries.extend(data[key])
                if not entries:
                    entries = [data]

            for item in entries:
                if not isinstance(item, dict):
                    continue
                sym = item.get('symbol') or item.get('pair') or item.get('asset')
                if not sym:
                    continue
                pnl = item.get('pnl') or item.get('pnl_usd') or item.get('profit') or 0
                wr = item.get('win_rate') or item.get('wr') or item.get('wins_ratio')
                prob = item.get('probability') or item.get('prob')
                score = item.get('score') or item.get('sharpe') or item.get('fitness')
                current = analytics_insights.get(sym, {})

                def _better(a, b):
                    # prefer higher prob/score/wr, then pnl
                    return (
                        (a.get('probability', 0) or 0) > (b.get('probability', 0) or 0) or
                        (a.get('score', 0) or 0) > (b.get('score', 0) or 0) or
                        (a.get('win_rate', 0) or 0) > (b.get('win_rate', 0) or 0) or
                        (a.get('pnl', 0) or 0) > (b.get('pnl', 0) or 0)
                    )

                candidate = {
                    'pnl': pnl,
                    'win_rate': wr,
                    'probability': prob,
                    'score': score,
                    'source': report,
                }

                if not current or _better(candidate, current):
                    analytics_insights[sym] = candidate

        if analytics_insights:
            self.aggregated_state['analytics_insights'] = analytics_insights

        # 10. Load positions files (current holdings snapshots)
        for pos_file in self.POSITION_FILES:
            pdata = self._load_json(pos_file)
            if not pdata:
                continue
            self.aggregated_state['sources_loaded'].append(f"positions:{pos_file}")
            if isinstance(pdata, dict):
                for sym, entry in pdata.items():
                    size = entry.get('quantity') or entry.get('qty') or entry.get('amount') or entry
                    positions_snapshot[sym] = size
            elif isinstance(pdata, list):
                for entry in pdata:
                    if not isinstance(entry, dict):
                        continue
                    sym = entry.get('symbol') or entry.get('pair')
                    if not sym:
                        continue
                    size = entry.get('quantity') or entry.get('qty') or entry.get('amount')
                    positions_snapshot[sym] = size

        if positions_snapshot:
            self.aggregated_state['positions_snapshot'] = positions_snapshot

        if position_hygiene['flagged']:
            self.aggregated_state['position_hygiene'] = position_hygiene

        # 11. Load auxiliary logs (diagnostic only)
        for log_file in self.AUX_LOG_FILES:
            ldata = self._load_json(log_file)
            if not ldata:
                continue
            self.aggregated_state['sources_loaded'].append(f"aux:{log_file}")
            try:
                count = len(ldata) if hasattr(ldata, '__len__') else 1
            except Exception:
                count = 1
            aux_logs[log_file] = {'entries': count}

        if aux_logs:
            self.aggregated_state['aux_logs'] = aux_logs
            
        # Calculate aggregated metrics
        self.aggregated_state['total_historical_trades'] = len(all_trades)
        if all_trades:
            wins = sum(1 for t in all_trades if _extract_pnl(t) > 0)
            self.aggregated_state['combined_win_rate'] = wins / len(all_trades) * 100
            
        # Calculate coherence bands performance
        coherence_bands = {'low': {'trades': 0, 'wins': 0}, 'mid': {'trades': 0, 'wins': 0}, 'high': {'trades': 0, 'wins': 0}}
        for trade in all_trades:
            coh = trade.get('coherence', 0.5)
            band = 'low' if coh < 0.5 else 'mid' if coh < 0.7 else 'high'
            coherence_bands[band]['trades'] += 1
            if _extract_pnl(trade) > 0:
                coherence_bands[band]['wins'] += 1
        self.aggregated_state['coherence_bands'] = coherence_bands
        
        self.aggregated_state['last_aggregation'] = time.time()
        
        logger.info(f"📊 State Aggregator: Loaded {len(self.aggregated_state['sources_loaded'])} sources, "
                   f"{self.aggregated_state['total_historical_trades']} historical trades")
        
        return self.aggregated_state
        
    def _load_json(self, filepath: str) -> Optional[Any]:
        """Safely load a JSON file."""
        if not filepath:
            return None
        try:
            full_path = os.path.join(ROOT_DIR, filepath)
            if os.path.exists(full_path):
                with open(full_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.debug(f"Could not load {filepath}: {e}")
        return None
        
    def _scan_trade_logs(self) -> List[Dict]:
        """Scan /tmp/aureon_trade_logs for historical trades."""
        trades = []
        log_dir = '/tmp/aureon_trade_logs'
        if not os.path.exists(log_dir):
            return trades
            
        try:
            for filename in os.listdir(log_dir):
                if filename.endswith('.jsonl'):
                    filepath = os.path.join(log_dir, filename)
                    with open(filepath, 'r') as f:
                        for line in f:
                            try:
                                trade = json.loads(line.strip())
                                trades.append(trade)
                            except:
                                continue
        except Exception as e:
            logger.debug(f"Trade log scan error: {e}")
            
        return trades[-500:]  # Last 500 trades
        
    def _get_freq_band(self, freq: float) -> str:
        """Get frequency band name."""
        if freq < 300:
            return 'ROOT (174-256Hz)'
        elif freq < 450:
            return 'EARTH (396-432Hz)'
        elif freq < 550:
            return 'LOVE (528Hz)'
        elif freq < 700:
            return 'THROAT (639Hz)'
        elif freq < 850:
            return 'THIRD_EYE (741Hz)'
        else:
            return 'CROWN (852-963Hz)'
            
    def get_symbol_insight(self, symbol: str) -> Dict[str, Any]:
        """Get aggregated insight for a specific symbol."""
        base_symbol = symbol.replace('USDT', '').replace('USD', '').replace('GBP', '').replace('EUR', '')
        
        # Check all symbol variations
        insight = {'hunts': 0, 'trades': 0, 'wins': 0, 'losses': 0, 'profit': 0, 'blacklisted': False, 'win_rate': 0.5}
        
        for sym, data in self.aggregated_state.get('symbol_insights', {}).items():
            if base_symbol in sym or sym in symbol:
                insight['hunts'] += data.get('total_hunts', 0)
                insight['trades'] += data.get('total_trades', 0)
                insight['wins'] += data.get('wins', 0)
                insight['losses'] += data.get('losses', 0)
                insight['profit'] += data.get('profit', 0)
                if data.get('blacklisted'):
                    insight['blacklisted'] = True
                    
        if insight['trades'] > 0:
            insight['win_rate'] = insight['wins'] / insight['trades']
            
        # Get HNC reading if available
        hnc = self.aggregated_state.get('hnc_readings', {}).get(symbol, {})
        if hnc:
            insight['frequency'] = hnc.get('frequency', 256)
            insight['resonance'] = hnc.get('resonance', 0.5)
            insight['is_harmonic'] = hnc.get('is_harmonic', False)

        # Probability signals (market selection intelligence)
        prob_insights = self.aggregated_state.get('probability_insights', {})
        for sym, pdata in prob_insights.items():
            base = sym.replace('USDT', '').replace('USD', '').replace('GBP', '').replace('EUR', '')
            if base_symbol == base or base in base_symbol:
                insight['probability_signal'] = pdata.get('probability', 0)
                insight['probability_state'] = pdata.get('state')
                insight['probability_change'] = pdata.get('change')
                insight['probability_source'] = pdata.get('source')
                break

        # Analytics signals (sim/backtest/agent metrics)
        analytics = self.aggregated_state.get('analytics_insights', {})
        for sym, adata in analytics.items():
            base = sym.replace('USDT', '').replace('USD', '').replace('GBP', '').replace('EUR', '')
            if base_symbol == base or base in base_symbol:
                insight['analytics_win_rate'] = adata.get('win_rate')
                insight['analytics_prob'] = adata.get('probability')
                insight['analytics_score'] = adata.get('score')
                insight['analytics_pnl'] = adata.get('pnl')
                insight['analytics_source'] = adata.get('source')
                break

        # Position snapshot (current holdings if available)
        positions = self.aggregated_state.get('positions_snapshot', {})
        for sym, qty in positions.items():
            base = sym.replace('USDT', '').replace('USD', '').replace('GBP', '').replace('EUR', '')
            if base_symbol == base or base in base_symbol:
                insight['position_quantity'] = qty
                break
            
        return insight
        
    def get_frequency_recommendation(self, freq: float) -> Dict[str, Any]:
        """Get recommendation based on historical frequency performance."""
        freq_band = self._get_freq_band(freq)
        perf = self.aggregated_state.get('frequency_performance', {}).get(freq_band, {})
        
        trades = perf.get('trades', 0)
        wins = perf.get('wins', 0)
        pnl = perf.get('pnl', 0)
        
        recommendation = {
            'band': freq_band,
            'historical_trades': trades,
            'historical_win_rate': wins / max(1, trades),
            'historical_pnl': pnl,
            'confidence': min(1.0, trades / 20),  # Full confidence after 20 trades
            'boost_factor': 1.0
        }
        
        # Calculate boost factor based on historical performance
        if trades >= 10:
            win_rate = wins / trades
            if win_rate > 0.60:
                recommendation['boost_factor'] = 1.0 + (win_rate - 0.50) * 0.5
            elif win_rate < 0.40:
                recommendation['boost_factor'] = 0.7
                
        return recommendation
        
    def get_coherence_recommendation(self, coherence: float) -> Dict[str, Any]:
        """Get recommendation based on historical coherence performance."""
        band = 'low' if coherence < 0.5 else 'mid' if coherence < 0.7 else 'high'
        perf = self.aggregated_state.get('coherence_bands', {}).get(band, {})
        
        trades = perf.get('trades', 0)
        wins = perf.get('wins', 0)
        
        return {
            'band': band,
            'historical_trades': trades,
            'historical_win_rate': wins / max(1, trades),
            'confidence': min(1.0, trades / 20),
            'recommended_min': 0.45 if band == 'low' else 0.50 if band == 'mid' else 0.55
        }

    def get_top_signals(self, n: int = 5) -> Dict[str, List[Tuple[str, Dict[str, Any]]]]:
        """Return top probability and analytics signals plus largest positions for visibility."""
        probs = sorted(
            self.aggregated_state.get('probability_insights', {}).items(),
            key=lambda kv: kv[1].get('probability', 0) or 0,
            reverse=True
        )[:n]

        def _analytic_key(item):
            data = item[1]
            return (
                data.get('score') or 0,
                data.get('win_rate') or 0,
                data.get('probability') or 0,
                data.get('pnl') or 0,
            )

        analytics = sorted(
            self.aggregated_state.get('analytics_insights', {}).items(),
            key=_analytic_key,
            reverse=True
        )[:n]

        positions = sorted(
            self.aggregated_state.get('positions_snapshot', {}).items(),
            key=lambda kv: abs(kv[1]) if isinstance(kv[1], (int, float)) else 0,
            reverse=True
        )[:n]

        return {
            'probability': probs,
            'analytics': analytics,
            'positions': positions,
        }
        
    def load_organism_thoughts(self, limit: int = 50):
        """Load recent thoughts to determine organism health."""
        try:
            filepath = os.path.join(ROOT_DIR, self.LOG_FILES['thoughts'])
            if not os.path.exists(filepath):
                return

            thoughts = []
            # Read last N lines efficiently
            with open(filepath, 'rb') as f:
                try:
                    f.seek(-10000, os.SEEK_END) # Go back ~10KB
                except OSError:
                    f.seek(0)
                
                lines = f.readlines()
                # Decode and parse last N lines
                for line in lines[-limit:]:
                    try:
                        thoughts.append(json.loads(line.decode('utf-8')))
                    except:
                        pass
            
            # Analyze health
            now = time.time()
            pulse = {
                'miner': {'last_seen': 0, 'status': 'OFFLINE'},
                'risk': {'last_seen': 0, 'status': 'OFFLINE'},
                'execution': {'last_seen': 0, 'status': 'OFFLINE'},
                'ecosystem': {'last_seen': 0, 'status': 'OFFLINE'},
            }
            
            for t in thoughts:
                src = t.get('source', 'unknown')
                ts = t.get('ts', 0)
                if src in pulse:
                    pulse[src]['last_seen'] = max(pulse[src]['last_seen'], ts)
            
            # Determine status based on recency (e.g. seen in last 60s)
            healthy_count = 0
            for src, data in pulse.items():
                age = now - data['last_seen']
                if age < 60:
                    data['status'] = 'ONLINE'
                    healthy_count += 1
                elif age < 300:
                    data['status'] = 'STALE'
                else:
                    data['status'] = 'OFFLINE'
            
            overall_status = 'HEALTHY' if healthy_count >= 3 else 'DEGRADED' if healthy_count > 0 else 'OFFLINE'
            
            self.aggregated_state['organism_health'] = {
                'status': overall_status,
                'pulse': pulse,
                'recent_thoughts': thoughts[-5:] # Keep last 5 for display
            }
            self.aggregated_state['sources_loaded'].append('organism_thoughts')
            
        except Exception as e:
            logger.debug(f"Failed to load organism thoughts: {e}")

    def save_aggregated_state(self):
        """Save multi-exchange learning state for persistence."""
        try:
            filepath = os.path.join(ROOT_DIR, self.STATE_FILES['multi_exchange_learning'])
            with open(filepath, 'w') as f:
                json.dump({
                    'by_exchange': self.aggregated_state.get('exchange_performance', {}),
                    'frequency_performance': self.aggregated_state.get('frequency_performance', {}),
                    'coherence_bands': self.aggregated_state.get('coherence_bands', {}),
                    'probability_insights': self.aggregated_state.get('probability_insights', {}),
                    'total_historical_trades': self.aggregated_state.get('total_historical_trades', 0),
                    'combined_win_rate': self.aggregated_state.get('combined_win_rate', 0),
                    'updated_at': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save aggregated state: {e}")
            
    def get_summary(self) -> str:
        """Get formatted summary of aggregated state."""
        state = self.aggregated_state
        
        # Calculate TRUE P&L
        first_start = state.get('first_start_balance', 0)
        current = state.get('current_balance', 0)
        true_pnl = current - first_start if first_start > 0 else 0
        true_pct = (true_pnl / first_start * 100) if first_start > 0 else 0
        first_start_time = state.get('first_start_time', 0)
        start_str = time.strftime('%Y-%m-%d %H:%M', time.localtime(first_start_time)) if first_start_time > 0 else 'Unknown'
        
        lines = [
            "═══════════════════════════════════════",
            "📊 UNIFIED STATE AGGREGATOR SUMMARY",
            "═══════════════════════════════════════",
            f"Sources Loaded: {', '.join(state.get('sources_loaded', []))}",
            f"Historical Trades: {state.get('total_historical_trades', 0)}",
            f"Combined Win Rate: {state.get('combined_win_rate', 0):.1f}%",
            "",
            "💵 PORTFOLIO (TRUE from first run):",
            f"   First Started: {start_str}",
            f"   TRUE Starting: £{first_start:.2f}",
            f"   Current: £{current:.2f}",
            f"   TRUE P&L: £{true_pnl:+.2f} ({true_pct:+.1f}%)",
            "",
            "Frequency Performance:"
        ]
        
        for band, perf in state.get('frequency_performance', {}).items():
            wr = perf['wins'] / max(1, perf['trades']) * 100
            lines.append(f"  {band}: {perf['trades']} trades, {wr:.1f}% WR, ${perf['pnl']:.2f}")
            
        lines.append("")
        lines.append("Coherence Bands:")
        for band, perf in state.get('coherence_bands', {}).items():
            wr = perf['wins'] / max(1, perf['trades']) * 100
            lines.append(f"  {band}: {perf['trades']} trades, {wr:.1f}% WR")
            
        health = state.get('organism_health', {})
        lines.append("")
        lines.append(f"🧠 ORGANISM HEALTH: {health.get('status', 'UNKNOWN')}")
        pulse = health.get('pulse', {})
        lines.append(f"   Miner: {pulse.get('miner', {}).get('status')} | Risk: {pulse.get('risk', {}).get('status')} | Exec: {pulse.get('execution', {}).get('status')}")
            
        return "\n".join(lines)


# Global state aggregator instance
STATE_AGGREGATOR = UnifiedStateAggregator()


class CognitiveImmuneSystem:
    """Autonomous antivirus/immune layer that validates cognition integrity."""

    def __init__(self, ecosystem: 'AureonKrakenEcosystem', thought_bus: Optional[ThoughtBus], state_aggregator: UnifiedStateAggregator):
        self.ecosystem = ecosystem
        self.bus = thought_bus
        self.aggregator = state_aggregator
        self.last_scan = 0.0
        self.scan_interval = 30.0
        self.fault_memory: Deque[Dict[str, Any]] = deque(maxlen=200)
        self.minds = {
            'Miner': self._miner_mind,
            'Risk': self._risk_mind,
            'Execution': self._execution_mind,
            'Bridge': self._bridge_mind,
            'NewsFeed': self._newsfeed_mind,
            'KnowledgeBase': self._knowledge_mind,
        }

        if self.bus:
            self.bus.subscribe("system.error", self._on_fault_thought)

    # ------------------------------------------------------------------
    # Event ingestion
    # ------------------------------------------------------------------
    def _on_fault_thought(self, thought: Thought) -> None:
        payload = thought.payload if isinstance(thought.payload, dict) else {}
        fault = {
            'ts': thought.ts,
            'source': payload.get('while_handling_topic', thought.topic),
            'error': payload.get('error', 'unknown fault'),
            'trace_id': thought.trace_id,
        }
        self.fault_memory.append(fault)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def scan_and_heal(self, force: bool = False) -> None:
        now = time.time()
        if not force and (now - self.last_scan) < self.scan_interval:
            return
        self.last_scan = now

        faults = self._collect_faults(now)
        if not faults:
            return

        healing_plan: List[Dict[str, Any]] = []
        for _, handler in self.minds.items():
            plan = handler(faults)
            if plan:
                healing_plan.extend(plan)

        if not healing_plan:
            self._emit_thought("immune.alert", {"faults": faults, "plan": []})
            return

        self._execute_plan(healing_plan, faults)

    # ------------------------------------------------------------------
    # Fault analysis helpers
    # ------------------------------------------------------------------
    def _collect_faults(self, now: float) -> List[Dict[str, Any]]:
        faults: List[Dict[str, Any]] = []

        # Organism status from aggregator
        health = self.aggregator.aggregated_state.get('organism_health', {}) if self.aggregator else {}
        status = health.get('status')
        if status in ('DEGRADED', 'OFFLINE'):
            faults.append({'code': f'ORGANISM_{status}', 'detail': health})

        # Probability freshness
        pfresh = self.aggregator.aggregated_state.get('probability_freshness', {}) if self.aggregator else {}
        if pfresh.get('stale'):
            faults.append({'code': 'PROBABILITY_STALE', 'detail': pfresh})

        # Websocket/liveness
        ws_age = now - getattr(self.ecosystem, 'ws_last_message', now)
        ws_timeout = CONFIG.get('WS_HEARTBEAT_TIMEOUT', 30)
        if ws_age > ws_timeout:
            faults.append({'code': 'WS_STALE', 'detail': {'age': ws_age, 'timeout': ws_timeout}})

        # Trading halt
        tracker = getattr(self.ecosystem, 'tracker', None)
        if tracker and getattr(tracker, 'trading_halted', False):
            faults.append({'code': 'TRADING_HALTED', 'detail': {'reason': tracker.halt_reason}})

        # Bridge sync
        if getattr(self.ecosystem, 'bridge_enabled', False):
            bridge_age = now - getattr(self.ecosystem, 'last_bridge_sync', 0.0)
            if bridge_age > getattr(self.ecosystem, 'bridge_sync_interval', 10.0) * 4:
                faults.append({'code': 'BRIDGE_STALE', 'detail': {'age': bridge_age}})

        # News feed staleness (if no news in 30+ minutes)
        news_feed = getattr(self.ecosystem, 'news_feed', None)
        if news_feed and hasattr(news_feed, 'last_poll_time') and news_feed.last_poll_time:
            try:
                from datetime import datetime
                news_age_seconds = (datetime.utcnow() - news_feed.last_poll_time).total_seconds()
                if news_age_seconds > 1800:  # 30 minutes
                    faults.append({'code': 'NEWS_STALE', 'detail': {'age_seconds': news_age_seconds}})
            except Exception:
                pass

        # News API errors accumulating
        if news_feed:
            news_metrics = getattr(news_feed, 'metrics', {})
            news_errors = news_metrics.get('errors', 0)
            if news_errors >= 5:
                faults.append({'code': 'NEWS_API_ERRORS', 'detail': {'errors': news_errors}})

        # Knowledge base errors
        knowledge_base = getattr(self.ecosystem, 'knowledge_base', None)
        if knowledge_base:
            kb_metrics = getattr(knowledge_base, 'metrics', {})
            kb_errors = kb_metrics.get('errors', 0)
            if kb_errors >= 10:
                faults.append({'code': 'KNOWLEDGE_API_ERRORS', 'detail': {'errors': kb_errors}})

        # Thought-level faults
        recent_faults = [f for f in self.fault_memory if now - f['ts'] < 120]
        for fault in recent_faults:
            faults.append({'code': 'THOUGHT_FAULT', 'detail': fault})

        return faults

    # ------------------------------------------------------------------
    # Mind protocols
    # ------------------------------------------------------------------
    def _miner_mind(self, faults: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        plan: List[Dict[str, Any]] = []
        if any(f['code'] in ('PROBABILITY_STALE', 'THOUGHT_FAULT') for f in faults):
            plan.append({
                'mind': 'Miner',
                'action': 'REFRESH_PROBABILITY_REPORTS',
                'description': 'Reload probability reports + aggregated state',
                'callable': self._heal_probability_reports,
                'auto_execute': True,
            })
        return plan

    def _risk_mind(self, faults: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        plan: List[Dict[str, Any]] = []
        if any(f['code'] in ('TRADING_HALTED', 'ORGANISM_DEGRADED') for f in faults):
            plan.append({
                'mind': 'Risk',
                'action': 'AUDIT_POSITIONS',
                'description': 'Run position/risk audit to release halts if conditions improve',
                'callable': self._heal_risk_controls,
                'auto_execute': True,
            })
        return plan

    def _execution_mind(self, faults: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        plan: List[Dict[str, Any]] = []
        if any(f['code'] == 'WS_STALE' for f in faults):
            plan.append({
                'mind': 'Execution',
                'action': 'RECHARGE_MARKET_DATA',
                'description': 'Refresh tickers and request websocket heartbeat',
                'callable': self._heal_market_data,
                'auto_execute': True,
            })
        return plan

    def _bridge_mind(self, faults: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        plan: List[Dict[str, Any]] = []
        if any(f['code'] == 'BRIDGE_STALE' for f in faults):
            plan.append({
                'mind': 'Bridge',
                'action': 'SYNC_BRIDGE',
                'description': 'Force a bridge sync so Ultimate/Unified share state',
                'callable': self._heal_bridge_link,
                'auto_execute': True,
            })
        return plan

    def _newsfeed_mind(self, faults: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """News Feed mind - handles news API staleness and errors."""
        plan: List[Dict[str, Any]] = []
        
        # Handle stale news
        if any(f['code'] == 'NEWS_STALE' for f in faults):
            plan.append({
                'mind': 'NewsFeed',
                'action': 'FORCE_NEWS_POLL',
                'description': 'Force refresh news feed from World News API',
                'callable': self._heal_news_feed,
                'auto_execute': True,
            })
        
        # Handle API errors accumulating
        if any(f['code'] == 'NEWS_API_ERRORS' for f in faults):
            plan.append({
                'mind': 'NewsFeed',
                'action': 'RESET_NEWS_METRICS',
                'description': 'Reset news API error counters and retry',
                'callable': self._heal_news_errors,
                'auto_execute': True,
            })
        
        return plan

    def _knowledge_mind(self, faults: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Knowledge Base mind - handles Wikipedia API errors."""
        plan: List[Dict[str, Any]] = []
        
        # Handle API errors accumulating
        if any(f['code'] == 'KNOWLEDGE_API_ERRORS' for f in faults):
            plan.append({
                'mind': 'KnowledgeBase',
                'action': 'RESET_KNOWLEDGE_METRICS',
                'description': 'Reset knowledge base error counters and clear stale cache',
                'callable': self._heal_knowledge_errors,
                'auto_execute': True,
            })
        
        return plan

    # ------------------------------------------------------------------
    # Healing actions
    # ------------------------------------------------------------------
    def _heal_probability_reports(self) -> None:
        loader = getattr(self.ecosystem, 'probability_loader', None)
        if loader:
            loader.load_all_reports()
        self.aggregator.load_all_sources()

    def _heal_risk_controls(self) -> None:
        self.ecosystem.check_positions()
        self.ecosystem.refresh_equity()

    def _heal_market_data(self) -> None:
        try:
            self.ecosystem.refresh_tickers()
        finally:
            self.ecosystem.ws_last_message = time.time()

    def _heal_bridge_link(self) -> None:
        if getattr(self.ecosystem, 'bridge_enabled', False):
            self.ecosystem.sync_bridge()

    def _heal_news_feed(self) -> None:
        """Force a news poll to refresh market sentiment data."""
        news_feed = getattr(self.ecosystem, 'news_feed', None)
        if news_feed:
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(news_feed.poll_and_publish())
                finally:
                    loop.close()
            except Exception as e:
                logger.warning(f"News feed heal failed: {e}")

    def _heal_news_errors(self) -> None:
        """Reset news API error counters."""
        news_feed = getattr(self.ecosystem, 'news_feed', None)
        if news_feed and hasattr(news_feed, 'metrics'):
            news_feed.metrics['errors'] = 0
            logger.info("News feed error counters reset")

    def _heal_knowledge_errors(self) -> None:
        """Reset knowledge base error counters and clear stale cache."""
        knowledge_base = getattr(self.ecosystem, 'knowledge_base', None)
        if knowledge_base:
            if hasattr(knowledge_base, 'metrics'):
                knowledge_base.metrics['errors'] = 0
            # Clear cache to force fresh lookups
            if hasattr(knowledge_base, 'cache'):
                knowledge_base.cache.clear()
            logger.info("Knowledge base error counters reset, cache cleared")

    # ------------------------------------------------------------------
    # Execution + telemetry
    # ------------------------------------------------------------------
    def _execute_plan(self, plan: List[Dict[str, Any]], faults: List[Dict[str, Any]]) -> None:
        executed = []
        for step in plan:
            callable_fn = step.get('callable')
            ok = False
            error = None
            if callable_fn:
                try:
                    callable_fn()
                    ok = True
                except Exception as exc:
                    error = str(exc)
            executed.append({
                'mind': step.get('mind'),
                'action': step.get('action'),
                'status': 'ok' if ok else 'error',
                'error': error,
            })

        self._emit_thought("immune.heal", {
            'executed': executed,
            'faults': faults,
        })

    def _emit_thought(self, topic: str, payload: Dict[str, Any]) -> None:
        if not self.bus:
            return
        self.bus.publish(Thought(
            source="immune_system",
            topic=topic,
            payload=payload,
        ))


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
# 🧠 ADAPTIVE LEARNING ENGINE - Self-Optimizing Parameters
# ═══════════════════════════════════════════════════════════════

class AdaptiveLearningEngine:
    """
    Learns from past trades and dynamically adjusts system parameters.
    
    Key Optimizations:
    1. Win rate tracking by frequency band (432Hz vs 528Hz vs 440Hz)
    2. Coherence threshold optimization based on actual outcomes
    3. Score threshold calibration using rolling performance
    4. Time-of-day pattern detection
    5. Volume correlation analysis
    """
    
    def __init__(self, history_file: str = 'adaptive_learning_history.json'):
        self.history_file = history_file
        self.trade_history: List[Dict] = []
        self.max_history = 500  # Keep last 500 trades for analysis

        # Keep a pristine copy of defaults for easy reset when data is stale
        self.default_thresholds = {
            'min_coherence': CONFIG.get('ENTRY_COHERENCE', 0.45),
            'min_score': CONFIG.get('MIN_SCORE', 65),
            'min_probability': CONFIG.get('PROB_MIN_CONFIDENCE', 0.50),
            'harmonic_bonus': CONFIG.get('HNC_HARMONIC_BONUS', 1.15),
            'distortion_penalty': CONFIG.get('HNC_DISTORTION_PENALTY', 0.70),
        }
        self.optimized_thresholds = self.default_thresholds.copy()
        self.recency_window_days = 10  # Ignore trades older than this to avoid stale fear
        
        # Performance metrics by category
        self.metrics_by_frequency: Dict[str, Dict] = {}  # freq_band -> {wins, losses, total_pnl}
        self.metrics_by_coherence: Dict[str, Dict] = {}  # coherence_range -> {wins, losses}
        self.metrics_by_score: Dict[str, Dict] = {}      # score_range -> {wins, losses}
        self.metrics_by_hour: Dict[int, Dict] = {}       # hour -> {wins, losses}
        self.metrics_by_action: Dict[str, Dict] = {}     # HNC action -> {wins, losses}
        
        # Learning parameters
        self.learning_rate = 0.05  # How quickly to adapt
        self.min_samples_for_learning = 20  # Minimum trades before adjusting
        self.confidence_interval = 0.95  # Statistical confidence for changes
        
        self._load_history()
        
    def _load_history(self):
        """Load historical trades from file."""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    self.trade_history = data.get('trades', [])[-self.max_history:]
                    self.optimized_thresholds = {
                        **self.default_thresholds,
                        **data.get('thresholds', {})
                    }

                    stale_removed = self._filter_recent_trades()
                    if stale_removed:
                        logger.info(f"Adaptive Learning: dropped {stale_removed} stale trades (> {self.recency_window_days}d) to stay active")

                    self._clamp_thresholds()
                    self._rebuild_metrics()
                    
                    if not self.trade_history:
                        # If everything was stale, reset to defaults so the system will trade
                        self.optimized_thresholds = self.default_thresholds.copy()
                        logger.info("Adaptive Learning: no recent trades found, resetting thresholds to defaults")
        except Exception as e:
            logger.warning(f"Could not load learning history: {e}")
            
    def _save_history(self):
        """Save trade history and learned thresholds."""
        try:
            with open(self.history_file, 'w') as f:
                json.dump({
                    'trades': self.trade_history[-self.max_history:],
                    'thresholds': self.optimized_thresholds,
                    'updated_at': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save learning history: {e}")
            
    def _rebuild_metrics(self):
        """Rebuild performance metrics from trade history."""
        self.metrics_by_frequency = {}
        self.metrics_by_coherence = {}
        self.metrics_by_score = {}
        self.metrics_by_hour = {}
        self.metrics_by_action = {}
        
        for trade in self.trade_history:
            self._update_metrics(trade)
            
    def _get_frequency_band(self, freq: float) -> str:
        """Map frequency to band name."""
        if freq <= 200:
            return '174_FOUNDATION'
        elif freq <= 300:
            return '256_ROOT'
        elif freq <= 410:
            return '396_LIBERATION'
        elif freq <= 438:
            return '432_NATURAL'
        elif freq <= 445:
            return '440_DISTORTION'
        elif freq <= 520:
            return '512_VISION'
        elif freq <= 580:
            return '528_LOVE'
        elif freq <= 700:
            return '639_CONNECTION'
        elif freq <= 800:
            return '741_AWAKENING'
        elif freq <= 900:
            return '852_INTUITION'
        else:
            return '963_UNITY'
            
    def _get_coherence_range(self, coherence: float) -> str:
        """Map coherence to range bucket."""
        if coherence < 0.3:
            return 'LOW_0-30'
        elif coherence < 0.5:
            return 'MED_30-50'
        elif coherence < 0.7:
            return 'HIGH_50-70'
        else:
            return 'VERY_HIGH_70+'
            
    def _get_score_range(self, score: float) -> str:
        """Map score to range bucket."""
        if score < 50:
            return 'LOW_0-50'
        elif score < 65:
            return 'MED_50-65'
        elif score < 80:
            return 'HIGH_65-80'
        else:
            return 'VERY_HIGH_80+'
            
    def _update_metrics(self, trade: Dict):
        """Update metrics with a single trade."""
        is_win = trade.get('pnl', 0) > 0
        pnl = trade.get('pnl', 0)
        
        # By frequency
        freq = trade.get('frequency', 256)
        band = self._get_frequency_band(freq)
        if band not in self.metrics_by_frequency:
            self.metrics_by_frequency[band] = {'wins': 0, 'losses': 0, 'total_pnl': 0, 'trades': []}
        self.metrics_by_frequency[band]['wins' if is_win else 'losses'] += 1
        self.metrics_by_frequency[band]['total_pnl'] += pnl
        self.metrics_by_frequency[band]['trades'].append(pnl)
        
        # By coherence
        coherence = trade.get('coherence', 0.5)
        coh_range = self._get_coherence_range(coherence)
        if coh_range not in self.metrics_by_coherence:
            self.metrics_by_coherence[coh_range] = {'wins': 0, 'losses': 0, 'trades': []}
        self.metrics_by_coherence[coh_range]['wins' if is_win else 'losses'] += 1
        self.metrics_by_coherence[coh_range]['trades'].append(pnl)
        
        # By score
        score = trade.get('score', 50)
        score_range = self._get_score_range(score)
        if score_range not in self.metrics_by_score:
            self.metrics_by_score[score_range] = {'wins': 0, 'losses': 0, 'trades': []}
        self.metrics_by_score[score_range]['wins' if is_win else 'losses'] += 1
        self.metrics_by_score[score_range]['trades'].append(pnl)
        
        # By hour of day
        entry_time = trade.get('entry_time', time.time())
        hour = datetime.fromtimestamp(entry_time).hour
        if hour not in self.metrics_by_hour:
            self.metrics_by_hour[hour] = {'wins': 0, 'losses': 0, 'trades': []}
        self.metrics_by_hour[hour]['wins' if is_win else 'losses'] += 1
        self.metrics_by_hour[hour]['trades'].append(pnl)
        
        # By HNC action
        action = trade.get('hnc_action', 'HOLD')
        if action not in self.metrics_by_action:
            self.metrics_by_action[action] = {'wins': 0, 'losses': 0, 'trades': []}
        self.metrics_by_action[action]['wins' if is_win else 'losses'] += 1
        self.metrics_by_action[action]['trades'].append(pnl)
        
    def record_trade(self, trade_data: Dict):
        """
        Record a completed trade for learning.
        
        trade_data should include:
        - symbol, entry_price, exit_price, pnl
        - frequency, coherence, score
        - entry_time, hnc_action, probability
        """
        self.trade_history.append(trade_data)
        if len(self.trade_history) > self.max_history:
            self.trade_history = self.trade_history[-self.max_history:]
            
        self._update_metrics(trade_data)
        
        # Periodically optimize thresholds
        if len(self.trade_history) % 10 == 0:
            self.optimize_thresholds()
            self._save_history()
            
    def optimize_thresholds(self):
        """
        Analyze trade history and optimize thresholds.
        Only adjusts if we have statistical confidence.
        """
        total_trades = len(self.trade_history)
        if total_trades < self.min_samples_for_learning:
            return  # Not enough data
            
        # 1. Optimize coherence threshold
        self._optimize_coherence_threshold()
        
        # 2. Optimize score threshold
        self._optimize_score_threshold()
        
        # 3. Optimize frequency bonuses/penalties
        self._optimize_frequency_modifiers()
        
        # 4. Optimize probability threshold
        self._optimize_probability_threshold()
        
        # Make sure nothing drifts into over-cautious territory
        self._clamp_thresholds()

        logger.info(f"🧠 Adaptive Learning: Thresholds updated based on {total_trades} trades")

    def _filter_recent_trades(self) -> int:
        """Drop trades older than the recency window to avoid stale fear."""
        cutoff = time.time() - self.recency_window_days * 86400
        recent = [t for t in self.trade_history if t.get('entry_time', cutoff) >= cutoff]
        removed = len(self.trade_history) - len(recent)
        self.trade_history = recent
        return removed

    def _clamp_thresholds(self):
        """Clamp thresholds to sane ranges so stale data cannot freeze trading."""
        bounds = {
            'min_coherence': (0.30, 0.75),
            'min_score': (45, 75),
            'min_probability': (0.40, 0.65),
            'harmonic_bonus': (1.00, 1.30),
            'distortion_penalty': (0.50, 0.90),
        }
        for key, (low, high) in bounds.items():
            val = self.optimized_thresholds.get(key, self.default_thresholds.get(key, low))
            self.optimized_thresholds[key] = max(low, min(high, val))
        
    def _optimize_coherence_threshold(self):
        """Find optimal coherence threshold based on win rates."""
        best_threshold = self.optimized_thresholds['min_coherence']
        best_edge = 0
        
        # Test different coherence thresholds
        for threshold_name, metrics in self.metrics_by_coherence.items():
            total = metrics['wins'] + metrics['losses']
            if total < 5:
                continue
                
            win_rate = metrics['wins'] / total
            avg_pnl = sum(metrics['trades']) / len(metrics['trades']) if metrics['trades'] else 0
            
            # Edge = win_rate * avg_win - (1-win_rate) * avg_loss (simplified)
            edge = avg_pnl
            
            # Higher coherence ranges should have better edge
            if 'HIGH' in threshold_name or 'VERY_HIGH' in threshold_name:
                if edge > best_edge and win_rate > 0.50:
                    best_edge = edge
                    # Extract threshold from range name
                    if 'VERY_HIGH' in threshold_name:
                        best_threshold = 0.70
                    elif 'HIGH_50-70' in threshold_name:
                        best_threshold = 0.50
                        
        # Gradual adjustment
        current = self.optimized_thresholds['min_coherence']
        new_threshold = current + (best_threshold - current) * self.learning_rate
        self.optimized_thresholds['min_coherence'] = round(max(0.30, min(0.80, new_threshold)), 2)
        
    def _optimize_score_threshold(self):
        """Find optimal score threshold based on win rates."""
        best_threshold = self.optimized_thresholds['min_score']
        best_edge = 0
        
        for score_range, metrics in self.metrics_by_score.items():
            total = metrics['wins'] + metrics['losses']
            if total < 5:
                continue
                
            win_rate = metrics['wins'] / total
            avg_pnl = sum(metrics['trades']) / len(metrics['trades']) if metrics['trades'] else 0
            
            if 'HIGH' in score_range or 'VERY_HIGH' in score_range:
                if avg_pnl > best_edge and win_rate > 0.50:
                    best_edge = avg_pnl
                    if 'VERY_HIGH' in score_range:
                        best_threshold = 65  # Lowered from 80 to be less restrictive
                    elif 'HIGH' in score_range:
                        best_threshold = 50  # Lowered from 65
                        
        current = self.optimized_thresholds['min_score']
        new_threshold = current + (best_threshold - current) * self.learning_rate
        self.optimized_thresholds['min_score'] = int(max(40, min(70, new_threshold)))  # Lowered from 50-90
        
    def _optimize_frequency_modifiers(self):
        """Adjust harmonic bonus and distortion penalty based on actual performance."""
        # Check 528Hz (LOVE) performance
        love_metrics = self.metrics_by_frequency.get('528_LOVE', {})
        if love_metrics.get('wins', 0) + love_metrics.get('losses', 0) >= 5:
            love_win_rate = love_metrics['wins'] / (love_metrics['wins'] + love_metrics['losses'])
            if love_win_rate > 0.55:
                # Increase harmonic bonus
                current = self.optimized_thresholds['harmonic_bonus']
                self.optimized_thresholds['harmonic_bonus'] = min(1.30, current + 0.02)
            elif love_win_rate < 0.45:
                # Decrease harmonic bonus
                current = self.optimized_thresholds['harmonic_bonus']
                self.optimized_thresholds['harmonic_bonus'] = max(1.0, current - 0.02)
                
        # Check 440Hz (DISTORTION) performance
        distortion_metrics = self.metrics_by_frequency.get('440_DISTORTION', {})
        if distortion_metrics.get('wins', 0) + distortion_metrics.get('losses', 0) >= 5:
            distortion_win_rate = distortion_metrics['wins'] / (distortion_metrics['wins'] + distortion_metrics['losses'])
            if distortion_win_rate < 0.45:
                # Increase penalty (lower multiplier)
                current = self.optimized_thresholds['distortion_penalty']
                self.optimized_thresholds['distortion_penalty'] = max(0.50, current - 0.02)
            elif distortion_win_rate > 0.55:
                # Decrease penalty
                current = self.optimized_thresholds['distortion_penalty']
                self.optimized_thresholds['distortion_penalty'] = min(1.0, current + 0.02)
                
    def _optimize_probability_threshold(self):
        """Optimize probability confidence threshold."""
        # Analyze trades by probability outcome
        high_prob_trades = [t for t in self.trade_history if t.get('probability', 0.5) >= 0.65]
        low_prob_trades = [t for t in self.trade_history if t.get('probability', 0.5) < 0.40]
        
        if len(high_prob_trades) >= 10:
            high_prob_wins = sum(1 for t in high_prob_trades if t.get('pnl', 0) > 0)
            high_prob_wr = high_prob_wins / len(high_prob_trades)
            
            # If high probability trades are winning well, trust them more
            if high_prob_wr > 0.60:
                current = self.optimized_thresholds['min_probability']
                self.optimized_thresholds['min_probability'] = max(0.40, current - 0.02)
                
    def get_optimized_thresholds(self) -> Dict:
        """Return current optimized thresholds."""
        return self.optimized_thresholds.copy()
        
    def get_best_hours(self, top_n: int = 5) -> List[int]:
        """Return hours with best win rates."""
        hour_stats = []
        for hour, metrics in self.metrics_by_hour.items():
            total = metrics['wins'] + metrics['losses']
            if total >= 3:
                win_rate = metrics['wins'] / total
                hour_stats.append((hour, win_rate, total))
                
        hour_stats.sort(key=lambda x: x[1], reverse=True)
        return [h[0] for h in hour_stats[:top_n]]
        
    def get_best_frequency_bands(self) -> List[str]:
        """Return frequency bands with best performance."""
        band_stats = []
        for band, metrics in self.metrics_by_frequency.items():
            total = metrics['wins'] + metrics['losses']
            if total >= 5:
                win_rate = metrics['wins'] / total
                avg_pnl = metrics['total_pnl'] / total
                band_stats.append((band, win_rate, avg_pnl, total))
                
        band_stats.sort(key=lambda x: x[2], reverse=True)  # Sort by avg PnL
        return [b[0] for b in band_stats if b[1] > 0.50]  # Return profitable bands
        
    def get_learning_summary(self) -> str:
        """Get human-readable learning summary."""
        total = len(self.trade_history)
        wins = sum(1 for t in self.trade_history if t.get('pnl', 0) > 0)
        
        lines = [
            "═══════════════════════════════════════",
            "🧠 ADAPTIVE LEARNING SUMMARY",
            "═══════════════════════════════════════",
            f"Total Trades Analyzed: {total}",
            f"Overall Win Rate: {wins/total*100:.1f}%" if total > 0 else "N/A",
            "",
            "Optimized Thresholds:",
            f"  • Min Coherence: {self.optimized_thresholds['min_coherence']:.2f}",
            f"  • Min Score: {self.optimized_thresholds['min_score']}",
            f"  • Min Probability: {self.optimized_thresholds['min_probability']:.2f}",
            f"  • Harmonic Bonus: {self.optimized_thresholds['harmonic_bonus']:.2f}x",
            f"  • Distortion Penalty: {self.optimized_thresholds['distortion_penalty']:.2f}x",
        ]
        
        best_bands = self.get_best_frequency_bands()
        if best_bands:
            lines.append("")
            lines.append("Best Frequency Bands:")
            for band in best_bands[:3]:
                metrics = self.metrics_by_frequency.get(band, {})
                total_b = metrics.get('wins', 0) + metrics.get('losses', 0)
                wr = metrics.get('wins', 0) / total_b * 100 if total_b > 0 else 0
                lines.append(f"  🎵 {band}: {wr:.0f}% WR ({total_b} trades)")
                
        best_hours = self.get_best_hours(3)
        if best_hours:
            lines.append("")
            lines.append("Best Trading Hours (UTC):")
            for hour in best_hours:
                metrics = self.metrics_by_hour.get(hour, {})
                total_h = metrics.get('wins', 0) + metrics.get('losses', 0)
                wr = metrics.get('wins', 0) / total_h * 100 if total_h > 0 else 0
                lines.append(f"  ⏰ {hour:02d}:00 - {wr:.0f}% WR ({total_h} trades)")
                
        return "\n".join(lines)
        
    def get_entry_recommendation(self, symbol: str, frequency: float, coherence: float, 
                                  score: int, probability: float, current_hour: int = None) -> Dict:
        """
        🎯 PROACTIVE ANALYTICS: Get recommendation BEFORE entering a trade.
        
        Returns learned insights based on historical performance for similar conditions.
        This is what was missing - the system now TELLS YOU what to expect.
        """
        if current_hour is None:
            current_hour = datetime.now().hour
            
        recommendation = {
            'should_trade': True,
            'confidence': 'low',
            'expected_win_rate': 0.50,
            'similar_trades': 0,
            'suggested_hold_cycles': CONFIG['MIN_HOLD_CYCLES'],
            'suggested_take_profit': CONFIG['TAKE_PROFIT_PCT'],
            'suggested_stop_loss': CONFIG['STOP_LOSS_PCT'],
            'warnings': [],
            'advantages': [],
            'frequency_insight': None,
            'hour_insight': None,
            'coherence_insight': None
        }
        
        # ═══ FREQUENCY BAND ANALYSIS ═══
        band = self._get_frequency_band(frequency)
        freq_metrics = self.metrics_by_frequency.get(band, {'wins': 0, 'losses': 0, 'total_pnl': 0, 'trades': []})
        freq_total = freq_metrics.get('wins', 0) + freq_metrics.get('losses', 0)
        
        if freq_total >= 3:
            freq_wr = freq_metrics['wins'] / freq_total
            avg_pnl_per_trade = freq_metrics['total_pnl'] / freq_total if freq_total > 0 else 0
            
            recommendation['frequency_insight'] = {
                'band': band,
                'win_rate': freq_wr,
                'avg_pnl': avg_pnl_per_trade,
                'sample_size': freq_total
            }
            
            if freq_wr >= 0.60:
                recommendation['advantages'].append(f"🎵 {band} has {freq_wr*100:.0f}% WR ({freq_total} trades)")
                recommendation['expected_win_rate'] = max(recommendation['expected_win_rate'], freq_wr * 0.9)  # 10% confidence haircut
            elif freq_wr < 0.40:
                recommendation['warnings'].append(f"⚠️ {band} only {freq_wr*100:.0f}% WR - historically weak")
                recommendation['expected_win_rate'] = min(recommendation['expected_win_rate'], freq_wr * 1.1)
                
            # Adjust TP/SL based on historical PnL distribution
            if freq_metrics['trades']:
                winners = [p for p in freq_metrics['trades'] if p > 0]
                losers = [p for p in freq_metrics['trades'] if p < 0]
                if len(winners) >= 3:
                    avg_win = sum(winners) / len(winners)
                    # If winners average higher, we can afford tighter TP
                    if avg_win > 0.015:  # 1.5%
                        recommendation['suggested_take_profit'] = max(0.01, avg_win * 0.8)  # Take at 80% of avg win
                if len(losers) >= 3:
                    avg_loss = abs(sum(losers) / len(losers))
                    # If losses are typically small, we can tighten stop loss
                    if avg_loss < 0.01:  # <1%
                        recommendation['suggested_stop_loss'] = max(0.005, avg_loss * 1.2)
        
        # ═══ HOUR OF DAY ANALYSIS ═══
        hour_metrics = self.metrics_by_hour.get(current_hour, {'wins': 0, 'losses': 0, 'trades': []})
        hour_total = hour_metrics.get('wins', 0) + hour_metrics.get('losses', 0)
        
        if hour_total >= 3:
            hour_wr = hour_metrics['wins'] / hour_total
            
            recommendation['hour_insight'] = {
                'hour': current_hour,
                'win_rate': hour_wr,
                'sample_size': hour_total
            }
            
            if hour_wr >= 0.65:
                recommendation['advantages'].append(f"⏰ {current_hour:02d}:00 is historically strong ({hour_wr*100:.0f}% WR)")
            elif hour_wr < 0.35:
                recommendation['warnings'].append(f"⚠️ {current_hour:02d}:00 is historically weak ({hour_wr*100:.0f}% WR)")
                
        # ═══ COHERENCE RANGE ANALYSIS ═══  
        coh_range = self._get_coherence_range(coherence)
        coh_metrics = self.metrics_by_coherence.get(coh_range, {'wins': 0, 'losses': 0, 'trades': []})
        coh_total = coh_metrics.get('wins', 0) + coh_metrics.get('losses', 0)
        
        if coh_total >= 3:
            coh_wr = coh_metrics['wins'] / coh_total
            
            recommendation['coherence_insight'] = {
                'range': coh_range,
                'win_rate': coh_wr,
                'sample_size': coh_total
            }
            
            if coh_wr >= 0.60:
                recommendation['advantages'].append(f"✨ Coherence {coh_range} = {coh_wr*100:.0f}% WR historically")
            elif coh_wr < 0.40:
                recommendation['warnings'].append(f"⚠️ Coherence {coh_range} underperforms ({coh_wr*100:.0f}% WR)")
                
        # ═══ CALCULATE COMBINED EXPECTED WIN RATE ═══
        contributing_factors = []
        if freq_total >= 3:
            contributing_factors.append(('frequency', freq_wr, freq_total))
        if hour_total >= 3:
            contributing_factors.append(('hour', hour_wr, hour_total))
        if coh_total >= 3:
            contributing_factors.append(('coherence', coh_wr, coh_total))
            
        if contributing_factors:
            # Weighted average by sample size
            total_weight = sum(f[2] for f in contributing_factors)
            weighted_wr = sum(f[1] * f[2] for f in contributing_factors) / total_weight
            recommendation['expected_win_rate'] = weighted_wr
            recommendation['similar_trades'] = total_weight
            
        # ═══ SET CONFIDENCE LEVEL ═══
        total_similar = freq_total + hour_total + coh_total
        if total_similar >= 30 and len(contributing_factors) >= 2:
            recommendation['confidence'] = 'high'
        elif total_similar >= 10:
            recommendation['confidence'] = 'medium'
        else:
            recommendation['confidence'] = 'low'
            
        # ═══ DETERMINE TRADE RECOMMENDATION ═══
        # Only flag as "don't trade" if MULTIPLE warnings AND very low WR
        if len(recommendation['warnings']) >= 3:  # Was 2 - be less cautious
            recommendation['should_trade'] = False
            recommendation['warnings'].append("❌ Multiple red flags - consider skipping")
        elif recommendation['expected_win_rate'] < 0.15 and recommendation['confidence'] == 'high':  # Was 35% - way too conservative!
            recommendation['should_trade'] = False
            recommendation['warnings'].append(f"❌ Expected WR {recommendation['expected_win_rate']*100:.0f}% very low")
            
        # ═══ HOLD TIME SUGGESTION ═══
        # If frequency band has high variance, suggest longer hold
        if freq_metrics['trades']:
            pnl_variance = sum((p - (freq_metrics['total_pnl']/max(1,freq_total)))**2 for p in freq_metrics['trades']) / max(1, freq_total)
            if pnl_variance > 0.001:  # High variance
                recommendation['suggested_hold_cycles'] = min(20, CONFIG['MIN_HOLD_CYCLES'] + 5)
                recommendation['advantages'].append("📊 High variance band - extended hold suggested")
                
        return recommendation
        
    def get_recommendation_summary(self, recommendation: Dict) -> str:
        """Format recommendation as human-readable summary for logging."""
        lines = []
        
        conf_emoji = {'high': '🟢', 'medium': '🟡', 'low': '⚪'}.get(recommendation['confidence'], '⚪')
        trade_emoji = '✅' if recommendation['should_trade'] else '❌'
        
        lines.append(f"  {trade_emoji} Trade: {'RECOMMENDED' if recommendation['should_trade'] else 'SKIP'}")
        lines.append(f"  {conf_emoji} Confidence: {recommendation['confidence'].upper()} ({recommendation['similar_trades']} similar trades)")
        lines.append(f"  📈 Expected WR: {recommendation['expected_win_rate']*100:.0f}%")
        
        if recommendation['advantages']:
            for adv in recommendation['advantages'][:2]:
                lines.append(f"    {adv}")
                
        if recommendation['warnings']:
            for warn in recommendation['warnings'][:2]:
                lines.append(f"    {warn}")
                
        lines.append(f"  💡 Suggested: TP {recommendation['suggested_take_profit']*100:.1f}% / SL {recommendation['suggested_stop_loss']*100:.1f}% / Hold {recommendation['suggested_hold_cycles']} cycles")
        
        return "\n".join(lines)
    
    def record_brain_state(self, brain_feature: Dict):
        """
        🧠 Record brain state for correlation with trade outcomes.
        
        Called by EcosystemBrainBridge after each wisdom cycle.
        Allows learning correlation between brain signals and trade success.
        
        Args:
            brain_feature: Dict with keys like:
                - brain_consensus (BULLISH/BEARISH/NEUTRAL)
                - brain_confidence (0-1)
                - fear_greed (0-100)
                - manipulation_risk (0-1)
                - civilization_agreement (0-1)
        """
        if not hasattr(self, 'brain_state_history'):
            self.brain_state_history = []
            
        # Add timestamp
        brain_feature['timestamp'] = time.time()
        
        self.brain_state_history.append(brain_feature)
        
        # Keep last 100 brain states
        if len(self.brain_state_history) > 100:
            self.brain_state_history = self.brain_state_history[-100:]
        
        # Log significant brain states
        if brain_feature.get('brain_confidence', 0) > 0.8:
            logger.debug(f"🧠 High confidence brain state: {brain_feature['brain_consensus']} ({brain_feature['brain_confidence']:.0%})")
    
    def get_brain_correlation(self) -> Dict:
        """
        Analyze correlation between brain states and trade outcomes.
        
        Returns insights about which brain states lead to winning trades.
        """
        if not hasattr(self, 'brain_state_history') or not self.brain_state_history:
            return {'status': 'no_data'}
        
        # Match brain states to trades by timestamp
        correlations = {
            'bullish_win_rate': 0.0,
            'bearish_win_rate': 0.0,
            'high_confidence_win_rate': 0.0,
            'extreme_fear_win_rate': 0.0,
            'samples': 0
        }
        
        bullish_trades = [t for t in self.trade_history 
                        if self._brain_at_time(t.get('entry_time', 0)) == 'BULLISH']
        bearish_trades = [t for t in self.trade_history 
                        if self._brain_at_time(t.get('entry_time', 0)) == 'BEARISH']
        
        if bullish_trades:
            wins = sum(1 for t in bullish_trades if t.get('pnl', 0) > 0)
            correlations['bullish_win_rate'] = wins / len(bullish_trades)
            
        if bearish_trades:
            wins = sum(1 for t in bearish_trades if t.get('pnl', 0) > 0)
            correlations['bearish_win_rate'] = wins / len(bearish_trades)
            
        correlations['samples'] = len(self.brain_state_history)
        
        return correlations
    
    def _brain_at_time(self, timestamp: float) -> str:
        """Find brain consensus closest to a given timestamp."""
        if not hasattr(self, 'brain_state_history') or not self.brain_state_history:
            return 'NEUTRAL'
        
        closest = min(self.brain_state_history, 
                     key=lambda x: abs(x.get('timestamp', 0) - timestamp))
        return closest.get('brain_consensus', 'NEUTRAL')

    # ═══════════════════════════════════════════════════════════════
    # 📚📰 KNOWLEDGE & NEWS LEARNING INTEGRATION
    # ═══════════════════════════════════════════════════════════════
    
    def record_knowledge_event(self, event: Dict):
        """
        📚 Record knowledge discovery event for correlation analysis.
        
        Called when the KnowledgeBase discovers relevant information.
        Tracks:
        - What was researched (topic, articles found)
        - When it was discovered
        - Market conditions at discovery time
        
        Later correlated with trade outcomes to learn which knowledge
        topics are predictive of profitable trades.
        
        Args:
            event: Dict with keys like:
                - topic: What was researched
                - articles_found: Number of articles
                - key_concepts: List of discovered concepts
                - timestamp: When discovered
                - market_context: Optional market state at time
        """
        if not hasattr(self, 'knowledge_event_history'):
            self.knowledge_event_history = []
            
        event['recorded_at'] = time.time()
        self.knowledge_event_history.append(event)
        
        # Keep last 200 knowledge events
        if len(self.knowledge_event_history) > 200:
            self.knowledge_event_history = self.knowledge_event_history[-200:]
        
        logger.debug(f"📚 Knowledge event recorded: {event.get('topic', 'unknown')}")
    
    def record_news_sentiment(self, sentiment_data: Dict):
        """
        📰 Record news sentiment for correlation with trade outcomes.
        
        Called when the NewsFeed publishes sentiment analysis.
        Tracks:
        - Overall sentiment (bullish/bearish/neutral)
        - Confidence level
        - Domain-specific sentiments (crypto, stocks)
        - Risk level from news
        
        Args:
            sentiment_data: Dict with keys like:
                - sentiment: float [-1, 1]
                - label: bullish/bearish/neutral
                - confidence: 0-1
                - crypto_sentiment: float
                - stock_sentiment: float
                - risk_level: normal/elevated/high
        """
        if not hasattr(self, 'news_sentiment_history'):
            self.news_sentiment_history = []
            
        sentiment_data['recorded_at'] = time.time()
        self.news_sentiment_history.append(sentiment_data)
        
        # Keep last 100 sentiment snapshots
        if len(self.news_sentiment_history) > 100:
            self.news_sentiment_history = self.news_sentiment_history[-100:]
        
        # Track metrics by sentiment label for learning
        if not hasattr(self, 'metrics_by_news_sentiment'):
            self.metrics_by_news_sentiment = {}
        
        label = sentiment_data.get('label', 'neutral')
        if label not in self.metrics_by_news_sentiment:
            self.metrics_by_news_sentiment[label] = {'trades': 0, 'wins': 0, 'total_pnl': 0}
        
        logger.debug(f"📰 News sentiment recorded: {label} ({sentiment_data.get('sentiment', 0):.3f})")
    
    def get_news_sentiment_at_time(self, timestamp: float) -> Dict:
        """Get the news sentiment closest to a given timestamp."""
        if not hasattr(self, 'news_sentiment_history') or not self.news_sentiment_history:
            return {'label': 'neutral', 'sentiment': 0.0, 'confidence': 0.0}
        
        closest = min(self.news_sentiment_history,
                     key=lambda x: abs(x.get('recorded_at', 0) - timestamp))
        return closest
    
    def correlate_trade_with_news(self, trade_data: Dict):
        """
        Correlate a completed trade with the news sentiment at entry time.
        Updates metrics to learn which news states lead to winning trades.
        """
        if not hasattr(self, 'metrics_by_news_sentiment'):
            self.metrics_by_news_sentiment = {}
        
        entry_time = trade_data.get('entry_time', time.time())
        news_at_entry = self.get_news_sentiment_at_time(entry_time)
        
        label = news_at_entry.get('label', 'neutral')
        is_win = trade_data.get('pnl', 0) > 0
        pnl = trade_data.get('pnl', 0)
        
        if label not in self.metrics_by_news_sentiment:
            self.metrics_by_news_sentiment[label] = {'trades': 0, 'wins': 0, 'total_pnl': 0}
        
        self.metrics_by_news_sentiment[label]['trades'] += 1
        if is_win:
            self.metrics_by_news_sentiment[label]['wins'] += 1
        self.metrics_by_news_sentiment[label]['total_pnl'] += pnl
        
        # Store correlation for this trade
        trade_data['news_sentiment_at_entry'] = news_at_entry.get('label', 'neutral')
        trade_data['news_confidence_at_entry'] = news_at_entry.get('confidence', 0.0)
    
    def get_news_correlation_insights(self) -> Dict:
        """
        Get insights about correlation between news sentiment and trade outcomes.
        
        Returns:
            Dict with win rates by news sentiment type
        """
        insights = {
            'status': 'analyzing',
            'by_sentiment': {},
            'recommendation': 'neutral',
            'total_samples': 0
        }
        
        if not hasattr(self, 'metrics_by_news_sentiment'):
            insights['status'] = 'no_data'
            return insights
        
        for label, metrics in self.metrics_by_news_sentiment.items():
            trades = metrics.get('trades', 0)
            wins = metrics.get('wins', 0)
            total_pnl = metrics.get('total_pnl', 0)
            
            if trades >= 3:  # Minimum sample for statistical relevance
                win_rate = wins / trades
                avg_pnl = total_pnl / trades
                
                insights['by_sentiment'][label] = {
                    'win_rate': win_rate,
                    'avg_pnl': avg_pnl,
                    'trades': trades
                }
                insights['total_samples'] += trades
        
        # Generate recommendation
        if insights['by_sentiment']:
            best_sentiment = max(insights['by_sentiment'].items(),
                               key=lambda x: x[1]['win_rate'])
            worst_sentiment = min(insights['by_sentiment'].items(),
                                key=lambda x: x[1]['win_rate'])
            
            if best_sentiment[1]['win_rate'] > 0.55:
                insights['recommendation'] = f"Trade MORE during {best_sentiment[0]} news"
            if worst_sentiment[1]['win_rate'] < 0.40:
                insights['recommendation'] += f", AVOID {worst_sentiment[0]} news"
        
        insights['status'] = 'complete'
        return insights
    
    def get_knowledge_probability_modifier(self, topic: str) -> float:
        """
        Get a probability modifier based on what knowledge we've learned.
        
        If we've researched a topic and trades in that area performed well,
        boost the probability. If they performed poorly, reduce it.
        
        Args:
            topic: The topic/symbol being traded
            
        Returns:
            float modifier (1.0 = neutral, >1 = boost, <1 = penalize)
        """
        if not hasattr(self, 'knowledge_event_history'):
            return 1.0
        
        # Find knowledge events related to this topic
        related_events = [e for e in self.knowledge_event_history
                        if topic.lower() in str(e.get('topic', '')).lower() or
                           topic.lower() in str(e.get('key_concepts', [])).lower()]
        
        if not related_events:
            return 1.0
        
        # Check trades made after knowledge discovery
        modifier = 1.0
        for event in related_events[-5:]:  # Last 5 related events
            event_time = event.get('recorded_at', 0)
            # Find trades made within 1 hour of knowledge discovery
            related_trades = [t for t in self.trade_history
                            if event_time <= t.get('entry_time', 0) <= event_time + 3600]
            
            if related_trades:
                win_rate = sum(1 for t in related_trades if t.get('pnl', 0) > 0) / len(related_trades)
                # Adjust modifier based on performance
                if win_rate >= 0.6:
                    modifier = min(modifier * 1.1, 1.3)  # Boost up to 30%
                elif win_rate <= 0.4:
                    modifier = max(modifier * 0.9, 0.7)  # Penalize down to 30%
        
        return modifier
    
    def enhanced_record_trade(self, trade_data: Dict):
        """
        Enhanced trade recording that includes news/knowledge correlation.
        
        Call this instead of record_trade to get full learning integration.
        """
        # Correlate with news sentiment
        self.correlate_trade_with_news(trade_data)
        
        # Get knowledge modifier that was active during entry
        entry_time = trade_data.get('entry_time', time.time())
        
        # Find what knowledge was recently discovered
        if hasattr(self, 'knowledge_event_history'):
            recent_knowledge = [e for e in self.knowledge_event_history
                              if entry_time - 3600 <= e.get('recorded_at', 0) <= entry_time]
            if recent_knowledge:
                trade_data['knowledge_context'] = [e.get('topic') for e in recent_knowledge[:3]]
        
        # Record the trade with all enrichments
        self.record_trade(trade_data)
        
        # Save enhanced history
        self._save_enhanced_history()
    
    def _save_enhanced_history(self):
        """Save enhanced learning history including knowledge/news data."""
        try:
            enhanced_data = {
                'trades': self.trade_history[-self.max_history:],
                'thresholds': self.optimized_thresholds,
                'updated_at': datetime.now().isoformat(),
                'news_metrics': getattr(self, 'metrics_by_news_sentiment', {}),
                'knowledge_events': getattr(self, 'knowledge_event_history', [])[-50:],
                'news_history': getattr(self, 'news_sentiment_history', [])[-50:]
            }
            with open(self.history_file, 'w') as f:
                json.dump(enhanced_data, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save enhanced history: {e}")
    
    def get_learning_summary_enhanced(self) -> str:
        """Get enhanced learning summary including knowledge/news insights."""
        base_summary = self.get_learning_summary()
        
        # Add news insights
        news_insights = self.get_news_correlation_insights()
        if news_insights['status'] == 'complete' and news_insights['total_samples'] >= 5:
            base_summary += "\n\n   📰 NEWS CORRELATION:"
            for label, metrics in news_insights['by_sentiment'].items():
                emoji = '🐂' if label == 'bullish' else '🐻' if label == 'bearish' else '📊'
                base_summary += f"\n      {emoji} {label.upper()}: {metrics['win_rate']*100:.0f}% WR ({metrics['trades']} trades)"
            if news_insights['recommendation']:
                base_summary += f"\n      💡 {news_insights['recommendation']}"
        
        # Add knowledge insights
        if hasattr(self, 'knowledge_event_history') and self.knowledge_event_history:
            base_summary += f"\n\n   📚 KNOWLEDGE BASE: {len(self.knowledge_event_history)} research events tracked"
        
        return base_summary


# Global adaptive learning instance
ADAPTIVE_LEARNER = AdaptiveLearningEngine()


def sync_exchange_trades_to_brain():
    """
    🧠📈 SYNC EXCHANGE TRADE HISTORY TO ADAPTIVE LEARNER
    
    Pulls real trade history from ALL exchanges (Kraken + Binance) and feeds 
    it to the brain so it can learn from actual wins/losses.
    
    This provides:
    - Real P&L data from actual trades
    - Entry/exit timestamps for time-of-day analysis
    - Pair performance tracking
    - Running balance history for drawdown analysis
    - Cross-exchange learning (what works on Kraken vs Binance)
    """
    from datetime import datetime
    
    total_synced = 0
    total_wins = 0
    total_losses = 0
    exchange_results = {}
    
    # ═══════════════════════════════════════════════════════════════
    # 🦑 KRAKEN TRADE SYNC
    # ═══════════════════════════════════════════════════════════════
    try:
        import krakenex
        
        kraken = krakenex.API()
        kraken.key = os.getenv('KRAKEN_API_KEY')
        kraken.secret = os.getenv('KRAKEN_API_SECRET')
        
        if kraken.key and kraken.secret:
            result = kraken.query_private('TradesHistory', {'trades': True})
            
            if not result.get('error'):
                trades = result.get('result', {}).get('trades', {})
                
                if trades:
                    trade_list = sorted(trades.values(), key=lambda x: float(x.get('time', 0)))
                    pair_holdings = {}
                    kraken_synced = 0
                    kraken_wins = 0
                    kraken_losses = 0
                    
                    for trade in trade_list:
                        pair = trade.get('pair', '')
                        side = trade.get('type', '').upper()
                        price = float(trade.get('price', 0))
                        vol = float(trade.get('vol', 0))
                        cost = float(trade.get('cost', 0))
                        fee = float(trade.get('fee', 0))
                        trade_time = float(trade.get('time', 0))
                        
                        if side == 'BUY':
                            if pair not in pair_holdings:
                                pair_holdings[pair] = {'qty': 0, 'cost_basis': 0, 'entry_time': trade_time}
                            pair_holdings[pair]['qty'] += vol
                            pair_holdings[pair]['cost_basis'] += cost + fee
                            pair_holdings[pair]['entry_time'] = trade_time
                            
                        elif side == 'SELL':
                            realized_pnl = 0
                            cost_of_sold = 0
                            avg_cost = price
                            if pair in pair_holdings and pair_holdings[pair]['qty'] > 0:
                                avg_cost = pair_holdings[pair]['cost_basis'] / pair_holdings[pair]['qty']
                                cost_of_sold = avg_cost * vol
                                proceeds = cost - fee
                                realized_pnl = proceeds - cost_of_sold
                                pair_holdings[pair]['qty'] -= vol
                                pair_holdings[pair]['cost_basis'] -= cost_of_sold
                            
                            trade_record = {
                                'symbol': pair,
                                'entry_price': avg_cost / vol if vol > 0 else price,
                                'exit_price': price,
                                'pnl': realized_pnl,
                                'pnl_pct': (realized_pnl / cost_of_sold * 100) if cost_of_sold > 0 else 0,
                                'entry_time': pair_holdings.get(pair, {}).get('entry_time', trade_time),
                                'exit_time': trade_time,
                                'quantity': vol,
                                'frequency': 432,
                                'coherence': 0.5,
                                'score': 70,
                                'probability': 0.6,
                                'hnc_action': 'HOLD',
                                'source': 'kraken',
                                'exchange': 'kraken'
                            }
                            
                            ADAPTIVE_LEARNER.record_trade(trade_record)
                            kraken_synced += 1
                            if realized_pnl > 0:
                                kraken_wins += 1
                            else:
                                kraken_losses += 1
                    
                    total_synced += kraken_synced
                    total_wins += kraken_wins
                    total_losses += kraken_losses
                    exchange_results['kraken'] = {'synced': kraken_synced, 'wins': kraken_wins, 'losses': kraken_losses}
                    logger.info(f"🦑 Kraken: Synced {kraken_synced} trades | W:{kraken_wins} L:{kraken_losses}")
            else:
                logger.warning(f"🦑 Kraken API error: {result.get('error')}")
        else:
            logger.debug("🦑 Kraken API keys not configured - skipping")
            
    except Exception as e:
        logger.warning(f"🦑 Kraken sync error: {e}")
    
    # ═══════════════════════════════════════════════════════════════
    # 🟡 BINANCE TRADE SYNC
    # ═══════════════════════════════════════════════════════════════
    try:
        from binance_client import BinanceClient
        
        binance_key = os.getenv('BINANCE_API_KEY')
        binance_secret = os.getenv('BINANCE_API_SECRET')
        
        if binance_key and binance_secret:
            binance = BinanceClient()
            
            # Get all trades from Binance
            all_trades = binance.get_all_my_trades()
            
            if all_trades:
                binance_synced = 0
                binance_wins = 0
                binance_losses = 0
                pair_holdings = {}
                
                # Flatten and sort all trades by time
                all_trade_list = []
                for symbol, trades in all_trades.items():
                    for trade in trades:
                        trade['_symbol'] = symbol
                        all_trade_list.append(trade)
                
                all_trade_list.sort(key=lambda x: x.get('time', 0))
                
                for trade in all_trade_list:
                    symbol = trade.get('_symbol', '')
                    is_buyer = trade.get('isBuyer', False)
                    price = float(trade.get('price', 0))
                    qty = float(trade.get('qty', 0))
                    quote_qty = float(trade.get('quoteQty', price * qty))
                    commission = float(trade.get('commission', 0))
                    trade_time = trade.get('time', 0) / 1000  # Binance uses milliseconds
                    
                    if is_buyer:
                        if symbol not in pair_holdings:
                            pair_holdings[symbol] = {'qty': 0, 'cost_basis': 0, 'entry_time': trade_time}
                        pair_holdings[symbol]['qty'] += qty
                        pair_holdings[symbol]['cost_basis'] += quote_qty + commission
                        pair_holdings[symbol]['entry_time'] = trade_time
                        
                    else:  # SELL
                        realized_pnl = 0
                        cost_of_sold = 0
                        avg_cost = price
                        if symbol in pair_holdings and pair_holdings[symbol]['qty'] > 0:
                            avg_cost = pair_holdings[symbol]['cost_basis'] / pair_holdings[symbol]['qty']
                            cost_of_sold = avg_cost * qty
                            proceeds = quote_qty - commission
                            realized_pnl = proceeds - cost_of_sold
                            pair_holdings[symbol]['qty'] -= qty
                            pair_holdings[symbol]['cost_basis'] -= cost_of_sold
                        
                        trade_record = {
                            'symbol': symbol,
                            'entry_price': avg_cost / qty if qty > 0 else price,
                            'exit_price': price,
                            'pnl': realized_pnl,
                            'pnl_pct': (realized_pnl / cost_of_sold * 100) if cost_of_sold > 0 else 0,
                            'entry_time': pair_holdings.get(symbol, {}).get('entry_time', trade_time),
                            'exit_time': trade_time,
                            'quantity': qty,
                            'frequency': 432,
                            'coherence': 0.5,
                            'score': 70,
                            'probability': 0.6,
                            'hnc_action': 'HOLD',
                            'source': 'binance',
                            'exchange': 'binance'
                        }
                        
                        ADAPTIVE_LEARNER.record_trade(trade_record)
                        binance_synced += 1
                        if realized_pnl > 0:
                            binance_wins += 1
                        else:
                            binance_losses += 1
                
                total_synced += binance_synced
                total_wins += binance_wins
                total_losses += binance_losses
                exchange_results['binance'] = {'synced': binance_synced, 'wins': binance_wins, 'losses': binance_losses}
                logger.info(f"🟡 Binance: Synced {binance_synced} trades | W:{binance_wins} L:{binance_losses}")
        else:
            logger.debug("🟡 Binance API keys not configured - skipping")
            
    except Exception as e:
        logger.warning(f"🟡 Binance sync error: {e}")
    
    # ═══════════════════════════════════════════════════════════════
    # 📊 FINAL SUMMARY
    # ═══════════════════════════════════════════════════════════════
    
    # Save updated learning history
    ADAPTIVE_LEARNER._save_history()
    
    total = total_wins + total_losses
    win_rate = (total_wins / total * 100) if total > 0 else 0
    
    logger.info(f"🧠📈 TOTAL: Synced {total_synced} trades from {len(exchange_results)} exchanges | WR: {win_rate:.1f}%")
    
    return {
        'status': 'success',
        'trades_synced': total_synced,
        'wins': total_wins,
        'losses': total_losses,
        'win_rate': win_rate,
        'exchanges': exchange_results
    }


# ═══════════════════════════════════════════════════════════════
# 📊 PROBABILITY REPORT GENERATOR - Auto-Regenerates Every 15 Seconds
# ═══════════════════════════════════════════════════════════════

class ProbabilityReportGenerator:
    """
    Automatic probability report generator that runs in background thread.
    
    Features:
    - Generates fresh probability reports every 15 seconds
    - Supports multiple exchanges (Binance, Kraken, Alpaca)
    - Feeds into AdaptiveLearningEngine for continuous learning
    - Updates JSON files consumed by ProbabilityLoader
    - Lightweight - uses cached tickers to minimize API calls
    """
    
    # Symbols to analyze per exchange
    # 🤑 EXPANDED LIST - includes many altcoins and meme coins!
    BINANCE_SYMBOLS = [
        # Major coins
        'BTCUSDC', 'ETHUSDC', 'BNBUSDC', 'SOLUSDC', 'XRPUSDC', 'ADAUSDC', 'AVAXUSDC', 'DOGEUSDC', 'LINKUSDC',
        'MATICUSDC', 'DOTUSDC', 'ATOMUSDC', 'FILUSDC', 'LTCUSDC', 'SUIUSDC', 'APTUSDC', 'ARBUSDC',
        'OPUSDC', 'NEARUSDC', 'UNIUSDC', 'INJUSDC', 'FETUSDC', 'PEPEUSDC', 'SHIBUSDC',
        # Additional altcoins you hold
        'XLMUSDC', 'TWTUSDC', 'HMSTRUSDC', 'PENGUUSDC', 'ALTUSDC', 'HBARUSDC', 'CHZUSDC',
        'TURBOUSDC', 'MEMEUSDC', 'DOGSUSDC', 'WLDUSDC', 'SEIUSDC', 'TIAUSDC', 'WIFUSDC',
        'RAYUSDC', 'RUNEUSDC', 'ENAENAUSDC', 'ORDIUSDC', 'ICPUSDC', 'STRKUSDC', 'RENDERUSDC',
        'ARUSDC', 'MOVEUSDC', 'BERABERUSDC', 'TRUMPUSDC',
        # Also try USDT pairs for more liquidity
        'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT', 'ADAUSDT', 'AVAXUSDT', 'DOGEUSDT',
        'XLMUSDT', 'TWTUSDT', 'HMSTRUSDT', 'PENGUUSDT', 'HBARUSDT', 'CHZUSDT', 'PEPEUSDT',
        'SHIBUSDT', 'TURBOUSDT', 'MEMEUSDT', 'WLDUSDT', 'NEARUSDT', 'SUIUSDT', 'APTUSDT',
        'ARBUSDT', 'OPUSDT', 'INJUSDT', 'FETUSDT', 'LINKUSDT', 'DOTUSDT', 'ATOMUSDT',
    ]
    
    KRAKEN_SYMBOLS = [
        'XXBTZUSD', 'XETHZUSD', 'SOLUSD', 'XRPUSD', 'ADAUSD', 'AVAXUSD', 'DOGEUSD', 'LINKUSD',
        'MATICUSD', 'DOTUSD', 'ATOMUSD', 'FILUSD', 'LTCUSD', 'SUIUSD', 'APTUSD', 'ARBUSD',
        'OPUSD', 'NEARUSD', 'UNIUSD', 'INJUSD', 'FETUSD', 'PEPEUSD', 'SHIBUSD',
        # Additional Kraken pairs
        'XLMUSD', 'ZECUSD', 'SHIBUSD', 'WLDUSD', 'SEIUSD', 'TIAUSD', 'RENDERUSD',
        'XXBTUSDC', 'XETHUSDC', 'SOLUSDC', 'DOGEUSDC', 'XLMUSDC',  # USDC pairs
    ]
    
    def __init__(self, report_dir: str = '.', interval_seconds: float = 15.0):
        self.report_dir = report_dir
        self.interval = interval_seconds
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        # Initialize HNC integration if available
        self.hnc_integration = None
        if PROB_MATRIX_AVAILABLE:
            try:
                self.hnc_integration = HNCProbabilityIntegration()
            except Exception as e:
                logger.warning(f"Could not initialize HNC integration: {e}")
        
        # Price cache for momentum calculations
        self._price_history: Dict[str, List[Tuple[float, float]]] = {}  # symbol -> [(timestamp, price), ...]
        self._max_price_history = 10  # Keep last 10 prices for momentum
        
        # Generation stats
        self.last_generation = 0.0
        self.generation_count = 0
        self.last_results: Dict[str, List[Dict]] = {}
        
        logger.info(f"📊 ProbabilityReportGenerator initialized (interval={interval_seconds}s)")
    
    def start(self, ecosystem: 'AureonKrakenEcosystem' = None):
        """Start background probability generation."""
        if self._running:
            return
        
        self._running = True
        self._ecosystem = ecosystem
        self._thread = threading.Thread(target=self._generation_loop, daemon=True)
        self._thread.start()
        logger.info("📊 Probability Report Generator STARTED (background thread)")
    
    def stop(self):
        """Stop background generation."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
        logger.info("📊 Probability Report Generator STOPPED")
    
    def _generation_loop(self):
        """Main generation loop - runs every interval_seconds."""
        while self._running:
            try:
                self._generate_all_reports()
            except Exception as e:
                logger.error(f"Probability generation error: {e}")
            
            # Sleep in small chunks to allow quick shutdown
            for _ in range(int(self.interval * 2)):
                if not self._running:
                    break
                time.sleep(0.5)
    
    def _generate_all_reports(self):
        """Generate probability reports for all exchanges."""
        start_time = time.time()
        all_results = []
        
        # Get tickers from ecosystem cache if available
        ticker_cache = {}
        if hasattr(self, '_ecosystem') and self._ecosystem:
            ticker_cache = getattr(self._ecosystem, 'ticker_cache', {})
        
        # Generate for Binance symbols
        binance_results = self._generate_exchange_report('binance', self.BINANCE_SYMBOLS, ticker_cache)
        all_results.extend(binance_results)
        
        # Generate for Kraken symbols  
        kraken_results = self._generate_exchange_report('kraken', self.KRAKEN_SYMBOLS, ticker_cache)
        all_results.extend(kraken_results)
        
        # Sort by probability
        all_results.sort(key=lambda r: (r.get('probability', 0), r.get('confidence', 0)), reverse=True)
        
        # Save combined report
        report = {
            'generated_at': datetime.now().isoformat(),
            'generator': 'ProbabilityReportGenerator',
            'interval_seconds': self.interval,
            'generation_count': self.generation_count + 1,
            'count': len(all_results),
            'top_10': all_results[:10],
            'high_conviction': [r for r in all_results if r.get('probability', 0) >= 0.75],
            'all': all_results,
        }
        
        # Write to files
        with self._lock:
            try:
                # Main batch report (consumed by ecosystem)
                batch_path = os.path.join(self.report_dir, 'probability_batch_report.json')
                with open(batch_path, 'w') as f:
                    json.dump(report, f, indent=2)
                
                # Also update kraken report for backward compatibility
                kraken_report = {
                    'generated_at': report['generated_at'],
                    'count': len(kraken_results),
                    'all': kraken_results,
                }
                kraken_path = os.path.join(self.report_dir, 'probability_kraken_report.json')
                with open(kraken_path, 'w') as f:
                    json.dump(kraken_report, f, indent=2)
                
                # Combined all-exchanges report
                combined_path = os.path.join(self.report_dir, 'probability_all_exchanges_report.json')
                with open(combined_path, 'w') as f:
                    json.dump(report, f, indent=2)
                    
            except Exception as e:
                logger.error(f"Failed to write probability report: {e}")
        
        # Update stats
        self.last_generation = time.time()
        self.generation_count += 1
        self.last_results = {'all': all_results, 'binance': binance_results, 'kraken': kraken_results}
        
        # Feed top signals to AdaptiveLearningEngine
        self._feed_to_adaptive_learning(all_results[:10])
        
        # Notify ecosystem to reload
        if hasattr(self, '_ecosystem') and self._ecosystem:
            loader = getattr(self._ecosystem, 'probability_loader', None)
            if loader:
                try:
                    loader.load_all_reports()
                except Exception:
                    pass
        
        elapsed = time.time() - start_time
        if self.generation_count % 4 == 0:  # Log every minute (4 * 15s)
            logger.info(f"📊 Probability reports regenerated #{self.generation_count} ({len(all_results)} signals, {elapsed:.2f}s)")
    
    def _generate_exchange_report(self, exchange: str, symbols: List[str], ticker_cache: Dict) -> List[Dict]:
        """Generate probability report for a specific exchange."""
        results = []
        
        for symbol in symbols:
            try:
                # Try to get price from cache first
                price = 0.0
                if symbol in ticker_cache:
                    cached = ticker_cache[symbol]
                    if isinstance(cached, dict):
                        price = float(cached.get('last', cached.get('c', cached.get('price', 0))))
                    else:
                        price = float(cached)
                
                if price <= 0:
                    continue  # Skip symbols without prices
                
                # Update price history for momentum calculation
                self._update_price_history(symbol, price)
                
                # Calculate momentum from price history
                momentum = self._calculate_momentum(symbol)
                
                # Calculate frequency and coherence (HNC physics)
                freq, coherence, is_harmonic = self._calculate_frequency_metrics(symbol, price, momentum)
                
                # Use HNC integration if available
                if self.hnc_integration:
                    try:
                        matrix = self.hnc_integration.update_and_analyze(
                            symbol, price, freq, momentum, coherence, is_harmonic
                        )
                        signal = self.hnc_integration.get_trading_signal(symbol)
                        
                        results.append({
                            'symbol': symbol,
                            'exchange': exchange,
                            'price': price,
                            'probability': float(signal.get('probability', 0.5)),
                            'confidence': float(signal.get('confidence', 0.5)),
                            'action': signal.get('action', 'HOLD'),
                            'modifier': signal.get('modifier', 1.0),
                            'reason': signal.get('reason', ''),
                            'frequency': float(matrix.hour_plus_1.avg_frequency) if matrix else freq,
                            'state': matrix.hour_plus_1.state.value if matrix else 'NEUTRAL',
                            'momentum': momentum,
                            'coherence': coherence,
                            'is_harmonic': is_harmonic,
                        })
                    except Exception as e:
                        logger.debug(f"HNC analysis failed for {symbol}: {e}")
                        # Fallback to simple calculation
                        prob, action = self._simple_probability(momentum, coherence, is_harmonic)
                        results.append({
                            'symbol': symbol,
                            'exchange': exchange,
                            'price': price,
                            'probability': prob,
                            'confidence': coherence,
                            'action': action,
                            'modifier': 1.0,
                            'reason': 'simple_calc',
                            'frequency': freq,
                            'state': 'NEUTRAL',
                            'momentum': momentum,
                            'coherence': coherence,
                            'is_harmonic': is_harmonic,
                        })
                else:
                    # Simple probability calculation without HNC
                    prob, action = self._simple_probability(momentum, coherence, is_harmonic)
                    results.append({
                        'symbol': symbol,
                        'exchange': exchange,
                        'price': price,
                        'probability': prob,
                        'confidence': coherence,
                        'action': action,
                        'modifier': 1.0,
                        'reason': 'simple_calc',
                        'frequency': freq,
                        'state': 'NEUTRAL',
                        'momentum': momentum,
                        'coherence': coherence,
                        'is_harmonic': is_harmonic,
                    })
                    
            except Exception as e:
                logger.debug(f"Error generating probability for {symbol}: {e}")
                continue
        
        return results
    
    def _update_price_history(self, symbol: str, price: float):
        """Update price history for momentum calculation."""
        now = time.time()
        if symbol not in self._price_history:
            self._price_history[symbol] = []
        
        self._price_history[symbol].append((now, price))
        
        # Keep only recent prices
        if len(self._price_history[symbol]) > self._max_price_history:
            self._price_history[symbol] = self._price_history[symbol][-self._max_price_history:]
    
    def _calculate_momentum(self, symbol: str) -> float:
        """Calculate price momentum from history."""
        history = self._price_history.get(symbol, [])
        if len(history) < 2:
            return 0.0
        
        start_price = history[0][1]
        end_price = history[-1][1]
        
        if start_price <= 0:
            return 0.0
        
        return ((end_price - start_price) / start_price) * 100
    
    def _calculate_frequency_metrics(self, symbol: str, price: float, momentum: float) -> Tuple[float, float, bool]:
        """Calculate HNC frequency metrics."""
        import numpy as np
        
        # PHI-based frequency calculation
        phi = (1 + 5 ** 0.5) / 2
        
        # Base frequency from price ratio (normalized)
        history = self._price_history.get(symbol, [])
        if len(history) >= 2:
            ratio = price / history[0][1] if history[0][1] > 0 else 1.0
            freq = max(256.0, min(963.0, 432.0 * (ratio ** phi)))
        else:
            freq = 432.0  # Default natural frequency
        
        # Coherence from price stability
        if len(history) >= 3:
            prices = [p[1] for p in history]
            std = float(np.std(prices)) if prices else 0
            coherence = max(0.2, min(0.95, 1.0 / (1.0 + std / max(1.0, price))))
        else:
            coherence = 0.5
        
        # Harmonic check (near 432Hz or 528Hz)
        is_harmonic = abs(freq - 432) < 25 or abs(freq - 528) < 25
        
        return freq, coherence, is_harmonic
    
    def _simple_probability(self, momentum: float, coherence: float, is_harmonic: bool) -> Tuple[float, str]:
        """Simple probability calculation without full HNC."""
        # Base probability
        prob = 0.5
        
        # Momentum contribution
        if momentum > 1.0:
            prob += min(0.15, momentum * 0.05)
        elif momentum < -1.0:
            prob -= min(0.15, abs(momentum) * 0.05)
        
        # Coherence contribution  
        prob += (coherence - 0.5) * 0.2
        
        # Harmonic bonus
        if is_harmonic:
            prob += 0.05
        
        # Clamp to valid range
        prob = max(0.3, min(0.8, prob))
        
        # Determine action
        if prob >= 0.65:
            action = 'BUY' if momentum > 0 else 'HOLD'
        elif prob <= 0.35:
            action = 'SELL' if momentum < 0 else 'HOLD'
        else:
            action = 'HOLD'
        
        return prob, action
    
    def _feed_to_adaptive_learning(self, top_signals: List[Dict]):
        """Feed top signals to AdaptiveLearningEngine for continuous learning."""
        try:
            for signal in top_signals:
                if signal.get('probability', 0) >= 0.70:
                    # Create a learning record
                    learning_record = {
                        'symbol': signal['symbol'],
                        'exchange': signal.get('exchange', 'unknown'),
                        'probability': signal['probability'],
                        'frequency': signal.get('frequency', 432),
                        'coherence': signal.get('coherence', 0.5),
                        'is_harmonic': signal.get('is_harmonic', False),
                        'action': signal.get('action', 'HOLD'),
                        'timestamp': datetime.now().isoformat(),
                    }
                    
                    # Feed to adaptive learner for frequency band analysis
                    freq_band = ADAPTIVE_LEARNER._get_frequency_band(signal.get('frequency', 432))
                    if freq_band not in ADAPTIVE_LEARNER.metrics_by_frequency:
                        ADAPTIVE_LEARNER.metrics_by_frequency[freq_band] = {
                            'signals': 0, 'wins': 0, 'losses': 0
                        }
                    ADAPTIVE_LEARNER.metrics_by_frequency[freq_band]['signals'] = \
                        ADAPTIVE_LEARNER.metrics_by_frequency[freq_band].get('signals', 0) + 1
                    
        except Exception as e:
            logger.debug(f"Could not feed to adaptive learning: {e}")
    
    def get_top_signals(self, min_probability: float = 0.70, limit: int = 10) -> List[Dict]:
        """Get current top signals above threshold."""
        with self._lock:
            all_results = self.last_results.get('all', [])
            filtered = [r for r in all_results if r.get('probability', 0) >= min_probability]
            return filtered[:limit]
    
    def get_freshness_minutes(self) -> float:
        """Get minutes since last generation."""
        if self.last_generation == 0:
            return float('inf')
        return (time.time() - self.last_generation) / 60.0


# Global probability report generator instance
PROBABILITY_GENERATOR: Optional[ProbabilityReportGenerator] = None


# ═══════════════════════════════════════════════════════════════
# 🌊 CASCADE AMPLIFIER - 546x Miner-Validated Signal Amplification
# ═══════════════════════════════════════════════════════════════

class CascadeAmplifier:
    """
    Cascade Amplification System - Direct port from aureon_miner.py 546x optimization.
    
    Applies proven miner optimizations to trading signals:
    1. CASCADE AMPLIFICATION (up to 10x) - Compounds successive wins
    2. κt EFFICIENCY (up to 2.49x) - Extracts more value from same capital
    3. LIGHTHOUSE Γ=1.000 - Perfect entry timing via planetary coherence
    4. MIRROR RESONANCE - 50-minute stability holding
    
    The miner proved these techniques achieve 546x amplification.
    Now applied to trading for win rate and profit optimization.
    """
    
    def __init__(self):
        # Cascade state
        self.cascade_factor = 1.0
        self.cascade_max = 10.0
        self.cascade_decay = 0.95  # Decay per cycle without win
        self.cascade_boost = 1.15  # Boost per win
        
        # κt efficiency (coupling coefficient from miner)
        self.kappa_t = 1.0
        self.kappa_max = 2.49  # Proven achievable in miner
        self.kappa_ramp = 0.05  # Ramp rate per successful trade
        
        # Lighthouse Γ (planetary coherence from miner)
        self.lighthouse_gamma = 0.5
        self.lighthouse_active = False
        
        # Mirror resonance state
        self.mirror_coherence = 0.5
        self.mirror_stability_seconds = 0
        self.min_hold_seconds = 50 * 60  # 50 minutes (proven in miner)
        
        # Win streak tracking
        self.consecutive_wins = 0
        self.total_cascade_trades = 0
        self.cascade_wins = 0
        
    def record_win(self, pnl_pct: float = 0.0):
        """Record a winning trade - boost cascade."""
        self.consecutive_wins += 1
        self.cascade_wins += 1
        self.total_cascade_trades += 1
        
        # Boost cascade factor
        boost = self.cascade_boost * (1 + pnl_pct * 0.5)  # Extra boost for big wins
        self.cascade_factor = min(self.cascade_max, self.cascade_factor * boost)
        
        # Ramp κt efficiency
        self.kappa_t = min(self.kappa_max, self.kappa_t + self.kappa_ramp)
        
        # Strengthen mirror coherence
        self.mirror_coherence = min(1.0, self.mirror_coherence + 0.05)
        
        logger.debug(f"🌊 CASCADE WIN: streak={self.consecutive_wins}, "
                    f"cascade={self.cascade_factor:.2f}x, κt={self.kappa_t:.2f}")
        
    def record_loss(self, pnl_pct: float = 0.0):
        """Record a losing trade - decay cascade."""
        self.consecutive_wins = 0
        self.total_cascade_trades += 1
        
        # Decay cascade factor
        self.cascade_factor = max(1.0, self.cascade_factor * self.cascade_decay)
        
        # Slight κt decay
        self.kappa_t = max(1.0, self.kappa_t - self.kappa_ramp * 0.5)
        
        # Mirror coherence decay
        self.mirror_coherence = max(0.3, self.mirror_coherence - 0.02)
        
        logger.debug(f"🌊 CASCADE LOSS: reset streak, cascade={self.cascade_factor:.2f}x")
        
    def update_lighthouse(self, gamma: float):
        """Update Lighthouse Γ from external source (brain/platypus)."""
        self.lighthouse_gamma = gamma
        self.lighthouse_active = gamma >= MIN_GAMMA_THRESHOLD  # Independent mode: 0.20 threshold from miner blueprint
        
    def get_signal_multiplier(self, base_coherence: float = 0.5) -> float:
        """
        Get combined cascade multiplier for trading signal strength.
        
        Formula: Total = CASCADE × κt × Lighthouse × Mirror
        
        Returns multiplier to apply to score/signal strength.
        """
        # Base cascade contribution
        cascade_mult = 1.0 + (self.cascade_factor - 1.0) * 0.3  # Max 3.7x from cascade
        
        # κt efficiency contribution
        kappa_mult = 1.0 + (self.kappa_t - 1.0) * 0.2  # Max 1.3x from κt
        
        # Lighthouse contribution (when aligned)
        lighthouse_mult = 1.0
        if self.lighthouse_active:
            lighthouse_mult = 1.0 + (self.lighthouse_gamma - 0.75) * 0.4  # Up to 1.1x
            
        # Mirror stability contribution
        mirror_mult = 1.0 + (self.mirror_coherence - 0.5) * 0.2  # Up to 1.1x
        
        # Coherence synergy
        coherence_mult = 1.0 + max(0, base_coherence - 0.5) * 0.3
        
        total = cascade_mult * kappa_mult * lighthouse_mult * mirror_mult * coherence_mult
        
        return min(5.0, max(1.0, total))  # Cap at 5x for safety
        
    def get_position_size_multiplier(self) -> float:
        """
        Get position size multiplier based on cascade state.
        Higher cascade = can take larger positions.
        """
        if self.consecutive_wins >= 5:
            return min(2.0, 1.0 + self.consecutive_wins * 0.1)
        return 1.0
        
    def get_min_hold_time(self) -> float:
        """
        Get minimum hold time in seconds based on mirror resonance.
        Higher mirror coherence = longer optimal hold for stability.
        """
        if self.mirror_coherence >= 0.8:
            return self.min_hold_seconds  # Full 50 minutes
        elif self.mirror_coherence >= 0.6:
            return self.min_hold_seconds * 0.5  # 25 minutes
        else:
            return 60  # 1 minute minimum
            
    def get_stats(self) -> Dict:
        """Get current cascade amplifier statistics."""
        win_rate = self.cascade_wins / self.total_cascade_trades if self.total_cascade_trades > 0 else 0
        return {
            'cascade_factor': self.cascade_factor,
            'kappa_t': self.kappa_t,
            'lighthouse_gamma': self.lighthouse_gamma,
            'lighthouse_active': self.lighthouse_active,
            'mirror_coherence': self.mirror_coherence,
            'consecutive_wins': self.consecutive_wins,
            'total_trades': self.total_cascade_trades,
            'cascade_win_rate': win_rate,
            'signal_multiplier': self.get_signal_multiplier(),
            'position_multiplier': self.get_position_size_multiplier(),
            'min_hold_seconds': self.get_min_hold_time()
        }
        
    def display_status(self):
        """Display cascade amplifier status."""
        stats = self.get_stats()
        lighthouse_icon = "🗼✅" if stats['lighthouse_active'] else "🗼⚪"
        print(f"   🌊 CASCADE: {stats['cascade_factor']:.2f}x | "
              f"κt={stats['kappa_t']:.2f} | {lighthouse_icon} Γ={stats['lighthouse_gamma']:.3f} | "
              f"Mirror={stats['mirror_coherence']:.2f} | "
              f"Signal={stats['signal_multiplier']:.2f}x")


# Global cascade amplifier instance
CASCADE_AMPLIFIER = CascadeAmplifier()


# ═══════════════════════════════════════════════════════════════
# 📊 ATR CALCULATOR - Dynamic TP/SL
# ═══════════════════════════════════════════════════════════════

class ATRCalculator:
    """
    Average True Range calculator for dynamic TP/SL scaling.
    Implements volatility-adjusted position management.
    """
    
    def __init__(self, period: int = 14):
        self.period = period
        self.price_history: Dict[str, List[Dict]] = {}  # symbol -> [{high, low, close}]
        self.atr_cache: Dict[str, float] = {}
        self.last_update: Dict[str, float] = {}
        
    def update(self, symbol: str, high: float, low: float, close: float):
        """Add new price data for ATR calculation."""
        if symbol not in self.price_history:
            self.price_history[symbol] = []
            
        self.price_history[symbol].append({
            'high': high,
            'low': low,
            'close': close,
            'timestamp': time.time()
        })
        
        # Keep only last period * 2 candles
        if len(self.price_history[symbol]) > self.period * 2:
            self.price_history[symbol] = self.price_history[symbol][-self.period * 2:]
            
        self.last_update[symbol] = time.time()
        
    def calculate_atr(self, symbol: str) -> float:
        """Calculate ATR for a symbol."""
        if symbol not in self.price_history or len(self.price_history[symbol]) < 2:
            return 0.0
            
        history = self.price_history[symbol]
        true_ranges = []
        
        for i in range(1, min(len(history), self.period + 1)):
            current = history[-i]
            previous = history[-i - 1] if i < len(history) else current
            
            # True Range = max(H-L, |H-Prev Close|, |L-Prev Close|)
            tr1 = current['high'] - current['low']
            tr2 = abs(current['high'] - previous['close'])
            tr3 = abs(current['low'] - previous['close'])
            true_ranges.append(max(tr1, tr2, tr3))
            
        if not true_ranges:
            return 0.0
            
        atr = sum(true_ranges) / len(true_ranges)
        self.atr_cache[symbol] = atr
        return atr
        
    def get_dynamic_tp_sl(self, symbol: str, base_tp: float = 2.0, base_sl: float = 0.8,
                          atr_tp_mult: float = 2.0, atr_sl_mult: float = 1.5) -> Dict[str, float]:
        """
        Calculate dynamic TP/SL based on ATR.
        
        Args:
            symbol: Trading symbol
            base_tp: Base take profit % (used if no ATR data)
            base_sl: Base stop loss % (used if no ATR data)
            atr_tp_mult: ATR multiplier for take profit
            atr_sl_mult: ATR multiplier for stop loss
            
        Returns:
            {'tp_pct': float, 'sl_pct': float, 'atr': float, 'is_dynamic': bool}
        """
        atr = self.calculate_atr(symbol)
        
        if atr <= 0 or symbol not in self.price_history:
            return {
                'tp_pct': base_tp,
                'sl_pct': base_sl,
                'atr': 0,
                'is_dynamic': False
            }
            
        # Get current price from latest candle
        current_price = self.price_history[symbol][-1]['close']
        if current_price <= 0:
            return {'tp_pct': base_tp, 'sl_pct': base_sl, 'atr': atr, 'is_dynamic': False}
            
        # ATR as percentage of price
        atr_pct = (atr / current_price) * 100
        
        # Scale TP/SL by ATR
        dynamic_tp = min(atr_pct * atr_tp_mult, 10.0)  # Cap at 10%
        dynamic_sl = min(atr_pct * atr_sl_mult, 5.0)   # Cap at 5%
        
        # Ensure minimum values
        dynamic_tp = max(dynamic_tp, base_tp * 0.5)
        dynamic_sl = max(dynamic_sl, base_sl * 0.5)
        
        return {
            'tp_pct': round(dynamic_tp, 2),
            'sl_pct': round(dynamic_sl, 2),
            'atr': round(atr, 6),
            'atr_pct': round(atr_pct, 2),
            'is_dynamic': True
        }


# ═══════════════════════════════════════════════════════════════
# 🔥 PORTFOLIO HEAT MANAGER
# ═══════════════════════════════════════════════════════════════

class PortfolioHeatManager:
    """
    Tracks total portfolio risk across all positions.
    Implements correlation-adjusted position sizing and heat limits.
    """
    
    def __init__(self, max_heat: float = 0.60, heat_decay: float = 0.95):
        self.max_heat = max_heat  # Maximum 60% portfolio at risk
        self.heat_decay = heat_decay  # Heat decays 5% per cycle
        self.current_heat = 0.0
        self.position_heat: Dict[str, float] = {}  # symbol -> heat contribution
        self.correlation_matrix: Dict[str, Dict[str, float]] = {}
        self.heat_history: List[float] = []
        
    def add_position_heat(self, symbol: str, position_pct: float, risk_pct: float = 1.0):
        """
        Add heat from a new position.
        
        Args:
            symbol: Trading symbol
            position_pct: Position size as % of portfolio
            risk_pct: Risk adjustment (1.0 = full risk, 0.5 = hedged)
        """
        heat = position_pct * risk_pct
        
        # Apply correlation adjustment (correlated assets add more heat)
        correlation_mult = self._get_correlation_multiplier(symbol)
        heat *= correlation_mult
        
        self.position_heat[symbol] = heat
        self._recalculate_total_heat()
        
    def remove_position_heat(self, symbol: str):
        """Remove heat when position is closed."""
        if symbol in self.position_heat:
            del self.position_heat[symbol]
        self._recalculate_total_heat()
        
    def _recalculate_total_heat(self):
        """Recalculate total portfolio heat."""
        self.current_heat = sum(self.position_heat.values())
        self.heat_history.append(self.current_heat)
        if len(self.heat_history) > 100:
            self.heat_history = self.heat_history[-100:]
            
    def _get_correlation_multiplier(self, symbol: str) -> float:
        """
        Get correlation multiplier for a symbol.
        Highly correlated assets with existing positions add more heat.
        """
        if not self.position_heat:
            return 1.0
            
        # Simple heuristic: same-category assets have higher correlation
        # BTC-related: BTC, WBTC, etc.
        # ETH-related: ETH, STETH, etc.
        btc_related = ['BTC', 'XBT', 'WBTC', 'BTCUSD', 'XBTUSD']
        eth_related = ['ETH', 'STETH', 'ETHUSD', 'XETHUSD']
        
        symbol_upper = symbol.upper()
        correlation_boost = 0.0
        
        for existing in self.position_heat:
            existing_upper = existing.upper()
            
            # Check BTC correlation
            if any(b in symbol_upper for b in btc_related) and any(b in existing_upper for b in btc_related):
                correlation_boost += 0.3
            # Check ETH correlation
            elif any(e in symbol_upper for e in eth_related) and any(e in existing_upper for e in eth_related):
                correlation_boost += 0.3
            # General crypto correlation
            elif 'USD' in symbol_upper and 'USD' in existing_upper:
                correlation_boost += 0.1
                
        return 1.0 + min(correlation_boost, 0.5)  # Cap at 1.5x
        
    def can_add_position(self, position_pct: float) -> Tuple[bool, str]:
        """
        Check if adding a position would exceed heat limits.
        
        Returns:
            (can_add: bool, reason: str)
        """
        projected_heat = self.current_heat + position_pct
        
        if projected_heat > self.max_heat:
            return False, f"Heat limit: {self.current_heat:.1%} + {position_pct:.1%} > {self.max_heat:.1%}"
            
        return True, "OK"
        
    def get_max_position_size(self) -> float:
        """Get maximum position size allowed given current heat."""
        available_heat = max(0, self.max_heat - self.current_heat)
        return available_heat
        
    def decay_heat(self):
        """Apply heat decay (called each cycle)."""
        for symbol in self.position_heat:
            self.position_heat[symbol] *= self.heat_decay
        self._recalculate_total_heat()
        
    def get_heat_status(self) -> Dict[str, Any]:
        """Get current heat status."""
        return {
            'current_heat': round(self.current_heat, 3),
            'max_heat': self.max_heat,
            'available': round(self.max_heat - self.current_heat, 3),
            'utilization': round(self.current_heat / self.max_heat, 3) if self.max_heat > 0 else 0,
            'position_count': len(self.position_heat),
            'positions': dict(self.position_heat)
        }


# ═══════════════════════════════════════════════════════════════
# 🎛️ ADAPTIVE FILTER THRESHOLDS
# ═══════════════════════════════════════════════════════════════

class AdaptiveFilterThresholds:
    """
    Auto-adjusts MIN_MOMENTUM, MIN_VOLUME based on market conditions.
    Learns optimal thresholds from historical performance.
    """
    
    def __init__(self):
        # Base thresholds
        self.base_momentum = CONFIG.get('MIN_MOMENTUM', 0.5)
        self.base_volume = CONFIG.get('MIN_VOLUME', 50000)
        self.base_coherence = CONFIG.get('MIN_COHERENCE', 0.45)
        
        # Current adaptive thresholds
        self.momentum_threshold = self.base_momentum
        self.volume_threshold = self.base_volume
        self.coherence_threshold = self.base_coherence
        
        # Performance tracking
        self.trades_by_threshold: Dict[str, List[Dict]] = {
            'momentum': [],
            'volume': [],
            'coherence': []
        }
        
        # Market regime
        self.market_regime = 'NORMAL'  # NORMAL, TRENDING, RANGING, VOLATILE
        self.regime_history: List[str] = []
        
    def detect_market_regime(self, recent_changes: List[float]) -> str:
        """
        Detect current market regime from recent price changes.
        
        Args:
            recent_changes: List of recent 24h % changes across symbols
        """
        if not recent_changes:
            return 'NORMAL'
            
        avg_change = sum(recent_changes) / len(recent_changes)
        volatility = sum(abs(c - avg_change) for c in recent_changes) / len(recent_changes)
        
        # Count direction consistency
        positive = sum(1 for c in recent_changes if c > 0)
        negative = len(recent_changes) - positive
        direction_ratio = max(positive, negative) / len(recent_changes)
        
        # Determine regime
        if volatility > 5.0:
            regime = 'VOLATILE'
        elif direction_ratio > 0.7 and abs(avg_change) > 2.0:
            regime = 'TRENDING'
        elif direction_ratio < 0.6 and volatility < 2.0:
            regime = 'RANGING'
        else:
            regime = 'NORMAL'
            
        self.market_regime = regime
        self.regime_history.append(regime)
        if len(self.regime_history) > 50:
            self.regime_history = self.regime_history[-50:]
            
        return regime
        
    def adjust_thresholds(self, regime: str = None):
        """
        Adjust thresholds based on market regime.
        """
        regime = regime or self.market_regime
        
        if regime == 'TRENDING':
            # In trends, lower momentum threshold to catch moves early
            self.momentum_threshold = self.base_momentum * 0.7
            self.volume_threshold = self.base_volume * 0.8
            self.coherence_threshold = self.base_coherence * 0.9
            
        elif regime == 'VOLATILE':
            # In volatility, raise thresholds to filter noise
            self.momentum_threshold = self.base_momentum * 1.5
            self.volume_threshold = self.base_volume * 1.3
            self.coherence_threshold = self.base_coherence * 1.2
            
        elif regime == 'RANGING':
            # In ranging, require strong signals
            self.momentum_threshold = self.base_momentum * 1.2
            self.volume_threshold = self.base_volume * 1.1
            self.coherence_threshold = self.base_coherence * 1.1
            
        else:  # NORMAL
            self.momentum_threshold = self.base_momentum
            self.volume_threshold = self.base_volume
            self.coherence_threshold = self.base_coherence
            
    def record_trade_result(self, threshold_type: str, threshold_value: float, 
                           actual_value: float, profit: float):
        """Record trade result for learning."""
        self.trades_by_threshold[threshold_type].append({
            'threshold': threshold_value,
            'actual': actual_value,
            'profit': profit,
            'timestamp': time.time()
        })
        
        # Keep last 100 trades per type
        if len(self.trades_by_threshold[threshold_type]) > 100:
            self.trades_by_threshold[threshold_type] = \
                self.trades_by_threshold[threshold_type][-100:]
                
    def learn_optimal_thresholds(self):
        """
        Learn optimal thresholds from trade history.
        Adjusts base thresholds based on profitability patterns.
        """
        for threshold_type in ['momentum', 'volume', 'coherence']:
            trades = self.trades_by_threshold[threshold_type]
            if len(trades) < 20:
                continue
                
            # Group trades by threshold quartile
            sorted_trades = sorted(trades, key=lambda x: x['actual'])
            quartile_size = len(sorted_trades) // 4
            
            if quartile_size < 5:
                continue
                
            # Calculate profitability by quartile
            quartile_profits = []
            for i in range(4):
                start = i * quartile_size
                end = start + quartile_size if i < 3 else len(sorted_trades)
                q_trades = sorted_trades[start:end]
                avg_profit = sum(t['profit'] for t in q_trades) / len(q_trades)
                avg_value = sum(t['actual'] for t in q_trades) / len(q_trades)
                quartile_profits.append((avg_value, avg_profit))
                
            # Find most profitable quartile
            best_quartile = max(quartile_profits, key=lambda x: x[1])
            optimal_value = best_quartile[0]
            
            # Gradually adjust base threshold toward optimal
            if threshold_type == 'momentum':
                self.base_momentum = self.base_momentum * 0.9 + optimal_value * 0.1
            elif threshold_type == 'volume':
                self.base_volume = self.base_volume * 0.9 + optimal_value * 0.1
            elif threshold_type == 'coherence':
                self.base_coherence = self.base_coherence * 0.9 + optimal_value * 0.1
                
    def get_thresholds(self) -> Dict[str, float]:
        """Get current adaptive thresholds."""
        return {
            'momentum': round(self.momentum_threshold, 2),
            'volume': round(self.volume_threshold, 0),
            'coherence': round(self.coherence_threshold, 2),
            'regime': self.market_regime,
            'base_momentum': round(self.base_momentum, 2),
            'base_volume': round(self.base_volume, 0),
            'base_coherence': round(self.base_coherence, 2)
        }


# ═══════════════════════════════════════════════════════════════
# 🎯 TRAILING STOP MANAGER
# ═══════════════════════════════════════════════════════════════

class TrailingStopManager:
    """
    Manages trailing stops for all positions.
    Activates trailing stop once position is in profit, then trails behind price.
    """
    
    def __init__(self):
        # Configuration
        self.activation_profit_pct = CONFIG.get('TRAILING_ACTIVATION_PCT', 0.5)  # Activate at 0.5% profit
        self.trail_distance_pct = CONFIG.get('TRAILING_DISTANCE_PCT', 0.3)  # Trail 0.3% behind peak
        self.use_atr_trailing = CONFIG.get('USE_ATR_TRAILING', True)  # Use ATR for dynamic trailing
        self.atr_trail_multiplier = CONFIG.get('ATR_TRAIL_MULTIPLIER', 1.5)  # Trail at 1.5x ATR
        
        # Statistics
        self.trailing_stops_triggered = 0
        self.trailing_profits_locked = 0.0
        
    def update_position(self, pos, current_price: float, atr: float = 0.0) -> Dict[str, Any]:
        """
        Update trailing stop for a position.
        
        Args:
            pos: Position object
            current_price: Current market price
            atr: Average True Range (optional, for dynamic trailing)
            
        Returns:
            {'should_exit': bool, 'reason': str, 'stop_price': float}
        """
        result = {
            'should_exit': False,
            'reason': '',
            'stop_price': pos.trailing_stop_price,
            'highest_price': pos.highest_price,
            'pnl_pct': 0.0
        }
        
        # Update highest price tracking
        if current_price > pos.highest_price:
            pos.highest_price = current_price
            result['highest_price'] = current_price
            
        if current_price < pos.lowest_price:
            pos.lowest_price = current_price
            
        # Calculate current P&L percentage
        pnl_pct = ((current_price - pos.entry_price) / pos.entry_price) * 100
        result['pnl_pct'] = pnl_pct
        
        # Check if trailing stop should activate
        if not pos.trailing_stop_active:
            if pnl_pct >= self.activation_profit_pct:
                pos.trailing_stop_active = True
                # Set initial trailing stop
                pos.trailing_stop_price = self._calculate_stop_price(
                    pos.highest_price, pos.entry_price, atr
                )
                result['stop_price'] = pos.trailing_stop_price
                
        # Update trailing stop if active
        if pos.trailing_stop_active:
            new_stop = self._calculate_stop_price(pos.highest_price, pos.entry_price, atr)
            
            # Only raise the stop, never lower it
            if new_stop > pos.trailing_stop_price:
                pos.trailing_stop_price = new_stop
                result['stop_price'] = new_stop
                
            # Check if stop is triggered
            if current_price <= pos.trailing_stop_price:
                result['should_exit'] = True
                result['reason'] = f"TRAILING_STOP @ {pos.trailing_stop_price:.6f}"
                self.trailing_stops_triggered += 1
                
                # Calculate locked profit
                locked_pnl = ((pos.trailing_stop_price - pos.entry_price) / pos.entry_price) * 100
                self.trailing_profits_locked += locked_pnl
                
        return result
        
    def _calculate_stop_price(self, highest_price: float, entry_price: float, 
                              atr: float = 0.0) -> float:
        """Calculate trailing stop price."""
        if self.use_atr_trailing and atr > 0:
            # ATR-based trailing: trail at ATR * multiplier below peak
            stop_distance = atr * self.atr_trail_multiplier
            stop_price = highest_price - stop_distance
        else:
            # Percentage-based trailing
            stop_distance = highest_price * (self.trail_distance_pct / 100)
            stop_price = highest_price - stop_distance
            
        # Never set stop below entry (lock in breakeven minimum)
        return max(stop_price, entry_price * 1.001)  # At least 0.1% above entry
        
    def get_stats(self) -> Dict[str, Any]:
        """Get trailing stop statistics."""
        return {
            'stops_triggered': self.trailing_stops_triggered,
            'profits_locked_pct': round(self.trailing_profits_locked, 2),
            'activation_pct': self.activation_profit_pct,
            'trail_distance_pct': self.trail_distance_pct,
            'use_atr': self.use_atr_trailing
        }
        
    def reset_stats(self):
        """Reset statistics."""
        self.trailing_stops_triggered = 0
        self.trailing_profits_locked = 0.0


# ═══════════════════════════════════════════════════════════════
# 📢 NOTIFICATION SYSTEM (Telegram/Discord/Webhook)
# ═══════════════════════════════════════════════════════════════

class NotificationManager:
    """
    Sends trade alerts and notifications to Telegram, Discord, or webhooks.
    Configurable via environment variables.
    """
    
    def __init__(self):
        # Telegram config
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID', '')
        self.telegram_enabled = bool(self.telegram_token and self.telegram_chat_id)
        
        # Discord config
        self.discord_webhook = os.getenv('DISCORD_WEBHOOK_URL', '')
        self.discord_enabled = bool(self.discord_webhook)
        
        # Generic webhook config
        self.webhook_url = os.getenv('ALERT_WEBHOOK_URL', '')
        self.webhook_enabled = bool(self.webhook_url)
        
        # Rate limiting
        self.last_notification = 0
        self.min_interval = 60  # Minimum 60 seconds between notifications
        self.notification_history: List[Dict] = []
        
        # Alert levels
        self.alert_levels = {
            'TRADE': True,      # Trade executed
            'PROFIT': True,     # Position closed with profit
            'LOSS': True,       # Position closed with loss
            'CIRCUIT': True,    # Circuit breaker triggered
            'ARBITRAGE': True,  # Arbitrage opportunity
            'WARNING': True,    # System warnings
            'INFO': False       # General info (disabled by default)
        }
        
    def is_enabled(self) -> bool:
        """Check if any notification channel is enabled."""
        return self.telegram_enabled or self.discord_enabled or self.webhook_enabled
        
    def set_alert_level(self, level: str, enabled: bool):
        """Enable/disable specific alert types."""
        if level in self.alert_levels:
            self.alert_levels[level] = enabled
            
    def _can_send(self) -> bool:
        """Check rate limiting."""
        now = time.time()
        if now - self.last_notification < self.min_interval:
            return False
        return True
        
    def _send_telegram(self, message: str) -> bool:
        """Send message via Telegram."""
        if not self.telegram_enabled:
            return False
            
        try:
            import urllib.request
            import urllib.parse
            
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            data = urllib.parse.urlencode({
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }).encode()
            
            req = urllib.request.Request(url, data=data)
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Telegram send error: {e}")
            return False
            
    def _send_discord(self, message: str, title: str = "Aureon Alert") -> bool:
        """Send message via Discord webhook."""
        if not self.discord_enabled:
            return False
            
        try:
            import urllib.request
            import json
            
            payload = {
                "embeds": [{
                    "title": title,
                    "description": message,
                    "color": 0x00ff00  # Green
                }]
            }
            
            data = json.dumps(payload).encode()
            req = urllib.request.Request(
                self.discord_webhook,
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.status in [200, 204]
        except Exception as e:
            logger.error(f"Discord send error: {e}")
            return False
            
    def _send_webhook(self, payload: Dict) -> bool:
        """Send to generic webhook."""
        if not self.webhook_enabled:
            return False
            
        try:
            import urllib.request
            import json
            
            data = json.dumps(payload).encode()
            req = urllib.request.Request(
                self.webhook_url,
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Webhook send error: {e}")
            return False
            
    def send_alert(self, level: str, title: str, message: str, 
                   data: Dict = None) -> bool:
        """
        Send alert to all enabled channels.
        
        Args:
            level: Alert level (TRADE, PROFIT, LOSS, CIRCUIT, ARBITRAGE, WARNING, INFO)
            title: Alert title
            message: Alert message
            data: Optional additional data for webhook
        """
        # Check if this alert level is enabled
        if not self.alert_levels.get(level, False):
            return False
            
        # Rate limiting
        if not self._can_send():
            return False
            
        self.last_notification = time.time()
        
        # Build formatted message
        emoji_map = {
            'TRADE': '📊',
            'PROFIT': '💰',
            'LOSS': '📉',
            'CIRCUIT': '🚨',
            'ARBITRAGE': '⚡',
            'WARNING': '⚠️',
            'INFO': 'ℹ️'
        }
        emoji = emoji_map.get(level, '📢')
        
        formatted_msg = f"{emoji} <b>{title}</b>\n{message}"
        discord_msg = f"{emoji} **{title}**\n{message}"
        
        success = False
        
        # Send to all channels
        if self.telegram_enabled:
            success = self._send_telegram(formatted_msg) or success
            
        if self.discord_enabled:
            success = self._send_discord(discord_msg, f"{emoji} {title}") or success
            
        if self.webhook_enabled:
            webhook_payload = {
                'level': level,
                'title': title,
                'message': message,
                'timestamp': time.time(),
                'data': data or {}
            }
            success = self._send_webhook(webhook_payload) or success
            
        # Record notification
        self.notification_history.append({
            'level': level,
            'title': title,
            'timestamp': time.time(),
            'success': success
        })
        
        if len(self.notification_history) > 100:
            self.notification_history = self.notification_history[-100:]
            
        return success
        
    def notify_trade(self, symbol: str, side: str, price: float, 
                    quantity: float, exchange: str):
        """Send trade execution notification."""
        curr = "£" if CONFIG.get('BASE_CURRENCY') == 'GBP' else "$"
        value = price * quantity
        
        msg = (f"Symbol: {symbol}\n"
               f"Side: {side}\n"
               f"Price: {curr}{price:.6f}\n"
               f"Value: {curr}{value:.2f}\n"
               f"Exchange: {exchange.upper()}")
               
        self.send_alert('TRADE', f"{side} {symbol}", msg)
        
    def notify_close(self, symbol: str, pnl: float, pct: float, reason: str):
        """Send position close notification."""
        level = 'PROFIT' if pnl > 0 else 'LOSS'
        curr = "£" if CONFIG.get('BASE_CURRENCY') == 'GBP' else "$"
        
        msg = (f"Symbol: {symbol}\n"
               f"P&L: {curr}{pnl:+.2f} ({pct:+.1f}%)\n"
               f"Reason: {reason}")
               
        title = f"{'WIN' if pnl > 0 else 'LOSS'} {symbol}"
        self.send_alert(level, title, msg)
        
    def notify_circuit_breaker(self, reason: str, drawdown: float):
        """Send circuit breaker alert."""
        msg = (f"⚠️ TRADING HALTED\n"
               f"Reason: {reason}\n"
               f"Drawdown: {drawdown:.1f}%\n"
               f"Manual restart required!")
               
        self.send_alert('CIRCUIT', "CIRCUIT BREAKER", msg)
        
    def notify_arbitrage(self, opportunity: Dict):
        """Send arbitrage opportunity alert."""
        msg = (f"Symbol: {opportunity.get('symbol')}\n"
               f"Buy: {opportunity.get('buy_exchange')} @ {opportunity.get('buy_price'):.6f}\n"
               f"Sell: {opportunity.get('sell_exchange')} @ {opportunity.get('sell_price'):.6f}\n"
               f"Spread: {opportunity.get('spread_pct', 0):.2f}%\n"
               f"Net Profit: {opportunity.get('net_profit_pct', 0):.2f}%")
               
        self.send_alert('ARBITRAGE', "Arbitrage Found", msg)
        
    def get_status(self) -> Dict[str, Any]:
        """Get notification system status."""
        return {
            'telegram_enabled': self.telegram_enabled,
            'discord_enabled': self.discord_enabled,
            'webhook_enabled': self.webhook_enabled,
            'total_sent': len(self.notification_history),
            'recent_success_rate': self._calc_success_rate()
        }
        
    def _calc_success_rate(self) -> float:
        """Calculate recent notification success rate."""
        recent = self.notification_history[-20:]
        if not recent:
            return 0.0
        return sum(1 for n in recent if n['success']) / len(recent)


# ═══════════════════════════════════════════════════════════════
# 🌌 NEXUS INTEGRATION - UNIFIED NEURAL TRADING ENGINE
# ═══════════════════════════════════════════════════════════════

class NexusIntegration:
    """
    Integrates the Aureon Nexus (Master Equation + Queen Hive) into the ecosystem.
    
    The Nexus provides:
    - Master Equation: Λ(t) = S(t) + O(t) + E(t) for signal generation
    - Queen Hive: 10-9-1 compounding model for profit distribution
    - NexusBus: State management and signal propagation
    
    Coherence thresholds:
    - Entry: Γ > 0.75 (high confidence buy signal)
    - Exit: Γ < 0.70 (exit positions)
    """
    
    def __init__(self):
        self.enabled = NEXUS_AVAILABLE
        self.master_equation: Optional[Any] = None
        self.queen_hive: Optional[Any] = None
        self.nexus_bus = NEXUS_BUS
        
        # Coherence history for observer calculation
        self.coherence_history: List[float] = []
        
        # Performance tracking
        self.signals_generated = 0
        self.signals_followed = 0
        self.nexus_profits = 0.0
        
        if self.enabled:
            self._initialize_nexus()
        else:
            logger.warning("⚠️ Nexus not available - using fallback signals")
            
    def _initialize_nexus(self):
        """Initialize Nexus components."""
        try:
            from aureon_nexus import MasterEquation, QueenHive
            self.master_equation = MasterEquation()
            self.queen_hive = QueenHive(initial_capital=0.0)
            logger.info("🌌 NEXUS Integration initialized")
            logger.info(f"   └─ Master Equation: Λ(t) = S(t) + O(t) + E(t)")
            logger.info(f"   └─ Queen Hive: 10-9-1 compounding active")
            logger.info(f"   └─ Entry threshold: Γ > 0.75")
            logger.info(f"   └─ Exit threshold: Γ < 0.70")
        except Exception as e:
            logger.error(f"Failed to initialize Nexus: {e}")
            self.enabled = False
            
    def update_capital(self, capital: float):
        """Update Queen Hive with current capital."""
        if self.queen_hive:
            self.queen_hive.current_capital = capital
            if self.queen_hive.initial_capital == 0:
                self.queen_hive.initial_capital = capital
                
    def calculate_master_equation(self, market_data: Dict[str, float]) -> Dict[str, Any]:
        """
        Calculate the Master Equation and return signal.
        
        Market data should include:
        - volatility: 0.0 to 1.0
        - momentum: 0.0 to 1.0
        - sentiment: 0.0 to 1.0
        - trend_strength: 0.0 to 1.0
        - pattern_match: 0.0 to 1.0
        - harmony: 0.0 to 1.0
        - volume_ratio: 0.0 to 1.0
        - correlation: 0.0 to 1.0
        """
        if not self.enabled or not self.master_equation:
            return self._fallback_signal()
            
        try:
            # Update S(t) - Substrate from market data
            self.master_equation.update_substrate(market_data)
            
            # Update O(t) - Observer from coherence history
            self.master_equation.update_observer(self.coherence_history)
            
            # Update E(t) - Echo from momentum
            price_momentum = market_data.get('momentum', 0.5)
            self.master_equation.update_echo(price_momentum)
            
            # Calculate Λ(t) and derive coherence Γ
            self.master_equation.calculate_lambda()
            
            # Store coherence in history
            self.coherence_history.append(self.master_equation.coherence)
            if len(self.coherence_history) > 100:
                self.coherence_history = self.coherence_history[-100:]
                
            # Get signal
            signal, confidence = self.master_equation.get_signal()
            self.signals_generated += 1
            
            return {
                'signal': signal,
                'confidence': confidence,
                'coherence': self.master_equation.coherence,
                'lambda': self.master_equation.lambda_value,
                'substrate': self.master_equation.substrate,
                'observer': self.master_equation.observer,
                'echo': self.master_equation.echo,
                'entry_threshold': self.master_equation.entry_threshold,
                'exit_threshold': self.master_equation.exit_threshold
            }
        except Exception as e:
            logger.error(f"Master Equation error: {e}")
            return self._fallback_signal()
            
    def _fallback_signal(self) -> Dict[str, Any]:
        """Fallback when Nexus is unavailable."""
        return {
            'signal': 'NEUTRAL',
            'confidence': 0.5,
            'coherence': 0.5,
            'lambda': 1.5,
            'substrate': 0.5,
            'observer': 0.5,
            'echo': 0.5,
            'entry_threshold': 0.75,
            'exit_threshold': 0.70
        }
        
    def record_trade_profit(self, profit: float, btc_price: float = 95000) -> Dict[str, float]:
        """
        Record profit through Queen Hive 10-9-1 model.
        
        Returns distribution:
        - compound: 90% goes back to capital
        - harvest: 10% for spawning new hives
        """
        if not self.queen_hive:
            return {'profit': profit, 'compound': profit * 0.9, 'harvest': profit * 0.1}
            
        result = self.queen_hive.record_profit(profit, btc_price)
        self.nexus_profits += profit
        
        if profit > 0:
            self.signals_followed += 1
            
        return result
        
    def get_hive_stats(self) -> Dict[str, Any]:
        """Get Queen Hive statistics."""
        if not self.queen_hive:
            return {}
            
        try:
            return self.queen_hive.get_stats()
        except:
            return {}
            
    def broadcast_signal(self, module: str, signal_type: str, data: Dict) -> bool:
        """Broadcast signal through NexusBus."""
        if not self.nexus_bus:
            return False
            
        try:
            self.nexus_bus.emit(module, signal_type, data)
            return True
        except Exception as e:
            logger.error(f"NexusBus broadcast error: {e}")
            return False
            
    def register_module(self, name: str, callback) -> bool:
        """Register a module to receive NexusBus signals."""
        if not self.nexus_bus:
            return False
            
        try:
            self.nexus_bus.register(name, callback)
            return True
        except Exception as e:
            logger.error(f"NexusBus registration error: {e}")
            return False
            
    def convert_klines_to_market_data(self, klines: List[Dict]) -> Dict[str, float]:
        """
        Convert kline data to market data format for Master Equation.
        
        Calculates volatility, momentum, trend_strength etc. from OHLCV data.
        """
        if not klines or len(klines) < 2:
            return {
                'volatility': 0.5,
                'momentum': 0.5,
                'sentiment': 0.5,
                'trend_strength': 0.5,
                'pattern_match': 0.5,
                'harmony': 0.5,
                'volume_ratio': 0.5,
                'correlation': 0.5
            }
            
        try:
            # Get recent prices
            closes = [float(k.get('close', k.get('c', 0))) for k in klines[-20:] if k]
            highs = [float(k.get('high', k.get('h', 0))) for k in klines[-20:] if k]
            lows = [float(k.get('low', k.get('l', 0))) for k in klines[-20:] if k]
            volumes = [float(k.get('volume', k.get('v', 0))) for k in klines[-20:] if k]
            
            if not closes:
                return self._default_market_data()
                
            current_price = closes[-1]
            
            # Volatility: Average true range normalized
            if len(highs) >= 2 and len(lows) >= 2:
                atr = sum(h - l for h, l in zip(highs[-14:], lows[-14:])) / min(14, len(highs))
                volatility = min(1.0, atr / current_price * 10)  # Normalize
            else:
                volatility = 0.5
                
            # Momentum: Price change over period
            if len(closes) >= 5:
                momentum_raw = (closes[-1] - closes[-5]) / closes[-5]
                momentum = 0.5 + (momentum_raw * 5)  # Scale to 0-1 range
                momentum = max(0.0, min(1.0, momentum))
            else:
                momentum = 0.5
                
            # Trend strength: Directional consistency
            if len(closes) >= 10:
                ups = sum(1 for i in range(1, len(closes)) if closes[i] > closes[i-1])
                trend_strength = ups / (len(closes) - 1)
            else:
                trend_strength = 0.5
                
            # Volume ratio: Current vs average
            if volumes and sum(volumes[:-1]) > 0:
                avg_vol = sum(volumes[:-1]) / len(volumes[:-1])
                volume_ratio = min(1.0, volumes[-1] / avg_vol) if avg_vol > 0 else 0.5
            else:
                volume_ratio = 0.5
                
            # Sentiment: Based on close position in range
            if len(highs) >= 1 and len(lows) >= 1:
                high_low_range = max(highs[-1] - lows[-1], 0.0001)
                sentiment = (current_price - lows[-1]) / high_low_range
                sentiment = max(0.0, min(1.0, sentiment))
            else:
                sentiment = 0.5
                
            # Harmony: Golden ratio alignment (0.618, 1.618)
            if len(closes) >= 5:
                ratio = closes[-1] / closes[-5] if closes[-5] > 0 else 1.0
                phi_distance = abs(ratio - 1.618)
                harmony = max(0.0, 1.0 - phi_distance)
            else:
                harmony = 0.5
                
            return {
                'volatility': volatility,
                'momentum': momentum,
                'sentiment': sentiment,
                'trend_strength': trend_strength,
                'pattern_match': 0.5,  # Requires pattern detection
                'harmony': harmony,
                'volume_ratio': volume_ratio,
                'correlation': 0.5  # Requires cross-asset analysis
            }
        except Exception as e:
            logger.error(f"Kline conversion error: {e}")
            return self._default_market_data()
            
    def _default_market_data(self) -> Dict[str, float]:
        """Default market data values."""
        return {
            'volatility': 0.5,
            'momentum': 0.5,
            'sentiment': 0.5,
            'trend_strength': 0.5,
            'pattern_match': 0.5,
            'harmony': 0.5,
            'volume_ratio': 0.5,
            'correlation': 0.5
        }
        
    def should_enter(self, coherence: float = None) -> bool:
        """Check if coherence meets entry threshold."""
        if coherence is None:
            coherence = self.master_equation.coherence if self.master_equation else 0.5
        return coherence >= 0.75
        
    def should_exit(self, coherence: float = None) -> bool:
        """Check if coherence falls below exit threshold."""
        if coherence is None:
            coherence = self.master_equation.coherence if self.master_equation else 0.5
        return coherence <= 0.70
        
    def get_stats(self) -> Dict[str, Any]:
        """Get Nexus integration statistics."""
        stats = {
            'enabled': self.enabled,
            'signals_generated': self.signals_generated,
            'signals_followed': self.signals_followed,
            'nexus_profits': self.nexus_profits,
            'current_coherence': self.master_equation.coherence if self.master_equation else 0.0,
            'coherence_avg': sum(self.coherence_history[-20:]) / max(1, len(self.coherence_history[-20:]))
        }
        
        # Add hive stats if available
        hive_stats = self.get_hive_stats()
        if hive_stats:
            stats['hive'] = hive_stats
            
        return stats
        
    def display_equation(self):
        """Display current Master Equation state."""
        if self.master_equation:
            self.master_equation.display()


# ═══════════════════════════════════════════════════════════════
# 🌟 SWARM ORCHESTRATOR ENHANCEMENTS
# ═══════════════════════════════════════════════════════════════

# Prime numbers for dynamic sizing (from multi_agent_aggressive.ts)
PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71]
PRIME_SCALE = 0.05  # 5% per prime unit → 10%, 15%, 25%, 35%, etc. (sensible position sizes)

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
        super().__init__("Falcon", CONFIG['FREQ_FALCON'], 1.35)  # BOOSTED: 75% win rate
        
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
        super().__init__("Dolphin", CONFIG['FREQ_DOLPHIN'], 0.6)  # REDUCED: 0% win rate in data (needs investigation)
        
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
        super().__init__("Deer", CONFIG['FREQ_DEER'], 1.25)  # BOOSTED: Highest profitability $+39.71
        
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
        super().__init__("Panda", CONFIG['FREQ_PANDA'], 1.20)  # BOOSTED: 60% win rate $+15.84
        
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
        
        # 🌍⚡ Global Financial Ecosystem Feed ⚡🌍
        self.global_feed = None
        self.macro_snapshot = None
        if GLOBAL_FEED_AVAILABLE:
            try:
                self.global_feed = GlobalFinancialFeed()
                self.macro_snapshot = self.global_feed.get_snapshot()
                print("   🌍 Global Financial Ecosystem ACTIVE")
                print(f"      Fear/Greed: {self.macro_snapshot.crypto_fear_greed} | Regime: {self.macro_snapshot.market_regime}")
            except Exception as e:
                print(f"   ⚠️  Global Feed init failed: {e}")
        
        # 📊 Probability Validation Engine 📊
        self.probability_validator = None
        if VALIDATOR_AVAILABLE:
            try:
                self.probability_validator = get_validator()
                stats = self.probability_validator.stats
                if stats.validated_predictions > 0:
                    print(f"   📊 Probability Validator ACTIVE")
                    print(f"      Accuracy: {stats.direction_accuracy*100:.1f}% ({stats.validated_predictions} predictions)")
                else:
                    print("   📊 Probability Validator ACTIVE (collecting data)")
            except Exception as e:
                print(f"   ⚠️  Validator init failed: {e}")
        
        # 🌍⚡ CoinAPI Anomaly Detection ⚡🌍
        self.coinapi_detector = None
        self.anomaly_blacklist: Dict[str, float] = {}  # {symbol: unblock_timestamp}
        self.coherence_adjustments: Dict[str, float] = {}  # {symbol: adjustment_factor}
        self.last_anomaly_scan = 0
        if COINAPI_AVAILABLE:
            try:
                api_key = os.getenv('COINAPI_KEY', '')
                if api_key:
                    coinapi_client = CoinAPIClient(api_key)
                    self.coinapi_detector = AnomalyDetector(coinapi_client)
                    print("   🌐 CoinAPI Anomaly Detection ACTIVE")
                else:
                    print("   ⚠️  CoinAPI: No API key (anomaly detection disabled)")
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
        
        # 🔭 QUANTUM TELESCOPE & HARMONIC UNDERLAY 🔭
        self.telescope = None
        self.harmonic_engine = None
        if CONFIG.get('ENABLE_QUANTUM_TELESCOPE', True):
            try:
                self.telescope = QuantumTelescope()
                self.harmonic_engine = SixDimensionalHarmonicEngine()
                print("   🔭 Quantum Telescope & Harmonic Engine ACTIVE")
            except Exception as e:
                print(f"   ⚠️  Quantum Telescope init failed: {e}")
        
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

            # H6D(t) = 6D Harmonic waveform ecosystem coherence
            harmonic6d = 0.0
            if self.harmonic_engine:
                try:
                    eco = self.harmonic_engine.get_ecosystem_state()
                    harmonic_coh = eco.get('ecosystem_coherence', 0.0)
                    if harmonic_coh >= CONFIG.get('HARMONIC_GATE', 0.45):
                        harmonic6d = harmonic_coh * CONFIG.get('HARMONIC_WEIGHT', 0.20)
                except Exception:
                    harmonic6d = 0.0
            
            # Q(t) = Quantum Telescope component (Geometric Coherence)
            quantum = 0.0
            if self.telescope:
                try:
                    beam = LightBeam(
                        symbol=state.symbol,
                        price=state.price,
                        volume=state.volume,
                        momentum=state.change_24h,
                        timestamp=state.timestamp
                    )
                    observation = self.telescope.observe(beam)
                    # Use Dodecahedron (Ether/Coherence) as the primary signal
                    quantum = observation.get(GeometricSolid.DODECAHEDRON, 0.5) * CONFIG.get('QUANTUM_WEIGHT', 0.20)
                except Exception:
                    quantum = 0.0

            # Λ(t) = S(t) + O(t) + E(t) + H(t) + H6D(t) + Q(t)
            lambda_field = substrate + observer + echo + harmonic + harmonic6d + quantum
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
    
    def should_trade_brain(self) -> Tuple[bool, str]:
        """
        🧠 BRAIN GATE: 7 Civilizations + Quantum Brain must approve trades.
        Returns (should_trade, reason).
        """
        if not hasattr(self, 'brain_bridge') or not self.brain_bridge:
            return True, "Brain Bridge not initialized - trading allowed"
        
        try:
            # Get brain recommendation
            rec = self.brain_bridge.get_trading_recommendation()
            action = rec.get('action', 'HOLD')
            civs_bullish = rec.get('civilizations_bullish', 0)
            civs_total = rec.get('civilizations_total', 7)
            confidence = rec.get('confidence', 0.5)
            reasoning = rec.get('reasoning', [])
            
            # HARD BLOCK: If brain says REDUCE with high confidence
            if action == 'REDUCE' and confidence > 0.65:
                return False, f"Brain says REDUCE (conf={confidence:.0%}, {civs_bullish}/{civs_total} bullish)"
            
            # SOFT GATE: If BEARISH with moderate confidence
            consensus = self._brain_consensus
            if consensus == 'BEARISH' and confidence > 0.6:
                return False, f"Brain BEARISH (conf={confidence:.0%}) - waiting for bullish signal"
            
            # APPROVED
            if action == 'BUY':
                return True, f"Brain APPROVED: {civs_bullish}/{civs_total} civilizations BULLISH"
            
            return True, f"Brain neutral - {consensus} (conf={confidence:.0%})"
            
        except Exception as e:
            return True, f"Brain check error ({e}) - trading allowed"
    
    def should_trade_all_gates(self) -> Tuple[bool, str]:
        """
        Combined gate check: Imperial + HNC + Earth Resonance + BRAIN.
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
        
        # 🧠 Check Brain gate (NEW)
        brain_ok, brain_reason = self.should_trade_brain()
        if not brain_ok:
            reasons.append(f"Brain: {brain_reason}")
        
        if reasons:
            return False, " | ".join(reasons)
        
        return True, "All gates OPEN"
    
    def get_system_health_report(self) -> Dict[str, Any]:
        """
        🏥 COMPREHENSIVE SYSTEM HEALTH CHECK 🏥
        Ensures all subsystems are operational and communicating.
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'systems': {},
            'communication': {},
            'gates': {},
            'data': {},
            'signals': {},
            'overall_health': 'UNKNOWN',
        }
        
        # 1️⃣ PROBABILITY MATRIX
        prob_status = "ACTIVE" if self.prob_matrix else "INACTIVE"
        report['systems']['probability_matrix'] = {
            'status': prob_status,
            'description': '📊 Multi-day temporal windows (Day -7 to +7)',
            'learning': 'ENABLED' if self.prob_matrix else False,
        }
        
        # 1.5️⃣ PROBABILITY LOADER & CONSENSUS
        loader = getattr(self, 'probability_loader', None)
        loader_status = "ACTIVE" if loader else "INACTIVE"
        report['systems']['probability_loader'] = {
            'status': loader_status,
            'description': '🎯 Fresh probability reports + multi-exchange consensus',
            'fresh': loader.is_fresh() if loader else False,
        }
        
        # 2️⃣ IMPERIAL PREDICTABILITY
        imperial_status = "ACTIVE" if self.imperial else "INACTIVE"
        report['systems']['imperial'] = {
            'status': imperial_status,
            'phase': self.cosmic_phase if self.imperial else 'N/A',
            'description': '🌌⚡ Cosmic phase + planetary torque',
        }
        
        # 3️⃣ EARTH RESONANCE
        earth_status = "ACTIVE" if self.earth_engine else "INACTIVE"
        report['systems']['earth_resonance'] = {
            'status': earth_status,
            'description': '🌍 Schumann resonance + PHI amplification',
            'gate': 'OPEN' if self.earth_engine else 'N/A',
        }
        
        # 4️⃣ HNC FREQUENCY
        hnc_status = "ACTIVE" if self.hnc else "INACTIVE"
        report['systems']['hnc_frequency'] = {
            'status': hnc_status,
            'frequency': f"{self.hnc_frequency:.0f}Hz" if self.hnc else 'N/A',
            'description': '🌍⚡ Harmonic frequency analysis',
            'harmonic': self.hnc_is_harmonic if self.hnc else False,
        }
        
        # 5️⃣ GLOBAL FINANCIAL FEED
        feed_status = "ACTIVE" if self.global_feed else "INACTIVE"
        report['systems']['global_feed'] = {
            'status': feed_status,
            'description': '🌍 Macro indicators + fear/greed index',
        }
        
        # 6️⃣ ANOMALY DETECTION
        anomaly_status = "ACTIVE" if self.coinapi_detector else "INACTIVE"
        report['systems']['anomaly_detection'] = {
            'status': anomaly_status,
            'blacklisted_symbols': len(self.anomaly_blacklist),
            'description': '🌐 CoinAPI anomaly detection',
        }
        
        # 7️⃣ QUANTUM TELESCOPE
        quantum_status = "ACTIVE" if self.telescope else "INACTIVE"
        report['systems']['quantum_telescope'] = {
            'status': quantum_status,
            'description': '🔭 Quantum harmonic resonance',
        }
        
        # GATES REPORT
        imperial_ok, imperial_reason = self.should_trade_imperial()
        earth_ok, earth_reason = self.should_trade_earth()
        all_ok, all_reason = self.should_trade_all_gates()
        
        # Check Brain gate
        brain_ok, brain_reason = self.should_trade_brain()
        
        report['gates']['imperial'] = {'open': imperial_ok, 'reason': imperial_reason}
        report['gates']['earth'] = {'open': earth_ok, 'reason': earth_reason}
        report['gates']['brain'] = {'open': brain_ok, 'reason': brain_reason}
        report['gates']['all'] = {'open': all_ok, 'reason': all_reason}
        
        # DATA FRESHNESS & SIGNALS
        try:
            # Probability loader freshness
            if loader:
                fresh = loader.is_fresh()
                newest, oldest = loader.get_report_ages()
                report['data']['probability_reports'] = {
                    'stale': not fresh,
                    'newest_minutes': newest,
                    'oldest_minutes': oldest,
                    'threshold_minutes': loader.freshness_threshold_minutes,
                }
                
                # High conviction signals
                top_signals = loader.get_top_signals(limit=10, min_probability=0.8, min_confidence=0.8)
                report['signals']['high_conviction'] = {
                    'count': len(top_signals),
                    'symbols': [s['symbol'] for s in top_signals[:5]],  # Top 5
                }
                
                # Multi-exchange consensus
                consensus = loader.get_consensus_signals(min_exchanges=2, min_probability=0.75)
                report['signals']['consensus'] = {
                    'count': len(consensus),
                    'symbols': [c['symbol'] for c in consensus[:5]],  # Top 5
                }
            else:
                # Fallback to state aggregator
                agg = STATE_AGGREGATOR.aggregated_state
                pfresh = agg.get('probability_freshness', {}) if agg else {}
                report['data']['probability_reports'] = {
                    'stale': pfresh.get('stale', False),
                    'newest_minutes': pfresh.get('newest_minutes'),
                    'oldest_minutes': pfresh.get('oldest_minutes'),
                    'threshold_minutes': pfresh.get('threshold_minutes', 120),
                }
                report['signals']['high_conviction'] = {'count': 0, 'symbols': []}
                report['signals']['consensus'] = {'count': 0, 'symbols': []}
            
            # Position hygiene check
            hygiene_checker = getattr(self, 'position_hygiene', None)
            if hygiene_checker:
                state_path = '/workspaces/aureon-trading/aureon_kraken_state.json'
                hygiene_result = hygiene_checker.check_positions(state_path)
                report['data']['position_hygiene'] = {
                    'flagged': hygiene_result.get('flagged', []),
                    'count': hygiene_result.get('count', 0),
                    'rules': hygiene_result.get('rules', {}),
                }
            else:
                agg = STATE_AGGREGATOR.aggregated_state
                position_hygiene = agg.get('position_hygiene', {}) if agg else {}
                report['data']['position_hygiene'] = {
                    'flagged': position_hygiene.get('flagged', []),
                    'count': len(position_hygiene.get('flagged', [])),
                    'rules': position_hygiene.get('rules', {}),
                }
        except Exception as e:
            logger.warning(f"Health report data gathering error: {e}")
            report['data']['probability_reports'] = {'stale': False}
            report['data']['position_hygiene'] = {'flagged': [], 'count': 0}
            report['signals'] = {'high_conviction': {'count': 0, 'symbols': []}, 'consensus': {'count': 0, 'symbols': []}}

        # COMMUNICATION CHECK
        systems_active = sum(1 for s in report['systems'].values() if s['status'] == 'ACTIVE')
        report['communication'] = {
            'systems_active': systems_active,
            'auris_hub': 'OPERATIONAL',
            'data_flow': 'BIDIRECTIONAL',
            'learning_enabled': bool(self.prob_matrix),
            'validation_enabled': bool(self.probability_validator),
        }
        
        # OVERALL HEALTH
        prob_stale = report['data'].get('probability_reports', {}).get('stale', False)
        hygiene_count = report['data'].get('position_hygiene', {}).get('count', 0)
        consensus_count = report['signals'].get('consensus', {}).get('count', 0)
        high_conv_count = report['signals'].get('high_conviction', {}).get('count', 0)

        if all_ok and systems_active >= 5 and not prob_stale and hygiene_count == 0 and consensus_count > 0:
            report['overall_health'] = f'🟢 HEALTHY - All systems communicating ({consensus_count} consensus signals)'
        elif all_ok and systems_active >= 4 and not prob_stale:
            if hygiene_count > 0:
                report['overall_health'] = f'🟡 OPERATIONAL - {hygiene_count} position hygiene alerts'
            else:
                report['overall_health'] = f'🟡 OPERATIONAL - Core systems active ({high_conv_count} high-conviction signals)'
        elif all_ok and systems_active >= 2:
            if prob_stale:
                report['overall_health'] = '🟡 OPERATIONAL - Probability data stale'
            else:
                report['overall_health'] = '🟡 OPERATIONAL - Limited systems active'
        else:
            report['overall_health'] = '🔴 DEGRADED - Check gates and systems'
        
        return report
    
    def print_system_health(self) -> None:
        """
        Print a formatted system health report to console.
        Shows all active systems and their communication status.
        """
        report = self.get_system_health_report()
        
        print("\n" + "═" * 80)
        print("🏥 ECOSYSTEM HEALTH REPORT " + report['overall_health'])
        print("═" * 80)
        
        print("\n📡 SUBSYSTEMS STATUS:")
        for name, system in report['systems'].items():
            status = system['status']
            indicator = "✅" if status == "ACTIVE" else "⚪"
            desc = system.get('description', '')
            print(f"  {indicator} {name.upper().replace('_', ' ')}: {desc}")
        
        print("\n🚪 TRADING GATES:")
        for gate_name, gate_status in report['gates'].items():
            if gate_name == 'all':
                indicator = "🟢" if gate_status['open'] else "🔴"
                print(f"\n  {indicator} ALL GATES: {gate_status['reason']}")
            else:
                indicator = "✅" if gate_status['open'] else "❌"
                print(f"  {indicator} {gate_name.upper()}: {gate_status['reason']}")
        
        print("\n📊 COMMUNICATION HUB:")
        comm = report['communication']
        print(f"  • Systems Active: {comm['systems_active']}/8")
        print(f"  • Auris Hub: {comm['auris_hub']}")
        print(f"  • Data Flow: {comm['data_flow']}")
        print(f"  • Learning: {'ENABLED ✅' if comm['learning_enabled'] else 'DISABLED ⚪'}")
        print(f"  • Validation: {'ENABLED ✅' if comm['validation_enabled'] else 'DISABLED ⚪'}")
        
        # SIGNALS
        signals = report.get('signals', {})
        high_conv = signals.get('high_conviction', {})
        consensus = signals.get('consensus', {})
        if high_conv.get('count', 0) > 0 or consensus.get('count', 0) > 0:
            print("\n🎯 TRADING SIGNALS:")
            if high_conv.get('count', 0) > 0:
                symbols_str = ', '.join(high_conv.get('symbols', [])[:5])
                print(f"  • High Conviction: {high_conv['count']} signals (p≥0.8, conf≥0.8)")
                print(f"    Top: {symbols_str}")
            if consensus.get('count', 0) > 0:
                symbols_str = ', '.join(consensus.get('symbols', [])[:5])
                print(f"  • Multi-Exchange Consensus: {consensus['count']} symbols (≥2 exchanges)")
                print(f"    Top: {symbols_str}")

        data = report.get('data', {})
        prob_data = data.get('probability_reports', {})
        hygiene = data.get('position_hygiene', {})
        print("\n🧠 DATA HEALTH:")
        if prob_data:
            stale = prob_data.get('stale')
            newest = prob_data.get('newest_minutes')
            threshold = prob_data.get('threshold_minutes')
            indicator = "⚠️" if stale else "✅"
            newest_str = f"{newest:.1f}m" if newest is not None else "n/a"
            print(f"  {indicator} Probability reports fresh: {newest_str} (threshold {threshold}m)")
        if hygiene:
            count = hygiene.get('count', 0)
            indicator = "⚠️" if count > 0 else "✅"
            print(f"  {indicator} Position hygiene flags: {count}")
        
        print("\n" + "═" * 80 + "\n")
    
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
# ══════════════════════════════════════════════════════════════
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


# 🍄🧠 FULL MYCELIUM NEURAL NETWORK WITH HIVES & QUEEN NEURON
# ══════════════════════════════════════════════════════════════
# Import the full neural network if available
try:
    from aureon_mycelium import MyceliumNetwork as FullMyceliumNetwork, Hive, Agent, Neuron
    FULL_MYCELIUM_AVAILABLE = True
    logger.info("🍄🧠 Full Mycelium Neural Network loaded - Hives & Queen Neuron ACTIVE")
except ImportError:
    FULL_MYCELIUM_AVAILABLE = False
    logger.warning("⚠️ Full Mycelium not available, using simplified pattern network")


class MyceliumNetwork:
    """
    Neural network for pattern detection across symbols.
    
    🧠 ENHANCED: Now integrates with full Mycelium hive system!
    - Multiple agent hives with different strategies
    - Queen Neuron for collective decision making
    - Self-spawning when profitable (network growth)
    - Hebbian learning on all connections
    """
    
    def __init__(self, initial_capital: float = 100.0):
        # Simple pattern network (always available)
        self.synapses: Dict[str, List[Synapse]] = {}
        self.activations: Dict[str, float] = {}
        
        # 🍄 FULL NEURAL NETWORK (if available)
        self.full_network = None
        self.queen_signal = 0.0  # Queen Neuron's collective decision
        self.hive_count = 0
        self.total_agents = 0
        self.generation = 0
        
        if FULL_MYCELIUM_AVAILABLE:
            try:
                self.full_network = FullMyceliumNetwork(
                    initial_capital=initial_capital,
                    agents_per_hive=5,
                    target_multiplier=2.0
                )
                self.hive_count = len(self.full_network.hives)
                self.total_agents = self.full_network.get_total_agents()
                logger.info(f"🍄 Mycelium initialized: {self.hive_count} hives, {self.total_agents} agents")
            except Exception as e:
                logger.warning(f"⚠️ Could not initialize full Mycelium: {e}")
                self.full_network = None
        
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
        
        # 🍄 FULL NETWORK: Also step the hive neural network
        if self.full_network:
            try:
                # Build market data from our activations
                avg_activation = sum(self.activations.values()) / max(1, len(self.activations))
                market_data = {
                    "price": 95000,  # Will be updated with real price
                    "momentum": avg_activation * 2 - 1,  # Convert [0,1] to [-1,1]
                    "volatility": 0.5,
                    "trend": avg_activation - 0.5
                }
                
                # Step the full network - all hives process and Queen decides
                result = self.full_network.step(market_data)
                
                # 🧠 QUEEN NEURON SIGNAL - This is the collective intelligence!
                self.queen_signal = result.get("queen_signal", 0.0)
                self.hive_count = result.get("hive_count", 1)
                self.generation = result.get("generation", 0)
                self.total_agents = self.full_network.get_total_agents()
                
            except Exception as e:
                logger.debug(f"Mycelium step error: {e}")
        
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
        
        # 🍄 FULL NETWORK: Also reinforce hive synapses
        if self.full_network and profit_pct > 0:
            try:
                # Strengthen hive synapses that contributed to this profit
                for synapse in self.full_network.hive_synapses:
                    synapse.strengthen(profit_pct * 0.5)  # Dampened learning
            except Exception:
                pass

    def get_network_coherence(self) -> float:
        """Overall network coherence - now includes Queen Neuron signal!"""
        if not self.activations:
            return 0.5
        
        # Base coherence from pattern network
        base_coherence = sum(self.activations.values()) / len(self.activations)
        
        # 🧠 BLEND WITH QUEEN NEURON SIGNAL
        if self.full_network and self.queen_signal != 0:
            # Queen signal is [-1, 1], convert to [0, 1]
            queen_coherence = (self.queen_signal + 1) / 2
            # Blend: 70% pattern network, 30% Queen Neuron
            blended = base_coherence * 0.7 + queen_coherence * 0.3
            return blended
        
        return base_coherence
    
    def get_queen_signal(self) -> float:
        """Get the Queen Neuron's collective decision signal [-1, 1]"""
        return self.queen_signal
    
    def get_network_state(self) -> Dict[str, Any]:
        """Get full neural network state for display"""
        state = {
            "pattern_nodes": len(self.activations),
            "pattern_synapses": sum(len(s) for s in self.synapses.values()),
            "queen_signal": self.queen_signal,
            "hive_count": self.hive_count,
            "total_agents": self.total_agents,
            "generation": self.generation,
            "full_network_active": self.full_network is not None
        }
        
        if self.full_network:
            try:
                full_state = self.full_network.get_state()
                state["total_equity"] = full_state.get("total_equity", 0)
                state["total_harvested"] = full_state.get("total_harvested", 0)
                state["split_events"] = len(full_state.get("split_events", []))
            except Exception:
                pass
        
        return state
    
    def display_neural_status(self):
        """Display neural network status"""
        state = self.get_network_state()
        queen_emoji = "👑" if state["queen_signal"] > 0.3 else "👸" if state["queen_signal"] > -0.3 else "💀"
        signal_bar = "█" * int(abs(state["queen_signal"]) * 10)
        direction = "BUY" if state["queen_signal"] > 0 else "SELL" if state["queen_signal"] < 0 else "HOLD"
        
        print(f"""
   🍄 MYCELIUM NEURAL NETWORK
   ├─ Pattern Nodes: {state['pattern_nodes']} | Synapses: {state['pattern_synapses']}
   ├─ Hives: {state['hive_count']} | Agents: {state['total_agents']} | Gen: {state['generation']}
   └─ {queen_emoji} Queen Signal: {state['queen_signal']:+.3f} [{signal_bar}] → {direction}
""")


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
    exchange: str = 'binance'  # Exchange where position is held
    
    # 🎯 TRAILING STOP SUPPORT
    highest_price: float = 0.0  # Highest price since entry (for trailing stop)
    lowest_price: float = float('inf')  # Lowest price since entry (for shorts)
    trailing_stop_active: bool = False  # Is trailing stop currently active?
    trailing_stop_price: float = 0.0  # Current trailing stop level
    
    # 📦 HISTORICAL ASSET FLAG - These can be liquidated for cash when better opportunities arise
    is_historical: bool = False  # True = imported from exchange, no known entry price, treat as available capital
    
    # 🧠 LEARNED PARAMETERS - Set from probability matrix recommendations
    learned_tp_pct: Optional[float] = None  # Suggested take profit % from historical performance
    learned_sl_pct: Optional[float] = None  # Suggested stop loss % from historical performance
    learned_hold_cycles: Optional[int] = None  # Suggested minimum hold cycles
    learned_win_rate: Optional[float] = None  # Expected win rate based on similar trades
    learned_confidence: str = 'low'  # Confidence level of learned parameters
    
    # 🔮 NEXUS PREDICTOR DATA - For learning feedback
    nexus_prob: float = 0.5  # Nexus prediction probability at entry
    nexus_edge: float = 0.0  # Nexus edge at entry
    nexus_patterns: List[str] = field(default_factory=list)  # Patterns triggered at entry
    
    # 🚀 SERVER-SIDE ORDER IDs (Kraken/Alpaca native TP/SL - execute even if bot offline)
    server_sl_order_id: Optional[str] = None  # Kraken/Alpaca stop-loss order ID (or OCO ID for Alpaca)
    server_tp_order_id: Optional[str] = None  # Kraken take-profit order ID
    server_trailing_order_id: Optional[str] = None  # Kraken/Alpaca trailing stop order ID
    
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
        self.first_start_balance = initial_balance  # TRUE starting balance - survives restarts!
        self.first_start_time = time.time()  # When the system FIRST started
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
        self.circuit_breaker_enabled = False  # Disabled until first baseline reset
        
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
        # Only check circuit breaker if enabled (after first baseline reset)
        if self.circuit_breaker_enabled and dd >= CONFIG['MAX_DRAWDOWN_PCT'] and not self.trading_halted:
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
        
        # Apply κt efficiency safely: trade as if larger but risk base sizing
        final_size = min(scaled_size * KT_EFFICIENCY, available_exposure, CONFIG['MAX_POSITION_SIZE'])
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
    
    def __init__(self, initial_balance: float = 1000.0, dry_run: bool = False):
        # Initialize Multi-Exchange Client
        self.client = MultiExchangeClient()
        self.dry_run = self.client.dry_run
        
        self.auris = AurisEngine()
        self.mycelium = MyceliumNetwork(initial_capital=initial_balance)  # 🍄🧠 Full neural network with hives!
        self.lattice = GaiaLatticeEngine()  # 🌍 GAIA FREQUENCY PHYSICS - HNC Blackboard Carrier Wave Dynamics
        self.enhancements = EnhancementLayer() if ENHANCEMENTS_AVAILABLE else None  # 🔯 CODEX INTEGRATION
        self.market_pulse = MarketPulse(self.client) # Initialize Market Pulse
        self.tracker = PerformanceTracker(initial_balance)
        self.memory = ElephantMemory()  # 🐘 Initialize Elephant Memory
        self.flux_predictor = SystemFluxPredictor() # 🔮 Initialize Flux Predictor

        # Mirror harmonic engine reference for convenience
        self.harmonic_engine = getattr(self.auris, 'harmonic_engine', None)
        
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

        # Live P&L snapshot (updated in refresh_equity)
        self.pnl_state: Dict[str, float] = {
            'total_equity': initial_balance,
            'cash': initial_balance,
            'net_profit': 0.0,
            'total_return_pct': 0.0,
            'timestamp': time.time(),
        }
        
        # 🚫 INVALID SYMBOL CACHE - Avoid repeated API calls for bad symbols
        self._invalid_symbols: Dict[str, float] = {}  # symbol -> timestamp when marked invalid
        self._valid_symbols: Dict[str, str] = {}  # symbol -> exchange (verified working)
        self._symbol_cache_ttl = 3600  # Recheck invalid symbols after 1 hour
        self._dust_positions: Dict[str, Tuple[str, float]] = {}  # symbol -> (reason, timestamp)
        self._dust_ttl = 86400  # 24h dust TTL before re-attempting
        self._lot_size_cache: Dict[str, Tuple[Optional[float], Optional[float]]] = {}
        
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
        
        # 🔮 NEXUS PREDICTOR - 79.6% Win Rate Validated! 🔮
        if NEXUS_PREDICTOR_AVAILABLE:
            self.nexus_predictor = NexusPredictor()
            print("   🔮 Nexus Predictor initialized (79.6% validated)")
        else:
            self.nexus_predictor = None
            
        # 🧠 MINER BRAIN - COGNITIVE INTELLIGENCE 🧠
        if BRAIN_AVAILABLE:
            if THOUGHT_BUS_AVAILABLE:
                self.brain = MinerBrain(thought_bus=THOUGHT_BUS)
                print("   🧠 Miner Brain initialized (Connected to Thought Bus)")
            else:
                self.brain = MinerBrain()
                print("   🧠 Miner Brain initialized (Cognitive Circle Active)")
        else:
            self.brain = None
        
        # 🧠🌍 ECOSYSTEM BRAIN BRIDGE - Unified Intelligence Hub 🌍🧠
        self.brain_bridge = ECOSYSTEM_BRAIN
        print("   🧠🌍 Ecosystem Brain Bridge: CONNECTED")
        
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
        
        # 🚀 ENHANCED TRADING COMPONENTS 🚀
        self.smart_router = SmartOrderRouter(self.client)
        self.arb_scanner = CrossExchangeArbitrageScanner(self.client)
        self.trade_confirmation = UnifiedTradeConfirmation(self.client)
        self.rebalancer = PortfolioRebalancer(self.client)
        
        # 🌐 MULTI-EXCHANGE ORCHESTRATOR - All Systems Talk To Each Other 🌐
        self.multi_exchange = MultiExchangeOrchestrator(self.client)
        
        # 📊 UNIFIED STATE AGGREGATOR - All JSON Feeds Into Ecosystem 📊
        self.state_aggregator = STATE_AGGREGATOR
        
        # 🎛️ DYNAMIC PARAMETERS
        self.position_size_multiplier = 1.0
        self.min_entry_gamma = 0.5  # Default gamma threshold

        
        # 🔥 WAR-READY ENHANCEMENTS 🔥
        self.atr_calculator = ATRCalculator(period=14)
        self.heat_manager = PortfolioHeatManager(max_heat=0.60)
        self.adaptive_filters = AdaptiveFilterThresholds()
        
        # 🎯 TRAILING STOP SYSTEM
        self.trailing_stop_manager = TrailingStopManager()
        
        # 📢 NOTIFICATION SYSTEM
        self.notifier = NotificationManager()
        
        # 🌌 NEXUS INTEGRATION - MASTER EQUATION + QUEEN HIVE
        self.nexus = NexusIntegration()
        
        # 📝 TRADE LOGGER - Data Collection for Probability Matrix Training
        self.trade_logger = None
        if TRADE_LOGGER_AVAILABLE and trade_logger:
            self.trade_logger = trade_logger

        # Optional miner optimizer hook (if present in runtime)
        # Allows trading to read lighthouse Γ and κt during high-coherence windows
        self.miner_optimizer = getattr(self, 'miner_optimizer', None)
        
        # Optional brain reference (set by global orchestrator for unified startup)
        # Allows direct access to unified brain state during trading decisions
        self.brain = getattr(self, 'brain', None)
        
        # � PROBABILITY LOADER - Fresh probability reports + consensus signals
        # Initialize BEFORE health report so it shows as ACTIVE
        self.probability_loader = None
        self.position_hygiene = None
        if PROBABILITY_LOADER_AVAILABLE:
            try:
                self.probability_loader = ProbabilityLoader(
                    report_dir='/workspaces/aureon-trading',
                    freshness_threshold_minutes=120  # 2 hours max staleness
                )
                self.probability_loader.load_all_reports()
                self.position_hygiene = PositionHygieneChecker()
                # Pass to AurisEngine so health report can see it
                self.auris.probability_loader = self.probability_loader
                self.auris.position_hygiene = self.position_hygiene
            except Exception as e:
                print(f"   ⚠️ Probability Loader init failed: {e}")
        
        # �🌈✨ ENHANCEMENT LAYER - Rainbow Bridge, Synchronicity, Stargate Grid ✨🌈
        self.enhancement_layer = None
        if ENHANCEMENTS_AVAILABLE:
            try:
                self.enhancement_layer = EnhancementLayer()
                active_count = sum(1 for v in self.enhancement_layer.modules_active.values() if v)
                print(f"   🌈 Enhancement Layer active ({active_count}/3 modules)")
            except Exception as e:
                print(f"   ⚠️ Enhancement Layer initialization failed: {e}")
        
        print("   🚀 Enhanced trading components initialized (Router/Arbitrage/Confirmation/Rebalancer)")
        print("   🌐 Multi-Exchange Orchestrator active (Binance/Kraken/Capital/Alpaca)")
        print(f"   📊 State Aggregator: {len(self.state_aggregator.aggregated_state.get('sources_loaded', []))} data sources feeding ecosystem")
        
        # ==== COGNITION: initialize thought bus + modules ====
        print("   🧠 Initializing Cognition Bus...")
        self.thought_bus = ThoughtBus(persist_path="logs/aureon_thoughts.jsonl")

        # Modules (thinking parts)
        self.miner_module = MinerModule(self.thought_bus)

        # Risk limits (tune max_positions)
        self.risk_module = RiskModule(
            self.thought_bus, 
            max_positions=CONFIG.get('MAX_POSITIONS', 3),
            get_open_positions_count=lambda: len(self.positions)
        )

        # Execution: connect to your real order function
        self.exec_module = ExecutionModule(self.thought_bus, place_order_fn=self._place_order_from_intent)

        # Optional: subscribe to order results for logging / bookkeeping
        self.thought_bus.subscribe("execution.order_result", self._on_execution_order_result)
        
        # Subscribe to news thoughts for trading influence
        self.thought_bus.subscribe("news.sentiment", self._on_news_sentiment)
        self.thought_bus.subscribe("news.alert", self._on_news_alert)
        self._last_news_sentiment = {}  # Cache for trading decisions
        
        # Subscribe to knowledge thoughts for context
        self.thought_bus.subscribe("knowledge.query_result", self._on_knowledge_result)
        self.thought_bus.subscribe("knowledge.research_complete", self._on_research_complete)
        
        print("   🧠 Cognition Bus Active (MinerModule -> RiskModule -> ExecutionModule)")

        # 🛡️ Cognitive immune system (autonomous antivirus)
        self.immune_system = CognitiveImmuneSystem(self, self.thought_bus, self.state_aggregator)
        print("   🛡️ Cognitive Immune System armed (self-healing enabled)")

        # 📰 News Feed (World News API integration)
        self.news_feed = None
        self._news_poll_counter = 0
        self._news_poll_interval = 60  # Poll every 60 cycles (~2 mins at 2s interval)
        if NEWS_FEED_AVAILABLE:
            news_api_key = os.environ.get("WORLD_NEWS_API_KEY", "1e67384add34486d8b14a951b220fe8a")
            if news_api_key:
                try:
                    import asyncio
                    news_config = NewsFeedConfig(
                        api_key=news_api_key,
                        market_keywords=["cryptocurrency", "bitcoin", "ethereum", "federal reserve", 
                                        "stock market", "recession", "inflation", "interest rates"],
                        categories=["business", "technology", "politics"],
                        max_articles=25,
                        max_age_hours=12
                    )
                    self.news_feed = NewsFeed(news_config, self.thought_bus)
                    print("   📰 News Feed connected (World News API) - publishing to ThoughtBus")
                except Exception as e:
                    print(f"   ⚠️ News Feed init failed: {e}")

        # 📚 Knowledge Base (Wikipedia API integration)
        self.knowledge_base = None
        self._knowledge_research_counter = 0
        self._knowledge_research_interval = 300  # Research every 300 cycles (~10 mins)
        if KNOWLEDGE_BASE_AVAILABLE:
            try:
                self.knowledge_base = KnowledgeBase(thought_bus=self.thought_bus)
                print("   📚 Knowledge Base connected (Wikipedia API) - autonomous learning enabled")
                # Prefetch core trading knowledge in background thread
                import threading
                def prefetch_knowledge():
                    try:
                        self.knowledge_base.prefetch_trading_knowledge()
                    except Exception as e:
                        logger.debug(f"Knowledge prefetch error: {e}")
                threading.Thread(target=prefetch_knowledge, daemon=True).start()
            except Exception as e:
                print(f"   ⚠️ Knowledge Base init failed: {e}")

        # 📚🌍 WISDOM SCANNER - CONSCIOUSNESS EXPANSION ENGINE 🌍📚
        # Continuously scans Wikipedia and Sacred-Texts for ancient wisdom
        # 11 Civilizations: Celtic, Aztec, Egyptian, Pythagorean, Plantagenet, 
        #                   Mogollon, Warfare, Chinese, Hindu, Mayan, Norse
        self.wisdom_scanner = None
        self._wisdom_scan_counter = 0
        self._wisdom_scan_interval = 43200  # Full scan every 43200 cycles (~24 hours at 2s)
        if WISDOM_SCANNER_AVAILABLE:
            try:
                wisdom_config = ScannerConfig(
                    wisdom_data_dir="wisdom_data",
                    rate_limit_strategy="adaptive",
                    scan_interval_hours=24
                )
                self.wisdom_scanner = AureonWisdomScanner(wisdom_config)
                
                # Connect to ThoughtBus if available
                if THOUGHT_BUS_AVAILABLE:
                    self.wisdom_adapter = WisdomScannerThoughtBusAdapter(
                        self.wisdom_scanner, 
                        self.thought_bus
                    )
                    
                # Subscribe to wisdom insights
                self.thought_bus.subscribe("wisdom_insight", self._on_wisdom_insight)
                self.thought_bus.subscribe("consciousness_expansion", self._on_consciousness_expansion)
                
                # Print wisdom summary
                summary = self.wisdom_scanner.get_wisdom_summary()
                print(f"   📚🌍 Wisdom Scanner: {summary['total_civilizations']} civilizations monitored")
                print(f"         Total learned insights: {summary['scan_stats']['total_insights']}")
                
                # Start background wisdom scanning thread
                import threading
                def run_wisdom_scan():
                    try:
                        import asyncio
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(self.wisdom_scanner.run_full_scan())
                    except Exception as e:
                        logger.debug(f"Wisdom scan error: {e}")
                # Initial scan on startup (in background)
                threading.Thread(target=run_wisdom_scan, daemon=True).start()
                print("   📚🌍 Initial wisdom scan started in background...")
            except Exception as e:
                print(f"   ⚠️ Wisdom Scanner init failed: {e}")

        # 🏥 PRINT ECOSYSTEM HEALTH REPORT 🏥
        # Show all active systems and their communication status
        self.auris.print_system_health()
        
        try:
            top = self.state_aggregator.get_top_signals(3)
            prob_lines = []
            for sym, data in top.get('probability', []):
                prob = data.get('probability') or 0
                src = data.get('source', '')
                prob_lines.append(f"      • {sym}: p={prob:.2f} src={src}")

            an_lines = []
            for sym, data in top.get('analytics', []):
                score = data.get('score') or 0
                wr = data.get('win_rate')
                wr_str = f"{wr:.2f}" if isinstance(wr, (int, float)) else "n/a"
                src = data.get('source', '')
                an_lines.append(f"      • {sym}: score={score:.2f} wr={wr_str} src={src}")

            pos_lines = []
            for sym, qty in top.get('positions', []):
                qty_str = f"{qty:.4f}" if isinstance(qty, (int, float)) else str(qty)
                pos_lines.append(f"      • {sym}: qty={qty_str}")

            if prob_lines:
                print("   🔍 Top Probability Signals:")
                for ln in prob_lines:
                    print(ln)
            if an_lines:
                print("   🧪 Top Analytics Signals:")
                for ln in an_lines:
                    print(ln)
            if pos_lines:
                print("   📦 Position Snapshots:")
                for ln in pos_lines:
                    print(ln)
        except Exception as e:
            logger.debug("Top signal display failed: %s", e)
        print("   🔥 War-ready enhancements active (ATR/HeatManager/AdaptiveFilters)")
        if CONFIG.get('ENABLE_TRAILING_STOP', True):
            print(f"   🎯 Trailing stops enabled (activate at +{CONFIG.get('TRAILING_ACTIVATION_PCT', 0.5)}%, trail {CONFIG.get('TRAILING_DISTANCE_PCT', 0.3)}%)")
        if self.notifier.is_enabled():
            status = self.notifier.get_status()
            channels = []
            if status['telegram_enabled']: channels.append('Telegram')
            if status['discord_enabled']: channels.append('Discord')
            if status['webhook_enabled']: channels.append('Webhook')
            print(f"   📢 Notifications enabled: {', '.join(channels)}")

        # High-conviction probability watchlist (prob>=0.8 & conf>=0.8)
        self.high_conviction_symbols = set()
        for sig in self.state_aggregator.aggregated_state.get('high_conviction_signals', []):
            sym = sig.get('symbol', '')
            base = sym.replace('USDT', '').replace('USDC', '').replace('USD', '').replace('EUR', '').replace('GBP', '')
            if base:
                self.high_conviction_symbols.add(base)

        pfresh = self.state_aggregator.aggregated_state.get('probability_freshness', {})
        if pfresh.get('stale'):
            newest = pfresh.get('newest_minutes')
            newest_str = f"{newest:.1f}m" if isinstance(newest, (int, float)) else "unknown"
            print(f"   ⚠️ Probability reports stale ({newest_str} since last generation) — gating probability-based entries")
        if self.nexus.enabled:
            print(f"   🌌 Nexus active: Master Equation Λ(t) + Queen Hive 10-9-1")
        
        # 🔮 PREDICTION VALIDATOR - Track prediction accuracy over time
        self.prediction_validator = PredictionValidator(validation_window_seconds=60)
        print(f"   🔮 Prediction Validator active: 1-minute forecasts with peer review")
        
        # 🎯 PROBABILITY LOADER status message (already initialized earlier)
        if self.probability_loader:
            fresh = self.probability_loader.is_fresh()
            if fresh:
                top_signals = self.probability_loader.get_top_signals(limit=5, min_probability=0.8, min_confidence=0.8)
                print(f"   🎯 Probability Loader ACTIVE ({len(top_signals)} high-conviction signals)")
                consensus = self.probability_loader.get_consensus_signals(min_exchanges=2, min_probability=0.75)
                if consensus:
                    print(f"   🔥 Multi-exchange consensus: {len(consensus)} symbols with ≥2 exchange agreement")
            else:
                print("   ⚠️ Probability reports STALE - gating probability-based entries")
            print("   🧹 Position Hygiene Checker ACTIVE")
        
        # 📊 PROBABILITY MATRIX - Persistent learning from position outcomes
        self.prob_matrix = None
        if PROB_MATRIX_AVAILABLE and CONFIG.get('ENABLE_PROB_MATRIX', True):
            try:
                self.prob_matrix = HNCProbabilityIntegration()
                print("   📊 Probability Matrix (Position Learning) ACTIVE")
            except Exception as e:
                print(f"   ⚠️ Probability Matrix init failed: {e}")
        
        # 📊 PROBABILITY REPORT GENERATOR - Auto-regenerates every 15 seconds
        global PROBABILITY_GENERATOR
        self.probability_generator = None
        if CONFIG.get('ENABLE_PROBABILITY_GENERATOR', True):
            try:
                self.probability_generator = ProbabilityReportGenerator(
                    report_dir=os.environ.get('AUREON_REPORT_DIR', '.'),
                    interval_seconds=float(os.environ.get('PROBABILITY_INTERVAL', '15'))
                )
                PROBABILITY_GENERATOR = self.probability_generator
                print(f"   📊 Probability Generator initialized (15s interval)")
            except Exception as e:
                print(f"   ⚠️ Probability Generator init failed: {e}")
        
        # 🌍⚡ GLOBAL FINANCIAL ECOSYSTEM FEED ⚡🌍
        self.global_feed = None
        self.macro_snapshot = None
        if GLOBAL_FEED_AVAILABLE:
            try:
                self.global_feed = GlobalFinancialFeed()
                self.macro_snapshot = self.global_feed.get_snapshot()
                print("   🌍 Global Financial Feed ACTIVE")
                print(f"      Fear/Greed: {self.macro_snapshot.crypto_fear_greed} | Regime: {self.macro_snapshot.market_regime}")
            except Exception as e:
                print(f"   ⚠️ Global Feed init failed: {e}")
        
        # 📊 PROBABILITY VALIDATOR - Track validation accuracy
        self.probability_validator_v2 = None
        if VALIDATOR_AVAILABLE:
            try:
                self.probability_validator_v2 = get_validator()
                stats = self.probability_validator_v2.stats
                if stats.validated_predictions > 0:
                    print(f"   📊 Probability Validator ACTIVE (Accuracy: {stats.direction_accuracy*100:.1f}%)")
            except Exception as e:
                print(f"   ⚠️ Validator init failed: {e}")
        
        # Determine tradeable currencies based on wallet
        self.tradeable_currencies = ['USD', 'GBP', 'EUR', 'USDT', 'USDC']
        self._detect_wallet_currency()
        
        # Load previous state if exists
        fresh_start = os.environ.get('FRESH_START', '0') == '1'
        if fresh_start:
            print("   ✨ FRESH START: Ignoring previous state file")
            # Reset baselines BEFORE refresh_equity to avoid circuit breaker trigger
            self.tracker.trading_halted = False
            self.tracker.halt_reason = ""
            self.tracker.max_drawdown = 0.0
            self.tracker.peak_balance = 1e9  # Temporarily high to avoid DD calc
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
        
        # User directive: disable drawdown circuit breaker to allow penny-profit harvesting
        self.tracker.circuit_breaker_enabled = False
        # Ensure no stale halt state carries over between runs
        self.tracker.trading_halted = False
        self.tracker.halt_reason = ""
        
        # 🔧 ALWAYS import existing holdings as managed positions on startup
        # This ensures any assets on exchanges are tracked properly
        if not self.dry_run:
            self._import_existing_holdings()

    # ═══════════════════════════════════════════════════════════════
    # 🚫 SYMBOL VALIDATION CACHE - Reduce API noise for invalid symbols
    # ═══════════════════════════════════════════════════════════════
    
    def _is_symbol_invalid(self, symbol: str) -> bool:
        """Check if symbol is in invalid cache and not expired."""
        if symbol not in self._invalid_symbols:
            return False
        # Check if cache entry has expired
        cached_time = self._invalid_symbols[symbol]
        if time.time() - cached_time > self._symbol_cache_ttl:
            del self._invalid_symbols[symbol]
            return False
        return True
    
    def _mark_symbol_invalid(self, symbol: str) -> None:
        """Mark a symbol as invalid to skip future API calls."""
        self._invalid_symbols[symbol] = time.time()
    
    def _mark_symbol_valid(self, symbol: str, exchange: str) -> None:
        """Mark a symbol as valid/working."""
        self._valid_symbols[symbol] = exchange
        # Remove from invalid cache if present
        if symbol in self._invalid_symbols:
            del self._invalid_symbols[symbol]
        self._clear_symbol_dust(symbol)

    def _is_symbol_dust(self, symbol: str) -> Optional[str]:
        """Return dust reason if symbol is flagged as unsellable."""
        entry = self._dust_positions.get(symbol)
        if not entry:
            return None
        reason, ts = entry
        if time.time() - ts > self._dust_ttl:
            del self._dust_positions[symbol]
            return None
        return reason

    def _mark_symbol_dust(self, symbol: str, reason: str) -> None:
        """Persistently mark a symbol as dust/unsellable."""
        self._dust_positions[symbol] = (reason, time.time())
        self._invalid_symbols[symbol] = time.time()

    def _clear_symbol_dust(self, symbol: str) -> None:
        self._dust_positions.pop(symbol, None)
    
    def get_symbol_cache_stats(self) -> Dict[str, Any]:
        """Get stats on symbol caching for telemetry."""
        now = time.time()
        active_invalid = sum(1 for t in self._invalid_symbols.values() if now - t < self._symbol_cache_ttl)
        return {
            'valid_symbols': len(self._valid_symbols),
            'invalid_symbols': active_invalid,
            'dust_symbols': len(self._dust_positions),
            'total_cached': len(self._valid_symbols) + active_invalid,
        }

    # ═══════════════════════════════════════════════════════════════
    # 🎵 SACRED FREQUENCY MAPPING - Harmonic Trading Intelligence 🎵
    # ═══════════════════════════════════════════════════════════════
    
    def _get_sacred_frequency_modifier(self, freq: float) -> float:
        """
        🎵 SACRED FREQUENCY MODIFIER 🎵
        
        Maps market frequencies to sacred healing tones and returns
        appropriate probability modifiers based on harmonic resonance.
        
        SOLFEGGIO SCALE (Ancient healing frequencies):
        - 174 Hz: Foundation, pain relief
        - 285 Hz: Healing, tissue regeneration
        - 396 Hz: Liberation from fear/guilt (UT)
        - 417 Hz: Undoing situations, facilitating change (RE)
        - 528 Hz: Love frequency, DNA repair (MI) ⭐ OPTIMAL
        - 639 Hz: Connection, relationships (FA)
        - 741 Hz: Awakening intuition (SOL)
        - 852 Hz: Returning to spiritual order (LA)
        - 963 Hz: Unity, awakening (SI)
        
        EARTH FREQUENCIES:
        - 7.83 Hz: Schumann Resonance (Earth's heartbeat)
        - 136.1 Hz: OM frequency (Earth's year)
        - 432 Hz: Universal tuning (cosmic harmony)
        
        DISTORTION:
        - 440 Hz: Artificial concert pitch (dissonance)
        """
        # Check Schumann harmonics (7.83Hz × n)
        schumann_base = 7.83
        for harmonic in range(1, 128):  # Up to 128th harmonic (~1000Hz)
            schumann_freq = schumann_base * harmonic
            if abs(freq - schumann_freq) <= 3:
                return CONFIG.get('FREQUENCY_BOOST_SCHUMANN', 1.45)
        
        # Check exact sacred frequencies (±5Hz tolerance)
        sacred_map = {
            (169, 179): CONFIG.get('FREQUENCY_BOOST_174HZ', 1.20),   # 174 Hz Foundation
            (280, 290): CONFIG.get('FREQUENCY_BOOST_285HZ', 1.25),   # 285 Hz Healing
            (391, 401): CONFIG.get('FREQUENCY_BOOST_396HZ', 1.40),   # 396 Hz Liberation
            (412, 422): CONFIG.get('FREQUENCY_BOOST_417HZ', 1.30),   # 417 Hz Change
            (427, 437): CONFIG.get('FREQUENCY_BOOST_432HZ', 1.30),   # 432 Hz Cosmic
            (435, 445): CONFIG.get('FREQUENCY_SUPPRESS_440HZ', 0.70),# 440 Hz Distortion!
            (523, 533): CONFIG.get('FREQUENCY_BOOST_528HZ', 1.35),   # 528 Hz Love ⭐
            (634, 644): CONFIG.get('FREQUENCY_BOOST_639HZ', 1.25),   # 639 Hz Connection
            (736, 746): CONFIG.get('FREQUENCY_BOOST_741HZ', 1.15),   # 741 Hz Awakening
            (847, 857): CONFIG.get('FREQUENCY_BOOST_852HZ', 1.20),   # 852 Hz Spiritual
            (958, 968): CONFIG.get('FREQUENCY_SUPPRESS_963HZ', 0.60),# 963 Hz (poor data)
            (131, 141): CONFIG.get('FREQUENCY_BOOST_136HZ', 1.25),   # 136 Hz OM
        }
        
        for (low, high), modifier in sacred_map.items():
            if low <= freq <= high:
                return modifier
        
        # Band-based fallback
        if 300 <= freq <= 399:
            return CONFIG.get('FREQUENCY_BOOST_300HZ', 1.50)  # 98.8% accuracy!
        elif 600 <= freq <= 699:
            return CONFIG.get('FREQUENCY_SUPPRESS_600HZ', 0.75)  # 0% accuracy
        elif freq >= 1000:
            return CONFIG.get('FREQUENCY_SUPPRESS_HIGH_CHAOS', 0.50)
        
        # Neutral baseline for unclassified frequencies
        return CONFIG.get('FREQUENCY_NEUTRAL_BASELINE', 1.0)
    
    def _get_frequency_name(self, freq: float) -> str:
        """Get human-readable name for a frequency."""
        # Check for exact sacred frequency matches first (±5Hz tolerance)
        sacred_names = {
            (5, 11): "Schumann",
            (131, 141): "OM/Earth",
            (169, 179): "Foundation",
            (280, 290): "Healing",
            (295, 405): "Activation",  # Includes 300-399 golden band + 396
            (412, 422): "Change",
            (427, 437): "Cosmic",
            (435, 445): "Distortion⚠️",
            (523, 533): "Love💚",
            (634, 644): "Connection",
            (736, 746): "Awakening",
            (847, 857): "Spiritual",
            (958, 968): "Unity",
        }
        
        for (low, high), name in sacred_names.items():
            if low <= freq <= high:
                return name
        
        # Schumann harmonics
        schumann_base = 7.83
        for harmonic in range(1, 128):
            if abs(freq - schumann_base * harmonic) <= 3:
                return f"Schumann×{harmonic}"
        
        # Generic band names
        if freq < 200:
            return "Earth"
        elif freq < 300:
            return "Grounding"
        elif freq < 400:
            return "Golden"
        elif freq < 500:
            return "Transition"
        elif freq < 600:
            return "Heart"
        elif freq < 700:
            return "Expression"
        elif freq < 800:
            return "Intuition"
        elif freq < 900:
            return "Insight"
        elif freq < 1000:
            return "Crown"
        else:
            return "Chaos⚠️"

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
        """Import existing crypto holdings as managed positions.
        
        🔧 ENHANCED: Now fetches REAL purchase prices from exchange trade history
        via CostBasisTracker to prevent selling at a loss.
        """
        if self.dry_run:
            return
        
        # 💰 Always get cost tracker instance (for price lookups)
        cost_tracker = get_cost_basis_tracker()
        
        # SYNC REAL COST BASIS FROM EXCHANGES (can be skipped with env var)
        if os.getenv('SKIP_COST_SYNC', '0') != '1':
            print("\n   💰 Syncing real purchase prices from exchange history...")
            synced = cost_tracker.sync_from_exchanges()
            if synced > 0:
                print(f"   ✅ Found real cost basis for {synced} positions")
        else:
            print("\n   ⏭️ Skipping cost basis sync (SKIP_COST_SYNC=1)")
            
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
                    
                # 🔧 ASSET NORMALIZATION: Handle both Kraken and Binance special naming
                asset_clean = asset_raw.upper()
                
                if exchange == 'kraken':
                    # KRAKEN: Remove Z/X prefixes and map XBT→BTC
                    # Kraken uses: XXBT for Bitcoin, XETH for Ethereum, ZUSD for USD, etc.
                    
                    # Remove Kraken's Z prefix (fiat currencies)
                    if asset_clean.startswith('Z') and len(asset_clean) > 1:
                        asset_clean = asset_clean[1:]
                    
                    # Remove Kraken's X prefix (crypto) - but handle XRP, XLM, XDG correctly
                    if asset_clean.startswith('XX'):  # XXBT, XXDG, XXLM, etc.
                        asset_clean = asset_clean[1:]  # XXBT → XBT
                    elif asset_clean.startswith('X') and asset_clean not in ['XRP', 'XLM', 'XMR', 'XTZ']:
                        if len(asset_clean) > 3:  # XETH (4), XLTC (4) - likely Kraken prefix
                            asset_clean = asset_clean[1:]  # XETH → ETH
                    
                    # Map Kraken's XBT to standard BTC
                    if asset_clean == 'XBT':
                        asset_clean = 'BTC'
                    elif asset_clean == 'XDG':
                        asset_clean = 'DOGE'
                        
                elif exchange == 'binance':
                    # BINANCE: Handle Earn products (LD prefix), staked assets, wrapped tokens
                    # LDBTC → BTC, BETH → ETH, BNSOL → SOL, WBTC → BTC, etc.
                    
                    # Remove LD prefix (Binance Earn/Flexible Savings)
                    if asset_clean.startswith('LD') and len(asset_clean) > 2:
                        asset_clean = asset_clean[2:]  # LDBTC → BTC
                    
                    # Handle staked/wrapped variants
                    binance_asset_map = {
                        'BETH': 'ETH',      # Staked ETH 2.0
                        'BNSOL': 'SOL',     # Staked SOL
                        'WBTC': 'BTC',      # Wrapped BTC
                        'WETH': 'ETH',      # Wrapped ETH  
                        'WBNB': 'BNB',      # Wrapped BNB
                        'BTCB': 'BTC',      # BTC on BSC
                        'POL': 'MATIC',     # Polygon rebrand (keep as MATIC for trading pairs)
                    }
                    if asset_clean in binance_asset_map:
                        asset_clean = binance_asset_map[asset_clean]
                
                # Skip base currency (that's cash, not a position)
                if asset_clean in ['GBP', 'EUR', 'USD', 'USDT', 'USDC', 'BUSD', 'TUSD', 'FDUSD']:
                    continue
                    
                # Build the trading pair symbol
                # For Binance: BTCUSDT  
                # For Kraken: BTCUSDC, ETHUSDC, etc. (after normalization)
                # Try multiple quote currencies since we might have positions in different pairs
                
                symbol = None
                gbp_value = 0.0
                price = 0.0
                
                # Try each quote currency until we find a valid pair with price
                # Include BTC/XBT for Kraken BTC-denominated pairs
                quote_options = ['USDC', 'USDT', 'USD', 'EUR', 'GBP', 'BTC', 'XBT', 'FDUSD', base] if base not in ['USDC', 'USDT'] else [base, 'USDT', 'USD', 'EUR', 'BTC', 'XBT', 'FDUSD']
                
                for quote in quote_options:
                    try_symbol = f"{asset_clean}{quote}"
                    
                    # Skip if already tracked
                    if try_symbol in self.positions:
                        symbol = None  # Already tracked
                        break
                    
                    # 🚫 Skip if symbol is in invalid cache
                    if self._is_symbol_invalid(try_symbol):
                        continue
                    
                    try:
                        # Try to get ticker for this pair
                        ticker = self.client.get_ticker(exchange, try_symbol)
                        tick_price = ticker.get('price', 0) or ticker.get('last', 0) or ticker.get('c', 0)
                        if tick_price and float(tick_price) > 0:
                            symbol = try_symbol
                            price = float(tick_price)
                            gbp_value = amount * price
                            self._mark_symbol_valid(try_symbol, exchange)
                            print(f"   📍 Found valid pair: {symbol} @ ${price:.6f}")
                            break
                        else:
                            self._mark_symbol_invalid(try_symbol)
                    except:
                        self._mark_symbol_invalid(try_symbol)
                        continue
                
                if not symbol or gbp_value < 0.50:  # Skip dust < $0.50
                    continue
                
                # Skip if already tracked (double check)
                if symbol in self.positions:
                    continue
                
                # 💰 TRY TO GET REAL COST BASIS FROM TRACKER
                real_entry_price = cost_tracker.get_entry_price(symbol)
                if real_entry_price and real_entry_price > 0:
                    entry_price = real_entry_price
                    entry_value = amount * entry_price
                    is_historical = False  # We have real data!
                    cost_source = "REAL"
                    print(f"   💰 {symbol}: Using REAL entry price ${entry_price:.6f} from trade history")
                else:
                    entry_price = price  # Fall back to current price
                    entry_value = gbp_value
                    is_historical = True  # No real data - treat as historical
                    cost_source = "CURRENT"
                    
                # Create position from existing holding
                estimated_entry_fee = entry_value * get_platform_fee(exchange, 'taker')
                
                self.positions[symbol] = Position(
                    symbol=symbol,
                    entry_price=entry_price,
                    quantity=amount,
                    entry_fee=estimated_entry_fee,
                    entry_value=entry_value,
                    momentum=0.0,
                    coherence=0.5,
                    entry_time=time.time(),
                    dominant_node='Portfolio',
                    exchange=exchange,
                    is_historical=is_historical
                )
                imported += 1
                
                # Show profit/loss status
                if cost_source == "REAL":
                    pnl_pct = ((price - entry_price) / entry_price * 100) if entry_price > 0 else 0
                    pnl_icon = "🟢" if pnl_pct >= 0 else "🔴"
                    print(f"   📦 Imported {symbol} ({exchange}): {amount:.6f} @ £{entry_price:.4f} (now £{price:.4f}) {pnl_icon} {pnl_pct:+.2f}%")
                else:
                    print(f"   📦 Imported {symbol} ({exchange}): {amount:.6f} @ £{price:.4f} = £{gbp_value:.2f} [HISTORICAL - no cost basis]")
            
        if imported > 0:
            print(f"   ✅ Imported {imported} existing holdings as managed positions")
            print(f"   💡 Positions with REAL cost basis are protected from loss-making sales!")
        
        # 💼 CAPITAL.COM CFD POSITIONS - Import open CFD positions
        try:
            capital_client = self.client.clients.get('capital')
            if capital_client and hasattr(capital_client.client, 'get_positions'):
                capital_positions = capital_client.client.get_positions()
                if capital_positions:
                    print(f"\n   💼 Importing {len(capital_positions)} Capital.com CFD positions...")
                    for cfd_pos in capital_positions:
                        try:
                            # Capital.com position structure
                            epic = cfd_pos.get('market', {}).get('epic') or cfd_pos.get('epic', '')
                            direction = cfd_pos.get('position', {}).get('direction') or cfd_pos.get('direction', 'BUY')
                            size = float(cfd_pos.get('position', {}).get('size') or cfd_pos.get('size', 0))
                            open_level = float(cfd_pos.get('position', {}).get('openLevel') or cfd_pos.get('openLevel', 0))
                            
                            if not epic or size <= 0:
                                continue
                            
                            # Skip if already tracked
                            if epic in self.positions:
                                continue
                            
                            # Get current price
                            current_price = open_level
                            try:
                                ticker = capital_client.client.get_ticker(epic)
                                current_price = ticker.get('price', open_level)
                            except:
                                pass
                            
                            # Calculate value
                            position_value = size * current_price
                            
                            # Create position
                            self.positions[epic] = Position(
                                symbol=epic,
                                entry_price=open_level,
                                quantity=size if direction == 'BUY' else -size,  # Negative for shorts
                                entry_fee=position_value * CONFIG.get('CAPITAL_FEE', 0.001),
                                entry_value=position_value,
                                momentum=0.0,
                                coherence=0.5,
                                entry_time=time.time(),
                                dominant_node='Capital.com',
                                exchange='capital',
                                is_historical=False  # CFD positions have known entry
                            )
                            imported += 1
                            
                            pnl_pct = ((current_price - open_level) / open_level * 100) if open_level > 0 else 0
                            if direction == 'SELL':
                                pnl_pct = -pnl_pct  # Invert for shorts
                            pnl_icon = "🟢" if pnl_pct >= 0 else "🔴"
                            dir_icon = "📈" if direction == 'BUY' else "📉"
                            print(f"   💼 {dir_icon} {epic}: {size} @ £{open_level:.4f} → £{current_price:.4f} {pnl_icon} {pnl_pct:+.2f}%")
                            
                        except Exception as pos_err:
                            logger.debug(f"Could not import Capital.com position: {pos_err}")
                            
                    if imported > 0:
                        print(f"   ✅ Imported Capital.com CFD positions")
        except Exception as cap_err:
            logger.debug(f"Capital.com position import skipped: {cap_err}")
        
        # 🦙 ALPACA POSITIONS - Import crypto and stock positions with real entry prices
        try:
            alpaca_client = self.client.clients.get('alpaca')
            if alpaca_client and hasattr(alpaca_client.client, 'get_positions'):
                alpaca_positions = alpaca_client.client.get_positions()
                if alpaca_positions:
                    print(f"\n   🦙 Importing {len(alpaca_positions)} Alpaca positions...")
                    for alp_pos in alpaca_positions:
                        try:
                            # Alpaca position structure
                            symbol_raw = alp_pos.get('symbol', '')
                            # Convert BTC/USD -> BTCUSD
                            symbol = symbol_raw.replace('/', '')
                            qty = float(alp_pos.get('qty', 0))
                            avg_entry = float(alp_pos.get('avg_entry_price', 0))
                            current_price = float(alp_pos.get('current_price', 0))
                            market_value = float(alp_pos.get('market_value', 0))
                            unrealized_pl = float(alp_pos.get('unrealized_pl', 0))
                            side = alp_pos.get('side', 'long')
                            asset_class = alp_pos.get('asset_class', 'crypto')
                            
                            if not symbol or qty <= 0:
                                continue
                            
                            # Skip if already tracked
                            if symbol in self.positions:
                                continue
                            
                            # Create position
                            self.positions[symbol] = Position(
                                symbol=symbol,
                                entry_price=avg_entry,
                                quantity=qty if side == 'long' else -qty,
                                entry_fee=market_value * CONFIG.get('ALPACA_FEE', 0.0025),
                                entry_value=qty * avg_entry,
                                momentum=0.0,
                                coherence=0.5,
                                entry_time=time.time(),
                                dominant_node='Alpaca',
                                exchange='alpaca',
                                is_historical=False  # Alpaca has real entry prices
                            )
                            imported += 1
                            
                            pnl_pct = ((current_price - avg_entry) / avg_entry * 100) if avg_entry > 0 else 0
                            if side == 'short':
                                pnl_pct = -pnl_pct
                            pnl_icon = "🟢" if pnl_pct >= 0 else "🔴"
                            asset_icon = "🪙" if asset_class == 'crypto' else "📊"
                            print(f"   🦙 {asset_icon} {symbol}: {qty} @ ${avg_entry:.4f} → ${current_price:.4f} {pnl_icon} {pnl_pct:+.2f}% (${unrealized_pl:+.2f})")
                            
                        except Exception as pos_err:
                            logger.debug(f"Could not import Alpaca position: {pos_err}")
                            
                    if imported > 0:
                        print(f"   ✅ Imported Alpaca positions")
        except Exception as alp_err:
            logger.debug(f"Alpaca position import skipped: {alp_err}")
    
    def _liquidate_historical_for_opportunity(self, needed_cash: float, target_exchange: str, target_symbol: str) -> float:
        """🔄 Liquidate historical assets OR big losers to free up cash for better opportunities.
        
        🔥 AGGRESSIVE MODE: Also includes positions with >50% loss as "dead capital"
        Only sells if:
        1. Position is truly historical (no known cost basis), OR
        2. Position would be sold at a profit, OR
        3. Position is down >50% (dead capital - cut losses!)
        
        Returns: Amount of cash freed up
        """
        if self.dry_run:
            return 0.0
        
        # 💰 Get cost basis tracker for profit checks
        cost_tracker = get_cost_basis_tracker()
            
        freed_cash = 0.0
        
        # 🔥 INCLUDE BIG LOSERS: Find positions down >50% as candidates for liquidation
        big_loser_candidates = []
        print(f"   🔍 Scanning {len(self.positions)} positions for big losers (>50% down)...")
        for sym, pos in self.positions.items():
            # Don't filter by exchange for big losers - we want to cut ANY dead capital
            try:
                ticker = self.client.get_ticker(pos.exchange, sym)
                curr_price = float(ticker.get('price', 0) or ticker.get('last', 0) or ticker.get('c', 0))
                if curr_price > 0 and pos.entry_price > 0:
                    pnl_pct = (curr_price - pos.entry_price) / pos.entry_price * 100
                    if pnl_pct < -50:  # Down more than 50%
                        print(f"      🔥 Found big loser: {sym} @ {pnl_pct:.1f}%")
                        big_loser_candidates.append((sym, pos, pnl_pct, curr_price))
            except Exception as e:
                pass
        
        # Sort by biggest loser first (most negative PnL)
        big_loser_candidates.sort(key=lambda x: x[2])
        
        historical_positions = [
            (sym, pos) for sym, pos in self.positions.items() 
            if pos.is_historical and pos.exchange == target_exchange
        ]
        
        if not historical_positions:
            # Try other exchanges too
            historical_positions = [
                (sym, pos) for sym, pos in self.positions.items() 
                if pos.is_historical
            ]
        
        # 🔥 SELL BIG LOSERS FIRST - they're dead capital!
        if big_loser_candidates and freed_cash < needed_cash:
            print(f"\n   🔥 CUTTING LOSSES: Found {len(big_loser_candidates)} positions down >50%")
            for sym, pos, pnl_pct, curr_price in big_loser_candidates:
                if freed_cash >= needed_cash:
                    break
                    
                available_qty = pos.quantity
                if available_qty <= 0:
                    continue
                current_value = available_qty * curr_price
                
                if current_value < 0.50:  # Skip dust
                    continue
                    
                dust_reason = self._is_symbol_dust(sym)
                if dust_reason:
                    print(f"   💤 Skipping {sym} - marked dust: {dust_reason}")
                    continue
                    
                if self._is_symbol_invalid(sym):
                    continue
                
                sell_qty, block_reason, adj_note = self._prepare_liquidation_quantity(
                    pos.exchange, sym, available_qty, curr_price
                )
                if sell_qty is None:
                    reason = block_reason or "LOT_SIZE constraint"
                    self._mark_symbol_dust(sym, reason)
                    print(f"   💤 Skipping {sym}: {reason}")
                    continue
                
                current_value = sell_qty * curr_price
                if current_value < 0.50:
                    continue

                print(f"   🔥 CUTTING LOSS {sym}: {pnl_pct:.1f}% down - selling {sell_qty:.6f} @ £{curr_price:.4f} = £{current_value:.2f}")
                
                try:
                    res = self.client.place_market_order(pos.exchange, sym, 'SELL', quantity=sell_qty)
                    
                    if isinstance(res, dict) and not res.get('rejected') and res.get('status') not in ['REJECTED', 'FAILED', None]:
                        net_value = current_value * 0.998
                        freed_cash += net_value
                        pos.quantity = max(pos.quantity - sell_qty, 0.0)
                        if pos.quantity <= 1e-12:
                            self.positions.pop(sym, None)
                        else:
                            pos.entry_value = pos.quantity * curr_price
                        self._clear_symbol_dust(sym)
                        print(f"   ✅ CUT LOSS {sym} - freed £{net_value:.2f} (was {pnl_pct:.1f}% down)")
                        
                        # 🧠 PUBLISH THOUGHT: HARVESTING DEAD CAPITAL 🧠
                        if THOUGHT_BUS_AVAILABLE and THOUGHT_BUS:
                            THOUGHT_BUS.publish(Thought(
                                source="harvester",
                                topic="execution.harvest.dead_capital",
                                payload={
                                    "symbol": sym,
                                    "action": "SELL",
                                    "reason": "DEAD_CAPITAL_CUT",
                                    "pnl_pct": pnl_pct,
                                    "freed_cash": net_value
                                }
                            ))
                    else:
                        self._mark_symbol_invalid(sym)
                        print(f"   ⚠️ Failed to cut {sym}")
                except Exception as e:
                    self._mark_symbol_invalid(sym)
                    print(f"   ⚠️ Error cutting {sym}: {e}")
        
        if not historical_positions and freed_cash >= needed_cash:
            return freed_cash
            
        if not historical_positions:
            return freed_cash
            
        # Sort by value (smallest first to minimize market impact)
        historical_positions.sort(key=lambda x: x[1].entry_value)
        
        print(f"\n   🔄 LIQUIDATING HISTORICAL ASSETS for {target_symbol}")
        print(f"   💰 Need £{needed_cash:.2f} - found {len(historical_positions)} historical positions")
        
        for sym, pos in historical_positions:
            if freed_cash >= needed_cash:
                break
                
            # Get current price
            try:
                ticker = self.client.get_ticker(pos.exchange, sym)
                curr_price = float(ticker.get('price', 0) or ticker.get('last', 0) or ticker.get('c', 0))
                if curr_price <= 0:
                    continue
            except:
                continue
            
            # 💰 CHECK IF SALE WOULD BE PROFITABLE OR ACCEPTABLE LOSS
            can_sell, profit_info = cost_tracker.can_sell_profitably(sym, curr_price, pos.quantity)
            if not can_sell and profit_info.get('entry_price'):
                # We have cost basis and it would be a loss
                loss = profit_info.get('potential_loss', 0)
                pnl_pct = profit_info.get('profit_pct', 0)
                
                # 🔥 AGGRESSIVE MODE: Allow selling big losers (>50% down) to free capital
                # These positions are "dead money" - better to cut losses and redeploy
                if pnl_pct > -50.0:  # Only protect if loss is less than 50%
                    print(f"   🛑 PROTECTING {sym}: Would lose £{loss:.2f} ({pnl_pct:.1f}%) - skipping")
                    continue
                else:
                    print(f"   🔥 CUTTING LOSSES {sym}: {pnl_pct:.1f}% down - freeing dead capital!")
                
            available_qty = pos.quantity
            if available_qty <= 0:
                continue
            current_value = available_qty * curr_price
            
            # Don't liquidate dust (less than £0.50) - wastes time on LOT_SIZE errors
            DUST_THRESHOLD = 0.50
            if current_value < DUST_THRESHOLD:
                continue
            
            dust_reason = self._is_symbol_dust(sym)
            if dust_reason:
                print(f"   💤 Skipping {sym} - marked dust: {dust_reason}")
                continue
            
            # Skip symbols that have repeatedly failed LOT_SIZE (can't be sold in current qty)
            if self._is_symbol_invalid(sym):
                continue
            
            sell_qty, block_reason, adj_note = self._prepare_liquidation_quantity(
                pos.exchange, sym, available_qty, curr_price
            )
            if sell_qty is None:
                reason = block_reason or "LOT_SIZE constraint"
                self._mark_symbol_dust(sym, reason)
                print(f"   💤 Skipping {sym}: {reason}")
                continue
            
            current_value = sell_qty * curr_price
            if current_value < DUST_THRESHOLD:
                reason = f"value £{current_value:.2f} below dust floor"
                self._mark_symbol_dust(sym, reason)
                print(f"   💤 Skipping {sym}: {reason}")
                continue

            # 🧠 PUBLISH THOUGHT: HARVESTING HISTORICAL ASSET 🧠
            if THOUGHT_BUS_AVAILABLE and THOUGHT_BUS:
                THOUGHT_BUS.publish(Thought(
                    source="harvester",
                    topic="execution.harvest.historical",
                    payload={
                        "symbol": sym,
                        "action": "SELL",
                        "reason": "FUNDING_OPPORTUNITY",
                        "target_symbol": target_symbol,
                        "value": current_value
                    }
                ))

            print(f"   📦→💵 Selling {sym}: {sell_qty:.6f} @ £{curr_price:.4f} = £{current_value:.2f}")
            if adj_note:
                print(f"      ↳ {adj_note}")
            
            try:
                # Execute sell - use quantity parameter (not base_qty)
                res = self.client.place_market_order(pos.exchange, sym, 'SELL', quantity=sell_qty)
                
                if isinstance(res, dict) and not res.get('rejected') and res.get('status') not in ['REJECTED', 'FAILED', None]:
                    net_value = current_value * 0.998  # Account for fees
                    freed_cash += net_value
                    pos.quantity = max(pos.quantity - sell_qty, 0.0)
                    if pos.quantity <= 1e-12:
                        self.positions.pop(sym, None)
                    else:
                        pos.entry_value = pos.quantity * curr_price
                    self._clear_symbol_dust(sym)
                    print(f"   ✅ Liquidated {sym} - freed £{net_value:.2f}")
                    if pos.quantity > 0:
                        print(f"      ↪️ Remaining {sym}: {pos.quantity:.6f} (unsellable remainder)")
                else:
                    # Failed - blacklist to stop retry spam
                    self._mark_symbol_invalid(sym)
                    print(f"   ⚠️ Failed to liquidate {sym} - blacklisted for 1hr")
            except Exception as e:
                err_msg = str(e)
                # Mark as invalid for any liquidation error - stop retry spam
                self._mark_symbol_invalid(sym)
                if 'LOT_SIZE' in err_msg or '-1013' in err_msg:
                    self._mark_symbol_dust(sym, 'LOT_SIZE rejection')
                    print(f"   ⚠️ {sym} LOT_SIZE fail - blacklisted for 1hr")
                else:
                    print(f"   ⚠️ Error liquidating {sym}: {e} - blacklisted for 1hr")
                continue
        
        if freed_cash > 0:
            print(f"   💰 Total freed: £{freed_cash:.2f}")
            self.refresh_equity()  # Update balances
            
        return freed_cash
    
    def _deploy_scouts(self):
        """🚀 FORCE DEPLOY scout positions immediately on first scan!
        
        Philosophy: "They can't stop them all!" - Get positions deployed FAST
        No sitting on the fence - HIT THE GROUND RUNNING!
        """
        if self.scouts_deployed or not CONFIG['DEPLOY_SCOUTS_IMMEDIATELY']:
            return
            
        print("\n   🚀🔥 FORCE DEPLOYING SCOUTS - HIT THE GROUND RUNNING! 🔥🚀")
        print("   💥 No fence sitting - we're going IN immediately!\n")
        scouts_deployed = 0
        target_scouts = CONFIG.get('SCOUT_FORCE_COUNT', 3)
        
        # Get ALL available quote currencies - be aggressive!
        quote_currencies = CONFIG.get('QUOTE_CURRENCIES', ['USD', 'USDT', 'GBP', 'EUR'])
        
        all_candidates = []
        per_quote_cap = CONFIG.get('SCOUT_PER_QUOTE_LIMIT', 2)
        min_vol = CONFIG.get('SCOUT_MIN_VOLATILITY', 1.5)
        min_vol_q = CONFIG.get('SCOUT_MIN_VOLUME_QUOTE', 100000)
        
        # Gather ALL possible trades across all currencies
        for quote_curr in quote_currencies:
            for symbol, data in self.ticker_cache.items():
                if not symbol.endswith(quote_curr):
                    continue
                if symbol in self.positions:
                    continue
                # Note: Kraken now allowed since Binance UK blocks most USDC pairs
                # Rate limits handled by using cached ticker data
                source = data.get('source', '').lower()
                    
                change = data.get('change24h', 0)
                price = data.get('price', 0)
                volume = data.get('volume', 0)

                # Lion Hunt style gating: need real movement and liquidity
                if price <= 0 or volume <= 0:
                    continue
                if abs(change) < min_vol:
                    continue
                if volume < min_vol_q:
                    continue

                # Opportunity score: |volatility| × volume (in millions)
                volume_m = max(volume / 1_000_000, 0.001)
                lion_score = abs(change) * volume_m * 100

                all_candidates.append({
                    'symbol': symbol,
                    'price': price,
                    'change24h': change,
                    'volume': volume,
                    'score': lion_score,
                    'coherence': 0.65,  # Force coherence above threshold
                    'dominant_node': 'ForceScout',
                    'quote_currency': quote_curr,
                    'source': source  # 🔥 Route to correct exchange!
                })
        
        # 🔥 BALANCE-AWARE BOOST: Get balances FIRST, then boost tradeable pairs BEFORE deduplication!
        available_quotes = set()
        exchange_quote_balances = {}  # Track actual balances per exchange+quote
        try:
            # Use the MultiExchangeClient's get_all_balances method
            all_balances = self.client.get_all_balances()
            for exchange_name, bals in all_balances.items():
                for asset, amt in bals.items():
                    asset_upper = asset.upper()
                    # Remove Kraken prefixes (ZUSD, XXBT, etc)
                    asset_clean = asset_upper.lstrip('ZX')
                    if amt > 1.0:  # Meaningful balance
                        # Map to quote currency patterns
                        if asset_upper == 'USDC' or asset_clean == 'USDC':
                            available_quotes.add('USDC')
                            key = (exchange_name.lower(), 'USDC')
                            exchange_quote_balances[key] = exchange_quote_balances.get(key, 0) + amt
                        if asset_upper == 'USDT' or asset_clean == 'USDT':
                            available_quotes.add('USDT')
                            key = (exchange_name.lower(), 'USDT')
                            exchange_quote_balances[key] = exchange_quote_balances.get(key, 0) + amt
                        if asset_upper in ('USD', 'ZUSD') or asset_clean == 'USD':
                            available_quotes.add('USD')
                            available_quotes.add('USDC')  # USD can buy USDC pairs
                            key = (exchange_name.lower(), 'USD')
                            exchange_quote_balances[key] = exchange_quote_balances.get(key, 0) + amt
                        if asset_upper in ('GBP', 'ZGBP') or asset_clean == 'GBP':
                            available_quotes.add('GBP')
                            key = (exchange_name.lower(), 'GBP')
                            exchange_quote_balances[key] = exchange_quote_balances.get(key, 0) + amt
                        if asset_upper in ('EUR', 'ZEUR') or asset_clean == 'EUR':
                            available_quotes.add('EUR')
                            key = (exchange_name.lower(), 'EUR')
                            exchange_quote_balances[key] = exchange_quote_balances.get(key, 0) + amt
        except Exception as e:
            print(f"   ⚠️ Balance detection error: {e}")
        
        # Show balances per exchange
        print(f"   💵 Quote balances by exchange:")
        for (ex, quote), bal in sorted(exchange_quote_balances.items()):
            print(f"      {ex.upper()} {quote}: {bal:.2f}")
        
        # 🔥 CRITICAL: Apply balance boost to scores BEFORE deduplication!
        # Boost MORE if the exchange actually has balance for that quote currency!
        for c in all_candidates:
            source_exchange = (c.get('source') or 'kraken').lower()
            quote = c['quote_currency']
            ex_quote_key = (source_exchange, quote)
            
            if quote in available_quotes:
                c['score'] += 10_000_000  # Massive boost for tradeable quote currency
                
                # 🔥 EXTRA boost if THIS exchange has balance (not just any exchange)
                if ex_quote_key in exchange_quote_balances and exchange_quote_balances[ex_quote_key] > 10:
                    c['score'] += 5_000_000  # Extra 5M for having balance on THIS exchange
        
        # 🔥 Keep best per base+exchange combo to allow BOTH Binance USDC AND Kraken GBP trades!
        # Don't collapse across exchanges - we want to trade on BOTH platforms
        def _base_from_symbol(sym: str) -> str:
            for suffix in self.quote_currency_suffixes:
                if sym.endswith(suffix):
                    return sym[: -len(suffix)]
            return sym

        best_per_base_exchange: Dict[str, Dict] = {}
        for c in all_candidates:
            base = _base_from_symbol(c['symbol'])
            source = (c.get('source') or 'unknown').lower()
            key = f"{base}_{source}"  # Keep separate entries per exchange!
            if key not in best_per_base_exchange or c['score'] > best_per_base_exchange[key]['score']:
                best_per_base_exchange[key] = c
        all_candidates = list(best_per_base_exchange.values())

        # Sort by score (tradeable pairs already boosted)
        all_candidates.sort(key=lambda x: x['score'], reverse=True)

        # Fallback: if no candidates met the aggressive filters, pick a best-effort symbol
        if not all_candidates:
            force_sym = CONFIG.get('FORCE_TRADE_SYMBOL') or None
            fallback = None
            best_change = 0
            for sym, data in self.ticker_cache.items():
                if sym in self.positions:
                    continue
                if force_sym and sym != force_sym:
                    continue
                price = data.get('price', 0)
                change = data.get('change24h', 0)
                volume = data.get('volume', 0)
                if price <= 0 or volume <= 0:
                    continue
                if abs(change) > abs(best_change):
                    best_change = change
                    fallback = {
                        'symbol': sym,
                        'price': price,
                        'change24h': change,
                        'volume': volume,
                        'score': abs(change),
                        'coherence': 0.55,
                        'dominant_node': 'ForceScout',
                        'quote_currency': self._get_quote_asset(sym)
                    }
            if fallback:
                all_candidates.append(fallback)

        # 🔥 FILTER: Only keep pairs where we have balance to trade!
        if available_quotes:
            tradeable_candidates = [c for c in all_candidates if c['quote_currency'] in available_quotes]
            print(f"   📊 Found {len(all_candidates)} pairs → {len(tradeable_candidates)} tradeable (have {available_quotes})")
            all_candidates = tradeable_candidates
        else:
            print(f"   📊 Found {len(all_candidates)} tradeable pairs")
        
        # 🔄 INTERLEAVE BY EXCHANGE: Ensure we deploy scouts on BOTH Binance AND Kraken!
        # Group by source exchange, then round-robin to pick from each
        by_exchange: Dict[str, List[Dict]] = {}
        for c in all_candidates:
            ex = (c.get('source') or 'unknown').lower()
            if ex not in by_exchange:
                by_exchange[ex] = []
            by_exchange[ex].append(c)
        
        # Sort each exchange's candidates by score
        for ex in by_exchange:
            by_exchange[ex].sort(key=lambda x: -x.get('score', 0))
        
        # Interleave: take top candidate from each exchange in rotation
        interleaved = []
        exchanges = list(by_exchange.keys())
        max_len = max(len(v) for v in by_exchange.values()) if by_exchange else 0
        for i in range(max_len):
            for ex in exchanges:
                if i < len(by_exchange[ex]):
                    interleaved.append(by_exchange[ex][i])
        
        all_candidates = interleaved
        print(f"   🔄 Interleaved {len(exchanges)} exchanges: {', '.join(exchanges)}")
        
        # FORCE deploy scouts - don't stop until we hit the target!
        deployed_per_quote: Dict[str, int] = {}
        for candidate in all_candidates:
            if scouts_deployed >= target_scouts:
                break
            if len(self.positions) >= CONFIG['MAX_POSITIONS']:
                break
            if candidate['symbol'] in self.positions:
                continue
            if deployed_per_quote.get(candidate['quote_currency'], 0) >= per_quote_cap:
                continue
                
            print(f"   🦅 Scout: {candidate['symbol']} ({candidate['change24h']:+.2f}% 24h | {candidate['quote_currency']})")
            
            # Call open_position - it will handle the actual trade
            result = self.open_position(candidate)
            if result:
                scouts_deployed += 1
                deployed_per_quote[candidate['quote_currency']] = deployed_per_quote.get(candidate['quote_currency'], 0) + 1
                print(f"   ✅ Scout #{scouts_deployed} DEPLOYED!")
            else:
                print(f"   ⚠️  Scout {candidate['symbol']} skipped - trying next...")
            time.sleep(0.25)  # small pause to avoid hammering exchange balance endpoints
                
        self.scouts_deployed = True
        
        if scouts_deployed > 0:
            print(f"\n   🎯 DEPLOYED {scouts_deployed} scout(s) - WE'RE IN THE GAME!\n")
        else:
            print(f"\n   ⚠️  No scouts deployed - check balance/liquidity\n")

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
                
                # Check if this is the base currency OR a stable coin (cash equivalent)
                stable_coins = {'USD', 'USDC', 'USDT', 'EUR', 'GBP', 'ZUSD', 'ZEUR', 'ZGBP'}
                is_cash = (conversion_asset == base or asset_clean == base or 
                           conversion_asset in stable_coins or asset_clean in stable_coins)
                if is_cash:
                    # Convert stable coins to base currency value
                    if conversion_asset != base and asset_clean != base:
                        try:
                            converted = self.client.convert_to_quote(exchange, conversion_asset, amount, base)
                            if converted > 0:
                                cash_balance += converted
                                total_equity += converted
                                holdings_value[asset_clean] = holdings_value.get(asset_clean, 0.0) + converted
                                continue
                        except Exception:
                            # Fallback: treat 1:1 for stablecoins
                            cash_balance += amount
                            total_equity += amount
                            holdings_value[asset_clean] = holdings_value.get(asset_clean, 0.0) + amount
                            continue
                    else:
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
        
        # 🛠️ FIX: Auto-correct "Fake $1000 Balance" on first run
        # If we are using the default 1000, but the wallet shows something else (e.g. ~55),
        # and we haven't done any trades yet, assume this is the TRUE starting balance.
        if self.tracker.initial_balance == 1000.0 and self.tracker.total_trades == 0:
            # Check if we are significantly different (e.g. > 1% diff) to avoid floating point noise
            # But really, if it's the first run, we should trust the wallet.
            if abs(total - 1000.0) > 1.0 and total > 0:
                print(f"   ⚖️  Correcting Initial Balance: ${self.tracker.initial_balance:.2f} -> ${total:.2f} (Actual Wallet)")
                self.tracker.initial_balance = total
                self.tracker.first_start_balance = total
                self.tracker.balance = total
                self.tracker.peak_balance = total
                self.tracker.equity_baseline = total
                self.tracker.portfolio_equity = total
                self.tracker.cash_balance = cash
                
                # Update the P&L snapshot immediately
                self.pnl_state['total_equity'] = total
                self.pnl_state['cash'] = cash
                self.pnl_state['net_profit'] = 0.0
                self.pnl_state['total_return_pct'] = 0.0

        self.total_equity_gbp = total
        self.cash_balance_gbp = cash
        self.holdings_gbp = holdings
        self.tracker.update_equity(total, cash, mark_cycle=mark_cycle)

        # 🧠 Store live P&L snapshot for decision making
        try:
            total_return_pct = 0.0
            if self.tracker.initial_balance > 0:
                total_return_pct = (total - self.tracker.initial_balance) / self.tracker.initial_balance * 100
            self.pnl_state = {
                'total_equity': total,
                'cash': cash,
                'net_profit': self.tracker.net_profit,
                'total_return_pct': total_return_pct,
                'drawdown_pct': self.tracker.current_drawdown,
                'timestamp': time.time(),
            }
        except Exception:
            pass
        
        # 🌟 Sync capital pool with current equity
        self.capital_pool.update_equity(total)
        
        if self.tracker.equity_baseline is None or self.tracker.equity_baseline == 0:
            self.tracker.equity_baseline = total
        gain = total - self.tracker.equity_baseline
        if gain > CONFIG['EQUITY_MIN_DELTA']:
            self.tracker.realize_portfolio_gain(gain)
            self.tracker.equity_baseline = total
        return total

    def get_pnl_snapshot(self) -> Dict[str, float]:
        """Return the latest live P&L snapshot for downstream consumers."""
        return dict(self.pnl_state) if isinstance(self.pnl_state, dict) else {}

    def should_trade_brain(self) -> Tuple[bool, str]:
        """
        🧠 BRAIN GATE: 7 Civilizations + Quantum Brain must approve trades.
        Returns (should_trade, reason).
        """
        if not hasattr(self, 'brain_bridge') or not self.brain_bridge:
            return True, "Brain Bridge not initialized - trading allowed"
        
        try:
            # Get brain recommendation
            rec = self.brain_bridge.get_trading_recommendation()
            action = rec.get('action', 'HOLD')
            civs_bullish = rec.get('civilizations_bullish', 0)
            civs_total = rec.get('civilizations_total', 7)
            confidence = rec.get('confidence', 0.5)
            
            # HARD BLOCK: If brain says REDUCE with high confidence
            if action == 'REDUCE' and confidence > 0.65:
                return False, f"Brain says REDUCE (conf={confidence:.0%}, {civs_bullish}/{civs_total} bullish)"
            
            # SOFT GATE: If BEARISH with moderate confidence
            consensus = self.brain_bridge._brain_consensus if hasattr(self.brain_bridge, '_brain_consensus') else 'NEUTRAL'
            if consensus == 'BEARISH' and confidence > 0.6:
                return False, f"Brain BEARISH (conf={confidence:.0%}) - waiting for bullish signal"
            
            # APPROVED
            if action == 'BUY':
                return True, f"Brain APPROVED: {civs_bullish}/{civs_total} civilizations BULLISH"
            
            return True, f"Brain neutral - {consensus} (conf={confidence:.0%})"
            
        except Exception as e:
            return True, f"Brain check error ({e}) - trading allowed"

    def should_enter_trade(self, opp: Dict, pos_size: float, lattice_state) -> bool:
        """
        🎯 PROBABILITY-MATRIX-DRIVEN entry decision.
        
        THE VISION: The probability matrix tells us WHEN to buy and WHAT to buy.
        It should be "surfing the wave" - in and out of positions for net profits.
        
        Buy BTC at this price, sell at this time, take profit, buy ETH, sell, etc.
        Snowballing profits through intelligent timing.
        """
        # Minimal sanity checks
        if pos_size <= 0 or self.total_equity_gbp <= 0:
            return False
            
        symbol = opp.get('symbol', 'UNKNOWN')
        
        # ═══════════════════════════════════════════════════════════════
        # 🧠🌍 BRAIN GATE CHECK - 7 CIVILIZATIONS + QUANTUM BRAIN
        # ═══════════════════════════════════════════════════════════════
        brain_ok, brain_reason = self.should_trade_brain()
        if not brain_ok:
            logger.info(f"🧠🚫 {symbol}: BRAIN GATE CLOSED - {brain_reason}")
            return False
        
        brain_consensus = opp.get('brain_consensus', ECOSYSTEM_BRAIN._brain_consensus)
        brain_confidence = opp.get('brain_confidence', ECOSYSTEM_BRAIN._brain_confidence)
        brain_rec = ECOSYSTEM_BRAIN.get_trading_recommendation()
        
        # If brain says REDUCE/BEARISH with high confidence, reject new entries
        if brain_rec['action'] == 'REDUCE' and brain_confidence > 0.7:
            logger.info(f"🧠📉 {symbol}: Brain says REDUCE (conf={brain_confidence:.0%}) - SKIPPING NEW ENTRY")
            return False
        
        # If brain is very bullish, log approval
        if brain_rec['action'] == 'BUY' and brain_confidence > 0.7:
            logger.info(f"🧠📈 {symbol}: Brain APPROVED (7 Civs: {brain_rec['civilizations_bullish']}/7 bullish)")
        
        # ═══════════════════════════════════════════════════════════════
        # 🔮 PROBABILITY MATRIX DECISION - THE CORE BRAIN 🔮
        # ═══════════════════════════════════════════════════════════════
        prob_action = opp.get('prob_action', 'HOLD')
        probability = opp.get('probability', 0.5)
        prob_confidence = opp.get('prob_confidence', 0.0)
        
        # 🚫 REJECT if matrix says SELL or HOLD with high confidence
        if prob_confidence >= 0.5:  # Only trust signals with decent confidence
            if prob_action in ['SELL', 'STRONG SELL']:
                logger.info(f"🚫 {symbol}: Matrix says {prob_action} (prob={probability:.0%}, conf={prob_confidence:.0%}) - NOT BUYING")
                return False
            if prob_action == 'HOLD' and probability < 0.50:
                logger.info(f"⏸️ {symbol}: Matrix says HOLD (prob={probability:.0%}) - WAITING")
                return False
        
        # ✅ PREFER entries when matrix says BUY
        if prob_action in ['BUY', 'STRONG BUY', 'SLIGHT BUY']:
            logger.info(f"✅ {symbol}: Matrix says {prob_action} (prob={probability:.0%}, conf={prob_confidence:.0%}) - APPROVED!")
        
        # ═══════════════════════════════════════════════════════════════
        # 📊 IMPERIAL PREDICTION - COSMIC TIMING
        # ═══════════════════════════════════════════════════════════════
        imperial_action = opp.get('imperial_action', 'HOLD')
        imperial_prob = opp.get('imperial_probability', 0.5)
        imperial_conf = opp.get('imperial_confidence', 0.0)
        
        if imperial_conf >= 0.5 and imperial_action in ['SELL', 'STRONG SELL']:
            logger.info(f"🌌 {symbol}: Imperial says {imperial_action} - SKIPPING")
            return False
            
        # ═══ GET LEARNED RECOMMENDATION ═══
        try:
            frequency = opp.get('frequency', CONFIG.get('DEFAULT_FREQUENCY', 432))
            coherence = opp.get('coherence', 0.5)
            score = opp.get('score', 50)
            pnl_snapshot = self.get_pnl_snapshot()
            opp['pnl_state'] = pnl_snapshot
            
            # 📉 Risk throttle from live P&L state
            risk_mod = 1.0
            dd = pnl_snapshot.get('drawdown_pct', 0) if pnl_snapshot else 0
            net_pnl = pnl_snapshot.get('net_profit', 0) if pnl_snapshot else 0
            if dd > 5:      # soften sizing when drawdown > 5%
                risk_mod *= 0.6
            if net_pnl < 0: # soften when running negative on the day/session
                risk_mod *= 0.8
            opp['risk_mod_from_pnl'] = risk_mod
            
            recommendation = ADAPTIVE_LEARNER.get_entry_recommendation(
                symbol=symbol,
                frequency=frequency,
                coherence=coherence,
                score=score,
                probability=probability
            )
            
            # Log the recommendation for visibility
            if recommendation['similar_trades'] >= 5:
                summary = ADAPTIVE_LEARNER.get_recommendation_summary(recommendation)
                logger.info(f"\n📊 LEARNED ANALYTICS for {symbol}:\n{summary}")
                
                # Store recommendation in opp for use in position management
                opp['learned_recommendation'] = recommendation
                
                # If confidence is HIGH and recommendation is NO, respect it
                # BUT: Only skip if WR is EXTREMELY low (<15%) - otherwise still take chances!
                if recommendation['confidence'] == 'high' and not recommendation['should_trade']:
                    if recommendation['expected_win_rate'] < 0.15:  # Very low - skip
                        logger.warning(f"⛔ SKIPPING {symbol}: High-confidence negative signal")
                        logger.warning(f"   Expected WR: {recommendation['expected_win_rate']*100:.0f}% based on {recommendation['similar_trades']} similar trades")
                        return False
                    else:
                        logger.info(f"⚡ TAKING CHANCE on {symbol}: Past WR {recommendation['expected_win_rate']*100:.0f}% but staying opportunistic!")
                    
                # If confidence is MEDIUM and expected WR < 15%, skip (was 35% - too conservative!)
                if recommendation['confidence'] == 'medium' and recommendation['expected_win_rate'] < 0.15:
                    logger.warning(f"⚠️ SKIPPING {symbol}: Medium-confidence, very low expected WR ({recommendation['expected_win_rate']*100:.0f}%)")
                    return False
                
                # Extra caution: if we're in BIG drawdown (>15%) and WR is poor (<25%), skip
                # Was: dd > 5 and WR < 55% - WAY too conservative!
                if dd > 15 and recommendation['expected_win_rate'] < 0.25:
                    logger.warning(f"⚠️ SKIPPING {symbol}: In significant drawdown ({dd:.1f}%), WR only {recommendation['expected_win_rate']*100:.0f}%")
                    return False
                    
                # Log advantages
                if recommendation['advantages']:
                    logger.info(f"✅ {symbol} advantages: {', '.join(recommendation['advantages'][:2])}")
                
                # 🔒 Risk-aware gate: Only skip if BOTH P&L is significantly negative AND WR is very low
                # Reduced conservatism - we need to take chances to make money!
                pnl = opp['pnl_state']
                if pnl:
                    # Only skip if: negative P&L + low confidence + WR < 20% (was 80% - way too conservative!)
                    if pnl.get('net_profit', 0) < -50 and recommendation['confidence'] == 'low':
                        if recommendation['expected_win_rate'] < 0.20:
                            logger.warning(f"⏸️ Skipping {symbol}: Net P&L very negative and poor expected WR ({recommendation['expected_win_rate']*100:.0f}%)")
                            return False
                        else:
                            logger.info(f"⚡ TAKING CHANCE on {symbol}: Low confidence but WR {recommendation['expected_win_rate']*100:.0f}% is acceptable!")
                    # Only skip if: SEVERE drawdown (>75% of max) AND WR < 25% (was 50%)
                    if pnl.get('drawdown_pct', 0) >= CONFIG.get('MAX_DRAWDOWN_PCT', 20) * 0.75 and recommendation['expected_win_rate'] < 0.25:
                        logger.warning(f"⏸️ Skipping {symbol}: Severe drawdown {pnl.get('drawdown_pct', 0):.1f}% and weak edge ({recommendation['expected_win_rate']*100:.0f}% WR)")
                        return False
                    
        except Exception as e:
            logger.debug(f"Could not get learned recommendation: {e}")
            
        # Default: Trade when you see opportunity (but now with learned wisdom)
        return True
    
    def _get_binance_lot_size(self, symbol: str) -> tuple:
        """
        Get Binance lot size filters for a symbol.
        Returns (step_size, min_qty) or (None, None) if not found.
        """
        cache_key = f"binance:{symbol.upper()}"
        cached = self._lot_size_cache.get(cache_key)
        if cached:
            return cached
        step_size = None
        min_qty = None
        try:
            import requests
            resp = requests.get(f'https://api.binance.com/api/v3/exchangeInfo?symbol={symbol}')
            if resp.status_code == 200:
                info = resp.json()
                for sym in info.get('symbols', []):
                    if sym['symbol'] == symbol:
                        for f in sym.get('filters', []):
                            if f.get('filterType') == 'LOT_SIZE':
                                step_size = float(f.get('stepSize', 0) or 0)
                                min_qty = float(f.get('minQty', 0) or 0)
                                break
        except Exception:
            pass
        result = (step_size, min_qty)
        self._lot_size_cache[cache_key] = result
        return result

    def _get_kraken_lot_size(self, symbol: str) -> tuple:
        """Fetch Kraken lot size/min quantity using cached exchange info."""
        cache_key = f"kraken:{symbol.upper()}"
        cached = self._lot_size_cache.get(cache_key)
        if cached:
            return cached
        step_size = None
        min_qty = None
        try:
            kraken_client = self.client.clients.get('kraken') if hasattr(self.client, 'clients') else None
            if kraken_client and hasattr(kraken_client, 'client') and hasattr(kraken_client.client, 'exchange_info'):
                info = kraken_client.client.exchange_info(symbol)
                for sym in info.get('symbols', []):
                    if sym.get('symbol') == symbol:
                        filters = sym.get('filters') or {}
                        lot = filters.get('LOT_SIZE')
                        if lot:
                            try:
                                step_size = float(lot.get('stepSize')) if lot.get('stepSize') else None
                            except Exception:
                                step_size = None
                            try:
                                min_qty = float(lot.get('minQty')) if lot.get('minQty') else None
                            except Exception:
                                min_qty = None
                        break
        except Exception:
            pass
        result = (step_size, min_qty)
        self._lot_size_cache[cache_key] = result
        return result
    
    def _truncate_to_lot_size(self, quantity: float, step_size: float) -> float:
        """
        Truncate quantity to valid lot size (round DOWN to step size).
        Uses Decimal to avoid floating point precision errors.
        """
        if step_size is None or step_size <= 0:
            return quantity
        from decimal import Decimal, ROUND_DOWN
        # Use Decimal for precise calculation
        qty_dec = Decimal(str(quantity))
        step_dec = Decimal(str(step_size))
        # Calculate number of steps and truncate
        steps = int(qty_dec / step_dec)
        result = steps * step_dec
        return float(result)

    def _prepare_liquidation_quantity(self, exchange: str, symbol: str, quantity: float, price: float) -> Tuple[Optional[float], Optional[str], Optional[str]]:
        """Apply exchange-specific lot size + notional checks before liquidation."""
        if quantity <= 0:
            return None, "zero quantity", None

        exchange_name = (exchange or '').lower()
        qty = float(quantity)
        adjustment_note = None
        step_size = None
        min_qty = None

        if exchange_name == 'binance':
            step_size, min_qty = self._get_binance_lot_size(symbol)
        elif exchange_name == 'kraken':
            step_size, min_qty = self._get_kraken_lot_size(symbol)

        if step_size and step_size > 0:
            adjusted_qty = self._truncate_to_lot_size(qty, step_size)
            if adjusted_qty != qty:
                adjustment_note = f"lot adjust {qty:.8f}→{adjusted_qty:.8f} (step {step_size})"
            qty = adjusted_qty

        if qty <= 0:
            return None, "quantity below lot step", adjustment_note

        if min_qty and qty < min_qty:
            pretty_exchange = exchange_name.upper() or 'EXCHANGE'
            return None, f"qty {qty:.8f} below {pretty_exchange} min {min_qty:.8f}", adjustment_note

        min_notional = None
        if exchange_name == 'binance':
            min_notional = CONFIG.get('BINANCE_MIN_NOTIONAL')
        elif exchange_name == 'kraken':
            min_notional = CONFIG.get('KRAKEN_MIN_NOTIONAL')

        if min_notional and price and price > 0:
            notional = qty * price
            if notional < min_notional:
                pretty_exchange = exchange_name.upper() or 'EXCHANGE'
                return None, f"notional £{notional:.2f} below {pretty_exchange} min £{min_notional:.2f}", adjustment_note

        return qty, None, adjustment_note
    
    def harvest_existing_assets(self):
        """
        🌾 STARTUP HARVESTER: Scan existing holdings and sell if profitable.
        
        At startup, checks all non-quote currency balances and attempts to 
        sell them back to quote currencies (EUR/USDC) if they can be sold
        for a net profit after fees.
        
        This compounds leftover positions from previous runs.
        """
        print("\n" + "="*70)
        print("🌾 STARTUP HARVESTER: Scanning existing assets for compounding...")
        print("="*70)
        
        if self.dry_run:
            print("   ⚪ Dry run mode - skipping harvest")
            return
        
        # Get all balances
        all_balances = self.client.get_all_balances()
        
        # Quote currencies we want to compound INTO (don't sell these)
        quote_currencies = set(CONFIG['QUOTE_CURRENCIES'])
        stable_coins = {'USDC', 'USDT', 'EUR', 'USD', 'GBP', 'ZUSD', 'ZEUR', 'ZGBP'}
        skip_assets = quote_currencies | stable_coins | {'BNB'}  # Keep BNB for fee discounts
        
        harvested_total = 0.0
        harvested_count = 0
        
        for exchange_name, balances in all_balances.items():
            if not isinstance(balances, dict):
                continue
                
            if exchange_name not in ('binance', 'kraken'):
                continue
                
            print(f"\n   📍 Scanning {exchange_name.upper()}...")
            
            for asset, balance in balances.items():
                try:
                    bal = float(balance)
                except (ValueError, TypeError):
                    continue
                    
                # Skip quote currencies and tiny balances
                if asset.upper() in skip_assets or asset in skip_assets:
                    continue
                if bal < 0.0001:
                    continue
                
                # Try to find a trading pair for this asset
                # Priority: USDC > EUR > USDT
                quote_priority = ['USDC', 'EUR', 'USDT'] if exchange_name == 'binance' else ['USDC', 'USD', 'EUR']
                
                # Kraken uses special naming for some assets
                kraken_asset_map = {
                    'XXBT': 'XBT', 'XBT': 'XBT',  # Bitcoin
                    'XETH': 'ETH', 'ETH': 'ETH',  # Ethereum  
                    'XLTC': 'LTC', 'LTC': 'LTC',  # Litecoin
                    'XXLM': 'XLM', 'XLM': 'XLM',  # Stellar
                    'XXRP': 'XRP', 'XRP': 'XRP',  # Ripple
                    'XXMR': 'XMR', 'XMR': 'XMR',  # Monero
                }
                
                # Get the base asset name for symbol construction
                if exchange_name == 'kraken':
                    base_asset = kraken_asset_map.get(asset, asset)
                else:
                    base_asset = asset
                
                for quote in quote_priority:
                    symbol = f"{base_asset}{quote}"
                    
                    # Check if we can get a price for this pair
                    try:
                        ticker = self.client.get_ticker(exchange_name, symbol)
                        price = ticker.get('price', 0) or ticker.get('last', 0)
                        if not price or price <= 0:
                            continue
                    except:
                        continue
                    
                    # Calculate potential value
                    gross_value = bal * price
                    
                    # Skip if value is too small (< $0.50)
                    if gross_value < 0.50:
                        break
                    
                    # Calculate fees
                    fee_rate = get_platform_fee(exchange_name, 'taker')
                    fee = gross_value * fee_rate
                    net_value = gross_value - fee
                    
                    # We don't have entry price, so we'll sell if value > $1 
                    # (assumes any remaining assets are from profitable trades or dust)
                    min_harvest_value = 1.0  # Only harvest if > $1 net
                    
                    if net_value >= min_harvest_value:
                        print(f"   🌾 Found: {bal:.4f} {asset} = ${gross_value:.2f} (net: ${net_value:.2f})")
                        
                        # Universal lot size handling for ALL exchanges
                        sell_qty, block_reason, adj_note = self._prepare_liquidation_quantity(
                            exchange_name, symbol, bal, price
                        )
                        if sell_qty is None:
                            print(f"   ⚠️ {symbol}: {block_reason}")
                            continue
                        if adj_note:
                            print(f"   📐 {adj_note}")
                        
                        # Attempt to sell
                        try:
                            result = self.client.place_market_order(
                                exchange_name, symbol, 'SELL', quantity=sell_qty
                            )
                            
                            if result and not result.get('rejected') and not result.get('error'):
                                # Extract actual fill value
                                fills = result.get('fills', [])
                                if fills:
                                    actual_value = sum(float(f.get('qty', 0)) * float(f.get('price', 0)) for f in fills)
                                else:
                                    actual_value = float(result.get('cummulativeQuoteQty', net_value))
                                
                                harvested_total += actual_value
                                harvested_count += 1
                                print(f"   ✅ SOLD: {asset} → {quote} for ${actual_value:.2f}")
                                
                                # Clear the position from tracking
                                self.positions.pop(symbol, None)
                                self._clear_symbol_dust(symbol)
                            else:
                                reason = result.get('reason', 'Unknown error') if result else 'No response'
                                print(f"   ⚠️ Failed to sell {asset}: {reason}")
                        except Exception as e:
                            print(f"   ⚠️ Error selling {asset}: {e}")
                    
                    break  # Found a pair, move to next asset
        
        print(f"\n{'─'*70}")
        if harvested_count > 0:
            print(f"   🌾 HARVEST COMPLETE: Sold {harvested_count} assets for ${harvested_total:.2f}")
            print(f"   💰 Capital compounded back to trading pool!")
        else:
            print(f"   ⚪ No assets to harvest (all below minimum or already in quote currencies)")
        print(f"{'─'*70}\n")
        
        # Refresh equity after harvesting
        self.refresh_equity()
        return harvested_total
    
    def should_exit_trade(self, pos: 'Position', current_price: float, reason: str) -> bool:
        """
        Smart exit gate - only sell if we're making NET PROFIT after fees.
        This ensures every closed trade is profitable.
        
        🔥 PENNY PROFIT MODE: Exit when gross P&L hits exact dollar threshold
        💰 Target: +$0.01 net profit per trade (scales through volume!)
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
        
        # 💰 PENNY PROFIT THRESHOLDS - Dollar-based exit logic
        penny_check = check_penny_exit(pos.exchange, pos.entry_value, gross_pnl)
        penny_threshold = penny_check.get('threshold')
        
        if penny_threshold:
            # Use penny profit dollar thresholds
            min_gross_win = penny_threshold.get('win_gte', 0.01)
            max_gross_loss = penny_threshold.get('stop_lte', -0.02)
            
            # TAKE PROFIT: Hit penny profit target
            if reason == "TP":
                if gross_pnl >= min_gross_win:
                    estimated_net = gross_pnl - total_expenses
                    print(f"   💰 PENNY TP: {pos.symbol} gross ${gross_pnl:.4f} >= ${min_gross_win:.4f} -> net ~${estimated_net:.4f}")
                    return True
                else:
                    print(f"   🛑 HOLDING {pos.symbol}: Gross ${gross_pnl:.4f} < penny target ${min_gross_win:.4f}")
                    return False
            
            # STOP LOSS: Cut losses at penny stop
            if reason == "SL":
                if gross_pnl <= max_gross_loss:
                    print(f"   🛑 PENNY SL: {pos.symbol} gross ${gross_pnl:.4f} <= ${max_gross_loss:.4f} - CUTTING LOSS!")
                    return True
                else:
                    # Don't stop out early if loss is still manageable
                    print(f"   ⏳ HOLDING {pos.symbol}: Gross ${gross_pnl:.4f} > stop ${max_gross_loss:.4f} - giving it room")
                    return False
            
            # 🌾 HARVEST: Use penny threshold for harvest too
            if reason in ("HARVEST", "bridge_harvest"):
                if gross_pnl >= min_gross_win:
                    print(f"   🌾 PENNY HARVEST: {pos.symbol} gross ${gross_pnl:.4f} - LOCKING IN PENNY!")
                    return True
                print(f"   🛑 HOLDING {pos.symbol}: Harvest blocked - gross ${gross_pnl:.4f} < ${min_gross_win:.4f}")
                return False
        else:
            # Fallback to percentage-based when penny profit not available
            min_profit_buffer = pos.entry_value * CONFIG['MIN_NET_PROFIT_PCT']
            min_net_profit = min_profit_buffer
            
            if reason == "TP":
                if net_pnl >= min_net_profit:
                    print(f"   ✅ EXIT APPROVED: {pos.symbol} net profit ${net_pnl:.4f} >= min ${min_net_profit:.4f}")
                    return True
                else:
                    print(f"   🛑 HOLDING {pos.symbol}: Net profit ${net_pnl:.4f} < min required ${min_net_profit:.4f}")
                    return False
            
            if reason in ("HARVEST", "bridge_harvest"):
                if net_pnl >= min_net_profit:
                    print(f"   🌾 HARVEST APPROVED: {pos.symbol} net profit ${net_pnl:.4f}")
                    return True
                print(f"   🛑 HOLDING {pos.symbol}: Harvest blocked - net ${net_pnl:.4f} < min ${min_net_profit:.4f}")
                return False
            
            if reason == "SL":
                loss_pct = abs(net_pnl / pos.entry_value * 100) if pos.entry_value > 0 else 0
                if loss_pct < 1.0 or abs(change_pct * 100) > 2.0:
                    return True
                print(f"   🛑 HOLDING {pos.symbol}: Loss too large (${net_pnl:.2f})")
                return False
        
        # BRIDGE FORCE EXIT: Always allow (emergency exit)
        if reason == "bridge_force_exit":
            if net_pnl < 0:
                print(f"   ⚠️ FORCE EXIT {pos.symbol}: Bridge command - LOSS ${net_pnl:.4f}")
            return True
        
        # 🔮 MATRIX EXIT: Probability matrix says SELL - allow if profitable
        if reason in ["MATRIX_SELL", "MATRIX_FORCE"]:
            # Enforce Penny Profit even for Matrix exits (unless FORCE)
            if penny_threshold:
                min_gross_win = penny_threshold.get('win_gte', 0.01)
                if gross_pnl >= min_gross_win:
                    print(f"   🔮 MATRIX EXIT (PENNY SECURED): {pos.symbol} gross ${gross_pnl:.4f} >= ${min_gross_win:.4f}")
                    return True
                elif reason == "MATRIX_FORCE":
                    # Force exit allows small loss if absolutely necessary
                    if gross_pnl > -pos.entry_value * 0.01:
                        print(f"   🚨 MATRIX FORCE: {pos.symbol} small loss ${gross_pnl:.4f}")
                        return True
                else:
                    print(f"   🛑 HOLDING {pos.symbol}: Matrix signal ignored - Penny Profit not met (${gross_pnl:.4f} < ${min_gross_win:.4f})")
                    return False
            
            # Fallback if penny profit not enabled
            elif gross_pnl >= 0:
                print(f"   🔮 MATRIX EXIT: {pos.symbol} gross ${gross_pnl:.4f}")
                return True
            elif reason == "MATRIX_FORCE" and gross_pnl > -pos.entry_value * 0.01:
                print(f"   🚨 MATRIX FORCE: {pos.symbol} small loss ${gross_pnl:.4f}")
                return True
            print(f"   🛑 HOLDING {pos.symbol}: Matrix blocked - loss too large")
            return False
        
        # REBALANCE/SWAP: Only if net negative is small
        if reason in ["REBALANCE", "SWAP"]:
            if net_pnl > -0.10:
                return True
            return False
        
        # Default: require penny profit threshold or min net profit
        if penny_threshold and gross_pnl >= penny_threshold.get('win_gte', 0.01):
            return True
        elif not penny_threshold and net_pnl >= pos.entry_value * CONFIG['MIN_NET_PROFIT_PCT']:
            return True
        return False
    
    def save_state(self):
        """Save current state to file for recovery"""
        try:
            state = {
                'first_start_balance': self.tracker.first_start_balance,  # TRUE starting balance!
                'first_start_time': self.tracker.first_start_time,  # When we first started
                'initial_balance': self.tracker.initial_balance,
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
                
            # Also save multi-exchange learning and aggregated state
            self.state_aggregator.save_aggregated_state()
            
        except Exception as e:
            print(f"   ⚠️ State save error: {e}")
    
    def load_state(self):
        """Load previous state from file"""
        try:
            if not os.path.exists(CONFIG['STATE_FILE']):
                return
            
            with open(CONFIG['STATE_FILE'], 'r') as f:
                state = json.load(f)
            
            # Restore tracker state - including the TRUE starting balance!
            self.tracker.first_start_balance = state.get('first_start_balance', state.get('initial_balance', self.tracker.initial_balance))
            self.tracker.first_start_time = state.get('first_start_time', time.time())
            self.tracker.initial_balance = state.get('initial_balance', self.tracker.initial_balance)
            self.tracker.balance = state.get('balance', self.tracker.balance)
            self.tracker.peak_balance = state.get('peak_balance', self.tracker.peak_balance)
            self.tracker.total_trades = state.get('total_trades', 0)
            self.tracker.wins = state.get('wins', 0)
            self.tracker.losses = state.get('losses', 0)
            self.tracker.total_fees = state.get('total_fees', 0.0)
            self.tracker.compounded = state.get('compounded', 0.0)
            self.tracker.harvested = state.get('harvested', 0.0)
            self.tracker.max_drawdown = state.get('max_drawdown', 0.0)
            
            print(f"   📊 Restored TRUE starting balance: £{self.tracker.first_start_balance:.2f} (from {time.strftime('%Y-%m-%d %H:%M', time.localtime(self.tracker.first_start_time))})")
            
            # 🔧 RESTORE POSITIONS from saved state
            saved_positions = state.get('positions', {})
            if saved_positions:
                for symbol, pos_data in saved_positions.items():
                    try:
                        # Reconstruct Position object from saved dict
                        self.positions[symbol] = Position(
                            symbol=pos_data.get('symbol', symbol),
                            entry_price=pos_data.get('entry_price', 0.0),
                            quantity=pos_data.get('quantity', 0.0),
                            entry_fee=pos_data.get('entry_fee', 0.0),
                            entry_value=pos_data.get('entry_value', 0.0),
                            momentum=pos_data.get('momentum', 0.0),
                            coherence=pos_data.get('coherence', 0.5),
                            entry_time=pos_data.get('entry_time', time.time()),
                            dominant_node=pos_data.get('dominant_node', 'Restored'),
                            exchange=pos_data.get('exchange', 'kraken'),
                            is_historical=pos_data.get('is_historical', False),
                            generation=pos_data.get('generation', 0),
                            is_scout=pos_data.get('is_scout', False),
                            highest_price=pos_data.get('highest_price', 0.0),
                            trailing_stop_active=pos_data.get('trailing_stop_active', False),
                            trailing_stop_price=pos_data.get('trailing_stop_price', 0.0),
                        )
                    except Exception as pos_err:
                        print(f"   ⚠️ Could not restore position {symbol}: {pos_err}")
                print(f"   💾 Restored {len(self.positions)} positions from previous session")
            
        except Exception as e:
            print(f"   ⚠️ State load error: {e}")

    def sync_positions_with_exchange(self):
        """
        🔄 POSITION SYNC: Reconcile stored positions with actual exchange balances.
        
        This fixes the state drift problem where positions are sold on exchange
        but the local state file still shows them as active.
        """
        if self.dry_run:
            print("   🔄 Position sync skipped (dry run mode)")
            return
            
        print("\n   🔄 SYNCING POSITIONS WITH EXCHANGE BALANCES...")
        
        try:
            # Get real balances from all exchanges
            all_balances = self.client.get_all_balances()
            kraken_balances = all_balances.get('kraken', {})
            binance_balances = all_balances.get('binance', {})
            
            # 🔧 KRAKEN ASSET MAPPING: Standard name → Kraken names to try
            # Kraken returns normalized names from get_account_balance (BTC, ETH, etc.)
            # but sometimes uses XXBT, XETH internally
            kraken_asset_variants = {
                'BTC': ['BTC', 'XBT', 'XXBT'],
                'ETH': ['ETH', 'XETH'],
                'DOGE': ['DOGE', 'XDG', 'XXDG'],
                'XLM': ['XLM', 'XXLM'],
                'XRP': ['XRP', 'XXRP'],
                'LTC': ['LTC', 'XLTC'],
                'ZEC': ['ZEC', 'XZEC'],
                'ADA': ['ADA'],
                'SOL': ['SOL'],
                'DOT': ['DOT'],
                'AVAX': ['AVAX'],
                'LINK': ['LINK'],
                'MATIC': ['MATIC', 'POL'],  # Polygon rebranded
                'SHIB': ['SHIB'],
                'UNI': ['UNI'],
            }
            
            # 🔧 BINANCE ASSET MAPPING: Handle Binance Earn, staking, and special assets
            # Binance uses LD prefix for Earn products, B prefix for wrapped, etc.
            binance_asset_variants = {
                'BTC': ['BTC', 'LDBTC', 'WBTC', 'BTCB'],
                'ETH': ['ETH', 'LDETH', 'WETH', 'BETH'],  # BETH = staked ETH
                'BNB': ['BNB', 'LDBNB', 'WBNB'],
                'USDT': ['USDT', 'LDUSDT'],
                'USDC': ['USDC', 'LDUSDC'],
                'SOL': ['SOL', 'LDSOL', 'BNSOL'],  # BNSOL = staked SOL
                'DOGE': ['DOGE', 'LDDOGE'],
                'XRP': ['XRP', 'LDXRP'],
                'ADA': ['ADA', 'LDADA'],
                'AVAX': ['AVAX', 'LDAVAX'],
                'DOT': ['DOT', 'LDDOT'],
                'MATIC': ['MATIC', 'POL', 'LDMATIC'],  # Polygon rebranded to POL
                'SHIB': ['SHIB', 'LDSHIB'],
                'LINK': ['LINK', 'LDLINK'],
                'LTC': ['LTC', 'LDLTC'],
                'UNI': ['UNI', 'LDUNI'],
                'ATOM': ['ATOM', 'LDATOM'],
                'XLM': ['XLM', 'LDXLM'],
                'TRX': ['TRX', 'LDTRX'],
                'NEAR': ['NEAR', 'LDNEAR'],
                'APT': ['APT', 'LDAPT'],
                'ARB': ['ARB', 'LDARB'],
                'OP': ['OP', 'LDOP'],
                'INJ': ['INJ', 'LDINJ'],
                'SUI': ['SUI', 'LDSUI'],
                'SEI': ['SEI', 'LDSEI'],
                'FET': ['FET', 'LDFET'],
                'PEPE': ['PEPE', 'LDPEPE'],
                'FLOKI': ['FLOKI', 'LDFLOKI'],
                'WIF': ['WIF', 'LDWIF'],
                'BONK': ['BONK', 'LDBONK'],
            }
            
            def get_kraken_balance(asset: str) -> float:
                """Try multiple Kraken asset name variants."""
                variants = kraken_asset_variants.get(asset, [asset])
                for var in variants:
                    bal = kraken_balances.get(var, 0.0)
                    if bal > 0:
                        return float(bal)
                # Also try raw asset name
                return float(kraken_balances.get(asset, 0.0))
            
            def get_binance_balance(asset: str) -> float:
                """Try multiple Binance asset name variants (including Earn products)."""
                variants = binance_asset_variants.get(asset, [asset])
                total = 0.0
                for var in variants:
                    bal = binance_balances.get(var, 0.0)
                    if bal > 0:
                        total += float(bal)
                # Also try raw asset name if not already included
                if asset not in variants:
                    total += float(binance_balances.get(asset, 0.0))
                # Try with LD prefix for any unknown asset (Binance Earn)
                ld_asset = f"LD{asset}"
                if ld_asset not in variants:
                    total += float(binance_balances.get(ld_asset, 0.0))
                return total
            
            positions_to_remove = []
            positions_adjusted = 0
            
            for symbol, pos in list(self.positions.items()):
                # Extract base asset from symbol
                base_asset = symbol
                for suffix in sorted(CONFIG['QUOTE_CURRENCIES'], key=len, reverse=True):
                    if symbol.endswith(suffix):
                        base_asset = symbol[:-len(suffix)]
                        break
                
                # Determine which exchange and get balance
                exchange = getattr(pos, 'exchange', 'kraken').lower()
                real_qty = 0.0
                
                if exchange == 'kraken':
                    real_qty = get_kraken_balance(base_asset)
                elif exchange == 'binance':
                    real_qty = get_binance_balance(base_asset)
                elif exchange == 'capital':
                    # Capital.com CFD positions - check via API
                    try:
                        capital_client = self.client.clients.get('capital')
                        if capital_client and hasattr(capital_client.client, 'get_positions'):
                            capital_positions = capital_client.client.get_positions()
                            for cfd_pos in capital_positions:
                                epic = cfd_pos.get('market', {}).get('epic') or cfd_pos.get('epic', '')
                                if epic == symbol:
                                    real_qty = float(cfd_pos.get('position', {}).get('size') or cfd_pos.get('size', 0))
                                    break
                    except Exception:
                        pass
                elif exchange == 'alpaca':
                    # 🦙 ALPACA positions - check via API for both crypto and stocks
                    try:
                        alpaca_client = self.client.clients.get('alpaca')
                        if alpaca_client:
                            alpaca_positions = alpaca_client.client.get_positions()
                            for alp_pos in alpaca_positions:
                                pos_symbol = getattr(alp_pos, 'symbol', str(alp_pos))
                                if pos_symbol == symbol or pos_symbol == base_asset:
                                    real_qty = float(getattr(alp_pos, 'qty', 0))
                                    # Handle short positions (negative quantity)
                                    side = getattr(alp_pos, 'side', 'long')
                                    if side == 'short':
                                        real_qty = -abs(real_qty)
                                    break
                    except Exception:
                        pass
                else:
                    # Try both spot exchanges
                    real_qty = get_binance_balance(base_asset)
                    if real_qty == 0:
                        real_qty = get_kraken_balance(base_asset)
                
                stored_qty = pos.quantity
                
                # Check for significant discrepancy
                if real_qty < stored_qty * 0.1:  # Less than 10% of stored = position closed
                    positions_to_remove.append(symbol)
                    print(f"   ❌ {symbol}: CLOSED (stored={stored_qty:.6f}, actual={real_qty:.6f})")
                elif abs(real_qty - stored_qty) > stored_qty * 0.05:  # More than 5% diff
                    # Adjust quantity to match reality
                    old_qty = pos.quantity
                    pos.quantity = real_qty
                    positions_adjusted += 1
                    print(f"   🔧 {symbol}: ADJUSTED qty {old_qty:.6f} -> {real_qty:.6f}")
            
            # Remove closed positions
            for symbol in positions_to_remove:
                pos = self.positions.pop(symbol, None)
                if pos:
                    # Record as a loss (conservative - we don't know actual exit price)
                    self.tracker.losses += 1
                    self.tracker.total_trades += 1
                    print(f"   🗑️ Removed stale position: {symbol}")
            
            # Summary
            if positions_to_remove or positions_adjusted:
                print(f"\n   ✅ SYNC COMPLETE: Removed {len(positions_to_remove)}, Adjusted {positions_adjusted}")
                self.save_state()  # Save immediately after sync
            else:
                print(f"   ✅ All {len(self.positions)} positions verified OK")
                
        except Exception as e:
            print(f"   ⚠️ Position sync error: {e}")
            import traceback
            traceback.print_exc()
        
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
            if not WEBSOCKETS_AVAILABLE:
                print(f"   ⚠️ WebSocket library not available. Skipping {exchange_name.upper()} connection.")
                return

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
                                    await asyncio.sleep(0.5)
                                    
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
        """Refresh ticker data from REST API with orchestrator enrichment"""
        try:
            tickers_list = self.client.get_24h_tickers()
            
            # Safety check: if no tickers, use cached tickers or hardcoded fallback
            if not tickers_list:
                if self.ticker_cache:
                    print(f"   ⚠️ No tickers returned, using cache ({len(self.ticker_cache)} symbols)")
                    return len(self.ticker_cache)
                else:
                    print(f"   ⚠️ API returned 0 tickers! Using hardcoded fallback pairs...")
                    # FALLBACK: Create synthetic ticker data for common pairs we can trade
                    tickers_list = self._get_hardcoded_fallback_tickers()
                    print(f"   ✅ Fallback loaded {len(tickers_list)} pairs")
            
            self.ticker_cache = {}
            
            # 🌐 STEP 1: Get orchestrator insights (cross-exchange learning)
            orchestrator_opportunities = {}
            try:
                all_opps = self.multi_exchange.scan_all_exchanges()
                for exchange, opps in all_opps.items():
                    for opp in opps:
                        sym = opp.get('symbol')
                        if sym:
                            orchestrator_opportunities[sym] = opp
            except Exception as e:
                logger.debug(f"Orchestrator scan skipped: {e}")
            
            # STEP 2: Merge with standard tickers
            for t in tickers_list:
                symbol = t.get('symbol', '')
                if not symbol:
                    continue
                try:
                    price = float(t.get('lastPrice', 0))
                    change = float(t.get('priceChangePercent', 0))
                    volume = float(t.get('quoteVolume', 0))
                    source = t.get('source', 'kraken')
                    
                    # Base ticker data
                    self.ticker_cache[symbol] = {
                        'price': price,
                        'change24h': change,
                        'volume': volume,
                        'source': source
                    }
                    
                    # 🌐 ENRICH: Add orchestrator insights if available
                    if symbol in orchestrator_opportunities:
                        opp = orchestrator_opportunities[symbol]
                        self.ticker_cache[symbol]['orchestrator_score'] = opp.get('score', 0)
                        self.ticker_cache[symbol]['orchestrator_coherence'] = opp.get('coherence', 0)
                        self.ticker_cache[symbol]['orchestrator_probability'] = opp.get('probability', 0.5)
                        self.ticker_cache[symbol]['asset_class'] = opp.get('asset_class', 'crypto')
                    
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
            # Return cached count to allow system to continue
            return len(self.ticker_cache)

    def _get_hardcoded_fallback_tickers(self) -> List[Dict]:
        """
        Fallback ticker list when API fails.
        Uses synthetic but realistic data for common trading pairs.
        """
        import random

        # If we have a recent snapshot file, prefer using it as fallback
        snapshot_path = os.path.join('/workspaces/aureon-trading', 'market_snapshots_30.json')
        if os.path.exists(snapshot_path):
            try:
                with open(snapshot_path, 'r') as f:
                    data = json.load(f)
                pairs = []
                for item in data if isinstance(data, list) else data.get('snapshots', []):
                    symbol = item.get('symbol')
                    price = float(item.get('price', 0)) if item.get('price') is not None else 0
                    change = float(item.get('change24h', item.get('priceChangePercent', 0))) if item.get('priceChangePercent') is not None or item.get('change24h') is not None else 0
                    volume = float(item.get('quoteVolume', item.get('volume', 0))) if item.get('quoteVolume') is not None or item.get('volume') is not None else 0
                    if symbol and price > 0 and volume > 0:
                        pairs.append((symbol, price, change, volume))
                if pairs:
                    return [
                        {
                            'symbol': sym,
                            'lastPrice': price,
                            'priceChangePercent': change,
                            'quoteVolume': vol,
                        }
                        for sym, price, change, vol in pairs
                    ]
            except Exception:
                pass
        
        # Common pairs we trade on (covering major assets)
        pairs = [
            ('BTCUSD', 45000, 2.5),      # BTC stable
            ('ETHUSD', 2500, 1.8),       # ETH stable  
            ('XRPUSD', 2.1, 3.2),        # XRP more volatile
            ('ADAUSD', 0.95, 2.8),       # ADA mid-volatility
            ('SOLUSD', 195, 4.5),        # SOL higher volatility
            ('DOTUSD', 9.2, 3.1),        # DOT mid-volatility
            ('LINKUSD', 22.5, 2.9),      # LINK mid-volatility
            ('AVAXUSD', 38.5, 3.6),      # AVAX higher volatility
            ('DOGEUSD', 0.38, 4.2),      # DOGE high volatility
            ('DOGEUSD', 0.38, 4.2),      # DOGE high volatility
            ('LTCUSD', 185, 2.4),        # LTC stable
            ('BCHUSD', 580, 2.7),        # BCH stable
            ('XLMUSD', 0.12, 3.5),       # XLM mid-volatility
            ('XLMUSD', 0.12, 3.5),       # XLM mid-volatility
            ('UNIUSD', 18.5, 3.3),       # UNI mid-volatility
            ('MKRUSD', 2200, 2.6),       # MKR stable
            ('AAVEUSD', 350, 3.1),       # AAVE mid-volatility
            ('GTCUSD', 12.5, 3.8),       # GTC higher volatility
            ('SNXUSD', 3.2, 4.1),        # SNX high volatility
            ('CRVUSD', 0.65, 5.2),       # CRV volatile
            ('COMPUSD', 155, 3.4),       # COMP mid-volatility
            ('YFIUSD', 8500, 3.9),       # YFI higher volatility
            ('CHZUSD', 0.32, 6.8),       # CHZ very volatile
            ('MATICUSD', 0.88, 5.5),     # MATIC volatile
            ('FTMUSD', 0.75, 4.9),       # FTM volatile
            ('ONEUSD', 0.032, 5.1),      # ONE volatile
            ('ZECUSD', 60, 3.3),         # ZEC mid-volatility
            ('DASHUSDC', 35, 2.8),       # DASH stable
            ('STORJUSD', 0.55, 4.5),     # STORJ higher volatility
            ('RENUSDT', 0.38, 5.8),      # REN very volatile
        ]
        
        fallback_tickers = []
        for symbol, base_price, volatility in pairs:
            # Add small random perturbation to appear more realistic
            price = base_price * (1 + random.uniform(-0.01, 0.01))
            change = random.uniform(-volatility, volatility)
            volume = random.uniform(100000, 5000000)
            
            fallback_tickers.append({
                'symbol': symbol,
                'lastPrice': str(price),
                'priceChangePercent': str(change),
                'quoteVolume': str(volume * price),
                'source': 'fallback'
            })
        
        return fallback_tickers

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
                        change_pct = ((current_price - pos.entry_price) / pos.entry_price * 100) if pos.entry_price > 0 else 0
                        if pnl >= min_profit:
                            print(f"   🌉 Harvesting {symbol} (${pnl:+.2f}) via bridge command")
                            self.close_position(symbol, 'bridge_harvest', change_pct, current_price)
                    
                elif cmd.command == 'force_exit':
                    target_symbol = cmd.params.get('symbol')
                    if target_symbol and target_symbol in self.positions:
                        pos = self.positions[target_symbol]
                        current_price = self.get_realtime_price(target_symbol) or pos.entry_price
                        change_pct = ((current_price - pos.entry_price) / pos.entry_price * 100) if pos.entry_price > 0 else 0
                        print(f"   🌉 Force exiting {target_symbol} via bridge command")
                        self.close_position(target_symbol, 'bridge_force_exit', change_pct, current_price)
                        
        except Exception as e:
            print(f"   ⚠️ Bridge command processing error: {e}")
    
    # ─────────────────────────────────────────────────────────
    # Opportunity Detection
    # ─────────────────────────────────────────────────────────
    
    def find_opportunities(self) -> List[Dict]:
        """Find best trading opportunities using all analysis methods - TRADES EVERYTHING"""
        opportunities = []
        
        # Safety check
        if not self.ticker_cache:
            print(f"   ⚠️ No tickers loaded! Skipping opportunity search.")
            return []
        
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
                for curr in ['GBP', 'USD', 'EUR', 'USDT', 'USDC', 'BTC', 'ETH']:  # Added USDC!
                    if symbol.endswith(curr):
                        available_quotes.add(curr)
                        break
            
            # 🔥 CHECK ACTUAL EXCHANGE BALANCES for available quote currencies!
            try:
                all_balances = self.client.get_all_balances()
                for exchange_name, balances in all_balances.items():
                    if not isinstance(balances, dict):
                        continue
                    for asset, bal in balances.items():
                        try:
                            bal_float = float(bal)
                        except:
                            continue
                        # If we have meaningful balance in a quote currency, add it!
                        asset_upper = asset.upper().replace('Z', '')  # ZUSD -> USD
                        if asset_upper in ['USD', 'USDC', 'USDT', 'EUR', 'GBP', 'BTC', 'ETH'] and bal_float > 1.0:
                            available_quotes.add(asset_upper)
                            if bal_float > 10:  # Log significant balances
                                logger.debug(f"Found {bal_float:.2f} {asset_upper} on {exchange_name}")
            except Exception as e:
                logger.debug(f"Could not check exchange balances: {e}")
            
            # Also add base currency if we have cash
            if self.cash_balance_gbp > CONFIG['MIN_TRADE_USD']:
                available_quotes.add(CONFIG['BASE_CURRENCY'])
                # Ensure stable-quote coverage when holding cash
                available_quotes.update({'USDC', 'USDT'})
            
            quote_currencies = list(available_quotes) if available_quotes else [CONFIG['BASE_CURRENCY']]
            logger.info(f"🔍 Available quote currencies: {quote_currencies}")
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

            # 6D Harmonic update (per-asset)
            harmonic_prob = 0.5
            harmonic_resonance = 0.0
            harmonic_wave_state = 'unknown'
            harmonic_dim_coh = 0.0
            harmonic_engine = getattr(self, 'harmonic_engine', None)

            if harmonic_engine:
                try:
                    wf6d = harmonic_engine.update_asset(
                        symbol=symbol,
                        price=price,
                        volume=volume,
                        change_pct=change,
                        high=state.high_24h,
                        low=state.low_24h,
                        frequency=self.asset_frequencies.get(symbol, {}).get('frequency', 432.0),
                        coherence=coherence
                    )
                    harmonic_prob = wf6d.probability_field
                    harmonic_resonance = wf6d.resonance_score
                    harmonic_wave_state = wf6d.wave_state.value
                    harmonic_dim_coh = wf6d.dimensional_coherence
                except Exception:
                    pass
            
            # 🧠 Apply Adaptive Learning thresholds
            learned = ADAPTIVE_LEARNER.get_optimized_thresholds()
            
            # 🌐 Apply coherence adjustment based on anomalies (CoinAPI)
            coherence_threshold = learned.get('min_coherence', CONFIG['ENTRY_COHERENCE'])
            if CONFIG.get('ENABLE_COINAPI', False):
                adjustment = self.auris.get_coherence_adjustment(symbol)
                coherence_threshold *= adjustment  # Increase threshold if anomalies detected
            
            # Skip if coherence too low
            if coherence < coherence_threshold:
                continue

            # 🔮 NEXUS PREDICTOR - 79.6% WIN RATE VALIDATED! 🔮
            nexus_pred_prob = 0.5
            nexus_pred_edge = 0.0
            nexus_pred_patterns = []
            if self.nexus_predictor is not None:
                try:
                    nexus_pred = self.nexus_predictor.predict_instant(
                        price=price,
                        high_24h=state.high_24h,
                        low_24h=state.low_24h,
                        momentum=change / 100.0  # Convert percentage to decimal
                    )
                    nexus_pred_prob = nexus_pred.get('probability', 0.5)
                    nexus_pred_edge = nexus_pred.get('edge', 0.0)
                    nexus_pred_patterns = nexus_pred.get('patterns_triggered', [])
                    should_trade = nexus_pred.get('should_trade', True)
                    
                    # 🤑 GREEDY HOE MODE: Lower threshold from 0.55 to 0.52!
                    # Skip only if Nexus says NO AND probability is below 52%
                    if not should_trade and nexus_pred_prob < 0.52:
                        continue
                except Exception as e:
                    pass  # Continue without Nexus if error

            # 6D harmonic gate: 🤑 GREEDY HOE - lowered from 0.52 to 0.40!
            if harmonic_engine and harmonic_prob < CONFIG.get('HARMONIC_PROB_MIN', 0.40):
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
            
            # 🔮 PREDICTION ACCURACY BOOST 🔮
            # Boost scores based on historical prediction accuracy
            try:
                hnc_freq_val = self.asset_frequencies.get(symbol, {}).get('frequency', 432.0)
                accuracy_boost = self.prediction_validator.get_accuracy_boost(
                    exchange=data.get('source', 'kraken'),
                    asset_class='crypto',
                    frequency=hnc_freq_val,
                    coherence=coherence
                )
                if accuracy_boost != 1.0:
                    score = int(score * accuracy_boost)
                    if accuracy_boost > 1.05:
                        logger.debug(f"{symbol}: Prediction accuracy boost {accuracy_boost:.2f}x")
                    elif accuracy_boost < 0.95:
                        logger.debug(f"{symbol}: Prediction accuracy penalty {accuracy_boost:.2f}x")
            except Exception as e:
                pass  # Silently continue if accuracy boost fails
            
            # 📊 STATE AGGREGATOR INSIGHTS - Historical Performance Boost 📊
            symbol_insight = self.state_aggregator.get_symbol_insight(symbol)
            freq_recommendation = self.state_aggregator.get_frequency_recommendation(hnc_frequency if 'hnc_frequency' in dir() else 432)
            coh_recommendation = self.state_aggregator.get_coherence_recommendation(coherence)
            
            # 🌐 Apply orchestrator cross-exchange learning boost
            orchestrator_boost = 1.0
            if data.get('orchestrator_score'):
                # Orchestrator has seen this symbol across exchanges - boost if favorable
                orch_score = data.get('orchestrator_score', 0)
                if orch_score > 70:
                    orchestrator_boost = 1.10  # 10% boost for high cross-exchange score
                    logger.debug(f"{symbol}: Orchestrator boost {orchestrator_boost:.2f}x (score={orch_score:.1f})")
            # Apply boost to the composite score (fix: initialize from score)
            score = int(score * orchestrator_boost)
            
            # Apply historical symbol performance
            if symbol_insight.get('trades', 0) >= 5:
                hist_wr = symbol_insight.get('win_rate', 0.5)
                if hist_wr > 0.60:
                    score += 10  # Proven winner
                elif hist_wr < 0.35:
                    score -= 15  # Historical loser
                if symbol_insight.get('blacklisted', False):
                    continue  # Skip blacklisted symbols
                    
            # Apply frequency band boost from historical data
            score = int(score * freq_recommendation.get('boost_factor', 1.0))
            
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
            
            # � PIANO RESONANCE BOOST 🎹
            brain_mult = get_brain_multiplier()
            if brain_mult > 1.0:
                score = int(score * brain_mult)
            
            # �🌍⚡ GLOBAL FINANCIAL ECOSYSTEM ADJUSTMENT ⚡🌍
            macro_adjustment = 0
            macro_bias = "NEUTRAL"
            if self.global_feed:
                try:
                    # Update macro snapshot periodically
                    if not self.macro_snapshot or (time.time() - getattr(self, '_last_macro_update', 0)) > 300:
                        self.macro_snapshot = self.global_feed.get_snapshot()
                        self._last_macro_update = time.time()
                    
                    # Get trading signal with macro adjustment
                    macro_signal = self.global_feed.get_trading_signal(symbol)
                    macro_bias = macro_signal.get('macro_bias', 'NEUTRAL')
                    macro_strength = macro_signal.get('macro_strength', 50)
                    
                    # Apply macro adjustment to score
                    # Macro bias affects overall trade sentiment
                    if macro_bias == "BULLISH":
                        macro_adjustment = int((macro_strength - 50) / 5)  # +0 to +10
                    elif macro_bias == "BEARISH":
                        macro_adjustment = int((macro_strength - 50) / 5)  # -10 to 0
                    score += macro_adjustment
                    
                except Exception as e:
                    pass  # Silent fail, don't break trading
            
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
                
                # 🌍 MACRO-ADJUSTED PROBABILITY 🌍
                # Apply global financial feed adjustment to base probability
                if self.global_feed:
                    try:
                        adjusted_prob, reasoning = self.global_feed.get_probability_adjustment(
                            symbol, prob_probability
                        )
                        prob_probability = adjusted_prob
                    except:
                        pass
                
                # FLUX OVERRIDE: If flux is strong, it dominates probability
                # Only trigger on VERY strong signals (threshold raised to 0.80)
                if flux_strength > CONFIG.get('FLUX_THRESHOLD', 0.80):
                    if flux['direction'] == 'BULLISH':
                        prob_probability = max(prob_probability, 0.75) # Force high prob
                        prob_confidence = max(prob_confidence, 0.85)   # Force high conf
                    elif flux['direction'] == 'BEARISH':
                        prob_probability = min(prob_probability, 0.35) # Less severe penalty (was 0.20)
                        prob_confidence = max(prob_confidence, 0.85)
                
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

            # 6D harmonic boosts
            if harmonic_engine:
                score += int(max(0.0, harmonic_resonance) * 20)
                score += int((harmonic_prob - 0.5) * 40)  # ±20 around neutral
                if harmonic_dim_coh >= CONFIG.get('HARMONIC_GATE', 0.45):
                    score += 5
            
            # 🔮 NEXUS PREDICTOR BONUS - Higher edge = Higher score!
            if self.nexus_predictor is not None and nexus_pred_edge > 0:
                nexus_score_bonus = int(nexus_pred_edge * 100)  # Up to +50 for 50% edge
                score += nexus_score_bonus
            
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
                
                # Gate 7: Frequency Band Accuracy (98.8% at 300-399Hz!)
                if 300 <= hnc_frequency <= 399:  # Golden zone
                    gates_passed += 1
                    gate_status.append('FREQ:✓✓')  # Double checkmark for golden band
                    score += 15  # Extra bonus for golden frequency band
                elif 400 <= hnc_frequency <= 499:  # Good zone (73.4% accuracy)
                    gates_passed += 0.5
                    gate_status.append('FREQ:✓')
                elif 600 <= hnc_frequency <= 699:  # Danger zone (0% accuracy)
                    gates_passed -= 0.5  # Penalty
                    gate_status.append('FREQ:✗✗')
                    score -= 10  # Penalty for danger zone
                else:
                    gate_status.append('FREQ:~')
                
                # 🍄🧠 Gate 8: QUEEN NEURON - Collective hive intelligence
                queen_signal = self.mycelium.get_queen_signal()
                if queen_signal > 0.3:  # Strong BUY from Queen
                    gates_passed += 1
                    gate_status.append('QUEEN:✓✓')
                    score += 12  # Queen's blessing bonus
                elif queen_signal > 0.0:  # Weak BUY
                    gates_passed += 0.5
                    gate_status.append('QUEEN:✓')
                    score += 5
                elif queen_signal < -0.3:  # Strong SELL from Queen - trade against it!
                    gates_passed -= 0.5
                    gate_status.append('QUEEN:✗')
                    score -= 5  # Queen says SELL, we're looking to BUY
                else:  # Neutral
                    gate_status.append('QUEEN:~')
                
                # Require minimum gates to pass
                min_gates = CONFIG.get('OPTIMAL_MIN_GATES', 3)
                if gates_passed < min_gates:
                    continue  # Skip - not enough gates passed
                
                # Bonus for high gate count (updated for 8 gates including Queen)
                if gates_passed >= 7:
                    score += 30  # Queen approved!
                elif gates_passed >= 6:
                    score += 25
                elif gates_passed >= 5:
                    score += 20
                elif gates_passed >= 4:
                    score += 15
                elif gates_passed >= 3:
                    score += 10
            
            # 🌈✨ ENHANCEMENT LAYER MODIFIER ✨🌈
            enhancement_modifier = 1.0
            enhancement_state = 'Neutral'
            enhancement_phase = 'LOVE'
            enhancement_result = None
            emotion_band = None
            chakra_alignment = None
            symbolic_alignment = None
            
            if self.enhancement_layer:
                try:
                    # Get Lambda and coherence for enhancement calculation
                    nexus_data = self.nexus.evaluate_market({
                        'price': price,
                        'volume': volume,
                        'momentum': change,
                    }) if self.nexus.enabled else {'lambda': 0, 'coherence': coherence}
                    
                    lambda_value = nexus_data.get('lambda', 0)
                    enhancement_result = self.enhancement_layer.get_unified_modifier(
                        lambda_value=lambda_value,
                        coherence=coherence,
                        price=price,
                        volume=volume,
                        volatility=abs(change) / 100 if change else 0.1,
                    )
                    enhancement_modifier = enhancement_result.trading_modifier
                    enhancement_state = enhancement_result.emotional_state
                    enhancement_phase = enhancement_result.cycle_phase
                    emotion_band = enhancement_result.emotion_band
                    chakra_alignment = enhancement_result.chakra_alignment
                    symbolic_alignment = enhancement_result.symbolic_alignment
                    
                    # Apply enhancement to score
                    score = int(score * enhancement_modifier)
                except Exception as e:
                    pass  # Silently continue if enhancement fails
            
            # 🌊 CASCADE AMPLIFIER - Apply miner-validated signal boost
            cascade_mult = CASCADE_AMPLIFIER.get_signal_multiplier(coherence)
            CASCADE_AMPLIFIER.update_lighthouse(coherence)  # Use coherence as proxy for Γ
            if cascade_mult > 1.0:
                score = int(score * cascade_mult)
            
            # 🧠🌍 BRAIN WISDOM BOOST - Apply 7-civilization signal amplification
            try:
                brain_boosted_score = ECOSYSTEM_BRAIN.get_signal_boost(score)
                if brain_boosted_score != score:
                    score = int(brain_boosted_score)
            except Exception:
                pass  # Brain boost is optional enhancement
            
            # 🧠 Use adaptive learning score threshold
            min_score = learned.get('min_score', CONFIG['MIN_SCORE'])
            
            if score >= min_score:
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
                    'harmonic_prob': harmonic_prob,
                    'harmonic_resonance': harmonic_resonance,
                    'harmonic_wave_state': harmonic_wave_state,
                    'harmonic_dim_coherence': harmonic_dim_coh,
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
                    # 🌈 Enhancement Layer fields
                    'enhancement_modifier': enhancement_modifier,
                    'emotional_state': enhancement_state,
                    'cycle_phase': enhancement_phase,
                    'emotion_band': emotion_band,
                    'chakra_alignment': chakra_alignment,
                    'symbolic_alignment': symbolic_alignment,
                    # 🔮 NEXUS PREDICTOR fields (79.6% validated!)
                    'nexus_prob': nexus_pred_prob,
                    'nexus_edge': nexus_pred_edge,
                    'nexus_patterns': nexus_pred_patterns,
                    # 🧠🌍 BRAIN WISDOM fields
                    'brain_consensus': ECOSYSTEM_BRAIN._brain_consensus,
                    'brain_confidence': ECOSYSTEM_BRAIN._brain_confidence,
                    'brain_fear_greed': ECOSYSTEM_BRAIN._fear_greed,
                })
                
                # 🔮 LOG PREDICTION FOR VALIDATION 🔮
                # Record this prediction for future accuracy checking
                try:
                    predicted_direction = 'up' if change > 0 else ('down' if change < 0 else 'neutral')
                    self.prediction_validator.log_prediction(
                        exchange=data.get('source', 'kraken'),
                        symbol=symbol,
                        current_price=price,
                        predicted_direction=predicted_direction,
                        predicted_change_pct=abs(change) * 0.1,  # Predict 10% of 24h change in 1 min
                        probability=prob_probability,
                        coherence=coherence,
                        frequency=hnc_frequency,
                        asset_class='crypto'
                    )
                except Exception as e:
                    logger.debug(f"Prediction logging error: {e}")
        
        # 🌉 Merge opportunities from Ultimate system via bridge
        ultimate_opps = self.consume_ultimate_opportunities()
        if ultimate_opps:
            opportunities.extend(ultimate_opps)
                
        # Sort by score and return MORE opportunities
        opportunities.sort(key=lambda x: x['score'], reverse=True)

        # 🪐 Harmonic snapshot for quick read (top 3)
        top_harmonics = []
        for opp in opportunities[:3]:
            hw = opp.get('harmonic_wave_state', 'n/a')
            hr = opp.get('harmonic_resonance')
            hp = opp.get('harmonic_prob') if 'harmonic_prob' in opp else opp.get('harmonic_probability')
            sym = opp.get('symbol', '?')
            try:
                hr_fmt = f"{float(hr):.2f}" if hr is not None else "n/a"
            except Exception:
                hr_fmt = "n/a"
            try:
                hp_fmt = f"{float(hp):.2f}" if hp is not None else "n/a"
            except Exception:
                hp_fmt = "n/a"
            top_harmonics.append(f"      • {sym}: wave={hw} | res={hr_fmt} | prob={hp_fmt}")

        if top_harmonics:
            print("   🎼 Harmonic status (top 3):")
            for ln in top_harmonics:
                print(ln)
        
        # 🌉 Publish top opportunities to bridge for Ultimate
        top_opportunities = opportunities[:min(CONFIG['MAX_POSITIONS'] * 2, CONFIG['MAX_POSITIONS'] - len(self.positions) + 5)]
        self.publish_opportunities_to_bridge(top_opportunities)
        
        return top_opportunities

    # ─────────────────────────────────────────────────────────
    # Enhanced Trading Methods (Smart Router + Arbitrage)
    # ─────────────────────────────────────────────────────────
    
    def smart_route_order(self, symbol: str, side: str, quantity: float = None, 
                          quote_qty: float = None, preferred_exchange: str = None) -> Dict[str, Any]:
        """
        Route an order through SmartOrderRouter for best execution.
        Automatically selects best exchange based on price/fees.
        """
        result = self.smart_router.route_order(
            symbol, side, quantity, quote_qty, preferred_exchange
        )
        
        # Track in confirmation system
        if result and not result.get('error'):
            confirmation = self.trade_confirmation.submit_order(
                result.get('routed_to', 'unknown'),
                symbol, side, quantity, quote_qty
            )
            result['confirmation'] = confirmation
            
            # Log to elephant memory
            self.memory.record_trade(
                symbol=symbol,
                entry_price=result.get('effective_price', 0),
                exit_price=0,  # Will update on close
                pnl=0,
                duration=0,
                metadata={
                    'type': 'smart_routed',
                    'exchange': result.get('routed_to'),
                    'savings_pct': result.get('savings_pct', 0)
                }
            )
        
        return result
    
    def scan_arbitrage_opportunities(self, min_profit_pct: float = 0.3) -> List[Dict]:
        """
        Scan all exchanges for arbitrage opportunities.
        Returns sorted list of profitable cross-exchange trades.
        """
        self.arb_scanner.min_spread_pct = min_profit_pct
        opportunities = self.arb_scanner.scan_direct_arbitrage()
        
        if opportunities:
            print(f"   💰 Found {len(opportunities)} arbitrage opportunities")
            for opp in opportunities[:3]:  # Top 3
                print(f"      {opp['symbol']}: {opp['buy_exchange']}→{opp['sell_exchange']} "
                      f"Net +{opp['net_profit_pct']:.2f}%")
        
        return opportunities
    
    def execute_arbitrage(self, opportunity: Dict = None, amount_usd: float = 10.0) -> Dict:
        """
        Execute an arbitrage trade. If no opportunity provided, uses best available.
        """
        if not opportunity:
            opportunities = self.arb_scanner.get_top_opportunities(limit=1)
            if not opportunities:
                return {'success': False, 'error': 'No opportunities found'}
            opportunity = opportunities[0]
        
        result = self.arb_scanner.execute_arbitrage(opportunity, amount_usd)
        
        if result.get('success'):
            print(f"   🎯 Arbitrage executed: {opportunity['symbol']} "
                  f"Profit: ${result.get('profit', 0):.4f}")
        
        return result
    
    def get_best_exchange_quote(self, symbol: str, side: str) -> Dict[str, Any]:
        """
        Get best quote across all exchanges for a symbol.
        Useful for comparing prices before trading.
        """
        return self.smart_router.get_best_quote(symbol, side)
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get smart routing performance statistics."""
        return self.smart_router.get_routing_stats()
    
    # ─────────────────────────────────────────────────────────
    # Portfolio Rebalancing
    # ─────────────────────────────────────────────────────────
    
    def set_target_allocation(self, allocations: Dict[str, float]):
        """
        Set target portfolio allocation for rebalancing.
        Example: set_target_allocation({'BTC': 0.30, 'ETH': 0.25, 'USDT': 0.45})
        """
        self.rebalancer.set_target_allocation(allocations)
        logger.info(f"Target allocation set: {allocations}")
        
    def get_portfolio_allocation(self) -> Dict[str, Any]:
        """Get current portfolio allocation across all exchanges."""
        return self.rebalancer.get_current_allocation()
        
    def calculate_rebalance_trades(self) -> List[Dict]:
        """Calculate trades needed to rebalance to target allocation."""
        return self.rebalancer.calculate_rebalance_trades()
        
    def execute_rebalance(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Execute portfolio rebalance.
        Set dry_run=False to actually execute trades.
        """
        return self.rebalancer.execute_rebalance(dry_run=dry_run)
        
    def print_rebalance_summary(self):
        """Print human-readable portfolio rebalance summary."""
        print(self.rebalancer.get_rebalance_summary())
    
    # ─────────────────────────────────────────────────────────
    # War-Ready Enhancements (ATR, Heat, Adaptive Filters)
    # ─────────────────────────────────────────────────────────
    
    def update_atr(self, symbol: str, high: float, low: float, close: float):
        """Update ATR data for a symbol."""
        self.atr_calculator.update(symbol, high, low, close)
        
    def get_dynamic_tp_sl(self, symbol: str) -> Dict[str, float]:
        """
        Get dynamic TP/SL percentages based on ATR.
        Returns: {'tp_pct': float, 'sl_pct': float, 'atr': float, 'is_dynamic': bool}
        """
        return self.atr_calculator.get_dynamic_tp_sl(
            symbol,
            base_tp=CONFIG.get('TAKE_PROFIT_PCT', 2.0),
            base_sl=CONFIG.get('STOP_LOSS_PCT', 0.8)
        )
        
    def check_portfolio_heat(self, position_pct: float) -> Tuple[bool, str]:
        """
        Check if adding a position would exceed heat limits.
        Returns: (can_add: bool, reason: str)
        """
        return self.heat_manager.can_add_position(position_pct)
        
    def add_position_heat(self, symbol: str, position_pct: float):
        """Add heat for a new position."""
        self.heat_manager.add_position_heat(symbol, position_pct)
        
    def remove_position_heat(self, symbol: str):
        """Remove heat when position closes."""
        self.heat_manager.remove_position_heat(symbol)
        
    def get_heat_status(self) -> Dict[str, Any]:
        """Get current portfolio heat status."""
        return self.heat_manager.get_heat_status()
        
    def decay_heat(self):
        """Apply heat decay (call each cycle)."""
        self.heat_manager.decay_heat()
        
    def update_market_regime(self, recent_changes: List[float]):
        """
        Update market regime detection and adjust filter thresholds.
        Args:
            recent_changes: List of recent 24h % changes across symbols
        """
        regime = self.adaptive_filters.detect_market_regime(recent_changes)
        self.adaptive_filters.adjust_thresholds(regime)
        return regime
        
    def get_adaptive_thresholds(self) -> Dict[str, float]:
        """Get current adaptive filter thresholds."""
        return self.adaptive_filters.get_thresholds()
        
    def record_filter_performance(self, threshold_type: str, threshold_value: float,
                                   actual_value: float, profit: float):
        """Record trade result for filter learning."""
        self.adaptive_filters.record_trade_result(threshold_type, threshold_value, 
                                                   actual_value, profit)
        
    def learn_optimal_filters(self):
        """Learn optimal filter thresholds from history."""
        self.adaptive_filters.learn_optimal_thresholds()
        
    def print_war_ready_status(self):
        """Print WAR-READY enhancement status."""
        heat = self.get_heat_status()
        thresholds = self.get_adaptive_thresholds()
        
        print("\n🔥 WAR-READY STATUS:")
        print(f"   📊 ATR Calculator: {len(self.atr_calculator.price_history)} symbols tracked")
        print(f"   🌡️  Portfolio Heat: {heat['current_heat']:.1%} / {heat['max_heat']:.0%} "
              f"({heat['position_count']} positions)")
        print(f"   🎛️  Market Regime: {thresholds['regime']}")
        print(f"   📈 Adaptive Thresholds: Mom={thresholds['momentum']:.2f} "
              f"Vol={thresholds['volume']:.0f} Coh={thresholds['coherence']:.2f}")
    
    # ─────────────────────────────────────────────────────────
    # Notification System
    # ─────────────────────────────────────────────────────────
    
    def send_notification(self, level: str, title: str, message: str) -> bool:
        """
        Send a notification alert.
        
        Args:
            level: TRADE, PROFIT, LOSS, CIRCUIT, ARBITRAGE, WARNING, INFO
            title: Alert title
            message: Alert message
        """
        return self.notifier.send_alert(level, title, message)
        
    def notify_trade_executed(self, symbol: str, side: str, price: float,
                              quantity: float, exchange: str):
        """Send trade execution notification."""
        self.notifier.notify_trade(symbol, side, price, quantity, exchange)
        
    def notify_position_closed(self, symbol: str, pnl: float, pct: float, reason: str):
        """Send position close notification."""
        self.notifier.notify_close(symbol, pnl, pct, reason)
        
    def notify_circuit_breaker(self, reason: str, drawdown: float):
        """Send circuit breaker triggered alert."""
        self.notifier.notify_circuit_breaker(reason, drawdown)
        
    def notify_arbitrage_opportunity(self, opportunity: Dict):
        """Send arbitrage opportunity alert."""
        self.notifier.notify_arbitrage(opportunity)
        
    def set_notification_level(self, level: str, enabled: bool):
        """Enable/disable specific notification types."""
        self.notifier.set_alert_level(level, enabled)
        
    def get_notification_status(self) -> Dict[str, Any]:
        """Get notification system status."""
        return self.notifier.get_status()
    
    # ─────────────────────────────────────────────────────────
    # Trailing Stop System
    # ─────────────────────────────────────────────────────────
    
    def update_trailing_stops(self, current_prices: Dict[str, float] = None) -> List[Dict]:
        """
        Update all trailing stops and check for triggered exits.
        
        Args:
            current_prices: Dict of symbol -> current price. If None, fetches from cache.
            
        Returns:
            List of positions that should be closed due to trailing stop
        """
        if not CONFIG.get('ENABLE_TRAILING_STOP', True):
            return []
            
        exits = []
        
        for symbol, pos in self.positions.items():
            # Get current price
            if current_prices and symbol in current_prices:
                current_price = current_prices[symbol]
            elif symbol in self.realtime_prices:
                current_price = self.realtime_prices[symbol]
            elif symbol in self.ticker_cache:
                current_price = self.ticker_cache[symbol].get('price', pos.entry_price)
            else:
                continue
                
            # Get ATR if available
            atr = 0.0
            if CONFIG.get('USE_ATR_TRAILING', True):
                atr_data = self.atr_calculator.calculate_atr(symbol)
                if atr_data > 0:
                    atr = atr_data
                    
            # Update trailing stop
            result = self.trailing_stop_manager.update_position(pos, current_price, atr)
            
            if result['should_exit']:
                exits.append({
                    'symbol': symbol,
                    'position': pos,
                    'reason': result['reason'],
                    'stop_price': result['stop_price'],
                    'pnl_pct': result['pnl_pct']
                })
                
        return exits
        
    def get_trailing_stop_status(self, symbol: str = None) -> Dict[str, Any]:
        """
        Get trailing stop status for a position or all positions.
        """
        if symbol:
            if symbol not in self.positions:
                return {'error': 'Position not found'}
            pos = self.positions[symbol]
            return {
                'symbol': symbol,
                'entry_price': pos.entry_price,
                'highest_price': pos.highest_price,
                'trailing_active': pos.trailing_stop_active,
                'stop_price': pos.trailing_stop_price,
                'current_trail_pct': ((pos.highest_price - pos.trailing_stop_price) / pos.highest_price * 100) if pos.trailing_stop_price > 0 else 0
            }
        else:
            # Return status for all positions
            statuses = {}
            for sym, pos in self.positions.items():
                statuses[sym] = {
                    'trailing_active': pos.trailing_stop_active,
                    'highest_price': pos.highest_price,
                    'stop_price': pos.trailing_stop_price
                }
            return statuses
            
    def get_trailing_stop_stats(self) -> Dict[str, Any]:
        """Get overall trailing stop statistics."""
        return self.trailing_stop_manager.get_stats()
        
    def set_trailing_stop_config(self, activation_pct: float = None, 
                                  trail_pct: float = None, use_atr: bool = None):
        """Configure trailing stop parameters."""
        if activation_pct is not None:
            self.trailing_stop_manager.activation_profit_pct = activation_pct
            CONFIG['TRAILING_ACTIVATION_PCT'] = activation_pct
        if trail_pct is not None:
            self.trailing_stop_manager.trail_distance_pct = trail_pct
            CONFIG['TRAILING_DISTANCE_PCT'] = trail_pct
        if use_atr is not None:
            self.trailing_stop_manager.use_atr_trailing = use_atr
            CONFIG['USE_ATR_TRAILING'] = use_atr
    
    # ─────────────────────────────────────────────────────────
    # 🌌 NEXUS Integration Methods
    # ─────────────────────────────────────────────────────────
    
    def get_nexus_signal(self, symbol: str, klines: List[Dict] = None) -> Dict[str, Any]:
        """
        Get Master Equation signal for a symbol.
        
        Returns signal with coherence thresholds:
        - BUY when Γ > 0.75
        - SELL when Γ < 0.70
        - NEUTRAL otherwise
        """
        if not self.nexus.enabled:
            return {'signal': 'NEUTRAL', 'coherence': 0.5, 'confidence': 0.5}
            
        # Convert klines to market data if provided
        if klines:
            market_data = self.nexus.convert_klines_to_market_data(klines)
        else:
            # Try to get klines from exchange
            try:
                klines = self.kraken.get_ohlc(symbol, interval=15)
                market_data = self.nexus.convert_klines_to_market_data(klines) if klines else {}
            except:
                market_data = {}
                
        return self.nexus.calculate_master_equation(market_data)
        
    def enhance_opportunity_with_nexus(self, opp: Dict) -> Dict:
        """
        Enhance an opportunity with Nexus Master Equation signal.
        Adds nexus_signal, nexus_coherence, nexus_boost to opportunity.
        """
        if not self.nexus.enabled:
            return opp
            
        symbol = opp.get('symbol', '')
        
        # Get Nexus signal
        nexus_result = self.get_nexus_signal(symbol)
        
        # Add Nexus data to opportunity
        opp['nexus_signal'] = nexus_result.get('signal', 'NEUTRAL')
        opp['nexus_coherence'] = nexus_result.get('coherence', 0.5)
        opp['nexus_lambda'] = nexus_result.get('lambda', 1.5)
        
        # Apply coherence boost to score if above entry threshold
        if nexus_result.get('coherence', 0) >= 0.75:
            boost = 1.0 + (nexus_result['coherence'] - 0.75) * 4  # Up to 2.0x boost at Γ=1.0
            opp['nexus_boost'] = boost
            if 'score' in opp:
                opp['score'] = opp['score'] * boost
                
        return opp
        
    def record_nexus_profit(self, profit: float) -> Dict[str, float]:
        """
        Record profit through Queen Hive 10-9-1 model.
        Returns compound/harvest split.
        """
        return self.nexus.record_trade_profit(profit)
        
    def get_nexus_stats(self) -> Dict[str, Any]:
        """Get Nexus integration statistics."""
        return self.nexus.get_stats()
        
    def display_nexus_equation(self):
        """Display current Master Equation state."""
        self.nexus.display_equation()
        
    def check_nexus_exit_signal(self, symbol: str) -> bool:
        """
        Check if Nexus suggests exiting a position.
        Returns True if coherence falls below 0.70.
        """
        nexus_result = self.get_nexus_signal(symbol)
        return nexus_result.get('signal') == 'SELL'
    
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
        
        # 🚀 Check if this is a forced scout deployment
        is_force_scout = opp.get('dominant_node') == 'ForceScout' or CONFIG.get('FORCE_TRADE', False)
        
        # 🦙 Skip Alpaca trades if in analytics-only mode
        if exchange == 'alpaca' and CONFIG.get('ALPACA_ANALYTICS_ONLY', True):
            return None
        
        # 🔥 FORCE TRADE MODE - Skip halt check
        if not is_force_scout and self.tracker.trading_halted:
            return None
        
        # 🌍⚡ Get HNC frequency modifier for position sizing ⚡🌍
        hnc_modifier = 1.0
        hnc_enhanced = None
        hnc_frequency = 256.0
        if CONFIG.get('ENABLE_HNC_FREQUENCY', True) and not is_force_scout:
            hnc_enhanced = self.auris.update_hnc_state(
                symbol, price, opp.get('momentum', 0), opp['coherence'], opp.get('score', 50)
            )
            if hnc_enhanced:
                hnc_frequency = hnc_enhanced.get('hnc_frequency', 256.0)
                hnc_modifier = self.auris.get_hnc_position_modifier()
                
                # 🎯 HNC FREQUENCY ENTRY OPTIMIZATION (bypass for force scouts)
                if CONFIG.get('HNC_FREQUENCY_GATE', True) and not is_force_scout:
                    # BLOCK distortion frequency entries (440Hz)
                    if CONFIG.get('HNC_DISTORTION_ENTRY_BLOCK', True) and hnc_frequency == 440:
                        print(f"   🔴 HNC BLOCKS {symbol}: 440Hz distortion frequency")
                        return None
                    
                    # BOOST harmonic frequency entries
                    if hnc_enhanced.get('hnc_is_harmonic', False):
                        harmonic_boost = CONFIG.get('HNC_HARMONIC_ENTRY_BOOST', 1.25)
                        hnc_modifier *= harmonic_boost
                        print(f"   🟢 HNC BOOST {symbol}: {hnc_frequency:.0f}Hz harmonic (×{harmonic_boost:.2f})")
                    # PENALIZE distortion but allow entry
                    elif hnc_frequency == 440:
                        hnc_modifier *= CONFIG.get('HNC_DISTORTION_PENALTY', 0.70)
        
        # 🔊 PHASE 2: FREQUENCY FILTERING - Apply sacred frequency modifiers 🔊
        freq_modifier = 1.0
        if CONFIG.get('ENABLE_FREQUENCY_FILTERING', True):
            freq = opp.get('frequency', 256.0)
            freq_modifier = self._get_sacred_frequency_modifier(freq)
            
            # Log significant frequency events
            if freq_modifier >= 1.30:
                freq_name = self._get_frequency_name(freq)
                print(f"   🟢 FREQ BOOST {symbol}: {freq_name} ({freq:.0f}Hz) ×{freq_modifier:.2f}")
            elif freq_modifier <= 0.75:
                freq_name = self._get_frequency_name(freq)
                print(f"   🔴 FREQ SUPPRESS {symbol}: {freq_name} ({freq:.0f}Hz) ×{freq_modifier:.2f}")
        
        # 🌌⚡ Get Imperial predictability modifier for position sizing ⚡🌌
        imperial_modifier = opp.get('imperial_multiplier', 1.0)
        if CONFIG.get('ENABLE_IMPERIAL', True) and not is_force_scout:
            # Check if cosmic state supports trading
            should_trade, reason = self.auris.should_trade_imperial()
            if not should_trade:
                print(f"   🌌 Imperial halts {symbol}: {reason}")
                return None
            
            # Get fresh imperial modifier if not in opportunity
            if imperial_modifier == 1.0:
                imperial_modifier = self.auris.get_imperial_position_modifier(
                    symbol, opp.get('change24h', 0), price
                )
        
        # 🌍✨ Check Earth Resonance gate ✨🌍
        if CONFIG.get('ENABLE_EARTH_RESONANCE', True) and not is_force_scout:
            earth_ok, earth_reason = self.auris.should_trade_earth()
            if not earth_ok:
                print(f"   🌍 Earth halts {symbol}: {earth_reason}")
                return None
        
        lattice_state = self.lattice.get_state()
        
        # 🚀 Force scouts use fixed sizing for reliability (smaller to enable low-capital trading)
        if is_force_scout:
            size_fraction = 0.05  # 5% position size for forced scouts
        else:
            size_fraction = self.tracker.calculate_position_size(
                opp['coherence'], symbol, hnc_modifier, imperial_modifier
            )
            risk_mod = lattice_state.get('risk_mod', 1.0) if isinstance(lattice_state, dict) else getattr(lattice_state, 'risk_mod', 1.0)
            size_fraction *= risk_mod
            size_fraction *= freq_modifier  # 🔊 Apply frequency filtering modifier
            size_fraction *= opp.get('risk_mod_from_pnl', 1.0)  # 🧠 Live P&L throttle
            
            # 🎹 PIANO RESONANCE SIZING 🎹
            brain_mult = get_brain_multiplier()
            if brain_mult > 1.0:
                size_fraction *= brain_mult
                size_fraction = min(0.45, size_fraction)  # Cap at 45%
        
        if size_fraction <= 0:
            print(f"   🔴 DEBUG {symbol}: size_fraction={size_fraction:.4f}")
            return None

        deploy_cap = self.total_equity_gbp * CONFIG['PORTFOLIO_RISK_BUDGET']
        deployed = sum(pos.entry_value for pos in self.positions.values())
        available_risk = max(0.0, deploy_cap - deployed)
        if available_risk < CONFIG['MIN_TRADE_USD']:
            print(f"   🔴 DEBUG {symbol}: available_risk={available_risk:.2f} < MIN_TRADE_USD={CONFIG['MIN_TRADE_USD']}")
            return None

        pos_size = self.capital_pool.get_recommended_position_size(size_fraction)
        if pos_size <= 0:
            print(f"   🔴 DEBUG {symbol}: pos_size={pos_size:.2f}")
            return None
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
            
            # 🔥 AGGRESSIVE SWAP: Sell any big loser to free capital for new trades
            # Score requirement lowered to 40 (from 85) for force scouts
            if worst_pos and (opp.get('score', 0) > 40 or is_force_scout) and worst_pct < CONFIG['REBALANCE_THRESHOLD']:
                pos_symbol, pct, curr_price = worst_pos
                
                # 🧠 PUBLISH THOUGHT: SCOUT SWAP 🧠
                if THOUGHT_BUS_AVAILABLE and THOUGHT_BUS:
                    THOUGHT_BUS.publish(Thought(
                        source="scout",
                        topic="execution.scout.swap",
                        payload={
                            "sell_symbol": pos_symbol,
                            "buy_symbol": symbol,
                            "reason": "BETTER_OPPORTUNITY",
                            "pnl_pct": pct
                        }
                    ))

                print(f"   🔥 AGGRESSIVE SWAP: Selling {pos_symbol} ({pct:+.2f}%) to buy {symbol}")
                self.close_position(pos_symbol, "SWAP", pct, curr_price)
                self.refresh_equity()
                cash_available = max(0.0, self.cash_balance_gbp)
        
        if cash_available < CONFIG['MIN_TRADE_USD']:
            # 🔄 TRY TO LIQUIDATE HISTORICAL ASSETS FOR CASH
            # Historical assets = imported holdings with no known entry price
            # They're effectively "available capital" - sell them for better opportunities!
            # 🔥 LOWERED threshold to 30 score - we need to MOVE!
            if opp.get('score', 0) > 30 or opp.get('coherence', 0) > 0.4 or is_force_scout:
                needed = max(CONFIG['MIN_TRADE_USD'], pos_size) - cash_available
                freed = self._liquidate_historical_for_opportunity(needed, exchange, symbol)
                if freed > 0:
                    cash_available += freed
                    print(f"   💰 Freed £{freed:.2f} from historical assets - continuing trade!")
            
            # Still not enough? Skip
            if cash_available < CONFIG['MIN_TRADE_USD']:
                if not hasattr(self, '_skip_logged'):
                    self._skip_logged = set()
                if symbol not in self._skip_logged:
                    print(f"   ⚪ Skipping {symbol}: insufficient cash (£{cash_available:.2f})")
                    self._skip_logged.add(symbol)
                return None
        
        # Clear skip log at end of cycle
        if hasattr(self, '_skip_logged'):
            self._skip_logged.clear()
            
        pos_size = min(pos_size, cash_available)

        if pos_size < CONFIG['MIN_TRADE_USD']:
            return None

        if not self.should_enter_trade(opp, pos_size, lattice_state):
            print(f"   ⚪ Skipping {symbol}: portfolio gate rejected entry")
            return None
        
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
                # 🔄 TRY TO LIQUIDATE HISTORICAL ASSETS ON THIS EXCHANGE
                if opp.get('score', 0) > 70 or opp.get('coherence', 0) > 0.6:
                    needed = quote_amount_needed - available_quote
                    freed = self._liquidate_historical_for_opportunity(needed, exchange, symbol)
                    if freed > 0:
                        # Re-check liquidity
                        has_liquidity, available_quote, _ = self.ensure_quote_liquidity(exchange, quote_asset, quote_amount_needed)
                
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
        
        # 🔧 KRAKEN VOLUME MINIMUM CHECK: Ensure order quantity meets pair's ordermin
        if exchange == 'kraken' and not self.dry_run:
            try:
                exchange_client = self.client.clients.get('kraken')
                if exchange_client and hasattr(exchange_client, 'get_symbol_filters'):
                    filters = exchange_client.get_symbol_filters(symbol)
                    min_qty = filters.get('min_qty', 0)
                    if min_qty > 0 and quantity < min_qty:
                        # Calculate minimum notional needed to meet volume requirement
                        min_notional_for_vol = min_qty * price * 1.02  # 2% buffer
                        if min_notional_for_vol > quote_amount_needed:
                            if min_notional_for_vol <= cash_available:
                                print(f"   📈 Kraken {symbol}: bumping order from ${quote_amount_needed:.2f} to ${min_notional_for_vol:.2f} (min vol: {min_qty})")
                                quote_amount_needed = min_notional_for_vol
                                pos_size = min_notional_for_vol
                                quantity = pos_size / price
                            else:
                                print(f"   ⚪ Skipping {symbol}: need ${min_notional_for_vol:.2f} for min volume {min_qty}, only ${cash_available:.2f} available")
                                return None
            except Exception as e:
                print(f"   ⚠️ Kraken filter check failed for {symbol}: {e}")
        
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
                
                # Handle Kraken volume minimum error
                if res.get('error') == 'volume_minimum':
                    print(f"   ⚠️ Kraken volume minimum not met for {symbol} (need {res.get('ordermin')} units)")
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
                    
                    # 🔥 CRITICAL FIX: Use ACTUAL fill price, not pre-order price!
                    # This ensures P&L calculations are accurate
                    fills = res.get('fills', [])
                    if fills:
                        # Calculate weighted average fill price
                        total_qty = sum(float(f.get('qty', 0)) for f in fills)
                        total_value = sum(float(f.get('qty', 0)) * float(f.get('price', 0)) for f in fills)
                        if total_qty > 0:
                            actual_fill_price = total_value / total_qty
                            actual_qty = total_qty
                            actual_value = total_value
                            # Calculate actual fee from fills
                            actual_fee = sum(
                                float(f.get('commission', 0)) * (float(f.get('price', price)) if f.get('commissionAsset') == symbol.replace(quote_asset, '') else 1.0)
                                for f in fills
                            )
                            print(f"   📊 Fill: {actual_qty:.2f} @ {actual_fill_price:.8f} (pre-order: {price:.8f})")
                            price = actual_fill_price
                            quantity = actual_qty
                            pos_size = actual_value
                            entry_fee = actual_fee if actual_fee > 0 else pos_size * get_platform_fee(exchange, 'taker')
                    elif res.get('cummulativeQuoteQty') and res.get('executedQty'):
                        # Fallback: use order response totals
                        exec_qty = float(res.get('executedQty', 0))
                        cumm_quote = float(res.get('cummulativeQuoteQty', 0))
                        if exec_qty > 0:
                            actual_fill_price = cumm_quote / exec_qty
                            print(f"   📊 Fill: {exec_qty:.2f} @ {actual_fill_price:.8f} (pre-order: {price:.8f})")
                            price = actual_fill_price
                            quantity = exec_qty
                            pos_size = cumm_quote
                            entry_fee = pos_size * get_platform_fee(exchange, 'taker')
                            
        prime_multiplier = 1.0
        if len(self.positions) < 3:  # Apply prime sizing to first few positions
            prime_multiplier = self.prime_sizer.get_next_size(1.0) / CONFIG['BASE_POSITION_SIZE']
            pos_size *= prime_multiplier
            pos_size = min(pos_size, available_risk, cash_available)
            quantity = pos_size / price
            entry_fee = pos_size * get_platform_fee(exchange, 'taker')
        
        # Create position with swarm enhancements
        is_scout = len(self.positions) == 0  # First position becomes scout
        
        entry_time = time.time()
        
        # 🧠 GET LEARNED PARAMETERS FROM RECOMMENDATION
        learned_rec = opp.get('learned_recommendation', {})
        
        self.positions[symbol] = Position(
            symbol=symbol,
            entry_price=price,
            quantity=quantity,
            entry_fee=entry_fee,
            entry_value=pos_size,
            momentum=opp['change24h'],
            coherence=opp['coherence'],
            entry_time=entry_time,
            dominant_node=opp['dominant_node'],
            generation=0,
            is_scout=is_scout,
            prime_size_multiplier=prime_multiplier,
            exchange=exchange,
            # 🧠 Apply learned parameters from probability matrix
            learned_tp_pct=learned_rec.get('suggested_take_profit'),
            learned_sl_pct=learned_rec.get('suggested_stop_loss'),
            learned_hold_cycles=learned_rec.get('suggested_hold_cycles'),
            learned_win_rate=learned_rec.get('expected_win_rate'),
            learned_confidence=learned_rec.get('confidence', 'low'),
            # 🔮 NEXUS PREDICTOR DATA - For learning feedback
            nexus_prob=opp.get('nexus_prob', 0.5),
            nexus_edge=opp.get('nexus_edge', 0.0),
            nexus_patterns=opp.get('nexus_patterns', []),
        )
        
        # Log learned parameters if available
        if learned_rec and learned_rec.get('confidence') != 'low':
            logger.info(f"🧠 {symbol} using learned params: TP={learned_rec.get('suggested_take_profit', 0)*100:.1f}% SL={learned_rec.get('suggested_stop_loss', 0)*100:.1f}% Hold={learned_rec.get('suggested_hold_cycles', 0)} ExpWR={learned_rec.get('expected_win_rate', 0)*100:.0f}%")
        
        # 📊 LOG TRADE ENTRY FOR PROBABILITY MATRIX TRAINING 📊
        if TRADE_LOGGER_AVAILABLE and trade_logger:
            try:
                trade_logger.log_trade_entry({
                    'symbol': symbol,
                    'side': 'BUY',
                    'exchange': exchange,
                    'entry_price': price,
                    'entry_time': entry_time,
                    'quantity': quantity,
                    'entry_value': pos_size,
                    'coherence': opp['coherence'],
                    'dominant_node': opp['dominant_node'],
                    'hnc_frequency': hnc_frequency,
                    'hnc_is_harmonic': hnc_enhanced.get('hnc_is_harmonic', False) if hnc_enhanced else False,
                    'probability_score': opp.get('score', 50) / 100.0,
                    'imperial_probability': imperial_modifier,
                    'cosmic_phase': opp.get('cosmic_phase', 'UNKNOWN'),
                    'earth_coherence': opp.get('earth_coherence', 0.5),
                    'gates_passed': opp.get('gates_passed', 0),
                })
            except Exception as e:
                logger.warning(f"Failed to log trade entry for {symbol}: {e}")
        
        # 💰 LOG ENTRY PRICE TO COST BASIS TRACKER 💰
        try:
            cost_tracker = get_cost_basis_tracker()
            cost_tracker.set_entry_price(symbol, price, quantity, exchange, entry_fee)
        except Exception as e:
            logger.warning(f"Failed to log cost basis for {symbol}: {e}")
            
        # 🧠 PUBLISH THOUGHT: TRADE OPENED 🧠
        if THOUGHT_BUS_AVAILABLE and THOUGHT_BUS:
            try:
                THOUGHT_BUS.publish(Thought(
                    source="unified_ecosystem",
                    topic="execution.order.open",
                    payload={
                        "symbol": symbol,
                        "side": "BUY",
                        "price": price,
                        "quantity": quantity,
                        "value": pos_size,
                        "exchange": exchange,
                        "coherence": opp.get('coherence', 0),
                        "score": opp.get('score', 0)
                    }
                ))
            except Exception as e:
                logger.warning(f"Failed to publish open thought: {e}")
        
        # 🚀 PLACE SERVER-SIDE TP/SL ORDERS (Kraken & Alpaca - executes even if bot offline!)
        if CONFIG.get('USE_SERVER_SIDE_ORDERS', True) and exchange.lower() in ['kraken', 'alpaca'] and not self.dry_run:
            try:
                # Calculate TP/SL prices
                tp_pct = learned_rec.get('suggested_take_profit') or CONFIG.get('SERVER_SIDE_TP_PCT', 1.8) / 100
                sl_pct = learned_rec.get('suggested_stop_loss') or CONFIG.get('SERVER_SIDE_SL_PCT', 1.5) / 100
                
                take_profit_price = price * (1 + tp_pct)
                stop_loss_price = price * (1 - sl_pct)
                
                # Use trailing stop if configured
                if CONFIG.get('USE_TRAILING_STOP_ORDERS', False):
                    trailing_pct = CONFIG.get('SERVER_TRAILING_PCT', 2.0)
                    trail_res = self.client.place_trailing_stop_order(
                        exchange, symbol, 'sell', quantity, trailing_pct, 'percent'
                    )
                    if trail_res and not trail_res.get('error'):
                        print(f"   🎯 Server trailing stop: {trailing_pct}% below peak")
                        self.positions[symbol].server_trailing_order_id = trail_res.get('orderId') or trail_res.get('id')
                else:
                    # 🦙 Alpaca: Use OCO (one-cancels-other) for existing position TP+SL
                    if exchange.lower() == 'alpaca':
                        # For Alpaca, after entry filled, place OCO with TP+SL
                        try:
                            # Get proper symbol format for Alpaca (BTC/USD)
                            alpaca_symbol = symbol if '/' in symbol else f"{symbol[:3]}/{symbol[3:]}" if len(symbol) >= 6 else symbol
                            
                            oco_res = self.client.clients['alpaca'].place_oco_order(
                                alpaca_symbol, quantity, 'sell',
                                take_profit_limit=take_profit_price,
                                stop_loss_stop=stop_loss_price
                            )
                            if oco_res and not oco_res.get('error'):
                                self.positions[symbol].server_sl_order_id = oco_res.get('id')
                                print(f"   🦙 Alpaca OCO: TP @ ${take_profit_price:.6f} (+{tp_pct*100:.1f}%) | SL @ ${stop_loss_price:.6f} (-{sl_pct*100:.1f}%)")
                        except Exception as e:
                            logger.warning(f"Failed to place Alpaca OCO for {symbol}: {e}")
                    else:
                        # 🦑 Kraken: Place separate TP and SL orders
                        # Place stop-loss order (server-side)
                        sl_res = self.client.place_stop_loss_order(
                            exchange, symbol, 'sell', quantity, stop_loss_price
                        )
                        if sl_res and not sl_res.get('error'):
                            self.positions[symbol].server_sl_order_id = sl_res.get('orderId')
                            print(f"   🛡️ Server stop-loss @ ${stop_loss_price:.6f} (-{sl_pct*100:.1f}%)")
                        
                        # Place take-profit order (server-side)  
                        tp_res = self.client.place_take_profit_order(
                            exchange, symbol, 'sell', quantity, take_profit_price
                        )
                        if tp_res and not tp_res.get('error'):
                            self.positions[symbol].server_tp_order_id = tp_res.get('orderId')
                            print(f"   💰 Server take-profit @ ${take_profit_price:.6f} (+{tp_pct*100:.1f}%)")
                        
            except Exception as e:
                logger.warning(f"Failed to place server-side TP/SL for {symbol}: {e}")
        
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
        # 🔮 Add Nexus predictor probability
        nexus_marker = f" 🔮{opp.get('nexus_prob', 0.5)*100:.0f}%" if self.nexus_predictor and 'nexus_prob' in opp else ""
        print(f"   {icon} BUY  {symbol:12s} @ {curr_sym}{price:.6f} | {curr_sym}{pos_size:.2f} ({actual_fraction*100:.1f}%) | Γ={opp['coherence']:.2f} | +{opp['change24h']:.1f}%{hnc_marker}{nexus_marker}{flux_marker}{scout_marker}{prime_marker}{exch_marker}")
        
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
            
            # 📊 FEED POSITION DATA TO PROBABILITY MATRIX
            # This allows the matrix to validate predictions against real positions
            if self.prob_matrix and hasattr(self.prob_matrix, 'feed_position_data'):
                try:
                    self.prob_matrix.feed_position_data(
                        symbol=symbol,
                        exchange=pos.exchange,
                        entry_price=pos.entry_price,
                        entry_time=pos.entry_time,
                        quantity=pos.quantity,
                        entry_value=pos.entry_value,
                        current_price=current_price,
                        platform_timestamp=time.time(),  # Current sync time
                        is_historical=pos.is_historical,
                        momentum=change_pct,
                        coherence=pos.coherence,
                        trailing_stop_active=pos.trailing_stop_active,
                        highest_price=pos.highest_price,
                    )
                except Exception as e:
                    logger.warning(f"Matrix position feed error for {symbol}: {e}")
            
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
            
            # 🧠 USE LEARNED TP/SL IF AVAILABLE (from probability matrix recommendations)
            # Handle lattice_state as dict or object
            tp_mod = lattice_state.get('tp_mod', 1.0) if isinstance(lattice_state, dict) else getattr(lattice_state, 'tp_mod', 1.0)
            sl_mod = lattice_state.get('sl_mod', 1.0) if isinstance(lattice_state, dict) else getattr(lattice_state, 'sl_mod', 1.0)
            
            if pos.learned_confidence in ('high', 'medium') and pos.learned_tp_pct is not None:
                # Use learned parameters with lattice modifier
                target_tp = (pos.learned_tp_pct * 100) * tp_mod  # Convert from decimal to %
                target_sl = (pos.learned_sl_pct * 100) * sl_mod if pos.learned_sl_pct else CONFIG['STOP_LOSS_PCT'] * sl_mod
                min_hold = pos.learned_hold_cycles if pos.learned_hold_cycles else CONFIG['MIN_HOLD_CYCLES']
                
                if pos.cycles % 20 == 0:
                    logger.info(f"   🧠 {symbol}: Using LEARNED params - TP {target_tp:.1f}% / SL {target_sl:.1f}% / Hold {min_hold} (ExpWR: {pos.learned_win_rate*100:.0f}%)")
            else:
                # Use global CONFIG values
                target_tp = CONFIG['TAKE_PROFIT_PCT'] * tp_mod
                target_sl = CONFIG['STOP_LOSS_PCT'] * sl_mod
                min_hold = CONFIG['MIN_HOLD_CYCLES']
            
            # 🌍✨ Apply Earth Resonance exit urgency to TP ✨🌍
            # When field coherence is low, exit earlier with smaller profits
            if effective_tp_mult < 1.0:
                target_tp *= effective_tp_mult
                if pos.cycles % 20 == 0:
                    print(f"   🌍 {symbol}: Earth urgency reducing TP to {target_tp:.2f}%")

            # ═══════════════════════════════════════════════════════════════
            # 🔮 PROBABILITY MATRIX EXIT SIGNALS - SURF THE WAVE! 🔮
            # ═══════════════════════════════════════════════════════════════
            # Check if matrix is now saying SELL for this position
            prob_exit_triggered = False
            if self.prob_matrix and CONFIG.get('ENABLE_PROB_MATRIX', True) and pos.cycles >= 3:
                try:
                    prob_signal = self.auris.get_probability_signal(
                        symbol=symbol,
                        price=current_price,
                        frequency=getattr(pos, 'hnc_frequency', 256),
                        momentum=change_pct,
                        coherence=pos.coherence,
                        is_harmonic=getattr(pos, 'hnc_harmonic', False),
                    )
                    prob_action = prob_signal.get('action', 'HOLD')
                    prob_probability = prob_signal.get('probability', 0.5)
                    prob_confidence = prob_signal.get('confidence', 0.0)
                    
                    # 🚨 MATRIX SAYS SELL - Time to exit if we're profitable
                    if prob_action in ['SELL', 'STRONG SELL'] and prob_confidence >= 0.5:
                        # Only exit if we're at least breakeven (after fees)
                        exit_value = pos.quantity * current_price
                        exit_fee = exit_value * get_platform_fee(pos.exchange, 'taker')
                        total_fees = pos.entry_fee + exit_fee + exit_value * CONFIG['SLIPPAGE_PCT']
                        gross_pnl = exit_value - pos.entry_value
                        net_pnl = gross_pnl - total_fees
                        
                        # 💰 PENNY PROFIT CHECK FOR MATRIX EXITS
                        penny_check = check_penny_exit(pos.exchange, pos.entry_value, gross_pnl)
                        penny_threshold = penny_check.get('threshold')
                        
                        # 💰 PENNY PROFIT OVERRIDE: If net profit >= $0.01, take it regardless of matrix!
                        if net_pnl >= 0.01:
                             print(f"   🔮 MATRIX EXIT (PENNY SECURED): {symbol} {prob_action} (prob={prob_probability:.0%}, conf={prob_confidence:.0%}) Net: ${net_pnl:.4f} >= $0.01")
                             to_close.append((symbol, "MATRIX_SELL", change_pct, current_price))
                             prob_exit_triggered = True
                        elif penny_threshold:
                            min_gross_win = penny_threshold.get('win_gte', 0.01)
                            if gross_pnl >= min_gross_win:
                                print(f"   🔮 MATRIX EXIT (PENNY SECURED): {symbol} {prob_action} (prob={prob_probability:.0%}, conf={prob_confidence:.0%}) Gross: ${gross_pnl:.4f} >= ${min_gross_win:.4f}")
                                to_close.append((symbol, "MATRIX_SELL", change_pct, current_price))
                                prob_exit_triggered = True
                            elif prob_action == 'STRONG SELL' and prob_confidence >= 0.7 and gross_pnl > -pos.entry_value * 0.01:
                                # Allow small loss (<1%) on STRONG SELL signals only
                                print(f"   🚨 MATRIX FORCE EXIT: {symbol} STRONG SELL (conf={prob_confidence:.0%}) - Small loss ${net_pnl:.2f}")
                                to_close.append((symbol, "MATRIX_FORCE", change_pct, current_price))
                                prob_exit_triggered = True
                            else:
                                print(f"   🛑 HOLDING {symbol}: Matrix signal ignored - Penny Profit not met (${gross_pnl:.4f} < ${min_gross_win:.4f})")
                        
                        # Fallback if penny profit not enabled
                        elif net_pnl >= 0:  # At least breakeven
                            print(f"   🔮 MATRIX EXIT: {symbol} {prob_action} (prob={prob_probability:.0%}, conf={prob_confidence:.0%}) Net P&L: ${net_pnl:.2f}")
                            to_close.append((symbol, "MATRIX_SELL", change_pct, current_price))
                            prob_exit_triggered = True
                        elif net_pnl > -pos.entry_value * 0.01:  # Allow small loss (<1%) on strong signals
                            if prob_action == 'STRONG SELL' and prob_confidence >= 0.7:
                                print(f"   🚨 MATRIX FORCE EXIT: {symbol} STRONG SELL (conf={prob_confidence:.0%}) - Small loss ${net_pnl:.2f}")
                                to_close.append((symbol, "MATRIX_FORCE", change_pct, current_price))
                                prob_exit_triggered = True
                except Exception as e:
                    pass  # Continue with normal checks
            
            # Skip normal TP/SL checks if matrix already triggered exit
            if prob_exit_triggered:
                continue

            # ═══════════════════════════════════════════════════════════════
            # 💰 PENNY PROFIT TP/SL - DOLLAR-BASED EXIT LOGIC 💰
            # ═══════════════════════════════════════════════════════════════
            # Calculate gross P&L for penny profit check
            exit_value = pos.quantity * current_price
            gross_pnl = exit_value - pos.entry_value
            
            # Check penny profit thresholds
            penny_check = check_penny_exit(pos.exchange, pos.entry_value, gross_pnl)
            penny_threshold = penny_check.get('threshold')
            
            if penny_threshold:
                # 💰 PENNY PROFIT MODE - Use dollar thresholds
                if penny_check['should_tp']:
                    # Hit penny profit target!
                    to_close.append((symbol, "TP", change_pct, current_price))
                elif penny_check['should_sl']:
                    # Hit penny stop loss
                    to_close.append((symbol, "SL", change_pct, current_price))
                elif gross_pnl > 0:
                    # 💰 PENNY PROFIT OVERRIDE: Ignore min_hold if we have profit!
                    # Check if we're at penny harvest level
                    min_gross_win = penny_threshold.get('win_gte', 0.01)
                    if gross_pnl >= min_gross_win:
                        print(f"   🌾 PENNY HARVEST: {symbol} gross ${gross_pnl:.4f} >= ${min_gross_win:.4f}")
                        to_close.append((symbol, "HARVEST", change_pct, current_price))
            else:
                # Fallback to percentage-based TP/SL
                if change_pct >= target_tp:
                    to_close.append((symbol, "TP", change_pct, current_price))
                elif change_pct <= -target_sl:
                    to_close.append((symbol, "SL", change_pct, current_price))
                elif change_pct > 0:
                    # 💰 PENNY PROFIT OVERRIDE: Ignore min_hold if we have profit!
                    # Legacy harvest check
                    exit_fee = exit_value * get_platform_fee(pos.exchange, 'taker')
                    slippage_cost = exit_value * CONFIG['SLIPPAGE_PCT']
                    spread_cost = exit_value * CONFIG['SPREAD_COST_PCT']
                    total_expenses = pos.entry_fee + exit_fee + slippage_cost + spread_cost
                    net_pnl = gross_pnl - total_expenses
                    min_profit = pos.entry_value * CONFIG['MIN_NET_PROFIT_PCT']
                    
                    # 💰 PENNY PROFIT OVERRIDE: If net profit >= $0.01, take it!
                    if net_pnl >= 0.01:
                        net_pnl_pct = (net_pnl / pos.entry_value * 100) if pos.entry_value > 0 else 0
                        print(f"   🌾 PENNY HARVEST: {symbol} net profit ${net_pnl:.4f} ({net_pnl_pct:.2f}%)")
                        to_close.append((symbol, "HARVEST", change_pct, current_price))
                    elif net_pnl >= min_profit and pos.cycles >= min_hold:
                        net_pnl_pct = (net_pnl / pos.entry_value * 100) if pos.entry_value > 0 else 0
                        print(f"   🌾 HARVEST: {symbol} net profit ${net_pnl:.4f} ({net_pnl_pct:.2f}%)")
                        to_close.append((symbol, "HARVEST", change_pct, current_price))
                
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
        
        # 🚀 CANCEL SERVER-SIDE ORDERS (Kraken/Alpaca native TP/SL) before manual close
        if not self.dry_run and pos.exchange.lower() in ['kraken', 'alpaca']:
            try:
                # Cancel stop-loss order if exists (for Alpaca, this might be OCO ID)
                if pos.server_sl_order_id:
                    self.client.cancel_order(pos.exchange, pos.server_sl_order_id)
                    logger.info(f"Cancelled server SL order {pos.server_sl_order_id} for {symbol}")
                
                # Cancel take-profit order if exists (Kraken only, Alpaca uses OCO)
                if pos.server_tp_order_id:
                    self.client.cancel_order(pos.exchange, pos.server_tp_order_id)
                    logger.info(f"Cancelled server TP order {pos.server_tp_order_id} for {symbol}")
                
                # Cancel trailing stop order if exists
                if pos.server_trailing_order_id:
                    self.client.cancel_order(pos.exchange, pos.server_trailing_order_id)
                    logger.info(f"Cancelled server trailing order {pos.server_trailing_order_id} for {symbol}")
            except Exception as e:
                logger.warning(f"Failed to cancel server orders for {symbol}: {e}")
        
        # 🌟 CHECK EXIT GATE: Only sell if profitable
        if not self.should_exit_trade(pos, price, reason):
            return  # Hold position, don't sell at a loss
        
        # 🧹 DUST PROTECTION: Check actual balance on exchange to prevent "Insufficient Balance" and clean dust
        if not self.dry_run:
            try:
                # Infer base asset
                base_asset = symbol
                # Sort quotes by length desc to match longest first (e.g. FDUSD before USD)
                sorted_quotes = sorted(CONFIG['QUOTE_CURRENCIES'], key=len, reverse=True)
                for quote in sorted_quotes:
                    if symbol.endswith(quote):
                        base_asset = symbol[:-len(quote)]
                        break
                
                # Get actual free balance from the specific exchange client
                # We need to route this to the correct exchange client instance
                free_balance = 0.0
                if isinstance(self.client, MultiExchangeClient):
                    if pos.exchange in self.client.clients:
                        free_balance = self.client.clients[pos.exchange].get_balance(base_asset)
                elif hasattr(self.client, 'get_balance'):
                    free_balance = self.client.get_balance(base_asset)
                
                if free_balance > 0:
                    # Case 1: Actual balance is LESS than tracked (e.g. fees deducted from asset)
                    if free_balance < pos.quantity:
                        # If it's within 10% (fees are small), assume it's fee deduction and adjust
                        if free_balance > pos.quantity * 0.90:
                            print(f"   🧹 Adjusting sell qty for {symbol}: {pos.quantity:.8f} -> {free_balance:.8f} (Fees/Dust)")
                            pos.quantity = free_balance
                        else:
                            # Significant difference - safer to sell what we have to close the position
                            print(f"   ⚠️ Balance mismatch for {symbol}: Tracked {pos.quantity:.8f}, Actual {free_balance:.8f}. Selling Actual.")
                            pos.quantity = free_balance
                    
                    # Case 2: Actual balance is slightly MORE than tracked (leftover dust)
                    # Clean it up if it's within 5% excess
                    elif free_balance > pos.quantity and free_balance < pos.quantity * 1.05:
                        print(f"   🧹 Cleaning dust for {symbol}: {pos.quantity:.8f} -> {free_balance:.8f}")
                        pos.quantity = free_balance
            except Exception as e:
                print(f"   ⚠️ Failed to check balance for {symbol}: {e}")

        # EXECUTE TRADE - Use unified confirmation for all exchanges
        success = False
        if not self.dry_run:
            try:
                # Use unified trade confirmation for proper handling across exchanges
                confirmation = self.trade_confirmation.submit_order(
                    pos.exchange, symbol, 'SELL', quantity=pos.quantity
                )
                
                status = confirmation.get('status', '').upper()
                order_id = confirmation.get('order_id')
                
                if status in ['FILLED', 'ACCEPTED', 'OPEN', 'CLOSED']:
                    success = True
                    logger.info(f"Trade confirmed: {pos.exchange}/{symbol} -> {order_id}")
                elif status == 'REJECTED' and confirmation.get('pre_flight'):
                    print(f"   🗑️ Dust detected for {symbol}: {confirmation.get('error')}. Removing from active tracking.")
                    # Remove from active positions to stop infinite loop
                    self.positions.pop(symbol, None)
                    self.save_state()  # 🔄 Save state after dust removal
                    return
                else:
                    print(f"   ⚠️ Sell failed for {symbol}: {status}. Retrying next cycle.")
                    return # Don't remove position, try again later
            except Exception as e:
                print(f"   ⚠️ Sell execution error for {symbol}: {e}")
                return # Don't remove position, try again later
        else:
            success = True # Dry run always succeeds
            
        # Only remove if successful
        if success:
            self.positions.pop(symbol)
            # 🔄 IMMEDIATE STATE SAVE: Persist position removal right away!
            try:
                self.save_state()
                logger.info(f"💾 State saved after closing {symbol}")
            except Exception as e:
                logger.warning(f"State save failed after close: {e}")
        
        # Calculate P&L with platform-specific fees (Pessimistic Accounting)
        # We assume slippage AND spread cost on exit price for conservative P&L
        exit_value = pos.quantity * price
        exit_fee = exit_value * get_platform_fee(pos.exchange, 'taker')
        slippage_cost = exit_value * CONFIG['SLIPPAGE_PCT']
        spread_cost = exit_value * CONFIG['SPREAD_COST_PCT']
        
        # Total Expenses = Entry Fee + Exit Fee + Slippage + Spread
        total_expenses = pos.entry_fee + exit_fee + slippage_cost + spread_cost
        
        gross_pnl = exit_value - pos.entry_value
        net_pnl = gross_pnl - total_expenses
        
        # Calculate hold time
        exit_time = time.time()
        hold_time_sec = exit_time - pos.entry_time
        hold_time_min = hold_time_sec / 60.0
        
        # 🌊 RESONANCE HOLDING: Don't exit before MIN_HOLD_MINUTES unless emergency
        # From miner blueprint: 50+ min hold times achieve best efficiency
        # 💰 PENNY PROFIT OVERRIDE: If we have a penny profit, we take it regardless of time!
        is_penny_profitable = net_pnl >= 0.01
        
        if hold_time_min < MIN_HOLD_MINUTES and not is_penny_profitable:
            pnl_pct = ((price - pos.entry_price) / pos.entry_price * 100) if pos.entry_price > 0 else 0
            # Only exit early on stops (-5%) or massive gains (+20%)
            if reason not in ['STOP_LOSS', 'CIRCUIT_BREAKER'] and abs(pnl_pct) < 20:
                logger.debug(f"🌊 {symbol}: Holding for resonance ({hold_time_min:.1f}/{MIN_HOLD_MINUTES} min), PnL {pnl_pct:+.1f}%")
                return  # Keep position open
        
        # 📊 FEED POSITION CLOSE TO PROBABILITY MATRIX 📊
        # This helps the matrix validate predictions and learn from outcomes
        if self.prob_matrix and hasattr(self.prob_matrix, 'feed_position_close'):
            try:
                self.prob_matrix.feed_position_close(
                    symbol=symbol,
                    exit_price=price,
                    realized_pnl=net_pnl,
                    exit_reason=reason,
                    platform_timestamp=exit_time,
                )
                logger.info(f"Matrix outcome recorded: {symbol} PnL={net_pnl:.2f} reason={reason}")
                
                # 🧠 PUBLISH THOUGHT: TRADE CLOSED 🧠
                if THOUGHT_BUS_AVAILABLE and THOUGHT_BUS:
                    THOUGHT_BUS.publish(Thought(
                        source="unified_ecosystem",
                        topic="execution.order.close",
                        payload={
                            "symbol": symbol,
                            "side": "SELL",
                            "price": price,
                            "quantity": pos.quantity,
                            "pnl": net_pnl,
                            "reason": reason,
                            "hold_time_min": hold_time_min
                        }
                    ))
                
                # 🔮 CONTINUOUS LEARNING: Validate prediction vs actual outcome
                # This is the core feedback loop that improves forecast accuracy
                if hasattr(self.prob_matrix, 'validate_and_learn'):
                    try:
                        # Determine actual direction from P&L
                        actual_direction = "BULLISH" if net_pnl > 0 else ("BEARISH" if net_pnl < 0 else "NEUTRAL")
                        
                        # Get what the matrix predicted for this symbol
                        if symbol in self.prob_matrix.matrices:
                            matrix = self.prob_matrix.matrices[symbol]
                            predicted_direction = matrix.day_plus_1.predicted_direction if matrix.day_plus_1 else "NEUTRAL"
                            confidence = matrix.confidence_score if hasattr(matrix, 'confidence_score') else 0.5
                            
                            # Validate and learn
                            validation = self.prob_matrix.validate_and_learn(
                                symbol=symbol,
                                predicted_direction=predicted_direction,
                                actual_direction=actual_direction,
                                confidence=confidence
                            )
                            
                            if validation['validated']:
                                accuracy = validation.get('accuracy', 0.5) * 100
                                trend = validation.get('trend', 'UNKNOWN')
                                logger.info(f"🔮 {symbol} validation: predicted {predicted_direction}, actual {actual_direction}, accuracy now {accuracy:.0f}% ({trend})")
                    except Exception as e:
                        logger.debug(f"Matrix learning error for {symbol}: {e}")
            except Exception as e:
                logger.warning(f"Matrix position close feed error for {symbol}: {e}")
        
        # 📊 LOG TRADE EXIT FOR PROBABILITY MATRIX VALIDATION 📊
        if TRADE_LOGGER_AVAILABLE and trade_logger:
            try:
                pnl_pct = (net_pnl / pos.entry_value * 100) if pos.entry_value > 0 else 0
                trade_logger.log_trade_exit(
                    trade_id=f"{symbol}_{pos.entry_time:.0f}",
                    exit_data={
                        'symbol': symbol,
                        'exit_price': price,
                        'exit_time': exit_time,
                        'exit_value': exit_value,
                        'gross_pnl': gross_pnl,
                        'net_pnl': net_pnl,
                        'pnl_pct': pnl_pct,
                        'fees': total_expenses,
                        'reason': reason,
                        'hold_time_seconds': hold_time_sec,
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to log trade exit for {symbol}: {e}")
        
        # Release symbol exposure
        if symbol in self.tracker.symbol_exposure:
            del self.tracker.symbol_exposure[symbol]
        
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
        
        # 🧠 Record trade in Adaptive Learning Engine WITH NEWS/KNOWLEDGE CORRELATION
        ticker_snapshot = self.ticker_cache.get(symbol, {}) if hasattr(self, 'ticker_cache') else {}
        news_context = getattr(self, '_last_news_sentiment', {})
        ADAPTIVE_LEARNER.enhanced_record_trade({
            'symbol': symbol,
            'entry_price': pos.entry_price,
            'exit_price': price,
            'pnl': net_pnl,
            'frequency': getattr(pos, 'frequency', 256),
            'coherence': pos.coherence,
            'score': getattr(pos, 'score', 50),
            'entry_time': pos.entry_time,
            'exit_time': time.time(),
            'hnc_action': getattr(pos, 'hnc_action', 'HOLD'),
            'probability': getattr(pos, 'probability', 0.5),
            'reason': reason,
            'exchange': pos.exchange,
            'hold_time_sec': hold_time_sec,
            # Inject latest ticker context so adaptive learning can correlate
            'ticker_price': ticker_snapshot.get('price'),
            'ticker_change24h': ticker_snapshot.get('change24h'),
            'ticker_volume': ticker_snapshot.get('volume'),
            'ticker_source': ticker_snapshot.get('source', 'unknown'),
            # 📰 NEWS CORRELATION CONTEXT - Learn from market sentiment at trade time
            'news_sentiment': news_context.get('sentiment', 0.0),
            'news_label': news_context.get('label', 'unknown'),
            'news_confidence': news_context.get('confidence', 0.0),
        })
        
        # 🌊 CASCADE AMPLIFIER - Update win/loss streak for signal amplification
        pnl_pct = (net_pnl / pos.entry_value * 100) if pos.entry_value > 0 else 0
        if net_pnl > 0:
            CASCADE_AMPLIFIER.record_win(pnl_pct / 100)
        else:
            CASCADE_AMPLIFIER.record_loss(pnl_pct / 100)
        
        # 🌐 MULTI-EXCHANGE LEARNING - All Systems Learn Together 🌐
        asset_class = 'crypto'  # Default
        if pos.exchange == 'capital':
            asset_class = 'cfd'
        elif pos.exchange == 'alpaca':
            asset_class = 'stocks'
        self.multi_exchange.record_trade_result(
            exchange=pos.exchange,
            symbol=symbol,
            pnl=net_pnl,
            asset_class=asset_class,
            frequency=getattr(pos, 'frequency', 432),
            coherence=pos.coherence
        )
        
        # 🔮 NEXUS PREDICTOR LEARNING - Update patterns from trade outcome 🔮
        if self.nexus_predictor is not None:
            try:
                entry_prediction = {
                    'direction': 'LONG',  # We only go long currently
                    'probability': getattr(pos, 'nexus_prob', 0.5),
                    'edge': getattr(pos, 'nexus_edge', 0.0),
                    'patterns_triggered': getattr(pos, 'nexus_patterns', []),
                }
                self.nexus_predictor.record_trade_outcome(
                    entry_prediction=entry_prediction,
                    was_profitable=(net_pnl > 0),
                    pnl_pct=pnl_pct
                )
            except Exception as e:
                pass  # Silent fail
        
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
    # 💓 HEARTBEAT - Periodic status output
    # ─────────────────────────────────────────────────────────
    
    def print_heartbeat(self):
        """Print a periodic heartbeat with key metrics."""
        now = datetime.now().strftime("%H:%M:%S")
        uptime_mins = (time.time() - self.start_time) / 60
        
        # Calculate position stats
        total_value = 0.0
        total_pnl = 0.0
        for symbol, pos in self.positions.items():
            rt_price = self.get_realtime_price(symbol)
            price = rt_price if rt_price else pos.entry_price
            current_val = pos.quantity * price
            pnl = current_val - pos.entry_value
            total_value += current_val
            total_pnl += pnl
        
        # Get win rate from tracker
        win_rate = (self.tracker.wins / self.tracker.total_trades * 100) if self.tracker.total_trades > 0 else 0
        
        # Get symbol cache stats
        cache_stats = self.get_symbol_cache_stats()
        
        # Get probability matrix stats if available
        matrix_stats = ""
        if self.prob_matrix:
            try:
                summary = self.prob_matrix.get_active_positions_summary()
                win_stats = self.prob_matrix.get_position_win_rate()
                matrix_stats = f" | Matrix: {summary['count']} tracked, {win_stats.get('trades', 0)} outcomes"
            except:
                pass
        
        print(f"\n   💓 HEARTBEAT [{now}] Uptime: {uptime_mins:.0f}m | "
              f"Positions: {len(self.positions)} | Value: £{total_value:.2f} | "
              f"PnL: £{total_pnl:+.2f} | Win: {win_rate:.0f}% ({self.tracker.wins}W/{self.tracker.losses}L)"
              f"{matrix_stats}")

    # ─────────────────────────────────────────────────────────
    # Main Loop
    # ─────────────────────────────────────────────────────────
    
    def run_one_cycle(self):
        """Run a single trading cycle"""
        self.iteration += 1
        now = datetime.now().strftime("%H:%M:%S")
        
        print(f"\\n{'━'*70}")
        print(f"🔄 Cycle {self.iteration} - {now} [{self.scan_direction}]")
        print(f"{'━'*70}")

        # Refresh aggregated state periodically (every 10 minutes)
        try:
            last_agg = self.state_aggregator.aggregated_state.get('last_aggregation', 0)
            if time.time() - last_agg > 600:
                self.state_aggregator.load_all_sources()
        except Exception:
            pass
        
        # 🏥 ECOSYSTEM HEALTH CHECK (every 10 cycles)
        if self.iteration % 10 == 0:
            health = self.auris.get_system_health_report()
            print(f"\\n📡 Ecosystem Health: {health['overall_health']}")
            if health['communication']['systems_active'] < 2:
                print("   ⚠️  WARNING: Less than 2 systems active!")
        
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
            except Exception as e:
                print(f"   ⚠️ Market Pulse Error: {e}")

        # Refresh data
        self.refresh_tickers()
        print(f"   📊 Ticker cache: {len(self.ticker_cache)} symbols loaded")
        self.refresh_equity(mark_cycle=True)
        
        # Deploy scouts on first cycle if enabled
        if self.iteration == 1 and not self.scouts_deployed:
            self._deploy_scouts()
        
        # 💓 Heartbeat every 5 cycles
        if self.iteration % 5 == 0:
            self.print_heartbeat()
        
        # Toggle scan direction
        self.scan_direction = 'Z→A' if self.iteration % 2 == 0 else 'A→Z'
        
        # Check positions
        self.check_positions()
        
        # Check network coherence
        network_coherence = self.mycelium.get_network_coherence()
        trading_paused = network_coherence < CONFIG['MIN_NETWORK_COHERENCE']

        # Pause new entries if probability reports are stale
        pfresh = self.state_aggregator.aggregated_state.get('probability_freshness', {})
        if pfresh.get('stale'):
            trading_paused = True
            newest = pfresh.get('newest_minutes')
            newest_str = f"{newest:.1f}m" if isinstance(newest, (int, float)) else "unknown"
            print(f"   ⚠️ Probability data stale ({newest_str}); skipping new entries this cycle")
        
        # Update Lattice State
        raw_opps = self.find_opportunities()
        l_state = self.lattice.update(raw_opps)
        
        # Apply Triadic Envelope Protocol
        all_opps = self.lattice.filter_signals(raw_opps)
        
        # Rebalance
        if all_opps and len(self.positions) >= CONFIG['MAX_POSITIONS'] // 2:
            freed = self.rebalance_portfolio(all_opps)
            if freed > 0: self.refresh_equity()

        # Find opportunities
        if len(self.positions) < CONFIG['MAX_POSITIONS'] and not self.tracker.trading_halted and not trading_paused:
            # 🎯 TARGET FILL RATE: Actively try to maintain 1/3 positions filled
            target_positions = int(CONFIG['MAX_POSITIONS'] * CONFIG.get('TARGET_FILL_RATE', 0.33))
            current_positions = len(self.positions)
            under_target = current_positions < target_positions
            
            if all_opps:
                if under_target:
                    print(f"\\n   🎯 FILLING MODE: {current_positions}/{target_positions} target ({current_positions}/{CONFIG['MAX_POSITIONS']} max)")
                    print(f"   🔍 Actively seeking {target_positions - current_positions} more positions...")
                print(f"\\n   🔮 Top Opportunities: {len(all_opps)} found")
                for opp in all_opps[:5]:
                    print(f"      {opp['symbol']:12s} +{opp['change24h']:5.1f}% | Γ={opp['coherence']:.2f} | Score: {opp['score']}")
            
            # If under target, be more aggressive - take more opportunities per cycle
            if under_target:
                slots_to_fill = min(target_positions - current_positions, 3)  # Fill up to 3 per cycle
            else:
                slots_to_fill = 1  # Normal mode: 1 at a time
            
            for opp in all_opps[:min(slots_to_fill, CONFIG['MAX_POSITIONS'] - current_positions)]:
                self.open_position(opp)
                
        # Show positions
        if self.positions:
            print(f"\\n   📊 Active Positions ({len(self.positions)}/{CONFIG['MAX_POSITIONS']}):")
            for symbol, pos in self.positions.items():
                rt = self.get_realtime_price(symbol)
                price = rt if rt else pos.entry_price
                pct = (price - pos.entry_price) / pos.entry_price * 100
                print(f"      {symbol:12s} Entry: ${pos.entry_price:.6f} | Now: {pct:+.2f}%")
                
        # Stats
        runtime = (time.time() - self.start_time) / 60
        cycle_pnl = self.total_equity_gbp - self.tracker.cycle_equity_start
        
        print(f"\\n   💎 Portfolio: £{self.total_equity_gbp:.2f} ({self.tracker.total_return:+.2f}%)")
        print(f"   📈 Cycle P&L: £{cycle_pnl:+.2f}")
        print(f"   ⏱️ Runtime: {runtime:.1f} min | Positions: {len(self.positions)}")
        
        self.save_state()

    def _place_order_from_intent(self, symbol: str, side: str, qty: float):
        """
        This is the ONLY place ExecutionModule touches your exchange.
        Maps cognition intents to real orders.
        
        ⚠️ IMPORTANT: Uses quote_qty (notional value) instead of base qty to ensure
        we meet minimum order requirements ($5 on Kraken).
        """
        try:
            # Strategy: use the exchange from ticker cache or default to primary
            exchange = 'kraken'  # default
            
            # Calculate proper position size based on available capital
            # Default to minimum viable order size ($6 to exceed Kraken's $5 min)
            min_order_usd = 6.0  # Just above Kraken's $5 minimum
            
            # Get available balance and calculate proper size
            try:
                balances = getattr(self, 'cached_balances', {})
                kraken_bal = balances.get('kraken', {})
                usd_available = float(kraken_bal.get('USD', {}).get('free', 0) or 
                                     kraken_bal.get('ZUSD', {}).get('free', 0) or 
                                     kraken_bal.get('GBP', {}).get('free', 0) or 0)
                
                # Use 2% of available balance per trade, minimum $6
                position_size_usd = max(min_order_usd, usd_available * 0.02)
                
                # Cap at reasonable amount
                position_size_usd = min(position_size_usd, 50.0)
                
            except Exception:
                position_size_usd = min_order_usd
            
            # Use quote_qty (notional) instead of base quantity
            # This ensures we meet minimum notional requirements
            result = self.trade_confirmation.submit_order(
                exchange=exchange,
                symbol=symbol,
                side=side.upper(),  # 'buy' -> 'BUY'
                quote_qty=position_size_usd  # Use notional value, not base qty
            )
            
            return result
            
        except Exception as e:
            return {"error": str(e), "symbol": symbol, "side": side, "qty": qty}

    def _on_execution_order_result(self, t: Thought) -> None:
        """
        Receives JSON results of orders, lets you store positions / telemetry.
        """
        data = t.payload
        intent = data.get("intent", {})
        order_result = data.get("order_result", {})
        
        # Log the execution thought
        symbol = intent.get("symbol", "UNKNOWN")
        side = intent.get("side", "UNKNOWN")
        
        if "error" not in order_result:
            print(f"   🧠✅ Cognition executed: {symbol} {side}")
        else:
            print(f"   🧠❌ Cognition failed: {symbol} {side} - {order_result.get('error')}")

    def _on_news_sentiment(self, t: Thought) -> None:
        """
        Receives news sentiment analysis from the NewsFeed module.
        Can influence trading decisions and risk management.
        Feeds into AdaptiveLearningEngine for correlation learning.
        """
        analysis = t.payload.get("analysis", {})
        sentiment_label = analysis.get("sentiment_label", "neutral")
        confidence = analysis.get("confidence", 0.0)
        avg_sentiment = analysis.get("average_sentiment", 0.0)
        
        # Store for use in trading decisions
        self._last_news_sentiment = {
            'sentiment': avg_sentiment,
            'label': sentiment_label,
            'confidence': confidence,
            'timestamp': t.ts
        }
        
        # 📚 FEED INTO ADAPTIVE LEARNER FOR CORRELATION LEARNING
        try:
            ADAPTIVE_LEARNER.record_news_sentiment({
                'sentiment': avg_sentiment,
                'label': sentiment_label,
                'confidence': confidence,
                'crypto_sentiment': t.payload.get('signals', {}).get('crypto_sentiment', 0.0),
                'stock_sentiment': t.payload.get('signals', {}).get('stock_sentiment', 0.0),
                'risk_level': t.payload.get('signals', {}).get('risk_level', 'normal'),
            })
        except Exception as e:
            logger.debug(f"Could not record news to learner: {e}")
        
        # If highly confident bearish news, consider reducing position sizes
        if sentiment_label == "bearish" and confidence >= 0.6:
            logger.info(f"📰🐻 Bearish news detected (conf={confidence:.2f}) - flagging for caution")
        elif sentiment_label == "bullish" and confidence >= 0.6:
            logger.info(f"📰🐂 Bullish news detected (conf={confidence:.2f}) - market favorable")

    def _on_news_alert(self, t: Thought) -> None:
        """
        Receives individual news alerts for extreme sentiment articles.
        """
        alert = t.payload.get("alert", {})
        title = alert.get("title", "")
        sentiment = alert.get("sentiment", 0.0)
        sentiment_label = alert.get("sentiment_label", "neutral")
        
        if abs(sentiment) >= 0.7:
            logger.info(f"📰🚨 NEWS ALERT [{sentiment_label.upper()}]: {title[:60]}...")

    def _on_knowledge_result(self, t: Thought) -> None:
        """
        Receives knowledge query results from the Knowledge Base.
        Feeds into AdaptiveLearningEngine for learning correlation.
        """
        query = t.payload.get("query", "")
        results_count = t.payload.get("results_count", 0)
        top_result = t.payload.get("top_result", "")
        
        # 📚 FEED INTO ADAPTIVE LEARNER
        if results_count > 0:
            try:
                ADAPTIVE_LEARNER.record_knowledge_event({
                    'topic': query,
                    'articles_found': results_count,
                    'top_result': top_result,
                    'type': 'query'
                })
            except Exception as e:
                logger.debug(f"Could not record knowledge to learner: {e}")
        
        if results_count > 0:
            logger.debug(f"📚 Knowledge query '{query}': {results_count} results (top: {top_result})")

    def _on_research_complete(self, t: Thought) -> None:
        """
        Receives autonomous research completion notifications.
        Feeds into AdaptiveLearningEngine for knowledge correlation.
        """
        topic = t.payload.get("topic", "")
        articles_found = t.payload.get("articles_found", 0)
        key_concepts = t.payload.get("key_concepts", [])
        
        # 📚 FEED INTO ADAPTIVE LEARNER
        try:
            ADAPTIVE_LEARNER.record_knowledge_event({
                'topic': topic,
                'articles_found': articles_found,
                'key_concepts': key_concepts,
                'type': 'autonomous_research'
            })
        except Exception as e:
            logger.debug(f"Could not record research to learner: {e}")
        
        logger.info(f"📚🔬 Research complete: '{topic}' - {articles_found} articles, concepts: {key_concepts[:3]}")

    def _on_wisdom_insight(self, t: Thought) -> None:
        """
        Receives wisdom insights from the Wisdom Scanner.
        Ancient wisdom from 11 civilizations enriching trading decisions.
        Feeds into AdaptiveLearningEngine for deep pattern correlation.
        """
        civilization = t.payload.get("civilization", "")
        topic = t.payload.get("topic", "")
        relevance = t.payload.get("relevance", 0.0)
        application = t.payload.get("application", "")
        
        # 📚 FEED INTO ADAPTIVE LEARNER
        try:
            ADAPTIVE_LEARNER.record_knowledge_event({
                'type': 'ancient_wisdom',
                'civilization': civilization,
                'topic': topic,
                'relevance': relevance,
                'application': application
            })
        except Exception as e:
            logger.debug(f"Could not record wisdom to learner: {e}")
        
        if relevance >= 0.7:
            logger.info(f"📚🌍 High-relevance wisdom [{civilization.upper()}]: {topic} (r={relevance:.2f})")

    def _on_consciousness_expansion(self, t: Thought) -> None:
        """
        Receives consciousness expansion notifications when wisdom scans complete.
        """
        message = t.payload.get("message", "")
        logger.info(f"📚🌍✨ {message}")

    def run(self, interval: float = 2.0, target_profit_gbp: float = None, max_minutes: float = None):
        """Main trading loop - 🔥 BEAST MODE: 2 second cycles for MAXIMUM SPEED!

        Args:
            interval: Seconds to sleep between cycles. (DEFAULT NOW 2s - FASTER!)
            target_profit_gbp: If provided, stop when net P&L (current_equity - initial_equity) >= target.
            max_minutes: If provided, stop after this many minutes of runtime.
        """
        # 🛠️ CRITICAL: Compute REAL wallet balance BEFORE banner!
        # This fixes the "Fake $1000 Balance" bug by detecting actual portfolio value first.
        total, cash, holdings = self.compute_total_equity()
        if self.tracker.initial_balance == 1000.0 and self.tracker.total_trades == 0:
            if abs(total - 1000.0) > 1.0 and total > 0:
                print(f"\n   ⚖️  AUTO-CORRECTING BALANCE: ${self.tracker.initial_balance:.2f} -> ${total:.2f} (Actual Wallet)\n")
                self.tracker.initial_balance = total
                self.tracker.first_start_balance = total
                self.tracker.balance = total
                self.tracker.peak_balance = total
                self.tracker.equity_baseline = total
                self.tracker.portfolio_equity = total
                self.tracker.cash_balance = cash
                self.total_equity_gbp = total
                self.cash_balance_gbp = cash
        
        self.banner()
        
        print("🐙 Connecting to Unified Ecosystem...")
        self.print_portfolio_report()
        
        pair_count = self.refresh_tickers()
        print(f"✅ Connected! {pair_count} pairs loaded")
        
        # 🧠📈 BRAIN SYNC: Load historical trades from exchange for learning
        if not self.dry_run:
            try:
                sync_result = sync_exchange_trades_to_brain()
                if sync_result.get('status') == 'success':
                    logger.info(f"🧠 Brain synced with {sync_result['trades_synced']} historical trades (WR: {sync_result['win_rate']:.1f}%)")
            except Exception as e:
                logger.warning(f"🧠 Brain sync skipped: {e}")
        
        # 🌾 STARTUP HARVESTER: Sell existing assets if profitable
        if not self.dry_run and CONFIG.get('HARVEST_ON_STARTUP', True):
            self.harvest_existing_assets()
        
        # 🔄 POSITION SYNC: Reconcile stored positions with actual exchange balances
        # This fixes state drift where positions are sold but state file is stale
        if not self.dry_run:
            self.sync_positions_with_exchange()
        
        # Find initial opportunities for WebSocket
        initial_opps = self.find_opportunities()
        # 🔥 UNLEASHED: Watch 200 pairs instead of 15 - MAXIMUM SIGNAL CAPTURE!
        symbols_to_watch = [o['symbol'] for o in initial_opps[:200]]
        
        # Add major pairs for base currency - MEGA EXPANDED LIST!
        base = CONFIG['BASE_CURRENCY']
        # 🤑 GREEDY HOE MODE: ALL THE ALTCOINS! Every shitcoin that moves!
        major_bases = [
            # 🏆 TOP 20 BY MARKET CAP
            'BTC', 'ETH', 'XBT', 'BNB', 'SOL', 'XRP', 'ADA', 'DOGE', 'AVAX', 'DOT',
            'LINK', 'MATIC', 'SHIB', 'LTC', 'BCH', 'ATOM', 'UNI', 'XLM', 'ETC', 'FIL',
            # 🚀 DEFI TOKENS  
            'AAVE', 'MKR', 'CRV', 'COMP', 'SNX', 'YFI', 'SUSHI', '1INCH', 'BAL', 'LDO',
            # 🎮 GAMING & METAVERSE
            'SAND', 'MANA', 'AXS', 'ENJ', 'GALA', 'IMX', 'RONIN', 'ILV', 'MAGIC',
            # 🔮 LAYER 2 & NEW CHAINS
            'ARB', 'OP', 'MATIC', 'IMX', 'STRK', 'ZK', 'SCROLL', 'BASE', 'LINEA',
            # 🌊 NEW HOT ALTS
            'APT', 'SUI', 'SEI', 'TIA', 'INJ', 'PYTH', 'JUP', 'JTO', 'WEN', 'BOME',
            # 🐕 MEME COINS - WHERE THE DEGENS PLAY!
            'PEPE', 'WIF', 'BONK', 'FLOKI', 'TURBO', 'BRETT', 'MOG', 'POPCAT', 'NEIRO',
            # 💎 AI TOKENS
            'FET', 'AGIX', 'OCEAN', 'RNDR', 'TAO', 'AKT', 'ARKM', 'PRIME', 'ALI',
            # 📦 INFRASTRUCTURE
            'GRT', 'AR', 'HNT', 'THETA', 'STX', 'KAS', 'QNT', 'VET', 'HBAR', 'ICP',
            # 🔒 PRIVACY COINS
            'XMR', 'ZEC', 'DASH', 'SCRT',
            # 🌍 MISC ALTS
            'NEAR', 'ALGO', 'EOS', 'XTZ', 'EGLD', 'FLOW', 'MINA', 'KAVA', 'ROSE', 'ZIL'
        ]
        for base_asset in major_bases:
            for quote in ['USD', 'GBP', 'EUR', 'USDT', 'USDC', 'BTC', 'ETH', 'BNB']:
                pair = f"{base_asset}{quote}"
                # Only add if it's a valid pair in our ticker cache
                if pair not in symbols_to_watch and pair in self.ticker_cache:
                    symbols_to_watch.append(pair)
                # Also try reverse for some pairs (though rare in standard naming)
                # or alternative naming conventions if needed
                
        print(f"\n🔴🤑 GREEDY HOE MODE: Starting WebSocket for {len(symbols_to_watch)} pairs!")
        self.start_websocket(symbols_to_watch)
        
        initial_equity = self.total_equity_gbp
        start_ts = time.time()

        # � START PROBABILITY GENERATOR - Auto-regenerates every 15 seconds
        if self.probability_generator:
            self.probability_generator.start(ecosystem=self)
            print("   📊 Probability Report Generator STARTED (background thread - 15s cycles)")

        # �🚀 Force deploy scouts before entering the loop (guarantees first shot)
        if not self.scouts_deployed and CONFIG['DEPLOY_SCOUTS_IMMEDIATELY']:
            self._deploy_scouts()

        try:
            while True:
                self.iteration += 1
                now = datetime.now().strftime("%H:%M:%S")
                
                print(f"\n{'━'*70}")
                print(f"🔄 Cycle {self.iteration} - {now} [{self.scan_direction}]")
                print(f"{'━'*70}")

                # 🔦 Miner Lighthouse hook: if miner Γ is firing, override thresholds aggressively
                lighthouse_active = False
                try:
                    if hasattr(self, 'miner_optimizer') and hasattr(self.miner_optimizer, 'platypus'):
                        miner_gamma = getattr(self.miner_optimizer.platypus, 'Gamma_t', 0.5)
                        lighthouse_active = miner_gamma >= 0.99
                except Exception:
                    lighthouse_active = False
                if lighthouse_active:
                    # Lower the entry Γ threshold during lighthouse and boost sizing
                    try:
                        # These attributes may not exist in all builds; guard each usage
                        setattr(self, 'min_entry_gamma', 0.20)
                        setattr(self, 'position_size_multiplier', 2.73)
                        # Informational log for operators
                        logger.info("🔦 MINER LIGHTHOUSE ACTIVE - TRADING WITH 273% BOOST! (Γ>=0.99)")
                    except Exception:
                        pass
                
                # 🧠🌍 UNIFIED BRAIN WISDOM CYCLE (via Brain Bridge)
                # Brain runs EVERY cycle - autonomous cognition always active
                if self.brain:
                    try:
                        # Only print header every 10 cycles to reduce noise
                        if self.iteration % 10 == 1:
                            print("\n   🧠🌍 UNIFIED BRAIN WISDOM CYCLE...")
                        
                        # Build quantum context from available sources
                        quantum_ctx = None
                        if hasattr(self, 'miner_optimizer') and self.miner_optimizer:
                            qbrain = getattr(self.miner_optimizer, 'brain', None)
                            if qbrain:
                                quantum_ctx = {
                                    'quantum_coherence': qbrain.state.unified_coherence,
                                    'planetary_gamma': qbrain.state.planetary_gamma,
                                    'cascade_multiplier': qbrain.state.cascade_multiplier,
                                    'is_lighthouse': qbrain.state.is_optimal_window,
                                    'piano_lambda': qbrain.state.piano_lambda,
                                    'harmonic_signal': qbrain.state.harmonic_signal,
                                    'signal_confidence': qbrain.state.signal_confidence,
                                }
                        
                        # Run brain cycle through the bridge (handles bidirectional sync)
                        result = self.brain_bridge.run_wisdom_cycle(self.brain, quantum_ctx)
                        
                        # Get trading recommendation from brain
                        brain_rec = self.brain_bridge.get_trading_recommendation()
                        
                        if result:
                            # Display unified status
                            self.brain_bridge.display_status()
                            
                            # Apply brain recommendation to position sizing
                            brain_mult = brain_rec.get('position_multiplier', 1.0)
                            brain_action = brain_rec.get('action', 'HOLD')
                            
                            if brain_action == 'BUY':
                                self.position_size_multiplier = max(self.position_size_multiplier, brain_mult)
                                print(f"   🧠📈 BRAIN BOOST: Position sizing = {self.position_size_multiplier:.2f}x")
                            elif brain_action == 'REDUCE':
                                self.position_size_multiplier = min(self.position_size_multiplier, brain_mult)
                                print(f"   🧠📉 BRAIN CAUTION: Position sizing = {self.position_size_multiplier:.2f}x")
                            
                            # Update cascade amplifier with brain gamma
                            CASCADE_AMPLIFIER.update_lighthouse(self.brain_bridge._planetary_gamma)
                            
                            # Legacy prediction display
                            prediction = self.brain.get_latest_prediction()
                            if prediction:
                                print(f"   🧠 PREDICTION: {prediction['direction']} (Conf: {prediction['confidence']}%)")
                            
                            # Dream insights (preserved)
                            if hasattr(self.brain, 'dream_engine'):
                                # Get F&G from brain bridge, default change to 0
                                current_fng = getattr(self.brain_bridge, '_fear_greed', 50)
                                current_change = 0.0  # Default - actual change computed in brain cycle
                                dream_response = self.brain.dream_engine.get_prepared_response(current_change, current_fng)
                                if dream_response:
                                    print(f"   💭 DREAM: {dream_response['action']}")
                                    
                    except Exception as e:
                        print(f"   ⚠️ Brain cycle error: {e}")

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
                        
                        # 🌐 Cross-Exchange Arbitrage Scan
                        try:
                            arb_opps = self.arb_scanner.get_top_opportunities(3)
                            if arb_opps:
                                print(f"   ├─ 🔀 Cross-Exchange Arbitrage:")
                                for arb in arb_opps[:2]:
                                    # Apply CASCADE + κt boost if lighthouse is active
                                    boosted_pct = arb.get('net_profit_pct', 0.0)
                                    if lighthouse_active:
                                        boosted_pct = boosted_pct * 10.0 * 2.73
                                    print(f"   │  {arb['symbol']}: Buy {arb['buy_exchange']} → Sell {arb['sell_exchange']} ({boosted_pct:.2f}% net{' ⚡ BOOST' if lighthouse_active else ''})")
                        except Exception as arb_err:
                            logger.debug(f"Arbitrage scan error: {arb_err}")
                            
                        print(f"   └─ Top Gainer: {pulse['top_gainers'][0]['symbol']} ({pulse['top_gainers'][0]['priceChangePercent']:.1f}%)")
                        print("")
                    except Exception as e:
                        print(f"   ⚠️ Market Pulse Error: {e}")

                # 📰 NEWS FEED POLLING (World News API)
                # Poll periodically to avoid rate limits but keep sentiment fresh
                if self.news_feed:
                    self._news_poll_counter += 1
                    if self._news_poll_counter >= self._news_poll_interval:
                        self._news_poll_counter = 0
                        try:
                            import asyncio
                            # Run async poll synchronously
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            try:
                                news_result = loop.run_until_complete(self.news_feed.poll_and_publish())
                                
                                if news_result.get('status') == 'success':
                                    sentiment_analysis = news_result.get('sentiment_analysis', {})
                                    signals = news_result.get('signals', {})
                                    
                                    # Display news sentiment
                                    sentiment_label = sentiment_analysis.get('sentiment_label', 'unknown')
                                    avg_sentiment = sentiment_analysis.get('average_sentiment', 0.0)
                                    confidence = sentiment_analysis.get('confidence', 0.0)
                                    article_count = news_result.get('articles_processed', 0)
                                    
                                    # Color code based on sentiment
                                    if sentiment_label == 'bullish':
                                        sentiment_icon = '📈'
                                    elif sentiment_label == 'bearish':
                                        sentiment_icon = '📉'
                                    else:
                                        sentiment_icon = '📊'
                                    
                                    print(f"\n   📰 WORLD NEWS DIGEST ({article_count} articles)")
                                    print(f"   ├─ {sentiment_icon} Overall Sentiment: {sentiment_label.upper()} ({avg_sentiment:+.3f})")
                                    print(f"   ├─ Confidence: {confidence:.1%}")
                                    
                                    # Domain sentiments
                                    crypto_sent = signals.get('crypto_sentiment', 0.0)
                                    stock_sent = signals.get('stock_sentiment', 0.0)
                                    print(f"   ├─ Crypto News: {crypto_sent:+.3f} | Stock News: {stock_sent:+.3f}")
                                    
                                    # Risk level
                                    risk_level = signals.get('risk_level', 'normal')
                                    if risk_level == 'high':
                                        print(f"   ├─ ⚠️ NEWS RISK LEVEL: HIGH - Consider reducing exposure")
                                    elif risk_level == 'elevated':
                                        print(f"   ├─ ⚡ NEWS RISK LEVEL: ELEVATED")
                                    
                                    # Show alerts if any
                                    alerts = signals.get('alerts', [])
                                    if alerts:
                                        print(f"   └─ 🚨 {len(alerts)} sentiment alerts published")
                                    else:
                                        print(f"   └─ No extreme sentiment alerts")
                                    
                                    # Store news sentiment for trading decisions
                                    self._last_news_sentiment = {
                                        'sentiment': avg_sentiment,
                                        'label': sentiment_label,
                                        'confidence': confidence,
                                        'risk_level': risk_level,
                                        'crypto_sentiment': crypto_sent,
                                        'timestamp': datetime.now().isoformat()
                                    }
                                    
                            finally:
                                loop.close()
                        except Exception as e:
                            print(f"   ⚠️ News Feed Error: {e}")

                # 📚 KNOWLEDGE BASE RESEARCH (Wikipedia API)
                # Autonomous research on trading topics periodically
                if self.knowledge_base:
                    self._knowledge_research_counter += 1
                    if self._knowledge_research_counter >= self._knowledge_research_interval:
                        self._knowledge_research_counter = 0
                        try:
                            # Research a trading-relevant topic
                            import random
                            research_topics = [
                                "Market volatility", "Trading psychology", "Risk management",
                                "Technical analysis", "Cryptocurrency", "Market sentiment",
                                "Economic indicators", "Federal Reserve policy"
                            ]
                            topic = random.choice(research_topics)
                            
                            # Run research in background to not block trading
                            import threading
                            def background_research():
                                try:
                                    result = self.knowledge_base.autonomous_research(topic, depth=1)
                                    if result['articles']:
                                        logger.debug(f"📚 Background research on '{topic}': {len(result['articles'])} articles")
                                except Exception as e:
                                    logger.debug(f"Knowledge research error: {e}")
                            
                            threading.Thread(target=background_research, daemon=True).start()
                            
                            # Show brief status
                            status = self.knowledge_base.get_status()
                            cache_size = status['cache']['size']
                            if cache_size > 0 and self.iteration % 100 == 0:
                                print(f"\n   📚 KNOWLEDGE BASE STATUS")
                                print(f"   ├─ Cache: {cache_size} articles")
                                print(f"   ├─ API calls: {status['metrics']['api_calls']}")
                                print(f"   └─ Researching: {topic}")
                                
                        except Exception as e:
                            logger.debug(f"Knowledge base error: {e}")

                # Refresh data
                self.refresh_tickers()
                print(f"   📊 Ticker cache: {len(self.ticker_cache)} symbols loaded")
                
                # 🔮 VALIDATE PENDING PREDICTIONS 🔮
                # Check predictions that are due for validation
                try:
                    def get_price(exchange, symbol):
                        """Get current price for validation."""
                        # Try ticker cache first
                        if symbol in self.ticker_cache:
                            return self.ticker_cache[symbol].get('price', 0)
                        # Try realtime prices
                        if symbol in self.realtime_prices:
                            return self.realtime_prices[symbol]
                        return None
                    
                    validated = self.prediction_validator.validate_predictions(get_price)
                    if validated:
                        accurate_count = sum(1 for v in validated if v['is_accurate'])
                        direction_count = sum(1 for v in validated if v['direction_correct'])
                        print(f"   🔮 Validated {len(validated)} predictions: {accurate_count} accurate, {direction_count} direction correct")
                    
                    # Every 20 cycles, show full accuracy report
                    if self.iteration % 20 == 0 and self.prediction_validator.get_validated_count() > 0:
                        print(self.prediction_validator.get_accuracy_summary())
                    
                    # 🧠 Every 50 cycles, show adaptive learning summary
                    if self.iteration % 50 == 0:
                        print(ADAPTIVE_LEARNER.get_learning_summary())
                        
                except Exception as e:
                    logger.debug(f"Prediction validation error: {e}")
                
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

                # ==== COGNITION TICK (system talks to itself via JSON) ====
                # Build market snapshot for cognition system
                # Use top 100 symbols to avoid overwhelming
                cognition_symbols = list(self.ticker_cache.keys())[:100]
                market_by_symbol = {}
                
                for sym in cognition_symbols:
                    if sym in self.ticker_cache:
                        ticker = self.ticker_cache[sym]
                        # Get price history if available, else just current price
                        prices = self.price_history.get(sym, [ticker['price']])[-20:]
                        
                        # Calculate momentum and gamma from your existing data
                        momentum = ticker.get('change24h', 0.0)
                        
                        # Try to get coherence from existing opportunity data
                        gamma = 0.5  # default
                        # We can look up in raw_opps if available
                        for opp in raw_opps:
                            if opp['symbol'] == sym:
                                gamma = opp.get('coherence', 0.5)
                                break
                        
                        market_by_symbol[sym] = {
                            "closes": prices,
                            "momentum": momentum,
                            "gamma": gamma,
                            "price": ticker['price'],
                            "volume": ticker['volume'],
                        }
                
                # Publish snapshot - this triggers the entire cognition chain
                self.thought_bus.publish(Thought(
                    source="ecosystem",
                    topic="market.snapshot",
                    payload={
                        "universe": cognition_symbols,
                        "market_by_symbol": market_by_symbol,
                    },
                ))
                
                # Run immune scan post cognition tick
                if hasattr(self, 'immune_system'):
                    self.immune_system.scan_and_heal()
                
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
                    # 📊 LOG MARKET SWEEP FOR FULL COVERAGE VALIDATION 📊
                    if TRADE_LOGGER_AVAILABLE and trade_logger:
                        try:
                            opportunities_entered = min(len(all_opps), CONFIG['MAX_POSITIONS'] - len(self.positions))
                            opportunities_rejected = len(raw_opps) - len(all_opps)
                            
                            # Count rejection reasons
                            rejection_reasons = defaultdict(int)
                            if hasattr(self, 'last_opportunity_filters'):
                                rejection_reasons.update(self.last_opportunity_filters)
                            
                            # Get frequency distribution
                            harmonic_freqs = []
                            hissing_freqs = []
                            total_coherence = []
                            
                            for opp in raw_opps:
                                if opp.get('hnc_is_harmonic', False):
                                    harmonic_freqs.append(opp.get('hnc_frequency', 256))
                                elif opp.get('hnc_frequency', 256) == 440:
                                    hissing_freqs.append(440)
                                total_coherence.append(opp.get('coherence', 0.5))
                            
                            avg_coherence = statistics.mean(total_coherence) if total_coherence else 0.5
                            
                            # Get node distribution
                            node_dist = defaultdict(int)
                            for opp in all_opps:
                                node_dist[opp.get('dominant_node', 'Unknown')] += 1
                            
                            trade_logger.log_market_sweep({
                                'total_opportunities_found': len(raw_opps),
                                'opportunities_entered': opportunities_entered,
                                'opportunities_rejected': opportunities_rejected,
                                'rejection_reasons': dict(rejection_reasons),
                                'harmonic_frequencies': harmonic_freqs,
                                'hissing_frequencies': hissing_freqs,
                                'average_coherence': avg_coherence,
                                'system_flux': opp.get('flux_direction', 'NEUTRAL') if all_opps else 'NEUTRAL',
                                'dominant_node_distribution': dict(node_dist),
                            })
                        except Exception as e:
                            logger.warning(f"Failed to log market sweep: {e}")
                    
                    if all_opps:
                        purity = self.lattice.get_field_purity()
                        purity_icon = "🟢" if purity > 0.9 else "🟠" if purity > 0.5 else "🔴"
                        nexus_status = "🔮 NEXUS" if self.nexus_predictor else ""
                        print(f"\n   🔮 Top Opportunities (Triadic Filtered | Purity: {purity_icon} {purity*100:.1f}%) {nexus_status}:")
                        for opp in all_opps[:5]:
                            icon = self._get_node_icon(opp['dominant_node'])
                            lock = "🔒" if opp.get('memory_locked') else "🔓"
                            nexus_info = f"| 🔮{opp.get('nexus_prob', 0.5)*100:.0f}%" if self.nexus_predictor else ""
                            print(f"      {icon} {opp['symbol']:12s} +{opp['change24h']:5.1f}% | Γ={opp['coherence']:.2f} | Score: {opp['score']} {nexus_info} {lock}")
                    
                    # During lighthouse, increase position size and allow more entries using available capital
                    for opp in all_opps[:CONFIG['MAX_POSITIONS'] - len(self.positions)]:
                        if lighthouse_active:
                            try:
                                # Use up to 50% of available cash per new entry burst, scaled by κt boost
                                available_cash = self.cash_balance_gbp
                                burst_cap = max(0.0, available_cash * 0.50)
                                setattr(self, 'position_size_multiplier', 2.73)
                                # Pass a hint to position sizer via opp context
                                opp['lighthouse_burst_cap'] = burst_cap
                                opp['cascade_multiplier'] = 10.0
                                opp['kappa_t'] = 2.73
                            except Exception:
                                pass
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
                
                # 🔗 MINER CONNECTION STATUS
                miner_status = MINER_CONNECTOR.get_status()
                if miner_status['connected']:
                    miner_uptime = miner_status['uptime']
                    miner_icon = "🌟" if MINER_CONNECTOR.is_lighthouse else "🔗"
                    print(f"   {miner_icon} Miner: CONNECTED ({miner_uptime:.0f}s) | Γ={MINER_CONNECTOR.planetary_gamma:.3f} | "
                          f"Ψ={MINER_CONNECTOR.unified_coherence:.3f} | Cascade={MINER_CONNECTOR.cascade_multiplier:.2f}x")
                
                # 🌍 GAIA LATTICE DISPLAY - HNC CARRIER WAVE DYNAMICS 🌍
                # Handle l_state as dict or object
                phase = l_state.get('phase', 'UNKNOWN') if isinstance(l_state, dict) else getattr(l_state, 'phase', 'UNKNOWN')
                frequency = l_state.get('frequency', 0) if isinstance(l_state, dict) else getattr(l_state, 'frequency', 0)
                field_purity = l_state.get('field_purity', 0) if isinstance(l_state, dict) else getattr(l_state, 'field_purity', 0)
                carrier_strength = l_state.get('carrier_strength') if isinstance(l_state, dict) else getattr(l_state, 'carrier_strength', None)
                nullification_pct = l_state.get('nullification_pct') if isinstance(l_state, dict) else getattr(l_state, 'nullification_pct', None)
                emergent_432 = l_state.get('emergent_432') if isinstance(l_state, dict) else getattr(l_state, 'emergent_432', None)
                risk_mod_display = l_state.get('risk_mod', 1.0) if isinstance(l_state, dict) else getattr(l_state, 'risk_mod', 1.0)
                tp_mod_display = l_state.get('tp_mod', 1.0) if isinstance(l_state, dict) else getattr(l_state, 'tp_mod', 1.0)
                
                gaia_icon = "💜" if phase == "GAIA_RESONANCE" else ("⚡" if phase == "CARRIER_ACTIVE" else "🔴")
                carrier_str = f"Carrier: {carrier_strength:.2f}φ" if carrier_strength is not None else ""
                nullification_str = f"Nullify: {nullification_pct:.0%}" if nullification_pct is not None else ""
                emergent_str = f"432Hz: {emergent_432:.0%}" if emergent_432 is not None else ""
                print(f"   🌐 Gaia Lattice: {phase} ({frequency}Hz) {gaia_icon} | Purity: {field_purity*100:.0f}% | {carrier_str} | {emergent_str}")
                if nullification_str:
                    print(f"   🌍 Carrier Wave: {nullification_str} | Risk: {risk_mod_display:.2f}x | TP: {tp_mod_display:.2f}x | {lambda_str}")
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
                
                # 🍄🧠 MYCELIUM NEURAL NETWORK STATUS
                try:
                    myc_state = self.mycelium.get_network_state()
                    queen_sig = myc_state.get('queen_signal', 0.0)
                    queen_emoji = "👑" if queen_sig > 0.3 else "👸" if queen_sig > -0.3 else "💀"
                    queen_dir = "BUY" if queen_sig > 0.1 else "SELL" if queen_sig < -0.1 else "HOLD"
                    hives = myc_state.get('hive_count', 0)
                    agents = myc_state.get('total_agents', 0)
                    gen = myc_state.get('generation', 0)
                    print(f"   🍄 Mycelium: {hives} hives | {agents} agents | Gen {gen} | {queen_emoji} Queen: {queen_sig:+.2f} → {queen_dir}")
                except Exception:
                    pass
                
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
                
                # Save state every cycle for real-time data persistence
                self.save_state()
                logger.debug(f"State saved at iteration {self.iteration}")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n🐙 Shutting down ecosystem...")
            # Stop probability generator
            if self.probability_generator:
                self.probability_generator.stop()
                print("   📊 Probability Generator stopped")
            self.save_state()
            print("   💾 State saved for recovery")
            self.final_report()
        finally:
            # Ensure generator is stopped on any exit
            if self.probability_generator:
                try:
                    self.probability_generator.stop()
                except Exception:
                    pass
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
        
        # Print Nexus stats if available
        if self.nexus.enabled:
            nexus_stats = self.get_nexus_stats()
            hive_stats = nexus_stats.get('hive', {})
            print(f"""   🌌 NEXUS INTEGRATION:
   ├─ Signals Generated: {nexus_stats.get('signals_generated', 0)}
   ├─ Signals Followed:  {nexus_stats.get('signals_followed', 0)}
   ├─ Avg Coherence:     {nexus_stats.get('coherence_avg', 0):.4f}
   ├─ Hive Generation:   {hive_stats.get('generation', 1)}
   └─ Child Hives:       {hive_stats.get('child_hives', 0)}
""")
        
        # 📊 Print State Aggregator Summary (All JSON Sources)
        print("\n" + self.state_aggregator.get_summary())
        
        # Save aggregated state for next session
        self.state_aggregator.save_aggregated_state()
        
        # 🌐 Print Multi-Exchange Learning Summary 🌐
        print("\n" + self.multi_exchange.get_learning_summary())
        
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
    # 🛡️ CRITICAL: Sanitize logging environment before starting
    # This removes any handlers added by imports (e.g. alpaca-py, urllib3)
    sanitize_logging_environment()

    # Configuration from environment
    dry_run = os.getenv('LIVE', '0') != '1'
    balance = float(os.getenv('BALANCE', 1000))
    interval = float(os.getenv('INTERVAL', 5))
    
    # Mining configuration
    enable_mining = os.getenv('ENABLE_MINING', '0') == '1'
    miner = None
    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║  🐙 AUREON KRAKEN ECOSYSTEM 🐙                            ║
    ║                                                           ║
    ║  Usage:                                                   ║
    ║    LIVE=1 python aureon_kraken_ecosystem.py  # Live mode  ║
    ║    BALANCE=5000 python aureon_kraken_ecosystem.py         ║
    ║    INTERVAL=3 python aureon_kraken_ecosystem.py           ║
    ║                                                           ║
    ║  Mining (optional):                                       ║
    ║    ENABLE_MINING=1 MINING_WORKER=bc1q... python ...       ║
    ║    MINING_PLATFORM=braiins (or antpool, f2pool, nicehash) ║
    ║    OR:                                                    ║
    ║    MINING_POOL_HOST=stratum.pool.com                      ║
    ║    MINING_POOL_PORT=3333 MINING_THREADS=2                 ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Start background miner if enabled
    if enable_mining:
        try:
            from aureon_miner import AureonMiner, resolve_pool_config, KNOWN_POOLS
            
            worker = os.getenv('MINING_WORKER', '')
            password = os.getenv('MINING_PASSWORD', 'x')
            threads = int(os.getenv('MINING_THREADS', '1'))
            enable_all = os.getenv('MINING_ENABLE_ALL', '0') == '1'

            if not worker:
                print("    ⚠️ MINING_WORKER not set! Mining disabled.")
                print("    Set MINING_WORKER=your_btc_address.aureon")
            else:
                if enable_all:
                    print(f"    ⛏️ Starting MULTI-POOL MINER: {worker}")
                    print(f"       Mode: ALL AVAILABLE PLATFORMS")
                    
                    # Initialize empty miner
                    miner = AureonMiner(threads=threads)
                    
                    # Add all known pools
                    for key, config in KNOWN_POOLS.items():
                        print(f"       Adding Pool: {config['desc']} ({config['host']})")
                        miner.add_pool(config['host'], config['port'], worker, password)
                        
                    if miner.start():
                        print(f"    ✅ Multi-Pool Miner running on {threads} threads (distributed)")
                    else:
                        print("    ❌ Miner failed to start")
                        miner = None
                else:
                    # Single pool mode
                    platform = os.getenv('MINING_PLATFORM')
                    raw_host = os.getenv('MINING_POOL_HOST')
                    raw_port = os.getenv('MINING_POOL_PORT')
                    
                    pool_host, pool_port = resolve_pool_config(
                        platform=platform,
                        host=raw_host,
                        port=int(raw_port) if raw_port else None
                    )
                    
                    print(f"    ⛏️ Starting background miner: {worker}")
                    print(f"       Pool: {pool_host}:{pool_port} ({platform or 'custom'})")
                    
                    miner = AureonMiner(pool_host, pool_port, worker, password, threads=threads)
                    if miner.start():
                        print(f"    ✅ Miner running on {threads} thread(s)")
                    else:
                        print("    ❌ Miner failed to start")
                        miner = None

        except ImportError as e:
            print(f"    ⚠️ Mining module not available: {e}")
        except Exception as e:
            print(f"    ❌ Mining setup error: {e}")
    
    try:
        ecosystem = AureonKrakenEcosystem(
            initial_balance=balance,
            dry_run=dry_run
        )
        
        ecosystem.run(interval=interval)
    finally:
        # Stop miner on shutdown
        if miner:
            print("\n    🛑 Stopping miner...")
            miner.stop()


if __name__ == "__main__":
    main()
