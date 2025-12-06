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
    console.log('[ingest-planetary-modulation] Received:', JSON.stringify(body));

    const { data, error } = await supabase
      .from('planetary_modulation_states')
      .insert({
        temporal_id: body.temporal_id || `planetary-${Date.now()}`,
        harmonic_weight_modulation: body.harmonic_weight_modulation || {},
        color_palette_shift: body.color_palette_shift || 0,
        coherence_nudge: body.coherence_nudge || 0,
        phase_bias: body.phase_bias || {},
        planetary_states: body.planetary_states || [],
        metadata: body.metadata || {},
      })
      .select()
      .single();

    if (error) {
      console.error('[ingest-planetary-modulation] Error:', error);
      throw error;
    }

    console.log('[ingest-planetary-modulation] Inserted:', data?.id);
    return new Response(JSON.stringify({ success: true, id: data?.id }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    console.error('[ingest-planetary-modulation] Error:', message);
    return new Response(JSON.stringify({ error: message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
