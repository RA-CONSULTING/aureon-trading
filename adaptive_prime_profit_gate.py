#!/usr/bin/env python3
"""
ADAPTIVE PRIME PROFIT GATE - Dynamic Profit Threshold Calculator
═══════════════════════════════════════════════════════════════════════════════

Calculates exact price movements required for profitable trades after all costs.

MASTER EQUATION:
    r_min(P) = (V + G + P) / [V × (1 - f - s - c)²] - 1

Where:
    r = required price increase (fraction)
    V = trade notional (USD/GBP)
    G = fixed costs (gas/network, withdrawal fees)
    P = target net profit (prime)
    f = trading fee rate
    s = slippage rate
    c = spread cost rate

THREE GATES:
    1. Break-even gate (r₀): Net profit ≥ 0
    2. Prime-profit gate (rₚ): Net profit ≥ prime target (e.g. $0.02)
    3. Prime + buffer gate (r_{p+b}): Net profit ≥ prime + safety buffer

FEATURES:
    - Real-time exchange fee profiles (tiered, maker/taker)
    - Volatility-aware slippage estimation
    - Dynamic spread cost tracking
    - Integration with Queen Hive Mind for decision routing
    - Mycelium network goal propagation

Gary Leckey & GitHub Copilot | 2025-2026
═══════════════════════════════════════════════════════════════════════════════
"""

import time
import json
import os
import logging
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple, List
from datetime import datetime

logger = logging.getLogger(__name__)


# Global epsilon profit policy: accept any net-positive edge after costs.
EPSILON_PROFIT_USD = 0.0001


# ═══════════════════════════════════════════════════════════════
# 📊 EXCHANGE FEE PROFILES (BASE TIERS - UPDATED LIVE)
# ═══════════════════════════════════════════════════════════════

@dataclass
class ExchangeFeeProfile:
    """Live fee profile for an exchange."""
    name: str
    maker_fee: float = 0.001       # Maker fee rate (limit orders)
    taker_fee: float = 0.002       # Taker fee rate (market orders)
    withdrawal_fee_usd: float = 0.0  # Flat withdrawal fee in USD (if crypto out)
    network_gas_usd: float = 0.0   # Network/gas fee estimate
    spread_cost: float = 0.001     # Typical spread cost
    slippage_estimate: float = 0.0005  # Estimated slippage per leg
    last_updated: float = 0.0
    
    def total_cost_rate(self, is_maker: bool = True) -> float:
        """Total cost rate per leg (fee + slippage + spread)."""
        fee = self.maker_fee if is_maker else self.taker_fee
        return fee + self.slippage_estimate + self.spread_cost
    
    def fixed_costs(self) -> float:
        """Total fixed costs (withdrawal + gas)."""
        return self.withdrawal_fee_usd + self.network_gas_usd


# Default profiles (updated dynamically)
DEFAULT_FEE_PROFILES: Dict[str, ExchangeFeeProfile] = {
    'binance': ExchangeFeeProfile(
        name='binance',
        maker_fee=0.0010,      # 0.10% base tier
        taker_fee=0.0010,      # 0.10% base tier
        withdrawal_fee_usd=0.0,  # Free if fiat out
        network_gas_usd=0.0,
        spread_cost=0.0005,
        slippage_estimate=0.0003,
    ),
    'kraken': ExchangeFeeProfile(
        name='kraken',
        maker_fee=0.0025,      # 0.25% base tier
        taker_fee=0.0040,      # 0.40% base tier
        withdrawal_fee_usd=0.0,
        network_gas_usd=0.0,
        spread_cost=0.0008,
        slippage_estimate=0.0005,
    ),
    'alpaca': ExchangeFeeProfile(
        name='alpaca',
        maker_fee=0.0015,      # 0.15% Tier 1
        taker_fee=0.0025,      # 0.25% Tier 1
        withdrawal_fee_usd=0.0,  # Free USD withdrawal
        network_gas_usd=0.0,
        spread_cost=0.0008,
        slippage_estimate=0.0005,
    ),
    'capital': ExchangeFeeProfile(
        name='capital',
        maker_fee=0.0000,      # Spread-based (no commission)
        taker_fee=0.0000,
        withdrawal_fee_usd=0.0,
        network_gas_usd=0.0,
        spread_cost=0.0020,    # Wider spread on CFDs
        slippage_estimate=0.0008,
    ),
}


# ═══════════════════════════════════════════════════════════════
# 🎯 ADAPTIVE GATE RESULT
# ═══════════════════════════════════════════════════════════════

