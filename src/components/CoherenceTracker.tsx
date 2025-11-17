import { useEffect, useState, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Area, AreaChart } from 'recharts';
import { Bell, BellOff, TrendingUp, AlertTriangle, Activity } from 'lucide-react';
import { useToast } from "@/hooks/use-toast";
import type { LambdaState } from '@/core/masterEquation';

interface CoherencePoint {
  timestamp: number;
  coherence: number;
  label: string;
}

interface CoherenceTrackerProps {
  lambda: LambdaState | null;
  isRunning: boolean;
}

const HIGH_COHERENCE_THRESHOLD = 0.92;
const OPTIMAL_ZONE_THRESHOLD = 0.945;
const HISTORY_LIMIT = 100;

export const CoherenceTracker = ({ lambda, isRunning }: CoherenceTrackerProps) => {
  const [coherenceHistory, setCoherenceHistory] = useState<CoherencePoint[]>([]);
  const [alertsEnabled, setAlertsEnabled] = useState(true);
  const [inHighCoherenceZone, setInHighCoherenceZone] = useState(false);
  const [peakCoherence, setPeakCoherence] = useState(0);
  const [avgCoherence, setAvgCoherence] = useState(0);
  const lastAlertTimeRef = useRef(0);
  const { toast } = useToast();

  useEffect(() => {
    if (!lambda || !isRunning) return;

    const now = Date.now();
    const coherence = lambda.coherence;

    // Update history
    setCoherenceHistory(prev => {
      const newPoint: CoherencePoint = {
        timestamp: now,
        coherence,
        label: new Date(now).toLocaleTimeString(),
      };
      
      const updated = [...prev, newPoint];
      if (updated.length > HISTORY_LIMIT) {
        updated.shift();
      }
      
      // Calculate statistics
      const recentPoints = updated.slice(-20);
      const avg = recentPoints.reduce((sum, p) => sum + p.coherence, 0) / recentPoints.length;
      const peak = Math.max(...recentPoints.map(p => p.coherence));
      
      setAvgCoherence(avg);
      setPeakCoherence(peak);
      
      return updated;
    });

    // Check for high coherence zone entry
    const wasInZone = inHighCoherenceZone;
    const isInZone = coherence >= HIGH_COHERENCE_THRESHOLD;
    
    if (isInZone && !wasInZone && alertsEnabled) {
      // Throttle alerts to once per 10 seconds
      const timeSinceLastAlert = now - lastAlertTimeRef.current;
      if (timeSinceLastAlert > 10000) {
        lastAlertTimeRef.current = now;
        
        const isOptimal = coherence >= OPTIMAL_ZONE_THRESHOLD;
        
        toast({
          title: isOptimal ? "🎯 OPTIMAL TRADING ZONE" : "⚡ High Coherence Detected",
          description: `C(t) = ${coherence.toFixed(4)} — ${isOptimal ? 'LIGHTHOUSE OPTIMAL' : 'High coherence trading window'}`,
          duration: 5000,
        });
      }
    }
    
    setInHighCoherenceZone(isInZone);
  }, [lambda, isRunning, inHighCoherenceZone, alertsEnabled, toast]);

  const currentCoherence = lambda?.coherence ?? 0;
  const isOptimalZone = currentCoherence >= OPTIMAL_ZONE_THRESHOLD;
  const isHighZone = currentCoherence >= HIGH_COHERENCE_THRESHOLD && !isOptimalZone;

  const getZoneStatus = () => {
    if (isOptimalZone) return { label: 'OPTIMAL', color: 'text-green-500', bg: 'bg-green-500/10' };
    if (isHighZone) return { label: 'HIGH', color: 'text-yellow-500', bg: 'bg-yellow-500/10' };
    return { label: 'FORMING', color: 'text-blue-500', bg: 'bg-blue-500/10' };
  };

  const zone = getZoneStatus();

  return (
    <Card className="border-primary/20 bg-card/50 backdrop-blur">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-xl font-bold flex items-center gap-2">
              <Activity className="h-5 w-5 text-primary" />
              Real-Time Coherence Tracker C(t)
            </CardTitle>
            <CardDescription>
              Live self-organization metric with high-coherence zone alerts
            </CardDescription>
          </div>
          <Button
            variant={alertsEnabled ? "default" : "outline"}
            size="sm"
            onClick={() => setAlertsEnabled(!alertsEnabled)}
            className="gap-2"
          >
            {alertsEnabled ? <Bell className="h-4 w-4" /> : <BellOff className="h-4 w-4" />}
            {alertsEnabled ? 'Alerts ON' : 'Alerts OFF'}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Current Status */}
        <div className="grid grid-cols-4 gap-4">
          <Card className={`${zone.bg} border-2 ${zone.color.replace('text-', 'border-')}`}>
            <CardContent className="p-4">
              <div className="text-center">
                <p className="text-xs text-muted-foreground mb-1">Current Zone</p>
                <Badge variant="outline" className={`${zone.color} font-bold text-lg`}>
                  {zone.label}
                </Badge>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-background/50">
            <CardContent className="p-4">
              <div className="text-center">
                <p className="text-xs text-muted-foreground mb-1">Current C(t)</p>
                <p className={`text-2xl font-mono font-bold ${zone.color}`}>
                  {currentCoherence.toFixed(4)}
                </p>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-background/50">
            <CardContent className="p-4">
              <div className="text-center">
                <p className="text-xs text-muted-foreground mb-1">20-Point Average</p>
                <p className="text-2xl font-mono font-bold text-foreground">
                  {avgCoherence.toFixed(4)}
                </p>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-background/50">
            <CardContent className="p-4">
              <div className="text-center">
                <p className="text-xs text-muted-foreground mb-1">Peak (20pt)</p>
                <p className="text-2xl font-mono font-bold text-green-500">
                  {peakCoherence.toFixed(4)}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Coherence Evolution Chart */}
        <Card className="bg-background/50">
          <CardHeader>
            <CardTitle className="text-sm font-semibold">C(t) Evolution — Rising from Chaos to Order</CardTitle>
          </CardHeader>
          <CardContent>
            {coherenceHistory.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={coherenceHistory}>
                  <defs>
                    <linearGradient id="coherenceGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
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
                    formatter={(value: number) => [value.toFixed(4), 'C(t)']}
                    contentStyle={{ 
                      backgroundColor: 'rgba(0, 0, 0, 0.8)', 
                      border: '1px solid #333',
                      borderRadius: '8px'
                    }}
                  />
                  
                  {/* Reference lines for thresholds */}
                  <ReferenceLine 
                    y={OPTIMAL_ZONE_THRESHOLD} 
                    stroke="#10b981" 
                    strokeDasharray="3 3"
                    label={{ value: 'Optimal (0.945)', position: 'right', fill: '#10b981', fontSize: 10 }}
                  />
                  <ReferenceLine 
                    y={HIGH_COHERENCE_THRESHOLD} 
                    stroke="#eab308" 
                    strokeDasharray="3 3"
                    label={{ value: 'High (0.92)', position: 'right', fill: '#eab308', fontSize: 10 }}
                  />
                  
                  <Area
                    type="monotone"
                    dataKey="coherence"
                    stroke="#10b981"
                    strokeWidth={2}
                    fill="url(#coherenceGradient)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                <div className="text-center space-y-2">
                  <Activity className="h-12 w-12 mx-auto opacity-50" />
                  <p>Waiting for coherence data...</p>
                  <p className="text-xs">Start the system to begin tracking</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Zone Information */}
        <div className="grid grid-cols-3 gap-3">
          <Card className="bg-green-500/10 border border-green-500/20">
            <CardContent className="p-3">
              <div className="flex items-start gap-2">
                <TrendingUp className="h-4 w-4 text-green-500 mt-0.5" />
                <div>
                  <h4 className="font-semibold text-sm text-green-500">Optimal Zone</h4>
                  <p className="text-xs text-muted-foreground mt-1">
                    C(t) ≥ 0.945 — Lighthouse consensus achieved. Maximal coherence for trading decisions.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-yellow-500/10 border border-yellow-500/20">
            <CardContent className="p-3">
              <div className="flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 text-yellow-500 mt-0.5" />
                <div>
                  <h4 className="font-semibold text-sm text-yellow-500">High Zone</h4>
                  <p className="text-xs text-muted-foreground mt-1">
                    0.92 ≤ C(t) {'<'} 0.945 — Strong phase-locking. Favorable trading window.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-blue-500/10 border border-blue-500/20">
            <CardContent className="p-3">
              <div className="flex items-start gap-2">
                <Activity className="h-4 w-4 text-blue-500 mt-0.5" />
                <div>
                  <h4 className="font-semibold text-sm text-blue-500">Forming Zone</h4>
                  <p className="text-xs text-muted-foreground mt-1">
                    C(t) {'<'} 0.92 — System organizing. Wait for higher coherence.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Mathematical Definition */}
        <Card className="bg-primary/5 border-primary/20">
          <CardContent className="p-3">
            <div className="space-y-2">
              <h4 className="font-semibold text-sm">Coherence Definition</h4>
              <div className="rounded-lg bg-background/50 p-3 font-mono text-sm">
                C = max<sub>δ</sub> ⟨Λ(t)Λ(t + δ)⟩ / ⟨Λ(t)²⟩
              </div>
              <p className="text-xs text-muted-foreground">
                Quantifies self-organization and phase-locking of the Master Equation field. 
                High C indicates stable branch formation and optimal market alignment.
              </p>
            </div>
          </CardContent>
        </Card>
      </CardContent>
    </Card>
  );
};
