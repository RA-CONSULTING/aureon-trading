import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

// Rate limit configuration per exchange (in milliseconds)
const RATE_LIMITS = {
  binance: 10000,    // 10 seconds between calls
  kraken: 120000,    // 2 MINUTES (Kraken is VERY strict - increase to avoid rate limit)
  alpaca: 15000,     // 15 seconds
  capital: 60000,    // 60 seconds (Capital.com is strict)
};

// Database-backed cache table name
const BALANCE_CACHE_TABLE = 'exchange_balance_cache';

interface CachedBalanceData {
  exchange: string;
  user_id: string;
  balance_data: ExchangeBalance;
  cached_at: string;
}

// Check database cache for exchange balance
async function getDbCachedBalance(
  supabase: any,
  userId: string,
  exchange: string
): Promise<{ data: ExchangeBalance | null; canFetch: boolean }> {
  try {
    const { data, error } = await supabase
      .from(BALANCE_CACHE_TABLE)
      .select('*')
      .eq('user_id', userId)
      .eq('exchange', exchange)
      .single();

    if (error || !data) {
      return { data: null, canFetch: true };
    }

    const cachedAt = new Date(data.cached_at).getTime();
    const elapsed = Date.now() - cachedAt;
    const rateLimit = RATE_LIMITS[exchange as keyof typeof RATE_LIMITS] || 30000;

    const balanceData = data.balance_data as ExchangeBalance | null;

    // If the cached payload is an error/offline result, avoid hammering the exchange.
    // We allow quicker retry for "Invalid nonce" (fixable), but respect strict backoff for rate limits.
    const isErrorPayload =
      !balanceData ||
      balanceData.connected === false ||
      !Array.isArray(balanceData.assets);

    if (isErrorPayload) {
      const errorText = typeof balanceData?.error === 'string' ? balanceData.error : '';
      const isRateLimit = /rate limit exceeded/i.test(errorText);
      const isInvalidNonce = /invalid nonce/i.test(errorText);

      const backoffMs = isRateLimit ? rateLimit : isInvalidNonce ? 15000 : 60000;
      const canFetch = elapsed >= backoffMs;

      return {
        data:
          elapsed < 300000 && balanceData
            ? {
                ...balanceData,
                error: canFetch
                  ? balanceData.error
                  : `${balanceData.error || 'Cached error'} (retry in ${Math.max(0, Math.ceil((backoffMs - elapsed) / 1000))}s)`,
              }
            : null,
        canFetch,
      };
    }

    // Can fetch if rate limit has passed
    const canFetch = elapsed >= rateLimit;

    // Return cached data if not too stale (5 minutes max)
    if (elapsed < 300000 && balanceData) {
      return {
        data: {
          ...balanceData,
          error: canFetch ? undefined : `Cached ${Math.round(elapsed / 1000)}s ago (rate limited)`,
        },
        canFetch,
      };
    }

    return { data: null, canFetch: true };
  } catch {
    return { data: null, canFetch: true };
  }
}

// Save balance to database cache
async function setDbCachedBalance(
  supabase: any, 
  userId: string, 
  exchange: string, 
  balanceData: ExchangeBalance
): Promise<void> {
  try {
    await supabase
      .from(BALANCE_CACHE_TABLE)
      .upsert({
        user_id: userId,
        exchange: exchange,
        balance_data: balanceData,
        cached_at: new Date().toISOString()
      }, { 
        onConflict: 'user_id,exchange' 
      });
  } catch (e) {
    console.error(`[get-user-balances] Failed to cache ${exchange} balance:`, e);
  }
}

// Move interface before cache functions that reference it
interface ExchangeBalance {
  exchange: string;
  connected: boolean;
  assets: Array<{ asset: string; free: number; locked: number; usdValue: number }>;
  totalUsd: number;
  error?: string;
}

