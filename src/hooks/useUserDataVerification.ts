import { useState, useEffect, useCallback } from 'react';
import { supabase } from '@/integrations/supabase/client';

export interface ExchangeVerification {
  exchange: string;
  hasCredentials: boolean;
  partialApiKey: string | null;
  lastVerified: string | null;
  status: 'VERIFIED' | 'UNVERIFIED' | 'ERROR' | 'CHECKING';
}

export interface DataSourceVerification {
  source: string;
  status: 'LIVE' | 'STALE' | 'NO_DATA' | 'DEMO';
  lastUpdate: string | null;
  value: number | null;
}

export interface UserDataVerificationState {
  userId: string | null;
  userEmail: string | null;
  sessionCreatedAt: string | null;
  isAuthenticated: boolean;
  isOwnData: boolean;
  exchanges: ExchangeVerification[];
  dataSources: DataSourceVerification[];
  overallStatus: 'VERIFIED' | 'PARTIAL' | 'UNVERIFIED' | 'CHECKING';
  lastFullVerification: string | null;
}

export function useUserDataVerification() {
  const [state, setState] = useState<UserDataVerificationState>({
    userId: null,
    userEmail: null,
    sessionCreatedAt: null,
    isAuthenticated: false,
    isOwnData: false,
    exchanges: [],
    dataSources: [],
    overallStatus: 'CHECKING',
    lastFullVerification: null,
  });
  const [isVerifying, setIsVerifying] = useState(false);

  const maskApiKey = (key: string | null): string | null => {
    if (!key || key.length < 8) return null;
    return `****${key.slice(-4)}`;
  };

  const verifyUserData = useCallback(async () => {
    setIsVerifying(true);
    
    try {
      // Get current auth session
      const { data: { user }, error: authError } = await supabase.auth.getUser();
      
      if (authError || !user) {
        setState(prev => ({
          ...prev,
          isAuthenticated: false,
          isOwnData: false,
          overallStatus: 'UNVERIFIED',
        }));
        return;
      }

      // Get user's session data from database
      const { data: sessionData, error: sessionError } = await supabase
        .from('aureon_user_sessions')
        .select('*')
        .eq('user_id', user.id)
        .single();

      if (sessionError) {
        console.warn('[UserDataVerification] No session found:', sessionError);
      }

      // Verify data ownership - user_id in session matches auth.uid()
      const isOwnData = sessionData?.user_id === user.id;

      // Check exchange credentials
      const exchanges: ExchangeVerification[] = [
        {
          exchange: 'Binance',
          hasCredentials: !!(sessionData?.binance_api_key_encrypted),
          partialApiKey: maskApiKey(sessionData?.binance_api_key_encrypted?.slice(-8) || null),
          lastVerified: sessionData?.updated_at || null,
          status: sessionData?.binance_api_key_encrypted ? 'VERIFIED' : 'UNVERIFIED',
        },
        {
          exchange: 'Kraken',
          hasCredentials: !!(sessionData?.kraken_api_key_encrypted),
          partialApiKey: maskApiKey(sessionData?.kraken_api_key_encrypted?.slice(-8) || null),
          lastVerified: sessionData?.updated_at || null,
          status: sessionData?.kraken_api_key_encrypted ? 'VERIFIED' : 'UNVERIFIED',
        },
        {
          exchange: 'Alpaca',
          hasCredentials: !!(sessionData?.alpaca_api_key_encrypted),
          partialApiKey: maskApiKey(sessionData?.alpaca_api_key_encrypted?.slice(-8) || null),
          lastVerified: sessionData?.updated_at || null,
          status: sessionData?.alpaca_api_key_encrypted ? 'VERIFIED' : 'UNVERIFIED',
        },
        {
          exchange: 'Capital.com',
          hasCredentials: !!(sessionData?.capital_api_key_encrypted),
          partialApiKey: maskApiKey(sessionData?.capital_api_key_encrypted?.slice(-8) || null),
          lastVerified: sessionData?.updated_at || null,
          status: sessionData?.capital_api_key_encrypted ? 'VERIFIED' : 'UNVERIFIED',
        },
      ];

      // Check data sources
      const dataSources: DataSourceVerification[] = [
        {
          source: 'Coherence (Γ)',
          status: sessionData?.current_coherence ? 'LIVE' : 'NO_DATA',
          lastUpdate: sessionData?.last_quantum_update_at || null,
          value: sessionData?.current_coherence || null,
        },
        {
          source: 'Lambda (Λ)',
          status: sessionData?.current_lambda ? 'LIVE' : 'NO_DATA',
          lastUpdate: sessionData?.last_quantum_update_at || null,
          value: sessionData?.current_lambda || null,
        },
        {
          source: 'Lighthouse Signal',
          status: sessionData?.current_lighthouse_signal ? 'LIVE' : 'NO_DATA',
          lastUpdate: sessionData?.last_quantum_update_at || null,
          value: sessionData?.current_lighthouse_signal || null,
        },
        {
          source: 'Total Equity',
          status: sessionData?.total_equity_usdt ? 'LIVE' : 'NO_DATA',
          lastUpdate: sessionData?.updated_at || null,
          value: sessionData?.total_equity_usdt || null,
        },
      ];

      // Calculate overall status
      const verifiedExchanges = exchanges.filter(e => e.status === 'VERIFIED').length;
      const liveDataSources = dataSources.filter(d => d.status === 'LIVE').length;
      
      let overallStatus: 'VERIFIED' | 'PARTIAL' | 'UNVERIFIED' = 'UNVERIFIED';
      if (isOwnData && verifiedExchanges > 0 && liveDataSources >= 2) {
        overallStatus = 'VERIFIED';
      } else if (isOwnData && (verifiedExchanges > 0 || liveDataSources > 0)) {
        overallStatus = 'PARTIAL';
      }

      setState({
        userId: user.id,
        userEmail: user.email || null,
        sessionCreatedAt: sessionData?.created_at || null,
        isAuthenticated: true,
        isOwnData,
        exchanges,
        dataSources,
        overallStatus,
        lastFullVerification: new Date().toISOString(),
      });

    } catch (error) {
      console.error('[UserDataVerification] Error:', error);
      setState(prev => ({
        ...prev,
        overallStatus: 'UNVERIFIED',
      }));
    } finally {
      setIsVerifying(false);
    }
  }, []);

  // Initial verification on mount
  useEffect(() => {
    verifyUserData();
  }, [verifyUserData]);

  // Re-verify on auth state change
  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange(() => {
      verifyUserData();
    });

    return () => subscription.unsubscribe();
  }, [verifyUserData]);

  return {
    ...state,
    isVerifying,
    verify: verifyUserData,
  };
}
