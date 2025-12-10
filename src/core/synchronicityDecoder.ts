/**
 * 🔮 SYNCHRONICITY DECODER - Pattern Detection & Fibonacci Sync
 * 
 * Detects meaningful coincidences and patterns in market data
 * using Fibonacci sequences and sacred geometry principles.
 */

import { unifiedBus, BusState } from './unifiedBus';
import { temporalLadder } from './temporalLadder';

// Fibonacci sequence for timing
const FIBONACCI = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610];

// Golden ratio and derived constants
const PHI = (1 + Math.sqrt(5)) / 2;
const PHI_INVERSE = 1 / PHI;

export interface SyncPattern {
  type: 'FIBONACCI' | 'GOLDEN_RATIO' | 'HARMONIC' | 'FRACTAL' | 'TEMPORAL';
  strength: number;
  description: string;
  timestamp: number;
  priceLevel?: number;
  timeOffset?: number;
}

export interface SyncState {
  patterns: SyncPattern[];
  overallSync: number;
  dominantPattern: string;
  fibonacciAlignment: number;
  goldenRatioPresence: number;
  temporalHarmony: number;
}

export function detectFibonacciSync(prices: number[], tolerance = 0.02): SyncPattern[] {
  const patterns: SyncPattern[] = [];
  
  if (prices.length < 5) return patterns;
  
  const high = Math.max(...prices);
  const low = Math.min(...prices);
  const range = high - low;
  
  if (range === 0) return patterns;
  
  // Fibonacci retracement levels
  const fibLevels = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0];
  const currentPrice = prices[prices.length - 1];
  const normalizedPrice = (currentPrice - low) / range;
  
  for (const level of fibLevels) {
    if (Math.abs(normalizedPrice - level) < tolerance) {
      patterns.push({
        type: 'FIBONACCI',
        strength: 1 - Math.abs(normalizedPrice - level) / tolerance,
        description: `Price at ${(level * 100).toFixed(1)}% Fibonacci level`,
        timestamp: Date.now(),
        priceLevel: low + range * level
      });
    }
  }
  
  // Check for Fibonacci time intervals
  for (let i = 0; i < FIBONACCI.length && FIBONACCI[i] < prices.length; i++) {
    const fibIndex = prices.length - 1 - FIBONACCI[i];
    if (fibIndex >= 0) {
      const fibPrice = prices[fibIndex];
      const priceDiff = Math.abs(currentPrice - fibPrice) / currentPrice;
      
      if (priceDiff < tolerance * 2) {
        patterns.push({
          type: 'TEMPORAL',
          strength: 1 - priceDiff / (tolerance * 2),
          description: `Price echoing ${FIBONACCI[i]} periods ago`,
          timestamp: Date.now(),
          timeOffset: FIBONACCI[i]
        });
      }
    }
  }
  
  return patterns;
}

export function detectGoldenRatio(value1: number, value2: number, tolerance = 0.02): boolean {
  if (value2 === 0) return false;
  const ratio = value1 / value2;
  return Math.abs(ratio - PHI) < tolerance || Math.abs(ratio - PHI_INVERSE) < tolerance;
}

export class SynchronicityDecoder {
  private patterns: SyncPattern[] = [];
  private priceHistory: number[] = [];
  private volumeHistory: number[] = [];
  private registered = false;
  
  constructor() {}
  
  register(): void {
    if (this.registered) return;
    
    temporalLadder.registerSystem({
      id: 'SYNCHRONICITY_DECODER',
      name: 'Synchronicity Decoder',
      type: 'DETECTION',
      priority: 6,
      heartbeatInterval: 2000,
      onHeartbeat: () => ({
        patterns: this.patterns.length,
        overallSync: this.calculateOverallSync()
      })
    });
    
    this.registered = true;
    console.log('🔮 Synchronicity Decoder registered');
  }
  
  addDataPoint(price: number, volume: number): void {
    this.priceHistory.push(price);
    this.volumeHistory.push(volume);
    
    // Keep last 500 points
    if (this.priceHistory.length > 500) {
      this.priceHistory.shift();
      this.volumeHistory.shift();
    }
  }
  
