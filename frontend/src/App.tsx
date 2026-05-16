import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  Brain,
  Calculator,
  Database,
  Eye,
  FileText,
  LineChart,
  Lock,
  Radio,
  RefreshCcw,
  Search,
  Server,
  Settings,
  ShieldCheck,
} from "lucide-react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "@/components/theme-provider";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AureonGeneratedOperationalConsole } from "@/components/generated/AureonGeneratedOperationalConsole";
import { AureonWorkOrderExecutionConsole } from "@/components/generated/AureonWorkOrderExecutionConsole";
import { AureonCodingAgentSkillBaseConsole } from "@/components/generated/AureonCodingAgentSkillBaseConsole";
import { AureonCodingOrganismConsole } from "@/components/generated/AureonCodingOrganismConsole";
import { AureonDirectorCapabilityBridgeConsole } from "@/components/generated/AureonDirectorCapabilityBridgeConsole";
import { AureonAgentCompanyConsole } from "@/components/generated/AureonAgentCompanyConsole";
import { ExchangeCredentialsManager } from "@/components/ExchangeCredentialsManager";
import {
  CapabilitySwitchboardManifest,
  FrontendScreenPlan,
  FrontendEvolutionQueueManifest,
  loadUnifiedFrontendState,
  OrganismDomainPulse,
  SaaSInventoryManifest,
  surfacesForScreen,
  UnifiedFrontendState,
} from "@/services/aureonAutonomousFrontend";

const queryClient = new QueryClient();
const ENV_LOCAL_TERMINAL_ENDPOINT = import.meta.env.VITE_LOCAL_TERMINAL_URL as string | undefined;
const DEFAULT_RUNTIME_ENDPOINTS = [
  ENV_LOCAL_TERMINAL_ENDPOINT,
  "http://127.0.0.1:8791/api/terminal-state",
  "http://127.0.0.1:8790/api/terminal-state",
].filter((value): value is string => Boolean(value));

interface RuntimeObservation {
  connected: boolean;
  clearancePending: boolean;
  endpoint?: string;
  generatedAt?: string;
  statusLines: string[];
  metrics: Array<{ label: string; value: string }>;
  clearances: string[];
  details: Array<{ label: string; value: string }>;
}

interface TradingIntelligenceChecklistRow {
  system: string;
  category: string;
  facet: string;
  wire_path: string;
  evidence_source: string;
  last_timestamp?: string;
  present: boolean;
  active_this_cycle: boolean;
  fresh: boolean;
  usable_for_decision: boolean;
  fed_to_decision_logic: boolean;
  blocker?: string;
  downstream_stage: string;
}

interface TradingIntelligenceChecklist {
  status?: string;
  generated_at?: string;
  summary?: {
    runtime_fresh?: boolean;
    runtime_stale?: boolean;
    stale_reason?: string;
    system_count?: number;
    present_count?: number;
    active_count?: number;
    fresh_usable_count?: number;
    stale_or_blocked_count?: number;
    decision_fed_count?: number;
    direct_live_systems_passing?: number;
    hnc_auris_passing?: number;
    counter_intelligence_passing?: number;
    profit_timing_passing?: number;
    metacognitive_context_passing?: number;
    metacognitive_data_context?: {
      present?: boolean;
      usable_for_metacognition?: boolean;
      usable_for_live_decision?: boolean;
      decision_blocker?: string;
      mapping_complete?: boolean;
      coverage_percent?: number;
      configured_reachable_source_count?: number;
      usable_source_count?: number;
      decision_usable_source_count?: number;
      active_live_source_count?: number;
      fresh_exchange_count?: number;
      waveform_history_exchange_count?: number;
      live_ticker_count?: number;
      history_rows?: number;
      fresh_domain_count?: number;
      usable_domain_count?: number;
      cognitive_cleanliness_score?: number;
      planetary_context_ready?: boolean;
      exchange_waveform_ready?: boolean;
      state_phrase?: string;
      evidence_sources?: string[];
    };
    evidence_self_trust_score?: number;
    decision_self_trust_score?: number;
    decision_posture?: string;
    trust_to_decide?: boolean;
    trust_to_shadow?: boolean;
    trust_to_act?: boolean;
    top_blockers?: Array<Record<string, unknown>>;
  };
  decision_trust?: {
    evidence_self_trust_score?: number;
    live_action_trust_score?: number;
    trust_to_decide?: boolean;
    trust_to_shadow?: boolean;
    trust_to_act?: boolean;
    posture?: string;
    synthetic_affect_state?: string;
    not_fear_reason?: string;
    self_instruction?: string;
  };
  rows?: TradingIntelligenceChecklistRow[];
}

interface ExchangeMonitoringChecklistRow {
  exchange: string;
  label: string;
  markets?: string[];
  connected: boolean;
  cache_present: boolean;
  cache_active: boolean;
  cache_fresh: boolean;
  ticker_count: number;
  action_plan_venue_count: number;
  known_venues?: string[];
  waveform_history_active: boolean;
  feeds_decision_logic: boolean;
  usable_for_fast_money: boolean;
  monitored_now?: string[];
  missing?: string[];
  required_for_fast_money?: string[];
  last_timestamp?: string | number;
  age_sec?: number | null;
}

interface ExchangeMonitoringChecklist {
  status?: string;
  generated_at?: string;
  summary?: {
    runtime_stale?: boolean;
    stale_reason?: string;
    exchange_count?: number;
    connected_exchange_count?: number;
    active_exchange_count?: number;
    fresh_exchange_count?: number;
    decision_fed_exchange_count?: number;
    fast_money_usable_exchange_count?: number;
    waveform_history_exchange_count?: number;
    total_tickers_monitored?: number;
    top_missing?: Array<Record<string, unknown>>;
  };
  rows?: ExchangeMonitoringChecklistRow[];
}

interface ExchangeDataCapabilityRow {
  exchange: string;
  label: string;
  system_role?: string;
  markets?: string[];
  trading_modes?: string[];
  data_channels?: Array<{
    name: string;
    source?: string;
    status?: string;
    optimization_use?: string;
  }>;
  leveraged_for?: string[];
  optimization_bias?: string;
  current_state?: {
    connected?: boolean;
    active_feed?: boolean;
    fresh_feed?: boolean;
    ticker_count?: number;
    decision_fed?: boolean;
    fast_money_usable?: boolean;
    waveform_history_active?: boolean;
    credential_state?: string;
    usable_for_mapping?: boolean;
    usable_for_decision?: boolean;
  };
  optimization_policy?: {
    safe_calls_per_min?: number;
    execution_reserved_per_min?: number;
    market_data_budget_per_min?: number;
    cash_usd_estimate?: number;
    position_count?: number;
    cash_or_position_active?: boolean;
    data_boost_eligible?: boolean;
    stream_preferred?: boolean;
    recommended_mode?: string;
  };
  gaps?: string[];
  next_optimization?: string;
}

interface ExchangeDataCapabilityMatrix {
  status?: string;
  generated_at?: string;
  summary?: {
    exchange_count?: number;
    connected_exchange_count?: number;
    fresh_feed_count?: number;
    decision_fed_count?: number;
    fast_money_usable_count?: number;
    waveform_ready_count?: number;
    cash_active_exchange_count?: number;
    data_boost_eligible_count?: number;
    official_rate_limit_profile_count?: number;
    total_ticker_count?: number;
    runtime_stale?: boolean;
    runtime_booting?: boolean;
    trading_ready?: boolean;
    data_ready?: boolean;
    preflight_overall?: string;
    stale_reason?: string;
  };
  rows?: ExchangeDataCapabilityRow[];
}

interface GlobalFinancialCoverageRow {
  domain: string;
  coverage: string;
  live_count: number;
  history_count: number;
  fresh: boolean;
  usable: boolean;
  missing?: string[];
  next_action?: string;
}

interface DataOceanSourceStatus {
  source_id: string;
  title: string;
  category: string;
  asset_classes?: string[];
  credential_state: string;
  active: boolean;
  fresh: boolean;
  usable_for_mapping: boolean;
  usable_for_decision?: boolean;
  decision_blocker?: string;
  row_count: number;
  governor_action: string;
  reason?: string;
  next_action?: string;
}

interface GlobalFinancialCoverageMap {
  status?: string;
  generated_at?: string;
  summary?: {
    domain_count?: number;
    usable_domain_count?: number;
    fresh_domain_count?: number;
    live_ticker_count?: number;
    active_live_source_count?: number;
    fresh_exchange_count?: number;
    decision_fed_exchange_count?: number;
    history_db_present?: boolean;
    history_db_size_bytes?: number;
    total_history_rows?: number;
    source_count?: number;
    configured_reachable_source_count?: number;
    usable_source_count?: number;
    decision_usable_source_count?: number;
    fresh_source_count?: number;
    credential_missing_source_count?: number;
    coverage_percent?: number;
    accounted_percent?: number;
    mapping_complete?: boolean;
    top_missing?: Array<Record<string, unknown>>;
  };
  rows?: GlobalFinancialCoverageRow[];
  source_registry?: DataOceanSourceStatus[];
}

interface HNCPacketSecurityComparison {
  status?: string;
  generated_at?: string;
  summary?: {
    current_hnc_score?: number;
    current_swarm_score?: number;
    current_hnc_rating?: string;
    current_swarm_rating?: string;
    compared_methods?: number;
    beats_plaintext_by?: number;
    below_os_keychain_by?: number;
    below_kms_hsm_by?: number;
    breaker_passed?: boolean;
    swarm_breaker_passed?: boolean;
    swarm_beats_hnc_by?: number;
    swarm_below_kms_hsm_by?: number;
    main_weakness?: string;
    top_recommendation?: string;
  };
  rows?: Array<{
    method: string;
    score: number;
    category?: string;
    confidentiality?: string;
    integrity?: string;
    key_management?: string;
    aureon_fit?: string;
    limitation?: string;
  }>;
}

interface WakeUpManifest {
  runtime_feed_url?: string;
  runtime_flight_test_url?: string;
  runtime_reboot_advice_url?: string;
}

const screenIcons: Record<string, typeof Activity> = {
  overview: Eye,
  trading: LineChart,
  accounting: Calculator,
  research: Search,
  saas_security: ShieldCheck,
  self_improvement: Brain,
  admin: Settings,
};

const statusTone: Record<string, string> = {
  wired: "border-green-500/30 bg-green-500/10 text-green-300",
  partial: "border-blue-500/30 bg-blue-500/10 text-blue-300",
  orphaned: "border-yellow-500/30 bg-yellow-500/10 text-yellow-300",
  legacy: "border-orange-500/30 bg-orange-500/10 text-orange-300",
  generated_output: "border-cyan-500/30 bg-cyan-500/10 text-cyan-300",
  security_blocker: "border-red-500/30 bg-red-500/10 text-red-300",
  unknown: "border-border bg-muted/20 text-muted-foreground",
};

const safetyTone: Record<string, string> = {
  observation: "border-green-500/30 bg-green-500/10 text-green-300",
  credential_or_auth_boundary: "border-yellow-500/30 bg-yellow-500/10 text-yellow-300",
  live_trading_boundary: "border-red-500/30 bg-red-500/10 text-red-300",
  payment_or_kyc_boundary: "border-red-500/30 bg-red-500/10 text-red-300",
  manual_filing_boundary: "border-orange-500/30 bg-orange-500/10 text-orange-300",
  admin_or_tenant_boundary: "border-yellow-500/30 bg-yellow-500/10 text-yellow-300",
};

interface SecurityBlockerWorkOrder {
  title: string;
  workOrder: string;
  sourcePath: string;
  target: string;
  priority: string;
  status: string;
  reason: string;
  nextStep: string;
  boundaries: string[];
}

