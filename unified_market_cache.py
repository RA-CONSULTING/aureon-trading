#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                      ║
║     🌐 UNIFIED MARKET CACHE - PRODUCTION-READY RATE LIMIT SOLUTION 🌐               ║
║     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                    ║
║                                                                                      ║
║     PROBLEM: Multiple processes hammering exchange APIs = rate limit death          ║
║                                                                                      ║
║     SOLUTION: Single WebSocket feeder → Shared JSON cache → All readers             ║
║                                                                                      ║
║     DATA SOURCES (priority order):                                                  ║
║       1. 🔶 Binance WebSocket (FREE, real-time, ~100ms latency)                     ║
║       2. 🐙 Kraken REST Cache (15s refresh, fallback)                               ║
║       3. 🦙 Alpaca REST (only for balance/orders - authenticated)                   ║
║                                                                                      ║
║     OUTPUT: ws_cache/unified_prices.json - ALL processes read from here             ║
║                                                                                      ║
║     Gary Leckey | January 2026 | PRODUCTION READY                                   ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
import json
import time
import threading
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime

# Windows UTF-8 Fix
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Cache file paths
CACHE_DIR = os.getenv('MARKET_CACHE_DIR', 'ws_cache')
UNIFIED_CACHE_PATH = os.path.join(CACHE_DIR, 'unified_prices.json')
BINANCE_CACHE_PATH = os.path.join(CACHE_DIR, 'binance_ws_prices.json')
KRAKEN_CACHE_PATH = os.path.join(CACHE_DIR, 'kraken_prices.json')

# Cache TTL (how old data can be before considered stale)
CACHE_TTL_SECONDS = float(os.getenv('MARKET_CACHE_TTL', '30'))  # 30s default
WS_CACHE_TTL_SECONDS = float(os.getenv('WS_CACHE_TTL', '5'))  # 5s for WebSocket data

# Symbols to track (top crypto by volume)
DEFAULT_SYMBOLS = [
    'BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'ADA', 'AVAX', 'LINK', 'DOT', 'MATIC',
    'SHIB', 'PEPE', 'LTC', 'BCH', 'UNI', 'AAVE', 'ATOM', 'XLM', 'ALGO', 'VET',
    'FTM', 'NEAR', 'APT', 'INJ', 'TIA', 'SEI', 'SUI', 'OP', 'ARB', 'RENDER',
    'TRUMP', 'BAT', 'SKY', 'MANA', 'SAND', 'AXS', 'ENJ', 'GALA', 'IMX', 'BLUR'
]


@dataclass
class CachedTicker:
    """Unified ticker data structure"""
    symbol: str           # Normalized: BTC, ETH, etc.
    price: float
    bid: float
    ask: float
    change_24h: float     # Percent change
    volume_24h: float     # Quote volume (USD)
    source: str           # 'binance_ws', 'kraken_rest', 'alpaca_rest'
    timestamp: float      # Unix timestamp
    pair: str             # Original pair: BTCUSDT, XXBTZUSD, BTC/USD
    
    def is_fresh(self, max_age: float = CACHE_TTL_SECONDS) -> bool:
        """Check if data is fresh enough to use"""
        return (time.time() - self.timestamp) <= max_age


