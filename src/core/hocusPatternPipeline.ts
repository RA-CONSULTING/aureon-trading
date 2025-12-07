/**
 * Hocus → Pattern → Template Pipeline
 * Enhanced with Ecosystem Codex Integration
 * 
 * 6-Stage Reality Field Emergence System:
 * 1. Pre-form (raw field + noise)
 * 2. Feedback + Resonance (delay echo)
 * 3. Mode Decomposition (waves → shapes)
 * 4. Coherence Measurement (stable pattern check)
 * 5. Template Activation (observer node recognition)
 * 6. Dominant Template Selection
 * 
 * + Ecosystem Enhancements from JSON codex files
 */

import { ecosystemEnhancements, FrequencyCodexEntry, AurisCodexEntry } from './ecosystemEnhancements';

export interface PipelineConfig {
  // Stage 1: Pre-form
  noiseAmplitude: number;      // η amplitude
  
  // Stage 2: Feedback
  alpha: number;               // feedback gain (0-1)
  tau: number;                 // delay samples
  
  // Stage 3: Modes
  numModes: number;            // number of eigenmodes to track
  modeFrequencies: number[];   // φₖ base frequencies (Hz)
  
  // Stage 4: Coherence
  coherenceWindow: number;     // Δ for autocorrelation
  
  // Stage 5: Template
  theta: number;               // coherence threshold for activation
  
  // Ecosystem enhancement
  useCodexEnhancement: boolean;
}

export interface ModeState {
  k: number;                   // mode index
  frequency: number;           // φₖ frequency
  amplitude: number;           // aₖ(t) current amplitude
  phase: number;               // current phase
  lambda: number;              // growth/decay rate
  coherence: number;           // Cₖ coherence metric
  isTemplate: boolean;         // Tₖ = 1 or 0
  // Ecosystem enhancements
  codexName?: string;          // Name from frequency codex
  harmonics?: number[];        // Harmonic series from codex
  emotionalPhase?: string;     // Emotional phase mapping
  aurisBoost?: number;         // Boost from Auris codex
}

export interface PipelineState {
  timestamp: number;
  
  // Stage 1: Raw field
  rawField: number;
  noise: number;
  
  // Stage 2: Feedback field
  feedbackField: number;
  echoContribution: number;
  
  // Stage 3-5: Mode states
  modes: ModeState[];
  
  // Stage 6: Dominant template
  dominantMode: number;        // k* = argmax Cₖ
  dominantCoherence: number;
  
  // Aggregate metrics
  totalCoherence: number;      // average across active templates
  activeTemplates: number;     // count of Tₖ = 1
  pipelineStage: 'HOCUS' | 'PATTERN' | 'TEMPLATE';
  
  // Ecosystem enhancement metrics
  codexEnhanced: boolean;
  dominantEmotionalPhase: string;
  harmonicResonance: number;
}

const DEFAULT_CONFIG: PipelineConfig = {
  noiseAmplitude: 0.1,
  alpha: 0.3,
  tau: 10,
  numModes: 5,
  modeFrequencies: [7.83, 14.1, 20.3, 528, 963], // Schumann + Love + Unity
  coherenceWindow: 20,
  theta: 0.7,
  useCodexEnhancement: true
};

export class HocusPatternPipeline {
  private config: PipelineConfig;
  private fieldHistory: number[] = [];
  private modeHistories: Map<number, number[]> = new Map();
  private currentState: PipelineState | null = null;
  private stepCount = 0;
  private codexLoaded = false;
  
  constructor(config: Partial<PipelineConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.initializeModeHistories();
    this.loadCodexEnhancements();
  }
  
  /**
   * Load ecosystem enhancements from JSON codex files
   */
  private async loadCodexEnhancements(): Promise<void> {
    if (!this.config.useCodexEnhancement) return;
    
    try {
      await ecosystemEnhancements.loadAll();
      this.codexLoaded = ecosystemEnhancements.isLoaded();
      
      // Enhance mode frequencies from codex
      if (this.codexLoaded) {
        this.enhanceModeFrequenciesFromCodex();
      }
      
      console.log('🔮 Pipeline codex enhancement:', this.codexLoaded ? 'ACTIVE' : 'PENDING');
    } catch (error) {
      console.warn('Pipeline codex enhancement failed:', error);
    }
  }
  
