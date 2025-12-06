/**
 * Ecosystem Connector
 * Prime Sentinel: GARY LECKEY 02111991
 * 
 * Central integration hub that wires ALL isolated systems into the unified ecosystem.
 * Every system feeds into the UnifiedBus and registers with Temporal Ladder.
 * JSONs become ENHANCEMENTS that modify behavior, not isolated data.
 */

import { unifiedBus, type SignalType } from './unifiedBus';
import { temporalLadder, SYSTEMS, type SystemName } from './temporalLadder';
import { HarmonicNexusCore, type HarmonicNexusState } from './harmonicNexusCore';
import { OmegaEquation, type OmegaState } from './omegaEquation';
import { QGITAEngine, type LighthouseEvent } from './qgitaEngine';
import { ecosystemEnhancements } from './ecosystemEnhancements';
import type { MarketSnapshot } from './aurisNodes';
import type { LambdaState } from './masterEquation';
import type { AkashicAttunement } from './akashicFrequencyMapper';
import type { LighthouseState } from './lighthouseConsensus';
import type { PrismOutput } from './thePrism';
// Note: Using thePrism.ts (5-level engine with full layers) not prism.ts (simple version)

// Extended system names for new systems
export type ExtendedSystemName = SystemName | 'qgita-engine' | 'eckoushic-cascade' | 'unity-detector' | 'fibonacci-lattice';

export interface EckoushicCascadeState {
  echoResonance: number;
  cascadeDepth: number;
  memoryStrength: number;
  harmonicFeedback: number;
}

export interface UnityDetectorState {
  isUnityDetected: boolean;
  unityStrength: number;
  phaseAlignment: number;
  frequencyLock: boolean;
}

export interface FibonacciLatticeState {
  currentLevel: number;
  ratioAlignment: number;
  spiralPhase: number;
  nextAnchor: Date;
}

export interface EcosystemState {
  // Core systems
  harmonicNexus: HarmonicNexusState | null;
  omega: OmegaState | null;
  qgita: LighthouseEvent | null;
  
  // Enhancement systems
  eckoushic: EckoushicCascadeState | null;
  unity: UnityDetectorState | null;
  fibonacci: FibonacciLatticeState | null;
  
  // Status
  totalSystems: number;
  activeSystems: number;
  enhancementsLoaded: boolean;
  lastUpdate: number;
}

class EcosystemConnectorCore {
  // Core systems
  private harmonicNexusCore: HarmonicNexusCore;
  private omegaEquation: OmegaEquation;
  private qgitaEngine: QGITAEngine;
  
  // State
  private eckoushicState: EckoushicCascadeState | null = null;
  private unityState: UnityDetectorState | null = null;
  private fibonacciState: FibonacciLatticeState | null = null;
  private harmonicNexusState: HarmonicNexusState | null = null;
  private omegaState: OmegaState | null = null;
  private qgitaState: LighthouseEvent | null = null;
  
  private isInitialized = false;
  private heartbeatInterval: number | null = null;
  private listeners: Set<(state: EcosystemState) => void> = new Set();

  constructor() {
    this.harmonicNexusCore = new HarmonicNexusCore();
    this.omegaEquation = new OmegaEquation();
    this.qgitaEngine = new QGITAEngine();
  }

  /**
   * Initialize the ecosystem connector
   */
  async initialize(): Promise<void> {
    if (this.isInitialized) return;

    console.log('🌐 Ecosystem Connector: Initializing all systems...');

    // Load JSON enhancements
    await ecosystemEnhancements.loadAll();

    // Register all systems with Temporal Ladder
    this.registerAllSystems();

    // Start heartbeat broadcasting
    this.startHeartbeat();

    this.isInitialized = true;
    console.log('🌐 Ecosystem Connector: All systems initialized and connected');
  }

  /**
   * Register all systems with Temporal Ladder
   */
  private registerAllSystems(): void {
    // Register extended systems
    temporalLadder.registerSystem(SYSTEMS.HARMONIC_NEXUS);
    temporalLadder.registerSystem(SYSTEMS.MASTER_EQUATION);
    temporalLadder.registerSystem(SYSTEMS.AKASHIC_MAPPER);
    temporalLadder.registerSystem(SYSTEMS.ZERO_POINT);
    temporalLadder.registerSystem(SYSTEMS.DIMENSIONAL_DIALLER);
    
    console.log('✅ All systems registered with Temporal Ladder');
  }

  /**
   * Start heartbeat broadcasting to Temporal Ladder
   */
  private startHeartbeat(): void {
    if (this.heartbeatInterval) return;

    this.heartbeatInterval = window.setInterval(() => {
      this.sendHeartbeats();
      this.notifyListeners();
    }, 2000);
  }

