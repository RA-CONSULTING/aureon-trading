import os
import sys
import unittest
from unittest.mock import Mock, patch


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXCHANGES_DIR = os.path.join(REPO_ROOT, "aureon", "exchanges")
if EXCHANGES_DIR not in sys.path:
    sys.path.insert(0, EXCHANGES_DIR)

import alpaca_client as alpaca_mod
import binance_ws_client as binance_ws_mod
import capital_client as capital_mod


class AlpacaClientResilienceTests(unittest.TestCase):
    @patch.dict(os.environ, {
        "ALPACA_API_KEY": "key",
        "ALPACA_SECRET_KEY": "secret",
        "ALPACA_PAPER": "false",
        "ALPACA_DRY_RUN": "false",
    }, clear=False)
    @patch.object(alpaca_mod.requests.Session, "get", side_effect=alpaca_mod.requests.exceptions.ReadTimeout("slow"))
    def test_initial_auth_timeout_keeps_client_enabled(self, _mock_get):
        client = alpaca_mod.AlpacaClient()

        self.assertTrue(client.is_authenticated)
        self.assertEqual(client.init_error, "")
        self.assertIn("slow", client.auth_probe_warning)


class CapitalClientResilienceTests(unittest.TestCase):
    @patch.dict(os.environ, {
        "CAPITAL_API_KEY": "key",
        "CAPITAL_IDENTIFIER": "user",
        "CAPITAL_PASSWORD": "pass",
        "CAPITAL_DEMO": "0",
    }, clear=False)
    @patch.object(capital_mod.requests, "post", side_effect=capital_mod.requests.exceptions.ReadTimeout("slow"))
    def test_initial_session_timeout_does_not_disable_client(self, _mock_post):
        client = capital_mod.CapitalClient()

        self.assertTrue(client.enabled)
        self.assertIn("slow", client.init_error)

    def test_request_without_session_returns_error_response(self):
        client = capital_mod.CapitalClient.__new__(capital_mod.CapitalClient)
        client.enabled = True
        client.base_url = "https://example.com"
        client.init_error = "session_missing"
        client.cst = None
        client.x_security_token = None
        client.session_start_time = 0.0
        client._rate_limit_until = 0.0
        client._rate_limit_logged = False
        client._session_error_logged = False
        client._next_session_retry_at = 0.0
        client._session_is_expired = lambda: True  # type: ignore[method-assign]
        client._create_session = lambda: None  # type: ignore[method-assign]
        client._get_headers = lambda: {}  # type: ignore[method-assign]

        response = client._request("GET", "/markets")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["errorCode"], "session_unavailable")


class BinanceWebSocketClientTests(unittest.TestCase):
    @patch.dict(os.environ, {"BINANCE_WS_DISABLE": "false"}, clear=False)
    @patch.object(binance_ws_mod.websocket, "WebSocketApp")
    @patch.object(binance_ws_mod.threading, "Thread")
    def test_connect_attempts_real_binance_socket_when_not_disabled(self, mock_thread, mock_ws_app):
        thread_instance = Mock()
        mock_thread.return_value = thread_instance
        client = binance_ws_mod.BinanceWebSocketClient()
        client.subscriptions.add("btcusdt@ticker")

        client._connect()

        mock_ws_app.assert_called_once()
        mock_thread.assert_called_once()
        thread_instance.start.assert_called_once()


if __name__ == "__main__":
    unittest.main()
