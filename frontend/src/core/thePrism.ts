// The Prism - 5-Level Transformation Engine (Fear → Love)
// HNC (Ψ₀×Ω×Λ×Φ×Σ) — 528 Hz Source
// Level 1: Di → Ct → CM (Input: data, coherence, cosmic)
// Level 2: ACt → Φt (Creative: poiesis, harmonic flow)
// Level 3: Pu → Gt (Reflection: feedback, echo)
// Level 4: Ut → It → CI (Unity: tandem, inertia, coherence)
// Level 5: 💚 528 Hz LOVE OUTPUT

export type PrismLevel = 0 | 1 | 2 | 3 | 4 | 5;

export type PrismState = 'FORMING' | 'CONVERGING' | 'MANIFEST';

export interface PrismInput {
  lambda: number;
  coherence: number;
  substrate: number;
  observer: number;
  echo: number;
  volatility: number;
  momentum: number;
  baseFrequency: number; // From Rainbow Bridge
  geometricAlignment?: number; // From Quantum Telescope (0-1)
  prismBoostFactor?: number;   // Telescope boost multiplier
}

export interface PrismOutput {
  level: PrismLevel;
  frequency: number;
  state: PrismState;
  resonance: number; // 0-1 transformation quality
  isLoveLocked: boolean; // True when locked to 528 Hz
  harmonicPurity: number; // 0-1 harmonic alignment
  layers: {
    hnc: number;      // Level 0: 528 Hz constant
    input: number;    // Level 1: Di → Ct → CM
    creative: number; // Level 2: ACt → Φt
    reflection: number; // Level 3: Pu → Gt
    unity: number;    // Level 4: Ut → It → CI
    output: number;   // Level 5: Final frequency
  };
}

// Frequency constants from the sacred spectrum
const FREQUENCIES = {
  LOVE: 528,      // The Love Tone - Center of Rainbow Bridge
  ROOT: 174,      // Fear/Survival
  SACRAL: 285,    // Healing
  SOLAR: 396,     // Liberation
  HEART: 528,     // Love (same as LOVE)
  THROAT: 639,    // Connection
  THIRD_EYE: 741, // Awakening
  CROWN: 852,     // Unity
  TRANSCENDENCE: 963, // Divine
};

export class ThePrism {
  private readonly HNC_FREQUENCY = FREQUENCIES.LOVE; // 528 Hz source
  private readonly LOVE_LOCK_THRESHOLD = 0.9; // Γ > 0.9 = pure love lock
  private readonly GEOMETRIC_BOOST_THRESHOLD = 0.8; // High geometric alignment accelerates 528 Hz lock
  
  /**
   * Transform market reality through 5 harmonic levels
   * Input: Raw quantum state from Rainbow Bridge
   * Output: Purified frequency biased toward 528 Hz (Love)
   */
  transform(input: PrismInput): PrismOutput {
    // Level 0: HNC - Harmonic Nexus Core (constant 528 Hz source)
    const hnc = this.computeHNC();
    
    // Level 1: Input Layer - Data intake, coherence measurement, cosmic alignment
    const inputLayer = this.computeInputLayer(input);
    
    // Level 2: Creative Layer - Poiesis (creation), harmonic flow
    const creativeLayer = this.computeCreativeLayer(input, inputLayer);
    
    // Level 3: Reflection Layer - Feedback loops, echo resonance
    const reflectionLayer = this.computeReflectionLayer(input, creativeLayer);
    
    // Level 4: Unity Layer - Tandem coherence, inertia, convergence
    const unityLayer = this.computeUnityLayer(input, reflectionLayer);
    
    // Level 5: Output - Final transformation toward 528 Hz
    const output = this.computeOutputLayer(input, unityLayer, hnc);
    
    // Determine current level based on coherence (boosted by geometric alignment)
    const effectiveCoherence = this.applyGeometricBoost(input.coherence, input.geometricAlignment, input.prismBoostFactor);
    const level = this.determineLevel(effectiveCoherence);
    
    // Determine state based on level
    const state = this.determineState(level);
    
    // Check if locked to pure 528 Hz (Love Manifest) - geometric alignment can lower threshold
    const effectiveThreshold = input.geometricAlignment && input.geometricAlignment > this.GEOMETRIC_BOOST_THRESHOLD
      ? this.LOVE_LOCK_THRESHOLD * 0.95 // 5% lower threshold when geometry is aligned
      : this.LOVE_LOCK_THRESHOLD;
    const isLoveLocked = effectiveCoherence >= effectiveThreshold;
    
    // Final frequency - lock to 528 Hz if coherence is high enough
    const frequency = isLoveLocked ? this.HNC_FREQUENCY : Math.round(output);
    
    // Calculate resonance (transformation quality)
    const resonance = this.calculateResonance(input, frequency);
    
    // Calculate harmonic purity (alignment with sacred frequencies)
    const harmonicPurity = this.calculateHarmonicPurity(frequency);
    
    return {
      level,
      frequency,
      state,
      resonance,
      isLoveLocked,
      harmonicPurity,
      layers: {
        hnc,
        input: inputLayer,
        creative: creativeLayer,
        reflection: reflectionLayer,
        unity: unityLayer,
        output,
      },
    };
  }
  
