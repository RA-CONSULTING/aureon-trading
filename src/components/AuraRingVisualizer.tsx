import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { fmt } from '@/utils/number';

interface AuraRingProps {
  hue: number;
  glow: number;
  calm: number;
  hrv: number;
  gsr: number;
  timestampUs?: number;
}

export function AuraRingVisualizer({ hue, glow, calm, hrv, gsr, timestampUs }: AuraRingProps) {
  const ringStyle = {
    background: `conic-gradient(
      hsl(${hue}, 70%, 50%) 0deg,
      hsl(${(hue + 60) % 360}, 70%, 60%) 120deg,
      hsl(${(hue + 120) % 360}, 70%, 50%) 240deg,
      hsl(${hue}, 70%, 50%) 360deg
    )`,
    filter: `blur(${Math.max(0, 1 - glow)}px) brightness(${0.5 + glow * 0.5})`,
    opacity: 0.3 + glow * 0.7
  };

  return (
    <Card className="bg-black/50 border-zinc-700">
      <CardContent className="p-6 flex flex-col items-center">
        {timestampUs && (
          <div className="text-xs text-zinc-400 mb-2">
            @ {Math.round(timestampUs)} μs
          </div>
        )}
        <div className="relative w-32 h-32 mb-4">
          {/* Outer ring */}
          <div 
            className="absolute inset-0 rounded-full"
            style={ringStyle}
          />
          {/* Inner ring */}
          <div 
            className="absolute inset-4 rounded-full bg-black/80 border-2"
            style={{ borderColor: `hsl(${hue}, 70%, 50%)` }}
          />
          {/* Center dot */}
          <div 
            className="absolute top-1/2 left-1/2 w-4 h-4 rounded-full transform -translate-x-1/2 -translate-y-1/2"
            style={{ backgroundColor: `hsl(${hue}, 70%, 60%)` }}
          />
        </div>
        
        <div className="grid grid-cols-3 gap-2 text-xs text-center w-full">
          <div className="space-y-1">
            <div className="text-zinc-400">Calm</div>
            <div className="font-mono">{fmt(calm, 2)}</div>
          </div>
          <div className="space-y-1">
            <div className="text-zinc-400">HRV</div>
            <div className="font-mono">{fmt(hrv, 2)}</div>
          </div>
          <div className="space-y-1">
            <div className="text-zinc-400">GSR</div>
            <div className="font-mono">{fmt(gsr, 2)}</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default AuraRingVisualizer;