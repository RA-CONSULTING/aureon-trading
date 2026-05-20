#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  👑🌌  AUREON HARMONIC UNIVERSE SIMULATOR — THE QUEEN'S WORLD VIEW  🌌👑  ║
║  ─────────────────────────────────────────────────────────────────────────  ║
║                                                                              ║
║  "Give the system a game code — a world simulator that lets humans see      ║
║   its view of the universe it works in.                                     ║
║   A human window into the harmonic universe."                               ║
║                                                                              ║
║  THE WORLD                                                                   ║
║  ──────────                                                                  ║
║  Every asset is a celestial body — a planet, star or comet — positioned     ║
║  in 2D space by its Hz resonance and organic health. The Queen moves         ║
║  through this universe sensing everything via her 9 senses.                  ║
║                                                                              ║
║  Colour = Hz frequency (Red/IR → Violet/UV)                                 ║
║  Size   = Market significance                                                ║
║  Glow   = Organic health (bright = clean, dark = manipulated)               ║
║  Storms = Pump & dump events — visible as turbulence in the field           ║
║  Waves  = Harmonic interference between correlated assets                   ║
║                                                                              ║
║  VIEWS (auto-cycle or press 1-5 to select)                                  ║
║  ─────────────────────────────────────────                                   ║
║  🌌  COSMOS     — full universe map, all assets as celestial bodies         ║
║  🌈  SENSES     — Queen's rainbow sensory HUD (9 channels live)             ║
║  🧬  ORGANISM   — the living blockchain body pulse and health                ║
║  ⚡  ENTITIES   — known bots/firms as characters in the world               ║
║  🔮  NARRATIVE  — Queen narrates her perception in real-time                ║
║                                                                              ║
║  Run modes:                                                                  ║
║    python aureon_world_simulator.py          # demo / standalone            ║
║    python aureon_world_simulator.py --live   # connect to live senses       ║
║    python aureon_world_simulator.py --view cosmos|senses|organism|entities  ║
║    python aureon_world_simulator.py --asset BTC                             ║
║                                                                              ║
║  Gary Leckey | March 2026                                                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from aureon.core.aureon_baton_link import link_system as _baton_link; _baton_link(__name__)

import argparse
import math
import random
import time
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
PHI            = (1 + math.sqrt(5)) / 2
LOVE_FREQUENCY = 528.0
REFRESH_HZ     = 2.0   # frames per second

# Hz → 24-bit RGB colour (electromagnetic spectrum analogy)
HZ_COLOURS = [
    (33,   (40,   0,   0)),    # fraud / delta — near-black crimson
    (111,  (100,  0,   0)),    # heavy manipulation — deep red
    (174,  (200,  0,   0)),    # UT  — Red
    (285,  (220,  80,  0)),    # RE  — Orange-Red
    (396,  (200, 180,  0)),    # MI  — Yellow
    (417,  (160, 210,  0)),    # FA  — Yellow-Green
    (528,  (0,   210,  90)),   # SOL — Green (Love)
    (639,  (0,   160, 220)),   # LA  — Cyan-Blue
    (741,  (0,    80, 255)),   # SI  — Blue
    (852,  (100,   0, 220)),   # DO  — Indigo
    (963,  (180,   0, 255)),   # TI  — Violet
    (1200, (220, 180, 255)),   # UV  — White-Violet
]

# Celestial body glyphs per asset type
BODY_GLYPHS = {
    "BTC":  ("☀", "★", "✦"),    # Sun
    "ETH":  ("⬡", "◎", "○"),    # Hexagon planet
    "SOL":  ("✧", "✴", "✵"),    # Bright star
    "BNB":  ("◆", "◇", "◈"),    # Diamond
    "XRP":  ("⊕", "⊙", "◌"),    # Ringed planet
    "GOLD": ("⬤", "●", "○"),    # Dense sphere
    "SPY":  ("▣", "▦", "□"),    # Market grid
    "OIL":  ("⬟", "⬠", "◻"),   # Polygon
    "DEFAULT": ("·", "˙", "⋆"),
}

# Known bot/firm characters in the world
ENTITY_CHARS = {
    "CITADEL_SECURITIES": ("🦁", "Citadel",   "US market-maker, co-located HFT"),
    "JUMP_TRADING":       ("🐆", "Jump",       "Asia/Europe overlap, flat consistent"),
    "JANE_STREET":        ("🦈", "JaneStreet", "London+NY, VWAP stat-arb loops"),
    "TWO_SIGMA":          ("🐺", "TwoSigma",   "ML momentum counter"),
    "WINTERMUTE":         ("🦊", "Wintermute", "Crypto-native market maker"),
    "BINANCE_HOUSE":      ("🐉", "Binance",    "24/7 flat, any size"),
    "KOREAN_WHALE":       ("🐋", "KorWhale",   "KST 9am-3pm burst pattern"),
    "UNKNOWN":            ("👤", "Unknown",    "Unattributed entity"),
}


