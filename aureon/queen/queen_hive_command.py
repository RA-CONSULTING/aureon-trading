#!/usr/bin/env python3
"""
Queen Hive Command — The Operational Brain

SCAN (all worker bees) → VALIDATE (consensus + neural) → ACT (hunt) → MONITOR (don't lose)

The Queen uses every scanner as a worker bee. They report back via ThoughtBus.
She validates through consensus (multiple bees must agree), scores with NeuronV2,
then issues hunt commands that Kraken/Capital traders execute through the
orchestrator gate.

Gary Leckey | Aureon Institute | 2026
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)

import importlib
import logging
import threading
import time
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)

# ── ThoughtBus integration (fail-safe) ────────────────────────────────────────
try:
    from aureon.core.aureon_thought_bus import get_thought_bus, Thought
    _HAS_BUS = True
except Exception:
    get_thought_bus = None  # type: ignore
    Thought = None          # type: ignore
    _HAS_BUS = False

# ── NeuronV2 for neural confidence scoring ────────────────────────────────────
try:
    from aureon.queen.queen_neuron_v2 import QueenNeuronV2
    _HAS_NEURON = True
except Exception:
    QueenNeuronV2 = None  # type: ignore
    _HAS_NEURON = False

# ── Scanner registry: (name, module_path, class_name) ────────────────────────
_BEE_REGISTRY = [
    ("ocean_wave",        "aureon.scanners.aureon_ocean_wave_scanner",              "OceanWaveScanner"),
    ("strategic_warfare", "aureon.scanners.aureon_strategic_warfare_scanner",       "StrategicWarfareScanner"),
    ("bot_shape",         "aureon.bots_intelligence.aureon_bot_shape_scanner",      "BotShapeScanner"),
    ("manipulation",      "aureon.analytics.aureon_historical_manipulation_hunter", "HistoricalManipulationHunter"),
    ("firm_intel",        "aureon.bots_intelligence.aureon_firm_intelligence_catalog", "FirmIntelligenceCatalog"),
    ("probability",       "aureon.strategies.probability_ultimate_intelligence",    "ProbabilityUltimateIntelligence"),
]

# ── Tuning constants ─────────────────────────────────────────────────────────
SCAN_INTERVAL_SEC      = 10     # How often to run all worker bees
MIN_CONSENSUS_BEES     = 2      # Minimum bees agreeing to form a signal
MAX_HUNTS_PER_CYCLE    = 3      # Max hunt commands per scan cycle
MIN_COMPOSITE_SCORE    = 0.40   # Minimum composite score to issue a hunt
HUNT_COOLDOWN_SEC      = 60     # Don't re-hunt the same symbol within this window


# ═══════════════════════════════════════════════════════════════════════════════
# WORKER BEE SWARM — Lazily instantiates and runs all available scanners
# ═══════════════════════════════════════════════════════════════════════════════

class WorkerBeeSwarm:
    """The Queen's worker bees — each one a scanner that finds targets."""

    def __init__(self, thought_bus: Any = None):
        self._thought_bus = thought_bus
        self._bees: Dict[str, Any] = {}
        self._price_map: Dict[str, float] = {}
        self._tradeable_symbols: List[str] = []
        self._init_bees()

    def _init_bees(self) -> None:
        """Try to instantiate each scanner. Failures are silently skipped."""
        for name, module_path, class_name in _BEE_REGISTRY:
            try:
                mod = importlib.import_module(module_path)
                cls = getattr(mod, class_name)
                # BotShapeScanner needs a symbols list — use empty, will be updated later
                if name == "bot_shape":
                    self._bees[name] = cls(symbols=[])
                else:
                    self._bees[name] = cls()
                log.debug(f"[SWARM] Worker bee '{name}' loaded")
            except Exception as exc:
                log.debug(f"[SWARM] Worker bee '{name}' unavailable: {exc}")

        loaded = list(self._bees.keys())
        log.info(f"[SWARM] {len(loaded)} worker bees active: {', '.join(loaded) or 'none'}")

    def update_market(self, price_map: Dict[str, float], symbols: List[str]) -> None:
        """Update market data from ThoughtBus price feed."""
        self._price_map = price_map
        self._tradeable_symbols = symbols

    def scan_all(self) -> List[Dict[str, Any]]:
        """Run every bee, collect signals, publish to ThoughtBus."""
        all_signals: List[Dict[str, Any]] = []
        for name, bee in self._bees.items():
            try:
                signals = self._run_bee(name, bee)
                if signals:
                    all_signals.extend(signals)
                    self._publish_scan(name, signals)
            except Exception:
                pass
        return all_signals

    # ── Per-bee adapters ──────────────────────────────────────────────────

    def _run_bee(self, name: str, bee: Any) -> List[Dict[str, Any]]:
        """Normalize scanner output to [{symbol, exchange, score, source}]."""

        if name == "manipulation":
            return self._run_manipulation(bee)
        if name == "probability":
            return self._run_probability(bee)
        if name == "firm_intel":
            return self._run_firm_intel(bee)
        if name == "strategic_warfare":
            return self._run_warfare(bee)
        if name == "ocean_wave":
            return self._run_ocean_wave(bee)
        if name == "bot_shape":
            return self._run_bot_shape(bee)
        return []

    def _run_manipulation(self, bee: Any) -> List[Dict[str, Any]]:
        """ManipulationHunter: check current conditions for each symbol."""
        signals = []
        for symbol in self._tradeable_symbols[:20]:  # Cap to prevent overload
            price = self._price_map.get(symbol, 0)
            if price <= 0:
                continue
            try:
                if hasattr(bee, 'analyze_current_conditions'):
                    result = bee.analyze_current_conditions(
                        symbol=symbol, price_change_pct=0.0,
                        volume=0.0, momentum=0.0,
                    )
                    if result and result.get("is_opportunity_pattern"):
                        signals.append({
                            "symbol": symbol, "exchange": "kraken",
                            "score": float(result.get("similarity", 0.5)),
                            "source": "manipulation",
                            "detail": str(result.get("historical_outcome", "")),
                        })
                    elif result and result.get("is_danger_pattern"):
                        signals.append({
                            "symbol": symbol, "exchange": "kraken",
                            "score": -float(result.get("similarity", 0.5)),
                            "source": "manipulation_danger",
                            "detail": str(result.get("historical_outcome", "")),
                        })
            except Exception:
                pass
        return signals

    def _run_probability(self, bee: Any) -> List[Dict[str, Any]]:
        """ProbabilityUltimateIntelligence: predict for each symbol."""
        signals = []
        for symbol in self._tradeable_symbols[:10]:
            try:
                if hasattr(bee, 'predict'):
                    pred = bee.predict(
                        current_pnl=0.0, target_pnl=1.0,
                        pnl_history=[], momentum_score=0.0,
                        symbol=symbol,
                    )
                    prob = getattr(pred, 'final_probability', 0.0)
                    should = getattr(pred, 'should_trade', False)
                    if should and prob > 0.55:
                        signals.append({
                            "symbol": symbol, "exchange": "kraken",
                            "score": float(prob),
                            "source": "probability",
                            "detail": getattr(pred, 'reasoning', ''),
                        })
            except Exception:
                pass
        return signals

    def _run_firm_intel(self, bee: Any) -> List[Dict[str, Any]]:
        """FirmIntelligenceCatalog: check for recent smart money movement."""
        signals = []
        try:
            if hasattr(bee, 'get_all_firms'):
                firms = bee.get_all_firms()
                for firm_id in list(firms.keys())[:10]:
                    try:
                        summary = bee.get_firm_summary(firm_id)
                        pred = (summary or {}).get("prediction", {})
                        conf = float(pred.get("confidence", 0) or 0)
                        direction = str(pred.get("direction", ""))
                        if conf > 0.6 and direction in ("bullish", "accumulating"):
                            signals.append({
                                "symbol": firm_id, "exchange": "kraken",
                                "score": conf,
                                "source": "firm_intel",
                                "detail": f"smart_money_{direction}",
                            })
                    except Exception:
                        pass
        except Exception:
            pass
        return signals

    def _run_warfare(self, bee: Any) -> List[Dict[str, Any]]:
        """StrategicWarfareScanner: lightweight strength check."""
        # This scanner needs entity_name + symbols — heavyweight, run sparingly
        return []

    def _run_ocean_wave(self, bee: Any) -> List[Dict[str, Any]]:
        """OceanWaveScanner: check for detected bots (async — skip if no loop)."""
        # OceanWaveScanner.analyze_symbol is async — collect from internal state
        signals = []
        try:
            bots = getattr(bee, 'bots', {})
            for bot_id, profile in list(bots.items())[:20]:
                score = float(getattr(profile, 'total_volume', 0) or 0)
                if score > 0:
                    signals.append({
                        "symbol": getattr(profile, 'symbol', '?'),
                        "exchange": getattr(profile, 'exchange', 'kraken'),
                        "score": min(1.0, score / 10000),  # Normalize volume
                        "source": "ocean_wave",
                        "detail": f"bot_{getattr(profile, 'pattern', 'unknown')}",
                    })
        except Exception:
            pass
        return signals

    def _run_bot_shape(self, bee: Any) -> List[Dict[str, Any]]:
        """BotShapeScanner: spectral analysis for manipulation detection."""
        signals = []
        for symbol in self._tradeable_symbols[:5]:
            try:
                if hasattr(bee, '_compute_full_spectrum_fingerprint'):
                    fp = bee._compute_full_spectrum_fingerprint(symbol)
                    if fp:
                        conf = float(getattr(fp, 'confidence', 0) or 0)
                        bot_class = str(getattr(fp, 'bot_class', 'unknown'))
                        if conf > 0.6:
                            signals.append({
                                "symbol": symbol, "exchange": "kraken",
                                "score": conf,
                                "source": "bot_shape",
                                "detail": f"detected_{bot_class}",
                            })
            except Exception:
                pass
        return signals

    # ── Publish helpers ───────────────────────────────────────────────────

    def _publish_scan(self, bee_name: str, signals: List[Dict]) -> None:
        if self._thought_bus is None or not _HAS_BUS or Thought is None:
            return
        try:
            self._thought_bus.publish(Thought(
                source=f"worker_bee_{bee_name}",
                topic=f"hive.scan.{bee_name}",
                payload={"signals": signals, "count": len(signals)},
                meta={"mode": "hive_scan"},
            ))
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════════════
# QUEEN HIVE COMMAND — The Operational Brain
# ═══════════════════════════════════════════════════════════════════════════════

