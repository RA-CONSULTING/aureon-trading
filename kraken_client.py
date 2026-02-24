import os, time, json, math, hmac, hashlib, base64, threading, random, logging
from typing import Dict, Any, List, Tuple
from decimal import Decimal

# Cross-process file locking for the Kraken nonce counter.
# - POSIX: fcntl.flock
# - Windows: msvcrt.locking (byte-range lock)
try:
    import fcntl  # type: ignore
except Exception:  # pragma: no cover - Windows
    fcntl = None  # type: ignore
    try:
        import msvcrt  # type: ignore
    except Exception:  # pragma: no cover
        msvcrt = None  # type: ignore

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # 🔑 Use override=True to ensure newest keys are always loaded!
    load_dotenv(override=True)
except ImportError:
    pass

KRAKEN_BASE = "https://api.kraken.com"

ASSETPAIR_CACHE_TTL = 300  # seconds
KRAKEN_TRADES_PAGE_SIZE = 50

logger = logging.getLogger(__name__)

# Import TokenBucket for proper rate limiting
try:
    from rate_limiter import TokenBucket, TTLCache
    _RATE_LIMITER_AVAILABLE = True
except ImportError:
    _RATE_LIMITER_AVAILABLE = False

# ─── Kraken Rate Limit Tiers ──────────────────────────────────────────
# Kraken uses a decaying counter model. Each private API call adds to the
# counter; it decays at a fixed rate depending on verification tier.
#   Starter:      max 15, decay 0.33/sec → sustain ~1 call / 3s
#   Intermediate: max 20, decay 0.5 /sec → sustain ~1 call / 2s
#   Pro:          max 20, decay 1.0 /sec → sustain ~1 call / 1s
# Matching orders add 0 (limit) or 1 (market). Ledger/TradesHistory add 2.
# Public endpoints have a separate, looser limit (~1 call/sec sustained).
KRAKEN_TIER = os.getenv("KRAKEN_TIER", "starter").lower()  # starter|intermediate|pro

_TIER_SETTINGS: Dict[str, Dict[str, float]] = {
    "starter":      {"capacity": 15, "decay": 0.33, "private_interval": 2.0, "page_interval": 4.0},
    "intermediate": {"capacity": 20, "decay": 0.50, "private_interval": 1.5, "page_interval": 3.0},
    "pro":          {"capacity": 20, "decay": 1.00, "private_interval": 1.0, "page_interval": 2.0},
}
_TIER = _TIER_SETTINGS.get(KRAKEN_TIER, _TIER_SETTINGS["starter"])

# 🔐 CROSS-PROCESS NONCE MANAGER
# Prevents "Invalid nonce" errors when multiple processes share the same API key
# Uses file-based atomic counter with locking
_DEFAULT_NONCE_FILE = os.path.join(os.path.dirname(__file__) or '.', '.kraken_nonce')
# Prefer a stable per-instance state path when provided (Docker/Windows-friendly).
NONCE_FILE = os.getenv("KRAKEN_NONCE_PATH") or _DEFAULT_NONCE_FILE
_nonce_lock = threading.Lock()

def _lock_file(handle) -> None:
    if fcntl is not None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        return
    if 'msvcrt' in globals() and msvcrt is not None:
        # Ensure file has at least one byte so we can lock a range.
        try:
            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write("0")
                handle.flush()
        except Exception:
            pass
        handle.seek(0)
        # Lock the first byte. This blocks until acquired.
        msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        return

def _unlock_file(handle) -> None:
    if fcntl is not None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        return
    if 'msvcrt' in globals() and msvcrt is not None:
        try:
            handle.seek(0)
        except Exception:
            pass
        try:
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        except Exception:
            pass

def _read_nonce_text(text: str) -> int:
    text = (text or "").strip()
    if not text:
        return 0
    if text.startswith("{"):
        try:
            payload = json.loads(text)
            return int(payload.get("nonce") or 0)
        except Exception:
            return 0
    try:
        return int(text)
    except Exception:
        return 0

def _get_next_nonce() -> int:
    """Get next nonce that's guaranteed higher than any previous nonce.
    
    Uses file-based atomic counter with locking to ensure:
    1. Nonces always increase (even across process restarts)
    2. Multiple parallel processes don't collide
    3. Recovers gracefully if nonce file is corrupted
    """
    with _nonce_lock:
        # Current time in microseconds as base
        current_us = int(time.time() * 1000000)
        
        try:
            # Try to read existing nonce from file (with locking)
            if os.path.exists(NONCE_FILE):
                with open(NONCE_FILE, 'r+') as f:
                    _lock_file(f)
                    try:
                        last_nonce = _read_nonce_text(f.read())
                    except Exception:
                        last_nonce = 0
                    
                    # New nonce = max(current_time, last_nonce + 1) + random offset
                    # Random offset (0-999) prevents collisions if multiple processes
                    # read the same last_nonce before any can write
                    new_nonce = max(current_us, last_nonce + 1) + random.randint(1, 999)
                    
                    # Write back atomically
                    f.seek(0)
                    f.truncate()
                    f.write(str(new_nonce))
                    f.flush()
                    try:
                        os.fsync(f.fileno())
                    except Exception:
                        pass
                    _unlock_file(f)
                    return new_nonce
            else:
                # Create new nonce file
                new_nonce = current_us + random.randint(1, 999)
                with open(NONCE_FILE, 'w+') as f:
                    _lock_file(f)
                    f.write(str(new_nonce))
                    f.flush()
                    try:
                        os.fsync(f.fileno())
                    except Exception:
                        pass
                    _unlock_file(f)
                return new_nonce
                
        except Exception as e:
            # Fallback: use time + PID + random (less safe but works)
            return current_us + (os.getpid() % 10000) * 1000 + random.randint(1, 999)

