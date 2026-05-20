#!/usr/bin/env python3
"""Static flight check for Capital trader mind-map/Mycelium/probability wiring."""

from __future__ import annotations

import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Iterator

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "aureon" / "exchanges") not in sys.path:
    sys.path.insert(0, str(ROOT / "aureon" / "exchanges"))
if str(ROOT / "aureon" / "core") not in sys.path:
    sys.path.insert(0, str(ROOT / "aureon" / "core"))

from aureon.exchanges import capital_cfd_trader as capital_module


@contextmanager
def _capital_disabled_env() -> Iterator[None]:
    keys = ("CAPITAL_API_KEY", "CAPITAL_IDENTIFIER", "CAPITAL_PASSWORD")
    backup = {key: os.environ.get(key) for key in keys}
    try:
        for key in keys:
            os.environ.pop(key, None)
        yield
    finally:
        for key, value in backup.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def run_flight_check() -> Dict[str, object]:
    with _capital_disabled_env():
        originals = {
            "HAS_UNIFIED_REGISTRY": capital_module.HAS_UNIFIED_REGISTRY,
            "get_unified_puller": capital_module.get_unified_puller,
            "HAS_UNIFIED_DECISION": capital_module.HAS_UNIFIED_DECISION,
            "UnifiedDecisionEngine": capital_module.UnifiedDecisionEngine,
            "HAS_CAPITAL_ORCHESTRATOR": capital_module.HAS_CAPITAL_ORCHESTRATOR,
            "AutonomousOrchestrator": capital_module.AutonomousOrchestrator,
            "HAS_TIMELINE_ORACLE": capital_module.HAS_TIMELINE_ORACLE,
            "get_timeline_oracle": capital_module.get_timeline_oracle,
            "HAS_HARMONIC_FUSION": capital_module.HAS_HARMONIC_FUSION,
            "HarmonicWaveFusion": capital_module.HarmonicWaveFusion,
            "HAS_THOUGHT_BUS": capital_module.HAS_THOUGHT_BUS,
            "get_thought_bus": capital_module.get_thought_bus,
            "Thought": capital_module.Thought,
            "_ensure_client_ready": capital_module.CapitalCFDTrader._ensure_client_ready,
        }
        capital_module.HAS_UNIFIED_REGISTRY = False
        capital_module.get_unified_puller = None
        capital_module.HAS_UNIFIED_DECISION = False
        capital_module.UnifiedDecisionEngine = None
        capital_module.HAS_CAPITAL_ORCHESTRATOR = False
        capital_module.AutonomousOrchestrator = None
        capital_module.HAS_TIMELINE_ORACLE = False
        capital_module.get_timeline_oracle = None
        capital_module.HAS_HARMONIC_FUSION = False
        capital_module.HarmonicWaveFusion = None
        capital_module.HAS_THOUGHT_BUS = False
        capital_module.get_thought_bus = None
        capital_module.Thought = None

        def _disabled_client_ready(self, force: bool = False) -> bool:
            self.client = None
            self.init_error = "validation_client_disabled"
            return False

        capital_module.CapitalCFDTrader._ensure_client_ready = _disabled_client_ready
        try:
            trader = capital_module.CapitalCFDTrader()
            trader._refresh_mind_map_snapshot(force=True)
            trader._refresh_mycelium_snapshot(force=True)
            trader._refresh_live_system_activity_snapshot()
            trader._refresh_probability_feed_snapshot()
        finally:
            capital_module.HAS_UNIFIED_REGISTRY = originals["HAS_UNIFIED_REGISTRY"]
            capital_module.get_unified_puller = originals["get_unified_puller"]
            capital_module.HAS_UNIFIED_DECISION = originals["HAS_UNIFIED_DECISION"]
            capital_module.UnifiedDecisionEngine = originals["UnifiedDecisionEngine"]
            capital_module.HAS_CAPITAL_ORCHESTRATOR = originals["HAS_CAPITAL_ORCHESTRATOR"]
            capital_module.AutonomousOrchestrator = originals["AutonomousOrchestrator"]
            capital_module.HAS_TIMELINE_ORACLE = originals["HAS_TIMELINE_ORACLE"]
            capital_module.get_timeline_oracle = originals["get_timeline_oracle"]
            capital_module.HAS_HARMONIC_FUSION = originals["HAS_HARMONIC_FUSION"]
            capital_module.HarmonicWaveFusion = originals["HarmonicWaveFusion"]
            capital_module.HAS_THOUGHT_BUS = originals["HAS_THOUGHT_BUS"]
            capital_module.get_thought_bus = originals["get_thought_bus"]
            capital_module.Thought = originals["Thought"]
            capital_module.CapitalCFDTrader._ensure_client_ready = originals["_ensure_client_ready"]

    payload = trader.get_dashboard_payload()
    return {
        "mind_map": payload.get("mind_map_snapshot", {}),
        "mycelium": payload.get("mycelium_snapshot", {}),
        "runtime": payload.get("live_system_activity", {}),
        "probability_feed": payload.get("probability_feed_snapshot", {}),
    }


def main() -> int:
    report = run_flight_check()
    print("=" * 80)
    print("CAPITAL TRADER FLIGHT CHECK (MIND MAP + MYCELIUM + PROBABILITY)")
    print("=" * 80)
    print(json.dumps(report, indent=2, default=str))

    mind_ok = bool((report.get("mind_map") or {}).get("ok"))
    mycelium_ok = bool((report.get("mycelium") or {}).get("ok"))
    runtime = report.get("runtime") or {}
    feed = report.get("probability_feed") or {}

    print("\nSUMMARY")
    print(f"- Mind map wiring: {'PASS' if mind_ok else 'FAIL'}")
    print(f"- Mycelium wiring: {'PASS' if mycelium_ok else 'FAIL'}")
    print(
        f"- Runtime visibility: {int(runtime.get('active_systems', 0) or 0)}/"
        f"{int(runtime.get('total_systems', 0) or 0)} systems active"
    )
    print(f"- Probability topic: {feed.get('topic', 'missing')}")

    return 0 if mind_ok and mycelium_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
