/**
 * Quantum Telescope - Geometric Light Analysis Engine
 * 
 * Observes market data as "light beams" and refracts them through
 * 5 Platonic solid lenses for geometric probability analysis.
 * 
 * The Telescope feeds geometric alignment into The Prism,
 * creating a unified observation → transformation pipeline.
 * 
 * Platonic Solids (5 Lenses):
 * 1. Tetrahedron (Fire) - Momentum/volatility analysis
 * 2. Hexahedron/Cube (Earth) - Stability/support analysis
 * 3. Octahedron (Air) - Velocity/trend analysis
 * 4. Icosahedron (Water) - Flow/liquidity analysis
 * 5. Dodecahedron (Ether) - Coherence/unity analysis
 */

import { temporalLadder, SYSTEMS, type SystemName } from './temporalLadder';
import { unifiedBus, type SignalType } from './unifiedBus';

// Sacred geometry constants
const PHI = (1 + Math.sqrt(5)) / 2; // Golden ratio ≈ 1.618
const SQRT_2 = Math.sqrt(2);
const SQRT_3 = Math.sqrt(3);
const SQRT_5 = Math.sqrt(5);

// Platonic solid enumeration
export enum GeometricSolid {
  Tetrahedron = 'Tetrahedron',   // Fire - 4 faces
  Hexahedron = 'Hexahedron',     // Earth - 6 faces (Cube)
  Octahedron = 'Octahedron',     // Air - 8 faces
  Icosahedron = 'Icosahedron',   // Water - 20 faces
  Dodecahedron = 'Dodecahedron', // Ether - 12 faces
}

// Light beam from market observation
export interface LightBeam {
  intensity: number;      // Derived from volume
  wavelength: number;     // Derived from price level
  velocity: number;       // Derived from momentum
  angle: number;          // Derived from trend direction
  polarization: number;   // Derived from volatility
}

// Result of refracting through a single lens
export interface RefractionResult {
  solid: GeometricSolid;
  refractiveIndex: number;  // How much the lens bends the beam
  dispersion: number;       // Spread of the refracted light
  focalPoint: number;       // Where the beam focuses (-1 to 1)
  clarity: number;          // Quality of the refraction (0-1)
  resonance: number;        // Harmonic alignment with the solid (0-1)
}

// Complete telescope observation
export interface TelescopeObservation {
  timestamp: number;
  symbol: string;
  lightBeam: LightBeam;
  refractions: RefractionResult[];
  geometricAlignment: number;     // Overall alignment across all solids (0-1)
  dominantSolid: GeometricSolid;  // Which solid has strongest resonance
  probabilitySpectrum: number[];  // 5 probability values per solid
  holographicProjection: {        // Price target projection
    direction: 'UP' | 'DOWN' | 'NEUTRAL';
    magnitude: number;
    confidence: number;
  };
  focalCoherence: number;         // Combined focal alignment (0-1)
  prismBoostFactor: number;       // Multiplier for Prism integration
}

// Market snapshot input (compatible with existing types)
export interface MarketInput {
  price: number;
  volume: number;
  volatility: number;
  momentum: number;
  spread?: number;
  high24h?: number;
  low24h?: number;
}

/**
 * QuantumPrism - Individual geometric lens
 */
class QuantumLens {
  constructor(
    public readonly solid: GeometricSolid,
    private readonly faces: number,
    private readonly vertices: number,
    private readonly edges: number,
    private readonly element: string,
  ) {}

  /**
   * Refract a light beam through this geometric lens
   */
  refract(beam: LightBeam): RefractionResult {
    // Base refractive index from geometric properties
    const geometricFactor = (this.faces + this.vertices) / this.edges;
    const refractiveIndex = geometricFactor * PHI;

    // Dispersion based on beam polarization and solid complexity
    const dispersion = beam.polarization * (this.faces / 20);

    // Focal point calculation using solid-specific logic
    const focalPoint = this.calculateFocalPoint(beam);

    // Clarity from beam intensity and geometric harmony
    const clarity = this.calculateClarity(beam);

    // Resonance - how well beam harmonizes with this solid
    const resonance = this.calculateResonance(beam);

    return {
      solid: this.solid,
      refractiveIndex,
      dispersion,
      focalPoint,
      clarity,
      resonance,
    };
  }

