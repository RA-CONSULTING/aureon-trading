/**
 * Earth-AUREON Bridge
 * Integrates Earth's electromagnetic field (Schumann resonance), solar wind, and geomagnetic data
 * into AUREON's Master Equation for quantum-enhanced trading signals
 * 
 * TEMPORAL LADDER INTEGRATION: Registered as 'earth-integration' system
 */

import type { SimpleEarthStreams } from '../lib/earth-streams';
// import type { EmotionalState } from '../lib/schumann-emotional-mapping';
// import { generateRegionalEmotionalState, generateEmotionalState, SCHUMANN_FREQUENCIES } from '../lib/schumann-emotional-mapping';
import { temporalLadder, SYSTEMS } from './temporalLadder';

// Temporary inline type until schumann-emotional-mapping is restored
type EmotionalState = { dominant: string; valence: number; arousal: number; intensity: number };
const SCHUMANN_FREQUENCIES = { 
  fundamental: 7.83,
  second: 14.3,
  third: 20.8,
  fourth: 27.3,
  fifth: 33.8,
  base: 7.83, 
  harmonics: [14.3, 20.8, 27.3, 33.8] 
};

// Temporary stub functions
const generateRegionalEmotionalState = (regionId: string, lat?: number, lon?: number, freq?: number): EmotionalState => ({
  dominant: 'neutral',
  valence: 0.5,
  arousal: 0.5,
  intensity: 0.5
});

const generateEmotionalState = (freq: number, intensity?: number, tags?: string[]): EmotionalState => ({
  dominant: 'neutral',
  valence: 0.5,
  arousal: 0.5,
  intensity: intensity || 0.5
});

export interface EarthFieldInfluence {
  schumannCoherence: number;      // 0-1, Schumann resonance stability
  solarWindModifier: number;       // -0.2 to +0.2, solar wind impact
  geomagneticStability: number;    // 0-1, geomagnetic field strength
  emotionalResonance: number;      // 0-1, collective emotional state
  combinedBoost: number;           // Net boost to trading coherence
  dominantFrequency: number;       // Hz, current dominant Schumann freq
  emotionalState: EmotionalState | null;
}

export interface EarthAureonConfig {
  schumannWeight: number;     // 0-1, how much Schumann affects signals
  solarWindWeight: number;    // 0-1, solar wind influence
  emotionalWeight: number;    // 0-1, emotional field influence
  enableEarthSync: boolean;   // Master toggle
}

export class EarthAureonBridge {
  private config: EarthAureonConfig = {
    schumannWeight: 0.25,
    solarWindWeight: 0.15,
    emotionalWeight: 0.20,
    enableEarthSync: true
  };

  private lastUpdate: number = 0;
  private updateInterval: number = 2000; // 2 seconds
  private cachedInfluence: EarthFieldInfluence | null = null;

  constructor(config?: Partial<EarthAureonConfig>) {
    if (config) {
      this.config = { ...this.config, ...config };
    }
    
    // Register with Temporal Ladder
    temporalLadder.registerSystem(SYSTEMS.EARTH_INTEGRATION);
  }

  /**
   * Main integration point - call this from Master Equation
   */
  async getEarthInfluence(earthStreams?: SimpleEarthStreams, regionId?: string): Promise<EarthFieldInfluence> {
    // Send heartbeat to Temporal Ladder
    const health = this.config.enableEarthSync ? 1.0 : 0.5;
    temporalLadder.heartbeat(SYSTEMS.EARTH_INTEGRATION, health);
    
    // Check cache to avoid excessive computation
    const now = Date.now();
    if (this.cachedInfluence && (now - this.lastUpdate < this.updateInterval)) {
      return this.cachedInfluence;
    }

    if (!this.config.enableEarthSync) {
      // Request assistance from fallback system
      temporalLadder.requestAssistance(
        SYSTEMS.EARTH_INTEGRATION,
        SYSTEMS.NEXUS_FEED,
        'earth_sync_disabled'
      );
      return this.getDefaultInfluence();
    }

    // If no earth streams provided, generate simulated data
    if (!earthStreams) {
      earthStreams = this.generateSimulatedEarthData();
    }

    // Calculate Schumann coherence
    const schumannCoherence = this.calculateSchumannCoherence(earthStreams);

    // Calculate solar wind modifier
    const solarWindModifier = this.calculateSolarWindModifier(earthStreams);

    // Calculate geomagnetic stability
    const geomagneticStability = this.calculateGeomagneticStability(earthStreams);

    // Generate emotional state
    const emotionalState = regionId 
      ? generateRegionalEmotionalState(regionId)
      : this.generateGlobalEmotionalState(earthStreams);

    const emotionalResonance = emotionalState.intensity * emotionalState.valence;

    // Determine dominant frequency
    const dominantFrequency = this.determineDominantFrequency(earthStreams, schumannCoherence);

    // Calculate combined boost
    const combinedBoost = this.calculateCombinedBoost(
      schumannCoherence,
      solarWindModifier,
      geomagneticStability,
      emotionalResonance
    );

    this.cachedInfluence = {
      schumannCoherence,
      solarWindModifier,
      geomagneticStability,
      emotionalResonance,
      combinedBoost,
      dominantFrequency,
      emotionalState
    };

    this.lastUpdate = now;
    return this.cachedInfluence;
  }