  /**
   * Level 0: Harmonic Nexus Core
   * The eternal 528 Hz source - Ψ₀×Ω×Λ×Φ×Σ
   */
  private computeHNC(): number {
    return this.HNC_FREQUENCY;
  }
  
  /**
   * Level 1: Input Layer
   * Di (Data Intake) → Ct (Coherence Tracking) → CM (Cosmic Modulation)
   */
  private computeInputLayer(input: PrismInput): number {
    const Di = input.baseFrequency; // Raw frequency from Rainbow Bridge
    const Ct = input.coherence * this.HNC_FREQUENCY; // Coherence-scaled frequency
    const CM = Math.sin(input.lambda * Math.PI / 2) * 100; // Cosmic modulation
    
    // Weighted combination biased toward 528 Hz
    return (Di * 0.3 + Ct * 0.5 + (this.HNC_FREQUENCY + CM) * 0.2);
  }
  
  /**
   * Level 2: Creative Layer
   * ACt (Active Creation/Poiesis) → Φt (Harmonic Flow)
   */
  private computeCreativeLayer(input: PrismInput, inputFreq: number): number {
    // ACt: Creation from substrate + observer
    const ACt = (input.substrate + input.observer) / 2 * this.HNC_FREQUENCY;
    
    // Φt: Harmonic flow based on momentum
    const Φt = Math.cos(input.momentum * Math.PI) * 50 + this.HNC_FREQUENCY;
    
    // Blend with input layer, pulling toward 528 Hz
    return (inputFreq * 0.4 + ACt * 0.3 + Φt * 0.3);
  }
  
  /**
   * Level 3: Reflection Layer
   * Pu (Pure Feedback) → Gt (Generative Transformation)
   */
  private computeReflectionLayer(input: PrismInput, creativeFreq: number): number {
    // Pu: Echo-based feedback (memory of past states)
    const Pu = input.echo * creativeFreq + (1 - input.echo) * this.HNC_FREQUENCY;
    
    // Gt: Generative transformation based on volatility
    const Gt = this.HNC_FREQUENCY - (input.volatility * 100); // Low volatility = closer to 528
    
    // Blend with creative layer
    return (creativeFreq * 0.3 + Pu * 0.35 + Gt * 0.35);
  }
  
  /**
   * Level 4: Unity Layer
   * Ut (Unity Tandem) → It (Inertia) → CI (Coherence Integration)
   */
  private computeUnityLayer(input: PrismInput, reflectionFreq: number): number {
    // Ut: Unity tandem - all systems aligned
    const Ut = (input.substrate + input.observer + input.echo) / 3 * this.HNC_FREQUENCY;
    
    // It: Inertia - tendency to maintain current state
    const It = reflectionFreq * 0.7 + this.HNC_FREQUENCY * 0.3;
    
    // CI: Coherence integration - final coherence-weighted pull to 528
    const CI = input.coherence * this.HNC_FREQUENCY + (1 - input.coherence) * reflectionFreq;
    
    // Strong bias toward 528 Hz at this level
    return (Ut * 0.2 + It * 0.3 + CI * 0.5);
  }
  