  private calculateFocalPoint(beam: LightBeam): number {
    switch (this.solid) {
      case GeometricSolid.Tetrahedron:
        // Fire: Responds to momentum (velocity)
        return Math.tanh(beam.velocity * 2);
      case GeometricSolid.Hexahedron:
        // Earth: Responds to stability (inverse volatility)
        return Math.tanh((1 - beam.polarization) * 2 - 1);
      case GeometricSolid.Octahedron:
        // Air: Responds to angle (trend direction)
        return Math.sin(beam.angle * Math.PI / 180);
      case GeometricSolid.Icosahedron:
        // Water: Responds to flow (intensity/volume)
        return Math.tanh(beam.intensity - 0.5);
      case GeometricSolid.Dodecahedron:
        // Ether: Responds to wavelength harmony
        return Math.cos(beam.wavelength * Math.PI);
      default:
        return 0;
    }
  }

  private calculateClarity(beam: LightBeam): number {
    // Higher intensity = clearer image
    const intensityFactor = Math.min(beam.intensity, 1);
    
    // Lower polarization (volatility) = clearer
    const stabilityFactor = 1 - beam.polarization * 0.5;
    
    // Geometric harmony factor
    const harmonyFactor = Math.abs(Math.sin(this.faces * beam.wavelength * Math.PI));
    
    return (intensityFactor * 0.4 + stabilityFactor * 0.3 + harmonyFactor * 0.3);
  }

  private calculateResonance(beam: LightBeam): number {
    // Each solid resonates with specific beam characteristics
    switch (this.solid) {
      case GeometricSolid.Tetrahedron:
        // Fire resonates with high velocity and polarization
        return (Math.abs(beam.velocity) * 0.6 + beam.polarization * 0.4);
      case GeometricSolid.Hexahedron:
        // Earth resonates with stability and consistent intensity
        return ((1 - beam.polarization) * 0.7 + beam.intensity * 0.3);
      case GeometricSolid.Octahedron:
        // Air resonates with clear direction and velocity
        return (Math.abs(Math.sin(beam.angle * Math.PI / 180)) * 0.5 + Math.abs(beam.velocity) * 0.5);
      case GeometricSolid.Icosahedron:
        // Water resonates with high intensity (volume/liquidity)
        return (beam.intensity * 0.8 + beam.wavelength * 0.2);
      case GeometricSolid.Dodecahedron:
        // Ether resonates with harmonic wavelength patterns (PHI alignment)
        const phiHarmony = 1 - Math.abs((beam.wavelength * PHI) % 1 - 0.5) * 2;
        return (phiHarmony * 0.6 + (1 - beam.polarization) * 0.4);
      default:
        return 0;
    }
  }
}

/**
 * QuantumTelescope - Main observation engine
 */
export class QuantumTelescope {
  private readonly lenses: QuantumLens[];
  private readonly systemName: SystemName = 'quantum-quackers'; // Register under quantum system
  private lastObservation: TelescopeObservation | null = null;

  constructor() {
    // Initialize 5 Platonic solid lenses
    this.lenses = [
      new QuantumLens(GeometricSolid.Tetrahedron, 4, 4, 6, 'Fire'),
      new QuantumLens(GeometricSolid.Hexahedron, 6, 8, 12, 'Earth'),
      new QuantumLens(GeometricSolid.Octahedron, 8, 6, 12, 'Air'),
      new QuantumLens(GeometricSolid.Icosahedron, 20, 12, 30, 'Water'),
      new QuantumLens(GeometricSolid.Dodecahedron, 12, 20, 30, 'Ether'),
    ];
  }

