import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

/**
 * Ingest Dimensional Dialler State
 * Prime Sentinel: GARY LECKEY 02111991
 * 
 * Stores dimensional stability, prime locks, Schumann lattice,
 * quantum entanglements, and drift correction data.
 */
serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    );

    const {
      temporal_id,
      sentinel_name,
      
      // Prime Locks
      active_prime,
      locked_primes_count,
      prime_alignment,
      
      // Schumann Lattice
      schumann_hold,
      dominant_harmonic_index,
      dominant_harmonic_frequency,
      lattice_stability,
      
      // Quantum Entanglements
      entanglement_count,
      coherent_pairs,
      quantum_coherence,
      
      // Dimensional Stability
      overall_stability,
      dimensional_integrity,
      temporal_sync,
      
      // Dial Position
      dial_position,
      
      // Drift Detection & Correction
      drift_detected,
      drift_magnitude,
      drift_direction,
      correction_applied,
      correction_success,
      
      metadata
    } = await req.json();

    console.log('Ingesting Dimensional Dialler state for temporal ID:', temporal_id);

    // Insert into dimensional_dialler_states table
    const { data, error } = await supabase
      .from('dimensional_dialler_states')
      .insert({
        temporal_id,
        sentinel_name,
        active_prime,
        locked_primes_count,
        prime_alignment,
        schumann_hold,
        dominant_harmonic_index,
        dominant_harmonic_frequency,
        lattice_stability,
        entanglement_count,
        coherent_pairs,
        quantum_coherence,
        overall_stability,
        dimensional_integrity,
        temporal_sync,
        dial_position,
        drift_detected: drift_detected || false,
        drift_magnitude,
        drift_direction,
        correction_applied: correction_applied || false,
        correction_success: correction_success || false,
        metadata: metadata || {}
      })
      .select()
      .single();

    if (error) {
      console.error('Error ingesting dimensional dialler state:', error);
      throw error;
    }

    console.log('Dimensional Dialler state ingested successfully:', data.id);

    // Insert into lighthouse_events for unified tracking
    const { error: lighthouseError } = await supabase
      .from('lighthouse_events')
      .insert({
        event_type: 'dimensional_dialler',
        temporal_id,
        sentinel_name,
        coherence: overall_stability,
        metadata: {
          active_prime,
          schumann_hold,
          quantum_coherence,
          temporal_sync,
          dial_position,
          drift_detected,
          correction_applied
        }
      });

    if (lighthouseError) {
      console.warn('Warning: Failed to insert lighthouse event:', lighthouseError.message);
    }

    // If drift was detected and corrected, log it separately
    if (drift_detected && correction_applied) {
      const { error: driftError } = await supabase
        .from('lighthouse_events')
        .insert({
          event_type: 'drift_correction',
          temporal_id,
          sentinel_name,
          coherence: correction_success ? 1.0 : 0.5,
          metadata: {
            drift_magnitude,
            drift_direction,
            correction_success,
            new_stability: overall_stability
          }
        });

      if (driftError) {
        console.warn('Warning: Failed to log drift correction:', driftError.message);
      }
    }

    return new Response(
      JSON.stringify({ 
        success: true, 
        id: data.id,
        overall_stability,
        drift_corrected: drift_detected && correction_success
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200 
      }
    );

  } catch (error) {
    console.error('Dimensional Dialler ingestion error:', error);
    return new Response(
      JSON.stringify({ 
        error: error.message,
        success: false 
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 500 
      }
    );
  }
});
