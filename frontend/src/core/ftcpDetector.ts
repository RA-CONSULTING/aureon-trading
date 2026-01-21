// FTCP Detector: Fibonacci-Tightened Curvature Points
// Identifies candidate anomalies where discrete curvature spikes
// coincide with near-golden-ratio spacing of neighboring timestamps

const PHI = (1 + Math.sqrt(5)) / 2; // Golden ratio ≈ 1.618
const PHI_TOLERANCE = 0.1; // Tolerance for golden ratio matching

export type CurvaturePoint = {
  timestamp: number;
  value: number;
  curvature: number;
  isFTCP: boolean;
  goldenRatioScore: number;
};

export class FTCPDetector {
  private history: Array<{ timestamp: number; value: number }> = [];
  private readonly maxHistory = 200;
  private readonly curvatureThreshold = 0.5;
  private curvatureHistory: number[] = [];
  
  addPoint(timestamp: number, value: number): CurvaturePoint | null {
    this.history.push({ timestamp, value });
    
    if (this.history.length > this.maxHistory) {
      this.history.shift();
    }
    
    // Need at least 3 points to compute curvature
    if (this.history.length < 3) {
      return null;
    }
    
    // Compute discrete curvature at current point
    const n = this.history.length;
    const prev = this.history[n - 2];
    const curr = this.history[n - 1];
    const pprev = this.history[n - 3];
    
    // Second derivative approximation: f''(x) ≈ (f(x+h) - 2f(x) + f(x-h)) / h²
    const curvature = Math.abs(
      (curr.value - 2 * prev.value + pprev.value) / 
      Math.pow((curr.timestamp - prev.timestamp) / 1000, 2)
    );
    
    // Track curvature history for adaptive threshold
    this.curvatureHistory.push(curvature);
    if (this.curvatureHistory.length > this.maxHistory) {
      this.curvatureHistory.shift();
    }
    
    // Adaptive threshold: 90th percentile of historical curvatures
    const adaptiveThreshold = this.computeAdaptiveThreshold(90);
    
    // Check for golden ratio timing
    const goldenRatioScore = this.computeGoldenRatioScore();
    const isFTCP = curvature > adaptiveThreshold && goldenRatioScore > 0.7;
    
    return {
      timestamp: curr.timestamp,
      value: curr.value,
      curvature,
      isFTCP,
      goldenRatioScore,
    };
  }
  
  private computeGoldenRatioScore(): number {
    if (this.history.length < 5) return 0;
    
    // Check temporal spacing for golden ratio patterns
    // Look at ratios of time intervals: dt(i+1) / dt(i)
    const n = this.history.length;
    const intervals: number[] = [];
    
    for (let i = n - 5; i < n - 1; i++) {
      intervals.push(this.history[i + 1].timestamp - this.history[i].timestamp);
    }
    
    // Compute ratios and compare to φ
    let matchCount = 0;
    let totalChecks = 0;
    
    for (let i = 0; i < intervals.length - 1; i++) {
      if (intervals[i] === 0) continue;
      
      const ratio = intervals[i + 1] / intervals[i];
      const phiError = Math.abs(ratio - PHI) / PHI;
      
      if (phiError < PHI_TOLERANCE) {
        matchCount++;
      }
      totalChecks++;
    }
    
    return totalChecks > 0 ? matchCount / totalChecks : 0;
  }
  
  // Compute effective gravity signal Geff(t) from recent curvature
  computeGeff(): number {
    if (this.history.length < 3) return 0;
    
    const recentPoints = this.history.slice(-10);
    let sumCurvature = 0;
    
    for (let i = 2; i < recentPoints.length; i++) {
      const curr = recentPoints[i].value;
      const prev = recentPoints[i - 1].value;
      const pprev = recentPoints[i - 2].value;
      
      const curvature = Math.abs(curr - 2 * prev + pprev);
      sumCurvature += curvature;
    }
    
    return sumCurvature / Math.max(recentPoints.length - 2, 1);
  }
  
  // Compute adaptive curvature threshold based on percentile
  private computeAdaptiveThreshold(percentile: number): number {
    if (this.curvatureHistory.length < 10) {
      return this.curvatureThreshold; // Use default if not enough history
    }
    
    const sorted = [...this.curvatureHistory].sort((a, b) => a - b);
    const index = Math.floor((percentile / 100) * sorted.length);
    return sorted[index];
  }
  
  reset() {
    this.history = [];
    this.curvatureHistory = [];
  }
}
