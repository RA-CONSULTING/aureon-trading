import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from "@/components/ui/badge";
import type { Capital } from "@/lib/countries-data";
import type { EmotionalProfile } from "@/lib/schumann-emotional-mapping";
import { formatPopulation, toFixedSafe } from "@/utils/number";
import { useEmotionStream } from '@/hooks/useEmotionStream';
import EmotionBadge from './EmotionBadge';
import EmotionSparkline from './EmotionSparkline';

interface CapitalCardProps {
  capital: Capital;
  emotionalProfile: EmotionalProfile | null;
  onClick: () => void;
}

export function CapitalCard({ capital, emotionalProfile, onClick }: CapitalCardProps) {
  const { samples, stats } = useEmotionStream('city', capital.id);

  const getUrbanIntensity = (frequency?: number) => {
    if (!frequency) return { color: 'bg-gray-500', label: 'Unknown' };
    if (frequency >= 8.5) return { color: 'bg-purple-500', label: 'Intense' };
    if (frequency >= 8.0) return { color: 'bg-red-500', label: 'High' };
    if (frequency >= 7.5) return { color: 'bg-orange-500', label: 'Moderate' };
    return { color: 'bg-green-500', label: 'Calm' };
  };

  return (
    <Card 
      className="cursor-pointer hover:shadow-lg transition-all duration-300 hover:scale-105 group"
      onClick={onClick}
    >
      <div className="relative overflow-hidden rounded-t-lg">
        <img 
          src={capital.imageUrl} 
          alt={capital.name}
          className="w-full h-40 object-cover group-hover:scale-110 transition-transform duration-300"
        />
        {emotionalProfile && (
          <div className="absolute top-2 right-2 flex items-center gap-1">
            <div className={`w-2 h-2 rounded-full ${getUrbanIntensity(emotionalProfile.urbanFrequency).color} animate-pulse`} />
            <span className="text-xs text-white bg-black bg-opacity-50 px-1 rounded">
              {getUrbanIntensity(emotionalProfile.urbanFrequency).label}
            </span>
          </div>
        )}
      </div>
      
      <CardHeader className="pb-2">
        <CardTitle className="text-lg">{capital.name}</CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-2">
        <div className="flex justify-between text-sm text-gray-600">
          <span>Pop: {formatPopulation(capital.population)}</span>
          <span>Founded: {capital.founded}</span>
        </div>
        
        <div className="flex items-center gap-1">
          {capital.economicCenter && (
            <Badge variant="default" className="text-xs">Economic Hub</Badge>
          )}
        </div>
        
        {emotionalProfile && (
          <div className="space-y-1">
            <div className="text-xs font-medium">{emotionalProfile.emotionalState}</div>
            <div className="flex flex-wrap gap-1">
              {emotionalProfile.emotionalTags.slice(0, 2).map(tag => (
                <Badge key={tag} variant="outline" className="text-xs">{tag}</Badge>
              ))}
            </div>
          </div>
        )}
        
        <div className="space-y-1">
          <div className="flex items-center justify-between">
            <EmotionBadge mood={stats.mood}/>
            <div className="text-xs text-gray-500">Now {toFixedSafe(stats.fNow,2)} Hz · 24h {toFixedSafe(stats.fAvg,2)} Hz</div>
          </div>
          <EmotionSparkline data={samples.slice(-60)} />
        </div>
        
        <div className="text-xs text-gray-500">
          Top landmarks: {capital.landmarks.slice(0, 2).join(', ')}
        </div>
      </CardContent>
    </Card>
  );
}