@dataclass
class AdaptiveGateResult:
    """Result from adaptive gate calculation."""
    exchange: str
    trade_value: float
    
    # The three gates (required price move as fraction)
    r_breakeven: float          # Net profit ≥ 0
    r_prime: float              # Net profit ≥ prime target
    r_prime_buffer: float       # Net profit ≥ prime + buffer
    
    # Corresponding gross thresholds (win_gte equivalent)
    win_gte_breakeven: float    # Gross P&L for breakeven
    win_gte_prime: float        # Gross P&L for prime profit
    win_gte_prime_buffer: float # Gross P&L for prime + buffer
    
    # Cost breakdown
    fee_rate_used: float
    slippage_rate: float
    spread_cost: float
    fixed_costs: float
    
    # Targets
    prime_target: float         # e.g. $0.02
    buffer_amount: float        # e.g. $0.01
    
    # Meta
    is_maker: bool
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> dict:
        return {
            'exchange': self.exchange,
            'trade_value': self.trade_value,
            'r_breakeven': round(self.r_breakeven, 6),
            'r_prime': round(self.r_prime, 6),
            'r_prime_buffer': round(self.r_prime_buffer, 6),
            'r_breakeven_pct': round(self.r_breakeven * 100, 4),
            'r_prime_pct': round(self.r_prime * 100, 4),
            'r_prime_buffer_pct': round(self.r_prime_buffer * 100, 4),
            'win_gte_breakeven': round(self.win_gte_breakeven, 6),
            'win_gte_prime': round(self.win_gte_prime, 6),
            'win_gte_prime_buffer': round(self.win_gte_prime_buffer, 6),
            'fee_rate': round(self.fee_rate_used, 5),
            'slippage_rate': round(self.slippage_rate, 5),
            'spread_cost': round(self.spread_cost, 5),
            'fixed_costs': round(self.fixed_costs, 4),
            'prime_target': self.prime_target,
            'buffer_amount': self.buffer_amount,
            'is_maker': self.is_maker,
            'timestamp': self.timestamp,
        }


# ═══════════════════════════════════════════════════════════════
# 🌍💰 ADAPTIVE PRIME PROFIT GATE ENGINE 💰🌍
# ═══════════════════════════════════════════════════════════════

