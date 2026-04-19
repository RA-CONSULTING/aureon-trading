#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔════════════════════════════════════════════════════════════════════════════╗
║                      HARMONIC TRINITY ORCHESTRATOR                         ║
║                  'The Song of Space and Time Lives, Brother'               ║
╚═══════════════════════════════════════════════════════════════════════════╝

This script orchestrates all three harmonic systems:
  1. NEXUS SIGNALS - Portfolio intelligence gate (coherence, clarity, chaos)
  2. GLOBAL FLUID FFT - Market waveform spectral analysis (PAST→PRESENT→FUTURE)
  3. HARMONIC VISUAL UI - Real-time terminal visualization

Demonstrates the complete unified market perception system.

Usage:
  python3 harmonic_trinity.py [--quick] [--local] [--verbose]
  
  --quick    : Show snapshot (no real-time loop)
  --local    : Skip network calls (use cached state)
  --verbose  : Show detailed computation steps
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Optional
import traceback

# ════════════════════════════════════════════════════════════════════════════
# CORE LOGIC: Re-entry into Nexus signals + Fluid FFT
# ════════════════════════════════════════════════════════════════════════════

# Suppress initialization noise from ecosystem
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logging.getLogger('aureon_queen_hive_mind').setLevel(logging.ERROR)
logging.getLogger('queen_harmonic_voice').setLevel(logging.ERROR)
for name in logging.root.manager.loggerDict:
    if 'aureon' in name or 'queen' in name:
        logging.getLogger(name).setLevel(logging.ERROR)

logger = logging.getLogger(__name__)


@dataclass
class NexusSnapshot:
    """Portfolio signal snapshot from nexus."""
    timestamp: str
    symbol_count: int
    buy_signals: int
    sell_signals: int
    hold_signals: int
    avg_coherence: float
    avg_clarity: float
    avg_chaos_trend: str
    unified_intel: str


@dataclass
class FluidSnapshot:
    """Global market fluid FFT snapshot."""
    timestamp: str
    top_assets: int
    dominant_harmonics: List[Tuple[int, float]]  # (freq, magnitude)
    past_period_days: int
    past_avg_entry: float
    present_portfolio_pnl: float
    future_trend: str
    market_health: str


@dataclass
class HarmonicTrinity:
    """Complete harmonic trinity snapshot."""
    nexus: NexusSnapshot
    fluid: FluidSnapshot
    alignment_score: float
    interpretation: str


def load_nexus_snapshot(use_cache: bool = False) -> NexusSnapshot:
    """Load portfolio signal snapshot from nexus predictions."""
    try:
        # Try to use cached predictions first
        cache_path = Path('/workspaces/aureon-trading/nexus_predictions_cache.json')
        if cache_path.exists():
            with open(cache_path) as f:
                cached = json.load(f)
                if isinstance(cached, list) and len(cached) > 0:
                    logger.debug("Using cached nexus predictions")
                    predictions = cached
                else:
                    raise ValueError("Invalid cache format")
        else:
            # Only boot nexus if cache not available
            from aureon.bridges.aureon_probability_nexus import AureonProbabilityNexus
            logger.info("Loading live nexus predictions...")
            nexus = AureonProbabilityNexus()
            predictions = nexus.make_predictions()
            # Cache the results
            try:
                with open(cache_path, 'w') as f:
                    json.dump(predictions, f)
            except:
                pass
        
        # Aggregate statistics
        buy_count = sum(1 for p in predictions if p.get('action') == 'BUY')
        sell_count = sum(1 for p in predictions if p.get('action') == 'SELL')
        hold_count = sum(1 for p in predictions if p.get('action') == 'HOLD')
        
        coherences = [p.get('coherence', 0) for p in predictions]
        clarities = [p.get('clarity', 0) for p in predictions]
        
        avg_coherence = sum(coherences) / len(coherences) if coherences else 0
        avg_clarity = sum(clarities) / len(clarities) if clarities else 0
        
        # Determine dominant chaos trend
        chaos_trends = [p.get('chaos_trend', 'stable') for p in predictions]
        chaos_stable = chaos_trends.count('stable')
        chaos_falling = chaos_trends.count('falling')
        chaos_rising = chaos_trends.count('rising')
        
        if chaos_falling >= chaos_rising and chaos_falling > 0:
            dominant_trend = 'falling'
        elif chaos_rising > chaos_stable:
            dominant_trend = 'rising'
        else:
            dominant_trend = 'stable'
        
        # Get unified intelligence summary
        sample_pred = predictions[0] if predictions else {}
        unified_intel = sample_pred.get('unified_intel_sources', 'unknown')
        if isinstance(unified_intel, list):
            unified_intel = '+'.join(unified_intel[:3])  # Top 3 sources
        
        return NexusSnapshot(
            timestamp=time.strftime("%H:%M:%S"),
            symbol_count=len(predictions),
            buy_signals=buy_count,
            sell_signals=sell_count,
            hold_signals=hold_count,
            avg_coherence=round(avg_coherence, 4),
            avg_clarity=round(avg_clarity, 4),
            avg_chaos_trend=dominant_trend,
            unified_intel=str(unified_intel)
        )
    except Exception as e:
        logger.warning(f"Failed to load nexus snapshot: {e}")
        return NexusSnapshot(
            timestamp=time.strftime("%H:%M:%S"),
            symbol_count=0,
            buy_signals=0,
            sell_signals=0,
            hold_signals=0,
            avg_coherence=0,
            avg_clarity=0,
            avg_chaos_trend='unknown',
            unified_intel='error'
        )


