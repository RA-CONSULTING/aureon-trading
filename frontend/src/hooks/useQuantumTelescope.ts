import { useState, useEffect, useCallback } from 'react';
import { quantumTelescope, type TelescopeObservation, type MarketInput, GeometricSolid } from '@/core/quantumTelescope';
import { supabase } from '@/integrations/supabase/client';

export interface UseQuantumTelescopeReturn {
  observation: TelescopeObservation | null;
  isObserving: boolean;
  geometricAlignment: number;
  dominantSolid: GeometricSolid | null;
  probabilitySpectrum: number[];
  holographicDirection: 'UP' | 'DOWN' | 'NEUTRAL';
  focalCoherence: number;
  prismBoostFactor: number;
  observe: (market: MarketInput, symbol?: string) => TelescopeObservation;
  persistObservation: (observation: TelescopeObservation, temporalId: string) => Promise<void>;
  recentObservations: TelescopeObservation[];
}

export function useQuantumTelescope(): UseQuantumTelescopeReturn {
  const [observation, setObservation] = useState<TelescopeObservation | null>(null);
  const [isObserving, setIsObserving] = useState(false);
  const [recentObservations, setRecentObservations] = useState<TelescopeObservation[]>([]);

  // Subscribe to real-time telescope observations
  useEffect(() => {
    const channel = supabase
      .channel('telescope-observations')
      .on(
        'postgres_changes',
        { event: 'INSERT', schema: 'public', table: 'telescope_observations' },
        (payload) => {
          const newObs = payload.new;
          // Convert DB record to TelescopeObservation format
          const converted: TelescopeObservation = {
            timestamp: new Date(newObs.timestamp).getTime(),
            symbol: newObs.symbol,
            lightBeam: {
              intensity: Number(newObs.beam_intensity),
              wavelength: Number(newObs.beam_wavelength),
              velocity: Number(newObs.beam_velocity),
              angle: Number(newObs.beam_angle),
              polarization: Number(newObs.beam_polarization),
            },
            refractions: [
              { solid: GeometricSolid.Tetrahedron, resonance: Number(newObs.tetrahedron_resonance), refractiveIndex: 0, dispersion: 0, focalPoint: 0, clarity: 0 },
              { solid: GeometricSolid.Hexahedron, resonance: Number(newObs.hexahedron_resonance), refractiveIndex: 0, dispersion: 0, focalPoint: 0, clarity: 0 },
              { solid: GeometricSolid.Octahedron, resonance: Number(newObs.octahedron_resonance), refractiveIndex: 0, dispersion: 0, focalPoint: 0, clarity: 0 },
              { solid: GeometricSolid.Icosahedron, resonance: Number(newObs.icosahedron_resonance), refractiveIndex: 0, dispersion: 0, focalPoint: 0, clarity: 0 },
              { solid: GeometricSolid.Dodecahedron, resonance: Number(newObs.dodecahedron_resonance), refractiveIndex: 0, dispersion: 0, focalPoint: 0, clarity: 0 },
            ],
            geometricAlignment: Number(newObs.geometric_alignment),
            dominantSolid: newObs.dominant_solid as GeometricSolid,
            probabilitySpectrum: newObs.probability_spectrum as number[],
            holographicProjection: newObs.holographic_projection as TelescopeObservation['holographicProjection'],
            focalCoherence: Number(newObs.focal_coherence),
            prismBoostFactor: Number(newObs.prism_boost_factor),
          };
          setObservation(converted);
          setRecentObservations(prev => [converted, ...prev.slice(0, 9)]);
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  const observe = useCallback((market: MarketInput, symbol: string = 'BTCUSDT'): TelescopeObservation => {
    setIsObserving(true);
    try {
      const obs = quantumTelescope.observe(market, symbol);
      quantumTelescope.registerAndPublish(obs);
      setObservation(obs);
      setRecentObservations(prev => [obs, ...prev.slice(0, 9)]);
      return obs;
    } finally {
      setIsObserving(false);
    }
  }, []);

  const persistObservation = useCallback(async (obs: TelescopeObservation, temporalId: string): Promise<void> => {
    try {
      const { error } = await supabase.functions.invoke('ingest-telescope-state', {
        body: {
          temporal_id: temporalId,
          symbol: obs.symbol,
          beam: obs.lightBeam,
          refractions: {
            tetrahedron: obs.refractions[0]?.resonance ?? 0,
            hexahedron: obs.refractions[1]?.resonance ?? 0,
            octahedron: obs.refractions[2]?.resonance ?? 0,
            icosahedron: obs.refractions[3]?.resonance ?? 0,
            dodecahedron: obs.refractions[4]?.resonance ?? 0,
          },
          geometric_alignment: obs.geometricAlignment,
          dominant_solid: obs.dominantSolid,
          probability_spectrum: obs.probabilitySpectrum,
          holographic_projection: obs.holographicProjection,
          focal_coherence: obs.focalCoherence,
          prism_boost_factor: obs.prismBoostFactor,
        },
      });

      if (error) {
        console.error('[useQuantumTelescope] Persist error:', error);
      }
    } catch (err) {
      console.error('[useQuantumTelescope] Persist exception:', err);
    }
  }, []);

  return {
    observation,
    isObserving,
    geometricAlignment: observation?.geometricAlignment ?? 0,
    dominantSolid: observation?.dominantSolid ?? null,
    probabilitySpectrum: observation?.probabilitySpectrum ?? [],
    holographicDirection: observation?.holographicProjection.direction ?? 'NEUTRAL',
    focalCoherence: observation?.focalCoherence ?? 0,
    prismBoostFactor: observation?.prismBoostFactor ?? 1,
    observe,
    persistObservation,
    recentObservations,
  };
}
