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

    // Insert into master_equation_field_history
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

    // ALSO insert into lighthouse_events for War Room dashboard
    const isLHE = coherence > 0.945 && lambda > 1.5;
    const lighthouseSignal = lambda * coherence * quality_factor;
    
    const { error: lighthouseError } = await supabase
      .from('lighthouse_events')
      .insert({
        timestamp: new Date().toISOString(),
        lambda_value: lambda,
        coherence,
        lighthouse_signal: lighthouseSignal,
        threshold: 0.945,
        is_lhe: isLHE,
        confidence: quality_factor,
        dominant_node,
        metric_clin: coherence_linear || 1.0,
        metric_cnonlin: coherence_nonlinear,
        metric_geff: effective_gain,
        metric_q: quality_factor,
        prism_level: isLHE ? 5 : Math.floor(coherence * 5),
        prism_state: isLHE ? 'MANIFEST' : coherence > 0.8 ? 'CONVERGING' : 'FORMING'
      });

    if (lighthouseError) {
      console.warn('Warning: Failed to insert lighthouse event:', lighthouseError);
      // Non-critical, continue
    } else {
      console.log('Lighthouse event created:', { isLHE, coherence, lambda });
    }

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
