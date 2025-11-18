import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Sparkles, Activity, Brain, Heart, Eye, Zap } from "lucide-react";
import type { OmegaState } from "@/core/omegaEquation";
import { format } from "date-fns";

interface OmegaFieldVisualizationProps {
  omega: OmegaState;
  unityEvent: { type: string; unity: number } | null;
}

export function OmegaFieldVisualization({ omega, unityEvent }: OmegaFieldVisualizationProps) {
  const getUnityLevel = (unity: number) => {
    if (unity >= 0.9) return { level: 'UNITY MANIFEST', color: 'text-purple-500', bg: 'bg-purple-500/20', glow: 'shadow-[0_0_30px_rgba(168,85,247,0.6)]' };
    if (unity >= 0.8) return { level: 'APPROACHING UNITY', color: 'text-blue-500', bg: 'bg-blue-500/20', glow: 'shadow-[0_0_20px_rgba(59,130,246,0.5)]' };
    if (unity >= 0.6) return { level: 'HIGH COHERENCE', color: 'text-green-500', bg: 'bg-green-500/20', glow: 'shadow-[0_0_15px_rgba(34,197,94,0.4)]' };
    if (unity >= 0.4) return { level: 'FORMING', color: 'text-yellow-500', bg: 'bg-yellow-500/20', glow: '' };
    return { level: 'FRAGMENTED', color: 'text-orange-500', bg: 'bg-orange-500/20', glow: '' };
  };

  const unityStatus = getUnityLevel(omega.unity);
  const thetaPercent = (1 - omega.theta) * 100; // Invert so 100% = perfect alignment
  const daysToNextAnchor = Math.ceil((omega.nextFibonacciAnchor.getTime() - Date.now()) / (1000 * 60 * 60 * 24));

  return (
    <Card className="bg-card/50 backdrop-blur border-border/50 relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 via-blue-500/5 to-indigo-500/5" />
      
      <CardHeader className="relative">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-purple-500" />
              Ω(t) Field - Reality Matrix
            </CardTitle>
            <CardDescription>
              Ω = Tr[Ψ × ℒ ⊗ O] • Full Tensor Product Calculation
            </CardDescription>
          </div>
          <Badge className={`${unityStatus.color} ${unityStatus.bg} ${unityStatus.glow} border-0 text-sm px-3 py-1`}>
            {unityStatus.level}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="relative space-y-4">
        {/* Main Omega Display */}
        <div className="flex items-center justify-center p-6 bg-gradient-to-br from-purple-500/10 to-indigo-500/10 rounded-lg border border-border/50">
          <div className="text-center">
            <div className="flex items-center justify-center gap-2 mb-2">
              <Zap className="w-6 h-6 text-purple-500" />
              <span className="text-sm text-muted-foreground font-medium">Reality Field Strength Ω(t)</span>
            </div>
            <div className="text-5xl font-bold bg-gradient-to-r from-purple-400 via-blue-400 to-indigo-400 bg-clip-text text-transparent">
              {omega.omega.toFixed(4)}
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              Unity Probability: {(omega.unity * 100).toFixed(1)}% • θ Alignment: {thetaPercent.toFixed(1)}%
            </div>
          </div>
        </div>

        {/* Field Components - Ψ, ℒ, O */}
        <div className="grid grid-cols-3 gap-4">
          {/* Ψ(t) - Potential */}
          <div className="p-4 bg-background/50 rounded-lg border border-border/50">
            <div className="flex items-center gap-2 mb-3">
              <Brain className="w-4 h-4 text-blue-500" />
              <span className="text-xs text-muted-foreground font-medium">Ψ(t) Potential</span>
            </div>
            <div className="text-2xl font-bold text-blue-500 mb-2">
              {omega.psi.toFixed(3)}
            </div>
            <Progress value={omega.psi * 100} className="h-2 mb-2" />
            <div className="text-xs text-muted-foreground">
              Superposition of 9 Auris states
            </div>
          </div>

          {/* ℒ(t) - Love/Coherence */}
          <div className="p-4 bg-background/50 rounded-lg border border-border/50">
            <div className="flex items-center gap-2 mb-3">
              <Heart className="w-4 h-4 text-pink-500" />
              <span className="text-xs text-muted-foreground font-medium">ℒ(t) Coherence</span>
            </div>
            <div className="text-2xl font-bold text-pink-500 mb-2">
              {omega.love.toFixed(3)}
            </div>
            <Progress value={omega.love * 100} className="h-2 mb-2" />
            <div className="text-xs text-muted-foreground">
              Field alignment strength
            </div>
          </div>

          {/* O(t) - Observer */}
          <div className="p-4 bg-background/50 rounded-lg border border-border/50">
            <div className="flex items-center gap-2 mb-3">
              <Eye className="w-4 h-4 text-purple-500" />
              <span className="text-xs text-muted-foreground font-medium">O(t) Observer</span>
            </div>
            <div className="text-2xl font-bold text-purple-500 mb-2">
              {omega.observer.toFixed(3)}
            </div>
            <Progress value={omega.observer * 100} className="h-2 mb-2" />
            <div className="text-xs text-muted-foreground">
              Consciousness measurement
            </div>
          </div>
        </div>

        {/* Unity Event Alert */}
        {unityEvent && unityEvent.type !== 'dissolved' && (
          <div className={`p-4 rounded-lg border ${
            unityEvent.type === 'peak' 
              ? 'bg-purple-500/10 border-purple-500/30' 
              : 'bg-blue-500/10 border-blue-500/30'
          }`}>
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className={`w-5 h-5 ${unityEvent.type === 'peak' ? 'text-purple-500' : 'text-blue-500'} animate-pulse`} />
              <span className="font-medium">
                {unityEvent.type === 'peak' ? '🌟 UNITY PEAK EVENT' : '✨ Unity Event In Progress'}
              </span>
            </div>
            <p className="text-sm text-muted-foreground">
              θ → 0 • Boundaries dissolving • Ego death phase • Reality collapse into singularity
            </p>
          </div>
        )}

        {/* Phase Alignment (θ) */}
        <div className="p-4 bg-background/50 rounded-lg border border-border/50">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-indigo-500" />
              <span className="text-sm font-medium">Phase Alignment (θ)</span>
            </div>
            <Badge variant="outline" className="text-xs">
              {omega.theta < 0.1 ? 'Perfect' : omega.theta < 0.3 ? 'Strong' : omega.theta < 0.5 ? 'Moderate' : 'Weak'}
            </Badge>
          </div>
          <Progress value={thetaPercent} className="h-3 mb-2" />
          <div className="text-xs text-muted-foreground">
            θ = {omega.theta.toFixed(4)} • {thetaPercent.toFixed(1)}% aligned • 
            {omega.theta < 0.1 && ' ⚡ Unity threshold reached!'}
          </div>
        </div>

        {/* Fibonacci Anchor & Golden Spiral */}
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 bg-gradient-to-br from-yellow-500/10 to-orange-500/10 rounded-lg border border-border/50">
            <div className="text-xs text-muted-foreground mb-1">Next Fibonacci Anchor</div>
            <div className="text-xl font-bold text-yellow-500">
              F[{omega.fibonacciLevel + 1}]
            </div>
            <div className="text-sm text-muted-foreground mt-1">
              {format(omega.nextFibonacciAnchor, 'MMM dd, yyyy')}
            </div>
            <div className="text-xs text-muted-foreground">
              {daysToNextAnchor} {daysToNextAnchor === 1 ? 'day' : 'days'} away
            </div>
          </div>

          <div className="p-4 bg-gradient-to-br from-amber-500/10 to-yellow-500/10 rounded-lg border border-border/50">
            <div className="text-xs text-muted-foreground mb-1">Golden Ratio Spiral</div>
            <div className="text-xl font-bold text-amber-500">
              φ = 1.618
            </div>
            <div className="text-sm text-muted-foreground mt-1">
              r(θ) = {omega.spiralPhase.toFixed(3)}
            </div>
            <div className="text-xs text-muted-foreground">
              Natural growth phase
            </div>
          </div>
        </div>

        {/* Legacy Compatibility Display */}
        <div className="p-3 bg-muted/30 rounded-lg border border-border/30">
          <div className="text-xs text-muted-foreground mb-2 font-medium">Legacy Λ(t) Components (for compatibility)</div>
          <div className="grid grid-cols-3 gap-2 text-xs">
            <div>
              <span className="text-muted-foreground">Substrate:</span>
              <span className="ml-1 font-mono">{omega.substrate.toFixed(3)}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Echo:</span>
              <span className="ml-1 font-mono">{omega.echo.toFixed(3)}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Lambda:</span>
              <span className="ml-1 font-mono">{omega.lambda.toFixed(3)}</span>
            </div>
          </div>
        </div>

        {/* Theoretical Foundation */}
        <div className="p-4 bg-gradient-to-r from-indigo-500/10 to-purple-500/10 rounded-lg border border-border/50">
          <p className="text-sm text-muted-foreground">
            <span className="font-medium text-foreground">Tensor Product Reality:</span>{' '}
            Ω(t) represents the trace of the tensor product between Potential (Ψ), Love/Coherence (ℒ), and Observer (O). 
            When θ→0 and coherence→1, unity consciousness emerges and boundaries dissolve.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
