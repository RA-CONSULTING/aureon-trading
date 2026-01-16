import os
import requests
import time
import logging
from pathlib import Path
from typing import Dict, Any, Iterable, List, Optional

# Load environment variables from .env file
#
# NOTE:
# This project is often run from different working directories (or via stdin).
# `python-dotenv`'s default `find_dotenv()` can fail or miss the repo root.
# We therefore try a few explicit candidate paths before falling back.
try:
    from dotenv import load_dotenv

    dotenv_candidates = []
    explicit = os.getenv("DOTENV_PATH")
    if explicit:
        dotenv_candidates.append(Path(explicit))

    dotenv_candidates.append(Path.cwd() / ".env")
    dotenv_candidates.append(Path(__file__).resolve().parent / ".env")

    loaded = False
    for candidate in dotenv_candidates:
        try:
            if candidate.exists():
                load_dotenv(dotenv_path=str(candidate), override=False)
                loaded = True
                break
        except Exception:
            continue

    if not loaded:
        load_dotenv(override=False)
except ImportError:
    pass

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════════════════════════
# CRYPTO SYMBOL DETECTION - Centralized set to prevent stock API fallback for crypto
# ═══════════════════════════════════════════════════════════════════════════════════════════════════
CRYPTO_BASE_SYMBOLS = {
    'BTC', 'ETH', 'LTC', 'XRP', 'SOL', 'DOGE', 'AVAX', 'DOT', 'LINK', 'UNI',
    'AAVE', 'BCH', 'XLM', 'ATOM', 'ALGO', 'MATIC', 'SHIB', 'PEPE', 'TRUMP',
    'ADA', 'BNB', 'XMR', 'ETC', 'FIL', 'NEAR', 'APT', 'OP', 'ARB', 'CRV',
    'MKR', 'SNX', 'COMP', 'YFI', 'SUSHI', 'GRT', 'BAT', 'ZRX', 'ENJ', 'MANA',
    'SAND', 'AXS', 'GALA', 'IMX', 'LRC', 'SKY', 'XTZ', 'USDG', 'BONK', 'WIF',
    'FLOKI', 'RENDER', 'INJ', 'TIA', 'SEI', 'SUI', 'BLUR', 'JTO', 'PYTH',
    'RNDR', 'FET', 'AGIX', 'OCEAN', 'TAO', 'ORDI', 'WLD', 'STRK', 'MEME',
    'USDC', 'USDT', 'DAI', 'BUSD',  # Stablecoins (quote currencies)
}

