export type Mood = 'Happy' | 'Calm' | 'Stressed' | 'Sad' | 'Neutral';

export function classifyMood(v?: number|null, a?: number|null): Mood {
  const V = typeof v === 'number' ? v : 0.5;
  const A = typeof a === 'number' ? a : 0.5;
  if (V >= 0.65 && A >= 0.6) return 'Happy';
  if (V >= 0.65 && A < 0.6)  return 'Calm';
  if (V <= 0.35 && A >= 0.6) return 'Stressed';
  if (V <= 0.35 && A < 0.6)  return 'Sad';
  return 'Neutral';
}

export interface EmotionSample { t: number; f: number; v: number; a: number; }
export interface EmotionStats24h {
  count: number; vAvg: number; aAvg: number; fAvg: number;
  vNow: number|null; aNow: number|null; fNow: number|null;
  mood: Mood; deltaV: number; deltaA: number; deltaF: number;
}

export function summarize24h(samples: EmotionSample[]): EmotionStats24h {
  const now = Date.now(), last24 = samples.filter(s => now - s.t <= 86_400_000);
  const n = last24.length || 1;
  const sum = (k: 'v'|'a'|'f') => last24.reduce((x,s)=>x+s[k],0)/n;
  const fAvg = sum('f'), vAvg = sum('v'), aAvg = sum('a');
  const last = last24[last24.length-1] ?? null;
  const oneHour = 3_600_000;
  const avg = (arr: EmotionSample[], k:'v'|'a'|'f') => arr.length?arr.reduce((x,s)=>x+s[k],0)/arr.length:0;
  const w1 = last24.filter(s => now - s.t <= oneHour);
  const w2 = last24.filter(s => now - s.t > oneHour && now - s.t <= 2*oneHour);
  return {
    count: last24.length, vAvg, aAvg, fAvg,
    vNow: last?.v ?? null, aNow: last?.a ?? null, fNow: last?.f ?? null,
    mood: classifyMood(vAvg, aAvg),
    deltaV: avg(w1,'v')-avg(w2,'v'), deltaA: avg(w1,'a')-avg(w2,'a'), deltaF: avg(w1,'f')-avg(w2,'f')
  };
}