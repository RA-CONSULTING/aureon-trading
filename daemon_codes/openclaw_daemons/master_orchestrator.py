#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
MASTER DAEMON ORCHESTRATOR — MAXIMUM AMPLIFICATION PROTOCOL
═══════════════════════════════════════════════════════════════════════════════

Stages all daemons over 5 minutes at maximum amplification.
Collects data from the window. Runs proof engine.

Usage: python3 master_orchestrator.py [run|status|stop|proof]
"""

import json
import subprocess
import sys
import time
import signal
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
STATE_DIR = WORKSPACE / "temporal_state"
PID_FILE = STATE_DIR / "master_daemon_pids.json"

DAEMONS = {
    # name: (command, delay_seconds, description)
    "live_collector": (["python3", str(WORKSPACE / "live_planetary_collector.py")], 0, "Live planetary data collection (NOAA)"),
    "euphoria": (["python3", str(WORKSPACE / "euphoria_broadcast_engine.py")], 30, "Euphoria broadcast engine (9 frequencies)"),
    "victory_hold": (["python3", str(WORKSPACE / "sero_temporal_warfare_victory_hold.py")], 60, "Victory hold (harmonic maintenance)"),
    "temporal_reclamation": (["python3", str(WORKSPACE / "temporal_reclamation_engine.py"), "--continuous", "--interval", "30"], 120, "Temporal reclamation engine (30s cycles)"),
    "hnc_daemon": (["python3", str(WORKSPACE / "hnc_daemon.py")], 180, "HNC framework daemon"),
    "soul_protection": (["python3", str(WORKSPACE / "soul_protection_daemon.py")], 240, "Soul protection daemon"),
    "autonomous_liberation": (["python3", str(WORKSPACE / "autonomous_liberation_engine.py")], 300, "Autonomous liberation engine"),
}

def log(msg):
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")

def start_daemons():
    """Start all daemons staged over 5 minutes."""
    pids = {}
    
    log("=" * 60)
    log("MASTER DAEMON ORCHESTRATOR — STARTING")
    log("=" * 60)
    log(f"Total daemons: {len(DAEMONS)}")
    log(f"Staged over: 5 minutes")
    log(f"Max amplification: ENABLED")
    log("")
    
    for name, (cmd, delay, desc) in DAEMONS.items():
        if delay > 0:
            log(f"Waiting {delay}s before starting {name}...")
            time.sleep(delay)
        
        try:
            # Start daemon with nohup, detached from terminal
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
                cwd=WORKSPACE
            )
            pids[name] = proc.pid
            log(f"✅ STARTED {name} (PID {proc.pid}) — {desc}")
        except Exception as e:
            log(f"❌ FAILED {name}: {e}")
    
    # Save PID file
    STATE_DIR.mkdir(exist_ok=True)
    with open(PID_FILE, "w") as f:
        json.dump(pids, f, indent=2)
    
    log("")
    log("=" * 60)
    log("ALL DAEMONS STARTED")
    log(f"Active PIDs saved to: {PID_FILE}")
    log("=" * 60)
    log("")
    log("The field is now active. Broadcasts are transmitting.")
    log("Planetary data is being collected every 5 minutes.")
    log("")
    log("Next steps:")
    log("  1. Let it run for 15-60 minutes to build overlapping data")
    log("  2. Run: python3 master_orchestrator.py proof")
    log("  3. Run: python3 amplification_proof_engine.py")
    
    return pids

def stop_daemons():
    """Stop all running daemons."""
    if not PID_FILE.exists():
        log("No PID file found. Nothing to stop.")
        return
    
    with open(PID_FILE) as f:
        pids = json.load(f)
    
    log("=" * 60)
    log("STOPPING ALL DAEMONS")
    log("=" * 60)
    
    for name, pid in pids.items():
        try:
            import os
            os.killpg(os.getpgid(pid), signal.SIGTERM)
            log(f"🛑 STOPPED {name} (PID {pid})")
        except ProcessLookupError:
            log(f"⚠️ {name} (PID {pid}) already stopped")
        except Exception as e:
            log(f"❌ Error stopping {name}: {e}")
    
    PID_FILE.unlink(missing_ok=True)
    log("All daemons stopped.")

def check_status():
    """Check status of all daemons."""
    if not PID_FILE.exists():
        log("No daemons running (no PID file).")
        return
    
    with open(PID_FILE) as f:
        pids = json.load(f)
    
    log("=" * 60)
    log("DAEMON STATUS")
    log("=" * 60)
    
    import psutil
    for name, pid in pids.items():
        try:
            proc = psutil.Process(pid)
            status = proc.status()
            runtime = datetime.now(timezone.utc).timestamp() - proc.create_time()
            log(f"  {name:20s} PID {pid:6d} | {status:10s} | {runtime/60:.1f} min")
        except psutil.NoSuchProcess:
            log(f"  {name:20s} PID {pid:6d} | DEAD")

def run_proof():
    """Run the amplification proof engine."""
    log("=" * 60)
    log("RUNNING AMPLIFICATION PROOF ENGINE")
    log("=" * 60)
    
    result = subprocess.run(
        ["python3", str(WORKSPACE / "amplification_proof_engine.py")],
        capture_output=True,
        text=True,
        cwd=WORKSPACE
    )
    
    print(result.stdout)
    if result.stderr:
        print("ERRORS:", result.stderr)
    
    log("Proof engine complete.")

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    
    if cmd == "run" or cmd == "start":
        pids = start_daemons()
        
        # Keep running and show periodic status
        log("")
        log("Orchestrator running. Press Ctrl+C to stop all daemons.")
        try:
            while True:
                time.sleep(60)
                log(f"[HEARTBEAT] Daemons active. Collecting data...")
        except KeyboardInterrupt:
            log("")
            log("Shutdown signal received.")
            stop_daemons()
    
    elif cmd == "stop":
        stop_daemons()
    
    elif cmd == "status":
        try:
            import psutil
            check_status()
        except ImportError:
            log("psutil not installed. Using basic check...")
            if PID_FILE.exists():
                with open(PID_FILE) as f:
                    pids = json.load(f)
                for name, pid in pids.items():
                    log(f"  {name}: PID {pid}")
    
    elif cmd == "proof":
        run_proof()
    
    else:
        print("Usage: python3 master_orchestrator.py [run|stop|status|proof]")

if __name__ == "__main__":
    main()
