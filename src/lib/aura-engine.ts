// Deterministic Aura Reading Engine

// Simple hash function to replace crypto-js dependency
function simpleHash(str: string): string {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32bit integer
  }
  return Math.abs(hash).toString(16).padStart(16, '0');
}
export interface AuraInput {
  name: string;
  dob: string;
  tob?: string;
  pob?: { lat: number; lon: number };
  now_timestamp: string;
  mode: 'dual' | 'symbolic' | 'technical' | 'story';
  options: {
    use_astrology: boolean;
    use_earth: boolean;
    use_db_cache: boolean;
  };
}

export interface AuraReading {
  qaid: string;
  qseed: string;
  state_profile: {
    archetype: { primary: string; secondary: string };
    strengths: string[];
    challenges: string[];
    crossroad: { theme: string };
    confidence: number;
  };
  chakra: {
    root: number; sacral: number; solar: number; heart: number;
    throat: number; third_eye: number; crown: number;
    coherence: number;
  };
  color: {
    red: number; orange: number; yellow: number; green: number;
    blue: number; indigo: number; violet: number;
  };
  colors: string[]; // Add colors array for compatibility
  karmic: { note: string }; // Add karmic field
  timelines: {
    aligned: { likelihood: number; outcomes: string[]; drivers: string[] };
    middle: { likelihood: number; outcomes: string[]; drivers: string[] };
    resistant: { likelihood: number; outcomes: string[]; drivers: string[] };
  };
  practices: {
    grounding: number; devotion: number; meditation: number; dreamwork: number;
    service: number; movement: number; ritual: number; timing: number;
  };
  cosmic: { note: string };
  earth: { note: string };
}

export function generateReading(input: AuraInput): AuraReading {
  // Generate deterministic IDs
  const qaid = simpleHash(`${input.name}|${input.dob}|${input.tob || ''}|${JSON.stringify(input.pob || {})}`).slice(0, 16);
  const hourBucket = Math.floor(new Date(input.now_timestamp).getTime() / 3600000);
  const qseed = simpleHash(`${qaid}|${hourBucket}`).slice(0, 16);
  
  // Convert seed to numeric for deterministic generation
  const seed = parseInt(qseed.slice(0, 8), 16);
  
  // Archetype determination
  const archetypes = [
    { primary: 'Seeker', secondary: 'Builder' },
    { primary: 'Healer', secondary: 'Guide' },
    { primary: 'Creator', secondary: 'Visionary' },
    { primary: 'Guardian', secondary: 'Protector' },
    { primary: 'Mystic', secondary: 'Oracle' },
    { primary: 'Warrior', secondary: 'Champion' },
    { primary: 'Teacher', secondary: 'Mentor' },
    { primary: 'Bridge', secondary: 'Connector' }
  ];
  
  const archetype = archetypes[seed % archetypes.length];
  
  // Generate chakra values (deterministic)
  const chakra = {
    root: 0.6 + (seed % 100) / 250,
    sacral: 0.5 + ((seed >> 8) % 100) / 200,
    solar: 0.7 + ((seed >> 16) % 100) / 300,
    heart: 0.8 + ((seed >> 24) % 100) / 400,
    throat: 0.6 + (seed % 150) / 300,
    third_eye: 0.75 + ((seed >> 4) % 100) / 400,
    crown: 0.85 + ((seed >> 12) % 100) / 500,
    coherence: 0.7 + (seed % 80) / 300
  };
  
  // Generate color bands
  const color = {
    red: chakra.root,
    orange: chakra.sacral,
    yellow: chakra.solar,
    green: chakra.heart,
    blue: chakra.throat,
    indigo: chakra.third_eye,
    violet: chakra.crown
  };
  
  return {
    qaid,
    qseed,
    state_profile: {
      archetype,
      strengths: ['intuitive wisdom', 'compassionate heart', 'clear vision'],
      challenges: ['self-doubt', 'overthinking', 'perfectionism'],
      crossroad: { theme: 'comfort_vs_growth' },
      confidence: 0.75 + (seed % 25) / 100
    },
    chakra,
    color,
    timelines: {
      aligned: {
        likelihood: 0.4 + (seed % 20) / 100,
        outcomes: ['spiritual awakening', 'creative breakthrough'],
        drivers: ['heart opening', 'trust in process']
      },
      middle: {
        likelihood: 0.3 + ((seed >> 8) % 20) / 100,
        outcomes: ['steady progress', 'gradual healing'],
        drivers: ['patience', 'consistent practice']
      },
      resistant: {
        likelihood: 0.2 + ((seed >> 16) % 15) / 100,
        outcomes: ['stagnation', 'missed opportunities'],
        drivers: ['fear', 'resistance to change']
      }
    },
    practices: {
      grounding: 0.8 + (seed % 20) / 100,
      devotion: 0.7 + ((seed >> 4) % 25) / 100,
      meditation: 0.9 + ((seed >> 8) % 10) / 100,
      dreamwork: 0.6 + ((seed >> 12) % 30) / 100,
      service: 0.75 + ((seed >> 16) % 25) / 100,
      movement: 0.65 + ((seed >> 20) % 35) / 100,
      ritual: 0.8 + (seed % 15) / 100,
      timing: 0.85 + ((seed >> 6) % 15) / 100
    },
    karmic: { note: 'Past life patterns emerging' },
    colors: Object.values(color).map((val, i) => {
      const colors = ['Red', 'Orange', 'Yellow', 'Green', 'Blue', 'Indigo', 'Violet'];
      return colors[i];
    }),
    cosmic: { note: 'Mercury in harmonious aspect', motifs: ['transformation', 'communication'] },
    earth: { note: 'Schumann resonance elevated', motifs: ['grounding', 'integration'] }
  };
}