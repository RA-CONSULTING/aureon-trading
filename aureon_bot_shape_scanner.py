#!/usr/bin/env python3
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

# Configuration
WINDOW_SIZE = 600       # 10 minutes of buffer for analysis
FFT_SAMPLE_RATE = 100   # 100ms resampling grid (10Hz)
MIN_TRADES_FOR_FFT = 50 # Minimum trades to attempt spectral analysis

logger = logging.getLogger("BotShapeScanner")
logging.basicConfig(level=logging.INFO)

@dataclass
class BotShapeFingerprint:
    """The spectral DNA of an algorithmic actor"""
    symbol: str
    timestamp: float
    dominant_freqs: List[float]  # Hz
    amplitudes: List[float]      # Magnitude
    volume_profile: List[float]  # Normalized volume buckets
    layering_score: float        # From depth (0.0 - 1.0)
    bot_class: str               # "HFT", "MM", "ACCUMULATOR", "ARBITRAGE"
    confidence: float

class BotShapeScanner:
    def __init__(self, symbols: List[str]):
        self.symbols = symbols
        self.ws_client = BinanceWebSocketClient()
        
        # Buffers: symbol -> deque of (timestamp, price, quantity)
        self.trade_buffers: Dict[str, deque] = {s: deque(maxlen=10000) for s in symbols}
        self.depth_snapshot: Dict[str, WSOrderBook] = {}
        
        # ThoughtBus
        self.bus = ThoughtBus() if THOUGHT_BUS_AVAILABLE else None
        
        # Analysis State
        self.last_scan_time = 0
        self.scan_interval = 5.0  # seconds between Shape refreshes
        
    def start(self):
        """Start the Quantum Telescope"""
        print(f"🔭 Starting AUREON BOT SHAPE SCANNER on {len(self.symbols)} assets...")
        
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
            print("\n👋 Scaling down Bot Shape Scanner...")
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
            
            # Prune old data (keep WINDOW_SIZE seconds)
            while self.trade_buffers[sym] and (ts - self.trade_buffers[sym][0]['ts'] > WINDOW_SIZE):
                self.trade_buffers[sym].popleft()

    def _on_depth(self, depth: WSOrderBook):
        """Update depth snapshot for layering metrics"""
        self.depth_snapshot[depth.symbol] = depth

    def _scan_all_shapes(self):
        """Process all buffers and compute 3D shapes"""
        shapes = []
        
        print("\n🔎 SCANNING BOT FREQUENCIES...")
        print(f"{'SYMBOL':<10} {'DOM FREQ':<12} {'ACTICITY':<10} {'CLASS':<15} {'SHAPE'}")
        print("-" * 65)
        
        for symbol in self.symbols:
            fingerprint = self._compute_fingerprint(symbol)
            if fingerprint:
                shapes.append(fingerprint)
                self._emit_shape(fingerprint)
                
                # Visual log
                freq_str = f"{fingerprint.dominant_freqs[0]:.2f}Hz" if fingerprint.dominant_freqs else "---"
                icon = "🤖" if fingerprint.bot_class != "HUMAN" else "👤"
                print(f"{symbol:<10} {freq_str:<12} {len(self.trade_buffers[symbol]):<10} {fingerprint.bot_class:<15} {icon}")

        # Save snapshot for external 3D viewer
        self._save_3d_snapshot(shapes)

    def _compute_fingerprint(self, symbol: str) -> Optional[BotShapeFingerprint]:
        """The core 'Quantum Telescope' Logic: FFT + Feature Extraction"""
        buffer = self.trade_buffers.get(symbol)
        if not buffer or len(buffer) < MIN_TRADES_FOR_FFT:
            return None
            
        data = list(buffer)
        now = time.time()
        
        # 1. Resample to uniform time grid (10Hz = 100ms)
        # We create a signal of 'volume traded per 100ms'
        grid_points = int(WINDOW_SIZE * (1000 / FFT_SAMPLE_RATE)) # 600 * 10
        signal = np.zeros(grid_points)
        
        start_time = now - WINDOW_SIZE
        
        for t in data:
            ts = t['ts']
            if ts < start_time: continue
            
            # Map time to index
            idx = int((ts - start_time) / (FFT_SAMPLE_RATE / 1000.0))
            if 0 <= idx < grid_points:
                signal[idx] += t['qty']
                
        # 2. FFT Analysis
        # Remove DC component (mean) to see fluctuations only
        signal_centered = signal - np.mean(signal)
        
        # Perform FFT
        fft_vals = np.fft.rfft(signal_centered)
        fft_freq = np.fft.rfftfreq(len(signal_centered), d=(FFT_SAMPLE_RATE/1000.0))
        
        magnitudes = np.abs(fft_vals)
        
        # 3. Find Dominant Frequencies (Peaks)
        # Simple peak finding: indices where val is larger than neighbors and > threshold
        threshold = np.max(magnitudes) * 0.2
        peaks = []
        for i in range(1, len(magnitudes)-1):
            if magnitudes[i] > magnitudes[i-1] and magnitudes[i] > magnitudes[i+1]:
                if magnitudes[i] > threshold:
                    peaks.append((fft_freq[i], magnitudes[i]))
                    
        peaks.sort(key=lambda x: x[1], reverse=True)
        top_freqs = [p[0] for p in peaks[:3]]
        top_amps = [p[1] for p in peaks[:3]]
        
        # 4. Analyze Order Book Layering
        layering = 0.0
        if symbol in self.depth_snapshot:
            depth = self.depth_snapshot[symbol]
            # Simple metric: how uniform are the bid/ask steps?
            # High uniformity / precise spacing = Bot
            # Random spacing = Organic
            bids = [p for p, q in depth.bids[:5]]
            asks = [p for p, q in depth.asks[:5]]
            bid_diffs = np.diff(bids)
            ask_diffs = np.diff(asks)
            
            bid_var = np.var(bid_diffs) if len(bid_diffs) > 0 else 1
            ask_var = np.var(ask_diffs) if len(ask_diffs) > 0 else 1
            
            # Lower variance = higher layering score
            layering = 1.0 / (1.0 + (bid_var + ask_var)*10000)

        # 5. Classify Bot
        bot_class = "UNKNOWN"
        if not top_freqs:
            bot_class = "ORGANIC/LOW_VOL"
        else:
            primary_freq = top_freqs[0]
            if primary_freq > 1.0: # Faster than 1Hz
                bot_class = "HFT_ALGO"
            elif 0.1 < primary_freq <= 1.0:
                bot_class = "MM_SPOOF"
            else: # Very slow periodicity
                bot_class = "ACCUMULATION_BOT"
                
            if layering > 0.8:
                bot_class += "_LAYERED"
                
        return BotShapeFingerprint(
            symbol=symbol,
            timestamp=now,
            dominant_freqs=top_freqs,
            amplitudes=top_amps,
            volume_profile=[], # TODO: Add volume profile buckets
            layering_score=layering,
            bot_class=bot_class,
            confidence=0.85 # Placeholder
        )

    def _emit_shape(self, shape: BotShapeFingerprint):
        """Emit ThoughtBus pulse"""
        if self.bus:
            self.bus.think(
                f"Bot Shape Detected: {shape.symbol} ({shape.bot_class})",
                topic="bot.shape",
                priority="high" if "HFT" in shape.bot_class else "normal",
                metadata=asdict(shape)
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