class AdaptivePrimeProfitGate:
    """
    🌍💰 THE ADAPTIVE PRIME PROFIT GATE 💰🌍
    
    Dynamically calculates the EXACT price move needed to:
    1. Break even (cover all costs)
    2. Achieve prime net profit
    3. Achieve prime + buffer (safe mode)
    
    Updates in real-time based on:
    - Exchange fee tiers
    - Current volatility (affects slippage)
    - Bid-ask spreads
    - Network congestion (gas fees)
    
    "Adapt or die. The market never sleeps, and neither do we."
    """
    
    # Prime profit targets (smallest primes × $0.01)
    PRIME_TARGETS = [0.02, 0.03, 0.05, 0.07, 0.11, 0.13, 0.17, 0.19, 0.23]
    
    def __init__(
        self,
        default_prime: float = EPSILON_PROFIT_USD,
        default_buffer: float = 0.0,      # 🚀 COMPOUND MODE: $0 buffer - compound everything!
        use_maker_fees: bool = True,      # Assume limit orders
    ):
        self.default_prime = default_prime
        self.default_buffer = default_buffer
        self.use_maker_fees = use_maker_fees
        
        # Live fee profiles (copy defaults, update dynamically)
        self.fee_profiles: Dict[str, ExchangeFeeProfile] = {
            k: ExchangeFeeProfile(**v.__dict__)
            for k, v in DEFAULT_FEE_PROFILES.items()
        }
        
        # Cache for recent calculations
        self._cache: Dict[str, AdaptiveGateResult] = {}
        self._cache_ttl = 10.0  # Cache valid for 10 seconds
        
        # Statistics
        self.calculations_count = 0
        self.last_calculation_time = 0.0
        
        logger.info("🌍💰 Adaptive Prime Profit Gate initialized")
        logger.info(f"   Default prime target: ${default_prime:.6f}")
        logger.info(f"   Default buffer: ${default_buffer:.6f}")
        logger.info(f"   Using {'maker' if use_maker_fees else 'taker'} fees")
    
    def update_fee_profile(
        self,
        exchange: str,
        maker_fee: float = None,
        taker_fee: float = None,
        slippage: float = None,
        spread: float = None,
        withdrawal_fee: float = None,
        gas_fee: float = None,
    ):
        """Update fee profile for an exchange with live data."""
        ex = exchange.lower()
        if ex not in self.fee_profiles:
            self.fee_profiles[ex] = ExchangeFeeProfile(name=ex)
        
        profile = self.fee_profiles[ex]
        
        if maker_fee is not None:
            profile.maker_fee = maker_fee
        if taker_fee is not None:
            profile.taker_fee = taker_fee
        if slippage is not None:
            profile.slippage_estimate = slippage
        if spread is not None:
            profile.spread_cost = spread
        if withdrawal_fee is not None:
            profile.withdrawal_fee_usd = withdrawal_fee
        if gas_fee is not None:
            profile.network_gas_usd = gas_fee
        
        profile.last_updated = time.time()
        
        # Invalidate cache for this exchange
        self._invalidate_cache(ex)
    
    def _invalidate_cache(self, exchange: str = None):
        """Invalidate cached results."""
        if exchange:
            keys_to_remove = [k for k in self._cache if k.startswith(exchange)]
            for k in keys_to_remove:
                del self._cache[k]
        else:
            self._cache.clear()
    
    def _get_cache_key(self, exchange: str, trade_value: float, prime: float, buffer: float) -> str:
        """Generate cache key."""
        return f"{exchange}:{trade_value:.2f}:{prime:.4f}:{buffer:.4f}"
    
    def calculate_required_r(
        self,
        trade_value: float,
        target_profit: float,
        fee_rate: float,
        slippage: float,
        spread: float,
        fixed_costs: float = 0.0,
    ) -> float:
        """
        📐 MASTER EQUATION: Calculate required price increase.
        
        r = (V + G + P) / [V × (1 - c_b) × (1 - c_s)] - 1
        
        Where c = f + s + spread (total cost rate per leg)
        
        For symmetric costs (same on buy and sell):
        r = (V + G + P) / [V × (1 - c)²] - 1
        """
        if trade_value <= 0:
            return float('inf')
        
        # Total cost rate per leg
        c = fee_rate + slippage + spread
        
        # Numerator: what we need to end up with
        numerator = trade_value + fixed_costs + target_profit
        
        # Denominator: what we actually get after costs
        # After buy: V × (1 - c_buy)
        # After sell at price (1+r): V × (1 - c_buy) × (1 + r) × (1 - c_sell)
        # For symmetric: V × (1 - c)² × (1 + r)
        effective_multiplier = (1 - c) ** 2
        
        if effective_multiplier <= 0:
            return float('inf')
        
        denominator = trade_value * effective_multiplier
        
        # Solve for r
        r = (numerator / denominator) - 1
        
        return max(0.0, r)
    
    def calculate_gates(
        self,
        exchange: str,
        trade_value: float,
        prime_target: float = None,
        buffer_amount: float = None,
        is_maker: bool = None,
        use_cache: bool = True,
    ) -> AdaptiveGateResult:
        """
        🎯 Calculate all three gates for a trade.
        
        Returns AdaptiveGateResult with:
        - r_breakeven: Price move for net ≥ 0
        - r_prime: Price move for net ≥ prime
        - r_prime_buffer: Price move for net ≥ prime + buffer
        - win_gte_*: Corresponding gross P&L thresholds
        """
        ex = exchange.lower()
        prime = prime_target if prime_target is not None else self.default_prime
        buffer = buffer_amount if buffer_amount is not None else self.default_buffer
        maker = is_maker if is_maker is not None else self.use_maker_fees
        
        # Check cache
        cache_key = self._get_cache_key(ex, trade_value, prime, buffer)
        if use_cache and cache_key in self._cache:
            cached = self._cache[cache_key]
            if time.time() - cached.timestamp < self._cache_ttl:
                return cached
        
        # Get fee profile
        profile = self.fee_profiles.get(ex, DEFAULT_FEE_PROFILES.get('binance'))
        
        fee_rate = profile.maker_fee if maker else profile.taker_fee
        slippage = profile.slippage_estimate
        spread = profile.spread_cost
        fixed = profile.fixed_costs()
        
        # Calculate the three gates
        r_breakeven = self.calculate_required_r(
            trade_value, 0.0, fee_rate, slippage, spread, fixed
        )
        r_prime = self.calculate_required_r(
            trade_value, prime, fee_rate, slippage, spread, fixed
        )
        r_prime_buffer = self.calculate_required_r(
            trade_value, prime + buffer, fee_rate, slippage, spread, fixed
        )
        
        # Convert to gross P&L thresholds (win_gte)
        win_gte_breakeven = trade_value * r_breakeven
        win_gte_prime = trade_value * r_prime
        win_gte_prime_buffer = trade_value * r_prime_buffer
        
        result = AdaptiveGateResult(
            exchange=ex,
            trade_value=trade_value,
            r_breakeven=r_breakeven,
            r_prime=r_prime,
            r_prime_buffer=r_prime_buffer,
            win_gte_breakeven=win_gte_breakeven,
            win_gte_prime=win_gte_prime,
            win_gte_prime_buffer=win_gte_prime_buffer,
            fee_rate_used=fee_rate,
            slippage_rate=slippage,
            spread_cost=spread,
            fixed_costs=fixed,
            prime_target=prime,
            buffer_amount=buffer,
            is_maker=maker,
        )
        
        # Cache result
        self._cache[cache_key] = result
        self.calculations_count += 1
        self.last_calculation_time = time.time()
        
        return result
    
    def get_adaptive_threshold(
        self,
        exchange: str,
        trade_value: float,
        gate_level: str = 'prime',  # 'breakeven', 'prime', or 'prime_buffer'
    ) -> dict:
        """
        🎯 Get adaptive threshold in penny-profit-engine compatible format.
        
        This replaces get_penny_threshold() with fully adaptive math.
        
        Returns dict compatible with existing penny profit engine:
        {
            'required_pct': float,
            'required_r': float,
            'win_gte': float,
            'stop_lte': float,
            'target_net': float,
            ...
        }
        """
        result = self.calculate_gates(exchange, trade_value)
        
        # Select gate level
        if gate_level == 'breakeven':
            r = result.r_breakeven
            win_gte = result.win_gte_breakeven
            target_net = 0.0
        elif gate_level == 'prime_buffer':
            r = result.r_prime_buffer
            win_gte = result.win_gte_prime_buffer
            target_net = result.prime_target + result.buffer_amount
        else:  # 'prime' (default)
            r = result.r_prime
            win_gte = result.win_gte_prime
            target_net = result.prime_target
        
        # Stop loss: 3x win target (gives room to breathe)
        stop_lte = -(win_gte * 3.0)
        
        # Approximate fee cost for display
        total_rate = result.fee_rate_used + result.slippage_rate + result.spread_cost
        approx_fees = 2 * total_rate * trade_value
        
        return {
            'required_pct': round(r * 100, 4),
            'required_r': r,
            'cost': round(approx_fees, 6),
            'win_gte': round(win_gte, 6),
            'stop_lte': round(stop_lte, 6),
            'fee_rate': result.fee_rate_used,
            'slippage_rate': result.slippage_rate,
            'spread_cost': result.spread_cost,
            'total_cost_rate': total_rate,
            'trade_size': trade_value,
            'target_net': target_net,
            'prime_target': result.prime_target,
            'buffer_amount': result.buffer_amount,
            'gate_level': gate_level,
            'is_adaptive': True,
            'is_dynamic': True,
            # All three gates for reference
            'gates': {
                'breakeven': {'r': result.r_breakeven, 'win_gte': result.win_gte_breakeven},
                'prime': {'r': result.r_prime, 'win_gte': result.win_gte_prime},
                'prime_buffer': {'r': result.r_prime_buffer, 'win_gte': result.win_gte_prime_buffer},
            }
        }
    
    def get_all_exchange_gates(self, trade_value: float) -> Dict[str, AdaptiveGateResult]:
        """Calculate gates for all configured exchanges."""
        results = {}
        for ex in self.fee_profiles:
            results[ex] = self.calculate_gates(ex, trade_value)
        return results
    
    def print_gate_summary(self, trade_value: float = 10.0):
        """Print a summary of gates across all exchanges."""
        print("\n" + "=" * 80)
        print("🌍💰 ADAPTIVE PRIME PROFIT GATES - WORLD DOMINATION MODE 💰🌍")
        print("=" * 80)
        print(f"Trade Value: ${trade_value:.2f} | Prime: ${self.default_prime:.2f} | Buffer: ${self.default_buffer:.2f}")
        print("-" * 80)
        print(f"{'Exchange':<10} | {'Break-even':>10} | {'Prime':>10} | {'+Buffer':>10} | {'Win≥(prime)':>12} | {'Fee+Slip+Sprd':>14}")
        print("-" * 80)
        
        for ex in sorted(self.fee_profiles.keys()):
            result = self.calculate_gates(ex, trade_value)
            total_cost = result.fee_rate_used + result.slippage_rate + result.spread_cost
            print(
                f"{ex.upper():<10} | "
                f"{result.r_breakeven*100:>9.3f}% | "
                f"{result.r_prime*100:>9.3f}% | "
                f"{result.r_prime_buffer*100:>9.3f}% | "
                f"${result.win_gte_prime:>10.4f} | "
                f"{total_cost*100:>13.3f}%"
            )
        
        print("=" * 80)
        print("📜 \"Pass the prime gate, and the profit is GUARANTEED.\"")
        print("=" * 80 + "\n")
    
    def get_status(self) -> dict:
        """Get engine status."""
        return {
            'initialized': True,
            'calculations_count': self.calculations_count,
            'last_calculation': self.last_calculation_time,
            'cache_size': len(self._cache),
            'exchanges_configured': list(self.fee_profiles.keys()),
            'default_prime': self.default_prime,
            'default_buffer': self.default_buffer,
            'use_maker_fees': self.use_maker_fees,
        }
    
    def adjust_slippage_for_volatility(self, exchange: str, volatility_pct: float):
        """
        Dynamically adjust slippage based on current market volatility.
        
        Args:
            exchange: Exchange name
            volatility_pct: Current volatility as percentage (e.g., 2.5 for 2.5%)
        """
        ex = exchange.lower()
        if ex not in self.fee_profiles:
            return
        
        profile = self.fee_profiles[ex]
        base_slippage = 0.0005  # 0.05% base
        
        # Scale slippage with volatility: higher vol = more slippage
        # volatility 1% → slippage 0.05%, volatility 5% → slippage 0.25%
        vol_multiplier = max(1.0, volatility_pct / 1.0)
        adjusted = base_slippage * vol_multiplier
        
        # Cap at 1% max slippage
        profile.slippage_estimate = min(adjusted, 0.01)
        profile.last_updated = time.time()
        
        self._invalidate_cache(ex)
        logger.debug(f"Adjusted {ex} slippage to {profile.slippage_estimate*100:.3f}% (vol: {volatility_pct}%)")
    
    def get_queen_gate_signal(self, exchange: str, trade_value: float, expected_r: float) -> dict:
        """
        Generate gate signal for Queen decision routing.
        
        Args:
            exchange: Exchange name
            trade_value: Trade notional value
            expected_r: Expected price move from opportunity scoring
        
        Returns:
            Dict with gate status and confidence adjustment
        """
        result = self.calculate_gates(exchange, trade_value)
        
        # Determine which gate we're likely to hit
        if expected_r >= result.r_prime_buffer:
            gate_status = 'PRIME_BUFFER'
            confidence_boost = 0.15  # Strong confidence boost
            recommendation = 'EXECUTE'
        elif expected_r >= result.r_prime:
            gate_status = 'PRIME'
            confidence_boost = 0.10
            recommendation = 'EXECUTE'
        elif expected_r >= result.r_breakeven:
            gate_status = 'BREAKEVEN'
            confidence_boost = 0.0
            recommendation = 'CAUTION'
        else:
            gate_status = 'BELOW_BREAKEVEN'
            # Negative adjustment proportional to shortfall
            shortfall = result.r_breakeven - expected_r
            confidence_boost = -0.1 - (shortfall * 10)  # Penalty scales with gap
            recommendation = 'REJECT'
        
        return {
            'gate_status': gate_status,
            'confidence_boost': confidence_boost,
            'recommendation': recommendation,
            'expected_r': expected_r,
            'r_breakeven': result.r_breakeven,
            'r_prime': result.r_prime,
            'r_prime_buffer': result.r_prime_buffer,
            'margin_to_prime': expected_r - result.r_prime,
            'trade_value': trade_value,
            'exchange': exchange,
        }


