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
      active_nodes,
      network_strength,
      grid_energy,
      avg_coherence,
      avg_frequency,
      phase_locks,
      resonance_quality,
      metadata
    } = await req.json();

    console.log('Ingesting Stargate network state for temporal ID:', temporal_id);

    const { data, error } = await supabase
      .from('stargate_network_states')
      .insert({
        temporal_id,
        sentinel_name,
        active_nodes,
        network_strength,
        grid_energy,
        avg_coherence,
        avg_frequency,
        phase_locks,
        resonance_quality,
        metadata: metadata || {}
      })
      .select()
      .single();

    if (error) {
      console.error('Error ingesting stargate network state:', error);
      throw error;
    }

    console.log('Stargate network state ingested successfully:', data.id);

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
    console.error('Error in ingest-stargate-network function:', error);
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
