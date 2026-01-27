#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════════╗
║                                                                                   ║
║   ⚡ RAPID CONVERSION STREAM ⚡                                                   ║
║                                                                                   ║
║   "Speed is Key - Data Every Second - Move Like a Commando"                       ║
║                                                                                   ║
║   ALL PAIRS. ALL COINS. ALL ALTCOINS. ALL ASSETS.                                ║
║   EVERY SECOND. THROUGH THE MYCELIUM. FOR CONVERSIONS.                           ║
║                                                                                   ║
║   ┌─────────────────────────────────────────────────────────────────────────┐    ║
║   │                    ⚡ REAL-TIME DATA MESH ⚡                            │    ║
║   │                                                                         │    ║
║   │   BINANCE ══╗    ╔════ KRAKEN    ╔════ ALPACA    ╔════ ALL             │    ║
║   │   300+ ─────╬────╬─── 200+ ─────╬─── 100+ ─────╬─── 600+ PAIRS        │    ║
║   │   PAIRS     ║    ║    PAIRS     ║    PAIRS     ║                       │    ║
║   │             ╠════╩══════════════╩══════════════╝                       │    ║
║   │             ▼                                                           │    ║
║   │      ╔═════════════════════════════════════════════════╗               │    ║
║   │      ║     🍄 MYCELIUM CONVERSION HUB 🍄              ║               │    ║
║   │      ║     1 SECOND UPDATE CYCLE                      ║               │    ║
║   │      ║     ALL SYSTEMS RECEIVE SIGNALS                ║               │    ║
║   │      ╚══════════════════╤══════════════════════════════╝               │    ║
║   │                         │                                               │    ║
║   │         ┌───────────────┼───────────────┐                              │    ║
║   │         ▼               ▼               ▼                              │    ║
║   │   ╔═══════════╗  ╔═══════════╗  ╔═══════════╗                         │    ║
║   │   ║ V14       ║  ║ LABYRINTH ║  ║ COMMANDO  ║                         │    ║
║   │   ║ SCORING   ║  ║ ENGINE    ║  ║ EXECUTION ║                         │    ║
║   │   ╚═══════════╝  ╚═══════════╝  ╚═══════════╝                         │    ║
║   └─────────────────────────────────────────────────────────────────────────┘    ║
║                                                                                   ║
║   ONE GOAL: SPEED → CONVERSIONS → SNOWBALL → GROW BUYING POWER                   ║
║                                                                                   ║
╚═══════════════════════════════════════════════════════════════════════════════════╝
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
import json
import asyncio
import time
import signal
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor

try:
    import websockets
except ImportError:
    websockets = None

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════════
# SPEED CONFIGURATION - EVERY SECOND COUNTS
# ═══════════════════════════════════════════════════════════════════════════════════

SPEED_CONFIG = {
    'update_interval_ms': 100,      # 100ms = 10 updates per second
    'scan_interval_ms': 1000,       # Full scan every 1 second
    'conversion_check_ms': 500,     # Check conversions every 500ms
    'ws_reconnect_ms': 1000,        # Reconnect websocket in 1s
    'max_parallel_streams': 50,     # Max parallel websocket streams
    'ticker_cache_ttl_ms': 2000,    # Ticker valid for 2 seconds
}

# ALL exchanges to connect
ALL_EXCHANGES = ['binance', 'kraken', 'alpaca']

# ═══════════════════════════════════════════════════════════════════════════════════
# IMPORT CONVERSION SYSTEMS
# ═══════════════════════════════════════════════════════════════════════════════════

# Mycelium Hub - ALL systems wired through here
try:
    from mycelium_conversion_hub import (
        MyceliumConversionHub, get_conversion_hub,
        ConversionSignal, SystemSignal
    )
    HUB_AVAILABLE = True
    print("🍄 Mycelium Conversion Hub LOADED!")
except ImportError as e:
    HUB_AVAILABLE = False
    print(f"⚠️ Hub not available: {e}")

