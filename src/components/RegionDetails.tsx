import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { X } from 'lucide-react';
import { Region } from './RegionCard';
import { EmotionalState } from '@/lib/schumann-emotional-mapping';
import { EmotionalResonanceDisplay } from './EmotionalResonanceDisplay';
import { toFixedSafe } from '@/utils/number';
import NewsCrossRef from './NewsCrossRef';
import { useEmotionStream } from '@/hooks/useEmotionStream';
import EmotionBadge from './EmotionBadge';
import EmotionSparkline from './EmotionSparkline';

interface RegionDetailsProps {
  region: Region | null;
  emotionalState?: EmotionalState;
  onClose: () => void;
}

export default function RegionDetails({ region, emotionalState, onClose }: RegionDetailsProps) {
  const { samples, stats } = useEmotionStream('region', region?.id || '');
  if (!region) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <Card className="bg-black/80 border-white/20 backdrop-blur-md max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-white text-2xl">{region.name}</CardTitle>
            <Badge className="bg-blue-500/20 text-blue-300 border-blue-400/30 mt-2">
              {region.continent}
            </Badge>
          </div>
          <Button 
            variant="ghost" 
            size="icon"
            onClick={onClose}
            className="text-white hover:bg-white/10"
          >
            <X className="h-5 w-5" />
          </Button>
        </CardHeader>
        <CardContent>
          <div className="aspect-video overflow-hidden rounded-lg mb-6">
            <img 
              src={region.imageUrl} 
              alt={region.name}
              className="w-full h-full object-cover"
            />
          </div>
          
          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div>
                <h3 className="text-white font-semibold mb-2">Demographics</h3>
                <div className="text-white/70 space-y-1">
                  <div>Population: {region.population.toLocaleString()}</div>
                  <div>Area: {region.area.toLocaleString()} km²</div>
                  <div>Density: {toFixedSafe(region?.population && region?.area ? region.population / region.area : null, 1)} per km²</div>
                </div>
              </div>
              
              <div>
                <h3 className="text-white font-semibold mb-2">Geography</h3>
                <div className="text-white/70 space-y-1">
                  <div>Climate: {region.climate}</div>
                  <div>Coordinates: {region.coordinates.lat}°, {region.coordinates.lng}°</div>
                  <div>Time Zone: {region.timeZone}</div>
                </div>
              </div>
              
              <div>
                <h3 className="text-white font-semibold mb-2">Culture</h3>
                <div className="text-white/70 space-y-1">
                  <div>Languages: {region.languages.join(', ')}</div>
                  <div>Currency: {region.currency}</div>
                </div>
              </div>
            </div>
            
            <div>
              {emotionalState && (
                <EmotionalResonanceDisplay 
                  emotionalState={emotionalState}
                  regionName={region.name}
                />
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}