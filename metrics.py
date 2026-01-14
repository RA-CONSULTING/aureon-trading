"""Lightweight Prometheus-friendly metrics wrapper with internal counters for tests.

- Uses prometheus_client when available to register real Prometheus metrics.
- Always maintains an internal in-process count store for easy access in unit tests.
"""
from typing import Dict, Tuple, Optional
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
