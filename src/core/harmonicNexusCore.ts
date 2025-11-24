/**
 * Harmonic Nexus Core
 * Prime Sentinel: GARY LECKEY 02111991
 * 
 * Ensures coherence within the reality field substrate and maps the multiversial
 * identity with data feedback to the prime timeline.
 * 
 * Integrates:
 * - Ω(t) = Tr[Ψ × ℒ ⊗ O] tensor field
 * - Akashic frequency harmonics
 * - Temporal identity mapping
 * - Prime timeline synchronization
 * 
 * ANCHORED TO: Primelines Multiversal Temporal Identity System
 */

import type { OmegaState } from './omegaEquation';
import type { AkashicAttunement } from './akashicFrequencyMapper';
import type { LighthouseState } from './lighthouseConsensus';
import type { PrismOutput } from './prism';
import { getTemporalId, getSentinelName, PRIME_SENTINEL_IDENTITY } from './primelinesIdentity';

export interface HarmonicNexusState {
  // Temporal Identity
  temporalId: string;
  sentinelName: string;
  timestamp: Date;
  
  // Ω(t) Field Components
  omega: number;
  psi: number;
  love: number;
  observer: number;
  theta: number;
  unityProbability: number;
  
  // Akashic Harmonics
  akashicFrequency: number;
  akashicConvergence: number;
  akashicStability: number;
  akashicBoost: number;
  
  // Field Substrate Coherence
  substrateCoherence: number;
  fieldIntegrity: number;
  harmonicResonance: number;
  dimensionalAlignment: number;
  
  // Prime Timeline Sync
  syncStatus: 'synced' | 'syncing' | 'diverged' | 'correcting';
  syncQuality: number;
  timelineDivergence: number;
  
  // Lighthouse & Prism (optional)
  lighthouseSignal?: number;
  prismLevel?: number;
}

// Export HNCRegionTick type for external use
export interface HNCRegionTick {
  score: number;
  byBand: Record<string, number>;
  drivers: Array<{ label: string; weight: number }>;
}

export class HarmonicNexusCore {
  private temporalId: string;
  private sentinelName: string;
  private lastState: HarmonicNexusState | null = null;
  
  constructor(temporalId?: string, sentinelName?: string) {
    // Anchor to Primelines identity by default
    this.temporalId = temporalId || getTemporalId();
    this.sentinelName = sentinelName || getSentinelName();
    
    // Verify temporal anchor
    if (this.temporalId === getTemporalId()) {
      console.log('🎯 Harmonic Nexus anchored to Prime Sentinel timeline:', PRIME_SENTINEL_IDENTITY.compactId);
    }
  }
  
  /**
   * Compute the harmonic nexus state from all field components
   */
  computeNexusState(
    omegaState: OmegaState,
    akashicAttunement: AkashicAttunement | null,
    akashicBoost: number,
    lighthouse?: LighthouseState,
    prism?: PrismOutput
  ): HarmonicNexusState {
    // Calculate substrate coherence (unified field coherence)
    const substrateCoherence = this.calculateSubstrateCoherence(
      omegaState.love,
      omegaState.unity,
      akashicAttunement?.stabilityIndex || 0
    );
    
    // Calculate field integrity (how stable the field is)
    const fieldIntegrity = this.calculateFieldIntegrity(
      omegaState.theta,
      omegaState.coherence,
      akashicAttunement?.convergenceRate || 0
    );
    
    // Calculate harmonic resonance (alignment of all frequencies)
    const harmonicResonance = this.calculateHarmonicResonance(
      omegaState,
      akashicAttunement,
      akashicBoost
    );
    
    // Calculate dimensional alignment (how aligned we are with higher dimensions)
    const dimensionalAlignment = this.calculateDimensionalAlignment(
      omegaState.omega,
      omegaState.unity,
      harmonicResonance
    );
    
    // Determine sync status and quality
    const { syncStatus, syncQuality, timelineDivergence } = this.evaluateTimelineSync(
      substrateCoherence,
      fieldIntegrity,
      dimensionalAlignment
    );
    
    const state: HarmonicNexusState = {
      // Temporal Identity
      temporalId: this.temporalId,
      sentinelName: this.sentinelName,
      timestamp: new Date(),
      
      // Ω(t) Field Components
      omega: omegaState.omega,
      psi: omegaState.psi,
      love: omegaState.love,
      observer: omegaState.observer,
      theta: omegaState.theta,
      unityProbability: omegaState.unity,
      
      // Akashic Harmonics
      akashicFrequency: akashicAttunement?.finalFrequency || 0,
      akashicConvergence: akashicAttunement?.convergenceRate || 0,
      akashicStability: akashicAttunement?.stabilityIndex || 0,
      akashicBoost,
      
      // Field Substrate Coherence
      substrateCoherence,
      fieldIntegrity,
      harmonicResonance,
      dimensionalAlignment,
      
      // Prime Timeline Sync
      syncStatus,
      syncQuality,
      timelineDivergence,
      
      // Lighthouse & Prism
      lighthouseSignal: lighthouse?.L,
      prismLevel: prism?.level,
    };
    
    this.lastState = state;
    return state;
  }
  
