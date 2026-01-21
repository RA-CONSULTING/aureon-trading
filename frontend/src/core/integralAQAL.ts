/**
 * Integral AQAL Framework Integration
 * Maps AUREON field states to Ken Wilber's All Quadrants, All Levels model
 */

export interface AQALStage {
  level: string;
  label: string;
  description: string;
  minCoherence: number;
  frequency: number;
  chakra?: string;
}

export interface AQALQuadrant {
  name: string;
  abbreviation: string;
  description: string;
  stages: AQALStage[];
}

// Upper Left: Interior-Individual (Subjective)
const upperLeftStages: AQALStage[] = [
  { level: 'D', label: 'WITNESS', description: 'Pure awareness beyond ego', minCoherence: 0.95, frequency: 963, chakra: 'Crown' },
  { level: 'C-3', label: 'VISION-LOGIC', description: 'Integrated awareness', minCoherence: 0.90, frequency: 852, chakra: 'Third Eye' },
  { level: 'C-2', label: 'PLURALIST MIND', description: 'Multiple perspectives', minCoherence: 0.85, frequency: 741, chakra: 'Throat' },
  { level: 'C-1', label: 'MATURE EGO', description: 'Integrated ego functions', minCoherence: 0.80, frequency: 639, chakra: 'Heart' },
  { level: 'B-7', label: 'FORMAL OPERATIONAL MIND', description: 'Abstract thinking', minCoherence: 0.75, frequency: 528, chakra: 'Solar Plexus' },
  { level: 'B-6', label: 'CONCRETE OPERATIONAL MIND', description: 'Logical operations', minCoherence: 0.70, frequency: 417, chakra: 'Sacral' },
  { level: 'B-5', label: 'CONCEPTUAL-PREOP. MIND', description: 'Symbolic thinking', minCoherence: 0.65, frequency: 396, chakra: 'Root' },
  { level: 'B-4', label: 'SYMBOLIC-PREOP. MIND', description: 'Symbol use emerges', minCoherence: 0.60, frequency: 285 },
  { level: 'B-3', label: 'IMAGINAL BODY', description: 'Image-based cognition', minCoherence: 0.55, frequency: 174 },
  { level: 'B-2', label: 'PRANIC BODY', description: 'Vital energy awareness', minCoherence: 0.50, frequency: 110 },
  { level: 'B-1', label: 'AXIAL BODY', description: 'Basic body awareness', minCoherence: 0.45, frequency: 96 },
  { level: 'A-7', label: 'SELF-AWARENESS', description: 'Emerging self-recognition', minCoherence: 0.40, frequency: 85 },
  { level: 'A-6', label: 'INTELLIGENCE', description: 'Adaptive responses', minCoherence: 0.35, frequency: 75 },
  { level: 'A-5', label: 'EXPRESSIVITY', description: 'Expressive capability', minCoherence: 0.30, frequency: 65 },
  { level: 'A-4', label: 'EMOTIONALITY', description: 'Emotional responses', minCoherence: 0.25, frequency: 55 },
  { level: 'A-3', label: 'LIVELINESS', description: 'Living systems', minCoherence: 0.20, frequency: 45 },
  { level: 'A-2', label: 'SENSATION', description: 'Sensory awareness', minCoherence: 0.15, frequency: 35 },
  { level: 'A-1', label: 'IRRITABILITY', description: 'Basic responsiveness', minCoherence: 0.10, frequency: 25 },
];

