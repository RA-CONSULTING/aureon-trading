#!/usr/bin/env python3
"""
KRAKEN MARGIN ARMY TRADER - ALL IN, GBP1 PROFIT, OUT
=====================================================
Army discipline: 1 position only. ALL margin. Max leverage.
Capture GBP1 real realized profit (~$1.27). Close. Next target. Repeat.

ARCHITECTURE:
  MONITORING -> FREE APIs (Binance public REST — no auth, no limits)
  EXECUTION  -> Kraken API (open + close ONLY — 3 calls per trade cycle)

  Kraken API calls per trade:
    1. get_trade_balance()       check margin before opening
    2. place_margin_order()      open the position
    3. close_margin_position()   close when profitable

  ALL price monitoring uses Binance public API.
  Zero rate-limit risk. Zero wasted Kraken calls.

Usage:
    python kraken_margin_penny_trader.py              # Live trading
    python kraken_margin_penny_trader.py --dry-run     # Simulation mode
    python kraken_margin_penny_trader.py --scan-only   # Show margin pairs
"""

import os
import json
import time
import hashlib
import logging
import argparse
import threading
import urllib.request
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import deque

# Import ETA predictor for margin positions
try:
    from margin_eta_predictor import MarginETAPredictor
    HAS_ETA_PREDICTOR = True
except ImportError:
    HAS_ETA_PREDICTOR = False
    logger_temp = logging.getLogger("margin_army")
    logger_temp.warning("ETA predictor not available - install margin_eta_predictor.py")

# Dead Man's Switch - Dynamic Take Profit
try:
    from dynamic_take_profit import DynamicTakeProfit, DTP_CONFIG
    HAS_DTP = True
except ImportError:
    HAS_DTP = False
    DynamicTakeProfit = None
    DTP_CONFIG = {'activation_threshold': 15.0, 'trailing_distance_pct': 0.02, 'gbp_usd_rate': 1.27}

# Margin Wave Rider - pre-entry 250% margin safety gate
try:
    from margin_wave_rider import MarginWaveRider, WAVE_CONFIG
    HAS_WAVE_RIDER = True
except ImportError:
    HAS_WAVE_RIDER = False
    MarginWaveRider = None
    WAVE_CONFIG = {'entry_min_margin_pct': 250.0, 'danger_margin_pct': 110.0}

# Stallion Tracker - Apache phase intelligence (ROPING→BUCKING→TIRING→TAMED)
try:
    from stallion_tracker import classify_phase, StallionPhase
    HAS_STALLION = True
except ImportError:
    HAS_STALLION = False
    classify_phase = None
    StallionPhase = None

# Stallion Multiverse - parallel shadow rides + 1-hour rotation
try:
    from stallion_multiverse import StallionMultiverse, MULTIVERSE_CONFIG
    HAS_MULTIVERSE = True
except ImportError:
    HAS_MULTIVERSE = False
    StallionMultiverse = None
    MULTIVERSE_CONFIG = {'real_ride_limit_secs': 3600, 'max_shadows': 10}

# Multiverse Learning Bridge - adaptive learning → Seer, Lyra, pre-trade
try:
    from multiverse_learning_bridge import MultiverseLearningBridge
    HAS_LEARNING_BRIDGE = True
except ImportError:
    HAS_LEARNING_BRIDGE = False
    MultiverseLearningBridge = None

try:
    import websocket as _ws_lib
    HAS_WEBSOCKET = True
except ImportError:
    HAS_WEBSOCKET = False

try:
    import numpy as np # type: ignore
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("margin_army")

# ==============================================================
#  CONFIGURATION - ARMY DISCIPLINE
# ==============================================================
PROFIT_TARGET_USD = 1.27      # GBP1 approx USD1.27 - minimum net profit to close
MIN_PROFIT_USD = 1.27         # Same - the gate
MONITOR_INTERVAL = 2          # Seconds between FREE API price checks
ENTRY_SCAN_INTERVAL = 30      # Seconds between scanning for new entry
LIQUIDATION_WARN = 150        # Margin level % warning
LIQUIDATION_FORCE = 110       # Margin level % force-close (Kraken liquidates at ~40%)
MARGIN_WAVE_ENTRY_PCT = 250.0 # Minimum PROJECTED margin % before entering any position
                              # Gives ~28% wave cushion at 5x, ~47% at 3x, ~14% at 10x
MIN_TRADE_USD = 25.0          # Minimum trade notional (fee gate)
KRAKEN_TAKER_FEE = 0.004      # 0.40% per side CONSERVATIVE (actual: opens ~0.376%, closes ~0.35%)
KRAKEN_OPEN_FEE = 0.00376     # Actual observed opening fee rate
KRAKEN_CLOSE_FEE = 0.0035     # Actual observed closing fee rate
KRAKEN_ROLLOVER_RATE = 0.0001 # 0.01% per 4 hours (Kraken margin rollover)
KRAKEN_ROLLOVER_INTERVAL = 4 * 3600  # 4 hours in seconds
MARGIN_BUFFER = 0.70          # Use 70% of free margin (30% safety for margin level)
STATE_FILE = "kraken_margin_army_state.json"
RESULTS_FILE = "kraken_margin_army_results.json"
USD_QUOTES = {"USD", "ZUSD"}

# Binance public API - FREE, no auth needed
BINANCE_TICKER_URL = "https://api.binance.com/api/v3/ticker/price"
BINANCE_24H_URL = "https://api.binance.com/api/v3/ticker/24hr"
BINANCE_DEPTH_URL = "https://api.binance.com/api/v3/depth"
BINANCE_TRADES_URL = "https://api.binance.com/api/v3/trades"
BINANCE_AGG_TRADES_URL = "https://api.binance.com/api/v3/aggTrades"
BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"

# === WAR INTELLIGENCE THRESHOLDS ===
WHALE_WALL_USD = 50000        # $50K+ wall = whale detected
WHALE_WALL_BLOCK_RATIO = 3.0  # Wall must be 3x average level size
BOT_PATTERN_THRESHOLD = 5     # 5+ same-size trades = bot detected
MOMENTUM_ALIGNMENT_MIN = 2    # At least 2 of 3 timeframes must agree
FLEE_MOMENTUM_REVERSAL = -0.3 # % reversal per minute = danger
FLEE_SPREAD_BLOWOUT = 0.5     # Spread > 0.5% = liquidity pulled
FLEE_VOLUME_SPIKE = 5.0       # 5x normal volume = whale dump/pump
INTEL_CACHE_SECONDS = 30      # How long intel stays fresh

# === WAVEFORM ANALYSIS THRESHOLDS ===
WAVE_FFT_WINDOW = 256         # FFT window size (power of 2)
WAVE_STFT_HOP = 32            # STFT hop size
WAVE_BOT_CONFIDENCE = 0.6     # Min confidence to flag bot waveform
WAVE_PREDICTION_HORIZON = 60  # Predict next 60 seconds
WAVE_HARMONIC_BANDS = {
    'accumulator': (0.001, 0.01),   # Very slow: whales accumulating over minutes
    'market_maker': (0.01, 0.5),    # Mid: market makers cycling every 2-100s
    'scalper': (0.5, 5.0),          # Fast: scalper bots every 0.2-2s
    'hft': (5.0, 100.0),            # Ultra fast: HFT sub-second
}
WAVE_DANGER_POWER_SHIFT = 2.0  # 2x power shift in opposing band = danger

# Kraken base asset name cleanup (internal -> standard)
KRAKEN_BASE_MAP = {
    "XXBT": "BTC", "XBT": "BTC", "XETH": "ETH", "XLTC": "LTC",
    "XXRP": "XRP", "XDOGE": "DOGE", "XXLM": "XLM", "XZEC": "ZEC",
    "XREP": "REP", "XMLN": "MLN", "XXMR": "XMR", "XETC": "ETC",
    "ZUSD": "USD", "ZEUR": "EUR", "ZGBP": "GBP", "ZJPY": "JPY",
}

# ==============================================================
#  BINANCE LIVE STREAM - FREE WebSocket (sub-second reaction)
# ==============================================================
# Streams: @trade (every trade in real-time) + @depth@100ms (orderbook)
# ZERO API calls. ZERO rate limits. 100% FREE. No auth.
# This replaces 2-second REST polling with sub-100ms live data.
# ==============================================================

BINANCE_WS_URL = "wss://stream.binance.com:9443/stream?streams="

class LiveStream:
    """
    Binance FREE WebSocket stream — sub-second market data.
    Runs in a daemon thread. The army trader reads from cache.
    
    Streams per symbol:
      @trade      — every trade: price, qty, buyer_maker
      @depth@100ms — orderbook changes every 100ms
    
    Cache (thread-safe reads via GIL):
      .price[symbol]        — latest trade price
      .trade_time[symbol]   — timestamp of last trade
      .buy_pressure[symbol] — rolling buy volume (last 5s)
      .sell_pressure[symbol]— rolling sell volume (last 5s)
      .bid_wall[symbol]     — biggest bid within 0.5%
      .ask_wall[symbol]     — biggest ask within 0.5%
      .spread[symbol]       — current spread %
      .trade_velocity[sym]  — trades per second (last 5s)
      .last_trades[symbol]  — deque of last 200 trades (price, qty, is_buy, ts)
      .flash_alert[symbol]  — True if price moved >0.3% in <2s
    """

    def __init__(self):
        self._ws = None
        self._thread = None
        self._running = False
        self._symbols = set()
        self._lock = threading.Lock()
        
        # === LIVE CACHE (read by monitoring loop) ===
        self.price: Dict[str, float] = {}
        self.trade_time: Dict[str, float] = {}
        self.buy_pressure: Dict[str, float] = {}
        self.sell_pressure: Dict[str, float] = {}
        self.bid_wall: Dict[str, float] = {}
        self.ask_wall: Dict[str, float] = {}
        self.spread: Dict[str, float] = {}
        self.trade_velocity: Dict[str, float] = {}
        self.last_trades: Dict[str, deque] = {}
        self.flash_alert: Dict[str, bool] = {}
        self.orderbook: Dict[str, dict] = {}  # {bids: [...], asks: [...]}
        
        # Rolling windows for pressure calculation
        self._trade_buf: Dict[str, deque] = {}  # (ts, qty, is_buy) last 5s
        self._price_buf: Dict[str, deque] = {}  # (ts, price) for flash detection
        
        # Stats
        self.connected = False
        self.msg_count = 0
        self.connect_time = 0.0
        self._reconnect_count = 0
        self._last_msg_time = 0.0

    def start(self, symbols: List[str]):
        """Start streaming for given Binance symbols (e.g. ['ETHUSDT', 'BTCUSDT'])."""
        if not HAS_WEBSOCKET:
            logger.warning("LIVE STREAM: websocket-client not installed — falling back to REST polling")
            return False
        
        self._symbols = set(s.upper() for s in symbols)
        if not self._symbols:
            return False
        
        # Build stream URL
        streams = []
        for sym in self._symbols:
            sl = sym.lower()
            streams.append(f"{sl}@trade")
            streams.append(f"{sl}@bookTicker")  # Best bid/ask in real-time
        
        url = BINANCE_WS_URL + "/".join(streams)
        
        self._running = True
        self._thread = threading.Thread(
            target=self._run_forever,
            args=(url,),
            daemon=True,
            name="LiveStream"
        )
        self._thread.start()
        logger.info(f"LIVE STREAM: Connecting to {len(self._symbols)} symbols ({len(streams)} streams)...")
        return True

    def add_symbol(self, symbol: str):
        """Dynamically subscribe to a new symbol (reconnects)."""
        symbol = symbol.upper()
        if symbol in self._symbols:
            return
        self._symbols.add(symbol)
        # Reconnect with new symbol set
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass

    def stop(self):
        """Stop the stream."""
        self._running = False
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass

    def get_live_price(self, symbol: str) -> float:
        """Get latest price from stream (0 if not available)."""
        return self.price.get(symbol.upper(), 0.0)

    def get_flow_snapshot(self, symbol: str) -> dict:
        """Get current flow analysis from live stream data."""
        sym = symbol.upper()
        bp = self.buy_pressure.get(sym, 0)
        sp = self.sell_pressure.get(sym, 0)
        total = bp + sp
        buy_pct = (bp / total * 100) if total > 0 else 50
        
        return {
            'price': self.price.get(sym, 0),
            'buy_pressure': bp,
            'sell_pressure': sp,
            'buy_pct': buy_pct,
            'sell_pct': 100 - buy_pct,
            'flow_direction': 'buying' if buy_pct > 55 else ('selling' if buy_pct < 45 else 'neutral'),
            'trade_velocity': self.trade_velocity.get(sym, 0),
            'spread_pct': self.spread.get(sym, 0),
            'bid_wall': self.bid_wall.get(sym, 0),
            'ask_wall': self.ask_wall.get(sym, 0),
            'flash_alert': self.flash_alert.get(sym, False),
            'age_ms': int((time.time() - self.trade_time.get(sym, 0)) * 1000) if sym in self.trade_time else -1,
            'connected': self.connected,
            'msg_count': self.msg_count,
        }

    def is_alive(self) -> bool:
        """Check if stream is healthy (received data in last 10s)."""
        if not self.connected:
            return False
        return (time.time() - self._last_msg_time) < 10

    # ---------- INTERNAL ----------

    def _build_url(self) -> str:
        """Build WebSocket URL from current symbol set."""
        streams = []
        for sym in self._symbols:
            sl = sym.lower()
            streams.append(f"{sl}@trade")
            streams.append(f"{sl}@bookTicker")
        return BINANCE_WS_URL + "/".join(streams)

    def _run_forever(self, url: str):
        """WebSocket run loop with auto-reconnect."""
        while self._running:
            # Rebuild URL each iteration to pick up newly added symbols
            current_url = self._build_url()
            try:
                self._ws = _ws_lib.WebSocketApp(
                    current_url,
                    on_message=self._on_message,
                    on_open=self._on_open,
                    on_close=self._on_close,
                    on_error=self._on_error,
                )
                self._ws.run_forever(
                    ping_interval=20,
                    ping_timeout=10,
                    reconnect=5,
                )
            except Exception as e:
                logger.warning(f"LIVE STREAM: Connection error: {e}")
            
            if self._running:
                self._reconnect_count += 1
                wait = min(5 * self._reconnect_count, 30)
                logger.info(f"LIVE STREAM: Reconnecting in {wait}s (attempt #{self._reconnect_count})...")
                self.connected = False
                time.sleep(wait)

    def _on_open(self, ws):
        self.connected = True
        self.connect_time = time.time()
        self._reconnect_count = 0
        logger.info(f"LIVE STREAM: CONNECTED — {len(self._symbols)} symbols streaming in real-time")

    def _on_close(self, ws, close_code, close_msg):
        self.connected = False
        logger.info(f"LIVE STREAM: Disconnected (code={close_code})")

    def _on_error(self, ws, error):
        logger.warning(f"LIVE STREAM: Error: {error}")

    def _on_message(self, ws, raw_msg):
        """Process incoming WebSocket message — sub-millisecond path."""
        try:
            msg = json.loads(raw_msg)
            self.msg_count += 1
            self._last_msg_time = time.time()
            
            # Combined stream format: {"stream": "ethusdt@trade", "data": {...}}
            stream = msg.get("stream", "")
            data = msg.get("data", msg)
            
            if "@trade" in stream and "@bookTicker" not in stream:
                self._handle_trade(data)
            elif "@bookTicker" in stream:
                self._handle_book_ticker(data)
        except Exception:
            pass  # Never crash the stream thread

    def _handle_trade(self, data: dict):
        """Process a single trade — update price + flow."""
        sym = data.get("s", "").upper()
        if not sym:
            return
        
        price = float(data.get("p", 0))
        qty = float(data.get("q", 0))
        is_buyer_maker = data.get("m", False)  # True = seller aggressor (sell), False = buyer aggressor (buy)
        is_buy = not is_buyer_maker
        ts = time.time()
        
        # Update latest price
        self.price[sym] = price
        self.trade_time[sym] = ts
        
        # Store trade
        if sym not in self.last_trades:
            self.last_trades[sym] = deque(maxlen=200)
        self.last_trades[sym].append((price, qty, is_buy, ts))
        
        # Rolling trade buffer (5s window for pressure)
        if sym not in self._trade_buf:
            self._trade_buf[sym] = deque(maxlen=2000)
        self._trade_buf[sym].append((ts, qty * price, is_buy))  # USD volume
        
        # Recalculate pressure (purge >5s old)
        cutoff = ts - 5.0
        buf = self._trade_buf[sym]
        while buf and buf[0][0] < cutoff:
            buf.popleft()
        
        bp = sum(v for _, v, b in buf if b)
        sp = sum(v for _, v, b in buf if not b)
        self.buy_pressure[sym] = bp
        self.sell_pressure[sym] = sp
        
        # Trade velocity (trades per second over 5s)
        self.trade_velocity[sym] = len(buf) / 5.0
        
        # Flash detection: >0.3% move in <2s
        if sym not in self._price_buf:
            self._price_buf[sym] = deque(maxlen=100)
        self._price_buf[sym].append((ts, price))
        flash_cutoff = ts - 2.0
        pbuf = self._price_buf[sym]
        while len(pbuf) > 1 and pbuf[0][0] < flash_cutoff:
            pbuf.popleft()
        if len(pbuf) >= 2:
            oldest_price = pbuf[0][1]
            pct_move = abs(price - oldest_price) / oldest_price * 100
            self.flash_alert[sym] = pct_move > 0.3
        else:
            self.flash_alert[sym] = False

    def _handle_book_ticker(self, data: dict):
        """Process bookTicker — best bid/ask in real-time."""
        sym = data.get("s", "").upper()
        if not sym:
            return
        
        try:
            best_bid = float(data.get("b", 0))
            best_ask = float(data.get("a", 0))
            bid_qty = float(data.get("B", 0))
            ask_qty = float(data.get("A", 0))
            
            if best_bid > 0 and best_ask > 0:
                self.spread[sym] = (best_ask - best_bid) / best_bid * 100
                self.bid_wall[sym] = best_bid * bid_qty  # USD value of best bid
                self.ask_wall[sym] = best_ask * ask_qty  # USD value of best ask
        except (ValueError, ZeroDivisionError):
            pass


@dataclass
class MarginPairInfo:
    """Info about a margin-eligible trading pair."""
    pair: str
    internal: str
    base: str
    base_clean: str
    quote: str
    leverage_buy: list
    leverage_sell: list
    max_leverage: int
    ordermin: float
    lot_decimals: int
    price_decimals: int
    binance_symbol: str = ""
    last_price: float = 0.0
    bid: float = 0.0
    ask: float = 0.0
    spread_pct: float = 0.0
    volume_24h: float = 0.0
    momentum: float = 0.0


@dataclass
class ActiveTrade:
    """The ONE active margin trade."""
    pair: str
    side: str
    volume: float
    entry_price: float
    leverage: int
    entry_fee: float
    entry_time: float
    order_id: str
    cost: float = 0.0
    breakeven_price: float = 0.0
    binance_symbol: str = ""
    rollover_fees: float = 0.0
    last_rollover_check: float = 0.0

    def to_dict(self):
        return asdict(self)


@dataclass
class ShadowTrade:
    """
    Paper trade that validates a prediction BEFORE real capital is deployed.
    Uses live stream data — zero cost, zero risk.
    The system watches the shadow play out and only goes LIVE when
    it proves the prediction was correct.
    """
    pair: str
    side: str               # 'buy' or 'sell'
    binance_symbol: str
    entry_price: float      # Price when shadow opened
    created_at: float       # time.time()
    target_move_pct: float  # How much we need the price to move (fee + profit)
    leverage: int
    volume: float
    trade_val: float
    pair_info_key: str      # Key into margin_pairs dict
    # Tracking
    best_price: float = 0.0   # Best price seen (highest for buy, lowest for sell)
    worst_price: float = 0.0  # Worst price seen
    current_price: float = 0.0
    validated: bool = False    # True when shadow proved profitable
    validation_time: float = 0.0
    peak_pnl_pct: float = 0.0 # Peak % move in our favour

    def update(self, price: float):
        """Update shadow with latest price."""
        self.current_price = price
        if self.side == "buy":
            if price > self.best_price or self.best_price == 0:
                self.best_price = price
            if price < self.worst_price or self.worst_price == 0:
                self.worst_price = price
            move_pct = (price - self.entry_price) / self.entry_price * 100
        else:
            if price < self.best_price or self.best_price == 0:
                self.best_price = price
            if price > self.worst_price or self.worst_price == 0:
                self.worst_price = price
            move_pct = (self.entry_price - price) / self.entry_price * 100

        if move_pct > self.peak_pnl_pct:
            self.peak_pnl_pct = move_pct

        # Shadow is VALIDATED when price moved enough to cover fees + profit
        if move_pct >= self.target_move_pct * 0.5:
            # Price moved at least 50% of what we need — direction is CONFIRMED
            if not self.validated:
                self.validated = True
                self.validation_time = time.time()

    @property
    def age_seconds(self) -> float:
        return time.time() - self.created_at

    @property
    def current_move_pct(self) -> float:
        if self.entry_price <= 0:
            return 0
        if self.side == "buy":
            return (self.current_price - self.entry_price) / self.entry_price * 100
        else:
            return (self.entry_price - self.current_price) / self.entry_price * 100


# ==============================================================
#  FREE PRICE MONITORING - NO KRAKEN API
# ==============================================================
class FreeMarketData:
    """
    Get prices from Binance public API.
    ZERO cost. ZERO auth. ZERO rate limit worries.
    """

    def __init__(self):
        self._binance_prices: Dict[str, float] = {}
        self._binance_24h: Dict[str, dict] = {}
        self._last_fetch = 0
        self._last_24h_fetch = 0

    def fetch_all_binance_prices(self) -> Dict[str, float]:
        """Fetch ALL Binance prices in ONE call."""
        try:
            req = urllib.request.Request(BINANCE_TICKER_URL)
            req.add_header("User-Agent", "AureonTrader/1.0")
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            prices = {}
            for item in data:
                sym = item.get("symbol", "")
                price = float(item.get("price", 0))
                if price > 0:
                    prices[sym] = price
            self._binance_prices = prices
            self._last_fetch = time.time()
            return prices
        except Exception as e:
            logger.warning(f"Binance price fetch failed: {e}")
            return self._binance_prices

    def fetch_binance_24h(self) -> Dict[str, dict]:
        """Fetch 24h stats from Binance (momentum, volume). ONE call."""
        try:
            req = urllib.request.Request(BINANCE_24H_URL)
            req.add_header("User-Agent", "AureonTrader/1.0")
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
            stats = {}
            for item in data:
                sym = item.get("symbol", "")
                stats[sym] = {
                    "price_change_pct": float(item.get("priceChangePercent", 0)),
                    "volume": float(item.get("quoteVolume", 0)),
                    "high": float(item.get("highPrice", 0)),
                    "low": float(item.get("lowPrice", 0)),
                    "bid": float(item.get("bidPrice", 0)),
                    "ask": float(item.get("askPrice", 0)),
                }
            self._binance_24h = stats
            self._last_24h_fetch = time.time()
            return stats
        except Exception as e:
            logger.warning(f"Binance 24h fetch failed: {e}")
            return self._binance_24h

    def get_price(self, binance_symbol: str) -> float:
        """Get cached price for a Binance symbol."""
        return self._binance_prices.get(binance_symbol, 0)

    def get_bid_ask(self, binance_symbol: str) -> Tuple[float, float]:
        """Get bid/ask from 24h data."""
        stats = self._binance_24h.get(binance_symbol, {})
        bid = stats.get("bid", 0)
        ask = stats.get("ask", 0)
        if bid <= 0 or ask <= 0:
            price = self.get_price(binance_symbol)
            return price, price
        return bid, ask

    def get_single_price(self, binance_symbol: str) -> float:
        """Get a FRESH single price from Binance for close decisions."""
        try:
            url = f"{BINANCE_TICKER_URL}?symbol={binance_symbol}"
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "AureonTrader/1.0")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
            price = float(data.get("price", 0))
            if price > 0:
                self._binance_prices[binance_symbol] = price
            return price
        except Exception as e:
            logger.debug(f"Single price fetch failed for {binance_symbol}: {e}")
            return self._binance_prices.get(binance_symbol, 0)


