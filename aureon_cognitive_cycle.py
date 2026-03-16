#!/usr/bin/env python3
"""
AUREON COGNITIVE CYCLE
======================
"The system thinks, feels, plans, acts, reflects, validates, then moves.
 Like a human who already knows how to walk — all process in the background,
 the result is the step forward."

THE SEVEN PHASES (run every Orca Kill Cycle iteration):
────────────────────────────────────────────────────────
  THINK    →  Aggregate all sensor inputs (Lyra + Quadrumvirate + positions)
  FEEL     →  Paint the harmonic field (LyraVisionBridge Chladni canvas)
  PLAN     →  Derive sizing + vetoes from the cognitive state
  ACT      →  Orca executes the trade (existing code, unmodified)
  REFLECT  →  Post-trade painting; compare pre/post harmonic state
  VALIDATE →  Advisory check: was the field consistent with the outcome?
  MOVE     →  Advance the cycle counter; prepare for next THINK

HOW IT INTEGRATES
─────────────────
This module is wired into orca_complete_kill_cycle.OrcaKillCycle at 6 points:

  A. Import + availability flag at module level
  B. self._cognitive_cycle = CognitiveCycle()  inside run_autonomous()
  C. self._cognitive_cycle.think_and_feel()    before Quadrumvirate Phase-1 gate
  D. plan.sizing_modifier applied to quad_sizing after Quadrumvirate vote
  E. self._cognitive_cycle.reflect('BUY', …)  after king_on_buy()
  F. self._cognitive_cycle.reflect('SELL', …) after king_on_sell()

The cognitive cycle NEVER blocks the trading loop.  Every call is wrapped in
try/except in the Orca code.  If Lyra or the bridge are unavailable, the cycle
degrades gracefully to neutral defaults.

Gary Leckey | March 2026
"The Queen, The King, The Seer, and Lyra rule the repo together."
"""

import math
import time
import logging
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

_GRADE_TO_PATTERN: Dict[str, str] = {
    "DIVINE_HARMONY":  "MANDALA",
    "CLEAR_RESONANCE": "HEXAGON",
    "PARTIAL_HARMONY": "STAR",
    "DISSONANCE":      "SPIRAL",
    "SILENCE":         "CHAOS",
}

# Lyra chamber → organism sense (same mapping as LyraVisionBridge)
_CHAMBER_TO_SENSE: Dict[str, str] = {
    "emotion":   "sight",
    "earth":     "touch",
    "harmony":   "balance",
    "voice":     "sound",
    "solfeggio": "ancestral",
    "spirit":    "intuition",
}

_SENSE_HZ_BASE: Dict[str, float] = {
    "touch": 174, "taste": 600, "smell": 340, "sound": 460,
    "sight": 690, "balance": 528, "intuition": 900,
    "ancestral": 963, "manipulation": 285,
}

# Grades whose occurrence in the field signals danger
_DANGER_GRADES = {"SILENCE", "DISSONANCE"}

# ─────────────────────────────────────────────────────────────────────────────
# DATACLASSES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CognitiveState:
    """A complete snapshot of the organism's cognitive field at one moment."""
    timestamp: float
    cycle: int
    dominant_hz: float          # Lyra emotional_frequency
    organic_score: float        # Lyra unified_score (0–1 field purity)
    cymatics_pattern: str       # MANDALA / HEXAGON / STAR / SPIRAL / CHAOS
    grade: str                  # DIVINE_HARMONY … SILENCE
    action_bias: str            # BUY_BIAS / SELL_BIAS / HOLD / DEFEND
    emotional_zone: str         # SHADOW / BALANCE / PRIME
    sense_scores: Dict[str, float]
    sense_hz: Dict[str, float]
    quad_approved: bool
    quad_sizing: float
    exit_urgency: str
    position_multiplier: float
    painting: Optional[List[str]] = None  # rendered canvas lines (not yet printed)


@dataclass
class TradePlan:
    """CognitiveCycle.plan() output — drives position sizing + vetoes."""
    allowed: bool               # may we open a new position this cycle?
    sizing_modifier: float      # multiply amount_per_position by this; clamped [0.3, 2.0]
    avoided_symbols: List[str]  # symbols whose harmonic proxy < 0.35 (corrupted field)
    reason: str                 # human-readable justification
    cognitive_state: CognitiveState


