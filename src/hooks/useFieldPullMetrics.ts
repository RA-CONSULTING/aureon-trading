import { useState, useEffect } from 'react';

export interface FieldPullMetric {
  isoTime: string;
  unixTime: number;
  monoNs: number;
  coherenceIndex: number;
  schumannLock: number;
  prime1091Balance: number;
  latticeIdMatch: number;
  resonanceGainDb: number;
  probabilityUpliftProxy: number;
  safetyStatus: string;
}

export function useFieldPullMetrics() {
  const [metrics, setMetrics] = useState<FieldPullMetric[]>([]);
  const [loading, setLoading] = useState(true);
  const [latestMetric, setLatestMetric] = useState<FieldPullMetric | null>(null);

  useEffect(() => {
    const loadMetrics = async () => {
      try {
        const response = await fetch('/data/field_pull_metrics_1.csv');
        const text = await response.text();
        
        const lines = text.trim().split('\n');
        const headers = lines[0].split(',');
        
        const parsedMetrics = lines.slice(1).map(line => {
          const values = line.split(',');
          return {
            isoTime: values[0],
            unixTime: parseFloat(values[1]),
            monoNs: parseFloat(values[2]),
            coherenceIndex: parseFloat(values[3]),
            schumannLock: parseFloat(values[4]),
            prime1091Balance: parseFloat(values[5]),
            latticeIdMatch: parseFloat(values[6]),
            resonanceGainDb: parseFloat(values[7]),
            probabilityUpliftProxy: parseFloat(values[8]),
            safetyStatus: values[9],
          };
        });

        setMetrics(parsedMetrics);
        setLatestMetric(parsedMetrics[parsedMetrics.length - 1]);
        setLoading(false);
      } catch (error) {
        console.error('Error loading field pull metrics:', error);
        setLoading(false);
      }
    };

    loadMetrics();
  }, []);

  return { metrics, latestMetric, loading };
}
