from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import unittest
import time
import sys
import os
import threading
from unittest.mock import MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestIntegrationFlow(unittest.TestCase):
    
    def test_thought_bus_connectivity(self):
        """Test end-to-end connectivity via ThoughtBus."""
        from aureon_thought_bus import ThoughtBus, Thought
        from aureon_quantum_mirror_scanner import QuantumMirrorScanner
        
        # 1. Initialize Bus
        bus = ThoughtBus()
        received_thoughts = []
        
        def listener(thought):
            received_thoughts.append(thought)
            
        bus.subscribe("mirror.branch.registered", listener)
        
        # 2. Initialize Scanner with Bus
        scanner = QuantumMirrorScanner(thought_bus=bus)
        
        # 3. Action: Register a branch
        scanner.register_branch(symbol="BTC/USD", exchange="kraken", initial_price=50000.0)
        
        # 4. Assert: Bus received it
        # Wait a moment for async processing if any (though ThoughtBus is sync in main thread usually)
        time.sleep(0.1)
        
        self.assertTrue(len(received_thoughts) > 0)
        self.assertEqual(received_thoughts[0].topic, "mirror.branch.registered")
        self.assertEqual(received_thoughts[0].payload['symbol'], "BTC/USD")
        
    def test_timeline_thought_emission(self):
        """Test TimelineAnchorValidator emitting thoughts."""
        from aureon_thought_bus import ThoughtBus
        from aureon_timeline_anchor_validator import TimelineAnchorValidator, TimelineAnchor, AnchorStatus
        
        bus = ThoughtBus()
        received = []
        bus.subscribe("timeline.anchor.*", lambda t: received.append(t))
        
        validator = TimelineAnchorValidator(thought_bus=bus)
        
        # Force emit a thought (simulate anchoring)
        # Use create_anchor to emit specific event
        validator.create_anchor(
             branch_id="branch_test",
             symbol="ETH/USD",
             exchange="binance",
             initial_price=100.0
        )
        
        time.sleep(0.1)
        self.assertTrue(len(received) > 0)
        self.assertTrue(received[0].topic == "timeline.anchor.created")

if __name__ == '__main__':
    unittest.main()
