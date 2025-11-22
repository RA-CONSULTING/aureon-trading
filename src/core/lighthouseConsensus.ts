// Lighthouse Consensus Model
// Integrates five metrics to compute L(t) via normalized geometric mean
// Lighthouse Event (LHE) confirmed when L(t) > μ + 2σ

export type LighthouseMetrics = {
  Clin: number;      // Linear coherence (QGITA: MACD-based)
  Cnonlin: number;   // Nonlinear coherence (QGITA: Volatility-adjusted)
  Cphi: number;      // Cross-scale coherence (QGITA: Self-similarity at φ)
  Geff: number;      // Effective gravity (from FTCP)
  Q: number;         // Anomaly pointer (sudden change detector)
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
  private readonly weights = [1, 1, 1, 1, 1]; // Equal weights by default
  
  validate(
    lambda: number,
    coherence: number,
    substrate: number,
    observer: number,
    echo: number,
    Geff: number,
    ftcpDetected: boolean
  ): LighthouseState {
    // Compute five consensus metrics
    
    // 1. Clin: Linear coherence (direct from Γ)
    const Clin = coherence;
    
    // 2. Cnonlin: Nonlinear coherence (substrate variance)
    const Cnonlin = this.computeNonlinearCoherence(substrate, observer, echo);
    
    // 3. Cφ: Phase coherence (lambda stability)
    const Cphi = this.computePhaseCoherence(lambda);
    
    // 4. Geff: Effective gravity (from FTCP detector)
    // Already provided as parameter
    
    // 5. |Q|: Quality factor (sharpness of coherence peak)
    const Q = this.computeQualityFactor(coherence, Geff);
    
    const metrics: LighthouseMetrics = {
      Clin,
      Cnonlin,
      Cphi,
      Geff,
      Q,
    };
    
    // Compute L(t) via weighted geometric mean
    // L(t) = (Clin^w1 * Cnonlin^w2 * Cφ^w3 * Geff^w4 * |Q|^w5)^(1/Σw_i)
    let product = 1.0;
    const metricsArray = [Clin, Cnonlin, Cphi, Geff, Math.abs(Q)];
    
    for (let i = 0; i < metricsArray.length; i++) {
      if (metricsArray[i] > 0) {
        product *= Math.pow(metricsArray[i], this.weights[i]);
      } else {
        product = 0; // Any zero kills the consensus
        break;
      }
    }
    
    const totalWeight = this.weights.reduce((sum, w) => sum + w, 0);
    const L = product > 0 ? Math.pow(product, 1.0 / totalWeight) : 0;
    
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
    
    return {
      L,
      metrics,
      isLHE,
      threshold,
      confidence,
    };
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
  
  private computeQualityFactor(coherence: number, Geff: number): number {
    // Q factor measures sharpness of coherence peak
    // High when coherence is high and gravity signal is focused
    if (Geff === 0) return 0;
    
    return coherence / (1 + Geff);
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
