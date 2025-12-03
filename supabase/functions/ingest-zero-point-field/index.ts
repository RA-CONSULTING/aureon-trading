import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

/**
 * Ingest Zero Point Field Detector State
 * Prime Sentinel: GARY LECKEY 02111991
 * 
 * Stores zero point field harmonics, seal activation, quantum echoes,
 * and temporal routing data to the database.
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
      
      // Seal Harmonics
      active_seal_name,
      active_seal_frequency,
      active_seal_earth_resonance,
      active_seal_multiplier,
      
      // Quantum Echoes
      composite_echo_signal,
      phase_lock_strength,
      
      // Temporal Regulators
      composite_regulator_field,
      
      // Fibonacci TCPs
      current_ftcp_g_eff,
      current_ftcp_phi_windowed,
      is_ftcp_active,
      
      // Family Resonances
      family_unity_wave,
      
      // Surge Windows
      active_surge_window_id,
      surge_unity_coherence,
      surge_alignment_strength,
      
      // Field Cavity Metrics
      spacetime_distortion,
      energy_flow_magnitude,
      cavity_resonance,
      
      // Zero Point Connection
      zero_point_coherence,
      temporal_routing_strength,
      guidance_vector,
      
      metadata
    } = await req.json();

    console.log('Ingesting Zero Point Field state for temporal ID:', temporal_id);

    // Insert into zero_point_field_states table
    const { data, error } = await supabase
      .from('zero_point_field_states')
      .insert({
        temporal_id,
        sentinel_name,
        active_seal_name,
        active_seal_frequency,
        active_seal_earth_resonance,
        active_seal_multiplier,
        composite_echo_signal,
        phase_lock_strength,
        composite_regulator_field,
        current_ftcp_g_eff,
        current_ftcp_phi_windowed,
        is_ftcp_active: is_ftcp_active || false,
        family_unity_wave,
        active_surge_window_id,
        surge_unity_coherence,
        surge_alignment_strength,
        spacetime_distortion,
        energy_flow_magnitude,
        cavity_resonance,
        zero_point_coherence,
        temporal_routing_strength,
        guidance_vector: guidance_vector || [0, 0, 0],
        metadata: metadata || {}
      })
      .select()
      .single();

    if (error) {
      console.error('Error ingesting zero point field state:', error);
      throw error;
    }

    console.log('Zero Point Field state ingested successfully:', data.id);

    // Also insert into lighthouse_events for unified War Room tracking
    const { error: lighthouseError } = await supabase
      .from('lighthouse_events')
      .insert({
        event_type: 'zero_point_field',
        temporal_id,
        sentinel_name,
        coherence: zero_point_coherence,
        metadata: {
          active_seal: active_seal_name,
          phase_lock: phase_lock_strength,
          cavity_resonance,
          spacetime_distortion,
          is_ftcp: is_ftcp_active,
          surge_window: active_surge_window_id
        }
      });

    if (lighthouseError) {
      console.warn('Warning: Failed to insert lighthouse event:', lighthouseError.message);
    }

    return new Response(
      JSON.stringify({ 
        success: true, 
        id: data.id,
        zero_point_coherence,
        active_seal: active_seal_name
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200 
      }
    );

  } catch (error) {
    console.error('Zero Point Field ingestion error:', error);
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
