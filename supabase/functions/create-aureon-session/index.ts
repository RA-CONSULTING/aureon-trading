import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

async function encryptCredential(value: string, cryptoKey: CryptoKey, iv: Uint8Array): Promise<string> {
  const encoder = new TextEncoder();
  const encrypted = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv: iv as unknown as BufferSource },
    cryptoKey,
    encoder.encode(value)
  );
  return btoa(String.fromCharCode(...new Uint8Array(encrypted)));
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  console.log('[create-aureon-session] Request received');

  try {
    const body = await req.json();
    const { 
      userId, 
      // Binance (required)
      apiKey, 
      apiSecret,
      // Kraken (optional)
      krakenApiKey,
      krakenApiSecret,
      // Alpaca (optional)
      alpacaApiKey,
      alpacaSecretKey,
      // Capital.com (optional)
      capitalApiKey,
      capitalPassword,
      capitalIdentifier
    } = body;

    console.log('[create-aureon-session] Processing for userId:', userId);

    if (!userId) {
      console.error('[create-aureon-session] Missing userId');
      return new Response(
        JSON.stringify({ error: 'Missing userId' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    const supabaseUrl = Deno.env.get('SUPABASE_URL');
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
    const supabaseAnonKey = Deno.env.get('SUPABASE_ANON_KEY');
    const encryptionKey = Deno.env.get('MASTER_ENCRYPTION_KEY') || 'aureon-default-key-32chars!!';

    if (!supabaseUrl || !supabaseServiceKey || !supabaseAnonKey) {
      console.error('[create-aureon-session] Missing env vars');
      return new Response(
        JSON.stringify({ error: 'Server configuration error' }),
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // === SECURITY: Verify the JWT token matches the userId ===
    const authHeader = req.headers.get('Authorization');
    const token = authHeader?.replace('Bearer ', '');

    if (!token) {
      console.error('[create-aureon-session] Missing authorization token');
      return new Response(
        JSON.stringify({ error: 'Unauthorized' }),
        { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    const anonSupabase = createClient(supabaseUrl, supabaseAnonKey);
    const { data: { user }, error: authError } = await anonSupabase.auth.getUser(token);

    if (authError || !user) {
      console.error('[create-aureon-session] Invalid token:', authError?.message);
      return new Response(
        JSON.stringify({ error: 'Unauthorized' }),
        { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    if (user.id !== userId) {
      console.error('[create-aureon-session] User ID mismatch');
      return new Response(
        JSON.stringify({ error: 'Unauthorized: user mismatch' }),
        { status: 403, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    console.log('[create-aureon-session] User verified:', user.id);

    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    // Prepare crypto key for encryption
    const encoder = new TextEncoder();
    const keyData = encoder.encode(encryptionKey.padEnd(32, '0').slice(0, 32));
    const cryptoKey = await crypto.subtle.importKey(
      'raw',
      keyData,
      { name: 'AES-GCM' },
      false,
      ['encrypt']
    );

    const sessionData: Record<string, any> = {
      user_id: userId,
      payment_completed: false,
      gas_tank_balance: 100,
      trading_mode: 'paper',
      is_trading_active: false
    };

    // Encrypt Binance credentials (required)
    if (apiKey && apiSecret) {
      console.log('[create-aureon-session] Encrypting Binance credentials...');
      const binanceIv = crypto.getRandomValues(new Uint8Array(12));
      sessionData.binance_api_key_encrypted = await encryptCredential(apiKey, cryptoKey, binanceIv);
      sessionData.binance_api_secret_encrypted = await encryptCredential(apiSecret, cryptoKey, binanceIv);
      sessionData.binance_iv = btoa(String.fromCharCode(...binanceIv));
    }

    // Encrypt Kraken credentials (optional)
    if (krakenApiKey && krakenApiSecret) {
      console.log('[create-aureon-session] Encrypting Kraken credentials...');
      const krakenIv = crypto.getRandomValues(new Uint8Array(12));
      sessionData.kraken_api_key_encrypted = await encryptCredential(krakenApiKey, cryptoKey, krakenIv);
      sessionData.kraken_api_secret_encrypted = await encryptCredential(krakenApiSecret, cryptoKey, krakenIv);
      sessionData.kraken_iv = btoa(String.fromCharCode(...krakenIv));
    }

    // Encrypt Alpaca credentials (optional)
    if (alpacaApiKey && alpacaSecretKey) {
      console.log('[create-aureon-session] Encrypting Alpaca credentials...');
      const alpacaIv = crypto.getRandomValues(new Uint8Array(12));
      sessionData.alpaca_api_key_encrypted = await encryptCredential(alpacaApiKey, cryptoKey, alpacaIv);
      sessionData.alpaca_secret_key_encrypted = await encryptCredential(alpacaSecretKey, cryptoKey, alpacaIv);
      sessionData.alpaca_iv = btoa(String.fromCharCode(...alpacaIv));
    }

    // Encrypt Capital.com credentials (optional)
    if (capitalApiKey && capitalPassword && capitalIdentifier) {
      console.log('[create-aureon-session] Encrypting Capital.com credentials...');
      const capitalIv = crypto.getRandomValues(new Uint8Array(12));
      sessionData.capital_api_key_encrypted = await encryptCredential(capitalApiKey, cryptoKey, capitalIv);
      sessionData.capital_password_encrypted = await encryptCredential(capitalPassword, cryptoKey, capitalIv);
      sessionData.capital_identifier_encrypted = await encryptCredential(capitalIdentifier, cryptoKey, capitalIv);
      sessionData.capital_iv = btoa(String.fromCharCode(...capitalIv));
    }

    console.log('[create-aureon-session] Upserting session...');

    const { data, error } = await supabase
      .from('aureon_user_sessions')
      .upsert(sessionData, { onConflict: 'user_id' })
      .select()
      .single();

    if (error) {
      console.error('[create-aureon-session] Database error:', error);
      return new Response(
        JSON.stringify({ error: 'Session creation failed. Please try again.' }),
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    console.log('[create-aureon-session] Session created successfully');

    return new Response(
      JSON.stringify({ success: true, sessionId: data?.id }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    console.error('[create-aureon-session] Unexpected error:', error);
    return new Response(
      JSON.stringify({ error: 'An unexpected error occurred. Please try again.' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});