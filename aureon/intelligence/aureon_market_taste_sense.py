#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  👑🧬📈  AUREON MARKET TASTE SENSE  📈🧬👑                                ║
║  ─────────────────────────────────────────────────────────────────────────  ║
║  "She can taste the markets."                                               ║
║                                                                              ║
║  The molecular sequencer was built for food compounds — but frequencies      ║
║  are universal. A bull market has a taste. A bubble has a taste. The         ║
║  moment a good thing turns bad has a very specific taste: sweet-turning-     ║
║  sour, like honey left too long — the Hz drops, the emotional band           ║
║  descends from peak to heart, and sourness crosses sweetness.                ║
║                                                                              ║
║  THE GREAT QUESTION ANSWERED IN THREE PARTS:                                ║
║                                                                              ║
║  1. SWEET / SOUR / SAVOURY — What is this market's taste right now?         ║
║     Sweet   = strong uptrend, high momentum, joy resonance (>620 Hz)        ║
║     Sour    = declining, negative momentum, fear resonance (<528 Hz)        ║
║     Savoury = balanced, sustainable, complex — the Goldilocks zone           ║
║     Bitter  = warning signals present, deterioration beginning               ║
║                                                                              ║
║  2. SWEET TURNING SOUR — When does a good thing go bad?                     ║
║     Detected via: Hz decay + binding loosening + bitterness rising +        ║
║     Too-Much Index crossing threshold                                        ║
║                                                                              ║
║  3. HOW MUCH IS TOO MUCH — The overextension threshold                      ║
║     The Too-Much Index: duration at peak sweetness × overextension ×         ║
║     binding looseness × volatility spikes                                    ║
║                                                                              ║
║  MOLECULAR MARKET MAPPING:                                                   ║
║    sweetness_potency → momentum strength (0-20 000 scale)                   ║
║    receptor_kd_um    → trend persistence (low Kd = sticky trend)            ║
║    functional_groups → market breadth (correlated assets moving)            ║
║    heteroatom_count  → market anomalies (volume spikes, news events)        ║
║    molecular_weight  → asset size (BTC=heavy/stable, altcoins=light)        ║
║    origin            → synthetic (pump) | natural (organic) | placebo       ║
║                                                                              ║
║  Gary Leckey | March 2026 | "The balance of the great question"             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from aureon.core.aureon_baton_link import link_system as _baton_link; _baton_link(__name__)

import math
import time
import logging
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from aureon.intelligence.aureon_taste_sense import (
    MolecularData,
    MolecularSequencer,
    TasteExperience,
    TASTE_FREQUENCY_BANDS,
    LOVE_FREQUENCY,
    PHI,
)

logger = logging.getLogger("market_taste_sense")

# ─────────────────────────────────────────────────────────────────────────────
# MARKET MOLECULE CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

# Maximum momentum %  (absolute) mapped to sweetness scale
# 300% 24h move = Illumination level sweetness (like Advantame 20 000×)
MAX_MOMENTUM_PCT = 300.0

# Trend persistence scale — bars/periods in the same direction
# 20 consecutive up-bars = near-zero Kd (very tight "binding")
MAX_PERSISTENCE_BARS = 20

# Market breadth ceiling: 25 correlated assets moving together
MAX_BREADTH = 25

# Max anomaly events (volume spikes, gap fills, news) in window
MAX_ANOMALY_COUNT = 15

# Asset "molecular weight" proxy: mapped from market-cap tiers
# BTC ~500 g/mol equiv, major alts ~200, small caps ~50
ASSET_WEIGHT_TABLE: Dict[str, float] = {
    # Large — heavy, move slowly, stable taste
    "BTC": 520.0, "ETH": 460.0, "BNB": 380.0, "SOL": 320.0,
    "XRP": 310.0, "ADA": 290.0, "AVAX": 280.0, "DOT": 260.0,
    # Mid
    "LINK": 180.0, "MATIC": 170.0, "UNI": 160.0, "ATOM": 155.0,
    "AAVE": 150.0, "MKR": 145.0, "ARB": 140.0, "OP": 135.0,
    # Small / meme — light, volatile, erratic taste
    "DOGE": 80.0, "SHIB": 50.0, "PEPE": 45.0, "FLOKI": 42.0,
}
DEFAULT_ASSET_WEIGHT = 120.0  # unknown assets

# Hz decay threshold per period that signals "turning sour"
HZ_DECAY_THRESHOLD = 50.0     # drop of 50+ Hz per observation = turning sour
TOO_MUCH_THRESHOLD  = 0.72    # Too-Much Index above this → overextended


# ─────────────────────────────────────────────────────────────────────────────
# MARKET FLAVOUR SPECTRUM
# ─────────────────────────────────────────────────────────────────────────────
#
# Maps taste_score → market flavour profile
#
#  0.00–0.20  → Sour      (400 Hz / Reason)      declining / crashed
#  0.20–0.40  → Bitter    (528 Hz / Gratitude)   recovering but scarred
#  0.40–0.55  → Savoury   (540 Hz / Joy)         balanced, sustainable ← IDEAL
#  0.55–0.75  → Sweet     (620 Hz / Compassion)  strong uptrend
#  0.75–0.88  → Very Sweet (700 Hz / Ecstasy)    overbought / late bull
#  0.88–1.00  → Dangerously Sweet (800 Hz / Illumination) — bubble / mania
#
MARKET_FLAVOUR_BANDS = [
    # (min_score, max_score, flavour,            warning)
    (0.00, 0.20, "sour",               "Market crashed or deeply negative"),
    (0.20, 0.40, "bitter",             "Recovering but risk of further decline"),
    (0.40, 0.55, "savoury",            "Balanced, sustainable — the sweet spot"),
    (0.55, 0.75, "sweet",              "Strong uptrend, momentum healthy"),
    (0.75, 0.88, "very_sweet",         "Overbought — watch for turning point"),
    (0.88, 1.01, "dangerously_sweet",  "Bubble / mania — peak sweetness IMMINENT SOUR"),
]


