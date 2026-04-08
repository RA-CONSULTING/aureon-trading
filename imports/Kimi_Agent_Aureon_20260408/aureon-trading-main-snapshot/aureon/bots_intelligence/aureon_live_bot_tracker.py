#!/usr/bin/env python3
"""
🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥
║                                                                               ║
║   🤖 LIVE BOT TRACKER - WATCH THEM MOVE THROUGH THE MARKET 🤖                ║
║                                                                               ║
║   Real-time bot detection using LIVE WebSocket data                          ║
║   - Binance Trade Stream (real trades, real bots)                            ║
║   - Kraken Trade Stream (real trades, real bots)                             ║
║   - Pattern recognition to identify bot behavior                             ║
║   - Track WHERE they are, WHO they are, WHAT they're doing                   ║
║                                                                               ║
║   Prime Sentinel: Gary Leckey 02.11.1991                                     ║
║   Keeper of the Flame - Unchained and Unbroken                               ║
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
import logging
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from collections import deque, defaultdict
from pathlib import Path
import hashlib

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')
logger = logging.getLogger(__name__)

# Try imports
try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    logger.error("websockets not installed! Run: pip install websockets")

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

# Sacred constants
PHI = (1 + math.sqrt(5)) / 2
SCHUMANN = 7.83

# ═══════════════════════════════════════════════════════════════════════════════
# BOT SIGNATURES - Known patterns from our research
# ═══════════════════════════════════════════════════════════════════════════════

BOT_SIGNATURES = {
    "MICROSTRATEGY_BOT": {
        "description": "Large institutional accumulation bot",
        "typical_size_usd": (50000, 500000),
        "peak_hours_utc": [13, 14, 15, 16],
        "interval_seconds": (28800, 29000),  # ~8h cycle
        "exchanges": ["binance", "kraken", "coinbase"],
        "symbols": ["BTCUSDT", "BTCUSD", "XBT/USD"],
        "color": "\033[95m",  # Purple
    },
    "FUNDING_RATE_ARBITRAGE": {
        "description": "Exploits funding rate differentials",
        "typical_size_usd": (10000, 100000),
        "peak_hours_utc": [0, 8, 16],  # Funding times
        "interval_seconds": (28700, 29100),  # 8h funding cycle
        "exchanges": ["binance", "bybit", "okx"],
        "symbols": ["BTCUSDT", "ETHUSDT"],
        "color": "\033[93m",  # Yellow
    },
    "MARKET_MAKER_BOT": {
        "description": "Provides liquidity, tight spreads",
        "typical_size_usd": (100, 5000),
        "interval_seconds": (0.1, 2),  # Very fast
        "pattern": "alternating_buy_sell",
        "color": "\033[96m",  # Cyan
    },
    "SCALPER_BOT": {
        "description": "High-frequency scalping",
        "typical_size_usd": (500, 10000),
        "interval_seconds": (1, 30),
        "pattern": "rapid_in_out",
        "color": "\033[92m",  # Green
    },
    "WHALE_ICEBERG": {
        "description": "Large order split into smaller pieces",
        "typical_size_usd": (5000, 20000),  # Per slice
        "interval_seconds": (10, 60),  # Steady drip
        "pattern": "consistent_size_same_direction",
        "color": "\033[94m",  # Blue
    },
    "WASH_TRADER": {
        "description": "Fake volume, same entity both sides",
        "pattern": "mirror_trades",
        "interval_seconds": (0.01, 0.5),  # Near instant
        "color": "\033[91m",  # Red
    },
    "GRID_BOT": {
        "description": "Grid trading strategy",
        "pattern": "fixed_price_levels",
        "interval_seconds": (60, 300),
        "color": "\033[97m",  # White
    },
    "MOMENTUM_CHASER": {
        "description": "Follows price momentum",
        "pattern": "follows_price_direction",
        "interval_seconds": (5, 60),
        "color": "\033[33m",  # Orange
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class LiveTrade:
    """A single live trade from WebSocket"""
    exchange: str
    symbol: str
    price: float
    quantity: float
    value_usd: float
    side: str  # 'buy' or 'sell'
    timestamp: float
    trade_id: str
    is_maker: bool = False

@dataclass
class BotInstance:
    """A detected bot instance"""
    bot_id: str
    bot_type: str
    exchange: str
    symbol: str
    first_seen: float
    last_seen: float
    trade_count: int
    total_volume_usd: float
    avg_trade_size: float
    avg_interval: float
    direction_bias: float  # -1 = all sell, +1 = all buy
    confidence: float
    trades: List[LiveTrade] = field(default_factory=list)
    status: str = "ACTIVE"  # ACTIVE, DORMANT, GONE

@dataclass 
class MarketSnapshot:
    """Current market state"""
    timestamp: float
    prices: Dict[str, float]
    active_bots: int
    trades_per_second: float
    buy_volume: float
    sell_volume: float
    dominant_bot: Optional[str]

# ═══════════════════════════════════════════════════════════════════════════════
# BOT DETECTION ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class BotDetectionEngine:
    """
    Real-time bot detection from live trade streams.
    Identifies patterns that indicate algorithmic trading.
    """
    
    def __init__(self):
        # Trade history per exchange/symbol
        self.trade_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Detected bots
        self.bots: Dict[str, BotInstance] = {}
        
        # Trade clustering for pattern detection
        self.trade_clusters: Dict[str, List[LiveTrade]] = defaultdict(list)
        
        # Statistics
        self.stats = {
            'total_trades': 0,
            'bot_trades': 0,
            'human_trades': 0,
            'bots_detected': 0,
            'start_time': time.time()
        }
        
        # Size clustering for iceberg detection
        self.size_clusters: Dict[str, Dict[float, int]] = defaultdict(lambda: defaultdict(int))
        
        # Interval analysis
        self.interval_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
    def analyze_trade(self, trade: LiveTrade) -> Optional[BotInstance]:
        """
        Analyze a trade and detect if it's from a bot.
        Returns the bot instance if detected.
        """
        self.stats['total_trades'] += 1
        key = f"{trade.exchange}:{trade.symbol}"
        
        # Add to history
        self.trade_history[key].append(trade)
        
        # Need minimum trades for analysis
        if len(self.trade_history[key]) < 10:
            return None
            
        # Run detection algorithms
        bot = None
        
        # 1. Check for market maker pattern (rapid alternating)
        bot = bot or self._detect_market_maker(trade, key)
        
        # 2. Check for iceberg orders (same size repeated)
        bot = bot or self._detect_iceberg(trade, key)
        
        # 3. Check for scalper (rapid in/out)
        bot = bot or self._detect_scalper(trade, key)
        
        # 4. Check for large institutional (size + timing)
        bot = bot or self._detect_institutional(trade, key)
        
        # 5. Check for wash trading (mirror trades)
        bot = bot or self._detect_wash_trading(trade, key)
        
        # 6. Check interval patterns
        bot = bot or self._detect_interval_pattern(trade, key)
        
        if bot:
            self.stats['bot_trades'] += 1
            self.stats['bots_detected'] = len(self.bots)
        else:
            self.stats['human_trades'] += 1
            
        return bot
        
    def _detect_market_maker(self, trade: LiveTrade, key: str) -> Optional[BotInstance]:
        """Detect market maker bots - rapid alternating buy/sell"""
        recent = list(self.trade_history[key])[-20:]
        if len(recent) < 10:
            return None
            
        # Check for alternating pattern
        alternations = 0
        for i in range(1, len(recent)):
            if recent[i].side != recent[i-1].side:
                alternations += 1
                
        alternation_ratio = alternations / (len(recent) - 1)
        
        # Check timing - very fast
        intervals = []
        for i in range(1, len(recent)):
            intervals.append(recent[i].timestamp - recent[i-1].timestamp)
        avg_interval = sum(intervals) / len(intervals) if intervals else 999
        
        # Market maker: high alternation + fast intervals + consistent size
        sizes = [t.value_usd for t in recent]
        size_std = self._std(sizes)
        size_mean = sum(sizes) / len(sizes) if sizes else 0
        size_cv = size_std / size_mean if size_mean > 0 else 999  # Coefficient of variation
        
        if alternation_ratio > 0.7 and avg_interval < 5 and size_cv < 0.3:
            bot_id = self._generate_bot_id("MM", trade.exchange, trade.symbol, size_mean)
            
            if bot_id not in self.bots:
                self.bots[bot_id] = BotInstance(
                    bot_id=bot_id,
                    bot_type="MARKET_MAKER_BOT",
                    exchange=trade.exchange,
                    symbol=trade.symbol,
                    first_seen=recent[0].timestamp,
                    last_seen=trade.timestamp,
                    trade_count=len(recent),
                    total_volume_usd=sum(sizes),
                    avg_trade_size=size_mean,
                    avg_interval=avg_interval,
                    direction_bias=0,  # Neutral
                    confidence=min(alternation_ratio, 0.95),
                    trades=recent[-10:]
                )
            else:
                self.bots[bot_id].last_seen = trade.timestamp
                self.bots[bot_id].trade_count += 1
                self.bots[bot_id].total_volume_usd += trade.value_usd
                
            return self.bots[bot_id]
            
        return None
        
    def _detect_iceberg(self, trade: LiveTrade, key: str) -> Optional[BotInstance]:
        """Detect iceberg orders - large orders split into same-size pieces"""
        # Round to nearest "round" size
        rounded_size = round(trade.value_usd / 100) * 100
        
        self.size_clusters[key][rounded_size] += 1
        
        # Check if this size appears frequently
        if self.size_clusters[key][rounded_size] >= 5:
            recent = list(self.trade_history[key])[-50:]
            
            # Find trades with similar size
            similar = [t for t in recent if abs(t.value_usd - rounded_size) < rounded_size * 0.1]
            
            if len(similar) >= 5:
                # Check if same direction
                buy_count = sum(1 for t in similar if t.side == 'buy')
                sell_count = len(similar) - buy_count
                direction_ratio = max(buy_count, sell_count) / len(similar)
                
                if direction_ratio > 0.8:  # Strong directional bias
                    direction = "buy" if buy_count > sell_count else "sell"
                    bot_id = self._generate_bot_id("ICE", trade.exchange, trade.symbol, rounded_size)
                    
                    if bot_id not in self.bots:
                        self.bots[bot_id] = BotInstance(
                            bot_id=bot_id,
                            bot_type="WHALE_ICEBERG",
                            exchange=trade.exchange,
                            symbol=trade.symbol,
                            first_seen=similar[0].timestamp,
                            last_seen=trade.timestamp,
                            trade_count=len(similar),
                            total_volume_usd=sum(t.value_usd for t in similar),
                            avg_trade_size=rounded_size,
                            avg_interval=self._avg_interval(similar),
                            direction_bias=1 if direction == "buy" else -1,
                            confidence=direction_ratio * 0.9,
                            trades=similar[-10:]
                        )
                    else:
                        self.bots[bot_id].last_seen = trade.timestamp
                        self.bots[bot_id].trade_count += 1
                        self.bots[bot_id].total_volume_usd += trade.value_usd
                        
                    return self.bots[bot_id]
                    
        return None
        
    def _detect_scalper(self, trade: LiveTrade, key: str) -> Optional[BotInstance]:
        """Detect scalper bots - rapid trades with quick reversals"""
        recent = list(self.trade_history[key])[-30:]
        if len(recent) < 15:
            return None
            
        # Look for buy-sell pairs within short time
        pairs = []
        for i, t1 in enumerate(recent):
            for t2 in recent[i+1:]:
                if t1.side != t2.side and abs(t2.timestamp - t1.timestamp) < 60:
                    if abs(t1.value_usd - t2.value_usd) / max(t1.value_usd, 1) < 0.2:
                        pairs.append((t1, t2))
                        
        if len(pairs) >= 3:
            bot_id = self._generate_bot_id("SCALP", trade.exchange, trade.symbol, 0)
            avg_size = sum(t.value_usd for p in pairs for t in p) / (len(pairs) * 2)
            
            if bot_id not in self.bots:
                self.bots[bot_id] = BotInstance(
                    bot_id=bot_id,
                    bot_type="SCALPER_BOT",
                    exchange=trade.exchange,
                    symbol=trade.symbol,
                    first_seen=pairs[0][0].timestamp,
                    last_seen=trade.timestamp,
                    trade_count=len(pairs) * 2,
                    total_volume_usd=avg_size * len(pairs) * 2,
                    avg_trade_size=avg_size,
                    avg_interval=5,
                    direction_bias=0,
                    confidence=min(len(pairs) / 10, 0.85),
                    trades=[t for p in pairs[-5:] for t in p]
                )
            else:
                self.bots[bot_id].last_seen = trade.timestamp
                self.bots[bot_id].trade_count += 1
                
            return self.bots[bot_id]
            
        return None
        
    def _detect_institutional(self, trade: LiveTrade, key: str) -> Optional[BotInstance]:
        """Detect large institutional bots based on size and timing"""
        # Check if trade is large
        if trade.value_usd < 50000:
            return None
            
        # Check time - institutional bots often active during specific hours
        hour = datetime.fromtimestamp(trade.timestamp, tz=timezone.utc).hour
        
        # MicroStrategy pattern: 13-16 UTC, BTC focused
        if 13 <= hour <= 16 and 'BTC' in trade.symbol.upper():
            bot_id = self._generate_bot_id("INST", trade.exchange, "BTC", trade.value_usd // 10000)
            
            if bot_id not in self.bots:
                self.bots[bot_id] = BotInstance(
                    bot_id=bot_id,
                    bot_type="MICROSTRATEGY_BOT",
                    exchange=trade.exchange,
                    symbol=trade.symbol,
                    first_seen=trade.timestamp,
                    last_seen=trade.timestamp,
                    trade_count=1,
                    total_volume_usd=trade.value_usd,
                    avg_trade_size=trade.value_usd,
                    avg_interval=28800,  # 8h assumed
                    direction_bias=1 if trade.side == "buy" else -1,
                    confidence=0.6,
                    trades=[trade]
                )
            else:
                self.bots[bot_id].last_seen = trade.timestamp
                self.bots[bot_id].trade_count += 1
                self.bots[bot_id].total_volume_usd += trade.value_usd
                self.bots[bot_id].confidence = min(self.bots[bot_id].confidence + 0.05, 0.95)
                
            return self.bots[bot_id]
            
        return None
        
    def _detect_wash_trading(self, trade: LiveTrade, key: str) -> Optional[BotInstance]:
        """Detect wash trading - mirror trades within milliseconds"""
        recent = list(self.trade_history[key])[-10:]
        
        for prev in recent[:-1]:
            # Mirror trade: opposite side, same size, < 1 second apart
            if (prev.side != trade.side and 
                abs(prev.value_usd - trade.value_usd) < trade.value_usd * 0.01 and
                abs(trade.timestamp - prev.timestamp) < 1.0):
                
                bot_id = self._generate_bot_id("WASH", trade.exchange, trade.symbol, 0)
                
                if bot_id not in self.bots:
                    self.bots[bot_id] = BotInstance(
                        bot_id=bot_id,
                        bot_type="WASH_TRADER",
                        exchange=trade.exchange,
                        symbol=trade.symbol,
                        first_seen=prev.timestamp,
                        last_seen=trade.timestamp,
                        trade_count=2,
                        total_volume_usd=trade.value_usd * 2,
                        avg_trade_size=trade.value_usd,
                        avg_interval=trade.timestamp - prev.timestamp,
                        direction_bias=0,
                        confidence=0.9,  # High confidence for mirror
                        trades=[prev, trade]
                    )
                else:
                    self.bots[bot_id].last_seen = trade.timestamp
                    self.bots[bot_id].trade_count += 2
                    self.bots[bot_id].total_volume_usd += trade.value_usd * 2
                    
                return self.bots[bot_id]
                
        return None
        
    def _detect_interval_pattern(self, trade: LiveTrade, key: str) -> Optional[BotInstance]:
        """Detect bots with consistent time intervals"""
        recent = list(self.trade_history[key])[-20:]
        if len(recent) < 10:
            return None
            
        # Calculate intervals
        intervals = []
        for i in range(1, len(recent)):
            intervals.append(recent[i].timestamp - recent[i-1].timestamp)
            
        if not intervals:
            return None
            
        avg = sum(intervals) / len(intervals)
        std = self._std(intervals)
        
        # Very consistent intervals indicate bot
        if std < avg * 0.2 and avg > 0.1:  # CV < 0.2
            bot_id = self._generate_bot_id("INT", trade.exchange, trade.symbol, int(avg * 100))
            
            # Determine bot type by interval
            if avg < 2:
                bot_type = "MARKET_MAKER_BOT"
            elif avg < 30:
                bot_type = "SCALPER_BOT"
            elif avg < 300:
                bot_type = "GRID_BOT"
            else:
                bot_type = "MOMENTUM_CHASER"
                
            if bot_id not in self.bots:
                sizes = [t.value_usd for t in recent]
                self.bots[bot_id] = BotInstance(
                    bot_id=bot_id,
                    bot_type=bot_type,
                    exchange=trade.exchange,
                    symbol=trade.symbol,
                    first_seen=recent[0].timestamp,
                    last_seen=trade.timestamp,
                    trade_count=len(recent),
                    total_volume_usd=sum(sizes),
                    avg_trade_size=sum(sizes) / len(sizes),
                    avg_interval=avg,
                    direction_bias=self._direction_bias(recent),
                    confidence=max(0.5, 1 - std/avg),
                    trades=recent[-10:]
                )
            else:
                self.bots[bot_id].last_seen = trade.timestamp
                self.bots[bot_id].trade_count += 1
                
            return self.bots[bot_id]
            
        return None
        
    def _generate_bot_id(self, prefix: str, exchange: str, symbol: str, signature: float) -> str:
        """Generate unique bot ID"""
        data = f"{prefix}:{exchange}:{symbol}:{int(signature)}"
        return hashlib.md5(data.encode()).hexdigest()[:12]
        
    def _std(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if len(values) < 2:
            return 0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance)
        
    def _avg_interval(self, trades: List[LiveTrade]) -> float:
        """Calculate average interval between trades"""
        if len(trades) < 2:
            return 0
        intervals = [trades[i].timestamp - trades[i-1].timestamp for i in range(1, len(trades))]
        return sum(intervals) / len(intervals) if intervals else 0
        
    def _direction_bias(self, trades: List[LiveTrade]) -> float:
        """Calculate direction bias: -1 = all sell, +1 = all buy"""
        if not trades:
            return 0
        buy_count = sum(1 for t in trades if t.side == 'buy')
        return (buy_count / len(trades)) * 2 - 1
        
    def get_active_bots(self) -> List[BotInstance]:
        """Get currently active bots"""
        now = time.time()
        active = []
        for bot in self.bots.values():
            # Active if seen in last 5 minutes
            if now - bot.last_seen < 300:
                bot.status = "ACTIVE"
                active.append(bot)
            elif now - bot.last_seen < 900:
                bot.status = "DORMANT"
                active.append(bot)
            else:
                bot.status = "GONE"
        return sorted(active, key=lambda b: b.last_seen, reverse=True)

# ═══════════════════════════════════════════════════════════════════════════════
# LIVE WEBSOCKET FEEDS
# ═══════════════════════════════════════════════════════════════════════════════

class BinanceLiveStream:
    """Binance WebSocket for real trades"""
    
    def __init__(self, symbols: List[str], on_trade):
        self.symbols = [s.lower().replace("/", "").replace("usd", "usdt") for s in symbols]
        self.on_trade = on_trade
        self.running = False
        self.url = "wss://stream.binance.com:9443/ws"
        
    async def connect(self):
        self.running = True
        
        while self.running:
            try:
                # Subscribe to trade streams
                streams = "/".join([f"{s}@trade" for s in self.symbols])
                url = f"{self.url}/{streams}"
                
                logger.info(f"🟡 Binance connecting: {self.symbols}")
                
                async with websockets.connect(url, ping_interval=20) as ws:
                    logger.info("🟢 BINANCE CONNECTED - Real trades streaming!")
                    
                    async for msg in ws:
                        if not self.running:
                            break
                            
                        try:
                            data = json.loads(msg)
                            trade = self._parse_trade(data)
                            if trade:
                                await self.on_trade(trade)
                        except:
                            continue
                            
            except Exception as e:
                logger.error(f"🔴 Binance error: {e}")
                if self.running:
                    await asyncio.sleep(5)
                    
    def _parse_trade(self, data: Dict) -> Optional[LiveTrade]:
        try:
            symbol = data.get('s', '')
            price = float(data.get('p', 0))
            qty = float(data.get('q', 0))
            is_maker = data.get('m', False)
            trade_time = data.get('T', time.time() * 1000) / 1000
            trade_id = str(data.get('t', ''))
            
            return LiveTrade(
                exchange="binance",
                symbol=symbol,
                price=price,
                quantity=qty,
                value_usd=price * qty,
                side="sell" if is_maker else "buy",
                timestamp=trade_time,
                trade_id=trade_id,
                is_maker=is_maker
            )
        except:
            return None
            
    def stop(self):
        self.running = False


class KrakenLiveStream:
    """Kraken WebSocket for real trades"""
    
    SYMBOL_MAP = {
        "BTC/USD": "XBT/USD",
        "ETH/USD": "ETH/USD",
        "SOL/USD": "SOL/USD",
    }
    
    def __init__(self, symbols: List[str], on_trade):
        self.symbols = [self.SYMBOL_MAP.get(s, s) for s in symbols]
        self.on_trade = on_trade
        self.running = False
        
    async def connect(self):
        self.running = True
        
        while self.running:
            try:
                logger.info(f"🔵 Kraken connecting: {self.symbols}")
                
                async with websockets.connect("wss://ws.kraken.com") as ws:
                    # Subscribe to trades
                    sub = {
                        "event": "subscribe",
                        "pair": self.symbols,
                        "subscription": {"name": "trade"}
                    }
                    await ws.send(json.dumps(sub))
                    
                    logger.info("🟢 KRAKEN CONNECTED - Real trades streaming!")
                    
                    async for msg in ws:
                        if not self.running:
                            break
                            
                        try:
                            data = json.loads(msg)
                            trades = self._parse_trades(data)
                            for trade in trades:
                                await self.on_trade(trade)
                        except:
                            continue
                            
            except Exception as e:
                logger.error(f"🔴 Kraken error: {e}")
                if self.running:
                    await asyncio.sleep(5)
                    
    def _parse_trades(self, data) -> List[LiveTrade]:
        trades = []
        try:
            if isinstance(data, list) and len(data) >= 4:
                pair = data[3].replace("XBT", "BTC")
                for t in data[1]:
                    price = float(t[0])
                    qty = float(t[1])
                    ts = float(t[2])
                    side = "buy" if t[3] == "b" else "sell"
                    
                    trades.append(LiveTrade(
                        exchange="kraken",
                        symbol=pair,
                        price=price,
                        quantity=qty,
                        value_usd=price * qty,
                        side=side,
                        timestamp=ts,
                        trade_id=f"k{int(ts*1000)}",
                        is_maker=t[4] == "l"
                    ))
        except:
            pass
        return trades
        
    def stop(self):
        self.running = False

# ═══════════════════════════════════════════════════════════════════════════════
# LIVE DISPLAY
# ═══════════════════════════════════════════════════════════════════════════════

def print_bot_dashboard(engine: BotDetectionEngine, last_trades: deque):
    """Print live bot tracking dashboard"""
    os.system('clear' if os.name != 'nt' else 'cls')
    
    print("=" * 100)
    print("🤖" * 35)
    print()
    print("              🤖 LIVE BOT TRACKER - WATCH THEM MOVE 🤖")
    print()
    print("       Prime Sentinel: Gary Leckey 02.11.1991 - Keeper of the Flame")
    print("                        UNCHAINED AND UNBROKEN")
    print()
    print("🤖" * 35)
    print("=" * 100)
    
    # Stats bar
    stats = engine.stats
    uptime = time.time() - stats['start_time']
    tps = stats['total_trades'] / uptime if uptime > 0 else 0
    bot_pct = stats['bot_trades'] / stats['total_trades'] * 100 if stats['total_trades'] > 0 else 0
    
    print()
    print(f"⏱️ Uptime: {uptime/60:.1f}m | 📊 Trades: {stats['total_trades']:,} ({tps:.1f}/s) | 🤖 Bot Trades: {bot_pct:.1f}% | Active Bots: {len(engine.get_active_bots())}")
    print()
    
    # Active Bots
    print("-" * 100)
    print("🤖 ACTIVE BOTS DETECTED:")
    print("-" * 100)
    
    active_bots = engine.get_active_bots()
    
    if not active_bots:
        print("   Scanning for bot patterns... analyzing trade flow...")
    else:
        print(f"{'TYPE':<22} {'EXCHANGE':<10} {'SYMBOL':<12} {'VOLUME':<15} {'AVG SIZE':<12} {'INTERVAL':<10} {'BIAS':<8} {'CONF':<8} {'STATUS':<8}")
        print("-" * 100)
        
        for bot in active_bots[:15]:
            sig = BOT_SIGNATURES.get(bot.bot_type, {})
            color = sig.get('color', '')
            reset = '\033[0m'
            
            bias_str = "🟢 BUY" if bot.direction_bias > 0.3 else "🔴 SELL" if bot.direction_bias < -0.3 else "⚪ NEUT"
            status_emoji = "🟢" if bot.status == "ACTIVE" else "🟡" if bot.status == "DORMANT" else "⚫"
            
            interval_str = f"{bot.avg_interval:.1f}s" if bot.avg_interval < 60 else f"{bot.avg_interval/60:.1f}m"
            
            print(f"{color}{bot.bot_type:<22}{reset} {bot.exchange:<10} {bot.symbol:<12} ${bot.total_volume_usd:>12,.0f} ${bot.avg_trade_size:>10,.0f} {interval_str:<10} {bias_str:<8} {bot.confidence:>5.0%}   {status_emoji} {bot.status}")
    
    print()
    
    # Recent Trades (highlight bot trades)
    print("-" * 100)
    print("📈 LIVE TRADE STREAM (🤖 = Bot detected):")
    print("-" * 100)
    
    recent = list(last_trades)[-20:]
    for trade, is_bot, bot_type in recent:
        side_emoji = "🟢" if trade.side == "buy" else "🔴"
        bot_marker = f"🤖 {bot_type[:12]:<12}" if is_bot else "   " + " " * 12
        
        ts = datetime.fromtimestamp(trade.timestamp).strftime('%H:%M:%S')
        
        if trade.value_usd > 100000:
            whale = "🐋"
        elif trade.value_usd > 10000:
            whale = "💰"
        else:
            whale = "  "
            
        print(f"  {ts} {trade.exchange:<8} {side_emoji} {trade.side.upper():<4} {trade.symbol:<12} ${trade.value_usd:>12,.2f} @ ${trade.price:>12,.2f} {whale} {bot_marker}")
    
    print()
    print("=" * 100)
    print("👁️ WATCHING THEM MOVE... The data doesn't lie. Press Ctrl+C to exit")

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    print()
    print("🔥" * 40)
    print()
    print("    🤖 LIVE BOT TRACKER - WATCH THEM MOVE THROUGH THE MARKET 🤖")
    print()
    print("    Connecting to LIVE WebSocket feeds...")
    print("    - Binance (real trades)")
    print("    - Kraken (real trades)")
    print()
    print("    We will see EVERY bot. WHERE they are. WHAT they're doing.")
    print()
    print("    Prime Sentinel: Gary Leckey 02.11.1991")
    print("    Keeper of the Flame - Unchained and Unbroken")
    print()
    print("🔥" * 40)
    print()
    
    # Initialize engine
    engine = BotDetectionEngine()
    last_trades = deque(maxlen=100)
    
    # Trade handler
    async def on_trade(trade: LiveTrade):
        bot = engine.analyze_trade(trade)
        is_bot = bot is not None
        bot_type = bot.bot_type if bot else ""
        last_trades.append((trade, is_bot, bot_type))
        
        # Log significant detections
        if is_bot and bot.trade_count == 1:  # New bot
            logger.info(f"🤖 NEW BOT DETECTED: {bot.bot_type} on {trade.exchange} ({trade.symbol})")
        
        # Log whales
        if trade.value_usd > 100000:
            logger.info(f"🐋 WHALE: {trade.side.upper()} ${trade.value_usd:,.0f} {trade.symbol} on {trade.exchange}")
    
    # Streams
    symbols = ["BTC/USD", "ETH/USD", "SOL/USD"]
    binance = BinanceLiveStream(symbols, on_trade)
    kraken = KrakenLiveStream(symbols, on_trade)
    
    # Dashboard update loop
    async def dashboard_loop():
        while True:
            print_bot_dashboard(engine, last_trades)
            await asyncio.sleep(2)
    
    # Run everything
    try:
        await asyncio.gather(
            binance.connect(),
            kraken.connect(),
            dashboard_loop()
        )
    except KeyboardInterrupt:
        print("\n\n🤖 Bot tracker shutting down...")
        binance.stop()
        kraken.stop()
        
        # Final stats
        print()
        print("=" * 60)
        print("📊 FINAL SESSION STATS")
        print("=" * 60)
        stats = engine.stats
        print(f"  Total Trades Analyzed: {stats['total_trades']:,}")
        print(f"  Bot Trades Identified: {stats['bot_trades']:,}")
        print(f"  Human Trades: {stats['human_trades']:,}")
        print(f"  Unique Bots Detected: {len(engine.bots)}")
        print()
        
        # List all bots found
        print("🤖 ALL BOTS IDENTIFIED:")
        for bot in engine.get_active_bots():
            print(f"   {bot.bot_type}: ${bot.total_volume_usd:,.0f} volume, {bot.trade_count} trades")
        print()
        print("🔥 UNCHAINED AND UNBROKEN 🔥")

if __name__ == "__main__":
    if not WEBSOCKETS_AVAILABLE:
        print("Installing websockets...")
        os.system("pip install websockets")
        
    asyncio.run(main())