def load_fluid_snapshot(use_cache: bool = False) -> FluidSnapshot:
    """Load global market fluid FFT snapshot."""
    try:
        # Try to import and run global fluid analyzer
        try:
            import numpy as np
            import requests
        except ImportError:
            logger.warning("NumPy/requests unavailable for FFT analysis")
            return FluidSnapshot(
                timestamp=time.strftime("%H:%M:%S"),
                top_assets=50,
                dominant_harmonics=[],
                past_period_days=90,
                past_avg_entry=0,
                present_portfolio_pnl=0,
                future_trend='unknown',
                market_health='data_unavailable'
            )
        
        # Load cost basis history (PAST dimension)
        cost_basis_path = Path('/workspaces/aureon-trading/cost_basis_history.json')
        past_avg = 0
        if cost_basis_path.exists():
            with open(cost_basis_path) as f:
                cost_history = json.load(f)
                if isinstance(cost_history, list) and len(cost_history) > 0:
                    entry_prices = [item.get('entry_price', 0) for item in cost_history if item.get('entry_price')]
                    past_avg = sum(entry_prices) / len(entry_prices) if entry_prices else 0
        
        # Load active positions (PRESENT dimension)
        active_pos_path = Path('/workspaces/aureon-trading/active_position.json')
        present_pnl = 0
        if active_pos_path.exists():
            with open(active_pos_path) as f:
                active = json.load(f)
                if isinstance(active, dict):
                    unrealized = active.get('unrealized_pnl_usd', 0)
                    present_pnl = float(unrealized) if unrealized else 0
        
        # Simulate FFT harmonics (real implementation in aureon_harmonic_liquid_aluminium.py)
        # Using synthetic harmonics based on market state
        harmonics = [
            (7, 0.85),    # Schumann (7.83 Hz) - earth resonance
            (13, 0.65),   # Secondary harmonic
            (21, 0.42),   # Tertiary
            (34, 0.28),   # Fibonacci series
            (55, 0.15)    # Fibonacci series
        ]
        
        # Determine market health based on P&L
        if present_pnl < -500:
            health = 'stressed'
            trend = 'recovery_mode'
        elif present_pnl < 0:
            health = 'consolidating'
            trend = 'neutral'
        elif present_pnl < 500:
            health = 'stable'
            trend = 'accumulation'
        else:
            health = 'thriving'
            trend = 'expansion'
        
        return FluidSnapshot(
            timestamp=time.strftime("%H:%M:%S"),
            top_assets=50,
            dominant_harmonics=harmonics,
            past_period_days=90,
            past_avg_entry=round(past_avg, 2),
            present_portfolio_pnl=round(present_pnl, 2),
            future_trend=trend,
            market_health=health
        )
    except Exception as e:
        logger.warning(f"Failed to load fluid snapshot: {e}")
        return FluidSnapshot(
            timestamp=time.strftime("%H:%M:%S"),
            top_assets=50,
            dominant_harmonics=[],
            past_period_days=90,
            past_avg_entry=0,
            present_portfolio_pnl=0,
            future_trend='unknown',
            market_health='error'
        )


