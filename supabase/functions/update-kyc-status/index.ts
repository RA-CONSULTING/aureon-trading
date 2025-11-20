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

    // Get authenticated user (admin)
    const authHeader = req.headers.get('Authorization');
    if (!authHeader) {
      throw new Error('No authorization header');
    }

    const token = authHeader.replace('Bearer ', '');
    const { data: { user: adminUser }, error: authError } = await supabase.auth.getUser(token);
    
    if (authError || !adminUser) {
      throw new Error('Unauthorized');
    }

    // Verify admin role
    const { data: roleData } = await supabase
      .from('user_roles')
      .select('role')
      .eq('user_id', adminUser.id)
      .eq('role', 'admin')
      .single();

    if (!roleData) {
      throw new Error('Admin access required');
    }

    const { userId, status, reason } = await req.json();

    if (!userId || !status || !reason) {
      throw new Error('Missing required fields: userId, status, reason');
    }

    if (!['verified', 'rejected'].includes(status)) {
      throw new Error('Invalid status. Must be "verified" or "rejected"');
    }

    console.log(`[update-kyc-status] Admin ${adminUser.email} updating KYC for user ${userId} to ${status}`);

    // Get user's current profile
    const { data: profile, error: profileError } = await supabase
      .from('profiles')
      .select('*')
      .eq('id', userId)
      .single();

    if (profileError) throw profileError;

    // Update KYC status
    const updateData: any = {
      kyc_status: status,
      updated_at: new Date().toISOString()
    };

    if (status === 'verified') {
      updateData.kyc_verified_at = new Date().toISOString();
    }

    const { error: updateError } = await supabase
      .from('profiles')
      .update(updateData)
      .eq('id', userId);

    if (updateError) throw updateError;

    // Create comprehensive audit log
    const { error: auditError } = await supabase
      .from('data_access_audit')
      .insert({
        user_id: userId,
        accessed_by: adminUser.id,
        access_type: status === 'verified' ? 'APPROVE_KYC' : 'REJECT_KYC',
        resource_type: 'KYC_VERIFICATION',
        ip_address: req.headers.get('x-forwarded-for') || 'unknown',
        metadata: {
          admin_email: adminUser.email,
          admin_id: adminUser.id,
          user_email: profile.email,
          user_full_name: profile.full_name,
          previous_status: profile.kyc_status,
          new_status: status,
          reason: reason,
          timestamp: new Date().toISOString(),
          action_date: new Date().toISOString()
        }
      });

    if (auditError) {
      console.error('[update-kyc-status] Audit log error:', auditError);
    }

    console.log(`[update-kyc-status] KYC status updated successfully for user ${userId}`);

    return new Response(
      JSON.stringify({ 
        success: true,
        message: `KYC ${status} successfully`,
        userId,
        status,
        timestamp: new Date().toISOString()
      }),
      {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    );

  } catch (error) {
    console.error('[update-kyc-status] Error:', error);
    return new Response(
      JSON.stringify({
        error: error instanceof Error ? error.message : 'Unknown error',
        details: 'Failed to update KYC status',
      }),
      {
        status: error instanceof Error && error.message.includes('Unauthorized') ? 403 : 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    );
  }
});
