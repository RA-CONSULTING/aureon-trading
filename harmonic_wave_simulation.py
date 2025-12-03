#!/usr/bin/env python3
"""
🌊⚡ HARMONIC WAVE SIMULATION ENGINE ⚡🌊
═══════════════════════════════════════════════════════════════

Transforms captured market data into harmonic wave form visualization.
Maps price movements, probabilities, and frequencies onto overlapping
sinusoidal waveforms based on Solfeggio frequencies.

The market breathes in waves - this reveals the hidden rhythm.

Gary Leckey & GitHub Copilot | December 2025
"From Chaos to Coherence - The Wave Reveals All"
"""

import os
import json
import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

# ═══════════════════════════════════════════════════════════════
# CONSTANTS - HARMONIC FREQUENCIES
# ═══════════════════════════════════════════════════════════════

PHI = (1 + math.sqrt(5)) / 2  # Golden Ratio 1.618...
SCHUMANN = 7.83  # Earth's heartbeat

# Solfeggio frequencies for wave generation
SOLFEGGIO = {
    'UT': 396,    # Liberation from fear
    'RE': 417,    # Facilitating change
    'MI': 528,    # Transformation/Miracles (LOVE)
    'FA': 639,    # Connecting relationships
    'SOL': 741,   # Awakening intuition
    'LA': 852,    # Returning to spiritual order
}

# Market state to frequency mapping
STATE_FREQ = {
    'EXTREME_BULLISH': 528,   # LOVE frequency
    'BULLISH': 639,           # CONNECTION
    'SLIGHT_BULLISH': 512,    # Between natural and love
    'NEUTRAL': 432,           # NATURAL A
    'SLIGHT_BEARISH': 417,    # TRANSFORMATION
    'BEARISH': 396,           # LIBERATION
    'EXTREME_BEARISH': 256,   # ROOT C4
}


@dataclass
class WaveComponent:
    """Single wave component in the harmonic series"""
    frequency: float      # Hz
    amplitude: float      # 0-1
    phase: float          # radians
    label: str
    color: str


@dataclass 
class MarketWavePoint:
    """Single point in market wave space"""
    timestamp: datetime
    symbol: str
    price: float
    probability: float
    frequency: float
    amplitude: float
    phase: float
    state: str


