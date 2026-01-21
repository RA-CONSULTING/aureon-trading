/**
 * useTerminalMetrics - Computes derived terminal metrics
 * Handles runtime calculation, drawdown tracking, and frequency analysis
 */

import { useState, useEffect, useCallback } from 'react';
import { useGlobalState } from './useGlobalState';
import { globalSystemsManager } from '@/core/globalSystemsManager';

export interface TerminalMetrics {
  runtimeMinutes: number;
  runtimeFormatted: string;
  sessionPnl: number;
  sessionPnlPercent: number;
}

export function useTerminalMetrics(): TerminalMetrics {
  const state = useGlobalState();
  const [runtimeMinutes, setRuntimeMinutes] = useState(0);
  
  // Update runtime every second
  useEffect(() => {
    const interval = setInterval(() => {
      if (state.sessionStartTime > 0) {
        const elapsed = Date.now() - state.sessionStartTime;
        setRuntimeMinutes(elapsed / 60000);
      }
    }, 1000);
    
    return () => clearInterval(interval);
  }, [state.sessionStartTime]);
  
  // Format runtime as "X.X min" or "Xh Xm"
  const formatRuntime = (minutes: number): string => {
    if (minutes < 60) {
      return `${minutes.toFixed(1)} min`;
    }
    const hours = Math.floor(minutes / 60);
    const mins = Math.floor(minutes % 60);
    return `${hours}h ${mins}m`;
  };
  
  return {
    runtimeMinutes,
    runtimeFormatted: formatRuntime(runtimeMinutes),
    sessionPnl: state.cyclePnl,
    sessionPnlPercent: state.cyclePnlPercent,
  };
}

/**
 * Hook to track WebSocket message count
 */
export function useWsMessageTracker() {
  const [messageCount, setMessageCount] = useState(0);
  
  const incrementCount = useCallback(() => {
    setMessageCount(prev => prev + 1);
  }, []);
  
  return { messageCount, incrementCount };
}

/**
 * Calculate drawdown from peak equity
 */
export function calculateDrawdown(currentEquity: number, peakEquity: number): number {
  if (peakEquity <= 0) return 0;
  const drawdown = ((peakEquity - currentEquity) / peakEquity) * 100;
  return Math.max(0, drawdown);
}

/**
 * Calculate Gaia Lattice state from frequency
 */
export function calculateGaiaState(frequency: number): 'COHERENT' | 'DISTORTION' | 'NEUTRAL' {
  // 432Hz = natural harmony (COHERENT)
  // 440Hz = distortion
  // In between = neutral
  const deviation = Math.abs(frequency - 432);
  
  if (deviation <= 2) return 'COHERENT';
  if (frequency >= 438 && frequency <= 442) return 'DISTORTION';
  return 'NEUTRAL';
}

/**
 * Map momentum to HNC frequency
 * Uses Solfeggio frequencies as anchors
 */
export function calculateHncFrequency(momentum: number, volatility: number): number {
  // Base frequency from momentum
  // Positive momentum → higher frequencies (852Hz trending up)
  // Negative momentum → lower frequencies (396Hz fear/greed)
  // Neutral → 432Hz harmony
  
  const baseFreq = 432;
  const momentumFactor = momentum * 100; // Scale momentum
  
  // Solfeggio anchors: 174, 285, 396, 417, 432, 528, 639, 741, 852, 963
  const targetFreq = baseFreq + momentumFactor;
  
  // Snap to nearest Solfeggio if close
  const solfeggio = [174, 285, 396, 417, 432, 528, 639, 741, 852, 963];
  const nearest = solfeggio.reduce((prev, curr) => 
    Math.abs(curr - targetFreq) < Math.abs(prev - targetFreq) ? curr : prev
  );
  
  // If within 20Hz of a solfeggio, snap to it
  if (Math.abs(nearest - targetFreq) < 20) {
    return nearest;
  }
  
  return Math.round(targetFreq);
}

/**
 * Determine HNC market state from coherence and volatility
 */
export function calculateHncMarketState(
  coherence: number, 
  volatility: number,
  momentum: number
): 'CONSOLIDATION' | 'TRENDING' | 'VOLATILE' | 'BREAKOUT' {
  if (volatility > 5 && Math.abs(momentum) > 0.03) {
    return 'BREAKOUT';
  }
  if (volatility > 3) {
    return 'VOLATILE';
  }
  if (Math.abs(momentum) > 0.02) {
    return 'TRENDING';
  }
  return 'CONSOLIDATION';
}
