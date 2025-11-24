// Auris Runtime Configuration Loader
// Loads and provides typed access to auris_runtime.json

interface AurisRuntimeConfig {
  name: string;
  version: string;
  description: string;
  identity: {
    default_name: string;
    default_dob: string;
    phi: number;
    gaia_hz: number;
    t0_hint_hz: number;
    lattice_id_format: string;
    prime_seal: string;
  };
  paths: {
    codex: string;
    compiler: string;
    auris_metrics_csv: string;
    aura_features_csv: string;
    control_hints: string;
    snapshots_dir: string;
  };
  streams: {
    waveform_stream: { format: string; sample_rate: number; channels: number };
    metrics_stream: { format: string; update_interval_ms: number };
    aura_stream: { format: string; update_interval_ms: number };
  };
  targets_hz: {
    fundamental_default: number;
    harmonics_default: number[];
    snap_fund: number[];
    snap_harm: number[];
  };
  controls: {
    gain_default: number;
    gain_min: number;
    gain_max: number;
    gain_step: number;
    softclip: string;
    debounce_ms: number;
  };
  roles: {
    [key: string]: {
      [metric: string]: string;
    };
  };
  ui: {
    identity: { t0_editable: boolean; show_phi_gaia_scalar: boolean };
    controls: { fund_min: number; fund_max: number; fund_step: number; harm_min: number; harm_max: number; harm_step: number };
    formatting: { safe_number_render: boolean };
  };
  heartbeat: {
    enabled: boolean;
    interval_ms: number;
    type: string;
    target_ws: string;
  };
  snapshots: {
    enabled: boolean;
    dir: string;
    pin_csv_markers: boolean;
    contents: string[];
  };
  safety: {
    clamp_inputs: boolean;
    fallback_targets_when_empty: boolean;
    null_safe_render: boolean;
  };
}

let runtimeConfig: AurisRuntimeConfig | null = null;

export async function loadRuntimeConfig(): Promise<AurisRuntimeConfig> {
  if (runtimeConfig) return runtimeConfig;
  
  try {
    const response = await fetch('/auris_runtime.json');
    runtimeConfig = await response.json();
    return runtimeConfig!;
  } catch (error) {
    console.error('Failed to load auris_runtime.json:', error);
    throw error;
  }
}

export function getRuntimeConfig(): AurisRuntimeConfig | null {
  return runtimeConfig;
}

// Safe number formatter from config
export function fmt(n?: number, d = 2): string {
  const config = getRuntimeConfig();
  if (config?.safety.null_safe_render) {
    return (typeof n === 'number' && isFinite(n)) ? n.toFixed(d) : '—';
  }
  return n?.toFixed(d) ?? '—';
}

// Role evaluation helper
export function evaluateRole(metrics: Record<string, number>): string {
  const config = getRuntimeConfig();
  if (!config) return 'Observer / Calibrator';

  for (const [roleName, requirements] of Object.entries(config.roles)) {
    if (Object.keys(requirements).length === 0) continue; // Skip empty roles
    
    const meetsAll = Object.entries(requirements).every(([metric, threshold]) => {
      const value = metrics[metric];
      if (typeof value !== 'number') return false;
      
      const thresholdValue = parseFloat(threshold.replace('>= ', ''));
      return value >= thresholdValue;
    });
    
    if (meetsAll) return roleName;
  }
  
  return 'Observer / Calibrator';
}