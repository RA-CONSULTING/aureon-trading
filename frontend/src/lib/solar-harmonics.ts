// Solar Harmonics Engine - Planetary frequency synthesis and chaining
export interface Planet {
  name: string;
  freq: number;
  note: string;
  color: string;
  desc: string;
  orbitalPeriod: number; // Earth days
  distance: number; // AU from Sun
  mass: number; // Earth masses
  harmonicRatio: number;
}

export const PLANETS: Planet[] = [
  { name: 'Mercury', freq: 22.0, note: 'G2-A2', color: '#db2777', desc: 'Metallic Ping', orbitalPeriod: 88, distance: 0.39, mass: 0.055, harmonicRatio: 2.81 },
  { name: 'Venus', freq: 10.0, note: 'C2', color: '#7c3aed', desc: 'Sister Hum', orbitalPeriod: 225, distance: 0.72, mass: 0.815, harmonicRatio: 1.28 },
  { name: 'Earth', freq: 7.83, note: 'B1 (Alpha)', color: '#10b981', desc: 'Human Alpha', orbitalPeriod: 365, distance: 1.0, mass: 1.0, harmonicRatio: 1.0 },
  { name: 'Mars', freq: 16.0, note: 'D#2-F2', color: '#ef4444', desc: 'Thin Sharp', orbitalPeriod: 687, distance: 1.52, mass: 0.107, harmonicRatio: 2.04 },
  { name: 'Jupiter', freq: 0.8, note: 'Sub-bass A0', color: '#f59e0b', desc: 'Cosmic Bass', orbitalPeriod: 4333, distance: 5.2, mass: 317.8, harmonicRatio: 0.10 },
  { name: 'Saturn', freq: 1.0, note: 'Bass B0-C1', color: '#8b5cf6', desc: 'Deep Drone', orbitalPeriod: 10759, distance: 9.5, mass: 95.2, harmonicRatio: 0.13 },
  { name: 'Uranus', freq: 2.5, note: 'Low D1-E1', color: '#06b6d4', desc: 'Low Pulse', orbitalPeriod: 30687, distance: 19.2, mass: 14.5, harmonicRatio: 0.32 },
  { name: 'Neptune', freq: 3.0, note: 'Low E1-F1', color: '#3b82f6', desc: 'Oceanic Wave', orbitalPeriod: 60190, distance: 30.1, mass: 17.1, harmonicRatio: 0.38 }
];

export interface ChainLink {
  from: string;
  to: string;
  harmonicRatio: number;
  resonanceStrength: number;
  phaseOffset: number;
}

export class SolarHarmonicsEngine {
  private audioContext: AudioContext | null = null;
  private oscillators: Map<string, OscillatorNode> = new Map();
  private gainNodes: Map<string, GainNode> = new Map();
  private chains: ChainLink[] = [];
  private masterGain: GainNode | null = null;

  async initialize() {
    if (!this.audioContext) {
      this.audioContext = new AudioContext();
      this.masterGain = this.audioContext.createGain();
      this.masterGain.connect(this.audioContext.destination);
      this.masterGain.gain.value = 0.1;
    }
  }

  createChain(fromPlanet: string, toPlanet: string): ChainLink {
    const from = PLANETS.find(p => p.name === fromPlanet);
    const to = PLANETS.find(p => p.name === toPlanet);
    
    if (!from || !to) throw new Error('Planet not found');
    
    const harmonicRatio = to.freq / from.freq;
    const resonanceStrength = Math.abs(1 - Math.abs(harmonicRatio - Math.round(harmonicRatio)));
    const phaseOffset = (from.orbitalPeriod % to.orbitalPeriod) / to.orbitalPeriod * 2 * Math.PI;
    
    const chain: ChainLink = {
      from: fromPlanet,
      to: toPlanet,
      harmonicRatio,
      resonanceStrength,
      phaseOffset
    };
    
    this.chains.push(chain);
    return chain;
  }

  async playPlanet(planetName: string, duration: number = 5000) {
    if (!this.audioContext || !this.masterGain) await this.initialize();
    
    const planet = PLANETS.find(p => p.name === planetName);
    if (!planet) return;

    // Stop existing oscillator
    this.stopPlanet(planetName);

    const osc = this.audioContext!.createOscillator();
    const gain = this.audioContext!.createGain();
    
    osc.frequency.value = planet.freq;
    osc.type = 'sine';
    
    gain.gain.setValueAtTime(0, this.audioContext!.currentTime);
    gain.gain.linearRampToValueAtTime(0.3, this.audioContext!.currentTime + 0.1);
    gain.gain.exponentialRampToValueAtTime(0.001, this.audioContext!.currentTime + duration / 1000);
    
    osc.connect(gain);
    gain.connect(this.masterGain!);
    
    this.oscillators.set(planetName, osc);
    this.gainNodes.set(planetName, gain);
    
    osc.start();
    osc.stop(this.audioContext!.currentTime + duration / 1000);
    
    setTimeout(() => {
      this.oscillators.delete(planetName);
      this.gainNodes.delete(planetName);
    }, duration);
  }

  stopPlanet(planetName: string) {
    const osc = this.oscillators.get(planetName);
    if (osc) {
      osc.stop();
      this.oscillators.delete(planetName);
      this.gainNodes.delete(planetName);
    }
  }

  playChain(chainedPlanets: string[], interval: number = 500) {
    chainedPlanets.forEach((planet, index) => {
      setTimeout(() => this.playPlanet(planet, 3000), index * interval);
    });
  }

  getHarmonicSeries(rootPlanet: string): Planet[] {
    const root = PLANETS.find(p => p.name === rootPlanet);
    if (!root) return [];
    
    return PLANETS
      .filter(p => p.freq >= root.freq)
      .sort((a, b) => {
        const ratioA = a.freq / root.freq;
        const ratioB = b.freq / root.freq;
        const harmA = Math.abs(ratioA - Math.round(ratioA));
        const harmB = Math.abs(ratioB - Math.round(ratioB));
        return harmA - harmB;
      });
  }

  calculateResonance(planet1: string, planet2: string): number {
    const p1 = PLANETS.find(p => p.name === planet1);
    const p2 = PLANETS.find(p => p.name === planet2);
    if (!p1 || !p2) return 0;
    
    const ratio = Math.max(p1.freq, p2.freq) / Math.min(p1.freq, p2.freq);
    return 1 / (1 + Math.abs(ratio - Math.round(ratio)));
  }
}