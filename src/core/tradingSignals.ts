// Trading Signals - Combines Lighthouse + High Coherence for optimal entry points
// Trade signal confirmed when:
// 1. Lighthouse Event (LHE) detected
// 2. Coherence Γ > 0.945
// 3. Prism state is CONVERGING or MANIFEST

import type { LighthouseState } from './lighthouseConsensus';
import type { LambdaState } from './masterEquation';
import type { PrismOutput } from './prism';
import type { HarmonizationProfile } from './stargateFrequencyHarmonizer';

export type TradingSignal = {
  timestamp: number;
  type: 'LONG' | 'SHORT' | 'HOLD';
  strength: number;        // 0-1, confidence in signal
  lighthouse: number;      // L(t) value
  coherence: number;       // Γ value
  prismLevel: number;      // 1-5
  reason: string;
  harmonizationBoost?: number; // Boost from frequency harmonization
  tradingBias?: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
};

export class TradingSignalGenerator {
  private readonly COHERENCE_THRESHOLD = 0.945;
  private lastSignal: TradingSignal | null = null;
  private signalHistory: TradingSignal[] = [];
  private readonly maxHistory = 50;
  
  generateSignal(
    lambda: LambdaState,
    lighthouse: LighthouseState,
    prism: PrismOutput,
    harmonization?: HarmonizationProfile
  ): TradingSignal {
    const timestamp = Date.now();
    
    // Apply frequency harmonization if available
    const harmonizedCoherence = harmonization 
      ? lambda.coherence + harmonization.coherenceBoost 
      : lambda.coherence;
    
    // Check conditions for optimal trading moment
    const highCoherence = harmonizedCoherence >= this.COHERENCE_THRESHOLD;
    const lighthouseEvent = lighthouse.isLHE;
    const prismReady = prism.state === 'CONVERGING' || prism.state === 'MANIFEST';
    const optimalWindow = harmonization?.optimalEntryWindow || false;
    
    // Determine signal type and strength
    let type: 'LONG' | 'SHORT' | 'HOLD' = 'HOLD';
    let strength = 0;
    let reason = '';
    
    // Apply trading bias from harmonization
    const biasModifier = harmonization ? this.getBiasModifier(harmonization.tradingBias) : 1;
    const signalAmp = harmonization?.signalAmplification || 1;
    const confidenceMod = harmonization?.confidenceModifier || 1;
    
    if (optimalWindow && lighthouseEvent && highCoherence && prismReady) {
      // PERFECT conditions - optimal entry window with all systems aligned
      type = harmonization?.tradingBias === 'BEARISH' ? 'SHORT' : 'LONG';
      strength = Math.min(
        lighthouse.confidence * harmonizedCoherence * (prism.level / 5) * signalAmp * confidenceMod,
        1
      );
      reason = `🌟 PERFECT: Optimal Window + LHE + Γ=${harmonizedCoherence.toFixed(3)} + Prism L${prism.level} + ${harmonization?.dominantFrequency}Hz`;
      
    } else if (lighthouseEvent && highCoherence && prismReady) {
      // Optimal conditions - strongest signal
      type = harmonization?.tradingBias === 'BEARISH' ? 'SHORT' : 'LONG';
      strength = Math.min(
        lighthouse.confidence * harmonizedCoherence * (prism.level / 5) * signalAmp * biasModifier,
        1
      );
      reason = `🎯 OPTIMAL: LHE + Γ=${harmonizedCoherence.toFixed(3)} + Prism L${prism.level}`;
      if (harmonization) {
        reason += ` + ${harmonization.tradingBias} bias`;
      }
      
    } else if (lighthouseEvent && highCoherence) {
      // Strong signal - lighthouse + coherence
      type = harmonization?.tradingBias === 'BEARISH' ? 'SHORT' : 'LONG';
      strength = lighthouse.confidence * harmonizedCoherence * 0.8 * signalAmp * biasModifier;
      reason = `✨ STRONG: LHE + High Coherence Γ=${harmonizedCoherence.toFixed(3)}`;
      
    } else if (highCoherence && prismReady) {
      // Moderate signal - coherence + prism alignment
      type = 'LONG';
      strength = harmonizedCoherence * (prism.level / 5) * 0.6 * signalAmp;
      reason = `📊 MODERATE: High Γ + Prism ${prism.state}`;
      
    } else if (harmonizedCoherence < 0.3 && lighthouse.L < lighthouse.threshold * 0.5) {
      // Weak conditions - consider short (amplified if bearish bias)
      type = 'SHORT';
      const shortBias = harmonization?.tradingBias === 'BEARISH' ? 1.5 : 1;
      strength = (1 - harmonizedCoherence) * 0.4 * shortBias;
      reason = `⚠️ WEAK: Low Γ=${harmonizedCoherence.toFixed(3)} + Low L(t)`;
      
    } else {
      // Hold - conditions not met
      type = 'HOLD';
      strength = 0.5;
      reason = `⏸️ HOLD: Γ=${harmonizedCoherence.toFixed(3)}, L(t)=${lighthouse.L.toFixed(2)}`;
    }
    
    const signal: TradingSignal = {
      timestamp,
      type,
      strength,
      lighthouse: lighthouse.L,
      coherence: harmonizedCoherence,
      prismLevel: prism.level,
      reason,
      harmonizationBoost: harmonization?.coherenceBoost,
      tradingBias: harmonization?.tradingBias,
    };
    
    this.lastSignal = signal;
    this.signalHistory.push(signal);
    
    if (this.signalHistory.length > this.maxHistory) {
      this.signalHistory.shift();
    }
    
    return signal;
  }

  private getBiasModifier(bias: 'BULLISH' | 'BEARISH' | 'NEUTRAL'): number {
    // Amplify signals that align with bias
    if (bias === 'BULLISH') return 1.2;
    if (bias === 'BEARISH') return 0.9; // Reduce long signals in bearish conditions
    return 1.0;
  }
  
  getLastSignal(): TradingSignal | null {
    return this.lastSignal;
  }
  
  getSignalHistory(): TradingSignal[] {
    return [...this.signalHistory];
  }
  
  // Get trade signal statistics
  getStatistics() {
    if (this.signalHistory.length === 0) {
      return {
        totalSignals: 0,
        longSignals: 0,
        shortSignals: 0,
        holdSignals: 0,
        averageStrength: 0,
        optimalSignals: 0,
      };
    }
    
    const longSignals = this.signalHistory.filter(s => s.type === 'LONG').length;
    const shortSignals = this.signalHistory.filter(s => s.type === 'SHORT').length;
    const holdSignals = this.signalHistory.filter(s => s.type === 'HOLD').length;
    const optimalSignals = this.signalHistory.filter(s => 
      s.reason.startsWith('🎯 OPTIMAL')
    ).length;
    
    const averageStrength = this.signalHistory.reduce((sum, s) => sum + s.strength, 0) / this.signalHistory.length;
    
    return {
      totalSignals: this.signalHistory.length,
      longSignals,
      shortSignals,
      holdSignals,
      averageStrength,
      optimalSignals,
    };
  }
  
  reset() {
    this.lastSignal = null;
    this.signalHistory = [];
  }
}
