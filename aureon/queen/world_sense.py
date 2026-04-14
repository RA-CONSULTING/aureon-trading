"""
WorldSense — live world-awareness aggregator for the Queen voice.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The Queen already has access to many live world-awareness sources in
the repo, but they were scattered and only the cosmic one (Dr Auris
Throne) was reaching the voice layer. This module is the coalescing
layer: a single ``snapshot()`` call pulls a compact ``WorldState``
across every source, caches the result for a short TTL so the
per-message cost stays low, and renders a prompt-ready text block.

Sources wired:

  * ``DrAurisThrone``              — cosmic advisory + Kp + Schumann + Λ(t) (10 s cycle)
  * ``SchumannResonanceBridge``    — live 7.83 Hz fundamental + earth_blessing (1 min cache)
  * ``EarthResonanceEngine``       — trading-gate status + PHI multiplier
  * ``SpaceWeatherBridge``         — NOAA Kp / solar wind / Bz / flares (5 min cache)
  * ``GlobalFinancialFeed``        — fear/greed + VIX + DXY + market regime (60 s cache)
  * ``news_signal``                — RSS-based news sentiment + geo risk (10 min refresh)

Every source is pulled inside a try/except — a missing or dead source
leaves its slice of the state empty instead of crashing the voice
path. A per-snapshot total budget (default 1.5 s) caps total wait time
even if a source stalls.

Usage::

    ws = get_world_sense()
    state = ws.snapshot()
    print(state.render_for_prompt())
"""

from __future__ import annotations

import datetime
import logging
import threading
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("aureon.queen.world_sense")


# ─────────────────────────────────────────────────────────────────────────────
# Data type
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class WorldState:
    """Snapshot of the Queen's external awareness at a single moment."""

    # ── Temporal ───────────────────────────────────────────────
    now_iso: str = ""
    weekday: str = ""
    hour_local: int = 0
    market_hours_open: Optional[bool] = None

    # ── Cosmic ─────────────────────────────────────────────────
    kp_index: Optional[float] = None
    solar_wind_kms: Optional[float] = None
    bz_component_nt: Optional[float] = None
    cosmic_advisory: str = ""
    cosmic_score: Optional[float] = None
    schumann_hz: Optional[float] = None
    schumann_coherence: Optional[float] = None
    earth_blessing: Optional[float] = None
    earth_gate_open: Optional[bool] = None

    # ── Market ─────────────────────────────────────────────────
    fear_greed: Optional[int] = None
    fear_greed_label: str = ""
    market_regime: str = ""
    risk_on_off: str = ""
    vix: Optional[float] = None
    dxy: Optional[float] = None
    btc_dominance: Optional[float] = None

    # ── News ───────────────────────────────────────────────────
    geo_risk: Optional[float] = None
    news_risk_level: str = ""
    dominant_themes: List[str] = field(default_factory=list)

    # ── Bookkeeping ────────────────────────────────────────────
    sources_ok: List[str] = field(default_factory=list)
    sources_failed: List[str] = field(default_factory=list)
    resolve_ms: float = 0.0
    captured_at: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def has_any(self) -> bool:
        return bool(self.sources_ok)

    def render_for_prompt(self, max_chars: int = 420) -> str:
        """
        Compact multi-line block the LLM can consume as "the world
        right now". Each line is one axis. Empty / unknown values are
        skipped so we never inject stale placeholders.
        """
        lines: List[str] = ["The world right now:"]

        # Time + market hours
        time_bits: List[str] = []
        if self.now_iso:
            time_bits.append(self.now_iso[:16].replace("T", " "))
        if self.weekday:
            time_bits.append(self.weekday)
        if self.market_hours_open is not None:
            time_bits.append("markets open" if self.market_hours_open else "markets closed")
        if time_bits:
            lines.append("  • time: " + ", ".join(time_bits))

        # Cosmic
        cosmic_bits: List[str] = []
        if self.cosmic_advisory:
            cosmic_bits.append(f"advisory={self.cosmic_advisory}")
        if self.kp_index is not None:
            cosmic_bits.append(f"Kp={self.kp_index:.1f}")
        if self.schumann_hz is not None:
            cosmic_bits.append(f"Schumann={self.schumann_hz:.2f}Hz")
        if self.earth_blessing is not None:
            cosmic_bits.append(f"earth_blessing={self.earth_blessing:.2f}")
        if self.earth_gate_open is not None:
            cosmic_bits.append("gate=open" if self.earth_gate_open else "gate=closed")
        if cosmic_bits:
            lines.append("  • cosmic: " + ", ".join(cosmic_bits))

        # Market
        market_bits: List[str] = []
        if self.fear_greed is not None:
            lbl = f"({self.fear_greed_label})" if self.fear_greed_label else ""
            market_bits.append(f"fear_greed={self.fear_greed}{lbl}")
        if self.market_regime:
            market_bits.append(f"regime={self.market_regime}")
        if self.vix is not None:
            market_bits.append(f"VIX={self.vix:.1f}")
        if self.dxy is not None:
            market_bits.append(f"DXY={self.dxy:.1f}")
        if self.btc_dominance is not None:
            market_bits.append(f"BTC.D={self.btc_dominance:.1f}%")
        if market_bits:
            lines.append("  • markets: " + ", ".join(market_bits))

        # News
        news_bits: List[str] = []
        if self.geo_risk is not None:
            news_bits.append(f"geo_risk={self.geo_risk:.2f}")
        if self.news_risk_level:
            news_bits.append(self.news_risk_level)
        if self.dominant_themes:
            news_bits.append("themes: " + ", ".join(self.dominant_themes[:3]))
        if news_bits:
            lines.append("  • news: " + ", ".join(news_bits))

        block = "\n".join(lines)
        if len(block) > max_chars:
            block = block[: max_chars - 3].rstrip() + "..."
        return block


