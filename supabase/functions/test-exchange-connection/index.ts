import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { exchange, apiKey, apiSecret, identifier, password } = await req.json();

    if (!exchange || !apiKey) {
      return new Response(JSON.stringify({ 
        success: false, 
        error: 'Exchange and API key required' 
      }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    console.log(`🔌 Testing ${exchange} connection...`);

    let result: { success: boolean; message: string; details?: any };

    switch (exchange.toLowerCase()) {
      case 'binance': {
        // Test Binance connection by checking account status
        const timestamp = Date.now();
        const queryString = `timestamp=${timestamp}`;
        
        // Create HMAC signature
        const encoder = new TextEncoder();
        const key = await crypto.subtle.importKey(
          'raw',
          encoder.encode(apiSecret),
          { name: 'HMAC', hash: 'SHA-256' },
          false,
          ['sign']
        );
        const signature = await crypto.subtle.sign('HMAC', key, encoder.encode(queryString));
        const signatureHex = Array.from(new Uint8Array(signature))
          .map(b => b.toString(16).padStart(2, '0'))
          .join('');

        const response = await fetch(
          `https://api.binance.com/api/v3/account?${queryString}&signature=${signatureHex}`,
          {
            headers: { 'X-MBX-APIKEY': apiKey }
          }
        );

        if (response.ok) {
          const data = await response.json();
          result = { 
            success: true, 
            message: 'Binance connection successful',
            details: { 
              canTrade: data.canTrade,
              canWithdraw: data.canWithdraw,
              canDeposit: data.canDeposit,
              accountType: data.accountType
            }
          };
        } else {
          const error = await response.json();
          result = { 
            success: false, 
            message: `Binance error: ${error.msg || 'Invalid credentials'}` 
          };
        }
        break;
      }

      case 'kraken': {
        // Test Kraken connection
        const nonce = Date.now() * 1000;
        const postData = `nonce=${nonce}`;
        const path = '/0/private/Balance';
        
        // Create Kraken signature
        const encoder = new TextEncoder();
        const sha256Hash = await crypto.subtle.digest('SHA-256', encoder.encode(nonce + postData));
        const message = new Uint8Array([...encoder.encode(path), ...new Uint8Array(sha256Hash)]);
        
        const secretDecoded = Uint8Array.from(atob(apiSecret), c => c.charCodeAt(0));
        const key = await crypto.subtle.importKey(
          'raw',
          secretDecoded,
          { name: 'HMAC', hash: 'SHA-512' },
          false,
          ['sign']
        );
        const signature = await crypto.subtle.sign('HMAC', key, message);
        const signatureB64 = btoa(String.fromCharCode(...new Uint8Array(signature)));

        const response = await fetch(`https://api.kraken.com${path}`, {
          method: 'POST',
          headers: {
            'API-Key': apiKey,
            'API-Sign': signatureB64,
            'Content-Type': 'application/x-www-form-urlencoded'
          },
          body: postData
        });

        const data = await response.json();
        if (data.error && data.error.length > 0) {
          result = { success: false, message: `Kraken error: ${data.error.join(', ')}` };
        } else {
          result = { 
            success: true, 
            message: 'Kraken connection successful',
            details: { balanceCount: Object.keys(data.result || {}).length }
          };
        }
        break;
      }

      case 'alpaca': {
        // Test Alpaca connection
        const response = await fetch('https://api.alpaca.markets/v2/account', {
          headers: {
            'APCA-API-KEY-ID': apiKey,
            'APCA-API-SECRET-KEY': apiSecret
          }
        });

        if (response.ok) {
          const data = await response.json();
          result = { 
            success: true, 
            message: 'Alpaca connection successful',
            details: { 
              status: data.status,
              tradingBlocked: data.trading_blocked,
              accountNumber: data.account_number?.slice(-4)
            }
          };
        } else {
          result = { success: false, message: 'Alpaca: Invalid credentials' };
        }
        break;
      }

      case 'capital': {
        // Test Capital.com connection
        const response = await fetch('https://api-capital.backend-capital.com/api/v1/session', {
          method: 'POST',
          headers: {
            'X-CAP-API-KEY': apiKey,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            identifier: identifier || '',
            password: password || ''
          })
        });

        if (response.ok) {
          result = { 
            success: true, 
            message: 'Capital.com connection successful' 
          };
        } else {
          result = { success: false, message: 'Capital.com: Invalid credentials' };
        }
        break;
      }

      default:
        result = { success: false, message: `Unknown exchange: ${exchange}` };
    }

    console.log(`${result.success ? '✅' : '❌'} ${exchange}: ${result.message}`);

    return new Response(JSON.stringify(result), {
      status: 200,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });

  } catch (error: unknown) {
    console.error('Connection test error:', error);
    const errorMessage = error instanceof Error ? error.message : 'Connection test failed';
    return new Response(JSON.stringify({ 
      success: false, 
      error: errorMessage 
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
