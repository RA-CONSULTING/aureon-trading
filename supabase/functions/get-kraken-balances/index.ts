import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

/**
 * Get Kraken Balances Edge Function
 * Prime Sentinel: GARY LECKEY 02111991
 * 
 * Fetches account balances from Kraken exchange
 */
serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    );

    // For now, return simulated Kraken balances
    // In production, this would use actual Kraken API credentials
    const krakenApiKey = Deno.env.get('KRAKEN_API_KEY');
    const krakenApiSecret = Deno.env.get('KRAKEN_API_SECRET');

    // NO DEMO MODE - Return explicit error if no credentials
    // This prevents silent fallback to fake data
    if (!krakenApiKey || !krakenApiSecret) {
      console.error('[get-kraken-balances] ❌ NO CREDENTIALS - Cannot fetch real balances');
      return new Response(
        JSON.stringify({
          success: false,
          exchange: 'kraken',
          error: 'NO_CREDENTIALS',
          message: 'Kraken API credentials not configured. Cannot fetch live balances.',
          dataSource: 'NONE',
          mode: 'error'
        }),
        { 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 401 
        }
      );
    }

    // Production Kraken API call
    const nonce = Date.now().toString();
    const apiPath = '/0/private/Balance';
    const apiData = `nonce=${nonce}`;

    // Create signature
    const encoder = new TextEncoder();
    const sha256Hash = await crypto.subtle.digest(
      'SHA-256',
      encoder.encode(nonce + apiData)
    );
    
    const apiSecretDecoded = atob(krakenApiSecret);
    const key = await crypto.subtle.importKey(
      'raw',
      encoder.encode(apiSecretDecoded),
      { name: 'HMAC', hash: 'SHA-512' },
      false,
      ['sign']
    );
    
    const pathBytes = encoder.encode(apiPath);
    const combined = new Uint8Array(pathBytes.length + sha256Hash.byteLength);
    combined.set(pathBytes);
    combined.set(new Uint8Array(sha256Hash), pathBytes.length);
    
    const signature = await crypto.subtle.sign('HMAC', key, combined);
    const signatureBase64 = btoa(String.fromCharCode(...new Uint8Array(signature)));

    const response = await fetch(`https://api.kraken.com${apiPath}`, {
      method: 'POST',
      headers: {
        'API-Key': krakenApiKey,
        'API-Sign': signatureBase64,
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: apiData
    });

    if (!response.ok) {
      throw new Error(`Kraken API error: ${response.status}`);
    }

    const data = await response.json();

    if (data.error && data.error.length > 0) {
      throw new Error(`Kraken error: ${data.error.join(', ')}`);
    }

    // Convert Kraken balances to unified format
    const balances = Object.entries(data.result || {}).map(([asset, balance]) => ({
      asset: asset.replace(/^X/, '').replace(/^Z/, ''), // Remove Kraken prefixes
      free: parseFloat(balance as string),
      locked: 0,
      total: parseFloat(balance as string),
      usdValue: 0 // Would need price data to calculate
    }));

    console.log(`Fetched ${balances.length} Kraken balances`);

    return new Response(
      JSON.stringify({
        success: true,
        exchange: 'kraken',
        balances,
        totalUsdValue: 0,
        mode: 'live'
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200 
      }
    );

  } catch (error) {
    console.error('Kraken balances error:', error);
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    return new Response(
      JSON.stringify({ 
        error: errorMessage,
        success: false,
        exchange: 'kraken'
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 500 
      }
    );
  }
});
