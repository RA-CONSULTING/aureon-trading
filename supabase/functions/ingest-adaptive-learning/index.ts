import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseKey);

    const body = await req.json();
    const {
      temporal_id,
      min_coherence,
      min_confidence,
      max_position_pct,
      kelly_multiplier,
      learning_rate,
      total_trades_learned,
      calibration_win_rate,
      calibration_profit_factor,
      band_performance,
      tier_performance,
      hourly_performance,
      symbol_adjustments,
      regime_adjustments,
      confidence_score,
      metadata
    } = body;

    console.log(`[ingest-adaptive-learning] Ingesting state for temporal_id: ${temporal_id}`);

    const { data, error } = await supabase
      .from('adaptive_learning_states')
      .insert({
        temporal_id,
        min_coherence: min_coherence || 0.45,
        min_confidence: min_confidence || 0.50,
        max_position_pct: max_position_pct || 5.0,
        kelly_multiplier: kelly_multiplier || 0.5,
        learning_rate: learning_rate || 0.01,
        total_trades_learned: total_trades_learned || 0,
        calibration_win_rate,
        calibration_profit_factor,
        band_performance: band_performance || {},
        tier_performance: tier_performance || {},
        hourly_performance: hourly_performance || {},
        symbol_adjustments: symbol_adjustments || {},
        regime_adjustments: regime_adjustments || {},
        confidence_score: confidence_score || 0,
        metadata: metadata || {}
      })
      .select()
      .single();

    if (error) {
      console.error('[ingest-adaptive-learning] Error:', error);
      throw error;
    }

    console.log(`[ingest-adaptive-learning] Successfully ingested state: ${data.id}`);

    return new Response(JSON.stringify({ success: true, data }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    console.error('[ingest-adaptive-learning] Error:', message);
    return new Response(JSON.stringify({ error: message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
