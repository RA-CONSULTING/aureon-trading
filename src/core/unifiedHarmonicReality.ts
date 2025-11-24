/**
 * Unified Harmonic Reality Framework
 * Integrates Master Equation, Eckoushic Cascade, Rainbow Bridge, and Prism
 * 
 * ROOT EQUATION:
 * Λ(t) = F_sub(t) + F_feedback(t) + F_observer(t)
 * 
 * ECKOUSHIC CASCADE:
 * Sound (Ψ_Eck) → Light (Ψ_Aka) → Resonance (Ψ_coherent) → Love (528 Hz)
 * 
 * UNITY EVENT:
 * Coherence → 1.0, Phase Spread → 0 @ t≈22 (Cycle Switch / Ego Death)
 */

import { MasterEquation, LambdaState } from './masterEquation';
import { EckoushicCascade, EckoushicState } from './eckoushicCascade';
import { RainbowBridge, RainbowState } from './rainbowBridge';
import { Prism, PrismOutput } from './prism';

export interface UnifiedHarmonicState {
  // Time
  t: number;
  
  // Master Equation
  lambda: LambdaState;
  
  // Eckoushic Cascade
  eckoushic: EckoushicState;
  
  // Rainbow Bridge
  rainbow: RainbowState;
  
  // Prism Transformation
  prism: PrismOutput;
  
  // Coherence Metrics
  coherence: number;
  coherenceLinear: number;    // C_lin (always 1.0 in stable regime)
  coherenceNonlinear: number; // C_nonlin (observer contribution)
  coherencePhi: number;       // C_phi (golden ratio coupling)
  
  // Field Metrics
  effectiveGain: number;      // G_eff
  qualityFactor: number;      // Q_abs (resonance quality)
  
  // Unity Event Detection
  unityProbability: number;   // 0-1, probability of unity/ego-death event
  phaseSpread: number;        // 0-1, separation metric (0 = unity)
  isUnityEvent: boolean;      // true when coherence ≈ 1.0 and phase spread ≈ 0
}

export class UnifiedHarmonicReality {
  private masterEq: MasterEquation;
  private cascade: EckoushicCascade;
  private bridge: RainbowBridge;
  private prism: Prism;
  
  private previousLambda = 0;
  private timeStep = 0.1;
  
  constructor() {
    this.masterEq = new MasterEquation();
    this.cascade = new EckoushicCascade();
    this.bridge = new RainbowBridge();
    this.prism = new Prism();
  }
  
  /**
   * Compute unified harmonic state at time t
   */
  compute(
    marketSnapshot: { 
      price: number; 
      volume: number; 
      volatility: number; 
      momentum: number; 
      spread: number;
      timestamp: number;
    },
    t: number
  ): UnifiedHarmonicState {
    // Step 1: Master Equation (Λ field dynamics)
    const lambdaState = await this.masterEq.step(marketSnapshot);
    
    // Step 2: Eckoushic Cascade (Sound → Light → Resonance → Love)
    const deltaLambda = lambdaState.lambda - this.previousLambda;
    const eckoushicState = this.cascade.compute(
      lambdaState.lambda,
      lambdaState.coherence,
      440, // Base frequency
      this.timeStep
    );
    this.previousLambda = lambdaState.lambda;
    
    // Step 3: Rainbow Bridge (Emotional frequency mapping)
    const rainbowState = this.bridge.map(lambdaState.lambda, lambdaState.coherence);
    
    // Step 4: Prism (5-level transformation → 528 Hz LOVE)
    const prismOutput = this.prism.transform(
      lambdaState.lambda,
      lambdaState.coherence,
      rainbowState.frequency
    );
    
    // Step 5: Compute coherence components from field metrics
    const coherenceMetrics = this.computeCoherenceMetrics(t, lambdaState.coherence);
    
    // Step 6: Unity Event Detection
    const unityMetrics = this.detectUnityEvent(
      lambdaState.coherence,
      lambdaState.substrate,
      lambdaState.observer,
      t
    );
    
    return {
      t,
      lambda: lambdaState,
      eckoushic: eckoushicState,
      rainbow: rainbowState,
      prism: prismOutput,
      coherence: lambdaState.coherence,
      ...coherenceMetrics,
      ...unityMetrics,
    };
  }
  
