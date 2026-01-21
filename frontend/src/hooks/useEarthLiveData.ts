// Hook to load and provide real Earth live data from CSV/JSON files
import { useState, useEffect, useCallback, useRef } from 'react';
import { 
  earthDataLoader, 
  type SchumannFeatures, 
  type LatticeTimeseries,
  type SealPacket,
  type TimelineMarker,
  type TimelineClip,
  type AurisCodexConfig,
  type FieldResonanceMapper,
  type EarthDataManifest
} from '@/lib/earth-data-loader';
import { earthValidation, type ValidationResult } from '@/lib/earth-validation';

export interface EarthLiveDataState {
  // Loading states
  isLoading: boolean;
  isInitialized: boolean;
  error: string | null;
  
  // Raw data
  manifest: EarthDataManifest | null;
  aurisCodex: AurisCodexConfig | null;
  fieldResonanceMapper: FieldResonanceMapper | null;
  timelineClip: TimelineClip | null;
  
  // Time series data
  latticeData: LatticeTimeseries[];
  schumannData: SchumannFeatures[];
  sealPackets: SealPacket[];
  timelineMarkers: TimelineMarker[];
  
  // Current values (animated through data)
  currentSchumann: SchumannFeatures | null;
  currentLattice: LatticeTimeseries | null;
  currentSealPacket: SealPacket | null;
  currentMarker: TimelineMarker | null;
  
  // Validation
  validation: ValidationResult | null;
  
  // Computed metrics
  schumannModes: {
    mode1: { freq: number; amplitude: number; phase: number };
    mode2: { freq: number; amplitude: number; phase: number };
    mode3: { freq: number; amplitude: number; phase: number };
    mode4: { freq: number; amplitude: number; phase: number };
    mode5: { freq: number; amplitude: number; phase: number };
  } | null;
  
  magneticField: {
    Bx: number;
    By: number;
    Bz: number;
    magnitude: number;
  } | null;
  
  electricField: {
    Ex: number;
    Ey: number;
    magnitude: number;
  } | null;
  
  primeSeal: {
    isLocked: boolean;
    coherence: number;
    packetValue: number;
    intent: string;
    weights: { unity: number; flow: number; anchor: number };
  } | null;
}

