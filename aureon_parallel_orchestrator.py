#!/usr/bin/env python3
"""
🌐🧠 AUREON PARALLEL ORCHESTRATOR - ALL SYSTEMS UNIFIED 🧠🌐
═══════════════════════════════════════════════════════════════════════════════

Master launcher that starts ALL intelligence systems in parallel, feeding the
Queen Hive Mind with validated data in real-time for optimal decision making.

ARCHITECTURE:
    ┌─────────────────────────────────────────────────────────────────────┐
    │                     👑 QUEEN HIVE MIND 👑                           │
    │                  (Central Consciousness / Sero)                     │
    └───────────────────────────────┬─────────────────────────────────────┘
                                    │
    ┌───────────────────────────────┴─────────────────────────────────────┐
    │                       📡 THOUGHT BUS 📡                             │
    │                   (Central Nervous System)                          │
    └───────────────────────────────┬─────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────────┐   ┌───────────────────┐   ┌───────────────────┐
│   📊 SCANNERS     │   │   🔮 VALIDATORS   │   │   🧠 COGNITION    │
│                   │   │                   │   │                   │
│ • Global Wave     │   │ • Probability     │   │ • Miner Brain     │
│ • Unified Eco     │   │   Nexus           │   │ • Mycelium Net    │
│ • Real Data Hub   │   │ • Timeline Oracle │   │ • Ultimate Intel  │
│ • Alpaca Bridge   │   │ • Quantum Mirror  │   │ • Elephant Memory │
└───────────────────┘   └───────────────────┘   └───────────────────┘
        │                           │                           │
        └───────────────────────────┼───────────────────────────┘
                                    │
                                    ▼
                        ┌───────────────────┐
                        │  🦈 ORCA KILL     │
                        │     CYCLE         │
                        │  (Execution)      │
                        └───────────────────┘

STARTUP SEQUENCE:
    1. ThoughtBus (central nervous system)
    2. Queen Hive Mind (central consciousness)
    3. Data Feeds (scanners)
    4. Validation Systems
    5. Cognition Systems
    6. Orca Kill Cycle (execution)

Gary Leckey | Parallel Intelligence | January 2026
═══════════════════════════════════════════════════════════════════════════════
"""

import sys
import os

# Windows UTF-8 fix (MANDATORY at top of every .py file)
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        def _is_utf8_wrapper(stream):
            """Check if stream is already a UTF-8 TextIOWrapper."""
            return (isinstance(stream, io.TextIOWrapper) and 
                    hasattr(stream, 'encoding') and stream.encoding and
                    stream.encoding.lower().replace('-', '') == 'utf8')
        def _is_buffer_valid(stream):
            """Check if stream buffer is valid and not closed."""
            if not hasattr(stream, 'buffer'):
                return False
            try:
                return stream.buffer is not None and not stream.buffer.closed
            except (ValueError, AttributeError):
                return False
        if _is_buffer_valid(sys.stdout) and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        if _is_buffer_valid(sys.stderr) and not _is_utf8_wrapper(sys.stderr):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

import asyncio
import signal
import time
import threading
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(name)s | %(message)s')
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM STATUS TRACKING
# ═══════════════════════════════════════════════════════════════════════════════

class SystemStatus(Enum):
    """Status of a parallel subsystem."""
    NOT_STARTED = "not_started"
    STARTING = "starting"
    RUNNING = "running"
    WARMING_UP = "warming_up"
    READY = "ready"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class SubsystemState:
    """State tracking for a parallel subsystem."""
    name: str
    status: SystemStatus = SystemStatus.NOT_STARTED
    started_at: Optional[float] = None
    last_heartbeat: Optional[float] = None
    error_message: Optional[str] = None
    thought_count: int = 0
    instance: Any = None
    task: Optional[asyncio.Task] = None
    thread: Optional[threading.Thread] = None
    
    @property
    def uptime_seconds(self) -> float:
        if self.started_at:
            return time.time() - self.started_at
        return 0.0
    
    @property
    def is_healthy(self) -> bool:
        if self.status not in [SystemStatus.RUNNING, SystemStatus.READY, SystemStatus.WARMING_UP]:
            return False
        if self.last_heartbeat:
            return (time.time() - self.last_heartbeat) < 60.0  # 60s timeout
        return True


# ═══════════════════════════════════════════════════════════════════════════════
# PARALLEL ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════════════

