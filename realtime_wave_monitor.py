#!/usr/bin/env python3
"""
🌊⚡ REAL-TIME HARMONIC WAVE MONITOR ⚡🌊
═══════════════════════════════════════════════════════════════

Live market data transformed into harmonic waveforms.
Continuously updates wave patterns as new data arrives.

Gary Leckey & GitHub Copilot | December 2025
"""

import os
import json
import math
import time
import numpy as np
from datetime import datetime
from typing import Dict, List

os.environ.setdefault('LIVE', '1')

# ═══════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════

PHI = (1 + math.sqrt(5)) / 2
SCHUMANN = 7.83

SOLFEGGIO = {
    'UT': 396, 'RE': 417, 'MI': 528, 
    'FA': 639, 'SOL': 741, 'LA': 852
}

STATE_FREQ = {
    'EXTREME_BULLISH': 528, 'BULLISH': 639, 'SLIGHT_BULLISH': 512,
    'NEUTRAL': 432, 'SLIGHT_BEARISH': 417, 'BEARISH': 396, 'EXTREME_BEARISH': 256,
}


def get_wave_char(amplitude: float) -> str:
    """Convert amplitude to wave character"""
    chars = '▁▂▃▄▅▆▇█'
    idx = int((amplitude + 1) / 2 * (len(chars) - 1))
    idx = max(0, min(len(chars) - 1, idx))
    return chars[idx]


def generate_wave_line(wave: np.ndarray, width: int = 60) -> str:
    """Generate ASCII wave visualization"""
    # Resample wave to width
    indices = np.linspace(0, len(wave) - 1, width).astype(int)
    samples = wave[indices]
    return ''.join(get_wave_char(s) for s in samples)


def calculate_coherence(wave: np.ndarray) -> float:
    """Calculate wave coherence (0-1)"""
    if len(wave) < 10:
        return 0.5
    std = np.std(wave)
    mean_abs = np.mean(np.abs(wave))
    if mean_abs < 0.001:
        return 0.5
    return max(0, min(1, 1 - std / mean_abs))


def calculate_dominant_frequency(wave: np.ndarray, sample_rate: int = 1000) -> float:
    """Find dominant frequency in wave"""
    fft = np.fft.fft(wave)
    freqs = np.fft.fftfreq(len(wave), 1/sample_rate)
    pos_mask = freqs > 0
    magnitudes = np.abs(fft[pos_mask])
    if len(magnitudes) == 0:
        return 0
    dominant_idx = np.argmax(magnitudes)
    return freqs[pos_mask][dominant_idx]


def map_frequency_to_solfeggio(freq: float) -> str:
    """Map frequency to nearest Solfeggio tone"""
    closest = min(SOLFEGGIO.items(), key=lambda x: abs(x[1] - freq * 100))
    return f"{closest[0]} ({closest[1]}Hz)"


