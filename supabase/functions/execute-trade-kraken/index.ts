import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { encode as base64Encode } from "https://deno.land/std@0.168.0/encoding/base64.ts";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

async function createKrakenSignature(
  apiSecret: string,
  path: string,
  nonce: number,
  postData: string
): Promise<string> {
  const message = nonce + postData;
  const msgHash = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(message));
  
  const secretDecoded = Uint8Array.from(atob(apiSecret), c => c.charCodeAt(0));
  const pathBytes = new TextEncoder().encode(path);
  
  const combined = new Uint8Array(pathBytes.length + msgHash.byteLength);
  combined.set(pathBytes);
  combined.set(new Uint8Array(msgHash), pathBytes.length);
  
  const key = await crypto.subtle.importKey(
    'raw',
    secretDecoded,
    { name: 'HMAC', hash: 'SHA-512' },
    false,
    ['sign']
  );
  
  const signature = await crypto.subtle.sign('HMAC', key, combined);
  return btoa(String.fromCharCode(...new Uint8Array(signature)));
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const apiKey = Deno.env.get('KRAKEN_API_KEY');
    const apiSecret = Deno.env.get('KRAKEN_API_SECRET');

    if (!apiKey || !apiSecret) {
      return new Response(
        JSON.stringify({ error: 'Kraken credentials not configured' }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 400 }
      );
    }

    const body = await req.json();
    const { symbol, side, quantity, orderType = 'market', price } = body;

    if (!symbol || !side || !quantity) {
      return new Response(
        JSON.stringify({ error: 'Missing required parameters: symbol, side, quantity' }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 400 }
      );
    }

    // Complete Kraken pair mapping (from Python aureon_unified_ecosystem.py)
    const normalizeToKrakenPair = (sym: string): string => {
      // Map standard symbols to Kraken format
      let pair = sym
        .replace('BTCUSDT', 'XBTUSD')
        .replace('BTCUSD', 'XBTUSD')
        .replace('ETHUSDT', 'ETHUSD')
        .replace('SOLUSDT', 'SOLUSD')
        .replace('XRPUSDT', 'XRPUSD')
        .replace('LTCUSDT', 'LTCUSD')
        .replace('DOGEUSDT', 'DOGEUSD')
        .replace('USDT', 'USD'); // Fallback for other pairs
      return pair;
    };
    const krakenPair = normalizeToKrakenPair(symbol);
    
    const nonce = Date.now() * 1000;
    const path = '/0/private/AddOrder';
    
    const params = new URLSearchParams({
      nonce: nonce.toString(),
      ordertype: orderType,
      type: side.toLowerCase(),
      volume: quantity.toString(),
      pair: krakenPair,
    });

    if (orderType === 'limit' && price) {
      params.append('price', price.toString());
    }

    const postData = params.toString();
    const signature = await createKrakenSignature(apiSecret, path, nonce, postData);

    console.log(`[execute-trade-kraken] Placing ${side} ${orderType} order for ${quantity} ${symbol}`);

    const response = await fetch('https://api.kraken.com/0/private/AddOrder', {
      method: 'POST',
      headers: {
        'API-Key': apiKey,
        'API-Sign': signature,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: postData,
    });

    const data = await response.json();

    if (data.error && data.error.length > 0) {
      console.error('[execute-trade-kraken] Kraken API error:', data.error);
      return new Response(
        JSON.stringify({ error: 'Trade execution failed' }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 400 }
      );
    }

    console.log('[execute-trade-kraken] Order placed successfully:', data.result);

    return new Response(
      JSON.stringify({
        success: true,
        exchange: 'kraken',
        orderId: data.result?.txid?.[0] || 'unknown',
        symbol,
        side,
        quantity,
        orderType,
        result: data.result,
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    console.error('[execute-trade-kraken] Error:', error);
    return new Response(
      JSON.stringify({ error: 'Internal error executing Kraken trade' }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
    );
  }
});
