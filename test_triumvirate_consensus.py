#!/usr/bin/env python3
"""
AUREON TRIUMVIRATE - Comprehensive Integration Test Suite
=====================================================
Tests all 3 systems (Queen, King, Seer) interacting together.

Tests cover:
  1. Freeway consensus - all 3 must pass independently
  2. Queen's absolute veto power (11+ systems = supreme authority)
  3. King and Seer analytical data flowing freely
  4. Control handoff between systems
  5. Edge cases and boundary conditions
  6. Override and escalation scenarios

Gary Leckey | February 2026
"""

import unittest
import time
import sys
import os

# Ensure we can import from the project
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aureon_triumvirate import (
    TriumvirateEngine, QueenEvaluator, KingEvaluator, SeerEvaluator,
    ControlHandoffEngine, PillarRole, ConsensusAction, VoteResult,
    PillarVote, TriumvirateConsensus, ControlHandoff,
    QUEEN_CONNECTED_SYSTEMS, QUEEN_PASS_THRESHOLD, QUEEN_VETO_THRESHOLD,
    KING_PASS_GRADES, SEER_PASS_GRADES,
    get_triumvirate,
)


# ═══════════════════════════════════════════════════════════════════════════
# TEST 1: FREEWAY CONSENSUS - All 3 Must Pass
# ═══════════════════════════════════════════════════════════════════════════

class TestFreewayConsensus(unittest.TestCase):
    """
    Tests the core freeway consensus rule: ALL 3 pillars must
    independently vote PASS for any action to proceed.
    """

    def setUp(self):
        self.engine = TriumvirateEngine()

    def test_all_three_pass_consensus_achieved(self):
        """When Queen, King, and Seer all pass, consensus is achieved."""
        result = self.engine.evaluate_consensus(
            queen_confidence=0.75,
            king_health="PROSPEROUS",
            seer_grade="CLEAR_SIGHT",
            seer_score=0.77,
        )
        self.assertTrue(result.passed)
        self.assertFalse(result.queen_vetoed)
        self.assertEqual(result.queen_vote.vote, VoteResult.PASS.value)
        self.assertEqual(result.king_vote.vote, VoteResult.PASS.value)
        self.assertEqual(result.seer_vote.vote, VoteResult.PASS.value)
        self.assertIn(result.action, [
            ConsensusAction.STRONG_BUY.value,
            ConsensusAction.BUY.value,
            ConsensusAction.HOLD.value,
        ])

    def test_queen_blocks_consensus_fails(self):
        """When Queen blocks, consensus fails even if King+Seer pass."""
        result = self.engine.evaluate_consensus(
            queen_confidence=0.35,  # Below QUEEN_PASS_THRESHOLD (0.45)
            king_health="PROSPEROUS",
            seer_grade="DIVINE_CLARITY",
            seer_score=0.92,
        )
        self.assertFalse(result.passed)
        self.assertEqual(result.queen_vote.vote, VoteResult.BLOCK.value)
        self.assertEqual(result.king_vote.vote, VoteResult.PASS.value)
        self.assertEqual(result.seer_vote.vote, VoteResult.PASS.value)

    def test_king_blocks_consensus_fails(self):
        """When King blocks, consensus fails even if Queen+Seer pass."""
        result = self.engine.evaluate_consensus(
            queen_confidence=0.80,
            king_health="BANKRUPT",
            seer_grade="DIVINE_CLARITY",
            seer_score=0.92,
        )
        self.assertFalse(result.passed)
        self.assertEqual(result.queen_vote.vote, VoteResult.PASS.value)
        self.assertEqual(result.king_vote.vote, VoteResult.BLOCK.value)
        self.assertEqual(result.action, ConsensusAction.HALT.value)

    def test_seer_blocks_consensus_fails(self):
        """When Seer blocks, consensus fails even if Queen+King pass."""
        result = self.engine.evaluate_consensus(
            queen_confidence=0.80,
            king_health="PROSPEROUS",
            seer_grade="BLIND",
            seer_score=0.15,
        )
        self.assertFalse(result.passed)
        self.assertEqual(result.queen_vote.vote, VoteResult.PASS.value)
        self.assertEqual(result.king_vote.vote, VoteResult.PASS.value)
        self.assertEqual(result.seer_vote.vote, VoteResult.BLOCK.value)

    def test_all_three_block_consensus_fails(self):
        """When all three block, consensus definitely fails."""
        result = self.engine.evaluate_consensus(
            queen_confidence=0.20,  # Below veto threshold
            king_health="BANKRUPT",
            seer_grade="BLIND",
            seer_score=0.10,
        )
        self.assertFalse(result.passed)
        self.assertTrue(result.queen_vetoed)
        self.assertEqual(result.action, ConsensusAction.HALT.value)

    def test_two_of_three_pass_still_blocked(self):
        """Even when 2 of 3 pass, the single blocker prevents consensus."""
        # Queen + Seer pass, King blocks
        result = self.engine.evaluate_consensus(
            queen_confidence=0.70,
            king_health="STRAINED",
            seer_grade="CLEAR_SIGHT",
            seer_score=0.75,
        )
        self.assertFalse(result.passed)
        self.assertEqual(result.king_vote.vote, VoteResult.BLOCK.value)
        # Should recommend SELL due to STRAINED king
        self.assertEqual(result.action, ConsensusAction.SELL.value)


# ═══════════════════════════════════════════════════════════════════════════
# TEST 2: QUEEN'S ABSOLUTE VETO POWER
# ═══════════════════════════════════════════════════════════════════════════

