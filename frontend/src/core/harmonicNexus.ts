/**
 * Harmonic Nexus - Top-Level System Orchestrator
 * Prime Sentinel: GARY LECKEY 02111991
 * 
 * The highest authority in the Temporal Ladder hierarchy.
 * Orchestrates all systems, monitors hive health, and triggers failovers.
 * 
 * Integrates:
 * - Ω(t) tensor field from Harmonic Nexus Core
 * - Master Equation (Λ) field dynamics
 * - Temporal Ladder coordination
 * - Quantum state management
 * - Earth field harmonics
 * - Akashic frequency mapping
 */

import { temporalLadder, SYSTEMS, type SystemName } from './temporalLadder';
import type { HarmonicNexusState } from './harmonicNexusCore';

export interface HarmonicNexusOrchestration {
  status: 'active' | 'standby' | 'failover';
  hiveMindCoherence: number;
  activeSystemsCount: number;
  criticalSystems: SystemName[];
  lastFailover: number | null;
  orchestrationQuality: number; // 0-1, measures how well systems work together
}

class HarmonicNexusOrchestrator {
  private status: HarmonicNexusOrchestration = {
    status: 'standby',
    hiveMindCoherence: 0,
    activeSystemsCount: 0,
    criticalSystems: [],
    lastFailover: null,
    orchestrationQuality: 1.0
  };

  private monitoringInterval: NodeJS.Timeout | null = null;
  private listeners: Array<(state: HarmonicNexusOrchestration) => void> = [];

  constructor() {
    // Register as top-level authority
    temporalLadder.registerSystem(SYSTEMS.HARMONIC_NEXUS);
    console.log('🎯 Harmonic Nexus Orchestrator initialized');
  }

  /**
   * Activate the orchestrator - begins monitoring all systems
   */
  activate() {
    if (this.status.status === 'active') return;

    this.status.status = 'active';
    console.log('🚀 Harmonic Nexus Orchestrator ACTIVATED');

    // Start monitoring loop
    this.monitoringInterval = setInterval(() => {
      this.monitorHiveHealth();
      this.sendHeartbeat();
      this.notifyListeners();
    }, 1000);

    // Broadcast activation
    temporalLadder.broadcast(
      SYSTEMS.HARMONIC_NEXUS,
      'ORCHESTRATOR_ACTIVATED',
      { timestamp: Date.now() }
    );
  }

  /**
   * Deactivate the orchestrator
   */
  deactivate() {
    if (this.status.status !== 'active') return;

    this.status.status = 'standby';
    console.log('⏸️ Harmonic Nexus Orchestrator deactivated');

    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = null;
    }

    temporalLadder.broadcast(
      SYSTEMS.HARMONIC_NEXUS,
      'ORCHESTRATOR_DEACTIVATED',
      { timestamp: Date.now() }
    );
  }

  /**
   * Monitor the health of all systems in the hive mind
   */
  private monitorHiveHealth() {
    const ladderState = temporalLadder.getState();
    
    this.status.hiveMindCoherence = ladderState.hiveMindCoherence;
    this.status.activeSystemsCount = ladderState.activeChain.length;

    // Identify critical systems (health < 0.5)
    const criticalSystems: SystemName[] = [];
    ladderState.systems.forEach((system, name) => {
      if (system.active && system.health < 0.5) {
        criticalSystems.push(name);
      }
    });

    this.status.criticalSystems = criticalSystems;

    // Calculate orchestration quality
    // High quality = all systems healthy and working together
    const healthSum = Array.from(ladderState.systems.values())
      .filter(s => s.active)
      .reduce((sum, s) => sum + s.health, 0);
    
    const activeCount = ladderState.activeChain.length;
    this.status.orchestrationQuality = activeCount > 0 
      ? healthSum / activeCount 
      : 0;

    // Trigger failover if orchestration quality drops below threshold
    if (this.status.orchestrationQuality < 0.6 && criticalSystems.length > 0) {
      this.handleCriticalFailure(criticalSystems);
    }

    // Warn if hive mind coherence is low
    if (this.status.hiveMindCoherence < 0.5) {
      console.warn('⚠️ Harmonic Nexus: Low hive mind coherence', this.status.hiveMindCoherence.toFixed(2));
    }
  }

  /**
   * Handle critical system failures
   */
  private handleCriticalFailure(criticalSystems: SystemName[]) {
    console.error('🚨 Harmonic Nexus: CRITICAL FAILURE DETECTED', criticalSystems);
    
    this.status.status = 'failover';
    this.status.lastFailover = Date.now();

    // Request assistance from healthy systems
    const ladderState = temporalLadder.getState();
    const healthySystems = ladderState.activeChain.filter(
      name => !criticalSystems.includes(name)
    );

    criticalSystems.forEach(critical => {
      // Find the first healthy system to assist
      const assistant = healthySystems[0];
      if (assistant) {
        temporalLadder.requestAssistance(
          critical,
          assistant,
          'critical_failure_recovery'
        );
      }
    });

    // Broadcast emergency alert
    temporalLadder.broadcast(
      SYSTEMS.HARMONIC_NEXUS,
      'CRITICAL_FAILURE',
      {
        criticalSystems,
        orchestrationQuality: this.status.orchestrationQuality,
        timestamp: Date.now()
      }
    );

    // Return to active after failover attempt
    setTimeout(() => {
      if (this.status.status === 'failover') {
        this.status.status = 'active';
      }
    }, 5000);
  }

  /**
   * Send heartbeat to Temporal Ladder
   */
  private sendHeartbeat() {
    temporalLadder.heartbeat(
      SYSTEMS.HARMONIC_NEXUS,
      this.status.orchestrationQuality
    );
  }

  /**
   * Get current orchestration status
   */
  getStatus(): HarmonicNexusOrchestration {
    return { ...this.status };
  }

  /**
   * Subscribe to orchestration updates
   */
  subscribe(listener: (state: HarmonicNexusOrchestration) => void) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  private notifyListeners() {
    this.listeners.forEach(listener => {
      try {
        listener(this.getStatus());
      } catch (err) {
        console.error('Harmonic Nexus listener error:', err);
      }
    });
  }

  /**
   * Process Harmonic Nexus Core state updates
   */
  processNexusState(nexusState: HarmonicNexusState) {
    // If substrate coherence is high, boost all system health
    if (nexusState.substrateCoherence > 0.9) {
      temporalLadder.broadcast(
        SYSTEMS.HARMONIC_NEXUS,
        'HIGH_SUBSTRATE_COHERENCE',
        {
          coherence: nexusState.substrateCoherence,
          syncQuality: nexusState.syncQuality,
          dimensionalAlignment: nexusState.dimensionalAlignment
        }
      );
    }

    // If timeline divergence detected, alert systems
    if (nexusState.timelineDivergence > 0.3) {
      console.warn('⚠️ Harmonic Nexus: Timeline divergence detected', nexusState.timelineDivergence);
      temporalLadder.broadcast(
        SYSTEMS.HARMONIC_NEXUS,
        'TIMELINE_DIVERGENCE',
        {
          divergence: nexusState.timelineDivergence,
          syncStatus: nexusState.syncStatus
        }
      );
    }
  }

  /**
   * Cleanup
   */
  destroy() {
    this.deactivate();
    temporalLadder.unregisterSystem(SYSTEMS.HARMONIC_NEXUS);
    this.listeners = [];
  }
}

// Singleton instance
export const harmonicNexus = new HarmonicNexusOrchestrator();
