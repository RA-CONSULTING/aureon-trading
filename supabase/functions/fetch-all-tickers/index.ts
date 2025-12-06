import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

interface TickerData {
  symbol: string;
  exchange: string;
  price: number;
  bidPrice: number;
  askPrice: number;
  volume: number;
  volumeUsd: number;
  high24h: number;
  low24h: number;
  priceChange24h: number;
  volatility: number;
  momentum: number;
  spread: number;
  timestamp: number;
  isValidated: boolean;
  dataSource: string;
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { symbols, exchanges = ['binance'], limit = 100 } = await req.json().catch(() => ({}));
    
    const allTickers: TickerData[] = [];
    const errors: string[] = [];
    const fetchedAt = Date.now();

    // Fetch from Binance (primary exchange)
    if (exchanges.includes('binance')) {
      try {
        console.log('[fetch-all-tickers] Fetching Binance tickers...');
        
        // Fetch all 24hr tickers in one call
        const response = await fetch('https://api.binance.com/api/v3/ticker/24hr');
        
        if (response.ok) {
          const tickers = await response.json();
          
          // Filter by symbols if provided, otherwise take top by volume
          let filteredTickers = tickers;
          
          if (symbols && symbols.length > 0) {
            filteredTickers = tickers.filter((t: any) => symbols.includes(t.symbol));
          } else {
            // Filter USDT pairs and sort by volume
            filteredTickers = tickers
              .filter((t: any) => t.symbol.endsWith('USDT') && parseFloat(t.quoteVolume) > 100000)
              .sort((a: any, b: any) => parseFloat(b.quoteVolume) - parseFloat(a.quoteVolume))
              .slice(0, limit);
          }
          
          for (const t of filteredTickers) {
            const price = parseFloat(t.lastPrice);
            const high = parseFloat(t.highPrice);
            const low = parseFloat(t.lowPrice);
            const bidPrice = parseFloat(t.bidPrice);
            const askPrice = parseFloat(t.askPrice);
            const volume = parseFloat(t.volume);
            const quoteVolume = parseFloat(t.quoteVolume);
            const priceChange = parseFloat(t.priceChangePercent);
            
            // Calculate derived metrics
            const volatility = price > 0 ? (high - low) / price : 0;
            const momentum = priceChange / 100;
            const spread = price > 0 ? (askPrice - bidPrice) / price : 0;
            
            allTickers.push({
              symbol: t.symbol,
              exchange: 'binance',
              price,
              bidPrice,
              askPrice,
              volume,
              volumeUsd: quoteVolume,
              high24h: high,
              low24h: low,
              priceChange24h: priceChange,
              volatility,
              momentum,
              spread,
              timestamp: fetchedAt,
              isValidated: true,
              dataSource: 'live',
            });
          }
          
          console.log(`[fetch-all-tickers] Binance: ${allTickers.length} tickers fetched`);
        } else {
          errors.push(`Binance API error: ${response.status}`);
        }
      } catch (error) {
        console.error('[fetch-all-tickers] Binance error:', error);
        errors.push(`Binance: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    }

    // Fetch from Kraken (if requested)
    if (exchanges.includes('kraken')) {
      try {
        console.log('[fetch-all-tickers] Fetching Kraken tickers...');
        
        const response = await fetch('https://api.kraken.com/0/public/Ticker?pair=XBTUSD,ETHUSD,SOLUSD');
        
        if (response.ok) {
          const data = await response.json();
          
          if (data.result) {
            for (const [pair, t] of Object.entries(data.result) as any) {
              const ticker = t as any;
              const price = parseFloat(ticker.c[0]);
              const high = parseFloat(ticker.h[1]); // 24h high
              const low = parseFloat(ticker.l[1]); // 24h low
              const volume = parseFloat(ticker.v[1]); // 24h volume
              
              // Map Kraken pairs to standard symbols
              const symbolMap: Record<string, string> = {
                'XXBTZUSD': 'BTCUSDT',
                'XETHZUSD': 'ETHUSDT',
                'SOLUSD': 'SOLUSDT',
              };
              
              const standardSymbol = symbolMap[pair] || pair;
              
              allTickers.push({
                symbol: standardSymbol,
                exchange: 'kraken',
                price,
                bidPrice: parseFloat(ticker.b[0]),
                askPrice: parseFloat(ticker.a[0]),
                volume,
                volumeUsd: volume * price,
                high24h: high,
                low24h: low,
                priceChange24h: price > 0 ? ((price - parseFloat(ticker.o)) / parseFloat(ticker.o)) * 100 : 0,
                volatility: price > 0 ? (high - low) / price : 0,
                momentum: 0,
                spread: price > 0 ? (parseFloat(ticker.a[0]) - parseFloat(ticker.b[0])) / price : 0,
                timestamp: fetchedAt,
                isValidated: true,
                dataSource: 'live',
              });
            }
          }
          
          console.log(`[fetch-all-tickers] Kraken: ${Object.keys(data.result || {}).length} tickers fetched`);
        }
      } catch (error) {
        console.error('[fetch-all-tickers] Kraken error:', error);
        errors.push(`Kraken: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    }

    // Sort by volume USD descending
    allTickers.sort((a, b) => b.volumeUsd - a.volumeUsd);

    // Calculate aggregate stats
    const stats = {
      totalTickers: allTickers.length,
      exchangeBreakdown: {} as Record<string, number>,
      avgVolatility: 0,
      avgSpread: 0,
      topSymbol: allTickers[0]?.symbol || null,
      topVolume: allTickers[0]?.volumeUsd || 0,
    };

    for (const t of allTickers) {
      stats.exchangeBreakdown[t.exchange] = (stats.exchangeBreakdown[t.exchange] || 0) + 1;
      stats.avgVolatility += t.volatility;
      stats.avgSpread += t.spread;
    }

    if (allTickers.length > 0) {
      stats.avgVolatility /= allTickers.length;
      stats.avgSpread /= allTickers.length;
    }

    console.log(`[fetch-all-tickers] Total: ${allTickers.length} tickers from ${Object.keys(stats.exchangeBreakdown).length} exchanges`);

    return new Response(
      JSON.stringify({
        success: true,
        tickers: allTickers,
        stats,
        fetchedAt,
        errors: errors.length > 0 ? errors : undefined,
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  } catch (error) {
    console.error('[fetch-all-tickers] Error:', error);
    return new Response(
      JSON.stringify({ 
        success: false, 
        error: error instanceof Error ? error.message : 'Unknown error' 
      }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});