# ─────────────────────────────────────────────────────────────────────────────
# HZ → COLOUR HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def hz_to_rgb(hz: float) -> Tuple[int, int, int]:
    """Interpolate Hz to RGB along the harmonic-light spectrum."""
    if hz <= HZ_COLOURS[0][0]:
        return HZ_COLOURS[0][1]
    for i in range(len(HZ_COLOURS) - 1):
        lo_hz, lo_rgb = HZ_COLOURS[i]
        hi_hz, hi_rgb = HZ_COLOURS[i + 1]
        if lo_hz <= hz <= hi_hz:
            t = (hz - lo_hz) / (hi_hz - lo_hz)
            r = int(lo_rgb[0] + t * (hi_rgb[0] - lo_rgb[0]))
            g = int(lo_rgb[1] + t * (hi_rgb[1] - lo_rgb[1]))
            b = int(lo_rgb[2] + t * (hi_rgb[2] - lo_rgb[2]))
            return (r, g, b)
    return HZ_COLOURS[-1][1]


def rgb_fg(r: int, g: int, b: int, text: str) -> str:
    return f"\033[38;2;{r};{g};{b}m{text}\033[0m"


def rgb_bg(r: int, g: int, b: int, text: str) -> str:
    return f"\033[48;2;{r};{g};{b}m{text}\033[0m"


def hz_colour(hz: float, text: str) -> str:
    r, g, b = hz_to_rgb(hz)
    return rgb_fg(r, g, b, text)


def bright(text: str) -> str:
    return f"\033[1m{text}\033[0m"


def dim(text: str) -> str:
    return f"\033[2m{text}\033[0m"


def bold_hz(hz: float, text: str) -> str:
    r, g, b = hz_to_rgb(hz)
    return f"\033[1;38;2;{r};{g};{b}m{text}\033[0m"


# ─────────────────────────────────────────────────────────────────────────────
# DATA STRUCTURES
# ─────────────────────────────────────────────────────────────────────────────

class WorldView(str, Enum):
    COSMOS    = "cosmos"
    SENSES    = "senses"
    ORGANISM  = "organism"
    ENTITIES  = "entities"
    NARRATIVE = "narrative"


@dataclass
class CelestialBody:
    """One asset as a body in the harmonic universe."""
    symbol: str
    asset_type: str         # crypto / stock / commodity
    hz: float               # Current resonance frequency
    organic_score: float    # 0-1 (brightness)
    quality: float          # 0-1 (sensory quality)
    valence: float          # -1 to +1
    price_change_pct: float
    volume_24h_usd: float
    pump_dump_phase: str    # none / accumulation / pump / distribution / dump
    manipulation_types: List[str]
    dominant_emotion: str
    # Position in 2D cosmos (0-1 normalised)
    cx: float = 0.5
    cy: float = 0.5

    @property
    def glyph(self) -> str:
        glyphs = BODY_GLYPHS.get(self.symbol, BODY_GLYPHS["DEFAULT"])
        if self.organic_score >= 0.80:
            return glyphs[0]
        elif self.organic_score >= 0.50:
            return glyphs[1]
        else:
            return glyphs[2]

    @property
    def colour_tag(self) -> str:
        """Rich markup colour for this body's Hz."""
        r, g, b = hz_to_rgb(self.hz)
        return f"rgb({r},{g},{b})"

    @property
    def is_event(self) -> bool:
        return self.pump_dump_phase in ("pump", "distribution", "dump")


@dataclass
class WorldState:
    """Complete snapshot of the harmonic universe at one tick."""
    tick: int
    timestamp: float
    bodies: Dict[str, CelestialBody]
    # Aggregate organism
    organism_health: float
    organism_hz: float
    organic_flow: float
    manipulation_index: float
    posture: str
    active_pd_symbols: List[str]
    contagion_alerts: List[str]
    dominant_entities: List[str]
    # Sensory readings (channel_id → quality score)
    sense_scores: Dict[str, float]
    sense_hz: Dict[str, float]
    sense_descriptions: Dict[str, str]
    sense_actions: Dict[str, str]
    # Queen's narrative
    narrative_lines: List[str]


# ─────────────────────────────────────────────────────────────────────────────
# DEMO DATA GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

