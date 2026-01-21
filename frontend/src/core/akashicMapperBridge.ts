/**
 * Akashic Mapper Bridge - Temporal Ladder Integration
 * Wraps the Akashic frequency mapping functionality and registers with hive mind
 */

import { temporalLadder, SYSTEMS } from './temporalLadder';
import { getTemporalId, getSentinelName } from './primelinesIdentity';

// Akashic frequency bands (Hz)
export const AKASHIC_FREQUENCIES = {
  ROOT: 396,        // Liberation from fear
  SACRAL: 417,      // Undoing situations
  SOLAR: 528,       // DNA repair / Love
  HEART: 639,       // Connecting relationships
  THROAT: 741,      // Awakening intuition
  THIRD_EYE: 852,   // Returning to spiritual order
  CROWN: 963,       // Divine consciousness
};

export interface AkashicState {
  activeFrequency: number;
  frequencyName: string;
  resonanceStrength: number;
  harmonicPurity: number;
  attenuationCycle: number;
  convergence: number;
  stability: number;
  timestamp: number;
}

export interface AkashicAttenuation {
  cyclePhase: number;      // 0-1 within current cycle
  attenuationFactor: number;
  boostMultiplier: number;
  isConverging: boolean;
}

class AkashicMapperBridge {
  private temporalId: string;
  private sentinelName: string;
  private currentState: AkashicState | null = null;
  private history: AkashicState[] = [];
  private maxHistory = 100;
  private attenuationCycle = 0;
  private isRegistered = false;

  constructor() {
    this.temporalId = getTemporalId();
    this.sentinelName = getSentinelName();
  }

  /**
   * Register with Temporal Ladder hive mind
   */
  public register(): void {
    if (this.isRegistered) return;
    
    temporalLadder.registerSystem(SYSTEMS.AKASHIC_MAPPER);
    this.isRegistered = true;
    console.log('📜 Akashic Mapper registered with Temporal Ladder');
  }

  /**
   * Unregister from Temporal Ladder
   */
  public unregister(): void {
    if (!this.isRegistered) return;
    
    temporalLadder.unregisterSystem(SYSTEMS.AKASHIC_MAPPER);
    this.isRegistered = false;
  }

  /**
   * Map a frequency value to its Akashic correspondence
   */
  public mapFrequency(inputFrequency: number): { name: string; frequency: number; deviation: number } {
    let closestName = 'UNKNOWN';
    let closestFreq = 0;
    let minDeviation = Infinity;

    Object.entries(AKASHIC_FREQUENCIES).forEach(([name, freq]) => {
      const deviation = Math.abs(inputFrequency - freq);
      if (deviation < minDeviation) {
        minDeviation = deviation;
        closestName = name;
        closestFreq = freq;
      }
    });

    return {
      name: closestName,
      frequency: closestFreq,
      deviation: minDeviation / closestFreq
    };
  }

  /**
   * Compute Akashic state from coherence and frequency inputs
   */
  public computeState(
    coherence: number,
    inputFrequency: number,
    timestamp: number
  ): AkashicState {
    // Map to nearest Akashic frequency
    const mapping = this.mapFrequency(inputFrequency);
    
    // Calculate resonance strength (how close to ideal frequency)
    const resonanceStrength = Math.max(0, 1 - mapping.deviation);
    
    // Harmonic purity based on coherence and resonance
    const harmonicPurity = coherence * resonanceStrength;
    
    // Attenuation cycle (used for convergence patterns)
    this.attenuationCycle = (this.attenuationCycle + 0.01) % 1;
    
    // Convergence increases when harmonic purity is high
    const convergence = harmonicPurity > 0.7 
      ? harmonicPurity * (1 + Math.sin(this.attenuationCycle * Math.PI * 2) * 0.1)
      : harmonicPurity * 0.5;
    
    // Stability from history variance
    const stability = this.computeStability();

    const state: AkashicState = {
      activeFrequency: mapping.frequency,
      frequencyName: mapping.name,
      resonanceStrength,
      harmonicPurity,
      attenuationCycle: this.attenuationCycle,
      convergence,
      stability,
      timestamp
    };

    // Store in history
    this.currentState = state;
    this.history.push(state);
    if (this.history.length > this.maxHistory) {
      this.history.shift();
    }

    // Send heartbeat to Temporal Ladder
    if (this.isRegistered) {
      temporalLadder.heartbeat(SYSTEMS.AKASHIC_MAPPER, stability);
    }

    return state;
  }

  /**
   * Compute stability from recent history
   */
  private computeStability(): number {
    if (this.history.length < 5) return 0.5;

    const recent = this.history.slice(-10);
    const avgConvergence = recent.reduce((sum, s) => sum + s.convergence, 0) / recent.length;
    const variance = recent.reduce((sum, s) => sum + Math.pow(s.convergence - avgConvergence, 2), 0) / recent.length;
    
    return Math.max(0, 1 - Math.sqrt(variance));
  }

  /**
   * Get current attenuation state
   */
  public getAttenuation(): AkashicAttenuation {
    const cyclePhase = this.attenuationCycle;
    const attenuationFactor = Math.cos(cyclePhase * Math.PI * 2) * 0.5 + 0.5;
    const boostMultiplier = 1 + attenuationFactor * 0.3;
    const isConverging = this.currentState ? this.currentState.convergence > 0.7 : false;

    return {
      cyclePhase,
      attenuationFactor,
      boostMultiplier,
      isConverging
    };
  }

  /**
   * Broadcast Akashic event to hive mind
   */
  public broadcastEvent(eventType: string, data?: any): void {
    if (this.isRegistered) {
      temporalLadder.broadcast(SYSTEMS.AKASHIC_MAPPER, eventType, {
        ...data,
        temporalId: this.temporalId,
        sentinelName: this.sentinelName
      });
    }
  }

  /**
   * Request assistance from another system
   */
  public requestAssistance(targetSystem: typeof SYSTEMS[keyof typeof SYSTEMS], reason: string): boolean {
    if (!this.isRegistered) return false;
    return temporalLadder.requestAssistance(SYSTEMS.AKASHIC_MAPPER, targetSystem, reason);
  }

  public getCurrentState(): AkashicState | null {
    return this.currentState;
  }

  public getHistory(): AkashicState[] {
    return [...this.history];
  }

  public getTemporalId(): string {
    return this.temporalId;
  }

  public getSentinelName(): string {
    return this.sentinelName;
  }
}

// Singleton instance
export const akashicMapper = new AkashicMapperBridge();
