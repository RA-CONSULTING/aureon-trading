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
      exchange,
      symbol,
      total_trades,
      wins,
      losses,
      total_profit,
      avg_latency_ms,
      last_trade_at,
      win_rate,
      avg_pnl,
      metadata
    } = body;

    console.log(`[ingest-exchange-learning] Ingesting state for ${exchange}/${symbol}`);

    const { data, error } = await supabase
      .from('exchange_learning_states')
      .insert({
        temporal_id,
        exchange,
        symbol,
        total_trades: total_trades || 0,
        wins: wins || 0,
        losses: losses || 0,
        total_profit: total_profit || 0,
        avg_latency_ms,
        last_trade_at,
        win_rate,
        avg_pnl,
        metadata: metadata || {}
      })
      .select()
      .single();

    if (error) {
      console.error('[ingest-exchange-learning] Error:', error);
      throw error;
    }

    console.log(`[ingest-exchange-learning] Successfully ingested state: ${data.id}`);

    return new Response(JSON.stringify({ success: true, data }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    console.error('[ingest-exchange-learning] Error:', message);
    return new Response(JSON.stringify({ error: message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