// Upper Right: Exterior-Individual (Objective)
const upperRightStages: AQALStage[] = [
  { level: 'D', label: 'REALIZED MAN', description: 'Fully actualized being', minCoherence: 0.95, frequency: 963 },
  { level: 'C-3', label: 'INTEGRAL MAN - SF8', description: 'Integrated structures', minCoherence: 0.90, frequency: 852 },
  { level: 'C-2', label: 'POST-MODERN MAN - SF5', description: 'Pluralistic worldview', minCoherence: 0.85, frequency: 741 },
  { level: 'C-1', label: 'MODERN MAN - SF4', description: 'Rational-scientific', minCoherence: 0.80, frequency: 639 },
  { level: 'B-7', label: 'MEDIEVAL MAN - SF3', description: 'Traditional order', minCoherence: 0.75, frequency: 528 },
  { level: 'B-6', label: 'ANCIENT MAN - SF2', description: 'Mythic structures', minCoherence: 0.70, frequency: 417 },
  { level: 'B-5', label: 'NEOLITHIC MAN - STRUCTURES AND FUNCTIONS 1', description: 'Agricultural societies', minCoherence: 0.65, frequency: 396 },
  { level: 'B-4', label: 'SUPREME PSYCHE - COMPLEX NEO-CORTEX', description: 'Advanced neural complexity', minCoherence: 0.60, frequency: 285 },
  { level: 'B-3', label: 'ELEMENTS - C-C - 100 CM³', description: 'Cerebral cortex development', minCoherence: 0.55, frequency: 174 },
  { level: 'B-2', label: 'ARCHAIC H. SAPIENS - C-C - 1300 CM³', description: 'Early human brain', minCoherence: 0.50, frequency: 110 },
  { level: 'B-1', label: 'ERECT BIPEDS - C-C - 900 CM³', description: 'Upright posture', minCoherence: 0.45, frequency: 96 },
  { level: 'A-7', label: 'GENUS HOMO (HABILIS) - C-C - 500 CM³', description: 'Tool use emergence', minCoherence: 0.40, frequency: 85 },
  { level: 'A-6', label: 'HOMINID - CRANIAL CAPACITY ~350 CM³', description: 'Hominid brain', minCoherence: 0.35, frequency: 75 },
  { level: 'A-5', label: 'SUPERFAMILY HOMINOID - NEOCORTEX', description: 'Primate neocortex', minCoherence: 0.30, frequency: 65 },
  { level: 'A-4', label: 'ORDER PRIMATE - PLACENTA', description: 'Mammalian placenta', minCoherence: 0.25, frequency: 55 },
  { level: 'A-3', label: 'CLASS MAMMALIA - REPTILIAN BRAIN STEM', description: 'Mammalian nervous system', minCoherence: 0.20, frequency: 45 },
  { level: 'A-2', label: 'PHYLUM CHORDATE - NEURAL CHORD', description: 'Spinal cord emergence', minCoherence: 0.15, frequency: 35 },
  { level: 'A-1', label: 'COMPLEX ANIMAL - CELL', description: 'Multicellular life', minCoherence: 0.10, frequency: 25 },
];

// Lower Left: Interior-Collective (Inter-Subjective)
const lowerLeftStages: AQALStage[] = [
  { level: 'D', label: 'OPENING', description: 'Collective awakening', minCoherence: 0.95, frequency: 963 },
  { level: 'A', label: 'OPENING', description: 'Cultural emergence', minCoherence: 0.90, frequency: 852 },
  { level: 'MATTER', label: 'VOID - NON-DUALITY', description: 'Pre-manifest potential', minCoherence: 0.85, frequency: 741 },
  { level: 'A-1', label: 'VEGETATIVE', description: 'Plant consciousness', minCoherence: 0.20, frequency: 45 },
  { level: 'A-2', label: 'LOCOMOTIVE', description: 'Movement cultures', minCoherence: 0.25, frequency: 55 },
  { level: 'A-3', label: 'UROBORIC', description: 'Ouroboric fusion', minCoherence: 0.30, frequency: 65 },
  { level: 'A-4', label: 'TYPHONIC', description: 'Body-self cultures', minCoherence: 0.35, frequency: 75 },
  { level: 'A-5', label: 'ARCHAIC', description: 'Archaic societies', minCoherence: 0.40, frequency: 85 },
  { level: 'A-6', label: 'MAGIC', description: 'Magical worldview', minCoherence: 0.45, frequency: 96 },
  { level: 'A-7', label: 'MYTHIC', description: 'Mythic membership', minCoherence: 0.50, frequency: 110 },
  { level: 'B-1', label: 'ARCHAIC-IT', description: 'Archaic imperatives', minCoherence: 0.55, frequency: 174 },
  { level: 'B-2', label: 'ARCHAIC-MAGIC', description: 'Magic-animistic', minCoherence: 0.60, frequency: 285 },
  { level: 'B-3', label: 'MAGIC (ANIMISTIC)', description: 'Animistic cultures', minCoherence: 0.65, frequency: 396 },
  { level: 'B-4', label: 'MAGIC-MYTHIC', description: 'Power-god myths', minCoherence: 0.70, frequency: 417 },
  { level: 'B-5', label: 'MYTHIC (MYTHIC)', description: 'Conformist cultures', minCoherence: 0.75, frequency: 528 },
  { level: 'B-6', label: 'MYTHIC-RATIONAL', description: 'Achievement orientation', minCoherence: 0.80, frequency: 639 },
  { level: 'B-7', label: 'RATIONAL (EGOCENTRIC)', description: 'Individualistic', minCoherence: 0.85, frequency: 741 },
];

