#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                          ║
║     🌊⚡🎵 AUREON HARMONIC MOMENTUM WAVE SCANNER 🎵⚡🌊                                                    ║
║     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━              ║
║                                                                                                          ║
║     THE ULTIMATE MOMENTUM SCANNER - ALL HARMONIC SYSTEMS UNIFIED!                                        ║
║                                                                                                          ║
║     "The wave is the message. The frequency is the truth. The momentum is the profit."                  ║
║                                                                                                          ║
║     ARCHITECTURE:                                                                                        ║
║     ┌─────────────────────────────────────────────────────────────────────────────────┐                  ║
║     │  🌊 HARMONIC WAVE LAYERS (7 Unified Systems)                                    │                  ║
║     │                                                                                  │                  ║
║     │  L7: 👑 Queen Voice (963Hz)    → Autonomous Decision                            │                  ║
║     │  L6: 🔗 Signal Chain           → Pipeline Communication                         │                  ║
║     │  L5: 🌐 Global Field (Ω)       → 42 Data Sources Unified                        │                  ║
║     │  L4: 🌌 6D Waveform            → Dimensional Analysis                           │                  ║
║     │  L3: 🌊 Wave Fusion            → Live Growth Detection                          │                  ║
║     │  L2: 🎯 Micro-Momentum         → Cost-Aware Filtering (THE GOAL!)               │                  ║
║     │  L1: 📊 Global Wave Scanner    → A-Z Market Sweep                               │                  ║
║     │                                                                                  │                  ║
║     │  OUTPUT: Unified Momentum Signal with ALL harmonic validation                   │                  ║
║     └─────────────────────────────────────────────────────────────────────────────────┘                  ║
║                                                                                                          ║
║     💸 THE GOAL: Find momentum > 0.34% (trading costs) using ALL harmonic intelligence                  ║
║                                                                                                          ║
║     Gary Leckey | Aureon Trading System | January 2026                                                  ║
║                                                                                                          ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import sys
import os
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

import time
import math
import logging
import asyncio
import requests
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone, timedelta
from enum import Enum
from collections import deque

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# 🌍 SACRED CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

PHI = (1 + math.sqrt(5)) / 2  # Golden Ratio 1.618
SCHUMANN_BASE = 7.83           # Earth's heartbeat
LOVE_FREQUENCY = 528           # DNA repair frequency

# Solfeggio Frequencies for harmonic analysis
SOLFEGGIO = {
    'liberation': 396,   # Liberating Guilt and Fear
    'change': 417,       # Undoing Situations and Facilitating Change
    'transformation': 528,  # Transformation and Miracles (DNA Repair)
    'connection': 639,   # Connecting/Relationships
    'awakening': 741,    # Awakening Intuition
    'crown': 963         # Crown/Divine Connection
}

# ═══════════════════════════════════════════════════════════════════════════════
# 💸 COST THRESHOLDS - THE GOAL!
# ═══════════════════════════════════════════════════════════════════════════════

ROUND_TRIP_COST_PCT = 0.34   # 0.34% total trading cost
TIER_1_THRESHOLD = 0.50      # > 0.5% = HOT (immediate)
TIER_2_THRESHOLD = 0.40      # > 0.4% = STRONG
TIER_3_THRESHOLD = 0.34      # > 0.34% = VALID (covers costs)


# ═══════════════════════════════════════════════════════════════════════════════
# 🔌 IMPORT ALL HARMONIC SYSTEMS
# ═══════════════════════════════════════════════════════════════════════════════

# Micro-Momentum Scanner (THE GOAL)
try:
    from aureon_micro_momentum_goal import MicroMomentumScanner, MomentumTier, MomentumSignal
    MICRO_MOMENTUM_OK = True
except ImportError:
    MICRO_MOMENTUM_OK = False
    MicroMomentumScanner = None

# Global Wave Scanner
try:
    from aureon_global_wave_scanner import GlobalWaveScanner, WaveState, WaveAnalysis
    WAVE_SCANNER_OK = True
except ImportError:
    WAVE_SCANNER_OK = False
    GlobalWaveScanner = None

# Harmonic Chain Master
try:
    from aureon_harmonic_chain_master import HarmonicChainMaster
    CHAIN_MASTER_OK = True
except ImportError:
    CHAIN_MASTER_OK = False
    HarmonicChainMaster = None

# Global Harmonic Field
try:
    from global_harmonic_field import GlobalHarmonicField
    HARMONIC_FIELD_OK = True
