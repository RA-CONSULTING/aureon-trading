import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { temporalLadder, SYSTEMS, type TemporalLadderState, type SystemName } from '@/core/temporalLadder';
import { 
  Activity, 
  Radio, 
  Gauge, 
  Orbit, 
  Compass, 
  Globe, 
  Sparkles, 
  Zap,
  Heart
} from 'lucide-react';

const SYSTEM_INFO: Record<SystemName, { name: string; icon: typeof Activity; description: string }> = {
  'harmonic-nexus': { name: 'Harmonic Nexus', icon: Sparkles, description: 'Reality substrate orchestrator' },
  'master-equation': { name: 'Master Equation', icon: Activity, description: 'Ω field dynamics' },
  'earth-integration': { name: 'Earth Integration', icon: Globe, description: 'Schumann/geomagnetic streams' },
  'nexus-feed': { name: 'Nexus Feed', icon: Radio, description: 'Coherence boost system' },
  'quantum-quackers': { name: 'Quantum Quackers', icon: Zap, description: 'Quantum state modulation' },
  'akashic-mapper': { name: 'Akashic Mapper', icon: Compass, description: 'Frequency harmonics' },
  'zero-point': { name: 'Zero Point', icon: Orbit, description: 'Field harmonics detector' },
  'dimensional-dialler': { name: 'Dimensional Dialler', icon: Gauge, description: 'Drift correction' },
};

