#!/usr/bin/env python3
"""
AUREON IGNITION -- One Switch. Everything Fires.

This is the master launcher. One command boots the entire Aureon operating
system: ThoughtBus, ChirpBus, Queen Hive Mind, Cortex brainwave layers,
Source Law consciousness funnel, Mycelium Mind, Metacognition mirror,
Sentient Loop, 60 queen modules, 50+ domain systems, Intelligence Engine,
Feed Hub, Whale Sonar, HFT Engine, Micro Profit Labyrinth, API Server,
and the autonomous trading loop.

    python scripts/aureon_ignition.py              # DRY-RUN mode
    python scripts/aureon_ignition.py --live        # LIVE TRADING
    python scripts/aureon_ignition.py --live --no-trade  # Boot only, no loop

The Queen boots first. All systems activate beneath her.
Then the trading loop runs until Ctrl+C.

Gary Leckey & Tina Brown | April 2026 | The Ignition Switch
"""

import os
import sys
import signal
import time
import logging
import argparse
from datetime import datetime
from pathlib import Path

# ============================================================================
# PATH SETUP -- ensure all aureon modules are importable
# ============================================================================

_REPO_ROOT = Path(__file__).resolve().parents[1]
_AUREON_DIR = _REPO_ROOT / "aureon"

# Add repo root and all aureon subdirectories to sys.path
sys.path.insert(0, str(_REPO_ROOT))
for sub in sorted(_AUREON_DIR.iterdir()):
    if sub.is_dir() and not sub.name.startswith(("_", ".")):
        p = str(sub)
        if p not in sys.path:
            sys.path.insert(0, p)

# Ensure scripts/ is in path for legacy runners
_SCRIPTS = _REPO_ROOT / "scripts"
if _SCRIPTS.exists():
    for sub in sorted(_SCRIPTS.iterdir()):
        if sub.is_dir() and not sub.name.startswith(("_", ".")):
            p = str(sub)
            if p not in sys.path:
                sys.path.insert(0, p)

os.chdir(str(_REPO_ROOT))  # Runtime JSONs live at repo root


# ============================================================================
# LOGGING
# ============================================================================

def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(level=level, format=fmt, datefmt="%H:%M:%S")
    # Quiet down noisy libraries
    for name in ("urllib3", "asyncio", "websockets", "httpx"):
        logging.getLogger(name).setLevel(logging.WARNING)


# ============================================================================
# BANNER
# ============================================================================

def print_banner():
    print("""
================================================================================

     A U R E O N   I G N I T I O N

     One switch. Everything fires.
     The Queen boots first. All systems activate beneath her.

     "We don't need data centers. We have the quantum space."
                                    -- Gary Leckey, April 2026

================================================================================
""")


# ============================================================================
# PHASE 0: BOOT THE QUEEN LAYER (all 6 phases inside)
# ============================================================================

def ignite_queen(live_trading: bool = False):
    """Boot the entire Queen Layer -- 6 phases, ~100+ systems."""
    from queen_layer import boot_queen_layer, get_queen_layer

    print("[IGNITION] Phase 0: Booting Queen Layer (6 internal phases)...\n")
    health = boot_queen_layer(live_trading=live_trading)

    layer = get_queen_layer()
    print(f"\n[IGNITION] Queen Layer: {health['online']}/{health['total']} systems ONLINE")

    return layer, health


# ============================================================================
# PHASE 1: WIRE EXECUTION SYSTEMS (from master launcher)
# ============================================================================

