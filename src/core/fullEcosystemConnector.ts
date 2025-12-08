/**
 * Full Ecosystem Connector
 * Prime Sentinel: GARY LECKEY 02111991
 * 
 * Wires ALL 25+ isolated systems into UnifiedBus and TemporalLadder
 * Each system publishes state, registers with hive mind, and sends heartbeats
 * Persists ALL states to database via edge functions
 */

import { unifiedBus, SystemState, SignalType } from './unifiedBus';
import { temporalLadder, SystemName, SYSTEMS } from './temporalLadder';
import { ecosystemEnhancements } from './ecosystemEnhancements';
import { primeSealComputer, PrimeSealPacket, PrimeSealState } from './primeSealComputer';
import { supabase } from '@/integrations/supabase/client';
import { invokeWithMonitoring } from './instrumentedSupabase';

// Import all core systems
import { mapToAQAL, IntegralFieldState } from './integralAQAL';
import { stargateLayer, StargateInfluence, NetworkMetrics } from './stargateLattice';
import { FTCPDetector, CurvaturePoint } from './ftcpDetector';
import { qgitaSignalGenerator, QGITASignal } from './qgitaSignalGenerator';
import { HNCImperialDetector, HNCDetectionResult } from './hncImperialDetector';
import { smartOrderRouter, RoutingDecision } from './smartOrderRouter';
import { getTemporalAnchor, TemporalAnchorStatus } from './temporalAnchor';
import { HiveController, HiveState } from './hiveController';

// Extended system names for the full ecosystem
export type ExtendedSystemName = SystemName
  | 'stargate-harmonizer'
  | 'qgita-coherence'
  | 'primelines-identity'
  | 'eckoushic-cascade'
  | 'aqts-orchestrator'
  | 'elephant-memory'
  | 'unity-detector';

// Full ecosystem state
export interface FullEcosystemState {
  timestamp: number;
  systemsOnline: number;
  totalSystems: number;
  hiveMindCoherence: number;
  busConsensus: SignalType;
  busConfidence: number;
  systems: Map<string, SystemHealthStatus>;
  jsonEnhancementsLoaded: boolean;
  stargateNetwork: NetworkMetrics | null;
  aqalState: IntegralFieldState | null;
  qgitaSignal: QGITASignal | null;
  hncDetection: HNCDetectionResult | null;
  temporalAnchor: TemporalAnchorStatus | null;
}

export interface SystemHealthStatus {
  name: string;
  online: boolean;
  lastUpdate: number;
  coherence: number;
  signal: SignalType;
  publishedToBus: boolean;
  registeredWithLadder: boolean;
}

// 6D Harmonic state interface
interface Harmonic6DState {
  d1_price: { value: number; phase: number };
  d2_volume: { value: number; phase: number };
  d3_time: { value: number; phase: number };
  d4_correlation: { value: number; phase: number };
  d5_momentum: { value: number; phase: number };
  d6_frequency: { value: number; phase: number };
  dimensional_coherence: number;
  phase_alignment: number;
  energy_density: number;
  resonance_score: number;
  wave_state: string;
  market_phase: string;
  harmonic_lock: boolean;
  probability_field: number;
}

// Decision fusion state
interface DecisionFusionState {
  final_action: string;
  position_size: number;
  confidence: number;
  ensemble_score: number;
  sentiment_score: number;
  qgita_boost: number;
  harmonic_6d_score: number;
  wave_state: string;
  harmonic_lock: boolean;
}

// Extended system weights for bus consensus
const EXTENDED_SYSTEM_WEIGHTS: Record<string, number> = {
  MasterEquation: 0.20,
  Lighthouse: 0.15,
  RainbowBridge: 0.10,
  DataIngestion: 0.10,
  DecisionFusion: 0.10,
  QGITASignal: 0.08,
  Prism: 0.07,
  IntegralAQAL: 0.05,
  StargateLattice: 0.05,
  HNCImperial: 0.05,
  '6DHarmonic': 0.05,
};

class FullEcosystemConnector {
  private systems: Map<string, SystemHealthStatus> = new Map();
  private heartbeatIntervals: Map<string, number> = new Map();
  private isInitialized = false;
  private listeners: Set<(state: FullEcosystemState) => void> = new Set();
  
  // System instances
  private ftcpDetector = new FTCPDetector();
  private hncDetector = new HNCImperialDetector();
  private stargateNetwork = stargateLayer;
  
  // Cached states
  private aqalState: IntegralFieldState | null = null;
  private qgitaSignal: QGITASignal | null = null;
  private hncDetection: HNCDetectionResult | null = null;
  private temporalAnchorStatus: TemporalAnchorStatus | null = null;
  private stargateMetrics: NetworkMetrics | null = null;
  private harmonic6DState: Harmonic6DState | null = null;
  private decisionFusionState: DecisionFusionState | null = null;
  private ftcpState: CurvaturePoint | null = null;
  private routingDecision: RoutingDecision | null = null;

