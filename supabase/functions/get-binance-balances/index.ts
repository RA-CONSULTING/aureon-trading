import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseKey);

    // Get all active credentials
    const { data: credentials, error: credError } = await supabase
      .from('binance_credentials')
      .select('*')
      .eq('is_active', true);

    if (credError) throw credError;

    if (!credentials || credentials.length === 0) {
      return new Response(
        JSON.stringify({ success: false, error: 'No active Binance credentials found' }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 400 }
      );
    }

    // Decrypt credentials
    function decryptValue(encrypted: string): string {
      const key = Deno.env.get('MASTER_ENCRYPTION_KEY') || 'default-key';
      const decoded = atob(encrypted);
      return decoded.split('::')[0];
    }

    // Fetch all current prices from Binance
    let priceMap: Record<string, number> = {};
    try {
      const priceResponse = await fetch('https://api.binance.com/api/v3/ticker/price');
      if (priceResponse.ok) {
        const prices = await priceResponse.json();
        priceMap = prices.reduce((acc: Record<string, number>, p: any) => {
          acc[p.symbol] = parseFloat(p.price);
          return acc;
        }, {});
        console.log(`✅ Fetched ${Object.keys(priceMap).length} price pairs`);
      }
    } catch (error) {
      console.error('Failed to fetch prices:', error);
    }

    // Fetch balances from all accounts
    const accountBalances = [];
    let totalUSDT = 0;
    let totalBTC = 0;
    let totalETH = 0;
    let totalUSDValue = 0;

    for (const cred of credentials) {
      const apiKey = decryptValue(cred.api_key_encrypted);
      const apiSecret = decryptValue(cred.api_secret_encrypted);

      try {
        // Get account balance from Binance
        const timestamp = Date.now();
        const queryString = `timestamp=${timestamp}`;
        
        // Sign request
        const crypto = await import("https://deno.land/std@0.177.0/crypto/mod.ts");
        const encoder = new TextEncoder();
        const key = await crypto.crypto.subtle.importKey(
          "raw",
          encoder.encode(apiSecret),
          { name: "HMAC", hash: "SHA-256" },
          false,
          ["sign"]
        );
        const signatureBuffer = await crypto.crypto.subtle.sign(
          "HMAC",
          key,
          encoder.encode(queryString)
        );
        const signature = Array.from(new Uint8Array(signatureBuffer))
          .map(b => b.toString(16).padStart(2, '0'))
          .join('');

        // Call Binance API
        const response = await fetch(
          `https://api.binance.com/api/v3/account?${queryString}&signature=${signature}`,
          {
            headers: {
              'X-MBX-APIKEY': apiKey,
            },
          }
        );

        if (!response.ok) {
          console.error(`Failed to fetch balance for ${cred.name}:`, await response.text());
          continue;
        }

        const accountData = await response.json();
        
        // Extract relevant balances and calculate USD value
        const balances: any = {};
        let accountUSDValue = 0;

        for (const balance of accountData.balances) {
          const free = parseFloat(balance.free);
          const locked = parseFloat(balance.locked);
          const total = free + locked;
          
          if (total > 0) {
            let usdValue = 0;
            
            // Calculate USD value
            if (balance.asset === 'USDT' || balance.asset === 'USDC' || balance.asset === 'BUSD') {
              usdValue = total; // Stablecoins are 1:1 with USD
            } else if (balance.asset === 'LDUSDT' || balance.asset === 'LDUSDC') {
              usdValue = total; // Liquid stablecoins are also ~1:1
            } else {
              // Try to find price in USDT pair
              const usdtSymbol = `${balance.asset}USDT`;
              if (priceMap[usdtSymbol]) {
                usdValue = total * priceMap[usdtSymbol];
              } else {
                // Try BTC pair, then convert BTC to USDT
                const btcSymbol = `${balance.asset}BTC`;
                if (priceMap[btcSymbol] && priceMap['BTCUSDT']) {
                  usdValue = total * priceMap[btcSymbol] * priceMap['BTCUSDT'];
                }
              }
            }
            
            balances[balance.asset] = {
              free,
              locked,
              total,
              usdValue
            };
            
            accountUSDValue += usdValue;
            
            // Aggregate totals
            if (balance.asset === 'USDT') totalUSDT += total;
            if (balance.asset === 'BTC') totalBTC += total;
            if (balance.asset === 'ETH') totalETH += total;
          }
        }

        totalUSDValue += accountUSDValue;

        accountBalances.push({
          name: cred.name,
          balances,
          canTrade: accountData.canTrade,
          canWithdraw: accountData.canWithdraw,
          canDeposit: accountData.canDeposit,
          updateTime: accountData.updateTime,
        });

      } catch (error) {
        console.error(`Error fetching balance for ${cred.name}:`, error);
        accountBalances.push({
          name: cred.name,
          error: error instanceof Error ? error.message : 'Unknown error',
        });
      }
    }

    console.log(`✅ Fetched balances from ${accountBalances.length} accounts`);
    console.log(`Total USDT: ${totalUSDT.toFixed(2)}, BTC: ${totalBTC.toFixed(6)}, ETH: ${totalETH.toFixed(6)}`);
    console.log(`💰 Total Portfolio Value: $${totalUSDValue.toFixed(2)} USD`);

    return new Response(
      JSON.stringify({
        success: true,
        accounts: accountBalances,
        totals: {
          USDT: totalUSDT,
          BTC: totalBTC,
          ETH: totalETH,
        },
        totalUSDValue,
        timestamp: new Date().toISOString(),
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    console.error('Get balances error:', error);
    return new Response(
      JSON.stringify({ success: false, error: error instanceof Error ? error.message : 'Unknown error' }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
    );
  }
});