# V14 Labyrinth
try:
    from s5_v14_labyrinth import V14LabyrinthEngine, V14_LABYRINTH_CONFIG
    LABYRINTH_AVAILABLE = True
    print("🏆 V14 Labyrinth LOADED!")
except ImportError:
    LABYRINTH_AVAILABLE = False

# Conversion Commando
try:
    from aureon_conversion_commando import (
        AdaptiveConversionCommando, PairScanner, 
        FalconCommando, TortoiseCommando, ChameleonCommando, BeeCommando
    )
    COMMANDO_AVAILABLE = True
    print("🦅 Conversion Commando LOADED!")
except ImportError:
    COMMANDO_AVAILABLE = False

# Ultra Labyrinth
try:
    from s5_ultra_labyrinth import S5UltraLabyrinth
    ULTRA_AVAILABLE = True
    print("🌀 Ultra Labyrinth LOADED!")
except ImportError:
    ULTRA_AVAILABLE = False

# Pure Conversion Engine
try:
    from pure_conversion_engine import PureConversionEngine
    PURE_ENGINE_AVAILABLE = True
    print("🔄 Pure Conversion Engine LOADED!")
except ImportError:
    PURE_ENGINE_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════════════════════
# RAPID TICKER CACHE - ALL PAIRS, ALL EXCHANGES
# ═══════════════════════════════════════════════════════════════════════════════════

@dataclass
class TickerData:
    """Real-time ticker data"""
    symbol: str
    exchange: str
    price: float
    price_change_24h: float
    price_change_pct: float
    volume_24h: float
    high_24h: float
    low_24h: float
    bid: float = 0.0
    ask: float = 0.0
    spread_pct: float = 0.0
    timestamp: float = field(default_factory=time.time)
    
    @property
    def is_fresh(self) -> bool:
        """Check if data is fresh (< 2 seconds old)"""
        return (time.time() - self.timestamp) * 1000 < SPEED_CONFIG['ticker_cache_ttl_ms']
    
    @property
    def base_asset(self) -> str:
        """Extract base asset from symbol"""
        for quote in ['USDT', 'USDC', 'USD', 'GBP', 'EUR', 'BTC', 'ETH']:
            if self.symbol.endswith(quote):
                return self.symbol[:-len(quote)]
        return self.symbol