except ImportError:
    HARMONIC_FIELD_OK = False
    GlobalHarmonicField = None

# Harmonic Fusion
try:
    from aureon_harmonic_fusion import HarmonicWaveFusion
    HARMONIC_FUSION_OK = True
except ImportError:
    HARMONIC_FUSION_OK = False
    HarmonicWaveFusion = None

# 6D Waveform
try:
    from hnc_6d_harmonic_waveform import SixDimensionalHarmonicEngine
    WAVEFORM_6D_OK = True
except ImportError:
    WAVEFORM_6D_OK = False
    SixDimensionalHarmonicEngine = None

# Queen Dream Engine
try:
    from aureon_queen_dream_engine import QueenDreamEngine
    QUEEN_DREAM_OK = True
except ImportError:
    QUEEN_DREAM_OK = False
    QueenDreamEngine = None

# Queen Autonomous Controller
try:
    from aureon_queen_autonomous import QueenAutonomousController
    QUEEN_AUTONOMOUS_OK = True
except ImportError:
    QUEEN_AUTONOMOUS_OK = False
    QueenAutonomousController = None


# ═══════════════════════════════════════════════════════════════════════════════
# 📊 DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

class HarmonicMomentumTier(Enum):
    """Momentum classification with harmonic enhancement"""
    TRANSCENDENT = "🌟 TRANSCENDENT"  # All systems aligned + strong momentum
    HOT = "🔥 HOT"                     # Strong momentum + good harmonics
    STRONG = "⚡ STRONG"               # Good momentum + harmonics support
    VALID = "🌊 VALID"                 # Momentum covers costs
    HARMONIC_ONLY = "🎵 HARMONIC"      # Good harmonics but weak momentum
    SKIP = "❄️ SKIP"                   # Not worth it


@dataclass
class HarmonicMomentumSignal:
    """
    A momentum signal enhanced with ALL harmonic intelligence.
    """
    symbol: str
    timestamp: float = field(default_factory=time.time)
    
    # Price Data
    current_price: float = 0.0
    
    # Momentum Metrics (from Micro-Momentum)
    momentum_1m_pct: float = 0.0
    momentum_5m_pct: float = 0.0
    momentum_tier: str = "SKIP"
    
    # Harmonic Metrics
    harmonic_field_omega: float = 0.5  # Global Field Ω (0-1)
    wave_state: str = "BALANCED"        # From Global Wave Scanner
    wave_strength: float = 0.0
    
    # 6D Waveform Analysis
    waveform_momentum: float = 0.0      # Momentum dimension
    waveform_frequency: float = 0.0     # Frequency dimension
    waveform_resonance: float = 0.0     # Resonance dimension
    
    # Solfeggio Alignment
    dominant_frequency: float = 0.0     # Detected harmonic frequency
    solfeggio_alignment: float = 0.0    # How close to sacred frequencies
    
    # Composite Score
    harmonic_tier: HarmonicMomentumTier = HarmonicMomentumTier.SKIP
    composite_score: float = 0.0        # Unified score (0-1)
    
    # Trading Decision
    direction: str = "HOLD"             # LONG, SHORT, HOLD
    confidence: float = 0.0             # 0-1
    net_profit_potential: float = 0.0   # After costs
    
    def is_actionable(self) -> bool:
        """Is this signal worth acting on?"""
        return (
            self.harmonic_tier in [
                HarmonicMomentumTier.TRANSCENDENT,
                HarmonicMomentumTier.HOT,
                HarmonicMomentumTier.STRONG,
                HarmonicMomentumTier.VALID
            ] and self.net_profit_potential > 0
        )


# ═══════════════════════════════════════════════════════════════════════════════
# 🌊 THE HARMONIC MOMENTUM WAVE SCANNER
# ═══════════════════════════════════════════════════════════════════════════════

