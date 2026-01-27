from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import unittest
from unittest.mock import MagicMock, patch
import logging
from aureon_queen_hive_mind import QueenHiveMind
from aureon_hft_websocket_order_router import HFTOrderRouter

class TestHFTWiring(unittest.TestCase):
    def setUp(self):
        # Configure logging to capture logs during tests
        logging.basicConfig(level=logging.INFO)
        self.queen = QueenHiveMind()
        self.router = HFTOrderRouter()

    def test_queen_wire_hft_engine_success(self):
        """Test wiring HFT engine to Queen Hive Mind successfully."""
        mock_hft_engine = MagicMock()
        mock_hft_engine.wire_queen = MagicMock()

        # Perform wiring
        result = self.queen.wire_hft_engine(mock_hft_engine)

        # Assertions
        self.assertTrue(result, "Queen should return True on successful wiring")
        self.assertEqual(self.queen.hft_engine, mock_hft_engine, "Queen should hold reference to HFT engine")
        mock_hft_engine.wire_queen.assert_called_once_with(self.queen)
        
        # Verify metric registration (child registration)
        self.assertIn("hft_engine", self.queen.children, "HFT engine should be registered as a child")

    def test_queen_wire_hft_engine_none(self):
        """Test wiring None as HFT engine."""
        result = self.queen.wire_hft_engine(None)
        self.assertFalse(result, "Queen should return False when hft_engine is None")

    def test_router_wire_exchange_clients(self):
        """Test wiring exchange clients to HFT Order Router."""
        mock_clients = {"kraken": MagicMock(), "binance": MagicMock()}

        # Perform wiring
        result = self.router.wire_exchange_clients(mock_clients)

        # Assertions
        self.assertTrue(result, "Router should return True on successful wiring")
        self.assertEqual(self.router.exchange_clients, mock_clients, "Router should hold reference to exchange clients")

    def test_router_wire_exchange_clients_empty(self):
        """Test wiring empty clients dict."""
        result = self.router.wire_exchange_clients({})
        self.assertTrue(result, "Router should handle empty clients dict gracefully")
        self.assertEqual(self.router.exchange_clients, {}, "Router should have empty dict")

if __name__ == "__main__":
    unittest.main()
