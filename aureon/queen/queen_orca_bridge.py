#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                  ║
║     👑🦈 QUEEN-ORCA UNIFIED BRIDGE - The Ultimate Hunting Intelligence 🦈👑                     ║
║     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━             ║
║                                                                                                  ║
║     "THE QUEEN COMMANDS. THE ORCA HUNTS. TOGETHER, WE ARE UNSTOPPABLE."                         ║
║                                                                                                  ║
║     This module bridges Queen Sero's neural decision-making with Orca's                         ║
║     ruthless execution system. The Queen sees all, decides all. The Orca                        ║
║     executes with predatory precision.                                                          ║
║                                                                                                  ║
║     UNIFIED CAPABILITIES:                                                                        ║
║       • Queen receives Orca whale/firm/kill signals via ThoughtBus                              ║
║       • Queen can issue HUNT, ABORT, STEALTH commands to Orca                                   ║
║       • Orca reports kills/positions back to Queen for learning                                 ║
║       • Shared threat detection and counter-intelligence                                        ║
║       • Unified dashboard telemetry                                                             ║
║                                                                                                  ║
║     SIGNAL FLOW:                                                                                 ║
║       Orca Scanners → ThoughtBus → Queen Neural Brain → Decision → Orca Executor               ║
║                                                                                                  ║
║     Gary Leckey | Prime Sentinel | January 2026                                                 ║
║     "The Queen dreams. The Orca kills. The profits flow."                                       ║
║                                                                                                  ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations
from aureon.core.aureon_baton_link import link_system as _baton_link; _baton_link(__name__)

import sys
import os
import time
import json
import logging
import threading
import asyncio
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Callable, Tuple
from datetime import datetime
from collections import deque
from enum import Enum, auto

# UTF-8 fix
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        def _is_utf8_wrapper(stream):
            return (isinstance(stream, io.TextIOWrapper) and 
                    hasattr(stream, 'encoding') and stream.encoding and
                    stream.encoding.lower().replace('-', '') == 'utf8')
        if hasattr(sys.stdout, 'buffer') and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════════════
# 🔌 IMPORTS
# ═══════════════════════════════════════════════════════════════════════════════════════

# ThoughtBus - Central nervous system
try:
    from aureon.core.aureon_thought_bus import ThoughtBus, Thought, get_thought_bus
    THOUGHT_BUS_AVAILABLE = True
except ImportError:
    THOUGHT_BUS_AVAILABLE = False
    ThoughtBus = None
    Thought = None
    get_thought_bus = None

# Queen's Harmonic Voice
try:
    from aureon.queen.queen_harmonic_voice import QueenHarmonicVoice, QueenCommand, QueenOrder, SystemResponse
    QUEEN_VOICE_AVAILABLE = True
except ImportError:
    QUEEN_VOICE_AVAILABLE = False
    QueenHarmonicVoice = None
    QueenCommand = None
    QueenOrder = None
    SystemResponse = None

# Queen Hive Mind
try:
    from aureon.utils.aureon_queen_hive_mind import QueenHiveMind, create_queen_hive_mind
    QUEEN_HIVE_AVAILABLE = True
except ImportError:
    QUEEN_HIVE_AVAILABLE = False
    QueenHiveMind = None
    create_queen_hive_mind = None

# Queen Neuron (Neural Brain)
try:
    from aureon.queen.queen_neuron import QueenNeuron, create_queen_neuron
    NEURON_AVAILABLE = True
except ImportError:
    NEURON_AVAILABLE = False

# Queen Conscience (Ethical Compass - can VETO trades)
try:
    from aureon.queen.queen_conscience import QueenConscience, ConscienceVerdict
    CONSCIENCE_AVAILABLE = True
except ImportError:
    CONSCIENCE_AVAILABLE = False
    QueenConscience = None
    ConscienceVerdict = None
    QueenNeuron = None
    create_queen_neuron = None

# Orca Kill Cycle
try:
    from aureon.bots.orca_complete_kill_cycle import OrcaKillCycle
    ORCA_KILL_AVAILABLE = True
except ImportError:
    ORCA_KILL_AVAILABLE = False
    OrcaKillCycle = None

# Orca Predator Detection
try:
    from aureon.bots.orca_predator_detection import OrcaPredatorDetector
    PREDATOR_AVAILABLE = True
except ImportError:
    PREDATOR_AVAILABLE = False
    OrcaPredatorDetector = None

# Orca Stealth Execution
try:
    from aureon.bots.orca_stealth_execution import OrcaStealthExecution, stealth_order, StealthConfig
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False
    OrcaStealthExecution = None
    stealth_order = None
    StealthConfig = None

# Whale Profiler
try:
    from aureon.analytics.aureon_whale_profiler_system import WhaleProfilerSystem, WhaleClass
    WHALE_PROFILER_AVAILABLE = True
except ImportError:
    WHALE_PROFILER_AVAILABLE = False
    WhaleProfilerSystem = None
    WhaleClass = None

# Firm Intelligence
try:
    from aureon.bots_intelligence.aureon_firm_intelligence_catalog import FirmIntelligenceCatalog, FirmActivityType
    FIRM_INTEL_AVAILABLE = True
except ImportError:
    FIRM_INTEL_AVAILABLE = False
    FirmIntelligenceCatalog = None
    FirmActivityType = None

