/**
Aureon Intervals Mapping - Final interval affect mapping functions
*/

import { NoteID, NoteDef, BlendWeight, IntervalAffect, IntervalOptions, CHROMATIC_ORDER } from './aureon-intervals';
import { blendAffect, bestIntervalPair } from './aureon-intervals-functions';

// Interval affect dictionary (compound emotions)
const INTERVAL_AFFECT: Record<string, { tags: string[]; dv: number; da: number }> = {
  P1:  { tags:["Singularity","Focus","Oneness"],                         dv:+0.05, da:-0.05 },
  m2:  { tags:["Tension","Edge","Alertness"],                             dv:-0.10, da:+0.20 },
  M2:  { tags:["Curious Motion","Reach","Openness"],                     dv:+0.05, da:+0.10 },
  m3:  { tags:["Tender Hope","Yearning-with-Care"],                        dv:+0.10, da:+0.05 },
  M3:  { tags:["Secure Joy","Warm Confidence"],                            dv:+0.20, da:+0.10 },
  P4:  { tags:["Illuminated Inspiration","Uplifted Clarity"],             dv:+0.18, da:+0.08 },
  TT:  { tags:["Transformational Healing","Deep Integration"],             dv:+0.15, da:+0.00 },
  P5:  { tags:["Stable Confidence","Belonging-in-Action"],                 dv:+0.16, da:+0.06 },
  m6:  { tags:["Bittersweet Courage","Protective Warmth"],                 dv:+0.08, da:+0.02 },
  M6:  { tags:["Expansive Warmth","Radiant Trust"],                        dv:+0.15, da:+0.08 },
  m7:  { tags:["Poised Awakening","Wise Distance"],                        dv:+0.10, da:+0.04 },
  M7:  { tags:["Imminent Resolution","Tense Clarity"],                     dv:+0.05, da:+0.12 },
  P8:  { tags:["Fulfilled Return","Octave Unity"],                         dv:+0.22, da:+0.00 },
};

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

/**
Map a note pair to an IntervalAffect with blended affect values.
*/
export function mapIntervalAffect(
  notes: NoteDef[],
  a: BlendWeight,
  b: BlendWeight,
  opts: IntervalOptions = {}
): IntervalAffect {
  const biasStrength = opts.biasStrength ?? 0.25;
  
  // choose root as the higher weight; tie-breaker: lower chromatic index
  const root = (a.w > b.w) ? a.note : (a.w < b.w) ? b.note : 
    (noteIndex(a.note) <= noteIndex(b.note) ? a.note : b.note);
  const other = (root===a.note) ? b.note : a.note;
  
  const semi = semitoneDistance(root, other);
  const name = intervalNameFromSemitones(semi);
  const base = INTERVAL_AFFECT[name] || { tags:["Compound Affect"], dv:0, da:0 };
  
  const blend = blendAffect(notes, [a,b]);
  const valence = Math.min(1, Math.max(-1, blend.valence + biasStrength*base.dv));
  const arousal = Math.min(1, Math.max(0,   blend.arousal + biasStrength*base.da));
  const tags = Array.from(new Set([ ...base.tags, ...blend.tags ])).slice(0,8);
  
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

/**
High-level: derive best IntervalAffect from a set of note weights.
Returns null if no suitable pair.
*/
export function detectIntervalAffect(
  notes: NoteDef[],
  weights: BlendWeight[],
  opts: IntervalOptions = {}
): IntervalAffect | null {
  const pair = bestIntervalPair(weights, opts);
  if (!pair) return null;
  return mapIntervalAffect(notes, pair[0], pair[1], opts);
}

export default {
  detectIntervalAffect,
  mapIntervalAffect,
};