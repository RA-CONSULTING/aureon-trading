/**
Aureon Intervals Utils - Complete interval detection system
*/

import { NoteID, NoteDef, BlendWeight, IntervalAffect, IntervalOptions, CHROMATIC_ORDER } from './aureon-intervals';

// --- helpers
function noteIndex(id: NoteID): number {
  return CHROMATIC_ORDER.indexOf(id);
}

function semitoneDistance(a: NoteID, b: NoteID): number {
  const i = noteIndex(a), j = noteIndex(b);
  if (i<0 || j<0) return 0;
  let d = Math.abs(j - i) % 12;
  if (d > 6) d = 12 - d;
  return d;
}

function intervalNameFromSemitones(s: number): string {
  switch (s) {
    case 0: return "P1"; case 1: return "m2"; case 2: return "M2";
    case 3: return "m3"; case 4: return "M3"; case 5: return "P4";
    case 6: return "TT"; case 7: return "P5"; case 8: return "m6";
    case 9: return "M6"; case 10: return "m7"; case 11: return "M7";
    case 12: return "P8"; default: return `${s}`;
  }
}

const INTERVAL_AFFECT: Record<string, { tags: string[]; dv: number; da: number }> = {
  P1: { tags:["Singularity","Focus"], dv:+0.05, da:-0.05 },
  m2: { tags:["Tension","Edge"], dv:-0.10, da:+0.20 },
  M2: { tags:["Motion","Openness"], dv:+0.05, da:+0.10 },
  m3: { tags:["Hope","Care"], dv:+0.10, da:+0.05 },
  M3: { tags:["Joy","Confidence"], dv:+0.20, da:+0.10 },
  P4: { tags:["Inspiration","Clarity"], dv:+0.18, da:+0.08 },
  TT: { tags:["Healing","Integration"], dv:+0.15, da:+0.00 },
  P5: { tags:["Stability","Action"], dv:+0.16, da:+0.06 },
  m6: { tags:["Courage","Warmth"], dv:+0.08, da:+0.02 },
  M6: { tags:["Trust","Radiance"], dv:+0.15, da:+0.08 },
  m7: { tags:["Awakening","Distance"], dv:+0.10, da:+0.04 },
  M7: { tags:["Resolution","Clarity"], dv:+0.05, da:+0.12 },
  P8: { tags:["Unity","Return"], dv:+0.22, da:+0.00 },
};

export function blendAffect(
  notes: NoteDef[],
  weights: BlendWeight[]
): { valence: number; arousal: number; tags: string[] } {
  let V=0, A=0, S=0;
  const tagMap = new Map<string, number>();
  for (const w of weights){
    const n = notes.find(x=> x.id===w.note);
    if (!n) continue;
    V += n.valence * w.w;
    A += n.arousal * w.w;
    S += w.w;
    for (const t of n.tags) tagMap.set(t, (tagMap.get(t)||0) + w.w);
  }
  S = S || 1;
  V/=S; A/=S;
  const tags = [...tagMap.entries()].sort((a,b)=> b[1]-a[1]).slice(0,6).map(([t])=>t);
  return { valence: V, arousal: A, tags };
}

export function bestIntervalPair(weights: BlendWeight[], opts: IntervalOptions = {}): [BlendWeight, BlendWeight] | null {
  const minW = opts.minPairWeight ?? 0.3;
  const minSemi = opts.minSemitones ?? 2;
  const sorted = [...weights].sort((a,b)=> b.w - a.w);
  let best: [BlendWeight, BlendWeight] | null = null;
  let bestScore = -1;
  for (let i=0;i<sorted.length;i++){
    for (let j=i+1;j<sorted.length;j++){
      const a = sorted[i], b = sorted[j];
      const semi = semitoneDistance(a.note, b.note);
      if (semi < minSemi) continue;
      const score = a.w + b.w;
      if (score > bestScore){
        bestScore = score;
        best = [a,b];
      }
    }
  }
  if (best && (best[0].w + best[1].w) >= minW) return best;
  return null;
}

export function mapIntervalAffect(
  notes: NoteDef[],
  a: BlendWeight,
  b: BlendWeight,
  opts: IntervalOptions = {}
): IntervalAffect {
  const biasStrength = opts.biasStrength ?? 0.25;
  
  const root = (a.w > b.w) ? a.note : (a.w < b.w) ? b.note : 
    (noteIndex(a.note) <= noteIndex(b.note) ? a.note : b.note);
  const other = (root===a.note) ? b.note : a.note;
  
  const semi = semitoneDistance(root, other);
  const name = intervalNameFromSemitones(semi);
  const base = INTERVAL_AFFECT[name] || { tags:["Compound"], dv:0, da:0 };
  
  const blend = blendAffect(notes, [a,b]);
  const valence = Math.min(1, Math.max(-1, blend.valence + biasStrength*base.dv));
  const arousal = Math.min(1, Math.max(0, blend.arousal + biasStrength*base.da));
  const tags = Array.from(new Set([...base.tags, ...blend.tags])).slice(0,8);
  
  return {
    interval: name,
    semitones: semi,
    root,
    other,
    tags,
    valence,
    arousal,
    weight: a.w + b.w
  };
}

export function detectIntervalAffect(
  notes: NoteDef[],
  weights: BlendWeight[],
  opts: IntervalOptions = {}
): IntervalAffect | null {
  const pair = bestIntervalPair(weights, opts);
  if (!pair) return null;
  return mapIntervalAffect(notes, pair[0], pair[1], opts);
}