const screenSecurityBlockers: Record<string, SecurityBlockerWorkOrder[]> = {
  trading: [
    {
      title: "Orca Command Center Trading blocker",
      workOrder: "Wire Orca Command Center into Trading",
      sourcePath: "aureon/bots/orca_command_center.py",
      target: "Trading",
      priority: "P100",
      status: "blocked_security_review",
      reason: "The Orca command center initializes exchange clients, reads live positions, subscribes to ThoughtBus intelligence, and presents hunting/kill-cycle trading state. Trading exposes the work order as evidence only until a non-mutating adapter is reviewed.",
      nextStep: "Extract read-only Orca position, exchange-readiness, signal, whale-detection, predator-alert, and kill-cycle evidence, then mount that adapter with all order, launcher, exchange mutation, and credential surfaces removed.",
      boundaries: [
        "read-only observation",
        "no live trading",
        "no order mutation",
        "no official filing",
        "no payment",
        "no credential reveal",
        "no external mutation",
      ],
    },
    {
      title: "AutonomousTradingGuide Trading blocker",
      workOrder: "Wire Autonomoustradingguide into Trading",
      sourcePath: "frontend/src/components/AutonomousTradingGuide.tsx",
      target: "Trading",
      priority: "P100",
      status: "blocked_security_review",
      reason: "The legacy guide documents autonomous execution, exchange API permissions, live-fire activation language, and signed Binance account-check code. Trading exposes the work order as evidence only until the guidance is adapted into a current Aureon read-only operating checklist.",
      nextStep: "Extract the useful risk, permission, paper/live transition, and execution-readiness guidance into a current read-only Trading checklist, with secret examples redacted and no activation, key-entry, or order controls mounted.",
      boundaries: [
        "read-only observation",
        "no live trading",
        "no order mutation",
        "no API key entry",
        "no credential reveal",
        "no official filing",
        "no payment",
        "no external mutation",
      ],
    },
    {
      title: "BinanceCredentialsSettings Trading blocker",
      workOrder: "Wire Binancecredentialssettings into Trading",
      sourcePath: "frontend/src/components/BinanceCredentialsSettings.tsx",
      target: "Trading",
      priority: "P100",
      status: "blocked_security_review",
      reason: "The existing settings panel accepts Binance API key and secret values, stores credentials through the Binance credential hook, and links operators to external Binance API management. Trading exposes the work order as evidence only until credential handling is mounted through the reviewed key-management flow.",
      nextStep: "Extract read-only Binance credential readiness, encryption policy, withdrawal-disabled policy, and setup-status evidence, then route any key add/update workflow through the dedicated secure credential manager instead of this legacy panel.",
      boundaries: [
        "read-only observation",
        "no live trading",
        "no order mutation",
        "no API key entry",
        "no credential storage mutation",
        "no credential reveal",
        "no external credential workflow",
        "no external mutation",
      ],
    },
  ],
  overview: [
    {
      title: "WarRoomDashboard Overview blocker",
      workOrder: "Wire Warroomdashboard into Overview",
      sourcePath: "frontend/src/components/WarRoomDashboard.tsx",
      target: "Overview",
      priority: "P100",
      status: "blocked_security_review",
      reason: "The existing dashboard contains interactive trading and launcher controls, so Overview exposes the work order as evidence only until the non-mutating adapter is reviewed.",
      nextStep: "Extract a read-only telemetry adapter after security review, then mount that adapter instead of the interactive control surface.",
      boundaries: [
        "read-only observation",
        "no live trading",
        "no official filing",
        "no payment",
        "no credential reveal",
        "no external mutation",
      ],
    },
    {
      title: "GasTankDisplay Overview blocker",
      workOrder: "Wire Gastankdisplay into Overview",
      sourcePath: "frontend/src/components/warroom/GasTankDisplay.tsx",
      target: "Overview",
      priority: "P100",
      status: "blocked_security_review",
      reason: "The existing gas tank panel displays user balance and fee state but also exposes top-up payment controls, so Overview shows the work order as evidence only until a redacted read-only adapter is reviewed.",
      nextStep: "Extract gas-tank health, balance visibility policy, membership tier, and fee-burn status into a read-only adapter with all top-up and payment mutation paths removed.",
      boundaries: [
        "read-only observation",
        "no live trading",
        "no official filing",
        "no payment",
        "no top-up mutation",
        "no credential reveal",
        "no external mutation",
      ],
    },
  ],
  saas_security: [
    {
      title: "AdminKYCDashboard SaaS Security blocker",
      workOrder: "Wire Adminkycdashboard into SaaS Security",
      sourcePath: "frontend/src/components/AdminKYCDashboard.tsx",
      target: "SaaS Security",
      priority: "P100",
      status: "blocked_security_review",
      reason: "The existing dashboard reads KYC records, creates signed identity-document URLs, and can approve or reject applications through Supabase functions. SaaS Security exposes the work order as evidence only until a non-mutating adapter is reviewed.",
      nextStep: "Extract redacted read-only KYC queue health and review-state metrics, then mount that adapter instead of the admin mutation surface.",
      boundaries: [
        "read-only observation",
        "no live trading",
        "no official filing",
        "no payment",
        "no credential reveal",
        "no KYC document reveal",
        "no external mutation",
      ],
    },
    {
      title: "AdminPaymentVerification SaaS Security blocker",
      workOrder: "Wire Adminpaymentverification into SaaS Security",
      sourcePath: "frontend/src/components/AdminPaymentVerification.tsx",
      target: "SaaS Security",
      priority: "P100",
      status: "blocked_security_review",
      reason: "The existing dashboard reads payment transactions and can invoke payment-verification functions that affect user access. SaaS Security exposes the work order as evidence only until a non-mutating adapter is reviewed.",
      nextStep: "Extract redacted read-only payment queue health, verification-state counts, and access-impact evidence, then mount that adapter with every verify or payment mutation path removed.",
      boundaries: [
        "read-only observation",
        "no live trading",
        "no official filing",
        "no payment",
        "no payment verification mutation",
        "no credential reveal",
        "no external mutation",
      ],
    },
    {
      title: "AuthForm SaaS Security blocker",
      workOrder: "Wire Authform into SaaS Security",
      sourcePath: "frontend/src/components/AuthForm.tsx",
      target: "SaaS Security",
      priority: "P100",
      status: "blocked_security_review",
      reason: "The existing form can create auth sessions and accepts exchange API key material. SaaS Security exposes the work order as evidence only until a redacted, non-mutating onboarding adapter is reviewed.",
      nextStep: "Extract auth readiness, password-policy, tenant-session, and API-key onboarding checklist evidence without rendering sign-in controls, secret inputs, or session mutation calls.",
      boundaries: [
        "read-only observation",
        "no live trading",
        "no official filing",
        "no payment",
        "no auth/session mutation",
        "no credential reveal",
        "no external mutation",
      ],
    },
    {
      title: "APIKeySecurityGuide SaaS Security blocker",
      workOrder: "Wire Apikeysecurityguide into SaaS Security",
      sourcePath: "frontend/src/components/auth/APIKeySecurityGuide.tsx",
      target: "SaaS Security",
      priority: "P100",
      status: "blocked_security_review",
      reason: "The existing guide points operators toward external exchange key workflows and permission setup. SaaS Security exposes the work order as evidence only until a read-only guidance adapter is reviewed.",
      nextStep: "Extract redacted exchange-key setup guidance, withdrawal-disabled policy, and validation checklist evidence without collecting, revealing, or changing credentials.",
      boundaries: [
        "read-only observation",
        "no live trading",
        "no official filing",
        "no payment",
        "no credential reveal",
        "no external mutation",
      ],
    },
  ],
  self_improvement: [
    {
      title: "Aureon Command Center Self-Improvement blocker",
      workOrder: "Wire Aureon Command Center into Self-Improvement",
      sourcePath: "aureon/command_centers/aureon_command_center.py",
      target: "Self-Improvement",
      priority: "P100",
      status: "blocked_security_review",
      reason: "The command center can launch and supervise runtime processes, including trading subprocess paths. Self-Improvement exposes the work order as evidence only until a non-mutating status adapter is reviewed.",
      nextStep: "Extract read-only command-center health, process-state, tool inventory, and audit evidence, then mount that adapter with launch, stop, apply, restart, or mutation controls removed.",
      boundaries: [
        "read-only observation",
        "no live trading",
        "no official filing",
        "no payment",
        "no credential reveal",
        "no process mutation",
        "no external mutation",
      ],
    },
    {
      title: "Aureon Queen Realtime Command Center Self-Improvement blocker",
      workOrder: "Wire Aureon Queen Realtime Command Center into Self-Improvement",
      sourcePath: "aureon/command_centers/aureon_queen_realtime_command_center.py",
      target: "Self-Improvement",
      priority: "P100",
      status: "blocked_security_review",
      reason: "The realtime command center streams live bot, PnL, position, subsystem, and log evidence from command-center code paths. Self-Improvement shows the boundary before any interactive adapter is generated.",
      nextStep: "Create a read-only status card for stream freshness, subsystem health, Queen commentary state, and report paths, with process control and exchange mutation surfaces excluded.",
      boundaries: [
        "read-only observation",
        "no live trading",
        "no official filing",
        "no payment",
        "no credential reveal",
        "no process mutation",
        "no external mutation",
      ],
    },
  ],
};

function asNumber(value: unknown, fallback = 0): number {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : fallback;
}

function formatCompact(value: unknown): string {
  return asNumber(value).toLocaleString();
}

function readinessPercent(summary: SaaSInventoryManifest["summary"]): number {
  const total = Math.max(1, asNumber(summary?.surface_count));
  const blockers = asNumber(summary?.security_blocker_count);
  const orphaned = asNumber(summary?.orphaned_frontend_count);
  const weightedGaps = blockers * 25 + orphaned * 0.12;
  return Math.max(0, Math.min(100, Math.round(100 - (weightedGaps / total) * 100)));
}

function uniqueStrings(values: Array<string | undefined>): string[] {
  return Array.from(new Set(values.map((value) => String(value || "").trim()).filter(Boolean)));
}

