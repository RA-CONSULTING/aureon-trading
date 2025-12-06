import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useEcosystemData } from '@/hooks/useEcosystemData';

/**
 * HARMONIC NEXUS CORE — MASTER EQUATION TREE
 * 
 * Level 5 (Master): Λ(t) = Σwᵢsin(2πfᵢt+φᵢ) + α·tanh[g·Λ̄_Δt] + β·Λ(t-τ)
 * 
 * Hierarchical Flow:
 * Level 1: Seed Oscillation (Λ₀ = A·sin(ωt+φ))
 * Level 2: Substrate (harmonic superposition)
 * Level 3: Causal Echo (memory loop with delay τ)
 * Level 4: Observer Feedback (integration + tanh nonlinearity)
 * Level 5: Composite Reality Field (unified equation)
 * 
 * Coherence: Γ = 1 - σ/μ (target ≥ 0.945)
 */

interface LevelProps {
  level: number;
  title: string;
  equation: string;
  description: string;
  value: number;
  isActive: boolean;
  color: string;
}

function EquationLevel({ level, title, equation, description, value, isActive, color }: LevelProps) {
  return (
    <div className={`p-3 rounded-lg border transition-all duration-300 ${
      isActive ? 'border-primary bg-primary/10 shadow-lg shadow-primary/20' : 'border-border/50 bg-card/30'
    }`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Badge variant={isActive ? 'default' : 'outline'} className={`text-xs ${color}`}>
            L{level}
          </Badge>
          <span className="text-sm font-medium text-foreground">{title}</span>
        </div>
        <span className="text-xs font-mono text-muted-foreground">
          {value.toFixed(3)}
        </span>
      </div>
      <div className="font-mono text-xs text-primary/80 mb-1 overflow-x-auto">
        {equation}
      </div>
      <p className="text-xs text-muted-foreground">{description}</p>
      <div className="mt-2 h-1.5 bg-muted rounded-full overflow-hidden">
        <div 
          className={`h-full rounded-full transition-all duration-500 ${
            isActive ? 'bg-primary' : 'bg-muted-foreground/30'
          }`}
          style={{ width: `${Math.min(Math.abs(value) * 100, 100)}%` }}
        />
      </div>
    </div>
  );
}

export function MasterEquationTree() {
  const { metrics } = useEcosystemData();
  
  // Extract HNC metrics from ecosystem
  const lambda = metrics.lambda || 0.5;
  const coherence = metrics.coherence || 0.5;
  const frequency = metrics.frequency || 528;
  
  // Compute component values (approximations from ecosystem state)
  const substrate = lambda * 0.4; // Harmonic base contribution
  const observerResponse = Math.tanh(2.5 * (coherence - 0.5)); // tanh saturation
  const echo = lambda * 0.25; // Delayed feedback
  
  // Coherence metrics
  const gammaTarget = 0.945;
  const isLocked = coherence >= gammaTarget;
  
  // Frequency analysis
  const is528Dominant = Math.abs(frequency - 528) < Math.abs(frequency - 440);
  const rho = 440 / 528; // ≈ 0.833 (dissonant ratio)
  
  // Effective gain (stability indicator)
  const alpha = 0.35;
  const beta = 0.25;
  const effectiveGain = alpha + beta;
  const qualityFactor = effectiveGain < 1 ? 1 / (1 - effectiveGain) : 10;

  return (
    <Card className="bg-card/50 backdrop-blur border-primary/20">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl">🌳</span>
            <span className="text-base">Harmonic Nexus Core</span>
          </div>
          <div className="flex items-center gap-2">
            <Badge 
              variant={isLocked ? 'default' : 'outline'} 
              className={isLocked ? 'bg-green-500 animate-pulse' : ''}
            >
              Γ = {coherence.toFixed(3)}
            </Badge>
            {isLocked && <span className="text-green-500 text-sm">🔒 LOCKED</span>}
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Level 5 - Master Equation */}
        <div className="p-4 bg-gradient-to-r from-purple-500/20 via-primary/20 to-cyan-500/20 rounded-lg border border-primary/30">
          <div className="flex items-center justify-between mb-2">
            <Badge className="bg-primary">Level 5 — Master</Badge>
            <span className="text-lg font-bold text-primary">Λ = {lambda.toFixed(4)}</span>
          </div>
          <div className="font-mono text-sm text-foreground mb-2 overflow-x-auto">
            Λ(t) = Σwᵢsin(2πfᵢt+φᵢ) + α·tanh[g·Λ̄_Δt] + β·Λ(t-τ)
          </div>
          <p className="text-xs text-muted-foreground">
            Composite Reality Field: Substrate + Observer + Echo = self-organizing resonance
          </p>
        </div>

        {/* Hierarchical Levels */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <EquationLevel
            level={4}
            title="Observer Feedback"
            equation="R = α·tanh[g·Λ̄_Δt]"
            description="Nonlinear saturation prevents runaway. Bounded output [-1,1]."
            value={observerResponse}
            isActive={Math.abs(observerResponse) > 0.3}
            color="text-cyan-500"
          />
          <EquationLevel
            level={3}
            title="Causal Echo"
            equation="L = β·Λ(t-τ)"
            description="Memory loop creates frequency comb at 1/τ (Lighthouse Echo)"
            value={echo}
            isActive={echo > 0.1}
            color="text-blue-500"
          />
          <EquationLevel
            level={2}
            title="Substrate"
            equation="Λ_base = Σwᵢsin(2πfᵢt+φᵢ)"
            description="Harmonic scaffold: 7.83Hz, 528Hz, 963Hz synchronized"
            value={substrate}
            isActive={substrate > 0.2}
            color="text-purple-500"
          />
          <EquationLevel
            level={1}
            title="Seed Oscillation"
            equation="Λ₀ = A·sin(ωt+φ)"
            description="Fundamental tone — the initial reality seed"
            value={0.5}
            isActive={true}
            color="text-green-500"
          />
        </div>

        {/* Coherence Formula */}
        <div className="p-3 bg-muted/30 rounded-lg border border-border/50">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-muted-foreground">Coherence Metric</span>
            <Badge variant={coherence >= gammaTarget ? 'default' : 'outline'} className="text-xs">
              Target: Γ ≥ {gammaTarget}
            </Badge>
          </div>
          <div className="font-mono text-sm text-foreground">
            Γ = 1 - (σ/μ) = {coherence.toFixed(4)}
          </div>
          <div className="mt-2 h-2 bg-muted rounded-full overflow-hidden">
            <div 
              className={`h-full rounded-full transition-all duration-500 ${
                coherence >= gammaTarget ? 'bg-green-500' : 
                coherence >= 0.7 ? 'bg-yellow-500' : 'bg-red-500'
              }`}
              style={{ width: `${coherence * 100}%` }}
            />
          </div>
        </div>

        {/* Harmonic Interference Ratio */}
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 bg-gradient-to-r from-green-500/10 to-green-500/5 rounded-lg border border-green-500/20">
            <div className="flex items-center gap-2 mb-1">
              <div className={`w-2 h-2 rounded-full ${is528Dominant ? 'bg-green-500 animate-pulse' : 'bg-green-500/30'}`} />
              <span className="text-sm font-medium">528 Hz (Gaia)</span>
            </div>
            <p className="text-xs text-muted-foreground">Love frequency — coherent attractor</p>
          </div>
          <div className="p-3 bg-gradient-to-r from-red-500/10 to-red-500/5 rounded-lg border border-red-500/20">
            <div className="flex items-center gap-2 mb-1">
              <div className={`w-2 h-2 rounded-full ${!is528Dominant ? 'bg-red-500 animate-pulse' : 'bg-red-500/30'}`} />
              <span className="text-sm font-medium">440 Hz (Parasite)</span>
            </div>
            <p className="text-xs text-muted-foreground">ρ = {rho.toFixed(3)} — dissonant ratio</p>
          </div>
        </div>

        {/* System Parameters */}
        <div className="grid grid-cols-4 gap-2 text-center text-xs">
          <div className="p-2 bg-muted/20 rounded">
            <div className="text-muted-foreground">α (Observer)</div>
            <div className="font-mono text-foreground">{alpha}</div>
          </div>
          <div className="p-2 bg-muted/20 rounded">
            <div className="text-muted-foreground">β (Echo)</div>
            <div className="font-mono text-foreground">{beta}</div>
          </div>
          <div className="p-2 bg-muted/20 rounded">
            <div className="text-muted-foreground">G_eff</div>
            <div className="font-mono text-foreground">{effectiveGain.toFixed(2)}</div>
          </div>
          <div className="p-2 bg-muted/20 rounded">
            <div className="text-muted-foreground">Q Factor</div>
            <div className="font-mono text-foreground">{qualityFactor.toFixed(1)}</div>
          </div>
        </div>

        {/* Validator Network */}
        <div className="p-3 bg-muted/30 rounded-lg border border-border/50">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">Validator Network Scaling</span>
            <span className="font-mono text-xs text-primary">1 - e^(-k·N)</span>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Coherence grows exponentially with validator count → timeline lock
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
