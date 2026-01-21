/**
io-intervals (Aureon v1.0)
---
Interval detection + compound affect mapping for the io engine.
Works alongside io-resonance-engine.ts without modifying it.
Rationale: when two note centers co‑occur (e.g., dual peaks or blended
weights), the emotional quality is shaped by their INTERVAL (m3, P5, etc.).
This module detects the best interval from a set of weighted notes and
returns a structured "IntervalAffect" for UI and analytics.
*/

// Keep NoteID aligned with engine
export type NoteID = 
  | "C" | "Cs" | "D" | "Ds" | "E" | "F" | "Fs" | "G" | "Gs" | "A" | "As" | "B" | "C5";

export interface NoteDef {
  id: NoteID;
  hz: number;
  valence: number;
  arousal: number;
  tags: string[];
  color: string;
}

export interface BlendWeight {
  note: NoteID;
  w: number;
}

// The canonical chromatic order used in io-resonance-engine
export const CHROMATIC_ORDER: NoteID[] = [
  "C","Cs","D","Ds","E","F","Fs","G","Gs","A","As","B"
];

export interface IntervalAffect {
  interval: string;     // e.g., "m3", "P5", "TT"
  semitones: number;    // 0..12
  root: NoteID;         // chosen base (the higher-weighted or lower index)
  other: NoteID;        // partner note
  tags: string[];       // compound affect descriptors
  valence: number;      // blended + bias
  arousal: number;      // blended + bias
  weight: number;       // strength of interval (0..1)
}

export interface IntervalOptions {
  /** minimum combined weight of the top 2 notes to form an interval */
  minPairWeight?: number; // default 0.5
  /** minimum separation in semitones between the two notes */
  minSemitones?: number;  // default 2
  /** blend strength for interval bias into valence/arousal */
  biasStrength?: number;  // default 0.25
}