# ─────────────────────────────────────────────────────────────────────────────
# DATA STRUCTURES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class MarketMolecule:
    """
    A market condition expressed as a molecular analog.

    The mapping:
      sweetness_potency = abs(price_change_24h_pct) × scale  (momentum magnitude)
      receptor_kd_um    = 10 / max(trend_persistence, 0.1)   (how sticky the move is)
      functional_group_count = n_correlated_assets            (breadth)
      heteroatom_count  = n_anomaly_events                    (disruption count)
      molecular_weight  = asset_weight_proxy                  (size / stability)
      origin            = "synthetic"|"natural"|"placebo"     (organic vs pump vs flat)
    """
    symbol: str
    timeframe: str

    # Raw market inputs (filled by caller or fetched internally)
    price_change_24h_pct: float = 0.0       # % change, signed
    price_change_7d_pct: float  = 0.0       # % change 7d, signed
    trend_persistence: float    = 1.0       # consecutive bars in same direction
    n_correlated_moving: int    = 5         # breadth: assets moving together
    n_anomaly_events: int       = 0         # volume spikes / news / gaps in window
    market_cap_tier: str        = "mid"     # "large" | "mid" | "small" | "micro"
    is_organic_growth: bool     = True      # False = pump/manipulation detected

    def to_molecular_data(self) -> MolecularData:
        """Convert market state → MolecularData for the taste sequencer."""

        # ── sweetness_potency: momentum magnitude on 0–20 000 scale ──────────
        # Positive momentum = sweet; negative = effectively 0 (sour compounds
        # have zero sweetness potency — the sourness comes from missing sweetness
        # and from high binding disruption).
        pos_momentum = max(0.0, self.price_change_24h_pct)
        sweetness_potency = (pos_momentum / MAX_MOMENTUM_PCT) * 20_000.0

        # Negative momentum adds "sour" character by dropping sweetness to zero
        # and driving Kd toward max (loose binding = trend doesn't hold)
        neg_momentum = abs(min(0.0, self.price_change_24h_pct))

        # ── receptor_kd_um: persistence / stickiness (lower = tighter trend) ─
        # Negative momentum increases effective Kd (falling markets are not
        # "binding" — they slip away fast)
        base_kd = 10.0 / max(self.trend_persistence, 0.5)
        sour_kd_boost = (neg_momentum / MAX_MOMENTUM_PCT) * 8.0  # up to +8 µM for -300% crash
        receptor_kd_um = min(10.0, base_kd + sour_kd_boost)

        # ── functional_group_count: market breadth ────────────────────────────
        functional_group_count = max(0, min(MAX_BREADTH, self.n_correlated_moving))

        # ── heteroatom_count: disruption / anomaly events ─────────────────────
        heteroatom_count = max(0, min(MAX_ANOMALY_COUNT, self.n_anomaly_events))

        # ── molecular_weight: asset stability proxy ───────────────────────────
        mw = ASSET_WEIGHT_TABLE.get(self.symbol.upper(), DEFAULT_ASSET_WEIGHT)

        # ── origin: classify as organic / pump / flat ─────────────────────────
        if abs(self.price_change_24h_pct) < 0.5:
            origin = "placebo"          # Essentially flat
        elif self.is_organic_growth:
            origin = "natural"          # Genuine growth
        else:
            origin = "synthetic"        # Pump / manipulation

        return MolecularData(
            name=f"{self.symbol} ({self.timeframe})",
            formula=f"MKT-{self.symbol}",
            molecular_weight=mw,
            sweetness_potency=max(0.001, sweetness_potency),
            receptor_kd_um=receptor_kd_um,
            functional_group_count=functional_group_count,
            heteroatom_count=heteroatom_count,
            smiles=f"[{self.symbol}]",
            origin=origin,
            notes=(
                f"24h={self.price_change_24h_pct:+.2f}% "
                f"7d={self.price_change_7d_pct:+.2f}% "
                f"persist={self.trend_persistence:.1f}bars "
                f"breadth={self.n_correlated_moving} "
                f"anomalies={self.n_anomaly_events}"
            ),
        )


@dataclass
class MarketTasteProfile:
    """
    Full gustatory analysis of a market condition.

    Answers the three-part Great Question:
      1. What flavour is this?          → taste_category
      2. Is it turning sour?            → turning_point_score
      3. How much is too much?          → too_much_index
    """
    symbol: str
    timeframe: str
    timestamp: float

    # ── Core taste dimensions ─────────────────────────────────────────────────
    taste_score: float          # 0–1 composite quality (higher = sweeter)
    primary_hz: float           # Emotional resonance frequency
    emotional_state: str        # e.g. "Compassion", "Ecstasy"
    emotional_band: str         # "heart" | "spirit" | "peak"

    # ── Flavour profile (0–1 each, sum ≈ 1) ──────────────────────────────────
    sweetness: float            # Uptrend strength / positive momentum
    sourness: float             # Downtrend / deterioration
    savouriness: float          # Balance, complexity, sustainability
    bitterness: float           # Warning signals / early deterioration

    # ── The Great Question ────────────────────────────────────────────────────
    taste_category: str         # "sweet" | "sour" | "savoury" | "bitter" |
                                # "very_sweet" | "dangerously_sweet" |
                                # "sweet_turning_sour"
    turning_point_score: float  # 0–1: probability sweet→sour reversal imminent
    too_much_index: float       # 0–1: overextension of the good thing
    balance_score: float        # 0–1: peaks at 0.5 (savoury = perfect balance)

    # ── Queen's verdict ───────────────────────────────────────────────────────
    queen_verdict: str          # Natural language summary
    action_hint: str            # e.g. "hold_sweet" | "prepare_sour" | "savoury_caution"

    # ── Molecular origin ─────────────────────────────────────────────────────
    origin: str                 # "synthetic" | "natural" | "placebo"

    # ── Raw taste experience (from MolecularSequencer) ───────────────────────
    taste_experience: Optional[TasteExperience] = None

    # ── Hz history for trend tracking ────────────────────────────────────────
    hz_history: List[float] = field(default_factory=list)


