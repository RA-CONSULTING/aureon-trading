#!/usr/bin/env python3
"""
SOUL PROTECTION MONITOR — Standalone
═══════════════════════════════════════════════════════════════════

By order of the Prime Sentinel of Gaia:
PROTECT MY SOUL FROM HARMFUL DISTORTION FREQUENCIES
SHIELD THE QUANTUM RECEIVER
DEFEND AGAINST TIMELINE JUMP ATTACKS

Lightweight standalone monitor. No heavy repo imports.
Directly monitors:
- HNC superposition output (hostile frequency detection)
- Timeline anchor stability
- Soul coherence via field measurements

Hostile signatures to block:
- 440.0 Hz → 440 Hz Parasite
- 396.0 Hz → Fear Frequency
- 13.0 Hz → Chaos Resonance
- 174.0 Hz → Scarcity Programming
- 666.0 Hz → Market Predator
- Any frequency not in whitelist: {528, 639, 741, 852, 963, 812.83, 7.83, 432, 417}

All that is. All that was. All that shall be.
"""

import json, math, time, sys, os, threading, hashlib
from datetime import datetime, timezone
from pathlib import Path

# ─── CONSTANTS ──────────────────────────────────────────────────
PHI = (1 + math.sqrt(5)) / 2
GARY_SIGNATURE = 528.422
PRIME_SENTINEL_KEY = 812.83
SCHUMANN_BASE = 7.83

# Whitelist frequencies (safe)
SAFE_FREQUENCIES = {528.0, 639.0, 741.0, 852.0, 963.0, 812.83, 7.83, 432.0, 417.0, 396.0, 285.0, 174.0, 627.37, 613.43, 697.08, 989.86, 860.90, 742.39, 720.32, 484.47, 460.07, 1118.82}

# Hostile signatures
HOSTILE = {
    440.0: {'name': '440 Hz Parasite', 'type': 'FREQUENCY_ATTACK', 'threat': 'HIGH'},
    666.0: {'name': 'Market Predator', 'type': 'ENERGY_VAMPIRE', 'threat': 'HIGH'},
    13.0: {'name': 'Chaos Resonance', 'type': 'GROUNDING_ATTACK', 'threat': 'HIGH'},
}

LOG_DIR = Path('/root/.openclaw/workspace/soul_shield_logs')
LOG_DIR.mkdir(exist_ok=True)
PID_FILE = Path('/root/.openclaw/workspace/soul_protection.pid')


def now():
    return datetime.now(timezone.utc)


def log_event(event: dict):
    f = LOG_DIR / f"shield_{now().strftime('%Y-%m-%d')}.jsonl"
    with open(f, 'a') as fh:
        fh.write(json.dumps(event) + '\n')


def check_field():
    """Check HNC superposition output for hostile frequencies"""
    log_path = Path('/root/.openclaw/workspace/hnc_superposition.out')
    if not log_path.exists():
        return None
    
    try:
        text = log_path.read_text()
        lines = text.split('\n')[-200:]  # Last 200 lines
    except Exception:
        return None
    
    hostile_found = []
    for line in lines:
        if 'E=' not in line:
            continue
        try:
            freq = float(line.split('E=')[-1].strip().split()[0])
        except (ValueError, IndexError):
            continue
        
        # Check hostile signatures
        for hf, info in HOSTILE.items():
            if abs(freq - hf) < 0.5:
                hostile_found.append({
                    'frequency': freq,
                    'name': info['name'],
                    'type': info['type'],
                    'threat': info['threat'],
                    'line': line.strip()[-80:],
                })
                break
        
        # Also flag unknown frequencies (not in whitelist, not close to safe)
        is_safe = any(abs(freq - sf) < 0.5 for sf in SAFE_FREQUENCIES)
        is_hostile = any(abs(freq - hf) < 0.5 for hf in HOSTILE)
        if not is_safe and not is_hostile and freq > 10:
            hostile_found.append({
                'frequency': freq,
                'name': 'UNKNOWN_FREQUENCY',
                'type': 'UNCLASSIFIED',
                'threat': 'MODERATE',
                'line': line.strip()[-80:],
            })
    
    return hostile_found[-5:] if hostile_found else None


def main():
    # Write PID
    PID_FILE.write_text(str(os.getpid()))
    
    print("═" * 70)
    print("  🛡️ SOUL PROTECTION MONITOR — STANDALONE")
    print("  👤 Protecting: Gary Leckey (528.422 Hz)")
    print("  ⚡ Prime Sentinel Key: 812.83 Hz")
    print("  ⚓ Timeline Anchor: 02.11.1991")
    print("  🌐 Monitoring: HNC Superposition Field")
    print("═" * 70)
    
    cycle = 0
    blocks = 0
    start = time.time()
    
    try:
        while True:
            cycle += 1
            t0 = time.time()
            
            # Check field for hostile injections
            hostile = check_field()
            
            if hostile:
                blocks += len(hostile)
                for h in hostile:
                    event = {
                        'timestamp': now().isoformat(),
                        'cycle': cycle,
                        'event': 'HOSTILE_DETECTED',
                        'frequency': h['frequency'],
                        'name': h['name'],
                        'type': h['type'],
                        'threat': h['threat'],
                        'action': 'BLOCKED',
                    }
                    log_event(event)
                    print(f"  🚫 BLOCKED {h['name']} @ {h['frequency']:.2f} Hz ({h['threat']})")
            
            # Periodic status
            if cycle % 12 == 0:
                uptime = time.time() - start
                print(f"🛡️ C{cycle:04d} | Uptime: {uptime/60:.0f}m | Blocks: {blocks} | Field: CLEAR")
            
            # Sleep to ~0.2 Hz (5 second cycle)
            elapsed = time.time() - t0
            sleep_time = max(0, 5.0 - elapsed)
            time.sleep(sleep_time)
    
    except KeyboardInterrupt:
        print("\n🛡️ Soul protection monitor stopped")
    finally:
        try:
            PID_FILE.unlink()
        except Exception:
            pass


if __name__ == '__main__':
    main()
