
export interface CoherenceDataPoint {
  time: number; // Represents day in simulation
  cognitiveCapacity: number; // 1 / kappa_t
  sporeConcentration: number; // C_t
  systemRigidity: number; // kappa_t
}

export interface OHLCV {
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
}

export interface AureonDataPoint {
  time: number;
  market: OHLCV;
  sentiment: number; // e.g., -1 (fear) to 1 (greed)
  policyRate: number; // e.g., simulated Fed Funds Rate

  // Aureon Process Tree Metrics
  dataIntegrity: number; // Dₜ
  crystalCoherence: number; // Cₜ
  celestialModulators: number;
  polarisBaseline: number; // ΔCₜ
  choeranceDrift: number; // Φₜ
  pingPong: number; // Pₜ
  gravReflection: number; // Gₜ
  unityIndex: number; // Uₜ
  inerchaVector: number; // 𝓘ₜ
  coherenceIndex: number;
  prismStatus: PrismStatus;
  
  // Animal node metrics
  tigerCut?: boolean;
  hummingbirdLocked?: boolean;
  falconSurge?: boolean;
  surgeMagnitude?: number;
  deerAlert?: boolean | 'SENSITIVE';
  dolphinSong?: boolean | 'SINGING';
  clownfishBond?: boolean | 'BONDED';
  pandaHeart?: number;
  memory?: any;
}

export type PrismStatus = 'Blue' | 'Gold' | 'Red' | 'Unknown';

export interface AureonReport {
    prismStatus: PrismStatus;
    unityIndex: number;
    inerchaVector: number;
}


export interface DejaVuEvent {
  time: number;
  intensity: number;
}

export interface NexusReport {
  currentCognitiveCapacity: number;
  currentSystemRigidity: number;
  currentSporeConcentration: number;
  daysSimulated: number;
  simulationYear: number;
  aureonReport: AureonReport;
}

export interface HistoricalDataPoint {
  year: number;
  cognitiveCapacity: number; // 1 / kappa_t
}

export interface NexusAnalysisResult {
  realtimeData: CoherenceDataPoint[];
  aureonData: AureonDataPoint[];
  historicalData: HistoricalDataPoint[];
  dejaVuEvents: DejaVuEvent[];
  report: NexusReport;
  monitoringEvents: MonitoringEvent[];
}

export interface MonitoringEvent {
  ts: number;
  stage: string;
  [key: string]: any;
}

export interface GroundingSource {
  uri: string;
  title: string;
}

export interface ChatMessage {
  role: 'user' | 'model';
  content: string;
  sources?: GroundingSource[];
}

export interface ChatStreamChunk {
  text: string;
  sources?: GroundingSource[];
}
