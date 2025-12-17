/**
 * Terminal Sync Hook
 * Prime Sentinel: GARY LECKEY 02111991
 * 
 * Reads REAL data from database tables populated by Python terminal
 * via ingest-terminal-state endpoint
 * 
 * PUBLIC LIVE FEED - No authentication required
 */

import { useEffect, useCallback, useRef } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { globalSystemsManager } from '@/core/globalSystemsManager';

// Public live feed user ID - data pushed from Python terminal
const LIVE_FEED_USER_ID = '69e5567f-7ad1-42af-860f-3709ef1f5935';

interface RuntimeStats {
  runtime_minutes: number;
  peak_equity: number;
  current_drawdown: number;
  max_drawdown: number;
  mycelium_hives: number;
  mycelium_agents: number;
  mycelium_generation: number;
  max_generation: number;
  queen_state: string;
  queen_pnl: number;
  scout_count: number;
  split_count: number;
  entry_threshold: number;
  exit_threshold: number;
  risk_multiplier: number;
  tp_multiplier: number;
  ws_connected: boolean;
  ws_message_count: number;
  gaia_purity: number;
  gaia_carrier_phi: number;
}

export function useTerminalSync(enabled: boolean = true, intervalMs: number = 5000) {
  const lastSyncRef = useRef<number>(0);
  const sessionStartRef = useRef<number>(Date.now());

  // Fetch session data from aureon_user_sessions (populated by Python)
  const fetchSessionData = useCallback(async () => {
    try {
      const { data, error } = await supabase
        .from('aureon_user_sessions')
        .select('*')
        .eq('user_id', LIVE_FEED_USER_ID)
        .single();

      if (error && error.code !== 'PGRST116') {
        console.error('[TerminalSync] Session fetch error:', error);
        return null;
      }

      return data;
    } catch (err) {
      console.error('[TerminalSync] Session failed:', err);
      return null;
    }
  }, []);

  // Fetch latest HNC state (populated by Python)
  const fetchHncState = useCallback(async () => {
    try {
      const { data, error } = await supabase
        .from('hnc_detection_states')
        .select('*')
        .order('timestamp', { ascending: false })
        .limit(1)
        .single();

      if (error && error.code !== 'PGRST116') {
        return null;
      }

      return data;
    } catch (err) {
      return null;
    }
  }, []);

  // Fetch trade statistics from trade_records (populated by Python)
  const fetchTradeStats = useCallback(async () => {
    try {
      const { data: trades, error } = await supabase
        .from('trade_records')
        .select('id, is_win, pnl')
        .eq('user_id', LIVE_FEED_USER_ID);

      if (error || !trades) {
        return { total: 0, wins: 0, winRate: 0, totalPnl: 0 };
      }

      const total = trades.length;
      const wins = trades.filter(t => t.is_win === true).length;
      const winRate = total > 0 ? (wins / total) * 100 : 0;
      const totalPnl = trades.reduce((sum, t) => sum + (t.pnl || 0), 0);

      return { total, wins, winRate, totalPnl };
    } catch (err) {
      return { total: 0, wins: 0, winRate: 0, totalPnl: 0 };
    }
  }, []);

  // Fetch open positions (populated by Python)
  const fetchPositions = useCallback(async () => {
    try {
      const { data, error } = await supabase
        .from('trading_positions')
        .select('*')
        .eq('user_id', LIVE_FEED_USER_ID)
        .eq('status', 'open');

      if (error) return [];
      return data || [];
    } catch (err) {
      return [];
    }
  }, []);

  // Fetch latest runtime stats from local_system_logs
  const fetchRuntimeStats = useCallback(async (): Promise<RuntimeStats | null> => {
    try {
      const { data, error } = await supabase
        .from('local_system_logs')
        .select('parsed_data')
        .eq('module', 'terminal_state')
        .eq('log_type', 'runtime_stats')
        .order('timestamp', { ascending: false })
        .limit(1)
        .single();

      if (error || !data?.parsed_data) return null;
      
      const stats = data.parsed_data as unknown as RuntimeStats;
      if (stats && typeof stats.runtime_minutes === 'number') {
        return stats;
      }
      return null;
    } catch (err) {
      return null;
    }
  }, []);

  const syncTerminalData = useCallback(async () => {
    const now = Date.now();
    if (now - lastSyncRef.current < 3000) return; // Throttle to 3s minimum
    lastSyncRef.current = now;

    // Fetch all data in parallel from DB (populated by Python)
    const [session, hncState, tradeStats, positions, runtimeStats] = await Promise.all([
      fetchSessionData(),
      fetchHncState(),
      fetchTradeStats(),
      fetchPositions(),
      fetchRuntimeStats(),
    ]);

    if (!session) {
      console.log('[TerminalSync] No session data - waiting for Python to push...');
      return;
    }

    // Map positions to display format
    const mappedPositions = positions.map(p => ({
      symbol: p.symbol,
      entryPrice: Number(p.entry_price),
      currentPrice: Number(p.current_price) || Number(p.entry_price),
      pnlPercent: p.current_price && p.entry_price 
        ? ((Number(p.current_price) - Number(p.entry_price)) / Number(p.entry_price)) * 100 
        : 0,
      side: (p.side === 'BUY' ? 'LONG' : 'SHORT') as 'LONG' | 'SHORT',
    }));

    // Determine Gaia state from HNC data
    const gaiaState = hncState?.distortion_power > 0 ? 'DISTORTION' : 
                      (session.current_coherence || 0) > 0.45 ? 'COHERENT' : 'NEUTRAL';

    // Update global state with REAL data from Python
    globalSystemsManager.setPartialState({
      // Portfolio from session (pushed by Python)
      totalEquity: session.total_equity_usdt || 0,
      peakEquity: runtimeStats?.peak_equity || session.total_equity_usdt || 0,
      currentDrawdownPercent: runtimeStats?.current_drawdown || 0,
      maxDrawdownPercent: runtimeStats?.max_drawdown || 0,
      
      // Trade stats from trade_records (pushed by Python)
      totalTrades: session.total_trades || tradeStats.total,
      winningTrades: session.winning_trades || tradeStats.wins,
      cyclePnl: tradeStats.totalPnl || session.total_pnl_usdt || 0,
      cyclePnlPercent: session.total_equity_usdt > 0 
        ? ((tradeStats.totalPnl || 0) / session.total_equity_usdt) * 100 
        : 0,
      
      // Positions from trading_positions (pushed by Python)
      activePositions: mappedPositions,
      
      // Session timing
      sessionStartTime: sessionStartRef.current,
      
      // Coherence/Lambda from session
      coherence: session.current_coherence || 0,
      lambda: session.current_lambda || 0,
      
      // Gaia state
      gaiaLatticeState: gaiaState as 'COHERENT' | 'DISTORTION' | 'NEUTRAL',
      gaiaFrequency: hncState?.schumann_power || (session.prism_level || 440),
      purityPercent: runtimeStats?.gaia_purity || 0,
      carrierWavePhi: runtimeStats?.gaia_carrier_phi || 0,
      harmonicLock432: hncState?.love_power || 0,
      
      // HNC state
      hncFrequency: session.current_lighthouse_signal || 318,
      hncMarketState: (hncState?.bridge_status || 'CONSOLIDATION') as 'CONSOLIDATION' | 'TRENDING' | 'VOLATILE' | 'BREAKOUT',
      hncCoherencePercent: hncState?.harmonic_fidelity || (session.current_coherence || 0) * 100,
      hncModifier: hncState?.imperial_yield || 0.8,
      
      // Trading mode
      tradingMode: (session.trading_mode || 'BALANCED') as 'AGGRESSIVE' | 'CONSERVATIVE' | 'BALANCED',
      entryCoherenceThreshold: runtimeStats?.entry_threshold || 0.2,
      exitCoherenceThreshold: runtimeStats?.exit_threshold || 0.15,
      riskMultiplier: runtimeStats?.risk_multiplier || 0.5,
      takeProfitMultiplier: runtimeStats?.tp_multiplier || 0.8,
      
      // Mycelium swarm
      myceliumHives: runtimeStats?.mycelium_hives || 1,
      myceliumAgents: runtimeStats?.mycelium_agents || 5,
      myceliumGeneration: runtimeStats?.mycelium_generation || 0,
      maxGeneration: runtimeStats?.max_generation || 0,
      queenState: (runtimeStats?.queen_state || session.dominant_node || 'HOLD') as 'HOLD' | 'BUY' | 'SELL',
      queenPnl: runtimeStats?.queen_pnl || 0,
      
      // Capital
      compoundedCapital: session.total_pnl_usdt || 0,
      harvestedCapital: session.gas_tank_balance || 0,
      poolAvailable: session.available_balance_usdt || 0,
      scoutCount: runtimeStats?.scout_count || 0,
      splitCount: runtimeStats?.split_count || 0,
      
      // WebSocket (from runtime stats)
      wsConnected: runtimeStats?.ws_connected || false,
      wsMessageCount: runtimeStats?.ws_message_count || 0,
    });

    console.log('[TerminalSync] DB data synced:', { 
      equity: (session.total_equity_usdt || 0).toFixed(2),
      trades: session.total_trades || tradeStats.total,
      wins: session.winning_trades || tradeStats.wins,
      winRate: ((session.winning_trades || tradeStats.wins) / Math.max(1, session.total_trades || tradeStats.total) * 100).toFixed(1) + '%',
      coherence: ((session.current_coherence || 0) * 100).toFixed(1) + '%',
      positions: positions.length,
    });
  }, [fetchSessionData, fetchHncState, fetchTradeStats, fetchPositions, fetchRuntimeStats]);

  useEffect(() => {
    if (!enabled) return;

    // Initial sync
    syncTerminalData();

    // Set up interval for continuous sync
    const interval = setInterval(syncTerminalData, intervalMs);

    return () => clearInterval(interval);
  }, [enabled, intervalMs, syncTerminalData]);

  return { syncNow: syncTerminalData };
}