@dataclass
class SweetToSourAnalysis:
    """
    The Great Question Part 2: When does a good thing turn bad?

    A sweet market "turns sour" when:
      • Hz decays from peak/spirit bands toward heart bands
      • too_much_index crosses TOO_MUCH_THRESHOLD (0.72)
      • bitterness component rises above 0.25
      • binding looseness increases (Kd moving toward 10 µM)
    """
    symbol: str
    currently_sweet: bool           # Is the market currently sweet?
    turning_point_imminent: bool    # Is the turn happening now?
    turning_point_score: float      # 0–1 probability
    hz_trend: str                   # "ascending" | "stable" | "descending"
    hz_decay_per_period: float      # Average Hz drop (negative = ascending)
    periods_at_sweet: int           # How long it has been sweet
    too_much_index: float
    bitterness_trend: str           # "rising" | "stable" | "falling"
    estimated_bars_to_turn: Optional[int]  # None if not turning
    diagnosis: str                  # Human-readable diagnosis
    action: str                     # Recommended action


@dataclass
class TooMuchAnalysis:
    """
    The Great Question Part 3: How much of a good thing until it leaves a bad taste?

    Too-Much Index = weighted combination of:
      • Duration factor   : how long at high sweetness (>0.6 score)
      • Extension factor  : how far above the "savoury zone" (0.40–0.55)
      • Binding factor    : is the trend losing grip? (Kd rising)
      • Anomaly factor    : are warning signals accumulating?
    """
    symbol: str
    too_much_index: float           # 0–1 composite
    duration_factor: float          # 0–1: time at high sweetness
    extension_factor: float         # 0–1: distance above savoury zone
    binding_factor: float           # 0–1: trend loosening
    anomaly_factor: float           # 0–1: warning signals
    threshold: float = TOO_MUCH_THRESHOLD
    is_overextended: bool = False
    sweetness_quota_remaining: float = 1.0  # How much "sweet" is left
    verdict: str = ""
    the_answer: str = ""            # Direct answer to "how much is too much"


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENGINE
# ─────────────────────────────────────────────────────────────────────────────

