/**
 * Emotion state type definitions for legacy compatibility
 */

import type { NoteID } from '@/lib/aureon';

export interface EmotionState {
  // Core properties
  frequency: number;
  valence: number;
  arousal: number;
  
  // Legacy properties for backwards compatibility
  note?: NoteID;
  emotion?: string[];
  
  // Extended properties
  color?: string;
  intensity?: number;
  dominantNote?: NoteID;
  emotionalTags?: string[];
  description?: string;
}

export interface EmotionSample {
  t: number;  // timestamp
  f: number;  // frequency
  v: number;  // valence
  a: number;  // arousal
}

export interface EmotionStats24h {
  avgFrequency: number;
  avgValence: number;
  avgArousal: number;
  count: number;
}