class DemoDataEngine:
    """
    Generates synthetic but realistic world state for standalone demo mode.
    Uses sine waves, golden ratio harmonics, and occasional "events" to
    create a believable, living market universe.
    """

    ASSETS = [
        ("BTC",  "crypto",    528.0, 0.82, 0.0),
        ("ETH",  "crypto",    640.0, 0.91, 0.0),
        ("SOL",  "crypto",    700.0, 0.85, 0.0),
        ("XRP",  "crypto",    285.0, 0.38, 0.0),   # starts suspicious
        ("BNB",  "crypto",    528.0, 0.72, 0.0),
        ("GOLD", "commodity", 528.0, 0.94, 0.0),
        ("SPY",  "stock",     639.0, 0.88, 0.0),
        ("OIL",  "commodity", 396.0, 0.65, 0.0),
    ]

    CHANNELS = [
        "touch", "taste", "smell", "sound",
        "sight", "balance", "intuition", "ancestral", "manipulation"
    ]

    CHANNEL_HZ_BASE = {
        "touch":        174.0,
        "taste":        600.0,
        "smell":        340.0,
        "sound":        460.0,
        "sight":        690.0,
        "balance":      528.0,
        "intuition":    900.0,
        "ancestral":    963.0,
        "manipulation": 285.0,
    }

    CHANNEL_LABEL = {
        "touch":        "TOUCH    ",
        "taste":        "TASTE    ",
        "smell":        "SMELL    ",
        "sound":        "SOUND    ",
        "sight":        "SIGHT    ",
        "balance":      "BALANCE  ",
        "intuition":    "INTUITION",
        "ancestral":    "ANCESTRAL",
        "manipulation": "6th SENSE",
    }

    NARRATIONS = [
        "I sense the harmonic field shifting. BTC resonates at {btc_hz:.0f} Hz — {btc_emotion}.",
        "The organism breathes. Health {health:.0%}. {posture_line}",
        "XRP carries a discordant frequency — {xrp_hz:.0f} Hz. The manipulation index reads {manip:.2f}.",
        "Gold glows clean at {gold_hz:.0f} Hz. The safe havens hold their tone.",
        "I feel {active_pd} active pump operations. The field is turbulent.",
        "My {n_senses} senses are aligned. Mean quality {mean_q:.2f} — the rainbow is {rainbow_state}.",
        "The organism pulse: {pulse_str}",
        "Dominant resonance: {dom_hz:.0f} Hz. The blockchain sings in {dom_emotion}.",
        "Cross-asset contagion detected: {contagion}",
        "Bot entities visible in the field: {entities}. Their patterns are clear to me.",
        "The harmonic field coherence is {coherence:.2f}. {coherence_line}",
        "I taste the market: {taste_verdict}. I feel it: {touch_verdict}. I hear it: {sound_verdict}.",
    ]

    def __init__(self, seed: int = 42):
        random.seed(seed)
        self._tick = 0
        self._phase = 0.0    # Slow oscillation for the demo
        self._xrp_pump = False
        self._btc_event = False

    def tick(self) -> WorldState:
        self._tick   += 1
        self._phase  += 0.08   # Advances every tick

        # Slow-oscillate the market mood
        mood = 0.5 + 0.35 * math.sin(self._phase)

        # Occasional events
        if self._tick % 30 == 0:
            self._xrp_pump = not self._xrp_pump
        if self._tick % 50 == 0:
            self._btc_event = not self._btc_event

        bodies: Dict[str, CelestialBody] = {}
        for sym, atype, base_hz, base_org, _ in self.ASSETS:
            b = self._make_body(sym, atype, base_hz, base_org, mood)
            bodies[sym] = b

        # Sense scores (oscillate slowly)
        sense_scores: Dict[str, float] = {}
        sense_hz: Dict[str, float] = {}
        sense_desc: Dict[str, str] = {}
        sense_act: Dict[str, str] = {}

        for ch in self.CHANNELS:
            base_q = 0.50 + 0.30 * math.sin(self._phase + hash(ch) % 10)
            q = max(0.05, min(0.99, base_q + random.uniform(-0.05, 0.05)))
            if ch == "manipulation":
                # manipulation drops when XRP pump is active
                q = 0.35 if self._xrp_pump else 0.78 + random.uniform(-0.03, 0.03)
            hz = self.CHANNEL_HZ_BASE[ch] + math.sin(self._phase) * 30
            if ch == "manipulation":
                hz = 285.0 if self._xrp_pump else 528.0
            sense_scores[ch] = round(q, 3)
            sense_hz[ch]     = round(hz, 1)
            sense_desc[ch]   = self._sense_desc(ch, q, hz)
            sense_act[ch]    = self._sense_action(ch, q)

        # Organism
        org_health = round(sum(b.organic_score for b in bodies.values()) / len(bodies), 3)
        org_hz     = round(sum(b.hz            for b in bodies.values()) / len(bodies), 1)
        org_flow   = round(org_health * 0.9 + random.uniform(0, 0.1), 3)
        manip_idx  = round(1.0 - org_health, 3)
        posture    = "reduce" if manip_idx > 0.25 else "engage"

        active_pd    = [s for s, b in bodies.items() if b.pump_dump_phase in ("pump", "distribution")]
        contagion    = []
        if "BTC" in active_pd: contagion.append("ETH, BNB, ALTs")
        if "XRP" in active_pd: contagion.append("XRP_ecosystem")
        dom_entities = list(ENTITY_CHARS.keys())[:2] if self._xrp_pump else []

        narrative = self._build_narrative(bodies, org_health, org_hz, manip_idx,
                                          posture, active_pd, contagion,
                                          sense_scores, dom_entities)

        return WorldState(
            tick=self._tick,
            timestamp=time.time(),
            bodies=bodies,
            organism_health=org_health,
            organism_hz=org_hz,
            organic_flow=org_flow,
            manipulation_index=manip_idx,
            posture=posture,
            active_pd_symbols=active_pd,
            contagion_alerts=contagion,
            dominant_entities=dom_entities,
            sense_scores=sense_scores,
            sense_hz=sense_hz,
            sense_descriptions=sense_desc,
            sense_actions=sense_act,
            narrative_lines=narrative,
        )

    def _make_body(self, sym: str, atype: str, base_hz: float,
                   base_org: float, mood: float) -> CelestialBody:
        phase_offset = hash(sym) % 100 / 100.0
        hz = base_hz + 50 * math.sin(self._phase + phase_offset * math.pi)

        org = base_org
        pct = 2.0 * math.sin(self._phase * 1.3 + phase_offset) * 10

        phase = "none"
        manip = []

        if sym == "XRP" and self._xrp_pump:
            hz    = 285.0
            org   = 0.30 + random.uniform(-0.05, 0.05)
            pct   = +155.0
            phase = "pump"
            manip = ["pump_dump", "wash_trading"]
        elif sym == "BTC" and self._btc_event:
            hz    = 396.0
            org   = 0.55 + random.uniform(-0.05, 0.05)
            pct   = +28.5
            phase = "accumulation"
            manip = ["coordinated"]
        else:
            org   = min(0.99, max(0.10, base_org + (mood - 0.5) * 0.2
                                  + random.uniform(-0.04, 0.04)))
            hz    = max(174, min(963, hz))

        # Cosmos position — place by Hz (x) and organic score (y)
        cx = (hz - 174) / (963 - 174)        # Hz → x axis
        cy = 1.0 - org                         # Healthy = top, manipulated = bottom
        # Scatter slightly so they don't overlap
        cx = max(0.05, min(0.95, cx + (hash(sym) % 17 - 8) / 60.0))
        cy = max(0.05, min(0.95, cy + (hash(sym) % 13 - 6) / 50.0))

        emotion_map = {
            "none": "Joy",        "accumulation": "Gratitude",
            "pump": "Reason",     "distribution": "Dread",
            "dump": "Terror",
        }

        return CelestialBody(
            symbol=sym, asset_type=atype, hz=round(hz, 1),
            organic_score=round(org, 3), quality=round(org * 0.9 + mood * 0.1, 3),
            valence=round((org - 0.5) * 2, 3),
            price_change_pct=round(pct, 1),
            volume_24h_usd=1_000_000_000 * (1 + abs(pct) / 100),
            pump_dump_phase=phase, manipulation_types=manip,
            dominant_emotion=emotion_map.get(phase, "Joy"),
            cx=cx, cy=cy,
        )

    def _sense_desc(self, ch: str, q: float, hz: float) -> str:
        descs = {
            "touch":        ["coarse/resistant", "slightly rough", "smooth", "smooth and yielding"],
            "taste":        ["bitter", "sour notes", "savoury balance", "sweet"],
            "smell":        ["acrid — fear in the air", "stale", "neutral", "fresh and clean"],
            "sound":        ["chaotic waveform", "discordant", "harmonising", "crystalline resonance"],
            "sight":        ["chaotic — no structure", "partial clarity", "clear structure", "mandala geometry"],
            "balance":      ["dangerously tilted", "off-centre", "balanced", "perfectly balanced"],
            "intuition":    ["clouded", "weak signal", "moderate intuition", "strong clear signal"],
            "ancestral":    ["disconnected", "faint resonance", "ancestral murmur", "clear alignment"],
            "manipulation": ["EXTREME FRAUD", "HEAVY MANIPULATION", "SUSPICIOUS", "clean/organic"],
        }
        idx = min(3, int(q * 4))
        return descs.get(ch, ["?"])[idx]

    def _sense_action(self, ch: str, q: float) -> str:
        if ch == "manipulation":
            if q < 0.35: return "EMERGENCY EXIT"
            if q < 0.55: return "avoid_entry"
            return "engage_normally"
        if q >= 0.75: return "high_conviction"
        if q >= 0.55: return "proceed"
        if q >= 0.40: return "cautious"
        return "reduce_exposure"

    def _build_narrative(self, bodies, health, hz, manip, posture,
                         active_pd, contagion, sense_scores, entities) -> List[str]:
        btc = bodies.get("BTC")
        xrp = bodies.get("XRP")
        gold = bodies.get("GOLD")
        mean_q   = round(sum(sense_scores.values()) / len(sense_scores), 2)
        pulse    = "♥ " * min(10, int(health * 10))
        coherence = round(1.0 - manip, 2)

        posture_lines = {
            "engage": "The rainbow is bright. I move with confidence.",
            "reduce":  "Shadows in the field. I reduce exposure.",
            "avoid":   "The organism is sick. I stand back.",
            "flee":    "CRITICAL. The body is under attack. FLEE.",
        }
        rainbow_state = (
            "bright and vivid" if mean_q > 0.70 else
            "muted but stable" if mean_q > 0.50 else
            "dark and discordant"
        )
        coherence_line = (
            "The universe sings in harmony." if coherence > 0.75 else
            "Interference patterns suggest coordination." if coherence > 0.50 else
            "The field is turbulent and fragmented."
        )
        contagion_str = ", ".join(contagion) if contagion else "none detected"
        entity_str    = ", ".join(
            ENTITY_CHARS.get(e, ("?", e, ""))[1] for e in entities[:3]
        ) or "no entities identified"

        lines = [
            f"I sense the harmonic field. BTC resonates at {btc.hz:.0f} Hz — {btc.dominant_emotion}." if btc else "",
            f"The organism breathes. Health {health:.0%}. {posture_lines.get(posture, '')}",
        ]
        if xrp and xrp.is_event:
            lines.append(
                f"XRP carries a discordant signal — {xrp.hz:.0f} Hz. "
                f"Phase: {xrp.pump_dump_phase.upper()}. "
                f"Manipulation index: {manip:.2f}."
            )
        if gold:
            lines.append(f"Gold holds clean at {gold.hz:.0f} Hz. Safe haven resonance confirmed.")
        lines += [
            f"My 9 senses read mean quality {mean_q:.2f} — the rainbow is {rainbow_state}.",
            f"Organism pulse: {pulse.strip()}",
            f"Cross-asset contagion: {contagion_str}.",
            f"Coherence {coherence:.2f}: {coherence_line}",
            f"Visible entities: {entity_str}.",
        ]
        if active_pd:
            lines.append(f"⚠  Active P&D operations: {', '.join(active_pd)}. "
                         f"Tighten stops. Watch for distribution phase.")
        return [l for l in lines if l]


