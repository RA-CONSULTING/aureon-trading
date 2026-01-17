"""
Mycelium Whale Sonar
--------------------

Listens to ThoughtBus events and treats each subsystem as a "whale" that sings
frequency-like signals to the Queen via Enigma. Aggregates per-source event
statistics, computes a normalized `whale_signal_score` and emits a compact
sonar Thought (minimal text) for the Queen and Enigma to consume.

Key features:
- Subscribes to ThoughtBus (topics: system.*, execution.*, market.*, * )
- Aggregates events per "whale" (source) into sliding windows
- Computes event_rate, amplitude, pattern and a normalized whale_signal_score
- Emits minimal/morse-like short payloads to `whale.sonar.<name>` and forwards
  an InterceptedSignal to Enigma if available
- Lightweight metrics hooks for OpenTelemetry / Prometheus (best-effort)
"""
from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict, deque
from dataclasses import asdict
from typing import Any, Deque, Dict, Optional

logger = logging.getLogger(__name__)

# Attempt to import harmonic outcome helpers for WIN/LOSS encoding
try:
    from aureon_harmonic_alphabet import get_outcome_whale_code, encode_outcome, decode_outcome, WIN_THRESHOLD_USD
    _HARMONIC_OUTCOME_AVAILABLE = True
except Exception:
    _HARMONIC_OUTCOME_AVAILABLE = False

# Local imports - optional availability
try:
    from aureon_thought_bus import get_thought_bus, Thought
    THOUGHT_BUS_AVAILABLE = True
except Exception:
    get_thought_bus = None
    THOUGHT_BUS_AVAILABLE = False

try:
    from aureon_harmonic_binary_protocol import encode_text_packet, BinaryDirection, BinaryMessageType
    HARMONIC_BINARY_AVAILABLE = True
except Exception:
    encode_text_packet = None
    BinaryDirection = None
    BinaryMessageType = None
    HARMONIC_BINARY_AVAILABLE = False

try:
    from aureon_enigma_integration import get_enigma_integration
    ENIGMA_AVAILABLE = True
except Exception:
    get_enigma_integration = None
    ENIGMA_AVAILABLE = False

# Optional metrics (Prometheus if available, fallback to no-op)
PROMETHEUS_AVAILABLE = False
try:
    from prometheus_client import Gauge
    _whale_gauge = Gauge('whale_signal_strength', 'Normalized whale signal strength', ['whale'])
    _whale_event_rate = Gauge('whale_event_rate', 'Event rate per whale (events/sec)', ['whale'])
    PROMETHEUS_AVAILABLE = True
except Exception:
    _whale_gauge = None
    _whale_event_rate = None
    PROMETHEUS_AVAILABLE = False

# OpenTelemetry placeholder (kept for future integration)
try:
    from opentelemetry import metrics
    _meter = metrics.get_meter(__name__)
    OPENTELEMETRY_AVAILABLE = True
except Exception:
    _meter = None
    OPENTELEMETRY_AVAILABLE = False