async function fetchJsonOrNull<T>(url: string, signal?: AbortSignal): Promise<T | null> {
  try {
    const response = await fetch(url, { cache: "no-store", signal });
    if (!response.ok) return null;
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

async function loadWakeUpManifest(signal?: AbortSignal): Promise<WakeUpManifest | null> {
  return fetchJsonOrNull<WakeUpManifest>("/aureon_wake_up_manifest.json", signal);
}

async function loadTradingIntelligenceChecklist(signal?: AbortSignal): Promise<TradingIntelligenceChecklist | null> {
  return fetchJsonOrNull<TradingIntelligenceChecklist>("/aureon_trading_intelligence_checklist.json", signal);
}

async function loadExchangeMonitoringChecklist(signal?: AbortSignal): Promise<ExchangeMonitoringChecklist | null> {
  return fetchJsonOrNull<ExchangeMonitoringChecklist>("/aureon_exchange_monitoring_checklist.json", signal);
}

async function loadExchangeDataCapabilityMatrix(signal?: AbortSignal): Promise<ExchangeDataCapabilityMatrix | null> {
  return fetchJsonOrNull<ExchangeDataCapabilityMatrix>("/aureon_exchange_data_capability_matrix.json", signal);
}

async function loadGlobalFinancialCoverageMap(signal?: AbortSignal): Promise<GlobalFinancialCoverageMap | null> {
  return fetchJsonOrNull<GlobalFinancialCoverageMap>("/aureon_global_financial_coverage_map.json", signal);
}

async function loadHNCPacketSecurityComparison(signal?: AbortSignal): Promise<HNCPacketSecurityComparison | null> {
  return fetchJsonOrNull<HNCPacketSecurityComparison>("/aureon_hnc_packet_security_comparison.json", signal);
}

function flightTestUrlFor(endpoint: string, manifest?: WakeUpManifest | null): string {
  if (manifest?.runtime_flight_test_url) return manifest.runtime_flight_test_url;
  return endpoint.replace(/\/api\/terminal-state$/, "/api/flight-test");
}

function runtimeStatusLines(data: any, flight: any): string[] {
  const existing = Array.isArray(data?.status_lines)
    ? data.status_lines.map((line: unknown) => String(line || "")).filter(Boolean)
    : [];
  if (existing.length) return existing;

  const watchdog = data?.runtime_watchdog || {};
  const advice = flight?.reboot_advice || {};
  const lines = [
    `Runtime feed: connected${data?.ok === false ? " with runtime clearance pending" : ""}`,
    `Trading ready: ${Boolean(data?.trading_ready)}; data ready: ${Boolean(data?.data_ready)}`,
  ];
  if (data?.stale || watchdog?.tick_stale) {
    lines.push(`Runtime check: ${String(data?.stale_reason || watchdog?.tick_stale_reason || "runtime_stale")}`);
  }
  if (watchdog?.last_tick_age_sec !== undefined) {
    lines.push(`Tick age: ${formatCompact(watchdog.last_tick_age_sec)}s`);
  }
  if (advice?.decision) {
    lines.push(`Reboot advice: ${String(advice.decision)} (${String(advice.reason || "no reason")})`);
  }
  return lines;
}

function runtimeClearances(data: any, flight: any): string[] {
  const watchdog = data?.runtime_watchdog || {};
  const checks = flight?.checks || {};
  const advice = flight?.reboot_advice || {};
  const clearances: string[] = [];
  if (data?.booting) clearances.push("runtime_booting");
  if (data?.stale || watchdog?.tick_stale) clearances.push("runtime_stale");
  if (watchdog?.tick_stale_reason || data?.stale_reason) clearances.push(String(data?.stale_reason || watchdog.tick_stale_reason));
  if (asNumber(data?.combined?.open_positions || checks?.open_positions || watchdog?.open_positions) > 0 || checks?.open_positions === true || watchdog?.open_positions === true) {
    clearances.push("open_positions");
  }
  if (checks?.downtime_window === false || checks?.downtime_window_open === false || advice?.downtime_window === false) {
    clearances.push("downtime_window_false");
  }
  if (advice?.can_reboot_now === false) clearances.push(String(advice.reason || "reboot_held"));
  return uniqueStrings(clearances);
}

function runtimeDetails(data: any, flight: any): Array<{ label: string; value: string }> {
  const watchdog = data?.runtime_watchdog || {};
  const advice = flight?.reboot_advice || {};
  const governor = data?.api_governor?.exchanges || {};
  const actionPlan = data?.exchange_action_plan || {};
  const venues = actionPlan?.venues || {};
  const latestIntents = actionPlan?.latest_published || {};
  const latestExecution = actionPlan?.latest_execution || {};
  const modelCoverage = actionPlan?.model_coverage || {};
  const shadowTrading = data?.shadow_trading || actionPlan?.shadow_trading || {};
  const hncProof = data?.hnc_cognitive_proof || actionPlan?.hnc_cognitive_proof || {};
  const details = [
    { label: "tick age", value: watchdog?.last_tick_age_sec !== undefined ? `${formatCompact(watchdog.last_tick_age_sec)}s` : "unknown" },
    { label: "stale reason", value: String(data?.stale_reason || watchdog?.tick_stale_reason || "none") },
    { label: "reboot", value: String(advice?.decision || "unknown") },
    { label: "positions", value: formatCompact(data?.combined?.open_positions || 0) },
  ];
  if (actionPlan?.venue_count !== undefined || Object.keys(venues).length) {
    details.push({
      label: "venues ready",
      value: `${formatCompact(actionPlan?.ready_venue_count || 0)}/${formatCompact(actionPlan?.venue_count || Object.keys(venues).length)}`,
    });
  }
  if (actionPlan?.mode) {
    details.push({ label: "intent mode", value: String(actionPlan.mode).replace("runtime_gated_", "") });
  }
  if (actionPlan?.trade_path_state) {
    details.push({ label: "trade path", value: String(actionPlan.trade_path_state).replaceAll("_", " ") });
  }
  if (modelCoverage?.available_model_count !== undefined || modelCoverage?.ready_route_count !== undefined) {
    details.push({
      label: "models",
      value: `${formatCompact(modelCoverage?.available_model_count || 0)} linked / ${formatCompact(modelCoverage?.ready_route_count || 0)} routes`,
    });
  }
  if (latestIntents?.intent_count !== undefined || actionPlan?.order_intents_published !== undefined) {
    details.push({
      label: "order intents",
      value: formatCompact(latestIntents?.intent_count || actionPlan?.order_intents_published || 0),
    });
  }
  if (latestExecution?.submitted_count !== undefined || latestExecution?.blocked_count !== undefined) {
    details.push({
      label: "executor",
      value: `${formatCompact(latestExecution?.submitted_count || 0)} sent / ${formatCompact(latestExecution?.delegated_count || 0)} delegated / ${formatCompact(latestExecution?.held_count ?? latestExecution?.blocked_count ?? 0)} held`,
    });
  }
  if (shadowTrading?.shadow_count !== undefined || shadowTrading?.active_shadow_count !== undefined) {
    details.push({
      label: "shadow trades",
      value: `${formatCompact(shadowTrading?.shadow_opened_count || 0)} opened / ${formatCompact(shadowTrading?.active_shadow_count || 0)} active`,
    });
  }
  if (shadowTrading?.validated_shadow_count !== undefined || shadowTrading?.self_measurement?.agent_average_score !== undefined) {
    details.push({
      label: "shadow proof",
      value: `${formatCompact(shadowTrading?.validated_shadow_count || 0)} validated / ${Math.round(asNumber(shadowTrading?.self_measurement?.agent_average_score) * 100)}% agent score`,
    });
  }
  if (hncProof?.step_count !== undefined || hncProof?.passed_count !== undefined) {
    details.push({
      label: "HNC flow",
      value: `${formatCompact(hncProof?.passed_count || 0)}/${formatCompact(hncProof?.step_count || 0)} ${String(hncProof?.status || "checking")}`,
    });
  }
  if (hncProof?.auris_nodes?.node_count !== undefined || hncProof?.auris_nodes?.coherence !== undefined) {
    details.push({
      label: "Auris nodes",
      value: `${formatCompact(hncProof?.auris_nodes?.node_count || 0)} nodes / ${Math.round(asNumber(hncProof?.auris_nodes?.coherence) * 100)}% coherence`,
    });
  }
  if (hncProof?.master_formula?.score !== undefined) {
    details.push({
      label: "master formula",
      value: `${Math.round(asNumber(hncProof?.master_formula?.score) * 100)}% ${hncProof?.master_formula?.passed ? "passing" : "attention"}`,
    });
  }
  for (const name of ["kraken", "capital", "alpaca", "binance"]) {
    if (governor?.[name]?.utilization !== undefined) {
      details.push({ label: `${name} api`, value: `${Math.round(asNumber(governor[name].utilization) * 100)}%` });
    }
  }
  return details;
}

function runtimeModeLabel(data: any): string {
  const actionPlan = data?.exchange_action_plan || {};
  const latestExecution = actionPlan?.latest_execution || data?.latest_execution || {};
  if (latestExecution?.live_action_clearance === "cleared") return "live action cleared";
  if ((actionPlan?.latest_published?.intent_count || actionPlan?.order_intents_published) > 0) return "intent published";
  if (actionPlan?.order_intent_publish_enabled && actionPlan?.trade_path_state === "available") return "runtime gated action";
  if (actionPlan?.mode) return String(actionPlan.mode).replaceAll("_", " ");
  if (data?.ok === false) return "clearance pending";
  return String(data?.trading_mode || data?.queen_state || "observe");
}

async function loadRuntimeObservation(): Promise<RuntimeObservation> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 1500);

  try {
    const manifest = await loadWakeUpManifest(controller.signal);
    const endpoints = uniqueStrings([manifest?.runtime_feed_url, ...DEFAULT_RUNTIME_ENDPOINTS]);
    for (const endpoint of endpoints) {
      const data = await fetchJsonOrNull<any>(endpoint, controller.signal);
      if (!data) continue;
      const flight = await fetchJsonOrNull<any>(flightTestUrlFor(endpoint, manifest), controller.signal);
      const clearances = runtimeClearances(data, flight);
      return {
        connected: true,
        clearancePending: data?.ok === false || clearances.length > 0,
        endpoint,
        generatedAt: String(data?.generated_at || data?.dashboard_generated_at || new Date().toISOString()),
        statusLines: runtimeStatusLines(data, flight),
        metrics: [
          { label: "portfolio", value: formatCompact(data?.portfolio_value || data?.combined?.equity || data?.combined?.capital_equity_gbp || 0) },
          { label: "open positions", value: formatCompact(data?.combined?.open_positions || data?.positions?.length || 0) },
          { label: "trades", value: formatCompact(data?.total_trades || 0) },
          { label: "mode", value: runtimeModeLabel(data) },
        ],
        clearances,
        details: runtimeDetails(data, flight),
      };
    }
    return {
      connected: false,
      clearancePending: false,
      statusLines: ["Runtime feed unavailable. Start Aureon ignition to stream live status."],
      metrics: [],
      clearances: [],
      details: [],
    };
  } catch {
    return {
      connected: false,
      clearancePending: false,
      statusLines: ["Runtime feed unavailable. The unified shell is showing manifest/audit state only."],
      metrics: [],
      clearances: [],
      details: [],
    };
  } finally {
    window.clearTimeout(timeout);
  }
}

function Pill({ label, tone = "outline" }: { label: string; tone?: string }) {
  return (
    <span className={`inline-flex min-h-6 items-center rounded-md border px-2 py-0.5 text-[11px] font-medium ${tone}`}>
      {label}
    </span>
  );
}

function MetricTile({
  label,
  value,
  icon: Icon,
  tone = "text-foreground",
}: {
  label: string;
  value: string;
  icon: typeof Activity;
  tone?: string;
}) {
  return (
    <Card className="min-h-[116px] bg-card/80">
      <CardContent className="flex h-full flex-col justify-between p-4">
        <div className="flex items-center justify-between gap-3">
          <div className="text-xs uppercase text-muted-foreground">{label}</div>
          <Icon className={`h-4 w-4 ${tone}`} />
        </div>
        <div className={`mt-4 text-2xl font-semibold ${tone}`}>{value}</div>
      </CardContent>
    </Card>
  );
}