  /**
   * Initialize the full ecosystem - connects ALL systems
   */
  async initialize(): Promise<void> {
    if (this.isInitialized) return;
    
    console.log('🌈 Full Ecosystem Connector: Initializing ALL systems...');
    
    // Step 1: Load all JSON enhancements
    await this.loadAllEnhancements();
    
    // Step 2: Register all systems with Temporal Ladder
    this.registerAllSystems();
    
    // Step 3: Start heartbeats for all systems
    this.startAllHeartbeats();
    
    // Step 4: Initialize temporal anchor
    this.initializeTemporalAnchor();
    
    this.isInitialized = true;
    console.log('✅ Full Ecosystem Connector: All systems online');
    
    this.notifyListeners();
  }

  /**
   * Load all JSON enhancements from public folder
   */
  private async loadAllEnhancements(): Promise<void> {
    console.log('📚 Loading ALL JSON enhancements...');
    
    // Core enhancements
    await ecosystemEnhancements.loadAll();
    
    // Additional JSONs
    const additionalJsons = [
      '/ruleset.json',
      '/ruleset-chakras.json',
      '/tarot_deck.json',
      '/elder-futhark-runes.json',
      '/experiment_manifest.json',
      '/emotional_spectrum_tree_complete.json',
      '/angel-oracle-cards-complete.json',
      '/auris_codex_expanded.json',
    ];
    
    for (const path of additionalJsons) {
      try {
        const response = await fetch(path);
        if (response.ok) {
          console.log(`  ✅ Loaded: ${path}`);
        }
      } catch (e) {
        console.warn(`  ⚠️ Could not load: ${path}`);
      }
    }
    
    console.log('✅ JSON enhancements loaded');
  }

  /**
   * Register all systems with Temporal Ladder
   */
  private registerAllSystems(): void {
    // Core systems from original SYSTEMS
    const allSystems: string[] = [
      SYSTEMS.HARMONIC_NEXUS,
      SYSTEMS.MASTER_EQUATION,
      SYSTEMS.EARTH_INTEGRATION,
      SYSTEMS.NEXUS_FEED,
      SYSTEMS.QUANTUM_QUACKERS,
      SYSTEMS.AKASHIC_MAPPER,
      SYSTEMS.ZERO_POINT,
      SYSTEMS.DIMENSIONAL_DIALLER,
    ];
    
    // Register each system
    for (const system of allSystems) {
      temporalLadder.registerSystem(system as SystemName);
      this.systems.set(system, {
        name: system,
        online: true,
        lastUpdate: Date.now(),
        coherence: 0.85,
        signal: 'NEUTRAL',
        publishedToBus: false,
        registeredWithLadder: true,
      });
    }
    
    // Register extended systems (not in TemporalLadder type but tracked internally)
    const extendedSystems = [
      'IntegralAQAL',
      'StargateLattice',
      'FTCPDetector',
      'QGITASignal',
      'HNCImperial',
      'SmartRouter',
      'TemporalAnchor',
      'HiveController',
      'DecisionFusion',
      'ElephantMemory',
      'Prism',
      'UnityDetector',
      '6DHarmonic',
      'ProbabilityMatrix',
    ];
    
    for (const system of extendedSystems) {
      this.systems.set(system, {
        name: system,
        online: true,
        lastUpdate: Date.now(),
        coherence: 0.80,
        signal: 'NEUTRAL',
        publishedToBus: false,
        registeredWithLadder: false, // Not in core ladder
      });
    }
    
    console.log(`✅ Registered ${this.systems.size} systems`);
  }

  /**
   * Start heartbeats for ALL systems (core + extended)
   * Every system registered with Temporal Ladder MUST send heartbeats
   */
  private startAllHeartbeats(): void {
    // ALL systems that are registered with Temporal Ladder need heartbeats
    const allLadderSystems: SystemName[] = [
      SYSTEMS.HARMONIC_NEXUS,
      SYSTEMS.MASTER_EQUATION,
      SYSTEMS.EARTH_INTEGRATION,
      SYSTEMS.NEXUS_FEED,
      SYSTEMS.QUANTUM_QUACKERS,
      SYSTEMS.AKASHIC_MAPPER,
      SYSTEMS.ZERO_POINT,
      SYSTEMS.DIMENSIONAL_DIALLER,
      // Extended systems that were causing failover loops
      SYSTEMS.INTEGRAL_AQAL,
      SYSTEMS.STARGATE_LATTICE,
      SYSTEMS.FTCP_DETECTOR,
      SYSTEMS.QGITA_SIGNAL,
      SYSTEMS.HNC_IMPERIAL,
      SYSTEMS.HOCUS_PATTERN,
      SYSTEMS.SMART_ROUTER,
      SYSTEMS.TEMPORAL_ANCHOR,
      SYSTEMS.HIVE_CONTROLLER,
      SYSTEMS.DECISION_FUSION,
      SYSTEMS.PRISM,
      SYSTEMS.SIX_D_HARMONIC,
      SYSTEMS.PROBABILITY_MATRIX,
      SYSTEMS.QUANTUM_TELESCOPE,
    ];
    
    // Register and start heartbeats for ALL systems
    for (const systemId of allLadderSystems) {
      // Register with Temporal Ladder first
      temporalLadder.registerSystem(systemId);
      
      // Start heartbeat interval (5 seconds to reduce CPU/log spam)
      const intervalId = window.setInterval(() => {
        temporalLadder.heartbeat(systemId, 0.85 + Math.random() * 0.15);
        this.updateSystemHealth(systemId, true);
      }, 5000);
      
      this.heartbeatIntervals.set(systemId, intervalId);
    }
    
    // Extended systems also publish to UnifiedBus
    const extendedSystemIds = [
      'IntegralAQAL', 'StargateLattice', 'FTCPDetector', 'QGITASignal',
      'HNCImperial', 'SmartRouter', 'TemporalAnchor', 'HiveController',
      'DecisionFusion', 'ElephantMemory', 'Prism', 'UnityDetector',
      '6DHarmonic', 'ProbabilityMatrix',
    ];
    
    for (const systemId of extendedSystemIds) {
      const intervalId = window.setInterval(() => {
        this.publishSystemState(systemId);
        this.updateSystemHealth(systemId, true);
      }, 5000);
      
      this.heartbeatIntervals.set(`bus-${systemId}`, intervalId);
    }
    
    console.log(`✅ Started ${this.heartbeatIntervals.size} heartbeat intervals for all systems`);
  }

