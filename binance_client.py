import os, time, hmac, hashlib, requests, json
from decimal import Decimal, InvalidOperation, ROUND_DOWN, ROUND_UP
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass
from typing import Dict, Any, Set, List, Optional, Tuple

# Rate limiting utilities (TokenBucket, TTLCache)
try:
    from rate_limiter import TokenBucket, TTLCache
except Exception:
    TokenBucket = None
    TTLCache = None

BINANCE_MAINNET = "https://api.binance.com"
BINANCE_TESTNET = "https://testnet.binance.vision"

# 🇬🇧 UK Binance Restrictions (FCA regulated)
# These are tokens/features restricted for UK retail accounts
UK_RESTRICTED_TOKENS = {
    # Derivatives/Leveraged tokens (banned for UK retail)
    "BTCDOWN", "BTCUP", "ETHDOWN", "ETHUP", "BNBDOWN", "BNBUP",
    "XRPDOWN", "XRPUP", "DOTDOWN", "DOTUP", "EOSDOWN", "EOSUP",
    "TRXDOWN", "TRXUP", "LINKDOWN", "LINKUP", "ADAUP", "ADADOWN",
    "SXPDOWN", "SXPUP", "UNIDOWN", "UNIUP", "FILDOWN", "FILUP",
    "AAVEDOWN", "AAVEUP", "SUSHIDOWN", "SUSHIUP", "1INCHDOWN", "1INCHUP",
    # Stock tokens (delisted for UK)
    "TSLA", "COIN", "AAPL", "MSFT", "GOOGL", "AMZN", "MSTR",
    # Some stablecoins have restrictions
    "BUSD",  # Deprecated
}

# Features not available for UK accounts
UK_RESTRICTED_FEATURES = {
    "margin",      # No margin trading
    "futures",     # No derivatives
    "options",     # No options
    "leveraged",   # No leveraged tokens
}