  /**
   * Calculate substrate coherence (0-1)
   * Measures how unified the reality field substrate is
   */
  private calculateSubstrateCoherence(
    loveCoherence: number,
    unityProbability: number,
    akashicStability: number
  ): number {
    // Weighted average with emphasis on unity
    const coherence = (
      loveCoherence * 0.4 +
      unityProbability * 0.4 +
      akashicStability * 0.2
    );
    
    return Math.max(0, Math.min(1, coherence));
  }
  
  /**
   * Calculate field integrity (0-1)
   * Measures stability and resistance to perturbations
   */
  private calculateFieldIntegrity(
    theta: number,
    coherence: number,
    akashicConvergence: number
  ): number {
    // Low theta = high alignment, high coherence = high integrity
    const thetaContribution = 1 - theta;
    const integrity = (
      thetaContribution * 0.5 +
      coherence * 0.3 +
      akashicConvergence * 0.2
    );
    
    return Math.max(0, Math.min(1, integrity));
  }
  
  /**
   * Calculate harmonic resonance (0-1)
   * Measures alignment of all frequency components
   */
  private calculateHarmonicResonance(
    omegaState: OmegaState,
    akashicAttunement: AkashicAttunement | null,
    akashicBoost: number
  ): number {
    if (!akashicAttunement) return omegaState.coherence;
    
    // Check if akashic frequency is harmonically aligned with omega
    const akashicFreq = akashicAttunement.finalFrequency;
    const omegaFreq = omegaState.omega * 10; // Scale for comparison
    
    // Calculate harmonic ratio (should be close to integer or simple fraction)
    const ratio = akashicFreq / omegaFreq;
    const nearestInteger = Math.round(ratio);
    const harmonicDeviation = Math.abs(ratio - nearestInteger);
    const harmonicAlignment = Math.max(0, 1 - harmonicDeviation);
    
    // Combine with boost and coherence
    const resonance = (
      harmonicAlignment * 0.4 +
      akashicBoost * 0.3 +
      omegaState.coherence * 0.3
    );
    
    return Math.max(0, Math.min(1, resonance));
  }
  
  /**
   * Calculate dimensional alignment (0-1)
   * Measures alignment with higher dimensional reality
   */
  private calculateDimensionalAlignment(
    omega: number,
    unity: number,
    harmonicResonance: number
  ): number {
    // High omega + high unity + high resonance = high dimensional alignment
    const alignment = (
      Math.min(1, omega) * 0.4 +
      unity * 0.4 +
      harmonicResonance * 0.2
    );
    
    return Math.max(0, Math.min(1, alignment));
  }
  
  /**
   * Evaluate prime timeline synchronization
   */
  private evaluateTimelineSync(
    substrateCoherence: number,
    fieldIntegrity: number,
    dimensionalAlignment: number
  ): {
    syncStatus: 'synced' | 'syncing' | 'diverged' | 'correcting';
    syncQuality: number;
    timelineDivergence: number;
  } {
    // Calculate overall sync quality
    const syncQuality = (
      substrateCoherence * 0.4 +
      fieldIntegrity * 0.3 +
      dimensionalAlignment * 0.3
    );
    
    // Calculate timeline divergence (inverse of sync quality)
    const timelineDivergence = 1 - syncQuality;
    
    // Determine sync status
    let syncStatus: 'synced' | 'syncing' | 'diverged' | 'correcting';
    
    if (syncQuality >= 0.9) {
      syncStatus = 'synced';
    } else if (syncQuality >= 0.7) {
      // If previous state was diverged, we're correcting
      syncStatus = this.lastState && this.lastState.syncStatus === 'diverged' 
        ? 'correcting' 
        : 'syncing';
    } else if (syncQuality >= 0.5) {
      syncStatus = 'syncing';
    } else {
      syncStatus = 'diverged';
    }
    
    return { syncStatus, syncQuality, timelineDivergence };
  }
  
  /**
   * Get the current temporal identity
   */
  getTemporalIdentity(): { id: string; name: string } {
    return {
      id: this.temporalId,
      name: this.sentinelName
    };
  }
  
  /**
   * Update temporal identity
   */
  setTemporalIdentity(temporalId: string, sentinelName: string): void {
    this.temporalId = temporalId;
    this.sentinelName = sentinelName;
  }
  
  /**
   * Get last computed state
   */
  getLastState(): HarmonicNexusState | null {
    return this.lastState;
  }
}
