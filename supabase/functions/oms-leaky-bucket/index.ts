import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

const RATE_LIMIT = 100; // Binance limit: 100 orders per 10 seconds
const WINDOW_DURATION_MS = 10000; // 10 seconds
const PROCESS_INTERVAL_MS = 100; // Process every 100ms

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseKey);

    const authHeader = req.headers.get('Authorization');
    if (!authHeader) {
      throw new Error('Missing authorization header');
    }

    const token = authHeader.replace('Bearer ', '');
    const { data: { user }, error: userError } = await supabase.auth.getUser(token);
    if (userError || !user) {
      throw new Error('Unauthorized');
    }

    const { action, ...params } = await req.json();
    console.log(`OMS ${action} request:`, { user: user.id, params });

    if (action === 'enqueue') {
      // === ADD ORDER TO QUEUE ===
      const { sessionId, hiveId, agentId, symbol, side, quantity, price, priority, metadata } = params;

      if (!sessionId || !hiveId || !agentId || !symbol || !side || !quantity || !price) {
        throw new Error('Missing required order parameters');
      }

      // Verify session ownership
      const { data: session } = await supabase
        .from('hive_sessions')
        .select('id')
        .eq('id', sessionId)
        .eq('user_id', user.id)
        .single();

      if (!session) {
        throw new Error('Session not found or unauthorized');
      }

      // Insert into queue
      const { data: order, error: orderError } = await supabase
        .from('oms_order_queue')
        .insert({
          session_id: sessionId,
          hive_id: hiveId,
          agent_id: agentId,
          symbol,
          side,
          quantity,
          price,
          priority: priority || 50,
          signal_strength: metadata?.signalStrength,
          coherence: metadata?.coherence,
          lighthouse_value: metadata?.lighthouseValue,
          status: 'queued',
        })
        .select()
        .single();

      if (orderError) {
        console.error('Failed to enqueue order:', orderError);
        throw new Error('Failed to enqueue order');
      }

      console.log(`✅ Order enqueued: ${order.id} | ${symbol} ${side} ${quantity} @ ${price}`);

      return new Response(
        JSON.stringify({
          success: true,
          orderId: order.id,
          position: await getQueuePosition(supabase, order.id),
        }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    if (action === 'process') {
      // === PROCESS QUEUED ORDERS (LEAKY BUCKET) ===
      const now = new Date();
      const windowStart = new Date(now.getTime() - WINDOW_DURATION_MS);

      // Get current window
      const { data: windows } = await supabase
        .from('oms_rate_limit_windows')
        .select('*')
        .gte('window_end', now.toISOString())
        .order('window_start', { ascending: false })
        .limit(1);

      let currentWindow = windows?.[0];

      // Create new window if needed
      if (!currentWindow || new Date(currentWindow.window_start) < windowStart) {
        const { data: newWindow } = await supabase
          .from('oms_rate_limit_windows')
          .insert({
            window_start: windowStart.toISOString(),
            window_end: now.toISOString(),
            orders_executed: 0,
          })
          .select()
          .single();

        currentWindow = newWindow!;
      }

      // Count orders in current window
      const { count: ordersInWindow } = await supabase
        .from('oms_order_queue')
        .select('*', { count: 'exact', head: true })
        .eq('status', 'executed')
        .gte('executed_at', windowStart.toISOString());

      const availableSlots = RATE_LIMIT - (ordersInWindow || 0);

      if (availableSlots <= 0) {
        return new Response(
          JSON.stringify({
            success: true,
            processed: 0,
            reason: 'Rate limit reached',
            availableSlots: 0,
            nextWindowIn: WINDOW_DURATION_MS - (now.getTime() - new Date(currentWindow.window_start).getTime()),
          }),
          { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        );
      }

      // Get orders to process (highest priority first)
      const { data: orders } = await supabase
        .from('oms_order_queue')
        .select('*')
        .eq('status', 'queued')
        .order('priority', { ascending: false })
        .order('queued_at', { ascending: true })
        .limit(Math.min(availableSlots, 10)); // Process max 10 at a time

      if (!orders || orders.length === 0) {
        return new Response(
          JSON.stringify({
            success: true,
            processed: 0,
            reason: 'No orders in queue',
            availableSlots,
          }),
          { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        );
      }

      let processed = 0;
      const results = [];

      for (const order of orders) {
        try {
          // Mark as processing
          await supabase
            .from('oms_order_queue')
            .update({ status: 'processing' })
            .eq('id', order.id);

          // Execute order (paper trading simulation for now)
          const executedPrice = order.price * (1 + (Math.random() * 0.002 - 0.001)); // ±0.1% slippage
          const executedQuantity = order.quantity;

          // Update order status
          await supabase
            .from('oms_order_queue')
            .update({
              status: 'executed',
              executed_at: new Date().toISOString(),
              executed_price: executedPrice,
              executed_quantity: executedQuantity,
              exchange_order_id: `PAPER-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            })
            .eq('id', order.id);

          // Record trade in hive_trades
          const pnl = order.side === 'BUY'
            ? (executedPrice - order.price) * executedQuantity
            : (order.price - executedPrice) * executedQuantity;

          await supabase
            .from('hive_trades')
            .insert({
              session_id: order.session_id,
              hive_id: order.hive_id,
              agent_id: order.agent_id,
              symbol: order.symbol,
              side: order.side,
              entry_price: executedPrice,
              exit_price: executedPrice,
              quantity: executedQuantity,
              pnl,
              status: 'closed',
              closed_at: new Date().toISOString(),
            });

          processed++;
          results.push({
            orderId: order.id,
            symbol: order.symbol,
            side: order.side,
            executedPrice,
            executedQuantity,
          });

          console.log(`✅ Order executed: ${order.symbol} ${order.side} ${executedQuantity} @ ${executedPrice}`);
        } catch (error) {
          console.error(`Failed to execute order ${order.id}:`, error);

          await supabase
            .from('oms_order_queue')
            .update({
              status: 'failed',
              error_message: error instanceof Error ? error.message : 'Unknown error',
            })
            .eq('id', order.id);
        }
      }

      // Update window count
      await supabase
        .from('oms_rate_limit_windows')
        .update({ orders_executed: (currentWindow.orders_executed || 0) + processed })
        .eq('id', currentWindow.id);

      // Record metrics
      const { count: queueDepth } = await supabase
        .from('oms_order_queue')
        .select('*', { count: 'exact', head: true })
        .eq('status', 'queued');

      await supabase
        .from('oms_execution_metrics')
        .insert({
          queue_depth: queueDepth || 0,
          current_window_orders: (ordersInWindow || 0) + processed,
          rate_limit_utilization: ((ordersInWindow || 0) + processed) / RATE_LIMIT,
          orders_executed_last_minute: processed,
          orders_failed_last_minute: 0,
        });

      return new Response(
        JSON.stringify({
          success: true,
          processed,
          availableSlots: availableSlots - processed,
          results,
        }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    if (action === 'status') {
      // === GET QUEUE STATUS ===
      const { sessionId } = params;

      // Queue depth
      const { count: queueDepth } = await supabase
        .from('oms_order_queue')
        .select('*', { count: 'exact', head: true })
        .eq('status', 'queued')
        .eq('session_id', sessionId);

      // Processing count
      const { count: processing } = await supabase
        .from('oms_order_queue')
        .select('*', { count: 'exact', head: true })
        .eq('status', 'processing')
        .eq('session_id', sessionId);

      // Rate limit status
      const now = new Date();
      const windowStart = new Date(now.getTime() - WINDOW_DURATION_MS);

      const { count: ordersInWindow } = await supabase
        .from('oms_order_queue')
        .select('*', { count: 'exact', head: true })
        .eq('status', 'executed')
        .gte('executed_at', windowStart.toISOString());

      const availableSlots = RATE_LIMIT - (ordersInWindow || 0);

      // Recent metrics
      const { data: metrics } = await supabase
        .from('oms_execution_metrics')
        .select('*')
        .order('timestamp', { ascending: false })
        .limit(1)
        .single();

      return new Response(
        JSON.stringify({
          success: true,
          queueDepth: queueDepth || 0,
          processing: processing || 0,
          rateLimit: {
            limit: RATE_LIMIT,
            used: ordersInWindow || 0,
            available: availableSlots,
            utilization: ((ordersInWindow || 0) / RATE_LIMIT) * 100,
            windowDurationMs: WINDOW_DURATION_MS,
          },
          metrics: metrics || null,
        }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    if (action === 'cancel') {
      // === CANCEL ORDER ===
      const { orderId } = params;

      const { data: order } = await supabase
        .from('oms_order_queue')
        .select('*, hive_sessions!inner(user_id)')
        .eq('id', orderId)
        .single();

      if (!order || order.hive_sessions.user_id !== user.id) {
        throw new Error('Order not found or unauthorized');
      }

      if (order.status !== 'queued') {
        throw new Error(`Cannot cancel order with status: ${order.status}`);
      }

      await supabase
        .from('oms_order_queue')
        .update({
          status: 'cancelled',
          cancelled_at: new Date().toISOString(),
        })
        .eq('id', orderId);

      return new Response(
        JSON.stringify({ success: true, message: 'Order cancelled' }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    throw new Error(`Unknown action: ${action}`);

  } catch (error) {
    console.error('OMS error:', error);
    return new Response(
      JSON.stringify({ success: false, error: error instanceof Error ? error.message : 'Unknown error' }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
    );
  }
});

async function getQueuePosition(supabase: any, orderId: string): Promise<number> {
  const { data: order } = await supabase
    .from('oms_order_queue')
    .select('priority, queued_at')
    .eq('id', orderId)
    .single();

  if (!order) return 0;

  const { count } = await supabase
    .from('oms_order_queue')
    .select('*', { count: 'exact', head: true })
    .eq('status', 'queued')
    .or(`priority.gt.${order.priority},and(priority.eq.${order.priority},queued_at.lt.${order.queued_at})`);

  return (count || 0) + 1;
}
