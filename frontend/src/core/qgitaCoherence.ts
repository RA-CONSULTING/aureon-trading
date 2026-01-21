// QGITA Coherence Metrics
// Linear, Nonlinear, and Cross-Scale Coherence Calculations

const PHI = (1 + Math.sqrt(5)) / 2; // Golden ratio ≈ 1.618

export type CoherenceMetrics = {
  linearCoherence: number;      // C_lin (0-1): MACD-based trend strength
  nonlinearCoherence: number;   // C_nonlin (0-1): Volatility-adjusted stability
  crossScaleCoherence: number;  // C_φ (0-1): Self-similarity at φ-scaled intervals
};

export class QGITACoherenceEngine {
  /**
   * Calculate linear coherence: MACD-based trend strength.
   * Returns value 0-1 (1 = strong trend, 0 = no trend)
   */
  calculateLinearCoherence(prices: number[], window: number = 20): number {
    if (prices.length < window) return 0.0;

    const recentPrices = prices.slice(-window);
    
    // Calculate EMA
    const emaFast = this.calculateEMA(recentPrices, 12);
    const emaSlow = this.calculateEMA(recentPrices, 26);
    
    const macd = emaFast - emaSlow;
    
    // Normalize to 0-1 range
    const coherence = Math.min(1.0, Math.abs(macd) / (emaSlow * 0.05));
    return coherence;
  }

  /**
   * Calculate nonlinear coherence: Volatility-adjusted consistency.
   * Returns value 0-1 (1 = stable, 0 = chaotic)
   */
  calculateNonlinearCoherence(prices: number[], window: number = 20): number {
    if (prices.length < window) return 0.0;

    const recent = prices.slice(-window);
    const mean = recent.reduce((sum, p) => sum + p, 0) / recent.length;
    const variance = recent.reduce((sum, p) => sum + Math.pow(p - mean, 2), 0) / recent.length;
    const stdDev = Math.sqrt(variance);
    
    const volatility = stdDev / mean;
    
    // Inverse relationship: low volatility = high coherence
    const coherence = 1.0 / (1.0 + volatility);
    return coherence;
  }

  /**
   * Calculate cross-scale coherence: Self-similarity at φ-scaled intervals.
   * Correlation between signal and φ-scaled version of itself.
   */
  calculateCrossScaleCoherence(prices: number[], scaleFactor: number = PHI): number {
    if (prices.length < 20) return 0.0;

    // Create φ-scaled indices
    const scaledIndices: number[] = [];
    for (let i = 0; i < prices.length; i++) {
      const scaledIndex = Math.floor(i * scaleFactor);
      if (scaledIndex < prices.length) {
        scaledIndices.push(scaledIndex);
      }
    }

    if (scaledIndices.length < 10) return 0.0;

    const original = prices.slice(0, scaledIndices.length);
    const scaled = scaledIndices.map(i => prices[i]);

    // Calculate correlation coefficient
    if (original.length !== scaled.length || original.length === 0) return 0.0;

    const correlation = this.calculateCorrelation(original, scaled);
    return Math.abs(correlation);
  }

  /**
   * Calculate all coherence metrics at once
   */
  calculateAllMetrics(prices: number[]): CoherenceMetrics {
    return {
      linearCoherence: this.calculateLinearCoherence(prices),
      nonlinearCoherence: this.calculateNonlinearCoherence(prices),
      crossScaleCoherence: this.calculateCrossScaleCoherence(prices),
    };
  }

  // Helper: Calculate Exponential Moving Average
  private calculateEMA(prices: number[], period: number): number {
    if (prices.length === 0) return 0;
    
    const multiplier = 2 / (period + 1);
    let ema = prices[0];
    
    for (let i = 1; i < prices.length; i++) {
      ema = (prices[i] - ema) * multiplier + ema;
    }
    
    return ema;
  }

  // Helper: Calculate correlation coefficient
  private calculateCorrelation(x: number[], y: number[]): number {
    const n = x.length;
    if (n === 0 || n !== y.length) return 0;

    const meanX = x.reduce((sum, val) => sum + val, 0) / n;
    const meanY = y.reduce((sum, val) => sum + val, 0) / n;

    let numerator = 0;
    let sumXSq = 0;
    let sumYSq = 0;

    for (let i = 0; i < n; i++) {
      const dx = x[i] - meanX;
      const dy = y[i] - meanY;
      numerator += dx * dy;
      sumXSq += dx * dx;
      sumYSq += dy * dy;
    }

    const denominator = Math.sqrt(sumXSq * sumYSq);
    
    if (denominator === 0) return 0;
    
    return numerator / denominator;
  }
}

/**
 * Calculate Anomaly Pointer (Q): Sudden change detector.
 * Combines price spike and volume spike detection.
 */
export function calculateAnomalyPointer(
  prices: number[],
  volumes: number[],
  window: number = 10
): number {
  if (prices.length < window || volumes.length < window) return 0.0;

  // Price change rate
  const priceChange = Math.abs(prices[prices.length - 1] - prices[prices.length - 2]) / 
                      prices[prices.length - 2];

  // Volume spike
  const recentVolumes = volumes.slice(-window, -1);
  const avgVolume = recentVolumes.reduce((sum, v) => sum + v, 0) / recentVolumes.length;
  const volumeSpike = avgVolume > 0 ? volumes[volumes.length - 1] / avgVolume : 1.0;

  // Combined anomaly score
  const qSignal = priceChange * volumeSpike;

  return qSignal;
}
