import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseKey);

    const body = await req.json();
    const {
      temporal_id,
      upper_left,
      upper_right,
      lower_left,
      lower_right,
      quadrant_balance,
      dominant_quadrant,
      integration_level,
      spiral_stage,
      metadata
    } = body;

    console.log(`[ingest-integral-aqal] Ingesting state for temporal_id: ${temporal_id}`);

    // Ensure numeric values (handle objects being passed)
    const safeNumber = (val: any, fallback: number = 0): number => {
      if (typeof val === 'number') return val;
      if (typeof val === 'object' && val !== null && 'coherenceLevel' in val) return val.coherenceLevel;
      return fallback;
    };
    
    const { data, error } = await supabase
      .from('integral_aqal_states')
      .insert({
        temporal_id,
        upper_left: safeNumber(upper_left),
        upper_right: safeNumber(upper_right),
        lower_left: safeNumber(lower_left),
        lower_right: safeNumber(lower_right),
        quadrant_balance: safeNumber(quadrant_balance),
        dominant_quadrant: typeof dominant_quadrant === 'string' ? dominant_quadrant : 'UPPER_RIGHT',
        integration_level: safeNumber(integration_level),
        spiral_stage: typeof spiral_stage === 'string' ? spiral_stage : 'ORANGE',
        metadata: metadata || {}
      })
      .select()
      .single();

    if (error) {
      console.error('[ingest-integral-aqal] Error:', error);
      throw error;
    }

    console.log(`[ingest-integral-aqal] Successfully ingested state: ${data.id}`);

    return new Response(JSON.stringify({ success: true, data }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    console.error('[ingest-integral-aqal] Error:', message);
    return new Response(JSON.stringify({ error: message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
