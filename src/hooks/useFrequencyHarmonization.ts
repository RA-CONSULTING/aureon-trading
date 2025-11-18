import { useState, useEffect } from 'react';
import { useStargateNetwork } from './useStargateNetwork';
import { stargateHarmonizer, type HarmonizationProfile } from '@/core/stargateFrequencyHarmonizer';

export function useFrequencyHarmonization() {
  const { activations, metrics, isActive } = useStargateNetwork();
  const [harmonization, setHarmonization] = useState<HarmonizationProfile | null>(null);
  const [lastUpdate, setLastUpdate] = useState<number>(Date.now());

  useEffect(() => {
    if (activations.length > 0 && metrics && isActive) {
      // Calculate harmonization profile
      const profile = stargateHarmonizer.harmonize(activations, metrics);
      setHarmonization(profile);
      setLastUpdate(Date.now());

      // Log significant events
      if (profile.optimalEntryWindow) {
        console.log('🌟 OPTIMAL ENTRY WINDOW DETECTED');
        console.log(`   Dominant Frequency: ${profile.dominantFrequency} Hz`);
        console.log(`   Resonance Quality: ${(profile.resonanceQuality * 100).toFixed(1)}%`);
        console.log(`   Trading Bias: ${profile.tradingBias}`);
      }
    }
  }, [activations, metrics, isActive]);

  return {
    harmonization,
    lastUpdate,
    isActive,
  };
}
