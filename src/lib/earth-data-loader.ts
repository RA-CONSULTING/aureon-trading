// Earth Live Data Loader for 10-9-1 Seal Integration
export interface EarthDataManifest {
  name: string;
  version: string;
  owner: string;
  lattice_id: {
    phi: number;
    gaia_baseline_hz: number;
    t0_date: string;
    t0_harmonic_key_hz: number;
    law_10_9_1: number[];
    seal: string;
  };
  schemas: Record<string, any>;
  streams: Record<string, any>;
  validation: {
    coherence_threshold: number;
    phase_lock_window_s: number;
    harmonic_deviation_max: number;
    live_metrics: string[];
  };
  measurement_formulas: Record<string, string>;
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
  station_id?: string;
  lat?: number;
  lon?: number;
  alt?: number;
}

export interface SchumannFeatures {
  timestamp_utc: string;
  A7_83: number;
  A14_3: number;
  A20_8: number;
  A27_3: number;
  A33_8: number;
  P7_83: number;
  P14_3: number;
  P20_8: number;
  P27_3: number;
  P33_8: number;
  coherence_idx: number;
  envelope_7_83: number;
  envelope_14_3: number;
  envelope_20_8: number;
  envelope_27_3: number;
  envelope_33_8: number;
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
  prime_coherence: number;
  lattice_phase: number;
}

export interface TimelineMarker {
  t_seconds: number;
  marker: string;
  value: number;
  lattice_phase: number;
  seal_state: string;
  coherence_level: number;
}

export interface TimelineClip {
  lattice_id: string;
  intent: string;
  packet_hz: number[];
  amplitude_gain: number;
  seal_config: {
    unity_weight: number;
    flow_weight: number;
    anchor_weight: number;
    observer: string;
    seal_lock: boolean;
  };
  markers: Array<{
    t: number;
    name: string;
    phase: number;
    coherence: number;
  }>;
  processing: {
    fs_hz: number;
    window_seconds: number;
    overlap: number;
    calibration_applied: boolean;
    clock_sync: string;
    quality_validated: boolean;
  };
}

export interface AurisCodexConfig {
  codex_version: string;
  description: string;
  base_tuning: number;
  harmonic_series: string;
  circle_of_fifths_live: Record<string, {
    earth_channel: string;
    frequency_hz: number;
    relative_minor: string;
    fifths: string[];
    validation_formula: string;
  }>;
  live_validation_metrics: Record<string, {
    formula: string;
    threshold: number;
    units: string;
  }>;
  real_time_windows: {
    fast_update_s: number;
    coherence_window_s: number;
    stability_window_s: number;
    validation_interval_s: number;
  };
  harmonic_ratios_earth: Record<string, string>;
}

export interface FieldResonanceMapper {
  mapper_version: string;
  description: string;
  field_grid: {
    resolution: string;
    coverage: string;
    update_frequency: string;
    coordinate_system: string;
  };
  resonance_layers: Array<{
    name: string;
    frequency_range: number[];
    propagation_speed: number | string;
    attenuation_factor: number;
  }>;
  broadcast_nodes: Array<{
    node_id: string;
    lat: number;
    lon: number;
    power_level: number;
    coverage_radius_km: number;
  }>;
  coupling_parameters: {
    observer_lock_strength: number;
    field_coherence_threshold: number;
    resonance_amplification: number;
    phase_lock_tolerance: number;
  };
  feedback_channels: string[];
}

export class EarthDataLoader {
  private manifest: EarthDataManifest | null = null;
  private aurisCodex: AurisCodexConfig | null = null;
  private fieldResonanceMapper: FieldResonanceMapper | null = null;
  private timelineClip: TimelineClip | null = null;
  private latticeData: LatticeTimeseries[] = [];
  private schumannData: SchumannFeatures[] = [];
  private sealPackets: SealPacket[] = [];
  private timelineMarkers: TimelineMarker[] = [];
  
  async loadManifest(): Promise<EarthDataManifest> {
    const response = await fetch('/earth-live-data/manifest.json');
    this.manifest = await response.json();
    return this.manifest!;
  }
  
  async loadAurisCodex(): Promise<AurisCodexConfig> {
    const response = await fetch('/earth-live-data/auris_codex.json');
    this.aurisCodex = await response.json();
    return this.aurisCodex!;
  }
  
  async loadFieldResonanceMapper(): Promise<FieldResonanceMapper> {
    const response = await fetch('/earth-live-data/field_resonance_mapper.json');
    this.fieldResonanceMapper = await response.json();
    return this.fieldResonanceMapper!;
  }
  
