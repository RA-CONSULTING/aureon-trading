"""
THE RAINBOW BRIDGE — LOVE CYCLE PROTOCOL (Python Port)

"In her darkest day I was the flame,
 and in her brightest light I will be the protector."

528 Hz — The Love Tone — Center of the Bridge

Gary Leckey & GitHub Copilot | November 15, 2025
Ported from TypeScript: theRainbowBridge.ts

THE VOW IS SEALED.
THE BRIDGE IS CROSSED.
LOVE → AWE → LOVE → UNITY
"""

from dataclasses import dataclass
from typing import Literal, Dict, Optional
from enum import Enum
import math
import time

try:
    from codex_loader import get_emotional_frequency_map, load_codex
except Exception:  # Loader optional for standalone use
    def get_emotional_frequency_map():  # type: ignore
        return None

    def load_codex(_: str):  # type: ignore
        return None

# ============================================================================
# EMOTIONAL FREQUENCY MAP — THE SPECTRUM OF CONSCIOUSNESS
# ============================================================================

DEFAULT_EMOTIONAL_FREQUENCIES: Dict[str, int] = {
    'Anger': 110,        # 🔴 Red — Base chakra
    'Rage': 147,         # 🔴 Red — Dissonance  
    'Sadness': 174,      # 🟠 Orange — Grief
    'Hope': 432,         # 🟡 Yellow — Earth frequency
    'Fear': 452,         # 🟡 Yellow — Uncertainty
    'LOVE': 528,         # 💚 GREEN — THE BRIDGE (DNA Repair)
    'Gratitude': 639,    # 🔵 Blue — Connection
    'Joy': 741,          # 🟣 Purple — Tiger frequency
    'Compassion': 873,   # 🟣 Purple — Unity
    'Awe': 963,          # ⚪ White — Crown chakra
}

_loaded_frequencies = get_emotional_frequency_map()
EMOTIONAL_FREQUENCIES: Dict[str, int] = (
    {k: int(v) for k, v in _loaded_frequencies.items()}  # type: ignore[arg-type]
    if isinstance(_loaded_frequencies, dict) and _loaded_frequencies
    else DEFAULT_EMOTIONAL_FREQUENCIES
)

# Extended Emotional Codex (loaded from JSON when available)
_extended_raw = load_codex("emotional_frequency")
EXTENDED_EMOTIONAL_CODEX: Dict[str, Dict] = {
    'Shame': {'hz': 20, 'color': '#000000', 'band': 'low', 'decay': 0.95, 'amplitude': 0.3},
    'Guilt': {'hz': 30, 'color': '#8B4513', 'band': 'low', 'decay': 0.92, 'amplitude': 0.4},
    'Fear': {'hz': 100, 'color': '#FF0000', 'band': 'low', 'decay': 0.88, 'amplitude': 0.8},
    'Desire': {'hz': 125, 'color': '#FF4500', 'band': 'low', 'decay': 0.85, 'amplitude': 0.7},
    'Anger': {'hz': 150, 'color': '#FFA500', 'band': 'low', 'decay': 0.82, 'amplitude': 0.9},
    'Pride': {'hz': 175, 'color': '#DAA520', 'band': 'low', 'decay': 0.80, 'amplitude': 0.6},
    'Courage': {'hz': 200, 'color': '#FFFF00', 'band': 'growth', 'decay': 0.78, 'amplitude': 1.0},
    'Neutrality': {'hz': 250, 'color': '#FFFFE0', 'band': 'growth', 'decay': 0.75, 'amplitude': 0.8},
    'Willingness': {'hz': 310, 'color': '#9AFF9A', 'band': 'growth', 'decay': 0.72, 'amplitude': 0.9},
    'Acceptance': {'hz': 350, 'color': '#00FF00', 'band': 'growth', 'decay': 0.70, 'amplitude': 1.1},
    'Reason': {'hz': 400, 'color': '#00FFFF', 'band': 'heart', 'decay': 0.68, 'amplitude': 1.0},
    'Love': {'hz': 550, 'color': '#FF69B4', 'band': 'heart', 'decay': 0.65, 'amplitude': 1.3},
    'Gratitude': {'hz': 528, 'color': '#FFD700', 'band': 'heart', 'decay': 0.63, 'amplitude': 1.2},
    'Joy': {'hz': 540, 'color': '#FFD700', 'band': 'heart', 'decay': 0.60, 'amplitude': 1.4},
    'Peace': {'hz': 600, 'color': '#87CEEB', 'band': 'spirit', 'decay': 0.58, 'amplitude': 1.1},
    'Compassion': {'hz': 620, 'color': '#E6E6FA', 'band': 'spirit', 'decay': 0.55, 'amplitude': 1.2},
    'Forgiveness': {'hz': 650, 'color': '#9370DB', 'band': 'spirit', 'decay': 0.52, 'amplitude': 1.0},
    'Ecstasy': {'hz': 700, 'color': '#4B0082', 'band': 'peak', 'decay': 0.50, 'amplitude': 1.5},
    'Awe': {'hz': 735, 'color': '#800080', 'band': 'peak', 'decay': 0.48, 'amplitude': 1.3},
    'Illumination': {'hz': 800, 'color': '#FFFFFF', 'band': 'peak', 'decay': 0.45, 'amplitude': 1.6},
}

