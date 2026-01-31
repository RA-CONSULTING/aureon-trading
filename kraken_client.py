from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import time
import json
import hmac
import base64
import hashlib
import threading
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

import requests

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

try:
    from rate_limiter import TokenBucket, TTLCache
except Exception:
    TokenBucket = None
    TTLCache = None


class KrakenClient:
    """Minimal Kraken REST client with public + private helpers."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        dry_run: Optional[bool] = None,
        base_url: Optional[str] = None,
    ) -> None:
        self.api_key = api_key or os.getenv("KRAKEN_API_KEY") or os.getenv("KRAKEN_KEY") or ""
        self.api_secret = (
            api_secret
            or os.getenv("KRAKEN_API_SECRET")
            or os.getenv("KRAKEN_PRIVATE_KEY")
            or os.getenv("KRAKEN_SECRET")
            or ""
        )
        if dry_run is None:
            dry_run = os.getenv("KRAKEN_DRY_RUN", "false").lower() == "true"
        self.dry_run = bool(dry_run)

        self.base = base_url or os.getenv("KRAKEN_API_BASE", "https://api.kraken.com")
        self.timeout = float(os.getenv("KRAKEN_TIMEOUT", "10"))
        self.session = requests.Session()

        self._alt_to_int: Dict[str, str] = {}
        self._int_to_alt: Dict[str, str] = {}
        self._asset_pairs_cache_ts = 0.0
        self._asset_pairs_cache_ttl = float(os.getenv("KRAKEN_ASSET_PAIRS_TTL", "3600"))

        self._nonce_path = os.getenv("KRAKEN_NONCE_PATH", "kraken_nonce.json")
        self._nonce_lock = threading.Lock()

        try:
            rate = float(os.getenv("KRAKEN_RATE_PER_SECOND", "1.0"))
        except Exception:
            rate = 1.0
        try:
            burst = float(os.getenv("KRAKEN_BURST_CAPACITY", str(max(1.0, rate))))
        except Exception:
            burst = max(1.0, rate)
        self._rate_limiter = TokenBucket(rate=rate, capacity=burst, name="kraken") if TokenBucket else None
        self._request_cache = TTLCache(default_ttl=float(os.getenv("KRAKEN_CACHE_TTL", "1.0"))) if TTLCache else None

    def _next_nonce(self) -> int:
        """Return a strictly increasing nonce (persisted to disk)."""
        with self._nonce_lock:
            last_nonce = 0
            try:
                if os.path.exists(self._nonce_path):
                    with open(self._nonce_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    last_nonce = int(data.get("last_nonce", 0))
            except Exception:
                last_nonce = 0

            nonce = int(time.time() * 1_000_000)
            if nonce <= last_nonce:
                nonce = last_nonce + 1

            try:
                with open(self._nonce_path, "w", encoding="utf-8") as f:
                    json.dump({"last_nonce": nonce, "updated": time.time()}, f)
            except Exception:
                pass

            return nonce

    def _sign(self, urlpath: str, data: Dict[str, Any]) -> str:
        postdata = urlencode(data)
        encoded = (str(data["nonce"]) + postdata).encode()
        message = urlpath.encode() + hashlib.sha256(encoded).digest()
        try:
            secret = base64.b64decode(self.api_secret)
        except Exception:
            secret = self.api_secret.encode()
        signature = hmac.new(secret, message, hashlib.sha512)
        return base64.b64encode(signature.digest()).decode()

    def _request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if self._rate_limiter:
            self._rate_limiter.wait()
        url = f"{self.base}{path}"
        if method == "GET":
            res = self.session.get(url, params=params, timeout=self.timeout)
        else:
            res = self.session.post(url, data=params, timeout=self.timeout)
        data = res.json()
        if not isinstance(data, dict):
            raise RuntimeError(f"Kraken API unexpected response: {data}")
        if data.get("error"):
            raise RuntimeError(f"Kraken API error: {data['error']}")
        return data.get("result", {}) or {}

    def _public(self, path: str, params: Optional[Dict[str, Any]] = None, cache_key: Optional[str] = None, cache_ttl: Optional[float] = None) -> Dict[str, Any]:
        if cache_key and self._request_cache:
            cached = self._request_cache.get(cache_key)
            if cached is not None:
                return cached
        result = self._request("GET", path, params=params)
        if cache_key and self._request_cache:
            self._request_cache.set(cache_key, result, ttl=cache_ttl)
        return result

    def _private(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if self.dry_run:
            return {}
        if not self.api_key or not self.api_secret:
            raise ValueError("Missing KRAKEN_API_KEY or KRAKEN_API_SECRET in environment")
        params = params or {}
        params["nonce"] = self._next_nonce()
        headers = {
            "API-Key": self.api_key,
            "API-Sign": self._sign(path, params),
        }
        if self._rate_limiter:
            self._rate_limiter.wait()
        url = f"{self.base}{path}"
        res = self.session.post(url, data=params, headers=headers, timeout=self.timeout)
        data = res.json()
        if not isinstance(data, dict):
            raise RuntimeError(f"Kraken API unexpected response: {data}")
        if data.get("error"):
            raise RuntimeError(f"Kraken API error: {data['error']}")
        return data.get("result", {}) or {}

    def _normalize_asset(self, asset: str) -> str:
        asset = asset.upper()
        if asset.startswith(("X", "Z")) and len(asset) > 3:
            asset = asset[1:]
        if asset in ("XBT", "XXBT"):
            return "BTC"
        return asset

    def _normalize_alt(self, symbol: str) -> str:
        alt = symbol.replace("/", "").upper()
        base_map = {"BTC": "XBT", "DOGE": "XDG"}
        for src, dst in base_map.items():
            if alt.startswith(src):
                alt = dst + alt[len(src):]
                break
        return alt

    def _load_asset_pairs(self, force: bool = False) -> None:
        now = time.time()
        if not force and self._alt_to_int and (now - self._asset_pairs_cache_ts) < self._asset_pairs_cache_ttl:
            return
        result = self._public("/0/public/AssetPairs", cache_key="asset_pairs", cache_ttl=self._asset_pairs_cache_ttl)
        alt_to_int: Dict[str, str] = {}
        int_to_alt: Dict[str, str] = {}
        for pair_name, info in result.items():
            altname = info.get("altname") or pair_name
            alt_to_int[altname] = pair_name
            int_to_alt[pair_name] = altname
        self._alt_to_int = alt_to_int
        self._int_to_alt = int_to_alt
        self._asset_pairs_cache_ts = now

    def _resolve_pair(self, symbol: str) -> Tuple[str, str]:
        self._load_asset_pairs()
        alt = self._normalize_alt(symbol)
        raw = symbol.replace("/", "").upper()
        if alt in self._alt_to_int:
            return alt, self._alt_to_int[alt]
        if raw in self._alt_to_int:
            return raw, self._alt_to_int[raw]
        if raw in self._int_to_alt:
            return self._int_to_alt[raw], raw
        return alt, alt

    def _ticker(self, symbols: List[str]) -> Dict[str, Any]:
        if not symbols:
            return {}
        pairs = []
        for s in symbols:
            _, pair = self._resolve_pair(s)
            pairs.append(pair)
        params = {"pair": ",".join(pairs)}
        return self._public("/0/public/Ticker", params=params)

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        try:
            result = self._ticker([symbol])
            if not result:
                return {"price": 0.0, "bid": 0.0, "ask": 0.0}
            _, data = next(iter(result.items()))
            bid = float(data.get("b", [0])[0])
            ask = float(data.get("a", [0])[0])
            last = float(data.get("c", [0])[0])
            return {"price": last, "bid": bid, "ask": ask}
        except Exception:
            return {"price": 0.0, "bid": 0.0, "ask": 0.0}

    def _format_ticker(self, symbol: str, data: Dict[str, Any]) -> Dict[str, Any]:
        last = float(data.get("c", [0])[0] or 0)
        bid = float(data.get("b", [0])[0] or 0)
        ask = float(data.get("a", [0])[0] or 0)
        vwap = float((data.get("p", [0, 0]) or [0, 0])[1] or 0)
        volume = float((data.get("v", [0, 0]) or [0, 0])[1] or 0)
        open_price = float(data.get("o", 0) or 0)
        change_pct = ((last - open_price) / open_price * 100) if open_price > 0 else 0.0
        quote_volume = vwap * volume if vwap and volume else 0.0
        return {
            "symbol": symbol,
            "lastPrice": last,
            "bidPrice": bid,
            "askPrice": ask,
            "priceChangePercent": change_pct,
            "quoteVolume": quote_volume,
            "volume": volume,
            "vwap": vwap,
            "openPrice": open_price,
        }

    def get_24h_ticker(self, symbol: str) -> Dict[str, Any]:
        try:
            result = self._ticker([symbol])
            if not result:
                return {}
            key, data = next(iter(result.items()))
            alt = self._int_to_alt.get(key, symbol.replace("/", "").upper())
            return self._format_ticker(alt, data)
        except Exception:
            return {}

    def get_24h_tickers(self) -> List[Dict[str, Any]]:
        try:
            self._load_asset_pairs()
            alts = list(self._alt_to_int.keys())
            if not alts:
                return []
            chunk_size = int(os.getenv("KRAKEN_TICKER_CHUNK_SIZE", "50"))
            tickers: List[Dict[str, Any]] = []
            for i in range(0, len(alts), chunk_size):
                chunk = alts[i:i + chunk_size]
                result = self._ticker(chunk)
                for pair_name, data in result.items():
                    alt = self._int_to_alt.get(pair_name, pair_name)
                    tickers.append(self._format_ticker(alt, data))
            return tickers
        except Exception:
            return []

    def get_account_balance(self) -> Dict[str, Any]:
        if self.dry_run:
            return {}
        return self._private("/0/private/Balance", {})

    def get_balance(self) -> Dict[str, float]:
        raw = self.get_account_balance()
        balances: Dict[str, float] = {}
        for asset, amount in raw.items():
            try:
                balances[self._normalize_asset(asset)] = float(amount)
            except Exception:
                continue
        return balances

    def account(self) -> Dict[str, Any]:
        balances = []
        raw = self.get_account_balance()
        for asset, amount in raw.items():
            balances.append(
                {
                    "asset": self._normalize_asset(asset),
                    "free": str(amount),
                    "locked": "0",
                }
            )
        return {"balances": balances, "canTrade": True}

    def get_trades_history(self, ofs: int = 0, include_count: bool = False) -> Dict[str, Any]:
        if self.dry_run:
            return {} if not include_count else {"trades": {}, "count": 0}
        result = self._private("/0/private/TradesHistory", {"ofs": ofs})
        trades = result.get("trades", {}) if isinstance(result, dict) else {}
        if include_count:
            return {"trades": trades, "count": result.get("count", len(trades))}
        return trades

    def get_ledgers(self, ofs: int = 0, ledger_type: Optional[str] = None) -> Dict[str, Any]:
        if self.dry_run:
            return {}
        params: Dict[str, Any] = {"ofs": ofs}
        if ledger_type:
            params["type"] = ledger_type
        result = self._private("/0/private/Ledgers", params)
        return result.get("ledger", {}) if isinstance(result, dict) else {}

    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        if self.dry_run:
            return []
        params: Dict[str, Any] = {"trades": True}
        result = self._private("/0/private/OpenOrders", params)
        orders = result.get("open", {}) if isinstance(result, dict) else {}
        items: List[Dict[str, Any]] = []
        norm_symbol = self._normalize_alt(symbol) if symbol else ""
        norm_internal = self._resolve_pair(symbol)[1] if symbol else ""
        for txid, order in orders.items():
            descr = order.get("descr", {}) if isinstance(order, dict) else {}
            pair = descr.get("pair", "")
            if (norm_symbol or norm_internal) and pair:
                pair_norm = pair.replace("/", "").upper()
                if pair_norm not in (norm_symbol, norm_internal) and norm_symbol not in pair_norm:
                    continue
            items.append(
                {
                    "orderId": txid,
                    "symbol": pair,
                    "side": descr.get("type", ""),
                    "price": order.get("price"),
                    "origQty": order.get("vol"),
                    "executedQty": order.get("vol_exec"),
                    "status": order.get("status", "open"),
                    "raw": order,
                }
            )
        return items

    def place_market_order(
        self,
        symbol: str,
        side: str,
        quantity: Optional[float] = None,
        quote_qty: Optional[float] = None,
    ) -> Dict[str, Any]:
        side = side.lower()
        if self.dry_run:
            return {
                "dryRun": True,
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "quoteQty": quote_qty,
            }
        alt, _ = self._resolve_pair(symbol)
        params: Dict[str, Any] = {
            "pair": alt,
            "type": side,
            "ordertype": "market",
        }
        if quantity is not None:
            params["volume"] = str(quantity)
        elif quote_qty is not None:
            params["volume"] = str(quote_qty)
            params["oflags"] = "viqc"
        else:
            raise ValueError("Either quantity or quote_qty must be provided")
        result = self._private("/0/private/AddOrder", params)
        return {
            "symbol": symbol,
            "side": side,
            "status": "NEW",
            "txid": result.get("txid"),
            "descr": result.get("descr"),
            "raw": result,
        }
