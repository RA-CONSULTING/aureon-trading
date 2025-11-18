import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { type IntegralFieldState, AQAL_QUADRANTS } from '@/core/integralAQAL';
import integralImage from '@/assets/research/integral-aqal-quadrants.jpg';

interface IntegralAQALVisualizationProps {
  fieldState: IntegralFieldState | null;
}

export function IntegralAQALVisualization({ fieldState }: IntegralAQALVisualizationProps) {
  if (!fieldState) {
    return (
      <Card className="p-6 bg-card border-border">
        <h3 className="text-xl font-semibold text-foreground mb-4">
          🌐 Integral AQAL Framework
        </h3>
        <p className="text-sm text-muted-foreground">
          Awaiting field state initialization...
        </p>
      </Card>
    );
  }

  const getQuadrantColor = (quadrant: string) => {
    switch (quadrant) {
      case 'UL': return '#9b87f5'; // Purple - Individual Interior
      case 'UR': return '#0EA5E9'; // Blue - Individual Exterior
      case 'LL': return '#f97316'; // Orange - Collective Interior
      case 'LR': return '#10b981'; // Green - Collective Exterior
      default: return '#6b7280';
    }
  };

  const formatEvolutionaryLevel = (level: number) => {
    if (level >= 0.9) return 'INTEGRAL+';
    if (level >= 0.8) return 'INTEGRAL';
    if (level >= 0.7) return 'PLURALISTIC';
    if (level >= 0.6) return 'RATIONAL';
    if (level >= 0.5) return 'MYTHIC';
    if (level >= 0.4) return 'MAGIC';
    if (level >= 0.3) return 'ARCHAIC';
    return 'PRIMORDIAL';
  };

  return (
    <Card className="p-6 bg-card border-border">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl font-semibold text-foreground mb-2">
              🌐 Integral AQAL Framework
            </h3>
            <p className="text-sm text-muted-foreground">
              All Quadrants, All Levels - Consciousness Evolution Mapping
            </p>
          </div>
          <Badge 
            className="text-sm px-3 py-1"
            style={{ backgroundColor: getQuadrantColor(fieldState.dominantQuadrant) }}
          >
            {formatEvolutionaryLevel(fieldState.overallEvolutionaryLevel)}
          </Badge>
        </div>

        {/* Overall Metrics */}
        <div className="grid grid-cols-2 gap-4 p-4 bg-black/10 rounded-lg border border-border">
          <div>
            <p className="text-xs text-muted-foreground mb-1">Evolutionary Level</p>
            <div className="flex items-center gap-2">
              <Progress value={fieldState.overallEvolutionaryLevel * 100} className="flex-1" />
              <span className="text-sm font-mono text-foreground">
                {(fieldState.overallEvolutionaryLevel * 100).toFixed(1)}%
              </span>
            </div>
          </div>
          <div>
            <p className="text-xs text-muted-foreground mb-1">Integration Score</p>
            <div className="flex items-center gap-2">
              <Progress value={fieldState.integrationScore * 100} className="flex-1" />
              <span className="text-sm font-mono text-foreground">
                {(fieldState.integrationScore * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        </div>

        {/* Reference Image */}
        <div className="border border-border rounded-lg overflow-hidden">
          <img 
            src={integralImage} 
            alt="Integral AQAL Quadrants" 
            className="w-full h-auto"
          />
        </div>

        {/* Quadrant Details */}
        <div className="grid grid-cols-2 gap-4">
          {/* Upper Left */}
          <Card className="p-4 bg-black/10 border-border">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div 
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: getQuadrantColor('UL') }}
                />
                <h4 className="text-sm font-semibold text-foreground">
                  {AQAL_QUADRANTS[0].name}
                </h4>
              </div>
              <Badge variant="outline" className="text-xs">
                {fieldState.upperLeft.stage.level}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mb-2">
              {AQAL_QUADRANTS[0].description}
            </p>
            <div className="space-y-1">
              <p className="text-sm font-medium text-foreground">
                {fieldState.upperLeft.stage.label}
              </p>
              <p className="text-xs text-muted-foreground">
                {fieldState.upperLeft.stage.description}
              </p>
              <div className="flex items-center justify-between mt-2">
                <span className="text-xs text-muted-foreground">Position:</span>
                <span className="text-xs font-mono text-primary">
                  {(fieldState.upperLeft.evolutionaryPosition * 100).toFixed(0)}%
                </span>
              </div>
              {fieldState.upperLeft.stage.chakra && (
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">Chakra:</span>
                  <span className="text-xs font-mono text-primary">
                    {fieldState.upperLeft.stage.chakra}
                  </span>
                </div>
              )}
            </div>
          </Card>

          {/* Upper Right */}
          <Card className="p-4 bg-black/10 border-border">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div 
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: getQuadrantColor('UR') }}
                />
                <h4 className="text-sm font-semibold text-foreground">
                  {AQAL_QUADRANTS[1].name}
                </h4>
              </div>
              <Badge variant="outline" className="text-xs">
                {fieldState.upperRight.stage.level}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mb-2">
              {AQAL_QUADRANTS[1].description}
            </p>
            <div className="space-y-1">
              <p className="text-sm font-medium text-foreground">
                {fieldState.upperRight.stage.label}
              </p>
              <p className="text-xs text-muted-foreground">
                {fieldState.upperRight.stage.description}
              </p>
              <div className="flex items-center justify-between mt-2">
                <span className="text-xs text-muted-foreground">Position:</span>
                <span className="text-xs font-mono text-primary">
                  {(fieldState.upperRight.evolutionaryPosition * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </Card>

          {/* Lower Left */}
          <Card className="p-4 bg-black/10 border-border">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div 
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: getQuadrantColor('LL') }}
                />
                <h4 className="text-sm font-semibold text-foreground">
                  {AQAL_QUADRANTS[2].name}
                </h4>
              </div>
              <Badge variant="outline" className="text-xs">
                {fieldState.lowerLeft.stage.level}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mb-2">
              {AQAL_QUADRANTS[2].description}
            </p>
            <div className="space-y-1">
              <p className="text-sm font-medium text-foreground">
                {fieldState.lowerLeft.stage.label}
              </p>
              <p className="text-xs text-muted-foreground">
                {fieldState.lowerLeft.stage.description}
              </p>
              <div className="flex items-center justify-between mt-2">
                <span className="text-xs text-muted-foreground">Position:</span>
                <span className="text-xs font-mono text-primary">
                  {(fieldState.lowerLeft.evolutionaryPosition * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </Card>

          {/* Lower Right */}
          <Card className="p-4 bg-black/10 border-border">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div 
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: getQuadrantColor('LR') }}
                />
                <h4 className="text-sm font-semibold text-foreground">
                  {AQAL_QUADRANTS[3].name}
                </h4>
              </div>
              <Badge variant="outline" className="text-xs">
                {fieldState.lowerRight.stage.level}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mb-2">
              {AQAL_QUADRANTS[3].description}
            </p>
            <div className="space-y-1">
              <p className="text-sm font-medium text-foreground">
                {fieldState.lowerRight.stage.label}
              </p>
              <p className="text-xs text-muted-foreground">
                {fieldState.lowerRight.stage.description}
              </p>
              <div className="flex items-center justify-between mt-2">
                <span className="text-xs text-muted-foreground">Position:</span>
                <span className="text-xs font-mono text-primary">
                  {(fieldState.lowerRight.evolutionaryPosition * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </Card>
        </div>

        {/* Integration Notes */}
        <div className="border-t border-border pt-4">
          <h4 className="text-sm font-semibold text-foreground mb-2">
            🔮 Field Integration Analysis
          </h4>
          <div className="space-y-2 text-xs text-muted-foreground">
            <p>
              <strong>Dominant Quadrant:</strong> {fieldState.dominantQuadrant} - 
              {fieldState.dominantQuadrant === 'UL' && ' Individual consciousness leading evolution'}
              {fieldState.dominantQuadrant === 'UR' && ' Material manifestation at peak'}
              {fieldState.dominantQuadrant === 'LL' && ' Collective consciousness awakening'}
              {fieldState.dominantQuadrant === 'LR' && ' External systems highly evolved'}
            </p>
            <p>
              <strong>Integration Status:</strong> {
                fieldState.integrationScore > 0.8 ? 'Highly Integrated - All quadrants evolving in harmony' :
                fieldState.integrationScore > 0.6 ? 'Moderately Integrated - Some imbalance across quadrants' :
                fieldState.integrationScore > 0.4 ? 'Fragmented - Significant developmental gaps' :
                'Severely Imbalanced - Focus required on underdeveloped quadrants'
              }
            </p>
            <p>
              <strong>Evolutionary Trajectory:</strong> Current field state indicates {formatEvolutionaryLevel(fieldState.overallEvolutionaryLevel)} consciousness level across all dimensions.
            </p>
          </div>
        </div>
      </div>
    </Card>
  );
}
