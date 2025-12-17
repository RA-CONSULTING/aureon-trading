import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

interface TradeRecord {
  transaction_id: string;
  exchange: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  price: number;
  quantity: number;
  quote_qty?: number;
  fee?: number;
  fee_asset?: string;
  timestamp: string;
  pnl?: number;
  is_win?: boolean;
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL') ?? '';
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '';

    if (!supabaseUrl || !supabaseServiceKey) {
      console.error('[ingest-trades] Missing env vars');
      return new Response(JSON.stringify({ error: 'Server configuration error' }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    const body = await req.json();
    const trades: TradeRecord[] = Array.isArray(body.trades) ? body.trades : body.trade ? [body.trade] : [];
    const userId = body.user_id;

    if (trades.length === 0) {
      return new Response(JSON.stringify({ error: 'No trades provided' }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    console.log(`[ingest-trades] Ingesting ${trades.length} trades for user: ${userId || 'system'}`);

    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    // Map trades to trade_records format
    const records = trades.map((t) => ({
      transaction_id: t.transaction_id || `${t.exchange}-${t.symbol}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      exchange: t.exchange || 'binance',
      symbol: t.symbol,
      side: t.side,
      price: t.price,
      quantity: t.quantity,
      quote_qty: t.quote_qty || t.price * t.quantity,
      fee: t.fee || 0,
      fee_asset: t.fee_asset || 'USDT',
      timestamp: t.timestamp || new Date().toISOString(),
      user_id: userId || null,
      pnl: t.pnl || null,
      is_win: t.is_win ?? null,
    }));

    // Upsert trades (avoid duplicates based on transaction_id)
    const { data, error } = await supabase
      .from('trade_records')
      .upsert(records, { onConflict: 'transaction_id' })
      .select();

    if (error) {
      console.error('[ingest-trades] Upsert error:', error);
      return new Response(JSON.stringify({ error: error.message }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    console.log(`[ingest-trades] Successfully ingested ${data?.length || 0} trades`);

    // Calculate summary stats
    const totalTrades = data?.length || 0;
    const wins = data?.filter((t: any) => t.is_win === true).length || 0;
    const winRate = totalTrades > 0 ? (wins / totalTrades * 100).toFixed(1) : '0';

    return new Response(JSON.stringify({
      success: true,
      ingested: totalTrades,
      wins,
      winRate: `${winRate}%`,
      trades: data,
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  } catch (error: unknown) {
    console.error('[ingest-trades] Error:', error);
    const message = error instanceof Error ? error.message : 'Unknown error';
    return new Response(JSON.stringify({ error: message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