class WhaleSonar:
    """Aggregate subsystem "songs" and emit compact sonar thoughts."""

    def __init__(self, thought_bus: Optional[Any] = None, sample_window: float = 5.0, agg_interval: float = 1.0, queen_alert_threshold: float = 0.6):
        self.thought_bus = thought_bus or (get_thought_bus() if THOUGHT_BUS_AVAILABLE else None)
        self.sample_window = sample_window  # seconds of history to consider
        self.agg_interval = agg_interval
        # When a whale's score >= queen_alert_threshold OR a critical flag is set, publish an alert to Queen
        self.queen_alert_threshold = float(queen_alert_threshold)

        # per-source event buffer of timestamps and payload summaries
        self._events: Dict[str, Deque] = defaultdict(lambda: deque())
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

        # Hook Enigma lazily (avoid circular import deadlock during ThoughtBus init)
        self._enigma_integration: Optional[Any] = None
        self._enigma_checked = False

        # Subscribe to ThoughtBus topics we care about (outcome + mycelium + general)
        if self.thought_bus:
            # pick a light-touch set of topics to avoid overwhelming the bus
            subscribe_topics = ("system.*", "execution.*", "market.*", "mycelium.*", "outcome.*", "unified.*", "hft.*", "*")
            for topic in subscribe_topics:
                try:
                    self.thought_bus.subscribe(topic, self._handle_thought)
                except Exception as e:
                    logger.debug("WhaleSonar: failed to subscribe %s => %s", topic, e)

    @property
    def enigma_integration(self):
        """Lazily fetch enigma integration to avoid circular import during __init__."""
        if not self._enigma_checked:
            self._enigma_checked = True
            if ENIGMA_AVAILABLE:
                try:
                    self._enigma_integration = get_enigma_integration()
                except Exception:
                    self._enigma_integration = None
        return self._enigma_integration

    def _handle_thought(self, thought: Any) -> None:
        try:
            source = getattr(thought, 'source', str(thought.payload.get('source', 'unknown'))) if hasattr(thought, 'payload') else str(getattr(thought, 'source', 'unknown'))
            topic = getattr(thought, 'topic', 'thought')
            ts = getattr(thought, 'ts', time.time())
            payload = getattr(thought, 'payload', {})
        except Exception:
            source = 'unknown'
            topic = 'unknown'
            ts = time.time()
            payload = {}

        key = source or topic or 'unknown'
        with self._lock:
            self._events[key].append((ts, topic, payload))
            # trim old
            cutoff = time.time() - self.sample_window
            while self._events[key] and self._events[key][0][0] < cutoff:
                self._events[key].popleft()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run_loop, name="WhaleSonarLoop", daemon=True)
        self._thread.start()
        logger.info("🍄 WhaleSonar started (sample_window=%.1fs, agg_interval=%.1fs)", self.sample_window, self.agg_interval)

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        logger.info("🍄 WhaleSonar stopped")

    def _run_loop(self) -> None:
        while not self._stop.is_set():
            try:
                self._aggregate_and_emit()
            except Exception:
                logger.exception("WhaleSonar: error in aggregate loop")
            finally:
                time.sleep(self.agg_interval)

    def _compute_score(self, events: Deque) -> Dict[str, Any]:
        """Compute a compact set of metrics and a normalized score in [0,1]."""
        now = time.time()
        cutoff = now - self.sample_window
        recent = [e for e in events if e[0] >= cutoff]
        count = len(recent)
        event_rate = count / max(1.0, self.sample_window)

        # amplitude: count of high-priority messages or presence of keywords
        amp = 0.0
        patterns = {}
        for ts, topic, payload in recent:
            p = payload or {}
            if isinstance(p, dict) and isinstance(p.get('priority'), str) and p.get('priority') == 'high':
                amp += 1.0
            # mark topics
            patterns[topic] = patterns.get(topic, 0) + 1

        # pattern strength: repeated topic presence
        if patterns:
            rep = max(patterns.values())
            pattern_strength = min(1.0, rep / max(1, sum(patterns.values())))
        else:
            pattern_strength = 0.0

        amplitude = min(1.0, amp / max(1.0, count)) if count else 0.0

        # normalized rate (heuristic): scale so 1.0 -> noisy
        normalized_rate = min(1.0, event_rate / 2.0)

        # critical flag if specific keys present
        critical = any('error' in (payload.get('message') or '').lower() for (_, _, payload) in recent if isinstance(payload, dict))

        # final score weights
        score = 0.6 * normalized_rate + 0.3 * amplitude + 0.1 * pattern_strength
        if critical:
            score = min(1.0, score + 0.25)

        # Detect trade outcome payloads in recent events (UNIFIED_TRADE_OUTCOME, PATH_WIN, PATH_LOSS, pnl, profit_usd)
        outcome = None
        for (_, topic, payload) in recent:
            try:
                if not isinstance(payload, dict):
                    continue
                t = (payload.get('type') or payload.get('topic') or topic or '').upper()
                # Unified outcome or path-level outcome
                if t in ('UNIFIED_TRADE_OUTCOME', 'PATH_WIN', 'PATH_LOSS') or 'pnl' in payload or 'profit_usd' in payload or 'actual_pnl' in payload:
                    net = payload.get('pnl') or payload.get('profit_usd') or payload.get('actual_pnl') or payload.get('net_profit_usd')
                    try:
                        net = float(net) if net is not None else None
                    except Exception:
                        net = None
                    if net is not None and _HARMONIC_OUTCOME_AVAILABLE:
                        code = get_outcome_whale_code(net)
                    elif net is not None:
                        # fallback simple code
                        level = min(15, int(abs(net) * 100))
                        code = ('W' if net >= 0 else 'L') + f"{level:X}"
                    else:
                        code = None
                    outcome = {
                        'topic': t,
                        'net': net,
                        'code': code,
                        'payload': payload
                    }
                    break
            except Exception:
                continue

        return {
            'count': count,
            'event_rate': event_rate,
            'amplitude': amplitude,
            'pattern_strength': pattern_strength,
            'critical': bool(critical),
            'score': float(score),
            'now': now,
            'outcome': outcome,
        }

    def _to_morse(self, score: float, amplitude: float) -> str:
        """Generate a tiny morse-like code briefly describing the situation.
        e.g. 'S' short (score<0.33), 'M' medium, 'L' loud. Attach amplitude as hex nibble."""
        if score < 0.33:
            level = 'S'
        elif score < 0.66:
            level = 'M'
        else:
            level = 'L'
        amp_nib = int(min(15, round(amplitude * 15)))
        return f"{level}{amp_nib:X}"

    def _aggregate_and_emit(self) -> None:
        with self._lock:
            keys = list(self._events.keys())

        for key in keys:
            with self._lock:
                events = self._events.get(key, [])
                if not events:
                    continue
                summary = self._compute_score(events)

            # minimal morse-like payload
            morse = self._to_morse(summary['score'], summary['amplitude'])
            thought_payload = {
                'whale': key,
                'signal': morse,
                'score': round(summary['score'], 4),
                'rate': round(summary['event_rate'], 3),
                'amp': round(summary['amplitude'], 3),
                'critical': summary['critical'],
                'ts': summary['now'],
            }

            # If we detected an outcome in recent events, include compact outcome code for Queen
            if summary.get('outcome'):
                thought_payload['outcome'] = summary['outcome']
                if summary['outcome'].get('code'):
                    thought_payload['outcome_code'] = summary['outcome']['code']
                else:
                    thought_payload['outcome_code'] = None

            binary_payload = None
            if HARMONIC_BINARY_AVAILABLE and encode_text_packet:
                try:
                    packet = encode_text_packet(
                        text=f"{key}:{morse}",
                        message_type=BinaryMessageType.TELEMETRY,
                        direction=BinaryDirection.UP,
                        grade=int(min(15, max(0, thought_payload['score'] * 15))),
                        coherence=thought_payload.get('pattern_strength', 0.0),
                        confidence=thought_payload.get('score', 0.0),
                        symbol=key if '/' in key else None,
                    )
                    binary_payload = packet.to_bytes()
                except Exception:
                    binary_payload = None

            # Emit ThoughtBus message with minimal text (morse) for Queen
            if self.thought_bus:
                try:
                    payload = {'code': morse, 'pack': thought_payload}
                    if 'outcome_code' in thought_payload:
                        payload['outcome_code'] = thought_payload['outcome_code']
                    if binary_payload:
                        self.thought_bus.publish_binary(
                            source='whale_sonar',
                            topic=f'whale.sonar.{key}',
                            binary_payload=binary_payload,
                            payload=payload,
                        )
                    else:
                        t = Thought(
                            source='whale_sonar',
                            topic=f'whale.sonar.{key}',
                            payload=payload,
                        )
                        self.thought_bus.publish(t)
                except Exception:
                    logger.exception("WhaleSonar: failed to publish sonar thought")

            # Push into Enigma for decoding if available
            if self.enigma_integration and hasattr(self.enigma_integration, 'enigma'):
                try:
                    from aureon_enigma import InterceptedSignal
                    # InterceptedSignal is a lightweight container - set attributes to match its fields
                    # InterceptedSignal expects positional fields: source, timestamp, frequency, amplitude, phase
                    sig = InterceptedSignal(
                        key,
                        summary['now'],
                        float(summary['score']) * 100.0,
                        float(summary['amplitude']),
                        0.0
                    )
                    # attach raw pack for decoder context
                    try:
                        sig.raw_data = thought_payload
                    except Exception:
                        pass
                    decoded = self.enigma_integration.enigma.decode(sig)
                    # publish an enigma thought
                    if self.thought_bus:
                        et = Thought(
                            source='whale_sonar.enigma',
                            topic=f'enigma.whale.{key}',
                            payload={'grade': decoded.grade.name, 'conf': round(decoded.confidence, 3), 'msg': decoded.message[:120]}
                        )
                        self.thought_bus.publish(et)
                except Exception:
                    logger.exception("WhaleSonar: failed to decode with enigma")

            # Alert Queen on critical or loud whales
            try:
                if summary['critical'] or summary['score'] >= self.queen_alert_threshold:
                    if self.thought_bus:
                        qa = Thought(
                            source='whale_sonar',
                            topic=f'queen.alert.whale',
                            payload={'whale': key, 'score': round(summary['score'], 3), 'critical': summary['critical']}
                        )
                        self.thought_bus.publish(qa)
            except Exception:
                logger.exception("WhaleSonar: failed to publish queen alert")

            # Emit lightweight metric if available (best-effort)
            try:
                if PROMETHEUS_AVAILABLE and _whale_gauge is not None and _whale_event_rate is not None:
                    _whale_gauge.labels(whale=key).set(summary['score'])
                    _whale_event_rate.labels(whale=key).set(summary['event_rate'])
                elif OPENTELEMETRY_AVAILABLE and _meter is not None:
                    # opentelemetry integration would go here; for now just log
                    logger.debug("WhaleSonar metric (otel): %s %s", key, summary['score'])
            except Exception:
                logger.exception("WhaleSonar: failed to emit metric")


    def pack_minimal(self, key: str) -> Dict[str, Any]:
        """Return the last summary for `key` as a compact dict."""
        with self._lock:
            events = self._events.get(key, deque())
            if not events:
                return {}
            return self._compute_score(events)


