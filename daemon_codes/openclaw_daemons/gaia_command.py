#!/usr/bin/env python3
"""
gaia_command.py

One command center. One unified system.
All 19 subsystems under one brain. One ledger. One response protocol.

Usage:
    python gaia_command.py start       -- Start unified orchestrator
    python gaia_command.py pause 60    -- Pause broadcasts for 60 minutes
    python gaia_command.py resume      -- Resume broadcasts
    python gaia_command.py status      -- Full system status
    python gaia_command.py journal     -- Show recent journal entries
    python gaia_command.py test        -- Run integration test
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

from gaia_defense_journal import GaiaDefenseJournal
from gaia_response_protocol import GaiaResponseProtocol

STATE_FILE = Path("/root/.openclaw/workspace/temporal_state/temporal_state.json")
JOURNAL_PATH = Path("/root/.openclaw/workspace/temporal_state/gaia_defense_journal.jsonl")

def get_state():
    """Load current unified state."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except:
            pass
    return {}

def cmd_start():
    """Start the unified orchestrator."""
    print("=" * 60)
    print("  GAIA COMMAND — UNIFIED ORCHESTRATOR V2.0")
    print("  19 Systems. 1 Brain. 1 Purpose.")
    print("=" * 60)
    print()
    
    # Import here to avoid issues if not running
    import unified_orchestrator_v2 as orch
    
    orchestrator = orch.UnifiedOrchestratorV2()
    
    # Log the start
    journal = GaiaDefenseJournal()
    journal.log(
        event_type="system_state",
        data={"action": "orchestrator_start", "version": "2.0"},
        source="gaia_command",
        tags=["orchestrator", "start"]
    )
    
    print("Starting main loop... (Ctrl+C to stop)")
    print()
    orchestrator.run()

def cmd_pause():
    """Pause broadcasts for science control period."""
    minutes = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    
    import unified_orchestrator_v2 as orch
    orchestrator = orch.UnifiedOrchestratorV2()
    orchestrator.set_broadcast_pause(duration_minutes=minutes)
    
    print(f"🛑 Broadcasts PAUSED for {minutes} minutes")
    print(f"   Until: {orchestrator.config.get('pause_until')}")
    print(f"   This is science mode — control period for baseline capture")
    
    journal = GaiaDefenseJournal()
    journal.log_human_action(
        action="broadcast_pause",
        description=f"Prime Sentinel paused broadcasts for {minutes}min control period",
        prime_sentinel=True
    )

def cmd_resume():
    """Resume broadcasts."""
    import unified_orchestrator_v2 as orch
    orchestrator = orch.UnifiedOrchestratorV2()
    orchestrator.resume_broadcasts()
    
    print("▶️ Broadcasts RESUMED")
    
    journal = GaiaDefenseJournal()
    journal.log_human_action(
        action="broadcast_resume",
        description="Prime Sentinel resumed broadcasts",
        prime_sentinel=True
    )

