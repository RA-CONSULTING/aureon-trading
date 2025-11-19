import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.39.7";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

interface HourlyFieldData {
  hour: number;
  seismicStability: number;
  schumannCoherence: number;
  solarWindStability: number;
  kpIndexNormalized: number;
  tradingCoherence: number;
  lighthouseEvents: number;
  unifiedFieldCoherence: number;
  optimalWindow: boolean;
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    console.log('[unified-field-analysis] Starting unified field analysis');

    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseKey);

    // Fetch 24 hours of data
    const twentyFourHoursAgo = new Date();
    twentyFourHoursAgo.setHours(twentyFourHoursAgo.getHours() - 24);

    // Initialize hourly data buckets
    const hourlyData: Map<number, {
      seismicEvents: number[];
      schumannReadings: number[];
      solarWindSpeeds: number[];
      kpIndices: number[];
      coherenceValues: number[];
      lighthouseCount: number;
    }> = new Map();

    for (let i = 0; i < 24; i++) {
      hourlyData.set(i, {
        seismicEvents: [],
        schumannReadings: [],
        solarWindSpeeds: [],
        kpIndices: [],
        coherenceValues: [],
        lighthouseCount: 0,
      });
    }

    // Fetch trading coherence history
    const { data: coherenceHistory } = await supabase
      .from('coherence_history')
      .select('coherence, lambda_value, timestamp, hour_of_day')
      .gte('timestamp', twentyFourHoursAgo.toISOString())
      .order('timestamp', { ascending: true });

    if (coherenceHistory) {
      for (const record of coherenceHistory) {
        const hour = record.hour_of_day;
        const bucket = hourlyData.get(hour);
        if (bucket) {
          bucket.coherenceValues.push(record.coherence);
        }
      }
    }

    // Fetch lighthouse events
    const { data: lighthouseEvents } = await supabase
      .from('lighthouse_events')
      .select('timestamp, is_lhe, coherence')
      .gte('timestamp', twentyFourHoursAgo.toISOString())
      .order('timestamp', { ascending: true });

    if (lighthouseEvents) {
      for (const event of lighthouseEvents) {
        const hour = new Date(event.timestamp).getHours();
        const bucket = hourlyData.get(hour);
        if (bucket && event.is_lhe) {
          bucket.lighthouseCount += 1;
        }
      }
    }

    // Fetch consciousness field history for Schumann data
    const { data: consciousnessHistory } = await supabase
      .from('consciousness_field_history')
      .select('schumann_frequency, schumann_coherence_boost, timestamp')
      .gte('timestamp', twentyFourHoursAgo.toISOString())
      .order('timestamp', { ascending: true });

    if (consciousnessHistory) {
      for (const record of consciousnessHistory) {
        const hour = new Date(record.timestamp).getHours();
        const bucket = hourlyData.get(hour);
        if (bucket) {
          bucket.schumannReadings.push(record.schumann_coherence_boost);
        }
      }
    }

    // Fetch USGS seismic data
    try {
      const seismicResponse = await fetch(
        `https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=${twentyFourHoursAgo.toISOString().split('T')[0]}&minmagnitude=4.0`
      );
      const seismicData = await seismicResponse.json();
      
      for (const feature of seismicData.features || []) {
        const eventTime = new Date(feature.properties.time);
        const hour = eventTime.getHours();
        const bucket = hourlyData.get(hour);
        if (bucket) {
          bucket.seismicEvents.push(feature.properties.mag);
        }
      }
    } catch (error) {
      console.log('[unified-field-analysis] Seismic data unavailable:', error);
    }

    // Fetch NOAA space weather data
    try {
      const solarWindResponse = await fetch(
        'https://services.swpc.noaa.gov/products/solar-wind/mag-7-day.json'
      );
      const solarWindRaw = await solarWindResponse.json();
      
      for (const row of solarWindRaw.slice(1)) {
        const timestamp = new Date(`${row[0]}T${row[1]}Z`);
        const hour = timestamp.getHours();
        const bucket = hourlyData.get(hour);
        if (bucket) {
          const speed = parseFloat(row[5]) || 0;
          bucket.solarWindSpeeds.push(speed);
        }
      }

      const kpResponse = await fetch(
        'https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json'
      );
      const kpRaw = await kpResponse.json();
      
      for (const row of kpRaw.slice(1)) {
        const timestamp = new Date(row[0]);
        const hour = timestamp.getHours();
        const bucket = hourlyData.get(hour);
        if (bucket) {
          const kp = parseFloat(row[1]) || 0;
          bucket.kpIndices.push(kp);
        }
      }
    } catch (error) {
      console.log('[unified-field-analysis] Space weather data unavailable:', error);
    }

    // Calculate unified field coherence for each hour
    const timeline: HourlyFieldData[] = [];
    
    for (let hour = 0; hour < 24; hour++) {
      const bucket = hourlyData.get(hour)!;
      
      // Calculate averages and normalize to 0-1 scale
      const avgSeismicMag = bucket.seismicEvents.length > 0
        ? bucket.seismicEvents.reduce((a, b) => a + b, 0) / bucket.seismicEvents.length
        : 5.0;
      const seismicStability = Math.max(0, 1 - (avgSeismicMag - 4.0) / 3.0); // Lower magnitude = more stable

      const schumannCoherence = bucket.schumannReadings.length > 0
        ? bucket.schumannReadings.reduce((a, b) => a + b, 0) / bucket.schumannReadings.length
        : 0.5;

      const avgSolarWind = bucket.solarWindSpeeds.length > 0
        ? bucket.solarWindSpeeds.reduce((a, b) => a + b, 0) / bucket.solarWindSpeeds.length
        : 400;
      const solarWindStability = Math.max(0, 1 - Math.abs(avgSolarWind - 400) / 400); // Closer to 400 = more stable

      const avgKp = bucket.kpIndices.length > 0
        ? bucket.kpIndices.reduce((a, b) => a + b, 0) / bucket.kpIndices.length
        : 2.0;
      const kpIndexNormalized = Math.max(0, 1 - avgKp / 9); // Lower Kp = more stable

      const tradingCoherence = bucket.coherenceValues.length > 0
        ? bucket.coherenceValues.reduce((a, b) => a + b, 0) / bucket.coherenceValues.length
        : 0.5;

      // Calculate unified field coherence (weighted average)
      const unifiedFieldCoherence = (
        seismicStability * 0.15 +
        schumannCoherence * 0.25 +
        solarWindStability * 0.20 +
        kpIndexNormalized * 0.20 +
        tradingCoherence * 0.20
      );

      // Optimal window: unified coherence > 0.75 AND lighthouse events present
      const optimalWindow = unifiedFieldCoherence > 0.75 && bucket.lighthouseCount > 0;

      timeline.push({
        hour,
        seismicStability,
        schumannCoherence,
        solarWindStability,
        kpIndexNormalized,
        tradingCoherence,
        lighthouseEvents: bucket.lighthouseCount,
        unifiedFieldCoherence,
        optimalWindow,
      });
    }

    // Identify recurring patterns (hours that are frequently optimal)
    const optimalHours = timeline.filter(h => h.optimalWindow).map(h => h.hour);
    const recurringPatterns = [];
    
    // Find clusters of optimal hours
    for (let i = 0; i < optimalHours.length; i++) {
      const hour = optimalHours[i];
      const cluster = [hour];
      
      // Check adjacent hours
      for (let j = 1; j <= 3; j++) {
        if (optimalHours.includes((hour + j) % 24)) {
          cluster.push((hour + j) % 24);
        }
        if (optimalHours.includes((hour - j + 24) % 24)) {
          cluster.unshift((hour - j + 24) % 24);
        }
      }
      
      if (cluster.length >= 2) {
        recurringPatterns.push({
          startHour: Math.min(...cluster),
          endHour: Math.max(...cluster),
          duration: cluster.length,
          avgCoherence: cluster.reduce((sum, h) => 
            sum + timeline.find(t => t.hour === h)!.unifiedFieldCoherence, 0
          ) / cluster.length,
        });
      }
    }

    // Remove duplicate patterns
    const uniquePatterns = recurringPatterns.filter((pattern, index, self) =>
      index === self.findIndex(p => p.startHour === pattern.startHour && p.endHour === pattern.endHour)
    );

    // Calculate peak coherence periods
    const sortedByCoherence = [...timeline].sort((a, b) => b.unifiedFieldCoherence - a.unifiedFieldCoherence);
    const topPeriods = sortedByCoherence.slice(0, 5).map(p => ({
      hour: p.hour,
      coherence: p.unifiedFieldCoherence,
      hasLHE: p.lighthouseEvents > 0,
    }));

    const response = {
      timestamp: new Date().toISOString(),
      timeline,
      statistics: {
        avgUnifiedCoherence: timeline.reduce((sum, h) => sum + h.unifiedFieldCoherence, 0) / 24,
        totalOptimalHours: optimalHours.length,
        totalLighthouseEvents: timeline.reduce((sum, h) => sum + h.lighthouseEvents, 0),
        peakCoherenceHour: sortedByCoherence[0].hour,
        peakCoherence: sortedByCoherence[0].unifiedFieldCoherence,
      },
      recurringPatterns: uniquePatterns,
      topPeriods,
      insights: {
        bestTradingWindow: uniquePatterns.length > 0 ? uniquePatterns[0] : null,
        fieldAlignment: timeline.filter(h => h.unifiedFieldCoherence > 0.8).length > 6 ? 'EXCELLENT' :
                       timeline.filter(h => h.unifiedFieldCoherence > 0.7).length > 4 ? 'GOOD' :
                       'MODERATE',
      }
    };

    console.log('[unified-field-analysis] Analysis complete');

    return new Response(JSON.stringify(response), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });

  } catch (error) {
    console.error('[unified-field-analysis] Error:', error);
    const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
    return new Response(
      JSON.stringify({ error: errorMessage }),
      { 
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    );
  }
});