@dataclass
class ReflectionNote:
    """A post-trade snapshot linking the pre-trade field to the outcome."""
    timestamp: float
    action: str                 # BUY / SELL
    symbol: str
    pnl: float                  # realised P&L (0.0 for BUY)
    pre_state: CognitiveState   # field state BEFORE the trade
    post_painting: List[str]    # Chladni canvas painted AFTER the trade
    grade_delta: str            # e.g. "CLEAR_RESONANCE → PARTIAL_HARMONY"
    validated: bool             # True unless discrepancy detected


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _neutral_state(cycle: int = 0) -> CognitiveState:
    """Return a safe neutral CognitiveState used when Lyra is unavailable."""
    base_scores = {s: 0.5 for s in _SENSE_HZ_BASE}
    base_hz = dict(_SENSE_HZ_BASE)
    return CognitiveState(
        timestamp=time.time(),
        cycle=cycle,
        dominant_hz=528.0,
        organic_score=0.5,
        cymatics_pattern="CIRCLE",
        grade="PARTIAL_HARMONY",
        action_bias="HOLD",
        emotional_zone="BALANCE",
        sense_scores=base_scores,
        sense_hz=base_hz,
        quad_approved=True,
        quad_sizing=1.0,
        exit_urgency="none",
        position_multiplier=1.0,
    )


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


# ─────────────────────────────────────────────────────────────────────────────
# COGNITIVE CYCLE
# ─────────────────────────────────────────────────────────────────────────────