class TestQueenVetoPower(unittest.TestCase):
    """
    The Queen has ABSOLUTE VETO because she has the most systems
    connected to her (11+ subsystems). When she vetoes, everything stops.
    """

    def setUp(self):
        self.engine = TriumvirateEngine()

    def test_queen_veto_overrides_all(self):
        """Queen's veto overrides even perfect King+Seer scores."""
        result = self.engine.evaluate_consensus(
            queen_confidence=0.20,  # Below QUEEN_VETO_THRESHOLD (0.30)
            king_health="SOVEREIGN",
            seer_grade="DIVINE_CLARITY",
            seer_score=0.95,
        )
        self.assertTrue(result.queen_vetoed)
        self.assertFalse(result.passed)
        self.assertEqual(result.action, ConsensusAction.HALT.value)
        self.assertEqual(result.queen_vote.vote, VoteResult.VETO.value)
        self.assertIn("VETO", result.reason)

    def test_queen_veto_vs_block_distinction(self):
        """VETO (below 0.30) is stronger than BLOCK (below 0.45)."""
        # Queen BLOCK (0.35 - above veto, below pass)
        result_block = self.engine.evaluate_consensus(
            queen_confidence=0.35,
            king_health="PROSPEROUS",
            seer_grade="CLEAR_SIGHT",
            seer_score=0.75,
        )
        self.assertEqual(result_block.queen_vote.vote, VoteResult.BLOCK.value)
        self.assertFalse(result_block.queen_vetoed)

        # Queen VETO (0.20 - below veto threshold)
        result_veto = self.engine.evaluate_consensus(
            queen_confidence=0.20,
            king_health="PROSPEROUS",
            seer_grade="CLEAR_SIGHT",
            seer_score=0.75,
        )
        self.assertEqual(result_veto.queen_vote.vote, VoteResult.VETO.value)
        self.assertTrue(result_veto.queen_vetoed)
        # Veto always results in HALT
        self.assertEqual(result_veto.action, ConsensusAction.HALT.value)

    def test_queen_has_most_connected_systems(self):
        """Queen has 11+ systems - more than King (5) or Seer (5)."""
        result = self.engine.evaluate_consensus(
            queen_confidence=0.75,
            king_health="PROSPEROUS",
            seer_grade="CLEAR_SIGHT",
            seer_score=0.77,
        )
        queen_systems = result.queen_vote.connected_systems
        king_systems = result.king_vote.connected_systems
        seer_systems = result.seer_vote.connected_systems

        self.assertEqual(queen_systems, len(QUEEN_CONNECTED_SYSTEMS))
        self.assertGreater(queen_systems, king_systems)
        self.assertGreater(queen_systems, seer_systems)
        # Queen has at least 11 systems
        self.assertGreaterEqual(queen_systems, 11)

    def test_queen_veto_at_exact_threshold(self):
        """At exactly the veto threshold, Queen does NOT veto (blocks instead)."""
        result = self.engine.evaluate_consensus(
            queen_confidence=0.30,  # Exactly at QUEEN_VETO_THRESHOLD
            king_health="PROSPEROUS",
            seer_grade="CLEAR_SIGHT",
            seer_score=0.77,
        )
        # 0.30 is NOT < 0.30, so should be BLOCK not VETO
        self.assertEqual(result.queen_vote.vote, VoteResult.BLOCK.value)
        self.assertFalse(result.queen_vetoed)

    def test_queen_veto_when_systems_down(self):
        """Queen blocks when required subsystems are offline."""
        result = self.engine.evaluate_consensus(
            queen_confidence=0.80,
            king_health="PROSPEROUS",
            seer_grade="CLEAR_SIGHT",
            seer_score=0.77,
            queen_data={"systems_online": 2, "systems_required": 4},
        )
        self.assertFalse(result.passed)
        self.assertEqual(result.queen_vote.vote, VoteResult.BLOCK.value)
        self.assertEqual(result.queen_vote.grade, "SYSTEMS_DOWN")

    def test_queen_zero_confidence_absolute_veto(self):
        """Zero confidence = absolute veto, hardest possible stop."""
        result = self.engine.evaluate_consensus(
            queen_confidence=0.0,
            king_health="SOVEREIGN",
            seer_grade="DIVINE_CLARITY",
            seer_score=0.99,
        )
        self.assertTrue(result.queen_vetoed)
        self.assertEqual(result.action, ConsensusAction.HALT.value)
        self.assertEqual(result.queen_vote.vote, VoteResult.VETO.value)


# ═══════════════════════════════════════════════════════════════════════════
# TEST 3: KING AND SEER ANALYTICAL DATA FLOWS FREELY
# ═══════════════════════════════════════════════════════════════════════════

class TestFreeDataExchange(unittest.TestCase):
    """
    King and Seer need analytical data pulled free - it flows as a
    freeway between all 3 systems. Each shares their data openly.
    """

    def setUp(self):
        self.engine = TriumvirateEngine()

    def test_king_shares_analytical_data(self):
        """King's financial data is shared freely with Queen and Seer."""
        king_data = {
            "total_realized_pnl": 5000.0,
            "unrealized_pnl": 1200.0,
            "win_rate": 62.0,
            "drawdown_pct": 5.0,
            "max_drawdown_pct": 15.0,
            "total_fees": 350.0,
            "equity": 125000.0,
            "cost_basis_available": True,
            "tax_liability": 1200.0,
        }
        result = self.engine.evaluate_consensus(
            queen_confidence=0.70,
            king_health="PROSPEROUS",
            seer_grade="CLEAR_SIGHT",
            seer_score=0.75,
            king_data=king_data,
        )
        # Verify King's data is in the exchange
        exchange = result.data_exchange
        self.assertIn("king_shares", exchange)
        king_shared = exchange["king_shares"]
        self.assertEqual(king_shared["total_realized_pnl"], 5000.0)
        self.assertEqual(king_shared["win_rate"], 62.0)
        self.assertEqual(king_shared["equity"], 125000.0)
        self.assertTrue(king_shared["cost_basis_available"])

    def test_seer_shares_oracle_data(self):
        """Seer's oracle data is shared freely with Queen and King."""
        seer_data = {
            "risk_modifier": 1.2,
            "action": "BUY_BIAS",
            "prophecy": "The cosmos aligns with profit",
            "gaia_score": 0.82,
            "cosmos_score": 0.71,
            "harmony_score": 0.88,
            "spirits_score": 0.65,
            "time_score": 0.73,
            "trend": "IMPROVING",
        }
        result = self.engine.evaluate_consensus(
            queen_confidence=0.70,
            king_health="PROSPEROUS",
            seer_grade="CLEAR_SIGHT",
            seer_score=0.77,
            seer_data=seer_data,
        )
        exchange = result.data_exchange
        self.assertIn("seer_shares", exchange)
        seer_shared = exchange["seer_shares"]
        self.assertEqual(seer_shared["risk_modifier"], 1.2)
        self.assertEqual(seer_shared["gaia_score"], 0.82)
        self.assertEqual(seer_shared["trend"], "IMPROVING")
        self.assertEqual(seer_shared["prophecy"], "The cosmos aligns with profit")

    def test_queen_shares_subsystem_data(self):
        """Queen's 11+ subsystem data is shared freely."""
        queen_data = {
            "coherence": 0.85,
            "harmonic_integrity": 0.90,
            "quantum_omega": 0.78,
            "lambda_stability": 0.95,
            "probability_nexus": 0.82,
            "profit_gate_active": True,
            "direction": "BULLISH",
            "decision_score": 0.72,
            "emotional_state": "CONFIDENT",
        }
        result = self.engine.evaluate_consensus(
            queen_confidence=0.85,
            king_health="SOVEREIGN",
            seer_grade="DIVINE_CLARITY",
            seer_score=0.92,
            queen_data=queen_data,
        )
        exchange = result.data_exchange
        self.assertIn("queen_shares", exchange)
        queen_shared = exchange["queen_shares"]
        self.assertEqual(queen_shared["harmonic_integrity"], 0.90)
        self.assertEqual(queen_shared["direction"], "BULLISH")
        self.assertEqual(queen_shared["decision_score"], 0.72)
        self.assertEqual(queen_shared["subsystem_count"], len(QUEEN_CONNECTED_SYSTEMS))

    def test_all_data_flows_bidirectionally(self):
        """All 3 pillars share data that's available to all others."""
        result = self.engine.evaluate_consensus(
            queen_confidence=0.70,
            king_health="PROSPEROUS",
            seer_grade="CLEAR_SIGHT",
            seer_score=0.75,
            queen_data={"direction": "BULLISH"},
            king_data={"win_rate": 60.0},
            seer_data={"gaia_score": 0.80},
        )
        exchange = result.data_exchange
        # All three share data
        self.assertIn("queen_shares", exchange)
        self.assertIn("king_shares", exchange)
        self.assertIn("seer_shares", exchange)
        # System counts are tracked
        self.assertIn("total_systems", exchange)
        total = exchange["total_systems"]
        self.assertGreater(total, 0)
        self.assertEqual(
            total,
            exchange["queen_systems_count"] +
            exchange["king_systems_count"] +
            exchange["seer_systems_count"]
        )

    def test_king_audit_alerts_flow_to_consensus(self):
        """King's audit alerts affect consensus when CRITICAL."""
        result = self.engine.evaluate_consensus(
            queen_confidence=0.80,
            king_health="PROSPEROUS",
            seer_grade="CLEAR_SIGHT",
            seer_score=0.77,
            king_data={
                "audit_alerts": [
                    {"severity": "CRITICAL", "message": "Balance mismatch"},
                ]
            },
        )
        self.assertFalse(result.passed)
        self.assertEqual(result.king_vote.vote, VoteResult.BLOCK.value)
        self.assertEqual(result.king_vote.grade, "AUDIT_CRITICAL")

    def test_data_exchange_total_systems_count(self):
        """The data exchange tracks total connected systems across all pillars."""
        result = self.engine.evaluate_consensus(
            queen_confidence=0.70,
            king_health="PROSPEROUS",
            seer_grade="CLEAR_SIGHT",
            seer_score=0.75,
        )
        exchange = result.data_exchange
        # Queen: 11, King: 5, Seer: 5 = 21 total
        self.assertEqual(exchange["queen_systems_count"], len(QUEEN_CONNECTED_SYSTEMS))
        self.assertEqual(exchange["king_systems_count"], 5)
        self.assertEqual(exchange["seer_systems_count"], 5)
        self.assertEqual(exchange["total_systems"], len(QUEEN_CONNECTED_SYSTEMS) + 10)


