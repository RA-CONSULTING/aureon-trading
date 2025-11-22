// QGITA Signal Generator
// Combines FTCP detection, Lighthouse consensus, and coherence metrics
// to generate high-confidence trading signals

import { FTCPDetector, CurvaturePoint } from './ftcpDetector';
import { LighthouseConsensus, LighthouseState } from './lighthouseConsensus';
import { QGITACoherenceEngine, calculateAnomalyPointer, CoherenceMetrics } from './qgitaCoherence';
import { FibonacciLattice } from './fibonacciLattice';

export type QGITASignal = {
  timestamp: number;
  signalType: 'BUY' | 'SELL' | 'HOLD';
  confidence: number; // 0-100%
  tier: 1 | 2 | 3; // Tier 1: 80-100%, Tier 2: 60-79%, Tier 3: <60%
  curvature: number;
  curvatureDirection: 'UPWARD' | 'DOWNWARD' | 'NEUTRAL';
  lighthouse: LighthouseState;
  coherence: CoherenceMetrics;
  ftcpDetected: boolean;
  goldenRatioScore: number;
  anomalyPointer: number;
  reasoning: string;
};

export class QGITASignalGenerator {
  private ftcpDetector: FTCPDetector;
  private lighthouse: LighthouseConsensus;
  private coherenceEngine: QGITACoherenceEngine;
  private fibLattice: FibonacciLattice;
  
  private priceHistory: number[] = [];
  private volumeHistory: number[] = [];
  private timestampHistory: number[] = [];
  
  private readonly minConfidenceThreshold = 60;
  
  constructor() {
    this.ftcpDetector = new FTCPDetector();
    this.lighthouse = new LighthouseConsensus();
    this.coherenceEngine = new QGITACoherenceEngine();
    this.fibLattice = new FibonacciLattice();
  }
  
  /**
   * Process new market data and generate trading signal
   */
  generateSignal(
    timestamp: number,
    price: number,
    volume: number,
    lambda: number,
    coherenceValue: number,
    substrate: number,
    observer: number,
    echo: number
  ): QGITASignal {
    // Update history
    this.priceHistory.push(price);
    this.volumeHistory.push(volume);
    this.timestampHistory.push(timestamp);
    
    // Keep only recent history
    const maxHistory = 200;
    if (this.priceHistory.length > maxHistory) {
      this.priceHistory.shift();
      this.volumeHistory.shift();
      this.timestampHistory.shift();
    }
    
    // Stage 1: FTCP Detection
    const ftcpResult = this.ftcpDetector.addPoint(timestamp, price);
    const ftcpDetected = ftcpResult?.isFTCP || false;
    const goldenRatioScore = ftcpResult?.goldenRatioScore || 0;
    const curvature = ftcpResult?.curvature || 0;
    
    // Determine curvature direction
    const curvatureDirection = this.determineCurvatureDirection(curvature);
    
    // Calculate Geff (effective gravity signal)
    const Geff = this.ftcpDetector.computeGeff();
    const normalizedGeff = Math.min(1.0, Geff / 10); // Normalize to 0-1
    
    // Stage 2: Coherence Metrics
    const coherence = this.coherenceEngine.calculateAllMetrics(this.priceHistory);
    
    // Calculate Anomaly Pointer
    const anomalyPointer = calculateAnomalyPointer(
      this.priceHistory,
      this.volumeHistory
    );
    const normalizedQ = Math.min(1.0, anomalyPointer);
    
    // Stage 3: Lighthouse Validation
    const lighthouseState = this.lighthouse.validate(
      lambda,
      coherenceValue,
      substrate,
      observer,
      echo,
      normalizedGeff,
      ftcpDetected
    );
    
    // Stage 4: Signal Generation
    const signal = this.interpretSignal(
      timestamp,
      curvature,
      curvatureDirection,
      lighthouseState,
      coherence,
      ftcpDetected,
      goldenRatioScore,
      normalizedQ
    );
    
    return signal;
  }
  
