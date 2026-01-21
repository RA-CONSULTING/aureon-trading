import { useState, useEffect, useCallback } from 'react';
import { supabase } from '@/integrations/supabase/client';

export interface ExchangeStatus {
  exchange: string;
  status: 'LIVE' | 'DEMO' | 'OFFLINE' | 'ERROR';
  hasCredentials: boolean;
  lastPrice?: number;
  lastTimestamp?: number;
  latencyMs?: number;
  errorMessage?: string;
}

export interface VerificationResult {
  success: boolean;
  timestamp: number;
  exchanges: ExchangeStatus[];
  overallStatus: 'ALL_LIVE' | 'PARTIAL_LIVE' | 'ALL_DEMO' | 'OFFLINE';
  priceVariance?: number;
  warnings: string[];
}

export interface UseExchangeDataVerificationResult {
  verification: VerificationResult | null;
  isLoading: boolean;
  isLiveData: boolean;
  isDemoMode: boolean;
  hasGhostData: boolean;
  liveExchangeCount: number;
  totalExchangeCount: number;
  verify: () => Promise<void>;
  getExchangeStatus: (exchange: string) => ExchangeStatus | undefined;
}

/**
 * Hook for verifying exchange data connectivity
 * Detects ghost/fake data and ensures real exchange connections
 */
export const useExchangeDataVerification = (
  autoVerify: boolean = true,
  intervalMs: number = 30000
): UseExchangeDataVerificationResult => {
  const [verification, setVerification] = useState<VerificationResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const verify = useCallback(async () => {
    setIsLoading(true);
    try {
      const { data, error } = await supabase.functions.invoke('verify-exchange-connectivity');
      
      if (error) {
        console.error('[useExchangeDataVerification] Error:', error);
        setVerification({
          success: false,
          timestamp: Date.now(),
          exchanges: [],
          overallStatus: 'OFFLINE',
          warnings: [error.message || 'Verification failed'],
        });
        return;
      }
      
      setVerification(data);
    } catch (error) {
      console.error('[useExchangeDataVerification] Exception:', error);
      setVerification({
        success: false,
        timestamp: Date.now(),
        exchanges: [],
        overallStatus: 'OFFLINE',
        warnings: ['Verification request failed'],
      });
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (autoVerify) {
      verify();
      const interval = setInterval(verify, intervalMs);
      return () => clearInterval(interval);
    }
  }, [autoVerify, intervalMs, verify]);

  const liveExchangeCount = verification?.exchanges.filter(e => e.status === 'LIVE').length || 0;
  const totalExchangeCount = verification?.exchanges.length || 0;
  const isLiveData = verification?.overallStatus === 'ALL_LIVE';
  const isDemoMode = verification?.overallStatus === 'ALL_DEMO';
  const hasGhostData = isDemoMode && totalExchangeCount > 0;

  const getExchangeStatus = useCallback((exchange: string) => {
    return verification?.exchanges.find(e => e.exchange.toLowerCase() === exchange.toLowerCase());
  }, [verification]);

  return {
    verification,
    isLoading,
    isLiveData,
    isDemoMode,
    hasGhostData,
    liveExchangeCount,
    totalExchangeCount,
    verify,
    getExchangeStatus,
  };
};
