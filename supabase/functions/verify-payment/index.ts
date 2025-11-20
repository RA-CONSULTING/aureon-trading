import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.81.1';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

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

    // Check if user is admin
    const { data: roleData } = await supabase
      .from('user_roles')
      .select('role')
      .eq('user_id', user.id)
      .eq('role', 'admin')
      .maybeSingle();

    if (!roleData) {
      throw new Error('Unauthorized - admin access required');
    }

    const { userId, transactionId } = await req.json();

    if (!userId) {
      throw new Error('Missing required field: userId');
    }

    console.log('[verify-payment] Admin verifying payment for user:', userId);

    // Update profile to mark payment as completed
    const { error: profileError } = await supabase
      .from('profiles')
      .update({
        payment_completed: true,
        payment_completed_at: new Date().toISOString()
      })
      .eq('id', userId);

    if (profileError) {
      throw new Error(`Failed to update profile: ${profileError.message}`);
    }

    // Update transaction status if provided
    if (transactionId) {
      await supabase
        .from('payment_transactions')
        .update({
          payment_status: 'completed',
          paid_at: new Date().toISOString(),
          metadata: {
            verified_by: user.id,
            verified_at: new Date().toISOString(),
            verification_method: 'manual_admin'
          }
        })
        .eq('id', transactionId);
    }

    // Log audit trail
    await supabase
      .from('data_access_audit')
      .insert({
        user_id: userId,
        accessed_by: user.id,
        access_type: 'UPDATE',
        resource_type: 'PAYMENT_VERIFICATION',
        ip_address: req.headers.get('x-forwarded-for') || 'unknown',
        metadata: {
          action: 'manual_payment_verification',
          transaction_id: transactionId,
          timestamp: new Date().toISOString()
        }
      });

    console.log('[verify-payment] Payment verified successfully');

    return new Response(
      JSON.stringify({ 
        success: true,
        message: 'Payment verified successfully'
      }),
      {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    );

  } catch (error) {
    console.error('[verify-payment] Error:', error);
    return new Response(
      JSON.stringify({
        error: error instanceof Error ? error.message : 'Unknown error',
        details: 'Failed to verify payment',
      }),
      {
        status: error instanceof Error && error.message.includes('Unauthorized') ? 403 : 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    );
  }
});
