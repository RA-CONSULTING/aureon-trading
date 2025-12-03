import os
import requests
import time
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class AlpacaClient:
    """
    Client for Alpaca Markets API (Stocks & Crypto).
    """
    def __init__(self):
        self.api_key = os.getenv('ALPACA_API_KEY')
        self.secret_key = os.getenv('ALPACA_SECRET_KEY')
        # Default to paper trading if not specified
        self.use_paper = os.getenv('ALPACA_PAPER', 'true').lower() == 'true'
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