  /**
   * Interpret all metrics to generate final signal
   */
  private interpretSignal(
    timestamp: number,
    curvature: number,
    curvatureDirection: 'UPWARD' | 'DOWNWARD' | 'NEUTRAL',
    lighthouse: LighthouseState,
    coherence: CoherenceMetrics,
    ftcpDetected: boolean,
    goldenRatioScore: number,
    anomalyPointer: number
  ): QGITASignal {
    let signalType: 'BUY' | 'SELL' | 'HOLD' = 'HOLD';
    let reasoning = '';
    
    // BUY Signal Conditions:
    // - FTCP detected with positive curvature (upward bend)
    // - Lighthouse Event confirmed (L > threshold)
    // - Confidence > 60%
    // - Cross-scale coherence increasing (self-similar uptrend)
    
    if (lighthouse.isLHE && ftcpDetected) {
      if (curvatureDirection === 'UPWARD' && coherence.crossScaleCoherence > 0.6) {
        signalType = 'BUY';
        reasoning = `🟢 BUY: FTCP detected with upward curvature (${curvature.toFixed(4)}). ` +
                   `Lighthouse Event confirmed (L=${lighthouse.L.toFixed(3)}). ` +
                   `Cross-scale coherence strong (${(coherence.crossScaleCoherence * 100).toFixed(1)}%). ` +
                   `Golden ratio timing: ${(goldenRatioScore * 100).toFixed(1)}%.`;
      } 
      // SELL Signal Conditions:
      // - FTCP detected with negative curvature (downward bend)
      // - Lighthouse Event confirmed
      // - Confidence > 60%
      // - Linear coherence breaking down (trend exhaustion)
      else if (curvatureDirection === 'DOWNWARD' && coherence.linearCoherence < 0.5) {
        signalType = 'SELL';
        reasoning = `🔴 SELL: FTCP detected with downward curvature (${curvature.toFixed(4)}). ` +
                   `Lighthouse Event confirmed (L=${lighthouse.L.toFixed(3)}). ` +
                   `Linear coherence breakdown (${(coherence.linearCoherence * 100).toFixed(1)}%). ` +
                   `Trend exhaustion detected.`;
      } else {
        signalType = 'HOLD';
        reasoning = `⚪ HOLD: Lighthouse Event detected but conditions unclear. ` +
                   `Curvature: ${curvatureDirection}, ` +
                   `Linear coherence: ${(coherence.linearCoherence * 100).toFixed(1)}%, ` +
                   `Cross-scale: ${(coherence.crossScaleCoherence * 100).toFixed(1)}%.`;
      }
    } else {
      signalType = 'HOLD';
      reasoning = `⚪ HOLD: No Lighthouse Event. ` +
                 `FTCP: ${ftcpDetected ? 'Yes' : 'No'}, ` +
                 `L: ${lighthouse.L.toFixed(3)}, ` +
                 `Threshold: ${lighthouse.threshold.toFixed(3)}.`;
    }
    
    // Calculate overall confidence
    const confidence = this.calculateConfidence(
      lighthouse,
      coherence,
      goldenRatioScore,
      ftcpDetected
    );
    
    // Determine signal tier
    const tier = this.determineSignalTier(confidence);
    
    return {
      timestamp,
      signalType,
      confidence,
      tier,
      curvature,
      curvatureDirection,
      lighthouse,
      coherence,
      ftcpDetected,
      goldenRatioScore,
      anomalyPointer,
      reasoning,
    };
  }
  
  /**
   * Calculate overall confidence score (0-100%)
   */
  private calculateConfidence(
    lighthouse: LighthouseState,
    coherence: CoherenceMetrics,
    goldenRatioScore: number,
    ftcpDetected: boolean
  ): number {
    let confidence = 0;
    
    // Lighthouse contribution (40%)
    confidence += lighthouse.confidence * 0.4;
    
    // Coherence metrics contribution (30%)
    const avgCoherence = (
      coherence.linearCoherence +
      coherence.nonlinearCoherence +
      coherence.crossScaleCoherence
    ) / 3;
    confidence += avgCoherence * 100 * 0.3;
    
    // Golden ratio timing (20%)
    confidence += goldenRatioScore * 100 * 0.2;
    
    // FTCP detection bonus (10%)
    if (ftcpDetected) {
      confidence += 10;
    }
    
    return Math.min(100, Math.max(0, confidence));
  }
  
  /**
   * Determine signal tier based on confidence
   */
  private determineSignalTier(confidence: number): 1 | 2 | 3 {
    if (confidence >= 80) return 1; // Full position
    if (confidence >= 60) return 2; // Half position
    return 3; // No trade
  }
  
  /**
   * Determine direction of curvature
   */
  private determineCurvatureDirection(curvature: number): 'UPWARD' | 'DOWNWARD' | 'NEUTRAL' {
    if (Math.abs(curvature) < 0.01) return 'NEUTRAL';
    
    // Check recent price trend to determine if curvature is upward or downward
    if (this.priceHistory.length < 3) return 'NEUTRAL';
    
    const recent = this.priceHistory.slice(-3);
    const trend = recent[2] - recent[0];
    
    if (trend > 0 && curvature > 0) return 'UPWARD';
    if (trend < 0 && curvature > 0) return 'DOWNWARD';
    if (trend > 0 && curvature < 0) return 'DOWNWARD';
    if (trend < 0 && curvature < 0) return 'UPWARD';
    
    return 'NEUTRAL';
  }
  
  /**
   * Get recommended position size based on signal tier
   */
  getPositionSizeMultiplier(tier: 1 | 2 | 3): number {
    switch (tier) {
      case 1: return 1.0;   // Full position (100%)
      case 2: return 0.5;   // Half position (50%)
      case 3: return 0.0;   // No trade (0%)
    }
  }
  
  /**
   * Reset all detection engines
   */
  reset() {
    this.ftcpDetector.reset();
    this.lighthouse.reset();
    this.priceHistory = [];
    this.volumeHistory = [];
    this.timestampHistory = [];
  }
}

// Singleton instance
export const qgitaSignalGenerator = new QGITASignalGenerator();
