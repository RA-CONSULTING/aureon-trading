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
    const temporalId = body.temporal_id || `kelly_${Date.now()}`;
    
    console.log('[ingest-kelly-computation] Computing Kelly from calibration_trades...');

    // Fetch recent calibration trades to compute Kelly
    const { data: trades, error: fetchError } = await supabase
      .from('calibration_trades')
      .select('pnl, pnl_percent, is_win')
      .order('created_at', { ascending: false })
      .limit(100);

    if (fetchError) {
      console.error('[ingest-kelly-computation] Fetch error:', fetchError);
      throw fetchError;
    }

    // Calculate Kelly inputs
    const totalTrades = trades?.length || 0;
    const winningTrades = trades?.filter(t => t.is_win === true).length || 0;
    const losingTrades = trades?.filter(t => t.is_win === false).length || 0;
    
    const winRate = totalTrades > 0 ? winningTrades / totalTrades : 0.5;
    
    // Calculate average win and loss
    const wins = trades?.filter(t => t.is_win === true && t.pnl_percent) || [];
    const losses = trades?.filter(t => t.is_win === false && t.pnl_percent) || [];
    
    const avgWin = wins.length > 0 
      ? wins.reduce((sum, t) => sum + Math.abs(t.pnl_percent || 0), 0) / wins.length 
      : 1.2; // Default 1.2% take profit
    
    const avgLoss = losses.length > 0 
      ? losses.reduce((sum, t) => sum + Math.abs(t.pnl_percent || 0), 0) / losses.length 
      : 0.8; // Default 0.8% stop loss
    
    // Win/Loss ratio (odds)
    const winLossRatio = avgLoss > 0 ? avgWin / avgLoss : 1.5;

    // Kelly Criterion: f* = (bp - q) / b
    // where b = win/loss ratio, p = win rate, q = loss rate (1-p)
    // f* = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio
    const b = winLossRatio;
    const p = winRate;
    const q = 1 - p;
    
    let kellyFraction = (b * p - q) / b;
    
    // Clamp Kelly to reasonable bounds
    kellyFraction = Math.max(0, Math.min(kellyFraction, 0.25)); // Max 25%
    
    const kellyHalf = kellyFraction / 2;
    const kellyQuarter = kellyFraction / 4;
    
    // Recommended position (half-Kelly for safety)
    const recommendedPct = Math.max(0.5, Math.min(kellyHalf * 100, 5)); // 0.5% to 5%

    console.log(`[ingest-kelly-computation] Trades: ${totalTrades}, WinRate: ${(winRate * 100).toFixed(1)}%, Kelly: ${(kellyFraction * 100).toFixed(2)}%`);

    const record = {
      temporal_id: temporalId,
      total_trades: totalTrades,
      winning_trades: winningTrades,
      losing_trades: losingTrades,
      win_rate: winRate,
      avg_win: avgWin,
      avg_loss: avgLoss,
      win_loss_ratio: winLossRatio,
      kelly_fraction: kellyFraction,
      kelly_half: kellyHalf,
      kelly_quarter: kellyQuarter,
      recommended_position_pct: recommendedPct,
      max_position_pct: 5,
      min_position_pct: 0.5,
      metadata: {
        computed_at: new Date().toISOString(),
        trades_analyzed: totalTrades,
      },
    };

    const { data, error } = await supabase
      .from('kelly_computation_states')
      .insert(record)
      .select()
      .single();

    if (error) {
      console.error('[ingest-kelly-computation] Insert error:', error);
      throw error;
    }

    console.log('[ingest-kelly-computation] Inserted:', data.id);

    return new Response(JSON.stringify({ 
      success: true, 
      id: data.id,
      kelly_fraction: kellyFraction,
      recommended_position_pct: recommendedPct,
      win_rate: winRate,
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });

  } catch (error) {
    console.error('[ingest-kelly-computation] Error:', error);
    const message = error instanceof Error ? error.message : 'Unknown error';
    return new Response(JSON.stringify({ error: message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
