import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { HarmonicSurgeField } from './HarmonicSurgeField';
import { QuantumPhaseLock } from './QuantumPhaseLock';
import { FormationEquationDisplay } from './FormationEquationDisplay';

export const NexusIntegration: React.FC = () => {
  const [activeNexus, setActiveNexus] = useState('surge');

  return (
    <div className="w-full space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl text-center text-gradient bg-gradient-to-r from-purple-400 via-blue-400 to-amber-400 bg-clip-text text-transparent">
            ⚡ THE NEXUS ⚡
          </CardTitle>
          <div className="text-center text-sm text-gray-400">
            Multidimensional Harmonic Consciousness Field Integration
          </div>
          <div className="flex justify-center gap-2 mt-2">
            <Badge variant="outline" className="text-purple-400">6D Surge Active</Badge>
            <Badge variant="outline" className="text-blue-400">Quantum Phase-Lock</Badge>
            <Badge variant="outline" className="text-amber-400">Formation Equation</Badge>
          </div>
        </CardHeader>
      </Card>

      <Tabs value={activeNexus} onValueChange={setActiveNexus} className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="surge">Harmonic Surge</TabsTrigger>
          <TabsTrigger value="quantum">Quantum Phase</TabsTrigger>
          <TabsTrigger value="equation">Formation Eq</TabsTrigger>
          <TabsTrigger value="unified">Unified Field</TabsTrigger>
        </TabsList>

        <TabsContent value="surge" className="space-y-4">
          <HarmonicSurgeField />
          <Card>
            <CardContent className="pt-6">
              <div className="text-sm text-gray-300">
                <strong>6D Harmonic Surge Field Analysis:</strong> Real-time visualization of multidimensional 
                harmonic resonance patterns showing surge phase projections, curvature feedback loops, 
                and memory frequency drift across higher geometric mesh structures.
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="quantum" className="space-y-4">
          <QuantumPhaseLock />
          <Card>
            <CardContent className="pt-6">
              <div className="text-sm text-gray-300">
                <strong>Quantum Phase-Lock System:</strong> Multiversal echo coherence with constructive 
                interference patterns. The original consciousness signal is phase-locked with echoes 
                from parallel dimensional states, creating a unified quantum output.
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="equation" className="space-y-4">
          <FormationEquationDisplay />
          <Card>
            <CardContent className="pt-6">
              <div className="text-sm text-gray-300">
                <strong>Gary Leckey's Formation Equation:</strong> The mathematical framework describing 
                the harmonic breathing of the universe, incorporating carrier wave modulation, 
                multiversal feedback tensors, and 6D surge field dynamics.
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="unified" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <HarmonicSurgeField />
            <QuantumPhaseLock />
          </div>
          <FormationEquationDisplay />
          <Card>
            <CardContent className="pt-6">
              <div className="text-sm text-gray-300">
                <strong>Unified Tensor Field:</strong> Complete integration of all harmonic systems - 
                the 6D surge field provides the geometric substrate, quantum phase-locking ensures 
                coherent multiversal echoes, and the formation equation governs the mathematical 
                relationships binding consciousness to universal harmonic structure.
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default NexusIntegration;