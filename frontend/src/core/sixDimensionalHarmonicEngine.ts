/**
 * 6D Harmonic Waveform Engine
 * Ported from Python hnc_6d_harmonic_waveform.py
 * Generates 6-dimensional harmonic analysis for quantum trading
 */

// Sacred constants
const PHI = 1.618033988749895; // Golden ratio
const SCHUMANN = 7.83; // Earth's heartbeat Hz
const SOLFEGGIO = [174, 285, 396, 417, 528, 639, 741, 852, 963];
const LOVE_FREQUENCY = 528;

export type WaveState = 'CRYSTALLINE' | 'RESONANT' | 'TURBULENT' | 'CHAOTIC';
export type MarketPhase = 'ACCUMULATION' | 'MARKUP' | 'DISTRIBUTION' | 'MARKDOWN';

export interface Dimension {
  name: string;
  value: number;
  velocity: number;
  acceleration: number;
  phase: number;
  amplitude: number;
  frequency: number;
  history: number[];
}

export interface HarmonicWaveform6D {
  timestamp: number;
  symbol: string;
  
  // 6 Dimensions
  d1_price: Dimension;
  d2_volume: Dimension;
  d3_time: Dimension;
  d4_correlation: Dimension;
  d5_momentum: Dimension;
  d6_frequency: Dimension;
  
  // Derived metrics
  dimensionalCoherence: number;
  phaseAlignment: number;
  energyDensity: number;
  resonanceScore: number;
  harmonicConvergence: number;
  
  // States
  waveState: WaveState;
  marketPhase: MarketPhase;
  harmonicLock: boolean;
  probabilityField: number;
  
  // Trading signal
  action: string;
  confidence: number;
}

export interface EcosystemState6D {
  globalResonance: number;
  marketEnergy: number;
  dominantFrequency: number;
  phaseCoherence: number;
  dimensionalAlignment: number[];
}

function createDimension(name: string): Dimension {
  return {
    name,
    value: 0,
    velocity: 0,
    acceleration: 0,
    phase: 0,
    amplitude: 1,
    frequency: SCHUMANN,
    history: []
  };
}

function updateDimensionHistory(dim: Dimension, maxHistory = 100): void {
  dim.history.push(dim.value);
  if (dim.history.length > maxHistory) {
    dim.history.shift();
  }
}

function calculateWaveValue(dim: Dimension, t: number): number {
  return dim.amplitude * Math.sin(dim.frequency * t + dim.phase);
}

function normalize(value: number, min: number, max: number): number {
  if (max === min) return 0.5;
  return Math.max(0, Math.min(1, (value - min) / (max - min)));
}

export class SixDimensionalHarmonicEngine {
  private assets: Map<string, HarmonicWaveform6D> = new Map();
  private ecosystemState: EcosystemState6D;
  private tickCount = 0;
  
