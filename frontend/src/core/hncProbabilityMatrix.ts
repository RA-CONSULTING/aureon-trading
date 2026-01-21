/**
 * HNC Probability Matrix - Temporal Frequency Analysis
 * Ported from hnc_probability_matrix.py
 * 
 * 2-HOUR PROBABILITY WINDOW:
 * ├─ HOUR -1 (LOOKBACK):  Base signal source - historical frequency patterns
 * ├─ HOUR  0 (NOW):       Current state calibration point
 * ├─ HOUR +1 (FORECAST):  High probability trading window (PRIMARY)
 * └─ HOUR +2 (FINE-TUNE): Secondary window to refine Hour +1 predictions
 */

import { unifiedBus, type SignalType } from './unifiedBus';
import { temporalLadder, type SystemName } from './temporalLadder';

// Constants from Python
const PHI = (1 + Math.sqrt(5)) / 2; // Golden Ratio 1.618
const PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71];
const FIBONACCI = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987];

// Solfeggio Frequencies
export const FREQ_MAP: Record<string, number> = {
  SCHUMANN: 7.83,
  FOUNDATION: 174.0,
  ROOT: 256.0,        // C4 Scientific Pitch (ANCHOR)
  LIBERATION: 396.0,
  TRANSFORMATION: 417.0,
  NATURAL_A: 432.0,
  DISTORTION: 440.0,  // Standard A (artificial)
  VISION: 512.0,
  LOVE: 528.0,        // DNA repair / Miracles
  CONNECTION: 639.0,
  AWAKENING: 741.0,
  INTUITION: 852.0,
  UNITY: 963.0,
};

// Probability thresholds
export const PROB_THRESHOLDS = {
  EXTREME_HIGH: 0.90,
  HIGH: 0.75,
  MODERATE: 0.55,
  NEUTRAL: 0.45,
  LOW: 0.25,
  EXTREME_LOW: 0.10,
} as const;

export type ProbabilityState = 
  | 'EXTREME_BULLISH'
  | 'BULLISH'
  | 'SLIGHT_BULLISH'
  | 'NEUTRAL'
  | 'SLIGHT_BEARISH'
  | 'BEARISH'
  | 'EXTREME_BEARISH';

export interface FrequencySnapshot {
  timestamp: number;
  symbol: string;
  price: number;
  frequency: number;
  resonance: number;
  isHarmonic: boolean;
  momentum: number;
  volume: number;
  coherence: number;
  phaseAngle: number; // 0-360 degrees
}

export interface HourlyProbabilityWindow {
  hourOffset: number; // -1, 0, +1, +2
  startTime: number;
  endTime: number;
  
  // Probability metrics
  bullishProbability: number;
  bearishProbability: number;
  confidence: number;
  
  // Frequency metrics
  avgFrequency: number;
  dominantFrequency: number;
  frequencyTrend: 'RISING' | 'FALLING' | 'STABLE';
  harmonicRatio: number;
  
  // Pattern metrics
  primeAlignment: number;
  fibonacciAlignment: number;
  goldenRatioProximity: number;
  
  // Signal strength
  signalStrength: number;
  noiseRatio: number;
  clarity: number;
  
  // State
  state: ProbabilityState;
}

export interface ProbabilityMatrix {
  symbol: string;
  generatedAt: number;
  
  // The 4 hourly windows
  hourMinus1: HourlyProbabilityWindow | null; // LOOKBACK (base signal)
  hour0: HourlyProbabilityWindow | null;       // NOW (calibration)
  hourPlus1: HourlyProbabilityWindow | null;   // FORECAST (primary)
  hourPlus2: HourlyProbabilityWindow | null;   // FINE-TUNE (secondary)
  
  // Combined metrics
  combinedProbability: number;
  fineTunedProbability: number;
  confidenceScore: number;
  recommendedAction: 'BUY' | 'SELL' | 'HOLD';
  positionModifier: number;
  
  // Fine-tuning results
  fineTuneAdjustment: number;
  fineTuneReason: string;
}

export interface TradingSignal {
  probability: number;
  confidence: number;
  action: 'BUY' | 'SELL' | 'HOLD';
  modifier: number;
  h1State: ProbabilityState;
  fineTune: number;
}

