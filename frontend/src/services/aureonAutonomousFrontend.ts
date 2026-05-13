export interface SaaSInventorySummary {
  surface_count?: number;
  frontend_surface_count?: number;
  supabase_function_count?: number;
  legacy_dashboard_count?: number;
  generated_accounting_html_count?: number;
  orphaned_frontend_count?: number;
  security_blocker_count?: number;
  uncalled_supabase_function_count?: number;
  missing_supabase_function_call_count?: number;
}

export interface SaaSInventorySurface {
  id: string;
  path: string;
  name: string;
  kind: string;
  domain: string;
  purpose: string;
  owner_subsystem: string;
  wiring_status: string;
  safety_class: string;
  auth_requirement: string;
  missing_next_step?: string;
  called_apis?: string[];
}

export interface SaaSInventoryManifest {
  status?: string;
  generated_at?: string;
  summary?: SaaSInventorySummary;
  counts?: Record<string, Record<string, number>>;
  gaps?: Record<string, unknown>;
  surfaces?: SaaSInventorySurface[];
}

export interface FrontendScreenPlan {
  id: string;
  title: string;
  domain: string;
  goal: string;
  source_surface_count: number;
  canonical_sources: string[];
  migrated_components: string[];
  embedded_legacy_surfaces: string[];
  backend_functions: string[];
  generated_outputs: string[];
  safety_notes: string[];
  missing_capabilities: string[];
}

export interface FrontendUnificationManifest {
  status?: string;
  generated_at?: string;
  summary?: {
    screen_count?: number;
    migration_action_count?: number;
    missing_screen_capability_count?: number;
    source_surface_count?: number;
    security_blocker_count?: number;
    frontend_surface_count?: number;
    supabase_function_count?: number;
  };
  canonical_screens?: FrontendScreenPlan[];
  migration_actions?: Array<Record<string, unknown>>;
  duplicate_dashboard_groups?: Array<Record<string, unknown>>;
  safety_contract?: Record<string, boolean>;
  observation_loop?: Record<string, unknown>;
}

export interface OrganismDomainPulse {
  id: string;
  label: string;
  domain: string;
  status: string;
  freshness: string;
  source_path: string;
  generated_at?: string;
  age_seconds?: number;
  summary?: Record<string, unknown>;
  metrics?: Record<string, unknown>;
  blind_spots?: string[];
  display_state?: string;
  next_action?: string;
}

export interface OrganismBlindSpot {
  id: string;
  severity: string;
  domain: string;
  issue: string;
  evidence?: Record<string, unknown>;
  next_action?: string;
}

export interface OrganismRuntimeManifest {
  status?: string;
  generated_at?: string;
  mode?: string;
  summary?: {
    domain_count?: number;
    blind_spot_count?: number;
    high_blind_spot_count?: number;
    fresh_domain_count?: number;
    stale_domain_count?: number;
    missing_domain_count?: number;
    attention_domain_count?: number;
    refresh_count?: number;
    failed_refresh_count?: number;
    runtime_feed_status?: string;
    frontend_public_manifest_count?: number;
  };
  safety?: Record<string, unknown>;
  domains?: OrganismDomainPulse[];
  blind_spots?: OrganismBlindSpot[];
  data_freshness?: Record<string, unknown>;
  refresh_results?: Array<Record<string, unknown>>;
  real_time_feeds?: Record<string, unknown>;
  status_lines?: string[];
  next_actions?: string[];
}

export interface FrontendEvolutionWorkOrder {
  id: string;
  title: string;
  source_path: string;
  source_kind: string;
  source_domain: string;
  target_screen: string;
  target_title: string;
  priority: number;
  status: string;
  capability_summary: string;
  evidence?: Record<string, unknown>;
  data_contract?: Record<string, unknown>;
  frontend_action?: string;
  safety_boundary?: string;
  acceptance_tests?: string[];
  next_action?: string;
}

export interface FrontendEvolutionQueueManifest {
  status?: string;
  generated_at?: string;
  summary?: {
    queue_count?: number;
    ready_adapter_count?: number;
    blocked_count?: number;
    archive_candidate_count?: number;
    generated_output_link_count?: number;
    target_screen_count?: number;
    highest_priority?: number;
  };
  work_orders?: FrontendEvolutionWorkOrder[];
  counts?: Record<string, Record<string, number>>;
  safety_contract?: Record<string, boolean>;
  notes?: string[];
}

