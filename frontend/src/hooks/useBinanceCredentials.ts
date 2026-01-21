import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';

export function useBinanceCredentials() {
  const [credentialsCount, setCredentialsCount] = useState(0);
  const [activeCount, setActiveCount] = useState(0);
  const [hasCredentials, setHasCredentials] = useState(false);
  const [useTestnet, setUseTestnet] = useState(true);

  useEffect(() => {
    fetchCredentials();
    const savedTestnet = localStorage.getItem('use_testnet');
    if (savedTestnet !== null) {
      setUseTestnet(savedTestnet === 'true');
    }
  }, []);

  const fetchCredentials = async () => {
    try {
      const { count: total } = await supabase
        .from('binance_credentials')
        .select('*', { count: 'exact', head: true });

      const { count: active } = await supabase
        .from('binance_credentials')
        .select('*', { count: 'exact', head: true })
        .eq('is_active', true);

      setCredentialsCount(total || 0);
      setActiveCount(active || 0);
      setHasCredentials((active || 0) > 0);
    } catch (error) {
      console.error('Failed to fetch credentials:', error);
    }
  };

  const toggleTestnet = (value: boolean) => {
    setUseTestnet(value);
    localStorage.setItem('use_testnet', value.toString());
  };

  const storeCredentials = async (credentials: Array<{ name: string; apiKey: string; apiSecret: string }>) => {
    const { data, error } = await supabase.functions.invoke('store-binance-credentials', {
      body: { credentials },
    });

    if (error) throw error;
    
    await fetchCredentials();
    return data;
  };

  return {
    credentialsCount,
    activeCount,
    hasCredentials,
    useTestnet,
    toggleTestnet,
    storeCredentials,
    refreshCredentials: fetchCredentials,
  };
}
