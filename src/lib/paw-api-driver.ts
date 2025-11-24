// PAW API Driver - Software mock of Phased Atomic Weaver API
// Implements: Init, Arm, Inject, Place, Pause, Abort, GetTelemetry

import { Element, Voxel, PlaceReply, Telemetry, PAWCapabilities, SafetyViolation } from '../types/paw-types';

export class PAWAPIDriver {
  private inited = false;
  private armed = false;
  private interlocks_ok = true;
  private temp_K = 2.4;
  private flux_ips = 0.0;
  private balance_B = 0.0;
  private error_pm = 0.0;
  private epa_eV = 0.0;
  private fault_bias = 0.0;
  private paused = false;
  private aborted = false;
  private last_place_t = 0.0;
  private rng_seed = 42;

  public caps: PAWCapabilities = {
    B_min: 0.6,
    error_goal_pm: 50.0,
    error_hard_pm: 200.0,
    flux_max: 2.0e6,
  };

  private random(): number {
    // Simple seeded random number generator
    this.rng_seed = (this.rng_seed * 9301 + 49297) % 233280;
    return this.rng_seed / 233280;
  }

  private gauss(mean: number, stddev: number): number {
    // Box-Muller transform for Gaussian distribution
    const u1 = this.random();
    const u2 = this.random();
    const z0 = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
    return mean + stddev * z0;
  }

  Init(profile: string): [boolean, string] {
    this.inited = true;
    this.aborted = false;
    this.paused = false;
    this.temp_K = 2.0 + (this.random() - 0.5) * 0.3;
    return [true, `Profile '${profile}' loaded`];
  }

  Arm(balance_B: number, interlocks_ok: boolean): [boolean, string] {
    this.balance_B = balance_B;
    this.interlocks_ok = interlocks_ok;
    
    if (!this.inited) {
      return [false, "Weaver not initialized"];
    }
    if (!interlocks_ok) {
      return [false, "Interlocks not OK"];
    }
    if (balance_B < this.caps.B_min) {
      return [false, `Balance ${balance_B.toFixed(2)} below minimum ${this.caps.B_min}`];
    }
    
    this.armed = true;
    // Lower fault bias when balance is high
    this.fault_bias = Math.max(0.0, 1.0 - Math.min(balance_B, 2.0) / 2.0);
    return [true, "Armed"];
  }

  Inject(element: Element, voxel: Voxel): [boolean, string] {
    if (!this.armed) {
      return [false, "Not armed"];
    }
    // Mock injection - always succeeds
    return [true, `Injected ${element} at (${voxel.x}, ${voxel.y}, ${voxel.z})`];
  }

  Place(): PlaceReply {
    if (this.aborted) {
      return {
        ok: false,
        error_pm: this.error_pm,
        epa_eV: this.epa_eV,
        safety_violation: { reason: "Aborted", category: "abort" }
      };
    }

    if (this.paused) {
      return {
        ok: false,
        error_pm: this.error_pm,
        epa_eV: this.epa_eV,
        safety_violation: { reason: "Paused", category: "pause" }
      };
    }

    // Simulate placement with Gaussian error
    this.error_pm = Math.abs(this.gauss(this.caps.error_goal_pm, 20.0)) + this.fault_bias * 50.0;
    this.epa_eV = this.gauss(0.8, 0.1);
    
    // Check safety thresholds
    if (this.error_pm > this.caps.error_hard_pm) {
      return {
        ok: false,
        error_pm: this.error_pm,
        epa_eV: this.epa_eV,
        safety_violation: { reason: `Error ${this.error_pm.toFixed(1)} pm exceeds limit`, category: "precision" }
      };
    }

    this.last_place_t = Date.now() / 1000.0;
    return {
      ok: true,
      error_pm: this.error_pm,
      epa_eV: this.epa_eV
    };
  }

  Pause(): [boolean, string] {
    this.paused = true;
    return [true, "Paused"];
  }

  Resume(): [boolean, string] {
    this.paused = false;
    return [true, "Resumed"];
  }

  Abort(): [boolean, string] {
    this.aborted = true;
    this.armed = false;
    return [true, "Aborted"];
  }

  GetTelemetry(): Telemetry {
    // Simulate temperature drift
    this.temp_K += (this.random() - 0.5) * 0.05;
    this.flux_ips = this.armed ? this.caps.flux_max * (0.3 + this.random() * 0.4) : 0.0;
    
    return {
      temp_K: this.temp_K,
      flux_ips: this.flux_ips,
      balance_B: this.balance_B,
      interlocks_ok: this.interlocks_ok,
      error_pm: this.error_pm,
      epa_eV: this.epa_eV,
      paused: this.paused,
      aborted: this.aborted
    };
  }
}