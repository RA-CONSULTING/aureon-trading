import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import type { LambdaState } from "@/core/masterEquation";
import type { RainbowState } from "@/core/rainbowBridge";
import type { PrismOutput } from "@/core/prism";

type AureonFieldProps = {
  lambda: LambdaState | null;
  rainbow: RainbowState | null;
  prism: PrismOutput | null;
};

export const AureonField = ({ lambda, rainbow, prism }: AureonFieldProps) => {
  if (!lambda || !rainbow || !prism) {
    return (
      <Card className="p-6">
        <p className="text-muted-foreground">Initializing field...</p>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Master Equation */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Master Equation Λ(t)</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-muted-foreground">Lambda</p>
            <p className="text-2xl font-bold">{lambda.lambda.toFixed(3)}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Coherence Γ</p>
            <Progress value={lambda.coherence * 100} className="mt-2" />
            <p className="text-sm mt-1">{(lambda.coherence * 100).toFixed(1)}%</p>
          </div>
        </div>
        
        <div className="mt-4 grid grid-cols-3 gap-4">
          <div>
            <p className="text-xs text-muted-foreground">Substrate S(t)</p>
            <p className="font-mono">{lambda.substrate.toFixed(2)}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Observer O(t)</p>
            <p className="font-mono">{lambda.observer.toFixed(2)}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Echo E(t)</p>
            <p className="font-mono">{lambda.echo.toFixed(2)}</p>
          </div>
        </div>

        <div className="mt-4">
          <p className="text-sm text-muted-foreground">Dominant Node</p>
          <Badge className="mt-1">{lambda.dominantNode}</Badge>
        </div>
        
        {lambda.stargateInfluence && (
          <div className="mt-4 p-3 rounded-lg bg-primary/5 border border-primary/20">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="text-xl">🌍</span>
                <p className="text-sm font-semibold">Stargate Lattice Active</p>
              </div>
              <Badge variant="default">
                +{(lambda.stargateInfluence.coherenceModifier * 100).toFixed(1)}% Γ
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mb-1">
              Nearest: {lambda.stargateInfluence.nearestNode} ({lambda.stargateInfluence.distance}km)
            </p>
            {lambda.stargateInfluence.celestialBoost !== undefined && lambda.stargateInfluence.celestialBoost > 0 && (
              <div className="mt-2 flex items-center gap-2 text-xs text-purple-400">
                <span>✨</span>
                <span>Celestial amplification active: +{(lambda.stargateInfluence.celestialBoost * 100).toFixed(1)}%</span>
              </div>
            )}
          </div>
        )}
      </Card>

      {/* Rainbow Bridge */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Rainbow Bridge</h3>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">Frequency</p>
            <p className="text-2xl font-bold">{rainbow.frequency} Hz</p>
          </div>
          <Badge 
            className="text-lg px-4 py-2"
            style={{ backgroundColor: getPhaseColor(rainbow.phase) }}
          >
            {rainbow.phase}
          </Badge>
        </div>
        <Progress value={rainbow.intensity * 100} className="mt-4" />
      </Card>

      {/* The Prism */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">The Prism 💎</h3>
        <div className="flex items-center justify-between mb-4">
          <div>
            <p className="text-sm text-muted-foreground">Level {prism.level}/5</p>
            <p className="text-xl font-bold">{prism.frequency} Hz</p>
          </div>
          <Badge 
            className="text-lg px-4 py-2"
            style={{ backgroundColor: getStateColor(prism.state) }}
          >
            {prism.state}
          </Badge>
        </div>
        <Progress value={prism.transformation * 100} />
        <p className="text-xs text-muted-foreground mt-2">
          {prism.state === 'MANIFEST' && '💚 LOVE MANIFEST (528 Hz)'}
          {prism.state === 'CONVERGING' && '🔄 Converging to Love'}
          {prism.state === 'FORMING' && '🌱 Forming from Fear'}
        </p>
      </Card>

      {/* Node Responses */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">9 Auris Nodes</h3>
        <div className="grid grid-cols-3 gap-3">
          {Object.entries(lambda.nodeResponses).map(([name, value]) => (
            <div key={name} className="text-center">
              <p className="text-xs font-medium">{name}</p>
              <p className="text-sm font-mono">{value.toFixed(2)}</p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};

function getPhaseColor(phase: string): string {
  const colors: Record<string, string> = {
    FEAR: '#8B0000',
    FORMING: '#FF6B35',
    LOVE: '#00FF88',
    AWE: '#4169E1',
    UNITY: '#9370DB',
  };
  return colors[phase] || '#888';
}

function getStateColor(state: string): string {
  return {
    FORMING: '#FF6B35',
    CONVERGING: '#FFD700',
    MANIFEST: '#00FF88',
  }[state] || '#888';
}
