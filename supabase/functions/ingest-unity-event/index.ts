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
    console.log('[ingest-unity-event] Received:', JSON.stringify(body));

    const { data, error } = await supabase
      .from('unity_event_states')
      .insert({
        temporal_id: body.temporal_id || `unity-${Date.now()}`,
        theta: body.theta || 0,
        coherence: body.coherence || 0,
        omega: body.omega || 0,
        unity: body.unity || 0,
        duration_ms: body.duration_ms || 0,
        is_peak: body.is_peak || false,
        event_type: body.event_type || 'forming',
        metadata: body.metadata || {},
      })
      .select()
      .single();

    if (error) {
      console.error('[ingest-unity-event] Error:', error);
      throw error;
    }

    console.log('[ingest-unity-event] Inserted:', data?.id);
    return new Response(JSON.stringify({ success: true, id: data?.id }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    console.error('[ingest-unity-event] Error:', message);
    return new Response(JSON.stringify({ error: message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
