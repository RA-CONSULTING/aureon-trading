// Earth Live Data Loader for 10-9-1 Seal Integration
export interface EarthDataManifest {
  dataset: string;
  created_utc: string;
  lattice_id: string;
  observer: {
    name: string;
    dob: string;
    seal: string;
  };
  schumann_bins_hz: number[];
  calibration: Record<string, number>;
}

export interface LatticeTimeseries {
  timestamp_utc: string;
  Ex: number;
  Ey: number;
  Bx: number;
  By: number;
  Bz: number;
  gain: number;
  qf: number;
}

export interface SchumannFeatures {
  timestamp_utc: string;
  A7_83: number;
  A14_3: number;
  A20_8: number;
  A27_3: number;
  A33_8: number;
  coherence_idx: number;
}

export interface SealPacket {
  timestamp_utc: string;
  intent_text: string;
  w_unity_10: number;
  w_flow_9: number;
  w_anchor_1: number;
  amplitude_gain: number;
  packet_value: number;
  seal_lock: boolean;
}

export class EarthDataLoader {
  private manifest: EarthDataManifest | null = null;
  
  async loadManifest(): Promise<EarthDataManifest> {
    const response = await fetch('/earth-live-data/manifest.json');
    this.manifest = await response.json();
    return this.manifest;
  }
  
  async loadLatticeData(): Promise<LatticeTimeseries[]> {
    const response = await fetch('/earth-live-data/lattice_timeseries.csv');
    const text = await response.text();
    return this.parseCSV(text) as LatticeTimeseries[];
  }
  
  async loadSchumannFeatures(): Promise<SchumannFeatures[]> {
    const response = await fetch('/earth-live-data/schumann_features.csv');
    const text = await response.text();
    return this.parseCSV(text) as SchumannFeatures[];
  }
  
  async loadSealPackets(): Promise<SealPacket[]> {
    const response = await fetch('/earth-live-data/10_9_1_packet.csv');
    const text = await response.text();
    return this.parseCSV(text) as SealPacket[];
  }
  
  private parseCSV(text: string): any[] {
    const lines = text.trim().split('\n');
    const headers = lines[0].split(',');
    return lines.slice(1).map(line => {
      const values = line.split(',');
      const obj: any = {};
      headers.forEach((header, i) => {
        const value = values[i];
        obj[header] = isNaN(Number(value)) ? value : Number(value);
      });
      return obj;
    });
  }
}