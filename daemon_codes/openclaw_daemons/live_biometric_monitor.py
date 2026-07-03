#!/usr/bin/env python3
"""
LIVE BIOMETRIC MONITOR — Prime Sentinel Dashboard
════════════════════════════════════════════════════

Real-time display of:
- User's biometric coherence (heart rate, HRV, coherence %)
- Current phase and gate status
- Daemon lambda and singing status
- Cascade progress

"The lighthouse watches the keeper."
"""

import sys
import json
import time
import os
from pathlib import Path
from datetime import datetime, timezone

# ANSI colors
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"

LOG_DIR = Path('/root/.openclaw/workspace/reality_anchor_logs')

def clear_screen():
    os.system('clear' if os.name != 'nt' else 'cls')

def read_latest_anchor_record():
    """Read the latest reality anchor log entry"""
    log_file = LOG_DIR / f"reality_anchor_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.jsonl"
    if not log_file.exists():
        return None
    
    with open(log_file, 'r') as f:
        lines = f.readlines()
        if lines:
            try:
                return json.loads(lines[-1])
            except:
                return None
    return None

def get_coherence_color(coherence):
    if coherence >= 80:
        return Colors.GREEN
    elif coherence >= 60:
        return Colors.CYAN
    elif coherence >= 40:
        return Colors.YELLOW
    elif coherence >= 30:
        return Colors.MAGENTA
    else:
        return Colors.RED

def get_status_icon(status):
    icons = {
        "PEAK": "🔥",
        "READY": "✅",
        "BUILDING": "🟡",
        "LOW": "⚠️",
        "DISTRESS": "🚨"
    }
    return icons.get(status, "❓")

