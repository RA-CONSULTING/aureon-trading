import { useEffect, useState } from 'react';
import { supabase } from '@/integrations/supabase/client';

interface HealthCheck {
  status: 'healthy' | 'degraded' | 'unhealthy' | 'not_configured' | 'skipped' | 'error';
  message: string;
  timestamp: string;
  [key: string]: any;
}

interface HealthReport {
  timestamp: string;
  overall_status: 'healthy' | 'degraded' | 'unhealthy';
  checks: {
    [key: string]: HealthCheck;
  };
  warnings: string[];
  errors: string[];
}

export function useBackendHealth(autoRefresh = false, interval = 30000) {
  const [healthReport, setHealthReport] = useState<HealthReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  const checkHealth = async () => {
    setLoading(true);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      
      const { data, error } = await supabase.functions.invoke('backend-health-check', {
        headers: session ? {
          Authorization: `Bearer ${session.access_token}`
        } : undefined
      });

      if (error) {
        console.error('[useBackendHealth] Health check error:', error);
        setHealthReport({
          timestamp: new Date().toISOString(),
          overall_status: 'unhealthy',
          checks: {
            error: {
              status: 'unhealthy',
              message: error.message,
              timestamp: new Date().toISOString(),
            }
          },
          warnings: [],
          errors: [error.message],
        });
      } else {
        setHealthReport(data);
        setLastChecked(new Date());
      }
    } catch (error) {
      console.error('[useBackendHealth] Fatal error:', error);
      setHealthReport({
        timestamp: new Date().toISOString(),
        overall_status: 'unhealthy',
        checks: {
          fatal: {
            status: 'unhealthy',
            message: error instanceof Error ? error.message : 'Unknown error',
            timestamp: new Date().toISOString(),
          }
        },
        warnings: [],
        errors: [error instanceof Error ? error.message : 'Unknown error'],
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Initial check
    checkHealth();

    // Auto-refresh if enabled
    if (autoRefresh) {
      const intervalId = setInterval(checkHealth, interval);
      return () => clearInterval(intervalId);
    }
  }, [autoRefresh, interval]);

  return {
    healthReport,
    loading,
    lastChecked,
    refresh: checkHealth,
  };
}
