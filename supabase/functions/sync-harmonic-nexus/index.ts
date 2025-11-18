import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  // Handle CORS preflight requests
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
      omega_value,
      psi_potential,
      love_coherence,
      observer_consciousness,
      theta_alignment,
      unity_probability,
      akashic_frequency,
      akashic_convergence,
      akashic_stability,
      akashic_boost,
      substrate_coherence,
      field_integrity,
      harmonic_resonance,
      dimensional_alignment,
      sync_status,
      sync_quality,
      timeline_divergence,
      lighthouse_signal,
      prism_level,
      metadata
    } = await req.json();

    console.log('Syncing harmonic nexus state for temporal ID:', temporal_id);

    // Insert harmonic nexus state
    const { data, error } = await supabase
      .from('harmonic_nexus_states')
      .insert({
        temporal_id,
        sentinel_name,
        omega_value,
        psi_potential,
        love_coherence,
        observer_consciousness,
        theta_alignment,
        unity_probability,
        akashic_frequency,
        akashic_convergence,
        akashic_stability,
        akashic_boost,
        substrate_coherence,
        field_integrity,
        harmonic_resonance,
        dimensional_alignment,
        sync_status,
        sync_quality,
        timeline_divergence,
        lighthouse_signal,
        prism_level,
        metadata: metadata || {}
      })
      .select()
      .single();

    if (error) {
      console.error('Error syncing harmonic nexus state:', error);
      throw error;
    }

    console.log('Harmonic nexus state synced successfully:', data.id);

    // Get timeline statistics
    const { data: stats } = await supabase
      .from('harmonic_nexus_states')
      .select('substrate_coherence, sync_quality, timeline_divergence')
      .eq('temporal_id', temporal_id)
      .order('event_timestamp', { ascending: false })
      .limit(10);

    const avgCoherence = stats ? stats.reduce((sum, s) => sum + Number(s.substrate_coherence), 0) / stats.length : 0;
    const avgSyncQuality = stats ? stats.reduce((sum, s) => sum + Number(s.sync_quality), 0) / stats.length : 0;

    return new Response(
      JSON.stringify({
        success: true,
        state: data,
        timeline_stats: {
          recent_avg_coherence: avgCoherence,
          recent_avg_sync_quality: avgSyncQuality,
          total_states_recorded: stats?.length || 0
        }
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200 
      }
    );
  } catch (error) {
    console.error('Error in sync-harmonic-nexus function:', error);
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    return new Response(
      JSON.stringify({ error: errorMessage }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 400 
      }
    );
  }
});