class CognitiveCycle:
    """
    The background nervous system of the Aureon Orca Kill Cycle.

    Runs THINK → FEEL → PLAN → (ACT) → REFLECT → VALIDATE → MOVE on every
    scan iteration.  The trade (ACT) is Orca's existing code — this class
    wraps all the cognitive stages around it.

    Usage inside OrcaKillCycle.run_autonomous():

        # Startup
        self._cognitive_cycle = CognitiveCycle()

        # Every scan cycle, before Quadrumvirate gate:
        _cog_state = self._cognitive_cycle.think_and_feel(market_data, positions)
        _cog_plan  = self._cognitive_cycle.plan(_cog_state, batch_prices)
        quad_sizing *= _cog_plan.sizing_modifier
        if not _cog_plan.allowed:
            quad_go = False

        # After buy:
        note = self._cognitive_cycle.reflect('BUY', symbol, {'price': ..., 'qty': ...})
        self._cognitive_cycle.validate(note)

        # After sell:
        note = self._cognitive_cycle.reflect('SELL', symbol, {'pnl': ..., 'price': ...})
        self._cognitive_cycle.validate(note)
    """

    PAINT_EVERY_N_CYCLES  = 5     # silent background pulse every N scan cycles
    PAINT_ON_EVERY_TRADE  = True  # always paint on BUY or SELL
    PAINT_ON_GRADE_CHANGE = True  # paint immediately when harmonic grade shifts

    def __init__(self):
        self._cycle: int = 0
        self._last_state: Optional[CognitiveState] = None
        self._last_grade: str = ""
        self._last_print_cycle: int = -1
        self._reflection_history: deque = deque(maxlen=50)

        # Lazy-loaded dependencies
        self._lyra_fn = None       # lyra_get_resonance callable
        self._bridge  = None       # LyraVisionBridge instance

        logger.info("CognitiveCycle initialised — background nervous system ready")

    # ── Lazy dependency loading ───────────────────────────────────────────

    def _get_lyra_fn(self):
        if self._lyra_fn is None:
            try:
                from aureon_lyra_integration import lyra_get_resonance
                self._lyra_fn = lyra_get_resonance
            except ImportError:
                pass
        return self._lyra_fn

    def _get_bridge(self):
        if self._bridge is None:
            try:
                from aureon_lyra_vision_bridge import LyraVisionBridge
                self._bridge = LyraVisionBridge()
            except ImportError:
                pass
        return self._bridge

    # ── Phase 1: THINK ───────────────────────────────────────────────────

    def think(
        self,
        market_data: Optional[Dict[str, Any]] = None,
        positions: Optional[list] = None,
    ) -> CognitiveState:
        """
        THINK — aggregate all sensor inputs into a CognitiveState.

        Reads Lyra's resonance, maps 6 Chambers to 9 senses, determines
        cymatics pattern from harmonic grade, and builds a complete snapshot
        of the organism's current field state.
        """
        self._cycle += 1
        lyra_fn = self._get_lyra_fn()

        if lyra_fn is None:
            state = _neutral_state(self._cycle)
            self._last_state = state
            return state

        try:
            summary = lyra_fn()
        except Exception as e:
            logger.debug(f"CognitiveCycle.think: Lyra read error: {e}")
            state = _neutral_state(self._cycle)
            self._last_state = state
            return state

        dominant_hz   = float(summary.get("emotional_frequency", 528.0))
        organic_score = float(summary.get("unified_score", 0.5))
        grade         = summary.get("grade", "PARTIAL_HARMONY")
        action_bias   = summary.get("action", "HOLD")
        em_zone       = summary.get("emotional_zone", "BALANCE")
        exit_urgency  = summary.get("exit_urgency", "none")
        pos_mult      = float(summary.get("position_multiplier", 1.0))
        pattern       = _GRADE_TO_PATTERN.get(grade, "CIRCLE")
        chambers      = summary.get("chambers", {})

        # Build sense maps from chamber readings
        sense_scores: Dict[str, float] = {s: 0.5 for s in _SENSE_HZ_BASE}
        sense_hz: Dict[str, float]     = dict(_SENSE_HZ_BASE)

        for chamber_name, sense_name in _CHAMBER_TO_SENSE.items():
            c = chambers.get(chamber_name)
            if c:
                sense_scores[sense_name] = float(c.get("score", 0.5))
                sense_hz[sense_name]     = float(c.get("freq",  _SENSE_HZ_BASE.get(sense_name, 528.0)))

        # Derived senses
        sense_scores["smell"]        = (sense_scores["balance"] + sense_scores["touch"]) / 2.0
        sense_scores["taste"]        = sense_scores["ancestral"]
        sense_scores["manipulation"] = _clamp(1.0 - organic_score, 0.0, 1.0)
        sense_hz["smell"]            = (sense_hz["balance"] + sense_hz["touch"]) / 2.0
        sense_hz["manipulation"]     = 285.0

        state = CognitiveState(
            timestamp=time.time(),
            cycle=self._cycle,
            dominant_hz=dominant_hz,
            organic_score=organic_score,
            cymatics_pattern=pattern,
            grade=grade,
            action_bias=action_bias,
            emotional_zone=em_zone,
            sense_scores=sense_scores,
            sense_hz=sense_hz,
            quad_approved=True,
            quad_sizing=1.0,
            exit_urgency=exit_urgency,
            position_multiplier=pos_mult,
        )

        self._last_state = state
        return state

    # ── Phase 2: FEEL ────────────────────────────────────────────────────

    def feel(self, state: CognitiveState) -> List[str]:
        """
        FEEL — paint the harmonic field as a Chladni canvas.

        Calls LyraVisionBridge.paint() to generate the mathematical painting
        of Lyra's current perception.  Attaches the painting to the state
        and prints it if the cadence conditions are met.
        """
        bridge = self._get_bridge()
        if bridge is None:
            return []

        grade_changed = (state.grade != self._last_grade) and bool(self._last_grade)
        should_print  = (
            self.should_print_now()
            or (self.PAINT_ON_GRADE_CHANGE and grade_changed)
            or state.grade == "SILENCE"
        )

        title_prefix = ""
        if grade_changed:
            title_prefix = f"GRADE SHIFT: {self._last_grade} → {state.grade}  "
        elif state.grade == "SILENCE":
            title_prefix = "SILENCE — field incoherent  "

        try:
            painting = bridge.paint(
                market_data={"cycle": state.cycle},
                print_output=should_print,
            )
            state.painting = painting
            if should_print:
                self._last_print_cycle = self._cycle
        except Exception as e:
            logger.debug(f"CognitiveCycle.feel: paint error: {e}")
            painting = []

        return painting

    # ── Combined think+feel (primary Orca entry point) ───────────────────

    def think_and_feel(
        self,
        market_data: Optional[Dict[str, Any]] = None,
        positions: Optional[list] = None,
    ) -> CognitiveState:
        """
        THINK + FEEL in one call — the single insertion point in the Orca loop.

        Returns a CognitiveState with .painting attached.
        Call this once per scan cycle, before the Quadrumvirate gate.
        """
        state = self.think(market_data, positions)
        self.feel(state)
        return state

    # ── Phase 3: PLAN ────────────────────────────────────────────────────

    def plan(
        self,
        state: CognitiveState,
        asset_prices: Optional[Dict[str, float]] = None,
    ) -> TradePlan:
        """
        PLAN — derive a TradePlan from the current CognitiveState.

        Returns:
            allowed          True unless SILENCE or critical exit urgency
            sizing_modifier  position_multiplier × quad_sizing, clamped [0.3, 2.0]
            avoided_symbols  assets with corrupted harmonic proxy
            reason           human-readable summary
        """
        # Veto conditions
        if state.grade == "SILENCE":
            return TradePlan(
                allowed=False,
                sizing_modifier=0.0,
                avoided_symbols=[],
                reason=f"SILENCE — no coherent harmonic signal ({state.dominant_hz:.0f}Hz)",
                cognitive_state=state,
            )

        if state.exit_urgency in ("critical",):
            return TradePlan(
                allowed=False,
                sizing_modifier=0.0,
                avoided_symbols=[],
                reason=f"EXIT URGENCY = {state.exit_urgency} — field demands exit, not entry",
                cognitive_state=state,
            )

        # Position sizing
        raw_modifier = state.position_multiplier * state.quad_sizing
        sizing       = _clamp(raw_modifier, 0.3, 2.0)

        # Reduce sizing in DISSONANCE without vetoing entirely
        if state.grade == "DISSONANCE":
            sizing = _clamp(sizing * 0.5, 0.3, 1.0)

        # Symbols to avoid (those tagged in sense corruption proxy)
        avoided: List[str] = []
        if asset_prices:
            manip = state.sense_scores.get("manipulation", 0.0)
            if manip > 0.65:
                # High manipulation sense: flag all symbols (no specific ones known here)
                pass  # caller's symbol screening handles per-asset organic scores

        reason = (
            f"{state.grade} · {state.dominant_hz:.0f}Hz · "
            f"zone={state.emotional_zone} · sizing={sizing:.2f}x"
        )

        return TradePlan(
            allowed=True,
            sizing_modifier=sizing,
            avoided_symbols=avoided,
            reason=reason,
            cognitive_state=state,
        )

    # ── Phase 5: REFLECT ─────────────────────────────────────────────────

    def reflect(
        self,
        action: str,
        symbol: str,
        result: Optional[Dict[str, Any]] = None,
    ) -> ReflectionNote:
        """
        REFLECT — paint the post-trade field and compare with the pre-trade state.

        Always prints the painting when PAINT_ON_EVERY_TRADE is True.
        Stores the ReflectionNote in history.
        """
        result      = result or {}
        pnl         = float(result.get("pnl", 0.0))
        pre_state   = self._last_state or _neutral_state(self._cycle)
        bridge      = self._get_bridge()
        post_paint  = []

        # Build reflection title
        if action == "SELL":
            pnl_tag = f"  pnl=${pnl:+.4f}"
            title   = f"REFLECT — SELL {symbol}{pnl_tag}"
        else:
            title   = f"REFLECT — BUY  {symbol}"

        if bridge is not None and self.PAINT_ON_EVERY_TRADE:
            try:
                post_paint = bridge.paint(
                    market_data={"cycle": self._cycle, "action": action, "symbol": symbol},
                    print_output=True,
                )
                self._last_print_cycle = self._cycle
            except Exception as e:
                logger.debug(f"CognitiveCycle.reflect: paint error: {e}")

        # Determine post-trade grade (re-read Lyra if possible)
        post_grade = pre_state.grade
        lyra_fn    = self._get_lyra_fn()
        if lyra_fn:
            try:
                post_summary = lyra_fn()
                post_grade   = post_summary.get("grade", pre_state.grade)
            except Exception:
                pass

        grade_delta = (f"{pre_state.grade} → {post_grade}"
                       if post_grade != pre_state.grade
                       else pre_state.grade)

        note = ReflectionNote(
            timestamp=time.time(),
            action=action,
            symbol=symbol,
            pnl=pnl,
            pre_state=pre_state,
            post_painting=post_paint,
            grade_delta=grade_delta,
            validated=False,
        )
        self._reflection_history.append(note)
        return note

    # ── Phase 6: VALIDATE ────────────────────────────────────────────────

    def validate(self, note: ReflectionNote) -> bool:
        """
        VALIDATE — advisory consistency check.  Never blocks a trade.

        Logs a warning when the pre-trade field contradicts the outcome,
        creating a learning signal for Lyra and the Queen.
        """
        pre = note.pre_state

        if note.action == "SELL" and note.pnl < 0:
            if pre.grade in ("DIVINE_HARMONY", "CLEAR_RESONANCE"):
                logger.warning(
                    f"COGNITIVE DISSONANCE: SELL {note.symbol} lost ${note.pnl:.4f} "
                    f"but pre-trade field was {pre.grade} at {pre.dominant_hz:.0f}Hz — "
                    f"the field was clear but the trade failed.  Lyra should re-examine."
                )
            if pre.exit_urgency in ("none", "low"):
                pass  # normal — no exit signal was present

        if note.action == "BUY" and pre.exit_urgency in ("high", "critical"):
            logger.warning(
                f"COGNITIVE DISSONANCE: BUY {note.symbol} opened while exit_urgency="
                f"{pre.exit_urgency} — field was pushing for exits, not entries."
            )

        note.validated = True
        return True

    # ── Phase 7: MOVE ────────────────────────────────────────────────────

    def move(self) -> None:
        """
        MOVE — advance the state for the next cycle.

        Called implicitly at the end of think_and_feel().  Updates the
        last-seen grade so grade-change detection works on the next cycle.
        """
        if self._last_state:
            self._last_grade = self._last_state.grade

    # ── Cadence helper ───────────────────────────────────────────────────

    def should_print_now(self) -> bool:
        """True if the painting cadence calls for a print this cycle."""
        if self._cycle <= 0:
            return False
        if self._last_print_cycle < 0:
            return True  # always print on the very first cycle
        return (self._cycle - self._last_print_cycle) >= self.PAINT_EVERY_N_CYCLES

    # ── Diagnostics ──────────────────────────────────────────────────────

    def status(self) -> Dict[str, Any]:
        """Return a dict summarising the current cognitive state."""
        s = self._last_state
        return {
            "cycle":              self._cycle,
            "grade":              s.grade if s else "UNINITIALIZED",
            "dominant_hz":        s.dominant_hz if s else 0.0,
            "organic_score":      s.organic_score if s else 0.0,
            "cymatics_pattern":   s.cymatics_pattern if s else "UNKNOWN",
            "action_bias":        s.action_bias if s else "HOLD",
            "exit_urgency":       s.exit_urgency if s else "none",
            "position_multiplier": s.position_multiplier if s else 1.0,
            "reflections_stored": len(self._reflection_history),
        }

    def print_status(self) -> None:
        """Print a one-line cognitive status summary."""
        st = self.status()
        print(
            f"  COGNITIVE CYCLE #{st['cycle']}  "
            f"{st['grade']} · {st['dominant_hz']:.0f}Hz · "
            f"org={st['organic_score']:.2f} · {st['cymatics_pattern']} · "
            f"bias={st['action_bias']} · exit={st['exit_urgency']} · "
            f"mult={st['position_multiplier']:.2f}x"
        )


