/**
 * Ingest Terminal State
 * Prime Sentinel: GARY LECKEY 02111991
 * 
 * Receives comprehensive terminal state from Python system
 * and updates all relevant database tables for web dashboard mirroring
 */

import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

interface TerminalState {
  user_id: string;
  
  // Portfolio
  portfolio_value: number;
  peak_equity: number;
  current_drawdown: number;
  max_drawdown: number;
  
  // Trades
  trades?: Array<{
    symbol: string;
    side: string;
    price: number;
    quantity: number;
    fee?: number;
    fee_asset?: string;
    timestamp: string;
    transaction_id?: string;
    pnl?: number;
    is_win?: boolean;
    exchange?: string;
  }>;
  total_trades: number;
  wins: number;
  win_rate: number;
  avg_hold_time?: number;
  
  // Positions
  positions?: Array<{
    symbol: string;
    side: string;
    entry_price: number;
    quantity: number;
    current_price?: number;
    unrealized_pnl?: number;
  }>;
  
  // Coherence/HNC/Gaia
  coherence: number;
  lambda?: number;
  gaia_state: string;
  gaia_frequency: number;
  gaia_purity?: number;
  gaia_carrier_phi?: number;
  gaia_432_lock?: number;
  hnc_frequency: number;
  hnc_market_state: string;
  hnc_coherence_percent?: number;
  hnc_modifier?: number;
  
  // Mycelium
  mycelium_hives: number;
  mycelium_agents: number;
  mycelium_generation: number;
  max_generation?: number;
  queen_state: string;
  queen_pnl?: number;
  
  // Capital
  compounded: number;
  harvested: number;
  pool_total?: number;
  pool_available: number;
  scout_count?: number;
  split_count?: number;
  
  // Trading Mode
  trading_mode: string;
  entry_threshold?: number;
  exit_threshold?: number;
  risk_multiplier?: number;
  tp_multiplier?: number;
  
