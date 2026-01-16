#!/usr/bin/env python3
"""
🌐⚡ UNIFIED WEBSOCKET FEED MANAGER ⚡🌐
═══════════════════════════════════════════════════════════════

Production-grade WebSocket feed aggregator for multi-exchange data:

📡 EXCHANGE STREAMS:
├─ 🟡 Binance (Spot WS)      wss://stream.binance.com:9443/ws
├─ 🐙 Kraken (WS v2)         wss://ws.kraken.com
├─ 🏛️ Capital.com (WS)       wss://api-streaming.capital.com
├─ 🪙 Coinbase (Advanced)    wss://advanced-trade-ws.coinbase.com
└─ 🦎 CoinGecko (REST poll)  api.coingecko.com/v3 (for reference prices)

🔗 OUTPUTS:
├─ Normalized ticker stream (symbol, bid, ask, last, exchange, ts)
├─ ThoughtBus events for downstream consumers
└─ GlobalFinancialFeed enrichment

Gary Leckey | January 2026
"All data flows through the Queen"
"""

from __future__ import annotations

import os
import sys
import json
import asyncio
import logging
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set
from collections import defaultdict

# Windows UTF-8 fix
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        # Skip stderr wrapping - causes Windows exit errors
    except Exception:
        pass

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# HFT HARMONIC MYCELIUM INTEGRATION
# ═══════════════════════════════════════════════════════════════

# Lazy load HFT engine for graceful degradation
try:
    from aureon_hft_harmonic_mycelium import get_hft_engine
    HFT_ENGINE_AVAILABLE = True
except ImportError:
    get_hft_engine = None
    HFT_ENGINE_AVAILABLE = False

# ═══════════════════════════════════════════════════════════════
# WEBSOCKET ENDPOINTS
# ═══════════════════════════════════════════════════════════════

WS_ENDPOINTS = {
    'binance': 'wss://stream.binance.com:9443/ws',
    'kraken': 'wss://ws.kraken.com',
    'capital': 'wss://api-streaming.capital.com/connect',
    'coinbase': 'wss://advanced-trade-ws.coinbase.com',
}

COINGECKO_API = 'https://api.coingecko.com/api/v3'

# ═══════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════

@dataclass
class NormalizedTick:
    """Unified tick format across all exchanges."""
    symbol: str           # Normalized symbol (e.g., BTC/USD)
    exchange: str         # Source exchange
    bid: float
    ask: float
    last: float
    volume_24h: float = 0.0
    change_24h: float = 0.0
    timestamp: float = field(default_factory=time.time)
    raw_symbol: str = ""  # Original exchange symbol
    
    @property
    def spread(self) -> float:
        if self.bid > 0:
            return (self.ask - self.bid) / self.bid
        return 0.0
    
    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ExchangeStatus:
    """Health status for an exchange connection."""
    exchange: str
    connected: bool = False
    last_message: float = 0.0
    message_count: int = 0
    error_count: int = 0
    subscribed_symbols: Set[str] = field(default_factory=set)
    
    @property
    def is_healthy(self) -> bool:
        # Healthy if connected and received message in last 60s
        return self.connected and (time.time() - self.last_message) < 60


# ═══════════════════════════════════════════════════════════════
# SYMBOL NORMALIZATION
# ═══════════════════════════════════════════════════════════════

