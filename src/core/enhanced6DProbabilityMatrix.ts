/**
 * Enhanced 6D Probability Matrix
 * Fuses 6D Harmonic probability with HNC/Lighthouse probability
 */

import { sixDimensionalEngine, HarmonicWaveform6D, WaveState } from './sixDimensionalHarmonicEngine';

export type TradingAction = 
  | 'STRONG_BUY' 
  | 'BUY' 
  | 'SLIGHT_BUY' 
  | 'HOLD' 
  | 'SLIGHT_SELL' 
  | 'SELL' 
  | 'STRONG_SELL';

export interface ProbabilityFusion {
  // Input probabilities
  probability6D: number;
  probabilityHNC: number;
  probabilityLighthouse: number;
  
  // Weights (dynamic based on wave state)
  weight6D: number;
  weightHNC: number;
  weightLighthouse: number;
  
  // Output
  fusedProbability: number;
  action: TradingAction;
  confidence: number;
  
  // Metadata
  waveState: WaveState;
  harmonicLock: boolean;
  resonanceBoost: number;
}

interface DynamicWeights {
  w6D: number;
  wHNC: number;
  wLighthouse: number;
}

function getWeightsForWaveState(waveState: WaveState): DynamicWeights {
  // Weights shift based on wave state
  switch (waveState) {
    case 'CRYSTALLINE':
      // In crystalline state, 6D is most reliable
      return { w6D: 0.50, wHNC: 0.30, wLighthouse: 0.20 };
    case 'RESONANT':
      // Balanced weights
      return { w6D: 0.40, wHNC: 0.35, wLighthouse: 0.25 };
    case 'TURBULENT':
      // Trust HNC more in turbulent conditions
      return { w6D: 0.30, wHNC: 0.40, wLighthouse: 0.30 };
    case 'CHAOTIC':
      // In chaos, rely more on Lighthouse consensus
      return { w6D: 0.20, wHNC: 0.35, wLighthouse: 0.45 };
    default:
      return { w6D: 0.33, wHNC: 0.34, wLighthouse: 0.33 };
  }
}

function mapProbabilityToAction(probability: number): TradingAction {
  if (probability >= 0.70) return 'STRONG_BUY';
  if (probability >= 0.60) return 'BUY';
  if (probability >= 0.55) return 'SLIGHT_BUY';
  if (probability >= 0.45) return 'HOLD';
  if (probability >= 0.40) return 'SLIGHT_SELL';
  if (probability >= 0.30) return 'SELL';
  return 'STRONG_SELL';
}

function calculateConfidence(
  fusedProb: number,
  waveState: WaveState,
  harmonicLock: boolean,
  inputVariance: number
): number {
  // Base confidence from distance from 0.5 (neutral)
  const baseConfidence = Math.abs(fusedProb - 0.5) * 2;
  
  // Wave state multiplier
  const stateMultiplier = 
    waveState === 'CRYSTALLINE' ? 1.0 :
    waveState === 'RESONANT' ? 0.85 :
    waveState === 'TURBULENT' ? 0.65 : 0.45;
  
  // Harmonic lock boost
  const lockBoost = harmonicLock ? 0.15 : 0;
  
  // Variance penalty (lower variance = higher confidence)
  const variancePenalty = Math.min(0.2, inputVariance * 0.5);
  
  return Math.min(1, Math.max(0, baseConfidence * stateMultiplier + lockBoost - variancePenalty));
}

export class Enhanced6DProbabilityMatrix {
  private lastFusion: ProbabilityFusion | null = null;
  
  fuse(
    symbol: string,
    hncProbability: number,
    lighthouseProbability: number,
    waveform?: HarmonicWaveform6D
  ): ProbabilityFusion {
    // Get 6D waveform if not provided
    const wf = waveform || sixDimensionalEngine.getWaveform(symbol);
    
    // Default 6D values if no waveform
    const prob6D = wf?.probabilityField ?? 0.5;
    const waveState = wf?.waveState ?? 'TURBULENT';
    const harmonicLock = wf?.harmonicLock ?? false;
    const resonanceScore = wf?.resonanceScore ?? 0.5;
    
    // Get dynamic weights based on wave state
    const weights = getWeightsForWaveState(waveState);
    
    // Calculate resonance boost (extra weight for 6D when in resonance)
    const resonanceBoost = resonanceScore > 0.7 ? (resonanceScore - 0.7) * 0.5 : 0;
    
    // Adjust weights with resonance boost
    const adjustedW6D = Math.min(0.6, weights.w6D + resonanceBoost);
    const remainingWeight = 1 - adjustedW6D;
    const ratio = weights.wHNC / (weights.wHNC + weights.wLighthouse);
    const adjustedWHNC = remainingWeight * ratio;
    const adjustedWLighthouse = remainingWeight * (1 - ratio);
    
    // Fuse probabilities
    const fusedProbability = 
      prob6D * adjustedW6D +
      hncProbability * adjustedWHNC +
      lighthouseProbability * adjustedWLighthouse;
    
    // Calculate input variance for confidence
    const mean = (prob6D + hncProbability + lighthouseProbability) / 3;
    const variance = (
      Math.pow(prob6D - mean, 2) +
      Math.pow(hncProbability - mean, 2) +
      Math.pow(lighthouseProbability - mean, 2)
    ) / 3;
    
    // Map to action
    const action = mapProbabilityToAction(fusedProbability);
    
    // Calculate confidence
    const confidence = calculateConfidence(fusedProbability, waveState, harmonicLock, variance);
    
    const fusion: ProbabilityFusion = {
      probability6D: prob6D,
      probabilityHNC: hncProbability,
      probabilityLighthouse: lighthouseProbability,
      weight6D: adjustedW6D,
      weightHNC: adjustedWHNC,
      weightLighthouse: adjustedWLighthouse,
      fusedProbability,
      action,
      confidence,
      waveState,
      harmonicLock,
      resonanceBoost
    };
    
    this.lastFusion = fusion;
    return fusion;
  }
  
  getLastFusion(): ProbabilityFusion | null {
    return this.lastFusion;
  }
  
  // Quick check if we should trade based on fusion
  shouldTrade(minConfidence = 0.6): boolean {
    if (!this.lastFusion) return false;
    
    const { action, confidence, waveState } = this.lastFusion;
    
    // Don't trade in chaotic state
    if (waveState === 'CHAOTIC') return false;
    
    // Need minimum confidence
    if (confidence < minConfidence) return false;
    
    // Only trade on actionable signals
    return action !== 'HOLD';
  }
  
  // Get direction: 1 = long, -1 = short, 0 = neutral
  getDirection(): number {
    if (!this.lastFusion) return 0;
    
    const { action } = this.lastFusion;
    
    if (['STRONG_BUY', 'BUY', 'SLIGHT_BUY'].includes(action)) return 1;
    if (['STRONG_SELL', 'SELL', 'SLIGHT_SELL'].includes(action)) return -1;
    return 0;
  }
}

// Singleton instance
export const probabilityMatrix = new Enhanced6DProbabilityMatrix();