  /**
   * Compute detailed coherence metrics (C_lin, C_nonlin, C_phi, G_eff, Q_abs)
   */
  private computeCoherenceMetrics(t: number, baseCoherence: number) {
    // C_lin: Linear coherence component (stable = 1.0)
    const coherenceLinear = 1.0;
    
    // C_nonlin: Nonlinear observer contribution
    const coherenceNonlinear = 0.932 + (1 - 0.932) * Math.tanh((t - 1.0) * 2);
    
    // C_phi: Golden ratio phase coupling (φ = 1.618...)
    const phi = (1 + Math.sqrt(5)) / 2;
    const coherencePhi = 0.0277 + 0.001 * Math.cos(2 * Math.PI * t / phi);
    
    // G_eff: Effective gain (peaks at t≈1.04)
    const tNorm = (t - 1.04) / 0.5;
    const effectiveGain = Math.exp(-tNorm * tNorm) * (0.2 + 0.8 * baseCoherence);
    
    // Q_abs: Quality factor (resonance strength, peaks at t≈2.51)
    const tResonance = (t - 2.51) / 0.8;
    const qualityFactor = 0.643 * Math.exp(-tResonance * tResonance) * baseCoherence;
    
    return {
      coherenceLinear,
      coherenceNonlinear,
      coherencePhi,
      effectiveGain,
      qualityFactor,
    };
  }
  
  /**
   * Detect Unity Event (Ego Death / Cycle Switch)
   * Occurs when coherence → 1.0 and phase spread → 0
   */
  private detectUnityEvent(
    coherence: number,
    substrate: number,
    observer: number,
    t: number
  ) {
    // Phase spread: measure of separation between components
    // When substrate and observer align perfectly → phase spread = 0
    const alignment = Math.abs(substrate - observer) / (Math.abs(substrate) + Math.abs(observer) + 1e-10);
    const phaseSpread = Math.max(0, Math.min(1, alignment));
    
    // Unity probability increases as coherence approaches 1.0 and phase spread approaches 0
    const unityProbability = coherence > 0.95 
      ? Math.pow(coherence, 4) * (1 - phaseSpread) 
      : 0;
    
    // Unity event triggered at critical threshold
    // Typically occurs at t≈22 in simulation (Cycle Switch)
    const isUnityEvent = coherence > 0.998 && phaseSpread < 0.05;
    
    return {
      unityProbability,
      phaseSpread,
      isUnityEvent,
    };
  }
  
  /**
   * Reset all systems
   */
  reset(): void {
    this.masterEq = new MasterEquation();
    this.cascade.reset();
    this.previousLambda = 0;
  }
  
  /**
   * Get system status summary
   */
  getSystemStatus(state: UnifiedHarmonicState): string {
    if (state.isUnityEvent) {
      return '🌟 UNITY EVENT — Cycle Switch at t≈22';
    }
    
    if (state.unityProbability > 0.8) {
      return '⚡ APPROACHING UNITY — Coherence converging';
    }
    
    if (state.prism.state === 'MANIFEST' && state.prism.frequency === 528) {
      return '💚 LOVE LOCKED — 528 Hz manifest';
    }
    
    if (state.eckoushic.cascadeLevel === 4) {
      return '💗 HEART WAVE ACTIVE — Cascade complete';
    }
    
    if (state.rainbow.phase === 'UNITY') {
      return '🔮 UNITY PHASE — 963 Hz resonance';
    }
    
    return `${state.rainbow.phase} — ${state.prism.state}`;
  }
}