# ─────────────────────────────────────────────────────────────────────────────
# WorldSense
# ─────────────────────────────────────────────────────────────────────────────


class WorldSense:
    """
    Coalescing aggregator over the live world-awareness sources.

    Thread-safe, TTL-cached. Callers should use ``get_world_sense()`` to
    get the process-wide singleton and call ``snapshot()`` every time
    they need a fresh read.
    """

    def __init__(
        self,
        *,
        cache_ttl_s: float = 20.0,
        total_budget_s: float = 1.5,
        sources: Optional[Dict[str, Any]] = None,
    ):
        self.cache_ttl_s = float(cache_ttl_s)
        self.total_budget_s = float(total_budget_s)
        self._cached: Optional[WorldState] = None
        self._cached_at: float = 0.0
        self._lock = threading.RLock()
        # ``sources`` lets tests inject fakes without monkey-patching.
        # Keys map to callables that return a dict with the fields
        # this aggregator cares about. Real sources are wired lazily.
        self._sources = sources or {}

    # ─────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────

    def snapshot(self) -> WorldState:
        now = time.time()
        with self._lock:
            if (
                self._cached is not None
                and (now - self._cached_at) < self.cache_ttl_s
            ):
                return self._cached

        t0 = time.time()
        state = WorldState(captured_at=now)
        self._populate_temporal(state)

        # Each source gets a slice of the total budget. We short-circuit
        # if the remaining budget runs out so a slow source can't block
        # the rest.
        pullers = [
            ("dr_auris", self._pull_dr_auris),
            ("schumann", self._pull_schumann),
            ("earth_gate", self._pull_earth_gate),
            ("space_weather", self._pull_space_weather),
            ("financial", self._pull_financial),
            ("news", self._pull_news),
        ]
        for name, fn in pullers:
            elapsed = time.time() - t0
            if elapsed >= self.total_budget_s:
                state.sources_failed.append(f"{name}:budget_exhausted")
                continue
            try:
                fn(state)
                state.sources_ok.append(name)
            except Exception as e:
                logger.debug("world_sense: %s pull failed: %s", name, e)
                state.sources_failed.append(name)

        state.resolve_ms = (time.time() - t0) * 1000.0
        with self._lock:
            self._cached = state
            self._cached_at = now
        return state

    def invalidate(self) -> None:
        with self._lock:
            self._cached = None
            self._cached_at = 0.0

    # ─────────────────────────────────────────────────────────────────
    # Per-source pullers (each is tiny and wrapped in try/except above)
    # ─────────────────────────────────────────────────────────────────

    def _populate_temporal(self, state: WorldState) -> None:
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        state.now_iso = now_utc.isoformat(timespec="seconds")
        state.weekday = now_utc.strftime("%A")
        state.hour_local = int(now_utc.hour)
        # Rough NYSE core hours check (13:30-20:00 UTC Mon-Fri) —
        # accurate enough for "is wall street awake right now".
        if 0 <= now_utc.weekday() <= 4:
            minutes = now_utc.hour * 60 + now_utc.minute
            state.market_hours_open = (13 * 60 + 30) <= minutes <= (20 * 60)
        else:
            state.market_hours_open = False

    def _pull_dr_auris(self, state: WorldState) -> None:
        src = self._sources.get("dr_auris")
        if src is None:
            try:
                from aureon.intelligence.dr_auris_throne import get_dr_auris_throne
                src = lambda: get_dr_auris_throne().get_state()
            except Exception:
                return
        data = src()
        if data is None:
            return
        for field_name, dst in (
            ("advisory", "cosmic_advisory"),
            ("cosmic_score", "cosmic_score"),
            ("kp_index", "kp_index"),
            ("solar_wind_speed", "solar_wind_kms"),
            ("bz_component", "bz_component_nt"),
        ):
            val = _get_attr_or_key(data, field_name)
            if val is not None:
                setattr(state, dst, val)

    def _pull_schumann(self, state: WorldState) -> None:
        src = self._sources.get("schumann")
        if src is None:
            try:
                from aureon.harmonic.aureon_schumann_resonance_bridge import (
                    SchumannResonanceBridge,
                )
                bridge = SchumannResonanceBridge()
                src = lambda: bridge.get_live_data()
            except Exception:
                return
        data = src()
        if data is None:
            return
        fund = _get_attr_or_key(data, "fundamental_hz")
        if fund is not None and state.schumann_hz is None:
            state.schumann_hz = float(fund)
        coh = _get_attr_or_key(data, "coherence")
        if coh is not None and state.schumann_coherence is None:
            state.schumann_coherence = float(coh)
        blessing = _get_attr_or_key(data, "earth_blessing")
        if blessing is not None and state.earth_blessing is None:
            state.earth_blessing = float(blessing)

    def _pull_earth_gate(self, state: WorldState) -> None:
        src = self._sources.get("earth_gate")
        if src is None:
            try:
                from aureon.harmonic.earth_resonance_engine import get_earth_engine
                engine = get_earth_engine()
                src = lambda: engine.get_trading_gate_status()
            except Exception:
                return
        data = src()
        if data is None:
            return
        # get_trading_gate_status returns either (bool, reason) or a dict
        if isinstance(data, tuple) and len(data) >= 1:
            state.earth_gate_open = bool(data[0])
        elif isinstance(data, dict):
            gate = data.get("gate_open")
            if gate is not None:
                state.earth_gate_open = bool(gate)

    def _pull_space_weather(self, state: WorldState) -> None:
        src = self._sources.get("space_weather")
        if src is None:
            try:
                from aureon.data_feeds.aureon_space_weather_bridge import (
                    SpaceWeatherBridge,
                )
                bridge = SpaceWeatherBridge()
                src = lambda: bridge.get_live_data()
            except Exception:
                return
        data = src()
        if data is None:
            return
        # Prefer Dr Auris values when already set, but fill gaps from
        # the direct bridge.
        for field_name, dst in (
            ("kp_index", "kp_index"),
            ("solar_wind_speed", "solar_wind_kms"),
            ("bz_component", "bz_component_nt"),
        ):
            val = _get_attr_or_key(data, field_name)
            if val is not None and getattr(state, dst) is None:
                setattr(state, dst, float(val))

    def _pull_financial(self, state: WorldState) -> None:
        src = self._sources.get("financial")
        if src is None:
            try:
                from aureon.data_feeds.global_financial_feed import GlobalFinancialFeed
                feed = GlobalFinancialFeed()
                src = lambda: feed.get_snapshot()
            except Exception:
                return
        data = src()
        if data is None:
            return
        for field_name, dst, cast in (
            ("crypto_fear_greed", "fear_greed", int),
            ("crypto_fg_classification", "fear_greed_label", str),
            ("market_regime", "market_regime", str),
            ("risk_on_off", "risk_on_off", str),
            ("vix", "vix", float),
            ("dxy", "dxy", float),
            ("btc_dominance", "btc_dominance", float),
        ):
            val = _get_attr_or_key(data, field_name)
            if val is None:
                continue
            try:
                setattr(state, dst, cast(val))
            except Exception:
                pass

    def _pull_news(self, state: WorldState) -> None:
        src = self._sources.get("news")
        if src is None:
            try:
                from aureon.data_feeds.news_signal import get_news_signal_engine
                engine = get_news_signal_engine()
                src = lambda: engine.get_latest_signal()
            except Exception:
                return
        data = src()
        if data is None:
            return
        geo = _get_attr_or_key(data, "geo_risk")
        if geo is not None:
            try:
                state.geo_risk = float(geo)
            except Exception:
                pass
        lvl = _get_attr_or_key(data, "risk_level")
        if lvl:
            state.news_risk_level = str(lvl)
        themes = _get_attr_or_key(data, "themes")
        if isinstance(themes, (list, tuple)):
            state.dominant_themes = [str(t) for t in themes[:5]]


def _get_attr_or_key(obj: Any, name: str) -> Any:
    """Works on both dataclasses and dict-like snapshots."""
    if obj is None:
        return None
    try:
        if isinstance(obj, dict):
            return obj.get(name)
        return getattr(obj, name, None)
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Module-level singleton
# ─────────────────────────────────────────────────────────────────────────────


_singleton: Optional[WorldSense] = None
_singleton_lock = threading.Lock()


def get_world_sense() -> WorldSense:
    global _singleton
    with _singleton_lock:
        if _singleton is None:
            _singleton = WorldSense()
        return _singleton


def reset_world_sense() -> None:
    global _singleton
    with _singleton_lock:
        _singleton = None


__all__ = [
    "WorldState",
    "WorldSense",
    "get_world_sense",
    "reset_world_sense",
]
