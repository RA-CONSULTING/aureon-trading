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
      final_action,
      position_size,
      confidence,
      ensemble_score,
      sentiment_score,
      qgita_boost,
      harmonic_6d_score,
      wave_state,
      harmonic_lock,
      metadata
    } = body;

    console.log(`[ingest-decision-fusion] Ingesting state for temporal_id: ${temporal_id}`);

    const { data, error } = await supabase
      .from('decision_fusion_states')
      .insert({
        temporal_id,
        final_action: final_action || 'HOLD',
        position_size: position_size || 0,
        confidence: confidence || 0,
        ensemble_score: ensemble_score || 0,
        sentiment_score: sentiment_score || 0,
        qgita_boost: qgita_boost || 0,
        harmonic_6d_score: harmonic_6d_score || 0,
        wave_state: wave_state || 'FORMING',
        harmonic_lock: harmonic_lock || false,
        metadata: metadata || {}
      })
      .select()
      .single();

    if (error) {
      console.error('[ingest-decision-fusion] Error:', error);
      throw error;
    }

    console.log(`[ingest-decision-fusion] Successfully ingested state: ${data.id}`);

    return new Response(JSON.stringify({ success: true, data }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    console.error('[ingest-decision-fusion] Error:', message);
    return new Response(JSON.stringify({ error: message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
