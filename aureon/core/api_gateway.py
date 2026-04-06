"""
Unified API Gateway — Cross-system request dedup + global rate budget.

Every exchange API call in the system should go through this gateway.
It prevents duplicate calls (3 systems asking for the same ticker within
2 seconds = 1 API call, not 3) and enforces a global rate budget per
exchange so the combined load from all systems never exceeds limits.

Usage:
    from aureon.core.api_gateway import gw

    # Read calls (cached + rate-budgeted):
    ticker = gw.get_ticker("kraken", "XXBTZUSD")
    balance = gw.get_balance("kraken")
    positions = gw.get_positions("kraken")

    # Write calls (NOT cached, but rate-budgeted):
    gw.place_order("kraken", ...)

    # After a trade executes:
    gw.invalidate("kraken", "balance")
    gw.invalidate("kraken", "positions")
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)

import logging
import threading
import time
from typing import Any, Dict, List, Optional

from aureon.core.rate_limiter import TokenBucket, TTLCache

log = logging.getLogger(__name__)

# ── ThoughtBus (optional, for price broadcasting) ────────────────────────────
try:
    from aureon.core.aureon_thought_bus import get_thought_bus, Thought
    _HAS_BUS = True
except Exception:
    get_thought_bus = None  # type: ignore
    Thought = None          # type: ignore
    _HAS_BUS = False


# ═══════════════════════════════════════════════════════════════════════════════
# RATE BUDGETS — one TokenBucket per exchange, shared by ALL systems
# ═══════════════════════════════════════════════════════════════════════════════

_BUDGETS: Dict[str, TokenBucket] = {
    "kraken":  TokenBucket(rate=0.33, capacity=10, name="gw_kraken"),
    "capital": TokenBucket(rate=0.8,  capacity=5,  name="gw_capital"),
    "binance": TokenBucket(rate=5.0,  capacity=20, name="gw_binance"),
    "alpaca":  TokenBucket(rate=2.0,  capacity=10, name="gw_alpaca"),
}

# ═══════════════════════════════════════════════════════════════════════════════
# RESPONSE CACHE — short-TTL dedup across all callers
# ═══════════════════════════════════════════════════════════════════════════════

_CACHE = TTLCache(default_ttl=2.0, name="api_gateway")

# ═══════════════════════════════════════════════════════════════════════════════
# CLIENT SINGLETONS — lazy-loaded, thread-safe
# ═══════════════════════════════════════════════════════════════════════════════

_clients: Dict[str, Any] = {}
_clients_lock = threading.Lock()


def _get_client(exchange: str) -> Any:
    """Get or create the singleton client for an exchange."""
    cached = _clients.get(exchange)
    if cached is not None:
        return cached

    with _clients_lock:
        # Double-check after acquiring lock
        cached = _clients.get(exchange)
        if cached is not None:
            return cached

        client = None
        try:
            if exchange == "kraken":
                from aureon.exchanges.kraken_client import get_kraken_client
                client = get_kraken_client()
            elif exchange == "binance":
                from aureon.exchanges.binance_client import get_binance_client
                client = get_binance_client()
            elif exchange == "capital":
                from aureon.exchanges.capital_client import CapitalClient
                client = CapitalClient()
                # CapitalClient sets self.enabled=False when credentials missing
                if not getattr(client, 'enabled', True):
                    log.debug("[GW] CapitalClient disabled (missing credentials)")
                    return None
            elif exchange == "alpaca":
                from aureon.exchanges.alpaca_client import get_alpaca_client
                client = get_alpaca_client()
        except Exception as exc:
            log.debug(f"[GW] Client init failed for {exchange}: {exc}")
            return None

        if client is not None:
            _clients[exchange] = client
        return client


# ═══════════════════════════════════════════════════════════════════════════════
# STATS
# ═══════════════════════════════════════════════════════════════════════════════

_stats = {
    "hits": 0,
    "misses": 0,
    "waits": 0,
    "calls": 0,
    "errors": 0,
}


# ═══════════════════════════════════════════════════════════════════════════════
# GATEWAY CLASS — all class methods, truly global
# ═══════════════════════════════════════════════════════════════════════════════

class APIGateway:
    """Unified API gateway — dedup + rate budget + price broadcast."""

    # ── Read methods (cached + rate-budgeted) ─────────────────────────────

    @classmethod
    def get_ticker(cls, exchange: str, symbol: str) -> Optional[Dict]:
        """Get ticker — deduped with 2s TTL."""
        key = f"ticker:{exchange}:{symbol}"
        cached = _CACHE.get(key)
        if cached is not None:
            _stats["hits"] += 1
            return cached

        _stats["misses"] += 1
        cls._wait_budget(exchange)

        client = _get_client(exchange)
        if client is None:
            return None
        try:
            _stats["calls"] += 1
            result = client.get_ticker(symbol)
            if result:
                _CACHE.set(key, result, ttl=2.0)
                cls._broadcast_price(exchange, symbol, result)
            return result
        except Exception as exc:
            _stats["errors"] += 1
            log.debug(f"[GW] get_ticker({exchange}, {symbol}) failed: {exc}")
            return None

    @classmethod
    def get_24h_ticker(cls, exchange: str, symbol: str) -> Optional[Dict]:
        """Get 24h ticker — deduped with 10s TTL."""
        key = f"24h:{exchange}:{symbol}"
        cached = _CACHE.get(key)
        if cached is not None:
            _stats["hits"] += 1
            return cached

        _stats["misses"] += 1
        cls._wait_budget(exchange)

        client = _get_client(exchange)
        if client is None:
            return None
        try:
            _stats["calls"] += 1
            result = client.get_24h_ticker(symbol)
            if result:
                _CACHE.set(key, result, ttl=10.0)
            return result
        except Exception as exc:
            _stats["errors"] += 1
            log.debug(f"[GW] get_24h_ticker({exchange}, {symbol}) failed: {exc}")
            return None

    @classmethod
    def get_24h_tickers(cls, exchange: str) -> Optional[list]:
        """Get all 24h tickers — deduped with 30s TTL."""
        key = f"24h_all:{exchange}"
        cached = _CACHE.get(key)
        if cached is not None:
            _stats["hits"] += 1
            return cached

        _stats["misses"] += 1
        cls._wait_budget(exchange)

        client = _get_client(exchange)
        if client is None:
            return None
        try:
            _stats["calls"] += 1
            result = client.get_24h_tickers()
            if result:
                _CACHE.set(key, result, ttl=30.0)
            return result
        except Exception as exc:
            _stats["errors"] += 1
            log.debug(f"[GW] get_24h_tickers({exchange}) failed: {exc}")
            return None

    @classmethod
    def get_balance(cls, exchange: str) -> Optional[Dict]:
        """Get balance — deduped with 5s TTL."""
        key = f"balance:{exchange}"
        cached = _CACHE.get(key)
        if cached is not None:
            _stats["hits"] += 1
            return cached

        _stats["misses"] += 1
        cls._wait_budget(exchange)

        client = _get_client(exchange)
        if client is None:
            return None
        try:
            _stats["calls"] += 1
            if exchange == "capital":
                result = client.get_accounts() if hasattr(client, 'get_accounts') else client.get_balance()
            else:
                result = client.get_balance()
            if result:
                _CACHE.set(key, result, ttl=5.0)
            return result
        except Exception as exc:
            _stats["errors"] += 1
            log.debug(f"[GW] get_balance({exchange}) failed: {exc}")
            return None

    @classmethod
    def get_trade_balance(cls, exchange: str = "kraken", asset: str = "ZUSD") -> Optional[Dict]:
        """Get trade balance (Kraken margin) — deduped with 10s TTL."""
        key = f"trade_balance:{exchange}:{asset}"
        cached = _CACHE.get(key)
        if cached is not None:
            _stats["hits"] += 1
            return cached

        _stats["misses"] += 1
        cls._wait_budget(exchange)

        client = _get_client(exchange)
        if client is None:
            return None
        try:
            _stats["calls"] += 1
            result = client.get_trade_balance(asset)
            if result:
                _CACHE.set(key, result, ttl=10.0)
            return result
        except Exception as exc:
            _stats["errors"] += 1
            log.debug(f"[GW] get_trade_balance({exchange}) failed: {exc}")
            return None

    @classmethod
    def get_positions(cls, exchange: str) -> Optional[Any]:
        """Get open positions — deduped with 3s TTL."""
        key = f"positions:{exchange}"
        cached = _CACHE.get(key)
        if cached is not None:
            _stats["hits"] += 1
            return cached

        _stats["misses"] += 1
        cls._wait_budget(exchange)

        client = _get_client(exchange)
        if client is None:
            return None
        try:
            _stats["calls"] += 1
            if exchange == "kraken":
                result = client.get_open_margin_positions(do_calcs=True)
            elif exchange == "capital":
                result = client.get_positions()
            else:
                result = getattr(client, 'get_positions', lambda: None)()
            if result is not None:
                _CACHE.set(key, result, ttl=3.0)
            return result
        except Exception as exc:
            _stats["errors"] += 1
            log.debug(f"[GW] get_positions({exchange}) failed: {exc}")
            return None

    # ── Write methods (NOT cached, but rate-budgeted) ─────────────────────

    @classmethod
    def place_order(cls, exchange: str, **kwargs) -> Optional[Any]:
        """Place order — NEVER cached, rate-budgeted, auto-invalidates."""
        cls._wait_budget(exchange)
        client = _get_client(exchange)
        if client is None:
            return None
        try:
            _stats["calls"] += 1
            if exchange == "kraken":
                result = client.place_margin_order(**kwargs)
            elif exchange == "capital":
                result = client.place_market_order(**kwargs)
            elif exchange == "binance":
                result = client.place_market_order(**kwargs)
            else:
                result = client.place_order(**kwargs)
            # Auto-invalidate stale data after trade
            cls.invalidate(exchange, "balance")
            cls.invalidate(exchange, "positions")
            cls.invalidate(exchange, "trade_balance")
            return result
        except Exception as exc:
            _stats["errors"] += 1
            log.debug(f"[GW] place_order({exchange}) failed: {exc}")
            return None

    # ── Cache management ──────────────────────────────────────────────────

    @classmethod
    def invalidate(cls, exchange: str, endpoint: str = "") -> None:
        """Invalidate cached data after a trade execution.

        Call with endpoint="" to clear ALL cache for an exchange.
        Call with endpoint="balance" to clear just balance.
        """
        if not endpoint:
            # Clear all keys for this exchange
            with _CACHE._lock:
                stale = [k for k in _CACHE._store if f":{exchange}:" in k or k.endswith(f":{exchange}")]
                for k in stale:
                    _CACHE._store.pop(k, None)
        else:
            key = f"{endpoint}:{exchange}"
            with _CACHE._lock:
                # Remove exact match and any with extra suffix
                stale = [k for k in _CACHE._store if k.startswith(key)]
                for k in stale:
                    _CACHE._store.pop(k, None)

    # ── Internal helpers ──────────────────────────────────────────────────

    @classmethod
    def _wait_budget(cls, exchange: str) -> None:
        """Block until the global rate budget allows a call."""
        budget = _BUDGETS.get(exchange)
        if budget is not None:
            if not budget.allow(1.0):
                _stats["waits"] += 1
                budget.wait(1.0)

    @classmethod
    def _broadcast_price(cls, exchange: str, symbol: str, ticker: Dict) -> None:
        """Publish fetched price to ThoughtBus for Hive Command and others."""
        if not _HAS_BUS or get_thought_bus is None or Thought is None:
            return
        try:
            price = float(
                ticker.get("price", 0)
                or ticker.get("lastPrice", 0)
                or ticker.get("c", [0])[0]  # Kraken ticker format
                or 0
            )
            if price <= 0:
                return
            bus = get_thought_bus()
            if bus is not None:
                bus.publish(Thought(
                    source="api_gateway",
                    topic=f"market.price.{exchange}",
                    payload={"symbol": symbol, "price": price, "exchange": exchange},
                    meta={"mode": "gateway"},
                ))
        except Exception:
            pass

    # ── Status ────────────────────────────────────────────────────────────

    @classmethod
    def stats(cls) -> Dict[str, Any]:
        """Return gateway statistics."""
        total = _stats["hits"] + _stats["misses"]
        return {
            **_stats,
            "hit_rate": (_stats["hits"] / total * 100) if total > 0 else 0,
            "clients_loaded": list(_clients.keys()),
        }

    @classmethod
    def status_lines(cls) -> List[str]:
        """Human-readable status for dashboard/terminal."""
        s = cls.stats()
        return [
            f"API Gateway: {s['calls']} calls, {s['hits']} cache hits ({s['hit_rate']:.0f}%)",
            f"  Waits: {s['waits']} | Errors: {s['errors']} | Clients: {', '.join(s['clients_loaded']) or 'none'}",
        ]


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE-LEVEL SHORTHAND — import gw and use directly
# ═══════════════════════════════════════════════════════════════════════════════

gw = APIGateway
