#!/usr/bin/env python3
# Windows UTF-8 fix - MANDATORY for all Aureon modules
import sys, os
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        def _is_utf8_wrapper(stream):
            """Check if stream is already a UTF-8 TextIOWrapper."""
            return (isinstance(stream, io.TextIOWrapper) and 
                    hasattr(stream, 'encoding') and stream.encoding and
                    stream.encoding.lower().replace('-', '') == 'utf8')
        # Only wrap if not already UTF-8 wrapped (prevents re-wrapping on import)
        if hasattr(sys.stdout, 'buffer') and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        if hasattr(sys.stderr, 'buffer') and not _is_utf8_wrapper(sys.stderr):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

"""
🔭🤖 AUREON BOT SHAPE SCANNER 🤖🔭
═══════════════════════════════════════════════════════════════════════════════
QUANTUM TELESCOPE FOR MARKET MICROSTRUCTURE
"See the shape of the bots traveling across the market"

This module visualizes algorithmic actors by decomposing market data into
spectral 3D fingerprints. It handles the "small to big" logic (micro to whale).

PRINCIPLES:
1. FREQUENCY DECOMPOSITION: Bots operate on loops. loops = frequencies.
2. 3D SHAPE CONSTRUCTION: Time x Frequency x Magnitude = The Bot's Shape.
3. SCALAR INVARIANCE: Small HFTs and Giant Whales share geometric properties.

OUTPUTS:
- `bot.shape.3d` (ThoughtBus)
- JSON Snapshots (for visualization)
- 3D Point Cloud Data (PLY/OBJ)

Gary Leckey | January 2026
═══════════════════════════════════════════════════════════════════════════════
"""

import os
import time
import json
import logging
import numpy as np
import math
from datetime import datetime
from collections import deque, defaultdict
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple

# Internal imports
from binance_ws_client import BinanceWebSocketClient, WSTrade, WSOrderBook
try:
    from aureon_thought_bus import ThoughtBus, Thought
    THOUGHT_BUS_AVAILABLE = True
except ImportError:
    THOUGHT_BUS_AVAILABLE = False
    ThoughtBus = None

# Chirp Bus - High Speed Signaling
try:
    from aureon_chirp_bus import ChirpBus
    CHIRP_BUS_AVAILABLE = True
except ImportError:
    CHIRP_BUS_AVAILABLE = False
    ChirpBus = None

# Counter-intelligence integration
try:
    from aureon_queen_counter_intelligence import queen_counter_intelligence, CounterIntelligenceSignal
    from aureon_global_firm_intelligence import get_attribution_engine
    COUNTER_INTELLIGENCE_AVAILABLE = True
except ImportError:
    COUNTER_INTELLIGENCE_AVAILABLE = False
    queen_counter_intelligence = None
    get_attribution_engine = None

# Firm intelligence catalog
try:
    from aureon_firm_intelligence_catalog import get_firm_catalog
    CATALOG_AVAILABLE = True
except ImportError:
    CATALOG_AVAILABLE = False
    get_firm_catalog = None

# Configuration
SPECTRUM_SCAN_INTERVAL = 5.0  # seconds between Shape refreshes

@dataclass
class SpectrumBandConfig:
    name: str # e.g. "INFRA_LOW"
    min_hz: float
    max_hz: float
    window_seconds: int
    sample_rate_ms: int # 0 for burst analysis
    description: str

# 🌈 THE FULL SPECTRUM (0.001 Hz to 10 MHz) 🌈
SPECTRUM_BANDS = [
    SpectrumBandConfig("INFRA_LOW", 0.001, 0.1, 7200, 10000, "Deep Ocean (Accumulators) 🌊"), 
    SpectrumBandConfig("MID_RANGE", 0.1, 10.0, 600, 100, "Surface Waves (Market Makers) 🏄"), 
    SpectrumBandConfig("HIGH_FREQ", 10.0, 1000.0, 60, 1, "The Rain (HFT/Scalpers) 🌧️"), 
    SpectrumBandConfig("ULTRA_HIGH", 1000.0, 10_000_000.0, 10, 0, "Quantum Foam (Flash Microwaves) ⚛️") 
]

