import os, time, json, math, hmac, hashlib, base64
from typing import Dict, Any, List, Tuple
from decimal import Decimal

import requests

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

KRAKEN_BASE = "https://api.kraken.com"

ASSETPAIR_CACHE_TTL = 300  # seconds

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
        if self.api_key:
            self.session.headers.update({"API-Key": self.api_key})

        self._pairs_cache: Dict[str, Any] = {}
        self._pairs_cache_time: float = 0.0
        # Map altname -> internal pair key used by ticker results
        self._alt_to_int: Dict[str, str] = {}
        self._int_to_alt: Dict[str, str] = {}

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

    def _private(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        if self.dry_run:
            raise RuntimeError("Private Kraken endpoint used in dry-run. Provide balances via env or disable dry-run.")
        if not self.api_key or not self.api_secret:
            raise RuntimeError("Missing KRAKEN_API_KEY / KRAKEN_API_SECRET")
        data = dict(data)
        data["nonce"] = str(int(time.time() * 1000))
        headers = {
            "API-Key": self.api_key,
            "API-Sign": self._kraken_sign(path, data)
        }
        url = f"{self.base}{path}"
        r = self.session.post(url, data=data, headers=headers, timeout=15)
        r.raise_for_status()
        res = r.json()
        if res.get("error"):
            raise RuntimeError(f"Kraken error: {res['error']}")
        return res.get("result", {})

    # ──────────────────────────────────────────────────────────────────────
    # Public helpers and Binance-like interface
    # ──────────────────────────────────────────────────────────────────────
    def _load_asset_pairs(self, force: bool = False) -> Dict[str, Any]:
        if not force and time.time() - self._pairs_cache_time < ASSETPAIR_CACHE_TTL and self._pairs_cache:
            return self._pairs_cache
        r = self.session.get(f"{self.base}/0/public/AssetPairs", timeout=20)
        r.raise_for_status()
        data = r.json()
        if data.get("error"):
            raise RuntimeError(f"Kraken AssetPairs error: {data['error']}")
        pairs = data.get("result", {})
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

    def _ticker(self, altnames: List[str]) -> Dict[str, Any]:
        if not altnames:
            return {}
        # Kraken expects internal pair names, not altnames; map
        self._load_asset_pairs()
        internal_names = [self._alt_to_int.get(a, a) for a in altnames]
        # Batch request (Kraken accepts comma-separated list)
        pairs_param = ",".join(internal_names)
        r = self.session.get(f"{self.base}/0/public/Ticker", params={"pair": pairs_param}, timeout=20)
        r.raise_for_status()
        data = r.json()
        if data.get("error"):
            raise RuntimeError(f"Kraken Ticker error: {data['error']}")
        return data.get("result", {})

    def get_24h_tickers(self) -> list:
        """
        Return a list of Binance-like 24h ticker dicts with fields:
        - symbol: altname like "ETHUSDC"
        - lastPrice, priceChangePercent, quoteVolume
        """
        pairs = self._load_asset_pairs()
        # Focus on common quote assets
        alts: List[str] = []
        for internal, info in pairs.items():
            alt = info.get("altname") or internal
            wsname = info.get("wsname", "")
            # Prefer quotes that align with Aureon config
            # Expanded to include more Kraken pairs if needed, but keeping focus on liquid quotes
            if any(alt.endswith(q) for q in ["USDC", "USDT", "USD", "EUR", "BTC", "XBT", "ETH", "GBP", "AUD", "CAD", "JPY"]):
                alts.append(alt)
            elif "/" in wsname and wsname.split("/")[-1] in ["USDC", "USDT", "USD", "EUR", "BTC", "XBT", "ETH", "GBP", "AUD", "CAD", "JPY"]:
                alts.append(alt)
        # De-duplicate and trim overly large lists to be kind to Kraken API
        alts = sorted(set(alts))
        out = []
        # Batch in chunks of 40
        for i in range(0, len(alts), 40):
            chunk = alts[i:i+40]
            result = self._ticker(chunk)
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
        res = self._ticker([symbol])
        # Only one expected
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
        # If not dry-run, try private Balance
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
        return {"balances": balances}

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
        
        # Resolve pair
        self._load_asset_pairs()
        pair = self._alt_to_int.get(symbol, symbol)
        
        params = {
            "pair": pair,
            "type": side.lower(),
            "ordertype": "market",
        }
        
        if quantity:
            params["volume"] = self._format_order_value(quantity)
        elif quote_qty:
            # Estimate volume from quote quantity
            price_info = self.best_price(symbol)
            price = float(price_info.get("price", 0))
            if price <= 0:
                raise RuntimeError(f"Cannot estimate volume for quote_qty: price is {price}")
            vol = float(quote_qty) / price
            params["volume"] = self._format_order_value(vol)
        else:
            raise ValueError("Must provide quantity or quote_qty")

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
        if asset.upper() == quote.upper():
            return amount
        pair = f"{asset.upper()}{quote.upper()}"
        inv_pair = f"{quote.upper()}{asset.upper()}"
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

    def compute_order_fees_in_quote(self, order: Dict[str, Any], primary_quote: str) -> float:
        # No fill info in dry-run; return 0 to let orchestrator use configured taker fee model if any
        return 0.0
