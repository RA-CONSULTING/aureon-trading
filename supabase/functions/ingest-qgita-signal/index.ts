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
      signal_type,
      tier,
      strength,
      confidence,
      curvature,
      curvature_direction,
      ftcp_detected,
      golden_ratio_score,
      lighthouse_l,
      is_lhe,
      lighthouse_threshold,
      linear_coherence,
      nonlinear_coherence,
      cross_scale_coherence,
      anomaly_pointer,
      reasoning,
      coherence_boost,
      phase,
      frequency,
      metadata
    } = body;

    // Log with QGITA-style formatting
    const tierEmoji = tier === 1 ? '🥇' : tier === 2 ? '🥈' : '🥉';
    const signalEmoji = signal_type === 'BUY' ? '🟢' : signal_type === 'SELL' ? '🔴' : '⚪';
    console.log(
      `[ingest-qgita-signal] ${signalEmoji} ${signal_type} ${tierEmoji}T${tier} ` +
      `Conf:${(confidence || 0).toFixed(1)}% LHE:${is_lhe} FTCP:${ftcp_detected} ` +
      `temporal_id: ${temporal_id}`
    );

    const { data, error } = await supabase
      .from('qgita_signal_states')
      .insert({
        temporal_id,
        signal_type: signal_type || 'HOLD',
        tier: tier || 3,
        strength: strength || 0,
        confidence: confidence || 0,
        curvature: curvature || 0,
        curvature_direction: curvature_direction || 'NEUTRAL',
        ftcp_detected: ftcp_detected || false,
        golden_ratio_score: golden_ratio_score || 0,
        lighthouse_l: lighthouse_l || 0,
        is_lhe: is_lhe || false,
        lighthouse_threshold: lighthouse_threshold || 0,
        linear_coherence: linear_coherence || 0,
        nonlinear_coherence: nonlinear_coherence || 0,
        cross_scale_coherence: cross_scale_coherence || 0,
        anomaly_pointer: anomaly_pointer || 0,
        reasoning: reasoning || '',
        coherence_boost: coherence_boost || 0,
        phase: phase || 'NEUTRAL',
        frequency: frequency || 528,
        metadata: metadata || {}
      })
      .select()
      .single();

    if (error) {
      console.error('[ingest-qgita-signal] Error:', error);
      throw error;
    }

    console.log(`[ingest-qgita-signal] Successfully ingested: ${data.id}`);

    return new Response(JSON.stringify({ success: true, data }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    console.error('[ingest-qgita-signal] Error:', message);
    return new Response(JSON.stringify({ error: message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