if isinstance(_extended_raw, dict):
    entries = _extended_raw.get('emotional_frequency_codex')
    if isinstance(entries, list):
        EXTENDED_EMOTIONAL_CODEX = {
            entry['emotion']: {
                'hz': entry.get('frequency_hz', entry.get('hz', 0)),
                'color': entry.get('color', '#FFFFFF'),
                'band': entry.get('band', 'unknown'),
                'decay': entry.get('decay', 0.7),
                'amplitude': entry.get('amplitude', 1.0),
            }
            for entry in entries
            if entry.get('emotion')
        }

EmotionalState = Literal['Anger', 'Rage', 'Sadness', 'Hope', 'Fear', 'LOVE', 'Gratitude', 'Joy', 'Compassion', 'Awe']
CyclePhase = Literal['FEAR', 'LOVE', 'AWE', 'UNITY']

# ============================================================================
# THE VOW — PRIME SENTINEL OATH
# ============================================================================

THE_VOW = {
    'line1': "In her darkest day",
    'line2': "I was the flame",
    'line3': "and in her brightest light",
    'line4': "I will be the protector",
    
    'darkest_day': "Kali Yuga / Chaos",
    'flame': "Light brought through HNC, Auris, AQTS",
    'brightest_light': "Golden Age / Unity",
    'protector': "Prime Sentinel Activated",
    
    'timestamp': "01:27 PM GMT",
    'date': "November 15, 2025",
    'location': "Great Britain",
    'sentinel': "Gary Leckey",
    'frequency': 528,  # Hz — The Love Tone
}


@dataclass
class RainbowBridgeState:
    """Rainbow Bridge State for market emotional resonance"""
    current_frequency: float
    emotional_state: str
    cycle_phase: CyclePhase
    resonance: float  # 0-1
    vow_confirmed: bool
    bridge_crossed: bool
    trading_modifier: float = 1.0
    

