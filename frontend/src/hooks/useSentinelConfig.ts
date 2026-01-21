import { useEffect, useState } from 'react';
import { supabase } from '@/integrations/supabase/client';

interface SentinelConfig {
  id: string;
  sentinel_name: string;
  sentinel_birthdate: string;
  sentinel_title: string;
  stargate_location: string;
  stargate_latitude: number;
  stargate_longitude: number;
  auto_initialize: boolean;
  created_at: string;
  updated_at: string;
}

export const useSentinelConfig = () => {
  const [config, setConfig] = useState<SentinelConfig | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const { data, error } = await supabase
          .from('sentinel_config')
          .select('*')
          .single();

        if (error) {
          console.error('Error fetching sentinel config:', error);
          return;
        }

        setConfig(data);
      } catch (err) {
        console.error('Unexpected error fetching sentinel config:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchConfig();

    // Subscribe to real-time updates
    const channel = supabase
      .channel('sentinel_config_changes')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'sentinel_config',
        },
        (payload) => {
          if (payload.eventType === 'UPDATE' || payload.eventType === 'INSERT') {
            setConfig(payload.new as SentinelConfig);
          }
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  return { config, loading };
};
