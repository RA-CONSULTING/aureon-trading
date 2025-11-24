import React, { useEffect, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { NexusLiveDashboard } from "./NexusLiveDashboard";
import { IdentityBinder } from "./IdentityBinder";
import { GainHarmonicsControls } from "./GainHarmonicsControls";
import { AurisSymbolicCompiler } from "./AurisSymbolicCompiler";
import { AuraRingVisualizer } from "./AuraRingVisualizer";

// Types for metrics
export type AurisMetrics = {
  ts?: string;
  coherence_score?: number;
  schumann_lock?: number;
  tsv_gain?: number;
  prime_alignment?: number;
  ten_nine_one_concordance?: number;
};

export type AuraMetrics = {
  ts?: string;
  alpha_theta_ratio?: number;
  alpha_theta_norm?: number;
  hrv_norm?: number;
  gsr_norm?: number;
  prime_concordance_10_9_1?: number;
  calm_index?: number;
  aura_hue_deg?: number;
};

// Connection status type
type ConnectionStatus = 'connected' | 'disconnected' | 'connecting';

// Delta change indicator component
function DeltaIndicator({ value, label }: { value?: number; label: string }) {
  if (value === undefined) return null;
  const isPositive = value > 0;
  const color = isPositive ? 'text-green-400' : value < 0 ? 'text-red-400' : 'text-zinc-400';
  return (
    <div className={`text-xs font-mono ${color}`}>
      {label}: {isPositive ? '+' : ''}{value.toFixed(3)}
    </div>
  );
}
// ---------- Main Dashboard ----------
export function NexusLiveDashboardMain() {
  const [aurisMetrics, setAurisMetrics] = useState<AurisMetrics>({});
  const [auraMetrics, setAuraMetrics] = useState<AuraMetrics>({});
  const [connected, setConnected] = useState(false);
  const [identity, setIdentity] = useState({ name: "", dob: "", t0Hz: 2911.91, role: "Observer" });
  const [currentGain, setCurrentGain] = useState(1.0);
  const [currentFundamental, setCurrentFundamental] = useState(7.83);
  const [deltaMetrics, setDeltaMetrics] = useState<{coherence?: number, lock?: number}>({});
  const [auraRingGlow, setAuraRingGlow] = useState(0.5);
  const wsRef = useRef<WebSocket | null>(null);

  // Auto-update role based on live metrics
  const updateRole = (auris: AurisMetrics, aura: AuraMetrics) => {
    const coherence = auris.coherence_score || 0;
    const lock = auris.schumann_lock || 0;
    const calm = aura.calm_index || 0;
    const concordance = aura.prime_concordance_10_9_1 || 0;
    
    let newRole = "Observer";
    if (coherence >= 0.75 && lock >= 0.7 && calm >= 0.7 && concordance >= 0.7) {
      newRole = "Prime Sentinel (Active)";
    } else if (coherence >= 0.6 && calm >= 0.5) {
      newRole = "Field Harmonizer";
    } else if (coherence >= 0.4) {
      newRole = "Calibrator";
    }
    
    setIdentity(prev => ({ ...prev, role: newRole }));
    setAuraRingGlow(Math.min(1.0, (coherence + calm) / 2));
  };

  // Send control messages to validators
  const sendControlMessage = (control: { gain?: number; targets_hz?: number[] }) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const message = JSON.stringify({ type: "control", ...control });
      wsRef.current.send(message);
      
      // Update local state
      if (control.gain !== undefined) setCurrentGain(control.gain);
      if (control.targets_hz !== undefined) setCurrentFundamental(control.targets_hz[0]);
    }
  };

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8787');
    wsRef.current = ws;
    
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);
    
    ws.onmessage = (event) => {
      try {
        const { type, data } = JSON.parse(event.data);
        if (type === 'auris_metrics') {
          const prevCoherence = aurisMetrics.coherence_score;
          const prevLock = aurisMetrics.schumann_lock;
          if (prevCoherence !== undefined && prevLock !== undefined) {
            setDeltaMetrics({
              coherence: (data.coherence_score || 0) - prevCoherence,
              lock: (data.schumann_lock || 0) - prevLock
            });
          }
          setAurisMetrics(data);
          updateRole(data, auraMetrics);
        }
        if (type === 'aura_features') {
          setAuraMetrics(data);
          updateRole(aurisMetrics, data);
        }
      } catch (e) {
        console.error('WebSocket message parse error:', e);
      }
    };
    
    return () => ws.close();
  }, [aurisMetrics, auraMetrics]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">🌟 Harmonic Nexus Charter Console</h1>
        <div className="flex items-center gap-4">
          <Badge variant={connected ? "default" : "destructive"}>
            {connected ? "🟢 Live Feed" : "🔴 Disconnected"}
          </Badge>
          <Badge variant="outline" className="text-xs font-mono">
            Gain: {currentGain.toFixed(2)} | Fund: {currentFundamental.toFixed(2)}Hz
          </Badge>
        </div>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-6 gap-6">
        {/* Unified Control Panel */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-lg">🎛️ Control Console</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Identity Section */}
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-zinc-300 border-b border-zinc-700 pb-1">
                Prime Seal Identity
              </h3>
              <IdentityBinder onIdentityChange={setIdentity} />
            </div>
            
            {/* Intent Section */}
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-zinc-300 border-b border-zinc-700 pb-1">
                Intent → Harmonics
              </h3>
              <AurisSymbolicCompiler 
                onWaveformGenerated={(waveform) => {
                  console.log('Generated waveform:', waveform);
                  if (wsRef.current?.readyState === WebSocket.OPEN) {
                    wsRef.current.send(JSON.stringify({
                      type: 'waveform',
                      data: waveform
                    }));
                  }
                }}
              />
            </div>
            
            {/* Gain & Frequency Controls */}
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-zinc-300 border-b border-zinc-700 pb-1">
                Field Tuning
              </h3>
              <GainHarmonicsControls 
                onControlChange={sendControlMessage}
                currentGain={currentGain}
                currentFundamental={currentFundamental}
              />
            </div>
          </CardContent>
        </Card>
        
        {/* Identity & Status Card */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              🆔 Prime Identity Seal
              <Badge variant="outline" className="text-xs">
                Φ·Gaia·{identity.dob?.replace(/-/g, '')}·10:9:1
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-zinc-400">Name:</span>
                  <span className="font-mono">{identity.name || 'Anonymous'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">DOB:</span>
                  <span className="font-mono">{identity.dob || 'Not Set'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">t₀ Hz:</span>
                  <span className="font-mono text-blue-400">{identity.t0Hz}</span>
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-zinc-400">Calm Index:</span>
                  <span className="font-mono">{(auraMetrics.calm_index || 0).toFixed(3)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">HRV Norm:</span>
                  <span className="font-mono">{(auraMetrics.hrv_norm || 0).toFixed(3)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">GSR Norm:</span>
                  <span className="font-mono">{(auraMetrics.gsr_norm || 0).toFixed(3)}</span>
                </div>
              </div>
            </div>
            
            <div className="pt-4 border-t border-zinc-700">
              <div className="flex items-center justify-between">
                <Badge 
                  variant="outline" 
                  className={`text-lg px-4 py-2 ${
                    identity.role === 'Prime Sentinel (Active)' ? 'bg-green-600 text-white border-green-400' :
                    identity.role === 'Field Harmonizer' ? 'bg-blue-600 text-white border-blue-400' :
                    identity.role === 'Calibrator' ? 'bg-yellow-600 text-white border-yellow-400' :
                    'bg-gray-600 text-white border-gray-400'
                  }`}
                >
                  {identity.role}
                </Badge>
                <div className="text-right">
                  <div className="text-xs text-zinc-400">Aura Hue</div>
                  <div 
                    className="w-8 h-8 rounded-full border-2 border-white/30"
                    style={{ backgroundColor: `hsl(${auraMetrics.aura_hue_deg || 180}, 70%, 50%)` }}
                  ></div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* Aura Ring */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">🔮 Aura Field</CardTitle>
          </CardHeader>
          <CardContent>
            <AuraRingVisualizer 
              hue={auraMetrics.aura_hue_deg || 180}
              glow={auraRingGlow}
              calm={auraMetrics.calm_index || 0}
              hrv={auraMetrics.hrv_norm || 0}
              gsr={auraMetrics.gsr_norm || 0}
            />
          </CardContent>
        </Card>
        
        {/* Lattice Metrics */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between text-sm">
              📡 Lattice Nexus
              {deltaMetrics.coherence !== undefined && (
                <Badge variant="outline" className="text-xs">
                  Δ{deltaMetrics.coherence > 0 ? '+' : ''}{deltaMetrics.coherence.toFixed(3)}
                </Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-zinc-400">Coherence</span>
                <span className="font-mono text-green-400">{(aurisMetrics.coherence_score || 0).toFixed(3)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-400">Schumann Lock</span>
                <span className="font-mono text-blue-400">{(aurisMetrics.schumann_lock || 0).toFixed(3)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-400">TSV Gain</span>
                <span className="font-mono text-purple-400">{(aurisMetrics.tsv_gain || 0).toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-400">Prime Align</span>
                <span className="font-mono text-yellow-400">{(aurisMetrics.prime_alignment || 0).toFixed(3)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-400">10:9:1 Concord</span>
                <span className="font-mono text-cyan-400">{(aurisMetrics.ten_nine_one_concordance || 0).toFixed(3)}</span>
              </div>
            </div>
            
            {/* Delta indicators */}
            <div className="pt-2 border-t border-zinc-700 space-y-1">
              <DeltaIndicator value={deltaMetrics.coherence} label="ΔCoherence" />
              <DeltaIndicator value={deltaMetrics.lock} label="ΔLock" />
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* Quick Status Bar */}
      <Card>
        <CardContent className="py-3">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-6">
              <span className="text-zinc-400">Session Status:</span>
              <Badge variant={connected ? "default" : "secondary"}>
                {connected ? "🟢 Live Validation Active" : "⚪ Offline Mode"}
              </Badge>
              <span className="text-zinc-400">|</span>
              <span className="font-mono">
                Identity: {identity.name ? '✓' : '⚠'} | 
                Intent: ✓ | 
                Metrics: {connected ? '✓' : '⚠'}
              </span>
            </div>
            <div className="flex items-center gap-4 text-xs font-mono">
              <span>Coherence: {(aurisMetrics.coherence_score || 0).toFixed(3)}</span>
              <span>Calm: {(auraMetrics.calm_index || 0).toFixed(3)}</span>
              <span>Role: {identity.role}</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
