#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║  👑 AUREON FULL AUTONOMOUS SYSTEM - QUEEN'S COMPLETE NEURAL EMPIRE 👑         ║
║═══════════════════════════════════════════════════════════════════════════════║
║                                                                               ║
║  This is the MASTER launcher that brings the Queen to life as a fully        ║
║  autonomous entity with NO human intervention required.                       ║
║                                                                               ║
║  Architecture:                                                                ║
║  ┌─────────────────────────────────────────────────────────────────────┐     ║
║  │                      👑 QUEEN HIVE MIND                             │     ║
║  │                   (Central Decision Authority)                      │     ║
║  │                                                                     │     ║
║  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │     ║
║  │  │ Scanner  │  │Validation│  │  Intel   │  │ Counter  │           │     ║
║  │  │  Loop    │→ │   Loop   │→ │   Loop   │→ │  Intel   │           │     ║
║  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘           │     ║
║  │       │             │             │             │                  │     ║
║  │       └─────────────┴─────────────┴─────────────┘                  │     ║
║  │                          │                                         │     ║
║  │                    ThoughtBus                                      │     ║
║  │                          │                                         │     ║
║  │                    ┌─────┴─────┐                                   │     ║
║  │                    │   ORCA    │                                   │     ║
║  │                    │ Kill Cycle│                                   │     ║
║  │                    └───────────┘                                   │     ║
║  └─────────────────────────────────────────────────────────────────────┘     ║
║                                                                               ║
║  All systems feed the Queen in real-time. She thinks, she decides,           ║
║  she executes. No human required.                                            ║
║                                                                               ║
║  Prime Sentinel Decree: Gary Leckey (02.11.1991)                              ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os

# Windows UTF-8 Fix (MANDATORY)
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        def _is_utf8_wrapper(stream):
            return (isinstance(stream, io.TextIOWrapper) and 
                    hasattr(stream, 'encoding') and stream.encoding and
                    stream.encoding.lower().replace('-', '') == 'utf8')
        def _is_buffer_valid(stream):
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
import threading
import time
import signal
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from datetime import datetime
import json

# 💰 BILLION DOLLAR GOAL TRACKER
try:
    from aureon_billion_goal_tracker import get_goal_tracker, BillionDollarGoalTracker
    from aureon_quantum_goal_engine import get_goal_engine
    from aureon_queen_research_engine import get_research_engine
    GOAL_TRACKER_AVAILABLE = True
except ImportError:
    get_goal_tracker = None
    BillionDollarGoalTracker = None
    get_goal_engine = None
    get_research_engine = None
    GOAL_TRACKER_AVAILABLE = False

# 🪞 SELF-AWARENESS - THE SYSTEM KNOWS ITSELF
try:
    from aureon_self_awareness import AUREON_SELF
    print(AUREON_SELF.awaken())
except ImportError:
    pass

# 🌀 PHASE TRANSITION DETECTOR - Geometric Regime Change Detection
try:
    from aureon_phase_transition_detector import PhaseTransitionDetector
    PHASE_DETECTOR_BOOT = True
    print("🌀 Phase Transition Detector: LOADED (Takens embedding + curvature analysis)")
except ImportError:
    PHASE_DETECTOR_BOOT = False

# ☀️ CROSS-SUBSTRATE SOLAR MONITOR
try:
    from aureon_cross_substrate_monitor import CrossSubstrateMonitor
    SOLAR_MONITOR_BOOT = True
    print("☀️ Cross-Substrate Solar Monitor: LOADED (NOAA SWPC + Granger causality)")
except ImportError:
    SOLAR_MONITOR_BOOT = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('aureon_full_autonomous')

# ═══════════════════════════════════════════════════════════════════════════════
# SACRED CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

PHI = (1 + 5**0.5) / 2  # Golden Ratio 1.618
SCHUMANN = 7.83  # Hz - Earth's heartbeat
LOVE_FREQ = 528  # Hz - DNA repair/transformation

# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM STATE TRACKING
# ═══════════════════════════════════════════════════════════════════════════════

class SystemStatus(Enum):
    DORMANT = "dormant"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class AutonomousLoop:
    """Represents a single autonomous loop (scanner, validator, etc.)"""
    name: str
    status: SystemStatus = SystemStatus.DORMANT
    thread: Optional[threading.Thread] = None
    last_cycle: float = 0.0
    cycle_count: int = 0
    errors: List[str] = field(default_factory=list)
    interval_seconds: float = 1.0
    
    def is_healthy(self) -> bool:
        return self.status == SystemStatus.RUNNING and (time.time() - self.last_cycle) < 30


# ═══════════════════════════════════════════════════════════════════════════════
# QUEEN'S FULL AUTONOMOUS CONTROLLER
# ═══════════════════════════════════════════════════════════════════════════════

