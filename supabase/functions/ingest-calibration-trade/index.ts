import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseKey);

    const body = await req.json();
    const { action, trade } = body;

    console.log(`[ingest-calibration-trade] Action: ${action}`);

    if (action === 'log_entry') {
      const { data, error } = await supabase
        .from('calibration_trades')
        .insert({
          temporal_id: trade.temporal_id || `trade-${Date.now()}`,
          symbol: trade.symbol,
          side: trade.side,
          entry_price: trade.entry_price,
          entry_time: trade.entry_time || new Date().toISOString(),
          quantity: trade.quantity,
          position_size_usd: trade.position_size_usd,
          frequency_band: trade.frequency_band,
          prism_frequency: trade.prism_frequency,
          coherence_at_entry: trade.coherence_at_entry,
          lambda_at_entry: trade.lambda_at_entry,
          lighthouse_confidence: trade.lighthouse_confidence,
          hnc_probability: trade.hnc_probability,
          qgita_tier: trade.qgita_tier,
          exchange: trade.exchange || 'binance',
          order_id: trade.order_id,
          regime: trade.regime || 'NORMAL',
          cosmic_phase: trade.cosmic_phase,
          is_forced: trade.is_forced || false,
          metadata: trade.metadata || {},
        })
        .select()
        .single();

      if (error) throw error;
      console.log(`[ingest-calibration-trade] Entry logged: ${data.id}`);
      return new Response(JSON.stringify({ success: true, data }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    if (action === 'log_exit') {
      const { data, error } = await supabase
        .from('calibration_trades')
        .update({
          exit_price: trade.exit_price,
          exit_time: trade.exit_time || new Date().toISOString(),
          pnl: trade.pnl,
          pnl_percent: trade.pnl_percent,
          is_win: trade.is_win,
        })
        .eq('id', trade.id)
        .select()
        .single();

      if (error) throw error;
      console.log(`[ingest-calibration-trade] Exit logged: ${data.id}, PnL: ${trade.pnl}`);
      return new Response(JSON.stringify({ success: true, data }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    if (action === 'get_calibration') {
      // Get recent trades for calibration
      const { data: trades, error } = await supabase
        .from('calibration_trades')
        .select('*')
        .not('pnl', 'is', null)
        .order('created_at', { ascending: false })
        .limit(trade?.limit || 100);

      if (error) throw error;

      // Compute calibration stats
      const totalTrades = trades.length;
      const wins = trades.filter(t => t.is_win).length;
      const winRate = totalTrades > 0 ? wins / totalTrades : 0;
      const avgPnlPercent = totalTrades > 0 
        ? trades.reduce((sum, t) => sum + (t.pnl_percent || 0), 0) / totalTrades 
        : 0;
      
      const grossProfit = trades.filter(t => (t.pnl || 0) > 0).reduce((sum, t) => sum + (t.pnl || 0), 0);
      const grossLoss = Math.abs(trades.filter(t => (t.pnl || 0) < 0).reduce((sum, t) => sum + (t.pnl || 0), 0));
      const profitFactor = grossLoss > 0 ? grossProfit / grossLoss : grossProfit > 0 ? 999 : 0;

      // Band performance
      const bandPerformance: Record<string, { trades: number; winRate: number; avgPnl: number }> = {};
      const bands = ['396Hz', '432Hz', '528Hz', '639Hz', '741Hz', '852Hz', '963Hz'];
      for (const band of bands) {
        const bandTrades = trades.filter(t => t.frequency_band === band);
        const bandWins = bandTrades.filter(t => t.is_win).length;
        bandPerformance[band] = {
          trades: bandTrades.length,
          winRate: bandTrades.length > 0 ? bandWins / bandTrades.length : 0,
          avgPnl: bandTrades.length > 0 
            ? bandTrades.reduce((sum, t) => sum + (t.pnl_percent || 0), 0) / bandTrades.length 
            : 0,
        };
      }

      // Tier performance
      const tierPerformance: Record<number, { trades: number; winRate: number; avgPnl: number }> = {};
      for (const tier of [1, 2, 3]) {
        const tierTrades = trades.filter(t => t.qgita_tier === tier);
        const tierWins = tierTrades.filter(t => t.is_win).length;
        tierPerformance[tier] = {
          trades: tierTrades.length,
          winRate: tierTrades.length > 0 ? tierWins / tierTrades.length : 0,
          avgPnl: tierTrades.length > 0 
            ? tierTrades.reduce((sum, t) => sum + (t.pnl_percent || 0), 0) / tierTrades.length 
            : 0,
        };
      }

      const calibration = {
        totalTrades,
        winRate,
        avgPnlPercent,
        profitFactor,
        bandPerformance,
        tierPerformance,
      };

      console.log(`[ingest-calibration-trade] Calibration computed: ${totalTrades} trades, ${(winRate * 100).toFixed(1)}% win rate`);
      return new Response(JSON.stringify({ success: true, calibration, trades }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    return new Response(JSON.stringify({ error: 'Invalid action' }), {
      status: 400,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    console.error('[ingest-calibration-trade] Error:', message);
    return new Response(JSON.stringify({ error: message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
