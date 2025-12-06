import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    );

    const body = await req.json();
    console.log('[ingest-akashic-attunement] Received:', JSON.stringify(body));

    const { data, error } = await supabase
      .from('akashic_attunement_states')
      .insert({
        temporal_id: body.temporal_id || `akashic-${Date.now()}`,
        final_frequency: body.final_frequency || 528,
        convergence_rate: body.convergence_rate || 0,
        stability_index: body.stability_index || 0,
        cycles_performed: body.cycles_performed || 0,
        attunement_quality: body.attunement_quality || 'MODERATE',
        metadata: body.metadata || {},
      })
      .select()
      .single();

    if (error) {
      console.error('[ingest-akashic-attunement] Error:', error);
      throw error;
    }

    console.log('[ingest-akashic-attunement] Inserted:', data?.id);
    return new Response(JSON.stringify({ success: true, id: data?.id }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    console.error('[ingest-akashic-attunement] Error:', message);
    return new Response(JSON.stringify({ error: message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