  constructor() {
    this.ecosystemState = {
      globalResonance: 0.5,
      marketEnergy: 0.5,
      dominantFrequency: SCHUMANN,
      phaseCoherence: 0.5,
      dimensionalAlignment: [0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
    };
  }
  
  updateAsset(
    symbol: string,
    price: number,
    volume: number,
    changePct: number,
    high: number,
    low: number,
    externalFrequency: number = LOVE_FREQUENCY,
    externalCoherence: number = 0.5
  ): HarmonicWaveform6D {
    this.tickCount++;
    const t = this.tickCount * 0.1; // Time factor
    
    // Get or create waveform
    let waveform = this.assets.get(symbol);
    if (!waveform) {
      waveform = this.initializeWaveform(symbol);
    }
    
    // Update timestamp
    waveform.timestamp = Date.now();
    
    // D1: Price Wave
    const prevPrice = waveform.d1_price.value || price;
    waveform.d1_price.velocity = price - prevPrice;
    waveform.d1_price.acceleration = waveform.d1_price.velocity - (waveform.d1_price.history[waveform.d1_price.history.length - 1] || 0);
    waveform.d1_price.value = price;
    waveform.d1_price.phase = Math.atan2(waveform.d1_price.velocity, Math.abs(price - low + 0.0001));
    waveform.d1_price.amplitude = high > low ? (high - low) / price : 0.01;
    waveform.d1_price.frequency = SCHUMANN * (1 + Math.abs(changePct) / 100);
    updateDimensionHistory(waveform.d1_price);
    
    // D2: Volume Pulse
    const prevVol = waveform.d2_volume.value || volume;
    waveform.d2_volume.velocity = volume - prevVol;
    waveform.d2_volume.value = volume;
    waveform.d2_volume.phase = Math.atan2(waveform.d2_volume.velocity, Math.max(volume, 1));
    waveform.d2_volume.amplitude = Math.min(volume / (prevVol + 1), 3);
    waveform.d2_volume.frequency = SCHUMANN * waveform.d2_volume.amplitude;
    updateDimensionHistory(waveform.d2_volume);
    
    // D3: Temporal Phase
    const hour = new Date().getUTCHours();
    const dayProgress = hour / 24;
    waveform.d3_time.value = dayProgress;
    waveform.d3_time.phase = dayProgress * 2 * Math.PI;
    waveform.d3_time.frequency = 1 / 24; // Daily cycle
    waveform.d3_time.amplitude = Math.sin(dayProgress * Math.PI); // Peak at noon
    updateDimensionHistory(waveform.d3_time);
    
    // D4: Cross-Market Resonance (correlation dimension)
    const globalFactor = this.ecosystemState.globalResonance;
    waveform.d4_correlation.value = globalFactor * externalCoherence;
    waveform.d4_correlation.phase = globalFactor * Math.PI;
    waveform.d4_correlation.amplitude = externalCoherence;
    waveform.d4_correlation.frequency = SCHUMANN * globalFactor;
    updateDimensionHistory(waveform.d4_correlation);
    
    // D5: Momentum Vortex
    const momentumRaw = changePct / 10; // Normalize percentage
    waveform.d5_momentum.velocity = momentumRaw - waveform.d5_momentum.value;
    waveform.d5_momentum.value = momentumRaw;
    waveform.d5_momentum.phase = Math.atan2(momentumRaw, 1);
    waveform.d5_momentum.amplitude = Math.abs(momentumRaw);
    waveform.d5_momentum.frequency = SCHUMANN * (1 + Math.abs(momentumRaw));
    updateDimensionHistory(waveform.d5_momentum);
    
    // D6: Harmonic Frequency
    const freqAlign = 1 - Math.abs(externalFrequency - LOVE_FREQUENCY) / LOVE_FREQUENCY;
    waveform.d6_frequency.value = externalFrequency;
    waveform.d6_frequency.phase = (externalFrequency / LOVE_FREQUENCY) * Math.PI;
    waveform.d6_frequency.amplitude = freqAlign;
    waveform.d6_frequency.frequency = externalFrequency / 100;
    updateDimensionHistory(waveform.d6_frequency);
    
    // Calculate derived metrics
    waveform.dimensionalCoherence = this.calculateDimensionalCoherence(waveform);
    waveform.phaseAlignment = this.calculatePhaseAlignment(waveform);
    waveform.energyDensity = this.calculateEnergyDensity(waveform);
    waveform.resonanceScore = this.calculateResonanceScore(waveform);
    waveform.harmonicConvergence = this.calculateHarmonicConvergence(waveform);
    
    // Determine states
    waveform.waveState = this.determineWaveState(waveform);
    waveform.marketPhase = this.determineMarketPhase(waveform);
    waveform.harmonicLock = waveform.resonanceScore > 0.8 && waveform.waveState === 'CRYSTALLINE';
    
    // Calculate probability field
    waveform.probabilityField = this.calculateProbabilityField(waveform);
    
    // Determine action
    const { action, confidence } = this.determineAction(waveform);
    waveform.action = action;
    waveform.confidence = confidence;
    
    // Update ecosystem
    this.updateEcosystemState();
    
    // Store updated waveform
    this.assets.set(symbol, waveform);
    
    return waveform;
  }
  
  private initializeWaveform(symbol: string): HarmonicWaveform6D {
    return {
      timestamp: Date.now(),
      symbol,
      d1_price: createDimension('Price Wave'),
      d2_volume: createDimension('Volume Pulse'),
      d3_time: createDimension('Temporal Phase'),
      d4_correlation: createDimension('Cross-Market Resonance'),
      d5_momentum: createDimension('Momentum Vortex'),
      d6_frequency: createDimension('Harmonic Frequency'),
      dimensionalCoherence: 0.5,
      phaseAlignment: 0.5,
      energyDensity: 0.5,
      resonanceScore: 0.5,
      harmonicConvergence: 0.5,
      waveState: 'TURBULENT',
      marketPhase: 'ACCUMULATION',
      harmonicLock: false,
      probabilityField: 0.5,
      action: 'HOLD',
      confidence: 0.5
    };
  }
  
  private calculateDimensionalCoherence(wf: HarmonicWaveform6D): number {
    const dims = [wf.d1_price, wf.d2_volume, wf.d3_time, wf.d4_correlation, wf.d5_momentum, wf.d6_frequency];
    const phases = dims.map(d => d.phase);
    
    // Calculate phase variance
    const meanPhase = phases.reduce((a, b) => a + b, 0) / phases.length;
    const variance = phases.reduce((sum, p) => sum + Math.pow(p - meanPhase, 2), 0) / phases.length;
    
    // Lower variance = higher coherence
    return Math.exp(-variance / Math.PI);
  }
  
  private calculatePhaseAlignment(wf: HarmonicWaveform6D): number {
    const dims = [wf.d1_price, wf.d2_volume, wf.d3_time, wf.d4_correlation, wf.d5_momentum, wf.d6_frequency];
    
    // Check alignment with golden ratio harmonics
    let alignment = 0;
    for (let i = 0; i < dims.length; i++) {
      const idealPhase = (i * 2 * Math.PI) / PHI;
      const diff = Math.abs(dims[i].phase - (idealPhase % (2 * Math.PI)));
      alignment += 1 - (diff / Math.PI);
    }
    
    return alignment / dims.length;
  }
  
  private calculateEnergyDensity(wf: HarmonicWaveform6D): number {
    const dims = [wf.d1_price, wf.d2_volume, wf.d3_time, wf.d4_correlation, wf.d5_momentum, wf.d6_frequency];
    
    // E = 0.5 * A² * ω² for each dimension
    const totalEnergy = dims.reduce((sum, d) => {
      return sum + 0.5 * Math.pow(d.amplitude, 2) * Math.pow(d.frequency, 2);
    }, 0);
    
    // Normalize to 0-1 range
    return Math.tanh(totalEnergy / 100);
  }
  
  private calculateResonanceScore(wf: HarmonicWaveform6D): number {
    // Resonance = coherence * alignment * (1 + energy dampening)
    const base = wf.dimensionalCoherence * wf.phaseAlignment;
    const energyFactor = 1 / (1 + wf.energyDensity);
    
    // Boost for 528 Hz alignment
    const freqBoost = wf.d6_frequency.amplitude;
    
    return Math.min(1, base * energyFactor + freqBoost * 0.2);
  }
  
  private calculateHarmonicConvergence(wf: HarmonicWaveform6D): number {
    // Check if frequencies are converging to harmonic ratios
    const dims = [wf.d1_price, wf.d2_volume, wf.d3_time, wf.d4_correlation, wf.d5_momentum, wf.d6_frequency];
    const freqs = dims.map(d => d.frequency);
    
    let harmonicScore = 0;
    for (let i = 0; i < freqs.length - 1; i++) {
      for (let j = i + 1; j < freqs.length; j++) {
        const ratio = freqs[i] / (freqs[j] + 0.001);
        // Check for simple harmonic ratios (1:1, 2:1, 3:2, etc.)
        const nearestHarmonic = Math.round(ratio * 2) / 2;
        const deviation = Math.abs(ratio - nearestHarmonic);
        harmonicScore += Math.exp(-deviation);
      }
    }
    
    return harmonicScore / 15; // 15 = C(6,2) combinations
  }
  
  private determineWaveState(wf: HarmonicWaveform6D): WaveState {
    const score = wf.resonanceScore;
    const coherence = wf.dimensionalCoherence;
    
    if (score > 0.8 && coherence > 0.7) return 'CRYSTALLINE';
    if (score > 0.6 && coherence > 0.5) return 'RESONANT';
    if (score > 0.4) return 'TURBULENT';
    return 'CHAOTIC';
  }
  
  private determineMarketPhase(wf: HarmonicWaveform6D): MarketPhase {
    const momentum = wf.d5_momentum.value;
    const volume = wf.d2_volume.amplitude;
    
    if (momentum > 0.3 && volume > 1.2) return 'MARKUP';
    if (momentum < -0.3 && volume > 1.2) return 'MARKDOWN';
    if (momentum > 0 && volume < 0.8) return 'ACCUMULATION';
    return 'DISTRIBUTION';
  }
  
  private calculateProbabilityField(wf: HarmonicWaveform6D): number {
    // Probability from dimensional convergence
    const convergence = (
      wf.dimensionalCoherence * 0.25 +
      wf.phaseAlignment * 0.25 +
      wf.resonanceScore * 0.25 +
      wf.harmonicConvergence * 0.25
    );
    
    // Boost for crystalline state
    const stateBoost = wf.waveState === 'CRYSTALLINE' ? 0.15 : 
                       wf.waveState === 'RESONANT' ? 0.05 : 0;
    
    // Direction from momentum
    const direction = Math.sign(wf.d5_momentum.value);
    
    // Final probability: 0.5 = neutral, >0.5 = bullish, <0.5 = bearish
    return Math.max(0, Math.min(1, 0.5 + (convergence - 0.5 + stateBoost) * direction));
  }
  
  private determineAction(wf: HarmonicWaveform6D): { action: string; confidence: number } {
    const prob = wf.probabilityField;
    const stateMultiplier = wf.waveState === 'CRYSTALLINE' ? 1.0 :
                           wf.waveState === 'RESONANT' ? 0.9 :
                           wf.waveState === 'TURBULENT' ? 0.7 : 0.5;
    
    const confidence = wf.resonanceScore * stateMultiplier;
    
    if (prob >= 0.70) return { action: 'STRONG_BUY', confidence };
    if (prob >= 0.60) return { action: 'BUY', confidence };
    if (prob >= 0.55) return { action: 'SLIGHT_BUY', confidence };
    if (prob >= 0.45) return { action: 'HOLD', confidence };
    if (prob >= 0.40) return { action: 'SLIGHT_SELL', confidence };
    if (prob >= 0.30) return { action: 'SELL', confidence };
    return { action: 'STRONG_SELL', confidence };
  }
  
  private updateEcosystemState(): void {
    const waveforms = Array.from(this.assets.values());
    if (waveforms.length === 0) return;
    
    // Calculate global resonance from all assets
    const avgResonance = waveforms.reduce((sum, wf) => sum + wf.resonanceScore, 0) / waveforms.length;
    this.ecosystemState.globalResonance = avgResonance;
    
    // Market energy from energy densities
    const avgEnergy = waveforms.reduce((sum, wf) => sum + wf.energyDensity, 0) / waveforms.length;
    this.ecosystemState.marketEnergy = avgEnergy;
    
    // Dominant frequency
    const avgFreq = waveforms.reduce((sum, wf) => sum + wf.d6_frequency.value, 0) / waveforms.length;
    this.ecosystemState.dominantFrequency = avgFreq;
    
    // Phase coherence
    const avgCoherence = waveforms.reduce((sum, wf) => sum + wf.dimensionalCoherence, 0) / waveforms.length;
    this.ecosystemState.phaseCoherence = avgCoherence;
    
    // Dimensional alignment
    this.ecosystemState.dimensionalAlignment = [
      waveforms.reduce((sum, wf) => sum + wf.d1_price.amplitude, 0) / waveforms.length,
      waveforms.reduce((sum, wf) => sum + wf.d2_volume.amplitude, 0) / waveforms.length,
      waveforms.reduce((sum, wf) => sum + wf.d3_time.amplitude, 0) / waveforms.length,
      waveforms.reduce((sum, wf) => sum + wf.d4_correlation.amplitude, 0) / waveforms.length,
      waveforms.reduce((sum, wf) => sum + wf.d5_momentum.amplitude, 0) / waveforms.length,
      waveforms.reduce((sum, wf) => sum + wf.d6_frequency.amplitude, 0) / waveforms.length,
    ];
  }
  
  getWaveform(symbol: string): HarmonicWaveform6D | undefined {
    return this.assets.get(symbol);
  }
  
  getEcosystemState(): EcosystemState6D {
    return this.ecosystemState;
  }
  
  getAllWaveforms(): HarmonicWaveform6D[] {
    return Array.from(this.assets.values());
  }
}

// Singleton instance
export const sixDimensionalEngine = new SixDimensionalHarmonicEngine();
