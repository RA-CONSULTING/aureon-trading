import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

interface HistoricalDataRequest {
  symbol: string;
  interval: string; // 1m, 5m, 15m, 1h, 4h, 1d
  startTime: number;
  endTime: number;
  limit?: number;
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { symbol, interval, startTime, endTime, limit = 1000 }: HistoricalDataRequest = await req.json();

    console.log(`📊 Fetching historical data for ${symbol} from ${new Date(startTime)} to ${new Date(endTime)}`);

    // Binance API endpoint for historical klines
    const url = new URL('https://api.binance.com/api/v3/klines');
    url.searchParams.append('symbol', symbol.toUpperCase());
    url.searchParams.append('interval', interval);
    url.searchParams.append('startTime', startTime.toString());
    url.searchParams.append('endTime', endTime.toString());
    url.searchParams.append('limit', Math.min(limit, 1000).toString());

    const response = await fetch(url.toString());
    
    if (!response.ok) {
      throw new Error(`Binance API error: ${response.statusText}`);
    }

    const klines = await response.json();

    // Transform Binance kline format to our format
    // [openTime, open, high, low, close, volume, closeTime, quoteVolume, trades, takerBuyBase, takerBuyQuote, ignore]
    const candles = klines.map((k: any[]) => ({
      timestamp: k[0],
      open: parseFloat(k[1]),
      high: parseFloat(k[2]),
      low: parseFloat(k[3]),
      close: parseFloat(k[4]),
      volume: parseFloat(k[5]),
      closeTime: k[6],
      quoteVolume: parseFloat(k[7]),
      trades: k[8],
    }));

    console.log(`✅ Fetched ${candles.length} candles`);

    return new Response(
      JSON.stringify({ success: true, candles, count: candles.length }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  } catch (error) {
    console.error('Historical data fetch error:', error);
    return new Response(
      JSON.stringify({ success: false, error: error instanceof Error ? error.message : 'Unknown error' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});
