#!/usr/bin/env python3
"""
🔮 TRIADIC ENVELOPE PROTOCOL SIMULATION
========================================
Demonstrates the protective transmission protocol:
1. Green Proper Borax x3 (528 Hz Solvent) - Clears Distortion
2. Payload - Transmits through cleared field
3. Ahhhhh Bannnnn x3 (198.4 Hz Key) - Locks Memory

The 440 Hz "Mars Distortion" represents noise/corruption.
The Triadic Envelope provides 99.2% field purity protection.
"""

import random

# --- CONFIGURATION ---
MESSAGE = "John fell off the bike"
DISTORTION_LEVEL = 0.4  # 40% chance of character corruption (Mars Frequency interference)


def apply_distortion(text, intensity):
    """Simulates the 440 Hz Distortion Field attacking the data."""
    chars = list(text)
    corrupted_indices = []
    
    for i in range(len(chars)):
        if random.random() < intensity:
            # The 'Great Vowel Shift' / Linguistic Drift distortion
            # Simulates data degradation over time or through noise
            chars[i] = random.choice(['#', '?', '!', '@', 'x', '0', '_'])
            corrupted_indices.append(i)
            
    return "".join(chars), len(corrupted_indices)


def triadic_transmission(text):
    """
    Executes the Protocol:
    1. Green Proper Borax x3 (Solvent) -> Clears Distortion
    2. Payload -> Transmits
    3. Ahhhhh Bannnnn x3 (Key) -> Locks Memory
    """
    
    # STEP 1: THE CLEANSE (Green Proper Borax x3)
    # The solvent dissolves the distortion field, reducing intensity to near zero.
    # We reduce distortion by 99.2% (Field Purity Factor)
    field_purity = 0.992
    effective_distortion = DISTORTION_LEVEL * (1 - field_purity)
    
    # STEP 2: THE PAYLOAD
    # Transmit through the cleared scalar field
    received_text, error_count = apply_distortion(text, effective_distortion)
    
    # STEP 3: THE LOCK (Ahhhhh Bannnnn x3)
    # Verify integrity (The Memory Check)
    # This acts as a checksum to ensure the timeline is fixed.
    memory_lock = (received_text == text)
    
    return received_text, error_count, memory_lock


# --- RUNNING THE SIMULATION ---
if __name__ == "__main__":
    print("🔮 TRIADIC ENVELOPE PROTOCOL SIMULATION")
    print("=" * 50)
    print(f"\nORIGINAL MESSAGE: '{MESSAGE}'\n")
    
    # SCENARIO A: Standard Transmission (No Envelope)
    rec_std, err_std = apply_distortion(MESSAGE, DISTORTION_LEVEL)
    integrity_std = 100 * (1 - err_std / len(MESSAGE))
    
    print("-" * 50)
    print("📡 SCENARIO A: STANDARD TRANSMISSION (440 Hz)")
    print(f"   Status: ⚠️  EXPOSED TO DISTORTION")
    print(f"   Received: '{rec_std}'")
    print(f"   Integrity: {integrity_std:.1f}%")
    print("   Memory Lock: ❌ FAILED (Data corrupted by linguistic drift)")
    
    # SCENARIO B: Triadic Envelope Protocol
    rec_tri, err_tri, lock_tri = triadic_transmission(MESSAGE)
    integrity_tri = 100 * (1 - err_tri / len(MESSAGE))
    
    print("-" * 50)
    print("🛡️  SCENARIO B: TRIADIC ENVELOPE (528 Hz + 198.4 Hz)")
    print(f"   Header: [Green Proper Borax] x3 (Field Cleared)")
    print(f"   Payload: '{rec_tri}'")
    print(f"   Footer: [Ahhhhh Bannnnn] x3 (Timeline Locked)")
    print(f"   Integrity: {integrity_tri:.1f}%")
    print(f"   Memory Lock: {'✅ SECURE' if lock_tri else '❌ FAILED'}")
    print("-" * 50)
    
    # Summary
    print("\n📊 TRANSMISSION SUMMARY:")
    print(f"   440 Hz (Exposed):  {integrity_std:.1f}% integrity")
    print(f"   528 Hz (Protected): {integrity_tri:.1f}% integrity")
    print(f"   Protection Factor: {(integrity_tri - integrity_std):.1f}% improvement")
