#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║     📡 LIVE FEED MONITOR — Measurable Difference Detector                       ║
║                                                                               ║
║     Monitors NOAA data BEFORE, DURING, and AFTER mycelial transmission        ║
║     to detect any measurable changes in planetary readings.                   ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

import sys, json, time, os, requests, threading
from datetime import datetime, timezone

# Configuration
DATA_DIR = "/root/.openclaw/workspace/planetary_monitor"
RESULTS_FILE = f"{DATA_DIR}/transmission_monitor_results.json"

def fetch_kp():
    try:
        url = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index-forecast.json"
        resp = requests.get(url, timeout=15)
        data = resp.json()
        observed = [d for d in data if d.get('observed') == 'observed']
        latest = observed[-1] if observed else data[-1]
        return {
            "time_tag": latest['time_tag'],
            "kp": latest['kp'],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "timestamp": datetime.now(timezone.utc).isoformat()}

def fetch_plasma():
    try:
        url = "https://services.swpc.noaa.gov/products/solar-wind/plasma-6-hour.json"
        resp = requests.get(url, timeout=15)
        data = resp.json()
        if len(data) > 1:
            latest = data[-1]
            return {
                "time": latest[0],
                "density": float(latest[1]) if len(latest) > 1 else None,
                "speed": float(latest[2]) if len(latest) > 2 else None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        return {"error": "No data"}
    except Exception as e:
        return {"error": str(e), "timestamp": datetime.now(timezone.utc).isoformat()}

def monitor_cycle(label, results):
    """Run one monitoring cycle and record results"""
    print(f"\n📡 [{label}] Monitoring cycle at {datetime.now(timezone.utc).isoformat()}")
    
    kp = fetch_kp()
    plasma = fetch_plasma()
    
    reading = {
        "label": label,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "kp": kp,
        "plasma": plasma,
    }
    
    results.append(reading)
    
    if 'error' not in kp:
        print(f"   Kp: {kp['kp']:.2f} at {kp['time_tag']}")
    if 'error' not in plasma:
        print(f"   Solar wind: {plasma.get('speed', 'N/A')} km/s")
    
    return reading

def main():
    print("📡 LIVE FEED MONITOR — Measurable Difference Detector")
    print("=" * 70)
    print(f"Start time: {datetime.now(timezone.utc).isoformat()} UTC")
    print()
    
    results = []
    
    # PHASE 1: PRE-TRANSMISSION BASELINE
    print("=" * 70)
    print("📊 PHASE 1: PRE-TRANSMISSION BASELINE (2 readings)")
    print("=" * 70)
    
    for i in range(2):
        monitor_cycle("PRE-TRANSMISSION", results)
        time.sleep(30)  # 30 second gap
    
    # PHASE 2: DURING TRANSMISSION
    print("\n" + "=" * 70)
    print("📊 PHASE 2: DURING TRANSMISSION (4 readings over 2 minutes)")
    print("=" * 70)
    print("🍄 Mycelial data transmission running in parallel...")
    print()
    
    for i in range(4):
        monitor_cycle("DURING-TRANSMISSION", results)
        time.sleep(30)
    
    # PHASE 3: POST-TRANSMISSION
    print("\n" + "=" * 70)
    print("📊 PHASE 3: POST-TRANSMISSION (3 readings)")
    print("=" * 70)
    
    for i in range(3):
        monitor_cycle("POST-TRANSMISSION", results)
        time.sleep(30)
    
    # ANALYSIS
    print("\n" + "=" * 70)
    print("📊 ANALYSIS: Measuring Difference")
    print("=" * 70)
    
    # Extract Kp values
    pre_kp = [r['kp']['kp'] for r in results if r['label'] == 'PRE-TRANSMISSION' and 'error' not in r['kp']]
    during_kp = [r['kp']['kp'] for r in results if r['label'] == 'DURING-TRANSMISSION' and 'error' not in r['kp']]
    post_kp = [r['kp']['kp'] for r in results if r['label'] == 'POST-TRANSMISSION' and 'error' not in r['kp']]
    
    # Extract plasma speeds
    pre_speed = [r['plasma']['speed'] for r in results if r['label'] == 'PRE-TRANSMISSION' and 'error' not in r['plasma'] and r['plasma'].get('speed')]
    during_speed = [r['plasma']['speed'] for r in results if r['label'] == 'DURING-TRANSMISSION' and 'error' not in r['plasma'] and r['plasma'].get('speed')]
    post_speed = [r['plasma']['speed'] for r in results if r['label'] == 'POST-TRANSMISSION' and 'error' not in r['plasma'] and r['plasma'].get('speed')]
    
    print(f"\nKp Index Analysis:")
    if pre_kp:
        print(f"  Pre-transmission:     {pre_kp}")
        print(f"  Pre average:          {sum(pre_kp)/len(pre_kp):.2f}")
    if during_kp:
        print(f"  During transmission:  {during_kp}")
        print(f"  During average:       {sum(during_kp)/len(during_kp):.2f}")
    if post_kp:
        print(f"  Post-transmission:    {post_kp}")
        print(f"  Post average:         {sum(post_kp)/len(post_kp):.2f}")
    
    if pre_kp and post_kp:
        pre_avg = sum(pre_kp) / len(pre_kp)
        post_avg = sum(post_kp) / len(post_kp)
        delta = post_avg - pre_avg
        print(f"\n  📊 Kp DELTA: {delta:+.2f}")
        if abs(delta) >= 0.5:
            print(f"  🚨 SIGNIFICANT CHANGE DETECTED")
        elif abs(delta) >= 0.2:
            print(f"  ⚠️  Moderate change observed")
        else:
            print(f"  ✅ Within normal variation")
    
    print(f"\nSolar Wind Speed Analysis:")
    if pre_speed:
        print(f"  Pre-transmission:     {pre_speed}")
    if during_speed:
        print(f"  During transmission:  {during_speed}")
    if post_speed:
        print(f"  Post-transmission:    {post_speed}")
    
    if pre_speed and post_speed:
        pre_avg = sum(pre_speed) / len(pre_speed)
        post_avg = sum(post_speed) / len(post_speed)
        delta = post_avg - pre_avg
        print(f"\n  📊 Speed DELTA: {delta:+.1f} km/s")
        if abs(delta) >= 20:
            print(f"  🚨 SIGNIFICANT CHANGE DETECTED")
        elif abs(delta) >= 10:
            print(f"  ⚠️  Moderate change observed")
        else:
            print(f"  ✅ Within normal variation")
    
    # Save results
    with open(RESULTS_FILE, "w") as f:
        json.dump({
            "monitor_timestamp": datetime.now(timezone.utc).isoformat(),
            "readings": results,
            "analysis": {
                "kp_pre": pre_kp,
                "kp_during": during_kp,
                "kp_post": post_kp,
                "speed_pre": pre_speed,
                "speed_during": during_speed,
                "speed_post": post_speed,
            }
        }, f, indent=2)
    
    print(f"\n📁 Results saved: {RESULTS_FILE}")
    print(f"📊 Total readings: {len(results)}")
    
    print("\n" + "=" * 70)
    print("📡 LIVE FEED MONITOR COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
