import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.81.1';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

// AES-256-GCM decryption using Web Crypto API
async function decryptCredential(encryptedCredential: string, iv: string): Promise<string> {
  try {
    const encoder = new TextEncoder();
    
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
      ['decrypt']
    );
    
    // Convert base64 strings back to Uint8Arrays
    const encryptedData = Uint8Array.from(atob(encryptedCredential), c => c.charCodeAt(0));
    const ivData = Uint8Array.from(atob(iv), c => c.charCodeAt(0));
    
    // Decrypt the credential
    const decryptedData = await crypto.subtle.decrypt(
      { name: 'AES-GCM', iv: ivData },
      masterKey,
      encryptedData
    );
    
    return new TextDecoder().decode(decryptedData);
  } catch (error) {
    console.error('[decrypt-credentials] Decryption error:', error);
    throw new Error('Failed to decrypt credentials - may be corrupted or encrypted with different key');
  }
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseKey);

    // Get authenticated user from JWT
    const authHeader = req.headers.get('Authorization');
    if (!authHeader) {
      throw new Error('No authorization header');
    }

    const token = authHeader.replace('Bearer ', '');
    const { data: { user }, error: authError } = await supabase.auth.getUser(token);
    
    if (authError || !user) {
      throw new Error('Unauthorized');
    }

    console.log('[get-binance-credentials] Fetching credentials for user:', user.id);

    // Retrieve encrypted credentials
    const { data: credentials, error: credError } = await supabase
      .from('user_binance_credentials')
      .select('*')
      .eq('user_id', user.id)
      .single();

    if (credError || !credentials) {
      throw new Error('No Binance credentials found. Please add your API credentials in settings.');
    }

    if (!credentials.iv) {
      throw new Error('Credentials encrypted with old format. Please re-enter your API credentials.');
    }

    // Decrypt credentials using AES-256-GCM
    const apiKey = await decryptCredential(credentials.api_key_encrypted, credentials.iv);
    const apiSecret = await decryptCredential(credentials.api_secret_encrypted, credentials.iv);

    // Update last_used_at
    await supabase
      .from('user_binance_credentials')
      .update({ last_used_at: new Date().toISOString() })
      .eq('user_id', user.id);

    // Log audit trail
    await supabase
      .from('data_access_audit')
      .insert({
        user_id: user.id,
        accessed_by: user.id,
        access_type: 'READ',
        resource_type: 'BINANCE_CREDENTIALS',
        ip_address: req.headers.get('x-forwarded-for') || 'unknown',
        metadata: {
          action: 'decrypt_credentials',
          timestamp: new Date().toISOString()
        }
      });

    console.log('[get-binance-credentials] Credentials retrieved successfully');

    return new Response(
      JSON.stringify({ 
        apiKey,
        apiSecret,
        userId: user.id
      }),
      {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    );

  } catch (error) {
    console.error('[get-binance-credentials] Error:', error);
    return new Response(
      JSON.stringify({
        error: error instanceof Error ? error.message : 'Unknown error',
        details: 'Failed to retrieve Binance credentials',
      }),
      {
        status: error instanceof Error && error.message.includes('Unauthorized') ? 403 : 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    );
  }
});
