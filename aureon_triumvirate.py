#!/usr/bin/env python3
"""
AUREON QUADRUMVIRATE - Four-Pillar Freeway Consensus Engine
=====================================================
"Four minds, one truth. All must agree. The Queen has final say."

The Quadrumvirate is the governance system for the Aureon trading ecosystem.
All FOUR pillars must independently vote PASS for any action to proceed
(freeway consensus - all lanes must be clear). However, the Queen holds
absolute veto power because she has the most systems connected to her
(11+ subsystems: Temporal Dialer, Harmonic Chain Master, Probability
Nexus, ThoughtBus, Elephant Memory, Queen Neuron, etc.).

THE FOUR PILLARS:
  Queen - Trading cognition (11+ systems = ABSOLUTE VETO)
  King  - Financial truth (5 Royal Deciphers)
  Seer  - Cosmic coherence (5 Oracles)
  Lyra  - Emotional frequency & harmonics (6 Chambers, 22+ systems)

FREEWAY CONSENSUS RULES:
  1. All 4 pillars must independently vote PASS for an action to proceed
  2. If ANY pillar votes BLOCK, the action is blocked
  3. The Queen has ABSOLUTE VETO - she can override all others
  4. The King has FINANCIAL VETO - BANKRUPT halts everything
  5. The Seer has COSMIC VETO - BLIND blocks new entries
  6. Lyra has HARMONIC VETO - SILENCE blocks new entries

CONTROL HANDOFF:
  The active controller shifts based on domain:
  - Queen leads: trade execution, position management, entries/exits
  - King leads:  profit-taking decisions, financial health, tax events
  - Seer leads:  risk adjustment, regime detection, cosmic alignment
  - Lyra leads:  emotional regime changes, harmonic dissonance, exit urgency

DATA FLOW (Freeway - all data flows freely between all 4):
  Queen <-> King:  P&L data, cost basis, position values
  Queen <-> Seer:  coherence scores, risk modifiers, vision grades
  Queen <-> Lyra:  emotional frequency, harmonic field, position multipliers
  King  <-> Seer:  financial health, portfolio snapshots, prophecy
  King  <-> Lyra:  exit urgency, emotional P&L context
  Seer  <-> Lyra:  cosmic alignment, harmonic resonance, solfeggio

Gary Leckey | February 2026
"""

import time
import logging
from enum import Enum
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# TRIUMVIRATE CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

# Queen's connected systems (why she has veto - most systems report to her)
QUEEN_CONNECTED_SYSTEMS = [
    "temporal_dialer", "temporal_ladder", "timeline_oracle",
    "harmonic_chain_master", "global_harmonic_field",
    "harmonic_signal_chain", "harmonic_fusion",
    "probability_nexus", "elephant_memory",
    "queen_neuron", "thought_bus",
]

# Lyra's connected systems (22+ harmonic/emotional/frequency systems)
LYRA_CONNECTED_SYSTEMS = [
    "harmonic_waveform_scanner", "harmonic_chain_master",
    "harmonic_signal_chain", "harmonic_fusion",
    "schumann_resonance_bridge", "earth_resonance_engine",
    "queen_harmonic_voice", "harmonic_alphabet",
    "harmonic_reality", "global_harmonic_field",
    "6d_harmonic_waveform", "harmonic_seed",
    "hft_harmonic_mycelium", "harmonic_momentum_wave",
    "harmonic_binary_protocol", "harmonic_counter_frequency",
    "harmonic_liquid_aluminium", "harmonic_symbol_table",
    "harmonic_underlay", "wave_simulation",
    "planetary_harmonic_sweep", "queen_coherence_mandala",
]

# Minimum thresholds for each pillar to independently PASS
QUEEN_PASS_THRESHOLD = 0.45      # Queen confidence must exceed this
KING_PASS_GRADES = ["SOVEREIGN", "PROSPEROUS", "STABLE"]  # King must be healthy
SEER_PASS_GRADES = ["DIVINE_CLARITY", "CLEAR_SIGHT", "PARTIAL_VISION"]  # Seer must see
LYRA_PASS_GRADES = ["DIVINE_HARMONY", "CLEAR_RESONANCE", "PARTIAL_HARMONY"]  # Lyra must feel

# Queen veto threshold - below this she blocks regardless
QUEEN_VETO_THRESHOLD = 0.30


class PillarRole(Enum):
    """Which pillar currently has control authority."""
    QUEEN = "QUEEN"   # Trading cognition - entries, exits, position management
    KING = "KING"     # Financial truth - profit-taking, health, tax
    SEER = "SEER"     # Cosmic coherence - risk adjustment, regime detection
    LYRA = "LYRA"     # Emotional frequency - harmonics, sentiment, exit urgency


class ConsensusAction(Enum):
    """Possible consensus outcomes."""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"
    HALT = "HALT"


class VoteResult(Enum):
    """A pillar's individual vote."""
    PASS = "PASS"
    BLOCK = "BLOCK"
    ABSTAIN = "ABSTAIN"
    VETO = "VETO"  # Only Queen can issue this


# ═══════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class PillarVote:
    """A single pillar's vote with reasoning."""
    pillar: str
    vote: str             # PASS / BLOCK / ABSTAIN / VETO
    score: float          # Numeric confidence/health/vision score
    grade: str            # Human-readable grade
    reason: str           # Why this vote was cast
    data: Dict[str, Any] = field(default_factory=dict)  # Analytical data shared freely
    connected_systems: int = 0  # Number of systems reporting to this pillar


@dataclass
class TriumvirateConsensus:
    """The final consensus of the four pillars (Quadrumvirate)."""
    timestamp: float
    action: str                    # ConsensusAction value
    passed: bool                   # Did all 4 pillars agree?
    queen_vetoed: bool             # Did Queen exercise veto?
    active_controller: str         # Who has control right now
    alignment_score: float         # 0.0 to 1.0 how aligned the four are
    queen_vote: PillarVote = None
    king_vote: PillarVote = None
    seer_vote: PillarVote = None
    lyra_vote: PillarVote = None
    reason: str = ""               # Human-readable explanation
    data_exchange: Dict[str, Any] = field(default_factory=dict)  # Shared analytical data
    council_session: Any = None    # CouncilSession dialogue (if council convened)


@dataclass
class ControlHandoff:
    """Records when control shifts between pillars."""
    timestamp: float
    from_pillar: str
    to_pillar: str
    reason: str
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PillarSpeech:
    """What a pillar says during a council session."""
    pillar: str
    round_num: int       # 1=briefing, 2=reaction
    message: str         # Natural language speech
    key_insight: str     # Their unique piece of the puzzle (one line)
    data_shared: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0


@dataclass
class CouncilSession:
    """A complete Pillar Council dialogue — where the four minds talk."""
    session_id: int
    timestamp: float
    briefings: List[PillarSpeech] = field(default_factory=list)
    reactions: List[PillarSpeech] = field(default_factory=list)
    adjustments: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    transcript: str = ""
    consensus_impact: str = ""


# ═══════════════════════════════════════════════════════════════════════════
# PILLAR EVALUATORS - Each pillar votes independently
# ═══════════════════════════════════════════════════════════════════════════