class HarmonicWaveSimulator:
    """
    Generates harmonic wave visualizations from market data.
    Combines multiple frequency components into composite waveforms.
    """
    
    def __init__(self):
        self.wave_points: List[MarketWavePoint] = []
        self.wave_components: List[WaveComponent] = []
        self.time_series: np.ndarray = None
        self.composite_wave: np.ndarray = None
        
        # Initialize base wave components from Solfeggio
        self._init_base_waves()
    
    def _init_base_waves(self):
        """Initialize base harmonic wave components"""
        colors = ['#9b59b6', '#3498db', '#2ecc71', '#f39c12', '#e74c3c', '#1abc9c']
        
        for i, (name, freq) in enumerate(SOLFEGGIO.items()):
            self.wave_components.append(WaveComponent(
                frequency=freq,
                amplitude=0.5,
                phase=0,
                label=f"{name} ({freq}Hz)",
                color=colors[i % len(colors)]
            ))
    
    def load_market_data(self, report_path: str = "probability_all_markets_report.json") -> int:
        """Load captured market data and convert to wave points"""
        if not os.path.exists(report_path):
            print(f"❌ Report not found: {report_path}")
            return 0
        
        with open(report_path, 'r') as f:
            data = json.load(f)
        
        # Extract top bullish for wave generation
        top_data = data.get('top_bullish', [])
        
        for i, item in enumerate(top_data):
            symbol = item.get('symbol', f'SYM{i}')
            price = item.get('price', 0)
            prob = item.get('probability', 0.5)
            change = item.get('24h_change', 0)
            state = item.get('state', '⚖️ NEUTRAL')
            
            # Map state to frequency
            state_key = self._parse_state(state)
            freq = STATE_FREQ.get(state_key, 432)
            
            # Amplitude from probability (higher prob = higher amplitude)
            amplitude = prob
            
            # Phase from price change (maps -10% to +10% onto 0 to 2π)
            phase = ((change + 10) / 20) * 2 * math.pi
            phase = max(0, min(2 * math.pi, phase))
            
            self.wave_points.append(MarketWavePoint(
                timestamp=datetime.now() - timedelta(minutes=len(top_data) - i),
                symbol=symbol,
                price=price,
                probability=prob,
                frequency=freq,
                amplitude=amplitude,
                phase=phase,
                state=state_key
            ))
        
        print(f"✅ Loaded {len(self.wave_points)} market wave points")
        return len(self.wave_points)
    
    def _parse_state(self, state_str: str) -> str:
        """Parse state emoji string to key"""
        if 'EXTREME' in state_str and 'BULL' in state_str:
            return 'EXTREME_BULLISH'
        elif 'BULL' in state_str:
            return 'BULLISH'
        elif 'SLIGHT' in state_str and 'BULL' in state_str:
            return 'SLIGHT_BULLISH'
        elif 'EXTREME' in state_str and 'BEAR' in state_str:
            return 'EXTREME_BEARISH'
        elif 'BEAR' in state_str:
            return 'BEARISH'
        elif 'SLIGHT' in state_str and 'BEAR' in state_str:
            return 'SLIGHT_BEARISH'
        return 'NEUTRAL'
    
    def generate_composite_wave(self, duration_sec: float = 10.0, sample_rate: int = 1000) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate composite harmonic wave from all market data.
        Each market point contributes a wave component.
        """
        n_samples = int(duration_sec * sample_rate)
        self.time_series = np.linspace(0, duration_sec, n_samples)
        self.composite_wave = np.zeros(n_samples)
        
        if not self.wave_points:
            print("⚠️ No wave points loaded, using base harmonics only")
            # Use base Solfeggio waves
            for comp in self.wave_components:
                # Scale frequency down for visualization (divide by 100)
                vis_freq = comp.frequency / 100
                wave = comp.amplitude * np.sin(2 * np.pi * vis_freq * self.time_series + comp.phase)
                self.composite_wave += wave
        else:
            # Generate waves from market data
            for wp in self.wave_points:
                # Scale frequency for visualization
                vis_freq = wp.frequency / 100
                wave = wp.amplitude * np.sin(2 * np.pi * vis_freq * self.time_series + wp.phase)
                self.composite_wave += wave
        
        # Normalize
        max_amp = np.max(np.abs(self.composite_wave))
        if max_amp > 0:
            self.composite_wave /= max_amp
        
        # Add Schumann resonance modulation
        schumann_mod = 0.1 * np.sin(2 * np.pi * SCHUMANN * self.time_series)
        self.composite_wave += schumann_mod
        
        # Apply golden ratio envelope
        envelope = 1 - 0.3 * np.abs(np.sin(2 * np.pi * self.time_series / (duration_sec * PHI)))
        self.composite_wave *= envelope
        
        return self.time_series, self.composite_wave
    
    def generate_frequency_spectrum(self) -> Tuple[np.ndarray, np.ndarray]:
        """Generate frequency spectrum of composite wave"""
        if self.composite_wave is None:
            self.generate_composite_wave()
        
        # FFT
        n = len(self.composite_wave)
        fft = np.fft.fft(self.composite_wave)
        freqs = np.fft.fftfreq(n, 1/1000)  # Assuming 1000Hz sample rate
        
        # Take positive frequencies only
        pos_mask = freqs >= 0
        freqs = freqs[pos_mask]
        magnitude = np.abs(fft[pos_mask]) / n
        
        return freqs, magnitude
    
    def plot_wave_analysis(self, save_path: str = "harmonic_wave_analysis.png"):
        """Generate comprehensive wave analysis visualization"""
        if self.composite_wave is None:
            self.generate_composite_wave()
        
        fig = plt.figure(figsize=(16, 12), facecolor='#1a1a2e')
        fig.suptitle('🌊⚡ HARMONIC MARKET WAVE SIMULATION ⚡🌊', 
                     fontsize=16, color='white', fontweight='bold')
        
        # Color scheme
        bg_color = '#1a1a2e'
        text_color = '#ffffff'
        grid_color = '#2d2d44'
        wave_color = '#00ff88'
        spectrum_color = '#ff6b6b'
        
        # 1. Composite Wave
        ax1 = fig.add_subplot(3, 2, 1, facecolor=bg_color)
        ax1.plot(self.time_series, self.composite_wave, color=wave_color, linewidth=0.8)
        ax1.fill_between(self.time_series, self.composite_wave, alpha=0.3, color=wave_color)
        ax1.set_title('Composite Market Wave', color=text_color, fontsize=12)
        ax1.set_xlabel('Time (s)', color=text_color)
        ax1.set_ylabel('Amplitude', color=text_color)
        ax1.tick_params(colors=text_color)
        ax1.grid(True, color=grid_color, alpha=0.3)
        ax1.set_xlim(0, 2)  # Show first 2 seconds
        
        # 2. Frequency Spectrum
        freqs, magnitude = self.generate_frequency_spectrum()
        ax2 = fig.add_subplot(3, 2, 2, facecolor=bg_color)
        ax2.plot(freqs[:500], magnitude[:500], color=spectrum_color, linewidth=0.8)
        ax2.fill_between(freqs[:500], magnitude[:500], alpha=0.3, color=spectrum_color)
        ax2.set_title('Frequency Spectrum', color=text_color, fontsize=12)
        ax2.set_xlabel('Frequency (Hz)', color=text_color)
        ax2.set_ylabel('Magnitude', color=text_color)
        ax2.tick_params(colors=text_color)
        ax2.grid(True, color=grid_color, alpha=0.3)
        
        # Mark Solfeggio frequencies
        for name, freq in SOLFEGGIO.items():
            scaled_freq = freq / 100
            if scaled_freq < 500:
                ax2.axvline(x=scaled_freq, color='yellow', alpha=0.5, linestyle='--', linewidth=0.5)
        
        # 3. Individual Wave Components (Solfeggio)
        ax3 = fig.add_subplot(3, 2, 3, facecolor=bg_color)
        t_short = self.time_series[:1000]  # First second
        
        for i, (name, freq) in enumerate(list(SOLFEGGIO.items())[:4]):
            vis_freq = freq / 100
            wave = np.sin(2 * np.pi * vis_freq * t_short)
            ax3.plot(t_short, wave + i*2.5, label=f'{name} ({freq}Hz)', linewidth=0.8)
        
        ax3.set_title('Solfeggio Components', color=text_color, fontsize=12)
        ax3.set_xlabel('Time (s)', color=text_color)
        ax3.tick_params(colors=text_color)
        ax3.legend(loc='upper right', fontsize=8)
        ax3.grid(True, color=grid_color, alpha=0.3)
        
        # 4. Market State Distribution (Polar)
        ax4 = fig.add_subplot(3, 2, 4, facecolor=bg_color, projection='polar')
        
        if self.wave_points:
            # Group by state
            state_counts = {}
            for wp in self.wave_points:
                state_counts[wp.state] = state_counts.get(wp.state, 0) + 1
            
            states = list(state_counts.keys())
            counts = list(state_counts.values())
            angles = np.linspace(0, 2*np.pi, len(states), endpoint=False)
            
            colors = ['#2ecc71', '#27ae60', '#3498db', '#f39c12', '#e67e22', '#e74c3c', '#c0392b']
            bars = ax4.bar(angles, counts, width=0.5, alpha=0.7, color=colors[:len(states)])
            ax4.set_title('Market State Distribution', color=text_color, fontsize=12, pad=20)
        else:
            ax4.text(0, 0, 'No Data', ha='center', va='center', color=text_color)
        
        # 5. Phase Space (Amplitude vs Frequency)
        ax5 = fig.add_subplot(3, 2, 5, facecolor=bg_color)
        
        if self.wave_points:
            freqs_plot = [wp.frequency for wp in self.wave_points]
            amps_plot = [wp.amplitude for wp in self.wave_points]
            probs_plot = [wp.probability for wp in self.wave_points]
            
            scatter = ax5.scatter(freqs_plot, amps_plot, c=probs_plot, cmap='RdYlGn', 
                                  s=50, alpha=0.7, edgecolors='white', linewidths=0.5)
            plt.colorbar(scatter, ax=ax5, label='Probability')
            
            # Mark key frequencies
            for name, freq in [('LOVE', 528), ('NATURAL', 432), ('DISTORTION', 440)]:
                ax5.axvline(x=freq, color='white', alpha=0.3, linestyle='--', linewidth=0.5)
                ax5.text(freq, 0.95, name, rotation=90, ha='right', va='top', 
                        color='white', fontsize=7, alpha=0.7)
        
        ax5.set_title('Phase Space: Amplitude vs Frequency', color=text_color, fontsize=12)
        ax5.set_xlabel('Frequency (Hz)', color=text_color)
        ax5.set_ylabel('Amplitude (Probability)', color=text_color)
        ax5.tick_params(colors=text_color)
        ax5.grid(True, color=grid_color, alpha=0.3)
        
        # 6. Wave Coherence Over Time
        ax6 = fig.add_subplot(3, 2, 6, facecolor=bg_color)
        
        # Calculate rolling coherence
        window = 100
        coherence = np.zeros(len(self.composite_wave) - window)
        for i in range(len(coherence)):
            segment = self.composite_wave[i:i+window]
            coherence[i] = 1 - np.std(segment) / (np.mean(np.abs(segment)) + 0.001)
        
        t_coherence = self.time_series[window//2:-window//2]
        ax6.plot(t_coherence, coherence, color='#9b59b6', linewidth=0.8)
        ax6.fill_between(t_coherence, coherence, alpha=0.3, color='#9b59b6')
        ax6.axhline(y=0.5, color='yellow', linestyle='--', alpha=0.5, label='Coherence Threshold')
        ax6.set_title('Wave Coherence Over Time', color=text_color, fontsize=12)
        ax6.set_xlabel('Time (s)', color=text_color)
        ax6.set_ylabel('Coherence', color=text_color)
        ax6.tick_params(colors=text_color)
        ax6.grid(True, color=grid_color, alpha=0.3)
        ax6.legend(loc='upper right', fontsize=8)
        ax6.set_ylim(0, 1)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, facecolor=bg_color, edgecolor='none')
        plt.savefig(save_path.replace('.png', '.svg'), format='svg', facecolor=bg_color)
        print(f"✅ Saved wave analysis: {save_path}")
        
        return fig
    
    def generate_wave_data_json(self, output_path: str = "harmonic_wave_data.json"):
        """Export wave simulation data as JSON for further analysis"""
        if self.composite_wave is None:
            self.generate_composite_wave()
        
        # Downsample for JSON (every 10th point)
        step = 10
        
        data = {
            'generated': datetime.now().isoformat(),
            'description': 'Harmonic wave simulation from market data',
            'parameters': {
                'phi': PHI,
                'schumann': SCHUMANN,
                'solfeggio': SOLFEGGIO,
            },
            'wave_points': [
                {
                    'symbol': wp.symbol,
                    'price': wp.price,
                    'probability': wp.probability,
                    'frequency': wp.frequency,
                    'amplitude': wp.amplitude,
                    'phase': wp.phase,
                    'state': wp.state,
                }
                for wp in self.wave_points
            ],
            'composite_wave': {
                'time': self.time_series[::step].tolist(),
                'amplitude': self.composite_wave[::step].tolist(),
                'sample_rate': 1000,
                'duration_sec': float(self.time_series[-1]),
            },
            'statistics': {
                'mean_amplitude': float(np.mean(self.composite_wave)),
                'std_amplitude': float(np.std(self.composite_wave)),
                'max_amplitude': float(np.max(self.composite_wave)),
                'min_amplitude': float(np.min(self.composite_wave)),
                'zero_crossings': int(np.sum(np.diff(np.sign(self.composite_wave)) != 0)),
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Saved wave data: {output_path}")
        return data
    
    def print_wave_summary(self):
        """Print summary of wave simulation"""
        print(f"""
