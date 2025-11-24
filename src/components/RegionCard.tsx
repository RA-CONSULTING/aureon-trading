import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { MapPin, Users, Globe } from 'lucide-react';
import { EmotionalState } from '@/lib/schumann-emotional-mapping';
import { toFixedSafe } from '@/utils/number';
import { useEmotionStream } from '@/hooks/useEmotionStream';
import EmotionBadge from './EmotionBadge';
import EmotionSparkline from './EmotionSparkline';
import { HNCScoreCard } from './HNCScoreCard';
import type { HNCRegionTick } from '@/types/hnc';
export interface Region {
  id: string;
  name: string;
  continent: string;
  climate: string;
  languages: string[];
  imageUrl: string;
  coordinates: { lat: number; lng: number };
  timeZone: string;
  currency: string;
}

interface RegionCardProps {
  region: Region;
  emotionalState?: EmotionalState;
  onClick: (region: Region) => void;
}

export function RegionCard({ region, emotionalState, onClick }: RegionCardProps) {
  const { samples, stats } = useEmotionStream('region', region.id);
  const [hncTick, setHncTick] = useState<HNCRegionTick | null>(null);
  
  useEffect(() => {
    const handleHNCTick = (event: CustomEvent<HNCRegionTick>) => {
      if (event.detail.region === region.id) {
        setHncTick(event.detail);
      }
    };
    
    window.addEventListener('hnc-tick', handleHNCTick as EventListener);
    return () => window.removeEventListener('hnc-tick', handleHNCTick as EventListener);
  }, [region.id]);
  return (
    <Card 
      className="bg-white/10 border-white/20 backdrop-blur-sm hover:bg-white/20 transition-all duration-300 cursor-pointer group relative overflow-hidden"
      onClick={() => onClick(region)}
    >
      {emotionalState && (
        <div 
          className="absolute top-0 left-0 w-full h-1 opacity-80"
          style={{ backgroundColor: emotionalState.color }}
        />
      )}
      <div className="aspect-square overflow-hidden rounded-t-lg">
        <img 
          src={region.imageUrl} 
          alt={region.name}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
        />
      </div>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-white text-lg">{region.name}</CardTitle>
          {emotionalState && (
            <div 
              className="w-3 h-3 rounded-full animate-pulse"
              style={{ backgroundColor: emotionalState.color }}
              title={`${toFixedSafe(emotionalState?.frequency, 1)} Hz`}
            />
          )}
        </div>
        <Badge className="bg-blue-500/20 text-blue-300 border-blue-400/30 w-fit">
          {region.continent}
        </Badge>
      </CardHeader>
      <CardContent className="pt-0 space-y-3">
        <div className="space-y-2 text-sm text-white/70">
          <div>Population: {toFixedSafe(region?.population ? region.population / 1000000 : null, 1)}M</div>
          <div>Languages: {region.languages.slice(0, 2).join(', ')}</div>
          {emotionalState && (
          <div className="text-xs pt-1 border-t border-white/10 space-y-1">
            <div className="flex items-center justify-between">
              <span style={{ color: emotionalState.color }}>
                {(emotionalState.emotionalTags?.[0] ?? '—')} • {toFixedSafe(emotionalState.frequency, 2)} Hz
              </span>
              <EmotionBadge mood={stats.mood} />
            </div>
            <EmotionSparkline data={samples.slice(-60)} />
            <div className="flex items-center justify-between text-white/60">
              <span>24h avg: {toFixedSafe(stats.fAvg, 2)} Hz</span>
              <span>Δ1h: {toFixedSafe(stats.deltaV, 2)} V</span>
            </div>
          </div>
          )}
        </div>
        
        {/* HNC Score Card */}
        <div className="pt-2 border-t border-white/10">
          <HNCScoreCard tick={hncTick} />
        </div>
      </CardContent>
    </Card>
  );
}