export function useEarthLiveData(autoPlay: boolean = true, updateIntervalMs: number = 1000) {
  const [state, setState] = useState<EarthLiveDataState>({
    isLoading: true,
    isInitialized: false,
    error: null,
    manifest: null,
    aurisCodex: null,
    fieldResonanceMapper: null,
    timelineClip: null,
    latticeData: [],
    schumannData: [],
    sealPackets: [],
    timelineMarkers: [],
    currentSchumann: null,
    currentLattice: null,
    currentSealPacket: null,
    currentMarker: null,
    validation: null,
    schumannModes: null,
    magneticField: null,
    electricField: null,
    primeSeal: null
  });
  
  const dataIndexRef = useRef(0);
  const schumannHistoryRef = useRef<SchumannFeatures[]>([]);
  
  // Load all data on mount
  useEffect(() => {
    let isMounted = true;
    
    const loadData = async () => {
      try {
        const data = await earthDataLoader.loadAll();
        
        if (!isMounted) return;
        
        // Set codex for validation
        if (data.aurisCodex) {
          earthValidation.setCodex(data.aurisCodex);
        }
        
        setState(prev => ({
          ...prev,
          isLoading: false,
          isInitialized: true,
          manifest: data.manifest,
          aurisCodex: data.aurisCodex,
          fieldResonanceMapper: data.fieldResonanceMapper,
          timelineClip: data.timelineClip,
          latticeData: data.latticeData,
          schumannData: data.schumannData,
          sealPackets: data.sealPackets,
          timelineMarkers: data.timelineMarkers,
          currentSchumann: data.schumannData[0] || null,
          currentLattice: data.latticeData[0] || null,
          currentSealPacket: data.sealPackets[0] || null,
          currentMarker: data.timelineMarkers[0] || null
        }));
        
        console.log('🌍 Earth Live Data loaded:', {
          schumann: data.schumannData.length,
          lattice: data.latticeData.length,
          seals: data.sealPackets.length,
          markers: data.timelineMarkers.length
        });
      } catch (err) {
        if (!isMounted) return;
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: err instanceof Error ? err.message : 'Failed to load Earth data'
        }));
      }
    };
    
    loadData();
    
    return () => { isMounted = false; };
  }, []);
  
  // Update current values periodically (cycle through data)
  useEffect(() => {
    if (!autoPlay || !state.isInitialized) return;
    
    const interval = setInterval(() => {
      setState(prev => {
        const schumannIdx = dataIndexRef.current % Math.max(1, prev.schumannData.length);
        const latticeIdx = dataIndexRef.current % Math.max(1, prev.latticeData.length);
        const sealIdx = dataIndexRef.current % Math.max(1, prev.sealPackets.length);
        const markerIdx = Math.floor((dataIndexRef.current / 10)) % Math.max(1, prev.timelineMarkers.length);
        
        const currentSchumann = prev.schumannData[schumannIdx] || null;
        const currentLattice = prev.latticeData[latticeIdx] || null;
        const currentSealPacket = prev.sealPackets[sealIdx] || null;
        const currentMarker = prev.timelineMarkers[markerIdx] || null;
        
        // Update history for validation
        if (currentSchumann) {
          schumannHistoryRef.current.push(currentSchumann);
          if (schumannHistoryRef.current.length > 60) {
            schumannHistoryRef.current.shift();
          }
        }
        
        // Run validation
        const validation = currentSchumann 
          ? earthValidation.validate(currentSchumann, schumannHistoryRef.current, currentLattice || undefined)
          : null;
        
        // Compute derived metrics
        const schumannModes = currentSchumann ? {
          mode1: { freq: 7.83, amplitude: currentSchumann.A7_83, phase: currentSchumann.P7_83 },
          mode2: { freq: 14.3, amplitude: currentSchumann.A14_3, phase: currentSchumann.P14_3 },
          mode3: { freq: 20.8, amplitude: currentSchumann.A20_8, phase: currentSchumann.P20_8 },
          mode4: { freq: 27.3, amplitude: currentSchumann.A27_3, phase: currentSchumann.P27_3 },
          mode5: { freq: 33.8, amplitude: currentSchumann.A33_8, phase: currentSchumann.P33_8 }
        } : null;
        
        const magneticField = currentLattice ? {
          Bx: currentLattice.Bx,
          By: currentLattice.By,
          Bz: currentLattice.Bz,
          magnitude: Math.sqrt(currentLattice.Bx ** 2 + currentLattice.By ** 2 + currentLattice.Bz ** 2)
        } : null;
        
        const electricField = currentLattice ? {
          Ex: currentLattice.Ex,
          Ey: currentLattice.Ey,
          magnitude: Math.sqrt(currentLattice.Ex ** 2 + currentLattice.Ey ** 2)
        } : null;
        
        const primeSeal = currentSealPacket ? {
          isLocked: currentSealPacket.seal_lock,
          coherence: currentSealPacket.prime_coherence,
          packetValue: currentSealPacket.packet_value,
          intent: currentSealPacket.intent_text,
          weights: {
            unity: currentSealPacket.w_unity_10,
            flow: currentSealPacket.w_flow_9,
            anchor: currentSealPacket.w_anchor_1
          }
        } : null;
        
        dataIndexRef.current++;
        
        return {
          ...prev,
          currentSchumann,
          currentLattice,
          currentSealPacket,
          currentMarker,
          validation,
          schumannModes,
          magneticField,
          electricField,
          primeSeal
        };
      });
    }, updateIntervalMs);
    
    return () => clearInterval(interval);
  }, [autoPlay, state.isInitialized, updateIntervalMs]);
  
  const reset = useCallback(() => {
    dataIndexRef.current = 0;
    schumannHistoryRef.current = [];
  }, []);
  
  return { ...state, reset };
}
