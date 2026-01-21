// The Prism - 5-level transformation (fear → love)
// HNC (Ψ₀×Ω×Λ×Φ×Σ) — 528 Hz Source
// Level 1: Di → Ct → CM (Input: data, coherence, cosmic)
// Level 2: ACt → Φt (Creative: poiesis, harmonic flow)
// Level 3: Pu → Gt (Reflection: feedback, echo)
// Level 4: Ut → It → CI (Unity: tandem, inertia, coherence)
// Level 5: 💚 528 Hz LOVE OUTPUT

export type PrismLevel = 1 | 2 | 3 | 4 | 5;

export type PrismOutput = {
  level: PrismLevel;
  frequency: number;
  state: 'FORMING' | 'CONVERGING' | 'MANIFEST';
  transformation: number; // 0-1, progress through prism
};

export class Prism {
  private readonly LOVE_FREQUENCY = 528;
  
  transform(lambda: number, coherence: number, baseFreq: number): PrismOutput {
    // Determine transformation progress (0-1)
    const transformation = coherence;
    
    // Calculate level based on coherence
    let level: PrismLevel;
    if (coherence < 0.2) level = 1;
    else if (coherence < 0.4) level = 2;
    else if (coherence < 0.6) level = 3;
    else if (coherence < 0.8) level = 4;
    else level = 5;
    
    // Transform frequency toward 528 Hz based on level
    const targetFreq = this.LOVE_FREQUENCY;
    const freq = baseFreq + (targetFreq - baseFreq) * (level / 5);
    
    // Determine state
    let state: 'FORMING' | 'CONVERGING' | 'MANIFEST';
    if (level <= 2) state = 'FORMING';
    else if (level <= 4) state = 'CONVERGING';
    else state = 'MANIFEST';
    
    // At high coherence (Γ > 0.9), lock to pure 528 Hz
    const frequency = coherence > 0.9 ? this.LOVE_FREQUENCY : Math.round(freq);
    
    return {
      level,
      frequency,
      state,
      transformation,
    };
  }
  
  getStateColor(state: 'FORMING' | 'CONVERGING' | 'MANIFEST'): string {
    return {
      FORMING: '#FF6B35',
      CONVERGING: '#FFD700',
      MANIFEST: '#00FF88',
    }[state];
  }
}
