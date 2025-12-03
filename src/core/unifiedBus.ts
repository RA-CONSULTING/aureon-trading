// UnifiedBus - Central state communication layer
// Each system publishes state, all systems read from bus
// "Each system reads and reassures the next. Each is a piece to a big puzzle."

export type SignalType = 'BUY' | 'SELL' | 'NEUTRAL';

export interface SystemState {
  systemName: string;
  timestamp: number;
  ready: boolean;
  coherence: number;
  confidence: number;
  signal: SignalType;
  data: Record<string, any>;
}

export interface BusSnapshot {
  states: Record<string, SystemState>;
  timestamp: number;
  consensusSignal: SignalType;
  consensusConfidence: number;
  systemsReady: number;
  totalSystems: number;
}

// System weights for consensus calculation
const SYSTEM_WEIGHTS: Record<string, number> = {
  MasterEquation: 0.35,
  Lighthouse: 0.30,
  RainbowBridge: 0.20,
  DataIngestion: 0.15,
};

const REQUIRED_SYSTEMS = ['DataIngestion', 'Lighthouse', 'MasterEquation', 'RainbowBridge'];

class UnifiedBus {
  private states: Map<string, SystemState> = new Map();
  private listeners: Set<(snapshot: BusSnapshot) => void> = new Set();
  
  /**
   * Publish a system's state to the bus
   */
  publish(state: SystemState): void {
    this.states.set(state.systemName, {
      ...state,
      timestamp: Date.now(),
    });
    this.notifyListeners();
  }
  
  /**
   * Read a specific system's state
   */
  read(systemName: string): SystemState | undefined {
    return this.states.get(systemName);
  }
  
  /**
   * Read all system states
   */
  readAll(): Record<string, SystemState> {
    const result: Record<string, SystemState> = {};
    this.states.forEach((state, name) => {
      result[name] = state;
    });
    return result;
  }
  
  /**
   * Get a complete snapshot of the bus including consensus
   */
  snapshot(): BusSnapshot {
    const states = this.readAll();
    const { signal, confidence } = this.computeConsensus();
    const systemsReady = Object.values(states).filter(s => s.ready).length;
    
    return {
      states,
      timestamp: Date.now(),
      consensusSignal: signal,
      consensusConfidence: confidence,
      systemsReady,
      totalSystems: this.states.size,
    };
  }
  
  /**
   * Check if all required systems are ready and compute consensus
   */
  checkConsensus(): { ready: boolean; signal: SignalType; confidence: number } {
    const allReady = REQUIRED_SYSTEMS.every(name => {
      const state = this.states.get(name);
      return state?.ready && state.coherence > 0.7;
    });
    
    const { signal, confidence } = this.computeConsensus();
    
    return {
      ready: allReady,
      signal,
      confidence,
    };
  }
  
  /**
   * Compute weighted consensus from all systems
   */
  private computeConsensus(): { signal: SignalType; confidence: number } {
    let buyScore = 0;
    let sellScore = 0;
    let totalWeight = 0;
    let totalConfidence = 0;
    
    for (const [name, weight] of Object.entries(SYSTEM_WEIGHTS)) {
      const state = this.states.get(name);
      if (!state?.ready) continue;
      
      totalWeight += weight;
      totalConfidence += state.confidence * weight;
      
      if (state.signal === 'BUY') {
        buyScore += weight * state.confidence;
      } else if (state.signal === 'SELL') {
        sellScore += weight * state.confidence;
      }
    }
    
    if (totalWeight === 0) {
      return { signal: 'NEUTRAL', confidence: 0 };
    }
    
    const normalizedBuy = buyScore / totalWeight;
    const normalizedSell = sellScore / totalWeight;
    const confidence = totalConfidence / totalWeight;
    
    let signal: SignalType = 'NEUTRAL';
    if (normalizedBuy > normalizedSell && normalizedBuy > 0.3) {
      signal = 'BUY';
    } else if (normalizedSell > normalizedBuy && normalizedSell > 0.3) {
      signal = 'SELL';
    }
    
    return { signal, confidence };
  }
  
  /**
   * Subscribe to bus updates
   */
  subscribe(callback: (snapshot: BusSnapshot) => void): () => void {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }
  
  /**
   * Notify all listeners of state changes
   */
  private notifyListeners(): void {
    const snapshot = this.snapshot();
    this.listeners.forEach(callback => callback(snapshot));
  }
  
  /**
   * Clear all states (useful for reset)
   */
  clear(): void {
    this.states.clear();
  }
  
  /**
   * Get system health status
   */
  getSystemHealth(): Array<{ name: string; ready: boolean; coherence: number; lastUpdate: number }> {
    const health: Array<{ name: string; ready: boolean; coherence: number; lastUpdate: number }> = [];
    
    const allSystems = [...REQUIRED_SYSTEMS, 'ElephantMemory', 'ZeroPoint', 'Dimensional', 'Akashic'];
    
    for (const name of allSystems) {
      const state = this.states.get(name);
      health.push({
        name,
        ready: state?.ready ?? false,
        coherence: state?.coherence ?? 0,
        lastUpdate: state?.timestamp ?? 0,
      });
    }
    
    return health;
  }
}

// Singleton instance
export const unifiedBus = new UnifiedBus();
