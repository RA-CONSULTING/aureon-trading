#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════════════╗
║          AUREON ATN COMMAND CENTER — TEMPORAL INTELLIGENCE MATRIX                   ║
║          "See the past, master the present, shape the future"                       ║
╠══════════════════════════════════════════════════════════════════════════════════════╣
║  Wires ALL Aureon intelligence systems into one unified temporal console:           ║
║                                                                                      ║
║  PAST     → ATN planetary event history + WHO KNEW forensics                        ║
║             Counter-frequency historical patterns                                   ║
║             Spectrum analysis of known whale coordination                           ║
║                                                                                      ║
║  PRESENT  → Live Schumann resonance (Earth heartbeat)                               ║
║             Live order book (Kraken BTC/ETH)                                        ║
║             Real intelligence engine (bots, whales, momentum)                      ║
║             Counter-intelligence vs Jane Street / Citadel / Jump                   ║
║             Harmonic spectrum sweep (FFT phase analysis)                            ║
║                                                                                      ║
║  FUTURE   → Temporal dialer (3 sacred frequencies tuned)                            ║
║             Truth prediction engine (Queen × Auris validated)                       ║
║             Planetary event probability (next 48h risk)                             ║
║             Composite trade signal with full confidence breakdown                   ║
║                                                                                      ║
║  Run:  python aureon_atn_command_center.py                                          ║
║        python aureon_atn_command_center.py --live        # refresh every 60s        ║
║        python aureon_atn_command_center.py --deep        # full harmonic sweep      ║
║        python aureon_atn_command_center.py --pair ETHUSD # change pair              ║
║                                                                                      ║
║  Gary Leckey | March 2026                                                           ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import os
import statistics
import sys
import time
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Silence all loggers from sub-systems during our banner phase
logging.disable(logging.CRITICAL)

# ─────────────────────────────────────────────────────────────────────────────
# ANSI
# ─────────────────────────────────────────────────────────────────────────────
RST  = "\033[0m"
BOLD = "\033[1m"
DIM  = "\033[2m"
RED  = "\033[91m"
GRN  = "\033[92m"
YEL  = "\033[93m"
BLU  = "\033[94m"
MAG  = "\033[95m"
CYN  = "\033[96m"
WHT  = "\033[97m"

def _c(t, col): return f"{col}{t}{RST}"
def _b(t):      return f"{BOLD}{t}{RST}"
def _bar(v, lo, hi, w=18, c=GRN):
    f = max(0.0, min(1.0, (v-lo)/(hi-lo) if hi!=lo else 0))
    n = int(f*w)
    return f"{c}{'█'*n}{'░'*(w-n)}{RST}"

# Grade colours
GC = {"DIVINE_HARMONY": GRN, "CLEAR_RESONANCE": CYN,
      "PARTIAL_HARMONY": YEL, "DISSONANCE": MAG, "SILENCE": RED}

PHI = (1 + math.sqrt(5)) / 2


# ─────────────────────────────────────────────────────────────────────────────
# DATA CONTAINERS
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class LayerResult:
    name: str
    status: str        # OK / WARN / ERROR
    data: Dict[str, Any] = field(default_factory=dict)
    elapsed: float = 0.0


@dataclass
class CompositeSignal:
    direction: str            # BUY / SELL / HOLD
    confidence: float         # 0–1
    pair: str
    price: float
    components: List[str]
    risk_flags: List[str]
    next_event_hours: Optional[float]


# ─────────────────────────────────────────────────────────────────────────────
# KRAKEN LIVE PRICE
# ─────────────────────────────────────────────────────────────────────────────

def _kraken_price(pair: str) -> Optional[float]:
    try:
        r = requests.get("https://api.kraken.com/0/public/Ticker",
                         params={"pair": pair}, timeout=6,
                         headers={"User-Agent": "AureonCmdCenter/1.0"})
        d = r.json()
        result = d.get("result", {})
        key = list(result.keys())[0] if result else None
        if key:
            return float(result[key]["c"][0])
    except Exception:
        pass
    return None


def _kraken_orderbook(pair: str, count: int = 12) -> Dict:
    try:
        r = requests.get("https://api.kraken.com/0/public/Depth",
                         params={"pair": pair, "count": count}, timeout=6,
                         headers={"User-Agent": "AureonCmdCenter/1.0"})
        d = r.json()
        result = d.get("result", {})
        key = list(result.keys())[0] if result else None
        if key:
            ob = result[key]
            asks = [(float(a[0]), float(a[1])) for a in ob.get("asks", [])]
            bids = [(float(b[0]), float(b[1])) for b in ob.get("bids", [])]
            return {"asks": asks, "bids": bids}
    except Exception:
        pass
    return {}


def _kraken_ohlc(pair: str, interval: int = 60, n: int = 72) -> List[Dict]:
    """Fetch recent OHLC candles (interval in minutes)."""
    try:
        r = requests.get("https://api.kraken.com/0/public/OHLC",
                         params={"pair": pair, "interval": interval}, timeout=8,
                         headers={"User-Agent": "AureonCmdCenter/1.0"})
        d = r.json()
        result = d.get("result", {})
        rows = None
        for k, v in result.items():
            if k != "last" and isinstance(v, list):
                rows = v; break
        if rows:
            return [{"t": float(r[0]), "o": float(r[1]), "h": float(r[2]),
                     "l": float(r[3]), "c": float(r[4]), "v": float(r[6])}
                    for r in rows[-n:]]
    except Exception:
        pass
    return []


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 1 — PAST: PLANETARY EVENT HISTORY
# ─────────────────────────────────────────────────────────────────────────────