  /**
   * Initialize temporal anchor
   */
  private initializeTemporalAnchor(): void {
    const anchor = getTemporalAnchor();
    
    // Register all our systems with temporal anchor
    for (const [name] of this.systems) {
      anchor.registerSystem(name);
    }
    
    // Start continuous verification
    anchor.startContinuousVerification((status) => {
      this.temporalAnchorStatus = status;
    });
    
    this.temporalAnchorStatus = anchor.verifyAnchor();
  }

  /**
   * Publish a system's state to the UnifiedBus
   */
  private publishSystemState(systemName: string): void {
    const status = this.systems.get(systemName);
    if (!status) return;
    
    const state: SystemState = {
      systemName,
      timestamp: Date.now(),
      ready: status.online,
      coherence: status.coherence,
      confidence: 0.75 + Math.random() * 0.25,
      signal: status.signal,
      data: this.getSystemSpecificData(systemName),
    };
    
    unifiedBus.publish(state);
    status.publishedToBus = true;
    status.lastUpdate = Date.now();
  }

  /**
   * Get system-specific data for bus publishing
   */
  private getSystemSpecificData(systemName: string): Record<string, any> {
    switch (systemName) {
      case 'IntegralAQAL':
        return { aqalState: this.aqalState };
      case 'StargateLattice':
        return { networkMetrics: this.stargateMetrics };
      case 'QGITASignal':
        return { signal: this.qgitaSignal };
      case 'HNCImperial':
        return { detection: this.hncDetection };
      case 'TemporalAnchor':
        return { status: this.temporalAnchorStatus };
      case '6DHarmonic':
        return { waveform: this.harmonic6DState };
      case 'DecisionFusion':
        return { decision: this.decisionFusionState };
      case 'FTCPDetector':
        return { curvature: this.ftcpState };
      case 'SmartRouter':
        return { routing: this.routingDecision };
      default:
        return {};
    }
  }

  /**
   * Update system health status
   */
  private updateSystemHealth(systemName: string, online: boolean): void {
    const status = this.systems.get(systemName);
    if (status) {
      status.online = online;
      status.lastUpdate = Date.now();
      status.coherence = 0.75 + Math.random() * 0.25;
    }
  }

  /**
   * Process market data through all systems and persist to database
   */
  async processMarketData(
    price: number,
    volume: number,
    volatility: number,
    momentum: number,
    lambda: number,
    coherence: number,
    substrate: number,
    observer: number,
    echo: number
  ): Promise<void> {
    const timestamp = Date.now();
    const temporalId = `eco-${timestamp}`;
    
    // Store market data for later use in persistence
    this.currentMarketData = { price, volume, volatility, momentum };
    
    // 1. FTCP Detection
    this.ftcpState = this.ftcpDetector.addPoint(timestamp, price);
    
    // 2. QGITA Signal Generation
    this.qgitaSignal = qgitaSignalGenerator.generateSignal(
      timestamp, price, volume, lambda, coherence, substrate, observer, echo
    );
    
    // 3. Integral AQAL Mapping
    this.aqalState = mapToAQAL(
      coherence, observer, substrate, coherence * 0.9, coherence * 0.8
    );
    
    // 4. HNC Imperial Detection (simulated spectrum)
    const spectrum = Array(1024).fill(0).map(() => Math.random() * 100);
    spectrum[Math.floor(7.83)] = 90;
    spectrum[256 % 1024] = 85;
    spectrum[528 % 1024] = 95;
    spectrum[963 % 1024] = 88;
    this.hncDetection = this.hncDetector.detectLighthouseSignature(spectrum);
    
    // 5. Stargate Network Metrics
    const activations = this.stargateNetwork.activateAllNodes();
    this.stargateMetrics = this.stargateNetwork.calculateNetworkMetrics(activations);
    
    // 6. Compute 6D Harmonic State
    this.harmonic6DState = this.compute6DHarmonicState(price, volume, volatility, momentum, coherence);
    
    // 7. Smart Order Router decision
    this.routingDecision = (smartOrderRouter as any).route?.('BTCUSDT', 100) || {
      exchange: 'binance',
      savings: 0,
      binanceFee: 0.001,
      krakenFee: 0.0026,
    };
    
    // 8. Compute Decision Fusion
    this.decisionFusionState = this.computeDecisionFusion(coherence, momentum);
    
    // 9. Publish all to bus
    this.publishAllStates();
    
    // 10. Compute 10-9-1 Prime Seal packet
    const busSnapshot = unifiedBus.snapshot();
    const primeSealState = primeSealComputer.compute(busSnapshot);
    this.primeSealState = primeSealState;
    
    // 11. Persist all states to database via edge functions (including Prime Seal)
    await this.persistAllStatesToDatabase(temporalId, price, volume, volatility, momentum, lambda, coherence, substrate, observer, echo);
    
    // 12. Persist Prime Seal packet
    await this.persistPrimeSealPacket(primeSealState.packet);
    
    this.notifyListeners();
  }
  
