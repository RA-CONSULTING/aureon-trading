import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { HarmonicNexusCore, type HNCRegionTick, type SurgeEvent } from '@/core/harmonicNexusCore';
import { stampNow } from '@/lib/HighResClock';

interface HarmonicNexusCoreDisplayProps {
  region?: string;
  className?: string;
}

export const HarmonicNexusCoreDisplay: React.FC<HarmonicNexusCoreDisplayProps> = ({
  region = "Global",
  className = ""
}) => {
  const [core] = useState(() => new HarmonicNexusCore());
  const [tick, setTick] = useState<HNCRegionTick | null>(null);
  const [isActive, setIsActive] = useState(false);

  useEffect(() => {
    const interval = setInterval(() => {
      // Simulate incoming streams
      const stamp = stampNow();
      
      // Add simulated resonance data
      core.addResonance({
        t: stamp.epochMillis / 1000,
        t_micros: stamp.epochMicros,
        band: "7.83",
        power: 0.6 + Math.random() * 0.4,
        phase: Math.random() * Math.PI * 2,
        amplitude: 0.8 + Math.random() * 0.2
      });

      // Add simulated emotional data
      core.addAffect({
        t: stamp.epochMillis / 1000,
        t_micros: stamp.epochMicros,
        v: (Math.sin(Date.now() / 10000) + 1) / 2, // Valence
        a: (Math.cos(Date.now() / 8000) + 1) / 2,  // Arousal
        coherence: 0.7 + Math.random() * 0.3
      });

      // Run core orchestration
      const newTick = core.run(region);
      setTick(newTick);
      setIsActive(true);
    }, 100);

    return () => clearInterval(interval);
  }, [core, region]);

  if (!tick) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            🔮 Harmonic Nexus Core
            <Badge variant="outline">Initializing</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center text-muted-foreground">
            Synchronizing with universal harmonics...
          </div>
        </CardContent>
      </Card>
    );
  }

  const getSurgeColor = (type: SurgeEvent['type']) => {
    switch (type) {
      case 'prime_lock': return 'bg-green-500';
      case 'constructive': return 'bg-blue-500';
      case 'destructive': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <Card className={`${className} ${isActive ? 'animate-pulse' : ''}`}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          🔮 Harmonic Nexus Core
          <Badge variant={tick.score > 75 ? "default" : "secondary"}>
            {tick.score}/100
          </Badge>
          <Badge variant="outline" className="text-xs">
            μs: {tick.updatedAtMicros.toString().slice(-6)}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Core Metrics */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-sm font-medium">Schumann Lock</div>
            <Progress value={tick.schumann_lock * 100} className="h-2" />
            <div className="text-xs text-muted-foreground">
              {(tick.schumann_lock * 100).toFixed(1)}%
            </div>
          </div>
          <div>
            <div className="text-sm font-medium">Prime Coherence</div>
            <Progress value={tick.prime_coherence * 100} className="h-2" />
            <div className="text-xs text-muted-foreground">
              {(tick.prime_coherence * 100).toFixed(1)}%
            </div>
          </div>
        </div>

        {/* Band Coherence */}
        <div>
          <div className="text-sm font-medium mb-2">Harmonic Bands</div>
          <div className="grid grid-cols-5 gap-2">
            {Object.entries(tick.byBand).map(([band, coherence]) => (
              <div key={band} className="text-center">
                <div className="text-xs font-mono">{band}Hz</div>
                <Progress value={coherence * 100} className="h-1" />
                <div className="text-xs text-muted-foreground">
                  {(coherence * 100).toFixed(0)}%
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Drivers */}
        <div>
          <div className="text-sm font-medium mb-2">Active Drivers</div>
          <div className="flex flex-wrap gap-2">
            {tick.drivers.map((driver, i) => (
              <Badge key={i} variant="outline" className="text-xs">
                {driver.label}
                {driver.frequency && (
                  <span className="ml-1 text-muted-foreground">
                    {driver.frequency.toFixed(1)}Hz
                  </span>
                )}
              </Badge>
            ))}
          </div>
        </div>

        {/* Surge Events */}
        {tick.surge_events.length > 0 && (
          <div>
            <div className="text-sm font-medium mb-2">Recent Surges</div>
            <div className="flex flex-wrap gap-1">
              {tick.surge_events.slice(-5).map((surge, i) => (
                <div
                  key={i}
                  className={`w-2 h-2 rounded-full ${getSurgeColor(surge.type)}`}
                  title={`${surge.type} - ${surge.frequency.toFixed(1)}Hz`}
                />
              ))}
            </div>
          </div>
        )}

        {/* Phase Edges */}
        <div className="text-xs text-muted-foreground">
          Edges: {tick.edges.length} active • 
          Last update: {new Date(tick.updatedAt).toLocaleTimeString()}
        </div>
      </CardContent>
    </Card>
  );
};

export default HarmonicNexusCoreDisplay;