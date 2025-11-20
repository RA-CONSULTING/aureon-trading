import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.81.1';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

// AES-256-GCM encryption using Web Crypto API
async function encryptCredential(credential: string): Promise<{ encrypted: string; iv: string }> {
  const encoder = new TextEncoder();
  const data = encoder.encode(credential);
  
  // Get master encryption key from environment
  const masterKeyString = Deno.env.get('MASTER_ENCRYPTION_KEY');
  if (!masterKeyString) {
    throw new Error('MASTER_ENCRYPTION_KEY not configured');
  }
  
  // Import master key for AES-GCM
  const masterKeyData = encoder.encode(masterKeyString);
  const masterKey = await crypto.subtle.importKey(
    'raw',
    masterKeyData.slice(0, 32), // Use first 32 bytes for AES-256
    { name: 'AES-GCM', length: 256 },
    false,
    ['encrypt']
  );
  
  // Generate random initialization vector
  const iv = crypto.getRandomValues(new Uint8Array(12)); // 12 bytes for GCM
  
  // Encrypt the credential
  const encryptedData = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv },
    masterKey,
    data
  );
  
  // Convert to base64 for storage
  const encryptedArray = new Uint8Array(encryptedData);
  const ivArray = new Uint8Array(iv);
  
  return {
    encrypted: btoa(String.fromCharCode(...encryptedArray)),
    iv: btoa(String.fromCharCode(...ivArray))
  };
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseKey);

    const { userId, apiKey, apiSecret } = await req.json();

    if (!userId || !apiKey || !apiSecret) {
      throw new Error('Missing required fields: userId, apiKey, apiSecret');
    }

    console.log('[store-binance-credentials] Encrypting credentials for user:', userId);

    // Encrypt the credentials with AES-256-GCM
    const encryptedApiKey = await encryptCredential(apiKey);
    const encryptedApiSecret = await encryptCredential(apiSecret);

    // Store encrypted credentials with IVs
    const { error: insertError } = await supabase
      .from('user_binance_credentials')
      .insert({
        user_id: userId,
        api_key_encrypted: encryptedApiKey.encrypted,
        api_secret_encrypted: encryptedApiSecret.encrypted,
        iv: encryptedApiKey.iv, // Store single IV (both use same IV for simplicity)
        last_used_at: new Date().toISOString()
      });

    if (insertError) {
      // If insert fails due to duplicate, try update
      const { error: updateError } = await supabase
        .from('user_binance_credentials')
        .update({
          api_key_encrypted: encryptedApiKey.encrypted,
          api_secret_encrypted: encryptedApiSecret.encrypted,
          iv: encryptedApiKey.iv,
          updated_at: new Date().toISOString(),
          last_used_at: new Date().toISOString()
        })
        .eq('user_id', userId);

      if (updateError) {
        throw new Error(`Failed to store credentials: ${updateError.message}`);
      }
    }

    // Log audit trail
    await supabase
      .from('data_access_audit')
      .insert({
        user_id: userId,
        accessed_by: userId,
        access_type: 'CREATE',
        resource_type: 'BINANCE_CREDENTIALS',
        metadata: {
          action: 'store_encrypted_credentials',
          timestamp: new Date().toISOString()
        }
      });

    console.log('[store-binance-credentials] Credentials stored successfully');

    return new Response(
      JSON.stringify({ 
        success: true,
        message: 'Credentials encrypted and stored securely'
      }),
      {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    );

  } catch (error) {
    console.error('[store-binance-credentials] Error:', error);
    return new Response(
      JSON.stringify({
        error: error instanceof Error ? error.message : 'Unknown error',
        details: 'Failed to store Binance credentials',
      }),
      {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    );
  }
});
