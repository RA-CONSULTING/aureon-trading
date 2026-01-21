/**
 * Dimensional Drift Corrector
 * Automated system for detecting and correcting dimensional instabilities
 * Applies prime lock recalibration and Schumann lattice reinforcement
 */

import type { DimensionalDiallerState, PrimeLock, SchumannLatticeNode } from './dimensionalDialler';

export interface CorrectionEvent {
  timestamp: number;
  triggerReason: string;
  preCorrection: {
    stability: number;
    primeAlignment: number;
    schumannHold: number;
    quantumCoherence: number;
  };
  postCorrection: {
    stability: number;
    primeAlignment: number;
    schumannHold: number;
    quantumCoherence: number;
  };
  correctionType: 'prime_recalibration' | 'schumann_reinforcement' | 'quantum_reset' | 'full_reset';
  duration: number;
  success: boolean;
}

export interface DriftDetection {
  isDrifting: boolean;
  driftMagnitude: number; // 0-1
  driftRate: number; // per second
  affectedSystems: ('prime' | 'schumann' | 'quantum')[];
  urgency: 'low' | 'medium' | 'high' | 'critical';
}

export interface CorrectionStatus {
  isActive: boolean;
  currentPhase: 'idle' | 'detecting' | 'analyzing' | 'correcting' | 'verifying' | 'complete';
  progress: number; // 0-1
  estimatedTimeRemaining: number; // ms
  lastCorrection: CorrectionEvent | null;
}

export class DimensionalDriftCorrector {
  private stabilityHistory: number[] = [];
  private maxHistory = 20;
  private correctionHistory: CorrectionEvent[] = [];
  private maxCorrectionHistory = 100;
  
  // Thresholds
  private readonly CRITICAL_THRESHOLD = 0.5;
  private readonly WARNING_THRESHOLD = 0.7;
  private readonly DRIFT_RATE_THRESHOLD = 0.05; // 5% per second
  
  // Correction state
  private correctionInProgress = false;
  private correctionStartTime = 0;
  private currentPhase: CorrectionStatus['currentPhase'] = 'idle';
  private correctionProgress = 0;
  
  constructor() {}

  /**
   * Detect dimensional drift from current state
   */
  public detectDrift(
    currentState: DimensionalDiallerState,
    previousState: DimensionalDiallerState | null
  ): DriftDetection {
    const { stability } = currentState;
    
    // Track stability history
    this.stabilityHistory.push(stability.overall);
    if (this.stabilityHistory.length > this.maxHistory) {
      this.stabilityHistory.shift();
    }

    // Calculate drift magnitude (how far from ideal)
    const driftMagnitude = 1 - stability.overall;

    // Calculate drift rate (how fast it's changing)
    let driftRate = 0;
    if (previousState && this.stabilityHistory.length >= 2) {
      const timeDelta = (currentState.timestamp - previousState.timestamp) / 1000; // seconds
      const stabilityDelta = previousState.stability.overall - currentState.stability.overall;
      driftRate = stabilityDelta / timeDelta;
    }

    // Identify affected systems
    const affectedSystems: ('prime' | 'schumann' | 'quantum')[] = [];
    if (stability.primeAlignment < this.WARNING_THRESHOLD) affectedSystems.push('prime');
    if (stability.schumannHold < this.WARNING_THRESHOLD) affectedSystems.push('schumann');
    if (stability.quantumCoherence < this.WARNING_THRESHOLD) affectedSystems.push('quantum');

    // Determine urgency
    let urgency: DriftDetection['urgency'] = 'low';
    if (stability.overall < this.CRITICAL_THRESHOLD || driftRate > this.DRIFT_RATE_THRESHOLD * 2) {
      urgency = 'critical';
    } else if (stability.overall < this.WARNING_THRESHOLD || driftRate > this.DRIFT_RATE_THRESHOLD) {
      urgency = 'high';
    } else if (affectedSystems.length > 1) {
      urgency = 'medium';
    }

    const isDrifting = stability.overall < this.WARNING_THRESHOLD || driftRate > this.DRIFT_RATE_THRESHOLD;

    return {
      isDrifting,
      driftMagnitude,
      driftRate,
      affectedSystems,
      urgency
    };
  }