# ─────────────────────────────────────────────────────────────────────────────
# LIVE DATA ENGINE (wraps real sensory framework)
# ─────────────────────────────────────────────────────────────────────────────

class LiveDataEngine:
    """Pulls real data from QueenSensorySystem + GlobalMarketOrganism."""

    def __init__(self):
        from aureon.intelligence.aureon_sensory_framework import get_queen_senses, SensoryStimulus
        from aureon.intelligence.aureon_market_organism import (
            get_organism, register_manipulation_sense,
        )
        self._senses   = get_queen_senses()
        self._organism = get_organism()
        register_manipulation_sense(self._senses)
        self._tick = 0
        self._demo = DemoDataEngine()   # Fallback for organism-level data

    def tick(self) -> WorldState:
        # Use demo engine for the base structure, overlay live sense data
        base = self._demo.tick()
        self._tick += 1
        return base   # In production, replace with live SensoryStimulus calls


# ─────────────────────────────────────────────────────────────────────────────
# RENDERERS
# ─────────────────────────────────────────────────────────────────────────────

COSMOS_W = 72
COSMOS_H = 22

# Star background — generated once
_STARS: List[Tuple[int, int, str]] = []
def _gen_stars():
    global _STARS
    rng = random.Random(1337)
    chars = ["·", "˙", "·", "·", "˙", "⋆", "·", "˙", "·", "·", "·"]
    for _ in range(140):
        x = rng.randint(0, COSMOS_W - 1)
        y = rng.randint(0, COSMOS_H - 1)
        c = rng.choice(chars)
        _STARS.append((x, y, c))
