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
    const {
      signalId,
      lighthouseEventId,
      symbol,
      signalType,
      coherence,
      lighthouseValue,
      lighthouseConfidence,
      prismLevel,
      currentPrice
    } = await req.json();

    console.log('Execute trade request:', { symbol, signalType, coherence, currentPrice });

    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseKey);

    // Get trading config
    const { data: configData, error: configError } = await supabase
      .from('trading_config')
      .select('*')
      .single();

    if (configError || !configData) {
      throw new Error('Trading config not found');
    }

    // Safety checks
    if (!configData.is_enabled) {
      return new Response(
        JSON.stringify({ success: false, error: 'Trading is disabled' }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 400 }
      );
    }

    // Check signal filters
    if (coherence < configData.min_coherence) {
      return new Response(
        JSON.stringify({ success: false, error: `Coherence ${coherence} below minimum ${configData.min_coherence}` }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 400 }
      );
    }

    if (lighthouseConfidence < configData.min_lighthouse_confidence) {
      return new Response(
        JSON.stringify({ success: false, error: `Lighthouse confidence ${lighthouseConfidence} below minimum` }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 400 }
      );
    }

    if (prismLevel < configData.min_prism_level) {
      return new Response(
        JSON.stringify({ success: false, error: `Prism level ${prismLevel} below minimum ${configData.min_prism_level}` }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 400 }
      );
    }

    if (!configData.allowed_symbols.includes(symbol)) {
      return new Response(
        JSON.stringify({ success: false, error: `Symbol ${symbol} not in allowed list` }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 400 }
      );
    }

    // Check daily limits
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const { data: todayExecutions } = await supabase
      .from('trading_executions')
      .select('*')
      .gte('executed_at', today.toISOString());

    const tradeCount = todayExecutions?.length || 0;
    if (tradeCount >= configData.max_daily_trades) {
      return new Response(
        JSON.stringify({ success: false, error: `Daily trade limit reached (${tradeCount}/${configData.max_daily_trades})` }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 400 }
      );
    }

    // Calculate daily P&L
    const dailyPnL = todayExecutions?.reduce((sum, ex) => {
      return sum + (parseFloat(ex.realized_pnl as any) || 0);
    }, 0) || 0;

    if (dailyPnL < -Math.abs(configData.max_daily_loss_usdt)) {
      return new Response(
        JSON.stringify({ success: false, error: `Daily loss limit reached ($${Math.abs(dailyPnL).toFixed(2)})` }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 400 }
      );
    }

    // Calculate position size
    const positionSizeUsdt = parseFloat(configData.base_position_size_usdt as any);
    const quantity = positionSizeUsdt / currentPrice;

    // Calculate stop loss and take profit
    const stopLossPrice = signalType === 'LONG'
      ? currentPrice * (1 - parseFloat(configData.stop_loss_percentage as any) / 100)
      : currentPrice * (1 + parseFloat(configData.stop_loss_percentage as any) / 100);

    const takeProfitPrice = signalType === 'LONG'
      ? currentPrice * (1 + parseFloat(configData.take_profit_percentage as any) / 100)
      : currentPrice * (1 - parseFloat(configData.take_profit_percentage as any) / 100);

    const side = signalType === 'LONG' ? 'BUY' : 'SELL';

    let executionResult;
    if (configData.trading_mode === 'paper') {
      // Paper trading - simulate execution
      console.log('Paper trading execution:', { side, symbol, quantity, currentPrice });
      executionResult = {
        success: true,
        orderId: `PAPER_${Date.now()}`,
        executedQty: quantity.toString(),
        executedPrice: currentPrice.toString(),
        status: 'FILLED',
      };
    } else {
      // Live trading - execute on Binance
      const binanceApiKey = Deno.env.get('BINANCE_API_KEY');
      const binanceApiSecret = Deno.env.get('BINANCE_API_SECRET');

      if (!binanceApiKey || !binanceApiSecret) {
        throw new Error('Binance API credentials not configured');
      }

      // Create order on Binance
      const timestamp = Date.now();
      const queryString = `symbol=${symbol}&side=${side}&type=MARKET&quantity=${quantity.toFixed(8)}&timestamp=${timestamp}`;
      
      // Sign the request (simplified - in production use proper HMAC-SHA256)
      const crypto = await import("https://deno.land/std@0.177.0/crypto/mod.ts");
      const encoder = new TextEncoder();
      const key = await crypto.crypto.subtle.importKey(
        "raw",
        encoder.encode(binanceApiSecret),
        { name: "HMAC", hash: "SHA-256" },
        false,
        ["sign"]
      );
      const signatureBuffer = await crypto.crypto.subtle.sign(
        "HMAC",
        key,
        encoder.encode(queryString)
      );
      const signature = Array.from(new Uint8Array(signatureBuffer))
        .map(b => b.toString(16).padStart(2, '0'))
        .join('');

      const binanceResponse = await fetch(
        `https://api.binance.com/api/v3/order?${queryString}&signature=${signature}`,
        {
          method: 'POST',
          headers: {
            'X-MBX-APIKEY': binanceApiKey,
          },
        }
      );

      if (!binanceResponse.ok) {
        const errorText = await binanceResponse.text();
        throw new Error(`Binance API error: ${errorText}`);
      }

      executionResult = await binanceResponse.json();
      console.log('Live trade executed:', executionResult);
    }

    // Save execution to database
    const { data: execution, error: execError } = await supabase
      .from('trading_executions')
      .insert({
        signal_id: signalId,
        lighthouse_event_id: lighthouseEventId,
        symbol,
        side,
        signal_type: signalType,
        order_type: 'MARKET',
        quantity,
        price: currentPrice,
        executed_price: parseFloat(executionResult.executedPrice || currentPrice),
        position_size_usdt: positionSizeUsdt,
        stop_loss_price: stopLossPrice,
        take_profit_price: takeProfitPrice,
        status: 'filled',
        exchange_order_id: executionResult.orderId,
        coherence,
        lighthouse_value: lighthouseValue,
        lighthouse_confidence: lighthouseConfidence,
        prism_level: prismLevel,
      })
      .select()
      .single();

    if (execError) {
      console.error('Error saving execution:', execError);
      throw execError;
    }

    // Create position
    await supabase
      .from('trading_positions')
      .insert({
        execution_id: execution.id,
        symbol,
        side: signalType,
        entry_price: currentPrice,
        quantity,
        position_value_usdt: positionSizeUsdt,
        stop_loss_price: stopLossPrice,
        take_profit_price: takeProfitPrice,
        current_price: currentPrice,
        status: 'open',
      });

    console.log('Trade executed successfully:', execution.id);

    return new Response(
      JSON.stringify({
        success: true,
        execution: execution,
        message: `${configData.trading_mode === 'paper' ? 'Paper' : 'Live'} trade executed: ${side} ${quantity.toFixed(8)} ${symbol} @ $${currentPrice.toFixed(2)}`
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    console.error('Execute trade error:', error);
    return new Response(
      JSON.stringify({ success: false, error: error instanceof Error ? error.message : 'Unknown error' }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
    );
  }
});
