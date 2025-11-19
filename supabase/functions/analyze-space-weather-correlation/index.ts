import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.39.7";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

interface SpaceWeatherCorrelation {
  timestamp: string;
  solarWindSpeed: number;
  kpIndex: number;
  coherence: number;
  lighthouseSignal: number;
  signalStrength: number;
  isLHE: boolean;
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    console.log('[analyze-space-weather-correlation] Starting analysis');

    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseKey);

    // Fetch recent solar wind and magnetometer data from NOAA
    const solarWindResponse = await fetch(
      'https://services.swpc.noaa.gov/products/solar-wind/mag-7-day.json'
    );
    const solarWindRaw = await solarWindResponse.json();
    
    const magnetometerResponse = await fetch(
      'https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json'
    );
    const magnetometerRaw = await magnetometerResponse.json();

    // Parse NOAA data
    const solarWindData = solarWindRaw.slice(1, 169).map((row: any[]) => ({
      timestamp: new Date(`${row[0]}T${row[1]}Z`),
      speed: parseFloat(row[5]) || 0,
      bz: parseFloat(row[4]) || 0,
    }));

    const kpData = magnetometerRaw.slice(1).map((row: any[]) => ({
      timestamp: new Date(row[0]),
      kpIndex: parseFloat(row[1]) || 0,
    }));

    // Fetch trading signals from last 7 days
    const sevenDaysAgo = new Date();
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);

    const { data: signals, error: signalsError } = await supabase
      .from('trading_signals')
      .select('timestamp, coherence, lighthouse_value, strength')
      .gte('timestamp', sevenDaysAgo.toISOString())
      .order('timestamp', { ascending: true });

    if (signalsError) throw signalsError;

    const { data: lighthouseEvents, error: lheError } = await supabase
      .from('lighthouse_events')
      .select('timestamp, coherence, lighthouse_signal, is_lhe')
      .gte('timestamp', sevenDaysAgo.toISOString())
      .order('timestamp', { ascending: true });

    if (lheError) throw lheError;

    // Correlate data by matching timestamps (within 1 hour window)
    const correlations: SpaceWeatherCorrelation[] = [];
    const hourInMs = 60 * 60 * 1000;

    for (const signal of signals || []) {
      const signalTime = new Date(signal.timestamp).getTime();
      
      // Find closest solar wind data
      const closestSolarWind = solarWindData.find((sw: any) => 
        Math.abs(sw.timestamp.getTime() - signalTime) < hourInMs
      );
      
      // Find closest Kp data
      const closestKp = kpData.find((kp: any) => 
        Math.abs(kp.timestamp.getTime() - signalTime) < hourInMs
      );

      if (closestSolarWind && closestKp) {
        const matchingLHE = lighthouseEvents?.find(lhe => 
          Math.abs(new Date(lhe.timestamp).getTime() - signalTime) < 5 * 60 * 1000 // 5 min window
        );

        correlations.push({
          timestamp: signal.timestamp,
          solarWindSpeed: closestSolarWind.speed,
          kpIndex: closestKp.kpIndex,
          coherence: signal.coherence,
          lighthouseSignal: signal.lighthouse_value,
          signalStrength: signal.strength,
          isLHE: matchingLHE?.is_lhe || false,
        });
      }
    }

    // Calculate correlation statistics
    const avgCoherenceByKp: Record<number, { total: number; count: number; lheCount: number }> = {};
    const avgCoherenceBySolarWind: Record<number, { total: number; count: number; optimalCount: number }> = {};

    for (const corr of correlations) {
      const kpBucket = Math.floor(corr.kpIndex);
      if (!avgCoherenceByKp[kpBucket]) {
        avgCoherenceByKp[kpBucket] = { total: 0, count: 0, lheCount: 0 };
      }
      avgCoherenceByKp[kpBucket].total += corr.coherence;
      avgCoherenceByKp[kpBucket].count += 1;
      if (corr.isLHE) avgCoherenceByKp[kpBucket].lheCount += 1;

      const swBucket = Math.floor(corr.solarWindSpeed / 100) * 100;
      if (!avgCoherenceBySolarWind[swBucket]) {
        avgCoherenceBySolarWind[swBucket] = { total: 0, count: 0, optimalCount: 0 };
      }
      avgCoherenceBySolarWind[swBucket].total += corr.coherence;
      avgCoherenceBySolarWind[swBucket].count += 1;
      if (corr.signalStrength > 0.7) avgCoherenceBySolarWind[swBucket].optimalCount += 1;
    }

    const kpCorrelation = Object.entries(avgCoherenceByKp).map(([kp, data]) => ({
      kpIndex: parseInt(kp),
      avgCoherence: data.total / data.count,
      lheRate: (data.lheCount / data.count) * 100,
      sampleSize: data.count,
    })).sort((a, b) => a.kpIndex - b.kpIndex);

    const solarWindCorrelation = Object.entries(avgCoherenceBySolarWind).map(([speed, data]) => ({
      speedRange: parseInt(speed),
      avgCoherence: data.total / data.count,
      optimalSignalRate: (data.optimalCount / data.count) * 100,
      sampleSize: data.count,
    })).sort((a, b) => a.speedRange - b.speedRange);

    // Calculate overall correlation coefficients
    const calcPearson = (x: number[], y: number[]) => {
      const n = x.length;
      const sum_x = x.reduce((a, b) => a + b, 0);
      const sum_y = y.reduce((a, b) => a + b, 0);
      const sum_xy = x.reduce((acc, xi, i) => acc + xi * y[i], 0);
      const sum_x2 = x.reduce((acc, xi) => acc + xi * xi, 0);
      const sum_y2 = y.reduce((acc, yi) => acc + yi * yi, 0);
      
      const numerator = n * sum_xy - sum_x * sum_y;
      const denominator = Math.sqrt((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y));
      
      return denominator === 0 ? 0 : numerator / denominator;
    };

    const kpValues = correlations.map(c => c.kpIndex);
    const coherenceValues = correlations.map(c => c.coherence);
    const solarWindValues = correlations.map(c => c.solarWindSpeed);
    const signalStrengthValues = correlations.map(c => c.signalStrength);

    const kpCoherenceCorr = calcPearson(kpValues, coherenceValues);
    const solarWindCoherenceCorr = calcPearson(solarWindValues, coherenceValues);
    const solarWindSignalCorr = calcPearson(solarWindValues, signalStrengthValues);

    // Find optimal conditions
    const optimalConditions = correlations
      .filter(c => c.signalStrength > 0.7 && c.isLHE)
      .reduce((acc, curr) => {
        return {
          avgKp: acc.avgKp + curr.kpIndex,
          avgSolarWind: acc.avgSolarWind + curr.solarWindSpeed,
          count: acc.count + 1,
        };
      }, { avgKp: 0, avgSolarWind: 0, count: 0 });

    const response = {
      correlations: correlations.slice(-100), // Last 100 for chart
      statistics: {
        kpCoherenceCorrelation: kpCoherenceCorr,
        solarWindCoherenceCorrelation: solarWindCoherenceCorr,
        solarWindSignalCorrelation: solarWindSignalCorr,
        totalSamples: correlations.length,
      },
      kpCorrelation,
      solarWindCorrelation,
      optimalConditions: optimalConditions.count > 0 ? {
        avgKpIndex: optimalConditions.avgKp / optimalConditions.count,
        avgSolarWindSpeed: optimalConditions.avgSolarWind / optimalConditions.count,
        sampleSize: optimalConditions.count,
      } : null,
      insights: {
        strongCorrelation: Math.abs(kpCoherenceCorr) > 0.5 || Math.abs(solarWindCoherenceCorr) > 0.5,
        favorableKpRange: kpCorrelation.filter(k => k.avgCoherence > 0.8).map(k => k.kpIndex),
        favorableSolarWindRange: solarWindCorrelation.filter(s => s.optimalSignalRate > 50).map(s => s.speedRange),
      }
    };

    console.log('[analyze-space-weather-correlation] Analysis complete');

    return new Response(JSON.stringify(response), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });

  } catch (error) {
    console.error('[analyze-space-weather-correlation] Error:', error);
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
