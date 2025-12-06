import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { symbol = 'BTCUSDT' } = await req.json();

    // Fetch real market data from Binance public API
    const tickerResponse = await fetch(
      `https://api.binance.com/api/v3/ticker/24hr?symbol=${symbol}`
    );

    if (!tickerResponse.ok) {
      throw new Error('Failed to fetch ticker data');
    }

    const ticker = await tickerResponse.json();

    // Calculate derived metrics
    const price = parseFloat(ticker.lastPrice);
    const volume = parseFloat(ticker.volume);
    const priceChange = parseFloat(ticker.priceChangePercent);
    const highPrice = parseFloat(ticker.highPrice);
    const lowPrice = parseFloat(ticker.lowPrice);
    
    // Volatility approximation from high-low range
    const volatility = (highPrice - lowPrice) / price;
    
    // Momentum from price change
    const momentum = priceChange / 100;
    
    // Spread approximation
    const spread = parseFloat(ticker.askPrice) - parseFloat(ticker.bidPrice);
    const spreadPercent = spread / price;

    const marketData = {
      symbol,
      price,
      volume,
      volatility,
      momentum,
      spread: spreadPercent,
      priceChange,
      highPrice,
      lowPrice,
      timestamp: Date.now(),
    };

    console.log(`[get-user-market-data] ${symbol}: $${price.toFixed(2)}, vol: ${volatility.toFixed(4)}, mom: ${momentum.toFixed(4)}`);

    return new Response(JSON.stringify(marketData), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    console.error('[get-user-market-data] Error:', errorMessage);
    
    return new Response(
      JSON.stringify({ error: errorMessage }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});
