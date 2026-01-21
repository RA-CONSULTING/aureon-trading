/**
 * Schumann Data Hook
 * -----------------
 * Provides live and simulated Schumann resonance data
 */

import { useState, useEffect } from 'react';

export interface SchumannReading {
  frequency: number;
  amplitude: number;
  phase: number;
  timestamp: number;
  region: string;
}

export interface TensorFieldData {
  phi: number;
  kappa: number;
  psi: number;
  TSV: number;
  timestamp: number;
}

export function useSchumannData() {
  const [readings, setReadings] = useState<SchumannReading[]>([]);
  const [tensorData, setTensorData] = useState<TensorFieldData[]>([]);
  const [isLive, setIsLive] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'active' | 'error'>('connecting');

  // Simulate live Schumann data
  useEffect(() => {
    // Initial connection simulation
    setIsLoading(true);
    setConnectionStatus('connecting');
    
    const connectionTimer = setTimeout(() => {
      setIsLoading(false);
      setConnectionStatus('active');
      setIsLive(true);
    }, 2000);

    const interval = setInterval(() => {
      const now = Date.now();
      
      // Base Schumann frequencies with natural variation
      const baseFreqs = [7.83, 14.3, 20.8, 27.3, 33.8];
      
      const newReadings: SchumannReading[] = baseFreqs.map((freq, i) => ({
        frequency: freq + (Math.random() - 0.5) * 0.1, // slight freq drift
        amplitude: 0.3 + Math.random() * 0.7, // varying amplitude
        phase: (Math.random() * 2 * Math.PI), // random phase
        timestamp: now,
        region: i === 0 ? 'Global' : `Mode${i + 1}`
      }));

      setReadings(newReadings);

      // Generate corresponding tensor field data
      const newTensorData: TensorFieldData[] = Array.from({ length: 8 }, () => ({
        phi: Math.random() * 2 * Math.PI,
        kappa: (Math.random() - 0.5) * 2,
        psi: Math.random(),
        TSV: (Math.random() - 0.5) * 4, // -2 to +2 range
        timestamp: now
      }));

      setTensorData(newTensorData);
    }, 2000); // Update every 2 seconds

    return () => {
      clearInterval(interval);
      clearTimeout(connectionTimer);
    };
  }, []);

  // Toggle between live simulation and static data
  const toggleLive = () => setIsLive(!isLive);

  // Get static reference data
  const getStaticData = (): SchumannReading[] => [
    { frequency: 7.83, amplitude: 1.0, phase: 0, timestamp: Date.now(), region: 'Global' },
    { frequency: 14.3, amplitude: 0.8, phase: 0.2, timestamp: Date.now(), region: 'Mode2' },
    { frequency: 20.8, amplitude: 0.6, phase: 0.4, timestamp: Date.now(), region: 'Mode3' },
    { frequency: 27.3, amplitude: 0.4, phase: 0.6, timestamp: Date.now(), region: 'Mode4' },
  ];

  return {
    data: isLive ? readings : getStaticData(),
    readings: isLive ? readings : getStaticData(),
    tensorData,
    isLive,
    isLoading,
    connectionStatus,
    toggleLive,
    lastUpdate: readings.length > 0 ? readings[0].timestamp : Date.now()
  };
}