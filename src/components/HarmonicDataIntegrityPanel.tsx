import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Shield, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';
import { useEcosystemData } from '@/hooks/useEcosystemData';
import { cn } from '@/lib/utils';

interface IntegrityMetric {
  name: string;
  score: number;
  weight: number;
  description: string;
}

export function HarmonicDataIntegrityPanel() {
  const { metrics } = useEcosystemData();
  const [overallScore, setOverallScore] = useState(0);
  const [status, setStatus] = useState<'valid' | 'suspect' | 'invalid'>('suspect');
  const [integrityMetrics, setIntegrityMetrics] = useState<IntegrityMetric[]>([]);
  const [history, setHistory] = useState<number[]>([]);

  useEffect(() => {
    if (!metrics) return;

    // Calculate integrity metrics
    const cymaticsMatch = Math.min(1, (metrics.coherence ?? 0.5) * 1.2);
    const prismAlignment = metrics.frequency 
      ? 1 - Math.abs(528 - (metrics.frequency ?? 396)) / 528
      : 0.5;
    const matrixConsensus = 1 - (metrics.harmonicFidelity 
      ? Math.abs((metrics.harmonicFidelity ?? 0.5) - (metrics.coherence ?? 0.5))
      : 0.3);
    const temporalSync = metrics.temporalAnchorStrength ?? 0.5;

    const metricsArray: IntegrityMetric[] = [
      { name: 'Cymatics Pattern Match', score: cymaticsMatch, weight: 0.25, description: 'Water frequency resonance alignment' },
      { name: 'Prism Alignment', score: prismAlignment, weight: 0.30, description: 'Distance to 528 Hz love frequency' },
      { name: 'Matrix Consensus', score: matrixConsensus, weight: 0.25, description: 'Source agreement level' },
      { name: 'Temporal Sync', score: temporalSync, weight: 0.20, description: 'Timeline coherence quality' },
    ];

    // Calculate weighted overall score
    const overall = metricsArray.reduce((sum, m) => sum + m.score * m.weight, 0);
    
    // Determine status
    let newStatus: 'valid' | 'suspect' | 'invalid' = 'valid';
    if (overall < 0.4) newStatus = 'invalid';
    else if (overall < 0.7) newStatus = 'suspect';

    setIntegrityMetrics(metricsArray);
    setOverallScore(overall);
    setStatus(newStatus);
    
    // Update history (keep last 20 values)
    setHistory(prev => [...prev.slice(-19), overall]);
  }, [metrics]);

  const getStatusIcon = () => {
    switch (status) {
      case 'valid':
        return <CheckCircle2 className="h-4 w-4 text-green-400" />;
      case 'suspect':
        return <AlertTriangle className="h-4 w-4 text-yellow-400" />;
      default:
        return <XCircle className="h-4 w-4 text-red-400" />;
    }
  };

  const getStatusBadge = () => {
    switch (status) {
      case 'valid':
        return <Badge className="bg-green-500/20 text-green-400 border-green-500/30">🟢 VALID</Badge>;
      case 'suspect':
        return <Badge className="bg-yellow-500/20 text-yellow-400 border-yellow-500/30">🟡 SUSPECT</Badge>;
      default:
        return <Badge className="bg-red-500/20 text-red-400 border-red-500/30">🔴 INVALID</Badge>;
    }
  };

  return (
    <Card className="border-border/50">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-xs font-medium text-muted-foreground flex items-center gap-2">
            <Shield className="h-3 w-3" />
            HARMONIC DATA INTEGRITY
          </CardTitle>
          {getStatusBadge()}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Overall Score */}
        <div className="flex items-center gap-4 p-3 rounded-lg bg-muted/30 border border-border/50">
          {getStatusIcon()}
          <div className="flex-1">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-muted-foreground">Overall Integrity</span>
              <span className={cn(
                "text-xl font-mono font-bold",
                status === 'valid' && "text-green-400",
                status === 'suspect' && "text-yellow-400",
                status === 'invalid' && "text-red-400"
              )}>
                {(overallScore * 100).toFixed(0)}%
              </span>
            </div>
            <Progress 
              value={overallScore * 100} 
              className={cn(
                "h-2",
                status === 'valid' && "[&>div]:bg-green-500",
                status === 'suspect' && "[&>div]:bg-yellow-500",
                status === 'invalid' && "[&>div]:bg-red-500"
              )}
            />
          </div>
        </div>

        {/* Metric Breakdown */}
        <div className="space-y-2">
          <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Breakdown</p>
          {integrityMetrics.map((metric) => (
            <div key={metric.name} className="space-y-1">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs">{metric.name}</span>
                  <span className="text-[10px] text-muted-foreground ml-1">({(metric.weight * 100).toFixed(0)}%)</span>
                </div>
                <span className={cn(
                  "text-xs font-mono",
                  metric.score > 0.7 && "text-green-400",
                  metric.score <= 0.7 && metric.score > 0.4 && "text-yellow-400",
                  metric.score <= 0.4 && "text-red-400"
                )}>
                  {(metric.score * 100).toFixed(0)}%
                </span>
              </div>
              <Progress 
                value={metric.score * 100} 
                className={cn(
                  "h-1",
                  metric.score > 0.7 && "[&>div]:bg-green-500/60",
                  metric.score <= 0.7 && metric.score > 0.4 && "[&>div]:bg-yellow-500/60",
                  metric.score <= 0.4 && "[&>div]:bg-red-500/60"
                )}
              />
            </div>
          ))}
        </div>

        {/* Mini History Chart */}
        <div className="space-y-1">
          <p className="text-[10px] text-muted-foreground uppercase tracking-wider">History (last 20 ticks)</p>
          <div className="flex items-end gap-0.5 h-8">
            {history.map((value, i) => (
              <div
                key={i}
                className={cn(
                  "flex-1 rounded-t transition-all",
                  value > 0.7 && "bg-green-500/60",
                  value <= 0.7 && value > 0.4 && "bg-yellow-500/60",
                  value <= 0.4 && "bg-red-500/60"
                )}
                style={{ height: `${value * 100}%` }}
              />
            ))}
            {history.length === 0 && (
              <div className="w-full h-full flex items-center justify-center">
                <span className="text-[10px] text-muted-foreground">Collecting data...</span>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
