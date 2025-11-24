/**
 * Hive Mind Integration Page
 * Prime Sentinel: GARY LECKEY 02111991
 * 
 * Demonstrates the complete temporal ladder chain-link system where
 * every program knows about the hive mind and can fall back on each other.
 */

import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Network, Zap, Activity, Radio } from 'lucide-react';
import { QuantumQuackersPanel } from '@/components/QuantumQuackersPanel';
import { TemporalLadderDashboard } from '@/components/TemporalLadderDashboard';
import { HarmonicNexusMonitor } from '@/components/HarmonicNexusMonitor';
import { EarthResonanceDashboard } from '@/components/EarthResonanceDashboard';

export default function HiveMindIntegrationPage() {
  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent">
          Hive Mind Integration
        </h1>
        <p className="text-muted-foreground max-w-2xl mx-auto">
          Temporal ladder chain-link system where every component maintains awareness 
          of the collective network and can fall back on sibling systems for support.
        </p>
        <div className="flex gap-2 justify-center">
          <Badge variant="outline" className="gap-1">
            <Network className="w-3 h-3" />
            Chain-Linked
          </Badge>
          <Badge variant="outline" className="gap-1">
            <Activity className="w-3 h-3" />
            Live Fallback
          </Badge>
          <Badge variant="outline" className="gap-1">
            <Radio className="w-3 h-3" />
            Hive Awareness
          </Badge>
        </div>
      </div>

      {/* System Architecture Overview */}
      <Card className="bg-gradient-to-br from-purple-900/20 via-black to-indigo-900/20 border-purple-500/30">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-purple-400" />
            Temporal Ladder Architecture
          </CardTitle>
          <CardDescription>
            Hierarchical system coordination with automatic failover
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-6">
            {/* Left: System Hierarchy */}
            <div className="space-y-3">
              <h3 className="text-sm font-semibold mb-3">System Hierarchy (Priority Order)</h3>
              <div className="space-y-2 font-mono text-sm">
                {[
                  { level: 1, name: 'harmonic-nexus', desc: 'Reality substrate authority' },
                  { level: 2, name: 'master-equation', desc: 'Ω field orchestrator' },
                  { level: 3, name: 'earth-integration', desc: 'Schumann/geomagnetic streams' },
                  { level: 4, name: 'nexus-feed', desc: 'Coherence boost provider' },
                  { level: 5, name: 'quantum-quackers', desc: 'Quantum state modulation' },
                  { level: 6, name: 'akashic-mapper', desc: 'Frequency harmonics' },
                  { level: 7, name: 'zero-point', desc: 'Field harmonic detection' },
                  { level: 8, name: 'dimensional-dialler', desc: 'Drift correction' },
                ].map(sys => (
                  <div key={sys.name} className="flex items-center gap-3 p-2 bg-black/30 rounded">
                    <Badge variant="outline" className="text-xs">{sys.level}</Badge>
                    <div className="flex-1">
                      <div className="text-indigo-400">{sys.name}</div>
                      <div className="text-xs text-muted-foreground">{sys.desc}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Right: Features */}
            <div className="space-y-4">
              <h3 className="text-sm font-semibold mb-3">Key Features</h3>
              
              <div className="p-3 bg-green-500/10 rounded-lg border border-green-500/30">
                <div className="flex items-center gap-2 mb-2">
                  <Network className="w-4 h-4 text-green-400" />
                  <span className="text-sm font-semibold">Hive Mind Awareness</span>
                </div>
                <p className="text-xs text-muted-foreground">
                  Every system knows about every other system's health, status, and capabilities 
                  through real-time heartbeat monitoring.
                </p>
              </div>

              <div className="p-3 bg-orange-500/10 rounded-lg border border-orange-500/30">
                <div className="flex items-center gap-2 mb-2">
                  <Activity className="w-4 h-4 text-orange-400" />
                  <span className="text-sm font-semibold">Automatic Failover</span>
                </div>
                <p className="text-xs text-muted-foreground">
                  When a system's health degrades below threshold (30%), the temporal ladder 
                  automatically activates the next system in the fallback chain.
                </p>
              </div>

              <div className="p-3 bg-cyan-500/10 rounded-lg border border-cyan-500/30">
                <div className="flex items-center gap-2 mb-2">
                  <Radio className="w-4 h-4 text-cyan-400" />
                  <span className="text-sm font-semibold">Inter-System Communication</span>
                </div>
                <p className="text-xs text-muted-foreground">
                  Systems broadcast events and request assistance from siblings. For example, 
                  Quantum Quackers can request amplification from Nexus Feed during high coherence.
                </p>
              </div>

              <div className="p-3 bg-purple-500/10 rounded-lg border border-purple-500/30">
                <div className="flex items-center gap-2 mb-2">
                  <Zap className="w-4 h-4 text-purple-400" />
                  <span className="text-sm font-semibold">Coherence Monitoring</span>
                </div>
                <p className="text-xs text-muted-foreground">
                  Aggregate "Hive Mind Coherence" metric (0-100%) reflects overall system health. 
                  Calculated as average health across all active systems.
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Integration Tabs */}
      <Tabs defaultValue="ladder" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="ladder">Temporal Ladder</TabsTrigger>
          <TabsTrigger value="quantum">Quantum Quackers</TabsTrigger>
          <TabsTrigger value="nexus">Harmonic Nexus</TabsTrigger>
          <TabsTrigger value="earth">Earth Integration</TabsTrigger>
        </TabsList>

        <TabsContent value="ladder" className="space-y-4">
          <TemporalLadderDashboard />
        </TabsContent>

        <TabsContent value="quantum" className="space-y-4">
          <QuantumQuackersPanel />
          <Card className="bg-black/40 border-border/30">
            <CardContent className="pt-6">
              <p className="text-sm text-muted-foreground">
                <strong>Quantum Quackers Integration:</strong> Receives harmonic frequency input 
                from the keyboard and modulates quantum field states. Broadcasts resonance events 
                to the temporal ladder network. When coherence exceeds 90%, automatically requests 
                amplification assistance from Nexus Feed system.
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="nexus" className="space-y-4">
          <HarmonicNexusMonitor />
          <Card className="bg-black/40 border-border/30">
            <CardContent className="pt-6">
              <p className="text-sm text-muted-foreground">
                <strong>Harmonic Nexus Integration:</strong> Serves as the highest authority system 
                in the temporal ladder, maintaining reality substrate coherence. Registered as 
                'harmonic-nexus' and coordinates with Master Equation for field orchestration.
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="earth" className="space-y-4">
          <EarthResonanceDashboard />
          <Card className="bg-black/40 border-border/30">
            <CardContent className="pt-6">
              <p className="text-sm text-muted-foreground">
                <strong>Earth Integration:</strong> Provides Schumann resonance and geomagnetic 
                field data to the system. When Earth sync is disabled, automatically requests 
                assistance from Nexus Feed to maintain coherence. Sends regular heartbeats to 
                temporal ladder reflecting stream health.
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Technical Notes */}
      <Card className="bg-black/40 border-border/30">
        <CardHeader>
          <CardTitle className="text-lg">Implementation Notes</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-muted-foreground">
          <div>
            <strong className="text-foreground">Temporal Ladder Core:</strong> Singleton service 
            (<code className="text-xs bg-black/40 px-1 py-0.5 rounded">src/core/temporalLadder.ts</code>) 
            manages system registration, heartbeat monitoring, and failover coordination.
          </div>
          <div>
            <strong className="text-foreground">Harmonic Keyboard:</strong> Web Audio API-based frequency 
            generator supporting Solfeggio scale (396-852 Hz) and Schumann harmonics (7.83-45 Hz). 
            Wired directly to Quantum Quackers for real-time quantum state modulation.
          </div>
          <div>
            <strong className="text-foreground">System Integration:</strong> Earth bridge, Nexus bridge, 
            and Master Equation all register with temporal ladder on initialization and send health 
            heartbeats every 2 seconds. Health metrics (0-1) determine failover eligibility.
          </div>
          <div>
            <strong className="text-foreground">Hive Mind Protocol:</strong> Systems broadcast events 
            (<code className="text-xs bg-black/40 px-1 py-0.5 rounded">broadcast()</code>) and request 
            assistance (<code className="text-xs bg-black/40 px-1 py-0.5 rounded">requestAssistance()</code>) 
            through the temporal ladder API. All active systems receive and can respond to broadcasts.
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