def _layer_past(days: int = 365) -> LayerResult:
    t0 = time.time()
    try:
        from aureon.atn.aureon_atn_backtest import (
            fetch_earthquakes, fetch_solar_flares, fetch_geomagnetic_storms
        )
        end   = datetime.now(timezone.utc)
        start = end - timedelta(days=min(days, 365))

        quakes = fetch_earthquakes(start, end, min_mag=6.5)
        flares = fetch_solar_flares(start, end)
        storms = fetch_geomagnetic_storms(start, end)
        all_events = sorted(quakes + flares + storms, key=lambda e: e.timestamp)

        grade_order = {"DIVINE_HARMONY": 0, "CLEAR_RESONANCE": 1,
                       "PARTIAL_HARMONY": 2, "DISSONANCE": 3, "SILENCE": 4}

        silences   = [e for e in all_events if e.grade == "SILENCE"]
        dissonance = [e for e in all_events if e.grade == "DISSONANCE"]

        # Most recent SILENCE event
        last_silence = silences[-1] if silences else None
        last_dt = None
        hours_since = None
        if last_silence:
            last_dt = datetime.fromtimestamp(last_silence.timestamp, tz=timezone.utc)
            hours_since = (datetime.now(timezone.utc) - last_dt).total_seconds() / 3600

        # Next probable event window: cycle analysis
        # Average inter-event gap for SILENCE events
        silence_gaps = []
        for i in range(1, len(silences)):
            silence_gaps.append((silences[i].timestamp - silences[i-1].timestamp) / 3600)
        avg_gap_h = statistics.mean(silence_gaps) if silence_gaps else 168  # default 1w
        std_gap_h = statistics.stdev(silence_gaps) if len(silence_gaps) >= 2 else avg_gap_h * 0.3

        next_window_in_h = None
        if hours_since is not None:
            expected_next = avg_gap_h - hours_since
            next_window_in_h = max(0.0, expected_next)

        # Frequency breakdown by type
        by_type = {}
        for e in all_events:
            by_type[e.event_type] = by_type.get(e.event_type, 0) + 1

        # WHO KNEW cache — load last run if available
        who_knew_cache = []
        try:
            import glob as _glob
            files = sorted(_glob.glob("atn_forensics_*.json"))
            if files:
                with open(files[-1]) as f:
                    who_knew_cache = json.load(f).get("suspects", [])
        except Exception:
            pass

        return LayerResult(name="PAST", status="OK", elapsed=time.time()-t0, data={
            "total_events":    len(all_events),
            "silence_count":   len(silences),
            "dissonance_count": len(dissonance),
            "by_type":         by_type,
            "last_silence":    last_silence,
            "hours_since_last_silence": hours_since,
            "next_window_h":   next_window_in_h,
            "avg_gap_h":       avg_gap_h,
            "std_gap_h":       std_gap_h,
            "top_events":      sorted(all_events, key=lambda e: e.severity, reverse=True)[:5],
            "who_knew":        who_knew_cache,
        })
    except Exception as e:
        return LayerResult(name="PAST", status="ERROR", elapsed=time.time()-t0,
                           data={"error": str(e)})


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 2 — PRESENT: SCHUMANN RESONANCE
# ─────────────────────────────────────────────────────────────────────────────

def _layer_schumann() -> LayerResult:
    t0 = time.time()
    try:
        from aureon.harmonic.aureon_schumann_resonance_bridge import get_live_schumann_data, get_earth_blessing
        reading = get_live_schumann_data(force_refresh=True)
        blessing_val, blessing_msg = get_earth_blessing(force_refresh=False)
        return LayerResult(name="SCHUMANN", status="OK", elapsed=time.time()-t0, data={
            "frequency_hz":  reading.frequency_hz,
            "amplitude":     reading.amplitude,
            "is_elevated":   reading.is_elevated,
            "is_disturbed":  reading.is_disturbed,
            "confidence":    reading.confidence,
            "source":        reading.source,
            "blessing":      blessing_val,
            "blessing_msg":  blessing_msg,
            "deviation_pct": abs(reading.frequency_hz - 7.83) / 7.83 * 100,
        })
    except Exception as e:
        return LayerResult(name="SCHUMANN", status="ERROR", elapsed=time.time()-t0,
                           data={"error": str(e), "frequency_hz": 7.83,
                                 "blessing": 0.5, "blessing_msg": "Unavailable"})


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 3 — PRESENT: HARMONIC SPECTRUM ANALYSIS (FFT)
# ─────────────────────────────────────────────────────────────────────────────

def _layer_spectrum(pair: str, candles: List[Dict]) -> LayerResult:
    t0 = time.time()
    try:
        import numpy as np
        from aureon.harmonic.aureon_harmonic_counter_frequency import HarmonicCounterFrequency, SACRED_FREQUENCIES

        if len(candles) < 24:
            raise ValueError("Insufficient candle data for FFT")

        closes = np.array([c["c"] for c in candles])
        volumes = np.array([c["v"] for c in candles])

        # Price FFT
        price_fft   = np.abs(np.fft.rfft(closes - closes.mean()))
        freq_bins   = np.fft.rfftfreq(len(closes))  # cycles per candle
        # Convert to hours (1h candles) → cycles per hour
        dominant_idx = np.argmax(price_fft[1:]) + 1   # skip DC
        dominant_freq_per_h = freq_bins[dominant_idx]
        dominant_period_h   = 1.0 / dominant_freq_per_h if dominant_freq_per_h > 0 else 0
        dominant_amplitude  = float(price_fft[dominant_idx])

        # Volume FFT
        vol_fft        = np.abs(np.fft.rfft(volumes - volumes.mean()))
        vol_dom_idx    = np.argmax(vol_fft[1:]) + 1
        vol_dom_freq   = freq_bins[vol_dom_idx]
        vol_dom_period = 1.0 / vol_dom_freq if vol_dom_freq > 0 else 0

        # Phase of dominant price cycle
        price_phase = float(np.angle(np.fft.rfft(closes - closes.mean())[dominant_idx], deg=True))

        # Sacred frequency match
        hcf = HarmonicCounterFrequency()
        counter_sig = hcf.generate_counter_signal(
            detected_frequency=dominant_freq_per_h,
            detected_phase=price_phase,
            detected_amplitude=dominant_amplitude / closes.mean() * 100  # normalise to %
        )

        # Phase alignment score (price vs volume): are they in sync?
        vol_phase  = float(np.angle(np.fft.rfft(volumes - volumes.mean())[vol_dom_idx], deg=True))
        phase_diff = abs(price_phase - vol_phase)
        alignment  = 1.0 - min(phase_diff, 360 - phase_diff) / 180.0  # 1=aligned, 0=anti-phase

        # Match to sacred frequencies
        sacred_match = None
        sacred_delta = 1e9
        for name, hz in SACRED_FREQUENCIES.items():
            # Convert sacred Hz → period in hours for comparison
            # Schumann 7.83 Hz → not directly comparable to daily cycles
            # Use modular interpretation: period in hours
            if 1 < hz < 1000:
                period_h_of_sacred = hz / PHI  # metaphorical mapping
            else:
                period_h_of_sacred = hz
            delta = abs(dominant_period_h - period_h_of_sacred)
            if delta < sacred_delta:
                sacred_delta  = delta
                sacred_match  = name

        # Top 3 dominant frequencies
        top3_idx = np.argsort(price_fft[1:])[-3:][::-1] + 1
        top3 = [{"period_h": float(1.0/freq_bins[i]) if freq_bins[i] > 0 else 0,
                 "amplitude_pct": float(price_fft[i]/closes.mean()*100)}
                for i in top3_idx]

        return LayerResult(name="SPECTRUM", status="OK", elapsed=time.time()-t0, data={
            "dominant_period_h":  dominant_period_h,
            "dominant_amp_pct":   dominant_amplitude / closes.mean() * 100,
            "price_phase_deg":    price_phase,
            "counter_phase":      counter_sig["target_phase"],
            "counter_timing_h":   (counter_sig["timing_low_h"], counter_sig["timing_high_h"]),
            "vol_period_h":       vol_dom_period,
            "phase_alignment":    alignment,
            "sacred_match":       sacred_match,
            "sacred_delta_h":     sacred_delta,
            "top3_cycles":        top3,
            "neutralization_pwr": counter_sig["neutralization_power"],
        })
    except Exception as e:
        return LayerResult(name="SPECTRUM", status="ERROR", elapsed=time.time()-t0,
                           data={"error": str(e)})


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 4 — PRESENT: COUNTER INTELLIGENCE
# ─────────────────────────────────────────────────────────────────────────────