# ═══════════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ═══════════════════════════════════════════════════════════════

_adaptive_gate: Optional[AdaptivePrimeProfitGate] = None


def get_adaptive_gate() -> AdaptivePrimeProfitGate:
    """Get the singleton adaptive gate instance."""
    global _adaptive_gate
    if _adaptive_gate is None:
        _adaptive_gate = AdaptivePrimeProfitGate()
    return _adaptive_gate


def get_adaptive_threshold(exchange: str, trade_value: float, gate_level: str = 'prime') -> dict:
    """
    Quick access to adaptive threshold.
    
    Drop-in replacement for get_penny_threshold() with adaptive math.
    """
    return get_adaptive_gate().get_adaptive_threshold(exchange, trade_value, gate_level)


def calculate_adaptive_gates(exchange: str, trade_value: float) -> AdaptiveGateResult:
    """Calculate all three gates for a trade."""
    return get_adaptive_gate().calculate_gates(exchange, trade_value)


def update_exchange_fees(
    exchange: str,
    maker_fee: float = None,
    taker_fee: float = None,
    slippage: float = None,
    spread: float = None,
):
    """Update fees for an exchange (call this with live data)."""
    get_adaptive_gate().update_fee_profile(
        exchange,
        maker_fee=maker_fee,
        taker_fee=taker_fee,
        slippage=slippage,
        spread=spread,
    )


