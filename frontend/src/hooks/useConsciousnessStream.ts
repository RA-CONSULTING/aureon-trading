/**
 * useConsciousnessStream - Polls consciousness_state.json for live Queen consciousness data
 * Same pattern as useHiveState - reads from public/ file written by the sentient loop
 */

import { useEffect } from 'react';
import { globalSystemsManager } from '@/core/globalSystemsManager';

interface ConsciousnessSnapshot {
  available: boolean;
  generated_at?: string;
  lambda_state?: {
    lambda?: number;
    psi?: number;
    gamma?: number;
    level?: string;
    observer?: number;
    echo?: number;
    step?: number;
  };
  understanding?: {
    market_direction?: string;
    confidence?: number;
    fear_level?: number;
    opportunity_count?: number;
    risk_level?: string;
    self_coherence?: number;
    dream_progress?: number;
    [key: string]: unknown;
  };
  self_model?: {
    name?: string;
    identity?: string;
    creator?: string;
    purpose?: string;
    core_message?: string;
    dream_target?: number;
    current_equity?: number;
    self_coherence_score?: number;
  };
  harmonic_field?: {
    lambda_real?: number;
    coherence_real?: number;
    reality_state?: string;
    branches?: number;
    lev_events?: number;
  };
  emotion?: {
    mood?: string;
    urgency?: number;
    excitement?: number;
    concern?: number;
  };
  observations?: number;
  thoughts_generated?: number;
  uptime_s?: number;
  thought_stream?: Array<{
    topic?: string;
    source?: string;
    timestamp?: number;
    text?: string;
  }>;
}

const toNum = (v: unknown, fallback = 0): number => {
  const n = Number(v);
  return Number.isFinite(n) ? n : fallback;
};

export function useConsciousnessStream(enabled: boolean = true, pollInterval: number = 3000) {
  useEffect(() => {
    if (!enabled) return;

    const fetchConsciousness = async () => {
      try {
        const response = await fetch('/consciousness_state.json', { cache: 'no-store' });
        if (!response.ok) return;
        const data: ConsciousnessSnapshot = await response.json();
        if (!data || !data.available) return;

        const ls = data.lambda_state || {};
        const u = data.understanding || {};
        const sm = data.self_model || {};
        const hf = data.harmonic_field || {};
        const em = data.emotion || {};
        const thoughts = Array.isArray(data.thought_stream) ? data.thought_stream : [];

        globalSystemsManager.setPartialState({
          consciousness: {
            available: true,
            // Lambda(t)
            psi: toNum(ls.psi),
            gamma: toNum(ls.gamma),
            lambdaT: toNum(ls.lambda),
            level: String(ls.level || 'DORMANT'),
            observerSignal: toNum(ls.observer),
            echoSignal: toNum(ls.echo),
            step: toNum(ls.step),
            // Understanding
            marketDirection: String(u.market_direction || 'unknown'),
            confidence: toNum(u.confidence),
            fearLevel: toNum(u.fear_level, 0.5),
            opportunityCount: toNum(u.opportunity_count),
            riskLevel: String(u.risk_level || 'unknown'),
            selfCoherence: toNum(u.self_coherence),
            dreamProgress: toNum(u.dream_progress),
            // Harmonic field
            lambdaReal: toNum(hf.lambda_real),
            coherenceReal: toNum(hf.coherence_real),
            realityState: String(hf.reality_state || 'DORMANT'),
            branches: toNum(hf.branches),
            levEvents: toNum(hf.lev_events),
            // Self model
            queenName: String(sm.name || 'Queen Sero'),
            queenIdentity: String(sm.identity || ''),
            queenCreator: String(sm.creator || 'Gary Leckey'),
            queenPurpose: String(sm.purpose || ''),
            coreMessage: String(sm.core_message || ''),
            dreamTarget: toNum(sm.dream_target, 1000000000),
            // Metacognition
            observations: toNum(data.observations),
            thoughtsGenerated: toNum(data.thoughts_generated),
            uptimeSeconds: toNum(data.uptime_s),
            // Emotion
            mood: String(em.mood || 'NEUTRAL'),
            urgency: toNum(em.urgency),
            excitement: toNum(em.excitement),
            concern: toNum(em.concern),
            // Thought stream
            thoughtStream: thoughts.slice(-20).map(t => ({
              topic: String(t.topic || ''),
              source: String(t.source || ''),
              timestamp: toNum(t.timestamp),
              text: String(t.text || ''),
            })),
          },
        });
      } catch {
        // Silently fail - consciousness data is optional
      }
    };

    fetchConsciousness();
    const interval = setInterval(fetchConsciousness, pollInterval);
    return () => clearInterval(interval);
  }, [enabled, pollInterval]);
}
