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
    const apiKey = Deno.env.get('CAPITAL_API_KEY');
    const password = Deno.env.get('CAPITAL_PASSWORD');
    const identifier = Deno.env.get('CAPITAL_IDENTIFIER');

    if (!apiKey || !password || !identifier) {
      return new Response(
        JSON.stringify({ error: 'Capital.com credentials not configured' }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 400 }
      );
    }

    const body = await req.json();
    const { epic, direction, size, stopLevel, profitLevel } = body;

    if (!epic || !direction || !size) {
      return new Response(
        JSON.stringify({ error: 'Missing required parameters: epic, direction, size' }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 400 }
      );
    }

    const baseUrl = 'https://api-capital.backend-capital.com';

    // Create session
    console.log('[execute-trade-capital] Creating session...');
    const sessionResponse = await fetch(`${baseUrl}/api/v1/session`, {
      method: 'POST',
      headers: {
        'X-CAP-API-KEY': apiKey,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ identifier, password }),
    });

    if (!sessionResponse.ok) {
      return new Response(
        JSON.stringify({ error: 'Authentication failed' }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 401 }
      );
    }

    const cst = sessionResponse.headers.get('CST');
    const securityToken = sessionResponse.headers.get('X-SECURITY-TOKEN');

    if (!cst || !securityToken) {
      return new Response(
        JSON.stringify({ error: 'Authentication failed - missing tokens' }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 401 }
      );
    }

    // Place order
    const orderPayload: Record<string, any> = {
      epic,
      direction: direction.toUpperCase(), // BUY or SELL
      size: size.toString(),
    };

    if (stopLevel) orderPayload.stopLevel = stopLevel;
    if (profitLevel) orderPayload.profitLevel = profitLevel;

    console.log(`[execute-trade-capital] Placing ${direction} order for ${size} ${epic}`);

    const orderResponse = await fetch(`${baseUrl}/api/v1/positions`, {
      method: 'POST',
      headers: {
        'X-CAP-API-KEY': apiKey,
        'CST': cst,
        'X-SECURITY-TOKEN': securityToken,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(orderPayload),
    });

    const data = await orderResponse.json();

    if (!orderResponse.ok) {
      console.error('[execute-trade-capital] Capital.com API error:', data);
      return new Response(
        JSON.stringify({ error: 'Trade execution failed' }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 400 }
      );
    }

    console.log('[execute-trade-capital] Position opened successfully:', data.dealReference);

    return new Response(
      JSON.stringify({
        success: true,
        exchange: 'capital',
        dealReference: data.dealReference,
        epic,
        direction,
        size,
        affectedDeals: data.affectedDeals,
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    console.error('[execute-trade-capital] Error:', error);
    return new Response(
      JSON.stringify({ error: 'Internal error executing Capital.com trade' }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
    );
  }
});
