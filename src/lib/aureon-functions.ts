import { EarthPacket, HumanPacket, ResonanceReport, NoteID, GriWeights } from './aureon';
import { NOTES } from './aureon-data';
import { normalizeToWindow, logistic, clamp } from './aureon-utils';
import { mapFrequencyToEmotion } from './aureon';

// ---------- Earth→Harmonic projection & alignment
export function projectToHarmonicWindow(f: number, lo=256, hi=512): number {
  if (!isFinite(f) || f<=0) return NaN;
  while (f < lo) f *= 2;
  while (f >= hi) f /= 2;
  return f;
}

export function earthAlignmentScore(earth: EarthPacket, humanMainFreq?: number, sigmaHz = 6): number {
  const bands = (earth.schumann||[]).map(f=>projectToHarmonicWindow(f));
  const targets = bands.concat(typeof humanMainFreq === 'number' ? [normalizeToWindow(humanMainFreq)] : []);
  if (!targets.length) return 0;
  
  const scorePerTarget = targets.map(ft => {
    const d = NOTES.map(n=> Math.abs(ft - n.hz));
    const w = d.map(x=> Math.exp(-(x*x)/(2*sigmaHz*sigmaHz)));
    return Math.max(...w);
  });
  const avg = scorePerTarget.reduce((a,b)=>a+b,0) / scorePerTarget.length;
  return clamp(avg, 0, 1);
}

// ---------- Coherence & Global Resonance Index (GRI)
export const DEFAULT_WEIGHTS: GriWeights = { a:1.6, b:1.0, c:0.8, d:0.6, e:0.8, g:0.4 };

export function computeGRI(
  earth: EarthPacket, 
  human: HumanPacket, 
  weights: GriWeights = DEFAULT_WEIGHTS
): { gri:number; align:number; breakdown: ResonanceReport['contributors'] } {
  const align = earthAlignmentScore(earth, human.mainFreq);

  const rmssd = human.rmssd ?? 0;
  const hf = human.hf ?? 0, lf = human.lf ?? 0;
  const lf_hf = human.lf_hf ?? (lf>0? lf/Math.max(hf,1e-6) : 0);
  const hrv = clamp((rmssd/60) * 0.6 + (hf/(lf+hf+1e-6)) * 0.4, 0, 1);

  const alpha = clamp(human.alpha ?? 0, 0, 1);
  const balance = Math.exp(-Math.pow(Math.log((lf_hf||1)),2) / (2*0.35*0.35));

  const kp = earth.kp ?? 2;
  const kpInv = 1 - clamp(kp/9, 0, 1);
  const lightning = earth.lightningDensity ?? 0;
  const lightInv = 1 - clamp(lightning/100, 0, 1);

  const z = weights.a*align + weights.b*hrv + weights.c*alpha + weights.d*balance + weights.e*kpInv + weights.g*lightInv;
  const gri = Math.round(100 * logistic(z - 2.5));

  return {
    gri, align,
    breakdown: { freqAlign: align, hrv, alpha, balance, kp: kpInv, lightning: lightInv }
  };
}

// ---------- Entraining suggestions
export function suggestEntrainments(note: NoteID, coherence = 0.5): string[] {
  const base: Record<NoteID,string[]> = {
    C:["Box breathing 4-4-4-4","Low-tempo drums","Red ambient"],
    Cs:["Soft arpeggios","Stepwise breath ramps","Warm red-orange"],
    D:["Coherent breathing 5-5","Gentle crescendos","Orange ambient"],
    Ds:["Suspended chords","Micro-breaks","Amber light"],
    E:["Laughter cues","Bright melodies","Yellow wash"],
    F:["Heart-breath 6 cpm","Slow strings/choir","Green ambient"],
    Fs:["Grounded stance practice","Percussive accents","Teal-blue"],
    G:["Steady pulse/gait sync","Blue ambient","Even pacing"],
    Gs:["Swing rhythms","Free play tasks","Blue-indigo"],
    A:["4-16 breath-holds","Cathedral reverb pads","Indigo"],
    As:["Drones / overtones","Candle gaze","Violet"],
    B:["Binaural lift","Silent sitting","Violet-deep"],
    C5:["Cadence resolution","Soft white spectrum","Long exhales"],
  };
  const items = base[note] ?? [];
  if (coherence < 0.4) return ["Return to body scan", "Lengthen exhale (2:1)", ...items];
  return items;
}

// ---------- High-level orchestrator
export function analyze(
  fIn: number,
  earth: EarthPacket = { schumann: [] },
  human: HumanPacket = {}
): ResonanceReport {
  const state = mapFrequencyToEmotion(fIn);
  const { gri, align, breakdown } = computeGRI(earth, human);
  return { state, gri, alignment: align, contributors: breakdown };
}