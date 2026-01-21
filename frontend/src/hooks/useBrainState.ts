import { useState, useEffect, useCallback } from "react";
import { supabase } from "@/integrations/supabase/client";

const LIVE_FEED_USER_ID = "69e5567f-7ad1-42af-860f-3709ef1f5935";

export interface LivePulse {
  pulse?: string;
  strength?: number;
  avg_change_24h?: number;
  btc_price?: number;
  fear_greed?: number;
}

export interface Dreams {
  scenarios_dreamed?: Array<{ scenario: string; decision: string }>;
  key_insights?: string[];
  prepared_responses?: Record<string, { action: string; reasoning: string }>;
}

export interface ExitTargets {
  take_profit_pct?: number;
  stop_loss_pct?: number;
  trailing_stop?: boolean;
}

export interface Reflection {
  blind_spots?: string[];
  self_critique?: string[];
  overconfidence_level?: number;
}

export interface WisdomConsensus {
  sentiment?: string;
  action?: string;
  confidence?: number;
  bullish_votes?: number;
  bearish_votes?: number;
  neutral_votes?: number;
  civilization_actions?: Record<string, string>;
}

export interface BrainState {
  id: string;
  timestamp: string;
  // Market
  fear_greed: number;
  fear_greed_class: string;
  btc_price: number;
  btc_dominance: number;
  btc_change_24h: number;
  // Live Pulse
  live_pulse: LivePulse;
  // Analysis
  manipulation_probability: number;
  red_flags: string[];
  green_flags: string[];
  // Council
  council_consensus: string;
  council_action: string;
  truth_score: number;
  spoof_score: number;
  council_arguments: string[];
  // Brain
  brain_directive: string | null;
  learning_directive: string;
  // Prediction
  prediction_direction: string;
  prediction_confidence: number;
  // Accuracy
  overall_accuracy: number;
  total_predictions: number;
  bullish_accuracy: number;
  bearish_accuracy: number;
  self_critique: string[];
  // Speculations
  speculations: string[];
  // Wisdom
  wisdom_consensus: WisdomConsensus;
  civilization_actions: Record<string, string>;
  // Quantum State
  quantum_coherence: number | null;
  planetary_gamma: number | null;
  cascade_multiplier: number | null;
  is_lighthouse: boolean;
  lambda_field: number | null;
  probability_edge: number | null;
  harmonic_signal: number | null;
  hnc_probability: number | null;
  // Dreams
  dreams: Dreams;
  // Sandbox Evolution
  sandbox_generation: number;
  sandbox_win_rate: number;
  should_trade: boolean | null;
  entry_filter_reason: string | null;
  exit_targets: ExitTargets;
  position_size_pct: number | null;
  evolved_generation: number;
  evolved_win_rate: number;
  // Piano/Diamond Harmony
  piano_lambda: number | null;
  piano_coherence: number | null;
  rainbow_state: string | null;
  diamond_coherence: number | null;
  diamond_phi_alignment: number | null;
  // Reflection
  reflection: Reflection;
}

const DEFAULT_BRAIN_STATE: BrainState = {
  id: "",
  timestamp: new Date().toISOString(),
  fear_greed: 50,
  fear_greed_class: "Neutral",
  btc_price: 0,
  btc_dominance: 0,
  btc_change_24h: 0,
  live_pulse: {},
  manipulation_probability: 0,
  red_flags: [],
  green_flags: [],
  council_consensus: "AWAITING_DATA",
  council_action: "HOLD",
  truth_score: 0.5,
  spoof_score: 0.5,
  council_arguments: [],
  brain_directive: null,
  learning_directive: "NEUTRAL",
  prediction_direction: "NEUTRAL",
  prediction_confidence: 0,
  overall_accuracy: 0,
  total_predictions: 0,
  bullish_accuracy: 0,
  bearish_accuracy: 0,
  self_critique: [],
  speculations: [],
  wisdom_consensus: {},
  civilization_actions: {},
  quantum_coherence: null,
  planetary_gamma: null,
  cascade_multiplier: null,
  is_lighthouse: false,
  lambda_field: null,
  probability_edge: null,
  harmonic_signal: null,
  hnc_probability: null,
  dreams: {},
  sandbox_generation: 0,
  sandbox_win_rate: 0,
  should_trade: null,
  entry_filter_reason: null,
  exit_targets: {},
  position_size_pct: null,
  evolved_generation: 0,
  evolved_win_rate: 0,
  piano_lambda: null,
  piano_coherence: null,
  rainbow_state: null,
  diamond_coherence: null,
  diamond_phi_alignment: null,
  reflection: {},
};

