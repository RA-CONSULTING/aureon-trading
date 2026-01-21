import { Country, Capital } from './countries-data';

export interface CountryEmotionalProfile {
  countryId: string;
  dominantFrequency: number;
  secondaryFrequencies: number[];
  emotionalState: string;
  valence: number; // -1 to 1
  arousal: number; // 0 to 1
  emotionalTags: string[];
  culturalResonance: string;
  historicalInfluence: number;
}

export interface CapitalEmotionalProfile {
  capitalId: string;
  urbanFrequency: number;
  populationResonance: number;
  economicVibes: number;
  culturalEnergy: number;
  politicalTension: number;
  emotionalState: string;
  valence: number;
  arousal: number;
  emotionalTags: string[];
}

export const COUNTRY_EMOTIONAL_PROFILES: CountryEmotionalProfile[] = [
  {
    countryId: 'usa',
    dominantFrequency: 7.83,
    secondaryFrequencies: [14.3, 20.8],
    emotionalState: 'Dynamic Ambition',
    valence: 0.6,
    arousal: 0.8,
    emotionalTags: ['ambitious', 'innovative', 'diverse', 'competitive'],
    culturalResonance: 'Individualistic Freedom',
    historicalInfluence: 0.9
  },
  {
    countryId: 'canada',
    dominantFrequency: 7.83,
    secondaryFrequencies: [14.3, 20.8],
    emotionalState: 'Harmonious Balance',
    valence: 0.8,
    arousal: 0.4,
    emotionalTags: ['peaceful', 'inclusive', 'nature-connected', 'stable'],
    culturalResonance: 'Collective Harmony',
    historicalInfluence: 0.7
  },
  {
    countryId: 'uk',
    dominantFrequency: 7.83,
    secondaryFrequencies: [14.3, 20.8],
    emotionalState: 'Traditional Innovation',
    valence: 0.4,
    arousal: 0.6,
    emotionalTags: ['traditional', 'resilient', 'sophisticated', 'reserved'],
    culturalResonance: 'Historical Dignity',
    historicalInfluence: 0.95
  },
  {
    countryId: 'france',
    dominantFrequency: 7.83,
    secondaryFrequencies: [14.3, 20.8],
    emotionalState: 'Passionate Elegance',
    valence: 0.7,
    arousal: 0.7,
    emotionalTags: ['passionate', 'artistic', 'intellectual', 'romantic'],
    culturalResonance: 'Cultural Refinement',
    historicalInfluence: 0.9
  }
];

export const CAPITAL_EMOTIONAL_PROFILES: CapitalEmotionalProfile[] = [
  {
    capitalId: 'washington-dc',
    urbanFrequency: 8.2,
    populationResonance: 0.6,
    economicVibes: 0.8,
    culturalEnergy: 0.7,
    politicalTension: 0.9,
    emotionalState: 'Political Intensity',
    valence: 0.3,
    arousal: 0.9,
    emotionalTags: ['powerful', 'tense', 'historic', 'influential']
  },
  {
    capitalId: 'ottawa',
    urbanFrequency: 7.6,
    populationResonance: 0.7,
    economicVibes: 0.6,
    culturalEnergy: 0.8,
    politicalTension: 0.3,
    emotionalState: 'Calm Governance',
    valence: 0.8,
    arousal: 0.3,
    emotionalTags: ['peaceful', 'organized', 'multicultural', 'stable']
  },
  {
    capitalId: 'london',
    urbanFrequency: 8.5,
    populationResonance: 0.9,
    economicVibes: 0.95,
    culturalEnergy: 0.9,
    politicalTension: 0.6,
    emotionalState: 'Global Metropolis',
    valence: 0.5,
    arousal: 0.8,
    emotionalTags: ['cosmopolitan', 'historic', 'financial', 'diverse']
  },
  {
    capitalId: 'paris',
    urbanFrequency: 8.1,
    populationResonance: 0.8,
    economicVibes: 0.7,
    culturalEnergy: 0.95,
    politicalTension: 0.5,
    emotionalState: 'Cultural Capital',
    valence: 0.8,
    arousal: 0.6,
    emotionalTags: ['artistic', 'romantic', 'intellectual', 'elegant']
  }
];