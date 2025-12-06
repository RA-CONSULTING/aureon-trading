import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Telescope, Triangle, Square, Hexagon, Circle, Star, ArrowUp, ArrowDown, Minus } from 'lucide-react';
import { GeometricSolid, type TelescopeObservation } from '@/core/quantumTelescope';

interface QuantumTelescopePanelProps {
  observation: TelescopeObservation | null;
  prismFrequency?: number;
  prismState?: string;
}

const solidConfig: Record<GeometricSolid, { icon: React.ReactNode; color: string; element: string }> = {
  [GeometricSolid.Tetrahedron]: { icon: <Triangle className="h-4 w-4" />, color: 'text-red-500', element: 'Fire' },
  [GeometricSolid.Hexahedron]: { icon: <Square className="h-4 w-4" />, color: 'text-amber-600', element: 'Earth' },
  [GeometricSolid.Octahedron]: { icon: <Hexagon className="h-4 w-4" />, color: 'text-sky-400', element: 'Air' },
  [GeometricSolid.Icosahedron]: { icon: <Circle className="h-4 w-4" />, color: 'text-blue-500', element: 'Water' },
  [GeometricSolid.Dodecahedron]: { icon: <Star className="h-4 w-4" />, color: 'text-purple-500', element: 'Ether' },
};

const solidOrder = [
  GeometricSolid.Tetrahedron,
  GeometricSolid.Hexahedron,
  GeometricSolid.Octahedron,
  GeometricSolid.Icosahedron,
  GeometricSolid.Dodecahedron,
];

export function QuantumTelescopePanel({ observation, prismFrequency, prismState }: QuantumTelescopePanelProps) {
  if (!observation) {
    return (
      <Card className="bg-card/50 backdrop-blur border-border/50">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-sm">
            <Telescope className="h-4 w-4 text-purple-400" />
            Quantum Telescope
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center text-muted-foreground text-sm py-4">
            Awaiting market observation...
          </div>
        </CardContent>
      </Card>
    );
  }

  const { geometricAlignment, dominantSolid, probabilitySpectrum, holographicProjection, focalCoherence, prismBoostFactor } = observation;

  const alignmentColor = geometricAlignment > 0.7 ? 'text-green-400' : geometricAlignment > 0.4 ? 'text-yellow-400' : 'text-red-400';
  const directionIcon = holographicProjection.direction === 'UP' 
    ? <ArrowUp className="h-4 w-4 text-green-400" />
    : holographicProjection.direction === 'DOWN'
    ? <ArrowDown className="h-4 w-4 text-red-400" />
    : <Minus className="h-4 w-4 text-muted-foreground" />;

  return (
    <Card className="bg-card/50 backdrop-blur border-border/50">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <Telescope className="h-4 w-4 text-purple-400" />
            Quantum Telescope
          </div>
          <Badge variant="outline" className={alignmentColor}>
            {(geometricAlignment * 100).toFixed(1)}% Aligned
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* 5 Platonic Solid Resonances */}
        <div className="space-y-2">
          <div className="text-xs text-muted-foreground mb-1">Platonic Solid Resonances</div>
          {solidOrder.map((solid, index) => {
            const config = solidConfig[solid];
            const resonance = probabilitySpectrum[index] ?? 0;
            const isDominant = solid === dominantSolid;
            
            return (
              <div key={solid} className={`flex items-center gap-2 ${isDominant ? 'bg-accent/20 rounded px-1 -mx-1' : ''}`}>
                <div className={`flex items-center gap-1 w-24 ${config.color}`}>
                  {config.icon}
                  <span className="text-xs">{config.element}</span>
                  {isDominant && <span className="text-[10px] text-primary">★</span>}
                </div>
                <Progress value={resonance * 100} className="h-2 flex-1" />
                <span className="text-xs w-12 text-right font-mono">{(resonance * 100).toFixed(0)}%</span>
              </div>
            );
          })}
        </div>

        {/* Holographic Projection */}
        <div className="flex items-center justify-between border-t border-border/50 pt-3">
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">Holographic Projection</div>
            <div className="flex items-center gap-2">
              {directionIcon}
              <span className="font-medium">{holographicProjection.direction}</span>
              <span className="text-xs text-muted-foreground">
                ({(holographicProjection.confidence * 100).toFixed(0)}% conf)
              </span>
            </div>
          </div>
          <div className="text-right space-y-1">
            <div className="text-xs text-muted-foreground">Focal Coherence</div>
            <span className="font-mono text-lg">{(focalCoherence * 100).toFixed(1)}%</span>
          </div>
        </div>

        {/* Prism Integration */}
        <div className="flex items-center justify-between border-t border-border/50 pt-3">
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">Prism Boost</div>
            <span className={`font-mono text-sm ${prismBoostFactor > 1 ? 'text-green-400' : prismBoostFactor < 1 ? 'text-red-400' : ''}`}>
              ×{prismBoostFactor.toFixed(3)}
            </span>
          </div>
          {prismFrequency !== undefined && (
            <div className="text-right space-y-1">
              <div className="text-xs text-muted-foreground">Prism Frequency</div>
              <span className={`font-mono text-sm ${prismFrequency === 528 ? 'text-green-400' : ''}`}>
                {prismFrequency} Hz {prismState && <span className="text-xs">({prismState})</span>}
              </span>
            </div>
          )}
        </div>

        {/* Dominant Solid Badge */}
        <div className="flex justify-center pt-2">
          <Badge 
            variant="secondary" 
            className={`${solidConfig[dominantSolid].color} flex items-center gap-1`}
          >
            {solidConfig[dominantSolid].icon}
            {dominantSolid} ({solidConfig[dominantSolid].element}) Dominant
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}
