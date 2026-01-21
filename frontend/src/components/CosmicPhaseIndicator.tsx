import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { CosmicPhase, type CosmicState, COSMIC_CALENDAR } from "@/core/imperialPredictability";

interface CosmicPhaseIndicatorProps {
  cosmicState: CosmicState | null;
}

const phaseConfig: Record<CosmicPhase, { emoji: string; color: string; bgColor: string; description: string }> = {
  [CosmicPhase.UNITY]: { 
    emoji: '🌈', 
    color: 'text-violet-400', 
    bgColor: 'bg-violet-500/20 border-violet-500/30',
    description: 'Perfect cosmic sync - maximum position size'
  },
  [CosmicPhase.COHERENCE]: { 
    emoji: '🔵', 
    color: 'text-blue-400', 
    bgColor: 'bg-blue-500/20 border-blue-500/30',
    description: 'Strong alignment - increase position'
  },
  [CosmicPhase.HARMONIC]: { 
    emoji: '🟢', 
    color: 'text-emerald-400', 
    bgColor: 'bg-emerald-500/20 border-emerald-500/30',
    description: 'Good alignment - normal trading'
  },
  [CosmicPhase.TRANSITION]: { 
    emoji: '🟡', 
    color: 'text-yellow-400', 
    bgColor: 'bg-yellow-500/20 border-yellow-500/30',
    description: 'Mixed signals - reduce position'
  },
  [CosmicPhase.DISTORTION]: { 
    emoji: '🔴', 
    color: 'text-red-400', 
    bgColor: 'bg-red-500/20 border-red-500/30',
    description: '440 Hz dominance - avoid trading'
  },
};

const getNextCosmicEvent = (): { date: string; phase: CosmicPhase; description: string } | null => {
  const today = new Date().toISOString().split('T')[0];
  const futureEvents = Object.entries(COSMIC_CALENDAR)
    .filter(([date]) => date > today)
    .sort(([a], [b]) => a.localeCompare(b));
  
  if (futureEvents.length === 0) return null;
  const [date, { phase, description }] = futureEvents[0];
  return { date, phase, description };
};

export function CosmicPhaseIndicator({ cosmicState }: CosmicPhaseIndicatorProps) {
  if (!cosmicState) {
    return (
      <Card className="bg-card border-border">
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center gap-2">
            <span>🌌</span>
            Imperial Cosmic State
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center text-muted-foreground py-8">
            Computing cosmic alignment...
          </div>
        </CardContent>
      </Card>
    );
  }

  const config = phaseConfig[cosmicState.phase];
  const nextEvent = getNextCosmicEvent();

  return (
    <Card className="bg-card border-border">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span>🌌</span>
            Imperial Cosmic State
          </div>
          <Badge className={`${config.bgColor} ${config.color} border`}>
            {config.emoji} {cosmicState.phase}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Phase Description */}
        <div className={`p-4 rounded-lg ${config.bgColor} border`}>
          <div className="flex items-center gap-3 mb-2">
            <span className="text-3xl">{config.emoji}</span>
            <div>
              <div className={`font-semibold ${config.color}`}>{cosmicState.phase}</div>
              <div className="text-sm text-muted-foreground">{config.description}</div>
            </div>
          </div>
          <div className="text-xs text-muted-foreground mt-2">
            {cosmicState.description}
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 gap-4">
          {/* Torque Multiplier */}
          <div className="p-3 rounded-lg bg-muted/50 border border-border">
            <div className="text-xs text-muted-foreground mb-1">Planetary Torque</div>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold">{cosmicState.torqueMultiplier.toFixed(2)}x</span>
              {cosmicState.torqueMultiplier >= 1.5 && <span className="text-xs text-emerald-400">⚡ High</span>}
            </div>
          </div>

          {/* Position Multiplier */}
          <div className="p-3 rounded-lg bg-muted/50 border border-border">
            <div className="text-xs text-muted-foreground mb-1">Position Modifier</div>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold">{cosmicState.positionMultiplier.toFixed(2)}x</span>
            </div>
          </div>

          {/* Lunar Phase */}
          <div className="p-3 rounded-lg bg-muted/50 border border-border">
            <div className="text-xs text-muted-foreground mb-1">Lunar Phase</div>
            <div className="text-sm font-medium">{cosmicState.lunarPhase.replace(/_/g, ' ')}</div>
            <Progress value={cosmicState.lunarInfluence * 100} className="h-1 mt-1" />
            <div className="text-xs text-muted-foreground mt-1">
              {(cosmicState.lunarInfluence * 100).toFixed(0)}% influence
            </div>
          </div>

          {/* Imperial Yield */}
          <div className="p-3 rounded-lg bg-muted/50 border border-border">
            <div className="text-xs text-muted-foreground mb-1">Imperial Yield</div>
            <div className="text-lg font-mono">{cosmicState.imperialYield.toFixed(4)}</div>
            <div className="text-xs text-muted-foreground">
              E = J³×C²×R×T² / D
            </div>
          </div>
        </div>

        {/* Alignment Metrics */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Planetary Alignment</span>
            <span className="font-mono">{(cosmicState.planetaryAlignment * 100).toFixed(1)}%</span>
          </div>
          <Progress value={cosmicState.planetaryAlignment * 100} className="h-2" />

          <div className="flex justify-between text-sm mt-2">
            <span className="text-muted-foreground">Frequency Ratio (528/440)</span>
            <span className="font-mono">{cosmicState.frequencyRatio.toFixed(3)}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Schumann Resonance</span>
            <span className="font-mono">{cosmicState.schumannResonance.toFixed(2)} Hz</span>
          </div>
        </div>

        {/* Trading Decision */}
        <div className={`p-3 rounded-lg border ${cosmicState.shouldTrade ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-red-500/10 border-red-500/30'}`}>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Trading Allowed</span>
            <Badge variant={cosmicState.shouldTrade ? "default" : "destructive"}>
              {cosmicState.shouldTrade ? '✅ YES' : '❌ NO'}
            </Badge>
          </div>
        </div>

        {/* Next Cosmic Event */}
        {nextEvent && (
          <div className="p-3 rounded-lg bg-muted/30 border border-border">
            <div className="text-xs text-muted-foreground mb-1">Next Cosmic Event</div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span>{phaseConfig[nextEvent.phase].emoji}</span>
                <span className="text-sm font-medium">{nextEvent.description}</span>
              </div>
              <span className="text-xs text-muted-foreground">{nextEvent.date}</span>
            </div>
          </div>
        )}

        {/* Timestamp */}
        <div className="text-xs text-muted-foreground text-right">
          Updated: {new Date(cosmicState.timestamp).toLocaleTimeString()}
        </div>
      </CardContent>
    </Card>
  );
}
