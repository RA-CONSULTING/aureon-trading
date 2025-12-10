/**
 * 🌐 STARGATE GRID - Global Resonance Network
 * 
 * Maps global leyline activity and sacred geometric nodes
 * for market timing and energy flow analysis.
 */

import { unifiedBus, BusState } from './unifiedBus';
import { temporalLadder } from './temporalLadder';

// Major Stargate nodes (simplified global grid)
const STARGATE_NODES: Record<string, { lat: number; lon: number; frequency: number; name: string }> = {
  GIZA: { lat: 29.9792, lon: 31.1342, frequency: 432, name: 'Great Pyramid' },
  STONEHENGE: { lat: 51.1789, lon: -1.8262, frequency: 528, name: 'Stonehenge' },
  MACHU_PICCHU: { lat: -13.1631, lon: -72.5450, frequency: 396, name: 'Machu Picchu' },
  SEDONA: { lat: 34.8697, lon: -111.7610, frequency: 639, name: 'Sedona Vortex' },
  ULURU: { lat: -25.3444, lon: 131.0369, frequency: 741, name: 'Uluru' },
  MOUNT_SHASTA: { lat: 41.3099, lon: -122.3106, frequency: 852, name: 'Mount Shasta' },
  GLASTONBURY: { lat: 51.1485, lon: -2.7149, frequency: 963, name: 'Glastonbury Tor' },
  TEOTIHUACAN: { lat: 19.6925, lon: -98.8438, frequency: 417, name: 'Teotihuacan' },
  ANGKOR_WAT: { lat: 13.4125, lon: 103.8670, frequency: 285, name: 'Angkor Wat' },
  EASTER_ISLAND: { lat: -27.1127, lon: -109.3497, frequency: 174, name: 'Easter Island' }
};

// Major leylines (simplified)
const LEYLINES: Array<{ name: string; nodes: string[]; baseActivity: number }> = [
  { name: 'Michael Line', nodes: ['GLASTONBURY', 'STONEHENGE'], baseActivity: 0.7 },
  { name: 'Apollo Line', nodes: ['GIZA', 'STONEHENGE', 'GLASTONBURY'], baseActivity: 0.8 },
  { name: 'Pacific Ring', nodes: ['ULURU', 'EASTER_ISLAND', 'MACHU_PICCHU'], baseActivity: 0.6 },
  { name: 'Dragon Line', nodes: ['ANGKOR_WAT', 'ULURU'], baseActivity: 0.65 },
  { name: 'Serpent Line', nodes: ['TEOTIHUACAN', 'SEDONA', 'MOUNT_SHASTA'], baseActivity: 0.75 }
];

export interface StargateNode {
  id: string;
  name: string;
  lat: number;
  lon: number;
  frequency: number;
  activity: number;
  resonance: number;
}

export interface LeylineState {
  name: string;
  activity: number;
  activeNodes: string[];
}

export interface GridState {
  nodes: StargateNode[];
  leylines: LeylineState[];
  overallCoherence: number;
  dominantNode: string;
  dominantFrequency: number;
  gridAlignment: number;
}

export function getLeylineActivity(leylineName: string): number {
  const leyline = LEYLINES.find(l => l.name === leylineName);
  if (!leyline) return 0;
  
  // Modulate by time of day (UTC)
  const hour = new Date().getUTCHours();
  const timeModulation = Math.sin((hour / 24) * 2 * Math.PI) * 0.2 + 1;
  
  return leyline.baseActivity * timeModulation;
}

export class StargateGrid {
  private nodes: Map<string, StargateNode> = new Map();
  private currentState: GridState;
  private registered = false;
  
  constructor() {
    // Initialize nodes
    for (const [id, data] of Object.entries(STARGATE_NODES)) {
      this.nodes.set(id, {
        id,
        name: data.name,
        lat: data.lat,
        lon: data.lon,
        frequency: data.frequency,
        activity: 0.5,
        resonance: 0.5
      });
    }
    
    this.currentState = this.calculateGridState();
  }
  