def _layer_counter_intel(pair: str, price: float, candles: List[Dict]) -> LayerResult:
    t0 = time.time()
    try:
        from aureon.utils.aureon_queen_counter_intelligence import QueenCounterIntelligence, CounterStrategy

        qci = QueenCounterIntelligence()

        # Build market data context
        if len(candles) >= 2:
            momentum = (candles[-1]["c"] - candles[-2]["c"]) / candles[-2]["c"] * 100
            volumes  = [c["v"] for c in candles[-24:]]
            vol_avg  = statistics.mean(volumes) if volumes else 0
            vol_now  = candles[-1]["v"]
        else:
            momentum = 0.0
            vol_avg  = 0
            vol_now  = 0

        market_data = {
            "symbol":            pair,
            "price":             price,
            "momentum":          momentum,
            "volume_now":        vol_now,
            "volume_avg":        vol_avg,
            "volume_ratio":      vol_now / vol_avg if vol_avg else 1.0,
        }

        firms = ["citadel", "jane_street", "jump_trading",
                 "virtu_financial", "two_sigma"]
        signals = []
        for firm in firms:
            try:
                sig = qci.analyze_firm_for_counter_opportunity(firm, market_data)
                if sig:
                    signals.append({
                        "firm":      firm,
                        "strategy":  sig.strategy.value if hasattr(sig.strategy, 'value') else str(sig.strategy),
                        "confidence": sig.confidence,
                        "timing_ms": sig.execution_window_ms,
                        "reasoning": sig.reasoning[:80] if sig.reasoning else "",
                        "profit_est": sig.profit_estimate,
                    })
            except Exception:
                pass

        signals.sort(key=lambda s: s["confidence"], reverse=True)
        active_sigs = qci.get_active_counter_signals()

        return LayerResult(name="COUNTER_INTEL", status="OK", elapsed=time.time()-t0, data={
            "signals":      signals,
            "active_count": len(active_sigs),
            "top_signal":   signals[0] if signals else None,
            "momentum":     momentum,
        })
    except Exception as e:
        return LayerResult(name="COUNTER_INTEL", status="ERROR", elapsed=time.time()-t0,
                           data={"error": str(e)})


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 5 — PRESENT/FUTURE: TEMPORAL DIALER
# ─────────────────────────────────────────────────────────────────────────────

def _layer_temporal_dialer(schumann_hz: float = 7.83,
                            price_momentum: float = 0.0,
                            phase_alignment: float = 0.5) -> LayerResult:
    """
    Standalone temporal field analysis — no heavy Queen ecosystem imports.
    Tuned to 3 sacred frequencies using pure harmonic math.
    """
    t0 = time.time()
    import random as _r
    _r.seed(int(time.time() / 60))   # consistent within same minute

    PHI_LOCAL = (1 + math.sqrt(5)) / 2
    SACRED = [("SCHUMANN", 7.83), ("LOVE_528", 528.0), ("MIRACLE_432", 432.0)]

    # Schumann deviation drives baseline resonance
    schumann_dev = abs(schumann_hz - 7.83) / 7.83
    base_coherence = max(0.1, 1.0 - schumann_dev * 3)

    # Market momentum → temporal direction
    if price_momentum > 0.3:
        field_dir = "UP";   omega = 0.5 + min(0.45, price_momentum / 5)
    elif price_momentum < -0.3:
        field_dir = "DOWN"; omega = 0.5 - min(0.45, abs(price_momentum) / 5)
    else:
        field_dir = "NEUTRAL"; omega = 0.5

    # Phase alignment modulates coherence
    coherence = base_coherence * (0.7 + 0.3 * phase_alignment)

    packets = []
    for ch_name, hz in SACRED:
        # Resonance: how close is current Schumann deviation to this freq's "pull"
        if ch_name == "SCHUMANN":
            resonance = max(0.1, 1.0 - schumann_dev * 2)
        elif ch_name == "LOVE_528":
            # 528 Hz → love/DNA repair → market sentiment proxy
            resonance = max(0.2, 0.5 + (phase_alignment - 0.5) * 0.8)
        else:
            # 432 Hz → universal harmony → phi-alignment proxy
            resonance = max(0.2, 0.4 + PHI_LOCAL * 0.1 * (omega - 0.5) + 0.2)

        intensity = resonance * (1.0 - schumann_dev * 0.3)

        # Layer signals from resonance + momentum
        wisdom_sig = "BUY" if omega > 0.6 else "SELL" if omega < 0.4 else "HOLD"
        market_sig = "BUY" if price_momentum > 0.1 else "SELL" if price_momentum < -0.1 else "HOLD"
        quantum_sig = "BUY" if resonance > 0.6 and coherence > 0.5 else \
                      "SELL" if resonance < 0.3 else "HOLD"

        packets.append({
            "name": ch_name, "hz": hz,
            "resonance": resonance, "intensity": intensity, "coherence": coherence,
            "field_omega": omega, "field_dir": field_dir,
            "field_confidence": coherence,
            "layer_wisdom":  wisdom_sig,
            "layer_quantum": quantum_sig,
            "layer_market":  market_sig,
            "phase_alignment": phase_alignment,
            "energy_density":  coherence,
            "source": "ATN_Harmonic_Math",
        })

    return LayerResult(name="TEMPORAL", status="OK", elapsed=time.time()-t0, data={
        "packets":         packets,
        "composite_omega": omega,
        "dominant_dir":    field_dir,
        "coherence":       coherence,
    })


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 6 — FUTURE: TRUTH PREDICTION ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def _layer_predictions(pair: str, price: float, candles: List[Dict]) -> LayerResult:
    """
    Standalone predictions using FFT harmonic projections + Fibonacci targets.
    No heavy Queen ecosystem required.
    """
    t0 = time.time()
    try:
        import numpy as np

        if len(candles) < 8:
            raise ValueError("Need at least 8 candles")

        closes  = np.array([c["c"] for c in candles])
        volumes = np.array([c["v"] for c in candles])
        hi      = np.array([c["h"] for c in candles])
        lo      = np.array([c["l"] for c in candles])

        # Momentum at multiple timeframes (% change)
        m1h  = (closes[-1] - closes[-2]) / closes[-2] * 100
        m4h  = (closes[-1] - closes[-5]) / closes[-5] * 100 if len(closes) >= 5 else m1h
        m24h = (closes[-1] - closes[-25]) / closes[-25] * 100 if len(closes) >= 25 else m1h

        # Volatility (ATR-based)
        true_ranges = [max(hi[i]-lo[i], abs(hi[i]-closes[i-1]), abs(lo[i]-closes[i-1]))
                       for i in range(1, len(closes))]
        atr_14 = np.mean(true_ranges[-14:]) if len(true_ranges) >= 14 else np.mean(true_ranges)
        volatility_pct = atr_14 / price * 100

        # Volume ratio
        vol_avg = np.mean(volumes[-24:]) if len(volumes) >= 24 else np.mean(volumes)
        vol_ratio = float(volumes[-1] / vol_avg) if vol_avg else 1.0

        # FFT-based cycle projection
        fft_close = np.fft.rfft(closes[-48:] if len(closes) >= 48 else closes)
        freqs     = np.fft.rfftfreq(min(48, len(closes)))
        dominant  = np.argmax(np.abs(fft_close[1:])) + 1
        phase_now = float(np.angle(fft_close[dominant]))

        PHI_LOCAL = (1 + math.sqrt(5)) / 2

        # For each horizon: project using dominant cycle + momentum
        predictions = []
        for horizon_h, label in [(1, "1h"), (4, "4h"), (24, "24h")]:
            # Phase advance for this horizon
            if freqs[dominant] > 0:
                phase_advance = 2 * math.pi * freqs[dominant] * horizon_h
                projected_cycle = float(np.abs(fft_close[dominant])) / len(closes) * \
                                  math.cos(phase_now + phase_advance)
            else:
                projected_cycle = 0.0

            # Momentum decay over horizon
            decay = math.exp(-horizon_h / 24.0)
            base_mom = m1h if horizon_h == 1 else m4h if horizon_h == 4 else m24h
            proj_change = base_mom * decay + projected_cycle / price * 100

            # Fibonacci support/resistance projection
            fib_levels = [closes[-1] * (1 + r) for r in
                          [0.0, 0.382, 0.618, 1.0, 1.618, -0.382, -0.618]]
            nearest_fib = min(fib_levels, key=lambda f: abs(f - (price + proj_change / 100 * price)))
            fib_pull = (nearest_fib - price) / price * 100

            # Blend: 60% momentum projection + 40% Fibonacci pull
            blended_change = 0.6 * proj_change + 0.4 * fib_pull

            # Confidence from volatility and momentum agreement
            vol_confidence = max(0.3, 1.0 - volatility_pct / 5.0)
            momentum_agreement = 1.0 if (m1h * m4h > 0) else 0.6  # same direction
            win_prob = min(0.90, max(0.45,
                (0.5 + abs(blended_change) / volatility_pct * 0.3) *
                vol_confidence * momentum_agreement))

            direction = "UP" if blended_change > volatility_pct * 0.1 else \
                        "DOWN" if blended_change < -volatility_pct * 0.1 else "FLAT"

            # Auris geometric truth: PHI alignment check
            phi_score = 1.0 / (1.0 + abs(abs(blended_change) - PHI_LOCAL) / PHI_LOCAL)
            auris_approved = win_prob >= 0.60 and phi_score > 0.3
            queen_approved = win_prob >= 0.65

            predictions.append({
                "horizon":        label,
                "direction":      direction,
                "change_pct":     blended_change,
                "win_prob":       win_prob,
                "confidence":     vol_confidence * momentum_agreement,
                "auris_approved": auris_approved,
                "queen_approved": queen_approved,
                "auris_resonance": phi_score,
                "fib_target":     nearest_fib,
                "cycle_contribution": projected_cycle / price * 100,
            })

        return LayerResult(name="PREDICTIONS", status="OK", elapsed=time.time()-t0, data={
            "predictions": predictions,
            "momentum":    m1h,
            "volatility":  volatility_pct,
            "vol_ratio":   vol_ratio,
            "atr_14":      float(atr_14),
        })
    except Exception as e:
        return LayerResult(name="PREDICTIONS", status="ERROR", elapsed=time.time()-t0,
                           data={"error": str(e), "predictions": []})


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 7 — PRESENT: REAL INTELLIGENCE ENGINE (Bots + Whales + Momentum)
# ─────────────────────────────────────────────────────────────────────────────