def wire_execution(layer):
    """Wire HFT, Enigma, and additional execution systems."""
    print("\n[IGNITION] Wiring execution systems...")

    queen = layer.queen
    labyrinth = layer.labyrinth
    wired = 0

    if not queen or not labyrinth:
        print("   Queen or Labyrinth not available -- execution wiring skipped")
        return wired

    # Enigma integration
    try:
        from aureon_enigma_integration import get_enigma_integration
        enigma = get_enigma_integration()
        if hasattr(queen, "wire_enigma"):
            queen.wire_enigma(enigma)
            wired += 1
    except Exception:
        pass

    # HFT Engine
    try:
        from aureon_hft_harmonic_mycelium import get_hft_engine
        hft = get_hft_engine()
        if hasattr(queen, "wire_hft_engine"):
            queen.wire_hft_engine(hft)
            wired += 1
    except Exception:
        pass

    # HFT Order Router
    try:
        from aureon_hft_websocket_order_router import get_order_router
        router = get_order_router()
        if hasattr(router, "wire_exchange_clients"):
            clients = {}
            for name in ("kraken", "binance", "alpaca"):
                client = getattr(labyrinth, name, None)
                if client:
                    clients[name] = client
            if clients:
                router.wire_exchange_clients(clients)
        if hasattr(queen, "wire_hft_order_router"):
            queen.wire_hft_order_router(router)
            wired += 1
    except Exception:
        pass

    # Harmonic signal chain + alphabet
    try:
        from aureon_harmonic_signal_chain import HarmonicSignalChain
        chain = HarmonicSignalChain()
        if hasattr(queen, "harmonic_signal_chain"):
            queen.harmonic_signal_chain = chain
            wired += 1
    except Exception:
        pass

    try:
        from aureon_harmonic_alphabet import HarmonicAlphabet
        alpha = HarmonicAlphabet()
        if hasattr(queen, "harmonic_alphabet"):
            queen.harmonic_alphabet = alpha
            wired += 1
    except Exception:
        pass

    print(f"   Execution wiring: {wired} additional systems connected")
    return wired


# ============================================================================
# PHASE 2: FLIGHT CHECK
# ============================================================================

def flight_check(layer):
    """Validate end-to-end connections before autonomous trading."""
    print("\n[IGNITION] Running system flight check...")

    queen = layer.queen
    health = layer.get_health()

    checks = {
        "queen_online": queen is not None,
        "queen_control": getattr(queen, "has_full_control", False) if queen else False,
        "trading_enabled": getattr(queen, "trading_enabled", False) if queen else False,
        "labyrinth": layer.labyrinth is not None,
        "thought_bus": layer.thought_bus is not None,
    }

    # Check critical subsystems
    for name in ("queen_cortex", "queen_source_law", "queen_mycelium_mind",
                 "queen_metacognition", "queen_sentient_loop",
                 "real_intelligence_engine", "dr_auris_throne"):
        info = layer.registry.get(name, {})
        checks[name] = info.get("status") == "ONLINE"

    passed = sum(1 for v in checks.values() if v)
    total = len(checks)

    print(f"   Flight check: {passed}/{total} systems GO")
    for name, ok in checks.items():
        status = "GO" if ok else "NO-GO"
        if not ok:
            print(f"   {status}: {name}")

    return checks


# ============================================================================
# PHASE 3: AUTONOMOUS TRADING LOOP
# ============================================================================

