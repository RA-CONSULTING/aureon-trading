import { useState, useEffect } from 'react';

export interface HiveState {
  updated_at: string;
  mood: string;
  active_scanner: string;
  coherence_score: number;
  veto_count: number;
  last_veto_reason: string;
  message_log: string[];
}

const EMPTY_HIVE_STATE: HiveState = {
  updated_at: '',
  mood: 'Neutral',
  active_scanner: 'Initializing',
  coherence_score: 0.0,
  veto_count: 0,
  last_veto_reason: 'None',
  message_log: ['Queen awaiting first signal'],
};

export function useHiveState(enabled: boolean = true, pollInterval: number = 5000) {
  const [hiveState, setHiveState] = useState<HiveState>(EMPTY_HIVE_STATE);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  useEffect(() => {
    if (!enabled) return;

    const fetchHiveState = async () => {
      try {
        const response = await fetch('/hive_state.json');
        if (response.ok) {
          const data = await response.json();
          setHiveState(data);
          setLastUpdated(new Date());
          setLoading(false);
        }
      } catch (error) {
        console.error('Failed to fetch hive state:', error);
        setLoading(false);
      }
    };

    // Initial fetch
    fetchHiveState();

    // Poll for updates
    const interval = setInterval(fetchHiveState, pollInterval);

    return () => clearInterval(interval);
  }, [enabled, pollInterval]);

  return { hiveState, loading, lastUpdated };
}
