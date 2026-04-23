from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import time
import unittest
from rate_limiter import TokenBucket, TTLCache

class TestRateLimiterAndCache(unittest.TestCase):
    def test_token_bucket_rate(self):
        tb = TokenBucket(rate=2.0, capacity=2.0)
        # Immediately consume 2 tokens
        self.assertTrue(tb.allow(1.0))
        self.assertTrue(tb.allow(1.0))
        # Third call should not be allowed immediately
        self.assertFalse(tb.allow(1.0))
        # Wait ~0.6s to get ~1.2 tokens and allow another
        time.sleep(0.6)
        self.assertTrue(tb.allow(1.0))

    def test_ttl_cache(self):
        c = TTLCache(default_ttl=0.2)
        c.set('foo', {'x': 1})
        self.assertEqual(c.get('foo'), {'x': 1})
        time.sleep(0.25)
        self.assertIsNone(c.get('foo'))

if __name__ == '__main__':
    unittest.main()
