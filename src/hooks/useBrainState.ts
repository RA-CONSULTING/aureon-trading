import { useState, useEffect, useCallback } from "react";
import { supabase } from "@/integrations/supabase/client";

// Public live feed user ID
const LIVE_FEED_USER_ID = "69e5567f-7ad1-42af-860f-3709ef1f5935";

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
  // Evolution
  evolved_generation: number;
  evolved_win_rate: number;
}

const DEFAULT_BRAIN_STATE: BrainState = {
  id: "",
  timestamp: new Date().toISOString(),
  fear_greed: 50,
  fear_greed_class: "Neutral",
  btc_price: 0,
  btc_dominance: 0,
  btc_change_24h: 0,
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
  evolved_generation: 0,
  evolved_win_rate: 0,
};

export function useBrainState(enabled: boolean = true, intervalMs: number = 10000) {
  const [brainState, setBrainState] = useState<BrainState>(DEFAULT_BRAIN_STATE);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchBrainState = useCallback(async () => {
    try {
      const { data, error } = await supabase
        .from("brain_states")
        .select("*")
        .eq("user_id", LIVE_FEED_USER_ID)
        .order("timestamp", { ascending: false })
        .limit(1)
        .single();

      if (error) {
        if (error.code !== "PGRST116") { // Not found is ok
          console.error("[useBrainState] Error fetching:", error);
        }
        return;
      }

      if (data) {
        setBrainState({
          ...data,
          wisdom_consensus: (data.wisdom_consensus as WisdomConsensus) || {},
        });
        setLastUpdated(new Date());
      }
    } catch (err) {
      console.error("[useBrainState] Fetch error:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial fetch and polling
  useEffect(() => {
    if (!enabled) return;

    fetchBrainState();

    const interval = setInterval(fetchBrainState, intervalMs);
    return () => clearInterval(interval);
  }, [enabled, intervalMs, fetchBrainState]);

  // Realtime subscription
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
          console.log("[useBrainState] Realtime update:", payload.new);
          const newState = payload.new as any;
          setBrainState({
            ...newState,
            wisdom_consensus: (newState.wisdom_consensus as WisdomConsensus) || {},
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
