import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Activity, Wifi, WifiOff } from "lucide-react";
import { useLiveTradingSignals } from "@/hooks/useLiveTradingSignals";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { useState, useEffect } from "react";

interface CoherencePoint {
  timestamp: number;
  coherence: number;
  lambda: number;
  label: string;
}

export const LiveCoherenceTracker = ({ symbol = 'btcusdt' }: { symbol?: string }) => {
  const { currentLambda, isConnected } = useLiveTradingSignals(symbol);
  const [history, setHistory] = useState<CoherencePoint[]>([]);

  useEffect(() => {
    if (!currentLambda) return;

    const point: CoherencePoint = {
      timestamp: Date.now(),
      coherence: currentLambda.coherence,
      lambda: currentLambda.lambda,
      label: new Date().toLocaleTimeString(),
    };

    setHistory(prev => {
      const updated = [...prev, point];
      if (updated.length > 100) updated.shift();
      return updated;
    });
  }, [currentLambda]);

  const currentCoherence = currentLambda?.coherence ?? 0;
  const isOptimal = currentCoherence >= 0.945;
  const isHigh = currentCoherence >= 0.92 && !isOptimal;

  const getZoneStatus = () => {
    if (isOptimal) return { label: 'OPTIMAL', color: 'text-success', bg: 'bg-success/10' };
    if (isHigh) return { label: 'HIGH', color: 'text-yellow-500', bg: 'bg-yellow-500/10' };
    return { label: 'FORMING', color: 'text-blue-500', bg: 'bg-blue-500/10' };
  };

  const zone = getZoneStatus();

  return (
    <Card className="bg-card shadow-card">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Activity className="h-5 w-5 text-primary" />
            Live Coherence Γ(t)
          </CardTitle>
          <Badge variant={isConnected ? "default" : "secondary"} className="gap-1">
            {isConnected ? (
              <>
                <Wifi className="w-3 h-3" />
                Live
              </>
            ) : (
              <>
                <WifiOff className="w-3 h-3" />
                Connecting...
              </>
            )}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Current Status */}
        <div className="grid grid-cols-3 gap-3">
          <Card className={`${zone.bg} border-2 ${zone.color.replace('text-', 'border-')}`}>
            <CardContent className="p-3">
              <div className="text-center">
                <p className="text-xs text-muted-foreground mb-1">Zone</p>
                <Badge variant="outline" className={`${zone.color} font-bold`}>
                  {zone.label}
                </Badge>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-background/50">
            <CardContent className="p-3">
              <div className="text-center">
                <p className="text-xs text-muted-foreground mb-1">Γ(t)</p>
                <p className={`text-xl font-mono font-bold ${zone.color}`}>
                  {currentCoherence.toFixed(4)}
                </p>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-background/50">
            <CardContent className="p-3">
              <div className="text-center">
                <p className="text-xs text-muted-foreground mb-1">Λ(t)</p>
                <p className="text-xl font-mono font-bold">
                  {currentLambda?.lambda.toFixed(4) ?? '0.0000'}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Chart */}
        <Card className="bg-background/50">
          <CardContent className="p-4">
            {history.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={history}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" opacity={0.3} />
                  <XAxis 
                    dataKey="timestamp" 
                    tickFormatter={(ts) => new Date(ts).toLocaleTimeString()}
                    stroke="#888"
                    fontSize={10}
                  />
                  <YAxis 
                    domain={[0, 1]}
                    stroke="#888"
                    fontSize={10}
                  />
                  <Tooltip 
                    labelFormatter={(ts) => new Date(ts as number).toLocaleTimeString()}
                    formatter={(value: number) => [value.toFixed(4), 'Γ(t)']}
                    contentStyle={{ 
                      backgroundColor: 'rgba(0, 0, 0, 0.8)', 
                      border: '1px solid #333',
                      borderRadius: '8px'
                    }}
                  />
                  <ReferenceLine 
                    y={0.945} 
                    stroke="#10b981" 
                    strokeDasharray="3 3"
                    label={{ value: 'Optimal', position: 'right', fill: '#10b981', fontSize: 10 }}
                  />
                  <ReferenceLine 
                    y={0.92} 
                    stroke="#eab308" 
                    strokeDasharray="3 3"
                    label={{ value: 'High', position: 'right', fill: '#eab308', fontSize: 10 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="coherence"
                    stroke="#10b981"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[200px] flex items-center justify-center text-muted-foreground">
                <p>Waiting for coherence data...</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Info */}
        <div className="text-xs text-muted-foreground space-y-1">
          <p>• <span className="text-success">Optimal Zone</span>: Γ ≥ 0.945 (Lighthouse consensus)</p>
          <p>• <span className="text-yellow-500">High Zone</span>: 0.92 ≤ Γ &lt; 0.945 (Strong phase-locking)</p>
          <p>• <span className="text-blue-500">Forming</span>: Γ &lt; 0.92 (System organizing)</p>
        </div>
      </CardContent>
    </Card>
  );
};