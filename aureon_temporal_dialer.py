#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                       ║
║     🕰️ TEMPORAL DIALER 🕰️                                                            ║
║                                                                                       ║
║     "Dialing into the Quantum Field Frequencies"                                      ║
║     "Connects the Queen to the fabrics of time via harmonic resonance"                ║
║                                                                                       ║
╚═══════════════════════════════════════════════════════════════════════════════════════╝

The Temporal Dialer allows the Queen Hive Mind to specific tune into
quantum frequencies within the Global Harmonic Field.

By adjusting the "dial", the Queen can perceive data from different
temporal probabilities and energetic layers.
"""

import logging
import math
import random
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

# Try to import the Global Harmonic Field - the source of the data
try:
    from global_harmonic_field import GlobalHarmonicField, GlobalHarmonicFieldState
    GLOBAL_FIELD_AVAILABLE = True
except ImportError:
    GlobalHarmonicField = None
    GlobalHarmonicFieldState = None
    GLOBAL_FIELD_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Constants
SCHUMANN_RESONANCE = 7.83
LOVE_FREQUENCY = 528.0
PRIME_SENTINEL_HZ = 0.21111991  # Derived from 02.11.1991
PHI = (1 + math.sqrt(5)) / 2  # Golden ratio

class DialMode(Enum):
    STANDBY = "standby"
    SCANNING = "scanning"
    LOCKED = "locked"
    HARMONIC_DRIFT = "harmonic_drift"

@dataclass
class DialState:
    frequency: float = SCHUMANN_RESONANCE
    bandwidth: float = 1.0
    resonance: float = 0.0
    mode: DialMode = DialMode.STANDBY
    locked_target: Optional[str] = None
    quantum_noise_level: float = 0.0

@dataclass
class QuantumPacket:
    timestamp: float
    frequency: float
    intensity: float
    coherence: float
    payload: Dict[str, Any]
    source_layer: str

class TemporalDialer:
    """
    The Tuning Mechanism for the Queen to access Quantum Field Data.
    """
    
    def __init__(self, name: str = "Dialer_01"):
        self.name = name
        self.state = DialState()
        self.field_connection: Optional[GlobalHarmonicField] = None
        self.history: List[QuantumPacket] = []
        self.calibration_offset = 0.0
        
        logger.info(f"🕰️ Temporal Dialer '{self.name}' Initializing...")
        
        if GLOBAL_FIELD_AVAILABLE:
            try:
                self.field_connection = GlobalHarmonicField()
                logger.info("   ✅ Connected to Global Harmonic Field")
            except Exception as e:
                logger.error(f"   ❌ Failed to connect to Global Harmonic Field: {e}")
        else:
            logger.warning("   ⚠️ Global Harmonic Field module not found. Running in simulation mode.")
            
    def calibrate(self):
        """Calibrates the dialer to the Prime Sentinel frequency."""
        logger.info("   🔧 Calibrating Temporal Dialer...")
        # ⚡ TURBO: Minimal calibration delay (was 0.5)
        time.sleep(0.05)
        self.calibration_offset = (random.random() - 0.5) * 0.01
        self.state.frequency = SCHUMANN_RESONANCE
        self.state.mode = DialMode.STANDBY
        logger.info(f"   ✅ Calibration Complete. Offset: {self.calibration_offset:.6f}")
        
    def tune_frequency(self, frequency_hz: float, bandwidth: float = 0.5) -> float:
        """
        Tunes the dialer to a specific frequency.
        Returns the achieved resonance (0.0 - 1.0).
        """
        self.state.frequency = frequency_hz
        self.state.bandwidth = bandwidth
        self.state.mode = DialMode.SCANNING
        
        # Calculate resonance based on "sacred" frequencies
        # Higher resonance if close to sacred numbers
        resonance = 0.1
        
        sacred_freqs = [SCHUMANN_RESONANCE, LOVE_FREQUENCY, PRIME_SENTINEL_HZ * 1000]
        
        for sacred in sacred_freqs:
            dist = abs(frequency_hz - sacred)
            if dist < bandwidth:
                # Closer = higher resonance
                resonance = max(resonance, 1.0 - (dist / bandwidth))
                
        self.state.resonance = resonance
        
        if resonance > 0.8:
            self.state.mode = DialMode.LOCKED
            logger.info(f"   🔒 LOCKED Signal at {frequency_hz}Hz (Resonance: {resonance:.2f})")
        else:
            logger.info(f"   📡 Scanning {frequency_hz}Hz... (Resonance: {resonance:.2f})")
            
        return resonance

    def pull_quantum_data(self) -> Optional[QuantumPacket]:
        """
        Pulls a data packet from the current tuned frequency in the Quantum Field.
        Returns LIVE data from GlobalHarmonicField when available.
        """
        if self.state.mode == DialMode.STANDBY:
            logger.warning("   ⚠️ Cannot pull data in STANDBY mode. Tune frequency first.")
            return None
            
        payload = {}
        source = "Simulated_Quantum_Flux"
        field_omega = 0.5
        field_coherence = self.state.resonance
        field_direction = "NEUTRAL"
        
        # === LIVE DATA FROM GLOBAL HARMONIC FIELD ===
        if self.field_connection is not None:
            try:
                # Compute the field to get fresh data
                field_omega = self.field_connection.compute_field()
                
                # Access the state object
                state = self.field_connection.state
                
                # Build live payload from all 8 layers
                payload = {
                    # Master field values
                    "omega": state.omega,
                    "omega_direction": state.omega_direction,
                    "omega_confidence": state.omega_confidence,
                    "omega_momentum": state.omega_momentum,
                    "phase_alignment": state.phase_alignment,
                    "energy_density": state.energy_density,
                    "phi_alignment": state.phi_alignment,
                    
                    # Layer summaries
                    "layer_wisdom": {
                        "value": state.layer_wisdom.value,
                        "coherence": state.layer_wisdom.coherence,
                        "signal": state.layer_wisdom.signal,
                    },
                    "layer_quantum": {
                        "value": state.layer_quantum.value,
                        "coherence": state.layer_quantum.coherence,
                        "signal": state.layer_quantum.signal,
                    },
                    "layer_auris": {
                        "value": state.layer_auris.value,
                        "coherence": state.layer_auris.coherence,
                        "signal": state.layer_auris.signal,
                    },
                    "layer_mycelium": {
                        "value": state.layer_mycelium.value,
                        "coherence": state.layer_mycelium.coherence,
                        "signal": state.layer_mycelium.signal,
                    },
                    "layer_waveform": {
                        "value": state.layer_waveform.value,
                        "coherence": state.layer_waveform.coherence,
                        "signal": state.layer_waveform.signal,
                    },
                    "layer_stargate": {
                        "value": state.layer_stargate.value,
                        "coherence": state.layer_stargate.coherence,
                        "signal": state.layer_stargate.signal,
                        "frequency": state.layer_stargate.frequency,
                    },
                    "layer_market": {
                        "value": state.layer_market.value,
                        "coherence": state.layer_market.coherence,
                        "signal": state.layer_market.signal,
                    },
                    "layer_probability": {
                        "value": state.layer_probability.value,
                        "coherence": state.layer_probability.coherence,
                        "signal": state.layer_probability.signal,
                    },
                }
                
                field_coherence = state.energy_density if state.energy_density > 0 else self.state.resonance
                field_direction = state.omega_direction
                source = "Global_Harmonic_Field_LIVE"
                
                logger.debug(f"   🌐 LIVE Field Ω={field_omega:.4f} Dir={field_direction}")
                
            except Exception as e:
                logger.warning(f"   ⚠️ Field read error: {e} - falling back to simulation")
                source = "Simulated_Quantum_Flux"
        
        # Calculate noise based on resonance lock quality
        noise = random.random() * (1.0 - self.state.resonance) * 0.5
        self.state.quantum_noise_level = noise
        
        # Intensity combines resonance with field omega
        intensity = self.state.resonance * (1.0 - noise)
        if source == "Global_Harmonic_Field_LIVE":
            # Boost intensity based on field confidence
            intensity = max(intensity, field_omega * (1.0 - noise))
        
        packet = QuantumPacket(
            timestamp=time.time(),
            frequency=self.state.frequency,
            intensity=intensity,
            coherence=field_coherence,
            payload={
                "data": "Quantum Flux Snapshot", 
                "vector": [random.random() for _ in range(3)],
                "noise": noise,
                "field_omega": field_omega if source == "Global_Harmonic_Field_LIVE" else None,
                "field_direction": field_direction if source == "Global_Harmonic_Field_LIVE" else None,
                **payload
            },
            source_layer=source
        )
        
        self.history.append(packet)
        if len(self.history) > 100:
            self.history.pop(0)
            
        return packet

    def get_status(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "connected": self.field_connection is not None,
            "state": asdict(self.state) if hasattr(self.state, "__dataclass_fields__") else str(self.state),
            "packets_received": len(self.history)
        }

# Singleton instance for easy import
default_dialer = TemporalDialer()