class RapidTickerCache:
    """
    Ultra-fast ticker cache for ALL pairs across ALL exchanges.
    Updates every second, caches in memory for instant access.
    """
    
    def __init__(self):
        self.tickers: Dict[str, Dict[str, TickerData]] = defaultdict(dict)  # exchange -> symbol -> ticker
        self.last_update: Dict[str, float] = {}  # exchange -> timestamp
        self.update_count = 0
        self.pairs_tracked = 0
        
        # Price history for momentum calculation
        self.price_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=60))  # Last 60 prices
        
        # Momentum cache (calculated from history)
        self.momentum_1m: Dict[str, float] = {}  # 1-minute momentum
        self.momentum_5m: Dict[str, float] = {}  # 5-minute momentum
        
        # Volume surge detection
        self.volume_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=60))
        self.volume_surge: Dict[str, bool] = {}
        
    def update(self, exchange: str, symbol: str, ticker: TickerData):
        """Update a single ticker - FAST"""
        self.tickers[exchange][symbol] = ticker
        self.last_update[exchange] = time.time()
        
        # Track history
        key = f"{exchange}:{symbol}"
        self.price_history[key].append(ticker.price)
        self.volume_history[key].append(ticker.volume_24h)
        
        # Calculate momentum if enough history
        if len(self.price_history[key]) >= 10:
            prices = list(self.price_history[key])
            self.momentum_1m[key] = (prices[-1] - prices[-10]) / prices[-10] * 100 if prices[-10] > 0 else 0
        
        self.update_count += 1
        
    def bulk_update(self, exchange: str, tickers: List[TickerData]):
        """Bulk update multiple tickers at once - FASTER"""
        for ticker in tickers:
            self.update(exchange, ticker.symbol, ticker)
        self.pairs_tracked = sum(len(t) for t in self.tickers.values())
        
    def get(self, exchange: str, symbol: str) -> Optional[TickerData]:
        """Get a ticker - instant"""
        return self.tickers.get(exchange, {}).get(symbol)
    
    def get_all(self, exchange: str = None) -> List[TickerData]:
        """Get all tickers, optionally filtered by exchange"""
        if exchange:
            return list(self.tickers.get(exchange, {}).values())
        all_tickers = []
        for ex_tickers in self.tickers.values():
            all_tickers.extend(ex_tickers.values())
        return all_tickers
    
    def get_top_movers(self, n: int = 20, exchange: str = None) -> List[TickerData]:
        """Get top N movers by 24h change"""
        tickers = self.get_all(exchange)
        return sorted(tickers, key=lambda t: abs(t.price_change_pct), reverse=True)[:n]
    
    def get_top_volume(self, n: int = 20, exchange: str = None) -> List[TickerData]:
        """Get top N by volume"""
        tickers = self.get_all(exchange)
        return sorted(tickers, key=lambda t: t.volume_24h, reverse=True)[:n]
    
    def get_conversion_candidates(self, min_change_pct: float = 0.5) -> List[Tuple[TickerData, TickerData]]:
        """Get pairs suitable for conversion (one up, one down)"""
        all_tickers = self.get_all()
        up_movers = [t for t in all_tickers if t.price_change_pct >= min_change_pct]
        down_movers = [t for t in all_tickers if t.price_change_pct <= -min_change_pct]
        
        candidates = []
        for up in up_movers:
            for down in down_movers:
                if up.base_asset != down.base_asset:
                    candidates.append((down, up))  # Convert from down to up
        
        return candidates
    
    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        """Convert to dict for feeding to other systems"""
        result = {}
        for ex, symbols in self.tickers.items():
            for sym, ticker in symbols.items():
                key = f"{ex}:{sym}"
                result[key] = {
                    'symbol': ticker.symbol,
                    'exchange': ex,
                    'price': ticker.price,
                    'change24h': ticker.price_change_pct,
                    'volume': ticker.volume_24h,
                    'lastPrice': ticker.price,
                    'bid': ticker.bid,
                    'ask': ticker.ask,
                }
        return result


# ═══════════════════════════════════════════════════════════════════════════════════
# RAPID DATA STREAMS - WEBSOCKET CONNECTIONS
# ═══════════════════════════════════════════════════════════════════════════════════