# ═══════════════════════════════════════════════════════════════════════════
# TEST 4: CONTROL HANDOFF BETWEEN SYSTEMS
# ═══════════════════════════════════════════════════════════════════════════

class TestControlHandoff(unittest.TestCase):
    """
    Tests that control properly shifts between pillars based on
    context. Each pillar can take control from the others when
    their domain is relevant.
    """

    def setUp(self):
        self.engine = TriumvirateEngine()

    def test_queen_is_default_controller(self):
        """Queen is the default controller (most systems = highest authority)."""
        result = self.engine.evaluate_consensus(
            queen_confidence=0.70,
            king_health="PROSPEROUS",
            seer_grade="CLEAR_SIGHT",
            seer_score=0.75,
        )
        self.assertEqual(result.active_controller, PillarRole.QUEEN.value)

    def test_queen_takes_control_on_veto(self):
        """When Queen vetoes, she takes direct control."""
        result = self.engine.evaluate_consensus(
            queen_confidence=0.20,  # Veto
            king_health="PROSPEROUS",
            seer_grade="CLEAR_SIGHT",
            seer_score=0.75,
        )
        self.assertEqual(result.active_controller, PillarRole.QUEEN.value)
        self.assertTrue(result.queen_vetoed)

    def test_king_takes_control_during_financial_distress(self):
        """King takes control when treasury is BANKRUPT."""
        result = self.engine.evaluate_consensus(
            queen_confidence=0.70,
            king_health="BANKRUPT",
            seer_grade="CLEAR_SIGHT",
            seer_score=0.75,
        )
        self.assertEqual(result.active_controller, PillarRole.KING.value)

    def test_king_takes_control_when_strained(self):
        """King takes control when treasury is STRAINED."""
        result = self.engine.evaluate_consensus(
            queen_confidence=0.70,
            king_health="STRAINED",
            seer_grade="CLEAR_SIGHT",
            seer_score=0.75,
        )
        self.assertEqual(result.active_controller, PillarRole.KING.value)

    def test_seer_takes_control_when_blind(self):
        """Seer takes control when vision is BLIND (managing risk)."""
        result = self.engine.evaluate_consensus(
            queen_confidence=0.70,
            king_health="PROSPEROUS",
            seer_grade="BLIND",
            seer_score=0.15,
        )
        self.assertEqual(result.active_controller, PillarRole.SEER.value)

    def test_seer_takes_control_in_fog(self):
        """Seer takes control when vision is FOG."""
        result = self.engine.evaluate_consensus(
            queen_confidence=0.70,
            king_health="PROSPEROUS",
            seer_grade="FOG",
            seer_score=0.42,
        )
        self.assertEqual(result.active_controller, PillarRole.SEER.value)

    def test_king_takes_control_for_profit_taking(self):
        """King takes control during profit-taking events."""
        result = self.engine.evaluate_consensus(
            queen_confidence=0.70,
            king_health="PROSPEROUS",
            seer_grade="CLEAR_SIGHT",
            seer_score=0.75,
            context={"event": "PROFIT_TAKING"},
        )
        self.assertEqual(result.active_controller, PillarRole.KING.value)

    def test_seer_takes_control_for_risk_adjustment(self):
        """Seer takes control during risk adjustment events."""
        result = self.engine.evaluate_consensus(
            queen_confidence=0.70,
            king_health="PROSPEROUS",
            seer_grade="CLEAR_SIGHT",
            seer_score=0.75,
            context={"event": "RISK_ADJUSTMENT"},
        )
        self.assertEqual(result.active_controller, PillarRole.SEER.value)

    def test_queen_veto_overrides_king_control(self):
        """Even when King would take control, Queen veto takes precedence."""
        result = self.engine.evaluate_consensus(
            queen_confidence=0.15,  # Veto level
            king_health="BANKRUPT",  # King would normally take control
            seer_grade="BLIND",
            seer_score=0.10,
        )
        # Queen veto is Rule 1, takes precedence over King distress (Rule 2)
        self.assertEqual(result.active_controller, PillarRole.QUEEN.value)
        self.assertTrue(result.queen_vetoed)

    def test_control_handoff_sequence(self):
        """Test a sequence of control handoffs as conditions change."""
        engine = TriumvirateEngine()

        # Step 1: Normal conditions - Queen leads
        r1 = engine.evaluate_consensus(
            queen_confidence=0.70, king_health="PROSPEROUS",
            seer_grade="CLEAR_SIGHT", seer_score=0.75,
        )
        self.assertEqual(r1.active_controller, PillarRole.QUEEN.value)

        # Step 2: King goes BANKRUPT - King takes control
        r2 = engine.evaluate_consensus(
            queen_confidence=0.70, king_health="BANKRUPT",
            seer_grade="CLEAR_SIGHT", seer_score=0.75,
        )
        self.assertEqual(r2.active_controller, PillarRole.KING.value)

        # Step 3: Seer goes BLIND - Seer takes control
        r3 = engine.evaluate_consensus(
            queen_confidence=0.70, king_health="PROSPEROUS",
            seer_grade="BLIND", seer_score=0.15,
        )
        self.assertEqual(r3.active_controller, PillarRole.SEER.value)

        # Step 4: Back to normal - Queen resumes
        r4 = engine.evaluate_consensus(
            queen_confidence=0.70, king_health="PROSPEROUS",
            seer_grade="CLEAR_SIGHT", seer_score=0.75,
        )
        self.assertEqual(r4.active_controller, PillarRole.QUEEN.value)

        # Verify handoff history was recorded
        history = engine.get_handoff_history()
        self.assertGreaterEqual(len(history), 3)  # At least 3 handoffs

    def test_handoff_records_from_and_to(self):
        """Control handoff records track source and destination."""
        engine = TriumvirateEngine()

        # Normal -> King distress
        engine.evaluate_consensus(
            queen_confidence=0.70, king_health="PROSPEROUS",
            seer_grade="CLEAR_SIGHT", seer_score=0.75,
        )
        engine.evaluate_consensus(
            queen_confidence=0.70, king_health="BANKRUPT",
            seer_grade="CLEAR_SIGHT", seer_score=0.75,
        )

        history = engine.get_handoff_history()
        self.assertGreaterEqual(len(history), 1)
        last_handoff = history[-1]
        self.assertEqual(last_handoff.from_pillar, PillarRole.QUEEN.value)
        self.assertEqual(last_handoff.to_pillar, PillarRole.KING.value)
        self.assertIn("BANKRUPT", last_handoff.reason)