class AlpacaClient:
    """
    Client for Alpaca Markets API (Stocks & Crypto).
    """
    def __init__(self):
        self.api_key = os.getenv('ALPACA_API_KEY')
        self.secret_key = os.getenv('ALPACA_SECRET_KEY')
        # Default to LIVE trading
        self.use_paper = os.getenv('ALPACA_PAPER', 'false').lower() == 'true'
        self.dry_run = os.getenv('ALPACA_DRY_RUN', 'false').lower() == 'true'
        
        # Telemetry: Start Prometheus server if configured
        prom_port = os.getenv('PROMETHEUS_METRICS_PORT')
        if prom_port:
            try:
                from telemetry_server import start_telemetry_server
                start_telemetry_server(int(prom_port))
            except Exception as e:
                logger.warning(f"Failed to start telemetry server: {e}")

        self.timeout_seconds = 10.0
        try:
            self.timeout_seconds = float(os.getenv("ALPACA_TIMEOUT", "10") or 10)
        except (TypeError, ValueError):
            self.timeout_seconds = 10.0
        self.max_retries = 3  # 🛡️ Increased for rate limit retries
        try:
            self.max_retries = max(0, int(os.getenv("ALPACA_RETRY_COUNT", "3") or 3))
        except (TypeError, ValueError):
            self.max_retries = 3

        if self.use_paper:
            self.base_url = "https://paper-api.alpaca.markets"
        else:
            self.base_url = "https://api.alpaca.markets"
            
        # Data API URL (Crypto)
        self.data_url = "https://data.alpaca.markets"
        
        self.session = requests.Session()
        self.last_error: Optional[Dict[str, Any]] = None

        # Rate limiting and in-memory TTL caching for market data
        from rate_limiter_v2 import AdaptiveRateLimiter
        from rate_limiter import TTLCache
        
        # Production-safe rates: trading below Alpaca's 200/min limit (3.33/sec)
        try:
            trading_rate = float(os.getenv('ALPACA_TRADING_RATE_PER_SECOND', '2.5'))  # Conservative trading rate
            data_rate = float(os.getenv('ALPACA_DATA_RATE_PER_SECOND', '5.0'))       # Data rate for quotes/bars
        except Exception:
            trading_rate = 2.5
            data_rate = 5.0
            
        try:
            trading_burst = float(os.getenv('ALPACA_TRADING_BURST_CAPACITY', str(max(1, int(trading_rate)))))
            data_burst = float(os.getenv('ALPACA_DATA_BURST_CAPACITY', str(max(1, int(data_rate)))))
        except Exception:
            trading_burst = max(1, trading_rate)
            data_burst = max(1, data_rate)

        self._rate_limiter = AdaptiveRateLimiter(
            trading_rate=trading_rate,
            data_rate=data_rate,
            trading_capacity=trading_burst,
            data_capacity=data_burst,
            name='alpaca'
        )
        try:
            ttl = float(os.getenv('ALPACA_QUOTE_CACHE_TTL', '2.0'))
        except Exception:
            ttl = 2.0
        self._quote_cache = TTLCache(default_ttl=ttl, name='alpaca_quotes')

        # Position and account caches
        try:
            pos_ttl = float(os.getenv('ALPACA_POSITION_CACHE_TTL', '5.0'))
        except Exception:
            pos_ttl = 5.0
        self._position_cache = TTLCache(default_ttl=pos_ttl, name='alpaca_positions')

        try:
            acc_ttl = float(os.getenv('ALPACA_ACCOUNT_CACHE_TTL', '10.0'))
        except Exception:
            acc_ttl = 10.0
        self._account_cache = TTLCache(default_ttl=acc_ttl, name='alpaca_account')

        # Short-lived response deduplication cache (used to avoid duplicate GETs)
        try:
            dedup_ttl = float(os.getenv('ALPACA_DEDUP_TTL', '0.2'))
        except Exception:
            dedup_ttl = 0.2
        self._response_cache = TTLCache(default_ttl=dedup_ttl, name='alpaca_response_cache')

        # Market Data Hub integration (Phase 2 optimization)
        self._market_data_hub = None
        try:
            from market_data_hub import get_market_data_hub
            self._market_data_hub = get_market_data_hub(self)
        except ImportError:
            logger.warning("MarketDataHub not available - running without prefetching")

        # Global Rate Budget integration (Phase 2 optimization)
        self._global_rate_budget = None
        try:
            from global_rate_budget import get_global_rate_budget, classify_request_type
            self._global_rate_budget = get_global_rate_budget()
        except ImportError:
            logger.warning("GlobalRateBudget not available - running without priority budgeting")

        if self.api_key and self.secret_key:
            self.session.headers.update({
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.secret_key
            })
        else:
            logger.warning("Alpaca API keys not found in environment variables.")

    def _request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None, base_url: str = None, request_type: str = 'data') -> Any:
        """Make a request with adaptive rate limiting.
        
        Args:
            request_type: 'trading' or 'data' - determines which rate limit bucket to use
        """
        url = f"{base_url or self.base_url}{endpoint}"
        for attempt in range(self.max_retries + 1):
            try:
                # Short GET dedup: avoid duplicate identical GET requests within short TTL
                cache_key = None
                if method.upper() == 'GET' and not data:
                    try:
                        params_key = ''
                        if params:
                            params_items = sorted((k, str(v)) for k, v in params.items())
                            params_key = '&'.join([f"{k}={v}" for k, v in params_items])
                        cache_key = f"GET::{url}::{params_key}"
                        cached = self._response_cache.get(cache_key)
                        if cached is not None:
                            return cached
                    except Exception:
                        cache_key = None

                # Phase 2: Global Rate Budget with priority allocation
                if self._global_rate_budget:
                    try:
                        priority = classify_request_type(endpoint, method)
                        is_trading = request_type == 'trading'
                        if not self._global_rate_budget.wait_for_slot(priority, is_trading):
                            # Request rejected due to high-priority backoff
                            logger.warning(f"Request rejected by GlobalRateBudget: {priority.name} for {endpoint}")
                            time.sleep(0.1)  # Brief delay before retry
                            continue
                    except Exception as e:
                        logger.debug(f"GlobalRateBudget check failed: {e}")

                # Respect adaptive rate limiter
                try:
                    if request_type == 'trading':
                        self._rate_limiter.wait_trading()
                    else:
                        self._rate_limiter.wait_data()
                except Exception:
                    # In case rate limiter fails, don't block the call
                    pass

                resp = self.session.request(method, url, params=params, json=data, timeout=self.timeout_seconds)

                # 🛡️ RATE LIMIT HANDLING - Respect Retry-After header if present
                if resp.status_code == 429:
                    # Trigger adaptive backoff
                    self._rate_limiter.on_429_error()

                    # Phase 2: Notify GlobalRateBudget of 429
                    if self._global_rate_budget:
                        try:
                            priority = classify_request_type(endpoint, method)
                            self._global_rate_budget.on_429_error(priority)
                        except Exception as e:
                            logger.debug(f"GlobalRateBudget 429 notification failed: {e}")
                    
                    # Metric: API 429
                    try:
                        from metrics import api_429_counter
                        api_429_counter.inc(1, exchange='alpaca', endpoint=endpoint)
                    except Exception:
                        pass

                    retry_after = resp.headers.get('Retry-After')
                    if retry_after:
                        try:
                            wait_time = float(retry_after)
                        except Exception:
                            wait_time = min(60, 2 ** (attempt + 2))  # More aggressive backoff
                    else:
                        wait_time = min(60, 2 ** (attempt + 2))  # More aggressive backoff

                    # add jitter
                    import random
                    jitter = min(2.0, wait_time * 0.2)  # More jitter
                    wait_time = wait_time + (jitter * (0.5 - random.random()))

                    logger.warning(f"Rate limited (429) - waiting {wait_time:.2f}s before retry {attempt + 1}")
                    time.sleep(max(1.0, wait_time))  # Min 1s wait
                    if attempt < self.max_retries:
                        continue
                    # Fall through to error handling if out of retries

                if not resp.ok:
                    body_text = (resp.text or "").strip()
                    logger.error(f"Alpaca API Error {resp.status_code}: {body_text} [URL: {url}]")
                    self.last_error = {
                        "status_code": resp.status_code,
                        "body": body_text[:2000],
                        "endpoint": endpoint,
                        "url": url,
                    }
                    return {}

                # Cache GET responses for dedup window
                try:
                    result_json = resp.json()
                    if cache_key and result_json is not None:
                        self._response_cache.set(cache_key, result_json)
                except Exception:
                    result_json = {}

                self.last_error = None
                return result_json
            except requests.exceptions.Timeout as e:
                if attempt < self.max_retries:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                logger.error(f"Alpaca Request Failed: {e}")
                self.last_error = {"exception": str(e), "endpoint": endpoint, "url": url}
                return {}
            except Exception as e:
                logger.error(f"Alpaca Request Failed: {e}")
                self.last_error = {"exception": str(e), "endpoint": endpoint, "url": url}
                return {}

    # ═════════════════════════════════════════════════════════════════════=
    # INTERNAL HELPERS
    # ═════════════════════════════════════════════════════════════════════=

    @staticmethod
    def _normalize_pair_symbol(symbol: str) -> Optional[str]:
        """
        Normalize crypto pair symbols to Alpaca's slash format (e.g., BTCUSD -> BTC/USD).

        Alpaca asset payloads sometimes return BTC/USD while upstream callers may
        provide BTCUSD. This helper makes sure we always talk to the API using the
        slash variant and keeps base/quote parsing consistent across the client.
        """
        if not symbol:
            return None

        cleaned = symbol.replace(' ', '').replace('-', '/').upper()
        if '/' in cleaned:
            parts = cleaned.split('/')
            if len(parts) == 2 and parts[0] and parts[1]:
                return f"{parts[0]}/{parts[1]}"

        # Check quote currencies - LONGEST FIRST to avoid "USDC".endswith("USD") matching!
        for quote in ("USDT", "USDC", "USD"):  # Longest first!
            if cleaned.endswith(quote) and len(cleaned) > len(quote):
                base = cleaned[:-len(quote)]
                return f"{base}/{quote}"

        # If it's a plain crypto symbol (no slash, doesn't end with quote), assume USD quote
        # This handles cases like "BTC", "ETH", "LTC" -> "BTC/USD", "ETH/USD", "LTC/USD"
        # Check in order: longest first to avoid substring matches
        if cleaned and not cleaned.endswith("USDT") and not cleaned.endswith("USDC") and not cleaned.endswith("USD"):
            return f"{cleaned}/USD"

        return None

    @staticmethod
    def _chunk_symbols(symbols: Iterable[str], chunk_size: int = 50) -> Iterable[List[str]]:
        chunk = []
        for sym in symbols:
            normalized = AlpacaClient._normalize_pair_symbol(sym)
            if not normalized:
                continue
            chunk.append(normalized)
            if len(chunk) >= chunk_size:
                yield chunk
                chunk = []
        if chunk:
            yield chunk

    @staticmethod
    def _resolve_symbol(symbol: str) -> str:
        normalized = AlpacaClient._normalize_pair_symbol(symbol)
        return normalized or symbol

    # ═════════════════════════════════════════════════════════════════════=
    # CORE ACCOUNT / MARKET DATA
    # ═════════════════════════════════════════════════════════════════════=

    def get_account(self) -> Dict[str, Any]:
        """Get account details with short-lived caching."""
        cached = None
        try:
            cached = self._account_cache.get('account')
        except Exception:
            pass
        if cached is not None:
            return cached

        resp = self._request("GET", "/v2/account", request_type='trading')
        try:
            if isinstance(resp, dict):
                self._account_cache.set('account', resp)
        except Exception:
            pass
        return resp

    def get_positions(self) -> List[Dict[str, Any]]:
        """Get open positions with short-lived caching."""
        cached = None
        try:
            cached = self._position_cache.get('positions')
        except Exception:
            pass
        if cached is not None:
            return cached

        resp = self._request("GET", "/v2/positions", request_type='trading')
        try:
            if isinstance(resp, list) or isinstance(resp, dict):
                self._position_cache.set('positions', resp)
        except Exception:
            pass
        return resp

    def get_position(self, symbol: str) -> Dict[str, Any]:
        """Get position for a specific symbol."""
        symbol = self._resolve_symbol(symbol)
        return self._request("GET", f"/v2/positions/{symbol}", request_type='trading')

    def list_assets(self, status: str = "active", asset_class: str = "crypto") -> List[Dict[str, Any]]:
        """List assets (compatibility helper for wave scanner)."""
        params = {"status": status, "asset_class": asset_class}
        resp = self._request("GET", "/v2/assets", params=params, request_type='data')
        return resp if isinstance(resp, list) else resp.get("assets", []) if isinstance(resp, dict) else []

    def get_clock(self) -> Dict[str, Any]:
        """Get market clock."""
        return self._request("GET", "/v2/clock", request_type='data')

    def place_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        type: str = "market",
        time_in_force: str = "gtc",
        position_intent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Place an order."""
        symbol = self._resolve_symbol(symbol)
        
        # Handle stock symbols (remove /USD for API)
        asset_class = "crypto" if symbol.endswith("USD") or ("/" in symbol and not symbol.split('/')[0].isupper()) else "us_equity"
        if asset_class == "us_equity" and "/" in symbol:
            symbol = symbol.split('/')[0]
        
        if self.dry_run:
            logger.info(f"[DRY RUN] Alpaca Order: {side} {qty} {symbol}")
            return {"id": "dry_run_id", "status": "accepted"}

        data = {
            "symbol": symbol,
            "qty": str(qty),
            "side": side,
            "type": type,
            "time_in_force": time_in_force
        }
        if position_intent:
            data["position_intent"] = position_intent
        result = self._request("POST", "/v2/orders", data=data, request_type='trading')
        
        # 🔧 FIX: For market orders, wait and query for actual fill data
        # Alpaca's initial response may not have filled_avg_price yet
        if type == "market" and result.get("id"):
            order_id = result["id"]
            import time as time_module
            
            # Poll for fill status (market orders should fill quickly)
            for attempt in range(3):  # Try up to 3 times
                # Exponential backoff: 0.5s, 1.0s, 1.5s
                time_module.sleep(0.5 * (attempt + 1))
                try:
                    order_status = self._request("GET", f"/v2/orders/{order_id}", request_type='trading')
                    status = order_status.get("status", "")
                    
                    if status == "filled":
                        # Got actual fill data!
                        filled_qty = float(order_status.get("filled_qty", 0) or 0)
                        filled_price = float(order_status.get("filled_avg_price", 0) or 0)
                        if filled_price > 0:
                            logger.info(f"   📊 Alpaca ACTUAL fill: price={filled_price:.6f}, qty={filled_qty:.6f}")
                        return order_status
                    elif status in ("canceled", "expired", "rejected"):
                        logger.warning(f"   ⚠️ Alpaca order {order_id} {status}")
                        return order_status
                    # else: still pending, keep polling
                except Exception as e:
                    logger.warning(f"   ⚠️ Could not query Alpaca order {order_id}: {e}")
            
            # Return last known status after polling
            return result
        
        return result

    # Compatibility alias for older code (create_order -> place_order)
    def create_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        type: str = "market",
        time_in_force: str = "gtc",
        position_intent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Backwards-compatible wrapper so older callers can use `create_order`."""
        return self.place_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type=type,
            time_in_force=time_in_force,
            position_intent=position_intent,
        )

    def get_crypto_bars(self, symbols: List[str], timeframe: str = "1Min", limit: int = 100) -> Dict[str, Any]:
        """Get crypto bars for one or more symbols with chunking support."""
        all_bars: Dict[str, List[Dict[str, Any]]] = {}

        for chunk in self._chunk_symbols(symbols):
            params = {
                "symbols": ",".join(chunk),
                "timeframe": timeframe,
                "limit": limit
            }
            resp = self._request("GET", "/v1beta3/crypto/us/bars", params=params, base_url=self.data_url, request_type='data')
            payload = resp.get('bars', resp) if isinstance(resp, dict) else {}

            if isinstance(payload, dict):
                for sym, data in payload.items():
                    all_bars.setdefault(sym, []).extend(data or [])

        return {"bars": all_bars} if all_bars else {}

    def get_latest_crypto_quotes(self, symbols: List[str]) -> Dict[str, Any]:
        """Get latest crypto quotes (bid/ask).

        This function will use an internal per-symbol cache to avoid making
        API calls for symbols we've recently fetched, and will batch the
        remaining symbols into as few requests as possible.
        """
        all_quotes: Dict[str, Any] = {}
        remaining: List[str] = []

        # First, try to serve from the quote cache
        for sym in symbols:
            # Normalize symbol to ensure proper format (BASE/QUOTE)
            normalized = AlpacaClient._normalize_pair_symbol(sym) or sym
            cache_key = f"last_quote::{normalized}"
            try:
                cached = self._quote_cache.get(cache_key)
            except Exception:
                cached = None
            if cached is not None and isinstance(cached, dict) and cached.get('raw') is not None:
                # Store raw API payload for compatibility
                all_quotes[normalized] = cached.get('raw')
            else:
                remaining.append(normalized)

        # For remaining symbols, batch requests into chunks and call API
        for chunk in self._chunk_symbols(remaining):
            params = {
                "symbols": ",".join(chunk)
            }
            resp = self._request("GET", "/v1beta3/crypto/us/latest/quotes", params=params, base_url=self.data_url, request_type='data')
            payload = resp.get('quotes', resp) if isinstance(resp, dict) else {}

            if isinstance(payload, dict):
                # Store results and prime the quote cache for each symbol
                for sym, q in payload.items():
                    all_quotes[sym] = q
                    try:
                        bp = float(q.get('bp', 0) or 0.0)
                        ap = float(q.get('ap', 0) or 0.0)
                        last = (bp + ap) / 2 if (bp > 0 and ap > 0) else (bp or ap or 0.0)
                        cache_val = {"last": {"price": last}, "raw": q}
                        self._quote_cache.set(f"last_quote::{sym}", cache_val)
                    except Exception:
                        # If cache priming fails, ignore
                        pass

        return all_quotes

    def get_last_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Compatibility helper used by some Aureon engines.

        Returns a dict shaped like:
          {"last": {"price": <mid>}, "raw": <api_response>}

        For stocks, uses Alpaca data API latest quote. For crypto pairs (e.g. BTC/USD
        or BTCUSD) it will prefer the crypto latest quotes endpoint and fall back
        to the stock quote endpoint when appropriate.

        Phase 2: Uses MarketDataHub prefetch cache if available.
        """
        sym = (symbol or "").upper().strip()
        if not sym:
            return {}

        # Phase 2: Check MarketDataHub first for prefetched quotes
        if self._market_data_hub:
            try:
                hub_quote = self._market_data_hub.get_quote(sym)
                if hub_quote:
                    return hub_quote
            except Exception as e:
                logger.debug(f"MarketDataHub lookup failed for {sym}: {e}")

        # Normalize to detect whether this is a crypto pair (contains '/').
        normalized = AlpacaClient._normalize_pair_symbol(sym)
        # Check TTL cache first
        cache_key = f"last_quote::{sym}"
        cached = self._quote_cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            # If looks like a crypto pair (e.g. BTC/USD or BTCUSD), prefer crypto API
            if normalized and '/' in normalized:
                try:
                    quotes = self.get_latest_crypto_quotes([normalized])
                    q = quotes.get(normalized)
                    if q:
                        bp = float(q.get('bp', 0) or 0.0)
                        ap = float(q.get('ap', 0) or 0.0)
                        last = (bp + ap) / 2 if (bp > 0 and ap > 0) else (bp or ap or 0.0)
                        res = {"last": {"price": last}, "raw": q}
                        self._quote_cache.set(cache_key, res)
                        return res
                except Exception:
                    # If crypto API fails, fall through to stock endpoint as a fallback
                    pass

            # Fallback: treat as stock symbol (use ORIGINAL symbol, NOT normalized crypto pair)
            # Stock API doesn't accept '/' in symbols - extract base for checking
            stock_sym = sym.replace("/", "").replace("USD", "").replace("USDT", "").replace("USDC", "") if '/' in (normalized or '') else sym
            # Also strip quote currencies from the end of stock_sym for bare symbols
            for quote_suffix in ('USDT', 'USDC', 'USD'):
                if stock_sym.endswith(quote_suffix) and len(stock_sym) > len(quote_suffix):
                    stock_sym = stock_sym[:-len(quote_suffix)]
                    break
            # Skip stock fallback if this is clearly a crypto pair - use centralized set
            if stock_sym.upper() in CRYPTO_BASE_SYMBOLS:
                logger.debug(f"Skipping stock fallback for crypto symbol {sym} (detected as {stock_sym})")
                return {}
            resp = self._request(
                "GET",
                f"/v2/stocks/{stock_sym}/quotes/latest",
                base_url=self.data_url,
                request_type='data'
            )
            q = {}
            if isinstance(resp, dict):
                q = resp.get("quote") or resp.get("quotes", {}).get(sym) or resp
            bp = float(q.get("bp", 0) or 0.0)
            ap = float(q.get("ap", 0) or 0.0)
            last = (bp + ap) / 2 if (bp > 0 and ap > 0) else (bp or ap or 0.0)
            res = {"last": {"price": last}, "raw": resp}
            self._quote_cache.set(cache_key, res)
            return res
        except Exception:
            return {}

    def get_assets(self, status: str = "active", asset_class: str = "crypto") -> List[Dict[str, Any]]:
        """Get list of assets."""
        params = {
            "status": status,
            "asset_class": asset_class
        }
        return self._request("GET", "/v2/assets", params=params, request_type='data')

    def get_tradable_crypto_symbols(self, quote_filter: Optional[str] = None) -> List[str]:
        """
        Return all tradable crypto symbols in normalized Alpaca format.

        Args:
            quote_filter: Optional quote currency to restrict to (e.g., 'USD')
        """
        symbols: List[str] = []
        assets = self.get_assets(status='active', asset_class='crypto') or []

        for asset in assets:
            if not asset.get('tradable'):
                continue

            normalized = self._normalize_pair_symbol(asset.get('symbol', ''))
            if not normalized:
                continue

            base, quote = normalized.split('/')
            if quote_filter and quote.upper() != quote_filter.upper():
                continue

            symbols.append(normalized)

        return symbols

    def get_tradable_stock_symbols(self) -> List[str]:
        """
        Return all tradable stock symbols.
        """
        symbols: List[str] = []
        assets = self.get_assets(status='active', asset_class='us_equity') or []

        for asset in assets:
            if not asset.get('tradable'):
                continue

            symbol = asset.get('symbol', '')
            if symbol:
                symbols.append(symbol)

        return symbols
        """Get list of assets."""
        params = {
            "status": status,
            "asset_class": asset_class
        }
        return self._request("GET", "/v2/assets", params=params)

    def get_order(self, order_id: str) -> Dict[str, Any]:
        """Get order details by ID."""
        return self._request("GET", f"/v2/orders/{order_id}", request_type='trading')

    def get_order_fills(self, order_id: str) -> Dict[str, Any]:
        """Get fill details for an order."""
        order = self.get_order(order_id)
        return order
    
    def compute_order_fees(self, order: Dict[str, Any], asset_class: str = "crypto") -> Dict[str, float]:
        """
        Calculate fees for an Alpaca order.
        
        Alpaca Fee Structure:
        - Stocks: $0 commission (PFOF revenue model)
        - Crypto: 0.15% maker / 0.25% taker (spread-based)
        
        Returns dict with:
        - fee_usd: Estimated fee in USD
        - fee_pct: Fee as percentage
        - fee_type: 'commission' or 'spread'
        """
        filled_qty = float(order.get('filled_qty', 0) or 0)
        filled_avg_price = float(order.get('filled_avg_price', 0) or 0)
        notional = filled_qty * filled_avg_price
        
        if asset_class == "us_equity":
            # Stocks are commission-free
            return {
                'fee_usd': 0.0,
                'fee_pct': 0.0,
                'fee_type': 'commission',
                'notional': notional
            }
        else:
            # Crypto: estimate based on taker fee (0.25%)
            # Note: Actual spread may vary
            taker_fee_pct = 0.0025
            fee_usd = notional * taker_fee_pct
            return {
                'fee_usd': fee_usd,
                'fee_pct': taker_fee_pct,
                'fee_type': 'spread',
                'notional': notional
            }

    def get_order_with_fees(self, order_id: str) -> Dict[str, Any]:
        """Get order with calculated fee metrics."""
        order = self.get_order(order_id)
        if not order:
            return {}
        
        symbol = order.get('symbol', '')
        # Determine asset class from symbol pattern
        asset_class = "crypto" if symbol.endswith("USD") or "/" in symbol else "us_equity"
        
        fees = self.compute_order_fees(order, asset_class)
        order['computed_fees'] = fees
        return order

    def compute_order_fees_in_quote(self, order: Dict[str, Any], primary_quote: str = "USD") -> float:
        """
        Calculate total fees for an order in the quote currency.
        This provides a consistent interface with Binance/Kraken clients.
        
        Returns: Total fee in quote currency (USD)
        """
        symbol = order.get('symbol', '')
        asset_class = "crypto" if symbol.endswith("USD") or "/" in symbol else "us_equity"
        fees = self.compute_order_fees(order, asset_class)
        return fees['fee_usd']

    def get_all_orders(self, status: str = "closed", limit: int = 500, symbols: str = None) -> List[Dict[str, Any]]:
        """
        Get all orders with optional filtering.
        
        Args:
            status: 'open', 'closed', or 'all'
            limit: Max orders to return (max 500)
            symbols: Comma-separated symbols (e.g., "BTCUSD,ETHUSD")
        """
        params = {
            "status": status,
            "limit": limit
        }
        if symbols:
            params["symbols"] = symbols
        result = self._request("GET", "/v2/orders", params=params, request_type='trading')
        return result if isinstance(result, list) else []

    def calculate_cost_basis(self, symbol: str) -> Dict[str, Any]:
        """
        Calculate cost basis for a symbol from filled orders.
        
        Returns dict with:
        - symbol: The symbol
        - total_quantity: Net quantity held
        - total_cost: Total cost of buys
        - avg_cost: Average cost per unit
        - trades: Number of trades
        """
        # Get closed (filled) orders for this symbol
        orders = self.get_all_orders(status="closed", symbols=symbol)
        
        if not orders:
            return {
                "symbol": symbol,
                "total_quantity": 0.0,
                "total_cost": 0.0,
                "avg_cost": 0.0,
                "trades": 0
            }
        
        total_qty = 0.0
        total_cost = 0.0
        buy_qty = 0.0
        buy_cost = 0.0
        trade_count = 0
        
        for order in orders:
            if order.get('status') != 'filled':
                continue
                
            filled_qty = float(order.get('filled_qty', 0) or 0)
            filled_price = float(order.get('filled_avg_price', 0) or 0)
            side = order.get('side', '')
            
            if filled_qty <= 0 or filled_price <= 0:
                continue
            
            trade_count += 1
            
            if side == 'buy':
                total_qty += filled_qty
                buy_qty += filled_qty
                buy_cost += filled_qty * filled_price
            elif side == 'sell':
                total_qty -= filled_qty
        
        avg_cost = buy_cost / buy_qty if buy_qty > 0 else 0.0
        
        return {
            "symbol": symbol,
            "total_quantity": total_qty,
            "total_cost": buy_cost,
            "avg_cost": avg_cost,
            "trades": trade_count
        }

    # ══════════════════════════════════════════════════════════════════════
    # ADVANCED ORDER TYPES - Limit, Stop, Trailing Stop, Bracket, OCO
    # ══════════════════════════════════════════════════════════════════════

    def place_limit_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        limit_price: float,
        time_in_force: str = "gtc",
        extended_hours: bool = False
    ) -> Dict[str, Any]:
        """
        Place a limit order on Alpaca.
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USD', 'AAPL')
            qty: Quantity to buy/sell
            side: 'buy' or 'sell'
            limit_price: Maximum buy price or minimum sell price
            time_in_force: 'day', 'gtc', 'ioc' (crypto only supports gtc, ioc)
            extended_hours: If True, order can execute in extended hours (stocks only)
            
        Returns:
            Order response
            
        Benefit: Better price control, may get better fills
        """
        symbol = self._resolve_symbol(symbol)
        if self.dry_run:
            logger.info(f"[DRY RUN] Alpaca Limit Order: {side} {qty} {symbol} @ {limit_price}")
            return {"id": "dry_run_id", "status": "accepted", "type": "limit"}

        data = {
            "symbol": symbol,
            "qty": str(qty),
            "side": side,
            "type": "limit",
            "limit_price": str(limit_price),
            "time_in_force": time_in_force
        }
        
        if extended_hours:
            data["extended_hours"] = True
            
        return self._request("POST", "/v2/orders", data=data, request_type='trading')

    def place_stop_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        stop_price: float,
        time_in_force: str = "gtc"
    ) -> Dict[str, Any]:
        """
        Place a stop order on Alpaca.
        
        Args:
            symbol: Trading pair
            qty: Quantity
            side: 'buy' or 'sell'
            stop_price: Price at which to trigger the order
            time_in_force: 'day', 'gtc'
            
        Returns:
            Order response
            
        Note: For crypto, use stop_limit instead (stop not supported directly)
        """
        symbol = self._resolve_symbol(symbol)
        if self.dry_run:
            logger.info(f"[DRY RUN] Alpaca Stop Order: {side} {qty} {symbol} @ stop={stop_price}")
            return {"id": "dry_run_id", "status": "accepted", "type": "stop"}

        data = {
            "symbol": symbol,
            "qty": str(qty),
            "side": side,
            "type": "stop",
            "stop_price": str(stop_price),
            "time_in_force": time_in_force
        }
        return self._request("POST", "/v2/orders", data=data, request_type='trading')

    def place_stop_limit_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        stop_price: float,
        limit_price: float,
        time_in_force: str = "gtc"
    ) -> Dict[str, Any]:
        """
        Place a stop-limit order on Alpaca.
        
        Args:
            symbol: Trading pair
            qty: Quantity
            side: 'buy' or 'sell'
            stop_price: Price at which to trigger
            limit_price: Price limit for execution after trigger
            time_in_force: 'day', 'gtc'
            
        Returns:
            Order response
            
        For crypto: This is the primary way to do stop-loss (stop orders not supported)
        """
        symbol = self._resolve_symbol(symbol)
        if self.dry_run:
            logger.info(f"[DRY RUN] Alpaca Stop-Limit: {side} {qty} {symbol} @ stop={stop_price} limit={limit_price}")
            return {"id": "dry_run_id", "status": "accepted", "type": "stop_limit"}

        data = {
            "symbol": symbol,
            "qty": str(qty),
            "side": side,
            "type": "stop_limit",
            "stop_price": str(stop_price),
            "limit_price": str(limit_price),
            "time_in_force": time_in_force
        }
        return self._request("POST", "/v2/orders", data=data, request_type='trading')

    def place_trailing_stop_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        trail_percent: float = None,
        trail_price: float = None,
        time_in_force: str = "day"
    ) -> Dict[str, Any]:
        """
        Place a trailing stop order on Alpaca.
        
        Args:
            symbol: Trading pair
            qty: Quantity
            side: 'buy' or 'sell'
            trail_percent: Percentage to trail (e.g., 2.0 = 2%)
            trail_price: Dollar amount to trail (alternative to percent)
            time_in_force: 'day' or 'gtc'
            
        Returns:
            Order response
            
        Example: 2% trailing stop on AAPL at $200 -> stop at $196
                 If AAPL rises to $210 -> stop auto-adjusts to $205.80
                 
        Note: Trailing stop only triggers during regular market hours
        """
        symbol = self._resolve_symbol(symbol)
        if self.dry_run:
            trail = f"{trail_percent}%" if trail_percent else f"${trail_price}"
            logger.info(f"[DRY RUN] Alpaca Trailing Stop: {side} {qty} {symbol} trail={trail}")
            return {"id": "dry_run_id", "status": "accepted", "type": "trailing_stop"}

        data = {
            "symbol": symbol,
            "qty": str(qty),
            "side": side,
            "type": "trailing_stop",
            "time_in_force": time_in_force
        }
        
        if trail_percent is not None:
            data["trail_percent"] = str(trail_percent)
        elif trail_price is not None:
            data["trail_price"] = str(trail_price)
        else:
            raise ValueError("Must provide either trail_percent or trail_price")
            
        return self._request("POST", "/v2/orders", data=data, request_type='trading')

    def place_bracket_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        entry_type: str = "market",
        entry_limit_price: float = None,
        take_profit_limit: float = None,
        stop_loss_stop: float = None,
        stop_loss_limit: float = None,
        time_in_force: str = "gtc",
        position_intent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Place a bracket order (entry + take-profit + stop-loss) on Alpaca.
        
        This is atomic - if entry fills, both TP and SL orders activate.
        One cancels the other when either fills.
        
        Args:
            symbol: Trading pair
            qty: Quantity for all legs
            side: 'buy' or 'sell' for entry
            entry_type: 'market' or 'limit' for entry order
            entry_limit_price: Required if entry_type is 'limit'
            take_profit_limit: Limit price for take-profit (required)
            stop_loss_stop: Stop trigger price for stop-loss (required)
            stop_loss_limit: Optional limit price for stop-loss (creates stop-limit)
            time_in_force: 'day' or 'gtc'
            
        Returns:
            Order response with legs array
            
        Example:
            place_bracket_order('AAPL', 100, 'buy',
                               take_profit_limit=210,
                               stop_loss_stop=195,
                               stop_loss_limit=194)
        """
        symbol = self._resolve_symbol(symbol)
        if self.dry_run:
            logger.info(f"[DRY RUN] Alpaca Bracket: {side} {qty} {symbol} TP={take_profit_limit} SL={stop_loss_stop}")
            return {"id": "dry_run_id", "status": "accepted", "order_class": "bracket"}

        if take_profit_limit is None or stop_loss_stop is None:
            raise ValueError("Bracket orders require both take_profit_limit and stop_loss_stop")

        data = {
            "symbol": symbol,
            "qty": str(qty),
            "side": side,
            "type": entry_type,
            "time_in_force": time_in_force,
            "order_class": "bracket",
            "take_profit": {
                "limit_price": str(take_profit_limit)
            },
            "stop_loss": {
                "stop_price": str(stop_loss_stop)
            }
        }
        if position_intent:
            data["position_intent"] = position_intent
        
        if entry_type == "limit" and entry_limit_price:
            data["limit_price"] = str(entry_limit_price)
            
        if stop_loss_limit:
            data["stop_loss"]["limit_price"] = str(stop_loss_limit)
            
        return self._request("POST", "/v2/orders", data=data, request_type='trading')

    def place_oco_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        take_profit_limit: float,
        stop_loss_stop: float,
        stop_loss_limit: float = None,
        time_in_force: str = "gtc"
    ) -> Dict[str, Any]:
        """
        Place an OCO (One-Cancels-Other) order on Alpaca.
        
        Use this for existing positions to add TP and SL.
        When one fills, the other is automatically cancelled.
        
        Args:
            symbol: Trading pair
            qty: Quantity to close
            side: 'sell' for long positions, 'buy' for short positions
            take_profit_limit: Limit price for take-profit
            stop_loss_stop: Stop trigger price for stop-loss
            stop_loss_limit: Optional limit price after stop triggers
            time_in_force: 'day' or 'gtc'
            
        Returns:
            Order response
        """
        symbol = self._resolve_symbol(symbol)
        if self.dry_run:
            logger.info(f"[DRY RUN] Alpaca OCO: {side} {qty} {symbol} TP={take_profit_limit} SL={stop_loss_stop}")
            return {"id": "dry_run_id", "status": "accepted", "order_class": "oco"}

        data = {
            "symbol": symbol,
            "qty": str(qty),
            "side": side,
            "type": "limit",  # OCO requires limit type
            "time_in_force": time_in_force,
            "order_class": "oco",
            "take_profit": {
                "limit_price": str(take_profit_limit)
            },
            "stop_loss": {
                "stop_price": str(stop_loss_stop)
            }
        }
        
        if stop_loss_limit:
            data["stop_loss"]["limit_price"] = str(stop_loss_limit)
            
        return self._request("POST", "/v2/orders", data=data, request_type='trading')

    def place_oto_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        entry_type: str = "market",
        entry_limit_price: float = None,
        take_profit_limit: float = None,
        stop_loss_stop: float = None,
        stop_loss_limit: float = None,
        time_in_force: str = "gtc",
        position_intent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Place an OTO (One-Triggers-Other) order on Alpaca.
        
        Entry order triggers a single exit order (either TP or SL, not both).
        Use this when you only want one exit condition.
        
        Args:
            symbol: Trading pair
            qty: Quantity
            side: 'buy' or 'sell' for entry
            entry_type: 'market' or 'limit'
            entry_limit_price: Required if entry_type is 'limit'
            take_profit_limit: Limit price for TP (provide this OR stop_loss)
            stop_loss_stop: Stop price for SL (provide this OR take_profit)
            stop_loss_limit: Optional limit price for SL
            time_in_force: 'day' or 'gtc'
            
        Returns:
            Order response
        """
        symbol = self._resolve_symbol(symbol)
        if self.dry_run:
            exit_type = f"TP={take_profit_limit}" if take_profit_limit else f"SL={stop_loss_stop}"
            logger.info(f"[DRY RUN] Alpaca OTO: {side} {qty} {symbol} {exit_type}")
            return {"id": "dry_run_id", "status": "accepted", "order_class": "oto"}

        if not take_profit_limit and not stop_loss_stop:
            raise ValueError("OTO orders require either take_profit_limit or stop_loss_stop")

        data = {
            "symbol": symbol,
            "qty": str(qty),
            "side": side,
            "type": entry_type,
            "time_in_force": time_in_force,
            "order_class": "oto"
        }
        if position_intent:
            data["position_intent"] = position_intent
        
        if entry_type == "limit" and entry_limit_price:
            data["limit_price"] = str(entry_limit_price)
            
        if take_profit_limit:
            data["take_profit"] = {"limit_price": str(take_profit_limit)}
        elif stop_loss_stop:
            data["stop_loss"] = {"stop_price": str(stop_loss_stop)}
            if stop_loss_limit:
                data["stop_loss"]["limit_price"] = str(stop_loss_limit)
                
        return self._request("POST", "/v2/orders", data=data, request_type='trading')

    # ══════════════════════════════════════════════════════════════════════
    # ORDER MANAGEMENT - Query, Cancel, Replace
    # ══════════════════════════════════════════════════════════════════════

    def get_open_orders(self, symbol: str = None) -> List[Dict[str, Any]]:
        """
        Get all open orders, optionally filtered by symbol.
        
        Args:
            symbol: If provided, filter to this symbol only
            
        Returns:
            List of open orders
        """
        params = {"status": "open"}
        if symbol:
            params["symbols"] = symbol
        result = self._request("GET", "/v2/orders", params=params, request_type='trading')
        return result if isinstance(result, list) else []

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """
        Cancel a specific order by ID.
        
        Args:
            order_id: The Alpaca order ID
            
        Returns:
            Empty dict on success, error on failure
        """
        if self.dry_run:
            logger.info(f"[DRY RUN] Cancel order: {order_id}")
            return {"status": "canceled"}
            
        return self._request("DELETE", f"/v2/orders/{order_id}", request_type='trading')

    def cancel_all_orders(self) -> Dict[str, Any]:
        """
        Cancel all open orders.
        
        Returns:
            Response with count of cancelled orders
        """
        if self.dry_run:
            logger.info("[DRY RUN] Cancel all orders")
            return {"status": "canceled", "count": 0}
            
        return self._request("DELETE", "/v2/orders", request_type='trading')

    def replace_order(
        self,
        order_id: str,
        qty: float = None,
        limit_price: float = None,
        stop_price: float = None,
        trail: float = None,
        time_in_force: str = None
    ) -> Dict[str, Any]:
        """
        Replace/modify an existing order.
        
        Args:
            order_id: The order to replace
            qty: New quantity (optional)
            limit_price: New limit price (optional)
            stop_price: New stop price (optional)
            trail: New trail value for trailing stop (optional)
            time_in_force: New TIF (optional)
            
        Returns:
            New order response (replacement creates new order ID)
        """
        if self.dry_run:
            logger.info(f"[DRY RUN] Replace order: {order_id}")
            return {"id": "dry_run_replaced", "status": "accepted"}

        data = {}
        if qty is not None:
            data["qty"] = str(qty)
        if limit_price is not None:
            data["limit_price"] = str(limit_price)
        if stop_price is not None:
            data["stop_price"] = str(stop_price)
        if trail is not None:
            data["trail"] = str(trail)
        if time_in_force is not None:
            data["time_in_force"] = time_in_force
            
        return self._request("PATCH", f"/v2/orders/{order_id}", data=data, request_type='trading')

    # ══════════════════════════════════════════════════════════════════════
    # CONVENIENCE METHODS - Kraken-compatible interface
    # ══════════════════════════════════════════════════════════════════════

    def place_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float = None,
        quote_qty: float = None,
        position_intent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Place a market order (Kraken-compatible interface).
        
        Args:
            symbol: Trading pair
            side: 'buy' or 'sell'
            quantity: Amount of base asset
            quote_qty: Amount of quote asset (converted to quantity)
            
        Returns:
            Order response
        """
        symbol = self._resolve_symbol(symbol)
        side_norm = (side or '').lower()
        if quote_qty and not quantity:
            # Need to estimate quantity from quote
            try:
                quotes = self.get_latest_crypto_quotes([symbol])
                if symbol in quotes:
                    q = quotes[symbol]
                    mid_price = (float(q.get('bp', 0)) + float(q.get('ap', 0))) / 2
                    if mid_price > 0:
                        quantity = quote_qty / mid_price
            except:
                pass
                
        if not quantity:
            logger.error(f"Cannot place market order without quantity for {symbol}")
            return {}

        # Crypto SELLs can fail if you try to sell the full filled quantity because
        # Alpaca may reserve a small amount for fees/spread, leaving qty_available
        # slightly below filled_qty. Clamp to available to prevent 40310000.
        try:
            if side_norm == 'sell' and '/' in symbol:
                base = symbol.split('/')[0]
                available = float(self.get_free_balance(base) or 0.0)
                req = float(quantity or 0.0)
                if available > 0 and req > 0:
                    if req > available:
                        logger.warning(
                            f"Alpaca SELL clamped for {symbol}: requested {req:.12f} > available {available:.12f}"
                        )
                        req = available
                    # Extra safety margin to avoid rounding/hold/reserve edge
                    req = req * 0.999
                    if req <= 0:
                        return {}
                    quantity = req
        except Exception:
            pass
            
        return self.place_order(symbol, quantity, side, type="market", position_intent=position_intent)

    def place_stop_loss_order(self, symbol: str, side: str, quantity: float, stop_price: float, limit_price: float = None) -> Dict[str, Any]:
        """
        Place a stop-loss order (Kraken-compatible interface).
        For crypto, uses stop_limit since stop orders aren't supported.
        
        Args:
            symbol: Trading pair
            side: 'sell' for long positions
            quantity: Amount to sell when triggered
            stop_price: Price at which to trigger
            limit_price: Optional limit price after trigger
            
        Returns:
            Order response
        """
        symbol = self._resolve_symbol(symbol)
        # For crypto, stop orders aren't supported - use stop_limit
        is_crypto = "/" in symbol or symbol.endswith("USD") and len(symbol) > 5
        
        if is_crypto or limit_price:
            # Use stop_limit for crypto (required) or if limit specified
            lp = limit_price if limit_price else stop_price * 0.995  # 0.5% below stop
            return self.place_stop_limit_order(symbol, quantity, side, stop_price, lp)
        else:
            return self.place_stop_order(symbol, quantity, side, stop_price)

    def place_take_profit_order(self, symbol: str, side: str, quantity: float, take_profit_price: float, limit_price: float = None) -> Dict[str, Any]:
        """
        Place a take-profit order (Kraken-compatible interface).
        Uses limit order at the take-profit price.
        
        Args:
            symbol: Trading pair
            side: 'sell' for long positions
            quantity: Amount to sell
            take_profit_price: Price at which to take profit
            limit_price: Optional different limit price
            
        Returns:
            Order response
        """
        symbol = self._resolve_symbol(symbol)
        price = limit_price if limit_price else take_profit_price
        return self.place_limit_order(symbol, quantity, side, price)

    def place_order_with_tp_sl(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "market",
        price: float = None,
        take_profit: float = None,
        stop_loss: float = None,
        position_intent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Place an order with attached Take-Profit and/or Stop-Loss (Kraken-compatible).
        Uses Alpaca's bracket order for atomic TP+SL, or OTO for single exit.
        
        Args:
            symbol: Trading pair
            side: 'buy' or 'sell' for entry
            quantity: Amount
            order_type: 'market' or 'limit'
            price: Required if order_type is 'limit'
            take_profit: Take-profit price
            stop_loss: Stop-loss price
            
        Returns:
            Order response
        """
        symbol = self._resolve_symbol(symbol)
        if take_profit and stop_loss:
            # Both TP and SL -> use bracket order
            return self.place_bracket_order(
                symbol, quantity, side,
                entry_type=order_type,
                entry_limit_price=price,
                take_profit_limit=take_profit,
                stop_loss_stop=stop_loss,
                position_intent=position_intent,
            )
        elif take_profit or stop_loss:
            # Single exit -> use OTO order
            return self.place_oto_order(
                symbol, quantity, side,
                entry_type=order_type,
                entry_limit_price=price,
                take_profit_limit=take_profit,
                stop_loss_stop=stop_loss,
                position_intent=position_intent,
            )
        else:
            # No exits -> regular order
            if order_type == "limit" and price:
                return self.place_limit_order(symbol, quantity, side, price)
            return self.place_order(symbol, quantity, side, position_intent=position_intent)

    def get_asset(self, symbol: str) -> Dict[str, Any]:
        """Fetch asset metadata (shortable, marginable, etc.)."""
        symbol = self._resolve_symbol(symbol)
        return self._request("GET", f"/v2/assets/{symbol}")

    def is_shortable(self, symbol: str) -> bool:
        """Return True if asset is shortable for the account."""
        try:
            asset = self.get_asset(symbol) or {}
            return bool(asset.get("shortable"))
        except Exception:
            return False

    def open_position_with_tp_sl(
        self,
        symbol: str,
        side: str,
        quantity: float,
        take_profit_pct: float = None,
        stop_loss_pct: float = None,
        entry_price: float = None,
        position_intent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Open a long/short with optional TP/SL based on current price."""
        symbol = self._resolve_symbol(symbol)

        if entry_price is None:
            try:
                quotes = self.get_latest_crypto_quotes([symbol]) or {}
                quote = quotes.get(symbol, {})
                bp = float(quote.get("bp") or 0)
                ap = float(quote.get("ap") or 0)
                if bp > 0 and ap > 0:
                    entry_price = (bp + ap) / 2
            except Exception:
                entry_price = None

        take_profit_price = None
        stop_loss_price = None
        if entry_price:
            if take_profit_pct is not None:
                if side == "buy":
                    take_profit_price = entry_price * (1 + take_profit_pct / 100.0)
                else:
                    take_profit_price = entry_price * (1 - take_profit_pct / 100.0)
            if stop_loss_pct is not None:
                if side == "buy":
                    stop_loss_price = entry_price * (1 - stop_loss_pct / 100.0)
                else:
                    stop_loss_price = entry_price * (1 + stop_loss_pct / 100.0)

        return self.place_order_with_tp_sl(
            symbol=symbol,
            side=side,
            quantity=quantity,
            take_profit=take_profit_price,
            stop_loss=stop_loss_price,
            position_intent=position_intent,
        )

    def get_free_balance(self, asset: str) -> float:
        """
        Get free balance for an asset (Kraken-compatible interface).
        
        Args:
            asset: Asset symbol (e.g., 'BTC', 'USD')
            
        Returns:
            Free balance amount
        """
        try:
            if asset.upper() in ['USD', 'USDT', 'USDC']:
                acct = self.get_account()
                return float(acct.get('cash', 0) or 0)
            
            positions = self.get_positions()
            for pos in positions:
                norm = self._normalize_pair_symbol(pos.get('symbol', '')) or ''
                base = norm.split('/')[0] if '/' in norm else ''
                if base.upper() == asset.upper():
                    # Prefer qty_available when present (crypto fee/hold safe)
                    return float(pos.get('qty_available', pos.get('qty', 0)) or 0)
            return 0.0
        except:
            return 0.0

    def get_account_balance(self) -> Dict[str, float]:
        """
        Get all balances (Kraken-compatible interface).
        
        Returns:
            Dict of asset -> amount
        """
        balances = {}
        try:
            acct = self.get_account()
            cash = float(acct.get('cash', 0) or 0)
            if cash > 0:
                balances['USD'] = cash
            
            positions = self.get_positions()
            for pos in positions:
                qty = float(pos.get('qty_available', pos.get('qty', 0)) or 0)
                if qty > 0:
                    norm = self._normalize_pair_symbol(pos.get('symbol', '')) or ''
                    base = norm.split('/')[0] if '/' in norm else ''
                    balances[base] = qty
        except:
            pass
        return balances

    def get_stock_snapshot(self, symbol: str) -> Dict[str, Any]:
        """Return snapshot for a stock symbol (latest/daily bars)."""
        try:
            sym = symbol.upper()
            # Use data API endpoint for market data
            return self._request("GET", f"/v2/stocks/{sym}/snapshot", base_url=self.data_url, request_type='data') or {}
        except Exception as e:
            logger.error(f"Error getting Alpaca stock snapshot for {symbol}: {e}")
            return {}

    def get_stock_snapshots(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Return snapshots for multiple stock symbols (BATCH REQUEST).
        Optimized for bulk data retrieval to avoid rate limits.
        """
        try:
            # Chunking handled by caller or simple join (URL length limits apply)
            results = {}
            # Split into chunks of 50 to be safe with URL length
            chunk_size = 50
            for i in range(0, len(symbols), chunk_size):
                chunk = symbols[i:i + chunk_size]
                syms_str = ",".join([s.upper() for s in chunk])
                # Use data API endpoint for market data
                resp = self._request("GET", "/v2/stocks/snapshots", params={"symbols": syms_str}, base_url=self.data_url, request_type='data')
                if resp and isinstance(resp, dict):
                    results.update(resp)
            return results
        except Exception as e:
            logger.error(f"Error getting Alpaca stock snapshots batch: {e}")
            return {}

    def get_latest_stock_quote(self, symbol: str) -> Dict[str, Any]:
        """Return latest quote for a stock symbol."""
        try:
            sym = symbol.upper()
            return self._request("GET", f"/v2/stocks/{sym}/quotes/latest", request_type='data') or {}
        except Exception as e:
            logger.debug(f"Stock quote endpoint unavailable for {symbol}: {e}")
            return {}

    def get_stock_bars(self, symbols: List[str], limit: int = 1) -> Dict[str, Any]:
        """Return latest bars (OHLCV) for stock symbols."""
        try:
            data = {"symbols": ",".join([s.upper() for s in symbols]), "limit": limit}
            result = self._request("GET", "/v2/stocks/bars/latest", params=data, request_type='data')
            return result if isinstance(result, dict) else {}
        except Exception as e:
            logger.debug(f"Stock bars endpoint error: {e}")
            return {}

    def get_24h_tickers(self) -> List[Dict[str, Any]]:
        """
        Get 24h ticker data for crypto assets (Kraken-compatible interface).
        
        Returns:
            List of ticker dicts with symbol, lastPrice, priceChangePercent, quoteVolume
        """
        try:
            symbols = self.get_tradable_crypto_symbols()
            if not symbols:
                return []

            bars_resp = self.get_crypto_bars(symbols, timeframe="1Day", limit=2)
            bars = bars_resp.get('bars', bars_resp) if isinstance(bars_resp, dict) else {}

            tickers = []
            for sym in symbols:
                data = bars.get(sym) if isinstance(bars, dict) else None
                if not data:
                    continue

                latest = data[-1]
                prev_close = data[-2]['c'] if len(data) > 1 else latest.get('o', 0)

                close = float(latest.get('c', 0))
                change_pct = ((close - prev_close) / prev_close * 100) if prev_close else 0
                volume = float(latest.get('v', 0)) * close

                tickers.append({
                    'symbol': sym.replace('/', ''),  # Convert BTC/USD to BTCUSD
                    'lastPrice': str(close),
                    'priceChangePercent': str(change_pct),
                    'quoteVolume': str(volume)
                })

            return tickers
        except Exception as e:
            logger.error(f"Error getting Alpaca tickers: {e}")
            return []

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Return latest bid/ask/last for a symbol (stocks or crypto)."""
        try:
            norm = self._resolve_symbol(symbol)
            
            # Check if this is a crypto symbol by examining the base
            base_sym = norm.split('/')[0] if '/' in norm else norm
            # Also check for bare crypto symbols that might not have been normalized
            for quote_suffix in ('USDT', 'USDC', 'USD'):
                if base_sym.endswith(quote_suffix) and len(base_sym) > len(quote_suffix):
                    base_sym = base_sym[:-len(quote_suffix)]
                    break
            is_crypto = base_sym.upper() in CRYPTO_BASE_SYMBOLS or '/' in norm

            # Stock path - only for actual stocks, NOT crypto
            if not is_crypto and '/' not in norm:
                # Try quote first, then snapshot, then bars as fallback
                quote_resp = self.get_latest_stock_quote(norm)
                snapshot = self.get_stock_snapshot(norm)

                quote = quote_resp.get('quote', {}) if isinstance(quote_resp, dict) else {}
                bid = float(quote.get('bp', 0) or 0.0)
                ask = float(quote.get('ap', 0) or 0.0)
                price = float(quote.get('bp', 0) or 0.0)
                if bid > 0 and ask > 0:
                    price = (bid + ask) / 2
                elif ask > 0:
                    price = ask
                elif bid > 0:
                    price = bid

                # Daily volume / change from snapshot
                daily_volume = 0.0
                todays_change_pct = 0.0
                if snapshot:
                    daily_bar = snapshot.get('dailyBar', {}) or snapshot.get('daily_bar', {})
                    prev_bar = snapshot.get('prevDailyBar', {}) or snapshot.get('prev_daily_bar', {})
                    daily_volume = float(daily_bar.get('v', 0) or 0.0)
                    prev_close = float(prev_bar.get('c', 0) or 0.0)
                    latest_close = float(daily_bar.get('c', price) or price)
                    if prev_close > 0:
                        todays_change_pct = ((latest_close - prev_close) / prev_close) * 100.0
                    if price <= 0:
                        price = latest_close

                # Fallback to bars if no price yet
                if price <= 0:
                    try:
                        bars_resp = self.get_stock_bars([norm], limit=1)
                        bars = bars_resp.get('bars', {})
                        bar = bars.get(norm, [{}])[0] if norm in bars else {}
                        price = float(bar.get('c', 0) or 0.0)
                        if daily_volume <= 0:
                            daily_volume = float(bar.get('v', 0) or 0.0)
                    except Exception:
                        pass

                return {
                    'symbol': norm,
                    'price': price,
                    'bid': bid,
                    'ask': ask,
                    'last': {'price': price},
                    'raw': {
                        'dailyVolume': daily_volume,
                        'todaysChangePerc': todays_change_pct,
                        'snapshot': snapshot
                    }
                }

            # Crypto path
            quotes = self.get_latest_crypto_quotes([norm]) or {}
            q = quotes.get(norm, {})
            bid = float(q.get('bp', 0) or 0.0)
            ask = float(q.get('ap', 0) or 0.0)
            # Use mid if both available, otherwise fall back to bid/ask
            if bid > 0 and ask > 0:
                price = (bid + ask) / 2
            else:
                price = bid or ask or 0.0
            return {
                'symbol': norm,
                'price': price,
                'bid': bid,
                'ask': ask,
            }
        except Exception as e:
            logger.error(f"Error getting Alpaca ticker for {symbol}: {e}")
            return {'symbol': symbol, 'price': 0.0, 'bid': 0.0, 'ask': 0.0}

    def convert_to_quote(self, asset: str, amount: float, quote: str) -> float:
        """
        Convert asset amount to quote currency (Kraken-compatible interface).
        
        Args:
            asset: Source asset (e.g., 'BTC')
            amount: Amount to convert
            quote: Target currency (e.g., 'USD')
            
        Returns:
            Value in quote currency
        """
        if asset.upper() == quote.upper():
            return amount
        if amount <= 0:
            return 0.0
        
        try:
            symbol = self._resolve_symbol(f"{asset}/{quote}")
            quotes = self.get_latest_crypto_quotes([symbol])
            if symbol in quotes:
                q = quotes[symbol]
                mid = (float(q.get('bp', 0)) + float(q.get('ap', 0))) / 2
                if mid > 0:
                    return amount * mid
        except:
            pass
        return 0.0

    # ══════════════════════════════════════════════════════════════════════
    # CRYPTO CONVERSION - Convert between crypto assets via USD
    # ══════════════════════════════════════════════════════════════════════

    def get_available_pairs(self, base: str = None, quote: str = None) -> List[Dict[str, Any]]:
        """
        Get available trading pairs, optionally filtered by base or quote asset.

        Note: Alpaca crypto pairs are typically USD-quoted but this helper
        normalizes any quote currency returned by the API (USD, USDT, USDC, etc.).
        
        Args:
            base: Filter by base asset (e.g., 'BTC', 'ETH')
            quote: Filter by quote asset (e.g., 'USD')
            
        Returns:
            List of pairs with base, quote, and pair name
        """
        try:
            assets = self.get_assets(status='active', asset_class='crypto') or []
            results = []

            for asset in assets:
                if not asset.get('tradable'):
                    continue

                normalized = self._normalize_pair_symbol(asset.get('symbol', ''))
                if not normalized:
                    continue

                pair_base, pair_quote = normalized.split('/')

                if base and pair_base.upper() != base.upper():
                    continue
                if quote and pair_quote.upper() != quote.upper():
                    continue

                min_qty = asset.get('min_order_size') or asset.get('min_trade_increment') or 0
                min_notional = asset.get('min_trade_increment') or 0

                results.append({
                    "pair": normalized,
                    "base": pair_base,
                    "quote": pair_quote,
                    "min_qty": float(min_qty),
                    "min_notional": float(min_notional)
                })

            return results
        except Exception as e:
            logger.error(f"Error getting Alpaca pairs: {e}")
            return []

    def find_conversion_path(self, from_asset: str, to_asset: str) -> List[Dict[str, Any]]:
        """
        Find the best path to convert from one asset to another.
        
        Note: Alpaca supports USD pairs and select BTC-quoted pairs.
        
        Args:
            from_asset: Source asset (e.g., 'BTC')
            to_asset: Target asset (e.g., 'ETH')
            
        Returns:
            List of {pair, side, description} for each trade needed
        """
        from_asset = from_asset.upper()
        to_asset = to_asset.upper()
        
        if from_asset == to_asset:
            return []
        
        pairs = self.get_available_pairs()
        pair_bases = {p["base"].upper() for p in pairs}
        pair_quotes = {(p["base"].upper(), p["quote"].upper()) for p in pairs}
        
        # If converting to/from USD, single trade
        if from_asset == 'USD':
            if (to_asset, 'USD') in pair_quotes:
                return [{
                    "pair": f"{to_asset}/USD",
                    "side": "buy",
                    "description": f"Buy {to_asset} with USD",
                    "from": "USD",
                    "to": to_asset
                }]
            return []
        
        if to_asset == 'USD':
            if (from_asset, 'USD') in pair_quotes:
                return [{
                    "pair": f"{from_asset}/USD",
                    "side": "sell",
                    "description": f"Sell {from_asset} for USD",
                    "from": from_asset,
                    "to": "USD"
                }]
            return []

        # BTC-quoted direct pairs
        if from_asset == 'BTC' and (to_asset, 'BTC') in pair_quotes:
            return [{
                "pair": f"{to_asset}/BTC",
                "side": "buy",
                "description": f"Buy {to_asset} with BTC",
                "from": "BTC",
                "to": to_asset
            }]

        if to_asset == 'BTC' and (from_asset, 'BTC') in pair_quotes:
            return [{
                "pair": f"{from_asset}/BTC",
                "side": "sell",
                "description": f"Sell {from_asset} for BTC",
                "from": from_asset,
                "to": "BTC"
            }]
        
        # Both are crypto - prefer USD bridge
        if (from_asset, 'USD') in pair_quotes and (to_asset, 'USD') in pair_quotes:
            return [
                {
                    "pair": f"{from_asset}/USD",
                    "side": "sell",
                    "description": f"Sell {from_asset} for USD",
                    "from": from_asset,
                    "to": "USD"
                },
                {
                    "pair": f"{to_asset}/USD",
                    "side": "buy",
                    "description": f"Buy {to_asset} with USD",
                    "from": "USD",
                    "to": to_asset
                }
            ]

        # Fallback: USD -> BTC -> asset when BTC-quote exists
        if (from_asset, 'USD') in pair_quotes and (to_asset, 'BTC') in pair_quotes and ('BTC', 'USD') in pair_quotes:
            return [
                {
                    "pair": f"{from_asset}/USD",
                    "side": "sell",
                    "description": f"Sell {from_asset} for USD",
                    "from": from_asset,
                    "to": "USD"
                },
                {
                    "pair": "BTC/USD",
                    "side": "buy",
                    "description": "Buy BTC with USD",
                    "from": "USD",
                    "to": "BTC"
                },
                {
                    "pair": f"{to_asset}/BTC",
                    "side": "buy",
                    "description": f"Buy {to_asset} with BTC",
                    "from": "BTC",
                    "to": to_asset
                }
            ]

    def convert_crypto(
        self,
        from_asset: str,
        to_asset: str,
        amount: float,
        use_quote_amount: bool = False
    ) -> Dict[str, Any]:
        """
        Convert one crypto asset to another within Alpaca.
        
        Note: Alpaca supports USD pairs and select BTC-quoted pairs.
        
        Args:
            from_asset: Source asset (e.g., 'BTC', 'ETH')
            to_asset: Target asset (e.g., 'ETH', 'SOL')
            amount: Amount of from_asset to convert
            use_quote_amount: If True, amount is in to_asset terms
            
        Returns:
            Conversion result with executed trades
        """
        from_asset = from_asset.upper()
        to_asset = to_asset.upper()
        
        if from_asset == to_asset:
            return {"error": "Cannot convert to same asset", "from": from_asset, "to": to_asset}
        
        # Find conversion path
        path = self.find_conversion_path(from_asset, to_asset)
        
        if not path:
            return {"error": f"No conversion path found from {from_asset} to {to_asset}"}
        
        # 👑 QUEEN MIND: Pre-flight validation for multi-step conversions
        # Alpaca typically has ~$1 minimum and goes through USD
        estimated_amount = amount
        min_value_usd = 1.0  # Alpaca minimum
        
        for i, trade in enumerate(path):
            pair = trade["pair"]
            
            # Get current price estimate
            try:
                quote_data = self.get_latest_crypto_quotes([pair])
                if pair in quote_data:
                    bp = quote_data[pair].get('bp', 0)
                    ap = quote_data[pair].get('ap', 0)
                    price = (float(bp or 0) + float(ap or 0)) / 2
                else:
                    price = 0
            except Exception:
                price = 0
            
            if trade["side"] == "sell":
                # Selling crypto for USD
                estimated_value = estimated_amount * price if price > 0 else 0
                if estimated_value < min_value_usd and estimated_value > 0:
                    return {
                        "error": f"Multi-hop step {i+1} would yield ${estimated_value:.2f} < min ${min_value_usd:.2f}",
                        "failed_step": i,
                        "pair": pair
                    }
                # Estimate received USD
                if price > 0:
                    estimated_amount = estimated_amount * price
            else:
                # Buying crypto with USD
                if estimated_amount < min_value_usd:
                    return {
                        "error": f"Multi-hop step {i+1} has ${estimated_amount:.2f} < min ${min_value_usd:.2f}",
                        "failed_step": i,
                        "pair": pair
                    }
                # Estimate received crypto
                if price > 0:
                    estimated_amount = estimated_amount / price
        
        if self.dry_run:
            return {
                "dryRun": True,
                "from_asset": from_asset,
                "to_asset": to_asset,
                "amount": amount,
                "path": path,
                "trades": len(path)
            }
        
        # Execute trades
        results = []
        remaining_amount = amount
        
        for trade in path:
            pair = trade["pair"]
            side = trade["side"]
            
            try:
                if side == "sell":
                    # Selling crypto for USD
                    result = self.place_market_order(pair, "sell", quantity=remaining_amount)
                else:
                    # Buying crypto with USD
                    result = self.place_market_order(pair, "buy", quote_qty=remaining_amount)
                
                # 🔧 FIX: Extract ACTUAL execution data from the filled order
                exec_qty_raw = result.get("filled_qty", result.get("qty", result.get("executedQty", 0)))
                exec_qty = float(exec_qty_raw) if exec_qty_raw is not None else 0.0
                filled_price = float(result.get("filled_avg_price", 0) or 0)
                
                # Calculate actual received amount
                received_amount = 0.0
                if side == "sell":
                    # SELL: We received USD (filled_qty * filled_avg_price)
                    if filled_price > 0 and exec_qty > 0:
                        received_amount = exec_qty * filled_price
                        logger.info(f"   💰 Alpaca SELL: received=${received_amount:.6f} (qty={exec_qty:.6f} @ ${filled_price:.6f})")
                    else:
                        # Fallback: estimate from current price
                        try:
                            quote_data = self.get_latest_crypto_quotes([pair])
                            if pair in quote_data:
                                bp = quote_data[pair].get('bp', 0)
                                ap = quote_data[pair].get('ap', 0)
                                mid = (float(bp or 0) + float(ap or 0)) / 2
                                if mid > 0:
                                    received_amount = remaining_amount * mid
                        except Exception:
                            pass
                else:
                    # BUY: We received crypto (filled_qty)
                    received_amount = exec_qty
                    if filled_price > 0:
                        logger.info(f"   💰 Alpaca BUY: received={exec_qty:.6f} (spent=${remaining_amount:.6f} @ ${filled_price:.6f})")
                
                # Store received amount in result for validation
                result['receivedQty'] = received_amount
                
                results.append({
                    "trade": trade,
                    "result": result,
                    "status": "success",
                    "receivedQty": received_amount
                })
                
                # Update remaining amount for next trade using ACTUAL received amount
                remaining_amount = received_amount if received_amount > 0 else remaining_amount
                    
            except Exception as e:
                results.append({
                    "trade": trade,
                    "error": str(e),
                    "status": "failed"
                })
                return {
                    "error": f"Trade failed: {e}",
                    "from_asset": from_asset,
                    "to_asset": to_asset,
                    "partial_results": results
                }
        
        return {
            "success": True,
            "from_asset": from_asset,
            "to_asset": to_asset,
            "original_amount": amount,
            "final_amount": remaining_amount,
            "path": path,
            "trades": results,
            "trade_count": len(results)
        }

    def get_convertible_assets(self) -> Dict[str, List[str]]:
        """
        Get all crypto assets that can be converted.
        
        Note: Alpaca only supports USD pairs, so all conversions go through USD.
        
        Returns:
            Dict mapping each asset to list of assets it can convert to
        """
        pairs = self.get_available_pairs()
        
        # All crypto can convert to USD and to each other (via USD)
        crypto_assets = set()
        for p in pairs:
            crypto_assets.add(p["base"].upper())
        
        conversions = {"USD": sorted(crypto_assets)}
        
        for asset in crypto_assets:
            # Can convert to USD directly, or to any other crypto via USD
            targets = {"USD"} | (crypto_assets - {asset})
            conversions[asset] = sorted(targets)
        
        return conversions
    # ══════════════════════════════════════════════════════════════════════
    # 🦙💰 EXTENDED FEE & COST TRACKING METHODS
    # ══════════════════════════════════════════════════════════════════════

    def get_all_crypto_pairs_extended(self) -> List[Dict[str, Any]]:
        """
        Get ALL crypto pairs with extended metadata.
        
        Returns list with:
        - symbol: Trading pair (e.g., 'BTC/USD')
        - base: Base asset (e.g., 'BTC')
        - quote: Quote asset (e.g., 'USD')
        - min_order_size: Minimum order quantity
        - min_trade_increment: Minimum trade increment
        - price_increment: Price tick size
        - fractionable: Whether fractional trading is supported
        - status: Active/inactive
        """
        assets = self.get_assets(status='active', asset_class='crypto')
        if not assets:
            return []
        
        pairs = []
        for asset in assets:
            if not asset.get('tradable'):
                continue
            
            symbol = asset.get('symbol', '')
            normalized = self._normalize_pair_symbol(symbol)
            if not normalized or '/' not in normalized:
                continue
            
            base, quote = normalized.split('/')
            
            pairs.append({
                'symbol': normalized,
                'base': base,
                'quote': quote,
                'min_order_size': float(asset.get('min_order_size', 0) or 0),
                'min_trade_increment': float(asset.get('min_trade_increment', 0) or 0),
                'price_increment': float(asset.get('price_increment', 0) or 0),
                'fractionable': asset.get('fractionable', False),
                'marginable': asset.get('marginable', False),
                'shortable': asset.get('shortable', False),
                'status': asset.get('status', 'unknown'),
                'exchange': asset.get('exchange', 'ALPACA'),
                'id': asset.get('id', ''),
                'name': asset.get('name', symbol)
            })
        
        logger.info(f"🦙 Found {len(pairs)} tradeable crypto pairs")
        return pairs

    def get_account_activities(
        self, 
        activity_types: str = None,
        date: str = None,
        after: str = None,
        until: str = None,
        direction: str = 'desc',
        page_size: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get account activities with filtering.
        
        Activity types:
        - FILL: Order fills
        - CFEE: Crypto fees
        - FEE: Other fees
        - DIV: Dividends
        - TRANS: Transfers
        - etc.
        
        Args:
            activity_types: Comma-separated activity types (e.g., 'FILL,CFEE')
            date: Filter to specific date (YYYY-MM-DD)
            after: Filter after this datetime
            until: Filter until this datetime
            direction: 'asc' or 'desc'
            page_size: Max results (max 100)
        """
        params = {
            'direction': direction,
            'page_size': page_size
        }
        
        if activity_types:
            params['activity_types'] = activity_types
        if date:
            params['date'] = date
        if after:
            params['after'] = after
        if until:
            params['until'] = until
        
        result = self._request("GET", "/v2/account/activities", params=params)
        return result if isinstance(result, list) else []

    def get_crypto_fees(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get crypto fee activities (CFEE) for the specified period.
        
        Returns list of fee records with qty, price, symbol.
        """
        from datetime import datetime, timedelta
        
        after = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        return self.get_account_activities(
            activity_types='CFEE,FEE',
            after=after,
            page_size=100
        )

    def get_trading_volume(self, days: int = 30) -> Dict[str, Any]:
        """
        Calculate trading volume over the specified period.
        
        Returns:
        - total_volume_usd: Total traded value
        - trade_count: Number of trades
        - by_symbol: Volume breakdown by symbol
        - fee_tier: Estimated fee tier based on volume
        """
        from datetime import datetime, timedelta
        
        after = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        fills = self.get_account_activities(
            activity_types='FILL',
            after=after,
            page_size=100
        )
        
        total_volume = 0.0
        by_symbol: Dict[str, float] = {}
        
        for fill in fills:
            qty = float(fill.get('qty', 0) or 0)
            price = float(fill.get('price', 0) or 0)
            symbol = fill.get('symbol', 'UNKNOWN')
            
            volume = qty * price
            total_volume += volume
            by_symbol[symbol] = by_symbol.get(symbol, 0) + volume
        
        # Estimate fee tier
        fee_tier = 1
        tier_thresholds = [0, 100_000, 500_000, 1_000_000, 10_000_000, 25_000_000, 50_000_000, 100_000_000]
        for i, threshold in enumerate(tier_thresholds):
            if total_volume >= threshold:
                fee_tier = i + 1
        
        return {
            'total_volume_usd': total_volume,
            'trade_count': len(fills),
            'by_symbol': by_symbol,
            'fee_tier': min(fee_tier, 8),
            'period_days': days
        }

    def get_orderbook(self, symbol: str) -> Dict[str, Any]:
        """
        Get real-time orderbook for a crypto symbol.
        
        Returns:
        - a: Ask array [{p: price, s: size}, ...]
        - b: Bid array [{p: price, s: size}, ...]
        - t: Timestamp
        """
        symbol = self._normalize_pair_symbol(symbol) or symbol
        
        params = {'symbols': symbol}
        result = self._request(
            "GET",
            "/v1beta3/crypto/us/latest/orderbooks",
            params=params,
            base_url=self.data_url
        )
        
        orderbooks = result.get('orderbooks', result) if isinstance(result, dict) else {}
        return orderbooks.get(symbol, {})

    def get_crypto_orderbook(self, symbol: str, depth: Optional[int] = None) -> Dict[str, Any]:
        """Compatibility wrapper: return Alpaca crypto orderbook with standardized keys.

        - Fetches the full orderbook payload Alpaca provides (no server-side truncation).
        - If `depth` is provided, trims bids/asks client-side.

        Returns keys:
        - symbol, t (timestamp)
        - bids / asks (also includes original a/b)
        """
        resolved = self._normalize_pair_symbol(symbol) or symbol
        ob = self.get_orderbook(resolved) or {}

        asks = ob.get('a', []) or []
        bids = ob.get('b', []) or []

        # Trim client-side if requested
        if depth is not None:
            try:
                d = max(0, int(depth))
            except (TypeError, ValueError):
                d = 0
            if d > 0:
                asks = asks[:d]
                bids = bids[:d]

        # Standardize keys expected by other modules
        out: Dict[str, Any] = dict(ob)
        out['symbol'] = resolved
        out['asks'] = asks
        out['bids'] = bids
        return out

    def get_spread(self, symbol: str) -> Dict[str, float]:
        """
        Get current spread for a symbol.
        
        Returns:
        - bid: Best bid price
        - ask: Best ask price
        - mid: Midpoint price
        - spread_abs: Absolute spread (ask - bid)
        - spread_pct: Spread as percentage of mid
        """
        # Try orderbook first
        ob = self.get_orderbook(symbol)
        
        if ob:
            bids = ob.get('b', [])
            asks = ob.get('a', [])
            
            if bids and asks:
                bid = float(bids[0].get('p', 0) if isinstance(bids[0], dict) else bids[0][0])
                ask = float(asks[0].get('p', 0) if isinstance(asks[0], dict) else asks[0][0])
                
                if bid > 0 and ask > 0:
                    mid = (bid + ask) / 2
                    spread_abs = ask - bid
                    spread_pct = (spread_abs / mid) * 100 if mid > 0 else 0
                    
                    return {
                        'bid': bid,
                        'ask': ask,
                        'mid': mid,
                        'spread_abs': spread_abs,
                        'spread_pct': spread_pct
                    }
        
        # Fallback to quotes
        symbol = self._normalize_pair_symbol(symbol) or symbol
        quotes = self.get_latest_crypto_quotes([symbol])
        
        if symbol in quotes:
            q = quotes[symbol]
            bid = float(q.get('bp', 0) or 0)
            ask = float(q.get('ap', 0) or 0)
            
            if bid > 0 and ask > 0:
                mid = (bid + ask) / 2
                spread_abs = ask - bid
                spread_pct = (spread_abs / mid) * 100 if mid > 0 else 0
                
                return {
                    'bid': bid,
                    'ask': ask,
                    'mid': mid,
                    'spread_abs': spread_abs,
                    'spread_pct': spread_pct
                }
        
        return {'bid': 0, 'ask': 0, 'mid': 0, 'spread_abs': 0, 'spread_pct': 0}

    def estimate_trade_cost(
        self,
        symbol: str,
        side: str,
        quantity: float,
        fee_tier: int = 1
    ) -> Dict[str, Any]:
        """
        Estimate total cost for a trade including fees and spread.
        
        Args:
            symbol: Trading pair
            side: 'buy' or 'sell'
            quantity: Trade quantity
            fee_tier: Fee tier (1-8, default 1 = 25 bps taker)
        
        Returns:
            Complete cost breakdown
        """
        # Fee rates by tier (taker fees in bps)
        taker_bps = {1: 25, 2: 22, 3: 20, 4: 18, 5: 15, 6: 13, 7: 12, 8: 10}
        fee_pct = taker_bps.get(fee_tier, 25) / 10000
        
        spread_data = self.get_spread(symbol)
        
        if spread_data['mid'] <= 0:
            return {
                'error': f'Could not get price for {symbol}',
                'notional': 0,
                'fee_pct': fee_pct,
                'fee_usd': 0,
                'spread_cost_pct': 0,
                'spread_cost_usd': 0,
                'total_cost_pct': fee_pct,
                'total_cost_usd': 0
            }
        
        # Execution price depends on side
        if side.lower() == 'buy':
            exec_price = spread_data['ask']
        else:
            exec_price = spread_data['bid']
        
        notional = quantity * exec_price
        fee_usd = notional * fee_pct
        
        # Spread cost (half spread per side)
        spread_cost_pct = (spread_data['spread_pct'] / 2) / 100
        spread_cost_usd = notional * spread_cost_pct
        
        total_cost_pct = fee_pct + spread_cost_pct
        total_cost_usd = fee_usd + spread_cost_usd
        
        return {
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'exec_price': exec_price,
            'mid_price': spread_data['mid'],
            'notional': notional,
            'fee_pct': fee_pct,
            'fee_usd': fee_usd,
            'fee_tier': fee_tier,
            'spread_pct': spread_data['spread_pct'],
            'spread_cost_pct': spread_cost_pct,
            'spread_cost_usd': spread_cost_usd,
            'total_cost_pct': total_cost_pct,
            'total_cost_usd': total_cost_usd
        }

    def get_full_account_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive account summary with all relevant data.
        
        Returns complete account state for cost tracking.
        """
        account = self.get_account()
        positions = self.get_positions()
        volume = self.get_trading_volume(days=30)
        recent_fees = self.get_crypto_fees(days=7)
        
        # Sum up fees
        total_fees_7d = sum(abs(float(f.get('qty', 0) or 0) * float(f.get('price', 0) or 0)) for f in recent_fees)
        
        return {
            'account': {
                'id': account.get('id'),
                'status': account.get('status'),
                'cash': float(account.get('cash', 0) or 0),
                'portfolio_value': float(account.get('portfolio_value', 0) or 0),
                'equity': float(account.get('equity', 0) or 0),
                'buying_power': float(account.get('buying_power', 0) or 0),
                'crypto_buying_power': float(account.get('non_marginable_buying_power', 0) or 0)
            },
            'positions': [{
                'symbol': p.get('symbol'),
                'qty': float(p.get('qty', 0) or 0),
                'avg_entry_price': float(p.get('avg_entry_price', 0) or 0),
                'market_value': float(p.get('market_value', 0) or 0),
                'unrealized_pl': float(p.get('unrealized_pl', 0) or 0),
                'unrealized_plpc': float(p.get('unrealized_plpc', 0) or 0)
            } for p in positions] if isinstance(positions, list) else [],
            'trading_volume': volume,
            'fees_7d': {
                'total_usd': total_fees_7d,
                'count': len(recent_fees)
            },
            'fee_tier': volume.get('fee_tier', 1)
        }

    # ═════════════════════════════════════════════════════════════════════=
    # MARKET DATA HUB INTEGRATION (Phase 2)
    # ═════════════════════════════════════════════════════════════════════=

    def start_market_data_hub(self):
        """Start the MarketDataHub prefetching service."""
        if self._market_data_hub:
            try:
                from market_data_hub import start_market_data_hub
                start_market_data_hub(self)
                logger.info("MarketDataHub started for Alpaca client")
            except Exception as e:
                logger.error(f"Failed to start MarketDataHub: {e}")

    def stop_market_data_hub(self):
        """Stop the MarketDataHub prefetching service."""
        try:
            from market_data_hub import stop_market_data_hub
            stop_market_data_hub()
            logger.info("MarketDataHub stopped")
        except Exception as e:
            logger.error(f"Failed to stop MarketDataHub: {e}")

    def get_market_data_hub_stats(self) -> Dict[str, Any]:
        """Get MarketDataHub statistics."""
        if self._market_data_hub:
            return self._market_data_hub.get_stats()
        return {"error": "MarketDataHub not available"}

    def get_global_rate_budget_stats(self) -> Dict[str, Any]:
        """Get GlobalRateBudget statistics."""
        if self._global_rate_budget:
            return self._global_rate_budget.get_stats()
        return {"error": "GlobalRateBudget not available"}