export function useBrainState(enabled: boolean = true, intervalMs: number = 10000) {
  const [brainState, setBrainState] = useState<BrainState>(DEFAULT_BRAIN_STATE);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchBrainState = useCallback(async () => {
    try {
      const [brainRes, sessionRes] = await Promise.all([
        supabase
          .from("brain_states")
          .select("*")
          .eq("user_id", LIVE_FEED_USER_ID)
          .order("timestamp", { ascending: false })
          .limit(1)
          .maybeSingle(),
        supabase
          .from("aureon_user_sessions")
          .select(
            "current_coherence,current_lambda,current_lighthouse_signal,dominant_node,prism_state,is_trading_active"
          )
          .eq("user_id", LIVE_FEED_USER_ID)
          .maybeSingle(),
      ]);

      const brainData = brainRes.data as any;
      const brainError = brainRes.error;
      const sessionData = sessionRes.data as any;

      if (brainError && brainError.code !== "PGRST116") {
        console.error("[useBrainState] Error fetching brain_states:", brainError);
      }

      const sessionOverrides: Partial<BrainState> = sessionData
        ? {
            quantum_coherence: sessionData.current_coherence ?? null,
            lambda_field: sessionData.current_lambda ?? null,
            is_lighthouse: (sessionData.current_lighthouse_signal ?? 0) > 1.0,
            rainbow_state: sessionData.prism_state ?? null,
            piano_coherence: sessionData.current_coherence ?? null,
            council_consensus:
              !brainData?.council_consensus && sessionData.dominant_node
                ? `${sessionData.dominant_node} DOMINANT`
                : undefined,
            council_action:
              !brainData?.council_action && sessionData.is_trading_active != null
                ? sessionData.is_trading_active
                  ? "ACTIVE"
                  : "HOLD"
                : undefined,
          }
        : {};

      if (brainData) {
        setBrainState({
          ...DEFAULT_BRAIN_STATE,
          ...brainData,
          ...sessionOverrides,
          live_pulse: (brainData.live_pulse as LivePulse) || {},
          wisdom_consensus: (brainData.wisdom_consensus as WisdomConsensus) || {},
          civilization_actions: (brainData.civilization_actions as Record<string, string>) || {},
          dreams: (brainData.dreams as Dreams) || {},
          exit_targets: (brainData.exit_targets as ExitTargets) || {},
          reflection: (brainData.reflection as Reflection) || {},
        });
        setLastUpdated(new Date());
      } else if (sessionData) {
        setBrainState({
          ...DEFAULT_BRAIN_STATE,
          ...sessionOverrides,
        });
        setLastUpdated(new Date());
      }
    } catch (err) {
      console.error("[useBrainState] Fetch error:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!enabled) return;
    fetchBrainState();
    const interval = setInterval(fetchBrainState, intervalMs);
    return () => clearInterval(interval);
  }, [enabled, intervalMs, fetchBrainState]);

  useEffect(() => {
    if (!enabled) return;

    const channel = supabase
      .channel("brain-states-realtime")
      .on(
        "postgres_changes",
        {
          event: "INSERT",
          schema: "public",
          table: "brain_states",
          filter: `user_id=eq.${LIVE_FEED_USER_ID}`,
        },
        (payload) => {
          console.log("[useBrainState] Realtime update received");
          const newState = payload.new as any;
          setBrainState({
            ...DEFAULT_BRAIN_STATE,
            ...newState,
            live_pulse: (newState.live_pulse as LivePulse) || {},
            wisdom_consensus: (newState.wisdom_consensus as WisdomConsensus) || {},
            civilization_actions: (newState.civilization_actions as Record<string, string>) || {},
            dreams: (newState.dreams as Dreams) || {},
            exit_targets: (newState.exit_targets as ExitTargets) || {},
            reflection: (newState.reflection as Reflection) || {},
          });
          setLastUpdated(new Date());
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [enabled]);

  return { brainState, loading, lastUpdated, refresh: fetchBrainState };
}