╔══════════════════════════════════════════════════════════════════════════╗
║  🌊⚡ HARMONIC WAVE SIMULATION SUMMARY ⚡🌊                              ║
╠══════════════════════════════════════════════════════════════════════════╣
║  Wave Points Loaded:    {len(self.wave_points):5d}                                        ║
║  Base Harmonics:        {len(self.wave_components):5d} (Solfeggio)                              ║
║  Golden Ratio (φ):      {PHI:.6f}                                      ║
║  Schumann Resonance:    {SCHUMANN:.2f} Hz                                        ║
╠══════════════════════════════════════════════════════════════════════════╣""")
        
        if self.composite_wave is not None:
            stats = {
                'mean': np.mean(self.composite_wave),
                'std': np.std(self.composite_wave),
                'max': np.max(self.composite_wave),
                'min': np.min(self.composite_wave),
            }
            print(f"""║  COMPOSITE WAVE STATISTICS                                               ║
╠══════════════════════════════════════════════════════════════════════════╣
║  Mean Amplitude:        {stats['mean']:+.6f}                                    ║
║  Std Deviation:         {stats['std']:.6f}                                     ║
║  Max Amplitude:         {stats['max']:+.6f}                                    ║
║  Min Amplitude:         {stats['min']:+.6f}                                    ║""")
        
        if self.wave_points:
            # State distribution
            state_counts = {}
            for wp in self.wave_points:
                state_counts[wp.state] = state_counts.get(wp.state, 0) + 1
            
            print(f"""╠══════════════════════════════════════════════════════════════════════════╣