class BinanceClient:
    def __init__(self):
        # Support common env var aliases from TS/Node side as well
        self.api_key = os.getenv("BINANCE_API_KEY") or os.getenv("BINANCE_KEY") or ""
        self.api_secret = os.getenv("BINANCE_API_SECRET") or os.getenv("BINANCE_SECRET") or ""
        self.use_testnet = (os.getenv("BINANCE_USE_TESTNET") or os.getenv("BINANCE_TESTNET") or "false").lower() == "true"
        self.dry_run = os.getenv("BINANCE_DRY_RUN", "false").lower() == "true"
        
        # 🇬🇧 UK Mode - Enable restrictions for FCA-regulated accounts
        self.uk_mode = os.getenv("BINANCE_UK_MODE", "true").lower() == "true"
        
        # Only require API keys if NOT in dry-run mode
        if not self.dry_run and (not self.api_key or not self.api_secret):
            raise ValueError("Missing BINANCE_API_KEY or BINANCE_API_SECRET in environment")
        
        self.base = BINANCE_TESTNET if self.use_testnet else BINANCE_MAINNET
        self.session = requests.Session()
        
        # Configure HTTPAdapter with connection pooling and SSL/TLS stability improvements
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
            backoff_factor=1
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=10,
            pool_block=False
        )
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        if self.api_key:
            self.session.headers.update({"X-MBX-APIKEY": self.api_key})
        
        # Cache allowed pairs for UK mode
        self._allowed_pairs_cache: Set[str] = set()
        self._cache_timestamp: float = 0
        self._symbol_filters_cache: dict[str, dict[str, float]] = {}
        
        # 🇬🇧 Cache UK restricted symbols to skip known-bad symbols proactively
        self._uk_restricted_symbols_cache: Set[str] = set()
        self._uk_restriction_cache_timestamp: float = 0
        
        # Server time offset for clock sync (fixes Windows clock drift)
        self._time_offset_ms: int = 0
        self._time_sync_timestamp: float = 0
        self._sync_server_time()  # Auto-sync on init

        # Token bucket rate limiter for Binance and request/quote caching
        try:
            rate = float(os.getenv('BINANCE_RATE_PER_SECOND', '0.2'))  # Even more conservative: 0.2 req/sec
        except Exception:
            rate = 0.2  # Very conservative default to avoid bans
        try:
            burst = float(os.getenv('BINANCE_BURST_CAPACITY', str(max(1, int(rate)))))
        except Exception:
            burst = max(1, rate)
        self._rate_limiter = TokenBucket(rate=rate, capacity=burst) if TokenBucket else None
        self._request_cache = TTLCache(default_ttl=float(os.getenv('BINANCE_EXCHANGE_CACHE_TTL', '1.0'))) if TTLCache else None
        self.max_retries = int(os.getenv('BINANCE_RETRY_COUNT', '2'))

    @staticmethod
    def _norm(symbol: str) -> str:
        """Normalize symbol for Binance API: strip '/' separators.
        E.g. 'XRP/USDC' -> 'XRPUSDC', 'BTCUSDT' -> 'BTCUSDT'.
        """
        return symbol.replace('/', '') if symbol else symbol
    
    def _sync_server_time(self) -> None:
        """Sync with Binance server time to handle local clock drift."""
        try:
            local_time_before = int(time.time() * 1000)
            r = self.session.get(f"{self.base}/api/v3/time", timeout=5)
            local_time_after = int(time.time() * 1000)
            
            if r.status_code == 200:
                server_time = r.json().get('serverTime', local_time_before)
                # Account for network latency (use midpoint)
                local_time_mid = (local_time_before + local_time_after) // 2
                self._time_offset_ms = server_time - local_time_mid
                self._time_sync_timestamp = time.time()
                
                if abs(self._time_offset_ms) > 1000:
                    print(f"   [Binance] Clock offset detected: {self._time_offset_ms}ms - auto-correcting")
        except Exception as e:
            print(f"   [Binance] Time sync failed: {e} - using local time")
            self._time_offset_ms = 0
    
    def _get_server_timestamp(self) -> int:
        """Get current timestamp adjusted for server time offset."""
        # Re-sync every 5 minutes to handle drift
        if time.time() - self._time_sync_timestamp > 300:
            self._sync_server_time()
        return int(time.time() * 1000) + self._time_offset_ms

    def _sign(self, params: Dict[str, Any]) -> str:
        query = "&".join(f"{k}={params[k]}" for k in params)
        signature = hmac.new(self.api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()
        return signature

    def is_uk_restricted_symbol(self, symbol: str) -> bool:
        """Check if a symbol contains UK-restricted tokens."""
        if not self.uk_mode:
            return False
        symbol_upper = symbol.upper()
        for token in UK_RESTRICTED_TOKENS:
            if token in symbol_upper:
                return True
        return False

    def get_allowed_pairs_uk(self, force_refresh: bool = False) -> Set[str]:
        """Get list of pairs allowed for UK accounts based on Trade Groups.
        
        Caches results for 1 hour to avoid repeated API calls.
        """
        if not self.uk_mode:
            return set()  # No filtering needed
        
        # Return cache if fresh (< 1 hour)
        if not force_refresh and self._allowed_pairs_cache and (time.time() - self._cache_timestamp) < 3600:
            return self._allowed_pairs_cache
        
        try:
            # Get account trade groups
            account = self.account()
            permissions = account.get('permissions', [])
            trade_groups = {p for p in permissions if p.startswith('TRD_GRP_')}
            
            if not trade_groups:
                print("⚠️  UK Account: No TRD_GRP permissions found - trading may be restricted")
                return set()
            
            # Get exchange info and filter by trade groups
            info = self.exchange_info()
            symbols = info.get('symbols', [])
            
            allowed = set()
            for sym in symbols:
                if sym.get('status') != 'TRADING':
                    continue
                if not sym.get('isSpotTradingAllowed', False):
                    continue
                
                # Check if symbol's permission sets match our trade groups
                permission_sets = sym.get('permissionSets') or []
                for perm_set in permission_sets:
                    if trade_groups.intersection({p for p in perm_set if p.startswith('TRD_GRP_')}):
                        symbol_name = sym.get('symbol', '')
                        # Also filter out known restricted tokens
                        if not self.is_uk_restricted_symbol(symbol_name):
                            allowed.add(symbol_name)
                        break
            
            self._allowed_pairs_cache = allowed
            self._cache_timestamp = time.time()
            print(f"🇬🇧 UK Mode: {len(allowed)} tradeable pairs loaded")
            return allowed
            
        except Exception as e:
            print(f"⚠️  Failed to load UK allowed pairs: {e}")
            return set()

    def can_trade_symbol(self, symbol: str) -> tuple[bool, str]:
        """Check if a symbol can be traded (considering UK restrictions).
        
        Returns (can_trade: bool, reason: str)
        """
        if not self.uk_mode:
            return True, "OK"
        
        # Check static blacklist first
        if self.is_uk_restricted_symbol(symbol):
            return False, f"🇬🇧 UK Restricted: Contains banned token"
        
        # Check dynamic allowed list (based on account's trade groups)
        allowed = self.get_allowed_pairs_uk()
        if allowed and symbol.upper() not in allowed:
            return False, f"🇬🇧 UK Restricted: Not in account's permitted trade groups"
        
        return True, "OK"

    def _do_request(self, method: str, path: str, params: Dict[str, Any] = None, data: Dict[str, Any] = None, timeout: int = 15):
        """Internal request helper: respects rate limiter, handles 429 Retry-After and retries."""
        url = f"{self.base}{path}"
        # Respect rate limiter
        if getattr(self, '_rate_limiter', None):
            try:
                self._rate_limiter.wait()
            except Exception:
                pass

        for attempt in range(self.max_retries + 1):
            # For signed POST requests, params go in query string, not body
            resp = self.session.request(method, url, params=params, data=data, timeout=timeout)
            if resp.status_code == 429:
                # Metric: API 429
                try:
                    from metrics import api_429_counter
                    api_429_counter.inc(1, exchange='binance', endpoint=path)
                except Exception:
                    pass

                retry_after = resp.headers.get('Retry-After')
                try:
                    wait_time = float(retry_after) if retry_after else 2 ** attempt
                except Exception:
                    wait_time = 2 ** attempt
                time.sleep(min(max(wait_time, 0.1), 10))
                if attempt < self.max_retries:
                    continue
            if resp.status_code != 200:
                # 🇬🇧 UK Mode: Cache -2010 errors (symbol not permitted)
                if self.uk_mode and resp.status_code == 400:
                    try:
                        error_data = resp.json()
                        if error_data.get('code') == -2010:
                            # Extract symbol from params and cache it
                            symbol = params.get('symbol') if params else None
                            if symbol:
                                self._uk_restricted_symbols_cache.add(symbol)
                                self._uk_restriction_cache_timestamp = time.time()
                                print(f"   🇬🇧 Cached UK restricted symbol: {symbol}")
                    except Exception:
                        pass
                raise RuntimeError(f"Binance error {resp.status_code}: {resp.text}")
            return resp.json()
        raise RuntimeError("Binance request failed after retries")

    def _signed_request(self, method: str, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        params["timestamp"] = self._get_server_timestamp()  # Use synced timestamp
        params["recvWindow"] = 60000  # Increased to 60 seconds for network latency
        signature = self._sign(params)
        params["signature"] = signature
        return self._do_request(method, path, params=params)

    def ping(self) -> bool:
        try:
            r = self.session.get(f"{self.base}/api/v3/ping", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def server_time(self) -> Dict[str, Any]:
        r = self.session.get(f"{self.base}/api/v3/time")
        return r.json()

    def exchange_info(self, symbol: str = None) -> Dict[str, Any]:
        params = {}
        key = f"exchange_info::{symbol or 'all'}"
        if self._request_cache:
            cached = self._request_cache.get(key)
            if cached is not None:
                return cached
        if symbol:
            params["symbol"] = symbol
        # Use _do_request to respect rate limits
        r = self._do_request("GET", "/api/v3/exchangeInfo", params=params)
        if self._request_cache:
            try:
                self._request_cache.set(key, r)
            except Exception:
                pass
        return r

    # Compatibility alias for callers expecting get_exchange_info
    def get_exchange_info(self, symbol: str = None) -> Dict[str, Any]:
        return self.exchange_info(symbol)

    def account(self) -> Dict[str, Any]:
        return self._signed_request("GET", "/api/v3/account", {})

    def get_free_balance(self, asset: str) -> float:
        acct = self.account()
        for bal in acct.get("balances", []):
            if bal["asset"] == asset:
                return float(bal["free"])
        return 0.0

    def get_balance(self) -> Dict[str, float]:
        """Compatibility: return free balances as {asset: amount}."""
        balances: Dict[str, float] = {}
        try:
            acct = self.account()
            for bal in acct.get("balances", []):
                asset = bal.get("asset")
                if not asset:
                    continue
                try:
                    free_amt = float(bal.get("free", 0) or 0)
                except Exception:
                    free_amt = 0.0
                if free_amt > 0:
                    balances[asset] = free_amt
        except Exception:
            return {}
        return balances

    def _format_order_value(self, value: float | str | Decimal | None) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            return value
        try:
            dec_value = Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise ValueError(f"Invalid order value: {value}") from exc
        
        # Use high precision to avoid rounding errors from default 'f' (6 decimals)
        formatted = "{:.20f}".format(dec_value)
        if '.' in formatted:
            formatted = formatted.rstrip('0').rstrip('.')
        return formatted
        return formatted or '0'

    def place_market_order(self, symbol: str, side: str, quantity: float | str | Decimal | None = None, quote_qty: float | str | Decimal | None = None) -> Dict[str, Any]:
        symbol = self._norm(symbol)
        # 🇬🇧 UK Mode: Check restrictions before attempting trade
        # Also check cached restricted symbols to skip known-bad symbols
        if self.uk_mode:
            # Check cache first (even for SELLs to avoid wasted API calls)
            if symbol in self._uk_restricted_symbols_cache:
                return {
                    "rejected": True,
                    "symbol": symbol,
                    "side": side,
                    "reason": "This symbol is not permitted for this account (cached).",
                    "uk_restricted": True
                }
            # For BUYs, do full validation
            if side.upper() != 'SELL':
                can_trade, reason = self.can_trade_symbol(symbol)
                if not can_trade:
                    # Cache this restriction
                    self._uk_restricted_symbols_cache.add(symbol)
                    self._uk_restriction_cache_timestamp = time.time()
                    return {
                        "rejected": True,
                        "symbol": symbol,
                        "side": side,
                        "reason": reason,
                        "uk_restricted": True
                    }
        
        # 🚨 CRITICAL: Verify balance before SELL orders to prevent insufficient funds errors
        if side.upper() == 'SELL' and quantity:
            try:
                # Extract base asset from symbol (e.g., "BTC" from "BTCUSDT")
                base_asset = symbol.replace('USDT', '').replace('USDC', '').replace('BUSD', '').replace('BTC', '').replace('BNB', '').replace('ETH', '')
                if not base_asset:
                    # Fallback: guess base asset is the first 3-4 chars
                    base_asset = symbol[:4] if len(symbol) > 4 else symbol[:3]
                
                # Get actual balance from account
                actual_balance = self.get_free_balance(base_asset)
                requested_qty = float(quantity)
                
                if actual_balance < requested_qty:
                    return {
                        "rejected": True,
                        "symbol": symbol,
                        "side": side,
                        "reason": f"Insufficient funds to sell {requested_qty:.8f} {base_asset}. Have {actual_balance:.8f}",
                        "balance_check": True,
                        "actual_balance": actual_balance,
                        "requested_qty": requested_qty
                    }
            except Exception as e:
                # Don't block order on balance check failure, but log it
                print(f"   ⚠️ Balance check warning: {e}")
        
        if self.dry_run:
            return {"dryRun": True, "symbol": symbol, "side": side, "quantity": quantity, "quoteQty": quote_qty}
        
        params = {"symbol": symbol, "side": side.upper(), "type": "MARKET", "newOrderRespType": "FULL"}
        filters = {}
        try:
            filters = self.get_symbol_filters(symbol)
        except Exception:
            filters = {}
        min_notional = float(filters.get('min_notional', 0.0) or 0.0)
        if quantity:
            # Adjust quantity to match symbol's lot size and precision
            adjusted_qty = self.adjust_quantity(symbol, float(quantity))
            if adjusted_qty <= 0:
                return {
                    "rejected": True,
                    "symbol": symbol,
                    "side": side,
                    "reason": f"Quantity {quantity} adjusts to {adjusted_qty} (below min qty)",
                    "uk_restricted": False
                }
            if min_notional > 0:
                try:
                    price_info = self.best_price(symbol)
                    price = float(price_info.get("price", 0))
                except Exception:
                    price = 0.0
                if price > 0:
                    notional = adjusted_qty * price
                    if notional < min_notional:
                        return {
                            "rejected": True,
                            "error": "min_notional",
                            "symbol": symbol,
                            "side": side,
                            "reason": f"Notional {notional:.8f} < minNotional {min_notional}",
                            "uk_restricted": False
                        }
            params["quantity"] = self._format_order_value(adjusted_qty)
        elif quote_qty:
            # Adjust quote quantity to match symbol's quote precision
            adjusted_quote = self.adjust_quote_qty(symbol, float(quote_qty))
            if adjusted_quote <= 0:
                return {
                    "rejected": True,
                    "error": "min_notional",
                    "symbol": symbol,
                    "side": side,
                    "reason": f"Quote amount {quote_qty} adjusts to {adjusted_quote}",
                    "uk_restricted": False
                }
            if min_notional > 0 and adjusted_quote < min_notional:
                return {
                    "rejected": True,
                    "error": "min_notional",
                    "symbol": symbol,
                    "side": side,
                    "reason": f"Notional {adjusted_quote:.8f} < minNotional {min_notional}",
                    "uk_restricted": False
                }
            params["quoteOrderQty"] = self._format_order_value(adjusted_quote)
        else:
            raise ValueError("Must provide either quantity or quote_qty")
            
        response = self._signed_request("POST", "/api/v3/order", params)

        # Attach fill-derived metadata for validation
        fills = response.get("fills") or []
        total_qty = 0.0
        total_cost = 0.0
        total_fees_quote = 0.0

        # Try to infer quote asset from common suffixes
        quote_asset = None
        for q in ("USDT", "USDC", "BUSD", "FDUSD", "TUSD", "USD", "EUR", "GBP", "BTC", "BNB", "ETH"):
            if symbol.endswith(q):
                quote_asset = q
                break

        for f in fills:
            try:
                qty = float(f.get("qty", 0) or 0)
                price = float(f.get("price", 0) or 0)
                commission = float(f.get("commission", 0) or 0)
                commission_asset = str(f.get("commissionAsset", "") or "").upper()
            except Exception:
                qty = 0.0
                price = 0.0
                commission = 0.0
                commission_asset = ""
            if qty > 0 and price > 0:
                total_qty += qty
                total_cost += qty * price
            if commission > 0 and quote_asset and commission_asset == quote_asset:
                total_fees_quote += commission

        avg_fill_price = (total_cost / total_qty) if total_qty > 0 else None
        response["avg_fill_price"] = avg_fill_price
        response["fees"] = total_fees_quote
        response["fills_verified"] = True if fills else False

        return response

    def get_symbol_filters(self, symbol: str) -> Dict[str, float]:
        symbol = symbol.upper()
        if symbol in self._symbol_filters_cache:
            return self._symbol_filters_cache[symbol]

        info = self.exchange_info(symbol=symbol)
        entry = None
        if isinstance(info, dict):
            symbols = info.get('symbols', [])
            if symbols:
                entry = symbols[0]
        if entry is None:
            raise RuntimeError(f"Failed to load symbol info for {symbol}")

        filters = entry.get('filters', [])
        def _find(filter_type: str) -> Dict[str, Any]:
            for f in filters:
                if f.get('filterType') == filter_type:
                    return f
            return {}

        lot = _find('LOT_SIZE')
        market_lot = _find('MARKET_LOT_SIZE')
        min_notional = _find('MIN_NOTIONAL') or _find('NOTIONAL')

        def _safe_float(value: str | float | None, fallback: float) -> float:
            try:
                parsed = float(value)
                if parsed > 0:
                    return parsed
            except (TypeError, ValueError):
                pass
            return fallback

        step_size = _safe_float(market_lot.get('stepSize'), 0.0) if market_lot else 0.0
        if step_size <= 0:
            step_size = _safe_float(lot.get('stepSize') if lot else None, 0.0001)

        min_qty = _safe_float(market_lot.get('minQty') if market_lot else None, 0.0)
        if min_qty <= 0:
            min_qty = _safe_float(lot.get('minQty') if lot else None, 0.0)

        max_qty = _safe_float(market_lot.get('maxQty') if market_lot else None, 0.0)
        if max_qty <= 0:
            max_qty = _safe_float(lot.get('maxQty') if lot else None, 0.0)

        min_notional_val = _safe_float((min_notional or {}).get('minNotional'), 0.0)

        base_precision = int(entry.get('baseAssetPrecision', 8))
        quote_precision = int(entry.get('quoteAssetPrecision', entry.get('quotePrecision', 8)))

        data = {
            'step_size': step_size,
            'min_qty': min_qty,
            'max_qty': max_qty,
            'min_notional': min_notional_val,
            'base_precision': base_precision,
            'quote_precision': quote_precision,
            'base_asset': entry.get('baseAsset'),
            'quote_asset': entry.get('quoteAsset'),
        }
        self._symbol_filters_cache[symbol] = data
        return data

    def adjust_quantity(self, symbol: str, quantity: float) -> float:
        filters = self.get_symbol_filters(symbol)
        qty_dec = Decimal(str(quantity))
        step = Decimal(str(filters.get('step_size', 0.0))) if filters.get('step_size') else Decimal('0')
        if step > 0:
            qty_dec = (qty_dec // step) * step

        precision = int(filters.get('base_precision', 8))
        try:
            scale = Decimal(1).scaleb(-precision)
            qty_dec = qty_dec.quantize(scale, rounding=ROUND_DOWN)
        except (InvalidOperation, ValueError):
            pass

        min_qty = Decimal(str(filters.get('min_qty', 0.0)))
        if qty_dec < min_qty:
            return 0.0

        max_qty_val = filters.get('max_qty', 0.0)
        if max_qty_val:
            max_qty = Decimal(str(max_qty_val))
            if qty_dec > max_qty:
                qty_dec = max_qty

        return float(qty_dec)

    def adjust_quote_qty(self, symbol: str, quote_qty: float) -> float:
        """Adjust quoteOrderQty to match the symbol's quote precision for Binance."""
        try:
            filters = self.get_symbol_filters(symbol)
            precision = int(filters.get('quote_precision', 8))
            # Binance typically accepts 2 decimal places for most quote currencies
            # But use the exchange's quote_precision as guidance
            # Clamp to max 8 decimals to be safe
            precision = min(precision, 8)
            qty_dec = Decimal(str(quote_qty))
            scale = Decimal(1).scaleb(-precision)
            qty_dec = qty_dec.quantize(scale, rounding=ROUND_DOWN)
            return float(qty_dec)
        except Exception:
            # Fallback: round to 2 decimal places
            return round(quote_qty, 2)

    def best_price(self, symbol: str, timeout: float = 3.0) -> Dict[str, Any]:
        try:
            r = self.session.get(f"{self.base}/api/v3/ticker/price", params={"symbol": symbol}, timeout=timeout)
            return r.json()
        except Exception:
            return {}
    
    def convert_to_quote(self, asset: str, amount: float, quote: str) -> float:
        """Convert an asset amount into quote using spot ticker price if available.
        
        Supports multi-hop conversion via USDT for pairs without direct trading pairs.
        """
        asset = asset.upper()
        quote = quote.upper()
        
        if asset == quote:
            return amount
        
        # Skip conversion for dust amounts (< $0.01 worth)
        if amount < 0.00001:
            return 0.0
        
        # Try direct pair first
        pair = f"{asset}{quote}"
        inv_pair = f"{quote}{asset}"
        try:
            price_info = self.best_price(pair, timeout=2.0)
            price = float(price_info.get("price", 0))
            if price > 0:
                return amount * price
        except Exception:
            pass
        try:
            price_info = self.best_price(inv_pair, timeout=2.0)
            price = float(price_info.get("price", 0))
            if price > 0:
                return amount / price
        except Exception:
            pass
        
        # Multi-hop conversion via USDT or USDC
        for pivot in ['USDT', 'USDC', 'BTC']:
            if pivot in (asset, quote):
                continue
            
            # asset -> pivot
            asset_to_pivot = 0.0
            try:
                pair1 = f"{asset}{pivot}"
                price_info = self.best_price(pair1, timeout=2.0)
                price = float(price_info.get("price", 0))
                if price > 0:
                    asset_to_pivot = amount * price
            except Exception:
                pass
            if asset_to_pivot <= 0:
                try:
                    pair1_inv = f"{pivot}{asset}"
                    price_info = self.best_price(pair1_inv, timeout=2.0)
                    price = float(price_info.get("price", 0))
                    if price > 0:
                        asset_to_pivot = amount / price
                except Exception:
                    pass
            
            if asset_to_pivot <= 0:
                continue
            
            # pivot -> quote
            pivot_to_quote = 0.0
            try:
                pair2 = f"{pivot}{quote}"
                price_info = self.best_price(pair2, timeout=2.0)
                price = float(price_info.get("price", 0))
                if price > 0:
                    pivot_to_quote = asset_to_pivot * price
            except Exception:
                pass
            if pivot_to_quote <= 0:
                try:
                    pair2_inv = f"{quote}{pivot}"
                    price_info = self.best_price(pair2_inv, timeout=2.0)
                    price = float(price_info.get("price", 0))
                    if price > 0:
                        pivot_to_quote = asset_to_pivot / price
                except Exception:
                    pass
            
            if pivot_to_quote > 0:
                return pivot_to_quote
        
        return 0.0

    def compute_order_fees_in_quote(self, order: Dict[str, Any], primary_quote: str) -> float:
        """Sum commissions from FULL order response into the target quote asset.
        Falls back to 0 if fills/commission are missing.
        """
        fills = order.get("fills") or []
        total_quote = 0.0
        for f in fills:
            try:
                commission = float(f.get("commission", 0) or 0)
                commission_asset = str(f.get("commissionAsset", "")).upper()
            except Exception:
                commission = 0.0
                commission_asset = ""
            if commission <= 0:
                continue
            if commission_asset == primary_quote.upper():
                total_quote += commission
            else:
                converted = self.convert_to_quote(commission_asset, commission, primary_quote)
                total_quote += converted
        return total_quote
    
    def get_ticker_price(self, symbol: str) -> Optional[Dict[str, str]]:
        """Get current price for a symbol."""
        symbol = self._norm(symbol)
        try:
            r = self.session.get(f"{self.base}/api/v3/ticker/price", params={"symbol": symbol}, timeout=5)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return None

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Unified ticker interface (symbol, price, bid, ask, last).
        
        Wraps get_24h_ticker to provide a richer object, but falls back
        to get_ticker_price if needed.
        """
        symbol = self._norm(symbol)
        try:
            # get_24h_ticker provides bid/ask, which is preferred
            ticker_24h = self.get_24h_ticker(symbol)
            if ticker_24h and 'lastPrice' in ticker_24h:
                price = float(ticker_24h['lastPrice'])
                bid = float(ticker_24h.get('bidPrice', 0))
                ask = float(ticker_24h.get('askPrice', 0))
                return {
                    "symbol": symbol,
                    "price": price,
                    "last": price,
                    "bid": bid if bid > 0 else price,
                    "ask": ask if ask > 0 else price,
                }
        except Exception:
            # Fallback to the simpler price-only endpoint if 24h fails
            pass

        try:
            ticker_price = self.get_ticker_price(symbol)
            if ticker_price and 'price' in ticker_price:
                price = float(ticker_price['price'])
                return {
                    "symbol": symbol,
                    "price": price,
                    "last": price,
                    "bid": price,
                    "ask": price,
                }
        except Exception:
            pass
        
        return {}

    def get_24h_tickers(self) -> list:
        """Get all 24h ticker stats for commando scanning 🦆⚔️
        
        In dry-run mode, fallback to mainnet public API if testnet fails.
        """
        # Try configured endpoint first
        try:
            r = self.session.get(f"{self.base}/api/v3/ticker/24hr", timeout=10)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        
        # In dry-run mode, fallback to mainnet public API (no auth needed)
        if self.dry_run:
            try:
                import requests as req
                r = req.get(f"{BINANCE_MAINNET}/api/v3/ticker/24hr", timeout=10)
                if r.status_code == 200:
                    return r.json()
            except Exception as e:
                raise RuntimeError(f"Failed to get 24h tickers (dry-run fallback failed): {e}")
        
        raise RuntimeError(f"Failed to get 24h tickers: {r.status_code if 'r' in dir() else 'no response'}")
    
    def get_24h_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get 24h ticker stats for specific symbol
        
        In dry-run mode, fallback to mainnet public API if testnet fails.
        """
        symbol = self._norm(symbol)
        # Try configured endpoint first
        try:
            r = self.session.get(f"{self.base}/api/v3/ticker/24hr", params={"symbol": symbol}, timeout=10)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        
        # In dry-run mode, fallback to mainnet public API
        if self.dry_run:
            try:
                import requests as req
                r = req.get(f"{BINANCE_MAINNET}/api/v3/ticker/24hr", params={"symbol": symbol}, timeout=10)
                if r.status_code == 200:
                    return r.json()
            except Exception as e:
                raise RuntimeError(f"Failed to get ticker for {symbol} (dry-run fallback failed): {e}")
        
        raise RuntimeError(f"Failed to get ticker for {symbol}: {r.status_code if 'r' in dir() else 'no response'}")

    def get_klines(self, symbol: str, interval: str = "15m", limit: int = 100) -> List[Dict]:
        """Get historical klines/candlestick data for market context.
        
        Returns list of OHLCV candles for technical analysis.
        Essential for 24h historical context on startup.
        
        Args:
            symbol: Trading pair (e.g., BTCUSDC)
            interval: Candle interval (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Number of candles (max 1000)
            
        Returns:
            List of dicts with open, high, low, close, volume, timestamp
        """
        try:
            params = {"symbol": symbol, "interval": interval, "limit": min(limit, 1000)}
            r = self.session.get(f"{self.base}/api/v3/klines", params=params, timeout=10)
            if r.status_code == 200:
                raw = r.json()
                # Parse Binance kline format into dict
                return [{
                    'timestamp': k[0],
                    'open': float(k[1]),
                    'high': float(k[2]),
                    'low': float(k[3]),
                    'close': float(k[4]),
                    'volume': float(k[5]),
                    'close_time': k[6],
                    'quote_volume': float(k[7]),
                    'trades': int(k[8]),
                    'taker_buy_base': float(k[9]),
                    'taker_buy_quote': float(k[10])
                } for k in raw]
        except Exception:
            pass
        
        # Fallback to mainnet for dry-run
        if self.dry_run:
            try:
                params = {"symbol": symbol, "interval": interval, "limit": min(limit, 1000)}
                r = requests.get(f"{BINANCE_MAINNET}/api/v3/klines", params=params, timeout=10)
                if r.status_code == 200:
                    raw = r.json()
                    return [{
                        'timestamp': k[0],
                        'open': float(k[1]),
                        'high': float(k[2]),
                        'low': float(k[3]),
                        'close': float(k[4]),
                        'volume': float(k[5]),
                        'close_time': k[6],
                        'quote_volume': float(k[7]),
                        'trades': int(k[8]),
                        'taker_buy_base': float(k[9]),
                        'taker_buy_quote': float(k[10])
                    } for k in raw]
            except Exception as e:
                print(f"⚠️ Failed to get klines for {symbol}: {e}")
        return []
    
    def get_24h_historical(self, symbols: List[str] = None, interval: str = "1h") -> Dict[str, List[Dict]]:
        """Bootstrap 24h historical data for multiple symbols.
        
        Fetches 24 hours of historical candles for each symbol to establish
        market context before live trading begins.
        
        Args:
            symbols: List of symbols to fetch (default: top volume pairs)
            interval: Candle interval (default 1h = 24 candles per day)
            
        Returns:
            Dict mapping symbol -> list of OHLCV candles
        """
        if symbols is None:
            # Get top volume USDC pairs
            try:
                tickers = self.get_24h_tickers()
                usdc_pairs = [t for t in tickers if t['symbol'].endswith('USDC')]
                usdc_pairs.sort(key=lambda x: float(x.get('quoteVolume', 0)), reverse=True)
                symbols = [t['symbol'] for t in usdc_pairs[:20]]
            except Exception:
                symbols = ['BTCUSDC', 'ETHUSDC', 'SOLUSDC', 'BNBUSDC', 'XRPUSDC']
        
        historical_data = {}
        limit = 24 if interval == "1h" else 96  # 24h of 1h candles or 24h of 15m candles
        
        print(f"📊 Bootstrapping 24h historical data for {len(symbols)} symbols...")
        for symbol in symbols:
            try:
                klines = self.get_klines(symbol, interval, limit)
                if klines:
                    historical_data[symbol] = klines
            except Exception as e:
                print(f"   ⚠️ {symbol}: {e}")
        
        print(f"   ✅ Loaded {len(historical_data)} symbol histories")
        return historical_data

    def get_deposit_address(self, coin: str, network: str | None = None) -> Dict[str, Any]:
        """Retrieve deposit address for a given coin (and optional network).

        Note: Not available on testnet. Will raise if testnet flag is set.
        """
        if self.use_testnet:
            raise RuntimeError("Deposit addresses are not provided by Binance testnet; switch BINANCE_USE_TESTNET=false only after validation.")
        params: Dict[str, Any] = {"coin": coin}
        if network:
            params["network"] = network
        return self._signed_request("GET", "/sapi/v1/capital/deposit/address", params)

    # ── Simple Earn (Flexible) ──────────────────────────────────────────────
    def get_flexible_positions(self, asset: str = None) -> Dict[str, Any]:
        """Get Simple Earn flexible product positions."""
        params: Dict[str, Any] = {"size": 100}
        if asset:
            params["asset"] = asset
        return self._signed_request("GET", "/sapi/v1/simple-earn/flexible/position", params)

    def redeem_flexible(self, product_id: str, amount: float = None, redeem_all: bool = False) -> Dict[str, Any]:
        """Redeem from Simple Earn flexible product back to spot wallet.
        
        Args:
            product_id: The product ID from get_flexible_positions()
            amount: Amount to redeem (None = all)
            redeem_all: If True, redeem entire position
        """
        params: Dict[str, Any] = {"productId": product_id}
        if redeem_all:
            params["redeemAll"] = True
        elif amount is not None:
            params["amount"] = str(amount)
        else:
            params["redeemAll"] = True
        return self._signed_request("POST", "/sapi/v1/simple-earn/flexible/redeem", params)

    def get_my_trades(self, symbol: str, limit: int = 500, silent: bool = False) -> list:
        """Get trade history for a symbol.
        
        Returns list of trades with entry prices, quantities, fees etc.
        Used to calculate real cost basis for positions.
        
        Args:
            symbol: Trading pair symbol
            limit: Max trades to return
            silent: If True, suppress error messages for invalid symbols
        """
        params = {"symbol": symbol, "limit": limit}
        try:
            return self._signed_request("GET", "/api/v3/myTrades", params)
        except Exception as e:
            # Only print errors if not silent and not an "Invalid symbol" error
            if not silent and 'Invalid symbol' not in str(e):
                print(f"⚠️ Failed to get trade history for {symbol}: {e}")
            return []
    
    def get_all_my_trades(self, symbols: list = None, limit_per_symbol: int = 100) -> Dict[str, list]:
        """Get trade history for multiple symbols.
        
        Returns dict: {symbol: [trades]}
        """
        # 🔧 BINANCE VALID PAIRS: Only try quote currencies that Binance actually supports
        # Binance has very limited EUR/GBP support - only major pairs
        BINANCE_EUR_SUPPORTED = {'BTC', 'ETH', 'BNB', 'XRP', 'ADA', 'SOL', 'DOT', 'DOGE', 'SHIB', 'MATIC', 'LTC', 'AVAX', 'LINK', 'ATOM'}
        BINANCE_GBP_SUPPORTED = {'BTC', 'ETH', 'BNB', 'XRP', 'ADA', 'SOL', 'DOT', 'DOGE', 'LTC'}
        
        # Assets that should NEVER be used as base (stablecoins, earn products, etc.)
        SKIP_AS_BASE = {'USDC', 'USDT', 'BUSD', 'TUSD', 'FDUSD', 'EUR', 'GBP', 'USD', 
                        'LDUSDC', 'LDUSDT', 'LDBUSD', 'LDBNB', 'LDBTC', 'LDETH'}
        
        if not symbols:
            # Get symbols from current balances
            account = self.account()
            balances = account.get('balances', [])
            symbols = []
            for b in balances:
                if float(b.get('free', 0)) > 0 or float(b.get('locked', 0)) > 0:
                    asset = b['asset'].upper()
                    
                    # Skip stablecoins and special assets as base
                    if asset in SKIP_AS_BASE or asset.startswith('LD'):
                        continue
                    
                    # Clean up Binance Earn prefix if present
                    clean_asset = asset[2:] if asset.startswith('LD') else asset
                    
                    # Only try quote currencies that this asset actually supports on Binance
                    # USDC and USDT are widely supported
                    symbols.append(f"{clean_asset}USDC")
                    symbols.append(f"{clean_asset}USDT")
                    
                    # EUR only for major coins
                    if clean_asset in BINANCE_EUR_SUPPORTED:
                        symbols.append(f"{clean_asset}EUR")
                    
                    # GBP only for top coins
                    if clean_asset in BINANCE_GBP_SUPPORTED:
                        symbols.append(f"{clean_asset}GBP")
        
        all_trades = {}
        for symbol in symbols:
            try:
                trades = self.get_my_trades(symbol, limit_per_symbol, silent=True)
                if trades:
                    all_trades[symbol] = trades
            except:
                continue
        return all_trades
    
    def calculate_cost_basis(self, symbol: str) -> Dict[str, Any]:
        """Calculate average cost basis for a symbol from trade history.
        
        Returns:
            {
                'symbol': str,
                'avg_entry_price': float,
                'total_quantity': float,
                'total_cost': float,
                'total_fees': float,
                'trade_count': int,
                'first_trade': timestamp,
                'last_trade': timestamp
            }
        """
        trades = self.get_my_trades(symbol)
        if not trades:
            return None
        
        total_qty = 0.0
        total_cost = 0.0
        total_fees = 0.0
        buy_trades = 0
        first_trade = None
        last_trade = None
        
        for trade in trades:
            is_buyer = trade.get('isBuyer', False)
            qty = float(trade.get('qty', 0))
            price = float(trade.get('price', 0))
            commission = float(trade.get('commission', 0))
            timestamp = trade.get('time', 0)
            
            if is_buyer:
                total_qty += qty
                total_cost += qty * price
                total_fees += commission
                buy_trades += 1
            else:
                # Sell reduces position
                total_qty -= qty
                # Proportionally reduce cost basis
                if total_qty > 0:
                    avg_price = total_cost / (total_qty + qty) if (total_qty + qty) > 0 else 0
                    total_cost = total_qty * avg_price
            
            if first_trade is None or timestamp < first_trade:
                first_trade = timestamp
            if last_trade is None or timestamp > last_trade:
                last_trade = timestamp
        
        avg_entry = total_cost / total_qty if total_qty > 0 else 0
        
        return {
            'symbol': symbol,
            'avg_entry_price': avg_entry,
            'total_quantity': total_qty,
            'total_cost': total_cost,
            'total_fees': total_fees,
            'trade_count': buy_trades,
            'first_trade': first_trade,
            'last_trade': last_trade
        }

    # ══════════════════════════════════════════════════════════════════════
    # CRYPTO CONVERSION - Convert between crypto assets internally
    # ══════════════════════════════════════════════════════════════════════

    _pairs_cache = None
    _pairs_cache_time = 0
    _PAIRS_CACHE_TTL = 300  # 5 minutes

    def get_available_pairs(self, base: str = None, quote: str = None) -> List[Dict[str, Any]]:
        """
        Get available trading pairs, optionally filtered by base or quote asset.
        Uses caching to avoid repeated API calls (5 min TTL).
        """
        import time as _time
        current_time = _time.time()
        
        # Check cache
        if BinanceClient._pairs_cache is None or (current_time - BinanceClient._pairs_cache_time) > BinanceClient._PAIRS_CACHE_TTL:
            try:
                info = self.exchange_info()
                symbols = info.get("symbols", [])
                all_pairs = []
                
                for sym in symbols:
                    if sym.get("status") != "TRADING":
                        continue
                    
                    all_pairs.append({
                        "pair": sym.get("symbol"),
                        "base": sym.get("baseAsset", ""),
                        "quote": sym.get("quoteAsset", "")
                    })
                
                BinanceClient._pairs_cache = all_pairs
                BinanceClient._pairs_cache_time = current_time
            except Exception as e:
                print(f"Error getting pairs: {e}")
                return BinanceClient._pairs_cache or []
        
        # Filter from cache
        results = []
        for p in (BinanceClient._pairs_cache or []):
            if base and p["base"].upper() != base.upper():
                continue
            if quote and p["quote"].upper() != quote.upper():
                continue
            results.append(p)
        
        return results

    def find_conversion_path(self, from_asset: str, to_asset: str) -> List[Dict[str, Any]]:
        """Find the best path to convert from one asset to another."""
        from_asset = from_asset.upper()
        to_asset = to_asset.upper()
        
        if from_asset == to_asset:
            return []
        
        pairs = self.get_available_pairs()
        pair_map = {p["pair"]: p for p in pairs}
        
        # Try direct pair
        direct_pair = f"{from_asset}{to_asset}"
        if direct_pair in pair_map:
            return [{"pair": direct_pair, "side": "sell", "from": from_asset, "to": to_asset}]
        
        # Try inverse pair
        inverse_pair = f"{to_asset}{from_asset}"
        if inverse_pair in pair_map:
            return [{"pair": inverse_pair, "side": "buy", "from": from_asset, "to": to_asset}]
        
        # Route through intermediary
        for intermediate in ['USDC', 'BTC', 'EUR']:  # UK-safe intermediaries
            if intermediate in (from_asset, to_asset):
                continue
            
            path1 = None
            p1_direct = f"{from_asset}{intermediate}"
            p1_inverse = f"{intermediate}{from_asset}"
            
            if p1_direct in pair_map:
                path1 = {"pair": p1_direct, "side": "sell", "from": from_asset, "to": intermediate}
            elif p1_inverse in pair_map:
                path1 = {"pair": p1_inverse, "side": "buy", "from": from_asset, "to": intermediate}
            
            if not path1:
                continue
            
            path2 = None
            p2_direct = f"{intermediate}{to_asset}"
            p2_inverse = f"{to_asset}{intermediate}"
            
            if p2_direct in pair_map:
                path2 = {"pair": p2_direct, "side": "sell", "from": intermediate, "to": to_asset}
            elif p2_inverse in pair_map:
                path2 = {"pair": p2_inverse, "side": "buy", "from": intermediate, "to": to_asset}
            
            if path2:
                return [path1, path2]
        
        return []

    def convert_crypto(self, from_asset: str, to_asset: str, amount: float) -> Dict[str, Any]:
        """Convert one crypto asset to another within Binance."""
        from_asset = from_asset.upper()
        to_asset = to_asset.upper()
        
        if from_asset == to_asset:
            return {"error": "Cannot convert to same asset"}
        
        # 🌍✨ PLANET SAVER: Freedom! Past doesn't define future!
        # Let the scanner and Queen decide profitability!
        
        path = self.find_conversion_path(from_asset, to_asset)
        
        if not path:
            return {"error": f"No conversion path found from {from_asset} to {to_asset}"}
        
        # 👑 QUEEN MIND: Pre-flight balance check
        # Get fresh balance BEFORE trading
        try:
            acct = self.account() or {}
            actual_balance = 0.0
            for bal in acct.get('balances', []):
                if bal.get('asset', '').upper() == from_asset:
                    actual_balance = float(bal.get('free', 0))
                    break
            
            if actual_balance <= 0:
                return {"error": f"No {from_asset} balance available on Binance (free: {actual_balance})"}
            
            # Clamp to actual balance if needed
            if amount > actual_balance:
                print(f"   👑 Binance pre-trade clamping: {amount:.6f} → {actual_balance * 0.98:.6f}")
                amount = actual_balance * 0.98  # Extra 2% buffer for fees
        except Exception as e:
            print(f"   ⚠️ Balance check warning: {e}")
        
        # 👑 SERO: Pre-flight validation for multi-step conversions
        # Binance MIN_NOTIONAL is typically $5-10 depending on pair
        min_notional = 5.0
        estimated_amount = amount
        estimated_value_usd = amount  # Track USD value through the path
        
        # Get SOL price for initial value estimate
        try:
            from_ticker = self.get_ticker_price(f"{from_asset}USDC") or self.get_ticker_price(f"{from_asset}USDT")
            if from_ticker:
                from_price = float(from_ticker.get("price", 0))
                estimated_value_usd = amount * from_price
        except:
            pass
        
        for i, trade in enumerate(path):
            pair = trade["pair"]
            side = trade["side"]
            
            # Get current price
            try:
                ticker = self.get_ticker_price(pair)
                price = float(ticker.get("price", 0)) if ticker else 0
            except Exception:
                price = 0
            
            if side == "sell":
                # Selling base asset - check notional value in USD terms
                if estimated_value_usd < min_notional and estimated_value_usd > 0:
                    return {
                        "error": f"Multi-hop step {i+1} value ${estimated_value_usd:.2f} < min ${min_notional:.2f} for {pair}",
                        "failed_step": i,
                        "pair": pair
                    }
                # After sell, we have quote currency (usually USDC)
                if price > 0:
                    estimated_amount = estimated_amount * price
                    # estimated_value_usd stays roughly the same (minus fees)
            else:
                # Buying with quote currency - check if we have enough USD value
                if estimated_value_usd < min_notional:
                    return {
                        "error": f"Multi-hop step {i+1} value ${estimated_value_usd:.2f} < min ${min_notional:.2f} for {pair}",
                        "failed_step": i,
                        "pair": pair
                    }
                # After buy, we have base currency
                if price > 0:
                    estimated_amount = estimated_amount / price
                    # estimated_value_usd stays roughly the same (minus fees)
        
        if self.dry_run:
            return {"dryRun": True, "path": path, "trades": len(path)}
        
        results = []
        # Reserve 2% for fees/rounding to avoid "insufficient balance" errors
        remaining_amount = amount * 0.98
        
        for trade in path:
            pair = trade["pair"]
            side = trade["side"]
            
            try:
                if side == "sell":
                    result = self.place_market_order(pair, "SELL", quantity=remaining_amount)
                else:
                    result = self.place_market_order(pair, "BUY", quote_qty=remaining_amount)
                
                results.append({"trade": trade, "result": result, "status": "success"})
                
                exec_qty = float(result.get("executedQty", 0))
                cumm_quote = float(result.get("cummulativeQuoteQty", 0))
                remaining_amount = cumm_quote if side == "sell" else exec_qty
                    
            except Exception as e:
                return {"error": f"Trade failed: {e}", "partial_results": results}
        
        return {"success": True, "trades": results, "final_amount": remaining_amount}


def position_size_from_balance(client: BinanceClient, symbol: str, fraction: float, max_usdt: float) -> float:
    # Assume quote asset is USDT for simplicity
    quote_free = client.get_free_balance("USDT")
    size = quote_free * fraction
    return min(size, max_usdt)


def load_risk_config() -> Dict[str, Any]:
    return {
        "fraction": float(os.getenv("BINANCE_RISK_FRACTION", "0.02")),
        "max_usdt": float(os.getenv("BINANCE_RISK_MAX_ORDER_USDT", "25"))
    }


# ═══════════════════════════════════════════════════════════════════════════
# BINANCE POOL MINING API
# ═══════════════════════════════════════════════════════════════════════════

class BinancePoolClient:
    """
    Binance Pool Mining API Client
    
    Endpoints for tracking mining earnings, hashrate, and payouts.
    https://binance-docs.github.io/apidocs/spot/en/#mining-endpoints
    """
    
    def __init__(self, client: BinanceClient = None):
        self.client = client or BinanceClient()
        self.base = self.client.base
        self.session = self.client.session
    
    def _signed_request(self, method: str, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Signed request using parent client's auth"""
        return self.client._signed_request(method, path, params)
    
    # ═══════════════════════════════════════════════════════════════════════
    # MINING ACCOUNT INFO
    # ═══════════════════════════════════════════════════════════════════════
    
    def get_algo_list(self) -> Dict[str, Any]:
        """Get list of mining algorithms (SAPI)"""
        return self._signed_request("GET", "/sapi/v1/mining/pub/algoList", {})
    
    def get_coin_list(self) -> Dict[str, Any]:
        """Get list of mineable coins (SAPI)"""
        return self._signed_request("GET", "/sapi/v1/mining/pub/coinList", {})
    
    def get_miner_list(self, algo: str = "sha256", user_name: str = None) -> Dict[str, Any]:
        """Get list of miners for account
        
        Args:
            algo: Algorithm name (sha256, ethash, etc.)
            user_name: Mining account username
        """
        params = {"algo": algo}
        if user_name:
            params["userName"] = user_name
        return self._signed_request("GET", "/sapi/v1/mining/worker/list", params)
    
    def get_miner_detail(self, algo: str, worker_name: str, user_name: str = None) -> Dict[str, Any]:
        """Get detailed miner/worker stats
        
        Args:
            algo: Algorithm name
            worker_name: Worker name (e.g., 'aureon')
            user_name: Mining account username
        """
        params = {"algo": algo, "workerName": worker_name}
        if user_name:
            params["userName"] = user_name
        return self._signed_request("GET", "/sapi/v1/mining/worker/detail", params)
    
    # ═══════════════════════════════════════════════════════════════════════
    # EARNINGS & PAYOUTS
    # ═══════════════════════════════════════════════════════════════════════
    
    def get_earnings_list(self, algo: str = "sha256", user_name: str = None, 
                          coin: str = None, start_date: int = None, 
                          end_date: int = None, page: int = 1, 
                          page_size: int = 20) -> Dict[str, Any]:
        """Get mining earnings history
        
        Args:
            algo: Algorithm name
            user_name: Mining account username
            coin: Coin name (BTC, ETH, etc.)
            start_date: Start timestamp (ms)
            end_date: End timestamp (ms)
            page: Page number
            page_size: Results per page (max 200)
        """
        params = {"algo": algo, "page": page, "pageSize": min(page_size, 200)}
        if user_name:
            params["userName"] = user_name
        if coin:
            params["coin"] = coin
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        return self._signed_request("GET", "/sapi/v1/mining/payment/list", params)
    
    def get_extra_bonus(self, algo: str = "sha256", user_name: str = None,
                        coin: str = None, start_date: int = None,
                        end_date: int = None, page: int = 1,
                        page_size: int = 20) -> Dict[str, Any]:
        """Get extra mining bonus (referral, events, etc.)"""
        params = {"algo": algo, "page": page, "pageSize": min(page_size, 200)}
        if user_name:
            params["userName"] = user_name
        if coin:
            params["coin"] = coin
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        return self._signed_request("GET", "/sapi/v1/mining/payment/other", params)
    
    def get_hashrate_resale_list(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """Get hashrate resale list (if selling hashpower)"""
        params = {"page": page, "pageSize": min(page_size, 200)}
        return self._signed_request("GET", "/sapi/v1/mining/hash-transfer/config/details/list", params)
    
    # ═══════════════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════════════
    
    def get_statistic_list(self, algo: str = "sha256", user_name: str = None) -> Dict[str, Any]:
        """Get mining statistics (hashrate, earnings summary)
        
        Returns:
            {
                "code": 0,
                "data": {
                    "fifteenMinHashRate": "457.38",
                    "dayHashRate": "450.12",
                    "validNum": 5,
                    "invalidNum": 0,
                    "profitToday": {"BTC": "0.00012345"},
                    "profitYesterday": {"BTC": "0.00011234"},
                    "userName": "mining_account",
                    "unit": "TH/s",
                    "algo": "sha256"
                }
            }
        """
        params = {"algo": algo}
        # userName is required by Binance Pool API
        if user_name:
            params["userName"] = user_name
        else:
            # Try to get from environment
            params["userName"] = os.getenv("BINANCE_POOL_USERNAME", os.getenv("MINING_WORKER", "").split(".")[0])
        
        if not params["userName"]:
            return {"code": -1, "msg": "userName required - set BINANCE_POOL_USERNAME env var", "data": {}}
        
        return self._signed_request("GET", "/sapi/v1/mining/statistics/user/status", params)
    
    def get_account_list(self, algo: str = "sha256", user_name: str = None) -> Dict[str, Any]:
        """Get mining account earnings list"""
        params = {"algo": algo}
        if user_name:
            params["userName"] = user_name
        return self._signed_request("GET", "/sapi/v1/mining/statistics/user/list", params)
    
    # ═══════════════════════════════════════════════════════════════════════
    # CONVENIENCE METHODS
    # ═══════════════════════════════════════════════════════════════════════
    
    def get_total_earnings(self, algo: str = "sha256", coin: str = "BTC") -> Dict[str, float]:
        """Get total earnings summary
        
        Returns:
            {
                'today': float,
                'yesterday': float,
                'total_paid': float,
                'hashrate_15m': float,
                'hashrate_24h': float,
                'unit': str
            }
        """
        try:
            stats = self.get_statistic_list(algo)
            data = stats.get('data', {})
            
            today = 0.0
            yesterday = 0.0
            
            profit_today = data.get('profitToday', {})
            profit_yesterday = data.get('profitYesterday', {})
            
            if isinstance(profit_today, dict):
                today = float(profit_today.get(coin, 0))
            if isinstance(profit_yesterday, dict):
                yesterday = float(profit_yesterday.get(coin, 0))
            
            return {
                'today': today,
                'yesterday': yesterday,
                'hashrate_15m': float(data.get('fifteenMinHashRate', 0)),
                'hashrate_24h': float(data.get('dayHashRate', 0)),
                'valid_workers': int(data.get('validNum', 0)),
                'invalid_workers': int(data.get('invalidNum', 0)),
                'unit': data.get('unit', 'H/s'),
                'algo': algo,
                'coin': coin
            }
        except Exception as e:
            return {
                'error': str(e),
                'today': 0.0,
                'yesterday': 0.0,
                'hashrate_15m': 0.0,
                'hashrate_24h': 0.0,
                'valid_workers': 0,
                'invalid_workers': 0,
                'unit': 'H/s',
                'algo': algo,
                'coin': coin
            }
    
    def get_wallet_balance(self, asset: str = "BTC") -> float:
        """Get current wallet balance for mining payouts"""
        try:
            balance = self.client.get_free_balance(asset)
            return float(balance)
        except Exception:
            return 0.0
    
    def format_earnings_display(self, algo: str = "sha256", coin: str = "BTC") -> str:
        """Format earnings for display"""
        earnings = self.get_total_earnings(algo, coin)
        balance = self.get_wallet_balance(coin)
        
        if 'error' in earnings:
            return f"⚠️ Mining API Error: {earnings['error']}"
        
        return (
            f"💰 BINANCE POOL EARNINGS ({coin})\n"
            f"   Today:     {earnings['today']:.8f} {coin}\n"
            f"   Yesterday: {earnings['yesterday']:.8f} {coin}\n"
            f"   Hashrate:  {earnings['hashrate_15m']:.2f} {earnings['unit']} (15m)\n"
            f"   Workers:   {earnings['valid_workers']} active, {earnings['invalid_workers']} inactive\n"
            f"   Wallet:    {balance:.8f} {coin}"
        )

    # ══════════════════════════════════════════════════════════════════════
    # CRYPTO CONVERSION - Convert between crypto assets internally
    # ══════════════════════════════════════════════════════════════════════

    def get_available_pairs(self, base: str = None, quote: str = None) -> List[Dict[str, Any]]:
        """
        Get available trading pairs, optionally filtered by base or quote asset.
        
        Args:
            base: Filter by base asset (e.g., 'BTC', 'ETH')
            quote: Filter by quote asset (e.g., 'USDT', 'ETH')
            
        Returns:
            List of pairs with base, quote, and pair name
        """
        try:
            info = self._request("GET", "/api/v3/exchangeInfo")
            symbols = info.get("symbols", [])
            results = []
            
            for sym in symbols:
                if sym.get("status") != "TRADING":
                    continue
                
                pair_base = sym.get("baseAsset", "")
                pair_quote = sym.get("quoteAsset", "")
                
                # Apply filters
                if base and pair_base.upper() != base.upper():
                    continue
                if quote and pair_quote.upper() != quote.upper():
                    continue
                
                results.append({
                    "pair": sym.get("symbol"),
                    "base": pair_base,
                    "quote": pair_quote,
                    "minNotional": self._get_min_notional(sym),
                    "minQty": self._get_min_qty(sym)
                })
            
            return results
        except Exception as e:
            print(f"Error getting pairs: {e}")
            return []
    
    def _get_min_notional(self, sym_info: Dict) -> float:
        """Extract minimum notional from symbol filters"""
        for f in sym_info.get("filters", []):
            if f.get("filterType") == "NOTIONAL":
                return float(f.get("minNotional", 0))
            if f.get("filterType") == "MIN_NOTIONAL":
                return float(f.get("minNotional", 0))
        return 0.0
    
    def _get_min_qty(self, sym_info: Dict) -> float:
        """Extract minimum quantity from symbol filters"""
        for f in sym_info.get("filters", []):
            if f.get("filterType") == "LOT_SIZE":
                return float(f.get("minQty", 0))
        return 0.0

    def find_conversion_path(self, from_asset: str, to_asset: str) -> List[Dict[str, Any]]:
        """
        Find the best path to convert from one asset to another.
        
        Returns list of trades to execute:
        - Single trade if direct pair exists
        - Two trades via USDT/BTC if no direct pair
        
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
        
        # Get all trading pairs
        pairs = self.get_available_pairs()
        pair_map = {p["pair"]: p for p in pairs}
        
        # Try direct pair: from_asset + to_asset
        direct_pair = f"{from_asset}{to_asset}"
        if direct_pair in pair_map:
            return [{
                "pair": direct_pair,
                "side": "sell",
                "description": f"Sell {from_asset} for {to_asset}",
                "from": from_asset,
                "to": to_asset
            }]
        
        # Try inverse pair: to_asset + from_asset
        inverse_pair = f"{to_asset}{from_asset}"
        if inverse_pair in pair_map:
            return [{
                "pair": inverse_pair,
                "side": "buy",
                "description": f"Buy {to_asset} with {from_asset}",
                "from": from_asset,
                "to": to_asset
            }]
        
        # No direct pair - route through intermediary (USDT, USDC, BTC, BNB)
        for intermediate in ['USDT', 'USDC', 'BTC', 'BNB', 'EUR']:
            if intermediate == from_asset or intermediate == to_asset:
                continue
            
            # 🐍 MEDUSA: Skip restricted intermediaries in UK mode
            if self.uk_mode:
                if intermediate in UK_RESTRICTED_TOKENS:
                    continue
                # Explicitly block USDC for UK users (often restricted/unavailable)
                if intermediate == 'USDC':
                    continue
            
            # Check if we can go from_asset -> intermediate
            path1 = None
            p1_direct = f"{from_asset}{intermediate}"
            p1_inverse = f"{intermediate}{from_asset}"
            
            if p1_direct in pair_map:
                path1 = {"pair": p1_direct, "side": "sell", "from": from_asset, "to": intermediate,
                         "description": f"Sell {from_asset} for {intermediate}"}
            elif p1_inverse in pair_map:
                path1 = {"pair": p1_inverse, "side": "buy", "from": from_asset, "to": intermediate,
                         "description": f"Buy {intermediate} with {from_asset}"}
            
            if not path1:
                continue
            
            # Check if we can go intermediate -> to_asset
            path2 = None
            p2_direct = f"{intermediate}{to_asset}"
            p2_inverse = f"{to_asset}{intermediate}"
            
            if p2_direct in pair_map:
                path2 = {"pair": p2_direct, "side": "sell", "from": intermediate, "to": to_asset,
                         "description": f"Sell {intermediate} for {to_asset}"}
            elif p2_inverse in pair_map:
                path2 = {"pair": p2_inverse, "side": "buy", "from": intermediate, "to": to_asset,
                         "description": f"Buy {to_asset} with {intermediate}"}
            
            if path2:
                return [path1, path2]
        
        return []  # No path found

    def convert_crypto(
        self,
        from_asset: str,
        to_asset: str,
        amount: float,
        use_quote_amount: bool = False
    ) -> Dict[str, Any]:
        """
        Convert one crypto asset to another within Binance.
        
        Automatically finds the best path:
        - Direct pair if available (e.g., ETHBTC)
        - Via USDT/BTC if no direct pair
        
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
        
        # 🌍✨ PLANET SAVER: Freedom! Past doesn't define future!
        # Let the scanner and Queen decide profitability!
        
        # REFRESH BALANCE & CLAMP AMOUNT
        # This prevents "Insufficient Balance" errors when selling 100% of an asset
        if not use_quote_amount:
            try:
                # Get fresh balance
                balance_info = self.get_asset_balance(from_asset)
                if balance_info:
                    available = float(balance_info.get('free', 0))
                    
                    # If we're trying to sell more than we have (or very close to it)
                    # Clamp to 99.9% to cover potential rounding/fees/dust
                    if amount > available * 0.99:
                        print(f"   ⚠️ Clamping amount {amount} to 99.9% of available {available} {from_asset}")
                        amount = available * 0.999
                        
                        # Truncate to 8 decimals to avoid precision errors
                        amount = float(f"{amount:.8f}")
            except Exception as e:
                print(f"   ⚠️ Could not refresh balance for {from_asset}: {e}")

        # Find conversion path
        path = self.find_conversion_path(from_asset, to_asset)
        
        if not path:
            return {"error": f"No conversion path found from {from_asset} to {to_asset}"}
        
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
                    # Selling base asset
                    result = self.place_market_order(pair, "SELL", quantity=remaining_amount)
                else:
                    # Buying base asset with quote
                    # Use quoteOrderQty to spend exact amount
                    result = self.place_market_order(pair, "BUY", quote_qty=remaining_amount)
                
                results.append({
                    "trade": trade,
                    "result": result,
                    "status": "success"
                })
                
                # Update remaining amount for next trade
                exec_qty = float(result.get("executedQty", 0))
                cumm_quote = float(result.get("cummulativeQuoteQty", 0))
                
                if side == "sell":
                    # We sold, received quote currency
                    remaining_amount = cumm_quote
                else:
                    # We bought, received base currency
                    remaining_amount = exec_qty
                    
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
        Get all assets that can be converted to/from.
        
        Returns:
            Dict mapping each asset to list of assets it can convert to
        """
        pairs = self.get_available_pairs()
        
        # Build conversion map
        conversions = {}
        
        for p in pairs:
            base = p["base"].upper()
            quote = p["quote"].upper()
            
            # Base can convert to quote (by selling)
            if base not in conversions:
                conversions[base] = set()
            conversions[base].add(quote)
            
            # Quote can convert to base (by buying)
            if quote not in conversions:
                conversions[quote] = set()
            conversions[quote].add(base)
        
        # Convert sets to sorted lists
        return {k: sorted(v) for k, v in conversions.items()}


# ═══════════════════════════════════════════════════════════════════════════════
# 🟡 SINGLETON PATTERN - Single Binance client instance across all modules
# ═══════════════════════════════════════════════════════════════════════════════
_binance_client_instance: Optional['BinanceClient'] = None
_binance_client_lock = None  # Lazy init to avoid import issues

def get_binance_client() -> Optional['BinanceClient']:
    """
    Get the singleton BinanceClient instance.
    
    This ensures only ONE BinanceClient exists across the entire application,
    preventing rate limit issues and connection pool exhaustion.
    
    Usage:
        from binance_client import get_binance_client
        client = get_binance_client()
        if client:
            balance = client.get_balance()
    
    Returns:
        BinanceClient instance, or None if credentials are missing
    """
    global _binance_client_instance, _binance_client_lock
    
    # Lazy init the lock
    if _binance_client_lock is None:
        import threading
        _binance_client_lock = threading.Lock()
    
    if _binance_client_instance is None:
        with _binance_client_lock:
            # Double-check locking pattern
            if _binance_client_instance is None:
                try:
                    _binance_client_instance = BinanceClient()
                    import logging
                    logging.getLogger(__name__).info("🟡 Binance singleton client initialized")
                except ValueError as e:
                    # Missing credentials
                    import logging
                    logging.getLogger(__name__).warning(f"⚠️ Binance client unavailable: {e}")
                    return None
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).error(f"❌ Binance client init failed: {e}")
                    return None
    
    return _binance_client_instance


def safe_trade(symbol: str = None, side: str = "BUY") -> Dict[str, Any]:
    symbol = symbol or os.getenv("BINANCE_SYMBOL", "BTCUSDT")
    client = get_binance_client()
    if not client:
        return {"error": "Binance client not available"}
    if not client.ping():
        raise RuntimeError("Binance API not reachable")
    risk = load_risk_config()
    size = position_size_from_balance(client, symbol, risk["fraction"], risk["max_usdt"])
    if size < 5:  # require a minimal notional for meaningful trade
        return {"skipped": True, "reason": "Insufficient free USDT for minimum trade", "calculatedSize": size}
    order = client.place_market_order(symbol, side, round(size, 2))
    return {"orderResult": order, "risk": risk}

if __name__ == "__main__":
    try:
        result = safe_trade()
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error executing trade: {e}")
