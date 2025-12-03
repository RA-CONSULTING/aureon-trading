import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

/**
 * Ingest Akashic Mapper Attunement State
 * Prime Sentinel: GARY LECKEY 02111991
 * 
 * Stores Akashic frequency attunement data including meditation cycles,
 * convergence rates, and stability indices.
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
      
      // Attunement Results
      final_frequency,
      base_frequency,
      point_of_intent,
      iterations_count,
      
      // Quality Metrics
      convergence_rate,
      stability_index,
      
      // Cycle Data
      cycles,
      
      // Harmonic Boost
      system_coherence,
      harmonic_boost,
      
      metadata
    } = await req.json();

    console.log('Ingesting Akashic Mapper attunement for temporal ID:', temporal_id);

    // Insert into akashic_attunement_states table
    const { data, error } = await supabase
      .from('akashic_attunement_states')
      .insert({
        temporal_id,
        sentinel_name,
        final_frequency,
        base_frequency: base_frequency || 7.83,
        point_of_intent: point_of_intent || 9.0,
        iterations_count,
        convergence_rate,
        stability_index,
        cycles: cycles || [],
        system_coherence,
        harmonic_boost,
        metadata: metadata || {}
      })
      .select()
      .single();

    if (error) {
      console.error('Error ingesting akashic attunement state:', error);
      throw error;
    }

    console.log('Akashic Mapper state ingested successfully:', data.id);

    // Insert into lighthouse_events for unified tracking
    const { error: lighthouseError } = await supabase
      .from('lighthouse_events')
      .insert({
        event_type: 'akashic_attunement',
        temporal_id,
        sentinel_name,
        coherence: stability_index,
        metadata: {
          final_frequency,
          convergence_rate,
          harmonic_boost,
          iterations: iterations_count
        }
      });

    if (lighthouseError) {
      console.warn('Warning: Failed to insert lighthouse event:', lighthouseError.message);
    }

    return new Response(
      JSON.stringify({ 
        success: true, 
        id: data.id,
        final_frequency,
        stability_index,
        harmonic_boost
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200 
      }
    );

  } catch (error) {
    console.error('Akashic Mapper ingestion error:', error);
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
