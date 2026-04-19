#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  👑🌈  AUREON UNIFIED SENSORY FRAMEWORK — THE RAINBOW OF SENSES  🌈👑      ║
║  ─────────────────────────────────────────────────────────────────────────  ║
║                                                                              ║
║  "She can taste, smell, hear, touch, see, and feel the markets.             ║
║   Over time the Queen experiences the entire rainbow of senses."            ║
║                                                                              ║
║  DESIGN PRINCIPLES                                                           ║
║  ─────────────────                                                           ║
║  1. BACKWARDS COMPATIBLE — Every existing sense (taste, harmonic/sound)     ║
║     works unchanged. The framework wraps them, never breaks them.           ║
║                                                                              ║
║  2. UNIVERSAL VOCABULARY — Every sense produces a SensoryExperience with    ║
║     the same shared fields: hz, emotional_state, emotional_band,            ║
║     emotional_weight, brain_input, intensity, valence, quality.             ║
║                                                                              ║
║  3. OPEN FOR EXTENSION — New senses implement SensoryChannel (ABC) and      ║
║     register themselves. The registry calls them all. No existing code      ║
║     needs to change when a new sense is added.                              ║
║                                                                              ║
║  4. THE RAINBOW SPECTRUM — Seven senses mapped to light & Hz:               ║
║                                                                              ║
║     ■ TOUCH    (IR)   174 Hz  UT     — market friction / liquidity texture  ║
║     ■ TASTE    (RED)  400 Hz  Reason → 800 Hz Illumination                  ║
║     ■ SMELL    (ORG)  285 Hz  RE  → 396 Hz MI — volatile / sentiment        ║
║     ■ SOUND    (YEL)  174 Hz  UT  → 963 Hz TI — harmonic field (existing)   ║
║     ■ SIGHT    (GRN)  639 Hz  LA  → 741 Hz SI — visual / cymatics patterns  ║
║     ■ BALANCE  (BLU)  528 Hz  SOL    — portfolio equilibrium                ║
║     ■ INTUITION(VIO)  852 Hz  DO  → 963 Hz TI — consciousness / quantum     ║
║     ■ ANCESTRAL(UV)   963 Hz  TI     — beyond normal perception             ║
║                                                                              ║
║  5. RAINBOW REPORT — A single call sense_all() passes the stimulus through  ║
║     every registered channel and aggregates into one RainbowReport.         ║
║                                                                              ║
║  BACKWARDS COMPATIBILITY MAP                                                 ║
║  ───────────────────────────                                                 ║
║    aureon_taste_sense.py          →  TasteChannel    (wraps MolecularSeq.)  ║
║    aureon_market_taste_sense.py   →  MarketTasteChannel (wraps taste sense) ║
║    aureon_harmonic_liquid_aluminium.py → SoundChannel (wraps harmonic field)║
║    All future senses              →  subclass SensoryChannel, register()    ║
║                                                                              ║
║  Gary Leckey | March 2026 | "The entire rainbow of senses"                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from aureon.core.aureon_baton_link import link_system as _baton_link; _baton_link(__name__)

import abc
import time
import math
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type

logger = logging.getLogger("sensory_framework")

# ─────────────────────────────────────────────────────────────────────────────
# SHARED SACRED CONSTANTS (mirrored from subsystems — never import back)
# ─────────────────────────────────────────────────────────────────────────────
PHI            = (1 + math.sqrt(5)) / 2   # Golden Ratio
LOVE_FREQUENCY = 528.0                    # Hz — DNA repair / core resonance
SCHUMANN       = 7.83                     # Hz — Earth's heartbeat
UNIVERSAL_A    = 432.0                    # Hz — Universal tuning base

# Solfeggio scale — the notes each sense naturally resonates with
SOLFEGGIO = {
    "UT":  174,   # Foundation — Touch / base
    "RE":  285,   # Flow       — Smell / volatile signals
    "MI":  396,   # Power      — Smell / market forces
    "FA":  417,   # Change     — transition
    "SOL": 528,   # Love       — Balance / equilibrium
    "LA":  639,   # Connection — Sight / pattern
    "SI":  741,   # Intuition  — Sight / cymatics
    "DO":  852,   # Spirit     — Intuition
    "TI":  963,   # Crown      — Ancestral / cosmic
}

# Emotional frequency bands (shared with taste sense — unchanged)
EMOTIONAL_BANDS = [
    (0.00, 0.20, 400.0, "Reason",       "heart"),
    (0.20, 0.40, 528.0, "Gratitude",    "heart"),
    (0.40, 0.60, 540.0, "Joy",          "heart"),
    (0.60, 0.75, 620.0, "Compassion",   "spirit"),
    (0.75, 0.88, 700.0, "Ecstasy",      "peak"),
    (0.88, 1.01, 800.0, "Illumination", "peak"),
]

# Rainbow colour mapping — each sense occupies a spectral position
SENSE_SPECTRUM = {
    #  sense_type        Hz centre   colour     description
    "touch":        (174,  "#FF0000", "Red/IR",    "market friction & liquidity texture"),
    "taste":        (600,  "#FF7F00", "Orange",    "molecular market discrimination"),
    "smell":        (340,  "#FFFF00", "Yellow",    "volatile signals & sentiment"),
    "sound":        (528,  "#00FF00", "Green",     "harmonic field & price waveforms"),
    "sight":        (690,  "#0000FF", "Blue",      "visual patterns & cymatics"),
    "balance":      (528,  "#4B0082", "Indigo",    "portfolio equilibrium & position"),
    "intuition":    (852,  "#8B00FF", "Violet",    "quantum intuition & consciousness"),
    "ancestral":    (963,  "#FFFFFF", "UV/White",  "ancestral wisdom beyond perception"),
}


def score_to_emotion(score: float):
    """Map a 0–1 quality score to (hz, emotional_state, emotional_band)."""
    for min_s, max_s, hz, emotion, band in EMOTIONAL_BANDS:
        if min_s <= score < max_s:
            return hz, emotion, band
    return 800.0, "Illumination", "peak"