  /**
   * Calculate Schumann resonance coherence
   * High coherence = stable Earth field = better trading signals
   */
  private calculateSchumannCoherence(streams: SimpleEarthStreams): number {
    const { geomagneticKp, fieldCoupling } = streams;

    // Lower Kp index = more stable field
    const kpStability = 1 - (geomagneticKp / 9);

    // Field coupling represents multi-layer synchronization
    const couplingFactor = Math.min(1, fieldCoupling / 2);

    // Combine factors
    const coherence = (kpStability * 0.6 + couplingFactor * 0.4);

    return Math.max(0, Math.min(1, coherence));
  }

  /**
   * Calculate solar wind impact on trading signals
   * Fast solar wind can disrupt or amplify depending on strength
   */
  private calculateSolarWindModifier(streams: SimpleEarthStreams): number {
    const { solarWindVelocity } = streams;

    // Optimal range: 350-450 km/s
    const optimalVelocity = 400;
    const deviation = Math.abs(solarWindVelocity - optimalVelocity);

    // Small deviation = positive modifier, large = negative
    if (deviation < 50) {
      return 0.1 * (1 - deviation / 50); // 0 to +0.1
    } else if (deviation < 150) {
      return -0.05 * ((deviation - 50) / 100); // -0.05 to 0
    } else {
      return -0.15; // Strong disruption
    }
  }

  /**
   * Calculate geomagnetic field stability
   */
  private calculateGeomagneticStability(streams: SimpleEarthStreams): number {
    const { geomagneticKp, ionosphericDensity } = streams;

    // Stable conditions
    if (geomagneticKp < 3) {
      return 0.9 + (ionosphericDensity / 100) * 0.1;
    }

    // Moderate activity
    if (geomagneticKp < 5) {
      return 0.6 + (ionosphericDensity / 100) * 0.1;
    }

    // Storm conditions
    return 0.3 - (geomagneticKp / 20);
  }

  /**
   * Generate emotional state from earth streams when no region specified
   */
  private generateGlobalEmotionalState(streams: SimpleEarthStreams): EmotionalState {
    // Map field coupling to frequency range
    const { fieldCoupling, geomagneticKp } = streams;

    // Use fundamental Schumann frequency as base
    let frequency = SCHUMANN_FREQUENCIES.fundamental;

    // Modulate based on geomagnetic activity
    if (geomagneticKp > 5) {
      frequency = SCHUMANN_FREQUENCIES.fourth; // Higher tension
    } else if (geomagneticKp < 2) {
      frequency = SCHUMANN_FREQUENCIES.second; // Calm, harmonious
    }

    // Intensity from field coupling
    const intensity = Math.min(1, fieldCoupling / 2);

    return generateEmotionalState(frequency, intensity, ['Global', 'Field', 'Resonance']);
  }

  /**
   * Determine current dominant Schumann frequency
   */
  private determineDominantFrequency(streams: SimpleEarthStreams, coherence: number): number {
    const { geomagneticKp } = streams;

    // During high coherence, fundamental dominates
    if (coherence > 0.7) {
      return SCHUMANN_FREQUENCIES.fundamental;
    }

    // During disturbances, higher harmonics emerge
    if (geomagneticKp > 5) {
      return SCHUMANN_FREQUENCIES.fourth;
    }

    // Moderate conditions - second harmonic
    return SCHUMANN_FREQUENCIES.second;
  }

  /**
   * Calculate combined boost to apply to Master Equation coherence
   */
  private calculateCombinedBoost(
    schumannCoherence: number,
    solarWindModifier: number,
    geomagneticStability: number,
    emotionalResonance: number
  ): number {
    const schumannContribution = schumannCoherence * this.config.schumannWeight;
    const solarContribution = solarWindModifier * this.config.solarWindWeight;
    const emotionalContribution = emotionalResonance * this.config.emotionalWeight;
    const geomagneticContribution = geomagneticStability * 0.1; // Small stabilizing factor

    const total = schumannContribution + solarContribution + emotionalContribution + geomagneticContribution;

    // Clamp to reasonable range
    return Math.max(-0.15, Math.min(0.25, total));
  }

  /**
   * Generate simulated earth data for testing
   */
  private generateSimulatedEarthData(): SimpleEarthStreams {
    const time = Date.now();
    
    return {
      solarWindVelocity: 400 + Math.sin(time / 20000) * 100 + Math.random() * 50,
      geomagneticKp: 2 + Math.sin(time / 30000) * 2 + Math.random() * 1,
      ionosphericDensity: 50 + Math.cos(time / 25000) * 20 + Math.random() * 10,
      fieldCoupling: 1.2 + Math.sin(time / 15000) * 0.5 + Math.random() * 0.3
    };
  }

  /**
   * Default influence when earth sync is disabled
   */
  private getDefaultInfluence(): EarthFieldInfluence {
    return {
      schumannCoherence: 0.5,
      solarWindModifier: 0,
      geomagneticStability: 0.5,
      emotionalResonance: 0.5,
      combinedBoost: 0,
      dominantFrequency: SCHUMANN_FREQUENCIES.fundamental,
      emotionalState: null
    };
  }

  /**
   * Update configuration
   */
  setConfig(config: Partial<EarthAureonConfig>) {
    this.config = { ...this.config, ...config };
    this.cachedInfluence = null; // Invalidate cache
  }

  /**
   * Get current configuration
   */
  getConfig(): EarthAureonConfig {
    return { ...this.config };
  }

  /**
   * Force cache refresh
   */
  invalidateCache() {
    this.cachedInfluence = null;
    this.lastUpdate = 0;
  }
}

// Singleton instance
export const earthAureonBridge = new EarthAureonBridge();