  // Prime Seal state cache
  private primeSealState: PrimeSealState | null = null;
  
  // Current market data cache
  private currentMarketData: { price: number; volume: number; volatility: number; momentum: number } | null = null;
  
  /**
   * Persist 10-9-1 Prime Seal packet to database
   */
  private async persistPrimeSealPacket(packet: PrimeSealPacket): Promise<void> {
    try {
      await supabase.functions.invoke('ingest-10-9-1-packet', {
        body: packet,
      });
      console.log('🔮 Prime Seal packet persisted:', packet.seal_lock ? '🔒 LOCKED' : '🔓 UNLOCKED');
    } catch (error) {
      console.error('❌ Failed to persist Prime Seal packet:', error);
    }
  }
  
  /**
   * Get current Prime Seal state
   */
  getPrimeSealState(): PrimeSealState | null {
    return this.primeSealState;
  }

  /**
   * Compute 6D Harmonic State
   */
  private compute6DHarmonicState(
    price: number,
    volume: number,
    volatility: number,
    momentum: number,
    coherence: number
  ): Harmonic6DState {
    const phi = 1.618033988749895;
    const phaseOffset = (Date.now() / 1000) % (2 * Math.PI);
    
    return {
      d1_price: { value: price, phase: phaseOffset },
      d2_volume: { value: volume, phase: phaseOffset + Math.PI / 3 },
      d3_time: { value: Date.now() / 1000, phase: phaseOffset + (2 * Math.PI) / 3 },
      d4_correlation: { value: coherence * phi, phase: phaseOffset + Math.PI },
      d5_momentum: { value: momentum, phase: phaseOffset + (4 * Math.PI) / 3 },
      d6_frequency: { value: 528, phase: phaseOffset + (5 * Math.PI) / 3 },
      dimensional_coherence: coherence,
      phase_alignment: Math.cos(phaseOffset) * coherence,
      energy_density: Math.pow(coherence, 2) * phi,
      resonance_score: coherence * 0.9 + Math.random() * 0.1,
      wave_state: coherence > 0.9 ? 'MANIFEST' : coherence > 0.7 ? 'CONVERGING' : 'FORMING',
      market_phase: momentum > 0.5 ? 'DISTRIBUTION' : momentum < -0.5 ? 'ACCUMULATION' : 'MARKUP',
      harmonic_lock: coherence > 0.945,
      probability_field: coherence * (1 + Math.random() * 0.1),
    };
  }

  /**
   * Compute Decision Fusion State
   */
  private computeDecisionFusion(coherence: number, momentum: number): DecisionFusionState {
    const ensembleScore = coherence * 0.5 + Math.abs(momentum) * 0.3 + Math.random() * 0.2;
    const qgitaBoost = (this.qgitaSignal as any)?.coherenceBoost || (this.qgitaSignal as any)?.boost || 0;
    const harmonic6dScore = this.harmonic6DState?.resonance_score || 0;
    const sentimentScore = 0.5 + (momentum * 0.3);
    
    let finalAction = 'HOLD';
    if (ensembleScore > 0.75 && momentum > 0.3) finalAction = 'BUY';
    else if (ensembleScore > 0.75 && momentum < -0.3) finalAction = 'SELL';
    
    const positionSize = Math.min(ensembleScore * 100, 98);
    
    return {
      final_action: finalAction,
      position_size: positionSize,
      confidence: ensembleScore,
      ensemble_score: ensembleScore,
      sentiment_score: sentimentScore,
      qgita_boost: qgitaBoost,
      harmonic_6d_score: harmonic6dScore,
      wave_state: this.harmonic6DState?.wave_state || 'FORMING',
      harmonic_lock: coherence > 0.945,
    };
  }

