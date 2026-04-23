from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import time
import math
import random
from dataclasses import dataclass
from typing import Dict, List, Any, Tuple

@dataclass
class LatticeState:
    phase: str          # "DISTORTION", "UNLOCK", "CLEANSE"
    frequency: float    # 440.0, 198.4, 528.0
    risk_mod: float     # Multiplier for position size
    tp_mod: float       # Multiplier for Take Profit
    sl_mod: float       # Multiplier for Stop Loss
    field_purity: float # 0.0 - 1.0, protection from distortion
    description: str


class TriadicEnvelope:
    """
    🔮 TRIADIC ENVELOPE PROTOCOL
    ============================
    Protects trading signals from market noise (440Hz distortion).
    
    Protocol:
    1. Green Proper Borax x3 (528 Hz Solvent) - Clears Distortion
    2. Payload (Signal) - Transmits through cleared field
    3. Ahhhhh Bannnnn x3 (198.4 Hz Key) - Locks Decision
    """
    
    # Field Purity Factors for each frequency
    PURITY_FACTORS = {
        528.0: 0.992,   # Love Frequency - Maximum protection
        198.4: 0.850,   # Belfast Key - Strong protection  
        440.0: 0.000,   # Mars Distortion - No protection
    }
    
    # Base distortion level in market signals
    BASE_DISTORTION = 0.40  # 40% noise in raw market data
    
    @classmethod
    def apply_envelope(cls, signal: Dict, lattice_frequency: float) -> Tuple[Dict, float, bool]:
        """
        Apply the Triadic Envelope to a trading signal.
        
        Returns: (filtered_signal, integrity_score, memory_locked)
        """
        purity = cls.PURITY_FACTORS.get(lattice_frequency, 0.5)
        effective_distortion = cls.BASE_DISTORTION * (1 - purity)
        
        # Calculate integrity - how much of the original signal survives
        integrity = 1.0 - effective_distortion
        
        # Apply the envelope - boost coherence based on field purity
        filtered_signal = signal.copy()
        
        if 'coherence' in filtered_signal:
            # Cleanse the coherence reading
            raw_coherence = filtered_signal['coherence']
            # Remove noise proportional to purity
            cleansed_coherence = raw_coherence * (1 + purity * 0.15)  # Up to 15% boost at max purity
            filtered_signal['coherence'] = min(1.0, cleansed_coherence)
            
        if 'score' in filtered_signal:
            # Amplify score through cleared field
            raw_score = filtered_signal['score']
            filtered_signal['score'] = int(raw_score * (1 + purity * 0.10))  # Up to 10% boost
            
        # Memory Lock - signal is trustworthy if integrity > 95%
        memory_locked = integrity >= 0.95
        
        return filtered_signal, integrity, memory_locked
    
    @classmethod
    def filter_opportunities(cls, opportunities: List[Dict], lattice_frequency: float) -> List[Dict]:
        """
        Filter a list of opportunities through the Triadic Envelope.
        Rejects signals that fail the memory lock (too corrupted).
        
        Memory lock thresholds by phase:
        - 528Hz (CLEANSE): 95% integrity required (very strict)
        - 198.4Hz (UNLOCK): 80% integrity required (moderate)
        - 440Hz (DISTORTION): 60% integrity required (lenient - accept more risk)
        """
        # Phase-aware integrity thresholds
        if lattice_frequency >= 528.0:
            min_integrity = 0.95  # CLEANSE - strict
        elif lattice_frequency >= 198.0:
            min_integrity = 0.80  # UNLOCK - moderate  
        else:
            min_integrity = 0.60  # DISTORTION - lenient
            
        filtered = []
        rejected = 0
        
        for opp in opportunities:
            filtered_opp, integrity, _ = cls.apply_envelope(opp, lattice_frequency)
            
            # Check against phase-aware threshold
            locked = integrity >= min_integrity
            
            if locked:
                filtered_opp['envelope_integrity'] = integrity
                filtered_opp['memory_locked'] = True
                filtered.append(filtered_opp)
            else:
                rejected += 1
                
        if rejected > 0:
            print(f"   🛡️ Triadic Envelope: {rejected} signals rejected (distortion too high)")
            
        return filtered