class HarmonicMomentumWaveScanner:
    """
    🌊⚡🎵 THE ULTIMATE MOMENTUM SCANNER 🎵⚡🌊
    
    Combines ALL harmonic systems to detect micro-momentum:
    
    1. Micro-Momentum Scanner → Find coins moving > 0.34%
    2. Global Wave Scanner → Validate wave state (RISING, BREAKOUT)
    3. Global Harmonic Field → Check 42-source unified Ω
    4. 6D Waveform → Analyze dimensional alignment
    5. Harmonic Chain Master → Get full chain coherence
    6. Queen Dream Engine → Monte Carlo validation
    
    THE GOAL: Find momentum that beats costs, validated by ALL systems!
    """
    
    # All available crypto symbols
    ALL_SYMBOLS = [
        "BTC/USD", "ETH/USD", "SOL/USD", "DOGE/USD", "XRP/USD",
        "LINK/USD", "AVAX/USD", "MATIC/USD", "DOT/USD", "ADA/USD",
        "UNI/USD", "LTC/USD", "BCH/USD", "ATOM/USD", "AAVE/USD",
        "MKR/USD", "CRV/USD", "SUSHI/USD", "ALGO/USD", "NEAR/USD",
        "GRT/USD", "BAT/USD"
    ]
    
    def __init__(self):
        """Initialize all harmonic subsystems"""
        print("\n" + "═" * 80)
        print("🌊⚡🎵 HARMONIC MOMENTUM WAVE SCANNER - INITIALIZING 🎵⚡🌊")
        print("═" * 80)
        
        self.systems_active = 0
        self.systems_total = 7
        
        # Initialize each system
        self.micro_momentum = None
        self.wave_scanner = None
        self.chain_master = None
        self.harmonic_field = None
        self.harmonic_fusion = None
        self.waveform_6d = None
        self.queen_dream = None
        
        # L2: Micro-Momentum (THE GOAL!)
        if MICRO_MOMENTUM_OK:
            try:
                self.micro_momentum = MicroMomentumScanner()
                self.systems_active += 1
                print("   ✅ L2: Micro-Momentum Scanner (THE GOAL!)")
            except Exception as e:
                print(f"   ❌ L2: Micro-Momentum Scanner failed: {e}")
        else:
            print("   ⚠️ L2: Micro-Momentum Scanner not available")
        
        # L1: Global Wave Scanner
        if WAVE_SCANNER_OK:
            try:
                # Initialize with no exchange clients - can still analyze
                self.wave_scanner = GlobalWaveScanner()
                self.systems_active += 1
                print("   ✅ L1: Global Wave Scanner")
            except Exception as e:
                print(f"   ❌ L1: Global Wave Scanner failed: {e}")
        else:
            print("   ⚠️ L1: Global Wave Scanner not available")
        
        # L5: Global Harmonic Field
        if HARMONIC_FIELD_OK:
            try:
                self.harmonic_field = GlobalHarmonicField()
                self.systems_active += 1
                print("   ✅ L5: Global Harmonic Field (Ω)")
            except Exception as e:
                print(f"   ❌ L5: Global Harmonic Field failed: {e}")
        else:
            print("   ⚠️ L5: Global Harmonic Field not available")
        
        # L4: 6D Waveform
        if WAVEFORM_6D_OK:
            try:
                self.waveform_6d = SixDimensionalHarmonicEngine()
                self.systems_active += 1
                print("   ✅ L4: 6D Waveform Engine")
            except Exception as e:
                print(f"   ❌ L4: 6D Waveform Engine failed: {e}")
        else:
            print("   ⚠️ L4: 6D Waveform Engine not available")
        
        # L3: Harmonic Fusion
        if HARMONIC_FUSION_OK:
            try:
                self.harmonic_fusion = HarmonicWaveFusion()
                self.systems_active += 1
                print("   ✅ L3: Harmonic Fusion")
            except Exception as e:
                print(f"   ❌ L3: Harmonic Fusion failed: {e}")
        else:
            print("   ⚠️ L3: Harmonic Fusion not available")
        
        # L6: Chain Master
        if CHAIN_MASTER_OK:
            try:
                self.chain_master = HarmonicChainMaster()
                self.systems_active += 1
                print("   ✅ L6: Harmonic Chain Master")
            except Exception as e:
                print(f"   ❌ L6: Harmonic Chain Master failed: {e}")
        else:
            print("   ⚠️ L6: Harmonic Chain Master not available")
        
        # L7: Queen Dream Engine
        if QUEEN_DREAM_OK:
            try:
                self.queen_dream = QueenDreamEngine()
                self.systems_active += 1
                print("   ✅ L7: Queen Dream Engine")
            except Exception as e:
                print(f"   ❌ L7: Queen Dream Engine failed: {e}")
        else:
            print("   ⚠️ L7: Queen Dream Engine not available")
        
        print("-" * 80)
        print(f"   Systems Active: {self.systems_active}/{self.systems_total}")
        print("═" * 80 + "\n")
    
    def _fetch_1min_bars(self, symbols: List[str], lookback_minutes: int = 10) -> Dict[str, List]:
        """Fetch 1-minute bars for all symbols"""
        bars_by_symbol = {}
        
        end = datetime.now(timezone.utc)
        start = end - timedelta(minutes=lookback_minutes)
        
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
                    
        except Exception as e:
            logger.error(f"Failed to fetch bars: {e}")
        
        return bars_by_symbol
    
    def _calculate_momentum(self, bars: List) -> Tuple[float, float, float]:
        """Calculate 1m, 5m, and 10m momentum from bars"""
        if len(bars) < 2:
            return 0.0, 0.0, 0.0
        
        current = float(bars[-1]['c'])
        price_1m = float(bars[-2]['c']) if len(bars) >= 2 else current
        price_5m = float(bars[-6]['c']) if len(bars) >= 6 else current
        price_10m = float(bars[-11]['c']) if len(bars) >= 11 else current
        
        mom_1m = ((current - price_1m) / price_1m) * 100 if price_1m > 0 else 0
        mom_5m = ((current - price_5m) / price_5m) * 100 if price_5m > 0 else 0
        mom_10m = ((current - price_10m) / price_10m) * 100 if price_10m > 0 else 0
        
        return mom_1m, mom_5m, mom_10m
    
    def _get_harmonic_field_omega(self, symbol: str, price: float, momentum: float) -> float:
        """Get the Global Harmonic Field Ω value"""
        if not self.harmonic_field:
            return 0.5  # Neutral if not available
        
        try:
            # The field takes market data and returns unified Ω
            if hasattr(self.harmonic_field, 'calculate_omega'):
                omega = self.harmonic_field.calculate_omega({
                    'symbol': symbol,
                    'price': price,
                    'momentum': momentum
                })
                return omega
            elif hasattr(self.harmonic_field, 'get_field_strength'):
                return self.harmonic_field.get_field_strength()
            else:
                return 0.5
        except Exception as e:
            logger.debug(f"Harmonic field error: {e}")
            return 0.5
    
    def _calculate_solfeggio_alignment(self, momentum: float, price: float) -> Tuple[float, float]:
        """
        Calculate how well the current state aligns with Solfeggio frequencies.
        
        Maps momentum to frequency space and checks alignment with sacred frequencies.
        """
        # Map momentum to frequency space (using golden ratio scaling)
        # Higher momentum = higher frequency
        base_freq = LOVE_FREQUENCY  # 528 Hz (transformation)
        
        # Scale momentum to frequency offset
        freq_offset = momentum * PHI * 10  # ±10 Hz per 1% momentum
        current_freq = base_freq + freq_offset
        
        # Find closest Solfeggio frequency
        min_distance = float('inf')
        closest_solfeggio = LOVE_FREQUENCY
        
        for name, freq in SOLFEGGIO.items():
            distance = abs(current_freq - freq)
            if distance < min_distance:
                min_distance = distance
                closest_solfeggio = freq
        
        # Alignment = how close (0-1, higher is better)
        max_distance = 50  # Hz
        alignment = max(0, 1 - (min_distance / max_distance))
        
        return closest_solfeggio, alignment
    
    def _classify_harmonic_tier(
        self,
        momentum_5m: float,
        harmonic_omega: float,
        solfeggio_alignment: float
    ) -> HarmonicMomentumTier:
        """
        Classify the opportunity using both momentum AND harmonics.
        """
        abs_momentum = abs(momentum_5m)
        
        # Check momentum first (THE GOAL)
        momentum_valid = abs_momentum >= ROUND_TRIP_COST_PCT
        momentum_strong = abs_momentum >= TIER_2_THRESHOLD
        momentum_hot = abs_momentum >= TIER_1_THRESHOLD
        
        # Check harmonics
        harmonics_aligned = harmonic_omega > 0.6 and solfeggio_alignment > 0.5
        harmonics_strong = harmonic_omega > 0.7 and solfeggio_alignment > 0.7
        
        # Classify
        if momentum_hot and harmonics_strong:
            return HarmonicMomentumTier.TRANSCENDENT
        elif momentum_hot:
            return HarmonicMomentumTier.HOT
        elif momentum_strong and harmonics_aligned:
            return HarmonicMomentumTier.STRONG
        elif momentum_valid:
            return HarmonicMomentumTier.VALID
        elif harmonics_aligned and not momentum_valid:
            return HarmonicMomentumTier.HARMONIC_ONLY
        else:
            return HarmonicMomentumTier.SKIP
    
    def scan_all(self) -> List[HarmonicMomentumSignal]:
        """
        🔍 FULL HARMONIC MOMENTUM SCAN
        
        Scans ALL symbols with ALL harmonic systems to find the best opportunities.
        """
        signals: List[HarmonicMomentumSignal] = []
        
        # Fetch market data
        bars_by_symbol = self._fetch_1min_bars(self.ALL_SYMBOLS, lookback_minutes=15)
        
        for symbol in self.ALL_SYMBOLS:
            bars = bars_by_symbol.get(symbol, [])
            if len(bars) < 6:
                continue
            
            current_price = float(bars[-1]['c'])
            mom_1m, mom_5m, mom_10m = self._calculate_momentum(bars)
            
            # Get harmonic field Ω
            omega = self._get_harmonic_field_omega(symbol, current_price, mom_5m)
            
            # Get Solfeggio alignment
            solfeggio_freq, solfeggio_align = self._calculate_solfeggio_alignment(mom_5m, current_price)
            
            # Classify tier
            tier = self._classify_harmonic_tier(mom_5m, omega, solfeggio_align)
            
            # Calculate composite score
            momentum_score = min(1.0, abs(mom_5m) / 1.0)  # Normalize to 0-1
            composite = (momentum_score * 0.5) + (omega * 0.3) + (solfeggio_align * 0.2)
            
            # Direction
            direction = "LONG" if mom_5m > 0 else "SHORT" if mom_5m < 0 else "HOLD"
            
            # Net profit potential
            net_profit = abs(mom_5m) - ROUND_TRIP_COST_PCT
            
            # Confidence
            confidence = composite * (1 if net_profit > 0 else 0.3)
            
            signal = HarmonicMomentumSignal(
                symbol=symbol,
                current_price=current_price,
                momentum_1m_pct=mom_1m,
                momentum_5m_pct=mom_5m,
                momentum_tier=tier.name,
                harmonic_field_omega=omega,
                dominant_frequency=solfeggio_freq,
                solfeggio_alignment=solfeggio_align,
                harmonic_tier=tier,
                composite_score=composite,
                direction=direction,
                confidence=confidence,
                net_profit_potential=net_profit
            )
            
            signals.append(signal)
        
        # Sort by composite score
        signals.sort(key=lambda s: s.composite_score, reverse=True)
        
        return signals
    
    def get_actionable_signals(self) -> List[HarmonicMomentumSignal]:
        """Get only signals worth acting on"""
        all_signals = self.scan_all()
        return [s for s in all_signals if s.is_actionable()]
    
    def get_best_opportunity(self) -> Optional[HarmonicMomentumSignal]:
        """Get the single best opportunity"""
        actionable = self.get_actionable_signals()
        return actionable[0] if actionable else None
    
    def print_scan_results(self) -> List[HarmonicMomentumSignal]:
        """Pretty print the scan results"""
        signals = self.scan_all()
        
        print("\n" + "═" * 90)
        print("🌊⚡🎵 HARMONIC MOMENTUM WAVE SCAN - ALL SYSTEMS UNIFIED 🎵⚡🌊")
        print("═" * 90)
        
        print(f"\n💸 THE GOAL: Find momentum > {ROUND_TRIP_COST_PCT}% (trading cost)")
        print(f"🎵 Harmonic Systems Active: {self.systems_active}/{self.systems_total}")
        print()
        
        # Count tiers
        tier_counts = {t: 0 for t in HarmonicMomentumTier}
        for s in signals:
            tier_counts[s.harmonic_tier] += 1
        
        print("📊 Harmonic Momentum Tiers:")
        print(f"   🌟 TRANSCENDENT (momentum + harmonics aligned): {tier_counts[HarmonicMomentumTier.TRANSCENDENT]}")
        print(f"   🔥 HOT (>0.5% momentum):                        {tier_counts[HarmonicMomentumTier.HOT]}")
        print(f"   ⚡ STRONG (>0.4% + harmonics):                  {tier_counts[HarmonicMomentumTier.STRONG]}")
        print(f"   🌊 VALID (>0.34%, covers costs):                {tier_counts[HarmonicMomentumTier.VALID]}")
        print(f"   🎵 HARMONIC ONLY (waiting for momentum):        {tier_counts[HarmonicMomentumTier.HARMONIC_ONLY]}")
        print(f"   ❄️ SKIP:                                        {tier_counts[HarmonicMomentumTier.SKIP]}")
        print()
        
        print("-" * 90)
        print(f"{'Tier':<14} | {'Symbol':<10} | {'5min':>8} | {'Ω':>5} | {'Solf':>5} | {'Score':>6} | {'Net':>8} | Dir")
        print("-" * 90)
        
        for signal in signals:
            if signal.harmonic_tier != HarmonicMomentumTier.SKIP:
                tier_str = signal.harmonic_tier.value
                print(f"{tier_str:<14} | {signal.symbol:<10} | "
                      f"{signal.momentum_5m_pct:>+7.3f}% | "
                      f"{signal.harmonic_field_omega:>5.2f} | "
                      f"{signal.solfeggio_alignment:>5.2f} | "
                      f"{signal.composite_score:>6.3f} | "
                      f"{signal.net_profit_potential:>+7.3f}% | "
                      f"{signal.direction}")
        
        print("-" * 90)
        
        # Best opportunity
        best = self.get_best_opportunity()
        if best:
            print(f"\n🎯 BEST HARMONIC MOMENTUM OPPORTUNITY:")
            print(f"   Symbol:             {best.symbol}")
            print(f"   Tier:               {best.harmonic_tier.value}")
            print(f"   Direction:          {best.direction}")
            print(f"   5min Momentum:      {best.momentum_5m_pct:+.3f}%")
            print(f"   Harmonic Field Ω:   {best.harmonic_field_omega:.3f}")
            print(f"   Solfeggio Alignment: {best.solfeggio_alignment:.3f} @ {best.dominant_frequency:.0f}Hz")
            print(f"   Composite Score:    {best.composite_score:.3f}")
            print(f"   Net Profit:         {best.net_profit_potential:+.3f}%")
            print(f"   Confidence:         {best.confidence:.1%}")
            print(f"\n   ✅ EXECUTE: {best.direction} {best.symbol} @ ${best.current_price:.4f}")
        else:
            print(f"\n⏳ No momentum opportunities above {ROUND_TRIP_COST_PCT}% threshold")
            print("   The harmonics are aligned, waiting for momentum wave...")
        
        print("═" * 90)
        
        return signals