def run_trading_loop(layer):
    """The main autonomous trading loop under Prime Sentinel authority."""
    queen = layer.queen
    labyrinth = layer.labyrinth

    # Gather intelligence imports
    hub = None
    try:
        from aureon_real_data_feed_hub import get_feed_hub
        hub = get_feed_hub()
    except Exception:
        pass

    wiring_status_fn = None
    try:
        from aureon_system_wiring import get_wiring_status
        wiring_status_fn = get_wiring_status
    except Exception:
        pass

    print("\n" + "=" * 80)
    print("  AUTONOMOUS TRADING ACTIVE -- Prime Sentinel Authority")
    print("  Press Ctrl+C to stop")
    print("=" * 80 + "\n")

    cycle = 0
    while True:
        cycle += 1
        ts = datetime.now().strftime("%H:%M:%S")

        try:
            # Gather and distribute intelligence
            intel_summary = {}
            if hub and hasattr(hub, "gather_and_distribute"):
                try:
                    prices = {}
                    if labyrinth and hasattr(labyrinth, "get_all_prices"):
                        prices = labyrinth.get_all_prices() or {}
                    intel_summary = hub.gather_and_distribute(prices) or {}
                except Exception:
                    pass

            stats = intel_summary.get("stats", {})
            bots = stats.get("bots_detected", 0)
            whales = stats.get("whales_predicted", 0)
            validated = stats.get("validated_signals", 0)

            # Wiring status
            events = 0
            if wiring_status_fn:
                try:
                    ws = wiring_status_fn()
                    events = ws.get("total_events", 0)
                except Exception:
                    pass

            # Cortex state
            cortex_info = ""
            cortex_entry = layer.registry.get("queen_cortex", {})
            cortex = cortex_entry.get("instance")
            if cortex and hasattr(cortex, "get_dominant_band"):
                band = cortex.get_dominant_band()
                cortex_info = f" | Band: {band}"

            # Metacognition state
            meta_info = ""
            meta_entry = layer.registry.get("queen_metacognition", {})
            meta = meta_entry.get("instance")
            if meta and hasattr(meta, "get_state"):
                ms = meta.get_state()
                seeds = ms.get("dormant_seeds", 0)
                meta_info = f" | Seeds: {seeds}"

            # Status line
            print(f"\r[{ts}] Cycle {cycle:5d} | "
                  f"Bots: {bots:3d} | Whales: {whales:3d} | "
                  f"Signals: {validated:2d} | Events: {events:,}"
                  f"{cortex_info}{meta_info}",
                  end="", flush=True)

            # Execute validated signals every 5 cycles
            if cycle % 5 == 0 and validated > 0 and queen and labyrinth:
                validated_signals = intel_summary.get("validated_intelligence", [])
                if isinstance(validated_signals, list):
                    for sig in validated_signals[:3]:
                        symbol = sig.get("symbol", "?")
                        action = sig.get("action", "HOLD")
                        conf = sig.get("confidence", 0)
                        if conf > 0.7 and action != "HOLD":
                            print(f"\n   Signal: {symbol} {action} ({conf:.0%})")

            # Flight check every 60 cycles
            if cycle % 60 == 0:
                h = layer.get_health()
                print(f"\n   Health: {h['online']}/{h['total']} ONLINE", end="")

            # Metacognition self-backtest every 300 cycles (~5 min)
            if cycle % 300 == 0 and meta and hasattr(meta, "self_backtest"):
                try:
                    bt = meta.self_backtest()
                    score = bt.get("overall_metacognitive_score", 0)
                    print(f"\n   Metacognitive self-test: {score:.4f}", end="")
                except Exception:
                    pass

        except Exception as e:
            logging.getLogger(__name__).debug(f"Trading loop error: {e}")

        time.sleep(1)


# ============================================================================
# SIGNAL HANDLING
# ============================================================================

_SHUTDOWN = False


def _signal_handler(sig, frame):
    global _SHUTDOWN
    if _SHUTDOWN:
        print("\n\nForce quit.")
        sys.exit(1)
    _SHUTDOWN = True
    print("\n\n[IGNITION] Shutdown signal received. Stopping gracefully...")
    sys.exit(0)


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Aureon Ignition -- One switch, everything fires.",
    )
    parser.add_argument("--live", action="store_true",
                        help="Enable LIVE trading (default: dry-run)")
    parser.add_argument("--no-trade", action="store_true",
                        help="Boot all systems but skip the trading loop")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable debug logging")
    args = parser.parse_args()

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    setup_logging(verbose=args.verbose)
    print_banner()

    live = args.live or os.getenv("AUREON_LIVE_TRADING", "0") in ("1", "true", "yes")
    mode = "LIVE" if live else "DRY-RUN"
    print(f"[IGNITION] Mode: {mode}")
    print(f"[IGNITION] Working directory: {os.getcwd()}")
    print()

    # ── BOOT ──────────────────────────────────────────────────────────
    boot_start = time.time()

    layer, health = ignite_queen(live_trading=live)
    wire_execution(layer)
    checks = flight_check(layer)

    boot_elapsed = time.time() - boot_start

    print(f"\n{'=' * 80}")
    print(f"  IGNITION COMPLETE")
    print(f"  Systems: {health['online']}/{health['total']} ONLINE")
    print(f"  Flight check: {sum(1 for v in checks.values() if v)}/{len(checks)} GO")
    print(f"  Boot time: {boot_elapsed:.1f}s")
    print(f"  Mode: {mode}")
    print(f"{'=' * 80}")

    if args.no_trade:
        print("\n[IGNITION] --no-trade flag set. Systems running. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(60)
                h = layer.get_health()
                ts = datetime.now().strftime("%H:%M:%S")
                print(f"[{ts}] Health: {h['online']}/{h['total']} ONLINE")
        except KeyboardInterrupt:
            print("\n[IGNITION] Shutdown.")
        return

    # ── TRADE ─────────────────────────────────────────────────────────
    try:
        run_trading_loop(layer)
    except KeyboardInterrupt:
        print("\n\n[IGNITION] Shutdown.")
    except SystemExit:
        pass


if __name__ == "__main__":
    main()
