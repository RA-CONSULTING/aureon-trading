import { useState, useEffect } from 'react';

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

export function useSchumannResonance() {
  const [schumannData, setSchumannData] = useState<SchumannData | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [spectrumHistory, setSpectrumHistory] = useState<number[][]>([]);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimeout: NodeJS.Timeout;

    const connect = () => {
      try {
        // Connect to Earth Live Data WebSocket server
        ws = new WebSocket('ws://localhost:8787/schumann');
        
        ws.onopen = () => {
          console.log('🌍 Connected to Earth Live Data - Schumann Resonance');
          setIsConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log('📡 Schumann data received:', data);
            
            // Parse incoming data from Earth Live Data server
            const fundamentalHz = data.frequency || 7.83;
            const amplitude = data.amplitude || 0.5;
            const quality = data.quality || 0.7;
            const variance = data.variance || 0.05;
            
            // Calculate coherence boost based on how close to ideal 7.83 Hz
            const baseHz = 7.83;
            const deviation = Math.abs(fundamentalHz - baseHz);
            const coherenceBoost = Math.max(0, (0.15 - deviation) / 0.15) * 0.12;
            
            // Determine resonance phase
            let resonancePhase: SchumannData['resonancePhase'] = 'stable';
            if (amplitude > 1.0 && quality > 0.85) resonancePhase = 'peak';
            else if (amplitude > 0.8 || quality > 0.75) resonancePhase = 'elevated';
            else if (amplitude < 0.4 || quality < 0.6) resonancePhase = 'disturbed';
            
            // Parse harmonics (if provided by server, or calculate)
            const harmonics: SchumannHarmonic[] = data.harmonics || [
              { frequency: 7.83, amplitude: amplitude, name: 'Fundamental' },
              { frequency: 14.3, amplitude: amplitude * 0.7, name: '2nd Harmonic' },
              { frequency: 20.8, amplitude: amplitude * 0.5, name: '3rd Harmonic' },
              { frequency: 27.3, amplitude: amplitude * 0.35, name: '4th Harmonic' },
              { frequency: 33.8, amplitude: amplitude * 0.25, name: '5th Harmonic' },
              { frequency: 39.0, amplitude: amplitude * 0.18, name: '6th Harmonic' },
              { frequency: 45.0, amplitude: amplitude * 0.12, name: '7th Harmonic' },
            ];
            
            // Update spectrum history for spectrograph
            setSpectrumHistory(prev => {
              const newSpectrum = harmonics.map(h => h.amplitude);
              const updated = [...prev, newSpectrum];
              return updated.slice(-100); // Keep last 100 samples
            });
            
            setSchumannData({
              fundamentalHz,
              amplitude,
              quality,
              variance,
              timestamp: new Date(),
              coherenceBoost,
              resonancePhase,
              harmonics,
              spectrumHistory
            });
          } catch (error) {
            console.error('❌ Error parsing Schumann data:', error);
          }
        };

        ws.onerror = (error) => {
          console.error('❌ WebSocket error:', error);
          setIsConnected(false);
        };

        ws.onclose = () => {
          console.log('🔌 Disconnected from Earth Live Data');
          setIsConnected(false);
          
          // Attempt to reconnect after 5 seconds
          reconnectTimeout = setTimeout(() => {
            console.log('🔄 Attempting to reconnect...');
            connect();
          }, 5000);
        };
      } catch (error) {
        console.error('❌ Failed to connect to Earth Live Data:', error);
        setIsConnected(false);
        
        // Retry connection
        reconnectTimeout = setTimeout(connect, 5000);
      }
    };

    connect();

    return () => {
      if (ws) {
        ws.close();
      }
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
    };
  }, []);

  return { schumannData, isConnected };
}