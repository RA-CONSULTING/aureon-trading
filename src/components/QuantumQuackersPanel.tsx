/**
 * Quantum Quackers Panel - Technicolor Protocol interface
 */

import { useState, useEffect, useCallback, useReducer, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Sparkles, Zap, Activity, Radio } from 'lucide-react';
import { HarmonicKeyboard, type HarmonicNote } from './HarmonicKeyboard';
import { temporalLadder, SYSTEMS } from '@/core/temporalLadder';
import { QuackersEventType, buildBroadcast, HarmonicResonancePayload, AbsurdityDeploymentPayload } from '@/core/quackersEvents';

export interface QuantumState {
  coherence: number;
  entanglement: number;
  superposition: number;
  decoherenceTime: number;
  waveFunction: number[];
  dominantFrequency: number | null;
}

export type FieldModulation = 'constructive' | 'destructive' | 'neutral';

export interface QuackerResponse {
  timestamp: number;
  inputFrequency: number;
  outputCoherence: number;
  resonanceAmplification: number;
  fieldModulation: FieldModulation;
}

const WAVE_SLOTS = 10;
const COHERENCE_FLOOR = 0.3;
const ENTANGLEMENT_FLOOR = 0.2;
const BROADCAST_TIME_THRESHOLD = 1500;
const BROADCAST_COHERENCE_DELTA = 0.02;

interface NoteAction {
  type: 'note_input';
  frequency: number;
  resonance: number;
}

interface ChordAction {
  type: 'chord_input';
  coherenceBoost: number;
  entanglementBoost: number;
  superpositionBoost: number;
  dominantFrequency: number;
}

interface EvolveAction {
  type: 'evolve';
}

type QuantumAction = NoteAction | ChordAction | EvolveAction;