# ═══════════════════════════════════════════════════════════════════════════
# TEST 5: CONSENSUS STRENGTH AND ACTION MAPPING
# ═══════════════════════════════════════════════════════════════════════════

class TestConsensusStrength(unittest.TestCase):
    """
    When all 3 pass, the strength of consensus determines the action.
    """

    def setUp(self):
        self.engine = TriumvirateEngine()

    def test_strong_buy_requires_high_alignment(self):
        """STRONG_BUY requires all pillars high and aligned."""
        result = self.engine.evaluate_consensus(
            queen_confidence=0.90,
            king_health="SOVEREIGN",
            seer_grade="DIVINE_CLARITY",
            seer_score=0.92,
        )
        self.assertTrue(result.passed)
        self.assertEqual(result.action, ConsensusAction.STRONG_BUY.value)

    def test_buy_with_good_scores(self):
        """BUY with good but not exceptional scores."""
        result = self.engine.evaluate_consensus(
            queen_confidence=0.72,
            king_health="PROSPEROUS",
            seer_grade="CLEAR_SIGHT",
            seer_score=0.73,
        )
        self.assertTrue(result.passed)
        self.assertIn(result.action, [
            ConsensusAction.BUY.value,
            ConsensusAction.STRONG_BUY.value,
        ])

    def test_hold_with_moderate_scores(self):
        """HOLD when all pass but scores are moderate."""
        result = self.engine.evaluate_consensus(
            queen_confidence=0.50,
            king_health="STABLE",
            seer_grade="PARTIAL_VISION",
            seer_score=0.55,
        )
        self.assertTrue(result.passed)
        self.assertIn(result.action, [
            ConsensusAction.HOLD.value,
            ConsensusAction.SELL.value,
        ])

    def test_alignment_score_high_when_pillars_agree(self):
        """Alignment score is high when all pillars have similar scores."""
        result = self.engine.evaluate_consensus(
            queen_confidence=0.75,
            king_health="PROSPEROUS",  # score=0.75
            seer_grade="CLEAR_SIGHT",
            seer_score=0.75,
        )
        self.assertGreater(result.alignment_score, 0.90)

    def test_alignment_score_low_when_pillars_diverge(self):
        """Alignment is lower when pillar scores diverge."""
        result = self.engine.evaluate_consensus(
            queen_confidence=0.90,
            king_health="STABLE",  # score=0.55
            seer_grade="PARTIAL_VISION",
            seer_score=0.55,
        )
        self.assertLess(result.alignment_score, 0.90)


# ═══════════════════════════════════════════════════════════════════════════
# TEST 6: INDIVIDUAL PILLAR EVALUATORS
# ═══════════════════════════════════════════════════════════════════════════

class TestQueenEvaluator(unittest.TestCase):
    """Test the Queen's individual vote logic."""

    def setUp(self):
        self.evaluator = QueenEvaluator()

    def test_queen_pass_above_threshold(self):
        vote = self.evaluator.evaluate(0.70)
        self.assertEqual(vote.vote, VoteResult.PASS.value)
        self.assertEqual(vote.pillar, "QUEEN")

    def test_queen_block_below_threshold(self):
        vote = self.evaluator.evaluate(0.40)
        self.assertEqual(vote.vote, VoteResult.BLOCK.value)

    def test_queen_veto_below_veto_threshold(self):
        vote = self.evaluator.evaluate(0.25)
        self.assertEqual(vote.vote, VoteResult.VETO.value)

    def test_queen_grade_supreme(self):
        vote = self.evaluator.evaluate(0.90)
        self.assertEqual(vote.grade, "SUPREME")

    def test_queen_grade_commanding(self):
        vote = self.evaluator.evaluate(0.75)
        self.assertEqual(vote.grade, "COMMANDING")

    def test_queen_grade_steady(self):
        vote = self.evaluator.evaluate(0.60)
        self.assertEqual(vote.grade, "STEADY")

    def test_queen_grade_cautious(self):
        vote = self.evaluator.evaluate(0.46)
        self.assertEqual(vote.grade, "CAUTIOUS")

    def test_queen_connected_systems_count(self):
        vote = self.evaluator.evaluate(0.70)
        self.assertEqual(vote.connected_systems, len(QUEEN_CONNECTED_SYSTEMS))
        self.assertGreaterEqual(vote.connected_systems, 11)

    def test_queen_shares_data(self):
        vote = self.evaluator.evaluate(0.70, {"direction": "BULLISH"})
        self.assertIn("direction", vote.data)
        self.assertEqual(vote.data["direction"], "BULLISH")


