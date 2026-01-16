#!/usr/bin/env python3
"""
🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥
║                                                                               ║
║   🔴 LIVE MARKET FEED - WATCH THEM IN REAL-TIME 🔴                           ║
║                                                                               ║
║   Connects to real exchanges to watch actual money movement                  ║
║   - Binance WebSocket (real trades)                                          ║
║   - Kraken WebSocket (real trades)                                           ║
║   - CoinGecko API (price updates)                                            ║
║                                                                               ║
║   Prime Sentinel: Gary Leckey 02.11.1991                                     ║
║   Keeper of the Flame - Unchained and Unbroken                               ║
║                                                                               ║
🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥
"""

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
import asyncio
import logging
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable, Any
from collections import deque

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

# Try imports
try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    
try:
    from aiohttp import web, ClientSession
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

# Import our surveillance system
try:
    from aureon_realtime_surveillance import (
        AureonSurveillanceSystem, 
        MarketTick, 
        FlowEvent, 
        FlowTracker
    )
    SURVEILLANCE_AVAILABLE = True
except ImportError:
    SURVEILLANCE_AVAILABLE = False
    logger.warning("Surveillance system not available")

# ═══════════════════════════════════════════════════════════════════════════════
# BINANCE LIVE FEED
# ═══════════════════════════════════════════════════════════════════════════════

class BinanceLiveFeed:
    """
    Connect to Binance WebSocket for LIVE trade data.
    Watch them move money in real-time!
    """
    
    BASE_URL = "wss://stream.binance.com:9443/ws"
    
    def __init__(self, symbols: List[str], callback: Callable):
        self.symbols = symbols
        self.callback = callback
        self.running = False
        self.reconnect_delay = 1
        
        # Map symbols to Binance format
        self.binance_symbols = [s.replace("/", "").lower() for s in symbols]
        
    async def connect(self):
        """Connect to Binance WebSocket"""
        self.running = True
        
        while self.running:
            try:
                # Build stream URL for trades
                streams = "/".join([f"{s}@trade" for s in self.binance_symbols])
                url = f"{self.BASE_URL}/{streams}"
                
                logger.info(f"🟡 Connecting to Binance: {url[:80]}...")
                
                async with websockets.connect(url) as ws:
                    logger.info("🟢 Binance WebSocket CONNECTED!")
                    self.reconnect_delay = 1
                    
                    async for message in ws:
                        if not self.running:
                            break
                            
                        try:
                            data = json.loads(message)
                            await self._process_trade(data)
                        except json.JSONDecodeError:
                            continue
                            
            except Exception as e:
                logger.error(f"🔴 Binance connection error: {e}")
                if self.running:
                    await asyncio.sleep(self.reconnect_delay)
                    self.reconnect_delay = min(self.reconnect_delay * 2, 60)
                    
    async def _process_trade(self, data: Dict):
        """Process incoming trade"""
        try:
            # Binance trade format
            symbol = data.get('s', '')
            price = float(data.get('p', 0))
            quantity = float(data.get('q', 0))
            is_buyer_maker = data.get('m', False)
            trade_time = data.get('T', time.time() * 1000) / 1000
            
            # Convert symbol back (BTCUSDT -> BTC/USD)
            normalized_symbol = self._normalize_symbol(symbol)
            
            # Create tick
            tick = MarketTick(
                symbol=normalized_symbol,
                price=price,
                bid=price * 0.9999,  # Approximate
                ask=price * 1.0001,
                volume=quantity,
                timestamp=trade_time,
                exchange="binance",
                side="sell" if is_buyer_maker else "buy",
                size=quantity
            )
            
            await self.callback(tick)
            
        except Exception as e:
            logger.error(f"Error processing Binance trade: {e}")
            
    def _normalize_symbol(self, binance_symbol: str) -> str:
        """Convert BTCUSDT -> BTC/USD"""
        mappings = {
            "BTCUSDT": "BTC/USD",
            "ETHUSDT": "ETH/USD",
            "SOLUSDT": "SOL/USD",
            "DOGEUSDT": "DOGE/USD",
            "XRPUSDT": "XRP/USD",
            "ADAUSDT": "ADA/USD",
        }
        return mappings.get(binance_symbol, binance_symbol)
        
    def stop(self):
        """Stop the feed"""
        self.running = False