class ParallelOrchestrator:
    """
    Master orchestrator that starts and coordinates all parallel intelligence systems.
    
    Ensures all systems are running and feeding the Queen validated data before
    the Orca Kill Cycle begins execution.
    """
    
    # Warm-up time before execution systems start (seconds)
    WARMUP_SECONDS = 15.0
    
    # System categories and their priority (lower = starts first)
    SYSTEM_PRIORITY = {
        'thought_bus': 1,
        'queen': 2,
        'memory_core': 3,
        'probability_nexus': 4,
        'global_wave_scanner': 5,
        'miner_brain': 6,
        'mycelium': 7,
        'timeline_oracle': 8,
        'quantum_mirror': 9,
        'whale_sonar': 10,
        'avalanche': 11,
    }
    
    def __init__(self):
        self.systems: Dict[str, SubsystemState] = {}
        self.thought_bus = None
        self.queen = None
        self.executor = ThreadPoolExecutor(max_workers=20, thread_name_prefix="aureon_parallel_")
        self._shutdown_event = threading.Event()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._startup_complete = threading.Event()
        
        # Initialize system states
        for name in self.SYSTEM_PRIORITY.keys():
            self.systems[name] = SubsystemState(name=name)
        
        # Register signal handlers
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """Setup graceful shutdown on SIGINT/SIGTERM."""
        def _signal_handler(signum, frame):
            logger.info(f"🛑 Received signal {signum}, initiating graceful shutdown...")
            self.shutdown()
        
        try:
            signal.signal(signal.SIGINT, _signal_handler)
            signal.signal(signal.SIGTERM, _signal_handler)
        except Exception:
            pass  # May fail in some environments
    
    # ═══════════════════════════════════════════════════════════════════════════
    # INDIVIDUAL SYSTEM STARTERS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _start_thought_bus(self) -> bool:
        """Start the ThoughtBus (central nervous system)."""
        state = self.systems['thought_bus']
        state.status = SystemStatus.STARTING
        state.started_at = time.time()
        
        try:
            from aureon_thought_bus import get_thought_bus, ThoughtBus
            self.thought_bus = get_thought_bus()
            state.instance = self.thought_bus
            state.status = SystemStatus.RUNNING
            state.last_heartbeat = time.time()
            logger.info("✅ ThoughtBus: ONLINE (Central Nervous System)")
            return True
        except Exception as e:
            state.status = SystemStatus.ERROR
            state.error_message = str(e)
            logger.error(f"❌ ThoughtBus failed: {e}")
            return False
    
    def _start_queen(self) -> bool:
        """Start the Queen Hive Mind (central consciousness)."""
        state = self.systems['queen']
        state.status = SystemStatus.STARTING
        state.started_at = time.time()
        
        try:
            from aureon_queen_hive_mind import get_queen, QueenHiveMind
            self.queen = get_queen()
            state.instance = self.queen
            state.status = SystemStatus.RUNNING
            state.last_heartbeat = time.time()
            
            # Subscribe Queen to shutdown signal
            if self.thought_bus:
                self.thought_bus.subscribe('system.shutdown', self._on_shutdown_thought)
            
            logger.info("✅ Queen Hive Mind: AWAKENED (Sero Online)")
            return True
        except Exception as e:
            state.status = SystemStatus.ERROR
            state.error_message = str(e)
            logger.error(f"❌ Queen failed: {e}")
            return False
    
    def _start_memory_core(self) -> bool:
        """Start the Memory Core (persistent memory)."""
        state = self.systems['memory_core']
        state.status = SystemStatus.STARTING
        state.started_at = time.time()
        
        try:
            from aureon_memory_core import spiral_memory
            state.instance = spiral_memory
            state.status = SystemStatus.RUNNING
            state.last_heartbeat = time.time()
            logger.info("✅ Memory Core: LOADED (Spiral Memory)")
            return True
        except Exception as e:
            state.status = SystemStatus.ERROR
            state.error_message = str(e)
            logger.warning(f"⚠️ Memory Core: {e}")
            return False
    
    def _start_probability_nexus(self) -> bool:
        """Start the Probability Nexus (validation system)."""
        state = self.systems['probability_nexus']
        state.status = SystemStatus.STARTING
        state.started_at = time.time()
        
        try:
            from aureon_probability_nexus import ProbabilityNexus, get_nexus
            nexus = get_nexus()
            state.instance = nexus
            state.status = SystemStatus.WARMING_UP
            state.last_heartbeat = time.time()
            
            # Start continuous scanning in background
            if hasattr(nexus, 'start_background_scan'):
                state.thread = threading.Thread(
                    target=nexus.start_background_scan,
                    name="probability_nexus_scan",
                    daemon=True
                )
                state.thread.start()
            
            logger.info("✅ Probability Nexus: SCANNING (9-Factor Validation)")
            return True
        except ImportError:
            state.status = SystemStatus.ERROR
            state.error_message = "Module not found"
            logger.warning("⚠️ Probability Nexus: Module not available")
            return False
        except Exception as e:
            state.status = SystemStatus.ERROR
            state.error_message = str(e)
            logger.warning(f"⚠️ Probability Nexus: {e}")
            return False
    
    def _start_global_wave_scanner(self) -> bool:
        """Start the Global Wave Scanner (A-Z market sweeps)."""
        state = self.systems['global_wave_scanner']
        state.status = SystemStatus.STARTING
        state.started_at = time.time()
        
        try:
            from aureon_global_wave_scanner import GlobalWaveScanner, get_global_scanner
            scanner = get_global_scanner()
            state.instance = scanner
            state.status = SystemStatus.WARMING_UP
            state.last_heartbeat = time.time()
            
            # Start continuous scanning in background thread
            if hasattr(scanner, 'start_background_sweep'):
                state.thread = threading.Thread(
                    target=scanner.start_background_sweep,
                    name="global_wave_scanner",
                    daemon=True
                )
                state.thread.start()
            
            logger.info("✅ Global Wave Scanner: SWEEPING (A-Z Coverage)")
            return True
        except ImportError:
            state.status = SystemStatus.ERROR
            state.error_message = "Module not found"
            logger.warning("⚠️ Global Wave Scanner: Module not available")
            return False
        except Exception as e:
            state.status = SystemStatus.ERROR
            state.error_message = str(e)
            logger.warning(f"⚠️ Global Wave Scanner: {e}")
            return False
    
    def _start_miner_brain(self) -> bool:
        """Start the Miner Brain (critical thinking engine)."""
        state = self.systems['miner_brain']
        state.status = SystemStatus.STARTING
        state.started_at = time.time()
        
        try:
            from aureon_miner_brain import MinerBrain, get_miner_brain
            brain = get_miner_brain()
            state.instance = brain
            state.status = SystemStatus.RUNNING
            state.last_heartbeat = time.time()
            logger.info("✅ Miner Brain: THINKING (Critical Analysis)")
            return True
        except ImportError:
            state.status = SystemStatus.ERROR
            state.error_message = "Module not found"
            logger.warning("⚠️ Miner Brain: Module not available")
            return False
        except Exception as e:
            state.status = SystemStatus.ERROR
            state.error_message = str(e)
            logger.warning(f"⚠️ Miner Brain: {e}")
            return False
    
    def _start_mycelium(self) -> bool:
        """Start the Mycelium Network (distributed intelligence)."""
        state = self.systems['mycelium']
        state.status = SystemStatus.STARTING
        state.started_at = time.time()
        
        try:
            from aureon_mycelium import MyceliumNetwork, get_mycelium
            network = get_mycelium()
            state.instance = network
            state.status = SystemStatus.RUNNING
            state.last_heartbeat = time.time()
            logger.info("✅ Mycelium Network: CONNECTED (Distributed Intelligence)")
            return True
        except ImportError:
            state.status = SystemStatus.ERROR
            state.error_message = "Module not found"
            logger.warning("⚠️ Mycelium Network: Module not available")
            return False
        except Exception as e:
            state.status = SystemStatus.ERROR
            state.error_message = str(e)
            logger.warning(f"⚠️ Mycelium: {e}")
            return False
    
    def _start_timeline_oracle(self) -> bool:
        """Start the Timeline Oracle (7-day predictions)."""
        state = self.systems['timeline_oracle']
        state.status = SystemStatus.STARTING
        state.started_at = time.time()
        
        try:
            from aureon_timeline_oracle import TimelineOracle, get_timeline_oracle
            oracle = get_timeline_oracle()
            state.instance = oracle
            state.status = SystemStatus.RUNNING
            state.last_heartbeat = time.time()
            logger.info("✅ Timeline Oracle: PROPHESYING (7-Day Vision)")
            return True
        except ImportError:
            state.status = SystemStatus.ERROR
            state.error_message = "Module not found"
            logger.warning("⚠️ Timeline Oracle: Module not available")
            return False
        except Exception as e:
            state.status = SystemStatus.ERROR
            state.error_message = str(e)
            logger.warning(f"⚠️ Timeline Oracle: {e}")
            return False
    
    def _start_quantum_mirror(self) -> bool:
        """Start the Quantum Mirror Scanner (reality branch coherence)."""
        state = self.systems['quantum_mirror']
        state.status = SystemStatus.STARTING
        state.started_at = time.time()
        
        try:
            from aureon_quantum_mirror_scanner import QuantumMirrorScanner, create_quantum_scanner
            scanner = create_quantum_scanner()
            state.instance = scanner
            state.status = SystemStatus.RUNNING
            state.last_heartbeat = time.time()
            logger.info("✅ Quantum Mirror: REFLECTING (Branch Coherence)")
            return True
        except ImportError:
            state.status = SystemStatus.ERROR
            state.error_message = "Module not found"
            logger.warning("⚠️ Quantum Mirror: Module not available")
            return False
        except Exception as e:
            state.status = SystemStatus.ERROR
            state.error_message = str(e)
            logger.warning(f"⚠️ Quantum Mirror: {e}")
            return False
    
    def _start_whale_sonar(self) -> bool:
        """Start the Whale Sonar (subsystem health monitoring)."""
        state = self.systems['whale_sonar']
        state.status = SystemStatus.STARTING
        state.started_at = time.time()
        
        try:
            from mycelium_whale_sonar import create_and_start_sonar
            sonar = create_and_start_sonar()
            state.instance = sonar
            state.status = SystemStatus.RUNNING
            state.last_heartbeat = time.time()
            logger.info("✅ Whale Sonar: LISTENING (Subsystem Health)")
            return True
        except ImportError:
            state.status = SystemStatus.ERROR
            state.error_message = "Module not found"
            logger.warning("⚠️ Whale Sonar: Module not available")
            return False
        except Exception as e:
            state.status = SystemStatus.ERROR
            state.error_message = str(e)
            logger.warning(f"⚠️ Whale Sonar: {e}")
            return False
    
    def _start_avalanche(self) -> bool:
        """Start the Avalanche Harvester (continuous profit scraping)."""
        state = self.systems['avalanche']
        state.status = SystemStatus.STARTING
        state.started_at = time.time()
        
        try:
            from aureon_avalanche_harvester import AvalancheHarvester
            harvester = AvalancheHarvester(
                min_profit_pct=0.5,
                harvest_pct=30.0,
                scan_interval=30.0
            )
            state.instance = harvester
            state.status = SystemStatus.RUNNING
            state.last_heartbeat = time.time()
            logger.info("✅ Avalanche Harvester: ACTIVE (Profit Scraping)")
            return True
        except ImportError:
            state.status = SystemStatus.ERROR
            state.error_message = "Module not found"
            logger.warning("⚠️ Avalanche Harvester: Module not available")
            return False
        except Exception as e:
            state.status = SystemStatus.ERROR
            state.error_message = str(e)
            logger.warning(f"⚠️ Avalanche: {e}")
            return False
    
    # ═══════════════════════════════════════════════════════════════════════════
    # ORCHESTRATION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def start_all_systems(self, skip_warmup: bool = False) -> Dict[str, bool]:
        """
        Start all parallel intelligence systems in priority order.
        
        Args:
            skip_warmup: If True, skip the warm-up period before marking ready
        
        Returns:
            Dict of system name -> success boolean
        """
        logger.info("")
        logger.info("🌐" * 30)
        logger.info("  🧠 AUREON PARALLEL ORCHESTRATOR - STARTING ALL SYSTEMS 🧠")
        logger.info("🌐" * 30)
        logger.info("")
        
        results = {}
        
        # Start systems in priority order
        starters = [
            ('thought_bus', self._start_thought_bus),
            ('queen', self._start_queen),
            ('memory_core', self._start_memory_core),
            ('probability_nexus', self._start_probability_nexus),
            ('global_wave_scanner', self._start_global_wave_scanner),
            ('miner_brain', self._start_miner_brain),
            ('mycelium', self._start_mycelium),
            ('timeline_oracle', self._start_timeline_oracle),
            ('quantum_mirror', self._start_quantum_mirror),
            ('whale_sonar', self._start_whale_sonar),
            ('avalanche', self._start_avalanche),
        ]
        
        for name, starter_fn in starters:
            try:
                results[name] = starter_fn()
            except Exception as e:
                logger.error(f"❌ Critical error starting {name}: {e}")
                results[name] = False
                self.systems[name].status = SystemStatus.ERROR
                self.systems[name].error_message = str(e)
        
        # Warm-up period
        if not skip_warmup:
            logger.info("")
            logger.info(f"⏳ Warming up systems ({self.WARMUP_SECONDS}s)...")
            time.sleep(self.WARMUP_SECONDS)
        
        # Mark startup complete
        self._startup_complete.set()
        
        # Print status summary
        self._print_status_summary()
        
        return results
    
    def _print_status_summary(self):
        """Print a summary of all system statuses."""
        logger.info("")
        logger.info("=" * 60)
        logger.info("  📊 PARALLEL SYSTEMS STATUS")
        logger.info("=" * 60)
        
        healthy_count = 0
        total_count = len(self.systems)
        
        for name, state in sorted(self.systems.items(), key=lambda x: self.SYSTEM_PRIORITY.get(x[0], 99)):
            status_icon = {
                SystemStatus.NOT_STARTED: "⬜",
                SystemStatus.STARTING: "🔄",
                SystemStatus.RUNNING: "🟢",
                SystemStatus.WARMING_UP: "🟡",
                SystemStatus.READY: "✅",
                SystemStatus.ERROR: "🔴",
                SystemStatus.STOPPED: "⬛",
            }.get(state.status, "❓")
            
            if state.is_healthy:
                healthy_count += 1
            
            uptime_str = f"{state.uptime_seconds:.1f}s" if state.started_at else "N/A"
            error_str = f" ({state.error_message})" if state.error_message else ""
            
            logger.info(f"  {status_icon} {name:20s} | {state.status.value:15s} | {uptime_str}{error_str}")
        
        logger.info("=" * 60)
        logger.info(f"  HEALTHY: {healthy_count}/{total_count} systems")
        logger.info("=" * 60)
        logger.info("")
    
    def get_system(self, name: str) -> Optional[Any]:
        """Get a running system instance by name."""
        state = self.systems.get(name)
        if state and state.instance:
            return state.instance
        return None
    
    def get_queen(self):
        """Get the Queen Hive Mind instance."""
        return self.queen
    
    def get_thought_bus(self):
        """Get the ThoughtBus instance."""
        return self.thought_bus
    
    def is_ready(self) -> bool:
        """Check if all critical systems are running."""
        critical_systems = ['thought_bus', 'queen']
        for name in critical_systems:
            state = self.systems.get(name)
            if not state or not state.is_healthy:
                return False
        return self._startup_complete.is_set()
    
    def wait_for_ready(self, timeout: float = 60.0) -> bool:
        """Wait for all systems to be ready."""
        return self._startup_complete.wait(timeout=timeout)
    
    def heartbeat(self, system_name: str):
        """Update heartbeat for a system."""
        state = self.systems.get(system_name)
        if state:
            state.last_heartbeat = time.time()
            state.thought_count += 1
    
    def _on_shutdown_thought(self, thought):
        """Handle shutdown signal from ThoughtBus."""
        logger.info("📡 Received shutdown thought, initiating graceful shutdown...")
        self.shutdown()
    
    def shutdown(self):
        """Gracefully shutdown all systems."""
        logger.info("")
        logger.info("🛑 INITIATING GRACEFUL SHUTDOWN...")
        self._shutdown_event.set()
        
        # Broadcast shutdown signal
        if self.thought_bus:
            try:
                self.thought_bus.publish('system.shutdown', {
                    'timestamp': time.time(),
                    'reason': 'orchestrator_shutdown'
                })
            except Exception:
                pass
        
        # Stop all systems
        for name, state in self.systems.items():
            if state.status in [SystemStatus.RUNNING, SystemStatus.WARMING_UP, SystemStatus.READY]:
                logger.info(f"  🛑 Stopping {name}...")
                state.status = SystemStatus.STOPPED
                
                # Cancel async tasks
                if state.task and not state.task.done():
                    state.task.cancel()
                
                # Stop instance if it has a stop method
                if state.instance and hasattr(state.instance, 'stop'):
                    try:
                        state.instance.stop()
                    except Exception as e:
                        logger.warning(f"  ⚠️ Error stopping {name}: {e}")
        
        # Shutdown executor
        self.executor.shutdown(wait=False)
        
        logger.info("✅ All systems stopped")
    
    def get_intelligence_snapshot(self) -> Dict[str, Any]:
        """
        Get a snapshot of all intelligence feeds for Orca consumption.
        
        Returns a dict with latest data from each running intelligence system.
        """
        snapshot = {
            'timestamp': time.time(),
            'systems_healthy': sum(1 for s in self.systems.values() if s.is_healthy),
            'systems_total': len(self.systems),
            'data': {}
        }
        
        # Probability Nexus
        nexus = self.get_system('probability_nexus')
        if nexus and hasattr(nexus, 'get_latest_predictions'):
            try:
                snapshot['data']['probability_nexus'] = nexus.get_latest_predictions()
            except Exception:
                pass
        
        # Global Wave Scanner
        scanner = self.get_system('global_wave_scanner')
        if scanner and hasattr(scanner, 'get_latest_opportunities'):
            try:
                snapshot['data']['global_wave_scanner'] = scanner.get_latest_opportunities()
            except Exception:
                pass
        
        # Miner Brain
        brain = self.get_system('miner_brain')
        if brain and hasattr(brain, 'get_latest_analysis'):
            try:
                snapshot['data']['miner_brain'] = brain.get_latest_analysis()
            except Exception:
                pass
        
        # Timeline Oracle
        oracle = self.get_system('timeline_oracle')
        if oracle and hasattr(oracle, 'get_active_timelines'):
            try:
                snapshot['data']['timeline_oracle'] = oracle.get_active_timelines()
            except Exception:
                pass
        
        # Quantum Mirror
        mirror = self.get_system('quantum_mirror')
        if mirror and hasattr(mirror, 'get_branch_coherence'):
            try:
                snapshot['data']['quantum_mirror'] = mirror.get_branch_coherence()
            except Exception:
                pass
        
        # Mycelium
        mycelium = self.get_system('mycelium')
        if mycelium and hasattr(mycelium, 'get_network_state'):
            try:
                snapshot['data']['mycelium'] = mycelium.get_network_state()
            except Exception:
                pass
        
        return snapshot


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ═══════════════════════════════════════════════════════════════════════════════

