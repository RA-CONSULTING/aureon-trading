#!/usr/bin/env python3
"""
🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥
║                                                                               ║
║   👁️ AUREON REAL-TIME SURVEILLANCE SYSTEM 👁️                                 ║
║                                                                               ║
║   "WATCH THEM MOVE OUR MONEY IN REAL-TIME"                                   ║
║                                                                               ║
║   Prime Sentinel: Gary Leckey 02.11.1991                                     ║
║   Keeper of the Flame - Unchained and Unbroken                               ║
║                                                                               ║
║   Features:                                                                   ║
║   - Live market data streaming (Binance, Kraken, Alpaca)                     ║
║   - Spectrogram visualization (frequency domain analysis)                    ║
║   - Buy/Sell flow tracking (who's moving what)                               ║
║   - Bot detection overlay (identify MICROSTRATEGY_BOT patterns)              ║
║   - Manipulation alert system (0.0° phase sync detection)                    ║
║                                                                               ║
║   WE ARE WATCHING. THE DATA DOESN'T LIE.                                     ║
║                                                                               ║
🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
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

import json
import time
import math
import asyncio
import threading
import logging
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Callable
from collections import deque
from pathlib import Path

# Sacred constants
PHI = (1 + math.sqrt(5)) / 2  # 1.618 Golden ratio
SCHUMANN = 7.83  # Hz - Earth resonance
LOVE_FREQ = 528  # Hz - DNA repair

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class MarketTick:
    """Single market data point"""
    symbol: str
    price: float
    bid: float
    ask: float
    volume: float
    timestamp: float
    exchange: str
    side: Optional[str] = None  # 'buy' or 'sell'
    size: Optional[float] = None
    
@dataclass
class SpectrogramBin:
    """Frequency bin for spectrogram"""
    frequency: float
    amplitude: float
    phase: float
    timestamp: float
    
@dataclass
class BotSignature:
    """Detected bot pattern"""
    bot_type: str
    confidence: float
    cycle_hours: float
    phase_sync: float
    last_seen: float
    exchange: str
    symbol: str
    
@dataclass  
class ManipulationAlert:
    """Real-time manipulation detection"""
    alert_type: str  # 'phase_sync', 'volume_spike', 'coordinated_move'
    severity: float  # 0-1
    symbols: List[str]
    exchanges: List[str]
    description: str
    timestamp: float
    evidence: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FlowEvent:
    """Buy/Sell flow event"""
    symbol: str
    exchange: str
    side: str  # 'buy' or 'sell'
    size: float
    price: float
    value_usd: float
    timestamp: float
    is_whale: bool = False  # >$100k
    bot_attributed: Optional[str] = None

# ═══════════════════════════════════════════════════════════════════════════════
# SPECTROGRAM ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class SpectrogramEngine:
    """
    Convert price movements into frequency domain.
    Reveals hidden cycles and bot patterns.
    """
    
    def __init__(self, window_size: int = 256):
        self.window_size = window_size
        self.price_buffer: Dict[str, deque] = {}  # symbol -> prices
        self.spectrogram_data: Dict[str, List[SpectrogramBin]] = {}
        
        # Known bot frequencies (hours converted to Hz for display)
        self.bot_frequencies = {
            8.0: "FUNDING_RATE_BOT",
            24.0: "SOLAR_CLOCK_BOT", 
            167.0: "WEEKEND_WHALE_BOT",
            4.0: "HIGH_FREQ_SCALPER",
            1.0: "MINUTE_MAKER_BOT"
        }
        
    def add_price(self, symbol: str, price: float, timestamp: float):
        """Add price to buffer and compute spectrogram"""
        if symbol not in self.price_buffer:
            self.price_buffer[symbol] = deque(maxlen=self.window_size)
            self.spectrogram_data[symbol] = []
            
        self.price_buffer[symbol].append((price, timestamp))
        
        # Compute FFT when we have enough data
        if len(self.price_buffer[symbol]) >= 64:
            self._compute_fft(symbol)
            
    def _compute_fft(self, symbol: str):
        """Compute Fast Fourier Transform on price data"""
        prices = [p[0] for p in self.price_buffer[symbol]]
        n = len(prices)
        
        # Simple DFT implementation (no numpy dependency)
        spectrum = []
        for k in range(n // 2):
            real_sum = 0
            imag_sum = 0
            for t in range(n):
                angle = 2 * math.pi * k * t / n
                # Detrend: subtract mean
                detrended = prices[t] - sum(prices) / n
                real_sum += detrended * math.cos(angle)
                imag_sum -= detrended * math.sin(angle)
            
            amplitude = math.sqrt(real_sum**2 + imag_sum**2) / n
            phase = math.atan2(imag_sum, real_sum)
            frequency = k  # Bin index (relates to cycle period)
            
            spectrum.append(SpectrogramBin(
                frequency=frequency,
                amplitude=amplitude,
                phase=math.degrees(phase),
                timestamp=time.time()
            ))
            
        self.spectrogram_data[symbol] = spectrum
        
    def get_dominant_frequencies(self, symbol: str, top_n: int = 5) -> List[SpectrogramBin]:
        """Get the strongest frequency components"""
        if symbol not in self.spectrogram_data:
            return []
        spectrum = sorted(self.spectrogram_data[symbol], 
                         key=lambda x: x.amplitude, reverse=True)
        return spectrum[:top_n]
    
    def detect_bot_frequencies(self, symbol: str) -> List[Dict]:
        """Check if any known bot frequencies are dominant"""
        detections = []
        dominant = self.get_dominant_frequencies(symbol, top_n=10)
        
        for freq_bin in dominant:
            for bot_freq, bot_name in self.bot_frequencies.items():
                # Check if this bin matches a known bot frequency
                if abs(freq_bin.frequency - bot_freq) < 0.5:
                    detections.append({
                        "bot": bot_name,
                        "frequency": freq_bin.frequency,
                        "amplitude": freq_bin.amplitude,
                        "phase": freq_bin.phase,
                        "confidence": min(freq_bin.amplitude * 10, 1.0)
                    })
        return detections

# ═══════════════════════════════════════════════════════════════════════════════
# FLOW TRACKER
# ═══════════════════════════════════════════════════════════════════════════════

class FlowTracker:
    """
    Track buy/sell flows in real-time.
    Identify whale movements and coordinated activity.
    """
    
    WHALE_THRESHOLD_USD = 100_000
    
    def __init__(self, history_size: int = 1000):
        self.flow_history: deque = deque(maxlen=history_size)
        self.buy_volume: Dict[str, float] = {}   # symbol -> total buy volume
        self.sell_volume: Dict[str, float] = {}  # symbol -> total sell volume
        self.whale_events: List[FlowEvent] = []
        self.flow_imbalance: Dict[str, float] = {}  # symbol -> buy/sell ratio
        
        # Bot attribution patterns
        self.bot_patterns = self._load_bot_patterns()
        
    def _load_bot_patterns(self) -> Dict:
        """Load known bot trading patterns"""
        try:
            with open('bot_cultural_attribution.json', 'r') as f:
                return json.load(f)
        except:
            return {
                "MICROSTRATEGY_BOT": {
                    "peak_hours": [13, 14, 15, 16],
                    "typical_size_btc": 0.5,
                    "exchange_preference": ["binance", "kraken"]
                }
            }
            
    def record_flow(self, event: FlowEvent):
        """Record a buy/sell event"""
        self.flow_history.append(event)
        
        # Update volume trackers
        if event.side == 'buy':
            self.buy_volume[event.symbol] = self.buy_volume.get(event.symbol, 0) + event.value_usd
        else:
            self.sell_volume[event.symbol] = self.sell_volume.get(event.symbol, 0) + event.value_usd
            
        # Calculate imbalance
        buy = self.buy_volume.get(event.symbol, 0)
        sell = self.sell_volume.get(event.symbol, 0)
        if sell > 0:
            self.flow_imbalance[event.symbol] = buy / sell
        else:
            self.flow_imbalance[event.symbol] = float('inf') if buy > 0 else 1.0
            
        # Check for whale
        if event.is_whale:
            self.whale_events.append(event)
            logger.warning(f"🐋 WHALE DETECTED: {event.side.upper()} ${event.value_usd:,.0f} {event.symbol} on {event.exchange}")
            
        # Attribute to bot if pattern matches
        event.bot_attributed = self._attribute_to_bot(event)
        if event.bot_attributed:
            logger.info(f"🤖 BOT ATTRIBUTED: {event.bot_attributed} - {event.side} {event.symbol}")
            
    def _attribute_to_bot(self, event: FlowEvent) -> Optional[str]:
        """Try to attribute this trade to a known bot"""
        hour = datetime.fromtimestamp(event.timestamp, tz=timezone.utc).hour
        
        for symbol, bots in self.bot_patterns.items():
            # bot_patterns is {symbol: [list of bot dicts]}
            if not isinstance(bots, list):
                continue
            for bot in bots:
                if not isinstance(bot, dict):
                    continue
                # Check peak hours from evidence or direct field
                peak_hours = []
                if 'peak_hours' in bot:
                    peak_hours = bot['peak_hours']
                elif 'evidence' in bot:
                    for ev in bot.get('evidence', []):
                        if 'Peak trading hours' in str(ev):
                            # Parse "[13, 14, 15, 16]" from evidence string
                            import re
                            match = re.search(r'\[([0-9,\s]+)\]', str(ev))
                            if match:
                                try:
                                    peak_hours = [int(x.strip()) for x in match.group(1).split(',')]
                                except:
                                    pass
                            break
                if hour in peak_hours:
                    return bot.get('bot_name', bot.get('owner_entity', 'UNKNOWN_BOT'))
        return None
        
    def get_flow_summary(self) -> Dict:
        """Get current flow summary"""
        return {
            "buy_volume": dict(self.buy_volume),
            "sell_volume": dict(self.sell_volume),
            "imbalance": dict(self.flow_imbalance),
            "whale_count": len(self.whale_events),
            "recent_whales": [asdict(w) for w in self.whale_events[-10:]]
        }

# ═══════════════════════════════════════════════════════════════════════════════
# MANIPULATION DETECTOR  
# ═══════════════════════════════════════════════════════════════════════════════

class ManipulationDetector:
    """
    Real-time detection of market manipulation patterns.
    Based on our historical analysis of $33.5T extraction.
    """
    
    def __init__(self):
        self.alerts: List[ManipulationAlert] = []
        self.phase_history: Dict[str, List[float]] = {}  # symbol -> phases
        self.price_history: Dict[str, deque] = {}
        self.correlation_matrix: Dict[str, Dict[str, float]] = {}
        
        # Load known manipulation patterns from our research
        self.known_patterns = self._load_patterns()
        
    def _load_patterns(self) -> Dict:
        """Load known manipulation patterns"""
        return {
            "pump_and_dump": {
                "volume_spike_threshold": 5.0,  # 5x normal volume
                "price_spike_threshold": 0.05,  # 5% move
                "dump_window_hours": 4
            },
            "coordinated_movement": {
                "correlation_threshold": 0.95,
                "phase_sync_threshold": 5.0,  # degrees
                "min_symbols": 3
            },
            "whale_manipulation": {
                "size_threshold_usd": 500_000,
                "follow_window_minutes": 5
            }
        }
        
    def check_phase_sync(self, symbols: List[str], spectrogram: SpectrogramEngine) -> Optional[ManipulationAlert]:
        """Check for suspicious phase synchronization"""
        phases = {}
        for symbol in symbols:
            dominant = spectrogram.get_dominant_frequencies(symbol, top_n=1)
            if dominant:
                phases[symbol] = dominant[0].phase
                
        if len(phases) < 2:
            return None
            
        # Check if phases are suspiciously aligned
        phase_values = list(phases.values())
        phase_spread = max(phase_values) - min(phase_values)
        
        if phase_spread < self.known_patterns["coordinated_movement"]["phase_sync_threshold"]:
            alert = ManipulationAlert(
                alert_type="PHASE_SYNC_DETECTED",
                severity=1.0 - (phase_spread / 180.0),  # Higher severity for tighter sync
                symbols=list(phases.keys()),
                exchanges=["multiple"],
                description=f"🚨 PERFECT PHASE SYNC: {phase_spread:.1f}° spread across {len(phases)} symbols! This is COORDINATION!",
                timestamp=time.time(),
                evidence={
                    "phases": phases,
                    "spread_degrees": phase_spread,
                    "historical_average_spread": 45.0  # Normal would be ~45°
                }
            )
            self.alerts.append(alert)
            return alert
        return None
        
    def check_volume_spike(self, symbol: str, current_volume: float, 
                           avg_volume: float) -> Optional[ManipulationAlert]:
        """Check for suspicious volume spikes"""
        if avg_volume <= 0:
            return None
            
        spike_ratio = current_volume / avg_volume
        threshold = self.known_patterns["pump_and_dump"]["volume_spike_threshold"]
        
        if spike_ratio > threshold:
            alert = ManipulationAlert(
                alert_type="VOLUME_SPIKE",
                severity=min(spike_ratio / 10, 1.0),
                symbols=[symbol],
                exchanges=["unknown"],
                description=f"📊 VOLUME SPIKE: {symbol} at {spike_ratio:.1f}x normal volume!",
                timestamp=time.time(),
                evidence={
                    "current_volume": current_volume,
                    "average_volume": avg_volume,
                    "spike_ratio": spike_ratio
                }
            )
            self.alerts.append(alert)
            return alert
        return None
        
    def get_recent_alerts(self, count: int = 20) -> List[ManipulationAlert]:
        """Get recent manipulation alerts"""
        return self.alerts[-count:]

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN SURVEILLANCE SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

class AureonSurveillanceSystem:
    """
    THE ALL-SEEING EYE
    
    Watches them move money in real-time.
    Prime Sentinel Gary Leckey 02.11.1991 - Keeper of the Flame
    """
    
    def __init__(self):
        self.spectrogram = SpectrogramEngine()
        self.flow_tracker = FlowTracker()
        self.manipulation_detector = ManipulationDetector()
        
        # Data buffers for UI
        self.market_data: Dict[str, deque] = {}  # symbol -> recent ticks
        self.ui_callbacks: List[Callable] = []
        
        # Tracked symbols
        self.symbols = ["BTC/USD", "ETH/USD", "SOL/USD", "DOGE/USD"]
        self.exchanges = ["kraken", "binance", "alpaca"]
        
        # Statistics
        self.stats = {
            "ticks_processed": 0,
            "alerts_generated": 0,
            "whales_detected": 0,
            "bots_detected": 0,
            "start_time": time.time()
        }
        
        logger.info("👁️ AUREON SURVEILLANCE SYSTEM INITIALIZED")
        logger.info("🔥 Prime Sentinel: Gary Leckey 02.11.1991")
        logger.info("🔥 Keeper of the Flame - Unchained and Unbroken")
        
    def process_tick(self, tick: MarketTick):
        """Process incoming market data tick"""
        self.stats["ticks_processed"] += 1
        
        # Store tick
        if tick.symbol not in self.market_data:
            self.market_data[tick.symbol] = deque(maxlen=1000)
        self.market_data[tick.symbol].append(tick)
        
        # Feed to spectrogram
        self.spectrogram.add_price(tick.symbol, tick.price, tick.timestamp)
        
        # Check for bot patterns
        bot_detections = self.spectrogram.detect_bot_frequencies(tick.symbol)
        if bot_detections:
            self.stats["bots_detected"] += len(bot_detections)
            for detection in bot_detections:
                logger.warning(f"🤖 BOT PATTERN: {detection['bot']} on {tick.symbol} (confidence: {detection['confidence']:.1%})")
        
        # Record flow if trade
        if tick.side and tick.size:
            flow = FlowEvent(
                symbol=tick.symbol,
                exchange=tick.exchange,
                side=tick.side,
                size=tick.size,
                price=tick.price,
                value_usd=tick.size * tick.price,
                timestamp=tick.timestamp,
                is_whale=(tick.size * tick.price) > FlowTracker.WHALE_THRESHOLD_USD
            )
            self.flow_tracker.record_flow(flow)
            if flow.is_whale:
                self.stats["whales_detected"] += 1
                
        # Check for manipulation
        if len(self.market_data.get(tick.symbol, [])) > 50:
            alert = self.manipulation_detector.check_phase_sync(
                list(self.market_data.keys()),
                self.spectrogram
            )
            if alert:
                self.stats["alerts_generated"] += 1
                self._broadcast_alert(alert)
                
        # Notify UI
        self._notify_ui(tick)
        
    def _broadcast_alert(self, alert: ManipulationAlert):
        """Broadcast manipulation alert"""
        logger.critical(f"🚨 MANIPULATION ALERT: {alert.alert_type}")
        logger.critical(f"   Severity: {alert.severity:.1%}")
        logger.critical(f"   Symbols: {alert.symbols}")
        logger.critical(f"   {alert.description}")

        # Feed into Autonomy Hub (The Big Wheel) for unified decision making
        try:
            from aureon_autonomy_hub import get_autonomy_hub
            hub = get_autonomy_hub()
            hub.data_bridge.ingest_surveillance_alert({
                'alert_type': alert.alert_type,
                'severity': 'critical' if alert.severity > 0.7 else 'medium' if alert.severity > 0.4 else 'low',
                'symbols': alert.symbols,
                'description': alert.description,
                'exchanges': getattr(alert, 'exchanges', []),
            })
        except Exception:
            pass
        
    def _notify_ui(self, tick: MarketTick):
        """Notify UI callbacks of new data"""
        for callback in self.ui_callbacks:
            try:
                callback("tick", tick)
            except Exception as e:
                logger.error(f"UI callback error: {e}")
                
    def register_ui_callback(self, callback: Callable):
        """Register a UI callback for data updates"""
        self.ui_callbacks.append(callback)
        
    def get_spectrogram_data(self, symbol: str) -> Dict:
        """Get spectrogram data for UI"""
        spectrum = self.spectrogram.spectrogram_data.get(symbol, [])
        return {
            "symbol": symbol,
            "bins": [asdict(b) for b in spectrum],
            "dominant": [asdict(b) for b in self.spectrogram.get_dominant_frequencies(symbol)],
            "bot_detections": self.spectrogram.detect_bot_frequencies(symbol)
        }
        
    def get_flow_data(self) -> Dict:
        """Get flow data for UI"""
        return self.flow_tracker.get_flow_summary()
        
    def get_alerts(self) -> List[Dict]:
        """Get recent alerts for UI"""
        return [asdict(a) for a in self.manipulation_detector.get_recent_alerts()]
        
    def get_dashboard_data(self) -> Dict:
        """Get complete dashboard data"""
        uptime = time.time() - self.stats["start_time"]
        
        return {
            "timestamp": time.time(),
            "uptime_seconds": uptime,
            "stats": self.stats,
            "spectrograms": {s: self.get_spectrogram_data(s) for s in self.symbols},
            "flows": self.get_flow_data(),
            "alerts": self.get_alerts(),
            "market_data": {
                s: [asdict(t) for t in list(self.market_data.get(s, []))[-50:]]
                for s in self.symbols
            }
        }

# ═══════════════════════════════════════════════════════════════════════════════
# SIMULATED DATA FEED (for testing)
# ═══════════════════════════════════════════════════════════════════════════════

class SimulatedFeed:
    """Simulate market data for testing"""
    
    def __init__(self, surveillance: AureonSurveillanceSystem):
        self.surveillance = surveillance
        self.running = False
        self.base_prices = {
            "BTC/USD": 95000.0,
            "ETH/USD": 3200.0,
            "SOL/USD": 180.0,
            "DOGE/USD": 0.35
        }
        
    async def start(self):
        """Start simulated feed"""
        self.running = True
        logger.info("📡 Starting simulated market feed...")
        
        while self.running:
            for symbol, base_price in self.base_prices.items():
                # Add some randomness with bot-like patterns
                hour = datetime.now(timezone.utc).hour
                
                # Simulate bot activity during peak hours
                if hour in [13, 14, 15, 16]:
                    volatility = 0.002  # Higher volatility during bot hours
                else:
                    volatility = 0.0005
                    
                # Random walk with drift
                import random
                change = random.gauss(0, volatility)
                
                # Add periodic component (simulate bot cycles)
                t = time.time()
                bot_cycle = 0.0005 * math.sin(2 * math.pi * t / (8 * 3600))  # 8h cycle
                
                price = base_price * (1 + change + bot_cycle)
                self.base_prices[symbol] = price
                
                # Create tick
                spread = price * 0.0001
                tick = MarketTick(
                    symbol=symbol,
                    price=price,
                    bid=price - spread,
                    ask=price + spread,
                    volume=random.uniform(0.1, 10.0),
                    timestamp=time.time(),
                    exchange="simulated",
                    side=random.choice(["buy", "sell"]),
                    size=random.uniform(0.01, 1.0)
                )
                
                self.surveillance.process_tick(tick)
                
            await asyncio.sleep(0.5)  # 2 ticks per second
            
    def stop(self):
        """Stop simulated feed"""
        self.running = False

# ═══════════════════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════

def print_dashboard(surveillance: AureonSurveillanceSystem):
    """Print ASCII dashboard to terminal"""
    os.system('clear' if os.name != 'nt' else 'cls')
    
    data = surveillance.get_dashboard_data()
    uptime = data["uptime_seconds"]
    stats = data["stats"]
    
    print("=" * 80)
    print("🔥" * 30)
    print()
    print("         👁️  AUREON REAL-TIME SURVEILLANCE SYSTEM  👁️")
    print()
    print("    Prime Sentinel: Gary Leckey 02.11.1991 - Keeper of the Flame")
    print("                   UNCHAINED AND UNBROKEN")
    print()
    print("🔥" * 30)
    print("=" * 80)
    print()
    print(f"⏱️  Uptime: {uptime/60:.1f} minutes | Ticks: {stats['ticks_processed']:,}")
    print(f"🐋 Whales: {stats['whales_detected']} | 🤖 Bots: {stats['bots_detected']} | 🚨 Alerts: {stats['alerts_generated']}")
    print()
    print("-" * 80)
    print("📊 LIVE PRICES")
    print("-" * 80)
    
    for symbol in surveillance.symbols:
        ticks = list(surveillance.market_data.get(symbol, []))
        if ticks:
            latest = ticks[-1]
            prev = ticks[-2] if len(ticks) > 1 else latest
            change = ((latest.price - prev.price) / prev.price) * 100 if prev.price else 0
            arrow = "📈" if change > 0 else "📉" if change < 0 else "➡️"
            print(f"  {symbol:12} ${latest.price:>12,.2f}  {arrow} {change:+.3f}%")
            
    print()
    print("-" * 80)
    print("📡 SPECTROGRAM - DOMINANT FREQUENCIES")
    print("-" * 80)
    
    for symbol in surveillance.symbols:
        dominant = surveillance.spectrogram.get_dominant_frequencies(symbol, top_n=3)
        if dominant:
            freqs = ", ".join([f"{b.frequency:.1f}Hz" for b in dominant])
            print(f"  {symbol:12} {freqs}")
            
        bot_detect = surveillance.spectrogram.detect_bot_frequencies(symbol)
        if bot_detect:
            for bd in bot_detect:
                print(f"    🤖 {bd['bot']} detected! Confidence: {bd['confidence']:.1%}")
                
    print()
    print("-" * 80)
    print("💰 FLOW ANALYSIS")
    print("-" * 80)
    
    flows = surveillance.get_flow_data()
    for symbol in surveillance.symbols:
        buy = flows["buy_volume"].get(symbol, 0)
        sell = flows["sell_volume"].get(symbol, 0)
        imbalance = flows["imbalance"].get(symbol, 1.0)
        
        if imbalance > 1.2:
            indicator = "🟢 BUYING PRESSURE"
        elif imbalance < 0.8:
            indicator = "🔴 SELLING PRESSURE"
        else:
            indicator = "⚪ BALANCED"
            
        print(f"  {symbol:12} Buy: ${buy:>12,.0f} | Sell: ${sell:>12,.0f} | {indicator}")
        
    print()
    print("-" * 80)
    print("🚨 RECENT ALERTS")
    print("-" * 80)
    
    alerts = surveillance.get_alerts()
    if alerts:
        for alert in alerts[-5:]:
            print(f"  [{alert['alert_type']}] {alert['description'][:60]}...")
    else:
        print("  No manipulation alerts detected... yet. We're watching.")
        
    print()
    print("=" * 80)
    print("Press Ctrl+C to exit")

async def run_cli_dashboard(surveillance: AureonSurveillanceSystem):
    """Run CLI dashboard update loop"""
    while True:
        print_dashboard(surveillance)
        await asyncio.sleep(2)  # Update every 2 seconds

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    """Main entry point"""
    print()
    print("🔥" * 40)
    print()
    print("    👁️  AUREON REAL-TIME SURVEILLANCE SYSTEM  👁️")
    print()
    print("    Prime Sentinel: Gary Leckey 02.11.1991")
    print("    Keeper of the Flame - Unchained and Unbroken")
    print()
    print("    'THEY MOVE OUR MONEY. WE WATCH THEM DO IT.'")
    print()
    print("🔥" * 40)
    print()
    
    # Initialize surveillance
    surveillance = AureonSurveillanceSystem()
    
    # Start simulated feed (replace with real feed later)
    feed = SimulatedFeed(surveillance)
    
    # Run feed and dashboard concurrently
    try:
        await asyncio.gather(
            feed.start(),
            run_cli_dashboard(surveillance)
        )
    except KeyboardInterrupt:
        print("\n\n👁️ Surveillance system shutting down...")
        feed.stop()
        
        # Print final stats
        data = surveillance.get_dashboard_data()
        stats = data["stats"]
        print()
        print("=" * 60)
        print("📊 FINAL SESSION STATS")
        print("=" * 60)
        print(f"  Ticks Processed: {stats['ticks_processed']:,}")
        print(f"  Whales Detected: {stats['whales_detected']}")
        print(f"  Bots Detected: {stats['bots_detected']}")
        print(f"  Alerts Generated: {stats['alerts_generated']}")
        print()
        print("🔥 UNCHAINED AND UNBROKEN 🔥")
        print()

if __name__ == "__main__":
    asyncio.run(main())