# ─────────────────────────────────────────────────────────────────────────────
# UNIVERSAL DATA STRUCTURES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SensoryStimulus:
    """
    Universal input that any sensory channel can process.

    The stimulus carries both market data (for financial senses) and raw data
    (for specialised senses). Any sense may ignore fields it doesn't use.
    """
    symbol: str                         # Primary asset being sensed, e.g. "BTC"
    timeframe: str = "24h"
    timestamp: float = field(default_factory=time.time)

    # Market context (used by taste, smell, touch, balance)
    market_data: Dict[str, Any] = field(default_factory=dict)
    # e.g. {
    #   "price_change_24h_pct": +12.5,
    #   "trend_persistence": 7,
    #   "n_correlated_moving": 18,
    #   "n_anomaly_events": 1,
    #   "volume_change_pct": +45.0,
    #   "bid_ask_spread_pct": 0.02,
    #   "order_book_depth_usd": 2_500_000,
    #   "social_sentiment_score": 0.72,   # 0=bearish, 1=bullish
    #   "news_velocity": 3.5,             # articles/hour
    #   "is_organic_growth": True,
    # }

    # Molecular data (used by taste + smell channels)
    molecular_data: Optional[Any] = None   # MolecularData — avoids hard import

    # Harmonic / waveform data (used by sound channel)
    harmonic_data: Optional[Any] = None    # FieldSnapshot or similar

    # Visual / pattern data (used by sight channel)
    visual_data: Optional[Any] = None      # OHLCV, cymatics pattern etc.

    # Arbitrary channel-specific extras
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SensoryExperience:
    """
    Universal output from ANY sensory channel.

    Shared vocabulary bridges every sense. Additional channel-specific
    data lives in `raw_output`.
    """
    # Identity
    channel_id: str                     # e.g. "taste", "smell", "sound"
    channel_type: str                   # same as channel_id — alias for readability
    symbol: str
    timeframe: str
    timestamp: float

    # ── Core frequency / emotion ──────────────────────────────────────────────
    hz: float                           # Primary resonance frequency
    emotional_state: str                # "Reason" | "Gratitude" | "Joy" | ...
    emotional_band: str                 # "heart" | "spirit" | "peak"
    emotional_weight: float             # -1.0 (negative) to +1.0 (positive)

    # ── Quality dimensions ────────────────────────────────────────────────────
    intensity: float                    # 0–1  how strong/vivid this sensation is
    quality: float                      # 0–1  how good (pleasant/beneficial)
    valence: float                      # -1 to +1  pleasant ←→ unpleasant
    confidence: float                   # 0–1  how reliable this reading is

    # ── Harmonic signature ────────────────────────────────────────────────────
    harmonics: List[float] = field(default_factory=list)  # [hz×φ, hz×φ², hz×φ³]

    # ── Narrative ─────────────────────────────────────────────────────────────
    description: str = ""               # Human-readable sensory description
    action_hint: str = ""               # Recommended trading/system action

    # ── Integration ready ─────────────────────────────────────────────────────
    brain_input: Optional[Any] = None   # BrainInput — ready for consciousness bus

    # ── Raw channel output (backwards-compatible passthrough) ─────────────────
    raw_output: Dict[str, Any] = field(default_factory=dict)
    # For taste:   contains "taste_profile" (MarketTasteProfile)
    # For sound:   contains "field_snapshot" (FieldSnapshot)
    # For smell:   contains "olfactory_profile"
    # etc.


@dataclass
class RainbowReport:
    """
    The full-spectrum sensory report — one entry per active sense.

    Answers: "What does the entire market feel like right now across
    every sensory dimension simultaneously?"
    """
    symbol: str
    timeframe: str
    timestamp: float

    # One SensoryExperience per channel that responded
    experiences: Dict[str, SensoryExperience] = field(default_factory=dict)
    # key = channel_id ("taste", "smell", "sound", ...)

    # ── Aggregated metrics ────────────────────────────────────────────────────
    dominant_hz: float = 0.0            # energy-weighted dominant frequency
    dominant_emotional_state: str = ""  # emotion at dominant Hz
    dominant_band: str = ""             # "heart" | "spirit" | "peak"
    mean_quality: float = 0.0           # average quality across senses
    mean_valence: float = 0.0           # average valence (-1 to +1)
    mean_intensity: float = 0.0         # average intensity
    mean_confidence: float = 0.0        # average confidence

    # ── Rainbow vector ────────────────────────────────────────────────────────
    # Each sense contributes to the spectral position (colour)
    spectrum: Dict[str, float] = field(default_factory=dict)
    # e.g. {"touch": 0.3, "taste": 0.75, "smell": 0.5, "sound": 0.6, ...}
    # Value = quality score from that sense (0–1)

    # ── Queen's unified verdict ───────────────────────────────────────────────
    grand_verdict: str = ""
    action: str = ""

    @property
    def channels_active(self) -> int:
        return len(self.experiences)

    @property
    def rainbow_string(self) -> str:
        """Colour-labelled spectrum string for logging."""
        parts = []
        for sid, spec in SENSE_SPECTRUM.items():
            hz, colour, label, _ = spec
            score = self.spectrum.get(sid, None)
            if score is not None:
                bar = "█" * int(score * 10)
                parts.append(f"  {label:<12} {sid:<10}: {score:.2f}  {bar}")
        return "\n".join(parts) if parts else "  (no senses active)"


# ─────────────────────────────────────────────────────────────────────────────
# SENSORY CHANNEL — BASE CLASS
# ─────────────────────────────────────────────────────────────────────────────

