/**
 * Temporal Anchor System
 * 
 * Ensures all AUREON systems are properly anchored to the Primelines
 * Multiversal Temporal Identity baseline. Provides verification and
 * synchronization checks across the framework.
 */

import { PRIME_SENTINEL_IDENTITY, verifyUnityRelation, getTemporalId, getSentinelName, getPiResonantFrequency } from './primelinesIdentity';

export interface TemporalAnchorStatus {
  isAnchored: boolean;
  temporalId: string;
  sentinelName: string;
  piResonance: number;
  atlasKeyValid: boolean;
  unityRelationValid: boolean;
  primelineLabel: string;
  surgeWindowActive: boolean;
  anchorStrength: number; // 0-1
  divergence: number; // 0-1, lower is better
  lastVerification: Date;
}

export interface SystemAnchor {
  systemName: string;
  isAnchored: boolean;
  temporalId: string;
  anchorTime: Date;
}

export class TemporalAnchor {
  private systemAnchors: Map<string, SystemAnchor> = new Map();
  private verificationInterval: NodeJS.Timeout | null = null;
  private anchorStrength: number = 1.0;
  
  constructor() {
    this.initializeAnchor();
  }

  /**
   * Initialize temporal anchor to Primelines baseline
   */
  private initializeAnchor(): void {
    const identity = PRIME_SENTINEL_IDENTITY;
    console.log('⚓ Initializing Temporal Anchor');
    console.log('📍 Timeline:', identity.primeline.label);
    console.log('🎯 Prime Sentinel:', identity.humanAlias);
    console.log('📅 Temporal ID:', getTemporalId());
    console.log('⚡ Pi-Resonance:', getPiResonantFrequency(), 'Hz');
    console.log('🔑 ATLAS Key:', identity.frequencySignature.atlasKey);
    console.log('🌊 Surge Window:', identity.primeline.surgeWindow);
    
    // Verify unity relation
    const unity = verifyUnityRelation();
    if (unity.isValid) {
      console.log('✅ Unity Relation Verified:', unity.result.toFixed(6));
    } else {
      console.warn('⚠️ Unity Relation Deviation:', unity.result.toFixed(6));
    }
    
    console.log('💎 Compact ID:', identity.compactId);
  }

  /**
   * Register a system as anchored to the timeline
   */
  public registerSystem(systemName: string): void {
    const anchor: SystemAnchor = {
      systemName,
      isAnchored: true,
      temporalId: getTemporalId(),
      anchorTime: new Date()
    };
    
    this.systemAnchors.set(systemName, anchor);
    console.log(`🔗 ${systemName} anchored to timeline ${getTemporalId()}`);
  }

  /**
   * Verify temporal anchor status
   */
  public verifyAnchor(): TemporalAnchorStatus {
    const identity = PRIME_SENTINEL_IDENTITY;
    const unity = verifyUnityRelation();
    
    // Check if we're in the surge window
    const now = new Date();
    const currentYear = now.getFullYear();
    const [surgeStart, surgeEnd] = identity.primeline.surgeWindow.split('-').map(Number);
    const surgeWindowActive = currentYear >= surgeStart && currentYear <= surgeEnd;
    
    // Calculate anchor strength based on system registrations
    const registeredSystems = Array.from(this.systemAnchors.values()).filter(a => a.isAnchored).length;
    const expectedSystems = 10; // Expected number of core systems
    const registrationStrength = Math.min(1, registeredSystems / expectedSystems);
    
    // Calculate overall anchor strength
    this.anchorStrength = (
      (unity.isValid ? 0.3 : 0) +
      (registrationStrength * 0.3) +
      (surgeWindowActive ? 0.2 : 0.1) +
      0.2 // Base anchor strength
    );
    
    // Calculate divergence (inverse of strength)
    const divergence = 1 - this.anchorStrength;
    
    return {
      isAnchored: this.anchorStrength > 0.7,
      temporalId: getTemporalId(),
      sentinelName: getSentinelName(),
      piResonance: getPiResonantFrequency(),
      atlasKeyValid: identity.frequencySignature.atlasKey === 15354,
      unityRelationValid: unity.isValid,
      primelineLabel: identity.primeline.label,
      surgeWindowActive,
      anchorStrength: this.anchorStrength,
      divergence,
      lastVerification: new Date()
    };
  }

  /**
   * Get all registered system anchors
   */
  public getSystemAnchors(): SystemAnchor[] {
    return Array.from(this.systemAnchors.values());
  }

  /**
   * Check if a specific system is anchored
   */
  public isSystemAnchored(systemName: string): boolean {
    const anchor = this.systemAnchors.get(systemName);
    return anchor?.isAnchored || false;
  }