  /**
   * Send heartbeats from all integrated systems
   */
  private sendHeartbeats(): void {
    // Harmonic Nexus heartbeat
    if (this.harmonicNexusState) {
      temporalLadder.heartbeat(SYSTEMS.HARMONIC_NEXUS, this.harmonicNexusState.substrateCoherence);
    }

    // Omega heartbeat via Master Equation
    if (this.omegaState) {
      temporalLadder.heartbeat(SYSTEMS.MASTER_EQUATION, this.omegaState.coherence);
    }
  }

  /**
   * Run a complete ecosystem cycle
   * Called by UnifiedOrchestrator to integrate all systems
   */
  runCycle(
    marketSnapshot: MarketSnapshot,
    lambdaState: LambdaState,
    akashicAttunement: AkashicAttunement | null,
    akashicBoost: number,
    lighthouseState?: LighthouseState,
    prismOutput?: PrismOutput
  ): EcosystemState {
    
    // 1. Compute Omega Equation (enhanced field state)
    this.omegaState = this.omegaEquation.step(marketSnapshot);
    this.publishOmega(this.omegaState);

    // 2. Compute Harmonic Nexus Core
    this.harmonicNexusState = this.harmonicNexusCore.computeNexusState(
      this.omegaState,
      akashicAttunement,
      akashicBoost,
      lighthouseState,
      prismOutput
    );
    this.publishHarmonicNexus(this.harmonicNexusState);

    // 3. Compute Eckoushic Cascade (enhances Echo term)
    this.eckoushicState = this.computeEckoushicCascade(
      lambdaState.echo,
      marketSnapshot.momentum,
      this.omegaState.observer
    );
    this.publishEckoushic(this.eckoushicState);

    // 4. Compute Unity Detector (feeds into Prism Level 5)
    this.unityState = this.detectUnity(
      lambdaState.coherence,
      this.harmonicNexusState.harmonicResonance,
      prismOutput?.frequency || 0
    );
    this.publishUnity(this.unityState);

    // 5. Compute Fibonacci Lattice
    this.fibonacciState = this.computeFibonacciLattice(
      this.omegaState.fibonacciLevel,
      this.omegaState.spiralPhase,
      this.omegaState.nextFibonacciAnchor
    );
    this.publishFibonacci(this.fibonacciState);

    // Return complete ecosystem state
    return this.getState();
  }

  /**
   * Compute Eckoushic Cascade - enhances Echo/Memory
   */
  private computeEckoushicCascade(
    echo: number,
    momentum: number,
    observer: number
  ): EckoushicCascadeState {
    // Cascade depth based on echo strength
    const cascadeDepth = Math.min(5, Math.floor(Math.abs(echo) * 5));
    
    // Resonance between echo and momentum
    const echoResonance = 1 - Math.abs(echo - momentum);
    
    // Memory strength from observer consciousness
    const memoryStrength = observer * (1 + echo * 0.3);
    
    // Harmonic feedback loop
    const harmonicFeedback = (echoResonance + memoryStrength) / 2;

    return {
      echoResonance: Math.max(0, Math.min(1, echoResonance)),
      cascadeDepth,
      memoryStrength: Math.max(0, Math.min(1, memoryStrength)),
      harmonicFeedback: Math.max(0, Math.min(1, harmonicFeedback)),
    };
  }

  /**
   * Detect Unity events - triggers Prism 528 Hz lock
   */
  private detectUnity(
    coherence: number,
    harmonicResonance: number,
    prismFrequency: number
  ): UnityDetectorState {
    // Phase alignment based on coherence and resonance
    const phaseAlignment = (coherence + harmonicResonance) / 2;
    
    // Frequency lock when close to 528 Hz
    const frequencyLock = Math.abs(prismFrequency - 528) < 20;
    
    // Unity strength
    const unityStrength = phaseAlignment * (frequencyLock ? 1.2 : 0.8);
    
    // Unity detected when all conditions align
    const isUnityDetected = coherence > 0.9 && harmonicResonance > 0.85 && frequencyLock;

    return {
      isUnityDetected,
      unityStrength: Math.max(0, Math.min(1, unityStrength)),
      phaseAlignment,
      frequencyLock,
    };
  }

  /**
   * Compute Fibonacci Lattice state
   */
  private computeFibonacciLattice(
    level: number,
    spiralPhase: number,
    nextAnchor: Date
  ): FibonacciLatticeState {
    // Calculate ratio alignment (how close to golden ratio)
    const PHI = 1.618033988749895;
    const ratioAlignment = 1 - Math.abs((spiralPhase / PHI) - Math.round(spiralPhase / PHI));

    return {
      currentLevel: level,
      ratioAlignment,
      spiralPhase,
      nextAnchor,
    };
  }