class QueenEvaluator:
    """
    Evaluates the Queen's vote. The Queen has the most systems connected
    (11+ subsystems) and therefore holds ABSOLUTE VETO power.
    She evaluates: coherence, harmonic integrity, quantum signals,
    probability nexus validation, profit gates.
    """

    def evaluate(self, queen_confidence: float,
                 queen_data: Dict[str, Any] = None) -> PillarVote:
        """
        The Queen votes based on her trading cognition.

        Args:
            queen_confidence: 0.0-1.0 from Queen's perception systems
            queen_data: Additional data from Queen's 11+ subsystems

        Returns:
            PillarVote with PASS, BLOCK, or VETO
        """
        data = queen_data or {}

        # Extract subsystem data the Queen shares freely
        shared_data = {
            "coherence": data.get("coherence", queen_confidence),
            "harmonic_integrity": data.get("harmonic_integrity", 0.0),
            "quantum_omega": data.get("quantum_omega", 0.0),
            "lambda_stability": data.get("lambda_stability", 1.0),
            "probability_nexus": data.get("probability_nexus", 0.0),
            "profit_gate_active": data.get("profit_gate_active", True),
            "direction": data.get("direction", "NEUTRAL"),
            "decision_score": data.get("decision_score", 0.0),
            "emotional_state": data.get("emotional_state", "VIGILANT"),
            "subsystem_count": len(QUEEN_CONNECTED_SYSTEMS),
        }

        # Queen's vote logic
        if queen_confidence < QUEEN_VETO_THRESHOLD:
            return PillarVote(
                pillar="QUEEN",
                vote=VoteResult.VETO.value,
                score=queen_confidence,
                grade="SOVEREIGN_VETO",
                reason=f"Queen exercises VETO - confidence {queen_confidence:.2f} below {QUEEN_VETO_THRESHOLD}",
                data=shared_data,
                connected_systems=len(QUEEN_CONNECTED_SYSTEMS),
            )

        if queen_confidence < QUEEN_PASS_THRESHOLD:
            return PillarVote(
                pillar="QUEEN",
                vote=VoteResult.BLOCK.value,
                score=queen_confidence,
                grade="INSUFFICIENT",
                reason=f"Queen BLOCKS - confidence {queen_confidence:.2f} below threshold {QUEEN_PASS_THRESHOLD}",
                data=shared_data,
                connected_systems=len(QUEEN_CONNECTED_SYSTEMS),
            )

        # Check subsystem health if provided
        systems_online = data.get("systems_online", len(QUEEN_CONNECTED_SYSTEMS))
        systems_required = data.get("systems_required", 4)
        if systems_online < systems_required:
            return PillarVote(
                pillar="QUEEN",
                vote=VoteResult.BLOCK.value,
                score=queen_confidence,
                grade="SYSTEMS_DOWN",
                reason=f"Queen BLOCKS - only {systems_online}/{systems_required} required systems online",
                data=shared_data,
                connected_systems=systems_online,
            )

        # Grade the Queen's confidence
        if queen_confidence >= 0.85:
            grade = "SUPREME"
        elif queen_confidence >= 0.70:
            grade = "COMMANDING"
        elif queen_confidence >= 0.55:
            grade = "STEADY"
        else:
            grade = "CAUTIOUS"

        # ── Enigma new-listing nominations: Queen nominates newborns when she PASSES ──
        _q_universe = data.get("symbol_universe", {})
        _q_newborns = _q_universe.get("newborns", [])[:5]
        if _q_newborns:
            shared_data["nominated_snipes"] = [
                {"symbol": s, "nominator": "QUEEN", "score": queen_confidence}
                for s in _q_newborns
            ]

        return PillarVote(
            pillar="QUEEN",
            vote=VoteResult.PASS.value,
            score=queen_confidence,
            grade=grade,
            reason=f"Queen PASSES - confidence {queen_confidence:.2f}, grade {grade}",
            data=shared_data,
            connected_systems=len(QUEEN_CONNECTED_SYSTEMS),
        )


class KingEvaluator:
    """
    Evaluates the King's vote. The King sees financial truth -
    P&L, cost basis, portfolio health, tax implications.
    He shares all analytical data freely with Queen and Seer.
    """

    HEALTH_SCORES = {
        "SOVEREIGN": 0.90,
        "PROSPEROUS": 0.75,
        "STABLE": 0.55,
        "STRAINED": 0.35,
        "BANKRUPT": 0.10,
    }

    def evaluate(self, king_health: str,
                 king_data: Dict[str, Any] = None) -> PillarVote:
        """
        The King votes based on financial health.

        Args:
            king_health: SOVEREIGN/PROSPEROUS/STABLE/STRAINED/BANKRUPT
            king_data: Analytical data from King's 5 Royal Deciphers

        Returns:
            PillarVote with PASS or BLOCK
        """
        data = king_data or {}
        score = self.HEALTH_SCORES.get(king_health, 0.5)

        # King shares all analytical data freely
        shared_data = {
            "health_grade": king_health,
            "health_score": score,
            "total_realized_pnl": data.get("total_realized_pnl", 0.0),
            "unrealized_pnl": data.get("unrealized_pnl", 0.0),
            "win_rate": data.get("win_rate", 50.0),
            "drawdown_pct": data.get("drawdown_pct", 0.0),
            "max_drawdown_pct": data.get("max_drawdown_pct", 0.0),
            "total_fees": data.get("total_fees", 0.0),
            "equity": data.get("equity", 0.0),
            "cost_basis_available": data.get("cost_basis_available", False),
            "tax_liability": data.get("tax_liability", 0.0),
            "audit_alerts": data.get("audit_alerts", []),
        }

        # King's vote logic
        if king_health == "BANKRUPT":
            return PillarVote(
                pillar="KING",
                vote=VoteResult.BLOCK.value,
                score=score,
                grade="BANKRUPT",
                reason="King BLOCKS - treasury is BANKRUPT, all trading must halt",
                data=shared_data,
                connected_systems=5,  # 5 Royal Deciphers
            )

        if king_health == "STRAINED":
            return PillarVote(
                pillar="KING",
                vote=VoteResult.BLOCK.value,
                score=score,
                grade="STRAINED",
                reason="King BLOCKS - treasury is STRAINED, reduce exposure",
                data=shared_data,
                connected_systems=5,
            )

        # Check for critical audit alerts
        critical_alerts = [a for a in data.get("audit_alerts", [])
                          if isinstance(a, dict) and a.get("severity") == "CRITICAL"]
        if critical_alerts:
            return PillarVote(
                pillar="KING",
                vote=VoteResult.BLOCK.value,
                score=score,
                grade="AUDIT_CRITICAL",
                reason=f"King BLOCKS - {len(critical_alerts)} CRITICAL audit alert(s)",
                data=shared_data,
                connected_systems=5,
            )

        # ── Enigma nominations: King nominates if treasury is healthy enough to speculate ──
        _k_universe = data.get("symbol_universe", {})
        _k_newborns = _k_universe.get("newborns", [])[:3]  # King is more conservative: top 3
        if _k_newborns and king_health in ("SOVEREIGN", "PROSPEROUS"):
            shared_data["nominated_snipes"] = [
                {"symbol": s, "nominator": "KING", "score": score}
                for s in _k_newborns
            ]

        return PillarVote(
            pillar="KING",
            vote=VoteResult.PASS.value,
            score=score,
            grade=king_health,
            reason=f"King PASSES - treasury is {king_health} (score {score:.2f})",
            data=shared_data,
            connected_systems=5,
        )


class SeerEvaluator:
    """
    Evaluates the Seer's vote. The Seer reads cosmic coherence through
    5 Oracles. He shares all vision data freely with Queen and King.
    """

    GRADE_SCORES = {
        "DIVINE_CLARITY": 0.92,
        "CLEAR_SIGHT": 0.77,
        "PARTIAL_VISION": 0.60,
        "FOG": 0.42,
        "BLIND": 0.15,
    }

    def evaluate(self, seer_grade: str, seer_score: float = 0.5,
                 seer_data: Dict[str, Any] = None) -> PillarVote:
        """
        The Seer votes based on cosmic coherence vision.

        Args:
            seer_grade: DIVINE_CLARITY/CLEAR_SIGHT/PARTIAL_VISION/FOG/BLIND
            seer_score: 0.0-1.0 unified score from All-Seeing Eye
            seer_data: Vision data from 5 Oracles

        Returns:
            PillarVote with PASS or BLOCK
        """
        data = seer_data or {}
        score = seer_score if seer_score > 0 else self.GRADE_SCORES.get(seer_grade, 0.5)

        # Seer shares all oracle data freely
        shared_data = {
            "vision_grade": seer_grade,
            "unified_score": score,
            "risk_modifier": data.get("risk_modifier", 1.0),
            "action_bias": data.get("action", "HOLD"),
            "prophecy": data.get("prophecy", ""),
            "gaia_score": data.get("gaia_score", 0.5),
            "cosmos_score": data.get("cosmos_score", 0.5),
            "harmony_score": data.get("harmony_score", 0.5),
            "spirits_score": data.get("spirits_score", 0.5),
            "time_score": data.get("time_score", 0.5),
            "trend": data.get("trend", "STABLE"),
        }

        # Seer's vote logic
        if seer_grade == "BLIND":
            return PillarVote(
                pillar="SEER",
                vote=VoteResult.BLOCK.value,
                score=score,
                grade="BLIND",
                reason="Seer BLOCKS - vision is BLIND, no coherence detected",
                data=shared_data,
                connected_systems=5,  # 5 Oracles
            )

        if seer_grade == "FOG":
            return PillarVote(
                pillar="SEER",
                vote=VoteResult.BLOCK.value,
                score=score,
                grade="FOG",
                reason="Seer BLOCKS - FOG clouds vision, reduce exposure",
                data=shared_data,
                connected_systems=5,
            )

        # ── Enigma nominations: Seer reads cosmic timing for new listings ──
        _s_universe = data.get("symbol_universe", {})
        _s_newborns = _s_universe.get("newborns", [])[:4]
        if _s_newborns and seer_grade in ("DIVINE_CLARITY", "CLEAR_SIGHT"):
            shared_data["nominated_snipes"] = [
                {"symbol": s, "nominator": "SEER", "score": score}
                for s in _s_newborns
            ]

        return PillarVote(
            pillar="SEER",
            vote=VoteResult.PASS.value,
            score=score,
            grade=seer_grade,
            reason=f"Seer PASSES - vision is {seer_grade} (score {score:.2f})",
            data=shared_data,
            connected_systems=5,
        )


