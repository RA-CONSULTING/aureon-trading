/**
 * Secret & Environment Validation Script
 *
 * Usage:
 *   npm run validate:secrets
 *
 * This script checks for presence (NOT values) of required and optional
 * environment variables used across the AUREON system (Node + Supabase edge).
 * It does not print secret contents. Exit code 0 = all required present.
 */

type EnvCategory = 'required' | 'optional' | 'trading' | 'frontend';

interface EnvVarSpec {
  name: string;
  description: string;
  category: EnvCategory;
  source?: string; // file or context reference
}

const specs: EnvVarSpec[] = [
  // Core security
  { name: 'MASTER_ENCRYPTION_KEY', description: 'AES-256-GCM master key for credential encryption', category: 'required', source: 'supabase/functions/store-binance-credentials' },
  { name: 'RESEND_API_KEY', description: 'Resend email service key (alerts, signup)', category: 'required', source: 'supabase/functions/send-health-alert & send-signup-notification' },
  // Supabase platform
  { name: 'SUPABASE_URL', description: 'Supabase project URL', category: 'required', source: 'multiple edge functions' },
  { name: 'SUPABASE_SERVICE_ROLE_KEY', description: 'Service role key (server-side only)', category: 'required', source: 'edge functions (Deno.env.get)' },
  // External / optional integrations
  { name: 'LOVABLE_API_KEY', description: 'Lovable tagging/AI API', category: 'optional', source: 'forecast-coherence / protocol-gateway' },
  { name: 'NASA_API_KEY', description: 'Space weather optional data', category: 'optional', source: 'backend-health-check optional secrets' },
  // Binance (used indirectly via encrypted storage – raw keys may not be set if stored in DB)
  { name: 'BINANCE_API_KEY', description: 'Direct Binance key (optional if using encrypted DB fetch)', category: 'optional', source: 'backend-health-check optional; direct trading functions' },
  { name: 'BINANCE_API_SECRET', description: 'Direct Binance secret (optional if using encrypted DB fetch)', category: 'optional', source: 'backend-health-check optional; direct trading functions' },
  // Trading runtime controls
  { name: 'DRY_RUN', description: 'Safety: prevents real trading when true', category: 'trading', source: 'README / scripts' },
  { name: 'CONFIRM_LIVE_TRADING', description: 'Explicit flag for live trading enablement', category: 'trading', source: 'README / scripts' },
  { name: 'BINANCE_TESTNET', description: 'Switch to Binance testnet environment', category: 'trading', source: 'README' },
  // Status / UI server
  { name: 'STATUS_MOCK', description: 'Mock status server responses', category: 'frontend', source: 'README / status server' },
  { name: 'PORT', description: 'Status server port', category: 'frontend', source: 'README' }
];

interface ValidationResult {
  name: string;
  present: boolean;
  category: EnvCategory;
  description: string;
}

function validate(): ValidationResult[] {
  return specs.map(s => ({
    name: s.name,
    present: !!process.env[s.name],
    category: s.category,
    description: s.description
  }));
}

function groupByCategory(results: ValidationResult[]): Record<EnvCategory, ValidationResult[]> {
  return results.reduce((acc, r) => {
    (acc[r.category] ||= []).push(r);
    return acc;
  }, {} as Record<EnvCategory, ValidationResult[]>);
}

function main() {
  const results = validate();
  const groups = groupByCategory(results);
  let missingRequired = 0;

  console.log('\nAUREON Environment Validation');
  console.log('================================');
  (Object.keys(groups) as EnvCategory[]).forEach(cat => {
    console.log(`\n[${cat.toUpperCase()}]`);
    groups[cat].forEach(r => {
      const status = r.present ? 'OK' : 'MISSING';
      if (!r.present && r.category === 'required') missingRequired++;
      console.log(` - ${r.name}: ${status} :: ${r.description}`);
    });
  });

  if (missingRequired > 0) {
    console.error(`\nMissing ${missingRequired} required environment variable(s).`);
    process.exitCode = 1;
  } else {
    console.log('\nAll required environment variables present.');
  }
}

main();
