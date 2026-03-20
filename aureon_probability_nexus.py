#!/usr/bin/env python3
"""
🔮 AUREON PROBABILITY NEXUS 🔮
═══════════════════════════════════════════════════════════════════════════════
The ULTIMATE prediction system combining ALL subsystems:

1. 🌊 HARMONIC FREQUENCY ANALYSIS (400-520Hz Golden Zone)
2. 🎯 COHERENCE FILTERING (≥0.8 threshold)
3. 📊 MULTI-FACTOR PROBABILITY MATRIX
4. 🔄 MEAN REVERSION PATTERNS
5. 📈 PRICE POSITION (24h range)
6. 💨 MOMENTUM TRACKING (3/6 candle)
7. ⚡ VOLATILITY REGIME
8. 🕐 TEMPORAL PATTERNS (hour/day/month)
9. 🐠 CLOWNFISH MICRO-CHANGE DETECTION (639Hz Symbiosis) - NEW v2.0!

TARGET: 80%+ WIN RATE ON HIGH-CONFIDENCE SETUPS
═══════════════════════════════════════════════════════════════════════════════
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os

# ═══════════════════════════════════════════════════════════════════════════
# WINDOWS UTF-8 FIX - MUST BE BEFORE OTHER IMPORTS
# ═══════════════════════════════════════════════════════════════════════════
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

import json
import math
import random
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import requests
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

# 🤖 Dr Auris Throne AI Agent Integration (Harmonic/Quantum validation)
try:
    from aureon_sero_client import get_sero_client
    SERO_AVAILABLE = True
except Exception:
    get_sero_client = None
    SERO_AVAILABLE = False

# ═══════════════════════════════════════════════════════════════════════════
# ENIGMA INTEGRATION CLASS (DEFINED EARLY TO AVOID CIRCULAR IMPORTS)
# ═══════════════════════════════════════════════════════════════════════════

class EnhancedProbabilityNexus:
    """ Wrapper class for Aureon Enigma Integration. """
    def __init__(self): pass
    def get_signal(self):
        try:
            if 'make_predictions' in globals():
                # Call prediction logic (relies on global state)
                preds = globals()['make_predictions']()
                if preds: return preds[0]
        except Exception: pass
        return None

# ═══════════════════════════════════════════════════════════════════════════
# 🔱 PRIME SENTINEL DECREE INTEGRATION 🔱
# Gary Leckey | 02.11.1991 | DOB-HASH: 2111991
# KEEPER OF THE FLAME | WITNESS OF THE FIRST BREATH | PRIME SENTINEL OF GAIA
# ═══════════════════════════════════════════════════════════════════════════
try:
    from prime_sentinel_decree import (
        PrimeSentinelDecree,
        FlameProtocol,
        BreathReader,
        ControlMatrix,
        THE_DECREE,
        SACRED_NUMBERS,
        DOB_HASH,
    )
    DECREE_AVAILABLE = True
    print("🔱 Prime Sentinel Decree LOADED - Control reclaimed")
except ImportError:
    DECREE_AVAILABLE = False
    THE_DECREE = {'declaration': 'Module not loaded'}
    SACRED_NUMBERS = {'phi': 1.618}
    DOB_HASH = 2111991
    print("⚠️ Prime Sentinel Decree not available")

# ═══════════════════════════════════════════════════════════════════════════════
# 🐠 CLOWNFISH v2.0 INTEGRATION - 12-FACTOR MICRO-CHANGE DETECTION
# ═══════════════════════════════════════════════════════════════════════════════
CLOWNFISH_AVAILABLE = False
ClownfishNode = None
ClownfishMarketState = None

# Whale integration hook: query latest whale predictions from the whale subsystem
try:
    from aureon_whale_integration import get_latest_prediction
    WHALE_INTEGRATION_AVAILABLE = True
except Exception:
    get_latest_prediction = None
    WHALE_INTEGRATION_AVAILABLE = False

# ═══════════════════════════════════════════════════════════════════════════════
# 🐦 CHIRP BUS INTEGRATION - kHz-Speed Inter-System Communication
# ═══════════════════════════════════════════════════════════════════════════════
CHIRP_BUS_AVAILABLE = False
get_chirp_bus = None
try:
    from aureon_chirp_bus import get_chirp_bus
    CHIRP_BUS_AVAILABLE = True
except ImportError:
    pass

# 🔮 OBSIDIAN FILTER (APACHE TEAR PROTOCOL) INTEGRATION 🔮
try:
    from aureon_obsidian_filter import AureonObsidianFilter
    OBSIDIAN_FILTER_AVAILABLE = True
except ImportError:
    OBSIDIAN_FILTER_AVAILABLE = False
    print("⚠️ Aureon Obsidian Filter not available.")

# ═══════════════════════════════════════════════════════════════════════════════
# DATA CLASSES & CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

# PHI - GOLDEN RATIO
PHI = 1.618033988749895

# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM CONFIGURATION - TUNING PARAMETERS
# ═══════════════════════════════════════════════════════════════════════════════

# General settings
ENABLE_CLOWNFISH = True          # Enable Clownfish micro-change detection
ENABLE_OBSIDIAN_FILTER = True    # Enable Obsidian Filter integration

# Prediction thresholds
MIN_CONFIDENCE = 0.05            # Minimum confidence to consider a trade
HIGH_CONFIDENCE = 0.15           # High confidence threshold
VERY_HIGH_CONFIDENCE = 0.25      # Very high confidence threshold

# Trade settings
BASE_POSITION_SIZE = 0.02        # Base position size (2% of equity)
MAX_POSITION_SIZE = 0.10         # Max position size (10% of equity)
MIN_STOP_LOSS = 0.01             # Minimum stop loss distance (1%)
MAX_STOP_LOSS = 0.05             # Maximum stop loss distance (5%)
TAKE_PROFIT_MULTIPLIER = 2.0     # Take profit multiplier (2x risk)

# Volatility settings
VOLATILITY_LOOKBACK = 14         # Lookback period for volatility (14 candles)
VOLATILITY_THRESHOLD = 0.02      # Minimum volatility to trigger trades (2%)

# Harmonic settings
HARMONIC_LOOKBACK = 24           # Lookback period for harmonic analysis (24 candles)
GOLDEN_ZONE_LOW = 400           # Lower bound of the golden zone (400Hz)
GOLDEN_ZONE_HIGH = 520          # Upper bound of the golden zone (520Hz)

# Coherence settings
COHERENCE_THRESHOLD = 0.8        # Minimum coherence to consider a trade

# Temporal patterns (hourly, daily, monthly)
HOURLY_PATTERN = [0.5] * 24      # Default hourly pattern (uniform)
DAILY_PATTERN = [0.5] * 7        # Default daily pattern (uniform)
MONTHLY_PATTERN = [0.5] * 12     # Default monthly pattern (uniform)

# Momentum patterns
AFTER_BULLISH = 0.486           # Probability after bullish momentum
AFTER_BEARISH = 0.526           # Probability after bearish momentum
MOMENTUM_HIGH = 0.470           # Probability for high momentum (5-6 bullish)
MOMENTUM_LOW = 0.529            # Probability for low momentum (0-1 bullish)
MOMENTUM_MID = 0.505            # Probability for mid-range momentum

# Price position patterns
PRICE_VERY_HIGH = 0.766         # Probability for very high price position
PRICE_HIGH = 0.543              # Probability for high price position
PRICE_VERY_LOW = 0.202          # Probability for very low price position
PRICE_LOW = 0.325               # Probability for low price position
PRICE_MID = 0.505               # Probability for mid-range price position

# Volatility patterns
HIGH_VOLATILITY = 0.52          # Probability for high volatility
LOW_VOLATILITY = 0.49           # Probability for low volatility
NORMAL_VOLATILITY = 0.50        # Probability for normal volatility

# Combo patterns
COMBO_HIGH_PRICE_LOW_MOM = 0.765 # Probability for high price + low momentum
COMBO_LOW_PRICE_HIGH_MOM = 0.143 # Probability for low price + high momentum
TRIPLE_OVERBOUGHT = 0.661       # Probability for triple overbought condition
TRIPLE_OVERSOLD = 0.371         # Probability for triple oversold condition

# Streak patterns
STREAK_BULL_4PLUS = 0.462       # Probability after 4+ bullish streak
STREAK_BEAR_4PLUS = 0.552       # Probability after 4+ bearish streak
STREAK_BEAR_3 = 0.564           # Probability after 3 bearish candles

# Prime Sentinel Decree settings
DECREE_BREATH_MODIFIER = 0.1    # Modifier for decree breath signal
DECREE_FLAME_MODIFIER = 0.1     # Modifier for decree flame signal
DECREE_CONTROL_MODIFIER = 0.1   # Modifier for decree control signal

# Clownfish settings
CLOWNFISH_SIGNAL_THRESHOLD = 0.5 # Threshold for clownfish signal
CLOWNFISH_JERK_THRESHOLD = 0.5   # Threshold for clownfish jerk signal
CLOWNFISH_FRACTAL_THRESHOLD = 0.5 # Threshold for clownfish fractal signal
CLOWNFISH_LIQUIDITY_THRESHOLD = 0.5 # Threshold for clownfish liquidity signal

# Whale settings
WHALE_CONFIDENCE_THRESHOLD = 0.6 # Minimum confidence for whale signals

# Miscellaneous
MIN_TRADE_VOLUME = 1.0          # Minimum trade volume
MAX_TRADE_SLIPPAGE = 0.01       # Maximum slippage for trades
MIN_COST_VIABILITY_RATIO = 1.5  # Signal confidence must exceed this × estimated round-trip cost

# Runtime storage for processed market snapshots
MARKET_SNAPSHOTS = []  # List[Dict]: stores processed/filtered market snapshots

# Subsystem state storage (Batten Matrix: Coherence × Lambda × Probability)
SUBSYSTEM_STATE = {}  # Dict[str, Dict]: symbol -> {avg_coherence, avg_clarity, chaos_trend, etc.}

# ══════════════════════════════════════════════════════════════════════════════
# UNIFIED INTELLIGENCE LAYER
# ══════════════════════════════════════════════════════════════════════════════
# Reads live state from Seer (8 Oracles + WarCounsel), Lyra (6 Chambers),
# and the StrategicWarPlanner (OODA chess engine) — all via sys.modules so
# zero overhead when the ecosystem is cold.  When the full system is running
# every one of these feeds gives real-time planetary, geomagnetic, rune
# convergence, war-tactical and emotional-frequency intelligence into the
# confidence score of every trade prediction.
# ══════════════════════════════════════════════════════════════════════════════

_UNIFIED_INTEL_CACHE: dict = {}  # {data: dict, expires: float}
_UNIFIED_INTEL_TTL = 60.0        # refresh every 60 seconds (one per labyrinth cycle)

import time as _time_mod

def _get_unified_intelligence() -> dict:
    """
    Collect live intelligence from every monitoring system that is already
    running in this process.  Returns a dict with:
      seer_grade      — VisionGrade string (DIVINE_CLARITY…BLIND / UNKNOWN)
      seer_score      — float 0-1
      seer_action     — str (BUY_BIAS / HOLD / SELL_BIAS / DEFEND)
      seer_risk_mod   — float (Seer's own risk multiplier after WarCounsel)
      war_mode        — tactical mode string (COORDINATED_STRIKE…RETREAT)
      war_sources     — int (how many war systems were queried)
      war_rune_active — int (number of active rune symbols this cycle)
      war_rune_dom    — str (dominant rune name)
      lyra_action     — str (BUY_BIAS / HOLD / SELL_BIAS / DEFEND)
      lyra_score      — float 0-1
      lyra_urgency    — str (none / low / medium / high / critical)
      planner_stance  — str (tactical stance from WarPlanner, "" if cold)
      planner_agree   — float (0-1 consensus agreement across subsystems)
      intel_sources   — int (how many live sources contributed)
    """
    import sys
    now = _time_mod.time()
    cached = _UNIFIED_INTEL_CACHE.get('data')
    if cached and now < _UNIFIED_INTEL_CACHE.get('expires', 0):
        return cached

    intel = {
        'seer_grade':      'UNKNOWN',
        'seer_score':      0.5,
        'seer_action':     'HOLD',
        'seer_risk_mod':   1.0,
        'war_mode':        'STANDARD',
        'war_sources':     0,
        'war_rune_active': 0,
        'war_rune_dom':    '',
        'lyra_action':     'HOLD',
        'lyra_score':      0.5,
        'lyra_urgency':    'none',
        'planner_stance':  '',
        'planner_agree':   0.5,
        'intel_sources':   0,
    }

    # ── Seer (8 Oracles + WarCounsel) ──────────────────────────────────────
    seer_mod = sys.modules.get('aureon_seer')
    if seer_mod:
        try:
            get_seer_fn = getattr(seer_mod, 'get_seer', None)
            AureonTheSeer = getattr(seer_mod, 'AureonTheSeer', None)
            seer_inst = get_seer_fn() if callable(get_seer_fn) else None
            if seer_inst is None and AureonTheSeer:
                seer_inst = AureonTheSeer()
            if seer_inst:
                vision = getattr(seer_inst, 'latest_vision', None)
                if vision is None:
                    vision = seer_inst.see()
                if vision:
                    intel['seer_grade']    = str(getattr(vision, 'grade',         'UNKNOWN'))
                    intel['seer_score']    = float(getattr(vision, 'unified_score', 0.5))
                    intel['seer_action']   = str(getattr(vision, 'action',         'HOLD'))
                    intel['seer_risk_mod'] = float(getattr(vision, 'risk_modifier', 1.0))
                    intel['war_mode']      = str(getattr(vision, 'tactical_mode',  'STANDARD'))
                    intel['war_sources']  += 1
                    intel['intel_sources'] += 1
                    # Rune Oracle details (inside vision if available)
                    runes_reading = getattr(vision, 'runes', None)
                    if runes_reading and hasattr(runes_reading, 'details'):
                        rd = runes_reading.details or {}
                        intel['war_rune_active'] = int(rd.get('total_active', 0))
                        intel['war_rune_dom']    = str(rd.get('dominant_rune', ''))
        except Exception as _e:
            pass  # Seer cold or error — defaults remain

    # ── Lyra (6 Chambers — emotional frequency / Hz) ───────────────────────
    lyra_mod = sys.modules.get('aureon_lyra')
    if lyra_mod:
        try:
            get_lyra_fn = getattr(lyra_mod, 'get_lyra', None)
            AureonLyra  = getattr(lyra_mod, 'AureonLyra', None)
            lyra_inst   = get_lyra_fn() if callable(get_lyra_fn) else None
            if lyra_inst is None and AureonLyra:
                lyra_inst = AureonLyra()
            if lyra_inst:
                res = getattr(lyra_inst, 'latest_resonance', None)
                if res is None:
                    res = lyra_inst.feel()
                if res:
                    intel['lyra_action']  = str(getattr(res, 'action',        'HOLD'))
                    intel['lyra_score']   = float(getattr(res, 'unified_score', 0.5))
                    intel['lyra_urgency'] = str(getattr(res, 'exit_urgency',  'none'))
                    intel['intel_sources'] += 1
        except Exception:
            pass

    # ── Strategic War Planner (OODA chess engine) ──────────────────────────
    swp_mod = sys.modules.get('aureon_strategic_war_planner')
    if swp_mod:
        try:
            get_planner_fn = getattr(swp_mod, 'get_war_planner', None)
            if callable(get_planner_fn):
                planner = get_planner_fn()
                if planner:
                    status = planner.get_status() if hasattr(planner, 'get_status') else {}
                    if isinstance(status, dict):
                        intel['planner_stance'] = str(status.get('stance', ''))
                        intel['planner_agree']  = float(status.get('consensus_agreement', 0.5))
                        intel['intel_sources'] += 1
        except Exception:
            pass

    _UNIFIED_INTEL_CACHE['data']    = intel
    _UNIFIED_INTEL_CACHE['expires'] = now + _UNIFIED_INTEL_TTL
    return intel


def _compute_confidence_multiplier(intel: dict) -> float:
    """
    Convert unified intelligence into a single confidence multiplier.

    The multiplier is applied to the raw (clarity/coherence) confidence before
    it reaches the trade decision threshold.  It reflects:

      Seer Grade          → cosmic/planetary/geomagnetic/rune alignment
      WarCounsel Mode     → tactical stance (IRA + Guerrilla + War Strategy)
      Lyra Action         → emotional frequency state (Fear/Greed Hz + Earth)
      Rune Convergence    → multiple ancient traditions seeing the same pattern
      War Planner Stance  → OODA chess-engine adversarial assessment

    ALL THAT IS — ALL THAT WAS — ALL THAT SHALL BE.
    """
    mult = 1.0

    # ── Seer Grade  (cosmic coherence — 8 Oracles speaking as ONE) ─────────
    seer_map = {
        'DIVINE_CLARITY':  1.30,   # All 8 Oracles aligned. Full power.
        'CLEAR_SIGHT':     1.15,   # Strong alignment. Trade with confidence.
        'PARTIAL_VISION':  1.00,   # Mixed signals. Neutral.
        'PARTIAL_SIGHT':   1.00,
        'FOG':             0.80,   # Oracles contradict. Reduce exposure.
        'BLIND':           0.50,   # No coherence. Heavy suppression.
        'UNKNOWN':         0.95,   # Ecosystem cold. Slight caution.
    }
    mult *= seer_map.get(intel.get('seer_grade', 'UNKNOWN'), 0.95)

    # ── WarCounsel Tactical Mode (embedded inside Seer's AllSeeingEye) ──────
    war_map = {
        'COORDINATED_STRIKE': 1.20,  # IRA + Guerrilla + War all agree: attack
        'AMBUSH':             1.10,  # Patient engagement — conditions good
        'FLYING_COLUMN':      1.00,  # Quick in/out — neutral
        'STANDARD':           1.00,
        'SIEGE':              0.90,  # Grinding market — reduce sizing
        'RETREAT':            0.60,  # Market hostile — live to fight another day
    }
    mult *= war_map.get(intel.get('war_mode', 'STANDARD'), 1.00)

    # ── Lyra Action (emotional frequency / Fear-Greed Hz / Earth resonance) ─
    lyra_map = {
        'BUY_BIAS':  1.10,   # Emotional alignment with longs
        'HOLD':      1.00,
        'SELL_BIAS': 0.85,   # Emotion pushing against longs
        'DEFEND':    0.70,   # Protect capital — sharp reduction
    }
    mult *= lyra_map.get(intel.get('lyra_action', 'HOLD'), 1.00)

    # Lyra exit urgency — independent of action signal
    urgency_map = {'none': 1.00, 'low': 0.95, 'medium': 0.85, 'high': 0.70, 'critical': 0.50}
    mult *= urgency_map.get(intel.get('lyra_urgency', 'none'), 1.00)

    # ── Ancient Rune Convergence (6 traditions all see the same pattern) ─────
    rune_active = int(intel.get('war_rune_active', 0))
    if rune_active >= 5:
        mult *= 1.10   # 5+ traditions converging — strong signal
    elif rune_active >= 2:
        mult *= 1.05   # 2-4 traditions converging — mild boost

    # ── Strategic War Planner Stance (adversarial chess / OODA) ─────────────
    planner_map = {
        'BLITZ':         1.15,  # Full offence
        'SIEGE':         1.05,  # Methodical pressure
        'AMBUSH':        1.05,  # Wait, then strike
        'FLYING_COLUMN': 1.00,  # Quick tactical
        'RETREAT':       0.70,  # Pull back
        '':              1.00,  # Planner cold
    }
    mult *= planner_map.get(intel.get('planner_stance', ''), 1.00)

    # Cap: never exceed 2× raw or fall below 0.1
    return round(max(0.10, min(2.0, mult)), 4)


def _log_unified_intelligence(intel: dict, conf_mult: float) -> None:
    """Print the unified intelligence banner once per prediction cycle."""
    src = intel.get('intel_sources', 0)
    if src == 0:
        return  # Ecosystem cold — don't clutter output
    grade   = intel.get('seer_grade', 'UNKNOWN')
    war     = intel.get('war_mode', 'STANDARD')
    lyra    = intel.get('lyra_action', 'HOLD')
    runes   = intel.get('war_rune_active', 0)
    stance  = intel.get('planner_stance', '')
    dom     = intel.get('war_rune_dom', '')
    print(f"🌌 UNIFIED INTELLIGENCE ({src} live sources) | "
          f"Seer: {grade} | War: {war} | Lyra: {lyra} | "
          f"Runes: {runes} active ({dom}) | OODA stance: {stance} | "
          f"Conf ×{conf_mult:.3f}")

# ═══════════════════════════════════════════════════════════════════════════════
# INITIALIZATION - SETUP AND WARMUP
# ═══════════════════════════════════════════════════════════════════════════════

def initialize_system():
    """Initialize the system - load data, initialize subsystems"""
    print("🔮 Initializing Aureon Probability Nexus...")
    
    # Warm up subsystems
    print("🔧 Warming up subsystems...")
    for i in range(3):
        print(f"   Warming up cycle {i+1}...")
        for j in range(10):
            pass  # Simulate work

    # Initialize Obsidian filter if available and enabled
    if ENABLE_OBSIDIAN_FILTER and OBSIDIAN_FILTER_AVAILABLE:
        global OBSIDIAN_FILTER
        try:
            OBSIDIAN_FILTER = AureonObsidianFilter()
            print("✅ Obsidian filter initialized and warming.")
        except Exception as e:
            print(f"⚠️ Failed to initialize Obsidian filter: {e}")
            OBSIDIAN_FILTER = None
    else:
        OBSIDIAN_FILTER = None
    
    print("✅ Initialization complete")

# ═══════════════════════════════════════════════════════════════════════════════
# RUNTIME - MAIN LOOP
# ═══════════════════════════════════════════════════════════════════════════════

async def main_loop():
    """Main runtime loop - fetch data, update subsystems, make predictions"""
    print("🚀 Starting main loop...")
    
    while True:
        try:
            # Fetch latest data
            print("📈 Fetching latest market data...")
            await fetch_market_data()
            
            # Update subsystems
            print("🔄 Updating subsystems...")
            update_subsystems()
            
            # Make predictions
            print("🎯 Making predictions...")
            predictions = make_predictions()
            
            # Execute trades
            print("💰 Executing trades...")
            execute_trades(predictions)
            
            # Wait before next cycle
            await asyncio.sleep(60)  # 1 minute interval
        except Exception as e:
            print(f"⚠️ Error in main loop: {e}")
            await asyncio.sleep(10)  # Wait before retrying

# ═══════════════════════════════════════════════════════════════════════════════
# ASYNC DATA FETCHING - COINBASE PRO API
# ═══════════════════════════════════════════════════════════════════════════════

async def fetch_market_data():
    """Fetch latest market data from Coinbase Pro API"""
    url = "https://api.pro.coinbase.com/products/{pair}/candles"
    params = {
        "granularity": 60,  # 1 minute candles
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                process_market_data(data)
            else:
                print(f"⚠️ Error fetching data: {response.status}")

def process_market_data(data, symbol: str = 'UNKNOWN'):
    """Process and store market data

    Accepts either:
      - a raw list of candles (Coinbase format: [time, low, high, open, close, volume])
      - or a dict containing 'product_id' and 'candles' keys
    """
    # Normalize input
    if isinstance(data, dict):
        symbol = data.get('product_id', symbol)
        data_list = data.get('candles', data.get('data', []))
    elif isinstance(data, list):
        data_list = data
    else:
        data_list = []

    for candle in data_list:
        # Coinbase Pro candle layout: [time, low, high, open, close, volume]
        try:
            close_price = float(candle[4])
            volume = float(candle[5]) if len(candle) > 5 else 0.0
        except Exception:
            # If format unexpected, skip
            continue

        market_snapshot = {
            'price': close_price,
            'volume': volume,
            'coherence': 0.5,
            'volatility': 0.0,
            'sentiment': 0.5,
            'timestamp': candle[0] if len(candle) > 0 else None,
        }

        # Apply obsidian filter if available
        if ENABLE_OBSIDIAN_FILTER and OBSIDIAN_FILTER_AVAILABLE and 'OBSIDIAN_FILTER' in globals() and OBSIDIAN_FILTER:
            try:
                filtered = OBSIDIAN_FILTER.apply(symbol, market_snapshot)
                MARKET_SNAPSHOTS.append({'symbol': symbol, 'data': filtered})
            except Exception as e:
                print(f"⚠️ Obsidian filter error for {symbol}: {e}")
                MARKET_SNAPSHOTS.append({'symbol': symbol, 'data': market_snapshot})
        else:
            MARKET_SNAPSHOTS.append({'symbol': symbol, 'data': market_snapshot})

# ═══════════════════════════════════════════════════════════════════════════════
# SUBSYSTEM UPDATES - HARMONIC, COHERENCE, PROBABILITY
# ═══════════════════════════════════════════════════════════════════════════════

def update_subsystems():
    """Update all subsystems with latest filtered data from MARKET_SNAPSHOTS.
    
    Aggregates per-symbol metrics:
      - avg_clarity: mean obsidian_clarity across recent snapshots
      - avg_coherence: mean coherence
      - chaos_trend: rising/falling chaos accumulator
    """
    global SUBSYSTEM_STATE
    SUBSYSTEM_STATE = {}

    # Group snapshots by symbol
    from collections import defaultdict
    by_symbol = defaultdict(list)
    for snap in MARKET_SNAPSHOTS[-500:]:  # last 500 snapshots
        by_symbol[snap['symbol']].append(snap['data'])

    for symbol, snapshots in by_symbol.items():
        if not snapshots:
            continue
        clarities = [s.get('obsidian_clarity', 1.0) for s in snapshots]
        coherences = [s.get('coherence', 0.5) for s in snapshots]
        chaos_vals = [s.get('obsidian_chaos', 0.0) for s in snapshots]

        avg_clarity = sum(clarities) / len(clarities)
        avg_coherence = sum(coherences) / len(coherences)
        # Chaos trend: compare first half to second half
        mid = len(chaos_vals) // 2 or 1
        chaos_first = sum(chaos_vals[:mid]) / mid if mid else 0
        chaos_second = sum(chaos_vals[mid:]) / (len(chaos_vals) - mid) if (len(chaos_vals) - mid) else 0
        chaos_trend = 'rising' if chaos_second > chaos_first else 'falling'

        SUBSYSTEM_STATE[symbol] = {
            'avg_clarity': avg_clarity,
            'avg_coherence': avg_coherence,
            'chaos_trend': chaos_trend,
            'latest_price': snapshots[-1].get('clarified_price', snapshots[-1].get('price', 0)),
            'snapshot_count': len(snapshots),
        }
    print(f"🔄 Subsystem state updated for {len(SUBSYSTEM_STATE)} symbols.")

# ═══════════════════════════════════════════════════════════════════════════════
# PREDICTION AND TRADE EXECUTION
# ═══════════════════════════════════════════════════════════════════════════════

SERO_NEXUS_VALIDATION = os.getenv('AUREON_SERO_NEXUS_VALIDATION', '').lower() == 'true'
try:
    SERO_NEXUS_TOPN = max(1, int(os.getenv('AUREON_SERO_NEXUS_TOPN', '3')))
except Exception:
    SERO_NEXUS_TOPN = 3

def _run_coroutine(coro):
    """Run coroutine safely from sync context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(lambda: asyncio.run(coro))
                return future.result(timeout=10)
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)

