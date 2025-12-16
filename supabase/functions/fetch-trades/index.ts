import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import { createHmac } from "https://deno.land/std@0.177.0/node/crypto.ts";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_ANON_KEY') ?? '',
      { global: { headers: { Authorization: req.headers.get('Authorization')! } } }
    );

    const { data: { user }, error: authError } = await supabaseClient.auth.getUser();
    if (authError || !user) {
      return new Response(JSON.stringify({ error: 'Unauthorized' }), {
        status: 401,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    const { symbol = 'BTCUSDT', limit = 50 } = await req.json().catch(() => ({}));

    const apiKey = Deno.env.get('BINANCE_API_KEY');
    const apiSecret = Deno.env.get('BINANCE_API_SECRET');

    if (!apiKey || !apiSecret) {
      return new Response(JSON.stringify({ error: 'Binance credentials not configured' }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    const timestamp = Date.now();
    const queryString = `symbol=${symbol}&limit=${limit}&timestamp=${timestamp}`;
    const signature = createHmac('sha256', apiSecret).update(queryString).digest('hex');

    const response = await fetch(
      `https://api.binance.com/api/v3/myTrades?${queryString}&signature=${signature}`,
      {
        headers: { 'X-MBX-APIKEY': apiKey },
      }
    );

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Binance API error:', errorText);
      return new Response(JSON.stringify({ error: 'Failed to fetch trades', details: errorText }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    const trades = await response.json();

    // Store new trades in database
    const tradeRecords = trades.map((t: any) => ({
      transaction_id: String(t.id),
      exchange: 'binance',
      symbol: t.symbol,
      side: t.isBuyer ? 'BUY' : 'SELL',
      price: parseFloat(t.price),
      quantity: parseFloat(t.qty),
      quote_qty: parseFloat(t.quoteQty),
      fee: parseFloat(t.commission),
      fee_asset: t.commissionAsset,
      timestamp: new Date(t.time).toISOString(),
      user_id: user.id,
    }));

    // Upsert trades (avoid duplicates)
    for (const record of tradeRecords) {
      await supabaseClient
        .from('trade_records')
        .upsert(record, { onConflict: 'transaction_id' })
        .select();
    }

    return new Response(JSON.stringify({ trades: tradeRecords, count: tradeRecords.length }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  } catch (error: unknown) {
    console.error('Error fetching trades:', error);
    const message = error instanceof Error ? error.message : 'Unknown error';
    return new Response(JSON.stringify({ error: message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
