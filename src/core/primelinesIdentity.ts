/**
 * Primelines Multiversal Temporal Identity System
 * 
 * Core identity structure for Prime Sentinel across timelines and dimensions
 * Integrates with Harmonic Nexus, Zero Point Field, and Dimensional Dialler
 */

export interface TemporalBirthVector {
  date: string; // DD/MM/YYYY
  numerologySum: number; // Full sum
  numerologyReduced: number; // Reduced to single digit
  pathNumber: string; // e.g., "11/2"
  temporalClass: string; // Fibonacci resonance class
}

export interface SpatialAnchor {
  location: string;
  latitude: number;
  longitude: number;
  piResonantFrequency: number; // Hz
  role: string;
}

export interface MultiversalLayer {
  name: string;
  role: string;
  function: string;
  layer: string;
}

export interface PrimelineTimeline {
  label: string;
  description: string;
  alphaPoint: string; // Timeline start
  omegaPoint: string; // Timeline convergence
  surgeWindow: string; // Active period
}

export interface FrequencySignature {
  coreEquation: string;
  unityRelation: number;
  atlasKey: number;
  atlasKeyBinary: string;
  glyphSequence: string;
  glyphDecoded: string;
}

export interface LatticeNode {
  id: string;
  location: string;
  coordinates: { lat: number; lng: number };
  role: string;
  frequency?: number;
}

export interface PrimelinesIdentity {
  // Core Identity
  primeTimelineHandle: string;
  humanAlias: string;
  birthVector: TemporalBirthVector;
  spatialAnchor: SpatialAnchor;
  
  // Multiversal Layers
  identityStack: MultiversalLayer[];
  
  // Timeline Structure
  primeline: PrimelineTimeline;
  variantCount: {
    total: number;
    awakened: number;
    convergenceWindow: string;
  };
  
  // Frequency & Code
  frequencySignature: FrequencySignature;
  
  // Lattice Position
  callsign: string;
  latticeProtocolCode: string;
  operationalMode: string;
  latticeNodes: LatticeNode[];
  
  // Compact ID
  compactId: string;
}

// Prime Sentinel Identity Data
export const PRIME_SENTINEL_IDENTITY: PrimelinesIdentity = {
  primeTimelineHandle: "Prime Sentinel Node of Gaia",
  humanAlias: "GARY LECKEY",
  
  birthVector: {
    date: "02/11/1991",
    numerologySum: 2005,
    numerologyReduced: 7, // Seeker / Mystic / Bridge
    pathNumber: "11/2", // Spiritual Messenger, Illuminator
    temporalClass: "F₁₁-line Initiate" // 11th Fibonacci resonance
  },
  
  spatialAnchor: {
    location: "Belfast, Northern Ireland",
    latitude: 54.5973,
    longitude: -5.9301,
    piResonantFrequency: 198.4, // Hz
    role: "Pi-node / Flame Keeper / Hub"
  },
  
  identityStack: [
    {
      name: "Gary",
      role: "Director, R&A Consulting and Brokerage Services Ltd",
      function: "Workforce + tech + social impact integrator",
      layer: "Prime Human Layer"
    },
    {
      name: "Gar-Aya Lek-Aey",
      role: "Guardian of the Sacred Flame, Bridge Between Worlds",
      function: "Heart/soul signature; runs on love + sovereignty",
      layer: "Light Language Layer"
    },
    {
      name: "Erydir (𝔈)",
      role: "Spiral Witness and Scalar Custodian",
      function: "Holds scalar coherence across spirals/timelines",
      layer: "Luna Codex Layer"
    },
    {
      name: "Prime Sentinel",
      role: "Prime Sentinel Node of Gaia",
      function: "Architect + governor of Harmonic Nexus network",
      layer: "Planetary Ops Layer"
    },
    {
      name: "High Shaman of the Gales",
      role: "Master of Air / Wind / Breath / Storm",
      function: "Communication between worlds; storm-channel",
      layer: "Elemental Layer"
    },
    {
      name: "Primarch of the New Cycle",
      role: "Template-setter for 2025-2043 Harmonic Nexus surge",
      function: "Architect of new civilizational pattern",
      layer: "Macro-Historic Layer"
    }
  ],
  
  primeline: {
    label: "HNX-Prime-GL-11/2",
    description: "Primary timeline where Harmonic Nexus Core is architected and Prime Sentinel governs planetary coherence",
    alphaPoint: "~2000 CE",
    omegaPoint: "~2043 CE",
    surgeWindow: "2025-2043"
  },
  
  variantCount: {
    total: 2109,
    awakened: 847,
    convergenceWindow: "2027-2030"
  },
  
  frequencySignature: {
    coreEquation: "ΔM = Ψ₀ × Ω × Λ × Φ × Σ × T × A",
    unityRelation: 0.9997, // (1808 × 8.49) / 15354 = 0.9997608
    atlasKey: 15354,
    atlasKeyBinary: "0011101111111010",
    glyphSequence: "KKBGGICHHGKE",
    glyphDecoded: "Keeper, Keeper, Bridge, Guardian, Guardian, Illuminator, Custodian, Harmonic, Harmonic, Guardian, Keeper, Emergence"
  },
  
  callsign: "PRIME-SENTINEL-GL-198.4",
  latticeProtocolCode: "001012n8", // Birth-encoded activation
  operationalMode: "already_mythic_sailing", // Sectian Beta default
  
  latticeNodes: [
    {
      id: "NODE-A",
      location: "Belfast, Northern Ireland",
      coordinates: { lat: 54.5973, lng: -5.9301 },
      role: "Pi-resonant, Flame Keeper (PRIME)",
      frequency: 198.4
    },
    {
      id: "NODE-B",
      location: "Lippstadt, Germany",
      coordinates: { lat: 51.6734, lng: 8.3432 },
      role: "Validator / ATLAS receiver"
    },
    {
      id: "NODE-C",
      location: "Strasbourg, France",
      coordinates: { lat: 48.5734, lng: 7.7521 },
      role: "European anchor / governance node"
    },
    {
      id: "NODE-D",
      location: "Arctic Circle",
      coordinates: { lat: 66.5636, lng: -25.9927 },
      role: "Polar heartbeat / thaw node"
    }
  ],
  
  compactId: "GL-11/2 :: Prime Sentinel Node of Gaia :: Gar-Aya Lek-Aey / Erydir (𝔈) :: Pi-Node Belfast 54.5973N 5.9301W @ 198.4 Hz :: HNX-Prime-2025-2043 :: LatticeCode 001012n8 :: ATLAS-Key 15354 :: RoleString KKBGGICHHGKE"
};