class TestKingEvaluator(unittest.TestCase):
    """Test the King's individual vote logic."""

    def setUp(self):
        self.evaluator = KingEvaluator()

    def test_king_pass_sovereign(self):
        vote = self.evaluator.evaluate("SOVEREIGN")
        self.assertEqual(vote.vote, VoteResult.PASS.value)
        self.assertEqual(vote.score, 0.90)

    def test_king_pass_prosperous(self):
        vote = self.evaluator.evaluate("PROSPEROUS")
        self.assertEqual(vote.vote, VoteResult.PASS.value)
        self.assertEqual(vote.score, 0.75)

    def test_king_pass_stable(self):
        vote = self.evaluator.evaluate("STABLE")
        self.assertEqual(vote.vote, VoteResult.PASS.value)
        self.assertEqual(vote.score, 0.55)

    def test_king_block_strained(self):
        vote = self.evaluator.evaluate("STRAINED")
        self.assertEqual(vote.vote, VoteResult.BLOCK.value)

    def test_king_block_bankrupt(self):
        vote = self.evaluator.evaluate("BANKRUPT")
        self.assertEqual(vote.vote, VoteResult.BLOCK.value)
        self.assertEqual(vote.score, 0.10)

    def test_king_block_on_critical_audit(self):
        vote = self.evaluator.evaluate("PROSPEROUS", {
            "audit_alerts": [{"severity": "CRITICAL", "message": "Mismatch"}]
        })
        self.assertEqual(vote.vote, VoteResult.BLOCK.value)
        self.assertEqual(vote.grade, "AUDIT_CRITICAL")

    def test_king_pass_with_info_audit(self):
        """Non-critical audit alerts don't block."""
        vote = self.evaluator.evaluate("PROSPEROUS", {
            "audit_alerts": [{"severity": "INFO", "message": "All good"}]
        })
        self.assertEqual(vote.vote, VoteResult.PASS.value)

    def test_king_shares_financial_data(self):
        vote = self.evaluator.evaluate("PROSPEROUS", {
            "total_realized_pnl": 5000.0,
            "win_rate": 62.0,
        })
        self.assertEqual(vote.data["total_realized_pnl"], 5000.0)
        self.assertEqual(vote.data["win_rate"], 62.0)


class TestSeerEvaluator(unittest.TestCase):
    """Test the Seer's individual vote logic."""

    def setUp(self):
        self.evaluator = SeerEvaluator()

    def test_seer_pass_divine_clarity(self):
        vote = self.evaluator.evaluate("DIVINE_CLARITY", 0.92)
        self.assertEqual(vote.vote, VoteResult.PASS.value)

    def test_seer_pass_clear_sight(self):
        vote = self.evaluator.evaluate("CLEAR_SIGHT", 0.77)
        self.assertEqual(vote.vote, VoteResult.PASS.value)

    def test_seer_pass_partial_vision(self):
        vote = self.evaluator.evaluate("PARTIAL_VISION", 0.60)
        self.assertEqual(vote.vote, VoteResult.PASS.value)

    def test_seer_block_fog(self):
        vote = self.evaluator.evaluate("FOG", 0.42)
        self.assertEqual(vote.vote, VoteResult.BLOCK.value)

    def test_seer_block_blind(self):
        vote = self.evaluator.evaluate("BLIND", 0.15)
        self.assertEqual(vote.vote, VoteResult.BLOCK.value)

    def test_seer_shares_oracle_data(self):
        vote = self.evaluator.evaluate("CLEAR_SIGHT", 0.77, {
            "gaia_score": 0.82,
            "cosmos_score": 0.71,
            "risk_modifier": 1.1,
        })
        self.assertEqual(vote.data["gaia_score"], 0.82)
        self.assertEqual(vote.data["risk_modifier"], 1.1)


# ═══════════════════════════════════════════════════════════════════════════
# TEST 7: CONTROL HANDOFF ENGINE (ISOLATED)
# ═══════════════════════════════════════════════════════════════════════════

