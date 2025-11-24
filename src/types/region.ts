/**
 * Region type definitions for geographic and harmonic data
 */

export interface Region {
  id: string;
  name: string;
  population?: number;
  area?: number;
  coordinates?: {
    latitude: number;
    longitude: number;
  };
  emotionalProfile?: {
    baseFrequency: number;
    variance: number;
    dominantEmotions: string[];
    intensityRange: [number, number];
  };
}

export interface RegionData extends Region {
  frequency: number;
  amplitude: number;
  coherence: number;
  emotionalState?: any;
}
