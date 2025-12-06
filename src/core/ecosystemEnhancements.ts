/**
 * Ecosystem Enhancements Loader
 * Prime Sentinel: GARY LECKEY 02111991
 * 
 * Loads and applies JSON configurations as enhancements to quantum systems.
 * JSONs are not isolated data - they ENHANCE specific systems.
 */

// Types for JSON configurations
export interface AurisCodexEntry {
  name: string;
  symbol: string;
  archetype: string;
  weight: number;
  frequency?: number;
  color?: string;
}

export interface EmotionalCodexEntry {
  phase: string;
  frequencyMin: number;
  frequencyMax: number;
  color: string;
  valence: number;
  arousal: number;
}

export interface FrequencyCodexEntry {
  frequency: number;
  name: string;
  phase: string;
  color: string;
  harmonics: number[];
}

export interface SymbolicCompilerLayer {
  intent: string;
  weight: number;
  triggers: string[];
  output: string;
}

export interface EcosystemEnhancements {
  aurisCodex: AurisCodexEntry[];
  emotionalCodex: EmotionalCodexEntry[];
  frequencyCodex: FrequencyCodexEntry[];
  symbolicCompiler: SymbolicCompilerLayer[];
  loaded: boolean;
  loadedAt: number;
}

// Default empty enhancements
const defaultEnhancements: EcosystemEnhancements = {
  aurisCodex: [],
  emotionalCodex: [],
  frequencyCodex: [],
  symbolicCompiler: [],
  loaded: false,
  loadedAt: 0,
};

class EcosystemEnhancementsLoader {
  private enhancements: EcosystemEnhancements = { ...defaultEnhancements };
  private listeners: Set<(enhancements: EcosystemEnhancements) => void> = new Set();
  private isLoading = false;

  /**
   * Load all JSON enhancements from public folder
   */
  async loadAll(): Promise<EcosystemEnhancements> {
    if (this.isLoading) return this.enhancements;
    this.isLoading = true;

    console.log('🔮 Loading Ecosystem Enhancements...');

    try {
      const [auris, emotional, frequency, symbolic] = await Promise.all([
        this.loadJSON<AurisCodexEntry[]>('/auris_codex.json'),
        this.loadJSON<EmotionalCodexEntry[]>('/emotional_codex.json'),
        this.loadJSON<FrequencyCodexEntry[]>('/emotional_frequency_codex.json'),
        this.loadJSON<SymbolicCompilerLayer[]>('/symbolic_compiler_layer.json'),
      ]);

      this.enhancements = {
        aurisCodex: auris || [],
        emotionalCodex: emotional || [],
        frequencyCodex: frequency || [],
        symbolicCompiler: symbolic || [],
        loaded: true,
        loadedAt: Date.now(),
      };

      console.log('✅ Ecosystem Enhancements loaded:', {
        aurisEntries: this.enhancements.aurisCodex.length,
        emotionalEntries: this.enhancements.emotionalCodex.length,
        frequencyEntries: this.enhancements.frequencyCodex.length,
        symbolicEntries: this.enhancements.symbolicCompiler.length,
      });

      this.notifyListeners();
    } catch (error) {
      console.error('❌ Failed to load ecosystem enhancements:', error);
    }

    this.isLoading = false;
    return this.enhancements;
  }

  /**
   * Load a single JSON file
   */
  private async loadJSON<T>(path: string): Promise<T | null> {
    try {
      const response = await fetch(path);
      if (!response.ok) {
        console.warn(`⚠️ Could not load ${path}: ${response.status}`);
        return null;
      }
      return await response.json();
    } catch (error) {
      console.warn(`⚠️ Error loading ${path}:`, error);
      return null;
    }
  }

  /**
   * Get current enhancements
   */
  getEnhancements(): EcosystemEnhancements {
    return { ...this.enhancements };
  }

  /**
   * Get Auris node enhancement by name
   */
  getAurisEnhancement(nodeName: string): AurisCodexEntry | undefined {
    return this.enhancements.aurisCodex.find(
      entry => entry.name.toLowerCase() === nodeName.toLowerCase()
    );
  }

  /**
   * Get emotional phase enhancement
   */
  getEmotionalEnhancement(phase: string): EmotionalCodexEntry | undefined {
    return this.enhancements.emotionalCodex.find(
      entry => entry.phase.toLowerCase() === phase.toLowerCase()
    );
  }

  /**
   * Get frequency enhancement for Prism
   */
  getFrequencyEnhancement(frequency: number): FrequencyCodexEntry | undefined {
    // Find closest frequency match
    return this.enhancements.frequencyCodex.reduce((closest, entry) => {
      if (!closest) return entry;
      const closestDiff = Math.abs(closest.frequency - frequency);
      const entryDiff = Math.abs(entry.frequency - frequency);
      return entryDiff < closestDiff ? entry : closest;
    }, undefined as FrequencyCodexEntry | undefined);
  }

  /**
   * Get symbolic compiler triggers for intent
   */
  getSymbolicTriggers(signal: 'BUY' | 'SELL' | 'HOLD'): SymbolicCompilerLayer | undefined {
    return this.enhancements.symbolicCompiler.find(
      entry => entry.intent.toLowerCase() === signal.toLowerCase()
    );
  }

  /**
   * Apply Auris enhancement to node weight
   */
  applyAurisBoost(nodeName: string, baseWeight: number): number {
    const enhancement = this.getAurisEnhancement(nodeName);
    if (!enhancement) return baseWeight;
    
    // Blend codex weight with base weight
    return baseWeight * 0.7 + enhancement.weight * 0.3;
  }

  /**
   * Apply emotional enhancement to Rainbow Bridge
   */
  applyEmotionalBoost(phase: string, baseIntensity: number): { intensity: number; color: string } {
    const enhancement = this.getEmotionalEnhancement(phase);
    if (!enhancement) return { intensity: baseIntensity, color: '#888888' };
    
    // Boost intensity based on arousal
    const boostedIntensity = baseIntensity * (1 + enhancement.arousal * 0.2);
    return {
      intensity: Math.min(1, boostedIntensity),
      color: enhancement.color,
    };
  }

  /**
   * Apply frequency enhancement to Prism output
   */
  applyFrequencyHarmonics(frequency: number): { harmonics: number[]; name: string } {
    const enhancement = this.getFrequencyEnhancement(frequency);
    if (!enhancement) return { harmonics: [], name: 'Unknown' };
    return { harmonics: enhancement.harmonics, name: enhancement.name };
  }

  /**
   * Subscribe to enhancement updates
   */
  subscribe(callback: (enhancements: EcosystemEnhancements) => void): () => void {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }

  private notifyListeners(): void {
    const enhancements = this.getEnhancements();
    this.listeners.forEach(cb => cb(enhancements));
  }

  /**
   * Check if enhancements are loaded
   */
  isLoaded(): boolean {
    return this.enhancements.loaded;
  }
}

// Singleton instance
export const ecosystemEnhancements = new EcosystemEnhancementsLoader();
