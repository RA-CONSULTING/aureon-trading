/**
 * AUTONOMY HUB BRIDGE
 * ═══════════════════════════════════════════════════════════════
 *
 * Bridges the Python AutonomyHub (The Big Wheel) into the TypeScript frontend.
 *
 * This closes the gap between:
 * - Python: data capture, prediction engines, feedback loop (aureon_autonomy_hub.py)
 * - TypeScript: decision fusion, execution engine, position manager
 *
 * The bridge:
 * 1. Reads the hub's latest decision from a shared state file
 * 2. Converts it into an AutonomyHubSignal for DecisionFusion
 * 3. Reads prediction accuracy stats from UnifiedBus and feeds back to hub
 *
 * This is the connective tissue that makes Python and TypeScript
 * two halves of the same brain instead of two separate islands.
 */

import { unifiedBus } from './unifiedBus';
import type { AutonomyHubSignal } from './decisionFusion';

// Shared state file written by Python aureon_autonomy_hub.py
const HUB_STATE_FILE = 'autonomy_hub_state.json';

interface HubStateFile {
  timestamp: number;
  cycle: number;
  symbol: string;
  action: string;
  confidence: number;
  strength: number;
  rollingWinRate: number;
  numPredictors: number;
  agreementRatio: number;
  reasons: string[];
}

/**
 * Reads the latest autonomy hub decision from shared state.
 * Returns null if state is stale (>60s old) or unavailable.
 */
export function getLatestHubSignal(): AutonomyHubSignal | null {
  try {
    // In browser context, this would come from an API endpoint or WebSocket
    // In Node.js/server context, read from file
    if (typeof globalThis !== 'undefined' && (globalThis as any).__autonomyHubState) {
      const state = (globalThis as any).__autonomyHubState as HubStateFile;
      const age = (Date.now() / 1000) - state.timestamp;

      if (age > 60) return null; // Stale

      return {
        direction: state.action === 'BUY' ? 'BULLISH' :
                   state.action === 'SELL' ? 'BEARISH' : 'NEUTRAL',
        confidence: state.confidence,
        strength: state.strength,
        rollingWinRate: state.rollingWinRate,
        numPredictors: state.numPredictors,
        agreementRatio: state.agreementRatio,
      };
    }
  } catch {
    // Silent fail - hub not available
  }
  return null;
}

/**
 * Updates the global hub state (called by server-side bridge or API handler).
 */
export function updateHubState(state: HubStateFile): void {
  if (typeof globalThis !== 'undefined') {
    (globalThis as any).__autonomyHubState = state;
  }
}

/**
 * Subscribe to UnifiedBus prediction accuracy stats and prepare
 * feedback data for the Python hub's feedback loop.
 */
export function initFeedbackBridge(): void {
  unifiedBus.subscribe((state) => {
    if (state.systemName === 'PredictionAccuracy' && state.data) {
      // Store accuracy data for Python hub to read
      if (typeof globalThis !== 'undefined') {
        (globalThis as any).__predictionAccuracyFeedback = {
          timestamp: Date.now(),
          accuracy1m: state.data.accuracy1m ?? 0,
          accuracy5m: state.data.accuracy5m ?? 0,
          accuracy15m: state.data.accuracy15m ?? 0,
          totalPredictions: state.data.totalPredictions ?? 0,
          validated: state.data.validated ?? 0,
          signal: state.signal,
          coherence: state.coherence,
        };
      }
    }
  });
}

/**
 * Get the latest prediction accuracy feedback for Python hub consumption.
 */
export function getAccuracyFeedback(): Record<string, unknown> | null {
  if (typeof globalThis !== 'undefined' && (globalThis as any).__predictionAccuracyFeedback) {
    return (globalThis as any).__predictionAccuracyFeedback;
  }
  return null;
}