class LyraEvaluator:
    """
    Evaluates Lyra's vote. Lyra is the emotional frequency and harmonics
    engine with 6 Resonance Chambers and 22+ connected systems.
    She shares all harmonic and emotional data freely with all pillars.
    """

    GRADE_SCORES = {
        "DIVINE_HARMONY": 0.92,
        "CLEAR_RESONANCE": 0.77,
        "PARTIAL_HARMONY": 0.60,
        "DISSONANCE": 0.42,
        "SILENCE": 0.15,
    }

    def evaluate(self, lyra_grade: str, lyra_score: float = 0.5,
                 lyra_data: Dict[str, Any] = None) -> PillarVote:
        """
        Lyra votes based on emotional frequency and harmonic resonance.

        Args:
            lyra_grade: DIVINE_HARMONY/CLEAR_RESONANCE/PARTIAL_HARMONY/DISSONANCE/SILENCE
            lyra_score: 0.0-1.0 unified resonance score
            lyra_data: Data from 6 Resonance Chambers

        Returns:
            PillarVote with PASS or BLOCK
        """
        data = lyra_data or {}
        score = lyra_score if lyra_score > 0 else self.GRADE_SCORES.get(lyra_grade, 0.5)

        # Lyra shares all harmonic and emotional data freely
        shared_data = {
            "resonance_grade": lyra_grade,
            "unified_score": score,
            "emotional_frequency": data.get("emotional_frequency", 432.0),
            "emotional_zone": data.get("emotional_zone", "BALANCE"),
            "position_multiplier": data.get("position_multiplier", 1.0),
            "exit_urgency": data.get("exit_urgency", "none"),
            "action_bias": data.get("action", "HOLD"),
            "song": data.get("song", ""),
            "emotion_score": data.get("emotion_score", 0.5),
            "earth_score": data.get("earth_score", 0.5),
            "harmony_score": data.get("harmony_score", 0.5),
            "voice_score": data.get("voice_score", 0.5),
            "solfeggio_score": data.get("solfeggio_score", 0.5),
            "spirit_score": data.get("spirit_score", 0.5),
            "trend": data.get("trend", "STABLE"),
        }

        # Lyra's vote logic
        if lyra_grade == "SILENCE":
            return PillarVote(
                pillar="LYRA",
                vote=VoteResult.BLOCK.value,
                score=score,
                grade="SILENCE",
                reason="Lyra BLOCKS - SILENCE, no harmonic coherence detected",
                data=shared_data,
                connected_systems=len(LYRA_CONNECTED_SYSTEMS),
            )

        if lyra_grade == "DISSONANCE":
            return PillarVote(
                pillar="LYRA",
                vote=VoteResult.BLOCK.value,
                score=score,
                grade="DISSONANCE",
                reason="Lyra BLOCKS - DISSONANCE, frequencies clashing",
                data=shared_data,
                connected_systems=len(LYRA_CONNECTED_SYSTEMS),
            )

        # Check exit urgency - critical urgency blocks new entries
        if data.get("exit_urgency") == "critical":
            return PillarVote(
                pillar="LYRA",
                vote=VoteResult.BLOCK.value,
                score=score,
                grade="EXIT_CRITICAL",
                reason="Lyra BLOCKS - exit urgency is CRITICAL",
                data=shared_data,
                connected_systems=len(LYRA_CONNECTED_SYSTEMS),
            )

        # ── Enigma nominations: Lyra feels the harmonic excitement of new energy ──
        _l_universe = data.get("symbol_universe", {})
        _l_newborns = _l_universe.get("newborns", [])[:4]
        if _l_newborns and lyra_grade in ("DIVINE_HARMONY", "CLEAR_RESONANCE"):
            shared_data["nominated_snipes"] = [
                {"symbol": s, "nominator": "LYRA", "score": score}
                for s in _l_newborns
            ]

        return PillarVote(
            pillar="LYRA",
            vote=VoteResult.PASS.value,
            score=score,
            grade=lyra_grade,
            reason=f"Lyra PASSES - resonance is {lyra_grade} (score {score:.2f})",
            data=shared_data,
            connected_systems=len(LYRA_CONNECTED_SYSTEMS),
        )


# ═══════════════════════════════════════════════════════════════════════════
# CONTROL HANDOFF ENGINE
# ═══════════════════════════════════════════════════════════════════════════

class ControlHandoffEngine:
    """
    Determines which pillar should have active control based on the
    current context. Each pillar has domains where they lead.

    Queen leads: trade execution, entries, exits, position sizing
    King leads:  profit-taking, financial review, tax optimization
    Seer leads:  risk modulation, regime detection, cosmic events
    Lyra leads:  emotional regime changes, harmonic dissonance, exit urgency
    """

    def __init__(self):
        self._current_controller = PillarRole.QUEEN
        self._handoff_history: List[ControlHandoff] = []

    @property
    def current_controller(self) -> PillarRole:
        return self._current_controller

    def determine_controller(self, queen_vote: PillarVote,
                             king_vote: PillarVote,
                             seer_vote: PillarVote,
                             lyra_vote: PillarVote = None,
                             context: Dict[str, Any] = None) -> Tuple[PillarRole, Optional[ControlHandoff]]:
        """
        Determine which pillar should have active control.

        Returns:
            (new_controller, handoff_record_or_None)
        """
        ctx = context or {}
        previous = self._current_controller

        # RULE 1: Queen always has final authority - if she vetoes, she leads
        if queen_vote.vote == VoteResult.VETO.value:
            new = PillarRole.QUEEN
            reason = "Queen exercised VETO - assuming direct control"

        # RULE 2: King leads during financial distress
        elif king_vote.grade in ["BANKRUPT", "STRAINED", "AUDIT_CRITICAL"]:
            new = PillarRole.KING
            reason = f"King assumes control - financial status: {king_vote.grade}"

        # RULE 3: Seer leads during cosmic events / risk regime changes
        elif seer_vote.grade in ["BLIND", "FOG"]:
            new = PillarRole.SEER
            reason = f"Seer assumes control - vision: {seer_vote.grade}, managing risk"

        # RULE 4: Lyra leads during emotional crisis / harmonic dissonance
        elif lyra_vote and lyra_vote.grade in ["SILENCE", "DISSONANCE", "EXIT_CRITICAL"]:
            new = PillarRole.LYRA
            reason = f"Lyra assumes control - resonance: {lyra_vote.grade}, managing harmonics"

        # RULE 5: King leads for profit-taking decisions
        elif ctx.get("event") == "PROFIT_TAKING":
            new = PillarRole.KING
            reason = "King leads profit-taking decision"

        # RULE 6: Seer leads for risk modulation
        elif ctx.get("event") == "RISK_ADJUSTMENT":
            new = PillarRole.SEER
            reason = "Seer leads risk adjustment"

        # RULE 7: Lyra leads for emotional/harmonic events
        elif ctx.get("event") == "EMOTIONAL_SHIFT":
            new = PillarRole.LYRA
            reason = "Lyra leads emotional regime change"

        # RULE 8: Seer leads when cosmic vision has significant shift
        elif (seer_vote.data.get("trend") == "DECLINING" and
              seer_vote.score < 0.5):
            new = PillarRole.SEER
            reason = "Seer assumes control - declining cosmic alignment detected"

        # RULE 9: Lyra leads when emotional trend is dissonating
        elif (lyra_vote and lyra_vote.data.get("trend") == "DISSONATING" and
              lyra_vote.score < 0.5):
            new = PillarRole.LYRA
            reason = "Lyra assumes control - dissonating emotional trend detected"

        # DEFAULT: Queen leads (she has the most systems)
        else:
            new = PillarRole.QUEEN
            reason = "Queen leads - default trading authority"

        # Record handoff if controller changed
        handoff = None
        if new != previous:
            handoff = ControlHandoff(
                timestamp=time.time(),
                from_pillar=previous.value,
                to_pillar=new.value,
                reason=reason,
                context=ctx,
            )
            self._handoff_history.append(handoff)
            logger.info(f"CONTROL HANDOFF: {previous.value} -> {new.value}: {reason}")

        self._current_controller = new
        return new, handoff

    def get_handoff_history(self) -> List[ControlHandoff]:
        return list(self._handoff_history)