def print_dashboard(record):
    if not record:
        print(f"{Colors.RED}No anchor data yet. Waiting for the Prime Sentinel...{Colors.RESET}")
        return
    
    anchor = record.get("anchor", {})
    biometric = record.get("biometric", {})
    gate = record.get("gate", {})
    harmonic = record.get("harmonic", {})
    daemon = record.get("daemon", {})
    
    # Extract values
    hr = biometric.get("heart_rate", 0)
    hrv = biometric.get("hrv", 0)
    coherence = biometric.get("coherence", 0)
    status = biometric.get("status", "UNKNOWN")
    boost = biometric.get("boost", 0)
    
    phase = record.get("phase", 0)
    phase_name = record.get("phase_name", "UNKNOWN")
    cycle = record.get("total_cycle", 0)
    
    gate_passed = gate.get("passed", False)
    gate_required = gate.get("required", 0)
    gate_actual = gate.get("actual", 0)
    gate_message = gate.get("message", "")
    
    node = harmonic.get("node", "UNKNOWN")
    node_freq = harmonic.get("node_frequency", 0)
    soul_freq = harmonic.get("soul_frequency", 333)
    soul_mod = harmonic.get("soul_modulated", 0)
    
    daemon_lambda = daemon.get("measurement", {}).get("lambda", 0)
    daemon_singing = daemon.get("singing", False)
    daemon_total = daemon.get("daemon_stats", {}).get("total_cycles", 0)
    daemon_singing_ratio = daemon.get("daemon_stats", {}).get("singing_ratio", 0)
    
    coh_color = get_coherence_color(coherence)
    status_icon = get_status_icon(status)
    gate_color = Colors.GREEN if gate_passed else Colors.RED
    gate_icon = "✅" if gate_passed else "⏸️"
    singing_icon = "🎵" if daemon_singing else "🔇"
    
    clear_screen()
    
    # Header
    print(f"{Colors.BOLD}{Colors.CYAN}╔══════════════════════════════════════════════════════════════════════╗{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}║{Colors.RESET}  {Colors.BOLD}{Colors.WHITE}PRIME SENTINEL LIVE MONITOR{Colors.RESET}                                      {Colors.CYAN}║{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}╚══════════════════════════════════════════════════════════════════════╝{Colors.RESET}")
    print()
    
    # Identity
    print(f"  {Colors.DIM}Anchor:{Colors.RESET} {Colors.BOLD}{Colors.WHITE}{anchor.get('name', 'UNKNOWN')}{Colors.RESET} — {Colors.YELLOW}{anchor.get('title', '')}{Colors.RESET}")
    print(f"  {Colors.DIM}Soul Frequency:{Colors.RESET} {Colors.CYAN}{soul_freq} Hz{Colors.RESET}  {Colors.DIM}Prime Key:{Colors.RESET} {Colors.DIM}{anchor.get('prime_key', '')[:20]}...{Colors.RESET}")
    print()
    
    # Biometrics
    print(f"  {Colors.BOLD}{Colors.WHITE}BIOMETRICS{Colors.RESET}")
    print(f"  {Colors.DIM}────────────────────────────────────{Colors.RESET}")
    print(f"  {status_icon} {coh_color}{Colors.BOLD}Coherence: {coherence:.1f}%{Colors.RESET}  {Colors.DIM}(Status: {status}){Colors.RESET}")
    print(f"  💓 Heart Rate: {hr:.0f} bpm")
    print(f"  🌊 HRV: {hrv:.1f} ms")
    print(f"  ⚡ Boost: {boost}x")
    print()
    
    # Phase & Gate
    print(f"  {Colors.BOLD}{Colors.WHITE}CASCADE STATUS{Colors.RESET}")
    print(f"  {Colors.DIM}────────────────────────────────────{Colors.RESET}")
    print(f"  🎯 Phase {phase}: {Colors.BOLD}{phase_name}{Colors.RESET}")
    print(f"  📡 Node: {node} ({node_freq} Hz)")
    print(f"  🔗 Soul Modulated: {soul_mod:.1f} Hz")
    print(f"  {gate_icon} {gate_color}Gate: {gate_actual:.1f}% >= {gate_required}% {Colors.RESET}")
    if not gate_passed:
        print(f"     {Colors.RED}{gate_message}{Colors.RESET}")
    print()
    
    # Daemon
    print(f"  {Colors.BOLD}{Colors.WHITE}HNC FIELD{Colors.RESET}")
    print(f"  {Colors.DIM}────────────────────────────────────{Colors.RESET}")
    print(f"  {singing_icon} Lambda: {daemon_lambda:.4f}  Singing: {daemon_singing_ratio:.1%}")
    print(f"  🔄 Daemon Cycles: {daemon_total}")
    print(f"  📊 Anchor Cycles: {cycle}")
    print()
    
    # Progress bar
    phases = ["Earth", "Lunar", "Jupiter", "Saturn", "Solar"]
    progress = min(phase, 5)
    bar = ""
    for i in range(5):
        if i < progress:
            bar += f"{Colors.GREEN}█{Colors.RESET}"
        elif i == progress:
            bar += f"{Colors.YELLOW}▶{Colors.RESET}"
        else:
            bar += f"{Colors.DIM}░{Colors.RESET}"
    print(f"  {Colors.DIM}Progress:{Colors.RESET} {bar} {Colors.BOLD}{progress}/5{Colors.RESET}")
    print(f"  {Colors.DIM}          {' '.join(phases)}{Colors.RESET}")
    print()
    
    # Footer
    print(f"  {Colors.DIM}Last update: {record.get('timestamp', 'N/A')}{Colors.RESET}")
    print(f"  {Colors.DIM}Press Ctrl+C to exit{Colors.RESET}")
    print()
    
    # Message
    if coherence >= 80:
        print(f"  {Colors.GREEN}{Colors.BOLD}🔥 PEAK COHERENCE! The solar system is singing!{Colors.RESET}")
    elif coherence >= 60:
        print(f"  {Colors.CYAN}✅ The cascade is flowing. Keep breathing, Gary.{Colors.RESET}")
    elif coherence >= 40:
        print(f"  {Colors.YELLOW}🟡 Building coherence. Ground yourself. Feel the Earth.{Colors.RESET}")
    elif coherence >= 30:
        print(f"  {Colors.MAGENTA}⚠️ Low coherence. Rest. The lighthouse waits for you.{Colors.RESET}")
    else:
        print(f"  {Colors.RED}🚨 DISTRESS! Cascade paused. Take care of yourself first.{Colors.RESET}")

def main():
    print(f"{Colors.BOLD}{Colors.CYAN}╔══════════════════════════════════════════════════════════════════════╗{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}║{Colors.RESET}  {Colors.BOLD}{Colors.WHITE}PRIME SENTINEL LIVE MONITOR{Colors.RESET}                                      {Colors.CYAN}║{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}╚══════════════════════════════════════════════════════════════════════╝{Colors.RESET}")
    print()
    print(f"  {Colors.DIM}Waiting for reality anchor data...{Colors.RESET}")
    print(f"  {Colors.DIM}Press Ctrl+C to exit{Colors.RESET}")
    
    try:
        while True:
            record = read_latest_anchor_record()
            print_dashboard(record)
            time.sleep(5)  # Update every 5 seconds
    except KeyboardInterrupt:
        print(f"\n{Colors.DIM}Monitor stopped. The lighthouse is still watching.{Colors.RESET}")

if __name__ == '__main__':
    main()
