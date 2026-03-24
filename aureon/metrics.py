"""Lightweight Prometheus-friendly metrics wrapper with internal counters for tests.

- Uses prometheus_client when available to register real Prometheus metrics.
- Always maintains an internal in-process count store for easy access in unit tests.
"""
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
from typing import Dict, Tuple, Optional, List, Any
import threading

try:
    from prometheus_client import Counter as _PromCounter, Gauge as _PromGauge
    PROM_AVAILABLE = True
except Exception:
    _PromCounter = None
    _PromGauge = None
    PROM_AVAILABLE = False

_lock = threading.Lock()
_internal_counters: Dict[Tuple[str, Tuple[Tuple[str, str], ...]], float] = {}


class MetricCounter:
    def __init__(self, name: str, description: str = "", labelnames: Optional[Tuple[str, ...]] = None):
        self.name = name
        self.description = description
        self.labelnames = tuple(labelnames) if labelnames else tuple()
        self._prom = None
        if PROM_AVAILABLE and _PromCounter is not None:
            try:
                if self.labelnames:
                    self._prom = _PromCounter(name, description, list(self.labelnames))
                else:
                    self._prom = _PromCounter(name, description)
            except Exception:
                self._prom = None

    def _key(self, labels: Dict[str, str]) -> Tuple[str, Tuple[Tuple[str, str], ...]]:
        items = tuple(sorted((k, str(labels.get(k, ""))) for k in self.labelnames))
        return (self.name, items)

    def inc(self, amount: float = 1.0, **labels: str) -> None:
        key = self._key(labels)
        with _lock:
            _internal_counters[key] = _internal_counters.get(key, 0.0) + float(amount)
        if self._prom is not None:
            try:
                if self.labelnames:
                    self._prom.labels(**labels).inc(amount)
                else:
                    self._prom.inc(amount)
            except Exception:
                pass

    def get(self, **labels) -> float:
        key = self._key(labels)
        return float(_internal_counters.get(key, 0.0))


class MetricGauge:
    def __init__(self, name: str, description: str = "", labelnames: Optional[Tuple[str, ...]] = None):
        self.name = name
        self.description = description
        self.labelnames = tuple(labelnames) if labelnames else tuple()
        self._prom = None
        if PROM_AVAILABLE and _PromGauge is not None:
            try:
                if self.labelnames:
                    self._prom = _PromGauge(name, description, list(self.labelnames))
                else:
                    self._prom = _PromGauge(name, description)
            except Exception:
                self._prom = None

    def _key(self, labels: Dict[str, str]) -> Tuple[str, Tuple[Tuple[str, str], ...]]:
        items = tuple(sorted((k, str(labels.get(k, ""))) for k in self.labelnames))
        return (self.name, items)

    def set(self, value: float, **labels) -> None:
        key = self._key(labels)
        with _lock:
            _internal_counters[key] = float(value)
        if self._prom is not None:
            try:
                if self.labelnames:
                    self._prom.labels(**labels).set(value)
                else:
                    self._prom.set(value)
            except Exception:
                pass

    def get(self, **labels) -> float:
        key = self._key(labels)
        return float(_internal_counters.get(key, 0.0))


# Common metrics
api_429_counter = MetricCounter('api_429_total', 'API 429 responses', labelnames=('exchange', 'endpoint'))
cache_hit_counter = MetricCounter('cache_hits_total', 'Cache hits', labelnames=('cache',))
cache_miss_counter = MetricCounter('cache_misses_total', 'Cache misses', labelnames=('cache',))
rate_limiter_waits = MetricCounter('rate_limiter_waits_total', 'Number of times rate limiter caused waits', labelnames=('exchange',))
rate_limiter_tokens = MetricGauge('rate_limiter_tokens', 'Current available tokens in rate limiter', labelnames=('exchange',))

# Convenience accessors for tests
def get_metric_value(counter: MetricCounter, **labels) -> float:
    return counter.get(**labels)

def get_gauge_value(gauge: MetricGauge, **labels) -> float:
    return gauge.get(**labels)


def dump_metrics() -> List[Dict[str, Any]]:
    """Return a snapshot of all metric values for monitoring dashboards."""
    with _lock:
        items = [
            {
                "name": name,
                "labels": dict(labels),
                "value": value,
            }
            for (name, labels), value in _internal_counters.items()
        ]
    return items

# Timeline anchor metrics
skipped_anchor_counter = MetricCounter(
    'timeline_anchor_skipped_total', 
    'Count of skipped or malformed timeline anchors',
    labelnames=('reason',)
)

# Adaptive rate limiter metrics
rate_limiter_backoff_seconds = MetricGauge(
    'rate_limiter_backoff_seconds',
    'Current backoff duration in seconds',
    labelnames=('limiter',)
)
rate_limiter_429_count = MetricCounter(
    'rate_limiter_429_total',
    'Number of 429 errors triggering backoff',
    labelnames=('limiter',)
)
rate_limiter_recovery_count = MetricCounter(
    'rate_limiter_recovery_total',
    'Number of times rate limiter recovered from backoff',
    labelnames=('limiter',)
)

# MarketDataHub metrics (Phase 2)
market_data_prefetch_cycles = MetricCounter(
    'market_data_prefetch_cycles_total',
    'Number of prefetch cycles performed by MarketDataHub'
)
market_data_cache_hits = MetricCounter(
    'market_data_cache_hits_total',
    'Number of cache hits served by MarketDataHub',
    labelnames=('hub',)
)
market_data_api_calls_saved = MetricCounter(
    'market_data_api_calls_saved_total',
    'Number of API calls saved by serving cached prefetch data',
    labelnames=('hub',)
)

# Global Rate Budget metrics (Phase 2)
global_budget_requests_total = MetricCounter(
    'global_rate_budget_requests_total',
    'Global Rate Budget requests processed, delayed, or rejected',
    labelnames=('priority', 'status')
)

