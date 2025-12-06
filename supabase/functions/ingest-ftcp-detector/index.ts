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
      curvature,
      curvature_direction,
      is_fibonacci_level,
      nearest_fib_ratio,
      divergence_from_fib,
      trend_strength,
      phase,
      metadata
    } = body;

    console.log(`[ingest-ftcp-detector] Ingesting state for temporal_id: ${temporal_id}`);

    const { data, error } = await supabase
      .from('ftcp_detector_states')
      .insert({
        temporal_id,
        curvature: curvature || 0,
        curvature_direction: curvature_direction || 'FLAT',
        is_fibonacci_level: is_fibonacci_level || false,
        nearest_fib_ratio: nearest_fib_ratio,
        divergence_from_fib: divergence_from_fib,
        trend_strength: trend_strength || 0,
        phase: phase || 'NEUTRAL',
        metadata: metadata || {}
      })
      .select()
      .single();

    if (error) {
      console.error('[ingest-ftcp-detector] Error:', error);
      throw error;
    }

    console.log(`[ingest-ftcp-detector] Successfully ingested state: ${data.id}`);

    return new Response(JSON.stringify({ success: true, data }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    console.error('[ingest-ftcp-detector] Error:', message);
    return new Response(JSON.stringify({ error: message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
