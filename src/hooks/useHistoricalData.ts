import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';

export interface HistoricalPoint {
  timestamp: string;
  value: number;
}

export interface HistoricalData {
  coherence: HistoricalPoint[];
  tradeVolume: HistoricalPoint[];
  cumulativePnL: HistoricalPoint[];
  isLoading: boolean;
}

export function useHistoricalData() {
  const [data, setData] = useState<HistoricalData>({
    coherence: [],
    tradeVolume: [],
    cumulativePnL: [],
    isLoading: true,
  });

  useEffect(() => {
    const fetchData = async () => {
      const now = new Date();
      const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);

      try {
        // Fetch coherence history
        const { data: coherenceData } = await supabase
          .from('lighthouse_events')
          .select('timestamp, coherence')
          .gte('timestamp', oneDayAgo.toISOString())
          .order('timestamp', { ascending: true });

        // Fetch trade executions
        const { data: tradesData } = await supabase
          .from('trading_executions')
          .select('executed_at, quantity')
          .gte('executed_at', oneDayAgo.toISOString())
          .order('executed_at', { ascending: true });

        // Fetch closed positions for P&L
        const { data: positionsData } = await supabase
          .from('trading_positions')
          .select('closed_at, realized_pnl')
          .eq('status', 'closed')
          .gte('closed_at', oneDayAgo.toISOString())
          .order('closed_at', { ascending: true });

        // Process coherence
        const coherence = (coherenceData || []).map(d => ({
          timestamp: d.timestamp,
          value: d.coherence,
        }));

        // Process trade volume (count per hour)
        const tradeVolume = aggregateByHour(tradesData || [], 'executed_at');

        // Process cumulative P&L
        let cumulative = 0;
        const cumulativePnL = (positionsData || []).map(d => {
          cumulative += parseFloat(String(d.realized_pnl || 0));
          return {
            timestamp: d.closed_at!,
            value: cumulative,
          };
        });

        setData({
          coherence,
          tradeVolume,
          cumulativePnL,
          isLoading: false,
        });
      } catch (error) {
        console.error('Failed to fetch historical data:', error);
        setData(prev => ({ ...prev, isLoading: false }));
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30s

    return () => clearInterval(interval);
  }, []);

  return data;
}

function aggregateByHour(data: any[], timestampField: string): HistoricalPoint[] {
  const hourlyCount: Record<string, number> = {};

  data.forEach(item => {
    const timestamp = new Date(item[timestampField]);
    const hourKey = new Date(
      timestamp.getFullYear(),
      timestamp.getMonth(),
      timestamp.getDate(),
      timestamp.getHours()
    ).toISOString();

    hourlyCount[hourKey] = (hourlyCount[hourKey] || 0) + 1;
  });

  return Object.entries(hourlyCount).map(([timestamp, value]) => ({
    timestamp,
    value,
  }));
}