/**
 * Compute probability state from net probability
 */
function computeState(bullishProb: number): ProbabilityState {
  const netProb = bullishProb - (1 - bullishProb);
  
  if (netProb > 0.4) return 'EXTREME_BULLISH';
  if (netProb > 0.25) return 'BULLISH';
  if (netProb > 0.10) return 'SLIGHT_BULLISH';
  if (netProb > -0.10) return 'NEUTRAL';
  if (netProb > -0.25) return 'SLIGHT_BEARISH';
  if (netProb > -0.40) return 'BEARISH';
  return 'EXTREME_BEARISH';
}

/**
 * Find dominant frequency in array
 */
function findDominantFrequency(frequencies: number[]): number {
  if (frequencies.length === 0) return FREQ_MAP.ROOT;
  
  // Simple mode detection: find most common rounded frequency
  const counts: Record<number, number> = {};
  for (const f of frequencies) {
    const rounded = Math.round(f / 10) * 10;
    counts[rounded] = (counts[rounded] || 0) + 1;
  }
  
  let maxCount = 0;
  let dominant = FREQ_MAP.ROOT;
  for (const [freq, count] of Object.entries(counts)) {
    if (count > maxCount) {
      maxCount = count;
      dominant = parseFloat(freq);
    }
  }
  
  return dominant;
}

/**
 * Compute prime alignment score
 */
function computePrimeAlignment(snapshots: FrequencySnapshot[]): number {
  if (snapshots.length === 0) return 0;
  
  let alignedCount = 0;
  for (let i = 0; i < snapshots.length; i++) {
    // Check if index aligns with prime number
    if (PRIMES.includes(i + 1)) {
      alignedCount++;
    }
  }
  
  return alignedCount / Math.min(snapshots.length, 20);
}

/**
 * Compute Fibonacci alignment score
 */
function computeFibonacciAlignment(snapshots: FrequencySnapshot[]): number {
  if (snapshots.length < 2) return 0;
  
  // Check if price ratios align with Fibonacci
  let alignedCount = 0;
  for (let i = 1; i < snapshots.length; i++) {
    const ratio = snapshots[i].price / snapshots[i - 1].price;
    // Check proximity to common Fib ratios: 0.618, 1.0, 1.618
    const fibRatios = [0.382, 0.5, 0.618, 1.0, 1.618, 2.618];
    for (const fibRatio of fibRatios) {
      if (Math.abs(ratio - fibRatio) < 0.05) {
        alignedCount++;
        break;
      }
    }
  }
  
  return alignedCount / (snapshots.length - 1);
}

/**
 * Compute golden ratio proximity
 */
function computeGoldenProximity(snapshots: FrequencySnapshot[]): number {
  if (snapshots.length < 2) return 0;
  
  const prices = snapshots.map(s => s.price);
  const high = Math.max(...prices);
  const low = Math.min(...prices);
  const current = prices[prices.length - 1];
  
  if (high === low) return 0;
  
  const ratio = (current - low) / (high - low);
  const phiProximity = 1 - Math.abs(ratio - (1 / PHI));
  
  return Math.max(0, Math.min(1, phiProximity));
}

/**
 * HNC Probability Matrix Engine
 */
export class HNCProbabilityMatrix {
  private history: Map<string, FrequencySnapshot[]> = new Map();
  private maxHistory = 180; // 3 hours of minute data
  private probabilityCache: Map<string, { matrix: ProbabilityMatrix; timestamp: number }> = new Map();
  private cacheTTL = 60000; // 60 seconds
  private systemName: SystemName = 'harmonic-nexus';
  
  constructor() {
    console.log('🔮 HNC Probability Matrix initialized');
  }
  
  /**
   * Add a frequency snapshot to history
   */
  addSnapshot(snapshot: FrequencySnapshot): void {
    const symbol = snapshot.symbol;
    if (!this.history.has(symbol)) {
      this.history.set(symbol, []);
    }
    
    const history = this.history.get(symbol)!;
    history.push(snapshot);
    
    // Trim to max history
    if (history.length > this.maxHistory) {
      history.shift();
    }
  }
  
