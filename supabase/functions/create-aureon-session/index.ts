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
    const { userId, apiKey, apiSecret } = await req.json();

    if (!userId || !apiKey || !apiSecret) {
      return new Response(
        JSON.stringify({ error: 'Missing required fields' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const encryptionKey = Deno.env.get('MASTER_ENCRYPTION_KEY') || 'default-key-for-dev';

    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    // Simple encryption (in production use proper AES encryption)
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
    
    const encryptedApiKey = await crypto.subtle.encrypt(
      { name: 'AES-GCM', iv },
      cryptoKey,
      encoder.encode(apiKey)
    );
    
    const encryptedApiSecret = await crypto.subtle.encrypt(
      { name: 'AES-GCM', iv },
      cryptoKey,
      encoder.encode(apiSecret)
    );

    // Convert to base64
    const apiKeyEncrypted = btoa(String.fromCharCode(...new Uint8Array(encryptedApiKey)));
    const apiSecretEncrypted = btoa(String.fromCharCode(...new Uint8Array(encryptedApiSecret)));
    const ivBase64 = btoa(String.fromCharCode(...iv));

    // Create or update aureon_user_sessions
    const { error } = await supabase
      .from('aureon_user_sessions')
      .upsert({
        user_id: userId,
        binance_api_key_encrypted: apiKeyEncrypted,
        binance_api_secret_encrypted: apiSecretEncrypted,
        binance_iv: ivBase64,
        payment_completed: false,
        gas_tank_balance: 100,
        trading_mode: 'paper'
      }, {
        onConflict: 'user_id'
      });

    if (error) {
      console.error('Error creating session:', error);
      return new Response(
        JSON.stringify({ error: error.message }),
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    return new Response(
      JSON.stringify({ success: true }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    console.error('Error:', error);
    return new Response(
      JSON.stringify({ error: error instanceof Error ? error.message : 'Unknown error' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});