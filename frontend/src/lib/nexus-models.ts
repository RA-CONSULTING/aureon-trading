// src/lib/nexus-models.ts
// TypeScript equivalents of Unity Nexus models for web integration

export interface TensorDatum {
  phi: number;   // phase (rad)
  psi: number;   // amplitude density
  TSV: number;   // coherence 0..1-ish (toolkit-specific)
}

export interface SchumannFrame {
  t: string;                    // timestamp or label
  schumannHz: number[];         // frequencies in Hz
  tensorField: TensorDatum[];   // tensor field data
}

export interface TriStream {
  past: SchumannFrame[];
  present: SchumannFrame[];
  future: SchumannFrame[];
}

export interface WavePacket {
  frequencies: number[];   // intent-derived Hz
  decay: number;          // seconds or unitless
  latticeId: string;      // who
  observerLock: boolean;  // lock state
}

export interface TriWeights {
  past: number;
  present: number;
  future: number;
}

// Golden ratio for unity weighting
export const PHI = (1 + Math.sqrt(5)) / 2;

export const GOLDEN_WEIGHTS: TriWeights = (() => {
  const raw = {
    past: 1 / (PHI * PHI),
    present: 1 / PHI,
    future: 1 - (1 / PHI + 1 / (PHI * PHI))
  };
  const sum = raw.past + raw.present + raw.future;
  return {
    past: raw.past / sum,
    present: raw.present / sum,
    future: raw.future / sum
  };
})();