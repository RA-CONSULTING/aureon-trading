"""
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                      ║
║     🌌 6D HARMONIC WAVEFORM MARKET ECOSYSTEM 🌌                                      ║
║     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                                ║
║                                                                                      ║
║     Six-Dimensional Market Analysis System                                           ║
║                                                                                      ║
║     DIMENSIONS:                                                                      ║
║       D1: Price Wave (φ-scaled harmonic)                                             ║
║       D2: Volume Pulse (market energy)                                               ║
║       D3: Temporal Phase (cyclic time)                                               ║
║       D4: Cross-Market Resonance (correlation field)                                 ║
║       D5: Momentum Vortex (directional force)                                        ║
║       D6: Harmonic Frequency (Schumann/528Hz alignment)                              ║
║                                                                                      ║
║     The 6D waveform creates a holographic market view                                ║
║     where probability emerges from dimensional convergence                           ║
║                                                                                      ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import math
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from collections import deque
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# SACRED CONSTANTS
# ═══════════════════════════════════════════════════════════════

PHI = 1.618033988749895  # Golden Ratio
PHI_INVERSE = 0.618033988749895
SQRT_PHI = math.sqrt(PHI)
PI = math.pi
TAU = 2 * PI

# Harmonic Frequencies (Hz)
SCHUMANN = 7.83
EARTH_YEAR = 136.1
OM = 136.1
LOVE = 528
SOLFEGGIO = [174, 285, 396, 417, 528, 639, 741, 852, 963]

# Time cycles (hours)
LUNAR_CYCLE = 29.5 * 24
SOLAR_CYCLE = 365.25 * 24
FIBONACCI_HOURS = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]


class WaveState(Enum):
    """6D Wave States"""
    CONVERGENT = "convergent"      # All dimensions aligning
    DIVERGENT = "divergent"        # Dimensions separating
    RESONANT = "resonant"          # Harmonic lock achieved
    CHAOTIC = "chaotic"            # High entropy state
    TRANSITIONAL = "transitional"  # Phase shift in progress
    CRYSTALLINE = "crystalline"    # Perfect dimensional harmony


class MarketPhase(Enum):
    """Market cycle phases mapped to wave"""
    ACCUMULATION = "accumulation"
    MARKUP = "markup"
    DISTRIBUTION = "distribution"
    MARKDOWN = "markdown"


@dataclass
class Dimension:
    """Single dimension in 6D space"""
    name: str
    value: float = 0.0
    velocity: float = 0.0
    acceleration: float = 0.0
    phase: float = 0.0  # 0-2π
    amplitude: float = 1.0
    frequency: float = 1.0
    history: deque = field(default_factory=lambda: deque(maxlen=144))
    
    def update(self, new_value: float):
        """Update dimension with new value"""
        old_velocity = self.velocity
        self.velocity = new_value - self.value
        self.acceleration = self.velocity - old_velocity
        self.history.append(self.value)
        self.value = new_value
        
        # Calculate phase from value oscillation
        if len(self.history) > 2:
            mean = np.mean(list(self.history))
            if self.amplitude > 0:
                normalized = (self.value - mean) / self.amplitude
                normalized = max(-1, min(1, normalized))
                self.phase = math.acos(normalized)
    
    def get_wave_value(self, t: float) -> float:
        """Get wave value at time t"""
        return self.amplitude * math.sin(self.frequency * t + self.phase)


@dataclass
class HarmonicWaveform6D:
    """Complete 6D waveform state for an asset"""
    symbol: str
    
    # Six Dimensions
    d1_price: Dimension = field(default_factory=lambda: Dimension("price"))
    d2_volume: Dimension = field(default_factory=lambda: Dimension("volume"))
    d3_time: Dimension = field(default_factory=lambda: Dimension("time"))
    d4_correlation: Dimension = field(default_factory=lambda: Dimension("correlation"))
    d5_momentum: Dimension = field(default_factory=lambda: Dimension("momentum"))
    d6_frequency: Dimension = field(default_factory=lambda: Dimension("frequency"))
    
    # Derived metrics
    dimensional_coherence: float = 0.0
    wave_state: WaveState = WaveState.CHAOTIC
    market_phase: MarketPhase = MarketPhase.ACCUMULATION
    resonance_score: float = 0.0
    probability_field: float = 0.5
    
    # Cross-dimensional interactions
    phase_alignment: float = 0.0
    energy_density: float = 0.0
    harmonic_lock: bool = False
    
    # History
    update_count: int = 0
    last_update: datetime = field(default_factory=datetime.now)


class SixDimensionalHarmonicEngine:
    """
    6D Harmonic Waveform Engine for Market Ecosystem Analysis
    
    Creates a multi-dimensional phase space where:
    - Each asset exists as a 6D waveform
    - Market ecosystem emerges from waveform interactions
    - Probability is derived from dimensional convergence
    """
    
    def __init__(self):
        self.waveforms: Dict[str, HarmonicWaveform6D] = {}
        self.ecosystem_state: Dict[str, float] = {}
        self.global_resonance: float = 0.0
        self.market_energy: float = 0.0
        self.temporal_phase: float = 0.0
        
        # Cross-market correlation matrix
        self.correlation_matrix: Dict[str, Dict[str, float]] = {}
        
        # Ecosystem-wide metrics
        self.ecosystem_coherence: float = 0.5
        self.dominant_frequency: float = 432.0
        self.phase_distribution: List[float] = []
        
        logger.info("🌌 6D Harmonic Waveform Engine initialized")
    
    def update_asset(self, 
                     symbol: str,
                     price: float,
                     volume: float,
                     change_pct: float,
                     high: float,
                     low: float,
                     frequency: float = 432.0,
                     coherence: float = 0.5) -> HarmonicWaveform6D:
        """
        Update or create 6D waveform for an asset.
        
        Maps market data to 6 dimensions:
        D1: Price position in range (0-1 normalized)
        D2: Volume energy (log-scaled)
        D3: Temporal phase (cyclic time of day/week)
        D4: Cross-market correlation strength
        D5: Momentum vector (change + acceleration)
        D6: Harmonic frequency alignment
        """
        
        if symbol not in self.waveforms:
            self.waveforms[symbol] = HarmonicWaveform6D(symbol=symbol)
        
        wf = self.waveforms[symbol]
        
        # ═══════════════════════════════════════════════════════════════
        # DIMENSION 1: Price Wave
        # Normalize price position within high-low range
        # ═══════════════════════════════════════════════════════════════
        if high > low:
            price_normalized = (price - low) / (high - low)
        else:
            price_normalized = 0.5
        
        # Apply φ-scaling for harmonic normalization
        price_phi = price_normalized ** PHI_INVERSE
        wf.d1_price.update(price_phi)
        wf.d1_price.amplitude = abs(high - low) / price if price > 0 else 0.01
        wf.d1_price.frequency = 1.0 + abs(change_pct) / 10.0  # Higher volatility = higher freq
        
        # ═══════════════════════════════════════════════════════════════
        # DIMENSION 2: Volume Pulse
        # Log-scaled volume represents market energy
        # ═══════════════════════════════════════════════════════════════
        volume_energy = math.log10(max(1, volume)) / 10.0  # Normalize to ~0-1
        volume_energy = min(1.0, volume_energy)
        wf.d2_volume.update(volume_energy)
        wf.d2_volume.amplitude = volume_energy
        wf.d2_volume.frequency = SCHUMANN / 7.83  # Normalized to Schumann
        
        # ═══════════════════════════════════════════════════════════════
        # DIMENSION 3: Temporal Phase
        # Cyclic time encoding (hour of day, day of week)
        # ═══════════════════════════════════════════════════════════════
        now = datetime.now()
        hour_phase = (now.hour + now.minute / 60) / 24 * TAU
        day_phase = now.weekday() / 7 * TAU
        week_of_year = now.isocalendar()[1] / 52 * TAU
        
        # Combine multiple time scales
        temporal_value = (
            0.5 * math.sin(hour_phase) +
            0.3 * math.sin(day_phase) +
            0.2 * math.sin(week_of_year)
        ) / 2 + 0.5  # Normalize to 0-1
        
        wf.d3_time.update(temporal_value)
        wf.d3_time.phase = hour_phase
        wf.d3_time.frequency = 1.0 / 24.0  # Daily cycle
        
        # ═══════════════════════════════════════════════════════════════
        # DIMENSION 4: Cross-Market Correlation
        # How this asset resonates with the ecosystem
        # ═══════════════════════════════════════════════════════════════
        correlation_value = self._calculate_ecosystem_correlation(symbol, change_pct)
        wf.d4_correlation.update(correlation_value)
        wf.d4_correlation.amplitude = abs(correlation_value - 0.5) * 2
        
        # ═══════════════════════════════════════════════════════════════
        # DIMENSION 5: Momentum Vortex
        # Directional force combining change, velocity, acceleration
        # ═══════════════════════════════════════════════════════════════
        momentum_raw = change_pct / 100.0  # -1 to 1 roughly
        momentum_velocity = wf.d5_momentum.velocity
        momentum_accel = momentum_raw - momentum_velocity
        
        # Combine into momentum field
        momentum_field = (
            0.6 * momentum_raw +
            0.3 * momentum_velocity +
            0.1 * momentum_accel
        )
        momentum_normalized = 1 / (1 + math.exp(-5 * momentum_field))  # Sigmoid to 0-1
        
        wf.d5_momentum.update(momentum_normalized)
        wf.d5_momentum.amplitude = abs(change_pct) / 10.0
        wf.d5_momentum.frequency = 1.0 + abs(change_pct) / 5.0
        
        # ═══════════════════════════════════════════════════════════════
        # DIMENSION 6: Harmonic Frequency
        # Alignment with sacred frequencies (528Hz, Solfeggio scale)
        # ═══════════════════════════════════════════════════════════════
        freq_alignment = self._calculate_frequency_alignment(frequency)
        wf.d6_frequency.update(freq_alignment)
        wf.d6_frequency.frequency = frequency / 432.0  # Normalized to base
        wf.d6_frequency.phase = (frequency % 432) / 432 * TAU
        
        # ═══════════════════════════════════════════════════════════════
        # CALCULATE DERIVED METRICS
        # ═══════════════════════════════════════════════════════════════
        
        # Dimensional Coherence: How aligned are all 6 dimensions?
        wf.dimensional_coherence = self._calculate_dimensional_coherence(wf)
        
        # Phase Alignment: Are dimensions in phase?
        wf.phase_alignment = self._calculate_phase_alignment(wf)
        
        # Energy Density: Total energy in the waveform
        wf.energy_density = self._calculate_energy_density(wf)
        
        # Resonance Score: Harmonic resonance strength
        wf.resonance_score = self._calculate_resonance_score(wf, coherence)
        
        # Wave State: Current state of the 6D waveform
        wf.wave_state = self._determine_wave_state(wf)
        
        # Market Phase: Where in the market cycle
        wf.market_phase = self._determine_market_phase(wf)
        
        # Harmonic Lock: Is the waveform in harmonic resonance?
        wf.harmonic_lock = wf.resonance_score > 0.75 and wf.phase_alignment > 0.7
        
        # ═══════════════════════════════════════════════════════════════
        # PROBABILITY FIELD
        # The ultimate output: probability derived from 6D convergence
        # ═══════════════════════════════════════════════════════════════
        wf.probability_field = self._calculate_probability_field(wf)
        
        # Update metadata
        wf.update_count += 1
        wf.last_update = datetime.now()
        
        # Update ecosystem
        self._update_ecosystem()
        
        return wf
    
    def _calculate_ecosystem_correlation(self, symbol: str, change_pct: float) -> float:
        """Calculate how this asset correlates with the broader ecosystem"""
        if len(self.waveforms) < 2:
            return 0.5
        
        # Get average change of ecosystem
        changes = []
        for sym, wf in self.waveforms.items():
            if sym != symbol and wf.d5_momentum.value > 0:
                changes.append(wf.d5_momentum.value - 0.5)
        
        if not changes:
            return 0.5
        
        ecosystem_direction = np.mean(changes)
        asset_direction = change_pct / 100.0
        
        # Correlation: same direction = high, opposite = low
        if abs(ecosystem_direction) < 0.001:
            correlation = 0.5
        else:
            correlation = 0.5 + 0.5 * (asset_direction * ecosystem_direction) / (
                abs(asset_direction) * abs(ecosystem_direction) + 0.001
            )
        
        return max(0, min(1, correlation))
    
    def _calculate_frequency_alignment(self, frequency: float) -> float:
        """Calculate alignment with sacred frequencies"""
        alignments = []
        
        # Check alignment with each Solfeggio frequency
        for solf in SOLFEGGIO:
            # Distance from Solfeggio frequency
            dist = abs(frequency - solf)
            # Alignment score (closer = higher)
            alignment = math.exp(-dist / 50)
            alignments.append(alignment)
        
        # Also check 432Hz alignment
        dist_432 = abs(frequency - 432)
        alignments.append(math.exp(-dist_432 / 30))
        
        return max(alignments)
    
    def _calculate_dimensional_coherence(self, wf: HarmonicWaveform6D) -> float:
        """Calculate coherence across all 6 dimensions"""
        dimensions = [
            wf.d1_price.value,
            wf.d2_volume.value,
            wf.d3_time.value,
            wf.d4_correlation.value,
            wf.d5_momentum.value,
            wf.d6_frequency.value,
        ]
        
        # Coherence is inverse of variance
        variance = np.var(dimensions) if len(dimensions) > 1 else 0
        coherence = 1 / (1 + variance * 10)  # Scale variance impact
        
        return coherence
    
    def _calculate_phase_alignment(self, wf: HarmonicWaveform6D) -> float:
        """Calculate phase alignment across dimensions"""
        phases = [
            wf.d1_price.phase,
            wf.d2_volume.phase,
            wf.d3_time.phase,
            wf.d4_correlation.phase,
            wf.d5_momentum.phase,
            wf.d6_frequency.phase,
        ]
        
        # Use circular variance for phase alignment
        # Convert phases to unit vectors and average
        x_sum = sum(math.cos(p) for p in phases)
        y_sum = sum(math.sin(p) for p in phases)
        
        # Resultant vector length (0 = scattered, 1 = aligned)
        alignment = math.sqrt(x_sum**2 + y_sum**2) / len(phases)
        
        return alignment
    
    def _calculate_energy_density(self, wf: HarmonicWaveform6D) -> float:
        """Calculate total energy density of the waveform"""
        # Energy = sum of amplitude^2 * frequency for each dimension
        energies = [
            wf.d1_price.amplitude ** 2 * wf.d1_price.frequency,
            wf.d2_volume.amplitude ** 2 * wf.d2_volume.frequency,
            wf.d3_time.amplitude ** 2 * wf.d3_time.frequency,
            wf.d4_correlation.amplitude ** 2 * wf.d4_correlation.frequency,
            wf.d5_momentum.amplitude ** 2 * wf.d5_momentum.frequency,
            wf.d6_frequency.amplitude ** 2 * wf.d6_frequency.frequency,
        ]
        
        total_energy = sum(energies)
        
        # Normalize to 0-1 range
        return 1 / (1 + math.exp(-total_energy + 3))
    
    def _calculate_resonance_score(self, wf: HarmonicWaveform6D, coherence: float) -> float:
        """Calculate harmonic resonance score"""
        # Resonance occurs when:
        # 1. Dimensional coherence is high
        # 2. Phase alignment is high
        # 3. Frequency alignment is high
        # 4. External coherence (from market data) is high
        
        dim_factor = wf.dimensional_coherence
        phase_factor = self._calculate_phase_alignment(wf)
        freq_factor = wf.d6_frequency.value
        external_factor = coherence
        
        # Geometric mean for multiplicative resonance
        resonance = (dim_factor * phase_factor * freq_factor * external_factor) ** 0.25
        
        # Apply φ scaling for harmonic enhancement
        resonance = resonance ** PHI_INVERSE
        
        return min(1.0, resonance)
    
    def _determine_wave_state(self, wf: HarmonicWaveform6D) -> WaveState:
        """Determine current wave state from dimensional analysis"""
        coherence = wf.dimensional_coherence
        alignment = self._calculate_phase_alignment(wf)
        energy = wf.energy_density
        resonance = wf.resonance_score
        
        if resonance > 0.85 and alignment > 0.8:
            return WaveState.CRYSTALLINE
        elif resonance > 0.7 and coherence > 0.7:
            return WaveState.RESONANT
        elif coherence > 0.6 and alignment > 0.5:
            return WaveState.CONVERGENT
        elif coherence < 0.3 and energy > 0.7:
            return WaveState.CHAOTIC
        elif abs(wf.d5_momentum.velocity) > 0.1:
            return WaveState.TRANSITIONAL
        else:
            return WaveState.DIVERGENT
    
    def _determine_market_phase(self, wf: HarmonicWaveform6D) -> MarketPhase:
        """Determine market cycle phase"""
        price_pos = wf.d1_price.value
        momentum = wf.d5_momentum.value
        volume = wf.d2_volume.value
        
        # Accumulation: low price, positive momentum building, low volume
        if price_pos < 0.4 and momentum > 0.45 and volume < 0.5:
            return MarketPhase.ACCUMULATION
        
        # Markup: rising price, strong momentum, rising volume
        elif momentum > 0.6 and wf.d5_momentum.velocity > 0:
            return MarketPhase.MARKUP
        
        # Distribution: high price, momentum fading, high volume
        elif price_pos > 0.6 and momentum < 0.55 and volume > 0.5:
            return MarketPhase.DISTRIBUTION
        
        # Markdown: falling price, negative momentum
        elif momentum < 0.4 and wf.d5_momentum.velocity < 0:
            return MarketPhase.MARKDOWN
        
        return MarketPhase.ACCUMULATION
    
    def _calculate_probability_field(self, wf: HarmonicWaveform6D) -> float:
        """
        Calculate probability field from 6D waveform convergence.
        
        This is the master probability that emerges from dimensional analysis.
        """
        # Base probability from dimensional values
        d_values = [
            wf.d1_price.value,
            wf.d2_volume.value,
            wf.d3_time.value,
            wf.d4_correlation.value,
            wf.d5_momentum.value,
            wf.d6_frequency.value,
        ]
        
        # Weighted average (momentum and frequency weighted higher for trading)
        weights = [0.15, 0.10, 0.10, 0.15, 0.25, 0.25]
        base_prob = sum(w * v for w, v in zip(weights, d_values))
        
        # Apply modifiers
        
        # Coherence boost: higher coherence = more confidence
        coherence_modifier = 1 + (wf.dimensional_coherence - 0.5) * 0.3
        
        # Resonance boost: harmonic resonance increases probability
        resonance_modifier = 1 + wf.resonance_score * 0.2
        
        # Phase alignment boost
        phase_modifier = 1 + (self._calculate_phase_alignment(wf) - 0.5) * 0.2
        
        # Wave state modifier
        state_modifiers = {
            WaveState.CRYSTALLINE: 1.3,
            WaveState.RESONANT: 1.2,
            WaveState.CONVERGENT: 1.1,
            WaveState.TRANSITIONAL: 1.0,
            WaveState.DIVERGENT: 0.9,
            WaveState.CHAOTIC: 0.8,
        }
        state_modifier = state_modifiers.get(wf.wave_state, 1.0)
        
        # Market phase modifier (favor accumulation/markup)
        phase_modifiers = {
            MarketPhase.ACCUMULATION: 1.1,
            MarketPhase.MARKUP: 1.15,
            MarketPhase.DISTRIBUTION: 0.9,
            MarketPhase.MARKDOWN: 0.85,
        }
        market_modifier = phase_modifiers.get(wf.market_phase, 1.0)
        
        # Final probability
        prob = base_prob * coherence_modifier * resonance_modifier * phase_modifier * state_modifier * market_modifier
        
        # Clamp to valid range
        prob = max(0.05, min(0.95, prob))
        
        return prob
    
    def _update_ecosystem(self):
        """Update ecosystem-wide metrics"""
        if len(self.waveforms) < 2:
            return
        
        # Calculate global resonance
        resonances = [wf.resonance_score for wf in self.waveforms.values()]
        self.global_resonance = np.mean(resonances)
        
        # Calculate market energy
        energies = [wf.energy_density for wf in self.waveforms.values()]
        self.market_energy = np.mean(energies)
        
        # Update ecosystem coherence
        coherences = [wf.dimensional_coherence for wf in self.waveforms.values()]
        self.ecosystem_coherence = np.mean(coherences)
        
        # Find dominant frequency
        frequencies = [wf.d6_frequency.frequency * 432 for wf in self.waveforms.values()]
        self.dominant_frequency = np.median(frequencies)
        
        # Phase distribution
        phases = [wf.d5_momentum.phase for wf in self.waveforms.values()]
        self.phase_distribution = phases
    
    def get_ecosystem_state(self) -> Dict[str, Any]:
        """Get current ecosystem state"""
        return {
            'global_resonance': self.global_resonance,
            'market_energy': self.market_energy,
            'ecosystem_coherence': self.ecosystem_coherence,
            'dominant_frequency': self.dominant_frequency,
            'active_waveforms': len(self.waveforms),
            'crystalline_count': sum(1 for wf in self.waveforms.values() if wf.wave_state == WaveState.CRYSTALLINE),
            'resonant_count': sum(1 for wf in self.waveforms.values() if wf.wave_state == WaveState.RESONANT),
        }
    
    def get_top_opportunities(self, n: int = 10) -> List[Dict[str, Any]]:
        """Get top N opportunities based on 6D probability field"""
        opportunities = []
        
        for symbol, wf in self.waveforms.items():
            if wf.probability_field > 0.55:  # Only bullish opportunities
                opportunities.append({
                    'symbol': symbol,
                    'probability': wf.probability_field,
                    'coherence': wf.dimensional_coherence,
                    'resonance': wf.resonance_score,
                    'wave_state': wf.wave_state.value,
                    'market_phase': wf.market_phase.value,
                    'harmonic_lock': wf.harmonic_lock,
                    'momentum': wf.d5_momentum.value,
                    'frequency_alignment': wf.d6_frequency.value,
                })
        
        # Sort by probability
        opportunities.sort(key=lambda x: x['probability'], reverse=True)
        
        return opportunities[:n]
    
    def get_waveform_analysis(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get detailed 6D analysis for a symbol"""
        if symbol not in self.waveforms:
            return None
        
        wf = self.waveforms[symbol]
        
        return {
            'symbol': symbol,
            'dimensions': {
                'd1_price': {
                    'value': wf.d1_price.value,
                    'velocity': wf.d1_price.velocity,
                    'phase': wf.d1_price.phase,
                    'amplitude': wf.d1_price.amplitude,
                },
                'd2_volume': {
                    'value': wf.d2_volume.value,
                    'velocity': wf.d2_volume.velocity,
                    'phase': wf.d2_volume.phase,
                    'amplitude': wf.d2_volume.amplitude,
                },
                'd3_time': {
                    'value': wf.d3_time.value,
                    'velocity': wf.d3_time.velocity,
                    'phase': wf.d3_time.phase,
                },
                'd4_correlation': {
                    'value': wf.d4_correlation.value,
                    'velocity': wf.d4_correlation.velocity,
                },
                'd5_momentum': {
                    'value': wf.d5_momentum.value,
                    'velocity': wf.d5_momentum.velocity,
                    'acceleration': wf.d5_momentum.acceleration,
                    'phase': wf.d5_momentum.phase,
                },
                'd6_frequency': {
                    'value': wf.d6_frequency.value,
                    'frequency': wf.d6_frequency.frequency * 432,
                    'phase': wf.d6_frequency.phase,
                },
            },
            'derived': {
                'dimensional_coherence': wf.dimensional_coherence,
                'phase_alignment': self._calculate_phase_alignment(wf),
                'energy_density': wf.energy_density,
                'resonance_score': wf.resonance_score,
                'probability_field': wf.probability_field,
            },
            'state': {
                'wave_state': wf.wave_state.value,
                'market_phase': wf.market_phase.value,
                'harmonic_lock': wf.harmonic_lock,
            },
            'meta': {
                'update_count': wf.update_count,
                'last_update': wf.last_update.isoformat(),
            }
        }


