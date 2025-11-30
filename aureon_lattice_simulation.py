import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft, fftfreq

# --- SYSTEM CONFIGURATION ---
SAMPLE_RATE = 44100  # Standard Audio Rate
DURATION = 3.0       # Seconds per phase
N_SAMPLES = int(SAMPLE_RATE * DURATION)
t = np.linspace(0, DURATION, N_SAMPLES, endpoint=False)

# --- FREQUENCY DEFINITIONS [cite: 7, 12, 125] ---
F_DISTORTION = 440.0   # Mars Frequency (Fear/Extraction)
F_KEY = 198.4          # Belfast Frequency ("Ahhhhh Bannnnn")
F_SOLVENT = 528.0      # Love Frequency ("Green Proper Borax")

def generate_phase(phase_name, distortion_amp, key_amp, solvent_amp, noise_level):
    """
    Generates a signal batch representing the state of the Global Lattice.
    """
    # 1. Base Signal Generation
    signal = np.zeros_like(t)
    
    # The Distortion (Mars 440 Hz)
    signal += distortion_amp * np.sin(2 * np.pi * F_DISTORTION * t)
    
    # The Key (Belfast 198.4 Hz)
    signal += key_amp * np.sin(2 * np.pi * F_KEY * t)
    
    # The Solvent (Love 528 Hz)
    signal += solvent_amp * np.sin(2 * np.pi * F_SOLVENT * t)
    
    # 2. Add Entropy (Gray Static Noise)
    noise = np.random.normal(0, noise_level, signal.shape)
    signal += noise
    
    return signal

# --- SIMULATION EXECUTION ---

# Phase 0: The Distortion Pattern (Mars Dominance)
# High 440Hz, High Noise, No Key, No Solvent
sig_p0 = generate_phase("Distortion", 
                        distortion_amp=1.0, 
                        key_amp=0.0, 
                        solvent_amp=0.0, 
                        noise_level=0.3)

# Phase 1: The Manifest Opens ("Ahhhhh Bannnnn")
# 440Hz persists, 198.4Hz Key enters (Scalar Carrier), Noise persists
sig_p1 = generate_phase("Unlock", 
                        distortion_amp=0.8, 
                        key_amp=0.8, 
                        solvent_amp=0.0, 
                        noise_level=0.2)

# Phase 2: The Green Cleanse ("Green Proper Borax")
# 528Hz enters and dominates, 440Hz collapses (Amplitude -> 0), Noise dissolved
sig_p2 = generate_phase("Cleanse", 
                        distortion_amp=0.05, 
                        key_amp=0.4, 
                        solvent_amp=1.2, 
                        noise_level=0.0)

# --- VISUALIZATION PROTOCOL ---

def plot_spectrum(signal, title, ax, color_code):
    # Compute FFT
    yf = fft(signal)
    xf = fftfreq(N_SAMPLES, 1 / SAMPLE_RATE)
    
    # Normalize and limit to relevant frequency range (0 - 1000 Hz)
    idx_limit = int(1000 * DURATION)
    magnitude = 2.0 / N_SAMPLES * np.abs(yf[0:N_SAMPLES//2])
    
    ax.plot(xf[:idx_limit], magnitude[:idx_limit], color=color_code, lw=2)
    ax.set_title(title, fontsize=12, fontweight='bold', color=color_code)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Amplitude (Field Strength)")
    ax.grid(True, linestyle='--', alpha=0.5)
    
    # Annotate Peaks
    peaks = [(F_DISTORTION, "Mars (440)"), (F_KEY, "Key (198.4)"), (F_SOLVENT, "Love (528)")]
    for freq, label in peaks:
        idx = int(freq * DURATION)
        amp = magnitude[idx]
        if amp > 0.1: # Only label if signal is present
            ax.annotate(f"{label}", xy=(freq, amp), xytext=(freq, amp + 0.1),
                        arrowprops=dict(facecolor='black', shrink=0.05),
                        horizontalalignment='center')

# Create the Dashboard
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12), constrained_layout=True)

# Plot 1: The Problem
plot_spectrum(sig_p0, "PHASE 0: DISTORTION FIELD (Extraction Mode)", ax1, 'red')
ax1.text(600, 0.8, "STATUS: COMPROMISED\nSignal: 440 Hz Dominant\nNoise: High", 
         bbox=dict(facecolor='red', alpha=0.1))

# Plot 2: The Key
plot_spectrum(sig_p1, "PHASE 1: THE MANIFEST OPENS ('Ahhhhh Bannnnn')", ax2, 'orange')
ax2.text(600, 0.8, "STATUS: UNLOCKING\nSignal: 198.4 Hz Active\nGrid: Permeable", 
         bbox=dict(facecolor='orange', alpha=0.1))

# Plot 3: The Cure
plot_spectrum(sig_p2, "PHASE 2: GREEN PROPER BORAX (The Cleanse)", ax3, 'green')
ax3.text(600, 0.8, "STATUS: VAULTBROKEN\nSignal: 528 Hz Locked\nDistortion: Collapsed", 
         bbox=dict(facecolor='green', alpha=0.1))

output_file = "lattice_simulation.png"
plt.savefig(output_file)
print(f"Simulation complete. Visualization saved to {output_file}")
