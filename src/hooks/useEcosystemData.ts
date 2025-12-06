/**
 * useEcosystemData Hook
 * Provides real ecosystem data from UnifiedBus and FullEcosystemConnector
 * Replaces Math.random() with actual system states
 */

import { useState, useEffect, useCallback } from 'react';
import { unifiedBus, BusSnapshot, SignalType } from '../core/unifiedBus';
import { fullEcosystemConnector, FullEcosystemState, SystemHealthStatus } from '../core/fullEcosystemConnector';
import { temporalLadder, TemporalLadderState } from '../core/temporalLadder';

export interface EcosystemMetrics {
  // Core field metrics
  coherence: number;
  lambda: number;
  frequency: number;
  
  // Consensus
  consensusSignal: SignalType;
  consensusConfidence: number;
  
  // System health
  systemsOnline: number;
  totalSystems: number;
  hiveMindCoherence: number;
  
  // 6D Harmonic
  waveState: string;
  harmonicLock: boolean;
  probabilityFusion: number;
  
  // Prism
  prismLevel: number;
  prismState: string;
  loveLocked: boolean;
  
  // Rainbow Bridge
  phase: string;
  emotion: string;
  emotionalFrequency: number;
  
  // QGITA
  qgitaSignalType: SignalType;
  qgitaTier: number;
  qgitaConfidence: number;
  
  // Stargate
  stargateNetworkStrength: number;
  activeNodes: number;
  
  // AQAL
  evolutionaryLevel: number;
  dominantQuadrant: string;
  integrationScore: number;
  
  // HNC Imperial
  harmonicFidelity: number;
  rainbowBridgeOpen: boolean;
  criticalMassAchieved: boolean;
  
  // Temporal
  temporalAnchorStrength: number;
  surgeWindowActive: boolean;
}

export interface UseEcosystemDataReturn {
  metrics: EcosystemMetrics;
  busSnapshot: BusSnapshot | null;
  ecosystemState: FullEcosystemState | null;
  ladderState: TemporalLadderState | null;
  systemHealth: SystemHealthStatus[];
  isInitialized: boolean;
  refresh: () => void;
}

const DEFAULT_METRICS: EcosystemMetrics = {
  coherence: 0,
  lambda: 0,
  frequency: 528,
  consensusSignal: 'NEUTRAL',
  consensusConfidence: 0,
  systemsOnline: 0,
  totalSystems: 0,
  hiveMindCoherence: 0,
  waveState: 'FORMING',
  harmonicLock: false,
  probabilityFusion: 0.5,
  prismLevel: 1,
  prismState: 'FORMING',
  loveLocked: false,
  phase: 'NEUTRAL',
  emotion: 'calm',
  emotionalFrequency: 528,
  qgitaSignalType: 'NEUTRAL',
  qgitaTier: 3,
  qgitaConfidence: 0,
  stargateNetworkStrength: 0,
  activeNodes: 0,
  evolutionaryLevel: 0,
  dominantQuadrant: 'UL',
  integrationScore: 0,
  harmonicFidelity: 0,
  rainbowBridgeOpen: false,
  criticalMassAchieved: false,
  temporalAnchorStrength: 0,
  surgeWindowActive: false,
};