# ═══════════════════════════════════════════════════════════════════════════════
# KRAKEN LIVE FEED
# ═══════════════════════════════════════════════════════════════════════════════

class KrakenLiveFeed:
    """
    Connect to Kraken WebSocket for LIVE trade data.
    """
    
    BASE_URL = "wss://ws.kraken.com"
    
    def __init__(self, symbols: List[str], callback: Callable):
        self.symbols = symbols
        self.callback = callback
        self.running = False
        self.reconnect_delay = 1
        
        # Map to Kraken format
        self.kraken_pairs = self._to_kraken_pairs(symbols)
        
    def _to_kraken_pairs(self, symbols: List[str]) -> List[str]:
        """Convert BTC/USD -> XBT/USD for Kraken"""
        mappings = {
            "BTC/USD": "XBT/USD",
            "ETH/USD": "ETH/USD",
            "SOL/USD": "SOL/USD",
            "DOGE/USD": "DOGE/USD",
        }
        return [mappings.get(s, s) for s in symbols]
        
    async def connect(self):
        """Connect to Kraken WebSocket"""
        self.running = True
        
        while self.running:
            try:
                logger.info(f"🔵 Connecting to Kraken...")
                
                async with websockets.connect(self.BASE_URL) as ws:
                    # Subscribe to trades
                    subscribe_msg = {
                        "event": "subscribe",
                        "pair": self.kraken_pairs,
                        "subscription": {"name": "trade"}
                    }
                    await ws.send(json.dumps(subscribe_msg))
                    
                    logger.info("🟢 Kraken WebSocket CONNECTED!")
                    self.reconnect_delay = 1
                    
                    async for message in ws:
                        if not self.running:
                            break
                            
                        try:
                            data = json.loads(message)
                            await self._process_message(data)
                        except json.JSONDecodeError:
                            continue
                            
            except Exception as e:
                logger.error(f"🔴 Kraken connection error: {e}")
                if self.running:
                    await asyncio.sleep(self.reconnect_delay)
                    self.reconnect_delay = min(self.reconnect_delay * 2, 60)
                    
    async def _process_message(self, data):
        """Process Kraken message"""
        try:
            # Kraken trade messages are arrays: [channelID, [[price, volume, time, side, orderType, misc]], channelName, pair]
            if isinstance(data, list) and len(data) >= 4:
                trades = data[1]
                pair = data[3]
                
                if isinstance(trades, list):
                    for trade in trades:
                        price = float(trade[0])
                        volume = float(trade[1])
                        trade_time = float(trade[2])
                        side = "buy" if trade[3] == "b" else "sell"
                        
                        # Normalize symbol
                        normalized = self._normalize_symbol(pair)
                        
                        tick = MarketTick(
                            symbol=normalized,
                            price=price,
                            bid=price * 0.9999,
                            ask=price * 1.0001,
                            volume=volume,
                            timestamp=trade_time,
                            exchange="kraken",
                            side=side,
                            size=volume
                        )
                        
                        await self.callback(tick)
                        
        except Exception as e:
            # Ignore subscription confirmations, etc.
            pass
            
    def _normalize_symbol(self, kraken_pair: str) -> str:
        """Convert XBT/USD -> BTC/USD"""
        return kraken_pair.replace("XBT", "BTC")
        
    def stop(self):
        """Stop the feed"""
        self.running = False

# ═══════════════════════════════════════════════════════════════════════════════
# COINGECKO PRICE FEED (FREE, No Auth)
# ═══════════════════════════════════════════════════════════════════════════════

