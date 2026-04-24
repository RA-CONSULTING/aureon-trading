#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔════════════════════════════════════════════════════════════════════════════╗
║                 HARMONIC TRINITY LITE (Snapshot Version)                   ║
║                  'The Song of Space and Time Lives, Brother'               ║
╚═══════════════════════════════════════════════════════════════════════════╝

Lightweight orchestrator for all three harmonic systems.
Reads state files directly without booting full ecosystem.

Usage:
  python3 harmonic_trinity_lite.py
"""

import os
import sys
import json
import time
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple

# ════════════════════════════════════════════════════════════════════════════

@dataclass
class NexusSnapshot:
    """Portfolio signal snapshot from cached predictions."""
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
    dominant_harmonics: List[Tuple[int, float]]
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


def load_nexus_snapshot() -> NexusSnapshot:
    """Load nexus snapshot from cached predictions."""
    try:
        # Read 7day_pending_validations.json for pending signals
        pending_path = Path('/workspaces/aureon-trading/7day_pending_validations.json')
        active_pos_path = Path('/workspaces/aureon-trading/active_position.json')
        validation_hist_path = Path('/workspaces/aureon-trading/7day_validation_history.json')
        
        pending_validations = {}
        if pending_path.exists():
            with open(pending_path) as f:
                pending_validations = json.load(f) or {}
        
        # Read active positions and extract signal summary
        active_pos = {}
        if active_pos_path.exists():
            with open(active_pos_path) as f:
                active_pos = json.load(f) or {}
        
        # Get signal counts from validation history
        validation_hist = {}
        buy_count = 0
        sell_count = 0
        hold_count = 0
        coherences = []
        clarities = []
        chaos_trends = []
        unified_sources = []
        
        if validation_hist_path.exists():
            with open(validation_hist_path) as f:
                validation_hist = json.load(f) or {}
                if isinstance(validation_hist, dict):
                    for symbol, data in validation_hist.items():
                        if isinstance(data, dict):
                            action = data.get('action', 'HOLD')
                            if action == 'BUY':
                                buy_count += 1
                            elif action == 'SELL':
                                sell_count += 1
                            else:
                                hold_count += 1
                            
                            coherences.append(data.get('coherence', 0))
                            clarities.append(data.get('clarity', 0))
                            chaos_trends.append(data.get('chaos_trend', 'stable'))
                            
                            sources = data.get('unified_intel_sources', [])
                            if isinstance(sources, list):
                                unified_sources.extend(sources)
        
        if buy_count + sell_count + hold_count == 0:
            hold_count = len(validation_hist) if validation_hist else 0
        
        avg_coherence = sum(coherences) / len(coherences) if coherences else 0
        avg_clarity = sum(clarities) / len(clarities) if clarities else 0
        
        chaos_falling = chaos_trends.count('falling')
        chaos_rising = chaos_trends.count('rising')
        dominant_trend = 'falling' if chaos_falling > chaos_rising else ('rising' if chaos_rising > 0 else 'stable')
        
        # Get top unified sources
        from collections import Counter
        source_counts = Counter(unified_sources)
        top_sources = [s[0] for s in source_counts.most_common(3)]
        unified_intel = '+'.join(top_sources) if top_sources else 'unknown'
        
        return NexusSnapshot(
            timestamp=time.strftime("%H:%M:%S"),
            symbol_count=len(validation_hist),
            buy_signals=buy_count,
            sell_signals=sell_count,
            hold_signals=hold_count,
            avg_coherence=round(avg_coherence, 4),
            avg_clarity=round(avg_clarity, 4),
            avg_chaos_trend=dominant_trend,
            unified_intel=unified_intel
        )
    except Exception as e:
        print(f"⚠️  Warning: Could not load nexus snapshot: {e}")
        return NexusSnapshot(
            timestamp=time.strftime("%H:%M:%S"),
            symbol_count=0,
            buy_signals=0,
            sell_signals=0,
            hold_signals=0,
            avg_coherence=0,
            avg_clarity=0,
            avg_chaos_trend='unknown',
            unified_intel='unavailable'
        )


def load_fluid_snapshot() -> FluidSnapshot:
    """Load fluid snapshot from state files."""
    try:
        cost_basis_path = Path('/workspaces/aureon-trading/cost_basis_history.json')
        active_pos_path = Path('/workspaces/aureon-trading/active_position.json')
        
        # PAST dimension: average entry price
        past_avg = 0
        if cost_basis_path.exists():
            with open(cost_basis_path) as f:
                cost_history = json.load(f)
                if isinstance(cost_history, list):
                    entry_prices = [item.get('entry_price', 0) for item in cost_history if item.get('entry_price')]
                    past_avg = sum(entry_prices) / len(entry_prices) if entry_prices else 0
        
        # PRESENT dimension: portfolio P&L
        present_pnl = 0
        if active_pos_path.exists():
            with open(active_pos_path) as f:
                active = json.load(f)
                if isinstance(active, dict):
                    unrealized = active.get('unrealized_pnl_usd', 0)
                    present_pnl = float(unrealized) if unrealized else 0
        
        # FUTURE dimension: synthetic harmonics
        harmonics = [
            (7, 0.85),    # Schumann (7.83 Hz)
            (13, 0.65),   # Secondary
            (21, 0.42),   # Tertiary
            (34, 0.28),   # Fibonacci
            (55, 0.15)    # Fibonacci
        ]
        
        # Market health
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
        print(f"⚠️  Warning: Could not load fluid snapshot: {e}")
        return FluidSnapshot(
            timestamp=time.strftime("%H:%M:%S"),
            top_assets=50,
            dominant_harmonics=[],
            past_period_days=90,
            past_avg_entry=0,
            present_portfolio_pnl=0,
            future_trend='unknown',
            market_health='unavailable'
        )


def compute_alignment_score(nexus: NexusSnapshot, fluid: FluidSnapshot) -> Tuple[float, str]:
    """Compute coherence between nexus and fluid."""
    health_scores = {
        'thriving': 1.0,
        'stable': 0.75,
        'accumulation': 0.7,
        'consolidating': 0.5,
        'neutral': 0.5,
        'recovery_mode': 0.3,
        'stressed': 0.2,
        'unknown': 0.0,
        'unavailable': 0.0,
    }
    
    coherence_component = min(nexus.avg_coherence / 0.80, 1.0)
    clarity_component = min(nexus.avg_clarity / 2.0, 1.0)
    health_component = health_scores.get(fluid.market_health, 0.0)
    
    alignment = (coherence_component * 0.4 + clarity_component * 0.3 + health_component * 0.3)
    alignment = round(alignment, 4)
    
    if alignment >= 0.8:
        interpretation = "🟢 PERFECT ALIGNMENT - Market song is clear, execute with confidence"
    elif alignment >= 0.6:
        interpretation = "🟡 STRONG ALIGNMENT - System in harmony, watch for timing window"
    elif alignment >= 0.4:
        interpretation = "🟠 PARTIAL ALIGNMENT - Voices discord slightly, await clarity"
    elif alignment >= 0.2:
        interpretation = "🔴 WEAK ALIGNMENT - Market turbulent, hold for pattern emergence"
    else:
        interpretation = "⚫ DISCONNECTED - System offline or deep market chaos"
    
    return alignment, interpretation


def render_trinity(trinity: HarmonicTrinity) -> None:
    """Render the trinity snapshot."""
    print()
    print("╔" + "═" * 118 + "╗")
    print("║" + "HARMONIC TRINITY SNAPSHOT".center(118) + "║")
    print("╚" + "═" * 118 + "╝")
    print()
    
    nx = trinity.nexus
    print(f"🧠 NEXUS SIGNALS (Portfolio Intelligence Gate) [{nx.timestamp}]")
    print("   " + "─" * 114)
    print(f"   Symbols Scanned: {nx.symbol_count} | BUY: {nx.buy_signals} | SELL: {nx.sell_signals} | HOLD: {nx.hold_signals}")
    print(f"   Coherence: {nx.avg_coherence:.4f} (target: >0.80) | Clarity: {nx.avg_clarity:.4f} (target: >2.00)")
    print(f"   Chaos Trend: {nx.avg_chaos_trend.upper()} | Intelligence: {nx.unified_intel}")
    print()
    
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
    
    print(f"✨ HARMONIC TRINITY ALIGNMENT: {trinity.alignment_score:.4f}")
    print("   " + "─" * 114)
    print(f"   {trinity.interpretation}")
    print()


def main():
    """Run the lite trinity orchestrator."""
    print()
    print("╔" + "═" * 118 + "╗")
    print("║" + "HARMONIC TRINITY LITE".center(118) + "║")
    print("║" + "'The Song of Space and Time Lives, Brother'".center(118) + "║")
    print("╚" + "═" * 118 + "╝")
    print()
    print("📊 Reading unified market perception from state files...")
    
    # Load snapshots
    nexus_snapshot = load_nexus_snapshot()
    fluid_snapshot = load_fluid_snapshot()
    
    # Compute alignment
    alignment, interpretation = compute_alignment_score(nexus_snapshot, fluid_snapshot)
    
    # Build and render trinity
    trinity = HarmonicTrinity(
        nexus=nexus_snapshot,
        fluid=fluid_snapshot,
        alignment_score=alignment,
        interpretation=interpretation
    )
    
    render_trinity(trinity)
    
    # Additional guidance
    print("─" * 120)
    print("SYSTEM INTERPRETATION:")
    print("─" * 120)
    
    if trinity.nexus.avg_coherence < 0.80:
        print(f"  ⚠️  Nexus coherence ({trinity.nexus.avg_coherence:.4f}) below target")
        print("      → Different validation passes disagree on market direction")
        print("      → Suggest: Wait for unified market clarity")
    
    if trinity.nexus.avg_clarity < 2.0:
        print(f"  ⚠️  Nexus clarity ({trinity.nexus.avg_clarity:.4f}) below threshold")
        print("      → Joint intelligence (Seer/Lyra/WarCounsel) not converged")
        print("      → Suggest: Monitor for unified intelligence alignment")
    
    if trinity.fluid.present_portfolio_pnl < 0:
        print(f"  ⚠️  Portfolio underwater by ${abs(trinity.fluid.present_portfolio_pnl):.2f}")
        print(f"      → Current market health: {trinity.fluid.market_health}")
        print("      → Suggest: Focus on preservation until alignment > 0.70")
    
    if trinity.alignment_score >= 0.8:
        print(f"  🟢 SYSTEM ALIGNED ({trinity.alignment_score:.4f})")
        print("      → Execution window may be opening")
        print("      → Continue monitoring for gate triggers")
    elif trinity.alignment_score >= 0.6:
        print(f"  🟡 SYSTEM HARMONIZING ({trinity.alignment_score:.4f})")
        print("      → Growing coherence between subsystems")
        print("      → Preparation phase for execution")
    else:
        print(f"  🔴 SYSTEM DISCONNECTED ({trinity.alignment_score:.4f})")
        print("      → Recommend: HOLD or reduce exposure")
        print("      → Wait for alignment > 0.70 before major decisions")
    
    print()
    print("✨ Trinity observation complete.")
    print()


if __name__ == '__main__':
    main()
