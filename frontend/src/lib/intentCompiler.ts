/**
 * Intent Compiler
 * ---------------
 * Symbolic compiler that translates human intent to harmonic frequencies
 * Based on the symbolic_compiler_layer.json structure
 */

export interface IntentResult {
  frequencies: number[];
  decay?: number;
  harmonics?: number[];
  emotion?: string;
}

// Emotional frequency mappings (Hz)
const EMOTION_FREQUENCIES: Record<string, number[]> = {
  peace: [7.83, 136.1, 256], // Schumann + OM + C
  joy: [528, 741, 852], // Solfeggio frequencies
  love: [528, 693.3, 1111], // Love frequency + harmonics
  healing: [174, 285, 396, 417], // Lower solfeggio
  transformation: [741, 852, 963], // Higher solfeggio
  grounding: [7.83, 14.3, 20.8], // Pure Schumann
  clarity: [40, 80, 160], // Gamma + harmonics
  compassion: [341.3, 528, 852], // Heart chakra based
  courage: [456.8, 741, 963], // Solar plexus + higher
  wisdom: [426.7, 639, 852] // Throat + heart + third eye
};

// Intent keywords to emotion mapping
const INTENT_KEYWORDS: Record<string, string> = {
  'peace': 'peace',
  'calm': 'peace',
  'serenity': 'peace',
  'joy': 'joy',
  'happiness': 'joy',
  'bliss': 'joy',
  'love': 'love',
  'compassion': 'compassion',
  'kindness': 'compassion',
  'heal': 'healing',
  'healing': 'healing',
  'restore': 'healing',
  'transform': 'transformation',
  'change': 'transformation',
  'evolve': 'transformation',
  'ground': 'grounding',
  'center': 'grounding',
  'focus': 'clarity',
  'clarity': 'clarity',
  'clear': 'clarity',
  'courage': 'courage',
  'strength': 'courage',
  'brave': 'courage',
  'wisdom': 'wisdom',
  'insight': 'wisdom',
  'understand': 'wisdom'
};

export class IntentCompiler {
  /**
   * Process human intent text into harmonic frequencies
   */
  async processIntent(text: string): Promise<IntentResult> {
    const words = text.toLowerCase().split(/\s+/);
    const emotions = new Set<string>();
    
    // Extract emotions from intent text
    words.forEach(word => {
      const emotion = INTENT_KEYWORDS[word];
      if (emotion) {
        emotions.add(emotion);
      }
    });

    // If no specific emotions found, default to peace/grounding
    if (emotions.size === 0) {
      emotions.add('peace');
      emotions.add('grounding');
    }

    // Combine frequencies from all detected emotions
    const allFreqs = Array.from(emotions).flatMap(emotion => 
      EMOTION_FREQUENCIES[emotion] || []
    );

    // Remove duplicates and sort
    const uniqueFreqs = [...new Set(allFreqs)].sort((a, b) => a - b);

    // Generate harmonics for fundamental frequencies
    const harmonics = uniqueFreqs.flatMap(freq => [
      freq * 2,    // Octave
      freq * 3,    // Perfect fifth
      freq * 4,    // Double octave
      freq * 1.5   // Perfect fifth below octave
    ]).filter(f => f < 2000); // Keep within reasonable range

    return {
      frequencies: uniqueFreqs,
      harmonics,
      decay: 0.8, // Default decay rate
      emotion: Array.from(emotions).join(', ')
    };
  }

  /**
   * Get frequency for specific emotion
   */
  getEmotionFrequencies(emotion: string): number[] {
    return EMOTION_FREQUENCIES[emotion.toLowerCase()] || [];
  }

  /**
   * List available emotions
   */
  getAvailableEmotions(): string[] {
    return Object.keys(EMOTION_FREQUENCIES);
  }
}

// Export singleton instance
export const intentCompiler = new IntentCompiler();