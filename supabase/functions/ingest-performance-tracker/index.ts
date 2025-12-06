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
    console.log('[ingest-performance-tracker] Received:', JSON.stringify(body));

    const { data, error } = await supabase
      .from('performance_tracker_states')
      .insert({
        temporal_id: body.temporal_id || `perf-${Date.now()}`,
        realized_pnl: body.realized_pnl || 0,
        unrealized_pnl: body.unrealized_pnl || 0,
        total_trades: body.total_trades || 0,
        wins: body.wins || 0,
        sharpe: body.sharpe || 0,
        max_drawdown: body.max_drawdown || 0,
        metadata: body.metadata || {},
      })
      .select()
      .single();

    if (error) {
      console.error('[ingest-performance-tracker] Error:', error);
      throw error;
    }

    console.log('[ingest-performance-tracker] Inserted:', data?.id);
    return new Response(JSON.stringify({ success: true, id: data?.id }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    console.error('[ingest-performance-tracker] Error:', message);
    return new Response(JSON.stringify({ error: message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