  /**
   * Enhance mode frequencies using frequency codex data
   */
  private enhanceModeFrequenciesFromCodex(): void {
    const enhancements = ecosystemEnhancements.getEnhancements();
    
    if (enhancements.frequencyCodex.length > 0) {
      // Add frequencies from codex that aren't already in config
      const existingFreqs = new Set(this.config.modeFrequencies);
      const codexFreqs = enhancements.frequencyCodex
        .map(entry => entry.frequency)
        .filter(f => !existingFreqs.has(f))
        .slice(0, 3); // Add up to 3 new frequencies
      
      if (codexFreqs.length > 0) {
        this.config.modeFrequencies = [...this.config.modeFrequencies, ...codexFreqs];
        this.config.numModes = this.config.modeFrequencies.length;
        this.initializeModeHistories();
        console.log('📊 Pipeline frequencies enhanced:', this.config.modeFrequencies);
      }
    }
  }
  
  private initializeModeHistories(): void {
    for (let k = 0; k < this.config.numModes; k++) {
      this.modeHistories.set(k, []);
    }
  }
  
  /**
   * Stage 1: Pre-form / "Hocus Pocus"
   * x(t+Δt) = x(t) + F(x(t))Δt + η(t)
   */
  private computePreform(currentField: number): { rawField: number; noise: number } {
    // F(x) - internal dynamics (simple damping toward 0)
    const F = -0.1 * currentField;
    const dt = 1;
    
    // η(t) - Gaussian noise
    const u1 = Math.random();
    const u2 = Math.random();
    const noise = this.config.noiseAmplitude * Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
    
    const rawField = currentField + F * dt + noise;
    
    return { rawField, noise };
  }
  
  /**
   * Stage 2: Feedback + Resonance
   * x(t+Δt) = (1-α)x(t) + αx(t-τ) + η(t)
   */
  private computeFeedback(rawField: number, noise: number): { feedbackField: number; echoContribution: number } {
    const { alpha, tau } = this.config;
    
    // Get delayed field value (echo)
    const delayedField = this.fieldHistory.length >= tau 
      ? this.fieldHistory[this.fieldHistory.length - tau] 
      : 0;
    
    // Feedback equation
    const echoContribution = alpha * delayedField;
    const feedbackField = (1 - alpha) * rawField + echoContribution + noise * 0.5;
    
    return { feedbackField, echoContribution };
  }
  
  /**
   * Stage 3: Mode Decomposition (Enhanced with Ecosystem Codex)
   * x(t) = Σₖ aₖ(t)φₖ
   * daₖ/dt = λₖaₖ(t) + ξₖ(t)
   */
  private decomposeIntoModes(field: number, t: number): ModeState[] {
    const modes: ModeState[] = [];
    
    for (let k = 0; k < this.config.numModes; k++) {
      const freq = this.config.modeFrequencies[k];
      
      // φₖ - basis function (sinusoidal eigenmode)
      const phi = Math.sin(2 * Math.PI * freq * t / 1000);
      
      // Project field onto mode: aₖ ≈ x · φₖ
      const amplitude = field * phi;
      
      // λₖ - growth rate (modes near resonance grow)
      // Enhanced with codex boost
      const { lambda, aurisBoost } = this.computeEnhancedGrowthRate(k, freq);
      
      // ξₖ - projected noise
      const xi = (Math.random() - 0.5) * 0.05;
      
      // Update amplitude with dynamics
      const history = this.modeHistories.get(k) || [];
      const prevAmplitude = history.length > 0 ? history[history.length - 1] : 0;
      const newAmplitude = prevAmplitude + lambda * prevAmplitude + xi + amplitude * 0.1;
      
      // Store in history
      history.push(newAmplitude);
      if (history.length > 100) history.shift();
      this.modeHistories.set(k, history);
      
      // Compute coherence for this mode (Stage 4)
      const coherence = this.computeModeCoherence(k);
      
      // Template activation (Stage 5) - enhanced threshold from codex
      const enhancedTheta = this.getEnhancedThreshold(freq);
      const isTemplate = coherence >= enhancedTheta;
      
      // Get codex enhancements for this mode
      const { codexName, harmonics, emotionalPhase } = this.getCodexEnhancements(freq);
      
      modes.push({
        k,
        frequency: freq,
        amplitude: newAmplitude,
        phase: (2 * Math.PI * freq * t / 1000) % (2 * Math.PI),
        lambda,
        coherence,
        isTemplate,
        codexName,
        harmonics,
        emotionalPhase,
        aurisBoost
      });
    }
    
    return modes;
  }
  
