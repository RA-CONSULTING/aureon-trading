/**
 * Dimensional Dialler - Prime Number Phase Locking System
 * Uses prime matrices for coherence stabilization
 * Schumann lattice provides hold and stability
 * Quantum entanglement through ping-pong resonance
 */

import { DimensionalDriftCorrector, type DriftDetection, type CorrectionStatus } from './dimensionalDriftCorrector';

export interface PrimeLock {
  prime: number;
  index: number;
  phase: number; // 0-2π
  coherence: number; // 0-1
  locked: boolean;
}

export interface SchumannLatticeNode {
  harmonicIndex: number; // 1-7
  frequency: number; // Hz
  amplitude: number;
  phaseOffset: number;
  stability: number; // 0-1
}

export interface QuantumEntanglement {
  nodeA: number;
  nodeB: number;
  entanglementStrength: number; // 0-1
  pingPongPhase: number; // 0-2π
  lastPing: number; // timestamp
  coherentState: boolean;
}

export interface DimensionalStability {
  overall: number; // 0-1
  primeAlignment: number;
  schumannHold: number;
  quantumCoherence: number;
  dimensionalIntegrity: number;
}

export interface DimensionalDiallerState {
  primeLocks: PrimeLock[];
  activePrime: number;
  schumannLattice: SchumannLatticeNode[];
  quantumEntanglements: QuantumEntanglement[];
  stability: DimensionalStability;
  dialPosition: number; // Current dimensional coordinate
  temporalSync: number; // 0-1
  timestamp: number;
  driftDetection: DriftDetection | null;
  correctionStatus: CorrectionStatus;
}

// First 20 prime numbers for phase locking
const PRIME_SEQUENCE = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71];

// Schumann resonance harmonics (Hz)
const SCHUMANN_HARMONICS = [7.83, 14.3, 20.8, 27.3, 33.8, 39.0, 45.0];

export class DimensionalDialler {
  private primeLocks: PrimeLock[] = [];
  private schumannLattice: SchumannLatticeNode[] = [];
  private quantumEntanglements: QuantumEntanglement[] = [];
  private dialPosition: number = 0;
  private history: DimensionalDiallerState[] = [];
  private maxHistory = 50;
  private driftCorrector: DimensionalDriftCorrector;
  private previousState: DimensionalDiallerState | null = null;
  private autoCorrectionEnabled = true;

  constructor() {
    this.initializePrimeLocks();
    this.initializeSchumannLattice();
    this.initializeQuantumEntanglements();
    this.driftCorrector = new DimensionalDriftCorrector();
  }

  public setAutoCorrection(enabled: boolean): void {
    this.autoCorrectionEnabled = enabled;
  }

  private initializePrimeLocks(): void {
    this.primeLocks = PRIME_SEQUENCE.map((prime, index) => ({
      prime,
      index,
      phase: (index * Math.PI / 10) % (2 * Math.PI),
      coherence: 0.5,
      locked: false
    }));
  }

  private initializeSchumannLattice(): void {
    this.schumannLattice = SCHUMANN_HARMONICS.map((freq, index) => ({
      harmonicIndex: index + 1,
      frequency: freq,
      amplitude: 1.0 / (index + 1), // Harmonics decay with order
      phaseOffset: (index * 2 * Math.PI / 7),
      stability: 0.7
    }));
  }

  private initializeQuantumEntanglements(): void {
    // Create entanglement pairs between adjacent primes
    this.quantumEntanglements = [];
    for (let i = 0; i < PRIME_SEQUENCE.length - 1; i++) {
      this.quantumEntanglements.push({
        nodeA: i,
        nodeB: i + 1,
        entanglementStrength: 0.5,
        pingPongPhase: 0,
        lastPing: Date.now(),
        coherentState: false
      });
    }
    
    // Add some non-adjacent entanglements for quantum complexity
    this.quantumEntanglements.push(
      { nodeA: 0, nodeB: 7, entanglementStrength: 0.6, pingPongPhase: 0, lastPing: Date.now(), coherentState: false },
      { nodeA: 3, nodeB: 11, entanglementStrength: 0.55, pingPongPhase: 0, lastPing: Date.now(), coherentState: false },
      { nodeA: 5, nodeB: 13, entanglementStrength: 0.58, pingPongPhase: 0, lastPing: Date.now(), coherentState: false }
    );
  }

