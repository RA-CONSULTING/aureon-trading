/**
 * Auris Stream Exporter - Formats data for Python validator
 */

export interface AurisStreamData {
  ts: string;                    // ISO-8601 timestamp
  site_id: string;               // site identifier
  lattice_id: string;            // Prime Seal ID
  sr: number;                    // sample rate (Hz)
  samples: number[];             // signal window
  gain: number;                  // current UI gain
  intent: number[];              // 10-9-1 vector
  targets_hz: number[];          // Schumann harmonics
}

export class AurisStreamExporter {
  private streamBuffer: AurisStreamData[] = [];
  private isExporting = false;
  
  constructor(private maxBufferSize = 100) {}

  /**
   * Generate signal samples for intent
   */
  generateSamples(intent: string, sampleRate = 200, duration = 2.0): number[] {
    const numSamples = Math.floor(sampleRate * duration);
    const samples: number[] = [];
    const currentTime = Date.now() / 1000;
    
    for (let i = 0; i < numSamples; i++) {
      const t = (i / sampleRate) + currentTime * 0.01;
      let amplitude = 0;
      
      // Map intents to frequencies
      if (intent.includes('peace')) {
        amplitude += 0.7 * Math.sin(2 * Math.PI * 7.83 * t);
      }
      if (intent.includes('joy')) {
        amplitude += 0.5 * Math.sin(2 * Math.PI * 14.3 * t);
      }
      if (intent.includes('love')) {
        amplitude += 0.6 * Math.sin(2 * Math.PI * 10.0 * t);
      }
      if (intent.includes('unity')) {
        amplitude += 0.8 * Math.sin(2 * Math.PI * 20.8 * t);
      }
      if (intent.includes('flow')) {
        amplitude += 0.4 * Math.sin(2 * Math.PI * 12.5 * t);
      }
      if (intent.includes('anchor')) {
        amplitude += 0.9 * Math.sin(2 * Math.PI * 6.5 * t);
      }
      
      // Add harmonics and modulation
      amplitude += 0.2 * Math.sin(2 * Math.PI * 26.7 * t);
      amplitude *= (1 + 0.15 * Math.sin(2 * Math.PI * 0.3 * t));
      
      // Add realistic noise
      amplitude += 0.05 * (Math.random() - 0.5);
      
      samples.push(Math.max(-1, Math.min(1, amplitude * 0.6)));
    }
    
    return samples;
  }

  /**
   * Convert intent string to 10-9-1 vector
   */
  intentToVector(intent: string): number[] {
    const baseVector = [10, 9, 1];
    
    // Modify based on intent components
    if (intent.includes('unity')) baseVector[0] += 2;
    if (intent.includes('flow')) baseVector[1] += 1;
    if (intent.includes('anchor')) baseVector[2] += 1;
    if (intent.includes('love')) {
      baseVector[0] += 1;
      baseVector[1] += 1;
    }
    
    return baseVector;
  }

  /**
   * Add sample to stream
   */
  addSample(intent: string, gain = 1.0, siteId = "EARTH-01"): void {
    const sample: AurisStreamData = {
      ts: new Date().toISOString(),
      site_id: siteId,
      lattice_id: "Φ•Gaia•02111991•10:9:1",
      sr: 200,
      samples: this.generateSamples(intent, 200, 2.0),
      gain: gain,
      intent: this.intentToVector(intent),
      targets_hz: [7.83, 14.3, 20.8, 27.3, 33.8]
    };
    
    this.streamBuffer.push(sample);
    
    // Maintain buffer size
    if (this.streamBuffer.length > this.maxBufferSize) {
      this.streamBuffer.shift();
    }
  }

  /**
   * Export as newline-delimited JSON
   */
  exportAsNDJSON(): string {
    return this.streamBuffer
      .map(sample => JSON.stringify(sample))
      .join('\n');
  }

  /**
   * Start continuous export to console
   */
  startConsoleExport(intervalMs = 1200): void {
    if (this.isExporting) return;
    
    this.isExporting = true;
    console.log('🎵 Auris Stream Export Started');
    
    const exportInterval = setInterval(() => {
      if (!this.isExporting) {
        clearInterval(exportInterval);
        return;
      }
      
      if (this.streamBuffer.length > 0) {
        const latest = this.streamBuffer[this.streamBuffer.length - 1];
        console.log(JSON.stringify(latest));
      }
    }, intervalMs);
  }

  /**
   * Stop export
   */
  stopExport(): void {
    this.isExporting = false;
    console.log('🎵 Auris Stream Export Stopped');
  }

  /**
   * Download as file
   */
  downloadAsFile(filename = 'auris_stream.jsonl'): void {
    const content = this.exportAsNDJSON();
    const blob = new Blob([content], { type: 'application/jsonl' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  /**
   * Get buffer stats
   */
  getStats() {
    return {
      bufferSize: this.streamBuffer.length,
      isExporting: this.isExporting,
      latestTimestamp: this.streamBuffer.length > 0 
        ? this.streamBuffer[this.streamBuffer.length - 1].ts 
        : null
    };
  }
}