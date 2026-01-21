import { StargateActivation, NetworkMetrics } from './stargateLattice';

export interface FrequencyHarmonic {
  frequency: number;
  strength: number; // 0-1, based on node coherence
  nodeName: string;
  resonanceType: 'FOUNDATION' | 'HEART' | 'VISION' | 'UNITY'; // Based on frequency range
}

export interface HarmonizationProfile {
  dominantFrequency: number;
  harmonics: FrequencyHarmonic[];
  coherenceBoost: number; // -0.3 to +0.3
  signalAmplification: number; // 0.5 to 2.0
  tradingBias: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  confidenceModifier: number; // 0.7 to 1.3
  optimalEntryWindow: boolean; // true when harmonics align
  resonanceQuality: number; // 0-1
}

export class StargateFrequencyHarmonizer {
  /**
   * Analyze active stargates and generate harmonization profile
   */
  harmonize(
    activations: StargateActivation[], 
    metrics: NetworkMetrics
  ): HarmonizationProfile {
    // Extract all active frequencies weighted by node coherence
    const harmonics: FrequencyHarmonic[] = [];
    const frequencyMap = new Map<number, { strength: number; nodes: string[] }>();

    activations
      .filter(a => a.status === 'ACTIVE')
      .forEach(activation => {
        // Weight by both coherence and connection strength
        const weight = (activation.coherence + activation.connectionStrength) / 2;
        
        const existing = frequencyMap.get(activation.frequencyLock);
        if (existing) {
          existing.strength += weight;
          existing.nodes.push(activation.nodeName);
        } else {
          frequencyMap.set(activation.frequencyLock, {
            strength: weight,
            nodes: [activation.nodeName]
          });
        }
      });

    // Convert to harmonics array
    frequencyMap.forEach((data, freq) => {
      harmonics.push({
        frequency: freq,
        strength: Math.min(1, data.strength / activations.length),
        nodeName: data.nodes.join(', '),
        resonanceType: this.getResonanceType(freq),
      });
    });

    // Sort by strength
    harmonics.sort((a, b) => b.strength - a.strength);

    // Determine dominant frequency (strongest)
    const dominantFrequency = harmonics[0]?.frequency || 528;

    // Calculate coherence boost based on network strength and dominant frequency
    const coherenceBoost = this.calculateCoherenceBoost(
      dominantFrequency, 
      metrics.networkStrength,
      harmonics
    );

    // Calculate signal amplification (how much to amplify trading signals)
    const signalAmplification = this.calculateSignalAmplification(
      metrics.avgCoherence,
      metrics.networkStrength,
      harmonics.length
    );

    // Determine trading bias based on frequency characteristics
    const tradingBias = this.determineTradingBias(dominantFrequency, harmonics);

    // Calculate confidence modifier
    const confidenceModifier = this.calculateConfidenceModifier(
      metrics.networkStrength,
      harmonics
    );

    // Detect optimal entry windows (when 3+ harmonics align)
    const optimalEntryWindow = this.detectOptimalWindow(harmonics, metrics);

    // Calculate overall resonance quality
    const resonanceQuality = this.calculateResonanceQuality(harmonics, metrics);

    return {
      dominantFrequency,
      harmonics,
      coherenceBoost,
      signalAmplification,
      tradingBias,
      confidenceModifier,
      optimalEntryWindow,
      resonanceQuality,
    };
  }

  private getResonanceType(frequency: number): 'FOUNDATION' | 'HEART' | 'VISION' | 'UNITY' {
    if (frequency < 400) return 'FOUNDATION'; // Root/Sacral (174-396)
    if (frequency < 550) return 'HEART'; // Heart (417-528)
    if (frequency < 750) return 'VISION'; // Throat/Third Eye (639-741)
    return 'UNITY'; // Crown/Unity (852-963+)
  }