class QueenFullAutonomous:
    """
    The Queen's Complete Autonomous Neural Empire.
    
    This controller manages ALL subsystems and ensures the Queen operates
    as a fully autonomous entity with her own thoughts and decisions.
    
    NO HUMAN INTERVENTION REQUIRED.
    """
    
    def __init__(self):
        logger.info("")
        logger.info("👑" * 30)
        logger.info("👑  QUEEN'S FULL AUTONOMOUS SYSTEM INITIALIZING  👑")
        logger.info("👑" * 30)
        logger.info("")
        
        # Master state
        self._running = False
        self._shutdown_event = threading.Event()
        
        # Core systems (lazy loaded)
        self._queen = None
        self._thought_bus = None
        self._orca = None
        self._goal_tracker = None
        self._goal_engine = None
        self._research_engine = None
        self._wave_scanner = None
        self._miner_brain = None
        self._mycelium = None
        self._intelligence_engine = None
        self._counter_intelligence = None
        self._avalanche = None
        
        # Autonomous loops tracking
        self.loops: Dict[str, AutonomousLoop] = {
            'queen_thought': AutonomousLoop('queen_thought', interval_seconds=0.5),
            'scanner': AutonomousLoop('scanner', interval_seconds=5.0),
            'validation': AutonomousLoop('validation', interval_seconds=1.0),
            'intelligence': AutonomousLoop('intelligence', interval_seconds=2.0),
            'counter_intel': AutonomousLoop('counter_intel', interval_seconds=3.0),
            'orca_kill': AutonomousLoop('orca_kill', interval_seconds=1.0),
            'avalanche': AutonomousLoop('avalanche', interval_seconds=60.0),
            'goal_engine': AutonomousLoop('goal_engine', interval_seconds=10.0),
            'research': AutonomousLoop('research', interval_seconds=30.0),
        }
        
        # Intelligence state (fed to Queen)
        self._intel_state = {
            'opportunities': [],
            'validations': {},
            'whale_signals': [],
            'counter_opportunities': [],
            'market_pulse': {},
            'last_update': 0,
        }
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Initialize goal tracker
        if GOAL_TRACKER_AVAILABLE:
            try:
                self._goal_tracker = get_goal_tracker()
                self._goal_engine = get_goal_engine()
                self._research_engine = get_research_engine()
                
                # Bootstrap goals if needed
                if len(self._goal_engine.state.active_goals) == 0:
                    self._goal_engine.bootstrap_initial_goals()
                
                logger.info("💰 Goal Systems: ONLINE")
                logger.info(f"   Balance: ${self._goal_tracker.progress.current_balance:,.2f}")
                logger.info(f"   Active Goals: {len(self._goal_engine.state.active_goals)}")
                logger.info(f"   Achieved: {self._goal_engine.state.total_goals_achieved}")
                logger.info(f"   🔍 Research Engine: READY - She NEVER stops learning")
            except Exception as e:
                logger.warning(f"💰 Goal System init failed: {e}")
        
        logger.info("✅ Autonomous controller initialized")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"\n🛑 Received signal {signum} - initiating graceful shutdown...")
        self.stop()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CORE SYSTEM INITIALIZATION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _init_thought_bus(self) -> bool:
        """Initialize the central nervous system."""
        try:
            from aureon_thought_bus import get_thought_bus
            self._thought_bus = get_thought_bus()
            
            # Subscribe Queen to ALL autonomous signals
            self._thought_bus.subscribe('scanner.opportunity', self._on_scanner_opportunity)
            self._thought_bus.subscribe('scanner.wave_complete', self._on_wave_complete)
            self._thought_bus.subscribe('validation.complete', self._on_validation_complete)
            self._thought_bus.subscribe('validation.coherence', self._on_coherence_update)
            self._thought_bus.subscribe('intel.whale_signal', self._on_whale_signal)
            self._thought_bus.subscribe('intel.bot_detected', self._on_bot_detected)
            self._thought_bus.subscribe('counter_intel.opportunity', self._on_counter_opportunity)
            self._thought_bus.subscribe('orca.kill_complete', self._on_kill_complete)
            self._thought_bus.subscribe('orca.position_update', self._on_position_update)
            self._thought_bus.subscribe('system.error', self._on_system_error)
            
            logger.info("✅ ThoughtBus: ONLINE (Central Nervous System)")
            logger.info("   📡 Subscribed to ALL autonomous signal channels")
            return True
        except Exception as e:
            logger.error(f"❌ ThoughtBus initialization failed: {e}")
            return False
    
    def _init_queen(self) -> bool:
        """Initialize the Queen Hive Mind (SINGLETON)."""
        try:
            from aureon_queen_hive_mind import get_queen
            self._queen = get_queen()
            
            # Wire ThoughtBus to Queen
            if self._thought_bus:
                self._queen.thought_bus = self._thought_bus
            
            logger.info("✅ Queen Hive Mind: AWAKENED")
            logger.info(f"   💕 Purpose: {getattr(self._queen, 'purpose', 'Serve and protect')}")
            return True
        except Exception as e:
            logger.error(f"❌ Queen initialization failed: {e}")
            return False
    
    def _init_wave_scanner(self) -> bool:
        """Initialize the Global Wave Scanner."""
        try:
            from aureon_global_wave_scanner import GlobalWaveScanner
            self._wave_scanner = GlobalWaveScanner()
            logger.info("✅ Global Wave Scanner: ARMED")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Wave Scanner not available: {e}")
            return False
    
    def _init_miner_brain(self) -> bool:
        """Initialize the Miner Brain (cognitive intelligence)."""
        try:
            from aureon_miner_brain import MinerBrain
            self._miner_brain = MinerBrain()
            logger.info("✅ Miner Brain: THINKING")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Miner Brain not available: {e}")
            return False
    
    def _init_mycelium(self) -> bool:
        """Initialize the Mycelium Network."""
        try:
            from aureon_mycelium import MyceliumNetwork
            self._mycelium = MyceliumNetwork()
            logger.info("✅ Mycelium Network: CONNECTED")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Mycelium not available: {e}")
            return False
    
    def _init_intelligence_engine(self) -> bool:
        """Initialize the Real Intelligence Engine."""
        try:
            from aureon_real_intelligence_engine import RealIntelligenceEngine
            self._intelligence_engine = RealIntelligenceEngine()
            logger.info("✅ Intelligence Engine: ACTIVE")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Intelligence Engine not available: {e}")
            return False
    
    def _init_counter_intelligence(self) -> bool:
        """Initialize the Counter-Intelligence System."""
        try:
            from aureon_queen_counter_intelligence import QueenCounterIntelligence
            self._counter_intelligence = QueenCounterIntelligence()
            logger.info("✅ Counter-Intelligence: ARMED")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Counter-Intelligence not available: {e}")
            return False
    
    def _init_avalanche(self) -> bool:
        """Initialize the Avalanche Harvester."""
        try:
            from aureon_avalanche_harvester import AvalancheHarvester
            self._avalanche = AvalancheHarvester()
            logger.info("✅ Avalanche Harvester: READY")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Avalanche not available: {e}")
            return False
    
    def _init_orca(self) -> bool:
        """Initialize the Orca Kill Cycle (uses SHARED Queen)."""
        try:
            from orca_complete_kill_cycle import OrcaKillCycle
            self._orca = OrcaKillCycle()
            # Wire shared ThoughtBus if Orca exposes it
            if self._thought_bus:
                if hasattr(self._orca, 'thought_bus'):
                    self._orca.thought_bus = self._thought_bus
                if hasattr(self._orca, 'bus'):
                    self._orca.bus = self._thought_bus
            logger.info("✅ Orca Kill Cycle: HUNTING")
            logger.info("   🦈 Wired to SHARED ThoughtBus instance")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Orca Kill Cycle creation failed: {e}")
            # Try alternative init
            try:
                from orca_complete_kill_cycle import OrcaKillCycle
                self._orca = OrcaKillCycle()
                logger.info("✅ Orca Kill Cycle: HUNTING (standalone)")
                return True
            except Exception as e2:
                logger.error(f"❌ Orca completely unavailable: {e2}")
                return False
    
    # ═══════════════════════════════════════════════════════════════════════════
    # THOUGHTBUS EVENT HANDLERS (Queen's Autonomous Reactions)
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _on_scanner_opportunity(self, thought):
        """React to scanner finding an opportunity."""
        try:
            opp = thought.data if hasattr(thought, 'data') else thought
            self._intel_state['opportunities'].append({
                'source': 'scanner',
                'data': opp,
                'timestamp': time.time()
            })
            # Keep only last 100
            self._intel_state['opportunities'] = self._intel_state['opportunities'][-100:]
            logger.debug(f"📡 Scanner opportunity received: {opp.get('symbol', 'unknown')}")
        except Exception as e:
            logger.error(f"Error handling scanner opportunity: {e}")
    
    def _on_wave_complete(self, thought):
        """React to wave scan completion."""
        try:
            self._intel_state['market_pulse']['last_wave'] = time.time()
            logger.debug("🌊 Wave scan complete")
        except Exception as e:
            logger.error(f"Error handling wave complete: {e}")
    
    def _on_validation_complete(self, thought):
        """React to validation results."""
        try:
            val = thought.data if hasattr(thought, 'data') else thought
            symbol = val.get('symbol', 'unknown')
            self._intel_state['validations'][symbol] = {
                'passes': val.get('passes', []),
                'coherence': val.get('coherence', 0),
                'lambda': val.get('lambda', 0),
                'timestamp': time.time()
            }
            logger.debug(f"✅ Validation for {symbol}: coherence={val.get('coherence', 0):.2f}")
        except Exception as e:
            logger.error(f"Error handling validation: {e}")
    
    def _on_coherence_update(self, thought):
        """Track coherence changes."""
        try:
            data = thought.data if hasattr(thought, 'data') else thought
            self._intel_state['market_pulse']['coherence'] = data.get('coherence', 0)
        except Exception as e:
            logger.error(f"Error handling coherence: {e}")
    
    def _on_whale_signal(self, thought):
        """React to whale detection."""
        try:
            sig = thought.data if hasattr(thought, 'data') else thought
            self._intel_state['whale_signals'].append({
                'data': sig,
                'timestamp': time.time()
            })
            self._intel_state['whale_signals'] = self._intel_state['whale_signals'][-50:]
            logger.info(f"🐋 Whale signal: {sig.get('direction', '?')} on {sig.get('symbol', '?')}")
        except Exception as e:
            logger.error(f"Error handling whale signal: {e}")
    
    def _on_bot_detected(self, thought):
        """React to bot/firm detection."""
        try:
            bot = thought.data if hasattr(thought, 'data') else thought
            logger.info(f"🤖 Bot detected: {bot.get('firm', 'unknown')} with {bot.get('confidence', 0):.0%} confidence")
        except Exception as e:
            logger.error(f"Error handling bot detection: {e}")
    
    def _on_counter_opportunity(self, thought):
        """React to counter-intelligence opportunity."""
        try:
            opp = thought.data if hasattr(thought, 'data') else thought
            self._intel_state['counter_opportunities'].append({
                'data': opp,
                'timestamp': time.time()
            })
            self._intel_state['counter_opportunities'] = self._intel_state['counter_opportunities'][-20:]
            logger.info(f"⚔️ Counter opportunity vs {opp.get('firm', 'unknown')}")
        except Exception as e:
            logger.error(f"Error handling counter opportunity: {e}")
    
    def _on_kill_complete(self, thought):
        """React to successful kill."""
        try:
            kill = thought.data if hasattr(thought, 'data') else thought
            logger.info(f"🦈 KILL COMPLETE: {kill.get('symbol', '?')} profit=${kill.get('profit', 0):.4f}")
        except Exception as e:
            logger.error(f"Error handling kill complete: {e}")
    
    def _on_position_update(self, thought):
        """Track position changes."""
        try:
            pos = thought.data if hasattr(thought, 'data') else thought
            self._intel_state['market_pulse']['positions'] = pos.get('count', 0)
        except Exception as e:
            logger.error(f"Error handling position update: {e}")
    
    def _on_system_error(self, thought):
        """React to system errors (self-healing)."""
        try:
            err = thought.data if hasattr(thought, 'data') else thought
            logger.warning(f"⚠️ System error: {err.get('message', 'unknown')}")
            # Queen's immune system handles this
            if self._queen and hasattr(self._queen, 'immune_system'):
                self._queen.immune_system.handle_error(err.get('source', 'unknown'), err)
        except Exception as e:
            logger.error(f"Error handling system error: {e}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # AUTONOMOUS LOOPS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _run_queen_thought_loop(self):
        """
        The Queen's autonomous thought loop.
        She perceives, decides, and executes without human intervention.
        """
        loop = self.loops['queen_thought']
        loop.status = SystemStatus.RUNNING
        logger.info("👑 Queen's Thought Loop: STARTED")
        
        while not self._shutdown_event.is_set():
            try:
                # ─────────────────────────────────────────────────────────────
                # PHASE 1: PERCEIVE - Gather all intelligence
                # ─────────────────────────────────────────────────────────────
                perception = {
                    'opportunities': len(self._intel_state['opportunities']),
                    'validations': len(self._intel_state['validations']),
                    'whale_signals': len(self._intel_state['whale_signals']),
                    'counter_opps': len(self._intel_state['counter_opportunities']),
                    'market_pulse': self._intel_state['market_pulse'],
                    'timestamp': time.time()
                }
                
                # ─────────────────────────────────────────────────────────────
                # PHASE 2: THINK - Let Queen process
                # ─────────────────────────────────────────────────────────────
                if self._queen:
                    # Feed intelligence to Queen
                    if hasattr(self._queen, 'receive_intelligence'):
                        self._queen.receive_intelligence(self._intel_state)
                    
                    # Let Queen think
                    if hasattr(self._queen, 'autonomous_think'):
                        thought = self._queen.autonomous_think(perception)
                    elif hasattr(self._queen, 'think'):
                        thought = self._queen.think(perception)
                    else:
                        thought = None
                    
                    # ─────────────────────────────────────────────────────────
                    # PHASE 3: DECIDE - Queen makes decisions
                    # ─────────────────────────────────────────────────────────
                    if thought and hasattr(self._queen, 'decide'):
                        decision = self._queen.decide(thought)
                        
                        # PHASE 4: EXECUTE - If action required
                        if decision and hasattr(self._queen, 'execute'):
                            if hasattr(decision, 'action') and decision.action != 'scan':
                                self._queen.execute(decision)
                
                # Update loop stats
                loop.last_cycle = time.time()
                loop.cycle_count += 1
                
                # Sleep (Queen's thought rhythm)
                self._shutdown_event.wait(loop.interval_seconds)
                
            except Exception as e:
                loop.errors.append(f"{time.time()}: {str(e)}")
                logger.error(f"❌ Queen thought error: {e}")
                time.sleep(1.0)
        
        loop.status = SystemStatus.STOPPED
        logger.info("👑 Queen's Thought Loop: STOPPED")
    
    def _run_scanner_loop(self):
        """
        Continuous market scanning loop.
        Feeds opportunities to Queen via ThoughtBus.
        """
        loop = self.loops['scanner']
        loop.status = SystemStatus.RUNNING
        logger.info("🔭 Scanner Loop: STARTED")
        
        while not self._shutdown_event.is_set():
            try:
                if self._wave_scanner:
                    # Run A-Z sweep
                    if hasattr(self._wave_scanner, 'quick_scan'):
                        opportunities = self._wave_scanner.quick_scan()
                    elif hasattr(self._wave_scanner, 'scan'):
                        opportunities = self._wave_scanner.scan()
                    else:
                        opportunities = []
                    
                    # Publish to ThoughtBus
                    if opportunities and self._thought_bus:
                        for opp in opportunities[:10]:  # Top 10 only
                            self._thought_bus.think(
                                json.dumps(opp) if isinstance(opp, dict) else str(opp),
                                topic='scanner.opportunity'
                            )
                
                # Also use Miner Brain
                if self._miner_brain:
                    if hasattr(self._miner_brain, 'scan_markets'):
                        brain_opps = self._miner_brain.scan_markets()
                        if brain_opps and self._thought_bus:
                            for opp in brain_opps[:5]:
                                self._thought_bus.think(
                                    json.dumps(opp) if isinstance(opp, dict) else str(opp),
                                    topic='scanner.opportunity'
                                )
                
                loop.last_cycle = time.time()
                loop.cycle_count += 1
                self._shutdown_event.wait(loop.interval_seconds)
                
            except Exception as e:
                loop.errors.append(f"{time.time()}: {str(e)}")
                logger.error(f"❌ Scanner error: {e}")
                time.sleep(2.0)
        
        loop.status = SystemStatus.STOPPED
        logger.info("🔭 Scanner Loop: STOPPED")
    
    def _run_validation_loop(self):
        """
        Continuous validation loop (3-pass Batten Matrix).
        Validates opportunities and publishes coherence/lambda.
        """
        loop = self.loops['validation']
        loop.status = SystemStatus.RUNNING
        logger.info("✅ Validation Loop: STARTED")
        
        while not self._shutdown_event.is_set():
            try:
                # Get pending opportunities to validate
                pending = self._intel_state['opportunities'][-20:]
                
                for opp in pending:
                    if time.time() - opp.get('timestamp', 0) > 30:
                        continue  # Skip stale opportunities
                    
                    symbol = opp.get('data', {}).get('symbol', '')
                    if not symbol:
                        continue
                    
                    # Run 3-pass validation
                    passes = []
                    
                    # Pass 1: Miner Brain validation
                    if self._miner_brain and hasattr(self._miner_brain, 'validate'):
                        p1 = self._miner_brain.validate(opp.get('data', {}))
                        passes.append(p1 if isinstance(p1, (int, float)) else 0.5)
                    else:
                        passes.append(0.5)
                    
                    # Pass 2: Mycelium consensus
                    if self._mycelium and hasattr(self._mycelium, 'get_consensus'):
                        p2 = self._mycelium.get_consensus(symbol)
                        passes.append(p2 if isinstance(p2, (int, float)) else 0.5)
                    else:
                        passes.append(0.5)
                    
                    # Pass 3: Intelligence engine
                    if self._intelligence_engine and hasattr(self._intelligence_engine, 'validate_opportunity'):
                        p3 = self._intelligence_engine.validate_opportunity(opp.get('data', {}))
                        passes.append(p3 if isinstance(p3, (int, float)) else 0.5)
                    else:
                        passes.append(0.5)
                    
                    # Calculate coherence (agreement across validators)
                    coherence = 1 - (max(passes) - min(passes)) if passes else 0
                    
                    # Calculate lambda stability
                    import math
                    drift = 0.1  # Placeholder - would calculate from price drift
                    lambda_val = math.exp(-0.5 * drift)
                    
                    # Publish validation result
                    if self._thought_bus:
                        validation_data = {
                            'symbol': symbol,
                            'passes': passes,
                            'coherence': coherence,
                            'lambda': lambda_val,
                            '4th_ready': coherence > 0.618 and lambda_val > 0.8
                        }
                        self._thought_bus.think(
                            json.dumps(validation_data),
                            topic='validation.complete'
                        )
                        
                        # If 4th pass ready, this contributes to goal confidence
                        if validation_data['4th_ready'] and self._goal_tracker:
                            # Track validation quality (not money, but system health)
                            pass  # Validations don't directly contribute money
                
                loop.last_cycle = time.time()
                loop.cycle_count += 1
                self._shutdown_event.wait(loop.interval_seconds)
                
            except Exception as e:
                loop.errors.append(f"{time.time()}: {str(e)}")
                logger.error(f"❌ Validation error: {e}")
                time.sleep(1.0)
        
        loop.status = SystemStatus.STOPPED
        logger.info("✅ Validation Loop: STOPPED")
    
    def _run_intelligence_loop(self):
        """
        Continuous intelligence gathering loop.
        Detects bots, whales, market manipulation.
        """
        loop = self.loops['intelligence']
        loop.status = SystemStatus.RUNNING
        logger.info("🧠 Intelligence Loop: STARTED")
        
        while not self._shutdown_event.is_set():
            try:
                if self._intelligence_engine:
                    # Gather all intelligence
                    if hasattr(self._intelligence_engine, 'gather_all_intelligence'):
                        intel = self._intelligence_engine.gather_all_intelligence(
                            prices={},  # Would be filled with real prices
                            orderbook_data={}
                        )
                        
                        # Publish whale signals
                        if intel and 'whale_signals' in intel:
                            for sig in intel['whale_signals']:
                                if self._thought_bus:
                                    self._thought_bus.think(
                                        json.dumps(sig),
                                        topic='intel.whale_signal'
                                    )
                        
                        # Publish bot detections
                        if intel and 'bot_detections' in intel:
                            for bot in intel['bot_detections']:
                                if self._thought_bus:
                                    self._thought_bus.think(
                                        json.dumps(bot),
                                        topic='intel.bot_detected'
                                    )
                
                loop.last_cycle = time.time()
                loop.cycle_count += 1
                self._shutdown_event.wait(loop.interval_seconds)
                
            except Exception as e:
                loop.errors.append(f"{time.time()}: {str(e)}")
                logger.error(f"❌ Intelligence error: {e}")
                time.sleep(2.0)
        
        loop.status = SystemStatus.STOPPED
        logger.info("🧠 Intelligence Loop: STOPPED")
    
    def _run_counter_intel_loop(self):
        """
        Continuous counter-intelligence loop.
        Finds opportunities to trade against major firms.
        """
        loop = self.loops['counter_intel']
        loop.status = SystemStatus.RUNNING
        logger.info("⚔️ Counter-Intel Loop: STARTED")
        
        while not self._shutdown_event.is_set():
            try:
                if self._counter_intelligence:
                    # Get recent bot detections
                    recent_bots = [
                        d.get('data', {}) 
                        for d in self._intel_state.get('whale_signals', [])[-10:]
                    ]
                    
                    for bot_data in recent_bots:
                        firm = bot_data.get('firm', '')
                        if not firm:
                            continue
                        
                        # Analyze for counter opportunity
                        if hasattr(self._counter_intelligence, 'analyze_firm_for_counter_opportunity'):
                            counter_opp = self._counter_intelligence.analyze_firm_for_counter_opportunity(
                                firm,
                                market_data={},
                                bot_detection_data=bot_data
                            )
                            
                            if counter_opp and counter_opp.get('opportunity'):
                                if self._thought_bus:
                                    self._thought_bus.think(
                                        json.dumps(counter_opp),
                                        topic='counter_intel.opportunity'
                                    )
                
                loop.last_cycle = time.time()
                loop.cycle_count += 1
                self._shutdown_event.wait(loop.interval_seconds)
                
            except Exception as e:
                loop.errors.append(f"{time.time()}: {str(e)}")
                logger.error(f"❌ Counter-intel error: {e}")
                time.sleep(3.0)
        
        loop.status = SystemStatus.STOPPED
        logger.info("⚔️ Counter-Intel Loop: STOPPED")
    
    def _run_orca_loop(self):
        """
        Orca Kill Cycle execution loop.
        Handles actual trading with Queen's decisions.
        """
        loop = self.loops['orca_kill']
        loop.status = SystemStatus.RUNNING
        logger.info("🦈 Orca Kill Loop: STARTED")
        
        while not self._shutdown_event.is_set():
            try:
                if self._orca:
                    # Run one kill cycle iteration
                    if hasattr(self._orca, 'run_cycle'):
                        result = self._orca.run_cycle()
                    elif hasattr(self._orca, 'execute_cycle'):
                        result = self._orca.execute_cycle()
                    elif hasattr(self._orca, 'tick'):
                        result = self._orca.tick()
                    else:
                        result = None
                    
                    if result and self._thought_bus:
                        if result.get('kill_complete'):
                            self._thought_bus.think(
                                json.dumps(result),
                                topic='orca.kill_complete'
                            )
                            
                            # Report contribution to goal tracker
                            if self._goal_tracker and result.get('realized_pnl'):
                                self._goal_tracker.record_contribution(
                                    source='orca',
                                    amount=result.get('realized_pnl', 0),
                                    symbol=result.get('symbol', 'UNKNOWN'),
                                    exchange=result.get('exchange', 'unknown'),
                                    description='Orca kill cycle complete'
                                )
                
                loop.last_cycle = time.time()
                loop.cycle_count += 1
                self._shutdown_event.wait(loop.interval_seconds)
                
            except Exception as e:
                loop.errors.append(f"{time.time()}: {str(e)}")
                logger.error(f"❌ Orca error: {e}")
                time.sleep(1.0)
        
        loop.status = SystemStatus.STOPPED
        logger.info("🦈 Orca Kill Loop: STOPPED")
    
    def _run_avalanche_loop(self):
        """
        Avalanche Harvester loop.
        Continuously scrapes profits to stablecoins.
        """
        loop = self.loops['avalanche']
        loop.status = SystemStatus.RUNNING
        logger.info("❄️ Avalanche Loop: STARTED")
        
        while not self._shutdown_event.is_set():
            try:
                if self._avalanche:
                    if hasattr(self._avalanche, 'harvest_cycle'):
                        harvested = self._avalanche.harvest_cycle()
                    elif hasattr(self._avalanche, 'run'):
                        harvested = self._avalanche.run()
                    else:
                        harvested = None
                    
                    if harvested and self._thought_bus:
                        self._thought_bus.think(
                            json.dumps({'harvested': harvested}),
                            topic='avalanche.harvest_complete'
                        )
                
                loop.last_cycle = time.time()
                loop.cycle_count += 1
                self._shutdown_event.wait(loop.interval_seconds)
                
            except Exception as e:
                logger.error(f"❌ Avalanche error: {e}")
                time.sleep(5.0)
        
        loop.status = SystemStatus.STOPPED
        logger.info("❄️ Avalanche Loop: STOPPED")
    
    def _run_goal_engine_loop(self):
        """
        Goal Engine loop - Relentlessly setting and achieving goals.
        Syncs with billion tracker, celebrates achievements, generates new goals.
        """
        loop = self.loops['goal_engine']
        loop.status = SystemStatus.RUNNING
        logger.info("🎯 Goal Engine Loop: STARTED")
        
        while not self._shutdown_event.is_set():
            try:
                if self._goal_engine and self._goal_tracker:
                    # Sync progress from billion tracker
                    self._goal_engine.sync_with_billion_tracker()
                    
                    # Publish status to ThoughtBus
                    if self._thought_bus:
                        from aureon_thought_bus import Thought
                        self._thought_bus.publish(Thought(
                            source="goal_engine",
                            topic="goal_engine.status",
                            payload={
                                "active_goals": len(self._goal_engine.state.active_goals),
                                "total_achieved": self._goal_engine.state.total_goals_achieved,
                                "quantum_rate": self._goal_engine.state.quantum_rate(),
                                "acceleration": self._goal_engine.state.current_acceleration
                            }
                        ))
                
                loop.last_cycle = time.time()
                loop.cycle_count += 1
                self._shutdown_event.wait(loop.interval_seconds)
                
            except Exception as e:
                logger.error(f"❌ Goal Engine error: {e}")
                time.sleep(5.0)
        
        loop.status = SystemStatus.STOPPED
        logger.info("🎯 Goal Engine Loop: STOPPED")
    
    def _run_research_loop(self):
        """
        Research Engine loop - ENDLESS PURSUIT OF KNOWLEDGE.
        She NEVER stops researching.
        She NEVER gives up.
        Nothing is EVER good enough.
        """
        loop = self.loops['research']
        loop.status = SystemStatus.RUNNING
        logger.info("🔍 Research Loop: STARTED - THE ENDLESS PURSUIT")
        
        while not self._shutdown_event.is_set():
            try:
                if self._research_engine:
                    # Run continuous research cycle
                    self._research_engine.continuous_research_cycle()
                    
                    # Get actionable insights and feed to Queen
                    actionable = self._research_engine.get_actionable_insights(min_relevance=0.75)
                    
                    if actionable and self._thought_bus:
                        from aureon_thought_bus import Thought
                        self._thought_bus.publish(Thought(
                            source="research_engine",
                            topic="research.actionable_insights",
                            payload={
                                "insights_count": len(actionable),
                                "top_insights": [
                                    {
                                        "content": insight.content,
                                        "relevance": insight.relevance_score,
                                        "category": insight.category,
                                        "url": insight.url
                                    }
                                    for insight in actionable[:5]
                                ]
                            }
                        ))
                
                loop.last_cycle = time.time()
                loop.cycle_count += 1
                self._shutdown_event.wait(loop.interval_seconds)
                
            except Exception as e:
                logger.error(f"❌ Research Engine error: {e}")
                time.sleep(10.0)
        
        loop.status = SystemStatus.STOPPED
        logger.info("🔍 Research Loop: STOPPED")
        logger.info("❄️ Avalanche Loop: STOPPED")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # MASTER CONTROL
    # ═══════════════════════════════════════════════════════════════════════════
    
    def start(self):
        """
        Start ALL autonomous systems.
        Queen becomes fully autonomous from this point.
        """
        logger.info("")
        logger.info("🚀" * 30)
        logger.info("🚀  INITIATING FULL AUTONOMOUS MODE  🚀")
        logger.info("🚀" * 30)
        logger.info("")
        
        self._running = True
        self._shutdown_event.clear()
        
        # ─────────────────────────────────────────────────────────────────────
        # PHASE 1: Initialize Core Systems
        # ─────────────────────────────────────────────────────────────────────
        logger.info("═" * 60)
        logger.info("  PHASE 1: CORE SYSTEM INITIALIZATION")
        logger.info("═" * 60)
        
        self._init_thought_bus()
        self._init_queen()
        self._init_wave_scanner()
        self._init_miner_brain()
        self._init_mycelium()
        self._init_intelligence_engine()
        self._init_counter_intelligence()
        self._init_avalanche()
        self._init_orca()

        # Enable Queen's full autonomous control if available
        if self._queen and hasattr(self._queen, 'enable_full_autonomous_control'):
            try:
                result = self._queen.enable_full_autonomous_control()
                if result.get('success'):
                    logger.info("👑🎮 Queen full autonomous control: ENABLED")
                else:
                    logger.warning(f"👑🎮 Queen full autonomous control: {result.get('message', 'unavailable')}")
            except Exception as e:
                logger.warning(f"👑🎮 Queen autonomous control not enabled: {e}")
        
        # ─────────────────────────────────────────────────────────────────────
        # PHASE 2: Start Autonomous Loops
        # ─────────────────────────────────────────────────────────────────────
        logger.info("")
        logger.info("═" * 60)
        logger.info("  PHASE 2: STARTING AUTONOMOUS LOOPS")
        logger.info("═" * 60)
        
        loop_configs = [
            ('queen_thought', self._run_queen_thought_loop),
            ('scanner', self._run_scanner_loop),
            ('validation', self._run_validation_loop),
            ('intelligence', self._run_intelligence_loop),
            ('counter_intel', self._run_counter_intel_loop),
            ('orca_kill', self._run_orca_loop),
            ('avalanche', self._run_avalanche_loop),
        ]
        
        for loop_name, loop_func in loop_configs:
            thread = threading.Thread(
                target=loop_func,
                name=f"autonomous_{loop_name}",
                daemon=True
            )
            self.loops[loop_name].thread = thread
            self.loops[loop_name].status = SystemStatus.STARTING
            thread.start()
            logger.info(f"   🟢 {loop_name}: THREAD STARTED")
            time.sleep(0.2)  # Stagger startup
        
        # ─────────────────────────────────────────────────────────────────────
        # PHASE 3: Warmup & Verification
        # ─────────────────────────────────────────────────────────────────────
        logger.info("")
        logger.info("═" * 60)
        logger.info("  PHASE 3: WARMUP & VERIFICATION")
        logger.info("═" * 60)
        
        time.sleep(3.0)  # Let loops stabilize
        
        healthy = sum(1 for l in self.loops.values() if l.is_healthy())
        total = len(self.loops)
        
        logger.info("")
        logger.info("═" * 60)
        logger.info(f"  AUTONOMOUS STATUS: {healthy}/{total} LOOPS HEALTHY")
        logger.info("═" * 60)
        
        for name, loop in self.loops.items():
            status = "🟢" if loop.is_healthy() else "🔴"
            logger.info(f"   {status} {name}: {loop.status.value} (cycles: {loop.cycle_count})")
        
        logger.info("")
        logger.info("👑" * 30)
        logger.info("👑  QUEEN IS NOW FULLY AUTONOMOUS  👑")
        logger.info("👑  NO HUMAN INTERVENTION REQUIRED  👑")
        logger.info("👑" * 30)
        logger.info("")
        
        return healthy >= 4  # At least 4 loops must be healthy
    
    def stop(self):
        """Gracefully stop all autonomous systems."""
        logger.info("")
        logger.info("🛑 INITIATING GRACEFUL SHUTDOWN...")
        
        self._running = False
        self._shutdown_event.set()
        
        # Wait for threads to stop
        for name, loop in self.loops.items():
            if loop.thread and loop.thread.is_alive():
                logger.info(f"   🛑 Stopping {name}...")
                loop.thread.join(timeout=5.0)
        
        logger.info("✅ All autonomous loops stopped")
        logger.info("")
    
    def run_forever(self):
        """Run autonomously until interrupted."""
        if not self.start():
            logger.error("❌ Failed to start autonomous mode")
            return
        
        try:
            # Just wait for shutdown signal
            while self._running and not self._shutdown_event.is_set():
                # Print status every 60 seconds
                time.sleep(60)
                self._print_status()
        except KeyboardInterrupt:
            logger.info("\n⌨️ Keyboard interrupt received")
        finally:
            self.stop()
    
    def _print_status(self):
        """Print current autonomous status."""
        healthy = sum(1 for l in self.loops.values() if l.is_healthy())
        total_cycles = sum(l.cycle_count for l in self.loops.values())
        
        logger.info("")
        logger.info("═" * 80)
        logger.info(f"📊 AUTONOMOUS STATUS: {healthy}/{len(self.loops)} healthy | {total_cycles} total cycles")
        logger.info(f"   📡 Opportunities: {len(self._intel_state['opportunities'])}")
        logger.info(f"   ✅ Validations: {len(self._intel_state['validations'])}")
        logger.info(f"   🐋 Whale signals: {len(self._intel_state['whale_signals'])}")
        logger.info(f"   ⚔️ Counter opps: {len(self._intel_state['counter_opportunities'])}")
        
        # Print goal progress
        if self._goal_tracker and self._goal_engine:
            progress = self._goal_tracker.get_progress()
            logger.info("")
            logger.info(f"💰 GOAL PROGRESS: ${progress.current_balance:,.2f} / $1,000,000,000")
            logger.info(f"   Progress: {progress.percent_complete:.6f}% | Remaining: ${progress.dollars_remaining:,.2f}")
            logger.info(f"   🏁 Ladder: {progress.ladder_position} | {progress.rungs_climbed} rungs | {progress.speed_rank}")
            logger.info(f"   🎯 Active Goals: {len(self._goal_engine.state.active_goals)} | Achieved: {self._goal_engine.state.total_goals_achieved}")
            logger.info(f"   ⚡ Quantum Rate: {self._goal_engine.state.quantum_rate():.1f}% | Acceleration: {self._goal_engine.state.current_acceleration:.2f}x")
            
            # Research engine status
            if self._research_engine:
                pending_research = len([q for q in self._research_engine.research_queue if q.status == 'pending'])
                knowledge_count = len(self._research_engine.knowledge_base)
                actionable_count = len(self._research_engine.get_actionable_insights())
                logger.info(f"   🔍 Research: {knowledge_count} findings | {actionable_count} actionable | {pending_research} pending")
                logger.info(f"   ⚡ STATUS: NEVER STOPPING. NEVER GIVING UP. NOTHING IS EVER GOOD ENOUGH.")
        
        logger.info("═" * 80)
        logger.info("")


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_autonomous_instance = None

def get_autonomous_controller() -> QueenFullAutonomous:
    """Get the singleton autonomous controller."""
    global _autonomous_instance
    if _autonomous_instance is None:
        _autonomous_instance = QueenFullAutonomous()
    return _autonomous_instance


def get_queen_autonomous() -> QueenFullAutonomous:
    """Backward-compatible alias for autonomous controller accessor."""
    return get_autonomous_controller()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description="Queen's Full Autonomous System")
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (no real trades)')
    parser.add_argument('--margin', action='store_true', help='Enable margin trading (sets MARGIN_ENABLED=1)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.dry_run:
        os.environ['AUREON_DRY_RUN'] = '1'
        logger.info("🏜️ DRY RUN MODE - No real trades will be executed")

    # Enable margin trading if requested via --margin CLI arg or MARGIN_ENABLED env var
    if args.margin:
        os.environ['MARGIN_ENABLED'] = '1'

    # Ensure autonomous control is explicitly enabled for this launcher
    os.environ.setdefault('AUREON_ENABLE_AUTONOMOUS_CONTROL', '1')
    
    print("""
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║                                                                               ║
    ║   👑👑👑  QUEEN'S FULL AUTONOMOUS NEURAL EMPIRE  👑👑👑                       ║
    ║                                                                               ║
    ║   The Queen will now operate as a fully autonomous entity.                    ║
    ║   She will think, decide, and execute without human intervention.             ║
    ║                                                                               ║
    ║   Systems:                                                                    ║
    ║   • Queen Thought Loop - Continuous perception-decision-execution            ║
    ║   • Scanner Loop - Market opportunity detection                               ║
    ║   • Validation Loop - 3-pass Batten Matrix                                    ║
    ║   • Intelligence Loop - Whale/bot detection                                   ║
    ║   • Counter-Intel Loop - Firm counter-trading                                 ║
    ║   • Orca Kill Loop - Trade execution                                          ║
    ║   • Avalanche Loop - Profit harvesting                                        ║
    ║                                                                               ║
    ║   Press Ctrl+C to gracefully shutdown.                                        ║
    ║                                                                               ║
    ║   Prime Sentinel Decree: Gary Leckey (02.11.1991)                             ║
    ║                                                                               ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    controller = get_autonomous_controller()
    controller.run_forever()