export function useEcosystemData(): UseEcosystemDataReturn {
  const [metrics, setMetrics] = useState<EcosystemMetrics>(DEFAULT_METRICS);
  const [busSnapshot, setBusSnapshot] = useState<BusSnapshot | null>(null);
  const [ecosystemState, setEcosystemState] = useState<FullEcosystemState | null>(null);
  const [ladderState, setLadderState] = useState<TemporalLadderState | null>(null);
  const [systemHealth, setSystemHealth] = useState<SystemHealthStatus[]>([]);
  const [isInitialized, setIsInitialized] = useState(false);

  // Extract metrics from ecosystem state
  const extractMetrics = useCallback((
    ecosystem: FullEcosystemState | null,
    bus: BusSnapshot | null,
    ladder: TemporalLadderState | null
  ): EcosystemMetrics => {
    if (!ecosystem && !bus) return DEFAULT_METRICS;

    // Get system states from bus
    const masterEq = bus?.states?.MasterEquation;
    const rainbow = bus?.states?.RainbowBridge;
    const prism = bus?.states?.Prism;
    const sixD = bus?.states?.['6DHarmonic'];
    
    return {
      // Core field
      coherence: masterEq?.coherence ?? ecosystem?.hiveMindCoherence ?? 0,
      lambda: masterEq?.data?.lambda ?? 0,
      frequency: rainbow?.data?.frequency ?? 528,
      
      // Consensus
      consensusSignal: bus?.consensusSignal ?? 'NEUTRAL',
      consensusConfidence: bus?.consensusConfidence ?? 0,
      
      // System health
      systemsOnline: ecosystem?.systemsOnline ?? bus?.systemsReady ?? 0,
      totalSystems: ecosystem?.totalSystems ?? bus?.totalSystems ?? 0,
      hiveMindCoherence: ladder?.hiveMindCoherence ?? ecosystem?.hiveMindCoherence ?? 0,
      
      // 6D Harmonic
      waveState: sixD?.data?.waveState ?? 'FORMING',
      harmonicLock: sixD?.data?.harmonicLock ?? false,
      probabilityFusion: sixD?.data?.fusedProbability ?? 0.5,
      
      // Prism
      prismLevel: prism?.data?.level ?? 1,
      prismState: prism?.data?.state ?? 'FORMING',
      loveLocked: prism?.data?.loveLocked ?? false,
      
      // Rainbow Bridge
      phase: rainbow?.data?.phase ?? 'NEUTRAL',
      emotion: rainbow?.data?.dominantEmotion ?? 'calm',
      emotionalFrequency: rainbow?.data?.frequency ?? 528,
      
      // QGITA (map HOLD to NEUTRAL for SignalType)
      qgitaSignalType: ecosystem?.qgitaSignal?.signalType === 'HOLD' 
        ? 'NEUTRAL' 
        : (ecosystem?.qgitaSignal?.signalType ?? 'NEUTRAL') as SignalType,
      qgitaTier: ecosystem?.qgitaSignal?.tier ?? 3,
      qgitaConfidence: ecosystem?.qgitaSignal?.confidence ?? 0,
      
      // Stargate
      stargateNetworkStrength: ecosystem?.stargateNetwork?.networkStrength ?? 0,
      activeNodes: ecosystem?.stargateNetwork?.activeNodes ?? 0,
      
      // AQAL
      evolutionaryLevel: ecosystem?.aqalState?.overallEvolutionaryLevel ?? 0,
      dominantQuadrant: ecosystem?.aqalState?.dominantQuadrant ?? 'UL',
      integrationScore: ecosystem?.aqalState?.integrationScore ?? 0,
      
      // HNC Imperial
      harmonicFidelity: ecosystem?.hncDetection?.harmonicFidelity ?? 0,
      rainbowBridgeOpen: ecosystem?.hncDetection?.rainbowBridgeOpen ?? false,
      criticalMassAchieved: ecosystem?.hncDetection?.criticalMassAchieved ?? false,
      
      // Temporal
      temporalAnchorStrength: ecosystem?.temporalAnchor?.anchorStrength ?? 0,
      surgeWindowActive: ecosystem?.temporalAnchor?.surgeWindowActive ?? false,
    };
  }, []);

  useEffect(() => {
    // Initialize ecosystem connector
    fullEcosystemConnector.initialize().then(() => {
      setIsInitialized(true);
    });

    // Subscribe to UnifiedBus
    const unsubBus = unifiedBus.subscribe((snapshot) => {
      setBusSnapshot(snapshot);
    });

    // Subscribe to Full Ecosystem
    const unsubEcosystem = fullEcosystemConnector.subscribe((state) => {
      setEcosystemState(state);
      setSystemHealth(Array.from(state.systems.values()));
    });

    // Subscribe to Temporal Ladder
    const unsubLadder = temporalLadder.subscribe((state) => {
      setLadderState(state);
    });

    // Initial states
    setBusSnapshot(unifiedBus.snapshot());
    setEcosystemState(fullEcosystemConnector.getState());
    setLadderState(temporalLadder.getState());
    setSystemHealth(fullEcosystemConnector.getSystemHealthArray());

    return () => {
      unsubBus();
      unsubEcosystem();
      unsubLadder();
    };
  }, []);

  // Update metrics when states change
  useEffect(() => {
    const newMetrics = extractMetrics(ecosystemState, busSnapshot, ladderState);
    setMetrics(newMetrics);
  }, [ecosystemState, busSnapshot, ladderState, extractMetrics]);

  const refresh = useCallback(() => {
    setBusSnapshot(unifiedBus.snapshot());
    setEcosystemState(fullEcosystemConnector.getState());
    setLadderState(temporalLadder.getState());
    setSystemHealth(fullEcosystemConnector.getSystemHealthArray());
  }, []);

  return {
    metrics,
    busSnapshot,
    ecosystemState,
    ladderState,
    systemHealth,
    isInitialized,
    refresh,
  };
}

