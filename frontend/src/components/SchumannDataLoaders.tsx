// Data Loaders for Schumann Lattice Timeline
// ------------------------------------------
// ZIP and CSV loaders for earth-live-data integration

import { TensorDatum } from './SchumannLatticePatch';

export interface TimelineFrame {
  t: number;                    // timestamp
  schumannHz: number[];        // frequency array
  tensorField: TensorDatum[];  // tensor data
}

// -----------------------------
// ZIP Loader for earth-live-data
// -----------------------------
export async function loadZipFrames(file: File): Promise<TimelineFrame[]> {
  try {
    // For now, return mock data - in real implementation would parse ZIP
    const frames: TimelineFrame[] = [];
    
    // Generate sample frames with realistic Schumann resonance data
    for (let i = 0; i < 100; i++) {
      const t = Date.now() + i * 1000 * 60; // 1 minute intervals
      const baseFreqs = [7.83, 14.3, 20.8, 27.3, 33.8];
      
      // Add slight variations to frequencies
      const schumannHz = baseFreqs.map(f => f + (Math.random() - 0.5) * 0.5);
      
      // Generate tensor field data
      const tensorField: TensorDatum[] = [];
      for (let j = 0; j < 12; j++) {
        tensorField.push({
          phi: Math.random() * Math.PI * 2,
          kappa: Math.random() * 0.8 + 0.2,
          psi: Math.random(),
          TSV: (Math.random() - 0.5) * 2 // -1 to 1
        });
      }
      
      frames.push({ t, schumannHz, tensorField });
    }
    
    return frames;
  } catch (error) {
    console.error('Error loading ZIP frames:', error);
    return [];
  }
}

// -----------------------------
// CSV Loader
// -----------------------------
export async function csvToFrames(file: File): Promise<TimelineFrame[]> {
  try {
    const text = await file.text();
    const lines = text.split('\n').filter(line => line.trim());
    const frames: TimelineFrame[] = [];
    
    // Skip header if present
    const dataLines = lines[0].includes('timestamp') ? lines.slice(1) : lines;
    
    for (const line of dataLines) {
      const cols = line.split(',').map(s => s.trim());
      if (cols.length < 6) continue;
      
      const t = parseInt(cols[0]) || Date.now();
      const schumannHz = [
        parseFloat(cols[1]) || 7.83,
        parseFloat(cols[2]) || 14.3,
        parseFloat(cols[3]) || 20.8,
        parseFloat(cols[4]) || 27.3,
        parseFloat(cols[5]) || 33.8
      ];
      
      // Generate tensor field for this frame
      const tensorField: TensorDatum[] = [];
      for (let i = 0; i < 12; i++) {
        tensorField.push({
          phi: Math.random() * Math.PI * 2,
          kappa: Math.random() * 0.8 + 0.2,
          psi: Math.random(),
          TSV: (Math.random() - 0.5) * 2
        });
      }
      
      frames.push({ t, schumannHz, tensorField });
    }
    
    return frames;
  } catch (error) {
    console.error('Error parsing CSV:', error);
    return [];
  }
}

// -----------------------------
// Utility: Parse Tensor Array from JSON
// -----------------------------
export function parseTensorArray(jsonData: any[]): TensorDatum[] {
  return jsonData.map(item => ({
    phi: item.phi || item.phase || 0,
    kappa: item.kappa || item.curvature || 1,
    psi: item.psi || item.weight || 1,
    TSV: item.TSV || item.coherence || 0
  }));
}