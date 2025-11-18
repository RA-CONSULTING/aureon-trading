import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Waves, Sparkles, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { AkashicAttunement } from "@/core/akashicFrequencyMapper";

interface AkashicFrequencyVisualizationProps {
  attunement: AkashicAttunement | null;
  onReattuned?: () => void;
  akashicBoost: number;
}

export function AkashicFrequencyVisualization({ 
  attunement, 
  onReattuned,
  akashicBoost 
}: AkashicFrequencyVisualizationProps) {
  if (!attunement) {
    return (
      <Card className="bg-card/50 backdrop-blur border-border/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Waves className="w-5 h-5 text-cyan-500" />
            Akashic Frequency Mapper
          </CardTitle>
          <CardDescription>Attuning to foundational layer of reality...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="w-8 h-8 text-muted-foreground animate-spin" />
          </div>
        </CardContent>
      </Card>
    );
  }

  const getQualityStatus = (stability: number) => {
    if (stability > 0.8) return { level: 'HIGH', color: 'text-green-500', bg: 'bg-green-500/20' };
    if (stability > 0.5) return { level: 'MODERATE', color: 'text-yellow-500', bg: 'bg-yellow-500/20' };
    return { level: 'LOW', color: 'text-orange-500', bg: 'bg-orange-500/20' };
  };

  const quality = getQualityStatus(attunement.stabilityIndex);
  const numCycles = attunement.cycles.length - 1;

  return (
    <Card className="bg-card/50 backdrop-blur border-border/50 relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 via-blue-500/5 to-indigo-500/5" />
      
      <CardHeader className="relative">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Waves className="w-5 h-5 text-cyan-500" />
              Akashic Frequency Mapper
            </CardTitle>
            <CardDescription>
              Unity-Point Reflection • 10-9-1 Synthesis
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Badge className={`${quality.color} ${quality.bg} border-0`}>
              {quality.level} QUALITY
            </Badge>
            {onReattuned && (
              <Button
                variant="outline"
                size="sm"
                onClick={onReattuned}
                className="gap-2"
              >
                <RefreshCw className="w-3 h-3" />
                Reattune
              </Button>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="relative space-y-4">
        {/* Final Frequency Display */}
        <div className="flex items-center justify-center p-6 bg-gradient-to-br from-cyan-500/10 to-indigo-500/10 rounded-lg border border-border/50">
          <div className="text-center">
            <div className="flex items-center justify-center gap-2 mb-2">
              <Sparkles className="w-6 h-6 text-cyan-500" />
              <span className="text-sm text-muted-foreground font-medium">Attuned Akashic Frequency</span>
            </div>
            <div className="text-5xl font-bold bg-gradient-to-r from-cyan-400 via-blue-400 to-indigo-400 bg-clip-text text-transparent">
              {attunement.finalFrequency.toFixed(4)} Hz
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              {numCycles} reflection cycles • Point of Intent: 9.0
            </div>
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-3 gap-4">
          {/* Convergence Rate */}
          <div className="p-4 bg-background/50 rounded-lg border border-border/50">
            <div className="text-xs text-muted-foreground mb-2">Convergence Rate</div>
            <div className="text-2xl font-bold text-cyan-500 mb-2">
              {(attunement.convergenceRate * 100).toFixed(1)}%
            </div>
            <Progress value={attunement.convergenceRate * 100} className="h-2" />
          </div>

          {/* Stability Index */}
          <div className="p-4 bg-background/50 rounded-lg border border-border/50">
            <div className="text-xs text-muted-foreground mb-2">Stability Index</div>
            <div className="text-2xl font-bold text-blue-500 mb-2">
              {attunement.stabilityIndex.toFixed(3)}
            </div>
            <Progress value={attunement.stabilityIndex * 100} className="h-2" />
          </div>

          {/* Akashic Boost */}
          <div className="p-4 bg-background/50 rounded-lg border border-border/50">
            <div className="text-xs text-muted-foreground mb-2">Field Boost</div>
            <div className="text-2xl font-bold text-indigo-500 mb-2">
              {(akashicBoost * 100).toFixed(1)}%
            </div>
            <Progress value={akashicBoost * 100} className="h-2" />
          </div>
        </div>

        {/* Reflection Cycles */}
        <div className="p-4 bg-background/50 rounded-lg border border-border/50">
          <div className="text-sm font-medium mb-3 flex items-center gap-2">
            <RefreshCw className="w-4 h-4 text-cyan-500" />
            Meditative Reflection Cycles
          </div>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {attunement.cycles.map((cycle) => (
              <div
                key={cycle.cycle}
                className={`text-xs p-2 rounded ${
                  cycle.cycle === 0 
                    ? 'bg-muted/50 text-muted-foreground' 
                    : cycle.cycle === numCycles
                    ? 'bg-cyan-500/10 border border-cyan-500/30 text-cyan-500'
                    : 'bg-background/50 text-foreground'
                }`}
              >
                <div className="font-mono">
                  {cycle.cycle === 0 ? '⚡ BASE' : `🔄 C${cycle.cycle}`}: {cycle.frequency.toFixed(4)} Hz
                </div>
                {cycle.cycle === numCycles && (
                  <div className="text-xs text-cyan-400 mt-1">✨ Final Attunement</div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Theory */}
        <div className="p-4 bg-gradient-to-r from-cyan-500/10 to-indigo-500/10 rounded-lg border border-border/50">
          <p className="text-sm text-muted-foreground">
            <span className="font-medium text-foreground">Ping-Pong Reflection:</span>{' '}
            Each cycle reflects the current frequency against the Point of Intent (9.0), creating a meditative
            attunement to the Akashic Records. The process mirrors consciousness itself: oscillating, converging,
            and stabilizing through repeated reflection.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
