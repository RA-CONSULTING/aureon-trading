"""
🚀 PRODUCTION API RATE LIMITER & DATA SOURCE MANAGER

Manages API rate limits across all sources (open source + trader data).
Implements circuit breakers, request batching, and intelligent fallback.
"""

import time
import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import deque
import os

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# PRODUCTION API RATE LIMITS (Per-Minute)
# ═══════════════════════════════════════════════════════════════════════════════
API_RATE_LIMITS = {
    # FREE OPEN SOURCE APIs (NO KEY REQUIRED)
    'coingecko': {
        'calls_per_minute': 10,
        'priority': 'high',
        'fallback': 'cache',
        'timeout': 5.0,
        'batch_size': 250,  # CoinGecko supports up to 250 IDs per request
    },
    'binance_public': {
        'calls_per_minute': 1200,  # 20 calls/sec (20 req/100ms)
        'priority': 'high',
        'fallback': 'coingecko',
        'timeout': 3.0,
        'batch_size': 100,
    },
    'kraken_public': {
        'calls_per_minute': 15,  # Conservative; actual is 15/sec but we batch
        'priority': 'high',
        'fallback': 'coingecko',
        'timeout': 3.0,
        'batch_size': 50,
    },
    
    # PREMIUM/PAID APIs (REQUIRE API KEYS)
    'kraken': {
        'calls_per_minute': 15,  # Tier 2: 15 calls/sec
        'priority': 'critical',
        'fallback': 'kraken_public',
        'timeout': 2.0,
        'batch_size': 20,
    },
    'binance': {
        'calls_per_minute': 1200,  # 20 calls/sec
        'priority': 'critical',
        'fallback': 'binance_public',
        'timeout': 2.0,
        'batch_size': 50,
    },
    'alpaca': {
        'calls_per_minute': 200,  # 3-4 calls/sec
        'priority': 'critical',
        'fallback': 'cache',
        'timeout': 2.0,
        'batch_size': 100,
    },
    'capital_com': {
        'calls_per_minute': 60,  # 1 call/sec
        'priority': 'medium',
        'fallback': 'coingecko',
        'timeout': 3.0,
        'batch_size': 50,
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# DATA SOURCE HIERARCHY (Priority Order)
# ═══════════════════════════════════════════════════════════════════════════════
DATA_SOURCE_PRIORITY = {
    'crypto_prices': ['kraken', 'binance', 'coingecko', 'kraken_public', 'binance_public'],
    'stock_prices': ['capital_com', 'alpaca', 'coingecko'],
    'exchange_balances': ['kraken', 'binance', 'alpaca'],
    'order_book': ['kraken', 'binance', 'kraken_public', 'binance_public'],
}

@dataclass
class RateLimitState:
    """Track rate limit state for an API."""
    name: str
    is_limited: bool = False
    limited_until: float = 0.0  # unix timestamp when limit expires
    total_requests: int = 0
    failed_requests: int = 0
    last_error: Optional[str] = None
    requests_made: deque = field(default_factory=deque)
    
    def __post_init__(self):
        if not self.requests_made:
            self.requests_made = deque(maxlen=API_RATE_LIMITS[self.name]['calls_per_minute'])
    
    def can_request(self) -> bool:
        """Check if we can make another request without hitting rate limit."""
        if self.is_limited and time.time() < self.limited_until:
            return False
        
        # Check if we've exceeded rate limit in last minute
        now = time.time()
        cutoff = now - 60
        
        # Remove timestamps older than 1 minute
        while self.requests_made and self.requests_made[0] < cutoff:
            self.requests_made.popleft()
        
        limit = API_RATE_LIMITS[self.name]['calls_per_minute']
        return len(self.requests_made) < limit
    
    def record_request(self):
        """Record a successful request."""
        self.requests_made.append(time.time())
        self.total_requests += 1
        self.is_limited = False
    
    def mark_limited(self, retry_after: int = 60):
        """Mark API as rate limited."""
        self.is_limited = True
        self.limited_until = time.time() + retry_after
        logger.warning(f"⚠️ API {self.name} rate limited until {self.limited_until}")
    
    def mark_failed(self, error: str):
        """Record a failed request."""
        self.failed_requests += 1
        self.last_error = error
        logger.warning(f"❌ API {self.name} failed: {error}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current API status."""
        now = time.time()
        cutoff = now - 60
        recent_requests = sum(1 for t in self.requests_made if t > cutoff)
        limit = API_RATE_LIMITS[self.name]['calls_per_minute']
        
        return {
            'name': self.name,
            'is_limited': self.is_limited,
            'recent_requests': recent_requests,
            'limit': limit,
            'utilization': (recent_requests / limit * 100),
            'total_requests': self.total_requests,
            'failed_requests': self.failed_requests,
            'last_error': self.last_error,
        }


class ProductionRateLimiter:
    """Production-grade API rate limiter for all data sources."""
    
    def __init__(self):
        self.apis: Dict[str, RateLimitState] = {
            name: RateLimitState(name)
            for name in API_RATE_LIMITS.keys()
        }
        self.circuit_breakers: Dict[str, float] = {}  # API -> time when open
        logger.info("✅ Production Rate Limiter initialized")
    
    async def wait_if_needed(self, api_name: str):
        """Async wait until we can make a request to this API."""
        if api_name not in self.apis:
            logger.warning(f"⚠️ Unknown API: {api_name}")
            return
        
        api_state = self.apis[api_name]
        limit_config = API_RATE_LIMITS[api_name]
        
        # Check circuit breaker
        if api_name in self.circuit_breakers:
            if time.time() < self.circuit_breakers[api_name]:
                logger.warning(f"🔌 Circuit breaker OPEN for {api_name}")
                await asyncio.sleep(0.1)
                return
            else:
                del self.circuit_breakers[api_name]
        
        # Wait if rate limited
        if api_state.is_limited and time.time() < api_state.limited_until:
            wait_time = api_state.limited_until - time.time()
            logger.info(f"⏳ Rate limited: {api_name} - waiting {wait_time:.1f}s")
            await asyncio.sleep(wait_time + 0.1)
            api_state.is_limited = False
        
        # Wait until we have capacity
        while not api_state.can_request():
            # Calculate minimum wait time
            now = time.time()
            cutoff = now - 60
            wait_ms = (60 - (now - api_state.requests_made[0])) * 1000
            
            if wait_ms > 0:
                sleep_time = min(0.1, wait_ms / 1000)
                await asyncio.sleep(sleep_time)
        
        api_state.record_request()
    
    def check_status(self) -> Dict[str, Any]:
        """Get status of all APIs."""
        return {
            api_name: api_state.get_status()
            for api_name, api_state in self.apis.items()
        }
    
    def open_circuit_breaker(self, api_name: str, duration: int = 300):
        """Open circuit breaker for an API (stop using it for N seconds)."""
        self.circuit_breakers[api_name] = time.time() + duration
        logger.error(f"🔌 CIRCUIT BREAKER OPEN: {api_name} for {duration}s")
    
    def get_best_source(self, data_type: str) -> Optional[str]:
        """Get best available data source for the given data type."""
        if data_type not in DATA_SOURCE_PRIORITY:
            return None
        
        for api_name in DATA_SOURCE_PRIORITY[data_type]:
            if api_name not in self.apis:
                continue
            
            api_state = self.apis[api_name]
            if not api_state.is_limited and api_name not in self.circuit_breakers:
                return api_name
        
        return None


# Global rate limiter instance
_global_rate_limiter: Optional[ProductionRateLimiter] = None

def get_rate_limiter() -> ProductionRateLimiter:
    """Get global rate limiter instance."""
    global _global_rate_limiter
    if _global_rate_limiter is None:
        _global_rate_limiter = ProductionRateLimiter()
    return _global_rate_limiter


async def rate_limited_call(
    api_name: str,
    coro,
    fallback_api: Optional[str] = None,
    retry_count: int = 3
) -> Optional[Any]:
    """
    Make a rate-limited API call with automatic fallback and retry.
    
    Args:
        api_name: Name of the API to call
        coro: Coroutine to execute
        fallback_api: Name of fallback API if this one fails
        retry_count: Number of retries before giving up
    
    Returns:
        Result from the API call, or None if all attempts failed
    """
    limiter = get_rate_limiter()
    api_state = limiter.apis.get(api_name)
    
    if not api_state:
        logger.warning(f"⚠️ Unknown API: {api_name}")
        return None
    
    # Try the primary API
    for attempt in range(retry_count):
        try:
            await limiter.wait_if_needed(api_name)
            result = await coro
            logger.debug(f"✅ {api_name} request succeeded (attempt {attempt + 1})")
            return result
        except asyncio.TimeoutError:
            api_state.mark_failed("timeout")
            logger.warning(f"⚠️ {api_name} timeout (attempt {attempt + 1}/{retry_count})")
        except Exception as e:
            api_state.mark_failed(str(e))
            logger.warning(f"⚠️ {api_name} error: {e} (attempt {attempt + 1}/{retry_count})")
        
        if attempt < retry_count - 1:
            await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff
    
    # Try fallback API if primary failed
    if fallback_api and fallback_api != api_name:
        logger.info(f"🔄 Falling back from {api_name} to {fallback_api}")
        return None  # Caller should retry with fallback
    
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# BATCH REQUEST OPTIMIZER
# ═══════════════════════════════════════════════════════════════════════════════
class BatchRequestOptimizer:
    """Optimize API requests by batching symbols to reduce total calls."""
    
    @staticmethod
    def batch_symbols(symbols: List[str], api_name: str) -> List[List[str]]:
        """
        Split symbols into optimal batch sizes for the given API.
        
        CoinGecko: up to 250 IDs per request
        Binance: up to 100 symbols per request
        Kraken: up to 50 pairs per request
        """
        batch_size = API_RATE_LIMITS.get(api_name, {}).get('batch_size', 50)
        batches = [symbols[i:i + batch_size] for i in range(0, len(symbols), batch_size)]
        return batches
    
    @staticmethod
    def estimate_api_calls(symbol_count: int, api_name: str) -> int:
        """Estimate number of API calls needed for N symbols."""
        batch_size = API_RATE_LIMITS.get(api_name, {}).get('batch_size', 50)
        return (symbol_count + batch_size - 1) // batch_size


# ═══════════════════════════════════════════════════════════════════════════════
# LOGGING & MONITORING
# ═══════════════════════════════════════════════════════════════════════════════
def print_api_status():
    """Print current API status for monitoring."""
    limiter = get_rate_limiter()
    status = limiter.check_status()
    
    print("\n" + "=" * 100)
    print("📊 PRODUCTION API RATE LIMIT STATUS")
    print("=" * 100)
    
    # Group by priority
    critical = {}
    high = {}
    medium = {}
    
    for api_name, config in API_RATE_LIMITS.items():
        if config['priority'] == 'critical':
            critical[api_name] = status[api_name]
        elif config['priority'] == 'high':
            high[api_name] = status[api_name]
        else:
            medium[api_name] = status[api_name]
    
    for group_name, apis in [('🔴 CRITICAL', critical), ('🟡 HIGH', high), ('🟢 MEDIUM', medium)]:
        if not apis:
            continue
        print(f"\n{group_name} PRIORITY:")
        for api_name, api_status in apis.items():
            limited_marker = "🔴 LIMITED" if api_status['is_limited'] else "✅"
            print(f"  {limited_marker} {api_name:15} | {api_status['recent_requests']:2}/{api_status['limit']:4} req/min | {api_status['utilization']:5.1f}% | Fails: {api_status['failed_requests']}")
    
    print("\n" + "=" * 100 + "\n")


if __name__ == '__main__':
    # Test the rate limiter
    logging.basicConfig(level=logging.INFO)
    limiter = get_rate_limiter()
    print_api_status()
    
    # Show batch estimates
    print("\n📦 BATCH REQUEST ESTIMATES:")
    for api_name in API_RATE_LIMITS.keys():
        for symbol_count in [100, 500, 1000, 5000]:
            batch_size = API_RATE_LIMITS[api_name]['batch_size']
            calls = BatchRequestOptimizer.estimate_api_calls(symbol_count, api_name)
            print(f"  {api_name:15} + {symbol_count:5} symbols = {calls:3} API calls (batch size: {batch_size})")