async function decryptCredential(
  encrypted: string, 
  cryptoKey: CryptoKey, 
  legacyCryptoKey: CryptoKey,
  iv: Uint8Array
): Promise<string> {
  const encryptedBytes = Uint8Array.from(atob(encrypted), c => c.charCodeAt(0));
  
  // Try new base64 key first, then fall back to legacy text-padded key
  try {
    const decrypted = await crypto.subtle.decrypt(
      { name: 'AES-GCM', iv: iv as unknown as BufferSource },
      cryptoKey,
      encryptedBytes
    );
    return new TextDecoder().decode(decrypted);
  } catch {
    // Fall back to legacy key
    const decrypted = await crypto.subtle.decrypt(
      { name: 'AES-GCM', iv: iv as unknown as BufferSource },
      legacyCryptoKey,
      encryptedBytes
    );
    return new TextDecoder().decode(decrypted);
  }
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

// Kraken asset name mapping - matches Python kraken_client.py
const KRAKEN_ASSET_MAP: Record<string, string> = {
  'XXBT': 'BTC',
  'XBT': 'BTC',
  'XETH': 'ETH',
  'XXLM': 'XLM',
  'XLTC': 'LTC',
  'XXRP': 'XRP',
  'XXDG': 'DOGE',
  'XZEC': 'ZEC',
  'XREP': 'REP',
  'XETC': 'ETC',
  'XMLN': 'MLN',
  'XXMR': 'XMR',
  'ZUSD': 'USD',
  'ZEUR': 'EUR',
  'ZGBP': 'GBP',
  'ZCAD': 'CAD',
  'ZJPY': 'JPY',
  'ZAUD': 'AUD',
  'USDT': 'USDT',
  'USDC': 'USDC',
  'DAI': 'DAI',
  'DOT': 'DOT',
  'SOL': 'SOL',
  'ADA': 'ADA',
  'MATIC': 'MATIC',
  'ATOM': 'ATOM',
  'LINK': 'LINK',
  'UNI': 'UNI',
  'AVAX': 'AVAX',
  'SHIB': 'SHIB',
  'TRX': 'TRX',
  'NEAR': 'NEAR',
  'APE': 'APE',
  'SAND': 'SAND',
  'MANA': 'MANA',
  'CRV': 'CRV',
  'AAVE': 'AAVE',
  'FTM': 'FTM',
  'GRT': 'GRT',
  'ALGO': 'ALGO',
  'XTZ': 'XTZ',
  'EOS': 'EOS',
  'FLOW': 'FLOW',
  'AXS': 'AXS',
  'CHZ': 'CHZ',
  'ENJ': 'ENJ',
  'BAT': 'BAT',
  'COMP': 'COMP',
  'MKR': 'MKR',
  'SNX': 'SNX',
  'YFI': 'YFI',
  'SUSHI': 'SUSHI',
  '1INCH': '1INCH',
  'OCEAN': 'OCEAN',
  'STORJ': 'STORJ',
  'OMG': 'OMG',
  'ZRX': 'ZRX',
  'KNC': 'KNC',
  'KEEP': 'KEEP',
  'ANT': 'ANT',
  'REN': 'REN',
  'LRC': 'LRC',
  'KAVA': 'KAVA',
  'WAVES': 'WAVES',
  'ICX': 'ICX',
  'NANO': 'NANO',
  'OMG.S': 'OMG',
  'SC': 'SC',
  'QTUM': 'QTUM',
  'LSK': 'LSK',
  'BABY': 'BABY',
  'BABY.S': 'BABY',
};

function cleanKrakenAsset(krakenName: string): string {
  // First check direct mapping
  if (KRAKEN_ASSET_MAP[krakenName]) {
    return KRAKEN_ASSET_MAP[krakenName];
  }
  
  // Handle staked assets (e.g., ETH2.S, DOT.S)
  const unstaked = krakenName.replace(/\.S$/, '');
  if (KRAKEN_ASSET_MAP[unstaked]) {
    return KRAKEN_ASSET_MAP[unstaked];
  }
  
  // Legacy prefix stripping for unknown assets
  let cleaned = krakenName;
  
  // Handle XX prefix (e.g., XXBT -> BTC is already mapped, but XXABC -> ABC)
  if (cleaned.startsWith('XX') && cleaned.length > 2) {
    cleaned = cleaned.slice(2);
  }
  // Handle single X prefix but preserve XRP, XLM, XTZ, XDG (DOGE)
  else if (cleaned.startsWith('X') && cleaned.length > 1 && 
           !['XRP', 'XLM', 'XTZ', 'XDG'].includes(cleaned)) {
    cleaned = cleaned.slice(1);
  }
  // Handle Z prefix for fiat (ZUSD, ZEUR etc) - already mapped above
  else if (cleaned.startsWith('Z') && cleaned.length > 1) {
    cleaned = cleaned.slice(1);
  }
  
  return cleaned;
}

async function fetchKrakenBalances(apiKey: string, apiSecret: string): Promise<ExchangeBalance> {
  try {
    // Kraken requires a strictly increasing integer nonce.
    // Using nanosecond-scale BigInt reduces collision risk under concurrent calls.
    const nonce = (BigInt(Date.now()) * 1000000n).toString();
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
    console.log('[get-user-balances] Kraken raw balances:', JSON.stringify(data.result));
    
    if (data.error && data.error.length > 0) {
      throw new Error(data.error[0]);
    }

    // Fetch ALL Kraken ticker prices for USD conversion
    const priceMap: Record<string, number> = {};
    try {
      const tickerRes = await fetch('https://api.kraken.com/0/public/Ticker');
      const tickerData = await tickerRes.json();
      
      if (tickerData.result) {
        for (const [pair, ticker] of Object.entries(tickerData.result)) {
          const t = ticker as any;
          const price = parseFloat(t.c?.[0] || '0');
          
          // Store USD pairs for conversion
          if (pair.includes('USD')) {
            // Extract base asset - handle various Kraken pair formats
            // XXBTZUSD, XETHZUSD, SOLUSD, ADAUSD, etc.
            let base = pair;
            
            // Remove USD suffix variants
            base = base.replace(/ZUSD$/, '').replace(/USD$/, '');
            
            // Clean the base using our mapping
            const cleanBase = cleanKrakenAsset(base);
            
            priceMap[cleanBase] = price;
            // Also store with original Kraken name for fallback
            priceMap[base] = price;
          }
        }
      }
      console.log('[get-user-balances] Kraken prices loaded:', Object.keys(priceMap).slice(0, 20).join(', '), '...');
    } catch (priceError) {
      console.warn('[get-user-balances] Failed to fetch Kraken prices:', priceError);
    }

    const assets: ExchangeBalance['assets'] = [];
    let totalUsd = 0;

    // Process ALL balances from Kraken
    for (const [rawAsset, balance] of Object.entries(data.result || {})) {
      const amount = parseFloat(balance as string);
      
      if (amount > 0) {
        // Use proper asset mapping
        const displayAsset = cleanKrakenAsset(rawAsset);
        let usdValue = 0;
        
        // Handle fiat and stablecoins
        if (displayAsset === 'USD' || displayAsset === 'USDT' || displayAsset === 'USDC' || displayAsset === 'DAI') {
          usdValue = amount;
        } else if (displayAsset === 'EUR') {
          usdValue = amount * 1.05; // EUR to USD approx
        } else if (displayAsset === 'GBP') {
          usdValue = amount * 1.27; // GBP to USD approx
        } else if (displayAsset === 'CAD') {
          usdValue = amount * 0.74; // CAD to USD approx
        } else if (displayAsset === 'AUD') {
          usdValue = amount * 0.65; // AUD to USD approx
        } else if (displayAsset === 'JPY') {
          usdValue = amount * 0.0067; // JPY to USD approx
        } else {
          // Look up price - try display name first, then raw name
          const price = priceMap[displayAsset] || priceMap[rawAsset] || 0;
          usdValue = amount * price;
        }
        
        assets.push({ asset: displayAsset, free: amount, locked: 0, usdValue });
        totalUsd += usdValue;
        console.log(`[get-user-balances] Kraken: ${rawAsset} -> ${displayAsset} = ${amount}, USD: $${usdValue.toFixed(2)}`);
      }
    }

    console.log(`[get-user-balances] Kraken total: $${totalUsd.toFixed(2)} from ${assets.length} assets`);
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

    // Use consistent text-padded encryption key (matches create-aureon-session and update-user-credentials)
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
    
    // Legacy key is same as primary now - unified encryption
    const legacyCryptoKey = cryptoKey;

    const balances: ExchangeBalance[] = [];
    const fetchPromises: Promise<ExchangeBalance>[] = [];

    const decodeIvFromB64 = (ivB64: string) => Uint8Array.from(atob(ivB64), c => c.charCodeAt(0));

    // === Use USER-SAVED credentials (never global/shared secrets) ===
    const userCreds = {
      binance: { apiKey: null as string | null, apiSecret: null as string | null },
      kraken: { apiKey: null as string | null, apiSecret: null as string | null },
      alpaca: { apiKey: null as string | null, apiSecret: null as string | null },
      capital: { apiKey: null as string | null, password: null as string | null, identifier: null as string | null },
    };

    // Binance
    if (session.binance_api_key_encrypted && session.binance_api_secret_encrypted && session.binance_iv) {
      const iv = decodeIvFromB64(session.binance_iv);
      userCreds.binance.apiKey = await decryptCredential(session.binance_api_key_encrypted, cryptoKey, legacyCryptoKey, iv);
      userCreds.binance.apiSecret = await decryptCredential(session.binance_api_secret_encrypted, cryptoKey, legacyCryptoKey, iv);
    }

    // Kraken
    if (session.kraken_api_key_encrypted && session.kraken_api_secret_encrypted && session.kraken_iv) {
      const iv = decodeIvFromB64(session.kraken_iv);
      userCreds.kraken.apiKey = await decryptCredential(session.kraken_api_key_encrypted, cryptoKey, legacyCryptoKey, iv);
      userCreds.kraken.apiSecret = await decryptCredential(session.kraken_api_secret_encrypted, cryptoKey, legacyCryptoKey, iv);
    }

    // Alpaca
    if (session.alpaca_api_key_encrypted && session.alpaca_secret_key_encrypted && session.alpaca_iv) {
      const iv = decodeIvFromB64(session.alpaca_iv);
      userCreds.alpaca.apiKey = await decryptCredential(session.alpaca_api_key_encrypted, cryptoKey, legacyCryptoKey, iv);
      userCreds.alpaca.apiSecret = await decryptCredential(session.alpaca_secret_key_encrypted, cryptoKey, legacyCryptoKey, iv);
    }

    // Capital.com
    if (session.capital_api_key_encrypted && session.capital_password_encrypted && session.capital_identifier_encrypted && session.capital_iv) {
      const iv = decodeIvFromB64(session.capital_iv);
      userCreds.capital.apiKey = await decryptCredential(session.capital_api_key_encrypted, cryptoKey, legacyCryptoKey, iv);
      userCreds.capital.password = await decryptCredential(session.capital_password_encrypted, cryptoKey, legacyCryptoKey, iv);
      userCreds.capital.identifier = await decryptCredential(session.capital_identifier_encrypted, cryptoKey, legacyCryptoKey, iv);
    }

    console.log('[get-user-balances] Using user credentials:', {
      binance: !!userCreds.binance.apiKey,
      kraken: !!userCreds.kraken.apiKey,
      alpaca: !!userCreds.alpaca.apiKey,
      capital: !!userCreds.capital.apiKey,
    });

    // Fetch Binance balances with database-backed rate limiting
    if (userCreds.binance.apiKey && userCreds.binance.apiSecret) {
      const binanceCache = await getDbCachedBalance(supabase, user.id, 'binance');
      if (binanceCache.canFetch) {
        fetchPromises.push(
          fetchBinanceBalances(userCreds.binance.apiKey, userCreds.binance.apiSecret)
            .then(async (result) => { 
              await setDbCachedBalance(supabase, user.id, 'binance', result); 
              return result; 
            })
        );
      } else if (binanceCache.data) {
        balances.push(binanceCache.data);
      } else {
        balances.push({ exchange: 'binance', connected: false, assets: [], totalUsd: 0, error: 'Rate limited, no cache' });
      }
    } else {
      balances.push({ exchange: 'binance', connected: false, assets: [], totalUsd: 0, error: 'Not configured' });
    }

    // Fetch Kraken balances with database-backed rate limiting (2 MINUTES to avoid rate limit)
    if (userCreds.kraken.apiKey && userCreds.kraken.apiSecret) {
      const krakenCache = await getDbCachedBalance(supabase, user.id, 'kraken');
      if (krakenCache.canFetch) {
        console.log('[get-user-balances] Kraken: fetching fresh data');
        fetchPromises.push(
          fetchKrakenBalances(userCreds.kraken.apiKey, userCreds.kraken.apiSecret)
            .then(async (result) => { 
              await setDbCachedBalance(supabase, user.id, 'kraken', result); 
              return result; 
            })
        );
      } else if (krakenCache.data) {
        console.log('[get-user-balances] Kraken: using cached data (rate limited)');
        balances.push(krakenCache.data);
      } else {
        balances.push({ exchange: 'kraken', connected: false, assets: [], totalUsd: 0, error: 'Rate limited, no cache' });
      }
    } else {
      balances.push({ exchange: 'kraken', connected: false, assets: [], totalUsd: 0, error: 'Not configured' });
    }

    // Fetch Alpaca balances with database-backed rate limiting
    if (userCreds.alpaca.apiKey && userCreds.alpaca.apiSecret) {
      const alpacaCache = await getDbCachedBalance(supabase, user.id, 'alpaca');
      if (alpacaCache.canFetch) {
        fetchPromises.push(
          fetchAlpacaBalances(userCreds.alpaca.apiKey, userCreds.alpaca.apiSecret)
            .then(async (result) => { 
              await setDbCachedBalance(supabase, user.id, 'alpaca', result); 
              return result; 
            })
        );
      } else if (alpacaCache.data) {
        balances.push(alpacaCache.data);
      } else {
        balances.push({ exchange: 'alpaca', connected: false, assets: [], totalUsd: 0, error: 'Rate limited, no cache' });
      }
    } else {
      balances.push({ exchange: 'alpaca', connected: false, assets: [], totalUsd: 0, error: 'Not configured' });
    }

    // Fetch Capital.com balances with database-backed rate limiting (60s minimum)
    if (userCreds.capital.apiKey && userCreds.capital.password && userCreds.capital.identifier) {
      const capitalCache = await getDbCachedBalance(supabase, user.id, 'capital');
      if (capitalCache.canFetch) {
        fetchPromises.push(
          fetchCapitalBalances(userCreds.capital.apiKey, userCreds.capital.password, userCreds.capital.identifier)
            .then(async (result) => { 
              await setDbCachedBalance(supabase, user.id, 'capital', result); 
              return result; 
            })
        );
      } else if (capitalCache.data) {
        console.log('[get-user-balances] Capital.com: using cached data (rate limited)');
        balances.push(capitalCache.data);
      } else {
        balances.push({ exchange: 'capital', connected: false, assets: [], totalUsd: 0, error: 'Rate limited, no cache' });
      }
    } else {
      balances.push({ exchange: 'capital', connected: false, assets: [], totalUsd: 0, error: 'Not configured' });
    }

    // Wait for all fetches
    const fetchedBalances = await Promise.all(fetchPromises);
    balances.push(...fetchedBalances);

    // Calculate totals
    const totalEquityUsd = balances.reduce((sum, b) => sum + b.totalUsd, 0);
    const connectedExchanges = balances.filter(b => b.connected).map(b => b.exchange);

    console.log('[get-user-balances] Fetched balances from', connectedExchanges.length, 'exchanges, total:', totalEquityUsd);

    // CRITICAL: Update aureon_user_sessions with fetched balance so trading system can use it
    if (totalEquityUsd > 0) {
      const { error: updateError } = await supabase
        .from('aureon_user_sessions')
        .update({
          total_equity_usdt: totalEquityUsd,
          available_balance_usdt: totalEquityUsd, // Use total as available for now
          updated_at: new Date().toISOString()
        })
        .eq('user_id', user.id);
      
      if (updateError) {
        console.error('[get-user-balances] Failed to update session balance:', updateError);
      } else {
        console.log('[get-user-balances] Updated session balance to:', totalEquityUsd);
      }
    }

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