class TestControlHandoffEngine(unittest.TestCase):
    """Test the control handoff engine in isolation."""

    def setUp(self):
        self.engine = ControlHandoffEngine()

    def _make_vote(self, pillar, vote, score, grade, data=None):
        return PillarVote(
            pillar=pillar, vote=vote, score=score, grade=grade,
            reason="test", data=data or {}, connected_systems=5,
        )

    def test_initial_controller_is_queen(self):
        self.assertEqual(self.engine.current_controller, PillarRole.QUEEN)

    def test_queen_veto_takes_control(self):
        queen = self._make_vote("QUEEN", VoteResult.VETO.value, 0.2, "SOVEREIGN_VETO")
        king = self._make_vote("KING", VoteResult.PASS.value, 0.75, "PROSPEROUS")
        seer = self._make_vote("SEER", VoteResult.PASS.value, 0.75, "CLEAR_SIGHT")

        controller, handoff = self.engine.determine_controller(queen, king, seer)
        self.assertEqual(controller, PillarRole.QUEEN)

    def test_king_distress_takes_control(self):
        queen = self._make_vote("QUEEN", VoteResult.PASS.value, 0.7, "COMMANDING")
        king = self._make_vote("KING", VoteResult.BLOCK.value, 0.1, "BANKRUPT")
        seer = self._make_vote("SEER", VoteResult.PASS.value, 0.75, "CLEAR_SIGHT")

        controller, handoff = self.engine.determine_controller(queen, king, seer)
        self.assertEqual(controller, PillarRole.KING)
        self.assertIsNotNone(handoff)
        self.assertEqual(handoff.to_pillar, PillarRole.KING.value)

    def test_seer_blind_takes_control(self):
        queen = self._make_vote("QUEEN", VoteResult.PASS.value, 0.7, "COMMANDING")
        king = self._make_vote("KING", VoteResult.PASS.value, 0.75, "PROSPEROUS")
        seer = self._make_vote("SEER", VoteResult.BLOCK.value, 0.15, "BLIND")

        controller, handoff = self.engine.determine_controller(queen, king, seer)
        self.assertEqual(controller, PillarRole.SEER)
        self.assertIsNotNone(handoff)

    def test_profit_taking_event_gives_king_control(self):
        queen = self._make_vote("QUEEN", VoteResult.PASS.value, 0.7, "COMMANDING")
        king = self._make_vote("KING", VoteResult.PASS.value, 0.75, "PROSPEROUS")
        seer = self._make_vote("SEER", VoteResult.PASS.value, 0.75, "CLEAR_SIGHT")

        controller, handoff = self.engine.determine_controller(
            queen, king, seer, {"event": "PROFIT_TAKING"}
        )
        self.assertEqual(controller, PillarRole.KING)

    def test_risk_adjustment_gives_seer_control(self):
        queen = self._make_vote("QUEEN", VoteResult.PASS.value, 0.7, "COMMANDING")
        king = self._make_vote("KING", VoteResult.PASS.value, 0.75, "PROSPEROUS")
        seer = self._make_vote("SEER", VoteResult.PASS.value, 0.75, "CLEAR_SIGHT")

        controller, handoff = self.engine.determine_controller(
            queen, king, seer, {"event": "RISK_ADJUSTMENT"}
        )
        self.assertEqual(controller, PillarRole.SEER)

    def test_declining_seer_takes_control(self):
        """Seer takes control when cosmic alignment is declining."""
        queen = self._make_vote("QUEEN", VoteResult.PASS.value, 0.7, "COMMANDING")
        king = self._make_vote("KING", VoteResult.PASS.value, 0.75, "PROSPEROUS")
        seer = self._make_vote("SEER", VoteResult.PASS.value, 0.45, "PARTIAL_VISION",
                               data={"trend": "DECLINING"})

        controller, handoff = self.engine.determine_controller(queen, king, seer)
        self.assertEqual(controller, PillarRole.SEER)

    def test_no_handoff_when_controller_unchanged(self):
        """No handoff record when controller stays the same."""
        queen = self._make_vote("QUEEN", VoteResult.PASS.value, 0.7, "COMMANDING")
        king = self._make_vote("KING", VoteResult.PASS.value, 0.75, "PROSPEROUS")
        seer = self._make_vote("SEER", VoteResult.PASS.value, 0.75, "CLEAR_SIGHT")

        controller, handoff = self.engine.determine_controller(queen, king, seer)
        self.assertEqual(controller, PillarRole.QUEEN)
        self.assertIsNone(handoff)  # No change, no handoff

    def test_handoff_history_accumulates(self):
        """Handoff history builds up over multiple changes."""
        queen = self._make_vote("QUEEN", VoteResult.PASS.value, 0.7, "COMMANDING")
        king_ok = self._make_vote("KING", VoteResult.PASS.value, 0.75, "PROSPEROUS")
        king_bad = self._make_vote("KING", VoteResult.BLOCK.value, 0.1, "BANKRUPT")
        seer = self._make_vote("SEER", VoteResult.PASS.value, 0.75, "CLEAR_SIGHT")

        # Start with Queen
        self.engine.determine_controller(queen, king_ok, seer)
        self.assertEqual(len(self.engine.get_handoff_history()), 0)

        # King takes over
        self.engine.determine_controller(queen, king_bad, seer)
        self.assertEqual(len(self.engine.get_handoff_history()), 1)

        # Queen resumes
        self.engine.determine_controller(queen, king_ok, seer)
        self.assertEqual(len(self.engine.get_handoff_history()), 2)


# ═══════════════════════════════════════════════════════════════════════════
# TEST 8: OVERRIDE AND ESCALATION SCENARIOS
# ═══════════════════════════════════════════════════════════════════════════

class TestOverrideScenarios(unittest.TestCase):
    """
    Test complex override scenarios where systems compete for control.
    """

    def setUp(self):
        self.engine = TriumvirateEngine()

    def test_queen_veto_overrides_king_bankrupt(self):
        """Queen veto takes precedence over King bankrupt."""
        result = self.engine.evaluate_consensus(
            queen_confidence=0.15,
            king_health="BANKRUPT",
            seer_grade="BLIND",
            seer_score=0.10,
        )
        # Queen veto is the dominant signal
        self.assertTrue(result.queen_vetoed)
        self.assertEqual(result.action, ConsensusAction.HALT.value)
        # Queen retains control even when King is bankrupt
        self.assertEqual(result.active_controller, PillarRole.QUEEN.value)

    def test_king_bankrupt_overrides_good_queen_seer(self):
        """King bankrupt halts even when Queen and Seer are perfect."""
        result = self.engine.evaluate_consensus(
            queen_confidence=0.95,
            king_health="BANKRUPT",
            seer_grade="DIVINE_CLARITY",
            seer_score=0.95,
        )
        self.assertFalse(result.passed)
        self.assertEqual(result.action, ConsensusAction.HALT.value)

    def test_seer_blind_blocks_new_entries(self):
        """Seer BLIND blocks entry even with good Queen+King."""
        result = self.engine.evaluate_consensus(
            queen_confidence=0.90,
            king_health="SOVEREIGN",
            seer_grade="BLIND",
            seer_score=0.10,
        )
        self.assertFalse(result.passed)
        # Should HALT when Seer is blind
        self.assertEqual(result.action, ConsensusAction.HALT.value)

    def test_seer_fog_results_in_hold(self):
        """Seer FOG results in HOLD (not as severe as BLIND)."""
        result = self.engine.evaluate_consensus(
            queen_confidence=0.80,
            king_health="PROSPEROUS",
            seer_grade="FOG",
            seer_score=0.42,
        )
        self.assertFalse(result.passed)
        self.assertEqual(result.action, ConsensusAction.HOLD.value)

    def test_king_strained_results_in_sell(self):
        """King STRAINED results in SELL recommendation."""
        result = self.engine.evaluate_consensus(
            queen_confidence=0.80,
            king_health="STRAINED",
            seer_grade="CLEAR_SIGHT",
            seer_score=0.75,
        )
        self.assertFalse(result.passed)
        self.assertEqual(result.action, ConsensusAction.SELL.value)

    def test_escalation_from_hold_to_halt(self):
        """Conditions escalating from good to crisis."""
        engine = TriumvirateEngine()

        # Good conditions
        r1 = engine.evaluate_consensus(
            queen_confidence=0.80,
            king_health="PROSPEROUS",
            seer_grade="CLEAR_SIGHT",
            seer_score=0.75,
        )
        self.assertTrue(r1.passed)
        self.assertIn(r1.action, [ConsensusAction.BUY.value, ConsensusAction.STRONG_BUY.value])

        # Seer goes foggy - HOLD
        r2 = engine.evaluate_consensus(
            queen_confidence=0.80,
            king_health="PROSPEROUS",
            seer_grade="FOG",
            seer_score=0.42,
        )
        self.assertFalse(r2.passed)
        self.assertEqual(r2.action, ConsensusAction.HOLD.value)

        # King goes strained - SELL
        r3 = engine.evaluate_consensus(
            queen_confidence=0.80,
            king_health="STRAINED",
            seer_grade="FOG",
            seer_score=0.42,
        )
        self.assertFalse(r3.passed)
        self.assertEqual(r3.action, ConsensusAction.SELL.value)

        # Queen vetoes - HALT
        r4 = engine.evaluate_consensus(
            queen_confidence=0.20,
            king_health="STRAINED",
            seer_grade="BLIND",
            seer_score=0.10,
        )
        self.assertTrue(r4.queen_vetoed)
        self.assertEqual(r4.action, ConsensusAction.HALT.value)


