/**
 * 🦆🪐 PLATYPUS COHERENCE PANEL - Song of the Sphaerae Visualization 🪐🦆
 * 
 * Real-time planetary coherence display showing:
 * - Gamma (Γ) coherence value with visual indicator
 * - Process tree breakdown (S, Q, H, E, O)
 * - Lighthouse event detection
 * - Top aligned planets
 * - Cascade contribution to trading
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { platypusEngine, type PlatypusState } from '@/core/platypusCoherenceEngine';
import { 
  Orbit, 
  Waves, 
  Sparkles, 
  Zap, 
  Eye, 
  Activity,
  Sun
} from 'lucide-react';

interface PlatypusCoherencePanelProps {
  compact?: boolean;
}

export default function PlatypusCoherencePanel({ compact = false }: PlatypusCoherencePanelProps) {
  const [state, setState] = useState<PlatypusState>(platypusEngine.getState());
  
  useEffect(() => {
    // Start the engine if not already running
    platypusEngine.start(1000);
    
    // Subscribe to updates
    const unsubscribe = platypusEngine.subscribe((newState) => {
      setState(newState);
    });
    
    return () => {
      unsubscribe();
    };
  }, []);
  
  const getCoherenceColor = (gamma: number) => {
    if (gamma >= 0.75) return 'text-green-400 bg-green-500/20';
    if (gamma >= 0.5) return 'text-yellow-400 bg-yellow-500/20';
    if (gamma >= 0.25) return 'text-orange-400 bg-orange-500/20';
    return 'text-red-400 bg-red-500/20';
  };
  
  const getCoherenceLabel = (gamma: number) => {
    if (gamma >= 0.75) return 'EXCELLENT';
    if (gamma >= 0.5) return 'GOOD';
    if (gamma >= 0.25) return 'MODERATE';
    return 'LOW';
  };
  
  // Compact version for dashboard
  if (compact) {
    return (
      <div className="flex items-center gap-2 p-2 rounded-lg bg-muted/30 border border-border/30">
        <Orbit className="w-4 h-4 text-purple-400" />
        <span className="text-sm font-medium">Γ</span>
        <span className={`font-mono text-sm ${state.Gamma_t >= 0.75 ? 'text-green-400' : 'text-foreground'}`}>
          {state.Gamma_t.toFixed(3)}
        </span>
        {state.L_t && (
          <Badge className="bg-yellow-500/30 text-yellow-300 text-xs animate-pulse">
            🔦 LIGHTHOUSE
          </Badge>
        )}
        <span className="text-xs text-muted-foreground ml-auto">
          ×{state.cascadeContribution.toFixed(2)}
        </span>
      </div>
    );
  }
  
  return (
    <Card className="border-purple-500/30 bg-gradient-to-br from-purple-950/20 to-background">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg flex items-center gap-2">
          <Orbit className="w-5 h-5 text-purple-400 animate-spin" style={{ animationDuration: '8s' }} />
          Song of the Sphaerae
          <Badge variant="outline" className="ml-auto text-xs">
            {state.ephemerisSource === 'DE440' ? '📡 DE440' : '🔮 Keplerian'}
          </Badge>
        </CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Main Coherence Display */}
        <div className="flex items-center justify-between p-4 rounded-lg bg-muted/30 border border-purple-500/30">
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground uppercase tracking-wide">
              Planetary Coherence Γ(t)
            </div>
            <div className={`text-4xl font-mono font-bold ${state.Gamma_t >= 0.75 ? 'text-green-400' : state.Gamma_t >= 0.5 ? 'text-yellow-400' : 'text-foreground'}`}>
              {state.Gamma_t.toFixed(3)}
            </div>
            <Badge className={getCoherenceColor(state.Gamma_t)}>
              {getCoherenceLabel(state.Gamma_t)}
            </Badge>
          </div>
          
          <div className="text-right space-y-1">
            <div className="text-xs text-muted-foreground">Cascade</div>
            <div className="text-2xl font-mono text-purple-400">
              ×{state.cascadeContribution.toFixed(2)}
            </div>
            {state.L_t && (
              <Badge className="bg-yellow-500/30 text-yellow-300 animate-pulse">
                🔦 LIGHTHOUSE
              </Badge>
            )}
          </div>
        </div>
        
        {/* Lighthouse Counter */}
        {state.lighthouseCount > 0 && (
          <div className="flex items-center justify-center gap-2 py-2 rounded bg-yellow-500/10 border border-yellow-500/30">
            <Sparkles className="w-4 h-4 text-yellow-400" />
            <span className="text-sm text-yellow-300">
              {state.lighthouseCount} Lighthouse Events Detected
            </span>
          </div>
        )}
        
        {/* Process Tree */}
        <div className="space-y-2">
          <div className="text-xs text-muted-foreground uppercase tracking-wide mb-2">
            Process Tree S→Q→H→E→O→Λ→Γ
          </div>
          
          <ProcessBar label="S(t) Spherical" value={state.S_t} icon={<Sun className="w-3 h-3" />} color="text-orange-400" />
          <ProcessBar label="Q(t) Quality" value={state.Q_t} icon={<Activity className="w-3 h-3" />} color="text-blue-400" />
          <ProcessBar label="H(t) Harmonic" value={state.H_t} icon={<Waves className="w-3 h-3" />} color="text-cyan-400" />
          <ProcessBar label="E(t) Energy" value={state.E_t} icon={<Zap className="w-3 h-3" />} color="text-yellow-400" />
          <ProcessBar label="O(t) Observer" value={state.O_t} icon={<Eye className="w-3 h-3" />} color="text-purple-400" />
          <ProcessBar label="Λ(t) Memory" value={state.Lambda_t} icon={<Sparkles className="w-3 h-3" />} color="text-pink-400" />
        </div>
        
        {/* Top Aligned Planets */}
        <div className="space-y-2">
          <div className="text-xs text-muted-foreground uppercase tracking-wide">
            Top Aligned Planets
          </div>
          <div className="flex flex-wrap gap-2">
            {state.topAligned.map((planet, i) => (
              <Badge 
                key={planet} 
                variant="outline" 
                className={`${i === 0 ? 'border-green-500/50 text-green-400' : 'border-border/50'}`}
              >
                {getPlanetEmoji(planet.split('=')[0])} {planet}
              </Badge>
            ))}
          </div>
        </div>
        
        {/* Planetary Positions */}
        <div className="space-y-2">
          <div className="text-xs text-muted-foreground uppercase tracking-wide">
            Planetary Alignments
          </div>
          <div className="grid grid-cols-4 gap-2">
            {state.planets.map(planet => (
              <div 
                key={planet.name}
                className="text-center p-2 rounded bg-muted/20 border border-border/30"
              >
                <div className="text-lg">{getPlanetEmoji(planet.name)}</div>
                <div className="text-xs text-muted-foreground capitalize">{planet.name}</div>
                <div className={`text-xs font-mono ${planet.quality > 0.7 ? 'text-green-400' : 'text-foreground'}`}>
                  q={planet.quality.toFixed(2)}
                </div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function ProcessBar({ 
  label, 
  value, 
  icon, 
  color 
}: { 
  label: string; 
  value: number; 
  icon: React.ReactNode; 
  color: string;
}) {
  return (
    <div className="flex items-center gap-2">
      <div className={`${color}`}>{icon}</div>
      <span className="text-xs w-24 text-muted-foreground">{label}</span>
      <div className="flex-1">
        <Progress value={value * 100} className="h-2" />
      </div>
      <span className="text-xs font-mono w-12 text-right">{value.toFixed(2)}</span>
    </div>
  );
}

function getPlanetEmoji(name: string): string {
  const emojis: Record<string, string> = {
    mercury: '☿️',
    venus: '♀️',
    mars: '♂️',
    jupiter: '♃',
    saturn: '♄',
    uranus: '⛢',
    neptune: '♆',
    earth: '🌍',
  };
  return emojis[name.toLowerCase()] || '🪐';
}
