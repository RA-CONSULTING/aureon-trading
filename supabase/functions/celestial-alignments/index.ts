import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

// Calculate moon phase (0 = new moon, 0.5 = full moon, 1 = new moon)
function calculateMoonPhase(date: Date): number {
  const year = date.getFullYear();
  const month = date.getMonth() + 1;
  const day = date.getDate();
  
  let c, e, jd, b;
  
  if (month < 3) {
    const yearAdjust = year - 1;
    const monthAdjust = month + 12;
    c = yearAdjust / 100;
    e = 2 - c + Math.floor(c / 4);
    jd = Math.floor(365.25 * (yearAdjust + 4716)) + Math.floor(30.6001 * (monthAdjust + 1)) + day + e - 1524.5;
  } else {
    c = year / 100;
    e = 2 - c + Math.floor(c / 4);
    jd = Math.floor(365.25 * (year + 4716)) + Math.floor(30.6001 * (month + 1)) + day + e - 1524.5;
  }
  
  const daysSinceNew = jd - 2451549.5;
  const newMoons = daysSinceNew / 29.53;
  const phase = (newMoons - Math.floor(newMoons));
  
  return phase;
}

// Get moon phase name and power
function getMoonPhaseInfo(phase: number): { name: string; power: number; influence: string } {
  if (phase < 0.03 || phase > 0.97) {
    return { name: 'New Moon', power: 1.5, influence: 'New Beginnings, Manifestation' };
  } else if (phase < 0.22) {
    return { name: 'Waxing Crescent', power: 1.1, influence: 'Growth, Intention Setting' };
  } else if (phase < 0.28) {
    return { name: 'First Quarter', power: 1.3, influence: 'Action, Decision Making' };
  } else if (phase < 0.47) {
    return { name: 'Waxing Gibbous', power: 1.2, influence: 'Refinement, Building' };
  } else if (phase < 0.53) {
    return { name: 'Full Moon', power: 2.0, influence: 'Completion, Illumination, Peak Power' };
  } else if (phase < 0.72) {
    return { name: 'Waning Gibbous', power: 1.2, influence: 'Gratitude, Sharing' };
  } else if (phase < 0.78) {
    return { name: 'Last Quarter', power: 1.3, influence: 'Release, Letting Go' };
  } else {
    return { name: 'Waning Crescent', power: 1.1, influence: 'Reflection, Rest' };
  }
}

// Calculate planetary positions (simplified - major planets only)
function calculatePlanetaryAlignment(date: Date): { score: number; alignedPlanets: string[] } {
  const dayOfYear = Math.floor((date.getTime() - new Date(date.getFullYear(), 0, 0).getTime()) / 86400000);
  
  // Simplified planetary periods (days)
  const mercury = (dayOfYear % 88) / 88;
  const venus = (dayOfYear % 225) / 225;
  const mars = (dayOfYear % 687) / 687;
  const jupiter = (dayOfYear % 4333) / 4333;
  const saturn = (dayOfYear % 10759) / 10759;
  
  const alignedPlanets: string[] = [];
  let alignmentScore = 0;
  
  // Check for conjunctions (planets in similar positions - within 0.1 phase)
  const positions = [
    { name: 'Mercury', pos: mercury },
    { name: 'Venus', pos: venus },
    { name: 'Mars', pos: mars },
    { name: 'Jupiter', pos: jupiter },
    { name: 'Saturn', pos: saturn }
  ];
  
  for (let i = 0; i < positions.length; i++) {
    for (let j = i + 1; j < positions.length; j++) {
      const diff = Math.abs(positions[i].pos - positions[j].pos);
      if (diff < 0.1 || diff > 0.9) {
        alignmentScore += 0.2;
        if (!alignedPlanets.includes(positions[i].name)) alignedPlanets.push(positions[i].name);
        if (!alignedPlanets.includes(positions[j].name)) alignedPlanets.push(positions[j].name);
      }
    }
  }
  
  return { score: Math.min(alignmentScore, 1.0), alignedPlanets };
}

// Get solar activity estimation (simplified - based on solar cycle)
function calculateSolarActivity(date: Date): { activity: number; phase: string; power: number } {
  // Solar cycle is approximately 11 years (4018 days)
  const solarCycleStart = new Date('2019-12-01'); // Solar Cycle 25 started
  const daysSinceStart = (date.getTime() - solarCycleStart.getTime()) / 86400000;
  const cyclePosition = (daysSinceStart % 4018) / 4018;
  
  // Peak activity around 0.4-0.6 of cycle
  let activity: number;
  let phase: string;
  let power: number;
  
  if (cyclePosition < 0.3) {
    phase = 'Solar Minimum';
    activity = 0.3 + cyclePosition;
    power = 1.0;
  } else if (cyclePosition < 0.7) {
    phase = 'Solar Maximum';
    activity = 0.8 + Math.sin((cyclePosition - 0.3) * Math.PI / 0.4) * 0.2;
    power = 1.5;
  } else {
    phase = 'Solar Declining';
    activity = 0.8 - (cyclePosition - 0.7) * 1.5;
    power = 1.1;
  }
  
  return { activity: Math.max(0, Math.min(1, activity)), phase, power };
}