class KrakenClient:
    """
    Minimal Kraken REST client exposing a Binance-like interface expected by the
    Aureon orchestrators. Designed for dry-run use by default; private/signed
    endpoints are stubbed unless keys are configured and dry_run is disabled.
    """

    def __init__(self):
        # API keys (optional in dry-run)
        self.api_key = os.getenv("KRAKEN_API_KEY", "")
        self.api_secret = os.getenv("KRAKEN_API_SECRET", "")
        # Kraken has no public testnet for spot; keep flag for parity
        self.use_testnet = False
        # Dry-run - default FALSE for live trading
        self.dry_run = os.getenv("KRAKEN_DRY_RUN", "false").lower() == "true"

        self.base = KRAKEN_BASE
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
            self.session.headers.update({"API-Key": self.api_key})

        self._pairs_cache: Dict[str, Any] = {}
        self._pairs_cache_time: float = 0.0
        # Map altname -> internal pair key used by ticker results
        self._alt_to_int: Dict[str, str] = {}
        self._int_to_alt: Dict[str, str] = {}
        
        # ── Rate Limiting (production-grade) ──────────────────────────────
        # Private API: token bucket mirroring Kraken's decaying counter model
        self._private_lock = threading.Lock()
        self._last_private_call: float = 0.0
        self._min_call_interval: float = _TIER["private_interval"]
        # Heavier interval for paginated endpoints (ledgers, trades history)
        self._page_call_interval: float = _TIER["page_interval"]

        if _RATE_LIMITER_AVAILABLE:
            # Private bucket: match Kraken tier capacity & decay rate
            self._private_bucket = TokenBucket(
                rate=_TIER["decay"],
                capacity=_TIER["capacity"],
                name="kraken_private",
            )
            # Public bucket: ~1 call/sec sustained, burst up to 15
            self._public_bucket = TokenBucket(
                rate=1.0,
                capacity=15.0,
                name="kraken_public",
            )
        else:
            self._private_bucket = None
            self._public_bucket = None
        
        # ── Response Caching (reduce redundant API calls) ─────────────────
        # Balance cache: 30s TTL — get_balance() is called 5+ times per Orca cycle
        self._balance_cache: Dict[str, Any] = {}
        self._balance_cache_time: float = 0.0
        self._balance_cache_ttl: float = 30.0
        # Backoff state for EAPI:Rate limit recovery
        self._rate_limit_backoff: float = 0.0
        self._rate_limit_until: float = 0.0
        self._consecutive_rate_limits: int = 0

    def _normalize_asset_name(self, asset: str) -> str:
        asset_up = (asset or "").upper()
        alias_map = {
            "XBT": "BTC",
            "XXBT": "BTC",
            "XDG": "DOGE",
            "XXDG": "DOGE",
            "XETH": "ETH",
            "XXETH": "ETH",
            "ZUSD": "USD",
            "ZEUR": "EUR",
            "ZGBP": "GBP",
            "ZCAD": "CAD",
        }
        if asset_up in alias_map:
            return alias_map[asset_up]
        if asset_up.startswith(("X", "Z")) and len(asset_up) > 3:
            return asset_up[1:]
        return asset_up

    def _pair_base_quote(self, pair: str) -> Tuple[str, str]:
        pairs = self._load_asset_pairs()
        internal = pair if pair in pairs else self._alt_to_int.get(pair) or self._alt_to_int.get(pair.upper())
        if not internal or internal not in pairs:
            return "", ""
        info = pairs[internal]
        base = self._normalize_asset_name(info.get("base", ""))
        quote = self._normalize_asset_name(info.get("quote", ""))
        return base, quote

    # ──────────────────────────────────────────────────────────────────────
    # Private signing helpers (only if we later enable non-dry-run)
    # ──────────────────────────────────────────────────────────────────────
    def _kraken_sign(self, url_path: str, data: Dict[str, Any]) -> str:
        # Kraken signature: HMAC-SHA512 of (url_path + SHA256(nonce+postdata)) with base64-decoded secret
        postdata = "".join([f"{k}={data[k]}&" for k in data]).rstrip("&")
        nonce = str(data.get("nonce", ""))
        message = (nonce + postdata).encode()
        sha256_hash = hashlib.sha256(message).digest()
        mac = hmac.new(base64.b64decode(self.api_secret), url_path.encode() + sha256_hash, hashlib.sha512)
        sigdigest = base64.b64encode(mac.digest()).decode()
        return sigdigest

    def _private(self, path: str, data: Dict[str, Any], _cost: float = 1.0) -> Dict[str, Any]:
        """Execute a private (authenticated) Kraken API call with production-grade rate limiting.
        
        Args:
            path: API endpoint path (e.g. /0/private/Balance)
            data: POST data dict
            _cost: Rate limit cost — 1 for normal calls, 2 for ledger/trades queries
        """
        if self.dry_run:
            raise RuntimeError("Private Kraken endpoint used in dry-run. Provide balances via env or disable dry-run.")
        if not self.api_key or not self.api_secret:
            raise RuntimeError("Missing KRAKEN_API_KEY / KRAKEN_API_SECRET")
        
        max_retries = 3
        for attempt in range(max_retries):
            # Thread-safe rate limiting
            with self._private_lock:
                # 1. Check if we're in a backoff period from a previous rate limit error
                now = time.time()
                if now < self._rate_limit_until:
                    wait_time = self._rate_limit_until - now
                    logger.warning(f"Kraken rate limit backoff: waiting {wait_time:.1f}s")
                    time.sleep(wait_time)
                    now = time.time()
                
                # 2. TokenBucket gate — mirrors Kraken's decaying counter model
                if self._private_bucket:
                    self._private_bucket.wait(tokens=_cost)
                
                # 3. Minimum interval between calls (prevents nonce errors too)
                elapsed = now - self._last_private_call
                if elapsed < self._min_call_interval:
                    time.sleep(self._min_call_interval - elapsed)
                
                data = dict(data)
                data["nonce"] = str(_get_next_nonce())
                headers = {
                    "API-Key": self.api_key,
                    "API-Sign": self._kraken_sign(path, data)
                }
                url = f"{self.base}{path}"
                
                # Update last call time before making request
                self._last_private_call = time.time()
                
                r = self.session.post(url, data=data, headers=headers, timeout=15)
                r.raise_for_status()
                res = r.json()
                
                errors = res.get("error", [])
                if errors:
                    error_str = str(errors)
                    # Handle rate limit errors with exponential backoff
                    if "EAPI:Rate limit exceeded" in error_str or "EGeneral:Too many requests" in error_str:
                        self._consecutive_rate_limits += 1
                        # Exponential backoff: 15s, 30s, 60s, 120s cap
                        backoff = min(15 * (2 ** (self._consecutive_rate_limits - 1)), 120)
                        self._rate_limit_until = time.time() + backoff
                        self._rate_limit_backoff = backoff
                        logger.warning(
                            f"Kraken RATE LIMIT on {path} (attempt {attempt+1}/{max_retries}). "
                            f"Backing off {backoff}s (consecutive: {self._consecutive_rate_limits})"
                        )
                        if attempt < max_retries - 1:
                            time.sleep(backoff)
                            continue  # Retry
                        else:
                            raise RuntimeError(f"Kraken error: {errors}")
                    
                    # Handle invalid nonce (retry with fresh nonce)
                    if "EAPI:Invalid nonce" in error_str and attempt < max_retries - 1:
                        logger.warning(f"Kraken invalid nonce on {path}, retrying...")
                        time.sleep(0.5)
                        continue
                    
                    raise RuntimeError(f"Kraken error: {errors}")
                
                # Success — reset backoff state
                if self._consecutive_rate_limits > 0:
                    logger.info(f"Kraken rate limit recovered after {self._consecutive_rate_limits} consecutive limits")
                    self._consecutive_rate_limits = 0
                    self._rate_limit_backoff = 0.0
                
                # Invalidate balance cache after order/cancel operations
                if "AddOrder" in path or "CancelOrder" in path:
                    self._balance_cache = {}
                    self._balance_cache_time = 0.0
                
                return res.get("result", {})

    # ──────────────────────────────────────────────────────────────────────
    # Public helpers and Binance-like interface
    # ──────────────────────────────────────────────────────────────────────
    def _public_get(self, endpoint: str, params: Dict[str, Any] | None = None, timeout: int = 20) -> Dict[str, Any]:
        """Execute a public Kraken API call with rate limiting.
        
        All public GET requests should go through this method.
        """
        if self._public_bucket:
            self._public_bucket.wait(tokens=1.0)
        
        url = f"{self.base}{endpoint}"
        r = self.session.get(url, params=params, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        if data.get("error"):
            error_str = str(data["error"])
            if "EAPI:Rate limit" in error_str or "EGeneral:Too many" in error_str:
                logger.warning(f"Kraken public rate limit on {endpoint}, waiting 5s...")
                time.sleep(5)
                # Retry once
                r = self.session.get(url, params=params, timeout=timeout)
                r.raise_for_status()
                data = r.json()
                if data.get("error"):
                    raise RuntimeError(f"Kraken error: {data['error']}")
            else:
                raise RuntimeError(f"Kraken error: {data['error']}")
        return data.get("result", {})

    def _load_asset_pairs(self, force: bool = False) -> Dict[str, Any]:
        if not force and time.time() - self._pairs_cache_time < ASSETPAIR_CACHE_TTL and self._pairs_cache:
            return self._pairs_cache
        pairs = self._public_get("/0/public/AssetPairs")
        self._pairs_cache = pairs
        self._pairs_cache_time = time.time()
        # Build alt<->internal maps
        self._alt_to_int = {}
        self._int_to_alt = {}
        for internal, info in pairs.items():
            alt = info.get("altname") or internal
            self._alt_to_int[alt] = internal
            self._int_to_alt[internal] = alt
        return pairs

    def get_ledgers(self, since: int | None = None, max_records: int = 1000) -> List[Dict[str, Any]]:
        if self.dry_run:
            return []
        data: Dict[str, Any] = {"ofs": 0}
        if since:
            data["start"] = int(since)
        ledgers: List[Dict[str, Any]] = []
        total = None
        page = 0
        while True:
            # Ledger queries cost 2 rate limit tokens per Kraken docs
            res = self._private("/0/private/Ledgers", data, _cost=2)
            page += 1
            batch = res.get("ledger", {}) or {}
            count = int(res.get("count", 0) or 0)
            if total is None:
                total = count
            for ledger_id, entry in batch.items():
                entry = dict(entry)
                entry["id"] = ledger_id
                entry["asset"] = self._normalize_asset_name(entry.get("asset", ""))
                ledgers.append(entry)
                if len(ledgers) >= max_records:
                    break
            if len(ledgers) >= max_records or not batch:
                break
            data["ofs"] += len(batch)
            if total is not None and data["ofs"] >= total:
                break
            # Extra delay between pages to avoid rate limit saturation
            time.sleep(self._page_call_interval)
        ledgers.sort(key=lambda x: x.get("time", 0))
        return ledgers

    def get_trades_history(self, since: int | None = None, max_records: int = 1000) -> List[Dict[str, Any]]:
        if self.dry_run:
            return []
        data: Dict[str, Any] = {"ofs": 0}
        if since:
            data["start"] = int(since)
        trades: List[Dict[str, Any]] = []
        total = None
        page = 0
        while True:
            # TradesHistory queries cost 2 rate limit tokens per Kraken docs
            res = self._private("/0/private/TradesHistory", data, _cost=2)
            page += 1
            batch = res.get("trades", {}) or {}
            count = int(res.get("count", 0) or 0)
            if total is None:
                total = count
            for trade_id, trade in batch.items():
                pair = trade.get("pair", "")
                base, quote = self._pair_base_quote(pair)
                trades.append({
                    "id": trade_id,
                    "pair": pair,
                    "base": base,
                    "quote": quote,
                    "type": trade.get("type", ""),
                    "price": float(trade.get("price", 0) or 0),
                    "vol": float(trade.get("vol", 0) or 0),
                    "cost": float(trade.get("cost", 0) or 0),
                    "fee": float(trade.get("fee", 0) or 0),
                    "time": float(trade.get("time", 0) or 0),
                })
                if len(trades) >= max_records:
                    break
            if len(trades) >= max_records or not batch:
                break
            data["ofs"] += len(batch)
            if total is not None and data["ofs"] >= total:
                break
            # Extra delay between pages to avoid rate limit saturation
            time.sleep(self._page_call_interval)
        trades.sort(key=lambda x: x.get("time", 0))
        return trades

    def _normalize_symbol(self, symbol: str) -> List[str]:
        """
        Generate Kraken-compatible alternative altnames for a given symbol.
        Handles BTC/XBT aliasing and quote currency fallbacks.
        """
        s = symbol.upper()
        alts: List[str] = [s]
        # BTC vs XBT
        if s.startswith("BTC"):
            alts.append("XBT" + s[3:])
        if s.startswith("XBT"):
            alts.append("BTC" + s[3:])
        # USDT/USDC/USD fallbacks
        for q in ["USDT", "USDC", "USD"]:
            if s.endswith(q):
                base = s[:-len(q)]
                for alt_q in ["USD", "USDC", "USDT"]:
                    alts.append(base + alt_q)
                break
        # EUR/GBP alt quotes
        for q in ["EUR", "GBP"]:
            if s.endswith(q):
                base = s[:-len(q)]
                alts.extend([base + "USD", base + "USDC", base + "USDT"])  # try USD family too
                break
        # Deduplicate order-preserving
        seen = set()
        out: List[str] = []
        for a in alts:
            if a not in seen:
                out.append(a)
                seen.add(a)
        return out

    def _resolve_pair(self, symbol: str) -> Tuple[str | None, Dict[str, Any] | None]:
        """
        Try to resolve a human-friendly symbol (e.g., 'PEPEUSD', 'ada/usdt')
        to Kraken's internal pair code and return the associated pair info.
        """
        pairs = self._load_asset_pairs()
        normalized = symbol.replace("/", "").upper()
        candidates = [normalized, *self._normalize_symbol(normalized)]

        # Include Kraken-style prefixed forms that sometimes appear in configs
        if normalized in self._int_to_alt:
            candidates.append(normalized)

        for cand in candidates:
            internal = self._alt_to_int.get(cand) or (cand if cand in pairs else None)
            if internal and internal in pairs:
                return internal, pairs[internal]
        return None, None

    def exchange_info(self, symbol: str | None = None) -> Dict[str, Any]:
        """
        Return a Binance-like exchangeInfo structure using Kraken AssetPairs.
        Only fields used by Aureon are populated.
        """
        pairs = self._load_asset_pairs()
        symbols = []
        wanted = None
        if symbol:
            # Kraken altname must be used; try to map from typical BINANCE-style like "ETHUSDC"
            wanted = symbol
        for internal, info in pairs.items():
            alt = info.get("altname") or internal
            if wanted and alt != wanted:
                continue
            wsname = info.get("wsname", "")  # e.g., "ETH/USDC"
            # Derive base/quote from altname if possible
            base_asset, quote_asset = None, None
            if isinstance(alt, str):
                # Try to split alt into [base][quote] by checking common quotes
                for q in ["USDC", "USDT", "USD", "EUR", "BTC", "ETH"]:
                    if alt.endswith(q):
                        base_asset = alt[:-len(q)]
                        quote_asset = q
                        break
            if not base_asset or not quote_asset:
                # Fallback from wsname like "ETH/USDC"
                if "/" in wsname:
                    base_asset, quote_asset = wsname.split("/")
                else:
                    continue

            lot_dec = int(info.get("lot_decimals", info.get("lot_decimals", 8)))
            step_size = 10 ** (-lot_dec)
            ordermin = info.get("ordermin")
            try:
                min_qty = float(ordermin) if ordermin is not None else step_size
            except Exception:
                min_qty = step_size

            # Cost min (quote notional); if missing, set sensible default like $5
            costmin = info.get("costmin")
            try:
                min_notional = float(costmin) if costmin is not None else 5.0
            except Exception:
                min_notional = 5.0

            symbols.append({
                "symbol": alt,
                "status": "TRADING",  # Kraken AssetPairs doesn't expose per-pair trading status consistently
                "baseAsset": base_asset,
                "quoteAsset": quote_asset,
                "filters": {
                    "LOT_SIZE": {"stepSize": str(step_size), "minQty": str(min_qty)},
                    "NOTIONAL": {"minNotional": str(min_notional)}
                }
            })
        return {"symbols": symbols}

    def get_symbol_filters(self, symbol: str) -> Dict[str, float]:
        """
        Get trading filters for a symbol (ordermin, lot_decimals, costmin).
        Returns dict with: min_qty, step_size, min_notional
        """
        pairs = self._load_asset_pairs()
        pair, pair_info = self._resolve_pair(symbol)
        if not pair_info:
            return {}
        
        lot_decimals = int(pair_info.get("lot_decimals", 8))
        step_size = 10 ** (-lot_decimals)
        
        ordermin = pair_info.get("ordermin")
        try:
            min_qty = float(ordermin) if ordermin is not None else step_size
        except Exception:
            min_qty = step_size
        
        costmin = pair_info.get("costmin")
        try:
            min_notional = float(costmin) if costmin is not None else 0.5
        except Exception:
            min_notional = 0.5
        
        return {
            "min_qty": min_qty,
            "step_size": step_size,
            "min_notional": min_notional,
            "lot_decimals": lot_decimals
        }

    def _ticker(self, altnames: List[str]) -> Dict[str, Any]:
        if not altnames:
            return {}
        # Kraken expects internal pair names, not altnames; map
        self._load_asset_pairs()
        
        internal_names = []
        for a in altnames:
            pair, _ = self._resolve_pair(a)
            if pair:
                internal_names.append(pair)
            # Else skip unknown pair to prevent API error
            
        if not internal_names:
            return {}

        # Batch request (Kraken accepts comma-separated list)
        pairs_param = ",".join(internal_names)
        result = self._public_get("/0/public/Ticker", params={"pair": pairs_param})
        # If empty result, try normalized alternatives once
        if not result and len(altnames) == 1:
            alts = self._normalize_symbol(altnames[0])
            internal_names = []
            for a in alts:
                if a in self._alt_to_int:
                    internal_names.append(self._alt_to_int[a])
            if internal_names:
                pairs_param = ",".join(internal_names)
                result = self._public_get("/0/public/Ticker", params={"pair": pairs_param})
        return result

    def get_24h_tickers(self) -> list:
        """
        Return a list of Binance-like 24h ticker dicts with fields:
        - symbol: altname like "ETHUSDC"
        - lastPrice, priceChangePercent, quoteVolume
        """
        pairs = self._load_asset_pairs()
        # Include *all* listed asset pairs to cover every Kraken market, including alt coins
        alts = sorted({info.get("altname") or internal for internal, info in pairs.items()})
        out = []
        # Batch in chunks of 40 with rate-limit-safe delay between chunks
        total_chunks = (len(alts) + 39) // 40
        for chunk_idx in range(total_chunks):
            i = chunk_idx * 40
            chunk = alts[i:i+40]
            try:
                result = self._ticker(chunk)
            except RuntimeError as e:
                if "Rate limit" in str(e):
                    logger.warning(f"Kraken 24h ticker rate limited at chunk {chunk_idx+1}/{total_chunks}, stopping")
                    break
                raise
            for internal, t in result.items():
                alt = self._int_to_alt.get(internal, internal)
                try:
                    last = float(t.get("c", [None])[0] or 0.0)
                    openp = float(t.get("o", 0.0) or 0.0)
                    vol_base = float(t.get("v", [0.0, 0.0])[1])  # 24h volume in base units
                    change_pct = ((last - openp) / openp * 100.0) if openp > 0 else 0.0
                    quote_vol = last * vol_base
                    out.append({
                        "symbol": alt,
                        "lastPrice": str(last),
                        "priceChangePercent": str(change_pct),
                        "quoteVolume": str(quote_vol)
                    })
                except Exception:
                    continue
        return out

    def get_24h_ticker(self, symbol: str) -> Dict[str, Any]:
        # Try symbol and normalized aliases
        candidates = self._normalize_symbol(symbol)
        res = self._ticker([candidates[0]])
        # Only one expected
        if not res:
            # Try other candidates
            for alt in candidates[1:]:
                res = self._ticker([alt])
                if res:
                    break
        if not res:
            return {}
        internal, t = next(iter(res.items()))
        last = float(t.get("c", [None])[0] or 0.0)
        openp = float(t.get("o", 0.0) or 0.0)
        vol_base = float(t.get("v", [0.0, 0.0])[1])
        change_pct = ((last - openp) / openp * 100.0) if openp > 0 else 0.0
        quote_vol = last * vol_base
        return {
            "symbol": self._int_to_alt.get(internal, symbol),
            "lastPrice": str(last),
            "priceChangePercent": str(change_pct),
            "quoteVolume": str(quote_vol)
        }

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Return bid/ask/last for a symbol in a Binance-like shape."""
        try:
            res = self._ticker([symbol]) or self._ticker(self._normalize_symbol(symbol))
            if not res:
                return {"symbol": symbol, "price": 0.0, "bid": 0.0, "ask": 0.0}

            _, t = next(iter(res.items()))
            last = float(t.get("c", [0])[0] or 0.0)
            bid = float(t.get("b", [last])[0] or last)
            ask = float(t.get("a", [last])[0] or last)
            return {
                "symbol": symbol,
                "price": last,
                "bid": bid,
                "ask": ask,
            }
        except Exception:
            return {"symbol": symbol, "price": 0.0, "bid": 0.0, "ask": 0.0}

    def best_price(self, symbol: str) -> Dict[str, Any]:
        t = self.get_24h_ticker(symbol)
        return {"symbol": t.get("symbol", symbol), "price": t.get("lastPrice", "0")}

    def account(self) -> Dict[str, Any]:
        """
        In dry-run, synthesize balances from env vars like DRY_RUN_BALANCE_USDC, DRY_RUN_BALANCE_USD, etc.
        Otherwise, call private Balance (not enabled by default).
        """
        if self.dry_run:
            balances = []
            for asset in ["USDC", "USDT", "USD", "EUR", "BTC", "ETH"]:
                val = os.getenv(f"DRY_RUN_BALANCE_{asset}")
                if val is None:
                    # default to 0 for safety
                    free = 0.0
                else:
                    try:
                        free = float(val)
                    except Exception:
                        free = 0.0
                if free > 0:
                    balances.append({"asset": asset, "free": str(free), "locked": "0"})
            return {"balances": balances}
        # Check balance cache first (30s TTL — prevents hammering for repeated calls)
        now = time.time()
        if self._balance_cache and (now - self._balance_cache_time) < self._balance_cache_ttl:
            return self._balance_cache
        
        # Live API call
        result = self._private("/0/private/Balance", {})
        balances = []
        for asset, amt in result.items():
            try:
                free = float(amt)
            except Exception:
                free = 0.0
            # Kraken uses asset codes like XBT -> map common ones
            norm = {"XBT": "BTC", "XETH": "ETH"}.get(asset, asset)
            balances.append({"asset": norm, "free": str(free), "locked": "0"})
        account_data = {"balances": balances}
        
        # Update cache
        self._balance_cache = account_data
        self._balance_cache_time = time.time()
        return account_data

    def get_account_balance(self) -> Dict[str, float]:
        """Return balances as a simple asset -> amount map (free+locked)."""
        try:
            acct = self.account()
        except Exception:
            return {}

        out: Dict[str, float] = {}
        for bal in acct.get("balances", []):
            try:
                free = float(bal.get("free", 0))
            except Exception:
                free = 0.0
            try:
                locked = float(bal.get("locked", 0))
            except Exception:
                locked = 0.0
            total = free + locked
            if total > 0:
                asset = bal.get("asset")
                if asset:
                    out[asset] = total
        return out

    def get_balance(self) -> Dict[str, float]:
        """Alias for get_account_balance for Alpaca-compatible interface."""
        return self.get_account_balance()

    def invalidate_balance_cache(self) -> None:
        """Force next get_balance() to make a live API call.
        Call this after placing/canceling orders."""
        self._balance_cache = {}
        self._balance_cache_time = 0.0

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Return current rate limit state for diagnostics."""
        status = {
            "tier": KRAKEN_TIER,
            "min_call_interval": self._min_call_interval,
            "page_call_interval": self._page_call_interval,
            "consecutive_rate_limits": self._consecutive_rate_limits,
            "backoff_seconds": self._rate_limit_backoff,
            "backoff_until": self._rate_limit_until,
            "in_backoff": time.time() < self._rate_limit_until,
        }
        if self._private_bucket:
            status["private_bucket_tokens"] = self._private_bucket._tokens
            status["private_bucket_capacity"] = self._private_bucket.capacity
        if self._public_bucket:
            status["public_bucket_tokens"] = self._public_bucket._tokens
            status["public_bucket_capacity"] = self._public_bucket.capacity
        return status

    def get_free_balance(self, asset: str) -> float:
        acct = self.account()
        for bal in acct.get("balances", []):
            if bal.get("asset") == asset:
                try:
                    return float(bal.get("free", 0))
                except Exception:
                    return 0.0
        return 0.0

    def _format_order_value(self, value: float | str | Decimal | None) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return format(Decimal(str(value)), 'f').rstrip('0').rstrip('.') or '0'

    def place_market_order(self, symbol: str, side: str, quantity: float | str | Decimal | None = None, quote_qty: float | str | Decimal | None = None) -> Dict[str, Any]:
        """
        Execute a market order. In dry-run, returns a mock.
        In live mode, calls Kraken AddOrder.
        """
        if self.dry_run:
            return {"dryRun": True, "symbol": symbol, "side": side, "quantity": quantity, "quoteQty": quote_qty}
        
        # Resolve pair and get pair info for validation across *all* Kraken markets
        pair, pair_info = self._resolve_pair(symbol)
        if not pair or not pair_info:
            raise RuntimeError(f"Unknown Kraken trading pair: {symbol}")
        
        ordermin = float(pair_info.get("ordermin", 0.0001))
        lot_decimals = int(pair_info.get("lot_decimals", 8))
        
        params = {
            "pair": pair,
            "type": side.lower(),
            "ordertype": "market",
        }
        
        if quantity:
            vol = float(quantity) if not isinstance(quantity, float) else quantity
        elif quote_qty:
            # Estimate volume from quote quantity
            price_info = self.best_price(symbol)
            price = float(price_info.get("price", 0))
            if price <= 0:
                raise RuntimeError(f"Cannot estimate volume for quote_qty: price is {price}")
            vol = float(quote_qty) / price
        else:
            raise ValueError("Must provide quantity or quote_qty")
        
        # Round to lot_decimals
        vol = round(vol, lot_decimals)
        
        # Validate volume meets minimum
        if vol < ordermin:
            print(f"   ⚠️ Kraken volume {vol:.8f} < min {ordermin} for {symbol}, need larger trade")
            return {"error": "volume_minimum", "symbol": symbol, "volume": vol, "ordermin": ordermin}
        
        params["volume"] = self._format_order_value(vol)

        res = self._private("/0/private/AddOrder", params)
        txid = res.get("txid", ["unknown"])[0]
        
        # Return Binance-compatible response structure
        return {
            "symbol": symbol,
            "orderId": txid,
            "clientOrderId": str(time.time()),
            "transactTime": int(time.time() * 1000),
            "price": "0.00000000",
            "origQty": params.get("volume"),
            "executedQty": params.get("volume"), # Assumed filled
            "cummulativeQuoteQty": str(quote_qty) if quote_qty else "0.00000000",
            "status": "FILLED",
            "timeInForce": "GTC",
            "type": "MARKET",
            "side": side.upper(),
            "fills": [] # Kraken doesn't return fills in AddOrder response immediately
        }

    def convert_to_quote(self, asset: str, amount: float, quote: str) -> float:
        asset_up = asset.upper()
        quote_up = quote.upper()

        if asset_up == quote_up:
            return amount

        # Treat USD stables as 1:1 to avoid false "insufficient funds" from missing pairs
        stable_usd = {"USD", "USDC", "USDT"}
        if asset_up in stable_usd and quote_up in stable_usd:
            return amount

        pair = f"{asset_up}{quote_up}"
        inv_pair = f"{quote_up}{asset_up}"
        try:
            price_info = self.best_price(pair)
            price = float(price_info.get("price", 0))
            if price > 0:
                return amount * price
        except Exception:
            pass
        try:
            price_info = self.best_price(inv_pair)
            price = float(price_info.get("price", 0))
            if price > 0:
                return amount / price
        except Exception:
            pass
        return 0.0

    def get_trades_history(self, start: int = None, end: int = None, ofs: int = 0) -> Dict[str, Any]:
        """Get trade history from Kraken.
        
        Returns dict of trades with entry prices, quantities, fees etc.
        Used to calculate real cost basis for positions.
        
        Kraken API: https://docs.kraken.com/rest/#tag/User-Data/operation/getTradeHistory
        """
        params = {"ofs": ofs}
        if start:
            params["start"] = start
        if end:
            params["end"] = end

        try:
            # Kraken returns paginated results (default ~50 per call).
            # Aggregate pages by default so downstream cost-basis calculations
            # are based on full ledger-backed trade history.
            all_trades: Dict[str, Any] = {}
            page_size = 50
            max_pages = 200
            page = 0
            next_ofs = ofs

            while page < max_pages:
                page_params = dict(params)
                page_params["ofs"] = next_ofs
                # TradesHistory costs 2 rate limit tokens per Kraken docs
                result = self._private("/0/private/TradesHistory", page_params, _cost=2)
                trades = result.get("trades", {}) or {}

                if not trades:
                    break

                all_trades.update(trades)
                page += 1

                if len(trades) < page_size:
                    break

                next_ofs += len(trades)
                # Extra delay between pages to avoid rate limit saturation
                time.sleep(self._page_call_interval)

            return all_trades
        except Exception as e:
            print(f"⚠️ Failed to get Kraken trade history: {e}")
            return {}
    
    def calculate_cost_basis(self, symbol: str) -> Dict[str, Any]:
        """Calculate average cost basis for a symbol from trade history.
        
        Returns:
            {
                'symbol': str,
                'avg_entry_price': float,
                'total_quantity': float,
                'total_cost': float,
                'total_fees': float,
                'trade_count': int
            }
        """
        trades = self.get_trades_history()
        if not trades:
            return None
        
        # Kraken uses different pair naming, normalize
        target_pairs = set()
        # Try various Kraken naming conventions
        base = symbol[:-3] if len(symbol) > 3 else symbol
        for quote in ['USD', 'USDC', 'USDT', 'EUR', 'GBP']:
            target_pairs.add(f"{base}{quote}")
            target_pairs.add(f"X{base}Z{quote}")
            target_pairs.add(f"XX{base}Z{quote}")
        
        total_qty = 0.0
        total_cost = 0.0
        total_fees = 0.0
        buy_trades = 0
        
        for trade_id, trade in trades.items():
            pair = trade.get('pair', '')
            # Check if this trade matches our target symbol
            if pair not in target_pairs and symbol not in pair:
                continue
            
            trade_type = trade.get('type', '')  # 'buy' or 'sell'
            qty = float(trade.get('vol', 0))
            price = float(trade.get('price', 0))
            fee = float(trade.get('fee', 0))
            
            if trade_type == 'buy':
                total_qty += qty
                total_cost += qty * price
                total_fees += fee
                buy_trades += 1
            elif trade_type == 'sell':
                total_qty -= qty
                if total_qty > 0:
                    avg_price = total_cost / (total_qty + qty) if (total_qty + qty) > 0 else 0
                    total_cost = total_qty * avg_price
        
        if total_qty <= 0 or buy_trades == 0:
            return None
        
        avg_entry = total_cost / total_qty if total_qty > 0 else 0
        
        return {
            'symbol': symbol,
            'avg_entry_price': avg_entry,
            'total_quantity': total_qty,
            'total_cost': total_cost,
            'total_fees': total_fees,
            'trade_count': buy_trades
        }

    def compute_order_fees_in_quote(self, order: Dict[str, Any], primary_quote: str) -> float:
        # No fill info in dry-run; return 0 to let orchestrator use configured taker fee model if any
        return 0.0

    # ══════════════════════════════════════════════════════════════════════
    # ADVANCED ORDER TYPES - Limit, Stop-Loss, Take-Profit, Trailing Stop
    # ══════════════════════════════════════════════════════════════════════

    def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float | str | Decimal,
        price: float | str | Decimal,
        post_only: bool = False,
        time_in_force: str = "GTC",
        reduce_only: bool = False
    ) -> Dict[str, Any]:
        """
        Place a limit order on Kraken.
        
        Args:
            symbol: Trading pair (e.g., 'ETHUSD', 'BTCUSDC')
            side: 'buy' or 'sell'
            quantity: Amount of base asset
            price: Limit price
            post_only: If True, order will only be maker (cancelled if would be taker)
            time_in_force: 'GTC' (good-til-cancelled), 'IOC' (immediate-or-cancel), 'GTD' (good-til-date)
            reduce_only: If True, only reduces existing position
            
        Returns:
            Binance-compatible order response
            
        Benefit: Maker fee 0.16% vs Taker fee 0.26% (40% savings with post_only)
        """
        if self.dry_run:
            return {
                "dryRun": True, "symbol": symbol, "side": side, 
                "type": "LIMIT", "quantity": str(quantity), "price": str(price),
                "postOnly": post_only, "timeInForce": time_in_force
            }
        
        self._load_asset_pairs()
        pair = self._alt_to_int.get(symbol, symbol)
        
        params = {
            "pair": pair,
            "type": side.lower(),
            "ordertype": "limit",
            "volume": self._format_order_value(quantity),
            "price": self._format_order_value(price),
        }
        
        # Order flags
        oflags = []
        if post_only:
            oflags.append("post")  # Post-only (maker) order
        if reduce_only:
            oflags.append("nompp")  # No market price protection (for reduce-only behavior)
        if oflags:
            params["oflags"] = ",".join(oflags)
        
        # Time in force
        if time_in_force == "IOC":
            params["timeinforce"] = "IOC"
        elif time_in_force == "GTD":
            params["timeinforce"] = "GTD"
        # GTC is default, no param needed
        
        res = self._private("/0/private/AddOrder", params)
        txid = res.get("txid", ["unknown"])[0]
        
        return {
            "symbol": symbol,
            "orderId": txid,
            "clientOrderId": str(time.time()),
            "transactTime": int(time.time() * 1000),
            "price": str(price),
            "origQty": str(quantity),
            "executedQty": "0",  # Not immediately filled
            "status": "NEW",
            "timeInForce": time_in_force,
            "type": "LIMIT",
            "side": side.upper(),
            "postOnly": post_only
        }

    def place_stop_loss_order(
        self,
        symbol: str,
        side: str,
        quantity: float | str | Decimal,
        stop_price: float | str | Decimal,
        limit_price: float | str | Decimal | None = None
    ) -> Dict[str, Any]:
        """
        Place a stop-loss order on Kraken (server-side, executes even if bot offline).
        
        Args:
            symbol: Trading pair
            side: 'sell' for long positions, 'buy' for short positions
            quantity: Amount to sell/buy when triggered
            stop_price: Price at which the stop triggers
            limit_price: If provided, uses stop-loss-limit instead of stop-loss-market
            
        Returns:
            Order response
            
        CRITICAL: Unlike client-side stops, these execute on Kraken's servers!
        """
        if self.dry_run:
            return {
                "dryRun": True, "symbol": symbol, "side": side,
                "type": "STOP_LOSS_LIMIT" if limit_price else "STOP_LOSS",
                "quantity": str(quantity), "stopPrice": str(stop_price),
                "limitPrice": str(limit_price) if limit_price else None
            }
        
        self._load_asset_pairs()
        pair = self._alt_to_int.get(symbol, symbol)
        
        # stop-loss = market order when triggered
        # stop-loss-limit = limit order when triggered
        order_type = "stop-loss-limit" if limit_price else "stop-loss"
        
        params = {
            "pair": pair,
            "type": side.lower(),
            "ordertype": order_type,
            "volume": self._format_order_value(quantity),
            "price": self._format_order_value(stop_price),  # Trigger price
        }
        
        if limit_price:
            params["price2"] = self._format_order_value(limit_price)  # Limit price after trigger
        
        res = self._private("/0/private/AddOrder", params)
        txid = res.get("txid", ["unknown"])[0]
        
        return {
            "symbol": symbol,
            "orderId": txid,
            "type": "STOP_LOSS_LIMIT" if limit_price else "STOP_LOSS",
            "side": side.upper(),
            "quantity": str(quantity),
            "stopPrice": str(stop_price),
            "limitPrice": str(limit_price) if limit_price else None,
            "status": "NEW"
        }

    def place_take_profit_order(
        self,
        symbol: str,
        side: str,
        quantity: float | str | Decimal,
        take_profit_price: float | str | Decimal,
        limit_price: float | str | Decimal | None = None
    ) -> Dict[str, Any]:
        """
        Place a take-profit order on Kraken (server-side, executes even if bot offline).
        
        Args:
            symbol: Trading pair
            side: 'sell' for long positions (take profit when price rises)
            quantity: Amount to sell when triggered
            take_profit_price: Price at which to take profit
            limit_price: If provided, uses take-profit-limit instead of market
            
        Returns:
            Order response
        """
        if self.dry_run:
            return {
                "dryRun": True, "symbol": symbol, "side": side,
                "type": "TAKE_PROFIT_LIMIT" if limit_price else "TAKE_PROFIT",
                "quantity": str(quantity), "takeProfitPrice": str(take_profit_price),
                "limitPrice": str(limit_price) if limit_price else None
            }
        
        self._load_asset_pairs()
        pair = self._alt_to_int.get(symbol, symbol)
        
        order_type = "take-profit-limit" if limit_price else "take-profit"
        
        params = {
            "pair": pair,
            "type": side.lower(),
            "ordertype": order_type,
            "volume": self._format_order_value(quantity),
            "price": self._format_order_value(take_profit_price),  # Trigger price
        }
        
        if limit_price:
            params["price2"] = self._format_order_value(limit_price)
        
        res = self._private("/0/private/AddOrder", params)
        txid = res.get("txid", ["unknown"])[0]
        
        return {
            "symbol": symbol,
            "orderId": txid,
            "type": "TAKE_PROFIT_LIMIT" if limit_price else "TAKE_PROFIT",
            "side": side.upper(),
            "quantity": str(quantity),
            "takeProfitPrice": str(take_profit_price),
            "limitPrice": str(limit_price) if limit_price else None,
            "status": "NEW"
        }

    def place_trailing_stop_order(
        self,
        symbol: str,
        side: str,
        quantity: float | str | Decimal,
        trailing_offset: float | str | Decimal,
        offset_type: str = "percent"
    ) -> Dict[str, Any]:
        """
        Place a trailing stop order on Kraken.
        
        Args:
            symbol: Trading pair
            side: 'sell' for long positions (trails below price as it rises)
            quantity: Amount to sell when triggered
            trailing_offset: Distance from peak price
            offset_type: 'percent' (e.g., 2.0 = 2%) or 'absolute' (price units)
            
        Returns:
            Order response
            
        Example: 2% trailing stop on ETH at $3000 -> stop at $2940
                 If ETH rises to $3500 -> stop auto-adjusts to $3430
        """
        if self.dry_run:
            return {
                "dryRun": True, "symbol": symbol, "side": side,
                "type": "TRAILING_STOP",
                "quantity": str(quantity), "trailingOffset": str(trailing_offset),
                "offsetType": offset_type
            }
        
        self._load_asset_pairs()
        pair = self._alt_to_int.get(symbol, symbol)
        
        params = {
            "pair": pair,
            "type": side.lower(),
            "ordertype": "trailing-stop",
            "volume": self._format_order_value(quantity),
        }
        
        # Kraken trailing stop uses price as the offset
        # For percentage, we need to prefix with + or - and %
        if offset_type == "percent":
            # Kraken format: "+2%" means trail 2% below (for sells)
            params["price"] = f"+{trailing_offset}%"
        else:
            # Absolute offset in price units
            params["price"] = f"+{self._format_order_value(trailing_offset)}"
        
        res = self._private("/0/private/AddOrder", params)
        txid = res.get("txid", ["unknown"])[0]
        
        return {
            "symbol": symbol,
            "orderId": txid,
            "type": "TRAILING_STOP",
            "side": side.upper(),
            "quantity": str(quantity),
            "trailingOffset": str(trailing_offset),
            "offsetType": offset_type,
            "status": "NEW"
        }

    def place_order_with_tp_sl(
        self,
        symbol: str,
        side: str,
        quantity: float | str | Decimal,
        order_type: str = "market",
        price: float | str | Decimal | None = None,
        take_profit: float | str | Decimal | None = None,
        stop_loss: float | str | Decimal | None = None
    ) -> Dict[str, Any]:
        """
        Place an order with attached Take-Profit and/or Stop-Loss (conditional close).
        
        This is atomic - the TP/SL orders are attached to the entry and only activate
        when the entry fills. If entry is cancelled, TP/SL are also cancelled.
        
        Args:
            symbol: Trading pair
            side: 'buy' or 'sell' for entry
            quantity: Amount for entry order
            order_type: 'market' or 'limit' for entry
            price: Required if order_type is 'limit'
            take_profit: Price to take profit (optional)
            stop_loss: Price to stop loss (optional)
            
        Returns:
            Order response with attached conditional close orders
            
        Example:
            place_order_with_tp_sl('ETHUSD', 'buy', 1.0, 
                                   take_profit=3500, stop_loss=2800)
            # Buys 1 ETH, auto-sells at $3500 profit or $2800 loss
        """
        if self.dry_run:
            return {
                "dryRun": True, "symbol": symbol, "side": side,
                "type": order_type.upper(), "quantity": str(quantity),
                "price": str(price) if price else None,
                "takeProfit": str(take_profit) if take_profit else None,
                "stopLoss": str(stop_loss) if stop_loss else None,
                "conditionalClose": True
            }
        
        self._load_asset_pairs()
        pair = self._alt_to_int.get(symbol, symbol)
        
        params = {
            "pair": pair,
            "type": side.lower(),
            "ordertype": order_type.lower(),
            "volume": self._format_order_value(quantity),
        }
        
        if order_type.lower() == "limit" and price:
            params["price"] = self._format_order_value(price)
        
        # Conditional close order - opposite side when entry fills
        close_side = "sell" if side.lower() == "buy" else "buy"
        
        if take_profit and stop_loss:
            # Use stop-loss with take-profit as conditional close
            # Kraken doesn't support both in one order directly,
            # so we create entry with stop-loss close, then add separate TP
            params["close[ordertype]"] = "stop-loss"
            params["close[price]"] = self._format_order_value(stop_loss)
            
            # Submit entry with stop-loss
            res = self._private("/0/private/AddOrder", params)
            entry_txid = res.get("txid", ["unknown"])[0]
            
            # Now add take-profit as separate order
            tp_params = {
                "pair": pair,
                "type": close_side,
                "ordertype": "take-profit",
                "volume": self._format_order_value(quantity),
                "price": self._format_order_value(take_profit),
            }
            tp_res = self._private("/0/private/AddOrder", tp_params)
            tp_txid = tp_res.get("txid", ["unknown"])[0]
            
            return {
                "symbol": symbol,
                "entryOrderId": entry_txid,
                "takeProfitOrderId": tp_txid,
                "stopLossAttached": True,
                "type": order_type.upper(),
                "side": side.upper(),
                "quantity": str(quantity),
                "takeProfit": str(take_profit),
                "stopLoss": str(stop_loss),
                "status": "NEW"
            }
        
        elif take_profit:
            # Entry with take-profit close
            params["close[ordertype]"] = "take-profit"
            params["close[price]"] = self._format_order_value(take_profit)
        
        elif stop_loss:
            # Entry with stop-loss close
            params["close[ordertype]"] = "stop-loss"
            params["close[price]"] = self._format_order_value(stop_loss)
        
        res = self._private("/0/private/AddOrder", params)
        txid = res.get("txid", ["unknown"])[0]
        
        return {
            "symbol": symbol,
            "orderId": txid,
            "type": order_type.upper(),
            "side": side.upper(),
            "quantity": str(quantity),
            "takeProfit": str(take_profit) if take_profit else None,
            "stopLoss": str(stop_loss) if stop_loss else None,
            "conditionalClose": True,
            "status": "NEW"
        }

    # ══════════════════════════════════════════════════════════════════════
    # ORDER MANAGEMENT - Query, Cancel, Modify
    # ══════════════════════════════════════════════════════════════════════

    def get_open_orders(self, symbol: str | None = None) -> List[Dict[str, Any]]:
        """
        Get all open orders, optionally filtered by symbol.
        
        Returns:
            List of open orders with order details
        """
        if self.dry_run:
            return []
        
        result = self._private("/0/private/OpenOrders", {})
        orders = result.get("open", {})
        
        out = []
        for txid, order in orders.items():
            descr = order.get("descr", {})
            pair = descr.get("pair", "")
            
            # Filter by symbol if provided
            if symbol:
                self._load_asset_pairs()
                target_pair = self._alt_to_int.get(symbol, symbol)
                if pair != target_pair and pair != symbol:
                    continue
            
            out.append({
                "orderId": txid,
                "symbol": pair,
                "side": descr.get("type", "").upper(),
                "type": descr.get("ordertype", "").upper(),
                "price": descr.get("price", "0"),
                "stopPrice": descr.get("price2", None),
                "origQty": str(order.get("vol", 0)),
                "executedQty": str(order.get("vol_exec", 0)),
                "status": order.get("status", "OPEN").upper(),
                "time": order.get("opentm", 0)
            })
        
        return out

    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        Get status of a specific order.
        
        Args:
            order_id: The Kraken transaction ID (txid)
            
        Returns:
            Order details including status
        """
        if self.dry_run:
            return {"orderId": order_id, "status": "UNKNOWN", "dryRun": True}
        
        result = self._private("/0/private/QueryOrders", {"txid": order_id})
        
        if order_id not in result:
            return {"orderId": order_id, "status": "NOT_FOUND"}
        
        order = result[order_id]
        descr = order.get("descr", {})
        
        # Map Kraken status to Binance-like status
        status_map = {
            "pending": "NEW",
            "open": "NEW",
            "closed": "FILLED",
            "canceled": "CANCELED",
            "expired": "EXPIRED"
        }
        kraken_status = order.get("status", "unknown")
        
        return {
            "orderId": order_id,
            "symbol": descr.get("pair", ""),
            "side": descr.get("type", "").upper(),
            "type": descr.get("ordertype", "").upper(),
            "price": descr.get("price", "0"),
            "origQty": str(order.get("vol", 0)),
            "executedQty": str(order.get("vol_exec", 0)),
            "status": status_map.get(kraken_status, kraken_status.upper()),
            "time": order.get("opentm", 0),
            "closedTime": order.get("closetm", None)
        }

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """
        Cancel a specific order.
        
        Args:
            order_id: The Kraken transaction ID to cancel
            
        Returns:
            Cancellation result
        """
        if self.dry_run:
            return {"orderId": order_id, "status": "CANCELED", "dryRun": True}
        
        result = self._private("/0/private/CancelOrder", {"txid": order_id})
        
        return {
            "orderId": order_id,
            "status": "CANCELED",
            "count": result.get("count", 0)
        }

    def cancel_all_orders(self, symbol: str | None = None) -> Dict[str, Any]:
        """
        Cancel all open orders, optionally filtered by symbol.
        
        Args:
            symbol: If provided, only cancel orders for this pair
            
        Returns:
            Count of cancelled orders
        """
        if self.dry_run:
            return {"count": 0, "dryRun": True}
        
        if symbol:
            # Cancel orders for specific symbol by iterating
            open_orders = self.get_open_orders(symbol)
            cancelled = 0
            for order in open_orders:
                try:
                    self.cancel_order(order["orderId"])
                    cancelled += 1
                except Exception:
                    pass
            return {"count": cancelled, "symbol": symbol}
        
        # Cancel all orders
        result = self._private("/0/private/CancelAll", {})
        return {"count": result.get("count", 0)}

    def edit_order(
        self,
        order_id: str,
        quantity: float | str | Decimal | None = None,
        price: float | str | Decimal | None = None
    ) -> Dict[str, Any]:
        """
        Edit an existing order (change price or quantity without cancel/replace).
        
        Args:
            order_id: The Kraken transaction ID to edit
            quantity: New quantity (optional)
            price: New price (optional)
            
        Returns:
            New order ID (Kraken returns new txid for edited orders)
        """
        if self.dry_run:
            return {"orderId": order_id, "status": "EDITED", "dryRun": True}
        
        params = {"txid": order_id}
        
        if quantity:
            params["volume"] = self._format_order_value(quantity)
        if price:
            params["price"] = self._format_order_value(price)
        
        result = self._private("/0/private/EditOrder", params)
        
        return {
            "originalOrderId": order_id,
            "newOrderId": result.get("txid", order_id),
            "status": "EDITED"
        }

    # ══════════════════════════════════════════════════════════════════════
    # CRYPTO CONVERSION - Convert between crypto assets internally
    # ══════════════════════════════════════════════════════════════════════

    def get_available_pairs(self, base: str = None, quote: str = None) -> List[Dict[str, Any]]:
        """
        Get available trading pairs, optionally filtered by base or quote asset.
        
        Args:
            base: Filter by base asset (e.g., 'BTC', 'ETH')
            quote: Filter by quote asset (e.g., 'USD', 'ETH')
            
        Returns:
            List of pairs with base, quote, and pair name
        """
        pairs = self._load_asset_pairs()
        results = []
        
        for internal, info in pairs.items():
            alt = info.get("altname") or internal
            wsname = info.get("wsname", "")
            pair_base = info.get("base", "")
            pair_quote = info.get("quote", "")
            
            # Normalize asset names (Kraken uses X prefix for crypto, Z for fiat)
            pair_base_clean = pair_base.lstrip("XZ")
            pair_quote_clean = pair_quote.lstrip("XZ")
            
            # Also handle altname parsing (e.g., ETHBTC -> ETH, BTC)
            if not pair_base_clean and len(alt) >= 6:
                # Try to parse from altname
                for q in ['USD', 'USDC', 'USDT', 'EUR', 'GBP', 'BTC', 'XBT', 'ETH']:
                    if alt.endswith(q):
                        pair_base_clean = alt[:-len(q)]
                        pair_quote_clean = q
                        break
            
            # Normalize XBT to BTC
            if pair_base_clean == 'XBT':
                pair_base_clean = 'BTC'
            if pair_quote_clean == 'XBT':
                pair_quote_clean = 'BTC'
            
            # Apply filters
            if base and pair_base_clean.upper() != base.upper():
                continue
            if quote and pair_quote_clean.upper() != quote.upper():
                continue
            
            results.append({
                "pair": alt,
                "internal": internal,
                "base": pair_base_clean,
                "quote": pair_quote_clean,
                "wsname": wsname
            })
        
        return results

    def find_conversion_path(self, from_asset: str, to_asset: str, _depth: int = 0) -> List[Dict[str, Any]]:
        """
        Find the best path to convert from one asset to another.
        
        Returns list of trades to execute:
        - Single trade if direct pair exists
        - Two trades via USD/USDC if no direct pair
        
        Args:
            from_asset: Source asset (e.g., 'BTC')
            to_asset: Target asset (e.g., 'ETH')
            _depth: Internal recursion depth limiter
            
        Returns:
            List of {pair, side, description} for each trade needed
        """
        # 🐍 MEDUSA: Prevent infinite recursion
        if _depth > 2:
            return []
            
        from_asset = from_asset.upper()
        to_asset = to_asset.upper()
        
        if from_asset == to_asset:
            return []
        
        # Normalize BTC/XBT
        from_norm = 'XBT' if from_asset == 'BTC' else from_asset
        to_norm = 'XBT' if to_asset == 'BTC' else to_asset
        
        # 🐍 MEDUSA: Normalize Kraken quote currencies
        # ZUSD = USD (Kraken internal naming)
        quote_currencies = ['USD', 'ZUSD', 'USDT', 'USDC', 'EUR', 'ZEUR']
        from_is_quote = from_asset in quote_currencies
        to_is_quote = to_asset in quote_currencies
        
        # Normalize ZUSD -> USD for matching purposes
        from_match = 'USD' if from_asset == 'ZUSD' else from_asset
        to_match = 'USD' if to_asset == 'ZUSD' else to_asset
        
        pairs = self._load_asset_pairs()
        
        # Try direct pair: from_asset/to_asset (sell from, get to)
        for internal, info in pairs.items():
            alt = info.get("altname", internal)
            raw_base = info.get("base", "")
            raw_quote = info.get("quote", "")
            
            # 🐍 MEDUSA: Smarter Kraken name normalization
            # XXBT -> BTC (not XBT or BT)
            # XETH -> ETH
            # ZUSD -> USD
            def normalize_kraken_asset(name: str) -> str:
                # Strip leading X or Z (Kraken prefixes)
                if name.startswith('XX'):
                    name = name[2:]  # XXBT -> BT
                elif name.startswith('X') and len(name) > 3:
                    name = name[1:]  # XETH -> ETH
                elif name.startswith('Z') and name not in ('ZUSD', 'ZEUR', 'ZGBP'):
                    name = name[1:]
                # XBT/BT -> BTC
                if name in ('XBT', 'BT'):
                    name = 'BTC'
                # Normalize quote currencies
                if name == 'ZUSD':
                    name = 'USD'
                if name == 'ZEUR':
                    name = 'EUR'
                return name.upper()
            
            base = normalize_kraken_asset(raw_base)
            quote = normalize_kraken_asset(raw_quote)
            
            # Normalize quote currencies for matching
            quote_normalized = 'USD' if quote in ('ZUSD', 'USD') else quote
            
            # Direct: from_asset is base, to_asset is quote -> SELL from_asset for to_asset
            if base == from_match and quote_normalized == to_match:
                return [{
                    "pair": alt,
                    "side": "sell",
                    "description": f"Sell {from_asset} for {to_asset}",
                    "from": from_asset,
                    "to": to_asset
                }]
            
            # Inverse: to_asset is base, from_asset is quote -> BUY to_asset with from_asset
            # 🐍 MEDUSA: When from_asset is USD/ZUSD, we BUY to_asset
            if base.upper() == to_match and quote_normalized == from_match:
                return [{
                    "pair": alt,
                    "side": "buy",
                    "description": f"Buy {to_asset} with {from_asset}",
                    "from": from_asset,
                    "to": to_asset
                }]
        
        # No direct pair - route through intermediary (USD, USDC, USDT, EUR)
        # 🐍 MEDUSA: Skip intermediate routing if from_asset IS the intermediate
        for intermediate in ['USD', 'USDC', 'USDT', 'EUR']:
            # Prevent infinite recursion: don't route through self
            if from_match == intermediate or to_match == intermediate:
                continue
            path1 = self.find_conversion_path(from_asset, intermediate, _depth + 1)
            path2 = self.find_conversion_path(intermediate, to_asset, _depth + 1)
            
            if path1 and path2 and len(path1) == 1 and len(path2) == 1:
                return path1 + path2
        
        return []  # No path found

    def convert_crypto(
        self,
        from_asset: str,
        to_asset: str,
        amount: float,
        use_quote_amount: bool = False
    ) -> Dict[str, Any]:
        """
        Convert one crypto asset to another within Kraken.
        
        Automatically finds the best path:
        - Direct pair if available (e.g., ETH/BTC)
        - Via USD/USDC if no direct pair
        
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
        
        # 🚨 CRITICAL: Block stablecoin→stablecoin swaps - they ALWAYS lose to fees!
        STABLECOINS = {'USD', 'ZUSD', 'USDT', 'USDC', 'TUSD', 'DAI', 'BUSD', 'EUR', 'ZEUR'}
        if from_asset in STABLECOINS and to_asset in STABLECOINS:
            return {"error": f"Stablecoin→stablecoin swap blocked ({from_asset}→{to_asset}) - always loses to fees!"}
        
        # Find conversion path
        path = self.find_conversion_path(from_asset, to_asset)
        
        if not path:
            return {"error": f"No conversion path found from {from_asset} to {to_asset}"}
        
        # 👑 QUEEN MIND: Pre-flight validation for multi-step conversions
        # Estimate if each step will meet minimum requirements
        estimated_amount = amount
        for i, trade in enumerate(path):
            pair = trade["pair"]
            filters = self.get_symbol_filters(pair)
            ordermin = filters.get('min_qty', 0.0001)
            costmin = filters.get('min_notional', 1.20)  # Kraken costmin ~$1.20
            
            # Estimate value at this step
            try:
                price_info = self.best_price(pair)
                price = float(price_info.get("price", 0))
            except Exception:
                price = 0
            
            if trade["side"] == "sell":
                # We're selling estimated_amount
                if estimated_amount < ordermin:
                    return {
                        "error": f"Multi-hop step {i+1} would have {estimated_amount:.6f} < min {ordermin} for {pair}",
                        "failed_step": i,
                        "pair": pair
                    }
                # Estimate received amount
                if price > 0:
                    estimated_amount = estimated_amount * price
            else:
                # We're buying with estimated_amount as quote
                estimated_value = estimated_amount
                if estimated_value < costmin:
                    return {
                        "error": f"Multi-hop step {i+1} value ${estimated_value:.2f} < min ${costmin:.2f} for {pair}",
                        "failed_step": i,
                        "pair": pair
                    }
                # Estimate received amount
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
                    # Selling from_asset
                    result = self.place_market_order(pair, "sell", quantity=remaining_amount)
                else:
                    # Buying to_asset - need to estimate quantity from current price
                    if use_quote_amount and len(path) == 1:
                        # User specified amount in target terms
                        result = self.place_market_order(pair, "buy", quantity=amount)
                    else:
                        # Use quote_qty to spend remaining_amount of from_asset
                        result = self.place_market_order(pair, "buy", quote_qty=remaining_amount)
                
                # Check for errors in result
                if result.get("error"):
                    results.append({
                        "trade": trade,
                        "result": result,
                        "status": "failed",
                        "error": result.get("error")
                    })
                    return {
                        "error": f"Trade failed: {result.get('error')}",
                        "from_asset": from_asset,
                        "to_asset": to_asset,
                        "partial_results": results
                    }

                # Calculate the RECEIVED amount for this trade
                received_amount = 0.0
                if side == "sell":
                    # For SELL, we receive quote currency (base_qty * price)
                    exec_qty = float(result.get("executedQty", 0))
                    price = float(self.best_price(pair).get("price", 0))
                    if price > 0 and exec_qty > 0:
                        received_amount = exec_qty * price
                else:
                    # For BUY, we receive base currency (executedQty)
                    received_amount = float(result.get("executedQty", 0))
                
                # Store the received amount in result for verification
                result['receivedQty'] = received_amount
                
                results.append({
                    "trade": trade,
                    "result": result,
                    "status": "success",
                    "receivedQty": received_amount  # Include for easy access
                })
                
                # Update remaining amount for next trade in chain
                if side == "sell":
                    # Use the calculated received amount
                    remaining_amount = received_amount if received_amount > 0 else remaining_amount
                else:
                    # We spent remaining_amount, received the bought asset
                    exec_qty = float(result.get("executedQty", 0))
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
        pairs = self._load_asset_pairs()

        # Build conversion map
        conversions = {}

        for internal, info in pairs.items():
            base = info.get("base", "").lstrip("XZ")
            quote = info.get("quote", "").lstrip("XZ")

            # Normalize XBT -> BTC
            if base == 'XBT': base = 'BTC'
            if quote == 'XBT': quote = 'BTC'

            if not base or not quote:
                continue

            base = base.upper()
            quote = quote.upper()

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

    # ══════════════════════════════════════════════════════════════════════
    # MARGIN TRADING - Leveraged positions on Kraken
    # ══════════════════════════════════════════════════════════════════════

    def get_trade_balance(self, asset: str = "ZUSD") -> Dict[str, Any]:
        """
        Get margin/trade balance information from Kraken.

        Args:
            asset: Base asset for balance calculation (default ZUSD for USD)

        Returns:
            Dict with margin account details:
            - equity_value: Total equity (balance + unrealized P&L)
            - trade_balance: Balance available for trading (equity - margin used)
            - margin_amount: Total margin used by open positions
            - unrealized_pnl: Net unrealized profit/loss of open margin positions
            - cost_basis: Total cost basis of open margin positions
            - floating_valuation: Current floating valuation of open positions
            - free_margin: Available margin for new trades
            - margin_level: Margin level percentage (equity / margin * 100)
        """
        if self.dry_run:
            return {
                "equity_value": 10000.0,
                "trade_balance": 10000.0,
                "margin_amount": 0.0,
                "unrealized_pnl": 0.0,
                "cost_basis": 0.0,
                "floating_valuation": 0.0,
                "free_margin": 10000.0,
                "margin_level": 0.0,
                "dryRun": True
            }

        result = self._private("/0/private/TradeBalance", {"asset": asset})

        return {
            "equity_value": float(result.get("e", 0)),        # Total equity
            "trade_balance": float(result.get("tb", 0)),      # Trade balance
            "margin_amount": float(result.get("m", 0)),       # Margin used
            "unrealized_pnl": float(result.get("n", 0)),      # Unrealized P&L
            "cost_basis": float(result.get("c", 0)),           # Cost basis
            "floating_valuation": float(result.get("v", 0)),   # Floating valuation
            "free_margin": float(result.get("mf", 0)),         # Free margin
            "margin_level": float(result.get("ml", 0)),        # Margin level %
        }

    def get_open_margin_positions(self, do_calcs: bool = True) -> List[Dict[str, Any]]:
        """
        Get all open margin positions on Kraken.

        Args:
            do_calcs: If True, include profit/loss calculations (default True)

        Returns:
            List of open margin positions with details:
            - position_id: Unique position identifier
            - pair: Trading pair
            - side: 'buy' (long) or 'sell' (short)
            - volume: Position volume
            - cost: Entry cost
            - fee: Fees paid
            - current_value: Current position value (if do_calcs=True)
            - unrealized_pnl: Unrealized P&L (if do_calcs=True)
            - leverage: Leverage used
            - margin: Margin allocated
        """
        if self.dry_run:
            return []

        params = {"docalcs": "true" if do_calcs else "false"}
        result = self._private("/0/private/OpenPositions", params)

        positions = []
        for pos_id, pos_data in result.items():
            base, quote = self._pair_base_quote(pos_data.get("pair", ""))
            positions.append({
                "position_id": pos_id,
                "pair": pos_data.get("pair", ""),
                "base": base,
                "quote": quote,
                "side": pos_data.get("type", ""),          # 'buy' or 'sell'
                "order_type": pos_data.get("ordertype", ""),
                "volume": float(pos_data.get("vol", 0)),
                "volume_closed": float(pos_data.get("vol_closed", 0)),
                "cost": float(pos_data.get("cost", 0)),
                "fee": float(pos_data.get("fee", 0)),
                "current_value": float(pos_data.get("value", 0)),
                "unrealized_pnl": float(pos_data.get("net", 0)),
                "leverage": pos_data.get("leverage", "1"),
                "margin": float(pos_data.get("margin", 0)),
                "terms": pos_data.get("terms", ""),
                "open_time": float(pos_data.get("time", 0)),
                "misc": pos_data.get("misc", ""),
            })

        return positions

    def get_margin_pairs(self) -> List[Dict[str, Any]]:
        """
        Get all trading pairs that support margin trading with their leverage limits.

        Returns:
            List of pairs with margin info:
            - pair: Altname of the pair
            - internal: Internal Kraken pair name
            - leverage_buy: List of available buy leverages (e.g., [2, 3, 4, 5])
            - leverage_sell: List of available sell leverages
            - max_leverage: Maximum leverage available
        """
        pairs = self._load_asset_pairs()
        margin_pairs = []

        for internal, info in pairs.items():
            leverage_buy = info.get("leverage_buy", [])
            leverage_sell = info.get("leverage_sell", [])

            # Only include pairs that support margin (have leverage options)
            if not leverage_buy and not leverage_sell:
                continue

            alt = info.get("altname") or internal
            base = self._normalize_asset_name(info.get("base", ""))
            quote = self._normalize_asset_name(info.get("quote", ""))

            max_lev = max(leverage_buy + leverage_sell) if (leverage_buy or leverage_sell) else 1

            margin_pairs.append({
                "pair": alt,
                "internal": internal,
                "base": base,
                "quote": quote,
                "leverage_buy": leverage_buy,
                "leverage_sell": leverage_sell,
                "max_leverage": max_lev,
            })

        return margin_pairs

    def get_pair_leverage(self, symbol: str) -> Dict[str, Any]:
        """
        Get available leverage options for a specific trading pair.

        Args:
            symbol: Trading pair (e.g., 'ETHUSD', 'BTCUSD')

        Returns:
            Dict with leverage info or empty dict if pair doesn't support margin
        """
        pair, pair_info = self._resolve_pair(symbol)
        if not pair_info:
            return {}

        leverage_buy = pair_info.get("leverage_buy", [])
        leverage_sell = pair_info.get("leverage_sell", [])

        if not leverage_buy and not leverage_sell:
            return {}

        return {
            "pair": pair_info.get("altname", symbol),
            "leverage_buy": leverage_buy,
            "leverage_sell": leverage_sell,
            "max_leverage": max(leverage_buy + leverage_sell) if (leverage_buy or leverage_sell) else 1,
            "margin_supported": True,
        }

    def place_margin_order(
        self,
        symbol: str,
        side: str,
        quantity: float | str | Decimal,
        leverage: int | str,
        order_type: str = "market",
        price: float | str | Decimal | None = None,
        take_profit: float | str | Decimal | None = None,
        stop_loss: float | str | Decimal | None = None,
        post_only: bool = False,
        reduce_only: bool = False,
    ) -> Dict[str, Any]:
        """
        Place a margin (leveraged) order on Kraken.

        This opens a leveraged position using borrowed funds. For example, with 3x
        leverage on a $100 trade, you put up ~$33 margin and borrow ~$67.

        Args:
            symbol: Trading pair (e.g., 'ETHUSD', 'BTCUSD')
            side: 'buy' for long, 'sell' for short
            quantity: Amount of base asset to trade
            leverage: Leverage multiplier (e.g., 2, 3, 5). Must be supported by pair.
            order_type: 'market' or 'limit'
            price: Limit price (required if order_type='limit')
            take_profit: Attach take-profit at this price (optional)
            stop_loss: Attach stop-loss at this price (optional)
            post_only: For limit orders, ensure maker-only (0.16% fee vs 0.26%)
            reduce_only: Only reduce an existing position, don't open new one

        Returns:
            Binance-compatible order response with margin details

        Example:
            # Long 0.5 ETH at 3x leverage
            place_margin_order('ETHUSD', 'buy', 0.5, leverage=3)

            # Short 0.01 BTC at 2x with stop-loss
            place_margin_order('BTCUSD', 'sell', 0.01, leverage=2, stop_loss=105000)
        """
        if self.dry_run:
            return {
                "dryRun": True, "symbol": symbol, "side": side,
                "type": order_type.upper(), "quantity": str(quantity),
                "leverage": str(leverage), "price": str(price) if price else None,
                "takeProfit": str(take_profit) if take_profit else None,
                "stopLoss": str(stop_loss) if stop_loss else None,
                "margin": True
            }

        # Resolve pair and validate
        pair, pair_info = self._resolve_pair(symbol)
        if not pair or not pair_info:
            raise RuntimeError(f"Unknown Kraken trading pair: {symbol}")

        # Validate leverage is supported for this pair
        lev = int(leverage)
        if side.lower() == "buy":
            valid_levs = pair_info.get("leverage_buy", [])
        else:
            valid_levs = pair_info.get("leverage_sell", [])

        if not valid_levs:
            raise RuntimeError(f"Margin trading not supported for {symbol}")
        if lev not in valid_levs:
            raise RuntimeError(
                f"Leverage {lev}x not supported for {symbol} ({side}). "
                f"Available: {valid_levs}"
            )

        # Validate minimum volume
        ordermin = float(pair_info.get("ordermin", 0.0001))
        lot_decimals = int(pair_info.get("lot_decimals", 8))
        vol = round(float(quantity), lot_decimals)

        if vol < ordermin:
            return {
                "error": "volume_minimum",
                "symbol": symbol,
                "volume": vol,
                "ordermin": ordermin,
                "margin": True
            }

        # Build order params
        params = {
            "pair": pair,
            "type": side.lower(),
            "ordertype": order_type.lower(),
            "volume": self._format_order_value(vol),
            "leverage": str(lev),
        }

        # Price for limit orders
        if order_type.lower() == "limit" and price:
            params["price"] = self._format_order_value(price)

        # Order flags
        oflags = []
        if post_only and order_type.lower() == "limit":
            oflags.append("post")
        if reduce_only:
            oflags.append("nompp")
        if oflags:
            params["oflags"] = ",".join(oflags)

        # Conditional close orders (TP/SL attached to margin position)
        if stop_loss and take_profit:
            # Attach stop-loss as conditional close, add TP as separate order
            params["close[ordertype]"] = "stop-loss"
            params["close[price]"] = self._format_order_value(stop_loss)

            res = self._private("/0/private/AddOrder", params)
            entry_txid = res.get("txid", ["unknown"])[0]

            # Add take-profit as separate margin order
            close_side = "sell" if side.lower() == "buy" else "buy"
            tp_params = {
                "pair": pair,
                "type": close_side,
                "ordertype": "take-profit",
                "volume": self._format_order_value(vol),
                "price": self._format_order_value(take_profit),
                "leverage": str(lev),
                "reduce_only": "true",
            }
            tp_res = self._private("/0/private/AddOrder", tp_params)
            tp_txid = tp_res.get("txid", ["unknown"])[0]

            return {
                "symbol": symbol,
                "entryOrderId": entry_txid,
                "takeProfitOrderId": tp_txid,
                "stopLossAttached": True,
                "type": order_type.upper(),
                "side": side.upper(),
                "quantity": str(vol),
                "leverage": str(lev),
                "takeProfit": str(take_profit),
                "stopLoss": str(stop_loss),
                "status": "NEW",
                "margin": True
            }

        elif take_profit:
            params["close[ordertype]"] = "take-profit"
            params["close[price]"] = self._format_order_value(take_profit)
        elif stop_loss:
            params["close[ordertype]"] = "stop-loss"
            params["close[price]"] = self._format_order_value(stop_loss)

        res = self._private("/0/private/AddOrder", params)
        txid = res.get("txid", ["unknown"])[0]

        filled = order_type.lower() == "market"

        return {
            "symbol": symbol,
            "orderId": txid,
            "clientOrderId": str(time.time()),
            "transactTime": int(time.time() * 1000),
            "price": str(price) if price else "0.00000000",
            "origQty": str(vol),
            "executedQty": str(vol) if filled else "0",
            "status": "FILLED" if filled else "NEW",
            "timeInForce": "GTC",
            "type": order_type.upper(),
            "side": side.upper(),
            "leverage": str(lev),
            "takeProfit": str(take_profit) if take_profit else None,
            "stopLoss": str(stop_loss) if stop_loss else None,
            "margin": True
        }

    def close_margin_position(
        self,
        symbol: str,
        side: str,
        volume: float | str | Decimal | None = None,
        order_type: str = "market",
        price: float | str | Decimal | None = None,
        leverage: int | str | None = None,
    ) -> Dict[str, Any]:
        """
        Close an open margin position by placing an opposing order.

        To close a long margin position, place a leveraged sell.
        To close a short margin position, place a leveraged buy.

        Args:
            symbol: Trading pair
            side: 'sell' to close a long, 'buy' to close a short
            volume: Amount to close (None = close entire position for this pair)
            order_type: 'market' or 'limit'
            price: Limit price (required if order_type='limit')
            leverage: Leverage (should match the open position's leverage)

        Returns:
            Order response
        """
        if self.dry_run:
            return {
                "dryRun": True, "symbol": symbol, "side": side,
                "type": order_type.upper(), "volume": str(volume),
                "margin_close": True
            }

        # If no volume specified, find the open position volume
        if volume is None:
            positions = self.get_open_margin_positions(do_calcs=False)
            pair, _ = self._resolve_pair(symbol)
            for pos in positions:
                if pos["pair"] == pair and pos["side"] != side.lower():
                    remaining = pos["volume"] - pos["volume_closed"]
                    if remaining > 0:
                        volume = remaining
                        if leverage is None:
                            leverage = pos["leverage"]
                        break
            if volume is None:
                return {"error": "no_position", "symbol": symbol}

        pair, pair_info = self._resolve_pair(symbol)
        if not pair:
            raise RuntimeError(f"Unknown Kraken trading pair: {symbol}")

        lot_decimals = int(pair_info.get("lot_decimals", 8)) if pair_info else 8
        vol = round(float(volume), lot_decimals)

        params = {
            "pair": pair,
            "type": side.lower(),
            "ordertype": order_type.lower(),
            "volume": self._format_order_value(vol),
        }

        if leverage:
            params["leverage"] = str(int(leverage) if str(leverage).isdigit() else leverage)

        if order_type.lower() == "limit" and price:
            params["price"] = self._format_order_value(price)

        # Add reduce_only flag to ensure we only close, never open new position
        params["reduce_only"] = "true"

        res = self._private("/0/private/AddOrder", params)
        txid = res.get("txid", ["unknown"])[0]

        return {
            "symbol": symbol,
            "orderId": txid,
            "type": order_type.upper(),
            "side": side.upper(),
            "quantity": str(vol),
            "leverage": str(leverage) if leverage else None,
            "status": "FILLED" if order_type.lower() == "market" else "NEW",
            "margin_close": True
        }


# ══════════════════════════════════════════════════════════════════════════════
# SINGLETON INSTANCE - for easy import
# ══════════════════════════════════════════════════════════════════════════════
_kraken_instance: KrakenClient = None

def get_kraken_client() -> KrakenClient:
    """Get singleton Kraken client instance."""
    global _kraken_instance
    if _kraken_instance is None:
        _kraken_instance = KrakenClient()
    return _kraken_instance