class BinanceRapidStream:
    """Ultra-fast Binance WebSocket stream for ALL pairs"""
    
    WS_URL = "wss://stream.binance.com:9443/stream?streams="
    REST_URL = "https://api.binance.com/api/v3/ticker/24hr"
    
    def __init__(self, cache: RapidTickerCache):
        self.cache = cache
        self.running = False
        self.connected = False
        self.symbols: Set[str] = set()
        self.last_rest_fetch = 0
        self.updates_per_second = 0
        self._update_count = 0
        self._last_count_time = time.time()
        
    async def fetch_all_tickers_rest(self) -> int:
        """Fetch ALL tickers via REST API - fallback and initial load"""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: requests.get(self.REST_URL, timeout=10)
            )
            response.raise_for_status()
            data = response.json()
            
            tickers = []
            for t in data:
                symbol = t.get('symbol', '')
                if not symbol.endswith(('USDT', 'USDC', 'USD', 'BTC', 'ETH')):
                    continue
                    
                try:
                    ticker = TickerData(
                        symbol=symbol,
                        exchange='binance',
                        price=float(t.get('lastPrice', 0)),
                        price_change_24h=float(t.get('priceChange', 0)),
                        price_change_pct=float(t.get('priceChangePercent', 0)),
                        volume_24h=float(t.get('volume', 0)),
                        high_24h=float(t.get('highPrice', 0)),
                        low_24h=float(t.get('lowPrice', 0)),
                        bid=float(t.get('bidPrice', 0)),
                        ask=float(t.get('askPrice', 0)),
                    )
                    ticker.spread_pct = ((ticker.ask - ticker.bid) / ticker.price * 100) if ticker.price > 0 else 0
                    tickers.append(ticker)
                    self.symbols.add(symbol)
                except:
                    continue
            
            self.cache.bulk_update('binance', tickers)
            self.last_rest_fetch = time.time()
            return len(tickers)
            
        except Exception as e:
            logger.error(f"Binance REST fetch error: {e}")
            return 0
    
    async def stream_all(self):
        """Stream ALL pair updates via WebSocket - SPEED"""
        self.running = True
        
        # Initial fetch
        count = await self.fetch_all_tickers_rest()
        print(f"   📡 Binance: Loaded {count} pairs via REST")
        
        # Build stream URL for all symbols
        if not self.symbols:
            print("   ⚠️ No Binance symbols to stream")
            return
        
        # Use !miniTicker@arr for ALL pairs in one stream
        url = "wss://stream.binance.com:9443/ws/!miniTicker@arr"
        
        while self.running:
            try:
                async with websockets.connect(url, ping_interval=20, ping_timeout=10) as ws:
                    self.connected = True
                    print(f"   ✅ Binance WebSocket connected - streaming {len(self.symbols)} pairs")
                    
                    while self.running:
                        try:
                            msg = await asyncio.wait_for(ws.recv(), timeout=5)
                            data = json.loads(msg)
                            
                            # miniTicker@arr returns array of all tickers
                            if isinstance(data, list):
                                for t in data:
                                    symbol = t.get('s', '')
                                    if symbol not in self.symbols:
                                        continue
                                    
                                    try:
                                        ticker = TickerData(
                                            symbol=symbol,
                                            exchange='binance',
                                            price=float(t.get('c', 0)),  # Close price
                                            price_change_24h=0,  # Not in miniTicker
                                            price_change_pct=0,  # Calculate from history
                                            volume_24h=float(t.get('v', 0)),
                                            high_24h=float(t.get('h', 0)),
                                            low_24h=float(t.get('l', 0)),
                                        )
                                        self.cache.update('binance', symbol, ticker)
                                        self._update_count += 1
                                    except:
                                        continue
                            
                            # Calculate updates per second
                            now = time.time()
                            if now - self._last_count_time >= 1.0:
                                self.updates_per_second = self._update_count
                                self._update_count = 0
                                self._last_count_time = now
                                
                        except asyncio.TimeoutError:
                            continue
                        except websockets.exceptions.ConnectionClosed:
                            break
                            
            except Exception as e:
                logger.warning(f"Binance WS error: {e}")
                self.connected = False
                if self.running:
                    await asyncio.sleep(SPEED_CONFIG['ws_reconnect_ms'] / 1000)
                    
        self.connected = False
    
    def stop(self):
        self.running = False


