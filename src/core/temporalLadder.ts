/**
 * Temporal Ladder - Hierarchical System Fallback Framework
 * Prime Sentinel: GARY LECKEY 02111991
 * 
 * Provides a hive-mind interconnection layer where every system knows about
 * every other system and can fall back when one fails or needs support.
 * 
 * Hierarchy:
 * 1. Harmonic Nexus Core (highest authority - reality substrate)
 * 2. Master Equation (Ω field orchestrator)
 * 3. Earth Integration (Schumann/geomagnetic streams)
 * 4. Nexus Live Feed (coherence boost)
 * 5. Quantum Quackers (quantum state modulation)
 * 6. Akashic Mapper (frequency harmonics)
 * 7. Zero Point Detector (field harmonics)
 * 8. Dimensional Dialler (drift correction)
 */

export type SystemName = 
  | 'harmonic-nexus'
  | 'master-equation'
  | 'earth-integration'
  | 'nexus-feed'
  | 'quantum-quackers'
  | 'akashic-mapper'
  | 'zero-point'
  | 'dimensional-dialler'
  | 'integral-aqal'
  | 'stargate-lattice'
  | 'ftcp-detector'
  | 'qgita-signal'
  | 'hnc-imperial'
  | 'smart-router'
  | 'temporal-anchor'
  | 'hive-controller'
  | 'decision-fusion'
  | 'prism'
  | '6d-harmonic'
  | 'probability-matrix'
  | 'quantum-telescope'
  | 'hocus-pattern'
  | 'gaia-lattice'
  | 'synchronicity-decoder'
  | 'stargate-grid'
  | 'market-pulse'
  | 'anomaly-detector'
  | 'enhancement-layer'
  | 'data-ingestion'
  | 'opportunity-scanner'
  | 'position-manager'
  | 'ticker-cache'
  | 'capital-pool'
  | 'startup-harvester';

export interface SystemStatus {
  name: SystemName;
  active: boolean;
  health: number; // 0-1
  lastHeartbeat: number;
  fallbackTarget?: SystemName;
  canTakeover: boolean;
}

export interface TemporalLadderState {
  systems: Map<SystemName, SystemStatus>;
  activeChain: SystemName[];
  primarySystem: SystemName;
  fallbackInProgress: boolean;
  hiveMindCoherence: number; // overall system integration
}

export interface FallbackEvent {
  timestamp: number;
  fromSystem: SystemName;
  toSystem: SystemName;
  reason: string;
  success: boolean;
}

class TemporalLadderCore {
  private state: TemporalLadderState;
  private fallbackHistory: FallbackEvent[] = [];
  private listeners: Array<(state: TemporalLadderState) => void> = [];
  private heartbeatInterval: number | null = null;

  // System hierarchy (priority order)
  private readonly SYSTEM_HIERARCHY: SystemName[] = [
    'harmonic-nexus',
    'master-equation',
    'earth-integration',
    'nexus-feed',
    'quantum-quackers',
    'akashic-mapper',
    'zero-point',
    'dimensional-dialler',
    'integral-aqal',
    'stargate-lattice',
    'ftcp-detector',
    'qgita-signal',
    'hnc-imperial',
    'hocus-pattern',
    'smart-router',
    'temporal-anchor',
    'hive-controller',
    'decision-fusion',
    'prism',
    '6d-harmonic',
    'probability-matrix',
    'quantum-telescope'
  ];

  constructor() {
    this.state = {
      systems: new Map(),
      activeChain: [],
      primarySystem: 'harmonic-nexus',
      fallbackInProgress: false,
      hiveMindCoherence: 0
    };

    this.initializeSystems();
    this.startHeartbeat();
  }

