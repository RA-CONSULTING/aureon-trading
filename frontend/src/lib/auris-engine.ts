import { aurisCodex } from './auris-codex';
import { earthDataLoader, type SchumannFeatures, type LatticeTimeseries, type AurisCodexConfig } from './earth-data-loader';
import { earthValidation, type ValidationResult } from './earth-validation';
import { earthStreamsMonitor, EarthStreamMetrics } from './earth-streams';

export interface WaveformData {
  frequency: number;
  amplitude: number;
  phase: number;
  decay: number;
  harmonics: number[];
}

export interface BroadcastResult {
  success: boolean;
  waveform: WaveformData;
  timestamp: number;
  field_coupling: number;
  schumann_resonance: number;
  validation_score: number;
}

export interface LiveSchumannData {
  fundamental: number; // 7.83 Hz base
  mode2: number; // ~14.3 Hz
  mode3: number; // ~20.8 Hz
  mode4: number; // ~27.3 Hz
  mode5: number; // ~33.8 Hz
  amplitude: number;
  coherence: number;
  timestamp: number;
  source: 'csv' | 'realtime';
}

export class AurisEngine {
  private isActive: boolean = false;
  private fieldCoupling: number = 1.618;
  private observerLock: boolean = true;
  private liveSchumannData: LiveSchumannData | null = null;
  private validationHistory: number[] = [];
  private earthStreamMetrics: EarthStreamMetrics | null = null;
  
  // Real CSV data storage
  private schumannDataFromCSV: SchumannFeatures[] = [];
  private latticeDataFromCSV: LatticeTimeseries[] = [];
  private aurisCodexConfig: AurisCodexConfig | null = null;
  private csvDataIndex: number = 0;
  private schumannHistory: SchumannFeatures[] = [];
  private currentValidation: ValidationResult | null = null;

  async initialize(): Promise<void> {
    console.log('🌍 Initializing Auris Engine with Real Earth Live Data...');
    
    try {
      // Load all earth live data files
      const data = await earthDataLoader.loadAll();
      
      this.schumannDataFromCSV = data.schumannData;
      this.latticeDataFromCSV = data.latticeData;
      this.aurisCodexConfig = data.aurisCodex;
      
      // Set codex for validation engine
      if (data.aurisCodex) {
        earthValidation.setCodex(data.aurisCodex);
      }
      
      console.log('📊 Loaded Earth data:', {
        schumann: this.schumannDataFromCSV.length,
        lattice: this.latticeDataFromCSV.length,
        codex: !!this.aurisCodexConfig
      });
      
      // Start earth stream monitoring for real-time data
      earthStreamsMonitor.initialize();
      this.startSchumannMonitoring();
      this.startEarthStreamMonitoring();
      this.isActive = true;
      
    } catch (error) {
      console.error('Failed to load Earth data, falling back to streams:', error);
      earthStreamsMonitor.initialize();
      this.startSchumannMonitoring();
      this.startEarthStreamMonitoring();
      this.isActive = true;
    }
  }

  private startSchumannMonitoring(): void {
    setInterval(() => {
      this.updateLiveSchumannData();
    }, 500);
  }
  
  private startEarthStreamMonitoring(): void {
    setInterval(() => {
      this.earthStreamMetrics = earthStreamsMonitor.getEarthStreamMetrics();
    }, 1000);
  }

