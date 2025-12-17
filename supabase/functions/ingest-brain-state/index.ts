import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabase = createClient(
      Deno.env.get("SUPABASE_URL") ?? "",
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? ""
    );

    const payload = await req.json();
    console.log("[ingest-brain-state] Received payload:", JSON.stringify(payload).slice(0, 500));

    const {
      user_id,
      timestamp,
      // Market Data
      fear_greed,
      fear_greed_class,
      btc_price,
      btc_dominance,
      btc_change_24h,
      // Skeptical Analysis
      manipulation_probability,
      red_flags,
      green_flags,
      // Truth Council
      council_consensus,
      council_action,
      truth_score,
      spoof_score,
      council_arguments,
      // Brain Synthesis
      brain_directive,
      learning_directive,
      // Prediction
      prediction_direction,
      prediction_confidence,
      // Accuracy (Self-Learning)
      overall_accuracy,
      total_predictions,
      bullish_accuracy,
      bearish_accuracy,
      self_critique,
      // Speculations
      speculations,
      // Wisdom Consensus
      wisdom_consensus,
      // Sandbox Evolution
      evolved_generation,
      evolved_win_rate,
      // Full state
      full_state,
    } = payload;

    if (!user_id) {
      throw new Error("user_id is required");
    }

    // Insert brain state
    const { data, error } = await supabase
      .from("brain_states")
      .insert({
        user_id,
        timestamp: timestamp || new Date().toISOString(),
        fear_greed: fear_greed ?? 50,
        fear_greed_class: fear_greed_class ?? "Neutral",
        btc_price: btc_price ?? 0,
        btc_dominance: btc_dominance ?? 0,
        btc_change_24h: btc_change_24h ?? 0,
        manipulation_probability: manipulation_probability ?? 0,
        red_flags: red_flags ?? [],
        green_flags: green_flags ?? [],
        council_consensus: council_consensus ?? "UNKNOWN",
        council_action: council_action ?? "HOLD",
        truth_score: truth_score ?? 0.5,
        spoof_score: spoof_score ?? 0.5,
        council_arguments: council_arguments ?? [],
        brain_directive: brain_directive ?? null,
        learning_directive: learning_directive ?? "NEUTRAL",
        prediction_direction: prediction_direction ?? "NEUTRAL",
        prediction_confidence: prediction_confidence ?? 0,
        overall_accuracy: overall_accuracy ?? 0,
        total_predictions: total_predictions ?? 0,
        bullish_accuracy: bullish_accuracy ?? 0,
        bearish_accuracy: bearish_accuracy ?? 0,
        self_critique: self_critique ?? [],
        speculations: speculations ?? [],
        wisdom_consensus: wisdom_consensus ?? {},
        evolved_generation: evolved_generation ?? 0,
        evolved_win_rate: evolved_win_rate ?? 0,
        full_state: full_state ?? payload,
      })
      .select()
      .single();

    if (error) {
      console.error("[ingest-brain-state] DB error:", error);
      throw error;
    }

    console.log("[ingest-brain-state] Successfully inserted brain state:", data.id);

    return new Response(
      JSON.stringify({ success: true, id: data.id }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : "Unknown error";
    console.error("[ingest-brain-state] Error:", errorMessage);
    return new Response(
      JSON.stringify({ error: errorMessage }),
      { 
        status: 500, 
        headers: { ...corsHeaders, "Content-Type": "application/json" } 
      }
    );
  }
});
