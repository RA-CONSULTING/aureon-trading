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
      selected_exchange,
      binance_fee,
      kraken_fee,
      fee_savings,
      routing_reason,
      metadata
    } = body;

    console.log(`[ingest-smart-router] Ingesting state for temporal_id: ${temporal_id}`);

    const { data, error } = await supabase
      .from('smart_router_states')
      .insert({
        temporal_id,
        selected_exchange: selected_exchange || 'binance',
        binance_fee: binance_fee || 0.001,
        kraken_fee: kraken_fee || 0.0026,
        fee_savings: fee_savings || 0,
        routing_reason: routing_reason || 'DEFAULT',
        metadata: metadata || {}
      })
      .select()
      .single();

    if (error) {
      console.error('[ingest-smart-router] Error:', error);
      throw error;
    }

    console.log(`[ingest-smart-router] Successfully ingested state: ${data.id}`);

    return new Response(JSON.stringify({ success: true, data }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    console.error('[ingest-smart-router] Error:', message);
    return new Response(JSON.stringify({ error: message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
