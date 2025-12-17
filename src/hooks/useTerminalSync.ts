import { useEffect, useCallback, useRef } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { globalSystemsManager } from '@/core/globalSystemsManager';
import { calculateDrawdown, calculateGaiaState, calculateHncFrequency, calculateHncMarketState } from './useTerminalMetrics';

interface BalanceData {
  totalEquityUsd: number;
  exchanges: Record<string, { totalUsd: number; assets: Record<string, { free: number; locked: number; usdValue: number }> }>;
}

interface TradeRecord {
  id: string;
  side: string;
  price: number;
  quantity: number;
  symbol: string;
  timestamp: string;
  quote_qty: number;
  fee: number;
}

export function useTerminalSync(enabled: boolean = true, intervalMs: number = 10000) {
  const peakEquityRef = useRef<number>(0);
  const sessionStartRef = useRef<number>(Date.now());
  const lastSyncRef = useRef<number>(0);
  const tradeSyncedRef = useRef<boolean>(false);

  // Fetch REAL balances from exchanges via edge function
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

      console.log('[TerminalSync] Real balances:', data);
      return data;
    } catch (err) {
      console.error('[TerminalSync] Balance fetch failed:', err);
      return null;
    }
  }, []);

  // Sync REAL trades from Binance API via edge function, then query DB
  const syncAndFetchTrades = useCallback(async (): Promise<TradeRecord[]> => {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return [];

      // First, sync trades from Binance (only once per session to avoid rate limits)
      if (!tradeSyncedRef.current) {
        console.log('[TerminalSync] Syncing trades from Binance...');
        const { data: syncResult, error: syncError } = await supabase.functions.invoke('fetch-trades', {
          body: { limit: 200 }  // Auto-detect symbols from balances
        });

        if (syncError) {
          console.error('[TerminalSync] Trade sync error:', syncError);
        } else {
          console.log('[TerminalSync] Synced trades from Binance:', syncResult?.count);
          tradeSyncedRef.current = true;
        }
      }

      // Now fetch from database
      const { data: trades, error } = await supabase
        .from('trade_records')
        .select('*')
        .eq('user_id', user.id)
        .order('timestamp', { ascending: false })
        .limit(500);

      if (error) {
        console.error('[TerminalSync] Trade fetch error:', error);
        return [];
      }

      return (trades || []) as TradeRecord[];
    } catch (err) {
      console.error('[TerminalSync] Trade sync failed:', err);
      return [];
    }
  }, []);

  // Calculate trade statistics from real trade history
  const calculateTradeStats = useCallback((trades: TradeRecord[]) => {
    if (!trades || trades.length === 0) {
      return { totalTrades: 0, wins: 0, winRate: 0, cyclePnl: 0, avgHoldTime: 0 };
    }

    const buyTrades = trades.filter(t => t.side === 'BUY');
    const sellTrades = trades.filter(t => t.side === 'SELL');
    
    // FIFO matching for P&L calculation
    let totalPnl = 0;
    let wins = 0;
    let totalHoldTime = 0;
    let matchedTrades = 0;

    const symbolBuys: Record<string, TradeRecord[]> = {};
    buyTrades.forEach(t => {
      if (!symbolBuys[t.symbol]) symbolBuys[t.symbol] = [];
      symbolBuys[t.symbol].push(t);
    });

    sellTrades.forEach(sell => {
      const buys = symbolBuys[sell.symbol];
      if (buys && buys.length > 0) {
        const buy = buys.shift()!;
        const qty = Math.min(sell.quantity, buy.quantity);
        const pnl = (sell.price - buy.price) * qty;
        totalPnl += pnl;
        if (pnl > 0) wins++;
        matchedTrades++;
        
        const holdTime = new Date(sell.timestamp).getTime() - new Date(buy.timestamp).getTime();
        totalHoldTime += holdTime;
      }
    });

    const totalTrades = trades.length;
    const winRate = matchedTrades > 0 ? (wins / matchedTrades) * 100 : 0;
    const avgHoldTime = matchedTrades > 0 ? (totalHoldTime / matchedTrades) / 60000 : 0;

    return { totalTrades, wins, winRate, cyclePnl: totalPnl, avgHoldTime };
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

    console.log('[TerminalSync] Syncing REAL terminal data...');

    // Fetch all data in parallel
    const [balances, trades, positions, session] = await Promise.all([
      fetchBalances(),
      syncAndFetchTrades(),
      fetchOpenPositions(),
      fetchSessionData()
    ]);

    // Calculate trade stats from REAL trade history
    const tradeStats = calculateTradeStats(trades);

    // Calculate equity and drawdown from REAL balances
    const currentEquity = balances?.totalEquityUsd || 0;
    if (currentEquity > peakEquityRef.current) {
      peakEquityRef.current = currentEquity;
    }
    const drawdown = calculateDrawdown(currentEquity, peakEquityRef.current);

    // Calculate Gaia/HNC state
    const coherence = session?.current_coherence || 0;
    const gaiaState = calculateGaiaState(coherence > 0.5 ? 528 : 440);
    const hncFreq = calculateHncFrequency(0, 0.02);
    const hncMarketState = calculateHncMarketState(coherence, 0.02, 0);

    // Map positions
    const mappedPositions = positions.map(p => ({
      symbol: p.symbol,
      entryPrice: Number(p.entry_price),
      currentPrice: Number(p.current_price) || Number(p.entry_price),
      pnlPercent: p.current_price && p.entry_price 
        ? ((Number(p.current_price) - Number(p.entry_price)) / Number(p.entry_price)) * 100 
        : 0,
      side: (p.side === 'BUY' ? 'LONG' : 'SHORT') as 'LONG' | 'SHORT',
    }));

    // Update global state with REAL data
    globalSystemsManager.setPartialState({
      // Portfolio metrics from REAL exchange balances
      totalEquity: currentEquity,
      peakEquity: peakEquityRef.current,
      currentDrawdownPercent: drawdown,
      maxDrawdownPercent: Math.max(globalSystemsManager.getState().maxDrawdownPercent, drawdown),
      
      // Trade stats from REAL Binance trade history
      totalTrades: tradeStats.totalTrades,
      winningTrades: tradeStats.wins,
      cyclePnl: tradeStats.cyclePnl,
      cyclePnlPercent: currentEquity > 0 ? (tradeStats.cyclePnl / currentEquity) * 100 : 0,
      avgHoldTimeMinutes: tradeStats.avgHoldTime,
      
      // Positions
      activePositions: mappedPositions,
      
      // Session timing
      sessionStartTime: sessionStartRef.current,
      
      // Coherence/Lambda from user session
      coherence: session?.current_coherence || 0,
      lambda: session?.current_lambda || 0,
      
      // Gaia/HNC state
      gaiaLatticeState: gaiaState,
      gaiaFrequency: coherence > 0.5 ? 432 : 440,
      hncFrequency: hncFreq,
      hncMarketState: hncMarketState,
      hncCoherencePercent: coherence * 100,
      
      // Capital from session
      compoundedCapital: session?.total_pnl_usdt || 0,
      harvestedCapital: session?.gas_tank_balance || 0,
      poolAvailable: session?.available_balance_usdt || 0,
    });

    console.log('[TerminalSync] REAL data synced:', { 
      equity: currentEquity.toFixed(2),
      trades: tradeStats.totalTrades,
      wins: tradeStats.wins,
      winRate: tradeStats.winRate.toFixed(1) + '%',
      pnl: tradeStats.cyclePnl.toFixed(2),
      coherence: (coherence * 100).toFixed(1) + '%'
    });
  }, [fetchBalances, syncAndFetchTrades, fetchOpenPositions, fetchSessionData, calculateTradeStats]);

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
