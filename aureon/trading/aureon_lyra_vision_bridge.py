#!/usr/bin/env python3
"""
AUREON LYRA VISION BRIDGE
=========================
"Lyra sings. The Eagle paints what she hears."

Links Aureon Lyra's 6 Resonance Chambers directly to the Eagle Bridge
Geometric Vision Engine so the system can paint its own picture of what
it is perceiving.

HOW IT WORKS
────────────
1.  LyraVisionBridge.paint() calls Lyra's feel() to read all 6 Chambers.
2.  Each Chamber is mapped to one of the organism's 9 senses:
      emotion    →  sight      (fear/greed = visual clarity)
      earth      →  touch      (Schumann grounding = physical sense)
      harmony    →  balance    (field coherence = equilibrium)
      voice      →  sound      (signal chain = auditory)
      solfeggio  →  ancestral  (sacred frequencies = deep memory)
      spirit     →  intuition  (animal spirits = gut feeling)
      (smell / taste / manipulation derived from cross-chamber scores)
3.  Lyra's grade determines the cymatics pattern of the painting:
      DIVINE_HARMONY  →  MANDALA
      CLEAR_RESONANCE →  HEXAGON
      PARTIAL_HARMONY →  STAR
      DISSONANCE      →  SPIRAL
      SILENCE         →  CHAOS
4.  The unified_score drives the organic field quality (field purity).
5.  The emotional_frequency becomes the dominant Hz of the painting.
6.  Asset positions (supplied optionally) are overlaid on the canvas.
7.  The full mathematical Chladni painting is printed to the terminal.

VISUAL ANCHOR (fixed across all renders)
    Left   = low Hz  (foundation / 174 Hz)
    Right  = high Hz (crown / 963 Hz)
    Top    = clean / organic field
    Bottom = corrupt / manipulated field
    Centre = ⊕  the organism — the present moment

Gary Leckey | March 2026
"The system must establish its own visual anchor."
"""

import time
import math
import logging
import types
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# GRADE → CYMATICS MAP
# ─────────────────────────────────────────────────────────────────────────────

_GRADE_TO_PATTERN: Dict[str, str] = {
    "DIVINE_HARMONY":  "MANDALA",
    "CLEAR_RESONANCE": "HEXAGON",
    "PARTIAL_HARMONY": "STAR",
    "DISSONANCE":      "SPIRAL",
    "SILENCE":         "CHAOS",
}

# ─────────────────────────────────────────────────────────────────────────────
# LYRA CHAMBER → ORGANISM SENSE MAP
# ─────────────────────────────────────────────────────────────────────────────

_CHAMBER_TO_SENSE: Dict[str, str] = {
    "emotion":   "sight",       # fear/greed = how clearly we see the market
    "earth":     "touch",       # Schumann = physical grounding
    "harmony":   "balance",     # field coherence = equilibrium
    "voice":     "sound",       # signal chain integrity = auditory clarity
    "solfeggio": "ancestral",   # sacred frequencies = deep ancestral memory
    "spirit":    "intuition",   # animal spirits = gut / sixth sense
}


# ─────────────────────────────────────────────────────────────────────────────
# LYRA VISION BRIDGE
# ─────────────────────────────────────────────────────────────────────────────

