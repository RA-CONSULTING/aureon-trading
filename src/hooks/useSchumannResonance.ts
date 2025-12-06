import { useState, useEffect, useCallback } from 'react';
import { useEcosystemData } from './useEcosystemData';

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
}

/**
 * Production-ready Schumann Resonance hook
 * Uses ecosystem data + realistic simulation (no localhost WebSocket)
 */
export function useSchumannResonance() {
  const [schumannData, setSchumannData] = useState<SchumannData | null>(null);
  const [isConnected, setIsConnected] = useState(true);
  const [spectrumHistory, setSpectrumHistory] = useState<number[][]>([]);
  
  const { metrics, isInitialized } = useEcosystemData();

  // Generate realistic Schumann data based on ecosystem coherence
  const generateSchumannData = useCallback(() => {
    // Base frequency with natural Earth variance (7.83 Hz ± 0.15 Hz)
    const timeVariance = Math.sin(Date.now() / 10000) * 0.08;
    const coherenceInfluence = (metrics.coherence - 0.5) * 0.1;
    const fundamentalHz = 7.83 + timeVariance + coherenceInfluence + (Math.random() - 0.5) * 0.05;
    
    // Amplitude correlates with ecosystem activity
    const baseAmplitude = 0.6 + metrics.hiveMindCoherence * 0.3;
    const amplitude = Math.max(0.3, Math.min(1.0, baseAmplitude + (Math.random() - 0.5) * 0.1));
    
    // Quality based on coherence
    const quality = 0.65 + metrics.coherence * 0.25 + (Math.random() - 0.5) * 0.05;
    
    // Variance (lower is more stable)
    const variance = 0.05 + (1 - metrics.coherence) * 0.1;
    
    // Calculate coherence boost
    const deviation = Math.abs(fundamentalHz - 7.83);
    const coherenceBoost = Math.max(0, (0.15 - deviation) / 0.15) * 0.12;
    
    // Determine resonance phase
    let resonancePhase: SchumannData['resonancePhase'] = 'stable';
    if (amplitude > 0.85 && quality > 0.85) resonancePhase = 'peak';
    else if (amplitude > 0.7 || quality > 0.75) resonancePhase = 'elevated';
    else if (amplitude < 0.4 || quality < 0.6) resonancePhase = 'disturbed';
    
    // Generate harmonics (Schumann resonance harmonics)
    const harmonics: SchumannHarmonic[] = [
      { frequency: fundamentalHz, amplitude: amplitude, name: 'Fundamental' },
      { frequency: 14.3 + (Math.random() - 0.5) * 0.2, amplitude: amplitude * 0.7, name: '2nd Harmonic' },
      { frequency: 20.8 + (Math.random() - 0.5) * 0.3, amplitude: amplitude * 0.5, name: '3rd Harmonic' },
      { frequency: 27.3 + (Math.random() - 0.5) * 0.4, amplitude: amplitude * 0.35, name: '4th Harmonic' },
      { frequency: 33.8 + (Math.random() - 0.5) * 0.5, amplitude: amplitude * 0.25, name: '5th Harmonic' },
      { frequency: 39.0 + (Math.random() - 0.5) * 0.5, amplitude: amplitude * 0.18, name: '6th Harmonic' },
      { frequency: 45.0 + (Math.random() - 0.5) * 0.5, amplitude: amplitude * 0.12, name: '7th Harmonic' },
    ];
    
    // Update spectrum history
    const newSpectrum = harmonics.map(h => h.amplitude);
    setSpectrumHistory(prev => {
      const updated = [...prev, newSpectrum];
      return updated.slice(-100);
    });
    
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
    };
  }, [metrics.coherence, metrics.hiveMindCoherence, spectrumHistory]);

  useEffect(() => {
    // Initial data
    if (isInitialized) {
      setSchumannData(generateSchumannData());
      setIsConnected(true);
    }

    // Update every 2 seconds (realistic Earth data update rate)
    const interval = setInterval(() => {
      setSchumannData(generateSchumannData());
    }, 2000);

    return () => clearInterval(interval);
  }, [isInitialized, generateSchumannData]);

  return { schumannData, isConnected };
}
