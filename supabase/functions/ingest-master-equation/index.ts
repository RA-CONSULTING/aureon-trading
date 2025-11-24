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
      symbol,
      lambda,
      substrate,
      observer,
      echo,
      coherence,
      coherence_linear,
      coherence_nonlinear,
      coherence_phi,
      quality_factor,
      effective_gain,
      dominant_node,
      node_weights,
      price,
      volume,
      volatility,
      momentum,
      metadata
    } = await req.json();

    console.log('Ingesting Master Equation field state for temporal ID:', temporal_id);

    const { data, error } = await supabase
      .from('master_equation_field_history')
      .insert({
        temporal_id,
        sentinel_name,
        symbol,
        lambda,
        substrate,
        observer,
        echo,
        coherence,
        coherence_linear: coherence_linear || 1.0,
        coherence_nonlinear,
        coherence_phi,
        quality_factor,
        effective_gain,
        dominant_node,
        node_weights: node_weights || {},
        price,
        volume,
        volatility,
        momentum,
        metadata: metadata || {}
      })
      .select()
      .single();

    if (error) {
      console.error('Error ingesting master equation state:', error);
      throw error;
    }

    console.log('Master equation state ingested successfully:', data.id);

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
    console.error('Error in ingest-master-equation function:', error);
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
