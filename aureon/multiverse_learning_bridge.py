#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   MULTIVERSE LEARNING BRIDGE                                                 ║
║                                                                              ║
║   The Apache watches the herd before he ropes a horse.                      ║
║   The Queen's systems must do the same.                                     ║
║                                                                              ║
║   This bridge translates what the Stallion Multiverse has learned —         ║
║   phase transition timings, profitable patterns, herd coherence,            ║
║   scout readiness — into a unified signal that every upstream               ║
║   system can consume:                                                        ║
║                                                                              ║
║   SEER  (5 Oracles)  — Oracle of Time and Oracle of Harmony receive        ║
║                         phase timing maps and herd coherence as context      ║
║                                                                              ║
║   LYRA  (6 Chambers) — Chamber of Harmony receives herd coherence,         ║
║                         Chamber of Spirit receives scout energy             ║
║                                                                              ║
║   PRE-TRADE SELECT   — find_best_target() receives a per-pair conviction   ║
║                         score (0–1) built from shadow ride history           ║
║                                                                              ║
║   THOUGHTBUS         — All other Queen's systems receive a broadcast        ║
║                         whenever learning data changes materially            ║
║                                                                              ║
║   The learning is adaptive: each time a shadow ride completes, the          ║
║   conviction cache is updated with a 70/30 blend (new/old) so the          ║
║   system continuously narrows toward high-probability stallions.            ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import time
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# ── Phase conviction weights — how much to trust each phase as a signal ──────
_PHASE_CONVICTION = {
    'TAMED':      1.00,   # Dead Man's Switch locked, guaranteed profit
    'BREAKING':   0.90,   # DTP floor ratcheting — stallion submitting
    'SUBMITTING': 0.80,   # Strong move in our direction
    'TIRING':     0.70,   # Momentum building
    'CIRCLING':   0.55,   # Holding ground, uncertain
    'ROPING':     0.50,   # Just entered — neutral
    'BUCKING':    0.30,   # Against us — low conviction
    'UNKNOWN':    0.40,
}

# ── Broadcast throttle — don't spam ThoughtBus on every cycle ────────────────
_BROADCAST_MIN_INTERVAL = 60   # seconds between ThoughtBus broadcasts