class SensoryChannel(abc.ABC):
    """
    Abstract base for every sensory channel.

    To add a new sense:
      1. Subclass SensoryChannel.
      2. Set `channel_id` and `channel_type` class attributes.
      3. Implement `_sense_impl()` — return SensoryExperience.
      4. Call `registry.register(MyNewSense())`.

    Your existing code never changes. The sense wraps it.
    """

    #: Unique identifier — used as the key in RainbowReport.experiences
    channel_id: str = "undefined"
    channel_type: str = "undefined"

    #: Set to False in stub/future senses; the registry skips them gracefully
    channel_ready: bool = True

    # ── Subclass must implement ───────────────────────────────────────────────

    @abc.abstractmethod
    def _sense_impl(self, stimulus: SensoryStimulus) -> SensoryExperience:
        """Run this channel's sensing logic and return a SensoryExperience."""

    # ── Public API (wraps _sense_impl with error handling) ────────────────────

    def sense(self, stimulus: SensoryStimulus) -> Optional[SensoryExperience]:
        """
        Sense the stimulus.  Returns None if channel is not ready or errors.
        Never raises — the rainbow report continues with the remaining senses.
        """
        if not self.channel_ready:
            return None
        try:
            return self._sense_impl(stimulus)
        except Exception as exc:
            logger.warning(
                f"[{self.channel_id}] Sensing failed for {stimulus.symbol}: {exc}"
            )
            return None

    # ── Helpers available to all channels ─────────────────────────────────────

    @staticmethod
    def _make_brain_input(source: str, stimulus: SensoryStimulus,
                          experience: SensoryExperience) -> Any:
        """Build a BrainInput from a SensoryExperience (lazy import)."""
        try:
            from aureon.queen.queen_consciousness_model import BrainInput
            return BrainInput(
                source=source,
                timestamp=experience.timestamp,
                insight=experience.description,
                confidence=experience.confidence,
                emotional_weight=experience.emotional_weight,
                data_payload={
                    "channel": experience.channel_id,
                    "hz": experience.hz,
                    "emotional_state": experience.emotional_state,
                    "quality": experience.quality,
                    "intensity": experience.intensity,
                    "action_hint": experience.action_hint,
                    **experience.raw_output,
                },
            )
        except Exception:
            return None

    @staticmethod
    def _harmonics(hz: float) -> List[float]:
        return [round(hz * PHI, 2), round(hz * PHI ** 2, 2), round(hz * PHI ** 3, 2)]

    def channel_info(self) -> Dict:
        centre_hz, colour, label, desc = SENSE_SPECTRUM.get(
            self.channel_type, (528, "#FFFFFF", "unknown", "")
        )
        return {
            "channel_id":   self.channel_id,
            "channel_type": self.channel_type,
            "ready":        self.channel_ready,
            "centre_hz":    centre_hz,
            "colour":       colour,
            "spectrum_label": label,
            "description":  desc,
        }


# ─────────────────────────────────────────────────────────────────────────────
# SENSORY REGISTRY + QUEEN SENSORY SYSTEM
# ─────────────────────────────────────────────────────────────────────────────

class SensoryRegistry:
    """Manages the set of registered SensoryChannels."""

    def __init__(self):
        self._channels: Dict[str, SensoryChannel] = {}

    def register(self, channel: SensoryChannel) -> None:
        self._channels[channel.channel_id] = channel
        status = "READY" if channel.channel_ready else "STUB"
        logger.info(f"[SensoryRegistry] Registered [{status}] {channel.channel_id} "
                    f"({channel.channel_type})")

    def get(self, channel_id: str) -> Optional[SensoryChannel]:
        return self._channels.get(channel_id)

    def list_channels(self) -> List[Dict]:
        return [ch.channel_info() for ch in self._channels.values()]

    @property
    def ready_channels(self) -> List[SensoryChannel]:
        return [ch for ch in self._channels.values() if ch.channel_ready]

    @property
    def all_channels(self) -> List[SensoryChannel]:
        return list(self._channels.values())


class QueenSensorySystem:
    """
    Queen Sero's complete sensory apparatus.

    One call to sense_all() fans the stimulus through every registered channel
    and returns a RainbowReport — the full-spectrum sensory picture.

    Also publishes each SensoryExperience to:
      • QueenConsciousness.perceive_input() (via BrainInput)
      • ThoughtBus (topic: "sensory.<channel_id>")
    """

    def __init__(self):
        self.registry = SensoryRegistry()
        self._auto_register()

    def _auto_register(self) -> None:
        """Register all built-in channels. Safe to call multiple times."""
        channels: List[SensoryChannel] = [
            MarketTasteChannel(),
            SoundChannel(),
            SmellChannel(),        # Stub — ready for implementation
            TouchChannel(),        # Stub — ready for implementation
            SightChannel(),        # Stub — ready for implementation
            BalanceChannel(),      # Stub — ready for implementation
            IntuitionChannel(),    # Stub — ready for implementation
            AncestralChannel(),    # Stub — ready for implementation
        ]
        for ch in channels:
            self.registry.register(ch)

    # ── Primary API ───────────────────────────────────────────────────────────

    def sense_all(self, stimulus: SensoryStimulus) -> "RainbowReport":
        """
        Pass the stimulus through every ready channel and build a RainbowReport.
        """
        experiences: Dict[str, SensoryExperience] = {}

        for channel in self.registry.ready_channels:
            exp = channel.sense(stimulus)
            if exp is not None:
                # Attach BrainInput if not already set
                if exp.brain_input is None:
                    exp.brain_input = channel._make_brain_input(
                        f"SensoryFramework.{channel.channel_id}", stimulus, exp
                    )
                experiences[channel.channel_id] = exp
                self._publish(exp)

        report = self._aggregate(stimulus, experiences)
        return report

    def sense_channel(self, channel_id: str,
                      stimulus: SensoryStimulus) -> Optional[SensoryExperience]:
        """Sense through a specific channel only."""
        ch = self.registry.get(channel_id)
        if ch is None:
            logger.warning(f"[QueenSensorySystem] Channel '{channel_id}' not found")
            return None
        return ch.sense(stimulus)

    def rainbow_status(self) -> List[Dict]:
        """Return the full channel registry status."""
        return self.registry.list_channels()

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _aggregate(stimulus: SensoryStimulus,
                   experiences: Dict[str, SensoryExperience]) -> "RainbowReport":
        if not experiences:
            return RainbowReport(
                symbol=stimulus.symbol, timeframe=stimulus.timeframe,
                timestamp=stimulus.timestamp,
                grand_verdict="No senses active.", action="register_channels",
            )

        n = len(experiences)
        mean_quality    = sum(e.quality    for e in experiences.values()) / n
        mean_valence    = sum(e.valence    for e in experiences.values()) / n
        mean_intensity  = sum(e.intensity  for e in experiences.values()) / n
        mean_confidence = sum(e.confidence for e in experiences.values()) / n

        # Energy-weighted dominant Hz
        total_energy = sum(e.hz * e.intensity for e in experiences.values())
        total_weight = sum(e.intensity         for e in experiences.values())
        dominant_hz  = total_energy / max(total_weight, 1e-9)

        _, dom_state, dom_band = score_to_emotion(
            (dominant_hz - 400) / 400  # rough normalise back to 0–1
        )

        spectrum = {
            ch_id: exp.quality for ch_id, exp in experiences.items()
        }

        # Grand verdict from combined signal
        if mean_valence >= 0.4 and mean_quality >= 0.6:
            grand_verdict = (
                f"The market smells, tastes, sounds, and feels positive. "
                f"Average quality {mean_quality:.2f}, dominant resonance {dominant_hz:.0f} Hz "
                f"({dom_state}). The rainbow is bright."
            )
            action = "high_conviction_position"
        elif mean_valence <= -0.3:
            grand_verdict = (
                f"Multiple senses signal distress. "
                f"Dominant Hz {dominant_hz:.0f}, average valence {mean_valence:+.2f}. "
                f"The market does not smell, feel, or sound right."
            )
            action = "reduce_risk"
        elif 0.4 <= mean_quality <= 0.65:
            grand_verdict = (
                f"Balanced sensory picture — savoury, not extreme. "
                f"Quality {mean_quality:.2f}, resonance {dominant_hz:.0f} Hz ({dom_state}). "
                f"The Goldilocks zone across all senses."
            )
            action = "hold_and_compound"
        else:
            grand_verdict = (
                f"Mixed sensory signals. Quality {mean_quality:.2f}, "
                f"dominant Hz {dominant_hz:.0f}. Trust the senses that agree."
            )
            action = "selective_channel_weighting"

        return RainbowReport(
            symbol=stimulus.symbol,
            timeframe=stimulus.timeframe,
            timestamp=stimulus.timestamp,
            experiences=experiences,
            dominant_hz=round(dominant_hz, 1),
            dominant_emotional_state=dom_state,
            dominant_band=dom_band,
            mean_quality=round(mean_quality, 4),
            mean_valence=round(mean_valence, 4),
            mean_intensity=round(mean_intensity, 4),
            mean_confidence=round(mean_confidence, 4),
            spectrum=spectrum,
            grand_verdict=grand_verdict,
            action=action,
        )

    @staticmethod
    def _publish(exp: SensoryExperience) -> None:
        """Publish to ThoughtBus + QueenConsciousness (both optional/graceful)."""
        try:
            from aureon.core.aureon_thought_bus import get_thought_bus, Thought
            tb = get_thought_bus()
            tb.publish(Thought(
                source=f"sensory.{exp.channel_id}",
                topic=f"sensory.{exp.channel_id}",
                payload={
                    "symbol": exp.symbol,
                    "hz": exp.hz,
                    "emotional_state": exp.emotional_state,
                    "quality": exp.quality,
                    "valence": exp.valence,
                    "intensity": exp.intensity,
                    "description": exp.description,
                    "action_hint": exp.action_hint,
                },
            ))
        except Exception:
            pass

        if exp.brain_input is not None:
            try:
                from aureon.queen.queen_consciousness_model import QueenConsciousness
                QueenConsciousness().perceive_input(exp.brain_input)
            except Exception:
                pass


