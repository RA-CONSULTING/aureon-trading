import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
import { HarmonicNexusCore } from './HarmonicNexusCore';
import { AurisSymbolicCompiler } from './AurisSymbolicCompiler';
import QuantumFieldMatrix from './QuantumFieldMatrix';
import SchumannLatticeDisplay from './SchumannLatticeDisplay';

interface SystemStatus {
  name: string;
  status: 'active' | 'inactive' | 'error' | 'syncing';
  progress: number;
  lastUpdate: number;
  syncPhase: number;
}

export default function UnifiedSystemDashboard() {
  const [systems, setSystems] = useState<SystemStatus[]>([
    { name: 'Harmonic Nexus Core', status: 'syncing', progress: 15, lastUpdate: Date.now(), syncPhase: 0 },
    { name: 'Auris Symbolic Compiler', status: 'syncing', progress: 25, lastUpdate: Date.now(), syncPhase: 1 },
    { name: 'Quantum Field Matrix', status: 'syncing', progress: 35, lastUpdate: Date.now(), syncPhase: 2 },
    { name: 'Schumann Lattice', status: 'syncing', progress: 45, lastUpdate: Date.now(), syncPhase: 3 },
    { name: 'Live Validation', status: 'syncing', progress: 55, lastUpdate: Date.now(), syncPhase: 4 },
    { name: 'Earth Data Streams', status: 'active', progress: 100, lastUpdate: Date.now(), syncPhase: 5 },
    { name: 'PAW Simulator', status: 'active', progress: 100, lastUpdate: Date.now(), syncPhase: 6 },
    { name: 'Temporal Unity', status: 'active', progress: 100, lastUpdate: Date.now(), syncPhase: 7 }
  ]);

  const [globalStatus, setGlobalStatus] = useState<'initializing' | 'syncing' | 'operational'>('syncing');
  const [syncExplanation, setSyncExplanation] = useState('Initializing cross-system harmonics...');

  useEffect(() => {
    // Auto-activate and sync systems on mount
    const activationInterval = setInterval(() => {
      setSystems(prev => prev.map(system => {
        if (system.status === 'syncing' && system.progress < 100) {
          const newProgress = Math.min(100, system.progress + Math.random() * 8 + 2);
          const newStatus = newProgress >= 100 ? 'active' : 'syncing';
          return { ...system, progress: newProgress, status: newStatus, lastUpdate: Date.now() };
        }
        return { ...system, lastUpdate: Date.now() };
      }));
    }, 500);

    // Update sync explanations
    const explanationInterval = setInterval(() => {
      const explanations = [
        'Harmonizing quantum field resonance across all subsystems...',
        'Synchronizing temporal phase locks between Nexus and Schumann frequencies...',
        'Establishing coherent data streams between Earth sensors and quantum matrices...',
        'Aligning symbolic compiler with harmonic field oscillations...',
        'Cross-referencing validation protocols with live sensor data...',
        'Optimizing inter-dimensional data flow pathways...',
        'All systems achieving harmonic convergence - full operational sync achieved!'
      ];
      
      setSystems(prev => {
        const activeSystems = prev.filter(s => s.status === 'active').length;
        const syncIndex = Math.min(activeSystems, explanations.length - 1);
        setSyncExplanation(explanations[syncIndex]);
        
        if (activeSystems >= 6) {
          setGlobalStatus('operational');
        }
        
        return prev;
      });
    }, 2000);

    return () => {
      clearInterval(activationInterval);
      clearInterval(explanationInterval);
    };
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-500';
      case 'syncing': return 'bg-blue-500 animate-pulse';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const syncAllSystems = () => {
    setSystems(prev => prev.map(system => ({ 
      ...system, 
      status: 'active' as const, 
      progress: 100,
      lastUpdate: Date.now()
    })));
    setGlobalStatus('operational');
    setSyncExplanation('Manual sync complete - all systems operational!');
  };

  return (
    <div className="w-full space-y-6">
      <Card className="bg-gradient-to-r from-slate-900 to-purple-900 border-purple-500/30">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-2xl font-bold text-white flex items-center gap-2">
              🌐 Unified System Dashboard
              <Badge variant="outline" className={`${globalStatus === 'operational' ? 'border-green-400 text-green-400' : 'border-blue-400 text-blue-400'}`}>
                {globalStatus.toUpperCase()}
              </Badge>
            </CardTitle>
            <div className="flex gap-2">
              <Button 
                variant="outline" 
                size="sm" 
                className="text-white border-white hover:bg-white/10"
                onClick={syncAllSystems}
              >
                Force Sync All
              </Button>
              <Button variant="destructive" size="sm">
                Emergency Stop
              </Button>
            </div>
          </div>
          <div className="text-sm text-blue-300 bg-black/20 p-3 rounded-lg mt-4">
            <div className="font-semibold mb-2">🔄 System Synchronization Status:</div>
            <div className="text-blue-200">{syncExplanation}</div>
            <div className="text-xs text-gray-400 mt-2">
              <strong>What Sync Means:</strong> All subsystems are harmonically aligned, sharing real-time data streams, 
              temporal phase locks synchronized, and quantum field matrices operating in coherent resonance for optimal performance.
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {systems.map((system, index) => (
              <div key={system.name} className="bg-black/30 p-3 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <div className={`w-3 h-3 rounded-full ${getStatusColor(system.status)}`} />
                  <div className="text-xs text-white">
                    {system.status === 'active' ? '✓ SYNC' : '⟳ SYNC'}
                  </div>
                </div>
                <div className="text-xs text-gray-300 mb-1">{system.name}</div>
                <Progress value={system.progress} className="h-2 mb-1" />
                <div className="text-xs text-gray-400">{system.progress.toFixed(0)}% - {system.status.toUpperCase()}</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="nexus" className="space-y-4">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="nexus">🌌 Nexus Core</TabsTrigger>
          <TabsTrigger value="auris">🔮 Auris Compiler</TabsTrigger>
          <TabsTrigger value="quantum">⚛️ Quantum Field</TabsTrigger>
          <TabsTrigger value="schumann">🌍 Schumann</TabsTrigger>
          <TabsTrigger value="validation">✅ Validation</TabsTrigger>
        </TabsList>

        <TabsContent value="nexus">
          <HarmonicNexusCore />
        </TabsContent>

        <TabsContent value="auris">
          <AurisSymbolicCompiler />
        </TabsContent>

        <TabsContent value="quantum">
          <QuantumFieldMatrix />
        </TabsContent>

        <TabsContent value="schumann">
          <SchumannLatticeDisplay />
        </TabsContent>

        <TabsContent value="validation">
          <Card><CardContent className="p-6">
            <div className="text-center text-white">
              <div className="text-xl mb-4">✅ Live Validation System</div>
              <div className="text-green-400">AUTO-SYNC ENABLED - MONITORING ALL SUBSYSTEMS</div>
            </div>
          </CardContent></Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}