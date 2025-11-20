import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.81.1';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

// Helper function to create HMAC signature for Binance
async function createSignature(secret: string, message: string): Promise<string> {
  const encoder = new TextEncoder();
  const keyData = encoder.encode(secret);
  const messageData = encoder.encode(message);
  
  const key = await crypto.subtle.importKey(
    'raw',
    keyData,
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );
  
  const signature = await crypto.subtle.sign('HMAC', key, messageData);
  return Array.from(new Uint8Array(signature))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    console.log('[backend-health-check] Starting comprehensive backend health check');

    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseKey);

    const healthReport: any = {
      timestamp: new Date().toISOString(),
      overall_status: 'healthy',
      checks: {},
      warnings: [],
      errors: [],
    };

    // 1. Check Database Connection
    console.log('[backend-health-check] Testing database connection...');
    try {
      const { data, error } = await supabase
        .from('trading_config')
        .select('id')
        .limit(1);
      
      healthReport.checks.database = {
        status: error ? 'unhealthy' : 'healthy',
        message: error ? error.message : 'Database connection successful',
        timestamp: new Date().toISOString(),
      };
      
      if (error) {
        healthReport.errors.push(`Database: ${error.message}`);
        healthReport.overall_status = 'degraded';
      }
    } catch (error) {
      healthReport.checks.database = {
        status: 'unhealthy',
        message: error instanceof Error ? error.message : 'Database connection failed',
        timestamp: new Date().toISOString(),
      };
      healthReport.errors.push('Database connection failed');
      healthReport.overall_status = 'unhealthy';
    }

    // 2. Check Auth System
    console.log('[backend-health-check] Testing auth system...');
    try {
      const authHeader = req.headers.get('Authorization');
      if (authHeader) {
        const token = authHeader.replace('Bearer ', '');
        const { data: { user }, error } = await supabase.auth.getUser(token);
        
        healthReport.checks.auth = {
          status: error ? 'unhealthy' : 'healthy',
          message: error ? error.message : 'Auth system operational',
          user_authenticated: !!user,
          timestamp: new Date().toISOString(),
        };
        
        if (error) {
          healthReport.warnings.push(`Auth: ${error.message}`);
        }
      } else {
        healthReport.checks.auth = {
          status: 'skipped',
          message: 'No auth token provided',
          timestamp: new Date().toISOString(),
        };
      }
    } catch (error) {
      healthReport.checks.auth = {
        status: 'unhealthy',
        message: error instanceof Error ? error.message : 'Auth check failed',
        timestamp: new Date().toISOString(),
      };
      healthReport.warnings.push('Auth system check failed');
    }

    // 3. Check Binance API Connectivity (if credentials available)
    console.log('[backend-health-check] Testing Binance API connectivity...');
    try {
      const authHeader = req.headers.get('Authorization');
      if (authHeader) {
        const { data: credsResponse, error: credsError } = await supabase.functions.invoke('get-binance-credentials', {
          headers: { Authorization: authHeader }
        });

        if (!credsError && credsResponse && credsResponse.apiKey && credsResponse.apiSecret) {
          const { apiKey, apiSecret } = credsResponse;
          
          // Test Binance connectivity
          const pingResponse = await fetch('https://api.binance.com/api/v3/ping', {
            signal: AbortSignal.timeout(5000), // 5 second timeout
          });
          
          if (pingResponse.ok) {
            // Test authenticated endpoint
            const timestamp = Date.now();
            const recvWindow = 60000;
            const queryString = `timestamp=${timestamp}&recvWindow=${recvWindow}`;
            const signature = await createSignature(apiSecret, queryString);
            const accountUrl = `https://api.binance.com/api/v3/account?${queryString}&signature=${signature}`;

            const accountResponse = await fetch(accountUrl, {
              method: 'GET',
              headers: { 'X-MBX-APIKEY': apiKey },
              signal: AbortSignal.timeout(5000),
            });

            if (accountResponse.ok) {
              healthReport.checks.binance = {
                status: 'healthy',
                message: 'Binance API fully operational',
                api_reachable: true,
                authenticated: true,
                timestamp: new Date().toISOString(),
              };
            } else {
              const errorText = await accountResponse.text();
              let errorJson;
              try {
                errorJson = JSON.parse(errorText);
              } catch (e) {
                errorJson = { msg: errorText };
              }

              let errorMessage = 'Binance API authentication failed';
              if (errorJson.code === -2015) {
                errorMessage = 'IP restrictions enabled - requires Binance API Management configuration';
              } else if (errorJson.code === -2014) {
                errorMessage = 'Invalid API key format';
              } else if (errorJson.code === -1022) {
                errorMessage = 'Invalid API signature';
              }

              healthReport.checks.binance = {
                status: 'degraded',
                message: errorMessage,
                api_reachable: true,
                authenticated: false,
                error_code: errorJson.code,
                timestamp: new Date().toISOString(),
              };
              healthReport.warnings.push(`Binance: ${errorMessage}`);
              if (healthReport.overall_status === 'healthy') {
                healthReport.overall_status = 'degraded';
              }
            }
          } else {
            healthReport.checks.binance = {
              status: 'unhealthy',
              message: 'Binance API unreachable',
              api_reachable: false,
              timestamp: new Date().toISOString(),
            };
            healthReport.errors.push('Binance API is unreachable');
            healthReport.overall_status = 'unhealthy';
          }
        } else {
          healthReport.checks.binance = {
            status: 'not_configured',
            message: 'Binance API credentials not configured',
            timestamp: new Date().toISOString(),
          };
          healthReport.warnings.push('Binance credentials not configured');
        }
      } else {
        healthReport.checks.binance = {
          status: 'skipped',
          message: 'No auth token - cannot check Binance credentials',
          timestamp: new Date().toISOString(),
        };
      }
    } catch (error) {
      healthReport.checks.binance = {
        status: 'error',
        message: error instanceof Error ? error.message : 'Binance check failed',
        timestamp: new Date().toISOString(),
      };
      healthReport.errors.push(`Binance: ${error instanceof Error ? error.message : 'Check failed'}`);
      if (healthReport.overall_status === 'healthy') {
        healthReport.overall_status = 'degraded';
      }
    }

    // 4. Check Edge Functions
    console.log('[backend-health-check] Testing edge functions...');
    const edgeFunctions = [
      'fetch-binance-market-data',
      'celestial-alignments',
      'sync-harmonic-nexus',
    ];

    for (const functionName of edgeFunctions) {
      try {
        const testPayload = functionName === 'fetch-binance-market-data' 
          ? { symbol: 'BTCUSDT' }
          : functionName === 'sync-harmonic-nexus'
          ? { temporal_id: '02111991', sentinel_name: 'HEALTH_CHECK', omega_value: 0, psi_potential: 1, love_coherence: 0, observer_consciousness: 0, theta_alignment: 1, unity_probability: 0, akashic_frequency: 10, akashic_convergence: 0.5, akashic_stability: 0.5, akashic_boost: 0, substrate_coherence: 0.5, field_integrity: 0.5, harmonic_resonance: 0, dimensional_alignment: 0, sync_status: 'test', sync_quality: 1, timeline_divergence: 0 }
          : {};

        const response = await fetch(`${supabaseUrl}/functions/v1/${functionName}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${supabaseKey}`,
          },
          body: JSON.stringify(testPayload),
          signal: AbortSignal.timeout(10000), // 10 second timeout
        });

        healthReport.checks[`edge_function_${functionName}`] = {
          status: response.ok ? 'healthy' : 'degraded',
          message: response.ok ? 'Function operational' : `HTTP ${response.status}`,
          timestamp: new Date().toISOString(),
        };

        if (!response.ok) {
          healthReport.warnings.push(`Edge function ${functionName}: HTTP ${response.status}`);
        }
      } catch (error) {
        healthReport.checks[`edge_function_${functionName}`] = {
          status: 'unhealthy',
          message: error instanceof Error ? error.message : 'Function unavailable',
          timestamp: new Date().toISOString(),
        };
        healthReport.errors.push(`Edge function ${functionName} failed`);
        if (healthReport.overall_status !== 'unhealthy') {
          healthReport.overall_status = 'degraded';
        }
      }
    }

    // 5. Check Secrets
    console.log('[backend-health-check] Checking secrets configuration...');
    const requiredSecrets = ['MASTER_ENCRYPTION_KEY', 'RESEND_API_KEY'];
    const optionalSecrets = ['BINANCE_API_KEY', 'BINANCE_API_SECRET', 'NASA_API_KEY'];
    
    healthReport.checks.secrets = {
      status: 'healthy',
      required: {},
      optional: {},
      timestamp: new Date().toISOString(),
    };

    for (const secret of requiredSecrets) {
      const value = Deno.env.get(secret);
      healthReport.checks.secrets.required[secret] = !!value;
      if (!value) {
        healthReport.errors.push(`Required secret ${secret} not configured`);
        healthReport.checks.secrets.status = 'unhealthy';
        healthReport.overall_status = 'unhealthy';
      }
    }

    for (const secret of optionalSecrets) {
      const value = Deno.env.get(secret);
      healthReport.checks.secrets.optional[secret] = !!value;
    }

    console.log('[backend-health-check] Health check complete:', healthReport.overall_status);

    return new Response(
      JSON.stringify(healthReport),
      {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    );

  } catch (error) {
    console.error('[backend-health-check] Fatal error:', error);
    
    return new Response(
      JSON.stringify({
        timestamp: new Date().toISOString(),
        overall_status: 'unhealthy',
        error: error instanceof Error ? error.message : 'Health check failed',
      }),
      {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    );
  }
});