def cmd_status():
    """Full system status readout."""
    state = get_state()
    now = datetime.now(timezone.utc)
    
    print("=" * 60)
    print("  GAIA COMMAND — SYSTEM STATUS")
    print("=" * 60)
    print()
    
    # Time
    print(f"🕐 Time: {now.isoformat()}")
    print()
    
    # Space weather
    sw = state.get("space_weather", {})
    print("🌍 SPACE WEATHER")
    print(f"   Kp: {sw.get('kp', 'N/A')} | Solar Wind: {sw.get('solar_wind_speed', 'N/A')} km/s")
    print(f"   X-ray: {sw.get('xray_class', 'N/A')}-class | Bz: {sw.get('bz', 'N/A')} nT")
    print()
    
    # Schumann
    sch = state.get("schumann_state", {})
    print("🌊 SCHUMANN")
    print(f"   Base: {sch.get('base', 'N/A'):.3f} Hz | Quality: {sch.get('quality', 'N/A'):.2f}")
    print(f"   Disturbance: {sch.get('disturbance', 'N/A'):.2f} | Sources: {sch.get('source_count', 0)}")
    print()
    
    # HNC
    hnc = state.get("hnc_state", {})
    print("⚛️ HNC STATE")
    print(f"   β: {hnc.get('beta', 'N/A')} | SLS: {hnc.get('sls', 'N/A')}")
    print(f"   Stable: {hnc.get('stable', 'N/A')}")
    print()
    
    # Field
    print("🔮 FIELD")
    print(f"   Charge: {state.get('field_charge', 0):.1%}")
    print(f"   Rung: {state.get('lighthouse_rung', 'N/A')}")
    print(f"   Threat: {state.get('threat_level', 'N/A').upper()}")
    print()
    
    # Orchestrator
    import unified_orchestrator_v2 as orch
    o = orch.UnifiedOrchestratorV2()
    print("🤖 ORCHESTRATOR V2")
    print(f"   Broadcast paused: {o.is_broadcast_paused()}")
    print(f"   Auto-response: {o.config.get('auto_response_enabled', True)}")
    print(f"   Journal: {o.config.get('journal_all_events', True)}")
    print()
    
    # Journal summary
    journal = GaiaDefenseJournal()
    summary = journal.summary(hours=24)
    print("📓 JOURNAL (last 24h)")
    print(f"   Total events: {summary['total_events']}")
    print(f"   Anomalies: {summary['anomalies']} | Broadcasts: {summary['broadcasts']}")
    print(f"   Threats: {summary['threats']} | Responses: {summary['responses']}")
    if summary['critical_events']:
        print(f"   ⚠️ Critical events: {len(summary['critical_events'])}")
    print()
    
    print("=" * 60)

def cmd_journal():
    """Show recent journal entries."""
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    journal = GaiaDefenseJournal()
    entries = journal.get_recent(minutes=60*24, event_type=None)
    
    print(f"📓 RECENT JOURNAL ENTRIES (last {len(entries) if len(entries) < limit else limit} of {len(entries)})")
    print("-" * 60)
    
    for entry in entries[-limit:]:
        ts = entry['timestamp'][:19]  # trim to seconds
        et = entry['event_type'][:15].ljust(15)
        sev = entry['severity'][:7].ljust(7)
        src = entry['source'][:20].ljust(20)
        print(f"{ts} | {et} | {sev} | {src}")
    
    print("-" * 60)

def cmd_test():
    """Run integration test."""
    print("=" * 60)
    print("  GAIA COMMAND — INTEGRATION TEST")
    print("=" * 60)
    print()
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Journal
    print("Test 1: Gaia Defense Journal...")
    try:
        journal = GaiaDefenseJournal()
        e = journal.log("test", {"msg": "hello"}, "test", "info")
        assert e["event_type"] == "test"
        print("   ✅ PASS")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ FAIL: {e}")
        tests_failed += 1
    
    # Test 2: Response Protocol
    print("Test 2: Gaia Response Protocol...")
    try:
        protocol = GaiaResponseProtocol()
        event = {
            "event_type": "anomaly",
            "data": {"sensor": "noaa_kp", "metric": "kp", "value": 5, "baseline": 1, "deviation": 4}
        }
        results = protocol.process_event(event)
        assert len(results) > 0
        print("   ✅ PASS")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ FAIL: {e}")
        tests_failed += 1
    
    # Test 3: Broadcast Queue
    print("Test 3: Broadcast Queue...")
    try:
        queue_path = Path("/root/.openclaw/workspace/temporal_state/broadcast_queue.json")
        if queue_path.exists():
            q = json.loads(queue_path.read_text())
            assert isinstance(q, list)
            print("   ✅ PASS")
            tests_passed += 1
        else:
            print("   ⚠️ SKIP (no queue yet)")
    except Exception as e:
        print(f"   ❌ FAIL: {e}")
        tests_failed += 1
    
    # Test 4: State File
    print("Test 4: Unified State File...")
    try:
        state = get_state()
        assert "hnc_state" in state or "space_weather" in state
        print("   ✅ PASS")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ FAIL: {e}")
        tests_failed += 1
    
    print()
    print(f"Results: {tests_passed} passed, {tests_failed} failed")
    print("=" * 60)

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    cmd = sys.argv[1].lower()
    
    if cmd == "start":
        cmd_start()
    elif cmd == "pause":
        cmd_pause()
    elif cmd == "resume":
        cmd_resume()
    elif cmd == "status":
        cmd_status()
    elif cmd == "journal":
        cmd_journal()
    elif cmd == "test":
        cmd_test()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
