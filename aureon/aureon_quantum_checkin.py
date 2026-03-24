"""
🌌 AUREON QUANTUM CHECK-IN PROTOCOL 🌌

The missing piece: SUPERPOSITION until OBSERVATION.

All systems must check in before execution collapses the wavefunction.
Like bats sending echos and whales singing through the mycelium -
every piece of the puzzle confirms before we act.

"Top to bottom, left to right, full circle looped feedback"

Based on the Harmonic Nexus Whitepaper principles:
Λ(t) = S(t) + O(t) + E(t)

Where:
- S(t) = Substrate (all systems in superposition)
- O(t) = Observer (the execution that collapses the wave)
- E(t) = Echo (feedback that travels back through mycelium)
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, Set, Optional, List, Callable, Any
from enum import Enum
from collections import defaultdict
from datetime import datetime
import threading
import logging

logger = logging.getLogger(__name__)


class QuantumState(Enum):
    """The state of a signal in the quantum field"""
    SUPERPOSITION = "⚛️ SUPERPOSITION"  # All possibilities exist
    COLLAPSING = "🌀 COLLAPSING"        # Check-ins in progress
    COLLAPSED = "💫 COLLAPSED"           # Observation complete - ready to execute
    EXECUTED = "✅ EXECUTED"             # Action taken
    DECOHERENT = "❌ DECOHERENT"         # Failed - lost coherence


@dataclass
class QuantumSignal:
    """A signal in superposition waiting for all systems to check in"""
    signal_id: str
    action: str  # BUY, SELL, CONVERT
    asset: str
    exchange: str
    amount: float
    price: float
    confidence: float
    created_at: float = field(default_factory=time.time)
    
    # Quantum state tracking
    state: QuantumState = QuantumState.SUPERPOSITION
    required_systems: Set[str] = field(default_factory=set)
    checked_in_systems: Dict[str, Dict] = field(default_factory=dict)
    
    # Echo data (feedback from each system)
    echoes: Dict[str, Any] = field(default_factory=dict)
    
    # Coherence score (product of all system confidences)
    coherence: float = 1.0
    
    def check_in(self, system: str, approval: bool, confidence: float, echo_data: Optional[Dict] = None):
        """System checks in with its vote"""
        self.checked_in_systems[system] = {
            'approved': approval,
            'confidence': confidence,
            'timestamp': time.time(),
            'echo': echo_data or {}
        }
        
        if echo_data:
            self.echoes[system] = echo_data
            
        # Update coherence (geometric mean of confidences)
        if approval:
            self.coherence *= confidence
        else:
            self.coherence *= (1 - confidence)  # Negative contribution
            
        # Check if all required systems have checked in
        if set(self.checked_in_systems.keys()) >= self.required_systems:
            self._maybe_collapse()
    
    def _maybe_collapse(self):
        """Attempt to collapse the wavefunction"""
        if self.state != QuantumState.SUPERPOSITION:
            return
            
        self.state = QuantumState.COLLAPSING
        
        # Count approvals
        approvals = sum(1 for v in self.checked_in_systems.values() if v['approved'])
        total = len(self.checked_in_systems)
        
        # Require majority approval AND positive coherence
        if approvals > total / 2 and self.coherence > 0.3:
            self.state = QuantumState.COLLAPSED
        else:
            self.state = QuantumState.DECOHERENT
            
    @property
    def is_ready(self) -> bool:
        """Is this signal ready for execution?"""
        return self.state == QuantumState.COLLAPSED
        
    @property
    def age_seconds(self) -> float:
        """How long has this signal been in superposition?"""
        return time.time() - self.created_at


class QuantumCheckInProtocol:
    """
    🔮 THE QUANTUM CHECK-IN PROTOCOL
    
    All systems must echo through the mycelium before execution.
    This ensures FULL CIRCLE FEEDBACK - nothing gets lost.
    """
    
    # The systems that must check in before execution
    REQUIRED_SYSTEMS = {
        'lighthouse',    # Pattern detection
        'harmonic',      # Frequency alignment
        'quantum',       # Geometric analysis
        'mycelium',      # Network consensus
        'probability',   # Nexus prediction
        'risk',          # Capital protection
    }
    
    # Minimum systems required (allows degraded mode)
    MIN_REQUIRED = 3
    
    # Maximum age before decoherence (seconds)
    MAX_SUPERPOSITION_AGE = 30.0
    
    def __init__(self, mycelium=None, thought_bus=None):
        self.pending_signals: Dict[str, QuantumSignal] = {}
        self.execution_callbacks: List[Callable] = []
        self.mycelium = mycelium
        self.thought_bus = thought_bus
        self.lock = threading.RLock()
        
        # Statistics
        self.stats = {
            'signals_created': 0,
            'signals_collapsed': 0,
            'signals_decoherent': 0,
            'signals_executed': 0,
            'total_echoes': 0,
        }
        
        # System health tracking
        self.system_health: Dict[str, Dict] = defaultdict(lambda: {
            'last_checkin': 0,
            'total_checkins': 0,
            'approvals': 0,
            'rejections': 0,
        })
        
        logger.info("🌌 Quantum Check-In Protocol initialized")
        logger.info(f"   Required systems: {self.REQUIRED_SYSTEMS}")
        logger.info(f"   Minimum required: {self.MIN_REQUIRED}")
        
    def register_execution_callback(self, callback: Callable):
        """Register a callback to be called when a signal collapses and is ready"""
        self.execution_callbacks.append(callback)
        
    def create_signal(
        self,
        action: str,
        asset: str,
        exchange: str,
        amount: float,
        price: float,
        confidence: float,
        required_systems: Optional[Set[str]] = None
    ) -> str:
        """
        🚀 Create a new signal in SUPERPOSITION
        
        The signal exists in all states until observed (executed).
        All required systems must check in before collapse.
        """
        signal_id = f"QS-{uuid.uuid4().hex[:8]}"
        
        with self.lock:
            signal = QuantumSignal(
                signal_id=signal_id,
                action=action,
                asset=asset,
                exchange=exchange,
                amount=amount,
                price=price,
                confidence=confidence,
                required_systems=required_systems or self.REQUIRED_SYSTEMS.copy()
            )
            
            self.pending_signals[signal_id] = signal
            self.stats['signals_created'] += 1
            
        # 🦇 SEND ECHO - Broadcast to all systems for check-in
        self._broadcast_echo(signal)
        
        logger.info(f"⚛️ Signal {signal_id} created in SUPERPOSITION")
        logger.info(f"   {action} {asset} on {exchange} | Amount: {amount:.4f} | Conf: {confidence:.2%}")
        logger.info(f"   Awaiting check-ins from: {signal.required_systems}")
        
        return signal_id
        
    def _broadcast_echo(self, signal: QuantumSignal):
        """🦇 Send echo through the mycelium to all systems"""
        echo_payload = {
            'signal_id': signal.signal_id,
            'action': signal.action,
            'asset': signal.asset,
            'exchange': signal.exchange,
            'amount': signal.amount,
            'price': signal.price,
            'confidence': signal.confidence,
            'timestamp': signal.created_at,
            'required_systems': list(signal.required_systems),
        }
        
        # Send through mycelium if available
        if self.mycelium and hasattr(self.mycelium, 'broadcast_event'):
            try:
                self.mycelium.broadcast_event('quantum.echo.request', echo_payload)
                logger.debug(f"🦇 Echo sent through mycelium: {signal.signal_id}")
            except Exception as e:
                logger.warning(f"Mycelium echo failed: {e}")
                
        # Send through thought bus if available
        if self.thought_bus and hasattr(self.thought_bus, 'publish'):
            try:
                from aureon_thought_bus import Thought
                self.thought_bus.publish(Thought(
                    source='quantum_checkin',
                    topic='quantum.echo.request',
                    trace_id=signal.signal_id,
                    payload=echo_payload
                ))
                logger.debug(f"🦇 Echo sent through thought bus: {signal.signal_id}")
            except Exception as e:
                logger.warning(f"ThoughtBus echo failed: {e}")
                
    def check_in(
        self,
        signal_id: str,
        system: str,
        approved: bool,
        confidence: float,
        echo_data: Optional[Dict] = None
    ) -> Optional[QuantumSignal]:
        """
        🐋 System checks in with its analysis
        
        Like a whale singing back through the deep - each system
        confirms it has analyzed the signal and provides its vote.
        """
        with self.lock:
            if signal_id not in self.pending_signals:
                logger.warning(f"Check-in for unknown signal: {signal_id}")
                return None
                
            signal = self.pending_signals[signal_id]
            
            # Record the check-in
            signal.check_in(system, approved, confidence, echo_data)
            self.stats['total_echoes'] += 1
            
            # Update system health
            self.system_health[system]['last_checkin'] = time.time()
            self.system_health[system]['total_checkins'] += 1
            if approved:
                self.system_health[system]['approvals'] += 1
            else:
                self.system_health[system]['rejections'] += 1
                
            status = "✅ APPROVED" if approved else "❌ REJECTED"
            logger.info(f"🐋 {system.upper()} checked in for {signal_id}: {status} ({confidence:.2%})")
            
            if echo_data:
                logger.debug(f"   Echo data: {echo_data}")
                
            # Check state after this check-in
            if signal.state == QuantumState.COLLAPSED:
                self.stats['signals_collapsed'] += 1
                logger.info(f"💫 Signal {signal_id} COLLAPSED! Ready for execution")
                logger.info(f"   Final coherence: {signal.coherence:.4f}")
                self._trigger_execution(signal)
                
            elif signal.state == QuantumState.DECOHERENT:
                self.stats['signals_decoherent'] += 1
                logger.warning(f"❌ Signal {signal_id} became DECOHERENT - execution blocked")
                del self.pending_signals[signal_id]
                
            return signal
            
    def _trigger_execution(self, signal: QuantumSignal):
        """Execute the collapsed signal"""
        signal.state = QuantumState.EXECUTED
        self.stats['signals_executed'] += 1
        
        # Remove from pending
        if signal.signal_id in self.pending_signals:
            del self.pending_signals[signal.signal_id]
            
        # Call all registered execution callbacks
        execution_payload = {
            'signal_id': signal.signal_id,
            'action': signal.action,
            'asset': signal.asset,
            'exchange': signal.exchange,
            'amount': signal.amount,
            'price': signal.price,
            'confidence': signal.confidence,
            'coherence': signal.coherence,
            'echoes': signal.echoes,
            'checked_in_systems': list(signal.checked_in_systems.keys()),
        }
        
        for callback in self.execution_callbacks:
            try:
                callback(execution_payload)
            except Exception as e:
                logger.error(f"Execution callback error: {e}")
                
        # Send execution confirmation through mycelium
        if self.mycelium and hasattr(self.mycelium, 'broadcast_event'):
            try:
                self.mycelium.broadcast_event('quantum.executed', execution_payload)
            except:
                pass
                
    def cleanup_stale_signals(self):
        """Remove signals that have been in superposition too long"""
        now = time.time()
        with self.lock:
            stale = [
                sid for sid, sig in self.pending_signals.items()
                if sig.age_seconds > self.MAX_SUPERPOSITION_AGE
            ]
            
            for sid in stale:
                signal = self.pending_signals[sid]
                signal.state = QuantumState.DECOHERENT
                self.stats['signals_decoherent'] += 1
                logger.warning(f"⏰ Signal {sid} timed out in superposition ({signal.age_seconds:.1f}s)")
                logger.warning(f"   Missing check-ins from: {signal.required_systems - set(signal.checked_in_systems.keys())}")
                del self.pending_signals[sid]
                
        return len(stale)
        
    def force_check_in(self, signal_id: str, system: str, confidence: float = 0.5):
        """Force a check-in when a system is unavailable (degraded mode)"""
        return self.check_in(signal_id, system, True, confidence, {'forced': True})
        
    def get_pending_signals(self) -> List[QuantumSignal]:
        """Get all signals currently in superposition"""
        with self.lock:
            return list(self.pending_signals.values())
            
    def get_system_health(self) -> Dict:
        """Get health status of all systems"""
        now = time.time()
        health = {}
        for system, data in self.system_health.items():
            last = data['last_checkin']
            health[system] = {
                **data,
                'seconds_since_checkin': now - last if last > 0 else float('inf'),
                'approval_rate': data['approvals'] / max(1, data['total_checkins']),
            }
        return health
        
    def get_stats(self) -> Dict:
        """Get protocol statistics"""
        return {
            **self.stats,
            'pending_signals': len(self.pending_signals),
            'execution_rate': self.stats['signals_executed'] / max(1, self.stats['signals_created']),
            'coherence_rate': self.stats['signals_collapsed'] / max(1, self.stats['signals_created']),
        }
        
    def print_status(self):
        """Print current protocol status"""
        stats = self.get_stats()
        print("\n" + "=" * 60)
        print("🌌 QUANTUM CHECK-IN PROTOCOL STATUS")
        print("=" * 60)
        print(f"   Signals Created:    {stats['signals_created']}")
        print(f"   Signals Collapsed:  {stats['signals_collapsed']} ({stats['coherence_rate']:.1%})")
        print(f"   Signals Decoherent: {stats['signals_decoherent']}")
        print(f"   Signals Executed:   {stats['signals_executed']} ({stats['execution_rate']:.1%})")
        print(f"   Total Echoes:       {stats['total_echoes']}")
        print(f"   Pending:            {stats['pending_signals']}")
        
        if self.pending_signals:
            print("\n   📡 PENDING SIGNALS:")
            for sig in self.pending_signals.values():
                missing = sig.required_systems - set(sig.checked_in_systems.keys())
                print(f"      {sig.signal_id}: {sig.action} {sig.asset} | Age: {sig.age_seconds:.1f}s | Missing: {missing}")
                
        health = self.get_system_health()
        if health:
            print("\n   🏥 SYSTEM HEALTH:")
            for system, data in sorted(health.items()):
                status = "🟢" if data['seconds_since_checkin'] < 60 else "🟡" if data['seconds_since_checkin'] < 300 else "🔴"
                print(f"      {status} {system.upper()}: {data['total_checkins']} check-ins | {data['approval_rate']:.1%} approval")
                
        print("=" * 60 + "\n")


# ═══════════════════════════════════════════════════════════════
# 🔌 SYSTEM CHECK-IN ADAPTERS
# ═══════════════════════════════════════════════════════════════

class LighthouseCheckIn:
    """Adapter for Lighthouse system to check in"""
    
    def __init__(self, protocol: QuantumCheckInProtocol, lighthouse=None):
        self.protocol = protocol
        self.lighthouse = lighthouse
        
    def analyze_and_check_in(self, signal_id: str, asset: str, price: float, momentum: float) -> bool:
        """Lighthouse analyzes and checks in"""
        try:
            # Get lighthouse analysis if available
            confidence = 0.6  # Default
            approved = True
            echo_data = {}
            
            if self.lighthouse:
                if hasattr(self.lighthouse, 'scan_for_patterns'):
                    patterns = self.lighthouse.scan_for_patterns({asset: {'price': price, 'momentum': momentum}})
                    echo_data['patterns'] = patterns
                    
                    # Check for dangerous patterns
                    for p in patterns:
                        if p.get('type') in ['coherence_collapse', 'phase_reset']:
                            approved = False
                            confidence = 0.3
                            break
                        elif p.get('type') in ['harmonic_convergence', 'schumann_alignment']:
                            confidence = min(0.95, confidence + 0.2)
                            
            self.protocol.check_in(signal_id, 'lighthouse', approved, confidence, echo_data)
            return approved
            
        except Exception as e:
            logger.error(f"Lighthouse check-in error: {e}")
            self.protocol.force_check_in(signal_id, 'lighthouse', 0.5)
            return True


class HarmonicCheckIn:
    """Adapter for Harmonic Waveform system to check in"""
    
    def __init__(self, protocol: QuantumCheckInProtocol, harmonic=None):
        self.protocol = protocol
        self.harmonic = harmonic
        
    def analyze_and_check_in(self, signal_id: str, asset: str) -> bool:
        """Harmonic system analyzes and checks in"""
        try:
            confidence = 0.6
            approved = True
            echo_data = {}
            
            if self.harmonic:
                if hasattr(self.harmonic, 'get_state'):
                    state = self.harmonic.get_state()
                    echo_data['frequency'] = state.get('global_frequency', 0)
                    echo_data['coherence'] = state.get('coherence', 0)
                    echo_data['phase'] = state.get('phase', 'UNKNOWN')
                    
                    # Check frequency alignment
                    freq = state.get('global_frequency', 0)
                    if 400 <= freq <= 520:  # Golden zone
                        confidence = 0.85
                    elif freq < 200 or freq > 600:  # Distortion
                        confidence = 0.4
                        
                    # Check coherence
                    if state.get('coherence', 0) < 0.4:
                        approved = False
                        confidence = 0.3
                        
            self.protocol.check_in(signal_id, 'harmonic', approved, confidence, echo_data)
            return approved
            
        except Exception as e:
            logger.error(f"Harmonic check-in error: {e}")
            self.protocol.force_check_in(signal_id, 'harmonic', 0.5)
            return True


class QuantumTelescopeCheckIn:
    """Adapter for Quantum Telescope to check in"""
    
    def __init__(self, protocol: QuantumCheckInProtocol, telescope=None):
        self.protocol = protocol
        self.telescope = telescope
        
    def analyze_and_check_in(self, signal_id: str, asset: str, price: float, volume: float = 0) -> bool:
        """Quantum Telescope analyzes and checks in"""
        try:
            confidence = 0.6
            approved = True
            echo_data = {}
            
            if self.telescope:
                if hasattr(self.telescope, 'observe_light_beam'):
                    observation = self.telescope.observe_light_beam(
                        price=price,
                        volume=volume,
                        sentiment=0.5
                    )
                    echo_data['spectrum'] = observation
                    
                    # Check spectral analysis
                    if observation.get('signal_strength', 0) > 0.7:
                        confidence = 0.8
                    elif observation.get('signal_strength', 0) < 0.3:
                        confidence = 0.4
                        
            self.protocol.check_in(signal_id, 'quantum', approved, confidence, echo_data)
            return approved
            
        except Exception as e:
            logger.error(f"Quantum Telescope check-in error: {e}")
            self.protocol.force_check_in(signal_id, 'quantum', 0.5)
            return True


class MyceliumCheckIn:
    """Adapter for Mycelium Network to check in"""
    
    def __init__(self, protocol: QuantumCheckInProtocol, mycelium=None):
        self.protocol = protocol
        self.mycelium = mycelium
        
    def analyze_and_check_in(self, signal_id: str, asset: str, action: str) -> bool:
        """Mycelium network provides consensus check-in"""
        try:
            confidence = 0.6
            approved = True
            echo_data = {}
            
            if self.mycelium:
                if hasattr(self.mycelium, 'get_consensus'):
                    consensus = self.mycelium.get_consensus(asset)
                    echo_data['consensus'] = consensus
                    
                    if action.upper() == 'BUY':
                        approved = consensus in ['BULLISH', 'STRONG_BUY', 'BUY']
                    elif action.upper() == 'SELL':
                        approved = consensus in ['BEARISH', 'STRONG_SELL', 'SELL']
                        
                    confidence = 0.8 if approved else 0.4
                    
                if hasattr(self.mycelium, 'get_network_health'):
                    health = self.mycelium.get_network_health()
                    echo_data['network_health'] = health
                    
            self.protocol.check_in(signal_id, 'mycelium', approved, confidence, echo_data)
            return approved
            
        except Exception as e:
            logger.error(f"Mycelium check-in error: {e}")
            self.protocol.force_check_in(signal_id, 'mycelium', 0.5)
            return True


class ProbabilityCheckIn:
    """Adapter for Probability Nexus to check in"""
    
    def __init__(self, protocol: QuantumCheckInProtocol, nexus=None):
        self.protocol = protocol
        self.nexus = nexus
        
    def analyze_and_check_in(self, signal_id: str, asset: str, action: str, price: float, momentum: float) -> bool:
        """Probability Nexus analyzes and checks in"""
        try:
            confidence = 0.6
            approved = True
            echo_data = {}
            
            if self.nexus:
                if hasattr(self.nexus, 'get_signal'):
                    signal = self.nexus.get_signal(asset, price, momentum)
                    echo_data['nexus_signal'] = signal
                    
                    # Check if nexus agrees with action
                    if signal.get('direction') == action.upper():
                        confidence = signal.get('confidence', 0.6)
                        approved = confidence > 0.5
                    else:
                        confidence = 0.3
                        approved = False
                        
            self.protocol.check_in(signal_id, 'probability', approved, confidence, echo_data)
            return approved
            
        except Exception as e:
            logger.error(f"Probability check-in error: {e}")
            self.protocol.force_check_in(signal_id, 'probability', 0.5)
            return True


class RiskCheckIn:
    """Adapter for Risk Management to check in"""
    
    def __init__(self, protocol: QuantumCheckInProtocol, risk_manager=None, max_position_pct: float = 0.1):
        self.protocol = protocol
        self.risk_manager = risk_manager
        self.max_position_pct = max_position_pct
        
    def analyze_and_check_in(self, signal_id: str, exchange: str, amount: float, portfolio_value: float) -> bool:
        """Risk manager analyzes and checks in"""
        try:
            confidence = 0.7
            approved = True
            echo_data = {}
            
            # Basic position size check
            position_pct = amount / max(1, portfolio_value)
            echo_data['position_pct'] = position_pct
            
            if position_pct > self.max_position_pct:
                approved = False
                confidence = 0.2
                echo_data['reason'] = 'position_too_large'
                
            # Check with risk manager if available
            if self.risk_manager and hasattr(self.risk_manager, 'check_risk'):
                risk_ok = self.risk_manager.check_risk(exchange, amount)
                if not risk_ok:
                    approved = False
                    confidence = 0.3
                    echo_data['reason'] = 'risk_limit_exceeded'
                    
            self.protocol.check_in(signal_id, 'risk', approved, confidence, echo_data)
            return approved
            
        except Exception as e:
            logger.error(f"Risk check-in error: {e}")
            self.protocol.force_check_in(signal_id, 'risk', 0.5)
            return True


# ═══════════════════════════════════════════════════════════════
# 🎯 UNIFIED QUANTUM GATE - THE FINAL ARBITER
# ═══════════════════════════════════════════════════════════════

class QuantumExecutionGate:
    """
    🎯 THE QUANTUM EXECUTION GATE
    
    The final arbiter that ensures ALL systems have checked in
    before any trade is executed. This is the "observation"
    that collapses the quantum wavefunction.
    
    "Top to bottom, left to right, full circle looped feedback"
    """
    
    def __init__(
        self,
        lighthouse=None,
        harmonic=None,
        telescope=None,
        mycelium=None,
        nexus=None,
        risk_manager=None
    ):
        # Initialize the quantum protocol
        self.protocol = QuantumCheckInProtocol(mycelium=mycelium)
        
        # Initialize check-in adapters
        self.lighthouse_checkin = LighthouseCheckIn(self.protocol, lighthouse)
        self.harmonic_checkin = HarmonicCheckIn(self.protocol, harmonic)
        self.quantum_checkin = QuantumTelescopeCheckIn(self.protocol, telescope)
        self.mycelium_checkin = MyceliumCheckIn(self.protocol, mycelium)
        self.probability_checkin = ProbabilityCheckIn(self.protocol, nexus)
        self.risk_checkin = RiskCheckIn(self.protocol, risk_manager)
        
        # Store references
        self.lighthouse = lighthouse
        self.harmonic = harmonic
        self.telescope = telescope
        self.mycelium = mycelium
        self.nexus = nexus
        
        # Execution callback
        self._execution_handler = None
        
        logger.info("🎯 Quantum Execution Gate initialized")
        logger.info("   All systems must check in before execution!")
        
    def set_execution_handler(self, handler: Callable):
        """Set the handler that will be called when a signal collapses"""
        self._execution_handler = handler
        self.protocol.register_execution_callback(handler)
        
    async def request_execution(
        self,
        action: str,
        asset: str,
        exchange: str,
        amount: float,
        price: float,
        confidence: float,
        portfolio_value: float = 100,
        momentum: float = 0,
        volume: float = 0
    ) -> Optional[str]:
        """
        🚀 Request execution through the quantum gate
        
        This creates a signal in SUPERPOSITION and triggers
        all systems to check in. When all systems have checked in
        and agree, the signal COLLAPSES and execution occurs.
        """
        # Create the signal in superposition
        signal_id = self.protocol.create_signal(
            action=action,
            asset=asset,
            exchange=exchange,
            amount=amount,
            price=price,
            confidence=confidence
        )
        
        # Trigger all system check-ins asynchronously
        await asyncio.gather(
            asyncio.to_thread(self.lighthouse_checkin.analyze_and_check_in, signal_id, asset, price, momentum),
            asyncio.to_thread(self.harmonic_checkin.analyze_and_check_in, signal_id, asset),
            asyncio.to_thread(self.quantum_checkin.analyze_and_check_in, signal_id, asset, price, volume),
            asyncio.to_thread(self.mycelium_checkin.analyze_and_check_in, signal_id, asset, action),
            asyncio.to_thread(self.probability_checkin.analyze_and_check_in, signal_id, asset, action, price, momentum),
            asyncio.to_thread(self.risk_checkin.analyze_and_check_in, signal_id, exchange, amount, portfolio_value),
            return_exceptions=True
        )
        
        return signal_id
        
    def sync_request_execution(
        self,
        action: str,
        asset: str,
        exchange: str,
        amount: float,
        price: float,
        confidence: float,
        portfolio_value: float = 100,
        momentum: float = 0,
        volume: float = 0
    ) -> Optional[str]:
        """Synchronous version of request_execution"""
        # Create the signal
        signal_id = self.protocol.create_signal(
            action=action,
            asset=asset,
            exchange=exchange,
            amount=amount,
            price=price,
            confidence=confidence
        )
        
        # Trigger all check-ins synchronously
        self.lighthouse_checkin.analyze_and_check_in(signal_id, asset, price, momentum)
        self.harmonic_checkin.analyze_and_check_in(signal_id, asset)
        self.quantum_checkin.analyze_and_check_in(signal_id, asset, price, volume)
        self.mycelium_checkin.analyze_and_check_in(signal_id, asset, action)
        self.probability_checkin.analyze_and_check_in(signal_id, asset, action, price, momentum)
        self.risk_checkin.analyze_and_check_in(signal_id, exchange, amount, portfolio_value)
        
        return signal_id
        
    def get_status(self):
        """Get gate status"""
        return self.protocol.get_stats()
        
    def print_status(self):
        """Print gate status"""
        self.protocol.print_status()


# ═══════════════════════════════════════════════════════════════
# 🧪 TEST THE QUANTUM GATE
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    print("\n" + "🌌" * 30)
    print("   QUANTUM CHECK-IN PROTOCOL TEST")
    print("🌌" * 30 + "\n")
    
    # Create the gate
    gate = QuantumExecutionGate()
    
    # Set execution handler
    def on_execution(payload):
        print("\n" + "💫" * 20)
        print("   SIGNAL COLLAPSED - EXECUTING!")
        print(f"   Action: {payload['action']} {payload['asset']}")
        print(f"   Exchange: {payload['exchange']}")
        print(f"   Amount: {payload['amount']}")
        print(f"   Coherence: {payload['coherence']:.4f}")
        print(f"   Systems: {payload['checked_in_systems']}")
        print("💫" * 20 + "\n")
        
    gate.set_execution_handler(on_execution)
    
    # Test signal
    print("📡 Creating test signal...")
    signal_id = gate.sync_request_execution(
        action='SELL',
        asset='CAKE',
        exchange='binance',
        amount=3.75,
        price=2.0,
        confidence=0.8,
        portfolio_value=100,
        momentum=0.05
    )
    
    # Print status
    gate.print_status()
