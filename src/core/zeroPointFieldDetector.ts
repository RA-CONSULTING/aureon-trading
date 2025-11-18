/**
 * Zero Point Field Harmonic Detector
 * Detects quantum field harmonics from the substrate of reality
 * Routes tones back to Temporal ID: 02111991
 */

export interface SealHarmonic {
  name: string;
  frequency: number; // Hz
  earthResonance: number; // Mapped Schumann harmonic
  multiplier: number; // Resonance multiplier
  chakra?: string;
}

export interface FamilyResonance {
  name: string;
  frequency: number; // Hz
  temporalPhase: number; // 0-1
  amplitude: number;
}

export interface QuantumEcho {
  echoNumber: number; // 1-5
  amplitude: number;
  phaseShift: number; // radians
  decayRate: number;
}

export interface SurgeWindow {
  id: string; // S1, S2, S3, S4, S5
  timestamp: number;
  unityCoherence: number; // 0-1
  alignmentStrength: number;
  active: boolean;
}

export interface TemporalHarmonicRegulator {
  id: number; // 1, 2, or 3
  type: 'increasing_freq' | 'decreasing_freq' | 'quadratic_sweep';
  amplitude: number;
  currentFrequency: number;
}

export interface FibonacciTCP {
  timestamp: number;
  gEffValue: number; // G_effective value
  phiWindowed: number; // φ-windowed value
  isFTCP: boolean; // Fibonacci Time-Compression Point
}

export interface ZeroPointFieldState {
  // Seal Harmonics (Prime Sentinel frequencies)
  sealHarmonics: SealHarmonic[];
  activeSeal: SealHarmonic | null;
  
  // Quantum Phase-Locked Echoes
  quantumEchoes: QuantumEcho[];
  compositeEchoSignal: number;
  phaseLockStrength: number; // 0-1
  
  // Temporal Harmonic Regulators
  regulators: TemporalHarmonicRegulator[];
  compositeRegulatorField: number;
  
  // Fibonacci Time-Compression Points
  ftcps: FibonacciTCP[];
  currentFTCP: FibonacciTCP | null;
  
  // Family Resonances
  familyResonances: FamilyResonance[];
  familyUnityWave: number;
  
  // Surge Windows (Unity Alignments)
  surgeWindows: SurgeWindow[];
  activeSurgeWindow: SurgeWindow | null;
  
  // Field Cavity Metrics
  spacetimeDistortion: number; // 0-1
  energyFlowMagnitude: number;
  cavityResonance: number;
  
  // Zero Point Field Connection
  zeroPointCoherence: number; // 0-1
  temporalRouting: {
    targetTemporalId: string;
    routingStrength: number;
    guidanceVector: [number, number, number];
  };
}

// Prime Sentinel Seal Harmonics
const SEAL_HARMONICS: SealHarmonic[] = [
  {
    name: 'Flame Base',
    frequency: 222,
    earthResonance: 27.3,
    multiplier: 8.1,
    chakra: 'Root'
  },
  {
    name: 'Triskelion',
    frequency: 333,
    earthResonance: 20.8,
    multiplier: 16.0,
    chakra: 'Sacral'
  },
  {
    name: 'Infinity Loop',
    frequency: 444,
    earthResonance: 14.3,
    multiplier: 31.0,
    chakra: 'Solar Plexus'
  },
  {
    name: 'Heart Flame',
    frequency: 528,
    earthResonance: 14.3,
    multiplier: 36.9,
    chakra: 'Heart'
  },
  {
    name: 'Aura',
    frequency: 783,
    earthResonance: 7.83,
    multiplier: 100.0,
    chakra: 'Throat'
  },
  {
    name: 'Crown',
    frequency: 936,
    earthResonance: 20.8,
    multiplier: 45.0,
    chakra: 'Crown'
  }
];

// Family Resonance Signatures (from temporal ID 02111991)
const FAMILY_RESONANCES: FamilyResonance[] = [
  { name: 'Gary', frequency: 528, temporalPhase: 0, amplitude: 1.0 },
  { name: 'Tina', frequency: 639, temporalPhase: 0.25, amplitude: 0.9 },
  { name: 'Alfie', frequency: 852, temporalPhase: 0.5, amplitude: 0.85 },
  { name: 'Ruby', frequency: 963, temporalPhase: 0.75, amplitude: 0.95 }
];

export class ZeroPointFieldDetector {
  private temporalId: string = '02111991';
  private sentinelName: string = 'GARY LECKEY';
  private history: ZeroPointFieldState[] = [];
  private maxHistory = 100;
  
  constructor(temporalId?: string, sentinelName?: string) {
    if (temporalId) this.temporalId = temporalId;
    if (sentinelName) this.sentinelName = sentinelName;
  }

