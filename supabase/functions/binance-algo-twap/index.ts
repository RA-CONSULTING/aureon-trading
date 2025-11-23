import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import { createHmac } from "https://deno.land/std@0.177.0/node/crypto.ts";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

interface TWAPOrderParams {
  symbol: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  duration: number;
  limitPrice?: number;
  omsOrderId?: string;
  huntSessionId?: string;
}

// Binance API signature helper
function signRequest(queryString: string, secret: string): string {
  return createHmac('sha256', secret)
    .update(queryString)
    .digest('hex');
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const binanceApiKey = Deno.env.get('BINANCE_API_KEY');
    const binanceApiSecret = Deno.env.get('BINANCE_API_SECRET');
    
    const supabase = createClient(supabaseUrl, supabaseKey);
    const { action, ...params } = await req.json();

    console.log(`Binance TWAP ${action} request:`, params);

    // ==========================
    // PLACE TWAP ORDER
    // ==========================
    if (action === 'place') {
      if (!binanceApiKey || !binanceApiSecret) {
        throw new Error('Binance API credentials not configured');
      }

      const { symbol, side, quantity, duration, limitPrice, omsOrderId, huntSessionId } = params as TWAPOrderParams;

      // Generate unique client algo ID
      const clientAlgoId = crypto.randomUUID().replace(/-/g, '');

      // Build request parameters
      const timestamp = Date.now();
      const queryParams: Record<string, string | number> = {
        symbol,
        side,
        quantity: quantity.toFixed(8),
        duration,
        clientAlgoId,
        timestamp,
      };

      if (limitPrice) {
        queryParams.limitPrice = limitPrice.toFixed(8);
      }

      // Create query string and sign
      const queryString = Object.entries(queryParams)
        .map(([key, value]) => `${key}=${value}`)
        .join('&');
      
      const signature = signRequest(queryString, binanceApiSecret);
      const signedQueryString = `${queryString}&signature=${signature}`;

      // Call Binance API
      const binanceResponse = await fetch(
        `https://api.binance.com/sapi/v1/algo/spot/newOrderTwap?${signedQueryString}`,
        {
          method: 'POST',
          headers: {
            'X-MBX-APIKEY': binanceApiKey,
          },
        }
      );

      const binanceData = await binanceResponse.json();

      if (!binanceData.success) {
        console.error('Binance TWAP order failed:', binanceData);
        throw new Error(`Binance error: ${binanceData.msg} (code: ${binanceData.code})`);
      }

      // Save to database
      const { data: twapOrder, error: insertError } = await supabase
        .from('twap_orders')
        .insert({
          client_algo_id: clientAlgoId,
          hunt_session_id: huntSessionId,
          oms_order_id: omsOrderId,
          symbol,
          side,
          total_quantity: quantity,
          duration_seconds: duration,
          limit_price: limitPrice,
          algo_status: 'WORKING',
          book_time: new Date().toISOString(),
        })
        .select()
        .single();

      if (insertError) {
        console.error('Failed to save TWAP order:', insertError);
        throw insertError;
      }

      console.log(`✅ TWAP order placed: ${symbol} ${side} ${quantity} over ${duration}s`);

      return new Response(
        JSON.stringify({
          success: true,
          twapOrderId: twapOrder.id,
          clientAlgoId,
          binanceResponse: binanceData,
        }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // ==========================
    // SYNC TWAP ORDER STATUS
    // ==========================
    if (action === 'sync') {
      if (!binanceApiKey || !binanceApiSecret) {
        throw new Error('Binance API credentials not configured');
      }

      const { twapOrderId } = params;

      // Get TWAP order from database
      const { data: twapOrder, error: fetchError } = await supabase
        .from('twap_orders')
        .select('*')
        .eq('id', twapOrderId)
        .single();

      if (fetchError || !twapOrder) {
        throw new Error('TWAP order not found');
      }

      // Query Binance for sub-orders
      const timestamp = Date.now();
      const queryString = `algoId=${twapOrder.algo_id}&timestamp=${timestamp}`;
      const signature = signRequest(queryString, binanceApiSecret);

      const subOrdersResponse = await fetch(
        `https://api.binance.com/sapi/v1/algo/spot/subOrders?${queryString}&signature=${signature}`,
        {
          headers: {
            'X-MBX-APIKEY': binanceApiKey,
          },
        }
      );

      const subOrdersData = await subOrdersResponse.json();

      // Update database with sub-orders
      if (subOrdersData.subOrders && subOrdersData.subOrders.length > 0) {
        const subOrderInserts = subOrdersData.subOrders.map((sub: any) => ({
          twap_order_id: twapOrderId,
          sub_id: sub.subId,
          order_id: sub.orderId,
          symbol: sub.symbol,
          side: sub.side,
          order_status: sub.orderStatus,
          executed_quantity: parseFloat(sub.executedQty),
          executed_amount: parseFloat(sub.executedAmt),
          orig_quantity: parseFloat(sub.origQty),
          avg_price: parseFloat(sub.avgPrice),
          fee_amount: parseFloat(sub.feeAmt),
          fee_asset: sub.feeAsset,
          book_time: new Date(sub.bookTime).toISOString(),
          time_in_force: sub.timeInForce,
        }));

        await supabase
          .from('twap_sub_orders')
          .upsert(subOrderInserts, {
            onConflict: 'twap_order_id,sub_id',
          });

        // Update main TWAP order
        await supabase
          .from('twap_orders')
          .update({
            executed_quantity: parseFloat(subOrdersData.executedQty),
            executed_amount: parseFloat(subOrdersData.executedAmt),
            avg_price: parseFloat(subOrdersData.executedAmt) / parseFloat(subOrdersData.executedQty),
            updated_at: new Date().toISOString(),
          })
          .eq('id', twapOrderId);
      }

      return new Response(
        JSON.stringify({
          success: true,
          subOrdersCount: subOrdersData.subOrders?.length || 0,
        }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // ==========================
    // CANCEL TWAP ORDER
    // ==========================
    if (action === 'cancel') {
      if (!binanceApiKey || !binanceApiSecret) {
        throw new Error('Binance API credentials not configured');
      }

      const { twapOrderId } = params;

      const { data: twapOrder } = await supabase
        .from('twap_orders')
        .select('algo_id')
        .eq('id', twapOrderId)
        .single();

      if (!twapOrder?.algo_id) {
        throw new Error('TWAP order not found or has no algo_id');
      }

      const timestamp = Date.now();
      const queryString = `algoId=${twapOrder.algo_id}&timestamp=${timestamp}`;
      const signature = signRequest(queryString, binanceApiSecret);

      const cancelResponse = await fetch(
        `https://api.binance.com/sapi/v1/algo/spot/order?${queryString}&signature=${signature}`,
        {
          method: 'DELETE',
          headers: {
            'X-MBX-APIKEY': binanceApiKey,
          },
        }
      );

      const cancelData = await cancelResponse.json();

      if (!cancelData.success) {
        throw new Error(`Cancel failed: ${cancelData.msg}`);
      }

      await supabase
        .from('twap_orders')
        .update({
          algo_status: 'CANCELLED',
          end_time: new Date().toISOString(),
        })
        .eq('id', twapOrderId);

      return new Response(
        JSON.stringify({ success: true }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    throw new Error(`Unknown action: ${action}`);

  } catch (error) {
    console.error('Binance TWAP error:', error);
    return new Response(
      JSON.stringify({ 
        success: false, 
        error: error instanceof Error ? error.message : 'Unknown error' 
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
    );
  }
});