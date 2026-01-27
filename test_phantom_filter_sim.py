#!/usr/bin/env python3
"""
🧪 PHANTOM FILTER LOGIC TEST 🧪
Verifies that the Cross-Reality Correlation works as expected.
"""
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import time
import logging
from dataclasses import dataclass
from typing import Dict, Any, List, Callable

# Mock infrastructure
class MockThought:
    def __init__(self, topic, payload, source="mock", **kwargs):
        self.topic = topic
        self.payload = payload
        self.source = source
        self.timestamp = time.time()
        for k, v in kwargs.items():
            setattr(self, k, v)

class MockThoughtBus:
    def __init__(self):
        self.subscribers = {}
        self.published = []

    def subscribe(self, topic, handler):
        print(f"✅ Subscribed to {topic}")
        self.subscribers[topic] = handler

    def publish(self, thought):
        self.published.append(thought)
        print(f"📤 Published: {thought.topic} -> {thought.payload}")

# Import the class to test
# We need to hack the import so it doesn't fail if dependencies are missing
import sys
import unittest
from unittest.mock import MagicMock

# Create a dummy aureon_thought_bus module for the import to work if it fails
sys.modules['aureon_thought_bus'] = MagicMock()
sys.modules['aureon_thought_bus'].ThoughtBus = MockThoughtBus
sys.modules['aureon_thought_bus'].Thought = MockThought

# Now import the target
# We read the file content and exec it to avoid import issues with the real environment
import importlib.util

def load_module_from_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

# Load Phantom Filter
pf_mod = load_module_from_file('aureon_phantom_signal_filter', '/workspaces/aureon-trading/aureon_phantom_signal_filter.py')

class TestPhantomFilter(unittest.TestCase):
    def setUp(self):
        # Override the thought bus availability check
        pf_mod.THOUGHT_BUS_AVAILABLE = True
        pf_mod.get_thought_bus = lambda: MockThoughtBus()
        
        self.filter = pf_mod.PhantomSignalFilter()
        self.filter.thought_bus = MockThoughtBus()  # Inject mock
        self.filter.start()

    def test_phantom_signal_detection(self):
        print("\n--- Test 1: Phantom Signal (HNC Only) ---")
        # 1. HNC Surge (No support)
        hnc_thought = MockThought("intelligence.surge.hnc", {"symbol": "BTC/USD", "strength": 0.8})
        
        # We manually trigger validatation since our mock bus doesn't route automatically in this simple test
        self.filter._on_hnc_event(hnc_thought)
        
        # Check output
        published = self.filter.thought_bus.published
        # Should have published intelligence.signal.phantom
        self.assertTrue(any(t.topic == "intelligence.signal.phantom" for t in published))
        print("✅ Correctly identified Phantom Signal (No correlation)")

    def test_verified_signal_detection(self):
        print("\n--- Test 2: Verified Signal (HNC + Whale) ---")
        self.filter.thought_bus.published = [] # Clear
        
        # 1. Whale Activity FIRST
        whale_thought = MockThought("whale.sonar.BTC", {"symbol": "BTC/USD", "whales": 5})
        self.filter._on_whale_event(whale_thought)
        
        # 2. HNC Surge Immediately After
        hnc_thought = MockThought("intelligence.surge.hnc", {"symbol": "BTC/USD", "strength": 0.9})
        self.filter._on_hnc_event(hnc_thought)
        
        # Check output
        published = self.filter.thought_bus.published
        # Should have published intelligence.signal.verified
        # Find the verified thought
        verified = next((t for t in published if t.topic == "intelligence.signal.verified"), None)
        
        if verified:
            print(f"🎉 VERIFIED! Payload: {verified.payload}")
            self.assertEqual(verified.payload['symbol'], "BTC/USD")
            self.assertIn("PHYSICAL", verified.payload['layers'])
        else:
            self.fail("Did not verify signal despite whale support")

    def test_planetary_override(self):
        print("\n--- Test 3: Planetary Override (Global Stargate) ---")
        self.filter.thought_bus.published = [] 
        
        # 1. Stargate Coherence (Global)
        stargate_thought = MockThought("stargate.node.coherence", {"coherence": 0.95, "node": "Giza"})
        self.filter._on_stargate_event(stargate_thought)
        
        # 2. HNC Surge (ETH/USD) - Different symbol, but Planetary is global
        hnc_thought = MockThought("intelligence.surge.hnc", {"symbol": "ETH/USD", "strength": 0.85})
        self.filter._on_hnc_event(hnc_thought)
        
        # Should verify because Stargate validates the *timeline*, not just the symbol
        published = self.filter.thought_bus.published
        verified = next((t for t in published if t.topic == "intelligence.signal.verified"), None)
        
        if verified:
             print(f"🎉 VERIFIED by Stargate! Layers: {verified.payload['layers']}")
        else:
             self.fail("Stargate Coherence should validate all surges")

if __name__ == '__main__':
    unittest.main()