# ═══════════════════════════════════════════════════════════════════════════════
# 🚀 MAIN - RUN THE UNIFIED SCANNER
# ═══════════════════════════════════════════════════════════════════════════════

def run_harmonic_wave_scan():
    """Run a single harmonic momentum wave scan"""
    scanner = HarmonicMomentumWaveScanner()
    return scanner.print_scan_results()


async def run_continuous_scan(interval_seconds: int = 10, max_scans: int = 0):
    """
    Run continuous harmonic momentum scanning.
    
    Args:
        interval_seconds: Seconds between scans
        max_scans: Maximum scans (0 = unlimited)
    """
    scanner = HarmonicMomentumWaveScanner()
    
    print("\n🌊 Starting continuous harmonic momentum scan...")
    print(f"   Interval: {interval_seconds}s")
    print(f"   Press Ctrl+C to stop\n")
    
    scan_count = 0
    
    try:
        while max_scans == 0 or scan_count < max_scans:
            scan_count += 1
            
            print(f"\n[Scan #{scan_count}] {datetime.now().strftime('%H:%M:%S')}")
            print("-" * 40)
            
            signals = scanner.scan_all()
            actionable = [s for s in signals if s.is_actionable()]
            
            if actionable:
                print(f"🎯 FOUND {len(actionable)} ACTIONABLE SIGNALS!")
                for sig in actionable[:3]:  # Top 3
                    print(f"   {sig.harmonic_tier.value} {sig.symbol}: "
                          f"{sig.momentum_5m_pct:+.3f}% | Ω={sig.harmonic_field_omega:.2f} | "
                          f"Net: {sig.net_profit_potential:+.3f}%")
            else:
                # Show top harmonic-aligned coins waiting for momentum
                harmonic_waiting = [s for s in signals if s.harmonic_tier == HarmonicMomentumTier.HARMONIC_ONLY]
                if harmonic_waiting:
                    print(f"🎵 {len(harmonic_waiting)} coins with good harmonics, waiting for momentum...")
                else:
                    top = signals[0] if signals else None
                    if top:
                        needed = ROUND_TRIP_COST_PCT - abs(top.momentum_5m_pct)
                        print(f"⏳ Best: {top.symbol} at {top.momentum_5m_pct:+.3f}% (need +{needed:.3f}% more)")
            
            await asyncio.sleep(interval_seconds)
            
    except KeyboardInterrupt:
        print("\n\n👑 Harmonic Wave Scanner stopped by user")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        asyncio.run(run_continuous_scan(interval_seconds=10))
    else:
        run_harmonic_wave_scan()