# ==============================================================
#  BATTLEFIELD INTELLIGENCE - FREE API WAR RESEARCH
# ==============================================================
class BattlefieldIntel:
    """
    War intelligence using 100% FREE Binance API.
    - Orderbook depth: Detect whale walls
    - Trade flow: Detect bot patterns & aggressor direction
    - Multi-timeframe momentum: Confirm direction across 1h/4h/1d
    - Volatility: Check if required move is achievable
    - Live danger detection: Flee triggers during monitoring
    """

    def __init__(self):
        self._depth_cache: Dict[str, dict] = {}
        self._trades_cache: Dict[str, list] = {}
        self._klines_cache: Dict[str, dict] = {}
        self._cache_times: Dict[str, float] = {}
        self._baseline_volume: Dict[str, float] = {}  # Normal per-minute volume
        self._last_prices: Dict[str, list] = {}  # Price history for momentum tracking
        self.waveform = None  # Initialized lazily after WaveformAnalyzer class defined

    def _fetch_json(self, url: str, timeout: int = 8) -> Any:
        """Fetch JSON from Binance FREE API."""
        try:
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "AureonWarIntel/1.0")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            logger.debug(f"Intel fetch failed: {url[:60]}... {e}")
            return None

    # ----------------------------------------------------------
    #  ORDERBOOK DEPTH ANALYSIS (Whale Wall Detection)
    # ----------------------------------------------------------
    def analyze_orderbook(self, symbol: str) -> dict:
        """
        Analyze orderbook depth. Detect whale walls.
        Returns: {
            'bid_walls': [(price, usd_size)],    # Large bid walls
            'ask_walls': [(price, usd_size)],    # Large ask walls
            'bid_depth_usd': float,               # Total bid depth in USD
            'ask_depth_usd': float,               # Total ask depth in USD
            'imbalance': float,                    # bid_depth/ask_depth ratio
            'whale_blocking_buy': bool,            # Whale wall above price (blocks our buy)
            'whale_supporting_buy': bool,          # Whale wall below price (supports our buy)
            'wall_distance_pct': float,            # Distance to nearest blocking wall
        }
        """
        cache_key = f"depth_{symbol}"
        if cache_key in self._cache_times and time.time() - self._cache_times[cache_key] < INTEL_CACHE_SECONDS:
            return self._depth_cache.get(symbol, {})

        url = f"{BINANCE_DEPTH_URL}?symbol={symbol}&limit=50"
        data = self._fetch_json(url)
        if not data:
            return {}

        bids = data.get("bids", [])
        asks = data.get("asks", [])

        result = {
            'bid_walls': [], 'ask_walls': [],
            'bid_depth_usd': 0, 'ask_depth_usd': 0,
            'imbalance': 1.0,
            'whale_blocking_buy': False, 'whale_supporting_buy': False,
            'whale_blocking_sell': False, 'whale_supporting_sell': False,
            'wall_distance_pct': 99.0,
            'best_bid': 0, 'best_ask': 0,
        }

        if not bids or not asks:
            return result

        best_bid = float(bids[0][0])
        best_ask = float(asks[0][0])
        mid_price = (best_bid + best_ask) / 2
        result['best_bid'] = best_bid
        result['best_ask'] = best_ask

        # Analyze bid side
        bid_sizes = []
        for price_s, qty_s in bids:
            price, qty = float(price_s), float(qty_s)
            usd = price * qty
            bid_sizes.append(usd)
            result['bid_depth_usd'] += usd
            if usd >= WHALE_WALL_USD:
                result['bid_walls'].append((price, usd))

        # Analyze ask side
        ask_sizes = []
        for price_s, qty_s in asks:
            price, qty = float(price_s), float(qty_s)
            usd = price * qty
            ask_sizes.append(usd)
            result['ask_depth_usd'] += usd
            if usd >= WHALE_WALL_USD:
                result['ask_walls'].append((price, usd))

        # Depth imbalance (>1 = more buying pressure)
        if result['ask_depth_usd'] > 0:
            result['imbalance'] = result['bid_depth_usd'] / result['ask_depth_usd']

        # Check for whale walls relative to average level
        avg_bid = sum(bid_sizes) / len(bid_sizes) if bid_sizes else 1
        avg_ask = sum(ask_sizes) / len(ask_sizes) if ask_sizes else 1

        # Whale blocking a BUY: Large ask wall within 2% above price
        for price_s, qty_s in asks[:20]:
            price, qty = float(price_s), float(qty_s)
            usd = price * qty
            dist_pct = (price - mid_price) / mid_price * 100
            if usd > avg_ask * WHALE_WALL_BLOCK_RATIO and usd >= WHALE_WALL_USD * 0.5 and dist_pct < 2.0:
                result['whale_blocking_buy'] = True
                result['wall_distance_pct'] = min(result['wall_distance_pct'], dist_pct)

        # Whale supporting a BUY: Large bid wall within 2% below price
        for price_s, qty_s in bids[:20]:
            price, qty = float(price_s), float(qty_s)
            usd = price * qty
            dist_pct = (mid_price - price) / mid_price * 100
            if usd > avg_bid * WHALE_WALL_BLOCK_RATIO and usd >= WHALE_WALL_USD * 0.5 and dist_pct < 2.0:
                result['whale_supporting_buy'] = True

        # Whale blocking a SELL (large bid wall = hard to sell through)
        for price_s, qty_s in bids[:20]:
            price, qty = float(price_s), float(qty_s)
            usd = price * qty
            dist_pct = (mid_price - price) / mid_price * 100
            if usd > avg_bid * WHALE_WALL_BLOCK_RATIO and usd >= WHALE_WALL_USD * 0.5 and dist_pct < 2.0:
                result['whale_blocking_sell'] = True

        self._depth_cache[symbol] = result
        self._cache_times[cache_key] = time.time()
        return result

    # ----------------------------------------------------------
    #  TRADE FLOW ANALYSIS (Bot Detection + Aggressor Side)
    # ----------------------------------------------------------
    def analyze_trade_flow(self, symbol: str) -> dict:
        """
        Analyze recent trades. Detect bots & institutional flow.
        Returns: {
            'bot_detected': bool,
            'bot_type': str,                # 'none', 'grid', 'iceberg', 'market_maker'
            'buy_volume_pct': float,         # % of volume that's aggressive buys
            'sell_volume_pct': float,        # % of volume that's aggressive sells
            'flow_direction': str,           # 'buying', 'selling', 'neutral'
            'flow_strength': float,          # 0-1 how strong the directional flow
            'avg_trade_usd': float,          # Average trade size
            'large_trade_pct': float,        # % of volume from large trades
            'trades_per_second': float,      # Activity rate
        }
        """
        cache_key = f"trades_{symbol}"
        if cache_key in self._cache_times and time.time() - self._cache_times[cache_key] < INTEL_CACHE_SECONDS:
            return self._trades_cache.get(symbol, {})

        url = f"{BINANCE_TRADES_URL}?symbol={symbol}&limit=500"
        data = self._fetch_json(url, timeout=10)
        if not data or len(data) < 10:
            return {'bot_detected': False, 'bot_type': 'none', 'flow_direction': 'neutral',
                    'flow_strength': 0, 'buy_volume_pct': 50, 'sell_volume_pct': 50,
                    'avg_trade_usd': 0, 'large_trade_pct': 0, 'trades_per_second': 0}

        buy_vol = 0
        sell_vol = 0
        trade_sizes = []
        total_usd = 0
        times = []

        for t in data:
            price = float(t.get("price", 0))
            qty = float(t.get("qty", 0))
            usd = price * qty
            is_buyer_maker = t.get("isBuyerMaker", False)
            ts = t.get("time", 0)

            trade_sizes.append(usd)
            total_usd += usd
            times.append(ts)

            if is_buyer_maker:
                sell_vol += usd   # Buyer is maker = seller is aggressor (taker sell)
            else:
                buy_vol += usd    # Buyer is taker = aggressive buy

        total = buy_vol + sell_vol
        buy_pct = (buy_vol / total * 100) if total > 0 else 50
        sell_pct = 100 - buy_pct

        # Flow direction
        if buy_pct > 60:
            direction = "buying"
            strength = min((buy_pct - 50) / 30, 1.0)
        elif sell_pct > 60:
            direction = "selling"
            strength = min((sell_pct - 50) / 30, 1.0)
        else:
            direction = "neutral"
            strength = 0

        # Average trade size
        avg_usd = total_usd / len(data) if data else 0

        # Large trades (>10x average)
        large_vol = sum(s for s in trade_sizes if s > avg_usd * 10)
        large_pct = (large_vol / total_usd * 100) if total_usd > 0 else 0

        # Trades per second
        if len(times) >= 2:
            time_span = (max(times) - min(times)) / 1000  # ms to seconds
            tps = len(data) / time_span if time_span > 0 else 0
        else:
            tps = 0

        # Store baseline volume for spike detection
        if symbol not in self._baseline_volume:
            self._baseline_volume[symbol] = tps
        else:
            self._baseline_volume[symbol] = self._baseline_volume[symbol] * 0.9 + tps * 0.1

        # BOT DETECTION: Look for patterns
        bot_detected = False
        bot_type = "none"

        # Pattern 1: Grid bot - identical trade sizes repeated
        size_counts: Dict[str, int] = {}
        for s in trade_sizes:
            key = f"{s:.2f}"
            size_counts[key] = size_counts.get(key, 0) + 1
        max_repeat = max(size_counts.values()) if size_counts else 0
        if max_repeat >= BOT_PATTERN_THRESHOLD:
            bot_detected = True
            bot_type = "grid"

        # Pattern 2: Iceberg - many same-size aggressive buys/sells in sequence
        consecutive_same = 0
        max_consecutive = 0
        last_size = None
        for t in data:
            qty = float(t.get("qty", 0))
            size_key = f"{qty:.6f}"
            if size_key == last_size:
                consecutive_same += 1
                max_consecutive = max(max_consecutive, consecutive_same)
            else:
                consecutive_same = 1
            last_size = size_key
        if max_consecutive >= 4:
            bot_detected = True
            bot_type = "iceberg"

        # Pattern 3: HFT - extremely high trade rate
        if tps > 10:  # >10 trades per second
            bot_detected = True
            bot_type = "hft" if bot_type == "none" else bot_type

        result = {
            'bot_detected': bot_detected,
            'bot_type': bot_type,
            'buy_volume_pct': buy_pct,
            'sell_volume_pct': sell_pct,
            'flow_direction': direction,
            'flow_strength': strength,
            'avg_trade_usd': avg_usd,
            'large_trade_pct': large_pct,
            'trades_per_second': tps,
        }
        self._trades_cache[symbol] = result
        self._cache_times[cache_key] = time.time()
        return result

    # ----------------------------------------------------------
    #  MULTI-TIMEFRAME MOMENTUM (Candlestick Alignment)
    # ----------------------------------------------------------
    def analyze_momentum(self, symbol: str) -> dict:
        """
        Check if momentum aligns across multiple timeframes.
        Uses Binance klines (free).
        Returns: {
            'aligned': bool,                 # All timeframes agree
            'alignment_count': int,           # How many agree (0-3)
            'direction': str,                # 'up', 'down', 'mixed'
            'tf_1h': float,                   # 1h momentum %
            'tf_4h': float,                   # 4h momentum %
            'tf_1d': float,                   # 1d momentum %
            'volatility_1h': float,           # 1h range as %
            'achievable': bool,               # Required move < recent volatility
        }
        """
        cache_key = f"klines_{symbol}"
        if cache_key in self._cache_times and time.time() - self._cache_times[cache_key] < 60:
            return self._klines_cache.get(symbol, {})

        result = {
            'aligned': False, 'alignment_count': 0, 'direction': 'mixed',
            'tf_1h': 0, 'tf_4h': 0, 'tf_1d': 0,
            'volatility_1h': 0, 'achievable': True,
        }

        timeframes = [
            ('1h', 3),   # Last 3 hours
            ('4h', 2),   # Last 8 hours
            ('1d', 2),   # Last 2 days
        ]
        directions = []

        for tf, limit in timeframes:
            url = f"{BINANCE_KLINES_URL}?symbol={symbol}&interval={tf}&limit={limit}"
            data = self._fetch_json(url)
            if not data or len(data) < 2:
                continue

            latest = data[-1]
            o, h, l, c = float(latest[1]), float(latest[2]), float(latest[3]), float(latest[4])
            change_pct = (c - o) / o * 100 if o > 0 else 0
            volatility = (h - l) / o * 100 if o > 0 else 0

            if tf == '1h':
                result['tf_1h'] = change_pct
                result['volatility_1h'] = volatility
            elif tf == '4h':
                result['tf_4h'] = change_pct
            elif tf == '1d':
                result['tf_1d'] = change_pct

            if change_pct > 0.05:
                directions.append('up')
            elif change_pct < -0.05:
                directions.append('down')
            else:
                directions.append('flat')

        # Check alignment
        up_count = directions.count('up')
        down_count = directions.count('down')

        if up_count >= MOMENTUM_ALIGNMENT_MIN:
            result['direction'] = 'up'
            result['alignment_count'] = up_count
            result['aligned'] = up_count == len(directions)
        elif down_count >= MOMENTUM_ALIGNMENT_MIN:
            result['direction'] = 'down'
            result['alignment_count'] = down_count
            result['aligned'] = down_count == len(directions)
        else:
            result['direction'] = 'mixed'
            result['alignment_count'] = max(up_count, down_count)

        self._klines_cache[symbol] = result
        self._cache_times[cache_key] = time.time()
        return result

    # ----------------------------------------------------------
    #  PRE-STRIKE RESEARCH (Full Assessment Before Entry)
    # ----------------------------------------------------------
    def pre_strike_research(self, symbol: str, side: str, required_move_pct: float) -> dict:
        """
        Full battlefield research before entering a position.
        Combine orderbook + trade flow + momentum into GO/NO-GO decision.

        Returns: {
            'verdict': str,        # 'GO', 'CAUTION', 'ABORT'
            'confidence': float,   # 0-1
            'reasons': [str],
            'intel': {orderbook, trade_flow, momentum}
        }
        """
        logger.info(f"INTEL: Running pre-strike research on {symbol} ({side.upper()})...")

        orderbook = self.analyze_orderbook(symbol)
        trade_flow = self.analyze_trade_flow(symbol)
        momentum = self.analyze_momentum(symbol)

        reasons = []
        score = 0
        max_score = 0

        # === ORDERBOOK CHECKS ===
        max_score += 3
        if side == "buy":
            if orderbook.get('whale_blocking_buy'):
                wall_dist = orderbook.get('wall_distance_pct', 99)
                if wall_dist < required_move_pct:
                    reasons.append(f"ABORT: Whale wall BLOCKING buy at {wall_dist:.2f}% (need {required_move_pct:.2f}%)")
                    score -= 2
                else:
                    reasons.append(f"WARN: Whale ask wall at {wall_dist:.2f}% but our target is {required_move_pct:.2f}%")
            if orderbook.get('whale_supporting_buy'):
                reasons.append("GOOD: Whale bid support below price")
                score += 2
            imb = orderbook.get('imbalance', 1.0)
            if imb > 1.3:
                reasons.append(f"GOOD: Orderbook favors buy (imbalance={imb:.2f})")
                score += 1
            elif imb < 0.7:
                reasons.append(f"BAD: Orderbook favors sell (imbalance={imb:.2f})")
                score -= 1
        else:  # sell
            if orderbook.get('whale_blocking_sell'):
                reasons.append("WARN: Whale bid wall may block sell")
                score -= 1
            imb = orderbook.get('imbalance', 1.0)
            if imb < 0.7:
                reasons.append(f"GOOD: Orderbook favors sell (imbalance={imb:.2f})")
                score += 1
            elif imb > 1.3:
                reasons.append(f"BAD: Orderbook favors buy, not sell (imbalance={imb:.2f})")
                score -= 1

        # === TRADE FLOW CHECKS ===
        max_score += 3
        flow = trade_flow.get('flow_direction', 'neutral')
        flow_str = trade_flow.get('flow_strength', 0)

        if side == "buy" and flow == "buying":
            reasons.append(f"GOOD: Aggressive buying flow (strength={flow_str:.2f}, {trade_flow['buy_volume_pct']:.0f}% buy)")
            score += 2
        elif side == "sell" and flow == "selling":
            reasons.append(f"GOOD: Aggressive selling flow (strength={flow_str:.2f}, {trade_flow['sell_volume_pct']:.0f}% sell)")
            score += 2
        elif (side == "buy" and flow == "selling") or (side == "sell" and flow == "buying"):
            reasons.append(f"BAD: Flow is AGAINST our {side} ({flow} detected)")
            score -= 2

        if trade_flow.get('bot_detected'):
            reasons.append(f"WARN: Bot detected ({trade_flow['bot_type']}) - market may be manipulated")
            score -= 1

        if trade_flow.get('large_trade_pct', 0) > 30:
            reasons.append(f"WARN: {trade_flow['large_trade_pct']:.0f}% volume from large trades (whale activity)")

        # === MOMENTUM CHECKS ===
        max_score += 3
        mom_dir = momentum.get('direction', 'mixed')
        alignment = momentum.get('alignment_count', 0)

        if (side == "buy" and mom_dir == "up") or (side == "sell" and mom_dir == "down"):
            reasons.append(f"GOOD: Momentum aligned {mom_dir} ({alignment}/3 timeframes)")
            score += alignment
        elif mom_dir == "mixed":
            reasons.append(f"NEUTRAL: Mixed momentum ({alignment}/3 aligned)")
        else:
            reasons.append(f"BAD: Momentum is {mom_dir} but we want to {side}")
            score -= 2

        # Check if volatility supports required move
        vol_1h = momentum.get('volatility_1h', 0)
        if vol_1h > 0 and required_move_pct > 0:
            if vol_1h >= required_move_pct:
                reasons.append(f"GOOD: 1h volatility {vol_1h:.2f}% covers {required_move_pct:.2f}% needed")
                score += 1
            else:
                reasons.append(f"WARN: 1h vol {vol_1h:.2f}% may not cover {required_move_pct:.2f}% needed")

        # === VERDICT ===
        _ = max(0, min(1, (score + max_score) / (2 * max_score)))

        if score >= 3:
            verdict = "GO"
        elif score >= 0:
            verdict = "CAUTION"
        else:
            verdict = "ABORT"

        # Hard ABORT conditions
        if side == "buy" and orderbook.get('whale_blocking_buy'):
            wall_dist = orderbook.get('wall_distance_pct', 99)
            if wall_dist < required_move_pct:
                verdict = "ABORT"
                _ = 0.1

        # === WAVEFORM ANALYSIS (See bot moves BEFORE they happen) ===
        waveform_result = {}
        if self.waveform and HAS_NUMPY:
            try:
                waveform_result = self.waveform.full_scan(symbol, side)
                if waveform_result.get('available'):
                    max_score += 3
                    dom = waveform_result.get('dominant_bot', 'organic')
                    shape = waveform_result.get('shape', 'unknown')
                    res_score = waveform_result.get('resonance_score', 0)
                    res_label = waveform_result.get('resonance_label', 'neutral')
                    flow_pred = waveform_result.get('flow_prediction', 'neutral')
                    energy = waveform_result.get('energy_trend', 0)

                    # Resonance check (bots moving WITH or AGAINST us)
                    if res_label == 'harmony':
                        reasons.append(f"WAVE GOOD: Bots in HARMONY (resonance={res_score:+.2f}, {dom})")
                        score += 2
                    elif res_label == 'dissonance':
                        reasons.append(f"WAVE BAD: Bots in DISSONANCE (resonance={res_score:+.2f}, {dom})")
                        score -= 2
                    else:
                        reasons.append(f"WAVE NEUTRAL: resonance={res_score:+.2f}, dominant={dom}")

                    # Shape/energy check
                    if shape == 'surge':
                        reasons.append(f"WAVE ALERT: Energy SURGING (trend={energy:+.2f}) - bots ramping up!")
                        if res_label == 'dissonance':
                            score -= 1  # Surge AGAINST us = very bad
                    elif shape == 'taper':
                        reasons.append(f"WAVE: Bot activity tapering (trend={energy:+.2f})")

                    # Flow prediction from waveform
                    if side == 'buy' and flow_pred == 'strong_sell_building':
                        reasons.append("WAVE DANGER: Strong sell flow building in waveform")
                        score -= 1
                    elif side == 'sell' and flow_pred == 'strong_buy_building':
                        reasons.append("WAVE DANGER: Strong buy flow building in waveform")
                        score -= 1
                    elif (side == 'buy' and flow_pred == 'strong_buy_building') or \
                         (side == 'sell' and flow_pred == 'strong_sell_building'):
                        reasons.append(f"WAVE GOOD: {flow_pred} supports our {side}")
                        score += 1
            except Exception as e:
                logger.debug(f"Waveform analysis failed: {e}")

        # === VERDICT (recalculate with waveform) ===
        confidence = max(0, min(1, (score + max_score) / (2 * max_score)))

        if score >= 3:
            verdict = "GO"
        elif score >= 0:
            verdict = "CAUTION"
        else:
            verdict = "ABORT"

        # Hard ABORT conditions
        if side == "buy" and orderbook.get('whale_blocking_buy'):
            wall_dist = orderbook.get('wall_distance_pct', 99)
            if wall_dist < required_move_pct:
                verdict = "ABORT"
                confidence = 0.1

        result = {
            'verdict': verdict,
            'confidence': confidence,
            'score': score,
            'max_score': max_score,
            'reasons': reasons,
            'intel': {
                'orderbook': orderbook,
                'trade_flow': trade_flow,
                'momentum': momentum,
                'waveform': waveform_result,
            }
        }

        logger.info(f"INTEL VERDICT: {verdict} (confidence={confidence:.2f}, score={score}/{max_score})")
        for r in reasons:
            logger.info(f"  {r}")

        return result

    # ----------------------------------------------------------
    #  LIVE DANGER DETECTION (Flee Trigger During Monitoring)
    # ----------------------------------------------------------
    def check_danger(self, symbol: str, side: str, entry_price: float,
                     target_price: float) -> dict:
        """
        Quick danger check during position monitoring.
        Returns: {
            'flee': bool,           # Should we close immediately?
            'danger_level': int,    # 0=safe, 1=watch, 2=danger, 3=flee
            'reasons': [str],
        }
        """
        reasons = []
        danger = 0

        # Quick orderbook check
        orderbook = self.analyze_orderbook(symbol)
        trade_flow = self.analyze_trade_flow(symbol)

        # Check 1: Whale wall appeared between us and target
        if side == "buy" and orderbook.get('whale_blocking_buy'):
            ask_walls = orderbook.get('ask_walls', [])
            for wall_price, wall_usd in ask_walls:
                if entry_price < wall_price < target_price:
                    reasons.append(f"DANGER: ${wall_usd:,.0f} whale wall at ${wall_price:.4f} BLOCKING target")
                    danger += 2
                    break

        if side == "sell" and orderbook.get('whale_blocking_sell'):
            bid_walls = orderbook.get('bid_walls', [])
            for wall_price, wall_usd in bid_walls:
                if target_price < wall_price < entry_price:
                    reasons.append(f"DANGER: ${wall_usd:,.0f} whale wall at ${wall_price:.4f} BLOCKING target")
                    danger += 2
                    break

        # Check 2: Flow reversed hard against us
        flow = trade_flow.get('flow_direction', 'neutral')
        flow_str = trade_flow.get('flow_strength', 0)
        if side == "buy" and flow == "selling" and flow_str > 0.5:
            reasons.append(f"DANGER: Strong selling flow ({trade_flow['sell_volume_pct']:.0f}% sells)")
            danger += 1
        elif side == "sell" and flow == "buying" and flow_str > 0.5:
            reasons.append(f"DANGER: Strong buying flow ({trade_flow['buy_volume_pct']:.0f}% buys)")
            danger += 1

        # Check 3: Volume spike (whale dump/pump)
        tps = trade_flow.get('trades_per_second', 0)
        baseline = self._baseline_volume.get(symbol, tps)
        if baseline > 0 and tps > baseline * FLEE_VOLUME_SPIKE:
            reasons.append(f"DANGER: Volume spike {tps:.1f}/s vs normal {baseline:.1f}/s")
            danger += 1

        # Check 4: Spread blowout
        best_bid = orderbook.get('best_bid', 0)
        best_ask = orderbook.get('best_ask', 0)
        if best_bid > 0 and best_ask > 0:
            spread_pct = (best_ask - best_bid) / best_bid * 100
            if spread_pct > FLEE_SPREAD_BLOWOUT:
                reasons.append(f"DANGER: Spread blowout {spread_pct:.3f}% (normal <{FLEE_SPREAD_BLOWOUT}%)")
                danger += 1

        # Check 5: Depth imbalance flip
        imb = orderbook.get('imbalance', 1.0)
        if side == "buy" and imb < 0.5:
            reasons.append(f"DANGER: Depth strongly favors sellers (imb={imb:.2f})")
            danger += 1
        elif side == "sell" and imb > 2.0:
            reasons.append(f"DANGER: Depth strongly favors buyers (imb={imb:.2f})")
            danger += 1

        # Check 6: WAVEFORM ANALYSIS — see the bots' next move
        if self.waveform and HAS_NUMPY:
            try:
                wave = self.waveform.full_scan(symbol, side)
                if wave.get('available'):
                    res_score = wave.get('resonance_score', 0)
                    res_label = wave.get('resonance_label', 'neutral')
                    shape = wave.get('shape', 'unknown')
                    flow_pred = wave.get('flow_prediction', 'neutral')
                    _ = wave.get('energy_trend', 0)
                    shifted = wave.get('spectrum_shifted', False)

                    # Strong dissonance = bots moving against us
                    if res_label == 'dissonance' and res_score < -0.4:
                        reasons.append(f"WAVE DANGER: Bot dissonance {res_score:+.2f} — moving AGAINST us")
                        danger += 1

                    # Energy surge + dissonance = imminent attack
                    if shape == 'surge' and res_label == 'dissonance':
                        reasons.append(f"WAVE CRITICAL: Surge + dissonance — bots attacking our direction!")
                        danger += 2

                    # Sell building when we're long (or vice versa)
                    if side == 'buy' and flow_pred == 'strong_sell_building':
                        reasons.append("WAVE DANGER: Strong sell flow building in waveform")
                        danger += 1
                    elif side == 'sell' and flow_pred == 'strong_buy_building':
                        reasons.append("WAVE DANGER: Strong buy flow building in waveform")
                        danger += 1

                    # Spectrum shift = bots changed strategy
                    if shifted:
                        reasons.append("WAVE ALERT: Spectrum shifted — bots changed strategy!")
                        danger += 1
            except Exception as e:
                logger.debug(f"Waveform danger check failed: {e}")

        flee = danger >= 3
        return {
            'flee': flee,
            'danger_level': min(danger, 3),
            'reasons': reasons,
        }


