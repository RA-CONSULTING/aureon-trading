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
      systems_online,
      total_systems,
      hive_mind_coherence,
      bus_consensus,
      bus_confidence,
      json_enhancements_loaded,
      system_states,
      metadata
    } = body;

    console.log(`[ingest-ecosystem-snapshot] Ingesting snapshot for temporal_id: ${temporal_id}`);

    const { data, error } = await supabase
      .from('ecosystem_snapshots')
      .insert({
        temporal_id,
        systems_online: systems_online || 0,
        total_systems: total_systems || 25,
        hive_mind_coherence: hive_mind_coherence || 0,
        bus_consensus: bus_consensus || 'HOLD',
        bus_confidence: bus_confidence || 0,
        json_enhancements_loaded: json_enhancements_loaded || false,
        system_states: system_states || {},
        metadata: metadata || {}
      })
      .select()
      .single();

    if (error) {
      console.error('[ingest-ecosystem-snapshot] Error:', error);
      throw error;
    }

    console.log(`[ingest-ecosystem-snapshot] Successfully ingested snapshot: ${data.id}`);

    return new Response(JSON.stringify({ success: true, data }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    console.error('[ingest-ecosystem-snapshot] Error:', message);
    return new Response(JSON.stringify({ error: message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
