export type Category = 'yes_no' | 'timing' | 'angel_message';

export interface TarotCard {
  name: string; 
  arcana: 'Major'|'Minor';
  suit?: 'Wands'|'Cups'|'Swords'|'Pentacles';
  number?: number;
  upright: string; 
  reversed: string; 
  keywords?: string[];
}

export interface TarotSpreadItem { 
  pos: string; 
  card: TarotCard; 
  reversed: boolean 
}

export interface AngelCard {
  name: string;
  message: string;
  keywords?: string[];
}

export type Aura = { 
  primary: string; 
  secondary?: string; 
  traits: string[]; 
  message?: string 
};

export type AngelSlot = { 
  slot: string; 
  card: AngelCard 
};

export type MergedNexus = { 
  field: string; 
  value: string; 
  support: number; 
  examples?: string[] 
};

export type Insights = {
  consensus_score: number;
  tensions: string[];
  opportunities: string[];
  risks: string[];
  affirmation: string;
  journal_prompts: string[];
  micro_advice: { slot: string; card: string; tip: string }[];
}

export type Milestone = { 
  label: string; 
  start?: string; 
  end?: string; 
  suggestion: string 
};

export type Candidate = {
  label: string;
  actions: string[];
  window?: { start?: string; end?: string; tag?: string };
  rationale: string;
  features: { 
    alignment: number; 
    timing: number; 
    coherence: number; 
    risk: number; 
    effort: number; 
    support: number 
  };
  score?: number;
  confidence?: number;
};

export type TemporalSynthesis = {
  best: Candidate;
  alternates: Candidate[];
  directive: string;
  diagnostics: { 
    label: string; 
    confidence: number; 
    features: Candidate['features'] 
  }[];
};

export type EngineOutput = {
  tlid: string;
  aura: Aura;
  angel: { 
    spread: AngelSlot[]; 
    timing: any; 
    merged_nexus: MergedNexus[] 
  };
  tarot: { spread: TarotSpreadItem[] };
  synthesis: string;
  plan: { day1: string[]; day2: string[]; day3: string[] };
  insights: Insights;
  milestones: Milestone[];
  tms: TemporalSynthesis;
  nexus_source_law: string;
  constraints: { peace_and_joy: boolean };
};