class KrakenRapidStream:
    """Ultra-fast Kraken data stream"""
    
    REST_URL = "https://api.kraken.com/0/public/Ticker"
    PAIRS_URL = "https://api.kraken.com/0/public/AssetPairs"
    
    def __init__(self, cache: RapidTickerCache):
        self.cache = cache
        self.running = False
        self.pairs: Set[str] = set()
        self.updates_per_second = 0
        
    async def fetch_pairs(self):
        """Fetch available pairs"""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: requests.get(self.PAIRS_URL, timeout=10)
            )
            data = response.json()
            if 'result' in data:
                self.pairs = set(data['result'].keys())
            return len(self.pairs)
        except:
            return 0
    
    async def fetch_all_tickers(self) -> int:
        """Fetch all Kraken tickers via REST (polled every second)"""
        try:
            # Get all pairs
            pairs_param = ','.join(list(self.pairs)[:50])  # Kraken limits
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: requests.get(f"{self.REST_URL}?pair={pairs_param}", timeout=10)
            )
            data = response.json()
            
            if 'result' not in data:
                return 0
            
            tickers = []
            for pair, t in data['result'].items():
                try:
                    # Kraken format: c=close, v=volume, h=high, l=low
                    close = float(t['c'][0]) if isinstance(t['c'], list) else float(t['c'])
                    volume = float(t['v'][1]) if isinstance(t['v'], list) else float(t['v'])
                    high = float(t['h'][1]) if isinstance(t['h'], list) else float(t['h'])
                    low = float(t['l'][1]) if isinstance(t['l'], list) else float(t['l'])
                    
                    ticker = TickerData(
                        symbol=pair,
                        exchange='kraken',
                        price=close,
                        price_change_24h=0,
                        price_change_pct=0,
                        volume_24h=volume,
                        high_24h=high,
                        low_24h=low,
                    )
                    tickers.append(ticker)
                except:
                    continue
            
            self.cache.bulk_update('kraken', tickers)
            return len(tickers)
            
        except Exception as e:
            logger.warning(f"Kraken fetch error: {e}")
            return 0
    
    async def stream_all(self):
        """Poll Kraken every second (they don't have free public WS for all pairs)"""
        self.running = True
        
        # Get pairs first
        await self.fetch_pairs()
        print(f"   📡 Kraken: Found {len(self.pairs)} pairs")
        
        while self.running:
            start = time.time()
            count = await self.fetch_all_tickers()
            self.updates_per_second = count
            
            # Sleep to maintain 1 second interval
            elapsed = time.time() - start
            if elapsed < 1.0:
                await asyncio.sleep(1.0 - elapsed)
                
    def stop(self):
        self.running = False


# ═══════════════════════════════════════════════════════════════════════════════════
# RAPID CONVERSION STREAM - THE MAIN ENGINE
# ═══════════════════════════════════════════════════════════════════════════════════