  /**
   * Convert market data into a light beam for observation
   */
  createLightBeam(market: MarketInput): LightBeam {
    // Intensity from volume (normalized)
    const intensity = Math.min(market.volume / 1000000, 1);

    // Wavelength from price level (normalized to 0-1 cycle)
    const priceRange = (market.high24h || market.price * 1.1) - (market.low24h || market.price * 0.9);
    const wavelength = priceRange > 0 
      ? ((market.price - (market.low24h || market.price * 0.9)) / priceRange)
      : 0.5;

    // Velocity from momentum (-1 to 1)
    const velocity = Math.tanh(market.momentum * 10);

    // Angle from price position (degrees, -90 to 90)
    const angle = velocity * 90;

    // Polarization from volatility (0-1)
    const polarization = Math.min(market.volatility * 10, 1);

    return { intensity, wavelength, velocity, angle, polarization };
  }

  /**
   * Observe market through the quantum telescope
   */
  observe(market: MarketInput, symbol: string = 'BTCUSDT'): TelescopeObservation {
    const timestamp = Date.now();
    const lightBeam = this.createLightBeam(market);

    // Refract through all 5 lenses
    const refractions = this.lenses.map(lens => lens.refract(lightBeam));

    // Calculate probability spectrum (resonance per solid)
    const probabilitySpectrum = refractions.map(r => r.resonance);

    // Find dominant solid (highest resonance)
    const maxResonance = Math.max(...probabilitySpectrum);
    const dominantIndex = probabilitySpectrum.indexOf(maxResonance);
    const dominantSolid = refractions[dominantIndex].solid;

    // Calculate geometric alignment (weighted average of resonances)
    // Dodecahedron (Ether) has highest weight as it represents unity
    const weights = [0.15, 0.15, 0.15, 0.20, 0.35]; // Fire, Earth, Air, Water, Ether
    const geometricAlignment = probabilitySpectrum.reduce((sum, r, i) => sum + r * weights[i], 0);

    // Calculate focal coherence (agreement of focal points)
    const focalPoints = refractions.map(r => r.focalPoint);
    const avgFocal = focalPoints.reduce((a, b) => a + b, 0) / focalPoints.length;
    const focalVariance = focalPoints.reduce((sum, f) => sum + Math.pow(f - avgFocal, 2), 0) / focalPoints.length;
    const focalCoherence = 1 - Math.min(focalVariance, 1);

    // Holographic projection (price direction prediction)
    const holographicProjection = this.computeHolographicProjection(refractions, focalCoherence);

    // Prism boost factor (how much this observation should boost Prism transformation)
    // Higher geometric alignment = faster 528 Hz convergence
    const prismBoostFactor = 1 + (geometricAlignment - 0.5) * 0.4;

    const observation: TelescopeObservation = {
      timestamp,
      symbol,
      lightBeam,
      refractions,
      geometricAlignment,
      dominantSolid,
      probabilitySpectrum,
      holographicProjection,
      focalCoherence,
      prismBoostFactor,
    };

    this.lastObservation = observation;
    return observation;
  }

  /**
   * Compute holographic projection from refractions
   */
  private computeHolographicProjection(
    refractions: RefractionResult[],
    focalCoherence: number
  ): TelescopeObservation['holographicProjection'] {
    // Weighted sum of focal points
    const weights = [0.25, 0.15, 0.20, 0.20, 0.20];
    const weightedFocal = refractions.reduce((sum, r, i) => sum + r.focalPoint * weights[i], 0);

    // Direction based on weighted focal
    let direction: 'UP' | 'DOWN' | 'NEUTRAL';
    if (weightedFocal > 0.1) direction = 'UP';
    else if (weightedFocal < -0.1) direction = 'DOWN';
    else direction = 'NEUTRAL';

    // Magnitude from focal strength
    const magnitude = Math.abs(weightedFocal);

    // Confidence from coherence and clarity
    const avgClarity = refractions.reduce((sum, r) => sum + r.clarity, 0) / refractions.length;
    const confidence = (focalCoherence * 0.6 + avgClarity * 0.4);

    return { direction, magnitude, confidence };
  }