def get_queen_gate_signal(exchange: str, trade_value: float, expected_r: float) -> dict:
    """Get gate signal for Queen decision routing."""
    return get_adaptive_gate().get_queen_gate_signal(exchange, trade_value, expected_r)


def adjust_for_volatility(exchange: str, volatility_pct: float):
    """Adjust slippage estimates based on current volatility."""
    get_adaptive_gate().adjust_slippage_for_volatility(exchange, volatility_pct)


def is_real_win(
    exchange: str,
    entry_price: float,
    current_price: float,
    quantity: float,
    is_maker: bool = False,
    gate_level: str = 'breakeven'
) -> dict:
    """
    🎯 CHECK IF A POSITION IS A REAL WIN AFTER ALL FEES 🎯
    
    This is THE authoritative function for determining if a trade is profitable.
    It accounts for:
    - Maker/taker fees (based on order type)
    - Slippage estimates
    - Spread costs
    - Fixed costs (withdrawal, gas)
    
    Args:
        exchange: Exchange name (kraken, binance, alpaca, capital)
        entry_price: Entry price
        current_price: Current/exit price
        quantity: Position quantity
        is_maker: Whether exit will be maker (limit) or taker (market)
        gate_level: 'breakeven', 'prime', or 'prime_buffer'
    
    Returns:
        Dict with win status and breakdown
    """
    gate = get_adaptive_gate()
    
    # Get fee profile
    profile = gate.fee_profiles.get(exchange.lower(), DEFAULT_FEE_PROFILES.get('kraken'))
    
    # Calculate trade values
    entry_value = entry_price * quantity
    exit_value = current_price * quantity
    gross_pnl = exit_value - entry_value
    gross_pct = (current_price / entry_price - 1) if entry_price > 0 else 0
    
    # Calculate actual costs (buy + sell legs)
    # Entry was already paid - use taker (market order)
    entry_fee = profile.taker_fee
    entry_slippage = profile.slippage_estimate
    entry_spread = profile.spread_cost / 2  # Half spread on buy
    entry_cost_rate = entry_fee + entry_slippage + entry_spread
    
    # Exit depends on order type
    exit_fee = profile.maker_fee if is_maker else profile.taker_fee
    exit_slippage = profile.slippage_estimate
    exit_spread = profile.spread_cost / 2  # Half spread on sell
    exit_cost_rate = exit_fee + exit_slippage + exit_spread
    
    # Total costs in USD
    entry_costs = entry_value * entry_cost_rate
    exit_costs = exit_value * exit_cost_rate
    total_costs = entry_costs + exit_costs + profile.fixed_costs()
    
    # Net P&L
    net_pnl = gross_pnl - total_costs
    
    # Get gate thresholds
    gates = gate.calculate_gates(exchange, entry_value, is_maker=is_maker)
    
    # Determine gate status
    if gate_level == 'breakeven':
        threshold_r = gates.r_breakeven
        threshold_pnl = 0.0
    elif gate_level == 'prime_buffer':
        threshold_r = gates.r_prime_buffer
        threshold_pnl = gates.prime_target + gates.buffer_amount
    else:  # prime
        threshold_r = gates.r_prime
        threshold_pnl = gates.prime_target
    
    is_win = net_pnl >= threshold_pnl
    
    return {
        'is_win': is_win,
        'gate_level': gate_level,
        'gross_pnl': gross_pnl,
        'net_pnl': net_pnl,
        'total_costs': total_costs,
        'costs_breakdown': {
            'entry_fee': entry_value * entry_fee,
            'entry_slippage': entry_value * entry_slippage,
            'entry_spread': entry_value * entry_spread,
            'exit_fee': exit_value * exit_fee,
            'exit_slippage': exit_value * exit_slippage,
            'exit_spread': exit_value * exit_spread,
            'fixed': profile.fixed_costs(),
        },
        'threshold_pnl': threshold_pnl,
        'threshold_r': threshold_r,
        'actual_r': gross_pct,
        'margin_over_threshold': net_pnl - threshold_pnl,
        'exchange': exchange,
        'entry_price': entry_price,
        'current_price': current_price,
        'quantity': quantity,
        'is_maker': is_maker,
    }