class CoinGeckoFeed:
    """
    Fetch prices from CoinGecko API (FREE, no API key needed).
    Slower but reliable backup feed.
    """
    
    API_URL = "https://api.coingecko.com/api/v3"
    
    # Map symbols to CoinGecko IDs
    SYMBOL_MAP = {
        "BTC/USD": "bitcoin",
        "ETH/USD": "ethereum",
        "SOL/USD": "solana",
        "DOGE/USD": "dogecoin",
        "XRP/USD": "ripple",
        "ADA/USD": "cardano",
    }
    
    def __init__(self, symbols: List[str], callback: Callable, interval: float = 10.0):
        self.symbols = symbols
        self.callback = callback
        self.interval = interval
        self.running = False
        self.last_prices: Dict[str, float] = {}
        
    async def start(self):
        """Start polling CoinGecko"""
        self.running = True
        logger.info(f"🦎 Starting CoinGecko feed (interval: {self.interval}s)")
        
        while self.running:
            try:
                await self._fetch_prices()
            except Exception as e:
                logger.error(f"CoinGecko error: {e}")
            await asyncio.sleep(self.interval)
            
    async def _fetch_prices(self):
        """Fetch current prices"""
        if not AIOHTTP_AVAILABLE:
            return
            
        ids = [self.SYMBOL_MAP.get(s) for s in self.symbols if s in self.SYMBOL_MAP]
        ids = [i for i in ids if i]
        
        if not ids:
            return
            
        url = f"{self.API_URL}/simple/price"
        params = {
            "ids": ",".join(ids),
            "vs_currencies": "usd",
            "include_24hr_change": "true"
        }
        
        async with ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    await self._process_prices(data)
                else:
                    logger.warning(f"CoinGecko returned {resp.status}")
                    
    async def _process_prices(self, data: Dict):
        """Process CoinGecko response"""
        for symbol, gecko_id in self.SYMBOL_MAP.items():
            if gecko_id in data:
                price_data = data[gecko_id]
                price = price_data.get('usd', 0)
                
                if price > 0:
                    # Determine if price went up or down
                    prev_price = self.last_prices.get(symbol, price)
                    side = "buy" if price > prev_price else "sell"
                    self.last_prices[symbol] = price
                    
                    tick = MarketTick(
                        symbol=symbol,
                        price=price,
                        bid=price * 0.999,
                        ask=price * 1.001,
                        volume=0,
                        timestamp=time.time(),
                        exchange="coingecko",
                        side=side,
                        size=0
                    )
                    
                    await self.callback(tick)
                    
    def stop(self):
        """Stop the feed"""
        self.running = False

# ═══════════════════════════════════════════════════════════════════════════════
# COMBINED LIVE FEED MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class LiveFeedManager:
    """
    Manages all live feeds and routes data to surveillance system.
    """
    
    def __init__(self, surveillance: Optional['AureonSurveillanceSystem'] = None):
        self.surveillance = surveillance
        self.feeds = []
        self.tick_count = 0
        self.start_time = time.time()
        
        self.symbols = ["BTC/USD", "ETH/USD", "SOL/USD", "DOGE/USD"]
        
    async def on_tick(self, tick: MarketTick):
        """Handle incoming tick from any feed"""
        self.tick_count += 1
        
        # Log significant trades
        value = (tick.size or 0) * tick.price
        if value > 10000:  # >$10k trade
            emoji = "🟢" if tick.side == "buy" else "🔴"
            logger.info(f"{emoji} {tick.exchange}: {tick.side.upper()} ${value:,.0f} {tick.symbol} @ ${tick.price:,.2f}")
            
        # Feed to surveillance system
        if self.surveillance:
            self.surveillance.process_tick(tick)
            
    async def start_all_feeds(self):
        """Start all available feeds"""
        tasks = []
        
        # CoinGecko feed (always works, no auth needed)
        coingecko = CoinGeckoFeed(self.symbols, self.on_tick, interval=10)
        self.feeds.append(coingecko)
        tasks.append(coingecko.start())
        
        # Binance WebSocket (requires websockets library)
        if WEBSOCKETS_AVAILABLE:
            binance = BinanceLiveFeed(self.symbols, self.on_tick)
            self.feeds.append(binance)
            tasks.append(binance.connect())
            
            # Kraken WebSocket
            kraken = KrakenLiveFeed(self.symbols, self.on_tick)
            self.feeds.append(kraken)
            tasks.append(kraken.connect())
        else:
            logger.warning("websockets not installed - using CoinGecko only")
            logger.warning("Run: pip install websockets")
            
        # Run all feeds
        await asyncio.gather(*tasks, return_exceptions=True)
        
    def stop_all(self):
        """Stop all feeds"""
        for feed in self.feeds:
            feed.stop()

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN: RUN LIVE SURVEILLANCE
# ═══════════════════════════════════════════════════════════════════════════════

