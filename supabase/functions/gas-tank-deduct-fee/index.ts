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
    const { userId, profit, tradeExecutionId } = await req.json();

    console.log('Gas tank fee deduction request:', { userId, profit, tradeExecutionId });

    if (!profit || profit <= 0) {
      return new Response(
        JSON.stringify({ success: false, error: 'Profit must be positive' }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 400 }
      );
    }

    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseKey);

    // Get gas tank account
    const { data: account, error: accountError } = await supabase
      .from('gas_tank_accounts')
      .select('*')
      .eq('user_id', userId)
      .single();

    if (accountError || !account) {
      return new Response(
        JSON.stringify({ success: false, error: 'Gas tank account not found' }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 404 }
      );
    }

    // Calculate new equity (current balance + profit)
    const currentEquity = parseFloat(account.balance as any);
    const newEquity = currentEquity + profit;
    const highWaterMark = parseFloat(account.high_water_mark as any);

    // Only charge fee on profits ABOVE high-water mark
    let feeAmount = 0;
    let newHighWaterMark = highWaterMark;

    if (newEquity > highWaterMark) {
      const taxableProfit = newEquity - highWaterMark;
      feeAmount = taxableProfit * parseFloat(account.fee_rate as any);
      newHighWaterMark = newEquity;
    }

    // Calculate new balance after fee deduction
    const balanceBefore = currentEquity;
    const newBalance = Math.max(0, currentEquity - feeAmount);

    // Calculate status based on percentage of initial balance
    let status = 'ACTIVE';
    const initialBalance = parseFloat(account.initial_balance as any);
    if (initialBalance > 0) {
      const percentageRemaining = (newBalance / initialBalance) * 100;
      if (newBalance <= 0) status = 'EMPTY';
      else if (percentageRemaining < 20) status = 'CRITICAL';
      else if (percentageRemaining < 30) status = 'LOW';
    } else if (newBalance <= 0) {
      status = 'EMPTY';
    }

    // Update gas tank account
    const feesPaidToday = parseFloat(account.fees_paid_today as any) + feeAmount;
    const totalFeesPaid = parseFloat(account.total_fees_paid as any) + feeAmount;

    const { error: updateError } = await supabase
      .from('gas_tank_accounts')
      .update({
        balance: newBalance,
        high_water_mark: newHighWaterMark,
        fees_paid_today: feesPaidToday,
        total_fees_paid: totalFeesPaid,
        status,
        last_fee_deducted_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      })
      .eq('user_id', userId);

    if (updateError) throw updateError;

    // Record transaction
    if (feeAmount > 0) {
      await supabase
        .from('gas_tank_transactions')
        .insert({
          account_id: account.id,
          type: 'FEE_DEDUCTION',
          amount: -feeAmount,
          balance_before: balanceBefore,
          balance_after: newBalance,
          description: `Performance fee: £${feeAmount.toFixed(2)} (${(parseFloat(account.fee_rate as any) * 100).toFixed(0)}% of £${profit.toFixed(2)} profit)`,
          trade_execution_id: tradeExecutionId,
          metadata: {
            profit,
            feeRate: account.fee_rate,
            highWaterMark,
            newHighWaterMark,
          },
        });
    }

    console.log('Gas tank fee deducted:', { userId, feeAmount, newBalance, status });

    return new Response(
      JSON.stringify({
        success: true,
        feeAmount,
        newBalance,
        status,
        highWaterMark: newHighWaterMark,
        message: feeAmount > 0 ? `Fee deducted: £${feeAmount.toFixed(2)}` : 'No fee deducted (profit below high-water mark)',
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    console.error('Gas tank fee deduction error:', error);
    return new Response(
      JSON.stringify({ success: false, error: error instanceof Error ? error.message : 'Unknown error' }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
    );
  }
});
