import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

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
      lambda_value,
      coherence,
      frequency,
      base_frequency,
      harmonic_index,
      phase,
      color,
      dominant_emotion,
      emotional_tags,
      valence,
      arousal,
      intensity,
      phase_transition,
      previous_phase,
      metadata
    } = await req.json();

    console.log('Ingesting Rainbow Bridge state for temporal ID:', temporal_id);

    const { data, error } = await supabase
      .from('rainbow_bridge_states')
      .insert({
        temporal_id,
        sentinel_name,
        lambda_value,
        coherence,
        frequency,
        base_frequency,
        harmonic_index,
        phase,
        color,
        dominant_emotion,
        emotional_tags: emotional_tags || [],
        valence,
        arousal,
        intensity,
        phase_transition: phase_transition || false,
        previous_phase,
        metadata: metadata || {}
      })
      .select()
      .single();

    if (error) {
      console.error('Error ingesting rainbow bridge state:', error);
      throw error;
    }

    console.log('Rainbow bridge state ingested successfully:', data.id);

    return new Response(
      JSON.stringify({
        success: true,
        state: data
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200 
      }
    );
  } catch (error) {
    console.error('Error in ingest-rainbow-bridge function:', error);
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    return new Response(
      JSON.stringify({ success: false, error: errorMessage }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 400 
      }
    );
  }
});
