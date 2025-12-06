import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

interface PrimeSealPacket {
  temporal_id: string;
  timestamp?: number;
  intent_text?: string;
  w_unity_10: number;
  w_flow_9: number;
  w_anchor_1: number;
  amplitude_gain: number;
  packet_value: number;
  seal_lock: boolean;
  prime_coherence: number;
  lattice_phase: number;
  systems_contributing?: string[];
  metadata?: Record<string, unknown>;
}

serve(async (req) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseKey);

    const packet: PrimeSealPacket = await req.json();

    console.log('🔮 Ingesting 10-9-1 Prime Seal packet:', {
      temporal_id: packet.temporal_id,
      seal_lock: packet.seal_lock,
      prime_coherence: packet.prime_coherence,
      packet_value: packet.packet_value,
    });

    // Validate required fields
    if (!packet.temporal_id) {
      return new Response(
        JSON.stringify({ error: 'temporal_id is required' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // Validate 10-9-1 weights
    if (packet.w_unity_10 !== 10 || packet.w_flow_9 !== 9 || packet.w_anchor_1 !== 1) {
      console.warn('⚠️ Non-standard 10-9-1 weights detected:', {
        unity: packet.w_unity_10,
        flow: packet.w_flow_9,
        anchor: packet.w_anchor_1,
      });
    }

    // Insert into database
    const { data, error } = await supabase
      .from('prime_seal_packets')
      .insert({
        temporal_id: packet.temporal_id,
        timestamp: packet.timestamp ? new Date(packet.timestamp).toISOString() : new Date().toISOString(),
        intent_text: packet.intent_text || '',
        w_unity_10: packet.w_unity_10,
        w_flow_9: packet.w_flow_9,
        w_anchor_1: packet.w_anchor_1,
        amplitude_gain: packet.amplitude_gain,
        packet_value: packet.packet_value,
        seal_lock: packet.seal_lock,
        prime_coherence: packet.prime_coherence,
        lattice_phase: packet.lattice_phase,
        systems_contributing: packet.systems_contributing || [],
        metadata: packet.metadata || {},
      })
      .select()
      .single();

    if (error) {
      console.error('❌ Failed to insert prime seal packet:', error);
      return new Response(
        JSON.stringify({ error: error.message }),
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    console.log('✅ Prime Seal packet ingested:', {
      id: data.id,
      seal_lock: data.seal_lock ? '🔒 LOCKED' : '🔓 UNLOCKED',
      prime_coherence: data.prime_coherence,
    });

    return new Response(
      JSON.stringify({
        success: true,
        packet: data,
        seal_status: data.seal_lock ? 'LOCKED' : 'UNLOCKED',
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    console.error('❌ Error in ingest-10-9-1-packet:', error);
    return new Response(
      JSON.stringify({ error: 'Internal server error' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});