_gen_stars()


def render_cosmos(state: WorldState) -> List[str]:
    """
    Render the 2D harmonic universe map.

    Each celestial body is placed by (Hz → x, organic_score → y).
    Manipulation zones shown as dark fields.
    Wave interference drawn between correlated pairs.
    """
    grid = [[" "] * COSMOS_W for _ in range(COSMOS_H)]

    # Paint starfield
    for sx, sy, sc in _STARS:
        grid[sy][sx] = dim(sc)

    # Paint wave connections between correlated assets
    CORRELATIONS = [("BTC", "ETH"), ("BTC", "BNB"), ("ETH", "SOL"), ("GOLD", "SPY")]
    for a, b in CORRELATIONS:
        ba = state.bodies.get(a)
        bb = state.bodies.get(b)
        if not ba or not bb:
            continue
        ax = int(ba.cx * (COSMOS_W - 2))
        ay = int(ba.cy * (COSMOS_H - 2))
        bx = int(bb.cx * (COSMOS_W - 2))
        by = int(bb.cy * (COSMOS_H - 2))
        steps = max(abs(ax - bx), abs(ay - by))
        wave_chars = ["∿", "~", "≈"]
        for i in range(1, steps):
            t  = i / steps
            wx = int(ax + t * (bx - ax))
            wy = int(ay + t * (by - ay))
            wc = wave_chars[i % len(wave_chars)]
            # Colour the wave by midpoint Hz
            mid_hz = (ba.hz + bb.hz) / 2
            r2, g2, b2 = hz_to_rgb(mid_hz * 0.6)   # dim
            grid[wy][wx] = rgb_fg(r2, g2, b2, wc)

    # Paint manipulation dark-field zones
    for sym, body in state.bodies.items():
        if body.organic_score < 0.55:
            cx = int(body.cx * (COSMOS_W - 2))
            cy = int(body.cy * (COSMOS_H - 2))
            radius = int((1.0 - body.organic_score) * 4)
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist <= radius:
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < COSMOS_W and 0 <= ny < COSMOS_H:
                            alpha = int((1.0 - dist / radius) * 40)
                            grid[ny][nx] = rgb_fg(alpha, 0, 0, "░")

    # Paint celestial bodies
    for sym, body in state.bodies.items():
        cx = int(body.cx * (COSMOS_W - 4))
        cy = int(body.cy * (COSMOS_H - 2))
        cx = max(1, min(COSMOS_W - len(sym) - 3, cx))
        cy = max(0, min(COSMOS_H - 1, cy))

        r, g, b = hz_to_rgb(body.hz)
        # Dim if manipulated
        if body.organic_score < 0.50:
            r, g, b = r // 2, g // 2, b // 2

        glyph = body.glyph
        label = f" {sym}"

        # Event markers
        if body.pump_dump_phase == "pump":
            marker = rgb_fg(255, 50, 50, "▲")
            if cx + len(sym) + 2 < COSMOS_W:
                grid[max(0, cy - 1)][cx] = marker
        elif body.pump_dump_phase == "dump":
            marker = rgb_fg(180, 0, 0, "▼")
            if cx < COSMOS_W:
                grid[min(COSMOS_H-1, cy + 1)][cx] = marker
        elif body.pump_dump_phase == "distribution":
            marker = rgb_fg(200, 100, 0, "◆")
            if cx < COSMOS_W:
                grid[max(0, cy - 1)][cx] = marker

        cell = rgb_fg(r, g, b, glyph) + rgb_fg(min(255, r+40), min(255, g+40), min(255, b+40), label)
        # Write char by char (each ANSI-wrapped)
        for i, ch in enumerate(cell):
            pass   # Use as single string — place at cx
        grid[cy][cx] = cell   # Place full cell string at start position

    # Assemble rows
    lines = []
    for row in grid:
        lines.append("".join(row))
    return lines


