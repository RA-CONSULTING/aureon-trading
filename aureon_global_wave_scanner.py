#!/usr/bin/env python3
"""
🌊🔭 AUREON GLOBAL WAVE SCANNER 🔭🌊
═══════════════════════════════════════════════════════════════════════════

MISSION: Full A-Z, Z-A coverage of the ENTIRE global market
         Wave allocation analysis → Deep dive live candles → EXECUTE

SCANNING STRATEGY:
    📊 PHASE 1: A-Z Sweep (alphabetical full scan)
    📊 PHASE 2: Z-A Sweep (reverse for pattern confirmation)
    📊 PHASE 3: Wave Allocation (distribute attention by wave quality)
    📊 PHASE 4: Deep Dive (live candle analysis on top waves)
    📊 PHASE 5: EXECUTE (Tina B decides, we act)

WAVE SIGNALS:
    🌊 RISING WAVE - Strong upward momentum, jump on the ride
    🏄 WAVE PEAK - Near top, prepare to exit or ride the crash
    🌀 WAVE TROUGH - Bottom forming, early entry opportunity
    📉 FALLING WAVE - Strong downward momentum, avoid or short
    ⚖️ BALANCED WAVE - Consolidation, wait for breakout

CANDLE PATTERNS:
    🕯️ BULLISH ENGULFING - Strong buy signal
    🕯️ BEARISH ENGULFING - Strong sell signal
    🔨 HAMMER/DOJI - Reversal patterns
    📊 VOLUME SPIKE - Confirm trend strength

Gary Leckey | Tina B Full Control | January 2026
═══════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import asyncio
import logging
import time
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Set
from collections import deque, defaultdict
from enum import Enum

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# 🌊 WAVE STATE CLASSIFICATIONS
# ═══════════════════════════════════════════════════════════════════════════

class WaveState(Enum):
    """Current wave state of an asset"""
    RISING = "🌊 RISING"          # Strong upward momentum
    PEAK = "🏄 PEAK"              # Near top, reversal likely
    FALLING = "📉 FALLING"        # Strong downward momentum  
    TROUGH = "🌀 TROUGH"          # Near bottom, reversal likely
    BALANCED = "⚖️ BALANCED"      # Consolidation, no clear direction
    BREAKOUT_UP = "🚀 BREAKOUT↑"  # Breaking out upward
    BREAKOUT_DOWN = "💥 BREAK↓"   # Breaking down


class CandlePattern(Enum):
    """Detected candle patterns"""
    BULLISH_ENGULF = "🕯️ BULL ENGULF"
    BEARISH_ENGULF = "🕯️ BEAR ENGULF"
    HAMMER = "🔨 HAMMER"
    INVERTED_HAMMER = "⚒️ INV HAMMER"
    DOJI = "✚ DOJI"
    MORNING_STAR = "⭐ MORNING STAR"
    EVENING_STAR = "🌙 EVENING STAR"
    VOLUME_SPIKE = "📊 VOLUME SPIKE"
    NO_PATTERN = "• NEUTRAL"


@dataclass
class WaveAnalysis:
    """Complete wave analysis for an asset"""
    symbol: str
    exchange: str
    base: str
    quote: str
    timestamp: float
    
    # Price data
    price: float
    change_1m: float = 0.0      # 1 minute change
    change_5m: float = 0.0      # 5 minute change
    change_15m: float = 0.0     # 15 minute change
    change_1h: float = 0.0      # 1 hour change
    change_24h: float = 0.0     # 24 hour change
    
    # Volume analysis
    volume_24h: float = 0.0
    volume_ratio: float = 1.0   # Current vs average
    volume_spike: bool = False
    
    # Wave classification
    wave_state: WaveState = WaveState.BALANCED
    wave_strength: float = 0.0  # 0-1 how strong the wave is
    wave_age_minutes: int = 0   # How long in this state
    
    # Candle patterns
    candle_pattern: CandlePattern = CandlePattern.NO_PATTERN
    pattern_confidence: float = 0.0
    
    # Technical indicators
    rsi_14: float = 50.0
    macd_signal: str = "NEUTRAL"  # "BUY", "SELL", "NEUTRAL"
    ema_trend: str = "NEUTRAL"    # "BULLISH", "BEARISH", "NEUTRAL"
    
    # Scoring
    jump_score: float = 0.0     # How good to jump on this wave
    exit_score: float = 0.0     # How urgent to exit
    
    # Execution signals
    action: str = "WATCH"       # "BUY", "SELL", "HOLD", "WATCH"
    action_reason: str = ""


@dataclass
class ScanBatch:
    """A batch of scanned assets in alphabetical order"""
    batch_id: int
    direction: str  # "A-Z" or "Z-A"
    start_letter: str
    end_letter: str
    symbols_count: int
    scan_time_ms: float
    waves_found: Dict[WaveState, int] = field(default_factory=dict)
    top_opportunities: List[WaveAnalysis] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════
# 🔭 GLOBAL WAVE SCANNER - A-Z / Z-A FULL COVERAGE
# ═══════════════════════════════════════════════════════════════════════════

class GlobalWaveScanner:
    """
    🌊🔭 GLOBAL WAVE SCANNER
    
    Full A-Z, Z-A coverage of the entire global market.
    Analyzes wave patterns and allocates attention to best opportunities.
    Deep dives into live candles for execution signals.
    """
    
    def __init__(
        self,
        kraken_client=None,
        binance_client=None,
        alpaca_client=None,
        queen=None,
        harmonic_fusion=None,
    ):
        self.kraken = kraken_client
        self.binance = binance_client
        self.alpaca = alpaca_client
        self.queen = queen
        self.harmonic = harmonic_fusion
        
        # Full universe of symbols per exchange
        self.universe: Dict[str, Set[str]] = {
            'kraken': set(),
            'binance': set(),
            'alpaca': set(),
        }
        
        # Alphabetically sorted symbols for A-Z/Z-A sweeps
        self.sorted_symbols_az: List[Tuple[str, str]] = []  # (symbol, exchange)
        self.sorted_symbols_za: List[Tuple[str, str]] = []  # Z-A order
        
        # Wave analysis cache
        self.wave_cache: Dict[str, WaveAnalysis] = {}  # symbol -> analysis
        self.wave_cache_time: Dict[str, float] = {}
        self.cache_ttl = 30.0  # 30 second cache
        
        # Wave allocation buckets
        self.wave_buckets: Dict[WaveState, List[WaveAnalysis]] = {
            state: [] for state in WaveState
        }
        
        # Top opportunities (sorted by jump_score)
        self.top_opportunities: List[WaveAnalysis] = []
        self.deep_dive_queue: deque = deque(maxlen=50)
        
        # Candle cache for deep dives
        self.candle_cache: Dict[str, List[Dict]] = {}
        
        # Scan stats
        self.total_scans = 0
        self.total_symbols_scanned = 0
        self.waves_detected = defaultdict(int)
        self.last_full_scan_time = 0.0
        
        # Scan batches (A-Z sweeps)
        self.batches: List[ScanBatch] = []
        
        logger.info("🌊🔭 Global Wave Scanner initialized")
    
    async def build_universe(self):
        """
        Build the complete universe of all symbols from all exchanges.
        This is the foundation for A-Z/Z-A sweeps.
        """
        logger.info("🌍 Building global symbol universe...")
        
        all_symbols = []
        
        # 🐙 KRAKEN
        if self.kraken:
            try:
                pairs = self.kraken.get_tradeable_pairs()
                for pair in pairs:
                    symbol = pair.get('symbol', pair.get('pair', ''))
                    if symbol:
                        self.universe['kraken'].add(symbol)
                        all_symbols.append((symbol, 'kraken'))
                logger.info(f"   🐙 Kraken: {len(self.universe['kraken'])} symbols")
            except Exception as e:
                logger.error(f"   🐙 Kraken error: {e}")
        
        # 🟡 BINANCE
        if self.binance:
            try:
                info = self.binance.get_exchange_info()
                for sym in info.get('symbols', []):
                    symbol = sym.get('symbol', '')
                    if symbol and sym.get('status') == 'TRADING':
                        self.universe['binance'].add(symbol)
                        all_symbols.append((symbol, 'binance'))
                logger.info(f"   🟡 Binance: {len(self.universe['binance'])} symbols")
            except Exception as e:
                logger.error(f"   🟡 Binance error: {e}")
        
        # 🦙 ALPACA
        if self.alpaca:
            try:
                assets = self.alpaca.list_assets(status='active', asset_class='crypto')
                for asset in assets:
                    base_symbol = getattr(asset, 'symbol', None)
                    if base_symbol is None and isinstance(asset, dict):
                        base_symbol = asset.get('symbol')
                    if not base_symbol:
                        continue
                    symbol = f"{base_symbol}/USD"
                    self.universe['alpaca'].add(symbol)
                    all_symbols.append((symbol, 'alpaca'))
                logger.info(f"   🦙 Alpaca: {len(self.universe['alpaca'])} symbols")
            except Exception as e:
                logger.error(f"   🦙 Alpaca error: {e}")
        
        # Sort A-Z and Z-A
        self.sorted_symbols_az = sorted(all_symbols, key=lambda x: x[0].upper())
        self.sorted_symbols_za = list(reversed(self.sorted_symbols_az))
        
        total = len(all_symbols)
        logger.info(f"🌍 Universe built: {total} total symbols (A-Z sorted)")
        logger.info(f"   📊 First: {self.sorted_symbols_az[0][0] if self.sorted_symbols_az else 'N/A'}")
        logger.info(f"   📊 Last: {self.sorted_symbols_az[-1][0] if self.sorted_symbols_az else 'N/A'}")
        
        return total
    
    async def full_az_sweep(self, ticker_cache: Dict[str, Dict] = None) -> List[ScanBatch]:
        """
        Perform a full A-Z sweep of all symbols.
        Returns batches of scanned symbols with wave classifications.
        """
        start = time.time()
        self.total_scans += 1
        self.batches = []
        
        # Clear wave buckets
        for state in WaveState:
            self.wave_buckets[state] = []
        
        # Process in batches of 100 symbols
        batch_size = 100
        symbols = self.sorted_symbols_az
        
        for i in range(0, len(symbols), batch_size):
            batch_start = time.time()
            batch_symbols = symbols[i:i + batch_size]
            
            batch_waves = {state: 0 for state in WaveState}
            batch_opportunities = []
            
            for symbol, exchange in batch_symbols:
                analysis = await self._analyze_wave(symbol, exchange, ticker_cache)
                if analysis:
                    self.wave_cache[symbol] = analysis
                    self.wave_cache_time[symbol] = time.time()
                    self.wave_buckets[analysis.wave_state].append(analysis)
                    batch_waves[analysis.wave_state] += 1
                    self.waves_detected[analysis.wave_state] += 1
                    
                    # Track high-score opportunities
                    if analysis.jump_score > 0.6:
                        batch_opportunities.append(analysis)
            
            # Create batch record
            start_letter = batch_symbols[0][0][0].upper() if batch_symbols else '?'
            end_letter = batch_symbols[-1][0][0].upper() if batch_symbols else '?'
            
            batch = ScanBatch(
                batch_id=len(self.batches),
                direction="A-Z",
                start_letter=start_letter,
                end_letter=end_letter,
                symbols_count=len(batch_symbols),
                scan_time_ms=(time.time() - batch_start) * 1000,
                waves_found=batch_waves,
                top_opportunities=sorted(batch_opportunities, key=lambda x: -x.jump_score)[:5]
            )
            self.batches.append(batch)
            self.total_symbols_scanned += len(batch_symbols)
        
        self.last_full_scan_time = time.time() - start
        
        # Update top opportunities
        all_opportunities = []
        for state in [WaveState.RISING, WaveState.BREAKOUT_UP, WaveState.TROUGH]:
            all_opportunities.extend(self.wave_buckets[state])
        
        self.top_opportunities = sorted(all_opportunities, key=lambda x: -x.jump_score)[:50]
        
        logger.info(f"🔭 A-Z SWEEP COMPLETE: {len(symbols)} symbols in {self.last_full_scan_time:.2f}s")
        logger.info(f"   🌊 Rising: {len(self.wave_buckets[WaveState.RISING])}")
        logger.info(f"   🚀 Breakout↑: {len(self.wave_buckets[WaveState.BREAKOUT_UP])}")
        logger.info(f"   🌀 Trough: {len(self.wave_buckets[WaveState.TROUGH])}")
        logger.info(f"   📊 Top opps: {len(self.top_opportunities)}")
        
        return self.batches
    
    async def full_za_sweep(self, ticker_cache: Dict[str, Dict] = None) -> List[ScanBatch]:
        """
        Perform a full Z-A sweep (reverse order) for pattern confirmation.
        Validates A-Z findings and catches fast-moving symbols.
        """
        start = time.time()
        
        # Use Z-A sorted list
        symbols = self.sorted_symbols_za
        za_batches = []
        
        batch_size = 100
        for i in range(0, len(symbols), batch_size):
            batch_start = time.time()
            batch_symbols = symbols[i:i + batch_size]
            
            batch_opportunities = []
            
            for symbol, exchange in batch_symbols:
                # Check if cache is still fresh from A-Z sweep
                cache_age = time.time() - self.wave_cache_time.get(symbol, 0)
                
                if cache_age < self.cache_ttl:
                    # Use cached analysis but check for changes
                    cached = self.wave_cache.get(symbol)
                    if cached:
                        # Quick momentum check
                        new_analysis = await self._quick_momentum_check(symbol, exchange, ticker_cache, cached)
                        if new_analysis and new_analysis.jump_score > 0.7:
                            batch_opportunities.append(new_analysis)
                else:
                    # Full re-analysis
                    analysis = await self._analyze_wave(symbol, exchange, ticker_cache)
                    if analysis and analysis.jump_score > 0.7:
                        batch_opportunities.append(analysis)
            
            start_letter = batch_symbols[0][0][0].upper() if batch_symbols else '?'
            end_letter = batch_symbols[-1][0][0].upper() if batch_symbols else '?'
            
            batch = ScanBatch(
                batch_id=len(za_batches),
                direction="Z-A",
                start_letter=start_letter,
                end_letter=end_letter,
                symbols_count=len(batch_symbols),
                scan_time_ms=(time.time() - batch_start) * 1000,
                top_opportunities=sorted(batch_opportunities, key=lambda x: -x.jump_score)[:5]
            )
            za_batches.append(batch)
        
        scan_time = time.time() - start
        logger.info(f"🔭 Z-A SWEEP COMPLETE: {len(symbols)} symbols in {scan_time:.2f}s (confirmation pass)")
        
        return za_batches
    
    async def _analyze_wave(
        self, 
        symbol: str, 
        exchange: str, 
        ticker_cache: Dict[str, Dict] = None
    ) -> Optional[WaveAnalysis]:
        """
        Analyze wave state for a single symbol.
        """
        try:
            # Get ticker data
            ticker = None
            if ticker_cache:
                ticker = ticker_cache.get(symbol)
            
            if not ticker:
                # Try to fetch fresh
                ticker = await self._fetch_ticker(symbol, exchange)
            
            if not ticker:
                return None
            
            # Extract price data
            price = float(ticker.get('price', ticker.get('lastPrice', 0)) or 0)
            change_24h = float(ticker.get('change24h', ticker.get('priceChangePercent', 0)) or 0)
            volume_24h = float(ticker.get('volume', ticker.get('quoteVolume', 0)) or 0)
            
            if price <= 0:
                return None
            
            # Parse base/quote
            base, quote = self._parse_symbol(symbol)
            if not base:
                return None
            
            # Calculate wave state
            wave_state, wave_strength = self._classify_wave(change_24h, volume_24h, ticker)
            
            # Calculate scores
            jump_score = self._calculate_jump_score(wave_state, wave_strength, change_24h, volume_24h)
            exit_score = self._calculate_exit_score(wave_state, wave_strength, change_24h)
            
            # Determine action
            action, reason = self._determine_action(wave_state, jump_score, exit_score)
            
            return WaveAnalysis(
                symbol=symbol,
                exchange=exchange,
                base=base,
                quote=quote,
                timestamp=time.time(),
                price=price,
                change_24h=change_24h,
                volume_24h=volume_24h,
                wave_state=wave_state,
                wave_strength=wave_strength,
                jump_score=jump_score,
                exit_score=exit_score,
                action=action,
                action_reason=reason,
            )
            
        except Exception as e:
            logger.debug(f"Wave analysis error for {symbol}: {e}")
            return None
    
    def _classify_wave(
        self, 
        change_24h: float, 
        volume: float, 
        ticker: Dict
    ) -> Tuple[WaveState, float]:
        """Classify the wave state based on momentum and volume."""
        
        # Extract additional data if available
        high = float(ticker.get('high', ticker.get('highPrice', 0)) or 0)
        low = float(ticker.get('low', ticker.get('lowPrice', 0)) or 0)
        price = float(ticker.get('price', ticker.get('lastPrice', 0)) or 0)
        
        # Calculate position in range
        range_size = high - low if high > low else 1
        range_position = (price - low) / range_size if range_size > 0 else 0.5
        
        # Strong upward momentum
        if change_24h > 10:
            return WaveState.BREAKOUT_UP, min(1.0, change_24h / 20)
        elif change_24h > 3:
            return WaveState.RISING, min(1.0, change_24h / 10)
        
        # Strong downward momentum
        elif change_24h < -10:
            return WaveState.BREAKOUT_DOWN, min(1.0, abs(change_24h) / 20)
        elif change_24h < -3:
            return WaveState.FALLING, min(1.0, abs(change_24h) / 10)
        
        # Peak detection (high in range, momentum slowing)
        elif range_position > 0.85 and change_24h > 0:
            return WaveState.PEAK, range_position
        
        # Trough detection (low in range, momentum may reverse)
        elif range_position < 0.15 and change_24h < 0:
            return WaveState.TROUGH, 1 - range_position
        
        # Default: balanced
        return WaveState.BALANCED, 0.5
    
    def _calculate_jump_score(
        self, 
        wave_state: WaveState, 
        wave_strength: float,
        change_24h: float,
        volume: float
    ) -> float:
        """Calculate how good this opportunity is to jump on."""
        
        base_scores = {
            WaveState.BREAKOUT_UP: 0.9,
            WaveState.RISING: 0.7,
            WaveState.TROUGH: 0.6,  # Early reversal opportunity
            WaveState.BALANCED: 0.3,
            WaveState.PEAK: 0.1,    # Risky to enter
            WaveState.FALLING: 0.1,
            WaveState.BREAKOUT_DOWN: 0.0,
        }
        
        base = base_scores.get(wave_state, 0.3)
        
        # Adjust by wave strength
        score = base * (0.5 + wave_strength * 0.5)
        
        # Volume bonus
        if volume > 1_000_000:  # High volume
            score *= 1.1
        
        # Momentum bonus for rising
        if wave_state in [WaveState.RISING, WaveState.BREAKOUT_UP]:
            score *= (1 + min(change_24h, 10) / 50)
        
        return min(1.0, score)
    
    def _calculate_exit_score(
        self, 
        wave_state: WaveState, 
        wave_strength: float,
        change_24h: float
    ) -> float:
        """Calculate urgency to exit if holding."""
        
        base_scores = {
            WaveState.BREAKOUT_DOWN: 0.95,
            WaveState.FALLING: 0.8,
            WaveState.PEAK: 0.7,
            WaveState.BALANCED: 0.3,
            WaveState.RISING: 0.1,
            WaveState.BREAKOUT_UP: 0.05,
            WaveState.TROUGH: 0.2,
        }
        
        return base_scores.get(wave_state, 0.3) * (0.5 + wave_strength * 0.5)
    
    def _determine_action(
        self, 
        wave_state: WaveState, 
        jump_score: float, 
        exit_score: float
    ) -> Tuple[str, str]:
        """Determine recommended action based on scores."""
        
        if jump_score > 0.7:
            return "BUY", f"Strong wave opportunity ({wave_state.value})"
        elif exit_score > 0.7:
            return "SELL", f"Exit signal ({wave_state.value})"
        elif jump_score > 0.5:
            return "WATCH", f"Developing opportunity ({wave_state.value})"
        else:
            return "HOLD", f"No clear signal ({wave_state.value})"
    
    def _parse_symbol(self, symbol: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse symbol into base and quote."""
        # Common quote currencies
        quotes = ["USDT", "USDC", "USD", "EUR", "GBP", "BTC", "ETH", "BNB", "ZUSD"]
        
        for quote in quotes:
            if symbol.endswith(quote):
                base = symbol[:-len(quote)]
                return base, quote
        
        # Handle slash notation
        if '/' in symbol:
            parts = symbol.split('/')
            if len(parts) == 2:
                return parts[0], parts[1]
        
        return None, None
    
    async def _fetch_ticker(self, symbol: str, exchange: str) -> Optional[Dict]:
        """Fetch ticker data from exchange."""
        try:
            if exchange == 'kraken' and self.kraken:
                return self.kraken.get_ticker(symbol)
            elif exchange == 'binance' and self.binance:
                return self.binance.get_ticker(symbol=symbol)
            elif exchange == 'alpaca' and self.alpaca:
                # Alpaca needs different handling
                pass
        except Exception as e:
            logger.debug(f"Fetch ticker error {symbol}@{exchange}: {e}")
        return None
    
    async def _quick_momentum_check(
        self, 
        symbol: str, 
        exchange: str, 
        ticker_cache: Dict,
        cached: WaveAnalysis
    ) -> Optional[WaveAnalysis]:
        """Quick check if momentum has changed significantly."""
        ticker = ticker_cache.get(symbol) if ticker_cache else None
        if not ticker:
            return cached
        
        new_change = float(ticker.get('change24h', 0) or 0)
        
        # Check for significant change (>1% difference)
        if abs(new_change - cached.change_24h) > 1.0:
            # Re-analyze
            return await self._analyze_wave(symbol, exchange, ticker_cache)
        
        return cached
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🌊 DEEP DIVE - Live Candle Analysis
    # ═══════════════════════════════════════════════════════════════════════
    
    async def deep_dive_candles(self, symbol: str, exchange: str) -> Dict:
        """
        Deep dive into live candles for a specific symbol.
        Analyzes candle patterns, volume, and micro-trends.
        """
        try:
            candles = await self._fetch_candles(symbol, exchange, limit=30)
            if not candles or len(candles) < 10:
                return {"error": "Insufficient candle data"}
            
            # Analyze candle patterns
            patterns = self._detect_candle_patterns(candles)
            
            # Calculate micro-trends
            micro_trend = self._calculate_micro_trend(candles)
            
            # Volume analysis
            volume_profile = self._analyze_volume(candles)
            
            # RSI approximation
            rsi = self._calculate_rsi(candles)
            
            # Generate signal
            signal, confidence = self._generate_signal(patterns, micro_trend, volume_profile, rsi)
            
            return {
                "symbol": symbol,
                "exchange": exchange,
                "candle_count": len(candles),
                "patterns": patterns,
                "micro_trend": micro_trend,
                "volume_profile": volume_profile,
                "rsi": rsi,
                "signal": signal,
                "confidence": confidence,
                "timestamp": time.time(),
            }
            
        except Exception as e:
            logger.error(f"Deep dive error for {symbol}: {e}")
            return {"error": str(e)}
    
    async def _fetch_candles(
        self, 
        symbol: str, 
        exchange: str, 
        interval: str = '1m',
        limit: int = 30
    ) -> List[Dict]:
        """Fetch recent candles from exchange."""
        try:
            if exchange == 'kraken' and self.kraken:
                ohlc = self.kraken.get_ohlc(symbol, interval=1)  # 1 minute
                if ohlc and 'result' in ohlc:
                    for key in ohlc['result']:
                        if key != 'last':
                            data = ohlc['result'][key]
                            return [
                                {
                                    'timestamp': c[0],
                                    'open': float(c[1]),
                                    'high': float(c[2]),
                                    'low': float(c[3]),
                                    'close': float(c[4]),
                                    'volume': float(c[6]),
                                }
                                for c in data[-limit:]
                            ]
            
            elif exchange == 'binance' and self.binance:
                klines = self.binance.get_klines(symbol=symbol, interval='1m', limit=limit)
                if klines:
                    return [
                        {
                            'timestamp': k[0],
                            'open': float(k[1]),
                            'high': float(k[2]),
                            'low': float(k[3]),
                            'close': float(k[4]),
                            'volume': float(k[5]),
                        }
                        for k in klines
                    ]
        except Exception as e:
            logger.debug(f"Fetch candles error: {e}")
        
        return []
    
    def _detect_candle_patterns(self, candles: List[Dict]) -> List[Dict]:
        """Detect candlestick patterns in recent candles."""
        patterns = []
        
        if len(candles) < 3:
            return patterns
        
        for i in range(2, len(candles)):
            c = candles[i]      # Current
            p = candles[i-1]    # Previous
            pp = candles[i-2]   # Two back
            
            body = abs(c['close'] - c['open'])
            wick_upper = c['high'] - max(c['open'], c['close'])
            wick_lower = min(c['open'], c['close']) - c['low']
            
            # Bullish engulfing
            if (p['close'] < p['open'] and  # Previous bearish
                c['close'] > c['open'] and   # Current bullish
                c['close'] > p['open'] and
                c['open'] < p['close']):
                patterns.append({
                    'pattern': CandlePattern.BULLISH_ENGULF,
                    'index': i,
                    'confidence': 0.8
                })
            
            # Bearish engulfing
            elif (p['close'] > p['open'] and  # Previous bullish
                  c['close'] < c['open'] and   # Current bearish
                  c['close'] < p['open'] and
                  c['open'] > p['close']):
                patterns.append({
                    'pattern': CandlePattern.BEARISH_ENGULF,
                    'index': i,
                    'confidence': 0.8
                })
            
            # Hammer (bullish reversal)
            elif (wick_lower > body * 2 and
                  wick_upper < body * 0.3):
                patterns.append({
                    'pattern': CandlePattern.HAMMER,
                    'index': i,
                    'confidence': 0.7
                })
            
            # Doji (indecision)
            elif body < (c['high'] - c['low']) * 0.1:
                patterns.append({
                    'pattern': CandlePattern.DOJI,
                    'index': i,
                    'confidence': 0.5
                })
        
        return patterns
    
    def _calculate_micro_trend(self, candles: List[Dict]) -> Dict:
        """Calculate micro-trend from recent candles."""
        if len(candles) < 5:
            return {"direction": "NEUTRAL", "strength": 0.0}
        
        closes = [c['close'] for c in candles[-10:]]
        
        # Simple linear regression approximation
        n = len(closes)
        x_sum = sum(range(n))
        y_sum = sum(closes)
        xy_sum = sum(i * c for i, c in enumerate(closes))
        x2_sum = sum(i * i for i in range(n))
        
        slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum) if (n * x2_sum - x_sum * x_sum) != 0 else 0
        
        # Normalize slope
        avg_price = y_sum / n if n > 0 else 1
        normalized_slope = (slope / avg_price) * 100  # Percent per candle
        
        if normalized_slope > 0.1:
            direction = "BULLISH"
        elif normalized_slope < -0.1:
            direction = "BEARISH"
        else:
            direction = "NEUTRAL"
        
        return {
            "direction": direction,
            "strength": min(1.0, abs(normalized_slope) / 0.5),
            "slope_pct": normalized_slope,
        }
    
    def _analyze_volume(self, candles: List[Dict]) -> Dict:
        """Analyze volume profile."""
        if not candles:
            return {"profile": "NEUTRAL", "ratio": 1.0}
        
        volumes = [c['volume'] for c in candles]
        avg_volume = sum(volumes) / len(volumes) if volumes else 1
        recent_volume = volumes[-1] if volumes else 0
        
        ratio = recent_volume / avg_volume if avg_volume > 0 else 1.0
        
        if ratio > 2.0:
            profile = "SPIKE"
        elif ratio > 1.3:
            profile = "HIGH"
        elif ratio < 0.5:
            profile = "LOW"
        else:
            profile = "NORMAL"
        
        return {
            "profile": profile,
            "ratio": ratio,
            "avg": avg_volume,
            "current": recent_volume,
        }
    
    def _calculate_rsi(self, candles: List[Dict], period: int = 14) -> float:
        """Calculate RSI from candles."""
        if len(candles) < period + 1:
            return 50.0
        
        changes = []
        for i in range(1, len(candles)):
            changes.append(candles[i]['close'] - candles[i-1]['close'])
        
        gains = [max(0, c) for c in changes[-period:]]
        losses = [abs(min(0, c)) for c in changes[-period:]]
        
        avg_gain = sum(gains) / period if gains else 0
        avg_loss = sum(losses) / period if losses else 0
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _generate_signal(
        self, 
        patterns: List[Dict], 
        micro_trend: Dict, 
        volume_profile: Dict, 
        rsi: float
    ) -> Tuple[str, float]:
        """Generate trading signal from deep dive analysis."""
        
        bullish_score = 0.0
        bearish_score = 0.0
        
        # Pattern signals
        for p in patterns:
            if p['pattern'] in [CandlePattern.BULLISH_ENGULF, CandlePattern.HAMMER]:
                bullish_score += p['confidence'] * 0.3
            elif p['pattern'] in [CandlePattern.BEARISH_ENGULF]:
                bearish_score += p['confidence'] * 0.3
        
        # Trend signals
        if micro_trend['direction'] == 'BULLISH':
            bullish_score += micro_trend['strength'] * 0.25
        elif micro_trend['direction'] == 'BEARISH':
            bearish_score += micro_trend['strength'] * 0.25
        
        # Volume confirmation
        if volume_profile['profile'] == 'SPIKE':
            # Confirms the dominant direction
            if bullish_score > bearish_score:
                bullish_score *= 1.2
            else:
                bearish_score *= 1.2
        
        # RSI signals
        if rsi < 30:
            bullish_score += 0.2  # Oversold
        elif rsi > 70:
            bearish_score += 0.2  # Overbought
        
        # Generate signal
        if bullish_score > 0.5 and bullish_score > bearish_score * 1.3:
            return "🟢 BUY", min(1.0, bullish_score)
        elif bearish_score > 0.5 and bearish_score > bullish_score * 1.3:
            return "🔴 SELL", min(1.0, bearish_score)
        else:
            return "⚪ HOLD", max(bullish_score, bearish_score)
    
    # ═══════════════════════════════════════════════════════════════════════
    # 📊 STATUS AND REPORTING
    # ═══════════════════════════════════════════════════════════════════════
    
    def get_wave_allocation(self) -> Dict[str, Any]:
        """Get current wave allocation summary."""
        return {
            "total_scanned": self.total_symbols_scanned,
            "last_scan_time": self.last_full_scan_time,
            "wave_counts": {
                state.value: len(self.wave_buckets[state])
                for state in WaveState
            },
            "top_opportunities": [
                {
                    "symbol": opp.symbol,
                    "exchange": opp.exchange,
                    "wave": opp.wave_state.value,
                    "jump_score": opp.jump_score,
                    "change_24h": opp.change_24h,
                    "action": opp.action,
                }
                for opp in self.top_opportunities[:10]
            ],
            "universe_size": sum(len(s) for s in self.universe.values()),
        }
    
    def print_wave_report(self):
        """Print formatted wave report."""
        print("\n" + "=" * 70)
        print("🌊🔭 GLOBAL WAVE SCANNER - ALLOCATION REPORT")
        print("=" * 70)
        
        print(f"\n📊 UNIVERSE: {sum(len(s) for s in self.universe.values())} symbols")
        for ex, symbols in self.universe.items():
            print(f"   {ex.upper()}: {len(symbols)}")
        
        print(f"\n🌊 WAVE ALLOCATION:")
        for state in WaveState:
            count = len(self.wave_buckets[state])
            bar = "█" * min(50, count // 5)
            print(f"   {state.value:20} {count:5} {bar}")
        
        print(f"\n🎯 TOP OPPORTUNITIES:")
        for i, opp in enumerate(self.top_opportunities[:10], 1):
            print(f"   {i:2}. {opp.symbol:12} {opp.wave_state.value:15} "
                  f"Jump: {opp.jump_score:.2f} | 24h: {opp.change_24h:+.1f}%")
        
        print("=" * 70 + "\n")


# ═══════════════════════════════════════════════════════════════════════════
# 🐝 BEE SWEEP - Systematic A-Z/Z-A pollination
# ═══════════════════════════════════════════════════════════════════════════

async def run_bee_sweep(scanner: GlobalWaveScanner, ticker_cache: Dict = None):
    """
    🐝 BEE SWEEP: Systematic A-Z then Z-A coverage
    
    Like bees pollinating every flower, we scan EVERY symbol
    in alphabetical order, then reverse for confirmation.
    """
    print("\n🐝 STARTING BEE SWEEP - Full A-Z/Z-A Coverage...")
    
    # Build universe if not done
    if not scanner.sorted_symbols_az:
        await scanner.build_universe()
    
    # A-Z Sweep
    print("\n📊 PHASE 1: A-Z Sweep...")
    az_batches = await scanner.full_az_sweep(ticker_cache)
    
    # Z-A Sweep (confirmation)
    print("\n📊 PHASE 2: Z-A Sweep (confirmation)...")
    za_batches = await scanner.full_za_sweep(ticker_cache)
    
    # Print report
    scanner.print_wave_report()
    
    # Deep dive top opportunities
    print("\n🔬 PHASE 3: Deep Dive Top Waves...")
    for opp in scanner.top_opportunities[:5]:
        dive = await scanner.deep_dive_candles(opp.symbol, opp.exchange)
        print(f"   {opp.symbol}: {dive.get('signal', 'N/A')} "
              f"(Conf: {dive.get('confidence', 0):.1%})")
    
    return {
        "az_batches": len(az_batches),
        "za_batches": len(za_batches),
        "top_opportunities": len(scanner.top_opportunities),
        "wave_allocation": scanner.get_wave_allocation(),
    }


# ═══════════════════════════════════════════════════════════════════════════
# 🧪 TEST / STANDALONE
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import asyncio
    
    print("🌊🔭 AUREON GLOBAL WAVE SCANNER")
    print("=" * 50)
    
    # Create scanner (without exchange connections for test)
    scanner = GlobalWaveScanner()
    
    # Simulate some data
    scanner.universe = {
        'binance': {'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'DOGEUSDT'},
        'kraken': {'XBTUSD', 'ETHUSD'},
    }
    
    scanner.sorted_symbols_az = sorted([
        (s, ex) for ex, symbols in scanner.universe.items() for s in symbols
    ])
    scanner.sorted_symbols_za = list(reversed(scanner.sorted_symbols_az))
    
    print(f"Universe: {scanner.universe}")
    print(f"A-Z: {[s[0] for s in scanner.sorted_symbols_az]}")
    print(f"Z-A: {[s[0] for s in scanner.sorted_symbols_za]}")
    
    print("\n✅ Global Wave Scanner ready for integration!")
