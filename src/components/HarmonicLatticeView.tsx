import React, { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import LatticeMap from './LatticeMap';
import { freqToLatticeBlobs } from '@/lib/tonnetz';
import { useEmotionStream } from '@/hooks/useEmotionStream';

interface Props {
  className?: string;
}

// Schumann resonance frequencies
const SCHUMANN_FREQUENCIES = [7.83, 14.3, 20.8, 27.3, 33.8, 39.3, 45.9];

export default function HarmonicLatticeView({ className = '' }: Props) {
  const { currentEmotion } = useEmotionStream();
  
  // Map Schumann frequencies to lattice blobs with emotional weighting
  const latticeBlobs = useMemo(() => {
    const baseIntensity = 0.3 + (currentEmotion?.arousal || 0) * 0.4;
    const harmonicShift = (currentEmotion?.valence || 0) * 2; // shift frequencies slightly
    
    return SCHUMANN_FREQUENCIES.flatMap((freq, i) => {
      const adjustedFreq = freq + harmonicShift * (i + 1);
      const intensity = baseIntensity * (1 - i * 0.1); // decay with higher harmonics
      
      return freqToLatticeBlobs(adjustedFreq).map(blob => ({
        ...blob,
        weight: blob.weight * intensity
      }));
    }).filter(blob => blob.weight > 0.05); // filter weak blobs
  }, [currentEmotion]);

  const emotionLabel = currentEmotion ? 
    `V:${currentEmotion.valence.toFixed(2)} A:${currentEmotion.arousal.toFixed(2)}` : 
    'No signal';

  return (
    <Card className={`bg-zinc-900/50 border-zinc-700 ${className}`}>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg font-medium text-white flex items-center justify-between">
          Harmonic Lattice Field
          <span className="text-sm text-zinc-400 font-normal">{emotionLabel}</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <LatticeMap 
          blobs={latticeBlobs}
          cellSize={50}
          radius={8}
          className="min-h-[300px]"
        />
        <div className="mt-4 text-xs text-zinc-500">
          Schumann resonances mapped to Tonnetz lattice • Emotional state modulates intensity
        </div>
      </CardContent>
    </Card>
  );
}