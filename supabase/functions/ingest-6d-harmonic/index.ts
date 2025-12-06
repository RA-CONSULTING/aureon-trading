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
      d1_price,
      d2_volume,
      d3_time,
      d4_correlation,
      d5_momentum,
      d6_frequency,
      dimensional_coherence,
      phase_alignment,
      energy_density,
      resonance_score,
      wave_state,
      market_phase,
      harmonic_lock,
      probability_field,
      metadata
    } = body;

    console.log(`[ingest-6d-harmonic] Ingesting state for temporal_id: ${temporal_id}`);

    const { data, error } = await supabase
      .from('harmonic_6d_states')
      .insert({
        temporal_id,
        d1_price: d1_price || {},
        d2_volume: d2_volume || {},
        d3_time: d3_time || {},
        d4_correlation: d4_correlation || {},
        d5_momentum: d5_momentum || {},
        d6_frequency: d6_frequency || {},
        dimensional_coherence: dimensional_coherence || 0,
        phase_alignment: phase_alignment || 0,
        energy_density: energy_density || 0,
        resonance_score: resonance_score || 0,
        wave_state: wave_state || 'FORMING',
        market_phase: market_phase || 'ACCUMULATION',
        harmonic_lock: harmonic_lock || false,
        probability_field: probability_field || 0,
        metadata: metadata || {}
      })
      .select()
      .single();

    if (error) {
      console.error('[ingest-6d-harmonic] Error:', error);
      throw error;
    }

    console.log(`[ingest-6d-harmonic] Successfully ingested state: ${data.id}`);

    return new Response(JSON.stringify({ success: true, data }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    console.error('[ingest-6d-harmonic] Error:', message);
    return new Response(JSON.stringify({ error: message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
