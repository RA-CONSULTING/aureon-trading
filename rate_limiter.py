"""Simple per-exchange rate limiter and TTL cache utilities.

Provides:
- TokenBucket: simple token-bucket rate limiter with blocking wait().
- TTLCache: tiny TTL-based cache for short-lived market data.

These are intentionally dependency-free and simple for easy testing.
"""
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import time
import threading
from typing import Any, Dict, Optional


class TokenBucket:
    """A simple token-bucket rate limiter.

    rate: tokens per second
    capacity: maximum burst size
    """

    def __init__(self, rate: float = 5.0, capacity: Optional[float] = None, name: Optional[str] = None):
        self.rate = float(rate)
        self.capacity = float(capacity) if capacity is not None else float(max(1.0, rate))
        self._tokens = self.capacity
        self._last = time.monotonic()
        self._lock = threading.Lock()
        self.name = name or 'unknown'
        # metrics
        try:
            from metrics import rate_limiter_tokens, rate_limiter_waits
            # set initial tokens metric
            rate_limiter_tokens.set(self._tokens, exchange=self.name)
        except Exception:
            pass

    def _add_tokens(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last
        if elapsed <= 0:
            return
        self._last = now
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)

    def allow(self, tokens: float = 1.0) -> bool:
        with self._lock:
            self._add_tokens()
            if self._tokens >= tokens:
                self._tokens -= tokens
                # update tokens gauge
                try:
                    from metrics import rate_limiter_tokens
                    rate_limiter_tokens.set(self._tokens, exchange=self.name)
                except Exception:
                    pass
                return True
            return False

    def wait(self, tokens: float = 1.0) -> None:
        """Block until tokens are available."""
        waited = False
        start_wait = None
        while True:
            with self._lock:
                self._add_tokens()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    # update tokens gauge
                    try:
                        from metrics import rate_limiter_tokens, rate_limiter_waits
                        rate_limiter_tokens.set(self._tokens, exchange=self.name)
                        if waited and start_wait is not None:
                            rate_limiter_waits.inc(1, exchange=self.name)
                    except Exception:
                        pass
                    return
                # compute small sleep based on deficit
                deficit = tokens - self._tokens
                wait_for = deficit / self.rate if self.rate > 0 else 0.1
                if not waited:
                    waited = True
                    start_wait = time.time()
            # sleep a small amount (cap to avoid long sleeps)
            time.sleep(max(0.01, min(wait_for, 0.5)))


class TTLCache:
    """Very small TTL cache for short-lived market data.

    Stores (value, expires_at) and returns cached value if not expired.
    """

    def __init__(self, default_ttl: float = 0.5, name: Optional[str] = None):
        self.default_ttl = float(default_ttl)
        self._store: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self.name = name or 'cache'

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            item = self._store.get(key)
            if not item:
                try:
                    from metrics import cache_miss_counter
                    cache_miss_counter.inc(1, cache=self.name)
                except Exception:
                    pass
                return None
            value, expires = item
            if time.time() > expires:
                del self._store[key]
                try:
                    from metrics import cache_miss_counter
                    cache_miss_counter.inc(1, cache=self.name)
                except Exception:
                    pass
                return None
            try:
                from metrics import cache_hit_counter
                cache_hit_counter.inc(1, cache=self.name)
            except Exception:
                pass
            return value

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        ttl = self.default_ttl if ttl is None else float(ttl)
        expires = time.time() + ttl
        with self._lock:
            self._store[key] = (value, expires)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
