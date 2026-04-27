"""HNC Live Field daemon — continuous Λ(t) computation from real data feeds.

Wires existing fetchers in ``aureon/`` onto an asyncio scheduler so the
Master Equation runs against live world data on a clock, instead of being
re-pulled per session. Each external source is polled at its native cadence;
their readings are normalised to the LambdaEngine's SubsystemReading shape
and fed to engine.step() in a fixed-rate compute loop.

Architecture (matches the 5-layer spec):

    Layer 1  — fetchers (existing repo APIs):
                * aureon.harmonic.aureon_schumann_resonance_bridge.SchumannResonanceBridge
                * aureon.data_feeds.aureon_space_weather_bridge.SpaceWeatherBridge
                * aureon.integrations.world_data.world_data_ingester.WorldDataIngester (.fetch_gdelt)
              Plug-in slots (NotImplemented unless the user supplies):
                * Bitfinex BTC ticks (no fetcher in repo today)
                * NASA OMNI hourly  (no fetcher in repo today)

    Layer 3  — kernel: aureon.core.aureon_lambda_engine.LambdaEngine,
              parameters loaded via aureon.core.hnc_params.

    Layer 4  — storage: piggybacks on LambdaEngine's auto-persist (which
              writes state/lambda_history.json every PERSIST_EVERY steps),
              plus an append-only JSONL trace at state/hnc_live_trace.jsonl.
              Parquet/SHA-chain (warm/cold storage) are out of scope here —
              the JSONL is the hot buffer.

    Layer 2 / 5 are out of scope of *this* module:
        Layer 2 (Schumann strip-diff render) is the single biggest gap and
        deserves its own module; today the SchumannResonanceBridge falls
        back to simulation when its sources are down. The daemon will
        happily consume real readings the moment the bridge starts
        returning them.
        Layer 5 (headless status command) is in ``aureon/status.py``.

The daemon is structured as one supervisor coroutine (``HNCLiveDaemon.run``)
that gathers source-pull tasks plus one fixed-cadence compute task. Each
source task owns its own retry/backoff. A source that fails its native
fetch leaves its last-good reading in place; the compute loop never blocks
waiting for any single source.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import signal
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Awaitable, Callable, Dict, List, Optional

from aureon.core.aureon_lambda_engine import LambdaEngine, SubsystemReading
from aureon.core.hnc_params import HNCParams, apply_to_lambda_engine, load_params

logger = logging.getLogger(__name__)


# ─── Cadence config ────────────────────────────────────────────────
# Source-native intervals (seconds). Match the spec table.
SCHUMANN_INTERVAL = 300         # Tomsk JPEG updates ~5–10 min
SPACE_WEATHER_INTERVAL = 60     # USGS geomag every 1 min, NOAA Kp every 5
GDELT_INTERVAL = 900            # GDELT 2.0 publishes every 15 min
BITFINEX_INTERVAL = 10          # ticker loop (when wired)
OMNI_INTERVAL = 3600            # OMNI hourly (when wired)

# Compute cadence — how often the engine takes a step against the latest
# readings. The kernel is cheap (<1 ms/step) so 5 s gives the field high
# resolution without hammering the fetchers.
COMPUTE_INTERVAL = 5

# Backoff applied after a fetch raises.
BACKOFF_INITIAL = 30
BACKOFF_MAX = 600


@dataclass
class SourceState:
    """Per-source running state — cached reading, error count, last fetch ts."""
    name: str
    interval_s: float
    last_reading: Optional[SubsystemReading] = None
    last_fetch_ts: float = 0.0
    error_count: int = 0
    backoff_s: float = BACKOFF_INITIAL


# ─── SubsystemReading mappers ─────────────────────────────────────
# Each external reading has its own shape. These functions normalise to
# the LambdaEngine input contract: name, value ∈ [0,1], confidence ∈ [0,1],
# state (free-form string).

def _map_schumann(reading) -> SubsystemReading:
    """SchumannReading → SubsystemReading.

    value      = amplitude (already 0..1)
    confidence = quality (Q-factor, already 0..1)
    state      = resonance_phase (stable/elevated/peak/disturbed)
    """
    return SubsystemReading(
        name="schumann",
        value=float(getattr(reading, "amplitude", 0.5) or 0.5),
        confidence=float(getattr(reading, "quality", 0.5) or 0.5),
        state=str(getattr(reading, "resonance_phase", "unknown")),
    )


def _map_space_weather(reading) -> SubsystemReading:
    """SpaceWeatherReading → SubsystemReading.

    The Kp index runs 0..9 (0 = quiet, 9 = severe storm). A *quiet*
    geomagnetic field is a high-coherence input to Λ, so we invert:
    value = 1 - Kp/9. Confidence is fixed because NOAA's feed is
    authoritative when present.
    """
    kp = float(getattr(reading, "kp_index", 3.0) or 3.0)
    value = max(0.0, min(1.0, 1.0 - kp / 9.0))
    return SubsystemReading(
        name="space_weather",
        value=value,
        confidence=0.9,
        state=str(getattr(reading, "kp_category", "unknown")),
    )


def _map_gdelt(items: list) -> SubsystemReading:
    """GDELT article list → SubsystemReading.

    Phase 1 mapping: more articles in the last pull = higher world-event
    pressure. We tanh-saturate against 50 articles so the value lives in
    [0,1] and is monotonic in count.

    A real Phase 2 should compute the GDELT *tone* signal (already part
    of GDELT 2.0), but ``WorldDataIngester.fetch_gdelt`` doesn't expose
    tone yet — extending that is a separate change, not a daemon concern.
    """
    n = len(items) if items else 0
    import math
    value = math.tanh(n / 25.0)
    return SubsystemReading(
        name="gdelt",
        value=value,
        confidence=0.7 if n else 0.3,
        state=f"{n}_articles",
    )


# ─── The daemon ───────────────────────────────────────────────────

class HNCLiveDaemon:
    """Asyncio-driven supervisor: one task per source + one compute loop.

    Usage:
        daemon = HNCLiveDaemon()
        asyncio.run(daemon.run(duration_s=None))   # run until SIGINT

    Caller wiring:
        - ``register_source(name, interval_s, fetch_coro, mapper)`` adds
          a custom source (Bitfinex, OMNI, etc.).
        - ``current_state`` returns the last LambdaState dict — used by
          the headless ``aureon.status`` entry point.
    """

    def __init__(self, params: Optional[HNCParams] = None,
                 trace_path: Optional[Path] = None,
                 attach_observer: bool = True,
                 observer=None):
        """
        attach_observer: when True (default), construct a HarmonicObserver
            and feed it engine state on every compute step. The observer
            auto-claims the singleton (see aureon.observer.__init__) so
            the Queen sentience layer, the Kelly gate, and the
            PredictionBus all auto-pick it up — no extra wiring needed.
            Set False when you want the daemon's pure compute behaviour
            (e.g. running multiple daemons in one process).

        observer: pass a pre-constructed HarmonicObserver to use instead
            of the default. Useful for tests or for sharing one observer
            across multiple daemons. When None and attach_observer=True,
            a default observer is created.
        """
        self.params = apply_to_lambda_engine(params or load_params())
        self.engine = LambdaEngine()
        self._sources: Dict[str, SourceState] = {}
        self._fetchers: Dict[str, Callable[[], Awaitable[Optional[SubsystemReading]]]] = {}
        self._last_state_dict: Optional[dict] = None
        self._step_lock = asyncio.Lock()
        self._stop = asyncio.Event()
        self._trace_path = trace_path or (
            Path(__file__).resolve().parents[2] / "state" / "hnc_live_trace.jsonl"
        )
        self._trace_path.parent.mkdir(parents=True, exist_ok=True)

        # Built-in sources — only wire if their bridges import cleanly.
        self._wire_default_sources()

        # Optional observer attach. Lazy-import + try/except so any
        # observer issue (missing module, missing numpy in sandbox) can
        # NEVER break daemon startup or the compute loop. The observer
        # is purely an output channel from this loop's perspective.
        self._observer = observer
        if self._observer is None and attach_observer:
            try:
                from aureon.observer import HarmonicObserver
                self._observer = HarmonicObserver(publish_to_bus=True)
                logger.info("HNC daemon: HarmonicObserver attached (auto)")
            except Exception as exc:
                logger.warning("HNC daemon: HarmonicObserver attach skipped: %s", exc)
                self._observer = None
        elif self._observer is not None:
            logger.info("HNC daemon: HarmonicObserver attached (caller-provided)")

    # ─── source registration ────────────────────────────────────

    def register_source(
        self,
        name: str,
        interval_s: float,
        fetcher: Callable[[], Awaitable[Optional[SubsystemReading]]],
    ) -> None:
        """Add a source. ``fetcher`` is an async callable that returns a
        SubsystemReading or None. The daemon handles cadence and retry.
        """
        self._sources[name] = SourceState(name=name, interval_s=interval_s)
        self._fetchers[name] = fetcher
        logger.info("HNC daemon: registered source %s @ %ss", name, interval_s)

    def _wire_default_sources(self) -> None:
        # Schumann
        try:
            from aureon.harmonic.aureon_schumann_resonance_bridge import SchumannResonanceBridge
            bridge = SchumannResonanceBridge()

            async def fetch_schumann():
                # SchumannResonanceBridge.get_live_data() is sync; run in thread.
                reading = await asyncio.to_thread(bridge.get_live_data)
                return _map_schumann(reading) if reading else None

            self.register_source("schumann", SCHUMANN_INTERVAL, fetch_schumann)
        except Exception as exc:
            logger.warning("HNC daemon: schumann not wired (%s)", exc)

        # Space weather
        try:
            from aureon.data_feeds.aureon_space_weather_bridge import SpaceWeatherBridge
            sw = SpaceWeatherBridge()

            async def fetch_space_weather():
                reading = await asyncio.to_thread(sw.get_live_data)
                return _map_space_weather(reading) if reading else None

            self.register_source("space_weather", SPACE_WEATHER_INTERVAL, fetch_space_weather)
        except Exception as exc:
            logger.warning("HNC daemon: space_weather not wired (%s)", exc)

        # GDELT
        try:
            from aureon.integrations.world_data.world_data_ingester import WorldDataIngester
            ingester = WorldDataIngester()

            async def fetch_gdelt():
                items = await asyncio.to_thread(ingester.fetch_gdelt, "world", 25)
                return _map_gdelt(items)

            self.register_source("gdelt", GDELT_INTERVAL, fetch_gdelt)
        except Exception as exc:
            logger.warning("HNC daemon: gdelt not wired (%s)", exc)

    # ─── per-source pull loop ──────────────────────────────────

    async def _source_loop(self, name: str) -> None:
        st = self._sources[name]
        fetch = self._fetchers[name]
        while not self._stop.is_set():
            try:
                reading = await fetch()
                if reading is not None:
                    st.last_reading = reading
                    st.last_fetch_ts = time.time()
                    st.error_count = 0
                    st.backoff_s = BACKOFF_INITIAL
                    # Stage AC: feed the value into the momentum tracker
                    # so multi-horizon EMAs update for every source the
                    # daemon pulls. The tracker is a singleton and
                    # auto-wires onto PredictionBus; this is the data
                    # ingestion side.
                    try:
                        from aureon.observer.momentum import get_momentum_tracker
                        mt = get_momentum_tracker()
                        if mt is not None:
                            mt.ingest(name, float(reading.value), st.last_fetch_ts)
                    except Exception:
                        pass
                wait = st.interval_s
            except Exception as exc:
                st.error_count += 1
                wait = min(st.backoff_s, BACKOFF_MAX)
                st.backoff_s = min(st.backoff_s * 2, BACKOFF_MAX)
                logger.warning(
                    "HNC daemon: source %s fetch failed (%s); backoff %ss",
                    name, exc, wait,
                )
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=wait)
                return  # stop requested
            except asyncio.TimeoutError:
                pass

    # ─── compute loop ──────────────────────────────────────────

    async def _compute_loop(self) -> None:
        while not self._stop.is_set():
            readings: List[SubsystemReading] = [
                st.last_reading for st in self._sources.values()
                if st.last_reading is not None
            ]
            async with self._step_lock:
                state = self.engine.step(readings)
            self._last_state_dict = state.to_dict()
            self._append_trace(self._last_state_dict, readings)

            # Feed the engine state into the attached observer. Wrapped
            # so any observer error (numpy missing in sandbox, scipy
            # crash on a degenerate window, etc.) cannot interrupt the
            # compute loop — the daemon's job is to keep ticking.
            if self._observer is not None:
                try:
                    self._observer.ingest_state(state)
                except Exception as exc:
                    logger.debug("observer.ingest_state failed: %s", exc)

            try:
                await asyncio.wait_for(self._stop.wait(), timeout=COMPUTE_INTERVAL)
                return
            except asyncio.TimeoutError:
                pass

    # ─── trace I/O ─────────────────────────────────────────────

    def _append_trace(self, state_dict: dict, readings: List[SubsystemReading]) -> None:
        """Append-only JSONL trace — the Phase-1 hot buffer.

        One line per kernel step. Cheap, recoverable, easy to feed back
        into a fitter. The LambdaEngine separately auto-persists its
        history deque to state/lambda_history.json.
        """
        try:
            row = {
                "ts": state_dict.get("timestamp"),
                "step": state_dict.get("step"),
                "lambda_t": state_dict.get("lambda_t"),
                "consciousness_psi": state_dict.get("consciousness_psi"),
                "consciousness_level": state_dict.get("consciousness_level"),
                "coherence_gamma": state_dict.get("coherence_gamma"),
                "symbolic_life_score": state_dict.get("symbolic_life_score"),
                "sources": {
                    r.name: {"value": r.value, "confidence": r.confidence, "state": r.state}
                    for r in readings
                },
            }
            with open(self._trace_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(row) + "\n")
        except Exception as exc:
            logger.debug("trace append failed: %s", exc)

    # ─── public API ────────────────────────────────────────────

    @property
    def current_state(self) -> Optional[dict]:
        """Last LambdaState as a dict, or None if the compute loop hasn't
        ticked yet. Used by aureon.status for headless inspection."""
        return self._last_state_dict

    @property
    def source_status(self) -> Dict[str, dict]:
        """Per-source last-fetch metadata for the status command."""
        now = time.time()
        return {
            name: {
                "interval_s": st.interval_s,
                "last_fetch_ts": st.last_fetch_ts,
                "lag_s": (now - st.last_fetch_ts) if st.last_fetch_ts else None,
                "error_count": st.error_count,
                "has_reading": st.last_reading is not None,
            }
            for name, st in self._sources.items()
        }

    async def run(self, duration_s: Optional[float] = None) -> None:
        """Start the daemon. ``duration_s=None`` runs until SIGINT/SIGTERM."""
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, self._stop.set)
            except (NotImplementedError, RuntimeError):
                pass  # Windows / non-main-thread

        tasks = [
            asyncio.create_task(self._source_loop(name), name=f"src:{name}")
            for name in self._sources
        ]
        tasks.append(asyncio.create_task(self._compute_loop(), name="compute"))

        if duration_s is not None:
            asyncio.create_task(self._stop_after(duration_s))

        logger.info(
            "HNC live daemon started (sources=%s, params=%s)",
            list(self._sources), self.params,
        )
        await self._stop.wait()
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        # Final persist so the lighthouse echo survives shutdown.
        try:
            self.engine.save_history()
        except Exception:
            pass
        logger.info("HNC live daemon stopped.")

    async def _stop_after(self, duration_s: float) -> None:
        await asyncio.sleep(duration_s)
        self._stop.set()


# ─── module main — quick smoke test ──────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(
        level=os.environ.get("AUREON_LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    duration = float(os.environ.get("AUREON_HNC_DAEMON_DURATION", "0")) or None
    asyncio.run(HNCLiveDaemon().run(duration_s=duration))
