import unittest

from aureon_trade_activation import (
    UnifiedTradeExecutor,
    ExecutionRequest,
    QueenExecutorBridge,
)


class TestTradeActivationWiring(unittest.TestCase):
    def setUp(self):
        self.executor = UnifiedTradeExecutor(dry_run=True)

    def test_gating_rejects_low_confidence(self):
        req = ExecutionRequest(
            symbol="BTC/USDT",
            side="buy",
            quantity=0.01,
            price=60000,
            confidence=0.2,
            coherence=0.9,
            lambda_val=0.9,
            exchange="binance",
        )
        result = self.executor.execute_trade(req)
        self.assertFalse(result.success)
        self.assertEqual(self.executor.stats["rejected"], 1)

    def test_build_from_opportunity_and_confirm_fill(self):
        bridge = QueenExecutorBridge(self.executor)
        opportunity = {
            "symbol": "ETH/USDT",
            "exchange": "kraken",
            "price": 3000,
            "confidence": 0.81,
            "ocean_score": 0.79,
        }
        result = bridge.process_ocean_opportunity(opportunity)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.order_id)

        ok = self.executor.record_fill_confirmation(
            order_id=result.order_id,
            exchange="kraken",
            filled_qty=result.executed_qty,
            filled_price=result.executed_price,
        )
        self.assertTrue(ok)
        self.assertEqual(self.executor.stats["confirmed_fills"], 1)

    def test_ghost_order_detection(self):
        req = ExecutionRequest(
            symbol="SOL/USDT",
            side="buy",
            quantity=1,
            price=100,
            confidence=0.9,
            coherence=0.9,
            lambda_val=0.9,
            exchange="binance",
        )
        result = self.executor.execute_trade(req)
        self.assertTrue(result.success)
        self.assertEqual(self.executor.sweep_for_ghost_orders(now=10**10), 1)
        self.assertEqual(self.executor.stats["ghost_orders"], 1)


if __name__ == "__main__":
    unittest.main()