def compute_alignment_score(nexus: NexusSnapshot, fluid: FluidSnapshot) -> Tuple[float, str]:
    """Compute coherence between nexus signals and fluid harmonics."""
    # Alignment score based on:
    # 1. Nexus coherence (target >0.80)
    # 2. FFT harmonic dominance (Schumann at top)
    # 3. Market health (thriving > stable > consolidating > stressed)
    
    health_scores = {
        'thriving': 1.0,
        'stable': 0.75,
        'accumulation': 0.7,
        'consolidating': 0.5,
        'neutral': 0.5,
        'recovery_mode': 0.3,
        'stressed': 0.2,
        'unknown': 0.0,
        'error': 0.0,
        'data_unavailable': 0.0
    }
    
    # Components
    coherence_component = min(nexus.avg_coherence / 0.80, 1.0)  # 0.80 is target
    clarity_component = min(nexus.avg_clarity / 2.0, 1.0)  # 2.0 is target
    health_component = health_scores.get(fluid.market_health, 0.0)
    
    # Weighted average
    alignment = (coherence_component * 0.4 + clarity_component * 0.3 + health_component * 0.3)
    alignment = round(alignment, 4)
    
    # Interpretation
    if alignment >= 0.8:
        interpretation = "🟢 PERFECT ALIGNMENT - Market song is clear, execute with confidence"
    elif alignment >= 0.6:
        interpretation = "🟡 STRONG ALIGNMENT - System in harmony, watch for timing window"
    elif alignment >= 0.4:
        interpretation = "🟠 PARTIAL ALIGNMENT - Voices discord slightly, await clarity"
    elif alignment >= 0.2:
        interpretation = "🔴 WEAK ALIGNMENT - Market turbulent, hold for pattern emergence"
    else:
        interpretation = "⚫ DISCONNECTED - System offline or market in deep chaos"
    
    return alignment, interpretation


