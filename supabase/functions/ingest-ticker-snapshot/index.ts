import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

interface TickerSnapshot {
  symbol: string;
  exchange: string;
  price: number;
  bidPrice?: number;
  askPrice?: number;
  volume?: number;
  volumeUsd?: number;
  high24h?: number;
  low24h?: number;
  priceChange24h?: number;
  volatility?: number;
  momentum?: number;
  spread?: number;
  isValidated?: boolean;
  dataSource?: string;
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    );

    const { temporal_id, tickers, single } = await req.json();

    // Support both single ticker and batch
    const tickersToInsert: TickerSnapshot[] = single ? [single] : (tickers || []);

    if (tickersToInsert.length === 0) {
      return new Response(
        JSON.stringify({ success: true, inserted: 0, message: 'No tickers to insert' }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    console.log(`[ingest-ticker-snapshot] Inserting ${tickersToInsert.length} ticker snapshots...`);

    // Transform to database format
    const records = tickersToInsert.map(t => ({
      temporal_id: temporal_id || `ticker-${Date.now()}`,
      symbol: t.symbol,
      exchange: t.exchange || 'binance',
      price: t.price,
      bid_price: t.bidPrice,
      ask_price: t.askPrice,
      volume: t.volume,
      volume_usd: t.volumeUsd,
      high_24h: t.high24h,
      low_24h: t.low24h,
      price_change_24h: t.priceChange24h,
      volatility: t.volatility,
      momentum: t.momentum,
      spread: t.spread,
      is_validated: t.isValidated ?? false,
      validation_status: t.isValidated ? 'valid' : 'pending',
      data_source: t.dataSource || 'live',
      fetched_at: new Date().toISOString(),
    }));

    // Insert in batch
    const { data, error } = await supabase
      .from('ticker_snapshots')
      .insert(records)
      .select('id');

    if (error) {
      console.error('[ingest-ticker-snapshot] Insert error:', error);
      throw error;
    }

    console.log(`[ingest-ticker-snapshot] Successfully inserted ${data?.length || 0} snapshots`);

    return new Response(
      JSON.stringify({
        success: true,
        inserted: data?.length || 0,
        temporal_id,
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  } catch (error) {
    console.error('[ingest-ticker-snapshot] Error:', error);
    return new Response(
      JSON.stringify({ 
        success: false, 
        error: error instanceof Error ? error.message : 'Unknown error' 
      }),
      { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});
