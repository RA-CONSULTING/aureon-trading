import { useEffect, useMemo, useState } from 'react';
import { summarize24h, type EmotionSample, type EmotionStats24h } from '@/lib/mood';

type Kind = 'region'|'city'; 
type Key = `${Kind}:${string}`;
const streams = new Map<Key, EmotionSample[]>();

function push(key: Key, s: EmotionSample) {
  const arr = streams.get(key) ?? []; 
  arr.push(s);
  const cutoff = Date.now()-86_400_000;
  const trimmed = arr.filter(x=>x.t>=cutoff); 
  while (trimmed.length>10000) trimmed.shift();
  streams.set(key, trimmed);
}

export function ingestEmotionSample(kind: Kind, id: string, s: EmotionSample){ 
  push(`${kind}:${id}`, s); 
}

export function useEmotionStream(kind: Kind, id: string) {
  const key = `${kind}:${id}` as Key; 
  const [, setTick] = useState(0);
  
  useEffect(() => { // seed if empty (dev)
    if (streams.has(key)) return;
    const now = Date.now(); 
    const seed: EmotionSample[] = [];
    for (let i=120;i>=0;i--) { 
      const t=now-i*30_000, f=7.83+(Math.random()-0.5)*1.2, v=0.5+(Math.random()-0.5)*0.3, a=v+(Math.random()-0.5)*0.2; 
      seed.push({t,f,v,a}); 
    }
    streams.set(key, seed);
  }, [key]);
  
  useEffect(() => { 
    const i=setInterval(()=>{ 
      push(key,{t:Date.now(), f:7.83+(Math.random()-0.5), v:0.5+(Math.random()-0.5)*0.2, a:0.5+(Math.random()-0.5)*0.2}); 
      setTick(x=>x+1); 
    }, 30_000); 
    return ()=>clearInterval(i); 
  }, [key]);
  
  const samples = streams.get(key) ?? []; 
  const stats: EmotionStats24h = useMemo(()=>summarize24h(samples),[samples]);
  return { samples, stats };
}