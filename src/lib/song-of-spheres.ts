// Song of the Spheres - Planetary modulator calculations
// Maps orbital periods to ultra-low frequency modulators for harmonic synthesis

export interface PlanetaryData {
  name: string;
  orbital_period_days: number;
  frequency_hz: number;
  weight: number;
  phase_offset: number;
  targets: string[];
}

export interface SynodicBeat {
  name: string;
  period_years: number;
  frequency_hz: number;
  weight: number;
  target: string;
}

export class SongOfSpheresEngine {
  private startTime: number;
  private planetaryData: Map<string, PlanetaryData>;
  private synodicBeats: Map<string, SynodicBeat>;
  
  constructor() {
    this.startTime = Date.now();
    this.planetaryData = new Map();
    this.synodicBeats = new Map();
    this.initializePlanets();
    this.initializeSynodics();
  }

  private initializePlanets() {
    const planets: PlanetaryData[] = [
      {
        name: 'mercury',
        orbital_period_days: 88,
        frequency_hz: 0.000131,
        weight: 0.15,
        phase_offset: 0,
        targets: ['harmonic_weights', 'color_palette']
      },
      {
        name: 'venus',
        orbital_period_days: 225,
        frequency_hz: 0.0000514,
        weight: 0.25,
        phase_offset: 120,
        targets: ['harmonic_weights', 'phase_bias']
      },
      {
        name: 'earth',
        orbital_period_days: 365.25,
        frequency_hz: 0.0000317,
        weight: 1.0,
        phase_offset: 0,
        targets: ['fundamental', 'color_palette', 'phase_bias']
      },
      {
        name: 'mars',
        orbital_period_days: 687,
        frequency_hz: 0.0000168,
        weight: 0.35,
        phase_offset: 240,
        targets: ['harmonic_weights', 'surge_modulation']
      },
      {
        name: 'jupiter',
        orbital_period_days: 4333,
        frequency_hz: 0.00000267,
        weight: 0.8,
        phase_offset: 90,
        targets: ['coherence_nudge', 'color_palette']
      },
      {
        name: 'saturn',
        orbital_period_days: 10759,
        frequency_hz: 0.00000107,
        weight: 0.6,
        phase_offset: 180,
        targets: ['phase_bias', 'surge_modulation']
      }
    ];

    planets.forEach(planet => {
      this.planetaryData.set(planet.name, planet);
    });
  }

  private initializeSynodics() {
    const synodics: SynodicBeat[] = [
      {
        name: 'jupiter_saturn',
        period_years: 19.86,
        frequency_hz: 0.00000159,
        weight: 0.4,
        target: 'coherence_nudge'
      },
      {
        name: 'earth_venus',
        period_years: 1.6,
        frequency_hz: 0.0000198,
        weight: 0.3,
        target: 'harmonic_weights'
      }
    ];

    synodics.forEach(synodic => {
      this.synodicBeats.set(synodic.name, synodic);
    });
  }

  // Calculate current planetary phase for a given planet
  getPlanetaryPhase(planetName: string): number {
    const planet = this.planetaryData.get(planetName);
    if (!planet) return 0;

    const elapsed = (Date.now() - this.startTime) / 1000; // seconds
    const cycles = elapsed * planet.frequency_hz;
    const phase = (cycles * 2 * Math.PI + (planet.phase_offset * Math.PI / 180)) % (2 * Math.PI);
    
    return phase;
  }

  // Get modulation value for a planet (-1 to 1)
  getPlanetaryModulation(planetName: string): number {
    const phase = this.getPlanetaryPhase(planetName);
    const planet = this.planetaryData.get(planetName);
    
    if (!planet) return 0;
    
    return Math.sin(phase) * planet.weight;
  }

  // Calculate synodic beat modulation
  getSynodicModulation(beatName: string): number {
    const beat = this.synodicBeats.get(beatName);
    if (!beat) return 0;

    const elapsed = (Date.now() - this.startTime) / 1000;
    const cycles = elapsed * beat.frequency_hz;
    const phase = cycles * 2 * Math.PI;
    
    return Math.sin(phase) * beat.weight;
  }

  // Get combined modulation for harmonic weights
  getHarmonicWeightModulation(): number[] {
    let modulation = [1.0, 1.0, 1.0, 1.0]; // Base weights for 4 harmonics
    
    // Apply planetary modulations
    ['mercury', 'venus', 'mars'].forEach((planet, index) => {
      const mod = this.getPlanetaryModulation(planet);
      modulation[index % 4] += mod * 0.1; // Scale modulation
    });

    // Apply synodic beats
    const earthVenus = this.getSynodicModulation('earth_venus');
    modulation[0] += earthVenus * 0.05;
    modulation[2] += earthVenus * 0.05;

    // Normalize to prevent extreme values
    return modulation.map(w => Math.max(0.1, Math.min(2.0, w)));
  }

  // Get color palette hue shift based on planetary positions
  getColorPaletteShift(): number {
    let hueShift = 0;
    
    // Earth and Jupiter influence color palette
    hueShift += this.getPlanetaryModulation('earth') * 30; // ±30 degrees
    hueShift += this.getPlanetaryModulation('jupiter') * 15; // ±15 degrees
    
    return hueShift;
  }

  // Get coherence nudge from Jupiter-Saturn synodic beat
  getCoherenceNudge(): number {
    const jupiterSaturn = this.getSynodicModulation('jupiter_saturn');
    const jupiter = this.getPlanetaryModulation('jupiter');
    
    return (jupiterSaturn + jupiter * 0.5) * 0.1; // Small nudge
  }

  // Get phase bias for Schumann harmonics
  getPhaseBias(): number[] {
    const venus = this.getPlanetaryModulation('venus');
    const earth = this.getPlanetaryModulation('earth');
    const saturn = this.getPlanetaryModulation('saturn');
    
    return [
      earth * 0.1,      // Fundamental phase bias
      venus * 0.15,     // First harmonic
      saturn * 0.1,     // Second harmonic
      (venus + saturn) * 0.05 // Third harmonic
    ];
  }

  // Update planetary weights from UI controls
  updatePlanetaryWeights(updates: Record<string, number>) {
    Object.entries(updates).forEach(([planet, weight]) => {
      const planetData = this.planetaryData.get(planet);
      if (planetData) {
        planetData.weight = weight;
      }
    });
  }

  // Get all current planetary states for debugging/display
  getAllPlanetaryStates() {
    const states: Record<string, any> = {};
    
    this.planetaryData.forEach((planet, name) => {
      states[name] = {
        phase: this.getPlanetaryPhase(name),
        modulation: this.getPlanetaryModulation(name),
        weight: planet.weight,
        frequency_hz: planet.frequency_hz
      };
    });
    
    return states;
  }
}