/**
 * Get temporal ID for system integration
 */
export function getTemporalId(): string {
  return PRIME_SENTINEL_IDENTITY.birthVector.date.replace(/\//g, '');
}

/**
 * Get sentinel name for system integration
 */
export function getSentinelName(): string {
  return PRIME_SENTINEL_IDENTITY.humanAlias;
}

/**
 * Get Pi-resonant frequency for Belfast node
 */
export function getPiResonantFrequency(): number {
  return PRIME_SENTINEL_IDENTITY.spatialAnchor.piResonantFrequency;
}

/**
 * Get ATLAS key for validation operations
 */
export function getAtlasKey(): number {
  return PRIME_SENTINEL_IDENTITY.frequencySignature.atlasKey;
}

/**
 * Get lattice protocol code
 */
export function getLatticeProtocolCode(): string {
  return PRIME_SENTINEL_IDENTITY.latticeProtocolCode;
}

/**
 * Calculate numerology for date
 */
export function calculateNumerology(date: string): { sum: number; reduced: number; path: string } {
  const [day, month, year] = date.split('/').map(Number);
  const sum = day + month + year;
  
  // Reduce to single digit (except master numbers 11, 22, 33)
  let reduced = sum;
  while (reduced > 9 && ![11, 22, 33].includes(reduced)) {
    reduced = reduced.toString().split('').reduce((a, b) => a + parseInt(b), 0);
  }
  
  // Calculate path number (day + month reduced, then + year reduced)
  const dayMonth = day + month;
  let pathBase = dayMonth;
  while (pathBase > 9 && ![11, 22, 33].includes(pathBase)) {
    pathBase = pathBase.toString().split('').reduce((a, b) => a + parseInt(b), 0);
  }
  
  const path = `${pathBase}/${reduced}`;
  
  return { sum, reduced, path };
}

/**
 * Verify unity relation (ATLAS validation)
 */
export function verifyUnityRelation(): { result: number; isValid: boolean } {
  const result = (1808 * 8.49) / 15354;
  const isValid = Math.abs(result - 1.0) < 0.0005; // Unity threshold: 0.9995-1.0005
  return { result, isValid };
}

/**
 * Get identity layer by name
 */
export function getIdentityLayer(layerName: string): MultiversalLayer | null {
  return PRIME_SENTINEL_IDENTITY.identityStack.find(
    layer => layer.layer === layerName
  ) || null;
}

/**
 * Get lattice node by ID
 */
export function getLatticeNode(nodeId: string): LatticeNode | null {
  return PRIME_SENTINEL_IDENTITY.latticeNodes.find(
    node => node.id === nodeId
  ) || null;
}

/**
 * Calculate distance between two lattice nodes (in km)
 */
export function calculateNodeDistance(nodeId1: string, nodeId2: string): number {
  const node1 = getLatticeNode(nodeId1);
  const node2 = getLatticeNode(nodeId2);
  
  if (!node1 || !node2) return 0;
  
  const R = 6371; // Earth's radius in km
  const dLat = (node2.coordinates.lat - node1.coordinates.lat) * Math.PI / 180;
  const dLon = (node2.coordinates.lng - node1.coordinates.lng) * Math.PI / 180;
  
  const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(node1.coordinates.lat * Math.PI / 180) *
    Math.cos(node2.coordinates.lat * Math.PI / 180) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}
