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
    console.log('[ingest-omega-equation] Received:', JSON.stringify(body));

    const { data, error } = await supabase
      .from('omega_equation_states')
      .insert({
        temporal_id: body.temporal_id || `omega-${Date.now()}`,
        omega: body.omega || 0,
        psi: body.psi || 0,
        love: body.love || 0,
        observer: body.observer || 0,
        lambda: body.lambda || 0,
        substrate: body.substrate || 0,
        echo: body.echo || 0,
        coherence: body.coherence || 0,
        theta: body.theta || 0,
        unity: body.unity || 0,
        dominant_node: body.dominant_node || 'Tiger',
        spiral_phase: body.spiral_phase || 0,
        fibonacci_level: body.fibonacci_level || 0,
        celestial_boost: body.celestial_boost || 0,
        schumann_boost: body.schumann_boost || 0,
        metadata: body.metadata || {},
      })
      .select()
      .single();

    if (error) {
      console.error('[ingest-omega-equation] Error:', error);
      throw error;
    }

    console.log('[ingest-omega-equation] Inserted:', data?.id);
    return new Response(JSON.stringify({ success: true, id: data?.id }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    console.error('[ingest-omega-equation] Error:', message);
    return new Response(JSON.stringify({ error: message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
