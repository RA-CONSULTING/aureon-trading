import { useState, useEffect, useCallback } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';
import { useQueenHive } from '@/hooks/useQueenHive';

export interface HuntSession {
  id: string;
  status: 'active' | 'paused' | 'stopped';
  min_volatility_pct: number;
  min_volume_usd: number;
  max_targets: number;
  scan_interval_seconds: number;
  total_scans: number;
  total_targets_found: number;
  total_signals_generated: number;
  total_orders_queued: number;
  started_at: string;
  last_scan_at: string | null;
}

export interface HuntTarget {
  id: string;
  symbol: string;
  opportunity_score: number;
  volatility_24h: number;
  volume_24h: number;
  status: string;
  signal_type: string | null;
  signal_confidence: number | null;
  signal_tier: number | null;
  order_queued: boolean;
}

export function useAutomatedHunt() {
  const { toast } = useToast();
  const { session: hiveSession } = useQueenHive();
  const [huntSession, setHuntSession] = useState<HuntSession | null>(null);
  const [recentTargets, setRecentTargets] = useState<HuntTarget[]>([]);
  const [isScanning, setIsScanning] = useState(false);
  const [autoScanInterval, setAutoScanInterval] = useState<number | null>(null);

  const startHunt = useCallback(async (config?: {
    minVolatility?: number;
    minVolume?: number;
    maxTargets?: number;
    scanInterval?: number;
  }) => {
    if (!hiveSession || hiveSession.status !== 'running') {
      toast({
        title: 'No Active Hive Session',
        description: 'Start a Queen-Hive session before starting the hunt',
        variant: 'destructive',
      });
      return null;
    }

    try {
      const { data: session, error } = await supabase
        .from('hunt_sessions')
        .insert({
          user_id: (await supabase.auth.getUser()).data.user?.id,
          hive_session_id: hiveSession.id,
          status: 'active',
          min_volatility_pct: config?.minVolatility || 2.0,
          min_volume_usd: config?.minVolume || 100000,
          max_targets: config?.maxTargets || 5,
          scan_interval_seconds: config?.scanInterval || 300,
        })
        .select()
        .single();

      if (error) throw error;

      setHuntSession(session as HuntSession);

      toast({
        title: '🦁 Hunt Started',
        description: `Scanning for opportunities every ${session.scan_interval_seconds}s`,
      });

      // Trigger immediate scan
      await triggerScan(session.id);

      return session;
    } catch (error) {
      console.error('Failed to start hunt:', error);
      toast({
        title: 'Failed to Start Hunt',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
      return null;
    }
  }, [hiveSession, toast]);

  const stopHunt = useCallback(async () => {
    if (!huntSession) return;

    try {
      await supabase
        .from('hunt_sessions')
        .update({
          status: 'stopped',
          stopped_at: new Date().toISOString(),
        })
        .eq('id', huntSession.id);

      setHuntSession(null);

      toast({
        title: 'Hunt Stopped',
        description: 'Automated hunt loop has been stopped',
      });
    } catch (error) {
      console.error('Failed to stop hunt:', error);
      toast({
        title: 'Failed to Stop Hunt',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
    }
  }, [huntSession, toast]);

  const triggerScan = useCallback(async (sessionId?: string) => {
    const id = sessionId || huntSession?.id;
    if (!id || isScanning) return;

    setIsScanning(true);

    try {
      const { data, error } = await supabase.functions.invoke('automated-hunt-loop', {
        body: { action: 'scan', huntSessionId: id },
      });

      if (error) throw error;

      if (data.success) {
        console.log('🦁 Hunt scan:', data);
        
        toast({
          title: '🦁 Scan Complete',
          description: `Found ${data.targetsFound} targets, queued ${data.ordersQueued} orders`,
        });

        // Refresh data
        await fetchHuntSession(id);
        await fetchRecentTargets(id);
      }
    } catch (error) {
      console.error('Scan failed:', error);
      toast({
        title: 'Scan Failed',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
    } finally {
      setIsScanning(false);
    }
  }, [huntSession, isScanning, toast]);

  const fetchHuntSession = useCallback(async (sessionId: string) => {
    const { data, error } = await supabase
      .from('hunt_sessions')
      .select('*')
      .eq('id', sessionId)
      .single();

    if (!error && data) {
      setHuntSession(data as HuntSession);
    }
  }, []);

  const fetchRecentTargets = useCallback(async (sessionId: string) => {
    const { data, error } = await supabase
      .from('hunt_targets')
      .select('*')
      .eq('hunt_session_id', sessionId)
      .order('opportunity_score', { ascending: false })
      .limit(10);

    if (!error && data) {
      setRecentTargets(data as HuntTarget[]);
    }
  }, []);

  // Load active hunt session on mount
  useEffect(() => {
    const loadActiveHunt = async () => {
      const user = (await supabase.auth.getUser()).data.user;
      if (!user) return;

      const { data } = await supabase
        .from('hunt_sessions')
        .select('*')
        .eq('user_id', user.id)
        .eq('status', 'active')
        .order('started_at', { ascending: false })
        .limit(1)
        .single();

      if (data) {
        setHuntSession(data as HuntSession);
        await fetchRecentTargets(data.id);
      }
    };

    loadActiveHunt();
  }, [fetchRecentTargets]);

  // Auto-scan at configured interval
  useEffect(() => {
    if (!huntSession || huntSession.status !== 'active') {
      if (autoScanInterval) {
        clearInterval(autoScanInterval);
        setAutoScanInterval(null);
      }
      return;
    }

    const interval = setInterval(() => {
      triggerScan();
    }, huntSession.scan_interval_seconds * 1000);

    setAutoScanInterval(interval as unknown as number);

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [huntSession, triggerScan]);

  return {
    huntSession,
    recentTargets,
    isScanning,
    startHunt,
    stopHunt,
    triggerScan,
  };
}