  /**
   * Get codex enhancements for a frequency
   */
  private getCodexEnhancements(freq: number): { 
    codexName: string; 
    harmonics: number[]; 
    emotionalPhase: string 
  } {
    if (!this.codexLoaded) {
      return { codexName: 'Unknown', harmonics: [], emotionalPhase: 'neutral' };
    }
    
    const freqEnhancement = ecosystemEnhancements.getFrequencyEnhancement(freq);
    const { harmonics: codexHarmonics, name } = ecosystemEnhancements.applyFrequencyHarmonics(freq);
    
    // Map frequency to emotional phase
    let emotionalPhase = 'neutral';
    if (freq < 100) emotionalPhase = 'grounding';
    else if (freq < 300) emotionalPhase = 'growth';
    else if (freq < 600) emotionalPhase = 'love';
    else emotionalPhase = 'transcendence';
    
    return {
      codexName: name || freqEnhancement?.name || 'Mode-' + Math.round(freq),
      harmonics: codexHarmonics,
      emotionalPhase
    };
  }
  
  /**
   * Get enhanced coherence threshold from codex
   */
  private getEnhancedThreshold(freq: number): number {
    if (!this.codexLoaded) return this.config.theta;
    
    // Sacred frequencies get lower threshold (easier to activate)
    const sacredFreqs = [7.83, 528, 963, 432];
    const isSacred = sacredFreqs.some(sf => Math.abs(freq - sf) < 10);
    
    return isSacred ? this.config.theta * 0.85 : this.config.theta;
  }
  
  /**
   * Compute enhanced growth rate λₖ for mode k with Auris codex boost
   * Modes that resonate with the system's natural frequencies grow
   */
  private computeEnhancedGrowthRate(k: number, freq: number): { lambda: number; aurisBoost: number } {
    // Base resonant frequencies grow (528 Hz Love frequency has highest growth)
    const resonanceFreqs = [7.83, 528, 963];
    let lambda = -0.01; // default decay
    let aurisBoost = 1.0;
    
    for (const resFreq of resonanceFreqs) {
      const distance = Math.abs(freq - resFreq) / resFreq;
      if (distance < 0.1) {
        lambda = 0.05 * (1 - distance * 10); // grow if close to resonance
      }
    }
    
    // Apply Auris codex enhancement
    if (this.codexLoaded) {
      const enhancements = ecosystemEnhancements.getEnhancements();
      
      // Check if frequency matches any Auris node
      for (const aurisNode of enhancements.aurisCodex) {
        if (aurisNode.frequency && Math.abs(freq - aurisNode.frequency) < 50) {
          aurisBoost = ecosystemEnhancements.applyAurisBoost(aurisNode.name, 1.0);
          lambda *= (1 + (aurisBoost - 1) * 0.5); // Apply weighted boost to growth
          break;
        }
      }
      
      // Symbolic compiler trigger check
      const symbolic = ecosystemEnhancements.getSymbolicTriggers('BUY');
      if (symbolic && freq >= 500 && freq <= 600) {
        // Love frequency range gets extra boost from symbolic layer
        lambda *= 1.15;
        aurisBoost *= 1.1;
      }
    }
    
    return { lambda, aurisBoost };
  }
  
  /**
   * Stage 4: Pattern Coherence
   * Cₖ = |⟨aₖ(t)aₖ*(t+Δ)⟩| / ⟨|aₖ(t)|²⟩
   */
  private computeModeCoherence(k: number): number {
    const history = this.modeHistories.get(k) || [];
    const delta = Math.min(this.config.coherenceWindow, Math.floor(history.length / 2));
    
    if (history.length < delta + 5) return 0;
    
    // Compute autocorrelation
    let numerator = 0;
    let denominator = 0;
    const n = history.length - delta;
    
    for (let i = 0; i < n; i++) {
      const a_t = history[i];
      const a_tplusdelta = history[i + delta];
      numerator += a_t * a_tplusdelta;
      denominator += a_t * a_t;
    }
    
    if (denominator === 0) return 0;
    
    // Coherence = |autocorrelation| normalized
    const coherence = Math.abs(numerator / denominator);
    return Math.min(1, Math.max(0, coherence));
  }
  
