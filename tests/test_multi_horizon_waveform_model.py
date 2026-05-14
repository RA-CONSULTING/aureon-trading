import json
import tempfile
import time
import unittest
from pathlib import Path

from aureon.analytics.aureon_multi_horizon_waveform_model import build_multi_horizon_waveform_report
from aureon.core.aureon_global_history_db import connect, insert_market_bar


class MultiHorizonWaveformModelTests(unittest.TestCase):
    def test_builds_1h_to_1y_waveform_models_from_history_and_live_points(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "history.sqlite"
            now_ms = 1_800_000_000_000
            conn = connect(str(db_path))
            try:
                for day in range(370, -1, -30):
                    ts_ms = now_ms - day * 24 * 60 * 60 * 1000
                    close = 100.0 + (370 - day) * 0.08
                    insert_market_bar(
                        conn,
                        {
                            "provider": "unit",
                            "venue": "TEST",
                            "symbol_id": "BTCUSD",
                            "symbol": "BTCUSD",
                            "period_id": "1DAY",
                            "time_start_ms": ts_ms,
                            "time_end_ms": ts_ms + 24 * 60 * 60 * 1000,
                            "open": close - 0.5,
                            "high": close + 1.0,
                            "low": close - 1.0,
                            "close": close,
                            "volume": 1000.0,
                            "raw_json": json.dumps({"close": close}),
                        },
                    )
                for minute in range(60, -1, -10):
                    ts_ms = now_ms - minute * 60 * 1000
                    close = 130.0 + (60 - minute) * 0.02
                    insert_market_bar(
                        conn,
                        {
                            "provider": "unit",
                            "venue": "TEST",
                            "symbol_id": "BTCUSD",
                            "symbol": "BTCUSD",
                            "period_id": "10MIN",
                            "time_start_ms": ts_ms,
                            "time_end_ms": ts_ms + 10 * 60 * 1000,
                            "open": close - 0.1,
                            "high": close + 0.2,
                            "low": close - 0.2,
                            "close": close,
                            "volume": 2000.0,
                            "raw_json": json.dumps({"close": close}),
                        },
                    )
                conn.commit()
            finally:
                conn.close()

            report = build_multi_horizon_waveform_report(
                symbols=["BTCUSD"],
                live_observations=[{"symbol": "BTCUSD", "ts_ms": now_ms, "close": 131.5, "source": "live"}],
                db_path=db_path,
                now_ms=now_ms,
            )

        model = report["symbol_models"]["BTCUSD"]
        self.assertEqual(report["horizon_labels"][0], "1h")
        self.assertEqual(report["horizon_labels"][-1], "1y")
        self.assertTrue(model["horizons"]["1h"]["usable"])
        self.assertTrue(model["horizons"]["1y"]["usable"])
        self.assertTrue(model["long_memory_ready"])
        self.assertGreater(report["decision_symbol_count"], 0)
        self.assertEqual(report["decision_symbols"]["BTCUSD"]["reason"], "multi_horizon_historical_waveform")

    def test_missing_history_is_explicit_not_fabricated(self):
        now_ms = int(time.time() * 1000)
        report = build_multi_horizon_waveform_report(
            symbols=["ETHUSD"],
            live_observations=[{"symbol": "ETHUSD", "ts_ms": now_ms, "close": 2500.0, "source": "live"}],
            db_path=str(Path(tempfile.gettempdir()) / "missing-aureon-waveform.sqlite"),
            now_ms=now_ms,
        )

        model = report["symbol_models"]["ETHUSD"]
        self.assertFalse(model["horizons"]["1y"]["usable"])
        self.assertIn("1y", model["blockers"])
        self.assertEqual(report["decision_symbol_count"], 0)


if __name__ == "__main__":
    unittest.main()
