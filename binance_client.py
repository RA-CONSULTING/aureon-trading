import os, time, hmac, hashlib, requests, json
from decimal import Decimal, InvalidOperation, ROUND_DOWN, ROUND_UP
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass
from typing import Dict, Any, Set

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
        if self.api_key:
            self.session.headers.update({"X-MBX-APIKEY": self.api_key})
        
        # Cache allowed pairs for UK mode
        self._allowed_pairs_cache: Set[str] = set()
        self._cache_timestamp: float = 0
        self._symbol_filters_cache: dict[str, dict[str, float]] = {}
        
        # Server time offset for clock sync (fixes Windows clock drift)
        self._time_offset_ms: int = 0
        self._time_sync_timestamp: float = 0
        self._sync_server_time()  # Auto-sync on init
    
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

    def _signed_request(self, method: str, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        params["timestamp"] = self._get_server_timestamp()  # Use synced timestamp
        params["recvWindow"] = 60000  # Increased to 60 seconds for network latency
        signature = self._sign(params)
        params["signature"] = signature
        url = f"{self.base}{path}"
        resp = self.session.request(method, url, params=params if method == "GET" else None, data=params if method != "GET" else None)
        if resp.status_code != 200:
            # If timestamp error, try re-syncing once
            if resp.status_code == 400 and "-1021" in resp.text:
                self._sync_server_time()
                params["timestamp"] = self._get_server_timestamp()
                signature = self._sign(params)
                params["signature"] = signature
                resp = self.session.request(method, url, params=params if method == "GET" else None, data=params if method != "GET" else None)
                if resp.status_code == 200:
                    return resp.json()
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
        # 🇬🇧 UK Mode: Check restrictions before attempting trade
        if self.uk_mode:
            can_trade, reason = self.can_trade_symbol(symbol)
            if not can_trade:
                return {
                    "rejected": True,
                    "symbol": symbol,
                    "side": side,
                    "reason": reason,
                    "uk_restricted": True
                }
        
        if self.dry_run:
            return {"dryRun": True, "symbol": symbol, "side": side, "quantity": quantity, "quoteQty": quote_qty}
        
        params = {"symbol": symbol, "side": side.upper(), "type": "MARKET", "newOrderRespType": "FULL"}
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
            params["quantity"] = self._format_order_value(adjusted_qty)
        elif quote_qty:
            # Adjust quote quantity to match symbol's quote precision
            adjusted_quote = self.adjust_quote_qty(symbol, float(quote_qty))
            params["quoteOrderQty"] = self._format_order_value(adjusted_quote)
        else:
            raise ValueError("Must provide either quantity or quote_qty")
            
        return self._signed_request("POST", "/api/v3/order", params)

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

    def get_my_trades(self, symbol: str, limit: int = 500) -> list:
        """Get trade history for a symbol.
        
        Returns list of trades with entry prices, quantities, fees etc.
        Used to calculate real cost basis for positions.
        """
        params = {"symbol": symbol, "limit": limit}
        try:
            return self._signed_request("GET", "/api/v3/myTrades", params)
        except Exception as e:
            print(f"⚠️ Failed to get trade history for {symbol}: {e}")
            return []
    
    def get_all_my_trades(self, symbols: list = None, limit_per_symbol: int = 100) -> Dict[str, list]:
        """Get trade history for multiple symbols.
        
        Returns dict: {symbol: [trades]}
        """
        if not symbols:
            # Get symbols from current balances
            account = self.account()
            balances = account.get('balances', [])
            symbols = []
            for b in balances:
                if float(b.get('free', 0)) > 0 or float(b.get('locked', 0)) > 0:
                    asset = b['asset']
                    # Try common quote currencies
                    for quote in ['USDC', 'USDT', 'EUR', 'GBP']:
                        symbols.append(f"{asset}{quote}")
        
        all_trades = {}
        for symbol in symbols:
            try:
                trades = self.get_my_trades(symbol, limit_per_symbol)
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