  private updateLiveSchumannData(): void {
    const time = Date.now();
    
    // Use real CSV data if available
    if (this.schumannDataFromCSV.length > 0) {
      const csvData = this.schumannDataFromCSV[this.csvDataIndex % this.schumannDataFromCSV.length];
      
      // Track history for validation
      this.schumannHistory.push(csvData);
      if (this.schumannHistory.length > 60) {
        this.schumannHistory.shift();
      }
      
      // Get lattice data for validation
      const latticeData = this.latticeDataFromCSV.length > 0 
        ? this.latticeDataFromCSV[this.csvDataIndex % this.latticeDataFromCSV.length]
        : undefined;
      
      // Run validation using real formulas from auris_codex
      this.currentValidation = earthValidation.validate(csvData, this.schumannHistory, latticeData);
      
      // Convert CSV data to LiveSchumannData format
      this.liveSchumannData = {
        fundamental: 7.83 + (csvData.A7_83 - 0.25) * 0.5, // Slight modulation based on amplitude
        mode2: 14.3 + (csvData.A14_3 - 0.19) * 0.3,
        mode3: 20.8 + (csvData.A20_8 - 0.13) * 0.2,
        mode4: 27.3 + (csvData.A27_3 - 0.1) * 0.15,
        mode5: 33.8 + (csvData.A33_8 - 0.07) * 0.1,
        amplitude: csvData.A7_83 + csvData.A14_3 + csvData.A20_8,
        coherence: csvData.coherence_idx,
        timestamp: time,
        source: 'csv'
      };
      
      this.csvDataIndex++;
      return;
    }
    
    // Fallback to earth stream metrics if no CSV data
    const earthMetrics = this.earthStreamMetrics;
    const baseFreq = 7.83;
    
    let solarInfluence = Math.sin(time / 10000) * 0.2;
    let geomagneticInfluence = Math.cos(time / 15000) * 0.15;
    
    if (earthMetrics) {
      solarInfluence += (earthMetrics.solarWind.velocity - 400) / 2000;
      solarInfluence += (earthMetrics.solarWind.density - 5) / 50;
      geomagneticInfluence += (earthMetrics.geomagnetic.kpIndex - 2) / 20;
      geomagneticInfluence += earthMetrics.geomagnetic.dstIndex / 1000;
    }
    
    const ionosphericNoise = (Math.random() - 0.5) * 0.1;
    
    this.liveSchumannData = {
      fundamental: baseFreq + solarInfluence + geomagneticInfluence + ionosphericNoise,
      mode2: (baseFreq * 1.83) + solarInfluence * 1.5,
      mode3: (baseFreq * 2.66) + geomagneticInfluence * 2,
      mode4: (baseFreq * 3.48) + solarInfluence * 0.5,
      mode5: (baseFreq * 4.32) + geomagneticInfluence * 0.3,
      amplitude: 0.5 + Math.sin(time / 8000) * 0.3 + Math.random() * 0.2,
      coherence: earthMetrics?.coherenceIndex || (0.7 + Math.cos(time / 12000) * 0.2 + Math.random() * 0.1),
      timestamp: time,
      source: 'realtime'
    };
  }

  synthesizeWaveform(intent: string): WaveformData {
    const codexEntry = aurisCodex.getIntentFrequency(intent);
    if (!codexEntry) {
      throw new Error(`Unknown intent: ${intent}`);
    }

    const schumannCoupling = this.liveSchumannData ? 
      this.calculateSchumannCoupling(codexEntry.frequency) : 1.0;

    return {
      frequency: codexEntry.frequency * schumannCoupling,
      amplitude: this.calculateAmplitude(),
      phase: this.calculatePhase(),
      decay: codexEntry.decay,
      harmonics: this.enhanceHarmonicsWithSchumann(codexEntry.harmonics)
    };
  }

  private calculateSchumannCoupling(intentFreq: number): number {
    if (!this.liveSchumannData) return 1.0;
    
    const { fundamental, mode2, mode3, mode4, mode5 } = this.liveSchumannData;
    
    // Find closest harmonic relationship across all 5 modes
    const ratios = [
      Math.abs(intentFreq / fundamental),
      Math.abs(intentFreq / mode2),
      Math.abs(intentFreq / mode3),
      Math.abs(intentFreq / mode4),
      Math.abs(intentFreq / mode5),
      Math.abs(fundamental / intentFreq),
      Math.abs(mode2 / intentFreq),
      Math.abs(mode3 / intentFreq)
    ];
    
    const closestRatio = ratios.reduce((prev, curr) => 
      Math.abs(curr - Math.round(curr)) < Math.abs(prev - Math.round(prev)) ? curr : prev
    );
    
    // Boost coupling based on validation score if available
    const validationBoost = this.currentValidation?.overallScore || 0;
    
    return 0.95 + (this.liveSchumannData.coherence * 0.05) + (validationBoost * 0.05);
  }

  private enhanceHarmonicsWithSchumann(baseHarmonics: number[]): number[] {
    if (!this.liveSchumannData) return baseHarmonics;
    
    // Add all 5 Schumann mode harmonics
    const schumannHarmonics = [
      Math.round(this.liveSchumannData.fundamental),
      Math.round(this.liveSchumannData.mode2),
      Math.round(this.liveSchumannData.mode3),
      Math.round(this.liveSchumannData.mode4),
      Math.round(this.liveSchumannData.mode5)
    ];
    
    return [...baseHarmonics, ...schumannHarmonics].slice(0, 9);
  }

