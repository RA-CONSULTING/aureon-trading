// Harmonic Nexus Core (HNC) Type Definitions
// Data contracts for coherence engine

export type ResonanceSample = {
  t: number;        // timestamp
  band: string;     // e.g., "7.83", "14.3", "20.8"
  power: number;    // band power
  region?: string;  // optional region
};

export type AffectSample = {
  t: number;        // timestamp
  v: number;        // valence 0-1
  a: number;        // arousal 0-1
  region: string;   // region identifier
};

export type NarrativeItem = {
  t: number;        // timestamp
  station: string;  // news source
  region?: string;  // optional region
  text: string;     // headline/content
  emotion: string;  // primary emotion
  tags: string[];   // context tags
  valence: number;  // 0-1
  arousal: number;  // 0-1
};

export type CoherenceBand = {
  frequency: string;  // band identifier
  gamma: number;      // coherence score 0-1
  power: number;      // band power
};

export type HNCDriver = {
  type: 'topic' | 'station' | 'emotion';
  name: string;       // tag/station/emotion name
  weight: number;     // influence weight
  contribution: number; // % contribution to score
};

export type HNCEdge = {
  from: string;       // source region
  to: string;         // target region
  weight: number;     // influence strength
  lag: number;        // time lag in minutes
  type: 'coherence' | 'narrative' | 'affect';
};

export type HNCRegionTick = {
  region: string;
  timestamp: number;
  score: number;      // overall coherence score 0-100
  gamma: CoherenceBand[];  // per-band coherence
  drivers: HNCDriver[];    // top influence drivers
  edges: HNCEdge[];        // outgoing influences
  stability: number;       // stability metric 0-1
  negShare: number;        // negative sentiment share
};

export type HNCGraph = {
  nodes: Array<{
    id: string;
    region: string;
    score: number;
    size: number;
  }>;
  edges: HNCEdge[];
};