  private initializeSystems() {
    this.SYSTEM_HIERARCHY.forEach((name, index) => {
      const fallbackTarget = index < this.SYSTEM_HIERARCHY.length - 1 
        ? this.SYSTEM_HIERARCHY[index + 1]
        : undefined;

      this.state.systems.set(name, {
        name,
        active: false,
        health: 1.0,
        lastHeartbeat: Date.now(),
        fallbackTarget,
        canTakeover: index > 0 // All except harmonic-nexus can take over
      });
    });
  }

  private startHeartbeat() {
    if (this.heartbeatInterval) return;

    this.heartbeatInterval = window.setInterval(() => {
      this.checkSystemHealth();
      this.updateHiveMindCoherence();
      this.notifyListeners();
    }, 1000);
  }

  private checkSystemHealth() {
    const now = Date.now();
    const HEARTBEAT_TIMEOUT = 15000; // Increased to 15 seconds for stability

    this.state.systems.forEach((status, name) => {
      if (status.active && now - status.lastHeartbeat > HEARTBEAT_TIMEOUT) {
        // Only log once per significant health drop to reduce spam
        if (status.health > 0.5) {
          console.warn(`⚠️ Temporal Ladder: ${name} heartbeat timeout (health: ${status.health.toFixed(2)})`);
        }
        status.health = Math.max(0, status.health - 0.05); // Slower degradation
        
        if (status.health < 0.2) {
          this.initiateFailover(name);
        }
      }
    });
  }

  private initiateFailover(failedSystem: SystemName) {
    const status = this.state.systems.get(failedSystem);
    if (!status || !status.fallbackTarget) {
      console.error(`❌ Temporal Ladder: No fallback for ${failedSystem}`);
      return;
    }

    console.log(`🔄 Temporal Ladder: Initiating failover from ${failedSystem} to ${status.fallbackTarget}`);
    
    this.state.fallbackInProgress = true;
    const targetStatus = this.state.systems.get(status.fallbackTarget);

    if (targetStatus && !targetStatus.active) {
      // Activate fallback system
      targetStatus.active = true;
      targetStatus.health = 1.0;
      targetStatus.lastHeartbeat = Date.now();
    }

    this.fallbackHistory.push({
      timestamp: Date.now(),
      fromSystem: failedSystem,
      toSystem: status.fallbackTarget,
      reason: 'health_degradation',
      success: true
    });

    this.state.fallbackInProgress = false;
    this.rebuildActiveChain();
  }

  private rebuildActiveChain() {
    this.state.activeChain = this.SYSTEM_HIERARCHY.filter(name => {
      const status = this.state.systems.get(name);
      return status?.active && status.health > 0.5;
    });
  }

  private updateHiveMindCoherence() {
    let totalHealth = 0;
    let activeCount = 0;

    this.state.systems.forEach(status => {
      if (status.active) {
        totalHealth += status.health;
        activeCount++;
      }
    });

    this.state.hiveMindCoherence = activeCount > 0 ? totalHealth / activeCount : 0;
  }

  // Public API

  registerSystem(name: SystemName) {
    const status = this.state.systems.get(name);
    if (status) {
      status.active = true;
      status.health = 1.0;
      status.lastHeartbeat = Date.now();
      this.rebuildActiveChain();
      console.log(`✅ Temporal Ladder: ${name} registered`);
    }
  }

  unregisterSystem(name: SystemName) {
    const status = this.state.systems.get(name);
    if (status) {
      status.active = false;
      this.rebuildActiveChain();
      console.log(`❌ Temporal Ladder: ${name} unregistered`);
    }
  }

  heartbeat(name: SystemName, health?: number) {
    const status = this.state.systems.get(name);
    if (status) {
      status.lastHeartbeat = Date.now();
      if (health !== undefined) {
        status.health = Math.max(0, Math.min(1, health));
      }
    }
  }

  getSystemStatus(name: SystemName): SystemStatus | undefined {
    return this.state.systems.get(name);
  }

  getState(): TemporalLadderState {
    return { ...this.state };
  }

  getFallbackHistory(): FallbackEvent[] {
    return [...this.fallbackHistory];
  }

