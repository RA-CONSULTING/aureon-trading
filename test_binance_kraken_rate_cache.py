from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import unittest
from binance_client import BinanceClient
from kraken_client import KrakenClient

class TestClientsRateAndCache(unittest.TestCase):
    def test_binance_has_rate_and_cache(self):
        b = BinanceClient()
        self.assertTrue(hasattr(b, '_rate_limiter'))
        self.assertTrue(hasattr(b, '_request_cache'))
        # Monkeypatch session.request to count calls
        calls = {'count': 0}
        def fake_request(method, url, params=None, data=None, timeout=5, **kwargs):
            calls['count'] += 1
            class R:
                status_code = 200
                def json(self):
                    return {'symbols': []}
            return R()
        b.session.request = fake_request
        # First call should call session.request
        b.exchange_info()
        # Second call should be cached (same symbol None) and not call again within TTL
        b.exchange_info()
        self.assertEqual(calls['count'], 1)

    def test_kraken_has_rate_and_cache(self):
        k = KrakenClient()
        self.assertTrue(hasattr(k, '_rate_limiter'))
        self.assertTrue(hasattr(k, '_request_cache'))
        # Monkeypatch session.get to count calls
        calls = {'count': 0}
        def fake_get(url, timeout=20, **kwargs):
            calls['count'] += 1
            class R:
                status_code = 200
                def raise_for_status(self):
                    return
                def json(self):
                    return {'result': {}}
            return R()
        k.session.get = fake_get
        k._load_asset_pairs(force=True)
        k._load_asset_pairs(force=False)
        self.assertEqual(calls['count'], 1)

if __name__ == '__main__':
    unittest.main()
