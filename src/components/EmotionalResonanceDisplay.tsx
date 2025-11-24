import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { EmotionalState } from '@/lib/schumann-emotional-mapping';
import { toFixedSafe } from '@/utils/number';

interface EmotionalResonanceDisplayProps {
  emotionalState: EmotionalState;
  regionName: string;
}

export const EmotionalResonanceDisplay: React.FC<EmotionalResonanceDisplayProps> = ({
  emotionalState,
  regionName
}) => {
  const valencePercentage = Math.round(emotionalState.valence * 100);
  const arousalPercentage = Math.round(emotionalState.arousal * 100);
  const intensityPercentage = Math.round(emotionalState.intensity * 100);

  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <div 
            className="w-4 h-4 rounded-full" 
            style={{ backgroundColor: emotionalState.color }}
          />
          {regionName} Emotional Resonance
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Frequency Display */
        <div className="flex justify-between items-center">
          <span className="text-sm font-medium">Schumann Frequency</span>
          <span className="text-lg font-bold text-foreground">
            {toFixedSafe(emotionalState?.frequency, 2)} Hz
          </span>
        </div>

        {/* Dominant Note */}
        <div className="flex justify-between items-center">
          <span className="text-sm font-medium">Dominant Note</span>
          <Badge variant="outline" style={{ borderColor: emotionalState.color }}>
            {emotionalState.dominantNote}
          </Badge>
        </div>

        {/* Emotional Metrics */}
        <div className="space-y-3">
          <div>
            <div className="flex justify-between text-sm font-medium text-gray-800 dark:text-gray-200 mb-1">
              <span>Valence (Positivity)</span>
              <span>{valencePercentage}%</span>
            </div>
            <Progress 
              value={valencePercentage} 
              className="h-2"
              style={{ 
                background: `linear-gradient(to right, #ef4444 0%, #eab308 50%, #22c55e 100%)` 
              }}
            />
          </div>

          <div>
            <div className="flex justify-between text-sm font-medium text-gray-800 dark:text-gray-200 mb-1">
              <span>Arousal (Energy)</span>
              <span>{arousalPercentage}%</span>
            </div>
            <Progress 
              value={arousalPercentage} 
              className="h-2"
              style={{ 
                background: `linear-gradient(to right, #64748b 0%, #f59e0b 50%, #dc2626 100%)` 
              }}
            />
          </div>

          <div>
            <div className="flex justify-between text-sm font-medium text-gray-800 dark:text-gray-200 mb-1">
              <span>Resonance Intensity</span>
              <span>{intensityPercentage}%</span>
            </div>
            <Progress 
              value={intensityPercentage} 
              className="h-2"
              style={{ backgroundColor: emotionalState.color + '40' }}
            />
          </div>
        </div>
        </div>

        {/* Emotional Tags */}
        <div>
          <span className="text-sm font-medium mb-2 block">Emotional Qualities</span>
          <div className="flex flex-wrap gap-1">
            {emotionalState.emotionalTags.map((tag, index) => (
              <Badge 
                key={index} 
                variant="secondary" 
                className="text-xs text-foreground"
                style={{ 
                  backgroundColor: emotionalState.color + '20',
                  borderColor: emotionalState.color
                }}
              >
                {tag}
              </Badge>
             ))}
          </div>
        </div>

        {/* Description */}
        <div className="pt-2 border-t">
          <p className="text-sm text-muted-foreground italic">
            {emotionalState.description}
          </p>
        </div>
      </CardContent>
    </Card>
  );
};