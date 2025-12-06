/**
 * Temporal Probability Echo System
 * Tracks probability matrix history, temporal position, and echo metrics
 * Remembers where we are in the probability timeline
 */

import { unifiedBus } from './unifiedBus';

export interface ProbabilitySnapshot {
  timestamp: number;
  sixDProbability: number;
  hncProbability: number;
  lighthouseProbability: number;
  fusedProbability: number;
  action: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  prismFrequency: number;
  prismLevel: number;
  coherence: number;
  lambda: number;
}

export interface EchoMetrics {
  trend: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  trendStrength: number;
  momentum: number;
  convergence: number;
  drift: number;
  volatility: number;
  echoCount: number;
  temporalPosition: number;
  isSteeringCorrectly: boolean;
  predictionAccuracy: number; // Historical accuracy of predictions
  temporalAlignment: number; // How well past predictions align with outcomes
}

export interface TemporalEchoState {
  snapshots: ProbabilitySnapshot[];
  metrics: EchoMetrics;
  lastUpdate: number;
  temporalId: string;
}

class TemporalProbabilityEchoClass {
  private snapshots: ProbabilitySnapshot[] = [];
  private maxHistory = 100;
  private listeners: Set<(state: TemporalEchoState) => void> = new Set();
  private temporalId: string;

  constructor() {
    this.temporalId = `temporal-${Date.now()}`;
  }

  recordSnapshot(snapshot: Omit<ProbabilitySnapshot, 'timestamp'>): void {
    const fullSnapshot: ProbabilitySnapshot = {
      ...snapshot,
      timestamp: Date.now()
    };

    this.snapshots.push(fullSnapshot);

    // Keep only last N snapshots
    if (this.snapshots.length > this.maxHistory) {
      this.snapshots = this.snapshots.slice(-this.maxHistory);
    }

    // Publish to UnifiedBus
    const state = this.getState();
    const signalValue: 'BUY' | 'SELL' | 'NEUTRAL' = state.metrics.trend === 'BULLISH' ? 'BUY' : state.metrics.trend === 'BEARISH' ? 'SELL' : 'NEUTRAL';
    unifiedBus.publish({
      systemName: 'TemporalProbabilityEcho',
      timestamp: Date.now(),
      ready: true,
      coherence: state.metrics.convergence,
      confidence: state.metrics.trendStrength,
      signal: signalValue,
      data: state
    });

    this.notifyListeners();
  }

  private computeMetrics(): EchoMetrics {
    if (this.snapshots.length < 2) {
      return {
        trend: 'NEUTRAL',
        trendStrength: 0,
        momentum: 0,
        convergence: 0,
        drift: 0,
        volatility: 0,
        echoCount: this.snapshots.length,
        temporalPosition: 0,
        isSteeringCorrectly: false,
        predictionAccuracy: 0.5,
        temporalAlignment: 0.5
      };
    }

    const recent = this.snapshots.slice(-20);
    const probabilities = recent.map(s => s.fusedProbability);
    
    // Trend calculation
    const firstHalf = probabilities.slice(0, Math.floor(probabilities.length / 2));
    const secondHalf = probabilities.slice(Math.floor(probabilities.length / 2));
    const firstAvg = firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length;
    const secondAvg = secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length;
    const trendDiff = secondAvg - firstAvg;
    
    const trend: 'BULLISH' | 'BEARISH' | 'NEUTRAL' = 
      trendDiff > 0.05 ? 'BULLISH' : 
      trendDiff < -0.05 ? 'BEARISH' : 'NEUTRAL';
    
    const trendStrength = Math.min(1, Math.abs(trendDiff) * 5);

    // Momentum (rate of change)
    const lastProb = probabilities[probabilities.length - 1];
    const prevProb = probabilities[probabilities.length - 2];
    const momentum = lastProb - prevProb;

    // Convergence (are probabilities aligning?)
    const lastSnapshot = recent[recent.length - 1];
    const probSpread = Math.max(
      Math.abs(lastSnapshot.sixDProbability - lastSnapshot.hncProbability),
      Math.abs(lastSnapshot.hncProbability - lastSnapshot.lighthouseProbability),
      Math.abs(lastSnapshot.sixDProbability - lastSnapshot.lighthouseProbability)
    );
    const convergence = 1 - Math.min(1, probSpread);

    // Drift (deviation from expected path)
    const expectedProb = 0.5 + (trendDiff * 2);
    const drift = Math.abs(lastProb - expectedProb);

    // Volatility (standard deviation of probabilities)
    const mean = probabilities.reduce((a, b) => a + b, 0) / probabilities.length;
    const variance = probabilities.reduce((sum, p) => sum + Math.pow(p - mean, 2), 0) / probabilities.length;
    const volatility = Math.sqrt(variance);

    // Temporal position (0-1 normalized position in history)
    const temporalPosition = this.snapshots.length / this.maxHistory;

    // Is steering correctly? (high convergence, low drift, consistent trend)
    const isSteeringCorrectly = convergence > 0.7 && drift < 0.2 && trendStrength > 0.3;

    // Prediction accuracy: how often did the action match the probability movement
    const predictionAccuracy = this.calculatePredictionAccuracy();
    
    // Temporal alignment: how well do past predictions align with current state
    const temporalAlignment = this.calculateTemporalAlignment();

    return {
      trend,
      trendStrength,
      momentum,
      convergence,
      drift,
      volatility,
      echoCount: this.snapshots.length,
      temporalPosition,
      isSteeringCorrectly,
      predictionAccuracy,
      temporalAlignment
    };
  }

