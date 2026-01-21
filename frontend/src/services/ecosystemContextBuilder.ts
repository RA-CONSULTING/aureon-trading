/**
 * Ecosystem Context Builder
 * 
 * Builds a rich context object from the current ecosystem state
 * for injection into AI prompts, enabling AUREON to perceive
 * the quantum field state in real-time.
 */

import { EcosystemMetrics } from '@/hooks/useEcosystemData';
import { BusSnapshot } from '@/core/unifiedBus';

export interface EcosystemContext {
  coherence: number;
  lambda: number;
  lighthouseSignal: number;
  dominantNode: string;
  prismLevel: number;
  prismState: string;
  prismFrequency: number;
  rainbowBridgePhase: string;
  harmonicLock: boolean;
  waveState: string;
  busConsensus: string;
  busConfidence: number;
  hiveMindCoherence: number;
  qgitaSignal: string;
  qgitaTier: number;
  schumannFrequency: number;
  tradingMode: string;
  recentTrades: number;
  totalPnL: number;
}

/**
 * Build ecosystem context from metrics for AI consumption
 */
export function buildEcosystemContext(
  metrics: EcosystemMetrics | null,
  busSnapshot?: BusSnapshot | null,
  tradingStats?: { recentTrades: number; totalPnL: number; tradingMode: string } | null
): EcosystemContext {
  // Default context when no data available
  const defaultContext: EcosystemContext = {
    coherence: 0,
    lambda: 0,
    lighthouseSignal: 0,
    dominantNode: 'Unknown',
    prismLevel: 0,
    prismState: 'OFFLINE',
    prismFrequency: 0,
    rainbowBridgePhase: 'UNKNOWN',
    harmonicLock: false,
    waveState: 'INACTIVE',
    busConsensus: 'NEUTRAL',
    busConfidence: 0,
    hiveMindCoherence: 0,
    qgitaSignal: 'HOLD',
    qgitaTier: 0,
    schumannFrequency: 7.83,
    tradingMode: 'paper',
    recentTrades: 0,
    totalPnL: 0,
  };

  if (!metrics) {
    return defaultContext;
  }

  return {
    // Core field metrics
    coherence: metrics.coherence ?? 0,
    lambda: metrics.lambda ?? 0,
    lighthouseSignal: metrics.consensusConfidence ?? 0,
    dominantNode: metrics.dominantQuadrant ?? 'Unknown',
    
    // Prism state
    prismLevel: metrics.prismLevel ?? 0,
    prismState: metrics.prismState ?? 'OFFLINE',
    prismFrequency: metrics.emotionalFrequency ?? 0,
    
    // Rainbow Bridge
    rainbowBridgePhase: metrics.phase ?? 'UNKNOWN',
    
    // 6D Harmonic
    harmonicLock: metrics.harmonicLock ?? false,
    waveState: metrics.waveState ?? 'INACTIVE',
    
    // Consensus from bus
    busConsensus: busSnapshot?.consensusSignal ?? metrics.consensusSignal ?? 'NEUTRAL',
    busConfidence: busSnapshot?.consensusConfidence ?? metrics.consensusConfidence ?? 0,
    hiveMindCoherence: metrics.hiveMindCoherence ?? 0,
    
    // QGITA signal
    qgitaSignal: metrics.qgitaSignalType ?? 'HOLD',
    qgitaTier: metrics.qgitaTier ?? 0,
    
    // Earth integration - use emotionalFrequency as proxy for schumann
    schumannFrequency: metrics.frequency ?? 7.83,
    
    // Trading stats
    tradingMode: tradingStats?.tradingMode ?? 'paper',
    recentTrades: tradingStats?.recentTrades ?? 0,
    totalPnL: tradingStats?.totalPnL ?? 0,
  };
}

/**
 * Format context as a human-readable summary
 */
export function formatContextSummary(context: EcosystemContext): string {
  const coherenceStatus = context.coherence > 0.9 ? 'OPTIMAL' :
                          context.coherence > 0.7 ? 'GOOD' :
                          context.coherence > 0.5 ? 'MODERATE' : 'LOW';
  
  const prismLock = Math.abs(context.prismFrequency - 528) < 10 ? '528 Hz LOCKED' : 'Converging';
  
  return `
Γ=${context.coherence.toFixed(3)} (${coherenceStatus}) | Λ=${context.lambda.toFixed(3)} | L=${context.lighthouseSignal.toFixed(3)}
Prism L${context.prismLevel} ${context.prismState} @ ${context.prismFrequency.toFixed(1)}Hz (${prismLock})
Rainbow: ${context.rainbowBridgePhase} | 6D: ${context.waveState} ${context.harmonicLock ? '🔒' : ''}
Consensus: ${context.busConsensus} @ ${(context.busConfidence * 100).toFixed(0)}% | Hive: ${(context.hiveMindCoherence * 100).toFixed(0)}%
QGITA: ${context.qgitaSignal} T${context.qgitaTier} | Node: ${context.dominantNode}
  `.trim();
}

/**
 * Check if ecosystem data is stale or missing
 */
export function isEcosystemDataValid(context: EcosystemContext): boolean {
  // Check if we have meaningful data (not all zeros)
  return context.coherence > 0 || context.lambda !== 0 || context.prismLevel > 0;
}