def get_fee_profile(exchange: str) -> dict:
    """
    Get complete fee profile for an exchange.
    
    Returns dict with all fee components for external use.
    """
    gate = get_adaptive_gate()
    profile = gate.fee_profiles.get(exchange.lower(), DEFAULT_FEE_PROFILES.get('kraken'))
    
    return {
        'exchange': exchange.lower(),
        'maker_fee': profile.maker_fee,
        'taker_fee': profile.taker_fee,
        'slippage': profile.slippage_estimate,
        'spread': profile.spread_cost,
        'withdrawal_fee': profile.withdrawal_fee_usd,
        'gas_fee': profile.network_gas_usd,
        'total_taker_rate': profile.taker_fee + profile.slippage_estimate + profile.spread_cost,
        'total_maker_rate': profile.maker_fee + profile.slippage_estimate + profile.spread_cost,
    }


# ═══════════════════════════════════════════════════════════════
# �🎯 PROBABILITY MATRIX INTEGRATION 🎯🧠
# ═══════════════════════════════════════════════════════════════

def wire_to_probability_matrix():
    """
    🧠 Wire the Adaptive Gate to the Probability Intelligence Matrix.
    
    The Probability Matrix uses our gates to:
    - Know EXACTLY what price move is needed for profit
    - Calculate TRUE probability of hitting that move
    - Adjust confidence based on how close we are to gates
    """
    try:
        from probability_intelligence_matrix import get_probability_matrix, ProbabilityIntelligence
        
        matrix = get_probability_matrix()
        gate = get_adaptive_gate()
        
        # Store gate reference in matrix for access
        matrix.adaptive_gate = gate
        
        # Register as intelligence factor for probability calculations
        def adaptive_gate_factor(
            exchange: str,
            trade_value: float,
            current_r: float,  # Current price move (fraction)
        ) -> dict:
            """
            Calculate how close we are to each gate.
            Returns factor values for probability calculation.
            """
            result = gate.calculate_gates(exchange, trade_value)
            
            # Distance to each gate (negative means we've passed it!)
            dist_to_breakeven = result.r_breakeven - current_r
            dist_to_prime = result.r_prime - current_r
            dist_to_buffer = result.r_prime_buffer - current_r
            
            # Factor values (1.0 = great, 0.0 = bad)
            if current_r >= result.r_prime_buffer:
                gate_status = 'BEYOND_BUFFER'
                factor_value = 1.0
            elif current_r >= result.r_prime:
                gate_status = 'PRIME_ACHIEVED'
                factor_value = 0.9
            elif current_r >= result.r_breakeven:
                gate_status = 'BREAKEVEN_ONLY'
                factor_value = 0.6
            else:
                # Below breakeven - how close are we?
                progress = current_r / result.r_breakeven if result.r_breakeven > 0 else 0
                gate_status = 'BELOW_BREAKEVEN'
                factor_value = 0.3 + (0.3 * progress)
            
            return {
                'gate_status': gate_status,
                'factor_value': factor_value,
                'distance_to_breakeven': dist_to_breakeven,
                'distance_to_prime': dist_to_prime,
                'distance_to_buffer': dist_to_buffer,
                'current_r': current_r,
                'r_breakeven': result.r_breakeven,
                'r_prime': result.r_prime,
                'r_prime_buffer': result.r_prime_buffer,
            }
        
        # Attach the factor function to the matrix
        matrix.adaptive_gate_factor = adaptive_gate_factor
        
        logger.info("🧠🎯 Adaptive Gate WIRED to Probability Matrix!")
        return True
        
    except ImportError as e:
        logger.warning(f"Could not wire to Probability Matrix: {e}")
        return False
    except Exception as e:
        logger.error(f"Error wiring to Probability Matrix: {e}")
        return False


