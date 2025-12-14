import os
import requests
import time
import logging
from typing import Dict, Any, List, Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)

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

        if self.use_paper:
            self.base_url = "https://paper-api.alpaca.markets"
        else:
            self.base_url = "https://api.alpaca.markets"
            
        # Data API URL (Crypto)
        self.data_url = "https://data.alpaca.markets"
        
        self.session = requests.Session()
        if self.api_key and self.secret_key:
            self.session.headers.update({
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.secret_key
            })
        else:
            logger.warning("Alpaca API keys not found in environment variables.")

    def _request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None, base_url: str = None) -> Any:
        url = f"{base_url or self.base_url}{endpoint}"
        try:
            resp = self.session.request(method, url, params=params, json=data, timeout=10)
            if not resp.ok:
                logger.error(f"Alpaca API Error {resp.status_code}: {resp.text}")
                return {}
            return resp.json()
        except Exception as e:
            logger.error(f"Alpaca Request Failed: {e}")
            return {}

    def get_account(self) -> Dict[str, Any]:
        """Get account details."""
        return self._request("GET", "/v2/account")

    def get_positions(self) -> List[Dict[str, Any]]:
        """Get open positions."""
        return self._request("GET", "/v2/positions")

    def get_position(self, symbol: str) -> Dict[str, Any]:
        """Get position for a specific symbol."""
        return self._request("GET", f"/v2/positions/{symbol}")

    def get_clock(self) -> Dict[str, Any]:
        """Get market clock."""
        return self._request("GET", "/v2/clock")

    def place_order(self, symbol: str, qty: float, side: str, type: str = "market", time_in_force: str = "gtc") -> Dict[str, Any]:
        """Place an order."""
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
        return self._request("POST", "/v2/orders", data=data)

    def get_crypto_bars(self, symbols: List[str], timeframe: str = "1Min", limit: int = 100) -> Dict[str, Any]:
        """Get crypto bars."""
        params = {
            "symbols": ",".join(symbols),
            "timeframe": timeframe,
            "limit": limit
        }
        # Crypto data endpoint
        return self._request("GET", "/v1beta3/crypto/us/bars", params=params, base_url=self.data_url)

    def get_latest_crypto_quotes(self, symbols: List[str]) -> Dict[str, Any]:
        """Get latest crypto quotes (bid/ask)."""
        params = {
            "symbols": ",".join(symbols)
        }
        return self._request("GET", "/v1beta3/crypto/us/latest/quotes", params=params, base_url=self.data_url)

    def get_assets(self, status: str = "active", asset_class: str = "crypto") -> List[Dict[str, Any]]:
        """Get list of assets."""
        params = {
            "status": status,
            "asset_class": asset_class
        }
        return self._request("GET", "/v2/assets", params=params)

    def get_order(self, order_id: str) -> Dict[str, Any]:
        """Get order details by ID."""
        return self._request("GET", f"/v2/orders/{order_id}")

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
        result = self._request("GET", "/v2/orders", params=params)
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
            
        return self._request("POST", "/v2/orders", data=data)

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
        return self._request("POST", "/v2/orders", data=data)

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
        return self._request("POST", "/v2/orders", data=data)

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
            
        return self._request("POST", "/v2/orders", data=data)

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
        time_in_force: str = "gtc"
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
        
        if entry_type == "limit" and entry_limit_price:
            data["limit_price"] = str(entry_limit_price)
            
        if stop_loss_limit:
            data["stop_loss"]["limit_price"] = str(stop_loss_limit)
            
        return self._request("POST", "/v2/orders", data=data)

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
            
        return self._request("POST", "/v2/orders", data=data)

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
        time_in_force: str = "gtc"
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
        
        if entry_type == "limit" and entry_limit_price:
            data["limit_price"] = str(entry_limit_price)
            
        if take_profit_limit:
            data["take_profit"] = {"limit_price": str(take_profit_limit)}
        elif stop_loss_stop:
            data["stop_loss"] = {"stop_price": str(stop_loss_stop)}
            if stop_loss_limit:
                data["stop_loss"]["limit_price"] = str(stop_loss_limit)
                
        return self._request("POST", "/v2/orders", data=data)

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
        result = self._request("GET", "/v2/orders", params=params)
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
            
        return self._request("DELETE", f"/v2/orders/{order_id}")

    def cancel_all_orders(self) -> Dict[str, Any]:
        """
        Cancel all open orders.
        
        Returns:
            Response with count of cancelled orders
        """
        if self.dry_run:
            logger.info("[DRY RUN] Cancel all orders")
            return {"status": "canceled", "count": 0}
            
        return self._request("DELETE", "/v2/orders")

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
            
        return self._request("PATCH", f"/v2/orders/{order_id}", data=data)

    # ══════════════════════════════════════════════════════════════════════
    # CONVENIENCE METHODS - Kraken-compatible interface
    # ══════════════════════════════════════════════════════════════════════

    def place_market_order(self, symbol: str, side: str, quantity: float = None, quote_qty: float = None) -> Dict[str, Any]:
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
            
        return self.place_order(symbol, quantity, side, type="market")

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
        stop_loss: float = None
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
        if take_profit and stop_loss:
            # Both TP and SL -> use bracket order
            return self.place_bracket_order(
                symbol, quantity, side,
                entry_type=order_type,
                entry_limit_price=price,
                take_profit_limit=take_profit,
                stop_loss_stop=stop_loss
            )
        elif take_profit or stop_loss:
            # Single exit -> use OTO order
            return self.place_oto_order(
                symbol, quantity, side,
                entry_type=order_type,
                entry_limit_price=price,
                take_profit_limit=take_profit,
                stop_loss_stop=stop_loss
            )
        else:
            # No exits -> regular order
            if order_type == "limit" and price:
                return self.place_limit_order(symbol, quantity, side, price)
            else:
                return self.place_order(symbol, quantity, side)

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
                sym = pos.get('symbol', '').replace('/', '')
                base = sym[:-3] if sym.endswith('USD') else sym
                if base.upper() == asset.upper():
                    return float(pos.get('qty', 0) or 0)
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
                qty = float(pos.get('qty', 0) or 0)
                if qty > 0:
                    sym = pos.get('symbol', '')
                    base = sym.replace('/', '').replace('USD', '')
                    balances[base] = qty
        except:
            pass
        return balances

    def get_24h_tickers(self) -> List[Dict[str, Any]]:
        """
        Get 24h ticker data for crypto assets (Kraken-compatible interface).
        
        Returns:
            List of ticker dicts with symbol, lastPrice, priceChangePercent, quoteVolume
        """
        try:
            # Get active crypto assets
            assets = self.get_assets(status='active', asset_class='crypto')
            symbols = [a['symbol'] for a in assets if a.get('tradable')]
            
            # Filter to USD pairs
            relevant = [s for s in symbols if s.endswith('/USD')][:50]
            
            if not relevant:
                return []
            
            # Get 1-day bars for 24h change calculation
            bars = self.get_crypto_bars(relevant, timeframe="1Day", limit=2)
            
            tickers = []
            for sym, data in bars.get('bars', {}).items():
                if not data:
                    continue
                latest = data[-1]
                prev_close = data[-2]['c'] if len(data) > 1 else latest['o']
                
                close = float(latest['c'])
                change_pct = ((close - prev_close) / prev_close * 100) if prev_close > 0 else 0
                volume = float(latest['v']) * close
                
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
            symbol = f"{asset}/{quote}"
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
        
        Note: Alpaca crypto only supports USD pairs currently.
        
        Args:
            base: Filter by base asset (e.g., 'BTC', 'ETH')
            quote: Filter by quote asset (e.g., 'USD')
            
        Returns:
            List of pairs with base, quote, and pair name
        """
        try:
            assets = self.get_assets(status='active', asset_class='crypto')
            results = []
            
            for asset in assets:
                if not asset.get('tradable'):
                    continue
                
                symbol = asset.get('symbol', '')
                if '/' not in symbol:
                    continue
                
                parts = symbol.split('/')
                if len(parts) != 2:
                    continue
                
                pair_base = parts[0]
                pair_quote = parts[1]
                
                # Apply filters
                if base and pair_base.upper() != base.upper():
                    continue
                if quote and pair_quote.upper() != quote.upper():
                    continue
                
                results.append({
                    "pair": symbol,
                    "base": pair_base,
                    "quote": pair_quote,
                    "min_qty": float(asset.get('min_order_size', 0)),
                    "min_notional": float(asset.get('min_trade_increment', 0))
                })
            
            return results
        except Exception as e:
            logger.error(f"Error getting Alpaca pairs: {e}")
            return []

    def find_conversion_path(self, from_asset: str, to_asset: str) -> List[Dict[str, Any]]:
        """
        Find the best path to convert from one asset to another.
        
        Note: Alpaca only supports USD pairs, so all conversions go through USD.
        
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
        
        # Alpaca crypto only supports USD pairs
        # Path is always: from_asset -> USD -> to_asset
        
        pairs = self.get_available_pairs()
        pair_bases = {p["base"].upper() for p in pairs}
        
        # If converting to/from USD, single trade
        if from_asset == 'USD':
            if to_asset in pair_bases:
                return [{
                    "pair": f"{to_asset}/USD",
                    "side": "buy",
                    "description": f"Buy {to_asset} with USD",
                    "from": "USD",
                    "to": to_asset
                }]
            return []
        
        if to_asset == 'USD':
            if from_asset in pair_bases:
                return [{
                    "pair": f"{from_asset}/USD",
                    "side": "sell",
                    "description": f"Sell {from_asset} for USD",
                    "from": from_asset,
                    "to": "USD"
                }]
            return []
        
        # Both are crypto - need to go through USD
        if from_asset not in pair_bases:
            return []  # Can't trade from_asset
        if to_asset not in pair_bases:
            return []  # Can't trade to_asset
        
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

    def convert_crypto(
        self,
        from_asset: str,
        to_asset: str,
        amount: float,
        use_quote_amount: bool = False
    ) -> Dict[str, Any]:
        """
        Convert one crypto asset to another within Alpaca.
        
        Note: Alpaca only supports USD pairs, so conversions go through USD.
        
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
                
                results.append({
                    "trade": trade,
                    "result": result,
                    "status": "success"
                })
                
                # Update remaining amount for next trade
                if side == "sell":
                    # Estimate USD received
                    exec_qty = float(result.get("qty", result.get("executedQty", 0)))
                    price = float(result.get("filled_avg_price", 0))
                    if price > 0 and exec_qty > 0:
                        remaining_amount = exec_qty * price
                    else:
                        # Fallback: estimate from current price
                        quote_data = self.get_latest_crypto_quotes([pair])
                        if pair in quote_data:
                            mid = (float(quote_data[pair].get('bp', 0)) + float(quote_data[pair].get('ap', 0))) / 2
                            remaining_amount = amount * mid
                else:
                    # We bought crypto
                    exec_qty = float(result.get("qty", result.get("executedQty", 0)))
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