async def run_live_surveillance():
    """Run the complete live surveillance system"""
    
    print()
    print("🔥" * 40)
    print()
    print("    🔴 LIVE MARKET SURVEILLANCE 🔴")
    print()
    print("    Prime Sentinel: Gary Leckey 02.11.1991")
    print("    Keeper of the Flame - Unchained and Unbroken")
    print()
    print("    Connecting to LIVE exchanges...")
    print("    - Binance (real trades)")
    print("    - Kraken (real trades)")
    print("    - CoinGecko (price updates)")
    print()
    print("    'WATCH THEM MOVE OUR MONEY'")
    print()
    print("🔥" * 40)
    print()
    
    # Initialize surveillance
    surveillance = None
    if SURVEILLANCE_AVAILABLE:
        surveillance = AureonSurveillanceSystem()
    else:
        logger.warning("Surveillance system not available")
        
    # Create feed manager
    feed_manager = LiveFeedManager(surveillance)
    
    # Web server for dashboard
    web_server = None
    if AIOHTTP_AVAILABLE:
        try:
            from aureon_surveillance_dashboard import SurveillanceWebServer
            web_server = SurveillanceWebServer(port=8888)
        except ImportError:
            logger.warning("Dashboard not available")
            
    # Broadcast loop
    async def broadcast_loop():
        while True:
            if web_server and surveillance:
                try:
                    data = surveillance.get_dashboard_data()
                    await web_server.broadcast(data)
                except Exception as e:
                    logger.error(f"Broadcast error: {e}")
            await asyncio.sleep(1)
            
    # Stats printer
    async def stats_printer():
        while True:
            await asyncio.sleep(30)
            uptime = time.time() - feed_manager.start_time
            logger.info(f"📊 Stats: {feed_manager.tick_count:,} ticks | Uptime: {uptime/60:.1f}m")
            if surveillance:
                stats = surveillance.stats
                logger.info(f"   🐋 Whales: {stats['whales_detected']} | 🤖 Bots: {stats['bots_detected']} | 🚨 Alerts: {stats['alerts_generated']}")
    
    # Run everything
    try:
        tasks = [feed_manager.start_all_feeds(), stats_printer()]
        
        if web_server:
            tasks.append(web_server.start())
            tasks.append(broadcast_loop())
            logger.info("🌐 Dashboard available at http://localhost:8888")
            
        await asyncio.gather(*tasks)
        
    except KeyboardInterrupt:
        print("\n👁️ Surveillance shutting down...")
        feed_manager.stop_all()
        
        print()
        print(f"📊 Final Stats:")
        print(f"   Ticks processed: {feed_manager.tick_count:,}")
        if surveillance:
            print(f"   Whales detected: {surveillance.stats['whales_detected']}")
            print(f"   Bots detected: {surveillance.stats['bots_detected']}")
            print(f"   Alerts generated: {surveillance.stats['alerts_generated']}")
        print()
        print("🔥 UNCHAINED AND UNBROKEN 🔥")

# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Install dependencies if needed
    if not WEBSOCKETS_AVAILABLE:
        print("Installing websockets...")
        os.system("pip install websockets")
        
    asyncio.run(run_live_surveillance())