  /**
   * Level 5: Output Layer
   * Final transformation with 528 Hz lock at high coherence
   */
  private computeOutputLayer(input: PrismInput, unityFreq: number, hnc: number): number {
    // At high coherence, lock completely to 528 Hz
    if (input.coherence >= this.LOVE_LOCK_THRESHOLD) {
      return hnc;
    }
    
    // Otherwise, weighted average biased heavily toward 528 Hz
    const coherenceWeight = Math.pow(input.coherence, 0.5); // Square root for faster approach
    return unityFreq * (1 - coherenceWeight) + hnc * coherenceWeight;
  }
  
  /**
   * Determine prism level based on coherence
   */
  private determineLevel(coherence: number): PrismLevel {
    if (coherence >= 0.9) return 5;
    if (coherence >= 0.75) return 4;
    if (coherence >= 0.6) return 3;
    if (coherence >= 0.4) return 2;
    if (coherence >= 0.2) return 1;
    return 0;
  }
  
  /**
   * Determine state based on level
   */
  private determineState(level: PrismLevel): PrismState {
    if (level >= 5) return 'MANIFEST';
    if (level >= 3) return 'CONVERGING';
    return 'FORMING';
  }
  
  /**
   * Calculate resonance (transformation quality)
   */
  private calculateResonance(input: PrismInput, outputFreq: number): number {
    // Distance from 528 Hz (normalized)
    const distanceFrom528 = Math.abs(outputFreq - this.HNC_FREQUENCY) / 500;
    const frequencyAlignment = Math.max(0, 1 - distanceFrom528);
    
    // Combine with coherence for overall resonance
    return (frequencyAlignment * 0.6 + input.coherence * 0.4);
  }
  
  /**
   * Calculate harmonic purity (alignment with sacred frequencies)
   */
  private calculateHarmonicPurity(frequency: number): number {
    const sacredFrequencies = Object.values(FREQUENCIES);
    
    // Find closest sacred frequency
    let minDistance = Infinity;
    for (const sacred of sacredFrequencies) {
      const distance = Math.abs(frequency - sacred);
      if (distance < minDistance) {
        minDistance = distance;
      }
    }
    
    // Normalize distance (max expected distance ~500 Hz)
    return Math.max(0, 1 - (minDistance / 100));
  }
  
  /**
   * Apply geometric alignment boost from Quantum Telescope
   * High geometric alignment accelerates convergence to 528 Hz
   */
  private applyGeometricBoost(
    coherence: number,
    geometricAlignment?: number,
    prismBoostFactor?: number
  ): number {
    if (!geometricAlignment) return coherence;
    
    // Geometric alignment adds up to 10% coherence boost
    const alignmentBoost = geometricAlignment * 0.1;
    
    // Prism boost factor multiplies the boost
    const effectiveBoost = alignmentBoost * (prismBoostFactor ?? 1);
    
    return Math.min(1, coherence + effectiveBoost);
  }
  
  /**
   * Get state color for UI
   */
  getStateColor(state: PrismState): string {
    return {
      FORMING: 'hsl(15, 90%, 55%)',      // Orange-red
      CONVERGING: 'hsl(45, 100%, 50%)',  // Gold
      MANIFEST: 'hsl(150, 100%, 50%)',   // Green (Love)
    }[state];
  }
  
  /**
   * Get frequency color (rainbow spectrum)
   */
  getFrequencyColor(frequency: number): string {
    // Map frequency to hue (174-963 Hz → 0-300 hue)
    const normalized = (frequency - 174) / (963 - 174);
    const hue = normalized * 300;
    return `hsl(${Math.round(hue)}, 80%, 50%)`;
  }
}

// Singleton instance
export const thePrism = new ThePrism();