logger = logging.getLogger("BotShapeScanner")
logging.basicConfig(level=logging.INFO)

@dataclass
class SpectralBandResult:
    band_name: str
    dominant_freq: float
    amplitude: float
    activity_score: float
    state_description: str # "Active", "Sleeping", "Spiking"

@dataclass
class BotShapeFingerprint:
    """The spectral DNA of an algorithmic actor"""
    symbol: str
    timestamp: float
    spectrum_results: List[SpectralBandResult] # Full spectrum breakdown
    volume_profile: List[float]  # Normalized volume buckets
    layering_score: float        # From depth (0.0 - 1.0)
    bot_class: str               # "HFT", "MM", "ACCUMULATOR", "ARBITRAGE"
    confidence: float
    
    @property
    def dominant_freqs(self) -> List[float]:
        # Backwards compatibility helper
        return [r.dominant_freq for r in self.spectrum_results if r.dominant_freq > 0]

class BotShapeScanner:
    def __init__(self, symbols: List[str]):
        self.symbols = symbols
        self.ws_client = BinanceWebSocketClient()
        
        # Buffers: symbol -> deque of (timestamp, price, quantity)
        # We need a large buffer to cover the INFRA_LOW band (2 hours)
        # Even at 10 trades/sec, 2 hours = 72,000 trades. 
        self.trade_buffers: Dict[str, deque] = {s: deque(maxlen=100000) for s in symbols}
        self.depth_snapshot: Dict[str, WSOrderBook] = {}
        
        # ThoughtBus
        self.bus = ThoughtBus() if THOUGHT_BUS_AVAILABLE else None
        
        # ChirpBus
        self.chirp_bus = None
        if CHIRP_BUS_AVAILABLE:
            try:
                self.chirp_bus = ChirpBus()
            except Exception:
                pass
        
        # Counter-intelligence integration
        self.attribution_engine = get_attribution_engine() if COUNTER_INTELLIGENCE_AVAILABLE else None
        self.counter_intelligence = queen_counter_intelligence if COUNTER_INTELLIGENCE_AVAILABLE else None
        
        # Firm intelligence catalog
        self.firm_catalog = get_firm_catalog() if CATALOG_AVAILABLE else None
        
        # Analysis State
        self.last_scan_time = 0
        self.scan_interval = SPECTRUM_SCAN_INTERVAL
        
        if COUNTER_INTELLIGENCE_AVAILABLE:
            logger.info("🤖 Counter-intelligence integration enabled")
        else:
            logger.warning("⚠️ Counter-intelligence not available - attribution disabled")
        
        if CATALOG_AVAILABLE:
            logger.info("📊 Firm Intelligence Catalog enabled")
        else:
            logger.warning("⚠️ Catalog not available - no firm tracking")
        
    def start(self):
        """Start the Quantum Telescope"""
        logger.info(f"🔭 Starting AUREON BOT SHAPE SCANNER on {len(self.symbols)} assets...")
        
        # Build streams: trades, depth, tickers
        # Use lowercase for subscription params
        streams = []
        for s in self.symbols:
            sl = s.lower()
            streams.append(f"{sl}@trade")
            streams.append(f"{sl}@depth5") # Light depth for layering analysis
            
        # Hook up callbacks
        self.ws_client.on_trade = self._on_trade
        self.ws_client.on_depth = self._on_depth
        
        self.ws_client.start(streams)
        
        # Main Loop
        try:
            while True:
                time.sleep(0.1)
                now = time.time()
                if now - self.last_scan_time > self.scan_interval:
                    self._scan_all_shapes()
                    self.last_scan_time = now
                    
        except KeyboardInterrupt:
            logger.info("👋 Scaling down Bot Shape Scanner...")
            self.ws_client.stop()

    def _on_trade(self, trade: WSTrade):
        """Buffer incoming trades for spectral analysis"""
        # Store as (ts, price, qty, is_maker)
        # We use trade.timestamp.timestamp() for epoch
        ts = trade.timestamp.timestamp()
        
        # Normalize symbol case just in case
        sym = trade.symbol.upper()
        
        if sym in self.trade_buffers:
            self.trade_buffers[sym].append({
                'ts': ts,
                'px': trade.price,
                'qty': trade.quantity,
                'maker': trade.is_buyer_maker
            })
            
            # Prune? No, let deque handle maxlen. 
            # We need deep history for INFRA_LOW band.

    def _on_depth(self, depth: WSOrderBook):
        """Update depth snapshot for layering metrics"""
        self.depth_snapshot[depth.symbol] = depth

    def _scan_all_shapes(self):
        """Process all buffers and compute 3D shapes"""
        shapes = []
        
        logger.info("🔎 SCANNING BOT SPECTRUM (0.001Hz - 10MHz)...")
        logger.info(f"{'SYMBOL':<8} {'BAND':<12} {'FREQ (Hz)':<10} {'STATE':<15} {'SHAPE'}")
        logger.info("-" * 65)
        
        for symbol in self.symbols:
            fingerprint = self._compute_full_spectrum_fingerprint(symbol)
            if fingerprint:
                shapes.append(fingerprint)
                self._emit_shape(fingerprint)
                
                # Visual log - show the "hottest" band
                active_bands = sorted(fingerprint.spectrum_results, key=lambda x: x.amplitude, reverse=True)
                top_band = active_bands[0] if active_bands else None
                
                if top_band:
                    freq_str = f"{top_band.dominant_freq:.3f}"
                    icon = "🤖" 
                    if fingerprint.bot_class == "ORGANIC": icon = "🌱"
                    elif fingerprint.bot_class == "QUANTUM_HFT": icon = "⚡"
                    
                    logger.info(f"{symbol:<8} {top_band.band_name[:10]:<12} {freq_str:<10} {top_band.state_description[:15]:<15} {icon}")

        # Save snapshot for external 3D viewer
        self._save_3d_snapshot(shapes)

    def _compute_full_spectrum_fingerprint(self, symbol: str) -> Optional[BotShapeFingerprint]:
        """The core 'Quantum Telescope' Logic: Full Spectrum Analysis"""
        buffer = self.trade_buffers.get(symbol)
        if not buffer or len(buffer) < 20: # Minimal data check
            return None
            
        data = list(buffer) # Copy for thread safety/stability
        now = time.time()
        
        results = []
        
        # Iterate through all spectral bands
        for band in SPECTRUM_BANDS:
            res = self._analyze_band(data, band, now)
            results.append(res)
            
        # Classify based on the full spectrum
        bot_class = self._classify_spectrum(results)
        
        # Layering analysis
        layering = self._analyze_layering(symbol)

        return BotShapeFingerprint(
            symbol=symbol,
            timestamp=now,
            spectrum_results=results,
            volume_profile=[], # TODO: Add volume profile buckets
            layering_score=layering,
            bot_class=bot_class,
            confidence=0.85 
        )

    def _analyze_band(self, data: List[Dict], band: SpectrumBandConfig, now: float) -> SpectralBandResult:
        """Analyze a specific frequency band"""
        # Filter data for this band's time window
        start_time = now - band.window_seconds
        
        # Optimization: Binary search or just skip
        # Since data is sorted by TS, we can slice efficiently
        # effective_data = [d for d in data if d['ts'] >= start_time] 
        # (Doing a simple filter for clarity, optimize if slow)
        effective_data = []
        for d in reversed(data):
            if d['ts'] < start_time:
                break
            effective_data.append(d)
        effective_data.reverse()
        
        if not effective_data:
            return SpectralBandResult(band.name, 0.0, 0.0, 0.0, "Silent")

        # --- ULTRA HIGH FREQUENCY (Burst Analysis) ---
        if band.sample_rate_ms == 0: 
            # 10 MHz equivalent -> 100ns resolution.
            # We look for "micro-bursts": multiple trades in < 1ms
            burst_count = 0
            max_burst_density = 0
            
            for i in range(1, len(effective_data)):
                dt = effective_data[i]['ts'] - effective_data[i-1]['ts']
                if dt < 0.001: # Less than 1ms separation
                    burst_count += 1
            
            # Frequency proxy: bursts per second * multiplier
            freq_proxy = (burst_count / max(1, band.window_seconds)) * 1000.0  
            amplitude = burst_count / len(effective_data) if effective_data else 0
            
            state = "Quantum Calm"
            if freq_proxy > 1000: state = "SINGULARITY ⚛️"
            elif freq_proxy > 100: state = "Micro-Ripples"
            
            return SpectralBandResult(band.name, freq_proxy, amplitude, amplitude, state)

        # --- HIGH FREQ (Inter-arrival Analysis) ---
        elif band.sample_rate_ms <= 10:
             # Fast FFT or Inter-arrival
             # For High Freq, FFT on 1ms grid is expensive.
             # Use inter-arrival times stats.
             deltas = []
             for i in range(1, len(effective_data)):
                 deltas.append(effective_data[i]['ts'] - effective_data[i-1]['ts'])
             
             if not deltas:
                 return SpectralBandResult(band.name, 0.0, 0.0, 0.0, "Silent")
                 
             mean_delta = np.mean(deltas)
             if mean_delta > 0:
                 approx_freq = 1.0 / mean_delta
             else:
                 approx_freq = 0.0
                 
             state = "Drizzle"
             if approx_freq > 50: state = "Heavy Rain 🌧️"
             
             return SpectralBandResult(band.name, approx_freq, 0.5, 0.5, state)

        # --- MID & LOW (Standard FFT) ---
        else:
            return self._perform_fft_analysis(effective_data, band, now)

    def _perform_fft_analysis(self, data: List[Dict], band: SpectrumBandConfig, now: float) -> SpectralBandResult:
        """Standard FFT for Mid/Low bands"""
        if len(data) < 10:
             return SpectralBandResult(band.name, 0.0, 0.0, 0.0, "Insufficient Data")

        # Resample to uniform grid
        grid_points = int(band.window_seconds * (1000 / band.sample_rate_ms))
        signal = np.zeros(grid_points)
        start_time = now - band.window_seconds
        sample_period_sec = band.sample_rate_ms / 1000.0
        
        for t in data:
            idx = int((t['ts'] - start_time) / sample_period_sec)
            if 0 <= idx < grid_points:
                signal[idx] += t['qty']
                
        # Remove DC
        if np.all(signal == 0):
             return SpectralBandResult(band.name, 0.0, 0.0, 0.0, "Flatline")
             
        signal_centered = signal - np.mean(signal)
        
        # FFT
        fft_vals = np.fft.rfft(signal_centered)
        fft_freq = np.fft.rfftfreq(len(signal_centered), d=sample_period_sec)
        magnitudes = np.abs(fft_vals)
        
        # Filter for band range
        mask = (fft_freq >= band.min_hz) & (fft_freq <= band.max_hz)
        band_freqs = fft_freq[mask]
        band_mags = magnitudes[mask]
        
        if len(band_mags) == 0:
             return SpectralBandResult(band.name, 0.0, 0.0, 0.0, "Quiet")
             
        peak_idx = np.argmax(band_mags)
        dom_freq = band_freqs[peak_idx]
        peak_amp = band_mags[peak_idx]
        
        # Normalize amp
        norm_amp = peak_amp / (np.sum(signal) + 1e-9) * 100.0
        
        state = "Normal"
        if norm_amp > 0.5: state = "High Coherence 🌊"
        if norm_amp > 1.0: state = "STANDING WAVE ⚠️"
        
        return SpectralBandResult(band.name, dom_freq, norm_amp, norm_amp, state)

    def _analyze_layering(self, symbol: str) -> float:
        """Analyze Order Book Layering"""
        if symbol not in self.depth_snapshot:
            return 0.0
        depth = self.depth_snapshot[symbol]
        # Simple metric: how uniform are the bid/ask steps?
        bids = [p for p, q in depth.bids[:5]]
        asks = [p for p, q in depth.asks[:5]]
        bid_diffs = np.diff(bids) if len(bids) > 1 else []
        ask_diffs = np.diff(asks) if len(asks) > 1 else []
        
        if len(bid_diffs) == 0 or len(ask_diffs) == 0:
            return 0.0
            
        bid_var = np.var(bid_diffs)
        ask_var = np.var(ask_diffs)
        
        # Lower variance = higher layering score (artificial uniformity)
        # Avoid div by zero
        return 1.0 / (1.0 + (bid_var + ask_var)*10000)

    def _classify_spectrum(self, results: List[SpectralBandResult]) -> str:
        """Determine Bot Class from Spectral Fingerprint"""
        # Find strongest band
        sorted_bands = sorted(results, key=lambda x: x.amplitude, reverse=True)
        if not sorted_bands or sorted_bands[0].amplitude < 0.01:
            return "ORGANIC"
        
        strongest = sorted_bands[0]
        
        if strongest.band_name == "ULTRA_HIGH":
            return "QUANTUM_HFT"
        elif strongest.band_name == "HIGH_FREQ":
            return "SCALPER_BOT"
        elif strongest.band_name == "MID_RANGE":
            return "MARKET_MAKER"
        elif strongest.band_name == "INFRA_LOW":
            return "WHALE_ACCUMULATOR"
            
        return "UNKNOWN_ENTITY"

    def _emit_shape(self, shape: BotShapeFingerprint):
        """Emit ThoughtBus pulse and analyze for counter-intelligence opportunities"""
        if self.bus:
            self.bus.think(
                f"Bot Shape Detected: {shape.symbol} ({shape.bot_class})",
                topic="bot.shape",
                priority="high" if "HFT" in shape.bot_class else "normal",
                metadata=asdict(shape)
            )
        
        # Counter-intelligence analysis
        if self.attribution_engine and self.counter_intelligence:
            self._analyze_counter_intelligence(shape)

    def _analyze_counter_intelligence(self, shape: BotShapeFingerprint):
        """Analyze bot shape for counter-intelligence opportunities"""
        try:
            # Extract bot characteristics for attribution
            primary_freq = shape.dominant_freqs[0] if shape.dominant_freqs else 0.0
            
            # Estimate order size from volume profile (rough approximation)
            buffer = self.trade_buffers.get(shape.symbol, [])
            if buffer:
                recent_trades = list(buffer)[-10:]  # Last 10 trades
                avg_order_size = sum(t['qty'] * t['px'] for t in recent_trades) / len(recent_trades)
            else:
                avg_order_size = 100_000  # Default assumption
            
            # Get current UTC hour
            current_hour_utc = int(time.gmtime(time.time()).tm_hour)
            
            # Attempt firm attribution
            attribution_matches = self.attribution_engine.attribute_bot_to_firm(
                symbol=shape.symbol,
                frequency=primary_freq,
                order_size_usd=avg_order_size,
                strategy=shape.bot_class.split('_')[0],  # Extract base strategy
                current_hour_utc=current_hour_utc
            )
            
            if attribution_matches:
                top_match = attribution_matches[0]
                firm_id, confidence = top_match
                
                if confidence >= 0.7:  # High confidence threshold
                    logger.info(f"🎯 Attributed {shape.symbol} bot to {firm_id} (confidence: {confidence:.2f})")
                    
                    # Prepare market data for counter-analysis
                    market_data = self._prepare_market_data(shape.symbol)
                    bot_detection_data = {
                        'confidence': shape.confidence,
                        'bot_class': shape.bot_class,
                        'frequency': primary_freq,
                        'layering_score': shape.layering_score
                    }
                    
                    # Analyze for counter-opportunity
                    counter_signal = self.counter_intelligence.analyze_firm_for_counter_opportunity(
                        firm_id=firm_id,
                        market_data=market_data,
                        bot_detection_data=bot_detection_data
                    )
                    
                    if counter_signal:
                        # Emit counter-intelligence signal
                        self._emit_counter_signal(counter_signal)
                        
                        # Add to active signals
                        self.counter_intelligence.active_counters.append(counter_signal)
                        
        except Exception as e:
            logger.error(f"Counter-intelligence analysis failed: {e}")

    def _prepare_market_data(self, symbol: str) -> Dict:
        """Prepare market data snapshot for counter-analysis"""
        market_data = {
            'symbol': symbol,
            'volatility': 0.5,  # Placeholder - would calculate from price movements
            'volume_ratio': 1.0,  # Placeholder - would calculate from volume
            'spread_pips': 2.0,  # Placeholder - would get from order book
            'average_latency_ms': 50.0  # Placeholder - would measure actual latency
        }
        
        # Try to get real data from buffers
        buffer = self.trade_buffers.get(symbol, [])
        if buffer:
            # Calculate simple volatility from recent trades
            prices = [t['px'] for t in buffer]
            if len(prices) > 10:
                returns = [abs(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
                market_data['volatility'] = sum(returns) / len(returns)
        
        # Try to get spread from depth
        if symbol in self.depth_snapshot:
            depth = self.depth_snapshot[symbol]
            if depth.bids and depth.asks:
                spread = depth.asks[0][0] - depth.bids[0][0]
                market_data['spread_pips'] = spread * 10000  # Convert to pips (assuming crypto)
        
        return market_data

    def _emit_counter_signal(self, signal: CounterIntelligenceSignal):
        """Emit counter-intelligence signal via ThoughtBus and Queen consultation"""
        # ThoughtBus emission
        if self.bus:
            self.bus.think(
                f"Counter-Intelligence: {signal.firm_id} ({signal.strategy.value})",
                topic="counter.intelligence",
                priority="critical" if signal.confidence > 0.9 else "high",
                metadata={
                    'firm_id': signal.firm_id,
                    'strategy': signal.strategy.value,
                    'confidence': signal.confidence,
                    'timing_advantage': signal.timing_advantage,
                    'expected_profit_pips': signal.expected_profit_pips,
                    'risk_score': signal.risk_score,
                    'execution_window_seconds': signal.execution_window_seconds,
                    'reasoning': signal.reasoning
                }
            )
            
        # ChirpBus emission
        if self.chirp_bus:
            self.chirp_bus.publish("counter.signal", {
                "firm": signal.firm_id,
                "strat": signal.strategy.value,
                "conf": signal.confidence,
                "pips": signal.expected_profit_pips
            })
        
        # 👑 QUEEN CONSULTATION - Send counter-signal to Queen for approval
        # (Would be wired externally if Queen is available)
        try:
            # Look for global queen instance
            from aureon_queen_hive_mind import QueenHiveMind
            if hasattr(QueenHiveMind, '_global_instance') and QueenHiveMind._global_instance:
                queen = QueenHiveMind._global_instance
                if hasattr(queen, 'receive_counter_intelligence_signal'):
                    queen_decision = queen.receive_counter_intelligence_signal({
                        'firm_id': signal.firm_id,
                        'strategy': signal.strategy.value,
                        'confidence': signal.confidence,
                        'timing_advantage': signal.timing_advantage,
                        'expected_profit_pips': signal.expected_profit_pips,
                        'risk_score': signal.risk_score,
                        'execution_window_seconds': signal.execution_window_seconds,
                        'reasoning': signal.reasoning,
                        'symbol': 'UNKNOWN',
                        'source': 'bot_shape_scanner'
                    })
                    
                    if queen_decision.get('approved'):
                        logger.info(f"👑🔪 Queen APPROVED counter-hunt: {signal.firm_id}")
        except Exception:
            pass  # Queen not available - continue anyway
            
        logger.info(
            f"🚨 Counter-signal emitted: {signal.firm_id} - {signal.strategy.value} "
            f"(confidence: {signal.confidence:.2f}, timing: {signal.timing_advantage:.1f}ms)"
        )

    def _save_3d_snapshot(self, shapes: List[BotShapeFingerprint]):
        """Save a snapshot for the 3D viewer"""
        data = {
            "timestamp": time.time(),
            "shapes": [asdict(s) for s in shapes]
        }
        with open("bot_shape_snapshot.json", "w") as f:
            json.dump(data, f, indent=2)

if __name__ == "__main__":
    scan_symbols = [
        "BTCUSDT", "ETHUSDT", "SOLUSDT", 
        "XRPUSDT", "BNBUSDT", "ADAUSDT"
    ]
    scanner = BotShapeScanner(scan_symbols)
    scanner.start()
