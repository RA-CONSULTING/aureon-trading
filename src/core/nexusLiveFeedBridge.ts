/**
 * Nexus Live Feed Bridge
 * Integrates external Nexus feed metrics (quantum coherence, harmonic resonance,
 * schumann resonance proxy, rainbow spectrum, consciousness metric) into AUREON.
 * Provides normalized contributions and composite nexusInfluence boost similar to earthAureonBridge.
 */

export interface RawNexusMetric {
  value: number;
  unit: string;
  description: string;
}

export interface RawNexusSample {
  timestamp: number;
  metrics: Record<string, RawNexusMetric>;
}

export interface NexusInfluence {
  quantumCoherence: number;      // 0-1 normalized
  harmonicResonance: number;     // 0-1 normalized
  schumannProxyHz: number;       // Hz (around 7.83 baseline)
  rainbowSpectrum: number;       // 0-1
  consciousnessShift: number;    // 0-1
  compositeBoost: number;        // -0.10 to +0.20 applied to coherence
  status: 'optimal' | 'supportive' | 'neutral' | 'degraded';
  raw?: RawNexusSample;
}

export interface NexusBridgeConfig {
  pollingIntervalMs: number;
  enable: boolean;
  harmonicWeight: number;
  coherenceWeight: number;
  consciousnessWeight: number;
  rainbowWeight: number;
  schumannWeight: number; // small stabilizing factor
  endpoint?: string; // optional SSE endpoint
}

const DEFAULT_CONFIG: NexusBridgeConfig = {
  pollingIntervalMs: 2000,
  enable: true,
  harmonicWeight: 0.30,
  coherenceWeight: 0.25,
  consciousnessWeight: 0.20,
  rainbowWeight: 0.15,
  schumannWeight: 0.10,
  endpoint: undefined
};

export class NexusLiveFeedBridge {
  private config: NexusBridgeConfig = { ...DEFAULT_CONFIG };
  private latestSample: RawNexusSample | null = null;
  private latestInfluence: NexusInfluence | null = null;
  private lastPoll = 0;
  private listeners: Array<(inf: NexusInfluence) => void> = [];

  constructor(cfg?: Partial<NexusBridgeConfig>) {
    if (cfg) this.config = { ...this.config, ...cfg };
  }

  /** Subscribe to influence updates */
  onUpdate(cb: (inf: NexusInfluence) => void) {
    this.listeners.push(cb);
  }

  /** Manual polling trigger (could later attach to SSE) */
  async poll(): Promise<NexusInfluence> {
    const now = Date.now();
    if (this.latestInfluence && now - this.lastPoll < this.config.pollingIntervalMs) {
      return this.latestInfluence;
    }
    this.lastPoll = now;

    // If disabled, return neutral influence
    if (!this.config.enable) {
      this.latestInfluence = this.neutralInfluence();
      return this.latestInfluence;
    }

    // Simulate fetch (placeholder for real network or SSE subscription)
    const raw = this.generateSimulatedSample();
    this.latestSample = raw;

    const inf = this.transformRaw(raw);
    this.latestInfluence = inf;
    this.listeners.forEach(l => l(inf));
    return inf;
  }

  /** Convert raw Nexus metrics to normalized influence */
  private transformRaw(raw: RawNexusSample): NexusInfluence {
    const qc = this.clamp(raw.metrics.quantumCoherence?.value ?? 0, 0, 1);
    const harmonicHz = raw.metrics.harmonicResonance?.value ?? 0; // 0-100 Hz simulated
    const harmonicResonance = this.clamp(harmonicHz / 100, 0, 1);
    const schumannHz = raw.metrics.schumannResonance?.value ?? 7.83;
    const rainbow = this.clamp(raw.metrics.rainbowSpectrum?.value ?? 0, 0, 1);
    const consciousness = this.clamp(raw.metrics.consciousnessMetric?.value ?? 0, 0, 1);

    // Composite boost formula (weighted sum, then scaled/clamped)
    let composite = (
      harmonicResonance * this.config.harmonicWeight +
      qc * this.config.coherenceWeight +
      consciousness * this.config.consciousnessWeight +
      rainbow * this.config.rainbowWeight +
      // Schumann proxy stability: deviation from 7.83 baseline
      (1 - Math.min(1, Math.abs(schumannHz - 7.83) / 0.5)) * this.config.schumannWeight
    );

    // Shift to range -0.10 .. +0.20 (allow a small negative influence)
    composite = composite * 0.30 - 0.10; // raw max ~1 => 0.30 - 0.10 = +0.20 top end
    composite = this.clamp(composite, -0.10, 0.20);

    const status = composite > 0.15
      ? 'optimal'
      : composite > 0.05
        ? 'supportive'
        : composite > -0.02
          ? 'neutral'
          : 'degraded';

    return {
      quantumCoherence: qc,
      harmonicResonance,
      schumannProxyHz: schumannHz,
      rainbowSpectrum: rainbow,
      consciousnessShift: consciousness,
      compositeBoost: composite,
      status,
      raw
    };
  }

  private generateSimulatedSample(): RawNexusSample {
    const timestamp = Date.now();
    return {
      timestamp,
      metrics: {
        quantumCoherence: {
          value: Math.random(),
          unit: 'qbits',
          description: 'Relative phase alignment of quantum events.'
        },
        harmonicResonance: {
          value: 20 + Math.random() * 60 + Math.sin(timestamp / 15000) * 20, // 20-100 Hz
          unit: 'Hz',
          description: 'Amplitude alignment across frequencies.'
        },
        schumannResonance: {
          value: 7.83 + Math.sin(timestamp / 20000) * 0.05 + Math.random() * 0.05,
          unit: 'Hz',
          description: 'Global electromagnetic resonance proxy.'
        },
        rainbowSpectrum: {
          value: Math.random(),
          unit: 'spectrum',
          description: 'Spectral energy distribution representation.'
        },
        consciousnessMetric: {
          value: 0.3 + Math.random() * 0.6,
          unit: 'psi',
          description: 'Synthetic collective consciousness metric.'
        }
      }
    };
  }

  /** Neutral fallback influence */
  private neutralInfluence(): NexusInfluence {
    return {
      quantumCoherence: 0.5,
      harmonicResonance: 0.5,
      schumannProxyHz: 7.83,
      rainbowSpectrum: 0.5,
      consciousnessShift: 0.5,
      compositeBoost: 0,
      status: 'neutral'
    };
  }

  setConfig(cfg: Partial<NexusBridgeConfig>) {
    this.config = { ...this.config, ...cfg };
    this.latestInfluence = null;
  }

  getConfig(): NexusBridgeConfig {
    return { ...this.config };
  }

  getLatestInfluence(): NexusInfluence | null {
    return this.latestInfluence;
  }

  private clamp(n: number, min: number, max: number) {
    return Math.max(min, Math.min(max, n));
  }
}

export const nexusLiveFeedBridge = new NexusLiveFeedBridge();