# ═══════════════════════════════════════════════════════════════════════════
# TEST 9: BOUNDARY CONDITIONS AND EDGE CASES
# ═══════════════════════════════════════════════════════════════════════════

class TestBoundaryConditions(unittest.TestCase):
    """Test edge cases and boundary conditions."""

    def setUp(self):
        self.engine = TriumvirateEngine()

    def test_all_at_minimum_pass_thresholds(self):
        """All three at their minimum passing thresholds."""
        result = self.engine.evaluate_consensus(
            queen_confidence=0.46,  # Just above 0.45
            king_health="STABLE",   # Lowest passing grade
            seer_grade="PARTIAL_VISION",  # Lowest passing grade
            seer_score=0.56,
        )
        self.assertTrue(result.passed)

    def test_queen_at_exact_pass_threshold(self):
        """Queen at exactly the pass threshold passes (threshold is exclusive lower bound)."""
        result = self.engine.evaluate_consensus(
            queen_confidence=0.45,  # Exactly at threshold
            king_health="PROSPEROUS",
            seer_grade="CLEAR_SIGHT",
            seer_score=0.77,
        )
        # 0.45 is NOT < 0.45, so Queen passes (threshold check uses <)
        self.assertTrue(result.passed)

    def test_queen_just_below_pass_threshold_blocks(self):
        """Queen just below pass threshold blocks."""
        result = self.engine.evaluate_consensus(
            queen_confidence=0.449,  # Just below 0.45
            king_health="PROSPEROUS",
            seer_grade="CLEAR_SIGHT",
            seer_score=0.77,
        )
        self.assertFalse(result.passed)

    def test_queen_just_above_pass_threshold(self):
        """Queen just above pass threshold passes."""
        result = self.engine.evaluate_consensus(
            queen_confidence=0.451,
            king_health="PROSPEROUS",
            seer_grade="CLEAR_SIGHT",
            seer_score=0.77,
        )
        self.assertTrue(result.passed)

    def test_perfect_scores_strong_buy(self):
        """All perfect scores = STRONG_BUY."""
        result = self.engine.evaluate_consensus(
            queen_confidence=1.0,
            king_health="SOVEREIGN",
            seer_grade="DIVINE_CLARITY",
            seer_score=1.0,
        )
        self.assertTrue(result.passed)
        self.assertEqual(result.action, ConsensusAction.STRONG_BUY.value)
        self.assertGreater(result.alignment_score, 0.90)

    def test_zero_scores_halt(self):
        """All zero scores = HALT."""
        result = self.engine.evaluate_consensus(
            queen_confidence=0.0,
            king_health="BANKRUPT",
            seer_grade="BLIND",
            seer_score=0.0,
        )
        self.assertFalse(result.passed)
        self.assertEqual(result.action, ConsensusAction.HALT.value)

    def test_unknown_king_health_defaults(self):
        """Unknown King health string defaults to reasonable behavior."""
        result = self.engine.evaluate_consensus(
            queen_confidence=0.70,
            king_health="UNKNOWN_STATUS",
            seer_grade="CLEAR_SIGHT",
            seer_score=0.75,
        )
        # Unknown health gets score 0.5 and passes (not in block list)
        self.assertEqual(result.king_vote.vote, VoteResult.PASS.value)

    def test_consensus_history_tracked(self):
        """Consensus history is maintained across evaluations."""
        for _ in range(5):
            self.engine.evaluate_consensus(
                queen_confidence=0.70,
                king_health="PROSPEROUS",
                seer_grade="CLEAR_SIGHT",
                seer_score=0.75,
            )
        history = self.engine.get_consensus_history()
        self.assertEqual(len(history), 5)

    def test_engine_summary(self):
        """Engine provides summary of its state."""
        self.engine.evaluate_consensus(
            queen_confidence=0.70,
            king_health="PROSPEROUS",
            seer_grade="CLEAR_SIGHT",
            seer_score=0.75,
        )
        summary = self.engine.get_summary()
        self.assertIn("active_controller", summary)
        self.assertIn("total_evaluations", summary)
        self.assertEqual(summary["total_evaluations"], 1)
        self.assertEqual(summary["queen_systems"], len(QUEEN_CONNECTED_SYSTEMS))

    def test_reason_includes_blocker_info(self):
        """When blocked, the reason identifies which pillar blocked."""
        result = self.engine.evaluate_consensus(
            queen_confidence=0.80,
            king_health="PROSPEROUS",
            seer_grade="FOG",
            seer_score=0.42,
        )
        self.assertIn("Seer", result.reason)
        self.assertIn("FOG", result.reason)


# ═══════════════════════════════════════════════════════════════════════════
# TEST 10: SINGLETON AND MODULE-LEVEL FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

class TestSingleton(unittest.TestCase):
    """Test the singleton pattern for the Triumvirate engine."""

    def test_get_triumvirate_returns_same_instance(self):
        """get_triumvirate() always returns the same instance."""
        import aureon_triumvirate
        aureon_triumvirate._triumvirate_instance = None  # Reset

        t1 = get_triumvirate()
        t2 = get_triumvirate()
        self.assertIs(t1, t2)

        # Cleanup
        aureon_triumvirate._triumvirate_instance = None


# ═══════════════════════════════════════════════════════════════════════════
# TEST 11: COMPLETE INTERACTION SIMULATION
# ═══════════════════════════════════════════════════════════════════════════

