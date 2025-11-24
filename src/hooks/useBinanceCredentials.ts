import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';

const TESTNET_KEY = 'aureon-use-testnet';

export const useBinanceCredentials = () => {
  const [hasCredentials, setHasCredentials] = useState<boolean>(false);
  const [loading, setLoading] = useState(true);
  const [useTestnet, setUseTestnet] = useState<boolean>(() => {
    // Default to testnet for safety
    try {
      const stored = localStorage.getItem(TESTNET_KEY);
      return stored === null ? true : stored === 'true';
    } catch {
      return true;
    }
  });
  const { toast } = useToast();

  // Persist testnet preference
  useEffect(() => {
    try {
      localStorage.setItem(TESTNET_KEY, String(useTestnet));
    } catch (error) {
      console.error('Failed to save testnet preference:', error);
    }
  }, [useTestnet]);

  const checkCredentials = async () => {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        setHasCredentials(false);
        setLoading(false);
        return;
      }

      const { data, error } = await supabase
        .from('user_binance_credentials')
        .select('id')
        .eq('user_id', user.id)
        .maybeSingle();

      setHasCredentials(!!data && !error);
    } catch (error) {
      console.error('Error checking credentials:', error);
      setHasCredentials(false);
    } finally {
      setLoading(false);
    }
  };

  const storeCredentials = async (apiKey: string, apiSecret: string) => {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error('Not authenticated');

      const { data, error } = await supabase.functions.invoke('store-binance-credentials', {
        body: { userId: user.id, apiKey, apiSecret }
      });

      if (error) throw error;

      toast({
        title: 'Credentials Stored',
        description: 'Your Binance API credentials have been encrypted and stored securely.',
      });

      await checkCredentials();
      return true;
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to store credentials',
        variant: 'destructive',
      });
      return false;
    }
  };

  const getCredentials = async () => {
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) throw new Error('Not authenticated');

      const { data, error } = await supabase.functions.invoke('get-binance-credentials', {
        headers: {
          Authorization: `Bearer ${session.access_token}`
        }
      });

      if (error) throw error;
      return data as { apiKey: string; apiSecret: string; userId: string };
    } catch (error: any) {
      console.error('Error fetching credentials:', error);
      toast({
        title: 'Error',
        description: error.message || 'Failed to retrieve credentials',
        variant: 'destructive',
      });
      return null;
    }
  };

  useEffect(() => {
    checkCredentials();
  }, []);

  return {
    hasCredentials,
    loading,
    useTestnet,
    setUseTestnet,
    storeCredentials,
    getCredentials,
    refreshCredentials: checkCredentials,
  };
};
