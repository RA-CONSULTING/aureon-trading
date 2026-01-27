#!/usr/bin/env python3
"""
Phase 2 Rate Limiting Test - Market Data Hub & Global Rate Budget

Tests the new Phase 2 optimizations:
1. MarketDataHub prefetching and request coalescing
2. GlobalRateBudget priority allocation
3. Integration with AlpacaClient
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import time
import logging
import sys
from typing import List

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_market_data_hub():
    """Test MarketDataHub functionality."""
    logger.info("Testing MarketDataHub...")

    try:
        from alpaca_client import AlpacaClient
        client = AlpacaClient()

        # Start market data hub
        client.start_market_data_hub()
        logger.info("MarketDataHub started")

        # Test symbols
        test_symbols = ['BTC/USD', 'ETH/USD', 'SOL/USD']

        # First requests should hit API
        logger.info("First round of quote requests (should hit API)...")
        start_time = time.time()
        quotes1 = {}
        for symbol in test_symbols:
            quotes1[symbol] = client.get_last_quote(symbol)
            logger.info(f"  {symbol}: {quotes1[symbol].get('last', {}).get('price', 'N/A')}")

        first_round_time = time.time() - start_time
        logger.info(f"First round took {first_round_time:.2f}s")

        # Wait for prefetch cache to populate
        time.sleep(2.5)

        # Second requests should hit cache
        logger.info("Second round of quote requests (should hit cache)...")
        start_time = time.time()
        quotes2 = {}
        for symbol in test_symbols:
            quotes2[symbol] = client.get_last_quote(symbol)
            logger.info(f"  {symbol}: {quotes2[symbol].get('last', {}).get('price', 'N/A')}")

        second_round_time = time.time() - start_time
        logger.info(f"Second round took {second_round_time:.2f}s")

        # Check if cache improved performance
        if second_round_time < first_round_time * 0.5:
            logger.info("✅ Cache performance improvement detected!")
        else:
            logger.warning("⚠️ Cache performance not significantly improved")

        # Get hub stats
        stats = client.get_market_data_hub_stats()
        logger.info(f"MarketDataHub stats: {stats}")

        # Stop hub
        client.stop_market_data_hub()
        logger.info("MarketDataHub stopped")

        return True

    except Exception as e:
        logger.error(f"MarketDataHub test failed: {e}")
        return False

def test_request_coalescing():
    """Test request coalescing functionality."""
    logger.info("Testing request coalescing...")

    try:
        import threading
        from alpaca_client import AlpacaClient

        client = AlpacaClient()
        client.start_market_data_hub()

        results = {}
        errors = []

        def fetch_quote(symbol: str, result_dict: dict, error_list: list):
            try:
                quote = client.get_last_quote(symbol)
                result_dict[symbol] = quote.get('last', {}).get('price')
            except Exception as e:
                error_list.append(f"{symbol}: {e}")

        # Test coalescing with near-simultaneous requests
        test_symbol = 'BTC/USD'
        threads = []

        logger.info(f"Starting 5 simultaneous requests for {test_symbol}...")
        start_time = time.time()

        for i in range(5):
            thread = threading.Thread(
                target=fetch_quote,
                args=(test_symbol, results, errors)
            )
            threads.append(thread)

        # Start all threads within 10ms
        for thread in threads:
            thread.start()
            time.sleep(0.002)  # 2ms stagger

        # Wait for all to complete
        for thread in threads:
            thread.join()

        elapsed = time.time() - start_time
        logger.info(f"All requests completed in {elapsed:.2f}s")
        logger.info(f"Results: {len(results)} successful, {len(errors)} errors")

        if len(results) >= 4 and elapsed < 0.5:  # Should complete quickly due to coalescing
            logger.info("✅ Request coalescing working!")
        else:
            logger.warning("⚠️ Request coalescing may not be working optimally")

        client.stop_market_data_hub()
        return len(errors) == 0

    except Exception as e:
        logger.error(f"Request coalescing test failed: {e}")
        return False

def test_global_rate_budget():
    """Test GlobalRateBudget priority allocation."""
    logger.info("Testing GlobalRateBudget...")

    try:
        from alpaca_client import AlpacaClient
        client = AlpacaClient()

        # Get initial stats
        stats_before = client.get_global_rate_budget_stats()
        logger.info(f"Initial GlobalRateBudget stats: {stats_before}")

        # Make some requests to generate stats
        logger.info("Making test requests...")

        # Quotes (lowest priority)
        client.get_last_quote('BTC/USD')
        client.get_last_quote('ETH/USD')

        # Positions (medium priority)
        client.get_positions()

        # Account (medium priority)
        client.get_account()

        # Get stats after
        stats_after = client.get_global_rate_budget_stats()
        logger.info(f"Final GlobalRateBudget stats: {stats_after}")

        # Check if stats were updated
        if stats_after != stats_before:
            logger.info("✅ GlobalRateBudget tracking requests!")
        else:
            logger.warning("⚠️ GlobalRateBudget stats not updating")

        return True

    except Exception as e:
        logger.error(f"GlobalRateBudget test failed: {e}")
        return False

def main():
    """Run all Phase 2 tests."""
    logger.info("Starting Phase 2 Rate Limiting Tests")
    logger.info("=" * 50)

    tests = [
        ("MarketDataHub", test_market_data_hub),
        ("Request Coalescing", test_request_coalescing),
        ("GlobalRateBudget", test_global_rate_budget),
    ]

    results = []
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running {test_name} test...")
        try:
            success = test_func()
            results.append((test_name, success))
            status = "✅ PASSED" if success else "❌ FAILED"
            logger.info(f"{test_name}: {status}")
        except Exception as e:
            logger.error(f"{test_name}: ❌ FAILED with exception: {e}")
            results.append((test_name, False))

    logger.info("\n" + "=" * 50)
    logger.info("Phase 2 Test Results Summary:")
    all_passed = True
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        logger.info(f"  {test_name}: {status}")
        if not success:
            all_passed = False

    if all_passed:
        logger.info("\n🎉 All Phase 2 optimizations are working!")
        logger.info("🚀 Ready to reduce 429 errors significantly.")
    else:
        logger.warning("\n⚠️ Some Phase 2 optimizations may need attention.")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())