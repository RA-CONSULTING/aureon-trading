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
    console.log('[ingest-eckoushic-cascade] Received:', JSON.stringify(body));

    const { data, error } = await supabase
      .from('eckoushic_cascade_states')
      .insert({
        temporal_id: body.temporal_id || `eckoushic-${Date.now()}`,
        eckoushic: body.eckoushic || 0,
        akashic: body.akashic || 0,
        harmonic_nexus: body.harmonic_nexus || 0,
        heart_wave: body.heart_wave || 0,
        frequency: body.frequency || 528,
        cascade_level: body.cascade_level || 1,
        metadata: body.metadata || {},
      })
      .select()
      .single();

    if (error) {
      console.error('[ingest-eckoushic-cascade] Error:', error);
      throw error;
    }

    console.log('[ingest-eckoushic-cascade] Inserted:', data?.id);
    return new Response(JSON.stringify({ success: true, id: data?.id }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    console.error('[ingest-eckoushic-cascade] Error:', message);
    return new Response(JSON.stringify({ error: message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