// Calculate equinox and solstice proximity
function calculateSeasonalAlignment(date: Date): { name: string; proximity: number; power: number } {
  const year = date.getFullYear();
  const dayOfYear = Math.floor((date.getTime() - new Date(year, 0, 0).getTime()) / 86400000);
  
  // Approximate dates (for Northern Hemisphere)
  const springEquinox = 80;  // ~March 20
  const summerSolstice = 172; // ~June 21
  const autumnEquinox = 266;  // ~September 23
  const winterSolstice = 355; // ~December 21
  
  const events = [
    { name: 'Spring Equinox', day: springEquinox },
    { name: 'Summer Solstice', day: summerSolstice },
    { name: 'Autumn Equinox', day: autumnEquinox },
    { name: 'Winter Solstice', day: winterSolstice }
  ];
  
  let closest = events[0];
  let minDist = Math.abs(dayOfYear - events[0].day);
  
  events.forEach(event => {
    const dist = Math.abs(dayOfYear - event.day);
    if (dist < minDist) {
      minDist = dist;
      closest = event;
    }
  });
  
  // Within 7 days = high power, decays to normal after 30 days
  const proximity = Math.max(0, 1 - minDist / 30);
  const power = 1 + proximity * 0.8; // Up to 1.8x during events
  
  return { name: closest.name, proximity, power };
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    console.log('[celestial-alignments] Calculating astronomical data');
    
    const now = new Date();
    
    // Calculate moon phase
    const moonPhase = calculateMoonPhase(now);
    const moonInfo = getMoonPhaseInfo(moonPhase);
    
    // Calculate planetary alignment
    const planetary = calculatePlanetaryAlignment(now);
    
    // Calculate solar activity
    const solar = calculateSolarActivity(now);
    
    // Calculate seasonal alignment
    const seasonal = calculateSeasonalAlignment(now);
    
    // Calculate overall cosmic power multiplier
    const cosmicPower = (moonInfo.power + solar.power + seasonal.power + (1 + planetary.score)) / 4;
    
    // Determine active sacred frequencies based on alignments
    const sacredFrequencies: number[] = [];
    
    // Moon phase influences
    if (moonInfo.name.includes('Full')) {
      sacredFrequencies.push(528, 639, 741); // Heart, connection, awakening
    } else if (moonInfo.name.includes('New')) {
      sacredFrequencies.push(396, 417, 528); // Liberation, change, love
    }
    
    // Solar activity influences
    if (solar.phase === 'Solar Maximum') {
      sacredFrequencies.push(852, 963); // Higher consciousness
    }
    
    // Seasonal influences
    if (seasonal.name.includes('Equinox')) {
      sacredFrequencies.push(528); // Balance
    } else if (seasonal.name.includes('Solstice')) {
      sacredFrequencies.push(396, 963); // Grounding and cosmic
    }
    
    // Planetary alignment influences
    if (planetary.score > 0.5) {
      sacredFrequencies.push(741, 852); // Intuition and spiritual order
    }
    
    const result = {
      timestamp: now.toISOString(),
      moon: {
        phase: moonPhase,
        name: moonInfo.name,
        power: moonInfo.power,
        influence: moonInfo.influence,
        illumination: Math.abs(moonPhase - 0.5) * 200 // 0-100%
      },
      solar: {
        activity: solar.activity,
        phase: solar.phase,
        power: solar.power,
        cycleDay: Math.floor(((now.getTime() - new Date('2019-12-01').getTime()) / 86400000) % 4018)
      },
      planetary: {
        alignmentScore: planetary.score,
        alignedPlanets: planetary.alignedPlanets,
        power: 1 + planetary.score * 0.5
      },
      seasonal: {
        name: seasonal.name,
        proximity: seasonal.proximity,
        power: seasonal.power,
        daysUntil: Math.round(seasonal.proximity * 30)
      },
      cosmic: {
        overallPower: cosmicPower,
        coherenceBoost: (cosmicPower - 1) * 0.15, // Up to +15% coherence
        sacredFrequencies: [...new Set(sacredFrequencies)].sort((a, b) => a - b)
      }
    };
    
    console.log(`[celestial-alignments] Cosmic power: ${cosmicPower.toFixed(2)}x`);
    
    return new Response(JSON.stringify(result), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 200,
    });
  } catch (error) {
    console.error('[celestial-alignments] Error:', error);
    const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
    return new Response(
      JSON.stringify({ error: errorMessage }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 500 
      }
    );
  }
});