def normalize_symbol(raw: str, exchange: str) -> str:
    """Convert exchange-specific symbol to unified format (BASE/QUOTE)."""
    raw = raw.upper().strip()
    
    if exchange == 'binance':
        # BTCUSDT -> BTC/USDT
        for quote in ['USDT', 'USDC', 'BUSD', 'USD', 'BTC', 'ETH', 'EUR', 'GBP']:
            if raw.endswith(quote) and len(raw) > len(quote):
                base = raw[:-len(quote)]
                return f"{base}/{quote}"
        return raw
    
    elif exchange == 'kraken':
        # XXBTZUSD -> BTC/USD, XETHZUSD -> ETH/USD
        raw = raw.replace('XXBT', 'BTC').replace('XETH', 'ETH').replace('ZUSD', 'USD')
        raw = raw.replace('ZEUR', 'EUR').replace('ZGBP', 'GBP').replace('ZJPY', 'JPY')
        if '/' in raw:
            return raw
        for quote in ['USD', 'USDT', 'USDC', 'EUR', 'GBP', 'BTC', 'ETH']:
            if raw.endswith(quote) and len(raw) > len(quote):
                base = raw[:-len(quote)]
                return f"{base}/{quote}"
        return raw
    
    elif exchange == 'coinbase':
        # BTC-USD -> BTC/USD
        if '-' in raw:
            return raw.replace('-', '/')
        return raw
    
    elif exchange == 'capital':
        # Already in BTCUSD format typically
        for quote in ['USD', 'EUR', 'GBP']:
            if raw.endswith(quote) and len(raw) > len(quote):
                base = raw[:-len(quote)]
                return f"{base}/{quote}"
        return raw
    
    return raw


def denormalize_symbol(symbol: str, exchange: str) -> str:
    """Convert unified symbol to exchange-specific format."""
    symbol = symbol.upper().replace('/', '')
    
    if exchange == 'binance':
        return symbol  # BTCUSDT
    elif exchange == 'kraken':
        # BTC/USD -> XXBTZUSD (Kraken uses X prefix for crypto, Z for fiat)
        return symbol.replace('BTC', 'XBT')  # Kraken uses XBT
    elif exchange == 'coinbase':
        # BTC/USD -> BTC-USD
        return symbol[:3] + '-' + symbol[3:] if len(symbol) >= 6 else symbol
    elif exchange == 'capital':
        return symbol
    
    return symbol


# ═══════════════════════════════════════════════════════════════
# WEBSOCKET HANDLERS
# ═══════════════════════════════════════════════════════════════