  register(): void {
    if (this.registered) return;
    
    temporalLadder.registerSystem({
      id: 'STARGATE_GRID',
      name: 'Stargate Grid',
      type: 'EARTH',
      priority: 7,
      heartbeatInterval: 3000,
      onHeartbeat: () => ({
        coherence: this.currentState.overallCoherence,
        dominantNode: this.currentState.dominantNode
      })
    });
    
    this.registered = true;
    console.log('🌐 Stargate Grid registered');
  }
  
  update(marketCoherence: number, schumannResonance = 7.83): GridState {
    // Update node activities based on time and market coherence
    const now = new Date();
    const hour = now.getUTCHours();
    const dayOfYear = Math.floor((now.getTime() - new Date(now.getFullYear(), 0, 0).getTime()) / 86400000);
    
    for (const [id, node] of this.nodes) {
      // Time-based modulation (nodes activate at different times)
      const nodePhase = (node.lon + 180) / 360; // 0-1 based on longitude
      const timeAlignment = Math.cos((hour / 24 - nodePhase) * 2 * Math.PI);
      
      // Seasonal modulation
      const seasonalPhase = Math.cos((dayOfYear / 365) * 2 * Math.PI);
      
      // Schumann resonance influence
      const schumannInfluence = 1 - Math.abs(schumannResonance - 7.83) / 7.83;
      
      // Calculate activity
      node.activity = Math.max(0, Math.min(1,
        0.5 + timeAlignment * 0.2 + seasonalPhase * 0.1 + schumannInfluence * 0.2
      ));
      
      // Resonance with market coherence
      node.resonance = (node.activity + marketCoherence) / 2;
    }
    
    this.currentState = this.calculateGridState();
    
    // Publish to UnifiedBus
    const busState: BusState = {
      system_name: 'StargateGrid',
      timestamp: Date.now(),
      ready: true,
      coherence: this.currentState.overallCoherence,
      confidence: this.currentState.gridAlignment,
      signal: this.currentState.overallCoherence > 0.6 ? 1 : 0,
      data: {
        dominantNode: this.currentState.dominantNode,
        dominantFrequency: this.currentState.dominantFrequency,
        activeNodes: this.currentState.nodes.filter(n => n.activity > 0.6).length
      }
    };
    unifiedBus.publish(busState);
    
    return this.currentState;
  }
  
  private calculateGridState(): GridState {
    const nodeArray = Array.from(this.nodes.values());
    
    // Find dominant node
    const dominantNode = nodeArray.reduce((a, b) => a.activity > b.activity ? a : b);
    
    // Calculate leyline states
    const leylineStates: LeylineState[] = LEYLINES.map(leyline => {
      const nodeActivities = leyline.nodes
        .map(id => this.nodes.get(id)?.activity ?? 0);
      const avgActivity = nodeActivities.reduce((a, b) => a + b, 0) / nodeActivities.length;
      
      return {
        name: leyline.name,
        activity: avgActivity * leyline.baseActivity,
        activeNodes: leyline.nodes.filter(id => (this.nodes.get(id)?.activity ?? 0) > 0.5)
      };
    });
    
    // Overall coherence
    const overallCoherence = nodeArray.reduce((sum, n) => sum + n.resonance, 0) / nodeArray.length;
    
    // Grid alignment (how many nodes are in sync)
    const activeNodes = nodeArray.filter(n => n.activity > 0.5);
    const gridAlignment = activeNodes.length / nodeArray.length;
    
    return {
      nodes: nodeArray,
      leylines: leylineStates,
      overallCoherence,
      dominantNode: dominantNode.id,
      dominantFrequency: dominantNode.frequency,
      gridAlignment
    };
  }
  
  getState(): GridState {
    return this.currentState;
  }
  
  getNodeActivity(nodeId: string): number {
    return this.nodes.get(nodeId)?.activity ?? 0;
  }
  
  getGridCoherence(): number {
    return this.currentState.overallCoherence;
  }
  
  getModifier(): number {
    // Trading modifier based on grid state
    const coherence = this.currentState.overallCoherence;
    const alignment = this.currentState.gridAlignment;
    
    return 0.8 + (coherence * 0.3) + (alignment * 0.2);
  }
}

export const stargateGrid = new StargateGrid();
