#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                  ║
║     🧪 HARMONIC SIGNAL CHAIN COMPREHENSIVE TESTS 🧪                                              ║
║     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━             ║
║                                                                                                  ║
║     Tests the full integrated harmonic signal chain:                                            ║
║       Queen → Enigma → Scanner → Ecosystem → Whale (turn) → back up to Queen                    ║
║                                                                                                  ║
║     Validates:                                                                                   ║
║       • Chain wiring and node connectivity                                                      ║
║       • Harmonic encoding/decoding at each hop                                                  ║
║       • ThoughtBus integration                                                                   ║
║       • Adaptive learning accumulation                                                          ║
║       • Coherence scores throughout                                                             ║
║       • Poem construction                                                                       ║
║       • Signal direction turnaround                                                             ║
║                                                                                                  ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════╝
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import unittest
import logging
import time

# Suppress verbose logging during tests
logging.basicConfig(level=logging.WARNING)

# Import chain components
from aureon_harmonic_signal_chain import (
    HarmonicSignalChain,
    ChainSignal,
    SignalDirection,
    QueenNode,
    EnigmaNode,
    ScannerNode,
    EcosystemNode,
    WhaleNode,
    CHAIN_ORDER_DOWN,
)

# Import harmonic alphabet for verification
from aureon_harmonic_alphabet import to_harmonics, from_harmonics


class TestHarmonicSignalChain(unittest.TestCase):
    """Test the integrated harmonic signal chain."""
    
    def setUp(self):
        """Initialize a fresh chain for each test."""
        self.chain = HarmonicSignalChain()
    
    def test_chain_initialization(self):
        """Test that all nodes are properly wired."""
        # Check all nodes exist
        self.assertIsNotNone(self.chain.queen)
        self.assertIsNotNone(self.chain.enigma)
        self.assertIsNotNone(self.chain.scanner)
        self.assertIsNotNone(self.chain.ecosystem)
        self.assertIsNotNone(self.chain.whale)
        
        # Check chain wiring (downstream)
        self.assertEqual(self.chain.queen.downstream, self.chain.enigma)
        self.assertEqual(self.chain.enigma.downstream, self.chain.scanner)
        self.assertEqual(self.chain.scanner.downstream, self.chain.ecosystem)
        self.assertEqual(self.chain.ecosystem.downstream, self.chain.whale)
        self.assertIsNone(self.chain.whale.downstream)
        
        # Check chain wiring (upstream)
        self.assertEqual(self.chain.whale.upstream, self.chain.ecosystem)
        self.assertEqual(self.chain.ecosystem.upstream, self.chain.scanner)
        self.assertEqual(self.chain.scanner.upstream, self.chain.enigma)
        self.assertEqual(self.chain.enigma.upstream, self.chain.queen)
        self.assertIsNone(self.chain.queen.upstream)
    
    def test_poem_chain_complete(self):
        """Test the full poem chain: DEEP WITHIN THE HARMONIC TRUTH."""
        signal = self.chain.send_signal("SING ME A POEM")
        
        # Check final content contains all contributions
        self.assertIn("DEEP", signal.current_content)      # Whale
        self.assertIn("WITHIN", signal.current_content)    # Ecosystem
        self.assertIn("THE", signal.current_content)       # Scanner
        self.assertIn("HARMONIC", signal.current_content)  # Enigma
        self.assertIn("TRUTH", signal.current_content)     # Queen
        
        # Exact expected poem
        self.assertEqual(signal.current_content, "DEEP WITHIN THE HARMONIC TRUTH")
    
    def test_signal_path_tracking(self):
        """Test that signal path is correctly tracked through chain."""
        signal = self.chain.send_signal("TEST PATH")
        
        # Path should include all nodes
        self.assertIn("queen", signal.chain_path)
        self.assertIn("enigma", signal.chain_path)
        self.assertIn("scanner", signal.chain_path)
        self.assertIn("ecosystem", signal.chain_path)
        self.assertIn("whale", signal.chain_path)
        
        # First entry should be queen (initiator)
        self.assertEqual(signal.chain_path[0], "queen")
    
    def test_direction_turnaround(self):
        """Test that signal direction changes at whale."""
        signal = self.chain.send_signal("TEST DIRECTION")
        
        # After completion, signal should be UP direction
        self.assertEqual(signal.direction, SignalDirection.UP)
        
        # Whale should have turnaround flag in contributions
        whale_contribution = signal.node_contributions.get("whale", {})
        self.assertTrue(whale_contribution.get("turnaround", False))
    
    def test_harmonic_encoding_decoding(self):
        """Test that harmonics encode/decode correctly through chain."""
        signal = self.chain.send_signal("HARMONIC TEST")
        
        # Final content should have harmonics
        self.assertTrue(len(signal.harmonics) > 0)
        
        # Round-trip verification
        encoded = [(h["freq"], h["amp"]) for h in signal.harmonics]
        decoded = from_harmonics(encoded)
        self.assertEqual(decoded, signal.current_content)
    
    def test_coherence_accumulation(self):
        """Test that coherence scores are accumulated from each node."""
        signal = self.chain.send_signal("COHERENCE TEST")
        
        # Should have coherence scores
        self.assertTrue(len(signal.coherence_scores) > 0)
        
        # Average coherence should be calculated
        avg_coherence = sum(signal.coherence_scores.values()) / len(signal.coherence_scores)
        self.assertGreater(avg_coherence, 0)
        self.assertLessEqual(avg_coherence, 1.0)
    
    def test_node_contributions(self):
        """Test that each node adds its contribution."""
        signal = self.chain.send_signal("CONTRIBUTION TEST")
        
        # Each node should have contributed
        expected_nodes = ["whale", "ecosystem", "scanner", "enigma", "queen"]
        for node in expected_nodes:
            self.assertIn(node, signal.node_contributions)
            contribution = signal.node_contributions[node]
            self.assertIn("word", contribution)
            self.assertIn("frequency", contribution)
    
    def test_adaptive_learning(self):
        """Test that adaptive learning records transmissions."""
        # Send multiple signals
        for i in range(3):
            self.chain.send_signal(f"LEARNING TEST {i}")
        
        # Check learning stats
        status = self.chain.get_chain_status()
        
        for node_id, stats in status.items():
            self.assertGreater(stats["signals_processed"], 0)
    
    def test_json_command_through_chain(self):
        """Test JSON structured command through chain."""
        signal = self.chain.send_signal('{"CMD": "EXECUTE", "VAL": 100}')
        
        # Signal should complete
        self.assertIsNotNone(signal.current_content)
        self.assertTrue(len(signal.chain_path) > 0)
    
    def test_signal_timing(self):
        """Test that signal timing is tracked."""
        start = time.time()
        signal = self.chain.send_signal("TIMING TEST")
        
        # Created timestamp should be reasonable
        self.assertGreater(signal.created_at, start - 1)
        self.assertLess(signal.created_at, time.time() + 1)
        
        # Last hop should be after created
        self.assertGreaterEqual(signal.last_hop_at, signal.created_at)


