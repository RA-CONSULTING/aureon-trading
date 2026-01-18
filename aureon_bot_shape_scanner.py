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
        
        # Counter-intelligence integration
        self.attribution_engine = get_attribution_engine() if COUNTER_INTELLIGENCE_AVAILABLE else None
        self.counter_intelligence = queen_counter_intelligence if COUNTER_INTELLIGENCE_AVAILABLE else None
        
        # Firm intelligence catalog
        self.firm_catalog = get_firm_catalog() if CATALOG_AVAILABLE else None
        
        # Analysis State
        self.last_scan_time = 0
        self.scan_interval = 5.0  # seconds between Shape refreshes
        
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