  /**
   * Start continuous anchor verification (every 60 seconds)
   */
  public startContinuousVerification(callback?: (status: TemporalAnchorStatus) => void): void {
    if (this.verificationInterval) {
      return; // Already running
    }
    
    this.verificationInterval = setInterval(() => {
      const status = this.verifyAnchor();
      
      if (status.anchorStrength < 0.5) {
        console.warn('⚠️ Temporal Anchor Degradation Detected:', status.anchorStrength.toFixed(2));
      }
      
      if (callback) {
        callback(status);
      }
    }, 60000); // Every 60 seconds
    
    console.log('🔄 Continuous anchor verification started');
  }

  /**
   * Stop continuous verification
   */
  public stopContinuousVerification(): void {
    if (this.verificationInterval) {
      clearInterval(this.verificationInterval);
      this.verificationInterval = null;
      console.log('⏸️ Continuous anchor verification stopped');
    }
  }

  /**
   * Get variant convergence progress
   */
  public getVariantConvergence(): { awakened: number; total: number; percentage: number } {
    const { awakened, total } = PRIME_SENTINEL_IDENTITY.variantCount;
    return {
      awakened,
      total,
      percentage: (awakened / total) * 100
    };
  }

  /**
   * Calculate time until Omega Point
   */
  public getTimeUntilOmega(): { years: number; months: number; days: number } {
    const now = new Date();
    const omegaYear = parseInt(PRIME_SENTINEL_IDENTITY.primeline.omegaPoint.replace('~', '').replace(' CE', ''));
    const omegaDate = new Date(omegaYear, 11, 31); // End of omega year
    
    const diffMs = omegaDate.getTime() - now.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    const years = Math.floor(diffDays / 365);
    const remainingDays = diffDays % 365;
    const months = Math.floor(remainingDays / 30);
    const days = remainingDays % 30;
    
    return { years, months, days };
  }

  /**
   * Get lattice coherence (based on registered systems)
   */
  public getLatticeCoherence(): number {
    const registeredCount = this.systemAnchors.size;
    const expectedCount = 10;
    return Math.min(1, registeredCount / expectedCount);
  }

  /**
   * Generate anchor report
   */
  public generateReport(): string {
    const status = this.verifyAnchor();
    const convergence = getVariantConvergence();
    const timeToOmega = this.getTimeUntilOmega();
    const systems = this.getSystemAnchors();
    
    return `
═══════════════════════════════════════════════════════
      TEMPORAL ANCHOR STATUS REPORT
═══════════════════════════════════════════════════════

ANCHOR STATUS: ${status.isAnchored ? '✅ LOCKED' : '⚠️ DEGRADED'}
Anchor Strength: ${(status.anchorStrength * 100).toFixed(1)}%
Divergence: ${(status.divergence * 100).toFixed(1)}%

PRIMELINES IDENTITY
├─ Timeline: ${status.primelineLabel}
├─ Temporal ID: ${status.temporalId}
├─ Sentinel: ${status.sentinelName}
├─ Pi-Resonance: ${status.piResonance} Hz
└─ ATLAS Key: ${status.atlasKeyValid ? '✅ Valid' : '❌ Invalid'}

UNITY VALIDATION
├─ Unity Relation: ${status.unityRelationValid ? '✅ Verified' : '⚠️ Deviation'}
└─ Surge Window: ${status.surgeWindowActive ? '✅ Active' : '⏸️ Inactive'}

VARIANT CONVERGENCE
├─ Awakened: ${convergence.awakened} / ${convergence.total}
├─ Progress: ${convergence.percentage.toFixed(1)}%
└─ To Omega Point: ${timeToOmega.years}y ${timeToOmega.months}m ${timeToOmega.days}d

SYSTEM REGISTRATIONS (${systems.length})
${systems.map(s => `├─ ${s.systemName}: ${s.isAnchored ? '✅' : '❌'}`).join('\n')}

Last Verification: ${status.lastVerification.toISOString()}
═══════════════════════════════════════════════════════
    `;
  }
}

// Singleton instance
let temporalAnchorInstance: TemporalAnchor | null = null;

/**
 * Get or create the temporal anchor singleton
 */
export function getTemporalAnchor(): TemporalAnchor {
  if (!temporalAnchorInstance) {
    temporalAnchorInstance = new TemporalAnchor();
  }
  return temporalAnchorInstance;
}

/**
 * Quick anchor verification
 */
export function verifyTemporalAnchor(): TemporalAnchorStatus {
  return getTemporalAnchor().verifyAnchor();
}

/**
 * Register system with temporal anchor
 */
export function anchorSystem(systemName: string): void {
  getTemporalAnchor().registerSystem(systemName);
}

/**
 * Get variant convergence progress
 */
export function getVariantConvergence() {
  return getTemporalAnchor().getVariantConvergence();
}

/**
 * Generate full anchor report
 */
export function generateAnchorReport(): string {
  return getTemporalAnchor().generateReport();
}