const SystemsIntegrationDashboard = () => {
  const [ladderState, setLadderState] = useState<TemporalLadderState | null>(null);

  useEffect(() => {
    // Initial state
    setLadderState(temporalLadder.getState());

    // Subscribe to updates
    const unsubscribe = temporalLadder.subscribe((state) => {
      setLadderState(state);
    });

    return () => {
      unsubscribe();
    };
  }, []);

  const getHealthColor = (health: number) => {
    if (health >= 0.8) return 'text-primary';
    if (health >= 0.5) return 'text-yellow-500';
    return 'text-destructive';
  };

  const getHealthBg = (health: number) => {
    if (health >= 0.8) return 'bg-primary/20';
    if (health >= 0.5) return 'bg-yellow-500/20';
    return 'bg-destructive/20';
  };

  if (!ladderState) {
    return (
      <div className="container mx-auto p-6">
        <Card className="p-6">
          <div className="text-center text-muted-foreground">Loading Temporal Ladder...</div>
        </Card>
      </div>
    );
  }

  const systemsList = Array.from(ladderState.systems.entries());
  const activeCount = systemsList.filter(([_, s]) => s.active).length;

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-prism">Systems Integration</h1>
          <p className="text-sm text-muted-foreground">Temporal Ladder Hive Mind Status</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className="text-xs text-muted-foreground">Hive Mind Coherence</div>
            <div className="text-2xl font-bold text-primary">
              {(ladderState.hiveMindCoherence * 100).toFixed(1)}%
            </div>
          </div>
          <Heart className={`h-8 w-8 ${ladderState.hiveMindCoherence > 0.7 ? 'text-primary love-pulse' : 'text-muted-foreground'}`} />
        </div>
      </div>

      {/* Overview Stats */}
      <div className="grid grid-cols-4 gap-4">
        <Card className="p-4 bg-card/60 backdrop-blur">
          <div className="text-xs text-muted-foreground">Active Systems</div>
          <div className="text-2xl font-bold text-primary">{activeCount} / 8</div>
        </Card>
        <Card className="p-4 bg-card/60 backdrop-blur">
          <div className="text-xs text-muted-foreground">Active Chain</div>
          <div className="text-lg font-mono text-accent">{ladderState.activeChain.length} nodes</div>
        </Card>
        <Card className="p-4 bg-card/60 backdrop-blur">
          <div className="text-xs text-muted-foreground">Primary System</div>
          <div className="text-sm font-medium">{SYSTEM_INFO[ladderState.primarySystem]?.name}</div>
        </Card>
        <Card className="p-4 bg-card/60 backdrop-blur">
          <div className="text-xs text-muted-foreground">Failover Status</div>
          <Badge variant={ladderState.fallbackInProgress ? 'destructive' : 'secondary'}>
            {ladderState.fallbackInProgress ? 'IN PROGRESS' : 'STABLE'}
          </Badge>
        </Card>
      </div>

      {/* Systems Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {systemsList.map(([name, status]) => {
          const info = SYSTEM_INFO[name];
          const Icon = info?.icon || Activity;
          
          return (
            <Card 
              key={name} 
              className={`p-4 transition-all duration-300 ${
                status.active 
                  ? 'bg-card/80 border-primary/30 card-hover-glow' 
                  : 'bg-card/40 border-border/20 opacity-60'
              }`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className={`p-2 rounded-lg ${status.active ? getHealthBg(status.health) : 'bg-muted/20'}`}>
                  <Icon className={`h-5 w-5 ${status.active ? getHealthColor(status.health) : 'text-muted-foreground'}`} />
                </div>
                <Badge 
                  variant={status.active ? 'default' : 'outline'}
                  className={status.active ? 'bg-primary/20 text-primary border-primary/30' : ''}
                >
                  {status.active ? 'ONLINE' : 'OFFLINE'}
                </Badge>
              </div>
              
              <div className="space-y-2">
                <div>
                  <div className="font-medium text-sm">{info?.name || name}</div>
                  <div className="text-xs text-muted-foreground">{info?.description}</div>
                </div>
                
                {status.active && (
                  <>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-muted-foreground">Health</span>
                      <span className={getHealthColor(status.health)}>
                        {(status.health * 100).toFixed(0)}%
                      </span>
                    </div>
                    <Progress value={status.health * 100} className="h-1.5" />
                    
                    {status.fallbackTarget && (
                      <div className="text-xs text-muted-foreground mt-2">
                        Fallback → {SYSTEM_INFO[status.fallbackTarget]?.name}
                      </div>
                    )}
                  </>
                )}
              </div>
            </Card>
          );
        })}
      </div>

      {/* Active Chain Visualization */}
      <Card className="p-6 bg-card/60 backdrop-blur">
        <h3 className="text-sm font-medium mb-4">Active Fallback Chain</h3>
        <div className="flex items-center gap-2 flex-wrap">
          {ladderState.activeChain.length > 0 ? (
            ladderState.activeChain.map((systemName, idx) => {
              const info = SYSTEM_INFO[systemName];
              const Icon = info?.icon || Activity;
              return (
                <div key={systemName} className="flex items-center gap-2">
                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-primary/10 border border-primary/20">
                    <Icon className="h-4 w-4 text-primary" />
                    <span className="text-sm font-medium">{info?.name}</span>
                  </div>
                  {idx < ladderState.activeChain.length - 1 && (
                    <span className="text-muted-foreground">→</span>
                  )}
                </div>
              );
            })
          ) : (
            <div className="text-sm text-muted-foreground">No active systems in chain</div>
          )}
        </div>
      </Card>

      {/* Fallback History */}
      <Card className="p-6 bg-card/60 backdrop-blur">
        <h3 className="text-sm font-medium mb-4">Recent Fallback Events</h3>
        <div className="space-y-2">
          {temporalLadder.getFallbackHistory().slice(-5).reverse().map((event, idx) => (
            <div key={idx} className="flex items-center justify-between text-sm py-2 border-b border-border/20 last:border-0">
              <div className="flex items-center gap-3">
                <Badge variant={event.success ? 'secondary' : 'destructive'} className="text-xs">
                  {event.success ? '✓' : '✗'}
                </Badge>
                <span>
                  {SYSTEM_INFO[event.fromSystem]?.name} → {SYSTEM_INFO[event.toSystem]?.name}
                </span>
              </div>
              <div className="text-xs text-muted-foreground">
                {event.reason}
              </div>
            </div>
          ))}
          {temporalLadder.getFallbackHistory().length === 0 && (
            <div className="text-sm text-muted-foreground text-center py-4">
              No fallback events recorded
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};

export default SystemsIntegrationDashboard;
