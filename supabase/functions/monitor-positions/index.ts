import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

interface BinanceTickerResponse {
  symbol: string;
  price: string;
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

    console.log('🔍 Monitoring positions...');

    // Get all open positions
    const { data: positions, error: positionsError } = await supabase
      .from('trading_positions')
      .select('*')
      .eq('status', 'open');

    if (positionsError) throw positionsError;

    if (!positions || positions.length === 0) {
      console.log('No open positions to monitor');
      return new Response(
        JSON.stringify({ success: true, message: 'No open positions', monitored: 0 }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    console.log(`Monitoring ${positions.length} open positions`);

    // Get current prices for all symbols
    const symbols = [...new Set(positions.map(p => p.symbol))];
    const priceUpdates: { symbol: string; price: number }[] = [];

    for (const symbol of symbols) {
      try {
        const response = await fetch(`https://api.binance.com/api/v3/ticker/price?symbol=${symbol}`);
        const data: BinanceTickerResponse = await response.json();
        priceUpdates.push({ symbol, price: parseFloat(data.price) });
      } catch (error) {
        console.error(`Failed to fetch price for ${symbol}:`, error);
      }
    }

    const closedPositions: any[] = [];
    const updatedPositions: any[] = [];

    // Check each position
    for (const position of positions) {
      const priceData = priceUpdates.find(p => p.symbol === position.symbol);
      if (!priceData) continue;

      const currentPrice = priceData.price;
      const entryPrice = parseFloat(position.entry_price);
      const quantity = parseFloat(position.quantity);

      // Calculate unrealized P&L
      let unrealizedPnL = 0;
      if (position.side === 'LONG') {
        unrealizedPnL = (currentPrice - entryPrice) * quantity;
      } else {
        unrealizedPnL = (entryPrice - currentPrice) * quantity;
      }

      let shouldClose = false;
      let closeReason = '';

      // Check stop-loss
      if (position.stop_loss_price) {
        const stopLoss = parseFloat(position.stop_loss_price);
        if (position.side === 'LONG' && currentPrice <= stopLoss) {
          shouldClose = true;
          closeReason = 'STOP_LOSS';
          console.log(`🛑 Stop-loss hit for ${position.symbol} (${position.side}): ${currentPrice} <= ${stopLoss}`);
        } else if (position.side === 'SHORT' && currentPrice >= stopLoss) {
          shouldClose = true;
          closeReason = 'STOP_LOSS';
          console.log(`🛑 Stop-loss hit for ${position.symbol} (${position.side}): ${currentPrice} >= ${stopLoss}`);
        }
      }

      // Check take-profit
      if (position.take_profit_price && !shouldClose) {
        const takeProfit = parseFloat(position.take_profit_price);
        if (position.side === 'LONG' && currentPrice >= takeProfit) {
          shouldClose = true;
          closeReason = 'TAKE_PROFIT';
          console.log(`🎯 Take-profit hit for ${position.symbol} (${position.side}): ${currentPrice} >= ${takeProfit}`);
        } else if (position.side === 'SHORT' && currentPrice <= takeProfit) {
          shouldClose = true;
          closeReason = 'TAKE_PROFIT';
          console.log(`🎯 Take-profit hit for ${position.symbol} (${position.side}): ${currentPrice} <= ${takeProfit}`);
        }
      }

      if (shouldClose) {
        // Close the position
        const { error: closeError } = await supabase
          .from('trading_positions')
          .update({
            status: 'closed',
            closed_at: new Date().toISOString(),
            close_reason: closeReason,
            current_price: currentPrice,
            realized_pnl: unrealizedPnL,
            updated_at: new Date().toISOString(),
          })
          .eq('id', position.id);

        if (closeError) {
          console.error(`Failed to close position ${position.id}:`, closeError);
        } else {
          closedPositions.push({
            symbol: position.symbol,
            side: position.side,
            reason: closeReason,
            pnl: unrealizedPnL,
            entryPrice,
            exitPrice: currentPrice,
          });
        }
      } else {
        // Update current price and unrealized P&L
        const { error: updateError } = await supabase
          .from('trading_positions')
          .update({
            current_price: currentPrice,
            unrealized_pnl: unrealizedPnL,
            updated_at: new Date().toISOString(),
          })
          .eq('id', position.id);

        if (updateError) {
          console.error(`Failed to update position ${position.id}:`, updateError);
        } else {
          updatedPositions.push({
            symbol: position.symbol,
            currentPrice,
            unrealizedPnL,
          });
        }
      }
    }

    console.log(`✅ Monitoring complete: ${updatedPositions.length} updated, ${closedPositions.length} closed`);

    return new Response(
      JSON.stringify({
        success: true,
        monitored: positions.length,
        updated: updatedPositions.length,
        closed: closedPositions.length,
        closedPositions,
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  } catch (error) {
    console.error('Position monitoring error:', error);
    return new Response(
      JSON.stringify({ success: false, error: error instanceof Error ? error.message : 'Unknown error' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});
