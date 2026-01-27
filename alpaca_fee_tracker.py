#!/usr/bin/env python3
"""
🦙💰 ALPACA FEE TRACKER & COST GUARDIAN 💰🦙
============================================

Comprehensive fee tracking and cost analysis for Alpaca trading.
NO DEATH BY 1000 CUTS - Every fee is tracked, every spread measured!

FEATURES:
1. Volume-tiered fee detection (8 tiers from 25bps down to 10bps)
2. Real-time orderbook spread calculation
3. Activity API fee querying (CFEE, FEE)
4. Pre/Post trade cost snapshots
5. Conservative cost estimation for gating

Alpaca Fee Tiers (Crypto):
┌──────┬────────────────────┬────────────┬────────────┐
│ Tier │ 30-Day Volume      │ Maker Fee  │ Taker Fee  │
├──────┼────────────────────┼────────────┼────────────┤
│  1   │ $0 - $100K         │ 15 bps     │ 25 bps     │
│  2   │ $100K - $500K      │ 12 bps     │ 22 bps     │
│  3   │ $500K - $1M        │ 10 bps     │ 20 bps     │
│  4   │ $1M - $10M         │ 8 bps      │ 18 bps     │
│  5   │ $10M - $25M        │ 5 bps      │ 15 bps     │
│  6   │ $25M - $50M        │ 2 bps      │ 13 bps     │
│  7   │ $50M - $100M       │ 2 bps      │ 12 bps     │
│  8   │ $100M+             │ 0 bps      │ 10 bps     │
└──────┴────────────────────┴────────────┴────────────┘

Gary Leckey | January 2026 | PROTECT THE SNOWBALL!
"""

from __future__ import annotations
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)

import os
import sys
import json
import time
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

# Windows UTF-8 fix
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# 💰 ALPACA FEE TIER STRUCTURE (As of 2025-2026)
# ═══════════════════════════════════════════════════════════════════════════

ALPACA_FEE_TIERS = [
    # (min_volume, max_volume, maker_bps, taker_bps)
    (0,           100_000,       15, 25),   # Tier 1
    (100_000,     500_000,       12, 22),   # Tier 2
    (500_000,     1_000_000,     10, 20),   # Tier 3
    (1_000_000,   10_000_000,     8, 18),   # Tier 4
    (10_000_000,  25_000_000,     5, 15),   # Tier 5
    (25_000_000,  50_000_000,     2, 13),   # Tier 6
    (50_000_000,  100_000_000,    2, 12),   # Tier 7
    (100_000_000, float('inf'),   0, 10),   # Tier 8
]


@dataclass
class FeeTier:
    """Alpaca fee tier information."""
    tier: int
    min_volume: float
    max_volume: float
    maker_bps: int  # Basis points (1 bps = 0.01%)
    taker_bps: int
    maker_pct: float = field(init=False)
    taker_pct: float = field(init=False)
    
    def __post_init__(self):
        self.maker_pct = self.maker_bps / 10000  # Convert bps to decimal
        self.taker_pct = self.taker_bps / 10000
    
    @property
    def name(self) -> str:
        """Human-readable tier name."""
        return f"Tier {self.tier} (${self.min_volume:,.0f}-${self.max_volume:,.0f})"


@dataclass
class SpreadSnapshot:
    """Real-time spread snapshot from orderbook."""
    symbol: str
    timestamp: float
    bid: float
    ask: float
    mid: float
    spread_abs: float  # Absolute spread (ask - bid)
    spread_pct: float  # Spread as percentage of mid
    bid_size: float = 0.0
    ask_size: float = 0.0
    
    @property
    def half_spread_pct(self) -> float:
        """Half spread - what you effectively pay per side."""
        return self.spread_pct / 2


@dataclass  
class TradeCostSnapshot:
    """Complete cost snapshot for a trade (before or after)."""
    timestamp: float
    phase: str  # 'pre_buy', 'post_buy', 'pre_sell', 'post_sell', 'pre_convert', 'post_convert'
    symbol: str
    
    # Price data
    bid: float = 0.0
    ask: float = 0.0
    mid: float = 0.0
    last_price: float = 0.0
    
    # Spread
    spread_pct: float = 0.0
    half_spread_pct: float = 0.0
    
    # Fee tier
    fee_tier: int = 1
    maker_fee_pct: float = 0.0015  # 15 bps default
    taker_fee_pct: float = 0.0025  # 25 bps default
    
    # Account state
    usd_balance: float = 0.0
    asset_balance: float = 0.0
    asset_value_usd: float = 0.0
    total_equity: float = 0.0
    
    # Estimated costs for a hypothetical trade
    est_fee_usd: float = 0.0
    est_slippage_pct: float = 0.0
    est_total_cost_pct: float = 0.0