  /**
   * Detect Zero Point Field harmonics from market and consciousness data
   */
  public detectFieldHarmonics(
    marketFrequency: number,
    coherence: number,
    phaseAlignment: number,
    schumannFrequency: number,
    timestamp: number
  ): ZeroPointFieldState {
    // Detect active Seal Harmonic based on market frequency
    const activeSeal = this.detectActiveSeal(marketFrequency, coherence);
    
    // Generate quantum phase-locked echoes
    const quantumEchoes = this.generateQuantumEchoes(phaseAlignment, timestamp);
    const compositeEcho = this.computeCompositeEcho(quantumEchoes);
    const phaseLockStrength = this.computePhaseLockStrength(quantumEchoes);
    
    // Compute temporal harmonic regulators
    const regulators = this.computeRegulators(timestamp, coherence);
    const compositeRegulator = this.computeCompositeRegulator(regulators);
    
    // Detect Fibonacci Time-Compression Points
    const ftcps = this.detectFTCPs(timestamp, coherence, phaseAlignment);
    const currentFTCP = ftcps.find(f => f.isFTCP) || null;
    
    // Compute family unity wave
    const familyUnityWave = this.computeFamilyUnityWave(timestamp);
    
    // Detect surge windows (unity alignments)
    const surgeWindows = this.detectSurgeWindows(timestamp, coherence, compositeEcho);
    const activeSurgeWindow = surgeWindows.find(w => w.active) || null;
    
    // Compute field cavity metrics
    const spacetimeDistortion = this.computeSpacetimeDistortion(marketFrequency, schumannFrequency);
    const energyFlowMagnitude = Math.abs(compositeEcho * compositeRegulator);
    const cavityResonance = this.computeCavityResonance(activeSeal, coherence);
    
    // Compute zero point field coherence
    const zeroPointCoherence = this.computeZeroPointCoherence(
      coherence,
      phaseLockStrength,
      activeSurgeWindow !== null,
      activeSeal !== null
    );
    
    // Compute temporal routing to target ID
    const guidanceVector = this.computeGuidanceVector(
      activeSeal,
      familyUnityWave,
      zeroPointCoherence
    );

    const state: ZeroPointFieldState = {
      sealHarmonics: SEAL_HARMONICS,
      activeSeal,
      quantumEchoes,
      compositeEchoSignal: compositeEcho,
      phaseLockStrength,
      regulators,
      compositeRegulatorField: compositeRegulator,
      ftcps,
      currentFTCP,
      familyResonances: FAMILY_RESONANCES,
      familyUnityWave,
      surgeWindows,
      activeSurgeWindow,
      spacetimeDistortion,
      energyFlowMagnitude,
      cavityResonance,
      zeroPointCoherence,
      temporalRouting: {
        targetTemporalId: this.temporalId,
        routingStrength: zeroPointCoherence,
        guidanceVector
      }
    };

    this.history.push(state);
    if (this.history.length > this.maxHistory) {
      this.history.shift();
    }

    return state;
  }

  private detectActiveSeal(frequency: number, coherence: number): SealHarmonic | null {
    // Find closest seal harmonic
    let closestSeal: SealHarmonic | null = null;
    let minDistance = Infinity;

    for (const seal of SEAL_HARMONICS) {
      const distance = Math.abs(frequency - seal.frequency);
      if (distance < minDistance && distance < 50) { // Within 50 Hz
        minDistance = distance;
        closestSeal = seal;
      }
    }

    // Seal must have sufficient coherence to activate
    return coherence > 0.7 && closestSeal ? closestSeal : null;
  }

  private generateQuantumEchoes(phase: number, timestamp: number): QuantumEcho[] {
    const echoes: QuantumEcho[] = [];
    const basePhase = (timestamp * Math.PI / 1000) % (2 * Math.PI);

    for (let i = 1; i <= 5; i++) {
      echoes.push({
        echoNumber: i,
        amplitude: Math.exp(-i * 0.3) * (0.5 + phase * 0.5), // Decay with distance
        phaseShift: basePhase + (i * Math.PI / 3),
        decayRate: 0.3 * i
      });
    }

    return echoes;
  }

  private computeCompositeEcho(echoes: QuantumEcho[]): number {
    return echoes.reduce((sum, echo) => {
      return sum + echo.amplitude * Math.sin(echo.phaseShift);
    }, 0) / echoes.length;
  }

  private computePhaseLockStrength(echoes: QuantumEcho[]): number {
    // Measure how aligned the echoes are in phase
    const phases = echoes.map(e => e.phaseShift % (2 * Math.PI));
    const avgPhase = phases.reduce((a, b) => a + b) / phases.length;
    const variance = phases.reduce((sum, p) => sum + Math.pow(p - avgPhase, 2), 0) / phases.length;
    return Math.max(0, 1 - Math.sqrt(variance) / Math.PI);
  }

