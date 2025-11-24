#!/usr/bin/env tsx
/**
 * Nexus Live Feed Integration Test
 * Demonstrates polling Nexus metrics and deriving composite coherence boost.
 */

import { nexusLiveFeedBridge } from '../src/core/nexusLiveFeedBridge';

console.log('🛰️ NEXUS LIVE FEED INTEGRATION TEST');
console.log('='.repeat(60));

async function run() {
  // Initial poll
  let influence = await nexusLiveFeedBridge.poll();
  printInfluence('INITIAL', influence);

  console.log('\nReal-time sampling (10 iterations)...');
  for (let i = 0; i < 10; i++) {
    await new Promise(res => setTimeout(res, 1500));
    influence = await nexusLiveFeedBridge.poll();
    printInfluence(`SAMPLE ${i + 1}`, influence, true);
  }

  console.log('\nConfiguration:');
  console.log(nexusLiveFeedBridge.getConfig());

  console.log('\nStatus Legend: optimal > supportive > neutral > degraded');
  console.log('\n✅ Nexus integration operational');
}

function printInfluence(label: string, inf: any, compact = false) {
  if (compact) {
    console.log(`${label.padEnd(10)} | QC ${(inf.quantumCoherence*100).toFixed(0)}% | HR ${(inf.harmonicResonance*100).toFixed(0)}% | Sch ${inf.schumannProxyHz.toFixed(2)}Hz | Boost ${(inf.compositeBoost*100).toFixed(1)}% | ${statusEmoji(inf.status)}`);
    return;
  }
  console.log(`\n[${label}]`);
  console.log(`Quantum Coherence: ${(inf.quantumCoherence*100).toFixed(1)}%`);
  console.log(`Harmonic Resonance: ${(inf.harmonicResonance*100).toFixed(1)}%`);
  console.log(`Schumann Proxy: ${inf.schumannProxyHz.toFixed(2)} Hz`);
  console.log(`Rainbow Spectrum: ${(inf.rainbowSpectrum*100).toFixed(1)}%`);
  console.log(`Consciousness Shift: ${(inf.consciousnessShift*100).toFixed(1)}%`);
  console.log(`Composite Boost: ${(inf.compositeBoost*100).toFixed(2)}% (${inf.status}) ${statusEmoji(inf.status)}`);
}

function statusEmoji(status: string) {
  switch(status) {
    case 'optimal': return '🟢';
    case 'supportive': return '🔵';
    case 'neutral': return '🟡';
    default: return '🔴';
  }
}

run().catch(err => {
  console.error('Nexus integration test failed:', err);
  process.exit(1);
});
