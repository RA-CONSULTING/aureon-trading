import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

// Decrypt credentials using the same key as create-aureon-session
async function decrypt(encrypted: string, iv: string): Promise<string> {
  // Must match the key used in create-aureon-session
  const encryptionKey = 'aureon-default-key-32chars!!';
  
  const encoder = new TextEncoder();
  const keyData = encoder.encode(encryptionKey.padEnd(32, '0').slice(0, 32));
  const cryptoKey = await crypto.subtle.importKey(
    'raw',
    keyData,
    { name: 'AES-GCM' },
    false,
    ['decrypt']
  );
  
  const encryptedData = Uint8Array.from(atob(encrypted), c => c.charCodeAt(0));
  const ivData = Uint8Array.from(atob(iv), c => c.charCodeAt(0));
  
  const decrypted = await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv: ivData },
    cryptoKey,
    encryptedData
  );
  return new TextDecoder().decode(decrypted);
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { exchange } = await req.json();

    if (!exchange) {
      return new Response(JSON.stringify({ 
        success: false, 
        error: 'Exchange required' 
      }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // Get authenticated user
    const authHeader = req.headers.get('Authorization');
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    );

    const token = authHeader?.replace('Bearer ', '');
    const { data: { user }, error: authError } = await supabase.auth.getUser(token);

    if (authError || !user) {
      return new Response(JSON.stringify({ 
        success: false, 
        error: 'Authentication required' 
      }), {
        status: 401,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // Get user's credentials from database
    const { data: session, error: sessionError } = await supabase
      .from('aureon_user_sessions')
      .select('*')
      .eq('user_id', user.id)
      .single();

    if (sessionError || !session) {
      return new Response(JSON.stringify({ 
        success: false, 
        error: 'No session found. Please configure credentials in Settings.' 
      }), {
        status: 404,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    console.log(`🔌 Testing ${exchange} connection for user ${user.id.slice(0, 8)}...`);

    let result: { success: boolean; message: string; balance?: number; details?: any };
    const exchangeLower = exchange.toLowerCase().replace('.', '');

    switch (exchangeLower) {
      case 'binance': {
        if (!session.binance_api_key_encrypted || !session.binance_iv) {
          result = { success: false, message: 'Binance credentials not configured' };
          break;
        }

        const apiKey = await decrypt(session.binance_api_key_encrypted, session.binance_iv);
        const apiSecret = await decrypt(session.binance_api_secret_encrypted, session.binance_iv);

        const timestamp = Date.now();
        const queryString = `timestamp=${timestamp}`;
        
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
          // Calculate total USDT balance
          const usdtBalance = data.balances?.find((b: any) => b.asset === 'USDT');
          const totalBalance = parseFloat(usdtBalance?.free || '0') + parseFloat(usdtBalance?.locked || '0');
          
          result = { 
            success: true, 
            message: 'Binance connection successful',
            balance: totalBalance,
            details: { 
              canTrade: data.canTrade,
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
        if (!session.kraken_api_key_encrypted || !session.kraken_iv) {
          result = { success: false, message: 'Kraken credentials not configured' };
          break;
        }

        const apiKey = await decrypt(session.kraken_api_key_encrypted, session.kraken_iv);
        const apiSecret = await decrypt(session.kraken_api_secret_encrypted, session.kraken_iv);

        const nonce = Date.now() * 1000;
        const postData = `nonce=${nonce}`;
        const path = '/0/private/Balance';
        
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
        const signatureBuf = await crypto.subtle.sign('HMAC', key, message);
        const signatureB64 = btoa(String.fromCharCode(...new Uint8Array(signatureBuf)));

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
          const zusd = parseFloat(data.result?.ZUSD || '0');
          result = { 
            success: true, 
            message: 'Kraken connection successful',
            balance: zusd,
            details: { balanceCount: Object.keys(data.result || {}).length }
          };
        }
        break;
      }

      case 'alpaca': {
        if (!session.alpaca_api_key_encrypted || !session.alpaca_iv) {
          result = { success: false, message: 'Alpaca credentials not configured' };
          break;
        }

        const apiKey = await decrypt(session.alpaca_api_key_encrypted, session.alpaca_iv);
        const apiSecret = await decrypt(session.alpaca_secret_key_encrypted, session.alpaca_iv);

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
            balance: parseFloat(data.portfolio_value || '0'),
            details: { 
              status: data.status,
              tradingBlocked: data.trading_blocked
            }
          };
        } else {
          result = { success: false, message: 'Alpaca: Invalid credentials' };
        }
        break;
      }

      case 'capitalcom': {
        if (!session.capital_api_key_encrypted || !session.capital_iv) {
          result = { success: false, message: 'Capital.com credentials not configured' };
          break;
        }

        const apiKey = await decrypt(session.capital_api_key_encrypted, session.capital_iv);
        const identifier = await decrypt(session.capital_identifier_encrypted, session.capital_iv);
        const password = await decrypt(session.capital_password_encrypted, session.capital_iv);

        const response = await fetch('https://api-capital.backend-capital.com/api/v1/session', {
          method: 'POST',
          headers: {
            'X-CAP-API-KEY': apiKey,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ identifier, password })
        });

        if (response.ok) {
          result = { 
            success: true, 
            message: 'Capital.com connection successful',
            balance: 0
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
