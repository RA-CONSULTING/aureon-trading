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

  console.log('[create-aureon-session] Request received');

  try {
    const body = await req.json();
    const { userId, apiKey, apiSecret } = body;

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
    const encryptionKey = Deno.env.get('MASTER_ENCRYPTION_KEY') || 'aureon-default-key-32chars!!';

    if (!supabaseUrl || !supabaseServiceKey) {
      console.error('[create-aureon-session] Missing env vars');
      return new Response(
        JSON.stringify({ error: 'Server configuration error' }),
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    let apiKeyEncrypted = null;
    let apiSecretEncrypted = null;
    let ivBase64 = null;

    // Only encrypt if API credentials are provided
    if (apiKey && apiSecret) {
      console.log('[create-aureon-session] Encrypting API credentials...');
      
      try {
        const encoder = new TextEncoder();
        const keyData = encoder.encode(encryptionKey.padEnd(32, '0').slice(0, 32));
        
        const cryptoKey = await crypto.subtle.importKey(
          'raw',
          keyData,
          { name: 'AES-GCM' },
          false,
          ['encrypt']
        );

        const iv = crypto.getRandomValues(new Uint8Array(12));
        
        const encryptedApiKeyBuffer = await crypto.subtle.encrypt(
          { name: 'AES-GCM', iv },
          cryptoKey,
          encoder.encode(apiKey)
        );
        
        const encryptedApiSecretBuffer = await crypto.subtle.encrypt(
          { name: 'AES-GCM', iv },
          cryptoKey,
          encoder.encode(apiSecret)
        );

        // Convert to base64
        apiKeyEncrypted = btoa(String.fromCharCode(...new Uint8Array(encryptedApiKeyBuffer)));
        apiSecretEncrypted = btoa(String.fromCharCode(...new Uint8Array(encryptedApiSecretBuffer)));
        ivBase64 = btoa(String.fromCharCode(...iv));
        
        console.log('[create-aureon-session] Encryption successful');
      } catch (encryptError) {
        console.error('[create-aureon-session] Encryption failed:', encryptError);
        // Continue without encryption - credentials won't be stored
      }
    }

    // Create or update aureon_user_sessions
    const sessionData: Record<string, any> = {
      user_id: userId,
      payment_completed: false,
      gas_tank_balance: 100,
      trading_mode: 'paper',
      is_trading_active: false
    };

    if (apiKeyEncrypted && apiSecretEncrypted && ivBase64) {
      sessionData.binance_api_key_encrypted = apiKeyEncrypted;
      sessionData.binance_api_secret_encrypted = apiSecretEncrypted;
      sessionData.binance_iv = ivBase64;
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
        JSON.stringify({ error: error.message, code: error.code }),
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
      JSON.stringify({ error: error instanceof Error ? error.message : 'Unknown error' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});