  /**
   * Main dial update - processes coherence and generates dimensional stability
   */
  public dial(
    harmonicCoherence: number,
    schumannFrequency: number,
    observerConsciousness: number,
    timestamp: number
  ): DimensionalDiallerState {
    // Update prime locks based on harmonic coherence
    this.updatePrimeLocks(harmonicCoherence, timestamp);

    // Update Schumann lattice with incoming frequency
    this.updateSchumannLattice(schumannFrequency, harmonicCoherence);

    // Process quantum entanglement ping-pong
    this.processQuantumPingPong(observerConsciousness, timestamp);

    // Calculate dimensional stability
    const stability = this.calculateDimensionalStability();

    // Update dial position (dimensional coordinate)
    this.dialPosition = this.calculateDialPosition(harmonicCoherence, stability.overall);

    // Calculate temporal sync
    const temporalSync = this.calculateTemporalSync(timestamp);

    // Create initial state (before drift detection/correction)
    let state: DimensionalDiallerState = {
      primeLocks: [...this.primeLocks],
      activePrime: this.getActivePrime(),
      schumannLattice: [...this.schumannLattice],
      quantumEntanglements: [...this.quantumEntanglements],
      stability,
      dialPosition: this.dialPosition,
      temporalSync,
      timestamp,
      driftDetection: null,
      correctionStatus: this.driftCorrector.getCorrectionStatus()
    };

    // Detect drift
    const drift = this.driftCorrector.detectDrift(state, this.previousState);
    state.driftDetection = drift;

    // Auto-correct if enabled and drifting detected
    if (this.autoCorrectionEnabled && drift.isDrifting && !state.correctionStatus.isActive) {
      this.triggerAutoCorrection(state, drift);
    }

    this.previousState = state;
    this.history.push(state);
    if (this.history.length > this.maxHistory) {
      this.history.shift();
    }

    return state;
  }

  /**
   * Trigger automatic drift correction (non-blocking)
   */
  private async triggerAutoCorrection(state: DimensionalDiallerState, drift: DriftDetection): Promise<void> {
    try {
      const result = await this.driftCorrector.applyCorrection(state, drift);
      
      // Apply corrections
      this.primeLocks = result.primeLocks;
      this.schumannLattice = result.schumannLattice;
      
      console.log('🔧 Dimensional drift corrected:', result.correctionEvent.correctionType);
    } catch (error) {
      console.error('❌ Drift correction failed:', error);
    }
  }

  /**
   * Manually trigger correction
   */
  public async manualCorrection(): Promise<void> {
    if (!this.previousState) {
      throw new Error('No state available for correction');
    }

    const drift = this.driftCorrector.detectDrift(this.previousState, null);
    await this.triggerAutoCorrection(this.previousState, drift);
  }

  private updatePrimeLocks(coherence: number, timestamp: number): void {
    const t = timestamp / 1000;

    this.primeLocks.forEach((lock, index) => {
      // Phase evolution based on prime number
      const primeInfluence = Math.sin(t * lock.prime / 100);
      lock.phase = (lock.phase + primeInfluence * 0.01) % (2 * Math.PI);

      // Coherence influenced by system coherence and prime alignment
      const primeAlignment = Math.cos(lock.phase);
      lock.coherence = (coherence * 0.7 + (primeAlignment * 0.5 + 0.5) * 0.3);

      // Lock achieved when coherence > 0.8 and phase near 0 or π
      const phaseAlignment = Math.abs(Math.cos(lock.phase));
      lock.locked = lock.coherence > 0.8 && phaseAlignment > 0.9;
    });
  }

  private updateSchumannLattice(frequency: number, coherence: number): void {
    this.schumannLattice.forEach((node, index) => {
      // Calculate deviation from ideal Schumann harmonic
      const deviation = Math.abs(frequency - node.frequency) / node.frequency;
      
      // Stability increases when frequency matches harmonic
      node.stability = Math.max(0.3, 1 - deviation) * coherence;

      // Amplitude modulation based on stability
      const baseAmplitude = 1.0 / (node.harmonicIndex);
      node.amplitude = baseAmplitude * node.stability;

      // Phase offset evolves with time
      node.phaseOffset = (node.phaseOffset + 0.01) % (2 * Math.PI);
    });
  }

