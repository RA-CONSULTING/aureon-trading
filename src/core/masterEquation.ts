// Master Equation: Λ(t) = S(t) + O(t) + E(t)
// S(t) = Substrate (9 Auris nodes respond to market)
// O(t) = Observer (self-referential field awareness)
// E(t) = Echo (memory and momentum)
// Γ = Coherence (0-1, measures field alignment)
//
// TEMPORAL LADDER INTEGRATION: Orchestrates all systems with hive-mind coordination

import { AurisNodes, type MarketSnapshot } from './aurisNodes';
import { stargateLayer, type StargateInfluence } from './stargateLattice';
import { earthAureonBridge, type EarthFieldInfluence } from './earthAureonBridge';
import { nexusLiveFeedBridge, type NexusInfluence } from './nexusLiveFeedBridge';
import type { NexusBridgeConfig } from './nexusLiveFeedBridge';
import type { SimpleEarthStreams } from '../lib/earth-streams';
import { temporalLadder, SYSTEMS } from './temporalLadder';

export type LambdaState = {
  lambda: number;
  coherence: number;
  substrate: number;
  observer: number;
  echo: number;
  dominantNode: string;
  nodeResponses: Record<string, number>;
  stargateInfluence?: StargateInfluence;
  earthFieldInfluence?: EarthFieldInfluence;
  nexusInfluence?: NexusInfluence;
};

export class MasterEquation {
  private history: number[] = [];
  private maxHistory = 100;
  private userLocation: { lat: number; lng: number } | null = null;
  private celestialBoost: number = 0;
  private schumannBoost: number = 0;
  private earthStreams: SimpleEarthStreams | null = null;
  private regionId: string | null = null;
  private nexusEnabled = true;
  
  constructor() {
    // Register with Temporal Ladder as primary orchestrator
    temporalLadder.registerSystem(SYSTEMS.MASTER_EQUATION);
  }
  
  setUserLocation(lat: number, lng: number, celestialBoost: number = 0, schumannBoost: number = 0) {
    this.userLocation = { lat, lng };
    this.celestialBoost = celestialBoost;
    this.schumannBoost = schumannBoost;
  }

  setEarthStreams(streams: SimpleEarthStreams, regionId?: string) {
    this.earthStreams = streams;
    if (regionId) this.regionId = regionId;
  }

  enableEarthSync(enable: boolean = true) {
    earthAureonBridge.setConfig({ enableEarthSync: enable });
  }

  enableNexusSync(enable: boolean = true, configOverrides?: Partial<NexusBridgeConfig>) {
    this.nexusEnabled = enable;
    nexusLiveFeedBridge.setConfig({ enable, ...(configOverrides || {}) });
  }
  
  async step(snapshot: MarketSnapshot): Promise<LambdaState> {
    // Compute substrate S(t) from all 9 Auris nodes
    const nodeResponses: Record<string, number> = {};
    let substrate = 0;
    let dominantNode = '';
    let maxResponse = -Infinity;
    
    Object.entries(AurisNodes).forEach(([name, node]) => {
      const response = node.compute(snapshot) * node.weight;
      nodeResponses[name] = response;
      substrate += response;
      
      if (response > maxResponse) {
        maxResponse = response;
        dominantNode = name;
      }
    });
    
    // Normalize substrate
    substrate = substrate / Object.keys(AurisNodes).length;
    
    // Compute observer O(t) - self-referential awareness
    const observer = this.history.length > 0 
      ? this.history[this.history.length - 1] * 0.3 
      : 0;
    
    // Compute echo E(t) - memory and momentum
    const echo = this.history.length > 5
      ? this.history.slice(-5).reduce((sum, val) => sum + val, 0) / 5 * 0.2
      : 0;
    
    // Master equation
    const lambda = substrate + observer + echo;
    
    // Update history
    this.history.push(lambda);
    if (this.history.length > this.maxHistory) {
      this.history.shift();
    }
    
    // Compute base coherence Γ
    let coherence = this.computeCoherence(nodeResponses, substrate);
    
    // Apply Earth Field influence (Schumann resonance, solar wind, geomagnetic)
    let earthFieldInfluence: EarthFieldInfluence | undefined;
    try {
      earthFieldInfluence = await earthAureonBridge.getEarthInfluence(
        this.earthStreams || undefined,
        this.regionId || undefined
      );
      
      // Apply Earth's electromagnetic boost to coherence
      coherence = Math.min(1, coherence + earthFieldInfluence.combinedBoost);
    } catch (error) {
      console.warn('Earth field sync error (non-critical):', error);
    }
    
    // Apply Nexus harmonic nexus influence
    let nexusInfluence: NexusInfluence | undefined;
    if (this.nexusEnabled) {
      try {
        nexusInfluence = await nexusLiveFeedBridge.poll();
        coherence = Math.min(1, Math.max(0, coherence + nexusInfluence.compositeBoost));
      } catch (error) {
        console.warn('Nexus live feed error (non-critical):', error);
      }
    }

    // Apply Stargate Lattice influence if location available
    let stargateInfluence: StargateInfluence | undefined;
    if (this.userLocation) {
      stargateInfluence = stargateLayer.getInfluence(
        this.userLocation.lat,
        this.userLocation.lng,
        this.celestialBoost
      );
      
      // Boost coherence based on:
      // 1. Proximity to sacred Stargate nodes
      // 2. Celestial alignments (moon, solar, planetary)
      // 3. Legacy Schumann boost (for backwards compatibility)
      const totalBoost = stargateInfluence.coherenceModifier + this.schumannBoost;
      coherence = Math.min(1, coherence + totalBoost);
    } else if (this.schumannBoost > 0) {
      // Apply legacy Schumann boost even without location
      coherence = Math.min(1, coherence + this.schumannBoost);
    }
    
    return {
      lambda,
      coherence,
      substrate,
      observer,
      echo,
      dominantNode,
      nodeResponses,
      stargateInfluence,
      earthFieldInfluence,
      nexusInfluence,
    };
  }
  
  private computeCoherence(
    nodeResponses: Record<string, number>,
    substrate: number
  ): number {
    // Coherence measures alignment of node responses
    const responses = Object.values(nodeResponses);
    const avg = substrate;
    
    // Calculate variance
    const variance = responses.reduce((sum, r) => sum + Math.pow(r - avg, 2), 0) / responses.length;
    
    // Normalize to 0-1 range (lower variance = higher coherence)
    const coherence = Math.max(0, Math.min(1, 1 - variance / 10));
    
    return coherence;
  }
  
  reset() {
    this.history = [];
  }
}