# ═══════════════════════════════════════════════════════════════════════════
# PILLAR COUNCIL - Where the Four Minds Speak, Listen, and React
# "Each has a different piece of the puzzle. They must talk."
# ═══════════════════════════════════════════════════════════════════════════

class PillarCouncil:
    """
    THE PILLAR COUNCIL
    ==================
    "Four minds, each with a different piece. They speak, listen,
     react, and find the truth together."

    Round 1 — BRIEFINGS:   Each pillar speaks what they see
    Round 2 — CROSS-TALK:  Each pillar reacts to the others' insights
    Output  — ADJUSTMENTS: Score modifications based on the dialogue

    The Council does NOT override votes (PASS/BLOCK stay unchanged).
    It adjusts confidence SCORES which affect consensus strength and
    action grading. This is how the pillars TALK to each other.
    """

    def __init__(self):
        self._session_count = 0
        self._sessions: List[CouncilSession] = []

    def convene(self, queen_vote: PillarVote, king_vote: PillarVote,
                seer_vote: PillarVote, lyra_vote: PillarVote) -> CouncilSession:
        """
        Convene a council session. All four pillars speak, listen, react.
        Returns a CouncilSession with the full dialogue and score adjustments.
        """
        self._session_count += 1
        now = time.time()

        # ── Round 1: Briefings — each pillar shares their piece ──
        queen_brief = self._queen_speaks(queen_vote, now)
        king_brief = self._king_speaks(king_vote, now)
        seer_brief = self._seer_speaks(seer_vote, now)
        lyra_brief = self._lyra_speaks(lyra_vote, now)
        briefings = [queen_brief, king_brief, seer_brief, lyra_brief]

        # ── Round 2: Cross-talk — each pillar reacts to the others ──
        queen_react, queen_adj = self._queen_reacts(queen_vote, king_brief, seer_brief, lyra_brief, now)
        king_react, king_adj = self._king_reacts(king_vote, queen_brief, seer_brief, lyra_brief, now)
        seer_react, seer_adj = self._seer_reacts(seer_vote, queen_brief, king_brief, lyra_brief, now)
        lyra_react, lyra_adj = self._lyra_reacts(lyra_vote, queen_brief, king_brief, seer_brief, now)
        reactions = [queen_react, king_react, seer_react, lyra_react]

        adjustments = {
            "queen": queen_adj,
            "king": king_adj,
            "seer": seer_adj,
            "lyra": lyra_adj,
        }

        # ── Build transcript ──
        transcript = self._build_transcript(
            self._session_count, now, briefings, reactions, adjustments
        )

        # ── Determine consensus impact ──
        total_delta = sum(abs(a.get("delta", 0)) for a in adjustments.values())
        if total_delta < 0.02:
            impact = "Minimal — pillars are well-aligned, no significant adjustments"
        elif total_delta < 0.10:
            impact = "Moderate — cross-pillar dialogue refined the picture"
        else:
            impact = "Significant — pillar reactions materially shifted confidence"

        session = CouncilSession(
            session_id=self._session_count,
            timestamp=now,
            briefings=briefings,
            reactions=reactions,
            adjustments=adjustments,
            transcript=transcript,
            consensus_impact=impact,
        )

        self._sessions.append(session)
        # Keep last 50 sessions
        if len(self._sessions) > 50:
            self._sessions = self._sessions[-50:]

        return session

    # ── Queen Speaks: Trading Cognition ──
    def _queen_speaks(self, vote: PillarVote, ts: float) -> PillarSpeech:
        d = vote.data
        confidence = vote.score
        direction = d.get("direction", "NEUTRAL")
        harmonic = d.get("harmonic_integrity", 0)
        nexus = d.get("probability_nexus", 0)
        systems = vote.connected_systems
        emotion = d.get("emotional_state", "VIGILANT")

        msg = (
            f"I see {direction} momentum with {confidence:.0%} confidence. "
            f"The probability nexus reads {nexus:.2f}. "
            f"My {systems} systems report {vote.grade}. "
            f"Harmonic integrity: {harmonic:.2f}. Emotional state: {emotion}. "
            f"I vote {vote.vote}."
        )

        insight = f"Trading cognition: {direction} at {confidence:.0%} confidence"

        return PillarSpeech(
            pillar="QUEEN", round_num=1, message=msg,
            key_insight=insight, data_shared=d, timestamp=ts
        )

    # ── King Speaks: Financial Truth ──
    def _king_speaks(self, vote: PillarVote, ts: float) -> PillarSpeech:
        d = vote.data
        health = d.get("health_grade", vote.grade)
        pnl = d.get("total_realized_pnl", 0)
        wr = d.get("win_rate", 50)
        fees = d.get("total_fees", 0)
        equity = d.get("equity", 0)
        cb = d.get("cost_basis_available", False)
        tax = d.get("tax_liability", 0)
        drawdown = d.get("drawdown_pct", 0)

        msg = (
            f"The treasury is {health}. "
            f"We've realized ${pnl:.2f} profit with a {wr:.1f}% win rate. "
            f"Total fees paid: ${fees:.2f}. Portfolio equity: ${equity:.2f}. "
            f"Drawdown: {drawdown:.1f}%. "
            f"{'Cost basis tracked across all positions' if cb else 'Cost basis incomplete'}. "
            f"Tax liability: ${tax:.2f}. I vote {vote.vote}."
        )

        insight = f"Financial truth: {health}, P&L ${pnl:.2f}, win rate {wr:.1f}%"

        return PillarSpeech(
            pillar="KING", round_num=1, message=msg,
            key_insight=insight, data_shared=d, timestamp=ts
        )

    # ── Seer Speaks: Cosmic Coherence ──
    def _seer_speaks(self, vote: PillarVote, ts: float) -> PillarSpeech:
        d = vote.data
        grade = d.get("vision_grade", vote.grade)
        score = vote.score
        gaia = d.get("gaia_score", 0.5)
        cosmos = d.get("cosmos_score", 0.5)
        harmony = d.get("harmony_score", 0.5)
        risk_mod = d.get("risk_modifier", 1.0)
        trend = d.get("trend", "STABLE")
        prophecy = d.get("prophecy", "")

        msg = (
            f"My vision is {grade} — unified score {score:.2f}. "
            f"Gaia reads {gaia:.2f}, the Cosmos {cosmos:.2f}, Harmony {harmony:.2f}. "
            f"The trend is {trend}. Risk modifier: {risk_mod:.1f}x. "
            f"{'Prophecy: ' + prophecy + '. ' if prophecy else ''}"
            f"I vote {vote.vote}."
        )

        insight = f"Cosmic coherence: {grade}, trend {trend}, risk {risk_mod:.1f}x"

        return PillarSpeech(
            pillar="SEER", round_num=1, message=msg,
            key_insight=insight, data_shared=d, timestamp=ts
        )

    # ── Lyra Speaks: Emotional Frequency ──
    def _lyra_speaks(self, vote: PillarVote, ts: float) -> PillarSpeech:
        d = vote.data
        grade = d.get("resonance_grade", vote.grade)
        freq = d.get("emotional_frequency", 432.0)
        zone = d.get("emotional_zone", "BALANCE")
        urgency = d.get("exit_urgency", "none")
        pos_mul = d.get("position_multiplier", 1.0)
        trend = d.get("trend", "STABLE")
        song = d.get("song", "")

        msg = (
            f"I feel {zone} with frequency {freq:.1f} Hz. "
            f"The harmonic resonance is {grade}. "
            f"Exit urgency: {urgency}. Position multiplier: {pos_mul:.2f}x. "
            f"My {vote.connected_systems} systems feel {trend}. "
            f"{'Song: ' + song + '. ' if song else ''}"
            f"I vote {vote.vote}."
        )

        insight = f"Emotional frequency: {zone} at {freq:.1f} Hz, resonance {grade}"

        return PillarSpeech(
            pillar="LYRA", round_num=1, message=msg,
            key_insight=insight, data_shared=d, timestamp=ts
        )

    # ── Cross-Talk: Queen Reacts ──
    def _queen_reacts(self, queen_vote, king_speech, seer_speech, lyra_speech, ts):
        delta = 0.0
        reactions = []

        # React to King's financial data
        king_d = king_speech.data_shared
        wr = king_d.get("win_rate", 50)
        pnl = king_d.get("total_realized_pnl", 0)

        if wr < 25:
            delta -= 0.05
            reactions.append(f"King's low win rate ({wr:.1f}%) concerns me — too many small losses")
        elif wr > 60:
            delta += 0.03
            reactions.append(f"King reports strong win rate ({wr:.1f}%) — confidence reinforced")

        if pnl < -20:
            delta -= 0.05
            reactions.append(f"King's negative P&L (${pnl:.2f}) warrants caution")
        elif pnl > 50:
            delta += 0.02
            reactions.append(f"King's positive P&L (${pnl:.2f}) supports continued trading")

        # React to Seer's cosmic data
        seer_d = seer_speech.data_shared
        seer_grade = seer_d.get("vision_grade", "PARTIAL_VISION")
        if seer_grade in ("BLIND", "FOG"):
            delta -= 0.05
            reactions.append(f"Seer's {seer_grade} vision clouds my confidence")
        elif seer_grade == "DIVINE_CLARITY":
            delta += 0.03
            reactions.append("Seer's divine clarity aligns with my pattern recognition")

        # React to Lyra's emotional data
        lyra_d = lyra_speech.data_shared
        urgency = lyra_d.get("exit_urgency", "none")
        if urgency in ("critical", "high"):
            delta -= 0.05
            reactions.append(f"Lyra's exit urgency ({urgency}) demands I reconsider")
        zone = lyra_d.get("emotional_zone", "BALANCE")
        if zone == "FEAR":
            delta -= 0.03
            reactions.append("Lyra detects FEAR in the emotional field — I temper my optimism")
        elif zone == "EUPHORIA":
            delta -= 0.02
            reactions.append("Lyra detects EUPHORIA — beware of overleveraging")

        # React to QGITA structural events (from Seer's data)
        seer_qgita_regime = seer_d.get("qgita_regime", "")
        seer_qgita_conf = seer_d.get("qgita_confidence", 0.5)
        if seer_qgita_regime == "coherent" and seer_qgita_conf > 0.65:
            delta += 0.04
            reactions.append(
                f"The Seer's QGITA reads COHERENT regime ({seer_qgita_conf:.0%}) — "
                "the Fibonacci lattice confirms my pattern recognition"
            )
        elif seer_qgita_regime == "chaotic":
            delta -= 0.04
            reactions.append(
                "The Seer's QGITA warns of CHAOTIC regime — "
                "structural noise clouds my signals"
            )

        # React to Lighthouse spectral signal (from Lyra's data)
        lh_coherence = lyra_d.get("lighthouse_coherence_score", 0)
        lh_distortion = lyra_d.get("lighthouse_distortion_index", 0)
        if lh_coherence > 0.6 and lh_distortion < 0.3:
            delta += 0.03
            reactions.append(
                f"Lyra's Lighthouse shows clean spectrum (coherence {lh_coherence:.2f}, "
                f"distortion {lh_distortion:.2f}) — my signals are riding a clear wave"
            )
        elif lh_distortion > 0.6:
            delta -= 0.04
            reactions.append(
                f"Lyra's Lighthouse shows high distortion ({lh_distortion:.2f}) — "
                "the price signal is contaminated, I reduce confidence"
            )

        # Clamp delta
        delta = max(-0.15, min(0.15, delta))

        if not reactions:
            reactions.append("All pillars present a coherent picture. I hold my position")

        msg = (
            " ".join(reactions) +
            f" [Confidence: {queen_vote.score:.2f} -> {queen_vote.score + delta:.2f} ({delta:+.2f})]"
        )

        adj = {
            "original_score": queen_vote.score,
            "adjusted_score": queen_vote.score + delta,
            "delta": delta,
            "reason": "; ".join(reactions),
        }

        speech = PillarSpeech(
            pillar="QUEEN", round_num=2, message=msg,
            key_insight=f"Confidence adjusted by {delta:+.2f}",
            data_shared={"delta": delta}, timestamp=ts
        )

        return speech, adj

    # ── Cross-Talk: King Reacts ──
    def _king_reacts(self, king_vote, queen_speech, seer_speech, lyra_speech, ts):
        delta = 0.0
        reactions = []

        # React to Queen's confidence
        queen_d = queen_speech.data_shared
        qconf = queen_d.get("coherence", 0.5)
        direction = queen_d.get("direction", "NEUTRAL")

        if qconf >= 0.75:
            delta += 0.03
            reactions.append(
                f"Queen's {qconf:.0%} confidence is strong — "
                f"the portfolio can support {direction} entries"
            )
        elif qconf < 0.35:
            delta -= 0.03
            reactions.append(f"Queen's low confidence ({qconf:.0%}) suggests reducing exposure")

        # React to Seer's risk modifier
        seer_d = seer_speech.data_shared
        risk_mod = seer_d.get("risk_modifier", 1.0)
        if risk_mod > 1.2:
            delta += 0.02
            reactions.append(f"Seer's risk modifier ({risk_mod:.1f}x) allows larger allocations")
        elif risk_mod < 0.7:
            delta -= 0.03
            reactions.append(f"Seer's risk modifier ({risk_mod:.1f}x) demands conservative sizing")

        # React to Lyra's emotional zone
        lyra_d = lyra_speech.data_shared
        urgency = lyra_d.get("exit_urgency", "none")
        zone = lyra_d.get("emotional_zone", "BALANCE")

        if urgency in ("critical", "high"):
            delta -= 0.05
            reactions.append(f"Lyra signals {urgency} exit urgency — treasury prepares for drawdown")
        elif zone == "CALM":
            delta += 0.01
            reactions.append("Lyra's calm emotional field suggests stable market conditions")

        # React to QGITA structural risk (from Seer's data)
        seer_d = seer_speech.data_shared
        qgita_risk = seer_d.get("qgita_risk_level", "")
        qgita_lh_intensity = seer_d.get("qgita_lighthouse_intensity", 0)
        if qgita_risk == "HIGH":
            delta -= 0.05
            reactions.append(
                f"Seer's QGITA flags HIGH risk regime — "
                "the treasury tightens position limits"
            )
        elif qgita_risk == "LOW" and qgita_lh_intensity > 0.5:
            delta += 0.03
            reactions.append(
                f"Seer's QGITA reads LOW risk with strong Lighthouse ({qgita_lh_intensity:.2f}) — "
                "the treasury can extend allocations"
            )

        # React to Lighthouse maker bias (profit tendency)
        lh_maker_bias = lyra_d.get("lighthouse_maker_bias", 0.5)
        if lh_maker_bias > 0.6:
            delta += 0.02
            reactions.append(
                f"Lyra's Lighthouse shows positive maker bias ({lh_maker_bias:.2f}) — "
                "capital flows favor profitability"
            )
        elif lh_maker_bias < 0.35:
            delta -= 0.03
            reactions.append(
                f"Lyra's Lighthouse shows negative maker bias ({lh_maker_bias:.2f}) — "
                "capital flows work against us"
            )

        delta = max(-0.15, min(0.15, delta))

        if not reactions:
            reactions.append("Treasury remains open for business — all signals nominal")

        msg = (
            " ".join(reactions) +
            f" [Health score: {king_vote.score:.2f} -> {king_vote.score + delta:.2f} ({delta:+.2f})]"
        )

        adj = {
            "original_score": king_vote.score,
            "adjusted_score": king_vote.score + delta,
            "delta": delta,
            "reason": "; ".join(reactions),
        }

        speech = PillarSpeech(
            pillar="KING", round_num=2, message=msg,
            key_insight=f"Health score adjusted by {delta:+.2f}",
            data_shared={"delta": delta}, timestamp=ts
        )

        return speech, adj

    # ── Cross-Talk: Seer Reacts ──
    def _seer_reacts(self, seer_vote, queen_speech, king_speech, lyra_speech, ts):
        delta = 0.0
        reactions = []

        # React to Queen's direction and confidence
        queen_d = queen_speech.data_shared
        qconf = queen_d.get("coherence", 0.5)

        if qconf >= 0.70:
            delta += 0.02
            reactions.append(f"Queen's cognition ({qconf:.0%}) aligns with my cosmic reading")
        elif qconf < 0.30:
            delta -= 0.02
            reactions.append(f"Queen's uncertainty ({qconf:.0%}) creates dissonance with my vision")

        # React to King's financial health
        king_d = king_speech.data_shared
        pnl = king_d.get("total_realized_pnl", 0)
        drawdown = king_d.get("drawdown_pct", 0)
        health = king_d.get("health_grade", "STABLE")

        if health in ("BANKRUPT", "STRAINED"):
            delta -= 0.05
            reactions.append(f"King's {health} treasury warns of material instability")
        elif pnl > 0:
            delta += 0.01
            reactions.append(f"King's positive P&L (${pnl:.2f}) reinforces cosmic stability")

        if drawdown > 15:
            delta -= 0.03
            reactions.append(f"King reports {drawdown:.1f}% drawdown — the stars warn of deeper loss")

        # React to Lyra's harmonic data
        lyra_d = lyra_speech.data_shared
        harmony = lyra_d.get("harmony_score", 0.5)
        freq = lyra_d.get("emotional_frequency", 432)

        if harmony > 0.7:
            delta += 0.02
            reactions.append(f"Lyra's harmonic resonance ({harmony:.2f}) resonates with my cosmic field")
        elif harmony < 0.3:
            delta -= 0.02
            reactions.append(f"Lyra's harmonic dissonance ({harmony:.2f}) contradicts my orbital readings")

        # Schumann resonance alignment check
        if abs(freq - 7.83) < 2:
            delta += 0.01
            reactions.append(f"Lyra's frequency ({freq:.1f} Hz) near Schumann resonance — Earth-aligned")

        # React to QGITA regime state (from Queen's data if available)
        queen_d = queen_speech.data_shared
        qgita_dir = queen_d.get("qgita_direction", "")
        qgita_regime = queen_d.get("qgita_regime", "")
        if qgita_regime == "coherent" and qgita_dir in ("BULLISH", "BEARISH"):
            delta += 0.03
            reactions.append(
                f"Queen's QGITA confirms {qgita_regime} regime with {qgita_dir} direction — "
                "my cosmic reading gains geometric validation"
            )
        elif qgita_regime == "chaotic":
            delta -= 0.03
            reactions.append(
                "Queen's QGITA signals CHAOTIC regime — "
                "my cosmic timeline may be unreliable in turbulent geometry"
            )

        # React to Lighthouse structural events
        qgita_structural = queen_d.get("qgita_structural_event", False)
        if qgita_structural:
            delta += 0.04
            reactions.append(
                "QGITA STRUCTURAL EVENT DETECTED — "
                "the Fibonacci lattice confirms a temporal inflection point!"
            )

        delta = max(-0.15, min(0.15, delta))

        if not reactions:
            reactions.append("The cosmos agrees with this moment — all pillars in harmony")

        msg = (
            " ".join(reactions) +
            f" [Vision score: {seer_vote.score:.2f} -> {seer_vote.score + delta:.2f} ({delta:+.2f})]"
        )

        adj = {
            "original_score": seer_vote.score,
            "adjusted_score": seer_vote.score + delta,
            "delta": delta,
            "reason": "; ".join(reactions),
        }

        speech = PillarSpeech(
            pillar="SEER", round_num=2, message=msg,
            key_insight=f"Vision score adjusted by {delta:+.2f}",
            data_shared={"delta": delta}, timestamp=ts
        )

        return speech, adj

    # ── Cross-Talk: Lyra Reacts ──
    def _lyra_reacts(self, lyra_vote, queen_speech, king_speech, seer_speech, ts):
        delta = 0.0
        reactions = []

        # React to Seer's cosmic data
        seer_d = seer_speech.data_shared
        seer_grade = seer_d.get("vision_grade", "PARTIAL_VISION")
        cosmos = seer_d.get("cosmos_score", 0.5)

        if seer_grade in ("DIVINE_CLARITY", "CLEAR_SIGHT"):
            delta += 0.02
            reactions.append(f"Seer's {seer_grade} vision harmonizes with my frequency field")
        elif seer_grade in ("BLIND", "FOG"):
            delta -= 0.03
            reactions.append(f"Seer's {seer_grade} vision creates static in my harmonic field")

        if cosmos > 0.7:
            delta += 0.01
            reactions.append(f"Seer's cosmic score ({cosmos:.2f}) resonates with my emotional reading")

        # React to King's P&L (losses create fear vibration, gains create calm)
        king_d = king_speech.data_shared
        pnl = king_d.get("total_realized_pnl", 0)
        wr = king_d.get("win_rate", 50)

        if pnl < -30:
            delta -= 0.04
            reactions.append(f"King's losses (${pnl:.2f}) amplify fear frequency in the field")
        elif pnl > 30:
            delta += 0.02
            reactions.append(f"King's profits (${pnl:.2f}) generate calm financial vibration")

        if wr < 20:
            delta -= 0.02
            reactions.append(f"King's low win rate ({wr:.1f}%) creates anxiety undertones")
        elif wr > 60:
            delta += 0.01
            reactions.append(f"King's win rate ({wr:.1f}%) adds confidence to the harmonic field")

        # React to Queen's emotional state
        queen_d = queen_speech.data_shared
        q_emotion = queen_d.get("emotional_state", "VIGILANT")
        qconf = queen_d.get("coherence", 0.5)

        if q_emotion in ("AGGRESSIVE", "EUPHORIC"):
            delta -= 0.02
            reactions.append(f"Queen's {q_emotion} state creates harmonic tension — I temper the melody")
        elif q_emotion in ("CAUTIOUS", "FEARFUL"):
            delta -= 0.01
            reactions.append(f"Queen's {q_emotion} state adds minor dissonance")
        elif qconf > 0.75:
            delta += 0.01
            reactions.append("Queen's strong confidence adds energy to my resonance field")

        # React to QGITA structural event (from Seer or Queen data)
        seer_d = seer_speech.data_shared
        qgita_structural = queen_d.get("qgita_structural_event", False)
        qgita_confidence = seer_d.get("qgita_confidence", 0.5)
        if qgita_structural and qgita_confidence > 0.6:
            delta += 0.04
            reactions.append(
                f"QGITA structural event with {qgita_confidence:.0%} confidence — "
                "my harmonic field amplifies at the temporal inflection point"
            )

        # React to own Lighthouse spectral data (self-awareness)
        lh_emotion = lyra_vote.data.get("lighthouse_emotion", "")
        lh_coherence = lyra_vote.data.get("lighthouse_coherence_score", 0)
        if lh_emotion in ("AWE (Resonant)", "LOVE (528Hz)") and lh_coherence > 0.5:
            delta += 0.03
            reactions.append(
                f"My Lighthouse reads {lh_emotion} — the spectral harmony "
                "validates my emotional reading"
            )
        elif lh_emotion == "ANGER (Chaotic)":
            delta -= 0.04
            reactions.append(
                "My Lighthouse reads ANGER (Chaotic) — the spectral analysis "
                "contradicts my emotional state, I reduce resonance"
            )

        delta = max(-0.15, min(0.15, delta))

        if not reactions:
            reactions.append("The emotional field is clear — all pillars contribute to harmony")

        msg = (
            " ".join(reactions) +
            f" [Resonance: {lyra_vote.score:.2f} -> {lyra_vote.score + delta:.2f} ({delta:+.2f})]"
        )

        adj = {
            "original_score": lyra_vote.score,
            "adjusted_score": lyra_vote.score + delta,
            "delta": delta,
            "reason": "; ".join(reactions),
        }

        speech = PillarSpeech(
            pillar="LYRA", round_num=2, message=msg,
            key_insight=f"Resonance adjusted by {delta:+.2f}",
            data_shared={"delta": delta}, timestamp=ts
        )

        return speech, adj

    # ── Build the Council Transcript ──
    def _build_transcript(self, session_id, timestamp, briefings, reactions, adjustments):
        """Build a human-readable council transcript."""
        from datetime import datetime as _dt, timezone as _tz
        dt = _dt.fromtimestamp(timestamp, tz=_tz.utc)

        lines = [
            "",
            "=" * 60,
            f"  PILLAR COUNCIL SESSION #{session_id}",
            f"  {dt.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "=" * 60,
            "",
            "-- ROUND 1: BRIEFINGS (Each pillar shares their piece) --",
            "",
        ]

        icons = {"QUEEN": "QUEEN", "KING": "KING", "SEER": "SEER", "LYRA": "LYRA"}

        for b in briefings:
            lines.append(f"  [{icons.get(b.pillar, b.pillar)}] speaks:")
            lines.append(f'   "{b.message}"')
            lines.append(f"   >> Puzzle piece: {b.key_insight}")
            lines.append("")

        lines.append("-- ROUND 2: CROSS-TALK (Each pillar reacts) --")
        lines.append("")

        for r in reactions:
            lines.append(f"  [{icons.get(r.pillar, r.pillar)}] responds:")
            lines.append(f'   "{r.message}"')
            lines.append("")

        lines.append("-- ADJUSTMENTS --")
        lines.append("")
        for pillar, adj in adjustments.items():
            delta = adj.get("delta", 0)
            if abs(delta) > 0.001:
                lines.append(
                    f"  {pillar.upper()}: "
                    f"{adj['original_score']:.3f} -> {adj['adjusted_score']:.3f} "
                    f"({delta:+.3f})"
                )
                lines.append(f"    Reason: {adj['reason']}")
            else:
                lines.append(f"  {pillar.upper()}: No adjustment needed")
        lines.append("")

        lines.append("-- COUNCIL CONCLUSION --")

        total_delta = sum(abs(adjustments[p].get("delta", 0)) for p in adjustments)
        if total_delta < 0.02:
            lines.append("  The four pieces of the puzzle fit together cleanly.")
            lines.append("  Minimal adjustments — the pillars are well-aligned.")
        elif total_delta < 0.10:
            lines.append("  The dialogue refined the picture.")
            lines.append("  Moderate adjustments — cross-pillar insights added clarity.")
        else:
            lines.append("  Significant dialogue shifted the picture.")
            lines.append("  The pillars revealed tensions that changed the outcome.")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)

    def get_latest_session(self) -> Optional[CouncilSession]:
        """Get the most recent council session."""
        return self._sessions[-1] if self._sessions else None

    def get_session_count(self) -> int:
        """How many council sessions have been held."""
        return self._session_count


