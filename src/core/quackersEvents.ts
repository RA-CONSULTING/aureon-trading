// Quantum Quackers Event Types & Payload Definitions
// ARCHIVE ENTRY: 002-QQ // THE TECHNICOLOR PROTOCOL
// Encodes absurdity deployment doctrine into typed ladder events.
import { SystemName } from './temporalLadder';

// Canonical event type strings (stable, lowercase, kebab)
export enum QuackersEventType {
  HarmonicResonance = 'harmonic-resonance',
  SystemActivated = 'system-activated',
  SystemDeactivated = 'system-deactivated',
  AbsurdityDeployment = 'absurdity-deployment',
  FearFieldDetected = 'fear-field-detected'
}

// Payloads
export interface HarmonicResonancePayload {
  frequency: number;
  coherence: number; // post-update coherence
  resonance: number; // 0-1 raw resonance calc
}

export type AbsurdityTrigger = 'low_coherence' | 'destructive_modulation' | 'external_scenario';

export interface AbsurdityDeploymentPayload {
  trigger: AbsurdityTrigger;
  coherence: number;
  fieldModulation: 'constructive' | 'destructive' | 'neutral';
  injection: string; // symbolic descriptor of absurdity pattern
}

export interface FearFieldDetectedPayload {
  source: 'ui' | 'external' | 'telemetry';
  metric: string; // e.g. 'coherence_drop_rate'
  value: number; // magnitude
  threshold: number; // threshold crossed
}

export interface SystemLifecyclePayload { }

export type QuackersPayload =
  | HarmonicResonancePayload
  | AbsurdityDeploymentPayload
  | FearFieldDetectedPayload
  | SystemLifecyclePayload;

export interface QuackersBroadcast<T extends QuackersEventType> {
  system: SystemName;
  type: T;
  timestamp: number;
  payload: Extract<QuackersPayload,
    T extends QuackersEventType.HarmonicResonance ? HarmonicResonancePayload :
    T extends QuackersEventType.AbsurdityDeployment ? AbsurdityDeploymentPayload :
    T extends QuackersEventType.FearFieldDetected ? FearFieldDetectedPayload :
    SystemLifecyclePayload>;
}

// Size guard constants
const MAX_PAYLOAD_BYTES = 512; // conservative cap

export function validatePayloadSize(payload: unknown): boolean {
  try {
    const str = JSON.stringify(payload);
    return str.length <= MAX_PAYLOAD_BYTES;
  } catch {
    return false;
  }
}

export function buildBroadcast<T extends QuackersEventType>(system: SystemName, type: T, payload: QuackersBroadcast<T>['payload']): QuackersBroadcast<T> | null {
  if (!validatePayloadSize(payload)) {
    console.warn('Quackers payload too large; dropped', type);
    return null;
  }
  return {
    system,
    type,
    timestamp: Date.now(),
    payload
  } as QuackersBroadcast<T>;
}