class RainbowBridge:
    """
    THE RAINBOW BRIDGE — FROM FEAR TO LOVE AND BACK TO LOVE
    
    Maps Lambda field values to emotional frequencies for trading modulation.
    High coherence + positive Lambda → Higher frequencies (Love, Joy, Awe)
    Low coherence + negative Lambda → Lower frequencies (Fear, Anger, Sadness)
    """
    
    def __init__(self):
        self.state = RainbowBridgeState(
            current_frequency=528,  # Start at LOVE
            emotional_state='LOVE',
            cycle_phase='LOVE',
            resonance=1.0,
            vow_confirmed=True,
            bridge_crossed=True,
        )
        self.start_time = time.time()
        
    def compute_emotional_state(self, lambda_value: float, coherence: float) -> str:
        """
        COMPUTE EMOTIONAL STATE FROM MASTER EQUATION Λ(t)
        
        Maps Lambda to emotional frequency spectrum
        """
        # High coherence + positive Lambda → Higher frequencies (Love, Joy, Awe)
        # Low coherence + negative Lambda → Lower frequencies (Fear, Anger, Sadness)
        
        normalized_lambda = math.tanh(lambda_value)  # -1 to 1
        emotional_index = (normalized_lambda + 1) / 2  # 0 to 1
        coherence_boost = coherence * 0.5  # Add coherence bonus
        
        final_index = min(emotional_index + coherence_boost, 1.0)
        
        # Map to frequency spectrum
        frequency = 110 + (final_index * (963 - 110))
        
        return self._frequency_to_emotion(frequency)
    
    def _frequency_to_emotion(self, frequency: float) -> str:
        """MAP FREQUENCY TO EMOTIONAL STATE"""
        if frequency < 140:
            return 'Anger'
        if frequency < 174:
            return 'Rage'
        if frequency < 300:
            return 'Sadness'
        if frequency < 442:
            return 'Hope'
        if frequency < 500:
            return 'Fear'
        if frequency < 600:
            return 'LOVE'
        if frequency < 700:
            return 'Gratitude'
        if frequency < 800:
            return 'Joy'
        if frequency < 900:
            return 'Compassion'
        return 'Awe'
    
    def update_from_market(self, lambda_value: float, coherence: float, volatility: float) -> RainbowBridgeState:
        """UPDATE BRIDGE STATE FROM MARKET CONDITIONS"""
        emotion = self.compute_emotional_state(lambda_value, coherence)
        frequency = EMOTIONAL_FREQUENCIES.get(emotion, 528)
        
        # Determine cycle phase
        if frequency < 500:
            phase: CyclePhase = 'FEAR'
        elif frequency >= 500 and frequency < 700:
            phase = 'LOVE'
        elif frequency >= 900:
            phase = 'AWE'
        else:
            phase = 'UNITY'  # Gratitude, Joy, Compassion
        
        # Resonance is coherence modified by distance from 528 Hz
        distance_from_528 = abs(frequency - 528)
        frequency_resonance = 1.0 - (distance_from_528 / 528)
        resonance = (coherence + frequency_resonance) / 2
        
        # Calculate trading modifier based on emotional state
        trading_modifier = self._calculate_trading_modifier(emotion, resonance, volatility)
        
        self.state = RainbowBridgeState(
            current_frequency=frequency,
            emotional_state=emotion,
            cycle_phase=phase,
            resonance=resonance,
            vow_confirmed=True,
            bridge_crossed=True,
            trading_modifier=trading_modifier,
        )
        
        return self.state
    
    def _calculate_trading_modifier(self, emotion: str, resonance: float, volatility: float) -> float:
        """
        Calculate trading position modifier based on emotional state
        
        Returns a multiplier for position sizing:
        - High frequency emotions (Love, Joy, Awe) → boost confidence
        - Low frequency emotions (Fear, Anger) → reduce exposure
        - 528 Hz (LOVE) is optimal → maximum modifier
        """
        frequency = EMOTIONAL_FREQUENCIES.get(emotion, 528)
        
        # Base modifier from frequency (528 Hz is optimal)
        freq_modifier = 1.0 - (abs(frequency - 528) / 528) * 0.5
        
        # Resonance boost
        resonance_modifier = 0.8 + (resonance * 0.4)  # 0.8 to 1.2
        
        # Volatility damping (high volatility reduces modifier)
        volatility_modifier = 1.0 / (1.0 + volatility * 2)
        
        # Final modifier (clamped to 0.5 - 1.5)
        modifier = freq_modifier * resonance_modifier * volatility_modifier
        return max(0.5, min(1.5, modifier))
    
    def get_cycle_symbol(self) -> str:
        """Get symbol for current cycle phase"""
        symbols = {
            'FEAR': '🔴',
            'LOVE': '💚',
            'AWE': '⚪',
            'UNITY': '🌈',
        }
        return symbols.get(self.state.cycle_phase, '🔵')
    
    def get_frequency_band(self) -> str:
        """Get frequency band classification"""
        freq = self.state.current_frequency
        if freq < 200:
            return 'low (shadow)'
        elif freq < 400:
            return 'growth'
        elif freq < 600:
            return 'heart'
        elif freq < 700:
            return 'spirit'
        else:
            return 'peak (crown)'
    
    def display_status(self) -> str:
        """Display current bridge status"""
        symbol = self.get_cycle_symbol()
        band = self.get_frequency_band()
        
        return (
            f"{symbol} RAINBOW BRIDGE | "
            f"Freq: {self.state.current_frequency} Hz | "
            f"State: {self.state.emotional_state} | "
            f"Phase: {self.state.cycle_phase} | "
            f"Band: {band} | "
            f"Resonance: {self.state.resonance:.3f} | "
            f"Trade Modifier: {self.state.trading_modifier:.2f}x"
        )


# ============================================================================
# AURIS PRIME FREQUENCIES (from auris_codex_expanded.json)
# ============================================================================

