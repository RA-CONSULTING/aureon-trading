import { useState, useEffect } from 'react';

export interface QGITAConfig {
  // Detection Sensitivity
  curvatureThresholdPercentile: number; // 80-99
  goldenRatioTolerance: number; // 0.01-0.10
  lighthouseThresholdSigma: number; // 1.5-3.0
  
  // Confidence Thresholds
  minConfidenceForSignal: number; // 40-80%
  tier1Threshold: number; // 70-95%
  tier2Threshold: number; // 50-75%
  
  // Position Size Multipliers
  tier1PositionMultiplier: number; // 0.5-1.0 (100% position)
  tier2PositionMultiplier: number; // 0.25-0.6 (50% position)
  tier3PositionMultiplier: number; // 0.0-0.3 (minimal/no position)
  
  // Lighthouse Weights
  linearCoherenceWeight: number;
  nonlinearCoherenceWeight: number;
  crossScaleWeight: number;
  geffWeight: number;
  anomalyWeight: number;
}

const DEFAULT_CONFIG: QGITAConfig = {
  curvatureThresholdPercentile: 90,
  goldenRatioTolerance: 0.05,
  lighthouseThresholdSigma: 2.0,
  
  minConfidenceForSignal: 60,
  tier1Threshold: 80,
  tier2Threshold: 60,
  
  tier1PositionMultiplier: 1.0,
  tier2PositionMultiplier: 0.5,
  tier3PositionMultiplier: 0.0,
  
  linearCoherenceWeight: 1.0,
  nonlinearCoherenceWeight: 1.0,
  crossScaleWeight: 1.0,
  geffWeight: 1.0,
  anomalyWeight: 1.0,
};

const STORAGE_KEY = 'qgita-config';

export function useQGITAConfig() {
  const [config, setConfig] = useState<QGITAConfig>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        return { ...DEFAULT_CONFIG, ...JSON.parse(stored) };
      }
    } catch (error) {
      console.error('Failed to load QGITA config:', error);
    }
    return DEFAULT_CONFIG;
  });

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
    } catch (error) {
      console.error('Failed to save QGITA config:', error);
    }
  }, [config]);

  const updateConfig = (updates: Partial<QGITAConfig>) => {
    setConfig(prev => ({ ...prev, ...updates }));
  };

  const resetToDefaults = () => {
    setConfig(DEFAULT_CONFIG);
  };

  return {
    config,
    updateConfig,
    resetToDefaults,
  };
}
