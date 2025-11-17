import { useState, useEffect } from 'react';

export interface SchumannData {
  fundamentalHz: number;
  amplitude: number;
  quality: number;
  variance: number;
  timestamp: Date;
  coherenceBoost: number;
  resonancePhase: 'stable' | 'elevated' | 'peak' | 'disturbed';
}

export function useSchumannResonance() {
  const [schumannData, setSchumannData] = useState<SchumannData | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // Simulated Schumann Resonance monitoring
    // In production, this would connect to the Earth Live Data WebSocket at port 8787
    const interval = setInterval(() => {
      // Base Schumann Resonance: 7.83 Hz
      const baseHz = 7.83;
      const now = Date.now();
      
      // Simulate natural variations and solar/cosmic influence
      const solarInfluence = Math.sin(now / 600000) * 0.15; // ~10 min cycle
      const cosmicInfluence = Math.sin(now / 3600000) * 0.08; // ~1 hour cycle
      const randomVariation = (Math.random() - 0.5) * 0.05;
      
      const fundamentalHz = baseHz + solarInfluence + cosmicInfluence + randomVariation;
      const amplitude = 0.5 + Math.abs(solarInfluence) * 0.8 + Math.random() * 0.2;
      const quality = 0.7 + Math.abs(cosmicInfluence) * 0.2 + Math.random() * 0.1;
      const variance = Math.abs(solarInfluence + cosmicInfluence + randomVariation);
      
      // Calculate coherence boost based on how close to ideal 7.83 Hz
      const deviation = Math.abs(fundamentalHz - baseHz);
      const coherenceBoost = Math.max(0, (0.15 - deviation) / 0.15) * 0.12; // Up to 12% boost
      
      // Determine resonance phase
      let resonancePhase: SchumannData['resonancePhase'] = 'stable';
      if (amplitude > 1.0 && quality > 0.85) resonancePhase = 'peak';
      else if (amplitude > 0.8 || quality > 0.75) resonancePhase = 'elevated';
      else if (amplitude < 0.4 || quality < 0.6) resonancePhase = 'disturbed';
      
      setSchumannData({
        fundamentalHz,
        amplitude,
        quality,
        variance,
        timestamp: new Date(),
        coherenceBoost,
        resonancePhase
      });
      
      setIsConnected(true);
    }, 2000); // Update every 2 seconds

    return () => clearInterval(interval);
  }, []);

  return { schumannData, isConnected };
}