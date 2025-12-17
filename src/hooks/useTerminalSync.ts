import { useEffect, useCallback, useRef } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { globalSystemsManager } from '@/core/globalSystemsManager';
import { calculateDrawdown, calculateGaiaState, calculateHncFrequency, calculateHncMarketState } from './useTerminalMetrics';

interface BalanceData {
  totalEquityUsd: number;
  exchanges: Record<string, { totalUsd: number; assets: Record<string, { free: number; locked: number; usdValue: number }> }>;
}

export function useTerminalSync(enabled: boolean = true, intervalMs: number = 10000) {
  const peakEquityRef = useRef<number>(0);
  const sessionStartRef = useRef<number>(Date.now());
  const lastSyncRef = useRef<number>(0);

  const fetchBalances = useCallback(async (): Promise<BalanceData | null> => {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return null;

      const { data, error } = await supabase.functions.invoke('get-user-balances', {
        body: { userId: user.id }
      });

      if (error) {
        console.error('[TerminalSync] Balance fetch error:', error);
        return null;
      }

      return data;
    } catch (err) {
      console.error('[TerminalSync] Balance fetch failed:', err);
      return null;
    }
  }, []);

  const fetchTradeStats = useCallback(async () => {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return null;

      // Get trade records from database
      const { data: trades, error } = await supabase
        .from('trade_records')
        .select('*')
        .order('timestamp', { ascending: false })
        .limit(500);

      if (error) {
        console.error('[TerminalSync] Trade fetch error:', error);
        return null;
      }

      if (!trades || trades.length === 0) {
        return { totalTrades: 0, wins: 0, winRate: 0, cyclePnl: 0, avgHoldTime: 0 };
      }

      // Calculate stats from trades using 'side' field (BUY/SELL)
      const buyTrades = trades.filter(t => t.side === 'BUY');
      const sellTrades = trades.filter(t => t.side === 'SELL');
      
      // Simple P&L calculation: match buys and sells by symbol (FIFO)
      let totalPnl = 0;
      let wins = 0;
      let totalHoldTime = 0;
      let matchedTrades = 0;

      const symbolBuys: Record<string, typeof trades> = {};
      buyTrades.forEach(t => {
        if (!symbolBuys[t.symbol]) symbolBuys[t.symbol] = [];
        symbolBuys[t.symbol].push(t);
      });

      sellTrades.forEach(sell => {
        const buys = symbolBuys[sell.symbol];
        if (buys && buys.length > 0) {
          const buy = buys.shift()!;
          const pnl = (sell.price - buy.price) * Math.min(sell.quantity, buy.quantity);
          totalPnl += pnl;
          if (pnl > 0) wins++;
          matchedTrades++;
          
          const holdTime = new Date(sell.timestamp).getTime() - new Date(buy.timestamp).getTime();
          totalHoldTime += holdTime;
        }
      });

      const totalTrades = trades.length;
      const winRate = matchedTrades > 0 ? (wins / matchedTrades) * 100 : 0;
      const avgHoldTime = matchedTrades > 0 ? (totalHoldTime / matchedTrades) / 60000 : 0; // in minutes

      return { totalTrades, wins, winRate, cyclePnl: totalPnl, avgHoldTime };
    } catch (err) {
      console.error('[TerminalSync] Trade stats failed:', err);
      return null;
    }
  }, []);

  const fetchOpenPositions = useCallback(async () => {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return [];

      const { data, error } = await supabase
        .from('trading_positions')
        .select('*')
        .eq('user_id', user.id)
        .eq('status', 'open');

      if (error) {
        console.error('[TerminalSync] Positions fetch error:', error);
        return [];
      }

      return data || [];
    } catch (err) {
      console.error('[TerminalSync] Positions failed:', err);
      return [];
    }
  }, []);

  const fetchSessionData = useCallback(async () => {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return null;

      const { data, error } = await supabase
        .from('aureon_user_sessions')
        .select('*')
        .eq('user_id', user.id)
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

  const syncTerminalData = useCallback(async () => {
    const now = Date.now();
    if (now - lastSyncRef.current < 5000) return; // Throttle to 5s minimum
    lastSyncRef.current = now;

    console.log('[TerminalSync] Syncing terminal data...');

    // Fetch all data in parallel
    const [balances, tradeStats, positions, session] = await Promise.all([
      fetchBalances(),
      fetchTradeStats(),
      fetchOpenPositions(),
      fetchSessionData()
    ]);

    // Calculate equity and drawdown
    const currentEquity = balances?.totalEquityUsd || 0;
    if (currentEquity > peakEquityRef.current) {
      peakEquityRef.current = currentEquity;
    }
    const drawdown = calculateDrawdown(currentEquity, peakEquityRef.current);

    // Calculate Gaia/HNC state from market data
    const coherence = session?.current_coherence || 0;
    const momentum = 0; // Would come from WebSocket data
    const volatility = 0.02; // Default

    const gaiaState = calculateGaiaState(coherence > 0.5 ? 528 : 440);
    const hncFreq = calculateHncFrequency(momentum, volatility);
    const hncMarketState = calculateHncMarketState(coherence, volatility, momentum);

    // Map positions to the expected format
    const mappedPositions = positions.map(p => ({
      symbol: p.symbol,
      entryPrice: Number(p.entry_price),
      currentPrice: Number(p.current_price) || Number(p.entry_price),
      pnlPercent: p.current_price && p.entry_price 
        ? ((Number(p.current_price) - Number(p.entry_price)) / Number(p.entry_price)) * 100 
        : 0,
      side: (p.side === 'BUY' ? 'LONG' : 'SHORT') as 'LONG' | 'SHORT',
    }));

    // Update global state with real data using public method
    globalSystemsManager.setPartialState({
      // Portfolio metrics
      totalEquity: currentEquity,
      peakEquity: peakEquityRef.current,
      currentDrawdownPercent: drawdown,
      maxDrawdownPercent: Math.max(globalSystemsManager.getState().maxDrawdownPercent, drawdown),
      
      // Trade stats
      totalTrades: tradeStats?.totalTrades || 0,
      winningTrades: tradeStats?.wins || 0,
      cyclePnl: tradeStats?.cyclePnl || 0,
      cyclePnlPercent: currentEquity > 0 ? ((tradeStats?.cyclePnl || 0) / currentEquity) * 100 : 0,
      avgHoldTimeMinutes: tradeStats?.avgHoldTime || 0,
      
      // Positions
      activePositions: mappedPositions,
      
      // Session data
      sessionStartTime: sessionStartRef.current,
      
      // Coherence/Lambda from session
      coherence: session?.current_coherence || 0,
      lambda: session?.current_lambda || 0,
      
      // Gaia/HNC state
      gaiaLatticeState: gaiaState,
      gaiaFrequency: coherence > 0.5 ? 432 : 440,
      hncFrequency: hncFreq,
      hncMarketState: hncMarketState,
      hncCoherencePercent: coherence * 100,
      
      // From session
      compoundedCapital: session?.total_pnl_usdt || 0,
      harvestedCapital: session?.gas_tank_balance || 0,
      poolAvailable: session?.available_balance_usdt || 0,
    });

    console.log('[TerminalSync] Synced:', { 
      equity: currentEquity, 
      trades: tradeStats?.totalTrades,
      positions: positions.length,
      coherence: session?.current_coherence
    });
  }, [fetchBalances, fetchTradeStats, fetchOpenPositions, fetchSessionData]);

  useEffect(() => {
    if (!enabled) return;

    // Initial sync
    syncTerminalData();

    // Set up interval
    const interval = setInterval(syncTerminalData, intervalMs);

    return () => clearInterval(interval);
  }, [enabled, intervalMs, syncTerminalData]);

  return { syncNow: syncTerminalData };
}
