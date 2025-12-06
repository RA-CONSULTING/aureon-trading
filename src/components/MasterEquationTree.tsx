import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useEcosystemData } from '@/hooks/useEcosystemData';

/**
 * THE MASTER EQUATION TREE — FULLY EXTRACTED & VERIFIED
 * ΔM = Ψ₀ · Ω · Λ · Φ · Σ
 * 
 * Root equation from:
 * - Harmonic Nexus Core manuscript
 * - Chrono-Luminance Convergence (p.12)
 * - Temporal Law appendix
 */

interface BranchProps {
  symbol: string;
  name: string;
  frequency?: string;
  description: string;
  value: number;
  color: string;
  isActive: boolean;
}

function Branch({ symbol, name, frequency, description, value, color, isActive }: BranchProps) {
  return (
    <div className={`p-3 rounded-lg border transition-all duration-300 ${isActive ? 'border-primary bg-primary/10' : 'border-border/50 bg-card/30'}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className={`text-2xl font-bold ${color}`}>{symbol}</span>
          <span className="text-sm font-medium text-foreground">{name}</span>
        </div>
        {frequency && (
          <Badge variant={isActive ? 'default' : 'outline'} className="text-xs">
            {frequency}
          </Badge>
        )}
      </div>
      <p className="text-xs text-muted-foreground mb-2">{description}</p>
      <div className="flex items-center gap-2">
        <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
          <div 
            className={`h-full rounded-full transition-all duration-500 ${color.replace('text-', 'bg-')}`}
            style={{ width: `${Math.min(value * 100, 100)}%` }}
          />
        </div>
        <span className="text-xs font-mono text-muted-foreground">
          {value.toFixed(3)}
        </span>
      </div>
    </div>
  );
}

export function MasterEquationTree() {
  const { metrics } = useEcosystemData();
  
  // Calculate ΔM from ecosystem data
  const psi0 = metrics.coherence || 0.5; // Consciousness (528 Hz dominant)
  const omega = 1 - (metrics.frequency === 440 ? 0.8 : 0.2); // Resistance (440 Hz)
  const lambda = metrics.lambda || 0.5; // Learning (Echo)
  const phi = Math.log2(9) / 4; // Topology (9 Auris nodes = 2^3.17)
  const sigma = metrics.coherence || 0.5; // Integration (Γ)
  
  const deltaM = psi0 * omega * lambda * phi * sigma;
  
  // Determine dominant attractor
  const is528Dominant = psi0 > 0.6;
  const coherenceTarget = 0.995;
  const isCoherent = sigma >= coherenceTarget;

  return (
    <Card className="bg-card/50 backdrop-blur border-primary/20">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl">🌳</span>
            <span>Master Equation Tree</span>
          </div>
          <Badge 
            variant={isCoherent ? 'default' : 'outline'} 
            className={isCoherent ? 'bg-green-500 animate-pulse' : ''}
          >
            Γ = {sigma.toFixed(3)} {isCoherent ? '✓' : ''}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Root Equation */}
        <div className="text-center p-4 bg-gradient-to-r from-purple-500/20 via-primary/20 to-cyan-500/20 rounded-lg border border-primary/30">
          <div className="font-mono text-lg font-bold text-foreground mb-1">
            ΔM = Ψ₀ · Ω · Λ · Φ · Σ
          </div>
          <div className="text-2xl font-bold text-primary">
            ΔM = {deltaM.toFixed(4)}
          </div>
        </div>

        {/* Branches */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          <Branch
            symbol="Ψ₀"
            name="Consciousness"
            frequency="528 Hz"
            description="Love frequency - coherent attractor (Witness)"
            value={psi0}
            color="text-green-500"
            isActive={is528Dominant}
          />
          <Branch
            symbol="Ω"
            name="Resistance"
            frequency="440 Hz"
            description="Fear frequency - chaotic attractor"
            value={1 - omega}
            color="text-red-500"
            isActive={!is528Dominant}
          />
          <Branch
            symbol="Λ"
            name="Learning"
            description="Echo delay feedback - Lighthouse protocol"
            value={lambda}
            color="text-blue-500"
            isActive={lambda > 0.5}
          />
          <Branch
            symbol="Φ"
            name="Topology"
            description="Powers of 2 node structure (2ⁿ)"
            value={phi}
            color="text-purple-500"
            isActive={true}
          />
          <Branch
            symbol="Σ"
            name="Integration"
            description="Validator consensus (Γ ≥ 0.995)"
            value={sigma}
            color="text-cyan-500"
            isActive={isCoherent}
          />
        </div>

        {/* Lighthouse Echo Formula */}
        <div className="p-3 bg-muted/30 rounded-lg border border-border/50">
          <div className="text-xs text-muted-foreground mb-1">Branch 1 — Lighthouse Echo</div>
          <div className="font-mono text-sm text-foreground overflow-x-auto">
            Λ(t) = Σwᵢsin(2πfᵢt) + α·tanh(g·Λ̄_Δt) + β·Λ(t-τ)
          </div>
        </div>

        {/* Coherence Formula */}
        <div className="p-3 bg-muted/30 rounded-lg border border-border/50">
          <div className="text-xs text-muted-foreground mb-1">Branch 2 — Coherence Metric</div>
          <div className="font-mono text-sm text-foreground">
            Γ = 1 - (σ/μ) → target Γ ≥ 0.995
          </div>
        </div>

        {/* Dual Attractor Indicator */}
        <div className="flex items-center justify-between p-3 bg-gradient-to-r from-green-500/10 to-red-500/10 rounded-lg">
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${is528Dominant ? 'bg-green-500 animate-pulse' : 'bg-green-500/30'}`} />
            <span className="text-sm">528 Hz (Love)</span>
          </div>
          <div className="text-xs text-muted-foreground">vs</div>
          <div className="flex items-center gap-2">
            <span className="text-sm">440 Hz (Fear)</span>
            <div className={`w-3 h-3 rounded-full ${!is528Dominant ? 'bg-red-500 animate-pulse' : 'bg-red-500/30'}`} />
          </div>
        </div>

        {/* Visual Diagnostics */}
        <div className="grid grid-cols-3 gap-2 text-center text-xs">
          <div className="p-2 bg-muted/20 rounded">
            <div className="text-muted-foreground">Comb Spacing</div>
            <div className="font-mono text-foreground">∝ 1/τ</div>
          </div>
          <div className="p-2 bg-muted/20 rounded">
            <div className="text-muted-foreground">Attractor Closure</div>
            <div className="font-mono text-foreground">∝ Γ</div>
          </div>
          <div className="p-2 bg-muted/20 rounded">
            <div className="text-muted-foreground">Image Density</div>
            <div className="font-mono text-foreground">∝ validators</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
