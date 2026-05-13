import json
import os
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
EXCHANGES_DIR = REPO_ROOT / "aureon" / "exchanges"
if str(EXCHANGES_DIR) not in sys.path:
    sys.path.insert(0, str(EXCHANGES_DIR))

import unified_market_status_server as status_server


class UnifiedMarketStatusServerFlightTestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state_root = Path(self.tmp.name)
        self.old_status_path = status_server.STATUS_PATH
        self.old_intent_path = status_server.MARKET_INTENT_PATH
        status_server.STATUS_PATH = self.state_root / "unified_runtime_status.json"
        status_server.MARKET_INTENT_PATH = self.state_root / "aureon_market_reboot_intent.json"
        self.old_env = {
            key: os.environ.get(key)
            for key in (
                "AUREON_MARKET_DOWNTIME_DAYS",
                "AUREON_MARKET_DOWNTIME_START_LOCAL",
                "AUREON_MARKET_DOWNTIME_END_LOCAL",
            )
        }
        os.environ["AUREON_MARKET_DOWNTIME_DAYS"] = "*"
        os.environ["AUREON_MARKET_DOWNTIME_START_LOCAL"] = "00:00"
        os.environ["AUREON_MARKET_DOWNTIME_END_LOCAL"] = "23:59"

    def tearDown(self):
        status_server.STATUS_PATH = self.old_status_path
        status_server.MARKET_INTENT_PATH = self.old_intent_path
        for key, value in self.old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self.tmp.cleanup()

    def _write_status(self, open_positions: int, stale: bool = False):
        payload = {
            "ok": not stale,
            "trading_ready": True,
            "data_ready": True,
            "stale": stale,
            "combined": {"open_positions": open_positions},
            "exchanges": {"kraken_ready": True, "capital_ready": True},
        }
        status_server.STATUS_PATH.write_text(json.dumps(payload), encoding="utf-8")

    def _write_pending_intent(self):
        payload = {"status": "pending", "surface": "market", "reason": "test"}
        status_server.MARKET_INTENT_PATH.write_text(json.dumps(payload), encoding="utf-8")

    def test_flight_test_holds_restart_when_open_positions_exist(self):
        self._write_status(open_positions=2)
        self._write_pending_intent()

        flight = status_server._flight_test()

        self.assertTrue(flight["checks"]["pending_restart"])
        self.assertTrue(flight["checks"]["open_positions"])
        self.assertFalse(flight["reboot_advice"]["can_reboot_now"])
        self.assertEqual(flight["reboot_advice"]["reason"], "open_positions_reported")

    def test_flight_test_reports_stale_tick_with_open_positions_as_position_monitor_hold(self):
        self._write_status(open_positions=2, stale=True)

        flight = status_server._flight_test()

        self.assertFalse(flight["checks"]["tick_fresh"])
        self.assertTrue(flight["checks"]["heartbeat_fresh_but_tick_stale"])
        self.assertFalse(flight["reboot_advice"]["can_reboot_now"])
        self.assertEqual(flight["reboot_advice"]["decision"], "hold_monitor_positions")
        self.assertEqual(flight["reboot_advice"]["reason"], "runtime_tick_stale_with_open_positions")
        self.assertEqual(
            flight["reboot_advice"]["recovery_action"],
            "preserve_position_monitoring_and_defer_restart_until_flat_downtime",
        )

    def test_flight_test_allows_pending_restart_when_flat_in_window(self):
        self._write_status(open_positions=0)
        self._write_pending_intent()

        flight = status_server._flight_test()

        self.assertTrue(flight["checks"]["downtime_window"])
        self.assertFalse(flight["checks"]["open_positions"])
        self.assertTrue(flight["reboot_advice"]["can_reboot_now"])


if __name__ == "__main__":
    unittest.main()
