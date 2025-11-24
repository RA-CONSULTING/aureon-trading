/**
 * Quantum Quackers Panel
 * Prime Sentinel: GARY LECKEY 02111991
 * 
 * Quantum state modulation system driven by harmonic keyboard input.
 * Responds to frequency stimulation and broadcasts quantum field updates
 * across the temporal ladder network.
 */

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Sparkles, Zap, Activity, Radio } from 'lucide-react';
import { HarmonicKeyboard, type HarmonicNote } from './HarmonicKeyboard';
import { temporalLadder, SYSTEMS } from '@/core/temporalLadder';

export interface QuantumState {
  coherence: number; // 0-1
  entanglement: number; // 0-1
  superposition: number; // 0-1
  decoherenceTime: number; // ms
  waveFunction: number[]; // probability amplitudes
  dominantFrequency: number | null;
}

export interface QuackerResponse {
  timestamp: number;
  inputFrequency: number;
  outputCoherence: number;
  resonanceAmplification: number;
  fieldModulation: string; // 'constructive' | 'destructive' | 'neutral'
}

export function QuantumQuackersPanel() {
  const [quantumState, setQuantumState] = useState<QuantumState>({
    coherence: 0.75,
    entanglement: 0.5,
    superposition: 0.6,
    decoherenceTime: 1000,
    waveFunction: Array(10).fill(0.1),
    dominantFrequency: null
  });

  const [isActive, setIsActive] = useState(false);
  const [responses, setResponses] = useState<QuackerResponse[]>([]);
  const [ladderHealth, setLadderHealth] = useState(0);

  // Register with Temporal Ladder
  useEffect(() => {
    temporalLadder.registerSystem(SYSTEMS.QUANTUM_QUACKERS);
    
    // Subscribe to ladder state updates
    const unsubscribe = temporalLadder.subscribe(state => {
      setLadderHealth(state.hiveMindCoherence);
    });

    return () => {
      temporalLadder.unregisterSystem(SYSTEMS.QUANTUM_QUACKERS);
      unsubscribe();
    };
  }, []);

  // Heartbeat to Temporal Ladder
  useEffect(() => {
    const interval = setInterval(() => {
      temporalLadder.heartbeat(SYSTEMS.QUANTUM_QUACKERS, quantumState.coherence);
    }, 2000);

    return () => clearInterval(interval);
  }, [quantumState.coherence]);

  // Quantum state evolution
  useEffect(() => {
    if (!isActive) return;

    const interval = setInterval(() => {
      setQuantumState(prev => {
        // Natural decoherence
        const coherence = Math.max(0.3, prev.coherence - 0.01);
        const entanglement = Math.max(0.2, prev.entanglement - 0.005);
        
        // Wave function collapse and regeneration
        const waveFunction = prev.waveFunction.map((amp, i) => {
          const noise = (Math.random() - 0.5) * 0.02;
          return Math.max(0, Math.min(1, amp + noise));
        });

        // Normalize wave function
        const sum = waveFunction.reduce((a, b) => a + b, 0);
        const normalized = waveFunction.map(amp => amp / sum);

        return {
          ...prev,
          coherence,
          entanglement,
          waveFunction: normalized
        };
      });
    }, 100);

    return () => clearInterval(interval);
  }, [isActive]);

  // Handle harmonic input from keyboard
  const handleNotePlay = useCallback((note: HarmonicNote) => {
    console.log('🦆 Quantum Quackers received note:', note);

    // Determine resonance with quantum field
    const resonance = calculateResonance(note.frequency, quantumState);
    
    // Update quantum state based on input
    setQuantumState(prev => {
      const coherenceBoost = resonance * 0.3;
      const entanglementBoost = resonance * 0.2;
      
      // Update wave function based on frequency
      const waveFunction = prev.waveFunction.map((amp, i) => {
        const freqIndex = Math.floor((note.frequency % 100) / 10);
        if (i === freqIndex) {
          return Math.min(1, amp + resonance * 0.5);
        }
        return amp * 0.95; // slight decay for non-resonant modes
      });

      const fieldModulation = resonance > 0.7 ? 'constructive' : 
                             resonance < 0.3 ? 'destructive' : 'neutral';

      const response: QuackerResponse = {
        timestamp: Date.now(),
        inputFrequency: note.frequency,
        outputCoherence: Math.min(1, prev.coherence + coherenceBoost),
        resonanceAmplification: resonance,
        fieldModulation
      };

      setResponses(prev => [...prev.slice(-19), response]);

      // Broadcast to temporal ladder
      temporalLadder.broadcast(SYSTEMS.QUANTUM_QUACKERS, 'harmonic_resonance', {
        frequency: note.frequency,
        coherence: response.outputCoherence,
        resonance
      });

      return {
        ...prev,
        coherence: Math.min(1, prev.coherence + coherenceBoost),
        entanglement: Math.min(1, prev.entanglement + entanglementBoost),
        superposition: Math.min(1, prev.superposition + resonance * 0.1),
        dominantFrequency: note.frequency,
        waveFunction
      };
    });
  }, [quantumState]);

  // Handle chord input
  const handleChordPlay = useCallback((notes: HarmonicNote[]) => {
    console.log('🦆 Quantum Quackers received chord:', notes);

    // Calculate constructive interference
    const avgFreq = notes.reduce((sum, n) => sum + n.frequency, 0) / notes.length;
    const interference = notes.length * 0.15; // chord multiplier

    setQuantumState(prev => ({
      ...prev,
      coherence: Math.min(1, prev.coherence + interference),
      entanglement: Math.min(1, prev.entanglement + interference * 0.8),
      superposition: Math.min(1, prev.superposition + interference * 0.5),
      dominantFrequency: avgFreq
    }));

    // Request assistance from Nexus if coherence is very high
    if (quantumState.coherence + interference > 0.9) {
      temporalLadder.requestAssistance(
        SYSTEMS.QUANTUM_QUACKERS,
        SYSTEMS.NEXUS_FEED,
        'high_coherence_amplification'
      );
    }
  }, [quantumState.coherence]);

  // Toggle system activation
  const toggleActive = () => {
    setIsActive(!isActive);
    if (!isActive) {
      temporalLadder.broadcast(SYSTEMS.QUANTUM_QUACKERS, 'system_activated', {});
    } else {
      temporalLadder.broadcast(SYSTEMS.QUANTUM_QUACKERS, 'system_deactivated', {});
    }
  };

  return (
    <div className="space-y-4">
      <Card className="bg-gradient-to-br from-purple-900/20 via-black to-cyan-900/20 border-purple-500/30">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2 text-2xl">
                <Sparkles className="w-6 h-6 text-purple-400" />
                Quantum Quackers
                <Badge variant={isActive ? "default" : "secondary"}>
                  {isActive ? 'ACTIVE' : 'STANDBY'}
                </Badge>
              </CardTitle>
              <CardDescription>
                Quantum state modulation via harmonic resonance
              </CardDescription>
            </div>
            <button
              onClick={toggleActive}
              className={`px-4 py-2 rounded-lg transition-all ${
                isActive 
                  ? 'bg-purple-500 hover:bg-purple-600' 
                  : 'bg-gray-600 hover:bg-gray-700'
              }`}
            >
              {isActive ? 'Deactivate' : 'Activate'}
            </button>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Quantum State Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-black/40 p-4 rounded-lg border border-purple-500/30">
              <div className="flex items-center gap-2 mb-2">
                <Activity className="w-4 h-4 text-purple-400" />
                <span className="text-xs text-muted-foreground">Coherence</span>
              </div>
              <Progress value={quantumState.coherence * 100} className="h-2 mb-1" />
              <span className="text-lg font-bold">{(quantumState.coherence * 100).toFixed(1)}%</span>
            </div>

            <div className="bg-black/40 p-4 rounded-lg border border-cyan-500/30">
              <div className="flex items-center gap-2 mb-2">
                <Zap className="w-4 h-4 text-cyan-400" />
                <span className="text-xs text-muted-foreground">Entanglement</span>
              </div>
              <Progress value={quantumState.entanglement * 100} className="h-2 mb-1" />
              <span className="text-lg font-bold">{(quantumState.entanglement * 100).toFixed(1)}%</span>
            </div>

            <div className="bg-black/40 p-4 rounded-lg border border-green-500/30">
              <div className="flex items-center gap-2 mb-2">
                <Radio className="w-4 h-4 text-green-400" />
                <span className="text-xs text-muted-foreground">Superposition</span>
              </div>
              <Progress value={quantumState.superposition * 100} className="h-2 mb-1" />
              <span className="text-lg font-bold">{(quantumState.superposition * 100).toFixed(1)}%</span>
            </div>

            <div className="bg-black/40 p-4 rounded-lg border border-orange-500/30">
              <div className="flex items-center gap-2 mb-2">
                <Sparkles className="w-4 h-4 text-orange-400" />
                <span className="text-xs text-muted-foreground">Ladder Health</span>
              </div>
              <Progress value={ladderHealth * 100} className="h-2 mb-1" />
              <span className="text-lg font-bold">{(ladderHealth * 100).toFixed(1)}%</span>
            </div>
          </div>

          {/* Dominant Frequency Display */}
          {quantumState.dominantFrequency && (
            <div className="bg-gradient-to-r from-purple-500/10 to-cyan-500/10 p-4 rounded-lg border border-border/30">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Dominant Resonance Frequency</span>
                <Badge variant="outline" className="text-lg">
                  {quantumState.dominantFrequency.toFixed(2)} Hz
                </Badge>
              </div>
            </div>
          )}

          {/* Wave Function Visualization */}
          <div className="bg-black/40 p-4 rounded-lg border border-border/30">
            <h3 className="text-sm font-semibold mb-3">Quantum Wave Function</h3>
            <div className="flex items-end gap-1 h-24">
              {quantumState.waveFunction.map((amp, i) => (
                <div
                  key={i}
                  className="flex-1 bg-gradient-to-t from-purple-500 to-cyan-500 rounded-t transition-all duration-300"
                  style={{ height: `${amp * 100}%` }}
                  title={`State ${i}: ${(amp * 100).toFixed(1)}%`}
                />
              ))}
            </div>
          </div>

          {/* Recent Responses */}
          {responses.length > 0 && (
            <div className="bg-black/40 p-4 rounded-lg border border-border/30">
              <h3 className="text-sm font-semibold mb-3">Recent Harmonic Responses</h3>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {responses.slice(-5).reverse().map((resp, i) => (
                  <div key={i} className="flex items-center justify-between text-xs p-2 bg-black/30 rounded">
                    <span>{resp.inputFrequency.toFixed(2)} Hz</span>
                    <Badge variant="outline" className={
                      resp.fieldModulation === 'constructive' ? 'border-green-500' :
                      resp.fieldModulation === 'destructive' ? 'border-red-500' :
                      'border-gray-500'
                    }>
                      {resp.fieldModulation}
                    </Badge>
                    <span>+{(resp.resonanceAmplification * 100).toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Harmonic Keyboard Integration */}
      <HarmonicKeyboard
        onNotePlay={handleNotePlay}
        onChordPlay={handleChordPlay}
        disabled={!isActive}
      />
    </div>
  );
}

/**
 * Calculate resonance between input frequency and quantum state
 */
function calculateResonance(frequency: number, state: QuantumState): number {
  // Check for Schumann resonance alignment
  const schumannHarmonics = [7.83, 14.3, 20.8, 27.3, 33.8, 39.0, 45.0];
  const schumannResonance = schumannHarmonics.reduce((max, harmonic) => {
    const alignment = 1 - Math.min(1, Math.abs(frequency - harmonic) / harmonic);
    return Math.max(max, alignment);
  }, 0);

  // Check for Solfeggio alignment
  const solfeggioFreqs = [396, 417, 528, 639, 741, 852];
  const solfeggioResonance = solfeggioFreqs.reduce((max, solfeggio) => {
    const alignment = 1 - Math.min(1, Math.abs(frequency - solfeggio) / solfeggio);
    return Math.max(max, alignment);
  }, 0);

  // Weight by current quantum state
  const baseResonance = Math.max(schumannResonance, solfeggioResonance);
  const stateModulation = (state.coherence + state.entanglement + state.superposition) / 3;

  return Math.min(1, baseResonance * (0.5 + stateModulation * 0.5));
}