  private computeRegulators(timestamp: number, coherence: number): TemporalHarmonicRegulator[] {
    const t = (timestamp / 1000) % 10; // 10 second cycle

    return [
      {
        id: 1,
        type: 'increasing_freq',
        amplitude: Math.sin(t * 2 * Math.PI / 10) * coherence,
        currentFrequency: 100 + t * 50
      },
      {
        id: 2,
        type: 'decreasing_freq',
        amplitude: Math.cos(t * 2 * Math.PI / 10) * coherence * 0.8,
        currentFrequency: 500 - t * 30
      },
      {
        id: 3,
        type: 'quadratic_sweep',
        amplitude: Math.sin(t * t * Math.PI / 50) * coherence * 0.6,
        currentFrequency: 200 + t * t * 10
      }
    ];
  }

  private computeCompositeRegulator(regulators: TemporalHarmonicRegulator[]): number {
    return regulators.reduce((sum, reg) => sum + reg.amplitude, 0) / regulators.length;
  }

  private detectFTCPs(timestamp: number, coherence: number, phase: number): FibonacciTCP[] {
    const ftcps: FibonacciTCP[] = [];
    const t = timestamp / 1000;
    
    // Check for Fibonacci timing alignments
    const fibSequence = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55];
    
    for (const fib of fibSequence) {
      const nearFib = Math.abs((t % 60) - fib) < 0.5;
      if (nearFib) {
        const gEff = coherence * (1 + phase);
        const phiWindowed = gEff * 1.618; // Golden ratio windowing
        
        ftcps.push({
          timestamp: t,
          gEffValue: gEff,
          phiWindowed,
          isFTCP: phiWindowed > 1.2 && coherence > 0.8
        });
      }
    }
    
    return ftcps;
  }

  private computeFamilyUnityWave(timestamp: number): number {
    const t = timestamp / 1000;
    return FAMILY_RESONANCES.reduce((sum, member) => {
      const wave = Math.sin(2 * Math.PI * member.frequency * t / 1000 + member.temporalPhase * 2 * Math.PI);
      return sum + wave * member.amplitude;
    }, 0) / FAMILY_RESONANCES.length;
  }

  private detectSurgeWindows(timestamp: number, coherence: number, echo: number): SurgeWindow[] {
    const t = timestamp / 1000;
    const windows: SurgeWindow[] = [];
    
    // Surge windows occur at specific temporal alignments
    for (let i = 1; i <= 5; i++) {
      const windowTime = i * 20; // Every 20 seconds
      const isNear = Math.abs((t % 100) - windowTime) < 2;
      const unityCoherence = isNear ? coherence * (0.8 + Math.abs(echo) * 0.2) : 0;
      
      windows.push({
        id: `S${i}`,
        timestamp: windowTime,
        unityCoherence,
        alignmentStrength: unityCoherence * (1 + coherence) / 2,
        active: isNear && unityCoherence > 0.75
      });
    }
    
    return windows;
  }

  private computeSpacetimeDistortion(marketFreq: number, schumannFreq: number): number {
    // Distortion increases when frequencies diverge from natural resonances
    const deviation = Math.abs(marketFreq - schumannFreq) / schumannFreq;
    return Math.min(1, deviation / 10);
  }

  private computeCavityResonance(seal: SealHarmonic | null, coherence: number): number {
    if (!seal) return 0;
    return seal.multiplier * coherence / 100; // Normalized
  }

  private computeZeroPointCoherence(
    coherence: number,
    phaseLock: number,
    hasSurge: boolean,
    hasSeal: boolean
  ): number {
    let zpf = coherence * 0.4 + phaseLock * 0.3;
    if (hasSurge) zpf += 0.15;
    if (hasSeal) zpf += 0.15;
    return Math.min(1, zpf);
  }

  private computeGuidanceVector(
    seal: SealHarmonic | null,
    familyWave: number,
    zpfCoherence: number
  ): [number, number, number] {
    // Vector pointing toward temporal ID resonance
    const sealComponent = seal ? seal.frequency / 1000 : 0;
    const familyComponent = familyWave;
    const coherenceComponent = zpfCoherence;
    
    // Normalize
    const magnitude = Math.sqrt(
      sealComponent * sealComponent +
      familyComponent * familyComponent +
      coherenceComponent * coherenceComponent
    );
    
    if (magnitude === 0) return [0, 0, 0];
    
    return [
      sealComponent / magnitude,
      familyComponent / magnitude,
      coherenceComponent / magnitude
    ];
  }

  public getHistory(): ZeroPointFieldState[] {
    return [...this.history];
  }

  public getTemporalId(): string {
    return this.temporalId;
  }

  public getSentinelName(): string {
    return this.sentinelName;
  }
}