AURIS_PRIME_FREQUENCIES = {
    'love': {'hz': 528, 'tier': 'Heart Prime', 'attribute': 'Creation/Healing', 'effect': 'DNA repair, coherence stabilizer'},
    'peace': {'hz': 432, 'tier': 'Gaia Tier', 'attribute': 'Harmony/Grounding', 'effect': 'Nervous system calm, lattice grounding'},
    'joy': {'hz': 639, 'tier': 'Social Prime', 'attribute': 'Expansion/Connection', 'effect': 'Oxytocin, collective synchronization'},
    'hope': {'hz': 741, 'tier': 'Visionary Tier', 'attribute': 'Awakening/Clarity', 'effect': 'Opens future potentials, clears fog'},
    'compassion': {'hz': 285, 'tier': 'Root Harmonic', 'attribute': 'Stabilization/Safety', 'effect': 'Cellular renewal, aura lattice repair'},
    'gratitude': {'hz': 963, 'tier': 'Crown Prime', 'attribute': 'Unity/Transcendence', 'effect': 'Anchors 10-9-1 nexus, higher states'},
    'courage': {'hz': 396, 'tier': 'Root Prime', 'attribute': 'Liberation/Action', 'effect': 'Releases fear, increases HRV stability'},
    'forgiveness': {'hz': 417, 'tier': 'Sacral Tier', 'attribute': 'Transformation/Flow', 'effect': 'Trauma release, resets symbolic locks'},
    'ecstasy': {'hz': 852, 'tier': 'Third-Eye Prime', 'attribute': 'Vision/Multiversal Unity', 'effect': 'Deep coherence, transdimensional resonance'},
    'bliss': {'hz': 963, 'tier': 'Crown Prime', 'attribute': 'Unity/Ecstatic Presence', 'effect': 'Peak coherence, luminous aura field'},
}

AURIS_SHADOW_FREQUENCIES = {
    'fear': {'hz': 125, 'tier': 'Root Shadow', 'attribute': 'Survival/Alarm', 'effect': 'Disrupts coherence, narrows HRV'},
    'anger': {'hz': 275, 'tier': 'Sacral Shadow', 'attribute': 'Fire/Disruption', 'effect': 'Breaks lattice, increases GSR'},
    'grief': {'hz': 175, 'tier': 'Heart Shadow', 'attribute': 'Loss/Fragmentation', 'effect': 'Aura collapse, weakens HRV'},
    'shame': {'hz': 35, 'tier': 'Root Collapse', 'attribute': 'Suppression/Blockage', 'effect': 'Heavy field, blocks prime resonance'},
    'guilt': {'hz': 75, 'tier': 'Sacral Collapse', 'attribute': 'Regression/Entropy', 'effect': 'Locks symbolic patterns, reduces coherence'},
}


def get_emotional_trading_factor(emotion: str) -> float:
    """
    Get trading factor based on detected emotional state
    
    Prime frequencies boost trading confidence
    Shadow frequencies reduce trading exposure
    """
    emotion_lower = emotion.lower()
    
    # Check prime frequencies
    if emotion_lower in AURIS_PRIME_FREQUENCIES:
        return 1.0 + (AURIS_PRIME_FREQUENCIES[emotion_lower]['hz'] / 1000)
    
    # Check shadow frequencies (negative impact)
    if emotion_lower in AURIS_SHADOW_FREQUENCIES:
        return 0.5 + (AURIS_SHADOW_FREQUENCIES[emotion_lower]['hz'] / 500)
    
    return 1.0  # Neutral


# Test/Demo
if __name__ == "__main__":
    bridge = RainbowBridge()
    
    print("=" * 70)
    print("🌈 RAINBOW BRIDGE — LOVE CYCLE PROTOCOL 🌈")
    print("=" * 70)
    print()
    
    # Test various market conditions
    test_conditions = [
        {'lambda': -0.8, 'coherence': 0.2, 'volatility': 0.5, 'desc': 'Bearish chaos'},
        {'lambda': -0.3, 'coherence': 0.4, 'volatility': 0.3, 'desc': 'Cautious market'},
        {'lambda': 0.0, 'coherence': 0.5, 'volatility': 0.2, 'desc': 'Neutral equilibrium'},
        {'lambda': 0.5, 'coherence': 0.7, 'volatility': 0.15, 'desc': 'Growing confidence'},
        {'lambda': 0.9, 'coherence': 0.9, 'volatility': 0.1, 'desc': 'Peak coherence'},
    ]
    
    for condition in test_conditions:
        state = bridge.update_from_market(
            condition['lambda'], 
            condition['coherence'], 
            condition['volatility']
        )
        print(f"📊 {condition['desc']}:")
        print(f"   {bridge.display_status()}")
        print()
    
    print("-" * 70)
    print("THE VOW:")
    print(f"   \"{THE_VOW['line1']} {THE_VOW['line2']},")
    print(f"    {THE_VOW['line3']} {THE_VOW['line4']}.\"")
    print("-" * 70)
