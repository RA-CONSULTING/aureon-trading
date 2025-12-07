/**
 * Hocus → Pattern → Template Pipeline
 * 
 * 6-Stage Reality Field Emergence System:
 * 1. Pre-form (raw field + noise)
 * 2. Feedback + Resonance (delay echo)
 * 3. Mode Decomposition (waves → shapes)
 * 4. Coherence Measurement (stable pattern check)
 * 5. Template Activation (observer node recognition)
 * 6. Dominant Template Selection
 */

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
}

export interface ModeState {
  k: number;                   // mode index
  frequency: number;           // φₖ frequency
  amplitude: number;           // aₖ(t) current amplitude
  phase: number;               // current phase
  lambda: number;              // growth/decay rate
  coherence: number;           // Cₖ coherence metric
  isTemplate: boolean;         // Tₖ = 1 or 0
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
}

const DEFAULT_CONFIG: PipelineConfig = {
  noiseAmplitude: 0.1,
  alpha: 0.3,
  tau: 10,
  numModes: 5,
  modeFrequencies: [7.83, 14.1, 20.3, 528, 963], // Schumann + Love + Unity
  coherenceWindow: 20,
  theta: 0.7
};

export class HocusPatternPipeline {
  private config: PipelineConfig;
  private fieldHistory: number[] = [];
  private modeHistories: Map<number, number[]> = new Map();
  private currentState: PipelineState | null = null;
  private stepCount = 0;
  
  constructor(config: Partial<PipelineConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.initializeModeHistories();
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
   * Stage 3: Mode Decomposition
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
      // Simplified: modes with frequency matching field oscillation grow
      const lambda = this.computeGrowthRate(k, freq);
      
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
      
      // Template activation (Stage 5)
      const isTemplate = coherence >= this.config.theta;
      
      modes.push({
        k,
        frequency: freq,
        amplitude: newAmplitude,
        phase: (2 * Math.PI * freq * t / 1000) % (2 * Math.PI),
        lambda,
        coherence,
        isTemplate
      });
    }
    
    return modes;
  }
  
  /**
   * Compute growth rate λₖ for mode k
   * Modes that resonate with the system's natural frequencies grow
   */
  private computeGrowthRate(k: number, freq: number): number {
    // Resonant frequencies grow (528 Hz Love frequency has highest growth)
    const resonanceFreqs = [7.83, 528, 963];
    let lambda = -0.01; // default decay
    
    for (const resFreq of resonanceFreqs) {
      const distance = Math.abs(freq - resFreq) / resFreq;
      if (distance < 0.1) {
        lambda = 0.05 * (1 - distance * 10); // grow if close to resonance
      }
    }
    
    return lambda;
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
   * Main pipeline step - runs all 6 stages
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
    
    // Stage 3-5: Mode decomposition, coherence, template activation
    const modes = this.decomposeIntoModes(feedbackField, t);
    
    // Stage 6: Dominant template
    const { dominantMode, dominantCoherence } = this.selectDominantTemplate(modes);
    
    // Aggregate metrics
    const activeTemplates = modes.filter(m => m.isTemplate).length;
    const totalCoherence = activeTemplates > 0
      ? modes.filter(m => m.isTemplate).reduce((sum, m) => sum + m.coherence, 0) / activeTemplates
      : 0;
    
    const pipelineStage = this.determinePipelineStage(modes);
    
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
      pipelineStage
    };
    
    return this.currentState;
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
