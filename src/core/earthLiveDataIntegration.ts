/**
 * Earth Live Data Integration
 * 
 * Wires all Earth live data (Schumann, lattice, seal packets) 
 * into the UnifiedBus and TemporalLadder ecosystem
 */

import { unifiedBus } from './unifiedBus';
import { temporalLadder, SYSTEMS } from './temporalLadder';
import { 
  earthDataLoader, 
  type SchumannFeatures, 
  type LatticeTimeseries,
  type SealPacket,
  type TimelineMarker
} from '@/lib/earth-data-loader';
import { earthValidation, type ValidationResult } from '@/lib/earth-validation';
import { supabase } from '@/integrations/supabase/client';

export interface EarthIntegrationState {
  isInitialized: boolean;
  lastUpdate: number;
  
  // Current values
  schumann: SchumannFeatures | null;
  lattice: LatticeTimeseries | null;
  sealPacket: SealPacket | null;
  marker: TimelineMarker | null;
  validation: ValidationResult | null;
  
  // Computed metrics for ecosystem
  coherence: number;
  frequency: number;
  fieldStrength: number;
  phaseLock: boolean;
  harmonicFidelity: number;
  
  // 5-mode Schumann
  modes: {
    mode1: number; // 7.83 Hz
    mode2: number; // 14.3 Hz
    mode3: number; // 20.8 Hz
    mode4: number; // 27.3 Hz
    mode5: number; // 33.8 Hz
  };
  
  // Magnetic field vector
  magneticField: {
    Bx: number;
    By: number;
    Bz: number;
    magnitude: number;
  };
  
  // Electric field vector
  electricField: {
    Ex: number;
    Ey: number;
    magnitude: number;
  };
}

class EarthLiveDataIntegration {
  private state: EarthIntegrationState = {
    isInitialized: false,
    lastUpdate: 0,
    schumann: null,
    lattice: null,
    sealPacket: null,
    marker: null,
    validation: null,
    coherence: 0,
    frequency: 7.83,
    fieldStrength: 0,
    phaseLock: false,
    harmonicFidelity: 0,
    modes: { mode1: 0, mode2: 0, mode3: 0, mode4: 0, mode5: 0 },
    magneticField: { Bx: 0, By: 0, Bz: 0, magnitude: 0 },
    electricField: { Ex: 0, Ey: 0, magnitude: 0 }
  };
  
  private dataIndex = 0;
  private schumannData: SchumannFeatures[] = [];
  private latticeData: LatticeTimeseries[] = [];
  private sealPackets: SealPacket[] = [];
  private markers: TimelineMarker[] = [];
  private schumannHistory: SchumannFeatures[] = [];
  private heartbeatInterval: number | null = null;
  private listeners: Set<(state: EarthIntegrationState) => void> = new Set();
  
  async initialize(): Promise<void> {
    if (this.state.isInitialized) return;
    
    console.log('🌍 Earth Live Data Integration: Initializing...');
    
    try {
      // Load all Earth data
      const data = await earthDataLoader.loadAll();
      
      this.schumannData = data.schumannData;
      this.latticeData = data.latticeData;
      this.sealPackets = data.sealPackets;
      this.markers = data.timelineMarkers;
      
      // Set codex for validation
      if (data.aurisCodex) {
        earthValidation.setCodex(data.aurisCodex);
      }
      
      console.log('🌍 Loaded Earth data:', {
        schumann: this.schumannData.length,
        lattice: this.latticeData.length,
        seals: this.sealPackets.length,
        markers: this.markers.length
      });
      
      // Register with Temporal Ladder
      temporalLadder.registerSystem(SYSTEMS.EARTH_INTEGRATION);
      
      // Start heartbeats
      this.startHeartbeat();
      
      // Initial update
      this.update();
      
      this.state.isInitialized = true;
      console.log('✅ Earth Live Data Integration: Online');
      
    } catch (error) {
      console.error('❌ Earth Live Data Integration failed:', error);
    }
  }
  
  private startHeartbeat(): void {
    if (this.heartbeatInterval) return;
    
    this.heartbeatInterval = window.setInterval(() => {
      this.update();
      this.publishToBus();
      this.sendHeartbeat();
    }, 1000);
  }
  