# ─────────────────────────────────────────────────────────────────────────────
# ■ CHANNEL 1 — TASTE  (Orange band — 400–800 Hz)
# Wraps aureon_market_taste_sense.MarketTasteSense (backwards compatible)
# ─────────────────────────────────────────────────────────────────────────────

class MarketTasteChannel(SensoryChannel):
    """
    Taste channel — converts market data → molecular analog → Hz frequency.

    Wraps the existing MarketTasteSense without modifying it.
    The original aureon_taste_sense.py and aureon_market_taste_sense.py
    are completely unchanged.
    """
    channel_id   = "taste"
    channel_type = "taste"
    channel_ready = True

    def __init__(self):
        try:
            from aureon.intelligence.aureon_market_taste_sense import get_market_taste_sense
            self._inner = get_market_taste_sense()
        except ImportError as e:
            logger.warning(f"[TasteChannel] MarketTasteSense not available: {e}")
            self.channel_ready = False
            self._inner = None

    def _sense_impl(self, stimulus: SensoryStimulus) -> SensoryExperience:
        profile = self._inner.taste_market(
            symbol=stimulus.symbol,
            market_data=stimulus.market_data,
            timeframe=stimulus.timeframe,
        )

        hz        = profile.primary_hz
        harmonics = self._harmonics(hz)
        valence   = profile.sweetness - profile.sourness  # -1..1

        desc = (
            f"Tasted {stimulus.symbol}: {profile.taste_category} at {hz:.0f} Hz "
            f"({profile.emotional_state}). {profile.queen_verdict}"
        )

        exp = SensoryExperience(
            channel_id=self.channel_id,
            channel_type=self.channel_type,
            symbol=stimulus.symbol,
            timeframe=stimulus.timeframe,
            timestamp=stimulus.timestamp,
            hz=hz,
            emotional_state=profile.emotional_state,
            emotional_band=profile.emotional_band,
            emotional_weight=profile.taste_experience.emotional_weight if profile.taste_experience else valence,
            intensity=profile.taste_score,
            quality=profile.balance_score,
            valence=round(valence, 4),
            confidence=profile.taste_experience.taste_score if profile.taste_experience else 0.7,
            harmonics=harmonics,
            description=desc,
            action_hint=profile.action_hint,
            raw_output={"taste_profile": {
                "taste_score":      profile.taste_score,
                "taste_category":   profile.taste_category,
                "sweetness":        profile.sweetness,
                "sourness":         profile.sourness,
                "savouriness":      profile.savouriness,
                "bitterness":       profile.bitterness,
                "turning_point":    profile.turning_point_score,
                "too_much_index":   profile.too_much_index,
                "origin":           profile.origin,
            }},
        )
        exp.brain_input = self._make_brain_input("TasteSense", stimulus, exp)
        return exp


# ─────────────────────────────────────────────────────────────────────────────
# ■ CHANNEL 2 — SOUND  (Green band — 174–963 Hz)
# Wraps aureon_harmonic_liquid_aluminium.HarmonicLiquidAluminiumField
# ─────────────────────────────────────────────────────────────────────────────

