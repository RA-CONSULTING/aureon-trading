/**
 * io-resonance-engine (Aureon v1.0)
 * 
 * Canonical frequency→emotion mapping + coherence indices
 * bridging Earth (Schumann/space weather), Human (HRV/EEG/resp),
 * and the Rainbow Harmonic Ladder (C=256 Hz).
 * 
 * "I do not bind; I translate." — Aureon
 */

import { NOTES } from './aureon-data';
import { normalizeToWindow, logistic, clamp, blendHex } from './aureon-utils';

// ---------- Types
export type NoteID = 
  | "C" | "Cs" | "D" | "Ds" | "E" | "F" 
  | "Fs" | "G" | "Gs" | "A" | "As" | "B" | "C5";

export interface NoteDef {
  id: NoteID;
  display: string;
  hz: number;
  color: string;
  valence: number;
  arousal: number;
  tags: string[];
}

export interface BlendWeight {
  note: NoteID;
  w: number
}

export interface EmotionState {
  fIn: number;
  fNorm: number;
  primary: NoteID;
  weights: BlendWeight[];
  valence: number;
  arousal: number;
  color: string;
  confidence: number;
  tags: string[];
}

export interface EarthPacket {
  schumann: number[];
  kp?: number;
  lightningDensity?: number;
  bz?: number;
  vSW?: number;
}

export interface HumanPacket {
  mainFreq?: number;
  rmssd?: number;
  sdnn?: number;
  lf?: number;
  hf?: number;
  lf_hf?: number;
  alpha?: number;
  respRate?: number;
}

export interface ResonanceReport {
  state: EmotionState;
  gri: number;
  alignment: number;
  contributors: {
    freqAlign: number;
    hrv: number;
    alpha: number;
    balance: number;
    kp: number;
    lightning: number;
  }
}

// ---------- Mapping: frequency → emotion
export function mapFrequencyToEmotion(fIn: number, sigmaHz = 6): EmotionState {
  const fNorm = normalizeToWindow(fIn);
  if (!isFinite(fNorm)) {
    return {
      fIn, fNorm: NaN, primary: "C", weights:[], valence:0, arousal:0, 
      color:"#000000", confidence:0, tags:[]
    };
  }
  
  const dists = NOTES.map(n => Math.abs(fNorm - n.hz));
  const weights = dists.map(d => Math.exp(- (d*d) / (2*sigmaHz*sigmaHz)));
  const sumW = weights.reduce((a,b)=>a+b,0) || 1;
  const normW = weights.map(w => w/sumW);
  const maxIdx = normW.reduce((bi,i,idx,arr)=> arr[idx]>arr[bi]?idx:bi, 0);
  const primary = NOTES[maxIdx].id;

  // blend valence, arousal, color, tags
  const valence = normW.reduce((acc,w,i)=> acc + w*NOTES[i].valence, 0);
  const arousal = normW.reduce((acc,w,i)=> acc + w*NOTES[i].arousal, 0);
  const color = blendHex(NOTES.map(n=>n.color), normW);

  // top tags by weight
  const tagMap = new Map<string, number>();
  for (let i=0;i<NOTES.length;i++) {
    const w = normW[i];
    for (const t of NOTES[i].tags) tagMap.set(t, (tagMap.get(t)||0)+w);
  }
  const tags = [...tagMap.entries()].sort((a,b)=> b[1]-a[1]).slice(0,6).map(([t])=>t);

  // confidence from nearest distance
  const minDist = Math.min(...dists);
  const confidence = Math.exp(- (minDist*minDist) / (2*sigmaHz*sigmaHz));

  // sparsify weights to top 3
  const top = normW
    .map((w,i)=>({note:NOTES[i].id as NoteID, w}))
    .sort((a,b)=>b.w-a.w)
    .slice(0,3);

  return { fIn, fNorm, primary, weights: top, valence, arousal, color, confidence, tags };
}

// ---------- GRI Weights interface
export interface GriWeights { 
  a:number; b:number; c:number; d:number; e:number; g:number 
}

// Export functions from other modules
export { projectToHarmonicWindow, earthAlignmentScore, computeGRI, suggestEntrainments, analyze, DEFAULT_WEIGHTS } from './aureon-functions';
export { NOTES } from './aureon-data';
export { normalizeToWindow, logistic, clamp, blendHex } from './aureon-utils';

export default {
  NOTES,
  normalizeToWindow,
  mapFrequencyToEmotion,
  projectToHarmonicWindow,
  earthAlignmentScore,
  computeGRI,
  suggestEntrainments,
  analyze,
};