/**
 * Simplified hook for components that just need basic metrics
 */
export function useBasicEcosystemMetrics() {
  const { metrics, isInitialized } = useEcosystemData();
  
  return {
    coherence: metrics.coherence,
    frequency: metrics.frequency,
    consensusSignal: metrics.consensusSignal,
    systemsOnline: metrics.systemsOnline,
    hiveMindCoherence: metrics.hiveMindCoherence,
    isInitialized,
  };
}

/**
 * Hook for Harmonic/Field visualizers
 */
export function useHarmonicMetrics() {
  const { metrics, busSnapshot, isInitialized } = useEcosystemData();
  
  return {
    frequency: metrics.frequency,
    coherence: metrics.coherence,
    waveState: metrics.waveState,
    harmonicLock: metrics.harmonicLock,
    prismLevel: metrics.prismLevel,
    prismState: metrics.prismState,
    loveLocked: metrics.loveLocked,
    harmonicFidelity: metrics.harmonicFidelity,
    probabilityFusion: metrics.probabilityFusion,
    phase: metrics.phase,
    isInitialized,
    busSnapshot,
  };
}

/**
 * Hook for Earth/Schumann analytics
 */
export function useEarthMetrics() {
  const { metrics, isInitialized } = useEcosystemData();
  
  // Derive Earth-specific metrics from ecosystem state
  const schumannFrequency = 7.83 + (metrics.coherence - 0.5) * 0.1;
  const magneticField = 0.7 + metrics.coherence * 0.25;
  const ionosphereActivity = 0.6 + metrics.hiveMindCoherence * 0.3;
  
  return {
    schumannFrequency,
    magneticField,
    ionosphereActivity,
    solarWind: 0.75 + (metrics.coherence - 0.5) * 0.2,
    geomagneticIndex: metrics.stargateNetworkStrength,
    coherenceBoost: Math.max(0, (0.15 - Math.abs(schumannFrequency - 7.83)) / 0.15) * 0.12,
    isInitialized,
  };
}

/**
 * Hook for QGITA/Signal analytics
 */
export function useSignalMetrics() {
  const { metrics, isInitialized } = useEcosystemData();
  
  return {
    signalType: metrics.qgitaSignalType,
    tier: metrics.qgitaTier,
    confidence: metrics.qgitaConfidence,
    consensusSignal: metrics.consensusSignal,
    consensusConfidence: metrics.consensusConfidence,
    isInitialized,
  };
}

/**
 * Hook for Stargate/Network analytics
 */
export function useStargateMetrics() {
  const { metrics, isInitialized } = useEcosystemData();
  
  return {
    networkStrength: metrics.stargateNetworkStrength,
    activeNodes: metrics.activeNodes,
    temporalAnchorStrength: metrics.temporalAnchorStrength,
    surgeWindowActive: metrics.surgeWindowActive,
    isInitialized,
  };
}

/**
 * Hook for Auris/Symbol analytics
 */
export function useAurisMetrics() {
  const { metrics, busSnapshot, isInitialized } = useEcosystemData();
  
  // Get dominant node from bus snapshot
  const masterEq = busSnapshot?.states?.MasterEquation;
  const dominantNode = masterEq?.data?.dominantNode || 'Tiger';
  
  return {
    compilationRate: metrics.coherence * 0.9 + 0.1,
    symbolProcessing: 0.85 + metrics.coherence * 0.1,
    quantumEntanglement: metrics.hiveMindCoherence,
    dataIntegrity: 0.95 + metrics.coherence * 0.04,
    dominantNode,
    isInitialized,
  };
}
