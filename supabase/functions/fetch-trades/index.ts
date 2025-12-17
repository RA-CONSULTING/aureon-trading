import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import { createHmac } from "https://deno.land/std@0.177.0/node/crypto.ts";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

function decodeIv(ivB64: string): Uint8Array {
  return Uint8Array.from(atob(ivB64), (c) => c.charCodeAt(0));
}

async function decryptCredential(encryptedB64: string, cryptoKey: CryptoKey, iv: Uint8Array): Promise<string> {
  const encryptedBytes = Uint8Array.from(atob(encryptedB64), (c) => c.charCodeAt(0));
  const decrypted = await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv: iv as unknown as BufferSource },
    cryptoKey,
    encryptedBytes
  );
  return new TextDecoder().decode(decrypted);
}

async function getCryptoKey(): Promise<CryptoKey> {
  // Must match create-aureon-session and update-user-credentials
  const encryptionKey = 'aureon-default-key-32chars!!';
  const encoder = new TextEncoder();
  const keyData = encoder.encode(encryptionKey.padEnd(32, '0').slice(0, 32));
  return crypto.subtle.importKey('raw', keyData, { name: 'AES-GCM' }, false, ['decrypt']);
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL') ?? '';
    const supabaseAnonKey = Deno.env.get('SUPABASE_ANON_KEY') ?? '';
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '';

    if (!supabaseUrl || !supabaseAnonKey || !supabaseServiceKey) {
      return new Response(JSON.stringify({ error: 'Server configuration error' }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    const supabaseClient = createClient(
      supabaseUrl,
      supabaseAnonKey,
      { global: { headers: { Authorization: req.headers.get('Authorization')! } } }
    );

    const { data: { user }, error: authError } = await supabaseClient.auth.getUser();
    if (authError || !user) {
      return new Response(JSON.stringify({ error: 'Unauthorized' }), {
        status: 401,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    const body = await req.json().catch(() => ({} as any));
    const symbolsRaw = Array.isArray(body?.symbols) ? (body.symbols as string[]) : undefined;
    const limitRaw = Number(body?.limit ?? 50);

    const DEFAULT_SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT', 'BNBUSDT', 'ADAUSDT', 'DOGEUSDT'];
    const EXCLUDED_ASSETS = new Set(['USDT', 'USDC', 'BUSD', 'TUSD', 'FDUSD', 'USDP', 'DAI', 'EUR', 'GBP', 'USD']);

    const normalizeSymbols = (input: string[]) =>
      Array.from(new Set((input || []).map((s) => String(s).toUpperCase().trim()))).filter(Boolean);

    async function deriveSymbolsFromBalances(maxSymbols = 25): Promise<string[]> {
      try {
        const timestamp = Date.now();
        const queryString = `timestamp=${timestamp}`;
        const signature = createHmac('sha256', apiSecret).update(queryString).digest('hex');

        const resp = await fetch(`https://api.binance.com/api/v3/account?${queryString}&signature=${signature}`, {
          headers: { 'X-MBX-APIKEY': apiKey },
        });

        if (!resp.ok) {
          const t = await resp.text();
          console.log('[fetch-trades] balance-based symbol discovery failed:', resp.status, t);
          return [];
        }

        const data = await resp.json();
        const assets: string[] = (data?.balances || [])
          .map((b: any) => ({ asset: String(b.asset || ''), total: Number(b.free || 0) + Number(b.locked || 0) }))
          .filter((b: any) => b.asset && b.total > 0)
          .map((b: any) => b.asset)
          .filter((a: string) => !EXCLUDED_ASSETS.has(a));

        // Prefer assets the user actually holds; map to common USDT pairs.
        // NOTE: Binance requires symbol param for /myTrades.
        const candidates = assets.slice(0, maxSymbols).map((a) => `${a}USDT`);
        return normalizeSymbols(candidates);
      } catch (e) {
        console.log('[fetch-trades] balance-based symbol discovery error:', e);
        return [];
      }
    }

    // If user didn't provide symbols (or they provided an empty list), auto-discover from balances.
    let symbols = symbolsRaw && symbolsRaw.length > 0 ? normalizeSymbols(symbolsRaw) : [];
    if (symbols.length === 0) {
      const discovered = await deriveSymbolsFromBalances();
      symbols = discovered.length > 0 ? discovered : DEFAULT_SYMBOLS;
    }

    const limit = Number.isFinite(limitRaw) ? Math.min(500, Math.max(1, limitRaw)) : 50;

    const uniqueSymbols = symbols;
    const perSymbolLimit = Math.min(50, Math.max(1, Math.ceil(limit / Math.max(1, uniqueSymbols.length))));

    // Load and decrypt THIS USER'S Binance credentials
    const service = createClient(supabaseUrl, supabaseServiceKey);
    const { data: session, error: sessionError } = await service
      .from('aureon_user_sessions')
      .select('binance_api_key_encrypted, binance_api_secret_encrypted, binance_iv')
      .eq('user_id', user.id)
      .single();

    if (sessionError || !session) {
      return new Response(JSON.stringify({ error: 'No trading session found. Please re-login.' }), {
        status: 404,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    if (!session.binance_api_key_encrypted || !session.binance_api_secret_encrypted || !session.binance_iv) {
      return new Response(JSON.stringify({ error: 'No Binance credentials saved. Add them in Settings → API Credentials.' }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    const cryptoKey = await getCryptoKey();
    const iv = decodeIv(session.binance_iv);
    const apiKey = await decryptCredential(session.binance_api_key_encrypted, cryptoKey, iv);
    const apiSecret = await decryptCredential(session.binance_api_secret_encrypted, cryptoKey, iv);

    console.log('[fetch-trades] Fetching trades for user:', user.id);
    console.log('[fetch-trades] Symbols:', uniqueSymbols);
    console.log('[fetch-trades] Per-symbol limit:', perSymbolLimit);

    // Fetch trades from multiple symbols
    const allTrades: any[] = [];
    
    for (const symbol of uniqueSymbols) {
      try {
        const timestamp = Date.now();
        const queryString = `symbol=${symbol}&limit=${perSymbolLimit}&timestamp=${timestamp}`;
        const signature = createHmac('sha256', apiSecret).update(queryString).digest('hex');

        const response = await fetch(
          `https://api.binance.com/api/v3/myTrades?${queryString}&signature=${signature}`,
          {
            headers: { 'X-MBX-APIKEY': apiKey },
          }
        );

        if (response.ok) {
          const trades = await response.json();
          console.log(`Found ${trades.length} trades for ${symbol}`);
          allTrades.push(...trades);
        } else {
          const errorText = await response.text();
          console.log(`No trades for ${symbol}: ${errorText}`);
        }
      } catch (err) {
        console.error(`Error fetching ${symbol}:`, err);
      }
    }

    console.log(`Total trades found: ${allTrades.length}`);
    
    // Sort by time descending
    const trades = allTrades.sort((a, b) => b.time - a.time).slice(0, limit);

    // Store new trades in database
    const tradeRecords = trades.map((t: any) => ({
      transaction_id: String(t.id),
      exchange: 'binance',
      symbol: t.symbol,
      side: t.isBuyer ? 'BUY' : 'SELL',
      price: parseFloat(t.price),
      quantity: parseFloat(t.qty),
      quote_qty: parseFloat(t.quoteQty),
      fee: parseFloat(t.commission),
      fee_asset: t.commissionAsset,
      timestamp: new Date(t.time).toISOString(),
      user_id: user.id,
    }));

    // Upsert trades (avoid duplicates)
    for (const record of tradeRecords) {
      await supabaseClient
        .from('trade_records')
        .upsert(record, { onConflict: 'transaction_id' })
        .select();
    }

    return new Response(JSON.stringify({ trades: tradeRecords, count: tradeRecords.length }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  } catch (error: unknown) {
    console.error('Error fetching trades:', error);
    const message = error instanceof Error ? error.message : 'Unknown error';
    return new Response(JSON.stringify({ error: message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