  /**
   * Apply automated correction to restore dimensional stability
   */
  public async applyCorrection(
    currentState: DimensionalDiallerState,
    drift: DriftDetection
  ): Promise<{
    primeLocks: PrimeLock[];
    schumannLattice: SchumannLatticeNode[];
    correctionEvent: CorrectionEvent;
  }> {
    if (this.correctionInProgress) {
      throw new Error('Correction already in progress');
    }

    this.correctionInProgress = true;
    this.correctionStartTime = Date.now();
    this.currentPhase = 'analyzing';
    this.correctionProgress = 0;

    const preCorrection = {
      stability: currentState.stability.overall,
      primeAlignment: currentState.stability.primeAlignment,
      schumannHold: currentState.stability.schumannHold,
      quantumCoherence: currentState.stability.quantumCoherence
    };

    let correctionType: CorrectionEvent['correctionType'] = 'prime_recalibration';
    let correctedPrimeLocks = [...currentState.primeLocks];
    let correctedSchumannLattice = [...currentState.schumannLattice];

    try {
      // Phase 1: Analyze (10%)
      await this.simulatePhaseDelay(100);
      this.correctionProgress = 0.1;

      // Phase 2: Apply corrections based on urgency (60%)
      this.currentPhase = 'correcting';

      if (drift.urgency === 'critical' || drift.affectedSystems.length >= 3) {
        // Full system reset
        correctionType = 'full_reset';
        correctedPrimeLocks = this.fullPrimeReset(currentState.primeLocks);
        correctedSchumannLattice = this.fullSchumannReset(currentState.schumannLattice);
        await this.simulatePhaseDelay(300);
      } else if (drift.affectedSystems.includes('quantum')) {
        // Quantum entanglement reset
        correctionType = 'quantum_reset';
        correctedPrimeLocks = this.recalibratePrimeLocks(
          currentState.primeLocks,
          drift.affectedSystems.includes('prime')
        );
        await this.simulatePhaseDelay(200);
      } else if (drift.affectedSystems.includes('schumann')) {
        // Schumann lattice reinforcement
        correctionType = 'schumann_reinforcement';
        correctedSchumannLattice = this.reinforceSchumannLattice(currentState.schumannLattice);
        await this.simulatePhaseDelay(150);
      } else {
        // Prime lock recalibration (lightest correction)
        correctionType = 'prime_recalibration';
        correctedPrimeLocks = this.recalibratePrimeLocks(currentState.primeLocks, true);
        await this.simulatePhaseDelay(100);
      }

      this.correctionProgress = 0.7;

      // Phase 3: Verification (20%)
      this.currentPhase = 'verifying';
      await this.simulatePhaseDelay(100);
      this.correctionProgress = 0.9;

      // Phase 4: Complete (10%)
      this.currentPhase = 'complete';
      await this.simulatePhaseDelay(50);
      this.correctionProgress = 1.0;

      const duration = Date.now() - this.correctionStartTime;

      // Calculate post-correction metrics (estimated improvement)
      const postCorrection = {
        stability: Math.min(1, preCorrection.stability + 0.3),
        primeAlignment: this.calculatePrimeAlignment(correctedPrimeLocks),
        schumannHold: this.calculateSchumannHold(correctedSchumannLattice),
        quantumCoherence: Math.min(1, preCorrection.quantumCoherence + 0.2)
      };

      const correctionEvent: CorrectionEvent = {
        timestamp: Date.now(),
        triggerReason: this.generateTriggerReason(drift),
        preCorrection,
        postCorrection,
        correctionType,
        duration,
        success: postCorrection.stability > preCorrection.stability
      };

      this.correctionHistory.push(correctionEvent);
      if (this.correctionHistory.length > this.maxCorrectionHistory) {
        this.correctionHistory.shift();
      }

      return {
        primeLocks: correctedPrimeLocks,
        schumannLattice: correctedSchumannLattice,
        correctionEvent
      };
    } finally {
      this.correctionInProgress = false;
      this.currentPhase = 'idle';
      this.correctionProgress = 0;
    }
  }

  /**
   * Prime lock recalibration - adjusts phase and coherence
   */
  private recalibratePrimeLocks(primeLocks: PrimeLock[], aggressive: boolean): PrimeLock[] {
    return primeLocks.map(lock => {
      const recalibrationFactor = aggressive ? 0.8 : 0.5;
      
      // Reset phase toward optimal alignment (0 or π)
      const targetPhase = lock.phase < Math.PI ? 0 : Math.PI;
      const newPhase = lock.phase + (targetPhase - lock.phase) * recalibrationFactor;
      
      // Boost coherence
      const coherenceBoost = aggressive ? 0.3 : 0.2;
      const newCoherence = Math.min(1, lock.coherence + coherenceBoost);
      
      return {
        ...lock,
        phase: newPhase,
        coherence: newCoherence,
        locked: newCoherence > 0.8 && Math.abs(Math.cos(newPhase)) > 0.9
      };
    });
  }