  // Meta
  runtime_minutes: number;
  ws_connected?: boolean;
  ws_message_count?: number;
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseKey);

    const state: TerminalState = await req.json();
    
    if (!state.user_id) {
      return new Response(JSON.stringify({ error: 'user_id required' }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    console.log('[IngestTerminalState] Received from Python:', {
      user_id: state.user_id,
      portfolio: state.portfolio_value,
      trades: state.total_trades,
      wins: state.wins,
      coherence: state.coherence,
      runtime: state.runtime_minutes
    });

    const now = new Date().toISOString();
    const results: Record<string, any> = {};

    // 1. Update aureon_user_sessions with all metrics
    const { error: sessionError } = await supabase
      .from('aureon_user_sessions')
      .upsert({
        user_id: state.user_id,
        total_equity_usdt: state.portfolio_value,
        available_balance_usdt: state.pool_available,
        total_pnl_usdt: state.compounded,
        gas_tank_balance: state.harvested,
        current_coherence: state.coherence,
        current_lambda: state.lambda || 0,
        current_lighthouse_signal: state.hnc_frequency,
        prism_state: state.gaia_state,
        prism_level: state.gaia_frequency,
        dominant_node: state.queen_state,
        total_trades: state.total_trades,
        winning_trades: state.wins,
        trading_mode: state.trading_mode,
        is_trading_active: true,
        updated_at: now,
      }, { onConflict: 'user_id' });

    if (sessionError) {
      console.error('[IngestTerminalState] Session update error:', sessionError);
      results.session = { error: sessionError.message };
    } else {
      results.session = { updated: true };
    }

    // 2. Upsert trades if provided
    if (state.trades && state.trades.length > 0) {
      const tradeRecords = state.trades.map(t => ({
        user_id: state.user_id,
        symbol: t.symbol,
        side: t.side.toUpperCase(),
        price: t.price,
        quantity: t.quantity,
        quote_qty: t.price * t.quantity,
        fee: t.fee || 0,
        fee_asset: t.fee_asset || 'USDT',
        exchange: t.exchange || 'binance',
        timestamp: t.timestamp,
        transaction_id: t.transaction_id || `py_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        pnl: t.pnl || null,
        is_win: t.is_win || null,
      }));

      const { error: tradesError, count } = await supabase
        .from('trade_records')
        .upsert(tradeRecords, { 
          onConflict: 'transaction_id',
          ignoreDuplicates: true 
        });

      if (tradesError) {
        console.error('[IngestTerminalState] Trades upsert error:', tradesError);
        results.trades = { error: tradesError.message };
      } else {
        results.trades = { upserted: tradeRecords.length };
      }
    }

    // 3. Upsert positions if provided
    if (state.positions && state.positions.length > 0) {
      // First, close any positions not in the current list
      const currentSymbols = state.positions.map(p => p.symbol);
      
      await supabase
        .from('trading_positions')
        .update({ status: 'closed', updated_at: now })
        .eq('user_id', state.user_id)
        .eq('status', 'open')
        .not('symbol', 'in', `(${currentSymbols.join(',')})`);

      // Upsert current positions
      for (const pos of state.positions) {
        const { error: posError } = await supabase
          .from('trading_positions')
          .upsert({
            user_id: state.user_id,
            symbol: pos.symbol,
            side: pos.side.toUpperCase(),
            entry_price: pos.entry_price,
            quantity: pos.quantity,
            current_price: pos.current_price || pos.entry_price,
            unrealized_pnl: pos.unrealized_pnl || 0,
            status: 'open',
            exchange: 'binance',
            updated_at: now,
          }, { 
            onConflict: 'user_id,symbol',
          });

        if (posError) {
          console.error('[IngestTerminalState] Position upsert error:', posError);
        }
      }
      results.positions = { upserted: state.positions.length };
    }

    // 4. Insert HNC detection state
    const { error: hncError } = await supabase
      .from('hnc_detection_states')
      .insert({
        temporal_id: `python_${state.user_id}_${Date.now()}`,
        harmonic_fidelity: state.hnc_coherence_percent || state.coherence * 100,
        imperial_yield: state.hnc_modifier || 1.0,
        bridge_status: state.hnc_market_state,
        schumann_power: state.gaia_frequency,
        love_power: state.gaia_432_lock || 0,
        anchor_power: state.coherence,
        unity_power: state.lambda || 0,
        distortion_power: state.gaia_state === 'DISTORTION' ? 1 : 0,
        is_lighthouse_detected: state.coherence > 0.45,
        timestamp: now,
      });

    if (hncError) {
      console.error('[IngestTerminalState] HNC insert error:', hncError);
      results.hnc = { error: hncError.message };
    } else {
      results.hnc = { inserted: true };
    }

    // 5. Store runtime/mycelium state in a system stats record
    const runtimeStats = {
      user_id: state.user_id,
      runtime_minutes: state.runtime_minutes,
      peak_equity: state.peak_equity,
      current_drawdown: state.current_drawdown,
      max_drawdown: state.max_drawdown,
      mycelium_hives: state.mycelium_hives,
      mycelium_agents: state.mycelium_agents,
      mycelium_generation: state.mycelium_generation,
      max_generation: state.max_generation || 0,
      queen_state: state.queen_state,
      queen_pnl: state.queen_pnl || 0,
      scout_count: state.scout_count || 0,
      split_count: state.split_count || 0,
      entry_threshold: state.entry_threshold || 0.2,
      exit_threshold: state.exit_threshold || 0.15,
      risk_multiplier: state.risk_multiplier || 0.5,
      tp_multiplier: state.tp_multiplier || 0.8,
      ws_connected: state.ws_connected || false,
      ws_message_count: state.ws_message_count || 0,
      gaia_purity: state.gaia_purity || 0,
      gaia_carrier_phi: state.gaia_carrier_phi || 0,
      timestamp: now,
    };

    // Store in local_system_logs as JSON for now (can create dedicated table later)
    const { error: statsError } = await supabase
      .from('local_system_logs')
      .insert({
        module: 'terminal_state',
        log_type: 'runtime_stats',
        level: 'INFO',
        message: JSON.stringify(runtimeStats),
        parsed_data: runtimeStats,
        timestamp: now,
      });

    if (statsError) {
      console.error('[IngestTerminalState] Stats insert error:', statsError);
      results.stats = { error: statsError.message };
    } else {
      results.stats = { inserted: true };
    }

    console.log('[IngestTerminalState] Completed:', results);

    return new Response(JSON.stringify({
      success: true,
      timestamp: now,
      results,
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });

  } catch (error) {
    console.error('[IngestTerminalState] Error:', error);
    return new Response(JSON.stringify({
      success: false,
      error: error instanceof Error ? error.message : String(error)
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
});