class UnifiedWSFeed:
    """
    Unified WebSocket feed manager for multi-exchange data.
    
    Connects to Binance, Kraken, Capital.com, Coinbase WebSockets
    and normalizes all ticks into a unified format.
    """
    
    def __init__(
        self,
        enable_binance: bool = True,
        enable_kraken: bool = True,
        enable_capital: bool = True,
        enable_coinbase: bool = True,
        enable_coingecko: bool = True,
    ):
        self.enable = {
            'binance': enable_binance,
            'kraken': enable_kraken,
            'capital': enable_capital,
            'coinbase': enable_coinbase,
            'coingecko': enable_coingecko,
        }
        
        # State
        self.status: Dict[str, ExchangeStatus] = {
            ex: ExchangeStatus(exchange=ex) for ex in WS_ENDPOINTS
        }
        self.ticks: Dict[str, NormalizedTick] = {}  # symbol -> latest tick
        self.callbacks: List[Callable[[NormalizedTick], None]] = []
        self._running = False
        self._tasks: List[asyncio.Task] = []
        
        # ThoughtBus integration
        self.thought_bus = None
        try:
            from aureon_thought_bus import ThoughtBus
            self.thought_bus = ThoughtBus(persist_path="ws_feed_thoughts.jsonl")
        except ImportError:
            pass
        
        # 🦈🔪 HFT Harmonic Mycelium Integration
        self.hft_engine = None
        if HFT_ENGINE_AVAILABLE and get_hft_engine is not None:
            try:
                self.hft_engine = get_hft_engine()
                logger.info("🦈🔪 HFT Harmonic Mycelium Engine WIRED to WebSocket Feed")
            except Exception as e:
                logger.warning(f"🦈🔪 HFT Engine initialization failed: {e}")
        
        logger.info("🌐⚡ UnifiedWSFeed initialized")
        for ex, enabled in self.enable.items():
            logger.info(f"   {ex}: {'✅' if enabled else '❌'}")
    
    def on_tick(self, callback: Callable[[NormalizedTick], None]):
        """Register a callback for new ticks."""
        self.callbacks.append(callback)
    
    def _emit(self, tick: NormalizedTick):
        """Emit tick to all callbacks, ThoughtBus, and HFT engine."""
        self.ticks[tick.symbol] = tick
        
        # 🦈🔪 Inject tick into HFT engine for sub-10ms processing
        if self.hft_engine and hasattr(self.hft_engine, 'inject_tick'):
            try:
                self.hft_engine.inject_tick(tick)
            except Exception as e:
                logger.debug(f"🦈🔪 HFT tick injection error: {e}")
        
        for cb in self.callbacks:
            try:
                cb(tick)
            except Exception as e:
                logger.warning(f"Tick callback error: {e}")
        
        if self.thought_bus:
            try:
                from aureon_thought_bus import Thought
                self.thought_bus.emit(Thought(
                    source=f"ws_{tick.exchange}",
                    type="tick",
                    data=tick.to_dict()
                ))
            except Exception:
                pass
    
    # ─────────────────────────────────────────────────────────────
    # BINANCE HANDLER
    # ─────────────────────────────────────────────────────────────
    
    async def _binance_stream(self, symbols: List[str]):
        """Connect to Binance combined stream for multiple symbols."""
        try:
            import websockets
        except ImportError:
            logger.error("❌ websockets package not installed: pip install websockets")
            return
        
        status = self.status['binance']
        
        # Build combined stream URL
        streams = [f"{s.lower()}@ticker" for s in symbols]
        url = f"{WS_ENDPOINTS['binance']}/{'/'.join(streams[:20])}"  # Max 20 per connection
        
        while self._running:
            try:
                async with websockets.connect(url, ping_interval=20) as ws:
                    status.connected = True
                    status.subscribed_symbols = set(symbols)
                    logger.info(f"🟡 Binance WS connected ({len(symbols)} symbols)")
                    
                    async for msg in ws:
                        if not self._running:
                            break
                        
                        try:
                            data = json.loads(msg)
                            if 'stream' in data:
                                data = data.get('data', data)
                            
                            raw_symbol = data.get('s', '')
                            tick = NormalizedTick(
                                symbol=normalize_symbol(raw_symbol, 'binance'),
                                exchange='binance',
                                bid=float(data.get('b', 0)),
                                ask=float(data.get('a', 0)),
                                last=float(data.get('c', 0)),
                                volume_24h=float(data.get('v', 0)),
                                change_24h=float(data.get('P', 0)),
                                raw_symbol=raw_symbol,
                            )
                            status.last_message = time.time()
                            status.message_count += 1
                            self._emit(tick)
                        except Exception as e:
                            status.error_count += 1
                            logger.debug(f"Binance parse error: {e}")
            
            except Exception as e:
                status.connected = False
                status.error_count += 1
                logger.warning(f"🟡 Binance WS error: {e}, reconnecting in 5s...")
                await asyncio.sleep(5)
    
    # ─────────────────────────────────────────────────────────────
    # KRAKEN HANDLER
    # ─────────────────────────────────────────────────────────────
    
    async def _kraken_stream(self, symbols: List[str]):
        """Connect to Kraken WebSocket v2."""
        try:
            import websockets
        except ImportError:
            return
        
        status = self.status['kraken']
        url = WS_ENDPOINTS['kraken']
        
        while self._running:
            try:
                async with websockets.connect(url) as ws:
                    status.connected = True
                    
                    # Subscribe to ticker
                    sub_msg = {
                        "event": "subscribe",
                        "pair": [denormalize_symbol(s, 'kraken') for s in symbols[:50]],
                        "subscription": {"name": "ticker"}
                    }
                    await ws.send(json.dumps(sub_msg))
                    status.subscribed_symbols = set(symbols)
                    logger.info(f"🐙 Kraken WS connected ({len(symbols)} symbols)")
                    
                    async for msg in ws:
                        if not self._running:
                            break
                        
                        try:
                            data = json.loads(msg)
                            
                            # Skip system messages
                            if isinstance(data, dict):
                                continue
                            
                            # Ticker format: [channelID, {...}, "ticker", "XBT/USD"]
                            if isinstance(data, list) and len(data) >= 4 and data[2] == "ticker":
                                ticker = data[1]
                                raw_symbol = data[3]
                                
                                tick = NormalizedTick(
                                    symbol=normalize_symbol(raw_symbol, 'kraken'),
                                    exchange='kraken',
                                    bid=float(ticker.get('b', [0])[0]),
                                    ask=float(ticker.get('a', [0])[0]),
                                    last=float(ticker.get('c', [0])[0]),
                                    volume_24h=float(ticker.get('v', [0, 0])[1]),
                                    raw_symbol=raw_symbol,
                                )
                                status.last_message = time.time()
                                status.message_count += 1
                                self._emit(tick)
                        except Exception as e:
                            status.error_count += 1
                            logger.debug(f"Kraken parse error: {e}")
            
            except Exception as e:
                status.connected = False
                status.error_count += 1
                logger.warning(f"🐙 Kraken WS error: {e}, reconnecting in 5s...")
                await asyncio.sleep(5)
    
    # ─────────────────────────────────────────────────────────────
    # COINBASE HANDLER
    # ─────────────────────────────────────────────────────────────
    
    async def _coinbase_stream(self, symbols: List[str]):
        """Connect to Coinbase Advanced Trade WebSocket."""
        try:
            import websockets
        except ImportError:
            return
        
        status = self.status['coinbase']
        url = WS_ENDPOINTS['coinbase']
        
        while self._running:
            try:
                async with websockets.connect(url) as ws:
                    status.connected = True
                    
                    # Subscribe message
                    product_ids = [denormalize_symbol(s, 'coinbase') for s in symbols[:50]]
                    sub_msg = {
                        "type": "subscribe",
                        "product_ids": product_ids,
                        "channel": "ticker"
                    }
                    await ws.send(json.dumps(sub_msg))
                    status.subscribed_symbols = set(symbols)
                    logger.info(f"🪙 Coinbase WS connected ({len(symbols)} symbols)")
                    
                    async for msg in ws:
                        if not self._running:
                            break
                        
                        try:
                            data = json.loads(msg)
                            
                            if data.get('type') == 'ticker':
                                raw_symbol = data.get('product_id', '')
                                
                                tick = NormalizedTick(
                                    symbol=normalize_symbol(raw_symbol, 'coinbase'),
                                    exchange='coinbase',
                                    bid=float(data.get('best_bid', 0)),
                                    ask=float(data.get('best_ask', 0)),
                                    last=float(data.get('price', 0)),
                                    volume_24h=float(data.get('volume_24h', 0)),
                                    raw_symbol=raw_symbol,
                                )
                                status.last_message = time.time()
                                status.message_count += 1
                                self._emit(tick)
                        except Exception as e:
                            status.error_count += 1
                            logger.debug(f"Coinbase parse error: {e}")
            
            except Exception as e:
                status.connected = False
                status.error_count += 1
                logger.warning(f"🪙 Coinbase WS error: {e}, reconnecting in 5s...")
                await asyncio.sleep(5)
    
    # ─────────────────────────────────────────────────────────────
    # CAPITAL.COM HANDLER
    # ─────────────────────────────────────────────────────────────
    
    async def _capital_stream(self, symbols: List[str]):
        """Connect to Capital.com WebSocket (requires API key)."""
        api_key = os.getenv("CAPITAL_API_KEY", "")
        if not api_key:
            logger.warning("🏛️ Capital.com: No API key, skipping WS")
            return
        
        try:
            import websockets
        except ImportError:
            return
        
        status = self.status['capital']
        url = WS_ENDPOINTS['capital']
        
        while self._running:
            try:
                async with websockets.connect(url) as ws:
                    # Authenticate
                    auth_msg = {"action": "auth", "apiKey": api_key}
                    await ws.send(json.dumps(auth_msg))
                    
                    # Wait for auth response
                    auth_resp = await ws.recv()
                    auth_data = json.loads(auth_resp)
                    if auth_data.get("status") != "ok":
                        logger.error(f"🏛️ Capital.com auth failed: {auth_data}")
                        await asyncio.sleep(30)
                        continue
                    
                    status.connected = True
                    
                    # Subscribe to prices
                    sub_msg = {
                        "action": "subscribe",
                        "channel": "prices",
                        "epics": [denormalize_symbol(s, 'capital') for s in symbols[:20]]
                    }
                    await ws.send(json.dumps(sub_msg))
                    status.subscribed_symbols = set(symbols)
                    logger.info(f"🏛️ Capital.com WS connected ({len(symbols)} symbols)")
                    
                    async for msg in ws:
                        if not self._running:
                            break
                        
                        try:
                            data = json.loads(msg)
                            
                            if data.get("type") == "price":
                                raw_symbol = data.get("epic", "")
                                
                                tick = NormalizedTick(
                                    symbol=normalize_symbol(raw_symbol, 'capital'),
                                    exchange='capital',
                                    bid=float(data.get('bid', 0)),
                                    ask=float(data.get('offer', 0)),
                                    last=float(data.get('mid', 0)),
                                    raw_symbol=raw_symbol,
                                )
                                status.last_message = time.time()
                                status.message_count += 1
                                self._emit(tick)
                        except Exception as e:
                            status.error_count += 1
                            logger.debug(f"Capital parse error: {e}")
            
            except Exception as e:
                status.connected = False
                status.error_count += 1
                logger.warning(f"🏛️ Capital.com WS error: {e}, reconnecting in 10s...")
                await asyncio.sleep(10)
    
    # ─────────────────────────────────────────────────────────────
    # COINGECKO POLLER (REST fallback)
    # ─────────────────────────────────────────────────────────────
    
    async def _coingecko_poll(self, coin_ids: List[str], interval: int = 30):
        """Poll CoinGecko for reference prices (rate-limited)."""
        import urllib.request
        
        api_key = os.getenv("COINGECKO_API_KEY", "")
        headers = {}
        if api_key:
            headers["x-cg-demo-api-key"] = api_key
        
        while self._running:
            try:
                ids = ",".join(coin_ids[:50])
                url = f"{COINGECKO_API}/simple/price?ids={ids}&vs_currencies=usd&include_24hr_change=true"
                
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode())
                
                for coin_id, info in data.items():
                    symbol = coin_id.upper()
                    if coin_id == 'bitcoin':
                        symbol = 'BTC'
                    elif coin_id == 'ethereum':
                        symbol = 'ETH'
                    
                    price = float(info.get('usd', 0))
                    change = float(info.get('usd_24h_change', 0))
                    
                    tick = NormalizedTick(
                        symbol=f"{symbol}/USD",
                        exchange='coingecko',
                        bid=price * 0.999,  # Approximate
                        ask=price * 1.001,
                        last=price,
                        change_24h=change,
                        raw_symbol=coin_id,
                    )
                    self._emit(tick)
                
                logger.debug(f"🦎 CoinGecko polled {len(data)} coins")
            
            except Exception as e:
                logger.warning(f"🦎 CoinGecko poll error: {e}")
            
            await asyncio.sleep(interval)
    
    # ─────────────────────────────────────────────────────────────
    # START/STOP
    # ─────────────────────────────────────────────────────────────
    
    async def start(
        self,
        symbols: Optional[List[str]] = None,
        coingecko_ids: Optional[List[str]] = None,
    ):
        """Start all enabled WebSocket streams."""
        if symbols is None:
            symbols = [
                "BTC/USD", "ETH/USD", "SOL/USD", "XRP/USD", "DOGE/USD",
                "ADA/USD", "AVAX/USD", "DOT/USD", "MATIC/USD", "LINK/USD",
            ]
        
        if coingecko_ids is None:
            coingecko_ids = [
                "bitcoin", "ethereum", "solana", "ripple", "dogecoin",
                "cardano", "avalanche-2", "polkadot", "matic-network", "chainlink",
            ]
        
        self._running = True
        
        if self.enable.get('binance'):
            binance_symbols = [s.replace('/', '') for s in symbols]
            self._tasks.append(asyncio.create_task(self._binance_stream(binance_symbols)))
        
        if self.enable.get('kraken'):
            self._tasks.append(asyncio.create_task(self._kraken_stream(symbols)))
        
        if self.enable.get('coinbase'):
            self._tasks.append(asyncio.create_task(self._coinbase_stream(symbols)))
        
        if self.enable.get('capital'):
            self._tasks.append(asyncio.create_task(self._capital_stream(symbols)))
        
        if self.enable.get('coingecko'):
            self._tasks.append(asyncio.create_task(self._coingecko_poll(coingecko_ids)))
        
        logger.info(f"🌐⚡ UnifiedWSFeed started with {len(self._tasks)} streams")
    
    async def stop(self):
        """Stop all WebSocket streams."""
        self._running = False
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()
        
        for status in self.status.values():
            status.connected = False
        
        logger.info("🌐 UnifiedWSFeed stopped")
    
    def get_best_tick(self, symbol: str) -> Optional[NormalizedTick]:
        """Get the best (tightest spread) tick for a symbol across exchanges."""
        symbol = symbol.upper()
        if '/' not in symbol:
            symbol = f"{symbol}/USD"
        
        candidates = [t for t in self.ticks.values() if t.symbol == symbol]
        if not candidates:
            return None
        
        # Return tick with tightest spread
        return min(candidates, key=lambda t: t.spread)
    
    def get_health(self) -> Dict[str, Any]:
        """Return health status of all exchange connections."""
        return {
            ex: {
                'connected': s.connected,
                'healthy': s.is_healthy,
                'msg_count': s.message_count,
                'error_count': s.error_count,
                'last_msg_ago': time.time() - s.last_message if s.last_message else None,
            }
            for ex, s in self.status.items()
        }