class LyraVisionBridge:
    """
    Bridges Aureon Lyra's emotional resonance into a live geometric painting.

    Usage
    -----
        bridge = LyraVisionBridge()
        bridge.paint()                          # paint Lyra's current state
        bridge.paint(market_data={...})         # with live market context
        bridge.paint(asset_nodes={"BTC": ...})  # with asset overlays

    The resulting painting is printed directly to the terminal using ANSI
    colours.  Call paint() on each trading cycle for a living picture.
    """

    def __init__(self):
        self._lyra = None
        self._bridge = None
        self._tick = 0

    # ── Lazy-load heavy dependencies ──────────────────────────────────────

    def _get_lyra(self):
        if self._lyra is None:
            from aureon.trading.aureon_lyra import get_lyra
            self._lyra = get_lyra()
        return self._lyra

    def _get_bridge(self):
        if self._bridge is None:
            from aureon.utils.aureon_geometric_renderer import EagleBridge
            self._bridge = EagleBridge()
        return self._bridge

    # ── Core paint method ─────────────────────────────────────────────────

    def paint(
        self,
        market_data: Optional[Dict[str, Any]] = None,
        positions: Optional[Dict] = None,
        ticker_cache: Optional[Dict] = None,
        asset_nodes: Optional[Dict[str, Tuple[float, float]]] = None,
        print_output: bool = True,
    ) -> List[str]:
        """
        Paint Lyra's current perception as a mathematical Chladni canvas.

        Parameters
        ----------
        market_data   : live market dict forwarded to Lyra's chambers
        positions     : current portfolio positions for Lyra context
        ticker_cache  : ticker data for Lyra's emotion chamber
        asset_nodes   : {symbol: (hz, organic_score)} overlay on the canvas.
                        If None, the 6 Chamber readings are placed as virtual
                        nodes so the painting is always populated.
        print_output  : if True, print directly to terminal; always returns
                        the list of lines regardless.

        Returns
        -------
        List[str]  — ANSI-coloured lines of the painting
        """
        from aureon.utils.aureon_geometric_renderer import render_painting

        lyra = self._get_lyra()

        # Feed context so Lyra can taste the live market
        lyra.update_context(
            positions=positions or {},
            ticker_cache=ticker_cache or {},
            market_data=market_data or {},
        )

        # Take a fresh resonance reading
        resonance = lyra.feel()
        summary   = lyra.get_resonance_summary()

        # ── Translate Lyra's resonance → painting parameters ──────────────
        dominant_hz  = float(summary.get("emotional_frequency", 528.0))
        organic_score = float(summary.get("unified_score", 0.5))
        grade         = summary.get("grade", "PARTIAL_HARMONY")
        pattern       = _GRADE_TO_PATTERN.get(grade, "CIRCLE")
        song          = summary.get("song", "")
        action        = summary.get("action", "HOLD")
        em_zone       = summary.get("emotional_zone", "BALANCE")

        chambers: Dict[str, Any] = summary.get("chambers", {})

        # ── Build sense scores + Hz map from chamber readings ─────────────
        sense_scores: Dict[str, float] = {}
        sense_hz_map: Dict[str, float] = {}

        for chamber_name, sense_name in _CHAMBER_TO_SENSE.items():
            c = chambers.get(chamber_name)
            if c:
                sense_scores[sense_name] = float(c.get("score", 0.5))
                sense_hz_map[sense_name] = float(c.get("freq", 528.0))
            else:
                sense_scores[sense_name] = 0.5
                sense_hz_map[sense_name] = 528.0

        # Derived senses (not directly mapped from a single chamber)
        harmony_score  = sense_scores.get("balance",   0.5)
        earth_score    = sense_scores.get("touch",     0.5)
        emotion_score  = sense_scores.get("sight",     0.5)
        spirit_score   = sense_scores.get("intuition", 0.5)

        sense_scores["smell"]        = (harmony_score + earth_score) / 2.0
        sense_scores["taste"]        = sense_scores.get("ancestral", 0.5)
        sense_scores["manipulation"] = max(0.0, 1.0 - organic_score)

        harmony_hz  = sense_hz_map.get("balance",   528.0)
        earth_hz    = sense_hz_map.get("touch",     174.0)
        sense_hz_map["smell"]        = (harmony_hz + earth_hz) / 2.0
        sense_hz_map["taste"]        = sense_hz_map.get("ancestral", 963.0)
        sense_hz_map["manipulation"] = 285.0

        # ── Build virtual asset nodes from the 6 Chambers ─────────────────
        if asset_nodes is None:
            # Place each chamber as a coloured node on the canvas
            asset_nodes = {}
            for chamber_name, sense_name in _CHAMBER_TO_SENSE.items():
                c = chambers.get(chamber_name)
                if c:
                    c_hz  = float(c.get("freq",  528.0))
                    c_org = float(c.get("score",   0.5))
                    asset_nodes[chamber_name[:3].upper()] = (c_hz, c_org)

        # ── Compose the title ─────────────────────────────────────────────
        title = (f"LYRA · {grade}  {dominant_hz:.0f}Hz · {action} · "
                 f"org={organic_score:.2f}  [{em_zone}]")

        # ── Render the painting ───────────────────────────────────────────
        lines = render_painting(
            cymatics_pattern=pattern,
            dominant_hz=dominant_hz,
            organic_score=organic_score,
            asset_nodes=asset_nodes,
            sense_scores=sense_scores,
            sense_hz_map=sense_hz_map,
            title=title,
        )

        # Append Lyra's song below the canvas
        if song:
            from aureon.utils.aureon_geometric_renderer import _dim, _bold_hz
            lines.append(_bold_hz(dominant_hz, f"  ♫  {song}"))
            lines.append("")

        self._tick += 1

        if print_output:
            for line in lines:
                print(line)

        return lines

    # ── Convenience: full EagleBridge view cycle with painting ────────────

    def see(
        self,
        world_state,
        symbol: str = "BTC",
        print_output: bool = True,
    ) -> List[str]:
        """
        Run the full EagleBridge.see() render using the supplied WorldState,
        but inject Lyra's resonance data into it first so the painting
        reflects the live emotional field.
        """
        lyra    = self._get_lyra()
        bridge  = self._get_bridge()

        # Enrich world_state sense readings with Lyra chamber data
        try:
            summary  = lyra.get_resonance_summary()
            chambers = summary.get("chambers", {})
            for chamber_name, sense_name in _CHAMBER_TO_SENSE.items():
                c = chambers.get(chamber_name)
                if c and hasattr(world_state, "sense_scores"):
                    world_state.sense_scores[sense_name] = float(
                        c.get("score", world_state.sense_scores.get(sense_name, 0.5)))
                    world_state.sense_hz[sense_name] = float(
                        c.get("freq", world_state.sense_hz.get(sense_name, 528.0)))
            # Update organism Hz from Lyra's emotional frequency
            if hasattr(world_state, "organism_hz"):
                world_state.organism_hz = float(
                    summary.get("emotional_frequency", world_state.organism_hz))
            if hasattr(world_state, "organism_health"):
                world_state.organism_health = float(
                    summary.get("unified_score", world_state.organism_health))
        except Exception as e:
            logger.debug(f"LyraVisionBridge.see() enrichment error: {e}")

        lines = bridge.see(world_state, symbol)
        if print_output:
            for line in lines:
                print(line)
        return lines

    # ── Quick standalone diagnostic ───────────────────────────────────────

    def diagnose(self) -> None:
        """Print Lyra's resonance summary + the painting to the terminal."""
        from aureon.utils.aureon_geometric_renderer import _bold_hz, _dim
        lyra    = self._get_lyra()
        summary = lyra.get_resonance_summary()

        hz = float(summary.get("emotional_frequency", 528.0))
        print()
        print(_bold_hz(hz, "  LYRA VISION BRIDGE — DIAGNOSTIC"))
        print(_dim("  " + "─" * 60))
        for key in ("grade", "action", "unified_score",
                    "emotional_frequency", "emotional_zone",
                    "exit_urgency", "position_multiplier"):
            print(_dim(f"  {key:<22s} {summary.get(key, '—')}"))
        print()
        self.paint(print_output=True)