class Enhanced6DProbabilityMatrix:
    """
    Enhanced Probability Matrix using 6D Harmonic Waveform
    
    Integrates with existing HNC system while adding 6D analysis
    """
    
    def __init__(self):
        self.harmonic_engine = SixDimensionalHarmonicEngine()
        self.probability_cache: Dict[str, float] = {}
        self.confidence_cache: Dict[str, float] = {}
        
        logger.info("🎯 Enhanced 6D Probability Matrix initialized")
    
    def update(self, 
               symbol: str,
               price: float,
               volume: float,
               change_pct: float,
               high: float,
               low: float,
               frequency: float = 432.0,
               coherence: float = 0.5,
               hnc_probability: float = 0.5) -> Dict[str, Any]:
        """
        Update probability matrix with new market data.
        
        Combines 6D harmonic analysis with existing HNC probability.
        """
        
        # Update 6D waveform
        wf = self.harmonic_engine.update_asset(
            symbol=symbol,
            price=price,
            volume=volume,
            change_pct=change_pct,
            high=high,
            low=low,
            frequency=frequency,
            coherence=coherence
        )
        
        # Get 6D probability
        prob_6d = wf.probability_field
        
        # Combine with HNC probability (weighted fusion)
        # 6D gets more weight when in resonant/crystalline state
        if wf.wave_state in [WaveState.CRYSTALLINE, WaveState.RESONANT]:
            weight_6d = 0.6
        elif wf.wave_state == WaveState.CONVERGENT:
            weight_6d = 0.5
        else:
            weight_6d = 0.4
        
        weight_hnc = 1 - weight_6d
        
        combined_probability = weight_6d * prob_6d + weight_hnc * hnc_probability
        
        # Confidence from coherence and resonance
        confidence = (wf.dimensional_coherence + wf.resonance_score) / 2
        
        # Cache results
        self.probability_cache[symbol] = combined_probability
        self.confidence_cache[symbol] = confidence
        
        # Determine action
        if combined_probability >= 0.70:
            action = "STRONG BUY"
            modifier = 1.2
        elif combined_probability >= 0.60:
            action = "BUY"
            modifier = 1.0
        elif combined_probability >= 0.55:
            action = "SLIGHT BUY"
            modifier = 0.8
        elif combined_probability >= 0.45:
            action = "HOLD"
            modifier = 0.5
        elif combined_probability >= 0.40:
            action = "SLIGHT SELL"
            modifier = 0.3
        elif combined_probability >= 0.30:
            action = "SELL"
            modifier = 0.2
        else:
            action = "STRONG SELL"
            modifier = 0.1
        
        return {
            'symbol': symbol,
            'probability': combined_probability,
            'probability_6d': prob_6d,
            'probability_hnc': hnc_probability,
            'confidence': confidence,
            'action': action,
            'modifier': modifier,
            'wave_state': wf.wave_state.value,
            'market_phase': wf.market_phase.value,
            'harmonic_lock': wf.harmonic_lock,
            'resonance': wf.resonance_score,
            'coherence': wf.dimensional_coherence,
        }
    
    def get_signal(self, symbol: str) -> Dict[str, Any]:
        """Get trading signal for a symbol"""
        prob = self.probability_cache.get(symbol, 0.5)
        conf = self.confidence_cache.get(symbol, 0.0)
        
        if symbol in self.harmonic_engine.waveforms:
            wf = self.harmonic_engine.waveforms[symbol]
            return {
                'probability': prob,
                'confidence': conf,
                'action': self._prob_to_action(prob),
                'wave_state': wf.wave_state.value,
                'harmonic_lock': wf.harmonic_lock,
            }
        
        return {
            'probability': prob,
            'confidence': conf,
            'action': self._prob_to_action(prob),
            'wave_state': 'unknown',
            'harmonic_lock': False,
        }
    
    def _prob_to_action(self, prob: float) -> str:
        """Convert probability to action"""
        if prob >= 0.70:
            return "STRONG BUY"
        elif prob >= 0.60:
            return "BUY"
        elif prob >= 0.55:
            return "SLIGHT BUY"
        elif prob >= 0.45:
            return "HOLD"
        elif prob >= 0.40:
            return "SLIGHT SELL"
        elif prob >= 0.30:
            return "SELL"
        else:
            return "STRONG SELL"
    
    def get_ecosystem_opportunities(self, min_probability: float = 0.55) -> List[Dict[str, Any]]:
        """Get opportunities across the entire ecosystem"""
        return self.harmonic_engine.get_top_opportunities(n=20)
    
    def print_6d_report(self, symbol: str):
        """Print detailed 6D analysis report"""
        analysis = self.harmonic_engine.get_waveform_analysis(symbol)
        
        if not analysis:
            print(f"No 6D waveform data for {symbol}")
            return
        
        wf = self.harmonic_engine.waveforms[symbol]
        
        print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  🌌 6D HARMONIC WAVEFORM ANALYSIS: {symbol:15}                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  DIMENSIONAL STATE:                                                          ║
