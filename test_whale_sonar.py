from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import time
import unittest
from unittest.mock import MagicMock

from aureon_thought_bus import Thought, get_thought_bus
from mycelium_whale_sonar import WhaleSonar


class TestWhaleSonar(unittest.TestCase):
    def test_basic_aggregation_and_thought_publish(self):
        tb = get_thought_bus(persist_path=None)
        # clear memory if any
        tb._memory.clear()

        ws = WhaleSonar(thought_bus=tb, sample_window=2.0, agg_interval=0.5)
        ws.start()

        # send a burst of messages from a simulated whale
        for _ in range(5):
            tb.publish(Thought(source='kraken_client', topic='system.health', payload={'message': 'ok', 'priority': 'high'}))
            time.sleep(0.1)

        # allow aggregator to run
        time.sleep(1.2)

        # check for whale.sonar.kraken_client thought
        thoughts = tb.recall(limit=200)
        sonar_thoughts = [t for t in thoughts if t['topic'].startswith('whale.sonar.kraken_client')]
        self.assertTrue(len(sonar_thoughts) >= 1)
        pack = sonar_thoughts[-1]['payload'].get('pack', {})
        self.assertIn('score', pack)
        self.assertGreaterEqual(pack['score'], 0.0)

        ws.stop()

    def test_enigma_decode_integration(self):
        tb = get_thought_bus(persist_path=None)
        tb._memory.clear()

        ws = WhaleSonar(thought_bus=tb, sample_window=2.0, agg_interval=0.5)
        # inject a fake enigma integration with a decode method
        mock_enigma = MagicMock()
        fake_decoded = MagicMock()
        fake_decoded.grade.name = 'MAGIC'
        fake_decoded.confidence = 0.77
        fake_decoded.message = 'decoded-intel'
        mock_enigma.enigma.decode.return_value = fake_decoded
        ws.enigma_integration = mock_enigma

        ws.start()
        for _ in range(3):
            tb.publish(Thought(source='wave_scanner', topic='market.signal', payload={'message': 'spike'}))
            time.sleep(0.1)

        time.sleep(1.2)
        thoughts = tb.recall(limit=300)
        enigma_thoughts = [t for t in thoughts if t['topic'].startswith('enigma.whale.wave_scanner')]
        self.assertTrue(len(enigma_thoughts) >= 1)
        self.assertIn('grade', enigma_thoughts[-1]['payload'])

        ws.stop()

    def test_get_thought_bus_auto_wires_sonar(self):
        # Ensure that calling get_thought_bus auto-attaches and starts a Sonar
        from aureon_thought_bus import get_thought_bus
        tb = get_thought_bus(persist_path=None)
        self.assertTrue(hasattr(tb, '_sonar'))
        sonar = getattr(tb, '_sonar')
        self.assertIsNotNone(sonar)

        # publish messages and confirm sonar emits whale.sonar.<source>
        for _ in range(6):
            tb.publish(Thought(source='auto_kraken', topic='system.health', payload={'message':'ok', 'priority':'high'}))
        time.sleep(1.2)
        thoughts = tb.recall(limit=500)
        sonar_thoughts = [t for t in thoughts if t['topic'].startswith('whale.sonar.auto_kraken')]
        self.assertTrue(len(sonar_thoughts) >= 1)

        # cleanup
        if hasattr(tb, '_sonar') and getattr(tb, '_sonar'):
            getattr(tb, '_sonar').stop()

    def test_queen_alert_on_loud_whale(self):
        tb = get_thought_bus(persist_path=None)
        tb._memory.clear()

        ws = WhaleSonar(thought_bus=tb, sample_window=1.0, agg_interval=0.2)
        ws.start()
        # publish many messages quickly to make a loud whale
        for _ in range(20):
            tb.publish(Thought(source='kraken_client', topic='system.health', payload={'message': 'ok', 'priority': 'high'}))
        time.sleep(0.6)
        thoughts = tb.recall(limit=500)
        alerts = [t for t in thoughts if t['topic'] == 'queen.alert.whale' and t['payload'].get('whale') == 'kraken_client']
        self.assertTrue(len(alerts) >= 1)
        ws.stop()

    def test_direct_instantiation_wires_sonar(self):
        """Test that instantiating ThoughtBus directly also attaches sonar."""
        from aureon_thought_bus import ThoughtBus
        
        # Create a fresh bus (detached from global singleton)
        tb = ThoughtBus(persist_path=None)
        
        # Should have _sonar attached
        self.assertTrue(hasattr(tb, '_sonar'))
        self.assertIsNotNone(tb._sonar)
        
        # Verify it's identifying as a whale
        self.assertEqual(tb._sonar.thought_bus, tb)
        
        # Cleanup
        if hasattr(tb, '_sonar'):
           tb._sonar.stop()


if __name__ == '__main__':
    unittest.main()
