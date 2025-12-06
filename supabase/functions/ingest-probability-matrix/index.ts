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
      six_d_probability,
      hnc_probability,
      fused_probability,
      dynamic_weight,
      trading_action,
      confidence,
      wave_state,
      harmonic_lock,
      metadata
    } = body;

    console.log(`[ingest-probability-matrix] Ingesting state for temporal_id: ${temporal_id}`);

    const { data, error } = await supabase
      .from('probability_matrix_states')
      .insert({
        temporal_id,
        six_d_probability: six_d_probability || 0,
        hnc_probability: hnc_probability || 0,
        fused_probability: fused_probability || 0,
        dynamic_weight: dynamic_weight || 0.5,
        trading_action: trading_action || 'HOLD',
        confidence: confidence || 0,
        wave_state: wave_state || 'FORMING',
        harmonic_lock: harmonic_lock || false,
        metadata: metadata || {}
      })
      .select()
      .single();

    if (error) {
      console.error('[ingest-probability-matrix] Error:', error);
      throw error;
    }

    console.log(`[ingest-probability-matrix] Successfully ingested state: ${data.id}`);

    return new Response(JSON.stringify({ success: true, data }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    console.error('[ingest-probability-matrix] Error:', message);
    return new Response(JSON.stringify({ error: message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
