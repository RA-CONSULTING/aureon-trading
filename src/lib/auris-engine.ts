import { aurisCodex } from './auris-codex';
import { EarthDataLoader } from './earth-data-loader';
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
  amplitude: number;
  coherence: number;
  timestamp: number;
}

export class AurisEngine {
  private isActive: boolean = false;
  private fieldCoupling: number = 1.618;
  private observerLock: boolean = true;
  private earthDataLoader: EarthDataLoader = new EarthDataLoader();
  private liveSchumannData: LiveSchumannData | null = null;
  private validationHistory: number[] = [];
  private earthStreamMetrics: EarthStreamMetrics | null = null;

  async initialize(): Promise<void> {
    console.log('🌍 Initializing Auris Engine with Enhanced Earth Streams...');
    await this.earthDataLoader.loadManifest();
    earthStreamsMonitor.initialize();
    this.startSchumannMonitoring();
    this.startEarthStreamMonitoring();
    this.isActive = true;
  }

  private startSchumannMonitoring(): void {
    // Simulate real-time Schumann resonance monitoring
    setInterval(() => {
      this.updateLiveSchumannData();
    }, 500); // Update every 500ms for high-frequency monitoring
  }
  private startEarthStreamMonitoring(): void {
    setInterval(() => {
      this.earthStreamMetrics = earthStreamsMonitor.getEarthStreamMetrics();
    }, 1000); // Update earth streams every second
  }

  private updateLiveSchumannData(): void {
    const time = Date.now();
    const baseFreq = 7.83;
    
    // Enhanced Schumann variations with real Earth stream influences
    const earthMetrics = this.earthStreamMetrics;
    let solarInfluence = Math.sin(time / 10000) * 0.2;
    let geomagneticInfluence = Math.cos(time / 15000) * 0.15;
    
    if (earthMetrics) {
      // Solar wind influence on Schumann resonance
      solarInfluence += (earthMetrics.solarWind.velocity - 400) / 2000; // velocity influence
      solarInfluence += (earthMetrics.solarWind.density - 5) / 50; // density influence
      
      // Geomagnetic field influence
      geomagneticInfluence += (earthMetrics.geomagnetic.kpIndex - 2) / 20;
      geomagneticInfluence += earthMetrics.geomagnetic.dstIndex / 1000;
    }
    
    const ionosphericNoise = (Math.random() - 0.5) * 0.1;
    
    this.liveSchumannData = {
      fundamental: baseFreq + solarInfluence + geomagneticInfluence + ionosphericNoise,
      mode2: (baseFreq * 1.83) + solarInfluence * 1.5,
      mode3: (baseFreq * 2.66) + geomagneticInfluence * 2,
      amplitude: 0.5 + Math.sin(time / 8000) * 0.3 + Math.random() * 0.2,
      coherence: earthMetrics?.coherenceIndex || (0.7 + Math.cos(time / 12000) * 0.2 + Math.random() * 0.1),
      timestamp: time
    };
  }

  synthesizeWaveform(intent: string): WaveformData {
    const codexEntry = aurisCodex.getIntentFrequency(intent);
    if (!codexEntry) {
      throw new Error(`Unknown intent: ${intent}`);
    }

    // Enhance waveform with live Schumann coupling
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
    
    // Calculate resonance coupling between intent frequency and Schumann modes
    const fundamental = this.liveSchumannData.fundamental;
    const mode2 = this.liveSchumannData.mode2;
    const mode3 = this.liveSchumannData.mode3;
    
    // Find closest harmonic relationship
    const ratios = [
      Math.abs(intentFreq / fundamental),
      Math.abs(intentFreq / mode2),
      Math.abs(intentFreq / mode3),
      Math.abs(fundamental / intentFreq),
      Math.abs(mode2 / intentFreq),
      Math.abs(mode3 / intentFreq)
    ];
    
    const closestRatio = ratios.reduce((prev, curr) => 
      Math.abs(curr - Math.round(curr)) < Math.abs(prev - Math.round(prev)) ? curr : prev
    );
    
    // Coupling strength based on harmonic alignment
    return 0.95 + (this.liveSchumannData.coherence * 0.1);
  }