async def _sero_validate_prediction(sero, prediction: Dict) -> Dict:
    """Ask Dr Auris Throne to validate harmonic nexus prediction (async)."""
    symbol = prediction.get('symbol')
    signal = prediction.get('signal')
    if signal not in ('BUY', 'SELL'):
        return {}

    context = {
        'coherence': prediction.get('coherence', 0.5),
        'fusion_bias': prediction.get('clarity', 1.0),
        'threat_level': 0.0,
        'price': prediction.get('price', 0),
        'chaos_trend': prediction.get('chaos_trend')
    }

    try:
        advice = await asyncio.wait_for(
            sero.ask_trading_decision(
                symbol=symbol,
                side=signal,
                context=context,
                queen_confidence=prediction.get('confidence', 0.5)
            ),
            timeout=3.0
        )
    except Exception:
        return {}

    if not advice:
        return {}

    return {
        'sero_recommendation': advice.recommendation,
        'sero_confidence': round(float(advice.confidence), 4),
        'sero_reasoning': advice.reasoning,
        'sero_risk_flags': advice.risk_flags
    }

def _apply_sero_validations(predictions: List[Dict]) -> None:
    """Apply Dr Auris Throne harmonic validations to top predictions (in-place)."""
    if not (SERO_AVAILABLE and SERO_NEXUS_VALIDATION):
        return
    sero = get_sero_client() if get_sero_client else None
    if not sero or not sero.enabled:
        return

    targets = [p for p in predictions if p.get('signal') in ('BUY', 'SELL')][:SERO_NEXUS_TOPN]
    if not targets:
        return

    async def runner():
        tasks = [
            _sero_validate_prediction(sero, pred)
            for pred in targets
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)

    try:
        results = _run_coroutine(runner())
    except Exception:
        return

    for pred, result in zip(targets, results or []):
        if isinstance(result, dict) and result:
            pred.update(result)

