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
    console.log('[ingest-stargate-harmonizer] Received:', JSON.stringify(body));

    const { data, error } = await supabase
      .from('stargate_harmonizer_states')
      .insert({
        temporal_id: body.temporal_id || `harmonizer-${Date.now()}`,
        dominant_frequency: body.dominant_frequency || 528,
        coherence_boost: body.coherence_boost || 0,
        signal_amplification: body.signal_amplification || 1,
        trading_bias: body.trading_bias || 'NEUTRAL',
        confidence_modifier: body.confidence_modifier || 0,
        optimal_entry_window: body.optimal_entry_window || false,
        resonance_quality: body.resonance_quality || 0,
        harmonics: body.harmonics || [],
        metadata: body.metadata || {},
      })
      .select()
      .single();

    if (error) {
      console.error('[ingest-stargate-harmonizer] Error:', error);
      throw error;
    }

    console.log('[ingest-stargate-harmonizer] Inserted:', data?.id);
    return new Response(JSON.stringify({ success: true, id: data?.id }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    console.error('[ingest-stargate-harmonizer] Error:', message);
    return new Response(JSON.stringify({ error: message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