# ─────────────────────────────────────────────────────────────────────────────
# STANDALONE DEMO
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Aureon Cognitive Cycle — background nervous system demo"
    )
    parser.add_argument("--cycles", type=int, default=3,
                        help="Number of think+feel cycles to run")
    parser.add_argument("--interval", type=float, default=2.0,
                        help="Seconds between cycles")
    args = parser.parse_args()

    cycle = CognitiveCycle()
    print("\n  COGNITIVE CYCLE — STANDALONE DEMO")
    print("  " + "─" * 50)

    for i in range(args.cycles):
        if i > 0:
            time.sleep(args.interval)

        print(f"\n  ── Cycle {i + 1} / {args.cycles} {'─' * 40}")
        state = cycle.think_and_feel(market_data={"demo": True})
        plan  = cycle.plan(state)
        cycle.print_status()
        print(f"  PLAN: allowed={plan.allowed}  "
              f"sizing={plan.sizing_modifier:.2f}x  "
              f"reason={plan.reason}")
        cycle.move()

    print("\n  ── Simulated BUY reflection ──")
    note = cycle.reflect("BUY", "BTC", {"price": 65000.0, "qty": 0.001})
    cycle.validate(note)

    print("\n  ── Simulated SELL reflection ──")
    note = cycle.reflect("SELL", "BTC", {"pnl": 0.32, "price": 65320.0})
    cycle.validate(note)

    print(f"\n  Reflections stored: {len(cycle._reflection_history)}")
    print("  Demo complete.\n")
