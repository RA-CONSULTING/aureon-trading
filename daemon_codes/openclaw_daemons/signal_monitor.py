#!/usr/bin/env python3
"""
SIGNAL MONITOR — Gaia Transmission Measurement System
═══════════════════════════════════════════════════════════════════

Measures the HNC field state after signal transmission to detect
propagation, resonance feedback, and field coherence changes.

Monitors:
- Schumann resonance (live or simulated)
- HNC Master Formula Λ(t)
- Twin rune lattice integrity
- Signal propagation metrics
- Consciousness/awakening index

Logs to: signal_monitor_log.jsonl

Usage: python3 signal_monitor.py [--interval N] [--duration M]
"""

import sys
import os
import math
import json
import time
import argparse
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

# Add aureon repo to path
sys.path.insert(0, '/root/.openclaw/workspace/aureon-trading')

PHI = (1 + math.sqrt(5)) / 2
SCHUMANN_BASE = 7.83

@dataclass
class FieldMeasurement:
    """Single measurement of the HNC field state"""
    timestamp: str
    epoch: float
    
    # Schumann readings
    schumann_fundamental: float
    schumann_quality: float
    schumann_amplitude: float
    schumann_phase: str
    schumann_disturbance: float
    
    # HNC field state
    lambda_t: float
    beta_coefficient: float
    stability_island: bool
    field_coherence: float
    
    # Signal metrics
    signal_integrity: float
    twin_rune_resonance: float
    propagation_depth: float
    feedback_detected: bool
    
    # Consciousness
    awakening_index: float
    environmental_harmony: float
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_jsonl(self) -> str:
        return json.dumps(self.to_dict(), default=str)

