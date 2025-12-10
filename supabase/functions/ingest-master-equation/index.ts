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

    // Insert into master_equation_field_history with safe defaults
    const { data, error } = await supabase
      .from('master_equation_field_history')
      .insert({
        temporal_id,
        sentinel_name,
        symbol,
        lambda: lambda ?? 1.0,
        substrate: substrate ?? 0.5,
        observer: observer ?? 0.5,
        echo: echo ?? 0.3,
        coherence: coherence ?? 0.5,
        coherence_linear: coherence_linear ?? 1.0,
        coherence_nonlinear: coherence_nonlinear ?? 0.5,
        coherence_phi: coherence_phi ?? 0.618,
        quality_factor: quality_factor ?? 1.0,
        effective_gain: effective_gain ?? 1.0,
        dominant_node: dominant_node ?? 'Tiger',
        node_weights: node_weights || {},
        price: price ?? null,
        volume: volume ?? null,
        volatility: volatility ?? null,
        momentum: momentum ?? null,
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
    // Ensure all values have safe defaults to prevent null constraint violations
    const safeLambda = lambda ?? 1.0;
    const safeCoherence = coherence ?? 0.5;
    const safeQualityFactor = quality_factor ?? 1.0;
    const safeEffectiveGain = effective_gain ?? 1.0;
    const safeCoherenceLinear = coherence_linear ?? 1.0;
    const safeCoherenceNonlinear = coherence_nonlinear ?? 0.5;
    
    const isLHE = safeCoherence > 0.945 && safeLambda > 1.5;
    const lighthouseSignal = safeLambda * safeCoherence * safeQualityFactor;
    
    const { error: lighthouseError } = await supabase
      .from('lighthouse_events')
      .insert({
        timestamp: new Date().toISOString(),
        lambda_value: safeLambda,
        coherence: safeCoherence,
        lighthouse_signal: lighthouseSignal,
        threshold: 0.945,
        is_lhe: isLHE,
        confidence: safeQualityFactor,
        dominant_node: dominant_node ?? 'Tiger',
        metric_clin: safeCoherenceLinear,
        metric_cnonlin: safeCoherenceNonlinear,
        metric_geff: safeEffectiveGain,
        metric_q: safeQualityFactor,
        prism_level: isLHE ? 5 : Math.floor(safeCoherence * 5),
        prism_state: isLHE ? 'MANIFEST' : safeCoherence > 0.8 ? 'CONVERGING' : 'FORMING'
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
