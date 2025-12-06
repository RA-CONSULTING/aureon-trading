import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Layers, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { useEcosystemData } from '@/hooks/useEcosystemData';
import { cn } from '@/lib/utils';

interface DataStream {
  name: string;
  value: number;
  weight: number;
  status: 'valid' | 'suspect' | 'invalid' | 'loading';
}

export function ProbabilityReconstructionPanel() {
  const { metrics } = useEcosystemData();
  const [streams, setStreams] = useState<DataStream[]>([
    { name: '6D Harmonic', value: 0.5, weight: 0.35, status: 'loading' },
    { name: 'HNC Signal', value: 0.5, weight: 0.35, status: 'loading' },
    { name: 'Lighthouse', value: 0.5, weight: 0.30, status: 'loading' },
  ]);
  const [fusedValue, setFusedValue] = useState(0.5);
  const [variance, setVariance] = useState(0);
  const [reconstructionStatus, setReconstructionStatus] = useState<'valid' | 'suspect' | 'invalid'>('suspect');
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    if (!metrics) return;

    // Simulate reconstruction animation
    setIsAnimating(true);
    
    const timer = setTimeout(() => {
      const harmonic6D = metrics.harmonicFidelity ?? 0.5;
      const hncSignal = metrics.coherence ?? 0.5;
      const lighthouse = metrics.consensusConfidence ?? 0.5;
      
      // Calculate weighted fusion
      const fused = harmonic6D * 0.35 + hncSignal * 0.35 + lighthouse * 0.30;
      
      // Calculate variance (how much sources disagree)
      const values = [harmonic6D, hncSignal, lighthouse];
      const mean = values.reduce((a, b) => a + b, 0) / values.length;
      const variance = values.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / values.length;
      
      // Determine status based on variance
      let status: 'valid' | 'suspect' | 'invalid' = 'valid';
      if (variance > 0.1) status = 'invalid';
      else if (variance > 0.03) status = 'suspect';
      
      setStreams([
        { name: '6D Harmonic', value: harmonic6D, weight: 0.35, status: harmonic6D > 0.3 ? 'valid' : 'suspect' },
        { name: 'HNC Signal', value: hncSignal, weight: 0.35, status: hncSignal > 0.3 ? 'valid' : 'suspect' },
        { name: 'Lighthouse', value: lighthouse, weight: 0.30, status: lighthouse > 0.3 ? 'valid' : 'suspect' },
      ]);
      setFusedValue(fused);
      setVariance(variance);
      setReconstructionStatus(status);
      setIsAnimating(false);
    }, 300);

    return () => clearTimeout(timer);
  }, [metrics]);

  const getStatusIcon = (status: DataStream['status']) => {
    switch (status) {
      case 'valid':
        return <CheckCircle2 className="h-3 w-3 text-green-400" />;
      case 'suspect':
        return <AlertCircle className="h-3 w-3 text-yellow-400" />;
      case 'invalid':
        return <AlertCircle className="h-3 w-3 text-red-400" />;
      default:
        return <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />;
    }
  };

  const getReconstructionBadge = () => {
    if (isAnimating) {
      return <Badge variant="outline" className="gap-1"><Loader2 className="h-3 w-3 animate-spin" /> RECONSTRUCTING</Badge>;
    }
    switch (reconstructionStatus) {
      case 'valid':
        return <Badge className="bg-green-500/20 text-green-400 border-green-500/30 gap-1"><CheckCircle2 className="h-3 w-3" /> VALIDATED</Badge>;
      case 'suspect':
        return <Badge className="bg-yellow-500/20 text-yellow-400 border-yellow-500/30 gap-1"><AlertCircle className="h-3 w-3" /> SUSPECT</Badge>;
      default:
        return <Badge className="bg-red-500/20 text-red-400 border-red-500/30 gap-1"><AlertCircle className="h-3 w-3" /> DIVERGENT</Badge>;
    }
  };

  return (
    <Card className="border-border/50">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-xs font-medium text-muted-foreground flex items-center gap-2">
            <Layers className="h-3 w-3" />
            PROBABILITY RECONSTRUCTION
          </CardTitle>
          {getReconstructionBadge()}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Input Streams */}
        <div className="space-y-2">
          <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Input Streams</p>
          {streams.map((stream, i) => (
            <div key={stream.name} className="space-y-1">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {getStatusIcon(stream.status)}
                  <span className="text-xs">{stream.name}</span>
                  <span className="text-[10px] text-muted-foreground">({(stream.weight * 100).toFixed(0)}%)</span>
                </div>
                <span className="text-xs font-mono">{stream.value.toFixed(3)}</span>
              </div>
              <Progress 
                value={stream.value * 100} 
                className={cn(
                  "h-1",
                  stream.status === 'valid' && "[&>div]:bg-green-500",
                  stream.status === 'suspect' && "[&>div]:bg-yellow-500",
                  stream.status === 'invalid' && "[&>div]:bg-red-500"
                )}
              />
            </div>
          ))}
        </div>

        {/* Fusion Arrow */}
        <div className="flex items-center justify-center py-2">
          <div className={cn(
            "flex items-center gap-2 px-3 py-1 rounded-full border",
            isAnimating && "animate-pulse",
            reconstructionStatus === 'valid' && "border-green-500/30 bg-green-500/10",
            reconstructionStatus === 'suspect' && "border-yellow-500/30 bg-yellow-500/10",
            reconstructionStatus === 'invalid' && "border-red-500/30 bg-red-500/10"
          )}>
            <span className="text-[10px] text-muted-foreground">MATRIX FUSION</span>
            <span className="text-lg">→</span>
          </div>
        </div>

        {/* Fused Output */}
        <div className="p-3 rounded-lg bg-muted/30 border border-border/50">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-muted-foreground">Reconstructed Probability</span>
            <span className={cn(
              "text-lg font-mono font-bold",
              fusedValue > 0.6 ? "text-green-400" : fusedValue > 0.4 ? "text-yellow-400" : "text-red-400"
            )}>
              {(fusedValue * 100).toFixed(1)}%
            </span>
          </div>
          <Progress 
            value={fusedValue * 100} 
            className={cn(
              "h-2",
              fusedValue > 0.6 && "[&>div]:bg-gradient-to-r [&>div]:from-green-600 [&>div]:to-green-400",
              fusedValue <= 0.6 && fusedValue > 0.4 && "[&>div]:bg-gradient-to-r [&>div]:from-yellow-600 [&>div]:to-yellow-400",
              fusedValue <= 0.4 && "[&>div]:bg-gradient-to-r [&>div]:from-red-600 [&>div]:to-red-400"
            )}
          />
          <div className="flex justify-between mt-2 text-[10px] text-muted-foreground">
            <span>Variance: {variance.toFixed(4)}</span>
            <span>Consensus: {variance < 0.03 ? 'STRONG' : variance < 0.1 ? 'WEAK' : 'NONE'}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