export function QuantumQuackersPanel() {
  const [quantumState, dispatchQuantumState] = useReducer(
    quantumStateReducer,
    undefined,
    createInitialQuantumState
  );
  const [isActive, setIsActive] = useState(false);
  const [responses, setResponses] = useState<QuackerResponse[]>([]);
  const [ladderHealth, setLadderHealth] = useState(0);
  const animationFrameRef = useRef<number | null>(null);
  const lastBroadcastTimeRef = useRef(0);
  const lastBroadcastCoherenceRef = useRef(quantumState.coherence);

  useEffect(() => {
    temporalLadder.registerSystem(SYSTEMS.QUANTUM_QUACKERS);
    const unsubscribe = temporalLadder.subscribe(state => {
      setLadderHealth(state.hiveMindCoherence);
    });
    return () => {
      temporalLadder.unregisterSystem(SYSTEMS.QUANTUM_QUACKERS);
      unsubscribe();
    };
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      temporalLadder.heartbeat(SYSTEMS.QUANTUM_QUACKERS, quantumState.coherence);
    }, 2000);
    return () => clearInterval(interval);
  }, [quantumState.coherence]);

  useEffect(() => {
    if (!isActive) {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }
      return;
    }

    const step = () => {
      dispatchQuantumState({ type: 'evolve' });
      animationFrameRef.current = requestAnimationFrame(step);
    };

    animationFrameRef.current = requestAnimationFrame(step);

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }
    };
  }, [isActive]);

  const handleNotePlay = useCallback((note: HarmonicNote) => {
    const resonance = calculateResonance(note.frequency, quantumState);
    const fieldModulation: FieldModulation = resonance > 0.7 ? 'constructive' :
      resonance < 0.3 ? 'destructive' : 'neutral';

    const action: NoteAction = { type: 'note_input', frequency: note.frequency, resonance };
    const nextState = quantumStateReducer(quantumState, action);
    dispatchQuantumState(action);

    const response: QuackerResponse = {
      timestamp: Date.now(),
      inputFrequency: note.frequency,
      outputCoherence: nextState.coherence,
      resonanceAmplification: resonance,
      fieldModulation
    };
    setResponses(prev => [...prev.slice(-19), response]);

    const now = Date.now();
    const coherenceDelta = Math.abs(nextState.coherence - lastBroadcastCoherenceRef.current);
    const timeDelta = now - lastBroadcastTimeRef.current;
    if (coherenceDelta > BROADCAST_COHERENCE_DELTA || timeDelta > BROADCAST_TIME_THRESHOLD) {
      const payload: HarmonicResonancePayload = {
        frequency: note.frequency,
        coherence: nextState.coherence,
        resonance
      };
      const broadcast = buildBroadcast(SYSTEMS.QUANTUM_QUACKERS, QuackersEventType.HarmonicResonance, payload);
      if (broadcast) {
        temporalLadder.broadcast(SYSTEMS.QUANTUM_QUACKERS, broadcast.type, broadcast.payload);
        lastBroadcastCoherenceRef.current = nextState.coherence;
        lastBroadcastTimeRef.current = now;
      }
    }

    if (fieldModulation === 'destructive' && nextState.coherence < 0.5) {
      const absurdPayload: AbsurdityDeploymentPayload = {
        trigger: 'destructive_modulation',
        coherence: nextState.coherence,
        fieldModulation,
        injection: 'duck_intrusion_protocol_v1'
      };
      const broadcast = buildBroadcast(
        SYSTEMS.QUANTUM_QUACKERS,
        QuackersEventType.AbsurdityDeployment,
        absurdPayload
      );
      if (broadcast) {
        temporalLadder.broadcast(SYSTEMS.QUANTUM_QUACKERS, broadcast.type, broadcast.payload);
      }
    }
  }, [quantumState]);

  const handleChordPlay = useCallback((notes: HarmonicNote[]) => {
    const avgFreq = notes.reduce((sum, note) => sum + note.frequency, 0) / notes.length;
    const interference = notes.length * 0.15;

    const action: ChordAction = {
      type: 'chord_input',
      coherenceBoost: interference,
      entanglementBoost: interference * 0.8,
      superpositionBoost: interference * 0.5,
      dominantFrequency: avgFreq
    };
    const nextState = quantumStateReducer(quantumState, action);
    dispatchQuantumState(action);

    if (nextState.coherence > 0.9) {
      temporalLadder.requestAssistance(
        SYSTEMS.QUANTUM_QUACKERS,
        SYSTEMS.NEXUS_FEED,
        'high_coherence_amplification'
      );
    }
  }, [quantumState]);

  const toggleActive = () => {
    setIsActive(prev => !prev);
    const type = !isActive ? QuackersEventType.SystemActivated : QuackersEventType.SystemDeactivated;
    const broadcast = buildBroadcast(SYSTEMS.QUANTUM_QUACKERS, type, {});
    if (broadcast) {
      temporalLadder.broadcast(SYSTEMS.QUANTUM_QUACKERS, broadcast.type, broadcast.payload);
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
                <Badge variant={isActive ? 'default' : 'secondary'}>
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
                isActive ? 'bg-purple-500 hover:bg-purple-600' : 'bg-gray-600 hover:bg-gray-700'
              }`}
            >
              {isActive ? 'Deactivate' : 'Activate'}
            </button>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard icon={Activity} label="Coherence" value={quantumState.coherence} border="border-purple-500/30" />
            <MetricCard icon={Zap} label="Entanglement" value={quantumState.entanglement} border="border-cyan-500/30" />
            <MetricCard icon={Radio} label="Superposition" value={quantumState.superposition} border="border-green-500/30" />
            <MetricCard icon={Sparkles} label="Ladder Health" value={ladderHealth} border="border-orange-500/30" />
          </div>

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

          {responses.length > 0 && (
            <div className="bg-black/40 p-4 rounded-lg border border-border/30">
              <h3 className="text-sm font-semibold mb-3">Recent Harmonic Responses</h3>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {responses.slice(-5).reverse().map((resp, i) => (
                  <div key={i} className="flex items-center justify-between text-xs p-2 bg-black/30 rounded">
                    <span>{resp.inputFrequency.toFixed(2)} Hz</span>
                    <Badge
                      variant="outline"
                      className={
                        resp.fieldModulation === 'constructive'
                          ? 'border-green-500'
                          : resp.fieldModulation === 'destructive'
                            ? 'border-red-500'
                            : 'border-gray-500'
                      }
                    >
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

      <HarmonicKeyboard onNotePlay={handleNotePlay} onChordPlay={handleChordPlay} disabled={!isActive} />
    </div>
  );
}

interface MetricCardProps {
  icon: typeof Activity;
  label: string;
  value: number;
  border: string;
}

function MetricCard({ icon: Icon, label, value, border }: MetricCardProps) {
  return (
    <div className={`bg-black/40 p-4 rounded-lg border ${border}`}>
      <div className="flex items-center gap-2 mb-2">
        <Icon className="w-4 h-4 text-purple-400" />
        <span className="text-xs text-muted-foreground">{label}</span>
      </div>
      <Progress value={value * 100} className="h-2 mb-1" />
      <span className="text-lg font-bold">{(value * 100).toFixed(1)}%</span>
    </div>
  );
}

function calculateResonance(frequency: number, state: QuantumState): number {
  const schumannHarmonics = [7.83, 14.3, 20.8, 27.3, 33.8, 39.0, 45.0];
  const schumannResonance = schumannHarmonics.reduce((max, harmonic) => {
    const alignment = 1 - Math.min(1, Math.abs(frequency - harmonic) / harmonic);
    return Math.max(max, alignment);
  }, 0);

  const solfeggioFreqs = [396, 417, 528, 639, 741, 852];
  const solfeggioResonance = solfeggioFreqs.reduce((max, solfeggio) => {
    const alignment = 1 - Math.min(1, Math.abs(frequency - solfeggio) / solfeggio);
    return Math.max(max, alignment);
  }, 0);

  const baseResonance = Math.max(schumannResonance, solfeggioResonance);
  const stateModulation = (state.coherence + state.entanglement + state.superposition) / 3;

  return Math.min(1, baseResonance * (0.5 + stateModulation * 0.5));
}

function createInitialQuantumState(): QuantumState {
  return {
    coherence: 0.75,
    entanglement: 0.5,
    superposition: 0.6,
    decoherenceTime: 1000,
    waveFunction: createUniformWaveFunction(),
    dominantFrequency: null
  };
}

function quantumStateReducer(state: QuantumState, action: QuantumAction): QuantumState {
  switch (action.type) {
    case 'evolve':
      return {
        ...state,
        coherence: Math.max(COHERENCE_FLOOR, state.coherence - 0.01),
        entanglement: Math.max(ENTANGLEMENT_FLOOR, state.entanglement - 0.005),
        waveFunction: evolveWaveFunction(state.waveFunction)
      };
    case 'note_input':
      return {
        ...state,
        coherence: Math.min(1, state.coherence + action.resonance * 0.3),
        entanglement: Math.min(1, state.entanglement + action.resonance * 0.2),
        superposition: Math.min(1, state.superposition + action.resonance * 0.1),
        dominantFrequency: action.frequency,
        waveFunction: exciteWaveFunction(state.waveFunction, action.frequency, action.resonance)
      };
    case 'chord_input':
      return {
        ...state,
        coherence: Math.min(1, state.coherence + action.coherenceBoost),
        entanglement: Math.min(1, state.entanglement + action.entanglementBoost),
        superposition: Math.min(1, state.superposition + action.superpositionBoost),
        dominantFrequency: action.dominantFrequency
      };
    default:
      return state;
  }
}

function createUniformWaveFunction(): number[] {
  const amplitude = 1 / WAVE_SLOTS;
  return Array.from({ length: WAVE_SLOTS }, () => amplitude);
}

function evolveWaveFunction(current: number[]): number[] {
  const next = current.map(amp => {
    const noise = (Math.random() - 0.5) * 0.02;
    return Math.max(0, Math.min(1, amp + noise));
  });
  return normalizeWaveFunction(next);
}

function exciteWaveFunction(current: number[], frequency: number, resonance: number): number[] {
  const slotSize = 100 / WAVE_SLOTS;
  const normalizedFreq = ((frequency % 100) + 100) % 100;
  const freqIndex = Math.min(WAVE_SLOTS - 1, Math.floor(normalizedFreq / slotSize));

  const next = current.map((amp, index) => {
    if (index === freqIndex) {
      return Math.min(1, amp + resonance * 0.5);
    }
    return amp * 0.95;
  });

  return normalizeWaveFunction(next);
}

function normalizeWaveFunction(wave: number[]): number[] {
  const sum = wave.reduce((acc, value) => acc + value, 0);
  if (sum <= 0) {
    return createUniformWaveFunction();
  }
  return wave.map(amp => amp / sum);
}