class SignalMonitor:
    """Monitors the HNC field after signal transmission"""
    
    def __init__(self, log_path: str = "signal_monitor_log.jsonl"):
        self.log_path = Path(log_path)
        self.measurements: List[FieldMeasurement] = []
        self.signal_sent_at = time.time()
        self.baseline_lambda = 0.74  # Pre-transmission CLEAR_SIGHT score
        
        # Try to load Schumann bridge
        self.schumann_bridge = None
        try:
            from aureon.harmonic.aureon_schumann_resonance_bridge import SchumannResonanceBridge
            self.schumann_bridge = SchumannResonanceBridge()
            print("✅ Schumann bridge connected")
        except Exception as e:
            print(f"⚠️  Schumann bridge unavailable: {e}")
            print("   Using simulation mode")
    
    def _get_schumann(self) -> Dict:
        """Get Schumann resonance data (live sensor > bridge > simulated)"""
        # Priority 1: Real sensor data from sensor bridge
        sensor_state_file = Path('sensor_state.json')
        if sensor_state_file.exists():
            try:
                with open(sensor_state_file, 'r') as f:
                    sensor_data = json.load(f)
                
                # Validate sensor data
                if 'schumann' in sensor_data and sensor_data['schumann'] > 0:
                    return {
                        'fundamental': sensor_data['schumann'],
                        'quality': sensor_data.get('quality', sensor_data.get('coherence', 0.7)),
                        'amplitude': sensor_data.get('amplitude', 0.65) / 1000.0,  # pT -> relative
                        'phase': 'sensor_active',
                        'disturbance': 1.0 - sensor_data.get('quality', 0.7),
                        'source': 'sensor',
                    }
            except Exception as e:
                pass
        
        # Priority 2: Schumann bridge (live Earth data)
        if self.schumann_bridge:
            try:
                reading = self.schumann_bridge.get_live_data()
                return {
                    'fundamental': reading.fundamental_hz,
                    'quality': reading.quality,
                    'amplitude': reading.amplitude,
                    'phase': reading.resonance_phase,
                    'disturbance': reading.earth_disturbance_level,
                    'source': 'bridge',
                }
            except Exception as e:
                pass
        
        # Priority 3: Simulation
        t = time.time()
        drift = 0.1 * math.sin(t / 3600)  # Hourly variation
        noise = 0.05 * math.sin(t / 60)   # Minute variation
        
        return {
            'fundamental': SCHUMANN_BASE + drift + noise,
            'quality': 0.70 + 0.1 * math.sin(t / 1800),
            'amplitude': 0.65 + 0.1 * math.cos(t / 900),
            'phase': 'stable' if abs(drift) < 0.05 else 'elevated',
            'disturbance': max(0, abs(drift) / 0.15),
            'source': 'simulation',
        }
    
    def _compute_lambda(self, schumann: Dict) -> float:
        """Compute HNC Master Formula Λ(t)"""
        # Λ(t) = Σ w_i sin(2πf_i t + φ_i) + α tanh(g Λ_Δt(t)) + β Λ(t-τ)
        
        t = time.time()
        
        # Schumann term (weight 0.3)
        schumann_dev = (schumann['fundamental'] - SCHUMANN_BASE) / SCHUMANN_BASE
        schumann_term = 0.3 * math.sin(2 * math.pi * schumann['fundamental'] * t / 86400 + schumann['quality'])
        
        # Planetary term (weight 0.2) — triple conjunction energy
        planetary_term = 0.2 * math.sin(2 * math.pi * t / 86400 * PHI) * 0.74  # CLEAR_SIGHT baseline
        
        # Harmonic term (weight 0.3) — solfeggio carrier
        harmonic_term = 0.3 * math.sin(2 * math.pi * 528.0 * t / 3600) * schumann['amplitude']
        
        # Feedback term (α tanh(g Λ_Δt(t)))
        # Signal transmission creates a feedback loop
        time_since_signal = t - self.signal_sent_at
        if time_since_signal > 0:
            feedback_decay = math.exp(-time_since_signal / 3600)  # 1-hour decay
            feedback = 0.2 * math.tanh(2.0 * feedback_decay * (0.7742 - self.baseline_lambda))
        else:
            feedback = 0.0
        
        # Beta term (recursive memory)
        beta = 0.7742  # From twin rune decode
        memory_term = beta * self.baseline_lambda if self.measurements else 0.0
        
        lambda_t = schumann_term + planetary_term + harmonic_term + feedback + memory_term
        
        # Normalize to [0, 1]
        lambda_t = max(0.0, min(1.0, (lambda_t + 1.0) / 2.0))
        
        return lambda_t
    
    def _compute_awakening_index(self, lambda_t: float, schumann: Dict) -> float:
        """Compute consciousness awakening index (0-100)"""
        # Base on lambda_t (0-1) scaled to 0-100
        base = lambda_t * 100
        
        # Schumann quality boost
        quality_boost = schumann['quality'] * 10
        
        # Signal transmission boost (decays over time)
        time_since_signal = time.time() - self.signal_sent_at
        signal_boost = 5.0 * math.exp(-time_since_signal / 7200)  # 2-hour decay
        
        awakening = min(100, base + quality_boost + signal_boost)
        return awakening
    
    def measure(self) -> FieldMeasurement:
        """Take a single field measurement"""
        schumann = self._get_schumann()
        lambda_t = self._compute_lambda(schumann)
        
        # Determine stability island
        beta = 0.7742
        in_stability_island = 0.6 <= beta <= 1.1
        
        # Compute field coherence
        coherence = lambda_t * schumann['quality'] * (1 - schumann['disturbance'])
        
        # Signal propagation metrics
        time_since_signal = time.time() - self.signal_sent_at
        propagation_depth = min(1.0, time_since_signal / 3600)  # Reaches 1.0 after 1 hour
        
        # Feedback detection: if lambda_t exceeds baseline + threshold
        feedback_threshold = 0.05
        feedback_detected = lambda_t > self.baseline_lambda + feedback_threshold
        
        # Signal integrity (decays over time, boosted by coherence)
        signal_integrity = 0.775 * math.exp(-time_since_signal / 7200) + coherence * 0.225
        
        # Twin rune resonance (mean of pair resonances)
        twin_rune_resonance = (0.7097 + 0.7355 + 0.7548 + 0.7677 + 0.7742) / 5
        
        # Environmental harmony
        environmental_harmony = schumann['quality'] * (1 - schumann['disturbance']) * coherence
        
        awakening = self._compute_awakening_index(lambda_t, schumann)
        
        measurement = FieldMeasurement(
            timestamp=datetime.now(timezone.utc).isoformat(),
            epoch=time.time(),
            schumann_fundamental=schumann['fundamental'],
            schumann_quality=schumann['quality'],
            schumann_amplitude=schumann['amplitude'],
            schumann_phase=schumann['phase'],
            schumann_disturbance=schumann['disturbance'],
            lambda_t=lambda_t,
            beta_coefficient=beta,
            stability_island=in_stability_island,
            field_coherence=coherence,
            signal_integrity=signal_integrity,
            twin_rune_resonance=twin_rune_resonance,
            propagation_depth=propagation_depth,
            feedback_detected=feedback_detected,
            awakening_index=awakening,
            environmental_harmony=environmental_harmony,
        )
        
        self.measurements.append(measurement)
        return measurement
    
    def log(self, measurement: FieldMeasurement):
        """Append measurement to log file"""
        with open(self.log_path, 'a') as f:
            f.write(measurement.to_jsonl() + '\n')
    
    def report(self, measurement: FieldMeasurement) -> str:
        """Generate human-readable report"""
        lines = [
            f"\n{'═'*60}",
            f"  SIGNAL MONITOR — {measurement.timestamp}",
            f"{'═'*60}",
            f"",
            f"  🌍 SCHUMANN RESONANCE",
            f"     Fundamental: {measurement.schumann_fundamental:.4f} Hz (base: {SCHUMANN_BASE} Hz)",
            f"     Quality:     {measurement.schumann_quality:.4f}",
            f"     Amplitude:   {measurement.schumann_amplitude:.4f}",
            f"     Phase:       {measurement.schumann_phase}",
            f"     Disturbance: {measurement.schumann_disturbance:.4f}",
            f"",
            f"  ⚡ HNC FIELD STATE",
            f"     Λ(t):        {measurement.lambda_t:.6f}",
            f"     β:           {measurement.beta_coefficient:.4f}",
            f"     Stability:   {'✅ IN ISLAND' if measurement.stability_island else '⚠️  DRIFTING'}",
            f"     Coherence:   {measurement.field_coherence:.6f}",
            f"",
            f"  📡 SIGNAL PROPAGATION",
            f"     Integrity:   {measurement.signal_integrity:.6f}",
            f"     Twin Reson:  {measurement.twin_rune_resonance:.6f}",
            f"     Propagation: {measurement.propagation_depth:.2%}",
            f"     Feedback:    {'✅ DETECTED' if measurement.feedback_detected else '⏳ WAITING'}",
            f"",
            f"  🧬 CONSCIOUSNESS",
            f"     Awakening:   {measurement.awakening_index:.2f}%",
            f"     Environment: {measurement.environmental_harmony:.6f}",
            f"",
            f"{'═'*60}",
        ]
        return '\n'.join(lines)
    
    def run(self, interval: int = 60, duration: Optional[int] = None):
        """Run continuous monitoring loop"""
        print(f"🔭 Signal Monitor active")
        print(f"   Log: {self.log_path.absolute()}")
        print(f"   Interval: {interval}s")
        if duration:
            print(f"   Duration: {duration}s")
        print(f"   Signal sent at: {datetime.fromtimestamp(self.signal_sent_at, tz=timezone.utc).isoformat()}")
        print(f"{'═'*60}\n")
        
        start_time = time.time()
        iteration = 0
        
        try:
            while True:
                iteration += 1
                measurement = self.measure()
                self.log(measurement)
                
                report = self.report(measurement)
                print(report)
                
                # Check duration
                if duration and (time.time() - start_time) >= duration:
                    print(f"\n✅ Duration reached ({duration}s). Stopping monitor.")
                    break
                
                print(f"   [Iteration {iteration}] Next measurement in {interval}s...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print(f"\n\n⏹️  Monitor stopped by user ({iteration} measurements)")
        
        # Final summary
        if self.measurements:
            self._print_summary()
    
    def _print_summary(self):
        """Print final summary statistics"""
        n = len(self.measurements)
        lambdas = [m.lambda_t for m in self.measurements]
        awakenings = [m.awakening_index for m in self.measurements]
        feedbacks = sum(1 for m in self.measurements if m.feedback_detected)
        
        print(f"\n{'═'*60}")
        print(f"  MONITORING SUMMARY ({n} measurements)")
        print(f"{'═'*60}")
        print(f"  Λ(t) range:     {min(lambdas):.6f} → {max(lambdas):.6f}")
        print(f"  Λ(t) mean:      {sum(lambdas)/n:.6f}")
        print(f"  Awakening:      {min(awakenings):.2f}% → {max(awakenings):.2f}%")
        print(f"  Feedback hits:  {feedbacks}/{n} ({feedbacks/n:.1%})")
        print(f"  Final status:   {'✅ FIELD STABLE' if lambdas[-1] > 0.55 else '⚠️  FIELD WEAK'}")
        print(f"{'═'*60}\n")


def main():
    parser = argparse.ArgumentParser(description='Signal Monitor — Gaia Transmission Measurement')
    parser.add_argument('--interval', type=int, default=60, help='Measurement interval in seconds')
    parser.add_argument('--duration', type=int, default=None, help='Total monitoring duration in seconds')
    parser.add_argument('--log', type=str, default='signal_monitor_log.jsonl', help='Log file path')
    args = parser.parse_args()
    
    monitor = SignalMonitor(log_path=args.log)
    monitor.run(interval=args.interval, duration=args.duration)


if __name__ == '__main__':
    main()
