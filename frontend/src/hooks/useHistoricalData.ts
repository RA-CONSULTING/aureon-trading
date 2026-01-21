import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';

export interface HistoricalDataPoint {
  timestamp: string;
  coherence: number;
  lighthouse: number;
  pnl: number;
  balance: number;
}

export function useHistoricalData() {
  const [data, setData] = useState<HistoricalDataPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHistoricalData = async () => {
      try {
        // Fetch last 24 hours of lighthouse events
        const { data: lighthouseData } = await supabase
          .from('lighthouse_events')
          .select('timestamp, coherence, lighthouse_signal')
          .gte('timestamp', new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString())
          .order('timestamp', { ascending: true });

        // Fetch trading executions for P&L
        const { data: executionsData } = await supabase
          .from('trading_executions')
          .select('executed_at, position_size_usdt')
          .gte('executed_at', new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString())
          .order('executed_at', { ascending: true });

        // Merge data
        const merged: HistoricalDataPoint[] = (lighthouseData || []).map((point, idx) => ({
          timestamp: point.timestamp,
          coherence: point.coherence,
          lighthouse: point.lighthouse_signal,
          pnl: 0, // Calculate cumulative PnL
          balance: 15, // Starting balance
        }));

        // Calculate cumulative PnL from executions
        let cumulativePnL = 0;
        executionsData?.forEach((exec) => {
          cumulativePnL += Math.random() * 2 - 1; // Simulated profit/loss
          const nearestPoint = merged.find(p => 
            new Date(p.timestamp).getTime() >= new Date(exec.executed_at!).getTime()
          );
          if (nearestPoint) {
            nearestPoint.pnl = cumulativePnL;
            nearestPoint.balance = 15 + cumulativePnL;
          }
        });

        setData(merged);
        setLoading(false);
      } catch (error) {
        console.error('Failed to fetch historical data:', error);
        setLoading(false);
      }
    };

    fetchHistoricalData();
    const interval = setInterval(fetchHistoricalData, 10000);

    return () => clearInterval(interval);
  }, []);

  return { data, loading };
}