# ═══════════════════════════════════════════════════════════════
# SINGLETON + INTEGRATION
# ═══════════════════════════════════════════════════════════════

_ws_feed: Optional[UnifiedWSFeed] = None

def get_ws_feed() -> UnifiedWSFeed:
    """Get or create the singleton UnifiedWSFeed instance."""
    global _ws_feed
    if _ws_feed is None:
        _ws_feed = UnifiedWSFeed()
    return _ws_feed


async def start_production_feeds(symbols: Optional[List[str]] = None):
    """Start the unified WS feed for production use."""
    feed = get_ws_feed()
    await feed.start(symbols=symbols)
    return feed


# ═══════════════════════════════════════════════════════════════
# CLI TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    async def main():
        feed = get_ws_feed()
        
        # Print ticks as they arrive
        def on_tick(tick: NormalizedTick):
            print(f"[{tick.exchange:10}] {tick.symbol:12} bid={tick.bid:.4f} ask={tick.ask:.4f} last={tick.last:.4f}")
        
        feed.on_tick(on_tick)
        
        await feed.start()
        
        try:
            # Run for 60 seconds
            await asyncio.sleep(60)
        finally:
            await feed.stop()
            print("\n📊 Final Health:")
            for ex, health in feed.get_health().items():
                print(f"   {ex}: {health}")
    
    asyncio.run(main())