@dataclass
class TradeExecution:
    """Complete record of a trade execution with all cost data."""
    trade_id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    timestamp: float
    
    # Requested vs Executed
    requested_qty: float
    executed_qty: float
    requested_price: float = 0.0  # For limit orders
    executed_price: float = 0.0
    
    # Pre/Post snapshots
    pre_snapshot: Optional[TradeCostSnapshot] = None
    post_snapshot: Optional[TradeCostSnapshot] = None
    
    # Actual fees (from Alpaca Activities API)
    actual_fee_asset: str = ""
    actual_fee_qty: float = 0.0
    actual_fee_usd: float = 0.0
    
    # Calculated metrics
    gross_value_usd: float = 0.0
    net_value_usd: float = 0.0
    total_cost_usd: float = 0.0
    total_cost_pct: float = 0.0
    slippage_usd: float = 0.0
    slippage_pct: float = 0.0


# ═══════════════════════════════════════════════════════════════════════════
# 🦙 ALPACA FEE TRACKER
# ═══════════════════════════════════════════════════════════════════════════

class AlpacaFeeTracker:
    """
    Comprehensive fee tracking for Alpaca trading.
    
    GOAL: Prevent death by 1000 cuts by tracking every cost component!
    """
    
    def __init__(self, alpaca_client=None):
        """
        Initialize the fee tracker.
        
        Args:
            alpaca_client: Optional AlpacaClient instance (will create if not provided)
        """
        self.client = alpaca_client
        self._fee_tier: Optional[FeeTier] = None
        self._30d_volume: float = 0.0
        self._last_tier_check: float = 0
        self._tier_check_interval = 3600  # Re-check tier every hour
        
        # Cache for spreads
        self._spread_cache: Dict[str, SpreadSnapshot] = {}
        self._spread_cache_ttl = 5  # 5 second TTL for spread cache
        
        # Trade execution history
        self._executions: List[TradeExecution] = []
        self._max_executions = 1000  # Keep last 1000 trades
        
        # Persistence
        self._state_file = Path("alpaca_fee_tracker_state.json")
        self._load_state()
        
        logger.info("🦙💰 Alpaca Fee Tracker initialized")
    
    def _load_state(self):
        """Load persisted state."""
        try:
            if self._state_file.exists():
                with open(self._state_file, 'r') as f:
                    data = json.load(f)
                self._30d_volume = data.get('30d_volume', 0.0)
                self._last_tier_check = data.get('last_tier_check', 0)
                logger.info(f"   📂 Loaded state: 30d volume=${self._30d_volume:,.2f}")
        except Exception as e:
            logger.warning(f"   ⚠️ Could not load fee tracker state: {e}")
    
    def _save_state(self):
        """Persist state to disk."""
        try:
            data = {
                '30d_volume': self._30d_volume,
                'last_tier_check': self._last_tier_check,
                'timestamp': time.time()
            }
            with open(self._state_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"   ⚠️ Could not save fee tracker state: {e}")
    
    def set_client(self, client):
        """Set the Alpaca client."""
        self.client = client
        logger.info("🦙 Fee tracker wired to Alpaca client")
    
    @property
    def current_tier(self) -> FeeTier:
        """Get current fee tier (convenience property)."""
        return self.get_fee_tier()
    
    @property
    def volume_30d(self) -> float:
        """Get 30-day trading volume."""
        # Refresh tier (which updates volume)
        self.get_fee_tier()
        return self._30d_volume
    
    # ═══════════════════════════════════════════════════════════════════════
    # 📊 FEE TIER DETECTION
    # ═══════════════════════════════════════════════════════════════════════
    
    def get_fee_tier(self, force_refresh: bool = False) -> FeeTier:
        """
        Get current fee tier based on 30-day trading volume.
        
        Uses Activities API to calculate actual volume.
        """
        now = time.time()
        
        # Use cached tier if still fresh
        if self._fee_tier and not force_refresh:
            if now - self._last_tier_check < self._tier_check_interval:
                return self._fee_tier
        
        # Calculate 30-day volume from trade history
        volume = self._calculate_30d_volume()
        self._30d_volume = volume
        self._last_tier_check = now
        
        # Find matching tier
        for tier_idx, (min_vol, max_vol, maker, taker) in enumerate(ALPACA_FEE_TIERS, 1):
            if min_vol <= volume < max_vol:
                self._fee_tier = FeeTier(
                    tier=tier_idx,
                    min_volume=min_vol,
                    max_volume=max_vol,
                    maker_bps=maker,
                    taker_bps=taker
                )
                break
        
        if not self._fee_tier:
            # Default to tier 1
            self._fee_tier = FeeTier(
                tier=1,
                min_volume=0,
                max_volume=100_000,
                maker_bps=15,
                taker_bps=25
            )
        
        self._save_state()
        
        logger.info(f"🦙💰 Fee Tier: {self._fee_tier.tier} | "
                   f"30d Volume: ${volume:,.2f} | "
                   f"Maker: {self._fee_tier.maker_bps}bps | "
                   f"Taker: {self._fee_tier.taker_bps}bps")
        
        return self._fee_tier
    
    def _calculate_30d_volume(self) -> float:
        """Calculate 30-day trading volume from Alpaca Activities."""
        if not self.client:
            return 0.0
        
        try:
            # Get activities from last 30 days
            # Alpaca uses FILL activity type for executed trades
            activities = self._get_trade_activities(days=30)
            
            total_volume = 0.0
            for act in activities:
                # Each fill has qty and price
                qty = float(act.get('qty', 0) or 0)
                price = float(act.get('price', 0) or 0)
                total_volume += qty * price
            
            return total_volume
            
        except Exception as e:
            logger.warning(f"⚠️ Could not calculate 30d volume: {e}")
            return 0.0
    
    def _get_trade_activities(self, days: int = 30) -> List[Dict]:
        """Get trade fill activities from Alpaca."""
        if not self.client:
            return []
        
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Use activities endpoint with FILL type
            params = {
                "activity_types": "FILL",
                "after": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "direction": "desc",
                "page_size": 100  # Alpaca max is 100
            }
            
            result = self.client._request("GET", "/v2/account/activities", params=params)
            return result if isinstance(result, list) else []
            
        except Exception as e:
            logger.warning(f"⚠️ Could not get trade activities: {e}")
            return []
    
    def get_fee_activities(self, days: int = 7) -> List[Dict]:
        """
        Get crypto fee activities (CFEE) from Alpaca.
        
        Returns list of fee records with:
        - activity_type: 'CFEE' or 'FEE'
        - symbol: The trading pair
        - qty: Fee quantity (negative = deducted)
        - price: Price at time of fee
        - net_amount: Fee in USD equivalent
        """
        if not self.client:
            return []
        
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Query CFEE (crypto fees) and FEE activities
            params = {
                "activity_types": "CFEE,FEE",
                "after": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "direction": "desc",
                "page_size": 100  # Alpaca max is 100
            }
            
            result = self.client._request("GET", "/v2/account/activities", params=params)
            fees = result if isinstance(result, list) else []
            
            logger.info(f"📊 Found {len(fees)} fee activities in last {days} days")
            return fees
            
        except Exception as e:
            logger.warning(f"⚠️ Could not get fee activities: {e}")
            return []
    
    def calculate_total_fees_paid(self, days: int = 30) -> Dict[str, float]:
        """
        Calculate total fees paid over a period.
        
        Returns:
            Dict with fee breakdown by asset and total USD equivalent
        """
        fees = self.get_fee_activities(days)
        
        by_asset: Dict[str, float] = {}
        total_usd = 0.0
        
        for fee in fees:
            symbol = fee.get('symbol', 'UNKNOWN')
            qty = abs(float(fee.get('qty', 0) or 0))
            price = float(fee.get('price', 0) or 0)
            
            by_asset[symbol] = by_asset.get(symbol, 0) + qty
            total_usd += qty * price
        
        return {
            'by_asset': by_asset,
            'total_usd': total_usd,
            'period_days': days,
            'fee_count': len(fees)
        }
    
    # ═══════════════════════════════════════════════════════════════════════
    # 📈 SPREAD & ORDERBOOK ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════
    
    def get_spread(self, symbol: str, force_refresh: bool = False) -> Optional[SpreadSnapshot]:
        """
        Get real-time spread from orderbook.
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USD', 'ETH/USD')
            force_refresh: Bypass cache
            
        Returns:
            SpreadSnapshot with bid/ask/spread data
        """
        if not self.client:
            return None
        
        # Normalize symbol
        symbol = self.client._normalize_pair_symbol(symbol) or symbol
        
        # Check cache
        now = time.time()
        if not force_refresh and symbol in self._spread_cache:
            cached = self._spread_cache[symbol]
            if now - cached.timestamp < self._spread_cache_ttl:
                return cached
        
        try:
            # Get orderbook snapshot
            orderbook = self.get_orderbook(symbol)
            if not orderbook:
                # Fallback to quotes
                return self._get_spread_from_quotes(symbol)
            
            # Parse orderbook
            bids = orderbook.get('b', [])  # List of [price, size]
            asks = orderbook.get('a', [])
            
            if not bids or not asks:
                return self._get_spread_from_quotes(symbol)
            
            # Best bid/ask
            best_bid = float(bids[0].get('p', 0) if isinstance(bids[0], dict) else bids[0][0])
            best_ask = float(asks[0].get('p', 0) if isinstance(asks[0], dict) else asks[0][0])
            bid_size = float(bids[0].get('s', 0) if isinstance(bids[0], dict) else bids[0][1])
            ask_size = float(asks[0].get('s', 0) if isinstance(asks[0], dict) else asks[0][1])
            
            if best_bid <= 0 or best_ask <= 0:
                return self._get_spread_from_quotes(symbol)
            
            mid = (best_bid + best_ask) / 2
            spread_abs = best_ask - best_bid
            spread_pct = (spread_abs / mid) * 100 if mid > 0 else 0
            
            snapshot = SpreadSnapshot(
                symbol=symbol,
                timestamp=now,
                bid=best_bid,
                ask=best_ask,
                mid=mid,
                spread_abs=spread_abs,
                spread_pct=spread_pct,
                bid_size=bid_size,
                ask_size=ask_size
            )
            
            self._spread_cache[symbol] = snapshot
            return snapshot
            
        except Exception as e:
            logger.warning(f"⚠️ Could not get spread for {symbol}: {e}")
            return self._get_spread_from_quotes(symbol)
    
    def _get_spread_from_quotes(self, symbol: str) -> Optional[SpreadSnapshot]:
        """Fallback: get spread from quotes API."""
        if not self.client:
            return None
        
        try:
            quotes = self.client.get_latest_crypto_quotes([symbol])
            if symbol not in quotes:
                return None
            
            q = quotes[symbol]
            bid = float(q.get('bp', 0) or 0)
            ask = float(q.get('ap', 0) or 0)
            
            if bid <= 0 or ask <= 0:
                return None
            
            mid = (bid + ask) / 2
            spread_abs = ask - bid
            spread_pct = (spread_abs / mid) * 100 if mid > 0 else 0
            
            snapshot = SpreadSnapshot(
                symbol=symbol,
                timestamp=time.time(),
                bid=bid,
                ask=ask,
                mid=mid,
                spread_abs=spread_abs,
                spread_pct=spread_pct,
                bid_size=float(q.get('bs', 0) or 0),
                ask_size=float(q.get('as', 0) or 0)
            )
            
            self._spread_cache[symbol] = snapshot
            return snapshot
            
        except Exception as e:
            logger.warning(f"⚠️ Could not get quote spread for {symbol}: {e}")
            return None
    
    def get_orderbook(self, symbol: str) -> Optional[Dict]:
        """
        Get full orderbook for a symbol.
        
        Returns raw orderbook data from Alpaca.
        """
        if not self.client:
            return None
        
        symbol = self.client._normalize_pair_symbol(symbol) or symbol
        
        try:
            params = {"symbols": symbol}
            result = self.client._request(
                "GET", 
                "/v1beta3/crypto/us/latest/orderbooks",
                params=params,
                base_url=self.client.data_url
            )
            
            orderbooks = result.get('orderbooks', result) if isinstance(result, dict) else {}
            return orderbooks.get(symbol)
            
        except Exception as e:
            logger.warning(f"⚠️ Could not get orderbook for {symbol}: {e}")
            return None
    
    # ═══════════════════════════════════════════════════════════════════════
    # 📸 TRADE COST SNAPSHOTS
    # ═══════════════════════════════════════════════════════════════════════
    
    def take_snapshot(self, symbol: str, phase: str) -> TradeCostSnapshot:
        """
        Take a complete cost snapshot before or after a trade.
        
        Args:
            symbol: Trading pair
            phase: 'pre_buy', 'post_buy', 'pre_sell', 'post_sell', 
                   'pre_convert', 'post_convert'
        
        Returns:
            TradeCostSnapshot with all cost metrics
        """
        symbol = self.client._normalize_pair_symbol(symbol) or symbol if self.client else symbol
        
        # Get spread data
        spread = self.get_spread(symbol)
        
        # Get fee tier
        tier = self.get_fee_tier()
        
        # Get account balances
        usd_balance = 0.0
        asset_balance = 0.0
        total_equity = 0.0
        
        if self.client:
            try:
                account = self.client.get_account()
                usd_balance = float(account.get('cash', 0) or 0)
                total_equity = float(account.get('equity', 0) or 0)
                
                # Get specific asset balance
                base = symbol.split('/')[0] if '/' in symbol else symbol[:3]
                asset_balance = float(self.client.get_free_balance(base) or 0)
                
            except Exception as e:
                logger.warning(f"⚠️ Could not get account data: {e}")
        
        snapshot = TradeCostSnapshot(
            timestamp=time.time(),
            phase=phase,
            symbol=symbol,
            bid=spread.bid if spread else 0.0,
            ask=spread.ask if spread else 0.0,
            mid=spread.mid if spread else 0.0,
            spread_pct=spread.spread_pct if spread else 0.0,
            half_spread_pct=spread.half_spread_pct if spread else 0.0,
            fee_tier=tier.tier if tier else 1,
            maker_fee_pct=tier.maker_pct if tier else 0.0015,
            taker_fee_pct=tier.taker_pct if tier else 0.0025,
            usd_balance=usd_balance,
            asset_balance=asset_balance,
            asset_value_usd=asset_balance * (spread.mid if spread else 0),
            total_equity=total_equity,
            # Estimate total cost for a market order (taker + half spread)
            est_slippage_pct=(spread.half_spread_pct if spread else 0.1) / 100,
            est_total_cost_pct=(tier.taker_pct if tier else 0.0025) + 
                              ((spread.half_spread_pct if spread else 0.1) / 100)
        )
        
        return snapshot
    
    def estimate_trade_cost(
        self, 
        symbol: str, 
        side: str, 
        quantity: float,
        is_maker: bool = False
    ) -> Dict[str, float]:
        """
        Estimate total cost for a hypothetical trade.
        
        Args:
            symbol: Trading pair
            side: 'buy' or 'sell'
            quantity: Amount to trade
            is_maker: If True, use maker fees (limit orders)
            
        Returns:
            Dict with:
            - notional: Trade value in USD
            - fee_pct: Fee percentage
            - fee_usd: Fee in USD
            - spread_cost_pct: Spread cost percentage
            - spread_cost_usd: Spread cost in USD
            - total_cost_pct: Total cost percentage
            - total_cost_usd: Total cost in USD
            - net_proceeds_usd: What you actually get/pay
        """
        spread = self.get_spread(symbol)
        tier = self.get_fee_tier()
        
        if not spread or spread.mid <= 0:
            return {
                'error': f'Could not get price data for {symbol}',
                'notional': 0,
                'fee_pct': tier.taker_pct if tier else 0.0025,
                'fee_usd': 0,
                'spread_cost_pct': 0.001,  # Assume 0.1% spread
                'spread_cost_usd': 0,
                'total_cost_pct': 0.0035,  # Conservative default
                'total_cost_usd': 0,
                'net_proceeds_usd': 0
            }
        
        # Calculate notional value
        if side.lower() == 'buy':
            # Buying at ask
            execution_price = spread.ask
        else:
            # Selling at bid
            execution_price = spread.bid
        
        notional = quantity * execution_price
        
        # Fee calculation
        fee_pct = tier.maker_pct if is_maker else tier.taker_pct
        fee_usd = notional * fee_pct
        
        # Spread cost (crossing the spread vs mid price)
        spread_cost_pct = spread.half_spread_pct / 100  # Convert to decimal
        spread_cost_usd = notional * spread_cost_pct
        
        # Total cost
        total_cost_pct = fee_pct + spread_cost_pct
        total_cost_usd = fee_usd + spread_cost_usd
        
        # Net proceeds
        if side.lower() == 'buy':
            net_proceeds_usd = -(notional + total_cost_usd)  # You pay
        else:
            net_proceeds_usd = notional - total_cost_usd  # You receive
        
        return {
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'execution_price': execution_price,
            'mid_price': spread.mid,
            'notional': notional,
            'fee_pct': fee_pct,
            'fee_usd': fee_usd,
            'spread_cost_pct': spread_cost_pct,
            'spread_cost_usd': spread_cost_usd,
            'total_cost_pct': total_cost_pct,
            'total_cost_usd': total_cost_usd,
            'net_proceeds_usd': net_proceeds_usd,
            'fee_tier': tier.tier if tier else 1
        }
    
    def estimate_conversion_cost(
        self,
        from_asset: str,
        to_asset: str,
        amount: float
    ) -> Dict[str, Any]:
        """
        Estimate total cost for a crypto-to-crypto conversion.
        
        Alpaca conversions go through USD, so it's 2 trades.
        
        Args:
            from_asset: Source asset (e.g., 'BTC')
            to_asset: Target asset (e.g., 'ETH')
            amount: Amount of from_asset to convert
            
        Returns:
            Dict with complete cost breakdown for both legs
        """
        from_symbol = f"{from_asset.upper()}/USD"
        to_symbol = f"{to_asset.upper()}/USD"
        
        # Leg 1: Sell from_asset for USD
        sell_cost = self.estimate_trade_cost(from_symbol, 'sell', amount)
        
        if sell_cost.get('error'):
            return {'error': sell_cost['error'], 'leg1': sell_cost}
        
        # USD received after sell
        usd_received = abs(sell_cost['net_proceeds_usd'])
        
        # Leg 2: Buy to_asset with USD
        # Estimate quantity from price
        to_spread = self.get_spread(to_symbol)
        if not to_spread or to_spread.ask <= 0:
            return {'error': f'Could not get price for {to_symbol}', 'leg1': sell_cost}
        
        to_quantity = usd_received / to_spread.ask
        buy_cost = self.estimate_trade_cost(to_symbol, 'buy', to_quantity)
        
        # Total conversion cost
        total_fee_usd = sell_cost['fee_usd'] + buy_cost['fee_usd']
        total_spread_usd = sell_cost['spread_cost_usd'] + buy_cost['spread_cost_usd']
        total_cost_usd = sell_cost['total_cost_usd'] + buy_cost['total_cost_usd']
        
        # Original value vs final value
        original_value_usd = sell_cost['notional']
        final_to_quantity = to_quantity * (1 - buy_cost['total_cost_pct'])
        final_value_usd = final_to_quantity * to_spread.mid
        
        cost_pct = (total_cost_usd / original_value_usd) * 100 if original_value_usd > 0 else 0
        
        return {
            'from_asset': from_asset,
            'to_asset': to_asset,
            'from_amount': amount,
            'to_amount_estimate': final_to_quantity,
            'original_value_usd': original_value_usd,
            'final_value_usd': final_value_usd,
            'leg1_sell': sell_cost,
            'leg2_buy': buy_cost,
            'total_fee_usd': total_fee_usd,
            'total_spread_usd': total_spread_usd,
            'total_cost_usd': total_cost_usd,
            'total_cost_pct': cost_pct,
            'usd_intermediate': usd_received,
            'fee_tier': sell_cost['fee_tier']
        }
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🎯 CONSERVATIVE GATE (PREVENT 1000 CUTS)
    # ═══════════════════════════════════════════════════════════════════════
    
    def should_execute_trade(
        self,
        symbol: str,
        side: str,
        quantity: float,
        expected_profit_usd: float,
        min_profit_margin: float = 0.5  # Need 50% more profit than cost
    ) -> Tuple[bool, str, Dict]:
        """
        Conservative gate: Should this trade be executed?
        
        Args:
            symbol: Trading pair
            side: 'buy' or 'sell'
            quantity: Trade quantity
            expected_profit_usd: Expected profit from this trade
            min_profit_margin: Required margin above costs (0.5 = 50%)
            
        Returns:
            (should_execute, reason, cost_breakdown)
        """
        cost = self.estimate_trade_cost(symbol, side, quantity)
        
        if cost.get('error'):
            return False, f"Could not estimate cost: {cost['error']}", cost
        
        total_cost_usd = cost['total_cost_usd']
        
        # Required profit = cost + margin
        required_profit = total_cost_usd * (1 + min_profit_margin)
        
        if expected_profit_usd >= required_profit:
            return True, f"Profit ${expected_profit_usd:.4f} >= required ${required_profit:.4f}", cost
        else:
            return False, f"Profit ${expected_profit_usd:.4f} < required ${required_profit:.4f} (cost=${total_cost_usd:.4f})", cost
    
    def should_execute_conversion(
        self,
        from_asset: str,
        to_asset: str,
        amount: float,
        expected_profit_usd: float,
        min_profit_margin: float = 0.5
    ) -> Tuple[bool, str, Dict]:
        """
        Conservative gate for conversions (2-leg trades).
        
        Conversions have DOUBLE the cost, so be extra careful!
        """
        cost = self.estimate_conversion_cost(from_asset, to_asset, amount)
        
        if cost.get('error'):
            return False, f"Could not estimate cost: {cost['error']}", cost
        
        total_cost_usd = cost['total_cost_usd']
        required_profit = total_cost_usd * (1 + min_profit_margin)
        
        if expected_profit_usd >= required_profit:
            return True, f"Conversion profit ${expected_profit_usd:.4f} >= required ${required_profit:.4f}", cost
        else:
            return False, f"Conversion profit ${expected_profit_usd:.4f} < required ${required_profit:.4f} (cost=${total_cost_usd:.4f})", cost
    
    # ═══════════════════════════════════════════════════════════════════════
    # 📊 REPORTING
    # ═══════════════════════════════════════════════════════════════════════
    
    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive fee tracking summary."""
        tier = self.get_fee_tier()
        fees_paid = self.calculate_total_fees_paid(days=30)
        
        return {
            'fee_tier': {
                'tier': tier.tier,
                'maker_bps': tier.maker_bps,
                'taker_bps': tier.taker_bps,
                'maker_pct': tier.maker_pct * 100,
                'taker_pct': tier.taker_pct * 100
            },
            '30d_volume': self._30d_volume,
            'fees_paid_30d': fees_paid,
            'volume_to_next_tier': self._volume_to_next_tier(),
            'executions_tracked': len(self._executions)
        }
    
    def _volume_to_next_tier(self) -> float:
        """Calculate volume needed to reach next tier."""
        tier = self.get_fee_tier()
        if tier.tier >= 8:
            return 0  # Already at highest tier
        
        next_tier_min = ALPACA_FEE_TIERS[tier.tier][0]  # Index = tier (0-based)
        return max(0, next_tier_min - self._30d_volume)
    
    def print_summary(self):
        """Print formatted fee tracking summary."""
        summary = self.get_summary()
        
        print("\n" + "═" * 60)
        print("🦙💰 ALPACA FEE TRACKER SUMMARY")
        print("═" * 60)
        print(f"📊 Fee Tier: {summary['fee_tier']['tier']}")
        print(f"   Maker Fee: {summary['fee_tier']['maker_bps']} bps ({summary['fee_tier']['maker_pct']:.2f}%)")
        print(f"   Taker Fee: {summary['fee_tier']['taker_bps']} bps ({summary['fee_tier']['taker_pct']:.2f}%)")
        print(f"\n💰 30-Day Volume: ${summary['30d_volume']:,.2f}")
        print(f"📈 Volume to next tier: ${summary['volume_to_next_tier']:,.2f}")
        print(f"\n💸 Fees Paid (30d): ${summary['fees_paid_30d']['total_usd']:.4f}")
        print(f"   Fee count: {summary['fees_paid_30d']['fee_count']}")
        print("═" * 60)

    def record_trade_completion(
        self,
        symbol: str,
        side: str,
        quantity: float,
        fill_price: float,
        expected_pnl: float,
        actual_pnl: float = None,
        order_id: str = None
    ) -> Dict[str, Any]:
        """
        Record trade completion metrics for learning.
        
        Called AFTER a trade completes to:
        1. Query actual fee from activities API
        2. Compare expected vs actual costs
        3. Update execution history for learning
        """
        timestamp = time.time()
        notional = quantity * fill_price
        
        # Calculate expected costs (what we thought we'd pay)
        expected_costs = self.estimate_trade_cost(symbol, side, quantity, fill_price)
        
        # Query actual fee from activities (may take a moment to appear)
        actual_fee = None
        if order_id:
            try:
                # Get recent fee activities
                fees = self.get_fee_activities(days=1)
                for fee in fees:
                    if fee.get('order_id') == order_id:
                        actual_fee = float(fee.get('net_amount', 0))
                        break
            except Exception:
                pass
        
        # If no actual fee found, estimate from tier
        if actual_fee is None:
            actual_fee = expected_costs['fee_usd']
        
        # Calculate actual P&L if not provided
        if actual_pnl is None:
            actual_pnl = expected_pnl - expected_costs['total_cost_usd']
        
        # Record execution
        execution = {
            'timestamp': timestamp,
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'fill_price': fill_price,
            'notional': notional,
            'expected_fee_usd': expected_costs['fee_usd'],
            'actual_fee_usd': abs(actual_fee),
            'expected_spread_cost': expected_costs['spread_cost_usd'],
            'total_expected_cost': expected_costs['total_cost_usd'],
            'expected_pnl': expected_pnl,
            'actual_pnl': actual_pnl,
            'fee_tier': self.current_tier.name,
            'order_id': order_id
        }
        
        self._executions.append(execution)
        
        # Keep only last 1000 executions
        if len(self._executions) > 1000:
            self._executions = self._executions[-1000:]
        
        # Update 30d volume (will be recalculated on next tier check)
        self._30d_volume += notional
        
        # Save state periodically
        if len(self._executions) % 10 == 0:
            self._save_state()
        
        # Calculate cost accuracy (how close were we?)
        fee_accuracy = 1.0 - abs(expected_costs['fee_usd'] - abs(actual_fee)) / max(abs(actual_fee), 0.0001)
        
        return {
            'recorded': True,
            'expected_cost_usd': expected_costs['total_cost_usd'],
            'actual_fee_usd': abs(actual_fee),
            'expected_pnl': expected_pnl,
            'actual_pnl': actual_pnl,
            'fee_accuracy': fee_accuracy,
            'current_tier': self.current_tier.name,
            '30d_volume': self._30d_volume
        }


# ═══════════════════════════════════════════════════════════════════════════
# 🌍 SINGLETON / FACTORY
# ═══════════════════════════════════════════════════════════════════════════

_fee_tracker_instance: Optional[AlpacaFeeTracker] = None

def get_fee_tracker(alpaca_client=None) -> AlpacaFeeTracker:
    """Get or create the fee tracker singleton."""
    global _fee_tracker_instance
    
    if _fee_tracker_instance is None:
        _fee_tracker_instance = AlpacaFeeTracker(alpaca_client)
    elif alpaca_client and not _fee_tracker_instance.client:
        _fee_tracker_instance.set_client(alpaca_client)
    
    return _fee_tracker_instance


# ═══════════════════════════════════════════════════════════════════════════
# 🧪 TEST / DEMO
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Test the fee tracker
    print("🦙💰 ALPACA FEE TRACKER TEST")
    print("=" * 60)
    
    try:
        from alpaca_client import AlpacaClient
        client = AlpacaClient()
        
        tracker = get_fee_tracker(client)
        
        # Print summary
        tracker.print_summary()
        
        # Test spread
        print("\n📈 Testing spread for BTC/USD...")
        spread = tracker.get_spread("BTC/USD")
        if spread:
            print(f"   Bid: ${spread.bid:,.2f}")
            print(f"   Ask: ${spread.ask:,.2f}")
            print(f"   Spread: {spread.spread_pct:.4f}%")
        
        # Test trade cost estimation
        print("\n💰 Estimating cost for 0.01 BTC sell...")
        cost = tracker.estimate_trade_cost("BTC/USD", "sell", 0.01)
        print(f"   Notional: ${cost['notional']:.2f}")
        print(f"   Fee: ${cost['fee_usd']:.4f} ({cost['fee_pct']*100:.3f}%)")
        print(f"   Spread Cost: ${cost['spread_cost_usd']:.4f}")
        print(f"   Total Cost: ${cost['total_cost_usd']:.4f} ({cost['total_cost_pct']*100:.3f}%)")
        
        # Test conversion cost
        print("\n🔄 Estimating BTC→ETH conversion cost...")
        conv = tracker.estimate_conversion_cost("BTC", "ETH", 0.01)
        print(f"   Original Value: ${conv['original_value_usd']:.2f}")
        print(f"   Total Cost: ${conv['total_cost_usd']:.4f} ({conv['total_cost_pct']:.3f}%)")
        print(f"   Final Value: ${conv['final_value_usd']:.2f}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
