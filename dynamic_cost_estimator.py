#!/usr/bin/env python3
"""
💰 DYNAMIC COST ESTIMATOR 💰
============================

Learns actual trading costs from recent executions and provides
conservative, data-driven cost estimates for Monte Carlo approval.

FEATURES:
- Rolling window of recent realized fees/spreads
- Conservative floor/ceiling bounds (never too optimistic)
- Fallback to safe defaults when no data available
- Per-symbol cost tracking with global fallback

Gary Leckey | January 2026 | TRUST THE MATH, LEARN FROM REALITY
"""

import sys
import os

# Windows UTF-8 fix
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


@dataclass
class CostSample:
    """A single cost observation."""
    timestamp: float
    symbol: str
    side: str  # 'buy' or 'sell'
    notional_usd: float
    fee_pct: float
    spread_pct: float
    slippage_pct: float
    total_cost_pct: float


@dataclass
class CostEstimate:
    """Estimated costs for a trade."""
    symbol: str
    side: str
    estimated_fee_pct: float
    estimated_spread_pct: float
    estimated_slippage_pct: float
    estimated_total_pct: float
    confidence: float  # 0-1 (based on sample count)
    sample_count: int
    source: str  # 'symbol_specific', 'global_average', 'fallback'


class DynamicCostEstimator:
    """
    Learns from recent trades to provide dynamic cost estimates.
    
    PHILOSOPHY:
    - Use recent data when available
    - Conservative floor (never underestimate costs)
    - Safe ceiling (cap extreme outliers)
    - Fallback to known defaults when no data
    
    ROLLING WINDOWS:
    - Per-symbol: last 20 samples (symbol-specific learning)
    - Global: last 100 samples (exchange-wide baseline)
    - Window age: samples older than 24h decay in weight
    """
    
    # Conservative bounds (never estimate below/above these)
    MIN_FEE_PCT = 0.10      # 10 bps (tier 8 best case = 10 bps taker)
    MAX_FEE_PCT = 0.30      # 30 bps (tier 1 worst case = 25 bps + buffer)
    MIN_SPREAD_PCT = 0.05   # 5 bps (highly liquid pairs)
    MAX_SPREAD_PCT = 0.20   # 20 bps (less liquid pairs)
    MIN_SLIPPAGE_PCT = 0.01 # 1 bp (market orders on liquid pairs)
    MAX_SLIPPAGE_PCT = 0.65 # 65% (allow extreme slippage learning)
    
    # Fallback defaults (when no data available)
    DEFAULT_FEE_PCT = 0.20      # 20 bps (tier 3 average)
    DEFAULT_SPREAD_PCT = 0.08   # 8 bps (reasonable for liquid crypto)
    DEFAULT_SLIPPAGE_PCT = 0.02 # 2 bps (small market orders)
    DEFAULT_TOTAL_PCT = 0.30    # 30 bps total (0.20 + 0.08 + 0.02)
    
    # Window sizes
    SYMBOL_WINDOW_SIZE = 20   # Per-symbol samples
    GLOBAL_WINDOW_SIZE = 100  # Global samples
    SAMPLE_TTL_SECONDS = 86400  # 24 hours
    
    def __init__(self):
        # Per-symbol rolling windows
        self._symbol_samples: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=self.SYMBOL_WINDOW_SIZE)
        )
        
        # Global rolling window (all symbols)
        self._global_samples: deque = deque(maxlen=self.GLOBAL_WINDOW_SIZE)
        
        # Stats
        self._total_samples = 0
        self._estimates_served = 0
        
        logger.info("💰 Dynamic Cost Estimator initialized")
        logger.info(f"   Conservative floor: {self.DEFAULT_TOTAL_PCT:.2f}%")
        logger.info(f"   Symbol window: {self.SYMBOL_WINDOW_SIZE} samples")
        logger.info(f"   Global window: {self.GLOBAL_WINDOW_SIZE} samples")
    
    def add_sample(
        self,
        symbol: str,
        side: str,
        notional_usd: float,
        fee_pct: float,
        spread_pct: float,
        slippage_pct: float
    ) -> None:
        """
        Record a new cost sample from an actual execution.
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USD')
            side: 'buy' or 'sell'
            notional_usd: Trade size in USD
            fee_pct: Realized fee as percentage (e.g., 0.15 for 15 bps)
            spread_pct: Realized spread as percentage
            slippage_pct: Realized slippage as percentage
        """
        total_cost_pct = fee_pct + spread_pct + slippage_pct
        
        sample = CostSample(
            timestamp=time.time(),
            symbol=symbol,
            side=side,
            notional_usd=notional_usd,
            fee_pct=fee_pct,
            spread_pct=spread_pct,
            slippage_pct=slippage_pct,
            total_cost_pct=total_cost_pct
        )
        
        # Add to both windows
        self._symbol_samples[symbol].append(sample)
        self._global_samples.append(sample)
        self._total_samples += 1
        
        logger.debug(
            f"💰 Cost sample: {symbol} {side} ${notional_usd:.2f} | "
            f"fee={fee_pct:.3f}% spread={spread_pct:.3f}% slip={slippage_pct:.3f}% | "
            f"total={total_cost_pct:.3f}%"
        )
    
    def estimate_cost(
        self,
        symbol: str,
        side: str,
        notional_usd: float
    ) -> CostEstimate:
        """
        Estimate costs for a trade.
        
        Priority:
        1. Symbol-specific data (if enough recent samples)
        2. Global average (if any samples exist)
        3. Conservative fallback defaults
        
        Returns:
            CostEstimate with breakdown and confidence score
        """
        self._estimates_served += 1
        now = time.time()
        
        # Try symbol-specific estimate
        symbol_samples = list(self._symbol_samples.get(symbol, []))
        if len(symbol_samples) >= 5:  # Need at least 5 samples for confidence
            # Filter recent samples (within TTL)
            recent = [s for s in symbol_samples if (now - s.timestamp) < self.SAMPLE_TTL_SECONDS]
            if len(recent) >= 3:
                return self._compute_estimate(symbol, side, recent, source='symbol_specific')
        
        # Fall back to global average
        if len(self._global_samples) >= 10:
            recent = [s for s in self._global_samples if (now - s.timestamp) < self.SAMPLE_TTL_SECONDS]
            if len(recent) >= 5:
                return self._compute_estimate(symbol, side, recent, source='global_average')
        
        # Fall back to conservative defaults
        return CostEstimate(
            symbol=symbol,
            side=side,
            estimated_fee_pct=self.DEFAULT_FEE_PCT,
            estimated_spread_pct=self.DEFAULT_SPREAD_PCT,
            estimated_slippage_pct=self.DEFAULT_SLIPPAGE_PCT,
            estimated_total_pct=self.DEFAULT_TOTAL_PCT,
            confidence=0.3,  # Low confidence with no data
            sample_count=0,
            source='fallback'
        )
    
    def _compute_estimate(
        self,
        symbol: str,
        side: str,
        samples: List[CostSample],
        source: str
    ) -> CostEstimate:
        """Compute estimate from samples with conservative bounds."""
        # Weight recent samples more heavily (exponential decay)
        now = time.time()
        weights = []
        for s in samples:
            age_hours = (now - s.timestamp) / 3600
            weight = 2.0 ** (-age_hours / 6)  # Half-life of 6 hours
            weights.append(weight)
        
        total_weight = sum(weights)
        if total_weight == 0:
            total_weight = 1.0
        
        # Weighted averages
        avg_fee = sum(s.fee_pct * w for s, w in zip(samples, weights)) / total_weight
        avg_spread = sum(s.spread_pct * w for s, w in zip(samples, weights)) / total_weight
        avg_slip = sum(s.slippage_pct * w for s, w in zip(samples, weights)) / total_weight
        
        # Apply conservative bounds (clamp)
        fee_pct = max(self.MIN_FEE_PCT, min(self.MAX_FEE_PCT, avg_fee))
        spread_pct = max(self.MIN_SPREAD_PCT, min(self.MAX_SPREAD_PCT, avg_spread))
        slip_pct = max(self.MIN_SLIPPAGE_PCT, min(self.MAX_SLIPPAGE_PCT, avg_slip))
        
        # Add 10% safety buffer to total (be pessimistic)
        total_pct = (fee_pct + spread_pct + slip_pct) * 1.10
        
        # Confidence based on sample count (more samples = higher confidence)
        confidence = min(1.0, len(samples) / 20)
        
        return CostEstimate(
            symbol=symbol,
            side=side,
            estimated_fee_pct=fee_pct,
            estimated_spread_pct=spread_pct,
            estimated_slippage_pct=slip_pct,
            estimated_total_pct=total_pct,
            confidence=confidence,
            sample_count=len(samples),
            source=source
        )
    
    def get_stats(self) -> Dict:
        """Get estimator statistics."""
        symbol_count = len(self._symbol_samples)
        symbols_with_data = sum(1 for samples in self._symbol_samples.values() if len(samples) > 0)
        
        return {
            'total_samples': self._total_samples,
            'global_window': len(self._global_samples),
            'symbol_count': symbol_count,
            'symbols_with_data': symbols_with_data,
            'estimates_served': self._estimates_served,
        }
    
    def reset(self) -> None:
        """Clear all samples (for testing or manual reset)."""
        self._symbol_samples.clear()
        self._global_samples.clear()
        self._total_samples = 0
        logger.info("💰 Cost estimator reset - all samples cleared")

    def _draw_total_costs(self, symbol: str, n_samples: int = 1000) -> List[float]:
        """Internal: draw raw samples of total cost% from historical samples.

        Returns a list of sampled total cost percentages (e.g., 0.30 == 0.30%).
        """
        import random
        base = list(self._symbol_samples.get(symbol, []))
        if not base:
            base = list(self._global_samples)
        if not base:
            return [self.DEFAULT_TOTAL_PCT for _ in range(n_samples)]

        draws = []
        for _ in range(n_samples):
            s = random.choice(base)
            # sample with small gaussian noise proportional to observed total (5% stddev)
            noise = random.gauss(0, max(1e-6, s.total_cost_pct * 0.05))
            val = s.total_cost_pct + noise
            # clamp to conservative bounds
            min_total = self.MIN_FEE_PCT + self.MIN_SPREAD_PCT + self.MIN_SLIPPAGE_PCT
            max_total = self.MAX_FEE_PCT + self.MAX_SPREAD_PCT + self.MAX_SLIPPAGE_PCT
            val = max(min_total, min(max_total, val))
            draws.append(val)
        return draws

    def sample_total_cost_distribution(self, symbol: str, side: str, notional_usd: float, n_samples: int = 1000) -> Dict[str, float]:
        """Monte Carlo sampling of total cost% from historical samples.

        Returns percentiles keyed by 'p5','p50','p90','p95' and a 'samples' list for debugging (truncated).
        """
        draws = self._draw_total_costs(symbol, n_samples=n_samples)
        draws.sort()
        def pct(p):
            idx = max(0, min(len(draws)-1, int(len(draws)*p/100)))
            return draws[idx]

        return {'p5': pct(5), 'p50': pct(50), 'p90': pct(90), 'p95': pct(95), 'samples': draws[:10]}

    def sample_total_cost_draws(self, symbol: str, side: str, notional_usd: float, n_samples: int = 1000) -> List[float]:
        """Return raw Monte Carlo draws of total cost% (percent units) for further analysis."""
        return self._draw_total_costs(symbol, n_samples=n_samples)


# Singleton instance
_instance: Optional[DynamicCostEstimator] = None


def get_cost_estimator() -> DynamicCostEstimator:
    """Get global cost estimator instance."""
    global _instance
    if _instance is None:
        _instance = DynamicCostEstimator()
    return _instance
