// Auris Harmonic Engine - Prime Sentinel Frequency Calculator
export interface AurisCodex {
  schema_version: string;
  identity: {
    name: string;
    dob_iso: string;
    prime_ratio_10_9_1: number[];
    t0_hz: number;
    phi: number;
    lattice_id_formula: string;
    oath: string;
  };
  base_modes_hz: number[];
  band_limits_hz: { min: number; max: number };
  bands: Record<string, { range_hz: [number, number] }>;
  personalization: {
    gaia_hz: number;
    phi: number;
    t0_hz: number;
    t0_mix: number;
    phi_mix: number;
    formula: string;
  };
  weights: {
    ten_nine_one: {
      vector: { alpha: number; theta: number; delta: number };
      normalize_to: number;
    };
  };
  intervals: Record<string, { ratio?: number[]; ratio_float?: number }>;
}

export interface EmotionRecipe {
  from: string;
  mode_idx: number;
  interval: string;
  weight: number;
  band_hint: string;
}

export interface Emotion {
  comment: string;
  recipe: EmotionRecipe[];
  color_hex: string;
}

export class AurisHarmonicEngine {
  private codex: AurisCodex | null = null;
  private emotions: Record<string, Emotion> = {};

  async initialize() {
    try {
      const [codexRes, emotionsRes] = await Promise.all([
        fetch('/auris_codex.json'),
        fetch('/auris_emotions.json')
      ]);
      
      this.codex = await codexRes.json();
      const emotionsData = await emotionsRes.json();
      this.emotions = emotionsData.emotions;
    } catch (error) {
      console.error('Failed to load Auris Codex:', error);
    }
  }

  // Calculate personalized frequency using 10-9-1 law and phi modulation
  calculatePersonalizedFrequency(baseHz: number, intervalRatio: number, bandHint: string): number {
    if (!this.codex) return baseHz;

    const { t0_hz, t0_mix, phi, phi_mix } = this.codex.personalization;
    const { min, max } = this.codex.band_limits_hz;

    // Apply interval ratio
    let freq = baseHz * intervalRatio;

    // Apply personalization formula
    freq = freq * (1 + t0_mix * (t0_hz / 3000)) * (1 + phi_mix * (phi - 1));

    // Apply 10-9-1 weighting based on band hint
    const weights = this.codex.weights.ten_nine_one.vector;
    const bandWeight = weights[bandHint as keyof typeof weights] || weights.alpha;
    freq = freq * (bandWeight / this.codex.weights.ten_nine_one.normalize_to);

    // Fold into band limits
    while (freq > max) freq /= 2;
    while (freq < min) freq *= 2;

    return Math.max(min, Math.min(max, freq));
  }

  // Get interval ratio from codex
  getIntervalRatio(intervalName: string): number {
    if (!this.codex) return 1;
    
    const interval = this.codex.intervals[intervalName];
    if (!interval) return 1;
    
    if (interval.ratio_float) return interval.ratio_float;
    if (interval.ratio) return interval.ratio[0] / interval.ratio[1];
    
    return 1;
  }

  // Calculate emotion frequency signature
  calculateEmotionFrequency(emotionName: string): { frequency: number; color: string; components: any[] } {
    if (!this.codex || !this.emotions[emotionName]) {
      return { frequency: 7.83, color: '#8FD3F4', components: [] };
    }

    const emotion = this.emotions[emotionName];
    const components = [];
    let totalWeight = 0;
    let weightedFreq = 0;

    for (const recipe of emotion.recipe) {
      const baseHz = this.codex.base_modes_hz[recipe.mode_idx] || 7.83;
      const intervalRatio = this.getIntervalRatio(recipe.interval);
      const freq = this.calculatePersonalizedFrequency(baseHz, intervalRatio, recipe.band_hint);
      
      components.push({
        base: baseHz,
        interval: recipe.interval,
        ratio: intervalRatio,
        frequency: freq,
        weight: recipe.weight,
        band: recipe.band_hint
      });

      weightedFreq += freq * recipe.weight;
      totalWeight += recipe.weight;
    }

    const finalFreq = totalWeight > 0 ? weightedFreq / totalWeight : 7.83;

    return {
      frequency: Math.round(finalFreq * 100) / 100,
      color: emotion.color_hex,
      components
    };
  }

  // Get all available emotions
  getAvailableEmotions(): string[] {
    return Object.keys(this.emotions);
  }

  // Get Prime Sentinel identity
  getIdentity() {
    return this.codex?.identity || null;
  }

  // Calculate 10-9-1 coherence score
  calculate10_9_1_Coherence(frequencies: number[]): number {
    if (!this.codex || frequencies.length === 0) return 0;

    const weights = this.codex.weights.ten_nine_one.vector;
    const alphaRange = this.codex.bands.alpha.range_hz;
    const thetaRange = this.codex.bands.theta.range_hz;
    const deltaRange = this.codex.bands.delta.range_hz;

    let alphaScore = 0, thetaScore = 0, deltaScore = 0;
    let count = 0;

    frequencies.forEach(freq => {
      if (freq >= alphaRange[0] && freq <= alphaRange[1]) {
        alphaScore += weights.alpha;
      } else if (freq >= thetaRange[0] && freq <= thetaRange[1]) {
        thetaScore += weights.theta;
      } else if (freq >= deltaRange[0] && freq <= deltaRange[1]) {
        deltaScore += weights.delta;
      }
      count++;
    });

    if (count === 0) return 0;

    const totalScore = alphaScore + thetaScore + deltaScore;
    const maxPossible = count * weights.alpha; // Alpha is highest weight
    
    return Math.min(100, (totalScore / maxPossible) * 100);
  }
}

export const aurisEngine = new AurisHarmonicEngine();