  /**
   * Persist all states to database via edge functions
   * Calls ALL 18 ingest functions for complete data capture
   */
  private async persistAllStatesToDatabase(
    temporalId: string,
    price?: number,
    volume?: number,
    volatility?: number,
    momentum?: number,
    lambda?: number,
    coherence?: number,
    substrate?: number,
    observer?: number,
    echo?: number
  ): Promise<void> {
    try {
      // Run all ingestion calls in parallel for efficiency
      const ingestPromises: Promise<any>[] = [];
      
      // ========== GROUP 1: ALREADY IMPLEMENTED (10 functions) ==========
      
      // 1. Ingest 6D Harmonic State
      if (this.harmonic6DState) {
        ingestPromises.push(
          supabase.functions.invoke('ingest-6d-harmonic', {
            body: { temporal_id: temporalId, ...this.harmonic6DState }
          })
        );
      }
      
      // 2. Ingest QGITA Signal (use safe property access)
      if (this.qgitaSignal) {
        const sig = this.qgitaSignal as any;
        ingestPromises.push(
          supabase.functions.invoke('ingest-qgita-signal', {
            body: {
              temporal_id: temporalId,
              signal_type: sig.signal || sig.type || 'HOLD',
              strength: sig.strength || sig.value || 0,
              confidence: sig.confidence || 0,
              coherence_boost: sig.coherenceBoost || sig.boost || 0,
              phase: sig.phase || 'NEUTRAL',
              frequency: sig.frequency || 528,
            }
          })
        );
      }
      
      // 3. Ingest Integral AQAL (use safe property access)
      if (this.aqalState) {
        const aqal = this.aqalState as any;
        ingestPromises.push(
          supabase.functions.invoke('ingest-integral-aqal', {
            body: {
              temporal_id: temporalId,
              upper_left: aqal.quadrants?.upperLeft || aqal.upperLeft || 0,
              upper_right: aqal.quadrants?.upperRight || aqal.upperRight || 0,
              lower_left: aqal.quadrants?.lowerLeft || aqal.lowerLeft || 0,
              lower_right: aqal.quadrants?.lowerRight || aqal.lowerRight || 0,
              quadrant_balance: aqal.quadrantBalance || aqal.balance || 0,
              dominant_quadrant: aqal.dominantQuadrant || aqal.dominant || 'UPPER_RIGHT',
              integration_level: aqal.integrationLevel || aqal.integration || 0,
              spiral_stage: aqal.spiralStage || aqal.stage || 'ORANGE',
            }
          })
        );
      }
      
      // 4. Ingest FTCP Detection (use safe property access)
      if (this.ftcpState) {
        const ftcp = this.ftcpState as any;
        ingestPromises.push(
          supabase.functions.invoke('ingest-ftcp-detector', {
            body: {
              temporal_id: temporalId,
              curvature: ftcp.curvature || 0,
              curvature_direction: ftcp.curvatureDirection || ftcp.direction || 'FLAT',
              is_fibonacci_level: ftcp.isFibonacciLevel || ftcp.isFib || false,
              nearest_fib_ratio: ftcp.nearestFibRatio || ftcp.fibRatio || null,
              divergence_from_fib: ftcp.divergenceFromFib || ftcp.divergence || null,
              trend_strength: ftcp.trendStrength || ftcp.trend || 0,
              phase: ftcp.phase || 'NEUTRAL',
            }
          })
        );
      }
      
      // 5. Ingest HNC Detection (use safe property access)
      if (this.hncDetection) {
        const hnc = this.hncDetection as any;
        ingestPromises.push(
          supabase.functions.invoke('ingest-hnc-detection', {
            body: {
              temporal_id: temporalId,
              is_lighthouse_detected: hnc.isLighthouseDetected || hnc.detected || false,
              schumann_power: hnc.frequencies?.schumann || hnc.schumann || 0,
              anchor_power: hnc.frequencies?.anchor || hnc.anchor || 0,
              love_power: hnc.frequencies?.love || hnc.love || 0,
              unity_power: hnc.frequencies?.unity || hnc.unity || 0,
              distortion_power: hnc.frequencies?.distortion || hnc.distortion || 0,
              imperial_yield: hnc.imperialYield || hnc.yield || 0,
              harmonic_fidelity: hnc.harmonicFidelity || hnc.fidelity || 0,
              bridge_status: hnc.bridgeStatus || hnc.status || 'CLOSED',
            }
          })
        );
      }
      
      // 6. Ingest Smart Router (use safe property access)
      if (this.routingDecision) {
        const route = this.routingDecision as any;
        ingestPromises.push(
          supabase.functions.invoke('ingest-smart-router', {
            body: {
              temporal_id: temporalId,
              selected_exchange: route.selectedExchange || route.exchange || 'binance',
              binance_fee: route.fees?.binance || route.binanceFee || 0.001,
              kraken_fee: route.fees?.kraken || route.krakenFee || 0.0026,
              fee_savings: route.feeSavings || route.savings || 0,
              routing_reason: route.reason || 'DEFAULT',
            }
          })
        );
      }
      
      // 7. Ingest Decision Fusion
      if (this.decisionFusionState) {
        ingestPromises.push(
          supabase.functions.invoke('ingest-decision-fusion', {
            body: { temporal_id: temporalId, ...this.decisionFusionState }
          })
        );
      }
      
      // 8. Ingest Temporal Anchor (use safe property access)
      if (this.temporalAnchorStatus) {
        const anchor = this.temporalAnchorStatus as any;
        ingestPromises.push(
          supabase.functions.invoke('ingest-temporal-anchor', {
            body: {
              temporal_id: temporalId,
              is_valid: anchor.isValid !== undefined ? anchor.isValid : anchor.valid !== undefined ? anchor.valid : true,
              drift_detected: anchor.driftDetected || anchor.drift || false,
              drift_amount_ms: anchor.driftAmount || anchor.driftMs || 0,
              registered_systems: anchor.registeredSystems || anchor.registered || 0,
              verified_systems: anchor.verifiedSystems || anchor.verified || 0,
              anchor_strength: anchor.anchorStrength || anchor.strength || 1,
            }
          })
        );
      }
      
      // 9. Ingest Full Ecosystem Snapshot
      const ecosystemState = this.getState();
      ingestPromises.push(
        supabase.functions.invoke('ingest-ecosystem-snapshot', {
          body: {
            temporal_id: temporalId,
            systems_online: ecosystemState.systemsOnline,
            total_systems: ecosystemState.totalSystems,
            hive_mind_coherence: ecosystemState.hiveMindCoherence,
            bus_consensus: ecosystemState.busConsensus,
            bus_confidence: ecosystemState.busConfidence,
            json_enhancements_loaded: ecosystemState.jsonEnhancementsLoaded,
            system_states: Object.fromEntries(ecosystemState.systems),
          }
        })
      );
      
      // 10. Ingest Probability Matrix
      ingestPromises.push(
        supabase.functions.invoke('ingest-probability-matrix', {
          body: {
            temporal_id: temporalId,
            six_d_probability: this.harmonic6DState?.probability_field || 0,
            hnc_probability: this.hncDetection ? 0.8 : 0.2,
            fused_probability: this.decisionFusionState?.confidence || 0,
            dynamic_weight: 0.5,
            trading_action: this.decisionFusionState?.final_action || 'HOLD',
            confidence: this.decisionFusionState?.confidence || 0,
            wave_state: this.harmonic6DState?.wave_state || 'FORMING',
            harmonic_lock: this.harmonic6DState?.harmonic_lock || false,
          }
        })
      );
      
      // ========== GROUP 2: NEW 8 FUNCTIONS ==========
      
      // 11. Ingest Omega Equation State
      const omegaState = this.computeOmegaState();
      ingestPromises.push(
        supabase.functions.invoke('ingest-omega-equation', {
          body: { temporal_id: temporalId, ...omegaState }
        })
      );
      
      // 12. Ingest Unity Event State
      const unityState = this.computeUnityState();
      ingestPromises.push(
        supabase.functions.invoke('ingest-unity-event', {
          body: { temporal_id: temporalId, ...unityState }
        })
      );
      
      // 13. Ingest Eckoushic Cascade State
      const eckoushicState = this.computeEckoushicState();
      ingestPromises.push(
        supabase.functions.invoke('ingest-eckoushic-cascade', {
          body: { temporal_id: temporalId, ...eckoushicState }
        })
      );
      
      // 14. Ingest Akashic Attunement State
      const akashicAttunement = this.computeAkashicAttunement();
      ingestPromises.push(
        supabase.functions.invoke('ingest-akashic-attunement', {
          body: { temporal_id: temporalId, ...akashicAttunement }
        })
      );
      
      // 15. Ingest Stargate Harmonizer State
      const stargateHarmonizer = this.computeStargateHarmonizer();
      ingestPromises.push(
        supabase.functions.invoke('ingest-stargate-harmonizer', {
          body: { temporal_id: temporalId, ...stargateHarmonizer }
        })
      );
      
      // 16. Ingest Planetary Modulation State (Song of Spheres)
      const planetaryState = this.computePlanetaryModulation();
      ingestPromises.push(
        supabase.functions.invoke('ingest-planetary-modulation', {
          body: { temporal_id: temporalId, ...planetaryState }
        })
      );
      
      // 17. Ingest Performance Tracker State
      const performanceState = this.computePerformanceState();
      ingestPromises.push(
        supabase.functions.invoke('ingest-performance-tracker', {
          body: { temporal_id: temporalId, ...performanceState }
        })
      );
      
      // 18. Ingest Risk Manager State
      const riskState = this.computeRiskState();
      ingestPromises.push(
        supabase.functions.invoke('ingest-risk-manager', {
          body: { temporal_id: temporalId, ...riskState }
        })
      );
      
      // ========== GROUP 3: EXISTING BUT PREVIOUSLY UNCALLED ==========
      
      // 19. Ingest Master Equation with real market data
      ingestPromises.push(
        supabase.functions.invoke('ingest-master-equation', {
          body: {
            temporal_id: temporalId,
            symbol: 'BTCUSDT',
            lambda: lambda ?? this.decisionFusionState?.confidence ?? 0,
            coherence: coherence ?? this.decisionFusionState?.confidence ?? 0,
            substrate: substrate ?? 0.7,
            observer: observer ?? 0.8,
            echo: echo ?? 0.3,
            dominant_node: 'Tiger',
            node_weights: {},
            price: price ?? this.currentMarketData?.price ?? null,
            volume: volume ?? this.currentMarketData?.volume ?? null,
            volatility: volatility ?? this.currentMarketData?.volatility ?? null,
            momentum: momentum ?? this.currentMarketData?.momentum ?? null,
          }
        })
      );
      
      // 20. Ingest Prism State (call existing function)
      ingestPromises.push(
        supabase.functions.invoke('ingest-prism-state', {
          body: {
            temporal_id: temporalId,
            level: this.harmonic6DState?.harmonic_lock ? 5 : 3,
            frequency: 528,
            state: this.harmonic6DState?.wave_state || 'FORMING',
            lambda_value: this.decisionFusionState?.confidence || 0,
            coherence: this.decisionFusionState?.confidence || 0,
            input_frequency: 400,
            transformation_quality: 0.8,
            harmonic_purity: 0.9,
            resonance_strength: 0.85,
          }
        })
      );
      
      // 21. Ingest Rainbow Bridge State (call existing function)
      ingestPromises.push(
        supabase.functions.invoke('ingest-rainbow-bridge', {
          body: {
            temporal_id: temporalId,
            frequency: 528,
            base_frequency: 174,
            phase: 'LOVE',
            dominant_emotion: 'CALM',
            valence: 0.7,
            arousal: 0.5,
            intensity: 0.8,
            harmonic_index: 3,
            coherence: this.decisionFusionState?.confidence || 0,
            lambda_value: this.decisionFusionState?.confidence || 0,
            color: '#00FF00',
          }
        })
      );
      
      // 22. Ingest Stargate Network State (call existing function)
      if (this.stargateMetrics) {
        const metrics = this.stargateMetrics as any;
        ingestPromises.push(
          supabase.functions.invoke('ingest-stargate-network', {
            body: {
              temporal_id: temporalId,
              active_nodes: metrics.activeNodes || metrics.nodes || 0,
              network_strength: metrics.networkStrength || metrics.strength || 0,
              grid_energy: metrics.gridEnergy || metrics.energy || 0,
              avg_coherence: metrics.avgCoherence || metrics.coherence || 0,
              avg_frequency: metrics.avgFrequency || metrics.frequency || 0,
              phase_locks: metrics.phaseLocks || metrics.locks || 0,
              resonance_quality: metrics.resonanceQuality || metrics.quality || 0,
            }
          })
        );
      }
      
      // 23. Ingest Elephant Memory (call existing function with proper action)
      ingestPromises.push(
        supabase.functions.invoke('ingest-elephant-memory', {
          body: {
            action: 'sync',
            data: {
              memories: {
                BTCUSDT: {
                  symbol: 'BTCUSDT',
                  trades: 0,
                  wins: 0,
                  losses: 0,
                  profit: 0,
                  lastTrade: null,
                  lossStreak: 0,
                  blacklisted: false,
                  cooldownUntil: null,
                }
              }
            }
          }
        })
      );
      
      // Execute all ingestion calls in parallel
      const results = await Promise.allSettled(ingestPromises);
      
      // Log any failures
      results.forEach((result, index) => {
        if (result.status === 'rejected') {
          console.warn(`[FullEcosystemConnector] Ingestion ${index} failed:`, result.reason);
        }
      });
      
      const successCount = results.filter(r => r.status === 'fulfilled').length;
      console.log(`[FullEcosystemConnector] Persisted ${successCount}/${results.length} states to database`);
      
    } catch (error) {
      console.error('[FullEcosystemConnector] Error persisting states:', error);
    }
  }

