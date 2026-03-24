#!/usr/bin/env python3
"""
🌐 QUEEN OPEN SOURCE DATA ENGINE 🌐
=====================================
Aggregates ALL open source, free data feeds to power Queen's intelligence.
No API keys needed - 100% open source data!

Data Sources:
- CoinGecko API (FREE) - Prices, Market Cap, Volume
- Binance Public WebSocket - Live Trades
- Kraken Public WebSocket - Live Trades
- CryptoCompare (FREE tier) - News, Social
- Fear & Greed Index - Market Sentiment
- Alternative.me - Crypto Fear/Greed
- DeFi Llama - TVL Data
- Mempool.space - Bitcoin Network Data
- BlockCypher - Blockchain Data

Prime Sentinel: Gary Leckey 02.11.1991
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
import json
import time
import asyncio
import threading
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Callable, Any
from collections import deque
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

# Imports
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    logger.warning("aiohttp not available - pip install aiohttp")

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    logger.warning("websockets not available - pip install websockets")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


@dataclass
class MarketData:
    """Unified market data structure"""
    symbol: str
    price: float
    volume_24h: float = 0.0
    change_24h: float = 0.0
    market_cap: float = 0.0
    timestamp: float = field(default_factory=time.time)
    source: str = "unknown"
    bid: float = 0.0
    ask: float = 0.0
    high_24h: float = 0.0
    low_24h: float = 0.0


@dataclass
class WhaleAlert:
    """Whale transaction detected"""
    symbol: str
    amount: float
    value_usd: float
    side: str  # buy/sell
    exchange: str
    timestamp: float
    tx_hash: Optional[str] = None


@dataclass
class SentimentData:
    """Market sentiment metrics"""
    fear_greed_index: int  # 0-100
    fear_greed_label: str  # Extreme Fear, Fear, Neutral, Greed, Extreme Greed
    social_volume: int = 0
    news_sentiment: float = 0.0  # -1 to 1
    timestamp: float = field(default_factory=time.time)


@dataclass
class NetworkData:
    """Blockchain network data"""
    chain: str
    block_height: int = 0
    mempool_size: int = 0
    avg_fee: float = 0.0
    hash_rate: float = 0.0
    difficulty: float = 0.0
    timestamp: float = field(default_factory=time.time)


class OpenSourceDataEngine:
    """
    The main engine that aggregates all open source data feeds.
    Queen uses this to know EVERYTHING without paying for APIs.
    """
    
    # FREE API Endpoints (No Auth Required!)
    ENDPOINTS = {
        'coingecko_prices': 'https://api.coingecko.com/api/v3/simple/price',
        'coingecko_markets': 'https://api.coingecko.com/api/v3/coins/markets',
        'coingecko_trending': 'https://api.coingecko.com/api/v3/search/trending',
        'fear_greed': 'https://api.alternative.me/fng/',
        'mempool_stats': 'https://mempool.space/api/v1/fees/recommended',
        'mempool_blocks': 'https://mempool.space/api/blocks/tip/height',
        'defillama_tvl': 'https://api.llama.fi/tvl/ethereum',
        'defillama_protocols': 'https://api.llama.fi/protocols',
        'blockcypher_btc': 'https://api.blockcypher.com/v1/btc/main',
        'blockcypher_eth': 'https://api.blockcypher.com/v1/eth/main',
        # NEWS & SOCIAL (FREE)
        'cryptocompare_news': 'https://min-api.cryptocompare.com/data/v2/news/',
        'reddit_crypto': 'https://www.reddit.com/r/cryptocurrency/new.json',
        'reddit_bitcoin': 'https://www.reddit.com/r/bitcoin/new.json',
        'lunarcrush_global': 'https://lunarcrush.com/api3/public/coins/list',
    }
    
    # Symbol mappings
    COINGECKO_IDS = {
        'BTC/USD': 'bitcoin',
        'ETH/USD': 'ethereum',
        'SOL/USD': 'solana',
        'DOGE/USD': 'dogecoin',
        'XRP/USD': 'ripple',
        'ADA/USD': 'cardano',
        'AVAX/USD': 'avalanche-2',
        'LINK/USD': 'chainlink',
        'DOT/USD': 'polkadot',
        'MATIC/USD': 'matic-network',
        'UNI/USD': 'uniswap',
        'ATOM/USD': 'cosmos',
        'LTC/USD': 'litecoin',
        'BCH/USD': 'bitcoin-cash',
    }
    
    def __init__(self, callback: Optional[Callable] = None):
        self.callback = callback
        self.running = False
        
        # Data stores
        self.market_data: Dict[str, MarketData] = {}
        self.whale_alerts: deque = deque(maxlen=100)
        self.sentiment: Optional[SentimentData] = None
        self.network_data: Dict[str, NetworkData] = {}
        self.trending_coins: List[Dict] = []
        self.defi_tvl: Dict[str, float] = {}
        
        # Live feed connections
        self.binance_ws = None
        self.kraken_ws = None
        self.coinbase_ws = None
        
        # Order Book tracking
        self.order_books: Dict[str, Dict] = {}  # symbol -> {bids, asks, spread, imbalance}
        self.spoofing_alerts: deque = deque(maxlen=50)
        
        # News & Social
        self.news_headlines: deque = deque(maxlen=100)
        self.social_sentiment: Dict[str, Dict] = {}  # symbol -> {reddit_mentions, sentiment}
        self.news_sentiment_score: float = 0.5  # -1 to 1 scale
        
        # Stats
        self.data_points_received = 0
        self.last_update = time.time()
        self.errors = 0
        
        logger.info("🌐 Open Source Data Engine initialized")
        logger.info(f"   📊 Tracking {len(self.COINGECKO_IDS)} symbols")
        logger.info(f"   🔗 {len(self.ENDPOINTS)} free API endpoints")
    
    async def start(self):
        """Start all data collection"""
        self.running = True
        logger.info("🚀 Starting Open Source Data Engine...")
        
        # Start all collectors concurrently
        tasks = [
            asyncio.create_task(self._poll_coingecko()),
            asyncio.create_task(self._poll_fear_greed()),
            asyncio.create_task(self._poll_network_data()),
            asyncio.create_task(self._poll_defi_data()),
            asyncio.create_task(self._poll_trending()),
        ]
        
        # Start WebSocket feeds if available
        if WEBSOCKETS_AVAILABLE:
            tasks.append(asyncio.create_task(self._binance_websocket()))
            tasks.append(asyncio.create_task(self._kraken_websocket()))
            tasks.append(asyncio.create_task(self._coinbase_websocket()))
        
        # News & Social polling
        tasks.append(asyncio.create_task(self._poll_news_sentiment()))
        tasks.append(asyncio.create_task(self._poll_social_volume()))
        tasks.append(asyncio.create_task(self._poll_order_books()))
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    def start_background(self):
        """Start in background thread"""
        def run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.start())
        
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        logger.info("🌐 Data engine running in background")
        return thread
    
    def stop(self):
        """Stop all data collection"""
        self.running = False
        logger.info("🛑 Data engine stopped")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # COINGECKO - FREE MARKET DATA
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def _poll_coingecko(self):
        """Poll CoinGecko for market data (free, no auth)"""
        logger.info("🦎 Starting CoinGecko feed...")
        
        while self.running:
            try:
                await self._fetch_coingecko_markets()
                self.data_points_received += len(self.COINGECKO_IDS)
                self.last_update = time.time()
            except Exception as e:
                logger.error(f"CoinGecko error: {e}")
                self.errors += 1
            
            # CoinGecko free tier: 10-30 calls/minute
            await asyncio.sleep(15)
    
    async def _fetch_coingecko_markets(self):
        """Fetch market data from CoinGecko"""
        if not AIOHTTP_AVAILABLE:
            return
        
        ids = list(self.COINGECKO_IDS.values())
        
        url = self.ENDPOINTS['coingecko_markets']
        params = {
            'vs_currency': 'usd',
            'ids': ','.join(ids),
            'order': 'market_cap_desc',
            'per_page': 50,
            'page': 1,
            'sparkline': 'false',
            'price_change_percentage': '24h'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=30) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    for coin in data:
                        # Find our symbol
                        symbol = None
                        for sym, cg_id in self.COINGECKO_IDS.items():
                            if cg_id == coin['id']:
                                symbol = sym
                                break
                        
                        if symbol:
                            market = MarketData(
                                symbol=symbol,
                                price=coin.get('current_price', 0),
                                volume_24h=coin.get('total_volume', 0),
                                change_24h=coin.get('price_change_percentage_24h', 0),
                                market_cap=coin.get('market_cap', 0),
                                high_24h=coin.get('high_24h', 0),
                                low_24h=coin.get('low_24h', 0),
                                timestamp=time.time(),
                                source='coingecko'
                            )
                            
                            self.market_data[symbol] = market
                            
                            # Check for significant moves (whale-like)
                            change = market.change_24h or 0
                            if abs(change) > 5:
                                await self._emit_whale_signal(market)
                            
                            if self.callback:
                                await self.callback('market_data', market)
                    
                    logger.info(f"🦎 CoinGecko: Updated {len(data)} coins")
                else:
                    logger.warning(f"CoinGecko returned {resp.status}")
    
    async def _emit_whale_signal(self, market: MarketData):
        """Emit a whale-like signal for large moves"""
        alert = WhaleAlert(
            symbol=market.symbol,
            amount=market.volume_24h / market.price if market.price > 0 else 0,
            value_usd=market.volume_24h,
            side='buy' if market.change_24h > 0 else 'sell',
            exchange='aggregate',
            timestamp=time.time()
        )
        self.whale_alerts.append(alert)
        
        if self.callback:
            await self.callback('whale_alert', alert)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # FEAR & GREED INDEX - FREE SENTIMENT
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def _poll_fear_greed(self):
        """Poll Fear & Greed Index (free, no auth)"""
        logger.info("😱 Starting Fear & Greed feed...")
        
        while self.running:
            try:
                await self._fetch_fear_greed()
                self.data_points_received += 1
            except Exception as e:
                logger.error(f"Fear & Greed error: {e}")
                self.errors += 1
            
            # Update every 5 minutes (index updates daily but we want responsive)
            await asyncio.sleep(300)
    
    async def _fetch_fear_greed(self):
        """Fetch Fear & Greed Index"""
        if not AIOHTTP_AVAILABLE:
            return
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.ENDPOINTS['fear_greed'], timeout=30) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    if data.get('data'):
                        latest = data['data'][0]
                        self.sentiment = SentimentData(
                            fear_greed_index=int(latest.get('value', 50)),
                            fear_greed_label=latest.get('value_classification', 'Neutral'),
                            timestamp=time.time()
                        )
                        
                        logger.info(f"😱 Fear & Greed: {self.sentiment.fear_greed_index} ({self.sentiment.fear_greed_label})")
                        
                        if self.callback:
                            await self.callback('sentiment', self.sentiment)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # NETWORK DATA - FREE BLOCKCHAIN STATS
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def _poll_network_data(self):
        """Poll blockchain network data (free)"""
        logger.info("⛓️ Starting Network Data feed...")
        
        while self.running:
            try:
                await self._fetch_mempool()
                await self._fetch_blockcypher()
                self.data_points_received += 3
            except Exception as e:
                logger.error(f"Network data error: {e}")
                self.errors += 1
            
            await asyncio.sleep(60)  # Every minute
    
    async def _fetch_mempool(self):
        """Fetch Bitcoin mempool data from mempool.space (free)"""
        if not AIOHTTP_AVAILABLE:
            return
        
        async with aiohttp.ClientSession() as session:
            # Get recommended fees
            async with session.get(self.ENDPOINTS['mempool_stats'], timeout=30) as resp:
                if resp.status == 200:
                    fees = await resp.json()
                    
                    self.network_data['bitcoin'] = NetworkData(
                        chain='bitcoin',
                        avg_fee=fees.get('halfHourFee', 0),
                        timestamp=time.time()
                    )
                    
                    logger.info(f"⛓️ BTC Fees: {fees.get('halfHourFee', 0)} sat/vB")
    
    async def _fetch_blockcypher(self):
        """Fetch blockchain stats from BlockCypher (free tier)"""
        if not AIOHTTP_AVAILABLE:
            return
        
        async with aiohttp.ClientSession() as session:
            # BTC stats
            async with session.get(self.ENDPOINTS['blockcypher_btc'], timeout=30) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    if 'bitcoin' in self.network_data:
                        self.network_data['bitcoin'].block_height = data.get('height', 0)
                        self.network_data['bitcoin'].hash_rate = data.get('hash_rate', 0)
                    
                    logger.info(f"⛓️ BTC Height: {data.get('height', 0)}")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # DEFI DATA - FREE TVL STATS
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def _poll_defi_data(self):
        """Poll DeFi Llama for TVL data (free)"""
        logger.info("🦙 Starting DeFi Llama feed...")
        
        while self.running:
            try:
                await self._fetch_defi_tvl()
                self.data_points_received += 1
            except Exception as e:
                logger.error(f"DeFi Llama error: {e}")
                self.errors += 1
            
            await asyncio.sleep(120)  # Every 2 minutes
    
    async def _fetch_defi_tvl(self):
        """Fetch DeFi TVL from DeFi Llama"""
        if not AIOHTTP_AVAILABLE:
            return
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.ENDPOINTS['defillama_tvl'], timeout=30) as resp:
                if resp.status == 200:
                    tvl = await resp.json()
                    if tvl is not None:
                        self.defi_tvl['ethereum'] = tvl
                        logger.info(f"🦙 ETH TVL: ${tvl/1e9:.2f}B")
                        
                        if self.callback:
                            await self.callback('defi_tvl', {'ethereum': tvl})
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # TRENDING - WHAT'S HOT
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def _poll_trending(self):
        """Poll CoinGecko trending (free)"""
        logger.info("🔥 Starting Trending feed...")
        
        while self.running:
            try:
                await self._fetch_trending()
                self.data_points_received += 1
            except Exception as e:
                logger.error(f"Trending error: {e}")
                self.errors += 1
            
            await asyncio.sleep(600)  # Every 10 minutes
    
    async def _fetch_trending(self):
        """Fetch trending coins"""
        if not AIOHTTP_AVAILABLE:
            return
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.ENDPOINTS['coingecko_trending'], timeout=30) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.trending_coins = data.get('coins', [])[:7]
                    
                    if self.trending_coins:
                        names = [c['item']['name'] for c in self.trending_coins[:3]]
                        logger.info(f"🔥 Trending: {', '.join(names)}")
                        
                        if self.callback:
                            await self.callback('trending', self.trending_coins)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # BINANCE WEBSOCKET - FREE LIVE TRADES
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def _binance_websocket(self):
        """Connect to Binance WebSocket for live trades"""
        logger.info("🟡 Starting Binance WebSocket...")
        
        symbols = ['btcusdt', 'ethusdt', 'solusdt', 'dogeusdt', 'xrpusdt']
        streams = '/'.join([f"{s}@aggTrade" for s in symbols])
        url = f"wss://stream.binance.com:9443/ws/{streams}"
        
        reconnect_delay = 1
        
        while self.running:
            try:
                async with websockets.connect(url) as ws:
                    logger.info("🟢 Binance WebSocket CONNECTED!")
                    reconnect_delay = 1
                    
                    async for message in ws:
                        if not self.running:
                            break
                        
                        try:
                            data = json.loads(message)
                            await self._process_binance_trade(data)
                        except:
                            pass
                            
            except Exception as e:
                logger.error(f"Binance WS error: {e}")
                if self.running:
                    await asyncio.sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 2, 60)
    
    async def _process_binance_trade(self, data: Dict):
        """Process Binance trade"""
        try:
            symbol_raw = data.get('s', '')
            price = float(data.get('p', 0))
            quantity = float(data.get('q', 0))
            is_buyer_maker = data.get('m', False)
            
            # Convert symbol
            symbol_map = {
                'BTCUSDT': 'BTC/USD',
                'ETHUSDT': 'ETH/USD',
                'SOLUSDT': 'SOL/USD',
                'DOGEUSDT': 'DOGE/USD',
                'XRPUSDT': 'XRP/USD',
            }
            symbol = symbol_map.get(symbol_raw, symbol_raw)
            
            # Value in USD
            value = price * quantity
            
            # Detect whale trades (>$100K)
            if value > 100000:
                alert = WhaleAlert(
                    symbol=symbol,
                    amount=quantity,
                    value_usd=value,
                    side='sell' if is_buyer_maker else 'buy',
                    exchange='binance',
                    timestamp=time.time()
                )
                self.whale_alerts.append(alert)
                
                logger.info(f"🐋 WHALE on Binance: {symbol} ${value:,.0f} ({alert.side.upper()})")
                
                if self.callback:
                    await self.callback('whale_alert', alert)
            
            self.data_points_received += 1
            
        except Exception as e:
            pass
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # KRAKEN WEBSOCKET - FREE LIVE TRADES
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def _kraken_websocket(self):
        """Connect to Kraken WebSocket for live trades"""
        logger.info("🔵 Starting Kraken WebSocket...")
        
        url = "wss://ws.kraken.com"
        reconnect_delay = 1
        
        # Kraken uses XBT for BTC
        kraken_pairs = ['XBT/USD', 'ETH/USD', 'SOL/USD', 'DOGE/USD', 'XRP/USD']
        
        while self.running:
            try:
                async with websockets.connect(url) as ws:
                    # Subscribe to trades
                    subscribe_msg = {
                        "event": "subscribe",
                        "pair": kraken_pairs,
                        "subscription": {"name": "trade"}
                    }
                    await ws.send(json.dumps(subscribe_msg))
                    logger.info("🟢 Kraken WebSocket CONNECTED!")
                    reconnect_delay = 1
                    
                    async for message in ws:
                        if not self.running:
                            break
                        
                        try:
                            data = json.loads(message)
                            await self._process_kraken_trade(data)
                        except:
                            pass
                            
            except Exception as e:
                logger.error(f"Kraken WS error: {e}")
                if self.running:
                    await asyncio.sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 2, 60)
    
    async def _process_kraken_trade(self, data):
        """Process Kraken trade message"""
        try:
            # Kraken trade format: [channelID, [[price, volume, time, side, orderType, misc], ...], "trade", "XBT/USD"]
            if not isinstance(data, list) or len(data) < 4:
                return
            
            if data[-2] != "trade":
                return
            
            pair = data[-1]
            trades = data[1]
            
            # Symbol mapping
            symbol_map = {
                'XBT/USD': 'BTC/USD',
                'ETH/USD': 'ETH/USD',
                'SOL/USD': 'SOL/USD',
                'DOGE/USD': 'DOGE/USD',
                'XRP/USD': 'XRP/USD',
            }
            symbol = symbol_map.get(pair, pair)
            
            for trade in trades:
                price = float(trade[0])
                volume = float(trade[1])
                side = 'buy' if trade[3] == 'b' else 'sell'
                value = price * volume
                
                # Detect whale trades (>$100K)
                if value > 100000:
                    alert = WhaleAlert(
                        symbol=symbol,
                        amount=volume,
                        value_usd=value,
                        side=side,
                        exchange='kraken',
                        timestamp=time.time()
                    )
                    self.whale_alerts.append(alert)
                    
                    logger.info(f"🐋 WHALE on Kraken: {symbol} ${value:,.0f} ({side.upper()})")
                    
                    if self.callback:
                        await self.callback('whale_alert', alert)
                
                self.data_points_received += 1
                
        except Exception as e:
            pass
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # COINBASE WEBSOCKET - FREE LIVE TRADES
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def _coinbase_websocket(self):
        """Connect to Coinbase WebSocket for live trades"""
        logger.info("🟠 Starting Coinbase WebSocket...")
        
        url = "wss://ws-feed.exchange.coinbase.com"
        reconnect_delay = 1
        
        coinbase_products = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'DOGE-USD', 'XRP-USD']
        
        while self.running:
            try:
                async with websockets.connect(url) as ws:
                    # Subscribe to matches (completed trades)
                    subscribe_msg = {
                        "type": "subscribe",
                        "product_ids": coinbase_products,
                        "channels": ["matches"]
                    }
                    await ws.send(json.dumps(subscribe_msg))
                    logger.info("🟢 Coinbase WebSocket CONNECTED!")
                    reconnect_delay = 1
                    
                    async for message in ws:
                        if not self.running:
                            break
                        
                        try:
                            data = json.loads(message)
                            await self._process_coinbase_trade(data)
                        except:
                            pass
                            
            except Exception as e:
                logger.error(f"Coinbase WS error: {e}")
                if self.running:
                    await asyncio.sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 2, 60)
    
    async def _process_coinbase_trade(self, data: Dict):
        """Process Coinbase trade message"""
        try:
            if data.get('type') != 'match':
                return
            
            product = data.get('product_id', '')
            price = float(data.get('price', 0))
            size = float(data.get('size', 0))
            side = data.get('side', 'unknown')
            
            # Symbol mapping
            symbol_map = {
                'BTC-USD': 'BTC/USD',
                'ETH-USD': 'ETH/USD',
                'SOL-USD': 'SOL/USD',
                'DOGE-USD': 'DOGE/USD',
                'XRP-USD': 'XRP/USD',
            }
            symbol = symbol_map.get(product, product.replace('-', '/'))
            
            value = price * size
            
            # Detect whale trades (>$100K)
            if value > 100000:
                alert = WhaleAlert(
                    symbol=symbol,
                    amount=size,
                    value_usd=value,
                    side=side,
                    exchange='coinbase',
                    timestamp=time.time()
                )
                self.whale_alerts.append(alert)
                
                logger.info(f"🐋 WHALE on Coinbase: {symbol} ${value:,.0f} ({side.upper()})")
                
                if self.callback:
                    await self.callback('whale_alert', alert)
            
            self.data_points_received += 1
            
        except Exception as e:
            pass
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # ORDER BOOK ANALYSIS - SPOOFING & ICEBERG DETECTION
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def _poll_order_books(self):
        """Poll order book data and detect manipulation"""
        logger.info("📊 Starting Order Book Analyzer...")
        
        while self.running:
            try:
                await self._fetch_binance_depth()
                self.data_points_received += 1
            except Exception as e:
                logger.error(f"Order book error: {e}")
                self.errors += 1
            
            await asyncio.sleep(10)  # Every 10 seconds
    
    async def _fetch_binance_depth(self):
        """Fetch order book depth from Binance (free)"""
        if not AIOHTTP_AVAILABLE:
            return
        
        symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
        
        async with aiohttp.ClientSession() as session:
            for sym in symbols:
                try:
                    url = f"https://api.binance.com/api/v3/depth?symbol={sym}&limit=20"
                    async with session.get(url, timeout=10) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            await self._analyze_order_book(sym, data)
                except:
                    pass
    
    async def _analyze_order_book(self, symbol: str, data: Dict):
        """Analyze order book for manipulation patterns"""
        try:
            bids = [(float(b[0]), float(b[1])) for b in data.get('bids', [])]
            asks = [(float(a[0]), float(a[1])) for a in data.get('asks', [])]
            
            if not bids or not asks:
                return
            
            best_bid = bids[0][0]
            best_ask = asks[0][0]
            spread = (best_ask - best_bid) / best_bid * 100
            
            # Calculate imbalance
            bid_volume = sum(b[1] * b[0] for b in bids[:10])
            ask_volume = sum(a[1] * a[0] for a in asks[:10])
            total_volume = bid_volume + ask_volume
            imbalance = (bid_volume - ask_volume) / total_volume if total_volume > 0 else 0
            
            # Detect large walls (potential spoofing)
            wall_threshold = 500000  # $500K
            bid_walls = [(p, v) for p, v in bids if p * v > wall_threshold]
            ask_walls = [(p, v) for p, v in asks if p * v > wall_threshold]
            
            # Detect layering (evenly spaced orders)
            layering_score = self._detect_layering(bids) + self._detect_layering(asks)
            layering_score = layering_score / 2
            
            # Normalize symbol
            norm_symbol = symbol.replace('USDT', '/USD')
            
            self.order_books[norm_symbol] = {
                'best_bid': best_bid,
                'best_ask': best_ask,
                'spread_pct': spread,
                'imbalance': imbalance,  # -1 (sell pressure) to +1 (buy pressure)
                'bid_walls': len(bid_walls),
                'ask_walls': len(ask_walls),
                'layering_score': layering_score,
                'timestamp': time.time()
            }
            
            # Alert on potential spoofing (high layering + large walls)
            if layering_score > 0.7 and (bid_walls or ask_walls):
                spoofing_alert = {
                    'symbol': norm_symbol,
                    'type': 'spoofing_suspected',
                    'layering_score': layering_score,
                    'walls': len(bid_walls) + len(ask_walls),
                    'direction': 'buy_wall' if bid_walls else 'sell_wall',
                    'timestamp': time.time()
                }
                self.spoofing_alerts.append(spoofing_alert)
                logger.warning(f"⚠️ SPOOFING DETECTED: {norm_symbol} - {len(bid_walls)} bid walls, {len(ask_walls)} ask walls, layering={layering_score:.2f}")
                
                if self.callback:
                    await self.callback('spoofing_alert', spoofing_alert)
                    
        except Exception as e:
            pass
    
    def _detect_layering(self, orders: List[tuple]) -> float:
        """Detect layering pattern (evenly spaced algorithmic orders)"""
        if len(orders) < 5:
            return 0.0
        
        # Check price spacing consistency
        prices = [o[0] for o in orders[:10]]
        spacings = [prices[i] - prices[i+1] for i in range(len(prices)-1)]
        
        if not spacings:
            return 0.0
        
        avg_spacing = sum(abs(s) for s in spacings) / len(spacings)
        if avg_spacing == 0:
            return 0.0
        
        # Calculate variance in spacing
        variance = sum((abs(s) - avg_spacing) ** 2 for s in spacings) / len(spacings)
        std_dev = variance ** 0.5
        
        # Low variance = suspicious layering
        consistency = 1 - min(1, std_dev / avg_spacing)
        
        # Check size consistency
        sizes = [o[1] for o in orders[:10]]
        avg_size = sum(sizes) / len(sizes)
        size_variance = sum((s - avg_size) ** 2 for s in sizes) / len(sizes)
        size_std = size_variance ** 0.5
        size_consistency = 1 - min(1, size_std / avg_size if avg_size > 0 else 1)
        
        return (consistency + size_consistency) / 2
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # NEWS SENTIMENT - CRYPTOCOMPARE (FREE)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def _poll_news_sentiment(self):
        """Poll CryptoCompare for news sentiment"""
        logger.info("📰 Starting News Sentiment feed...")
        
        while self.running:
            try:
                await self._fetch_crypto_news()
                self.data_points_received += 1
            except Exception as e:
                logger.error(f"News error: {e}")
                self.errors += 1
            
            await asyncio.sleep(120)  # Every 2 minutes
    
    async def _fetch_crypto_news(self):
        """Fetch news from CryptoCompare (free)"""
        if not AIOHTTP_AVAILABLE:
            return
        
        async with aiohttp.ClientSession() as session:
            try:
                url = self.ENDPOINTS['cryptocompare_news']
                headers = {'Accept': 'application/json'}
                
                async with session.get(url, headers=headers, timeout=30) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        articles = data.get('Data', [])[:20]
                        
                        sentiment_sum = 0
                        count = 0
                        
                        for article in articles:
                            headline = {
                                'title': article.get('title', ''),
                                'source': article.get('source', 'unknown'),
                                'url': article.get('url', ''),
                                'categories': article.get('categories', ''),
                                'timestamp': article.get('published_on', time.time()),
                                'sentiment': self._analyze_headline_sentiment(article.get('title', ''))
                            }
                            self.news_headlines.append(headline)
                            sentiment_sum += headline['sentiment']
                            count += 1
                        
                        if count > 0:
                            self.news_sentiment_score = sentiment_sum / count
                            self.sentiment.news_sentiment = self.news_sentiment_score if self.sentiment else 0
                            
                        logger.info(f"📰 News: {len(articles)} articles, sentiment={self.news_sentiment_score:.2f}")
                        
                        if self.callback:
                            await self.callback('news_update', {
                                'count': len(articles),
                                'sentiment': self.news_sentiment_score,
                                'latest': list(self.news_headlines)[-5:]
                            })
                            
            except Exception as e:
                logger.debug(f"CryptoCompare news error: {e}")
    
    def _analyze_headline_sentiment(self, title: str) -> float:
        """Quick sentiment analysis on headline (-1 to 1)"""
        title_lower = title.lower()
        
        # Bullish keywords
        bullish = ['surge', 'soar', 'rally', 'bull', 'gain', 'rise', 'jump', 'high', 
                   'breakout', 'moon', 'pump', 'buy', 'support', 'adoption', 'institutional',
                   'upgrade', 'milestone', 'record', 'ath', 'all-time high']
        
        # Bearish keywords
        bearish = ['crash', 'dump', 'plunge', 'bear', 'drop', 'fall', 'sink', 'low',
                   'breakdown', 'sell', 'fear', 'panic', 'hack', 'scam', 'fraud', 'ban',
                   'regulation', 'lawsuit', 'investigation', 'warning', 'risk']
        
        score = 0
        for word in bullish:
            if word in title_lower:
                score += 0.2
        for word in bearish:
            if word in title_lower:
                score -= 0.2
        
        return max(-1, min(1, score))
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # SOCIAL VOLUME - REDDIT (FREE)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def _poll_social_volume(self):
        """Poll Reddit for social sentiment"""
        logger.info("🗣️ Starting Social Volume feed...")
        
        while self.running:
            try:
                await self._fetch_reddit_sentiment()
                self.data_points_received += 1
            except Exception as e:
                logger.error(f"Reddit error: {e}")
                self.errors += 1
            
            await asyncio.sleep(180)  # Every 3 minutes (respect rate limits)
    
    async def _fetch_reddit_sentiment(self):
        """Fetch sentiment from Reddit crypto subreddits (free, no auth)"""
        if not AIOHTTP_AVAILABLE:
            return
        
        subreddits = [
            ('cryptocurrency', self.ENDPOINTS['reddit_crypto']),
            ('bitcoin', self.ENDPOINTS['reddit_bitcoin']),
        ]
        
        async with aiohttp.ClientSession() as session:
            total_mentions = {}
            total_sentiment = 0
            post_count = 0
            
            for sub_name, url in subreddits:
                try:
                    headers = {'User-Agent': 'QueenIntelligence/1.0'}
                    async with session.get(url, headers=headers, timeout=30) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            posts = data.get('data', {}).get('children', [])
                            
                            for post in posts[:25]:
                                post_data = post.get('data', {})
                                title = post_data.get('title', '').lower()
                                score = post_data.get('score', 0)
                                
                                # Count coin mentions
                                coins = ['btc', 'bitcoin', 'eth', 'ethereum', 'sol', 'solana', 
                                        'doge', 'dogecoin', 'xrp', 'ripple', 'ada', 'cardano']
                                
                                for coin in coins:
                                    if coin in title:
                                        key = coin.upper()
                                        if key not in total_mentions:
                                            total_mentions[key] = {'count': 0, 'engagement': 0}
                                        total_mentions[key]['count'] += 1
                                        total_mentions[key]['engagement'] += score
                                
                                # Sentiment from title
                                sentiment = self._analyze_headline_sentiment(title)
                                total_sentiment += sentiment
                                post_count += 1
                                
                except Exception as e:
                    logger.debug(f"Reddit {sub_name} error: {e}")
            
            if post_count > 0:
                avg_sentiment = total_sentiment / post_count
                
                self.social_sentiment = {
                    'reddit': {
                        'avg_sentiment': avg_sentiment,
                        'post_count': post_count,
                        'mentions': total_mentions,
                        'timestamp': time.time()
                    }
                }
                
                # Update main sentiment if available
                if self.sentiment:
                    self.sentiment.social_volume = post_count
                
                top_coins = sorted(total_mentions.items(), key=lambda x: x[1]['count'], reverse=True)[:3]
                logger.info(f"🗣️ Reddit: {post_count} posts, sentiment={avg_sentiment:.2f}, trending={[c[0] for c in top_coins]}")
                
                if self.callback:
                    await self.callback('social_update', self.social_sentiment)

    # ═══════════════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def get_market_data(self, symbol: str = None) -> Dict:
        """Get current market data"""
        if symbol:
            return asdict(self.market_data.get(symbol)) if symbol in self.market_data else None
        return {k: asdict(v) for k, v in self.market_data.items()}
    
    def get_sentiment(self) -> Optional[Dict]:
        """Get current sentiment"""
        return asdict(self.sentiment) if self.sentiment else None
    
    def get_whale_alerts(self, limit: int = 20) -> List[Dict]:
        """Get recent whale alerts"""
        alerts = list(self.whale_alerts)[-limit:]
        return [asdict(a) for a in alerts]
    
    def get_trending(self) -> List[Dict]:
        """Get trending coins"""
        return self.trending_coins
    
    def get_network_data(self) -> Dict:
        """Get network data"""
        return {k: asdict(v) for k, v in self.network_data.items()}
    
    def get_stats(self) -> Dict:
        """Get engine stats"""
        return {
            'data_points_received': self.data_points_received,
            'symbols_tracked': len(self.market_data),
            'whale_alerts': len(self.whale_alerts),
            'last_update': self.last_update,
            'uptime': time.time() - (self.last_update - 60),
            'errors': self.errors,
            'sentiment': self.sentiment.fear_greed_label if self.sentiment else None,
            'news_sentiment': self.news_sentiment_score,
            'order_books_tracked': len(self.order_books),
            'spoofing_alerts': len(self.spoofing_alerts),
        }
    
    def get_news(self, limit: int = 20) -> Dict:
        """Get recent news headlines and sentiment"""
        headlines = list(self.news_headlines)[-limit:]
        return {
            'sentiment_score': self.news_sentiment_score,
            'headlines': headlines,
            'count': len(headlines)
        }
    
    def get_social_sentiment(self) -> Dict:
        """Get Reddit social sentiment and coin mentions"""
        return self.social_sentiment
    
    def get_order_books(self) -> Dict:
        """Get order book analysis for tracked symbols"""
        return self.order_books
    
    def get_spoofing_alerts(self, limit: int = 20) -> List[Dict]:
        """Get recent spoofing/manipulation alerts"""
        return list(self.spoofing_alerts)[-limit:]
    
    def get_market_intelligence(self) -> Dict:
        """Get comprehensive market intelligence summary"""
        order_book_bias = 'neutral'
        if self.order_books:
            avg_imbalance = sum(ob.get('imbalance', 0) for ob in self.order_books.values()) / len(self.order_books)
            if avg_imbalance > 0.2:
                order_book_bias = 'bullish'
            elif avg_imbalance < -0.2:
                order_book_bias = 'bearish'
        
        return {
            'fear_greed': self.sentiment.fear_greed_index if self.sentiment else None,
            'fear_greed_label': self.sentiment.fear_greed_label if self.sentiment else None,
            'news_sentiment': self.news_sentiment_score,
            'social_sentiment': self.social_sentiment.get('reddit', {}).get('avg_sentiment', 0),
            'order_book_bias': order_book_bias,
            'whale_activity': len(self.whale_alerts),
            'spoofing_detected': len(self.spoofing_alerts) > 0,
            'trending_coins': self._get_trending_names(),
            'data_health': {
                'points_received': self.data_points_received,
                'errors': self.errors,
                'uptime_seconds': time.time() - self.last_update + 60 if self.last_update else 0
            }
        }
    
    def _get_trending_names(self) -> List[str]:
        """Extract trending coin names safely"""
        names = []
        try:
            for coin in self.trending_coins[:5]:
                if isinstance(coin, dict):
                    # CoinGecko format: {'item': {'name': 'Bitcoin', ...}}
                    if 'item' in coin:
                        names.append(coin['item'].get('name', coin['item'].get('id', '?')))
                    else:
                        names.append(coin.get('name', coin.get('id', '?')))
                else:
                    names.append(str(coin))
        except:
            pass
        return names


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ═══════════════════════════════════════════════════════════════════════════════
_data_engine: Optional[OpenSourceDataEngine] = None

def get_data_engine() -> OpenSourceDataEngine:
    """Get or create the global data engine"""
    global _data_engine
    if _data_engine is None:
        _data_engine = OpenSourceDataEngine()
    return _data_engine


# ═══════════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 80)
    print("🌐 QUEEN OPEN SOURCE DATA ENGINE - TEST MODE")
    print("=" * 80)
    
    async def test_callback(event_type: str, data):
        print(f"📥 {event_type}: {data}")
    
    engine = OpenSourceDataEngine(callback=test_callback)
    
    print("\n📊 Starting data collection from FREE sources...")
    print("   - CoinGecko (prices, market cap)")
    print("   - Fear & Greed Index (sentiment)")
    print("   - Mempool.space (BTC network)")
    print("   - DeFi Llama (TVL)")
    print("   - Binance WebSocket (live trades)")
    print("\nPress Ctrl+C to stop\n")
    
    try:
        asyncio.run(engine.start())
    except KeyboardInterrupt:
        engine.stop()
        print("\n✅ Data engine stopped")
