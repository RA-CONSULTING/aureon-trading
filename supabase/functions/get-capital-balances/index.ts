import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

interface CapitalBalance {
  asset: string;
  free: number;
  locked: number;
  total: number;
  usdValue: number;
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const apiKey = Deno.env.get('CAPITAL_API_KEY');
    const password = Deno.env.get('CAPITAL_PASSWORD');
    const identifier = Deno.env.get('CAPITAL_IDENTIFIER');

    if (!apiKey || !password || !identifier) {
      console.log('[get-capital-balances] No Capital.com credentials configured');
      return new Response(
        JSON.stringify({ 
          balances: [], 
          totalUsd: 0,
          connected: false,
          message: 'Capital.com credentials not configured'
        }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // Capital.com API - Create session first
    const baseUrl = 'https://api-capital.backend-capital.com';
    
    console.log('[get-capital-balances] Creating Capital.com session...');
    
    const sessionResponse = await fetch(`${baseUrl}/api/v1/session`, {
      method: 'POST',
      headers: {
        'X-CAP-API-KEY': apiKey,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        identifier,
        password,
      }),
    });

    if (!sessionResponse.ok) {
      console.error('[get-capital-balances] Session creation failed:', sessionResponse.status);
      return new Response(
        JSON.stringify({ 
          balances: [], 
          totalUsd: 0,
          connected: false,
          error: 'Failed to authenticate with Capital.com'
        }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // Get security tokens from response headers
    const cst = sessionResponse.headers.get('CST');
    const securityToken = sessionResponse.headers.get('X-SECURITY-TOKEN');

    if (!cst || !securityToken) {
      console.error('[get-capital-balances] Missing security tokens');
      return new Response(
        JSON.stringify({ 
          balances: [], 
          totalUsd: 0,
          connected: false,
          error: 'Authentication failed - missing tokens'
        }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // Fetch account info
    console.log('[get-capital-balances] Fetching account balances...');
    
    const accountResponse = await fetch(`${baseUrl}/api/v1/accounts`, {
      headers: {
        'X-CAP-API-KEY': apiKey,
        'CST': cst,
        'X-SECURITY-TOKEN': securityToken,
      },
    });

    if (!accountResponse.ok) {
      console.error('[get-capital-balances] Account fetch failed:', accountResponse.status);
      return new Response(
        JSON.stringify({ 
          balances: [], 
          totalUsd: 0,
          connected: false,
          error: 'Failed to fetch account data'
        }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    const accountData = await accountResponse.json();
    const balances: CapitalBalance[] = [];
    let totalUsd = 0;

    // Process accounts
    for (const account of accountData.accounts || []) {
      const balance = account.balance?.balance || 0;
      const currency = account.currency || 'USD';
      
      // Convert to USD (simplified - in production use real FX rates)
      let usdValue = balance;
      if (currency === 'GBP') usdValue = balance * 1.27;
      if (currency === 'EUR') usdValue = balance * 1.08;

      if (balance > 0) {
        balances.push({
          asset: currency,
          free: balance,
          locked: 0,
          total: balance,
          usdValue,
        });
        totalUsd += usdValue;
      }
    }

    // Fetch positions
    const positionsResponse = await fetch(`${baseUrl}/api/v1/positions`, {
      headers: {
        'X-CAP-API-KEY': apiKey,
        'CST': cst,
        'X-SECURITY-TOKEN': securityToken,
      },
    });

    if (positionsResponse.ok) {
      const positionsData = await positionsResponse.json();
      
      for (const position of positionsData.positions || []) {
        const marketValue = position.position?.upl || 0; // Unrealized P/L
        const size = position.position?.size || 0;
        const epic = position.market?.epic || 'UNKNOWN';
        
        if (size !== 0) {
          balances.push({
            asset: epic,
            free: size,
            locked: 0,
            total: size,
            usdValue: Math.abs(marketValue),
          });
        }
      }
    }

    console.log(`[get-capital-balances] Found ${balances.length} assets, total: $${totalUsd.toFixed(2)}`);

    return new Response(
      JSON.stringify({ 
        balances, 
        totalUsd,
        connected: true,
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    console.error('[get-capital-balances] Error:', error);
    return new Response(
      JSON.stringify({ 
        balances: [], 
        totalUsd: 0,
        connected: false,
        error: 'Internal error fetching Capital.com balances'
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
    );
  }
});