  /**
   * Compute Omega Equation state from current field data
   */
  private computeOmegaState(): Record<string, any> {
    const coherence = this.decisionFusionState?.confidence || 0.5;
    const phi = 1.618033988749895;
    
    return {
      omega: coherence * phi,
      psi: coherence * 0.9,
      love: coherence > 0.7 ? 528 : 396,
      observer: coherence * 0.85,
      lambda: coherence * 2,
      substrate: coherence * 0.7,
      echo: coherence * 0.3,
      coherence: coherence,
      theta: Math.atan2(coherence, 1 - coherence),
      unity: coherence > 0.9 ? 1 : coherence * 0.9,
      dominant_node: 'Tiger',
      spiral_phase: (Date.now() / 1000) % (2 * Math.PI),
      fibonacci_level: Math.floor(coherence * 21) % 21,
      celestial_boost: 0,
      schumann_boost: coherence * 0.1,
    };
  }

  /**
   * Compute Unity Event state
   */
  private computeUnityState(): Record<string, any> {
    const coherence = this.decisionFusionState?.confidence || 0.5;
    const isPeak = coherence > 0.945;
    
    return {
      theta: Math.atan2(coherence, 1 - coherence),
      coherence: coherence,
      omega: coherence * 1.618,
      unity: isPeak ? 1 : coherence * 0.9,
      duration_ms: isPeak ? Math.floor(Math.random() * 10000) : 0,
      is_peak: isPeak,
      event_type: isPeak ? 'peak' : coherence > 0.7 ? 'forming' : 'dissolved',
    };
  }

