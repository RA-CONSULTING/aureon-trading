import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

interface SolarWindData {
  timestamp: string;
  speed: number;
  density: number;
  temperature: number;
  bz: number;
}

interface MagnetometerData {
  timestamp: string;
  hComponent: number;
  intensity: number;
  kIndex: number;
}

interface AuroraForecast {
  timestamp: string;
  kpIndex: number;
  probability: number;
  viewingLatitude: number;
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    console.log('[fetch-noaa-space-weather] Fetching NOAA space weather data');

    // Fetch real-time solar wind data from NOAA SWPC
    const solarWindResponse = await fetch(
      'https://services.swpc.noaa.gov/products/solar-wind/mag-7-day.json'
    );
    const solarWindRaw = await solarWindResponse.json();
    
    // Parse solar wind data (skip header row)
    const solarWindData: SolarWindData[] = solarWindRaw.slice(1, 25).map((row: any[]) => ({
      timestamp: `${row[0]}T${row[1]}Z`,
      speed: parseFloat(row[5]) || 0,
      density: parseFloat(row[2]) || 0,
      temperature: parseFloat(row[3]) || 0,
      bz: parseFloat(row[4]) || 0,
    }));

    // Fetch magnetometer data
    const magnetometerResponse = await fetch(
      'https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json'
    );
    const magnetometerRaw = await magnetometerResponse.json();
    
    // Parse magnetometer data (skip header)
    const magnetometerData: MagnetometerData[] = magnetometerRaw.slice(1, 9).map((row: any[]) => ({
      timestamp: row[0],
      kIndex: parseFloat(row[1]) || 0,
      hComponent: Math.random() * 100 - 50, // Mock H component
      intensity: Math.random() * 60000 + 45000, // Mock intensity
    }));

    // Fetch 3-day forecast
    const forecastResponse = await fetch(
      'https://services.swpc.noaa.gov/products/noaa-planetary-k-index-forecast.json'
    );
    const forecastRaw = await forecastResponse.json();
    
    // Parse aurora forecast
    const auroraForecast: AuroraForecast[] = forecastRaw.slice(1, 13).map((row: any[]) => {
      const kp = parseFloat(row[2]) || 0;
      return {
        timestamp: row[0],
        kpIndex: kp,
        probability: Math.min(100, (kp / 9) * 100),
        viewingLatitude: 66 - (kp * 4), // Aurora oval latitude
      };
    });

    // Current conditions summary
    const currentSolarWind = solarWindData[solarWindData.length - 1];
    const currentMag = magnetometerData[magnetometerData.length - 1];
    const currentForecast = auroraForecast[0];

    // Calculate storm level
    const stormLevel = 
      currentMag.kIndex >= 8 ? 'Severe' :
      currentMag.kIndex >= 6 ? 'Strong' :
      currentMag.kIndex >= 5 ? 'Moderate' :
      currentMag.kIndex >= 4 ? 'Minor' :
      'Quiet';

    // Calculate aurora visibility
    const auroraVisible = currentForecast.kpIndex >= 5;
    const auroraLocation = 
      currentForecast.kpIndex >= 7 ? 'Mid-latitudes (45°+)' :
      currentForecast.kpIndex >= 5 ? 'High latitudes (55°+)' :
      currentForecast.kpIndex >= 3 ? 'Arctic Circle (65°+)' :
      'Polar regions only';

    const response = {
      timestamp: new Date().toISOString(),
      solarWind: {
        current: currentSolarWind,
        history: solarWindData,
        status: currentSolarWind.speed > 600 ? 'High' : currentSolarWind.speed > 400 ? 'Moderate' : 'Normal',
      },
      magnetometer: {
        current: currentMag,
        history: magnetometerData,
        stormLevel,
      },
      aurora: {
        current: currentForecast,
        forecast: auroraForecast,
        visible: auroraVisible,
        location: auroraLocation,
      },
      alerts: {
        solarWindAlert: currentSolarWind.speed > 700,
        magneticStorm: currentMag.kIndex >= 5,
        auroraAlert: currentForecast.kpIndex >= 5,
      }
    };

    console.log('[fetch-noaa-space-weather] Data fetched successfully');

    return new Response(JSON.stringify(response), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });

  } catch (error) {
    console.error('[fetch-noaa-space-weather] Error:', error);
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
