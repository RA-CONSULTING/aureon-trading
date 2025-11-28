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
    const { userId } = await req.json();

    console.log('Gas tank balance check request:', { userId });

    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseKey);

    // Get gas tank account
    const { data: account, error } = await supabase
      .from('gas_tank_accounts')
      .select('*')
      .eq('user_id', userId)
      .single();

    if (error || !account) {
      // No gas tank account = can't trade
      return new Response(
        JSON.stringify({
          success: true,
          canTrade: false,
          reason: 'NO_ACCOUNT',
          message: 'Gas tank not initialized - please top up to start trading',
          balance: 0,
          status: 'EMPTY',
        }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    const balance = parseFloat(account.balance as any);
    const status = account.status;

    // Check if user can trade
    const canTrade = balance > 0 && status !== 'PAUSED' && status !== 'EMPTY';
    
    let reason = null;
    let message = 'Gas tank ready';

    if (balance <= 0) {
      reason = 'EMPTY_TANK';
      message = 'Gas tank empty - please top up to resume trading';
    } else if (status === 'PAUSED') {
      reason = 'PAUSED';
      message = 'Trading paused - please top up to resume';
    } else if (status === 'CRITICAL') {
      message = 'Gas tank critically low - top up recommended';
    } else if (status === 'LOW') {
      message = 'Gas tank running low - consider topping up';
    }

    console.log('Gas tank balance check result:', { userId, canTrade, balance, status });

    return new Response(
      JSON.stringify({
        success: true,
        canTrade,
        reason,
        message,
        account: {
          balance,
          status,
          feeRate: account.fee_rate,
          membershipType: account.membership_type,
          highWaterMark: account.high_water_mark,
          feesPaidToday: account.fees_paid_today,
          totalFeesPaid: account.total_fees_paid,
        },
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    console.error('Gas tank balance check error:', error);
    return new Response(
      JSON.stringify({ success: false, error: error instanceof Error ? error.message : 'Unknown error' }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
    );
  }
});
