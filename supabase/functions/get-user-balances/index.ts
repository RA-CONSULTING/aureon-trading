import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

async function decryptCredential(encrypted: string, cryptoKey: CryptoKey, iv: Uint8Array): Promise<string> {
  const encryptedBytes = Uint8Array.from(atob(encrypted), c => c.charCodeAt(0));
  const decrypted = await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv: iv as unknown as BufferSource },
    cryptoKey,
    encryptedBytes
  );
  return new TextDecoder().decode(decrypted);
}

interface ExchangeBalance {
  exchange: string;
  connected: boolean;
  assets: Array<{ asset: string; free: number; locked: number; usdValue: number }>;
  totalUsd: number;
  error?: string;
}

async function fetchBinanceBalances(apiKey: string, apiSecret: string): Promise<ExchangeBalance> {
  try {
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
      { headers: { 'X-MBX-APIKEY': apiKey } }
    );

    if (!response.ok) {
      throw new Error(`Binance API error: ${response.status}`);
    }

    const data = await response.json();
    
    // Get prices for USD conversion
    const pricesRes = await fetch('https://api.binance.com/api/v3/ticker/price');
    const prices = await pricesRes.json();
    const priceMap: Record<string, number> = {};
    prices.forEach((p: { symbol: string; price: string }) => {
      priceMap[p.symbol] = parseFloat(p.price);
    });

    const assets: ExchangeBalance['assets'] = [];
    let totalUsd = 0;

    for (const bal of data.balances) {
      const free = parseFloat(bal.free);
      const locked = parseFloat(bal.locked);
      if (free > 0 || locked > 0) {
        let usdValue = 0;
        if (bal.asset === 'USDT' || bal.asset === 'USDC' || bal.asset === 'BUSD') {
          usdValue = free + locked;
        } else if (priceMap[`${bal.asset}USDT`]) {
          usdValue = (free + locked) * priceMap[`${bal.asset}USDT`];
        } else if (priceMap[`${bal.asset}BUSD`]) {
          usdValue = (free + locked) * priceMap[`${bal.asset}BUSD`];
        }
        assets.push({ asset: bal.asset, free, locked, usdValue });
        totalUsd += usdValue;
      }
    }

    return { exchange: 'binance', connected: true, assets, totalUsd };
  } catch (error) {
    console.error('[get-user-balances] Binance error:', error);
    return { exchange: 'binance', connected: false, assets: [], totalUsd: 0, error: String(error) };
  }
}

