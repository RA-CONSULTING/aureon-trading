// Earth Field Validation - Implements formulas from auris_codex.json
import type { SchumannFeatures, LatticeTimeseries, AurisCodexConfig } from './earth-data-loader';

export interface ValidationResult {
  fieldAlignment: number;       // 0-1, phase coherence across channels
  harmonicCoherence: number;    // 0-1, multi-band coherence index
  resonanceStability: number;   // 0-1, frequency deviation tracking
  phaseLockStrength: number;    // 0-1, complex phase lock index
  overallScore: number;         // 0-1, weighted average
  isValid: boolean;             // Passes all thresholds
  timestamp: Date;
}

export interface ValidationThresholds {
  fieldAlignment: number;
  harmonicCoherence: number;
  resonanceStability: number;
  phaseLockStrength: number;
}

const DEFAULT_THRESHOLDS: ValidationThresholds = {
  fieldAlignment: 0.75,
  harmonicCoherence: 0.6,
  resonanceStability: 0.95,
  phaseLockStrength: 0.8
};

export class EarthValidation {
  private thresholds: ValidationThresholds;
  private codex: AurisCodexConfig | null = null;
  private phaseHistory: number[][] = [];
  private frequencyHistory: number[] = [];
  
  constructor(thresholds: Partial<ValidationThresholds> = {}) {
    this.thresholds = { ...DEFAULT_THRESHOLDS, ...thresholds };
  }
  
  setCodex(codex: AurisCodexConfig): void {
    this.codex = codex;
    // Update thresholds from codex if available
    if (codex.live_validation_metrics) {
      if (codex.live_validation_metrics.field_alignment) {
        this.thresholds.fieldAlignment = codex.live_validation_metrics.field_alignment.threshold;
      }
      if (codex.live_validation_metrics.harmonic_coherence) {
        this.thresholds.harmonicCoherence = codex.live_validation_metrics.harmonic_coherence.threshold;
      }
      if (codex.live_validation_metrics.resonance_stability) {
        this.thresholds.resonanceStability = codex.live_validation_metrics.resonance_stability.threshold;
      }
      if (codex.live_validation_metrics.phase_lock_strength) {
        this.thresholds.phaseLockStrength = codex.live_validation_metrics.phase_lock_strength.threshold;
      }
    }
  }
  
  /**
   * Field Alignment: sum(cos(phase_diff[i,j])) / n_pairs
   * Measures phase coherence across all Schumann mode pairs
   */
  calculateFieldAlignment(schumann: SchumannFeatures): number {
    const phases = [
      schumann.P7_83,
      schumann.P14_3,
      schumann.P20_8,
      schumann.P27_3,
      schumann.P33_8
    ];
    
    let sumCos = 0;
    let nPairs = 0;
    
    for (let i = 0; i < phases.length; i++) {
      for (let j = i + 1; j < phases.length; j++) {
        const phaseDiff = phases[i] - phases[j];
        sumCos += Math.cos(phaseDiff);
        nPairs++;
      }
    }
    
    // Normalize to 0-1 range (cos ranges from -1 to 1)
    return nPairs > 0 ? (sumCos / nPairs + 1) / 2 : 0;
  }
  
  /**
   * Harmonic Coherence: sqrt(sum(coherence[band]²) / n_bands)
   * RMS of coherence across all frequency bands
   */
  calculateHarmonicCoherence(schumann: SchumannFeatures): number {
    // Use envelopes as proxy for per-band coherence
    const bandCoherences = [
      schumann.envelope_7_83 / schumann.A7_83,
      schumann.envelope_14_3 / schumann.A14_3,
      schumann.envelope_20_8 / schumann.A20_8,
      schumann.envelope_27_3 / schumann.A27_3,
      schumann.envelope_33_8 / schumann.A33_8
    ].filter(v => isFinite(v) && !isNaN(v));
    
    if (bandCoherences.length === 0) return schumann.coherence_idx;
    
    const sumSquares = bandCoherences.reduce((sum, c) => sum + c * c, 0);
    const rms = Math.sqrt(sumSquares / bandCoherences.length);
    
    // Blend with direct coherence index
    return (rms * 0.5 + schumann.coherence_idx * 0.5);
  }
  