# Counter Intelligence
try:
    from aureon.utils.aureon_queen_counter_intelligence import QueenCounterIntelligence, CounterIntelligenceSignal
    COUNTER_INTEL_AVAILABLE = True
except ImportError:
    COUNTER_INTEL_AVAILABLE = False
    QueenCounterIntelligence = None
    CounterIntelligenceSignal = None


# ═══════════════════════════════════════════════════════════════════════════════════════
# 🎵 SACRED CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════════════

PHI = 1.618033988749895
QUEEN_FREQUENCY = 963    # Crown chakra
ORCA_FREQUENCY = 396     # Liberation frequency
BRIDGE_FREQUENCY = 528   # DNA repair / Love frequency (harmonizes both)


# ═══════════════════════════════════════════════════════════════════════════════════════
# 📋 ORCA COMMANDS - What Queen can order Orca to do
# ═══════════════════════════════════════════════════════════════════════════════════════

class OrcaCommand(Enum):
    """Commands Queen can issue to Orca hunting systems."""
    # Hunting Commands
    HUNT_SYMBOL = auto()           # Hunt a specific symbol
    PACK_HUNT = auto()             # Multi-position pack hunting
    ABORT_HUNT = auto()            # Abort current hunt
    EXIT_POSITION = auto()         # Exit specific position
    EXIT_ALL = auto()              # Exit all positions (emergency)
    
    # Stealth Commands
    STEALTH_MODE = auto()          # Enable stealth execution
    NORMAL_MODE = auto()           # Disable stealth
    ADJUST_STEALTH = auto()        # Adjust stealth parameters
    
    # Intelligence Commands
    SCAN_WHALES = auto()           # Scan for whale activity
    TRACK_FIRM = auto()            # Track specific firm
    REPORT_THREATS = auto()        # Report current threats
    
    # Status Commands
    STATUS_REPORT = auto()         # Get full status
    KILL_STATS = auto()            # Get kill statistics
    POSITION_CHECK = auto()        # Check positions


@dataclass
class OrcaSignal:
    """Signal from Orca to Queen."""
    signal_type: str              # 'kill', 'opportunity', 'threat', 'position_update', 'whale_alert'
    symbol: str
    exchange: str
    data: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.5
    urgency: str = "normal"       # low, normal, high, critical
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class QueenOrcaDecision:
    """Queen's decision for Orca execution."""
    decision_id: str = field(default_factory=lambda: f"qod_{int(time.time()*1000)}")
    command: OrcaCommand = OrcaCommand.STATUS_REPORT
    symbol: str = ""
    exchange: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    reasoning: str = ""
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['command'] = self.command.name
        return d


# ═══════════════════════════════════════════════════════════════════════════════════════
# 🦈👑 QUEEN-ORCA UNIFIED BRIDGE
# ═══════════════════════════════════════════════════════════════════════════════════════