  private calculateCoherenceBoost(
    dominantFreq: number, 
    networkStrength: number,
    harmonics: FrequencyHarmonic[]
  ): number {
    // 528 Hz (love frequency) provides maximum boost
    const frequencyFactor = Math.abs(dominantFreq - 528) / 528;
    const baseBoost = (1 - frequencyFactor) * 0.3; // -0.3 to +0.3
    
    // Network strength multiplier
    const strengthMultiplier = networkStrength;
    
    // Harmonic diversity bonus (more unique frequencies = better)
    const diversityBonus = Math.min(harmonics.length / 12, 1) * 0.1;
    
    return (baseBoost * strengthMultiplier) + diversityBonus;
  }

  private calculateSignalAmplification(
    avgCoherence: number,
    networkStrength: number,
    harmonicCount: number
  ): number {
    // Base amplification from network strength (0.5 to 2.0)
    const base = 0.5 + (networkStrength * 1.5);
    
    // Coherence modifier
    const coherenceMod = avgCoherence * 0.3;
    
    // Harmonic count bonus (more harmonics = more amplification)
    const harmonicBonus = (harmonicCount / 12) * 0.2;
    
    return Math.max(0.5, Math.min(2.0, base + coherenceMod + harmonicBonus));
  }

  private determineTradingBias(
    dominantFreq: number,
    harmonics: FrequencyHarmonic[]
  ): 'BULLISH' | 'BEARISH' | 'NEUTRAL' {
    // Higher frequencies (above 528) tend toward bullish
    // Lower frequencies (below 528) tend toward bearish
    // 528 Hz (love/balance) is neutral
    
    const deviation = dominantFreq - 528;
    const threshold = 150; // Hz threshold for bias
    
    // Check if multiple high-frequency harmonics are active
    const highFreqStrength = harmonics
      .filter(h => h.frequency > 528)
      .reduce((sum, h) => sum + h.strength, 0);
    
    const lowFreqStrength = harmonics
      .filter(h => h.frequency < 528)
      .reduce((sum, h) => sum + h.strength, 0);
    
    if (highFreqStrength - lowFreqStrength > 0.3) return 'BULLISH';
    if (lowFreqStrength - highFreqStrength > 0.3) return 'BEARISH';
    if (Math.abs(deviation) < threshold) return 'NEUTRAL';
    
    return deviation > 0 ? 'BULLISH' : 'BEARISH';
  }

  private calculateConfidenceModifier(
    networkStrength: number,
    harmonics: FrequencyHarmonic[]
  ): number {
    // Base confidence from network strength
    const base = 0.7 + (networkStrength * 0.6); // 0.7 to 1.3
    
    // Penalty for too few harmonics (lack of diversity)
    const diversityPenalty = harmonics.length < 3 ? 0.1 : 0;
    
    // Bonus for strong individual harmonics
    const strongHarmonicBonus = harmonics.filter(h => h.strength > 0.8).length * 0.05;
    
    return Math.max(0.7, Math.min(1.3, base - diversityPenalty + strongHarmonicBonus));
  }

  private detectOptimalWindow(
    harmonics: FrequencyHarmonic[],
    metrics: NetworkMetrics
  ): boolean {
    // Optimal window when:
    // 1. At least 3 strong harmonics (>0.7 strength)
    // 2. Network strength >0.9
    // 3. Avg coherence >0.85
    
    const strongHarmonics = harmonics.filter(h => h.strength > 0.7).length;
    
    return (
      strongHarmonics >= 3 &&
      metrics.networkStrength > 0.9 &&
      metrics.avgCoherence > 0.85
    );
  }

  private calculateResonanceQuality(
    harmonics: FrequencyHarmonic[],
    metrics: NetworkMetrics
  ): number {
    // Combine multiple factors into overall quality score (0-1)
    
    // Factor 1: Harmonic strength distribution
    const avgStrength = harmonics.reduce((sum, h) => sum + h.strength, 0) / harmonics.length;
    
    // Factor 2: Network metrics
    const networkQuality = (metrics.avgCoherence + metrics.networkStrength + metrics.avgEnergyFlow) / 3;
    
    // Factor 3: Harmonic diversity (more unique frequencies = better)
    const diversityScore = Math.min(harmonics.length / 12, 1);
    
    // Weighted combination
    return (avgStrength * 0.4) + (networkQuality * 0.4) + (diversityScore * 0.2);
  }
}

export const stargateHarmonizer = new StargateFrequencyHarmonizer();
