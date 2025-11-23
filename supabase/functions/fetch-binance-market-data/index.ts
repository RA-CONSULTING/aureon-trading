import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { z } from 'https://deno.land/x/zod@v3.22.4/mod.ts';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

// Helper function to create HMAC signature
async function createSignature(secret: string, message: string): Promise<string> {
  const encoder = new TextEncoder();
  const keyData = encoder.encode(secret);
  const messageData = encoder.encode(message);
  
  const key = await crypto.subtle.importKey(
    'raw',
    keyData,
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );
  
  const signature = await crypto.subtle.sign('HMAC', key, messageData);
  return Array.from(new Uint8Array(signature))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    // Input validation
    const requestSchema = z.object({
      symbol: z.string().regex(/^[A-Z]+USDT$/, 'Invalid symbol').default('BTCUSDT')
    });
    
    const body = await req.json().catch(() => ({}));
    const { symbol } = requestSchema.parse(body);
    
    console.log('[fetch-binance-market-data] Fetching market data for:', symbol);

    const apiKey = Deno.env.get('BINANCE_API_KEY');
    const apiSecret = Deno.env.get('BINANCE_API_SECRET');

    if (!apiKey || !apiSecret) {
      throw new Error('Binance API credentials not configured');
    }

    const timestamp = Date.now();
    
    // Helper function to fetch with timeout and retry
    const fetchWithTimeout = async (url: string, options: RequestInit, timeoutMs = 15000, retries = 2) => {
      for (let attempt = 0; attempt <= retries; attempt++) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
        
        try {
          const response = await fetch(url, {
            ...options,
            signal: controller.signal
          });
          clearTimeout(timeoutId);
          return response;
        } catch (error) {
          clearTimeout(timeoutId);
          
          // If this is the last attempt, throw the error
          if (attempt === retries) {
            if (error instanceof Error && error.name === 'AbortError') {
              throw new Error(`Request timeout after ${timeoutMs}ms (${retries + 1} attempts)`);
            }
            throw error;
          }
          
          // Wait before retrying (exponential backoff)
          const delay = Math.min(1000 * Math.pow(2, attempt), 3000);
          console.log(`[fetch-binance-market-data] Retry attempt ${attempt + 1} after ${delay}ms`);
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
      
      throw new Error('Max retries exceeded');
    };

    // Fetch multiple endpoints in parallel for comprehensive market data with timeout
    const requests = [
      // 24hr ticker statistics
      fetchWithTimeout(`https://api.binance.com/api/v3/ticker/24hr?symbol=${symbol}`, {
        headers: { 'X-MBX-APIKEY': apiKey }
      }),
      
      // Current average price
      fetchWithTimeout(`https://api.binance.com/api/v3/avgPrice?symbol=${symbol}`, {
        headers: { 'X-MBX-APIKEY': apiKey }
      }),
      
      // Order book depth
      fetchWithTimeout(`https://api.binance.com/api/v3/depth?symbol=${symbol}&limit=20`, {
        headers: { 'X-MBX-APIKEY': apiKey }
      }),
      
      // Recent trades
      fetchWithTimeout(`https://api.binance.com/api/v3/trades?symbol=${symbol}&limit=10`, {
        headers: { 'X-MBX-APIKEY': apiKey }
      }),
    ];

    const [tickerRes, avgPriceRes, depthRes, tradesRes] = await Promise.all(requests);

    if (!tickerRes.ok) {
      console.error('[fetch-binance-market-data] Ticker API error:', tickerRes.status);
      return new Response(
        JSON.stringify({ success: false, error: 'Market data unavailable' }),
        { status: 503, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    const ticker = await tickerRes.json();
    const avgPrice = await avgPriceRes.json();
    const depth = await depthRes.json();
    const trades = await tradesRes.json();

    // Calculate additional metrics
    const bidPrice = depth.bids && depth.bids.length > 0 ? parseFloat(depth.bids[0][0]) : 0;
    const askPrice = depth.asks && depth.asks.length > 0 ? parseFloat(depth.asks[0][0]) : 0;
    const spread = askPrice - bidPrice;
    const spreadPercent = bidPrice > 0 ? (spread / bidPrice) * 100 : 0;

    // Calculate volatility from price change
    const priceChangePercent = parseFloat(ticker.priceChangePercent);
    const volatility = Math.abs(priceChangePercent) / 100;

    // Calculate momentum from weighted average price vs current price
    const currentPrice = parseFloat(ticker.lastPrice);
    const weightedAvgPrice = parseFloat(ticker.weightedAvgPrice);
    const momentum = ((currentPrice - weightedAvgPrice) / weightedAvgPrice) * 100;

    const marketData = {
      symbol: ticker.symbol,
      timestamp: Date.now(),
      
      // Price data
      price: currentPrice,
      highPrice: parseFloat(ticker.highPrice),
      lowPrice: parseFloat(ticker.lowPrice),
      openPrice: parseFloat(ticker.openPrice),
      previousClosePrice: parseFloat(ticker.prevClosePrice),
      priceChange: parseFloat(ticker.priceChange),
      priceChangePercent: priceChangePercent,
      avgPrice: parseFloat(avgPrice.price),
      weightedAvgPrice: weightedAvgPrice,
      
      // Volume data
      volume: parseFloat(ticker.volume),
      quoteVolume: parseFloat(ticker.quoteVolume),
      volumeNormalized: parseFloat(ticker.volume) / parseFloat(ticker.highPrice), // Normalize by high
      
      // Order book
      bidPrice: bidPrice,
      askPrice: askPrice,
      spread: spread,
      spreadPercent: spreadPercent,
      
      // Calculated metrics
      volatility: volatility,
      momentum: momentum,
      
      // Trading counts
      tradeCount: ticker.count,
      
      // Recent trades summary
      recentTrades: trades.map((t: any) => ({
        price: parseFloat(t.price),
        quantity: parseFloat(t.qty),
        time: t.time,
        isBuyerMaker: t.isBuyerMaker,
      })),
      
      // Top order book levels
      topBids: depth.bids.slice(0, 5).map((b: string[]) => ({
        price: parseFloat(b[0]),
        quantity: parseFloat(b[1]),
      })),
      topAsks: depth.asks.slice(0, 5).map((a: string[]) => ({
        price: parseFloat(a[0]),
        quantity: parseFloat(a[1]),
      })),
      
      // Metadata
      fetchedAt: new Date().toISOString(),
    };

    console.log('[fetch-binance-market-data] Market data fetched successfully');

    return new Response(
      JSON.stringify(marketData),
      {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    );

  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    console.error('[fetch-binance-market-data] Error:', errorMessage);
    
    // Return specific error types
    if (error instanceof z.ZodError) {
      return new Response(
        JSON.stringify({ success: false, error: 'Invalid symbol format', details: error.errors }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }
    
    // Network/timeout errors
    if (errorMessage.includes('timeout') || errorMessage.includes('network')) {
      return new Response(
        JSON.stringify({ success: false, error: 'Network timeout - please try again', details: errorMessage }),
        { status: 503, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }
    
    return new Response(
      JSON.stringify({ success: false, error: 'Failed to fetch market data', details: errorMessage }),
      {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    );
  }
});
