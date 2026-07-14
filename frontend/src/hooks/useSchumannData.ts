/**
 * Schumann Data Hook
 * -----------------
 * Provides source-backed Schumann resonance data when a real feed is mounted.
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
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'active' | 'error'>('error');

  // No local synthesis: this hook remains empty until a real feed is mounted.
  useEffect(() => {
    setReadings([]);
    setTensorData([]);
    setIsLoading(false);
    setConnectionStatus('error');
    setIsLive(false);
  }, []);

  const toggleLive = () => setIsLive(false);

  return {
    data: readings,
    readings,
    tensorData,
    isLive,
    isLoading,
    connectionStatus,
    toggleLive,
    lastUpdate: readings.length > 0 ? readings[0].timestamp : 0
  };
}