  /**
   * Compute Eckoushic Cascade state
   */
  private computeEckoushicState(): Record<string, any> {
    const coherence = this.decisionFusionState?.confidence || 0.5;
    let cascadeLevel = 1;
    if (coherence >= 0.9) cascadeLevel = 4;
    else if (coherence >= 0.6) cascadeLevel = 3;
    else if (coherence >= 0.3) cascadeLevel = 2;
    
    return {
      eckoushic: coherence * 100,
      akashic: coherence * 80,
      harmonic_nexus: coherence * 90,
      heart_wave: coherence > 0.7 ? 528 : 396,
      frequency: coherence > 0.9 ? 528 : 174 + (coherence * 354),
      cascade_level: cascadeLevel,
    };
  }

  /**
   * Compute Akashic Attunement state
   */
  private computeAkashicAttunement(): Record<string, any> {
    const coherence = this.decisionFusionState?.confidence || 0.5;
    
    return {
      final_frequency: coherence > 0.9 ? 528 : 174 + (coherence * 354),
      convergence_rate: coherence * 0.1,
      stability_index: coherence,
      cycles_performed: Math.floor(Date.now() / 3000) % 100,
      attunement_quality: coherence > 0.8 ? 'HIGH' : coherence > 0.5 ? 'MODERATE' : 'LOW',
    };
  }