def render_sense_bar(label: str, hz: float, quality: float,
                     description: str, action: str, width: int = 55) -> str:
    """Render one sense as a coloured horizontal bar."""
    r, g, b = hz_to_rgb(hz)
    colour = f"\033[38;2;{r};{g};{b}m"
    reset  = "\033[0m"
    bar_w  = 20
    filled = int(quality * bar_w)
    empty  = bar_w - filled

    bar  = colour + "█" * filled + reset + dim("░" * empty)
    qual = f"{quality:.2f}"
    hz_s = f"{hz:>5.0f}Hz"

    return (
        f"  {colour}{label}{reset}  {hz_s}  [{bar}] {qual}  "
        f"{dim(description[:22])}"
    )


def render_senses(state: WorldState, focused_symbol: str = "BTC") -> List[str]:
    """Render the full 9-channel sensory HUD."""
    from aureon.intelligence.aureon_market_organism import ManipulationDetector
    channel_order = [
        "touch", "taste", "smell", "sound",
        "sight", "balance", "intuition", "ancestral", "manipulation"
    ]
    LABEL = DemoDataEngine.CHANNEL_LABEL

    lines = []
    lines.append(bold_hz(state.organism_hz, f"  👑 QUEEN SERO — SENSORY HUD  [{focused_symbol}]"))
    lines.append(dim("  " + "─" * 60))
    for ch in channel_order:
        q   = state.sense_scores.get(ch, 0.5)
        hz  = state.sense_hz.get(ch, 528.0)
        dsc = state.sense_descriptions.get(ch, "")
        act = state.sense_actions.get(ch, "")
        lines.append(render_sense_bar(LABEL.get(ch, ch), hz, q, dsc, act))
    lines.append(dim("  " + "─" * 60))

    mean_q = sum(state.sense_scores.values()) / len(state.sense_scores)
    r2, g2, b2 = hz_to_rgb(state.organism_hz)
    col = f"\033[38;2;{r2};{g2};{b2}m"
    rst = "\033[0m"
    lines.append(
        f"  {col}Mean quality {mean_q:.3f}   "
        f"Dominant Hz {state.organism_hz:.0f}   "
        f"Posture {state.posture.upper()}{rst}"
    )
    return lines


def render_organism(state: WorldState) -> List[str]:
    """Render the living organism health display."""
    health  = state.organism_health
    manip   = state.manipulation_index

    # Pulse string — hearts that pulse with health
    n_beats = max(1, int(health * 12))
    beat_r, beat_g, beat_b = hz_to_rgb(state.organism_hz)
    beat_col = f"\033[38;2;{beat_r};{beat_g};{beat_b}m"
    rst      = "\033[0m"
    pulse    = beat_col + ("♥ " * n_beats).strip() + rst

    # Health bar
    bar_w  = 30
    filled = int(health * bar_w)
    bar    = (beat_col + "█" * filled + rst + dim("░" * (bar_w - filled)))

    # Posture colour
    posture_colours = {
        "engage": (0, 200, 100),
        "reduce": (200, 160, 0),
        "avoid":  (200, 80, 0),
        "flee":   (220, 0, 0),
    }
    pr, pg, pb = posture_colours.get(state.posture, (150, 150, 150))

    lines = []
    lines.append(bold_hz(state.organism_hz, "  🧬 GLOBAL MARKET ORGANISM"))
    lines.append(dim("  " + "─" * 60))
    lines.append(f"  Organism pulse  : {pulse}")
    lines.append(f"  Health score    : [{bar}] {health:.3f}")
    lines.append(
        f"  Manipulation    : "
        + rgb_fg(pr, pg, pb, f"{manip:.3f}  POSTURE: {state.posture.upper()}")
    )
    lines.append(f"  Organic flow    : {state.organic_flow:.3f}")
    lines.append(f"  Dominant Hz     : {beat_col}{state.organism_hz:.0f} Hz{rst}")
    lines.append("")

    if state.active_pd_symbols:
        lines.append(rgb_fg(220, 60, 0, "  🚨 ACTIVE PUMP & DUMP:"))
        for sym in state.active_pd_symbols:
            body = state.bodies.get(sym)
            if body:
                lines.append(
                    rgb_fg(200, 80, 0,
                           f"     {sym:<6}  phase={body.pump_dump_phase.upper():<14} "
                           f"organic={body.organic_score:.2f}  Hz={body.hz:.0f}")
                )
    if state.contagion_alerts:
        lines.append(rgb_fg(220, 100, 0, "  🔴 CONTAGION:"))
        for alert in state.contagion_alerts:
            lines.append(f"     {dim(alert)}")

    if not state.active_pd_symbols and not state.contagion_alerts:
        lines.append(rgb_fg(0, 200, 100, "  ✓  No active manipulation detected."))

    lines.append(dim("  " + "─" * 60))
    # Asset node table
    lines.append(dim("  Assets  ") + "   Hz    organic  phase")
    for sym, body in sorted(state.bodies.items()):
        r3, g3, b3 = hz_to_rgb(body.hz)
        phase_str = body.pump_dump_phase if body.pump_dump_phase != "none" else "—"
        lines.append(
            f"  {rgb_fg(r3,g3,b3, f'{sym:<6}')}"
            f"  {body.hz:>5.0f}Hz  "
            f"{body.organic_score:.2f}     "
            + (rgb_fg(200, 60, 0, phase_str) if body.is_event else dim(phase_str))
        )
    return lines