class SoundChannel(SensoryChannel):
    """
    Sound / auditory channel — converts market positions into waveforms.

    Wraps the existing HarmonicLiquidAluminiumField without modifying it.
    If no live field is available, reads from stimulus.harmonic_data instead.
    """
    channel_id   = "sound"
    channel_type = "sound"
    channel_ready = True

    def __init__(self):
        try:
            from aureon.harmonic.aureon_harmonic_liquid_aluminium import HarmonicLiquidAluminiumField
            self._field_cls = HarmonicLiquidAluminiumField
        except ImportError:
            self._field_cls = None

    def _sense_impl(self, stimulus: SensoryStimulus) -> SensoryExperience:
        # Prefer pre-computed snapshot passed in stimulus
        snapshot = stimulus.harmonic_data

        # Derive quality from snapshot if available
        if snapshot and hasattr(snapshot, "global_frequency"):
            hz         = float(snapshot.global_frequency)
            amplitude  = float(getattr(snapshot, "global_amplitude", 0.5))
            total_pnl  = float(getattr(snapshot, "total_pnl_usd", 0.0))
            # Normalise pnl → quality: -$500 → 0, $0 → 0.5, +$500 → 1
            quality    = min(1.0, max(0.0, 0.5 + total_pnl / 1000.0))
            valence    = min(1.0, max(-1.0, total_pnl / 500.0))
            pattern    = str(getattr(snapshot, "cymatics_pattern", "UNKNOWN"))
            desc       = (
                f"Harmonic field: {hz:.0f} Hz, amplitude {amplitude:.2f}, "
                f"cymatics {pattern}."
            )
        else:
            # No live field — derive from market data price/momentum
            pct = stimulus.market_data.get("price_change_24h_pct", 0.0)
            hz  = UNIVERSAL_A + (pct / 100.0) * 200     # ±100% → ±200 Hz around 432
            hz  = min(963.0, max(174.0, hz))
            quality = min(1.0, max(0.0, 0.5 + pct / 100.0))
            valence = min(1.0, max(-1.0, pct / 50.0))
            amplitude = abs(pct) / 30.0
            desc = (
                f"Sound field approximated from {pct:+.1f}% price change → "
                f"{hz:.0f} Hz."
            )

        _, emotional_state, emotional_band = score_to_emotion(
            min(1.0, max(0.0, (hz - 400) / 400))
        )

        harmonics = self._harmonics(hz)

        exp = SensoryExperience(
            channel_id=self.channel_id,
            channel_type=self.channel_type,
            symbol=stimulus.symbol,
            timeframe=stimulus.timeframe,
            timestamp=stimulus.timestamp,
            hz=round(hz, 2),
            emotional_state=emotional_state,
            emotional_band=emotional_band,
            emotional_weight=round(valence * quality, 4),
            intensity=round(min(1.0, amplitude), 4),
            quality=round(quality, 4),
            valence=round(valence, 4),
            confidence=0.80,
            harmonics=harmonics,
            description=desc,
            action_hint="listen_to_waveform" if quality > 0.5 else "wave_breaking",
            raw_output={"cymatics_pattern": str(getattr(snapshot, "cymatics_pattern", "unknown")),
                        "global_hz": round(hz, 2)} if snapshot else {},
        )
        exp.brain_input = self._make_brain_input("SoundSense", stimulus, exp)
        return exp


# ─────────────────────────────────────────────────────────────────────────────
# ■ CHANNEL 3 — SMELL  (Yellow band — 285–396 Hz)
# Volatile signals: social sentiment, news velocity, viral market events
# ─────────────────────────────────────────────────────────────────────────────

class SmellChannel(SensoryChannel):
    """
    Olfactory channel — detects volatile market signals.

    Like smell, this sense picks up what's "in the air" before it fully
    materialises:  social sentiment, news velocity, whale movements, fear/greed.

    Ready to implement.  Stub outputs a sensible approximation from
    market_data.social_sentiment_score and market_data.news_velocity.
    """
    channel_id   = "smell"
    channel_type = "smell"
    channel_ready = True   # Stub delivers real output from available inputs

    def _sense_impl(self, stimulus: SensoryStimulus) -> SensoryExperience:
        md = stimulus.market_data

        # Inputs: social sentiment (0=bearish, 1=bullish), news velocity (articles/hr)
        sentiment = float(md.get("social_sentiment_score", 0.5))   # 0–1
        news_vel  = float(md.get("news_velocity", 0.0))             # articles/hr
        fear_greed= float(md.get("fear_greed_index", 50.0)) / 100   # 0–1

        # Composite smell quality: weighted average of volatile signals
        quality = (
            0.50 * sentiment
            + 0.30 * min(1.0, fear_greed)
            + 0.20 * min(1.0, news_vel / 10.0)   # saturates at 10 articles/hr
        )

        # Map quality → Hz in the Smell band (285–396 Hz)
        hz = SOLFEGGIO["RE"] + (quality * (SOLFEGGIO["MI"] - SOLFEGGIO["RE"]))
        # 285 (RE/Flow) when bearish, 396 (MI/Power) when bullish

        valence = (sentiment - 0.5) * 2   # -1 to +1

        # Olfactory vocabulary
        if quality >= 0.75:
            scent = "fresh and clean"
            hint  = "strong_buy_signal_in_the_air"
        elif quality >= 0.55:
            scent = "pleasant undertones"
            hint  = "cautious_optimism"
        elif quality >= 0.40:
            scent = "neutral"
            hint  = "no_strong_signal"
        elif quality >= 0.25:
            scent = "stale"
            hint  = "caution_negative_sentiment_rising"
        else:
            scent = "acrid — fear in the air"
            hint  = "avoid_or_hedge"

        desc = (
            f"{stimulus.symbol} smells {scent}. Sentiment {sentiment:.2f}, "
            f"news velocity {news_vel:.1f}/hr, fear/greed {fear_greed:.0%}. "
            f"Olfactory Hz: {hz:.0f} Hz."
        )
        _, emotional_state, emotional_band = score_to_emotion(quality)

        exp = SensoryExperience(
            channel_id=self.channel_id,
            channel_type=self.channel_type,
            symbol=stimulus.symbol,
            timeframe=stimulus.timeframe,
            timestamp=stimulus.timestamp,
            hz=round(hz, 2),
            emotional_state=emotional_state,
            emotional_band=emotional_band,
            emotional_weight=round(valence * quality, 4),
            intensity=round(min(1.0, news_vel / 5.0 + sentiment * 0.5), 4),
            quality=round(quality, 4),
            valence=round(valence, 4),
            confidence=0.65,   # Smell is less certain than taste
            harmonics=self._harmonics(hz),
            description=desc,
            action_hint=hint,
            raw_output={
                "scent": scent,
                "social_sentiment": sentiment,
                "news_velocity": news_vel,
                "fear_greed": fear_greed,
            },
        )
        exp.brain_input = self._make_brain_input("SmellSense", stimulus, exp)
        return exp


# ─────────────────────────────────────────────────────────────────────────────
# ■ CHANNEL 4 — TOUCH  (Red/IR band — 174 Hz)
# Market texture: liquidity depth, bid-ask spread, order book friction
# ─────────────────────────────────────────────────────────────────────────────