def run_live_wave_monitor():
    """Run real-time wave monitoring"""
    from binance_client import BinanceClient
    from hnc_probability_matrix import HNCProbabilityIntegration
    
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║  🌊⚡ REAL-TIME HARMONIC WAVE MONITOR ⚡🌊                               ║
║  Live Market → Harmonic Waveform Transformation                          ║
╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    client = BinanceClient()
    integration = HNCProbabilityIntegration()
    
    # Track symbols
    symbols = ['BTCUSDC', 'ETHUSDC', 'SOLUSDC', 'XRPUSDC', 'AVAXUSDC']
    
    # Wave buffer
    wave_buffer = np.zeros(1000)
    price_history: Dict[str, List[float]] = {s: [] for s in symbols}
    
    iteration = 0
    
    try:
        while True:
            iteration += 1
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            print(f"\n{'═'*70}")
            print(f"  ⏱️  {timestamp} | Iteration #{iteration}")
            print(f"{'═'*70}")
            
            # Collect current data
            wave_components = []
            
            for symbol in symbols:
                try:
                    ticker = client.get_24h_ticker(symbol)
                    price = float(ticker.get('lastPrice', 0))
                    change = float(ticker.get('priceChangePercent', 0))
                    
                    # Track history
                    price_history[symbol].append(price)
                    if len(price_history[symbol]) > 100:
                        price_history[symbol] = price_history[symbol][-100:]
                    
                    # Calculate wave parameters
                    phi = PHI
                    freq = max(256, min(963, 432 * ((1 + change/100) ** phi)))
                    amplitude = max(0.1, min(1.0, 0.5 + change/20))
                    phase = ((change + 10) / 20) * 2 * math.pi
                    
                    # Determine state
                    if change > 5:
                        state = 'EXTREME_BULLISH'
                    elif change > 2:
                        state = 'BULLISH'
                    elif change > 0.5:
                        state = 'SLIGHT_BULLISH'
                    elif change > -0.5:
                        state = 'NEUTRAL'
                    elif change > -2:
                        state = 'SLIGHT_BEARISH'
                    elif change > -5:
                        state = 'BEARISH'
                    else:
                        state = 'EXTREME_BEARISH'
                    
                    wave_components.append({
                        'symbol': symbol,
                        'price': price,
                        'change': change,
                        'frequency': freq,
                        'amplitude': amplitude,
                        'phase': phase,
                        'state': state,
                    })
                    
                except Exception as e:
                    pass
            
            # Generate composite wave
            t = np.linspace(0, 1, 1000)
            composite = np.zeros(1000)
            
            for comp in wave_components:
                vis_freq = comp['frequency'] / 100
                wave = comp['amplitude'] * np.sin(2 * np.pi * vis_freq * t + comp['phase'])
                composite += wave
            
            # Normalize
            max_amp = np.max(np.abs(composite))
            if max_amp > 0:
                composite /= max_amp
            
            # Add Schumann modulation
            composite += 0.1 * np.sin(2 * np.pi * SCHUMANN * t)
            
            # Update buffer with smoothing
            wave_buffer = 0.7 * wave_buffer + 0.3 * composite
            
            # Calculate metrics
            coherence = calculate_coherence(wave_buffer)
            dom_freq = calculate_dominant_frequency(wave_buffer)
            solf_tone = map_frequency_to_solfeggio(dom_freq)
            
            # Display wave
            wave_viz = generate_wave_line(wave_buffer, 60)
            
            print(f"\n  🌊 COMPOSITE WAVE:")
            print(f"  ┌{'─'*62}┐")
            print(f"  │ {wave_viz} │")
            print(f"  └{'─'*62}┘")
            
            print(f"\n  📊 WAVE METRICS:")
            print(f"     Coherence:     {coherence:.1%} {'🟢' if coherence > 0.6 else '🟡' if coherence > 0.4 else '🔴'}")
            print(f"     Dom. Freq:     {dom_freq:.2f} Hz → {solf_tone}")
            print(f"     Amplitude:     {np.std(wave_buffer):.3f}")
            
            # Individual symbol waves
            print(f"\n  📈 SYMBOL WAVES:")
            for comp in wave_components:
                sym = comp['symbol'].replace('USDC', '')
                chg = comp['change']
                freq = comp['frequency']
                amp = comp['amplitude']
                state = comp['state']
                
                # Mini wave for this symbol
                mini_wave = amp * np.sin(2 * np.pi * (freq/100) * t + comp['phase'])
                mini_viz = generate_wave_line(mini_wave, 20)
                
                state_icon = '🚀' if 'EXTREME_BULL' in state else '📈' if 'BULL' in state else '📉' if 'BEAR' in state else '⚖️'
                
                print(f"     {sym:6s} {mini_viz} {chg:+6.2f}% {freq:5.0f}Hz {state_icon}")
            
            # Market sentiment
            bullish = len([c for c in wave_components if 'BULL' in c['state']])
            bearish = len([c for c in wave_components if 'BEAR' in c['state']])
            
            if bullish > bearish:
                sentiment = "BULLISH 🟢"
            elif bearish > bullish:
                sentiment = "BEARISH 🔴"
            else:
                sentiment = "NEUTRAL ⚪"
            
            print(f"\n  🎯 MARKET SENTIMENT: {sentiment}")
            print(f"     Bullish: {bullish} | Bearish: {bearish} | Neutral: {len(wave_components) - bullish - bearish}")
            
            # Harmonic resonance check
            love_proximity = abs(dom_freq * 100 - 528)
            if love_proximity < 30:
                print(f"\n  ✨ LOVE FREQUENCY RESONANCE DETECTED! ({528 - love_proximity:.0f}Hz proximity)")
            
            print(f"\n  ⏳ Next update in 5 seconds... (Ctrl+C to stop)")
            time.sleep(5)
            
    except KeyboardInterrupt:
        print(f"\n\n  👋 Wave monitor stopped.")
        
        # Save final state
        final_data = {
            'timestamp': datetime.now().isoformat(),
            'iterations': iteration,
            'final_coherence': float(coherence),
            'final_wave': wave_buffer.tolist()[:100],  # Sample
            'symbols_tracked': symbols,
        }
        
        with open('wave_monitor_final.json', 'w') as f:
            json.dump(final_data, f, indent=2)
        print(f"  💾 Saved final state: wave_monitor_final.json")


if __name__ == "__main__":
    run_live_wave_monitor()
