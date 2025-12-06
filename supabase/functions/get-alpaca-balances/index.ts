import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

interface AlpacaBalance {
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
    const apiKey = Deno.env.get('ALPACA_API_KEY');
    const apiSecret = Deno.env.get('ALPACA_SECRET_KEY');

    if (!apiKey || !apiSecret) {
      console.log('[get-alpaca-balances] No Alpaca credentials configured');
      return new Response(
        JSON.stringify({ 
          balances: [], 
          totalUsd: 0,
          connected: false,
          message: 'Alpaca credentials not configured'
        }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // Alpaca paper trading API (use api.alpaca.markets for live)
    const baseUrl = 'https://paper-api.alpaca.markets';
    
    // Fetch account info
    console.log('[get-alpaca-balances] Fetching account from Alpaca API...');
    const accountResponse = await fetch(`${baseUrl}/v2/account`, {
      headers: {
        'APCA-API-KEY-ID': apiKey,
        'APCA-API-SECRET-KEY': apiSecret,
      },
    });

    if (!accountResponse.ok) {
      console.error('[get-alpaca-balances] Account fetch failed:', accountResponse.status);
      return new Response(
        JSON.stringify({ 
          balances: [], 
          totalUsd: 0,
          connected: false,
          error: 'Failed to fetch Alpaca account'
        }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    const account = await accountResponse.json();
    
    // Fetch positions
    const positionsResponse = await fetch(`${baseUrl}/v2/positions`, {
      headers: {
        'APCA-API-KEY-ID': apiKey,
        'APCA-API-SECRET-KEY': apiSecret,
      },
    });

    const positions = positionsResponse.ok ? await positionsResponse.json() : [];

    const balances: AlpacaBalance[] = [];
    let totalUsd = 0;

    // Add cash balance
    const cashBalance = parseFloat(account.cash || '0');
    if (cashBalance > 0) {
      balances.push({
        asset: 'USD',
        free: cashBalance,
        locked: 0,
        total: cashBalance,
        usdValue: cashBalance,
      });
      totalUsd += cashBalance;
    }

    // Add positions
    for (const position of positions) {
      const marketValue = parseFloat(position.market_value || '0');
      const qty = parseFloat(position.qty || '0');
      
      balances.push({
        asset: position.symbol,
        free: qty,
        locked: 0,
        total: qty,
        usdValue: marketValue,
      });
      totalUsd += marketValue;
    }

    console.log(`[get-alpaca-balances] Found ${balances.length} assets, total: $${totalUsd.toFixed(2)}`);

    return new Response(
      JSON.stringify({ 
        balances, 
        totalUsd,
        connected: true,
        account: {
          id: account.id,
          status: account.status,
          buyingPower: parseFloat(account.buying_power || '0'),
          equity: parseFloat(account.equity || '0'),
          portfolioValue: parseFloat(account.portfolio_value || '0'),
        }
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    console.error('[get-alpaca-balances] Error:', error);
    return new Response(
      JSON.stringify({ 
        balances: [], 
        totalUsd: 0,
        connected: false,
        error: 'Internal error fetching Alpaca balances'
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
    );
  }
});
