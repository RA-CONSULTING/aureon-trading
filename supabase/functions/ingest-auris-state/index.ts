import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

interface AurisNodeState {
  temporal_id: string;
  tiger_value: number;
  tiger_frequency?: number;
  falcon_value: number;
  falcon_frequency?: number;
  hummingbird_value: number;
  hummingbird_frequency?: number;
  dolphin_value: number;
  dolphin_frequency?: number;
  deer_value: number;
  deer_frequency?: number;
  owl_value: number;
  owl_frequency?: number;
  panda_value: number;
  panda_frequency?: number;
  cargoship_value: number;
  cargoship_frequency?: number;
  clownfish_value: number;
  clownfish_frequency?: number;
  dominant_node?: string;
  total_coherence?: number;
  active_nodes?: number;
  harmonic_resonance?: number;
  metadata?: Record<string, unknown>;
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseKey);

    const body: AurisNodeState = await req.json();
    console.log('[ingest-auris-state] Received:', JSON.stringify(body));

    if (!body.temporal_id) {
      throw new Error('temporal_id is required');
    }

    // Calculate dominant node (highest value)
    const nodes = [
      { name: 'tiger', value: body.tiger_value || 0 },
      { name: 'falcon', value: body.falcon_value || 0 },
      { name: 'hummingbird', value: body.hummingbird_value || 0 },
      { name: 'dolphin', value: body.dolphin_value || 0 },
      { name: 'deer', value: body.deer_value || 0 },
      { name: 'owl', value: body.owl_value || 0 },
      { name: 'panda', value: body.panda_value || 0 },
      { name: 'cargoship', value: body.cargoship_value || 0 },
      { name: 'clownfish', value: body.clownfish_value || 0 },
    ];

    const dominant = nodes.reduce((max, n) => n.value > max.value ? n : max, nodes[0]);
    const totalCoherence = nodes.reduce((sum, n) => sum + n.value, 0) / 9;
    const activeNodes = nodes.filter(n => n.value > 0.1).length;

    // Calculate harmonic resonance based on frequency alignment
    const frequencies = [741, 852, 963, 528, 396, 432, 412, 174, 639];
    const values = nodes.map(n => n.value);
    let harmonicSum = 0;
    for (let i = 0; i < frequencies.length; i++) {
      // Weight by value and check for harmonic relationships
      const baseFreq = 528; // Love frequency as reference
      const ratio = frequencies[i] / baseFreq;
      const harmonicScore = Math.abs(ratio - Math.round(ratio)) < 0.1 ? 1.2 : 1.0;
      harmonicSum += values[i] * harmonicScore;
    }
    const harmonicResonance = harmonicSum / 9;

    const record = {
      temporal_id: body.temporal_id,
      tiger_value: body.tiger_value || 0,
      tiger_frequency: body.tiger_frequency || 741,
      falcon_value: body.falcon_value || 0,
      falcon_frequency: body.falcon_frequency || 852,
      hummingbird_value: body.hummingbird_value || 0,
      hummingbird_frequency: body.hummingbird_frequency || 963,
      dolphin_value: body.dolphin_value || 0,
      dolphin_frequency: body.dolphin_frequency || 528,
      deer_value: body.deer_value || 0,
      deer_frequency: body.deer_frequency || 396,
      owl_value: body.owl_value || 0,
      owl_frequency: body.owl_frequency || 432,
      panda_value: body.panda_value || 0,
      panda_frequency: body.panda_frequency || 412,
      cargoship_value: body.cargoship_value || 0,
      cargoship_frequency: body.cargoship_frequency || 174,
      clownfish_value: body.clownfish_value || 0,
      clownfish_frequency: body.clownfish_frequency || 639,
      dominant_node: body.dominant_node || dominant.name,
      total_coherence: body.total_coherence ?? totalCoherence,
      active_nodes: body.active_nodes ?? activeNodes,
      harmonic_resonance: body.harmonic_resonance ?? harmonicResonance,
      metadata: body.metadata || {},
    };

    const { data, error } = await supabase
      .from('auris_node_states')
      .insert(record)
      .select()
      .single();

    if (error) {
      console.error('[ingest-auris-state] Insert error:', error);
      throw error;
    }

    console.log('[ingest-auris-state] Inserted:', data.id);

    return new Response(JSON.stringify({ success: true, id: data.id }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });

  } catch (error) {
    console.error('[ingest-auris-state] Error:', error);
    const message = error instanceof Error ? error.message : 'Unknown error';
    return new Response(JSON.stringify({ error: message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
