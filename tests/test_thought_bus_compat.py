import unittest

from aureon.core.aureon_thought_bus import Thought, ThoughtBus


class TestThoughtBusCompat(unittest.TestCase):
    def test_publish_accepts_topic_and_payload(self):
        bus = ThoughtBus()

        published = bus.publish("decisions.trading", {"symbol": "NATURALGAS", "side": "SELL"}, source="capital")

        self.assertIsInstance(published, Thought)
        self.assertEqual(published.topic, "decisions.trading")
        self.assertEqual(published.source, "capital")
        self.assertEqual(published.payload["symbol"], "NATURALGAS")

    def test_publish_accepts_dict_event(self):
        bus = ThoughtBus()

        published = bus.publish({"topic": "coordination.monitor", "source": "coordinator", "ready": True})

        self.assertEqual(published.topic, "coordination.monitor")
        self.assertEqual(published.source, "coordinator")
        self.assertTrue(published.payload["ready"])

    def test_publish_accepts_foreign_thought_like_object(self):
        class ForeignThought:
            def __init__(self):
                self.source = "whale_sonar"
                self.topic = "whale.sonar.BTCUSD"
                self.payload = {"code": "..."}
                self.meta = {"origin": "foreign"}
                self.trace_id = "trace-1"

        bus = ThoughtBus()

        published = bus.publish(ForeignThought())

        self.assertEqual(published.source, "whale_sonar")
        self.assertEqual(published.topic, "whale.sonar.BTCUSD")
        self.assertEqual(published.payload["code"], "...")
        self.assertEqual(published.meta["origin"], "foreign")


if __name__ == "__main__":
    unittest.main()