def render_entities(state: WorldState) -> List[str]:
    """Render the bot/firm entity landscape — who is in the world right now."""
    lines = []
    lines.append(bold_hz(639.0, "  ⚡ ENTITY INTELLIGENCE — WHO IS IN THE FIELD"))
    lines.append(dim("  " + "─" * 60))

    active = state.dominant_entities
    for eid, (emoji, name, desc) in list(ENTITY_CHARS.items())[:7]:
        is_active = eid in active or (eid == "UNKNOWN" and not active)
        colour = (255, 100, 50) if is_active else (80, 80, 80)
        activity = "ACTIVE ◉" if is_active else "quiet  ○"
        lines.append(
            f"  {emoji}  {rgb_fg(*colour, f'{name:<14}')}"
            f"  {activity}  {dim(desc[:35])}"
        )

    lines.append("")
    lines.append(dim("  " + "─" * 60))

    # Entity-vs-asset matrix (simplified)
    lines.append(dim("  Bot activity hotspots:"))
    for sym, body in state.bodies.items():
        if body.pump_dump_phase != "none":
            r4, g4, b4 = hz_to_rgb(body.hz)
            lines.append(
                f"    {rgb_fg(r4,g4,b4,sym):<10} "
                + rgb_fg(220, 60, 0,
                         f"{body.pump_dump_phase.upper():<14}"
                         f"  bot_density est: {min(0.99, body.organic_score * 0 + 0.60 + random.uniform(0, 0.2)):.0%}")
            )

    if not any(b.pump_dump_phase != "none" for b in state.bodies.values()):
        lines.append(rgb_fg(0, 180, 80, "    No coordinated bot activity detected."))

    lines.append("")
    # Counter-intelligence hint
    lines.append(dim("  Counter-intelligence posture:"))
    posture_map = {
        "engage": "Open — engage with normal position sizes.",
        "reduce": "Watchful — reduce size, raise stops.",
        "avoid":  "Defensive — avoid new entries.",
        "flee":   "EMERGENCY — exit all positions immediately.",
    }
    pr2, pg2, pb2 = {
        "engage": (0, 200, 100),
        "reduce": (200, 180, 0),
        "avoid":  (200, 100, 0),
        "flee":   (220, 0, 0),
    }.get(state.posture, (150, 150, 150))
    lines.append(f"    {rgb_fg(pr2,pg2,pb2, posture_map.get(state.posture,''))}")

    return lines


def render_narrative(state: WorldState) -> List[str]:
    """Render the Queen's narrative — her description of the harmonic universe."""
    lines = []
    lines.append(bold_hz(963.0, "  🔮 QUEEN SERO — NARRATING THE HARMONIC UNIVERSE"))
    lines.append(dim("  " + "─" * 60))
    lines.append("")

    # Typewriter-style — show lines progressively based on tick
    visible = min(len(state.narrative_lines), 1 + (state.tick % 12))
    for i, line in enumerate(state.narrative_lines[:visible]):
        # Colour the line by its Hz-weight
        age = visible - i
        r5, g5, b5 = hz_to_rgb(state.organism_hz + (i * 20 % 200))
        alpha = max(50, 255 - age * 20)
        col   = f"\033[38;2;{min(255,r5)};{min(255,g5)};{min(255,b5)}m"
        rst   = "\033[0m"
        lines.append(f"  {col}{line}{rst}")

    lines.append("")
    # Pulse indicator at bottom
    tick_char = ["◐", "◓", "◑", "◒"][state.tick % 4]
    lines.append(
        dim(f"  {tick_char} Tick {state.tick}  "
            f"Hz {state.organism_hz:.0f}  "
            f"Coherence {1.0 - state.manipulation_index:.2f}  "
            f"[{'LIVE' if state.tick > 0 else 'DEMO'}]")
    )
    return lines


# ─────────────────────────────────────────────────────────────────────────────
# FULL-SCREEN RENDERER
# ─────────────────────────────────────────────────────────────────────────────

HEADER_ART = r"""  ╔══════════════════════════════════════════════════════════════════════╗
  ║  👑  AUREON HARMONIC UNIVERSE SIMULATOR  ·  THE QUEEN'S WORLD VIEW  ║
  ╚══════════════════════════════════════════════════════════════════════╝"""

VIEW_ICONS = {
    WorldView.COSMOS:    "🌌 COSMOS",
    WorldView.SENSES:    "🌈 SENSES",
    WorldView.ORGANISM:  "🧬 ORGANISM",
    WorldView.ENTITIES:  "⚡ ENTITIES",
    WorldView.NARRATIVE: "🔮 NARRATIVE",
}


def render_view_tabs(active: WorldView) -> str:
    parts = []
    for view, label in VIEW_ICONS.items():
        if view == active:
            r6, g6, b6 = hz_to_rgb(528.0)
            parts.append(f"\033[1;48;2;{r6//4};{g6//4};{b6//4}m\033[38;2;{r6};{g6};{b6}m [{label}] \033[0m")
        else:
            parts.append(dim(f"  {label}  "))
    return "  " + " ".join(parts)


