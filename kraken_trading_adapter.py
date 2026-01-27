#!/usr/bin/env python3
"""
🦑🔌 KRAKEN TRADING ADAPTER 🔌🦑
══════════════════════════════════════════════════════════════════

Wraps KrakenClient to provide Alpaca-compatible interface for the Orca.

Kraken is SPOT trading - you OWN the crypto in your balance.
This adapter tracks "positions" by monitoring balance changes.

Gary Leckey | January 2026
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
import json
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path
from decimal import Decimal

# UTF-8 fix
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from kraken_client import KrakenClient
    KRAKEN_AVAILABLE = True
except ImportError:
    KRAKEN_AVAILABLE = False
    KrakenClient = None


@dataclass
class KrakenPosition:
    """Simulated position for Kraken spot holdings."""
    symbol: str              # e.g., "SOL/USD"
    asset: str              # e.g., "SOL"
    qty: float              # Amount held
    avg_entry_price: float  # Estimated entry price
    current_price: float    # Current market price
    market_value: float     # qty * current_price
    unrealized_pl: float    # Estimated P&L
    unrealized_plpc: float  # P&L percentage
    entry_time: float       # When we started tracking
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict matching Alpaca position format."""
        return {
            'symbol': self.symbol,
            'asset': self.asset,
            'qty': str(self.qty),
            'avg_entry_price': str(self.avg_entry_price),
            'current_price': str(self.current_price),
            'market_value': str(self.market_value),
            'unrealized_pl': str(self.unrealized_pl),
            'unrealized_plpc': str(self.unrealized_plpc),
        }


