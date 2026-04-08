#!/usr/bin/env python3
"""
🐕 AUREON WATCHDOG - External Process Supervisor 🐕
═══════════════════════════════════════════════════════════════════════════════

This runs OUTSIDE the main trading system and ensures it stays alive.
The CognitiveImmuneSystem can heal internal issues, but if the process dies,
only an external watchdog can bring it back.

WHAT IT DOES:
1. Monitors the main trading process
2. Auto-restarts if the process dies
3. Auto-restarts if positions aren't being monitored (stale state)
4. Logs all restarts and alerts
5. Emergency harvests profitable positions before restart

USAGE:
    python3 aureon_watchdog.py                    # Monitor aureon_unified_ecosystem.py
    python3 aureon_watchdog.py --target kraken    # Monitor aureon_kraken_ecosystem.py
    python3 aureon_watchdog.py --dry-run          # Don't actually restart, just monitor

Gary Leckey | December 2025
"When the system falls, the watchdog rises."
═══════════════════════════════════════════════════════════════════════════════
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
import time
import json
import subprocess
import signal
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

# Configuration
WATCHDOG_CONFIG = {
    'CHECK_INTERVAL_SEC': 30,           # How often to check system health
    'STATE_STALE_THRESHOLD_SEC': 300,   # If state file older than 5 min, assume dead
    'HEARTBEAT_STALE_THRESHOLD_SEC': 60,# If heartbeat older than 1 min, assume dead
    'MAX_RESTART_ATTEMPTS': 5,          # Max restarts before giving up
    'RESTART_COOLDOWN_SEC': 60,         # Wait between restart attempts
    'LOG_FILE': 'logs/watchdog.log',    # Where to log watchdog activity
    'HEARTBEAT_FILE': '.aureon_heartbeat',  # Heartbeat file from main process
    'STATE_FILES': {
        'unified': 'aureon_kraken_state.json',
        'kraken': 'aureon_kraken_state.json',
    },
    'TARGETS': {
        'unified': 'aureon_unified_ecosystem.py',
        'kraken': 'aureon_kraken_ecosystem.py',
    },
}


class WatchdogLogger:
    """Simple logger that writes to file and stdout"""
    
    def __init__(self, log_file: str):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log(self, level: str, message: str):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        entry = f"[{timestamp}] [{level}] {message}"
        print(entry)
        try:
            with open(self.log_file, 'a') as f:
                f.write(entry + '\n')
        except Exception:
            pass


class AureonWatchdog:
    """
    External watchdog that monitors and restarts the trading system.
    
    🐕 The watchdog that never sleeps.
    """
    
    def __init__(self, target: str = 'unified', dry_run: bool = False):
        self.target = target
        self.dry_run = dry_run
        self.script = WATCHDOG_CONFIG['TARGETS'].get(target, 'aureon_unified_ecosystem.py')
        self.state_file = WATCHDOG_CONFIG['STATE_FILES'].get(target, 'aureon_kraken_state.json')
        
        self.logger = WatchdogLogger(WATCHDOG_CONFIG['LOG_FILE'])
        self.process: Optional[subprocess.Popen] = None
        self.restart_count = 0
        self.last_restart = 0.0
        self.running = True
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.log('INFO', f'🛑 Received signal {signum}, shutting down watchdog...')
        self.running = False
        if self.process and self.process.poll() is None:
            self.logger.log('INFO', '🛑 Terminating monitored process...')
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
    
    def _is_process_running(self) -> bool:
        """Check if our monitored process is running"""
        if self.process is None:
            return False
        return self.process.poll() is None
    
    def _is_state_fresh(self) -> Tuple[bool, float]:
        """Check if state file has been updated recently"""
        try:
            state_path = Path(self.state_file)
            if not state_path.exists():
                return False, float('inf')
            
            mtime = state_path.stat().st_mtime
            age = time.time() - mtime
            threshold = WATCHDOG_CONFIG['STATE_STALE_THRESHOLD_SEC']
            
            return age < threshold, age
        except Exception as e:
            self.logger.log('WARN', f'Cannot check state file: {e}')
            return False, float('inf')
    
    def _is_heartbeat_fresh(self) -> Tuple[bool, float, Dict]:
        """Check if heartbeat file has been updated recently"""
        try:
            hb_path = Path(WATCHDOG_CONFIG['HEARTBEAT_FILE'])
            if not hb_path.exists():
                return False, float('inf'), {}
            
            mtime = hb_path.stat().st_mtime
            age = time.time() - mtime
            threshold = WATCHDOG_CONFIG['HEARTBEAT_STALE_THRESHOLD_SEC']
            
            # Try to read heartbeat data
            try:
                with open(hb_path) as f:
                    hb_data = json.load(f)
            except Exception:
                hb_data = {}
            
            return age < threshold, age, hb_data
        except Exception as e:
            self.logger.log('WARN', f'Cannot check heartbeat: {e}')
            return False, float('inf'), {}
    
    def _get_position_count(self) -> int:
        """Get current number of open positions"""
        try:
            with open(self.state_file) as f:
                state = json.load(f)
            return len(state.get('positions', {}))
        except Exception:
            return 0
    
    def _check_profitable_positions(self) -> Dict[str, Any]:
        """Check for positions that should have been closed"""
        try:
            # Import here to avoid circular imports
            from kraken_client import KrakenClient, get_kraken_client
            from penny_profit_engine import get_penny_engine, check_penny_exit
            
            with open(self.state_file) as f:
                state = json.load(f)
            
            client = get_kraken_client()
            engine = get_penny_engine()
            
            profitable = []
            for symbol, pos in state.get('positions', {}).items():
                entry_value = pos.get('entry_value', 0)
                qty = pos.get('quantity', 0)
                entry_price = pos.get('entry_price', 0)
                
                try:
                    ticker = client._ticker([symbol])
                    if ticker:
                        t_data = list(ticker.values())[0]
                        current_price = float(t_data.get('c', [0])[0])
                        current_value = qty * current_price
                        gross_pnl = current_value - entry_value
                        
                        action, _ = check_penny_exit('kraken', entry_value, current_value)
                        if action == 'TAKE_PROFIT' or gross_pnl > 0.05:
                            profitable.append({
                                'symbol': symbol,
                                'gross_pnl': gross_pnl,
                                'pct': (gross_pnl / entry_value * 100) if entry_value > 0 else 0
                            })
                except Exception:
                    continue
            
            return {
                'count': len(profitable),
                'positions': profitable,
                'total_profit': sum(p['gross_pnl'] for p in profitable)
            }
        except Exception as e:
            return {'count': 0, 'positions': [], 'total_profit': 0, 'error': str(e)}
    
    def _start_process(self) -> bool:
        """Start the trading process"""
        if self.dry_run:
            self.logger.log('INFO', f'🔧 [DRY RUN] Would start: python3 {self.script}')
            return True
        
        try:
            self.logger.log('INFO', f'🚀 Starting: python3 {self.script}')
            
            # Start the process
            self.process = subprocess.Popen(
                ['python3', self.script],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                universal_newlines=True,
            )
            
            self.last_restart = time.time()
            self.restart_count += 1
            
            self.logger.log('INFO', f'✅ Process started with PID: {self.process.pid}')
            return True
            
        except Exception as e:
            self.logger.log('ERROR', f'❌ Failed to start process: {e}')
            return False
    
    def _should_restart(self) -> Tuple[bool, str]:
        """Determine if we should restart the process"""
        
        # Check 1: Is the process running?
        if not self._is_process_running():
            return True, "Process not running"
        
        # Check 2: Is the heartbeat fresh? (Most accurate indicator)
        hb_fresh, hb_age, hb_data = self._is_heartbeat_fresh()
        if not hb_fresh:
            return True, f"Heartbeat stale ({hb_age:.0f}s old)"
        
        # Check 3: Is the state file being updated?
        fresh, age = self._is_state_fresh()
        if not fresh:
            return True, f"State file stale ({age:.0f}s old)"
        
        # Check 4: Are there profitable positions not being closed?
        profitable = self._check_profitable_positions()
        if profitable['count'] >= 3 and profitable['total_profit'] > 0.50:
            # Multiple profitable positions sitting - system not acting
            return True, f"{profitable['count']} profitable positions not being harvested (${profitable['total_profit']:.2f})"
        
        return False, "System healthy"
    
    def _can_restart(self) -> bool:
        """Check if we're allowed to restart (cooldown and max attempts)"""
        # Check max attempts
        if self.restart_count >= WATCHDOG_CONFIG['MAX_RESTART_ATTEMPTS']:
            self.logger.log('ERROR', f'❌ Max restart attempts ({WATCHDOG_CONFIG["MAX_RESTART_ATTEMPTS"]}) reached. Manual intervention required.')
            return False
        
        # Check cooldown
        cooldown = WATCHDOG_CONFIG['RESTART_COOLDOWN_SEC']
        time_since_restart = time.time() - self.last_restart
        if time_since_restart < cooldown:
            self.logger.log('INFO', f'⏳ Restart cooldown: {cooldown - time_since_restart:.0f}s remaining')
            return False
        
        return True
    
    def _emergency_harvest(self):
        """Try to harvest profitable positions before restart"""
        try:
            self.logger.log('INFO', '💰 Attempting emergency harvest before restart...')
            
            if self.dry_run:
                self.logger.log('INFO', '🔧 [DRY RUN] Would run emergency_harvest.py')
                return
            
            # Run the emergency harvester
            result = subprocess.run(
                ['python3', 'emergency_harvest.py'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                self.logger.log('INFO', '✅ Emergency harvest completed')
            else:
                self.logger.log('WARN', f'⚠️ Emergency harvest failed: {result.stderr}')
                
        except Exception as e:
            self.logger.log('WARN', f'⚠️ Emergency harvest error: {e}')
    
    def run(self):
        """Main watchdog loop"""
        self.logger.log('INFO', '=' * 60)
        self.logger.log('INFO', f'🐕 AUREON WATCHDOG STARTED')
        self.logger.log('INFO', f'   Target: {self.script}')
        self.logger.log('INFO', f'   State: {self.state_file}')
        self.logger.log('INFO', f'   Mode: {"DRY RUN" if self.dry_run else "LIVE"}')
        self.logger.log('INFO', '=' * 60)
        
        # Initial start
        if not self.dry_run:
            self._start_process()
        
        check_interval = WATCHDOG_CONFIG['CHECK_INTERVAL_SEC']
        
        while self.running:
            try:
                time.sleep(check_interval)
                
                should_restart, reason = self._should_restart()
                
                if should_restart:
                    self.logger.log('WARN', f'⚠️ RESTART NEEDED: {reason}')
                    
                    if self._can_restart():
                        # Kill existing process if running
                        if self.process and self.process.poll() is None:
                            self.logger.log('INFO', '🛑 Terminating stale process...')
                            self.process.terminate()
                            try:
                                self.process.wait(timeout=10)
                            except subprocess.TimeoutExpired:
                                self.process.kill()
                        
                        # Emergency harvest first
                        self._emergency_harvest()
                        
                        # Restart
                        if self._start_process():
                            self.logger.log('INFO', f'✅ Restart #{self.restart_count} successful')
                        else:
                            self.logger.log('ERROR', f'❌ Restart #{self.restart_count} failed')
                else:
                    # All good - periodic status
                    pos_count = self._get_position_count()
                    fresh, age = self._is_state_fresh()
                    self.logger.log('DEBUG', f'💚 System healthy | Positions: {pos_count} | State age: {age:.0f}s')
                    
                    # Reset restart count on sustained health
                    if self.restart_count > 0 and age < 60:
                        self.restart_count = max(0, self.restart_count - 1)
                
            except Exception as e:
                self.logger.log('ERROR', f'❌ Watchdog error: {e}')
                time.sleep(5)
        
        self.logger.log('INFO', '🐕 AUREON WATCHDOG STOPPED')


def main():
    parser = argparse.ArgumentParser(
        description='🐕 Aureon Watchdog - External Process Supervisor'
    )
    parser.add_argument(
        '--target', '-t',
        choices=['unified', 'kraken'],
        default='unified',
        help='Which ecosystem to monitor (default: unified)'
    )
    parser.add_argument(
        '--dry-run', '-d',
        action='store_true',
        help='Monitor only, do not restart'
    )
    
    args = parser.parse_args()
    
    watchdog = AureonWatchdog(target=args.target, dry_run=args.dry_run)
    watchdog.run()


if __name__ == '__main__':
    main()
