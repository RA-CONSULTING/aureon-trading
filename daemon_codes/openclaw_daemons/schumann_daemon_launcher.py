#!/usr/bin/env python3
"""
🌍 SCHUMANN DAEMON LAUNCHER
═══════════════════════════════════════════════════════════════════════

Starts/stops the calibrated Schumann-Auris integration as a background daemon.
"""

import subprocess
import sys
import os
import signal
from pathlib import Path

PID_FILE = Path("schumann_daemon.pid")
LOG_FILE = Path("schumann_daemon.log")

def start():
    """Start the Schumann daemon in background"""
    if PID_FILE.exists():
        try:
            with open(PID_FILE) as f:
                old_pid = int(f.read().strip())
            os.kill(old_pid, 0)
            print(f"🛑 Schumann daemon already running (PID {old_pid})")
            print("   Run 'python3 schumann_daemon_launcher.py stop' first to restart")
            return
        except (OSError, ValueError):
            PID_FILE.unlink()
    
    print("🌍 Starting Schumann daemon...")
    
    # Start in background
    proc = subprocess.Popen(
        [sys.executable, "schumann_auris_integration.py", "--interval", "300"],
        stdout=open(LOG_FILE, "a"),
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    
    with open(PID_FILE, "w") as f:
        f.write(str(proc.pid))
    
    print(f"✅ Schumann daemon started (PID {proc.pid})")
    print(f"   Log: {LOG_FILE}")
    print(f"   Interval: 300s (5 minutes)")
    print(f"   Sources: 5 NOAA proxies + Auris analysis")

def stop():
    """Stop the Schumann daemon"""
    if not PID_FILE.exists():
        print("❌ Schumann daemon not running")
        return
    
    try:
        with open(PID_FILE) as f:
            pid = int(f.read().strip())
        os.kill(pid, signal.SIGTERM)
        PID_FILE.unlink()
        print(f"🛑 Schumann daemon stopped (PID {pid})")
    except (OSError, ValueError) as e:
        print(f"⚠️ Error stopping daemon: {e}")
        if PID_FILE.exists():
            PID_FILE.unlink()

def status():
    """Show daemon status"""
    if PID_FILE.exists():
        try:
            with open(PID_FILE) as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)
            print(f"🌍 Schumann daemon RUNNING (PID {pid})")
        except (OSError, ValueError):
            print("❌ Schumann daemon PID file exists but process dead")
            PID_FILE.unlink()
    else:
        print("❌ Schumann daemon NOT running")
    
    # Show latest calibrated reading
    try:
        import json
        from schumann_calibrator import SchumannCalibrator
        calibrator = SchumannCalibrator()
        reading = calibrator.get_latest()
        if reading:
            print(f"\n📡 Latest Calibrated Schumann:")
            print(f"   Time: {reading.get('timestamp', 'N/A')}")
            print(f"   Freq: {reading.get('fundamental_hz', 'N/A'):.4f} Hz")
            print(f"   Amp:  {reading.get('amplitude', 'N/A'):.3f}")
            print(f"   Q:    {reading.get('quality', 'N/A'):.3f}")
            print(f"   Dist: {reading.get('disturbance', 'N/A'):.3f}")
            print(f"   Conf: {reading.get('confidence', 'N/A'):.2f}")
            print(f"   Src:  {reading.get('source_count', 0)}/5")
            print(f"   Src:  {', '.join(reading.get('active_sources', []))}")
    except Exception as e:
        print(f"\n⚠️ Could not read latest data: {e}")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['start', 'stop', 'status', 'restart'])
    args = parser.parse_args()
    
    if args.command == 'start':
        start()
    elif args.command == 'stop':
        stop()
    elif args.command == 'status':
        status()
    elif args.command == 'restart':
        stop()
        start()