  decode(): SyncState {
    this.patterns = [];
    
    // Detect Fibonacci patterns in price
    const fibPatterns = detectFibonacciSync(this.priceHistory);
    this.patterns.push(...fibPatterns);
    
    // Detect golden ratio in price/volume relationship
    if (this.priceHistory.length >= 2) {
      const recentPrice = this.priceHistory[this.priceHistory.length - 1];
      const prevPrice = this.priceHistory[this.priceHistory.length - 2];
      
      if (detectGoldenRatio(recentPrice, prevPrice)) {
        this.patterns.push({
          type: 'GOLDEN_RATIO',
          strength: 0.8,
          description: 'Golden ratio detected in price movement',
          timestamp: Date.now()
        });
      }
    }
    
    // Detect harmonic patterns (simplified)
    const harmonicStrength = this.detectHarmonicPatterns();
    if (harmonicStrength > 0.5) {
      this.patterns.push({
        type: 'HARMONIC',
        strength: harmonicStrength,
        description: 'Harmonic wave pattern detected',
        timestamp: Date.now()
      });
    }
    
    // Detect fractal self-similarity
    const fractalStrength = this.detectFractalPatterns();
    if (fractalStrength > 0.5) {
      this.patterns.push({
        type: 'FRACTAL',
        strength: fractalStrength,
        description: 'Fractal self-similarity detected',
        timestamp: Date.now()
      });
    }
    
    const state = this.getState();
    
    // Publish to UnifiedBus
    const busState: BusState = {
      system_name: 'SynchronicityDecoder',
      timestamp: Date.now(),
      ready: true,
      coherence: state.overallSync,
      confidence: state.fibonacciAlignment,
      signal: state.overallSync > 0.6 ? 1 : state.overallSync > 0.3 ? 0 : -1,
      data: {
        patterns: this.patterns.length,
        dominantPattern: state.dominantPattern,
        goldenRatioPresence: state.goldenRatioPresence
      }
    };
    unifiedBus.publish(busState);
    
    return state;
  }
  
  private detectHarmonicPatterns(): number {
    if (this.priceHistory.length < 20) return 0;
    
    // Simple harmonic detection using autocorrelation
    const recent = this.priceHistory.slice(-20);
    const mean = recent.reduce((a, b) => a + b, 0) / recent.length;
    const normalized = recent.map(p => p - mean);
    
    let maxCorr = 0;
    for (let lag = 3; lag < 10; lag++) {
      let corr = 0;
      for (let i = 0; i < normalized.length - lag; i++) {
        corr += normalized[i] * normalized[i + lag];
      }
      corr /= normalized.length - lag;
      maxCorr = Math.max(maxCorr, Math.abs(corr));
    }
    
    const variance = normalized.reduce((a, b) => a + b * b, 0) / normalized.length;
    return variance > 0 ? Math.min(1, maxCorr / variance) : 0;
  }
  
  private detectFractalPatterns(): number {
    if (this.priceHistory.length < 50) return 0;
    
    // Compare short-term and long-term patterns
    const short = this.priceHistory.slice(-10);
    const long = this.priceHistory.slice(-50, -40);
    
    if (long.length < 10) return 0;
    
    // Normalize both
    const normalizeArray = (arr: number[]) => {
      const min = Math.min(...arr);
      const max = Math.max(...arr);
      const range = max - min || 1;
      return arr.map(v => (v - min) / range);
    };
    
    const shortNorm = normalizeArray(short);
    const longNorm = normalizeArray(long);
    
    // Calculate similarity
    let similarity = 0;
    for (let i = 0; i < 10; i++) {
      similarity += 1 - Math.abs(shortNorm[i] - longNorm[i]);
    }
    
    return similarity / 10;
  }
  
  private calculateOverallSync(): number {
    if (this.patterns.length === 0) return 0;
    return this.patterns.reduce((sum, p) => sum + p.strength, 0) / this.patterns.length;
  }
  
  getState(): SyncState {
    const overallSync = this.calculateOverallSync();
    
    const fibPatterns = this.patterns.filter(p => p.type === 'FIBONACCI');
    const goldenPatterns = this.patterns.filter(p => p.type === 'GOLDEN_RATIO');
    const temporalPatterns = this.patterns.filter(p => p.type === 'TEMPORAL');
    
    const dominantType = this.patterns.length > 0
      ? this.patterns.reduce((a, b) => a.strength > b.strength ? a : b).type
      : 'NONE';
    
    return {
      patterns: this.patterns,
      overallSync,
      dominantPattern: dominantType,
      fibonacciAlignment: fibPatterns.length > 0
        ? fibPatterns.reduce((sum, p) => sum + p.strength, 0) / fibPatterns.length
        : 0,
      goldenRatioPresence: goldenPatterns.length > 0 ? 1 : 0,
      temporalHarmony: temporalPatterns.length > 0
        ? temporalPatterns.reduce((sum, p) => sum + p.strength, 0) / temporalPatterns.length
        : 0
    };
  }
  
  getSyncBoost(): number {
    const state = this.getState();
    // Boost based on pattern detection
    return 1.0 + (state.overallSync * 0.3);
  }
}

export const synchronicityDecoder = new SynchronicityDecoder();