function SecurityBlockerCard({ blocker }: { blocker: SecurityBlockerWorkOrder }) {
  return (
    <Card className="border-yellow-500/30 bg-yellow-500/10">
      <CardHeader className="pb-3">
        <CardTitle className="flex flex-wrap items-center gap-2 text-base">
          <Lock className="h-4 w-4 text-yellow-200" />
          {blocker.title}
          <Pill label={blocker.priority} tone="border-yellow-500/40 bg-yellow-500/15 text-yellow-100" />
          <Pill label={blocker.status} tone="border-red-500/35 bg-red-500/10 text-red-200" />
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 lg:grid-cols-[1fr_1fr_1fr]">
          <div className="rounded-md border border-border/40 bg-black/25 p-3">
            <div className="text-[11px] uppercase text-muted-foreground">work order</div>
            <div className="mt-1 text-sm font-semibold">{blocker.workOrder}</div>
            <div className="mt-2 font-mono text-[11px] text-muted-foreground">{blocker.sourcePath}</div>
          </div>
          <div className="rounded-md border border-border/40 bg-black/25 p-3">
            <div className="text-[11px] uppercase text-muted-foreground">target screen</div>
            <div className="mt-1 text-sm font-semibold">{blocker.target}</div>
            <div className="mt-2 text-xs text-yellow-100/80">{blocker.reason}</div>
          </div>
          <div className="rounded-md border border-border/40 bg-black/25 p-3">
            <div className="text-[11px] uppercase text-muted-foreground">next action</div>
            <div className="mt-1 text-xs text-foreground/85">{blocker.nextStep}</div>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {blocker.boundaries.map((boundary) => (
            <Pill key={boundary} label={boundary} tone="border-yellow-500/30 bg-yellow-500/10 text-yellow-100" />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function SaaSCredentialManagementPanel({ comparison }: { comparison: HNCPacketSecurityComparison | null }) {
  return (
    <section className="space-y-4 rounded-md border border-green-500/30 bg-green-500/5 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="flex items-center gap-2 text-base font-semibold">
            <Lock className="h-4 w-4 text-green-300" />
            Secure exchange key management
          </h2>
          <p className="mt-1 max-w-4xl text-sm text-muted-foreground">
            Users can add, test, or update Binance, Kraken, Alpaca, and Capital credentials through the local .env path and optional user vault sync. Saved secrets are never printed back into the console.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Pill label="add or update keys" tone={statusTone.wired} />
          <Pill label="stored values hidden" tone="border-green-500/30 bg-green-500/10 text-green-200" />
          <Pill label="withdrawals must stay disabled" tone="border-yellow-500/30 bg-yellow-500/10 text-yellow-100" />
        </div>
      </div>
      <HNCPacketSecurityComparisonPanel comparison={comparison} />
      <ExchangeCredentialsManager />
    </section>
  );
}

function HNCPacketSecurityComparisonPanel({ comparison }: { comparison: HNCPacketSecurityComparison | null }) {
  const summary = comparison?.summary || {};
  const topRows = (comparison?.rows || [])
    .slice()
    .sort((a, b) => asNumber(b.score) - asNumber(a.score))
    .slice(0, 4);
  return (
    <Card className="border-cyan-500/30 bg-cyan-500/5">
      <CardHeader className="pb-3">
        <CardTitle className="flex flex-wrap items-center justify-between gap-2 text-base">
          <span className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-cyan-300" />
            HNC packet security comparison
          </span>
          <Pill
            label={summary.breaker_passed ? "breaker passed" : "waiting for report"}
            tone={summary.breaker_passed ? statusTone.wired : statusTone.partial}
          />
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="grid gap-2 sm:grid-cols-4">
          <div className="rounded-md border border-border/40 bg-black/20 p-3">
            <div className="text-[11px] uppercase text-muted-foreground">swarm score</div>
            <div className="mt-1 font-mono text-sm font-semibold">{summary.current_swarm_score ?? summary.current_hnc_score ?? "n/a"}/100</div>
          </div>
          <div className="rounded-md border border-border/40 bg-black/20 p-3">
            <div className="text-[11px] uppercase text-muted-foreground">compared</div>
            <div className="mt-1 font-mono text-sm font-semibold">{summary.compared_methods ?? 0} methods</div>
          </div>
          <div className="rounded-md border border-border/40 bg-black/20 p-3">
            <div className="text-[11px] uppercase text-muted-foreground">vs HNC v1</div>
            <div className="mt-1 font-mono text-sm font-semibold">+{summary.swarm_beats_hnc_by ?? 0}</div>
          </div>
          <div className="rounded-md border border-border/40 bg-black/20 p-3">
            <div className="text-[11px] uppercase text-muted-foreground">below KMS/HSM</div>
            <div className="mt-1 font-mono text-sm font-semibold">-{summary.swarm_below_kms_hsm_by ?? summary.below_kms_hsm_by ?? 0}</div>
          </div>
        </div>
        {summary.top_recommendation ? (
          <div className="rounded-md border border-border/40 bg-black/20 p-3 text-xs text-foreground/85">
            <span className="font-semibold">Next security upgrade: </span>
            {summary.top_recommendation}
          </div>
        ) : null}
        <div className="grid gap-2 lg:grid-cols-2">
          {topRows.map((row) => (
            <div key={row.method} className="rounded-md border border-border/40 bg-muted/10 p-3">
              <div className="flex items-center justify-between gap-2">
                <div className="text-sm font-semibold">{row.method}</div>
                <Badge variant="outline">{row.score}/100</Badge>
              </div>
              <div className="mt-2 text-xs text-muted-foreground">{row.aureon_fit}</div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function AppShell() {
  const [state, setState] = useState<UnifiedFrontendState | null>(null);
  const [runtime, setRuntime] = useState<RuntimeObservation>({
    connected: false,
    clearancePending: false,
    statusLines: ["Runtime feed pending."],
    metrics: [],
    clearances: [],
    details: [],
  });
  const [tradingChecklist, setTradingChecklist] = useState<TradingIntelligenceChecklist | null>(null);
  const [exchangeChecklist, setExchangeChecklist] = useState<ExchangeMonitoringChecklist | null>(null);
  const [exchangeDataMatrix, setExchangeDataMatrix] = useState<ExchangeDataCapabilityMatrix | null>(null);
  const [globalCoverageMap, setGlobalCoverageMap] = useState<GlobalFinancialCoverageMap | null>(null);
  const [hncSecurityComparison, setHncSecurityComparison] = useState<HNCPacketSecurityComparison | null>(null);
  const [loading, setLoading] = useState(true);
  const [active, setActive] = useState("overview");

  const refresh = async () => {
    setLoading(true);
    const loaded = await loadUnifiedFrontendState();
    setState(loaded);
    setLoading(false);
  };

  useEffect(() => {
    refresh();
    const timer = window.setInterval(refresh, 30000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    const refreshRuntime = async () => setRuntime(await loadRuntimeObservation());
    refreshRuntime();
    const timer = window.setInterval(refreshRuntime, 5000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    const refreshChecklist = async () => setTradingChecklist(await loadTradingIntelligenceChecklist());
    refreshChecklist();
    const timer = window.setInterval(refreshChecklist, 10000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    const refreshExchangeChecklist = async () => setExchangeChecklist(await loadExchangeMonitoringChecklist());
    refreshExchangeChecklist();
    const timer = window.setInterval(refreshExchangeChecklist, 10000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    const refreshExchangeDataMatrix = async () => setExchangeDataMatrix(await loadExchangeDataCapabilityMatrix());
    refreshExchangeDataMatrix();
    const timer = window.setInterval(refreshExchangeDataMatrix, 15000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    const refreshGlobalCoverage = async () => setGlobalCoverageMap(await loadGlobalFinancialCoverageMap());
    refreshGlobalCoverage();
    const timer = window.setInterval(refreshGlobalCoverage, 15000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    const refreshSecurity = async () => setHncSecurityComparison(await loadHNCPacketSecurityComparison());
    refreshSecurity();
    const timer = window.setInterval(refreshSecurity, 30000);
    return () => window.clearInterval(timer);
  }, []);

  const inventory = state?.inventory || {};
  const plan = state?.plan || {};
  const organism = state?.organism || {};
  const evolution = state?.evolution || {};
  const switchboard = state?.switchboard || {};
  const screens = plan.canonical_screens || [];
  const summary = inventory.summary || {};
  const organismSummary = organism.summary || {};
  const evolutionSummary = evolution.summary || {};
  const switchboardSummary = switchboard.summary || {};
  const planSummary = plan.summary || {};
  const percent = readinessPercent(summary);
  const securityBlockers = asNumber(summary.security_blocker_count);
  const blindSpotCount = asNumber(organismSummary.blind_spot_count);
  const highBlindSpotCount = asNumber(organismSummary.high_blind_spot_count);
  const manualActions = Object.entries(plan.safety_contract || {}).filter(([, value]) => Boolean(value));
  const activeScreen = screens.find((screen) => screen.id === active) || screens[0];
  const statusLines = organism.status_lines?.length ? organism.status_lines : runtime.statusLines;
  const activeSecurityBlockers = screenSecurityBlockers[active] || [];

  const domainCounts = useMemo(() => inventory.counts?.by_domain || {}, [inventory.counts]);
  const topDomains = Object.entries(domainCounts)
    .sort((a, b) => asNumber(b[1]) - asNumber(a[1]))
    .slice(0, 8);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border/50 bg-background/95">
        <div className="mx-auto flex max-w-[1500px] flex-col gap-4 px-4 py-5 lg:px-6">
          <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-center">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-2xl font-semibold tracking-normal">Aureon Unified Autonomous Console</h1>
                <Badge variant={securityBlockers ? "destructive" : "success"}>
                  {securityBlockers ? `${securityBlockers} blockers` : "clear"}
                </Badge>
                <Badge variant={highBlindSpotCount ? "destructive" : blindSpotCount ? "outline" : "success"}>
                  {blindSpotCount ? `${blindSpotCount} blind spots` : "fresh pulse"}
                </Badge>
                <Badge variant="outline">{plan.status || "manifest pending"}</Badge>
              </div>
              <p className="mt-1 max-w-4xl text-sm text-muted-foreground">
                Aureon works through its trading, accounting, research, vault, cognition, SaaS security, and self-audit systems while this shell exposes evidence, blockers, and manual-only boundaries.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Button onClick={refresh} variant="outline" size="sm" disabled={loading}>
                <RefreshCcw className="mr-2 h-4 w-4" />
                Refresh
              </Button>
              <Pill
                label={runtime.connected ? (runtime.clearancePending ? "runtime feed checking" : "runtime feed live") : "runtime feed offline"}
                tone={runtime.connected ? (runtime.clearancePending ? statusTone.orphaned : statusTone.wired) : statusTone.security_blocker}
              />
              <Pill label={`loaded ${state?.loadedAt ? new Date(state.loadedAt).toLocaleTimeString() : "pending"}`} tone="border-border bg-muted/20 text-muted-foreground" />
            </div>
          </div>

          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
            <MetricTile label="SaaS surfaces" value={formatCompact(summary.surface_count)} icon={Database} />
            <MetricTile label="Frontend surfaces" value={formatCompact(summary.frontend_surface_count)} icon={Activity} />
            <MetricTile label="Fresh domains" value={`${formatCompact(organismSummary.fresh_domain_count)}/${formatCompact(organismSummary.domain_count)}`} icon={Server} />
            <MetricTile label="Evolution queue" value={formatCompact(evolutionSummary.queue_count)} icon={ShieldCheck} tone={asNumber(evolutionSummary.blocked_count) ? "text-yellow-300" : "text-green-300"} />
            <MetricTile label="Capability modes" value={formatCompact(switchboardSummary.capability_count)} icon={Brain} tone={asNumber(switchboardSummary.blocker_count) ? "text-yellow-300" : "text-green-300"} />
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1500px] px-4 py-5 lg:px-6">
        {state?.errors?.length ? (
          <Card className="mb-4 border-yellow-500/30 bg-yellow-500/10">
            <CardContent className="flex flex-col gap-2 p-4 text-sm text-yellow-100 md:flex-row md:items-center">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              <div>{state.errors.join(" ")}</div>
            </CardContent>
          </Card>
        ) : null}

        {activeSecurityBlockers.map((blocker) => (
          <SecurityBlockerCard key={blocker.sourcePath} blocker={blocker} />
        ))}
        {active === "saas_security" ? <SaaSCredentialManagementPanel comparison={hncSecurityComparison} /> : null}
        <OrganismPulsePanel organism={organism} runtimeConnected={runtime.connected} />
        <AureonGeneratedOperationalConsole />
        <AureonWorkOrderExecutionConsole />
        <AureonCodingAgentSkillBaseConsole />
        <AureonCodingOrganismConsole />
        <AureonDirectorCapabilityBridgeConsole />
        <AureonAgentCompanyConsole />
        <FrontendEvolutionPanel evolution={evolution} />
        <CapabilitySwitchboardPanel switchboard={switchboard} />

        <Tabs value={active} onValueChange={setActive}>
          <ScrollArea className="w-full">
            <TabsList className="mb-4 h-auto min-w-max justify-start gap-1 bg-card/80 p-1">
              {screens.map((screen) => {
                const Icon = screenIcons[screen.id] || Activity;
                const missing = screen.missing_capabilities?.length || 0;
                return (
                  <TabsTrigger key={screen.id} value={screen.id} className="gap-2 whitespace-nowrap px-3 py-2">
                    <Icon className="h-4 w-4" />
                    <span>{screen.title}</span>
                    {missing ? <span className="rounded bg-yellow-500/20 px-1.5 text-[10px] text-yellow-200">{missing}</span> : null}
                  </TabsTrigger>
                );
              })}
            </TabsList>
          </ScrollArea>

          {screens.map((screen) => (
            <TabsContent key={screen.id} value={screen.id} className="mt-0">
              <ScreenPanel screen={screen} inventory={inventory} />
              {screen.id === "trading" ? (
                <>
                  <GlobalFinancialCoveragePanel coverage={globalCoverageMap} />
                  <ExchangeDataCapabilityMatrixPanel matrix={exchangeDataMatrix} />
                  <ExchangeMonitoringChecklistPanel checklist={exchangeChecklist} />
                  <TradingIntelligenceChecklistPanel checklist={tradingChecklist} />
                </>
              ) : null}
            </TabsContent>
          ))}
        </Tabs>

        <div className="mt-5 grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
          <Card className="bg-card/80">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <Radio className="h-4 w-4 text-primary" />
                Runtime Mirror
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
                {(runtime.metrics.length ? runtime.metrics : [
                  { label: "portfolio", value: "offline" },
                  { label: "open positions", value: "offline" },
                  { label: "trades", value: "offline" },
                  { label: "mode", value: "observe" },
                ]).map((metric) => (
                  <div key={metric.label} className="rounded-md border border-border/40 bg-muted/10 p-3">
                    <div className="text-[11px] uppercase text-muted-foreground">{metric.label}</div>
                    <div className="mt-1 truncate font-mono text-sm font-semibold">{metric.value}</div>
                  </div>
                ))}
              </div>
              <div className="flex flex-wrap gap-2">
                <Pill label={runtime.connected ? (runtime.clearancePending ? "connected checking" : "connected clear") : "offline"} tone={runtime.connected ? (runtime.clearancePending ? statusTone.orphaned : statusTone.wired) : statusTone.partial} />
                <Pill label={runtime.generatedAt ? `updated ${new Date(runtime.generatedAt).toLocaleTimeString()}` : "no runtime timestamp"} tone="border-border bg-muted/20 text-muted-foreground" />
                {runtime.endpoint ? <Pill label={runtime.endpoint.replace("http://127.0.0.1:", "")} tone="border-cyan-500/30 bg-cyan-500/10 text-cyan-300" /> : null}
                {runtime.clearances.map((clearance) => (
                  <Pill key={clearance} label={clearance} tone={statusTone.security_blocker} />
                ))}
              </div>
              {runtime.details.length ? (
                <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
                  {runtime.details.map((detail) => (
                    <div key={detail.label} className="rounded-md border border-border/40 bg-muted/10 p-3">
                      <div className="text-[11px] uppercase text-muted-foreground">{detail.label}</div>
                      <div className="mt-1 truncate font-mono text-sm font-semibold">{detail.value}</div>
                    </div>
                  ))}
                </div>
              ) : null}
              <div className="rounded-md border border-border/50 bg-black/35 p-3">
                {statusLines.length ? (
                  <pre className="max-h-52 overflow-auto whitespace-pre-wrap font-mono text-[11px] leading-5 text-foreground">
                    {statusLines.slice(-24).join("\n")}
                  </pre>
                ) : (
                  <div className="font-mono text-[11px] text-muted-foreground">Waiting for runtime status...</div>
                )}
              </div>
            </CardContent>
          </Card>

          <Card className="bg-card/80">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <Lock className="h-4 w-4 text-primary" />
                Safety And Manual Boundaries
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                {manualActions.map(([key]) => (
                  <div key={key} className="flex items-center justify-between gap-3 rounded-md border border-border/40 bg-muted/10 px-3 py-2">
                    <span className="text-sm">{key.replace(/_/g, " ")}</span>
                    <Badge variant="outline">visible</Badge>
                  </div>
                ))}
              </div>
              <div>
                <div className="mb-2 flex items-center justify-between text-xs text-muted-foreground">
                  <span>Inventory readiness</span>
                  <span>{percent}%</span>
                </div>
                <Progress value={percent} className="h-2" />
              </div>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div className="rounded-md border border-border/40 bg-muted/10 p-3">
                  <div className="text-xs text-muted-foreground">orphaned frontend</div>
                  <div className="mt-1 text-lg font-semibold">{formatCompact(summary.orphaned_frontend_count)}</div>
                </div>
                <div className="rounded-md border border-border/40 bg-muted/10 p-3">
                  <div className="text-xs text-muted-foreground">uncalled functions</div>
                  <div className="mt-1 text-lg font-semibold">{formatCompact(summary.uncalled_supabase_function_count)}</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="mt-5 grid gap-4 lg:grid-cols-[0.85fr_1.15fr]">
          <Card className="bg-card/80">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Domain Spread</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {topDomains.map(([domain, count]) => {
                const width = Math.min(100, Math.round((asNumber(count) / Math.max(1, asNumber(summary.surface_count))) * 100));
                return (
                  <div key={domain}>
                    <div className="mb-1 flex items-center justify-between text-xs">
                      <span className="capitalize text-muted-foreground">{domain.replace(/_/g, " ")}</span>
                      <span className="font-mono">{count}</span>
                    </div>
                    <div className="h-2 overflow-hidden rounded bg-muted/30">
                      <div className="h-full bg-primary" style={{ width: `${Math.max(4, width)}%` }} />
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>

          <Card className="bg-card/80">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Current Screen Focus</CardTitle>
            </CardHeader>
            <CardContent>
              {activeScreen ? (
                <div className="space-y-4">
                  <div>
                    <div className="text-lg font-semibold">{activeScreen.title}</div>
                    <p className="mt-1 text-sm text-muted-foreground">{activeScreen.goal}</p>
                  </div>
                  <div className="grid gap-3 md:grid-cols-3">
                    <div className="rounded-md border border-border/40 bg-muted/10 p-3">
                      <div className="text-xs text-muted-foreground">source surfaces</div>
                      <div className="mt-1 text-lg font-semibold">{activeScreen.source_surface_count}</div>
                    </div>
                    <div className="rounded-md border border-border/40 bg-muted/10 p-3">
                      <div className="text-xs text-muted-foreground">backend functions</div>
                      <div className="mt-1 text-lg font-semibold">{activeScreen.backend_functions.length}</div>
                    </div>
                    <div className="rounded-md border border-border/40 bg-muted/10 p-3">
                      <div className="text-xs text-muted-foreground">missing items</div>
                      <div className="mt-1 text-lg font-semibold">{activeScreen.missing_capabilities.length}</div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-sm text-muted-foreground">No screen plan available.</div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="mt-5 text-xs text-muted-foreground">
          Sources: {state?.inventorySource || "pending"}, {state?.planSource || "pending"}, {state?.organismSource || "pending"}, {state?.evolutionSource || "pending"}, and {state?.switchboardSource || "pending"}. Generated screens: {formatCompact(planSummary.screen_count)}. Readiness signal: {percent}%.
        </div>
      </main>
    </div>
  );
}

function freshnessTone(status: string): string {
  if (status === "fresh") return statusTone.wired;
  if (status === "attention") return "border-yellow-500/30 bg-yellow-500/10 text-yellow-200";
  if (status === "stale") return "border-orange-500/30 bg-orange-500/10 text-orange-200";
  if (status === "missing" || status === "broken") return statusTone.security_blocker;
  return statusTone.unknown;
}

function formatAge(seconds: unknown): string {
  const total = asNumber(seconds, -1);
  if (total < 0) return "unknown";
  if (total < 60) return `${Math.round(total)}s`;
  if (total < 3600) return `${Math.round(total / 60)}m`;
  return `${Math.round(total / 3600)}h`;
}

function OrganismPulsePanel({
  organism,
  runtimeConnected,
}: {
  organism: UnifiedFrontendState["organism"];
  runtimeConnected: boolean;
}) {
  const domains = organism.domains || [];
  const blindSpots = organism.blind_spots || [];
  const summary = organism.summary || {};
  const sortedDomains = [...domains].sort((a, b) => {
    const order: Record<string, number> = { missing: 0, broken: 1, stale: 2, attention: 3, fresh: 4 };
    return (order[a.status] ?? 5) - (order[b.status] ?? 5);
  });

  return (
    <div className="mb-5 grid gap-4 xl:grid-cols-[1fr_0.95fr]">
      <Card className="bg-card/80">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <Brain className="h-4 w-4 text-primary" />
            Organism Pulse
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <Pill label={organism.status || "pulse pending"} tone={freshnessTone((organism.status || "").includes("blind") ? "attention" : "fresh")} />
            <Pill label={`mode ${organism.mode || "safe_observation"}`} tone="border-blue-500/30 bg-blue-500/10 text-blue-200" />
            <Pill label={runtimeConnected ? "runtime feed connected" : "runtime feed offline"} tone={runtimeConnected ? statusTone.wired : statusTone.partial} />
            <Pill label={`updated ${organism.generated_at ? new Date(organism.generated_at).toLocaleTimeString() : "pending"}`} tone="border-border bg-muted/20 text-muted-foreground" />
          </div>

          <div className="grid gap-2 md:grid-cols-4">
            <div className="rounded-md border border-border/40 bg-muted/10 p-3">
              <div className="text-[11px] uppercase text-muted-foreground">domains</div>
              <div className="mt-1 text-lg font-semibold">{formatCompact(summary.domain_count)}</div>
            </div>
            <div className="rounded-md border border-border/40 bg-muted/10 p-3">
              <div className="text-[11px] uppercase text-muted-foreground">fresh</div>
              <div className="mt-1 text-lg font-semibold text-green-300">{formatCompact(summary.fresh_domain_count)}</div>
            </div>
            <div className="rounded-md border border-border/40 bg-muted/10 p-3">
              <div className="text-[11px] uppercase text-muted-foreground">stale/missing</div>
              <div className="mt-1 text-lg font-semibold text-yellow-200">
                {formatCompact(asNumber(summary.stale_domain_count) + asNumber(summary.missing_domain_count))}
              </div>
            </div>
            <div className="rounded-md border border-border/40 bg-muted/10 p-3">
              <div className="text-[11px] uppercase text-muted-foreground">blind spots</div>
              <div className="mt-1 text-lg font-semibold text-red-200">{formatCompact(summary.blind_spot_count)}</div>
            </div>
          </div>

          <ScrollArea className="h-[245px] pr-3">
            <div className="space-y-2">
              {sortedDomains.slice(0, 14).map((domain: OrganismDomainPulse) => (
                <div key={domain.id} className="rounded-md border border-border/40 bg-muted/10 p-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <div className="text-sm font-medium">{domain.label}</div>
                      <div className="mt-1 font-mono text-[11px] text-muted-foreground">{domain.source_path}</div>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      <Pill label={domain.status} tone={freshnessTone(domain.status)} />
                      <Pill label={formatAge(domain.age_seconds)} tone="border-border bg-muted/20 text-muted-foreground" />
                    </div>
                  </div>
                  {domain.blind_spots?.length ? (
                    <div className="mt-2 text-xs text-yellow-100">{domain.blind_spots.slice(0, 3).join(", ")}</div>
                  ) : null}
                </div>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>

      <Card className="bg-card/80">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <AlertTriangle className="h-4 w-4 text-primary" />
            Blind Spots And Next Actions
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <ScrollArea className="h-[276px] pr-3">
            <div className="space-y-2">
              {blindSpots.length ? (
                blindSpots.slice(0, 16).map((spot) => (
                  <div key={spot.id} className="rounded-md border border-border/40 bg-muted/10 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="font-mono text-[11px] text-muted-foreground">{spot.id}</div>
                      <Pill label={spot.severity} tone={spot.severity === "high" ? statusTone.security_blocker : "border-yellow-500/30 bg-yellow-500/10 text-yellow-200"} />
                    </div>
                    <div className="mt-2 text-sm">{spot.issue}</div>
                    {spot.next_action ? <div className="mt-2 text-xs text-muted-foreground">{spot.next_action}</div> : null}
                  </div>
                ))
              ) : (
                <div className="rounded-md border border-green-500/30 bg-green-500/10 p-4 text-sm text-green-100">
                  No blind spots in the current organism pulse.
                </div>
              )}
            </div>
          </ScrollArea>
          <div className="rounded-md border border-border/50 bg-black/35 p-3">
            <pre className="max-h-32 overflow-auto whitespace-pre-wrap font-mono text-[11px] leading-5 text-foreground">
              {(organism.status_lines || ["Waiting for organism pulse..."]).slice(0, 10).join("\n")}
            </pre>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function FrontendEvolutionPanel({ evolution }: { evolution: FrontendEvolutionQueueManifest }) {
  const summary = evolution.summary || {};
  const orders = [...(evolution.work_orders || [])]
    .sort((a, b) => asNumber(b.priority) - asNumber(a.priority))
    .slice(0, 10);

  return (
    <Card className="mb-5 bg-card/80">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <Activity className="h-4 w-4 text-primary" />
          Frontend Evolution Queue
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap gap-2">
          <Pill label={evolution.status || "queue pending"} tone={asNumber(summary.blocked_count) ? "border-yellow-500/30 bg-yellow-500/10 text-yellow-200" : statusTone.wired} />
          <Pill label={`${formatCompact(summary.ready_adapter_count)} ready adapters`} tone="border-green-500/30 bg-green-500/10 text-green-200" />
          <Pill label={`${formatCompact(summary.blocked_count)} blocked`} tone={asNumber(summary.blocked_count) ? statusTone.security_blocker : "border-border bg-muted/20 text-muted-foreground"} />
          <Pill label={`updated ${evolution.generated_at ? new Date(evolution.generated_at).toLocaleTimeString() : "pending"}`} tone="border-border bg-muted/20 text-muted-foreground" />
        </div>

        <div className="grid gap-2 md:grid-cols-5">
          <div className="rounded-md border border-border/40 bg-muted/10 p-3">
            <div className="text-[11px] uppercase text-muted-foreground">work orders</div>
            <div className="mt-1 text-lg font-semibold">{formatCompact(summary.queue_count)}</div>
          </div>
          <div className="rounded-md border border-border/40 bg-muted/10 p-3">
            <div className="text-[11px] uppercase text-muted-foreground">targets</div>
            <div className="mt-1 text-lg font-semibold">{formatCompact(summary.target_screen_count)}</div>
          </div>
          <div className="rounded-md border border-border/40 bg-muted/10 p-3">
            <div className="text-[11px] uppercase text-muted-foreground">generated links</div>
            <div className="mt-1 text-lg font-semibold">{formatCompact(summary.generated_output_link_count)}</div>
          </div>
          <div className="rounded-md border border-border/40 bg-muted/10 p-3">
            <div className="text-[11px] uppercase text-muted-foreground">archive</div>
            <div className="mt-1 text-lg font-semibold">{formatCompact(summary.archive_candidate_count)}</div>
          </div>
          <div className="rounded-md border border-border/40 bg-muted/10 p-3">
            <div className="text-[11px] uppercase text-muted-foreground">top priority</div>
            <div className="mt-1 text-lg font-semibold">{formatCompact(summary.highest_priority)}</div>
          </div>
        </div>

        <ScrollArea className="h-[330px] pr-3">
          <div className="space-y-3">
            {orders.length ? (
              orders.map((order) => (
                <div key={order.id} className="rounded-md border border-border/40 bg-muted/10 p-3">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="text-sm font-medium">{order.title}</div>
                      <div className="mt-1 truncate font-mono text-[11px] text-muted-foreground">{order.source_path}</div>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      <Pill label={`P${order.priority}`} tone="border-blue-500/30 bg-blue-500/10 text-blue-200" />
                      <Pill label={order.status} tone={order.status.includes("blocked") ? statusTone.security_blocker : freshnessTone("attention")} />
                      <Pill label={order.target_title} tone="border-border bg-muted/20 text-muted-foreground" />
                    </div>
                  </div>
                  <div className="mt-2 text-xs text-muted-foreground">{order.capability_summary}</div>
                  {order.frontend_action ? <div className="mt-2 text-xs text-foreground">{order.frontend_action}</div> : null}
                  {order.safety_boundary ? <div className="mt-2 text-[11px] text-yellow-100">{order.safety_boundary}</div> : null}
                </div>
              ))
            ) : (
              <div className="rounded-md border border-border/40 bg-muted/10 p-4 text-sm text-muted-foreground">
                No evolution work orders are mounted yet.
              </div>
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

function CapabilitySwitchboardPanel({ switchboard }: { switchboard: CapabilitySwitchboardManifest }) {
  const summary = switchboard.summary || {};
  const modes = [...(switchboard.capability_modes || [])];
  const intents = [...(switchboard.presentation_intents || [])]
    .sort((a, b) => asNumber(b.priority) - asNumber(a.priority))
    .slice(0, 10);
  const blockers = switchboard.blockers || [];
  const gates = Array.isArray(switchboard.hnc_control_contract?.anti_hallucination_gates)
    ? switchboard.hnc_control_contract.anti_hallucination_gates.map((gate) => String(gate))
    : [];

  return (
    <div className="mb-5 grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
      <Card className="bg-card/80">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <Brain className="h-4 w-4 text-primary" />
            Autonomous Capability Switchboard
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <Pill label={switchboard.status || "switchboard pending"} tone={asNumber(summary.blocker_count) ? "border-yellow-500/30 bg-yellow-500/10 text-yellow-200" : statusTone.wired} />
            <Pill label={`${formatCompact(summary.autonomous_capability_count)} autonomous modes`} tone="border-green-500/30 bg-green-500/10 text-green-200" />
            <Pill label={`${formatCompact(summary.presentation_intent_count)} presentation intents`} tone="border-blue-500/30 bg-blue-500/10 text-blue-200" />
            <Pill label={`updated ${switchboard.generated_at ? new Date(switchboard.generated_at).toLocaleTimeString() : "pending"}`} tone="border-border bg-muted/20 text-muted-foreground" />
          </div>

          <div className="grid gap-2 md:grid-cols-5">
            <div className="rounded-md border border-border/40 bg-muted/10 p-3">
              <div className="text-[11px] uppercase text-muted-foreground">capabilities</div>
              <div className="mt-1 text-lg font-semibold">{formatCompact(summary.capability_count)}</div>
            </div>
            <div className="rounded-md border border-border/40 bg-muted/10 p-3">
              <div className="text-[11px] uppercase text-muted-foreground">blocked</div>
              <div className="mt-1 text-lg font-semibold text-yellow-200">{formatCompact(summary.blocker_count)}</div>
            </div>
            <div className="rounded-md border border-border/40 bg-muted/10 p-3">
              <div className="text-[11px] uppercase text-muted-foreground">app/UI queue</div>
              <div className="mt-1 text-lg font-semibold">{formatCompact(summary.frontend_work_order_count)}</div>
            </div>
            <div className="rounded-md border border-border/40 bg-muted/10 p-3">
              <div className="text-[11px] uppercase text-muted-foreground">ready adapters</div>
              <div className="mt-1 text-lg font-semibold text-green-300">{formatCompact(summary.ready_adapter_count)}</div>
            </div>
            <div className="rounded-md border border-border/40 bg-muted/10 p-3">
              <div className="text-[11px] uppercase text-muted-foreground">runtime</div>
              <div className="mt-1 truncate text-sm font-semibold">{String(summary.runtime_feed_status || "unknown")}</div>
            </div>
          </div>

          <ScrollArea className="h-[356px] pr-3">
            <div className="space-y-3">
              {modes.length ? (
                modes.map((mode) => (
                  <div key={mode.id} className="rounded-md border border-border/40 bg-muted/10 p-3">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div className="min-w-0">
                        <div className="text-sm font-medium">{mode.title}</div>
                        <div className="mt-1 text-xs text-muted-foreground">{mode.authority_level.replace(/_/g, " ")}</div>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        <Pill label={mode.domain} tone="border-border bg-muted/20 text-muted-foreground" />
                        <Pill label={mode.status} tone={mode.status.startsWith("blocked") ? statusTone.security_blocker : freshnessTone(mode.status.includes("ready") ? "fresh" : "attention")} />
                        <Pill label={mode.autonomous_allowed ? "autonomous" : "manual"} tone={mode.autonomous_allowed ? statusTone.wired : statusTone.partial} />
                      </div>
                    </div>
                    {mode.systems?.length ? (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {mode.systems.slice(0, 5).map((system) => (
                          <Pill key={system} label={system} tone="border-blue-500/30 bg-blue-500/10 text-blue-100" />
                        ))}
                      </div>
                    ) : null}
                    {mode.next_action ? <div className="mt-2 text-xs text-muted-foreground">{mode.next_action}</div> : null}
                  </div>
                ))
              ) : (
                <div className="rounded-md border border-border/40 bg-muted/10 p-4 text-sm text-muted-foreground">
                  No capability modes are mounted yet.
                </div>
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>

      <Card className="bg-card/80">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <Eye className="h-4 w-4 text-primary" />
            What Aureon Chooses To Show Next
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-md border border-border/40 bg-muted/10 p-3">
            <div className="text-[11px] uppercase text-muted-foreground">HNC anti-drift gates</div>
            <div className="mt-2 flex flex-wrap gap-1">
              {(gates.length ? gates : ["source_evidence_required", "safe_authority_boundary_checked"]).slice(0, 7).map((gate) => (
                <Pill key={gate} label={gate.replace(/_/g, " ")} tone="border-green-500/30 bg-green-500/10 text-green-100" />
              ))}
            </div>
          </div>

          <ScrollArea className="h-[255px] pr-3">
            <div className="space-y-2">
              {intents.length ? (
                intents.map((intent) => (
                  <div key={intent.id} className="rounded-md border border-border/40 bg-muted/10 p-3">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div>
                        <div className="text-sm font-medium">{intent.title}</div>
                        <div className="mt-1 text-xs text-muted-foreground">{intent.reason}</div>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        <Pill label={`P${intent.priority}`} tone="border-blue-500/30 bg-blue-500/10 text-blue-200" />
                        <Pill label={intent.display_mode.replace(/_/g, " ")} tone="border-border bg-muted/20 text-muted-foreground" />
                      </div>
                    </div>
                    {intent.next_action ? <div className="mt-2 text-xs text-foreground">{intent.next_action}</div> : null}
                  </div>
                ))
              ) : (
                <div className="rounded-md border border-border/40 bg-muted/10 p-4 text-sm text-muted-foreground">
                  No presentation intents are mounted yet.
                </div>
              )}
            </div>
          </ScrollArea>

          <div className="space-y-2">
            <div className="text-xs uppercase text-muted-foreground">Current blockers</div>
            {(blockers.length ? blockers.slice(0, 4) : [{ id: "none", reason: "No switchboard blockers reported." }]).map((blocker) => (
              <div key={String(blocker.id)} className="rounded-md border border-border/40 bg-muted/10 px-3 py-2 text-xs">
                <span className="font-mono text-muted-foreground">{String(blocker.id)}</span>
                <span className="ml-2 text-foreground">{String(blocker.reason || "")}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function GlobalFinancialCoveragePanel({ coverage }: { coverage: GlobalFinancialCoverageMap | null }) {
  const summary = coverage?.summary || {};
  const rows = coverage?.rows || [];
  const sources = coverage?.source_registry || [];
  const blockedSources = sources.filter((source) => !source.usable_for_mapping).slice(0, 8);
  const missing = (summary.top_missing || []).slice(0, 6);
  const coveragePercent = Math.round(asNumber(summary.coverage_percent));
  const accountedPercent = Math.round(asNumber(summary.accounted_percent));

  return (
    <Card className="mt-4 bg-card/80">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <LineChart className="h-4 w-4 text-primary" />
          Global Financial Coverage Map
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap items-center gap-2">
          <Pill
            label={coverage?.status ? String(coverage.status).replace(/_/g, " ") : "coverage map pending"}
            tone={summary.mapping_complete ? statusTone.wired : statusTone.partial}
          />
          <Pill
            label={coverage?.generated_at ? `updated ${new Date(coverage.generated_at).toLocaleTimeString()}` : "no map timestamp"}
            tone="border-border bg-muted/20 text-muted-foreground"
          />
          <Pill label="/aureon_global_financial_coverage_map.json" tone="border-cyan-500/30 bg-cyan-500/10 text-cyan-200" />
        </div>

        <div className="rounded-md border border-cyan-500/30 bg-cyan-500/10 p-3">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="text-[11px] uppercase text-cyan-100/80">configured source coverage</div>
              <div className="mt-1 text-lg font-semibold text-cyan-50">{coveragePercent}% mapped</div>
              <div className="mt-1 text-xs text-cyan-50/70">
                {formatCompact(summary.usable_source_count)}/{formatCompact(summary.configured_reachable_source_count)} configured/reachable sources usable; {accountedPercent}% accounted.
              </div>
            </div>
            <Pill
              label={summary.mapping_complete ? "100% mapped for configured registry" : "expanding map"}
              tone={summary.mapping_complete ? statusTone.wired : statusTone.partial}
            />
          </div>
          <Progress value={coveragePercent} className="mt-3 h-2" />
        </div>

        <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-6">
          <div className="rounded-md border border-border/40 bg-muted/10 p-3">
            <div className="text-[11px] uppercase text-muted-foreground">usable domains</div>
            <div className="mt-1 text-lg font-semibold">{formatCompact(summary.usable_domain_count)}/{formatCompact(summary.domain_count)}</div>
          </div>
          <div className="rounded-md border border-border/40 bg-muted/10 p-3">
            <div className="text-[11px] uppercase text-muted-foreground">fresh domains</div>
            <div className="mt-1 text-lg font-semibold">{formatCompact(summary.fresh_domain_count)}</div>
          </div>
          <div className="rounded-md border border-border/40 bg-muted/10 p-3">
            <div className="text-[11px] uppercase text-muted-foreground">live tickers</div>
            <div className="mt-1 text-lg font-semibold">{formatCompact(summary.live_ticker_count)}</div>
          </div>
          <div className="rounded-md border border-border/40 bg-muted/10 p-3">
            <div className="text-[11px] uppercase text-muted-foreground">live sources</div>
            <div className="mt-1 text-lg font-semibold">{formatCompact(summary.active_live_source_count)}</div>
          </div>
          <div className="rounded-md border border-border/40 bg-muted/10 p-3">
            <div className="text-[11px] uppercase text-muted-foreground">history rows</div>
            <div className="mt-1 text-lg font-semibold">{formatCompact(summary.total_history_rows)}</div>
          </div>
          <div className="rounded-md border border-border/40 bg-muted/10 p-3">
            <div className="text-[11px] uppercase text-muted-foreground">missing creds</div>
            <div className="mt-1 text-lg font-semibold text-yellow-200">{formatCompact(summary.credential_missing_source_count)}</div>
          </div>
        </div>

        {missing.length ? (
          <div className="space-y-2">
            <div className="text-xs uppercase text-muted-foreground">Map gaps</div>
            {missing.map((item, index) => (
              <div key={`${String(item.domain)}-${index}`} className="rounded-md border border-yellow-500/30 bg-yellow-500/10 px-3 py-2 text-xs">
                <span className="font-semibold text-yellow-100">{String(item.domain || "unknown")}</span>
                <span className="ml-2 text-yellow-100/80">{String(item.missing || "")}</span>
              </div>
            ))}
          </div>
        ) : null}

        {blockedSources.length ? (
          <div className="space-y-2">
            <div className="text-xs uppercase text-muted-foreground">Source registry gaps</div>
            {blockedSources.map((source) => (
              <div key={source.source_id} className="rounded-md border border-border/40 bg-muted/10 px-3 py-2 text-xs">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-semibold">{source.title || source.source_id}</span>
                  <div className="flex flex-wrap gap-1">
                    <Pill label={source.credential_state || "unknown"} tone={source.credential_state === "missing" ? statusTone.security_blocker : statusTone.partial} />
                    <Pill label={source.governor_action || "checking"} tone={source.usable_for_mapping ? statusTone.wired : statusTone.orphaned} />
                  </div>
                </div>
                <div className="mt-1 text-muted-foreground">{source.reason || source.next_action || "No blocker detail."}</div>
                {source.decision_blocker ? <div className="mt-1 text-yellow-100">Decision hold: {source.decision_blocker.replace(/_/g, " ")}</div> : null}
                <div className="mt-2 flex flex-wrap gap-1">
                  {(source.asset_classes || []).slice(0, 5).map((assetClass) => (
                    <Pill key={`${source.source_id}-${assetClass}`} label={assetClass.replace(/_/g, " ")} tone="border-blue-500/30 bg-blue-500/10 text-blue-200" />
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : null}

        <ScrollArea className="h-[235px] pr-3">
          <div className="space-y-2">
            {rows.length ? (
              rows.map((row) => (
                <div key={row.domain} className="rounded-md border border-border/40 bg-muted/10 p-3">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div className="min-w-0">
                      <div className="text-sm font-medium">{row.domain.replace(/_/g, " ")}</div>
                      <div className="mt-1 text-xs text-muted-foreground">{row.coverage}</div>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      <Pill label={row.fresh ? "fresh" : "not fresh"} tone={row.fresh ? statusTone.wired : statusTone.partial} />
                      <Pill label={row.usable ? "usable" : "gap"} tone={row.usable ? statusTone.wired : statusTone.orphaned} />
                    </div>
                  </div>
                  <div className="mt-2 grid gap-2 sm:grid-cols-2">
                    <div className="rounded-md border border-border/40 bg-background/30 px-2 py-1">
                      <div className="text-[10px] uppercase text-muted-foreground">live count</div>
                      <div className="font-mono text-xs">{formatCompact(row.live_count)}</div>
                    </div>
                    <div className="rounded-md border border-border/40 bg-background/30 px-2 py-1">
                      <div className="text-[10px] uppercase text-muted-foreground">history count</div>
                      <div className="font-mono text-xs">{formatCompact(row.history_count)}</div>
                    </div>
                  </div>
                  {row.next_action ? <div className="mt-2 text-xs text-muted-foreground">{row.next_action}</div> : null}
                </div>
              ))
            ) : (
              <div className="rounded-md border border-border/40 bg-muted/10 p-4 text-sm text-muted-foreground">
                Coverage map not generated yet. Run python -m aureon.autonomous.aureon_global_financial_coverage_map.
              </div>
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

function ExchangeMonitoringChecklistPanel({ checklist }: { checklist: ExchangeMonitoringChecklist | null }) {
  const summary = checklist?.summary || {};
  const rows = checklist?.rows || [];
  const missing = (summary.top_missing || []).slice(0, 6);

  return (
    <Card className="mt-4 bg-card/80">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <Radio className="h-4 w-4 text-primary" />
          Exchange Monitoring Checklist
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap items-center gap-2">
          <Pill
            label={checklist?.status ? String(checklist.status).replace(/_/g, " ") : "exchange checklist pending"}
            tone={summary.runtime_stale ? statusTone.orphaned : statusTone.wired}
          />
          <Pill
            label={checklist?.generated_at ? `updated ${new Date(checklist.generated_at).toLocaleTimeString()}` : "no checklist timestamp"}
            tone="border-border bg-muted/20 text-muted-foreground"
          />
          <Pill label="/aureon_exchange_monitoring_checklist.json" tone="border-cyan-500/30 bg-cyan-500/10 text-cyan-200" />
          {summary.stale_reason ? <Pill label={String(summary.stale_reason)} tone={statusTone.security_blocker} /> : null}
        </div>

        <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-6">
          <div className="rounded-md border border-border/40 bg-muted/10 p-3">
            <div className="text-[11px] uppercase text-muted-foreground">connected</div>
            <div className="mt-1 text-lg font-semibold">{formatCompact(summary.connected_exchange_count)}/{formatCompact(summary.exchange_count)}</div>
          </div>
          <div className="rounded-md border border-border/40 bg-muted/10 p-3">
            <div className="text-[11px] uppercase text-muted-foreground">active feeds</div>
            <div className="mt-1 text-lg font-semibold">{formatCompact(summary.active_exchange_count)}</div>
          </div>
          <div className="rounded-md border border-border/40 bg-muted/10 p-3">
            <div className="text-[11px] uppercase text-muted-foreground">fresh feeds</div>
            <div className="mt-1 text-lg font-semibold">{formatCompact(summary.fresh_exchange_count)}</div>
          </div>
          <div className="rounded-md border border-border/40 bg-muted/10 p-3">
            <div className="text-[11px] uppercase text-muted-foreground">decision fed</div>
            <div className="mt-1 text-lg font-semibold">{formatCompact(summary.decision_fed_exchange_count)}</div>
          </div>
          <div className="rounded-md border border-border/40 bg-muted/10 p-3">
            <div className="text-[11px] uppercase text-muted-foreground">waveforms</div>
            <div className="mt-1 text-lg font-semibold">{formatCompact(summary.waveform_history_exchange_count)}</div>
          </div>
          <div className="rounded-md border border-border/40 bg-muted/10 p-3">
            <div className="text-[11px] uppercase text-muted-foreground">tickers</div>
            <div className="mt-1 text-lg font-semibold">{formatCompact(summary.total_tickers_monitored)}</div>
          </div>
        </div>

        {missing.length ? (
          <div className="space-y-2">
            <div className="text-xs uppercase text-muted-foreground">Missing by exchange</div>
            {missing.map((item, index) => (
              <div key={`${String(item.exchange)}-${index}`} className="rounded-md border border-yellow-500/30 bg-yellow-500/10 px-3 py-2 text-xs">
                <span className="font-semibold text-yellow-100">{String(item.exchange || "unknown")}</span>
                <span className="ml-2 text-yellow-100/80">{String(item.missing || "")}</span>
              </div>
            ))}
          </div>
        ) : null}

        <ScrollArea className="h-[280px] pr-3">
          <div className="space-y-2">
            {rows.length ? (
              rows.map((row) => (
                <div key={row.exchange} className="rounded-md border border-border/40 bg-muted/10 p-3">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div className="min-w-0">
                      <div className="text-sm font-medium">{row.label || row.exchange}</div>
                      <div className="mt-1 flex flex-wrap gap-1">
                        {(row.markets || []).slice(0, 4).map((market) => (
                          <Pill key={market} label={market.replace(/_/g, " ")} tone="border-blue-500/30 bg-blue-500/10 text-blue-200" />
                        ))}
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      <Pill label={row.connected ? "client ready" : "client missing"} tone={row.connected ? statusTone.wired : statusTone.orphaned} />
                      <Pill label={row.cache_fresh ? "fresh feed" : row.cache_active ? "feed stale" : "feed missing"} tone={row.cache_fresh ? statusTone.wired : statusTone.partial} />
                      <Pill label={row.feeds_decision_logic ? "decision fed" : "not fed"} tone={row.feeds_decision_logic ? statusTone.wired : statusTone.orphaned} />
                    </div>
                  </div>
                  <div className="mt-3 grid gap-2 sm:grid-cols-4">
                    <div className="rounded-md border border-border/40 bg-background/30 px-2 py-1">
                      <div className="text-[10px] uppercase text-muted-foreground">tickers</div>
                      <div className="font-mono text-xs">{formatCompact(row.ticker_count)}</div>
                    </div>
                    <div className="rounded-md border border-border/40 bg-background/30 px-2 py-1">
                      <div className="text-[10px] uppercase text-muted-foreground">venues</div>
                      <div className="font-mono text-xs">{formatCompact(row.action_plan_venue_count)}</div>
                    </div>
                    <div className="rounded-md border border-border/40 bg-background/30 px-2 py-1">
                      <div className="text-[10px] uppercase text-muted-foreground">waveform</div>
                      <div className="font-mono text-xs">{row.waveform_history_active ? "active" : "missing"}</div>
                    </div>
                    <div className="rounded-md border border-border/40 bg-background/30 px-2 py-1">
                      <div className="text-[10px] uppercase text-muted-foreground">fast money</div>
                      <div className="font-mono text-xs">{row.usable_for_fast_money ? "usable" : "held"}</div>
                    </div>
                  </div>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {(row.monitored_now || []).slice(0, 6).map((item) => (
                      <Pill key={item} label={item.replace(/_/g, " ")} tone="border-green-500/30 bg-green-500/10 text-green-100" />
                    ))}
                  </div>
                  {(row.missing || []).length ? (
                    <div className="mt-2 text-xs text-yellow-100">{(row.missing || []).slice(0, 5).join(", ")}</div>
                  ) : null}
                </div>
              ))
            ) : (
              <div className="rounded-md border border-border/40 bg-muted/10 p-4 text-sm text-muted-foreground">
                Exchange checklist not generated yet. Run python -m aureon.autonomous.aureon_exchange_monitoring_checklist.
              </div>
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

function ExchangeDataCapabilityMatrixPanel({ matrix }: { matrix: ExchangeDataCapabilityMatrix | null }) {
  const summary = matrix?.summary || {};
  const rows = matrix?.rows || [];

  return (
    <Card className="mt-4 bg-card/80">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <Database className="h-4 w-4 text-primary" />
          Exchange Data Capability Matrix
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap items-center gap-2">
          <Pill
            label={matrix?.status ? String(matrix.status).replace(/_/g, " ") : "capability matrix pending"}
            tone={summary.runtime_stale ? statusTone.orphaned : summary.runtime_booting || summary.trading_ready === false || summary.data_ready === false ? statusTone.partial : statusTone.wired}
          />
          <Pill
            label={matrix?.generated_at ? `updated ${new Date(matrix.generated_at).toLocaleTimeString()}` : "no matrix timestamp"}
            tone="border-border bg-muted/20 text-muted-foreground"
          />
          <Pill label="/aureon_exchange_data_capability_matrix.json" tone="border-cyan-500/30 bg-cyan-500/10 text-cyan-200" />
          {summary.stale_reason ? <Pill label={String(summary.stale_reason)} tone={statusTone.security_blocker} /> : null}
        </div>

        <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-6">
          <div className="rounded-md border border-border/40 bg-muted/10 p-3">
            <div className="text-[11px] uppercase text-muted-foreground">connected</div>
            <div className="mt-1 text-lg font-semibold">{formatCompact(summary.connected_exchange_count)}/{formatCompact(summary.exchange_count)}</div>
          </div>
          <div className="rounded-md border border-border/40 bg-muted/10 p-3">
            <div className="text-[11px] uppercase text-muted-foreground">fresh feeds</div>
            <div className="mt-1 text-lg font-semibold">{formatCompact(summary.fresh_feed_count)}</div>
          </div>
          <div className="rounded-md border border-border/40 bg-muted/10 p-3">
            <div className="text-[11px] uppercase text-muted-foreground">decision fed</div>
            <div className="mt-1 text-lg font-semibold">{formatCompact(summary.decision_fed_count)}</div>
          </div>
          <div className="rounded-md border border-border/40 bg-muted/10 p-3">
            <div className="text-[11px] uppercase text-muted-foreground">cash active</div>
            <div className="mt-1 text-lg font-semibold">{formatCompact(summary.cash_active_exchange_count)}</div>
          </div>
          <div className="rounded-md border border-border/40 bg-muted/10 p-3">
            <div className="text-[11px] uppercase text-muted-foreground">data boost</div>
            <div className="mt-1 text-lg font-semibold">{formatCompact(summary.data_boost_eligible_count)}</div>
          </div>
          <div className="rounded-md border border-border/40 bg-muted/10 p-3">
            <div className="text-[11px] uppercase text-muted-foreground">tickers</div>
            <div className="mt-1 text-lg font-semibold">{formatCompact(summary.total_ticker_count)}</div>
          </div>
        </div>

        <ScrollArea className="h-[360px] pr-3">
          <div className="space-y-3">
            {rows.length ? (
              rows.map((row) => {
                const state = row.current_state || {};
                const policy = row.optimization_policy || {};
                return (
                  <div key={row.exchange} className="rounded-md border border-border/40 bg-muted/10 p-3">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div className="min-w-0">
                        <div className="text-sm font-medium">{row.label || row.exchange}</div>
                        {row.system_role ? <div className="mt-1 text-xs text-muted-foreground">{row.system_role}</div> : null}
                      </div>
                      <div className="flex flex-wrap gap-1">
                        <Pill label={state.connected ? "client ready" : "client missing"} tone={state.connected ? statusTone.wired : statusTone.orphaned} />
                        <Pill label={state.fresh_feed ? "fresh feed" : state.active_feed ? "feed stale" : "feed missing"} tone={state.fresh_feed ? statusTone.wired : statusTone.partial} />
                        <Pill label={policy.data_boost_eligible ? "data boost" : "execution reserve"} tone={policy.data_boost_eligible ? "border-cyan-500/30 bg-cyan-500/10 text-cyan-200" : "border-yellow-500/30 bg-yellow-500/10 text-yellow-200"} />
                      </div>
                    </div>

                    <div className="mt-3 grid gap-2 sm:grid-cols-4">
                      <div className="rounded-md border border-border/40 bg-background/30 px-2 py-1">
                        <div className="text-[10px] uppercase text-muted-foreground">safe calls/min</div>
                        <div className="font-mono text-xs">{formatCompact(policy.safe_calls_per_min)}</div>
                      </div>
                      <div className="rounded-md border border-border/40 bg-background/30 px-2 py-1">
                        <div className="text-[10px] uppercase text-muted-foreground">market data/min</div>
                        <div className="font-mono text-xs">{formatCompact(policy.market_data_budget_per_min)}</div>
                      </div>
                      <div className="rounded-md border border-border/40 bg-background/30 px-2 py-1">
                        <div className="text-[10px] uppercase text-muted-foreground">reserve/min</div>
                        <div className="font-mono text-xs">{formatCompact(policy.execution_reserved_per_min)}</div>
                      </div>
                      <div className="rounded-md border border-border/40 bg-background/30 px-2 py-1">
                        <div className="text-[10px] uppercase text-muted-foreground">cash estimate</div>
                        <div className="font-mono text-xs">{formatCompact(policy.cash_usd_estimate)}</div>
                      </div>
                    </div>

                    <div className="mt-2 flex flex-wrap gap-1">
                      {(row.trading_modes || []).slice(0, 5).map((mode) => (
                        <Pill key={`${row.exchange}-${mode}`} label={mode.replace(/_/g, " ")} tone="border-blue-500/30 bg-blue-500/10 text-blue-200" />
                      ))}
                    </div>

                    <div className="mt-3 grid gap-2 lg:grid-cols-2">
                      {(row.data_channels || []).slice(0, 6).map((channel) => (
                        <div key={`${row.exchange}-${channel.name}`} className="rounded-md border border-border/40 bg-background/30 px-2 py-2">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <div className="text-xs font-medium">{channel.name.replace(/_/g, " ")}</div>
                            <Pill label={String(channel.status || "mapped").replace(/_/g, " ")} tone={String(channel.status || "").includes("missing") ? statusTone.orphaned : statusTone.wired} />
                          </div>
                          <div className="mt-1 text-[11px] text-muted-foreground">{channel.optimization_use || channel.source}</div>
                        </div>
                      ))}
                    </div>

                    {row.next_optimization ? <div className="mt-3 text-xs text-foreground">{row.next_optimization}</div> : null}
                    {(row.gaps || []).length ? <div className="mt-2 text-xs text-yellow-100">{(row.gaps || []).slice(0, 5).join(", ")}</div> : null}
                  </div>
                );
              })
            ) : (
              <div className="rounded-md border border-border/40 bg-muted/10 p-4 text-sm text-muted-foreground">
                Capability matrix not generated yet. Run python -m aureon.autonomous.aureon_exchange_data_capability_matrix.
              </div>
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

function TradingIntelligenceChecklistPanel({ checklist }: { checklist: TradingIntelligenceChecklist | null }) {
  const summary = checklist?.summary || {};
  const trust = checklist?.decision_trust;
  const rows = checklist?.rows || [];
  const metaContext = summary.metacognitive_data_context;
  const blockers = (summary.top_blockers || []).slice(0, 5);
  const criticalRows = rows
    .filter((row) => row.blocker || !row.usable_for_decision)
    .slice(0, 8);
  const categoryRows = [
    { label: "direct live", value: summary.direct_live_systems_passing, total: rows.filter((row) => row.category === "live_market_intelligence").length },
    { label: "HNC/Auris", value: summary.hnc_auris_passing, total: rows.filter((row) => row.category === "hnc_auris_cognition").length },
    { label: "counter intel", value: summary.counter_intelligence_passing, total: rows.filter((row) => row.category === "counter_intelligence_validation").length },
    { label: "profit timing", value: summary.profit_timing_passing, total: rows.filter((row) => row.category === "profit_timing").length },
    { label: "meta context", value: summary.metacognitive_context_passing, total: rows.filter((row) => row.category === "metacognitive_data_context").length },
  ];

  return (
    <Card className="mt-4 bg-card/80">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <ShieldCheck className="h-4 w-4 text-primary" />
          Trading Intelligence Freshness Checklist
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap items-center gap-2">
          <Pill
            label={checklist?.status ? String(checklist.status).replace(/_/g, " ") : "checklist pending"}
            tone={summary.runtime_fresh ? statusTone.wired : statusTone.orphaned}
          />
          <Pill
            label={checklist?.generated_at ? `updated ${new Date(checklist.generated_at).toLocaleTimeString()}` : "no checklist timestamp"}
            tone="border-border bg-muted/20 text-muted-foreground"
          />
          <Pill label="/aureon_trading_intelligence_checklist.json" tone="border-cyan-500/30 bg-cyan-500/10 text-cyan-200" />
          {summary.stale_reason ? <Pill label={String(summary.stale_reason)} tone={statusTone.security_blocker} /> : null}
        </div>

        <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-6">
          <div className="rounded-md border border-border/40 bg-muted/10 p-3">
            <div className="text-[11px] uppercase text-muted-foreground">fresh usable</div>
            <div className="mt-1 text-lg font-semibold">{formatCompact(summary.fresh_usable_count)}/{formatCompact(summary.system_count)}</div>
          </div>
          <div className="rounded-md border border-border/40 bg-muted/10 p-3">
            <div className="text-[11px] uppercase text-muted-foreground">decision fed</div>
            <div className="mt-1 text-lg font-semibold">{formatCompact(summary.decision_fed_count)}</div>
          </div>
          <div className="rounded-md border border-border/40 bg-muted/10 p-3">
            <div className="text-[11px] uppercase text-muted-foreground">present</div>
            <div className="mt-1 text-lg font-semibold">{formatCompact(summary.present_count)}</div>
          </div>
          <div className="rounded-md border border-border/40 bg-muted/10 p-3">
            <div className="text-[11px] uppercase text-muted-foreground">active</div>
            <div className="mt-1 text-lg font-semibold">{formatCompact(summary.active_count)}</div>
          </div>
          <div className="rounded-md border border-border/40 bg-muted/10 p-3">
            <div className="text-[11px] uppercase text-muted-foreground">stale/blocked</div>
            <div className="mt-1 text-lg font-semibold text-yellow-200">{formatCompact(summary.stale_or_blocked_count)}</div>
          </div>
          <div className="rounded-md border border-border/40 bg-muted/10 p-3">
            <div className="text-[11px] uppercase text-muted-foreground">self trust</div>
            <div className="mt-1 text-lg font-semibold">{Math.round(asNumber(summary.decision_self_trust_score) * 100)}%</div>
          </div>
        </div>

        {trust ? (
          <div className="rounded-md border border-cyan-500/30 bg-cyan-500/10 p-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <div className="text-[11px] uppercase text-cyan-100/80">decision posture</div>
                <div className="mt-1 font-mono text-sm font-semibold text-cyan-50">
                  {String(trust.posture || summary.decision_posture || "checking").replace(/_/g, " ")}
                </div>
              </div>
              <div className="flex flex-wrap gap-1">
                <Pill label={trust.trust_to_decide ? "trusts decision" : "still measuring"} tone={trust.trust_to_decide ? statusTone.wired : statusTone.orphaned} />
                <Pill label={trust.trust_to_act ? "live intent ready" : trust.trust_to_shadow ? "shadow ready" : "learning"} tone={trust.trust_to_act ? statusTone.wired : statusTone.partial} />
              </div>
            </div>
            <div className="mt-2 text-xs text-cyan-50/80">{trust.self_instruction}</div>
            <div className="mt-1 text-[11px] text-cyan-50/60">{trust.not_fear_reason}</div>
          </div>
        ) : null}

        {metaContext?.present ? (
          <div className="rounded-md border border-emerald-500/30 bg-emerald-500/10 p-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <div className="text-[11px] uppercase text-emerald-100/80">metacognitive data ocean</div>
                <div className="mt-1 text-sm text-emerald-50">
                  {metaContext.state_phrase || "Global data context is being measured."}
                </div>
              </div>
              <div className="flex flex-wrap gap-1">
                <Pill
                  label={metaContext.usable_for_metacognition ? "usable for thought" : "filling gaps"}
                  tone={metaContext.usable_for_metacognition ? statusTone.wired : statusTone.partial}
                />
                <Pill
                  label={metaContext.usable_for_live_decision ? "live decision usable" : "runtime gated"}
                  tone={metaContext.usable_for_live_decision ? statusTone.wired : statusTone.orphaned}
                />
              </div>
            </div>
            <div className="mt-3 grid gap-2 sm:grid-cols-2 xl:grid-cols-5">
              <div className="rounded-md border border-emerald-400/20 bg-background/30 p-2">
                <div className="text-[10px] uppercase text-emerald-100/70">mapped</div>
                <div className="font-mono text-sm text-emerald-50">{Math.round(asNumber(metaContext.coverage_percent))}%</div>
              </div>
              <div className="rounded-md border border-emerald-400/20 bg-background/30 p-2">
                <div className="text-[10px] uppercase text-emerald-100/70">live sources</div>
                <div className="font-mono text-sm text-emerald-50">{formatCompact(metaContext.active_live_source_count)}</div>
              </div>
              <div className="rounded-md border border-emerald-400/20 bg-background/30 p-2">
                <div className="text-[10px] uppercase text-emerald-100/70">tickers</div>
                <div className="font-mono text-sm text-emerald-50">{formatCompact(metaContext.live_ticker_count)}</div>
              </div>
              <div className="rounded-md border border-emerald-400/20 bg-background/30 p-2">
                <div className="text-[10px] uppercase text-emerald-100/70">history rows</div>
                <div className="font-mono text-sm text-emerald-50">{formatCompact(metaContext.history_rows)}</div>
              </div>
              <div className="rounded-md border border-emerald-400/20 bg-background/30 p-2">
                <div className="text-[10px] uppercase text-emerald-100/70">cleanliness</div>
                <div className="font-mono text-sm text-emerald-50">{Math.round(asNumber(metaContext.cognitive_cleanliness_score) * 100)}%</div>
              </div>
            </div>
            {metaContext.decision_blocker ? <div className="mt-2 text-[11px] text-yellow-100">{metaContext.decision_blocker}</div> : null}
          </div>
        ) : null}

        <div className="grid gap-2 md:grid-cols-5">
          {categoryRows.map((item) => (
            <div key={item.label} className="rounded-md border border-border/40 bg-muted/10 p-3">
              <div className="text-[11px] uppercase text-muted-foreground">{item.label}</div>
              <div className="mt-1 font-mono text-sm font-semibold">{formatCompact(item.value)}/{formatCompact(item.total)}</div>
            </div>
          ))}
        </div>

        {blockers.length ? (
          <div className="space-y-2">
            <div className="text-xs uppercase text-muted-foreground">Top blockers</div>
            {blockers.map((blocker, index) => (
              <div key={`${String(blocker.system)}-${index}`} className="rounded-md border border-yellow-500/30 bg-yellow-500/10 px-3 py-2 text-xs">
                <span className="font-semibold text-yellow-100">{String(blocker.system || "unknown")}</span>
                <span className="ml-2 text-yellow-100/80">{String(blocker.blocker || "")}</span>
              </div>
            ))}
          </div>
        ) : null}

        <ScrollArea className="h-[260px] pr-3">
          <div className="space-y-2">
            {(criticalRows.length ? criticalRows : rows.slice(0, 8)).map((row) => (
              <div key={`${row.system}-${row.downstream_stage}`} className="rounded-md border border-border/40 bg-muted/10 p-3">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className="text-sm font-medium">{row.system}</div>
                    <div className="mt-1 truncate font-mono text-[11px] text-muted-foreground">{row.evidence_source}</div>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    <Pill label={row.downstream_stage.replace(/_/g, " ")} tone="border-blue-500/30 bg-blue-500/10 text-blue-200" />
                    <Pill label={row.fed_to_decision_logic ? "decision fed" : "not fed"} tone={row.fed_to_decision_logic ? statusTone.wired : statusTone.partial} />
                    <Pill label={row.usable_for_decision ? "fresh usable" : "held"} tone={row.usable_for_decision ? statusTone.wired : statusTone.orphaned} />
                  </div>
                </div>
                {row.blocker ? <div className="mt-2 text-xs text-yellow-100">{row.blocker}</div> : null}
              </div>
            ))}
            {!rows.length ? (
              <div className="rounded-md border border-border/40 bg-muted/10 p-4 text-sm text-muted-foreground">
                Checklist not generated yet. Run python -m aureon.autonomous.aureon_trading_intelligence_checklist.
              </div>
            ) : null}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

function ScreenPanel({ screen, inventory }: { screen: FrontendScreenPlan; inventory: SaaSInventoryManifest }) {
  const surfaces = surfacesForScreen(inventory, screen);
  const Icon = screenIcons[screen.id] || Activity;

  return (
    <div className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
      <Card className="bg-card/80">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <Icon className="h-4 w-4 text-primary" />
            {screen.title}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">{screen.goal}</p>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <div className="rounded-md border border-border/40 bg-muted/10 p-3">
              <div className="text-xs text-muted-foreground">sources</div>
              <div className="mt-1 text-lg font-semibold">{screen.source_surface_count}</div>
            </div>
            <div className="rounded-md border border-border/40 bg-muted/10 p-3">
              <div className="text-xs text-muted-foreground">canonical</div>
              <div className="mt-1 text-lg font-semibold">{screen.canonical_sources.length}</div>
            </div>
            <div className="rounded-md border border-border/40 bg-muted/10 p-3">
              <div className="text-xs text-muted-foreground">legacy</div>
              <div className="mt-1 text-lg font-semibold">{screen.embedded_legacy_surfaces.length}</div>
            </div>
            <div className="rounded-md border border-border/40 bg-muted/10 p-3">
              <div className="text-xs text-muted-foreground">outputs</div>
              <div className="mt-1 text-lg font-semibold">{screen.generated_outputs.length}</div>
            </div>
          </div>

          <div className="space-y-2">
            <div className="text-xs uppercase text-muted-foreground">Safety notes</div>
            {screen.safety_notes.length ? (
              <div className="flex flex-wrap gap-2">
                {screen.safety_notes.map((note) => (
                  <Pill key={note} label={note} tone="border-yellow-500/30 bg-yellow-500/10 text-yellow-200" />
                ))}
              </div>
            ) : (
              <div className="text-sm text-muted-foreground">Observation-only screen.</div>
            )}
          </div>

          {screen.missing_capabilities.length ? (
            <div className="space-y-2">
              <div className="text-xs uppercase text-muted-foreground">Missing or blocked</div>
              {screen.missing_capabilities.map((item) => (
                <div key={item} className="rounded-md border border-yellow-500/30 bg-yellow-500/10 px-3 py-2 text-sm text-yellow-100">
                  {item}
                </div>
              ))}
            </div>
          ) : null}
        </CardContent>
      </Card>

      <Card className="bg-card/80">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <FileText className="h-4 w-4 text-primary" />
            Source Surfaces
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[420px] pr-3">
            <div className="space-y-3">
              {surfaces.length ? (
                surfaces.map((surface) => (
                  <div key={surface.id} className="rounded-md border border-border/40 bg-muted/10 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="min-w-0">
                        <div className="truncate font-mono text-xs text-foreground">{surface.path}</div>
                        <div className="mt-1 text-xs text-muted-foreground">{surface.purpose}</div>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        <Pill label={surface.wiring_status} tone={statusTone[surface.wiring_status] || statusTone.unknown} />
                        <Pill label={surface.safety_class} tone={safetyTone[surface.safety_class] || statusTone.unknown} />
                      </div>
                    </div>
                    {surface.missing_next_step ? (
                      <div className="mt-2 text-xs text-muted-foreground">{surface.missing_next_step}</div>
                    ) : null}
                  </div>
                ))
              ) : (
                <div className="rounded-md border border-border/40 bg-muted/10 p-4 text-sm text-muted-foreground">
                  No matching surfaces in the current manifest.
                </div>
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}

const App = () => (
  <ThemeProvider defaultTheme="dark">
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <AppShell />
      </TooltipProvider>
    </QueryClientProvider>
  </ThemeProvider>
);

export default App;
