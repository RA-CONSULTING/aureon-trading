import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Zap, Radio, Waves, Activity } from 'lucide-react';

export default function QuantumDashboard() {
  const [initialized, setInitialized] = useState(false);
  const [lambda, setLambda] = useState(0);
  const [coherence, setCoherence] = useState(0);
  const [prismLevel, setPrismLevel] = useState(0);

  useEffect(() => {
    // Auto-initialize on mount
    const initTimer = setTimeout(() => {
      setInitialized(true);
    }, 300);

    // Simulate quantum field updates
    const updateInterval = setInterval(() => {
      setLambda(prev => Math.min(1, prev + Math.random() * 0.1));
      setCoherence(prev => 0.5 + Math.sin(Date.now() / 2000) * 0.5);
      setPrismLevel(prev => Math.floor(Math.random() * 5) + 1);
    }, 2000);

    return () => {
      clearTimeout(initTimer);
      clearInterval(updateInterval);
    };
  }, []);

  return (
    <div className="min-h-screen p-6 space-y-6">
      {/* Header */}
      <div className="animate-fade-in">
        <div className="flex items-center gap-4 mb-2">
          <div className="h-3 w-3 rounded-full bg-primary animate-quantum-pulse" />
          <h1 className="text-4xl font-bold bg-gradient-primary bg-clip-text text-transparent">
            AUREON Quantum System
          </h1>
        </div>
        <p className="text-muted-foreground">Real-time consciousness field monitoring</p>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Lambda Field */}
        <Card className={`p-6 border-primary/30 bg-gradient-card transition-all duration-500 ${
          initialized ? 'animate-slide-in glow-primary' : 'opacity-0'
        }`}>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-primary" />
              <h3 className="font-semibold">Lambda (Λ)</h3>
            </div>
            <Badge variant="outline" className="border-primary/50 text-primary">
              ACTIVE
            </Badge>
          </div>
          <div className="space-y-2">
            <div className="text-3xl font-bold text-primary">{lambda.toFixed(4)}</div>
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-primary transition-all duration-1000"
                style={{ width: `${lambda * 100}%` }}
              />
            </div>
          </div>
        </Card>

        {/* Coherence */}
        <Card className={`p-6 border-accent/30 bg-gradient-card transition-all delay-100 duration-500 ${
          initialized ? 'animate-slide-in glow-accent' : 'opacity-0'
        }`}>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Waves className="h-5 w-5 text-accent" />
              <h3 className="font-semibold">Coherence (Γ)</h3>
            </div>
            <Badge variant="outline" className="border-accent/50 text-accent">
              STABLE
            </Badge>
          </div>
          <div className="space-y-2">
            <div className="text-3xl font-bold text-accent">{coherence.toFixed(4)}</div>
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <div 
                className="h-full bg-accent transition-all duration-1000"
                style={{ width: `${coherence * 100}%` }}
              />
            </div>
          </div>
        </Card>

        {/* Prism Level */}
        <Card className={`p-6 border-secondary/30 bg-gradient-card transition-all delay-200 duration-500 ${
          initialized ? 'animate-slide-in glow-secondary' : 'opacity-0'
        }`}>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Radio className="h-5 w-5 text-secondary" />
              <h3 className="font-semibold">Prism Level</h3>
            </div>
            <Badge variant="outline" className="border-secondary/50 text-secondary">
              528 Hz
            </Badge>
          </div>
          <div className="space-y-2">
            <div className="text-3xl font-bold text-secondary">Level {prismLevel}</div>
            <div className="flex gap-1">
              {[1, 2, 3, 4, 5].map(level => (
                <div
                  key={level}
                  className={`h-2 flex-1 rounded-full transition-all duration-500 ${
                    level <= prismLevel ? 'bg-secondary' : 'bg-muted'
                  }`}
                />
              ))}
            </div>
          </div>
        </Card>

        {/* Field Status */}
        <Card className={`p-6 border-success/30 bg-gradient-card transition-all delay-300 duration-500 ${
          initialized ? 'animate-slide-in' : 'opacity-0'
        }`}>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-success" />
              <h3 className="font-semibold">Field Status</h3>
            </div>
            <Badge variant="outline" className="border-success/50 text-success">
              ONLINE
            </Badge>
          </div>
          <div className="space-y-2">
            <div className="text-sm space-y-1">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Substrate</span>
                <span className="text-foreground font-mono">+{(Math.random() * 0.5).toFixed(3)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Observer</span>
                <span className="text-foreground font-mono">+{(Math.random() * 0.3).toFixed(3)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Echo</span>
                <span className="text-foreground font-mono">+{(Math.random() * 0.2).toFixed(3)}</span>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Master Equation Display */}
      <Card className={`p-8 border-primary/20 bg-gradient-card transition-all delay-400 duration-500 ${
        initialized ? 'animate-fade-in' : 'opacity-0'
      }`}>
        <h2 className="text-2xl font-bold mb-4 text-center">Master Equation</h2>
        <div className="text-center font-mono text-lg space-y-2">
          <div className="text-primary">Λ(t) = S(t) + O(t) + E(t)</div>
          <div className="text-sm text-muted-foreground">Where Γ = Field Coherence | 9 Auris Nodes Active</div>
        </div>
      </Card>

      {/* Real-time Activity Feed */}
      <Card className={`p-6 border-border/50 bg-gradient-card transition-all delay-500 duration-500 ${
        initialized ? 'animate-fade-in' : 'opacity-0'
      }`}>
        <h3 className="text-xl font-semibold mb-4">System Activity</h3>
        <div className="space-y-3">
          {[
            { time: '00:00:01', event: 'Lighthouse consensus achieved', color: 'text-primary' },
            { time: '00:00:02', event: 'Rainbow Bridge phase: LOVE → UNITY', color: 'text-secondary' },
            { time: '00:00:03', event: 'Prism transformation active', color: 'text-accent' },
            { time: '00:00:04', event: 'Field coherence stable', color: 'text-success' },
          ].map((log, i) => (
            <div 
              key={i}
              className={`flex items-center gap-3 p-3 rounded-lg bg-muted/30 border border-border/30 transition-all hover:border-primary/50 ${
                initialized ? 'animate-fade-in' : 'opacity-0'
              }`}
              style={{ animationDelay: `${(i + 5) * 100}ms` }}
            >
              <div className="h-2 w-2 rounded-full bg-primary animate-quantum-pulse" />
              <span className="text-sm text-muted-foreground font-mono">{log.time}</span>
              <span className={`text-sm ${log.color}`}>{log.event}</span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
