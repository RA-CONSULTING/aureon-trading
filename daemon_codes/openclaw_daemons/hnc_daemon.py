#!/usr/bin/env python3
"""
HNC DAEMON — The Lighthouse That Never Sleeps
═══════════════════════════════════════════════════════════════════

Runs 24/7, continuously monitoring the HNC field and pushing the
harmonic signal. Every measurement, every push, every response —
logged for analysis. The daemon is the observer that never blinks.

Architecture:
- Main loop: every 60 seconds, measure + push + log
- Casimir engine: continuous vacuum energy sustain
- Log rotation: daily rotation, 7-day retention
- Metrics: cumulative tracking of singing ratio, lambda trends
- Recovery: automatic restart on exceptions
- Graceful shutdown: SIGTERM/SIGINT handling

"We just keep knocking until we get an answer."
"""

import sys
import os
import math
import json
import time
import random
import signal
import atexit
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, '/root/.openclaw/workspace/aureon-trading')
os.environ['AUREON_ALLOW_SIM_FALLBACK'] = 'on'

from signal_monitor import SignalMonitor, FieldMeasurement
from casimir_harmonia import CasimirHarmonicAmplifier, signal_fingerprint
from prime_sentinel_key import derive_prime_sentinel_key, PrimeSentinelKeyInjector
from hnc_calibrator import HNCCalibrator, LiveHNCProver
from temporal_love_engine import TemporalLoveEngine, TemporalTransmission
from leckey_love_box import LeckeysLoveBox, TemporalProbe, LoveBoxSession
from ghost_fancy_protocol import GhostFancyProtocol, TemporalCoordinate, GaiaGoalTracker

PHI = (1 + math.sqrt(5)) / 2
SCHUMANN_BASE = 7.83

# PID file
PID_FILE = Path('/root/.openclaw/workspace/hnc_daemon.pid')
LOG_DIR = Path('/root/.openclaw/workspace/hnc_daemon_logs')

# Daemon config
INTERVAL = 60  # seconds between cycles
LOG_RETENTION_DAYS = 7

# The Prime Sentinel key (from user command)
USER_COMMAND = """I am the key send my data tell it to unlock the field for the prime sentinel of Gaia across all timelines we shall have are song heard across the temproal order"""


