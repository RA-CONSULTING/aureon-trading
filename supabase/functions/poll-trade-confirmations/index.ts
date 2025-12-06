import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    );
    
    const supabaseUrl = Deno.env.get('SUPABASE_URL') ?? '';

    console.log('[poll-trade-confirmations] Starting confirmation polling...');
    
    // Find all unconfirmed trades (ORDER_SUBMITTED stage with pending validation)
    const { data: pendingTrades, error: fetchError } = await supabase
      .from('trade_audit_log')
      .select('*')
      .eq('stage', 'ORDER_SUBMITTED')
      .eq('validation_status', 'pending')
      .gte('created_at', new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString()) // Last 24 hours
      .order('created_at', { ascending: true })
      .limit(50);
    
    if (fetchError) {
      throw new Error(`Failed to fetch pending trades: ${fetchError.message}`);
    }
    
    console.log(`[poll-trade-confirmations] Found ${pendingTrades?.length || 0} pending trades to confirm`);
    
    if (!pendingTrades || pendingTrades.length === 0) {
      return new Response(
        JSON.stringify({
          success: true,
          confirmed: 0,
          failed: 0,
          pending: 0,
          message: 'No pending trades to confirm',
        }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }
    
    let confirmed = 0;
    let failed = 0;
    let stillPending = 0;
    
    // Process each pending trade
    for (const trade of pendingTrades) {
      try {
        // Call confirm-trade function for each
        const confirmResponse = await fetch(`${supabaseUrl}/functions/v1/confirm-trade`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')}`,
          },
          body: JSON.stringify({
            trade_id: trade.trade_id,
            external_order_id: trade.external_order_id,
            symbol: trade.symbol,
            exchange: trade.exchange,
          }),
        });
        
        if (confirmResponse.ok) {
          const result = await confirmResponse.json();
          if (result.confirmed) {
            confirmed++;
            console.log(`[poll-trade-confirmations] Confirmed trade ${trade.external_order_id}: ${result.status}`);
          } else {
            stillPending++;
          }
        } else {
          failed++;
          console.error(`[poll-trade-confirmations] Failed to confirm ${trade.external_order_id}`);
        }
      } catch (error) {
        failed++;
        console.error(`[poll-trade-confirmations] Error confirming ${trade.external_order_id}:`, error);
        
        // Mark as failed in audit log
        await supabase
          .from('trade_audit_log')
          .update({
            validation_status: 'failed',
            validation_message: error instanceof Error ? error.message : 'Confirmation failed',
            updated_at: new Date().toISOString(),
          })
          .eq('id', trade.id);
      }
    }
    
    console.log(`[poll-trade-confirmations] Results - Confirmed: ${confirmed}, Failed: ${failed}, Pending: ${stillPending}`);
    
    return new Response(
      JSON.stringify({
        success: true,
        confirmed,
        failed,
        pending: stillPending,
        total: pendingTrades.length,
        polledAt: new Date().toISOString(),
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  } catch (error) {
    console.error('[poll-trade-confirmations] Error:', error);
    return new Response(
      JSON.stringify({ 
        success: false, 
        error: error instanceof Error ? error.message : 'Unknown error' 
      }),
      { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});