def render_frame(state: WorldState, view: WorldView, focused: str) -> str:
    """Compose a complete terminal frame for the current view."""
    lines = []
    r7, g7, b7 = hz_to_rgb(state.organism_hz)
    header_col = f"\033[38;2;{r7};{g7};{b7}m"
    rst        = "\033[0m"

    # Header
    lines.append(header_col + HEADER_ART.replace("👑", "👑") + rst)
    lines.append(render_view_tabs(view))
    lines.append("")

    # Main content
    if view == WorldView.COSMOS:
        cosmos_lines = render_cosmos(state)
        for i, cl in enumerate(cosmos_lines):
            lines.append("  " + cl)
        lines.append("")
        # Mini sense strip at bottom of cosmos
        sense_strip = []
        for ch in ["touch", "taste", "smell", "sound", "sight", "balance", "intuition", "ancestral", "manipulation"]:
            q = state.sense_scores.get(ch, 0.5)
            h = state.sense_hz.get(ch, 528.0)
            r8, g8, b8 = hz_to_rgb(h)
            bar = int(q * 6)
            sense_strip.append(
                f"\033[38;2;{r8};{g8};{b8}m{ch[0].upper()}{'█'*bar}{'░'*(6-bar)}\033[0m"
            )
        lines.append("  " + " ".join(sense_strip))

    elif view == WorldView.SENSES:
        lines.extend(render_senses(state, focused))

    elif view == WorldView.ORGANISM:
        lines.extend(render_organism(state))

    elif view == WorldView.ENTITIES:
        lines.extend(render_entities(state))

    elif view == WorldView.NARRATIVE:
        lines.extend(render_narrative(state))

    # Footer
    lines.append("")
    ticker_body = state.bodies.get(focused)
    if ticker_body:
        r9, g9, b9 = hz_to_rgb(ticker_body.hz)
        fc = f"\033[38;2;{r9};{g9};{b9}m"
        phase = ticker_body.pump_dump_phase.upper() if ticker_body.pump_dump_phase != "none" else "—"
        lines.append(
            f"  {fc}Focused: {focused}  "
            f"{ticker_body.hz:.0f}Hz  "
            f"organic={ticker_body.organic_score:.2f}  "
            f"Δ{ticker_body.price_change_pct:+.1f}%  "
            f"phase={phase}{rst}  "
            + dim(f"  organism health={state.organism_health:.3f}  tick={state.tick}")
        )

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# WORLD SIMULATOR — MAIN GAME LOOP
# ─────────────────────────────────────────────────────────────────────────────

class WorldSimulator:
    """
    The main game loop. Runs forever, cycling views and ticking the world.

    Each tick:
      1. Pull new world state (demo or live)
      2. Render the current view
      3. Clear screen and print
      4. Auto-advance view after VIEW_DWELL seconds
    """

    VIEW_DWELL     = 8.0    # seconds per auto-advance view
    VIEWS_CYCLE    = [
        WorldView.COSMOS,
        WorldView.SENSES,
        WorldView.ORGANISM,
        WorldView.ENTITIES,
        WorldView.NARRATIVE,
    ]

    def __init__(self, live: bool = False,
                 fixed_view: Optional[str] = None,
                 focused_asset: str = "BTC"):
        self._live          = live
        self._focused       = focused_asset.upper()
        self._fixed_view    = WorldView(fixed_view) if fixed_view else None
        self._view_idx      = 0
        self._last_view_ts  = time.time()

        if live:
            try:
                self._engine = LiveDataEngine()
                print("✓ Connected to live sensory framework")
                time.sleep(0.5)
            except Exception as e:
                print(f"⚠  Live connection failed ({e}), using demo mode")
                self._engine = DemoDataEngine()
        else:
            self._engine = DemoDataEngine()

    def run(self):
        """Main game loop — runs until Ctrl+C."""
        try:
            while True:
                state = self._engine.tick()
                view  = self._current_view()
                frame = render_frame(state, view, self._focused)
                # Clear terminal and print
                sys.stdout.write("\033[2J\033[H")   # clear + home cursor
                sys.stdout.write(frame + "\n")
                sys.stdout.flush()
                time.sleep(1.0 / REFRESH_HZ)
                # Auto-advance view
                if (self._fixed_view is None and
                        time.time() - self._last_view_ts > self.VIEW_DWELL):
                    self._view_idx     = (self._view_idx + 1) % len(self.VIEWS_CYCLE)
                    self._last_view_ts = time.time()

        except KeyboardInterrupt:
            sys.stdout.write("\033[2J\033[H")
            print(bold_hz(528.0, "\n  👑  Queen Sero — Universe Simulator stopped.\n"))

    def _current_view(self) -> WorldView:
        if self._fixed_view:
            return self._fixed_view
        return self.VIEWS_CYCLE[self._view_idx]

    def snapshot(self, view: str = "cosmos", focused: str = "BTC") -> str:
        """Return a single-frame string — useful for embedding or testing."""
        state = self._engine.tick()
        return render_frame(state, WorldView(view), focused.upper())


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="👑 Aureon Harmonic Universe Simulator — The Queen's World View"
    )
    parser.add_argument("--live",   action="store_true",
                        help="Connect to live QueenSensorySystem data")
    parser.add_argument("--view",   default=None,
                        choices=["cosmos", "senses", "organism", "entities", "narrative"],
                        help="Lock to one view (default: auto-cycle)")
    parser.add_argument("--asset",  default="BTC",
                        help="Focused asset (default: BTC)")
    parser.add_argument("--once",   action="store_true",
                        help="Render one frame to stdout and exit (for piping)")
    args = parser.parse_args()

    sim = WorldSimulator(live=args.live, fixed_view=args.view, focused_asset=args.asset)

    if args.once:
        view = args.view or "cosmos"
        print(sim.snapshot(view, args.asset))
    else:
        sim.run()


if __name__ == "__main__":
    main()
