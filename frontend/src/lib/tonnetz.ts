/**
 * Tonnetz Lattice for 12TET Harmonic Mapping
 * Maps frequencies to musical pitch classes using lattice coordinates
 */

export interface LatticePoint {
  noteIndex: number;   // 0..11 (C..B)
  x: number;           // steps of perfect fifth (+7)
  y: number;           // steps of major third (+4)
}

const NOTE_IDS = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"] as const;
export type NoteID = typeof NOTE_IDS[number];

export const noteIndexFromId = (id: NoteID) => NOTE_IDS.indexOf(id);
export const idFromNoteIndex = (i: number) => NOTE_IDS[(i % 12 + 12) % 12];

/** Find small integers (a,b) with (7a+4b) % 12 == n, minimizing |a|+|b| */
export function pitchClassToLattice(n: number): LatticePoint {
  let best = {a:0,b:0, cost: 1e9};
  for (let a = -6; a <= 6; a++) {
    for (let b = -6; b <= 6; b++) {
      if (((7*a + 4*b) % 12 + 12) % 12 === ((n % 12) + 12) % 12) {
        const cost = Math.abs(a) + Math.abs(b) + 0.001*Math.abs(a*b);
        if (cost < best.cost) best = {a,b,cost};
      }
    }
  }
  return { noteIndex: ((n%12)+12)%12, x: best.a, y: best.b };
}

/** 12TET semitone number relative to C=256Hz; octave-agnostic pitch class */
export function freqToPitchClass(f: number): number {
  const semis = 12 * Math.log2(f / 256); // C=256 reference
  return Math.round(semis) % 12;
}

/** Soft Gaussian weights over nearest 3 pitch classes */
export function freqToPitchWeights(f: number) {
  const semis = 12 * Math.log2(f / 256);
  const base = Math.round(semis);
  const spread = 0.45; // tweak: narrower = crisper nodes
  const idxs = [base-1, base, base+1];
  const weights = idxs.map(k => Math.exp(-0.5 * Math.pow((semis - k)/spread, 2)));
  const sum = weights.reduce((a,b)=>a+b,0) || 1;
  return idxs.map((k,i) => ({
    semitone: k,
    noteIndex: ((k%12)+12)%12,
    w: weights[i]/sum
  }));
}

/** Map one frequency into lattice "blobs" (3 neighbors) */
export function freqToLatticeBlobs(f: number) {
  return freqToPitchWeights(f).map(({noteIndex,w}) => {
    const p = pitchClassToLattice(noteIndex);
    return {...p, weight: w};
  });
}