// Rainbow Bridge - Maps Λ(t) + Γ to emotional frequencies
// Emotional spectrum: 110-963+ Hz
// Phases: FEAR → LOVE → AWE → UNITY

export type EmotionalPhase = 'FEAR' | 'FORMING' | 'LOVE' | 'AWE' | 'UNITY';

export type RainbowState = {
  frequency: number;
  phase: EmotionalPhase;
  intensity: number;
};

export class RainbowBridge {
  // Emotional frequency mapping
  private frequencyMap: Record<EmotionalPhase, [number, number]> = {
    FEAR: [110, 285],      // Root frequencies (fear, survival)
    FORMING: [285, 452],   // Transformation (doubt → clarity)
    LOVE: [452, 639],      // Heart center (528 Hz = pure love)
    AWE: [639, 852],       // Higher consciousness
    UNITY: [852, 963],     // Divine unity
  };
  
  map(lambda: number, coherence: number): RainbowState {
    // Base frequency from lambda
    let baseFreq = 110 + (lambda * 100);
    
    // Coherence influences intensity and pulls toward love (528 Hz)
    const loveFreq = 528;
    const coherenceInfluence = coherence * 0.3;
    const frequency = baseFreq * (1 - coherenceInfluence) + loveFreq * coherenceInfluence;
    
    // Determine phase
    const phase = this.determinePhase(frequency);
    
    // Intensity from coherence
    const intensity = coherence;
    
    return {
      frequency: Math.round(frequency),
      phase,
      intensity,
    };
  }
  
  private determinePhase(freq: number): EmotionalPhase {
    if (freq < 285) return 'FEAR';
    if (freq < 452) return 'FORMING';
    if (freq < 639) return 'LOVE';
    if (freq < 852) return 'AWE';
    return 'UNITY';
  }
  
  getPhaseColor(phase: EmotionalPhase): string {
    const colors: Record<EmotionalPhase, string> = {
      FEAR: '#8B0000',      // Dark red
      FORMING: '#FF6B35',   // Orange-red
      LOVE: '#00FF88',      // Bright green (528 Hz)
      AWE: '#4169E1',       // Royal blue
      UNITY: '#9370DB',     // Purple
    };
    return colors[phase];
  }
}