class KrakenTradingAdapter:
    """
    🦑🔌 Adapter to make Kraken work like Alpaca for the Orca! 🔌🦑
    
    Provides:
    - place_order() - unified interface
    - get_positions() - tracks balance as positions
    - get_account() - account info
    - get_ticker() - price data
    """
    
    # Assets we consider as "base" (not quote/stablecoins)
    TRADING_ASSETS = {'BTC', 'ETH', 'SOL', 'DOGE', 'ATOM', 'SEI', 'DOT', 'LINK', 'AVAX', 'ADA'}
    STABLECOINS = {'USD', 'ZUSD', 'USDT', 'USDC', 'TUSD', 'DAI', 'BUSD'}
    
    # Kraken asset name mapping
    ASSET_MAP = {
        'XXBT': 'BTC',
        'XETH': 'ETH',
        'XBT': 'BTC',
        'ZUSD': 'USD',
    }
    
    # Fee rate (taker)
    FEE_RATE = 0.0026  # 0.26%
    
    def __init__(self):
        if not KRAKEN_AVAILABLE:
            raise RuntimeError("KrakenClient not available")
        
        self.client = KrakenClient()
        self.positions_file = Path("kraken_positions.json")
        self.tracked_positions: Dict[str, Dict] = {}
        
        self._load_positions()
        logger.info("🦑 Kraken Trading Adapter initialized")
    
    def _normalize_asset(self, asset: str) -> str:
        """Normalize Kraken asset names."""
        return self.ASSET_MAP.get(asset, asset)
    
    def _load_positions(self):
        """Load tracked positions from file."""
        try:
            if self.positions_file.exists():
                self.tracked_positions = json.loads(self.positions_file.read_text())
                logger.info(f"📂 Loaded {len(self.tracked_positions)} tracked positions")
        except Exception as e:
            logger.warning(f"Could not load positions: {e}")
            self.tracked_positions = {}
    
    def _save_positions(self):
        """Save tracked positions to file."""
        try:
            self.positions_file.write_text(json.dumps(self.tracked_positions, indent=2))
        except Exception as e:
            logger.error(f"Could not save positions: {e}")
    
    def get_account(self) -> Dict[str, Any]:
        """Get account info in Alpaca-compatible format."""
        balance = self.client.get_account_balance()
        
        # Calculate total USD value
        total_usd = 0.0
        cash = 0.0
        
        for asset, amount in balance.items():
            amt = float(amount) if amount else 0
            asset_norm = self._normalize_asset(asset)
            
            if asset_norm in self.STABLECOINS or asset in self.STABLECOINS:
                cash += amt
                total_usd += amt
            elif amt > 0:
                # Get current price for non-stablecoins
                try:
                    pair = f"{asset_norm}USD"
                    ticker = self.client.get_24h_ticker(pair)
                    if ticker:
                        # Handle new ticker format
                        if 'lastPrice' in ticker:
                            price = float(ticker.get('lastPrice', 0))
                        else:
                            price = float(ticker.get('c', [0])[0]) if isinstance(ticker.get('c'), list) else 0
                        total_usd += amt * price
                except:
                    pass
        
        # Return FLOATS, not strings (for easier arithmetic)
        return {
            'cash': cash,
            'equity': total_usd,
            'buying_power': cash,
            'status': 'ACTIVE',
        }
    
    def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get ticker in Alpaca-compatible format."""
        # Convert symbol format: "SOL/USD" -> "SOLUSD"
        pair = symbol.replace('/', '')
        
        try:
            ticker = self.client.get_24h_ticker(pair)
            if not ticker:
                return None
            
            # Kraken returns different format depending on endpoint
            # New format: {'symbol': 'SOLUSD', 'lastPrice': '142.21', ...}
            if 'lastPrice' in ticker:
                last = float(ticker.get('lastPrice', 0))
                # Estimate bid/ask from last price (spread ~0.1%)
                spread = last * 0.001
                bid = last - spread/2
                ask = last + spread/2
            else:
                # Old format with arrays
                bid = float(ticker.get('b', [0])[0]) if isinstance(ticker.get('b'), list) else 0
                ask = float(ticker.get('a', [0])[0]) if isinstance(ticker.get('a'), list) else 0
                last = float(ticker.get('c', [0])[0]) if isinstance(ticker.get('c'), list) else 0
            
            return {
                'symbol': symbol,
                'bid': bid,
                'ask': ask,
                'price': last,
                'last': last,
            }
        except Exception as e:
            logger.error(f"Error getting ticker {symbol}: {e}")
            return None
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get positions based on current balance.
        
        On Kraken, "positions" = non-stablecoin holdings.
        We track entry prices from when we started monitoring.
        """
        positions = []
        balance = self.client.get_account_balance()
        
        for asset, amount in balance.items():
            amt = float(amount) if amount else 0
            asset_norm = self._normalize_asset(asset)
            
            # Skip stablecoins and dust
            if asset_norm in self.STABLECOINS or asset in self.STABLECOINS:
                continue
            if amt < 0.0001:
                continue
            
            # Get current price
            symbol = f"{asset_norm}/USD"
            pair = f"{asset_norm}USD"
            
            try:
                ticker = self.client.get_24h_ticker(pair)
                if not ticker:
                    continue
                
                # Handle different ticker formats
                if 'lastPrice' in ticker:
                    current_price = float(ticker.get('lastPrice', 0))
                else:
                    current_price = float(ticker.get('c', [0])[0]) if isinstance(ticker.get('c'), list) else 0
                    
                if current_price <= 0:
                    continue
                
                # Get or estimate entry price
                if asset_norm in self.tracked_positions:
                    entry_price = self.tracked_positions[asset_norm].get('entry_price', current_price)
                    entry_time = self.tracked_positions[asset_norm].get('entry_time', time.time())
                else:
                    # First time seeing this asset - use current price as entry
                    entry_price = current_price
                    entry_time = time.time()
                    self.tracked_positions[asset_norm] = {
                        'entry_price': entry_price,
                        'entry_time': entry_time,
                        'entry_qty': amt,
                    }
                    self._save_positions()
                
                market_value = amt * current_price
                unrealized_pl = (current_price - entry_price) * amt
                unrealized_plpc = (current_price - entry_price) / entry_price if entry_price > 0 else 0
                
                positions.append({
                    'symbol': symbol,
                    'asset': asset_norm,
                    'qty': amt,
                    'avg_entry_price': entry_price,
                    'current_price': current_price,
                    'market_value': market_value,
                    'unrealized_pl': unrealized_pl,
                    'unrealized_plpc': unrealized_plpc,
                })
                
            except Exception as e:
                logger.debug(f"Error processing {asset}: {e}")
        
        return positions
    
    def place_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        type: str = 'market',
        time_in_force: str = 'gtc',
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Place order in Alpaca-compatible format.
        
        Args:
            symbol: e.g., "SOL/USD"
            qty: Amount to trade
            side: "buy" or "sell"
            type: "market" or "limit"
            
        Returns:
            Order result or None
        """
        # Convert symbol
        pair = symbol.replace('/', '')
        
        try:
            if type.lower() == 'market':
                result = self.client.place_market_order(
                    symbol=pair,
                    side=side.lower(),
                    quantity=qty
                )
            elif type.lower() == 'limit':
                price = kwargs.get('limit_price') or kwargs.get('price')
                if not price:
                    logger.error("Limit order requires price")
                    return None
                result = self.client.place_limit_order(
                    symbol=pair,
                    side=side.lower(),
                    quantity=qty,
                    price=price
                )
            else:
                logger.error(f"Unsupported order type: {type}")
                return None
            
            if result:
                # Update position tracking
                asset = symbol.split('/')[0]
                if side.lower() == 'buy':
                    # Track new entry
                    ticker = self.get_ticker(symbol)
                    if ticker:
                        self.tracked_positions[asset] = {
                            'entry_price': ticker.get('price', 0),
                            'entry_time': time.time(),
                            'entry_qty': qty,
                        }
                        self._save_positions()
                elif side.lower() == 'sell':
                    # Clear position tracking
                    if asset in self.tracked_positions:
                        del self.tracked_positions[asset]
                        self._save_positions()
                
                logger.info(f"🦑 Kraken order placed: {side} {qty} {symbol}")
                return {
                    'id': result.get('txid', [None])[0] if isinstance(result.get('txid'), list) else result.get('txid'),
                    'symbol': symbol,
                    'side': side,
                    'qty': qty,
                    'status': 'filled' if type == 'market' else 'new',
                    'raw': result,
                }
            
            return None
            
        except Exception as e:
            logger.error(f"🦑 Kraken order failed: {e}")
            return None
    
    def get_available_cash(self) -> float:
        """Get available cash (stablecoins) for trading."""
        balance = self.client.get_account_balance()
        cash = 0.0
        
        for asset, amount in balance.items():
            amt = float(amount) if amount else 0
            asset_norm = self._normalize_asset(asset)
            
            if asset_norm in self.STABLECOINS or asset in self.STABLECOINS:
                cash += amt
        
        return cash


def main():
    """Test the adapter."""
    adapter = KrakenTradingAdapter()
    
    print("=" * 70)
    print("🦑 KRAKEN TRADING ADAPTER TEST")
    print("=" * 70)
    
    # Test account
    print("\n📊 ACCOUNT:")
    account = adapter.get_account()
    print(f"   Cash: ${float(account['cash']):.2f}")
    print(f"   Equity: ${float(account['equity']):.2f}")
    
    # Test positions
    print("\n📈 POSITIONS:")
    positions = adapter.get_positions()
    for pos in positions:
        print(f"   {pos['symbol']}: {pos['qty']:.6f} @ ${pos['current_price']:.2f}")
        print(f"      P&L: ${pos['unrealized_pl']:.4f} ({pos['unrealized_plpc']*100:.2f}%)")
    
    # Test ticker
    print("\n💹 TICKER (SOL/USD):")
    ticker = adapter.get_ticker("SOL/USD")
    if ticker:
        print(f"   Bid: ${ticker['bid']:.2f}")
        print(f"   Ask: ${ticker['ask']:.2f}")
        print(f"   Last: ${ticker['price']:.2f}")
    
    print("\n" + "=" * 70)
    print("✅ Adapter ready for trading!")
    print("=" * 70)


if __name__ == "__main__":
    main()
