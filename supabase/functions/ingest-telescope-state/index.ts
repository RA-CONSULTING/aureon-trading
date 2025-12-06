import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

interface TelescopePayload {
  temporal_id: string;
  symbol: string;
  beam: {
    intensity: number;
    wavelength: number;
    velocity: number;
    angle: number;
    polarization: number;
  };
  refractions: {
    tetrahedron: number;
    hexahedron: number;
    octahedron: number;
    icosahedron: number;
    dodecahedron: number;
  };
  geometric_alignment: number;
  dominant_solid: string;
  probability_spectrum: number[];
  holographic_projection: {
    direction: string;
    magnitude: number;
    confidence: number;
  };
  focal_coherence: number;
  prism_boost_factor: number;
}

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    const supabaseKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
    const supabase = createClient(supabaseUrl, supabaseKey);

    const payload: TelescopePayload = await req.json();

    console.log("[ingest-telescope-state] Ingesting telescope observation:", {
      temporal_id: payload.temporal_id,
      symbol: payload.symbol,
      geometric_alignment: payload.geometric_alignment,
      dominant_solid: payload.dominant_solid,
    });

    // Insert telescope observation
    const { data, error } = await supabase
      .from("telescope_observations")
      .insert({
        temporal_id: payload.temporal_id,
        symbol: payload.symbol,
        beam_intensity: payload.beam.intensity,
        beam_wavelength: payload.beam.wavelength,
        beam_velocity: payload.beam.velocity,
        beam_angle: payload.beam.angle,
        beam_polarization: payload.beam.polarization,
        tetrahedron_resonance: payload.refractions.tetrahedron,
        hexahedron_resonance: payload.refractions.hexahedron,
        octahedron_resonance: payload.refractions.octahedron,
        icosahedron_resonance: payload.refractions.icosahedron,
        dodecahedron_resonance: payload.refractions.dodecahedron,
        geometric_alignment: payload.geometric_alignment,
        dominant_solid: payload.dominant_solid,
        probability_spectrum: payload.probability_spectrum,
        holographic_projection: payload.holographic_projection,
        focal_coherence: payload.focal_coherence,
        prism_boost_factor: payload.prism_boost_factor,
      })
      .select()
      .single();

    if (error) {
      console.error("[ingest-telescope-state] Insert error:", error);
      throw error;
    }

    console.log("[ingest-telescope-state] Observation persisted:", data.id);

    return new Response(
      JSON.stringify({
        success: true,
        observation_id: data.id,
        geometric_alignment: data.geometric_alignment,
        dominant_solid: data.dominant_solid,
      }),
      {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      }
    );
  } catch (error) {
    console.error("[ingest-telescope-state] Error:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return new Response(
      JSON.stringify({ error: message }),
      {
        status: 500,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      }
    );
  }
});
