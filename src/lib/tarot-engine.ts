// Simple hash function to replace SHA3 dependency
function simpleHash(input: string): string {
  let hash = 0;
  for (let i = 0; i < input.length; i++) {
    const char = input.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32bit integer
  }
  return Math.abs(hash).toString(16);
}

export interface TarotCard {
  id: string;
  name: string;
  number?: number;
  arcana: 'major' | 'minor';
  suit?: string;
  element: string;
  upright: string;
  reversed: string;
  lesson: string;
  warning: string;
  keywords: string[];
}

export interface TarotReading {
  qaid: string;
  positions: {
    origins: { card: TarotCard; orientation: 'upright' | 'reversed' };
    present: { card: TarotCard; orientation: 'upright' | 'reversed' };
    aligned: { card: TarotCard; orientation: 'upright' | 'reversed' };
    middle: { card: TarotCard; orientation: 'upright' | 'reversed' };
    resistant: { card: TarotCard; orientation: 'upright' | 'reversed' };
    unity: { card: TarotCard; orientation: 'upright' | 'reversed' };
  };
  narrative: {
    mythic: string;
    plain: string;
  };
  practices: Record<string, number>;
  claims: Array<{ text: string; supports: string[] }>;
}

export class TarotEngine {
  private deck: TarotCard[] = [];

  async loadDeck() {
    try {
      const response = await fetch('/tarot-major-arcana-complete.json');
      const data = await response.json();
      this.deck = data.major_arcana;
    } catch (error) {
      console.error('Failed to load tarot deck:', error);
      this.deck = this.getDefaultDeck();
    }
  }

  private getDefaultDeck(): TarotCard[] {
    return [
      {
        id: 'fool',
        name: 'The Fool',
        number: 0,
        arcana: 'major',
        element: 'Air',
        upright: 'New beginnings, innocence, spontaneity',
        reversed: 'Recklessness, poor judgment',
        lesson: 'Trust the journey with open heart',
        warning: 'Beware naivety and impulsiveness',
        keywords: ['beginnings', 'trust', 'adventure']
      }
    ];
  }

  generateQAID(name: string, dob: string, tob?: string, pob?: string): string {
    const input = `${name}|${dob}|${tob || ''}|${pob || ''}`;
    return simpleHash(input);
  }


  private getHourBucket(timestamp: Date): number {
    return Math.floor(timestamp.getTime() / (1000 * 60 * 60));
  }

  private deterministicCardDraw(qaid: string, position: string, hourBucket: number): {
    card: TarotCard;
    orientation: 'upright' | 'reversed';
  } {
    const seed = `${qaid}|${position}|${hourBucket}`;
    const hash = simpleHash(seed);
    
    const cardIndex = parseInt(hash.substring(0, 8), 16) % this.deck.length;
    const orientationBit = parseInt(hash.substring(8, 9), 16) % 2;
    
    return {
      card: this.deck[cardIndex],
      orientation: orientationBit === 0 ? 'upright' : 'reversed'
    };
  }

  async generateReading(
    name: string,
    dob: string,
    tob?: string,
    pob?: string,
    timestamp: Date = new Date()
  ): Promise<TarotReading> {
    if (this.deck.length === 0) {
      await this.loadDeck();
    }

    const qaid = this.generateQAID(name, dob, tob, pob);
    const hourBucket = this.getHourBucket(timestamp);

    const positions = {
      origins: this.deterministicCardDraw(qaid, 'origins', hourBucket),
      present: this.deterministicCardDraw(qaid, 'present', hourBucket),
      aligned: this.deterministicCardDraw(qaid, 'aligned', hourBucket),
      middle: this.deterministicCardDraw(qaid, 'middle', hourBucket),
      resistant: this.deterministicCardDraw(qaid, 'resistant', hourBucket),
      unity: this.deterministicCardDraw(qaid, 'unity', hourBucket)
    };

    return {
      qaid,
      positions,
      narrative: this.generateNarrative(positions),
      practices: this.calculatePractices(positions),
      claims: this.generateClaims(positions)
    };
  }

  private generateNarrative(positions: TarotReading['positions']) {
    const mythic = this.generateMythicNarrative(positions);
    const plain = this.generatePlainNarrative(positions);
    return { mythic, plain };
  }

  private generateMythicNarrative(positions: TarotReading['positions']): string {
    return `The cards speak of your journey through time and spirit. In the realm of origins, ${positions.origins.card.name} ${positions.origins.orientation} reveals the ancient patterns that shaped your soul. The present moment calls forth ${positions.present.card.name} ${positions.present.orientation}, speaking to your current crossroads. Three paths unfold before you: the aligned path shows ${positions.aligned.card.name}, the middle way reveals ${positions.middle.card.name}, and the resistant path warns through ${positions.resistant.card.name}. All threads weave together in ${positions.unity.card.name}, the card of integration and wholeness.`;
  }

  private generatePlainNarrative(positions: TarotReading['positions']): string {
    return `Your tarot reading reveals key insights across time. Your foundational pattern is represented by ${positions.origins.card.name} ${positions.origins.orientation}. Currently, you're experiencing the energy of ${positions.present.card.name} ${positions.present.orientation}. Looking ahead, your most aligned path shows ${positions.aligned.card.name}, while ${positions.unity.card.name} suggests how to integrate all these energies for growth and balance.`;
  }

  private calculatePractices(positions: TarotReading['positions']): Record<string, number> {
    // Calculate practice weights based on card keywords
    const practices = {
      grounding: 0.5,
      meditation: 0.5,
      service: 0.5,
      ritual: 0.5,
      timing: 0.5,
      movement: 0.5,
      devotion: 0.5,
      dreamwork: 0.5
    };

    Object.values(positions).forEach(({ card }) => {
      card.keywords.forEach(keyword => {
        switch (keyword) {
          case 'beginnings':
          case 'adventure':
            practices.movement += 0.1;
            break;
          case 'wisdom':
          case 'intuition':
            practices.meditation += 0.15;
            practices.dreamwork += 0.1;
            break;
          case 'nurturing':
          case 'abundance':
            practices.service += 0.1;
            practices.grounding += 0.1;
            break;
          case 'authority':
          case 'structure':
            practices.grounding += 0.15;
            practices.timing += 0.1;
            break;
        }
      });
    });

    // Normalize to 0-1 range
    Object.keys(practices).forEach(key => {
      practices[key] = Math.min(1, Math.max(0, practices[key]));
    });

    return practices;
  }

  private generateClaims(positions: TarotReading['positions']) {
    return [
      {
        text: `Your foundational energy is ${positions.origins.card.name}, suggesting ${positions.origins.card.lesson}`,
        supports: ['origins.card', 'origins.lesson']
      },
      {
        text: `The present moment calls for attention to ${positions.present.card.name} energy`,
        supports: ['present.card', 'present.meaning']
      },
      {
        text: `Your most aligned path forward is supported by ${positions.aligned.card.name}`,
        supports: ['aligned.card', 'aligned.upright_meaning']
      }
    ];
  }
}