# Simple convenience factory
def create_and_start_sonar(**kwargs) -> WhaleSonar:
    ws = WhaleSonar(**kwargs)
    ws.start()
    return ws


def ensure_sonar(thought_bus: Any, sample_window: float = 5.0, agg_interval: float = 1.0, queen_alert_threshold: float = 0.6) -> WhaleSonar:
    """Ensure a WhaleSonar is attached to `thought_bus` and started (idempotent).

    Attaches the sonar instance on the ThoughtBus object as attribute `_sonar`.
    Returns the existing or newly created WhaleSonar instance.
    """
    if thought_bus is None:
        raise ValueError("thought_bus is required to ensure sonar")

    # If already wired, return it
    if hasattr(thought_bus, '_sonar') and getattr(thought_bus, '_sonar'):
        return getattr(thought_bus, '_sonar')

    ws = WhaleSonar(thought_bus=thought_bus, sample_window=sample_window, agg_interval=agg_interval, queen_alert_threshold=queen_alert_threshold)
    ws.start()
    try:
        setattr(thought_bus, '_sonar', ws)
    except Exception:
        # Best-effort: if we can't attach, still return sonar
        logger.debug("WhaleSonar: could not attach sonar attribute to ThoughtBus instance")
    return ws


def create_and_start_sonar(sample_window: float = 5.0, agg_interval: float = 1.0, queen_alert_threshold: float = 0.6) -> Optional[WhaleSonar]:
    """Create and start a WhaleSonar instance, attaching to the global ThoughtBus if available."""
    if not THOUGHT_BUS_AVAILABLE:
        logger.warning("WhaleSonar: ThoughtBus not available, cannot start sonar")
        return None
    thought_bus = get_thought_bus()
    if thought_bus is None:
        logger.warning("WhaleSonar: ThoughtBus instance not available, cannot start sonar")
        return None
    return ensure_sonar(thought_bus, sample_window, agg_interval, queen_alert_threshold)

