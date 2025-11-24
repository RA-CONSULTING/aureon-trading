// src/lib/tri-timeline-blender.ts
// TypeScript equivalent of Unity TriTimelineBlender.cs for web integration

import { SchumannFrame, TensorDatum, TriWeights } from './nexus-models';

export class TriTimelineBlender {
  private static clamp01(x: number): number {
    return Math.max(0, Math.min(1, x));
  }

  /**
   * Pick the prime frame from an array based on observer phase lock
   */
  static pickPrime(frames: SchumannFrame[], anchorPhase: number): SchumannFrame | null {
    if (!frames || frames.length === 0) return null;

    const score = (frame: SchumannFrame): number => {
      const tf = frame.tensorField;
      if (!tf || tf.length === 0) return 0;

      // Calculate mean phase and coherence
      const meanPhi = tf.reduce((sum, d) => sum + d.phi, 0) / tf.length;
      const dphi = Math.acos(Math.cos(meanPhi - anchorPhase)); // wrap-safe difference
      const meanPsi = tf.reduce((sum, d) => sum + Math.abs(d.psi), 0) / tf.length;
      
      const phaseScore = 1 - (dphi / Math.PI);     // 0..1
      const cohScore = 0.6 + 0.4 * this.clamp01(meanPsi);
      
      return phaseScore * cohScore;
    };

    let bestIndex = 0;
    let bestScore = -1;
    
    for (let i = 0; i < frames.length; i++) {
      const s = score(frames[i]);
      if (s > bestScore) {
        bestScore = s;
        bestIndex = i;
      }
    }

    return frames[bestIndex];
  }

  /**
   * Blend three frames into one unified frame
   */
  static blend(
    a: SchumannFrame | null, 
    b: SchumannFrame | null, 
    c: SchumannFrame | null, 
    weights: TriWeights
  ): SchumannFrame {
    // Normalize weights
    const sumW = weights.past + weights.present + weights.future;
    const normalizedWeights = sumW > 1e-6 ? {
      past: weights.past / sumW,
      present: weights.present / sumW,
      future: weights.future / sumW
    } : { past: 1/3, present: 1/3, future: 1/3 };

    // Find longest frequency array
    const lengths = [
      a?.schumannHz?.length ?? 0,
      b?.schumannHz?.length ?? 0,
      c?.schumannHz?.length ?? 0
    ];
    const longest = Math.max(...lengths) || 1;

    // Blend frequencies
    const hz: number[] = [];
    for (let i = 0; i < longest; i++) {
      const av = a?.schumannHz ? (i < a.schumannHz.length ? a.schumannHz[i] : a.schumannHz[a.schumannHz.length - 1]) : 0;
      const bv = b?.schumannHz ? (i < b.schumannHz.length ? b.schumannHz[i] : b.schumannHz[b.schumannHz.length - 1]) : 0;
      const cv = c?.schumannHz ? (i < c.schumannHz.length ? c.schumannHz[i] : c.schumannHz[c.schumannHz.length - 1]) : 0;
      
      hz[i] = av * normalizedWeights.past + bv * normalizedWeights.present + cv * normalizedWeights.future;
    }

    // Blend tensor fields
    const tensorField: TensorDatum[] = [];
    
    if (a?.tensorField) {
      a.tensorField.forEach(d => tensorField.push({
        phi: d.phi,
        psi: d.psi * normalizedWeights.past,
        TSV: d.TSV
      }));
    }
    
    if (b?.tensorField) {
      b.tensorField.forEach(d => tensorField.push({
        phi: d.phi,
        psi: d.psi * normalizedWeights.present,
        TSV: d.TSV
      }));
    }
    
    if (c?.tensorField) {
      c.tensorField.forEach(d => tensorField.push({
        phi: d.phi,
        psi: d.psi * normalizedWeights.future,
        TSV: d.TSV
      }));
    }

    // Create label
    const labels = [a?.t, b?.t, c?.t].filter(Boolean);
    const label = labels.join(' ⊕ ') || 'unified';

    return {
      t: label,
      schumannHz: hz,
      tensorField
    };
  }
}