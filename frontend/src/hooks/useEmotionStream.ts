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
  
  useEffect(() => {
    if (!streams.has(key)) streams.set(key, []);
  }, [key]);
  
  useEffect(() => { 
    const i=setInterval(()=>{ 
      setTick(x=>x+1); 
    }, 30_000); 
    return ()=>clearInterval(i); 
  }, [key]);
  
  const samples = streams.get(key) ?? []; 
  const stats: EmotionStats24h = useMemo(()=>summarize24h(samples),[samples]);
  return { samples, stats };
}
