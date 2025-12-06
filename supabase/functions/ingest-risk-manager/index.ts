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
    console.log('[ingest-risk-manager] Received:', JSON.stringify(body));

    const { data, error } = await supabase
      .from('risk_manager_states')
      .insert({
        temporal_id: body.temporal_id || `risk-${Date.now()}`,
        equity: body.equity || 0,
        max_drawdown: body.max_drawdown || 0,
        open_positions_count: body.open_positions_count || 0,
        open_positions: body.open_positions || [],
        metadata: body.metadata || {},
      })
      .select()
      .single();

    if (error) {
      console.error('[ingest-risk-manager] Error:', error);
      throw error;
    }

    console.log('[ingest-risk-manager] Inserted:', data?.id);
    return new Response(JSON.stringify({ success: true, id: data?.id }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    console.error('[ingest-risk-manager] Error:', message);
    return new Response(JSON.stringify({ error: message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