  /**
   * Schumann lattice reinforcement - increases stability and amplitude
   */
  private reinforceSchumannLattice(lattice: SchumannLatticeNode[]): SchumannLatticeNode[] {
    return lattice.map(node => {
      // Boost stability
      const newStability = Math.min(1, node.stability + 0.3);
      
      // Increase amplitude based on harmonic order (lower harmonics get more boost)
      const amplitudeBoost = 0.3 / node.harmonicIndex;
      const newAmplitude = Math.min(1, node.amplitude + amplitudeBoost);
      
      // Align phase offset to ideal harmonic spacing
      const idealPhaseOffset = (node.harmonicIndex - 1) * 2 * Math.PI / 7;
      const newPhaseOffset = node.phaseOffset + (idealPhaseOffset - node.phaseOffset) * 0.5;
      
      return {
        ...node,
        stability: newStability,
        amplitude: newAmplitude,
        phaseOffset: newPhaseOffset
      };
    });
  }

  /**
   * Full prime reset - completely reinitialize all locks
   */
  private fullPrimeReset(primeLocks: PrimeLock[]): PrimeLock[] {
    return primeLocks.map((lock, index) => ({
      ...lock,
      phase: (index * Math.PI / 10) % (2 * Math.PI),
      coherence: 0.9,
      locked: true
    }));
  }

  /**
   * Full Schumann reset - reinitialize entire lattice
   */
  private fullSchumannReset(lattice: SchumannLatticeNode[]): SchumannLatticeNode[] {
    return lattice.map((node, index) => ({
      ...node,
      amplitude: 1.0 / (node.harmonicIndex),
      phaseOffset: (index * 2 * Math.PI / 7),
      stability: 0.95
    }));
  }

  private calculatePrimeAlignment(primeLocks: PrimeLock[]): number {
    const lockedCount = primeLocks.filter(lock => lock.locked).length;
    return lockedCount / primeLocks.length;
  }

  private calculateSchumannHold(lattice: SchumannLatticeNode[]): number {
    return lattice.reduce((sum, node) => sum + node.stability, 0) / lattice.length;
  }

  private generateTriggerReason(drift: DriftDetection): string {
    const reasons: string[] = [];
    if (drift.urgency === 'critical') reasons.push('Critical stability loss');
    if (drift.driftRate > this.DRIFT_RATE_THRESHOLD) reasons.push('Rapid drift detected');
    drift.affectedSystems.forEach(system => {
      reasons.push(`${system} system below threshold`);
    });
    return reasons.join(', ') || 'Preventive correction';
  }

  private simulatePhaseDelay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  public getCorrectionStatus(): CorrectionStatus {
    const estimatedTimeRemaining = this.correctionInProgress
      ? Math.max(0, 750 - (Date.now() - this.correctionStartTime))
      : 0;

    return {
      isActive: this.correctionInProgress,
      currentPhase: this.currentPhase,
      progress: this.correctionProgress,
      estimatedTimeRemaining,
      lastCorrection: this.correctionHistory[this.correctionHistory.length - 1] || null
    };
  }

  public getCorrectionHistory(): CorrectionEvent[] {
    return [...this.correctionHistory];
  }

  public getStabilityTrend(): { direction: 'improving' | 'stable' | 'degrading', confidence: number } {
    if (this.stabilityHistory.length < 5) {
      return { direction: 'stable', confidence: 0.5 };
    }

    const recent = this.stabilityHistory.slice(-5);
    const older = this.stabilityHistory.slice(-10, -5);
    
    const recentAvg = recent.reduce((a, b) => a + b) / recent.length;
    const olderAvg = older.length > 0 ? older.reduce((a, b) => a + b) / older.length : recentAvg;
    
    const delta = recentAvg - olderAvg;
    
    let direction: 'improving' | 'stable' | 'degrading';
    if (delta > 0.05) direction = 'improving';
    else if (delta < -0.05) direction = 'degrading';
    else direction = 'stable';
    
    const confidence = Math.min(1, Math.abs(delta) * 10);
    
    return { direction, confidence };
  }
}