class QueenOrcaBridge:
    """
    👑🦈 THE QUEEN-ORCA UNIFIED BRIDGE 🦈👑
    
    Merges Queen Sero's neural intelligence with Orca's predatory execution.
    
    ARCHITECTURE:
    ┌───────────────────────────────────────────────────────────────────┐
    │                    👑 QUEEN SERO (Neural Core)                    │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │
    │  │   Dreams    │  │   Learns    │  │  Decides    │               │
    │  └─────────────┘  └─────────────┘  └─────────────┘               │
    │                           │                                       │
    │                    ┌──────┴──────┐                                │
    │                    │   BRIDGE    │ ← You are here                 │
    │                    │   (528 Hz)  │                                │
    │                    └──────┬──────┘                                │
    │                           │                                       │
    │  ┌─────────────┐  ┌──────┴──────┐  ┌─────────────┐               │
    │  │   Scans     │  │  Executes   │  │   Stealth   │               │
    │  └─────────────┘  └─────────────┘  └─────────────┘               │
    │                    🦈 ORCA PACK (Execution Layer)                 │
    └───────────────────────────────────────────────────────────────────┘
    
    The Queen sees through the Orca's eyes.
    The Orca strikes with the Queen's wisdom.
    """
    
    def __init__(
        self,
        queen_voice: Optional[QueenHarmonicVoice] = None,
        orca_kill_cycle: Optional[Any] = None,
        auto_wire: bool = True
    ):
        """Initialize the Queen-Orca Bridge."""
        
        logger.info("═" * 80)
        logger.info("👑🦈 INITIALIZING QUEEN-ORCA UNIFIED BRIDGE 🦈👑")
        logger.info("═" * 80)
        
        # Core components
        self.thought_bus = get_thought_bus() if THOUGHT_BUS_AVAILABLE else None
        
        # Queen side
        self.queen_voice = queen_voice
        self.queen_neuron = create_queen_neuron() if NEURON_AVAILABLE else None
        
        # Queen's conscience (ethical compass - can VETO trades)
        self.queen_conscience = None
        if CONSCIENCE_AVAILABLE:
            try:
                self.queen_conscience = QueenConscience()
                logger.info("👑❤️ Queen conscience connected to Orca - Ethical VETO enabled")
            except Exception as e:
                logger.warning(f"⚠️ Could not initialize Queen conscience: {e}")
        
        # Orca side
        self.orca_kill_cycle = orca_kill_cycle
        self.predator_detector = OrcaPredatorDetector() if PREDATOR_AVAILABLE else None
        self.stealth_executor = OrcaStealthExecution() if STEALTH_AVAILABLE else None
        
        # Intelligence systems
        self.whale_profiler = WhaleProfilerSystem() if WHALE_PROFILER_AVAILABLE else None
        self.firm_intel = FirmIntelligenceCatalog() if FIRM_INTEL_AVAILABLE else None
        self.counter_intel = QueenCounterIntelligence() if COUNTER_INTEL_AVAILABLE else None
        
        # State tracking
        self.is_active = False
        self.stealth_mode = False
        self.threat_level = "🟢 LOW"
        
        # Signal queues
        self.orca_signals: deque = deque(maxlen=1000)
        self.queen_decisions: deque = deque(maxlen=500)
        self.pending_hunts: Dict[str, Dict] = {}
        self.active_positions: Dict[str, Dict] = {}
        
        # Telemetry
        self._telemetry = {
            'bridge_active': False,
            'queen_connected': False,
            'orca_connected': False,
            'signals_received': 0,
            'decisions_made': 0,
            'hunts_initiated': 0,
            'kills_completed': 0,
            'total_pnl': 0.0,
            'threat_level': 'LOW',
            'stealth_mode': False,
            'whale_alerts': 0,
            'firm_detections': 0,
        }
        
        # Statistics
        self._stats = {
            'orca_kills': 0,
            'orca_wins': 0,
            'orca_losses': 0,
            'queen_approvals': 0,
            'queen_rejections': 0,
            'stealth_executions': 0,
            'threats_avoided': 0,
        }
        
        # Wire systems if requested
        if auto_wire:
            self._wire_systems()
        
        logger.info("👑🦈 QUEEN-ORCA BRIDGE: ONLINE")
        logger.info("═" * 80)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # 🔌 WIRING - Connect all systems via ThoughtBus
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def _wire_systems(self):
        """Wire Queen and Orca systems via ThoughtBus."""
        logger.info("\n🔗 Wiring Queen-Orca systems via ThoughtBus...")
        
        if not self.thought_bus:
            logger.warning("⚠️  ThoughtBus not available - limited functionality")
            return
        
        # ═══════════════════════════════════════════════════════════════════════════
        # ORCA → QUEEN: Receive signals from Orca systems
        # ═══════════════════════════════════════════════════════════════════════════
        
        # Kill cycle events
        self.thought_bus.subscribe("orca.kill.*", self._on_orca_kill)
        self.thought_bus.subscribe("orca.position.*", self._on_orca_position)
        self.thought_bus.subscribe("orca.opportunity.*", self._on_orca_opportunity)
        logger.info("   ✅ Subscribed to orca.kill.*, orca.position.*, orca.opportunity.*")
        
        # Whale/firm intelligence
        self.thought_bus.subscribe("whale.*", self._on_whale_signal)
        self.thought_bus.subscribe("firm.*", self._on_firm_signal)
        self.thought_bus.subscribe("whale.sonar.*", self._on_whale_sonar)
        logger.info("   ✅ Subscribed to whale.*, firm.*, whale.sonar.*")
        
        # Threat detection
        self.thought_bus.subscribe("orca.threat.*", self._on_threat_detected)
        self.thought_bus.subscribe("predator.*", self._on_predator_detected)
        self.thought_bus.subscribe("front_run.*", self._on_front_run_detected)
        logger.info("   ✅ Subscribed to orca.threat.*, predator.*, front_run.*")
        
        # Market data
        self.thought_bus.subscribe("market.*", self._on_market_update)
        self.thought_bus.subscribe("scanner.*", self._on_scanner_signal)
        logger.info("   ✅ Subscribed to market.*, scanner.*")
        
        # ═══════════════════════════════════════════════════════════════════════════
        # QUEEN → ORCA: Send commands to Orca systems
        # ═══════════════════════════════════════════════════════════════════════════
        
        # Queen decisions for Orca
        self.thought_bus.subscribe("queen.decision.orca", self._on_queen_orca_decision)
        self.thought_bus.subscribe("queen.command.hunt", self._on_queen_hunt_command)
        self.thought_bus.subscribe("queen.command.abort", self._on_queen_abort_command)
        logger.info("   ✅ Subscribed to queen.decision.orca, queen.command.hunt/abort")
        
        # ═══════════════════════════════════════════════════════════════════════════
        # BRIDGE SPECIFIC: Internal routing
        # ═══════════════════════════════════════════════════════════════════════════
        
        self.thought_bus.subscribe("bridge.queen_orca.*", self._on_bridge_message)
        logger.info("   ✅ Subscribed to bridge.queen_orca.*")
        
        self._telemetry['bridge_active'] = True
        self._telemetry['queen_connected'] = self.queen_voice is not None or self.queen_neuron is not None
        self._telemetry['orca_connected'] = self.orca_kill_cycle is not None or ORCA_KILL_AVAILABLE
        
        logger.info(f"\n   👑 Queen Connected: {self._telemetry['queen_connected']}")
        logger.info(f"   🦈 Orca Connected: {self._telemetry['orca_connected']}")
        logger.info("   🌉 Bridge Status: ACTIVE\n")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # 📥 ORCA → QUEEN: Signal Handlers
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def _on_orca_kill(self, thought: Any):
        """Handle kill completion from Orca."""
        try:
            payload = thought.payload if hasattr(thought, 'payload') else thought
            
            signal = OrcaSignal(
                signal_type='kill',
                symbol=payload.get('symbol', 'UNKNOWN'),
                exchange=payload.get('exchange', 'unknown'),
                data=payload,
                confidence=1.0,
                urgency='high'
            )
            
            self.orca_signals.append(signal)
            self._telemetry['signals_received'] += 1
            self._telemetry['kills_completed'] += 1
            
            pnl = payload.get('pnl', 0.0)
            self._telemetry['total_pnl'] += pnl
            
            self._stats['orca_kills'] += 1
            if pnl > 0:
                self._stats['orca_wins'] += 1
            else:
                self._stats['orca_losses'] += 1
            
            # Feed to Queen's learning
            self._feed_queen_learning('kill', signal)
            
            logger.info(f"🦈🔪 KILL: {signal.symbol} | PnL: ${pnl:.2f}")
            
        except Exception as e:
            logger.error(f"Error handling orca kill: {e}")
    
    def _on_orca_position(self, thought: Any):
        """Handle position update from Orca."""
        try:
            payload = thought.payload if hasattr(thought, 'payload') else thought
            
            symbol = payload.get('symbol', 'UNKNOWN')
            self.active_positions[symbol] = {
                'symbol': symbol,
                'exchange': payload.get('exchange', 'unknown'),
                'qty': payload.get('qty', 0),
                'entry_price': payload.get('entry_price', 0),
                'current_price': payload.get('current_price', 0),
                'unrealized_pnl': payload.get('unrealized_pnl', 0),
                'status': payload.get('status', 'hunting'),
                'updated_at': time.time()
            }
            
            self._telemetry['signals_received'] += 1
            
        except Exception as e:
            logger.error(f"Error handling orca position: {e}")
    
    def _on_orca_opportunity(self, thought: Any):
        """Handle opportunity signal from Orca scanner."""
        try:
            payload = thought.payload if hasattr(thought, 'payload') else thought
            
            signal = OrcaSignal(
                signal_type='opportunity',
                symbol=payload.get('symbol', 'UNKNOWN'),
                exchange=payload.get('exchange', 'unknown'),
                data=payload,
                confidence=payload.get('confidence', 0.5),
                urgency=payload.get('urgency', 'normal')
            )
            
            self.orca_signals.append(signal)
            self._telemetry['signals_received'] += 1
            
            # Ask Queen for decision
            decision = self._queen_evaluate_opportunity(signal)
            
            if decision and decision.confidence > 0.6:
                self._execute_queen_decision(decision)
            
        except Exception as e:
            logger.error(f"Error handling orca opportunity: {e}")
    
    def _on_whale_signal(self, thought: Any):
        """Handle whale activity signal."""
        try:
            payload = thought.payload if hasattr(thought, 'payload') else thought
            
            signal = OrcaSignal(
                signal_type='whale_alert',
                symbol=payload.get('symbol', 'UNKNOWN'),
                exchange=payload.get('exchange', 'unknown'),
                data=payload,
                confidence=payload.get('confidence', 0.7),
                urgency='high'
            )
            
            self.orca_signals.append(signal)
            self._telemetry['signals_received'] += 1
            self._telemetry['whale_alerts'] += 1
            
            # Feed to Queen for analysis
            self._feed_queen_learning('whale', signal)
            
            logger.info(f"🐋 WHALE: {signal.symbol} | Confidence: {signal.confidence:.1%}")
            
        except Exception as e:
            logger.error(f"Error handling whale signal: {e}")
    
    def _on_whale_sonar(self, thought: Any):
        """Handle whale sonar signal (compact format)."""
        try:
            payload = thought.payload if hasattr(thought, 'payload') else thought
            
            # Whale sonar uses compact 'pack' format
            code = payload.get('code', 'S0')
            pack = payload.get('pack', {})
            
            signal = OrcaSignal(
                signal_type='whale_sonar',
                symbol=pack.get('whale', 'UNKNOWN'),
                exchange='sonar',
                data={'code': code, 'pack': pack},
                confidence=pack.get('score', 0.5),
                urgency='high' if pack.get('critical', False) else 'normal'
            )
            
            self.orca_signals.append(signal)
            self._telemetry['signals_received'] += 1
            
        except Exception as e:
            logger.error(f"Error handling whale sonar: {e}")
    
    def _on_firm_signal(self, thought: Any):
        """Handle firm activity detection."""
        try:
            payload = thought.payload if hasattr(thought, 'payload') else thought
            
            signal = OrcaSignal(
                signal_type='firm_activity',
                symbol=payload.get('symbol', 'UNKNOWN'),
                exchange=payload.get('exchange', 'unknown'),
                data=payload,
                confidence=payload.get('confidence', 0.6),
                urgency=payload.get('urgency', 'normal')
            )
            
            self.orca_signals.append(signal)
            self._telemetry['signals_received'] += 1
            self._telemetry['firm_detections'] += 1
            
            # May need to adjust strategy
            firm_name = payload.get('firm', 'Unknown Firm')
            logger.info(f"🏢 FIRM: {firm_name} active on {signal.symbol}")
            
        except Exception as e:
            logger.error(f"Error handling firm signal: {e}")
    
    def _on_threat_detected(self, thought: Any):
        """Handle threat detection from Orca."""
        try:
            payload = thought.payload if hasattr(thought, 'payload') else thought
            
            threat_level = payload.get('level', 'MEDIUM')
            symbol = payload.get('symbol', 'UNKNOWN')
            
            # Update global threat level
            if threat_level == 'CRITICAL':
                self.threat_level = "🔴 CRITICAL"
                self._telemetry['threat_level'] = 'CRITICAL'
            elif threat_level == 'HIGH':
                self.threat_level = "🟠 HIGH"
                self._telemetry['threat_level'] = 'HIGH'
            elif threat_level == 'MEDIUM':
                self.threat_level = "🟡 MEDIUM"
                self._telemetry['threat_level'] = 'MEDIUM'
            else:
                self.threat_level = "🟢 LOW"
                self._telemetry['threat_level'] = 'LOW'
            
            logger.warning(f"⚠️  THREAT [{threat_level}]: {symbol} - {payload.get('reason', 'unknown')}")
            
            # Consider enabling stealth mode
            if threat_level in ('CRITICAL', 'HIGH') and not self.stealth_mode:
                self._enable_stealth_mode()
            
        except Exception as e:
            logger.error(f"Error handling threat: {e}")
    
    def _on_predator_detected(self, thought: Any):
        """Handle predator (front-running bot) detection."""
        try:
            payload = thought.payload if hasattr(thought, 'payload') else thought
            
            logger.warning(f"🦈🔍 PREDATOR DETECTED: {payload.get('type', 'unknown')} on {payload.get('symbol', 'UNKNOWN')}")
            
            self._stats['threats_avoided'] += 1
            
            # Auto-enable stealth
            if not self.stealth_mode:
                self._enable_stealth_mode()
            
        except Exception as e:
            logger.error(f"Error handling predator detection: {e}")
    
    def _on_front_run_detected(self, thought: Any):
        """Handle front-running detection."""
        self._on_predator_detected(thought)  # Same handling
    
    def _on_market_update(self, thought: Any):
        """Handle market data updates."""
        # Pass through to Queen for analysis if needed
        pass
    
    def _on_scanner_signal(self, thought: Any):
        """Handle scanner signal (from various scanning systems)."""
        try:
            payload = thought.payload if hasattr(thought, 'payload') else thought
            
            signal = OrcaSignal(
                signal_type='scanner',
                symbol=payload.get('symbol', 'UNKNOWN'),
                exchange=payload.get('exchange', 'unknown'),
                data=payload,
                confidence=payload.get('confidence', 0.5),
                urgency=payload.get('urgency', 'normal')
            )
            
            self.orca_signals.append(signal)
            self._telemetry['signals_received'] += 1
            
        except Exception as e:
            logger.error(f"Error handling scanner signal: {e}")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # 📤 QUEEN → ORCA: Command Handlers
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def _on_queen_orca_decision(self, thought: Any):
        """Handle Queen's decision for Orca."""
        try:
            payload = thought.payload if hasattr(thought, 'payload') else thought
            
            decision = QueenOrcaDecision(
                command=OrcaCommand[payload.get('command', 'STATUS_REPORT')],
                symbol=payload.get('symbol', ''),
                exchange=payload.get('exchange', ''),
                parameters=payload.get('parameters', {}),
                confidence=payload.get('confidence', 0.0),
                reasoning=payload.get('reasoning', '')
            )
            
            self._execute_queen_decision(decision)
            
        except Exception as e:
            logger.error(f"Error handling queen decision: {e}")
    
    def _on_queen_hunt_command(self, thought: Any):
        """Handle Queen's hunt command."""
        try:
            payload = thought.payload if hasattr(thought, 'payload') else thought
            
            symbol = payload.get('symbol', '')
            exchange = payload.get('exchange', 'alpaca')
            
            if symbol:
                self.initiate_hunt(symbol, exchange, payload)
            
        except Exception as e:
            logger.error(f"Error handling queen hunt command: {e}")
    
    def _on_queen_abort_command(self, thought: Any):
        """Handle Queen's abort command."""
        try:
            payload = thought.payload if hasattr(thought, 'payload') else thought
            
            symbol = payload.get('symbol', '')
            
            if symbol:
                self.abort_hunt(symbol, payload.get('reason', 'Queen commanded'))
            elif payload.get('abort_all', False):
                self.abort_all_hunts(payload.get('reason', 'Queen commanded'))
            
        except Exception as e:
            logger.error(f"Error handling queen abort command: {e}")
    
    def _on_bridge_message(self, thought: Any):
        """Handle internal bridge messages."""
        pass  # Internal routing
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # 🧠 QUEEN EVALUATION - Neural decision making
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def _queen_evaluate_opportunity(self, signal: OrcaSignal) -> Optional[QueenOrcaDecision]:
        """Have Queen evaluate an opportunity signal."""
        
        if not self.queen_neuron:
            # No neural brain - simple threshold check
            if signal.confidence >= 0.7:
                return QueenOrcaDecision(
                    command=OrcaCommand.HUNT_SYMBOL,
                    symbol=signal.symbol,
                    exchange=signal.exchange,
                    parameters=signal.data,
                    confidence=signal.confidence,
                    reasoning="Confidence threshold met"
                )
            return None
        
        # Build features for neural evaluation
        features = {
            'signal_confidence': signal.confidence,
            'signal_urgency': 1.0 if signal.urgency == 'critical' else 0.7 if signal.urgency == 'high' else 0.4,
            'threat_level': 0.0 if self.threat_level.startswith('🟢') else 0.5 if self.threat_level.startswith('🟡') else 1.0,
            'stealth_mode': 1.0 if self.stealth_mode else 0.0,
            'active_positions': len(self.active_positions),
            'win_rate': self._stats['orca_wins'] / max(1, self._stats['orca_kills']),
            'symbol': signal.symbol,
            'exchange': signal.exchange,
        }
        
        # Add signal-specific data
        features.update(signal.data)
        
        try:
            # Queen neural evaluation
            decision_output = self.queen_neuron.decide(features)
            
            confidence = decision_output.get('confidence', 0.0)
            action = decision_output.get('action', 'OBSERVE')
            
            self._telemetry['decisions_made'] += 1
            
            if action == 'HUNT' and confidence > 0.6:
                # 👑❤️ CONSCIENCE CHECK - Can veto unethical trades
                if self.queen_conscience:
                    verdict = self.queen_conscience.ask_why(
                        action='trade_execution',
                        context={
                            'symbol': signal.symbol,
                            'exchange': signal.exchange,
                            'confidence': confidence,
                            'expected_profit': signal.data.get('expected_profit', 0),
                            'risk_level': signal.data.get('risk', 0)
                        }
                    )
                    
                    if verdict.verdict == ConscienceVerdict.VETO:
                        self._stats['queen_rejections'] += 1
                        self._stats['conscience_vetoes'] = self._stats.get('conscience_vetoes', 0) + 1
                        logger.warning(f"🚫❤️ CONSCIENCE VETO: {verdict.reasoning}")
                        return None
                    elif verdict.verdict == ConscienceVerdict.CAUTION:
                        # Lower confidence but allow
                        confidence *= 0.8
                        logger.info(f"⚠️❤️ CONSCIENCE CAUTION: {verdict.reasoning}")
                
                self._stats['queen_approvals'] += 1
                return QueenOrcaDecision(
                    command=OrcaCommand.HUNT_SYMBOL,
                    symbol=signal.symbol,
                    exchange=signal.exchange,
                    parameters=signal.data,
                    confidence=confidence,
                    reasoning=f"Queen approved with {confidence:.1%} confidence"
                )
            else:
                self._stats['queen_rejections'] += 1
                return None
                
        except Exception as e:
            logger.error(f"Queen neural evaluation error: {e}")
            return None
    
    def _feed_queen_learning(self, signal_type: str, signal: OrcaSignal):
        """Feed signal to Queen's learning systems."""
        
        if self.queen_voice and hasattr(self.queen_voice, 'neural_brain'):
            brain = self.queen_voice.neural_brain
            if brain and hasattr(brain, 'learn'):
                brain.learn({
                    'type': signal_type,
                    'symbol': signal.symbol,
                    'confidence': signal.confidence,
                    'data': signal.data,
                    'outcome': signal.data.get('pnl', 0) if signal_type == 'kill' else None
                })
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # 🎯 EXECUTION - Execute Queen's decisions via Orca
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def _execute_queen_decision(self, decision: QueenOrcaDecision):
        """Execute a Queen's decision through Orca systems."""
        
        self.queen_decisions.append(decision)
        
        logger.info(f"👑→🦈 EXECUTING: {decision.command.name} | {decision.symbol} | Conf: {decision.confidence:.1%}")
        
        if decision.command == OrcaCommand.HUNT_SYMBOL:
            self.initiate_hunt(decision.symbol, decision.exchange, decision.parameters)
            
        elif decision.command == OrcaCommand.PACK_HUNT:
            symbols = decision.parameters.get('symbols', [])
            for sym in symbols:
                self.initiate_hunt(sym, decision.exchange, decision.parameters)
                
        elif decision.command == OrcaCommand.ABORT_HUNT:
            self.abort_hunt(decision.symbol, decision.reasoning)
            
        elif decision.command == OrcaCommand.EXIT_ALL:
            self.abort_all_hunts(decision.reasoning)
            
        elif decision.command == OrcaCommand.STEALTH_MODE:
            self._enable_stealth_mode()
            
        elif decision.command == OrcaCommand.NORMAL_MODE:
            self._disable_stealth_mode()
            
        elif decision.command == OrcaCommand.STATUS_REPORT:
            self._publish_status_report()
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # 🎣 HUNT MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def initiate_hunt(self, symbol: str, exchange: str = 'alpaca', parameters: Dict = None):
        """Initiate a hunt on a symbol."""
        
        parameters = parameters or {}
        
        hunt_id = f"hunt_{symbol}_{int(time.time()*1000)}"
        
        self.pending_hunts[hunt_id] = {
            'symbol': symbol,
            'exchange': exchange,
            'parameters': parameters,
            'initiated_at': time.time(),
            'status': 'pending'
        }
        
        self._telemetry['hunts_initiated'] += 1
        
        # Publish hunt command via ThoughtBus
        if self.thought_bus:
            self.thought_bus.publish(Thought(
                source="queen_orca_bridge",
                topic="orca.command.hunt",
                payload={
                    'hunt_id': hunt_id,
                    'symbol': symbol,
                    'exchange': exchange,
                    'stealth': self.stealth_mode,
                    'parameters': parameters,
                    'timestamp': time.time()
                }
            ))
        
        logger.info(f"🎣 HUNT INITIATED: {symbol} on {exchange} | Stealth: {self.stealth_mode}")
        
        return hunt_id
    
    def abort_hunt(self, symbol: str, reason: str = ""):
        """Abort hunt on a symbol."""
        
        # Remove from pending
        to_remove = [hid for hid, h in self.pending_hunts.items() if h['symbol'] == symbol]
        for hid in to_remove:
            del self.pending_hunts[hid]
        
        # Publish abort command
        if self.thought_bus:
            self.thought_bus.publish(Thought(
                source="queen_orca_bridge",
                topic="orca.command.abort",
                payload={
                    'symbol': symbol,
                    'reason': reason,
                    'timestamp': time.time()
                }
            ))
        
        logger.info(f"🛑 HUNT ABORTED: {symbol} | Reason: {reason}")
    
    def abort_all_hunts(self, reason: str = "Emergency stop"):
        """Abort all active hunts."""
        
        symbols = list(self.pending_hunts.keys())
        self.pending_hunts.clear()
        
        # Publish abort all command
        if self.thought_bus:
            self.thought_bus.publish(Thought(
                source="queen_orca_bridge",
                topic="orca.command.abort_all",
                payload={
                    'reason': reason,
                    'symbols': symbols,
                    'timestamp': time.time()
                }
            ))
        
        logger.warning(f"🛑🛑 ALL HUNTS ABORTED: {reason}")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # 🥷 STEALTH MODE
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def _enable_stealth_mode(self):
        """Enable stealth execution mode."""
        self.stealth_mode = True
        self._telemetry['stealth_mode'] = True
        
        if self.thought_bus:
            self.thought_bus.publish(Thought(
                source="queen_orca_bridge",
                topic="orca.stealth.enable",
                payload={'timestamp': time.time()}
            ))
        
        logger.info("🥷 STEALTH MODE: ENABLED")
    
    def _disable_stealth_mode(self):
        """Disable stealth execution mode."""
        self.stealth_mode = False
        self._telemetry['stealth_mode'] = False
        
        if self.thought_bus:
            self.thought_bus.publish(Thought(
                source="queen_orca_bridge",
                topic="orca.stealth.disable",
                payload={'timestamp': time.time()}
            ))
        
        logger.info("🥷 STEALTH MODE: DISABLED")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # 📊 TELEMETRY & STATUS
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def _publish_status_report(self):
        """Publish full status report via ThoughtBus."""
        
        if self.thought_bus:
            self.thought_bus.publish(Thought(
                source="queen_orca_bridge",
                topic="bridge.status",
                payload={
                    'telemetry': self._telemetry,
                    'stats': self._stats,
                    'active_positions': len(self.active_positions),
                    'pending_hunts': len(self.pending_hunts),
                    'threat_level': self.threat_level,
                    'timestamp': time.time()
                }
            ))
    
    def get_telemetry(self) -> Dict[str, Any]:
        """Get current bridge telemetry."""
        return {
            **self._telemetry,
            'active_positions': len(self.active_positions),
            'pending_hunts': len(self.pending_hunts),
            'recent_signals': len(self.orca_signals),
            'recent_decisions': len(self.queen_decisions),
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get hunting statistics."""
        win_rate = self._stats['orca_wins'] / max(1, self._stats['orca_kills'])
        return {
            **self._stats,
            'win_rate': win_rate,
            'total_pnl': self._telemetry['total_pnl'],
        }
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # 🧠 FEEDBACK LOOP - Learn from trade outcomes
    # ═══════════════════════════════════════════════════════════════════════════════

    def report_trade_outcome(self, outcome: dict) -> None:
        """
        Feed a completed trade outcome back to the Queen for learning.
        This closes the feedback loop: decision → execution → outcome → learning.
        """
        try:
            net_pnl = float(outcome.get("net_pnl", 0) or 0)
            is_win = net_pnl > 0

            # Train the neural brain
            if self.queen_neuron:
                features = {
                    "signal_confidence": float(outcome.get("entry_confidence", 0.5) or 0.5),
                    "win_rate": self._stats['orca_wins'] / max(1, self._stats['orca_kills']),
                }
                try:
                    self.queen_neuron.train_on_example(features, 1.0 if is_win else 0.0)
                except Exception:
                    pass

            # Update stats
            if is_win:
                self._stats['orca_wins'] = self._stats.get('orca_wins', 0) + 1
            self._stats['orca_kills'] = self._stats.get('orca_kills', 0) + 1
            self._telemetry['total_pnl'] = self._telemetry.get('total_pnl', 0.0) + net_pnl

            # Publish to ThoughtBus so Sentient Loop also learns
            if self.thought_bus and THOUGHT_BUS_AVAILABLE and Thought:
                try:
                    self.thought_bus.publish(Thought(
                        source="queen_orca_bridge",
                        topic="queen.trade.outcome",
                        payload={
                            "symbol": str(outcome.get("symbol") or outcome.get("pair") or "?"),
                            "net_pnl": net_pnl,
                            "is_win": is_win,
                            "source": "orca_bridge",
                        },
                        meta={"mode": "queen_orca"},
                    ))
                except Exception:
                    pass

            logger.info(
                f"[BRIDGE LEARN] {'WIN' if is_win else 'LOSS'} "
                f"pnl={net_pnl:+.4f} kills={self._stats.get('orca_kills', 0)}"
            )
        except Exception as e:
            logger.debug(f"Bridge outcome learning failed: {e}")

    def get_status_summary(self) -> str:
        """Get human-readable status summary."""
        stats = self.get_stats()
        tel = self.get_telemetry()
        
        return f"""
👑🦈 QUEEN-ORCA BRIDGE STATUS
═══════════════════════════════════════
🌉 Bridge: {'ACTIVE' if tel['bridge_active'] else 'OFFLINE'}
👑 Queen: {'CONNECTED' if tel['queen_connected'] else 'OFFLINE'}
🦈 Orca: {'CONNECTED' if tel['orca_connected'] else 'OFFLINE'}
🥷 Stealth: {'ENABLED' if tel['stealth_mode'] else 'DISABLED'}
⚠️  Threat: {self.threat_level}

📊 STATISTICS
───────────────────────────────────────
🎯 Signals Received: {tel['signals_received']}
🧠 Decisions Made: {tel['decisions_made']}
🎣 Hunts Initiated: {tel['hunts_initiated']}
🔪 Kills: {stats['orca_kills']} (W:{stats['orca_wins']} L:{stats['orca_losses']})
📈 Win Rate: {stats['win_rate']:.1%}
💰 Total P&L: ${stats['total_pnl']:.2f}
👑 Queen Approvals: {stats['queen_approvals']}
🚫 Queen Rejections: {stats['queen_rejections']}
🛡️ Threats Avoided: {stats['threats_avoided']}

📍 ACTIVE
───────────────────────────────────────
📊 Positions: {tel['active_positions']}
🎣 Pending Hunts: {tel['pending_hunts']}
🐋 Whale Alerts: {tel['whale_alerts']}
🏢 Firm Detections: {tel['firm_detections']}
═══════════════════════════════════════
"""
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # 🚀 ACTIVATION
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def activate(self):
        """Activate the bridge."""
        self.is_active = True
        self._telemetry['bridge_active'] = True
        
        if self.thought_bus:
            self.thought_bus.publish(Thought(
                source="queen_orca_bridge",
                topic="bridge.activated",
                payload={'timestamp': time.time()}
            ))
        
        logger.info("👑🦈 QUEEN-ORCA BRIDGE: ACTIVATED")
    
    def deactivate(self):
        """Deactivate the bridge."""
        self.is_active = False
        self._telemetry['bridge_active'] = False
        
        if self.thought_bus:
            self.thought_bus.publish(Thought(
                source="queen_orca_bridge",
                topic="bridge.deactivated",
                payload={'timestamp': time.time()}
            ))
        
        logger.info("👑🦈 QUEEN-ORCA BRIDGE: DEACTIVATED")


# ═══════════════════════════════════════════════════════════════════════════════════════
# 🏭 FACTORY FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════════════

_bridge_instance: Optional[QueenOrcaBridge] = None

def get_queen_orca_bridge() -> QueenOrcaBridge:
    """Get or create the singleton Queen-Orca Bridge."""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = QueenOrcaBridge()
    return _bridge_instance

def create_queen_orca_bridge(
    queen_voice: Optional[QueenHarmonicVoice] = None,
    orca_kill_cycle: Optional[Any] = None
) -> QueenOrcaBridge:
    """Create a new Queen-Orca Bridge with specified components."""
    global _bridge_instance
    _bridge_instance = QueenOrcaBridge(
        queen_voice=queen_voice,
        orca_kill_cycle=orca_kill_cycle
    )
    return _bridge_instance


# ═══════════════════════════════════════════════════════════════════════════════════════
# 🧪 TEST / DEMO
# ═══════════════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Queen-Orca Unified Bridge")
    parser.add_argument('--test', action='store_true', help='Run integration test')
    parser.add_argument('--status', action='store_true', help='Show status')
    args = parser.parse_args()
    
    print("═" * 80)
    print("👑🦈 QUEEN-ORCA UNIFIED BRIDGE - INTEGRATION TEST 🦈👑")
    print("═" * 80)
    
    # Create bridge
    bridge = get_queen_orca_bridge()
    bridge.activate()
    
    print(bridge.get_status_summary())
    
    if args.test:
        print("\n🧪 Running integration test...\n")
        
        # Simulate an opportunity signal
        test_signal = OrcaSignal(
            signal_type='opportunity',
            symbol='BTC/USD',
            exchange='alpaca',
            data={
                'price': 50000.0,
                'volume_ratio': 2.5,
                'momentum': 0.8
            },
            confidence=0.75,
            urgency='high'
        )
        
        print(f"📡 Test Signal: {test_signal.symbol} | Conf: {test_signal.confidence:.1%}")
        
        # Evaluate
        decision = bridge._queen_evaluate_opportunity(test_signal)
        
        if decision:
            print(f"✅ Queen Decision: {decision.command.name} | Conf: {decision.confidence:.1%}")
            print(f"   Reasoning: {decision.reasoning}")
        else:
            print("🚫 Queen rejected opportunity")
        
        print("\n📊 Final Status:")
        print(bridge.get_status_summary())
    
    print("\n✅ Queen-Orca Bridge ready for action!")