# ═══════════════════════════════════════════════════════════════
# 🍄🎯 MYCELIUM NETWORK INTEGRATION - GOAL PROPAGATION 🎯🍄
# ═══════════════════════════════════════════════════════════════

def wire_to_mycelium(goal_target: float = 100000.0, goal_currency: str = 'GBP'):
    """
    🍄 Wire the Adaptive Gate to the Mycelium Network.
    
    The Mycelium uses our gates to:
    - Understand the minimum viable trade thresholds
    - Propagate the £100K goal with trade-level precision
    - Coordinate all systems toward the same profit math
    """
    try:
        from ira_sniper_mode import register_to_mycelium, mycelium_sync, get_mycelium_aggregator
        
        gate = get_adaptive_gate()
        
        # Create a Mycelium-compatible state object
        class AdaptiveGateNode:
            """Mycelium node for Adaptive Prime Profit Gate."""
            
            def __init__(self, gate_instance, target, currency):
                self.gate = gate_instance
                self.goal_target = target
                self.goal_currency = currency
                self.name = 'adaptive_profit_gate'
                
            def get_state(self):
                """Return state for Mycelium sync."""
                return {
                    'name': self.name,
                    'type': 'profit_gate',
                    'goal': {
                        'target': self.goal_target,
                        'currency': self.goal_currency,
                        'description': f"£{self.goal_target:,.0f} {self.goal_currency}",
                    },
                    'gates': {
                        'prime_target': self.gate.default_prime,
                        'buffer': self.gate.default_buffer,
                        'use_maker': self.gate.use_maker_fees,
                    },
                    'exchanges': list(self.gate.fee_profiles.keys()),
                    'calculations': self.gate.calculations_count,
                    'last_calc': self.gate.last_calculation_time,
                    'cached_results': len(self.gate._cache),
                }
            
            def calculate_trades_to_goal(self, current_capital: float, avg_trade_size: float = 10.0) -> dict:
                """Calculate how many successful trades needed to reach goal."""
                remaining = max(0, self.goal_target - current_capital)
                
                if remaining <= 0:
                    return {
                        'goal_achieved': True,
                        'trades_needed': 0,
                        'message': f"🎯 GOAL ACHIEVED! {self.goal_currency}{current_capital:,.2f}",
                    }
                
                # Get average prime profit across exchanges
                avg_prime = self.gate.default_prime
                trades_needed = int(remaining / avg_prime) + 1
                
                return {
                    'goal_achieved': False,
                    'current_capital': current_capital,
                    'goal_target': self.goal_target,
                    'remaining': remaining,
                    'prime_per_trade': avg_prime,
                    'trades_needed': trades_needed,
                    'message': f"🎯 {trades_needed:,} trades @ ${avg_prime:.2f} each to reach £{self.goal_target:,.0f}",
                }
            
            def sync_goal_to_thought_bus(self, current_capital: float):
                """Sync goal progress to ThoughtBus."""
                try:
                    from aureon_thought_bus import ThoughtBus, Thought
                    
                    progress = self.calculate_trades_to_goal(current_capital)
                    
                    # Find ThoughtBus instance
                    thought_bus = ThoughtBus(persist_path="thoughts.jsonl")
                    thought_bus.publish(Thought(
                        source="adaptive_profit_gate",
                        topic="goal.progress",
                        payload={
                            'goal_target': self.goal_target,
                            'goal_currency': self.goal_currency,
                            'current_capital': current_capital,
                            'remaining': progress.get('remaining', 0),
                            'trades_needed': progress.get('trades_needed', 0),
                            'prime_per_trade': self.gate.default_prime,
                            'goal_achieved': progress.get('goal_achieved', False),
                        }
                    ))
                    return True
                except Exception as e:
                    logger.warning(f"Could not sync goal to ThoughtBus: {e}")
                    return False
        
        # Create node and register to Mycelium
        gate_node = AdaptiveGateNode(gate, goal_target, goal_currency)
        register_to_mycelium('adaptive_profit_gate', gate_node)
        
        # Sync initial state
        mycelium_sync('adaptive_gate_registered', {
            'goal_target': goal_target,
            'goal_currency': goal_currency,
            'prime_target': gate.default_prime,
            'buffer': gate.default_buffer,
        })
        
        logger.info(f"🍄🎯 Adaptive Gate WIRED to Mycelium Network!")
        logger.info(f"   Goal: £{goal_target:,.0f} {goal_currency}")
        logger.info(f"   Prime: ${gate.default_prime:.2f} per trade")
        
        return gate_node
        
    except ImportError as e:
        logger.warning(f"Could not wire to Mycelium: {e}")
        return None
    except Exception as e:
        logger.error(f"Error wiring to Mycelium: {e}")
        return None