  private update(): void {
    const now = Date.now();
    
    // Get current data points (cycle through arrays)
    const schumannIdx = this.dataIndex % Math.max(1, this.schumannData.length);
    const latticeIdx = this.dataIndex % Math.max(1, this.latticeData.length);
    const sealIdx = this.dataIndex % Math.max(1, this.sealPackets.length);
    const markerIdx = Math.floor(this.dataIndex / 10) % Math.max(1, this.markers.length);
    
    const schumann = this.schumannData[schumannIdx] || null;
    const lattice = this.latticeData[latticeIdx] || null;
    const sealPacket = this.sealPackets[sealIdx] || null;
    const marker = this.markers[markerIdx] || null;
    
    // Update history for validation
    if (schumann) {
      this.schumannHistory.push(schumann);
      if (this.schumannHistory.length > 60) {
        this.schumannHistory.shift();
      }
    }
    
    // Run validation
    const validation = schumann 
      ? earthValidation.validate(schumann, this.schumannHistory, lattice || undefined)
      : null;
    
    // Compute ecosystem metrics
    const coherence = validation?.overallScore ?? (schumann?.coherence_idx ?? 0);
    const frequency = schumann?.A7_83 ?? 7.83;
    const fieldStrength = lattice 
      ? Math.sqrt(lattice.Bx ** 2 + lattice.By ** 2 + lattice.Bz ** 2) / 100
      : 0;
    const phaseLock = validation?.phaseLockStrength ? validation.phaseLockStrength > 0.8 : false;
    const harmonicFidelity = validation?.harmonicCoherence ?? 0;
    
    // 5-mode Schumann
    const modes = schumann ? {
      mode1: schumann.A7_83,
      mode2: schumann.A14_3,
      mode3: schumann.A20_8,
      mode4: schumann.A27_3,
      mode5: schumann.A33_8
    } : { mode1: 0, mode2: 0, mode3: 0, mode4: 0, mode5: 0 };
    
    // Field vectors
    const magneticField = lattice ? {
      Bx: lattice.Bx,
      By: lattice.By,
      Bz: lattice.Bz,
      magnitude: Math.sqrt(lattice.Bx ** 2 + lattice.By ** 2 + lattice.Bz ** 2)
    } : { Bx: 0, By: 0, Bz: 0, magnitude: 0 };
    
    const electricField = lattice ? {
      Ex: lattice.Ex,
      Ey: lattice.Ey,
      magnitude: Math.sqrt(lattice.Ex ** 2 + lattice.Ey ** 2)
    } : { Ex: 0, Ey: 0, magnitude: 0 };
    
    // Update state
    this.state = {
      ...this.state,
      lastUpdate: now,
      schumann,
      lattice,
      sealPacket,
      marker,
      validation,
      coherence,
      frequency,
      fieldStrength,
      phaseLock,
      harmonicFidelity,
      modes,
      magneticField,
      electricField
    };
    
    this.dataIndex++;
    this.notifyListeners();
  }
  
  private publishToBus(): void {
    const { coherence, phaseLock, harmonicFidelity, frequency } = this.state;
    
    // Determine signal based on coherence and phase lock
    let signal: 'BUY' | 'SELL' | 'NEUTRAL' = 'NEUTRAL';
    if (coherence > 0.8 && phaseLock) {
      signal = 'BUY'; // High coherence + phase lock = favorable conditions
    } else if (coherence < 0.4 || harmonicFidelity < 0.3) {
      signal = 'SELL'; // Poor coherence = unfavorable conditions
    }
    
    unifiedBus.publish({
      systemName: 'EarthIntegration',
      timestamp: Date.now(),
      ready: this.state.isInitialized,
      coherence,
      confidence: harmonicFidelity,
      signal,
      data: {
        frequency,
        phaseLock,
        harmonicFidelity,
        modes: this.state.modes,
        magneticField: this.state.magneticField,
        electricField: this.state.electricField,
        validation: this.state.validation ? {
          fieldAlignment: this.state.validation.fieldAlignment,
          harmonicCoherence: this.state.validation.harmonicCoherence,
          resonanceStability: this.state.validation.resonanceStability,
          phaseLockStrength: this.state.validation.phaseLockStrength,
          overallScore: this.state.validation.overallScore
        } : null
      }
    });
  }
  
  private sendHeartbeat(): void {
    temporalLadder.heartbeat(SYSTEMS.EARTH_INTEGRATION, this.state.coherence);
  }
  
  /**
   * Persist current state to consciousness_field_history
   */
  async persistToDatabase(): Promise<void> {
    const { schumann, validation, coherence, frequency, phaseLock } = this.state;
    if (!schumann) return;
    
    try {
      await supabase.from('consciousness_field_history').insert({
        schumann_frequency: frequency,
        schumann_amplitude: schumann.A7_83,
        schumann_coherence_boost: coherence,
        schumann_phase: phaseLock ? 'LOCKED' : 'UNLOCKED',
        schumann_quality: validation?.overallScore ?? 0,
        total_coherence: coherence,
        celestial_boost: 0,
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      console.warn('Failed to persist Earth data:', error);
    }
  }
  
  getState(): EarthIntegrationState {
    return { ...this.state };
  }
  
  subscribe(callback: (state: EarthIntegrationState) => void): () => void {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }
  
  private notifyListeners(): void {
    const state = this.getState();
    this.listeners.forEach(cb => cb(state));
  }
  
  destroy(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
    this.listeners.clear();
  }
}

export const earthLiveDataIntegration = new EarthLiveDataIntegration();
