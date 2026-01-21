import { useEffect, useRef } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';

const MONITOR_INTERVAL = 5000; // 5 seconds

export const usePositionMonitor = (isEnabled: boolean) => {
  const { toast } = useToast();
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!isEnabled) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }

    const monitorPositions = async () => {
      try {
        const { data, error } = await supabase.functions.invoke('monitor-positions');

        if (error) throw error;

        if (data?.closedPositions && data.closedPositions.length > 0) {
          data.closedPositions.forEach((position: any) => {
            const isProfitable = position.pnl >= 0;
            const emoji = position.reason === 'TAKE_PROFIT' ? '🎯' : '🛑';
            
            toast({
              title: `${emoji} Position Closed`,
              description: `${position.symbol} ${position.side} - ${position.reason}\nP&L: ${isProfitable ? '+' : ''}$${position.pnl.toFixed(2)}`,
              variant: isProfitable ? 'default' : 'destructive',
              duration: 7000,
            });
          });
        }
      } catch (error) {
        console.error('Position monitoring error:', error);
      }
    };

    // Initial check
    monitorPositions();

    // Set up interval
    intervalRef.current = setInterval(monitorPositions, MONITOR_INTERVAL);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isEnabled, toast]);
};
