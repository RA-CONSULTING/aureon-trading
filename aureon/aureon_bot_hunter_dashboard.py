#!/usr/bin/env python3
"""
🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥
║                                                                               ║
║   🤖 BOT HUNTER DASHBOARD - VISUAL REAL-TIME TRACKING 🤖                      ║
║                                                                               ║
║   Web dashboard to SEE every bot move through the market                      ║
║   - Real WebSocket data from Binance & Kraken                                 ║
║   - Visual bot identification                                                 ║
║   - Trade flow visualization                                                  ║
║   - Pattern detection graphs                                                  ║
║                                                                               ║
║   Prime Sentinel: Gary Leckey 02.11.1991                                      ║
║   Keeper of the Flame - Unchained and Unbroken                                ║
║                                                                               ║
🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import json
import time
import math
import asyncio
import logging
import hashlib
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Set
from collections import deque, defaultdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')
logger = logging.getLogger(__name__)

try:
    import websockets
except ImportError:
    os.system("pip install websockets")
    import websockets

try:
    import aiohttp
    from aiohttp import web
except ImportError:
    os.system("pip install aiohttp")
    import aiohttp
    from aiohttp import web

# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Trade:
    exchange: str
    symbol: str
    price: float
    quantity: float
    value_usd: float
    side: str
    timestamp: float
    trade_id: str
    is_bot: bool = False
    bot_type: str = ""

@dataclass
class Bot:
    bot_id: str
    bot_type: str
    exchange: str
    symbol: str
    first_seen: float
    last_seen: float
    trades: int
    volume: float
    avg_size: float
    avg_interval: float
    direction: float  # -1 sell, +1 buy
    confidence: float
    status: str = "ACTIVE"
    color: str = "#00ff00"

# ═══════════════════════════════════════════════════════════════════════════════
# BOT DETECTION ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class BotEngine:
    BOT_COLORS = {
        "MARKET_MAKER": "#00ffff",
        "SCALPER": "#00ff00",
        "ICEBERG": "#0066ff",
        "INSTITUTIONAL": "#ff00ff",
        "WASH_TRADER": "#ff0000",
        "GRID_BOT": "#ffff00",
        "MOMENTUM": "#ff6600",
        "HFT": "#ffffff",
    }
    
    def __init__(self):
        self.trades = defaultdict(lambda: deque(maxlen=500))
        self.bots: Dict[str, Bot] = {}
        self.size_freq = defaultdict(lambda: defaultdict(int))
        self.stats = {'total': 0, 'bot': 0, 'human': 0, 'start': time.time()}
        
    def analyze(self, trade: Trade) -> Optional[Bot]:
        self.stats['total'] += 1
        key = f"{trade.exchange}:{trade.symbol}"
        self.trades[key].append(trade)
        
        if len(self.trades[key]) < 5:
            return None
            
        bot = (
            self._detect_hft(trade, key) or
            self._detect_market_maker(trade, key) or
            self._detect_iceberg(trade, key) or
            self._detect_scalper(trade, key) or
            self._detect_wash(trade, key) or
            self._detect_pattern(trade, key)
        )
        
        if bot:
            self.stats['bot'] += 1
            trade.is_bot = True
            trade.bot_type = bot.bot_type
        else:
            self.stats['human'] += 1
            
        return bot
        
    def _detect_hft(self, trade: Trade, key: str) -> Optional[Bot]:
        """High-frequency trading: many trades per second"""
        recent = list(self.trades[key])[-50:]
        if len(recent) < 20:
            return None
            
        # Count trades in last second
        now = trade.timestamp
        trades_1s = sum(1 for t in recent if now - t.timestamp < 1)
        
        if trades_1s >= 10:  # 10+ trades per second
            return self._create_bot("HFT", trade, recent, 0.9)
        return None
        
    def _detect_market_maker(self, trade: Trade, key: str) -> Optional[Bot]:
        recent = list(self.trades[key])[-30:]
        if len(recent) < 15:
            return None
            
        # Check alternation
        alternations = sum(1 for i in range(1, len(recent)) if recent[i].side != recent[i-1].side)
        alt_ratio = alternations / (len(recent) - 1)
        
        # Check timing
        intervals = [recent[i].timestamp - recent[i-1].timestamp for i in range(1, len(recent))]
        avg_int = sum(intervals) / len(intervals)
        
        # Check size consistency
        sizes = [t.value_usd for t in recent]
        cv = self._cv(sizes)
        
        if alt_ratio > 0.7 and avg_int < 5 and cv < 0.4:
            return self._create_bot("MARKET_MAKER", trade, recent, alt_ratio)
        return None
        
    def _detect_iceberg(self, trade: Trade, key: str) -> Optional[Bot]:
        rounded = round(trade.value_usd / 50) * 50
        self.size_freq[key][rounded] += 1
        
        if self.size_freq[key][rounded] >= 5:
            recent = list(self.trades[key])[-50:]
            similar = [t for t in recent if abs(t.value_usd - rounded) < rounded * 0.15]
            
            if len(similar) >= 5:
                buys = sum(1 for t in similar if t.side == 'buy')
                direction_ratio = max(buys, len(similar)-buys) / len(similar)
                
                if direction_ratio > 0.75:
                    return self._create_bot("ICEBERG", trade, similar, direction_ratio)
        return None
        
    def _detect_scalper(self, trade: Trade, key: str) -> Optional[Bot]:
        recent = list(self.trades[key])[-30:]
        if len(recent) < 15:
            return None
            
        # Look for quick reversals
        pairs = []
        for i, t1 in enumerate(recent):
            for t2 in recent[i+1:]:
                if t1.side != t2.side and abs(t2.timestamp - t1.timestamp) < 30:
                    if abs(t1.value_usd - t2.value_usd) / max(t1.value_usd, 1) < 0.25:
                        pairs.append((t1, t2))
                        
        if len(pairs) >= 3:
            return self._create_bot("SCALPER", trade, [t for p in pairs for t in p], len(pairs) / 10)
        return None
        
    def _detect_wash(self, trade: Trade, key: str) -> Optional[Bot]:
        recent = list(self.trades[key])[-10:]
        
        for prev in recent[:-1]:
            if (prev.side != trade.side and
                abs(prev.value_usd - trade.value_usd) < trade.value_usd * 0.02 and
                abs(trade.timestamp - prev.timestamp) < 0.5):
                return self._create_bot("WASH_TRADER", trade, [prev, trade], 0.95)
        return None
        
    def _detect_pattern(self, trade: Trade, key: str) -> Optional[Bot]:
        recent = list(self.trades[key])[-25:]
        if len(recent) < 12:
            return None
            
        intervals = [recent[i].timestamp - recent[i-1].timestamp for i in range(1, len(recent))]
        avg = sum(intervals) / len(intervals)
        cv = self._cv(intervals)
        
        if cv < 0.25 and avg > 0.05:
            if avg < 1:
                return self._create_bot("HFT", trade, recent, 1 - cv)
            elif avg < 15:
                return self._create_bot("SCALPER", trade, recent, 1 - cv)
            elif avg < 120:
                return self._create_bot("GRID_BOT", trade, recent, 1 - cv)
            else:
                return self._create_bot("MOMENTUM", trade, recent, 1 - cv)
        return None
        
    def _create_bot(self, bot_type: str, trade: Trade, trades: List[Trade], conf: float) -> Bot:
        bot_id = hashlib.md5(f"{bot_type}:{trade.exchange}:{trade.symbol}:{len(trades)}".encode()).hexdigest()[:10]
        
        if bot_id in self.bots:
            self.bots[bot_id].last_seen = trade.timestamp
            self.bots[bot_id].trades += 1
            self.bots[bot_id].volume += trade.value_usd
            return self.bots[bot_id]
            
        sizes = [t.value_usd for t in trades]
        intervals = [trades[i].timestamp - trades[i-1].timestamp for i in range(1, len(trades))]
        buys = sum(1 for t in trades if t.side == 'buy')
        
        self.bots[bot_id] = Bot(
            bot_id=bot_id,
            bot_type=bot_type,
            exchange=trade.exchange,
            symbol=trade.symbol,
            first_seen=trades[0].timestamp,
            last_seen=trade.timestamp,
            trades=len(trades),
            volume=sum(sizes),
            avg_size=sum(sizes) / len(sizes),
            avg_interval=sum(intervals) / len(intervals) if intervals else 0,
            direction=(buys / len(trades)) * 2 - 1,
            confidence=min(conf, 0.99),
            color=self.BOT_COLORS.get(bot_type, "#888888")
        )
        return self.bots[bot_id]
        
    def _cv(self, values: List[float]) -> float:
        if len(values) < 2 or sum(values) == 0:
            return 999
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance) / mean if mean > 0 else 999
        
    def get_active(self) -> List[Bot]:
        now = time.time()
        active = []
        for bot in self.bots.values():
            age = now - bot.last_seen
            if age < 60:
                bot.status = "ACTIVE"
                active.append(bot)
            elif age < 300:
                bot.status = "DORMANT"
                active.append(bot)
        return sorted(active, key=lambda b: b.last_seen, reverse=True)

# ═══════════════════════════════════════════════════════════════════════════════
# WEBSOCKET FEEDS
# ═══════════════════════════════════════════════════════════════════════════════

class Feeds:
    def __init__(self, on_trade):
        self.on_trade = on_trade
        self.running = False
        
    async def binance(self, symbols):
        self.running = True
        syms = [s.lower().replace("/", "").replace("usd", "usdt") for s in symbols]
        streams = "/".join([f"{s}@trade" for s in syms])
        url = f"wss://stream.binance.com:9443/ws/{streams}"
        
        while self.running:
            try:
                async with websockets.connect(url, ping_interval=20) as ws:
                    logger.info("🟢 BINANCE CONNECTED")
                    async for msg in ws:
                        if not self.running:
                            break
                        try:
                            d = json.loads(msg)
                            t = Trade(
                                exchange="binance",
                                symbol=d.get('s', ''),
                                price=float(d.get('p', 0)),
                                quantity=float(d.get('q', 0)),
                                value_usd=float(d.get('p', 0)) * float(d.get('q', 0)),
                                side="sell" if d.get('m') else "buy",
                                timestamp=d.get('T', time.time()*1000) / 1000,
                                trade_id=str(d.get('t', ''))
                            )
                            await self.on_trade(t)
                        except:
                            continue
            except Exception as e:
                logger.error(f"Binance error: {e}")
                if self.running:
                    await asyncio.sleep(3)
                    
    async def kraken(self, symbols):
        self.running = True
        pairs = [s.replace("BTC", "XBT") for s in symbols]
        
        while self.running:
            try:
                async with websockets.connect("wss://ws.kraken.com") as ws:
                    await ws.send(json.dumps({
                        "event": "subscribe",
                        "pair": pairs,
                        "subscription": {"name": "trade"}
                    }))
                    logger.info("🟢 KRAKEN CONNECTED")
                    async for msg in ws:
                        if not self.running:
                            break
                        try:
                            d = json.loads(msg)
                            if isinstance(d, list) and len(d) >= 4:
                                pair = d[3].replace("XBT", "BTC")
                                for trade_data in d[1]:
                                    t = Trade(
                                        exchange="kraken",
                                        symbol=pair,
                                        price=float(trade_data[0]),
                                        quantity=float(trade_data[1]),
                                        value_usd=float(trade_data[0]) * float(trade_data[1]),
                                        side="buy" if trade_data[3] == "b" else "sell",
                                        timestamp=float(trade_data[2]),
                                        trade_id=f"k{int(float(trade_data[2])*1000)}"
                                    )
                                    await self.on_trade(t)
                        except:
                            continue
            except Exception as e:
                logger.error(f"Kraken error: {e}")
                if self.running:
                    await asyncio.sleep(3)
                    
    def stop(self):
        self.running = False

# ═══════════════════════════════════════════════════════════════════════════════
# WEB DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

HTML_DASHBOARD = """
<!DOCTYPE html>
<html>
<head>
    <title>🤖 BOT HUNTER - Live Market Surveillance</title>
    <meta charset="UTF-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #0a0a0f;
            color: #00ff88;
            font-family: 'Courier New', monospace;
            overflow-x: hidden;
        }
        .header {
            background: linear-gradient(90deg, #ff0066, #6600ff, #00ff66, #ff6600);
            background-size: 400% 400%;
            animation: gradient 3s ease infinite;
            padding: 20px;
            text-align: center;
            border-bottom: 2px solid #00ff88;
        }
        @keyframes gradient {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        .header h1 {
            font-size: 2.5em;
            color: #fff;
            text-shadow: 0 0 20px #00ff88;
        }
        .header p { color: #ddd; margin-top: 10px; }
        .stats-bar {
            display: flex;
            justify-content: space-around;
            background: #111;
            padding: 15px;
            border-bottom: 1px solid #333;
        }
        .stat {
            text-align: center;
        }
        .stat-value {
            font-size: 2em;
            color: #00ff88;
        }
        .stat-label { color: #888; }
        .main-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            padding: 20px;
        }
        .panel {
            background: #111;
            border: 1px solid #333;
            border-radius: 10px;
            overflow: hidden;
        }
        .panel-header {
            background: #1a1a1a;
            padding: 15px;
            border-bottom: 1px solid #333;
            font-size: 1.2em;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .panel-content {
            padding: 15px;
            max-height: 400px;
            overflow-y: auto;
        }
        .bot-card {
            background: #1a1a1a;
            border-left: 4px solid;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 5px;
            transition: transform 0.2s;
        }
        .bot-card:hover {
            transform: translateX(5px);
        }
        .bot-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
        }
        .bot-type {
            font-weight: bold;
            font-size: 1.1em;
        }
        .bot-status {
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.8em;
        }
        .status-active { background: #00ff88; color: #000; }
        .status-dormant { background: #ffaa00; color: #000; }
        .bot-stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            font-size: 0.9em;
            color: #aaa;
        }
        .trade-row {
            display: grid;
            grid-template-columns: 80px 80px 60px 100px 120px 80px auto;
            padding: 8px 0;
            border-bottom: 1px solid #222;
            font-size: 0.9em;
            align-items: center;
        }
        .trade-buy { color: #00ff88; }
        .trade-sell { color: #ff4466; }
        .bot-indicator {
            background: #ff00ff;
            color: #fff;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.75em;
        }
        .whale-indicator { color: #00aaff; font-size: 1.2em; }
        .flow-bar {
            height: 30px;
            display: flex;
            margin: 10px 0;
            border-radius: 5px;
            overflow: hidden;
        }
        .flow-buy {
            background: linear-gradient(90deg, #00ff88, #00aa55);
            transition: width 0.5s;
        }
        .flow-sell {
            background: linear-gradient(90deg, #ff4466, #aa2244);
            transition: width 0.5s;
        }
        .flow-labels {
            display: flex;
            justify-content: space-between;
            color: #888;
            font-size: 0.9em;
        }
        #price-chart {
            width: 100%;
            height: 200px;
            background: #0a0a0f;
        }
        .price-display {
            font-size: 2em;
            text-align: center;
            padding: 20px;
        }
        .price-btc { color: #f7931a; }
        .price-eth { color: #627eea; }
        .price-sol { color: #9945ff; }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .live-dot {
            width: 10px;
            height: 10px;
            background: #ff0000;
            border-radius: 50%;
            display: inline-block;
            animation: pulse 1s infinite;
        }
        .footer {
            text-align: center;
            padding: 20px;
            background: #111;
            border-top: 1px solid #333;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 BOT HUNTER DASHBOARD 🤖</h1>
        <p>Real-Time Market Manipulation Detection | Prime Sentinel: Gary Leckey 02.11.1991</p>
        <p style="margin-top: 5px; font-size: 0.9em;">👁️ WATCHING THEM MOVE THROUGH THE MARKET 👁️</p>
    </div>
    
    <div class="stats-bar">
        <div class="stat">
            <div class="stat-value" id="total-trades">0</div>
            <div class="stat-label">Total Trades</div>
        </div>
        <div class="stat">
            <div class="stat-value" id="trades-per-sec">0</div>
            <div class="stat-label">Trades/sec</div>
        </div>
        <div class="stat">
            <div class="stat-value" id="bot-percent">0%</div>
            <div class="stat-label">Bot Trades</div>
        </div>
        <div class="stat">
            <div class="stat-value" id="active-bots">0</div>
            <div class="stat-label">Active Bots</div>
        </div>
        <div class="stat">
            <div class="stat-value" id="volume">$0</div>
            <div class="stat-label">Volume</div>
        </div>
    </div>
    
    <div class="main-grid">
        <div class="panel">
            <div class="panel-header">
                <span class="live-dot"></span>
                🤖 ACTIVE BOTS DETECTED
            </div>
            <div class="panel-content" id="bot-list">
                <p style="color: #666;">Scanning for bot patterns...</p>
            </div>
        </div>
        
        <div class="panel">
            <div class="panel-header">
                <span class="live-dot"></span>
                📈 LIVE TRADE STREAM
            </div>
            <div class="panel-content" id="trade-list">
                <p style="color: #666;">Connecting to exchanges...</p>
            </div>
        </div>
        
        <div class="panel">
            <div class="panel-header">
                💰 BUY/SELL FLOW
            </div>
            <div class="panel-content">
                <h3 style="color: #f7931a;">BTC</h3>
                <div class="flow-bar">
                    <div class="flow-buy" id="btc-buy" style="width: 50%;"></div>
                    <div class="flow-sell" id="btc-sell" style="width: 50%;"></div>
                </div>
                <div class="flow-labels">
                    <span id="btc-buy-vol">$0</span>
                    <span id="btc-sell-vol">$0</span>
                </div>
                
                <h3 style="color: #627eea; margin-top: 20px;">ETH</h3>
                <div class="flow-bar">
                    <div class="flow-buy" id="eth-buy" style="width: 50%;"></div>
                    <div class="flow-sell" id="eth-sell" style="width: 50%;"></div>
                </div>
                <div class="flow-labels">
                    <span id="eth-buy-vol">$0</span>
                    <span id="eth-sell-vol">$0</span>
                </div>
                
                <h3 style="color: #9945ff; margin-top: 20px;">SOL</h3>
                <div class="flow-bar">
                    <div class="flow-buy" id="sol-buy" style="width: 50%;"></div>
                    <div class="flow-sell" id="sol-sell" style="width: 50%;"></div>
                </div>
                <div class="flow-labels">
                    <span id="sol-buy-vol">$0</span>
                    <span id="sol-sell-vol">$0</span>
                </div>
            </div>
        </div>
        
        <div class="panel">
            <div class="panel-header">
                💲 LIVE PRICES
            </div>
            <div class="panel-content">
                <div class="price-display">
                    <div class="price-btc">BTC: $<span id="btc-price">0</span></div>
                    <div class="price-eth">ETH: $<span id="eth-price">0</span></div>
                    <div class="price-sol">SOL: $<span id="sol-price">0</span></div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="footer">
        <p>🔥 UNCHAINED AND UNBROKEN 🔥</p>
        <p style="margin-top: 5px;">Data from: Binance WebSocket | Kraken WebSocket | System Hub API</p>
    </div>

    <script>
        const ws = new WebSocket('ws://' + window.location.host + '/ws');
        
        // Central Hub API for additional data
        const HUB_API = 'http://localhost:13001/api';
        
        async function fetchHubData() {
            try {
                const [bots, whales, live] = await Promise.all([
                    fetch(HUB_API + '/bots').then(r => r.json()).catch(() => ({})),
                    fetch(HUB_API + '/whales').then(r => r.json()).catch(() => ({})),
                    fetch(HUB_API + '/live').then(r => r.json()).catch(() => ({}))
                ]);
                
                // Update bot count from hub
                if (bots.bots_detected && bots.bots_detected.length > 0) {
                    const activeBots = bots.bots_detected.filter(b => b.confidence > 0.5).length;
                    document.getElementById('active-bots').textContent = activeBots + '+';
                    
                    // Add hub bots to the list
                    const hubBots = bots.bots_detected.filter(b => b.symbol).slice(0, 5).map(b => ({
                        id: 'HUB-' + b.type,
                        name: b.type + ' Bot',
                        symbol: b.symbol,
                        trades: Math.floor(b.confidence * 100),
                        type: b.type,
                        confidence: (b.confidence * 100).toFixed(0) + '%'
                    }));
                    if (hubBots.length > 0) {
                        updateBotList(hubBots);
                    }
                }
                
                // Update whale stats
                if (whales.total_whale_events) {
                    console.log('🐋 Hub whale events:', whales.total_whale_events);
                }
                
                // Update queen signal display
                if (live.queen_signal) {
                    const signalPct = (live.queen_signal * 100).toFixed(1);
                    document.getElementById('bot-percent').textContent = signalPct + '%';
                }
                
            } catch (e) {
                console.log('Hub fetch error:', e);
            }
        }
        
        // Poll hub every 3 seconds
        setInterval(fetchHubData, 3000);
        fetchHubData();
        
        const trades = [];
        const flow = {
            BTC: {buy: 0, sell: 0},
            ETH: {buy: 0, sell: 0},
            SOL: {buy: 0, sell: 0}
        };
        let prices = {BTC: 0, ETH: 0, SOL: 0};
        let totalVolume = 0;
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.type === 'trade') {
                const trade = data.trade;
                trades.unshift(trade);
                if (trades.length > 50) trades.pop();
                
                // Update flow
                const sym = trade.symbol.includes('BTC') ? 'BTC' : 
                           trade.symbol.includes('ETH') ? 'ETH' : 
                           trade.symbol.includes('SOL') ? 'SOL' : null;
                if (sym) {
                    if (trade.side === 'buy') {
                        flow[sym].buy += trade.value_usd;
                    } else {
                        flow[sym].sell += trade.value_usd;
                    }
                    prices[sym] = trade.price;
                }
                totalVolume += trade.value_usd;
                
                updateTradeList();
                updateFlow();
                updatePrices();
            }
            
            if (data.type === 'stats') {
                document.getElementById('total-trades').textContent = data.total.toLocaleString();
                document.getElementById('trades-per-sec').textContent = data.tps.toFixed(1);
                document.getElementById('bot-percent').textContent = data.bot_pct.toFixed(1) + '%';
                document.getElementById('active-bots').textContent = data.active_bots;
                document.getElementById('volume').textContent = '$' + formatNum(totalVolume);
            }
            
            if (data.type === 'bots') {
                updateBotList(data.bots);
            }
        };
        
        function updateTradeList() {
            const list = document.getElementById('trade-list');
            list.innerHTML = trades.slice(0, 30).map(t => {
                const sideClass = t.side === 'buy' ? 'trade-buy' : 'trade-sell';
                const sideIcon = t.side === 'buy' ? '🟢' : '🔴';
                const whale = t.value_usd > 50000 ? '🐋' : t.value_usd > 10000 ? '💰' : '';
                const botTag = t.is_bot ? `<span class="bot-indicator">🤖 ${t.bot_type}</span>` : '';
                
                const time = new Date(t.timestamp * 1000).toLocaleTimeString();
                
                return `
                    <div class="trade-row ${sideClass}">
                        <span>${time}</span>
                        <span>${t.exchange}</span>
                        <span>${sideIcon} ${t.side.toUpperCase()}</span>
                        <span>${t.symbol}</span>
                        <span>$${t.value_usd.toLocaleString(undefined, {maximumFractionDigits: 2})}</span>
                        <span>${whale}</span>
                        <span>${botTag}</span>
                    </div>
                `;
            }).join('');
        }
        
        function updateBotList(bots) {
            const list = document.getElementById('bot-list');
            if (!bots || bots.length === 0) {
                list.innerHTML = '<p style="color: #666;">Scanning for bot patterns...</p>';
                return;
            }
            
            list.innerHTML = bots.map(b => {
                const statusClass = b.status === 'ACTIVE' ? 'status-active' : 'status-dormant';
                const direction = b.direction > 0.3 ? '📈 BUYING' : b.direction < -0.3 ? '📉 SELLING' : '↔️ NEUTRAL';
                
                return `
                    <div class="bot-card" style="border-color: ${b.color}">
                        <div class="bot-header">
                            <span class="bot-type" style="color: ${b.color}">${b.bot_type}</span>
                            <span class="bot-status ${statusClass}">${b.status}</span>
                        </div>
                        <div class="bot-stats">
                            <div>📍 ${b.exchange}</div>
                            <div>🪙 ${b.symbol}</div>
                            <div>📊 ${b.trades} trades</div>
                            <div>💰 $${formatNum(b.volume)}</div>
                            <div>📏 Avg: $${formatNum(b.avg_size)}</div>
                            <div>⏱️ ${b.avg_interval.toFixed(1)}s</div>
                            <div>${direction}</div>
                            <div>🎯 ${(b.confidence * 100).toFixed(0)}%</div>
                        </div>
                    </div>
                `;
            }).join('');
        }
        
        function updateFlow() {
            for (const sym of ['BTC', 'ETH', 'SOL']) {
                const total = flow[sym].buy + flow[sym].sell;
                if (total > 0) {
                    const buyPct = (flow[sym].buy / total * 100);
                    const sellPct = 100 - buyPct;
                    document.getElementById(sym.toLowerCase() + '-buy').style.width = buyPct + '%';
                    document.getElementById(sym.toLowerCase() + '-sell').style.width = sellPct + '%';
                    document.getElementById(sym.toLowerCase() + '-buy-vol').textContent = '$' + formatNum(flow[sym].buy);
                    document.getElementById(sym.toLowerCase() + '-sell-vol').textContent = '$' + formatNum(flow[sym].sell);
                }
            }
        }
        
        function updatePrices() {
            document.getElementById('btc-price').textContent = prices.BTC.toLocaleString(undefined, {maximumFractionDigits: 2});
            document.getElementById('eth-price').textContent = prices.ETH.toLocaleString(undefined, {maximumFractionDigits: 2});
            document.getElementById('sol-price').textContent = prices.SOL.toLocaleString(undefined, {maximumFractionDigits: 2});
        }
        
        function formatNum(n) {
            if (n >= 1000000) return (n/1000000).toFixed(2) + 'M';
            if (n >= 1000) return (n/1000).toFixed(1) + 'K';
            return n.toFixed(0);
        }
    </script>
</body>
</html>
"""

# ═══════════════════════════════════════════════════════════════════════════════
# WEB SERVER
# ═══════════════════════════════════════════════════════════════════════════════

class DashboardServer:
    def __init__(self, engine: BotEngine):
        self.engine = engine
        self.clients: Set[web.WebSocketResponse] = set()
        self.app = web.Application()
        self.app.router.add_get('/', self.index)
        self.app.router.add_get('/ws', self.websocket)
        
    async def index(self, request):
        return web.Response(text=HTML_DASHBOARD, content_type='text/html')
        
    async def websocket(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.clients.add(ws)
        logger.info(f"📱 Client connected ({len(self.clients)} total)")
        
        try:
            async for msg in ws:
                pass
        finally:
            self.clients.discard(ws)
            
        return ws
        
    async def broadcast(self, data: dict):
        for ws in list(self.clients):
            try:
                await ws.send_json(data)
            except:
                self.clients.discard(ws)
                
    async def broadcast_trade(self, trade: Trade):
        await self.broadcast({
            'type': 'trade',
            'trade': asdict(trade)
        })
        
    async def broadcast_stats(self):
        stats = self.engine.stats
        uptime = time.time() - stats['start']
        tps = stats['total'] / uptime if uptime > 0 else 0
        bot_pct = stats['bot'] / stats['total'] * 100 if stats['total'] > 0 else 0
        
        await self.broadcast({
            'type': 'stats',
            'total': stats['total'],
            'tps': tps,
            'bot_pct': bot_pct,
            'active_bots': len(self.engine.get_active())
        })
        
    async def broadcast_bots(self):
        bots = self.engine.get_active()
        await self.broadcast({
            'type': 'bots',
            'bots': [asdict(b) for b in bots[:20]]
        })
        
    def run(self, port=9999):
        return web._run_app(self.app, port=port, print=None)

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    print()
    print("🔥" * 40)
    print()
    print("    🤖 BOT HUNTER DASHBOARD 🤖")
    print()
    print("    WATCHING THEM MOVE THROUGH THE MARKET")
    print()
    print("    Prime Sentinel: Gary Leckey 02.11.1991")
    print("    Keeper of the Flame - Unchained and Unbroken")
    print()
    print("🔥" * 40)
    print()
    
    # Initialize
    engine = BotEngine()
    server = DashboardServer(engine)
    
    # Trade callback
    async def on_trade(trade: Trade):
        bot = engine.analyze(trade)
        await server.broadcast_trade(trade)
        
    feeds = Feeds(on_trade)
    
    # Stats broadcast loop
    async def stats_loop():
        while True:
            await server.broadcast_stats()
            await server.broadcast_bots()
            await asyncio.sleep(1)
    
    # Start server
    runner = web.AppRunner(server.app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 9999)
    await site.start()
    
    print()
    print("🌐 DASHBOARD LIVE AT: http://localhost:9999")
    print()
    print("Connecting to exchanges...")
    print()
    
    symbols = ["BTC/USD", "ETH/USD", "SOL/USD"]
    
    try:
        await asyncio.gather(
            feeds.binance(symbols),
            feeds.kraken(symbols),
            stats_loop()
        )
    except KeyboardInterrupt:
        feeds.stop()
        await runner.cleanup()
        
        print()
        print("=" * 60)
        print("📊 SESSION SUMMARY")
        print("=" * 60)
        stats = engine.stats
        print(f"  Total Trades: {stats['total']:,}")
        print(f"  Bot Trades: {stats['bot']:,}")
        print(f"  Bots Found: {len(engine.bots)}")
        print()
        for bot in engine.get_active()[:10]:
            print(f"  🤖 {bot.bot_type}: ${bot.volume:,.0f} volume")
        print()
        print("🔥 UNCHAINED AND UNBROKEN 🔥")

if __name__ == "__main__":
    asyncio.run(main())