class TestIndividualNodes(unittest.TestCase):
    """Test individual node behavior."""
    
    def test_queen_initiates_signal(self):
        """Test Queen can initiate signals."""
        queen = QueenNode()
        signal = queen.initiate_signal("TEST MESSAGE")
        
        self.assertEqual(signal.original_message, "TEST MESSAGE")
        self.assertEqual(signal.direction, SignalDirection.DOWN)
        self.assertEqual(signal.origin_system, "queen")
    
    def test_whale_turnaround(self):
        """Test Whale turns signals around."""
        whale = WhaleNode()
        
        # Create DOWN signal
        signal = ChainSignal(
            original_message="TEST",
            current_content="TEST",
            direction=SignalDirection.DOWN,
        )
        
        # Process at whale
        processed = whale.receive_signal(signal)
        
        # Should be turned around to UP
        self.assertEqual(processed.direction, SignalDirection.UP)
        self.assertEqual(processed.current_content, "DEEP")
    
    def test_enigma_decodes(self):
        """Test Enigma decodes harmonic signals."""
        enigma = EnigmaNode()
        
        # Create signal with harmonics
        signal = ChainSignal(
            original_message="HELLO",
            current_content="HELLO",
            direction=SignalDirection.DOWN,
        )
        signal.encode_to_harmonics()
        
        # Process at enigma
        processed = enigma.receive_signal(signal)
        
        # Content should be preserved
        self.assertIn("HELLO", processed.current_content)


class TestHarmonicAlphabetIntegration(unittest.TestCase):
    """Test harmonic alphabet integration with chain."""
    
    def test_full_alphabet_through_chain(self):
        """Test full alphabet passes through chain."""
        chain = HarmonicSignalChain()
        signal = chain.send_signal("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        
        # Should complete without error
        self.assertIsNotNone(signal.current_content)
    
    def test_numbers_through_chain(self):
        """Test numbers pass through chain."""
        chain = HarmonicSignalChain()
        signal = chain.send_signal("0123456789")
        
        # Should complete without error
        self.assertIsNotNone(signal.current_content)
    
    def test_punctuation_through_chain(self):
        """Test punctuation passes through chain."""
        chain = HarmonicSignalChain()
        signal = chain.send_signal("HELLO! HOW ARE YOU?")
        
        # Should complete without error
        self.assertIsNotNone(signal.current_content)


class TestChainContinuity(unittest.TestCase):
    """Test end-to-end chain continuity."""
    
    def test_multiple_signals_maintain_state(self):
        """Test chain handles multiple signals correctly."""
        chain = HarmonicSignalChain()
        
        # Send multiple different signals
        signals = []
        messages = ["FIRST", "SECOND", "THIRD"]
        
        for msg in messages:
            signal = chain.send_signal(msg)
            signals.append(signal)
        
        # Each should complete with correct poem
        for signal in signals:
            self.assertEqual(signal.current_content, "DEEP WITHIN THE HARMONIC TRUTH")
    
    def test_chain_status_updates(self):
        """Test chain status reflects processing."""
        chain = HarmonicSignalChain()
        
        # Get initial status
        initial_status = chain.get_chain_status()
        
        # Send signal
        chain.send_signal("STATUS TEST")
        
        # Get updated status
        updated_status = chain.get_chain_status()
        
        # Counts should increase
        for node_id in ["queen", "enigma", "scanner", "ecosystem", "whale"]:
            self.assertGreaterEqual(
                updated_status[node_id]["signals_processed"],
                initial_status[node_id]["signals_processed"]
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