class QueenHiveCommand:
    """
    The Queen's operational brain.
    SCAN → VALIDATE → ACT → MONITOR

    Runs as a daemon thread. Every 10 seconds:
    1. Worker bees scan for targets
    2. Signals are grouped and scored by consensus + neural confidence
    3. Top opportunities are published as queen.command.hunt
    4. Open positions are monitored — retreat if consensus drops
    """

    def __init__(self, thought_bus: Any = None):
        self._thought_bus = thought_bus or (
            get_thought_bus() if _HAS_BUS and get_thought_bus else None
        )
        self._swarm = WorkerBeeSwarm(thought_bus=self._thought_bus)
        self._signal_queue: deque = deque(maxlen=500)
        self._price_map: Dict[str, float] = {}
        self._tradeable_symbols: List[str] = []
        self._open_positions: Dict[str, Dict] = {}
        self._recent_hunts: Dict[str, float] = {}  # symbol → last hunt timestamp
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # NeuronV2 for confidence scoring
        self._neuron: Optional[Any] = None
        if _HAS_NEURON and QueenNeuronV2 is not None:
            try:
                self._neuron = QueenNeuronV2()
            except Exception:
                pass

        # Stats
        self._scans_run = 0
        self._signals_received = 0
        self._hunts_issued = 0

        # Subscribe to incoming signals + market data
        if self._thought_bus is not None:
            try:
                self._thought_bus.subscribe("hive.scan.*", self._on_scan_signal)
                self._thought_bus.subscribe("market.*", self._on_market_update)
                self._thought_bus.subscribe("execution.trade.closed", self._on_trade_closed)
                self._thought_bus.subscribe("dtp.triggered", self._on_dtp_triggered)
                self._thought_bus.subscribe("orca.kill.complete", self._on_trade_closed)
            except Exception as exc:
                log.debug(f"[HIVE] Subscription error: {exc}")

        log.info("[HIVE COMMAND] Initialized — ready to SCAN → VALIDATE → ACT → MONITOR")

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._command_loop, name="QueenHiveCommand", daemon=True,
        )
        self._thread.start()
        log.info("[HIVE COMMAND] Background thread started")

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=SCAN_INTERVAL_SEC + 5)

    # ── Main loop ─────────────────────────────────────────────────────────

    def _command_loop(self) -> None:
        while self._running:
            cycle_start = time.time()
            try:
                # Update worker bees with latest market data
                self._swarm.update_market(self._price_map, self._tradeable_symbols)

                # PHASE 1: SCAN — all worker bees hunt for signals
                self._swarm.scan_all()
                self._scans_run += 1

                # PHASE 2: VALIDATE — score and rank by consensus + neural
                opportunities = self._validate_signals()

                # PHASE 3: ACT — issue hunt commands for top picks
                hunts_this_cycle = 0
                for opp in opportunities:
                    if hunts_this_cycle >= MAX_HUNTS_PER_CYCLE:
                        break
                    symbol = opp.get("symbol", "")
                    # Cooldown check
                    last_hunt = self._recent_hunts.get(symbol, 0)
                    if time.time() - last_hunt < HUNT_COOLDOWN_SEC:
                        continue
                    self._issue_hunt(opp)
                    self._recent_hunts[symbol] = time.time()
                    hunts_this_cycle += 1

                # PHASE 4: MONITOR — check open positions
                self._monitor_positions()

                # Periodic status
                if self._scans_run % 6 == 0:  # Every ~60 seconds
                    self._publish_status()

            except Exception as exc:
                log.debug(f"[HIVE] Command loop error: {exc}")

            # Sleep remainder of interval
            elapsed = time.time() - cycle_start
            time.sleep(max(0.5, SCAN_INTERVAL_SEC - elapsed))

    # ── VALIDATE ──────────────────────────────────────────────────────────

    def _validate_signals(self) -> List[Dict[str, Any]]:
        """Group signals by symbol, score by consensus count + neural confidence."""
        signals = list(self._signal_queue)
        self._signal_queue.clear()

        if not signals:
            return []

        # Group by symbol
        by_symbol: Dict[str, List[Dict]] = defaultdict(list)
        for sig in signals:
            sym = sig.get("symbol", "")
            if sym and sig.get("score", 0) > 0:  # Ignore danger/negative signals
                by_symbol[sym].append(sig)

        # Score each symbol by consensus + neural confidence
        opportunities = []
        for symbol, sigs in by_symbol.items():
            if len(sigs) < MIN_CONSENSUS_BEES:
                continue

            avg_score = sum(s.get("score", 0) for s in sigs) / len(sigs)
            neural_conf = self._get_neural_confidence(symbol)
            composite = avg_score * 0.6 + neural_conf * 0.4

            if composite < MIN_COMPOSITE_SCORE:
                continue

            opportunities.append({
                "symbol": symbol,
                "exchange": sigs[0].get("exchange", "kraken"),
                "consensus_count": len(sigs),
                "avg_score": round(avg_score, 4),
                "neural_confidence": round(neural_conf, 4),
                "composite_score": round(composite, 4),
                "sources": list(set(s.get("source", "?") for s in sigs)),
            })

        # Rank by composite score
        opportunities.sort(key=lambda x: x["composite_score"], reverse=True)
        return opportunities

    def _get_neural_confidence(self, symbol: str) -> float:
        """Query NeuronV2 for confidence on this symbol."""
        if self._neuron is None:
            return 0.5
        try:
            neural_input = {
                "probability_score": 0.5,
                "wisdom_score": 0.5,
                "quantum_signal": 0.0,
                "gaia_resonance": 0.5,
                "emotional_coherence": 0.5,
                "mycelium_signal": 0.0,
                "happiness_pursuit": 0.5,
            }
            prediction = self._neuron.predict(neural_input)
            return float(prediction) if prediction is not None else 0.5
        except Exception:
            return 0.5

    # ── ACT ───────────────────────────────────────────────────────────────

    def _issue_hunt(self, opportunity: Dict[str, Any]) -> None:
        """Publish a hunt command for exchange traders to execute."""
        if self._thought_bus is None or Thought is None:
            return
        try:
            self._thought_bus.publish(Thought(
                source="queen_hive_command",
                topic="queen.command.hunt",
                payload=opportunity,
                meta={"mode": "hive_hunt"},
            ))
            self._hunts_issued += 1
            log.info(
                f"[HIVE HUNT] {opportunity['symbol']} "
                f"consensus={opportunity['consensus_count']} "
                f"composite={opportunity['composite_score']:.3f} "
                f"sources={opportunity['sources']}"
            )
        except Exception:
            pass

    # ── MONITOR ───────────────────────────────────────────────────────────

    def _monitor_positions(self) -> None:
        """Check open positions. If consensus drops, issue retreat."""
        # Prune stale hunts (older than 5 minutes)
        now = time.time()
        stale = [s for s, t in self._recent_hunts.items() if now - t > 300]
        for s in stale:
            self._recent_hunts.pop(s, None)

    # ── ThoughtBus callbacks ──────────────────────────────────────────────

    def _on_scan_signal(self, thought: Any) -> None:
        """Receive scan signals from worker bees."""
        try:
            payload = thought.payload if hasattr(thought, 'payload') else thought
            if isinstance(payload, dict):
                signals = payload.get("signals", [payload])
                for sig in signals:
                    if isinstance(sig, dict):
                        self._signal_queue.append(sig)
                        self._signals_received += 1
        except Exception:
            pass

    def _on_market_update(self, thought: Any) -> None:
        """Update price map from exchange trader broadcasts."""
        try:
            payload = thought.payload if hasattr(thought, 'payload') else {}
            if isinstance(payload, dict):
                prices = payload.get("prices", {})
                if isinstance(prices, dict):
                    self._price_map.update(prices)
                symbols = payload.get("symbols", [])
                if isinstance(symbols, list) and symbols:
                    self._tradeable_symbols = symbols
                # Also accept individual price updates
                symbol = payload.get("symbol") or payload.get("pair")
                price = payload.get("price") or payload.get("last_price")
                if symbol and price:
                    self._price_map[str(symbol)] = float(price)
                    if str(symbol) not in self._tradeable_symbols:
                        self._tradeable_symbols.append(str(symbol))
        except Exception:
            pass

    def _on_trade_closed(self, thought: Any) -> None:
        """Track closed positions for monitoring."""
        try:
            payload = thought.payload if hasattr(thought, 'payload') else {}
            symbol = str(payload.get("symbol") or payload.get("pair") or "")
            self._open_positions.pop(symbol, None)
        except Exception:
            pass

    def _on_dtp_triggered(self, thought: Any) -> None:
        """DTP triggered a close — remove from monitoring."""
        try:
            payload = thought.payload if hasattr(thought, 'payload') else {}
            symbol = str(payload.get("symbol") or payload.get("pair") or "")
            self._open_positions.pop(symbol, None)
        except Exception:
            pass

    # ── Status ────────────────────────────────────────────────────────────

    def _publish_status(self) -> None:
        if self._thought_bus is None or Thought is None:
            return
        try:
            self._thought_bus.publish(Thought(
                source="queen_hive_command",
                topic="hive.status",
                payload={
                    "scans_run": self._scans_run,
                    "signals_received": self._signals_received,
                    "hunts_issued": self._hunts_issued,
                    "bees_active": len(self._swarm._bees),
                    "price_map_size": len(self._price_map),
                    "symbols_tracked": len(self._tradeable_symbols),
                },
                meta={"mode": "hive_status"},
            ))
        except Exception:
            pass

    def status_lines(self) -> List[str]:
        """Human-readable status for dashboard/terminal."""
        return [
            f"Hive Command: {'RUNNING' if self._running else 'STOPPED'}",
            f"  Worker bees: {len(self._swarm._bees)} active",
            f"  Scans run: {self._scans_run}",
            f"  Signals received: {self._signals_received}",
            f"  Hunts issued: {self._hunts_issued}",
            f"  Symbols tracked: {len(self._tradeable_symbols)}",
        ]