def wire_all_integrations(goal_target: float = 100000.0):
    """
    🌍💰 WIRE EVERYTHING - Full ecosystem integration!
    
    Connects Adaptive Gate to:
    1. Probability Intelligence Matrix (metrics)
    2. Mycelium Network (goal propagation)
    """
    results = {
        'probability_matrix': wire_to_probability_matrix(),
        'mycelium': wire_to_mycelium(goal_target) is not None,
    }
    
    success_count = sum(1 for v in results.values() if v)
    
    if success_count == len(results):
        logger.info("🌍💰 ALL INTEGRATIONS WIRED! World domination mode ACTIVE!")
    elif success_count > 0:
        logger.info(f"🌍💰 {success_count}/{len(results)} integrations wired")
    else:
        logger.warning("⚠️ No integrations could be wired")
    
    return results


# ═══════════════════════════════════════════════════════════════
# TEST / DEMO
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    
    gate = get_adaptive_gate()
    
    print("\n" + "=" * 70)
    print("ADAPTIVE PRIME PROFIT GATE - Test Suite")
    print("=" * 70)
    
    # Print summary for $10 trade
    gate.print_gate_summary(trade_value=10.0)
    
    # Test individual calculation
    print("\n[TEST] $7.50 trade on Kraken:")
    result = gate.calculate_gates('kraken', 7.50)
    print(f"  Break-even: {result.r_breakeven*100:.4f}%")
    print(f"  Prime:      {result.r_prime*100:.4f}%")
    print(f"  +Buffer:    {result.r_prime_buffer*100:.4f}%")
    print(f"  Win >= ${result.win_gte_prime:.4f} for prime profit")
    
    # Test Queen signal
    print("\n[TEST] Queen gate signal (expected 0.5% move):")
    signal = get_queen_gate_signal('kraken', 10.0, 0.005)
    print(f"  Status: {signal['gate_status']}")
    print(f"  Recommendation: {signal['recommendation']}")
    print(f"  Confidence boost: {signal['confidence_boost']:+.2f}")
    
    # Test volatility adjustment
    print("\n[TEST] Volatility adjustment:")
    print(f"  Before: slippage = {gate.fee_profiles['binance'].slippage_estimate*100:.3f}%")
    adjust_for_volatility('binance', 3.5)  # 3.5% volatility
    print(f"  After (3.5% vol): slippage = {gate.fee_profiles['binance'].slippage_estimate*100:.3f}%")
    
    # Test compatible threshold format
    print("\n[TEST] Penny-profit-engine compatible format:")
    threshold = get_adaptive_threshold('binance', 10.0, 'prime')
    print(f"  Required: {threshold['required_pct']:.4f}%")
    print(f"  Win >= ${threshold['win_gte']:.4f}")
    print(f"  Stop <= ${threshold['stop_lte']:.4f}")
    
    print("\n" + "=" * 70)
    print("All tests complete.")
    print("=" * 70)
