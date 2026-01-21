/**
 * Hook to wire decision explainer with accuracy tracking and database persistence
 */

import { useEffect, useState, useCallback } from 'react';
import { decisionExplainer, DecisionExplanation, DecisionMetrics } from '@/core/decisionExplainer';
import { decisionAccuracyTracker, AccuracyMetrics, TrackedDecision } from '@/core/decisionAccuracyTracker';
import { temporalProbabilityEcho, EchoMetrics } from '@/core/temporalProbabilityEcho';
import { supabase } from '@/integrations/supabase/client';

export interface DecisionVerificationState {
  latestDecision: DecisionExplanation | null;
  recentDecisions: DecisionExplanation[];
  accuracyMetrics: AccuracyMetrics | null;
  echoMetrics: EchoMetrics | null;
  trackedDecisions: TrackedDecision[];
  isTracking: boolean;
}

export function useDecisionVerification(userId: string | null) {
  const [state, setState] = useState<DecisionVerificationState>({
    latestDecision: null,
    recentDecisions: [],
    accuracyMetrics: null,
    echoMetrics: null,
    trackedDecisions: [],
    isTracking: false
  });

  // Make a decision and track it
  const makeDecision = useCallback(async (
    metrics: DecisionMetrics,
    currentPrice: number,
    symbol: string = 'BTCUSDT'
  ) => {
    // Generate explanation
    const explanation = decisionExplainer.explain(metrics, symbol);

    // Track for accuracy
    decisionAccuracyTracker.trackDecision(explanation, currentPrice);

    // Record to temporal echo
    temporalProbabilityEcho.recordSnapshot({
      sixDProbability: metrics.probabilityFused,
      hncProbability: metrics.harmonicLock ? 0.8 : 0.5,
      lighthouseProbability: metrics.lighthouseL,
      fusedProbability: metrics.probabilityFused,
      action: explanation.action,
      confidence: explanation.confidence,
      prismFrequency: metrics.prismFrequency,
      prismLevel: metrics.prismLevel,
      coherence: metrics.coherence,
      lambda: metrics.lambda
    });

    // Persist to database if user is authenticated
    if (userId) {
      try {
        const insertData = {
          user_id: userId,
          symbol,
          decision_action: explanation.action,
          confidence: explanation.confidence,
          coherence: metrics.coherence,
          lambda: metrics.lambda,
          lighthouse_l: metrics.lighthouseL,
          qgita_tier: metrics.qgitaTier,
          qgita_confidence: metrics.qgitaConfidence,
          prism_frequency: metrics.prismFrequency,
          prism_level: metrics.prismLevel,
          wave_state: metrics.waveState,
          harmonic_lock: metrics.harmonicLock,
          probability_fused: metrics.probabilityFused,
          sentiment_score: metrics.sentimentScore,
          geometric_alignment: metrics.geometricAlignment,
          price_at_decision: currentPrice,
          summary: explanation.summary,
          reasoning: explanation.reasoning as unknown as Record<string, unknown>,
          factors: explanation.factors as unknown as Record<string, unknown>
        };
        await supabase.from('decision_audit_log').insert(insertData as any);
      } catch (error) {
        console.error('Failed to persist decision:', error);
      }
    }

    return explanation;
  }, [userId]);

  // Update price for accuracy tracking
  const updatePrice = useCallback((price: number) => {
    decisionAccuracyTracker.updatePrice(price);
  }, []);

  // Subscribe to updates
  useEffect(() => {
    // Initial state
    setState(prev => ({
      ...prev,
      latestDecision: decisionExplainer.getLatest(),
      recentDecisions: decisionExplainer.getExplanations().slice(0, 20),
      accuracyMetrics: decisionAccuracyTracker.getMetrics(),
      echoMetrics: temporalProbabilityEcho.getMetrics(),
      trackedDecisions: decisionAccuracyTracker.getTrackedDecisions().slice(0, 10),
      isTracking: true
    }));

    const unsubExplainer = decisionExplainer.subscribe((explanation) => {
      setState(prev => ({
        ...prev,
        latestDecision: explanation,
        recentDecisions: decisionExplainer.getExplanations().slice(0, 20)
      }));
    });

    const unsubAccuracy = decisionAccuracyTracker.subscribe((metrics) => {
      setState(prev => ({
        ...prev,
        accuracyMetrics: metrics,
        trackedDecisions: decisionAccuracyTracker.getTrackedDecisions().slice(0, 10)
      }));
    });

    const unsubEcho = temporalProbabilityEcho.subscribe((echoState) => {
      setState(prev => ({
        ...prev,
        echoMetrics: echoState.metrics
      }));
    });

    return () => {
      unsubExplainer();
      unsubAccuracy();
      unsubEcho();
    };
  }, []);

  return {
    ...state,
    makeDecision,
    updatePrice
  };
}