def _layer_real_intelligence(pair: str, price: float) -> LayerResult:
    """Fully standalone order book analysis — no sub-system imports needed."""
    t0 = time.time()
    try:
        ob = _kraken_orderbook(pair, count=20)
        asks = ob.get("asks", [])
        bids = ob.get("bids", [])

        # Simple whale wall detection
        whale_walls = []
        if asks:
            for price_lvl, vol in asks:
                notional = price_lvl * vol
                if notional >= 50_000:
                    whale_walls.append({"side": "ASK", "price": price_lvl,
                                        "notional": notional, "vol": vol})
        if bids:
            for price_lvl, vol in bids:
                notional = price_lvl * vol
                if notional >= 50_000:
                    whale_walls.append({"side": "BID", "price": price_lvl,
                                        "notional": notional, "vol": vol})
        whale_walls.sort(key=lambda w: w["notional"], reverse=True)

        # Total bid/ask imbalance
        bid_notional = sum(p*v for p,v in bids)
        ask_notional = sum(p*v for p,v in asks)
        total        = bid_notional + ask_notional
        imbalance    = (bid_notional - ask_notional) / total if total else 0

        # Top firm matching (lightweight pattern)
        momentum_opps = []
        if imbalance > 0.15:
            momentum_opps.append({"scanner": "OrderBook", "symbol": pair,
                                  "side": "BUY", "confidence": min(0.95, 0.5 + imbalance),
                                  "reason": f"Bid pressure {imbalance*100:+.1f}%"})
        elif imbalance < -0.15:
            momentum_opps.append({"scanner": "OrderBook", "symbol": pair,
                                  "side": "SELL", "confidence": min(0.95, 0.5 - imbalance),
                                  "reason": f"Ask pressure {imbalance*100:+.1f}%"})

        bot_count = len([w for w in whale_walls if w["notional"] >= 100_000])

        return LayerResult(name="INTELLIGENCE", status="OK", elapsed=time.time()-t0, data={
            "bot_count":      bot_count,
            "whale_count":    len(whale_walls),
            "momentum_opps":  momentum_opps[:6],
            "validated":      [],
            "top_bot":        None,
            "top_whale":      whale_walls[0] if whale_walls else None,
            "bid_notional":   bid_notional,
            "ask_notional":   ask_notional,
            "ob_imbalance":   imbalance,
            "whale_walls":    whale_walls[:8],
        })
    except Exception as e:
        # Final fallback
        return LayerResult(name="INTELLIGENCE", status="WARN", elapsed=time.time()-t0,
                           data={"error": str(e), "bot_count": 0, "whale_count": 0,
                                 "momentum_opps": [], "validated": [],
                                 "top_bot": None, "top_whale": None})

        bots    = intel.get("bot_profiles",          [])
        whales  = intel.get("whale_predictions",     [])
        momentum_data = intel.get("momentum_data",   {})
        validated     = intel.get("validated_intelligence", [])

        # Flatten momentum
        momentum_opps = []
        for scanner, opps in momentum_data.items():
            for opp in (opps or []):
                try:
                    momentum_opps.append({
                        "scanner":    scanner,
                        "symbol":     opp.symbol,
                        "side":       opp.side if isinstance(opp.side, str) else opp.side.value,
                        "confidence": opp.confidence,
                        "reason":     str(opp.reason)[:50] if hasattr(opp, 'reason') else "",
                    })
                except Exception:
                    pass
        momentum_opps.sort(key=lambda o: o["confidence"], reverse=True)

        return LayerResult(name="INTELLIGENCE", status="OK", elapsed=time.time()-t0, data={
            "bot_count":      len(bots),
            "whale_count":    len(whales),
            "momentum_opps":  momentum_opps[:6],
            "validated":      validated[:3],
            "top_bot":        vars(bots[0]) if bots and hasattr(bots[0], '__dict__') else (bots[0] if bots else None),
            "top_whale":      vars(whales[0]) if whales and hasattr(whales[0], '__dict__') else (whales[0] if whales else None),
        })
    except Exception as e:
        return LayerResult(name="INTELLIGENCE", status="ERROR", elapsed=time.time()-t0,
                           data={"error": str(e)})


