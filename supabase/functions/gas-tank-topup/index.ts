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
    const { userId, amount, membershipType = 'standard' } = await req.json();

    console.log('Gas tank top-up request:', { userId, amount, membershipType });

    // Validate amount
    if (!amount || amount < 10 || amount > 10000) {
      return new Response(
        JSON.stringify({ success: false, error: 'Amount must be between £10 and £10,000' }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 400 }
      );
    }

    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseKey);

    // Get or create gas tank account
    const { data: existingAccount } = await supabase
      .from('gas_tank_accounts')
      .select('*')
      .eq('user_id', userId)
      .single();

    const feeRate = membershipType === 'founder' ? 0.10 : 0.20;
    const balanceBefore = existingAccount?.balance || 0;
    const newBalance = balanceBefore + amount;

    // Calculate status based on new balance
    let status = 'ACTIVE';
    const percentageOfInitial = existingAccount?.initial_balance 
      ? (newBalance / existingAccount.initial_balance) * 100 
      : 100;
    
    if (percentageOfInitial < 20) status = 'CRITICAL';
    else if (percentageOfInitial < 30) status = 'LOW';

    let account;
    if (existingAccount) {
      // Update existing account
      const { data, error } = await supabase
        .from('gas_tank_accounts')
        .update({
          balance: newBalance,
          initial_balance: existingAccount.initial_balance === 0 ? amount : existingAccount.initial_balance,
          status,
          last_top_up_at: new Date().toISOString(),
          membership_type: membershipType,
          fee_rate: feeRate,
          updated_at: new Date().toISOString(),
        })
        .eq('user_id', userId)
        .select()
        .single();

      if (error) throw error;
      account = data;
    } else {
      // Create new account
      const { data, error } = await supabase
        .from('gas_tank_accounts')
        .insert({
          user_id: userId,
          balance: amount,
          initial_balance: amount,
          high_water_mark: amount,
          membership_type: membershipType,
          fee_rate: feeRate,
          status: 'ACTIVE',
          last_top_up_at: new Date().toISOString(),
        })
        .select()
        .single();

      if (error) throw error;
      account = data;
    }

    // Record transaction
    await supabase
      .from('gas_tank_transactions')
      .insert({
        account_id: account.id,
        type: 'TOP_UP',
        amount,
        balance_before: balanceBefore,
        balance_after: newBalance,
        description: `Top-up: £${amount.toFixed(2)}`,
        metadata: { membershipType },
      });

    console.log('Gas tank topped up:', { userId, newBalance, status });

    return new Response(
      JSON.stringify({
        success: true,
        account,
        message: `Gas tank topped up: £${amount.toFixed(2)}`,
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    console.error('Gas tank top-up error:', error);
    return new Response(
      JSON.stringify({ success: false, error: error instanceof Error ? error.message : 'Unknown error' }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
    );
  }
});
