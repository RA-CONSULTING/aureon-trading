import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

async function encryptCredential(value: string, cryptoKey: CryptoKey, iv: Uint8Array): Promise<string> {
  const encoded = new TextEncoder().encode(value);
  const encrypted = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv: iv as unknown as BufferSource },
    cryptoKey,
    encoded
  );
  return btoa(String.fromCharCode(...new Uint8Array(encrypted)));
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseKey);

    // Get user from JWT
    const authHeader = req.headers.get('Authorization');
    if (!authHeader) {
      return new Response(JSON.stringify({ error: 'No authorization header' }), {
        status: 401,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    const token = authHeader.replace('Bearer ', '');
    const { data: { user }, error: authError } = await supabase.auth.getUser(token);
    
    if (authError || !user) {
      return new Response(JSON.stringify({ error: 'Invalid token' }), {
        status: 401,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    const body = await req.json();
    const {
      binanceApiKey,
      binanceApiSecret,
      krakenApiKey,
      krakenApiSecret,
      alpacaApiKey,
      alpacaSecretKey,
      capitalApiKey,
      capitalPassword,
      capitalIdentifier
    } = body;

    // Use consistent text-padded encryption key (same as create-aureon-session)
    const encryptionKey = 'aureon-default-key-32chars!!';
    const encoder = new TextEncoder();
    const keyData = encoder.encode(encryptionKey.padEnd(32, '0').slice(0, 32));
    
    const cryptoKey = await crypto.subtle.importKey(
      'raw',
      keyData,
      { name: 'AES-GCM' },
      false,
      ['encrypt']
    );

    // Build update object with only provided credentials
    const updateData: Record<string, any> = {
      updated_at: new Date().toISOString()
    };

    // Binance
    if (binanceApiKey && binanceApiSecret) {
      const binanceIv = crypto.getRandomValues(new Uint8Array(12));
      updateData.binance_api_key_encrypted = await encryptCredential(binanceApiKey, cryptoKey, binanceIv);
      updateData.binance_api_secret_encrypted = await encryptCredential(binanceApiSecret, cryptoKey, binanceIv);
      updateData.binance_iv = btoa(String.fromCharCode(...binanceIv));
    }

    // Kraken
    if (krakenApiKey && krakenApiSecret) {
      const krakenIv = crypto.getRandomValues(new Uint8Array(12));
      updateData.kraken_api_key_encrypted = await encryptCredential(krakenApiKey, cryptoKey, krakenIv);
      updateData.kraken_api_secret_encrypted = await encryptCredential(krakenApiSecret, cryptoKey, krakenIv);
      updateData.kraken_iv = btoa(String.fromCharCode(...krakenIv));
    }

    // Alpaca
    if (alpacaApiKey && alpacaSecretKey) {
      const alpacaIv = crypto.getRandomValues(new Uint8Array(12));
      updateData.alpaca_api_key_encrypted = await encryptCredential(alpacaApiKey, cryptoKey, alpacaIv);
      updateData.alpaca_secret_key_encrypted = await encryptCredential(alpacaSecretKey, cryptoKey, alpacaIv);
      updateData.alpaca_iv = btoa(String.fromCharCode(...alpacaIv));
    }

    // Capital.com
    if (capitalApiKey && capitalPassword) {
      const capitalIv = crypto.getRandomValues(new Uint8Array(12));
      updateData.capital_api_key_encrypted = await encryptCredential(capitalApiKey, cryptoKey, capitalIv);
      updateData.capital_password_encrypted = await encryptCredential(capitalPassword, cryptoKey, capitalIv);
      if (capitalIdentifier) {
        updateData.capital_identifier_encrypted = await encryptCredential(capitalIdentifier, cryptoKey, capitalIv);
      }
      updateData.capital_iv = btoa(String.fromCharCode(...capitalIv));
    }

    // Check if session exists
    const { data: existingSession } = await supabase
      .from('aureon_user_sessions')
      .select('id')
      .eq('user_id', user.id)
      .single();

    if (existingSession) {
      // Update existing session
      const { error: updateError } = await supabase
        .from('aureon_user_sessions')
        .update(updateData)
        .eq('user_id', user.id);

      if (updateError) {
        console.error('Update error:', updateError);
        return new Response(JSON.stringify({ error: 'Failed to update credentials' }), {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }
    } else {
      // Create new session
      const { error: insertError } = await supabase
        .from('aureon_user_sessions')
        .insert({
          user_id: user.id,
          ...updateData,
          payment_completed: true,
          is_trading_active: false,
          gas_tank_balance: 100
        });

      if (insertError) {
        console.error('Insert error:', insertError);
        return new Response(JSON.stringify({ error: 'Failed to create session' }), {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }
    }

    // Return which exchanges were updated
    const updatedExchanges = [];
    if (updateData.binance_api_key_encrypted) updatedExchanges.push('binance');
    if (updateData.kraken_api_key_encrypted) updatedExchanges.push('kraken');
    if (updateData.alpaca_api_key_encrypted) updatedExchanges.push('alpaca');
    if (updateData.capital_api_key_encrypted) updatedExchanges.push('capital');

    return new Response(JSON.stringify({ 
      success: true, 
      updatedExchanges,
      message: `Updated ${updatedExchanges.length} exchange(s)` 
    }), {
      status: 200,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });

  } catch (error) {
    console.error('Error:', error);
    return new Response(JSON.stringify({ error: 'Internal server error' }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