class LatticeEngine:
    def __init__(self):
        self.current_phase = "DISTORTION"
        self.global_coherence = 0.0
        self.global_entropy = 0.0
        self.last_update = time.time()
        self.envelope = TriadicEnvelope()
        
        # Phase Definitions
        self.PHASES = {
            "DISTORTION": LatticeState(
                phase="DISTORTION",
                frequency=440.0,
                risk_mod=0.5,   # Defensive sizing
                tp_mod=0.8,     # Take profit early
                sl_mod=0.8,     # Tight stops
                field_purity=0.0,
                description="🔴 MARS FIELD (440Hz) - High Entropy, Low Coherence. DEFENSIVE MODE."
            ),
            "UNLOCK": LatticeState(
                phase="UNLOCK",
                frequency=198.4,
                risk_mod=1.0,   # Normal sizing
                tp_mod=1.2,     # Let winners run slightly
                sl_mod=1.0,     # Normal stops
                field_purity=0.85,
                description="🟠 KEY RESONANCE (198.4Hz) - Transition State. NORMAL MODE."
            ),
            "CLEANSE": LatticeState(
                phase="CLEANSE",
                frequency=528.0,
                risk_mod=1.5,   # Aggressive sizing
                tp_mod=2.0,     # Target moon
                sl_mod=1.2,     # Wide stops to avoid wicks
                field_purity=0.992,
                description="🟢 SOLVENT FLOW (528Hz) - High Coherence. AGGRESSIVE MODE."
            )
        }

    def update(self, opportunities: list) -> LatticeState:
        """
        Update the Global Lattice state based on market opportunities.
        """
        if not opportunities:
            # Default to Distortion if no data
            self.current_phase = "DISTORTION"
            return self.PHASES["DISTORTION"]

        # 1. Calculate Global Metrics
        # Average Coherence of the market (from top opportunities)
        coherences = [opp.get('coherence', 0) for opp in opportunities]
        avg_coherence = sum(coherences) / len(coherences) if coherences else 0
        
        # Entropy (Volatility of the opportunities)
        # We can use the standard deviation of price changes as a proxy for entropy
        changes = [opp.get('change24h', 0) for opp in opportunities]
        avg_change = sum(changes) / len(changes) if changes else 0
        variance = sum((x - avg_change) ** 2 for x in changes) / len(changes) if changes else 0
        entropy = math.sqrt(variance)

        self.global_coherence = avg_coherence
        self.global_entropy = entropy

        # 2. Determine Phase
        # Logic:
        # High Coherence (> 0.7) -> CLEANSE
        # Moderate Coherence (> 0.4) -> UNLOCK
        # Low Coherence / High Entropy -> DISTORTION
        
        prev_phase = self.current_phase
        
        if avg_coherence > 0.75:
            self.current_phase = "CLEANSE"
        elif avg_coherence > 0.45:
            self.current_phase = "UNLOCK"
        else:
            self.current_phase = "DISTORTION"
            
        # Hysteresis / Stability check (optional, but good for preventing rapid switching)
        # For now, we allow direct switching as market conditions change
        
        state = self.PHASES[self.current_phase]
        
        # Log transition
        if self.current_phase != prev_phase:
            print(f"\n🌐 LATTICE SHIFT: {prev_phase} -> {self.current_phase}")
            print(f"   Γ={avg_coherence:.2f} | Δ={entropy:.2f} | Freq={state.frequency}Hz")
            print(f"   {state.description}\n")
            
        return state

    def get_state(self) -> LatticeState:
        return self.PHASES[self.current_phase]
    
    def filter_signals(self, opportunities: List[Dict]) -> List[Dict]:
        """
        Apply Triadic Envelope filtering to trading signals.
        Signals that fail the memory lock are rejected.
        """
        current_freq = self.PHASES[self.current_phase].frequency
        return TriadicEnvelope.filter_opportunities(opportunities, current_freq)
    
    def get_field_purity(self) -> float:
        """Return the current field purity (protection level)."""
        return self.PHASES[self.current_phase].field_purity
