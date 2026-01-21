export interface IntentFrequency {
  frequency: number;
  decay: number;
  harmonics: number[];
  consciousness?: string;
}

export interface SchumannMode {
  frequency: number;
  decay: number;
  consciousness: string;
}

class AurisCodex {
  private intentFrequencies: Map<string, IntentFrequency> = new Map();
  private schumannModes: Map<string, SchumannMode> = new Map();

  constructor() {
    this.initializeCodex();
  }

  private initializeCodex(): void {
    // Intent frequencies based on Solfeggio and sacred geometry
    this.intentFrequencies.set('peace', { 
      frequency: 432.0, decay: 0.92, harmonics: [1, 3, 5] 
    });
    this.intentFrequencies.set('joy', { 
      frequency: 528.0, decay: 0.95, harmonics: [1, 2, 4] 
    });
    this.intentFrequencies.set('love', { 
      frequency: 639.0, decay: 0.88, harmonics: [1, 3, 5, 7] 
    });
    this.intentFrequencies.set('hope', { 
      frequency: 741.0, decay: 0.90, harmonics: [1, 2, 3] 
    });
    this.intentFrequencies.set('healing', { 
      frequency: 852.0, decay: 0.85, harmonics: [1, 5, 9] 
    });
    this.intentFrequencies.set('unity', { 
      frequency: 963.0, decay: 0.93, harmonics: [1, 3, 9] 
    });

    // Schumann resonance modes
    this.schumannModes.set('mode1', { 
      frequency: 7.83, decay: 0.96, consciousness: 'alpha_bridge' 
    });
    this.schumannModes.set('mode2', { 
      frequency: 14.3, decay: 0.94, consciousness: 'beta_activation' 
    });
    this.schumannModes.set('mode3', { 
      frequency: 20.8, decay: 0.92, consciousness: 'gamma_coherence' 
    });
    this.schumannModes.set('mode4', { 
      frequency: 27.3, decay: 0.90, consciousness: 'theta_deep' 
    });
    this.schumannModes.set('mode5', { 
      frequency: 33.8, decay: 0.88, consciousness: 'delta_unity' 
    });
  }

  getIntentFrequency(intent: string): IntentFrequency | undefined {
    return this.intentFrequencies.get(intent.toLowerCase());
  }

  getSchumannMode(mode: string): SchumannMode | undefined {
    return this.schumannModes.get(mode.toLowerCase());
  }

  getAllIntents(): string[] {
    return Array.from(this.intentFrequencies.keys());
  }

  getAllModes(): string[] {
    return Array.from(this.schumannModes.keys());
  }
}

export const aurisCodex = new AurisCodex();