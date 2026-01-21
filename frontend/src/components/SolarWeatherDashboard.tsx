import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useCelestialData } from '@/hooks/useCelestialData';
import { Sun, Moon, Zap, TrendingUp, Activity, Orbit } from 'lucide-react';

export const SolarWeatherDashboard = () => {
  const { celestialBoost, sacredFrequencies, isLoading } = useCelestialData();

  if (isLoading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-muted rounded w-1/3" />
          <div className="h-32 bg-muted rounded" />
        </div>
      </Card>
    );
  }

  const coherenceImpact = celestialBoost * 100;
  const impactLevel = coherenceImpact > 10 ? 'high' : coherenceImpact > 5 ? 'medium' : 'low';
  const impactColor = impactLevel === 'high' ? 'text-green-500' : impactLevel === 'medium' ? 'text-yellow-500' : 'text-muted-foreground';

  return (
    <div className="space-y-6">
      <Card className="p-6 bg-gradient-to-br from-background to-muted/20 border-primary/20">
        <div className="flex items-center gap-3 mb-6">
          <Sun className="w-8 h-8 text-primary animate-pulse" />
          <div>
            <h2 className="text-2xl font-bold text-foreground">Solar Weather Dashboard</h2>
            <p className="text-sm text-muted-foreground">Real-time space weather & market coherence impact</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Coherence Impact */}
          <Card className="p-4 border-primary/30 bg-background/50">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className={`w-5 h-5 ${impactColor}`} />
              <h3 className="font-semibold text-foreground">Market Coherence Impact</h3>
            </div>
            <div className="space-y-2">
              <div className={`text-3xl font-bold ${impactColor}`}>
                {coherenceImpact > 0 ? '+' : ''}{coherenceImpact.toFixed(1)}%
              </div>
              <Badge variant={impactLevel === 'high' ? 'default' : 'secondary'} className="uppercase">
                {impactLevel} Impact
              </Badge>
              <p className="text-xs text-muted-foreground mt-2">
                {impactLevel === 'high' && 'Strong cosmic alignment enhancing field coherence'}
                {impactLevel === 'medium' && 'Moderate celestial influence on trading signals'}
                {impactLevel === 'low' && 'Minimal space weather impact on coherence'}
              </p>
            </div>
          </Card>

          {/* Solar Activity */}
          <Card className="p-4 border-orange-500/30 bg-background/50">
            <div className="flex items-center gap-2 mb-2">
              <Zap className="w-5 h-5 text-orange-500" />
              <h3 className="font-semibold text-foreground">Solar Activity</h3>
            </div>
            <div className="space-y-2">
              <div className="text-2xl font-bold text-orange-500">MONITORING</div>
              <Badge variant="outline" className="border-orange-500/50 text-orange-500">
                X-Ray Flux Active
              </Badge>
              <p className="text-xs text-muted-foreground mt-2">
                Tracking M & X-class flares for coherence correlation analysis
              </p>
            </div>
          </Card>

          {/* Moon Phase */}
          <Card className="p-4 border-blue-500/30 bg-background/50">
            <div className="flex items-center gap-2 mb-2">
              <Moon className="w-5 h-5 text-blue-500" />
              <h3 className="font-semibold text-foreground">Lunar Influence</h3>
            </div>
            <div className="space-y-2">
              <div className="text-2xl font-bold text-blue-500">ACTIVE</div>
              <Badge variant="outline" className="border-blue-500/50 text-blue-500">
                Phase Tracking
              </Badge>
              <p className="text-xs text-muted-foreground mt-2">
                Full & New Moon phases show strongest market correlation
              </p>
            </div>
          </Card>
        </div>
      </Card>

      {/* Geomagnetic Forecast */}
      <Card className="p-6 bg-gradient-to-br from-background to-primary/5 border-primary/20">
        <div className="flex items-center gap-2 mb-4">
          <Activity className="w-6 h-6 text-primary" />
          <h3 className="text-xl font-semibold text-foreground">Geomagnetic Storm Forecast</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-3">
            <div>
              <div className="text-sm text-muted-foreground mb-1">Current Kp Index</div>
              <div className="text-2xl font-bold text-primary">Kp 3-4</div>
              <Badge variant="secondary" className="mt-1">Unsettled</Badge>
            </div>
            <p className="text-sm text-muted-foreground">
              Minor geomagnetic activity detected. Increased coherence fluctuations expected in 6-12 hour window.
            </p>
          </div>
          <div className="space-y-3">
            <div>
              <div className="text-sm text-muted-foreground mb-1">24h Forecast</div>
              <div className="text-2xl font-bold text-yellow-500">G1 Watch</div>
              <Badge variant="outline" className="mt-1 border-yellow-500/50 text-yellow-500">
                Minor Storm
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground">
              G1 conditions possible if CME arrives. May enhance LHE signal probability by 15-20%.
            </p>
          </div>
        </div>
      </Card>

      {/* Sacred Frequencies */}
      {sacredFrequencies.length > 0 && (
        <Card className="p-6 bg-gradient-to-br from-background to-secondary/10 border-secondary/20">
          <div className="flex items-center gap-2 mb-4">
            <Orbit className="w-6 h-6 text-secondary" />
            <h3 className="text-xl font-semibold text-foreground">Active Sacred Frequencies</h3>
          </div>
          <div className="flex flex-wrap gap-2">
            {sacredFrequencies.map((freq) => (
              <Badge key={freq} variant="secondary" className="text-base px-3 py-1">
                {freq} Hz
              </Badge>
            ))}
          </div>
          <p className="text-sm text-muted-foreground mt-3">
            Celestial alignments activating specific Solfeggio frequencies. These harmonics enhance field resonance and trading signal quality.
          </p>
        </Card>
      )}

      {/* Predictive Analysis */}
      <Card className="p-6 bg-gradient-to-br from-background to-accent/10 border-accent/20">
        <h3 className="text-xl font-semibold text-foreground mb-4">Predictive Analysis</h3>
        <div className="space-y-3">
          <div className="flex items-start gap-3">
            <div className="w-2 h-2 rounded-full bg-green-500 mt-2" />
            <div>
              <div className="font-semibold text-foreground">High Coherence Window</div>
              <p className="text-sm text-muted-foreground">
                Next 6-12 hours show optimal conditions for LHE signal generation based on current space weather trajectory.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-2 h-2 rounded-full bg-yellow-500 mt-2" />
            <div>
              <div className="font-semibold text-foreground">Planetary Alignment</div>
              <p className="text-sm text-muted-foreground">
                Mercury-Venus conjunction in 48h may amplify substrate coherence. Monitor for increased signal strength.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-2 h-2 rounded-full bg-blue-500 mt-2" />
            <div>
              <div className="font-semibold text-foreground">Solar Minimum Phase</div>
              <p className="text-sm text-muted-foreground">
                Approaching solar minimum. Historical data shows 18% increase in optimal trading signals during low solar activity.
              </p>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};