  /**
   * Register with Temporal Ladder and publish to UnifiedBus
   */
  registerAndPublish(observation: TelescopeObservation): void {
    // Register with Temporal Ladder
    temporalLadder.registerSystem(this.systemName);
    temporalLadder.heartbeat(this.systemName, observation.geometricAlignment);

    // Determine signal from holographic projection
    let signal: SignalType = 'NEUTRAL';
    if (observation.holographicProjection.direction === 'UP' && observation.holographicProjection.confidence > 0.6) {
      signal = 'BUY';
    } else if (observation.holographicProjection.direction === 'DOWN' && observation.holographicProjection.confidence > 0.6) {
      signal = 'SELL';
    }

    // Publish to UnifiedBus
    unifiedBus.publish({
      systemName: 'QuantumTelescope',
      timestamp: observation.timestamp,
      ready: true,
      coherence: observation.focalCoherence,
      confidence: observation.holographicProjection.confidence,
      signal,
      data: {
        geometricAlignment: observation.geometricAlignment,
        dominantSolid: observation.dominantSolid,
        probabilitySpectrum: observation.probabilitySpectrum,
        holographicProjection: observation.holographicProjection,
        prismBoostFactor: observation.prismBoostFactor,
      },
    });

    // Broadcast to hive mind
    temporalLadder.broadcast(
      this.systemName,
      'TELESCOPE_OBSERVATION',
      {
        geometricAlignment: observation.geometricAlignment,
        dominantSolid: observation.dominantSolid,
        direction: observation.holographicProjection.direction,
      }
    );
  }

  /**
   * Get last observation
   */
  getLastObservation(): TelescopeObservation | null {
    return this.lastObservation;
  }

  /**
   * Synthesize multiple observations into a probability field
   */
  synthesize(observations: TelescopeObservation[]): {
    meanAlignment: number;
    alignmentTrend: number;
    dominantSolidFrequency: Record<GeometricSolid, number>;
    consensusDirection: 'UP' | 'DOWN' | 'NEUTRAL';
    consensusConfidence: number;
  } {
    if (observations.length === 0) {
      return {
        meanAlignment: 0,
        alignmentTrend: 0,
        dominantSolidFrequency: {
          [GeometricSolid.Tetrahedron]: 0,
          [GeometricSolid.Hexahedron]: 0,
          [GeometricSolid.Octahedron]: 0,
          [GeometricSolid.Icosahedron]: 0,
          [GeometricSolid.Dodecahedron]: 0,
        },
        consensusDirection: 'NEUTRAL',
        consensusConfidence: 0,
      };
    }

    // Calculate mean alignment
    const meanAlignment = observations.reduce((sum, o) => sum + o.geometricAlignment, 0) / observations.length;

    // Calculate alignment trend (last - first)
    const alignmentTrend = observations.length > 1
      ? observations[observations.length - 1].geometricAlignment - observations[0].geometricAlignment
      : 0;

    // Count dominant solid frequency
    const dominantSolidFrequency: Record<GeometricSolid, number> = {
      [GeometricSolid.Tetrahedron]: 0,
      [GeometricSolid.Hexahedron]: 0,
      [GeometricSolid.Octahedron]: 0,
      [GeometricSolid.Icosahedron]: 0,
      [GeometricSolid.Dodecahedron]: 0,
    };
    observations.forEach(o => {
      dominantSolidFrequency[o.dominantSolid]++;
    });

    // Consensus direction
    let upVotes = 0, downVotes = 0;
    observations.forEach(o => {
      if (o.holographicProjection.direction === 'UP') upVotes += o.holographicProjection.confidence;
      else if (o.holographicProjection.direction === 'DOWN') downVotes += o.holographicProjection.confidence;
    });

    let consensusDirection: 'UP' | 'DOWN' | 'NEUTRAL' = 'NEUTRAL';
    if (upVotes > downVotes * 1.2) consensusDirection = 'UP';
    else if (downVotes > upVotes * 1.2) consensusDirection = 'DOWN';

    const consensusConfidence = Math.abs(upVotes - downVotes) / (upVotes + downVotes + 0.001);

    return {
      meanAlignment,
      alignmentTrend,
      dominantSolidFrequency,
      consensusDirection,
      consensusConfidence,
    };
  }
}

// Singleton instance
export const quantumTelescope = new QuantumTelescope();
