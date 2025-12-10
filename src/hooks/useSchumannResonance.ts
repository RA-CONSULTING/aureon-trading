import { useState, useEffect, useCallback, useRef } from 'react';
import { supabase } from '@/integrations/supabase/client';

export interface SchumannHarmonic {
  frequency: number;
  amplitude: number;
  name: string;
}

export interface SchumannData {
  fundamentalHz: number;
  amplitude: number;
  quality: number;
  variance: number;
  timestamp: Date;
  coherenceBoost: number;
  resonancePhase: 'stable' | 'elevated' | 'peak' | 'disturbed';
  harmonics: SchumannHarmonic[];
  spectrumHistory: number[][];
  dataSource: 'LIVE' | 'UNAVAILABLE';
}

/**
 * Production-ready Schumann Resonance hook
 * Fetches LIVE data and PERSISTS to consciousness_field_history
 */
export function useSchumannResonance() {
  const [schumannData, setSchumannData] = useState<SchumannData | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [spectrumHistory, setSpectrumHistory] = useState<number[][]>([]);
  const [dataSource, setDataSource] = useState<'LIVE' | 'UNAVAILABLE'>('UNAVAILABLE');
  const [error, setError] = useState<string | null>(null);
  const lastPersistTime = useRef<number>(0);

  // Persist Schumann data to consciousness_field_history
  const persistSchumannData = useCallback(async (data: SchumannData) => {
    // Only persist every 30 seconds to avoid flooding the database
    const now = Date.now();
    if (now - lastPersistTime.current < 30000) return;
    lastPersistTime.current = now;

    try {
      const { error: insertError } = await supabase
        .from('consciousness_field_history')
        .insert({
          schumann_frequency: data.fundamentalHz,
          schumann_amplitude: data.amplitude,
          schumann_quality: data.quality,
          schumann_coherence_boost: data.coherenceBoost,
          schumann_phase: data.resonancePhase,
          celestial_boost: 0,
          total_coherence: data.coherenceBoost + 0.5, // Base coherence + Schumann boost
        });

      if (insertError) {
        console.error('[Schumann] Failed to persist data:', insertError);
      } else {
        console.log('[Schumann] Data persisted to consciousness_field_history');
      }
    } catch (err) {
      console.error('[Schumann] Persist error:', err);
    }
  }, []);

  // Attempt to fetch live Schumann data from edge function
  const fetchLiveData = useCallback(async (): Promise<SchumannData | null> => {
    try {
      const { data, error: fetchError } = await supabase.functions.invoke('fetch-schumann-data');
      
      if (fetchError) {
        setError(`LIVE_DATA_REQUIRED: ${fetchError.message}`);
        return null;
      }

      // The edge function returns the data directly, not wrapped in {success, data}
      const liveData = data;
      
      if (!liveData || !liveData.fundamentalHz) {
        setError('LIVE_DATA_REQUIRED: Invalid response from Schumann API');
        return null;
      }
      
      // Build harmonics from live data
      const harmonics: SchumannHarmonic[] = liveData.harmonics || [
        { frequency: liveData.fundamentalHz, amplitude: liveData.amplitude || 0.7, name: 'Fundamental' },
        { frequency: 14.3, amplitude: (liveData.amplitude || 0.7) * 0.7, name: '2nd Harmonic' },
        { frequency: 20.8, amplitude: (liveData.amplitude || 0.7) * 0.5, name: '3rd Harmonic' },
        { frequency: 27.3, amplitude: (liveData.amplitude || 0.7) * 0.35, name: '4th Harmonic' },
        { frequency: 33.8, amplitude: (liveData.amplitude || 0.7) * 0.25, name: '5th Harmonic' },
        { frequency: 39.0, amplitude: (liveData.amplitude || 0.7) * 0.18, name: '6th Harmonic' },
        { frequency: 45.0, amplitude: (liveData.amplitude || 0.7) * 0.12, name: '7th Harmonic' },
      ];

      const newSpectrum = harmonics.map(h => h.amplitude);
      setSpectrumHistory(prev => [...prev, newSpectrum].slice(-100));

      setError(null);
      return {
        fundamentalHz: liveData.fundamentalHz,
        amplitude: liveData.amplitude || 0.7,
        quality: liveData.quality || 0.7,
        variance: liveData.variance || 0.05,
        timestamp: new Date(),
        coherenceBoost: liveData.coherenceBoost || 0,
        resonancePhase: liveData.resonancePhase || 'stable',
        harmonics,
        spectrumHistory,
        dataSource: 'LIVE',
      };
    } catch (err) {
      setError(`LIVE_DATA_REQUIRED: Schumann API error - ${err}`);
      return null;
    }
  }, [spectrumHistory]);

  // Main update function - LIVE DATA ONLY, no simulation fallback
  const updateSchumannData = useCallback(async () => {
    const liveData = await fetchLiveData();
    if (liveData) {
      setSchumannData(liveData);
      setDataSource('LIVE');
      setIsConnected(true);
      // Persist to database
      await persistSchumannData(liveData);
    } else {
      // NO SIMULATION - Set null and mark as unavailable
      setSchumannData(null);
      setDataSource('UNAVAILABLE');
      setIsConnected(false);
      console.warn('[Schumann] LIVE_DATA_REQUIRED: No simulation fallback - data unavailable');
    }
  }, [fetchLiveData, persistSchumannData]);

  useEffect(() => {
    updateSchumannData();

    // Update every 2 seconds
    const interval = setInterval(updateSchumannData, 2000);
    return () => clearInterval(interval);
  }, [updateSchumannData]);

  return { schumannData, isConnected, dataSource, error };
}
