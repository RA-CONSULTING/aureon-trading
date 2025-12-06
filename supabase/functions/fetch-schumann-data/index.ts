import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

/**
 * Schumann Resonance Data Endpoint
 * Returns realistic Schumann resonance data based on time of day
 * and natural Earth electromagnetic variations
 */
serve(async (req) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const now = Date.now();
    const hourOfDay = new Date().getUTCHours();
    
    // Natural diurnal variation in Schumann resonance
    // Peak activity typically around local noon, minimum at night
    const diurnalFactor = Math.sin((hourOfDay - 6) * Math.PI / 12) * 0.08;
    
    // Base frequency with natural Earth variance (7.83 Hz ± 0.15 Hz)
    const fundamentalHz = 7.83 + diurnalFactor + (Math.random() - 0.5) * 0.05;
    
    // Amplitude varies with solar activity and ionospheric conditions
    const amplitude = 0.65 + diurnalFactor * 0.3 + (Math.random() - 0.5) * 0.1;
    
    // Quality factor (Q) of the resonance
    const quality = 0.70 + (Math.random() - 0.5) * 0.1;
    
    // Variance in measurements
    const variance = 0.05 + Math.random() * 0.03;
    
    // Calculate coherence boost based on how close to ideal 7.83 Hz
    const deviation = Math.abs(fundamentalHz - 7.83);
    const coherenceBoost = Math.max(0, (0.15 - deviation) / 0.15) * 0.12;
    
    // Determine resonance phase
    let resonancePhase = 'stable';
    if (amplitude > 0.85 && quality > 0.85) resonancePhase = 'peak';
    else if (amplitude > 0.7 || quality > 0.75) resonancePhase = 'elevated';
    else if (amplitude < 0.4 || quality < 0.6) resonancePhase = 'disturbed';
    
    // Generate harmonics (Schumann resonance has multiple modes)
    const harmonics = [
      { frequency: fundamentalHz, amplitude: amplitude, name: 'Fundamental (n=1)' },
      { frequency: 14.3 + (Math.random() - 0.5) * 0.2, amplitude: amplitude * 0.7, name: '2nd Mode (n=2)' },
      { frequency: 20.8 + (Math.random() - 0.5) * 0.3, amplitude: amplitude * 0.5, name: '3rd Mode (n=3)' },
      { frequency: 27.3 + (Math.random() - 0.5) * 0.4, amplitude: amplitude * 0.35, name: '4th Mode (n=4)' },
      { frequency: 33.8 + (Math.random() - 0.5) * 0.5, amplitude: amplitude * 0.25, name: '5th Mode (n=5)' },
      { frequency: 39.0 + (Math.random() - 0.5) * 0.5, amplitude: amplitude * 0.18, name: '6th Mode (n=6)' },
      { frequency: 45.0 + (Math.random() - 0.5) * 0.5, amplitude: amplitude * 0.12, name: '7th Mode (n=7)' },
    ];

    const schumannData = {
      fundamentalHz,
      amplitude,
      quality,
      variance,
      timestamp: new Date().toISOString(),
      coherenceBoost,
      resonancePhase,
      harmonics,
      metadata: {
        source: 'AUREON Schumann Monitor',
        hourOfDay,
        diurnalFactor,
      },
    };

    console.log(`📡 Schumann data: ${fundamentalHz.toFixed(3)} Hz, ${resonancePhase}`);

    return new Response(JSON.stringify(schumannData), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  } catch (error) {
    console.error('❌ Schumann data error:', error);
    const message = error instanceof Error ? error.message : 'Unknown error';
    return new Response(JSON.stringify({ error: message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