  /**
   * Create snapshot from market data
   */
  createSnapshot(
    symbol: string,
    price: number,
    volume: number,
    momentum: number,
    coherence: number
  ): FrequencySnapshot {
    // Convert price action to frequency using golden ratio
    const frequency = 432 * Math.pow(1 + momentum / 100, PHI);
    const clampedFreq = Math.max(174, Math.min(963, frequency));
    
    // Check if frequency is harmonic (near Solfeggio frequencies)
    const isHarmonic = Object.values(FREQ_MAP).some(
      f => Math.abs(clampedFreq - f) < 20
    );
    
    // Phase angle from price position
    const phaseAngle = ((price % 360) + 360) % 360;
    
    return {
      timestamp: Date.now(),
      symbol,
      price,
      frequency: clampedFreq,
      resonance: coherence,
      isHarmonic,
      momentum,
      volume,
      coherence,
      phaseAngle,
    };
  }
  
  /**
   * Get hourly data for a specific hour offset
   */
  private getHourlyData(symbol: string, hourOffset: number): FrequencySnapshot[] {
    const history = this.history.get(symbol) || [];
    const now = Date.now();
    
    const oneHour = 60 * 60 * 1000;
    let startTime: number;
    let endTime: number;
    
    if (hourOffset < 0) {
      startTime = now + hourOffset * oneHour;
      endTime = now + (hourOffset + 1) * oneHour;
    } else if (hourOffset === 0) {
      startTime = now - 30 * 60 * 1000;
      endTime = now + 30 * 60 * 1000;
    } else {
      return []; // Future data computed from patterns
    }
    
    return history.filter(s => s.timestamp >= startTime && s.timestamp <= endTime);
  }
  
  /**
   * Compute base signal from Hour -1 (lookback)
   */
  private computeBaseSignal(symbol: string): HourlyProbabilityWindow {
    const now = Date.now();
    const oneHour = 60 * 60 * 1000;
    
    const window: HourlyProbabilityWindow = {
      hourOffset: -1,
      startTime: now - oneHour,
      endTime: now,
      bullishProbability: 0.5,
      bearishProbability: 0.5,
      confidence: 0,
      avgFrequency: FREQ_MAP.ROOT,
      dominantFrequency: FREQ_MAP.ROOT,
      frequencyTrend: 'STABLE',
      harmonicRatio: 0,
      primeAlignment: 0,
      fibonacciAlignment: 0,
      goldenRatioProximity: 0,
      signalStrength: 0,
      noiseRatio: 0.5,
      clarity: 0,
      state: 'NEUTRAL',
    };
    
    const data = this.getHourlyData(symbol, -1);
    if (data.length === 0) return window;
    
    // Calculate frequency metrics
    const frequencies = data.map(s => s.frequency);
    const momentums = data.map(s => s.momentum);
    const coherences = data.map(s => s.coherence);
    const harmonics = data.map(s => s.isHarmonic);
    const volumes = data.map(s => s.volume);
    
    window.avgFrequency = frequencies.reduce((a, b) => a + b, 0) / frequencies.length;
    window.dominantFrequency = findDominantFrequency(frequencies);
    window.harmonicRatio = harmonics.filter(h => h).length / harmonics.length;
    
    // Frequency trend
    if (frequencies.length >= 2) {
      const freqChange = frequencies[frequencies.length - 1] - frequencies[0];
      if (freqChange > 20) {
        window.frequencyTrend = 'RISING';
      } else if (freqChange < -20) {
        window.frequencyTrend = 'FALLING';
      }
    }
    
    // Momentum analysis for probability
    const avgMomentum = momentums.reduce((a, b) => a + b, 0) / momentums.length;
    const avgVolume = volumes.reduce((a, b) => a + b, 0) / volumes.length;
    
    // Volume trend
    let volumeFactor = 1.0;
    if (volumes.length >= 2 && avgVolume > 0) {
      const volumeTrend = (volumes[volumes.length - 1] - volumes[0]) / avgVolume;
      if (volumeTrend > 0.1) volumeFactor = 1.1;
      else if (volumeTrend < -0.1) volumeFactor = 0.9;
    }
    
    // Convert momentum to probability
    const momentumSignal = Math.tanh(avgMomentum / 10);
    window.bullishProbability = 0.5 + momentumSignal * 0.3 * volumeFactor;
    window.bearishProbability = 1 - window.bullishProbability;
    
    // Coherence affects confidence
    window.confidence = coherences.reduce((a, b) => a + b, 0) / coherences.length;
    
    // Signal strength
    window.signalStrength = window.harmonicRatio * window.confidence;
    
    // Noise ratio
    const coherenceStd = Math.sqrt(
      coherences.reduce((sum, c) => sum + Math.pow(c - window.confidence, 2), 0) / coherences.length
    );
    window.noiseRatio = 1 - Math.min(1, coherenceStd * 2);
    
    // Clarity
    window.clarity = window.signalStrength / (window.signalStrength + window.noiseRatio + 0.01);
    
    // Pattern alignments
    window.primeAlignment = computePrimeAlignment(data);
    window.fibonacciAlignment = computeFibonacciAlignment(data);
    window.goldenRatioProximity = computeGoldenProximity(data);
    
    window.state = computeState(window.bullishProbability);
    return window;
  }
  