# ==============================================================
#  WAVEFORM ANALYZER - SEE THEIR MOVES BEFORE THEY MAKE THEM
# ==============================================================
class WaveformAnalyzer:
    """
    The harmonic pool — crypto is a living waveform.
    Bots leave frequency signatures they can't hide.
    FFT reveals their rhythm. STFT shows it evolving.
    We predict their next move before they even make it.

    Input: Raw Binance trades (FREE API, 1000 trades per call)
    Analysis:
      1. FFT Spectral Fingerprint: Volume resampled → frequency bands → bot classification
      2. STFT Price Spectrogram: Log returns → sliding FFT → shape classification
      3. Flow Momentum Waveform: Buy/sell aggressor pressure as wave → phase prediction
      4. Harmonic Resonance: Do bot frequencies align WITH or AGAINST our trade?
    """

    def __init__(self):
        if not HAS_NUMPY:
            logger.warning("numpy not available - WaveformAnalyzer disabled")
        self._trade_buffers: Dict[str, deque] = {}  # Raw trades per symbol
        self._spectral_cache: Dict[str, dict] = {}
        self._cache_times: Dict[str, float] = {}
        self._prev_spectrums: Dict[str, dict] = {}  # Previous spectrum for shift detection
        self._flow_waves: Dict[str, deque] = {}  # Buy/sell pressure wave per symbol

    def _fetch_trades(self, symbol: str) -> list:
        """Fetch 1000 recent trades from Binance (FREE)."""
        try:
            url = f"{BINANCE_AGG_TRADES_URL}?symbol={symbol}&limit=1000"
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "AureonWaveform/1.0")
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            # aggTrades: {a: id, p: price, q: qty, f: first_trade_id, l: last_trade_id, T: timestamp, m: is_buyer_maker}
            trades = []
            for t in data:
                trades.append({
                    'ts': t['T'] / 1000.0,  # ms -> seconds
                    'price': float(t['p']),
                    'qty': float(t['p']) * float(t['q']),  # USD volume
                    'qty_base': float(t['q']),
                    'is_sell': t['m'],  # isBuyerMaker = seller is aggressor
                })
            return trades
        except Exception as e:
            logger.debug(f"Waveform trade fetch failed for {symbol}: {e}")
            return []

    # ----------------------------------------------------------
    #  FFT SPECTRAL FINGERPRINT: What bots are in the pool?
    # ----------------------------------------------------------
    def _fft_spectral_fingerprint(self, trades: list) -> dict:
        """
        Resample trade volume onto uniform time grid.
        Run FFT. Extract power in each frequency band.
        Returns band powers + dominant frequencies + bot classification.
        """
        if not HAS_NUMPY or len(trades) < 50:
            return {}

        # Build time series: volume per time bucket
        ts_start = trades[0]['ts']
        ts_end = trades[-1]['ts']
        duration = ts_end - ts_start
        if duration < 5:  # Need at least 5 seconds of data
            return {}

        # Resample to uniform grid (100ms buckets for good resolution)
        bucket_size = 0.1  # 100ms
        n_buckets = int(duration / bucket_size) + 1
        n_buckets = min(n_buckets, 8192)  # Cap for performance

        # Three signals: total volume, buy volume, sell volume
        vol_signal = np.zeros(n_buckets)
        buy_signal = np.zeros(n_buckets)
        sell_signal = np.zeros(n_buckets)

        for t in trades:
            idx = int((t['ts'] - ts_start) / bucket_size)
            idx = min(idx, n_buckets - 1)
            vol_signal[idx] += t['qty']
            if t['is_sell']:
                sell_signal[idx] += t['qty']
            else:
                buy_signal[idx] += t['qty']

        # Remove DC component (mean)
        vol_centered = vol_signal - np.mean(vol_signal)
        buy_centered = buy_signal - np.mean(buy_signal)
        sell_centered = sell_signal - np.mean(sell_signal)

        # Apply Hanning window to reduce spectral leakage
        window = np.hanning(n_buckets)
        vol_windowed = vol_centered * window
        buy_windowed = buy_centered * window
        sell_windowed = sell_centered * window

        # FFT
        vol_fft = np.abs(np.fft.rfft(vol_windowed))
        buy_fft = np.abs(np.fft.rfft(buy_windowed))
        sell_fft = np.abs(np.fft.rfft(sell_windowed))
        freqs = np.fft.rfftfreq(n_buckets, d=bucket_size)

        # Extract power per harmonic band
        total_power = np.sum(vol_fft) + 1e-10
        bands = {}
        dominant_freq = 0
        dominant_power = 0

        for band_name, (f_lo, f_hi) in WAVE_HARMONIC_BANDS.items():
            mask = (freqs >= f_lo) & (freqs < f_hi)
            if not np.any(mask):
                bands[band_name] = {
                    'power': 0, 'power_pct': 0, 'dominant_freq': 0,
                    'buy_power': 0, 'sell_power': 0, 'buy_sell_ratio': 1.0,
                }
                continue

            band_power = np.sum(vol_fft[mask])
            band_buy = np.sum(buy_fft[mask])
            band_sell = np.sum(sell_fft[mask])

            # Find peak frequency in this band
            band_freqs = freqs[mask]
            band_mags = vol_fft[mask]
            peak_idx = np.argmax(band_mags)
            peak_freq = band_freqs[peak_idx]
            peak_power = band_mags[peak_idx]

            if peak_power > dominant_power:
                dominant_power = peak_power
                dominant_freq = peak_freq

            bands[band_name] = {
                'power': float(band_power),
                'power_pct': float(band_power / total_power * 100),
                'dominant_freq': float(peak_freq),
                'peak_amplitude': float(peak_power),
                'buy_power': float(band_buy),
                'sell_power': float(band_sell),
                'buy_sell_ratio': float(band_buy / (band_sell + 1e-10)),
            }

        # Classify the dominant bot type
        max_band = max(bands.items(), key=lambda x: x[1]['power_pct'])
        bot_class = max_band[0]
        bot_power = max_band[1]['power_pct']

        # Check if organic (no strong peaks, flat spectrum)
        if bot_power < 30:
            bot_class = 'organic'

        return {
            'bands': bands,
            'dominant_freq': float(dominant_freq),
            'dominant_band': bot_class,
            'dominant_power_pct': float(bot_power),
            'total_power': float(total_power),
            'duration_sec': duration,
            'n_trades': len(trades),
        }

    # ----------------------------------------------------------
    #  STFT SPECTROGRAM: How is the waveform EVOLVING?
    # ----------------------------------------------------------
    def _stft_spectrogram(self, trades: list) -> dict:
        """
        Short-time FFT on price log returns.
        Shows how bot activity is CHANGING over time.
        Reveals: are bots ramping up? Fading? Shifting frequency?
        """
        if not HAS_NUMPY or len(trades) < WAVE_FFT_WINDOW:
            return {}

        # Extract price series
        prices = np.array([t['price'] for t in trades])

        # Log returns (the actual signal)
        log_returns = np.diff(np.log(prices + 1e-12))
        if len(log_returns) < WAVE_FFT_WINDOW:
            return {}

        # STFT: sliding window FFT
        n_fft = min(WAVE_FFT_WINDOW, len(log_returns))
        hop = WAVE_STFT_HOP
        frames = []
        timestamps = []

        for start in range(0, len(log_returns) - n_fft + 1, hop):
            chunk = log_returns[start:start + n_fft]
            windowed = chunk * np.hanning(n_fft)
            fft_result = np.fft.rfft(windowed)
            frames.append(np.abs(fft_result))
            # Timestamp of this frame (midpoint)
            mid_idx = start + n_fft // 2
            if mid_idx < len(trades):
                timestamps.append(trades[mid_idx]['ts'])

        if not frames:
            return {}

        S = np.column_stack(frames)  # shape: (n_fft//2+1, n_frames)

        # Spectral features per frame
        freq_bins = np.arange(S.shape[0], dtype=float)
        mean_power = np.mean(S, axis=1) + 1e-12

        # Centroid: where is the "center of mass" of the spectrum?
        centroid = float(np.sum(freq_bins * mean_power) / np.sum(mean_power))

        # Bandwidth: how spread out is the spectrum?
        bandwidth = float(np.sqrt(np.sum(((freq_bins - centroid)**2) * mean_power) / np.sum(mean_power)))

        # Dominant peaks
        sorted_bins = np.argsort(mean_power)[::-1]
        peaks = [{'bin': int(b), 'power': float(mean_power[b])} for b in sorted_bins[:5]]

        # Flatness: geometric_mean / arithmetic_mean (1.0 = white noise, 0.0 = pure tone)
        geo_mean = np.exp(np.mean(np.log(mean_power + 1e-12)))
        arith_mean = np.mean(mean_power)
        flatness = float(geo_mean / (arith_mean + 1e-12))

        # Energy evolution: is the spectrum getting STRONGER or WEAKER over time?
        frame_energies = np.sum(S, axis=0)
        if len(frame_energies) >= 4:
            first_half = np.mean(frame_energies[:len(frame_energies)//2])
            second_half = np.mean(frame_energies[len(frame_energies)//2:])
            energy_trend = float((second_half - first_half) / (first_half + 1e-10))
        else:
            energy_trend = 0.0

        # Classify the spectrogram shape
        shape = self._classify_shape(centroid, bandwidth, flatness, peaks, energy_trend)

        return {
            'centroid': centroid,
            'bandwidth': bandwidth,
            'flatness': flatness,
            'peaks': peaks,
            'energy_trend': energy_trend,
            'shape': shape,
            'n_frames': len(frames),
        }

    def _classify_shape(self, centroid: float, bandwidth: float, flatness: float,
                        peaks: list, energy_trend: float) -> str:
        """
        Classify spectrogram shape — reveals bot strategy.
        - grid: Regular pattern (grid bots placing orders at intervals)
        - oscillator: Single dominant frequency (market maker bouncing)
        - spiral: Wide bandwidth, high centroid (chaotic algo)
        - taper: Energy fading (bot withdrawing from market)
        - surge: Energy increasing (bot ramping up — ALERT!)
        - organic: Flat spectrum, no dominant patterns (real humans)
        """
        # Energy change is the most critical signal
        if energy_trend > 0.5:
            return 'surge'  # Something is ramping up activity — WATCH CLOSELY
        if energy_trend < -0.3:
            return 'taper'  # Activity dying down

        # Multiple strong peaks = grid pattern
        if len(peaks) >= 2 and peaks[1]['power'] > 0.4 * peaks[0]['power'] and flatness < 0.5:
            return 'grid'

        # Single dominant peak = oscillator (market maker)
        if bandwidth < 2.0 and peaks[0]['power'] > 0.5 * sum(p['power'] for p in peaks):
            return 'oscillator'

        # Wide bandwidth + high centroid = chaotic high-freq algo
        if bandwidth > 4.0 and centroid > 3.0:
            return 'spiral'

        # Very flat = organic/noise
        if flatness > 0.8:
            return 'organic'

        return 'mixed'

    # ----------------------------------------------------------
    #  FLOW MOMENTUM WAVEFORM: Buy/Sell pressure as a wave
    # ----------------------------------------------------------
    def _flow_momentum_wave(self, trades: list) -> dict:
        """
        Build the buy/sell pressure wave over time.
        Phase analysis tells us: are buyers or sellers building momentum?
        Derivative tells us: is the momentum ACCELERATING or DECELERATING?
        This predicts the next price move direction.
        """
        if not HAS_NUMPY or len(trades) < 100:
            return {}

        # Build cumulative buy-sell pressure in 1-second buckets
        ts_start = trades[0]['ts']
        ts_end = trades[-1]['ts']
        duration = ts_end - ts_start
        if duration < 10:
            return {}

        n_buckets = min(int(duration), 600)  # 1-second buckets, max 10 min
        flow = np.zeros(n_buckets)

        for t in trades:
            idx = int(t['ts'] - ts_start)
            idx = min(idx, n_buckets - 1)
            if t['is_sell']:
                flow[idx] -= t['qty']
            else:
                flow[idx] += t['qty']

        # Cumulative flow (running sum)
        cum_flow = np.cumsum(flow)

        # Smooth with simple moving average (5-second window)
        kernel = np.ones(5) / 5
        if len(cum_flow) >= 5:
            smoothed = np.convolve(cum_flow, kernel, mode='valid')
        else:
            smoothed = cum_flow

        if len(smoothed) < 3:
            return {}

        # Current phase: last value of cumulative flow
        current_flow = float(cum_flow[-1])

        # Velocity: rate of change (first derivative)
        velocity = np.diff(smoothed)
        current_velocity = float(velocity[-1]) if len(velocity) > 0 else 0

        # Acceleration: rate of velocity change (second derivative)
        if len(velocity) >= 2:
            acceleration = np.diff(velocity)
            current_accel = float(acceleration[-1])
        else:
            current_accel = 0

        # Recent trend (last 20% of data)
        recent_start = max(0, len(smoothed) - len(smoothed) // 5)
        recent = smoothed[recent_start:]
        if len(recent) >= 2:
            recent_slope = float(np.polyfit(range(len(recent)), recent, 1)[0])
        else:
            recent_slope = 0

        # Prediction: extrapolate flow momentum
        # If velocity > 0 AND accelerating → strong buy pressure building
        # If velocity > 0 AND decelerating → buy pressure fading
        # If velocity < 0 AND accelerating down → strong sell pressure building
        if current_velocity > 0 and current_accel > 0:
            prediction = 'strong_buy_building'
            confidence = min(abs(current_velocity) / (abs(current_flow) + 1e-10), 1.0)
        elif current_velocity > 0 and current_accel <= 0:
            prediction = 'buy_fading'
            confidence = 0.3
        elif current_velocity < 0 and current_accel < 0:
            prediction = 'strong_sell_building'
            confidence = min(abs(current_velocity) / (abs(current_flow) + 1e-10), 1.0)
        elif current_velocity < 0 and current_accel >= 0:
            prediction = 'sell_fading'
            confidence = 0.3
        else:
            prediction = 'neutral'
            confidence = 0.1

        return {
            'current_flow': current_flow,
            'velocity': current_velocity,
            'acceleration': current_accel,
            'recent_slope': recent_slope,
            'prediction': prediction,
            'confidence': confidence,
            'total_buy_usd': float(sum(t['qty'] for t in trades if not t['is_sell'])),
            'total_sell_usd': float(sum(t['qty'] for t in trades if t['is_sell'])),
            'duration_sec': duration,
        }

    # ----------------------------------------------------------
    #  HARMONIC RESONANCE: Are bots moving WITH or AGAINST us?
    # ----------------------------------------------------------
    def _harmonic_resonance(self, spectrum: dict, flow: dict, side: str) -> dict:
        """
        The key question: do the bot waveforms HELP or HURT our position?

        If we're LONG (buy):
          - Buy flow building + accumulator power rising = HARMONY (they're buying WITH us)
          - Sell flow building + market_maker power shifting to sell = DISSONANCE (against us)

        Returns resonance score: -1 (total dissonance) to +1 (perfect harmony)
        """
        if not spectrum or not flow:
            return {'resonance': 0, 'label': 'no_data', 'details': []}

        resonance = 0
        details = []
        bands = spectrum.get('bands', {})

        # Check flow alignment
        pred = flow.get('prediction', 'neutral')
        if side == 'buy':
            if pred in ('strong_buy_building', 'buy_fading'):
                resonance += 0.3 if pred == 'strong_buy_building' else 0.1
                details.append(f"Flow: {pred} (helps buy)")
            elif pred in ('strong_sell_building', 'sell_fading'):
                resonance -= 0.3 if pred == 'strong_sell_building' else -0.1
                details.append(f"Flow: {pred} (hurts buy)")
        else:  # sell
            if pred in ('strong_sell_building', 'sell_fading'):
                resonance += 0.3 if pred == 'strong_sell_building' else 0.1
                details.append(f"Flow: {pred} (helps sell)")
            elif pred in ('strong_buy_building', 'buy_fading'):
                resonance -= 0.3 if pred == 'strong_buy_building' else -0.1
                details.append(f"Flow: {pred} (hurts sell)")

        # Check band-level buy/sell power ratios
        for band_name in ['accumulator', 'market_maker', 'scalper']:
            band = bands.get(band_name, {})
            bsr = band.get('buy_sell_ratio', 1.0)
            power_pct = band.get('power_pct', 0)

            if power_pct < 5:  # Negligible band
                continue

            if side == 'buy':
                if bsr > 1.5:
                    resonance += 0.15
                    details.append(f"{band_name}: buy-heavy ({bsr:.1f}x ratio)")
                elif bsr < 0.67:
                    resonance -= 0.15
                    details.append(f"{band_name}: sell-heavy ({bsr:.1f}x ratio)")
            else:
                if bsr < 0.67:
                    resonance += 0.15
                    details.append(f"{band_name}: sell-heavy (helps our sell)")
                elif bsr > 1.5:
                    resonance -= 0.15
                    details.append(f"{band_name}: buy-heavy (hurts our sell)")

        # Check if dominant bot is accumulator (whale) — most important signal
        dom = spectrum.get('dominant_band', 'organic')
        if dom == 'accumulator':
            acc_band = bands.get('accumulator', {})
            acc_bsr = acc_band.get('buy_sell_ratio', 1.0)
            if side == 'buy' and acc_bsr > 1.2:
                resonance += 0.2
                details.append("WHALE ACCUMULATING (buying with us)")
            elif side == 'buy' and acc_bsr < 0.8:
                resonance -= 0.2
                details.append("WHALE DISTRIBUTING (selling against us)")
            elif side == 'sell' and acc_bsr < 0.8:
                resonance += 0.2
                details.append("WHALE DISTRIBUTING (selling with us)")
            elif side == 'sell' and acc_bsr > 1.2:
                resonance -= 0.2
                details.append("WHALE ACCUMULATING (buying against us)")

        resonance = max(-1, min(1, resonance))

        if resonance > 0.3:
            label = 'harmony'
        elif resonance < -0.3:
            label = 'dissonance'
        else:
            label = 'neutral'

        return {
            'resonance': float(resonance),
            'label': label,
            'details': details,
        }

    # ----------------------------------------------------------
    #  SPECTRUM SHIFT DETECTION: Did the waveform change?
    # ----------------------------------------------------------
    def _detect_spectrum_shift(self, symbol: str, current: dict) -> dict:
        """
        Compare current spectrum to previous.
        A sudden shift means bots are changing strategy.
        """
        prev = self._prev_spectrums.get(symbol)
        if not prev or not current:
            self._prev_spectrums[symbol] = current
            return {'shifted': False, 'shift_magnitude': 0, 'details': []}

        details = []
        total_shift = 0

        curr_bands = current.get('bands', {})
        prev_bands = prev.get('bands', {})

        for band_name in WAVE_HARMONIC_BANDS:
            curr_pct = curr_bands.get(band_name, {}).get('power_pct', 0)
            prev_pct = prev_bands.get(band_name, {}).get('power_pct', 0)
            delta = curr_pct - prev_pct

            if abs(delta) > 10:  # >10% shift in band power
                direction = "increased" if delta > 0 else "decreased"
                details.append(f"{band_name} {direction} {abs(delta):.0f}%")
                total_shift += abs(delta)

        shifted = total_shift > 20  # Total >20% cross-band shift
        self._prev_spectrums[symbol] = current

        return {
            'shifted': shifted,
            'shift_magnitude': total_shift,
            'details': details,
        }

    # ----------------------------------------------------------
    #  FULL WAVEFORM SCAN: The complete picture
    # ----------------------------------------------------------
    def full_scan(self, symbol: str, side: str = 'buy') -> dict:
        """
        Complete waveform analysis on a symbol.
        Returns the full harmonic picture: who's in the pool,
        what they're doing, and whether it helps or hurts us.
        """
        if not HAS_NUMPY:
            return {'available': False, 'reason': 'numpy not installed'}

        cache_key = f"wave_{symbol}"
        if cache_key in self._cache_times and time.time() - self._cache_times[cache_key] < 10:
            return self._spectral_cache.get(symbol, {})

        trades = self._fetch_trades(symbol)
        if len(trades) < 50:
            return {'available': False, 'reason': f'only {len(trades)} trades'}

        # Run all analyzers
        spectrum = self._fft_spectral_fingerprint(trades)
        spectrogram = self._stft_spectrogram(trades)
        flow = self._flow_momentum_wave(trades)
        resonance = self._harmonic_resonance(spectrum, flow, side)
        shift = self._detect_spectrum_shift(symbol, spectrum)

        result = {
            'available': True,
            'symbol': symbol,
            'side': side,
            'spectrum': spectrum,
            'spectrogram': spectrogram,
            'flow': flow,
            'resonance': resonance,
            'shift': shift,
            'timestamp': time.time(),
            # === SUMMARY for quick decisions ===
            'dominant_bot': spectrum.get('dominant_band', 'unknown'),
            'dominant_power': spectrum.get('dominant_power_pct', 0),
            'shape': spectrogram.get('shape', 'unknown'),
            'energy_trend': spectrogram.get('energy_trend', 0),
            'flow_prediction': flow.get('prediction', 'neutral'),
            'flow_velocity': flow.get('velocity', 0),
            'resonance_score': resonance.get('resonance', 0),
            'resonance_label': resonance.get('label', 'neutral'),
            'spectrum_shifted': shift.get('shifted', False),
        }

        self._spectral_cache[symbol] = result
        self._cache_times[cache_key] = time.time()
        return result


# ==============================================================
#  BOT CATALOG - LABEL, TRACK, AND PREDICT EVERY PLAYER
# ==============================================================
# Firm signatures: frequency range → name + animal mascot
# Source: aureon_bot_intelligence_profiler.py (30+ firms)
FIRM_SIGNATURES = {
    # firm_id: (name, animal, freq_lo_Hz, freq_hi_Hz, order_size_lo, order_size_hi, mm_ratio, strategies)
    'jane_street':    ('Jane Street',         '🦈 Shark',     0.5, 8.0,   50000, 500000, 0.80, ['mm', 'arb', 'hft']),
    'citadel':        ('Citadel Securities',   '🦁 Lion',      1.0, 8.0,   50000, 500000, 0.85, ['mm', 'stat_arb', 'hft']),
    'renaissance':    ('Renaissance Tech',     '🦉 Owl',       0.2, 3.0,   10000, 200000, 0.30, ['stat_arb', 'mean_rev']),
    'two_sigma':      ('Two Sigma',            '🐺 Wolf',      0.3, 5.0,   10000, 300000, 0.50, ['ml', 'stat_arb']),
    'jump_trading':   ('Jump Trading',         '🐆 Cheetah',   1.0, 10.0,  100000, 800000, 0.75, ['hft', 'arb']),
    'virtu':          ('Virtu Financial',      '🕷️ Spider',    0.8, 8.0,   20000, 400000, 0.90, ['mm', 'liquidity']),
    'de_shaw':        ('D.E. Shaw',            '🦅 Eagle',     0.1, 2.0,   10000, 200000, 0.40, ['stat_arb', 'macro']),
    'point72':        ('Point72',              '🐻 Bear',      0.15, 1.5,  10000, 150000, 0.35, ['fundamental', 'quant']),
    'millennium':     ('Millennium Mgmt',      '🦎 Chameleon',  0.2, 3.0,   10000, 200000, 0.45, ['multi_strat']),
    'aqr':            ('AQR Capital',          '🐘 Elephant',   0.05, 1.0,  5000,  100000, 0.25, ['factor', 'momentum']),
    'bridgewater':    ('Bridgewater',          '🐋 Blue Whale', 0.01, 0.3,  5000,  50000,  0.10, ['macro', 'risk_parity']),
    'blackrock':      ('BlackRock',            '🦍 Gorilla',    0.05, 1.5,  50000, 1000000, 0.20, ['index', 'etf']),
    'susquehanna':    ('SIG',                  '🦊 Fox',        0.5, 6.0,   20000, 300000, 0.85, ['options_mm', 'arb']),
    'drw':            ('DRW Trading',          '🐉 Dragon',     0.6, 7.0,   30000, 400000, 0.70, ['mm', 'arb', 'crypto']),
    'hudson_river':   ('Hudson River Trading', '🦑 Squid',      1.5, 12.0,  50000, 600000, 0.88, ['hft', 'mm']),
    'tower_research': ('Tower Research',       '🦇 Bat',        2.0, 12.0,  75000, 400000, 0.82, ['hft', 'mm', 'stat_arb']),
    'optiver':        ('Optiver',              '🐙 Octopus',    1.0, 10.0,  30000, 400000, 0.92, ['options_mm', 'arb']),
    'flow_traders':   ('Flow Traders',         '🐟 Fish',       0.5, 6.0,   20000, 200000, 0.88, ['etf_mm', 'crypto']),
    'wintermute':     ('Wintermute',           '🐧 Penguin',    0.5, 8.0,   10000, 300000, 0.85, ['crypto_mm', 'defi']),
    'alameda_ghost':  ('Alameda Ghost',        '👻 Ghost',      0.3, 5.0,   50000, 500000, 0.60, ['arb', 'manipulation']),
    'binance_house':  ('Binance Internal',     '🏠 House',      0.5, 10.0,  100000, 2000000, 0.90, ['mm', 'liquidity']),
    'retail_swarm':   ('Retail Swarm',         '🐜 Ants',       0.01, 0.5,  10,    5000,   0.50, ['momentum', 'fomo']),
    'grid_bot':       ('Grid Bot Army',        '🤖 Robot',      0.1, 3.0,   100,   10000,  0.95, ['grid', 'dca']),
}

# Catalog state file
BOT_CATALOG_FILE = "bot_army_catalog.json"


class BotCatalog:
    """
    THE WAR ROOM REGISTRY — Every player labeled, cataloged, tracked.

    We see:
    - WHO is in the market (firm, animal mascot, type)
    - WHAT they're doing (buying/selling, power level, strategy)
    - WHERE they've been (first seen, sighting history)
    - WHAT they'll do next (based on past behavior patterns)

    Persistent: saves every sighting to bot_army_catalog.json
    Knowledge is power. We have ALL the knowledge.
    """

    def __init__(self):
        self.catalog: Dict[str, dict] = {}  # bot_id -> full record
        self._load_catalog()

    def _load_catalog(self):
        """Load persistent catalog from disk."""
        try:
            if os.path.exists(BOT_CATALOG_FILE):
                with open(BOT_CATALOG_FILE, 'r') as f:
                    self.catalog = json.load(f)
                logger.info(f"BOT CATALOG: Loaded {len(self.catalog)} known players from disk")
        except Exception as e:
            logger.warning(f"BOT CATALOG: Fresh start ({e})")
            self.catalog = {}

    def _save_catalog(self):
        """Save catalog to disk (atomic write)."""
        try:
            tmp = BOT_CATALOG_FILE + ".tmp"
            with open(tmp, 'w') as f:
                json.dump(self.catalog, f, indent=2, default=str)
            os.replace(tmp, BOT_CATALOG_FILE)
        except Exception as e:
            logger.debug(f"Catalog save failed: {e}")

    def _match_firm(self, dominant_freq: float, band_powers: dict,
                    avg_trade_usd: float, shape: str) -> tuple:
        """
        Match spectral fingerprint to a known firm.
        Frequency is the #1 identifier — bots can't change their rhythm.
        Returns: (firm_id, name, animal, confidence)
        """
        best_match = ('unknown', 'Unknown Bot', '❓ Unknown', 0.0)
        best_score = 0

        # In crypto, individual aggTrade sizes are small (fragmented)
        # so we weight frequency more heavily than size
        is_crypto_scale = avg_trade_usd < 5000  # Typical crypto aggTrade

        for firm_id, sig in FIRM_SIGNATURES.items():
            name, animal, freq_lo, freq_hi, size_lo, size_hi, mm_ratio, strategies = sig
            score = 0
            factors = 0

            # Factor 1: Frequency match (MOST IMPORTANT — spectral DNA)
            freq_weight = 50 if is_crypto_scale else 40
            if freq_lo <= dominant_freq <= freq_hi:
                score += freq_weight
            elif dominant_freq < freq_lo:
                dist = (freq_lo - dominant_freq) / max(freq_lo, 0.01)
                score += max(0, freq_weight * 0.7 - dist * 40)
            else:
                dist = (dominant_freq - freq_hi) / max(freq_hi, 0.01)
                score += max(0, freq_weight * 0.7 - dist * 40)
            factors += freq_weight

            # Factor 2: Trade size (less weight for crypto — fragmented orderflow)
            size_weight = 10 if is_crypto_scale else 25
            if size_lo <= avg_trade_usd <= size_hi:
                score += size_weight
            elif avg_trade_usd < size_lo:
                # In crypto small trades are normal — don't penalize too much
                ratio = avg_trade_usd / max(size_lo, 1)
                score += max(0, size_weight * 0.5 * ratio) if is_crypto_scale else max(0, size_weight * 0.8 * ratio)
            else:
                ratio = size_hi / max(avg_trade_usd, 1)
                score += max(0, size_weight * 0.8 * ratio)
            factors += size_weight

            # Factor 3: Band power distribution matches expected strategy
            mm_band_pct = band_powers.get('market_maker', {}).get('power_pct', 0)
            scalper_band_pct = band_powers.get('scalper', {}).get('power_pct', 0)
            acc_band_pct = band_powers.get('accumulator', {}).get('power_pct', 0)

            strat_weight = 25
            if mm_ratio > 0.7:  # Firm is a market maker
                if mm_band_pct > 8 or scalper_band_pct > 50:
                    score += strat_weight
                elif scalper_band_pct > 30:
                    score += strat_weight * 0.7
            elif mm_ratio < 0.3:  # Firm is slow/strategic
                if acc_band_pct > 1 or (mm_band_pct > 5 and scalper_band_pct < 30):
                    score += strat_weight
            else:
                score += strat_weight * 0.5  # Mixed
            factors += strat_weight

            # Factor 4: Shape matches strategy
            shape_weight = 15
            if shape in ('grid', 'oscillator') and 'mm' in strategies:
                score += shape_weight
            elif shape == 'spiral' and ('hft' in strategies or 'arb' in strategies):
                score += shape_weight
            elif shape == 'taper' and ('momentum' in strategies or 'factor' in strategies):
                score += shape_weight * 0.7
            elif shape == 'surge' and ('manipulation' in strategies or 'fomo' in strategies):
                score += shape_weight
            elif shape == 'organic' and ('macro' in strategies or 'fundamental' in strategies):
                score += shape_weight * 0.6
            else:
                score += shape_weight * 0.2  # Small base score
            factors += shape_weight

            # Factor 5: Crypto-specific firm bonus
            if is_crypto_scale:
                crypto_strats = ['crypto_mm', 'crypto', 'defi', 'arb']
                if any(s in strategies for s in crypto_strats):
                    score += 10
                factors += 10

            confidence = score / factors if factors > 0 else 0

            if score > best_score:
                best_score = score
                best_match = (firm_id, name, animal, confidence)

        return best_match

    def _generate_bot_id(self, symbol: str, dominant_freq: float,
                         dominant_band: str, shape: str) -> str:
        """
        Generate a consistent bot ID from spectral signature.
        Same bot = same frequency + band + shape → same ID.
        """
        # Quantize frequency to 0.5Hz buckets for stability
        freq_bucket = round(dominant_freq * 2) / 2
        sig = f"{symbol}:{dominant_band}:{freq_bucket:.1f}:{shape}"
        return hashlib.md5(sig.encode()).hexdigest()[:12]

    def catalog_from_waveform(self, symbol: str, wave_result: dict) -> dict:
        """
        Take a waveform analysis result and catalog every bot we can identify.
        Returns summary of players in this market right now.
        """
        if not wave_result or not wave_result.get('available'):
            return {'players': [], 'total': 0}

        spectrum = wave_result.get('spectrum', {})
        spectrogram = wave_result.get('spectrogram', {})
        flow = wave_result.get('flow', {})
        bands = spectrum.get('bands', {})

        _ = spectrum.get('dominant_freq', 0)
        _ = spectrum.get('dominant_band', 'organic')
        shape = spectrogram.get('shape', 'unknown')
        n_trades = spectrum.get('n_trades', 0)

        # Average trade size (total volume / num trades)
        total_buy = flow.get('total_buy_usd', 0)
        total_sell = flow.get('total_sell_usd', 0)
        avg_trade = (total_buy + total_sell) / max(n_trades, 1)

        now = time.time()
        players = []

        # For each active band, identify a player
        for band_name, band_data in bands.items():
            power_pct = band_data.get('power_pct', 0)
            if power_pct < 2:  # Negligible
                continue

            band_freq = band_data.get('dominant_freq', 0)
            bsr = band_data.get('buy_sell_ratio', 1.0)
            _ = band_data.get('peak_amplitude', 0)

            # Generate bot ID for this band's actor
            bot_id = self._generate_bot_id(symbol, band_freq, band_name, shape)

            # Match to firm
            firm_id, firm_name, animal, confidence = self._match_firm(
                band_freq, bands, avg_trade, shape
            )

            # Determine what this player is doing right now
            if bsr > 1.3:
                action = 'BUYING'
                direction = 'bullish'
            elif bsr < 0.77:
                action = 'SELLING'
                direction = 'bearish'
            else:
                action = 'NEUTRAL'
                direction = 'neutral'

            player = {
                'bot_id': bot_id,
                'firm_id': firm_id,
                'firm_name': firm_name,
                'animal': animal,
                'band': band_name,
                'frequency': round(band_freq, 4),
                'power_pct': round(power_pct, 1),
                'buy_sell_ratio': round(bsr, 2),
                'action': action,
                'direction': direction,
                'confidence': round(confidence, 2),
                'shape': shape,
                'symbol': symbol,
                'timestamp': now,
            }
            players.append(player)

            # === UPDATE PERSISTENT CATALOG ===
            if bot_id in self.catalog:
                record = self.catalog[bot_id]
                record['last_seen'] = now
                record['sighting_count'] = record.get('sighting_count', 0) + 1
                record['last_action'] = action
                record['last_direction'] = direction
                record['last_power_pct'] = power_pct
                record['last_bsr'] = round(bsr, 2)
                record['last_shape'] = shape
                record['last_symbol'] = symbol

                # Track action history (last 50 sightings)
                history = record.get('action_history', [])
                history.append({
                    'ts': round(now),
                    'action': action,
                    'bsr': round(bsr, 2),
                    'power': round(power_pct, 1),
                    'symbol': symbol,
                })
                record['action_history'] = history[-50:]

                # Update confidence if better match found
                if confidence > record.get('confidence', 0):
                    record['firm_id'] = firm_id
                    record['firm_name'] = firm_name
                    record['animal'] = animal
                    record['confidence'] = round(confidence, 2)
            else:
                # NEW PLAYER DETECTED — catalog them
                self.catalog[bot_id] = {
                    'bot_id': bot_id,
                    'firm_id': firm_id,
                    'firm_name': firm_name,
                    'animal': animal,
                    'band': band_name,
                    'first_seen': now,
                    'last_seen': now,
                    'first_symbol': symbol,
                    'last_symbol': symbol,
                    'sighting_count': 1,
                    'confidence': round(confidence, 2),
                    'frequency': round(band_freq, 4),
                    'shape': shape,
                    'last_action': action,
                    'last_direction': direction,
                    'last_power_pct': round(power_pct, 1),
                    'last_bsr': round(bsr, 2),
                    'action_history': [{
                        'ts': round(now),
                        'action': action,
                        'bsr': round(bsr, 2),
                        'power': round(power_pct, 1),
                        'symbol': symbol,
                    }],
                }
                logger.info(
                    f"NEW PLAYER CATALOGED: {animal} {firm_name} | "
                    f"ID={bot_id} band={band_name} freq={band_freq:.3f}Hz | "
                    f"{action} (bsr={bsr:.2f}) power={power_pct:.1f}%"
                )

        # Save every 10 sightings to avoid excessive I/O
        total_sightings = sum(r.get('sighting_count', 0) for r in self.catalog.values())
        if total_sightings % 10 < len(players):
            self._save_catalog()

        return {
            'players': players,
            'total': len(players),
            'catalog_size': len(self.catalog),
        }

    def predict_player(self, bot_id: str) -> dict:
        """
        Predict a player's next move based on their history.
        Knowledge is power — we've watched them before.
        """
        record = self.catalog.get(bot_id)
        if not record:
            return {'prediction': 'unknown', 'confidence': 0}

        history = record.get('action_history', [])
        if len(history) < 3:
            return {
                'prediction': record.get('last_direction', 'neutral'),
                'confidence': 0.2,
                'reason': 'insufficient_history',
            }

        # Analyze recent pattern
        recent = history[-10:]  # Last 10 sightings
        buy_count = sum(1 for h in recent if h['action'] == 'BUYING')
        sell_count = sum(1 for h in recent if h['action'] == 'SELLING')
        _ = sum(1 for h in recent if h['action'] == 'NEUTRAL')

        # Power trend
        powers = [h['power'] for h in recent]
        if len(powers) >= 3:
            power_trend = powers[-1] - powers[0]
        else:
            power_trend = 0

        # BSR trend (are they becoming more bullish or bearish?)
        bsrs = [h['bsr'] for h in recent]
        if len(bsrs) >= 3:
            bsr_trend = bsrs[-1] - bsrs[0]
        else:
            bsr_trend = 0

        # Predict based on momentum of their behavior
        total = len(recent)
        if buy_count > sell_count * 2:
            if bsr_trend > 0:
                prediction = 'will_keep_buying'
                confidence = min(0.9, buy_count / total)
            else:
                prediction = 'buy_exhaustion'
                confidence = 0.5
        elif sell_count > buy_count * 2:
            if bsr_trend < 0:
                prediction = 'will_keep_selling'
                confidence = min(0.9, sell_count / total)
            else:
                prediction = 'sell_exhaustion'
                confidence = 0.5
        elif power_trend > 5:
            prediction = 'ramping_up'
            confidence = 0.6
        elif power_trend < -5:
            prediction = 'withdrawing'
            confidence = 0.6
        else:
            prediction = 'holding_pattern'
            confidence = 0.3

        return {
            'prediction': prediction,
            'confidence': confidence,
            'history_length': len(history),
            'recent_buys': buy_count,
            'recent_sells': sell_count,
            'power_trend': round(power_trend, 1),
            'bsr_trend': round(bsr_trend, 2),
            'firm': record.get('firm_name', 'Unknown'),
            'animal': record.get('animal', '❓'),
        }

    def get_market_players(self, symbol: str) -> list:
        """
        Get all known players in a specific market.
        Shows: who's been here, what they've done, what they'll do.
        """
        now = time.time()
        players = []
        for bot_id, record in self.catalog.items():
            if record.get('last_symbol') == symbol or record.get('first_symbol') == symbol:
                age = now - record.get('first_seen', now)
                last_active = now - record.get('last_seen', now)

                if last_active > 3600:  # Gone for > 1 hour
                    status = 'GONE'
                elif last_active > 300:  # Gone for > 5 min
                    status = 'DORMANT'
                else:
                    status = 'ACTIVE'

                prediction = self.predict_player(bot_id)

                players.append({
                    'bot_id': bot_id,
                    'animal': record.get('animal', '❓'),
                    'firm': record.get('firm_name', 'Unknown'),
                    'status': status,
                    'sightings': record.get('sighting_count', 0),
                    'first_seen_ago': round(age),
                    'last_action': record.get('last_action', '?'),
                    'power': record.get('last_power_pct', 0),
                    'prediction': prediction.get('prediction', '?'),
                    'pred_confidence': prediction.get('confidence', 0),
                })

        # Sort: active first, then by power
        status_order = {'ACTIVE': 0, 'DORMANT': 1, 'GONE': 2}
        players.sort(key=lambda p: (status_order.get(p['status'], 3), -p['power']))
        return players

    def get_battlefield_summary(self, symbol: str, wave_result: dict = None) -> str:
        """
        One-line summary of all players in this market.
        For the monitoring log: who's here and what they're doing.
        """
        if wave_result:
            self.catalog_from_waveform(symbol, wave_result)

        players = self.get_market_players(symbol)
        active = [p for p in players if p['status'] == 'ACTIVE']

        if not active:
            return "no known players"

        parts = []
        for p in active[:4]:  # Show top 4
            animal = p['animal'].split(' ')[0] if p['animal'] else '❓'
            action = p['last_action'][0] if p['last_action'] else '?'
            pred = p['prediction'][:8] if p['prediction'] else '?'
            parts.append(f"{animal}{action}({p['power']:.0f}%→{pred})")

        total = len(self.catalog)
        return f"{' '.join(parts)} [{len(active)} active/{total} cataloged]"


# ==============================================================
#  THE ARMY TRADER
# ==============================================================
class KrakenMarginArmyTrader:
    """
    Army discipline: 1 position. ALL in. GBP1 profit. Out. Next.
    Monitoring: FREE APIs only (Binance public)
    Execution: Kraken API only (open/close)
    """

    def __init__(self, dry_run: bool = False):
        if dry_run:
            os.environ["KRAKEN_DRY_RUN"] = "true"
        from kraken_client import KrakenClient
        self.client = KrakenClient()
        self.dry_run = dry_run or self.client.dry_run
        self.market = FreeMarketData()
        self.intel = BattlefieldIntel()
        # Arm the intel with the waveform analyzer (sees bot moves before they happen)
        if HAS_NUMPY:
            self.intel.waveform = WaveformAnalyzer()
            logger.info("WAVEFORM ANALYZER: Armed and scanning the harmonic pool")
        # The War Room: label, catalog, and track every player
        self.bot_catalog = BotCatalog()
        logger.info(f"BOT CATALOG: {len(self.bot_catalog.catalog)} players in the war room")
        # LIVE STREAM: Binance WebSocket for sub-second reaction
        self.stream = LiveStream() if HAS_WEBSOCKET else None
        self._stream_started = False
        self.margin_pairs: Dict[str, MarginPairInfo] = {}
        # DUAL POSITION: 1 LONG + 1 SHORT simultaneously
        self.active_long: Optional[ActiveTrade] = None
        self.active_short: Optional[ActiveTrade] = None
        # SHADOW TRADES: Prove predictions before deploying capital
        self.shadow_trades: List[ShadowTrade] = []
        self.shadow_validated_count = 0  # How many shadows proved right
        self.shadow_failed_count = 0     # How many shadows proved wrong
        # Legacy alias for code that still references active_trade
        self.active_trade: Optional[ActiveTrade] = None
        self.total_profit = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        self.completed_trades: List[dict] = []
        self.start_time = time.time()
        self._last_danger_check = 0
        self._danger_check_interval = 15  # Check danger every 15s
        self._consecutive_danger = 0       # Track consecutive danger signals
        # ETA predictor for margin time-to-profit estimates
        self.eta_predictor = MarginETAPredictor() if HAS_ETA_PREDICTOR else None
        self._last_eta_report = 0        # Track ETA report frequency
        self._eta_report_interval = 300  # Report ETA every 300s (5 min)
        # Dead Man's Switch trackers - one DTP instance per active margin trade.
        # Keyed by trade.order_id so they survive across monitoring cycles.
        # The DTP receives the pre-calculated net_pnl (USD) directly so all
        # rollover/fee math already done by the existing pipeline feeds straight in.
        self.dtp_trackers: dict = {}
        # Margin Wave Rider - pre-entry 250% margin gate
        self.wave_rider = MarginWaveRider(
            entry_min_margin_pct=MARGIN_WAVE_ENTRY_PCT,
            danger_margin_pct=LIQUIDATION_FORCE,
        ) if HAS_WAVE_RIDER else None
        # Stallion Multiverse - 1-hour ride limit + parallel shadow rides
        self.multiverse: object = StallionMultiverse() if HAS_MULTIVERSE else None
        self._multiverse_ride_registered = False
        # Learning Bridge - pipes multiverse insight to Seer, Lyra, pre-trade
        self.learning_bridge: object = (
            MultiverseLearningBridge(self.multiverse)
            if HAS_LEARNING_BRIDGE and self.multiverse is not None
            else None
        )
        self._load_state()

    # ----------------------------------------------------------
    #  ETA PREDICTION: Estimate time to profitability
    # ----------------------------------------------------------
    def _report_margin_eta(self) -> None:
        """Calculate and log ETA for margin positions (every 5 mins)."""
        if not HAS_ETA_PREDICTOR or not self.eta_predictor:
            return
        
        try:
            now = time.time()
            if now - self._last_eta_report < self._eta_report_interval:
                return  # Not time yet
            
            self._last_eta_report = now
            etas = self.eta_predictor.predict_all()
            
            if not etas:
                return
            
            # Log ETA summary
            logger.info("="*80)
            logger.info("MARGIN ETA ANALYSIS - TIME-TO-PROFITABILITY")
            logger.info("="*80)
            
            for eta in etas:
                logger.info(
                    f"{eta.symbol}: Entry={eta.entry_price:.6f} | Current={eta.current_price:.6f} | "
                    f"Breakeven={eta.breakeven_price:.6f} | Distance={eta.pct_to_breakeven:+.2f}%"
                )
                
                if eta.eta_minutes == 0:
                    logger.info(f"  ✅ PROFITABLE - Position is now profitable!")
                else:
                    logger.info(
                        f"  ⏱️  ETA: {eta.eta_minutes:.0f}m ({eta.eta_minutes/60:.1f}h) | "
                        f"Bullish: {eta.bullish_eta:.0f}m | Bearish: {eta.bearish_eta:.0f}m | "
                        f"Confidence: {eta.confidence*100:.0f}%"
                    )
            
            logger.info("="*80)
        except Exception as e:
            logger.debug(f"ETA report failed: {e}")

    # ----------------------------------------------------------
    #  STARTUP: Discover margin pairs (ONE Kraken API batch)
    # ----------------------------------------------------------
    def discover_margin_universe(self) -> Dict[str, MarginPairInfo]:
        """Fetch ALL margin-eligible pairs from Kraken (once at startup)."""
        logger.info("Scanning Kraken margin universe (one-time)...")
        margin_pairs_raw = self.client.get_margin_pairs()
        pairs_data = self.client._load_asset_pairs()
        usd_margin_pairs = {}

        for mp in margin_pairs_raw:
            pair_name = mp["pair"]
            internal = mp["internal"]
            base = mp["base"]
            quote = mp["quote"]
            if quote not in USD_QUOTES and quote != "USD":
                continue
            pair_info = pairs_data.get(internal, {})
            ordermin = float(pair_info.get("ordermin", 0.0001))
            lot_decimals = int(pair_info.get("lot_decimals", 8))
            price_decimals = int(pair_info.get("pair_decimals", 4))

            base_clean = KRAKEN_BASE_MAP.get(base, base)
            binance_sym = f"{base_clean}USDT"

            info = MarginPairInfo(
                pair=pair_name,
                internal=internal,
                base=base,
                base_clean=base_clean,
                quote="USD",
                leverage_buy=mp["leverage_buy"],
                leverage_sell=mp["leverage_sell"],
                max_leverage=mp["max_leverage"],
                ordermin=ordermin,
                lot_decimals=lot_decimals,
                price_decimals=price_decimals,
                binance_symbol=binance_sym,
            )
            usd_margin_pairs[pair_name] = info

        self.margin_pairs = usd_margin_pairs
        logger.info(f"Found {len(usd_margin_pairs)} USD margin-eligible pairs")
        return usd_margin_pairs

    # ----------------------------------------------------------
    #  FREE PRICE UPDATE (Binance public API)
    # ----------------------------------------------------------
    def update_prices_free(self):
        """Update all pair prices using Binance public API. ONE call."""
        prices = self.market.fetch_all_binance_prices()
        stats = self.market.fetch_binance_24h()
        matched = 0
        for _, info in self.margin_pairs.items():
            bsym = info.binance_symbol
            price = prices.get(bsym, 0)
            if price > 0:
                info.last_price = price
                matched += 1
            s = stats.get(bsym, {})
            if s:
                info.bid = s.get("bid", price)
                info.ask = s.get("ask", price)
                info.momentum = s.get("price_change_pct", 0)
                info.volume_24h = s.get("volume", 0)
                if info.bid > 0 and info.ask > 0:
                    info.spread_pct = (info.ask - info.bid) / info.bid * 100
        logger.info(f"FREE API: {matched}/{len(self.margin_pairs)} pairs priced from Binance")
        return matched

    # ----------------------------------------------------------
    #  TARGET SELECTION - pick THE ONE best trade
    # ----------------------------------------------------------
    def find_best_target(self) -> Optional[Tuple[MarginPairInfo, str, float, float, int]]:
        """
        Score all margin pairs and pick THE ONE best target.
        All margin into this one trade. Maximum leverage.
        Returns: (pair_info, side, volume, trade_value, leverage) or None
        """
        try:
            tb = self.client.get_trade_balance()
            free_margin = tb.get("free_margin", 0)
            equity = tb.get("equity", 0)
        except Exception as e:
            logger.error(f"Could not get trade balance: {e}")
            return None

        if free_margin < 5.0:
            logger.warning(f"Not enough free margin: ${free_margin:.2f}")
            return None

        margin_budget = free_margin * MARGIN_BUFFER
        # Get currently committed margin for wave-rider projections
        margin_used = float(tb.get("margin_amount", tb.get("m", 0)) or 0)
        logger.info(f"ARMY: ${equity:.2f} equity, ${free_margin:.2f} free -> ${margin_budget:.2f} budget")

        # Log wave rider status (informational — per-candidate check below)
        if self.wave_rider and equity > 0:
            logger.info(
                f"[WaveRider] {self.wave_rider.status_line(equity, margin_used, 5)}"
            )

        candidates = []
        for _, info in self.margin_pairs.items():
            if info.last_price <= 0:
                continue
            if info.spread_pct > 0.5:
                continue
            if not info.leverage_buy or not info.leverage_sell:
                continue

            # === DIRECTION: Use ALL intel, not just momentum ===
            # Live stream flow is the #1 signal (sub-second real data)
            stream_side = None
            if self.stream and self.stream.is_alive():
                bsym = info.binance_symbol
                if bsym:
                    sf = self.stream.get_flow_snapshot(bsym)
                    if sf['buy_pct'] > 60 and sf['trade_velocity'] > 10:
                        stream_side = "buy"
                    elif sf['sell_pct'] > 60 and sf['trade_velocity'] > 10:
                        stream_side = "sell"

            # Stream flow overrides kline momentum (it's LIVE vs 24h delayed)
            if stream_side:
                side = stream_side
            elif info.momentum > 0.05:
                side = "buy"
            elif info.momentum < -0.05:
                side = "sell"
            else:
                # Neutral momentum — let stream or orderbook decide
                side = stream_side if stream_side else "buy"

            leverages = info.leverage_buy if side == "buy" else info.leverage_sell

            max_lev = max(leverages)
            notional = margin_budget * max_lev
            if notional < MIN_TRADE_USD:
                continue

            # ── WAVE RIDER: pre-entry 250% margin gate ────────────────
            # Cap notional to the largest size that keeps projected
            # margin level >= 250% after entry.  If even the minimum
            # trade size would breach 250%, skip this pair entirely.
            if self.wave_rider:
                wave_ok, wave_check = self.wave_rider.check(
                    equity=equity,
                    margin_used=margin_used,
                    new_notional=notional,
                    leverage=max_lev,
                )
                if not wave_ok:
                    # Try capping to max safe notional instead of skipping
                    if wave_check.max_safe_notional >= MIN_TRADE_USD:
                        notional = wave_check.max_safe_notional
                        logger.debug(
                            f"[WaveRider] {info.pair}: capped notional to "
                            f"${notional:.2f} (projected {wave_check.projected_margin_pct:.0f}%)"
                        )
                    else:
                        logger.debug(
                            f"[WaveRider] {info.pair}: skipped — {wave_check.reason}"
                        )
                        continue
                else:
                    logger.debug(
                        f"[WaveRider] {info.pair}: {wave_check.reason}"
                    )

            vol = notional / info.last_price
            vol = max(vol, info.ordermin)
            vol = round(vol, info.lot_decimals)
            if vol < info.ordermin:
                vol = info.ordermin
            trade_val = vol * info.last_price

            round_trip_fee = trade_val * (KRAKEN_OPEN_FEE + KRAKEN_CLOSE_FEE)
            required_move_pct = (round_trip_fee + PROFIT_TARGET_USD) / trade_val * 100

            momentum_score = min(abs(info.momentum) / 5, 2.0)  # Normalize to 0-2
            spread_score = max(0, 1.0 - info.spread_pct * 5)
            lev_score = max_lev / 5.0  # 10x = 2.0, 5x = 1.0, 3x = 0.6
            vol_score = min(info.volume_24h / 500_000, 1.0)
            ease_score = max(0, 2.0 - required_move_pct * 2)  # Bigger = easier target

            # For our small account, LEVERAGE is king:
            # 10x lev needs 0.7% move vs 3x needing 1.4% move
            # Weight leverage and ease heavily, momentum as tiebreaker
            # Multiverse learning conviction: ±0.5 based on shadow phase history
            conviction_bonus = (
                self.learning_bridge.get_conviction_bonus(info.pair)
                if self.learning_bridge is not None else 0.0
            )
            total_score = (ease_score * 3 + lev_score * 3 + spread_score * 2
                          + momentum_score + vol_score + conviction_bonus)

            candidates.append((info, side, vol, trade_val, max_lev,
                              total_score, required_move_pct, round_trip_fee))

        if not candidates:
            logger.info("No valid candidates found")
            return None

        # Multiverse scout boost: if the multiverse already knows the next
        # stallion, give that pair a +2 score bonus so it wins the selection.
        _mv_next = (
            self.multiverse.get_next_stallion()
            if self.multiverse is not None else None
        )
        if _mv_next:
            boosted = []
            for item in candidates:
                info_obj, side, vol, tv, lev, score, req, fees = item
                bonus = 2.0 if info_obj.pair == _mv_next else 0.0
                if bonus:
                    logger.info(
                        f"[Multiverse] Boosting {info_obj.pair} score by +{bonus:.1f} "
                        f"(scouted as next stallion)"
                    )
                boosted.append((info_obj, side, vol, tv, lev, score + bonus, req, fees))
            candidates = boosted

        candidates.sort(key=lambda x: x[5], reverse=True)

        logger.info("TOP 5 TARGETS:")
        for i, (info, side, vol, tv, lev, score, req, fees) in enumerate(candidates[:5]):
            logger.info(
                f"  #{i+1} {info.pair} {side.upper()} | "
                f"${tv:.0f} notional ({lev}x) | mom={info.momentum:+.2f}% | "
                f"spread={info.spread_pct:.3f}% | need={req:.3f}% move | "
                f"fees=${fees:.2f} | score={score:.3f}"
            )

        best = candidates[0]
        # Store top candidates for fallback if intel rejects #1
        self._last_candidates = candidates[:5]
        return (best[0], best[1], best[2], best[3], best[4])

    # ----------------------------------------------------------
    #  PRE-STRIKE RESEARCH GATE (War Intelligence Before Entry)
    # ----------------------------------------------------------
    def research_target(self, pair_info: MarginPairInfo, side: str,
                        trade_val: float, leverage: int) -> tuple:
        """
        Run full battlefield research before committing capital.
        If intel says ABORT for our side, FLIP to the other side.
        
        Returns: (approved: bool, final_side: str)
          - approved=True, side=original  -> GO with original direction
          - approved=True, side=flipped   -> Intel said FLIP, go other way
          - approved=False, side=original -> Both directions rejected
        """
        if not pair_info.binance_symbol:
            logger.warning("No Binance symbol for intel - skipping research (CAUTION)")
            return (True, side)

        # ── MULTIVERSE PRE-TRADE CONTEXT ─────────────────────────────────────
        # Before burning API calls on full research, check what the shadow herd
        # already knows about this pair from parallel tracking.
        if self.learning_bridge is not None:
            try:
                mv_ctx = self.learning_bridge.get_pre_trade_context(pair_info.pair)
                rec    = mv_ctx.get('recommendation', 'HOLD')
                conviction = mv_ctx.get('conviction', 0.5)
                phase  = mv_ctx.get('phase', 'UNKNOWN')
                logger.info(
                    f"[LearningBridge] Pre-trade: {pair_info.pair} | "
                    f"phase={phase} | conviction={conviction:.2f} | rec={rec} | "
                    f"seer={mv_ctx.get('seer_aligned')} lyra={mv_ctx.get('lyra_aligned')}"
                )
                if mv_ctx.get('stubborn_bucking'):
                    logger.warning(
                        f"[LearningBridge] {pair_info.pair} has been BUCKING in shadow "
                        f"for 45+ min — treat this as a caution signal"
                    )
            except Exception:
                pass

        # Calculate required move for profit
        round_trip_fee = trade_val * (KRAKEN_OPEN_FEE + KRAKEN_CLOSE_FEE)
        required_move_pct = (round_trip_fee + PROFIT_TARGET_USD) / trade_val * 100

        research = self.intel.pre_strike_research(
            symbol=pair_info.binance_symbol,
            side=side,
            required_move_pct=required_move_pct
        )

        verdict = research.get('verdict', 'ABORT')
        confidence = research.get('confidence', 0)

        if verdict == "GO":
            logger.info(f"INTEL: GO signal for {pair_info.pair} {side.upper()} (confidence={confidence:.2f})")
            return (True, side)
        elif verdict == "CAUTION":
            if confidence >= 0.4:
                logger.info(f"INTEL: CAUTION but proceeding {side.upper()} (confidence={confidence:.2f} >= 0.4)")
                return (True, side)
            # Low-confidence caution — try flipping

        # === ABORT or low-confidence CAUTION: FLIP DIRECTION ===
        # The intel that was used to FEAR is now used to CAPITALIZE
        flip_side = "sell" if side == "buy" else "buy"
        logger.info(
            f"INTEL: {verdict} for {pair_info.pair} {side.upper()} "
            f"— FLIPPING to {flip_side.upper()} (using fear as fuel)"
        )

        # Check if the flipped side has leverage available
        flip_levs = pair_info.leverage_sell if flip_side == "sell" else pair_info.leverage_buy
        if not flip_levs:
            logger.warning(f"  No {flip_side} leverage for {pair_info.pair} — cannot flip")
            return (False, side)

        # Research the flipped side
        flip_research = self.intel.pre_strike_research(
            symbol=pair_info.binance_symbol,
            side=flip_side,
            required_move_pct=required_move_pct
        )

        fv = flip_research.get('verdict', 'ABORT')
        fc = flip_research.get('confidence', 0)

        if fv == "GO":
            logger.info(f"INTEL: FLIP CONFIRMED — {flip_side.upper()} is GO (confidence={fc:.2f})")
            return (True, flip_side)
        elif fv == "CAUTION" and fc >= 0.35:
            logger.info(f"INTEL: FLIP to {flip_side.upper()} CAUTION but proceeding (confidence={fc:.2f})")
            return (True, flip_side)
        else:
            logger.warning(
                f"INTEL: Both {side.upper()} and {flip_side.upper()} rejected for {pair_info.pair}"
            )
            return (False, side)

    # ----------------------------------------------------------
    #  EXECUTION - Kraken API (open/close only)
    # ----------------------------------------------------------
    def open_position(self, pair_info: MarginPairInfo, side: str,
                      volume: float, leverage: int) -> Optional[ActiveTrade]:
        """Open THE ONE margin position - Kraken API call."""
        price = pair_info.last_price
        logger.info(
            f"OPENING {side.upper()} {volume:.6f} {pair_info.base_clean} "
            f"@ ~${price:,.4f} ({leverage}x leverage) on {pair_info.pair}"
        )

        try:
            result = self.client.place_margin_order(
                symbol=pair_info.pair,
                side=side,
                quantity=volume,
                leverage=leverage,
                order_type="market",
            )
            if result.get("error"):
                logger.error(f"Order REJECTED: {pair_info.pair}: {result}")
                return None

            order_id = result.get("orderId", "unknown")

            # Get ACTUAL fill price AND actual fee from Kraken (1-2 extra API calls, CRITICAL)
            actual_price = price  # Default to Binance estimate
            actual_entry_fee = 0.0  # Will be set from Kraken data
            try:
                time.sleep(1)  # Brief wait for order to settle
                kraken_positions = self.client.get_open_margin_positions(do_calcs=True)
                for kp in kraken_positions:
                    kp_pair = kp.get("pair", "")
                    alt = self.client._int_to_alt.get(kp_pair, kp_pair)
                    if alt == pair_info.pair or kp_pair == pair_info.pair:
                        kp_vol = kp.get("volume", kp.get("vol", 0))
                        kp_cost = kp.get("cost", 0)
                        kp_fee = kp.get("fee", 0)
                        if kp_vol > 0 and kp_cost > 0:
                            actual_price = kp_cost / kp_vol
                            logger.info(f"Actual Kraken fill: ${actual_price:,.4f} (Binance est: ${price:,.4f})")
                            price = actual_price
                        if kp_fee > 0:
                            actual_entry_fee = kp_fee
                            actual_rate = kp_fee / kp_cost * 100 if kp_cost > 0 else 0
                            logger.info(f"Actual Kraken fee: ${kp_fee:.4f} ({actual_rate:.3f}% of ${kp_cost:.2f})")
                        break
            except Exception as e:
                logger.debug(f"Could not get actual fill from Kraken: {e}")

            trade_val = volume * price
            # Use ACTUAL fee if we got it, otherwise conservative estimate
            if actual_entry_fee > 0:
                entry_fee = actual_entry_fee
                logger.info(f"Using ACTUAL Kraken entry fee: ${entry_fee:.4f}")
            else:
                entry_fee = trade_val * KRAKEN_OPEN_FEE
                logger.warning(f"Using ESTIMATED entry fee: ${entry_fee:.4f} (could not get actual)")
            # Estimate exit fee conservatively
            exit_fee_est = trade_val * KRAKEN_CLOSE_FEE
            total_fees = entry_fee + exit_fee_est

            if side == "buy":
                breakeven = price + (total_fees + PROFIT_TARGET_USD) / volume
            else:
                breakeven = price - (total_fees + PROFIT_TARGET_USD) / volume

            trade = ActiveTrade(
                pair=pair_info.pair,
                side=side,
                volume=volume,
                entry_price=price,
                leverage=leverage,
                entry_fee=entry_fee,
                entry_time=time.time(),
                order_id=order_id,
                cost=trade_val,
                breakeven_price=breakeven,
                binance_symbol=pair_info.binance_symbol,
            )
            # Place into correct slot: buy→long, sell→short
            if side == "buy":
                self.active_long = trade
            else:
                self.active_short = trade
            self.active_trade = self.active_long or self.active_short
            self._save_state()

            logger.info(
                f"POSITION OPENED: {pair_info.pair} {side.upper()} | "
                f"Entry: ~${price:,.4f} | Target: ${breakeven:,.4f} | "
                f"Fees: ${total_fees:.2f} | Order: {order_id}"
            )
            return trade

        except Exception as e:
            logger.error(f"FAILED to open {pair_info.pair}: {e}")
            return None

    def close_position(self, reason: str = "PROFIT_TARGET", trade: Optional[ActiveTrade] = None) -> Optional[dict]:
        """Close a specific position - Kraken API call."""
        if trade is None:
            trade = self.active_trade
        if not trade:
            return None

        close_side = "sell" if trade.side == "buy" else "buy"
        logger.info(f"CLOSING {trade.pair} ({reason}) - {close_side} {trade.volume:.6f}")

        try:
            # Try with explicit leverage first, then without (Kraken leverage quirk)
            result = self.client.close_margin_position(
                symbol=trade.pair,
                side=close_side,
                volume=trade.volume,
                leverage=trade.leverage,
            )
            if result.get("error"):
                logger.warning(f"Close with leverage failed, retrying without: {result}")
                result = self.client.close_margin_position(
                    symbol=trade.pair,
                    side=close_side,
                    volume=trade.volume,
                )
                if result.get("error"):
                    logger.warning(f"Close without leverage failed, trying bare: {result}")
                    result = self.client.close_margin_position(
                        symbol=trade.pair,
                        side=close_side,
                    )
                    if result.get("error"):
                        logger.error(f"ALL close attempts FAILED: {result}")
                        return None

            close_id = result.get("orderId", "unknown")
            current_price = self.market.get_single_price(trade.binance_symbol)
            if current_price <= 0:
                current_price = trade.entry_price

            if trade.side == "buy":
                gross_pnl = (current_price - trade.entry_price) * trade.volume
            else:
                gross_pnl = (trade.entry_price - current_price) * trade.volume

            # Try to get ACTUAL exit fee and price from Kraken trade history
            actual_exit_fee = 0.0
            try:
                time.sleep(1.5)  # Wait for trade to settle on Kraken
                recent_trades = self.client.get_trades_history(max_records=10)
                # Walk backwards (newest first) to find our closing trade
                for td in reversed(recent_trades):
                    tp = td.get("pair", "")
                    alt = self.client._int_to_alt.get(tp, tp)
                    if alt == trade.pair or tp == trade.pair:
                        actual_exit_fee = td.get("fee", 0)
                        exit_cost = td.get("cost", 0)
                        actual_exit_price = td.get("price", 0)
                        if actual_exit_price > 0:
                            current_price = actual_exit_price
                            logger.info(f"ACTUAL Kraken exit price: ${actual_exit_price:,.6f}")
                        if actual_exit_fee > 0:
                            rate = actual_exit_fee / exit_cost * 100 if exit_cost > 0 else 0
                            logger.info(f"ACTUAL Kraken exit fee: ${actual_exit_fee:.4f} ({rate:.3f}% of ${exit_cost:.2f})")
                        # Recalculate gross P&L with ACTUAL exit price
                        if trade.side == "buy":
                            gross_pnl = (current_price - trade.entry_price) * trade.volume
                        else:
                            gross_pnl = (trade.entry_price - current_price) * trade.volume
                        break
            except Exception as e:
                logger.warning(f"Could not get actual exit data from Kraken: {e}")

            if actual_exit_fee > 0:
                exit_fee = actual_exit_fee
            else:
                exit_fee = current_price * trade.volume * KRAKEN_CLOSE_FEE
                logger.warning(f"Using ESTIMATED exit fee: ${exit_fee:.4f} (could not get actual)")

            # Include rollover fees in net P&L
            rollover = getattr(trade, 'rollover_fees', 0.0)
            net_pnl = gross_pnl - trade.entry_fee - exit_fee - rollover
            total_fees = trade.entry_fee + exit_fee + rollover

            completed = {
                "pair": trade.pair,
                "side": trade.side,
                "volume": trade.volume,
                "entry_price": trade.entry_price,
                "exit_price": current_price,
                "leverage": trade.leverage,
                "entry_fee": trade.entry_fee,
                "exit_fee": exit_fee,
                "rollover_fees": rollover,
                "total_fees": total_fees,
                "gross_pnl": gross_pnl,
                "net_pnl": net_pnl,
                "reason": reason,
                "entry_time": datetime.fromtimestamp(trade.entry_time).isoformat(),
                "exit_time": datetime.now().isoformat(),
                "hold_seconds": time.time() - trade.entry_time,
                "order_id": trade.order_id,
                "close_order_id": close_id,
            }
            self.completed_trades.append(completed)
            self.total_trades += 1
            self.total_profit += net_pnl
            if net_pnl > 0:
                self.winning_trades += 1
            # Clear the correct position slot
            if self.active_long and self.active_long.order_id == trade.order_id:
                self.active_long = None
            if self.active_short and self.active_short.order_id == trade.order_id:
                self.active_short = None
            self.active_trade = self.active_long or self.active_short
            self._save_state()

            logger.info(
                f"TRADE COMPLETED: {trade.pair} {trade.side.upper()} | "
                f"Net P&L: ${net_pnl:+.2f} | Gross: ${gross_pnl:+.2f} | "
                f"Fees: ${total_fees:.4f} (open=${trade.entry_fee:.4f} close=${exit_fee:.4f} roll=${rollover:.4f}) | "
                f"Hold: {time.time() - trade.entry_time:.0f}s | "
                f"Session: ${self.total_profit:+.2f}"
            )
            return completed

        except Exception as e:
            logger.error(f"FAILED to close {trade.pair}: {e}")
            return None

    # ----------------------------------------------------------
    #  MONITOR - FREE API price check + profit gate
    # ----------------------------------------------------------
    def _start_stream_for(self, binance_symbol: str):
        """Start or add a symbol to the live WebSocket stream."""
        if not self.stream:
            return
        if not self._stream_started:
            self.stream.start([binance_symbol])
            self._stream_started = True
            # Give WebSocket a moment to connect
            for _ in range(10):
                if self.stream.connected:
                    break
                time.sleep(0.3)
            if self.stream.connected:
                logger.info(f"LIVE STREAM: ARMED for {binance_symbol} — sub-second kill speed")
            else:
                logger.warning("LIVE STREAM: Connecting... will use REST fallback until ready")
        else:
            self.stream.add_symbol(binance_symbol)

    def monitor_position(self, trade: Optional[ActiveTrade] = None) -> Optional[dict]:
        """
        Check a position using LIVE WebSocket stream (sub-second).
        Falls back to FREE Binance REST if stream unavailable.
        Returns completed trade dict if closed, else None.
        ALL COSTS INCLUDED: entry fee + estimated exit fee + rollover fees.
        """
        if trade is None:
            trade = self.active_trade
        if not trade:
            return None

        # === LIVE STREAM PRICE (sub-100ms) — preferred ===
        current_price = 0.0
        stream_live = False
        if self.stream and self.stream.is_alive():
            current_price = self.stream.get_live_price(trade.binance_symbol)
            if current_price > 0:
                stream_live = True

        # === FLASH CRASH DETECTION (stream-only, sub-second) ===
        if stream_live and self.stream.flash_alert.get(trade.binance_symbol, False):
            flow = self.stream.get_flow_snapshot(trade.binance_symbol)
            logger.warning(
                f"⚡ FLASH ALERT: {trade.binance_symbol} moved >0.3% in <2s! "
                f"flow={flow['flow_direction']} vel={flow['trade_velocity']:.1f}/s "
                f"spread={flow['spread_pct']:.3f}%"
            )

        # === REST FALLBACK ===
        if current_price <= 0:
            current_price = self.market.get_single_price(trade.binance_symbol)
        if current_price <= 0:
            self.market.fetch_all_binance_prices()
            current_price = self.market.get_price(trade.binance_symbol)

        if current_price <= 0:
            logger.warning(f"Cannot get price for {trade.binance_symbol} - using Kraken fallback")
            try:
                ticker = self.client.get_ticker(trade.pair)
                current_price = ticker.get("price", 0)
            except Exception:
                pass

        if current_price <= 0:
            return None

        # === ROLLOVER FEE TRACKING ===
        # Kraken charges ~0.01% per 4 hours on margin positions
        hold_time = time.time() - trade.entry_time
        rollover_periods = int(hold_time / KRAKEN_ROLLOVER_INTERVAL)
        rollover_fees = rollover_periods * trade.cost * KRAKEN_ROLLOVER_RATE
        if rollover_fees != getattr(trade, 'rollover_fees', 0):
            trade.rollover_fees = rollover_fees
            if rollover_fees > 0:
                logger.info(f"Rollover fee update: ${rollover_fees:.4f} ({rollover_periods} x 4h periods)")
            # Recalculate breakeven with rollover
            total_fees_est = trade.entry_fee + (trade.cost * KRAKEN_CLOSE_FEE) + rollover_fees
            if trade.side == "buy":
                trade.breakeven_price = trade.entry_price + (total_fees_est + PROFIT_TARGET_USD) / trade.volume
            else:
                trade.breakeven_price = trade.entry_price - (total_fees_est + PROFIT_TARGET_USD) / trade.volume
            self._save_state()

        if trade.side == "buy":
            gross_pnl = (current_price - trade.entry_price) * trade.volume
        else:
            gross_pnl = (trade.entry_price - current_price) * trade.volume

        exit_value = current_price * trade.volume
        exit_fee = exit_value * KRAKEN_CLOSE_FEE  # Use actual close fee rate
        rollover = getattr(trade, 'rollover_fees', 0.0)
        net_pnl = gross_pnl - trade.entry_fee - exit_fee - rollover
        total_fees = trade.entry_fee + exit_fee + rollover

        if hold_time < 60:
            hold_str = f"{int(hold_time)}s"
        elif hold_time < 3600:
            hold_str = f"{hold_time/60:.1f}m"
        else:
            hold_str = f"{hold_time/3600:.1f}h"

        # Show clear target price
        need_to_target = trade.breakeven_price - current_price if trade.side == "buy" else current_price - trade.breakeven_price
        need_pct = need_to_target / current_price * 100 if current_price > 0 else 0

        # ── DEAD MAN'S SWITCH ─────────────────────────────────────────────────
        # Feed the fully-calculated net P&L (includes entry fee + exit fee est +
        # rollover) straight into the DTP engine.  Keyed by order_id so the
        # floor survives across monitoring cycles.
        dtp_status_str = ""
        if HAS_DTP and DynamicTakeProfit is not None:
            trade_key = getattr(trade, 'order_id', trade.pair)
            if trade_key not in self.dtp_trackers:
                self.dtp_trackers[trade_key] = DynamicTakeProfit(
                    activation_threshold_gbp=DTP_CONFIG['activation_threshold'],
                    gbp_usd_rate=DTP_CONFIG['gbp_usd_rate'],
                    trailing_distance_pct=DTP_CONFIG['trailing_distance_pct'],
                )
                logger.info(
                    f"[DTP] Armed Dead Man's Switch for {trade.pair} "
                    f"(activates at £{DTP_CONFIG['activation_threshold']:.2f} net profit)"
                )
            dtp = self.dtp_trackers[trade_key]
            dtp_triggered, dtp_reason, dtp_state = dtp.update(net_pnl)
            if dtp_state.activated:
                net_gbp = net_pnl / DTP_CONFIG['gbp_usd_rate']
                dtp_status_str = (
                    f" | DTP: floor=£{dtp_state.floor_gbp:.2f} "
                    f"peak=£{dtp_state.peak_profit_gbp:.2f}"
                )
            if dtp_triggered:
                logger.info(f"[DTP] DEAD MAN TRIGGERED: {dtp_reason}")
                return self.close_position(
                    reason=f"DTP_DEAD_MAN (floor=£{dtp_state.floor_gbp:.2f})",
                    trade=trade
                )

        # ── STALLION PHASE ────────────────────────────────────────────────────
        stallion_str = ""
        if HAS_STALLION and classify_phase is not None:
            # Pull live margin level for wave capacity (best-effort)
            _ml = 0.0
            try:
                _tb = self.client.get_trade_balance()
                _ml = float(_tb.get("margin_level", 0) or 0)
            except Exception:
                pass
            _dtp_activated  = dtp_state.activated  if HAS_DTP and 'dtp_state' in dir() else False
            _dtp_triggers   = dtp_state.trigger_count if _dtp_activated else 0
            _dtp_floor_gbp  = dtp_state.floor_gbp    if _dtp_activated else 0.0
            _dtp_peak_gbp   = dtp_state.peak_profit_gbp if _dtp_activated else 0.0

            snap = classify_phase(
                hold_seconds    = hold_time,
                entry_price     = trade.entry_price,
                current_price   = current_price,
                net_pnl         = net_pnl,
                trade_side      = trade.side,
                dtp_activated   = _dtp_activated,
                dtp_trigger_count = _dtp_triggers,
                dtp_floor_gbp   = _dtp_floor_gbp,
                dtp_peak_gbp    = _dtp_peak_gbp,
                margin_level    = _ml,
                leverage        = float(trade.leverage),
            )
            stallion_str = f" | STALLION:{snap.phase.value}"

        # ── LEARNING BRIDGE SYNC — push to Seer, Lyra, ThoughtBus ────────
        if self.learning_bridge is not None:
            try:
                self.learning_bridge.sync()
            except Exception:
                pass

        if net_pnl >= PROFIT_TARGET_USD:
            status = f"TARGET HIT +${net_pnl:.2f} - CLOSING!"
        elif net_pnl > 0:
            status = f"+${net_pnl:.2f} (need ${PROFIT_TARGET_USD - net_pnl:.2f} more -> ${trade.breakeven_price:.4f})"
        elif gross_pnl > 0:
            status = f"Gross+ but fees eating (net ${net_pnl:+.2f}, fees=${total_fees:.2f})"
        else:
            status = f"${net_pnl:+.2f} | target=${trade.breakeven_price:.4f} ({need_pct:+.2f}% away)"

        logger.info(
            f"[{hold_str}] {trade.pair} {trade.side.upper()} {trade.leverage}x | "
            f"${trade.entry_price:,.4f} -> ${current_price:,.4f} | "
            f"Net: ${net_pnl:+.2f} (fees:${total_fees:.2f}) | {status}"
            f"{' [LIVE]' if stream_live else ' [REST]'}"
            f"{dtp_status_str}"
            f"{stallion_str}"
        )

        # === MULTIVERSE: register real ride on first monitor call ===
        if self.multiverse is not None and not self._multiverse_ride_registered:
            self.multiverse.start_real_ride(
                pair       = trade.pair,
                entry_time = trade.entry_time,
            )
            self._multiverse_ride_registered = True

        # === 1-HOUR ROTATION CHECK — time to move to the next stallion ===
        if self.multiverse is not None and self.multiverse.is_rotation_due():
            _next = self.multiverse.get_next_stallion()
            logger.info(
                f"[Multiverse] 1-hour ride limit reached on {trade.pair} "
                f"— rotating to next stallion: {_next or '?'}"
            )
            result = self.close_position(
                reason = f"ROTATION_DUE (1h limit | next→{_next or '?'})",
                trade  = trade,
            )
            # Advance the multiverse clock to the new pair
            if _next and self.multiverse is not None:
                self.multiverse.start_real_ride(_next, time.time())
                self._multiverse_ride_registered = False  # reset for next trade
            return result

        # === THE GBP1 PROFIT GATE - close immediately ===
        if net_pnl >= PROFIT_TARGET_USD:
            return self.close_position(reason=f"PROFIT_TARGET (${net_pnl:+.2f})", trade=trade)

        # === LIVE STREAM INTEL (log-only, NO closing on loss) ===
        if stream_live and self.stream:
            flow = self.stream.get_flow_snapshot(trade.binance_symbol)
            # Log opposing flow as intel — but NEVER close on it
            opposing_flow = (
                (trade.side == "buy" and flow['sell_pct'] > 80) or
                (trade.side == "sell" and flow['buy_pct'] > 80)
            )
            if opposing_flow and flow['trade_velocity'] > 20:
                logger.info(
                    f"  STREAM: opposing flow {flow['flow_direction']} "
                    f"{flow['sell_pct' if trade.side == 'buy' else 'buy_pct']:.0f}% "
                    f"vel={flow['trade_velocity']:.0f}/s — HOLDING (no stop loss)"
                )
            # Spread info (log only)
            if flow['spread_pct'] > FLEE_SPREAD_BLOWOUT:
                logger.info(
                    f"  STREAM: Wide spread {flow['spread_pct']:.3f}% — watching"
                )

        # === WAR INTELLIGENCE: DEEP DANGER CHECK (every 15s) ===
        now = time.time()
        if now - self._last_danger_check >= self._danger_check_interval and trade.binance_symbol:
            self._last_danger_check = now
            try:
                danger = self.intel.check_danger(
                    symbol=trade.binance_symbol,
                    side=trade.side,
                    entry_price=trade.entry_price,
                    target_price=trade.breakeven_price,
                )
                dl = danger.get('danger_level', 0)
                if dl > 0:
                    for r in danger.get('reasons', []):
                        logger.warning(f"  INTEL: {r}")
                else:
                    flow = danger.get('reasons', [])
                    # Show flow info from trade analysis
                    tf = self.intel._trades_cache.get(trade.binance_symbol, {})
                    flow_dir = tf.get('flow_direction', '?')
                    buy_pct = tf.get('buy_volume_pct', 50)
                    bot = tf.get('bot_type', 'none')
                    ob = self.intel._depth_cache.get(trade.binance_symbol, {})
                    imb = ob.get('imbalance', 1.0)
                    # Waveform info
                    wave_tag = ""
                    players_tag = ""
                    if self.intel.waveform and HAS_NUMPY:
                        try:
                            wc = self.intel.waveform._spectral_cache.get(trade.binance_symbol, {})
                            if wc.get('available'):
                                res = wc.get('resonance_score', 0)
                                dom = wc.get('dominant_bot', '?')
                                shp = wc.get('shape', '?')
                                fpred = wc.get('flow_prediction', '?')
                                wave_tag = f" | WAVE: {dom}/{shp} res={res:+.2f} {fpred}"
                                # Catalog the players and get summary
                                try:
                                    players_tag = " | PLAYERS: " + self.bot_catalog.get_battlefield_summary(
                                        trade.binance_symbol, wc
                                    )
                                except Exception:
                                    pass
                        except Exception:
                            pass
                    # Live stream overlay
                    stream_tag = ""
                    if stream_live and self.stream:
                        sf = self.stream.get_flow_snapshot(trade.binance_symbol)
                        stream_tag = (
                            f" | STREAM: vel={sf['trade_velocity']:.0f}/s "
                            f"buy={sf['buy_pct']:.0f}% spread={sf['spread_pct']:.3f}%"
                        )
                    logger.info(
                        f"  INTEL: SAFE | flow={flow_dir} buy={buy_pct:.0f}% | "
                        f"depth_imb={imb:.2f} | bots={bot}{wave_tag}{stream_tag}"
                    )
                    if players_tag:
                        logger.info(f"  {players_tag}")

                # === INTEL IS EYES ONLY — NO CLOSING ON LOSS ===
                # Log danger for awareness but NEVER close at a loss
                if danger.get('flee'):
                    logger.warning(
                        f"  INTEL: Flee signal detected (level={dl}) — "
                        f"HOLDING (net=${net_pnl:+.2f}, no stop loss)"
                    )
                elif dl >= 2:
                    logger.warning(
                        f"  INTEL: Danger level {dl} — HOLDING "
                        f"(net=${net_pnl:+.2f}, no stop loss)"
                    )
                else:
                    pass  # Safe, nothing to report
            except Exception as e:
                logger.debug(f"Danger check error: {e}")

        # === TRUTH CHECK: Reconcile with Kraken every ~2 minutes ===
        if int(hold_time) % 120 < MONITOR_INTERVAL + 1:
            try:
                tb = self.client.get_trade_balance()
                ml = tb.get("margin_level", 0)
                kraken_equity = tb.get("trade_balance", 0) + tb.get("unrealized_pnl", 0)

                # Get Kraken's actual position P&L
                positions = self.client.get_open_margin_positions(do_calcs=True)
                for p in positions:
                    pp = p.get("pair", "")
                    alt = self.client._int_to_alt.get(pp, pp)
                    if alt == trade.pair or pp == trade.pair:
                        kraken_pnl = p.get("net", p.get("unrealized_pnl", 0))
                        kraken_fee = p.get("fee", 0)
                        logger.info(
                            f"TRUTH CHECK: Kraken equity=${kraken_equity:.2f} ml={ml:.1f}% | "
                            f"Position pnl=${kraken_pnl:+.2f} fee=${kraken_fee:.4f} | "
                            f"Our net=${net_pnl:+.2f} fees=${total_fees:.4f}"
                        )
                        # Update entry_fee if Kraken shows different (includes rollover)
                        if kraken_fee > 0 and abs(kraken_fee - trade.entry_fee) > 0.001:
                            logger.info(f"Fee drift: Kraken=${kraken_fee:.4f} vs ours=${trade.entry_fee:.4f}")
                            # Kraken's fee field on position includes rollover fees
                            trade.entry_fee = kraken_fee
                            trade.rollover_fees = 0  # Kraken fee already includes rollovers
                            self._save_state()
                        break

                if 0 < ml < LIQUIDATION_FORCE:
                    return self.close_position(reason=f"LIQUIDATION_RISK (ml={ml:.0f}%)", trade=trade)
                elif 0 < ml < LIQUIDATION_WARN:
                    logger.warning(f"WARNING: Margin level {ml:.1f}%")
            except Exception as e:
                logger.debug(f"Truth check failed: {e}")

        return None

    # ----------------------------------------------------------
    #  STATE PERSISTENCE (atomic writes)
    # ----------------------------------------------------------
    def _save_state(self):
        """Save current state atomically."""
        try:
            # Legacy active_trade = whichever is open (prefer long)
            at = self.active_long or self.active_short
            state = {
                "active_long": self.active_long.to_dict() if self.active_long else None,
                "active_short": self.active_short.to_dict() if self.active_short else None,
                "active_trade": at.to_dict() if at else None,
                "total_profit": self.total_profit,
                "total_trades": self.total_trades,
                "winning_trades": self.winning_trades,
                "shadow_validated": self.shadow_validated_count,
                "shadow_failed": self.shadow_failed_count,
                "completed_trades": self.completed_trades[-50:],
                "last_updated": datetime.now().isoformat(),
            }
            tmp = STATE_FILE + ".tmp"
            with open(tmp, "w") as f:
                json.dump(state, f, indent=2)
            os.replace(tmp, STATE_FILE)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def _load_state(self):
        """Load saved state — supports dual positions."""
        try:
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE) as f:
                    state = json.load(f)

                valid_fields = {f.name for f in ActiveTrade.__dataclass_fields__.values()}

                # Load dual positions (new format)
                for slot, attr in [("active_long", "active_long"), ("active_short", "active_short")]:
                    td = state.get(slot)
                    if td:
                        filtered = {k: v for k, v in td.items() if k in valid_fields}
                        t = ActiveTrade(**filtered)
                        setattr(self, attr, t)
                        logger.info(f"Resumed {slot}: {t.pair} {t.side.upper()}")
                        if t.binance_symbol:
                            self._start_stream_for(t.binance_symbol)

                # Legacy: load old single active_trade into correct slot
                if not self.active_long and not self.active_short:
                    td = state.get("active_trade")
                    if td:
                        filtered = {k: v for k, v in td.items() if k in valid_fields}
                        t = ActiveTrade(**filtered)
                        if t.side == "buy":
                            self.active_long = t
                        else:
                            self.active_short = t
                        logger.info(f"Resumed active trade (legacy): {t.pair} {t.side.upper()}")
                        if t.binance_symbol:
                            self._start_stream_for(t.binance_symbol)

                # Keep active_trade alias pointing at something
                self.active_trade = self.active_long or self.active_short

                self.total_profit = state.get("total_profit", 0)
                self.total_trades = state.get("total_trades", 0)
                self.winning_trades = state.get("winning_trades", 0)
                self.shadow_validated_count = state.get("shadow_validated", 0)
                self.shadow_failed_count = state.get("shadow_failed", 0)
                self.completed_trades = state.get("completed_trades", [])
        except Exception as e:
            logger.warning(f"Could not load state: {e}")

    def _save_results(self):
        """Save completed trades."""
        try:
            results = {
                "session_start": datetime.fromtimestamp(self.start_time).isoformat(),
                "session_end": datetime.now().isoformat(),
                "total_trades": self.total_trades,
                "winning_trades": self.winning_trades,
                "total_profit": self.total_profit,
                "completed_trades": self.completed_trades,
            }
            with open(RESULTS_FILE, "w") as f:
                json.dump(results, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save results: {e}")

    # ----------------------------------------------------------
    #  DISPLAY
    # ----------------------------------------------------------
    def print_universe(self):
        """Print margin pairs ranked by suitability."""
        pairs_with_price = [p for p in self.margin_pairs.values() if p.last_price > 0]
        pairs_with_price.sort(key=lambda x: x.max_leverage * abs(x.momentum), reverse=True)

        print()
        print(f"{'=' * 90}")
        print(f"  MARGIN ARMY - {len(pairs_with_price)} pairs with Binance prices")
        print(f"{'=' * 90}")
        print(f"  {'Pair':<12} {'Binance':<12} {'Price':>12} {'Spread':>8} "
              f"{'MaxLev':>7} {'Mom%':>8} {'24hVol':>14}")
        print(f"  {'-' * 85}")

        for info in pairs_with_price[:30]:
            print(
                f"  {info.pair:<12} {info.binance_symbol:<12} "
                f"${info.last_price:>11,.4f} "
                f"{info.spread_pct:>7.3f}% "
                f"{info.max_leverage:>5}x "
                f"{info.momentum:>+7.2f}% "
                f"${info.volume_24h:>13,.0f}"
            )

        if len(pairs_with_price) > 30:
            print(f"  ... and {len(pairs_with_price) - 30} more")
        no_price = len(self.margin_pairs) - len(pairs_with_price)
        if no_price > 0:
            print(f"  ({no_price} pairs had no Binance match)")
        print(f"{'=' * 90}")
        print()

    # ----------------------------------------------------------
    #  SHADOW VALIDATION — simulate before deploying real capital
    # ----------------------------------------------------------
    SHADOW_MAX_AGE = 120       # Kill shadows older than 2 min
    SHADOW_MIN_VALIDATE = 10   # Must be validated for at least 10s
    SHADOW_MAX_ACTIVE = 4      # Max simultaneous shadows

    def create_shadow(self, pair_info: MarginPairInfo, side: str,
                      vol: float, trade_val: float, lev: int) -> Optional[ShadowTrade]:
        """Create a paper trade to validate a prediction."""
        if len(self.shadow_trades) >= self.SHADOW_MAX_ACTIVE:
            logger.debug("Shadow slots full — skipping")
            return None

        # Don't shadow a pair we already have a real or shadow position on
        existing_pairs = set()
        if self.active_long:
            existing_pairs.add(self.active_long.pair)
        if self.active_short:
            existing_pairs.add(self.active_short.pair)
        for s in self.shadow_trades:
            if s.side == side:
                existing_pairs.add(s.pair)

        if pair_info.pair in existing_pairs:
            return None

        # Get entry price from live stream or REST
        entry_price = 0.0
        if self.stream and self.stream.is_alive() and pair_info.binance_symbol:
            entry_price = self.stream.get_live_price(pair_info.binance_symbol)
        if entry_price <= 0:
            entry_price = self.market.get_single_price(pair_info.binance_symbol)
        if entry_price <= 0:
            entry_price = pair_info.last_price
        if entry_price <= 0:
            return None

        round_trip_fee_pct = (KRAKEN_OPEN_FEE + KRAKEN_CLOSE_FEE) * 100
        target_move_pct = round_trip_fee_pct + (PROFIT_TARGET_USD / trade_val * 100)

        shadow = ShadowTrade(
            pair=pair_info.pair,
            side=side,
            binance_symbol=pair_info.binance_symbol,
            entry_price=entry_price,
            created_at=time.time(),
            target_move_pct=target_move_pct,
            leverage=lev,
            volume=vol,
            trade_val=trade_val,
            pair_info_key=pair_info.pair,
        )

        self.shadow_trades.append(shadow)

        # Start stream for this symbol
        if pair_info.binance_symbol:
            self._start_stream_for(pair_info.binance_symbol)

        logger.info(
            f"SHADOW OPENED: {pair_info.pair} {side.upper()} {lev}x | "
            f"entry=${entry_price:,.4f} | need {target_move_pct:.3f}% move | "
            f"Watching prediction play out..."
        )
        return shadow

    def update_shadows(self):
        """Update all shadow trades with live prices. Expire stale ones."""
        expired = []
        for shadow in self.shadow_trades:
            price = 0.0
            if self.stream and self.stream.is_alive():
                price = self.stream.get_live_price(shadow.binance_symbol)
            if price <= 0:
                price = self.market.get_single_price(shadow.binance_symbol)
            if price > 0:
                shadow.update(price)

            # Expire shadows that are too old without validating
            if shadow.age_seconds > self.SHADOW_MAX_AGE and not shadow.validated:
                expired.append(shadow)
                self.shadow_failed_count += 1
                logger.info(
                    f"SHADOW EXPIRED: {shadow.pair} {shadow.side.upper()} | "
                    f"age={shadow.age_seconds:.0f}s | moved {shadow.current_move_pct:+.3f}% "
                    f"(needed {shadow.target_move_pct:.3f}%) — prediction WRONG"
                )

        for s in expired:
            self.shadow_trades.remove(s)

    def promote_shadow(self, shadow: ShadowTrade) -> Optional[ActiveTrade]:
        """
        Shadow validated — deploy REAL capital on this prediction.
        Returns the real ActiveTrade if successfully opened.
        """
        # Check correct slot is free
        if shadow.side == "buy" and self.active_long:
            logger.debug(f"Long slot occupied — cannot promote {shadow.pair}")
            return None
        if shadow.side == "sell" and self.active_short:
            logger.debug(f"Short slot occupied — cannot promote {shadow.pair}")
            return None

        # Get the pair info
        pair_info = self.margin_pairs.get(shadow.pair_info_key)
        if not pair_info:
            logger.warning(f"Pair info missing for {shadow.pair_info_key}")
            return None

        # Run intel research on the validated shadow
        approved, final_side = self.research_target(
            pair_info, shadow.side, shadow.trade_val, shadow.leverage
        )

        if not approved:
            logger.info(
                f"SHADOW VALIDATED but intel says NO for {shadow.pair} — skipping promotion"
            )
            self.shadow_trades.remove(shadow)
            return None

        # Use the intel's final_side (may have flipped)
        side = final_side
        lev = shadow.leverage
        if side != shadow.side:
            flip_levs = pair_info.leverage_sell if side == "sell" else pair_info.leverage_buy
            lev = max(flip_levs) if flip_levs else lev

        # Recalculate volume based on current margin
        try:
            tb = self.client.get_trade_balance()
            free_margin = tb.get("free_margin", 0)
        except Exception:
            free_margin = 10.0

        # If both slots will be used, use half the margin
        if (side == "buy" and self.active_short) or (side == "sell" and self.active_long):
            margin_budget = free_margin * MARGIN_BUFFER * 0.5
        else:
            margin_budget = free_margin * MARGIN_BUFFER

        notional = margin_budget * lev
        if notional < MIN_TRADE_USD:
            logger.warning(f"Not enough margin to promote shadow (${notional:.2f} notional)")
            self.shadow_trades.remove(shadow)
            return None

        # ── WAVE RIDER: final 250% margin gate before real capital ────
        if self.wave_rider:
            try:
                tb2 = self.client.get_trade_balance()
                eq2 = float(tb2.get("equity", tb2.get("equity_value", 0)) or 0)
                mu2 = float(tb2.get("margin_amount", tb2.get("m", 0)) or 0)
            except Exception:
                eq2, mu2 = 0.0, 0.0

            if eq2 > 0:
                wave_ok, wave_check = self.wave_rider.check(eq2, mu2, notional, lev)
                if not wave_ok:
                    if wave_check.max_safe_notional >= MIN_TRADE_USD:
                        # Cap to safe size rather than abandoning entirely
                        notional = wave_check.max_safe_notional
                        logger.info(
                            f"[WaveRider] Shadow {shadow.pair}: notional capped to "
                            f"${notional:.2f} — projected margin "
                            f"{wave_check.projected_margin_pct:.0f}% >= "
                            f"{self.wave_rider.entry_min:.0f}%"
                        )
                    else:
                        logger.warning(
                            f"[WaveRider] Shadow {shadow.pair}: BLOCKED — "
                            f"{wave_check.reason} — waiting for margin to recover"
                        )
                        # Leave shadow in place; retry next scan cycle
                        return None
                else:
                    logger.info(
                        f"[WaveRider] Shadow {shadow.pair}: APPROVED — "
                        f"{wave_check.reason}"
                    )

        vol = notional / pair_info.last_price if pair_info.last_price > 0 else shadow.volume
        vol = max(vol, pair_info.ordermin)
        vol = round(vol, pair_info.lot_decimals)

        logger.info(
            f"SHADOW VALIDATED -> DEPLOYING REAL: {shadow.pair} {side.upper()} {lev}x | "
            f"Shadow moved {shadow.peak_pnl_pct:+.3f}% in {shadow.age_seconds:.0f}s | "
            f"Prediction CONFIRMED — going LIVE!"
        )

        trade = self.open_position(pair_info, side, vol, lev)
        if trade:
            self.shadow_validated_count += 1
            self._start_stream_for(trade.binance_symbol)
            tag = "FLIPPED" if side != shadow.side else "CONFIRMED"
            logger.info(
                f"ARMY DEPLOYED (shadow-validated): {trade.pair} {side.upper()} | "
                f"Intel {tag} | Shadow peak={shadow.peak_pnl_pct:+.3f}%"
            )

        # Remove the shadow regardless of success
        if shadow in self.shadow_trades:
            self.shadow_trades.remove(shadow)
        return trade

    def print_status(self):
        """Print current status — dual positions + shadows."""
        runtime = time.time() - self.start_time
        hours = int(runtime // 3600)
        mins = int((runtime % 3600) // 60)

        print()
        print(f"{'=' * 65}")
        print(f"  ARMY STATUS | Runtime: {hours}h {mins}m")

        # Dual position display
        for label, trade in [("LONG", self.active_long), ("SHORT", self.active_short)]:
            if trade:
                age = time.time() - trade.entry_time
                if age < 60:
                    age_str = f"{int(age)}s"
                elif age < 3600:
                    age_str = f"{age/60:.1f}m"
                else:
                    age_str = f"{age/3600:.1f}h"
                # Stallion phase for status display
                phase_str = ""
                if HAS_STALLION and classify_phase is not None:
                    try:
                        _snap = classify_phase(
                            hold_seconds=age,
                            entry_price=trade.entry_price,
                            current_price=getattr(trade, 'last_price', trade.entry_price),
                            net_pnl=0.0,
                            trade_side=trade.side,
                        )
                        phase_str = f" | {_snap.phase.value}"
                    except Exception:
                        pass
                print(f"  {label}: {trade.pair} {trade.side.upper()} {trade.leverage}x | "
                      f"${trade.entry_price:,.4f} | age={age_str}{phase_str}")
            else:
                print(f"  {label}: EMPTY (scanning)")

        # Shadow trades
        if self.shadow_trades:
            print(f"  Shadows: {len(self.shadow_trades)} active")
            for s in self.shadow_trades:
                v = "VALIDATED" if s.validated else f"{s.current_move_pct:+.3f}%"
                print(f"    {s.pair} {s.side.upper()} | {v} | age={s.age_seconds:.0f}s")
        else:
            print(f"  Shadows: none (will create on next scan)")

        # Multiverse status + learning bridge status
        if self.multiverse is not None:
            for mv_line in self.multiverse.status_lines():
                print(mv_line)
        if self.learning_bridge is not None:
            for lb_line in self.learning_bridge.learning_status_lines():
                print(lb_line)

        print()
        print(f"  Trades: {self.total_trades} ({self.winning_trades} wins)")
        print(f"  Shadows: {self.shadow_validated_count} validated, {self.shadow_failed_count} failed")
        print(f"  Session profit: ${self.total_profit:+.2f}")
        print(f"  Target: ${PROFIT_TARGET_USD} per trade (approx GBP1)")
        print(f"{'=' * 65}")
        print()

    # ----------------------------------------------------------
    #  1-MINUTE MISSION HUNT: SELECT WINNER → OPEN → CLOSE IN 60s
    # ----------------------------------------------------------
    def mission_hunt(self, side_filter: str = None) -> dict:
        """
        1-MINUTE MISSION HUNT — Full profitable cycle within 60 seconds.

        DISCIPLINE:
          Selection IS the gate. Only open a trade when ALL signals align for
          a completion within 60 seconds. No stop loss needed because we only
          trade confirmed momentum breakouts with volume surge confirmation.

        ENTRY CRITERIA (all must pass):
          ✓ 3+ consecutive 1-minute candles in same direction (streak)
          ✓ Last candle volume >= 1.2× average of previous 5 candles (surge)
          ✓ Momentum score > 0.75% net move on last 3 candles
          ✓ Spread < 0.3%
          ✓ Leverage >= 3×
          ✓ Required breakeven move <= 1-minute ATR (achievable in 1 minute)

        EXECUTION:
          → Open market order (Kraken margin)
          → Monitor every 2 seconds for 60 seconds
          → Close immediately when net_pnl > any positive profit
          → Close at deadline (60s) at best available market price

        ARGS:
          side_filter : 'buy' | 'sell' | None (None = hunt both directions)
        """
        MISSION_WINDOW_SEC   = 60      # Full cycle must complete within 60s
        MONITOR_POLL_SEC     = 2       # Price check interval
        MIN_STREAK           = 3       # Consecutive same-direction candles
        MIN_VOLUME_SURGE     = 1.2     # Last candle vol / avg(prev 5) — 1.2× = meaningful surge
        MIN_MOM_PCT          = 0.75    # >= round-trip fee (0.73%) — only enter genuine surges
        MIN_LAST_CANDLE_PCT  = 0.25    # Last individual candle must move > 0.25% (current impulse)
        MAX_SPREAD_PCT       = 0.30    # Max allowed spread
        MIN_LEVERAGE         = 3       # Minimum leverage to bother
        MISSION_PROFIT_MIN   = 0.75    # Benchmark: minimum $0.75 true net profit before closing
        SCAN_INTERVAL_SEC    = 10      # Seconds between re-scans when hunting
        HUNT_TIMEOUT_SEC     = 300     # Give up after 5 minutes of scanning

        mode_tag = "DRY RUN" if self.dry_run else "LIVE"
        direction_tag = ("SHORT ONLY ↓" if side_filter == "sell"
                         else "LONG ONLY ↑" if side_filter == "buy"
                         else "LONG + SHORT")
        print("=" * 70)
        print(f"  🎯 1-MINUTE MISSION HUNT  |  Mode: {mode_tag}  |  Direction: {direction_tag}")
        print("  Discipline: SELECT WINNER → OPEN → CLOSE IN 60s")
        print("  Signal: streak + volume surge + momentum + spread + leverage")
        print("  Entry gate: ALL criteria must pass – no exceptions")
        print("=" * 70)

        # ── Step 1: Discover universe and live prices ──────────────────────
        # Skip re-discovery if already loaded (pride mode calls hunt repeatedly)
        if not self.margin_pairs:
            self.discover_margin_universe()
        self.update_prices_free()

        # ── Step 2: Check available capital ───────────────────────────────
        try:
            tb    = self.client.get_trade_balance()
            free_margin = tb.get("free_margin", 0.0)
            equity      = tb.get("equity", 0.0)
        except Exception as e:
            logger.error(f"MISSION: Cannot get trade balance: {e}")
            return {'traded': False, 'reason': 'balance_error', 'net_pnl': 0.0,
                    'pair': None, 'side': None}

        margin_budget = free_margin * MARGIN_BUFFER
        print(f"\n💰 Capital: ${equity:.2f} equity  |  ${free_margin:.2f} free"
              f"  |  Budget: ${margin_budget:.2f}")

        if free_margin < 5.0:
            print("❌ MISSION ABORTED: Insufficient free margin (need $5+)")
            return {'traded': False, 'reason': 'insufficient_margin', 'net_pnl': 0.0,
                    'pair': None, 'side': None}

        # ── Step 3: Scan 1-minute Binance klines for momentum signals ─────
        print("\n🔍 Scanning 1-minute momentum signals across margin universe...")
        candidates = []

        valid_pairs = [
            (pair, info) for pair, info in self.margin_pairs.items()
            if (info.binance_symbol
                and info.last_price > 0
                and info.spread_pct <= MAX_SPREAD_PCT
                and (max(info.leverage_buy or [0]) >= MIN_LEVERAGE or
                     max(info.leverage_sell or [0]) >= MIN_LEVERAGE))
        ]

        print(f"   Universe: {len(valid_pairs)} pairs with Binance symbol, spread"
              f" ≤{MAX_SPREAD_PCT}%, leverage ≥{MIN_LEVERAGE}×")

        for pair_name, info in valid_pairs:
            bsym = info.binance_symbol
            try:
                url = (f"{BINANCE_KLINES_URL}?symbol={bsym}"
                       f"&interval=1m&limit=10")
                req = urllib.request.Request(
                    url, headers={"User-Agent": "MissionHunt/1.0"})
                with urllib.request.urlopen(req, timeout=5) as r:
                    klines = json.loads(r.read().decode())
            except Exception:
                continue

            if len(klines) < 6:
                continue

            # kline layout: [open_time, open, high, low, close, volume, ...]
            closes  = [float(k[4]) for k in klines]
            volumes = [float(k[5]) for k in klines]

            # ── Candle direction streak (last MIN_STREAK candles) ──────────
            # Work from the most-recent complete candle backwards (skip last
            # partially-formed candle by analysing klines[-2] as "last closed")
            # Use closes[-6] .. closes[-1] for analysis (6 complete candles)
            c = closes[-7:]   # 7 values → 6 candle bodies
            v = volumes[-7:]

            directions = []
            for i in range(1, len(c)):
                if c[i] > c[i - 1]:
                    directions.append(1)     # bullish
                elif c[i] < c[i - 1]:
                    directions.append(-1)    # bearish
                else:
                    directions.append(0)     # doji

            # Streak: count consecutive matching direction at the end
            streak_dir   = directions[-1]    # direction of most recent candle
            streak_count = 0
            for d in reversed(directions):
                if d == streak_dir:
                    streak_count += 1
                else:
                    break

            if streak_count < MIN_STREAK or streak_dir == 0:
                continue   # Streak gate

            # ── Volume surge: last vs avg of prior 5 ──────────────────────
            last_vol = v[-1]
            avg_vol  = sum(v[-6:-1]) / 5 if len(v) >= 6 else last_vol
            vol_surge = last_vol / avg_vol if avg_vol > 0 else 1.0

            if vol_surge < MIN_VOLUME_SURGE:
                continue   # Volume surge gate

            # ── Climax/Exhaustion filter ───────────────────────────────────
            # A >5× volume spike at streak-end with a reversal wick means the
            # move is EXHAUSTED (sell climax / buy climax), not a breakout.
            # ZEC post-mortem: 10.5× vol candle had a lower wick → reversed 3%.
            if vol_surge > 5.0 and len(klines) >= 2:
                last_k  = klines[-2]   # last fully-closed candle
                k_hi    = float(last_k[2])
                k_lo    = float(last_k[3])
                k_cl    = float(last_k[4])
                k_range = k_hi - k_lo
                if k_range > 0:
                    if streak_dir == -1:   # SELL signal
                        lower_wick = (k_cl - k_lo) / k_range  # bounce off low
                        if lower_wick > 0.20:  # wick ≥ 20% of range → sell climax
                            continue  # Exhaustion — skip
                    else:              # BUY signal
                        upper_wick = (k_hi - k_cl) / k_range  # rejection off high
                        if upper_wick > 0.20:  # wick ≥ 20% of range → buy climax
                            continue  # Exhaustion — skip

            # ── 3-candle momentum ──────────────────────────────────────────
            mom_3c = abs(c[-1] - c[-4]) / c[-4] * 100 if c[-4] > 0 else 0.0
            if mom_3c < MIN_MOM_PCT:
                continue   # Momentum gate

            # ── Current candle impulse check (last closed candle) ─────────
            last_candle_pct = abs(c[-1] - c[-2]) / c[-2] * 100 if c[-2] > 0 else 0.0
            if last_candle_pct < MIN_LAST_CANDLE_PCT:
                continue   # Current impulse gate

            # ── Side from streak direction ─────────────────────────────────
            side = "buy" if streak_dir == 1 else "sell"

            # ── Direction filter (--side long/short) ──────────────────────
            if side_filter and side != side_filter:
                continue

            # ── Leverage available for this side ──────────────────────────
            levs = info.leverage_buy if side == "buy" else info.leverage_sell
            if not levs:
                continue
            max_lev = max(levs)
            if max_lev < MIN_LEVERAGE:
                continue

            # ── Position size ──────────────────────────────────────────────
            notional = margin_budget * max_lev
            if notional < MIN_TRADE_USD:
                continue
            vol_qty  = notional / info.last_price
            vol_qty  = max(vol_qty, info.ordermin)
            vol_qty  = round(vol_qty, info.lot_decimals)
            if vol_qty < info.ordermin:
                continue
            trade_val = vol_qty * info.last_price

            # ── Check achievability: can it move enough in 1 minute? ───────
            # Use 1-min ATR (average of high-low range of last 5 candles)
            atr_1m_pct = (
                sum(abs(float(k[2]) - float(k[3])) / float(k[4]) * 100
                    for k in klines[-6:-1]) / 5
            ) if len(klines) >= 6 else 0.5
            round_trip_fee = trade_val * (KRAKEN_OPEN_FEE + KRAKEN_CLOSE_FEE)
            required_pct   = (round_trip_fee + MISSION_PROFIT_MIN) / trade_val * 100
            # ATR gate: hard reject only if 1m ATR is basically zero (ultra-frozen market)
            # During momentum surges, price can move 5-10× normal ATR in a single minute
            if atr_1m_pct < 0.02:   # Completely frozen — skip
                continue

            # ── Mission score ──────────────────────────────────────────────
            streak_score  = min(streak_count / 5, 1.0)        # 0-1
            surge_score   = min((vol_surge - 1) / 2, 1.0)     # 0-1
            mom_score     = min(mom_3c / 2.0, 1.0)            # 0-1
            lev_score     = min(max_lev / 10.0, 1.0)          # 0-1
            spread_score  = max(0, 1.0 - info.spread_pct / MAX_SPREAD_PCT)
            atr_ease      = max(0, 1.0 - required_pct / atr_1m_pct) if atr_1m_pct else 0
            mission_score = (streak_score * 3 + surge_score * 2.5 + mom_score * 2
                             + atr_ease * 2 + lev_score + spread_score)

            candidates.append({
                "info":         info,
                "side":         side,
                "vol":          vol_qty,
                "trade_val":    trade_val,
                "leverage":     max_lev,
                "streak":       streak_count,
                "vol_surge":    vol_surge,
                "mom_3c_pct":   mom_3c,
                "last_c_pct":   last_candle_pct,
                "atr_1m_pct":   atr_1m_pct,
                "required_pct": required_pct,
                "score":        mission_score,
            })

        if not candidates:
            print(f"\n⏳ No targets qualifying right now. Continuous scanning every {SCAN_INTERVAL_SEC}s...")
            print(f"   Will hunt for up to {HUNT_TIMEOUT_SEC//60} minutes. Ctrl+C to abort.")
            hunt_start = time.time()
            while time.time() - hunt_start < HUNT_TIMEOUT_SEC:
                elapsed_hunt = int(time.time() - hunt_start)
                remaining_hunt = HUNT_TIMEOUT_SEC - elapsed_hunt
                print(f"   [{elapsed_hunt:>3}s] Rescanning... ({remaining_hunt}s remaining)", end="\r")
                time.sleep(SCAN_INTERVAL_SEC)
                # Skip update_prices_free() here — the kline scan below fetches
                # fresh data per-pair already. The bulk price call adds 30s delay.
                candidates = []
                for pair_name2, info2 in valid_pairs:
                    bsym2 = info2.binance_symbol
                    try:
                        url2 = (f"{BINANCE_KLINES_URL}?symbol={bsym2}"
                                f"&interval=1m&limit=10")
                        req2 = urllib.request.Request(url2, headers={"User-Agent": "MissionHunt/1.0"})
                        with urllib.request.urlopen(req2, timeout=5) as r2:
                            klines2 = json.loads(r2.read().decode())
                    except Exception:
                        continue
                    if len(klines2) < 6:
                        continue
                    c2 = [float(k[4]) for k in klines2[-7:]]
                    v2 = [float(k[5]) for k in klines2[-7:]]
                    dirs2 = [1 if c2[i]>c2[i-1] else (-1 if c2[i]<c2[i-1] else 0)
                             for i in range(1, len(c2))]
                    sd2 = dirs2[-1]
                    sc2 = 0
                    for d2 in reversed(dirs2):
                        if d2 == sd2: sc2 += 1
                        else: break
                    if sc2 < MIN_STREAK or sd2 == 0:
                        continue
                    lv2 = v2[-1]; av2 = sum(v2[-6:-1])/5 if len(v2)>=6 else lv2
                    vs2 = lv2/av2 if av2>0 else 1.0
                    if vs2 < MIN_VOLUME_SURGE:
                        continue
                    # Climax exhaustion filter (pass 2)
                    if vs2 > 5.0 and len(klines2) >= 2:
                        lk2  = klines2[-2]
                        lkhi = float(lk2[2]); lklo = float(lk2[3]); lkcl = float(lk2[4])
                        lkrng = lkhi - lklo
                        if lkrng > 0:
                            if sd2 == -1 and (lkcl - lklo) / lkrng > 0.20:
                                continue  # sell climax
                            elif sd2 == 1 and (lkhi - lkcl) / lkrng > 0.20:
                                continue  # buy climax
                    m2 = abs(c2[-1]-c2[-4])/c2[-4]*100 if c2[-4]>0 else 0
                    if m2 < MIN_MOM_PCT:
                        continue
                    m2_last = abs(c2[-1]-c2[-2])/c2[-2]*100 if c2[-2]>0 else 0
                    if m2_last < MIN_LAST_CANDLE_PCT:
                        continue
                    side2 = "buy" if sd2==1 else "sell"
                    if side_filter and side2 != side_filter:
                        continue
                    levs2 = info2.leverage_buy if side2=="buy" else info2.leverage_sell
                    if not levs2 or max(levs2)<MIN_LEVERAGE:
                        continue
                    lev2 = max(levs2)
                    notional2 = margin_budget * lev2
                    if notional2 < MIN_TRADE_USD:
                        continue
                    vq2 = max(round(notional2/info2.last_price, info2.lot_decimals), info2.ordermin)
                    tv2 = vq2 * info2.last_price
                    atr2 = (sum(abs(float(k[2])-float(k[3]))/float(k[4])*100
                                for k in klines2[-6:-1])/5) if len(klines2)>=6 else 0.5
                    if atr2 < 0.02:
                        continue
                    rt2 = tv2*(KRAKEN_OPEN_FEE+KRAKEN_CLOSE_FEE)
                    rp2 = (rt2+MISSION_PROFIT_MIN)/tv2*100
                    ss2 = min(sc2/5,1.0); sg2 = min((vs2-1)/2,1.0)
                    ms2 = min(m2/2,1.0); ls2 = min(lev2/10,1.0)
                    sprd2 = max(0,1.0-info2.spread_pct/MAX_SPREAD_PCT)
                    ae2 = max(0,1.0-rp2/atr2) if atr2>0 else 0
                    sc_total = ss2*3+sg2*2.5+ms2*2+ae2*2+ls2+sprd2
                    candidates.append({
                        "info": info2, "side": side2, "vol": vq2,
                        "trade_val": tv2, "leverage": lev2,
                        "streak": sc2, "vol_surge": vs2, "mom_3c_pct": m2,
                        "last_c_pct": m2_last,
                        "atr_1m_pct": atr2, "required_pct": rp2, "score": sc_total
                    })
                if candidates:
                    print()
                    print(f"\n🚨 SIGNAL LOCKED after {elapsed_hunt}s scanning!")
                    break

        if not candidates:
            print()
            print(f"\n⏸️  No qualifying signal this patrol ({HUNT_TIMEOUT_SEC//60}m window). Resuming hunt...")
            return {'traded': False, 'reason': 'no_signal', 'net_pnl': 0.0,
                    'pair': None, 'side': None}

        # Sort by mission score descending
        candidates.sort(key=lambda x: x["score"], reverse=True)

        print(f"\n🏆 TOP MISSION CANDIDATES (passed all gates):")
        print(f"{'#':<3} {'PAIR':<12} {'SIDE':<5} {'LEV':>4} {'STREAK':>7}"
              f" {'SURGE':>6} {'3cMOM%':>7} {'1cMOM%':>7} {'SCORE':>6}")
        print("-" * 70)
        for i, c_ in enumerate(candidates[:5]):
            print(
                f"{i+1:<3} {c_['info'].pair:<12} {c_['side'].upper():<5}"
                f" {c_['leverage']:>3}×"
                f" {c_['streak']:>6}c"
                f" {c_['vol_surge']:>5.1f}×"
                f" {c_['mom_3c_pct']:>+6.3f}%"
                f" {c_['last_c_pct']:>+6.3f}%"
                f" {c_['score']:>6.2f}"
            )

        best = candidates[0]
        info_b   = best["info"]
        side_b   = best["side"]
        vol_b    = best["vol"]
        lev_b    = best["leverage"]
        tv_b     = best["trade_val"]

        print(f"\n🎯 MISSION TARGET: {info_b.pair} {side_b.upper()} {lev_b}×")
        print(f"   Streak          : {best['streak']} consecutive 1m candles")
        print(f"   Volume surge    : {best['vol_surge']:.1f}× normal")
        print(f"   3-candle mom    : {best['mom_3c_pct']:+.3f}%  (need ≥{0.75:.2f}%)")
        print(f"   Last candle     : {best['last_c_pct']:+.3f}%  (current impulse)")
        print(f"   1m ATR          : {best['atr_1m_pct']:.3f}%  |  Round-trip fee: {best['required_pct']:.3f}%")
        print(f"   Notional        : ${tv_b:.2f}  |  Volume: {vol_b}")

        # ── Step 4: Open the position ──────────────────────────────────────
        print(f"\n⚡ Opening {side_b.upper()} position...")
        trade = self.open_position(info_b, side_b, vol_b, lev_b)
        if not trade:
            print("❌ MISSION FAILED: Order rejected by Kraken. Aborting.")
            return {'traded': False, 'reason': 'order_rejected', 'net_pnl': 0.0,
                    'pair': info_b.pair, 'side': side_b}

        print(f"✅ POSITION OPEN: {trade.pair} {trade.side.upper()}"
              f" @ ${trade.entry_price:,.4f}  |  Breakeven: ${trade.breakeven_price:,.4f}")

        # ── Step 5: Monitor until profit — NEVER close at a loss ────────────
        # SINGLE EXIT RULE: net_pnl > 0 only. Entry gates guarantee recovery.
        # We hold as long as needed. No stop loss. No time deadline.
        mission_start  = time.time()
        poll           = 0
        max_net_pnl    = -9999.0
        closed_result  = None

        print(f"\n⏱️  MONITORING POSITION — HOLD UNTIL PROFIT")
        print(f"   ONLY exit: net_pnl >= ${MISSION_PROFIT_MIN:.2f}  |  No stop loss  |  No time limit")
        print("-" * 55)

        while True:  # Hold until profitable — no deadline
            poll += 1
            elapsed = time.time() - mission_start

            # Get live price
            current = 0.0
            if self.stream and self.stream.is_alive():
                current = self.stream.get_live_price(trade.binance_symbol)
            if current <= 0:
                current = self.market.get_single_price(trade.binance_symbol)
            if current <= 0:
                time.sleep(MONITOR_POLL_SEC)
                continue

            # Calculate net P&L
            if trade.side == "buy":
                gross = (current - trade.entry_price) * trade.volume
            else:
                gross = (trade.entry_price - current) * trade.volume

            exit_fee_est = current * trade.volume * KRAKEN_CLOSE_FEE
            net_pnl = gross - trade.entry_fee - exit_fee_est
            max_net_pnl = max(max_net_pnl, net_pnl)

            status_icon = "📈" if net_pnl > 0 else "⏳"
            print(f"  {status_icon} {elapsed:6.0f}s | ${trade.entry_price:,.4f}→${current:,.4f}"
                  f" | Net: ${net_pnl:+.4f}  peak=${max_net_pnl:+.4f}",
                  end="\r", flush=True)

            # ONLY exit condition: net profit >= $0.75 benchmark floor
            if net_pnl >= MISSION_PROFIT_MIN:
                print()
                print(f"\n💰 PROFIT FLOOR HIT! Net: ${net_pnl:+.4f} (≥ ${MISSION_PROFIT_MIN:.2f} benchmark)  Closing...")
                closed_result = self.close_position(
                    reason=f"MISSION_PROFIT (${net_pnl:+.4f})",
                    trade=trade
                )
                break

            time.sleep(MONITOR_POLL_SEC)

        # ── Mission report ─────────────────────────────────────────────────
        print("\n" + "=" * 70)
        print("  🏁  MISSION COMPLETE")
        if closed_result:
            final_pnl = closed_result.get("net_pnl", 0.0)
            hold_s    = closed_result.get("hold_seconds", 0.0)
            reason    = closed_result.get("reason", "?")
            print(f"  Pair     : {trade.pair}")
            print(f"  Side     : {trade.side.upper()}  {lev_b}× leverage")
            print(f"  Entry    : ${trade.entry_price:,.4f}")
            print(f"  Exit     : ${closed_result.get('exit_price', 0):,.4f}")
            print(f"  Hold     : {hold_s:.1f}s")
            print(f"  Net P&L  : ${final_pnl:+.4f}")
            print(f"  Reason   : {reason}")
            if final_pnl > 0:
                print(f"  Result   : ✅  PROFITABLE MISSION")
            else:
                print(f"  Result   : ⚠️  MISSION CLOSED (market did not cooperate)")
        else:
            print("  Position close failed — check Kraken dashboard manually!")
        print("=" * 70)
        self._save_results()

        final_pnl = closed_result.get("net_pnl", 0.0) if closed_result else 0.0
        return {
            'traded':   True,
            'reason':   closed_result.get('reason', '?') if closed_result else 'close_failed',
            'net_pnl':  final_pnl,
            'pair':     trade.pair,
            'side':     trade.side,
        }

    # ----------------------------------------------------------
    #  PRIDE HUNT — Infinite patrol loop (lion never stops hunting)
    # ----------------------------------------------------------
    def pride_hunt(self, side_filter: str = None) -> None:
        """
        PRIDE MODE — Continuous mission hunt loop.
        The lion does not eat once and sleep. It patrols, strikes, feeds,
        rests briefly, then resumes the patrol. Runs until Ctrl+C.

        After each hunt cycle (trade or no-trade), rest briefly then scan again.
        Tracks all kills (profits) and displays pride stats.
        """
        REST_AFTER_TRADE_SEC   = 30   # Digest after a kill — brief rest
        REST_AFTER_NO_SIGNAL   = 15   # Resume quickly when no signal found
        REST_AFTER_REJECTION   = 20   # Brief pause after rejected order

        direction_tag = ("SHORT ONLY ↓" if side_filter == "sell"
                         else "LONG ONLY ↑" if side_filter == "buy"
                         else "LONG + SHORT")
        mode_tag = "DRY RUN" if self.dry_run else "LIVE"

        print("\n" + "▓" * 70)
        print("  🦁  PRIDE MODE — THE HUNT NEVER ENDS")
        print(f"  Mode: {mode_tag}  |  Direction: {direction_tag}")
        print("  The pride patrols the Serengeti. The meal comes to those who wait.")
        print("  Ctrl+C to end the patrol.")
        print("▓" * 70 + "\n")

        patrol     = 0
        kills      = 0
        total_pnl  = 0.0
        no_signal_streak = 0

        try:
            while True:
                patrol += 1
                print(f"\n{'─'*70}")
                print(f"  🐾  PATROL #{patrol}  |  Kills: {kills}  |  "
                      f"Cumulative P&L: ${total_pnl:+.4f}")
                print(f"{'─'*70}")

                result = self.mission_hunt(side_filter=side_filter)

                if result is None:
                    result = {'traded': False, 'reason': 'unknown', 'net_pnl': 0.0,
                              'pair': None, 'side': None}

                traded  = result.get('traded', False)
                net_pnl = result.get('net_pnl', 0.0)
                reason  = result.get('reason', '?')
                pair    = result.get('pair')

                if traded:
                    total_pnl += net_pnl
                    if net_pnl > 0:
                        kills += 1
                        print(f"\n🥩 KILL #{kills}!  {pair}  P&L: ${net_pnl:+.4f}")
                        print(f"   Total kills: {kills}  |  Total P&L: ${total_pnl:+.4f}")
                    else:
                        print(f"\n⚔️  Traded but market moved against us: ${net_pnl:+.4f}")
                    no_signal_streak = 0
                    rest = REST_AFTER_TRADE_SEC

                elif reason == 'insufficient_margin':
                    print("\n❌ Insufficient margin. Waiting 60s before re-check...")
                    rest = 60

                elif reason == 'order_rejected':
                    rest = REST_AFTER_REJECTION
                    no_signal_streak = 0

                else:  # no_signal
                    no_signal_streak += 1
                    rest = REST_AFTER_NO_SIGNAL

                print(f"\n💤  Resting {rest}s before next patrol...  "
                      f"(Press Ctrl+C to end hunt)")
                time.sleep(rest)

        except KeyboardInterrupt:
            print("\n\n" + "▓" * 70)
            print("  🦁  PRIDE PATROL ENDED  — The pride rests.")
            print(f"  Patrols   : {patrol}")
            print(f"  Kills     : {kills}")
            print(f"  Total P&L : ${total_pnl:+.4f}")
            print("▓" * 70 + "\n")

    # ----------------------------------------------------------
    #  MAIN LOOP - THE ARMY CYCLE (DUAL POSITIONS + SHADOW VALIDATION)
    # ----------------------------------------------------------
    def run(self, scan_only: bool = False):
        """
        Main loop — Shadow Validation + Dual Positions.
        The cycle:
        1. Monitor active positions (LONG and/or SHORT)
        2. Update shadows with live prices — expire stale, note validated
        3. Promote validated shadows to real positions
        4. If slots empty → find candidates → create shadows
        5. Repeat forever. NO STOP LOSS.
        """
        mode = "DRY RUN" if self.dry_run else "LIVE"

        print("=" * 70)
        print(f"  KRAKEN MARGIN ARMY TRADER — SHADOW VALIDATION + DUAL POSITIONS")
        print(f"  Mode: {mode}")
        print(f"  Strategy: 1 LONG + 1 SHORT | SHADOW VALIDATE FIRST | NO STOP LOSS")
        print(f"  Intel: Pre-strike research + Live danger detection")
        print(f"  Stream: {'Binance WebSocket (sub-second)' if HAS_WEBSOCKET else 'REST polling (2s)'}")
        print(f"  Shadow: Simulated plays validate predictions before real capital")
        print(f"  Execution: Kraken API (open/close only)")
        print(f"  Profit target: ${PROFIT_TARGET_USD} per position (approx GBP1)")
        print(f"  Policy: NO STOP LOSS — only close on PROFIT or liquidation risk")
        print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

        # Step 1: Discover pairs (ONE Kraken batch)
        self.discover_margin_universe()

        # Step 2: Prices from FREE API
        self.update_prices_free()

        # Step 3: Show universe
        self.print_universe()

        if scan_only:
            print("Scan-only mode. Exiting.")
            return

        # Step 4: The Army cycle
        cycle = 0
        last_full_refresh = 0
        last_shadow_scan = 0
        SHADOW_SCAN_INTERVAL = 15  # Seconds between shadow creation scans

        try:
            while True:
                cycle += 1
                now = time.time()

                # ============================
                # PHASE 0: ETA REPORTING (every 5 mins)
                # ============================
                self._report_margin_eta()

                # ============================
                # PHASE 1: Monitor active positions
                # ============================
                for label, trade in [("LONG", self.active_long), ("SHORT", self.active_short)]:
                    if trade:
                        result = self.monitor_position(trade=trade)
                        if result:
                            pnl = result.get("net_pnl", 0)
                            logger.info(
                                f"TRADE #{self.total_trades}: {result['pair']} {label} "
                                f"${pnl:+.2f} | Session: ${self.total_profit:+.2f}"
                            )
                            self._save_results()

                # ============================
                # PHASE 2: Update shadows
                # ============================
                if self.shadow_trades:
                    self.update_shadows()

                # ============================
                # PHASE 3: Promote validated shadows
                # ============================
                promoted_this_cycle = False
                for shadow in list(self.shadow_trades):
                    if not shadow.validated:
                        continue
                    # Must have been validated for at least SHADOW_MIN_VALIDATE seconds
                    if shadow.validation_time > 0 and (now - shadow.validation_time) < self.SHADOW_MIN_VALIDATE:
                        continue
                    # Check if the correct slot is free
                    if shadow.side == "buy" and self.active_long:
                        continue
                    if shadow.side == "sell" and self.active_short:
                        continue

                    trade = self.promote_shadow(shadow)
                    if trade:
                        promoted_this_cycle = True
                        break  # Only promote one per cycle

                # ============================
                # PHASE 4: Find candidates → create shadows (if slots empty)
                # ============================
                has_open = self.active_long or self.active_short
                need_long = self.active_long is None
                need_short = self.active_short is None

                if (need_long or need_short) and not promoted_this_cycle:
                    if now - last_full_refresh > 30:
                        self.update_prices_free()
                        last_full_refresh = now

                    if now - last_shadow_scan > SHADOW_SCAN_INTERVAL:
                        last_shadow_scan = now

                        # Get candidates
                        target = self.find_best_target()
                        if target:
                            info, side, vol, trade_val, lev = target

                            # Create shadow for this candidate's side
                            if (side == "buy" and need_long) or (side == "sell" and need_short):
                                self.create_shadow(info, side, vol, trade_val, lev)

                            # Also create shadow for the OPPOSITE side (dual strategy)
                            opp_side = "sell" if side == "buy" else "buy"
                            opp_need = need_short if side == "buy" else need_long
                            if opp_need and hasattr(self, '_last_candidates'):
                                # Find a good candidate for the opposite direction
                                for cand in self._last_candidates:
                                    ci, _, cv, ctv, _ = cand[0], cand[1], cand[2], cand[3], cand[4]
                                    # Try flipping this candidate
                                    flip_levs = ci.leverage_sell if opp_side == "sell" else ci.leverage_buy
                                    if flip_levs and ci.pair != info.pair:
                                        opp_lev = max(flip_levs)
                                        self.create_shadow(ci, opp_side, cv, ctv, opp_lev)
                                        break
                        else:
                            if not has_open and not self.shadow_trades:
                                logger.info("No targets met criteria. Scanning again soon...")

                # ============================
                # Sleep & periodic tasks
                # ============================
                if self.active_long or self.active_short:
                    time.sleep(MONITOR_INTERVAL)
                elif self.shadow_trades:
                    time.sleep(1)  # Fast updates for shadows
                else:
                    time.sleep(5)  # Idle scanning

                if cycle % 30 == 0:
                    self.print_status()
                if cycle % 60 == 0:
                    self._save_results()

        except KeyboardInterrupt:
            print()
            print("Army trader stopped by user.")
            self.print_status()
            self._save_state()
            self._save_results()


def main():
    global PROFIT_TARGET_USD, MIN_PROFIT_USD

    parser = argparse.ArgumentParser(
        description="Kraken Margin Army Trader - ALL IN, GBP1 PROFIT, OUT"
    )
    parser.add_argument("--dry-run", action="store_true", help="Simulation mode")
    parser.add_argument("--scan-only", action="store_true", help="Show pairs and exit")
    parser.add_argument(
        "--target", type=float, default=PROFIT_TARGET_USD,
        help=f"Profit target in USD (default: {PROFIT_TARGET_USD})"
    )
    parser.add_argument(
        "--mission-hunt", action="store_true",
        help="1-minute mission: scan for winner, open, close within 60s"
    )
    parser.add_argument(
        "--pride", action="store_true",
        help="Pride mode: continuous hunt loop — patrol, strike, feed, repeat until Ctrl+C"
    )
    parser.add_argument(
        "--side", choices=["long", "short"], default=None,
        help="Force mission/pride direction: 'long' (buy) or 'short' (sell). Default: hunt both."
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Debug logging")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    PROFIT_TARGET_USD = args.target
    MIN_PROFIT_USD = args.target

    trader = KrakenMarginArmyTrader(dry_run=args.dry_run)

    if args.mission_hunt or args.pride:
        # Map CLI --side (long/short) → internal side filter (buy/sell)
        side_filter = None
        if args.side == "long":
            side_filter = "buy"
        elif args.side == "short":
            side_filter = "sell"

        if args.pride:
            trader.pride_hunt(side_filter=side_filter)
        else:
            trader.mission_hunt(side_filter=side_filter)
    else:
        trader.run(scan_only=args.scan_only)


if __name__ == "__main__":
    main()