  /**
   * Publish Omega state to bus
   */
  private publishOmega(state: OmegaState): void {
    let signal: SignalType = 'NEUTRAL';
    if (state.omega > 0.6 && state.unity > 0.7) {
      signal = 'BUY';
    } else if (state.omega < 0.4 && state.unity < 0.3) {
      signal = 'SELL';
    }

    unifiedBus.publish({
      systemName: 'OmegaEquation',
      timestamp: Date.now(),
      ready: true,
      coherence: state.coherence,
      confidence: state.unity,
      signal,
      data: {
        omega: state.omega,
        psi: state.psi,
        love: state.love,
        observer: state.observer,
        theta: state.theta,
        unity: state.unity,
      },
    });
  }

  /**
   * Publish Harmonic Nexus state to bus
   */
  private publishHarmonicNexus(state: HarmonicNexusState): void {
    let signal: SignalType = 'NEUTRAL';
    if (state.syncStatus === 'synced' && state.substrateCoherence > 0.8) {
      signal = 'BUY';
    } else if (state.syncStatus === 'diverged') {
      signal = 'SELL';
    }

    unifiedBus.publish({
      systemName: 'HarmonicNexus',
      timestamp: Date.now(),
      ready: true,
      coherence: state.substrateCoherence,
      confidence: state.syncQuality,
      signal,
      data: {
        omega: state.omega,
        harmonicResonance: state.harmonicResonance,
        dimensionalAlignment: state.dimensionalAlignment,
        syncStatus: state.syncStatus,
        akashicBoost: state.akashicBoost,
      },
    });
  }

  /**
   * Publish Eckoushic state to bus
   */
  private publishEckoushic(state: EckoushicCascadeState): void {
    unifiedBus.publish({
      systemName: 'EckoushicCascade',
      timestamp: Date.now(),
      ready: true,
      coherence: state.echoResonance,
      confidence: state.harmonicFeedback,
      signal: 'NEUTRAL',
      data: {
        cascadeDepth: state.cascadeDepth,
        memoryStrength: state.memoryStrength,
      },
    });
  }

  /**
   * Publish Unity state to bus
   */
  private publishUnity(state: UnityDetectorState): void {
    let signal: SignalType = 'NEUTRAL';
    if (state.isUnityDetected) {
      signal = 'BUY'; // Unity = positive signal
    }

    unifiedBus.publish({
      systemName: 'UnityDetector',
      timestamp: Date.now(),
      ready: true,
      coherence: state.phaseAlignment,
      confidence: state.unityStrength,
      signal,
      data: {
        isUnityDetected: state.isUnityDetected,
        frequencyLock: state.frequencyLock,
      },
    });
  }

  /**
   * Publish Fibonacci state to bus
   */
  private publishFibonacci(state: FibonacciLatticeState): void {
    unifiedBus.publish({
      systemName: 'FibonacciLattice',
      timestamp: Date.now(),
      ready: true,
      coherence: state.ratioAlignment,
      confidence: state.ratioAlignment,
      signal: 'NEUTRAL',
      data: {
        level: state.currentLevel,
        spiralPhase: state.spiralPhase,
        nextAnchor: state.nextAnchor.toISOString(),
      },
    });
  }

  /**
   * Get current ecosystem state
   */
  getState(): EcosystemState {
    const ladderState = temporalLadder.getState();
    let activeSystems = 0;
    ladderState.systems.forEach(s => { if (s.active) activeSystems++; });

    return {
      harmonicNexus: this.harmonicNexusState,
      omega: this.omegaState,
      qgita: this.qgitaState,
      eckoushic: this.eckoushicState,
      unity: this.unityState,
      fibonacci: this.fibonacciState,
      totalSystems: 11, // All quantum systems
      activeSystems,
      enhancementsLoaded: ecosystemEnhancements.isLoaded(),
      lastUpdate: Date.now(),
    };
  }

  /**
   * Subscribe to ecosystem state updates
   */
  subscribe(callback: (state: EcosystemState) => void): () => void {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }

  private notifyListeners(): void {
    const state = this.getState();
    this.listeners.forEach(cb => cb(state));
  }

  /**
   * Get enhancement boost for a system
   */
  getEnhancementBoost(systemName: string, value: number): number {
    if (!ecosystemEnhancements.isLoaded()) return value;
    
    switch (systemName) {
      case 'Auris':
        return ecosystemEnhancements.applyAurisBoost(systemName, value);
      default:
        return value;
    }
  }

  /**
   * Cleanup
   */
  destroy(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
    this.listeners.clear();
    this.isInitialized = false;
  }
}

// Singleton instance
export const ecosystemConnector = new EcosystemConnectorCore();
