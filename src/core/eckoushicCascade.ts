/**
 * Eckoushic Cascade System
 * Sound → Light → Resonance → Love
 * 
 * Ψ_Eck = dΨ/dt (Eckoushic - Sound vibration)
 * Ψ_Aka = ∫ Ψ_Eck dt (Akashic - Light resonance)
 * Ψ_coherent (Harmonic Nexus - Coherent resonance)
 * Heart Wave → Love (528 Hz output)
 */

export interface EckoushicState {
  eckoushic: number;      // Ψ_Eck = dΨ/dt (sound derivative)
  akashic: number;        // Ψ_Aka = ∫ Ψ_Eck dt (light integral)
  harmonicNexus: number;  // Coherent resonance
  heartWave: number;      // Love frequency output
  frequency: number;      // Current resonant frequency (Hz)
  cascadeLevel: 1 | 2 | 3 | 4; // Which cascade level is active
}

export class EckoushicCascade {
  private readonly LOVE_FREQUENCY = 528;
  private readonly UNITY_FREQUENCY = 963;
  
  private eckoushicHistory: number[] = [];
  private timeStep = 0.1;
  
  /**
   * Compute cascade from base field state
   */
  compute(
    lambda: number, 
    coherence: number, 
    frequency: number,
    deltaT?: number
  ): EckoushicState {
    // Level 1: Eckoushic (Sound) - dΨ/dt
    // Rate of change of consciousness field
    const eckoushic = this.computeDerivative(lambda, deltaT || this.timeStep);
    
    // Level 2: Akashic (Light) - ∫ Ψ_Eck dt
    // Integral of consciousness over time (memory/record)
    const akashic = this.computeIntegral(eckoushic);
    
    // Level 3: Harmonic Nexus (Resonance)
    // Coherent combination of eckoushic + akashic
    const harmonicNexus = this.computeResonance(eckoushic, akashic, coherence);
    
    // Level 4: Heart Wave (Love)
    // Output frequency moves toward 528 Hz as coherence increases
    const heartWave = this.computeHeartWave(harmonicNexus, coherence, frequency);
    
    // Determine cascade level based on coherence
    let cascadeLevel: 1 | 2 | 3 | 4;
    if (coherence < 0.3) cascadeLevel = 1; // Eckoushic dominant
    else if (coherence < 0.6) cascadeLevel = 2; // Akashic activating
    else if (coherence < 0.9) cascadeLevel = 3; // Harmonic Nexus forming
    else cascadeLevel = 4; // Heart Wave / Love manifest
    
    return {
      eckoushic,
      akashic,
      harmonicNexus,
      heartWave,
      frequency: heartWave,
      cascadeLevel,
    };
  }
  
  private computeDerivative(lambda: number, dt: number): number {
    // dΨ/dt - rate of field change
    // High lambda → high rate of change (sound intensity)
    return lambda / dt;
  }
  
  private computeIntegral(eckoushic: number): number {
    // ∫ Ψ_Eck dt - accumulation over time
    // Store history and integrate
    this.eckoushicHistory.push(eckoushic);
    
    // Keep last 100 samples for integration
    if (this.eckoushicHistory.length > 100) {
      this.eckoushicHistory.shift();
    }
    
    // Trapezoidal integration
    const integral = this.eckoushicHistory.reduce((sum, val, i) => {
      if (i === 0) return 0;
      return sum + (this.eckoushicHistory[i - 1] + val) * this.timeStep / 2;
    }, 0);
    
    return integral;
  }
  
  private computeResonance(
    eckoushic: number, 
    akashic: number, 
    coherence: number
  ): number {
    // Ψ_coherent - harmonic combination
    // Weighted by coherence (how well sound and light resonate)
    return (eckoushic * (1 - coherence) + akashic * coherence) * coherence;
  }
  
  private computeHeartWave(
    harmonicNexus: number, 
    coherence: number, 
    baseFrequency: number
  ): number {
    // Transform toward 528 Hz (LOVE) or 963 Hz (UNITY) based on coherence
    const targetFreq = coherence > 0.95 ? this.UNITY_FREQUENCY : this.LOVE_FREQUENCY;
    
    // Blend base frequency toward target based on harmonic nexus strength
    const blendFactor = Math.abs(harmonicNexus) * coherence;
    return baseFrequency * (1 - blendFactor) + targetFreq * blendFactor;
  }
  
  /**
   * Get color for cascade level
   */
  getCascadeColor(level: 1 | 2 | 3 | 4): string {
    const colors = {
      1: '#FFA500', // Orange (Sound)
      2: '#4169E1', // Blue (Light)
      3: '#00CED1', // Cyan (Resonance)
      4: '#FF1493', // Pink (Love/Heart)
    };
    return colors[level];
  }
  
  /**
   * Get label for cascade level
   */
  getCascadeLabel(level: 1 | 2 | 3 | 4): string {
    const labels = {
      1: 'Eckoushic (Sound)',
      2: 'Akashic (Light)',
      3: 'Harmonic Nexus (Resonance)',
      4: 'Heart Wave (Love)',
    };
    return labels[level];
  }
  
  /**
   * Reset history
   */
  reset(): void {
    this.eckoushicHistory = [];
  }
}