  /**
   * Compute current state (Hour 0)
   */
  private computeCurrentState(currentData: {
    frequency: number;
    isHarmonic: boolean;
    momentum: number;
    volume: number;
    coherence: number;
    resonance: number;
  }): HourlyProbabilityWindow {
    const now = Date.now();
    
    const window: HourlyProbabilityWindow = {
      hourOffset: 0,
      startTime: now - 30 * 60 * 1000,
      endTime: now + 30 * 60 * 1000,
      bullishProbability: 0.5,
      bearishProbability: 0.5,
      confidence: currentData.coherence,
      avgFrequency: currentData.frequency,
      dominantFrequency: currentData.frequency,
      frequencyTrend: 'STABLE',
      harmonicRatio: currentData.isHarmonic ? 1.0 : 0.0,
      primeAlignment: 0,
      fibonacciAlignment: 0,
      goldenRatioProximity: 0,
      signalStrength: currentData.resonance,
      noiseRatio: 0.5,
      clarity: 0.5,
      state: 'NEUTRAL',
    };
    
    const momentumSignal = Math.tanh(currentData.momentum / 10);
    const volumeConfidence = currentData.volume > 0 ? 1.05 : 1.0;
    
    window.bullishProbability = 0.5 + momentumSignal * 0.35 * volumeConfidence;
    window.bearishProbability = 1 - window.bullishProbability;
    
    window.state = computeState(window.bullishProbability);
    return window;
  }
  
  /**
   * Forecast Hour +1 (PRIMARY trading window)
   */
  private forecastHourPlus1(
    baseSignal: HourlyProbabilityWindow,
    current: HourlyProbabilityWindow
  ): HourlyProbabilityWindow {
    const now = Date.now();
    const oneHour = 60 * 60 * 1000;
    
    const window: HourlyProbabilityWindow = {
      hourOffset: 1,
      startTime: now,
      endTime: now + oneHour,
      bullishProbability: 0.5,
      bearishProbability: 0.5,
      confidence: 0,
      avgFrequency: current.avgFrequency,
      dominantFrequency: current.avgFrequency,
      frequencyTrend: baseSignal.frequencyTrend,
      harmonicRatio: (baseSignal.harmonicRatio + current.harmonicRatio) / 2,
      primeAlignment: baseSignal.primeAlignment,
      fibonacciAlignment: baseSignal.fibonacciAlignment,
      goldenRatioProximity: baseSignal.goldenRatioProximity,
      signalStrength: 0,
      noiseRatio: 0.5,
      clarity: 0,
      state: 'NEUTRAL',
    };
    
    // Project frequency based on trend
    const freqDelta = current.avgFrequency - baseSignal.avgFrequency;
    if (baseSignal.frequencyTrend === 'RISING') {
      window.avgFrequency = current.avgFrequency + freqDelta * 0.5;
    } else if (baseSignal.frequencyTrend === 'FALLING') {
      window.avgFrequency = current.avgFrequency - Math.abs(freqDelta) * 0.5;
    }
    window.dominantFrequency = window.avgFrequency;
    
    // Probability projection: 40% base, 60% current
    let projectedBullish = baseSignal.bullishProbability * 0.4 + current.bullishProbability * 0.6;
    
    // Volume confirmation boost
    if (baseSignal.bullishProbability > 0.55 && baseSignal.signalStrength > 0.6) {
      projectedBullish *= 1.05;
    }
    
    // Harmonic boost/penalty
    if (current.harmonicRatio > 0.5) {
      projectedBullish *= 1.1; // 10% boost for harmonic
    } else if (window.avgFrequency >= 435 && window.avgFrequency <= 445) {
      projectedBullish *= 0.9; // 10% penalty for 440 Hz distortion
    }
    
    window.bullishProbability = Math.max(0.1, Math.min(0.9, projectedBullish));
    window.bearishProbability = 1 - window.bullishProbability;
    
    // Confidence
    window.confidence = 
      baseSignal.confidence * 0.3 +
      current.confidence * 0.5 +
      baseSignal.primeAlignment * 0.1 +
      baseSignal.fibonacciAlignment * 0.1;
    
    window.signalStrength = window.harmonicRatio * window.confidence;
    window.clarity = window.signalStrength * baseSignal.clarity;
    
    window.state = computeState(window.bullishProbability);
    return window;
  }
  
