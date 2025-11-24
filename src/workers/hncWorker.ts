/**
 * HNC Worker
 * ----------
 * Runs the Harmonic Nexus Core periodically
 * and publishes results into the app state.
 */

import { HarmonicNexusCore, type NarrativeItem, type AffectSample } from "@/core/harmonicNexusCore";

const core = new HarmonicNexusCore();

export function startHNC() {
  setInterval(() => {
    // In real use, pull latest 60 min of samples from stores
    const tick = core.run("Global");
    publishHNC(tick);
  }, 60_000); // every minute
}

export function ingestNarrative(item: NarrativeItem) {
  core.addNarrative(item);
}

export function ingestAffect(sample: AffectSample) {
  core.addAffect(sample);
}

function publishHNC(tick: any) {
  // TODO: wire to Zustand/Redux or message bus
  console.log("HNC Tick", tick);
}