_orchestrator: Optional[ParallelOrchestrator] = None

def get_orchestrator() -> ParallelOrchestrator:
    """Get or create the singleton orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ParallelOrchestrator()
    return _orchestrator


def get_parallel_orchestrator() -> ParallelOrchestrator:
    """Backward-compatible alias used by older modules."""
    return get_orchestrator()


def start_all_parallel_systems(skip_warmup: bool = False) -> Dict[str, bool]:
    """
    Convenience function to start all parallel systems.
    
    Call this before starting the Orca Kill Cycle to ensure all intelligence
    feeds are running and warming up.
    """
    orchestrator = get_orchestrator()
    return orchestrator.start_all_systems(skip_warmup=skip_warmup)


def shutdown_all_systems():
    """Gracefully shutdown all parallel systems."""
    global _orchestrator
    if _orchestrator:
        _orchestrator.shutdown()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   🌐🧠 AUREON PARALLEL ORCHESTRATOR 🧠🌐                                       ║
║                                                                               ║
║   Starting ALL intelligence systems in parallel...                           ║
║                                                                               ║
║   Systems:                                                                    ║
║   • ThoughtBus (Central Nervous System)                                      ║
║   • Queen Hive Mind (Central Consciousness)                                  ║
║   • Probability Nexus (9-Factor Validation)                                  ║
║   • Global Wave Scanner (A-Z Market Coverage)                                ║
║   • Miner Brain (Critical Thinking)                                          ║
║   • Mycelium Network (Distributed Intelligence)                              ║
║   • Timeline Oracle (7-Day Predictions)                                      ║
║   • Quantum Mirror (Branch Coherence)                                        ║
║   • Whale Sonar (Subsystem Health)                                           ║
║   • Avalanche Harvester (Profit Scraping)                                    ║
║                                                                               ║
║   Press Ctrl+C to stop all systems gracefully                                ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    orchestrator = get_orchestrator()
    results = orchestrator.start_all_systems()
    
    # Keep running until shutdown
    try:
        while not orchestrator._shutdown_event.is_set():
            time.sleep(1.0)
    except KeyboardInterrupt:
        pass
    
    orchestrator.shutdown()
