import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';
import { createHmac } from 'https://deno.land/std@0.168.0/node/crypto.ts';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

interface TradeConfirmationResult {
  orderId: string;
  status: string;
  executedQty: number;
  executedPrice: number;
  fills: any[];
  commission: number;
  commissionAsset: string;
  isConfirmed: boolean;
}

function decryptCredential(encrypted: string, iv: string, masterKey: string): string {
  // Simple XOR decryption for demo - in production use proper AES
  const encryptedBytes = Uint8Array.from(atob(encrypted), c => c.charCodeAt(0));
  const keyBytes = new TextEncoder().encode(masterKey.slice(0, encryptedBytes.length));
  const decryptedBytes = encryptedBytes.map((b, i) => b ^ keyBytes[i % keyBytes.length]);
  return new TextDecoder().decode(decryptedBytes);
}

async function confirmBinanceOrder(
  orderId: string,
  symbol: string,
  apiKey: string,
  apiSecret: string
): Promise<TradeConfirmationResult> {
  const timestamp = Date.now();
  const queryString = `symbol=${symbol}&orderId=${orderId}&timestamp=${timestamp}`;
  
  const signature = createHmac('sha256', apiSecret)
    .update(queryString)
    .digest('hex');
  
  const url = `https://api.binance.com/api/v3/order?${queryString}&signature=${signature}`;
  
  const response = await fetch(url, {
    headers: { 'X-MBX-APIKEY': apiKey },
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Binance order query failed: ${response.status} - ${errorText}`);
  }
  
  const order = await response.json();
  
  return {
    orderId: order.orderId.toString(),
    status: order.status,
    executedQty: parseFloat(order.executedQty),
    executedPrice: parseFloat(order.price) || parseFloat(order.cummulativeQuoteQty) / parseFloat(order.executedQty),
    fills: order.fills || [],
    commission: order.fills?.reduce((sum: number, f: any) => sum + parseFloat(f.commission), 0) || 0,
    commissionAsset: order.fills?.[0]?.commissionAsset || '',
    isConfirmed: ['FILLED', 'PARTIALLY_FILLED', 'CANCELED', 'REJECTED', 'EXPIRED'].includes(order.status),
  };
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    );
    
    const masterKey = Deno.env.get('MASTER_ENCRYPTION_KEY') ?? 'default-key-for-demo';

    const { trade_id, external_order_id, symbol, exchange, user_id } = await req.json();
    
    if (!external_order_id || !symbol) {
      throw new Error('Missing required fields: external_order_id, symbol');
    }
    
    console.log(`[confirm-trade] Confirming order ${external_order_id} for ${symbol} on ${exchange}`);
    
    // Get user credentials
    const { data: session, error: sessionError } = await supabase
      .from('aureon_user_sessions')
      .select('binance_api_key_encrypted, binance_api_secret_encrypted, binance_iv')
      .eq('user_id', user_id)
      .single();
    
    if (sessionError || !session) {
      throw new Error('User session not found');
    }
    
    let confirmResult: TradeConfirmationResult;
    
    if (exchange === 'binance' || !exchange) {
      const apiKey = decryptCredential(
        session.binance_api_key_encrypted,
        session.binance_iv || '',
        masterKey
      );
      const apiSecret = decryptCredential(
        session.binance_api_secret_encrypted,
        session.binance_iv || '',
        masterKey
      );
      
      confirmResult = await confirmBinanceOrder(external_order_id, symbol, apiKey, apiSecret);
    } else {
      throw new Error(`Exchange ${exchange} confirmation not yet implemented`);
    }
    
    console.log(`[confirm-trade] Order status: ${confirmResult.status}, executed: ${confirmResult.executedQty}`);
    
    // Update trade audit log
    const stage = confirmResult.status === 'FILLED' ? 'FILLED' :
                  confirmResult.status === 'PARTIALLY_FILLED' ? 'PARTIALLY_FILLED' :
                  confirmResult.status === 'CANCELED' ? 'CANCELED' :
                  confirmResult.status === 'REJECTED' ? 'FAILED' : 'ORDER_CONFIRMED';
    
    const validationStatus = confirmResult.isConfirmed ? 'confirmed' : 'pending';
    
    const { error: auditError } = await supabase
      .from('trade_audit_log')
      .insert({
        trade_id: trade_id || crypto.randomUUID(),
        external_order_id,
        stage,
        exchange: exchange || 'binance',
        symbol,
        side: 'UNKNOWN', // Will be updated from original trade
        quantity: confirmResult.executedQty,
        executed_qty: confirmResult.executedQty,
        executed_price: confirmResult.executedPrice,
        commission: confirmResult.commission,
        commission_asset: confirmResult.commissionAsset,
        exchange_response: confirmResult,
        validation_status: validationStatus,
        validation_message: `Order ${confirmResult.status} - Executed ${confirmResult.executedQty} @ ${confirmResult.executedPrice}`,
      });
    
    if (auditError) {
      console.error('[confirm-trade] Audit log error:', auditError);
    }
    
    // Update trading_executions if exists
    if (trade_id) {
      await supabase
        .from('trading_executions')
        .update({
          status: confirmResult.status === 'FILLED' ? 'executed' : confirmResult.status.toLowerCase(),
          executed_price: confirmResult.executedPrice,
          executed_quantity: confirmResult.executedQty,
          updated_at: new Date().toISOString(),
        })
        .eq('id', trade_id);
    }
    
    return new Response(
      JSON.stringify({
        success: true,
        confirmed: confirmResult.isConfirmed,
        orderId: confirmResult.orderId,
        status: confirmResult.status,
        executedQty: confirmResult.executedQty,
        executedPrice: confirmResult.executedPrice,
        commission: confirmResult.commission,
        commissionAsset: confirmResult.commissionAsset,
        fills: confirmResult.fills,
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  } catch (error) {
    console.error('[confirm-trade] Error:', error);
    return new Response(
      JSON.stringify({ 
        success: false, 
        confirmed: false,
        error: error instanceof Error ? error.message : 'Unknown error' 
      }),
      { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});
