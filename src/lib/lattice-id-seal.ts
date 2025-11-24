// src/lib/lattice-id-seal.ts
// TypeScript equivalent of Unity LatticeIDSeal.cs for web integration

export class LatticeIDSeal {
  /**
   * Deterministic phase anchor in [0, 2π) from an ID.
   */
  static anchorPhase(latticeId?: string): number {
    if (!latticeId) return 0;
    
    let h = 0;
    for (let i = 0; i < latticeId.length; i++) {
      h = (h * 131 + latticeId.charCodeAt(i)) >>> 0; // unsigned 32-bit
    }
    
    return ((h % 10000) / 10000) * (Math.PI * 2);
  }

  /**
   * Soft safety clamp for amplitude.
   */
  static safeGain(requested: number, cap: number = 3.0): number {
    return Math.max(0.2, Math.min(cap, requested));
  }

  /**
   * Generate observer-specific phase offset for timeline synchronization
   */
  static observerPhaseOffset(latticeId: string, timeIndex: number): number {
    const basePhase = this.anchorPhase(latticeId);
    const timePhase = (timeIndex * 0.618034) % (Math.PI * 2); // Golden angle
    return (basePhase + timePhase) % (Math.PI * 2);
  }

  /**
   * Calculate coherence score based on lattice ID and tensor field
   */
  static coherenceScore(latticeId: string, tensorField: Array<{phi: number, psi: number}>): number {
    if (!tensorField.length) return 0;
    
    const anchorPhase = this.anchorPhase(latticeId);
    let totalCoherence = 0;
    
    for (const datum of tensorField) {
      const phaseDiff = Math.abs(Math.cos(datum.phi - anchorPhase));
      const amplitudeWeight = Math.abs(datum.psi);
      totalCoherence += phaseDiff * amplitudeWeight;
    }
    
    return totalCoherence / tensorField.length;
  }
}