class TestCompleteInteractionSimulation(unittest.TestCase):
    """
    Simulate a complete trading session where all 3 systems interact,
    hand off control, share data, and the Queen exercises veto.
    """

    def test_full_trading_session_simulation(self):
        """Simulate a multi-phase trading session with all 3 pillars."""
        engine = TriumvirateEngine()
        results = []

        # ── Phase 1: Dawn - Systems boot up, all good ──
        r = engine.evaluate_consensus(
            queen_confidence=0.75,
            king_health="STABLE",
            seer_grade="CLEAR_SIGHT",
            seer_score=0.72,
            queen_data={"direction": "BULLISH", "coherence": 0.75},
            king_data={"total_realized_pnl": 100, "win_rate": 55},
            seer_data={"gaia_score": 0.70, "trend": "STABLE"},
        )
        results.append(r)
        self.assertTrue(r.passed, "Phase 1 should pass - all systems healthy")
        self.assertEqual(r.active_controller, PillarRole.QUEEN.value)

        # ── Phase 2: Market turbulence - Seer detects cosmic disturbance ──
        r = engine.evaluate_consensus(
            queen_confidence=0.65,
            king_health="STABLE",
            seer_grade="FOG",
            seer_score=0.42,
            seer_data={"trend": "DECLINING", "cosmos_score": 0.30},
        )
        results.append(r)
        self.assertFalse(r.passed, "Phase 2 should fail - Seer in FOG")
        self.assertEqual(r.active_controller, PillarRole.SEER.value,
                        "Seer should take control in FOG")
        self.assertEqual(r.action, ConsensusAction.HOLD.value)

        # ── Phase 3: Financial strain - King detects losses ──
        r = engine.evaluate_consensus(
            queen_confidence=0.60,
            king_health="STRAINED",
            seer_grade="FOG",
            seer_score=0.42,
            king_data={"total_realized_pnl": -30, "drawdown_pct": 12},
        )
        results.append(r)
        self.assertFalse(r.passed)
        self.assertEqual(r.active_controller, PillarRole.KING.value,
                        "King should take control when STRAINED")
        self.assertEqual(r.action, ConsensusAction.SELL.value)

        # ── Phase 4: Crisis - Queen vetoes everything ──
        r = engine.evaluate_consensus(
            queen_confidence=0.20,
            king_health="STRAINED",
            seer_grade="BLIND",
            seer_score=0.10,
        )
        results.append(r)
        self.assertTrue(r.queen_vetoed)
        self.assertEqual(r.action, ConsensusAction.HALT.value)
        self.assertEqual(r.active_controller, PillarRole.QUEEN.value,
                        "Queen takes control with VETO")

        # ── Phase 5: Recovery - Systems gradually improve ──
        r = engine.evaluate_consensus(
            queen_confidence=0.55,
            king_health="STABLE",
            seer_grade="PARTIAL_VISION",
            seer_score=0.58,
        )
        results.append(r)
        self.assertTrue(r.passed, "Phase 5 should pass - systems recovering")
        self.assertEqual(r.active_controller, PillarRole.QUEEN.value)

        # ── Phase 6: Prosperity - All systems aligned ──
        r = engine.evaluate_consensus(
            queen_confidence=0.88,
            king_health="SOVEREIGN",
            seer_grade="DIVINE_CLARITY",
            seer_score=0.90,
            queen_data={"direction": "BULLISH", "decision_score": 0.85},
            king_data={"total_realized_pnl": 5000, "win_rate": 65, "equity": 125000},
            seer_data={"gaia_score": 0.88, "cosmos_score": 0.85, "trend": "IMPROVING"},
        )
        results.append(r)
        self.assertTrue(r.passed)
        self.assertEqual(r.action, ConsensusAction.STRONG_BUY.value)
        self.assertGreater(r.alignment_score, 0.85)

        # ── Phase 7: Profit-taking - King takes the lead ──
        r = engine.evaluate_consensus(
            queen_confidence=0.80,
            king_health="SOVEREIGN",
            seer_grade="CLEAR_SIGHT",
            seer_score=0.75,
            context={"event": "PROFIT_TAKING"},
        )
        results.append(r)
        self.assertTrue(r.passed)
        self.assertEqual(r.active_controller, PillarRole.KING.value,
                        "King should lead profit-taking")

        # Verify we went through the full cycle
        self.assertEqual(len(results), 7)

        # Verify handoff history captured the session
        history = engine.get_handoff_history()
        self.assertGreaterEqual(len(history), 4, "At least 4 handoffs in the session")

        # Verify data was shared in all phases
        for r in results:
            self.assertIn("queen_shares", r.data_exchange)
            self.assertIn("king_shares", r.data_exchange)
            self.assertIn("seer_shares", r.data_exchange)

    def test_rapid_control_handoff_sequence(self):
        """Test rapid handoffs don't cause issues."""
        engine = TriumvirateEngine()

        scenarios = [
            (0.70, "PROSPEROUS", "CLEAR_SIGHT", 0.75),  # Queen leads
            (0.70, "BANKRUPT", "CLEAR_SIGHT", 0.75),    # King takes over
            (0.70, "PROSPEROUS", "BLIND", 0.15),         # Seer takes over
            (0.15, "PROSPEROUS", "CLEAR_SIGHT", 0.75),   # Queen vetoes
            (0.70, "PROSPEROUS", "CLEAR_SIGHT", 0.75),   # Queen leads again
            (0.70, "STRAINED", "FOG", 0.42),             # King takes over
            (0.70, "PROSPEROUS", "CLEAR_SIGHT", 0.75),   # Queen leads again
        ]

        for qc, kh, sg, ss in scenarios:
            engine.evaluate_consensus(
                queen_confidence=qc, king_health=kh,
                seer_grade=sg, seer_score=ss,
            )

        history = engine.get_handoff_history()
        # Should have multiple handoffs
        self.assertGreater(len(history), 3)

        # All handoffs should have valid pillar names
        valid_pillars = {PillarRole.QUEEN.value, PillarRole.KING.value, PillarRole.SEER.value}
        for h in history:
            self.assertIn(h.from_pillar, valid_pillars)
            self.assertIn(h.to_pillar, valid_pillars)
            self.assertNotEqual(h.from_pillar, h.to_pillar)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN - Run all tests
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("AUREON TRIUMVIRATE - COMPREHENSIVE INTEGRATION TEST SUITE")
    print("Testing: Queen (11+ systems) + King (5 Deciphers) + Seer (5 Oracles)")
    print("Freeway Consensus: All 3 must pass. Queen has absolute veto.")
    print("=" * 70)
    print()

    # Run with verbose output
    unittest.main(verbosity=2)