  private processQuantumPingPong(consciousness: number, timestamp: number): void {
    this.quantumEntanglements.forEach(entanglement => {
      const timeSinceLastPing = timestamp - entanglement.lastPing;
      const pingPongRate = 100; // ms between ping-pong

      if (timeSinceLastPing > pingPongRate) {
        // Ping-pong phase advances
        entanglement.pingPongPhase = (entanglement.pingPongPhase + Math.PI) % (2 * Math.PI);
        entanglement.lastPing = timestamp;

        // Entanglement strength influenced by both nodes' coherence
        const nodeACoherence = this.primeLocks[entanglement.nodeA]?.coherence || 0.5;
        const nodeBCoherence = this.primeLocks[entanglement.nodeB]?.coherence || 0.5;
        
        entanglement.entanglementStrength = (nodeACoherence + nodeBCoherence) / 2 * consciousness;

        // Coherent state achieved when both nodes locked and strong entanglement
        const nodeALocked = this.primeLocks[entanglement.nodeA]?.locked || false;
        const nodeBLocked = this.primeLocks[entanglement.nodeB]?.locked || false;
        entanglement.coherentState = 
          nodeALocked && nodeBLocked && entanglement.entanglementStrength > 0.75;
      }
    });
  }

  private calculateDimensionalStability(): DimensionalStability {
    // Prime alignment - how many primes are locked
    const lockedCount = this.primeLocks.filter(lock => lock.locked).length;
    const primeAlignment = lockedCount / this.primeLocks.length;

    // Average prime coherence
    const avgPrimeCoherence = this.primeLocks.reduce((sum, lock) => sum + lock.coherence, 0) / this.primeLocks.length;

    // Schumann hold - average lattice stability
    const schumannHold = this.schumannLattice.reduce((sum, node) => sum + node.stability, 0) / this.schumannLattice.length;

    // Quantum coherence - entangled pairs in coherent state
    const coherentPairs = this.quantumEntanglements.filter(e => e.coherentState).length;
    const quantumCoherence = coherentPairs / this.quantumEntanglements.length;

    // Average entanglement strength
    const avgEntanglement = this.quantumEntanglements.reduce((sum, e) => sum + e.entanglementStrength, 0) / this.quantumEntanglements.length;

    // Dimensional integrity - composite metric
    const dimensionalIntegrity = (
      primeAlignment * 0.3 +
      schumannHold * 0.25 +
      quantumCoherence * 0.25 +
      avgPrimeCoherence * 0.1 +
      avgEntanglement * 0.1
    );

    // Overall stability
    const overall = (
      primeAlignment * 0.25 +
      schumannHold * 0.25 +
      quantumCoherence * 0.25 +
      dimensionalIntegrity * 0.25
    );

    return {
      overall,
      primeAlignment,
      schumannHold,
      quantumCoherence,
      dimensionalIntegrity
    };
  }

  private calculateDialPosition(coherence: number, stability: number): number {
    // Dial position represents dimensional coordinate (0-360 degrees)
    const basePosition = coherence * 360;
    const stabilityModulation = stability * 30; // ±30 degrees based on stability
    return (basePosition + stabilityModulation) % 360;
  }

  private calculateTemporalSync(timestamp: number): number {
    // Temporal sync based on Fibonacci timing
    const t = (timestamp / 1000) % 60;
    const fibSequence = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55];
    
    let maxSync = 0;
    fibSequence.forEach(fib => {
      const distance = Math.abs(t - fib);
      if (distance < 1) {
        maxSync = Math.max(maxSync, 1 - distance);
      }
    });

    return maxSync;
  }

  private getActivePrime(): number {
    // Return the prime with highest coherence
    const maxLock = this.primeLocks.reduce((max, lock) => 
      lock.coherence > max.coherence ? lock : max
    );
    return maxLock.prime;
  }

  public getHistory(): DimensionalDiallerState[] {
    return [...this.history];
  }

  public getPrimeMatrix(): number[][] {
    // Generate 2D prime matrix for visualization
    const size = 5;
    const matrix: number[][] = [];
    
    for (let i = 0; i < size; i++) {
      matrix[i] = [];
      for (let j = 0; j < size; j++) {
        const index = i * size + j;
        if (index < this.primeLocks.length) {
          matrix[i][j] = this.primeLocks[index].coherence;
        } else {
          matrix[i][j] = 0;
        }
      }
    }
    
    return matrix;
  }

  public getSchumannStabilityWave(): number[] {
    // Generate composite Schumann wave
    const samples = 100;
    const wave: number[] = [];
    
    for (let i = 0; i < samples; i++) {
      const t = i / samples * 2 * Math.PI;
      let amplitude = 0;
      
      this.schumannLattice.forEach(node => {
        amplitude += node.amplitude * Math.sin(t * node.harmonicIndex + node.phaseOffset);
      });
      
      wave.push(amplitude / this.schumannLattice.length);
    }
    
    return wave;
  }
}