async function fetchKrakenBalances(apiKey: string, apiSecret: string): Promise<ExchangeBalance> {
  try {
    const nonce = Date.now() * 1000;
    const path = '/0/private/Balance';
    const postData = `nonce=${nonce}`;
    
    const encoder = new TextEncoder();
    const secretDecoded = Uint8Array.from(atob(apiSecret), c => c.charCodeAt(0));
    
    const sha256Hash = await crypto.subtle.digest('SHA-256', encoder.encode(nonce + postData));
    const message = new Uint8Array([...encoder.encode(path), ...new Uint8Array(sha256Hash)]);
    
    const hmacKey = await crypto.subtle.importKey('raw', secretDecoded, { name: 'HMAC', hash: 'SHA-512' }, false, ['sign']);
    const signature = await crypto.subtle.sign('HMAC', hmacKey, message);
    const signatureB64 = btoa(String.fromCharCode(...new Uint8Array(signature)));

    const response = await fetch(`https://api.kraken.com${path}`, {
      method: 'POST',
      headers: {
        'API-Key': apiKey,
        'API-Sign': signatureB64,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: postData,
    });

    const data = await response.json();
    if (data.error && data.error.length > 0) {
      throw new Error(data.error[0]);
    }

    const assets: ExchangeBalance['assets'] = [];
    let totalUsd = 0;

    for (const [asset, balance] of Object.entries(data.result || {})) {
      const amount = parseFloat(balance as string);
      if (amount > 0) {
        // Simplified USD conversion (Kraken uses different asset names)
        let usdValue = 0;
        if (asset === 'ZUSD' || asset === 'USD') {
          usdValue = amount;
        } else {
          usdValue = amount * 1; // Would need ticker call for accurate conversion
        }
        assets.push({ asset, free: amount, locked: 0, usdValue });
        totalUsd += usdValue;
      }
    }

    return { exchange: 'kraken', connected: true, assets, totalUsd };
  } catch (error) {
    console.error('[get-user-balances] Kraken error:', error);
    return { exchange: 'kraken', connected: false, assets: [], totalUsd: 0, error: String(error) };
  }
}

async function fetchAlpacaBalances(apiKey: string, secretKey: string): Promise<ExchangeBalance> {
  try {
    const response = await fetch('https://paper-api.alpaca.markets/v2/account', {
      headers: {
        'APCA-API-KEY-ID': apiKey,
        'APCA-API-SECRET-KEY': secretKey,
      },
    });

    if (!response.ok) {
      throw new Error(`Alpaca API error: ${response.status}`);
    }

    const data = await response.json();
    const equity = parseFloat(data.equity || '0');
    const cash = parseFloat(data.cash || '0');

    return {
      exchange: 'alpaca',
      connected: true,
      assets: [
        { asset: 'USD', free: cash, locked: equity - cash, usdValue: equity }
      ],
      totalUsd: equity
    };
  } catch (error) {
    console.error('[get-user-balances] Alpaca error:', error);
    return { exchange: 'alpaca', connected: false, assets: [], totalUsd: 0, error: String(error) };
  }
}

async function fetchCapitalBalances(apiKey: string, password: string, identifier: string): Promise<ExchangeBalance> {
  try {
    // Create session
    const sessionRes = await fetch('https://api-capital.backend-capital.com/api/v1/session', {
      method: 'POST',
      headers: {
        'X-CAP-API-KEY': apiKey,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ identifier, password }),
    });

    if (!sessionRes.ok) {
      throw new Error(`Capital.com auth failed: ${sessionRes.status}`);
    }

    const cst = sessionRes.headers.get('CST');
    const securityToken = sessionRes.headers.get('X-SECURITY-TOKEN');

    if (!cst || !securityToken) {
      throw new Error('Missing auth tokens');
    }

    // Get accounts
    const accountsRes = await fetch('https://api-capital.backend-capital.com/api/v1/accounts', {
      headers: {
        'X-CAP-API-KEY': apiKey,
        'CST': cst,
        'X-SECURITY-TOKEN': securityToken,
      },
    });

    const accountsData = await accountsRes.json();
    const accounts = accountsData.accounts || [];
    
    let totalUsd = 0;
    const assets: ExchangeBalance['assets'] = [];

    for (const acc of accounts) {
      const balance = parseFloat(acc.balance?.balance || '0');
      assets.push({
        asset: acc.currency || 'USD',
        free: balance,
        locked: 0,
        usdValue: balance // Simplified, would need conversion
      });
      totalUsd += balance;
    }

    return { exchange: 'capital', connected: true, assets, totalUsd };
  } catch (error) {
    console.error('[get-user-balances] Capital.com error:', error);
    return { exchange: 'capital', connected: false, assets: [], totalUsd: 0, error: String(error) };
  }
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  console.log('[get-user-balances] Request received');

  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseAnonKey = Deno.env.get('SUPABASE_ANON_KEY')!;
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;

    // Verify user
    const authHeader = req.headers.get('Authorization');
    const token = authHeader?.replace('Bearer ', '');

    if (!token) {
      return new Response(
        JSON.stringify({ error: 'Unauthorized' }),
        { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    const anonSupabase = createClient(supabaseUrl, supabaseAnonKey);
    const { data: { user }, error: authError } = await anonSupabase.auth.getUser(token);

    if (authError || !user) {
      return new Response(
        JSON.stringify({ error: 'Unauthorized' }),
        { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    console.log('[get-user-balances] User verified:', user.id);

    // Get user's credentials
    const supabase = createClient(supabaseUrl, supabaseServiceKey);
    const { data: session, error: sessionError } = await supabase
      .from('aureon_user_sessions')
      .select('*')
      .eq('user_id', user.id)
      .single();

    if (sessionError || !session) {
      return new Response(
        JSON.stringify({ error: 'No session found' }),
        { status: 404, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // Prepare decryption key - must match encryption key format from update-user-credentials
    const masterKeyBase64 = Deno.env.get('MASTER_ENCRYPTION_KEY');
    if (!masterKeyBase64) {
      console.error('[get-user-balances] MASTER_ENCRYPTION_KEY not configured');
      return new Response(
        JSON.stringify({ error: 'Encryption key not configured' }),
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }
    
    const keyBytes = Uint8Array.from(atob(masterKeyBase64), c => c.charCodeAt(0));
    const cryptoKey = await crypto.subtle.importKey(
      'raw',
      keyBytes,
      { name: 'AES-GCM', length: 256 },
      false,
      ['decrypt']
    );

    const balances: ExchangeBalance[] = [];
    const fetchPromises: Promise<ExchangeBalance>[] = [];

    // Fetch Binance balances
    if (session.binance_api_key_encrypted && session.binance_api_secret_encrypted && session.binance_iv) {
      const iv = Uint8Array.from(atob(session.binance_iv), c => c.charCodeAt(0));
      const apiKey = await decryptCredential(session.binance_api_key_encrypted, cryptoKey, iv);
      const apiSecret = await decryptCredential(session.binance_api_secret_encrypted, cryptoKey, iv);
      fetchPromises.push(fetchBinanceBalances(apiKey, apiSecret));
    } else {
      balances.push({ exchange: 'binance', connected: false, assets: [], totalUsd: 0 });
    }

    // Fetch Kraken balances
    if (session.kraken_api_key_encrypted && session.kraken_api_secret_encrypted && session.kraken_iv) {
      const iv = Uint8Array.from(atob(session.kraken_iv), c => c.charCodeAt(0));
      const apiKey = await decryptCredential(session.kraken_api_key_encrypted, cryptoKey, iv);
      const apiSecret = await decryptCredential(session.kraken_api_secret_encrypted, cryptoKey, iv);
      fetchPromises.push(fetchKrakenBalances(apiKey, apiSecret));
    } else {
      balances.push({ exchange: 'kraken', connected: false, assets: [], totalUsd: 0 });
    }

    // Fetch Alpaca balances
    if (session.alpaca_api_key_encrypted && session.alpaca_secret_key_encrypted && session.alpaca_iv) {
      const iv = Uint8Array.from(atob(session.alpaca_iv), c => c.charCodeAt(0));
      const apiKey = await decryptCredential(session.alpaca_api_key_encrypted, cryptoKey, iv);
      const secretKey = await decryptCredential(session.alpaca_secret_key_encrypted, cryptoKey, iv);
      fetchPromises.push(fetchAlpacaBalances(apiKey, secretKey));
    } else {
      balances.push({ exchange: 'alpaca', connected: false, assets: [], totalUsd: 0 });
    }

    // Fetch Capital.com balances
    if (session.capital_api_key_encrypted && session.capital_password_encrypted && session.capital_identifier_encrypted && session.capital_iv) {
      const iv = Uint8Array.from(atob(session.capital_iv), c => c.charCodeAt(0));
      const apiKey = await decryptCredential(session.capital_api_key_encrypted, cryptoKey, iv);
      const password = await decryptCredential(session.capital_password_encrypted, cryptoKey, iv);
      const identifier = await decryptCredential(session.capital_identifier_encrypted, cryptoKey, iv);
      fetchPromises.push(fetchCapitalBalances(apiKey, password, identifier));
    } else {
      balances.push({ exchange: 'capital', connected: false, assets: [], totalUsd: 0 });
    }

    // Wait for all fetches
    const fetchedBalances = await Promise.all(fetchPromises);
    balances.push(...fetchedBalances);

    // Calculate totals
    const totalEquityUsd = balances.reduce((sum, b) => sum + b.totalUsd, 0);
    const connectedExchanges = balances.filter(b => b.connected).map(b => b.exchange);

    console.log('[get-user-balances] Fetched balances from', connectedExchanges.length, 'exchanges, total:', totalEquityUsd);

    return new Response(
      JSON.stringify({
        success: true,
        balances,
        totalEquityUsd,
        connectedExchanges
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    console.error('[get-user-balances] Error:', error);
    return new Response(
      JSON.stringify({ error: 'Failed to fetch balances' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});