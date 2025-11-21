import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    console.log('Fetching all Binance spot trading symbols...');

    // Fetch exchange info from Binance
    const response = await fetch('https://api.binance.com/api/v3/exchangeInfo');
    
    if (!response.ok) {
      throw new Error(`Binance API error: ${response.status}`);
    }

    const data = await response.json();

    // Filter for USDT spot trading pairs that are actively trading
    const usdtPairs = data.symbols
      .filter((symbol: any) => 
        symbol.quoteAsset === 'USDT' && 
        symbol.status === 'TRADING' &&
        symbol.isSpotTradingAllowed &&
        !symbol.symbol.includes('DOWN') &&
        !symbol.symbol.includes('UP') &&
        !symbol.symbol.includes('BEAR') &&
        !symbol.symbol.includes('BULL')
      )
      .map((symbol: any) => ({
        symbol: symbol.symbol,
        baseAsset: symbol.baseAsset,
        quoteAsset: symbol.quoteAsset,
        minQty: parseFloat(symbol.filters.find((f: any) => f.filterType === 'LOT_SIZE')?.minQty || '0'),
        maxQty: parseFloat(symbol.filters.find((f: any) => f.filterType === 'LOT_SIZE')?.maxQty || '0'),
        stepSize: parseFloat(symbol.filters.find((f: any) => f.filterType === 'LOT_SIZE')?.stepSize || '0'),
        minNotional: parseFloat(symbol.filters.find((f: any) => f.filterType === 'NOTIONAL')?.minNotional || '10'),
        tickSize: parseFloat(symbol.filters.find((f: any) => f.filterType === 'PRICE_FILTER')?.tickSize || '0'),
        permissions: symbol.permissions,
      }))
      .sort((a: any, b: any) => a.symbol.localeCompare(b.symbol));

    console.log(`Found ${usdtPairs.length} USDT spot trading pairs`);

    // Fetch current prices for all symbols
    const tickerResponse = await fetch('https://api.binance.com/api/v3/ticker/24hr');
    const tickers = await tickerResponse.json();
    
    // Create price map
    const priceMap: Record<string, any> = {};
    tickers.forEach((ticker: any) => {
      priceMap[ticker.symbol] = {
        price: parseFloat(ticker.lastPrice),
        volume24h: parseFloat(ticker.volume),
        priceChange24h: parseFloat(ticker.priceChangePercent),
        high24h: parseFloat(ticker.highPrice),
        low24h: parseFloat(ticker.lowPrice),
      };
    });

    // Enrich symbol data with prices
    const enrichedPairs = usdtPairs.map((pair: any) => ({
      ...pair,
      ...priceMap[pair.symbol],
    }));

    return new Response(
      JSON.stringify({
        symbols: enrichedPairs,
        count: enrichedPairs.length,
        fetchedAt: new Date().toISOString(),
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    console.error('Error fetching Binance symbols:', error);
    return new Response(
      JSON.stringify({ 
        error: error instanceof Error ? error.message : 'Failed to fetch symbols',
        symbols: [],
        count: 0,
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
    );
  }
});