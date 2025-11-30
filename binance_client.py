import os, time, hmac, hashlib, requests, json
from decimal import Decimal, InvalidOperation
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass
from typing import Dict, Any

BINANCE_MAINNET = "https://api.binance.com"
BINANCE_TESTNET = "https://testnet.binance.vision"

class BinanceClient:
    def __init__(self):
        # Support common env var aliases from TS/Node side as well
        self.api_key = os.getenv("BINANCE_API_KEY") or os.getenv("BINANCE_KEY") or ""
        self.api_secret = os.getenv("BINANCE_API_SECRET") or os.getenv("BINANCE_SECRET") or ""
        self.use_testnet = (os.getenv("BINANCE_USE_TESTNET") or os.getenv("BINANCE_TESTNET") or "true").lower() == "true"
        self.dry_run = os.getenv("BINANCE_DRY_RUN", "true").lower() == "true"
        
        # Only require API keys if NOT in dry-run mode
        if not self.dry_run and (not self.api_key or not self.api_secret):
            raise ValueError("Missing BINANCE_API_KEY or BINANCE_API_SECRET in environment")
        
        self.base = BINANCE_TESTNET if self.use_testnet else BINANCE_MAINNET
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({"X-MBX-APIKEY": self.api_key})

    def _sign(self, params: Dict[str, Any]) -> str:
        query = "&".join(f"{k}={params[k]}" for k in params)
        signature = hmac.new(self.api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()
        return signature

    def _signed_request(self, method: str, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        params["timestamp"] = int(time.time() * 1000)
        params["recvWindow"] = 60000  # Increased to 60 seconds for network latency
        signature = self._sign(params)
        params["signature"] = signature
        url = f"{self.base}{path}"
        resp = self.session.request(method, url, params=params if method == "GET" else None, data=params if method != "GET" else None)
        if resp.status_code != 200:
            raise RuntimeError(f"Binance error {resp.status_code}: {resp.text}")
        return resp.json()

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
        if symbol:
            params["symbol"] = symbol
        r = self.session.get(f"{self.base}/api/v3/exchangeInfo", params=params)
        return r.json()

    def account(self) -> Dict[str, Any]:
        return self._signed_request("GET", "/api/v3/account", {})

    def get_free_balance(self, asset: str) -> float:
        acct = self.account()
        for bal in acct.get("balances", []):
            if bal["asset"] == asset:
                return float(bal["free"])
        return 0.0

    def _format_order_value(self, value: float | str | Decimal | None) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            return value
        try:
            dec_value = Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise ValueError(f"Invalid order value: {value}") from exc
        formatted = format(dec_value, 'f')
        if '.' in formatted:
            formatted = formatted.rstrip('0').rstrip('.')
        return formatted or '0'

    def place_market_order(self, symbol: str, side: str, quantity: float | str | Decimal | None = None, quote_qty: float | str | Decimal | None = None) -> Dict[str, Any]:
        if self.dry_run:
            return {"dryRun": True, "symbol": symbol, "side": side, "quantity": quantity, "quoteQty": quote_qty}
        
        params = {"symbol": symbol, "side": side.upper(), "type": "MARKET", "newOrderRespType": "FULL"}
        if quantity:
            params["quantity"] = self._format_order_value(quantity)
        elif quote_qty:
            params["quoteOrderQty"] = self._format_order_value(quote_qty)
        else:
            raise ValueError("Must provide either quantity or quote_qty")
            
        return self._signed_request("POST", "/api/v3/order", params)

    def best_price(self, symbol: str) -> Dict[str, Any]:
        r = self.session.get(f"{self.base}/api/v3/ticker/price", params={"symbol": symbol})
        return r.json()
    
    def convert_to_quote(self, asset: str, amount: float, quote: str) -> float:
        """Convert an asset amount into quote using spot ticker price if available."""
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


def safe_trade(symbol: str = None, side: str = "BUY") -> Dict[str, Any]:
    symbol = symbol or os.getenv("BINANCE_SYMBOL", "BTCUSDT")
    client = BinanceClient()
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