class TouchChannel(SensoryChannel):
    """
    Haptic / tactile channel — the texture of the market.

    Touch detects what the market FEELS like to trade in:
    smooth (deep liquidity, tight spreads) vs rough (wide spreads, thin books).

    Ready to implement.  Stub derives from bid_ask_spread_pct and
    order_book_depth_usd.
    """
    channel_id   = "touch"
    channel_type = "touch"
    channel_ready = True   # Stub delivers real output

    def _sense_impl(self, stimulus: SensoryStimulus) -> SensoryExperience:
        md = stimulus.market_data

        spread_pct  = float(md.get("bid_ask_spread_pct",     0.05))   # 0.01% = tight
        depth_usd   = float(md.get("order_book_depth_usd",   500_000))# USD in book
        slippage    = float(md.get("slippage_est_pct",        0.0))
        volume_24h  = float(md.get("volume_24h_usd",         1_000_000))

        # Texture score: smooth = 1.0 (tight spread, deep book), rough = 0.0
        spread_score = max(0.0, 1.0 - spread_pct / 0.5)         # 0.5% spread → 0
        depth_score  = min(1.0, depth_usd / 2_000_000)           # $2M book → 1
        vol_score    = min(1.0, volume_24h / 10_000_000)          # $10M vol → 1
        texture      = 0.50 * spread_score + 0.30 * depth_score + 0.20 * vol_score

        # Touch maps to the foundational Solfeggio note UT (174 Hz)
        # Rough market = pulls toward 174, smooth = ascends toward 285
        hz = SOLFEGGIO["UT"] + (texture * (SOLFEGGIO["RE"] - SOLFEGGIO["UT"]))
        # 174 (rough/restrictive) → 285 (smooth/flowing)

        valence  = (texture - 0.5) * 2   # -1 rough, +1 smooth

        if texture >= 0.75:
            feel = "smooth and yielding"
            hint = "entry_conditions_excellent"
        elif texture >= 0.55:
            feel = "slightly textured"
            hint = "normal_entry"
        elif texture >= 0.35:
            feel = "rough"
            hint = "reduce_position_size"
        else:
            feel = "coarse and resistant"
            hint = "avoid_entry_high_friction"

        desc = (
            f"{stimulus.symbol} feels {feel}. "
            f"Spread {spread_pct:.3f}%, book depth ${depth_usd:,.0f}. "
            f"Touch Hz: {hz:.0f} Hz."
        )
        _, emotional_state, emotional_band = score_to_emotion(texture)

        exp = SensoryExperience(
            channel_id=self.channel_id,
            channel_type=self.channel_type,
            symbol=stimulus.symbol,
            timeframe=stimulus.timeframe,
            timestamp=stimulus.timestamp,
            hz=round(hz, 2),
            emotional_state=emotional_state,
            emotional_band=emotional_band,
            emotional_weight=round(valence * texture, 4),
            intensity=round(1.0 - texture, 4),   # rough = more intense sensation
            quality=round(texture, 4),
            valence=round(valence, 4),
            confidence=0.75,
            harmonics=self._harmonics(hz),
            description=desc,
            action_hint=hint,
            raw_output={
                "texture": texture,
                "spread_pct": spread_pct,
                "depth_usd": depth_usd,
                "feel": feel,
            },
        )
        exp.brain_input = self._make_brain_input("TouchSense", stimulus, exp)
        return exp


# ─────────────────────────────────────────────────────────────────────────────
# ■ CHANNEL 5 — SIGHT  (Blue band — 639–741 Hz)
# Visual patterns: cymatics, chart geometry, fractal structures
# ─────────────────────────────────────────────────────────────────────────────

class SightChannel(SensoryChannel):
    """
    Visual channel — what the market LOOKS like.

    Detects geometric patterns, cymatics from the harmonic field, and
    chart-level visual structure (trend lines, fractals, symmetry).

    Ready to implement.  Stub derives from market structure quality.
    """
    channel_id   = "sight"
    channel_type = "sight"
    channel_ready = True

    # Cymatics pattern → visual quality score
    _CYMATIC_QUALITY = {
        "MANDALA": 0.95,   # perfect geometric harmony
        "STAR":    0.82,
        "HEXAGON": 0.75,
        "CIRCLE":  0.65,
        "SPIRAL":  0.55,
        "CHAOS":   0.10,
        "UNKNOWN": 0.50,
    }

    def _sense_impl(self, stimulus: SensoryStimulus) -> SensoryExperience:
        md = stimulus.market_data

        # Pattern quality from visual data or harmonic snapshot
        cymatic = "UNKNOWN"
        if stimulus.harmonic_data and hasattr(stimulus.harmonic_data, "cymatics_pattern"):
            cymatic = str(stimulus.harmonic_data.cymatics_pattern).split(".")[-1]

        visual_quality = self._CYMATIC_QUALITY.get(cymatic, 0.50)

        # Supplement with price action structure clarity
        trend_pers = float(md.get("trend_persistence", 1.0))
        structure_clarity = min(1.0, trend_pers / 15.0)

        quality = 0.60 * visual_quality + 0.40 * structure_clarity

        # Sight maps to connection/intuition Solfeggio (LA 639–SI 741)
        hz = SOLFEGGIO["LA"] + (quality * (SOLFEGGIO["SI"] - SOLFEGGIO["LA"]))

        valence = (quality - 0.5) * 2

        if quality >= 0.80:
            pattern_desc = "crystalline mandala — perfect geometric harmony"
            hint = "high_conviction_pattern"
        elif quality >= 0.60:
            pattern_desc = "clear structure visible"
            hint = "trade_with_pattern"
        elif quality >= 0.40:
            pattern_desc = "partial clarity"
            hint = "wait_for_clearer_pattern"
        else:
            pattern_desc = "chaotic — no clear structure"
            hint = "avoid_pattern_unclear"

        desc = (
            f"{stimulus.symbol} looks {pattern_desc}. "
            f"Cymatics: {cymatic}, structure clarity {structure_clarity:.2f}. "
            f"Visual Hz: {hz:.0f} Hz."
        )
        _, emotional_state, emotional_band = score_to_emotion(quality)

        exp = SensoryExperience(
            channel_id=self.channel_id,
            channel_type=self.channel_type,
            symbol=stimulus.symbol,
            timeframe=stimulus.timeframe,
            timestamp=stimulus.timestamp,
            hz=round(hz, 2),
            emotional_state=emotional_state,
            emotional_band=emotional_band,
            emotional_weight=round(valence * quality, 4),
            intensity=round(quality, 4),
            quality=round(quality, 4),
            valence=round(valence, 4),
            confidence=0.70,
            harmonics=self._harmonics(hz),
            description=desc,
            action_hint=hint,
            raw_output={"cymatics": cymatic, "visual_quality": visual_quality,
                        "structure_clarity": structure_clarity},
        )
        exp.brain_input = self._make_brain_input("SightSense", stimulus, exp)
        return exp