  subscribe(listener: (state: TemporalLadderState) => void) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  private notifyListeners() {
    this.listeners.forEach(listener => {
      try {
        listener(this.getState());
      } catch (err) {
        console.error('Temporal Ladder listener error:', err);
      }
    });
  }

  /**
   * Request assistance from another system in the chain
   */
  requestAssistance(requester: SystemName, target: SystemName, reason: string): boolean {
    const requesterStatus = this.state.systems.get(requester);
    const targetStatus = this.state.systems.get(target);

    if (!requesterStatus?.active || !targetStatus?.active) {
      console.warn(`⚠️ Temporal Ladder: Cannot request assistance - systems not active`);
      return false;
    }

    if (targetStatus.health < 0.7) {
      console.warn(`⚠️ Temporal Ladder: ${target} health too low to assist`);
      return false;
    }

    console.log(`🤝 Temporal Ladder: ${requester} requesting assistance from ${target} (${reason})`);
    
    this.fallbackHistory.push({
      timestamp: Date.now(),
      fromSystem: requester,
      toSystem: target,
      reason: `assistance_${reason}`,
      success: true
    });

    return true;
  }

  /**
   * Hive mind broadcast - notify all systems of an event
   */
  broadcast(sourceSystem: SystemName, event: string, data?: any) {
    console.log(`📡 Temporal Ladder Broadcast from ${sourceSystem}: ${event}`, data);
    
    // In a real implementation, this would dispatch to all active systems
    // For now, just log and track
    this.state.systems.forEach((status, name) => {
      if (status.active && name !== sourceSystem) {
        // Each system would receive and process the broadcast
      }
    });
  }

  destroy() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
    this.listeners = [];
  }
}

// Singleton instance
export const temporalLadder = new TemporalLadderCore();

// Export system names for easy reference
export const SYSTEMS = {
  HARMONIC_NEXUS: 'harmonic-nexus' as SystemName,
  MASTER_EQUATION: 'master-equation' as SystemName,
  EARTH_INTEGRATION: 'earth-integration' as SystemName,
  NEXUS_FEED: 'nexus-feed' as SystemName,
  QUANTUM_QUACKERS: 'quantum-quackers' as SystemName,
  AKASHIC_MAPPER: 'akashic-mapper' as SystemName,
  ZERO_POINT: 'zero-point' as SystemName,
  DIMENSIONAL_DIALLER: 'dimensional-dialler' as SystemName,
  INTEGRAL_AQAL: 'integral-aqal' as SystemName,
  STARGATE_LATTICE: 'stargate-lattice' as SystemName,
  FTCP_DETECTOR: 'ftcp-detector' as SystemName,
  QGITA_SIGNAL: 'qgita-signal' as SystemName,
  HNC_IMPERIAL: 'hnc-imperial' as SystemName,
  HOCUS_PATTERN: 'hocus-pattern' as SystemName,
  SMART_ROUTER: 'smart-router' as SystemName,
  TEMPORAL_ANCHOR: 'temporal-anchor' as SystemName,
  HIVE_CONTROLLER: 'hive-controller' as SystemName,
  DECISION_FUSION: 'decision-fusion' as SystemName,
  PRISM: 'prism' as SystemName,
  SIX_D_HARMONIC: '6d-harmonic' as SystemName,
  PROBABILITY_MATRIX: 'probability-matrix' as SystemName,
  QUANTUM_TELESCOPE: 'quantum-telescope' as SystemName,
  DATA_INGESTION: 'data-ingestion' as SystemName,
  OPPORTUNITY_SCANNER: 'opportunity-scanner' as SystemName,
  POSITION_MANAGER: 'position-manager' as SystemName,
  TICKER_CACHE: 'ticker-cache' as SystemName,
  CAPITAL_POOL: 'capital-pool' as SystemName,
  STARTUP_HARVESTER: 'startup-harvester' as SystemName,
};
