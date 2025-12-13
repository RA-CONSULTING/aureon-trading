"""
🌍 AUREON GLOBAL ORCHESTRATOR 🌍

Single unified startup and control point for:
- Quantum Processing Brain
- Harmonic Mining Optimizer  
- Aureon Kraken Unified Ecosystem (Trading)

ONE SWITCH TO RULE THEM ALL! 🎚️
"""

import os
import sys
import time
import logging
import threading
import io
from typing import Optional, Dict
from threading import Thread, Event

# ✅ FIX: Ensure UTF-8 encoding for stream output (Windows compatibility)
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except:
        pass

# Configure logger with UTF-8/ASCII-safe handling
logger = logging.getLogger("AureonOrchestrator")
logger.setLevel(logging.INFO)
if not logger.handlers:
    class SafeUTF8Formatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            msg = super().format(record)
            try:
                _ = msg.encode('utf-8')
                return msg
            except Exception:
                return msg.encode('utf-8', errors='replace').decode('ascii', errors='replace')

    handler = logging.StreamHandler(sys.stdout)
    formatter = SafeUTF8Formatter('[%(asctime)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class GlobalAureonOrchestrator:
    """
    Master orchestrator for all Aureon subsystems.
    
    Architecture:
    1. Brain is initialized FIRST (global state broadcast)
    2. Miner bootstrap runs (reads latest brain state)
    3. Ecosystem loads (links to miner Lighthouse)
    4. Trading loop and mining loop run synchronized
    
    One master on/off switch controls all three.
    """
    
    def __init__(self, initial_balance_gbp: float = 1000.0, dry_run: bool = False):
        """Initialize the complete Aureon ecosystem."""
        self.initial_balance = initial_balance_gbp
        self.dry_run = dry_run
        
        # Subsystem references
        self.brain = None
        self.miner_optimizer = None
        self.ecosystem = None
        
        # Thread control
        self.running = Event()
        self.miner_thread = None
        self.ecosystem_thread = None
        
        # Health tracking
        self.system_health = {
            'brain': 'IDLE',
            'miner': 'IDLE',
            'ecosystem': 'IDLE',
            'startup_time': None,
            'cycles': 0
        }
    
    def initialize_brain(self):
        """Step 1: Initialize the Quantum Processing Brain (global state)."""
        logger.info("🧠 Initializing Quantum Processing Brain...")
        try:
            from aureon_miner import QuantumProcessingBrain
            self.brain = QuantumProcessingBrain()
            # Bootstrap brain state
            self.brain.compute_with_ecosystem()
            self.brain.broadcast_state()
            self.system_health['brain'] = 'ACTIVE'
            logger.info("✅ 🧠 Brain ACTIVE - Broadcasting state to ecosystem")
            return True
        except Exception as e:
            logger.error(f"❌ Brain initialization failed: {e}")
            self.system_health['brain'] = 'ERROR'
            return False
    
    def initialize_miner(self):
        """Step 2: Initialize Harmonic Mining Optimizer (reads brain state)."""
        logger.info("⛏️  Initializing Harmonic Mining Optimizer...")
        try:
            from aureon_miner import HarmonicMiningOptimizer
            self.miner_optimizer = HarmonicMiningOptimizer()
            # Miner bootstrap sync will read latest brain state
            self.system_health['miner'] = 'ACTIVE'
            logger.info("✅ ⛏️  Miner ACTIVE - Lighthouse locked on to Γ(t)")
            return True
        except Exception as e:
            logger.error(f"❌ Miner initialization failed: {e}")
            self.system_health['miner'] = 'ERROR'
            return False
    
    def initialize_ecosystem(self):
        """Step 3: Initialize Trading Ecosystem (links to miner)."""
        logger.info("🐙 Initializing Aureon Kraken Unified Ecosystem...")
        try:
            from aureon_unified_ecosystem import AureonKrakenEcosystem
            self.ecosystem = AureonKrakenEcosystem(
                initial_balance=self.initial_balance,
                dry_run=self.dry_run
            )
            # LINK MINER TO ECOSYSTEM
            # This allows ecosystem to read Lighthouse Γ during trading decisions
            self.ecosystem.miner_optimizer = self.miner_optimizer
            self.ecosystem.brain = self.brain
            
            self.system_health['ecosystem'] = 'ACTIVE'
            logger.info("✅ 🐙 Ecosystem ACTIVE - Linked to Miner & Brain")
            return True
        except Exception as e:
            logger.error(f"❌ Ecosystem initialization failed: {e}")
            self.system_health['ecosystem'] = 'ERROR'
            return False
    
    def startup_sequence(self) -> bool:
        """Execute the three-phase startup sequence."""
        logger.info("\n" + "="*70)
        logger.info("🌍 AUREON GLOBAL ORCHESTRATOR - STARTUP SEQUENCE 🌍")
        logger.info("="*70)
        
        self.system_health['startup_time'] = time.time()
        
        # Phase 1: Brain
        if not self.initialize_brain():
            return False
        time.sleep(0.5)
        
        # Phase 2: Miner
        if not self.initialize_miner():
            return False
        time.sleep(0.5)
        
        # Phase 3: Ecosystem
        if not self.initialize_ecosystem():
            return False
        
        logger.info("\n" + "="*70)
        logger.info("✅ ALL SYSTEMS INITIALIZED AND SYNCHRONIZED")
        logger.info("="*70 + "\n")
        
        return True
    
    def print_unified_status(self):
        """Print unified health report for all systems."""
        print("\n" + "="*70)
        print("🌍 UNIFIED SYSTEM STATUS")
        print("="*70)
        print(f"  🧠 Brain:       {self.system_health['brain']}")
        print(f"  ⛏️  Miner:       {self.system_health['miner']}")
        print(f"  🐙 Ecosystem:   {self.system_health['ecosystem']}")
        print(f"  📊 Cycles:      {self.system_health['cycles']}")
        if self.system_health['startup_time']:
            runtime = (time.time() - self.system_health['startup_time']) / 60
            print(f"  ⏱️  Runtime:     {runtime:.1f} minutes")
        print("="*70 + "\n")
    
    def run_mining_loop(self, mining_interval: float = 5.0):
        """Run mining in background thread (non-blocking)."""
        logger.info("🔨 Starting Mining Loop (background thread)...")
        while self.running.is_set():
            try:
                # Update miner state
                if self.miner_optimizer:
                    self.miner_optimizer.update_state()
                    self.miner_optimizer.update_probability_signal()
                    self.miner_optimizer.apply_adaptive_learning_feedback()
                    self.miner_optimizer.update_brain()
                    
                    # Every 10 cycles, log miner status
                    if self.system_health['cycles'] % 10 == 0:
                        insight = self.miner_optimizer.get_mining_insight()
                        gamma = insight.get('platypus_gamma', 0.5)
                        cascade = insight.get('cascade_factor', 1.0)
                        kappa = insight.get('coherence_kappa', 1.0)
                        logger.info(f"⛏️  Miner: Γ={gamma:.2f} | CASCADE={cascade:.1f}x | κ={kappa:.2f}x")
                
                time.sleep(mining_interval)
            except Exception as e:
                logger.error(f"Mining loop error: {e}")
                time.sleep(1)
    
    def run_ecosystem_loop(self, ecosystem_interval: float = 2.0):
        """Run trading ecosystem in main thread."""
        logger.info("🐙 Starting Trading Ecosystem Loop (main thread)...")
        try:
            self.ecosystem.run(interval=ecosystem_interval)
        except KeyboardInterrupt:
            logger.info("⏹️  Trading loop interrupted")
            self.stop()
        except Exception as e:
            logger.error(f"Ecosystem loop error: {e}")
            self.stop()
    
    def start(self):
        """
        START ALL SYSTEMS 🚀
        
        - Brain broadcasts state
        - Miner syncs to brain Γ
        - Ecosystem reads miner Lighthouse
        - All systems tick together
        """
        if not self.startup_sequence():
            logger.error("❌ Startup failed - aborting")
            return False
        
        self.running.set()
        
        # Start mining in background thread
        self.miner_thread = Thread(target=self.run_mining_loop, daemon=True)
        self.miner_thread.start()
        logger.info("✅ Mining thread started (background)")
        
        # Run ecosystem in main thread (blocks)
        self.run_ecosystem_loop()
        
        return True
    
    def stop(self):
        """STOP ALL SYSTEMS 🛑"""
        logger.info("\n🛑 Stopping all systems...")
        self.running.clear()
        
        # Stop ecosystem (if running)
        if self.ecosystem:
            try:
                self.ecosystem.tracker.trading_halted = True
                logger.info("   Ecosystem halted")
            except Exception as e:
                logger.debug(f"Ecosystem stop error: {e}")
        
        # Wait for miner thread
        if self.miner_thread and self.miner_thread.is_alive():
            self.miner_thread.join(timeout=2)
            logger.info("   Miner stopped")
        
        logger.info("✅ All systems stopped\n")
    
    def get_status(self) -> Dict:
        """Get unified status dictionary."""
        status = {
            'brain': self.system_health['brain'],
            'miner': self.system_health['miner'],
            'ecosystem': self.system_health['ecosystem'],
            'running': self.running.is_set(),
            'cycles': self.system_health['cycles'],
        }
        
        if self.miner_optimizer:
            insight = self.miner_optimizer.get_mining_insight()
            status['miner_gamma'] = insight.get('platypus_gamma', 0.5)
            status['miner_cascade'] = insight.get('cascade_factor', 1.0)
            status['miner_kappa'] = insight.get('coherence_kappa', 1.0)
        
        if self.ecosystem:
            status['portfolio_value'] = self.ecosystem.total_equity_gbp
            status['positions_open'] = len(self.ecosystem.positions)
        
        return status


def main():
    """
    Master entry point - ONE GLOBAL SWITCH! 🎚️
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Aureon Global Orchestrator')
    parser.add_argument('--balance', type=float, default=1000.0, help='Initial trading balance (GBP)')
    parser.add_argument('--dry-run', action='store_true', help='Run in dry-run mode')
    parser.add_argument('--mining-only', action='store_true', help='Run mining only (no trading)')
    parser.add_argument('--trading-only', action='store_true', help='Run trading only (no mining)')
    args = parser.parse_args()
    
    # Create global orchestrator
    orchestrator = GlobalAureonOrchestrator(
        initial_balance_gbp=args.balance,
        dry_run=args.dry_run
    )
    
    # Start all systems
    try:
        orchestrator.start()
    except KeyboardInterrupt:
        orchestrator.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        orchestrator.stop()
        sys.exit(1)


if __name__ == '__main__':
    main()
