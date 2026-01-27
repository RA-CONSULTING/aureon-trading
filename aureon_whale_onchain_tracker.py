"""
Exchange Whale Tracker

Monitors exchange activity for large movements using existing exchange APIs:
- Binance: Recent trades, order history, large orders
- Kraken: Ledger history, trade volume spikes
- Capital.com: Position changes, large flows

Publishes `whale.onchain.detected` for transfers >= threshold.
Note: Uses exchange APIs instead of blockchain providers (no extra API keys needed).
"""
from __future__ import annotations
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)

import logging
import time
import threading
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import deque, defaultdict

from aureon_thought_bus import get_thought_bus, Thought

logger = logging.getLogger(__name__)

# Import exchange clients
try:
    from kraken_client import KrakenClient
    KRAKEN_AVAILABLE = True
except ImportError:
    KRAKEN_AVAILABLE = False

try:
    from binance_client import BinanceClient
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False

try:
    from alpaca_client import AlpacaClient
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False


class WhaleExchangeTracker:
    """Track whale activity using exchange APIs directly"""
    
    def __init__(
        self, 
        threshold_usd: float = 100_000.0,
        poll_interval_seconds: float = 60.0,
        track_balance_changes: bool = True
    ):
        self.thought_bus = get_thought_bus()
        self.threshold_usd = float(threshold_usd)
        self.poll_interval = poll_interval_seconds
        self.track_balance_changes = track_balance_changes
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
        # Track previous balances to detect deposits/withdrawals
        self._prev_balances: Dict[str, Dict[str, float]] = defaultdict(dict)  # exchange -> {asset: amount}
        
        # Track large trades
        self._seen_trades: deque = deque(maxlen=1000)
        
        # Initialize exchange clients
        self.exchanges = {}
        if KRAKEN_AVAILABLE:
            try:
                self.exchanges['kraken'] = KrakenClient()
                logger.info("✅ Kraken client initialized for whale tracking")
            except Exception as e:
                logger.debug(f"Kraken init failed: {e}")
        
        if BINANCE_AVAILABLE:
            try:
                self.exchanges['binance'] = BinanceClient()
                logger.info("✅ Binance client initialized for whale tracking")
            except Exception as e:
                logger.debug(f"Binance init failed: {e}")
        
        if ALPACA_AVAILABLE:
            try:
                self.exchanges['alpaca'] = AlpacaClient()
                logger.info("✅ Alpaca client initialized for whale tracking")
            except Exception as e:
                logger.debug(f"Alpaca init failed: {e}")
        
        if not self.exchanges:
            logger.warning("⚠️  No exchange clients available for whale tracking")

    def start(self):
        """Start background polling thread"""
        if not self.exchanges:
            logger.warning("No exchanges available; tracker disabled")
            return
        
        if self._running:
            logger.debug("WhaleExchangeTracker already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._polling_loop, daemon=True)
        self._thread.start()
        logger.info(f'WhaleExchangeTracker started; monitoring {len(self.exchanges)} exchanges, threshold=${self.threshold_usd:,.0f}')
    
    def stop(self):
        """Stop polling thread"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("WhaleExchangeTracker stopped")
    
    def _polling_loop(self):
        """Background polling for whale activity"""
        while self._running:
            try:
                for exchange_name, client in self.exchanges.items():
                    if not self._running:
                        break
                    
                    try:
                        # Check for balance changes (deposits/withdrawals)
                        if self.track_balance_changes:
                            self._check_balance_changes(exchange_name, client)
                        
                        # Check for large recent trades
                        self._check_large_trades(exchange_name, client)
                        
                    except Exception as e:
                        logger.debug(f"Error polling {exchange_name}: {e}")
                        continue
                
                time.sleep(self.poll_interval)
                
            except Exception as e:
                logger.error(f"Polling loop error: {e}", exc_info=True)
                time.sleep(10)
    
    def _check_balance_changes(self, exchange_name: str, client):
        """Detect large balance changes (deposits/withdrawals)"""
        try:
            current_balances = client.get_balance()
            prev_balances = self._prev_balances[exchange_name]
            
            for asset, current_amount in current_balances.items():
                if current_amount < 1.0:  # Skip dust
                    continue
                
                prev_amount = prev_balances.get(asset, 0.0)
                delta = current_amount - prev_amount
                
                if abs(delta) > 0:  # Any change
                    # Estimate USD value (simplified - would need price oracle)
                    usd_value = self._estimate_usd_value(asset, abs(delta), client)
                    
                    if usd_value >= self.threshold_usd:
                        direction = 'deposit' if delta > 0 else 'withdrawal'
                        self._emit_whale_event(
                            exchange=exchange_name,
                            asset=asset,
                            amount=abs(delta),
                            amount_usd=usd_value,
                            direction=direction,
                            event_type='balance_change'
                        )
            
            # Update previous balances
            self._prev_balances[exchange_name] = current_balances.copy()
            
        except Exception as e:
            logger.debug(f"Balance check error on {exchange_name}: {e}")
    
    def _check_large_trades(self, exchange_name: str, client):
        """Check for large recent trades on the exchange"""
        try:
            # For Kraken: check recent trades
            if exchange_name == 'kraken' and hasattr(client, 'get_recent_trades'):
                pairs = ['XXBTZUSD', 'XETHZUSD']  # BTC/USD, ETH/USD
                for pair in pairs:
                    try:
                        trades = client.get_recent_trades(pair, count=50)
                        for trade in trades:
                            trade_id = f"{exchange_name}:{pair}:{trade.get('time', 0)}"
                            if trade_id in self._seen_trades:
                                continue
                            self._seen_trades.append(trade_id)
                            
                            # Check trade size
                            volume = float(trade.get('volume', 0))
                            price = float(trade.get('price', 0))
                            usd_value = volume * price
                            
                            if usd_value >= self.threshold_usd:
                                self._emit_whale_event(
                                    exchange=exchange_name,
                                    asset=pair,
                                    amount=volume,
                                    amount_usd=usd_value,
                                    direction='trade',
                                    event_type='large_trade',
                                    extra={'price': price, 'side': trade.get('type', 'unknown')}
                                )
                    except Exception as e:
                        logger.debug(f"Trade check error for {pair}: {e}")
            
            # For Binance: check recent trades
            elif exchange_name == 'binance' and hasattr(client, 'get_recent_trades'):
                symbols = ['BTCUSDT', 'ETHUSDT']
                for symbol in symbols:
                    try:
                        trades = client.get_recent_trades(symbol, limit=50)
                        for trade in trades.get('data', []):
                            trade_id = f"{exchange_name}:{symbol}:{trade.get('id', 0)}"
                            if trade_id in self._seen_trades:
                                continue
                            self._seen_trades.append(trade_id)
                            
                            qty = float(trade.get('qty', 0))
                            price = float(trade.get('price', 0))
                            usd_value = qty * price
                            
                            if usd_value >= self.threshold_usd:
                                self._emit_whale_event(
                                    exchange=exchange_name,
                                    asset=symbol,
                                    amount=qty,
                                    amount_usd=usd_value,
                                    direction='trade',
                                    event_type='large_trade',
                                    extra={'price': price}
                                )
                    except Exception as e:
                        logger.debug(f"Trade check error for {symbol}: {e}")
        
        except Exception as e:
            logger.debug(f"Large trade check error on {exchange_name}: {e}")
    
    def _estimate_usd_value(self, asset: str, amount: float, client) -> float:
        """Estimate USD value of an asset amount"""
        # Simplified USD estimation
        if asset in ['USD', 'USDT', 'USDC', 'ZUSD']:
            return amount
        
        # Try to get ticker price
        try:
            if hasattr(client, 'get_ticker'):
                # Map asset to trading pair
                pair_map = {
                    'BTC': 'XXBTZUSD',
                    'ETH': 'XETHZUSD',
                    'XBT': 'XXBTZUSD',
                    'XETH': 'XETHZUSD'
                }
                pair = pair_map.get(asset.upper())
                if pair:
                    ticker = client.get_ticker(pair)
                    price = float(ticker.get('c', [0])[0] if isinstance(ticker.get('c'), list) else ticker.get('last', 0))
                    return amount * price
        except Exception:
            pass
        
        # Fallback estimates
        usd_estimates = {
            'BTC': 45000, 'XBT': 45000, 'XBTC': 45000,
            'ETH': 2500, 'XETH': 2500,
            'BNB': 300,
            'SOL': 100,
        }
        return amount * usd_estimates.get(asset.upper(), 0.0)
    
    def _emit_whale_event(self, exchange: str, asset: str, amount: float, amount_usd: float, 
                          direction: str, event_type: str, extra: Optional[Dict] = None):
        """Emit whale detection event"""
        payload = {
            'exchange': exchange,
            'asset': asset,
            'amount': amount,
            'amount_usd': amount_usd,
            'direction': direction,
            'event_type': event_type,
            'detected_at': time.time(),
            **(extra or {})
        }
        
        th = Thought(source='whale_exchange_tracker', topic='whale.onchain.detected', payload=payload)
        try:
            self.thought_bus.publish(th)
            logger.info(f"🐋 Whale {event_type}: {exchange} {asset} ${amount_usd:,.0f} {direction}")
        except Exception as e:
            logger.debug(f'Failed to publish whale.onchain.detected: {e}')
    
    def simulate_transfer(self, symbol: str, tx_hash: str, from_addr: str, to_addr: str, amount_usd: float) -> None:
        """Simulate detection of a large transfer (for tests)"""
        payload = {
            'symbol': symbol,
            'tx_hash': tx_hash,
            'from': from_addr,
            'to': to_addr,
            'amount_usd': float(amount_usd),
            'detected_at': time.time(),
            'direction': 'simulated',
            'exchange': 'test',
            'event_type': 'simulated'
        }
        if amount_usd >= self.threshold_usd:
            th = Thought(source='whale_exchange_tracker', topic='whale.onchain.detected', payload=payload)
            try:
                self.thought_bus.publish(th)
            except Exception:
                logger.debug('Failed to publish whale.onchain.detected')
            logger.info('Simulated large transfer detected: %s %s', symbol, amount_usd)


# Default instance
_default_tracker: Optional[WhaleExchangeTracker] = None
try:
    _default_tracker = WhaleExchangeTracker()
    _default_tracker.start()  # Auto-start background polling
except Exception as e:
    logger.debug(f"Failed to initialize default WhaleExchangeTracker: {e}")
    _default_tracker = None


def get_exchange_tracker() -> Optional[WhaleExchangeTracker]:
    """Get singleton instance"""
    return _default_tracker