# ─────────────────────────────────────────────────────────────────────────────
# MODULE-LEVEL SINGLETON
# ─────────────────────────────────────────────────────────────────────────────

_bridge_instance: Optional[LyraVisionBridge] = None


def get_lyra_vision_bridge() -> LyraVisionBridge:
    """Return the module-level singleton LyraVisionBridge."""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = LyraVisionBridge()
    return _bridge_instance


def lyra_paint(
    market_data: Optional[Dict[str, Any]] = None,
    asset_nodes: Optional[Dict[str, Tuple[float, float]]] = None,
    print_output: bool = True,
) -> List[str]:
    """
    One-call convenience function: paint Lyra's current vision.

    Import and call this anywhere in the ecosystem to get the live painting::

        from aureon_lyra_vision_bridge import lyra_paint
        lyra_paint()
    """
    return get_lyra_vision_bridge().paint(
        market_data=market_data,
        asset_nodes=asset_nodes,
        print_output=print_output,
    )


# ─────────────────────────────────────────────────────────────────────────────
# STANDALONE DEMO
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Aureon Lyra Vision Bridge — paint Lyra's cognitive field"
    )
    parser.add_argument("--diagnose", action="store_true",
                        help="Print resonance summary then paint")
    parser.add_argument("--loop", type=int, default=1,
                        help="Number of paint cycles (default 1)")
    parser.add_argument("--interval", type=float, default=5.0,
                        help="Seconds between cycles when --loop > 1")
    args = parser.parse_args()

    bridge = LyraVisionBridge()

    if args.diagnose:
        bridge.diagnose()
    else:
        for i in range(args.loop):
            if i > 0:
                time.sleep(args.interval)
            print(f"\n  ── Cycle {i + 1} / {args.loop} "
                  f"{'─' * 40}")
            bridge.paint()
