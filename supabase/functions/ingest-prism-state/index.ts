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
      level,
      state,
      input_frequency,
      frequency,
      transformation_quality,
      harmonic_purity,
      resonance_strength,
      is_love_locked,
      lighthouse_event_id,
      lighthouse_signal,
      is_lhe_correlated,
      metadata
    } = await req.json();

    console.log('Ingesting Prism transformation state for temporal ID:', temporal_id);

    const { data, error } = await supabase
      .from('prism_transformation_states')
      .insert({
        temporal_id,
        sentinel_name,
        lambda_value,
        coherence,
        level,
        state,
        input_frequency,
        frequency,
        transformation_quality,
        harmonic_purity,
        resonance_strength,
        is_love_locked: is_love_locked || false,
        lighthouse_event_id,
        lighthouse_signal,
        is_lhe_correlated: is_lhe_correlated || false,
        metadata: metadata || {}
      })
      .select()
      .single();

    if (error) {
      console.error('Error ingesting prism state:', error);
      throw error;
    }

    console.log('Prism state ingested successfully:', data.id);

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
    console.error('Error in ingest-prism-state function:', error);
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