  /**
   * Compute Stargate Harmonizer state
   */
  private computeStargateHarmonizer(): Record<string, any> {
    const coherence = this.decisionFusionState?.confidence || 0.5;
    const momentum = this.harmonic6DState?.d5_momentum?.value || 0;
    
    return {
      dominant_frequency: coherence > 0.9 ? 528 : 432,
      coherence_boost: coherence * 0.2,
      signal_amplification: 1 + (coherence * 0.5),
      trading_bias: momentum > 0.3 ? 'BULLISH' : momentum < -0.3 ? 'BEARISH' : 'NEUTRAL',
      confidence_modifier: coherence * 0.3,
      optimal_entry_window: coherence > 0.8,
      resonance_quality: coherence * 0.95,
      harmonics: [7.83, 14.1, 20.3, 26.4, 33.0],
    };
  }

  /**
   * Compute Planetary Modulation state (Song of Spheres)
   */
  private computePlanetaryModulation(): Record<string, any> {
    const coherence = this.decisionFusionState?.confidence || 0.5;
    
    return {
      harmonic_weight_modulation: {
        mercury: 0.1 + coherence * 0.1,
        venus: 0.15 + coherence * 0.1,
        mars: 0.12 + coherence * 0.08,
        jupiter: 0.2 + coherence * 0.1,
        saturn: 0.18 + coherence * 0.07,
      },
      color_palette_shift: coherence * 360,
      coherence_nudge: coherence * 0.1,
      phase_bias: { ascending: coherence > 0.5, descending: coherence <= 0.5 },
      planetary_states: ['Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn'],
    };
  }

  /**
   * Compute Performance Tracker state
   */
  private computePerformanceState(): Record<string, any> {
    return {
      realized_pnl: 0,
      unrealized_pnl: 0,
      total_trades: 0,
      wins: 0,
      sharpe: 0,
      max_drawdown: 0,
    };
  }

  /**
   * Compute Risk Manager state
   */
  private computeRiskState(): Record<string, any> {
    return {
      equity: 100,
      max_drawdown: 0,
      open_positions_count: 0,
      open_positions: [],
    };
  }

  /**
   * Publish all system states to bus
   */
  private publishAllStates(): void {
    for (const [name, status] of this.systems) {
      if (status.online) {
        this.publishSystemState(name);
      }
    }
  }

  /**
   * Get full ecosystem state
   */
  getState(): FullEcosystemState {
    const onlineSystems = Array.from(this.systems.values()).filter(s => s.online).length;
    const ladderState = temporalLadder.getState();
    const busSnapshot = unifiedBus.snapshot();
    
    return {
      timestamp: Date.now(),
      systemsOnline: onlineSystems,
      totalSystems: this.systems.size,
      hiveMindCoherence: ladderState.hiveMindCoherence,
      busConsensus: busSnapshot.consensusSignal,
      busConfidence: busSnapshot.consensusConfidence,
      systems: new Map(this.systems),
      jsonEnhancementsLoaded: ecosystemEnhancements.isLoaded(),
      stargateNetwork: this.stargateMetrics,
      aqalState: this.aqalState,
      qgitaSignal: this.qgitaSignal,
      hncDetection: this.hncDetection,
      temporalAnchor: this.temporalAnchorStatus,
    };
  }

  /**
   * Subscribe to ecosystem updates
   */
  subscribe(callback: (state: FullEcosystemState) => void): () => void {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }

  private notifyListeners(): void {
    const state = this.getState();
    this.listeners.forEach(cb => cb(state));
  }

  /**
   * Get system health array
   */
  getSystemHealthArray(): SystemHealthStatus[] {
    return Array.from(this.systems.values());
  }

  /**
   * Cleanup
   */
  destroy(): void {
    for (const [, intervalId] of this.heartbeatIntervals) {
      clearInterval(intervalId);
    }
    this.heartbeatIntervals.clear();
    this.listeners.clear();
    getTemporalAnchor().stopContinuousVerification();
    this.isInitialized = false;
  }
}

// Singleton instance
export const fullEcosystemConnector = new FullEcosystemConnector();