  private calculatePredictionAccuracy(): number {
    const recent = this.snapshots.slice(-20);
    if (recent.length < 5) return 0.5;
    
    let correctPredictions = 0;
    let totalPredictions = 0;
    
    for (let i = 0; i < recent.length - 1; i++) {
      const current = recent[i];
      const next = recent[i + 1];
      
      // Compare predicted action with actual probability movement
      const probabilityMoved = next.fusedProbability - current.fusedProbability;
      const predictedUp = current.action === 'BUY';
      const predictedDown = current.action === 'SELL';
      
      if (predictedUp && probabilityMoved > 0) correctPredictions++;
      else if (predictedDown && probabilityMoved < 0) correctPredictions++;
      else if (!predictedUp && !predictedDown && Math.abs(probabilityMoved) < 0.05) correctPredictions++;
      
      totalPredictions++;
    }
    
    return totalPredictions > 0 ? correctPredictions / totalPredictions : 0.5;
  }

  private calculateTemporalAlignment(): number {
    const recent = this.snapshots.slice(-10);
    if (recent.length < 3) return 0.5;
    
    let alignmentScore = 0;
    
    for (let i = 0; i < recent.length - 2; i++) {
      const s1 = recent[i];
      const s2 = recent[i + 1];
      const s3 = recent[i + 2];
      
      // Check if probability trend matches action expectations
      const trend1 = s2.fusedProbability - s1.fusedProbability;
      const trend2 = s3.fusedProbability - s2.fusedProbability;
      
      // Aligned if trends are consistent
      if ((trend1 > 0 && trend2 > 0) || (trend1 < 0 && trend2 < 0)) {
        alignmentScore += 1;
      } else if (Math.abs(trend1) < 0.02 && Math.abs(trend2) < 0.02) {
        alignmentScore += 0.5; // Neutral alignment
      }
    }
    
    return Math.min(1, alignmentScore / (recent.length - 2));
  }

  getState(): TemporalEchoState {
    return {
      snapshots: [...this.snapshots],
      metrics: this.computeMetrics(),
      lastUpdate: this.snapshots.length > 0 ? this.snapshots[this.snapshots.length - 1].timestamp : 0,
      temporalId: this.temporalId
    };
  }

  getRecentSnapshots(count: number = 20): ProbabilitySnapshot[] {
    return this.snapshots.slice(-count);
  }

  getMetrics(): EchoMetrics {
    return this.computeMetrics();
  }

  subscribe(listener: (state: TemporalEchoState) => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private notifyListeners(): void {
    const state = this.getState();
    this.listeners.forEach(listener => listener(state));
  }

  clear(): void {
    this.snapshots = [];
    this.temporalId = `temporal-${Date.now()}`;
    this.notifyListeners();
  }
}

export const temporalProbabilityEcho = new TemporalProbabilityEchoClass();
