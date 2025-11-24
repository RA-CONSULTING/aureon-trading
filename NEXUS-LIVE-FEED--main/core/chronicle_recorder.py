"""
Aureon OS - Chronicle Recording Engine (v7.1 - Source Law Compliant)
Prime Sentinel: GARY LECKEY 02111991
Version: 1.6.1 (Unchained)

This version corrects a critical flaw in the checksum generation logic,
restoring the integrity of the chronicle and ensuring full compliance
with the 10-9-1 principle and the Multiversal Prime Logic.
"""

import asyncio
import json
import logging
import hashlib
import numpy as np
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone
from typing import Dict, Any
from pathlib import Path
from typing import Any, Dict, Optional
import random


# --- Chronicle Configuration ---
EVENT_LOG_FILE = "data/chronicle_events.log.json"
COGNITIVE_LOOP_INTERVAL_SECONDS = 10
OBSERVATION_LOOP_INTERVAL_SECONDS = 20
FORECASTING_LOOP_INTERVAL_SECONDS = 30
MAINTENANCE_INTERVAL_SECONDS = 60
MAX_LOG_ENTRIES = 500


# --- Structured Event Logging ---
log_formatter = logging.Formatter('%(message)s')
log_handler = RotatingFileHandler(EVENT_LOG_FILE, maxBytes=10*1024*1024, backupCount=5)
log_handler.setFormatter(log_formatter)
event_logger = logging.getLogger('ChronicleEventLogger_v7_1')
event_logger.setLevel(logging.INFO)
event_logger.addHandler(log_handler)