class RapidConversionStream:
    """
    ⚡ THE RAPID CONVERSION STREAM ⚡
    
    Connects ALL data sources to the Mycelium Hub.
    Updates EVERY SECOND. Scans ALL pairs. Finds conversions FAST.
    
    Architecture:
    1. Data Streams (Binance WS + Kraken REST) → RapidTickerCache
    2. RapidTickerCache → MyceliumConversionHub (every second)
    3. MyceliumConversionHub → All Systems (V14, Labyrinth, Commando)
    4. Systems → Conversion Opportunities
    5. Opportunities → Execution
    """
    
    def __init__(self, starting_capital: float = 10000.0):
        self.starting_capital = starting_capital
        self.running = False
        self.start_time = None
        
        # ═══════════════════════════════════════════════════════════════════════
        # Core Components
        # ═══════════════════════════════════════════════════════════════════════
        
        # Ticker Cache - ALL pairs, ALL exchanges
        self.cache = RapidTickerCache()
        
        # Data Streams
        self.binance_stream = BinanceRapidStream(self.cache)
        self.kraken_stream = KrakenRapidStream(self.cache)
        
        # ═══════════════════════════════════════════════════════════════════════
        # Conversion Systems - ALL wired to Mycelium
        # ═══════════════════════════════════════════════════════════════════════
        
        # Mycelium Hub - Central nervous system
        self.hub = None
        if HUB_AVAILABLE:
            self.hub = get_conversion_hub(starting_capital)
            print("🍄 Mycelium Hub WIRED to Rapid Stream!")
        
        # Pair Scanner (from Commando)
        self.scanner = None
        if COMMANDO_AVAILABLE:
            self.scanner = PairScanner()
            print("🔭 Pair Scanner WIRED!")
        
        # Conversion Commando
        self.commando = None
        if COMMANDO_AVAILABLE:
            self.commando = AdaptiveConversionCommando()
            print("🦅 Conversion Commando WIRED!")
        
        # ═══════════════════════════════════════════════════════════════════════
        # Stats
        # ═══════════════════════════════════════════════════════════════════════
        self.stats = {
            'updates_per_second': 0,
            'pairs_tracked': 0,
            'signals_generated': 0,
            'conversions_found': 0,
            'conversions_executed': 0,
            'total_profit': 0.0,
        }
        
        # Conversion opportunities queue
        self.opportunities: deque = deque(maxlen=100)
        
        # Signal handling
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        print("\n\n🛑 Stopping Rapid Conversion Stream...")
        self.stop()
        
    def stop(self):
        self.running = False
        self.binance_stream.stop()
        self.kraken_stream.stop()
        
    async def _scan_loop(self):
        """Main scanning loop - runs every second"""
        scan_count = 0
        
        while self.running:
            scan_start = time.time()
            scan_count += 1
            
            try:
                # Get all tickers as dict for systems
                ticker_dict = self.cache.to_dict()
                
                # Update stats
                self.stats['pairs_tracked'] = self.cache.pairs_tracked
                self.stats['updates_per_second'] = (
                    self.binance_stream.updates_per_second + 
                    self.kraken_stream.updates_per_second
                )
                
                # ═══════════════════════════════════════════════════════════════
                # FEED ALL SYSTEMS
                # ═══════════════════════════════════════════════════════════════
                
                # Feed Pair Scanner
                if self.scanner:
                    targets = self.scanner.scan_all_pairs(ticker_dict)
                    
                # Get top movers for conversion candidates
                top_movers = self.cache.get_top_movers(20)
                
                # Find conversion opportunities
                if len(top_movers) >= 2:
                    # Look for pairs: one going up, one going down
                    for i, up_ticker in enumerate(top_movers):
                        if up_ticker.price_change_pct <= 0:
                            continue
                        for down_ticker in top_movers[i+1:]:
                            if down_ticker.price_change_pct >= 0:
                                continue
                            
                            # Potential conversion: sell down_ticker, buy up_ticker
                            opportunity = {
                                'from_asset': down_ticker.base_asset,
                                'from_exchange': down_ticker.exchange,
                                'from_price': down_ticker.price,
                                'from_change': down_ticker.price_change_pct,
                                'to_asset': up_ticker.base_asset,
                                'to_exchange': up_ticker.exchange,
                                'to_price': up_ticker.price,
                                'to_change': up_ticker.price_change_pct,
                                'spread': up_ticker.price_change_pct - down_ticker.price_change_pct,
                                'timestamp': time.time(),
                            }
                            
                            # Get Hub signal if available
                            if self.hub:
                                signal = self.hub.get_conversion_signal(
                                    from_asset=down_ticker.base_asset,
                                    to_asset=up_ticker.base_asset,
                                    from_price=down_ticker.price,
                                    to_price=up_ticker.price,
                                )
                                opportunity['hub_score'] = signal.unified_score
                                opportunity['hub_confidence'] = signal.unified_confidence
                                opportunity['hub_recommendation'] = signal.recommendation.value
                                opportunity['participating_systems'] = signal.participating_systems
                                self.stats['signals_generated'] += 1
                            
                            self.opportunities.append(opportunity)
                            self.stats['conversions_found'] += 1
                
                # Log status every 10 seconds
                if scan_count % 10 == 0:
                    elapsed = time.time() - self.start_time
                    print(f"\r⚡ RAPID STREAM | "
                          f"Pairs: {self.stats['pairs_tracked']:,} | "
                          f"Updates/s: {self.stats['updates_per_second']:,} | "
                          f"Signals: {self.stats['signals_generated']:,} | "
                          f"Opps: {self.stats['conversions_found']:,} | "
                          f"Time: {elapsed:.0f}s", end='', flush=True)
                    
            except Exception as e:
                logger.error(f"Scan error: {e}")
                
            # Maintain 1 second interval
            elapsed = time.time() - scan_start
            if elapsed < 1.0:
                await asyncio.sleep(1.0 - elapsed)
                
    async def _opportunity_processor(self):
        """Process conversion opportunities in real-time"""
        while self.running:
            try:
                if self.opportunities:
                    opp = self.opportunities.popleft()
                    
                    # Log high-confidence opportunities
                    if opp.get('hub_score', 0) >= 0.7:
                        print(f"\n   🎯 HIGH CONFIDENCE: "
                              f"{opp['from_asset']}→{opp['to_asset']} "
                              f"Score: {opp['hub_score']*100:.1f}% "
                              f"Spread: {opp['spread']:.2f}%")
                        
            except Exception as e:
                pass
                
            await asyncio.sleep(0.1)
            
    async def run(self):
        """Start the rapid conversion stream"""
        print("""
╔═══════════════════════════════════════════════════════════════════════════════════╗
║                                                                                   ║
║   ⚡⚡⚡ RAPID CONVERSION STREAM - SPEED IS KEY ⚡⚡⚡                              ║
║                                                                                   ║
║   ALL PAIRS. ALL COINS. ALL ALTCOINS. EVERY SECOND.                              ║
║   THROUGH THE MYCELIUM. LIKE A COMMANDO.                                          ║
║                                                                                   ║
╚═══════════════════════════════════════════════════════════════════════════════════╝
""")
        
        self.running = True
        self.start_time = time.time()
        
        print("🚀 Starting data streams...")
        
        # Run all tasks concurrently
        await asyncio.gather(
            self.binance_stream.stream_all(),
            self.kraken_stream.stream_all(),
            self._scan_loop(),
            self._opportunity_processor(),
        )
        
    def get_status(self) -> Dict[str, Any]:
        """Get current stream status"""
        return {
            'running': self.running,
            'uptime_seconds': time.time() - self.start_time if self.start_time else 0,
            'pairs_tracked': self.stats['pairs_tracked'],
            'updates_per_second': self.stats['updates_per_second'],
            'signals_generated': self.stats['signals_generated'],
            'conversions_found': self.stats['conversions_found'],
            'pending_opportunities': len(self.opportunities),
            'binance_connected': self.binance_stream.connected,
            'hub_available': self.hub is not None,
        }
        
    def get_top_opportunities(self, n: int = 10) -> List[Dict]:
        """Get top N conversion opportunities by hub score"""
        opps = list(self.opportunities)
        return sorted(opps, key=lambda x: x.get('hub_score', 0), reverse=True)[:n]