// Lower Right: Exterior-Collective (Inter-Objective)
const lowerRightStages: AQALStage[] = [
  { level: 'D', label: 'EVOLUTIONARY SUMMIT', description: 'Planetary awakening', minCoherence: 0.95, frequency: 963 },
  { level: 'C-3', label: 'POST-INDUSTRIAL (POST-MODERN AGE) - INFORMATIONAL', description: 'Information age', minCoherence: 0.90, frequency: 852 },
  { level: 'C-2', label: 'INDUSTRIAL (MODERNAGE) - NATION-STATE', description: 'Industrial societies', minCoherence: 0.85, frequency: 741 },
  { level: 'C-1', label: 'INDUSTRIAL (RENAISSANCE) - FEUDAL KINGDOMS', description: 'Early modern', minCoherence: 0.80, frequency: 639 },
  { level: 'B-7', label: 'PRE-INDUSTRIAL (MIDDLE AGES)', description: 'Medieval societies', minCoherence: 0.75, frequency: 528 },
  { level: 'B-6', label: 'NEOLITHIC (MONOLITHIC INDUSTRY) - AGROPASTORAL', description: 'Agricultural revolution', minCoherence: 0.70, frequency: 417 },
  { level: 'B-5', label: 'PALEOLITHIC (ARCHAIC AGE) - AGRARIAN', description: 'Early agriculture', minCoherence: 0.65, frequency: 396 },
  { level: 'B-4', label: 'LATE (ANCIENT AGE) - AGRARIAN', description: 'Ancient civilizations', minCoherence: 0.60, frequency: 285 },
  { level: 'B-3', label: 'MIDDLE PALEOLITHIC (MOUSETERIAN)', description: 'Hunter-gatherer societies', minCoherence: 0.55, frequency: 174 },
  { level: 'B-2', label: 'LOWER PALEOLITHIC (ACHEULEAN)', description: 'Tool-making cultures', minCoherence: 0.50, frequency: 110 },
  { level: 'B-1', label: 'LOWER PALEOLITHIC (OLDUVUN)', description: 'Early tool use', minCoherence: 0.45, frequency: 96 },
  { level: 'A-7', label: 'INITIAL ACHEULEAN (SCAVENGER)', description: 'Scavenging groups', minCoherence: 0.40, frequency: 85 },
  { level: 'A-6', label: 'MATURE ACHEULEAN (HUNTER)', description: 'Hunting societies', minCoherence: 0.35, frequency: 75 },
  { level: 'A-5', label: 'MIDDLE PALEOLITHIC (MOUSTERIAN)', description: 'Foraging groups', minCoherence: 0.30, frequency: 65 },
  { level: 'A-4', label: 'GATHERED BAND (PRIMATE)', description: 'Primate social groups', minCoherence: 0.25, frequency: 55 },
  { level: 'A-3', label: 'SEXUAL REPRODUCTION', description: 'Sexual species', minCoherence: 0.20, frequency: 45 },
  { level: 'A-2', label: 'PROKARYOTIC (FREE OXYGEN)', description: 'Oxygen-based life', minCoherence: 0.15, frequency: 35 },
  { level: 'A-1', label: 'GALAXIES', description: 'Cosmic structures', minCoherence: 0.10, frequency: 25 },
];

export const AQAL_QUADRANTS: AQALQuadrant[] = [
  {
    name: 'Upper Left',
    abbreviation: 'UL',
    description: 'Interior-Individual (Subjective)',
    stages: upperLeftStages
  },
  {
    name: 'Upper Right',
    abbreviation: 'UR',
    description: 'Exterior-Individual (Objective)',
    stages: upperRightStages
  },
  {
    name: 'Lower Left',
    abbreviation: 'LL',
    description: 'Interior-Collective (Inter-Subjective)',
    stages: lowerLeftStages
  },
  {
    name: 'Lower Right',
    abbreviation: 'LR',
    description: 'Exterior-Collective (Inter-Objective)',
    stages: lowerRightStages
  }
];