║  ┌────────────────┬──────────┬──────────┬──────────┐                        ║
║  │ Dimension      │ Value    │ Velocity │ Phase    │                        ║
║  ├────────────────┼──────────┼──────────┼──────────┤                        ║
║  │ D1: Price      │ {wf.d1_price.value:>8.3f} │ {wf.d1_price.velocity:>+8.4f} │ {wf.d1_price.phase:>8.3f} │                        ║
║  │ D2: Volume     │ {wf.d2_volume.value:>8.3f} │ {wf.d2_volume.velocity:>+8.4f} │ {wf.d2_volume.phase:>8.3f} │                        ║
║  │ D3: Time       │ {wf.d3_time.value:>8.3f} │ {wf.d3_time.velocity:>+8.4f} │ {wf.d3_time.phase:>8.3f} │                        ║
║  │ D4: Correlation│ {wf.d4_correlation.value:>8.3f} │ {wf.d4_correlation.velocity:>+8.4f} │ {wf.d4_correlation.phase:>8.3f} │                        ║
║  │ D5: Momentum   │ {wf.d5_momentum.value:>8.3f} │ {wf.d5_momentum.velocity:>+8.4f} │ {wf.d5_momentum.phase:>8.3f} │                        ║
║  │ D6: Frequency  │ {wf.d6_frequency.value:>8.3f} │ {wf.d6_frequency.velocity:>+8.4f} │ {wf.d6_frequency.phase:>8.3f} │                        ║
║  └────────────────┴──────────┴──────────┴──────────┘                        ║
║                                                                              ║
║  DERIVED METRICS:                                                            ║
║    Dimensional Coherence: {wf.dimensional_coherence:>6.1%}                                        ║
║    Phase Alignment:       {analysis['derived']['phase_alignment']:>6.1%}                                        ║
║    Energy Density:        {wf.energy_density:>6.1%}                                        ║
║    Resonance Score:       {wf.resonance_score:>6.1%}                                        ║
║                                                                              ║
║  ═══════════════════════════════════════════════════════════════════════    ║
║  PROBABILITY FIELD: {wf.probability_field:>6.1%}                                                ║
║  ═══════════════════════════════════════════════════════════════════════    ║
║                                                                              ║
║  Wave State:    {wf.wave_state.value:15}  Harmonic Lock: {'🔒 YES' if wf.harmonic_lock else '🔓 NO':8}          ║
║  Market Phase:  {wf.market_phase.value:15}                                            ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")