class UnifiedMarketCache:
    """
    Singleton cache that ALL processes should use for market data.
    
    Usage:
        from unified_market_cache import get_market_cache, get_price, get_ticker
        
        # Get singleton
        cache = get_market_cache()
        
        # Get price (reads from cache file, no API calls!)
        price = get_price('BTC')  # Returns float or None
        
        # Get full ticker
        ticker = get_ticker('BTC')  # Returns CachedTicker or None
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        # In-memory cache
        self._tickers: Dict[str, CachedTicker] = {}
        self._cache_lock = threading.Lock()
        self._last_file_read = 0.0
        self._file_read_interval = 1.0  # Read file max once per second
        
        # Ensure cache directory exists
        os.makedirs(CACHE_DIR, exist_ok=True)
        
        logger.info(f"🌐 UnifiedMarketCache initialized (cache dir: {CACHE_DIR})")
    
    def _read_cache_files(self) -> None:
        """Read all cache files and merge into memory"""
        now = time.time()
        if now - self._last_file_read < self._file_read_interval:
            return  # Don't read too often
        
        self._last_file_read = now
        
        # Priority order: Binance WS > Unified > Kraken REST
        cache_files = [
            (BINANCE_CACHE_PATH, 'binance_ws', WS_CACHE_TTL_SECONDS),
            (UNIFIED_CACHE_PATH, 'unified', CACHE_TTL_SECONDS),
            (KRAKEN_CACHE_PATH, 'kraken_rest', CACHE_TTL_SECONDS),
        ]
        
        for path, source, ttl in cache_files:
            try:
                if not os.path.exists(path):
                    continue
                    
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                file_ts = data.get('generated_at', 0)
                if now - file_ts > ttl * 2:  # File too old
                    continue
                
                ticker_cache = data.get('ticker_cache', {})
                for key, t in ticker_cache.items():
                    if not isinstance(t, dict):
                        continue
                    
                    # Normalize symbol
                    symbol = t.get('base', '').upper()
                    if not symbol:
                        # Try to extract from key
                        symbol = self._extract_symbol(key)
                    if not symbol:
                        continue
                    
                    # Skip if we already have fresher data
                    existing = self._tickers.get(symbol)
                    ticker_ts = t.get('timestamp', file_ts)
                    if existing and existing.timestamp > ticker_ts:
                        continue
                    
                    # Create ticker
                    try:
                        ticker = CachedTicker(
                            symbol=symbol,
                            price=float(t.get('price', 0) or 0),
                            bid=float(t.get('bid', t.get('price', 0)) or 0),
                            ask=float(t.get('ask', t.get('price', 0)) or 0),
                            change_24h=float(t.get('change24h', t.get('change_24h', 0)) or 0),
                            volume_24h=float(t.get('volume', t.get('volume_24h', 0)) or 0),
                            source=t.get('source', source),
                            timestamp=ticker_ts,
                            pair=t.get('pair', key)
                        )
                        if ticker.price > 0:
                            with self._cache_lock:
                                self._tickers[symbol] = ticker
                    except (ValueError, TypeError):
                        continue
                        
            except Exception as e:
                logger.debug(f"Failed to read {path}: {e}")
    
    def _extract_symbol(self, key: str) -> str:
        """Extract base symbol from pair key"""
        key = key.upper()
        # Remove exchange prefix
        if ':' in key:
            key = key.split(':')[1]
        # Remove quote currencies
        for quote in ['USDT', 'USDC', 'USD', 'ZUSD', 'EUR', 'ZEUR', 'BTC', 'ETH']:
            if key.endswith(quote):
                base = key[:-len(quote)]
                # Handle Kraken prefixes
                if len(base) == 4 and base[0] in ('X', 'Z'):
                    base = base[1:]
                if base == 'XBT':
                    base = 'BTC'
                return base
        return ''
    
    def get_ticker(self, symbol: str, max_age: float = CACHE_TTL_SECONDS) -> Optional[CachedTicker]:
        """
        Get ticker for symbol from cache.
        
        NO API CALLS - reads from shared cache files only!
        """
        symbol = symbol.upper()
        
        # Refresh from files
        self._read_cache_files()
        
        with self._cache_lock:
            ticker = self._tickers.get(symbol)
            if ticker and ticker.is_fresh(max_age):
                return ticker
        return None
    
    def get_price(self, symbol: str, max_age: float = CACHE_TTL_SECONDS) -> Optional[float]:
        """Get price for symbol from cache. Returns None if not available/stale."""
        ticker = self.get_ticker(symbol, max_age)
        return ticker.price if ticker else None
    
    def get_all_tickers(self, max_age: float = CACHE_TTL_SECONDS) -> Dict[str, CachedTicker]:
        """Get all fresh tickers"""
        self._read_cache_files()
        with self._cache_lock:
            return {s: t for s, t in self._tickers.items() if t.is_fresh(max_age)}
    
    def get_all_prices(self, max_age: float = CACHE_TTL_SECONDS) -> Dict[str, float]:
        """Get all fresh prices as symbol -> price dict"""
        tickers = self.get_all_tickers(max_age)
        return {s: t.price for s, t in tickers.items()}
    
    def update_ticker(self, ticker: CachedTicker) -> None:
        """Update a ticker in memory (used by feeders)"""
        with self._cache_lock:
            self._tickers[ticker.symbol] = ticker
    
    def write_cache(self) -> None:
        """Write current cache to unified file"""
        with self._cache_lock:
            tickers = dict(self._tickers)
        
        # Build cache structure
        ticker_cache = {}
        prices = {}
        for symbol, t in tickers.items():
            prices[symbol] = t.price
            key = f"{symbol}USDT"  # Binance-style key
            ticker_cache[key] = {
                'base': symbol,
                'quote': 'USDT',
                'price': t.price,
                'bid': t.bid,
                'ask': t.ask,
                'change24h': t.change_24h,
                'volume': t.volume_24h,
                'source': t.source,
                'timestamp': t.timestamp,
                'pair': t.pair,
                'exchange': t.source.split('_')[0] if '_' in t.source else t.source
            }
            # Also add with exchange prefix for compatibility
            ticker_cache[f"binance:{key}"] = ticker_cache[key]
        
        data = {
            'generated_at': time.time(),
            'source': 'unified_market_cache',
            'prices': prices,
            'ticker_cache': ticker_cache,
            'count': len(prices)
        }
        
        _atomic_write_json(UNIFIED_CACHE_PATH, data)


def _atomic_write_json(path: str, data: Dict[str, Any]) -> None:
    """Atomic JSON write to prevent corruption"""
    tmp = f"{path}.tmp"
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp, path)


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS - Use these from any module!
# ═══════════════════════════════════════════════════════════════════════════════

_cache_instance: Optional[UnifiedMarketCache] = None

def get_market_cache() -> UnifiedMarketCache:
    """Get the singleton market cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = UnifiedMarketCache()
    return _cache_instance