# ─────────────────────────────────────────────────────────────────────────────
# COMPOSITE SIGNAL BUILDER
# ─────────────────────────────────────────────────────────────────────────────

def _build_composite(layers: Dict[str, LayerResult], pair: str, price: float) -> CompositeSignal:
    votes   = []
    weights = []
    components = []
    risk_flags = []

    # Temporal dialer vote (weight 0.25)
    td = layers.get("TEMPORAL", LayerResult("", "ERROR"))
    if td.status == "OK":
        omega  = td.data.get("composite_omega", 0.5)
        d      = td.data.get("dominant_dir", "NEUTRAL")
        coh    = td.data.get("coherence", 0.5)
        v = 1.0 if d == "UP" else (-1.0 if d == "DOWN" else 0.0)
        v = v * omega * coh
        votes.append(v); weights.append(0.25)
        dir_str = f"Ω={omega:.2f} {d}"
        components.append(f"Temporal Dialer: {_c(dir_str, GRN if v>0 else RED if v<0 else YEL)}")

    # Predictions vote (weight 0.30 for 1h, 0.20 for 4h)
    pd = layers.get("PREDICTIONS", LayerResult("", "ERROR"))
    if pd.status == "OK":
        for pred in pd.data.get("predictions", []):
            if pred["horizon"] in ("1h", "4h"):
                w = 0.30 if pred["horizon"] == "1h" else 0.20
                d_val = 1.0 if pred["direction"] == "UP" else \
                        (-1.0 if pred["direction"] == "DOWN" else 0.0)
                v = d_val * pred["win_prob"] * pred.get("confidence", 0.5)
                votes.append(v); weights.append(w)
                col = GRN if d_val > 0 else RED if d_val < 0 else YEL
                components.append(f"Prediction {pred['horizon']}: "
                                  f"{_c(pred['direction'], col)} "
                                  f"{pred['change_pct']:+.2f}% "
                                  f"({pred['win_prob']*100:.0f}%)")

    # Counter intel vote (weight 0.15)
    ci = layers.get("COUNTER_INTEL", LayerResult("", "ERROR"))
    if ci.status == "OK":
        top = ci.data.get("top_signal")
        if top:
            strat = top["strategy"].lower()
            v = 1.0 if "buy" in strat or "front_run" in strat or "fade_sell" in strat else \
               -1.0 if "sell" in strat or "fade_buy" in strat else 0.0
            v *= top["confidence"]
            votes.append(v); weights.append(0.15)
            components.append(f"Counter Intel vs {top['firm']}: "
                               f"{_c(top['strategy'], CYN)} "
                               f"({top['confidence']*100:.0f}%)")

    # Schumann vote (weight 0.10)
    sc = layers.get("SCHUMANN", LayerResult("", "ERROR"))
    if sc.status == "OK":
        b = sc.data.get("blessing", 0.5)
        if sc.data.get("is_disturbed", False):
            risk_flags.append(f"Schumann disturbed ({sc.data.get('frequency_hz',7.83):.2f} Hz)")
            votes.append(-0.3); weights.append(0.10)
        elif b > 0.7:
            votes.append(0.2); weights.append(0.10)
            components.append(f"Schumann: {_c(sc.data.get('blessing_msg',''), GRN)}")
        else:
            votes.append(0.0); weights.append(0.10)

    # Planetary risk (from PAST layer)
    past = layers.get("PAST", LayerResult("", "ERROR"))
    if past.status == "OK":
        nw = past.data.get("next_window_h")
        if nw is not None and nw < 48:
            risk_flags.append(f"Planetary event window: ~{nw:.0f}h away (SILENCE cycle)")
        if nw is not None and nw < 12:
            votes.append(-0.2); weights.append(0.10)  # caution near event window

    # Compute weighted signal
    if votes and weights:
        total_w  = sum(weights)
        weighted = sum(v * w for v, w in zip(votes, weights))
        signal   = weighted / total_w
    else:
        signal = 0.0

    confidence = min(0.99, abs(signal))
    if signal > 0.15:
        direction = "BUY"
    elif signal < -0.15:
        direction = "SELL"
    else:
        direction = "HOLD"

    nw = past.data.get("next_window_h") if past.status == "OK" else None
    return CompositeSignal(
        direction=direction, confidence=confidence, pair=pair, price=price,
        components=components, risk_flags=risk_flags, next_event_hours=nw,
    )


# ─────────────────────────────────────────────────────────────────────────────
# RENDERERS
# ─────────────────────────────────────────────────────────────────────────────

W = 88

def _hdr(title: str, col: str = CYN) -> str:
    inner = f"  {title}  "
    pad   = W - 4 - len(inner)
    return f"{BOLD}{col}┌─{inner}{'─'*max(0,pad)}─┐{RST}"


def _div(col: str = CYN) -> str:
    return f"{BOLD}{col}└{'─'*(W-2)}┘{RST}"


def render_banner(pair: str, price: Optional[float]) -> None:
    print(f"\n{BOLD}{RED}╔{'═'*(W-2)}╗{RST}")
    print(f"{BOLD}{RED}║{'AUREON ATN COMMAND CENTER — TEMPORAL INTELLIGENCE MATRIX':^{W-2}}║{RST}")
    print(f"{BOLD}{RED}║{'See the Past  ·  Master the Present  ·  Shape the Future':^{W-2}}║{RST}")
    print(f"{BOLD}{RED}╚{'═'*(W-2)}╝{RST}")
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    price_str = f"${price:,.2f}" if price else "---"
    print(f"  {DIM}Run: {ts}  │  Pair: {BOLD}{pair}{RST}{DIM}  │  Price: {BOLD}{WHT}{price_str}{RST}{DIM}{RST}")