║  MARKET STATE DISTRIBUTION                                               ║
╠══════════════════════════════════════════════════════════════════════════╣""")
            for state, count in sorted(state_counts.items(), key=lambda x: -x[1]):
                pct = count / len(self.wave_points) * 100
                bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
                print(f"║  {state:20s} {bar} {count:4d} ({pct:5.1f}%)      ║")
        
        print(f"""╚══════════════════════════════════════════════════════════════════════════╝
""")


def main():
    """Run harmonic wave simulation"""
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║  🌊⚡ HARMONIC WAVE SIMULATION ENGINE ⚡🌊                               ║
║  Transforming Market Chaos into Coherent Waves                           ║
╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    simulator = HarmonicWaveSimulator()
    
    # Load market data from reports
    print("📊 Loading market data...")
    
    # Try multiple report sources
    loaded = 0
    for report in ['probability_all_markets_report.json', 'probability_kraken_report.json']:
        if os.path.exists(report):
            loaded += simulator.load_market_data(report)
            break
    
    if loaded == 0:
        print("⚠️ No market reports found, generating synthetic data...")
        # Generate synthetic wave points for demo
        for i in range(50):
            prob = 0.3 + 0.5 * np.random.random()
            state_idx = int(prob * 6)
            states = ['EXTREME_BEARISH', 'BEARISH', 'SLIGHT_BEARISH', 'NEUTRAL', 'SLIGHT_BULLISH', 'BULLISH', 'EXTREME_BULLISH']
            
            simulator.wave_points.append(MarketWavePoint(
                timestamp=datetime.now() - timedelta(minutes=50-i),
                symbol=f'SYN{i}',
                price=100 + np.random.randn() * 10,
                probability=prob,
                frequency=STATE_FREQ[states[min(state_idx, 6)]],
                amplitude=prob,
                phase=np.random.random() * 2 * np.pi,
                state=states[min(state_idx, 6)]
            ))
    
    # Generate composite wave
    print("\n🌊 Generating composite harmonic wave...")
    t, wave = simulator.generate_composite_wave(duration_sec=10.0)
    
    # Print summary
    simulator.print_wave_summary()
    
    # Generate visualization
    print("📈 Generating wave analysis visualization...")
    simulator.plot_wave_analysis("harmonic_wave_analysis.png")
    
    # Export data
    print("\n💾 Exporting wave data...")
    simulator.generate_wave_data_json("harmonic_wave_data.json")
    
    print("\n✨ Harmonic Wave Simulation Complete!")
    print("   📊 harmonic_wave_analysis.png")
    print("   📊 harmonic_wave_analysis.svg")
    print("   📄 harmonic_wave_data.json")


if __name__ == "__main__":
    main()
