import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';

export interface NetworkHistoryPoint {
  timestamp: string;
  networkStrength: number;
  avgCoherence: number;
  avgFrequency: number;
  phaseLocks: number;
  resonanceQuality: number;
  gridEnergy: number;
  activeNodes: number;
}

export function useStargateNetworkHistory(hoursBack = 24) {
  const [history, setHistory] = useState<NetworkHistoryPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHistory = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const startTime = new Date(Date.now() - hoursBack * 60 * 60 * 1000).toISOString();

        const { data, error: queryError } = await supabase
          .from('stargate_network_states')
          .select('*')
          .eq('temporal_id', '02111991')
          .gte('event_timestamp', startTime)
          .order('event_timestamp', { ascending: true });

        if (queryError) throw queryError;

        if (data) {
          const formattedData: NetworkHistoryPoint[] = data.map(point => ({
            timestamp: point.event_timestamp,
            networkStrength: Number(point.network_strength),
            avgCoherence: Number(point.avg_coherence || 0),
            avgFrequency: Number(point.avg_frequency || 0),
            phaseLocks: point.phase_locks || 0,
            resonanceQuality: Number(point.resonance_quality || 0),
            gridEnergy: Number(point.grid_energy),
            activeNodes: point.active_nodes,
          }));

          setHistory(formattedData);
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to fetch history';
        setError(errorMessage);
        console.error('Failed to fetch network history:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchHistory();

    // Refresh every 30 seconds
    const interval = setInterval(fetchHistory, 30000);

    return () => clearInterval(interval);
  }, [hoursBack]);

  return { history, isLoading, error };
}