  private enhanceHarmonicsWithSchumann(baseHarmonics: number[]): number[] {
    if (!this.liveSchumannData) return baseHarmonics;
    
    // Add Schumann-influenced harmonics
    const schumannHarmonics = [
      Math.round(this.liveSchumannData.fundamental),
      Math.round(this.liveSchumannData.mode2),
      Math.round(this.liveSchumannData.mode3)
    ];
    
    return [...baseHarmonics, ...schumannHarmonics].slice(0, 7); // Limit to 7 harmonics
  }

  async broadcast(waveform: WaveformData): Promise<BroadcastResult> {
    if (!this.isActive) {
      throw new Error('Auris Engine not initialized');
    }

    const validationScore = this.calculateValidationScore(waveform);
    this.validationHistory.push(validationScore);
    
    // Keep only last 100 validation scores
    if (this.validationHistory.length > 100) {
      this.validationHistory.shift();
    }

    console.log('📡 Live Broadcasting:', {
      freq: waveform.frequency.toFixed(2),
      amp: waveform.amplitude.toFixed(3),
      schumann: this.liveSchumannData?.fundamental.toFixed(2),
      validation: validationScore.toFixed(2)
    });

    const result: BroadcastResult = {
      success: validationScore > 0.5,
      waveform,
      timestamp: Date.now(),
      field_coupling: this.fieldCoupling,
      schumann_resonance: this.liveSchumannData?.fundamental || 7.83,
      validation_score: validationScore
    };

    return result;
  }

  private calculateValidationScore(waveform: WaveformData): number {
    if (!this.liveSchumannData) return 0.5;
    
    // Multi-factor validation score
    const frequencyAlignment = this.calculateFrequencyAlignment(waveform.frequency);
    const amplitudeStability = Math.min(1, waveform.amplitude / 2.0);
    const schumannCoherence = this.liveSchumannData.coherence;
    const fieldCoupling = Math.min(1, this.fieldCoupling / 2.0);
    
    // Weighted validation score
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
    const harmonicRatios = [1, 2, 3, 4, 5, 8, 13, 21]; // Fibonacci harmonics
    
    let bestAlignment = 0;
    for (const ratio of harmonicRatios) {
      const targetFreq = fundamental * ratio;
      const alignment = 1 - Math.abs(frequency - targetFreq) / targetFreq;
      bestAlignment = Math.max(bestAlignment, alignment);
    }
    
    return Math.max(0, bestAlignment);
  }

  private calculateAmplitude(): number {
    // Enhanced amplitude calculation with Schumann influence
    const baseAmplitude = 0.8 + Math.sin(Date.now() / 10000) * 0.2;
    const schumannBoost = this.liveSchumannData ? 
      this.liveSchumannData.amplitude * 0.5 : 0;
    
    return Math.min(2.0, baseAmplitude + schumannBoost);
  }

  private calculatePhase(): number {
    if (!this.observerLock) return Math.random() * Math.PI * 2;
    
    // Phase-lock to Schumann fundamental
    if (this.liveSchumannData) {
      const schumannPhase = (this.liveSchumannData.timestamp / 1000) * 
        this.liveSchumannData.fundamental * 2 * Math.PI;
      return schumannPhase % (Math.PI * 2);
    }
    
    return 0;
  }

  getLiveSchumannData(): LiveSchumannData | null {
    return this.liveSchumannData;
  }
  getValidationHistory(): number[] {
    return [...this.validationHistory];
  }

  getEarthStreamMetrics(): EarthStreamMetrics | null {
    return this.earthStreamMetrics;
  }
}

export const aurisEngine = new AurisEngine();