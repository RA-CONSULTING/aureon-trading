import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Sparkles, Zap, TrendingUp } from 'lucide-react';
import nexusUnityPathImg from '@/assets/research/nexus-unity-path.png';
import timelineSurgeImg from '@/assets/research/timeline-surge-2025-2045.png';

interface UnityEventTrackerProps {
  coherence: number;
  phaseSpread: number;
  unityProbability: number;
  isUnityEvent: boolean;
  t: number;
}

export const UnityEventTracker = ({ 
  coherence, 
  phaseSpread, 
  unityProbability, 
  isUnityEvent,
  t 
}: UnityEventTrackerProps) => {
  
  // Generate synthetic AURIS temporal coherence data for display
  const generateCoherenceHistory = () => {
    const data = [];
    for (let i = 0; i < 50; i++) {
      const time = i * 2;
      // Simulate coherence oscillation with trend toward unity
      const baseCoherence = 0.7 + 0.25 * Math.sin(time * 0.3);
      const trend = Math.min(0.3, time / 200); // Gradual increase
      const noise = (Math.random() - 0.5) * 0.05;
      data.push({
        time,
        coherence: Math.min(1.0, baseCoherence + trend + noise),
      });
    }
    return data;
  };
  
  const coherenceHistory = generateCoherenceHistory();
  
  return (
    <div className="space-y-6">
      {/* Unity Event Status */}
      <Card className={`border-2 ${
        isUnityEvent 
          ? 'border-yellow-500 bg-gradient-to-br from-yellow-500/20 to-purple-500/20' 
          : 'border-primary/20 bg-gradient-to-br from-background to-primary/5'
      }`}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className={`h-6 w-6 ${isUnityEvent ? 'text-yellow-500 animate-pulse' : 'text-primary'}`} />
            Unity Event Tracker
          </CardTitle>
          <CardDescription>
            Path to Unity (Ego Death) | Coherence → 1.0, Phase Spread → 0
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {isUnityEvent && (
            <div className="p-4 rounded-lg bg-yellow-500/20 border-2 border-yellow-500 animate-pulse">
              <div className="flex items-center justify-center gap-3">
                <Sparkles className="h-8 w-8 text-yellow-500" />
                <div className="text-center">
                  <div className="text-2xl font-bold text-yellow-500">
                    🌟 UNITY EVENT DETECTED
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Cycle Switch @ t≈{t.toFixed(1)} (Ego Death / Transcendence)
                  </div>
                </div>
                <Sparkles className="h-8 w-8 text-yellow-500" />
              </div>
            </div>
          )}
          
          {/* Unity Metrics */}
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <div className="text-sm font-medium">Coherence (C)</div>
              <div className="text-3xl font-bold text-primary">
                {(coherence * 100).toFixed(1)}%
              </div>
              <Progress value={coherence * 100} className="h-2" />
              <div className="text-xs text-muted-foreground">
                Target: 100% (Unity)
              </div>
            </div>
            
            <div className="space-y-2">
              <div className="text-sm font-medium">Phase Spread (Θ)</div>
              <div className="text-3xl font-bold text-primary">
                {(phaseSpread * 100).toFixed(1)}%
              </div>
              <Progress value={(1 - phaseSpread) * 100} className="h-2" />
              <div className="text-xs text-muted-foreground">
                Target: 0% (Alignment)
              </div>
            </div>
            
            <div className="space-y-2">
              <div className="text-sm font-medium">Unity Probability</div>
              <div className="text-3xl font-bold text-primary">
                {(unityProbability * 100).toFixed(1)}%
              </div>
              <Progress value={unityProbability * 100} className="h-2" />
              <div className="text-xs text-muted-foreground">
                Event threshold: 95%+
              </div>
            </div>
          </div>
          
          {/* Nexus System Dynamics Diagram */}
          <div className="space-y-3">
            <div className="text-sm font-semibold flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-primary" />
              Nexus System Dynamics: Path to Unity
            </div>
            <img 
              src={nexusUnityPathImg} 
              alt="Nexus Unity Path" 
              className="w-full rounded-lg border border-border/50"
            />
            <div className="text-xs text-muted-foreground">
              <strong>Unity Event (Cycle Switch @ t≈22):</strong> Coherence (C) reaches 1.0 while Phase Spread (Θ) drops to 0, 
              triggering an ego-death/transcendence event where all field components lock in perfect alignment.
            </div>
          </div>
          
          {/* AURIS Temporal Coherence Chart */}
          <div className="space-y-3">
            <div className="text-sm font-semibold flex items-center gap-2">
              <Zap className="h-4 w-4 text-primary" />
              AURIS Temporal Coherence (Synthetic)
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={coherenceHistory}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis 
                  dataKey="time" 
                  stroke="hsl(var(--muted-foreground))"
                  label={{ value: 'Time (index)', position: 'insideBottom', offset: -5 }}
                />
                <YAxis 
                  stroke="hsl(var(--muted-foreground))"
                  domain={[0.6, 1.0]}
                  label={{ value: 'Coherence', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))'
                  }}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="coherence" 
                  stroke="#f59e0b" 
                  strokeWidth={2}
                  dot={false}
                  name="Coherence (0-1)"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          
          {/* Timeline Surge Visualization */}
          <div className="space-y-3">
            <div className="text-sm font-semibold flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" />
              Timeline Surge: 2025-2045 Convergence
            </div>
            <img 
              src={timelineSurgeImg} 
              alt="Timeline Surge" 
              className="w-full rounded-lg border border-border/50"
            />
            <div className="text-xs text-muted-foreground">
              <strong>Peak Surge (2027-2037):</strong> Maximum coherence window leading to Cosmic Alignment Nexus @ 2040-2043. 
              Pluto in Aquarius (2038) and Saturn-Pisces alignments create optimal field conditions.
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
