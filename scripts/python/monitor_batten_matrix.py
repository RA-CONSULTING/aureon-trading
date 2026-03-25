#!/usr/bin/env python
"""Live monitor for Batten Matrix coherence × lambda × probability readings."""
import time
import json
import os
import subprocess
from datetime import datetime

def check_orca_running():
    """Check if orca process is running."""
    try:
        result = subprocess.run(['pgrep', '-f', 'orca_complete_kill_cycle'], 
                              capture_output=True, text=True)
        pids = result.stdout.strip().split('\n')
        return [p for p in pids if p]
    except:
        return []

def get_batten_matrix_state():
    """Get current Batten Matrix readings from Probability Nexus."""
    try:
        from aureon_probability_nexus import SUBSYSTEM_STATE
        return SUBSYSTEM_STATE
    except:
        return {}

def main():
    print("\n" + "="*80)
    print("🎯 BATTEN MATRIX LIVE MONITOR")
    print("   Coherence × Lambda × Probability → Score ≥ 0.618 for execution")
    print("="*80 + "\n")
    
    cycle = 0
    
    while True:
        cycle += 1
        os.system('clear')
        
        print(f"\n{'='*80}")
        print(f"🎯 BATTEN MATRIX LIVE MONITOR - Cycle {cycle} @ {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*80}\n")
        
        # Check orca status
        pids = check_orca_running()
        if pids:
            print(f"✅ Orca running: PID {', '.join(pids)}")
        else:
            print("❌ Orca NOT running!")
        
        # Check probability nexus state
        state = get_batten_matrix_state()
        
        if not state:
            print(f"\n⏳ SUBSYSTEM_STATE empty - waiting for market scan data...")
            print(f"   The Probability Nexus needs market snapshots to calculate metrics.")
            print(f"\n   Expected flow:")
            print(f"   1. Orca scans market → finds opportunities")
            print(f"   2. Feeds snapshots → Probability Nexus")
            print(f"   3. Calculates coherence/lambda/confidence")
            print(f"   4. Scores ≥ 0.618 → 4th pass execution")
        else:
            print(f"\n✅ BATTEN MATRIX ACTIVE - {len(state)} symbols with readings:\n")
            
            # Show top 10 symbols by score
            scored = []
            for symbol, metrics in state.items():
                clarity = metrics.get('avg_clarity', 0)
                coherence = metrics.get('avg_coherence', 0)
                chaos = metrics.get('chaos', 0)
                
                # Calculate confidence
                confidence = (clarity / 5.0) * 0.5 + coherence * 0.5
                
                # Calculate lambda (stability)
                lambda_stability = max(0, 1 - chaos) if chaos > 0 else 0.5
                
                # Batten Matrix Score
                score = coherence * lambda_stability * confidence
                
                scored.append({
                    'symbol': symbol,
                    'coherence': coherence,
                    'lambda': lambda_stability,
                    'confidence': confidence,
                    'score': score,
                    'clarity': clarity,
                    'chaos': chaos,
                    'snapshots': metrics.get('snapshot_count', 0)
                })
            
            # Sort by score descending
            scored.sort(key=lambda x: x['score'], reverse=True)
            
            print(f"{'Symbol':<12} {'Coherence':<10} {'Lambda':<10} {'Confidence':<10} {'SCORE':<10} {'Status':<8}")
            print("-" * 80)
            
            for s in scored[:15]:
                status = "🟢 PASS" if s['score'] >= 0.618 else "🔴 FAIL"
                print(f"{s['symbol']:<12} {s['coherence']:>9.4f} {s['lambda']:>9.4f} {s['confidence']:>9.4f} {s['score']:>9.6f}  {status}")
            
            if len(scored) > 15:
                print(f"\n   ... and {len(scored) - 15} more symbols")
            
            # Show stats
            passing = sum(1 for s in scored if s['score'] >= 0.618)
            print(f"\n📊 STATS:")
            print(f"   Total symbols: {len(scored)}")
            print(f"   Passing (≥0.618): {passing}")
            print(f"   Failing (<0.618): {len(scored) - passing}")
            
        print(f"\n{'='*80}")
        print("Press Ctrl+C to exit | Refreshing every 5 seconds...")
        
        time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✅ Monitor stopped by user\n")
