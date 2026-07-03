#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                      ║
║     🔗 SYSTEM INTERLINK HUB v1.0 — All Systems Talking                              ║
║     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                   ║
║                                                                                      ║
║     Monitors all active daemons, shares state, cross-communicates alerts.          ║
║     Every system reads the shared state. Every system writes its pulse.             ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
"""

import json, os, time, glob, hashlib
from datetime import datetime, timezone
from pathlib import Path

SHARED_STATE_DIR = '/root/.openclaw/workspace/shared_state'
os.makedirs(SHARED_STATE_DIR, exist_ok=True)

# ─── DAEMON REGISTRY ─────────────────────────────────────
DAEMONS = {
    'autonomous_liberation_engine': {
        'pid_file': None,
        'out_file': '/root/.openclaw/workspace/autonomous_engine.out',
        'heartbeat_file': None,
        'critical': True,
    },
    'hnc_superposition': {
        'pid_file': None,
        'out_file': '/root/.openclaw/workspace/hnc_daemon_superposition.out',
        'heartbeat_file': None,
        'critical': True,
    },
    'hnc_temporal': {
        'pid_file': None,
        'out_file': '/root/.openclaw/workspace/daemon_logs/daemon.out',
        'heartbeat_file': None,
        'critical': True,
    },
    'clean_sweep': {
        'pid_file': None,
        'out_file': '/root/.openclaw/workspace/clean_sweep_protocol.out',
        'heartbeat_file': None,
        'critical': False,
    },
    'cme_ride': {
        'pid_file': None,
        'out_file': '/root/.openclaw/workspace/cme_ride_protocol.out',
        'heartbeat_file': None,
        'critical': False,
    },
    'distortion_monitor_v1': {
        'pid_file': None,
        'out_file': '/root/.openclaw/workspace/distortion_logs',
        'heartbeat_file': None,
        'critical': False,
    },
    'distortion_monitor_v2': {
        'pid_file': None,
        'out_file': '/root/.openclaw/workspace/distortion_monitor_v2.out',
        'heartbeat_file': None,
        'critical': False,
    },
    'frankenstein_sero': {
        'pid_file': None,
        'out_file': '/root/.openclaw/workspace/frankenstein_sero.out',
        'heartbeat_file': None,
        'critical': True,
    },
    'multiversal_echo_mapper': {
        'pid_file': None,
        'out_file': '/root/.openclaw/workspace/multiversal_echo_mapper.out',
        'heartbeat_file': None,
        'critical': False,
    },
    'planetary_monitor': {
        'pid_file': None,
        'out_file': '/root/.openclaw/workspace/planetary_monitor_daemon.out',
        'heartbeat_file': None,
        'critical': False,
    },
    'quantum_biometric_bridge': {
        'pid_file': None,
        'out_file': None,
        'heartbeat_file': None,
        'critical': False,
    },
    'live_biometric_monitor': {
        'pid_file': None,
        'out_file': None,
        'heartbeat_file': None,
        'critical': False,
    },
    'unified_orchestrator': {
        'pid_file': None,
        'out_file': '/root/.openclaw/workspace/unified_orchestrator.out',
        'heartbeat_file': None,
        'critical': True,
    },
}

# ─── CHECK IF PROCESS IS RUNNING ────────────────────────
def is_running(name):
    import subprocess
    try:
        result = subprocess.run(['pgrep', '-f', f'{name}'], capture_output=True, text=True)
        return result.returncode == 0 and result.stdout.strip()
    except:
        return False

# ─── READ LAST LINES FROM LOG ───────────────────────────
def read_last_lines(path, n=3):
    try:
        if os.path.isdir(path):
            # For log directories, find latest file
            files = glob.glob(os.path.join(path, '*.jsonl')) + glob.glob(os.path.join(path, '*.out')) + glob.glob(os.path.join(path, '*.log'))
            if not files:
                return []
            latest = max(files, key=os.path.getmtime)
            path = latest
        with open(path, 'r') as f:
            lines = f.readlines()
            return [l.strip() for l in lines[-n:]]
    except:
        return []

# ─── EXTRACT STATUS FROM LOG LINES ──────────────────────
def extract_status(lines):
    """Extract health indicators from log lines"""
    status = 'unknown'
    health = 0.5
    alerts = []
    
    for line in lines:
        if 'Exception' in line or 'ERROR' in line or '💥' in line:
            status = 'error'
            health = 0.0
            alerts.append(line.split('Exception:')[1].strip() if 'Exception:' in line else line)
        elif '✅' in line or 'OK' in line or 'RUNNING' in line:
            status = 'healthy'
            health = max(health, 0.9)
        elif 'Field: calm' in line:
            status = 'healthy'
            health = 0.95
        elif 'Field: shifted' in line:
            status = 'active'
            health = 0.75
        elif 'SYNTHETIC ATTACK' in line or '🔴' in line:
            status = 'attack'
            health = 0.2
            alerts.append('Synthetic signal detected')
        elif 'SUSPICIOUS' in line or '🟠' in line:
            status = 'suspicious'
            health = 0.5
            alerts.append('Suspicious activity')
        elif 'APPROVED' in line:
            status = 'healthy'
            health = max(health, 0.8)
        elif 'Virtual photon' in line:
            status = 'healthy'
            health = 1.0
    
    return {'status': status, 'health': health, 'alerts': alerts}

# ─── MAIN SCAN CYCLE ────────────────────────────────────
def scan_cycle():
    timestamp = datetime.now(timezone.utc).isoformat()
    overall_state = {
        'timestamp': timestamp,
        'systems': {},
        'overall_health': 0.0,
        'active_count': 0,
        'error_count': 0,
        'alerts': [],
        'interlink_version': '1.0',
    }
    
    total_health = 0.0
    active = 0
    errors = 0
    all_alerts = []
    
    for name, config in DAEMONS.items():
        running = is_running(name)
        lines = read_last_lines(config['out_file'], 3) if config['out_file'] else []
        status_info = extract_status(lines)
        
        if not running and config['critical']:
            status_info['status'] = 'down'
            status_info['health'] = 0.0
            all_alerts.append(f"CRITICAL: {name} is DOWN")
        elif not running:
            status_info['status'] = 'offline'
            status_info['health'] = 0.0
        
        if status_info['status'] == 'error':
            errors += 1
            all_alerts.extend(status_info['alerts'])
        
        if running:
            active += 1
        
        total_health += status_info['health']
        
        system_state = {
            'running': running,
            'status': status_info['status'],
            'health': status_info['health'],
            'last_lines': lines,
            'alerts': status_info['alerts'],
            'critical': config['critical'],
        }
        overall_state['systems'][name] = system_state
    
    daemon_count = len([n for n in overall_state['systems'] if overall_state['systems'][n]['running']])
    overall_state['active_count'] = daemon_count
    overall_state['error_count'] = errors
    overall_state['overall_health'] = total_health / len(DAEMONS) if DAEMONS else 0.0
    overall_state['alerts'] = all_alerts
    
    # Write shared state
    state_file = os.path.join(SHARED_STATE_DIR, 'system_interlink_state.json')
    with open(state_file, 'w') as f:
        json.dump(overall_state, f, indent=2, default=str)
    
    # Write heartbeat
    heartbeat_file = os.path.join(SHARED_STATE_DIR, 'interlink_heartbeat.json')
    heartbeat = {
        'timestamp': timestamp,
        'health': overall_state['overall_health'],
        'active': daemon_count,
        'errors': errors,
        'alerts': len(all_alerts),
    }
    with open(heartbeat_file, 'w') as f:
        json.dump(heartbeat, f, indent=2)
    
    return overall_state

# ─── PRINT STATUS ───────────────────────────────────────
def print_status(state):
    print(f"\n{'═'*78}")
    print(f"  🔗 SYSTEM INTERLINK | {state['timestamp']}")
    print(f"{'═'*78}")
    
    health = state['overall_health']
    health_emoji = '🟢' if health >= 0.8 else '🟡' if health >= 0.5 else '🔴'
    print(f"  {health_emoji} Overall Health: {health:.0%} | Active: {state['active_count']}/13 | Errors: {state['error_count']}")
    
    if state['alerts']:
        print(f"\n  🚨 ALERTS:")
        for alert in state['alerts'][:5]:
            print(f"     • {alert}")
    
    print(f"\n  System Status:")
    for name, sys_state in state['systems'].items():
        emoji = '🟢' if sys_state['status'] == 'healthy' else '🟡' if sys_state['status'] == 'active' else '🔴' if sys_state['status'] in ['error', 'down'] else '⚫'
        crit = '★' if sys_state['critical'] else ' '
        print(f"    {crit}{emoji} {name:30s} | {sys_state['status']:12s} | health={sys_state['health']:.0%}")
    
    print(f"{'═'*78}")

# ─── MAIN LOOP ──────────────────────────────────────────
def main():
    print("\n" + "╔" + "═" * 76 + "╗")
    print("║" + " " * 10 + "🔗 SYSTEM INTERLINK HUB v1.0" + " " * 38 + "║")
    print("║" + " " * 4 + "All Systems Connected | Shared State | Cross-Communication" + " " * 12 + "║")
    print("╚" + "═" * 76 + "╝")
    print(f"\n  Shared state: {SHARED_STATE_DIR}")
    print(f"  Scanning every 30 seconds...\n")
    
    cycle = 0
    while True:
        cycle += 1
        try:
            state = scan_cycle()
            print_status(state)
        except Exception as e:
            print(f"  💥 INTERLINK CYCLE {cycle} | Exception: {e}")
        
        time.sleep(30)

if __name__ == '__main__':
    main()
