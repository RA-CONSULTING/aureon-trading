// Master Equation: Λ(t) = S(t) + O(t) + E(t)
// S(t) = Substrate (9 Auris nodes respond to market)
// O(t) = Observer (self-referential field awareness)
// E(t) = Echo (memory and momentum)
// Γ = Coherence (0-1, measures field alignment)

import { AurisNodes, type MarketSnapshot } from './aurisNodes';
import { stargateLayer, type StargateInfluence } from './stargateLattice';

export type LambdaState = {
  lambda: number;
  coherence: number;
  substrate: number;
  observer: number;
  echo: number;
  dominantNode: string;
  nodeResponses: Record<string, number>;
  stargateInfluence?: StargateInfluence;
};

export class MasterEquation {
  private history: number[] = [];
  private maxHistory = 100;
  private userLocation: { lat: number; lng: number } | null = null;
  private celestialBoost: number = 0;
  
  setUserLocation(lat: number, lng: number, celestialBoost: number = 0) {
    this.userLocation = { lat, lng };
    this.celestialBoost = celestialBoost;
  }
  
  step(snapshot: MarketSnapshot): LambdaState {
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
    
    // Apply Stargate Lattice influence if location available
    let stargateInfluence: StargateInfluence | undefined;
    if (this.userLocation) {
      stargateInfluence = stargateLayer.getInfluence(
        this.userLocation.lat,
        this.userLocation.lng,
        this.celestialBoost
      );
      
      // Boost coherence based on proximity to sacred nodes + celestial alignments
      coherence = Math.min(1, coherence + stargateInfluence.coherenceModifier);
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
