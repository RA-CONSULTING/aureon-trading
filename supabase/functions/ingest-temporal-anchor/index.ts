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
      is_valid,
      drift_detected,
      drift_amount_ms,
      registered_systems,
      verified_systems,
      anchor_strength,
      metadata
    } = body;

    console.log(`[ingest-temporal-anchor] Ingesting state for temporal_id: ${temporal_id}`);

    const { data, error } = await supabase
      .from('temporal_anchor_states')
      .insert({
        temporal_id,
        is_valid: is_valid !== undefined ? is_valid : true,
        drift_detected: drift_detected || false,
        drift_amount_ms: drift_amount_ms || 0,
        registered_systems: registered_systems || 0,
        verified_systems: verified_systems || 0,
        anchor_strength: anchor_strength || 1,
        metadata: metadata || {}
      })
      .select()
      .single();

    if (error) {
      console.error('[ingest-temporal-anchor] Error:', error);
      throw error;
    }

    console.log(`[ingest-temporal-anchor] Successfully ingested state: ${data.id}`);

    return new Response(JSON.stringify({ success: true, data }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    console.error('[ingest-temporal-anchor] Error:', message);
    return new Response(JSON.stringify({ error: message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