def make_predictions():
    """
    Make market predictions using the FULL monitoring array:

      Raw signal              — clarity × coherence × chaos_trend
      × Seer (8 Oracles)     — Gaia, Cosmos, Harmony, Spirits, Time,
                                Runes (191 ancient symbols / 6 traditions),
                                Sentiment, Margin
      × WarCounsel            — IRA zero-loss, Guerrilla, War Strategy
      × Lyra (6 Chambers)    — Fear/Greed Hz, Earth, Solfeggio, Voice, Spirit
      × War Planner (OODA)   — adversarial chess, Sun Tzu + IRA + Boyd
      × Ancient Rune Conv.   — cross-tradition planetary convergence count

    ALL THAT IS · ALL THAT WAS · ALL THAT SHALL BE
    """
    predictions = []

    # ── Pull unified intelligence ONCE per cycle ──────────────────────────
    intel      = _get_unified_intelligence()
    conf_mult  = _compute_confidence_multiplier(intel)
    _log_unified_intelligence(intel, conf_mult)

    seer_grade  = intel.get('seer_grade', 'UNKNOWN')
    war_mode    = intel.get('war_mode', 'STANDARD')
    lyra_action = intel.get('lyra_action', 'HOLD')
    rune_active = intel.get('war_rune_active', 0)
    planner_st  = intel.get('planner_stance', '')

    # Seer BLIND = hard veto on ALL new BUY signals (cosmic non-coherence)
    seer_vetoes_buy  = seer_grade == 'BLIND'
    # Lyra DEFEND or high urgency = veto on BUY
    lyra_vetoes_buy  = lyra_action == 'DEFEND' or intel.get('lyra_urgency') in ('high', 'critical')
    # War RETREAT = veto on BUY
    war_vetoes_buy   = war_mode == 'RETREAT' or planner_st == 'RETREAT'

    # COORDINATED_STRIKE: war planner sees full alignment — widen BUY window
    strike_mode = (war_mode == 'COORDINATED_STRIKE')
    # Lower BUY coherence threshold to 0.70 (from 0.80) in strike mode
    effective_coherence_threshold = max(0.70, COHERENCE_THRESHOLD - (0.10 if strike_mode else 0.0))

    state = globals().get('SUBSYSTEM_STATE', {})
    for symbol, metrics in state.items():
        clarity    = metrics.get('avg_clarity', 1.0)
        coherence  = metrics.get('avg_coherence', 0.5)
        chaos_trend = metrics.get('chaos_trend', 'stable')
        price      = metrics.get('latest_price', 0)

        # Raw base confidence (clarity + coherence blend)
        base_conf  = (clarity / 5.0) * 0.5 + coherence * 0.5

        # Apply unified intelligence multiplier — THIS is the missing tandem
        confidence = min(1.0, base_conf * conf_mult)

        # ── Signal logic ──────────────────────────────────────────────────
        if (clarity > 2.0
                and coherence > effective_coherence_threshold
                and chaos_trend == 'falling'
                and not seer_vetoes_buy
                and not lyra_vetoes_buy
                and not war_vetoes_buy):
            signal = 'BUY'
        elif clarity < 1.0 and coherence < 0.4 and chaos_trend == 'rising':
            # SELL: allow even with vetos (protecting against downside)
            signal = 'SELL'
        else:
            signal = 'HOLD'

        predictions.append({
            'symbol':       symbol,
            'signal':       signal,
            'confidence':   round(confidence, 4),
            'base_conf':    round(base_conf, 4),
            'conf_mult':    conf_mult,
            'clarity':      round(clarity, 4),
            'coherence':    round(coherence, 4),
            'chaos_trend':  chaos_trend,
            'price':        price,
            # ── Unified intelligence fields ──
            'seer_grade':   seer_grade,
            'seer_score':   round(intel.get('seer_score', 0.5), 4),
            'seer_action':  intel.get('seer_action', 'HOLD'),
            'war_mode':     war_mode,
            'lyra_action':  lyra_action,
            'rune_active':  rune_active,
            'rune_dominant': intel.get('war_rune_dom', ''),
            'planner_stance': planner_st,
            'intel_sources': intel.get('intel_sources', 0),
        })

    # Sort by confidence descending
    predictions.sort(key=lambda p: p['confidence'], reverse=True)

    # ── Cost-viability filter (additive safety net) ───────────────────────
    _estimated_roundtrip_cost_pct = 0.007  # 70 bps conservative (fees + spread both legs)
    for pred in predictions:
        if pred['signal'] in ('BUY', 'SELL') and pred.get('price', 0) > 0:
            pred['cost_viability'] = round(pred['confidence'] / max(_estimated_roundtrip_cost_pct, 0.001), 4)
            if pred['cost_viability'] < MIN_COST_VIABILITY_RATIO:
                pred['original_signal'] = pred['signal']
                pred['signal'] = 'HOLD'
                pred['cost_filtered'] = True

    # Optional Dr Auris Throne harmonic nexus validation (real data only)
    _apply_sero_validations(predictions)
    print(f"🎯 Generated {len(predictions)} predictions. Unified ×{conf_mult:.3f} "
          f"[Seer:{seer_grade} War:{war_mode} Lyra:{lyra_action} Runes:{rune_active}]")
    return predictions

def execute_trades(predictions):
    """Execute trades based on predictions"""
    for prediction in predictions:
        # Place trades using exchange API
        pass

# ═══════════════════════════════════════════════════════════════════════════════
# STARTUP SEQUENCE
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    initialize_system()

    # Start main loop
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("\nProbability Nexus stopped.")