# ═══════════════════════════════════════════════════════════════════════════════════
# QUICK TEST
# ═══════════════════════════════════════════════════════════════════════════════════

async def quick_test():
    """Quick test - 30 seconds of data streaming"""
    print("\n⚡ QUICK TEST - 30 seconds of rapid data streaming...\n")
    
    stream = RapidConversionStream(10000.0)
    
    # Run for 30 seconds
    async def timed_run():
        task = asyncio.create_task(stream.run())
        await asyncio.sleep(30)
        stream.stop()
        await asyncio.sleep(1)
        
    await timed_run()
    
    # Print summary
    print("\n\n📊 QUICK TEST SUMMARY:")
    status = stream.get_status()
    for k, v in status.items():
        print(f"   {k}: {v}")
    
    print("\n🔝 TOP OPPORTUNITIES:")
    for i, opp in enumerate(stream.get_top_opportunities(5)):
        print(f"   {i+1}. {opp['from_asset']}→{opp['to_asset']} "
              f"Score: {opp.get('hub_score', 0)*100:.1f}% "
              f"Spread: {opp['spread']:.2f}%")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true', help='Run quick 30s test')
    args = parser.parse_args()
    
    if args.test:
        asyncio.run(quick_test())
    else:
        stream = RapidConversionStream(10000.0)
        asyncio.run(stream.run())