def _agg_nominated_snipes(*votes) -> list:
    """
    Aggregate Enigma newborn snipe nominations from N PillarVote objects.
    Returns a deduplicated list sorted by number of nominators (most agreed-upon first).
    Called internally by TriumvirateEngine._exchange_data().
    """
    all_nominations: Dict[str, Dict] = {}
    for vote in votes:
        for nom in (vote.data.get("nominated_snipes") or []):
            sym = nom.get("symbol", "")
            if not sym:
                continue
            if sym not in all_nominations:
                all_nominations[sym] = {"symbol": sym, "nominators": [], "score_sum": 0.0}
            nominator = nom.get("nominator", "?")
            if nominator not in all_nominations[sym]["nominators"]:
                all_nominations[sym]["nominators"].append(nominator)
            all_nominations[sym]["score_sum"] += nom.get("score", 0.5)
    return sorted(
        all_nominations.values(),
        key=lambda x: (len(x["nominators"]), x["score_sum"]),
        reverse=True,
    )


# ═══════════════════════════════════════════════════════════════════════════
# THE TRIUMVIRATE ENGINE - Three-Way Freeway Consensus
# ═══════════════════════════════════════════════════════════════════════════

class TriumvirateEngine:
    """
    The Quadrumvirate Engine enforces freeway consensus:
    ALL FOUR pillars must independently vote PASS for any action.
    The Queen holds absolute veto (most systems connected = 11+).

    FREEWAY RULES:
      Lane 1 (Queen): Must PASS with confidence >= 0.45
      Lane 2 (King):  Must PASS with health in [SOVEREIGN, PROSPEROUS, STABLE]
      Lane 3 (Seer):  Must PASS with vision in [DIVINE_CLARITY, CLEAR_SIGHT, PARTIAL_VISION]
      Lane 4 (Lyra):  Must PASS with resonance in [DIVINE_HARMONY, CLEAR_RESONANCE, PARTIAL_HARMONY]

      ALL FOUR LANES MUST BE CLEAR.
      Queen can VETO at any time (overrides all other votes).
    """

    def __init__(self):
        self.queen_eval = QueenEvaluator()
        self.king_eval = KingEvaluator()
        self.seer_eval = SeerEvaluator()
        self.lyra_eval = LyraEvaluator()
        self.handoff_engine = ControlHandoffEngine()
        self.council = PillarCouncil()
        self._consensus_history: List[TriumvirateConsensus] = []

    def evaluate_consensus(self,
                           queen_confidence: float,
                           king_health: str,
                           seer_grade: str,
                           seer_score: float = 0.5,
                           lyra_grade: str = "PARTIAL_HARMONY",
                           lyra_score: float = 0.5,
                           queen_data: Dict[str, Any] = None,
                           king_data: Dict[str, Any] = None,
                           seer_data: Dict[str, Any] = None,
                           lyra_data: Dict[str, Any] = None,
                           context: Dict[str, Any] = None) -> TriumvirateConsensus:
        """
        Run full freeway consensus evaluation.

        All FOUR pillars vote independently. All must PASS for consensus.
        Queen has absolute veto regardless of other votes.

        Args:
            queen_confidence: 0.0-1.0 from Queen's cognition systems
            king_health: SOVEREIGN/PROSPEROUS/STABLE/STRAINED/BANKRUPT
            seer_grade: DIVINE_CLARITY/CLEAR_SIGHT/PARTIAL_VISION/FOG/BLIND
            seer_score: 0.0-1.0 unified vision score
            lyra_grade: DIVINE_HARMONY/CLEAR_RESONANCE/PARTIAL_HARMONY/DISSONANCE/SILENCE
            lyra_score: 0.0-1.0 unified resonance score
            queen_data: Queen's subsystem data (shared freely)
            king_data: King's analytical data (shared freely)
            seer_data: Seer's oracle data (shared freely)
            lyra_data: Lyra's harmonic/emotional data (shared freely)
            context: Additional context for control handoff

        Returns:
            TriumvirateConsensus with final action and all vote details
        """
        # ─── Phase 1: Each pillar votes independently ───
        queen_vote = self.queen_eval.evaluate(queen_confidence, queen_data)
        king_vote = self.king_eval.evaluate(king_health, king_data)
        seer_vote = self.seer_eval.evaluate(seer_grade, seer_score, seer_data)
        lyra_vote = self.lyra_eval.evaluate(lyra_grade, lyra_score, lyra_data)

        # ─── Phase 2: Free data exchange between all pillars ───
        data_exchange = self._exchange_data(queen_vote, king_vote, seer_vote, lyra_vote)

        # ─── Phase 2.5: PILLAR COUNCIL — the four minds speak and react ───
        council_session = self.council.convene(queen_vote, king_vote, seer_vote, lyra_vote)
        # Apply council score adjustments (votes PASS/BLOCK stay, only scores shift)
        for pillar_name, vote in [("queen", queen_vote), ("king", king_vote),
                                   ("seer", seer_vote), ("lyra", lyra_vote)]:
            adj = council_session.adjustments.get(pillar_name, {})
            adj_delta = adj.get("delta", 0)
            if abs(adj_delta) > 0.001:
                vote.score = max(0.0, min(1.0, vote.score + adj_delta))
        logger.info(
            "PILLAR COUNCIL #%d: %s",
            council_session.session_id, council_session.consensus_impact
        )

        # ─── Phase 3: Determine active controller ───
        active_controller, handoff = self.handoff_engine.determine_controller(
            queen_vote, king_vote, seer_vote, lyra_vote, context
        )

        # ─── Phase 4: Apply freeway consensus rules ───
        queen_vetoed = queen_vote.vote == VoteResult.VETO.value
        all_passed = (
            queen_vote.vote == VoteResult.PASS.value and
            king_vote.vote == VoteResult.PASS.value and
            seer_vote.vote == VoteResult.PASS.value and
            lyra_vote.vote == VoteResult.PASS.value
        )

        # Calculate alignment score (how closely the four agree)
        alignment = self._calculate_alignment(queen_vote, king_vote, seer_vote, lyra_vote)

        # Determine final action
        action, reason = self._determine_action(
            queen_vote, king_vote, seer_vote, lyra_vote,
            all_passed, queen_vetoed, alignment,
            active_controller
        )

        consensus = TriumvirateConsensus(
            timestamp=time.time(),
            action=action,
            passed=all_passed,
            queen_vetoed=queen_vetoed,
            active_controller=active_controller.value,
            alignment_score=alignment,
            queen_vote=queen_vote,
            king_vote=king_vote,
            seer_vote=seer_vote,
            lyra_vote=lyra_vote,
            reason=reason,
            data_exchange=data_exchange,
            council_session=council_session,
        )

        self._consensus_history.append(consensus)
        return consensus

    def _exchange_data(self, queen_vote: PillarVote,
                       king_vote: PillarVote,
                       seer_vote: PillarVote,
                       lyra_vote: PillarVote) -> Dict[str, Any]:
        """
        Free data exchange - all analytical data flows between all 4 pillars.
        King, Seer, and Lyra need analytical data pulled free.
        """
        return {
            "queen_shares": queen_vote.data,
            "king_shares": king_vote.data,
            "seer_shares": seer_vote.data,
            "lyra_shares": lyra_vote.data,
            "queen_systems_count": queen_vote.connected_systems,
            "king_systems_count": king_vote.connected_systems,
            "seer_systems_count": seer_vote.connected_systems,
            "lyra_systems_count": lyra_vote.connected_systems,
            "total_systems": (
                queen_vote.connected_systems +
                king_vote.connected_systems +
                seer_vote.connected_systems +
                lyra_vote.connected_systems
            ),
            # ── Aggregated Pillar snipe nominations ──────────────────────────────────
            # Symbols that multiple Pillars all want to snipe rise to the top.
            "nominated_snipes": _agg_nominated_snipes(
                queen_vote, king_vote, seer_vote, lyra_vote
            ),
        }

    def _calculate_alignment(self, queen: PillarVote, king: PillarVote,
                             seer: PillarVote, lyra: PillarVote) -> float:
        """Calculate how aligned the four pillars are (0.0 to 1.0)."""
        scores = [queen.score, king.score, seer.score, lyra.score]
        avg = sum(scores) / 4.0
        # Variance-based alignment - low variance = high alignment
        variance = sum((s - avg) ** 2 for s in scores) / 4.0
        # Max possible variance is when one is 0 and others are 1: ~0.1875
        alignment = max(0.0, 1.0 - (variance / 0.25))
        return round(alignment, 3)

    def _determine_action(self, queen: PillarVote, king: PillarVote,
                          seer: PillarVote, lyra: PillarVote,
                          all_passed: bool,
                          queen_vetoed: bool, alignment: float,
                          controller: PillarRole) -> Tuple[str, str]:
        """
        Determine the final consensus action.

        FREEWAY RULE: All four must pass. Queen has absolute veto.
        """
        # ─── Queen VETO overrides everything ───
        if queen_vetoed:
            return ConsensusAction.HALT.value, (
                f"QUEEN VETO - {queen.reason}. "
                f"Queen has {queen.connected_systems} systems and absolute authority."
            )

        # ─── King BANKRUPT halts everything ───
        if king.grade == "BANKRUPT":
            return ConsensusAction.HALT.value, (
                f"KING HALT - Treasury is BANKRUPT. {king.reason}"
            )

        # ─── Freeway consensus: all must pass ───
        if not all_passed:
            # Identify which lanes are blocked
            blockers = []
            if queen.vote != VoteResult.PASS.value:
                blockers.append(f"Queen ({queen.grade})")
            if king.vote != VoteResult.PASS.value:
                blockers.append(f"King ({king.grade})")
            if seer.vote != VoteResult.PASS.value:
                blockers.append(f"Seer ({seer.grade})")
            if lyra.vote != VoteResult.PASS.value:
                blockers.append(f"Lyra ({lyra.grade})")

            # Action depends on severity of the blocker
            if king.grade == "STRAINED":
                return ConsensusAction.SELL.value, (
                    f"FREEWAY BLOCKED by {', '.join(blockers)}. "
                    f"King is STRAINED - reducing exposure."
                )
            if seer.grade == "BLIND":
                return ConsensusAction.HALT.value, (
                    f"FREEWAY BLOCKED by {', '.join(blockers)}. "
                    f"Seer is BLIND - no coherence detected."
                )
            if lyra.grade == "SILENCE":
                return ConsensusAction.HALT.value, (
                    f"FREEWAY BLOCKED by {', '.join(blockers)}. "
                    f"Lyra is SILENT - no harmonic coherence."
                )
            if seer.grade == "FOG":
                return ConsensusAction.HOLD.value, (
                    f"FREEWAY BLOCKED by {', '.join(blockers)}. "
                    f"Seer sees FOG - holding positions."
                )
            if lyra.grade == "DISSONANCE":
                return ConsensusAction.HOLD.value, (
                    f"FREEWAY BLOCKED by {', '.join(blockers)}. "
                    f"Lyra hears DISSONANCE - frequencies clashing."
                )

            return ConsensusAction.HOLD.value, (
                f"FREEWAY BLOCKED by {', '.join(blockers)}. "
                f"Consensus not reached - holding."
            )

        # ─── ALL FOUR PASSED - Determine strength of consensus ───
        avg_score = (queen.score + king.score + seer.score + lyra.score) / 4.0
        min_score = min(queen.score, king.score, seer.score, lyra.score)

        if avg_score >= 0.80 and min_score >= 0.60 and alignment >= 0.85:
            action = ConsensusAction.STRONG_BUY.value
            reason = (
                f"FREEWAY CLEAR - STRONG consensus. "
                f"All pillars aligned (avg={avg_score:.2f}, alignment={alignment:.2f}). "
                f"Controller: {controller.value}"
            )
        elif avg_score >= 0.65 and min_score >= 0.50:
            action = ConsensusAction.BUY.value
            reason = (
                f"FREEWAY CLEAR - Good consensus. "
                f"All pillars agree (avg={avg_score:.2f}). "
                f"Controller: {controller.value}"
            )
        elif avg_score >= 0.50:
            action = ConsensusAction.HOLD.value
            reason = (
                f"FREEWAY CLEAR but cautious. "
                f"Average score {avg_score:.2f} suggests holding. "
                f"Controller: {controller.value}"
            )
        else:
            action = ConsensusAction.SELL.value
            reason = (
                f"FREEWAY CLEAR but weak. "
                f"Average score {avg_score:.2f} suggests reducing exposure. "
                f"Controller: {controller.value}"
            )

        return action, reason

    def get_active_controller(self) -> PillarRole:
        """Get the currently active controller."""
        return self.handoff_engine.current_controller

    def get_consensus_history(self) -> List[TriumvirateConsensus]:
        return list(self._consensus_history)

    def get_handoff_history(self) -> List[ControlHandoff]:
        return self.handoff_engine.get_handoff_history()

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the Quadrumvirate's state."""
        last = self._consensus_history[-1] if self._consensus_history else None
        council_latest = self.council.get_latest_session()
        return {
            "active_controller": self.handoff_engine.current_controller.value,
            "total_evaluations": len(self._consensus_history),
            "total_handoffs": len(self.handoff_engine.get_handoff_history()),
            "total_council_sessions": self.council.get_session_count(),
            "last_action": last.action if last else None,
            "last_passed": last.passed if last else None,
            "last_alignment": last.alignment_score if last else None,
            "last_council_impact": council_latest.consensus_impact if council_latest else None,
            "queen_systems": len(QUEEN_CONNECTED_SYSTEMS),
            "lyra_systems": len(LYRA_CONNECTED_SYSTEMS),
        }


# ═══════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════════════════

_triumvirate_instance: Optional[TriumvirateEngine] = None


def get_triumvirate() -> TriumvirateEngine:
    """Get the singleton Triumvirate engine instance."""
    global _triumvirate_instance
    if _triumvirate_instance is None:
        _triumvirate_instance = TriumvirateEngine()
    return _triumvirate_instance