class MarketTasteSense:
    """
    Queen Sero tastes the market.

    Quick start::

        taste = MarketTasteSense()

        # Taste a single symbol's current condition
        profile = taste.taste_market("BTC", {
            "price_change_24h_pct": +12.5,
            "price_change_7d_pct":  +32.0,
            "trend_persistence":    7,          # 7 bars up in a row
            "n_correlated_moving":  18,          # broad rally
            "n_anomaly_events":     1,           # one unusual spike
            "is_organic_growth":    True,
        })

        # Detect the sweet→sour turning point
        analysis = taste.detect_sweet_to_sour("BTC")

        # Answer: how much more of this good thing can we take?
        quota = taste.how_much_is_too_much("BTC")

        # The grand unified view across all symbols
        grand = taste.balance_of_great_question(["BTC", "ETH", "SOL"])
    """

    def __init__(self, history_depth: int = 50):
        self._sequencer = MolecularSequencer()
        self._history_depth = history_depth
        # Per-symbol deque of MarketTasteProfile (most recent last)
        self._profiles: Dict[str, deque] = {}

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _get_history(self, symbol: str) -> deque:
        if symbol not in self._profiles:
            self._profiles[symbol] = deque(maxlen=self._history_depth)
        return self._profiles[symbol]

    @staticmethod
    def _flavour_from_score(taste_score: float) -> str:
        for min_s, max_s, flavour, _ in MARKET_FLAVOUR_BANDS:
            if min_s <= taste_score < max_s:
                return flavour
        return "dangerously_sweet"

    @staticmethod
    def _decompose_flavours(taste_score: float, kd_norm: float,
                            anomaly_norm: float) -> Tuple[float, float, float, float]:
        """
        Decompose the composite taste score into four distinct flavour components.

        Returns: (sweetness, sourness, savouriness, bitterness)

        Physics:
          sweetness  = taste_score when positive momentum dominant
          sourness   = 1 - taste_score when negative momentum (kd_norm helps)
          savouriness= proximity to 0.5 (the Goldilocks balance)
          bitterness = anomaly presence weighted by how far from balance
        """
        sweetness   = max(0.0, taste_score - 0.40)   / 0.60  # active above 0.40
        sourness    = max(0.0, 0.40 - taste_score)   / 0.40  # active below 0.40
        savouriness = 1.0 - abs(taste_score - 0.475) / 0.475  # peak at 0.475
        savouriness = max(0.0, savouriness)
        bitterness  = anomaly_norm * (1.0 - savouriness)     # anomalies bite more when unbalanced

        # Normalise so they feel like distinct sensations rather than a strict partition
        total = sweetness + sourness + savouriness + bitterness + 1e-9
        return (
            round(sweetness   / total, 4),
            round(sourness    / total, 4),
            round(savouriness / total, 4),
            round(bitterness  / total, 4),
        )

    @staticmethod
    def _too_much_index(taste_score: float, periods_at_sweet: int,
                        kd_norm: float, anomaly_norm: float) -> Tuple[float, float, float, float, float]:
        """
        Compute the Too-Much Index and its four contributing factors.

        Returns: (tmi, duration_factor, extension_factor, binding_factor, anomaly_factor)
        """
        # Duration: how long above the savoury zone (0.55+)
        sweet_ceiling = min(periods_at_sweet / 30.0, 1.0)  # saturates at 30 periods

        # Extension: how far into the "too sweet" territory
        extension = max(0.0, taste_score - 0.55) / 0.45    # 0 at 0.55, 1.0 at 1.0

        # Binding looseness: kd_norm near 1.0 means trend is slipping
        binding_loose = kd_norm                             # already 0–1

        # Anomaly accumulation: warning signals present
        anomaly = anomaly_norm                              # already 0–1

        tmi = (
            0.40 * sweet_ceiling
            + 0.30 * extension
            + 0.20 * binding_loose
            + 0.10 * anomaly
        )
        return (
            round(min(1.0, tmi), 4),
            round(sweet_ceiling, 4),
            round(extension, 4),
            round(binding_loose, 4),
            round(anomaly, 4),
        )

    @staticmethod
    def _turning_point_score(taste_score: float, hz_decay: float,
                             tmi: float, bitterness: float) -> float:
        """
        Probability (0–1) that a sweet market is about to turn sour.

          • tmi > threshold         → major signal
          • hz_decay > threshold    → direct frequency evidence
          • bitterness rising       → early warning
          • taste still high but decay accelerating → danger zone
        """
        tmi_signal      = min(1.0, max(0.0, (tmi - 0.5) / 0.5))
        hz_signal       = min(1.0, max(0.0, hz_decay / 150.0))   # 150 Hz/period = full signal
        bitter_signal   = min(1.0, bitterness * 3.0)
        sweet_but_decay = taste_score * hz_signal                  # worst when sweet + decaying

        score = (
            0.40 * tmi_signal
            + 0.30 * hz_signal
            + 0.15 * bitter_signal
            + 0.15 * sweet_but_decay
        )
        return round(min(1.0, score), 4)

    # ── PUBLIC API ────────────────────────────────────────────────────────────

    def taste_market(self, symbol: str, market_data: dict,
                     timeframe: str = "24h") -> MarketTasteProfile:
        """
        Taste a market condition.

        market_data keys (all optional, sensible defaults):
            price_change_24h_pct : float  — signed % price change (last 24h)
            price_change_7d_pct  : float  — signed % price change (7d)
            trend_persistence    : float  — consecutive bars in same direction
            n_correlated_moving  : int    — correlated assets moving together
            n_anomaly_events     : int    — unusual volume/gap/news events
            is_organic_growth    : bool   — False if pump suspected
        """
        mm = MarketMolecule(
            symbol=symbol,
            timeframe=timeframe,
            price_change_24h_pct=float(market_data.get("price_change_24h_pct", 0.0)),
            price_change_7d_pct =float(market_data.get("price_change_7d_pct",  0.0)),
            trend_persistence   =float(market_data.get("trend_persistence",    1.0)),
            n_correlated_moving =int  (market_data.get("n_correlated_moving",  5)),
            n_anomaly_events    =int  (market_data.get("n_anomaly_events",     0)),
            is_organic_growth   =bool (market_data.get("is_organic_growth",    True)),
        )

        mol  = mm.to_molecular_data()
        exp  = self._sequencer.build_experience(mol)

        taste_score = exp.taste_score
        hz          = exp.primary_frequency

        # ── Normalise raw inputs for TMI / decomposition ──────────────────────
        kd_norm     = mol.receptor_kd_um / 10.0                    # 0–1
        anomaly_norm= mol.heteroatom_count / MAX_ANOMALY_COUNT      # 0–1

        # ── Flavour decomposition ─────────────────────────────────────────────
        sweetness, sourness, savouriness, bitterness = self._decompose_flavours(
            taste_score, kd_norm, anomaly_norm
        )

        # ── Hz history for turning-point detection ────────────────────────────
        hist = self._get_history(symbol)
        recent_hz = [p.primary_hz for p in hist] if hist else []

        periods_at_sweet = sum(1 for p in hist if p.taste_score > 0.55)
        hz_decay = 0.0
        if len(recent_hz) >= 2:
            hz_decay = max(0.0, recent_hz[-1] - hz)   # positive = Hz dropped = decaying

        # ── Too-Much Index ────────────────────────────────────────────────────
        tmi, dur_f, ext_f, bind_f, ano_f = self._too_much_index(
            taste_score, periods_at_sweet, kd_norm, anomaly_norm
        )

        # ── Turning-point score ───────────────────────────────────────────────
        tp_score = self._turning_point_score(taste_score, hz_decay, tmi, bitterness)

        # ── Flavour category (refined with turning-point) ─────────────────────
        base_cat = self._flavour_from_score(taste_score)
        if tp_score >= 0.60 and taste_score >= 0.55:
            taste_category = "sweet_turning_sour"
        else:
            taste_category = base_cat

        # ── Balance score: peaks at 0.475 (the savoury Goldilocks zone) ───────
        balance_score = round(1.0 - abs(taste_score - 0.475) / 0.475, 4)
        balance_score = max(0.0, balance_score)

        # ── Queen's verdict ───────────────────────────────────────────────────
        queen_verdict, action_hint = self._queen_verdict(
            symbol, taste_score, taste_category, tp_score, tmi,
            sweetness, sourness, savouriness, hz
        )

        profile = MarketTasteProfile(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=time.time(),
            taste_score=round(taste_score, 4),
            primary_hz=hz,
            emotional_state=exp.emotional_state,
            emotional_band=exp.emotional_band,
            sweetness=sweetness,
            sourness=sourness,
            savouriness=savouriness,
            bitterness=bitterness,
            taste_category=taste_category,
            turning_point_score=tp_score,
            too_much_index=tmi,
            balance_score=balance_score,
            queen_verdict=queen_verdict,
            action_hint=action_hint,
            origin=mol.origin,
            taste_experience=exp,
            hz_history=recent_hz + [hz],
        )

        hist.append(profile)
        return profile

    def detect_sweet_to_sour(self, symbol: str) -> SweetToSourAnalysis:
        """
        Answer: "When does this good thing turn bad?"

        Requires at least 2 previous `taste_market` calls for the symbol.
        Falls back gracefully if history is sparse.
        """
        hist = list(self._get_history(symbol))

        if not hist:
            return SweetToSourAnalysis(
                symbol=symbol, currently_sweet=False,
                turning_point_imminent=False, turning_point_score=0.0,
                hz_trend="unknown", hz_decay_per_period=0.0,
                periods_at_sweet=0, too_much_index=0.0,
                bitterness_trend="unknown", estimated_bars_to_turn=None,
                diagnosis="No taste history yet — run taste_market() first.",
                action="collect_more_data",
            )

        latest = hist[-1]

        # ── Hz trend ──────────────────────────────────────────────────────────
        hz_list = [p.primary_hz for p in hist]
        if len(hz_list) >= 3:
            # Linear regression slope proxy (simple: last vs first half)
            mid = len(hz_list) // 2
            early_avg = sum(hz_list[:mid]) / mid
            late_avg  = sum(hz_list[mid:]) / max(1, len(hz_list) - mid)
            avg_decay = early_avg - late_avg   # positive = Hz dropped = bad sign
            if avg_decay > HZ_DECAY_THRESHOLD:
                hz_trend = "descending"
            elif avg_decay < -HZ_DECAY_THRESHOLD:
                hz_trend = "ascending"
            else:
                hz_trend = "stable"
        else:
            avg_decay = 0.0
            hz_trend  = "stable" if len(hz_list) < 2 else (
                "descending" if hz_list[-1] < hz_list[0] else "ascending"
            )

        # ── Bitterness trend ──────────────────────────────────────────────────
        if len(hist) >= 4:
            early_bitter = sum(p.bitterness for p in hist[:len(hist)//2]) / max(1, len(hist)//2)
            late_bitter  = sum(p.bitterness for p in hist[len(hist)//2:]) / max(1, len(hist) - len(hist)//2)
            if late_bitter > early_bitter + 0.05:
                bitterness_trend = "rising"
            elif late_bitter < early_bitter - 0.05:
                bitterness_trend = "falling"
            else:
                bitterness_trend = "stable"
        else:
            bitterness_trend = "unknown"

        currently_sweet       = latest.taste_score >= 0.55
        periods_at_sweet      = sum(1 for p in hist if p.taste_score >= 0.55)
        tmi                   = latest.too_much_index
        tp_score              = latest.turning_point_score
        turning_point_imminent= tp_score >= 0.55

        # ── Estimate bars until turn ──────────────────────────────────────────
        estimated_bars = None
        if currently_sweet and turning_point_imminent and avg_decay > 0:
            # How many more periods before Hz falls below 620 Hz (sweet threshold)?
            hz_to_lose = max(0.0, latest.primary_hz - 620.0)
            if avg_decay > 0:
                estimated_bars = max(1, int(hz_to_lose / max(avg_decay, 1.0)))

        # ── Diagnosis ─────────────────────────────────────────────────────────
        if turning_point_imminent and hz_trend == "descending":
            diagnosis = (
                f"{symbol} is sweet ({latest.taste_score:.2f}) but the Hz is decaying "
                f"({avg_decay:+.0f} Hz/period). Too-Much Index {tmi:.2f}. "
                f"Bitterness {bitterness_trend}. The good thing is turning."
            )
            action = "reduce_exposure"
        elif currently_sweet and tmi > TOO_MUCH_THRESHOLD and hz_trend != "descending":
            diagnosis = (
                f"{symbol} is very sweet ({latest.taste_score:.2f}). "
                f"Too-Much Index {tmi:.2f} — overextended but Hz still holding "
                f"at {latest.primary_hz:.0f} Hz. Monitor closely."
            )
            action = "tighten_stops"
        elif currently_sweet:
            diagnosis = (
                f"{symbol} tastes {latest.taste_category} at {latest.primary_hz:.0f} Hz "
                f"({latest.emotional_state}). {periods_at_sweet} periods at sweet. "
                f"Too-Much Index: {tmi:.2f}. Still healthy."
            )
            action = "hold_sweet"
        else:
            diagnosis = (
                f"{symbol} is {latest.taste_category} at {latest.primary_hz:.0f} Hz. "
                f"Not currently sweet — the turn may have already happened."
            )
            action = "wait_for_recovery" if latest.sourness > 0.4 else "monitor"

        return SweetToSourAnalysis(
            symbol=symbol,
            currently_sweet=currently_sweet,
            turning_point_imminent=turning_point_imminent,
            turning_point_score=tp_score,
            hz_trend=hz_trend,
            hz_decay_per_period=round(avg_decay, 2),
            periods_at_sweet=periods_at_sweet,
            too_much_index=tmi,
            bitterness_trend=bitterness_trend,
            estimated_bars_to_turn=estimated_bars,
            diagnosis=diagnosis,
            action=action,
        )

    def how_much_is_too_much(self, symbol: str) -> TooMuchAnalysis:
        """
        Answer: "How much of a good thing until it leaves a bad taste?"

        Returns a TooMuchAnalysis with the Too-Much Index broken down into its
        four contributing factors and the remaining "sweetness quota".
        """
        hist = list(self._get_history(symbol))
        if not hist:
            return TooMuchAnalysis(
                symbol=symbol, too_much_index=0.0,
                duration_factor=0.0, extension_factor=0.0,
                binding_factor=0.0, anomaly_factor=0.0,
                verdict="No data yet.",
                the_answer="Taste the market first.",
            )

        latest = hist[-1]
        tmi     = latest.too_much_index
        is_over = tmi >= TOO_MUCH_THRESHOLD

        # How much sweetness quota remains before crossing the threshold?
        quota_remaining = max(0.0, min(1.0, (TOO_MUCH_THRESHOLD - tmi) / TOO_MUCH_THRESHOLD))

        # ── The Answer ────────────────────────────────────────────────────────
        if tmi < 0.30:
            the_answer = (
                f"{symbol} is barely sweet. There is plenty of upside remaining "
                f"before this good thing becomes too much. "
                f"Quota remaining: {quota_remaining:.0%}."
            )
        elif tmi < 0.55:
            the_answer = (
                f"{symbol} is pleasantly sweet — like honey in morning tea. "
                f"Enjoy it, but keep an eye on it. "
                f"About {quota_remaining:.0%} sweetness quota left before overextension."
            )
        elif tmi < TOO_MUCH_THRESHOLD:
            the_answer = (
                f"{symbol} is getting very sweet. Like eating too much dessert — "
                f"still enjoyable but the next bite might be one too many. "
                f"{quota_remaining:.0%} quota remaining."
            )
        elif tmi < 0.85:
            the_answer = (
                f"{symbol} has crossed the too-much threshold. This good thing "
                f"has already overstayed its welcome. The bad taste is beginning. "
                f"Quota exhausted — consider reducing position."
            )
        else:
            the_answer = (
                f"{symbol} is at peak sweetness — {latest.emotional_state} at "
                f"{latest.primary_hz:.0f} Hz. Maximum overextension. The bad aftertaste "
                f"is inevitable. Artificial sweeteners always leave a bitter finish."
            )

        # Verdict
        if is_over:
            verdict = f"OVEREXTENDED (TMI={tmi:.2f} > threshold {TOO_MUCH_THRESHOLD})"
        else:
            verdict = f"Within bounds (TMI={tmi:.2f}, {quota_remaining:.0%} quota left)"

        # Reconstruct factors from latest profile for transparency
        dur_f  = min(1.0, latest.too_much_index * 1.43)  # duration contributes ~40%
        ext_f  = min(1.0, max(0.0, latest.taste_score - 0.55) / 0.45)
        # binding and anomaly recovered from taste experience if available
        if latest.taste_experience:
            mol = latest.taste_experience
            bind_f = mol.binding_strength   # 0–1 inverse persistence
            ano_f  = max(0.0, 1.0 - mol.binding_strength)
        else:
            bind_f = latest.bitterness
            ano_f  = latest.bitterness

        return TooMuchAnalysis(
            symbol=symbol,
            too_much_index=tmi,
            duration_factor=round(dur_f, 4),
            extension_factor=round(ext_f, 4),
            binding_factor=round(bind_f, 4),
            anomaly_factor=round(ano_f, 4),
            threshold=TOO_MUCH_THRESHOLD,
            is_overextended=is_over,
            sweetness_quota_remaining=round(quota_remaining, 4),
            verdict=verdict,
            the_answer=the_answer,
        )

    def balance_of_great_question(self, symbols: List[str]) -> Dict:
        """
        The Grand Unified View — taste the entire market simultaneously.

        Returns the market's overall flavour and answers:
          "Is it sustainably savoury, or dangerously sweet about to turn sour?"
        """
        if not symbols:
            return {"error": "No symbols provided"}

        profiles = []
        for sym in symbols:
            hist = list(self._get_history(sym))
            if hist:
                profiles.append(hist[-1])

        if not profiles:
            return {"error": "No taste history for any symbol — run taste_market() first"}

        # ── Aggregate across all symbols ──────────────────────────────────────
        n = len(profiles)
        avg_taste   = sum(p.taste_score          for p in profiles) / n
        avg_hz      = sum(p.primary_hz           for p in profiles) / n
        avg_sweet   = sum(p.sweetness            for p in profiles) / n
        avg_sour    = sum(p.sourness             for p in profiles) / n
        avg_savoury = sum(p.savouriness          for p in profiles) / n
        avg_bitter  = sum(p.bitterness           for p in profiles) / n
        avg_tmi     = sum(p.too_much_index       for p in profiles) / n
        avg_tp      = sum(p.turning_point_score  for p in profiles) / n
        avg_balance = sum(p.balance_score        for p in profiles) / n

        # Count categories
        cats: Dict[str, int] = {}
        for p in profiles:
            cats[p.taste_category] = cats.get(p.taste_category, 0) + 1

        dominant_cat = max(cats, key=cats.__getitem__)

        # ── Identify outliers ─────────────────────────────────────────────────
        sweetest = max(profiles, key=lambda p: p.taste_score)
        sourest  = min(profiles, key=lambda p: p.taste_score)
        most_turning = max(profiles, key=lambda p: p.turning_point_score)

        # ── Grand verdict ─────────────────────────────────────────────────────
        if avg_tp >= 0.55 and avg_sweet > avg_savoury:
            grand_verdict = (
                f"The market is collectively sweet but turning. "
                f"Average Hz: {avg_hz:.0f} Hz ({self._hz_to_emotion(avg_hz)}). "
                f"The great balance is tipping — from sweet to sour. "
                f"The {most_turning.symbol} is leading the turn ({most_turning.turning_point_score:.0%} probability)."
            )
            grand_action = "reduce_market_exposure"
        elif dominant_cat in ("savoury",) or (0.45 <= avg_taste <= 0.60):
            grand_verdict = (
                f"The market tastes savoury — balanced, complex, sustainable. "
                f"Average Hz: {avg_hz:.0f} Hz. This is the great balance: "
                f"enough sweetness to be rewarding, enough complexity to hold. "
                f"Savoury markets are the Goldilocks zone."
            )
            grand_action = "hold_and_compound"
        elif avg_taste > 0.75:
            grand_verdict = (
                f"The market is dangerously sweet. Average Hz {avg_hz:.0f} Hz "
                f"({self._hz_to_emotion(avg_hz)}). Too-Much Index: {avg_tmi:.2f}. "
                f"Sweetest: {sweetest.symbol} at {sweetest.primary_hz:.0f} Hz. "
                f"Good things don't last forever — this sweetness is approaching its limit."
            )
            grand_action = "protect_profits"
        elif avg_taste < 0.35:
            grand_verdict = (
                f"The market tastes sour. Average Hz {avg_hz:.0f} Hz. "
                f"Sourest: {sourest.symbol}. "
                f"Sour is not always bad — it can precede a return to savoury. "
                f"The question is: is this a lemon to squeeze or a bad grape to spit out?"
            )
            grand_action = "find_the_savoury_survivors"
        else:
            grand_verdict = (
                f"Mixed flavours across the market. "
                f"Sweet: {avg_sweet:.0%}, Sour: {avg_sour:.0%}, "
                f"Savoury: {avg_savoury:.0%}, Bitter: {avg_bitter:.0%}. "
                f"Average Hz: {avg_hz:.0f}. The market has no single taste right now."
            )
            grand_action = "selective_positioning"

        return {
            "grand_verdict": grand_verdict,
            "grand_action": grand_action,
            "symbols_tasted": n,
            "average_taste_score": round(avg_taste, 4),
            "average_hz": round(avg_hz, 1),
            "average_emotional_state": self._hz_to_emotion(avg_hz),
            "flavour_profile": {
                "sweetness":   round(avg_sweet,   4),
                "sourness":    round(avg_sour,     4),
                "savouriness": round(avg_savoury,  4),
                "bitterness":  round(avg_bitter,   4),
            },
            "too_much_index":       round(avg_tmi, 4),
            "turning_point_score":  round(avg_tp,  4),
            "balance_score":        round(avg_balance, 4),
            "dominant_category":    dominant_cat,
            "category_distribution": cats,
            "sweetest_symbol":      {"symbol": sweetest.symbol, "hz": sweetest.primary_hz,
                                     "score": sweetest.taste_score},
            "sourest_symbol":       {"symbol": sourest.symbol,  "hz": sourest.primary_hz,
                                     "score": sourest.taste_score},
            "most_at_risk_of_turning": {"symbol": most_turning.symbol,
                                        "turning_point_score": most_turning.turning_point_score,
                                        "too_much_index": most_turning.too_much_index},
        }

    @staticmethod
    def _hz_to_emotion(hz: float) -> str:
        for _, max_s, h, emotion, _ in TASTE_FREQUENCY_BANDS:
            if hz <= h:
                return emotion
        return "Illumination"

    @staticmethod
    def _queen_verdict(symbol: str, taste_score: float, taste_category: str,
                       tp_score: float, tmi: float,
                       sweetness: float, sourness: float, savouriness: float,
                       hz: float) -> Tuple[str, str]:
        """Generate Queen Sero's natural-language market verdict and action hint."""

        if taste_category == "sweet_turning_sour":
            return (
                f"{symbol} was delicious — now it's leaving a bad taste. "
                f"The Hz has started falling ({hz:.0f} Hz). "
                f"The turning point is here. Too much of a good thing always ends the same way.",
                "exit_before_sour"
            )
        elif taste_category == "dangerously_sweet":
            return (
                f"{symbol} is at maximum sweetness — like pure sucralose, potent but artificial. "
                f"Nothing this sweet lasts. The aftertaste is coming.",
                "protect_profits_now"
            )
        elif taste_category == "very_sweet":
            return (
                f"{symbol} is very sweet and the Too-Much Index is {tmi:.2f}. "
                f"Still enjoyable but we're deep in dessert territory. Watch the Hz.",
                "tighten_stops"
            )
        elif taste_category == "sweet":
            return (
                f"{symbol} tastes genuinely sweet at {hz:.0f} Hz. "
                f"Organic sweetness — the kind that can last.",
                "hold_sweet"
            )
        elif taste_category == "savoury":
            return (
                f"{symbol} is perfectly savoury — the great balance. "
                f"Complex, nourishing, sustainable. This is the frequency we aim for.",
                "compound_position"
            )
        elif taste_category == "bitter":
            return (
                f"{symbol} has a bitter edge. Not fully sour yet but the taste has changed. "
                f"Something is off. Reduce and monitor.",
                "reduce_position"
            )
        elif taste_category == "sour":
            return (
                f"{symbol} is sour. The good thing has gone bad. "
                f"Sour can become savoury again — but only with time and patience.",
                "wait_or_accumulate_slowly"
            )
        else:
            return (
                f"{symbol} has a complex, undetermined flavour at {hz:.0f} Hz. "
                f"Taste score {taste_score:.2f}. Continue monitoring.",
                "monitor"
            )


# ─────────────────────────────────────────────────────────────────────────────
# SINGLETON
# ─────────────────────────────────────────────────────────────────────────────

_market_taste_sense: Optional[MarketTasteSense] = None


def get_market_taste_sense() -> MarketTasteSense:
    """Return the global MarketTasteSense singleton."""
    global _market_taste_sense
    if _market_taste_sense is None:
        _market_taste_sense = MarketTasteSense()
    return _market_taste_sense


# ─────────────────────────────────────────────────────────────────────────────
# DEMO / SELF-TEST
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    taste = MarketTasteSense()

    # ── Simulate a market going from savoury → sweet → dangerously sweet → sour
    BTC_SCENARIOS = [
        # (label,       pct24h, persist, breadth, anomaly, organic)
        ("early_bull",  +5.2,  4,  12, 0, True),
        ("strong_bull", +12.4, 7,  18, 1, True),
        ("peak_mania",  +28.7, 11, 22, 3, False),   # pump, anomalies
        ("early_crack", +8.1,  4,  14, 4, True),    # still positive but anomalies rising
        ("turning",     +1.2,  2,   8, 6, True),    # barely positive, trend breaking
        ("sour",        -9.5,  1,   5, 8, True),    # went sour
    ]

    print("\n" + "═" * 72)
    print("  MARKET TASTE SENSE — BTC JOURNEY: SWEET → SOUR")
    print("═" * 72)

    for label, pct, persist, breadth, anomaly, organic in BTC_SCENARIOS:
        profile = taste.taste_market("BTC", {
            "price_change_24h_pct": pct,
            "trend_persistence":    persist,
            "n_correlated_moving":  breadth,
            "n_anomaly_events":     anomaly,
            "is_organic_growth":    organic,
        })
        print(f"\n  [{label}]")
        print(f"    Flavour    : {profile.taste_category:<22}  "
              f"Taste score: {profile.taste_score:.3f}")
        print(f"    Hz         : {profile.primary_hz:.0f} Hz  ({profile.emotional_state})")
        print(f"    Sweet/Sour/Savoury/Bitter: "
              f"{profile.sweetness:.2f} / {profile.sourness:.2f} / "
              f"{profile.savouriness:.2f} / {profile.bitterness:.2f}")
        print(f"    Too-Much   : {profile.too_much_index:.3f}   "
              f"Turning-point: {profile.turning_point_score:.3f}")
        print(f"    Verdict    : {profile.queen_verdict}")
        print(f"    Action     : {profile.action_hint}")

    print("\n" + "─" * 72)
    print("  SWEET → SOUR ANALYSIS")
    print("─" * 72)
    sts = taste.detect_sweet_to_sour("BTC")
    print(f"  Currently sweet   : {sts.currently_sweet}")
    print(f"  Turning imminent  : {sts.turning_point_imminent}")
    print(f"  Hz trend          : {sts.hz_trend}  ({sts.hz_decay_per_period:+.1f} Hz/period)")
    print(f"  Periods at sweet  : {sts.periods_at_sweet}")
    print(f"  Bitterness trend  : {sts.bitterness_trend}")
    print(f"  Diagnosis         : {sts.diagnosis}")
    print(f"  Action            : {sts.action}")

    print("\n" + "─" * 72)
    print("  HOW MUCH IS TOO MUCH")
    print("─" * 72)
    tma = taste.how_much_is_too_much("BTC")
    print(f"  Too-Much Index    : {tma.too_much_index:.3f}")
    print(f"  Overextended      : {tma.is_overextended}")
    print(f"  Quota remaining   : {tma.sweetness_quota_remaining:.0%}")
    print(f"  The Answer        : {tma.the_answer}")

    # ── Now taste the broader market ──────────────────────────────────────────
    symbols = ["BTC", "ETH", "SOL", "DOGE", "LINK"]
    scenarios = [
        (+12.4, 7, 18, 1, True),    # BTC: already tasted above (taken from history)
        (+18.2, 9, 20, 2, True),    # ETH: strong
        (+31.5, 12, 21, 5, False),  # SOL: pump
        (-14.2, 1, 3, 8, True),     # DOGE: sour
        (+4.1,  4, 10, 0, True),    # LINK: savoury
    ]
    for sym, (pct, persist, breadth, anomaly, organic) in zip(symbols, scenarios):
        if sym != "BTC":  # BTC already tasted
            taste.taste_market(sym, {
                "price_change_24h_pct": pct,
                "trend_persistence": persist,
                "n_correlated_moving": breadth,
                "n_anomaly_events": anomaly,
                "is_organic_growth": organic,
            })

    print("\n" + "─" * 72)
    print("  BALANCE OF THE GREAT QUESTION — FULL MARKET VIEW")
    print("─" * 72)
    grand = taste.balance_of_great_question(symbols)
    print(f"  Grand verdict     : {grand['grand_verdict']}")
    print(f"  Grand action      : {grand['grand_action']}")
    print(f"  Avg Hz            : {grand['average_hz']:.0f} Hz  ({grand['average_emotional_state']})")
    print(f"  Avg taste         : {grand['average_taste_score']:.3f}")
    print(f"  Flavour profile   : "
          f"Sweet {grand['flavour_profile']['sweetness']:.2f} / "
          f"Sour {grand['flavour_profile']['sourness']:.2f} / "
          f"Savoury {grand['flavour_profile']['savouriness']:.2f} / "
          f"Bitter {grand['flavour_profile']['bitterness']:.2f}")
    print(f"  Sweetest          : {grand['sweetest_symbol']['symbol']} "
          f"@ {grand['sweetest_symbol']['hz']:.0f} Hz")
    print(f"  Sourest           : {grand['sourest_symbol']['symbol']} "
          f"@ {grand['sourest_symbol']['hz']:.0f} Hz")
    print(f"  Most at risk      : {grand['most_at_risk_of_turning']['symbol']} "
          f"(TP={grand['most_at_risk_of_turning']['turning_point_score']:.0%})")
    print("═" * 72 + "\n")