  /**
   * Forecast Hour +2 (FINE-TUNING window)
   */
  private forecastHourPlus2(
    baseSignal: HourlyProbabilityWindow,
    current: HourlyProbabilityWindow,
    hour1: HourlyProbabilityWindow
  ): HourlyProbabilityWindow {
    const now = Date.now();
    const oneHour = 60 * 60 * 1000;
    const decay = 0.7; // Confidence decays further out
    
    const window: HourlyProbabilityWindow = {
      hourOffset: 2,
      startTime: now + oneHour,
      endTime: now + 2 * oneHour,
      bullishProbability: 0.5,
      bearishProbability: 0.5,
      confidence: hour1.confidence * decay,
      avgFrequency: FREQ_MAP.ROOT,
      dominantFrequency: FREQ_MAP.ROOT,
      frequencyTrend: hour1.frequencyTrend,
      harmonicRatio: hour1.harmonicRatio * decay,
      primeAlignment: hour1.primeAlignment,
      fibonacciAlignment: hour1.fibonacciAlignment,
      goldenRatioProximity: hour1.goldenRatioProximity,
      signalStrength: hour1.signalStrength * decay,
      noiseRatio: 0.5,
      clarity: hour1.clarity * decay,
      state: 'NEUTRAL',
    };
    
    // Frequency with momentum decay
    if (hour1.frequencyTrend === 'RISING') {
      window.avgFrequency = hour1.avgFrequency * 1.02 * decay + FREQ_MAP.ROOT * (1 - decay);
    } else if (hour1.frequencyTrend === 'FALLING') {
      window.avgFrequency = hour1.avgFrequency * 0.98 * decay + FREQ_MAP.ROOT * (1 - decay);
    } else {
      window.avgFrequency = hour1.avgFrequency * decay + FREQ_MAP.ROOT * (1 - decay);
    }
    window.dominantFrequency = window.avgFrequency;
    
    // Probability with mean reversion
    const meanReversion = 0.3;
    window.bullishProbability = hour1.bullishProbability * (1 - meanReversion) + 0.5 * meanReversion;
    window.bearishProbability = 1 - window.bullishProbability;
    
    window.state = computeState(window.bullishProbability);
    return window;
  }
  
