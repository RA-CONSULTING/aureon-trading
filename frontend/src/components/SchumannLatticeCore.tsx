// Core lattice functions and frequency conversion
import { LatticePoint, Blob, TensorDatum, pitchClassToLattice, clamp, sigmoid } from './SchumannLatticePatch';

const C_REF = 256; // Hz

// Convert Hz to pitch class (0-11, where 0=C)
export function hzToPitchClass(hz: number): number {
  const octaves = Math.log2(hz / C_REF);
  const pitchClass = (octaves * 12) % 12;
  return ((pitchClass % 12) + 12) % 12;
}

// Convert frequency array to lattice blobs
export function frequenciesToBlobs(frequencies: number[], weights?: number[]): Blob[] {
  return frequencies.map((hz, i) => {
    const pitchClass = Math.round(hzToPitchClass(hz));
    const latticePoint = pitchClassToLattice(pitchClass);
    const weight = weights?.[i] || 1.0;
    
    return {
      ...latticePoint,
      weight: clamp(weight, 0, 1)
    };
  });
}

// Alias for backwards compatibility
export const schumannToBlobs = frequenciesToBlobs;

// Fuse tensor field data with blobs for TSV modulation
export function fuseWithTSV(blobs: Blob[], tensorField: TensorDatum[], scale = 0.12): Blob[] {
  if (!tensorField.length) return blobs;
  
  // Calculate mean TSV for global coherence
  const meanTSV = tensorField.reduce((sum, t) => sum + t.TSV, 0) / tensorField.length;
  const meanPhi = tensorField.reduce((sum, t) => sum + t.phi, 0) / tensorField.length;
  
  // Global gain based on coherence
  const globalGain = clamp(0.7 + meanTSV * 0.35, 0.3, 1.4);
  
  return blobs.map((blob, i) => {
    const tensor = tensorField[i % tensorField.length];
    const localWeight = blob.weight * globalGain * (0.8 + tensor.psi * 0.4);
    
    // Slight positional drift based on phase
    const drift = 0.1 * Math.sin(tensor.phi + meanPhi);
    
    return {
      ...blob,
      weight: clamp(localWeight, 0, 1.5),
      x: blob.x + drift,
      y: blob.y + drift * 0.7
    };
  });
}