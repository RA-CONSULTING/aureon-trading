import { useEffect, useState } from 'react';
import { supabase } from '@/integrations/supabase/client';

type CelestialData = {
  cosmic: {
    overallPower: number;
    coherenceBoost: number;
    sacredFrequencies: number[];
  };
};

export const useCelestialData = () => {
  const [celestialBoost, setCelestialBoost] = useState(0);
  const [sacredFrequencies, setSacredFrequencies] = useState<number[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchCelestialData = async () => {
    setIsLoading(true);
    try {
      const { data, error } = await supabase.functions.invoke('celestial-alignments', {
        body: {},
      });

      if (error) throw error;
      if (data.error) throw new Error(data.error);

      const celestialData = data as CelestialData;
      setCelestialBoost(celestialData.cosmic.coherenceBoost);
      setSacredFrequencies(celestialData.cosmic.sacredFrequencies);
    } catch (err) {
      console.error('Failed to fetch celestial data:', err);
      // Fallback to no boost
      setCelestialBoost(0);
      setSacredFrequencies([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCelestialData();
    
    // Refresh every 10 minutes
    const interval = setInterval(fetchCelestialData, 600000);
    return () => clearInterval(interval);
  }, []);

  return {
    celestialBoost,
    sacredFrequencies,
    isLoading
  };
};
