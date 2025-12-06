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
      strength,
      confidence,
      coherence_boost,
      phase,
      frequency,
      metadata
    } = body;

    console.log(`[ingest-qgita-signal] Ingesting state for temporal_id: ${temporal_id}`);

    const { data, error } = await supabase
      .from('qgita_signal_states')
      .insert({
        temporal_id,
        signal_type: signal_type || 'HOLD',
        strength: strength || 0,
        confidence: confidence || 0,
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

    console.log(`[ingest-qgita-signal] Successfully ingested state: ${data.id}`);

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
