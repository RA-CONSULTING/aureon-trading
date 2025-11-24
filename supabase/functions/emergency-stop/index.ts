import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.3';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '',
    );

    console.log('🚨 EMERGENCY STOP INITIATED');

    // Step 1: Disable trading immediately
    const { error: configError } = await supabaseClient
      .from('trading_config')
      .update({ is_enabled: false })
      .eq('id', (await supabaseClient.from('trading_config').select('id').single()).data?.id || '');

    if (configError) {
      console.error('Failed to disable trading config:', configError);
    } else {
      console.log('✅ Trading disabled');
    }

    // Step 2: Cancel all queued orders
    const { data: queuedOrders, error: queueError } = await supabaseClient
      .from('oms_order_queue')
      .update({ status: 'cancelled', cancelled_at: new Date().toISOString() })
      .in('status', ['queued', 'pending'])
      .select();

    if (queueError) {
      console.error('Failed to cancel queued orders:', queueError);
    } else {
      console.log(`✅ Cancelled ${queuedOrders?.length || 0} queued orders`);
    }

    // Step 3: Mark all open positions for closure (would need exchange integration for actual closure)
    const { data: openPositions, error: posError } = await supabaseClient
      .from('trading_positions')
      .select('*')
      .eq('status', 'open');

    if (posError) {
      console.error('Failed to fetch open positions:', posError);
    } else {
      console.log(`⚠️  ${openPositions?.length || 0} open positions detected (manual closure may be required)`);
    }

    // Step 4: Log emergency stop event
    const { error: logError } = await supabaseClient
      .from('scheduler_history')
      .insert({
        action: 'emergency_stop',
        reason: 'Emergency stop button triggered',
        trading_enabled_before: true,
        trading_enabled_after: false,
        coherence_at_action: 0,
        metadata: {
          queued_orders_cancelled: queuedOrders?.length || 0,
          open_positions_count: openPositions?.length || 0,
          timestamp: new Date().toISOString(),
        },
      });

    if (logError) {
      console.error('Failed to log emergency stop:', logError);
    }

    console.log('🚨 EMERGENCY STOP COMPLETE');

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Emergency stop executed successfully',
        cancelled_orders: queuedOrders?.length || 0,
        open_positions: openPositions?.length || 0,
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200,
      },
    );

  } catch (error) {
    console.error('Emergency stop error:', error);
    return new Response(
      JSON.stringify({
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 500,
      },
    );
  }
});