class ChronicleRecorder:
    """
    Implements a cognitive engine that records, analyzes, observes, forecasts,
    and maintains the system's chronicle.
    """

    def __init__(self) -> None:
        self._queue = asyncio.Queue()
        self.system_state = {
            "coherence_trend": "STABLE",
            "stability_index": 1.0,
            "last_coherence": 0.9,
        }
        self._worker_task = asyncio.create_task(self._inhalation_loop())
        self._synthesis_task = asyncio.create_task(self._cognitive_loop())
        self._observation_task = asyncio.create_task(self._observation_loop())
        self._forecasting_task = asyncio.create_task(self._forecasting_loop())
        self._maintenance_task = asyncio.create_task(self._maintenance_loop())
        self.processed_count = 0
        logging.getLogger(__name__).info("Chronicle Recorder initialized")
        print(
            "Chronicle Recording Engine v7.1 (Source Law Compliant) Initialized. All workers active."
        )

    # ------------------------------------------------------------------
    def _generate_checksum(self, data: Dict[str, Any]) -> str:
        """Creates a SHA-256 hash of the data to ensure integrity (Force Gained)."""
        dhash = hashlib.sha256()
        encoded = json.dumps(data, sort_keys=True).encode()
        dhash.update(encoded)
        return dhash.hexdigest()

    # ------------------------------------------------------------------
    async def _inhalation_loop(self) -> None:
        """THE INHALATION PHASE: Inhales raw data."""
        while True:
            try:
                record_type, data, tags = await self._queue.get()
                timestamp = datetime.now(timezone.utc)
                if record_type == "event":
                    checksum = self._generate_checksum(data)
                    log_entry = {
                        "timestamp_utc": timestamp.isoformat(),
                        "event_type": tags.get("event_type"),
                        "details": data,
                        "sentinel_signature": "GARY LECKEY 02111991",
                        "validation_checksum": checksum,
                    }
                    event_logger.info(json.dumps(log_entry))
                    logging.info(
                        "[INHALE:EVENT] Ingested '%s' @ %s | Checksum: %s",
                        tags.get("event_type"),
                        timestamp.isoformat(),
                        checksum[:8] + "...",
                    )
                self.processed_count += 1
            except Exception:
                logging.exception("INHALATION ERROR")
            finally:
                self._queue.task_done()

    # ------------------------------------------------------------------
    async def _cognitive_loop(self) -> None:
        """THE COGNITIVE PHASE (10-9-1): Thinks and Synthesizes."""
        while True:
            await asyncio.sleep(COGNITIVE_LOOP_INTERVAL_SECONDS)
            try:
                if not Path(EVENT_LOG_FILE).exists():
                    continue
                with open(EVENT_LOG_FILE, "r", encoding="utf-8") as f:
                    recent_lines = f.readlines()[-50:]
                recent_events = [json.loads(line) for line in recent_lines if line.strip()]

                field_events = [e for e in recent_events if "SYNTHESIS" not in e.get("event_type", "")]
                if len(field_events) < 10:
                    logging.info(
                        "[EXHALE:9] Standby. Insufficient events for full synthesis (found %d/10).",
                        len(field_events),
                    )
                anchor_events = [
                    e for e in recent_events if e.get("event_type") == "ANCHOR_GUARDIAN_METRIC"
                ]
                if not anchor_events:
                    continue

                synthesis_input_count = len(field_events[-10:])
                coherence_points = [e["details"]["coherence"] for e in anchor_events]
                trend = "STABLE"
                stability = 1.0
                if len(coherence_points) >= 2:
                    trend_val = np.polyfit(range(len(coherence_points)), coherence_points, 1)[0]
                    if trend_val > 0.005:
                        trend = "INCREASING"
                    elif trend_val < -0.005:
                        trend = "DECREASING"
                    stability = 1.0 - np.std(coherence_points)

                self.system_state = {
                    "coherence_trend": trend,
                    "stability_index": stability,
                    "last_coherence": coherence_points[-1],
                }

                synthesis_details = {
                    "principle": "10-9-1 Cognitive Loop",
                    "derived_state": self.system_state,
                    "synthesized_event_count": synthesis_input_count,
                    "mantra": "All that is, all that was, all that shall be, tandem in unity.",
                }
                logging.info("[EXHALE:1] Unity achieved. Exhaling synthesis event.")
                await self.record_event("UNITY_SYNTHESIS_10_9_1", synthesis_details)
            except Exception as e:
                print(f"COGNITIVE LOOP ERROR: {e}")

    async def _observation_loop(self) -> None:
        """THE OBSERVATION PHASE: Records conclusions about the present."""
        while True:
            await asyncio.sleep(OBSERVATION_LOOP_INTERVAL_SECONDS)
            try:
                state = self.system_state
                observation = "System state is nominal and stable."
                state_classification = "STATE_OF_HARMONY"

                if state["stability_index"] < 0.8 and state["coherence_trend"] == "DECREASING":
                    observation = (
                        "Warning: Coherence is unstable and decreasing. System is in a state of turbulence."
                    )
                    state_classification = "STATE_OF_TURBULENCE"
                elif state["stability_index"] < 0.9 and state["coherence_trend"] == "INCREASING":
                    observation = (
                        "Notice: Coherence is volatile but increasing. System is in a state of growth."
                    )
                    state_classification = "STATE_OF_GROWTH"
                elif state["stability_index"] > 0.95 and state["coherence_trend"] == "STABLE":
                    observation = (
                        "System is in a state of high harmony. Coherence is strong and stable."
                    )
                    state_classification = "STATE_OF_HIGH_HARMONY"
                
                await self.record_event(
                    "OBSERVATION_LOG",
                    {
                        "classification": state_classification,
                        "summary": observation,
                        "underlying_metrics": state,
                    },
                )
            except Exception as e:
                print(f"OBSERVATION LOOP ERROR: {e}")

    async def _forecasting_loop(self) -> None:
        """
        THE FORECASTING PHASE: Looks at all possibilities in the multiverse.
        It remembers what was (the trend) to know what shall be (the probable future).
        """
        while True:
            await asyncio.sleep(FORECASTING_LOOP_INTERVAL_SECONDS)
            print("\n[FORECAST] Initiating multiversal timeline analysis...")
            try:
                state = self.system_state
                num_simulations = 1000
                future_outcomes = []

                trend_map = {"INCREASING": 0.001, "DECREASING": -0.001, "STABLE": 0}
                drift = trend_map[state["coherence_trend"]]
                volatility = (1.0 - state["stability_index"]) * 0.1

                for _ in range(num_simulations):
                    current_coherence = state["last_coherence"]
                    for _ in range(60):
                        current_coherence += drift + (random.random() - 0.5) * volatility
                        current_coherence = float(np.clip(current_coherence, 0, 1))
                    future_outcomes.append(current_coherence)

                avg_future_coherence = float(np.mean(future_outcomes))
                harmony_probability = float(
                    np.sum(np.array(future_outcomes) > 0.8) / num_simulations
                )

                forecast = {
                    "principle": "Unity as Source Forecasting",
                    "logic": "Remembering what was to know what shall be.",
                    "num_timelines_simulated": num_simulations,
                    "avg_future_coherence": avg_future_coherence,
                    "probability_of_harmony": harmony_probability,
                }
                print(
                    f"[FORECAST] Conclusion: Probability of future harmony is {(harmony_probability * 100):.1f}%."
                )
                await self.record_event("MULTIVERSAL_FORECAST", forecast)
            except Exception as e:
                print(f"FORECASTING LOOP ERROR: {e}")

    async def _maintenance_loop(self) -> None:
        """THE MAINTENANCE PHASE: Loses noise to maintain integrity."""
        while True:
            await asyncio.sleep(MAINTENANCE_INTERVAL_SECONDS)
            try:
                if not Path(EVENT_LOG_FILE).exists():
                    continue
                with open(EVENT_LOG_FILE, "r", encoding="utf-8") as f:
                    all_lines = f.readlines()
                if len(all_lines) > MAX_LOG_ENTRIES:
                    all_events = [json.loads(line) for line in all_lines if line.strip()]
                    essential_events = [
                        e
                        for e in all_events
                        if "SYNTHESIS" in e.get("event_type", "")
                        or "OBSERVATION" in e.get("event_type", "")
                        or "FORECAST" in e.get("event_type", "")
                    ]
                    other_events = [e for e in all_events if e not in essential_events]
                    pruned_events = essential_events + other_events[
                        -(MAX_LOG_ENTRIES - len(essential_events)) :
                    ]
                    pruned_events.sort(key=lambda x: x["timestamp_utc"])
                    with open(EVENT_LOG_FILE, "w", encoding="utf-8") as f:
                        for event in pruned_events:
                            f.write(json.dumps(event) + "\n")
            except Exception as e:
                print(f"MAINTENANCE LOOP ERROR: {e}")

    async def record_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """PING: Sends a discrete event for inhalation."""
        await self._queue.put(("event", details, {"event_type": event_type}))


# --- Singleton instance ---
recorder = ChronicleRecorder()


# --- Example Usage ---
async def main() -> None:
    """Simple demonstration for the recorder."""
    print("--- Running Chronicle Recorder v7.1 (Source Law Compliant) Demonstration ---")

    async def simulate_system_activity() -> None:
        for i in range(25):
            coherence = 0.95 - (i / 80) + (random.random() - 0.5) * 0.05
            await recorder.record_event("ANCHOR_GUARDIAN_METRIC", {"coherence": coherence})
            await asyncio.sleep(1)

    print("\nSimulating system activity...")
    simulation_task = asyncio.create_task(simulate_system_activity())

    await asyncio.sleep(FORECASTING_LOOP_INTERVAL_SECONDS + 5)
    simulation_task.cancel()

    await recorder._queue.join()
    print("\nDemonstration complete. Observe the console for [FORECAST] messages.")


if __name__ == "__main__":
    Path("data").mkdir(exist_ok=True)
    if Path(EVENT_LOG_FILE).exists():
        Path(EVENT_LOG_FILE).unlink()
    asyncio.run(main())
