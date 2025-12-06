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
      is_lighthouse_detected,
      schumann_power,
      anchor_power,
      love_power,
      unity_power,
      distortion_power,
      imperial_yield,
      harmonic_fidelity,
      bridge_status,
      metadata
    } = body;

    console.log(`[ingest-hnc-detection] Ingesting state for temporal_id: ${temporal_id}`);

    const { data, error } = await supabase
      .from('hnc_detection_states')
      .insert({
        temporal_id,
        is_lighthouse_detected: is_lighthouse_detected || false,
        schumann_power: schumann_power || 0,
        anchor_power: anchor_power || 0,
        love_power: love_power || 0,
        unity_power: unity_power || 0,
        distortion_power: distortion_power || 0,
        imperial_yield: imperial_yield || 0,
        harmonic_fidelity: harmonic_fidelity || 0,
        bridge_status: bridge_status || 'CLOSED',
        metadata: metadata || {}
      })
      .select()
      .single();

    if (error) {
      console.error('[ingest-hnc-detection] Error:', error);
      throw error;
    }

    console.log(`[ingest-hnc-detection] Successfully ingested state: ${data.id}`);

    return new Response(JSON.stringify({ success: true, data }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    console.error('[ingest-hnc-detection] Error:', message);
    return new Response(JSON.stringify({ error: message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