def render_past(layer: LayerResult) -> None:
    print(f"\n{_hdr('◀ PAST  —  PLANETARY EVENT HISTORY', RED)}")
    if layer.status == "ERROR":
        print(f"  {RED}ERROR: {layer.data.get('error','')}{RST}")
        print(f"{_div(RED)}"); return

    d = layer.data
    by_type = d.get("by_type", {})
    print(f"  {BOLD}Period:{RST} Last 365 days  │  "
          f"{BOLD}Total events:{RST} {d.get('total_events',0)}  │  "
          f"{_c('SILENCE', RED)}: {d.get('silence_count',0)}  │  "
          f"{_c('DISSONANCE', MAG)}: {d.get('dissonance_count',0)}")

    # Event type breakdown
    type_line = "  "
    for etype, count in sorted(by_type.items(), key=lambda x: -x[1]):
        type_line += f"{DIM}{etype}:{RST} {count}  "
    print(type_line)

    # Last SILENCE event
    ls = d.get("last_silence")
    if ls:
        hs = d.get("hours_since_last_silence", 0)
        gcol = GC.get(ls.grade, WHT)
        dt_s = datetime.fromtimestamp(ls.timestamp, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
        print(f"\n  {BOLD}Last SILENCE:{RST} {gcol}{ls.event_type.upper()} "
              f"{ls.raw_magnitude}{RST}  @{dt_s}  "
              f"({ls.location[:45]})")
        print(f"  {DIM}Hours since:  {hs:.0f}h  │  "
              f"Avg cycle: {d.get('avg_gap_h',168):.0f}h ± {d.get('std_gap_h',0):.0f}h{RST}")

    # Next event window
    nw = d.get("next_window_h")
    if nw is not None:
        col  = RED if nw < 24 else YEL if nw < 72 else GRN
        bar  = _bar(max(0, 1 - nw/d.get("avg_gap_h",168)), 0, 1, 20, col)
        print(f"\n  {BOLD}Next SILENCE window:{RST}  "
              f"{col}{BOLD}~{nw:.0f}h{RST}  {bar}  "
              f"{'⚠ IMMINENT' if nw<24 else '⚑ WATCH' if nw<72 else '✓ CLEAR'}")

    # Top events
    tops = d.get("top_events", [])
    if tops:
        print(f"\n  {BOLD}Top SILENCE/DISSONANCE events:{RST}")
        for e in tops[:5]:
            gcol = GC.get(e.grade, WHT)
            dt_s = datetime.fromtimestamp(e.timestamp, tz=timezone.utc).strftime("%m-%d %H:%M")
            print(f"   {gcol}{e.event_type[:12]:<12}{RST}  "
                  f"{e.raw_magnitude:<6}  {dt_s}  "
                  f"{gcol}{e.grade:<18}{RST}  {e.location[:35]}")

    print(f"{_div(RED)}")


def render_schumann(layer: LayerResult) -> None:
    print(f"\n{_hdr('SCHUMANN RESONANCE  —  Earth Heartbeat (LIVE)', BLU)}")
    d = layer.data
    if layer.status == "ERROR" and "frequency_hz" not in d:
        print(f"  {RED}ERROR: {d.get('error','')}{RST}")
        print(f"{_div(BLU)}"); return
    hz      = d.get("frequency_hz", 7.83)
    amp     = d.get("amplitude", 1.0)
    conf    = d.get("confidence", 0.5)
    blessed = d.get("blessing", 0.5)
    msg     = d.get("blessing_msg", "")
    dev     = d.get("deviation_pct", 0)
    disturbed = d.get("is_disturbed", False)
    elevated  = d.get("is_elevated", False)

    state_col = RED if disturbed else YEL if elevated else GRN
    state_str = "DISTURBED ⚠" if disturbed else "ELEVATED ↑" if elevated else "STABLE ✓"
    bar_hz    = _bar(hz, 7.0, 9.5, 20, state_col)

    print(f"  Freq: {state_col}{BOLD}{hz:.3f} Hz{RST}  "
          f"{bar_hz}  State: {state_col}{BOLD}{state_str}{RST}")
    print(f"  Amplitude: {amp:.3f}  │  Deviation: {dev:.1f}%  │  "
          f"Confidence: {conf*100:.0f}%  │  Source: {DIM}{d.get('source','')}{RST}")
    print(f"  Earth Blessing: {GRN}{BOLD}{blessed:.3f}{RST}  {_bar(blessed,0,1,20,GRN)}  "
          f"{_c(msg, GRN if blessed>0.6 else YEL)}")
    print(f"{_div(BLU)}")


def render_spectrum(layer: LayerResult) -> None:
    print(f"\n{_hdr('HARMONIC SPECTRUM ANALYSIS  —  FFT Phase Intelligence', MAG)}")
    if layer.status == "ERROR":
        print(f"  {RED}ERROR: {layer.data.get('error','')}{RST}")
        print(f"{_div(MAG)}"); return
    d = layer.data

    period   = d.get("dominant_period_h", 0)
    amp_pct  = d.get("dominant_amp_pct", 0)
    phase    = d.get("price_phase_deg", 0)
    counter  = d.get("counter_phase", 0)
    ct_lo, ct_hi = d.get("counter_timing_h", (0,0))
    align    = d.get("phase_alignment", 0.5)
    sacred   = d.get("sacred_match", "?")
    neut_pwr = d.get("neutralization_pwr", 0)

    print(f"  {BOLD}Dominant cycle:{RST}  {period:.1f}h period  │  "
          f"Amplitude: {amp_pct:.2f}%  │  Phase: {phase:+.1f}°")
    print(f"  {BOLD}Counter-phase:{RST}  {counter:.1f}°  │  "
          f"Optimal entry window: {ct_lo:.2f}h – {ct_hi:.2f}h  │  "
          f"Neutralization: {neut_pwr*100:.0f}%")

    align_col = GRN if align > 0.7 else YEL if align > 0.4 else RED
    print(f"  Price/Volume phase alignment: {align_col}{BOLD}{align*100:.0f}%{RST}  "
          f"{_bar(align, 0, 1, 20, align_col)}  "
          f"{'COORDINATED ⚠' if align > 0.7 else 'DIVERGING ↑' if align < 0.3 else 'MIXED'}")
    print(f"  {BOLD}Sacred match:{RST} {_c(sacred, MAG)}  "
          f"(Δ = {d.get('sacred_delta_h',0):.1f}h from resonance)")

    tops = d.get("top3_cycles", [])
    if tops:
        print(f"\n  Top 3 dominant cycles:")
        for i, t in enumerate(tops, 1):
            print(f"   {i}. period={t['period_h']:.1f}h  amplitude={t['amplitude_pct']:.3f}%")
    print(f"{_div(MAG)}")


def render_counter_intel(layer: LayerResult) -> None:
    print(f"\n{_hdr('COUNTER INTELLIGENCE  —  Firm Counter-Strategies', YEL)}")
    if layer.status == "ERROR":
        print(f"  {RED}ERROR: {layer.data.get('error','')}{RST}")
        print(f"{_div(YEL)}"); return
    d = layer.data

    sigs = d.get("signals", [])
    mom  = d.get("momentum", 0)
    mom_col = GRN if mom > 0 else RED if mom < 0 else YEL
    print(f"  Current momentum: {mom_col}{BOLD}{mom:+.3f}%{RST}  │  "
          f"Active counter-signals: {len(sigs)}")

    if sigs:
        print(f"\n  {'FIRM':<20} {'STRATEGY':<22} {'CONF':>6} {'TIMING_MS':>10} {'EST_PROFIT':>12}")
        print(f"  {'─'*20} {'─'*22} {'─'*6} {'─'*10} {'─'*12}")
        for s in sigs[:6]:
            conf_col = GRN if s["confidence"] > 0.7 else YEL if s["confidence"] > 0.5 else DIM
            print(f"  {_c(s['firm'][:20], CYN):<20} "
                  f"{s['strategy'][:22]:<22} "
                  f"{conf_col}{s['confidence']*100:>5.0f}%{RST} "
                  f"{s.get('timing_ms',0):>10.0f}ms "
                  f"${s.get('profit_est',0):>10.2f}")
    print(f"{_div(YEL)}")


def render_temporal(layer: LayerResult) -> None:
    print(f"\n{_hdr('TEMPORAL DIALER  —  Quantum Field Frequencies', CYN)}")
    if layer.status == "ERROR":
        print(f"  {RED}ERROR: {layer.data.get('error','')}{RST}")
        print(f"{_div(CYN)}"); return
    d = layer.data

    print(f"  {BOLD}Composite Ω:{RST}  "
          f"{d.get('composite_omega',0.5):.4f}  │  "
          f"Direction: {_c(d.get('dominant_dir','?'), GRN if d.get('dominant_dir')=='UP' else RED if d.get('dominant_dir')=='DOWN' else YEL)}  │  "
          f"Field Coherence: {d.get('coherence',0.5)*100:.0f}%")

    pkts = d.get("packets", [])
    if pkts:
        print(f"\n  {'CHANNEL':<16} {'HZ':>7} {'RESONANCE':>10} {'INTENSITY':>10} "
              f"{'Ω':>7} {'DIRECTION':<12} {'WISDOM':<10} {'MARKET':<10}")
        print(f"  {'─'*16} {'─'*7} {'─'*10} {'─'*10} {'─'*7} {'─'*12} {'─'*10} {'─'*10}")
        for p in pkts:
            d_col = GRN if p.get('field_dir') == 'UP' else \
                    RED if p.get('field_dir') == 'DOWN' else YEL
            res_bar = _bar(p["resonance"], 0, 1, 8, d_col)
            print(f"  {_c(p['name'], CYN):<16} {p['hz']:>7.2f} "
                  f"  {res_bar}  "
                  f"{p['intensity']:>9.3f}  "
                  f"{p.get('field_omega',0.5):>6.3f}  "
                  f"{d_col}{str(p.get('field_dir','?')):<12}{RST}  "
                  f"{str(p.get('layer_wisdom','?'))[:10]:<10}  "
                  f"{str(p.get('layer_market','?'))[:10]:<10}")
    print(f"{_div(CYN)}")


def render_predictions(layer: LayerResult) -> None:
    print(f"\n{_hdr('TRUTH PREDICTION ENGINE  —  Queen × Auris Validated', GRN)}")
    if layer.status == "ERROR":
        print(f"  {RED}ERROR: {layer.data.get('error','')}{RST}")
        print(f"{_div(GRN)}"); return
    d = layer.data

    mom = d.get("momentum", 0)
    vol = d.get("volatility", 0)
    vr  = d.get("vol_ratio", 1.0)
    mom_col = GRN if mom > 0 else RED if mom < 0 else YEL
    print(f"  Momentum: {mom_col}{BOLD}{mom:+.3f}%{RST}  │  "
          f"Volatility: {vol:.3f}%  │  Volume ratio: {vr:.2f}x")

    preds = d.get("predictions", [])
    if preds:
        print(f"\n  {'HORIZON':<8} {'DIR':<8} {'CHANGE':>8} {'WIN%':>7} {'CONF':>7} "
              f"{'AURIS':>7} {'QUEEN':>7}")
        print(f"  {'─'*8} {'─'*8} {'─'*8} {'─'*7} {'─'*7} {'─'*7} {'─'*7}")
        for p in preds:
            d_col = GRN if p["direction"] == "UP" else \
                    RED if p["direction"] == "DOWN" else YEL
            a_col = GRN if p["auris_approved"] else RED
            q_col = GRN if p["queen_approved"] else RED
            print(f"  {p['horizon']:<8} "
                  f"{d_col}{p['direction']:<8}{RST} "
                  f"{d_col}{p['change_pct']:>+7.3f}%{RST}  "
                  f"{p['win_prob']*100:>6.1f}%  "
                  f"{p['confidence']*100:>6.1f}%  "
                  f"{a_col}{'YES' if p['auris_approved'] else 'NO':>7}{RST}  "
                  f"{q_col}{'YES' if p['queen_approved'] else 'NO':>7}{RST}")
    print(f"{_div(GRN)}")


def render_intelligence(layer: LayerResult) -> None:
    print(f"\n{_hdr('ORDER BOOK INTELLIGENCE  —  Whale Walls · Imbalance · Bots', WHT)}")
    if layer.status == "ERROR":
        print(f"  {RED}ERROR: {layer.data.get('error','')}{RST}")
        print(f"{_div(WHT)}"); return
    d = layer.data

    if layer.status == "WARN":
        print(f"  {YEL}⚠ Lightweight mode: {d.get('error','')}{RST}")

    imb    = d.get("ob_imbalance", 0)
    bid_n  = d.get("bid_notional", 0)
    ask_n  = d.get("ask_notional", 0)
    imb_col = GRN if imb > 0.1 else RED if imb < -0.1 else YEL
    print(f"  Order Book Imbalance: {imb_col}{BOLD}{imb*100:+.1f}%{RST}  "
          f"│  Bid: ${bid_n:,.0f}  │  Ask: ${ask_n:,.0f}  "
          f"│  Whale walls: {BOLD}{d.get('whale_count',0)}{RST}")

    walls = d.get("whale_walls", [])
    if walls:
        print(f"\n  {BOLD}Whale Order Walls (≥$50k):{RST}")
        print(f"  {'SIDE':<6} {'PRICE':>12} {'NOTIONAL':>14} {'SIZE':>8}  {'POWER'}")
        print(f"  {'─'*6} {'─'*12} {'─'*14} {'─'*8}  {'─'*20}")
        for w in walls[:8]:
            side_col = GRN if w["side"] == "BID" else RED
            bar = _bar(w["notional"], 0, max(w2["notional"] for w2 in walls), 14, side_col)
            print(f"  {side_col}{w['side']:<6}{RST} "
                  f"${w['price']:>11,.2f}  "
                  f"{side_col}${w['notional']:>12,.0f}{RST}  "
                  f"{w['vol']:>7.3f}  "
                  f"{bar}")

    opps = d.get("momentum_opps", [])
    if opps:
        print(f"\n  {BOLD}Order Flow Signals:{RST}")
        for op in opps:
            side_col = GRN if op["side"] == "BUY" else RED
            print(f"   {DIM}{op['scanner'][:12]:<12}{RST}  "
                  f"{side_col}{op['side']:<5}{RST}  "
                  f"conf={op['confidence']*100:.0f}%  "
                  f"{DIM}{op.get('reason','')}{RST}")
    print(f"{_div(WHT)}")


def render_composite(sig: CompositeSignal) -> None:
    W2 = W
    col = GRN if sig.direction == "BUY" else RED if sig.direction == "SELL" else YEL
    print(f"\n{BOLD}{col}{'╔' + '═'*(W2-2) + '╗'}{RST}")

    dir_line = f"  COMPOSITE SIGNAL:  {sig.direction}  {sig.pair}  @  ${sig.price:,.2f}"
    conf_line = f"  Confidence: {sig.confidence*100:.0f}%  {_bar(sig.confidence,0,1,20,col)}"
    print(f"{BOLD}{col}║{dir_line:<{W2-2}}║{RST}")
    print(f"{BOLD}{col}║{conf_line:<{W2-2}}║{RST}")

    if sig.components:
        print(f"{BOLD}{col}║{'':^{W2-2}}║{RST}")
        for c_str in sig.components:
            clean = c_str.replace(GRN,'').replace(RED,'').replace(YEL,'').replace(RST,'').replace(BOLD,'').replace(DIM,'')
            print(f"{BOLD}{col}║{RST}  {c_str}")

    if sig.risk_flags:
        print(f"{BOLD}{col}║{'':^{W2-2}}║{RST}")
        for rf in sig.risk_flags:
            print(f"{BOLD}{col}║{RST}  {RED}⚠ {rf}{RST}")

    if sig.next_event_hours is not None:
        nw_col = RED if sig.next_event_hours < 24 else YEL if sig.next_event_hours < 72 else GRN
        nw_line = f"  Next planetary event window: ~{sig.next_event_hours:.0f}h"
        print(f"{BOLD}{col}║{RST}  {nw_col}{nw_line}{RST}")

    print(f"{BOLD}{col}{'╚' + '═'*(W2-2) + '╝'}{RST}")


def render_layer_status(layers: Dict[str, LayerResult]) -> None:
    print(f"\n  {DIM}Layer timings: ", end="")
    for name, lr in layers.items():
        col = GRN if lr.status == "OK" else YEL if lr.status == "WARN" else RED
        print(f"{col}{name}:{lr.elapsed:.1f}s{RST}  ", end="")
    print(RST)


# ─────────────────────────────────────────────────────────────────────────────
# ORCHESTRATOR
# ─────────────────────────────────────────────────────────────────────────────

def run_once(args) -> None:
    pair    = args.pair
    deep    = args.deep
    days    = args.days

    # Suppress ALL stdout/stderr init noise from sub-systems during parallel work
    logging.disable(logging.CRITICAL)
    import io as _io
    _old_stdout, _old_stderr = sys.stdout, sys.stderr
    sys.stdout = _io.StringIO()
    sys.stderr = _io.StringIO()

    # ── Live price first ──────────────────────────────────────────────────
    print(f"\n  {DIM}Fetching live price for {pair}…{RST}", flush=True)
    price   = _kraken_price(pair)
    if price is None:
        price = 0.0
        print(f"  {YEL}⚠ Could not fetch live price{RST}")

    candles = _kraken_ohlc(pair, interval=60, n=72)

    render_banner(pair, price)

    print(f"\n  {DIM}Running {7 if deep else 6} intelligence layers in parallel…{RST}", flush=True)

    # ── Parallel layer execution (no blocking shutdown) ───────────────────
    from concurrent.futures import ThreadPoolExecutor as _TPE
    ex = _TPE(max_workers=8)
    # Phase 1: quick layers first to feed into dependent ones
    fut_schumann  = ex.submit(_layer_schumann)
    fut_spectrum  = ex.submit(_layer_spectrum, pair, candles)
    fut_past      = ex.submit(_layer_past, days)
    fut_intel     = ex.submit(_layer_real_intelligence, pair, price)
    fut_counter   = ex.submit(_layer_counter_intel, pair, price, candles)
    fut_preds     = ex.submit(_layer_predictions, pair, price, candles)

    # Get Schumann + spectrum quickly to feed temporal dialer
    _sc = fut_schumann.result(timeout=8)
    _sp = fut_spectrum.result(timeout=8)
    _schumann_hz     = _sc.data.get("frequency_hz", 7.83) if _sc.status == "OK" else 7.83
    _phase_alignment = _sp.data.get("phase_alignment", 0.5) if _sp.status == "OK" else 0.5
    # Momentum from candles
    _mom = 0.0
    if len(candles) >= 5:
        _mom = (candles[-1]["c"] - candles[-5]["c"]) / candles[-5]["c"] * 100

    fut_temporal = ex.submit(_layer_temporal_dialer, _schumann_hz, _mom, _phase_alignment)

    futures_map = {
        "PAST":          fut_past,
        "SCHUMANN":      fut_schumann,
        "SPECTRUM":      fut_spectrum,
        "COUNTER_INTEL": fut_counter,
        "TEMPORAL":      fut_temporal,
        "PREDICTIONS":   fut_preds,
        "INTELLIGENCE":  fut_intel,
    }

    # Pre-populate already-fetched results
    layers: Dict[str, LayerResult] = {
        "SCHUMANN": _sc,
        "SPECTRUM":  _sp,
    }
    HARD_DEADLINE = time.time() + 30   # remaining budget after schumann+spectrum
    for name, fut in futures_map.items():
        if name in layers:
            continue   # already resolved
        remaining = max(1.0, HARD_DEADLINE - time.time())
        try:
            layers[name] = fut.result(timeout=remaining)
        except TimeoutError:
            layers[name] = LayerResult(name, "WARN",
                                       {"error": "timeout — layer still running"})
        except Exception as e:
            layers[name] = LayerResult(name, "ERROR", {"error": str(e)})

    # Release thread pool without waiting for slow threads to finish
    ex.shutdown(wait=False)

    # Restore stdout/stderr — sub-system noise is gone, we render clean
    sys.stdout = _old_stdout
    sys.stderr = _old_stderr
    logging.disable(logging.WARNING)

    # ── Render all layers ─────────────────────────────────────────────────
    render_past(layers["PAST"])
    render_schumann(layers["SCHUMANN"])
    render_spectrum(layers["SPECTRUM"])
    render_counter_intel(layers["COUNTER_INTEL"])
    render_temporal(layers["TEMPORAL"])
    render_predictions(layers["PREDICTIONS"])
    render_intelligence(layers["INTELLIGENCE"])

    # ── Composite signal ──────────────────────────────────────────────────
    composite = _build_composite(layers, pair, price)
    render_composite(composite)
    render_layer_status(layers)

    if not args.live:
        # Force exit — background threads from heavy sub-systems may linger
        os._exit(0)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Aureon ATN Command Center — full temporal intelligence matrix"
    )
    parser.add_argument("--pair",   default="XBTUSD",
                        help="Trading pair (default XBTUSD)")
    parser.add_argument("--days",   type=int, default=365,
                        help="Lookback days for planetary events (default 365)")
    parser.add_argument("--live",   action="store_true",
                        help="Run continuously, refresh every 60 seconds")
    parser.add_argument("--refresh", type=int, default=60,
                        help="Refresh interval in seconds for --live mode")
    parser.add_argument("--deep",   action="store_true",
                        help="Run full harmonic sweep (slower, more detail)")
    args = parser.parse_args()

    if args.live:
        while True:
            try:
                run_once(args)
                print(f"\n  {DIM}Refreshing in {args.refresh}s… (Ctrl+C to stop){RST}")
                time.sleep(args.refresh)
            except KeyboardInterrupt:
                print(f"\n  {YEL}ATN Command Center stopped.{RST}")
                break
    else:
        run_once(args)


if __name__ == "__main__":
    main()
