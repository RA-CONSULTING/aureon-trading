
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

// ═══════════════════════════════════════════════════════════════════════════════
// UNIFIED DASHBOARD TYPES
// ═══════════════════════════════════════════════════════════════════════════════

export interface OrcaStatus {
  status: string; // "idle", "running", "stopped", "failed", etc.
  ready_for_execution: boolean;
  blockers: string[];
  last_heartbeat: number;
  error?: string;
  metadata?: Record<string, any>;
  timestamp: string;
}

export interface SystemState {
  name: string;
  category: string;
  state: string;
  last_heartbeat: number;
  error?: string;
  ready_for_orca: boolean;
  metadata?: Record<string, any>;
}

export interface CoordinationState {
  timestamp: string;
  uptime: number;
  total_systems: number;
  state_counts: Record<string, number>;
  systems_by_category: Record<string, SystemState[]>;
  orca_ready: boolean;
  orca_blockers: string[];
  orca_dependencies: {
    required: string[];
    all_ready: boolean;
  };
}

export interface FeedEvent {
  timestamp: string;
  source?: string;
  [key: string]: any;
}

export interface ConsolidatedFeedStream {
  stream_type: string; // "market_data", "intelligence", "risk_metrics", "execution_status", "system_health"
  is_healthy: boolean;
  event_count: number;
  last_update: number;
  latest_events: FeedEvent[];
}

export interface FeedsStatus {
  market_data: ConsolidatedFeedStream;
  intelligence: ConsolidatedFeedStream;
  risk_metrics: ConsolidatedFeedStream;
  execution_status: ConsolidatedFeedStream;
  system_health: ConsolidatedFeedStream;
}

export interface TradingDecision {
  id: string;
  type: "buy" | "sell" | "hold" | "close" | "wait";
  symbol: string;
  timestamp: string;
  confidence: number;
  reason: string;
  signals_used: string[];
  coordination_ok: boolean;
  risk_ok: boolean;
  cancel_reason?: string;
  metadata?: Record<string, any>;
}

export interface DecisionsResponse {
  total: number;
  decisions: Record<string, TradingDecision>;
  timestamp: string;
}

export interface UnifiedState {
  timestamp: string;
  coordination: CoordinationState;
  decisions: Record<string, TradingDecision>;
  feeds: FeedsStatus;
  uptime: number;
}

export interface SystemHealth {
  healthy: number;
  total: number;
  health_percentage: number;
  systems: Record<string, boolean>;
  timestamp: string;
}

export interface HealthCheckResponse {
  status: "healthy" | "degraded" | "error";
  timestamp: string;
  uptime: number;
  components: {
    coordinator: "ok" | "missing" | "error";
    decision_engine: "ok" | "missing" | "error";
    feed_hub: "ok" | "missing" | "error";
  };
}
