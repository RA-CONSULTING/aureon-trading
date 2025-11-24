import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from "@/components/ui/badge";
import type { Country } from "@/lib/countries-data";
import type { EmotionalProfile } from "@/lib/schumann-emotional-mapping";
import { formatPopulation } from "@/utils/number";

interface CountryCardProps {
  country: Country;
  emotionalProfile: EmotionalProfile | null;
  onClick: () => void;
}

export function CountryCard({ country, emotionalProfile, onClick }: CountryCardProps) {

  const getFrequencyColor = (frequency?: number) => {
    if (!frequency) return 'bg-gray-500';
    if (frequency >= 8.0) return 'bg-red-500';
    if (frequency >= 7.8) return 'bg-orange-500';
    return 'bg-green-500';
  };

  return (
    <Card 
      className="cursor-pointer hover:shadow-lg transition-all duration-300 hover:scale-105 group"
      onClick={onClick}
    >
      <div className="relative overflow-hidden rounded-t-lg">
        <img 
          src={country.imageUrl} 
          alt={country.name}
          className="w-full h-48 object-cover group-hover:scale-110 transition-transform duration-300"
        />
        {emotionalProfile && (
          <div className="absolute top-2 right-2">
            <div className={`w-3 h-3 rounded-full ${getFrequencyColor(emotionalProfile.dominantFrequency)} animate-pulse`} />
          </div>
        )}
      </div>
      
      <CardHeader className="pb-2">
        <CardTitle className="flex justify-between items-center">
          <span>{country.name}</span>
          <Badge variant="secondary">{country.currency}</Badge>
        </CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-2">
        <div className="flex justify-between text-sm text-gray-600">
          <span>Population: {formatPopulation(country.population)}</span>
          <span>Capital: {country.capital}</span>
        </div>
        
        {emotionalProfile && (
          <div className="space-y-1">
            <div className="flex justify-between text-xs">
              <span>Emotional State:</span>
              <span className="font-medium">{emotionalProfile.emotionalState}</span>
            </div>
            <div className="flex flex-wrap gap-1">
              {emotionalProfile.emotionalTags.slice(0, 2).map(tag => (
                <Badge key={tag} variant="outline" className="text-xs">{tag}</Badge>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}