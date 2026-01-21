import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';

export interface ConsciousnessHistoryData {
  id: string;
  timestamp: string;
  schumann_frequency: number;
  schumann_amplitude: number;
  schumann_quality: number;
  schumann_coherence_boost: number;
  schumann_phase: string;
  hrv: number | null;
  heart_rate: number | null;
  alpha_waves: number | null;
  theta_waves: number | null;
  delta_waves: number | null;
  beta_waves: number | null;
  biometric_coherence_index: number | null;
  celestial_boost: number;
  total_coherence: number;
}

export function useConsciousnessHistory(hoursBack: number = 24) {
  const [historyData, setHistoryData] = useState<ConsciousnessHistoryData[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchHistory();

    // Subscribe to realtime updates
    const channel = supabase
      .channel('consciousness-history-changes')
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'consciousness_field_history'
        },
        (payload) => {
          setHistoryData(prev => [payload.new as ConsciousnessHistoryData, ...prev].slice(0, 1000));
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [hoursBack]);

  const fetchHistory = async () => {
    try {
      const cutoffTime = new Date();
      cutoffTime.setHours(cutoffTime.getHours() - hoursBack);

      const { data, error } = await supabase
        .from('consciousness_field_history')
        .select('*')
        .gte('timestamp', cutoffTime.toISOString())
        .order('timestamp', { ascending: true })
        .limit(1000);

      if (error) {
        console.error('Error fetching consciousness history:', error);
        return;
      }

      setHistoryData(data || []);
    } catch (error) {
      console.error('Error in fetchHistory:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const saveDataPoint = async (
    schumannData: any,
    biometricData: any,
    celestialBoost: number,
    totalCoherence: number
  ) => {
    try {
      const { error } = await supabase
        .from('consciousness_field_history')
        .insert({
          schumann_frequency: schumannData?.fundamentalHz || 7.83,
          schumann_amplitude: schumannData?.amplitude || 0.5,
          schumann_quality: schumannData?.quality || 0.7,
          schumann_coherence_boost: schumannData?.coherenceBoost || 0,
          schumann_phase: schumannData?.resonancePhase || 'stable',
          hrv: biometricData?.hrv || null,
          heart_rate: biometricData?.heartRate || null,
          alpha_waves: biometricData?.alpha || null,
          theta_waves: biometricData?.theta || null,
          delta_waves: biometricData?.delta || null,
          beta_waves: biometricData?.beta || null,
          biometric_coherence_index: biometricData?.coherenceIndex || null,
          celestial_boost: celestialBoost,
          total_coherence: totalCoherence
        });

      if (error) {
        console.error('Error saving consciousness data:', error);
      }
    } catch (error) {
      console.error('Error in saveDataPoint:', error);
    }
  };

  return { historyData, isLoading, saveDataPoint };
}
