import { useState, useEffect, useCallback } from 'react';
import { useEcosystemData } from './useEcosystemData';
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
  dataSource: 'LIVE' | 'SIMULATED';
}

/**
 * Production-ready Schumann Resonance hook
 * Phase 5D: Now attempts live API data first, falls back to simulation
 */
export function useSchumannResonance() {
  const [schumannData, setSchumannData] = useState<SchumannData | null>(null);
  const [isConnected, setIsConnected] = useState(true);
  const [spectrumHistory, setSpectrumHistory] = useState<number[][]>([]);
  const [dataSource, setDataSource] = useState<'LIVE' | 'SIMULATED'>('SIMULATED');
  
  const { metrics, isInitialized } = useEcosystemData();

  // Attempt to fetch live Schumann data from edge function
  const fetchLiveData = useCallback(async (): Promise<SchumannData | null> => {
    try {
      const { data, error } = await supabase.functions.invoke('fetch-schumann-data');
      
      if (error || !data || !data.success) {
        return null;
      }

      const liveData = data.data;
      
      // Build harmonics from live data
      const harmonics: SchumannHarmonic[] = [
        { frequency: liveData.frequency || 7.83, amplitude: liveData.amplitude || 0.7, name: 'Fundamental' },
        { frequency: 14.3, amplitude: (liveData.amplitude || 0.7) * 0.7, name: '2nd Harmonic' },
        { frequency: 20.8, amplitude: (liveData.amplitude || 0.7) * 0.5, name: '3rd Harmonic' },
        { frequency: 27.3, amplitude: (liveData.amplitude || 0.7) * 0.35, name: '4th Harmonic' },
        { frequency: 33.8, amplitude: (liveData.amplitude || 0.7) * 0.25, name: '5th Harmonic' },
        { frequency: 39.0, amplitude: (liveData.amplitude || 0.7) * 0.18, name: '6th Harmonic' },
        { frequency: 45.0, amplitude: (liveData.amplitude || 0.7) * 0.12, name: '7th Harmonic' },
      ];

      const newSpectrum = harmonics.map(h => h.amplitude);
      setSpectrumHistory(prev => [...prev, newSpectrum].slice(-100));

      // Calculate coherence boost
      const deviation = Math.abs((liveData.frequency || 7.83) - 7.83);
      const coherenceBoost = Math.max(0, (0.15 - deviation) / 0.15) * 0.12;

      // Determine resonance phase
      let resonancePhase: SchumannData['resonancePhase'] = 'stable';
      const amp = liveData.amplitude || 0.7;
      const qual = liveData.quality || 0.7;
      if (amp > 0.85 && qual > 0.85) resonancePhase = 'peak';
      else if (amp > 0.7 || qual > 0.75) resonancePhase = 'elevated';
      else if (amp < 0.4 || qual < 0.6) resonancePhase = 'disturbed';

      return {
        fundamentalHz: liveData.frequency || 7.83,
        amplitude: liveData.amplitude || 0.7,
        quality: liveData.quality || 0.7,
        variance: liveData.variance || 0.05,
        timestamp: new Date(),
        coherenceBoost,
        resonancePhase,
        harmonics,
        spectrumHistory,
        dataSource: 'LIVE',
      };
    } catch {
      return null;
    }
  }, [spectrumHistory]);

  // Generate simulated Schumann data based on ecosystem coherence (fallback)
  const generateSimulatedData = useCallback((): SchumannData => {
    const timeVariance = Math.sin(Date.now() / 10000) * 0.08;
    const coherenceInfluence = (metrics.coherence - 0.5) * 0.1;
    const fundamentalHz = 7.83 + timeVariance + coherenceInfluence + (Math.random() - 0.5) * 0.05;
    
    const baseAmplitude = 0.6 + metrics.hiveMindCoherence * 0.3;
    const amplitude = Math.max(0.3, Math.min(1.0, baseAmplitude + (Math.random() - 0.5) * 0.1));
    const quality = 0.65 + metrics.coherence * 0.25 + (Math.random() - 0.5) * 0.05;
    const variance = 0.05 + (1 - metrics.coherence) * 0.1;
    
    const deviation = Math.abs(fundamentalHz - 7.83);
    const coherenceBoost = Math.max(0, (0.15 - deviation) / 0.15) * 0.12;
    
    let resonancePhase: SchumannData['resonancePhase'] = 'stable';
    if (amplitude > 0.85 && quality > 0.85) resonancePhase = 'peak';
    else if (amplitude > 0.7 || quality > 0.75) resonancePhase = 'elevated';
    else if (amplitude < 0.4 || quality < 0.6) resonancePhase = 'disturbed';
    
    const harmonics: SchumannHarmonic[] = [
      { frequency: fundamentalHz, amplitude: amplitude, name: 'Fundamental' },
      { frequency: 14.3 + (Math.random() - 0.5) * 0.2, amplitude: amplitude * 0.7, name: '2nd Harmonic' },
      { frequency: 20.8 + (Math.random() - 0.5) * 0.3, amplitude: amplitude * 0.5, name: '3rd Harmonic' },
      { frequency: 27.3 + (Math.random() - 0.5) * 0.4, amplitude: amplitude * 0.35, name: '4th Harmonic' },
      { frequency: 33.8 + (Math.random() - 0.5) * 0.5, amplitude: amplitude * 0.25, name: '5th Harmonic' },
      { frequency: 39.0 + (Math.random() - 0.5) * 0.5, amplitude: amplitude * 0.18, name: '6th Harmonic' },
      { frequency: 45.0 + (Math.random() - 0.5) * 0.5, amplitude: amplitude * 0.12, name: '7th Harmonic' },
    ];
    
    const newSpectrum = harmonics.map(h => h.amplitude);
    setSpectrumHistory(prev => [...prev, newSpectrum].slice(-100));
    
    return {
      fundamentalHz,
      amplitude,
      quality,
      variance,
      timestamp: new Date(),
      coherenceBoost,
      resonancePhase,
      harmonics,
      spectrumHistory,
      dataSource: 'SIMULATED',
    };
  }, [metrics.coherence, metrics.hiveMindCoherence, spectrumHistory]);

  // Main update function - tries live first, falls back to simulated
  const updateSchumannData = useCallback(async () => {
    const liveData = await fetchLiveData();
    if (liveData) {
      setSchumannData(liveData);
      setDataSource('LIVE');
      setIsConnected(true);
    } else {
      setSchumannData(generateSimulatedData());
      setDataSource('SIMULATED');
      setIsConnected(true);
    }
  }, [fetchLiveData, generateSimulatedData]);

  useEffect(() => {
    if (isInitialized) {
      updateSchumannData();
    }

    // Update every 2 seconds
    const interval = setInterval(updateSchumannData, 2000);
    return () => clearInterval(interval);
  }, [isInitialized, updateSchumannData]);

  return { schumannData, isConnected, dataSource };
}
