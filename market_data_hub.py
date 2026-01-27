#!/usr/bin/env python3
"""
Market Data Hub - Phase 2 Rate Limiting Optimization

Central prefetching service for market data to reduce API calls and 429 errors.
Periodically fetches quotes for commonly watched symbols and serves them from cache.

Features:
- Periodic prefetching (2s intervals)
- Request coalescing (50ms windows)
- Integration with AlpacaClient caching
- Background thread operation
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import time
import threading
import logging
import os
from typing import Dict, List, Optional, Set
from rate_limiter import TTLCache

# Metrics (optional)
try:
    from metrics import market_data_prefetch_cycles, market_data_cache_hits, market_data_api_calls_saved
    METRICS_AVAILABLE = True
except Exception:
    METRICS_AVAILABLE = False

logger = logging.getLogger(__name__)

class MarketDataHub:
    """
    Central market data prefetching hub to reduce API calls.

    Periodically fetches quotes for watched symbols and serves them from cache.
    Integrates with AlpacaClient for seamless operation.
    """

    def __init__(self, alpaca_client, prefetch_interval: float = 2.0, coalesce_window: float = 0.05):
        """
        Initialize the Market Data Hub.

        Args:
            alpaca_client: AlpacaClient instance to use for fetching
            prefetch_interval: Seconds between prefetch cycles (default 2.0)
            coalesce_window: Seconds to wait for request coalescing (default 0.05)
        """
        # Read from environment variables
        try:
            prefetch_interval = float(os.getenv('MARKET_DATA_HUB_PREFETCH_INTERVAL', str(prefetch_interval)))
        except Exception:
            pass

        try:
            coalesce_window = float(os.getenv('MARKET_DATA_HUB_COALESCE_WINDOW', str(coalesce_window)))
        except Exception:
            pass

        self.alpaca_client = alpaca_client
        self.prefetch_interval = prefetch_interval
        self.coalesce_window = coalesce_window

        # Cache for prefetched quotes
        self._prefetch_cache = TTLCache(default_ttl=prefetch_interval * 1.5, name='market_data_hub')

        # Symbols to prefetch
        self.watched_symbols: Set[str] = set()

        # Background thread control
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Request coalescing
        self._pending_requests: Dict[str, List[threading.Event]] = {}
        self._coalesce_lock = threading.Lock()

        # Stats
        self.prefetch_cycles = 0
        self.cache_hits = 0
        self.api_calls_saved = 0

    def add_watched_symbols(self, symbols: List[str]):
        """Add symbols to the prefetch watchlist."""
        self.watched_symbols.update(symbols)
        logger.info(f"MarketDataHub: Added {len(symbols)} symbols to watchlist (total: {len(self.watched_symbols)})")

    def remove_watched_symbols(self, symbols: List[str]):
        """Remove symbols from the prefetch watchlist."""
        self.watched_symbols.difference_update(symbols)
        logger.info(f"MarketDataHub: Removed {len(symbols)} symbols from watchlist (total: {len(self.watched_symbols)})")

    def start(self):
        """Start the background prefetching thread."""
        if self._running:
            logger.warning("MarketDataHub: Already running")
            return

        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._prefetch_loop, daemon=True, name="MarketDataHub")
        self._thread.start()
        logger.info("MarketDataHub: Started prefetching thread")

    def stop(self):
        """Stop the background prefetching thread."""
        if not self._running:
            return

        self._running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5.0)
        logger.info("MarketDataHub: Stopped prefetching thread")

    def get_quote(self, symbol: str) -> Dict:
        """
        Get quote for symbol, preferring hub cache over API calls.

        Uses request coalescing for near-simultaneous requests.
        """
        # Check prefetch cache first
        cache_key = f"quote::{symbol}"
        cached = self._prefetch_cache.get(cache_key)
        if cached is not None:
            self.cache_hits += 1
            if METRICS_AVAILABLE:
                try:
                    market_data_cache_hits.inc(1, hub='global')
                except Exception:
                    pass
            return cached

        # Check if there's already a pending request for this symbol
        with self._coalesce_lock:
            if symbol in self._pending_requests:
                # Wait for the existing request to complete
                event = threading.Event()
                self._pending_requests[symbol].append(event)
                event.wait(timeout=self.coalesce_window * 2)
                # Check cache again after waiting
                cached = self._prefetch_cache.get(cache_key)
                if cached is not None:
                    self.api_calls_saved += 1
                    if METRICS_AVAILABLE:
                        try:
                            market_data_api_calls_saved.inc(1, hub='global')
                        except Exception:
                            pass
                    return cached
            else:
                # Start a new coalesced request
                self._pending_requests[symbol] = []

        try:
            # Fetch from Alpaca client but avoid calling get_last_quote to prevent
            # recursive calls (MarketDataHub -> AlpacaClient.get_last_quote -> hub.get_quote ...)
            normalized = self.alpaca_client._normalize_pair_symbol(symbol)
            quote = None

            if normalized and '/' in normalized:
                # Use batched crypto quotes endpoint
                try:
                    quotes = self.alpaca_client.get_latest_crypto_quotes([normalized])
                    q = quotes.get(normalized)
                    if q:
                        last_price = (float(q.get('bp', 0) or 0.0) + float(q.get('ap', 0) or 0.0)) / 2 if (q.get('bp') and q.get('ap')) else (float(q.get('bp', 0) or 0.0) or float(q.get('ap', 0) or 0.0) or 0.0)
                        quote = {"last": {"price": last_price}, "raw": q}
                except Exception:
                    quote = None

            if quote is None:
                # Fallback to stock latest quote endpoint - only for actual stocks
                # Skip crypto symbols (they will have '/' in normalized form or be known crypto base)
                is_crypto = False
                if normalized and '/' in normalized:
                    is_crypto = True
                else:
                    # Check if bare symbol is a known crypto
                    try:
                        from alpaca_client import CRYPTO_BASE_SYMBOLS
                        base_sym = symbol.upper()
                        for suffix in ('USDT', 'USDC', 'USD'):
                            if base_sym.endswith(suffix) and len(base_sym) > len(suffix):
                                base_sym = base_sym[:-len(suffix)]
                                break
                        if base_sym in CRYPTO_BASE_SYMBOLS:
                            is_crypto = True
                    except ImportError:
                        pass
                
                if is_crypto:
                    # This is a crypto pair - skip stock fallback
                    quote = None
                else:
                    try:
                        resp = self.alpaca_client._request(
                            "GET",
                            f"/v2/stocks/{symbol}/quotes/latest",
                            base_url=self.alpaca_client.data_url,
                            request_type='data'
                        )
                        q = resp.get('quote') or resp.get('quotes', {}).get(symbol) or resp
                        bp = float(q.get('bp', 0) or 0.0)
                        ap = float(q.get('ap', 0) or 0.0)
                        last_price = (bp + ap) / 2 if (bp > 0 and ap > 0) else (bp or ap or 0.0)
                        quote = {"last": {"price": last_price}, "raw": q}
                    except Exception:
                        quote = None

            if quote:
                # Store in prefetch cache
                self._prefetch_cache.set(cache_key, quote)
                return quote

            # If all fetches failed, return empty dict
            return {}
        finally:
            # Notify any waiting requests
            with self._coalesce_lock:
                waiting_events = self._pending_requests.pop(symbol, [])
                for event in waiting_events:
                    event.set()

    def _prefetch_loop(self):
        """Background thread that periodically prefetches quotes."""
        logger.info("MarketDataHub: Prefetch loop started")

        while not self._stop_event.wait(timeout=self.prefetch_interval):
            if not self.watched_symbols:
                continue

            try:
                symbols_to_fetch = list(self.watched_symbols)
                self.prefetch_cycles += 1

                # Batch fetch quotes
                quotes = self.alpaca_client.get_latest_crypto_quotes(symbols_to_fetch)

                # Store in prefetch cache
                for symbol, quote in quotes.items():
                    cache_key = f"quote::{symbol}"
                    self._prefetch_cache.set(cache_key, {
                        "last": {"price": (quote.get('bp', 0) + quote.get('ap', 0)) / 2 if quote.get('bp') and quote.get('ap') else 0},
                        "raw": quote
                    })

                # Update metrics
                if METRICS_AVAILABLE:
                    try:
                        market_data_prefetch_cycles.inc(1)
                    except Exception:
                        pass

                if self.prefetch_cycles % 10 == 0:  # Log every 10 cycles
                    logger.info(f"MarketDataHub: Cycle {self.prefetch_cycles} - prefetched {len(symbols_to_fetch)} symbols, "
                              f"cache hits: {self.cache_hits}, API calls saved: {self.api_calls_saved}")

            except Exception as e:
                logger.error(f"MarketDataHub: Prefetch error: {e}")

        logger.info("MarketDataHub: Prefetch loop ended")

    def get_stats(self) -> Dict:
        """Get hub statistics."""
        return {
            "prefetch_cycles": self.prefetch_cycles,
            "cache_hits": self.cache_hits,
            "api_calls_saved": self.api_calls_saved,
            "watched_symbols": len(self.watched_symbols),
            "cache_size": len(self._prefetch_cache._cache) if hasattr(self._prefetch_cache, '_cache') else 0
        }

# Global hub instance
_market_data_hub: Optional[MarketDataHub] = None

def get_market_data_hub(alpaca_client=None) -> MarketDataHub:
    """Get or create the global market data hub instance."""
    global _market_data_hub
    if _market_data_hub is None and alpaca_client is not None:
        _market_data_hub = MarketDataHub(alpaca_client)
        # Add common symbols to watchlist
        common_symbols = [
            'BTC/USD', 'ETH/USD', 'SOL/USD', 'AVAX/USD', 'ADA/USD',
            'DOT/USD', 'LINK/USD', 'UNI/USD', 'AAVE/USD', 'MATIC/USD'
        ]
        _market_data_hub.add_watched_symbols(common_symbols)
    return _market_data_hub

def start_market_data_hub(alpaca_client):
    """Start the global market data hub."""
    hub = get_market_data_hub(alpaca_client)
    if hub:
        hub.start()

def stop_market_data_hub():
    """Stop the global market data hub."""
    global _market_data_hub
    if _market_data_hub:
        _market_data_hub.stop()
        _market_data_hub = None