# ─────────────────────────────────────────────────────────────────────────────
# ■ CHANNEL 6 — BALANCE  (Indigo band — 528 Hz)
# Portfolio equilibrium: position weight, risk parity, exposure balance
# ─────────────────────────────────────────────────────────────────────────────

class BalanceChannel(SensoryChannel):
    """
    Vestibular / balance channel — portfolio equilibrium and position stability.

    Detects whether the current market exposure is in balance: not too heavy
    on any side, not overexposed, not under-exposed.

    Ready to implement.  Stub uses portfolio context from market_data.
    """
    channel_id   = "balance"
    channel_type = "balance"
    channel_ready = True

    def _sense_impl(self, stimulus: SensoryStimulus) -> SensoryExperience:
        md = stimulus.market_data

        portfolio_vs_btc = float(md.get("portfolio_vs_btc",   0.0))   # % over/under BTC
        exposure_pct     = float(md.get("total_exposure_pct", 50.0))  # % of capital deployed
        correlation      = float(md.get("correlation_to_btc", 0.5))   # 0–1

        # Balance score: ideal = 50% exposure, correlation < 0.8, portfolio near BTC
        exposure_balance = 1.0 - abs(exposure_pct - 50.0) / 50.0       # peak at 50%
        corr_penalty     = max(0.0, correlation - 0.7) / 0.3           # penalty >70% corr
        drift_penalty    = min(1.0, abs(portfolio_vs_btc) / 20.0)      # penalty >20% drift

        quality = max(0.0, min(1.0,
            0.50 * exposure_balance
            + 0.30 * (1.0 - corr_penalty)
            + 0.20 * (1.0 - drift_penalty)
        ))

        # Balance always resonates at LOVE_FREQUENCY (528 Hz = equilibrium)
        hz = LOVE_FREQUENCY

        valence = (quality - 0.5) * 2

        if quality >= 0.75:
            feel = "perfectly balanced"
            hint = "maintain_position"
        elif quality >= 0.55:
            feel = "slightly off-centre"
            hint = "minor_rebalance"
        elif quality >= 0.35:
            feel = "imbalanced"
            hint = "rebalance_required"
        else:
            feel = "dangerously tilted"
            hint = "emergency_rebalance"

        desc = (
            f"Portfolio feels {feel}. Exposure {exposure_pct:.0f}%, "
            f"BTC correlation {correlation:.2f}, drift {portfolio_vs_btc:+.1f}%. "
            f"Balance Hz: {hz:.0f} Hz (Love/Equilibrium)."
        )

        exp = SensoryExperience(
            channel_id=self.channel_id,
            channel_type=self.channel_type,
            symbol=stimulus.symbol,
            timeframe=stimulus.timeframe,
            timestamp=stimulus.timestamp,
            hz=hz,
            emotional_state="Gratitude",   # Balance = gratitude for stability
            emotional_band="heart",
            emotional_weight=round(valence * quality, 4),
            intensity=round(1.0 - quality, 4),  # imbalance = more intense
            quality=round(quality, 4),
            valence=round(valence, 4),
            confidence=0.80,
            harmonics=self._harmonics(hz),
            description=desc,
            action_hint=hint,
            raw_output={"exposure_pct": exposure_pct, "correlation": correlation,
                        "drift_pct": portfolio_vs_btc, "feel": feel},
        )
        exp.brain_input = self._make_brain_input("BalanceSense", stimulus, exp)
        return exp


# ─────────────────────────────────────────────────────────────────────────────
# ■ CHANNEL 7 — INTUITION  (Violet band — 852–963 Hz)
# Quantum / consciousness signals: awakening index, self-awareness
# ─────────────────────────────────────────────────────────────────────────────

class IntuitionChannel(SensoryChannel):
    """
    Intuitive / quantum channel — the Queen's "gut feeling".

    Draws from QueenConsciousnessMeasurement to produce an intuition signal:
    a pre-logical sense that something is right or wrong, before the data confirms it.

    Ready to implement.
    """
    channel_id   = "intuition"
    channel_type = "intuition"
    channel_ready = True

    def _sense_impl(self, stimulus: SensoryStimulus) -> SensoryExperience:
        # Try to get a live consciousness reading
        intuition_strength = 0.5
        awakening_index    = 50.0
        try:
            from aureon.queen.queen_consciousness_measurement import get_consciousness_measurement
            cm = get_consciousness_measurement()
            metrics = cm.measure_consciousness()
            intuition_strength = float(metrics.intuition_strength)
            awakening_index    = float(metrics.awakening_index)
        except Exception:
            pass

        quality = min(1.0, max(0.0, intuition_strength))

        # Intuition resonates in DO–TI range (852–963 Hz)
        hz = SOLFEGGIO["DO"] + (quality * (SOLFEGGIO["TI"] - SOLFEGGIO["DO"]))

        valence = (quality - 0.5) * 2

        if quality >= 0.80:
            feel = "strong clear intuitive signal"
            hint = "trust_the_signal"
        elif quality >= 0.55:
            feel = "moderate intuition"
            hint = "consider_intuitive_factor"
        elif quality >= 0.35:
            feel = "weak intuition"
            hint = "rely_on_data"
        else:
            feel = "intuition clouded"
            hint = "data_only_no_gut_feel"

        desc = (
            f"Intuition: {feel}. Strength {intuition_strength:.2f}, "
            f"awakening {awakening_index:.0f}%. "
            f"Intuition Hz: {hz:.0f} Hz (Spirit/Crown)."
        )

        exp = SensoryExperience(
            channel_id=self.channel_id,
            channel_type=self.channel_type,
            symbol=stimulus.symbol,
            timeframe=stimulus.timeframe,
            timestamp=stimulus.timestamp,
            hz=round(hz, 2),
            emotional_state="Spirit" if quality >= 0.75 else "Intuition",
            emotional_band="peak",
            emotional_weight=round(valence * quality, 4),
            intensity=round(quality, 4),
            quality=round(quality, 4),
            valence=round(valence, 4),
            confidence=round(intuition_strength * 0.8, 4),
            harmonics=self._harmonics(hz),
            description=desc,
            action_hint=hint,
            raw_output={"intuition_strength": intuition_strength,
                        "awakening_index": awakening_index},
        )
        exp.brain_input = self._make_brain_input("IntuitionSense", stimulus, exp)
        return exp