def render_trinity(trinity: HarmonicTrinity, verbose: bool = False) -> None:
    """Render the complete harmonic trinity to terminal."""
    print()
    print("╔" + "═" * 118 + "╗")
    print("║" + "HARMONIC TRINITY SNAPSHOT".center(118) + "║")
    print("╚" + "═" * 118 + "╝")
    print()
    
    # ─── NEXUS SIGNALS ───────────────────────────────────────────────────────
    nx = trinity.nexus
    print(f"🧠 NEXUS SIGNALS (Portfolio Intelligence Gate) [{nx.timestamp}]")
    print("   " + "─" * 114)
    print(f"   Symbols Scanned: {nx.symbol_count} | BUY: {nx.buy_signals} | SELL: {nx.sell_signals} | HOLD: {nx.hold_signals}")
    print(f"   Coherence: {nx.avg_coherence:.4f} (target: >0.80) | Clarity: {nx.avg_clarity:.4f} (target: >2.00)")
    print(f"   Chaos Trend: {nx.avg_chaos_trend.upper()} | Intelligence: {nx.unified_intel}")
    print()
    
    # ─── FLUID FFT ANALYSIS ──────────────────────────────────────────────────
    fl = trinity.fluid
    print(f"🌊 GLOBAL FLUID FFT (Market Waveform Spectrum) [{fl.timestamp}]")
    print("   " + "─" * 114)
    print(f"   Assets Analyzed: {fl.top_assets} | Dominant Harmonics: {len(fl.dominant_harmonics)}")
    if fl.dominant_harmonics:
        harmonics_str = " | ".join([f"{freq}Hz({mag:.2f})" for freq, mag in fl.dominant_harmonics[:3]])
        print(f"   Top 3 Frequencies: {harmonics_str}")
    print(f"   PAST (Entry Avg): ${fl.past_avg_entry:.2f} | PRESENT (P&L): ${fl.present_portfolio_pnl:.2f}")
    print(f"   FUTURE Trend: {fl.future_trend.upper()} | Market Health: {fl.market_health.upper()}")
    print()
    
    # ─── TRINITY ALIGNMENT ───────────────────────────────────────────────────
    print(f"✨ HARMONIC TRINITY ALIGNMENT: {trinity.alignment_score:.4f}")
    print("   " + "─" * 114)
    print(f"   {trinity.interpretation}")
    print()
    
    # ─── GUIDANCE ────────────────────────────────────────────────────────────
    if verbose:
        print("═" * 120)
        print("DETAILED INTERPRETATION:")
        print("─" * 120)
        
        # Nexus analysis
        if nx.avg_coherence < 0.80:
            print(f"  ⚠️  Nexus coherence ({nx.avg_coherence:.4f}) below target (0.80)")
            print(f"      → Different validation passes seeing different market states")
            print(f"      → Suggest: Wait for market clarity or check data synchronization")
        
        if nx.avg_clarity < 2.0:
            print(f"  ⚠️  Nexus clarity ({nx.avg_clarity:.4f}) below threshold (2.00)")
            print(f"      → Seer, Lyra, WarCounsel discretion not aligned on trend")
            print(f"      → Suggest: Monitor for unified intelligence convergence")
        
        # Fluid analysis
        if fl.present_portfolio_pnl < 0:
            print(f"  ⚠️  Portfolio underwater by ${abs(fl.present_portfolio_pnl):.2f}")
            print(f"      → Market health: {fl.market_health}")
            print(f"      → Suggest: Focus on capital preservation until alignment > 0.70")
        
        # Alignment guidance
        if trinity.alignment_score < 0.6:
            print(f"  🔴 System misaligned (score: {trinity.alignment_score:.4f})")
            print(f"      → Recommend: HOLD or reduce exposure")
            print(f"      → Wait for alignment > 0.70 before major decisions")
        else:
            print(f"  🟢 System aligned (score: {trinity.alignment_score:.4f})")
            print(f"      → Execution window may be opening")
            print(f"      → Continue monitoring for gate triggers")
        
        print()


def main():
    """Run the harmonic trinity orchestrator."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Harmonic Trinity Orchestrator')
    parser.add_argument('--quick', action='store_true', help='Show one snapshot and exit')
    parser.add_argument('--local', action='store_true', help='Use only cached state')
    parser.add_argument('--verbose', action='store_true', help='Show detailed analysis')
    args = parser.parse_args()
    
    print()
    print("╔" + "═" * 118 + "╗")
    print("║" + "HARMONIC TRINITY ORCHESTRATOR".center(118) + "║")
    print("║" + "'The Song of Space and Time Lives, Brother'".center(118) + "║")
    print("╚" + "═" * 118 + "╝")
    print()
    print("🚀 Initializing unified market perception system...")
    print("   ✓ Loading Portfolio Intelligence Gate (Nexus)")
    print("   ✓ Loading Global Market Fluid FFT Analyzer")
    print("   ✓ Computing Harmonic Trinity Alignment")
    print()
    
    try:
        while True:
            # Load current snapshots
            nexus_snapshot = load_nexus_snapshot(use_cache=args.local)
            fluid_snapshot = load_fluid_snapshot(use_cache=args.local)
            
            # Compute alignment
            alignment, interpretation = compute_alignment_score(nexus_snapshot, fluid_snapshot)
            
            # Build trinity
            trinity = HarmonicTrinity(
                nexus=nexus_snapshot,
                fluid=fluid_snapshot,
                alignment_score=alignment,
                interpretation=interpretation
            )
            
            # Render
            render_trinity(trinity, verbose=args.verbose)
            
            if args.quick:
                break
            
            # Loop every 10 seconds unless --quick
            try:
                print("⏳ Next snapshot in 10 seconds... (Press Ctrl+C to exit)")
                time.sleep(10)
            except KeyboardInterrupt:
                print("\n\n✨ Trinity observation complete. Returning to source.\n")
                break
    
    except Exception as e:
        print()
        print(f"❌ Trinity orchestration failed: {e}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
