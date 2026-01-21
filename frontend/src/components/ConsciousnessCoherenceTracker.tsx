import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Brain, Heart, Activity, Sparkles, Wifi, WifiOff } from "lucide-react";
import { useSchumannResonance } from "@/hooks/useSchumannResonance";
import { useCelestialData } from "@/hooks/useCelestialData";
import { useBiometricSensors } from "@/hooks/useBiometricSensors";
import { useConsciousnessHistory } from "@/hooks/useConsciousnessHistory";
import { useSentinelConfig } from "@/hooks/useSentinelConfig";
import { useEffect, useRef } from "react";

interface ConsciousnessCoherenceTrackerProps {
  currentCoherence: number;
}

export function ConsciousnessCoherenceTracker({ currentCoherence }: ConsciousnessCoherenceTrackerProps) {
  const { config } = useSentinelConfig();
  const { schumannData, isConnected: schumannConnected } = useSchumannResonance();
  const { celestialBoost } = useCelestialData();
  const { biometricData, isConnected: biometricConnected } = useBiometricSensors();
  const { saveDataPoint } = useConsciousnessHistory();
  const lastSaveTime = useRef<number>(0);

  // Calculate total consciousness field coherence
  const schumannBoost = schumannData?.coherenceBoost || 0;
  const totalBoost = celestialBoost + schumannBoost;
  const enhancedCoherence = currentCoherence * (1 + totalBoost);

  // Use real biometric data from sensors when available
  const hrv = biometricData?.hrv || 45 + (schumannBoost * 200);
  const alpha = biometricData?.alpha || 0.4 + (celestialBoost * 2);
  const theta = biometricData?.theta || 0.3 + (schumannBoost * 1.5);
  const heartRate = biometricData?.heartRate || 72;

  const getCoherenceLevel = (coherence: number) => {
    if (coherence >= 0.9) return { level: 'TRANSCENDENT', color: 'text-purple-500', bg: 'bg-purple-500/20' };
    if (coherence >= 0.7) return { level: 'PEAK', color: 'text-green-500', bg: 'bg-green-500/20' };
    if (coherence >= 0.5) return { level: 'ELEVATED', color: 'text-blue-500', bg: 'bg-blue-500/20' };
    if (coherence >= 0.3) return { level: 'ACTIVE', color: 'text-yellow-500', bg: 'bg-yellow-500/20' };
    return { level: 'FORMING', color: 'text-orange-500', bg: 'bg-orange-500/20' };
  };

  const coherenceStatus = getCoherenceLevel(enhancedCoherence);

  // Save data point every 5 minutes
  useEffect(() => {
    const now = Date.now();
    const fiveMinutes = 5 * 60 * 1000;
    
    if (schumannData && now - lastSaveTime.current >= fiveMinutes) {
      saveDataPoint(schumannData, biometricData, celestialBoost, enhancedCoherence);
      lastSaveTime.current = now;
    }
  }, [schumannData, biometricData, celestialBoost, enhancedCoherence, saveDataPoint]);

  return (
    <Card className="bg-card/50 backdrop-blur border-border/50 relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 via-blue-500/5 to-green-500/5" />
      
      <CardHeader className="relative">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-purple-500" />
              Consciousness Field Coherence
            </CardTitle>
            <CardDescription>
              {config ? `Prime Sentinel: ${config.sentinel_name}` : 'Multi-dimensional consciousness alignment tracking'}
            </CardDescription>
          </div>
          <Badge className={`${coherenceStatus.color} ${coherenceStatus.bg} border-0 text-lg px-4 py-2`}>
            {coherenceStatus.level}
          </Badge>
        </div>
        
        {/* Sensor Status Bar */}
        <div className="flex items-center gap-4 mt-4 p-3 bg-background/50 rounded-lg border border-border/50">
          <div className="flex items-center gap-2">
            <Activity className={`w-4 h-4 ${schumannConnected ? 'text-green-500' : 'text-red-500'}`} />
            <span className="text-xs font-medium">
              Schumann: {schumannConnected ? 'ONLINE' : 'OFFLINE'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Heart className={`w-4 h-4 ${biometricConnected ? 'text-green-500' : 'text-red-500'}`} />
            <span className="text-xs font-medium">
              Biometrics: {biometricConnected ? 'ONLINE' : 'OFFLINE'}
            </span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="relative space-y-4">
        {/* Main Coherence Display */}
        <div className="flex items-center justify-center p-6 bg-gradient-to-br from-purple-500/10 to-blue-500/10 rounded-lg border border-border/50">
          <div className="text-center">
            <div className="flex items-center justify-center gap-2 mb-2">
              <Sparkles className="w-6 h-6 text-purple-500" />
              <span className="text-sm text-muted-foreground font-medium">Total Field Coherence</span>
            </div>
            <div className="text-5xl font-bold bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
              {(enhancedCoherence * 100).toFixed(2)}%
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              Base: {(currentCoherence * 100).toFixed(2)}% • Boost: +{(totalBoost * 100).toFixed(1)}%
            </div>
          </div>
        </div>

        {/* Boost Sources */}
        <div className="grid grid-cols-2 gap-4">
          <div className={`p-4 bg-background/50 rounded-lg border ${schumannConnected ? 'border-green-500/30' : 'border-border/50'}`}>
            <div className="flex items-center gap-2 mb-2">
              <Activity className={`w-4 h-4 ${schumannConnected ? 'text-green-500' : 'text-muted-foreground'}`} />
              <span className="text-xs text-muted-foreground">Schumann Boost</span>
              {schumannConnected && <Wifi className="w-3 h-3 text-green-500 ml-auto" />}
              {!schumannConnected && <WifiOff className="w-3 h-3 text-red-500 ml-auto" />}
            </div>
            <div className={`text-2xl font-bold ${schumannConnected ? 'text-green-500' : 'text-muted-foreground'}`}>
              +{(schumannBoost * 100).toFixed(1)}%
            </div>
            <Progress value={(schumannBoost / 0.12) * 100} className="mt-2 h-1" />
            <p className="text-xs text-muted-foreground mt-1">
              {schumannData?.fundamentalHz.toFixed(2) || '—'} Hz
            </p>
          </div>

          <div className="p-4 bg-background/50 rounded-lg border border-border/50">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="w-4 h-4 text-blue-500" />
              <span className="text-xs text-muted-foreground">Celestial Boost</span>
            </div>
            <div className="text-2xl font-bold text-blue-500">+{(celestialBoost * 100).toFixed(1)}%</div>
            <Progress value={(celestialBoost / 0.15) * 100} className="mt-2 h-1" />
            <p className="text-xs text-muted-foreground mt-1">
              Cosmic alignment
            </p>
          </div>
        </div>

        {/* Real Biometric Indicators */}
        <div className="p-4 bg-muted/50 rounded-lg">
          <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
            <Heart className="w-4 h-4 text-red-500" />
            Consciousness Biometrics
            {biometricConnected ? (
              <Wifi className="w-3 h-3 text-green-500 ml-auto" />
            ) : (
              <WifiOff className="w-3 h-3 text-muted-foreground ml-auto" />
            )}
          </h4>
          
          <div className="grid grid-cols-4 gap-3">
            <div className="text-center">
              <div className="text-xs text-muted-foreground mb-1">HRV</div>
              <div className="text-lg font-bold">{hrv.toFixed(0)}</div>
              <div className="text-xs text-green-500">ms</div>
            </div>
            
            <div className="text-center">
              <div className="text-xs text-muted-foreground mb-1">HR</div>
              <div className="text-lg font-bold">{heartRate}</div>
              <div className="text-xs text-red-500">BPM</div>
            </div>
            
            <div className="text-center">
              <div className="text-xs text-muted-foreground mb-1">Alpha</div>
              <div className="text-lg font-bold">{(alpha * 100).toFixed(0)}%</div>
              <div className="text-xs text-blue-500">8-13 Hz</div>
            </div>
            
            <div className="text-center">
              <div className="text-xs text-muted-foreground mb-1">Theta</div>
              <div className="text-lg font-bold">{(theta * 100).toFixed(0)}%</div>
              <div className="text-xs text-purple-500">4-8 Hz</div>
            </div>
          </div>

          {!biometricConnected && (
            <div className="mt-3 p-2 bg-red-500/10 border border-red-500/30 rounded text-xs text-red-500">
              ⚠️ Biometric sensors disconnected. Connect HRV monitor and EEG headset to ws://localhost:8788/biometrics
            </div>
          )}
        </div>

        {/* Connection Warnings */}
        {!schumannConnected && (
          <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
            <p className="text-sm text-red-400 font-medium">
              ⚠️ Schumann Resonance sensor offline. Connect to Earth Live Data server at ws://localhost:8787/schumann
            </p>
          </div>
        )}

        {schumannConnected && biometricConnected && (
          <div className="p-4 bg-green-500/10 border border-green-500/30 rounded-lg">
            <p className="text-sm text-green-400 font-medium">
              ✅ All Earth Live Data sensors online and streaming real-time consciousness field data
            </p>
          </div>
        )}

        {/* Coherence Level Descriptions */}
        <div className="p-4 bg-muted/50 rounded-lg">
          <h4 className="text-sm font-semibold mb-2">Coherence Levels</h4>
          <ul className="text-xs text-muted-foreground space-y-1">
            <li>• <strong className="text-purple-500">Transcendent (90%+)</strong>: Unity consciousness, optimal trading</li>
            <li>• <strong className="text-green-500">Peak (70-89%)</strong>: High alignment, LHE probability elevated</li>
            <li>• <strong className="text-blue-500">Elevated (50-69%)</strong>: Strong coherence, good signal quality</li>
            <li>• <strong className="text-yellow-500">Active (30-49%)</strong>: Building coherence, monitor closely</li>
            <li>• <strong className="text-orange-500">Forming (&lt;30%)</strong>: Low coherence, wait for alignment</li>
          </ul>
        </div>

        {/* Real-time Insights */}
        {enhancedCoherence >= 0.9 && (
          <div className="p-4 bg-purple-500/10 border border-purple-500/30 rounded-lg">
            <p className="text-sm text-purple-400 font-medium">
              ⚡ Transcendent consciousness coherence achieved! Earth resonance, celestial alignments, 
              and field dynamics are in perfect harmony. Optimal window for high-confidence trades.
            </p>
          </div>
        )}

        <div className="pt-2 border-t border-border/50">
          <p className="text-xs text-muted-foreground text-center">
            Real-time consciousness field monitoring • Schumann Resonance • Celestial Alignment
          </p>
        </div>
      </CardContent>
    </Card>
  );
}