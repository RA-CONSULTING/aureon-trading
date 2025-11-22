import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useQGITASignals } from '@/hooks/useQGITASignals';
import { TrendingUp, TrendingDown, Minus, Activity, Zap } from 'lucide-react';

interface QGITASignalPanelProps {
  symbol: string;
}

export function QGITASignalPanel({ symbol }: QGITASignalPanelProps) {
  const { latestSignal, signals, stats } = useQGITASignals(symbol);
  
  if (!latestSignal) {
    return (
      <Card className="p-6">
        <div className="flex items-center gap-2 mb-4">
          <Activity className="w-5 h-5 text-primary" />
          <h3 className="font-semibold">QGITA Signal Engine</h3>
          <Badge variant="outline" className="ml-auto">Initializing...</Badge>
        </div>
        <p className="text-sm text-muted-foreground">
          Analyzing market geometry...
        </p>
      </Card>
    );
  }
  
  const getSignalColor = () => {
    if (latestSignal.signalType === 'BUY') return 'text-green-500';
    if (latestSignal.signalType === 'SELL') return 'text-red-500';
    return 'text-muted-foreground';
  };
  
  const getSignalIcon = () => {
    if (latestSignal.signalType === 'BUY') return <TrendingUp className="w-5 h-5" />;
    if (latestSignal.signalType === 'SELL') return <TrendingDown className="w-5 h-5" />;
    return <Minus className="w-5 h-5" />;
  };
  
  const getTierBadge = () => {
    const tierColors = {
      1: 'bg-green-500 text-white',
      2: 'bg-yellow-500 text-white',
      3: 'bg-gray-500 text-white',
    };
    const tierLabels = {
      1: 'Full Position',
      2: 'Half Position',
      3: 'No Trade',
    };
    return (
      <Badge className={tierColors[latestSignal.tier]}>
        Tier {latestSignal.tier}: {tierLabels[latestSignal.tier]}
      </Badge>
    );
  };
  
  return (
    <Card className="p-6">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-primary" />
            <h3 className="font-semibold">QGITA Signal Engine</h3>
          </div>
          {getTierBadge()}
        </div>
        
        {/* Main Signal */}
        <div className="bg-card border rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <div className={`flex items-center gap-2 ${getSignalColor()}`}>
              {getSignalIcon()}
              <span className="text-2xl font-bold">{latestSignal.signalType}</span>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold">{latestSignal.confidence.toFixed(1)}%</div>
              <div className="text-xs text-muted-foreground">Confidence</div>
            </div>
          </div>
          
          <p className="text-sm text-muted-foreground mb-3">
            {latestSignal.reasoning}
          </p>
          
          {/* FTCP Status */}
          {latestSignal.ftcpDetected && (
            <div className="flex items-center gap-2 text-xs">
              <Zap className="w-4 h-4 text-yellow-500" />
              <span className="text-yellow-500 font-semibold">FTCP Detected</span>
              <Badge variant="outline" className="text-xs">
                Golden Ratio: {(latestSignal.goldenRatioScore * 100).toFixed(0)}%
              </Badge>
            </div>
          )}
        </div>
        
        {/* Metrics Grid */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">Lighthouse Signal</div>
            <div className="text-lg font-semibold">
              {latestSignal.lighthouse.L.toFixed(3)}
            </div>
            <div className="text-xs text-muted-foreground">
              {latestSignal.lighthouse.isLHE ? '✅ LHE Confirmed' : '⏳ Below Threshold'}
            </div>
          </div>
          
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">Curvature</div>
            <div className="text-lg font-semibold">
              {latestSignal.curvature.toFixed(4)}
            </div>
            <div className="text-xs text-muted-foreground">
              Direction: {latestSignal.curvatureDirection}
            </div>
          </div>
          
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">Linear Coherence</div>
            <div className="text-lg font-semibold">
              {(latestSignal.coherence.linearCoherence * 100).toFixed(1)}%
            </div>
          </div>
          
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">Cross-Scale φ</div>
            <div className="text-lg font-semibold">
              {(latestSignal.coherence.crossScaleCoherence * 100).toFixed(1)}%
            </div>
          </div>
        </div>
        
        {/* Signal Statistics */}
        <div className="border-t pt-4">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-xs text-muted-foreground">Total Signals</div>
              <div className="text-lg font-semibold">{stats.totalSignals}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Buy/Sell</div>
              <div className="text-lg font-semibold">
                <span className="text-green-500">{stats.buySignals}</span>
                {' / '}
                <span className="text-red-500">{stats.sellSignals}</span>
              </div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Avg Confidence</div>
              <div className="text-lg font-semibold">{stats.avgConfidence.toFixed(1)}%</div>
            </div>
          </div>
        </div>
        
        {/* Recent Signals */}
        {signals.length > 0 && (
          <div className="border-t pt-4">
            <h4 className="text-sm font-semibold mb-3">Recent Signals</h4>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {signals.slice(-5).reverse().map((signal, idx) => (
                <div key={idx} className="flex items-center justify-between text-xs border-b pb-2">
                  <div className="flex items-center gap-2">
                    {signal.signalType === 'BUY' ? (
                      <TrendingUp className="w-3 h-3 text-green-500" />
                    ) : (
                      <TrendingDown className="w-3 h-3 text-red-500" />
                    )}
                    <span className={signal.signalType === 'BUY' ? 'text-green-500' : 'text-red-500'}>
                      {signal.signalType}
                    </span>
                    <Badge variant="outline" className="text-xs">
                      Tier {signal.tier}
                    </Badge>
                  </div>
                  <div className="text-muted-foreground">
                    {signal.confidence.toFixed(0)}% • {new Date(signal.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}
