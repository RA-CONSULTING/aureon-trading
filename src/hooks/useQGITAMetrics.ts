/**
 * useQGITAMetrics Hook
 * Specialized hook for QGITA signal analytics with comprehensive logging
 */

import { useState, useEffect, useCallback } from 'react';
import { qgitaSignalGenerator, QGITASignal } from '../core/qgitaSignalGenerator';
import { fullEcosystemConnector } from '../core/fullEcosystemConnector';
import { unifiedBus, SignalType } from '../core/unifiedBus';

export interface QGITAMetrics {
  // Signal data
  signalType: 'BUY' | 'SELL' | 'HOLD';
  tier: 1 | 2 | 3;
  confidence: number;
  
  // Curvature
  curvature: number;
  curvatureDirection: 'UPWARD' | 'DOWNWARD' | 'NEUTRAL';
  
  // FTCP Detection
  ftcpDetected: boolean;
  goldenRatioScore: number;
  
  // Lighthouse
  lighthouseL: number;
  isLHE: boolean;
  lighthouseThreshold: number;
  
  // Coherence
  linearCoherence: number;
  nonlinearCoherence: number;
  crossScaleCoherence: number;
  
  // Anomaly
  anomalyPointer: number;
  
  // Status
  reasoning: string;
  lastUpdate: number;
  historyLength: number;
}

const DEFAULT_QGITA_METRICS: QGITAMetrics = {
  signalType: 'HOLD',
  tier: 3,
  confidence: 0,
  curvature: 0,
  curvatureDirection: 'NEUTRAL',
  ftcpDetected: false,
  goldenRatioScore: 0,
  lighthouseL: 0,
  isLHE: false,
  lighthouseThreshold: 0,
  linearCoherence: 0,
  nonlinearCoherence: 0,
  crossScaleCoherence: 0,
  anomalyPointer: 0,
  reasoning: 'Initializing...',
  lastUpdate: 0,
  historyLength: 0,
};

/**
 * Extract QGITAMetrics from a QGITASignal
 */
function extractMetrics(signal: QGITASignal | null): QGITAMetrics {
  if (!signal) return DEFAULT_QGITA_METRICS;
  
  return {
    signalType: signal.signalType,
    tier: signal.tier,
    confidence: signal.confidence,
    curvature: signal.curvature,
    curvatureDirection: signal.curvatureDirection,
    ftcpDetected: signal.ftcpDetected,
    goldenRatioScore: signal.goldenRatioScore,
    lighthouseL: signal.lighthouse.L,
    isLHE: signal.lighthouse.isLHE,
    lighthouseThreshold: signal.lighthouse.threshold,
    linearCoherence: signal.coherence.linearCoherence,
    nonlinearCoherence: signal.coherence.nonlinearCoherence,
    crossScaleCoherence: signal.coherence.crossScaleCoherence,
    anomalyPointer: signal.anomalyPointer,
    reasoning: signal.reasoning,
    lastUpdate: signal.timestamp,
    historyLength: 0, // Will be set from ecosystem state
  };
}

export function useQGITAMetrics() {
  const [metrics, setMetrics] = useState<QGITAMetrics>(DEFAULT_QGITA_METRICS);
  const [rawSignal, setRawSignal] = useState<QGITASignal | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    // Subscribe to ecosystem updates
    const unsubEcosystem = fullEcosystemConnector.subscribe((state) => {
      if (state.qgitaSignal) {
        setRawSignal(state.qgitaSignal);
        const newMetrics = extractMetrics(state.qgitaSignal);
        setMetrics(newMetrics);
        
        // Log QGITA signal for debugging
        logQGITASignal(state.qgitaSignal);
      }
    });

    // Subscribe to bus for QGITA state
    const unsubBus = unifiedBus.subscribe((snapshot) => {
      const qgitaState = snapshot.states?.QGITASignal;
      if (qgitaState?.data?.signal) {
        setRawSignal(qgitaState.data.signal);
        const newMetrics = extractMetrics(qgitaState.data.signal);
        setMetrics(newMetrics);
      }
    });

    setIsInitialized(true);

    return () => {
      unsubEcosystem();
      unsubBus();
    };
  }, []);

  const refresh = useCallback(() => {
    const state = fullEcosystemConnector.getState();
    if (state.qgitaSignal) {
      setRawSignal(state.qgitaSignal);
      setMetrics(extractMetrics(state.qgitaSignal));
    }
  }, []);

  return {
    metrics,
    rawSignal,
    isInitialized,
    refresh,
  };
}

/**
 * Log QGITA signal with structured formatting
 */
function logQGITASignal(signal: QGITASignal): void {
  const tierEmoji = signal.tier === 1 ? '🥇' : signal.tier === 2 ? '🥈' : '🥉';
  const signalEmoji = signal.signalType === 'BUY' ? '🟢' : signal.signalType === 'SELL' ? '🔴' : '⚪';
  const lheEmoji = signal.lighthouse.isLHE ? '🔥' : '❄️';
  const ftcpEmoji = signal.ftcpDetected ? '✅' : '❌';
  
  console.log(
    `[QGITA] ${signalEmoji} ${signal.signalType} | ` +
    `${tierEmoji} Tier ${signal.tier} | ` +
    `Conf: ${signal.confidence.toFixed(1)}% | ` +
    `${lheEmoji} LHE: ${signal.lighthouse.isLHE} (L=${signal.lighthouse.L.toFixed(3)}) | ` +
    `${ftcpEmoji} FTCP | ` +
    `Curv: ${signal.curvatureDirection} (${signal.curvature.toFixed(4)}) | ` +
    `φ: ${(signal.goldenRatioScore * 100).toFixed(1)}%`
  );
  
  // Log coherence breakdown
  console.log(
    `       Coherence: Lin=${(signal.coherence.linearCoherence * 100).toFixed(1)}% ` +
    `NonLin=${(signal.coherence.nonlinearCoherence * 100).toFixed(1)}% ` +
    `CrossScale=${(signal.coherence.crossScaleCoherence * 100).toFixed(1)}% | ` +
    `|Q|=${signal.anomalyPointer.toFixed(3)}`
  );
}

/**
 * Simplified hook for just the signal
 */
export function useQGITASignal() {
  const { metrics, isInitialized } = useQGITAMetrics();
  
  // Map HOLD to NEUTRAL for SignalType compatibility
  const busSignal: SignalType = metrics.signalType === 'HOLD' ? 'NEUTRAL' : metrics.signalType;
  
  return {
    signalType: busSignal,
    tier: metrics.tier,
    confidence: metrics.confidence,
    isLHE: metrics.isLHE,
    ftcpDetected: metrics.ftcpDetected,
    reasoning: metrics.reasoning,
    isInitialized,
  };
}

/**
 * Hook for position sizing based on QGITA tier
 */
export function useQGITAPositionSize(basePositionUsd: number = 100) {
  const { metrics, isInitialized } = useQGITAMetrics();
  
  const positionMultiplier = qgitaSignalGenerator.getPositionSizeMultiplier(metrics.tier);
  const recommendedPosition = basePositionUsd * positionMultiplier;
  
  return {
    tier: metrics.tier,
    multiplier: positionMultiplier,
    recommendedPositionUsd: recommendedPosition,
    signalType: metrics.signalType,
    isInitialized,
  };
}
