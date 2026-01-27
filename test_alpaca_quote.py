from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import unittest
from alpaca_client import AlpacaClient

class TestAlpacaQuoteFallback(unittest.TestCase):
    def test_crypto_fallback_when_stock_empty(self):
        c = AlpacaClient()
        # Monkeypatch _request to simulate stock endpoint returning empty and crypto endpoint returning quotes
        def fake_request(method, endpoint, params=None, json=None, base_url=None):
            if endpoint.startswith('/v2/stocks/'):
                return {}  # simulate 404/no-data
            if endpoint.startswith('/v1beta3/crypto'):
                # mimic the crypto quotes payload
                return {'BTC/USD': {'bp': 97000.0, 'ap': 97100.0, 't': '2026-01-01T00:00:00Z'}}
            return {}
        c._request = fake_request
        res = c.get_last_quote('BTCUSD')
        self.assertIn('last', res)
        self.assertAlmostEqual(res['last']['price'], 97050.0)

    def test_stock_quote_uses_stock_endpoint(self):
        c = AlpacaClient()
        def fake_request(method, endpoint, params=None, json=None, base_url=None):
            if endpoint.startswith('/v2/stocks/'):
                return {'quote': {'bp': 100.0, 'ap': 102.0}}
            return {}
        c._request = fake_request
        res = c.get_last_quote('AAPL')
        self.assertIn('last', res)
        self.assertAlmostEqual(res['last']['price'], 101.0)

if __name__ == '__main__':
    unittest.main()
