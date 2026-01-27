#!/usr/bin/env python3
"""
🌐🧠 AUREON REAL DATA FEED HUB 🧠🌐
====================================
CENTRAL HUB FOR DISTRIBUTING REAL INTELLIGENCE TO ALL SYSTEMS

This module:
1. Gathers real intelligence from aureon_real_intelligence_engine
2. Publishes to ThoughtBus with standardized topics
3. All 200+ systems can subscribe to get real data

Topics Published:
- intelligence.bot.*       - Bot detection & firm profiling
- intelligence.whale.*     - Validated whale predictions
- intelligence.momentum.*  - Momentum scanner opportunities
- intelligence.validated.* - Combined validated intelligence
- intelligence.summary     - Periodic summary of all intelligence

Gary Leckey & Tina Brown | January 2026 | REAL DATA DISTRIBUTION
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os

# Windows UTF-8 fix
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
    except Exception:
        pass

import time
import json
import logging
import threading
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path

logger = logging.getLogger(__name__)

# Sacred constants
PHI = 1.618033988749895
SCHUMANN = 7.83


# ═══════════════════════════════════════════════════════════════════════════════
# DATA CLASSES FOR FEED EVENTS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class BotFeedEvent:
    """Bot detection event for distribution"""
    symbol: str
    firm: str
    firm_animal: str
    bot_type: str
    confidence: float
    country: str
    estimated_capital: int
    known_strategies: List[str]
    layering_score: float
    timing_ms: int
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


@dataclass
class WhaleFeedEvent:
    """Whale prediction event for distribution"""
    symbol: str
    action: str
    side: str
    confidence: float
    size_usd: float
    coherence: float
    lambda_stability: float
    validated: bool
    validators: Dict[str, float]
    time_horizon_minutes: int
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


@dataclass
class MomentumFeedEvent:
    """Momentum opportunity event for distribution"""
    symbol: str
    scanner_type: str  # wolf, lion, ants, hummingbird
    side: str
    move_pct: float
    net_pct: float
    volume: float
    confidence: float
    reason: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


@dataclass  
class ValidatedIntelFeedEvent:
    """Combined validated intelligence event"""
    symbol: str
    recommended_action: str
    composite_score: float
    reasoning: str
    bot_count: int
    whale_count: int
    momentum_count: int
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


# ═══════════════════════════════════════════════════════════════════════════════
# REAL DATA FEED HUB
# ═══════════════════════════════════════════════════════════════════════════════

class RealDataFeedHub:
    """
    🌐 CENTRAL HUB FOR REAL INTELLIGENCE DISTRIBUTION
    
    Collects data from:
    - aureon_real_intelligence_engine (bot profiler, whale predictor, momentum scanners)
    - Market data feeds
    - ThoughtBus history
    
    Distributes to all systems via ThoughtBus topics.
    """
    
    def __init__(self):
        self.thought_bus = None
        self.intelligence_engine = None
        self.running = False
        self.feed_thread = None
        
        # Statistics
        self.bots_distributed = 0
        self.whales_distributed = 0
        self.momentum_distributed = 0
        self.intel_distributed = 0
        
        # Subscribers (direct callbacks in addition to ThoughtBus)
        self._subscribers: Dict[str, List[Callable]] = {}
        
        self._init_dependencies()
        
    def _init_dependencies(self):
        """Initialize ThoughtBus and Intelligence Engine"""
        # Get ThoughtBus
        try:
            from aureon_thought_bus import ThoughtBus
            # Use global thoughts file
            self.thought_bus = ThoughtBus(
                max_memory=5000,
                persist_path=str(Path(__file__).parent / "thoughts.jsonl")
            )
            logger.info("🌐 ThoughtBus connected for real data distribution")
        except Exception as e:
            logger.warning(f"⚠️ ThoughtBus not available: {e}")
            
        # Get Intelligence Engine
        try:
            from aureon_real_intelligence_engine import get_intelligence_engine
            self.intelligence_engine = get_intelligence_engine()
            logger.info("🧠 Real Intelligence Engine connected")
        except Exception as e:
            logger.warning(f"⚠️ Intelligence Engine not available: {e}")
    
    def subscribe(self, topic: str, callback: Callable):
        """Subscribe to a specific feed topic (direct callback)"""
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(callback)
        logger.debug(f"📡 Subscribed to {topic}")
    
    def _publish_to_bus(self, topic: str, data: Dict):
        """Publish data to ThoughtBus"""
        if self.thought_bus:
            try:
                from aureon_thought_bus import Thought
                thought = Thought(
                    source="real_data_feed_hub",
                    topic=topic,
                    payload=data
                )
                self.thought_bus.publish(thought)
            except Exception as e:
                logger.debug(f"Bus publish error: {e}")
        
        # Also notify direct subscribers
        for pattern, handlers in self._subscribers.items():
            if self._topic_matches(topic, pattern):
                for handler in handlers:
                    try:
                        handler(topic, data)
                    except Exception as e:
                        logger.debug(f"Subscriber error: {e}")
    
    def _topic_matches(self, topic: str, pattern: str) -> bool:
        """Check if topic matches pattern (supports * wildcard)"""
        if pattern == "*":
            return True
        if pattern.endswith("*"):
            return topic.startswith(pattern[:-1])
        return topic == pattern
    
    def gather_and_distribute(self, prices: Dict[str, float] = None) -> Dict[str, Any]:
        """
        Gather all intelligence and distribute to all systems.
        
        This is the main method that should be called periodically.
        Returns summary of distributed data.
        """
        if not self.intelligence_engine:
            return {"error": "Intelligence engine not available"}
        
        # Use default prices if none provided
        if not prices:
            prices = self._get_default_prices()
        
        # Gather intelligence
        try:
            intel = self.intelligence_engine.gather_all_intelligence(prices)
        except Exception as e:
            logger.error(f"Intelligence gathering error: {e}")
            return {"error": str(e)}
        
        # Distribute bot profiles
        for bp in intel.get('bot_profiles', []):
            self._distribute_bot(bp)
        
        # Distribute whale predictions
        for wp in intel.get('whale_predictions', []):
            self._distribute_whale(wp)
        
        # Distribute momentum opportunities
        for scanner_type, opps in intel.get('momentum_opportunities', {}).items():
            for opp in opps:
                self._distribute_momentum(opp, scanner_type)
        
        # Distribute validated intelligence
        for vi in intel.get('validated_intelligence', []):
            self._distribute_validated_intel(vi)
        
        # Publish summary
        summary = {
            "bots_distributed": self.bots_distributed,
            "whales_distributed": self.whales_distributed,
            "momentum_distributed": self.momentum_distributed,
            "intel_distributed": self.intel_distributed,
            "stats": intel.get('stats', {}),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        self._publish_to_bus("intelligence.summary", summary)
        
        return summary
    
    def _distribute_bot(self, bp: Dict):
        """Distribute a bot detection event"""
        event = BotFeedEvent(
            symbol=bp.get('symbol', ''),
            firm=bp.get('firm', 'Unknown'),
            firm_animal=bp.get('firm_animal', '🤖'),
            bot_type=bp.get('bot_type', 'UNKNOWN'),
            confidence=bp.get('confidence', 0),
            country=bp.get('country', 'Unknown'),
            estimated_capital=bp.get('estimated_capital', 0),
            known_strategies=bp.get('known_strategies', []),
            layering_score=bp.get('layering_score', 0),
            timing_ms=bp.get('timing_ms', 100)
        )
        
        # Publish to multiple topics for different consumers
        data = asdict(event)
        self._publish_to_bus("intelligence.bot.detected", data)
        self._publish_to_bus(f"intelligence.bot.firm.{bp.get('firm', 'unknown').lower().replace(' ', '_')}", data)
        self._publish_to_bus(f"intelligence.bot.symbol.{bp.get('symbol', '').replace('/', '_')}", data)
        
        self.bots_distributed += 1
    
    def _distribute_whale(self, wp: Dict):
        """Distribute a whale prediction event"""
        event = WhaleFeedEvent(
            symbol=wp.get('symbol', ''),
            action=wp.get('action', 'wait'),
            side="BUY" if wp.get('action', '') in ['buy', 'lean_buy'] else "SELL" if wp.get('action', '') in ['sell', 'lean_sell'] else "NEUTRAL",
            confidence=wp.get('confidence', 0),
            size_usd=wp.get('size_usd', 0),
            coherence=wp.get('coherence', 0),
            lambda_stability=wp.get('lambda_stability', 1.0),
            validated=wp.get('validated', False),
            validators=wp.get('validators', {}),
            time_horizon_minutes=wp.get('time_horizon_minutes', 30)
        )
        
        data = asdict(event)
        self._publish_to_bus("intelligence.whale.prediction", data)
        
        if event.validated:
            self._publish_to_bus("intelligence.whale.validated", data)
        
        self._publish_to_bus(f"intelligence.whale.symbol.{wp.get('symbol', '').replace('/', '_')}", data)
        
        self.whales_distributed += 1
    
    def _distribute_momentum(self, opp: Dict, scanner_type: str):
        """Distribute a momentum opportunity event"""
        event = MomentumFeedEvent(
            symbol=opp.get('symbol', ''),
            scanner_type=scanner_type,
            side=opp.get('side', 'hold'),
            move_pct=opp.get('move_pct', 0),
            net_pct=opp.get('net_pct', 0),
            volume=opp.get('volume', 0),
            confidence=opp.get('confidence', 0),
            reason=opp.get('reason', '')
        )
        
        data = asdict(event)
        self._publish_to_bus("intelligence.momentum.opportunity", data)
        self._publish_to_bus(f"intelligence.momentum.{scanner_type}", data)
        self._publish_to_bus(f"intelligence.momentum.symbol.{opp.get('symbol', '').replace('/', '_')}", data)
        
        self.momentum_distributed += 1
    
    def _distribute_validated_intel(self, vi: Dict):
        """Distribute validated intelligence event"""
        event = ValidatedIntelFeedEvent(
            symbol=vi.get('symbol', ''),
            recommended_action=vi.get('recommended_action', 'HOLD'),
            composite_score=vi.get('composite_score', 0),
            reasoning=vi.get('reasoning', ''),
            bot_count=vi.get('bot_count', 0),
            whale_count=vi.get('whale_count', 0),
            momentum_count=vi.get('momentum_count', 0)
        )
        
        data = asdict(event)
        self._publish_to_bus("intelligence.validated.signal", data)
        
        # High confidence signals get special topic
        if event.composite_score > 0.618:  # Golden ratio
            self._publish_to_bus("intelligence.validated.high_confidence", data)
        
        self._publish_to_bus(f"intelligence.validated.{event.recommended_action.lower()}", data)
        
        self.intel_distributed += 1
    
    def _get_default_prices(self) -> Dict[str, float]:
        """Get default prices from various sources"""
        prices = {
            "BTC/USD": 97500.0,
            "ETH/USD": 3400.0,
            "SOL/USD": 195.0,
            "XRP/USD": 2.50,
            "ADA/USD": 0.95,
            "DOGE/USD": 0.35,
            "AVAX/USD": 38.0,
            "DOT/USD": 7.50,
            "LINK/USD": 22.0,
            "MATIC/USD": 0.45
        }
        
        # Try to get live prices from cache
        try:
            cache_file = Path(__file__).parent / "coingecko_market_cache.json"
            if cache_file.exists():
                data = json.loads(cache_file.read_text())
                for item in data.get('data', []):
                    symbol = f"{item.get('symbol', '').upper()}/USD"
                    price = item.get('current_price', 0)
                    if price > 0:
                        prices[symbol] = price
        except:
            pass
        
        return prices
    
    def start_continuous_feed(self, interval: float = 5.0):
        """Start continuous data feed in background thread"""
        if self.running:
            return
            
        self.running = True
        
        def feed_loop():
            logger.info(f"🌐 Starting continuous real data feed (interval: {interval}s)")
            while self.running:
                try:
                    summary = self.gather_and_distribute()
                    logger.debug(f"📡 Distributed: Bots={summary.get('bots_distributed', 0)}, Whales={summary.get('whales_distributed', 0)}")
                except Exception as e:
                    logger.error(f"Feed error: {e}")
                time.sleep(interval)
        
        self.feed_thread = threading.Thread(target=feed_loop, daemon=True)
        self.feed_thread.start()
    
    def stop_feed(self):
        """Stop continuous feed"""
        self.running = False
        if self.feed_thread:
            self.feed_thread.join(timeout=2.0)


# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM WIRING HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def wire_system_to_real_data(system_name: str, callback: Callable, topics: List[str] = None):
    """
    Helper to wire any system to receive real intelligence data.
    
    Usage:
        def my_handler(topic, data):
            print(f"Got {topic}: {data}")
        
        wire_system_to_real_data("my_system", my_handler, ["intelligence.bot.*", "intelligence.whale.*"])
    """
    hub = get_feed_hub()
    
    if topics is None:
        topics = ["intelligence.*"]  # Subscribe to all intelligence
    
    for topic in topics:
        hub.subscribe(topic, callback)
    
    logger.info(f"🔗 Wired {system_name} to real data feed ({len(topics)} topics)")


def get_latest_intel_for_symbol(symbol: str) -> Dict[str, Any]:
    """Get the latest intelligence for a specific symbol"""
    hub = get_feed_hub()
    
    # Gather fresh data
    prices = {symbol: 0}  # Price will be filled by intelligence engine
    intel = hub.gather_and_distribute(prices)
    
    # Filter for this symbol
    result = {
        "symbol": symbol,
        "bots": [],
        "whales": [],
        "momentum": [],
        "validated": None
    }
    
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL FEED HUB INSTANCE
# ═══════════════════════════════════════════════════════════════════════════════

_global_hub: Optional[RealDataFeedHub] = None

def get_feed_hub() -> RealDataFeedHub:
    """Get or create the global feed hub"""
    global _global_hub
    if _global_hub is None:
        _global_hub = RealDataFeedHub()
    return _global_hub


def start_global_feed(interval: float = 5.0):
    """Start the global real data feed"""
    hub = get_feed_hub()
    hub.start_continuous_feed(interval)
    return hub


# ═══════════════════════════════════════════════════════════════════════════════
# STANDALONE TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(message)s'
    )
    
    print("\n" + "=" * 60)
    print("🌐🧠 REAL DATA FEED HUB - STANDALONE TEST")
    print("=" * 60)
    
    hub = get_feed_hub()
    
    # Test subscriber
    def test_handler(topic: str, data: Dict):
        print(f"📡 [{topic}] {data.get('symbol', '')} - {data.get('firm', data.get('action', ''))}")
    
    # Subscribe to all intelligence
    hub.subscribe("intelligence.*", test_handler)
    
    print("\n📊 Gathering and distributing real intelligence...")
    summary = hub.gather_and_distribute()
    
    print(f"\n📈 Results:")
    print(f"   Bots distributed: {summary.get('bots_distributed', 0)}")
    print(f"   Whales distributed: {summary.get('whales_distributed', 0)}")
    print(f"   Momentum distributed: {summary.get('momentum_distributed', 0)}")
    print(f"   Intel distributed: {summary.get('intel_distributed', 0)}")
    
    print("\n✅ Test complete!")