  /**
   * Stage 6: Dominant Template Selection
   * k* = argmax_k Cₖ
   */
  private selectDominantTemplate(modes: ModeState[]): { dominantMode: number; dominantCoherence: number } {
    let maxCoherence = 0;
    let dominantMode = 0;
    
    for (const mode of modes) {
      if (mode.coherence > maxCoherence) {
        maxCoherence = mode.coherence;
        dominantMode = mode.k;
      }
    }
    
    return { dominantMode, dominantCoherence: maxCoherence };
  }
  
  /**
   * Determine pipeline stage based on system state
   */
  private determinePipelineStage(modes: ModeState[]): 'HOCUS' | 'PATTERN' | 'TEMPLATE' {
    const activeTemplates = modes.filter(m => m.isTemplate).length;
    const avgCoherence = modes.reduce((sum, m) => sum + m.coherence, 0) / modes.length;
    
    if (avgCoherence < 0.3) return 'HOCUS';      // Still noise
    if (activeTemplates === 0) return 'PATTERN'; // Patterns forming
    return 'TEMPLATE';                            // Templates locked
  }
  
  /**
   * Main pipeline step - runs all 6 stages with ecosystem enhancement
   */
  public step(externalInput: number = 0): PipelineState {
    this.stepCount++;
    const t = this.stepCount;
    
    // Get current field from history or start at 0
    const currentField = this.fieldHistory.length > 0 
      ? this.fieldHistory[this.fieldHistory.length - 1] 
      : 0;
    
    // Stage 1: Pre-form
    const { rawField, noise } = this.computePreform(currentField + externalInput);
    
    // Stage 2: Feedback + Resonance
    const { feedbackField, echoContribution } = this.computeFeedback(rawField, noise);
    
    // Store in field history
    this.fieldHistory.push(feedbackField);
    if (this.fieldHistory.length > 200) this.fieldHistory.shift();
    
    // Stage 3-5: Mode decomposition, coherence, template activation (enhanced)
    const modes = this.decomposeIntoModes(feedbackField, t);
    
    // Stage 6: Dominant template
    const { dominantMode, dominantCoherence } = this.selectDominantTemplate(modes);
    
    // Aggregate metrics
    const activeTemplates = modes.filter(m => m.isTemplate).length;
    const totalCoherence = activeTemplates > 0
      ? modes.filter(m => m.isTemplate).reduce((sum, m) => sum + m.coherence, 0) / activeTemplates
      : 0;
    
    const pipelineStage = this.determinePipelineStage(modes);
    
    // Ecosystem enhancement metrics
    const dominantEmotionalPhase = modes[dominantMode]?.emotionalPhase || 'neutral';
    const harmonicResonance = this.computeHarmonicResonance(modes);
    
    this.currentState = {
      timestamp: Date.now(),
      rawField,
      noise,
      feedbackField,
      echoContribution,
      modes,
      dominantMode,
      dominantCoherence,
      totalCoherence,
      activeTemplates,
      pipelineStage,
      codexEnhanced: this.codexLoaded,
      dominantEmotionalPhase,
      harmonicResonance
    };
    
    return this.currentState;
  }
  
  /**
   * Compute harmonic resonance across all modes using codex harmonics
   */
  private computeHarmonicResonance(modes: ModeState[]): number {
    if (!this.codexLoaded || modes.length === 0) return 0;
    
    let resonanceSum = 0;
    let count = 0;
    
    for (const mode of modes) {
      if (mode.harmonics && mode.harmonics.length > 0) {
        // Check how many harmonics are reinforcing
        const harmonicStrength = mode.harmonics.reduce((sum, h, i) => {
          return sum + h / (i + 1); // Weight earlier harmonics more
        }, 0) / mode.harmonics.length;
        
        resonanceSum += mode.coherence * harmonicStrength * (mode.aurisBoost || 1);
        count++;
      }
    }
    
    return count > 0 ? resonanceSum / count : 0;
  }
  
  public getState(): PipelineState | null {
    return this.currentState;
  }
  
  public getFieldHistory(): number[] {
    return [...this.fieldHistory];
  }
  
  public getModeHistory(k: number): number[] {
    return [...(this.modeHistories.get(k) || [])];
  }
  
  public reset(): void {
    this.fieldHistory = [];
    this.modeHistories.clear();
    this.initializeModeHistories();
    this.currentState = null;
    this.stepCount = 0;
  }
}

// Singleton instance
export const hocusPatternPipeline = new HocusPatternPipeline();
