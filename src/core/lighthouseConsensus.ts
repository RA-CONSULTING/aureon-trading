// Lighthouse Consensus Model
// Integrates five metrics to compute L(t) via normalized geometric mean
// Lighthouse Event (LHE) confirmed when L(t) > μ + 2σ

import { unifiedBus, SignalType } from './unifiedBus';

export type LighthouseMetrics = {
  Q: number;         // |Q| — Anomaly pointer (0-1), FLAME metric
  Geff: number;      // G_eff — Effective gravity (0-1), BRAKE metric
  Clin: number;      // C_lin — Linear coherence (MACD-based)
  Cnonlin: number;   // C_nonlin — Nonlinear coherence (volatility-adjusted)
};

export type LighthouseState = {
  L: number;               // Lighthouse signal
  metrics: LighthouseMetrics;
  isLHE: boolean;         // Is this a Lighthouse Event?
  threshold: number;      // Current threshold (μ + 2σ)
  confidence: number;     // Confidence score 0-1
};

export class LighthouseConsensus {
  private history: number[] = [];
  private readonly maxHistory = 100;
  // Ablation study weights: C_nonlin and G_eff strongest drivers, |Q| suppressor
  private readonly weights = {
    Cnonlin: 1.2,  // Strongest driver
    Geff: 1.2,     // Strongest driver
    Clin: 1.0,     // Baseline
    Q: 0.8,        // Suppressor for spurious triggers
  };
  
  validate(
    lambda: number,
    coherence: number,
    substrate: number,
    observer: number,
    echo: number,
    Geff: number,
    ftcpDetected: boolean,
    volumeSpike: number = 0,
    spreadExpansion: number = 0,
    priceAcceleration: number = 0
  ): LighthouseState {
    // Compute four consensus metrics (ablation study alignment)
    
    // 1. C_lin: Linear coherence (direct from Γ)
    const Clin = coherence;
    
    // 2. C_nonlin: Nonlinear coherence (substrate variance)
    const Cnonlin = this.computeNonlinearCoherence(substrate, observer, echo);
    
    // 3. G_eff: Effective gravity (from FTCP detector)
    // Already provided as parameter (0-1 normalized)
    
    // 4. |Q|: Anomaly pointer (flame metric)
    const Q = this.computeAnomalyPointer(volumeSpike, spreadExpansion, priceAcceleration);
    
    const metrics: LighthouseMetrics = {
      Q,
      Geff,
      Clin,
      Cnonlin,
    };
    
    // Compute L(t) via weighted geometric mean (ablation study formula)
    // L(t) = (C_lin^w1 × C_nonlin^w2 × G_eff^w3 × |Q|^w4)^(1/Σw_i)
    // Use minimum floor values to prevent zero (geometric mean requires all > 0)
    const metricsWithWeights = [
      { value: Math.max(Clin, 0.1), weight: this.weights.Clin },
      { value: Math.max(Cnonlin, 0.1), weight: this.weights.Cnonlin },
      { value: Math.max(Geff, 0.1), weight: this.weights.Geff },
      { value: Math.max(Math.abs(Q), 0.1), weight: this.weights.Q },
    ];
    
    let product = 1.0;
    
    for (const { value, weight } of metricsWithWeights) {
      product *= Math.pow(value, weight);
    }
    
    const totalWeight = Object.values(this.weights).reduce((sum, w) => sum + w, 0);
    const L = Math.pow(product, 1.0 / totalWeight);
    
    // Track history
    this.history.push(L);
    if (this.history.length > this.maxHistory) {
      this.history.shift();
    }
    
    // Compute threshold: μ + 2σ
    const threshold = this.computeThreshold();
    
    // Lighthouse Event (LHE) detected if:
    // 1. L(t) > μ + 2σ
    // 2. FTCP detected nearby
    const isLHE = L > threshold && ftcpDetected;
    
    // Confidence based on how far above threshold
    const confidence = threshold > 0 ? Math.min((L - threshold) / threshold, 1) : 0;
    
    const state: LighthouseState = {
      L,
      metrics,
      isLHE,
      threshold,
      confidence,
    };
    
    // Publish to UnifiedBus
    this.publishToBus(state, coherence);
    
    return state;
  }
  
  /**
   * Publish Lighthouse state to UnifiedBus
   */
  private publishToBus(state: LighthouseState, coherence: number): void {
    let signal: SignalType = 'NEUTRAL';
    if (state.isLHE) {
      signal = state.L > 0.5 ? 'BUY' : 'SELL';
    }
    
    unifiedBus.publish({
      systemName: 'Lighthouse',
      timestamp: Date.now(),
      ready: true,
      coherence,
      confidence: state.confidence,
      signal,
      data: {
        L: state.L,
        isLHE: state.isLHE,
        threshold: state.threshold,
        metrics: state.metrics,
      },
    });
  }
  
  private computeNonlinearCoherence(
    substrate: number,
    observer: number,
    echo: number
  ): number {
    // Measure alignment of substrate with observer and echo
    // High when all three components are balanced
    const total = Math.abs(substrate) + Math.abs(observer) + Math.abs(echo);
    if (total === 0) return 0;
    
    const weights = [
      Math.abs(substrate) / total,
      Math.abs(observer) / total,
      Math.abs(echo) / total,
    ];
    
    // Entropy-based measure: lower entropy = higher coherence
    const entropy = weights.reduce((sum, w) => {
      return sum + (w > 0 ? -w * Math.log(w) : 0);
    }, 0);
    
    // Normalize to 0-1 (max entropy for 3 equal parts is ln(3))
    return 1 - entropy / Math.log(3);
  }
  
  private computePhaseCoherence(lambda: number): number {
    if (this.history.length < 5) return 0.5;
    
    // Measure stability of recent lambda values
    const recentLambdas = this.history.slice(-5);
    const mean = recentLambdas.reduce((sum, val) => sum + val, 0) / recentLambdas.length;
    const variance = recentLambdas.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / recentLambdas.length;
    const stddev = Math.sqrt(variance);
    
    // Lower variance = higher phase coherence
    return Math.max(0, Math.min(1, 1 - stddev));
  }
  
  private computeAnomalyPointer(
    volumeSpike: number,
    spreadExpansion: number,
    priceAcceleration: number
  ): number {
    // |Q| — Anomaly pointer (FLAME metric)
    // Composition: 40% volume spike, 30% spread expansion, 30% price acceleration
    // Range: 0-1 (normalized)
    return 0.4 * volumeSpike + 0.3 * spreadExpansion + 0.3 * priceAcceleration;
  }
  
  private computeThreshold(): number {
    if (this.history.length < 10) {
      return 0.5; // Default threshold
    }
    
    // Compute μ + 2σ
    const mean = this.history.reduce((sum, val) => sum + val, 0) / this.history.length;
    const variance = this.history.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / this.history.length;
    const stddev = Math.sqrt(variance);
    
    return mean + 2 * stddev;
  }
  
  reset() {
    this.history = [];
  }
}
