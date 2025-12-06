import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

/**
 * Fetch Kraken Market Data Edge Function
 * Prime Sentinel: GARY LECKEY 02111991
 * 
 * Fetches real-time market data from Kraken public API
 * No authentication required - public endpoint
 */
serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { symbols } = await req.json().catch(() => ({ symbols: ['XBTUSD', 'ETHUSD', 'SOLUSD'] }));
    
    // Kraken uses different symbol naming
    const krakenSymbols = symbols.map((s: string) => {
      const mapping: Record<string, string> = {
        'BTCUSDT': 'XBTUSDT',
        'BTCUSD': 'XBTUSD',
        'ETHUSDT': 'ETHUSDT',
        'ETHUSD': 'ETHUSD',
        'SOLUSDT': 'SOLUSDT',
        'SOLUSD': 'SOLUSD',
      };
      return mapping[s] || s;
    });

    const startTime = Date.now();
    
    // Fetch ticker data from Kraken public API
    const pairParam = krakenSymbols.join(',');
    const response = await fetch(`https://api.kraken.com/0/public/Ticker?pair=${pairParam}`);
    
    const latencyMs = Date.now() - startTime;

    if (!response.ok) {
      throw new Error(`Kraken API error: ${response.status}`);
    }

    const data = await response.json();

    if (data.error && data.error.length > 0) {
      throw new Error(`Kraken error: ${data.error.join(', ')}`);
    }

    // Parse Kraken ticker format
    const tickers: Record<string, any> = {};
    
    for (const [krakenPair, tickerData] of Object.entries(data.result || {})) {
      const ticker = tickerData as any;
      const price = parseFloat(ticker.c?.[0] || '0');
      const volume = parseFloat(ticker.v?.[1] || '0');
      const high = parseFloat(ticker.h?.[1] || '0');
      const low = parseFloat(ticker.l?.[1] || '0');
      const open = parseFloat(ticker.o || '0');
      const change = open > 0 ? ((price - open) / open) * 100 : 0;
      
      // Calculate volatility as (high - low) / price * 100
      const volatility = price > 0 ? ((high - low) / price) * 100 : 0;
      
      // Momentum approximation
      const momentum = change / 10; // Simplified momentum

      tickers[krakenPair] = {
        symbol: krakenPair,
        price,
        volume24h: volume,
        high24h: high,
        low24h: low,
        change24h: change,
        volatility,
        momentum,
        timestamp: Date.now(),
        exchange: 'kraken',
      };
    }

    console.log(`[fetch-kraken-market-data] ✅ Fetched ${Object.keys(tickers).length} tickers in ${latencyMs}ms`);

    return new Response(
      JSON.stringify({
        success: true,
        exchange: 'kraken',
        tickers,
        primaryTicker: tickers['XXBTZUSD'] || tickers['XBTUSDT'] || Object.values(tickers)[0],
        latencyMs,
        timestamp: Date.now(),
        dataSource: 'LIVE',
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200 
      }
    );

  } catch (error) {
    console.error('[fetch-kraken-market-data] ❌ Error:', error);
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    
    return new Response(
      JSON.stringify({ 
        success: false,
        exchange: 'kraken',
        error: errorMessage,
        dataSource: 'ERROR',
        timestamp: Date.now(),
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 500 
      }
    );
  }
});