def get_price(symbol: str, max_age: float = CACHE_TTL_SECONDS) -> Optional[float]:
    """
    Get price for symbol from shared cache.
    
    This is the RECOMMENDED way to get prices - NO API CALLS!
    
    Args:
        symbol: Asset symbol (BTC, ETH, etc.)
        max_age: Maximum age of data in seconds
        
    Returns:
        Price as float, or None if not available/stale
    """
    return get_market_cache().get_price(symbol, max_age)


def get_ticker(symbol: str, max_age: float = CACHE_TTL_SECONDS) -> Optional[CachedTicker]:
    """Get full ticker data for symbol from shared cache"""
    return get_market_cache().get_ticker(symbol, max_age)


def get_all_prices(max_age: float = CACHE_TTL_SECONDS) -> Dict[str, float]:
    """Get all available prices from shared cache"""
    return get_market_cache().get_all_prices(max_age)


# ═══════════════════════════════════════════════════════════════════════════════
# BINANCE WEBSOCKET FEEDER
# ═══════════════════════════════════════════════════════════════════════════════

class BinanceWSFeeder:
    """
    Binance WebSocket feeder that writes to shared cache.
    
    This should be the ONLY process making market data calls!
    All other processes read from the cache file.
    """
    
    def __init__(self, symbols: List[str] = None):
        self.symbols = symbols or DEFAULT_SYMBOLS
        self.cache = get_market_cache()
        self.running = False
        self._ws = None
        self._thread = None
        
    def start(self):
        """Start the WebSocket feeder in background thread"""
        if self.running:
            return
        
        self.running = True
        self._thread = threading.Thread(target=self._run_forever, daemon=True)
        self._thread.start()
        logger.info(f"🔶 BinanceWSFeeder started for {len(self.symbols)} symbols")
    
    def stop(self):
        """Stop the feeder"""
        self.running = False
        if self._ws:
            try:
                self._ws.close()
            except:
                pass
    
    def _run_forever(self):
        """Run WebSocket connection with auto-reconnect"""
        while self.running:
            try:
                self._connect_and_stream()
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            
            if self.running:
                logger.info("Reconnecting in 5 seconds...")
                time.sleep(5)
    
    def _connect_and_stream(self):
        """Connect to Binance WebSocket and stream data"""
        try:
            import websocket
        except ImportError:
            logger.error("websocket-client not installed!")
            return
        
        # Build stream URL for all symbols
        streams = [f"{s.lower()}usdt@ticker" for s in self.symbols]
        url = f"wss://stream.binance.com:9443/stream?streams={'/'.join(streams)}"
        
        def on_message(ws, message):
            try:
                data = json.loads(message)
                if 'data' in data:
                    self._handle_ticker(data['data'])
            except Exception as e:
                logger.debug(f"Message parse error: {e}")
        
        def on_error(ws, error):
            logger.warning(f"WebSocket error: {error}")
        
        def on_close(ws, close_status, close_msg):
            logger.info(f"WebSocket closed: {close_status} {close_msg}")
        
        def on_open(ws):
            logger.info(f"🔶 Connected to Binance WebSocket ({len(self.symbols)} symbols)")
        
        self._ws = websocket.WebSocketApp(
            url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open
        )
        
        self._ws.run_forever()
    
    def _handle_ticker(self, data: Dict):
        """Handle incoming ticker data"""
        try:
            symbol_pair = data.get('s', '')  # BTCUSDT
            if not symbol_pair:
                return
            
            # Extract base symbol
            base = symbol_pair.replace('USDT', '').replace('USDC', '').replace('USD', '')
            if not base:
                return
            
            ticker = CachedTicker(
                symbol=base,
                price=float(data.get('c', 0)),  # Close/last price
                bid=float(data.get('b', 0)),    # Best bid
                ask=float(data.get('a', 0)),    # Best ask
                change_24h=float(data.get('P', 0)),  # Price change percent
                volume_24h=float(data.get('q', 0)),  # Quote volume
                source='binance_ws',
                timestamp=time.time(),
                pair=symbol_pair
            )
            
            if ticker.price > 0:
                self.cache.update_ticker(ticker)
                
        except Exception as e:
            logger.debug(f"Ticker parse error: {e}")
    
    def write_cache_periodically(self, interval: float = 1.0):
        """Write cache to file periodically"""
        while self.running:
            try:
                self.cache.write_cache()
                # Also write to Binance-specific path for compatibility
                _write_binance_cache(self.cache.get_all_tickers())
            except Exception as e:
                logger.debug(f"Cache write error: {e}")
            time.sleep(interval)


