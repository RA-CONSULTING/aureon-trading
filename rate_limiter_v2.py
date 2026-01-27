"""Advanced adaptive rate limiter with separate buckets and backoff.

Provides:
- AdaptiveRateLimiter: Dual-bucket rate limiter with exponential backoff on 429 errors
- Separate trading and data request buckets
- Auto-recovery from backoff state
- Metrics integration for monitoring

This builds on the simple TokenBucket but adds production-ready features.
"""
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import time
import threading
from typing import Any, Dict, Optional, Tuple
import math

from rate_limiter import TokenBucket


class AdaptiveRateLimiter:
    """Adaptive rate limiter with separate buckets and exponential backoff.

    Features:
    - Separate TokenBuckets for trading and data requests
    - Exponential backoff on 429 errors with jitter
    - Auto-recovery: gradually reduce backoff over time
    - Metrics integration for monitoring rate limits and backoffs
    """

    def __init__(
        self,
        trading_rate: float = 2.5,  # Conservative trading rate (below Alpaca's 3.33/sec)
        data_rate: float = 5.0,     # Data rate for quotes/bars
        trading_capacity: Optional[float] = None,
        data_capacity: Optional[float] = None,
        name: str = "adaptive_limiter",
        max_backoff: float = 60.0,  # Max backoff 60 seconds
        backoff_multiplier: float = 2.0,
        recovery_rate: float = 0.1   # Recover 10% of backoff per second
    ):
        self.name = name
        self.max_backoff = max_backoff
        self.backoff_multiplier = backoff_multiplier
        self.recovery_rate = recovery_rate

        # Separate buckets
        self.trading_bucket = TokenBucket(
            rate=trading_rate,
            capacity=trading_capacity or max(1.0, trading_rate),
            name=f"{name}_trading"
        )
        self.data_bucket = TokenBucket(
            rate=data_rate,
            capacity=data_capacity or max(1.0, data_rate),
            name=f"{name}_data"
        )

        # Backoff state
        self._backoff_until = 0.0
        self._current_backoff = 0.0
        self._backoff_count = 0
        self._last_429 = 0.0
        self._lock = threading.Lock()

        # Metrics
        self._init_metrics()

    def _init_metrics(self):
        """Initialize metrics if available."""
        try:
            from metrics import (
                rate_limiter_backoff_seconds,
                rate_limiter_429_count,
                rate_limiter_recovery_count
            )
            # These will be created if they don't exist
            pass
        except Exception:
            pass

    def _update_metrics(self, metric_name: str, value: float = 1.0, **labels):
        """Update metrics if available."""
        try:
            from metrics import get_metric
            metric = get_metric(metric_name)
            if metric:
                if hasattr(metric, 'set'):
                    metric.set(value, **labels)
                elif hasattr(metric, 'inc'):
                    metric.inc(value, **labels)
        except Exception:
            pass

    def _is_in_backoff(self) -> bool:
        """Check if currently in backoff state."""
        return time.time() < self._backoff_until

    def _apply_backoff(self):
        """Apply exponential backoff on 429 error."""
        with self._lock:
            now = time.time()
            self._backoff_count += 1

            # Exponential backoff with jitter
            base_backoff = min(
                self.max_backoff,
                self.backoff_multiplier ** (self._backoff_count - 1)
            )
            # Add jitter (±25%)
            jitter = base_backoff * 0.25 * (2 * (hash(str(now)) % 1000) / 1000 - 1)
            self._current_backoff = base_backoff + jitter
            self._backoff_until = now + self._current_backoff
            self._last_429 = now

            self._update_metrics(
                'rate_limiter_backoff_seconds',
                self._current_backoff,
                limiter=self.name
            )
            self._update_metrics(
                'rate_limiter_429_count',
                limiter=self.name
            )

    def _recover_backoff(self):
        """Gradually recover from backoff state."""
        with self._lock:
            if not self._is_in_backoff():
                return

            now = time.time()
            elapsed = now - self._last_429

            # Recover backoff over time
            recovery_amount = elapsed * self.recovery_rate
            self._current_backoff = max(0.0, self._current_backoff - recovery_amount)

            if self._current_backoff <= 0.0:
                self._backoff_until = 0.0
                self._backoff_count = 0
                self._update_metrics(
                    'rate_limiter_recovery_count',
                    limiter=self.name
                )

    def allow_trading(self, tokens: float = 1.0) -> bool:
        """Check if trading request is allowed."""
        self._recover_backoff()
        if self._is_in_backoff():
            return False
        return self.trading_bucket.allow(tokens)

    def allow_data(self, tokens: float = 1.0) -> bool:
        """Check if data request is allowed."""
        self._recover_backoff()
        if self._is_in_backoff():
            return False
        return self.data_bucket.allow(tokens)

    def wait_trading(self, tokens: float = 1.0) -> None:
        """Wait for trading tokens to be available."""
        self._recover_backoff()
        if self._is_in_backoff():
            # Wait out the backoff
            sleep_time = self._backoff_until - time.time()
            if sleep_time > 0:
                time.sleep(min(sleep_time, 1.0))  # Cap sleep to 1s for responsiveness
            return
        self.trading_bucket.wait(tokens)

    def wait_data(self, tokens: float = 1.0) -> None:
        """Wait for data tokens to be available."""
        self._recover_backoff()
        if self._is_in_backoff():
            # Wait out the backoff
            sleep_time = self._backoff_until - time.time()
            if sleep_time > 0:
                time.sleep(min(sleep_time, 1.0))
            return
        self.data_bucket.wait(tokens)

    def on_429_error(self):
        """Call this when a 429 error occurs to trigger backoff."""
        self._apply_backoff()

    def get_status(self) -> Dict[str, Any]:
        """Get current status for monitoring."""
        now = time.time()
        return {
            'name': self.name,
            'in_backoff': self._is_in_backoff(),
            'backoff_remaining': max(0.0, self._backoff_until - now),
            'current_backoff': self._current_backoff,
            'backoff_count': self._backoff_count,
            'trading_tokens': self.trading_bucket._tokens,
            'data_tokens': self.data_bucket._tokens,
            'last_429': self._last_429
        }