  /**
   * Resonance Stability: 1 - std(freq_deviation) / center_freq
   * Measures how stable the fundamental frequency is over time
   */
  calculateResonanceStability(schumannHistory: SchumannFeatures[]): number {
    if (schumannHistory.length < 2) return 0.95;
    
    const centerFreq = 7.83; // Schumann fundamental
    
    // Extract frequency deviations (using amplitude ratios as proxy)
    const deviations = schumannHistory.map(s => {
      // Higher order modes should maintain harmonic ratios
      const expectedRatio2 = 14.3 / 7.83;
      const actualRatio2 = s.A14_3 / s.A7_83;
      return Math.abs(actualRatio2 - expectedRatio2);
    });
    
    const mean = deviations.reduce((a, b) => a + b, 0) / deviations.length;
    const variance = deviations.reduce((sum, d) => sum + (d - mean) ** 2, 0) / deviations.length;
    const std = Math.sqrt(variance);
    
    // Normalize to 0-1 range
    return Math.max(0, Math.min(1, 1 - std / centerFreq));
  }
  
  /**
   * Phase Lock Strength: abs(mean(exp(i*phase_diff)))
   * Measures circular mean of phase differences (complex magnitude)
   */
  calculatePhaseLockStrength(schumann: SchumannFeatures): number {
    const phases = [
      schumann.P7_83,
      schumann.P14_3,
      schumann.P20_8,
      schumann.P27_3,
      schumann.P33_8
    ];
    
    // Track phase history for temporal phase locking
    this.phaseHistory.push(phases);
    if (this.phaseHistory.length > 60) {
      this.phaseHistory.shift();
    }
    
    // Calculate instantaneous phase lock
    let sumReal = 0;
    let sumImag = 0;
    
    for (let i = 0; i < phases.length - 1; i++) {
      const phaseDiff = phases[i + 1] - phases[i];
      sumReal += Math.cos(phaseDiff);
      sumImag += Math.sin(phaseDiff);
    }
    
    const n = phases.length - 1;
    const magnitude = Math.sqrt((sumReal / n) ** 2 + (sumImag / n) ** 2);
    
    return magnitude;
  }
  
  /**
   * Validate lattice raw sensor data quality
   */
  validateLatticeData(lattice: LatticeTimeseries): {
    electricFieldValid: boolean;
    magneticFieldValid: boolean;
    qualityFactor: number;
  } {
    // Check electric field components
    const electricMagnitude = Math.sqrt(lattice.Ex ** 2 + lattice.Ey ** 2);
    const electricFieldValid = electricMagnitude > 0.0001 && electricMagnitude < 1.0;
    
    // Check magnetic field components
    const magneticMagnitude = Math.sqrt(lattice.Bx ** 2 + lattice.By ** 2 + lattice.Bz ** 2);
    const magneticFieldValid = magneticMagnitude > 1 && magneticMagnitude < 100;
    
    // Quality factor from raw data
    const qualityFactor = lattice.qf === 0 ? 1.0 : 
      lattice.qf < 3 ? 0.8 : 
      lattice.qf < 5 ? 0.5 : 0.2;
    
    return {
      electricFieldValid,
      magneticFieldValid,
      qualityFactor: qualityFactor * lattice.gain
    };
  }
  
  /**
   * Full validation run
   */
  validate(
    currentSchumann: SchumannFeatures,
    schumannHistory: SchumannFeatures[],
    currentLattice?: LatticeTimeseries
  ): ValidationResult {
    const fieldAlignment = this.calculateFieldAlignment(currentSchumann);
    const harmonicCoherence = this.calculateHarmonicCoherence(currentSchumann);
    const resonanceStability = this.calculateResonanceStability(schumannHistory);
    const phaseLockStrength = this.calculatePhaseLockStrength(currentSchumann);
    
    // Weighted average for overall score
    const weights = { fieldAlignment: 0.25, harmonicCoherence: 0.30, resonanceStability: 0.20, phaseLockStrength: 0.25 };
    const overallScore = 
      fieldAlignment * weights.fieldAlignment +
      harmonicCoherence * weights.harmonicCoherence +
      resonanceStability * weights.resonanceStability +
      phaseLockStrength * weights.phaseLockStrength;
    
    // Check if all thresholds pass
    const isValid = 
      fieldAlignment >= this.thresholds.fieldAlignment &&
      harmonicCoherence >= this.thresholds.harmonicCoherence &&
      resonanceStability >= this.thresholds.resonanceStability &&
      phaseLockStrength >= this.thresholds.phaseLockStrength;
    
    return {
      fieldAlignment,
      harmonicCoherence,
      resonanceStability,
      phaseLockStrength,
      overallScore,
      isValid,
      timestamp: new Date()
    };
  }
  
  getThresholds(): ValidationThresholds {
    return { ...this.thresholds };
  }
}

// Singleton instance
export const earthValidation = new EarthValidation();
