import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Brain, Heart, Activity, Sparkles } from "lucide-react";
import { useSchumannResonance } from "@/hooks/useSchumannResonance";
import { useCelestialData } from "@/hooks/useCelestialData";

interface ConsciousnessCoherenceTrackerProps {
  currentCoherence: number;
}

export function ConsciousnessCoherenceTracker({ currentCoherence }: ConsciousnessCoherenceTrackerProps) {
  const { schumannData } = useSchumannResonance();
  const { celestialBoost } = useCelestialData();

  // Calculate total consciousness field coherence
  const schumannBoost = schumannData?.coherenceBoost || 0;
  const totalBoost = celestialBoost + schumannBoost;
  const enhancedCoherence = currentCoherence * (1 + totalBoost);

  // Simulate biometric data (in production, this would come from actual sensors)
  const mockHRV = 45 + (schumannBoost * 200); // Heart Rate Variability
  const mockAlpha = 0.4 + (celestialBoost * 2); // Alpha brain waves
  const mockTheta = 0.3 + (schumannBoost * 1.5); // Theta brain waves

  const getCoherenceLevel = (coherence: number) => {
    if (coherence >= 0.9) return { level: 'TRANSCENDENT', color: 'text-purple-500', bg: 'bg-purple-500/20' };
    if (coherence >= 0.7) return { level: 'PEAK', color: 'text-green-500', bg: 'bg-green-500/20' };
    if (coherence >= 0.5) return { level: 'ELEVATED', color: 'text-blue-500', bg: 'bg-blue-500/20' };
    if (coherence >= 0.3) return { level: 'ACTIVE', color: 'text-yellow-500', bg: 'bg-yellow-500/20' };
    return { level: 'FORMING', color: 'text-orange-500', bg: 'bg-orange-500/20' };
  };

  const coherenceStatus = getCoherenceLevel(enhancedCoherence);

  return (
    <Card className="bg-card/50 backdrop-blur border-border/50 relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 via-blue-500/5 to-green-500/5" />
      
      <CardHeader className="relative">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-purple-500" />
              Consciousness Field Coherence
            </CardTitle>
            <CardDescription>
              Multi-dimensional consciousness alignment tracking
            </CardDescription>
          </div>
          <Badge className={`${coherenceStatus.color} ${coherenceStatus.bg} border-0 text-lg px-4 py-2`}>
            {coherenceStatus.level}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="relative space-y-4">
        {/* Main Coherence Display */}
        <div className="flex items-center justify-center p-6 bg-gradient-to-br from-purple-500/10 to-blue-500/10 rounded-lg border border-border/50">
          <div className="text-center">
            <div className="flex items-center justify-center gap-2 mb-2">
              <Sparkles className="w-6 h-6 text-purple-500" />
              <span className="text-sm text-muted-foreground font-medium">Total Field Coherence</span>
            </div>
            <div className="text-5xl font-bold bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
              {(enhancedCoherence * 100).toFixed(2)}%
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              Base: {(currentCoherence * 100).toFixed(2)}% • Boost: +{(totalBoost * 100).toFixed(1)}%
            </div>
          </div>
        </div>

        {/* Boost Sources */}
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 bg-background/50 rounded-lg border border-border/50">
            <div className="flex items-center gap-2 mb-2">
              <Activity className="w-4 h-4 text-green-500" />
              <span className="text-xs text-muted-foreground">Schumann Boost</span>
            </div>
            <div className="text-2xl font-bold text-green-500">+{(schumannBoost * 100).toFixed(1)}%</div>
            <Progress value={(schumannBoost / 0.12) * 100} className="mt-2 h-1" />
            <p className="text-xs text-muted-foreground mt-1">
              {schumannData?.fundamentalHz.toFixed(2) || '—'} Hz
            </p>
          </div>

          <div className="p-4 bg-background/50 rounded-lg border border-border/50">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="w-4 h-4 text-blue-500" />
              <span className="text-xs text-muted-foreground">Celestial Boost</span>
            </div>
            <div className="text-2xl font-bold text-blue-500">+{(celestialBoost * 100).toFixed(1)}%</div>
            <Progress value={(celestialBoost / 0.15) * 100} className="mt-2 h-1" />
            <p className="text-xs text-muted-foreground mt-1">
              Cosmic alignment
            </p>
          </div>
        </div>

        {/* Biometric Indicators (Simulated) */}
        <div className="p-4 bg-muted/50 rounded-lg">
          <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
            <Heart className="w-4 h-4 text-red-500" />
            Consciousness Biometrics
          </h4>
          
          <div className="grid grid-cols-3 gap-3">
            <div className="text-center">
              <div className="text-xs text-muted-foreground mb-1">HRV</div>
              <div className="text-lg font-bold">{mockHRV.toFixed(0)}</div>
              <div className="text-xs text-green-500">Optimal</div>
            </div>
            
            <div className="text-center">
              <div className="text-xs text-muted-foreground mb-1">Alpha</div>
              <div className="text-lg font-bold">{(mockAlpha * 100).toFixed(0)}%</div>
              <div className="text-xs text-blue-500">8-13 Hz</div>
            </div>
            
            <div className="text-center">
              <div className="text-xs text-muted-foreground mb-1">Theta</div>
              <div className="text-lg font-bold">{(mockTheta * 100).toFixed(0)}%</div>
              <div className="text-xs text-purple-500">4-8 Hz</div>
            </div>
          </div>
        </div>

        {/* Coherence Level Descriptions */}
        <div className="p-4 bg-muted/50 rounded-lg">
          <h4 className="text-sm font-semibold mb-2">Coherence Levels</h4>
          <ul className="text-xs text-muted-foreground space-y-1">
            <li>• <strong className="text-purple-500">Transcendent (90%+)</strong>: Unity consciousness, optimal trading</li>
            <li>• <strong className="text-green-500">Peak (70-89%)</strong>: High alignment, LHE probability elevated</li>
            <li>• <strong className="text-blue-500">Elevated (50-69%)</strong>: Strong coherence, good signal quality</li>
            <li>• <strong className="text-yellow-500">Active (30-49%)</strong>: Building coherence, monitor closely</li>
            <li>• <strong className="text-orange-500">Forming (&lt;30%)</strong>: Low coherence, wait for alignment</li>
          </ul>
        </div>

        {/* Real-time Insights */}
        {enhancedCoherence >= 0.9 && (
          <div className="p-4 bg-purple-500/10 border border-purple-500/30 rounded-lg">
            <p className="text-sm text-purple-400 font-medium">
              ⚡ Transcendent consciousness coherence achieved! Earth resonance, celestial alignments, 
              and field dynamics are in perfect harmony. Optimal window for high-confidence trades.
            </p>
          </div>
        )}

        <div className="pt-2 border-t border-border/50">
          <p className="text-xs text-muted-foreground text-center">
            Real-time consciousness field monitoring • Schumann Resonance • Celestial Alignment
          </p>
        </div>
      </CardContent>
    </Card>
  );
}