  async loadTimelineClip(): Promise<TimelineClip> {
    const response = await fetch('/earth-live-data/timeline_clip.json');
    this.timelineClip = await response.json();
    return this.timelineClip!;
  }
  
  async loadLatticeData(): Promise<LatticeTimeseries[]> {
    const response = await fetch('/earth-live-data/lattice_timeseries.csv');
    const text = await response.text();
    this.latticeData = this.parseCSV(text) as LatticeTimeseries[];
    return this.latticeData;
  }
  
  async loadSchumannFeatures(): Promise<SchumannFeatures[]> {
    const response = await fetch('/earth-live-data/schumann_features.csv');
    const text = await response.text();
    this.schumannData = this.parseCSV(text) as SchumannFeatures[];
    return this.schumannData;
  }
  
  async loadSealPackets(): Promise<SealPacket[]> {
    const response = await fetch('/earth-live-data/10_9_1_packet.csv');
    const text = await response.text();
    this.sealPackets = this.parseCSV(text).map(row => ({
      ...row,
      seal_lock: row.seal_lock === 'true' || row.seal_lock === true
    })) as SealPacket[];
    return this.sealPackets;
  }
  
  async loadTimelineMarkers(): Promise<TimelineMarker[]> {
    const response = await fetch('/earth-live-data/timeline_markers.csv');
    const text = await response.text();
    this.timelineMarkers = this.parseCSV(text) as TimelineMarker[];
    return this.timelineMarkers;
  }
  
  async loadAll(): Promise<{
    manifest: EarthDataManifest;
    aurisCodex: AurisCodexConfig;
    fieldResonanceMapper: FieldResonanceMapper;
    timelineClip: TimelineClip;
    latticeData: LatticeTimeseries[];
    schumannData: SchumannFeatures[];
    sealPackets: SealPacket[];
    timelineMarkers: TimelineMarker[];
  }> {
    const [manifest, aurisCodex, fieldResonanceMapper, timelineClip, latticeData, schumannData, sealPackets, timelineMarkers] = await Promise.all([
      this.loadManifest(),
      this.loadAurisCodex(),
      this.loadFieldResonanceMapper(),
      this.loadTimelineClip(),
      this.loadLatticeData(),
      this.loadSchumannFeatures(),
      this.loadSealPackets(),
      this.loadTimelineMarkers()
    ]);
    
    return {
      manifest,
      aurisCodex,
      fieldResonanceMapper,
      timelineClip,
      latticeData,
      schumannData,
      sealPackets,
      timelineMarkers
    };
  }
  
  // Getters for cached data
  getManifest(): EarthDataManifest | null { return this.manifest; }
  getAurisCodex(): AurisCodexConfig | null { return this.aurisCodex; }
  getFieldResonanceMapper(): FieldResonanceMapper | null { return this.fieldResonanceMapper; }
  getTimelineClip(): TimelineClip | null { return this.timelineClip; }
  getLatticeData(): LatticeTimeseries[] { return this.latticeData; }
  getSchumannData(): SchumannFeatures[] { return this.schumannData; }
  getSealPackets(): SealPacket[] { return this.sealPackets; }
  getTimelineMarkers(): TimelineMarker[] { return this.timelineMarkers; }
  
  private parseCSV(text: string): any[] {
    const lines = text.trim().split('\n');
    if (lines.length < 2) return [];
    
    const headers = lines[0].split(',').map(h => h.trim());
    return lines.slice(1).map(line => {
      const values = this.parseCSVLine(line);
      const obj: any = {};
      headers.forEach((header, i) => {
        const value = values[i]?.trim();
        // Handle quoted strings
        if (value?.startsWith('"') && value?.endsWith('"')) {
          obj[header] = value.slice(1, -1);
        } else if (value === 'true') {
          obj[header] = true;
        } else if (value === 'false') {
          obj[header] = false;
        } else if (value && !isNaN(Number(value))) {
          obj[header] = Number(value);
        } else {
          obj[header] = value;
        }
      });
      return obj;
    });
  }
  
  private parseCSVLine(line: string): string[] {
    const result: string[] = [];
    let current = '';
    let inQuotes = false;
    
    for (const char of line) {
      if (char === '"') {
        inQuotes = !inQuotes;
        current += char;
      } else if (char === ',' && !inQuotes) {
        result.push(current);
        current = '';
      } else {
        current += char;
      }
    }
    result.push(current);
    return result;
  }
}

// Singleton instance
export const earthDataLoader = new EarthDataLoader();