export interface CapabilityMode {
  id: string;
  title: string;
  domain: string;
  authority_level: string;
  status: string;
  autonomous_allowed: boolean;
  triggers?: string[];
  systems?: string[];
  data_sources?: string[];
  hnc_checks?: string[];
  safe_actions?: string[];
  blocked_actions?: string[];
  frontend_contract?: Record<string, unknown>;
  next_action?: string;
}

export interface PresentationIntent {
  id: string;
  title: string;
  display_mode: string;
  target_screen: string;
  priority: number;
  status: string;
  reason: string;
  source_paths?: string[];
  generated_artifact_contract?: Record<string, unknown>;
  hnc_evidence?: Record<string, unknown>;
  next_action?: string;
}

export interface CapabilitySwitchboardManifest {
  status?: string;
  generated_at?: string;
  goal?: string;
  summary?: {
    capability_count?: number;
    autonomous_capability_count?: number;
    blocked_capability_count?: number;
    presentation_intent_count?: number;
    blocker_count?: number;
    frontend_work_order_count?: number;
    ready_adapter_count?: number;
    security_blocker_count?: number;
    runtime_feed_status?: string;
    canonical_screen_count?: number;
  };
  capability_modes?: CapabilityMode[];
  presentation_intents?: PresentationIntent[];
  route_map?: Record<string, unknown>;
  hnc_control_contract?: Record<string, unknown>;
  safety_contract?: Record<string, boolean>;
  blockers?: Array<Record<string, unknown>>;
  notes?: string[];
}

export interface UnifiedFrontendState {
  loadedAt: string;
  inventorySource: string;
  planSource: string;
  organismSource: string;
  evolutionSource: string;
  switchboardSource: string;
  inventory: SaaSInventoryManifest;
  plan: FrontendUnificationManifest;
  organism: OrganismRuntimeManifest;
  evolution: FrontendEvolutionQueueManifest;
  switchboard: CapabilitySwitchboardManifest;
  errors: string[];
}

const emptyInventory: SaaSInventoryManifest = {
  status: "manifest_missing",
  summary: {
    surface_count: 0,
    frontend_surface_count: 0,
    supabase_function_count: 0,
    security_blocker_count: 0,
    orphaned_frontend_count: 0,
  },
  counts: {},
  gaps: {},
  surfaces: [],
};