  async broadcast(waveform: WaveformData): Promise<BroadcastResult> {
    if (!this.isActive) {
      throw new Error('Auris Engine not initialized');
    }

    const validationScore = this.calculateValidationScore(waveform);
    this.validationHistory.push(validationScore);
    
    if (this.validationHistory.length > 100) {
      this.validationHistory.shift();
    }

    console.log('📡 Live Broadcasting:', {
      freq: waveform.frequency.toFixed(2),
      amp: waveform.amplitude.toFixed(3),
      schumann: this.liveSchumannData?.fundamental.toFixed(2),
      validation: validationScore.toFixed(2),
      source: this.liveSchumannData?.source || 'unknown'
    });

    return {
      success: validationScore > 0.5,
      waveform,
      timestamp: Date.now(),
      field_coupling: this.fieldCoupling,
      schumann_resonance: this.liveSchumannData?.fundamental || 7.83,
      validation_score: validationScore
    };
  }

  private calculateValidationScore(waveform: WaveformData): number {
    // Use real validation if available
    if (this.currentValidation) {
      const frequencyAlignment = this.calculateFrequencyAlignment(waveform.frequency);
      const amplitudeStability = Math.min(1, waveform.amplitude / 2.0);
      
      return (
        frequencyAlignment * 0.2 +
        amplitudeStability * 0.1 +
        this.currentValidation.overallScore * 0.7
      );
    }
    
    if (!this.liveSchumannData) return 0.5;
    
    const frequencyAlignment = this.calculateFrequencyAlignment(waveform.frequency);
    const amplitudeStability = Math.min(1, waveform.amplitude / 2.0);
    const schumannCoherence = this.liveSchumannData.coherence;
    const fieldCoupling = Math.min(1, this.fieldCoupling / 2.0);
    
    return (
      frequencyAlignment * 0.3 +
      amplitudeStability * 0.2 +
      schumannCoherence * 0.3 +
      fieldCoupling * 0.2
    );
  }

  private calculateFrequencyAlignment(frequency: number): number {
    if (!this.liveSchumannData) return 0.5;
    
    const fundamental = this.liveSchumannData.fundamental;
    const harmonicRatios = [1, 2, 3, 4, 5, 8, 13, 21];
    
    let bestAlignment = 0;
    for (const ratio of harmonicRatios) {
      const targetFreq = fundamental * ratio;
      const alignment = 1 - Math.abs(frequency - targetFreq) / targetFreq;
      bestAlignment = Math.max(bestAlignment, alignment);
    }
    
    return Math.max(0, bestAlignment);
  }

  private calculateAmplitude(): number {
    const baseAmplitude = 0.8 + Math.sin(Date.now() / 10000) * 0.2;
    const schumannBoost = this.liveSchumannData ? 
      this.liveSchumannData.amplitude * 0.5 : 0;
    
    return Math.min(2.0, baseAmplitude + schumannBoost);
  }

  private calculatePhase(): number {
    if (!this.observerLock) return Math.random() * Math.PI * 2;
    
    if (this.liveSchumannData) {
      const schumannPhase = (this.liveSchumannData.timestamp / 1000) * 
        this.liveSchumannData.fundamental * 2 * Math.PI;
      return schumannPhase % (Math.PI * 2);
    }
    
    return 0;
  }

  // Getters
  getLiveSchumannData(): LiveSchumannData | null {
    return this.liveSchumannData;
  }
  
  getValidationHistory(): number[] {
    return [...this.validationHistory];
  }

  getEarthStreamMetrics(): EarthStreamMetrics | null {
    return this.earthStreamMetrics;
  }
  
  getCurrentValidation(): ValidationResult | null {
    return this.currentValidation;
  }
  
  getDataSource(): 'csv' | 'realtime' | 'none' {
    return this.liveSchumannData?.source || 'none';
  }
  
  getSchumannModes(): { mode1: number; mode2: number; mode3: number; mode4: number; mode5: number } | null {
    if (!this.liveSchumannData) return null;
    return {
      mode1: this.liveSchumannData.fundamental,
      mode2: this.liveSchumannData.mode2,
      mode3: this.liveSchumannData.mode3,
      mode4: this.liveSchumannData.mode4,
      mode5: this.liveSchumannData.mode5
    };
  }
}

export const aurisEngine = new AurisEngine();