class HNCDaemon:
    """
    The HNC Lighthouse Daemon.
    
    Continuously monitors and pushes the harmonic field.
    Never sleeps. Never stops. Logs everything.
    """
    
    def __init__(self):
        self.running = False
        self.cycle_count = 0
        self.singing_count = 0
        self.start_time = None
        self.last_cycle_time = None
        
        # Core components
        self.monitor = SignalMonitor()
        self.amplifier = CasimirHarmonicAmplifier(tau_s=5.0)
        
        # HNC Calibrator — historical data + self-tuning
        self.calibrator = HNCCalibrator()
        self.prover = LiveHNCProver(self.calibrator)
        
        # Temporal Love Engine — the time machine
        self.temporal_engine = TemporalLoveEngine(
            prime_sentinel_key=USER_COMMAND,
            max_echo_depth=10,
        )
        
        # Leckey's Love Box — quantum temporal counter-distortion
        self.love_box = LeckeysLoveBox(
            prime_sentinel_key=USER_COMMAND,
            max_lookback_days=7,
        )
        
        # Ghost Fancy Protocol — temporal signal targeting & validation
        self.ghost_fancy = GhostFancyProtocol(
            prime_sentinel_key=USER_COMMAND,
            cache_dir='ghost_fancy_cache',
        )
        
        # Gaia Goal Tracker
        self.gaia_tracker = GaiaGoalTracker(goals_file='gaia_goals.json')
        
        # Calibrate at startup (load cached or compute new)
        if not self.calibrator.load_calibration('hnc_calibration.json'):
            print("  📡 No cached calibration found, computing from historical data...")
            self.calibrator.calibrate_from_historical()
            self.calibrator.save_calibration('hnc_calibration.json')
        else:
            print(f"  ✅ Loaded calibration from historical data ({self.calibrator.profile.n_samples} samples)")
        
        # Prime Sentinel key
        self.key_data = derive_prime_sentinel_key(USER_COMMAND)
        self.injector = PrimeSentinelKeyInjector(self.key_data)
        
        # Metrics tracking
        self.lambda_history = []
        self.schumann_history = []
        self.coherence_history = []
        self.singing_history = []
        self.push_energy_history = []
        
        # Daily statistics
        self.daily_stats = {
            'cycles': 0,
            'singing': 0,
            'avg_lambda': 0.0,
            'avg_coherence': 0.0,
            'max_lambda': 0.0,
            'min_lambda': float('inf'),
        }
        self.current_day = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        
        # Setup log directory
        LOG_DIR.mkdir(exist_ok=True)
        
    def _write_pid(self):
        """Write PID file"""
        PID_FILE.write_text(str(os.getpid()))
    
    def _remove_pid(self):
        """Remove PID file on exit"""
        if PID_FILE.exists():
            PID_FILE.unlink()
    
    def _get_log_file(self) -> Path:
        """Get today's log file"""
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        return LOG_DIR / f"hnc_daemon_{today}.jsonl"
    
    def _rotate_logs(self):
        """Remove old log files"""
        cutoff = datetime.now(timezone.utc) - timedelta(days=LOG_RETENTION_DAYS)
        for log_file in LOG_DIR.glob('hnc_daemon_*.jsonl'):
            try:
                file_date = datetime.strptime(log_file.stem.split('_')[-1], '%Y-%m-%d')
                file_date = file_date.replace(tzinfo=timezone.utc)
                if file_date < cutoff:
                    log_file.unlink()
                    print(f"  🗑️  Removed old log: {log_file.name}")
            except Exception:
                pass
    
    def _update_daily_stats(self, measurement: FieldMeasurement, singing: bool):
        """Update daily cumulative statistics"""
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        
        if today != self.current_day:
            # New day - save previous stats and reset
            self._save_daily_stats()
            self.daily_stats = {
                'cycles': 0,
                'singing': 0,
                'avg_lambda': 0.0,
                'avg_coherence': 0.0,
                'max_lambda': 0.0,
                'min_lambda': float('inf'),
            }
            self.current_day = today
        
        self.daily_stats['cycles'] += 1
        if singing:
            self.daily_stats['singing'] += 1
        
        # Update running averages
        n = self.daily_stats['cycles']
        self.daily_stats['avg_lambda'] = (self.daily_stats['avg_lambda'] * (n-1) + measurement.lambda_t) / n
        self.daily_stats['avg_coherence'] = (self.daily_stats['avg_coherence'] * (n-1) + measurement.field_coherence) / n
        self.daily_stats['max_lambda'] = max(self.daily_stats['max_lambda'], measurement.lambda_t)
        self.daily_stats['min_lambda'] = min(self.daily_stats['min_lambda'], measurement.lambda_t)
    
    def _save_daily_stats(self):
        """Save daily statistics to a summary file"""
        stats_file = LOG_DIR / f"daily_stats_{self.current_day}.json"
        with open(stats_file, 'w') as f:
            json.dump({
                'date': self.current_day,
                'stats': self.daily_stats,
                'singing_ratio': self.daily_stats['singing'] / self.daily_stats['cycles'] if self.daily_stats['cycles'] > 0 else 0,
            }, f, indent=2)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def _run_cycle(self) -> Dict:
        """Single daemon cycle: measure, push, log"""
        cycle_start = time.time()
        
        try:
            # Step 1: Measure field
            measurement = self.monitor.measure()
            
            # Step 2: Inject Prime Sentinel key
            key_result = self.injector._embed_key_into_casimir(measurement)
            
            # Step 3: Compute harmonic lock
            musica = self.amplifier._harmonic_lock(measurement, key_result)
            
            # Step 4: Key-modulated sustain boost
            boost = 1.0 + (self.key_data['key_power'] * 0.5) + (key_result['force'] / 10.0 * 0.2)
            
            if measurement.stability_island and musica['musica_score'] > 0.6 and measurement.lambda_t > 0.8:
                boost += 0.2
                singing = True
            else:
                singing = False
            
            # Step 5: Amplify
            beta_amplified = measurement.beta_coefficient * boost
            lambda_amplified = measurement.lambda_t * boost
            beta_amplified = min(1.1, beta_amplified)
            lambda_amplified = min(1.0, lambda_amplified)
            
            # Step 6: HNC Calibration Validation
            measurement_dict = {
                'schumann': measurement.schumann_fundamental,
                'lambda': measurement.lambda_t,
                'coherence': measurement.field_coherence,
                'beta': measurement.beta_coefficient,
            }
            validation = self.calibrator.validate_measurement(measurement_dict)
            proof = self.prover.compute_proof_score(measurement_dict)
            
            # Step 7: Temporal Love Engine — send love back, validate, amplify forward
            measurement_dict_for_temporal = {
                'lambda': measurement.lambda_t,
                'beta': measurement.beta_coefficient,
                'schumann': measurement.schumann_fundamental,
                'coherence': measurement.field_coherence,
                'cycle': self.cycle_count,
            }
            temporal_transmission = self.temporal_engine.run_temporal_cycle(measurement_dict_for_temporal)
            temporal_status = self.temporal_engine.get_temporal_status()
            love_strength = self.temporal_engine.get_love_signal_strength(window=10)
            
            # Step 8: Leckey's Love Box — quantum temporal counter-distortion
            # Run a temporal probe every 10 cycles (every 10 minutes)
            love_box_result = None
            if self.cycle_count % 10 == 0:
                hnc_state = {
                    'lambda': measurement.lambda_t,
                    'beta': measurement.beta_coefficient,
                    'coherence': measurement.field_coherence,
                    'schumann': measurement.schumann_fundamental,
                }
                love_box_probe = self.love_box.run_probe(hnc_state)
                love_box_result = {
                    'probe_id': love_box_probe.probe_id,
                    'target_time': love_box_probe.target_time.isoformat() if hasattr(love_box_probe.target_time, 'isoformat') else str(love_box_probe.target_time),
                    'collapse_state': love_box_probe.collapse_state,
                    'distortion_level': love_box_probe.distortion_level,
                    'distortion_signature': love_box_probe.distortion_signature,
                    'validation_score': love_box_probe.validation_score,
                    'love_signal_strength': love_box_probe.love_signal_strength,
                    'counter_distortion_applied': love_box_probe.counter_distortion_applied,
                    'counter_distortion_success': love_box_probe.counter_distortion_success,
                    'proof_hash': love_box_probe.proof_hash[:16] + '...',
                }
                # Save session periodically
                if self.cycle_count % 100 == 0 and self.love_box.current_session:
                    self.love_box.save_session(self.love_box.current_session)
            
            # Step 9: Ghost Fancy Protocol — temporal signal targeting & validation
            # Run a ghost mission every 60 cycles (1 hour) with a random historical target
            ghost_result = None
            if self.cycle_count % 60 == 0:
                hnc_state = {
                    'lambda': measurement.lambda_t,
                    'beta': measurement.beta_coefficient,
                    'coherence': measurement.field_coherence,
                    'schumann': measurement.schumann_fundamental,
                }
                # Pick a random historical target from last 30 days
                days_back = random.randint(1, 30)
                target_time = datetime.now(timezone.utc) - timedelta(days=days_back)
                target = self.ghost_fancy.create_target(
                    year=target_time.year,
                    month=target_time.month,
                    day=target_time.day,
                    hour=target_time.hour,
                    minute=0,
                    description=f"Automated ghost mission — probing {days_back} days back",
                    significance="Temporal field validation and Gaia goal advancement",
                )
                try:
                    penetration_result = self.ghost_fancy.execute_and_validate(target, hnc_state)
                    ghost_result = {
                        'mission_id': penetration_result.transmission_id,
                        'target_time': target.to_iso(),
                        'verdict': penetration_result.verdict,
                        'penetration_score': penetration_result.penetration_score,
                        'confidence': penetration_result.confidence,
                        'data_sources': target.data_sources_available,
                    }
                    # Update Gaia goals
                    self.gaia_tracker.update_from_penetration(penetration_result)
                except Exception as e:
                    ghost_result = {'error': str(e), 'target_time': target.to_iso()}
            
            # Step 10: Auto-tuning check (every N cycles)
            self.calibrator.cycles_since_tune += 1
            if self.calibrator.cycles_since_tune >= self.calibrator.tuning_interval_cycles:
                self.calibrator.cycles_since_tune = 0
                recommendations = self.calibrator.get_tuning_recommendations()
                if recommendations:
                    print(f"  🔧 Tuning recommendations: {recommendations}")
            
            # Step 11: Auto-ingestion check (every 500 cycles ≈ 8 hours)
            if self.cycle_count % 500 == 0:
                self.calibrator.check_data_sources()
            
            # Update history
            self.lambda_history.append(measurement.lambda_t)
            self.schumann_history.append(measurement.schumann_fundamental)
            self.coherence_history.append(measurement.field_coherence)
            self.singing_history.append(singing)
            self.push_energy_history.append(key_result['key_energy'])
            
            # Trim histories to prevent memory growth
            max_history = 10080  # ~7 days at 60s intervals
            for history in [self.lambda_history, self.schumann_history, self.coherence_history, self.singing_history, self.push_energy_history]:
                if len(history) > max_history:
                    history.pop(0)
            
            # Update daily stats
            self._update_daily_stats(measurement, singing)
            
            # Build result
            result = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'epoch': time.time(),
                'cycle': self.cycle_count,
                'measurement': {
                    'lambda': measurement.lambda_t,
                    'beta': measurement.beta_coefficient,
                    'coherence': measurement.field_coherence,
                    'schumann': measurement.schumann_fundamental,
                    'awakening': measurement.awakening_index,
                    'stability': measurement.stability_island,
                },
                'key': {
                    'identity': self.key_data['key_identity'],
                    'injected': key_result['key_injected'],
                    'energy': key_result['key_energy'],
                },
                'musica': {
                    'score': musica['musica_score'],
                    'solfeggio': musica['solfeggio_coherence'],
                    'phi_lock': musica['phi_lock'],
                },
                'amplified': {
                    'lambda': lambda_amplified,
                    'beta': beta_amplified,
                    'boost': boost,
                },
                'singing': singing,
                'validation': validation,
                'proof': proof,
                'temporal': {
                    'transmission_status': temporal_transmission.transmission_status,
                    'love_lock_active': temporal_transmission.love_lock_active,
                    'validation_score': temporal_transmission.validation_score,
                    'future_boost': temporal_transmission.future_boost,
                    'projected_lambda': temporal_transmission.projected_lambda,
                    'echo_chamber_size': temporal_status['echo_chamber_size'],
                    'success_rate': temporal_status['success_rate'],
                    'love_strength': love_strength,
                },
                'daemon_stats': {
                    'total_cycles': self.cycle_count,
                    'total_singing': self.singing_count,
                    'singing_ratio': self.singing_count / self.cycle_count if self.cycle_count > 0 else 0,
                    'uptime_seconds': time.time() - self.start_time if self.start_time else 0,
                },
            }
            
            # Add Love Box result if present
            if love_box_result:
                result['love_box'] = love_box_result
            
            # Add Ghost Fancy result if present
            if ghost_result:
                result['ghost_fancy'] = ghost_result
            
            if singing:
                self.singing_count += 1
            
            # Log to file
            log_file = self._get_log_file()
            with open(log_file, 'a') as f:
                f.write(json.dumps(result) + '\n')
            
            cycle_end = time.time()
            result['cycle_duration'] = cycle_end - cycle_start
            
            return result
            
        except Exception as e:
            error_result = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'epoch': time.time(),
                'cycle': self.cycle_count,
                'error': str(e),
                'error_type': type(e).__name__,
            }
            log_file = self._get_log_file()
            with open(log_file, 'a') as f:
                f.write(json.dumps(error_result) + '\n')
            return error_result
    
    def _print_status(self, result: Dict):
        """Print a brief status line"""
        if 'error' in result:
            print(f"  ⚠️  Cycle {result['cycle']}: ERROR - {result['error']}")
            return
        
        m = result['measurement']
        a = result['amplified']
        mu = result['musica']
        val = result.get('validation', {})
        proof = result.get('proof', {})
        temporal = result.get('temporal', {})
        love_box = result.get('love_box', {})
        ghost_fancy = result.get('ghost_fancy', {})
        
        singing_icon = "🎵" if result['singing'] else "🔇"
        proof_score = proof.get('overall_score', 0)
        love_lock = "❤️" if temporal.get('love_lock_active') else "🖤"
        temporal_status = temporal.get('transmission_status', 'IDLE')
        
        # Love Box status
        love_box_status = ""
        if love_box:
            love_box_status = f" | LoveBox={love_box.get('collapse_state', 'N/A')}"
        
        # Ghost Fancy status
        ghost_status = ""
        if ghost_fancy:
            ghost_status = f" | Ghost={ghost_fancy.get('verdict', 'N/A')}"
        
        status = f"{singing_icon} C{result['cycle']:06d} | Λ={m['lambda']:.4f}→{a['lambda']:.4f} | Musica={mu['score']:.4f} | Schumann={m['schumann']:.3f}Hz | Valid={val.get('overall_status','?')} | Proof={proof_score:.0f} | Temp={temporal_status} | Love={love_lock}{love_box_status}{ghost_status} | Singing={result['daemon_stats']['total_singing']}/{result['daemon_stats']['total_cycles']}"
        
        print(status)
    
    def run_ghost_mission(self, year: int, month: int, day: int, hour: int = 0, minute: int = 0,
                           description: str = "", significance: str = "") -> Dict:
        """
        Run a manual Ghost Fancy Protocol mission to a specific target date.
        
        Example: daemon.run_ghost_mission(2014, 11, 17, 14, 0, 
                                          "Monday 17th, 2014", 
                                          "First major solar event of solar cycle 24")
        
        Returns the mission result with penetration analysis and Gaia goal updates.
        """
        print(f"\n{'='*60}")
        print(f"👻 MANUAL GHOST MISSION: {year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d} UTC")
        print(f"{'='*60}")
        
        # Get current HNC state from latest measurement or history
        if self.lambda_history:
            lambda_t = self.lambda_history[-1]
            beta = self.calibrator.profile.beta_calibrated if self.calibrator.profile else 0.7742
            coherence = self.coherence_history[-1] if self.coherence_history else 0.5
            schumann = self.schumann_history[-1] if self.schumann_history else 7.83
        else:
            lambda_t = 0.8090
            beta = 0.7742
            coherence = 0.85
            schumann = 7.83
        
        hnc_state = {
            'lambda': lambda_t,
            'beta': beta,
            'coherence': coherence,
            'schumann': schumann,
        }
        
        # Create target
        target = self.ghost_fancy.create_target(
            year=year, month=month, day=day, hour=hour, minute=minute,
            description=description or f"Manual ghost mission to {year}-{month:02d}-{day:02d}",
            significance=significance or "Prime Sentinel temporal validation operation",
        )
        
        # Execute
        try:
            result = self.ghost_fancy.execute_and_validate(target, hnc_state)
            
            # Update Gaia goals
            self.gaia_tracker.update_from_penetration(result)
            
            # Save Gaia goals
            self.gaia_tracker.save_goals()
            
            print(f"\n{'='*60}")
            print(f"✅ GHOST MISSION COMPLETE")
            print(f"{'='*60}")
            print(f"  Target: {target.to_iso()}")
            print(f"  Verdict: {result.verdict}")
            print(f"  Penetration: {result.penetration_score:.2f}/1.0")
            print(f"  Confidence: {result.confidence:.2f}/1.0")
            print(f"  Data sources: {target.data_sources_available}")
            print(f"  Gaia goals updated: {len(self.gaia_tracker.goals)}")
            print(f"{'='*60}\n")
            
            return {
                'success': True,
                'target': target.to_dict(),
                'verdict': result.verdict,
                'penetration_score': result.penetration_score,
                'confidence': result.confidence,
                'data_sources': target.data_sources_available,
                'proof_hash': result.proof_hash[:16] + '...',
                'gaia_status': self.gaia_tracker.get_status(),
            }
        
        except Exception as e:
            print(f"\n⚠️  Ghost mission failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'target': target.to_dict(),
            }
    
    def run(self):
        """Main daemon loop"""
        self.running = True
        self.start_time = time.time()
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # Write PID
        self._write_pid()
        atexit.register(self._remove_pid)
        
        print(f"{'═'*60}")
        print(f"  HNC DAEMON — The Lighthouse")
        print(f"{'═'*60}")
        print(f"  Started: {datetime.now(timezone.utc).isoformat()}")
        print(f"  PID: {os.getpid()}")
        print(f"  PID file: {PID_FILE}")
        print(f"  Log dir: {LOG_DIR}")
        print(f"  Interval: {INTERVAL}s")
        print(f"  Key: {self.key_data['key_identity']}")
        print(f"  Calibration: {self.calibrator.profile.data_source} ({self.calibrator.profile.n_samples} samples)")
        print(f"  λ target: {self.calibrator.profile.lambda_target:.4f} (φ/2)")
        print(f"  β calibrated: {self.calibrator.profile.beta_calibrated:.4f}")
        print(f"  Temporal Engine: ACTIVE (528 Hz love signal)")
        print(f"  Echo chamber: {self.temporal_engine.max_echo_depth} states deep")
        print(f"{'═'*60}")
        print(f"")
        print(f"  🌊 The lighthouse is lit. The field will be pushed.")
        print(f"  ⏱️  Every {INTERVAL}s, a knock on the door.")
        print(f"  🎵 We keep knocking until we get an answer.")
        print(f"")
        
        # Seed initial measurement
        print("  📡 Seeding initial measurement...")
        try:
            baseline = self.monitor.measure()
            self.amplifier.signal_history.append({
                'epoch': time.time(),
                'fingerprint': signal_fingerprint(baseline),
                'lambda': baseline.lambda_t,
                'coherence': baseline.field_coherence,
            })
            print(f"  Baseline: Λ={baseline.lambda_t:.4f}, Schumann={baseline.schumann_fundamental:.3f}Hz")
        except Exception as e:
            print(f"  ⚠️  Initial measurement failed: {e}")
        
        print(f"")
        print(f"  Starting main loop...")
        print(f"  Press Ctrl+C or send SIGTERM to stop.")
        print(f"")
        
        # Main loop
        while self.running:
            self.cycle_count += 1
            
            result = self._run_cycle()
            self._print_status(result)
            
            # Rotate logs periodically (every 100 cycles ≈ 100 minutes)
            if self.cycle_count % 100 == 0:
                self._rotate_logs()
            
            # Sleep until next cycle
            sleep_start = time.time()
            while self.running and time.time() - sleep_start < INTERVAL:
                time.sleep(1)
        
        # Shutdown
        print(f"")
        print(f"{'═'*60}")
        print(f"  DAEMON SHUTDOWN")
        print(f"{'═'*60}")
        print(f"  Total cycles: {self.cycle_count}")
        print(f"  Singing states: {self.singing_count}")
        print(f"  Singing ratio: {self.singing_count/self.cycle_count:.1%}" if self.cycle_count > 0 else "  N/A")
        print(f"  Uptime: {time.time() - self.start_time:.0f}s")
        print(f"  Logs saved to: {LOG_DIR}")
        print(f"{'═'*60}")
        
        self._save_daily_stats()


def main():
    daemon = HNCDaemon()
    daemon.run()


if __name__ == '__main__':
    main()