export interface AQALMapping {
  quadrant: string;
  stage: AQALStage;
  coherenceLevel: number;
  evolutionaryPosition: number; // 0-1 scale
}

export interface IntegralFieldState {
  upperLeft: AQALMapping;
  upperRight: AQALMapping;
  lowerLeft: AQALMapping;
  lowerRight: AQALMapping;
  overallEvolutionaryLevel: number;
  dominantQuadrant: string;
  integrationScore: number; // How balanced across quadrants
}

/**
 * Maps AUREON field metrics to AQAL developmental stages
 */
export function mapToAQAL(
  coherence: number,
  observerConsciousness: number,
  substrateCoherence: number,
  harmonicResonance: number,
  dimensionalAlignment: number
): IntegralFieldState {
  // Upper Left (Individual Interior) - maps to observer consciousness
  const ulStage = findStageByCoherence(AQAL_QUADRANTS[0].stages, observerConsciousness);
  const ulMapping: AQALMapping = {
    quadrant: 'UL',
    stage: ulStage,
    coherenceLevel: observerConsciousness,
    evolutionaryPosition: calculateEvolutionaryPosition(ulStage, AQAL_QUADRANTS[0].stages)
  };

  // Upper Right (Individual Exterior) - maps to coherence
  const urStage = findStageByCoherence(AQAL_QUADRANTS[1].stages, coherence);
  const urMapping: AQALMapping = {
    quadrant: 'UR',
    stage: urStage,
    coherenceLevel: coherence,
    evolutionaryPosition: calculateEvolutionaryPosition(urStage, AQAL_QUADRANTS[1].stages)
  };

  // Lower Left (Collective Interior) - maps to harmonic resonance
  const llStage = findStageByCoherence(AQAL_QUADRANTS[2].stages, harmonicResonance);
  const llMapping: AQALMapping = {
    quadrant: 'LL',
    stage: llStage,
    coherenceLevel: harmonicResonance,
    evolutionaryPosition: calculateEvolutionaryPosition(llStage, AQAL_QUADRANTS[2].stages)
  };

  // Lower Right (Collective Exterior) - maps to substrate coherence
  const lrStage = findStageByCoherence(AQAL_QUADRANTS[3].stages, substrateCoherence);
  const lrMapping: AQALMapping = {
    quadrant: 'LR',
    stage: lrStage,
    coherenceLevel: substrateCoherence,
    evolutionaryPosition: calculateEvolutionaryPosition(lrStage, AQAL_QUADRANTS[3].stages)
  };

  // Calculate overall evolutionary level (average across quadrants)
  const overallEvolutionaryLevel = (
    ulMapping.evolutionaryPosition +
    urMapping.evolutionaryPosition +
    llMapping.evolutionaryPosition +
    lrMapping.evolutionaryPosition
  ) / 4;

  // Find dominant quadrant
  const positions = [
    { quadrant: 'UL', position: ulMapping.evolutionaryPosition },
    { quadrant: 'UR', position: urMapping.evolutionaryPosition },
    { quadrant: 'LL', position: llMapping.evolutionaryPosition },
    { quadrant: 'LR', position: lrMapping.evolutionaryPosition }
  ];
  const dominant = positions.reduce((max, curr) => 
    curr.position > max.position ? curr : max
  );

  // Calculate integration score (how balanced across quadrants)
  const variance = positions.reduce((sum, p) => 
    sum + Math.pow(p.position - overallEvolutionaryLevel, 2), 0
  ) / 4;
  const integrationScore = Math.max(0, 1 - Math.sqrt(variance));

  return {
    upperLeft: ulMapping,
    upperRight: urMapping,
    lowerLeft: llMapping,
    lowerRight: lrMapping,
    overallEvolutionaryLevel,
    dominantQuadrant: dominant.quadrant,
    integrationScore
  };
}

function findStageByCoherence(stages: AQALStage[], coherence: number): AQALStage {
  // Find the highest stage that meets the coherence requirement
  for (let i = 0; i < stages.length; i++) {
    if (coherence >= stages[i].minCoherence) {
      return stages[i];
    }
  }
  // Return lowest stage if coherence is below all thresholds
  return stages[stages.length - 1];
}

function calculateEvolutionaryPosition(stage: AQALStage, allStages: AQALStage[]): number {
  const index = allStages.indexOf(stage);
  if (index === -1) return 0;
  return 1 - (index / (allStages.length - 1)); // Inverted: highest stage = 1.0
}