const fallbackPlan: FrontendUnificationManifest = {
  status: "manifest_missing",
  summary: {
    screen_count: 7,
    migration_action_count: 0,
    missing_screen_capability_count: 7,
    source_surface_count: 0,
    security_blocker_count: 0,
    frontend_surface_count: 0,
    supabase_function_count: 0,
  },
  canonical_screens: [
    {
      id: "overview",
      title: "Overview",
      domain: "operator",
      goal: "Show organism state, active goals, ThoughtBus health, blockers, and what Aureon is doing now.",
      source_surface_count: 0,
      canonical_sources: [],
      migrated_components: [],
      embedded_legacy_surfaces: [],
      backend_functions: [],
      generated_outputs: [],
      safety_notes: [],
      missing_capabilities: ["Generate aureon_frontend_unification_plan.json."],
    },
    {
      id: "trading",
      title: "Trading",
      domain: "trading",
      goal: "Observe dynamic margin, positions, risk, live/sim status, and decision audit.",
      source_surface_count: 0,
      canonical_sources: [],
      migrated_components: [],
      embedded_legacy_surfaces: [],
      backend_functions: [],
      generated_outputs: [],
      safety_notes: ["live orders remain behind runtime trading gates"],
      missing_capabilities: ["Generate the SaaS inventory."],
    },
    {
      id: "accounting",
      title: "Accounting",
      domain: "accounting",
      goal: "Show company accounts status, evidence, generated packs, and manual filing checklist.",
      source_surface_count: 0,
      canonical_sources: [],
      migrated_components: [],
      embedded_legacy_surfaces: [],
      backend_functions: [],
      generated_outputs: [],
      safety_notes: ["Companies House and HMRC submission remain manual"],
      missing_capabilities: ["Generate the SaaS inventory."],
    },
    {
      id: "research",
      title: "Research",
      domain: "research",
      goal: "Show vault sources, research reports, source ingestion, and knowledge coverage.",
      source_surface_count: 0,
      canonical_sources: [],
      migrated_components: [],
      embedded_legacy_surfaces: [],
      backend_functions: [],
      generated_outputs: [],
      safety_notes: [],
      missing_capabilities: ["Generate the SaaS inventory."],
    },
    {
      id: "saas_security",
      title: "SaaS Security",
      domain: "saas_security",
      goal: "Show auth, tenant isolation, authorized attack-lab findings, fixes, and release gates.",
      source_surface_count: 0,
      canonical_sources: [],
      migrated_components: [],
      embedded_legacy_surfaces: [],
      backend_functions: [],
      generated_outputs: [],
      safety_notes: ["production deployment requires release-gate evidence"],
      missing_capabilities: ["Generate the SaaS inventory."],
    },
    {
      id: "self_improvement",
      title: "Self-Improvement",
      domain: "autonomy",
      goal: "Show audits, benchmarks, queued fixes, retest loop, and restart/apply handoff.",
      source_surface_count: 0,
      canonical_sources: [],
      migrated_components: [],
      embedded_legacy_surfaces: [],
      backend_functions: [],
      generated_outputs: [],
      safety_notes: ["code apply/restart approval when required"],
      missing_capabilities: ["Generate the SaaS inventory."],
    },
    {
      id: "admin",
      title: "Admin",
      domain: "admin",
      goal: "Show env checks, integrations, credentials status, safety gates, and manual-only actions.",
      source_surface_count: 0,
      canonical_sources: [],
      migrated_components: [],
      embedded_legacy_surfaces: [],
      backend_functions: [],
      generated_outputs: [],
      safety_notes: ["credential values stay hidden"],
      missing_capabilities: ["Generate the SaaS inventory."],
    },
  ],
  migration_actions: [],
  duplicate_dashboard_groups: [],
  safety_contract: {
    human_observes_aureon_works: true,
    live_trading_requires_existing_runtime_gates: true,
    official_filing_and_payments_manual_only: true,
    credentials_status_visible_secret_values_hidden: true,
    security_blockers_visible: true,
    legacy_dashboards_preserved_until_migrated: true,
  },
};

const emptyOrganism: OrganismRuntimeManifest = {
  status: "manifest_missing",
  mode: "safe_observation",
  summary: {
    domain_count: 0,
    blind_spot_count: 1,
    high_blind_spot_count: 1,
    fresh_domain_count: 0,
    stale_domain_count: 0,
    missing_domain_count: 1,
    attention_domain_count: 0,
    refresh_count: 0,
    failed_refresh_count: 0,
    runtime_feed_status: "unknown",
    frontend_public_manifest_count: 0,
  },
  safety: {
    observer_only: true,
    live_orders_allowed: false,
    official_filing_allowed: false,
    payments_allowed: false,
    external_mutations_allowed: false,
  },
  domains: [],
  blind_spots: [
    {
      id: "organism_runtime_status.missing",
      severity: "high",
      domain: "runtime",
      issue: "Organism runtime status manifest is not mounted in frontend/public.",
      next_action: "Run python -m aureon.autonomous.aureon_organism_runtime_observer --refresh-core.",
    },
  ],
  status_lines: ["Organism pulse manifest missing."],
  next_actions: ["Run python -m aureon.autonomous.aureon_organism_runtime_observer --refresh-core."],
};

const emptyEvolution: FrontendEvolutionQueueManifest = {
  status: "manifest_missing",
  summary: {
    queue_count: 0,
    ready_adapter_count: 0,
    blocked_count: 0,
    archive_candidate_count: 0,
    generated_output_link_count: 0,
    target_screen_count: 0,
    highest_priority: 0,
  },
  work_orders: [],
  counts: {},
  safety_contract: {
    proposal_only: true,
    legacy_systems_not_executed: true,
    read_only_frontend_adapters_first: true,
    no_live_trading: true,
    no_official_filing: true,
    no_payments: true,
    secret_values_hidden: true,
    apply_requires_explicit_handoff: true,
  },
  notes: ["Frontend evolution queue manifest is missing."],
};