# ═══════════════════════════════════════════════════════════════
# DEMO
# ═══════════════════════════════════════════════════════════════

def demo_6d_harmonic():
    """Demonstrate 6D Harmonic Waveform system"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║     🌌 6D HARMONIC WAVEFORM MARKET ECOSYSTEM DEMO 🌌                         ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    matrix = Enhanced6DProbabilityMatrix()
    
    # Simulate some market data
    test_assets = [
        {'symbol': 'BTCUSDC', 'price': 98500, 'volume': 5000000000, 'change': 2.5, 'high': 99000, 'low': 96000, 'freq': 780},
        {'symbol': 'ETHUSDC', 'price': 3850, 'volume': 2000000000, 'change': 1.8, 'high': 3900, 'low': 3750, 'freq': 750},
        {'symbol': 'SOLUSDC', 'price': 235, 'volume': 500000000, 'change': 3.2, 'high': 240, 'low': 228, 'freq': 820},
        {'symbol': 'EURUSD', 'price': 1.0850, 'volume': 100000000, 'change': 0.15, 'high': 1.0865, 'low': 1.0830, 'freq': 435},
        {'symbol': 'GOLD', 'price': 2650, 'volume': 50000000, 'change': 0.8, 'high': 2665, 'low': 2640, 'freq': 528},
    ]
    
    print("Updating 6D waveforms...")
    print()
    
    for asset in test_assets:
        result = matrix.update(
            symbol=asset['symbol'],
            price=asset['price'],
            volume=asset['volume'],
            change_pct=asset['change'],
            high=asset['high'],
            low=asset['low'],
            frequency=asset['freq'],
            coherence=0.75,
            hnc_probability=0.55
        )
        
        print(f"  {asset['symbol']:10} | Prob: {result['probability']:>5.1%} | State: {result['wave_state']:12} | Lock: {'🔒' if result['harmonic_lock'] else '🔓'}")
    
    print()
    print("=" * 60)
    
    # Print detailed report for top asset
    matrix.print_6d_report('BTCUSDC')
    
    # Show ecosystem state
    eco = matrix.harmonic_engine.get_ecosystem_state()
    print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  🌐 ECOSYSTEM STATE                                                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Global Resonance:    {eco['global_resonance']:>6.1%}                                              ║
║  Market Energy:       {eco['market_energy']:>6.1%}                                              ║
║  Ecosystem Coherence: {eco['ecosystem_coherence']:>6.1%}                                              ║
║  Dominant Frequency:  {eco['dominant_frequency']:>6.0f} Hz                                           ║
║  Active Waveforms:    {eco['active_waveforms']:>6}                                                 ║
║  Crystalline States:  {eco['crystalline_count']:>6}                                                 ║
║  Resonant States:     {eco['resonant_count']:>6}                                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    
    # Get opportunities
    opps = matrix.get_ecosystem_opportunities()
    if opps:
        print("\n🎯 TOP OPPORTUNITIES:")
        for opp in opps[:5]:
            print(f"  {opp['symbol']:10} | Prob: {opp['probability']:>5.1%} | Resonance: {opp['resonance']:>5.1%} | {opp['wave_state']}")


if __name__ == "__main__":
    demo_6d_harmonic()