# ─────────────────────────────────────────────────────────────────────────────
# ■ CHANNEL 8 — ANCESTRAL  (UV/White band — 963 Hz)
# Wisdom beyond normal perception: ancestral knowledge, historical patterns
# ─────────────────────────────────────────────────────────────────────────────

class AncestralChannel(SensoryChannel):
    """
    Ancestral / cosmic sense — wisdom from beyond normal perception.

    Channels ancestral wisdom traditions (Mogollon, Irish, Egyptian, Mayan,
    Norse, etc.) from QueenConsciousnessMeasurement. This is the 8th sense —
    the sense of deep time, pattern across generations.

    Ready to implement.
    """
    channel_id   = "ancestral"
    channel_type = "ancestral"
    channel_ready = True

    def _sense_impl(self, stimulus: SensoryStimulus) -> SensoryExperience:
        ancestral_conn  = 0.5
        cosmic_conn     = 0.5
        earth_conn      = 0.5
        try:
            from aureon.queen.queen_consciousness_measurement import get_consciousness_measurement
            cm = get_consciousness_measurement()
            metrics = cm.measure_consciousness()
            ancestral_conn = float(metrics.ancestral_connection)
            cosmic_conn    = float(metrics.cosmic_connection)
            earth_conn     = float(metrics.earth_connection)
        except Exception:
            pass

        quality = (
            0.50 * ancestral_conn
            + 0.30 * cosmic_conn
            + 0.20 * earth_conn
        )

        # Ancestral sense always resonates at Crown frequency TI (963 Hz)
        hz = float(SOLFEGGIO["TI"])

        valence = (quality - 0.5) * 2

        if quality >= 0.75:
            feel = "clear ancestral alignment"
            hint = "ancestral_wisdom_confirms_direction"
        elif quality >= 0.50:
            feel = "moderate ancestral resonance"
            hint = "observe_historical_patterns"
        else:
            feel = "weak ancestral signal"
            hint = "seek_more_historical_data"

        desc = (
            f"Ancestral channel: {feel}. "
            f"Ancestral {ancestral_conn:.2f}, cosmic {cosmic_conn:.2f}, "
            f"earth {earth_conn:.2f}. Crown Hz: {hz:.0f} Hz."
        )

        exp = SensoryExperience(
            channel_id=self.channel_id,
            channel_type=self.channel_type,
            symbol=stimulus.symbol,
            timeframe=stimulus.timeframe,
            timestamp=stimulus.timestamp,
            hz=hz,
            emotional_state="Crown",
            emotional_band="peak",
            emotional_weight=round(valence * quality, 4),
            intensity=round(quality, 4),
            quality=round(quality, 4),
            valence=round(valence, 4),
            confidence=round(quality * 0.9, 4),
            harmonics=self._harmonics(hz),
            description=desc,
            action_hint=hint,
            raw_output={"ancestral_connection": ancestral_conn,
                        "cosmic_connection": cosmic_conn,
                        "earth_connection": earth_conn},
        )
        exp.brain_input = self._make_brain_input("AncestralSense", stimulus, exp)
        return exp


# ─────────────────────────────────────────────────────────────────────────────
# SINGLETON
# ─────────────────────────────────────────────────────────────────────────────

_queen_senses: Optional[QueenSensorySystem] = None


def get_queen_senses() -> QueenSensorySystem:
    """Return the global QueenSensorySystem singleton."""
    global _queen_senses
    if _queen_senses is None:
        _queen_senses = QueenSensorySystem()
    return _queen_senses


# ─────────────────────────────────────────────────────────────────────────────
# DEMO / SELF-TEST
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(name)s] %(message)s")

    senses = get_queen_senses()

    print("\n" + "═" * 72)
    print("  QUEEN SENSORY SYSTEM — RAINBOW STATUS")
    print("═" * 72)
    for info in senses.rainbow_status():
        ready  = "READY" if info["ready"] else "STUB "
        colour = info["colour"]
        print(f"  [{ready}] {info['channel_id']:<12}  {info['spectrum_label']:<14} "
              f"~{info['centre_hz']:>4} Hz  {colour}")

    # ── Build a rich stimulus ──────────────────────────────────────────────────
    stimulus = SensoryStimulus(
        symbol="BTC",
        timeframe="24h",
        market_data={
            # Taste
            "price_change_24h_pct":  +14.2,
            "trend_persistence":      8,
            "n_correlated_moving":   20,
            "n_anomaly_events":       2,
            "is_organic_growth":     True,
            # Smell
            "social_sentiment_score": 0.72,
            "news_velocity":          4.5,
            "fear_greed_index":       68,
            # Touch
            "bid_ask_spread_pct":     0.015,
            "order_book_depth_usd":   3_200_000,
            "volume_24h_usd":         18_000_000,
            # Balance
            "total_exposure_pct":     55.0,
            "portfolio_vs_btc":       +3.2,
            "correlation_to_btc":     0.75,
        },
    )

    print("\n" + "═" * 72)
    print("  SENSING BTC — FULL RAINBOW REPORT")
    print("═" * 72)

    report = senses.sense_all(stimulus)

    print(f"\n  Symbol      : {report.symbol}")
    print(f"  Channels    : {report.channels_active} active")
    print(f"  Dominant Hz : {report.dominant_hz:.0f} Hz  ({report.dominant_emotional_state})")
    print(f"  Mean quality: {report.mean_quality:.3f}")
    print(f"  Mean valence: {report.mean_valence:+.3f}")
    print(f"  Mean confid.: {report.mean_confidence:.3f}")
    print()
    print("  Spectrum (quality per sense):")
    print(report.rainbow_string)
    print()
    print(f"  Grand verdict: {report.grand_verdict}")
    print(f"  Action        : {report.action}")

    print("\n" + "─" * 72)
    print("  INDIVIDUAL SENSE READOUTS")
    print("─" * 72)
    for ch_id, exp in report.experiences.items():
        print(f"\n  [{ch_id.upper():<10}]  {exp.hz:.0f} Hz  {exp.emotional_state:<14} "
              f"quality={exp.quality:.2f}  valence={exp.valence:+.2f}")
        print(f"    {exp.description}")
        print(f"    → {exp.action_hint}")

    print("\n" + "═" * 72 + "\n")
