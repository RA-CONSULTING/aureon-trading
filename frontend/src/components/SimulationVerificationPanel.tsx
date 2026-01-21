import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Play, 
  Pause, 
  Activity, 
  TrendingUp, 
  TrendingDown, 
  Target,
  Zap,
  Eye,
  CheckCircle,
  XCircle,
  AlertTriangle
} from 'lucide-react';
import { automatedSimulationEngine, SimulationStats, SimulationResult } from '@/core/automatedSimulationEngine';
import { temporalProbabilityEcho, TemporalEchoState, EchoMetrics } from '@/core/temporalProbabilityEcho';
import { lightPathTracer, LightPathStats, LightPathTrace } from '@/core/lightPathTracer';

export const SimulationVerificationPanel: React.FC = () => {
  const [simStats, setSimStats] = useState<SimulationStats>(automatedSimulationEngine.getStats());
  const [echoState, setEchoState] = useState<TemporalEchoState>(temporalProbabilityEcho.getState());
  const [pathStats, setPathStats] = useState<LightPathStats>(lightPathTracer.getStats());
  const [recentResults, setRecentResults] = useState<SimulationResult[]>([]);
  const [recentTraces, setRecentTraces] = useState<LightPathTrace[]>([]);

  useEffect(() => {
    const unsubSim = automatedSimulationEngine.subscribe(stats => {
      setSimStats(stats);
      setRecentResults(automatedSimulationEngine.getRecentResults(5));
    });
    
    const unsubEcho = temporalProbabilityEcho.subscribe(state => {
      setEchoState(state);
    });
    
    const unsubPath = lightPathTracer.subscribe(traces => {
      setPathStats(lightPathTracer.getStats());
      setRecentTraces(traces.slice(-5));
    });

    // Initial load
    setRecentResults(automatedSimulationEngine.getRecentResults(5));
    setRecentTraces(lightPathTracer.getRecentTraces(5));

    return () => {
      unsubSim();
      unsubEcho();
      unsubPath();
    };
  }, []);

  const handleToggleSimulation = () => {
    if (simStats.isRunning) {
      automatedSimulationEngine.stop();
    } else {
      automatedSimulationEngine.start(3000);
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'BULLISH': return <TrendingUp className="h-4 w-4 text-green-400" />;
      case 'BEARISH': return <TrendingDown className="h-4 w-4 text-red-400" />;
      default: return <Activity className="h-4 w-4 text-yellow-400" />;
    }
  };

  const getActionColor = (action: string) => {
    switch (action) {
      case 'BUY': return 'bg-green-500/20 text-green-400 border-green-500/30';
      case 'SELL': return 'bg-red-500/20 text-red-400 border-red-500/30';
      default: return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
    }
  };

  return (
    <Card className="bg-background/40 backdrop-blur-sm border-primary/20">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Eye className="h-4 w-4 text-primary" />
            Simulation Verification
          </CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant={simStats.isRunning ? "default" : "secondary"} className="text-xs">
              {simStats.isRunning ? 'RUNNING' : 'STOPPED'}
            </Badge>
            <Button 
              size="sm" 
              variant="outline" 
              onClick={handleToggleSimulation}
              className="h-7 px-2"
            >
              {simStats.isRunning ? <Pause className="h-3 w-3" /> : <Play className="h-3 w-3" />}
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <Tabs defaultValue="overview" className="w-full">
          <TabsList className="grid w-full grid-cols-4 h-8">
            <TabsTrigger value="overview" className="text-xs">Overview</TabsTrigger>
            <TabsTrigger value="lightpath" className="text-xs">Light Path</TabsTrigger>
            <TabsTrigger value="temporal" className="text-xs">Temporal</TabsTrigger>
            <TabsTrigger value="results" className="text-xs">Results</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-3 mt-3">
            {/* Stats Grid */}
            <div className="grid grid-cols-4 gap-2">
              <div className="bg-muted/30 rounded p-2 text-center">
                <div className="text-lg font-bold text-primary">{simStats.totalSimulations}</div>
                <div className="text-xs text-muted-foreground">Simulations</div>
              </div>
              <div className="bg-muted/30 rounded p-2 text-center">
                <div className="text-lg font-bold text-green-400">{(simStats.accuracy * 100).toFixed(1)}%</div>
                <div className="text-xs text-muted-foreground">Accuracy</div>
              </div>
              <div className="bg-muted/30 rounded p-2 text-center">
                <div className="text-lg font-bold text-cyan-400">{simStats.avgPrismFrequency.toFixed(0)} Hz</div>
                <div className="text-xs text-muted-foreground">Avg Freq</div>
              </div>
              <div className="bg-muted/30 rounded p-2 text-center">
                <div className="text-lg font-bold text-yellow-400">{(simStats.dataValidationRate * 100).toFixed(0)}%</div>
                <div className="text-xs text-muted-foreground">Valid Data</div>
              </div>
            </div>

            {/* Action Distribution */}
            <div className="bg-muted/20 rounded p-2">
              <div className="text-xs text-muted-foreground mb-2">Action Distribution</div>
              <div className="flex gap-2">
                <div className="flex-1 bg-green-500/20 rounded p-1 text-center">
                  <div className="text-sm font-bold text-green-400">{simStats.actionDistribution.BUY}</div>
                  <div className="text-xs text-green-400/70">BUY</div>
                </div>
                <div className="flex-1 bg-yellow-500/20 rounded p-1 text-center">
                  <div className="text-sm font-bold text-yellow-400">{simStats.actionDistribution.HOLD}</div>
                  <div className="text-xs text-yellow-400/70">HOLD</div>
                </div>
                <div className="flex-1 bg-red-500/20 rounded p-1 text-center">
                  <div className="text-sm font-bold text-red-400">{simStats.actionDistribution.SELL}</div>
                  <div className="text-xs text-red-400/70">SELL</div>
                </div>
              </div>
            </div>

            {/* Confidence Gauge */}
            <div className="bg-muted/20 rounded p-2">
              <div className="flex justify-between text-xs mb-1">
                <span className="text-muted-foreground">Avg Confidence</span>
                <span className="text-primary">{(simStats.avgConfidence * 100).toFixed(1)}%</span>
              </div>
              <Progress value={simStats.avgConfidence * 100} className="h-2" />
            </div>
          </TabsContent>

          <TabsContent value="lightpath" className="space-y-3 mt-3">
            {/* Path Stats */}
            <div className="grid grid-cols-3 gap-2">
              <div className="bg-muted/30 rounded p-2 text-center">
                <div className="text-sm font-bold text-primary">{pathStats.totalTraces}</div>
                <div className="text-xs text-muted-foreground">Traces</div>
              </div>
              <div className="bg-muted/30 rounded p-2 text-center">
                <div className="text-sm font-bold text-cyan-400">{(pathStats.avgAlignmentScore * 100).toFixed(0)}%</div>
                <div className="text-xs text-muted-foreground">Alignment</div>
              </div>
              <div className="bg-muted/30 rounded p-2 text-center">
                <div className="text-sm font-bold text-green-400">{(pathStats.successRate * 100).toFixed(0)}%</div>
                <div className="text-xs text-muted-foreground">Success</div>
              </div>
            </div>

            {/* Component Health */}
            <div className="bg-muted/20 rounded p-2 space-y-1">
              <div className="text-xs text-muted-foreground mb-2">Component Health</div>
              {Object.entries(pathStats.componentHealth).map(([component, health]) => (
                <div key={component} className="flex items-center justify-between text-xs">
                  <span className="text-foreground/70">{component}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-muted-foreground">{health.avgLatency.toFixed(0)}ms</span>
                    <Badge 
                      variant={health.successRate > 0.9 ? "default" : health.successRate > 0.7 ? "secondary" : "destructive"}
                      className="text-xs px-1"
                    >
                      {(health.successRate * 100).toFixed(0)}%
                    </Badge>
                  </div>
                </div>
              ))}
            </div>

            {/* Recent Traces */}
            <div className="bg-muted/20 rounded p-2 max-h-32 overflow-y-auto">
              <div className="text-xs text-muted-foreground mb-2">Recent Traces</div>
              {recentTraces.map((trace, idx) => (
                <div key={trace.traceId} className="flex items-center justify-between text-xs py-1 border-b border-border/20 last:border-0">
                  <div className="flex items-center gap-2">
                    {trace.isValid ? 
                      <CheckCircle className="h-3 w-3 text-green-400" /> : 
                      <XCircle className="h-3 w-3 text-red-400" />
                    }
                    <span className="text-foreground/70">{trace.nodes.length} nodes</span>
                  </div>
                  <Badge className={`text-xs ${getActionColor(trace.outputAction)}`}>
                    {trace.outputAction}
                  </Badge>
                </div>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="temporal" className="space-y-3 mt-3">
            {/* Echo Metrics */}
            <div className="grid grid-cols-2 gap-2">
              <div className="bg-muted/30 rounded p-2">
                <div className="flex items-center gap-2 mb-1">
                  {getTrendIcon(echoState.metrics.trend)}
                  <span className="text-xs text-muted-foreground">Trend</span>
                </div>
                <div className="text-sm font-bold">{echoState.metrics.trend}</div>
                <Progress value={echoState.metrics.trendStrength * 100} className="h-1 mt-1" />
              </div>
              <div className="bg-muted/30 rounded p-2">
                <div className="flex items-center gap-2 mb-1">
                  <Zap className="h-3 w-3 text-yellow-400" />
                  <span className="text-xs text-muted-foreground">Momentum</span>
                </div>
                <div className="text-sm font-bold">{echoState.metrics.momentum.toFixed(3)}</div>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2">
              <div className="bg-muted/20 rounded p-2 text-center">
                <div className="text-sm font-bold text-cyan-400">{(echoState.metrics.convergence * 100).toFixed(0)}%</div>
                <div className="text-xs text-muted-foreground">Convergence</div>
              </div>
              <div className="bg-muted/20 rounded p-2 text-center">
                <div className="text-sm font-bold text-yellow-400">{(echoState.metrics.drift * 100).toFixed(0)}%</div>
                <div className="text-xs text-muted-foreground">Drift</div>
              </div>
              <div className="bg-muted/20 rounded p-2 text-center">
                <div className="text-sm font-bold text-purple-400">{echoState.metrics.echoCount}</div>
                <div className="text-xs text-muted-foreground">Echoes</div>
              </div>
            </div>

            {/* Steering Status */}
            <div className={`rounded p-2 flex items-center justify-between ${
              echoState.metrics.isSteeringCorrectly ? 'bg-green-500/10 border border-green-500/30' : 'bg-yellow-500/10 border border-yellow-500/30'
            }`}>
              <div className="flex items-center gap-2">
                {echoState.metrics.isSteeringCorrectly ? 
                  <CheckCircle className="h-4 w-4 text-green-400" /> :
                  <AlertTriangle className="h-4 w-4 text-yellow-400" />
                }
                <span className="text-sm font-medium">
                  {echoState.metrics.isSteeringCorrectly ? 'Matrix Steering Correctly' : 'Matrix Needs Calibration'}
                </span>
              </div>
              <Badge variant={echoState.metrics.isSteeringCorrectly ? "default" : "secondary"}>
                {(echoState.metrics.temporalPosition * 100).toFixed(0)}% filled
              </Badge>
            </div>

            {/* Temporal Position Bar */}
            <div className="bg-muted/20 rounded p-2">
              <div className="text-xs text-muted-foreground mb-1">Temporal Position</div>
              <div className="relative h-4 bg-muted/30 rounded overflow-hidden">
                <div 
                  className="absolute left-0 top-0 h-full bg-gradient-to-r from-purple-500 to-cyan-500"
                  style={{ width: `${echoState.metrics.temporalPosition * 100}%` }}
                />
                <div className="absolute inset-0 flex items-center justify-center text-xs font-bold">
                  {echoState.metrics.echoCount} / 100
                </div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="results" className="space-y-2 mt-3">
            {/* Recent Simulation Results */}
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {recentResults.length === 0 ? (
                <div className="text-xs text-muted-foreground text-center py-4">
                  No simulation results yet. Start simulation to see results.
                </div>
              ) : (
                recentResults.map((result, idx) => (
                  <div key={result.simulationId} className="bg-muted/20 rounded p-2 space-y-1">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge className={`text-xs ${getActionColor(result.predictedAction)}`}>
                          {result.predictedAction}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {(result.predictedConfidence * 100).toFixed(0)}% conf
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        {result.dataValidation.isValid ? 
                          <CheckCircle className="h-3 w-3 text-green-400" /> :
                          <XCircle className="h-3 w-3 text-red-400" />
                        }
                        <span className="text-xs text-primary">{result.prismFrequency.toFixed(0)} Hz</span>
                      </div>
                    </div>
                    <div className="flex gap-1 text-xs">
                      <span className="text-blue-400">6D: {(result.probabilityMatrix.sixD * 100).toFixed(0)}%</span>
                      <span className="text-purple-400">HNC: {(result.probabilityMatrix.hnc * 100).toFixed(0)}%</span>
                      <span className="text-cyan-400">LH: {(result.probabilityMatrix.lighthouse * 100).toFixed(0)}%</span>
                      <span className="text-green-400">→ {(result.probabilityMatrix.fused * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};