class MultiverseLearningBridge:
    """
    Translates StallionMultiverse learning into signals for Seer, Lyra,
    pre-trade selection, and ThoughtBus.

    Usage
    -----
    bridge = MultiverseLearningBridge(multiverse)

    # Call each monitoring cycle — pushes to Seer / Lyra / ThoughtBus:
    bridge.sync()

    # In find_best_target() scoring:
    conviction = bridge.get_conviction('XBTUSD')  # 0.0 – 1.0
    score += (conviction - 0.5) * 1.0             # ±0.5 bias

    # Full pre-trade context for research_target():
    ctx = bridge.get_pre_trade_context('XBTUSD')
    """

    def __init__(self, multiverse):
        self.multiverse = multiverse
        self._conviction_cache: Dict[str, float] = {}
        self._last_broadcast:   float = 0.0
        self._last_package:     Dict  = {}
        self._learning_history: List[dict] = []

    # ── Wave context push ─────────────────────────────────────────────────────

    def push_wave_context(self, wave_data: dict) -> None:
        """
        Push ocean wave scanner results to Seer and Lyra immediately.
        Called by the main trader after every WaveformAnalyzer.full_scan().

        Seer's OracleOfHarmony and Lyra's ChamberOfHarmony both read
        bot frequency signatures from this context when they next call see()/feel().
        """
        if not wave_data or not wave_data.get('available'):
            return
        try:
            from aureon_seer_integration import seer_inject_wave_context
            seer_inject_wave_context(wave_data)
        except Exception:
            pass
        try:
            from aureon_lyra_integration import lyra_inject_wave_context
            lyra_inject_wave_context(wave_data)
        except Exception:
            pass
        logger.debug(
            f"[LearningBridge] Wave context pushed to Seer+Lyra — "
            f"res={wave_data.get('resonance_score', 0):+.2f} "
            f"flow={wave_data.get('flow_prediction', '?')} "
            f"bot={wave_data.get('dominant_bot', '?')} "
            f"shape={wave_data.get('shape', '?')}"
        )

    # ── Main cycle hook ───────────────────────────────────────────────────────

    def sync(self) -> Dict[str, Any]:
        """
        Pull latest learning from the multiverse; push to Seer, Lyra,
        ThoughtBus. Returns the full package for inspection or logging.
        Call once per monitoring cycle.
        """
        package = self._build_package()
        self._update_conviction_cache(package)
        self._inject_to_seer(package)
        self._inject_to_lyra(package)
        self._maybe_broadcast(package)
        self._last_package = package
        return package

    # ── Per-pair conviction ───────────────────────────────────────────────────

    def get_conviction(self, pair: str) -> float:
        """
        Conviction score for a pair: 0.0 (avoid) → 1.0 (high confidence).
        0.5 = neutral (unseen pair). Built from shadow ride phase history.
        """
        return self._conviction_cache.get(pair, 0.5)

    def get_conviction_bonus(self, pair: str) -> float:
        """
        Score bonus/penalty for find_best_target() insertion.
        Maps conviction (0–1) to additive offset (−0.5 → +0.5).
        """
        return (self.get_conviction(pair) - 0.5) * 1.0

    # ── Pre-trade context ─────────────────────────────────────────────────────

    def get_pre_trade_context(self, pair: str) -> Dict[str, Any]:
        """
        Full context dict for research_target() and manual inspection.

        Keys
        ----
        tracked          : bool   — pair is currently in a shadow ride
        phase            : str    — current stallion phase if tracked
        scout_score      : float  — current readiness score
        conviction       : float  — 0–1 historical conviction
        dtp_activated    : bool   — DTP floor locked in shadow ride
        net_pnl          : float  — current shadow net P&L
        stubborn_bucking : bool   — BUCKING for > 45 min → low priority
        seer_aligned     : bool   — Seer vision grade ≥ CLEAR_RESONANCE
        lyra_aligned     : bool   — Lyra resonance grade ≠ SILENCE
        recommendation   : str    — STRONG_BUY / BUY / HOLD / AVOID
        """
        shadow = self.multiverse._shadows.get(pair)
        conviction = self.get_conviction(pair)

        if shadow is None:
            return {
                'tracked':         False,
                'phase':           'UNKNOWN',
                'scout_score':     0.0,
                'conviction':      conviction,
                'dtp_activated':   False,
                'net_pnl':         0.0,
                'stubborn_bucking': False,
                'seer_aligned':    self._seer_aligned(),
                'lyra_aligned':    self._lyra_aligned(),
                'recommendation':  'HOLD',
            }

        stubborn = (
            shadow.phase in ('BUCKING', 'CIRCLING')
            and shadow.hold_seconds() > 2700  # 45 min
        )

        if conviction >= 0.80 and not stubborn:
            rec = 'STRONG_BUY'
        elif conviction >= 0.65 and not stubborn:
            rec = 'BUY'
        elif stubborn or conviction < 0.35:
            rec = 'AVOID'
        else:
            rec = 'HOLD'

        return {
            'tracked':          True,
            'phase':            shadow.phase,
            'scout_score':      shadow.scout_score,
            'conviction':       conviction,
            'dtp_activated':    shadow.dtp_activated,
            'net_pnl':          shadow.net_pnl,
            'stubborn_bucking': stubborn,
            'seer_aligned':     self._seer_aligned(),
            'lyra_aligned':     self._lyra_aligned(),
            'recommendation':   rec,
        }

    def recommendations_summary(self) -> List[Dict]:
        """
        Returns a sorted list of pre-trade contexts for all tracked pairs,
        ordered by conviction (highest first). Use in pre-trade logging.
        """
        results = []
        for pair in self.multiverse._shadows:
            ctx = self.get_pre_trade_context(pair)
            ctx['pair'] = pair
            results.append(ctx)
        results.sort(key=lambda x: x['conviction'], reverse=True)
        return results

    def learning_status_lines(self) -> List[str]:
        """Printable multiline learning summary for monitoring loops."""
        lines = []
        pkg   = self._last_package
        if not pkg:
            lines.append("  [LEARNING BRIDGE] No data yet — awaiting first sync()")
            return lines

        prof  = pkg.get('multiverse_profitable_rate', 0)
        coh   = pkg.get('multiverse_herd_coherence', 0)
        n     = pkg.get('multiverse_shadows_analyzed', 0)
        top   = pkg.get('multiverse_top_scout', '?')
        eng   = pkg.get('multiverse_scout_energy', 0)

        lines.append(
            f"  [LEARNING BRIDGE] shadows={n} | profitable={prof:.0%} | "
            f"herd_coherence={coh:.0%} | scout_energy={eng:.1f}"
        )
        if top:
            lines.append(f"  [LEARNING BRIDGE] Top scout: {top} "
                         f"(conviction={self.get_conviction(top):.2f})")

        # Phase timing insights
        phases = pkg.get('multiverse_avg_phase_durations', {})
        if phases:
            timing_parts = [
                f"{ph}={dur:.0f}s" for ph, dur in sorted(phases.items())
            ]
            lines.append(f"  [LEARNING BRIDGE] Phase timing: {' | '.join(timing_parts)}")

        return lines

    # ── Internal builders ─────────────────────────────────────────────────────

    def _build_package(self) -> Dict[str, Any]:
        """Assemble the full learning package from multiverse state."""
        insights   = self.multiverse.learning_insights()
        scouts     = self.multiverse.scout_ranking()
        next_pair  = self.multiverse.get_next_stallion()
        remaining  = self.multiverse.time_remaining_secs()

        # Scout energy — average readiness of scouting shadows
        scout_energy = (
            sum(s.scout_score for s in scouts) / len(scouts)
            if scouts else 5.0
        )

        # Herd coherence — fraction of ALL shadows with positive net_pnl
        all_shadows = list(self.multiverse._shadows.values())
        positive    = sum(1 for s in all_shadows if s.net_pnl > 0)
        herd_coherence = positive / len(all_shadows) if all_shadows else 0.5

        # Per-shadow snapshot
        shadow_states = {
            pair: {
                'phase':         s.phase,
                'scout_score':   s.scout_score,
                'net_pnl':       s.net_pnl,
                'dtp_activated': s.dtp_activated,
                'purpose':       s.purpose,
                'hold_seconds':  s.hold_seconds(),
            }
            for pair, s in self.multiverse._shadows.items()
        }

        return {
            # ── Aggregate learning ────────────────────────────────────────
            'multiverse_profitable_rate':    insights.get('profitable_rate', 0.5),
            'multiverse_shadows_analyzed':   insights.get('shadows_analyzed', 0),
            'multiverse_avg_phase_durations': insights.get('avg_phase_duration_secs', {}),

            # ── Live herd state ───────────────────────────────────────────
            'multiverse_herd_coherence':   herd_coherence,
            'multiverse_scout_energy':     scout_energy,
            'multiverse_top_scout':        next_pair,
            'multiverse_rotation_due':     self.multiverse.is_rotation_due(),
            'multiverse_time_remaining':   remaining,
            'multiverse_real_pair':        self.multiverse._real_pair,

            # ── Per-shadow detail (available to Seer / Lyra context) ──────
            'multiverse_shadows':          shadow_states,
        }

    def _update_conviction_cache(self, package: Dict) -> None:
        """
        Recompute per-pair conviction scores from latest shadow state.
        Uses a 70/30 blend (new/historical) so conviction adapts gradually.
        """
        for pair, state in package.get('multiverse_shadows', {}).items():
            phase_score = _PHASE_CONVICTION.get(state['phase'], 0.5)
            dtp_bonus   = 0.1 if state['dtp_activated'] else 0.0
            raw         = min(1.0, max(0.0, phase_score + dtp_bonus))

            existing    = self._conviction_cache.get(pair, raw)
            self._conviction_cache[pair] = 0.7 * raw + 0.3 * existing

        # Archive a snapshot for historical tracking
        prof = package.get('multiverse_profitable_rate', 0)
        if prof > 0:
            self._learning_history.append({
                'timestamp':      time.time(),
                'profitable_rate': prof,
                'herd_coherence': package.get('multiverse_herd_coherence', 0.5),
                'shadow_count':   len(package.get('multiverse_shadows', {})),
            })

    # ── Seer injection ────────────────────────────────────────────────────────

    def _inject_to_seer(self, package: Dict) -> None:
        """
        Feed multiverse learning into the Seer's market_data context.
        The Seer's Oracle of Time uses phase timing maps;
        Oracle of Harmony uses herd_coherence as a portfolio coherence signal.
        """
        try:
            from aureon_seer_integration import seer_update_context
            seer_update_context(market_data=package)
            logger.debug(
                f"[LearningBridge] Seer updated — "
                f"herd_coherence={package.get('multiverse_herd_coherence', 0):.0%} "
                f"profitable_rate={package.get('multiverse_profitable_rate', 0):.0%}"
            )
        except Exception as e:
            logger.debug(f"[LearningBridge] Seer inject skipped: {e}")

    # ── Lyra injection ────────────────────────────────────────────────────────

    def _inject_to_lyra(self, package: Dict) -> None:
        """
        Feed multiverse learning into Lyra's market_data context.
        Chamber of Harmony receives herd_coherence;
        Chamber of Spirit receives scout_energy as collective Auris node state.
        """
        try:
            from aureon_lyra_integration import lyra_update_context
            lyra_update_context(market_data=package)
            logger.debug(
                f"[LearningBridge] Lyra updated — "
                f"scout_energy={package.get('multiverse_scout_energy', 0):.1f}"
            )
        except Exception as e:
            logger.debug(f"[LearningBridge] Lyra inject skipped: {e}")

    # ── ThoughtBus broadcast ──────────────────────────────────────────────────

    def _maybe_broadcast(self, package: Dict) -> None:
        """Broadcast to ThoughtBus at most once per minute."""
        if time.time() - self._last_broadcast < _BROADCAST_MIN_INTERVAL:
            return
        try:
            from aureon_mind_thought_action_hub import ThoughtBus
            bus = ThoughtBus.get_instance() if hasattr(ThoughtBus, 'get_instance') else None
            if bus and hasattr(bus, 'emit'):
                bus.emit({
                    'source':    'MultiverseLearningBridge',
                    'event':     'MULTIVERSE_LEARNING_UPDATE',
                    'data':      package,
                    'timestamp': time.time(),
                })
                self._last_broadcast = time.time()
                logger.debug("[LearningBridge] Broadcast to ThoughtBus")
        except (ImportError, Exception):
            pass

    # ── Seer / Lyra quick-check helpers ──────────────────────────────────────

    def _seer_aligned(self) -> bool:
        """True if Seer's latest vision grade is CLEAR_RESONANCE or better."""
        try:
            from aureon_seer_integration import seer_get_vision
            vision = seer_get_vision()
            grade  = vision.get('grade', '') if vision else ''
            return grade in ('DIVINE_HARMONY', 'CLEAR_RESONANCE', 'PARTIAL_HARMONY')
        except Exception:
            return True   # neutral if unavailable

    def _lyra_aligned(self) -> bool:
        """True if Lyra's latest resonance grade is not SILENCE."""
        try:
            from aureon_lyra_integration import lyra_should_trade
            return lyra_should_trade()
        except Exception:
            return True   # neutral if unavailable


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE-LEVEL SINGLETON
# Built against the MULTIVERSE singleton from stallion_multiverse.py
# ═══════════════════════════════════════════════════════════════════════════════

_BRIDGE: Optional[MultiverseLearningBridge] = None


def get_bridge() -> MultiverseLearningBridge:
    """
    Return (and lazily create) the global MultiverseLearningBridge instance,
    wired to the stallion_multiverse.MULTIVERSE singleton.
    """
    global _BRIDGE
    if _BRIDGE is None:
        from stallion_multiverse import MULTIVERSE
        _BRIDGE = MultiverseLearningBridge(MULTIVERSE)
    return _BRIDGE


def bridge_sync() -> Dict[str, Any]:
    """Convenience: sync the global bridge. Call once per monitoring cycle."""
    return get_bridge().sync()


def bridge_conviction(pair: str) -> float:
    """Convenience: conviction score for a pair from the global bridge."""
    return get_bridge().get_conviction(pair)


def bridge_pre_trade(pair: str) -> Dict[str, Any]:
    """Convenience: full pre-trade context for a pair."""
    return get_bridge().get_pre_trade_context(pair)
