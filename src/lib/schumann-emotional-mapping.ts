/**
 * Schumann Resonance Emotional Frequency Mapping
 * Maps Schumann resonance frequencies to emotional states using Aureon system
 */

import { NOTES } from './aureon-data';
import { NoteID } from './aureon';

// Schumann resonance fundamental frequencies (Hz)
export const SCHUMANN_FREQUENCIES = {
  fundamental: 7.83,    // Primary resonance
  second: 14.3,         // Second harmonic
  third: 20.8,          // Third harmonic
  fourth: 27.3,         // Fourth harmonic
  fifth: 33.8,          // Fifth harmonic
  sixth: 39.3,          // Sixth harmonic
  seventh: 45.9,        // Seventh harmonic
  eighth: 59.9          // Eighth harmonic
};

// Map Schumann frequencies to emotional states
export interface EmotionalState {
  frequency: number;
  intensity: number;
  dominantNote: NoteID;
  valence: number;
  arousal: number;
  emotionalTags: string[];
  color: string;
  description: string;
}

// Regional emotional frequency profiles based on geographical characteristics
export const REGIONAL_EMOTIONAL_PROFILES = {
  'north-america': {
    baseFrequency: 7.83,
    variance: 2.1,
    dominantEmotions: ['Confidence', 'Trust', 'Empowerment'],
    intensityRange: [0.6, 0.9]
  },
  'south-america': {
    baseFrequency: 14.3,
    variance: 3.2,
    dominantEmotions: ['Joy', 'Celebration', 'Warmth'],
    intensityRange: [0.7, 0.95]
  },
  'europe': {
    baseFrequency: 20.8,
    variance: 1.8,
    dominantEmotions: ['Stability', 'Integration', 'Wisdom'],
    intensityRange: [0.5, 0.8]
  },
  'asia': {
    baseFrequency: 27.3,
    variance: 4.1,
    dominantEmotions: ['Transcendence', 'Harmony', 'Balance'],
    intensityRange: [0.6, 0.85]
  },
  'africa': {
    baseFrequency: 33.8,
    variance: 3.5,
    dominantEmotions: ['Vitality', 'Connection', 'Rhythm'],
    intensityRange: [0.8, 0.98]
  },
  'oceania': {
    baseFrequency: 39.3,
    variance: 2.7,
    dominantEmotions: ['Flow', 'Serenity', 'Freedom'],
    intensityRange: [0.4, 0.75]
  },
  'antarctica': {
    baseFrequency: 45.9,
    variance: 1.2,
    dominantEmotions: ['Clarity', 'Purity', 'Stillness'],
    intensityRange: [0.2, 0.5]
  },
  'arctic': {
    baseFrequency: 59.9,
    variance: 1.5,
    dominantEmotions: ['Awakening', 'Insight', 'Transformation'],
    intensityRange: [0.3, 0.6]
  }
};

/**
 * Map a frequency to the closest Aureon note
 */
function mapFrequencyToNote(frequency: number): NoteID {
  let closestNote = NOTES[0];
  let minDiff = Math.abs(frequency - closestNote.hz);
  
  for (const note of NOTES) {
    const diff = Math.abs(frequency - note.hz);
    if (diff < minDiff) {
      minDiff = diff;
      closestNote = note;
    }
  }
  
  return closestNote.id as NoteID;
}

/**
 * Generate emotional state for a region based on Schumann resonance
 */
export function generateRegionalEmotionalState(regionId: string): EmotionalState {
  const profile = REGIONAL_EMOTIONAL_PROFILES[regionId as keyof typeof REGIONAL_EMOTIONAL_PROFILES];
  if (!profile) {
    // Default fallback
    return generateEmotionalState(7.83, 0.5);
  }
  
  // Add some variance to the base frequency
  const variance = (Math.random() - 0.5) * profile.variance;
  const currentFrequency = profile.baseFrequency + variance;
  
  // Generate intensity within the region's range
  const [minIntensity, maxIntensity] = profile.intensityRange;
  const intensity = minIntensity + Math.random() * (maxIntensity - minIntensity);
  
  return generateEmotionalState(currentFrequency, intensity, profile.dominantEmotions);
}

/**
 * Generate emotional state from frequency and intensity
 */
export function generateEmotionalState(
  frequency: number, 
  intensity: number, 
  dominantEmotions?: string[]
): EmotionalState {
  const dominantNote = mapFrequencyToNote(frequency);
  const noteData = NOTES.find(n => n.id === dominantNote)!;
  
  // Modulate valence and arousal based on intensity
  const valence = Math.min(1, Math.max(0, noteData.valence * intensity));
  const arousal = Math.min(1, Math.max(0, noteData.arousal * intensity));
  
  // Combine note tags with dominant emotions
  const emotionalTags = dominantEmotions 
    ? [...dominantEmotions, ...noteData.tags.slice(0, 3)]
    : noteData.tags;
  
  return {
    frequency,
    intensity,
    dominantNote,
    valence,
    arousal,
    emotionalTags: emotionalTags.slice(0, 6),
    color: noteData.color,
    description: generateEmotionalDescription(valence, arousal, emotionalTags?.[0] ?? 'Balanced')
  };
}

/**
 * Generate human-readable emotional description
 */
function generateEmotionalDescription(valence: number, arousal: number, primaryEmotion: string): string {
  const intensityLevel = arousal > 0.7 ? 'high' : arousal > 0.4 ? 'moderate' : 'low';
  const positivity = valence > 0.6 ? 'positive' : valence > 0.4 ? 'neutral' : 'contemplative';
  
  return `${primaryEmotion} with ${intensityLevel} intensity and ${positivity} resonance`;
}

// Alias for backwards compatibility
export const getEmotionalStateFromFrequency = generateEmotionalState;

// Type alias for backwards compatibility
export type EmotionalProfile = typeof REGIONAL_EMOTIONAL_PROFILES[keyof typeof REGIONAL_EMOTIONAL_PROFILES];