def _write_binance_cache(tickers: Dict[str, CachedTicker]):
    """Write Binance-format cache for compatibility"""
    ticker_cache = {}
    prices = {}
    
    for symbol, t in tickers.items():
        if t.source != 'binance_ws':
            continue
        prices[symbol] = t.price
        key = f"{symbol}USDT"
        ticker_cache[key] = {
            'base': symbol,
            'quote': 'USDT',
            'price': t.price,
            'bid': t.bid,
            'ask': t.ask,
            'change24h': t.change_24h,
            'volume': t.volume_24h,
            'source': 'binance_ws',
            'timestamp': t.timestamp,
            'pair': t.pair,
            'exchange': 'binance'
        }
        ticker_cache[f"binance:{key}"] = ticker_cache[key]
    
    data = {
        'generated_at': time.time(),
        'source': 'binance_websocket',
        'prices': prices,
        'ticker_cache': ticker_cache,
        'count': len(prices)
    }
    
    _atomic_write_json(BINANCE_CACHE_PATH, data)


# ═══════════════════════════════════════════════════════════════════════════════
# CLI - Run as standalone feeder
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Run the Binance WebSocket feeder as a standalone process"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Unified Market Cache - Binance WebSocket Feeder')
    parser.add_argument('--symbols', nargs='+', default=DEFAULT_SYMBOLS, help='Symbols to track')
    parser.add_argument('--write-interval', type=float, default=1.0, help='Cache write interval in seconds')
    args = parser.parse_args()
    
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║     🌐 UNIFIED MARKET CACHE - BINANCE WEBSOCKET FEEDER                       ║")
    print("║     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                        ║")
    print(f"║     Tracking {len(args.symbols)} symbols via FREE WebSocket                            ║")
    print(f"║     Cache: {UNIFIED_CACHE_PATH:<52} ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    
    feeder = BinanceWSFeeder(args.symbols)
    feeder.start()
    
    # Run cache writer in main thread
    try:
        feeder.write_cache_periodically(args.write_interval)
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        feeder.stop()


if __name__ == '__main__':
    main()