  /**
   * Generate complete probability matrix
   */
  generateMatrix(
    symbol: string,
    currentData: {
      price: number;
      volume: number;
      momentum: number;
      coherence: number;
      resonance?: number;
    }
  ): ProbabilityMatrix {
    // Check cache
    const cached = this.probabilityCache.get(symbol);
    if (cached && Date.now() - cached.timestamp < this.cacheTTL) {
      return cached.matrix;
    }
    
    // Add current snapshot to history
    const snapshot = this.createSnapshot(
      symbol,
      currentData.price,
      currentData.volume,
      currentData.momentum,
      currentData.coherence
    );
    this.addSnapshot(snapshot);
    
    // Compute all windows
    const hourMinus1 = this.computeBaseSignal(symbol);
    const hour0 = this.computeCurrentState({
      frequency: snapshot.frequency,
      isHarmonic: snapshot.isHarmonic,
      momentum: currentData.momentum,
      volume: currentData.volume,
      coherence: currentData.coherence,
      resonance: currentData.resonance || currentData.coherence,
    });
    const hourPlus1 = this.forecastHourPlus1(hourMinus1, hour0);
    const hourPlus2 = this.forecastHourPlus2(hourMinus1, hour0, hourPlus1);
    
    // Combined probability from Hour +1 (primary)
    const combinedProbability = hourPlus1.bullishProbability;
    
    // Fine-tune using Hour +2
    const fineTuneAdjustment = (hourPlus2.bullishProbability - 0.5) * 0.1;
    const fineTunedProbability = Math.max(0.1, Math.min(0.9, 
      combinedProbability + fineTuneAdjustment
    ));
    
    // Determine action
    let recommendedAction: 'BUY' | 'SELL' | 'HOLD' = 'HOLD';
    if (fineTunedProbability > 0.60) {
      recommendedAction = 'BUY';
    } else if (fineTunedProbability < 0.40) {
      recommendedAction = 'SELL';
    }
    
    // Position modifier (0.5 - 1.5 range)
    const positionModifier = 0.5 + fineTunedProbability;
    
    // Fine-tune reason
    let fineTuneReason = '';
    if (Math.abs(fineTuneAdjustment) > 0.02) {
      fineTuneReason = fineTuneAdjustment > 0 
        ? 'Hour +2 confirms bullish continuation'
        : 'Hour +2 suggests momentum fade';
    }
    
    const matrix: ProbabilityMatrix = {
      symbol,
      generatedAt: Date.now(),
      hourMinus1,
      hour0,
      hourPlus1,
      hourPlus2,
      combinedProbability,
      fineTunedProbability,
      confidenceScore: hourPlus1.confidence,
      recommendedAction,
      positionModifier,
      fineTuneAdjustment,
      fineTuneReason,
    };
    
    // Cache result
    this.probabilityCache.set(symbol, { matrix, timestamp: Date.now() });
    
    return matrix;
  }
  
  /**
   * Get trading signal from probability matrix
   */
  getTradingSignal(symbol: string, currentData: {
    price: number;
    volume: number;
    momentum: number;
    coherence: number;
  }): TradingSignal {
    const matrix = this.generateMatrix(symbol, currentData);
    
    return {
      probability: matrix.fineTunedProbability,
      confidence: matrix.confidenceScore,
      action: matrix.recommendedAction,
      modifier: matrix.positionModifier,
      h1State: matrix.hourPlus1?.state || 'NEUTRAL',
      fineTune: matrix.fineTuneAdjustment,
    };
  }
  
  /**
   * Register with Temporal Ladder and publish to UnifiedBus
   */
  publishState(matrix: ProbabilityMatrix): void {
    temporalLadder.registerSystem(this.systemName);
    temporalLadder.heartbeat(this.systemName, matrix.confidenceScore);
    
    let signal: SignalType = 'NEUTRAL';
    if (matrix.recommendedAction === 'BUY') signal = 'BUY';
    else if (matrix.recommendedAction === 'SELL') signal = 'SELL';
    
    unifiedBus.publish({
      systemName: 'HNCProbabilityMatrix',
      timestamp: Date.now(),
      ready: true,
      coherence: matrix.hourPlus1?.harmonicRatio || 0,
      confidence: matrix.confidenceScore,
      signal,
      data: {
        fineTunedProbability: matrix.fineTunedProbability,
        h1State: matrix.hourPlus1?.state,
        h2State: matrix.hourPlus2?.state,
        frequencyTrend: matrix.hourPlus1?.frequencyTrend,
        positionModifier: matrix.positionModifier,
      },
    });
  }
  
  /**
   * Get last cached matrix for symbol
   */
  getLastMatrix(symbol: string): ProbabilityMatrix | null {
    return this.probabilityCache.get(symbol)?.matrix || null;
  }
}

// Singleton instance
export const hncProbabilityMatrix = new HNCProbabilityMatrix();