const emptySwitchboard: CapabilitySwitchboardManifest = {
  status: "manifest_missing",
  goal: "Select the safest available Aureon capability and presentation surface.",
  summary: {
    capability_count: 0,
    autonomous_capability_count: 0,
    blocked_capability_count: 1,
    presentation_intent_count: 0,
    blocker_count: 1,
    frontend_work_order_count: 0,
    ready_adapter_count: 0,
    security_blocker_count: 0,
    runtime_feed_status: "unknown",
    canonical_screen_count: 0,
  },
  capability_modes: [],
  presentation_intents: [],
  route_map: {},
  hnc_control_contract: {
    anti_hallucination_gates: ["source_evidence_required", "safe_authority_boundary_checked"],
  },
  safety_contract: {
    llm_can_select_capability: true,
    llm_can_create_presentation_intents: true,
    llm_can_place_direct_live_orders: false,
    llm_can_file_hmrc_or_companies_house: false,
    llm_can_make_payments: false,
    llm_can_attack_third_party_targets: false,
    secret_values_hidden: true,
  },
  blockers: [
    {
      id: "capability_switchboard.missing",
      severity: "high",
      reason: "Capability switchboard manifest is not mounted in frontend/public.",
    },
  ],
  notes: ["Capability switchboard manifest is missing."],
};

async function fetchJson<T>(url: string): Promise<T | null> {
  try {
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) return null;
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

export async function loadUnifiedFrontendState(): Promise<UnifiedFrontendState> {
  const errors: string[] = [];
  const inventoryUrl = "/aureon_saas_system_inventory.json";
  const planUrl = "/aureon_frontend_unification_plan.json";
  const organismUrl = "/aureon_organism_runtime_status.json";
  const evolutionUrl = "/aureon_frontend_evolution_queue.json";
  const switchboardUrl = "/aureon_autonomous_capability_switchboard.json";
  const [inventory, plan, organism, evolution, switchboard] = await Promise.all([
    fetchJson<SaaSInventoryManifest>(inventoryUrl),
    fetchJson<FrontendUnificationManifest>(planUrl),
    fetchJson<OrganismRuntimeManifest>(organismUrl),
    fetchJson<FrontendEvolutionQueueManifest>(evolutionUrl),
    fetchJson<CapabilitySwitchboardManifest>(switchboardUrl),
  ]);

  if (!inventory) errors.push("SaaS inventory manifest is not mounted in frontend/public.");
  if (!plan) errors.push("Frontend unification manifest is not mounted in frontend/public.");
  if (!organism) errors.push("Organism runtime status manifest is not mounted in frontend/public.");
  if (!evolution) errors.push("Frontend evolution queue manifest is not mounted in frontend/public.");
  if (!switchboard) errors.push("Autonomous capability switchboard manifest is not mounted in frontend/public.");

  return {
    loadedAt: new Date().toISOString(),
    inventorySource: inventory ? inventoryUrl : "fallback",
    planSource: plan ? planUrl : "fallback",
    organismSource: organism ? organismUrl : "fallback",
    evolutionSource: evolution ? evolutionUrl : "fallback",
    switchboardSource: switchboard ? switchboardUrl : "fallback",
    inventory: inventory || emptyInventory,
    plan: plan || fallbackPlan,
    organism: organism || emptyOrganism,
    evolution: evolution || emptyEvolution,
    switchboard: switchboard || emptySwitchboard,
    errors,
  };
}

export function surfaceCountByDomain(inventory: SaaSInventoryManifest): Record<string, number> {
  return inventory.counts?.by_domain || {};
}

export function surfacesForScreen(inventory: SaaSInventoryManifest, screen: FrontendScreenPlan): SaaSInventorySurface[] {
  const keywords = [screen.id, screen.domain, ...screen.title.toLowerCase().split(/\s+/)];
  return (inventory.surfaces || [])
    .filter((surface) => {
      const haystack = `${surface.path} ${surface.domain} ${surface.kind} ${surface.purpose}`.toLowerCase();
      return surface.domain === screen.domain || keywords.some((keyword) => keyword && haystack.includes(keyword));
    })
    .slice(0, 12);
}
